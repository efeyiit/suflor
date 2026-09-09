"""T-003 -- TESTER'IN BAGIMSIZ dogrulama paketi (src/capture/dpi.py).

Bu dosya implementer'in test_dpi.py'sinden KOPYALANMADI. packet.md, env.md
ve tasarim dokumanindan (5.1, 5.6, 8.3 A2) yola cikilarak sifirdan
yazildi. Amac onaylamak degil, dokumante edilen iddialari -- ozellikle
round-trip ve yuvarlama simetrisi -- kendi rastgele/kapsamli
orneklememle sinamak (env.md "sizin sinama" talimati).

Sabit tohum kullanilir (deterministik, tekrar uretilebilir).
"""
from __future__ import annotations

import ast
import random
from pathlib import Path

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

SEED = 908171  # sabit tohum -- tekrar uretilebilirlik icin

DPI_MODULE_PATH = Path(__file__).resolve().parents[4] / "src" / "capture" / "dpi.py"


# ===========================================================================
# 1. SAFLIK -- otomatik statik denetim (elle grep yerine AST taramasi)
# ===========================================================================


def test_module_imports_only_allowlisted_names() -> None:
    """Paket: 'Yalniz stdlib + numpy.' Ayrica ctypes/win32/importlib/IO
    yasak. AST ile tum import ifadelerini tara, izin listesi disina
    cikani reddet."""
    source = DPI_MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    allowed_roots = {"__future__", "math", "collections", "enum", "typing", "src"}
    # Not: "os" bilerek disarida birakildi -- Turkce metin/docstring icinde
    # ("dosya", "kosul" vb.) siradan bir alt-dizge olarak COK sik geciyor ve
    # naif substring taramasi yanlis pozitif uretiyordu. Gercek `import os`
    # zaten yukaridaki AST tabanli found_roots/allowed_roots denetimiyle
    # yakalanir (os, allowed_roots'ta degil).
    forbidden_substrings = ("ctypes", "win32", "importlib", "socket", "subprocess")
    found_roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found_roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            found_roots.add(node.module.split(".")[0])
    assert found_roots <= allowed_roots, f"beklenmeyen import: {found_roots - allowed_roots}"
    lowered = source.lower()
    for bad in forbidden_substrings:
        assert bad not in lowered, f"yasak kalip modulde geciyor: {bad!r}"


def test_module_defines_no_class_and_no_mutable_module_state() -> None:
    """Paket: 'Sinif, durum, I/O yok.' `RegionValidity` (StrEnum) ve
    `Monitor` (TypeAlias) disinda sinif tanimi olmamali; modul seviyesinde
    mutable bir kap (list/dict/set) atanmamis olmali."""
    source = DPI_MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    class_names = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    assert class_names == ["RegionValidity"], f"beklenmeyen sinif(lar): {class_names}"
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and not target.id.startswith("_"):
                    assert isinstance(node.value, (ast.Tuple, ast.Constant)) or isinstance(
                        node.value, ast.Call
                    ), f"modul seviyesinde supheli mutable atama: {target.id}"


def test_functions_are_deterministic_same_input_same_output() -> None:
    """Ayni girdiyle iki kez cagirinca ayni sonuc (gizli durum/rastgelelik
    yok)."""
    r = Rect(x=-137, y=42, w=301, h=17, monitor_index=2, dpi_scale=1.75)
    m = Rect(x=-500, y=-500, w=1000, h=1000, monitor_index=1, dpi_scale=1.25)
    assert logical_to_physical(r) == logical_to_physical(r)
    assert physical_to_logical(r) == physical_to_logical(r)
    assert to_monitor_relative(r, m) == to_monitor_relative(r, m)
    assert to_virtual_desktop(r, m) == to_virtual_desktop(r, m)
    assert intersect(r, m) == intersect(r, m)
    assert clamp_to_monitor(r, m) == clamp_to_monitor(r, m)
    assert classify_region(r, [m]) == classify_region(r, [m])


