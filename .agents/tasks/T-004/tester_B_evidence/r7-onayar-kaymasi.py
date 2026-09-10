"""T7-2: testin 'esik carpimlari ASSERT'te' korumasinin DISI var mi?

Iddia (test docstring'i): "on ayar tablosu kayarsa bu test TOTOLOJIYE dusmek
yerine KIRILIR". Olcu: `presets.py`'yi BELLEKTE kaydirip testin GERCEKTEN
kirildigini ve KIRILMA YERININ esik assert'i oldugunu gosteririm.
`src/` YAZILMAZ.
"""
from __future__ import annotations

import importlib.util
import sys
import traceback
import types
from pathlib import Path

KOK = Path(__file__).resolve()
while not (KOK / ".agents").is_dir():
    KOK = KOK.parent
for _y in (str(KOK), str(KOK / ".agents" / "tasks" / "T-004")):
    if _y not in sys.path:
        sys.path.insert(0, _y)

PRESETS = KOK / "src" / "ocr" / "presets.py"
KAYMALAR = {
    "P-a": ("dialogue esigi 0.8 -> 0.5 (miras artik UYGULANMAZ)",
            "max_vertical_gap_ratio=0.8", "max_vertical_gap_ratio=0.5"),
    "P-b": ("tooltip esigi 0.3 -> 0.8 (iki on ayar AYNI olur, ayirt gucu biter)",
            "max_vertical_gap_ratio=0.3", "max_vertical_gap_ratio=0.8"),
}


def kur(eski: str, yeni: str) -> None:
    kaynak = PRESETS.read_text(encoding="utf-8")
    if kaynak.count(eski) != 1:
        raise SystemExit(f"'{eski}' {kaynak.count(eski)} kez -- 1 bekleniyordu")
    import src.ocr
    mod = types.ModuleType("src.ocr.presets")
    mod.__file__, mod.__package__ = str(PRESETS), "src.ocr"
    sys.modules["src.ocr.presets"] = mod
    exec(compile(kaynak.replace(eski, yeni), str(PRESETS), "exec"), mod.__dict__)
    src.ocr.presets = mod  # type: ignore[attr-defined]


ad = sys.argv[1]
aciklama, eski, yeni = KAYMALAR[ad]
kur(eski, yeni)

spec = importlib.util.spec_from_file_location(
    "t7_tn", KOK / "tests" / "unit" / "ocr" / "test_normalizer.py")
assert spec and spec.loader
tm = importlib.util.module_from_spec(spec)
sys.modules["t7_tn"] = tm
spec.loader.exec_module(tm)

try:
    tm.test_k28_miras_sorgusu_ayni_params_ile_sorulur()
    print(f"{ad} | test=GECTI  <-- TOTOLOJI RISKI | {aciklama}")
except AssertionError:
    tb = traceback.extract_tb(sys.exc_info()[2])
    son = [f for f in tb if f.filename.endswith("test_normalizer.py")][-1]
    print(f"{ad} | test=DUSTU  | {aciklama}")
    print(f"     `-> kirildigi satir {son.lineno}: {(son.line or '').strip()[:100]}")
