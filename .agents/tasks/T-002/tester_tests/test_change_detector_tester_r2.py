"""T-002 -- ChangeDetector, TUR 2 bagimsiz tester dogrulamasi.

Bu dosya .agents/tasks/T-002/tester_tests/test_change_detector_tester.py (TUR 1,
onceki bir tester tarafindan yazildi) ile AYNI seyi tekrar etmez: o dosya
zaten (bu implementasyona karsi) tamamen yesil (bkz. r2-tester_tests_round1_
rerun.txt). Bu dosya SIFIRDAN, implementer'in `delivery.md`/`evidence/`
klasoru OKUNMADAN, implementer'in yardimci fonksiyonlari (`_pattern`,
`_jitter`, 16px dosemeli blok vs.) KOPYALANMADAN yazildi -- farkli uretim
teknikleri kullanir:
  - kucuk-bolge/cokme taramasi icin tam kombinasyon (1..24 x 1..24 + ekstra
    oranlar) + genislik/yukseklik "bit butcesi" yapisal analizi
  - esik testleri icin RASTGELE/tahmini icerik degil, dogrudan 8x9 izgara
    piksel kontrolu ile INSA EDILMIS (constructed) goruntuler -- Hamming
    mesafesi olculmez, INSA EDILIR (bkz. `_grid_image`/`_flipped_grid`)
  - "harf harf yazma" simulasyonu: implementer'in 16px dosemeli deseni
    yerine, sabit bir gurultu tuvalinin soldan saga kademeli acilmasi
  - livelock/jitter icin implementer'in `_jitter` fonksiyonu degil, ayri bir
    RNG akisi ve farkli genlik semasi
"""
from __future__ import annotations

import itertools
import sys
import time
import warnings
from pathlib import Path
from typing import Sequence

import numpy as np
import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.capture import change_detector as cd  # noqa: E402
from src.capture.change_detector import ChangeDetector  # noqa: E402
from src.contracts.models import Frame, ImageArray, Rect  # noqa: E402

_seq = 0


def _frame(image: ImageArray, rect: Rect) -> Frame:
    global _seq
    _seq += 1
    return Frame(image=image, rect=rect, captured_at=float(_seq), seq=_seq)


# ===========================================================================
# GOREV 1 -- cokme gercekten gitti mi? genis boyut taramasi, warnings=error
# ===========================================================================

def _crash_scan_sizes() -> list[tuple[int, int]]:
    full_grid = list(itertools.product(range(1, 25), range(1, 25)))  # 1x1..24x24
    extras = [(1, 50), (50, 1), (3, 80), (80, 3), (600, 200)]
    return full_grid + extras


@pytest.mark.parametrize("h,w", _crash_scan_sizes())
def test_no_crash_no_warning_bool_return_across_full_size_sweep(h: int, w: int) -> None:
    """Gorev 1: 1x1..24x24 tum kombinasyonlar + ekstra oranlar, `error`
    filtresi altinda. Cokme, uyari (RuntimeWarning dahil), veya bool
    olmayan donus -> basarisizlik."""
    detector = ChangeDetector()
    rect = Rect(x=0, y=0, w=w, h=h)
    # iki farkli, deterministik (ama implementer'in _pattern'inden BAGIMSIZ)
    # icerik: dogrusal gradyan (baseline) ve tersi (aday)
    grad = (np.linspace(0, 255, num=h * w, dtype=np.float64)
            .reshape(h, w).astype(np.uint8))
    img_a: ImageArray = np.stack([grad, grad, grad], axis=-1).astype(np.uint8)
    img_b: ImageArray = np.stack([255 - grad, 255 - grad, 255 - grad], axis=-1).astype(np.uint8)

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        r1 = detector.has_changed(_frame(img_a, rect))
        r2 = detector.has_changed(_frame(img_b, rect))
        r3 = detector.has_changed(_frame(img_b, rect))

    for r in (r1, r2, r3):
        assert type(r) is bool
    assert r1 is True  # ilk kare kosulsuz


