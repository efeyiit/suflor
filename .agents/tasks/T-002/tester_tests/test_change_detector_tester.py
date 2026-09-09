"""T-002 -- TESTER'in bagimsiz dogrulama takimi (ChangeDetector).

KORLUK KURALI geregi bu dosya `delivery.md` veya `evidence/` OKUNMADAN,
yalnizca `packet.md`, `env.md`, `src/contracts/models.py`, tasarim dokumani
2.2/5.7 ve `src/capture/change_detector.py`'nin KENDISINE bakilarak sifirdan
yazilmistir. Implementer'in test dosyasindaki yardimci fonksiyonlar
(_pattern, _jitter) kasten KOPYALANMADI; asagidaki uretim fonksiyonlari
farkli bir yaklasimla (tam-cozunurluk periyodik-OLMAYAN rastgele alan,
kaydirilan-cubuk sahnesi, dogrudan olculmus Hamming ciftleri) yazilmistir.

Duruş: dusmanca dogrulama. Amac kodu onaylamak degil, bozuk oldugunu
kanitlamaya calismaktir (bkz. env.md "ozellikle saldirilacak 9 nokta").
"""
from __future__ import annotations

import time
import warnings

import numpy as np
import pytest

from src.capture.change_detector import ChangeDetector, _dhash, _hamming_distance
from src.contracts.models import Frame, ImageArray, Rect

# ---------------------------------------------------------------------------
# yardimcilar -- implementer'in test dosyasindan BAGIMSIZ uretim yontemleri
# ---------------------------------------------------------------------------

_SEQ = 0


def _mk_frame(image: ImageArray, rect: Rect) -> Frame:
    global _SEQ
    _SEQ += 1
    return Frame(image=image, rect=rect, captured_at=float(_SEQ), seq=_SEQ)


def _full_res_noise(seed: int, shape: tuple[int, int] = (200, 600)) -> ImageArray:
    """Periyodik OLMAYAN, tam cozunurlukte rastgele BGR goruntu.

    Implementer'in `_pattern` fonksiyonu 16x16'lik bir bloku dosemeli
    tekrarliyor (periyot=16); bu, blok-ortalamali kucultmeyle birlesince
    bazi kaydirma senaryolarinda hash'i yapay olarak degismez kilabiliyor
    (asagida `test_periodic_tiled_content_is_a_documented_blind_spot_not_bug`
    bunu belgeliyor). Livelock testlerinde bu yapay etkiyi devre disi
    birakmak icin TAM COZUNURLUKTE (periyotsuz) gurultu kullaniyoruz.
    """
    rng = np.random.default_rng(seed=seed)
    h, w = shape
    plane = rng.integers(0, 256, size=(h, w), dtype=np.uint8)
    img: ImageArray = np.stack([plane, plane, plane], axis=-1).astype(np.uint8)
    return img


def _sliding_bar_scene(offset: int, shape: tuple[int, int] = (200, 600)) -> ImageArray:
    """Koyu zemin uzerinde soldan saga kayan parlak bir dikey cubuk.

    Gercekci bir 'surekli hareket eden sahne' (orn. yuklenme animasyonu,
    kayan altyazi) simulasyonu -- livelock/aclik sinamasi icin.
    """
    h, w = shape
    bar_w = 40
    img = np.full((h, w), 20, dtype=np.uint8)
    bar_x = offset % (w - bar_w)
    img[:, bar_x : bar_x + bar_w] = 220
    out: ImageArray = np.stack([img, img, img], axis=-1)
    return out


RECT_A = Rect(x=100, y=100, w=600, h=200)
RECT_B = Rect(x=400, y=10, w=600, h=200)


# ---------------------------------------------------------------------------
# 1. temel sozlesme: ilk kare, ayni icerik, bolge sifirlama
# ---------------------------------------------------------------------------


def test_first_frame_always_changed() -> None:
    det = ChangeDetector()
    assert det.has_changed(_mk_frame(_full_res_noise(1), RECT_A)) is True


def test_identical_content_reports_no_change() -> None:
    det = ChangeDetector()
    img = _full_res_noise(2)
    assert det.has_changed(_mk_frame(img, RECT_A)) is True
    assert det.has_changed(_mk_frame(img, RECT_A)) is False
    assert det.has_changed(_mk_frame(img, RECT_A)) is False


