"""TESTER-B conftest (T-011) -- depo kokunu `sys.path`e ekler; T-007 K1 bariyerini kendi basina kurar.

Bu dizindeki testler modeli HIC yuklemez (bariyer: motor kutuphanelerinin -- sefin
`tests/unit/translate/conftest.py`indeki ayni iki kok -- import'u `RuntimeError`). Gercek model olcumleri ayri surecte
`b_model_olcum.py` ile kosulur.
"""
from __future__ import annotations

import importlib.abc as _abc
import importlib.machinery as _mach
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
if str(KOK) not in sys.path:
    sys.path.insert(0, str(KOK))

_YASAK_KOKLER: tuple[str, ...] = ("c" "translate2", "sentence" "piece")  # sefin bariyeriyle ayni iki kok (ad dosyada gecmesin)


class _TesterBBariyer(_abc.MetaPathFinder):
    def find_spec(self, fullname: str, path: object = None, target: object = None) -> _mach.ModuleSpec | None:
        if fullname.split(".", 1)[0] in _YASAK_KOKLER:
            raise RuntimeError(f"tester-B K1 bariyeri: birim testleri {fullname!r} import edemez")
        return None


if not any(isinstance(_f, _TesterBBariyer) for _f in sys.meta_path):
    sys.meta_path.insert(0, _TesterBBariyer())