# ===========================================================================
# GOREV 2 -- regresyon: TUR 1'de saglam bulunan davranislar hala tutuyor mu
# ===========================================================================

_CANVAS_SHAPE = (200, 600)  # (h, w)


def _noise_canvas(shape: tuple[int, int], seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed=seed)
    return rng.integers(20, 236, size=shape, dtype=np.uint8)


def _typing_frame(revealed_cols: int, shape: tuple[int, int] = _CANVAS_SHAPE,
                   seed: int = 4242, bg: int = 128) -> ImageArray:
    """Sabit bir 'metin tuvalinin' soldan saga kademeli acilmasi -- harf
    harf yazma simulasyonu, implementer'in dosemeli desenine ALTERNATIF bir
    teknik."""
    h, w = shape
    canvas = _noise_canvas(shape, seed=seed)
    frame2d = np.full((h, w), bg, dtype=np.uint8)
    revealed_cols = max(0, min(w, revealed_cols))
    frame2d[:, :revealed_cols] = canvas[:, :revealed_cols]
    return np.stack([frame2d, frame2d, frame2d], axis=-1).astype(np.uint8)


def _build_diverging_reveal_chain(
    w: int, threshold: int, shape: tuple[int, int] = _CANVAS_SHAPE,
    seed: int = 4242, col_step: int = 5,
) -> list[int]:
    """Kademeli olarak acilan (revealed_cols artan) bir 'yazma' zincirinin
    KONTROL NOKTALARINI uretir -- ardisik her checkpoint cifti, GERCEKTEN
    esik disi (hamming > threshold) olacak sekilde secilir (bunu TAHMIN
    etmek yerine `cd._dhash`/`cd._hamming_distance` ile ZAMANINDA olcerek).
    Boylece '520 ile 600 sanki ayniymis gibi gorunuyor' turu bir tuzaga
    dusmeden, her checkpoint gercekten 'hala aktif olarak degisiyor' bir
    ara-adimi temsil eder. Zincir daima tam-acilmis (`w`) ile biter."""
    checkpoints = [0]
    last_hash = cd._dhash(_typing_frame(0, shape=shape, seed=seed), hash_size=8)
    cols = 0
    while cols < w:
        cols = min(w, cols + col_step)
        current_hash = cd._dhash(_typing_frame(cols, shape=shape, seed=seed), hash_size=8)
        if cd._hamming_distance(last_hash, current_hash) > threshold:
            checkpoints.append(cols)
            last_hash = current_hash

    # tam-acilmis (`w`) durum, dogal taramada zaten esik-disi bir adim
    # olarak eklendiyse dokunma; degilse (coarse hash son birkac sutunu
    # ayirt edemiyorsa -- bu ayri, bloke etmeyen bir gozlem) son checkpoint'i
    # `w` olarak ETIKETLE (fiziksel olarak zaten ayirt edilemez oldugundan
    # bu, zincirin "ardisik her cift esik-disi farkli" degismezini bozmaz).
    if checkpoints[-1] != w:
        final_hash = cd._dhash(_typing_frame(w, shape=shape, seed=seed), hash_size=8)
        if cd._hamming_distance(last_hash, final_hash) > threshold:
            checkpoints.append(w)
        else:
            checkpoints[-1] = w
    return checkpoints