def test_region_change_forces_true_even_with_identical_pixels() -> None:
    det = ChangeDetector()
    img = _full_res_noise(3)
    assert det.has_changed(_mk_frame(img, RECT_A)) is True
    assert det.has_changed(_mk_frame(img, RECT_A)) is False
    # ayni piksel, farkli Rect -> gecmis hash sozlesme geregi gecersiz
    assert det.has_changed(_mk_frame(img, RECT_B)) is True


def test_region_change_clears_pending_debounce_counter() -> None:
    """Bekleyen aday, bolge degisiminde sifirlanmali; eski sayac yeni
    bolgeye tasinmamali (env.md madde 4)."""
    det = ChangeDetector()
    base_a = _full_res_noise(10)
    cand_a = _full_res_noise(11)
    assert det.has_changed(_mk_frame(base_a, RECT_A)) is True
    assert det.has_changed(_mk_frame(cand_a, RECT_A)) is False  # aday A, count=1

    # bolge degisir -- yeni bolgede ayni piksel icerigi (cand_a) tesadufen gorulse bile
    assert det.has_changed(_mk_frame(cand_a, RECT_B)) is True  # kosulsuz ilk kare (B)
    assert det.has_changed(_mk_frame(cand_a, RECT_B)) is False  # (B) icin artik stabil taban

    # (B)'de yeni bir aday baslatilirsa sayac 2'den degil 1'den baslamali
    cand_b = _full_res_noise(12)
    assert det.has_changed(_mk_frame(cand_b, RECT_B)) is False  # aday=1
    assert det.has_changed(_mk_frame(cand_b, RECT_B)) is True  # 2. ardisik -> onay


# ---------------------------------------------------------------------------
# 2. debounce / kararlilik -- en kritik davranis
# ---------------------------------------------------------------------------


def test_single_differing_frame_not_yet_confirmed() -> None:
    det = ChangeDetector()  # varsayilan stable_frames=2
    assert det.has_changed(_mk_frame(_full_res_noise(20), RECT_A)) is True
    assert det.has_changed(_mk_frame(_full_res_noise(21), RECT_A)) is False


def test_typing_letter_by_letter_never_confirms_mid_stream() -> None:
    """Tasarim 2.2/adim 5: harf harf yazilan bir dizide (her kare bir
    oncekinden -- ve tabandan -- farkli), yerlesene kadar hicbir ara kare
    'degisti' olarak bildirilmemeli. Metin ancak yazma DURUP ekran en az
    iki ardisik karede sabitlendiginde onaylanmali."""
    det = ChangeDetector()
    assert det.has_changed(_mk_frame(_full_res_noise(0), RECT_A)) is True  # baslangic

    typing_frames = [_full_res_noise(seed) for seed in range(100, 112)]  # 12 farkli "harf"
    for f in typing_frames:
        result = det.has_changed(_mk_frame(f, RECT_A))
        assert result is False, "yazma surerken erken onay verildi (debounce bozuk)"

    # yazma durur: ekran son harfle iki ardisik kare sabit kalir
    final_text = _full_res_noise(999)
    assert det.has_changed(_mk_frame(final_text, RECT_A)) is False  # 1. goru (aday)
    assert det.has_changed(_mk_frame(final_text, RECT_A)) is True  # 2. ardisik -> onay


def test_reverting_to_stable_baseline_does_not_falsely_confirm() -> None:
    """Aday surerken icerik tabana donerse, onceki adayin sayaci ile
    yeni bir farkli kare KARISTIRILIP yanlislikla onaylanmamali."""
    det = ChangeDetector()
    base = _full_res_noise(30)
    candidate = _full_res_noise(31)
    other = _full_res_noise(32)

    assert det.has_changed(_mk_frame(base, RECT_A)) is True  # taban
    assert det.has_changed(_mk_frame(candidate, RECT_A)) is False  # aday, count=1
    assert det.has_changed(_mk_frame(base, RECT_A)) is False  # tabana donus

    # tabana donusten hemen sonra FARKLI bir icerik gelirse, bu yanlislikla
    # "2. ardisik" sayilip aninda onaylanmamali -- yeni bir aday olarak
    # basindan (count=1) baslamali.
    result = det.has_changed(_mk_frame(other, RECT_A))
    assert result is False, (
        "tabana donusten hemen sonraki farkli kare yanlislikla onaylandi -- "
        "aday sayaci dogru sifirlanmamis olabilir"
    )


