"""T-005 · `src/capture/service.py` -- CaptureService (K1-K13).

Butun testler `FakeBackend` ile kosar; gercek ekrana ve gercek `mss`'e
dokunulmaz (K1 engeli `conftest.py`'de). `MssBackend`'in gercek `mss`
davranisi `.agents/tasks/T-005/headless_check.py` §3 ile denetlenir.
"""
from __future__ import annotations

import json
import math
import statistics
import time
import typing
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict
from typing import Any

import numpy as np
import pytest

from src.capture.service import (
    CaptureBackend,
    CaptureService,
    FakeBackend,
    MssBackend,
)
from src.contracts.errors import CaptureError
from src.contracts.models import Frame, Rect

# Bu makinenin GERCEK duzeni (sef olctu): sol monitor NEGATIF x'te ve
# birincil DEGIL. `Rect`'in varsayilan `monitor_index=0` degeri bu duzende
# birincil olmayan sol monitoru gosterir -- K4'un tuzagi tam burasi.
M_SOL = Rect(-2560, 0, 2560, 1440)
M_SAG = Rect(0, 0, 2560, 1440)
GERCEK_DUZEN = (M_SOL, M_SAG)

SABIT_SAAT = 1234.5


def _saat(deger: float = SABIT_SAAT) -> Callable[[], float]:
    return lambda: deger


def _kur(
    monitors: tuple[Rect, ...] = GERCEK_DUZEN,
    image_factory: Callable[[Rect], Any] | None = None,
    clock: Callable[[], float] | None = None,
) -> tuple[CaptureService, FakeBackend]:
    fb = FakeBackend(monitors) if image_factory is None else FakeBackend(monitors, image_factory)
    return CaptureService(fb, clock or _saat()), fb


def _ham(rects: Sequence[Rect]) -> list[Mapping[str, object]]:
    """`rects`'ten ham `mss` listesi kurar ([0] birlesim girdisi dahil)."""
    if not rects:
        return [{"left": 0, "top": 0, "width": 0, "height": 0}]
    x = min(r.x for r in rects)
    y = min(r.y for r in rects)
    sag = max(r.right for r in rects)
    alt = max(r.bottom for r in rects)
    ham: list[Mapping[str, object]] = [{"left": x, "top": y, "width": sag - x, "height": alt - y}]
    for r in rects:
        ham.append({"left": r.x, "top": r.y, "width": r.w, "height": r.h})
    return ham


# ==========================================================================
# K1 -- backend enjeksiyonu, protokol uyumu, tembellik
# ==========================================================================


def test_k1_protokol_uyumu_calisma_zamaninda() -> None:
    protokol = typing.runtime_checkable(CaptureBackend)
    assert isinstance(FakeBackend(()), protokol)
    assert isinstance(MssBackend(), protokol)


def test_k1_mss_backend_yapimi_mss_e_dokunmaz() -> None:
    """K10: `__init__` tembeldir -- K1 engeli altinda bile kurulabilir."""
    b = MssBackend()
    with b as ic:
        assert ic is b
    b.close()  # idempotent, tutamac hic kurulmadi


def test_k1_clock_enjeksiyonu_captured_at_i_belirler() -> None:
    servis, _ = _kur(clock=_saat(99.25))
    assert servis.capture_region(Rect(0, 0, 10, 10)).captured_at == 99.25


def test_k1_varsayilan_saat_monotonic() -> None:
    servis = CaptureService(FakeBackend(GERCEK_DUZEN))
    once = time.monotonic()
    kare = servis.capture_region(Rect(0, 0, 10, 10))
    assert once <= kare.captured_at <= time.monotonic()


def test_k1_fake_backend_varsayilan_ureticisi_bgra_sifir_dizi() -> None:
    """K1 bicim sozlesmesi: varsayilan `image_factory` -> `(rect.h, rect.w, 4)`.

    Bu olcu tur 1'de YOKTU: sekli `(h, w, 3)` yapan bir varsayilan uretici bes
    kabul komutundan da geciyordu (Tester-D olctu). `h != w` secildi ki
    devrik (`(w, h, 4)`) bir uretici de dussun.
    """
    r = Rect(0, 0, 4, 3)
    dizi = FakeBackend((r,)).grab(r)
    assert dizi.shape == (3, 4, 4), (
        f"varsayilan uretici (rect.h, rect.w, 4) dondurmeli, gelen {dizi.shape}"
    )
    assert dizi.dtype == np.uint8
    assert not dizi.any(), "varsayilan uretici SIFIR dizi dondurmeli"


# ==========================================================================
# K2 -- kare sira numarasi
# ==========================================================================


def test_k2_ilk_yakalama_sifir() -> None:
    servis, _ = _kur()
    assert servis.capture_region(Rect(0, 0, 10, 10)).seq == 0


def test_k2_ardisik_yakalamalar_birer_artar() -> None:
    servis, _ = _kur()
    assert [servis.capture_region(Rect(0, 0, 10, 10)).seq for _ in range(4)] == [0, 1, 2, 3]


def test_k2_sinif_a_seq_tuketmez() -> None:
    servis, _ = _kur()
    assert servis.capture_region(Rect(0, 0, 10, 10)).seq == 0
    with pytest.raises(CaptureError):
        servis.capture_region(Rect(-99999, 0, 10, 10))  # OUTSIDE
    assert servis.capture_region(Rect(0, 0, 10, 10)).seq == 1


