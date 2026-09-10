"""MERCEK B -- SAYISAL: tip, tasma, duzlestirme.

*Sayilar hangi tipte akiyor; nerede sessizce baska bir seye donusuyor?*

Bu dosya `env.md`'nin MERCEK B listesindeki alti saldiri noktasini bagimsiz
olarak olcer. Iki tur test vardir ve **ayrimi bilerek yapilmistir**:

* `test_olgu_*` -- ONCE tehlikeyi kendi elimle yeniden uretir (dondurulmus
  `dpi.py`'yi ve `Rect` sozlesmesini dogrudan cagirarak). Bu testler
  uygulamayi degil, olcunun ANLAMLI oldugunu kanitlar: tehlike gercekten
  varsa, uygulamanin ondan korumasi bir sey ifade eder.
* `test_b*` -- uygulamanin o tehlikeye karsi korudugunu olcer.

Olcum araci secimi (B1): sizintiyi `==`, `hash`, `set` ve aritmetik
**GOREMEZ** -- `test_olgu_esitlik_sizintiyi_goremez` bunu kanitlar. Bu yuzden
her duzlestirme iddiasi `type(...) is int` **tip kimligiyle** ve zararin
kendisiyle (`json.dumps(asdict(...))`) olculur, esitlikle degil.
"""
from __future__ import annotations

import ast
import json
import numbers
import subprocess
import sys
import tokenize
import warnings
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from src.capture import dpi
from src.capture.monitors import list_monitors, rects_from_mss_monitors, union_bbox
from src.capture.service import CaptureService, FakeBackend
from src.contracts.errors import CaptureError
from src.contracts.models import Frame, Rect

_KOK = Path(__file__).resolve().parents[4]

# Bu makinenin GERCEK duzeni (env.md): M0 birincil DEGIL ve x'i NEGATIF.
M0 = Rect(-2560, 0, 2560, 1440, monitor_index=0, dpi_scale=1.0)
M1 = Rect(0, 0, 2560, 1440, monitor_index=1, dpi_scale=1.0)
GERCEK_DUZEN = (M0, M1)

# `np.uint8` yalnizca 0..255 tasiyabilir ve isaretsiz tipler NEGATIF koordinat
# tasiyamaz (`np.uint32(-2560)` -> `OverflowError`, daha yapimda). Dort tipin
# HEPSINDE kurulabilen kucuk, pozitif ikinci duzen; birlesim (0,0,200,100).
K0 = Rect(0, 0, 100, 100, monitor_index=0, dpi_scale=1.0)
K1 = Rect(100, 0, 100, 100, monitor_index=1, dpi_scale=1.0)
KUCUK_DUZEN = (K0, K1)

# K5/K8'in parametrelendirdigi dort tip.
DORT_TIP = [np.int64, np.int32, np.uint8, int]
DORT_TIP_ID = ["int64", "int32", "uint8", "int"]

# Dondurulmus `dpi.py`'yi tasiran isaretsiz tipler.
ISARETSIZ = [np.uint8, np.uint16, np.uint32]
ISARETSIZ_ID = ["uint8", "uint16", "uint32"]

ALANLAR = ("x", "y", "w", "h")


# ---------------------------------------------------------------------------
# yardimcilar
# ---------------------------------------------------------------------------


def _uretici(rect: Rect) -> np.ndarray:
    """`grab` icin (h, w, 4) sifir dizi -- `hedef`in boyutunu birebir izler."""
    return np.zeros((rect.h, rect.w, 4), dtype=np.uint8)


def _kur(
    monitorler: tuple[Rect, ...] = GERCEK_DUZEN,
    ham: list[dict[str, object]] | None = None,
) -> tuple[CaptureService, FakeBackend]:
    fb = FakeBackend(monitorler, _uretici, raw_override=ham)
    return CaptureService(fb, clock=lambda: 1.0), fb


def _ham_liste(tip: Any, monitorler: tuple[Rect, ...]) -> list[dict[str, object]]:
    """Ham `mss` bicimi liste; `[0]` birlesim girdisi DAHIL, degerler `tip`."""
    birlesim = union_bbox(monitorler)
    assert birlesim is not None
    return [
        {
            "left": tip(r.x),
            "top": tip(r.y),
            "width": tip(r.w),
            "height": tip(r.h),
        }
        for r in (birlesim, *monitorler)
    ]


def _tipler(rect: Rect) -> list[str]:
    return [type(getattr(rect, ad)).__name__ for ad in ALANLAR]


def _duz_int_mi(rect: Rect) -> None:
    """Tip KIMLIGI olcusu -- `isinstance` DEGIL.

    `np.int64` `int`'in alt sinifi degildir ama `isinstance(v, numbers.Integral)`
    ona `True` der; `bool` ise `int`'in alt sinifidir. Ikisini de yalnizca
    `type(v) is int` eler.
    """
    for ad in ALANLAR:
        deger = getattr(rect, ad)
        assert type(deger) is int, f"{ad}: {type(deger).__name__} (beklenen int)"
    assert type(rect.monitor_index) is int
    assert type(rect.dpi_scale) is float
    json.dumps(asdict(rect))  # zararin kendisi: sizinti varsa TypeError


# ===========================================================================
# OLGULAR -- olcunun anlamli oldugunu kanitlayan yeniden uretimler
# ===========================================================================