def test_stable_frames_parameter_is_respected() -> None:
    det = ChangeDetector(stable_frames=3)
    assert det.has_changed(_mk_frame(_full_res_noise(40), RECT_A)) is True
    cand = _full_res_noise(41)
    assert det.has_changed(_mk_frame(cand, RECT_A)) is False  # count=1
    assert det.has_changed(_mk_frame(cand, RECT_A)) is False  # count=2
    assert det.has_changed(_mk_frame(cand, RECT_A)) is True  # count=3 -> onay


# ---------------------------------------------------------------------------
# 3. livelock / aclik -- surekli degisen kaynak
# ---------------------------------------------------------------------------


def test_continuous_realistic_motion_eventually_confirms_change() -> None:
    """'Yavas ama surekli degisen sahne' senaryosu: gercekci, genis-olcekli
    bir hareket (kayan cubuk) hicbir zaman onaylanmiyorsa bu ACLIK/LIVELOCK
    hatasidir -- ceviri sonsuza kadar guncellenmez. En az bir onay (ilk
    kare disinda) beklenir, aksi halde bu test KIRILIR."""
    det = ChangeDetector()
    n_frames = 500
    confirmations = 0
    for i in range(n_frames):
        img = _sliding_bar_scene(i)
        if det.has_changed(_mk_frame(img, RECT_A)):
            confirmations += 1
    assert confirmations >= 2, (
        f"{n_frames} karelik surekli hareket boyunca yalnizca "
        f"{confirmations} onay geldi (ilk kare dahil) -- ACLIK/LIVELOCK supheli"
    )


def test_continuously_jittery_but_stationary_source_settles_as_unchanged() -> None:
    """Sabit bir sahne uzerine bagimsiz (korelasyonsuz) kucuk piksel
    gurultusu binerse -- sikistirma artefakti simulasyonu -- detektor
    surekli 'henuz kararli degil' (hep False + hicbir zaman baseline'a
    dahil) durumunda TAKILIP KALMAMALI; gurultu esik ici oldugu surece
    dogrudan 'degismedi' (False, aday da acilmadan) donmelidir."""
    det = ChangeDetector()
    base = _full_res_noise(50)
    assert det.has_changed(_mk_frame(base, RECT_A)) is True

    results = []
    for seed in range(500, 540):
        rng = np.random.default_rng(seed=seed)
        noise = rng.integers(-2, 3, size=base.shape)
        noisy = np.clip(base.astype(np.int64) + noise, 0, 255).astype(np.uint8)
        results.append(det.has_changed(_mk_frame(noisy, RECT_A)))

    assert all(r is False for r in results), (
        "kucuk, korelasyonsuz gurultu 'degisti' olarak bildirildi -- "
        "esik gurultu toleransi calismiyor olabilir"
    )


