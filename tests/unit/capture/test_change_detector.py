"""T-002 -- ChangeDetector: algisal hash + kararlilik (debounce).

TUR 2 notu: bu dosyaya, tester'in tur 1 RET gerekcesi (feedback.md --
`_block_mean_resize` kucuk bolgelerde `IndexError` / sessiz `NaN`
uretiyordu) icin bir regresyon bloku eklendi (asagida "kucuk bolge / cokme
regresyonu" basligi altinda). Yukarisindaki her sey tur 1'den degismedi.

Tasarim dokumani 2.2 (adim 4-5) ve 5.7'yi dogrular:
  - ilk kare kosulsuz "degisti" sayilir
  - ayni icerik (esik ici hash farki) "degismedi" sayilir
  - bir aday degisiklik ancak `stable_frames` ardisik ayni/yakin hash
    goruldukten sonra "degisti" olarak bildirilir (debounce)
  - bolge (Rect) degisince gecmis hash gecersiz olur, ilk kare yine
    kosulsuz "degisti" sayilir
  - performans butcesi <= 5 ms (paket madde "Performans butcesi")

Test goruntuleri BILEREK duz renk DEGIL: dHash komsu hucre farkina dayanir,
duz bir goruntude her komsu fark esittir (deger ne olursa olsun hash sifir
cikar). Bunun yerine ayirt edici, tohumlu bir "dosemeli" desen kullanilir;
degisik `content_id` degerleri arasindaki Hamming mesafeleri asagidaki
matriks ile onceden dogrulanmistir (bkz. modul ici not).
"""
from __future__ import annotations

import itertools
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pytest

# `tests/unit/capture` altinda conftest.py yok (bu gorevin `owns` kapsaminda
# degil). `python -m pytest` zaten calisma dizinini (depo koku) sys.path'e
# ekliyor; bu blok yalnizca baska bir dizinden kosulma ihtimaline karsi
# guvenlik agidir (bkz. tests/unit/contracts/conftest.py, ayni gerekce).
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.capture.change_detector import ChangeDetector  # noqa: E402
from src.contracts.models import Frame, ImageArray, Rect  # noqa: E402

# ---------------------------------------------------------------------------
# yardimcilar: gercekci olmayan (duz renk) DEGIL, ayirt edici desenli goruntu
# ---------------------------------------------------------------------------

_REGION_SHAPE = (200, 600)  # (h, w) -- paketin onerdigi gercekci bolge boyutu