def test_olgu_esitlik_sizintiyi_goremez() -> None:
    """B1'in olcum araci gerekcesi: `==`/`hash`/aritmetik sizintiya KORDUR.

    Sefin olctugu olgu. Bu test uygulamayi degil, OLCUYU dogrular: eger
    esitlik sizintiyi gorseydi `type(...) is int` iddialarina gerek kalmazdi
    ve K3'un `==` tabanli olculeri yeterli olurdu. Gormuyor.
    """
    kirli = Rect(np.int64(10), np.int64(20), np.int64(30), np.int64(40))
    temiz = Rect(10, 20, 30, 40)

    # --- esitligin GORMEDIKLERI ---
    assert kirli == temiz
    assert hash(kirli) == hash(temiz)
    assert len({kirli, temiz}) == 1
    assert kirli.right == temiz.right == 40
    assert kirli.bottom == temiz.bottom == 60

    # --- yalniz tip kimliginin GORDUGU ---
    assert type(kirli.x) is not int
    assert type(temiz.x) is int
    assert isinstance(kirli.x, numbers.Integral)  # kabul kapisi bunu gecirir

    # --- zararin kendisi ---
    with pytest.raises(TypeError, match="int64"):
        json.dumps(asdict(kirli))
    assert json.loads(json.dumps(asdict(temiz)))["x"] == 10


def test_olgu_np_float32_serilesmez_np_float64_serilesir() -> None:
    """B3'un gerekcesi: `np.float64` `float` ALT SINIFIDIR, `np.float32` degil.

    Bu yuzden `dpi_scale` icin `isinstance(v, float)` yeterli bir kapi
    DEGILDIR ve `float()` KOSULSUZ uygulanmalidir.
    """
    assert isinstance(np.float64(1.5), float)
    assert not isinstance(np.float32(1.5), float)
    assert json.loads(json.dumps({"s": np.float64(1.5)}))["s"] == 1.5
    with pytest.raises(TypeError, match="float32"):
        json.dumps({"s": np.float32(1.5)})
    # ...ve bir `Rect` icinde de ayni sey olur:
    with pytest.raises(TypeError, match="float32"):
        json.dumps(asdict(Rect(0, 0, 10, 10, dpi_scale=np.float32(1.5))))


@pytest.mark.parametrize("tip", ISARETSIZ, ids=ISARETSIZ_ID)
def test_olgu_dondurulmus_dpi_isaretsizde_overflow_uyarisi_dogurur(tip: Any) -> None:
    """B2'nin gerekcesi (1/2): `dpi.py` isaretsiz numpy'de TASAR.

    Dondurulmus modul DOGRUDAN cagrilir -- servis araya girmez. `Rect.right`
    (`x + w`) ve `intersect`'in `x2 - x1` cikarmasi isaretsiz tipte sarar.
    """
    kirli = Rect(tip(10), tip(10), tip(100), tip(50))
    with warnings.catch_warnings(record=True) as yakalanan:
        warnings.simplefilter("always")
        dpi.classify_region(kirli, GERCEK_DUZEN)
        [dpi.intersect(kirli, m) for m in GERCEK_DUZEN]

    tasmalar = [w for w in yakalanan if issubclass(w.category, RuntimeWarning)
                and "overflow" in str(w.message)]
    assert tasmalar, f"{tip}: overflow uyarisi bekleniyordu, gelen: {list(yakalanan)}"


@pytest.mark.parametrize("tip", ISARETSIZ, ids=ISARETSIZ_ID)
def test_olgu_dondurulmus_dpi_isaretsizde_monitor_index_i_bozar(tip: Any) -> None:
    """B2'nin gerekcesi (2/2): tasma SESSIZ bir YANLISA donusur.

    `Rect(10,10,100,50)` yalnizca M1'in icindedir; duz `int` ile tam **1**
    monitorle kesisir. Isaretsiz numpy ile **2** monitorle kesisiyor gorunur
    -- yani K8'in `monitor_index` kurali `1` yerine `-1` uretirdi.
    """
    temiz = Rect(10, 10, 100, 50)
    kirli = Rect(tip(10), tip(10), tip(100), tip(50))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        temiz_kesisen = [m for m in GERCEK_DUZEN if dpi.intersect(temiz, m) is not None]
        kirli_kesisen = [m for m in GERCEK_DUZEN if dpi.intersect(kirli, m) is not None]

    assert len(temiz_kesisen) == 1 and temiz_kesisen[0].monitor_index == 1
    assert len(kirli_kesisen) == 2, f"{tip}: tasma beklenmisti, kesisen={kirli_kesisen}"


@pytest.mark.parametrize("tip", [np.uint16, np.uint32], ids=["uint16", "uint32"])
def test_olgu_dondurulmus_dpi_isaretsizde_siniflandirmayi_bozar(tip: Any) -> None:
    """B2 devami: `inside` olmasi gereken bolge `partial` cikiyor (sef olctu)."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        temiz = dpi.classify_region(Rect(10, 10, 100, 50), GERCEK_DUZEN)
        kirli = dpi.classify_region(
            Rect(tip(10), tip(10), tip(100), tip(50)), GERCEK_DUZEN
        )
    assert temiz is dpi.RegionValidity.INSIDE
    assert kirli is dpi.RegionValidity.PARTIAL, f"{tip}: {kirli}"


def test_olgu_karisik_isaretli_aritmetik_float_uretir() -> None:
    """K5'in `np.uint64 - np.int64 -> float64` olgusu: `w` sessizce float olur."""
    fark = np.uint64(100) - np.int64(0)
    assert isinstance(fark, np.floating)
    assert type(fark) is not int


# ===========================================================================
# B1 -- numpy skaler sizintisi: iki yol, dort tip, tip kimligiyle
# ===========================================================================


@pytest.mark.parametrize("tip", DORT_TIP, ids=DORT_TIP_ID)
def test_b1_monitors_yolu_duz_int(tip: Any) -> None:
    """`rects_from_mss_monitors` her alani duz `int`'e DUZLESTIRIR (K5)."""
    ham: list[dict[str, object]] = [
        {"left": tip(0), "top": tip(0), "width": tip(200), "height": tip(100)},
        {"left": tip(0), "top": tip(0), "width": tip(100), "height": tip(100)},
        {"left": tip(100), "top": tip(0), "width": tip(100), "height": tip(100)},
    ]
    rects = rects_from_mss_monitors(ham)
    assert len(rects) == 2
    for r in rects:
        _duz_int_mi(r)
    # geometri de dogru (duzlestirme degeri BOZMAZ)
    assert rects[0] == Rect(0, 0, 100, 100, 0, 1.0)
    assert rects[1] == Rect(100, 0, 100, 100, 1, 1.0)


