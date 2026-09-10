"""T-005 test kosullari: gercek `mss` modulu testlerde ERISILEMEZ (K1).

Bu dizindeki testler gercek ekrana dokunmaz. Guvence bir sozle degil, bir
ENGEL MODULLE saglanir: oturum basinda `sys.modules["mss"]` bos bir
`types.ModuleType("mss")` ile degistirilir. Engel modul:

  * gercek `mss`'e **devretmez** -- `__file__`'i yoktur ve gercek paketin
    `base`/`factory` alt modullerini tasimaz (bir kopyalama/devir olsaydi
    `import mss.base` sessizce gercek koda ulasirdi),
  * `MSS` ve `mss` oznitelikleri cagrilinca `AssertionError` firlatir --
    yani bir sizinti sessiz degil, GURULTULUDUR.

Kapsam **oturumdur** (`scope="session"`), fonksiyon/modul degil: engel
modulun kimligi dosyalar arasinda degismemelidir. Fonksiyon ya da modul
kapsaminda her dosya icin YENI bir engel modul kurulur; bir test dosyasinda
`sys.modules["mss"]`'e tutulan bir referans digerinde baska bir nesneyi
gosterir ve "engel gercekten tek mi" sorusu olculemez hale gelir.
`.agents/tasks/T-005/headless_check.py` §1 bunu iki ayri sonda dosyasiyla
denetler.

`sys.path` eklemesi: bu dizin bir paket degil ve depoda `pytest.ini` yok;
testler `src.contracts...` / `src.capture...` yollarini kullaniyor. `python -m
pytest` depo kokunden kosunca kok zaten `sys.path`'te olur, ama bu dizin tek
basina (baska bir calisma dizininden) kosuldugunda olmaz -- headless denetimi
tam olarak boyle kosar. `tests/unit/contracts/conftest.py` ayni onlemi alir.
"""
from __future__ import annotations

import sys
import types
from collections.abc import Iterator
from pathlib import Path

import pytest

_KOK = Path(__file__).resolve().parents[3]
if str(_KOK) not in sys.path:
    sys.path.insert(0, str(_KOK))


def _gercek_mss_cagrildi(*_args: object, **_kwargs: object) -> object:
    """Engel modulun `MSS` / `mss` girisleri -- cagrilirsa gurultulu duser."""
    raise AssertionError("gercek mss testte yasak")


def _engel_modul() -> types.ModuleType:
    """Gercek `mss`'in yerine gececek bos modul.

    Bilincli olarak `types.ModuleType` ile kurulur ve gercek paketten HICBIR
    sey kopyalanmaz: `__file__` yok, `base`/`factory` yok. Boylece bir
    devretme (fallback) yolu kalmaz.
    """
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