def test_input_rect_is_never_mutated_and_functions_return_new_objects() -> None:
    """Sozlesme: `Rect` dondurulmus, mutasyon zaten imkansiz olmali
    (frozen dataclass) ve donusler yeni nesne olmali (ayni nesneyi
    donup 'mutasyon' yapmis gibi davranmamali)."""
    r = Rect(x=10, y=10, w=100, h=100, dpi_scale=1.5)
    with pytest.raises(Exception):
        r.x = 999  # type: ignore[misc]
    p = logical_to_physical(r)
    assert p is not r
    assert r == Rect(x=10, y=10, w=100, h=100, dpi_scale=1.5)  # r degismedi


# ===========================================================================
# 2. YUVARLAMA SIMETRISI (env.md saldiri noktasi #2)
# ===========================================================================


def test_rounding_is_symmetric_across_wide_random_sample() -> None:
    """-2.5 ile 2.5 ayni yonde (disari) yuvarlanmali; banker's rounding
    sizmamali. Genis, rastgele bir ornek uzerinde dogrula."""
    rng = random.Random(SEED)
    for _ in range(200_000):
        v = rng.uniform(-5000, 5000)
        assert _round_half_away_from_zero(v) == -_round_half_away_from_zero(-v), v


def test_rounding_half_integer_boundaries_go_away_from_zero() -> None:
    """Tam sayi + 0.5 bicimindeki her deger SIFIRDAN UZAGA yuvarlanmali
    (Python round()'un aksine)."""
    for i in range(-50_000, 50_000):
        v = i + 0.5
        expected = i + 1 if v > 0 else i  # away-from-zero; v==0.5*... asla 0 olmaz burada
        got = _round_half_away_from_zero(v)
        assert got == expected, (v, got, expected)


def test_rounding_matches_python_round_away_reference_impl() -> None:
    """Bagimsiz referans implementasyonla (Decimal tabanli ROUND_HALF_UP
    varyanti, isaretli) karsilastir -- implementer'in kendi fonksiyonuna
    guvenmeden ikinci bir yontemle capraz dogrulama."""
    import decimal

    rng = random.Random(SEED + 1)
    ctx = decimal.Context(rounding=decimal.ROUND_HALF_UP)
    for _ in range(20_000):
        v = rng.uniform(-100_000, 100_000)
        sign = -1 if v < 0 else 1
        ref = sign * int(ctx.create_decimal(str(abs(v))).to_integral_value())
        got = _round_half_away_from_zero(v)
        assert got == ref, (v, got, ref)


# ===========================================================================
# 3. ROUND-TRIP: mantiksal -> fiziksel -> mantiksal (env.md saldiri #1)
# ===========================================================================


IN_DOMAIN_SCALES = (1.0, 1.02, 1.1, 1.2, 1.25, 1.33, 1.5, 1.6, 1.75, 1.8, 1.9, 2.0, 2.25, 2.5, 3.0, 4.0)


def test_round_trip_logical_physical_logical_random_fuzz_in_domain() -> None:
    """Paketin iddiasi: mantiksal->fiziksel->mantiksal sapma olmamali.
    Kendi genis, rastgele orneklemim (negatif koordinatlar, tek sayi
    genislikler, tam olmayan olcekler dahil) -- implementer'in ornekleri
    kullanilmiyor."""
    rng = random.Random(SEED + 2)
    failures: list[tuple[int, int, int, int, float]] = []
    for _ in range(50_000):
        x = rng.randint(-200_000, 200_000)
        y = rng.randint(-200_000, 200_000)
        w = rng.randint(0, 200_000)
        h = rng.randint(0, 200_000)
        scale = rng.choice(IN_DOMAIN_SCALES)
        original = Rect(x=x, y=y, w=w, h=h, dpi_scale=scale)
        physical = logical_to_physical(original)
        recovered = physical_to_logical(physical)
        if recovered != original:
            failures.append((x, y, w, h, scale))
    assert not failures, f"round-trip {len(failures)} durumda bozuldu, ornekler: {failures[:5]}"


