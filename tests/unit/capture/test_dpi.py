"""T-003 -- DPI ve monitor koordinat donusumleri (saf matematik).

Tasarim dokumani 5.1 (`CaptureService`, DPI farkindaligi), 5.6 ("bolge
gecersiz" hata satiri) ve 8.3 A2 kabul kriterlerini (%100/%150/%200
donusum testleri) dogrular. Kapsam:

  1. mantiksal <-> fiziksel piksel (dpi_scale ile), round-trip kararliligi
  2. monitore-relatif <-> sanal masaustu (negatif koordinatli monitor dahil)
  3. bolge gecerliligi (INSIDE / PARTIAL / OUTSIDE)
  4. monitore kirpma (clamp), boyut sifira duserse acikca None
"""
from __future__ import annotations

import pytest

from src.capture.dpi import (
    Monitor,
    RegionValidity,
    _round_half_away_from_zero,
    clamp_to_monitor,
    classify_region,
    intersect,
    logical_to_physical,
    physical_to_logical,
    to_monitor_relative,
    to_virtual_desktop,
)
from src.contracts.models import Rect

# ---------------------------------------------------------------------------
# ortak sabitler / yardimcilar
# ---------------------------------------------------------------------------

SCALES: tuple[float, ...] = (1.0, 1.25, 1.5, 1.75, 2.0)  # %100 %125 %150 %175 %200


def _pct(scale: float) -> str:
    return f"%{round(scale * 100)}"


# Uc monitorlu, karisik DPI'li sanal masaustu. Windows'un klasik tuzagi:
# birincilin solunda ve ustunde duran monitorler negatif koordinatlidir.
PRIMARY = Rect(x=0, y=0, w=1920, h=1080, monitor_index=0, dpi_scale=1.0)
LEFT_SECONDARY = Rect(x=-1280, y=0, w=1280, h=1024, monitor_index=1, dpi_scale=1.25)
ABOVE_SECONDARY = Rect(x=0, y=-1080, w=1920, h=1080, monitor_index=2, dpi_scale=1.5)
ALL_MONITORS: tuple[Monitor, ...] = (PRIMARY, LEFT_SECONDARY, ABOVE_SECONDARY)

# Mantiksal ornek dikdortgenler: sifir, tek piksel, negatif koordinat,
# buyuk/kucuk/tek-cift karisik degerler.
LOGICAL_SAMPLE_RECTS: tuple[tuple[int, int, int, int], ...] = (
    (0, 0, 0, 0),
    (0, 0, 1, 1),
    (1, 1, 1, 1),
    (2, 3, 5, 7),
    (100, 50, 200, 80),
    (333, 41, 999, 501),
    (1920, 1080, 640, 480),
    (-100, -50, 200, 80),
    (-1920, 0, 1280, 1024),
    (0, -1080, 1920, 1080),
    (7, 13, 1, 1),
    (1001, 2559, 3, 3),
    (-1, -1, 1, 1),
)


# ---------------------------------------------------------------------------
# 0. Monitor takma adi
# ---------------------------------------------------------------------------


def test_monitor_is_a_rect_alias() -> None:
    """Ek tip yok -- Monitor, Rect'in okunabilirlik icin takma adidir."""
    assert Monitor is Rect


# ---------------------------------------------------------------------------
# 1. yuvarlama sozlesmesi: sifirdan uzaga (round-half-away-from-zero)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0.5, 1), (1.5, 2), (2.5, 3), (3.5, 4),
        (-0.5, -1), (-1.5, -2), (-2.5, -3), (-3.5, -4),
        (0.4, 0), (0.6, 1), (-0.4, 0), (-0.6, -1),
        (0.0, 0), (3.0, 3), (-3.0, -3),
    ],
    ids=lambda v: str(v),
)
def test_round_half_away_from_zero(value: float, expected: int) -> None:
    """Python'un yerlesik round()'u (banker's rounding) DEGIL, simetrik
    sifirdan-uzaga kurali kullanilir -- bilincli secim, bkz. modul
    dokumantasyonu."""
    assert _round_half_away_from_zero(value) == expected


# ---------------------------------------------------------------------------
# 2. mantiksal <-> fiziksel piksel
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("scale", SCALES, ids=_pct)
def test_logical_to_physical_scales_each_field(scale: float) -> None:
    r = Rect(x=100, y=50, w=200, h=80, monitor_index=4, dpi_scale=scale)
    p = logical_to_physical(r)
    assert p.x == _round_half_away_from_zero(100 * scale)
    assert p.y == _round_half_away_from_zero(50 * scale)
    assert p.w == _round_half_away_from_zero(200 * scale)
    assert p.h == _round_half_away_from_zero(80 * scale)
    assert p.monitor_index == 4
    assert p.dpi_scale == scale