def test_regression_debounce_typing_never_confirms_mid_stream() -> None:
    """Her checkpoint ciftinin GERCEKTEN esik-disi farkli oldugu (olculmus,
    tahmin edilmemis) bir 'harf harf yazma' zinciri: hicbir ara adim
    onaylanmamali; yazma durup son durum 2. kez gorulunce onay gelmeli."""
    threshold = cd._DEFAULT_THRESHOLD
    checkpoints = _build_diverging_reveal_chain(600, threshold)
    assert len(checkpoints) >= 5, "test zinciri yeterince adim uretmedi (kurulum hatasi)"

    # kurulum saglamasi: zincirdeki ARDISIK HER cift GERCEKTEN esik-disi mi
    # (varsayimla degil, olcerek) -- aksi halde test gecersiz olur
    hashes = [cd._dhash(_typing_frame(c), hash_size=8) for c in checkpoints]
    for i in range(len(hashes) - 1):
        dist = cd._hamming_distance(hashes[i], hashes[i + 1])
        assert dist > threshold, (
            f"zincir kurulumu bozuk: checkpoint {checkpoints[i]}->{checkpoints[i+1]} "
            f"hamming={dist} <= threshold={threshold}"
        )

    detector = ChangeDetector()
    rect = Rect(0, 0, 600, 200)
    assert detector.has_changed(_frame(_typing_frame(checkpoints[0]), rect)) is True

    for cols in checkpoints[1:]:
        result = detector.has_changed(_frame(_typing_frame(cols), rect))
        assert result is False, f"revealed_cols={cols} erken onaylandi (henuz yazma bitmedi)"

    # yukaridaki dongude son checkpoint (tam ekran) zaten 1. kez goruldu (aday, count=1).
    # yazma durur, AYNI son durum bir kez daha gorulur -> 2. ardisik ayni -> onay
    final = _typing_frame(checkpoints[-1])
    assert detector.has_changed(_frame(final, rect)) is True


def _moving_bar_frame(t: int, shape: tuple[int, int] = _CANVAS_SHAPE, bar_w: int = 24) -> ImageArray:
    h, w = shape
    frame2d = np.full((h, w), 40, dtype=np.uint8)
    pos = (t * 7) % max(1, (w - bar_w))
    frame2d[:, pos:pos + bar_w] = 220
    return np.stack([frame2d, frame2d, frame2d], axis=-1).astype(np.uint8)


def test_regression_no_livelock_continuous_motion_periodically_confirms() -> None:
    """Surekli hareket eden (kayan cubuk) sahne -- sonsuza kadar 'henuz
    kararli degil' dememeli, periyodik onay uretmeli."""
    detector = ChangeDetector()
    rect = Rect(0, 0, 600, 200)
    confirmations = 0
    for t in range(400):
        if detector.has_changed(_frame(_moving_bar_frame(t, rect_shape := _CANVAS_SHAPE), rect)):
            confirmations += 1
    assert confirmations > 3, f"acilik/livelock suphesi: sadece {confirmations} onay 400 karede"


def test_regression_no_starvation_jittery_stationary_settles_unchanged() -> None:
    """Duragan ama surekli hafif gurultulu kaynak -- sonsuza dek 'degisti'
    demeyi surdurmemeli (asiri hassasiyet/acilk hatasi)."""
    detector = ChangeDetector()
    rect = Rect(0, 0, 600, 200)
    base = _noise_canvas(_CANVAS_SHAPE, seed=99)
    base_img: ImageArray = np.stack([base, base, base], axis=-1).astype(np.uint8)
    assert detector.has_changed(_frame(base_img, rect)) is True

    confirmations = 0
    for i in range(60):
        rng = np.random.default_rng(seed=5000 + i)
        noise = rng.integers(-2, 3, size=base.shape)
        jittered = np.clip(base.astype(np.int64) + noise, 0, 255).astype(np.uint8)
        jittered_img: ImageArray = np.stack([jittered, jittered, jittered], axis=-1).astype(np.uint8)
        if detector.has_changed(_frame(jittered_img, rect)):
            confirmations += 1
    assert confirmations == 0, f"gurultuye karsi yanlis pozitif: {confirmations} onay"


# --- esigin iki tarafi: dogrudan izgara insasiyla (rastgele/tahmini DEGIL) ---

