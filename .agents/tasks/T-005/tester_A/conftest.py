"""MERCEK A test kosullari -- gercek `mss` ERISILEMEZ (K1).

Bu dizin `tests/unit/capture/` agacinin disindadir, yani oradaki engel
fixture'i buraya uygulanmaz. K1 "T-005 testleri gercek ekrana dokunmaz"
diyor; bu dizinin testleri de T-005 testidir, bu yuzden ayni engel burada
yeniden kurulur. Engel modul, uygulamanin `conftest.py`'sinin kopyasi
DEGILDIR: burada bagimsiz olarak yazilir ki denetleyen ile denetlenen ayni
kaynaktan referans turetmesin (PROTOKOL 4.6/8).

`sys.path` eklemesi: depoda `pytest.ini`/`pyproject.toml` yok ve bu dizin bir
paket degil; `src.*` mutlak import'larinin cozulmesi icin depo koku yola
konur.
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


def _yasak(*_a: object, **_k: object) -> object:
    raise AssertionError("gercek mss testte yasak (MERCEK A)")


@pytest.fixture(scope="session", autouse=True)
def mss_engeli() -> Iterator[None]:
    onceki = sys.modules.get("mss")
    engel = types.ModuleType("mss")
    engel.MSS = _yasak  # type: ignore[attr-defined]
    engel.mss = _yasak  # type: ignore[attr-defined]
    sys.modules["mss"] = engel
    try:
        yield
    finally:
        if onceki is None:
            sys.modules.pop("mss", None)
        else:
            sys.modules["mss"] = onceki
