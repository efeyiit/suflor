[Türkçe](README.md) · **English**

# Suflör

**A Windows desktop app that captures, recognizes and translates on-screen text.**
Built for games, works anywhere. Free and offline.

---

> [!NOTE]
> **Status: design phase.** No code yet. This repository currently holds the design
> document only. Development starts once the implementation plan is written.

## Two modes

**1 · Snapshot Mode** — Hit the hotkey and the screen freezes. Detected text blocks
get outlined, you pick the ones you want, and the selection is translated together
with its visual context.

**2 · Region Watch Mode** — Draw a rectangle on screen. Every piece of text that
appears inside it is translated automatically and continuously; the translation flows
into a semi-transparent strip attached to the region. You can detach the strip and
move it to a second monitor.

## Three core stances

**Free and offline by default.** No API key is requested on first run. Local OCR and
local translation engines are downloaded, and the app comes up working. Cloud
providers are an opt-in upgrade you enable in settings — not required, not the default.

**Safe with respect to anti-cheat.** No process injection, no DLL injection, no API
hooks, no memory reads. Only Windows' own screen capture paths and an ordinary
top-most window — that is, strictly less than what OBS does. The risk of getting your
game account banned should be zero. This is not a limitation, it is a deliberate
architectural stance.

**No error stops the pipeline.** Persistent failures show as a single line in the
status bar. Throwing a modal dialog at someone who is mid-game is unforgivable.

## Translation intelligence: four layers

| Layer | What | Status |
|---|---|---|
| **0** | Per-game glossary + translation memory (TM) | v1 |
| **1** | Local NMT (CTranslate2, int8) — fast, default for Mode 2 | v1 |
| **2** | Local small LLM (4B, vision) — context-aware, default for Mode 1 | v1 |
| **3** | Own model fine-tuned on game dialogue (QLoRA) | roadmap |
| — | Cloud providers (Gemini / DeepL / others) | v1, optional |

Layer 0 is the highest-return layer: what makes even a mediocre engine feel specific
to *that* game is the per-game glossary and translation memory — and it costs nothing
but code.

## The game side

- **Game profiles** — per-game regions, languages, engine, glossary, style profile and
  OCR preset. Suggested automatically from the active window's executable name, and
  shareable as `.json`.
- **Text-type presets** — dialogue box, menu, tooltip, subtitle; each needs different
  block-grouping and debounce behavior.
- **Exclusive fullscreen** — overlays are invisible in this mode (a Windows
  constraint). The app detects it and says so plainly: switch to borderless, or detach
  the strip to a second monitor.

## Technology

Python 3.12 · PySide6 (Qt 6) · RapidOCR (ONNX Runtime) · CTranslate2 · llama.cpp ·
SQLite · PyInstaller

Targets: end-to-end ≤ 160 ms on cache hit / ≤ 320 ms on cache miss in Mode 2, and
≤ 3% game FPS drop.

## Documentation

| | |
|---|---|
| **Design document (Markdown)** | [`docs/superpowers/specs/2026-09-09-suflor-design.md`](docs/superpowers/specs/2026-09-09-suflor-design.md) |
| **Design document (PDF, 28 pages)** | [`docs/superpowers/specs/2026-09-09-suflor-design.pdf`](docs/superpowers/specs/2026-09-09-suflor-design.pdf) |
| **Agent communication network — comparison (Markdown, Turkish)** | [`docs/superpowers/specs/2026-09-09-ajan-iletisim-agi-karsilastirma.md`](docs/superpowers/specs/2026-09-09-ajan-iletisim-agi-karsilastirma.md) |
| **Agent communication network — comparison (PDF, 8 pages, Turkish)** | [`docs/superpowers/specs/2026-09-09-ajan-iletisim-agi-karsilastirma.pdf`](docs/superpowers/specs/2026-09-09-ajan-iletisim-agi-karsilastirma.pdf) |

Twelve sections: the product and its two modes, game-specific details, the four-layer
translation intelligence, runtime architecture (components, contracts, concurrency,
error handling, performance budget), development agents and orchestration, test
strategy, risks, roadmap, open questions and a decision log.

> The design document is currently in Turkish only. An English translation is planned.

## License

No license has been chosen yet — the legal default is therefore all rights reserved.
An explicit license will be added for contribution and redistribution (see design
document §12.6).