_GRID_H = 8
_GRID_W = 9  # hash_size + 1, varsayilan
RECT_GRID = Rect(x=0, y=0, w=_GRID_W, h=_GRID_H)


def _baseline_grid() -> list[list[int]]:
    return [[10, 20, 30, 40, 50, 60, 70, 80, 90] for _ in range(_GRID_H)]


def _flipped_grid(k: int) -> list[list[int]]:
    """Baseline'a gore TAM `k` bit farkli bir izgara insa eder.

    Her satirin 0. sutunu yalnizca o satirin ILK karsilastirmasinda
    (sutun 0 vs 1) kullanilir -- komsu karsilastirmaya (sutun 1 vs 2) sizmaz
    (sutun 1 degismiyor). Bu yuzden `r < k` icin sutun 0'i degistirmek,
    digerlerine dokunmadan TAM olarak `k` bit flip eder."""
    rows = _baseline_grid()
    for r in range(k):
        rows[r][0] = 25  # onceden 10 (< col1=20) -> simdi 25 (>= 20): bit 1 -> 0
    return rows


def _grid_image(rows: Sequence[Sequence[int]]) -> ImageArray:
    arr = np.array(rows, dtype=np.uint8)
    img = np.repeat(arr[:, :, None], 3, axis=2)
    return img.astype(np.uint8)


def test_construction_sanity_flipped_grid_hamming_matches_intended_k() -> None:
    """On kosul: `_flipped_grid` gercekten iddia ettigi Hamming mesafesini
    uretiyor mu -- bu, esik testlerinin gecerliligi icin sart."""
    base_hash = cd._dhash(_grid_image(_baseline_grid()), hash_size=8)
    for k in (0, 1, 4, 5, 8):
        target_hash = cd._dhash(_grid_image(_flipped_grid(k)), hash_size=8)
        assert cd._hamming_distance(base_hash, target_hash) == k, (
            f"k={k} icin beklenen Hamming mesafesi uretilmedi"
        )


def test_regression_threshold_exact_value_is_not_changed_constructed() -> None:
    """hamming == threshold(4) -> '<=' kapsayici -> 'degismedi'.
    Rastgele/tahmini icerik degil, dogrudan izgara insasiyla."""
    detector = ChangeDetector(threshold=4)
    assert detector.has_changed(_frame(_grid_image(_baseline_grid()), RECT_GRID)) is True
    at_threshold = _grid_image(_flipped_grid(4))
    assert detector.has_changed(_frame(at_threshold, RECT_GRID)) is False


def test_regression_threshold_plus_one_starts_candidate_then_confirms_constructed() -> None:
    """hamming == threshold+1(5) -> aday baslar, 2. ardisik ayni kare ->
    onay. Dogrudan izgara insasiyla."""
    detector = ChangeDetector(threshold=4)
    assert detector.has_changed(_frame(_grid_image(_baseline_grid()), RECT_GRID)) is True
    beyond = _grid_image(_flipped_grid(5))
    assert detector.has_changed(_frame(beyond, RECT_GRID)) is False  # aday, count=1
    assert detector.has_changed(_frame(beyond, RECT_GRID)) is True   # 2. ardisik -> onay


def test_regression_reverting_to_baseline_cancels_pending_candidate() -> None:
    detector = ChangeDetector(threshold=4)
    assert detector.has_changed(_frame(_grid_image(_baseline_grid()), RECT_GRID)) is True
    beyond = _grid_image(_flipped_grid(5))
    assert detector.has_changed(_frame(beyond, RECT_GRID)) is False  # aday=1
    assert detector.has_changed(_frame(_grid_image(_baseline_grid()), RECT_GRID)) is False  # taban'a donus
    assert detector.has_changed(_frame(beyond, RECT_GRID)) is False  # aday YENIDEN 1'den basliyor
    assert detector.has_changed(_frame(beyond, RECT_GRID)) is True   # 2. ardisik -> onay