@pytest.mark.parametrize("scale", SCALES, ids=_pct)
def test_physical_to_logical_scales_each_field(scale: float) -> None:
    r = Rect(x=300, y=150, w=640, h=480, monitor_index=2, dpi_scale=scale)
    l = physical_to_logical(r)
    assert l.x == _round_half_away_from_zero(300 / scale)
    assert l.y == _round_half_away_from_zero(150 / scale)
    assert l.w == _round_half_away_from_zero(640 / scale)
    assert l.h == _round_half_away_from_zero(480 / scale)
    assert l.monitor_index == 2
    assert l.dpi_scale == scale


def test_scale_100_percent_is_identity() -> None:
    r = Rect(x=17, y=-5, w=333, h=41, dpi_scale=1.0)
    assert logical_to_physical(r) == r
    assert physical_to_logical(r) == r


@pytest.mark.parametrize("scale", SCALES, ids=_pct)
def test_zero_size_rect_scales_to_zero_size(scale: float) -> None:
    """Sinir durumu: sifir genislik/yukseklik cokmemeli, sifir kalmali."""
    r = Rect(x=100, y=100, w=0, h=0, dpi_scale=scale)
    p = logical_to_physical(r)
    assert (p.w, p.h) == (0, 0)
    l = physical_to_logical(r)
    assert (l.w, l.h) == (0, 0)


@pytest.mark.parametrize("bad_scale", [0.0, -1.0, -0.5, 0.5, 0.75, 0.99, 0.999999])
def test_logical_to_physical_rejects_scale_below_one(bad_scale: float) -> None:
    """Tur 2 duzeltmesi: yalnizca `<= 0` degil, `< 1.0` olan HER olcek
    reddedilir (0 < dpi_scale < 1.0 dahil) -- bkz. asagidaki
    REGRESSION testi ve modul dokumantasyonu."""
    r = Rect(x=0, y=0, w=10, h=10, dpi_scale=bad_scale)
    with pytest.raises(ValueError, match=r"dpi_scale >= 1\.0"):
        logical_to_physical(r)


@pytest.mark.parametrize("bad_scale", [0.0, -1.0, -0.5, 0.5, 0.75, 0.99, 0.999999])
def test_physical_to_logical_rejects_scale_below_one(bad_scale: float) -> None:
    """Tur 2 duzeltmesi: yalnizca `<= 0` degil, `< 1.0` olan HER olcek
    reddedilir (0 < dpi_scale < 1.0 dahil)."""
    r = Rect(x=0, y=0, w=10, h=10, dpi_scale=bad_scale)
    with pytest.raises(ValueError, match=r"dpi_scale >= 1\.0"):
        physical_to_logical(r)


# ---------------------------------------------------------------------------
# REGRESSION: tur 1'de tester'in buldugu kusur -- 0 < dpi_scale < 1.0
# sessizce kabul ediliyor ve round-trip garantisini sessizce bozuyordu.
# Bu test o davranisin GERI GELMEDIGINI dogrudan dogrular: ayni girdi
# artik ValueError ile reddedilir, sessizce yanlis sonuc URETMEZ.
# ---------------------------------------------------------------------------


def test_scale_below_one_is_rejected_not_silently_broken_REGRESSION() -> None:
    """Tester'in tur 1 bulgusu: `Rect(x=3,y=3,w=3,h=3,dpi_scale=0.5)`
    icin round-trip once sessizce bozuluyordu (3 -> fiziksel 2 -> geri
    donen 4, orijinalden farkli) cunku yalnizca `dpi_scale <= 0`
    reddediliyordu. Artik `dpi_scale < 1.0` tamami reddedildigi icin bu
    girdi hicbir zaman sessizce yanlis bir sonuc URETEMEZ -- ya acikca
    reddedilir ya da (dpi_scale >= 1.0 oldugunda) garanti tutar."""
    original = Rect(x=3, y=3, w=3, h=3, dpi_scale=0.5)

    with pytest.raises(ValueError, match=r"dpi_scale >= 1\.0"):
        logical_to_physical(original)

    with pytest.raises(ValueError, match=r"dpi_scale >= 1\.0"):
        physical_to_logical(original)