def test_k2_sinif_b_seq_tuketmez() -> None:
    kaynak: list[Any] = [None]

    def uretici(rect: Rect) -> Any:
        if kaynak[0] == "patlat":
            raise RuntimeError("backend coktu")
        return np.zeros((rect.h, rect.w, 4), dtype=np.uint8)

    servis, _ = _kur(image_factory=uretici)
    assert servis.capture_region(Rect(0, 0, 10, 10)).seq == 0
    kaynak[0] = "patlat"
    with pytest.raises(CaptureError):
        servis.capture_region(Rect(0, 0, 10, 10))
    kaynak[0] = None
    assert servis.capture_region(Rect(0, 0, 10, 10)).seq == 1


def test_k2_sinif_c_seq_tuketmez() -> None:
    kaynak: list[Any] = [None]

    def uretici(rect: Rect) -> Any:
        if kaynak[0] == "bozuk":
            return None
        return np.zeros((rect.h, rect.w, 4), dtype=np.uint8)

    servis, _ = _kur(image_factory=uretici)
    assert servis.capture_region(Rect(0, 0, 10, 10)).seq == 0
    kaynak[0] = "bozuk"
    with pytest.raises(CaptureError):
        servis.capture_region(Rect(0, 0, 10, 10))
    kaynak[0] = None
    assert servis.capture_region(Rect(0, 0, 10, 10)).seq == 1


def test_k2_refresh_seq_i_sifirlamaz() -> None:
    servis, _ = _kur()
    servis.capture_region(Rect(0, 0, 10, 10))
    servis.capture_region(Rect(0, 0, 10, 10))
    servis.refresh_monitors()
    assert servis.capture_region(Rect(0, 0, 10, 10)).seq == 2


def test_k2_yeni_ornek_sifirdan_baslar() -> None:
    servis, fb = _kur()
    servis.capture_region(Rect(0, 0, 10, 10))
    servis.capture_region(Rect(0, 0, 10, 10))
    yeni = CaptureService(fb, _saat())
    assert yeni.capture_region(Rect(0, 0, 10, 10)).seq == 0


# ==========================================================================
# K3 -- servis DPI'ye kordur
# ==========================================================================


@pytest.mark.parametrize("olcek", [1.0, 1.25, 1.5, 2.0])
def test_k3_dpi_scale_backend_kutusunu_degistirmez(olcek: float) -> None:
    servis, fb = _kur()
    servis.capture_region(Rect(100, 200, 300, 150, monitor_index=1, dpi_scale=olcek))
    (giden,) = fb.grab_rects
    assert (giden.x, giden.y, giden.w, giden.h) == (100, 200, 300, 150)


def test_k3_dort_olcek_ayni_kutuyu_uretir() -> None:
    servis, fb = _kur()
    for olcek in (1.0, 1.25, 1.5, 2.0):
        servis.capture_region(Rect(100, 200, 300, 150, dpi_scale=olcek))
    kutular = {(r.x, r.y, r.w, r.h) for r in fb.grab_rects}
    assert kutular == {(100, 200, 300, 150)}


def test_k3_inside_kutusu_cagiranin_verdigiyle_birebir() -> None:
    servis, fb = _kur()
    for r in (Rect(-2560, 0, 64, 16), Rect(-1, 0, 2, 2), Rect(0, 0, 2560, 1440)):
        servis.capture_region(r)
    assert [(g.x, g.y, g.w, g.h) for g in fb.grab_rects] == [
        (-2560, 0, 64, 16), (-1, 0, 2, 2), (0, 0, 2560, 1440),
    ]


def test_k3_backend_kutusu_duz_int_tasir() -> None:
    """Backend'e giden kutuda numpy skaleri OLMAZ -- TIP KIMLIGIYLE olculur.

    Diger `test_k3_*` olculeri `==` ile yazilmistir ve bu sizintiyi
    **goremez**: `Rect(np.int64(100), ...) == Rect(100, ...)` `True` doner,
    hash'ler esittir, demet/kume karsilastirmasi da esittir (Tester-D olctu;
    kutuya numpy sizdiran bir uygulama butun `==` tabanli K3 olculerini
    geciyordu). Ayirt eden tek gozlem `type(x) is int`.

    Dort tip birden kosuluyor (PROTOKOL §4.6/7): yalnizca `int64`'u
    duzlestiren bir uygulama tek tipli bir olcuyu gecer.
    """
    for tip in (np.int64, np.int32, np.uint8, np.uint16):
        servis, fb = _kur()
        servis.capture_region(Rect(tip(100), tip(50), tip(120), tip(80)))
        (giden,) = fb.grab_rects
        assert (giden.x, giden.y, giden.w, giden.h) == (100, 50, 120, 80), tip.__name__
        for ad in ("x", "y", "w", "h"):
            deger = getattr(giden, ad)
            assert type(deger) is int, (
                f"{tip.__name__} girdisinde backend kutusunun `{ad}` alani "
                f"{type(deger).__name__} -- duz `int` olmali; `==` bu sizintiyi "
                f"goremez, `Rect` serilesirken `json.dumps` TypeError verir"
            )


# ==========================================================================
# K4 -- bolge dogrulama, her zaman birlesime gore
# ==========================================================================


