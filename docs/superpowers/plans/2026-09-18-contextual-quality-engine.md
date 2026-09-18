# Contextual Local Quality Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Translate game text with glossary, translation-memory and surrounding-text context through an offline local Qwen3 model, with automatic fallback to NLLB.

**Architecture:** `LlamaLocalProvider` formats the existing `TranslationRequest` contract into a strict JSON translation prompt and delegates generation to a small `ChatClient` protocol. `LlamaServer` lazily owns a hidden local llama.cpp process and HTTP client. `QualityFallbackProvider` makes the quality engine the first choice while retaining NLLB whenever runtime files are missing or the local server fails.

**Tech Stack:** Python 3.12 stdlib HTTP/process APIs, llama.cpp b10964 Vulkan, Qwen3-4B Q4_K_M GGUF, PySide6, pytest

**Spec:** `docs/superpowers/specs/2026-09-18-capture-overlay-quality-design.md`

## Global Constraints

- Offline by default; bind the server to `127.0.0.1` only.
- Model: `Qwen/Qwen3-4B-GGUF`, commit `bc640142c66e1fdd12af0bd68f40445458f3869b`, file `Qwen3-4B-Q4_K_M.gguf`, 2,497,280,256 bytes, SHA-256 `7485fe6f11af29433bc51cab58009521f205840f5b4ae3a32fa7f92e8534fdf5`.
- Runtime: llama.cpp `b10964`, Windows Vulkan x64 archive SHA-256 `1ee3ad952f4ba71f438bd6d7bebef19e1c7af04adcaa35d08b4ddabb27d4c642`.
- No OCR source text, prompt or translation may be logged or persisted by the provider.
- Invalid or unavailable quality output falls back to the existing NLLB provider.

---

### Task 1: Context prompt and provider contract

**Files:**
- Create: `src/translate/llama_local.py`
- Create: `tests/unit/translate/test_llama_local.py`

**Interfaces:**
- Consumes: `TranslationRequest`
- Produces: `ChatClient.complete(system: str, user: str, max_tokens: int) -> str`
- Produces: `LlamaLocalProvider.translate(request) -> TranslationResult`

- [ ] **Step 1: Write failing tests for prompt content and aligned JSON parsing**

```python
def test_prompt_uses_glossary_tm_style_and_all_segments():
    provider = LlamaLocalProvider(FakeChat('{"translations":["Çeviri"]}'))
    result = provider.translate(request_with_context)
    assert result.translations == ("Çeviri",)
    assert "İhtiyar" in fake.user and "önceki çeviri" in fake.user
```

- [ ] **Step 2: Confirm the tests fail because the provider module is missing**

Run: `python -m pytest tests/unit/translate/test_llama_local.py -q`

- [ ] **Step 3: Implement deterministic prompt building and strict result validation**

Use `json.dumps(..., ensure_ascii=False)`, temperature `0`, exact segment IDs, and `ensure_aligned`. Reject Markdown fences, missing arrays, non-string values and count mismatch as `ProviderUnavailable` without including source/output text in the error.

- [ ] **Step 4: Run focused tests and commit**

Commit: `Bağlamı kullanan yerel kalite sağlayıcısını ekle`

### Task 2: Hidden llama.cpp server lifecycle

**Files:**
- Create: `src/translate/llama_server.py`
- Create: `tests/unit/translate/test_llama_server.py`

**Interfaces:**
- Produces: `LlamaServer.complete(system: str, user: str, max_tokens: int) -> str`
- Produces: `LlamaServer.close() -> None`

- [ ] **Step 1: Write failing tests with injected process and HTTP adapters**

Cover hidden-process flags, loopback host, health polling, JSON request shape, timeout classification and idempotent close.

- [ ] **Step 2: Implement lazy process start and stdlib HTTP call**

Start `llama-server.exe -m <model> --host 127.0.0.1 --port <port> -ngl 99 -c 4096`; use `CREATE_NO_WINDOW`; send `/v1/chat/completions`; never copy prompt/output into exceptions.

- [ ] **Step 3: Run focused tests and commit**

Commit: `Yerel kalite modelini gizli llama.cpp sunucusuyla çalıştır`

### Task 3: Verified runtime downloader

**Files:**
- Create: `src/model_yonetimi/kalite_modeli.py`
- Create: `tests/unit/model_yonetimi/test_kalite_modeli.py`

**Interfaces:**
- Produces: `KaliteModeliDurumu`
- Produces: `KaliteModeliYoneticisi.indir(progress: Callable[[int, int], None]) -> None`
- Produces: `KaliteModeliYoneticisi.hazir_mi -> bool`

- [ ] **Step 1: Write failing tests for `.part` downloads, SHA-256, atomic rename and zip-slip rejection**

- [ ] **Step 2: Implement streaming downloads and verified extraction**

Write only to ignored `models/qwen3-4b/` and `runtime/llama/`; verify exact length and SHA-256 before `Path.replace`; reject archive members outside the destination.

- [ ] **Step 3: Run focused tests and commit**

Commit: `Kalite modeli ve yerel çalıştırıcı için doğrulamalı indirme ekle`

### Task 4: Quality-first fallback wiring

**Files:**
- Create: `src/translate/fallback.py`
- Create: `tests/unit/translate/test_fallback.py`
- Modify: `src/pipeline/motorlar.py`
- Modify: `demo/kabuk.py`

**Interfaces:**
- Produces: `QualityFallbackProvider(primary, fallback)` implementing `TranslationProvider`
- `gercek_fabrikalar(..., kalite_yollari=None)` returns NLLB alone when quality files are absent and quality-first fallback when present.

- [ ] **Step 1: Write failing fallback tests**

Prove primary success, fallback on `ProviderUnavailable`, fallback on `ProviderTimeout`, no fallback on invalid request, and both providers close exactly once.

- [ ] **Step 2: Implement the wrapper and wire it into the motor factory**

- [ ] **Step 3: Run pipeline and provider suites and commit**

Commit: `Bağlamlı kalite motorunu NLLB yedeğiyle ürüne bağla`

### Task 5: Nontechnical installation UI and verification

**Files:**
- Modify: `src/ui/kabuk.py`
- Modify: `demo/kabuk.py`
- Modify: `tests/unit/ui/test_kabuk.py`
- Modify: `docs/KULLANICI_TEST_REHBERI.md`

**Interfaces:**
- Main window shows `Kalite modelini indir · 2,5 GB` when absent, progress while downloading, and `Bağlamlı çeviri hazır` after verification.

- [ ] **Step 1: Write failing Qt tests for absent/downloading/ready/error states**

- [ ] **Step 2: Add the nonmodal download control and background worker**

No file picker, terminal or API key. A failed download leaves NLLB usable and offers retry.

- [ ] **Step 3: Add Blue Prince manual quality checks**

The guide asks the user to compare an ambiguous sentence with neighbouring lines visible and verifies proper names against the glossary.

- [ ] **Step 4: Run complete verification and commit**

Run: `python -m pytest -q`  
Run: `python -m mypy --strict --explicit-package-bases src`

Commit: `Bağlamlı çeviri modelini kullanıcı akışına ekle`