@pytest.mark.parametrize("bad_scale", [0.05, 0.1, 0.5, 0.6, 0.75, 0.9, 0.9999])
def test_scale_below_one_systematically_rejected_across_range_REGRESSION(
    bad_scale: float,
) -> None:
    """Tester'in sistematik olcumu ((0,1) araliginda gecerli girdilerin
    yaklasik yarisinda round-trip bozuluyordu) artik hicbir sekilde
    olusamaz: `(0, 1)` araligindaki HER deger, hangi (x,y,w,h) ile
    birlesirse birlessin, kayitsiz sartsiz reddedilir."""
    r = Rect(x=3, y=3, w=3, h=3, dpi_scale=bad_scale)
    with pytest.raises(ValueError):
        logical_to_physical(r)
    with pytest.raises(ValueError):
        physical_to_logical(r)


# ---------------------------------------------------------------------------
# 3. round-trip kararliligi
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("scale", SCALES, ids=_pct)
@pytest.mark.parametrize(("x", "y", "w", "h"), LOGICAL_SAMPLE_RECTS)
def test_round_trip_logical_to_physical_to_logical_is_always_stable(
    x: int, y: int, w: int, h: int, scale: float
) -> None:
    """Garanti edilen yon: mantiksal -> fiziksel -> mantiksal HER ZAMAN
    orijinali verir (bkz. modul dokumantasyonundaki ispat taslagi:
    yuvarlama hatasi <= 0.5, olcege (>=1) bolununce < 0.5 kalir)."""
    original = Rect(x=x, y=y, w=w, h=h, dpi_scale=scale)
    physical = logical_to_physical(original)
    recovered = physical_to_logical(physical)
    assert recovered == original


def test_round_trip_physical_to_logical_to_physical_can_drift() -> None:
    """Garanti EDILMEYEN yon: fiziksel -> mantiksal donusum kayiplidir
    (guvercin yuvasi ilkesi -- fiziksel uzay daha yogundur). Bu, bilincli
    ve belgelenmis bir sinirlamadir, bug degildir."""
    physical = Rect(x=7, y=0, w=1, h=1, dpi_scale=2.0)
    logical = physical_to_logical(physical)
    assert logical.x == 4  # round_away(7/2) = round_away(3.5) = 4
    recovered = logical_to_physical(logical)
    assert recovered.x == 8  # round_away(4*2) = 8 -- orijinal 7 KAYBOLDU
    assert recovered != physical


def test_round_trip_physical_to_logical_to_physical_holds_when_exact() -> None:
    """Fiziksel deger olcege tam bolunuyorsa (yuvarlama hic gerekmiyorsa)
    ters yon de kararlidir -- kayip yalnizca yuvarlama devreye girince
    olusur."""
    physical = Rect(x=100, y=200, w=300, h=400, dpi_scale=2.0)
    logical = physical_to_logical(physical)
    recovered = logical_to_physical(logical)
    assert recovered == physical


# ---------------------------------------------------------------------------
# 4. monitore-relatif <-> sanal masaustu (negatif koordinatli monitor)
# ---------------------------------------------------------------------------


def test_to_monitor_relative_on_primary_is_unchanged() -> None:
    r = Rect(x=100, y=50, w=200, h=80)
    rel = to_monitor_relative(r, PRIMARY)
    assert (rel.x, rel.y, rel.w, rel.h) == (100, 50, 200, 80)
    assert rel.monitor_index == PRIMARY.monitor_index
    assert rel.dpi_scale == PRIMARY.dpi_scale


def test_to_monitor_relative_on_negative_left_monitor() -> None:
    """En klasik tuzak: birincilin SOLUNDAKI monitorun sanal masaustu
    x koordinati negatiftir (LEFT_SECONDARY.x == -1280)."""
    r = Rect(x=-1200, y=10, w=50, h=50)  # LEFT_SECONDARY icinde bir bolge
    rel = to_monitor_relative(r, LEFT_SECONDARY)
    assert rel.x == 80  # -1200 - (-1280)
    assert rel.y == 10
    assert rel.dpi_scale == 1.25
    assert rel.monitor_index == 1


def test_to_monitor_relative_on_negative_above_monitor() -> None:
    """Ikinci klasik durum: birincilin USTUNDEKI monitor negatif y'ye
    sahiptir (ABOVE_SECONDARY.y == -1080)."""
    r = Rect(x=10, y=-1000, w=50, h=50)
    rel = to_monitor_relative(r, ABOVE_SECONDARY)
    assert rel.x == 10
    assert rel.y == 80  # -1000 - (-1080)


def test_to_virtual_desktop_places_rect_at_negative_coordinates() -> None:
    rel = Rect(x=80, y=10, w=50, h=50)
    absolute = to_virtual_desktop(rel, LEFT_SECONDARY)
    assert absolute.x == -1200
    assert absolute.y == 10
    assert absolute.dpi_scale == 1.25
    assert absolute.monitor_index == 1