def test_regression_region_reset_clears_stable_and_pending_state() -> None:
    detector = ChangeDetector()
    rect_a = Rect(x=10, y=10, w=600, h=200)
    rect_b = Rect(x=99, y=99, w=600, h=200)
    img = _noise_canvas(_CANVAS_SHAPE, seed=11)
    img3: ImageArray = np.stack([img, img, img], axis=-1).astype(np.uint8)

    assert detector.has_changed(_frame(img3, rect_a)) is True
    assert detector.has_changed(_frame(img3, rect_a)) is False  # stabil (A)

    other = _noise_canvas(_CANVAS_SHAPE, seed=12)
    other3: ImageArray = np.stack([other, other, other], axis=-1).astype(np.uint8)
    assert detector.has_changed(_frame(other3, rect_a)) is False  # aday=1 (A)

    # bolge degisir -- eski aday sizmamali, kosulsuz True
    assert detector.has_changed(_frame(img3, rect_b)) is True
    assert detector.has_changed(_frame(img3, rect_b)) is False  # (B) icin stabil


def test_regression_determinism_same_sequence_twice_yields_same_results() -> None:
    frames_spec = [
        (_typing_frame(0), Rect(0, 0, 600, 200)),
        (_typing_frame(150), Rect(0, 0, 600, 200)),
        (_typing_frame(150), Rect(0, 0, 600, 200)),
        (_typing_frame(600), Rect(0, 0, 600, 200)),
        (_typing_frame(600), Rect(0, 0, 600, 200)),
    ]

    def _run() -> list[bool]:
        det = ChangeDetector()
        out = []
        for img, rect in frames_spec:
            out.append(det.has_changed(_frame(img.copy(), rect)))
        return out

    assert _run() == _run()


def test_regression_purity_read_only_image_not_mutated() -> None:
    img = _noise_canvas(_CANVAS_SHAPE, seed=21)
    img3: ImageArray = np.stack([img, img, img], axis=-1).astype(np.uint8)
    img3.setflags(write=False)
    checksum_before = img3.copy()

    detector = ChangeDetector()
    detector.has_changed(_frame(img3, Rect(0, 0, 600, 200)))  # yazma denerse ValueError firlar
    detector.has_changed(_frame(img3, Rect(0, 0, 600, 200)))

    assert np.array_equal(img3, checksum_before)


def test_regression_return_type_is_plain_bool_across_scenarios() -> None:
    detector = ChangeDetector()
    r1 = detector.has_changed(_frame(_typing_frame(0), Rect(0, 0, 600, 200)))
    r2 = detector.has_changed(_frame(_typing_frame(300), Rect(0, 0, 600, 200)))
    for r in (r1, r2):
        assert type(r) is bool
        assert not isinstance(r, np.bool_)


# --- butce: bagimsiz olcum + mekanizmanin gercekligi ---

def test_regression_budget_independent_measurement_600x200() -> None:
    detector = ChangeDetector()
    rect = Rect(0, 0, 600, 200)
    frames = [_frame(_typing_frame(i * 20), rect) for i in range(31)]
    detector.has_changed(frames[0])  # isinma

    times_ms = []
    for f in frames[1:]:
        t0 = time.perf_counter()
        detector.has_changed(f)
        times_ms.append((time.perf_counter() - t0) * 1000.0)

    times_ms.sort()
    print(f"\n[r2-budget] n={len(times_ms)} min={times_ms[0]:.4f}ms "
          f"max={times_ms[-1]:.4f}ms mean={sum(times_ms)/len(times_ms):.4f}ms")
    assert times_ms[-1] <= 5.0, f"butce asildi: {times_ms[-1]:.4f}ms"