def test_k4_kirpma_birlesime_gore() -> None:
    """Iki monitore yayilan 5300w bolge: TEK monitore kirpma 2560 verirdi."""
    servis, _ = _kur()
    kare = servis.capture_region(Rect(-2600, 0, 5300, 100))
    assert kare.rect.w == 5120


@pytest.mark.parametrize(
    ("girdi", "beklenen"),
    [
        (Rect(-2600, 0, 100, 100), (-2560, 0, 60, 100)),      # sol
        (Rect(2500, 0, 100, 100), (2500, 0, 60, 100)),        # sag
        (Rect(100, -50, 100, 100), (100, 0, 100, 50)),        # ust
        (Rect(100, 1400, 100, 100), (100, 1400, 100, 40)),    # alt
        (Rect(-2600, -50, 100, 100), (-2560, 0, 60, 50)),     # kose
        (Rect(-2600, 0, 5300, 100), (-2560, 0, 5120, 100)),   # yayilan + tasan
    ],
    ids=["sol", "sag", "ust", "alt", "kose", "yayilan"],
)
def test_k4_partial_kirpilir(girdi: Rect, beklenen: tuple[int, int, int, int]) -> None:
    servis, fb = _kur()
    kare = servis.capture_region(girdi)
    assert (kare.rect.x, kare.rect.y, kare.rect.w, kare.rect.h) == beklenen
    (giden,) = fb.grab_rects
    assert (giden.x, giden.y, giden.w, giden.h) == beklenen


@pytest.mark.parametrize("indeks", [0, 1, 7])
def test_k4_monitor_index_girdisi_karari_degistirmez(indeks: int) -> None:
    """Karar yalnizca x,y,w,h ile verilir; cagiranin `monitor_index`'i yok sayilir."""
    servis, _ = _kur()
    kare = servis.capture_region(Rect(-2600, 0, 100, 100, monitor_index=indeks))
    assert (kare.rect.x, kare.rect.y, kare.rect.w, kare.rect.h) == (-2560, 0, 60, 100)


@pytest.mark.parametrize("indeks", [0, 1, 7])
def test_k4_inside_monitor_index_girdisinden_bagimsiz(indeks: int) -> None:
    servis, fb = _kur()
    servis.capture_region(Rect(-2000, 100, 100, 100, monitor_index=indeks))
    (giden,) = fb.grab_rects
    assert (giden.x, giden.y, giden.w, giden.h) == (-2000, 100, 100, 100)


def test_k4_backend_cagrisi_yok_tamamen_disarida() -> None:
    servis, fb = _kur()
    with pytest.raises(CaptureError):
        servis.capture_region(Rect(-5000, 0, 100, 100))
    assert fb.grab_calls == 0


@pytest.mark.parametrize(
    "girdi",
    [Rect(0, 0, 0, 100), Rect(0, 0, 100, 0), Rect(0, 0, -10, 100), Rect(0, 0, 100, -10)],
    ids=["w0", "h0", "w_negatif", "h_negatif"],
)
def test_k4_backend_cagrisi_yok_sifir_negatif_alan(girdi: Rect) -> None:
    servis, fb = _kur()
    with pytest.raises(CaptureError):
        servis.capture_region(girdi)
    assert fb.grab_calls == 0


def test_k4_backend_cagrisi_yok_bos_monitor_kumesi() -> None:
    servis, fb = _kur(monitors=())
    with pytest.raises(CaptureError):
        servis.capture_region(Rect(0, 0, 10, 10))
    with pytest.raises(CaptureError):
        servis.capture_full(0)
    assert fb.grab_calls == 0


def test_k4_bos_monitor_kumesiyle_servis_kurulur() -> None:
    servis, _ = _kur(monitors=())
    assert servis.monitors == ()


def test_k4_l_duzeninde_olu_alana_degen_bolge() -> None:
    """L duzeni: birlesim dikdortgeni hicbir monitore dusmeyen alan icerir."""
    servis, _ = _kur(monitors=(Rect(0, 0, 100, 100), Rect(100, 100, 100, 100)))
    kare = servis.capture_region(Rect(90, 50, 20, 20))
    assert (kare.rect.x, kare.rect.y, kare.rect.w, kare.rect.h) == (90, 50, 20, 20)


# ==========================================================================
# K5 -- monitor anlik goruntusu (servis tarafi)
# ==========================================================================


def test_k5_yapimda_bozuk_sozluk() -> None:
    fb = FakeBackend((Rect(0, 0, 100, 100),))
    fb.raw_override = [
        {"left": 0, "top": 0, "width": 100, "height": 100},
        {"left": None, "top": 0, "width": 100, "height": 100},
    ]
    with pytest.raises(CaptureError):
        CaptureService(fb, _saat())


def test_k5_refresh_hatasi_eski_kumeyi_korur() -> None:
    servis, fb = _kur()
    eski = servis.monitors
    fb.raw_override = [
        {"left": 0, "top": 0, "width": 100, "height": 100},
        {"left": 0, "top": 0, "width": "2560", "height": 100},
    ]
    with pytest.raises(CaptureError):
        servis.refresh_monitors()
    assert servis.monitors == eski
    assert servis.capture_region(Rect(-2600, 0, 100, 100)).rect.w == 60


def test_k5_monitors_cagri_sayaci() -> None:
    servis, fb = _kur()
    for _ in range(100):
        servis.capture_region(Rect(0, 0, 10, 10))
    assert fb.monitors_calls == 1
    servis.refresh_monitors()
    assert fb.monitors_calls == 2


