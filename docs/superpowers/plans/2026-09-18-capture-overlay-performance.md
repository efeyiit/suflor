# Capture-safe Overlay and Performance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep Suflor out of captures, replace the Region Watch tool window with an attached translation strip, and remove avoidable repeated work.

**Architecture:** A focused Windows capture-privacy service owns `SetWindowDisplayAffinity` and the hide/restore fallback. Pure geometry functions place a compact Qt strip relative to the selected physical-pixel rectangle. Region Watch suppresses duplicate normalized OCR text while preserving its existing one-in-flight/latest-frame backpressure.

**Tech Stack:** Python 3.12, PySide6, ctypes/Win32, pytest, pytest-qt

**Spec:** `docs/superpowers/specs/2026-09-18-capture-overlay-quality-design.md`

## Global Constraints

- Windows 11 x64 is the target platform.
- No process injection, API hook or game-memory access.
- No modal dialog in the game flow.
- No screenshot, OCR text or translation is written to disk or logs.
- NLLB remains available as the current translation provider.

---

### Task 1: Windows capture privacy

**Files:**
- Create: `src/ui/yakalama_gizliligi.py`
- Create: `tests/unit/ui/test_yakalama_gizliligi.py`
- Modify: `demo/kabuk.py`

**Interfaces:**
- Produces: `YakalamaGizliligi.koru(widget) -> bool`
- Produces: `YakalamaGizliligi.yakala(capture, windows) -> object`

- [ ] **Step 1: Write the failing API tests**

```python
def test_koru_exclude_from_capture_degerini_kullanir(qtbot):
    calls = []
    privacy = YakalamaGizliligi(set_affinity=lambda hwnd, value: calls.append((hwnd, value)) or True)
    widget = QWidget(); qtbot.addWidget(widget); widget.show()
    assert privacy.koru(widget)
    assert calls[-1][1] == 0x11

def test_yakala_fallbackta_gizler_ve_hatada_da_geri_gosterir(qtbot):
    privacy = YakalamaGizliligi(set_affinity=lambda *_: False, compositor_wait=lambda: None)
    widget = QWidget(); qtbot.addWidget(widget); widget.show()
    with pytest.raises(CaptureError):
        privacy.yakala(lambda: (_ for _ in ()).throw(CaptureError("x")), [widget])
    assert widget.isVisible()
```

- [ ] **Step 2: Run the focused tests and confirm failure because the module is missing**

Run: `python -m pytest tests/unit/ui/test_yakalama_gizliligi.py -q`

- [ ] **Step 3: Implement the Win32 adapter and fallback**

```python
WDA_EXCLUDEFROMCAPTURE = 0x11

class YakalamaGizliligi:
    def koru(self, widget: QWidget) -> bool: ...
    def yakala(self, capture: Callable[[], T], windows: Sequence[QWidget]) -> T: ...
```

- [ ] **Step 4: Use one shared privacy service in `demo/kabuk.py`**

Protect `AnaPencere`, `KenarSekmesi`, selection layers, Snapshot windows and Region Watch. Route `capture_full` through `yakala` so the fallback precedes capture.

- [ ] **Step 5: Run focused tests and commit**

Run: `python -m pytest tests/unit/ui/test_yakalama_gizliligi.py tests/unit/ui/test_kabuk.py -q`

Commit: `Ekran yakalamalarında Suflör pencerelerini gizle`

### Task 2: Attached Region Watch strip

**Files:**
- Create: `src/ui/bolge_geometrisi.py`
- Create: `tests/unit/ui/test_bolge_geometrisi.py`
- Modify: `src/ui/bolge_pencere.py`
- Modify: `tests/unit/ui/test_bolge_pencere.py`

**Interfaces:**
- Produces: `serit_dikdortgeni(bolge: Rect, ekran: Rect, yukseklik: int = 112, bosluk: int = 8) -> Rect`
- Produces: `BolgePenceresi.araclar_gorunur: bool`