def test_regression_budget_assertion_mechanism_is_real() -> None:
    """Butce olcumune uygulanan assert, imkansiz bir esikle (0.0 ms) GERCEKTEN
    kirilir mi -- dekoratif print degil, gercek assert oldugunu kanitlar."""
    detector = ChangeDetector()
    rect = Rect(0, 0, 600, 200)
    detector.has_changed(_frame(_typing_frame(0), rect))
    t0 = time.perf_counter()
    detector.has_changed(_frame(_typing_frame(300), rect))
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    with pytest.raises(AssertionError):
        assert elapsed_ms <= 0.0, "beklenen: bu satir HER ZAMAN AssertionError firlatir"


# ===========================================================================
# GOREV 3a -- dar bolge sinirini netlestir (yatay-desenli/metin-benzeri)
# ===========================================================================

def _monotonic_columns(h: int, w: int, ascending: bool) -> ImageArray:
    """Her sutun kendi icinde sabit, sutunlar arasi MONOTONIK artan/azalan
    deger -- dHash'in yatay komsu-fark karsilastirmasi icin EN KOTU/EN IYI
    durum (ilgili tum bitleri ayni yonde 'tetikler'). Gercek metnin ureteceginden
    DAHA GUCLU bir sinyal -- boylece 'algilanamiyor' sonucu sansa degil
    yapisal bir sinira baglanir."""
    if w == 1:
        col_vals = np.array([128], dtype=np.uint8)
    else:
        vals = np.linspace(0, 255, num=w)
        if not ascending:
            vals = vals[::-1]
        col_vals = vals.astype(np.uint8)
    row = np.tile(col_vals, (h, 1))
    return np.stack([row, row, row], axis=-1).astype(np.uint8)


def test_narrow_region_width_one_never_detects_change_regardless_of_content_or_height() -> None:
    """w=1: dHash yalnizca YATAY komsu farkina bakar; tek sutunda karsilastirilacak
    2. sutun yok -> 0 bitlik hash -> HANGI icerik/yukseklik olursa olsun
    `has_changed` ilk kareden sonra HEP False doner."""
    for h in (1, 2, 5, 20, 100):
        detector = ChangeDetector()
        rect = Rect(x=0, y=0, w=1, h=h)
        asc = _monotonic_columns(h, 1, ascending=True)
        desc = _monotonic_columns(h, 1, ascending=False)
        assert detector.has_changed(_frame(asc, rect)) is True  # ilk kare
        for _ in range(5):
            # en zit icerikle bile -- asla algilanmiyor
            assert detector.has_changed(_frame(desc, rect)) is False


def test_narrow_region_bit_budget_matches_structural_formula() -> None:
    """`_dhash` cikisinin bit uzunlugu (Hamming mesafesinin ULASABILECEGI
    tavan), her (h, w) icin eff_out_h * (eff_out_w - 1) formulune uyuyor mu
    -- BAGIMSIZ olarak (implementer'in docstring iddiasina guvenmeden)
    dogrudan olculur (asc/desc en-uzak-cift ile)."""
    hash_size = 8
    mismatches = []
    for h in (1, 2, 3, 4, 5, 8, 9, 20):
        for w in (1, 2, 3, 4, 5, 8, 9, 20, 40):
            eff_out_h = min(hash_size, h)
            eff_out_w = min(hash_size + 1, w)
            expected_bits = eff_out_h * max(0, eff_out_w - 1)

            asc = _monotonic_columns(h, w, ascending=True)
            desc = _monotonic_columns(h, w, ascending=False)
            ha = cd._dhash(asc, hash_size=hash_size)
            hb = cd._dhash(desc, hash_size=hash_size)
            observed_max_distance = cd._hamming_distance(ha, hb)

            # en-zit icerik TUM mumkun bitleri ceviriyor olmali (ust sinira ulasir)
            if observed_max_distance != expected_bits:
                mismatches.append((h, w, expected_bits, observed_max_distance))

    assert mismatches == [], f"bit butcesi formulu tutmadi: {mismatches[:10]}"