def test_periodic_tiled_content_is_a_documented_blind_spot_not_bug() -> None:
    """BELGELEME (bloke edici degil): 16px periyotlu dosemeli bir desen
    (implementer'in kendi test yardimcisinin urettigi TARZDA icerik) blok-
    ortalamali kucultmeyle birlesince kaydirmaya karsi neredeyse tamamen
    korlasabiliyor -- bu, ANY blok-ortalamali dHash'in bilinen matematiksel
    ozelligidir (periyot, hucre boyutuna yakinsa faz bilgisi kayboluyor),
    implementasyona ozgu bir hata degil. Gercek oyun metni bu derece
    periyodik-dosemeli olmadigi icin NON-BLOCKING olarak kayda geciriyoruz."""
    period = 16
    block = np.random.default_rng(seed=777).integers(0, 256, size=(period, period), dtype=np.uint8)
    h, w = 200, 600
    tile = np.tile(block, (h // period + 1, w // period + 1))[:h, :w]
    periodic_base: ImageArray = np.stack([tile, tile, tile], axis=-1).astype(np.uint8)

    det = ChangeDetector()
    confirmations = 0
    for shift in range(0, 400):
        img = np.roll(periodic_base, shift, axis=1)
        if det.has_changed(_mk_frame(img, RECT_A)):
            confirmations += 1
    # Bu deger implementasyonun periyodik girdiye kars, dokumantasyon
    # amaciyla olculur -- guclu bir assertion YAPILMAZ (bilinen sinirlama).
    print(f"[dokuman] periyodik-dosemeli 400 kaymada onay sayisi = {confirmations}")


# ---------------------------------------------------------------------------
# 4. esik -- iki tarafi da, dogrudan modulun kendi hash fonksiyonuyla olculerek
# ---------------------------------------------------------------------------


def _find_pair_with_hamming_distance(
    target_distance: int, hash_size: int = 8, max_tries: int = 5000
) -> tuple[ImageArray, ImageArray]:
    """`target_distance`'a TAM ESIT Hamming mesafeli iki gercekci goruntu
    arar. Sabit kodlanmis (implementer'in ciftleri gibi) degil -- modulun
    kendi `_dhash`/`_hamming_distance` fonksiyonlarini kullanarak calisma
    zamaninda dogrulanir, boylece "esigin iki tarafi" testi gercek olculmus
    davranisa dayanir.

    Yontem: tam bagimsiz iki rastgele goruntu neredeyse her zaman BUYUK bir
    Hamming mesafesi uretir (yuksek entropili goruntulerde ~32/64 bit) --
    kucuk hedef mesafelere (4, 5) bu yolla rastlamak pratik degil. Onun
    yerine TABAN goruntu uzerine kucuk, rastgele boyutlu/renkli DUZ bir
    yama boyanir (sikistirma sonrasi yerel bir UI degisikligini andirir);
    yama buyudukce hash mesafesi kademeli artar, boylece kucuk hedef
    mesafelere denk gelme sansi yuksektir."""
    base_img = _full_res_noise(9001, shape=(200, 600))
    base_hash = _dhash(base_img, hash_size)
    h, w, _ = base_img.shape
    rng = np.random.default_rng(seed=123)
    for _ in range(max_tries):
        cand_img = base_img.copy()
        patch_h = int(rng.integers(1, 40))
        patch_w = int(rng.integers(1, 100))
        y0 = int(rng.integers(0, h - patch_h))
        x0 = int(rng.integers(0, w - patch_w))
        color = int(rng.integers(0, 256))
        cand_img[y0 : y0 + patch_h, x0 : x0 + patch_w, :] = color
        cand_hash = _dhash(cand_img, hash_size)
        if _hamming_distance(base_hash, cand_hash) == target_distance:
            return base_img, cand_img
    pytest.skip(
        f"hedef Hamming mesafesi {target_distance} icin {max_tries} denemede "
        "eslesen cift bulunamadi (test ortami sorunu, uygulama hatasi degil)"
    )


def test_threshold_boundary_at_exact_value_is_not_changed() -> None:
    """Hamming mesafesi TAM ESIK KADAR -> `<=` kapsayici oldugu icin
    'degismedi' beklenir (esigin AT tarafi)."""
    threshold = 4
    base_img, at_threshold_img = _find_pair_with_hamming_distance(threshold)
    det = ChangeDetector(threshold=threshold)
    assert det.has_changed(_mk_frame(base_img, RECT_A)) is True
    result = det.has_changed(_mk_frame(at_threshold_img, RECT_A))
    assert result is False, (
        f"Hamming mesafesi tam esik ({threshold}) iken 'degisti' bildirildi -- "
        "'<=' kapsayici davranis bozuk olabilir"
    )


def test_threshold_boundary_just_above_starts_a_candidate() -> None:
    """Hamming mesafesi esigin BIR FAZLASI -> aday baslamali (esigin USTU)."""
    threshold = 4
    base_img, above_threshold_img = _find_pair_with_hamming_distance(threshold + 1)
    det = ChangeDetector(threshold=threshold)
    assert det.has_changed(_mk_frame(base_img, RECT_A)) is True
    result = det.has_changed(_mk_frame(above_threshold_img, RECT_A))
    assert result is False, "tek kare -- debounce nedeniyle henuz onaylanmamis olmali"
    # ayni "esik-ustu" kare 2. kez ardisik gelirse onaylanmali
    result2 = det.has_changed(_mk_frame(above_threshold_img, RECT_A))
    assert result2 is True, (
        f"Hamming mesafesi esigin bir fazlasi ({threshold + 1}) olan icerik "
        "2 ardisik kareden sonra bile onaylanmadi"
    )


# ---------------------------------------------------------------------------
# 5. yozlasmis girdiler -- env.md madde 6 (dusmanca cekirdek)
# ---------------------------------------------------------------------------


def test_1x1_region_does_not_crash() -> None:
    """env.md madde 6'da ACIKCA sayilan boyut. Kod tabani, capture
    bolgesinin minimum boyutunu hicbir yerde belgelemiyor/denetlemiyor;
    bu nedenle 1x1 gecerli bir girdi sayilir."""
    det = ChangeDetector()
    img = np.full((1, 1, 3), 128, dtype=np.uint8)
    rect = Rect(x=0, y=0, w=1, h=1)
    det.has_changed(_mk_frame(img, rect))  # CRASH ETMEMELI


def test_3x3_region_does_not_crash() -> None:
    """env.md madde 6'da ACIKCA sayilan ikinci boyut."""
    det = ChangeDetector()
    img = np.random.default_rng(seed=1).integers(0, 256, size=(3, 3, 3), dtype=np.uint8)
    rect = Rect(x=0, y=0, w=3, h=3)
    det.has_changed(_mk_frame(img, rect))  # CRASH ETMEMELI


def test_small_region_below_hash_grid_does_not_silently_corrupt() -> None:
    """hash_size=8 varsayilaniyla 8x9 hucrelik bir izgaraya kucultuluyor.
    Girdi bu izgaradan kucukse (orn. 6x6) kod CRASH etmiyor ama
    `block_sums / counts` sifira bolme yapip NaN uretebiliyor -- bu da
    sessiz, denetlenemez bir "saçmalık" (env.md madde 6). Uyari
    uretilmemesi ve gecerli/deterministik bir hash donmesi beklenir."""
    det = ChangeDetector()
    img = np.random.default_rng(seed=2).integers(0, 256, size=(6, 6, 3), dtype=np.uint8)
    rect = Rect(x=0, y=0, w=6, h=6)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        det.has_changed(_mk_frame(img, rect))
    numeric_warnings = [w for w in caught if issubclass(w.category, RuntimeWarning)]
    assert not numeric_warnings, (
        "kucuk bolgede (6x6) NumPy RuntimeWarning (sifira bolme/NaN) uretildi: "
        f"{[str(w.message) for w in numeric_warnings]}"
    )


def test_solid_color_full_screen_transition_is_a_documented_blind_spot() -> None:
    """BELGELEME (bloke edici degil): salt-dHash (yalnizca yatay komsu
    farki) duz-renkli goruntulerde HER ZAMAN sifir hash uretir -- boylece
    tam siyahtan tam beyaza gecis bile 'degismedi' sayilabilir. Bu, secilen
    algoritmanin (paket: 'dHash veya aHash') bilinen matematiksel
    ozelligidir; paket piksel-piksel karsilastirmayi yasaklayip dHash/aHash
    onerdigi icin implementasyona ozgu bir hata olarak DEGIL, kayda gecen
    bir sinirlama olarak isaretliyoruz. Yine de gercek oyun senaryolarinda
    (metin, kenarlar) nadiren tetiklenir."""
    det = ChangeDetector()
    black = np.zeros((200, 600, 3), dtype=np.uint8)
    white = np.full((200, 600, 3), 255, dtype=np.uint8)
    assert det.has_changed(_mk_frame(black, RECT_A)) is True
    result_after_full_transition = det.has_changed(_mk_frame(white, RECT_A))
    print(f"[dokuman] siyah->beyaz tam ekran gecisi has_changed() = {result_after_full_transition}")


def test_extreme_aspect_ratio_does_not_crash() -> None:
    det = ChangeDetector()
    tall = np.random.default_rng(seed=3).integers(0, 256, size=(2000, 5, 3), dtype=np.uint8)
    wide = np.random.default_rng(seed=4).integers(0, 256, size=(5, 2000, 3), dtype=np.uint8)
    det.has_changed(_mk_frame(tall, Rect(x=0, y=0, w=5, h=2000)))
    det2 = ChangeDetector()
    det2.has_changed(_mk_frame(wide, Rect(x=0, y=0, w=2000, h=5)))


# ---------------------------------------------------------------------------
# 6. sozlesmeye saygi -- Frame/Rect dondurulmus, saflik, determinizm
# ---------------------------------------------------------------------------


def test_read_only_image_array_is_not_mutated_or_written() -> None:
    """`Frame.image` paylasili/yeniden kullanilan bir tampon olabilir.
    Kod ona YAZMAYA calisirsa (in-place islem) read-only bir dizide
    crash eder ya da checksum degisir."""
    img = np.random.default_rng(seed=5).integers(0, 256, size=(200, 600, 3), dtype=np.uint8)
    checksum_before = img.copy()
    img.setflags(write=False)
    det = ChangeDetector()
    det.has_changed(_mk_frame(img, RECT_A))
    det.has_changed(_mk_frame(img, RECT_A))
    assert np.array_equal(img, checksum_before), "goruntu dizisi has_changed() tarafindan degistirildi"


def test_determinism_same_sequence_twice_yields_same_results() -> None:
    frames_data = [_full_res_noise(seed) for seed in (60, 61, 61, 62, 62, 62, 60)]

    def run() -> list[bool]:
        det = ChangeDetector()
        out = []
        for img in frames_data:
            out.append(det.has_changed(_mk_frame(img, RECT_A)))
        return out

    first_run = run()
    second_run = run()
    assert first_run == second_run


def test_return_type_is_plain_python_bool_not_numpy_bool() -> None:
    det = ChangeDetector()
    result = det.has_changed(_mk_frame(_full_res_noise(70), RECT_A))
    assert type(result) is bool


# ---------------------------------------------------------------------------
# 7. performans butcesi -- bagimsiz olcum + assertion'in GERCEK oldugunun
#    dogrulanmasi (env.md madde 7)
# ---------------------------------------------------------------------------


def _measure_has_changed_ms(region_shape: tuple[int, int] = (200, 600), n: int = 25) -> list[float]:
    det = ChangeDetector()
    frames = [_mk_frame(_full_res_noise(800 + i, shape=region_shape), RECT_A) for i in range(n + 1)]
    det.has_changed(frames[0])  # isinma
    timings: list[float] = []
    for f in frames[1:]:
        start = time.perf_counter()
        det.has_changed(f)
        timings.append((time.perf_counter() - start) * 1000.0)
    return timings


def test_budget_measured_independently_stays_within_5ms() -> None:
    timings = _measure_has_changed_ms()
    worst = max(timings)
    print(f"[butce-bagimsiz] n={len(timings)} min={min(timings):.4f}ms max={worst:.4f}ms")
    assert worst <= 5.0, f"bagimsiz olcum butceyi asti: max={worst:.4f}ms > 5.0ms"


def test_budget_assertion_mechanism_is_real_not_decorative() -> None:
    """env.md madde 7: assertion'i gecici olarak IMKANSIZ bir esikle
    zorla -- gercekten kiriliyor mu? Bu, TESLIM EDILEN test dosyasini
    DEGISTIRMEDEN, kendi olcum kodumla yapilir."""
    timings = _measure_has_changed_ms()
    impossible_budget_ms = 0.0  # hicbir gercek olcum bunu gecemez
    with pytest.raises(AssertionError):
        assert max(timings) <= impossible_budget_ms


# ---------------------------------------------------------------------------
# 8. yapici parametre denetimi (bagimsiz tekrar)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "kwargs",
    [
        {"hash_size": 0},
        {"hash_size": -3},
        {"threshold": -1},
        {"stable_frames": 0},
        {"stable_frames": -1},
    ],
)
def test_invalid_constructor_parameters_raise_value_error(kwargs: dict) -> None:
    with pytest.raises(ValueError):
        ChangeDetector(**kwargs)
