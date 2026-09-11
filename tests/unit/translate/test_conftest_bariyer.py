"""ŞEFE AİT — T-007 K1 bariyerinin POZİTİF KONTROLÜ (PROTOKOL §4.6/10)."""
from __future__ import annotations

import importlib
import sys

import pytest


@pytest.mark.parametrize("ad", ["ctranslate2", "sentencepiece", "ctranslate2.converters"])
def test_bariyer_gercekten_atesliyor(ad: str) -> None:
    sys.modules.pop(ad, None)
    with pytest.raises(RuntimeError, match="K1 bariyeri"):
        importlib.import_module(ad)


def test_bariyer_komsulari_engellemiyor() -> None:
    importlib.import_module("numpy")
    importlib.import_module("json")