@pytest.mark.parametrize("tip", DORT_TIP, ids=DORT_TIP_ID)
def test_b1_monitors_yolu_dort_alan_ayri_ayri(tip: Any) -> None:
    """Tek alani numpy olan sozluk: yalniz `left`'i duzlesten uygulama duser."""
    for alan, oznitelik in zip(("left", "top", "width", "height"), ALANLAR):
        ham: list[dict[str, object]] = [
            {"left": 0, "top": 0, "width": 200, "height": 100},
            {"left": 0, "top": 0, "width": 100, "height": 100},
        ]
        ham[1][alan] = tip(ham[1][alan])  # type: ignore[arg-type]
        (r,) = rects_from_mss_monitors(ham)
        assert type(getattr(r, oznitelik)) is int, f"{alan} -> {oznitelik}"


@pytest.mark.parametrize("tip", DORT_TIP, ids=DORT_TIP_ID)
def test_b1_servis_onbellegi_duz_int(tip: Any) -> None:
    """Servisin monitor onbellegi (yapim + `refresh_monitors`) duz `int`."""
    servis, fb = _kur(monitorler=(), ham=_ham_liste(tip, KUCUK_DUZEN))
    assert servis.monitors == KUCUK_DUZEN
    for r in servis.monitors:
        _duz_int_mi(r)
    fb.raw_override = _ham_liste(tip, (K1,))
    yeni = servis.refresh_monitors()
    assert len(yeni) == 1
    for r in yeni:
        _duz_int_mi(r)


@pytest.mark.parametrize("tip", DORT_TIP, ids=DORT_TIP_ID)
@pytest.mark.parametrize("yol", ["inside", "partial"])
def test_b1_frame_rect_duz_int(tip: Any, yol: str) -> None:
    """`Frame.rect` alanlari duz `int` -- INSIDE ve PARTIAL yollarinda AYRI.

    Iki nokta AYRISTIRICIDIR: INSIDE yolunda `Frame.rect` cagiranin
    `Rect`'inden, PARTIAL yolunda `dpi.intersect` ciktisindan gelir. Sef
    olctu: `intersect` PARTIAL'da **karisik** uretir (`x` duzlesir cunku
    `max()` Python `int`'ini secer, digerleri numpy kalir) -- yalniz INSIDE'i
    duzlesten bir uygulama burada duser.

    Kucuk pozitif duzen kullanilir cunku `np.uint8` 255'ten buyuk bir
    koordinat, isaretsiz tiplerin hicbiri de negatif koordinat KURAMAZ.
    Negatif duzenin kendi olcusu `test_b1_frame_rect_negatif_partial_duz_int`.
    """
    if yol == "inside":
        girdi = Rect(tip(10), tip(10), tip(50), tip(50))
        beklenen = (10, 10, 50, 50)
    else:
        # sag kenardan tasan bolge: birlesim 200'de biter -> (180,0,20,50)
        girdi = Rect(tip(180), tip(0), tip(100), tip(50))
        beklenen = (180, 0, 20, 50)

    servis, _ = _kur(monitorler=KUCUK_DUZEN)
    kare = servis.capture_region(girdi)

    _duz_int_mi(kare.rect)
    assert (kare.rect.x, kare.rect.y, kare.rect.w, kare.rect.h) == beklenen


@pytest.mark.parametrize("tip", DORT_TIP, ids=DORT_TIP_ID)
def test_b1_frame_rect_negatif_partial_duz_int(tip: Any) -> None:
    """K8'in PARTIAL ornegi: `Rect(-2600,0,100,100)` -> `(-2560,0,60,100)`.

    `np.uint8` bu vakayi kuramaz (negatif tasiyamaz) -- o tipte test
    duzlestirmenin degeri bozmadigini pozitif tarafta olcer.
    """
    if tip is np.uint8:
        pytest.skip("np.uint8 negatif koordinat tasiyamaz")
    servis, fb = _kur()
    kare = servis.capture_region(
        Rect(tip(-2600), tip(0), tip(100), tip(100), monitor_index=tip(7), dpi_scale=1.5)
    )
    _duz_int_mi(kare.rect)
    assert kare.rect == Rect(-2560, 0, 60, 100, monitor_index=0, dpi_scale=1.5)
    # backend'e giden kutu da duz `int` olmali: `mss` sozlugu JSON degil ama
    # `np.uint64` bir `left` degeri ctypes sinirinda sessizce bozulur.
    assert _tipler(fb.grab_rects[-1]) == ["int"] * 4


@pytest.mark.parametrize("tip", DORT_TIP, ids=DORT_TIP_ID)
def test_b1_capture_full_frame_rect_duz_int(tip: Any) -> None:
    """`capture_full` yolu -- AYIRT ETME GUCU YOK, yalnizca regresyon nobeti.

    Paket bu bacagi `[OLCULMUYOR]` damgaladi (Y7-8) ve HAKLI: bu yolun
    `rect`'i K5'in zaten duzlestirdigi monitor kumesinden gelir, numpy skaleri
    oraya ULASAMAZ. Kendim dogruladim: girdi numpy'si `rects_from_mss_monitors`
    tarafindan yutuluyor, yani duzlestirmeyi yalniz burada atlayan bir uygulama
    bu testi de gecer. Yine de kaydediliyor -- ileride `capture_full` baska bir
    kaynaktan `rect` uretirse kapi hazir olsun diye.
    """
    servis, _ = _kur(monitorler=(), ham=_ham_liste(tip, KUCUK_DUZEN))
    kare = servis.capture_full(1)
    _duz_int_mi(kare.rect)
    assert kare.rect == Rect(100, 0, 100, 100, monitor_index=1, dpi_scale=1.0)