def test_narrow_region_default_threshold_detection_boundary_by_width_and_height() -> None:
    """Varsayilan threshold=4 ile: en-kotu-durum (asc/desc) mesafe > 4
    OLMADIKCA `has_changed` o boyutta ASLA True doneemez (kac aday kare
    verilirse verilsin). Bu testte, kucuk h/w kombinasyonlarinda bu yapisal
    sinirin GERCEKTEN de algilamayi engelledigini (butun icerik en-kotu-durum
    olsa BILE) dogruluyoruz -- yani 'algilama kayboluyor' sadece w=1'e ozgu
    degil, dusuk h ile birlesince daha genis bir bantta da olusuyor."""
    hash_size, threshold = 8, 4
    results = {}
    for h in (1, 2, 3, 4, 5, 8, 20):
        for w in (1, 2, 3, 4, 5, 8, 9, 20, 40):
            eff_out_h = min(hash_size, h)
            eff_out_w = min(hash_size + 1, w)
            max_possible_distance = eff_out_h * max(0, eff_out_w - 1)

            detector = ChangeDetector(hash_size=hash_size, threshold=threshold, stable_frames=1)
            rect = Rect(x=0, y=0, w=w, h=h)
            asc = _monotonic_columns(h, w, ascending=True)
            desc = _monotonic_columns(h, w, ascending=False)
            detector.has_changed(_frame(asc, rect))  # ilk kare, taban
            detected = detector.has_changed(_frame(desc, rect))  # stable_frames=1 -> aninda karar

            structurally_possible = max_possible_distance > threshold
            results[(h, w)] = (detected, structurally_possible)
            # yapisal olarak imkansizsa detected KESINLIKLE False olmali;
            # yapisal olarak mumkunse (en kotu durum uretildigi icin) detected True olmali
            assert detected == structurally_possible, (
                f"h={h} w={w}: detected={detected} ama yapisal_mumkun={structurally_possible} "
                f"(max_dist={max_possible_distance}, threshold={threshold})"
            )

    # w=1 HER h icin yapisal olarak imkansiz olmali (kayitlarin ozeti)
    for h in (1, 2, 3, 4, 5, 8, 20):
        assert results[(h, 1)] == (False, False)


def test_narrow_region_realistic_text_like_stripe_pattern_h20_width_sweep() -> None:
    """Somut, 'metin benzeri' (yuksek yatay frekansli, alternatif siyah/beyaz
    1px seritler) bir desenle, gercekci bir satir yuksekliginde (h=20)
    genislik 2..40 arasinda TARAMA -- hangi genislikten itibaren algilama
    kayboluyor?"""
    h = 20
    detected_widths = []
    not_detected_widths = []
    for w in range(2, 41):
        cols = np.zeros(w, dtype=np.uint8)
        cols[::2] = 235  # alternatif siyah/beyaz 1px serit -- metin-kenarina benzer yuksek frekans
        row = np.tile(cols, (h, 1))
        stripe_a: ImageArray = np.stack([row, row, row], axis=-1).astype(np.uint8)
        cols_b = 235 - cols  # fazi ters cevrilmis (metnin bir "harf" ilerlemesi gibi)
        row_b = np.tile(cols_b, (h, 1))
        stripe_b: ImageArray = np.stack([row_b, row_b, row_b], axis=-1).astype(np.uint8)

        detector = ChangeDetector()  # varsayilan threshold=4, stable_frames=2
        rect = Rect(x=0, y=0, w=w, h=h)
        detector.has_changed(_frame(stripe_a, rect))
        r1 = detector.has_changed(_frame(stripe_b, rect))
        r2 = detector.has_changed(_frame(stripe_b, rect))
        confirmed = r1 is True or r2 is True
        (detected_widths if confirmed else not_detected_widths).append(w)

    print(f"\n[r2-narrow] h=20 icin ALGILANMAYAN genislikler: {not_detected_widths}")
    print(f"[r2-narrow] h=20 icin ALGILANAN genislik araligi: "
          f"{min(detected_widths) if detected_widths else None}..{max(detected_widths) if detected_widths else None}")
    # w=2 alternatif-serit deseniyle bile en az bazi genislikler algilanmali
    # (asagidaki assert, bu somut desenle GERCEKTE ne oldugunu kayda gecirir --
    # verdict.md'de tam sayilarla raporlanir)
    assert detected_widths, "h=20 satirinda HICBIR genislik algilanmadi -- beklenmedik"