@pytest.mark.parametrize("m", ALL_MONITORS, ids=lambda m: f"monitor_{m.monitor_index}")
def test_monitor_relative_round_trip_is_exact_no_rounding(m: Monitor) -> None:
    """Salt toplama/cikarma -- yuvarlama yok, HER ZAMAN kayipsiz."""
    samples = [(0, 0, 1, 1), (-50, -50, 10, 10), (5000, 5000, 1, 1), (m.x, m.y, m.w, m.h)]
    for x, y, w, h in samples:
        original = Rect(x=x, y=y, w=w, h=h)
        rel = to_monitor_relative(original, m)
        back = to_virtual_desktop(rel, m)
        assert (back.x, back.y, back.w, back.h) == (x, y, w, h)


# ---------------------------------------------------------------------------
# 5. karisik DPI: iki monitor farkli dpi_scale ile
# ---------------------------------------------------------------------------


def test_mixed_dpi_each_monitor_scales_with_its_own_factor() -> None:
    """PRIMARY %100, LEFT_SECONDARY %125, ABOVE_SECONDARY %150 -- ayni
    mantiksal boyut, farkli monitorlerde farkli fiziksel boyuta cevrilir."""
    logical_size = (100, 100)

    on_primary = logical_to_physical(Rect(x=0, y=0, w=logical_size[0], h=logical_size[1], dpi_scale=PRIMARY.dpi_scale))
    on_left = logical_to_physical(Rect(x=0, y=0, w=logical_size[0], h=logical_size[1], dpi_scale=LEFT_SECONDARY.dpi_scale))
    on_above = logical_to_physical(Rect(x=0, y=0, w=logical_size[0], h=logical_size[1], dpi_scale=ABOVE_SECONDARY.dpi_scale))

    assert (on_primary.w, on_primary.h) == (100, 100)
    assert (on_left.w, on_left.h) == (125, 125)
    assert (on_above.w, on_above.h) == (150, 150)


def test_mixed_dpi_placing_on_monitor_carries_that_monitors_scale() -> None:
    on_left_logical = Rect(x=50, y=50, w=100, h=100, dpi_scale=LEFT_SECONDARY.dpi_scale)
    placed = to_virtual_desktop(on_left_logical, LEFT_SECONDARY)
    assert placed.dpi_scale == 1.25
    assert placed.x == LEFT_SECONDARY.x + 50  # -1280 + 50 = -1230


# ---------------------------------------------------------------------------
# 6. intersect (genel geometri yardimcisi)
# ---------------------------------------------------------------------------


def test_intersect_basic_overlap_and_tag_propagation() -> None:
    a = Rect(x=0, y=0, w=100, h=100)
    b = Rect(x=50, y=50, w=100, h=100, monitor_index=3, dpi_scale=1.5)
    result = intersect(a, b)
    assert result == Rect(x=50, y=50, w=50, h=50, monitor_index=3, dpi_scale=1.5)


def test_intersect_no_overlap_returns_none() -> None:
    a = Rect(x=0, y=0, w=10, h=10)
    b = Rect(x=100, y=100, w=10, h=10)
    assert intersect(a, b) is None


def test_intersect_touching_edges_do_not_overlap() -> None:
    """Yari-acik aralik sozlesmesi: right/bottom HARIC uctur."""
    a = Rect(x=0, y=0, w=10, h=10)   # x in [0,10)
    b = Rect(x=10, y=0, w=10, h=10)  # x in [10,20) -- tam bitisik
    assert intersect(a, b) is None


# ---------------------------------------------------------------------------
# 7. bolge gecerliligi: classify_region
# ---------------------------------------------------------------------------


def test_classify_region_fully_inside_single_monitor() -> None:
    r = Rect(x=100, y=100, w=200, h=200)
    assert classify_region(r, ALL_MONITORS) == RegionValidity.INSIDE


def test_classify_region_outside_all_monitors() -> None:
    r = Rect(x=5000, y=5000, w=100, h=100)
    assert classify_region(r, ALL_MONITORS) == RegionValidity.OUTSIDE


def test_classify_region_partial_when_overflowing_off_virtual_desktop() -> None:
    """PRIMARY sag kenarindan (x=1920) tasan bolge; sagda baska monitor yok."""
    r = Rect(x=1900, y=100, w=200, h=100)
    assert classify_region(r, ALL_MONITORS) == RegionValidity.PARTIAL


def test_classify_region_inside_when_spanning_two_adjacent_monitors() -> None:
    """PRIMARY (y: 0..1080) ile ABOVE_SECONDARY (y: -1080..0) tam y=0'da
    bitisik. Sinirin ustunden altina yayilan bolge, birlesim tarafindan
    tam kapsanir -> INSIDE (PARTIAL degil)."""
    r = Rect(x=100, y=-50, w=100, h=100)  # y: -50..50
    assert classify_region(r, ALL_MONITORS) == RegionValidity.INSIDE