def test_k5_capture_full_monitors_cagirmaz() -> None:
    servis, fb = _kur()
    for _ in range(10):
        servis.capture_full(0)
    assert fb.monitors_calls == 1


def test_k5_sira_degisimi_kirpmayi_degistirmez_metadatayi_degistirir() -> None:
    servis, fb = _kur()
    once = servis.capture_region(Rect(-2600, 0, 100, 100))
    assert (once.rect.x, once.rect.y, once.rect.w, once.rect.h) == (-2560, 0, 60, 100)
    assert once.rect.monitor_index == 0

    fb.raw_override = _ham([M_SAG, M_SOL])  # sira TERS
    servis.refresh_monitors()
    sonra = servis.capture_region(Rect(-2600, 0, 100, 100))
    assert (sonra.rect.x, sonra.rect.y, sonra.rect.w, sonra.rect.h) == (-2560, 0, 60, 100)
    assert sonra.rect.monitor_index == 1  # degisen YALNIZCA metadata


def test_k5_refresh_kume_kuculunce_bolge_gecersizlesir() -> None:
    servis, fb = _kur()
    assert servis.capture_region(Rect(-2000, 0, 100, 100)).rect.w == 100
    fb.raw_override = _ham([M_SAG])
    servis.refresh_monitors()
    assert servis.monitors == (Rect(0, 0, 2560, 1440, monitor_index=0, dpi_scale=1.0),)
    with pytest.raises(CaptureError):
        servis.capture_region(Rect(-2000, 0, 100, 100))


def test_k5_refresh_yeni_kumeyi_dondurur() -> None:
    servis, fb = _kur()
    fb.raw_override = _ham([M_SAG])
    assert servis.refresh_monitors() == servis.monitors


# ==========================================================================
# K6 -- yeniden deneme taksonomisi (3x3 matris)
# ==========================================================================


def _patlayan(mesaj: str = "backend coktu") -> Callable[[Rect], Any]:
    def uretici(rect: Rect) -> Any:
        raise RuntimeError(mesaj)

    return uretici


def test_k6_a_cagri_sayisi() -> None:
    servis, fb = _kur()
    with pytest.raises(CaptureError):
        servis.capture_region(Rect(-5000, 0, 10, 10))
    assert fb.grab_calls == 0


def test_k6_a_seq() -> None:
    servis, _ = _kur()
    with pytest.raises(CaptureError):
        servis.capture_region(Rect(-5000, 0, 10, 10))
    assert servis.capture_region(Rect(0, 0, 10, 10)).seq == 0


def test_k6_a_cause() -> None:
    servis, _ = _kur()
    with pytest.raises(CaptureError) as ex:
        servis.capture_region(Rect(-5000, 0, 10, 10))
    assert ex.value.__cause__ is None


def test_k6_b_cagri_sayisi() -> None:
    servis, fb = _kur(image_factory=_patlayan())
    with pytest.raises(CaptureError):
        servis.capture_region(Rect(0, 0, 10, 10))
    assert fb.grab_calls == 3


def test_k6_b_seq() -> None:
    sayac = [0]

    def uretici(rect: Rect) -> Any:
        sayac[0] += 1
        if sayac[0] <= 3:
            raise RuntimeError("backend coktu")
        return np.zeros((rect.h, rect.w, 4), dtype=np.uint8)

    servis, _ = _kur(image_factory=uretici)
    with pytest.raises(CaptureError):
        servis.capture_region(Rect(0, 0, 10, 10))
    assert servis.capture_region(Rect(0, 0, 10, 10)).seq == 0  # hic seq tuketilmedi


def test_k6_b_cause() -> None:
    servis, _ = _kur(image_factory=_patlayan("ucuncu"))
    with pytest.raises(CaptureError) as ex:
        servis.capture_region(Rect(0, 0, 10, 10))
    assert isinstance(ex.value.__cause__, RuntimeError)
    assert str(ex.value.__cause__) == "ucuncu"


def test_k6_b_mesaj_rect_ve_deneme_sayisi() -> None:
    servis, _ = _kur(image_factory=_patlayan())
    with pytest.raises(CaptureError) as ex:
        servis.capture_region(Rect(11, 22, 33, 44))
    mesaj = str(ex.value)
    for parca in ("11", "22", "33", "44", "3"):
        assert parca in mesaj


def _gecersiz(rect: Rect) -> Any:
    return np.zeros((3, 3, 3), dtype=np.uint8)  # boyut uyusmuyor


def test_k6_c_cagri_sayisi() -> None:
    servis, fb = _kur(image_factory=_gecersiz)
    with pytest.raises(CaptureError):
        servis.capture_region(Rect(0, 0, 10, 10))
    assert fb.grab_calls == 1  # yeniden deneme YOK


def test_k6_c_seq() -> None:
    sayac = [0]

    def uretici(rect: Rect) -> Any:
        sayac[0] += 1
        if sayac[0] == 1:
            return np.zeros((3, 3, 3), dtype=np.uint8)
        return np.zeros((rect.h, rect.w, 4), dtype=np.uint8)

    servis, _ = _kur(image_factory=uretici)
    with pytest.raises(CaptureError):
        servis.capture_region(Rect(0, 0, 10, 10))
    assert servis.capture_region(Rect(0, 0, 10, 10)).seq == 0