@pytest.mark.parametrize("tip", DORT_TIP, ids=DORT_TIP_ID)
def test_b1_union_bbox_servis_yolunda_duz_int(tip: Any) -> None:
    """`union_bbox`, `list_monitors` ciktisi uzerinde duz `int` uretir.

    (`union_bbox`'a DOGRUDAN numpy tasiyan `Rect` verilirse ciktisi numpy
    olur -- `test_b1_union_bbox_dogrudan_cagrida_sizdirir` bunu olcuyor. O
    yol servis icinden erisilemez.)
    """
    fb = FakeBackend((), _uretici, raw_override=_ham_liste(tip, KUCUK_DUZEN))
    birlesim = union_bbox(list_monitors(fb))
    assert birlesim is not None
    _duz_int_mi(birlesim)
    assert birlesim == Rect(0, 0, 200, 100, monitor_index=-1, dpi_scale=1.0)


def test_b1_union_bbox_dogrudan_cagrida_sizdirir() -> None:
    """OLCULEN GOZLEM (kirik degil): `union_bbox` girdisinin tipini tasir.

    `union_bbox` saf aritmetiktir ve `int()` uygulamaz; numpy tasiyan `Rect`
    verilirse ciktisi da numpy tasir. Servisin hicbir yolu bunu KURAMAZ:
    `union_bbox`'in iki cagiran yeri (`CaptureService._hedef_dikdortgen` ve
    `FakeBackend.monitors`) ona ya `list_monitors` ciktisini ya da bir ham
    sozluge cevrilecek `Rect` verir; ikisi de duzlesir. Bu yuzden BLOKE EDICI
    degil, belgelenen bir sinirdir -- ve olcum noktasi servis disindadir.
    """
    kirli = Rect(np.int64(0), np.int64(0), np.int64(100), np.int64(50))
    birlesim = union_bbox((kirli,))
    assert birlesim is not None
    assert type(birlesim.x) is not int  # sizinti gercek
    assert birlesim == Rect(0, 0, 100, 50, monitor_index=-1, dpi_scale=1.0)  # esitlik kor


# ===========================================================================
# B2 -- isaretsiz tasma: servis dondurulmus `dpi.py`'yi KORUR
# ===========================================================================


@pytest.mark.filterwarnings("error::RuntimeWarning")
@pytest.mark.parametrize("tip", ISARETSIZ + [np.uint64], ids=ISARETSIZ_ID + ["uint64"])
def test_b2_servis_isaretsiz_numpy_de_tasmaz_inside(tip: Any) -> None:
    """Girisdeki duzlestirme tasmayi ONLER: `inside`, `monitor_index=1`.

    `filterwarnings("error::RuntimeWarning")` bu testi tasmaya karsi
    SESSIZ OLMAYAN kilar: bir `RuntimeWarning: overflow` dogsa test coker.
    `test_olgu_dondurulmus_dpi_*` ayni girdiyle tasmanin gercek oldugunu
    kanitliyor, yani bu olcunun ayirt etme gucu var.
    """
    servis, fb = _kur()
    kare = servis.capture_region(Rect(tip(10), tip(10), tip(100), tip(50)))

    assert kare.rect == Rect(10, 10, 100, 50, monitor_index=1, dpi_scale=1.0)
    _duz_int_mi(kare.rect)
    assert fb.grab_calls == 1
    assert fb.grab_rects[-1] == Rect(10, 10, 100, 50, monitor_index=1, dpi_scale=1.0)


@pytest.mark.filterwarnings("error::RuntimeWarning")
@pytest.mark.parametrize("tip", ISARETSIZ + [np.uint64], ids=ISARETSIZ_ID + ["uint64"])
def test_b2_servis_isaretsiz_numpy_de_tasmaz_partial(tip: Any) -> None:
    """PARTIAL yolu da korunur: kirpma birlesime gore, `monitor_index` dogru.

    Kucuk pozitif duzen (`np.uint8` 255'ten buyuk deger tasiyamaz).
    `x=180, w=100` `np.uint8`'de `right`'i **tasirir** (280 -> 24), yani bu
    olcu en dar tipte AYIRT EDICIDIR; genis tiplerde regresyon nobetidir.
    """
    servis, fb = _kur(monitorler=KUCUK_DUZEN)
    kare = servis.capture_region(Rect(tip(180), tip(0), tip(100), tip(50)))
    assert kare.rect == Rect(180, 0, 20, 50, monitor_index=1, dpi_scale=1.0)
    assert fb.grab_rects[-1].w == 20
    _duz_int_mi(kare.rect)


@pytest.mark.filterwarnings("error::RuntimeWarning")
@pytest.mark.parametrize("tip", ISARETSIZ, ids=ISARETSIZ_ID)
def test_b2_servis_isaretsiz_numpy_de_tasmaz_l_duzeni(tip: Any) -> None:
    """L duzeninde olu alana degen bolge: yalniz A ile kesisir -> `0` (K8)."""
    a = Rect(0, 0, 100, 100, monitor_index=0, dpi_scale=1.0)
    b = Rect(100, 100, 100, 100, monitor_index=1, dpi_scale=1.0)
    servis, _ = _kur(monitorler=(a, b))
    kare = servis.capture_region(Rect(tip(90), tip(50), tip(20), tip(20)))
    assert kare.rect == Rect(90, 50, 20, 20, monitor_index=0, dpi_scale=1.0)


@pytest.mark.filterwarnings("error::RuntimeWarning")
@pytest.mark.parametrize("tip", ISARETSIZ, ids=ISARETSIZ_ID)
def test_b2_isaretsiz_monitor_sozlugu_de_tasmaz(tip: Any) -> None:
    """Tasma ikinci bir yoldan da girebilirdi: MONITOR kumesi isaretsizse.

    `rects_from_mss_monitors` sozluk degerlerini `int()`'e duzlestirdigi icin
    servisin onbellegi hicbir zaman numpy tasimaz ve `classify_region` ile
    `intersect` duz `int` gorur.
    """
    duzen = (Rect(0, 0, 100, 100, 0, 1.0), Rect(100, 0, 100, 100, 1, 1.0))
    servis, _ = _kur(monitorler=(), ham=_ham_liste(tip, duzen))
    kare = servis.capture_region(Rect(150, 10, 40, 40))
    assert kare.rect == Rect(150, 10, 40, 40, monitor_index=1, dpi_scale=1.0)
    for r in servis.monitors:
        _duz_int_mi(r)