@pytest.mark.parametrize("scale", IN_DOMAIN_SCALES)
def test_round_trip_holds_for_odd_widths_and_negative_coords(scale: float) -> None:
    """env.md ozellikle 'tek sayi genislikler' ve negatif koordinatlari
    isaret ediyor -- ayri, kucuk ve okunabilir bir test olarak da dahil."""
    for x, y, w, h in [
        (-1, -1, 1, 1),
        (-2001, 777, 333, 555),
        (7, -13, 9999, 1),
        (-1, 0, 1, 0),
        (0, -1, 0, 1),
    ]:
        original = Rect(x=x, y=y, w=w, h=h, dpi_scale=scale)
        recovered = physical_to_logical(logical_to_physical(original))
        assert recovered == original, (x, y, w, h, scale)


def test_round_trip_claim_as_documented_is_scale_ge_1_only_FIXED() -> None:
    """TUR 2 -- bayatlamis iddia guncellendi (bug degil, bulgu duzeldi).

    Tur 1 BULGUSU: modul dokumantasyonu round-trip'i KOSULSUZ 'HER ZAMAN
    dogru' diye tanimliyordu ama kodun TEK girdi denetimi `dpi_scale <= 0`
    idi -- yani `dpi_scale` (0, 1) araligindaki degerleri SESSIZCE gecerli
    kabul edip yanlis sonuc uretiyordu (`Rect(x=3,y=3,w=3,h=3,
    dpi_scale=0.5)` icin 3 -> 2 -> 4).

    TUR 2 DUZELTMESI: `logical_to_physical` / `physical_to_logical` artik
    `dpi_scale < 1.0` olan HER girdiyi `ValueError` ile reddediyor (yalniz
    `<= 0` degil). Docstring'in "HER ZAMAN dogru" iddiasi da "kodun kabul
    ettigi HER girdi icin (yani dpi_scale >= 1.0)" diye daraltildi. Sonuc:
    `dpi_scale=0.5` gibi bir girdi artik SESSIZCE yanlis sonuc URETEMEZ --
    ya acikca reddedilir (bu test bunu dogrular) ya da (>=1.0 oldugunda)
    garanti gercekten tutar (bkz. asagidaki
    `test_round_trip_logical_physical_logical_random_fuzz_in_domain` ve
    diger round-trip testleri)."""
    original = Rect(x=3, y=3, w=3, h=3, dpi_scale=0.5)  # tur-1 bulgusundaki AYNI girdi

    with pytest.raises(ValueError, match=r"dpi_scale >= 1\.0"):
        logical_to_physical(original)
    with pytest.raises(ValueError, match=r"dpi_scale >= 1\.0"):
        physical_to_logical(original)


def test_scale_below_one_systematically_rejected_across_range_FIXED() -> None:
    """TUR 2 -- bayatlamis iddia guncellendi (bug degil, bulgu duzeldi).

    Tur 1'de bu test, (0,1) araligindaki genis bir taramanin round-trip'i
    SISTEMATIK olarak bozdugunu (mismatches > %30) olcerek bulguyu
    nicelendiriyordu. Artik `logical_to_physical` bu araligin TAMAMINI
    `ValueError` ile pesin reddettigi icin `physical_to_logical` cagrisina
    hic ULASILMIYOR -- yani "sessiz yanlis sonuc" sinifi tamamen ortadan
    kalkti. Bu test artik ayni taramayi, HER degerin (istisnasiz)
    reddedildigini dogrulayacak sekilde kosuyor."""
    total = 0
    rejected = 0
    for scale_hundredths in range(5, 100, 5):  # 0.05 .. 0.95
        scale = scale_hundredths / 100.0
        for L in range(-30, 31):
            r = Rect(x=L, y=0, w=1, h=1, dpi_scale=scale)
            total += 1
            with pytest.raises(ValueError):
                logical_to_physical(r)
            rejected += 1
    assert rejected == total, (
        f"(0,1) araliginda {total - rejected}/{total} deger sessizce kabul "
        "edildi -- tamami reddedilmeli"
    )


