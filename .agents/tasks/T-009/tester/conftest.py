"""T-009 kör tester (tek mercek: K11 tablosu / gercek model / regresyon) -- kendi bariyeri.

Sefin `tests/unit/ocr/conftest.py` bariyerine YASLANMAZ: bu dizin tek basina
kosuldugunda da (`pytest .agents/tasks/T-009/tester -q`) `rapidocr*` ve
`onnxruntime*` import girisimi `RuntimeError` ile kesilir. Pozitif kontrol
`test_t0_bariyer_atesliyor` (`match="K1 bariyeri"`: sefin bariyeri once
ateslerse de desen tutar).

Depo koku `sys.path`e eklenir ki `src.*` mutlak import edilebilsin.
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


class T009TesterBariyer(importlib.abc.MetaPathFinder):
    """`rapidocr`/`onnxruntime` import'unu bu test surecinde keser; sorgulari sayar."""

    def __init__(self) -> None:
        self.ates = 0

    def find_spec(
        self, fullname: str, path: object = None, target: object = None
    ) -> importlib.machinery.ModuleSpec | None:
        if fullname.split(".", 1)[0] in YASAK_KOKLER:
            self.ates += 1
            raise RuntimeError(
                f"T-009 tester K1 bariyeri: {fullname!r} birim testte import edilemez"
            )
        return None


BARIYER = T009TesterBariyer()
if not any(isinstance(f, T009TesterBariyer) for f in sys.meta_path):
    sys.meta_path.insert(0, BARIYER)

for _ad in list(sys.modules):
    if _ad.split(".", 1)[0] in YASAK_KOKLER:
        del sys.modules[_ad]
