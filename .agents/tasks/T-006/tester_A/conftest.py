"""Tester-A (mercek A) — kendi başına ayakta duran K1 bariyeri + sys.path.

Şefin `tests/unit/ocr/conftest.py` bariyerine YASLANMAZ: bu dizin tek başına
koşulduğunda da (`pytest .agents/tasks/T-006/tester_A -q`) `rapidocr*` ve
`onnxruntime*` import girişimi `RuntimeError` ile kesilir. Pozitif kontrol
`test_a0_bariyer_atesliyor` içinde (§4.6/10).

Depo kökü `sys.path`e eklenir ki `src.*` mutlak import edilebilsin.
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

_YASAK = ("rapidocr", "onnxruntime")


class _TesterABariyer(importlib.abc.MetaPathFinder):
    """`rapidocr`/`onnxruntime` import'unu bu test sürecinde keser (tester-A'nın kendi nöbetçisi)."""

    ates_sayaci = 0

    def find_spec(
        self, fullname: str, path: object = None, target: object = None
    ) -> importlib.machinery.ModuleSpec | None:
        if fullname.split(".", 1)[0] in _YASAK:
            type(self).ates_sayaci += 1
            # Mesajda "T-006 K1 bariyeri" ifadesi bilerek var: şefin pozitif kontrolü
            # (`tests/unit/ocr/test_conftest_bariyer.py`) bu desene bakar; iki dizin
            # birlikte toplandığında hangi bariyer önce ateşlerse ateşlesin desen tutar.
            raise RuntimeError(
                f"T-006 K1 bariyeri (tester-A nöbetçisi): {fullname!r} birim testte import edilemez"
            )
        return None


if not any(isinstance(f, _TesterABariyer) for f in sys.meta_path):
    sys.meta_path.insert(0, _TesterABariyer())

# Toplama öncesi ek güvence: daha önce yüklenmiş bir kopya varsa dışarı at.
for _ad in list(sys.modules):
    if _ad.split(".", 1)[0] in _YASAK:
        del sys.modules[_ad]
