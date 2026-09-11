"""TESTER-B K1 bariyeri (T-007) -- `conftest.py` bunu import eder; KENDI BASINA kurulur.

Bu dizin `tests/unit/translate` disinda oldugu icin sefin
`tests/unit/translate/conftest.py` bariyeri burada YUKLENMEZ. Mercek B'nin
testleri sahte fabrikayla kosar ama bir hata olursa gercek kutuphaneye
kaymasin diye bariyer burada bagimsiz bir uygulamayla yeniden kurulur.

Mesaj "K1 bariyeri" alt dizesini TASIR: testler `match="K1 bariyeri"` kullanir,
boylece sefin bariyeriyle BIRLIKTE kosulunca (`pytest tests/unit/translate
.agents/tasks/T-007/tester_B`) hangisi once ateslerse ateslesin `match` tutar
(T-006'da bu yanlis yapildi, 9 kirik verdi).

Ayrica conftest yuklendigi anda `sys.modules`ta yasak koklerden biri var
miydi -- KAYDEDILIR (B3: "sys.modules onceden dolu" kacisi olculur,
varsayilmaz).
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

YASAK_KOKLER: tuple[str, ...] = ("ctranslate2", "sentencepiece")
BARIYER_MESAJI = "tester-B T-007 K1 bariyeri"

ONCEDEN_YUKLU: tuple[str, ...] = tuple(
    sorted(k for k in sys.modules if k.split(".", 1)[0] in YASAK_KOKLER)
)


class TesterBBariyer(importlib.abc.MetaPathFinder):
    """`ctranslate2*` / `sentencepiece*` icin her `find_spec` sorgusunu RuntimeError ile keser."""

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