def test_classify_region_zero_area_rect_is_outside() -> None:
    assert classify_region(Rect(x=100, y=100, w=0, h=50), ALL_MONITORS) == RegionValidity.OUTSIDE
    assert classify_region(Rect(x=100, y=100, w=50, h=0), ALL_MONITORS) == RegionValidity.OUTSIDE


def test_classify_region_no_monitors_given_is_outside() -> None:
    assert classify_region(Rect(x=0, y=0, w=10, h=10), ()) == RegionValidity.OUTSIDE


def test_classify_region_exact_boundary_rect_is_inside_not_partial() -> None:
    """Tam sinirda oturan dikdortgen: rect == monitor sinirlari -> INSIDE."""
    r = Rect(x=0, y=0, w=1920, h=1080)
    assert classify_region(r, ALL_MONITORS) == RegionValidity.INSIDE


def test_classify_region_touching_edge_without_overlap_is_outside() -> None:
    """PRIMARY'nin hemen saginda, tam bitisik ama kesismeyen bolge."""
    r = Rect(x=1920, y=0, w=100, h=100)
    assert classify_region(r, ALL_MONITORS) == RegionValidity.OUTSIDE


# ---------------------------------------------------------------------------
# 8. monitore kirpma: clamp_to_monitor
# ---------------------------------------------------------------------------


def test_clamp_to_monitor_no_overflow_returns_equivalent_region() -> None:
    r = Rect(x=100, y=100, w=200, h=200)
    clamped = clamp_to_monitor(r, PRIMARY)
    assert clamped is not None
    assert (clamped.x, clamped.y, clamped.w, clamped.h) == (100, 100, 200, 200)
    assert clamped.monitor_index == PRIMARY.monitor_index
    assert clamped.dpi_scale == PRIMARY.dpi_scale


def test_clamp_to_monitor_clips_overflowing_rect() -> None:
    r = Rect(x=1800, y=1000, w=300, h=200)  # PRIMARY: 1920x1080
    clamped = clamp_to_monitor(r, PRIMARY)
    assert clamped is not None
    assert clamped.x == 1800
    assert clamped.y == 1000
    assert clamped.w == 120  # 1920 - 1800
    assert clamped.h == 80   # 1080 - 1000
    assert clamped.right == 1920
    assert clamped.bottom == 1080


def test_clamp_to_monitor_fully_outside_returns_none() -> None:
    r = Rect(x=5000, y=5000, w=100, h=100)
    assert clamp_to_monitor(r, PRIMARY) is None


def test_clamp_to_monitor_zero_width_returns_none() -> None:
    assert clamp_to_monitor(Rect(x=100, y=100, w=0, h=50), PRIMARY) is None


def test_clamp_to_monitor_exact_boundary_rect_is_unchanged() -> None:
    r = Rect(x=0, y=0, w=1920, h=1080)
    clamped = clamp_to_monitor(r, PRIMARY)
    assert clamped == Rect(
        x=0, y=0, w=1920, h=1080,
        monitor_index=PRIMARY.monitor_index, dpi_scale=PRIMARY.dpi_scale,
    )


def test_clamp_to_monitor_touching_edge_without_overlap_returns_none() -> None:
    assert clamp_to_monitor(Rect(x=1920, y=0, w=50, h=50), PRIMARY) is None


def test_clamp_to_monitor_on_negative_coordinate_monitor() -> None:
    """Sol/negatif monitorde de kirpma dogru calismali."""
    r = Rect(x=-1300, y=-10, w=100, h=50)  # LEFT_SECONDARY: x in [-1280,0), y in [0,1024)
    clamped = clamp_to_monitor(r, LEFT_SECONDARY)
    assert clamped is not None
    assert clamped.x == -1280
    assert clamped.y == 0
    assert clamped.w == 100 - (-1280 - (-1300))  # sol kenardan 20 birim tasti
    assert clamped.h == 40  # ust kenardan 10 birim tasti


def test_clamp_to_monitor_result_never_has_nonpositive_size() -> None:
    cases = [
        Rect(x=-100, y=-100, w=300, h=300),
        Rect(x=1800, y=-50, w=300, h=300),
        Rect(x=-9999, y=-9999, w=5, h=5),
    ]
    for r in cases:
        clamped = clamp_to_monitor(r, PRIMARY)
        if clamped is not None:
            assert clamped.w > 0
            assert clamped.h > 0