def test_scale_exactly_one_is_accepted_not_off_by_one_TUR2() -> None:
    """TUR 2 ek kontrol: sinir DEGERIN kendisi (`dpi_scale == 1.0`) yanlis-
    likla reddedilmemeli -- yalnizca kesin altindaki degerler reddedilir.
    Kapali/acik aralik hatasi (`<` yerine `<=` yazilmis olabilir) bu testle
    yakalanir."""
    r = Rect(x=11, y=-22, w=333, h=444, dpi_scale=1.0)
    physical = logical_to_physical(r)  # ValueError firlatmamali
    assert physical == r  # %100 olcekte kimlik donusumu
    recovered = physical_to_logical(physical)  # ValueError firlatmamali
    assert recovered == r


def test_scale_just_below_one_is_rejected_TUR2() -> None:
    """TUR 2 ek kontrol: `1.0`'a asiri yakin ama kesinlikle altinda olan
    degerler (`0.999999`, `1.0 - 1e-9`) de reddedilmeli -- kayan nokta
    karsilastirmasinda `<` gercekten kesin mi diye dogrudan sinar."""
    for bad in (0.999999, 1.0 - 1e-9, 0.9999999999):
        with pytest.raises(ValueError):
            logical_to_physical(Rect(x=0, y=0, w=1, h=1, dpi_scale=bad))
        with pytest.raises(ValueError):
            physical_to_logical(Rect(x=0, y=0, w=1, h=1, dpi_scale=bad))


def test_scale_just_above_one_is_accepted_TUR2() -> None:
    """TUR 2 ek kontrol: `1.0`'in hemen ustundeki degerler kabul edilmeli
    -- sinirin YANLIS tarafa kaymadigini (`<=` yerine `<` oldugunu) ikinci
    yonden dogrular."""
    r = Rect(x=3, y=3, w=3, h=3, dpi_scale=1.0000001)
    logical_to_physical(r)  # ValueError firlatmamali
    physical_to_logical(r)  # ValueError firlatmamali


def test_value_error_message_explains_why_not_just_invalid_TUR2() -> None:
    """TUR 2 ek kontrol: pipeline'da bu mesaj 5.6'daki 'bolge gecersiz'
    bandina donusecek -- yalniz 'invalid' demek yetmez, kullaniciya/
    loglayan koda NEDEN gecersiz oldugunu (esik deger + gerekce) anlatmali.
    Gelen degerin kendisi de mesajda gorunmeli (hata ayiklama icin)."""
    for bad_scale in (0.5, 0.0, -3.0):
        r = Rect(x=0, y=0, w=1, h=1, dpi_scale=bad_scale)
        with pytest.raises(ValueError) as exc_info:
            logical_to_physical(r)
        msg = str(exc_info.value)
        assert msg.strip().lower() != "invalid", f"mesaj yalnizca 'invalid' -- aciklayici degil: {msg!r}"
        assert len(msg) > 20, f"mesaj cok kisa, aciklayici olamaz: {msg!r}"
        assert "1.0" in msg or "1,0" in msg, f"mesaj esik degeri (1.0) belirtmiyor: {msg!r}"
        assert repr(bad_scale) in msg or str(bad_scale) in msg, (
            f"mesaj gelen gecersiz degeri ({bad_scale!r}) icermiyor: {msg!r}"
        )


def test_reverse_round_trip_physical_logical_physical_can_drift_when_inexact() -> None:
    """Dokumante edilen SINIRLAMA: fiziksel->mantiksal->fiziksel kayipli
    olabilir. Bagimsiz bir ornekle (implementer'inkinden farkli) dogrula
    -- bu bir bug degil, ama iddia edilen davranis gercekten boyle mi?"""
    physical = Rect(x=9, y=0, w=1, h=1, dpi_scale=2.0)
    logical = physical_to_logical(physical)
    assert logical.x == 5  # round_away(9/2) = round_away(4.5) = 5
    back = logical_to_physical(logical)
    assert back.x == 10  # round_away(5*2) = 10 -- orijinal 9 kayboldu
    assert back != physical


def test_reverse_round_trip_holds_when_physical_exactly_divisible() -> None:
    physical = Rect(x=400, y=600, w=200, h=100, dpi_scale=4.0)
    logical = physical_to_logical(physical)
    back = logical_to_physical(logical)
    assert back == physical


