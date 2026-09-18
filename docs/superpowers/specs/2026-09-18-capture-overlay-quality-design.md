# Suflor Capture, Overlay and Translation Quality Design

**Date:** 2026-09-18  
**Status:** Approved by the user  
**Parent spec:** `docs/superpowers/specs/2026-09-09-suflor-design.md`

## Problem

The current local NLLB provider translates only the selected OCR text. It accepts glossary, translation-memory, style and image fields but does not use them. Automatic language detection can run multiple OCR models serially on the first capture. Region Watch uses a large independent tool window. Suflor windows can also appear in a full-screen capture because capture starts before the shell is hidden.

## Approved behavior

1. Every Suflor top-level window is excluded from Windows screen capture with `SetWindowDisplayAffinity(WDA_EXCLUDEFROMCAPTURE)`. If Windows rejects that call, Snapshot temporarily hides visible Suflor windows for one compositor turn before capture and restores them afterwards.
2. Region Watch is a frameless translucent strip attached above the selected area. If there is no room above, it is placed below and clamped to the current screen. Only translated text is permanently visible; controls appear on hover.
3. Region Watch keeps one in-flight OCR/translation job, retains only the newest changed frame, and does not translate identical normalized OCR text twice.
4. Automatic OCR starts with English for a fresh installation and remembers the last successful language during the application session. A fixed language setting remains available.
5. A separate quality provider will use a local Apache-2.0 Qwen3 4B GGUF model through llama.cpp. It will receive selected text, neighbouring text, glossary terms, translation-memory examples and style instructions. NLLB remains the fast and failure fallback provider.
6. Snapshot defaults to the quality provider after it is installed. Region Watch uses the quality provider with latest-frame backpressure; it falls back to NLLB if the quality runtime is unavailable.
7. No screenshots, OCR text or translations are written to disk or sent over the network by the offline path.

## Delivery split

The first delivery contains capture exclusion, the attached strip, duplicate-text suppression and the faster fresh-session language default. It is independently useful and testable. The second delivery contains the local quality runtime, model manager and Blue Prince quality corpus. Keeping the runtime separate prevents a 2.5 GB model download from blocking the UI and privacy fixes.

## Acceptance criteria

- A Windows API unit test proves the exact `0x11` affinity value and a Qt integration test proves every registered top-level window is protected after `show()`.
- Snapshot capture runs after protected windows are hidden only when affinity is unavailable, and visibility is restored even when capture raises.
- Region strip geometry is deterministic for space above, space below and screen-edge clamping.
- Hovering reveals controls; leaving hides them; translated text remains visible throughout.
- Repeated OCR text causes no second translation request.
- Existing tests remain green and the user guide contains a manual game test for capture privacy, strip placement and speed.

