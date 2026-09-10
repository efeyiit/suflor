"""MERCEK C -- kor tester kosum kosullari.

Bu dizin `tests/` altinda DEGIL, bu yuzden `tests/unit/capture/conftest.py`'nin
K1 engeli buraya ULASMAZ. Ayni engel burada YENIDEN kurulur: gercek `mss`
modulu bu testlerde erisilemez ve bir sizinti sessiz degil GURULTULU duser.

Gerekce (K1): gercek `mss.MSS()` process DPI politikasini geri alinamaz
bicimde degistirir ve CI'da ekran yoktur. `MssBackend`'in omru bu yuzden
testle degil, ALT SURECTE kurulan bir casus modulle olculur
(`test_c_mss_omru.py`; `headless_check.py` §3'un yaptigi gibi).
"""
from __future__ import annotations

import sys
import types
from collections.abc import Iterator
from pathlib import Path

import pytest

# .agents/tasks/T-005/tester_C/conftest.py -> parents[4] depo KOKUDUR
# ([0]=tester_C, [1]=T-005, [2]=tasks, [3]=.agents, [4]=kok). Depoda
# `pytest.ini` yok ve bu dizin bir paket degil; baska bir calisma dizininden
# kosuldugunda `src.*` yalnizca bu ekleme sayesinde bulunur.
_KOK = Path(__file__).resolve().parents[4]
if str(_KOK) not in sys.path:
    sys.path.insert(0, str(_KOK))


def _gercek_mss_cagrildi(*_args: object, **_kwargs: object) -> object:
    raise AssertionError("gercek mss testte yasak (MERCEK C engeli)")


@pytest.fixture(scope="session", autouse=True)
def mercek_c_mss_engeli() -> Iterator[None]:
    """Oturum boyunca `import mss` gercek modulu DEGIL bos bir engeli verir."""
    onceki = sys.modules.get("mss")
    engel = types.ModuleType("mss")
    engel.MSS = _gercek_mss_cagrildi  # type: ignore[attr-defined]
    engel.mss = _gercek_mss_cagrildi  # type: ignore[attr-defined]
    sys.modules["mss"] = engel
    try:
        yield
    finally:
        if onceki is None:
            sys.modules.pop("mss", None)
        else:
            sys.modules["mss"] = onceki