# ===========================================================================
# 4. NEGATIF KOORDINATLI MONITOR (env.md saldiri #3)
# ===========================================================================


def test_relative_virtual_round_trip_negative_left_and_above_and_corner() -> None:
    """Sol, ust VE sol-ust kosede (hem x hem y negatif) monitorler icin
    iki yonlu round-trip -- implementer'in monitor duzeninden FARKLI bir
    kurulum kullaniliyor (bagimsizlik icin)."""
    monitors = [
        Rect(x=-1600, y=0, w=1600, h=900, monitor_index=1, dpi_scale=1.0),      # sol
        Rect(x=0, y=-900, w=1600, h=900, monitor_index=2, dpi_scale=1.5),        # ust
        Rect(x=-1600, y=-900, w=1600, h=900, monitor_index=3, dpi_scale=2.0),    # sol-ust kose
    ]
    rng = random.Random(SEED + 3)
    for m in monitors:
        for _ in range(500):
            x = rng.randint(-5000, 5000)
            y = rng.randint(-5000, 5000)
            w = rng.randint(0, 3000)
            h = rng.randint(0, 3000)
            original = Rect(x=x, y=y, w=w, h=h)
            rel = to_monitor_relative(original, m)
            back = to_virtual_desktop(rel, m)
            assert (back.x, back.y, back.w, back.h) == (x, y, w, h)


def test_to_monitor_relative_negative_monitor_produces_correct_offset() -> None:
    m = Rect(x=-2560, y=-1440, w=2560, h=1440, monitor_index=5, dpi_scale=1.0)
    r = Rect(x=-2000, y=-1000, w=10, h=10)
    rel = to_monitor_relative(r, m)
    assert (rel.x, rel.y) == (560, 440)  # -2000-(-2560)=560 ; -1000-(-1440)=440
    assert rel.monitor_index == 5


def test_negative_monitor_metadata_carried_correctly_not_swapped() -> None:
    """Sol monitorun dpi_scale'i, birincilin degil, KENDI degeri olarak
    tasinmali."""
    primary = Rect(x=0, y=0, w=1920, h=1080, monitor_index=0, dpi_scale=1.0)
    left = Rect(x=-1920, y=0, w=1920, h=1080, monitor_index=1, dpi_scale=2.0)
    r_on_left = Rect(x=-1000, y=100, w=50, h=50)
    rel = to_monitor_relative(r_on_left, left)
    assert rel.dpi_scale == 2.0  # primary'nin 1.0'i degil
    assert rel.monitor_index == 1


# ===========================================================================
# 5. KARISIK DPI (env.md saldiri #4)
# ===========================================================================


def test_mixed_dpi_three_monitors_scale_never_crosses_over() -> None:
    """Uc farkli olcekli monitor -- her birinin kendi olcegiyle
    donusmesi, digerlerinin olceginin sizmamasi."""
    mons = {
        "a": Rect(x=0, y=0, w=1000, h=1000, monitor_index=0, dpi_scale=1.0),
        "b": Rect(x=1000, y=0, w=1000, h=1000, monitor_index=1, dpi_scale=1.5),
        "c": Rect(x=2000, y=0, w=1000, h=1000, monitor_index=2, dpi_scale=2.0),
    }
    logical = Rect(x=10, y=10, w=100, h=100)
    physical_sizes = {}
    for key, mon in mons.items():
        physical = logical_to_physical(Rect(x=logical.x, y=logical.y, w=logical.w, h=logical.h, dpi_scale=mon.dpi_scale))
        physical_sizes[key] = (physical.w, physical.h)
    assert physical_sizes["a"] == (100, 100)
    assert physical_sizes["b"] == (150, 150)
    assert physical_sizes["c"] == (200, 200)
    # capraz kontrol: b'nin olcegi a icin kullanilmadi
    assert physical_sizes["a"] != physical_sizes["b"]
    assert physical_sizes["b"] != physical_sizes["c"]