def _pattern(content_id: int, shape: tuple[int, int] = _REGION_SHAPE) -> ImageArray:
    """`content_id`'ye gore deterministik, kenar/gradyan icreren BGR desen.

    Ayni `content_id` her zaman bit-bit ayni diziyi uretir (numpy Generator
    sabit tohumla deterministiktir). Farkli `content_id` degerleri buyuk
    olasilikla genis bir Hamming mesafesi uretir, ama GARANTI degildir --
    bu yuzden testlerde kullanilan ciftler asagida elle dogrulanmis
    (proto-olcum) degerlerle secilmistir.
    """
    rng = np.random.default_rng(seed=content_id)
    h, w = shape
    block = rng.integers(0, 256, size=(16, 16), dtype=np.uint8)
    tile = np.tile(block, (h // 16 + 1, w // 16 + 1))[:h, :w]
    img: ImageArray = np.stack([tile, tile, tile], axis=-1).astype(np.uint8)
    return img


def _jitter(base: ImageArray, seed: int, magnitude: int = 3) -> ImageArray:
    """`base`'e kucuk, deterministik gurultu ekler (sikistirma artefakti /
    tek piksellik oynama simulasyonu). Perceptual hash bunu tolere etmeli."""
    rng = np.random.default_rng(seed=seed)
    noise = rng.integers(-magnitude, magnitude + 1, size=base.shape)
    out = np.clip(base.astype(np.int64) + noise, 0, 255).astype(np.uint8)
    return out


_seq_counter = 0


def _frame(image: ImageArray, rect: Rect) -> Frame:
    global _seq_counter
    _seq_counter += 1
    return Frame(image=image, rect=rect, captured_at=float(_seq_counter), seq=_seq_counter)


RECT_A = Rect(x=100, y=100, w=600, h=200)
RECT_B = Rect(x=300, y=50, w=600, h=200)  # RECT_A'dan farkli -- bolge degisimi

# Asagidaki content_id ciftleri, varsayilan (hash_size=8, threshold=4)
# yapilandirmasiyla proto-olculmus Hamming mesafeleridir (bkz. gorev
# kanit notlari). Boylece testler "buyuk ihtimalle" degil, dogrulanmis
# degerlerle calisir:
#   hamming(0, 1)  = 59  (cok farkli -- esigin cok uzerinde)
#   hamming(1, 3)  = 4   (esige TAM esit -- '<=' kapsayici davranisi sinar)
#   hamming(2, 4)  = 38, hamming(4, 5) = 36, hamming(5, 6) = 38 (yazi
#       yazilirken surekli degisen ara kareler icin -- hicbiri birbirine
#       veya 0'a esik ici degil)
#   hamming(9, 10) = 2   (kucuk ama sifir olmayan fark -- gurultu benzeri)


# ---------------------------------------------------------------------------
# ilk kare her zaman "degisti" sayilir
# ---------------------------------------------------------------------------

def test_first_frame_is_always_changed() -> None:
    detector = ChangeDetector()
    frame = _frame(_pattern(0), RECT_A)
    assert detector.has_changed(frame) is True


def test_first_frame_changed_regardless_of_content() -> None:
    """Ilk karede karsilastirilacak bir gecmis yok; icerik onemsiz."""
    detector = ChangeDetector()
    frame = _frame(_pattern(7), RECT_A)
    assert detector.has_changed(frame) is True


# ---------------------------------------------------------------------------
# ayni icerik = degisiklik yok
# ---------------------------------------------------------------------------

def test_identical_content_is_not_changed() -> None:
    detector = ChangeDetector()
    base = _pattern(0)
    assert detector.has_changed(_frame(base, RECT_A)) is True
    assert detector.has_changed(_frame(base, RECT_A)) is False
    assert detector.has_changed(_frame(base, RECT_A)) is False


def test_small_hash_difference_within_threshold_is_not_changed() -> None:
    """hamming(1, 3) == 4 == varsayilan esik -> '<=' kapsayici, degisiklik yok."""
    detector = ChangeDetector()  # varsayilan threshold=4
    assert detector.has_changed(_frame(_pattern(1), RECT_A)) is True
    assert detector.has_changed(_frame(_pattern(3), RECT_A)) is False


def test_compression_noise_does_not_trigger_false_positive() -> None:
    """Paket madde 1: piksel-piksel karsilastirma degil, algisal hash --
    sikistirma gurultusu / tek piksellik oynama yanlis pozitif URETMEMELI."""
    detector = ChangeDetector()
    base = _pattern(1)
    assert detector.has_changed(_frame(base, RECT_A)) is True
    for seed in range(50, 55):
        noisy = _jitter(base, seed=seed, magnitude=3)
        assert detector.has_changed(_frame(noisy, RECT_A)) is False


# ---------------------------------------------------------------------------
# kararlilik / debounce -- en kritik davranis
# ---------------------------------------------------------------------------

def test_single_differing_frame_is_not_yet_confirmed() -> None:
    """Tek bir farkli kare KARARLI sayilmaz; 2. ardisik ayni hash gerekir."""
    detector = ChangeDetector()
    assert detector.has_changed(_frame(_pattern(0), RECT_A)) is True
    assert detector.has_changed(_frame(_pattern(1), RECT_A)) is False  # aday, henuz onaylanmadi


def test_change_confirmed_on_second_consecutive_identical_hash() -> None:
    detector = ChangeDetector()
    assert detector.has_changed(_frame(_pattern(0), RECT_A)) is True
    assert detector.has_changed(_frame(_pattern(1), RECT_A)) is False  # aday, count=1
    assert detector.has_changed(_frame(_pattern(1), RECT_A)) is True   # 2. ardisik ayni -> onay
    # onaydan sonraki ayni icerik tekrar "degisti" degildir
    assert detector.has_changed(_frame(_pattern(1), RECT_A)) is False


def test_typing_letter_by_letter_never_confirms_while_still_changing() -> None:
    """Tasarim 2.2/adim 5: metin harf harf yaziliyorsa (her kare farkli),
    yerlesene kadar hicbir ara kare OCR'a girmemeli (hep False)."""
    detector = ChangeDetector()
    assert detector.has_changed(_frame(_pattern(0), RECT_A)) is True  # baslangic karari

    typing_steps = [2, 4, 5]  # her adim bir oncekinden esik disi farkli
    for content_id in typing_steps:
        assert detector.has_changed(_frame(_pattern(content_id), RECT_A)) is False

    # yazma durur, ekran "6" icerigiyle yerlesir
    assert detector.has_changed(_frame(_pattern(6), RECT_A)) is False  # 1. goru
    assert detector.has_changed(_frame(_pattern(6), RECT_A)) is True   # 2. ardisik -> onay


def test_reverting_to_stable_baseline_cancels_pending_candidate() -> None:
    """Tasarimin sessiz kaldigi bir durum: aday degisiklik surerken icerik
    eski kararli hash'e donerse bekleyen aday IPTAL edilir (bkz. teslim
    raporu known_gaps -- bu davranis paket metninde acikca yazmiyor)."""
    detector = ChangeDetector()
    assert detector.has_changed(_frame(_pattern(0), RECT_A)) is True    # kararli=0
    assert detector.has_changed(_frame(_pattern(1), RECT_A)) is False   # aday=1, count=1
    assert detector.has_changed(_frame(_pattern(0), RECT_A)) is False   # taban'a donus -> aday iptal
    # ayni "1" icerigi yeniden gorulse bile sayac 0'dan basliyor (2 degil)
    assert detector.has_changed(_frame(_pattern(1), RECT_A)) is False   # aday=1, count=1 (YENIDEN)
    assert detector.has_changed(_frame(_pattern(1), RECT_A)) is True    # 2. ardisik -> onay


# ---------------------------------------------------------------------------
# esik yapilandirilabilir (paket madde 2)
# ---------------------------------------------------------------------------

def test_threshold_default_tolerates_small_difference() -> None:
    detector = ChangeDetector()  # threshold=4 varsayilan; hamming(9,10)=2
    assert detector.has_changed(_frame(_pattern(9), RECT_A)) is True
    assert detector.has_changed(_frame(_pattern(10), RECT_A)) is False


def test_threshold_zero_requires_exact_hash_match() -> None:
    """threshold=0 ile ayni kucuk fark artik 'degisiklik adayi' sayilir."""
    detector = ChangeDetector(threshold=0)
    assert detector.has_changed(_frame(_pattern(9), RECT_A)) is True
    assert detector.has_changed(_frame(_pattern(10), RECT_A)) is False  # aday, count=1
    assert detector.has_changed(_frame(_pattern(10), RECT_A)) is True   # 2. ardisik -> onay


# ---------------------------------------------------------------------------
# stable_frames yapilandirilabilir
# ---------------------------------------------------------------------------

def test_stable_frames_one_disables_debounce_wait() -> None:
    detector = ChangeDetector(stable_frames=1)
    assert detector.has_changed(_frame(_pattern(0), RECT_A)) is True
    assert detector.has_changed(_frame(_pattern(1), RECT_A)) is True  # tek kare yeterli


def test_stable_frames_three_requires_three_consecutive() -> None:
    detector = ChangeDetector(stable_frames=3)
    assert detector.has_changed(_frame(_pattern(0), RECT_A)) is True
    assert detector.has_changed(_frame(_pattern(1), RECT_A)) is False  # count=1
    assert detector.has_changed(_frame(_pattern(1), RECT_A)) is False  # count=2
    assert detector.has_changed(_frame(_pattern(1), RECT_A)) is True   # count=3 -> onay


# ---------------------------------------------------------------------------
# bolge degisince durum sifirlanir (paket madde 4)
# ---------------------------------------------------------------------------

def test_region_change_forces_changed_even_with_identical_pixels() -> None:
    """Ayni piksel icerigi olsa bile FARKLI Rect -> kosulsuz True."""
    detector = ChangeDetector()
    same_pixels = _pattern(0)
    assert detector.has_changed(_frame(same_pixels, RECT_A)) is True
    assert detector.has_changed(_frame(same_pixels, RECT_A)) is False  # stabil
    assert detector.has_changed(_frame(same_pixels, RECT_B)) is True   # bolge degisti
    assert detector.has_changed(_frame(same_pixels, RECT_B)) is False  # yeni bolgede stabil


def test_region_change_clears_pending_debounce_state() -> None:
    """Bolge degisimi, bekleyen (henuz onaylanmamis) aday sayacini da
    sifirlamali -- eski sayac yeni bolgeye 'tasinmis' gibi davranmamali."""
    detector = ChangeDetector()
    assert detector.has_changed(_frame(_pattern(0), RECT_A)) is True   # kararli=0 (A)
    assert detector.has_changed(_frame(_pattern(1), RECT_A)) is False  # aday=1, count=1 (A)

    # bolge degisir; yeni bolgede icerik tesaduefen eski adayla ayni (1)
    assert detector.has_changed(_frame(_pattern(1), RECT_B)) is True   # kosulsuz ilk kare (B)
    assert detector.has_changed(_frame(_pattern(1), RECT_B)) is False  # (B) icin stabil

    # (B) icinde yeni bir aday baslat -- sayac 2'den degil 1'den baslamali
    assert detector.has_changed(_frame(_pattern(2), RECT_B)) is False  # aday=2, count=1
    assert detector.has_changed(_frame(_pattern(2), RECT_B)) is True   # 2. ardisik -> onay


# ---------------------------------------------------------------------------
# donus tipi: gercek Python bool (numpy.bool_ degil)
# ---------------------------------------------------------------------------

def test_return_type_is_plain_python_bool() -> None:
    detector = ChangeDetector()
    result = detector.has_changed(_frame(_pattern(0), RECT_A))
    assert type(result) is bool


# ---------------------------------------------------------------------------
# yapici parametre denetimi
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "kwargs",
    [
        {"hash_size": 0},
        {"hash_size": -1},
        {"threshold": -1},
        {"stable_frames": 0},
        {"stable_frames": -2},
    ],
)
def test_invalid_constructor_parameters_raise_value_error(kwargs: dict) -> None:
    with pytest.raises(ValueError):
        ChangeDetector(**kwargs)


def test_custom_hash_size_does_not_crash() -> None:
    detector = ChangeDetector(hash_size=4)
    assert detector.has_changed(_frame(_pattern(0), RECT_A)) is True
    assert detector.has_changed(_frame(_pattern(0), RECT_A)) is False


# ---------------------------------------------------------------------------
# performans butcesi: <= 5 ms (paket + tasarim 5.7)
# ---------------------------------------------------------------------------

_BUDGET_MS = 5.0
_BENCHMARK_ITERATIONS = 30


def test_has_changed_stays_within_5ms_budget_for_realistic_region() -> None:
    """600x200 gercekci bolge boyutuyla olcer. Butce asilirsa test KIRILIR
    (paket: 'Bütçe aşımı bir bug'dır, gözlem değil'). Ham zamanlama ciktisi
    `-s` ile kosulup `evidence/budget.txt`'e yazilir."""
    detector = ChangeDetector()
    frames = [_frame(_pattern(i, shape=_REGION_SHAPE), RECT_A) for i in range(_BENCHMARK_ITERATIONS + 1)]

    # isinma turu: ilk cagrinin numpy/OS onbellek maliyetini olcum disi tutar
    detector.has_changed(frames[0])

    times_ms: list[float] = []
    for frame in frames[1:]:
        start = time.perf_counter()
        detector.has_changed(frame)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        times_ms.append(elapsed_ms)

    times_ms.sort()
    mean_ms = sum(times_ms) / len(times_ms)
    print(f"\n[budget] has_changed() 600x200 bolge, n={len(times_ms)} olcum")
    for i, t in enumerate(times_ms):
        print(f"[budget]   call[{i:02d}] = {t:.4f} ms")
    print(
        f"[budget] min={times_ms[0]:.4f}ms max={times_ms[-1]:.4f}ms "
        f"mean={mean_ms:.4f}ms p95={times_ms[int(len(times_ms) * 0.95)]:.4f}ms "
        f"budget={_BUDGET_MS}ms"
    )

    assert times_ms[-1] <= _BUDGET_MS, (
        f"has_changed() butceyi asti: max={times_ms[-1]:.4f}ms > {_BUDGET_MS}ms"
    )


# ---------------------------------------------------------------------------
# saf hash yardimcilarinin dogrudan testi (kucuk, ayirt edici destek testi)
# ---------------------------------------------------------------------------

def test_hamming_distance_helper_counts_differing_bits() -> None:
    from src.capture import change_detector as cd

    assert cd._hamming_distance(0b1010, 0b0110) == 2
    assert cd._hamming_distance(0, 0) == 0
    assert cd._hamming_distance(0b1111, 0b0000) == 4


def test_dhash_helper_is_deterministic_and_distinguishes_content() -> None:
    from src.capture import change_detector as cd

    a1 = cd._dhash(_pattern(0), hash_size=8)
    a2 = cd._dhash(_pattern(0), hash_size=8)
    b = cd._dhash(_pattern(1), hash_size=8)
    assert a1 == a2  # deterministik: ayni girdi -> ayni hash
    assert cd._hamming_distance(a1, b) == 59  # proto-olculmus deger


# ---------------------------------------------------------------------------
# TUR 2 regresyonu -- kucuk bolge / cokme (feedback.md Blokaj 1 ve 2)
#
# Tur 1'de `_block_mean_resize`, hedef izgaradan (varsayilan 8x9) kucuk
# bolgelerde `np.add.reduceat` icin cakisan kova sinirlari uretiyordu:
#   h<5 veya w<5  -> IndexError (cokme)
#   5<=h/w<izgara -> sessiz "divide by zero encountered in divide" + NaN
# Asagidaki testler, tasarim dokumaninin (SS2.2) kullanicinin yakalama
# bolgesini SERBESTCE yeniden boyutlandirabilecegini soyledigi icin bunu
# bir daha sessizce geri gelemeyecek sekilde kilitler: 1x1'den 20x20'ye
# HER boyut + birkac dikdortgen-olmayan oran, uc kosul da denetlenir:
#   (1) cokme yok, (2) numpy uyarisi yok (RuntimeWarning dahil -- `error`
#   filtresiyle sinanir), (3) donen deger gercek Python `bool`.
# ---------------------------------------------------------------------------

def _small_region_sizes() -> list[tuple[int, int]]:
    """1x1 .. 20x20 (tum kare + dikdortgen kombinasyonlari) + birkac
    ekstrem-oranli dikdortgen (feedback.md'nin acikca istedigi orneklerle
    birlikte, her iki yonde de: genislik=1 VE yukseklik=1 uc durumlari)."""
    squares_and_rects = [
        (h, w) for h, w in itertools.product(range(1, 21), range(1, 21))
    ]
    extreme_ratios = [(1, 50), (50, 1), (3, 80), (80, 3)]
    return squares_and_rects + extreme_ratios


@pytest.mark.parametrize("h,w", _small_region_sizes())
def test_small_region_sizes_never_crash_or_warn_and_return_bool(
    h: int, w: int
) -> None:
    """Rejim: her (h, w) icin iki farkli kare besle (baseline + degisiklik
    adayi); ikisinde de cokme/uyari olmamali, ikisi de `bool` donmeli."""
    detector = ChangeDetector()
    rect = Rect(x=0, y=0, w=w, h=h)
    frame_a = _frame(_pattern(0, shape=(h, w)), rect)
    frame_b = _frame(_pattern(1, shape=(h, w)), rect)

    with warnings.catch_warnings():
        warnings.simplefilter("error")  # RuntimeWarning (ör. divide by zero) -> hata
        result_a = detector.has_changed(frame_a)
        result_b = detector.has_changed(frame_b)

    assert type(result_a) is bool
    assert type(result_b) is bool
    assert result_a is True  # ilk kare kosulsuz "degisti"


def test_1x1_region_does_not_crash() -> None:
    """feedback.md'nin birebir tekrar uretim senaryosu -- artik cokmemeli."""
    detector = ChangeDetector()
    img = np.full((1, 1, 3), 128, dtype=np.uint8)
    frame = _frame(img, Rect(x=0, y=0, w=1, h=1))
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = detector.has_changed(frame)
    assert result is True
    assert type(result) is bool


def test_3x3_region_does_not_crash() -> None:
    detector = ChangeDetector()
    img = np.full((3, 3, 3), 200, dtype=np.uint8)
    frame = _frame(img, Rect(x=0, y=0, w=3, h=3))
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = detector.has_changed(frame)
    assert result is True
    assert type(result) is bool


def test_boundary_band_5x5_to_8x8_does_not_silently_produce_nan() -> None:
    """feedback.md Blokaj 2 -- 5x5..8x8 bandinda oncesinde cokmuyordu ama
    sessizce NaN uretiyordu (RuntimeWarning: divide by zero). Simdi hem
    uyari hem NaN olmamali; debounce/esik akisi normal calismaya devam
    etmeli (aday -> 2. ardisik ayni -> onay)."""
    for size in (5, 6, 7, 8):
        detector = ChangeDetector()
        rect = Rect(x=0, y=0, w=size, h=size)
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            r1 = detector.has_changed(_frame(_pattern(0, shape=(size, size)), rect))
            r2 = detector.has_changed(_frame(_pattern(1, shape=(size, size)), rect))
            r3 = detector.has_changed(_frame(_pattern(1, shape=(size, size)), rect))
        assert r1 is True
        for r in (r1, r2, r3):
            assert type(r) is bool
        assert not (r2 is True and r3 is True)  # debounce hala hemen onaylamiyor


def test_large_region_16x16_and_above_is_unaffected_by_small_region_clamp() -> None:
    """Izgaradan (8x9) buyuk/esit bolgelerde kirpma devreye girmemeli --
    tester'in olcumunde "saglam" isaretlenen bant (16x16 ve 600x200)."""
    for h, w in [(16, 16), (600, 200)]:
        detector = ChangeDetector()
        rect = Rect(x=0, y=0, w=w, h=h)
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            r1 = detector.has_changed(_frame(_pattern(0, shape=(h, w)), rect))
            r2 = detector.has_changed(_frame(_pattern(0, shape=(h, w)), rect))
        assert r1 is True
        assert r2 is False  # ayni icerik -> degisiklik yok (regresyon yok)


def test_small_region_hash_helper_never_raises_indexerror_directly() -> None:
    """`_dhash`/`_block_mean_resize` yardimcilarini dogrudan, tum kucuk
    boyut matrisinde sinar (feedback.md'nin kapsam haritasindaki TUM X/N
    hucreleri): saf fonksiyon seviyesinde de cokme/NaN olmamali."""
    from src.capture import change_detector as cd

    bad: list[tuple[int, int, str]] = []
    for h in range(1, 21):
        for w in range(1, 21):
            img = np.random.default_rng(seed=h * 100 + w).integers(
                0, 256, size=(h, w, 3), dtype=np.uint8
            )
            with warnings.catch_warnings():
                warnings.simplefilter("error")
                try:
                    value = cd._dhash(img, hash_size=8)
                except Exception as exc:  # pragma: no cover -- basarisizlikta rapor icin
                    bad.append((h, w, repr(exc)))
                    continue
            assert isinstance(value, int)
    assert bad == [], f"kucuk bolgelerde cokme/uyari: {bad[:10]}"