def test_k6_c_cause() -> None:
    servis, _ = _kur(image_factory=_gecersiz)
    with pytest.raises(CaptureError) as ex:
        servis.capture_region(Rect(0, 0, 10, 10))
    assert ex.value.__cause__ is None


def test_k6_ilk_denemede_basari_tam_bir_cagri() -> None:
    servis, fb = _kur()
    servis.capture_region(Rect(0, 0, 10, 10))
    assert fb.grab_calls == 1


def test_k6_karisik_b_sonra_c() -> None:
    sayac = [0]

    def uretici(rect: Rect) -> Any:
        sayac[0] += 1
        if sayac[0] == 1:
            raise RuntimeError("once istisna")
        if sayac[0] == 2:
            return np.zeros((3, 3, 3), dtype=np.uint8)  # sonra gecersiz cikti
        return np.zeros((rect.h, rect.w, 4), dtype=np.uint8)

    servis, fb = _kur(image_factory=uretici)
    with pytest.raises(CaptureError) as ex:
        servis.capture_region(Rect(0, 0, 10, 10))
    assert fb.grab_calls == 2  # (c)'den sonra yeniden DENENMEZ
    assert ex.value.__cause__ is None  # son olay (c)
    assert servis.capture_region(Rect(0, 0, 10, 10)).seq == 0  # seq tuketilmedi


def test_k6_b_sonra_basari() -> None:
    sayac = [0]

    def uretici(rect: Rect) -> Any:
        sayac[0] += 1
        if sayac[0] == 1:
            raise RuntimeError("once istisna")
        return np.zeros((rect.h, rect.w, 4), dtype=np.uint8)

    servis, fb = _kur(image_factory=uretici)
    kare = servis.capture_region(Rect(0, 0, 10, 10))
    assert fb.grab_calls == 2
    assert kare.seq == 0  # seq TUKETILIR


# ==========================================================================
# K7 -- goruntu bicimi ve sahiplik
# ==========================================================================


def _sabit(dizi: Any) -> Callable[[Rect], Any]:
    return lambda rect: dizi


@pytest.mark.parametrize(
    "uretici",
    [
        _sabit(None),
        _sabit(np.zeros((10, 10), dtype=np.uint8)),               # ndim 2
        _sabit(np.zeros((10,), dtype=np.uint8)),                  # ndim 1
        _sabit(np.zeros((2, 10, 10, 3), dtype=np.uint8)),         # ndim 4
        _sabit(np.zeros((10, 10, 2), dtype=np.uint8)),            # kanal 2
        _sabit(np.zeros((10, 10, 5), dtype=np.uint8)),            # kanal 5
        _sabit(np.zeros((10, 10, 3), dtype=np.float32)),          # dtype float32
        _sabit(np.zeros((10, 10, 3), dtype=np.uint16)),           # dtype uint16
        _sabit(np.zeros((9, 10, 3), dtype=np.uint8)),             # boyut uyusmuyor (h)
        _sabit(np.zeros((10, 9, 3), dtype=np.uint8)),             # boyut uyusmuyor (w)
    ],
    ids=["none", "ndim2", "ndim1", "ndim4", "kanal2", "kanal5",
         "float32", "uint16", "h_uyusmuyor", "w_uyusmuyor"],
)
def test_k7_bicim_gecersiz_cikti(uretici: Callable[[Rect], Any]) -> None:
    servis, fb = _kur(image_factory=uretici)
    with pytest.raises(CaptureError):
        servis.capture_region(Rect(0, 0, 10, 10))
    assert fb.grab_calls == 1  # sinif (c): yeniden deneme yok


class _ArrayInterfaceNesnesi:
    """Gercek `mss.ScreenShot` gibi: `np.asarray` bunu SESSIZCE kabul eder."""

    def __init__(self, h: int, w: int) -> None:
        self._h, self._w = h, w
        self._tampon = bytearray(b"\x01\x02\x03\xff" * (h * w))

    @property
    def __array_interface__(self) -> dict[str, Any]:
        return {"shape": (self._h, self._w, 4), "typestr": "|u1",
                "data": self._tampon, "version": 3}


class _ArrayMetotluNesne:
    def __init__(self, h: int, w: int) -> None:
        self._dizi = np.zeros((h, w, 4), dtype=np.uint8)

    def __array__(self, dtype: Any = None, copy: Any = None) -> Any:
        return self._dizi if dtype is None else self._dizi.astype(dtype)


class _BufferNesnesi:
    """PEP 688: `__buffer__` tasiyan nesne."""

    def __init__(self, h: int, w: int) -> None:
        self._h, self._w = h, w
        self._tampon = bytearray(h * w * 4)

    def __buffer__(self, flags: int) -> memoryview:
        return memoryview(self._tampon).cast("B", (self._h, self._w, 4))