def test_clamp_to_monitor_uses_monitor_dpi_scale_not_rects_own() -> None:
    """`rect`in tasidigi (belki yanlis/eski) dpi_scale, kirpma sonrasi
    yerini monitorun otoriter degerine birakmali."""
    stale_rect = Rect(x=50, y=50, w=5000, h=5000, dpi_scale=9.99, monitor_index=42)
    monitor = Rect(x=0, y=0, w=1920, h=1080, monitor_index=7, dpi_scale=1.25)
    clamped = clamp_to_monitor(stale_rect, monitor)
    assert clamped is not None
    assert clamped.dpi_scale == 1.25
    assert clamped.monitor_index == 7


# ===========================================================================
# 6. SINIR DURUMLARI (env.md saldiri #5)
# ===========================================================================


@pytest.mark.parametrize(
    ("rect_args", "monitor_args", "expected_none"),
    [
        # tamamen disarida
        (dict(x=9000, y=9000, w=10, h=10), dict(x=0, y=0, w=1920, h=1080), True),
        # tam sinirda oturan (esit) -- kesisim var, None DEGIL
        (dict(x=0, y=0, w=1920, h=1080), dict(x=0, y=0, w=1920, h=1080), False),
        # sinira deger ama kesismeyen: rect.right == monitor.x
        (dict(x=-100, y=0, w=100, h=10), dict(x=0, y=0, w=1920, h=1080), True),
        # sinira deger digger yon: rect.x == monitor.right
        (dict(x=1920, y=0, w=10, h=10), dict(x=0, y=0, w=1920, h=1080), True),
        # sifir genislik
        (dict(x=100, y=100, w=0, h=50), dict(x=0, y=0, w=1920, h=1080), True),
        # sifir yukseklik
        (dict(x=100, y=100, w=50, h=0), dict(x=0, y=0, w=1920, h=1080), True),
        # bir piksel kesisim (kose)
        (dict(x=1919, y=1079, w=10, h=10), dict(x=0, y=0, w=1920, h=1080), False),
    ],
    ids=[
        "fully_outside", "exact_boundary_match", "touches_right_of_monitor_start",
        "touches_monitor_right_edge", "zero_width", "zero_height", "one_pixel_corner_overlap",
    ],
)
def test_intersect_boundary_matrix(rect_args: dict, monitor_args: dict, expected_none: bool) -> None:
    result = intersect(Rect(**rect_args), Rect(**monitor_args))
    if expected_none:
        assert result is None
    else:
        assert result is not None
        assert result.w > 0 and result.h > 0


def test_intersect_one_pixel_corner_overlap_has_exact_size() -> None:
    a = Rect(x=1919, y=1079, w=10, h=10)
    b = Rect(x=0, y=0, w=1920, h=1080)
    result = intersect(a, b)
    assert result is not None
    assert (result.x, result.y, result.w, result.h) == (1919, 1079, 1, 1)


def test_negative_width_height_does_not_crash_anywhere() -> None:
    """paket bunu zorunlu kilmadi -- ama en azindan COKMEMELI. Her
    fonksiyonu negatif w/h ile bir kez cagirip istisna beklenmedigini
    dogrula (davranis 'sessiz ama tutarli' mi diye ayrica kontrol
    edilir)."""
    weird = Rect(x=10, y=10, w=-50, h=-30, dpi_scale=1.5)
    monitor = Rect(x=0, y=0, w=1920, h=1080)
    # cokme yok:
    logical_to_physical(weird)
    physical_to_logical(weird)
    to_monitor_relative(weird, monitor)
    to_virtual_desktop(weird, monitor)
    intersect(weird, monitor)
    clamp_to_monitor(weird, monitor)
    classify_region(weird, [monitor])


def test_negative_width_height_is_treated_as_no_area_not_silently_valid() -> None:
    """Gozlem: negatif w/h -- intersect/clamp/classify onu 'alani yok'
    olarak ele aliyor (None / OUTSIDE), 'gorunuse gore hala gecerli'
    bir dikdortgen DONDURMUYOR. Bu, en azindan GUVENLI bir secim (bug
    degil ama modul dokumantasyonunda ACIKCA yazilmiyor)."""
    weird = Rect(x=10, y=10, w=-50, h=-30, dpi_scale=1.0)
    monitor = Rect(x=0, y=0, w=1920, h=1080)
    assert intersect(weird, monitor) is None
    assert clamp_to_monitor(weird, monitor) is None
    assert classify_region(weird, [monitor]) == RegionValidity.OUTSIDE