# ===========================================================================
# B3 -- `dpi_scale` float tipi
# ===========================================================================


@pytest.mark.parametrize(
    "deger",
    [1.5, np.float32(1.5), np.float64(1.5), 2, np.int64(2), np.uint8(2)],
    ids=["float", "float32", "float64", "int", "int64", "uint8"],
)
def test_b3_dpi_scale_duz_float_a_duzlesir(deger: Any) -> None:
    """`type(f.rect.dpi_scale) is float` -- `isinstance` DEGIL.

    `np.float64` `float` alt sinifi oldugu icin `isinstance` onu gecirirdi ve
    olcu ayirt etme gucunu kaybederdi; `np.float32` ise `isinstance`'i de
    gecmez ama sizintisini yalniz `type` ve `json` gosterir.
    """
    servis, _ = _kur()
    kare = servis.capture_region(Rect(0, 0, 100, 50, dpi_scale=deger))
    assert type(kare.rect.dpi_scale) is float
    assert kare.rect.dpi_scale == float(deger)
    json.dumps(asdict(kare.rect))


def test_b3_dpi_scale_partial_yolunda_cagiranin_degeri_ezilmez() -> None:
    """Y-B: `dpi.intersect` metadata'yi IKINCI argumandan alir.

    `union_bbox`'in `dpi_scale`'i daima `1.0`'dir; `Frame.rect` `intersect`
    ciktisinin metadata'siyla kurulsaydi cagiranin `1.5`'i sessizce `1.0`
    olurdu. Ayni sey `monitor_index` icin de gecerlidir (`-1`'e ezilirdi).
    """
    servis, _ = _kur()
    kirpik = dpi.intersect(Rect(-2600, 0, 100, 100, dpi_scale=1.5), union_bbox(GERCEK_DUZEN))
    assert kirpik is not None
    assert kirpik.dpi_scale == 1.0 and kirpik.monitor_index == -1  # olgunun kendisi

    kare = servis.capture_region(Rect(-2600, 0, 100, 100, monitor_index=7, dpi_scale=1.5))
    assert kare.rect.dpi_scale == 1.5
    assert type(kare.rect.dpi_scale) is float
    assert kare.rect.monitor_index == 0


def test_b3_capture_full_dpi_scale_bir_nokta_sifir_ve_float() -> None:
    servis, _ = _kur()
    for i in (0, 1):
        kare = servis.capture_full(i)
        assert kare.rect.dpi_scale == 1.0
        assert type(kare.rect.dpi_scale) is float


@pytest.mark.parametrize(
    "deger", ["1.5", None, True, np.bool_(True), object()],
    ids=["str", "None", "bool", "np_bool", "object"],
)
def test_b3_dpi_scale_sayi_olmayan_reddedilir(deger: Any) -> None:
    """Sayi olmayan `dpi_scale` sessizce cevrilmez; backend cagrilmaz."""
    servis, fb = _kur()
    with pytest.raises(CaptureError):
        servis.capture_region(Rect(0, 0, 100, 50, dpi_scale=deger))
    assert fb.grab_calls == 0


def test_b3_dpi_scale_nan_kabul_ediliyor_gozlem() -> None:
    """OLCULEN GOZLEM (kirik degil): `dpi_scale=nan/inf` KABUL ediliyor.

    Paket `dpi_scale` icin yalnizca "duz `float` olmali" diyor; sonlu olma
    kosulu YAZMIYOR ve K3/K8 geregi servis bu degeri hicbir kararda
    kullanmiyor -- yani `nan` yakalanan pikselleri etkilemiyor. `json.dumps`
    da varsayilan ayarla `NaN` uretiyor (istisna yok). Bloke edici degil;
    A7'ye tasinacak bir sozlesme sorusu olarak kaydedildi.
    """
    servis, _ = _kur()
    kare = servis.capture_region(Rect(0, 0, 100, 50, dpi_scale=float("nan")))
    assert type(kare.rect.dpi_scale) is float
    assert kare.rect.dpi_scale != kare.rect.dpi_scale  # nan
    assert kare.rect.x == 0 and kare.rect.w == 100  # piksel karari etkilenmedi


# ===========================================================================
# B4 -- giristeki kabul kapisi
# ===========================================================================


RED_DEGERLERI = ["10", True, 10.9, float("nan"), float("inf"), np.float32(10.5)]
RED_ID = ["str", "bool", "kesirli", "nan", "inf", "float32_kesirli"]


@pytest.mark.parametrize("deger", RED_DEGERLERI, ids=RED_ID)
@pytest.mark.parametrize("alan", ALANLAR)
def test_b4_kabul_kapisi_dort_alanda_reddeder(deger: Any, alan: str) -> None:
    """Alti deger x dort alan = 24 hucre; hicbiri bos kalmasin.

    Tek alanda (`x`) olcen bir kapi, `w`'yi `int()` ile ciplak cevirent bir
    uygulamayi KACIRIRDI. Ayrica: red K6 sinif (a)'dir -- backend cagrilmaz.
    """
    servis, fb = _kur()
    args: dict[str, Any] = {"x": 0, "y": 0, "w": 100, "h": 50}
    args[alan] = deger
    with pytest.raises(CaptureError) as bilgi:
        servis.capture_region(Rect(**args))
    assert f"'{alan}'" in str(bilgi.value), str(bilgi.value)
    assert fb.grab_calls == 0
    assert bilgi.value.__cause__ is None


