"""TESTER-B K1 bariyeri (T-008) -- `conftest.py` bunu import eder; KENDI BASINA kurulur.

Bu dizin `tests/unit/ocr` disinda oldugu icin sefin `tests/unit/ocr/conftest.py`
bariyeri burada YUKLENMEZ. Mercek B'nin testleri sentetik `TextBlock` ile kosar
ama bir hata olursa gercek OCR kutuphanesine kaymasin diye bariyer burada
bagimsiz bir uygulamayla yeniden kurulur.

Mesaj "K1 bariyeri" alt dizesini TASIR: testler `match="K1 bariyeri"` kullanir,
boylece sefin bariyeriyle BIRLIKTE kosulunca (`pytest tests/unit/ocr
.agents/tasks/T-008/tester_B`) hangisi once ateslerse ateslesin `match` tutar.
"""
from __future__ import annotations

import importlib.abc
import importlib.machinery
import sys
from pathlib import Path

_KOK = Path(__file__).resolve()
while _KOK.name and not (_KOK / ".agents").is_dir():
    _KOK = _KOK.parent
if str(_KOK) not in sys.path:
    sys.path.insert(0, str(_KOK))

YASAK_KOKLER: tuple[str, ...] = ("rapidocr", "onnxruntime")
BARIYER_MESAJI = "tester-B T-008 K1 bariyeri"

ONCEDEN_YUKLU: tuple[str, ...] = tuple(
    sorted(k for k in sys.modules if k.split(".", 1)[0] in YASAK_KOKLER)
)


class TesterBBariyer(importlib.abc.MetaPathFinder):
    """`rapidocr*` / `onnxruntime*` icin her `find_spec` sorgusunu RuntimeError ile keser."""

    sorgular: list[str]

    def __init__(self) -> None:
        self.sorgular = []

    def find_spec(
        self, fullname: str, path: object = None, target: object = None
    ) -> importlib.machinery.ModuleSpec | None:
        if fullname.split(".", 1)[0] in YASAK_KOKLER:
            self.sorgular.append(fullname)
            raise RuntimeError(f"{BARIYER_MESAJI}: {fullname!r} birim testte import edilemez")
        return None


BARIYER = TesterBBariyer()
if not any(isinstance(f, TesterBBariyer) for f in sys.meta_path):
    # Sefin bariyeri (`_T006Bariyer`) zaten kuruluysa ONUN ARKASINA gir: sefin pozitif
    # kontrolu (`tests/unit/ocr/test_conftest_bariyer.py`) `match="T-006 K1 bariyeri"` ile
    # KESIN eslesir; onune gecersem birlikte kosumda o test duser (olculdu:
    # B5-birlikte-kosum-sef-ve-tester-B-ilk.txt, 3 kirik). Sefinki sonra yuklenirse
    # zaten basa girer ve once ateslenir.
    _mevcut = [i for i, f in enumerate(sys.meta_path) if "Bariyer" in type(f).__name__]
    sys.meta_path.insert((_mevcut[-1] + 1) if _mevcut else 0, BARIYER)