def test_classify_region_touching_two_monitors_exactly_at_seam_is_inside() -> None:
    """Farkli bir monitor duzeni: dikey degil YATAY bitisik iki monitor,
    tam dikisin uzerine oturan bolge -> INSIDE olmali (union kapsuyor)."""
    left = Rect(x=0, y=0, w=1000, h=1000, monitor_index=0)
    right = Rect(x=1000, y=0, w=1000, h=1000, monitor_index=1)
    seam_rect = Rect(x=900, y=100, w=200, h=100)  # 900..1100, dikis 1000'i asiyor
    assert classify_region(seam_rect, [left, right]) == RegionValidity.INSIDE


def test_classify_region_gap_between_non_adjacent_monitors_is_partial() -> None:
    """Iki monitor arasinda BOSLUK varsa (bitisik degiller) ve bolge o
    bosluga tasiyorsa PARTIAL olmali."""
    left = Rect(x=0, y=0, w=1000, h=1000, monitor_index=0)
    right = Rect(x=1500, y=0, w=1000, h=1000, monitor_index=1)  # 1000..1500 arasi bosluk
    spanning_gap = Rect(x=900, y=100, w=700, h=100)  # 900..1600
    assert classify_region(spanning_gap, [left, right]) == RegionValidity.PARTIAL


def test_classify_region_single_pixel_rect_inside() -> None:
    m = Rect(x=0, y=0, w=100, h=100)
    assert classify_region(Rect(x=50, y=50, w=1, h=1), [m]) == RegionValidity.INSIDE


def test_classify_region_single_pixel_rect_just_outside() -> None:
    m = Rect(x=0, y=0, w=100, h=100)
    assert classify_region(Rect(x=100, y=50, w=1, h=1), [m]) == RegionValidity.OUTSIDE


def test_clamp_zero_area_after_clip_returns_none_not_zero_rect() -> None:
    """Paket: 'boyut sifira duserse bunu acikca bildir.' None donmeli,
    w=0/h=0 tasiyan 'sozde gecerli' bir Rect degil."""
    r = Rect(x=1919, y=0, w=100, h=100)  # sag kenardan 1 px icerde basliyor
    m = Rect(x=0, y=0, w=1920, h=1080)
    clamped = clamp_to_monitor(r, m)
    assert clamped is not None
    assert clamped.w == 1  # 1920-1919
    # simdi tamamen disariya alalim
    r_outside = Rect(x=1920, y=0, w=100, h=100)
    assert clamp_to_monitor(r_outside, m) is None


# ===========================================================================
# 7. TASARIM DOKUMANI UYUMU (env.md saldiri #8) -- 5.6 "bolge gecersiz"
# ===========================================================================


def test_region_validity_enum_covers_the_three_states_design_doc_needs() -> None:
    """5.6: Capture asamasi 'bolge gecersiz' durumunu bu siniflandirmaya
    dayandiriyor -- INSIDE disindaki her sey (PARTIAL, OUTSIDE) capture
    katmaninin 'gecersiz/duraklat' kararina girdi olabilecek sekilde
    ayirt edilebilir olmali."""
    assert set(RegionValidity) == {RegionValidity.INSIDE, RegionValidity.PARTIAL, RegionValidity.OUTSIDE}
    m = Rect(x=0, y=0, w=1000, h=1000)
    assert classify_region(Rect(x=100, y=100, w=100, h=100), [m]) == RegionValidity.INSIDE
    assert classify_region(Rect(x=950, y=950, w=100, h=100), [m]) == RegionValidity.PARTIAL
    assert classify_region(Rect(x=5000, y=5000, w=10, h=10), [m]) == RegionValidity.OUTSIDE


def test_classify_region_empty_monitor_list_is_outside_not_crash() -> None:
    assert classify_region(Rect(x=0, y=0, w=10, h=10), []) == RegionValidity.OUTSIDE