@pytest.mark.parametrize("deger", [10.0, np.float64(10.0)], ids=["float", "float64"])
@pytest.mark.parametrize("alan", ALANLAR)
def test_b4_kabul_kapisi_tam_sayi_degerli_float_u_kabul_eder(deger: Any, alan: str) -> None:
    """`10.0` ve `np.float64(10.0)` KABUL; sonuc duz `int`."""
    servis, fb = _kur()
    args: dict[str, Any] = {"x": 0, "y": 0, "w": 100, "h": 50}
    args[alan] = deger
    kare = servis.capture_region(Rect(**args))
    assert fb.grab_calls == 1
    _duz_int_mi(kare.rect)
    assert getattr(kare.rect, alan) == 10


def test_b4_ciplak_int_in_yapacagi_sessiz_yanlis() -> None:
    """Kapinin GEREKCESI: `int()` tek basina bir DONUSUMDUR, dogrulama degil.

    Bu test uygulamayi degil, `int()`'in kendisini olcer -- kapi kaldirilsa
    ne olurdu: `10.9` sessizce `10`, `'10'`/`True` sessizce kabul,
    `inf`/`nan` K6 taksonomisi DISINDA istisna.
    """
    assert int(10.9) == 10
    assert int("10") == 10 and int(True) == 1
    with pytest.raises(OverflowError):
        int(float("inf"))
    with pytest.raises(ValueError):
        int(float("nan"))


@pytest.mark.parametrize("deger", RED_DEGERLERI, ids=RED_ID)
def test_b4_kapi_hatasi_seq_tuketmez(deger: Any) -> None:
    """Kabul kapisi hatasi K6 sinif (a)'dir: `seq` tuketilmez."""
    servis, _ = _kur()
    ilk = servis.capture_region(Rect(0, 0, 10, 10))
    assert ilk.seq == 0
    with pytest.raises(CaptureError):
        servis.capture_region(Rect(deger, 0, 10, 10))
    assert servis.capture_region(Rect(0, 0, 10, 10)).seq == 1


@pytest.mark.parametrize(
    "deger", [None, np.bool_(True), np.bool_(False), b"10", 10 + 0j],
    ids=["None", "np_true", "np_false", "bytes", "complex"],
)
def test_b4_kapi_ek_yozlasmis_girdiler(deger: Any) -> None:
    """Paketin saymadigi girdiler de reddedilmeli (kural TIP DUZEYINDE).

    `np.bool_` ozellikle onemli: `numbers.Integral` DEGILDIR (sef olctu), yani
    `Integral` kapisi onu zaten eler; ama `bool` kontrolune GUVENEN bir
    uygulama `np.bool_`'u kacirirdi cunku `isinstance(np.bool_(True), bool)`
    `False`'tur.
    """
    assert not isinstance(np.bool_(True), bool)
    servis, fb = _kur()
    with pytest.raises(CaptureError):
        servis.capture_region(Rect(deger, 0, 100, 50))
    assert fb.grab_calls == 0


def test_b4_kapi_alan_denetiminden_ONCE_kosar() -> None:
    """Sira onemli: `'10'` bir `w` degeriyse hata mesaji TIP hatasi olmali.

    Once alan denetimi kosaydi `w='10'` karsilastirmasi `TypeError`
    dogururdu -- K6 taksonomisi disinda bir istisna.
    """
    servis, _ = _kur()
    with pytest.raises(CaptureError) as bilgi:
        servis.capture_region(Rect(0, 0, "10", 50))
    assert "tamsayi" in str(bilgi.value)


def test_b4_k5_ve_k8_kapilari_bilerek_FARKLI() -> None:
    """Belgelenen asimetri: `10.0` monitor sozlugunde RET, giris `Rect`'inde KABUL.

    Paket ikisini ayri yaziyor (K5: `float` ret; K8: tam sayi degerli float
    kabul) ve gerekcesi farkli kaynaklar: monitor sozlugu `mss`'ten gelir ve
    daima `int`'tir; giris `Rect`'i Qt'den gelebilir ve `float` tasiyabilir.
    Bir kirik degil, olculmus bir tasarim karari.
    """
    with pytest.raises(CaptureError, match="tamsayi degil"):
        rects_from_mss_monitors([{}, {"left": 10.0, "top": 0, "width": 10, "height": 10}])
    with pytest.raises(CaptureError, match="tamsayi degil"):
        rects_from_mss_monitors(
            [{}, {"left": np.float64(10.0), "top": 0, "width": 10, "height": 10}]
        )
    servis, _ = _kur()
    assert servis.capture_region(Rect(10.0, 0, 100, 50)).rect.x == 10


# ===========================================================================
# B5 -- `numbers.Integral` daraltmasi ve `cast` kacisi
# ===========================================================================


def _kaynak_agaci(ad: str) -> ast.Module:
    return ast.parse((_KOK / "src" / "capture" / ad).read_text(encoding="utf-8"))


@pytest.mark.parametrize("dosya", ["service.py", "monitors.py"])
def test_b5_kaynakta_cast_kacisi_yok(dosya: str) -> None:
    """`typing.cast` YASAK (K5): mypy'yi gecer, numpy skalerini sizdirir.

    AST ile olculur -- yorum/docstring icindeki "cast" kelimesi sayilmaz
    (iki dosyada da gecer). Aranan: `cast(...)` cagrisi, `from typing import
    cast` ve `typing.cast` oznitelik erisimi.
    """
    agac = _kaynak_agaci(dosya)
    ihlaller: list[str] = []
    for dugum in ast.walk(agac):
        if isinstance(dugum, ast.Call):
            hedef = dugum.func
            if isinstance(hedef, ast.Name) and hedef.id == "cast":
                ihlaller.append(f"cast(...) cagrisi satir {dugum.lineno}")
            if isinstance(hedef, ast.Attribute) and hedef.attr == "cast":
                ihlaller.append(f"*.cast(...) cagrisi satir {dugum.lineno}")
        if isinstance(dugum, ast.ImportFrom) and dugum.module == "typing":
            for ad in dugum.names:
                if ad.name == "cast":
                    ihlaller.append(f"from typing import cast satir {dugum.lineno}")
    assert not ihlaller, ihlaller