@pytest.mark.parametrize(
    "yapici",
    [
        lambda h, w: _ArrayInterfaceNesnesi(h, w),
        lambda h, w: _ArrayMetotluNesne(h, w),
        lambda h, w: memoryview(bytearray(h * w * 4)).cast("B", (h, w, 4)),
        lambda h, w: _BufferNesnesi(h, w),
    ],
    ids=["array_interface", "array_metodu", "memoryview_3b", "buffer_pep688"],
)
def test_k7_bicim_donusum_yok(yapici: Callable[[int, int], Any]) -> None:
    """Kural TIP DUZEYINDE: `isinstance(arr, np.ndarray)` degilse CaptureError.

    Dordu de `np.asarray` ile `(h,w,4) uint8` verir; girdi SAYAN bir kural
    (ornegin ikisini `hasattr` ile eleyip gerisini ceviren) burada duser.
    """
    servis, fb = _kur(image_factory=lambda rect: yapici(rect.h, rect.w))
    with pytest.raises(CaptureError):
        servis.capture_region(Rect(0, 0, 10, 10))
    assert fb.grab_calls == 1


def test_k7_bicim_bgra_dan_alfa_atilir() -> None:
    servis, _ = _kur(image_factory=lambda rect: np.full((rect.h, rect.w, 4), 7, dtype=np.uint8))
    kare = servis.capture_region(Rect(0, 0, 10, 20))
    assert kare.image.shape == (20, 10, 3)
    assert kare.image.dtype == np.uint8
    assert bool(np.all(kare.image == 7))


def test_k7_bicim_uc_kanal_oldugu_gibi() -> None:
    servis, _ = _kur(image_factory=lambda rect: np.full((rect.h, rect.w, 3), 5, dtype=np.uint8))
    kare = servis.capture_region(Rect(0, 0, 10, 20))
    assert kare.image.shape == (20, 10, 3)
    assert bool(np.all(kare.image == 5))


def test_k7_bicim_kanal_sirasi_korunur() -> None:
    """BGR duzeni: kanallar yeniden siralanmaz, yalniz alfa atilir."""
    desen = np.zeros((2, 2, 4), dtype=np.uint8)
    desen[..., 0], desen[..., 1], desen[..., 2], desen[..., 3] = 1, 2, 3, 255
    servis, _ = _kur(image_factory=_sabit(desen))
    kare = servis.capture_region(Rect(0, 0, 2, 2))
    assert list(kare.image[0, 0]) == [1, 2, 3]


def _sahiplik_iddialari(kare: Frame, kaynak: Any) -> None:
    assert np.shares_memory(kare.image, kaynak) is False
    assert kare.image.flags.writeable is True
    kopya = np.array(kaynak, copy=True)
    kare.image[0, 0, 0] = 200
    assert bool(np.array_equal(np.asarray(kaynak), kopya)), "Frame.image backend dizisini bozdu"


def test_k7_sahiplik_3kanal() -> None:
    kaynak = np.full((20, 10, 3), 5, dtype=np.uint8)
    servis, _ = _kur(image_factory=_sabit(kaynak))
    kare = servis.capture_region(Rect(0, 0, 10, 20))
    _sahiplik_iddialari(kare, kaynak)
    kaynak[:] = 9
    assert bool(np.all(kare.image[1:] == 5)), "backend dizisi onceki Frame'i bozdu"


def test_k7_sahiplik_4kanal() -> None:
    kaynak = np.full((20, 10, 4), 6, dtype=np.uint8)
    servis, _ = _kur(image_factory=_sabit(kaynak))
    kare = servis.capture_region(Rect(0, 0, 10, 20))
    _sahiplik_iddialari(kare, kaynak)
    kaynak[:] = 9
    assert bool(np.all(kare.image[1:] == 6)), "backend dizisi onceki Frame'i bozdu"


def test_k7_sahiplik_salt_okunur_kaynak() -> None:
    """Gercek `mss` yolunda `np.frombuffer(shot.bgra, ...)` boyle bir dizi uretir."""
    ham = np.frombuffer(bytes(b"\x04" * (20 * 10 * 4)), dtype=np.uint8).reshape(20, 10, 4)
    assert ham.flags.writeable is False
    servis, _ = _kur(image_factory=_sabit(ham))
    kare = servis.capture_region(Rect(0, 0, 10, 20))
    _sahiplik_iddialari(kare, ham)


# ==========================================================================
# K8 -- Frame.rect metadata'si
# ==========================================================================


def test_k8_dpi_scale_korunur_inside() -> None:
    servis, _ = _kur()
    kare = servis.capture_region(Rect(100, 100, 200, 100, dpi_scale=1.5))
    assert kare.rect.dpi_scale == 1.5


def test_k8_dpi_scale_korunur_partial() -> None:
    """`dpi.intersect` cikti metadata'si IKINCI argumandan gelir -> kullanilmaz."""
    servis, _ = _kur()
    kare = servis.capture_region(Rect(-2600, 0, 100, 100, dpi_scale=1.5))
    assert kare.rect == Rect(-2560, 0, 60, 100, monitor_index=0, dpi_scale=1.5)


def test_k8_capture_full_dpi_scale_1_0() -> None:
    servis, _ = _kur()
    assert servis.capture_full(1).rect.dpi_scale == 1.0


def test_k8_monitor_index_inside_cagiranin_degeri_yok_sayilir() -> None:
    servis, _ = _kur()
    kare = servis.capture_region(Rect(100, 100, 200, 100, monitor_index=7))
    assert kare.rect.monitor_index == 1


def test_k8_monitor_index_partial_tek_monitore_duser() -> None:
    servis, _ = _kur()
    kare = servis.capture_region(Rect(100, -50, 100, 100))
    assert (kare.rect.x, kare.rect.y, kare.rect.w, kare.rect.h) == (100, 0, 100, 50)
    assert kare.rect.monitor_index == 1


