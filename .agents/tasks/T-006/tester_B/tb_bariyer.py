"""TESTER-B K1 bariyeri -- conftest.py bunu import eder; KENDI BASINA kurulur (sefin conftest'ine bagimli degil).

Bu dizin `tests/unit/ocr` disinda oldugu icin sefin `tests/unit/ocr/conftest.py`
bariyeri burada YUKLENMEZ. Mercek B'nin testleri sahte fabrikayla kosar ama
bir hata olursa gercek kutuphaneye kaymasin diye bariyer burada bagimsiz
bir uygulamayla yeniden kurulur. Ayrica conftest yuklendigi anda
`sys.modules`'ta yasak koklerden biri var miydi -- KAYDEDILIR (B3: "sys.modules
onceden dolu" kacisi olculur, varsayilmaz).
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
BARIYER_MESAJI = "tester-B K1 bariyeri"

# B3 olcumu: bariyer kurulmadan ONCE sys.modules'ta yasak kok var miydi?
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
    sys.meta_path.insert(0, BARIYER)