- [ ] **Step 1: Write failing pure geometry tests**

```python
def test_serit_bolgenin_ustunde_ve_ayni_genislikte():
    assert serit_dikdortgeni(Rect(100, 300, 500, 100), Rect(0, 0, 1920, 1080)) == Rect(100, 180, 500, 112)

def test_ustte_yer_yoksa_alta_koyar():
    assert serit_dikdortgeni(Rect(100, 20, 500, 100), Rect(0, 0, 1920, 1080)).y == 128
```

- [ ] **Step 2: Confirm the geometry tests fail, implement the pure function, and make them pass**

Run: `python -m pytest tests/unit/ui/test_bolge_geometrisi.py -q`

- [ ] **Step 3: Write failing Qt behavior tests**

Assert frameless/translucent flags, attached geometry, controls hidden initially, controls visible on `Enter`, hidden on `Leave`, and translation text still visible.

- [ ] **Step 4: Rebuild `BolgePenceresi` as the compact strip**

Use a translucent rounded `QFrame`, a translation label, a hidden hover toolbar with source/pause/reselect/close buttons, and a small status line shown only during work or errors.

- [ ] **Step 5: Run UI tests and commit**

Run: `python -m pytest tests/unit/ui/test_bolge_geometrisi.py tests/unit/ui/test_bolge_pencere.py -q`

Commit: `Bölge çevirisini seçili alana yapışık şeride dönüştür`

### Task 3: Duplicate work suppression and fresh-session language speed

**Files:**
- Modify: `src/ui/bolge_pencere.py`
- Modify: `tests/unit/ui/test_bolge_pencere.py`
- Modify: `demo/kabuk.py`
- Create: `tests/unit/demo/test_kabuk_urun_kararlari.py`

**Interfaces:**
- Region Watch compares `" ".join(text.split()).casefold()` before translation.
- `OTOMATIK_BASLANGIC` is `OcrLanguage.ENGLISH`; `DilSecici.mevcut` still changes and persists for the session.

- [ ] **Step 1: Write a failing duplicate-text test**

```python
def test_ayni_ocr_metni_ikinci_kez_cevirmez(qtbot):
    # emit equivalent whitespace/case text on the second changed frame
    assert len(akis.cevrilen) == 1
```

- [ ] **Step 2: Confirm failure and implement normalized source deduplication**

Do not update the displayed translation when the source is unchanged; finish the job and process the newest pending frame.

- [ ] **Step 3: Write a failing product-policy test for English automatic start**

```python
def test_yeni_oturum_otomatik_dile_ingilizceyle_baslar():
    assert OTOMATIK_BASLANGIC is OcrLanguage.ENGLISH
```

- [ ] **Step 4: Make the policy test pass and run the affected suite**

Run: `python -m pytest tests/unit/ui/test_bolge_pencere.py tests/unit/demo/test_kabuk_urun_kararlari.py tests/unit/ocr/test_dil_algila.py tests/unit/pipeline/test_dil_secici.py -q`

- [ ] **Step 5: Commit**

Commit: `Bölge izleme tekrarlarını ve ilk İngilizce algılama gecikmesini azalt`

### Task 4: User test guide and complete verification

**Files:**
- Modify: `docs/KULLANICI_TEST_REHBERI.md`
- Modify: `README.md`

**Interfaces:**
- Produces a nontechnical manual test for Snapshot privacy, strip placement, repeated text and Blue Prince first capture.

- [ ] **Step 1: Add the manual test sequence and expected results**

The sequence checks that no Suflor UI appears in the frozen screenshot, the strip hugs the selected area, hover controls work, and unchanged dialogue does not show a new loading state.

- [ ] **Step 2: Run formatting/type/unit gates**

Run: `python -m pytest -q`  
Run: `python -m mypy --strict src demo`

- [ ] **Step 3: Inspect diff and commit**

Run: `git diff --check`  
Commit: `Yakalama ve bölge şeridi kullanıcı testini belgele`

