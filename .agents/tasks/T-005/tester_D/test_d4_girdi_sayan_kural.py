"""D4 -- Girdi SAYARAK yazilmis kural var mi?

Sayim kacinilmaz olarak anahtar deligi acar. K7'nin "`np.ndarray` degilse"
degismezi icin en az DORT ayrisan bicim var; ucunu `hasattr` ile reddedip
birini `np.asarray` ile ceviren bir uygulama, uc bicimi sayan bir olcuyu gecer.

Burada:
  (a) dort bicimin GERCEKTEN ayristigi bagimsiz kanalla gosterilir
      (`np.asarray` dordunu de sessizce `(h,w,4) uint8` yapiyor);
  (b) servis dordunu de reddediyor mu;
  (c) girdi SAYAN bir uygulama (M03) kapiya takiliyor mu;
  (d) K5'in tamsayi kabul kurali da tip duzeyinde mi (dort numpy tipi).
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pytest

from src.capture.monitors import rects_from_mss_monitors
from src.capture.service import CaptureService, FakeBackend
from src.contracts.errors import CaptureError
from src.contracts.models import Rect

SERVICE = "src/capture/service.py"
DUZEN = (Rect(-2560, 0, 2560, 1440), Rect(0, 0, 2560, 1440))


class _ArrayInterface:
    def __init__(self, h: int, w: int) -> None:
        self._h, self._w = h, w
        self._t = bytearray(b"\x01\x02\x03\xff" * (h * w))

    @property
    def __array_interface__(self) -> dict[str, Any]:
        return {"shape": (self._h, self._w, 4), "typestr": "|u1",
                "data": self._t, "version": 3}


class _ArrayMetodu:
    def __init__(self, h: int, w: int) -> None:
        self._d = np.zeros((h, w, 4), dtype=np.uint8)

    def __array__(self, dtype: Any = None, copy: Any = None) -> Any:
        return self._d if dtype is None else self._d.astype(dtype)


class _Buffer:
    def __init__(self, h: int, w: int) -> None:
        self._h, self._w = h, w
        self._t = bytearray(h * w * 4)

    def __buffer__(self, flags: int) -> memoryview:
        return memoryview(self._t).cast("B", (self._h, self._w, 4))


BICIMLER = [
    ("array_interface", lambda h, w: _ArrayInterface(h, w)),
    ("array_metodu", lambda h, w: _ArrayMetodu(h, w)),
    ("memoryview_3b", lambda h, w: memoryview(bytearray(h * w * 4)).cast("B", (h, w, 4))),
    ("buffer_pep688", lambda h, w: _Buffer(h, w)),
]


@pytest.mark.parametrize("ad,yapici", BICIMLER, ids=[a for a, _ in BICIMLER])
def test_d4_dort_bicim_np_asarray_ile_AYRISIYOR(ad: str, yapici: Any) -> None:
    """Bagimsiz kanal: dordu de sessizce (h,w,4) uint8 oluyor -> gercekten ayrisan girdiler."""
    a = np.asarray(yapici(4, 6))
    assert a.shape == (4, 6, 4) and a.dtype == np.uint8, (
        f"{ad} np.asarray ile sessizce kabul edilmiyor -> ayrisan girdi degil"
    )
    assert not isinstance(yapici(4, 6), np.ndarray)


@pytest.mark.parametrize("ad,yapici", BICIMLER, ids=[a for a, _ in BICIMLER])
def test_d4_servis_dordunu_de_REDDEDER(ad: str, yapici: Any) -> None:
    fb = FakeBackend(DUZEN, lambda r: yapici(r.h, r.w))
    servis = CaptureService(fb, lambda: 0.0)
    with pytest.raises(CaptureError):
        servis.capture_region(Rect(0, 0, 6, 4))
    assert fb.grab_calls == 1, "sinif (c) yeniden denendi"


def test_d4_GIRDI_SAYAN_uygulama_kapiya_takilir(ayna) -> None:  # type: ignore[no-untyped-def]
    """M03: iki bicimi `hasattr` ile eleyip gerisini `np.asarray` ile ceviren uygulama."""
    ayna.geri_al()
    ayna.yaz(SERVICE, [
        ("        if not isinstance(ham, np.ndarray):",
         "        if hasattr(ham, '__array_interface__') or hasattr(ham, '__array__'):"),
        ("        if ham.ndim != 3:",
         "        ham = ham if isinstance(ham, np.ndarray) else np.asarray(ham)\n"
         "        if ham.ndim != 3:"),
    ])
    try:
        s = ayna.kapilar(["G2-pytest"])
        assert s["G2-pytest"] != 0, (
            "girdi SAYAN uygulama kabul komutu #2'den GECTI -> K7 olcusu dort "
            "ayrisan bicimi birlikte parametrelemiyor demektir"
        )
        assert "test_k7_bicim_donusum_yok" in s["G2-pytest::cikti"]
    finally:
        ayna.geri_al()


@pytest.mark.parametrize("tip", [np.int64, np.int32, np.uint8, np.int16, np.uint32],
                         ids=["int64", "int32", "uint8", "int16", "uint32"])
def test_d4_K5_tamsayi_kabulu_TIP_duzeyinde(tip: Any) -> None:
    """Paket dort tipte olcuyor; burada BES tipte -- kural sayim degil, tip duzeyi olmali."""
    ham = [{"left": 0, "top": 0, "width": 1, "height": 1},
           {"left": tip(10), "top": tip(20), "width": tip(30), "height": tip(40)}]
    (r,) = rects_from_mss_monitors(ham)
    assert (r.x, r.y, r.w, r.h) == (10, 20, 30, 40)
    assert type(r.x) is int and type(r.y) is int
    assert type(r.w) is int and type(r.h) is int, (
        f"{tip.__name__} duzlestirilmedi -> kural girdi sayarak yazilmis"
    )


# uint8 icin de gecerli KUCUK duzen: butun degerler <= 60 kalir, boylece
# ayni geometri BES tipte de kurulabilir (uint8 tavani 255).
DUZEN_KUCUK = (Rect(0, 0, 20, 20), Rect(20, 0, 20, 20))


@pytest.mark.parametrize("tip", [np.int64, np.int32, np.uint8, np.int16, np.uint32],
                         ids=["int64", "int32", "uint8", "int16", "uint32"])
@pytest.mark.parametrize("yol", ["inside", "partial"])
def test_d4_K8_giris_duzlestirmesi_TIP_duzeyinde(tip: Any, yol: str) -> None:
    """`Frame.rect` alanlari BES numpy tipinde de duz `int` olmali (paket dortte olcuyor)."""
    import json
    from dataclasses import asdict

    ham = (2, 2, 10, 10) if yol == "inside" else (30, 2, 20, 10)  # partial: x+w=50 > 40
    fb = FakeBackend(DUZEN_KUCUK)
    servis = CaptureService(fb, lambda: 0.0)
    kare = servis.capture_region(Rect(tip(ham[0]), tip(ham[1]), tip(ham[2]), tip(ham[3])))
    if yol == "partial":
        assert (kare.rect.w, kare.rect.x) == (10, 30), "PARTIAL yolu kurulamadi"
    for alan in ("x", "y", "w", "h"):
        assert type(getattr(kare.rect, alan)) is int, (
            f"{yol}/{tip.__name__}: Frame.rect.{alan} duz int degil "
            f"({type(getattr(kare.rect, alan)).__name__})"
        )
    assert type(kare.rect.dpi_scale) is float
    json.dumps(asdict(kare.rect))