@pytest.mark.parametrize("dosya", ["service.py", "monitors.py"])
def test_b5_duzlestirmede_type_ignore_ile_susturma_yok(dosya: str) -> None:
    """Sayisal yolda `# type: ignore` ile susturma yok.

    Paketin izin verdigi TEK `# type: ignore` `FakeBackend.grab`'in
    `[return-value]`'sudur (O-F). Baska bir tanesi -- ozellikle bir
    duzlestirme satirinda -- `cast` ile ayni kacistir.

    Olcu METIN ARAMASI DEGIL, `tokenize` ile GERCEK yorum belirteclerini
    tarar: ilk yazisinda docstring icindeki "`# type: ignore[return-value]`"
    aciklamasini bir susturma sanip yanlis pozitif verdi (bu dosyanin
    gecmisinde kayitlidir). Bir olcu, denetledigi seyi metin olarak
    aradiginda kacinilmaz olarak aciklamayi da sayar.
    """
    yol = _KOK / "src" / "capture" / dosya
    with yol.open("rb") as akis:
        yorumlar = [
            (t.start[0], t.string)
            for t in tokenize.tokenize(akis.readline)
            if t.type == tokenize.COMMENT and "type: ignore" in t.string
        ]
    for _, metin in yorumlar:
        assert "[return-value]" in metin, f"beklenmeyen susturma: {metin}"
    assert len(yorumlar) <= 1, yorumlar


def test_b5_integral_isinstance_int_e_DARALTMAZ_calisma_zamani() -> None:
    """Y-C'nin cekirdegi: `Integral` bir TANIM verir, bir DONUSUM degil.

    `isinstance(v, numbers.Integral)` `np.int64`'e `True` der ama `v` hala
    `np.int64`'tur. Kuralin LAFZI uygulamasi (`return v`) bu yuzden sizdirir.
    """
    v: object = np.int64(10)
    assert isinstance(v, numbers.Integral)
    assert type(v) is not int
    assert type(int(v)) is int


def test_b5_integral_daraltmasi_mypy_altinda(tmp_path: Path) -> None:
    """Y-C'yi mypy ile yeniden uretir: `return v` KIRAR, `cast(int, v)` GECER.

    Sefin olctugu olgu bu: kuralin lafzi uygulamasi `mypy --strict`'i kirdigi
    icin implementer'in onunde bir KACIS (`cast`) duruyordu ve o kacis
    mypy'den gecerken numpy'yi `Rect`'e sizdiriyordu. Ucuncu varyant --
    `int(v)` -- hem mypy'yi gecer hem sizdirmaz; uygulamanin sectigi budur
    (`test_b5_kaynakta_cast_kacisi_yok` ile birlikte okunur).
    """
    varyantlar = {
        "A_return_v": "    return v\n",
        "C_cast": "    return cast(int, v)\n",
        "E_int": "    return int(v)\n",
    }
    sonuc: dict[str, int] = {}
    for ad, govde in varyantlar.items():
        yol = tmp_path / f"{ad}.py"
        yol.write_text(
            "import numbers\n"
            "from typing import cast\n"
            "\n"
            "def f(v: object) -> int:\n"
            "    if not isinstance(v, numbers.Integral):\n"
            "        raise ValueError\n" + govde,
            encoding="utf-8",
        )
        p = subprocess.run(
            [sys.executable, "-m", "mypy", "--strict", "--no-error-summary",
             "--cache-dir", str(tmp_path / ".cache"), str(yol)],
            capture_output=True, text=True,
        )
        sonuc[ad] = p.returncode

    assert sonuc["A_return_v"] != 0, "lafzi uygulama mypy'yi kirmaliydi"
    assert sonuc["C_cast"] == 0, "cast kacisi mypy'yi gecmeliydi (tehlike gercek)"
    assert sonuc["E_int"] == 0, "int(v) hem gecmeli hem sizdirmamali"


# ===========================================================================
# B6 -- kirpma aritmetigi
# ===========================================================================


def test_b6_iki_monitore_yayilan_bolge_birlesime_kirpilir() -> None:
    """K4: 5300w bolge -> **5120**, 2560 DEGIL.

    Ayirt edici olcu: `intersect` ve `clamp_to_monitor` BIREBIR ayni govdedir,
    yanlislik ikinci argumandadir. Ikisi de burada olculuyor ki "5120 dogru mu"
    sorusu bir sayiya degil bir FARKA dayansin.
    """
    yayilan = Rect(-2560, 0, 5300, 100)
    tek_monitore = dpi.clamp_to_monitor(yayilan, M0)
    assert tek_monitore is not None and tek_monitore.w == 2560  # YANLIS cevap
    birlesime = dpi.intersect(yayilan, union_bbox(GERCEK_DUZEN))
    assert birlesime is not None and birlesime.w == 5120  # DOGRU cevap

    servis, fb = _kur()
    kare = servis.capture_region(yayilan)
    assert kare.rect.w == 5120
    assert fb.grab_rects[-1].w == 5120  # backend'e giden kutu da 5120
    assert kare.rect.monitor_index == -1  # iki monitore atfedilemez
    _duz_int_mi(kare.rect)


@pytest.mark.parametrize(
    ("girdi", "beklenen"),
    [
        (Rect(-2600, 0, 100, 100), (-2560, 0, 60, 100)),
        (Rect(2500, 0, 200, 100), (2500, 0, 60, 100)),
        (Rect(100, -50, 100, 100), (100, 0, 100, 50)),
        (Rect(100, 1400, 100, 100), (100, 1400, 100, 40)),
        (Rect(-2600, -50, 100, 100), (-2560, 0, 60, 50)),
    ],
    ids=["sol", "sag", "ust", "alt", "kose"],
)
def test_b6_dort_kenar_ve_kose_kirpmasi(
    girdi: Rect, beklenen: tuple[int, int, int, int]
) -> None:
    """Kirpma aritmetigi bes noktada; negatif duzende isaret hatasi burada cikar."""
    servis, fb = _kur()
    kare = servis.capture_region(girdi)
    assert (kare.rect.x, kare.rect.y, kare.rect.w, kare.rect.h) == beklenen
    assert kare.image.shape == (beklenen[3], beklenen[2], 3)
    assert fb.grab_rects[-1].w == beklenen[2]
    _duz_int_mi(kare.rect)


