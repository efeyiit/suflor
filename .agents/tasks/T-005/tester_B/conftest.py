"""MERCEK B (sayisal) test kosullari -- K1 engeli bu dizinde de gecerlidir.

Bu dizin `tests/unit/capture/` altinda DEGILDIR, yani oradaki oturum kapsamli
engel fixture'i buraya ULASMAZ. Tester'in testleri gercek ekrana dokunamaz
(K1), bu yuzden engel burada yeniden kurulur -- ayni bicimde: `types.ModuleType`
ile bos bir `mss`, gercek pakete devretmeyen, `MSS`/`mss` cagrilinca gurultulu
dusen.

`sys.path` eklemesi: depoda `pytest.ini`/`pyproject.toml` yok ve bu dizin bir
paket degil; `src.capture...` / `src.contracts...` yollarinin cozulmesi icin
depo koku eklenir.
"""
from __future__ import annotations

import sys
import types
from collections.abc import Iterator
from pathlib import Path

import pytest

_KOK = Path(__file__).resolve().parents[4]
if str(_KOK) not in sys.path:
    sys.path.insert(0, str(_KOK))


def _gercek_mss_cagrildi(*_args: object, **_kwargs: object) -> object:
    raise AssertionError("gercek mss testte yasak")


def _engel_modul() -> types.ModuleType:
    modul = types.ModuleType("mss")
    modul.MSS = _gercek_mss_cagrildi  # type: ignore[attr-defined]
    modul.mss = _gercek_mss_cagrildi  # type: ignore[attr-defined]
    return modul


@pytest.fixture(scope="session", autouse=True)
def gercek_mss_engeli() -> Iterator[None]:
    """K1: oturum boyunca `import mss` gercek modulu DEGIL engeli verir."""
    onceki = sys.modules.get("mss")
    sys.modules["mss"] = _engel_modul()
    try:
        yield
    finally:
        if onceki is None:
            sys.modules.pop("mss", None)
        else:
            sys.modules["mss"] = onceki