def test_k8_monitor_index_iki_monitore_yayilan_eksi_bir() -> None:
    servis, _ = _kur()
    kare = servis.capture_region(Rect(-100, 0, 200, 100))
    assert kare.rect.monitor_index == -1


def test_k8_monitor_index_l_duzeni() -> None:
    servis, _ = _kur(monitors=(Rect(0, 0, 100, 100), Rect(100, 100, 100, 100)))
    kare = servis.capture_region(Rect(90, 50, 20, 20))
    assert kare.rect.monitor_index == 0  # yalnizca A ile kesisir


@pytest.mark.parametrize("i", [0, 1])
def test_k8_monitor_index_capture_full(i: int) -> None:
    servis, _ = _kur()
    assert servis.capture_full(i).rect.monitor_index == i


@pytest.mark.parametrize(
    "deger",
    ["10", True, 10.9, float("nan"), float("inf"), np.float32(10.5)],
    ids=["str", "bool", "kusuratli", "nan", "inf", "float32_kusuratli"],
)
def test_k8_giris_tamsayi_olmayan_reddedilir(deger: Any) -> None:
    """Duzlestirme bir DONUSUMDUR: onune kabul kapisi konur (Y7-3).

    Ciplak `int()` `10.9`'u sessizce `10` yapar, `'10'`/`True`'yu kabul eder,
    `inf`/`nan` icin K6 taksonomisi disinda `OverflowError`/`ValueError` verir.
    """
    servis, fb = _kur()
    with pytest.raises(CaptureError):
        servis.capture_region(Rect(deger, 0, 100, 100))
    assert fb.grab_calls == 0


@pytest.mark.parametrize(
    "deger", ["1.5", True, None, object()], ids=["str", "bool", "none", "obj"]
)
def test_k8_giris_dpi_scale_sayi_olmayan_reddedilir(deger: Any) -> None:
    """`float('1.5')` sessizce calisirdi; kabul kapisi bunu gurultulu yapar."""
    servis, fb = _kur()
    with pytest.raises(CaptureError):
        servis.capture_region(Rect(0, 0, 100, 100, dpi_scale=deger))
    assert fb.grab_calls == 0


def test_k8_giris_dpi_scale_float32_duz_float_a_duzlesir() -> None:
    """`np.float32` JSON'a serilesmez (sef olctu) -> duz `float`'a cevrilir."""
    servis, _ = _kur()
    kare = servis.capture_region(Rect(0, 0, 100, 100, dpi_scale=np.float32(1.5)))
    assert type(kare.rect.dpi_scale) is float
    assert kare.rect.dpi_scale == pytest.approx(1.5)
    json.dumps(asdict(kare.rect))


@pytest.mark.parametrize("deger", [10.0, np.float64(10.0)], ids=["float", "float64"])
def test_k8_giris_tam_sayi_degerli_float_kabul(deger: Any) -> None:
    servis, _ = _kur()
    kare = servis.capture_region(Rect(deger, 0, 100, 100))
    assert kare.rect.x == 10
    assert type(kare.rect.x) is int


@pytest.mark.parametrize("tip", [np.int64, np.int32, np.uint8, int], ids=["int64", "int32", "uint8", "int"])
@pytest.mark.parametrize("yol", ["inside", "partial"])
def test_k8_frame_rect_alanlari_duz_int(tip: Any, yol: str) -> None:
    """INSIDE ve PARTIAL yollarinin IKISI de ayristiricidir (Y5-2/Y6-5).

    `capture_full` bacagi [OLCULMUYOR]: o yolun rect'i K5'in zaten
    duzlestirdigi monitor kumesinden gelir, numpy skaleri oraya ULASAMAZ.
    """
    servis, _ = _kur(monitors=(Rect(0, 0, 100, 100),))
    if yol == "inside":
        girdi = Rect(tip(10), tip(20), tip(30), tip(40))
        beklenen = (10, 20, 30, 40)
    else:
        girdi = Rect(tip(50), tip(50), tip(100), tip(100))
        beklenen = (50, 50, 50, 50)
    kare = servis.capture_region(girdi)
    assert (kare.rect.x, kare.rect.y, kare.rect.w, kare.rect.h) == beklenen
    assert type(kare.rect.x) is int
    assert type(kare.rect.y) is int
    assert type(kare.rect.w) is int
    assert type(kare.rect.h) is int
    assert type(kare.rect.monitor_index) is int
    assert type(kare.rect.dpi_scale) is float
    json.dumps(asdict(kare.rect))  # istisna YOK


@pytest.mark.parametrize("tip", [np.uint16, np.uint32], ids=["uint16", "uint32"])
def test_k8_monitor_index_isaretsiz_numpy(tip: Any) -> None:
    """Dondurulmus `dpi.py` isaretsiz numpy'de TASAR: `inside` yerine `partial`.

    Duzlestirme `capture_region`'in GIRISINDE yapilmazsa `monitor_index`
    sessizce yanlis cikar (sef olctu: uc `RuntimeWarning: overflow`).
    """
    servis, _ = _kur()
    kare = servis.capture_region(Rect(tip(100), tip(100), tip(200), tip(100)))
    assert (kare.rect.x, kare.rect.y, kare.rect.w, kare.rect.h) == (100, 100, 200, 100)
    assert kare.rect.monitor_index == 1


