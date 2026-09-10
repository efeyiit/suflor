"""T-005 · `src/capture/monitors.py` -- saf monitor yardimcilari (K5).

Bu dosya yalnizca SAF fonksiyonlari olcer: ham `mss` sozluk listesinden
`Rect` uretimi, bozuk sozluk taksonomisi, numpy tamsayilarinin duz `int`'e
duzlestirilmesi ve birlesim sinirlayici dikdortgeni. Servis davranisi
`test_service.py`'dedir.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
import pytest

from src.capture.monitors import list_monitors, rects_from_mss_monitors, union_bbox
from src.capture.service import FakeBackend
from src.contracts.errors import CaptureError
from src.contracts.models import Rect

# Bu makinede sefin OLCTUGU ham liste (olgular.txt [K5]); birebir gomulu.
GERCEK_HAM: list[dict[str, object]] = [
    {"left": -2560, "top": 0, "width": 5120, "height": 1440},
    {
        "left": -2560, "top": 0, "width": 2560, "height": 1440,
        "is_primary": False, "name": "Generic PnP Monitor",
        "unique_id": "\\\\?\\DISPLAY#AUS27FE#7&282f24eb&0&UID260",
    },
    {
        "left": 0, "top": 0, "width": 2560, "height": 1440,
        "is_primary": True, "name": "Generic PnP Monitor",
        "unique_id": "\\\\?\\DISPLAY#AUS27FE#7&282f24eb&0&UID264",
    },
]


# --------------------------------------------------------------------------
# K5 -- bicim
# --------------------------------------------------------------------------


def test_k5_gercek_duzen() -> None:
    """Sefin olctugu ham liste dogru cevrilir: `[0]` atilir, `[1:]` sirayla."""
    assert rects_from_mss_monitors(GERCEK_HAM) == (
        Rect(-2560, 0, 2560, 1440, monitor_index=0, dpi_scale=1.0),
        Rect(0, 0, 2560, 1440, monitor_index=1, dpi_scale=1.0),
    )


def test_k5_tek_monitor() -> None:
    ham = [
        {"left": 0, "top": 0, "width": 1920, "height": 1080},
        {"left": 0, "top": 0, "width": 1920, "height": 1080, "is_primary": True},
    ]
    assert rects_from_mss_monitors(ham) == (
        Rect(0, 0, 1920, 1080, monitor_index=0, dpi_scale=1.0),
    )


def test_k5_uc_monitor() -> None:
    ham = [
        {"left": -1920, "top": 0, "width": 5760, "height": 1080},
        {"left": -1920, "top": 0, "width": 1920, "height": 1080},
        {"left": 0, "top": 0, "width": 1920, "height": 1080},
        {"left": 1920, "top": 0, "width": 1920, "height": 1080},
    ]
    sonuc = rects_from_mss_monitors(ham)
    assert len(sonuc) == 3
    assert [r.monitor_index for r in sonuc] == [0, 1, 2]
    assert sonuc[0] == Rect(-1920, 0, 1920, 1080, monitor_index=0, dpi_scale=1.0)
    assert sonuc[2] == Rect(1920, 0, 1920, 1080, monitor_index=2, dpi_scale=1.0)


def test_k5_bos_kuyruk_bos_demet() -> None:
    """Yalnizca birlesim girdisi olan liste -> `()`."""
    assert rects_from_mss_monitors([{"left": 0, "top": 0, "width": 0, "height": 0}]) == ()


def test_k5_bos_liste_bos_demet() -> None:
    assert rects_from_mss_monitors([]) == ()


def test_k5_dpi_scale_daima_bir_nokta_sifir() -> None:
    """`mss` sozlukleri DPI olcegi TASIMAZ (sef olctu) -> hepsi 1.0."""
    for r in rects_from_mss_monitors(GERCEK_HAM):
        assert r.dpi_scale == 1.0
        assert type(r.dpi_scale) is float


def test_k5_fazladan_anahtarlar_yok_sayilir() -> None:
    ham = [
        {"left": 0, "top": 0, "width": 10, "height": 10},
        {"left": 1, "top": 2, "width": 3, "height": 4,
         "is_primary": True, "name": "X", "unique_id": "u", "beklenmeyen": object()},
    ]
    assert rects_from_mss_monitors(ham) == (Rect(1, 2, 3, 4, monitor_index=0, dpi_scale=1.0),)


# --------------------------------------------------------------------------
# K5 -- yozlasmis sozluk
# --------------------------------------------------------------------------


@pytest.mark.parametrize("eksik", ["left", "top", "width", "height"])
def test_k5_bozuk_sozluk_eksik_anahtar(eksik: str) -> None:
    m: dict[str, object] = {"left": 0, "top": 0, "width": 100, "height": 50}
    del m[eksik]
    ham = [{"left": 0, "top": 0, "width": 100, "height": 50}, m]
    with pytest.raises(CaptureError) as ex:
        rects_from_mss_monitors(ham)
    assert eksik in str(ex.value)
    assert "0" in str(ex.value)  # hangi indeks


@pytest.mark.parametrize(
    "deger",
    [None, "2560", 2560.0, 2560.5, True, False, np.bool_(True), object()],
    ids=["none", "str", "float", "float_kusurat", "bool_true", "bool_false", "np_bool", "obj"],
)
def test_k5_bozuk_sozluk_tamsayi_olmayan(deger: object) -> None:
    ham = [
        {"left": 0, "top": 0, "width": 100, "height": 50},
        {"left": 0, "top": 0, "width": deger, "height": 50},
    ]
    with pytest.raises(CaptureError) as ex:
        rects_from_mss_monitors(ham)
    assert "width" in str(ex.value)


@pytest.mark.parametrize("tip", [np.int64, np.int32, np.uint8], ids=["int64", "int32", "uint8"])
def test_k5_bozuk_sozluk_numpy_tamsayi_kabul(tip: Any) -> None:
    """`numbers.Integral` kabul: numpy tamsayilari (DXGI / numpy tabanli sahte)."""
    ham = [
        {"left": tip(0), "top": tip(0), "width": tip(100), "height": tip(50)},
        {"left": tip(10), "top": tip(20), "width": tip(30), "height": tip(40)},
    ]
    assert rects_from_mss_monitors(ham) == (Rect(10, 20, 30, 40, monitor_index=0, dpi_scale=1.0),)


def test_k5_bozuk_sozluk_indeks_bildirir() -> None:
    """Mesaj hangi monitorde bozuldugunu soyler (ikinci monitor = indeks 1)."""
    ham = [
        {"left": 0, "top": 0, "width": 100, "height": 50},
        {"left": 0, "top": 0, "width": 100, "height": 50},
        {"left": 0, "top": 0, "width": None, "height": 50},
    ]
    with pytest.raises(CaptureError) as ex:
        rects_from_mss_monitors(ham)
    assert "1" in str(ex.value)


@pytest.mark.parametrize("tip", [np.int64, np.int32, np.uint8, int], ids=["int64", "int32", "uint8", "int"])
def test_k5_numpy_tamsayi_duz_int_e_duzlestirilir(tip: Any) -> None:
    """Y-C: `Rect` alanlarina HICBIR ZAMAN numpy skaleri yazilmaz.

    Esitlik olcusu YETMEZ (`Rect(np.int64(10),...) == Rect(10,...)` -> True,
    hash esit, aritmetik dogru); sizinti yalnizca TIP KIMLIGINDE ve
    serilestirmede gorunur. Dort tipte birden kosar: yalniz `int64`'u
    duzlestiren bir uygulama tek tipli olcuyu gecer, `int32`/`uint8` sizdirir.
    """
    ham = [
        {"left": tip(0), "top": tip(0), "width": tip(100), "height": tip(50)},
        {"left": tip(10), "top": tip(20), "width": tip(30), "height": tip(40)},
    ]
    (r,) = rects_from_mss_monitors(ham)
    assert type(r.x) is int
    assert type(r.y) is int
    assert type(r.w) is int
    assert type(r.h) is int
    assert type(r.monitor_index) is int
    assert type(r.dpi_scale) is float


def test_k5_duzlestirme_json_serilesir() -> None:
    """Sizintinin gercek zarari: `json.dumps(asdict(rect))` -> TypeError."""
    import json
    from dataclasses import asdict

    ham = [
        {"left": np.int64(0), "top": np.int64(0), "width": np.int64(100), "height": np.int64(50)},
        {"left": np.int64(10), "top": np.int64(20), "width": np.int64(30), "height": np.int64(40)},
    ]
    (r,) = rects_from_mss_monitors(ham)
    assert json.loads(json.dumps(asdict(r)))["x"] == 10


# --------------------------------------------------------------------------
# K5 -- list_monitors
# --------------------------------------------------------------------------


def test_k5_list_monitors_backend_uzerinden() -> None:
    fb = FakeBackend((Rect(-2560, 0, 2560, 1440), Rect(0, 0, 2560, 1440)))
    assert list_monitors(fb) == (
        Rect(-2560, 0, 2560, 1440, monitor_index=0, dpi_scale=1.0),
        Rect(0, 0, 2560, 1440, monitor_index=1, dpi_scale=1.0),
    )


def test_k5_list_monitors_istisnayi_sarmalamaz() -> None:
    """`backend.monitors()` istisnasi OLDUGU GIBI yayilir (docstring'de)."""

    class _Patlayan:
        def monitors(self) -> Sequence[Mapping[str, object]]:
            raise RuntimeError("backend coktu")

    with pytest.raises(RuntimeError, match="backend coktu"):
        list_monitors(_Patlayan())


def test_k5_fake_backend_bicimi() -> None:
    """`FakeBackend.monitors()` HAM `mss` biciminde ve `[0]` BIRLESIM girdisi dahil.

    `[0]`'i unutan bir FakeBackend ilk monitoru sessizce yutar.
    """
    fb = FakeBackend((Rect(-2560, 0, 2560, 1440), Rect(0, 0, 2560, 1440)))
    ham = fb.monitors()
    assert len(ham) == 3
    assert dict(ham[0]) == {"left": -2560, "top": 0, "width": 5120, "height": 1440}
    assert dict(ham[1]) == {"left": -2560, "top": 0, "width": 2560, "height": 1440}
    assert dict(ham[2]) == {"left": 0, "top": 0, "width": 2560, "height": 1440}


def test_k5_fake_backend_raw_override_public_ve_canli() -> None:
    """`raw_override` PUBLIC oznitelik ve her cagrida O ANKI hali okunur."""
    fb = FakeBackend((Rect(0, 0, 100, 100),))
    assert fb.raw_override is None
    fb.raw_override = [
        {"left": 0, "top": 0, "width": 10, "height": 10},
        {"left": 1, "top": 2, "width": 3, "height": 4},
    ]
    assert len(fb.monitors()) == 2
    fb.raw_override = [{"left": 0, "top": 0, "width": 10, "height": 10}]
    assert len(fb.monitors()) == 1  # anlik goruntu ALINMAZ
    fb.raw_override = None
    assert len(fb.monitors()) == 2  # yapim kumesine geri doner


def test_k5_fake_backend_bos_kume() -> None:
    fb = FakeBackend(())
    ham = fb.monitors()
    assert len(ham) == 1  # yalnizca birlesim girdisi
    assert rects_from_mss_monitors(ham) == ()


# --------------------------------------------------------------------------
# K5 -- union_bbox
# --------------------------------------------------------------------------


def test_k5_union_bbox_negatif_x_iki_monitor() -> None:
    m = (Rect(-2560, 0, 2560, 1440, 0, 1.0), Rect(0, 0, 2560, 1440, 1, 1.0))
    assert union_bbox(m) == Rect(-2560, 0, 5120, 1440, monitor_index=-1, dpi_scale=1.0)


def test_k5_union_bbox_ters_sira_ayni_sonuc() -> None:
    m = (Rect(-2560, 0, 2560, 1440, 0, 1.0), Rect(0, 0, 2560, 1440, 1, 1.0))
    assert union_bbox(tuple(reversed(m))) == union_bbox(m)


def test_k5_union_bbox_uc_monitor() -> None:
    m = (
        Rect(-1920, 0, 1920, 1080, 0, 1.0),
        Rect(0, 0, 1920, 1080, 1, 1.0),
        Rect(1920, -200, 1920, 1080, 2, 1.0),
    )
    assert union_bbox(m) == Rect(-1920, -200, 5760, 1280, monitor_index=-1, dpi_scale=1.0)


def test_k5_union_bbox_l_duzeni() -> None:
    m = (Rect(0, 0, 100, 100, 0, 1.0), Rect(100, 100, 100, 100, 1, 1.0))
    assert union_bbox(m) == Rect(0, 0, 200, 200, monitor_index=-1, dpi_scale=1.0)


def test_k5_union_bbox_tek_monitor_ayni_geometri() -> None:
    m = (Rect(5, 7, 100, 200, 3, 1.5),)
    b = union_bbox(m)
    assert b is not None
    assert (b.x, b.y, b.w, b.h) == (5, 7, 100, 200)
    assert b.monitor_index == -1  # "birlesim, tek monitor degil" isareti
    assert b.dpi_scale == 1.0


def test_k5_union_bbox_bos_none() -> None:
    assert union_bbox(()) is None


def test_k5_union_bbox_kapsar_ve_daha_buyuk_degil() -> None:
    m = (
        Rect(-2560, 0, 2560, 1440, 0, 1.0),
        Rect(0, -300, 2560, 1440, 1, 1.0),
    )
    b = union_bbox(m)
    assert b is not None
    assert b.x == min(r.x for r in m)
    assert b.y == min(r.y for r in m)
    assert b.right == max(r.right for r in m)
    assert b.bottom == max(r.bottom for r in m)