def test_b6_l_duzeninde_olu_alan_kirpmaya_dahil() -> None:
    """K4'un kabul edilen siniri: birlesim dikdortgeni olu alan icerebilir.

    `A=(0,0,100,100)`, `B=(100,100,100,100)` -> birlesim `(0,0,200,200)`;
    `(150,50)` civari hicbir monitore dusmez ama birlesime dahildir. Kural
    geregi kirpma birlesime gore yapilir, yani olu alan yakalanir (`mss` siyah
    doldurur) ve `monitor_index` "tek monitore atfedilemez" der.
    """
    a = Rect(0, 0, 100, 100, monitor_index=0, dpi_scale=1.0)
    b = Rect(100, 100, 100, 100, monitor_index=1, dpi_scale=1.0)
    servis, fb = _kur(monitorler=(a, b))

    kare = servis.capture_region(Rect(50, 50, 300, 300))
    assert kare.rect == Rect(50, 50, 150, 150, monitor_index=-1, dpi_scale=1.0)
    assert fb.grab_rects[-1].w == 150

    # olu alanin kendisi HIC kesismedigi icin OUTSIDE:
    with pytest.raises(CaptureError):
        servis.capture_region(Rect(150, 10, 20, 20))
    # yalniz A ile kesisen bolge -> 0 (tamamen A'nin icinde OLMASA da)
    assert servis.capture_region(Rect(90, 50, 20, 20)).rect.monitor_index == 0


def test_b6_kirpma_sira_degisimine_duyarsiz() -> None:
    """K5 sira degismezi: kirpma GEOMETRISI degismez, yalniz metadata degisir."""
    servis, fb = _kur(monitorler=(), ham=_ham_liste(int, GERCEK_DUZEN))
    once = servis.capture_region(Rect(-2600, 0, 100, 100))

    fb.raw_override = _ham_liste(int, (M1, M0))
    servis.refresh_monitors()
    sonra = servis.capture_region(Rect(-2600, 0, 100, 100))

    assert (once.rect.x, once.rect.y, once.rect.w, once.rect.h) == (-2560, 0, 60, 100)
    assert (sonra.rect.x, sonra.rect.y, sonra.rect.w, sonra.rect.h) == (-2560, 0, 60, 100)
    assert once.rect.monitor_index == 0 and sonra.rect.monitor_index == 1


@pytest.mark.filterwarnings("error::RuntimeWarning")
@pytest.mark.parametrize("tip", [np.int64, np.int32, int], ids=["int64", "int32", "int"])
def test_b6_kirpma_aritmetigi_numpy_girdide_de_ayni(tip: Any) -> None:
    """Duzlestirme kirpma DEGERINI bozmaz -- yalnizca tipini duzeltir."""
    servis, fb = _kur()
    kare = servis.capture_region(Rect(tip(-2560), tip(0), tip(5300), tip(100)))
    assert kare.rect.w == 5120 and kare.rect.monitor_index == -1
    assert fb.grab_rects[-1].w == 5120
    _duz_int_mi(kare.rect)


def test_b6_asiri_buyuk_koordinat_K6_taksonomisinde_kalir() -> None:
    """Cok buyuk tamsayi/float: `CaptureError`, `OverflowError` DEGIL.

    Python `int` sinirsizdir, `dpi.py`'nin aritmetigi tasmaz; onemli olan
    hatanin K6 taksonomisi ICINDE kalmasi ve backend'in cagrilmamasidir.
    """
    for deger in (1e30, 2**70, np.uint64(2**64 - 1), -(2**70)):
        servis, fb = _kur()
        with pytest.raises(CaptureError):
            servis.capture_region(Rect(deger, 0, 100, 50))
        assert fb.grab_calls == 0


# ===========================================================================
# Butunluk -- sayisal yolun ucundan ucuna serilesebilirligi
# ===========================================================================


@pytest.mark.filterwarnings("error::RuntimeWarning")
def test_bB_uctan_uca_numpy_girdi_serilesebilir_frame_uretir() -> None:
    """Tek testte butun sayisal yol: numpy monitor sozlugu + numpy giris `Rect`.

    Sizinti iki yoldan da girebilir; ikisi ayni anda acikken bile `Frame.rect`
    JSON'a serilesmeli.
    """
    # monitor sozlugu numpy (`np.int32` -- negatif `left` tasiyabilen en dar
    # tip; `np.uint*` bu duzeni yapimda kuramaz) + giris `Rect`'i de numpy.
    ham = _ham_liste(np.int32, GERCEK_DUZEN)
    servis, fb = _kur(monitorler=(), ham=ham)
    kare: Frame = servis.capture_region(
        Rect(np.int64(-2600), np.int32(0), np.uint16(100), np.uint8(100),
             monitor_index=np.int64(7), dpi_scale=np.float32(1.5))
    )
    assert kare.rect == Rect(-2560, 0, 60, 100, monitor_index=0, dpi_scale=1.5)
    _duz_int_mi(kare.rect)
    geri = json.loads(json.dumps(asdict(kare.rect)))
    assert geri == {"x": -2560, "y": 0, "w": 60, "h": 100,
                    "monitor_index": 0, "dpi_scale": 1.5}
    assert kare.image.shape == (100, 60, 3) and kare.image.dtype == np.uint8
    assert fb.grab_calls == 1
    assert type(kare.seq) is int and kare.seq == 0