def test_k8_frame_rect_geometrisi_gercekten_yakalanan() -> None:
    servis, fb = _kur()
    kare = servis.capture_region(Rect(-2600, -50, 100, 100))
    (giden,) = fb.grab_rects
    assert (kare.rect.x, kare.rect.y, kare.rect.w, kare.rect.h) == (giden.x, giden.y, giden.w, giden.h)
    assert kare.image.shape == (kare.rect.h, kare.rect.w, 3)


# ==========================================================================
# K9 -- capture_full
# ==========================================================================


def test_k9_capture_full_ayni_rect_ve_ayni_grab_cagrisi() -> None:
    servis, fb = _kur()
    a = servis.capture_full(1)
    b = servis.capture_region(servis.monitors[1])
    g1, g2 = fb.grab_rects
    assert (g1.x, g1.y, g1.w, g1.h) == (g2.x, g2.y, g2.w, g2.h)
    assert a.rect == b.rect
    assert bool(np.array_equal(a.image, b.image))
    assert a.captured_at == b.captured_at
    assert a.seq == 0 and b.seq == 1  # seq K2 geregi ARTAR
    assert a != b  # Frame esitligi beklenmez (seq karsilastirmaya dahil)


@pytest.mark.parametrize("i", [-1, -2, 2, 3, 99])
def test_k9_aralik_disi(i: int) -> None:
    servis, fb = _kur()
    with pytest.raises(CaptureError):
        servis.capture_full(i)
    assert fb.grab_calls == 0


def test_k9_sanal_masaustu_birlesim_ile_yakalanir() -> None:
    """Sanal masaustunun tamami `capture_region(union_bbox(monitors))` ile."""
    from src.capture.monitors import union_bbox

    servis, _ = _kur()
    birlesim = union_bbox(servis.monitors)
    assert birlesim is not None
    kare = servis.capture_region(birlesim)
    assert (kare.rect.x, kare.rect.w) == (-2560, 5120)
    assert kare.rect.monitor_index == -1


# ==========================================================================
# K11 -- performans butcesi
# ==========================================================================


def test_k11_butce() -> None:
    """Servisin KENDI ek yuku: dogrulama + kirpma + kopya + Frame kurma."""
    servis, _ = _kur(monitors=(Rect(0, 0, 600, 200),))
    bolge = Rect(0, 0, 600, 200)
    servis.capture_region(bolge)  # isinma

    sureler: list[float] = []
    for _ in range(200):
        t0 = time.perf_counter()
        servis.capture_region(bolge)
        sureler.append((time.perf_counter() - t0) * 1000.0)

    medyan = statistics.median(sureler)
    sirali = sorted(sureler)
    p95 = sirali[min(len(sirali) - 1, math.ceil(0.95 * len(sirali)) - 1)]
    print(
        f"\n[K11 butce] n=200 rect=600x200 backend=(200,600,4)\n"
        f"  medyan = {medyan:.4f} ms\n"
        f"  p95    = {p95:.4f} ms\n"
        f"  min    = {sirali[0]:.4f} ms\n"
        f"  maks   = {sirali[-1]:.4f} ms\n"
        f"  butce  = 10 ms (paket budget_ms; mss.grab'in 13.5 ms'i HARIC)"
    )
    assert medyan <= 10.0, f"medyan {medyan:.4f} ms > 10 ms"
    assert p95 <= 10.0, f"p95 {p95:.4f} ms > 10 ms"


# ==========================================================================
# K10 -- MssBackend omru (baglam yoneticisi + close idempotensi)
# ==========================================================================


class _SahteTutamac:
    """`mss.MSS` gibi davranan sahte tutamac -- gercek ekrana dokunmaz.

    Gercek `mss.MSS.close()` KENDI ICINDE idempotenttir ("It is safe to call
    this multiple times"); sahte de oyle davranir ki olcu `MssBackend`'in
    KENDI idempotensini olcsun, alttaki nesneninkini degil. Ayirt eden
    gozlem sayac degil, `_tutamac`'in sifirlanmasidir.
    """

    def __init__(self) -> None:
        self.kapatma = 0
        self._kapali = False

    def close(self) -> None:
        if not self._kapali:
            self.kapatma += 1
            self._kapali = True


def test_k10_exit_uzun_omurlu_tutamaci_kapatir() -> None:
    b = MssBackend()
    t = _SahteTutamac()
    b._tutamac = t  # type: ignore[assignment]
    with b as ic:
        assert ic is b
        assert t.kapatma == 0
    assert t.kapatma == 1, (
        "__exit__ close() cagirmadi -> her `with` blogu bir window DC sizdirir "
        "(K10: 5001. kapatilmamis ornekte GetWindowDC kalici olarak duser)"
    )
    assert b._tutamac is None


def test_k10_close_tutamaci_sifirlar_ve_idempotenttir() -> None:
    b = MssBackend()
    t = _SahteTutamac()
    b._tutamac = t  # type: ignore[assignment]
    b.close()
    assert t.kapatma == 1
    assert b._tutamac is None, (
        "close() tutamaci sifirlamadi -> sonraki grab KAPATILMIS MSS'i kullanir "
        "(mss: 'Once the MSS object is closed, it may not be used again')"
    )
    b.close()
    assert t.kapatma == 1, "ikinci close() sessiz olmali (idempotent)"