# ===========================================================================
# GOREV 3b -- duz renk gecisi: hicbir boyutta algilanmiyor mu? (dogru belgeli mi?)
# ===========================================================================

def test_solid_color_transition_never_detected_at_normal_region_size() -> None:
    """Duz koyu (20) -> duz parlak (230), 64x50 gibi NORMAL bir bolge
    boyutunda bile algilanmiyor -- stable_frames=1 ile debounce'u devre disi
    birakip SADECE hash'in kendisini sinariz."""
    h, w = 64, 50
    dark = np.full((h, w, 3), 20, dtype=np.uint8)
    bright = np.full((h, w, 3), 230, dtype=np.uint8)

    detector = ChangeDetector(stable_frames=1)
    rect = Rect(x=0, y=0, w=w, h=h)
    assert detector.has_changed(_frame(dark, rect)) is True  # ilk kare
    assert detector.has_changed(_frame(bright, rect)) is False  # tam ters renk -- ALGILANAMADI
    assert detector.has_changed(_frame(dark, rect)) is False    # geri donus de algilanamiyor


def test_solid_color_transition_also_invisible_at_large_realistic_region() -> None:
    h, w = 200, 600
    dark = np.full((h, w, 3), 20, dtype=np.uint8)
    bright = np.full((h, w, 3), 230, dtype=np.uint8)
    detector = ChangeDetector(stable_frames=1)
    rect = Rect(x=0, y=0, w=w, h=h)
    assert detector.has_changed(_frame(dark, rect)) is True
    assert detector.has_changed(_frame(bright, rect)) is False


def test_solid_color_blind_spot_is_documented_accurately_in_module_docstring() -> None:
    """Bloke edici kontrol: bu kor nokta docstring'de ACIKCA ve DOGRU
    belgelenmis mi? Belgelenmemis veya yanlis/eksikse bu test KIRILMALI."""
    doc = cd.__doc__ or ""
    lowered = doc.lower()
    # "duz renk" / "solid" gecisinin gorunmez kaldigina dair acik bir ifade var mi
    assert "duz renk" in lowered or "duz renkli" in lowered, (
        "modul docstring'inde duz-renk kor noktasina dair acik bir ifade bulunamadi"
    )
    assert "gorunmez" in lowered or "goruntude her komsu fark esittir" in lowered, (
        "docstring, duz-renk gecisinin ALGILANAMADIGINI acikca belirtmiyor"
    )
    # yanlis yonlendirme kontrolu: docstring bunun SADECE kucuk bolgelere
    # ozgu oldugunu ima etmemeli -- yukaridaki test (buyuk 200x600 bolgede de
    # gorunmez) bunun HER boyutta gecerli oldugunu kanitliyor; docstring'in
    # "her boyutta" / "her hangi" turden bir kisitlama YAPMADIGINI (yani
    # yalnizca kucuk bolgelere atfetmedigini) metinde ariyoruz
    small_region_only_claim = (
        "yalnizca kucuk bolge" in lowered and "duz renk" in lowered
    )
    assert not small_region_only_claim, (
        "docstring duz-renk korlugunu YANLIS sekilde yalnizca kucuk bolgelere "
        "ozguymus gibi sunuyor olabilir -- ama bu HER boyutta gecerli (bkz. "
        "test_solid_color_transition_also_invisible_at_large_realistic_region)"
    )
