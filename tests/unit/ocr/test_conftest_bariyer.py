"""ŞEFE AİT — T-006 K1 bariyerinin POZİTİF KONTROLÜ (PROTOKOL §4.6/10).

Bariyer `tests/unit/ocr/conftest.py`'de modül düzeyinde kurulu. Bu dosya
bariyerin gerçekten ateşlediğini doğrular: sessizce boşalırsa burada düşer.
"""
from __future__ import annotations

import importlib
import sys

import pytest


@pytest.mark.parametrize("ad", ["rapidocr", "rapidocr.main", "onnxruntime"])
def test_bariyer_gercekten_atesliyor(ad: str) -> None:
    sys.modules.pop(ad, None)
    with pytest.raises(RuntimeError, match="T-006 K1 bariyeri"):
        importlib.import_module(ad)


def test_bariyer_baska_modulleri_engellemiyor() -> None:
    """Bariyer yalnız iki kökü keser; `numpy` gibi komşular serbest."""
    importlib.import_module("numpy")
    importlib.import_module("json")
