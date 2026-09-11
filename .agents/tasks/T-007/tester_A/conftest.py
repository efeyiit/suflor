"""Tester-A (mercek A) — kendi başına ayakta duran K1 bariyeri + sys.path.

Şefin `tests/unit/translate/conftest.py` bariyerine YASLANMAZ: bu dizin tek
başına koşulduğunda da (`pytest .agents/tasks/T-007/tester_A -q`) `ctranslate2*`
ve `sentencepiece*` import girişimi `RuntimeError("... K1 bariyeri ...")` ile
kesilir. Şefin dizini ile birlikte koşulduğunda iki bariyer de aynı deseni
("K1 bariyeri") taşır; hangisi önce ateşlerse ateşlesin `match="K1 bariyeri"`
tutar. Pozitif kontrol: `test_a0_bariyer_atesliyor`.

Depo kökü `sys.path`e eklenir ki `src.*` mutlak import edilebilsin.
`TESTER_A_KOK` ortam değişkeni verilirse kök ORADAN alınır (mutant kiti:
`src/` kopyası mutasyona uğratılıp aynı testler ona karşı koşulur).
"""
from __future__ import annotations

import importlib.abc
import importlib.machinery
import os
import sys
from pathlib import Path

_KOK = Path(__file__).resolve()
while _KOK.name and not (_KOK / ".agents").is_dir():
    _KOK = _KOK.parent
_KOK = Path(os.environ.get("TESTER_A_KOK") or _KOK).resolve()
if str(_KOK) in sys.path:
    sys.path.remove(str(_KOK))
sys.path.insert(0, str(_KOK))

_YASAK = ("ctranslate2", "sentencepiece")


class _TesterABariyer(importlib.abc.MetaPathFinder):
    """`ctranslate2`/`sentencepiece` import'unu bu test sürecinde keser (tester-A'nın kendi nöbetçisi)."""

    ates_sayaci = 0

    def find_spec(
        self, fullname: str, path: object = None, target: object = None
    ) -> importlib.machinery.ModuleSpec | None:
        if fullname.split(".", 1)[0] in _YASAK:
            type(self).ates_sayaci += 1
            raise RuntimeError(
                f"T-007 K1 bariyeri (tester-A nöbetçisi): {fullname!r} birim testte import edilemez; "
                "gerçek model yalnız ayrı süreçte ölçülür"
            )
        return None


if not any(isinstance(f, _TesterABariyer) for f in sys.meta_path):
    sys.meta_path.insert(0, _TesterABariyer())

# Toplama öncesi ek güvence: daha önce yüklenmiş bir kopya varsa dışarı at.
for _ad in list(sys.modules):
    if _ad.split(".", 1)[0] in _YASAK:
        del sys.modules[_ad]
