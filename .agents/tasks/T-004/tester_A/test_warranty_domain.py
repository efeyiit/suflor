r"""T-004 -- TESTER-A (MERCEK: Garanti alani) -- TUR 2 bagimsiz saldiri paketi.

Implementer'in testinden KOPYALANMAMISTIR (PROTOKOL SS3 gerektirdigi gibi;
`tests/unit/ocr/test_normalizer.py` yalnizca OKUNDU, buradaki testler
BAGIMSIZ yazildi -- farkli fixture'lar, farkli geometri, farkli metinler).
Soru: "Docstring ne soz veriyor ve bu soz, fonksiyonun kabul ettigi HER
girdi icin tutuyor mu?"

## TUR 2 -- bu dosyanin durumu

TUR 1'de bu dosyanin 42 testinden 2'si KALDI (bloke edici bulgu: K10
govde-aciklamasinin "h==0 -> kosul basitce gruplama-yok tarafina duser"
iddiasi `h==0`/negatif `h` icin YANLISTI -- bkz. feedback-A.md Bulgu 1).
Sef K16 karariyla kodu duzeltti (`ref_height<=0` -> KOSULSUZ red). Bu
TUR 2 guncellemesi:

  1. O iki testi SILMEDI -- assertion'lari zaten DOGRU iddiayi (docstring'in
     SOZ VERDIGI davranisi) kontrol ediyordu, TUR 1'de KIRMIZI (kod yanlisti),
     simdi YESIL (kod duzeldi) olmalari BEKLENIYOR. Isimleri/docstring'leri
     TUR 2 baglamini yansitacak sekilde guncellendi (asagida `## 1 -- K16`).
  2. feedback-A.md'nin BIREBIR kurulumunu ayri, sozde-degismez bir testle
     de koruyor (`test_r2_feedback_a_exact_repro...`).
  3. Kendi KAPSAMLI (sabit tohumlu, TAM izgara + rastgele fuzz) orneklemesini
     ekliyor -- tek bir (h, gap) noktasina degil, K16'nin KOSULSUZ iddiasina
     (ref_height<=0 VEYA ref_width<=0 -> gruplama YOK, gap/overlap ONEMSIZ)
     genis bir girdi uzayinda saldiriyor. Sef'in KENDI ilk sondasinin da
     yanlis kuruldugu icin hatayi kacirdigi (`sef_karari-tur2.md`, PROTOKOL
     S3 kapi 6, "yanlis kurulmus bir sonda hatanin yoklugunu kanitlamaz")
     goz onune alinarak, TEK bir el-ile-kurulmus ornege guvenilmiyor.
  4. K17 (ayirac kumesi) ve K18 (NFKC istisnasi) -- TUR 2'nin YENI kod
     yollari -- icin KENDI garanti-alani sinirlarini sinayan yeni bir
     bolum ekliyor (metin ORTASINDA ayirac, birden fazla ayirac, ayiracla
     BASLAYAN blok, NFKC'nin ?/! DISINDA neyi eslemedigi).
  5. K15 (konusmaci matrisi) -- K9'un "iki farkli konusmaci ASLA birlesmez"
     garantisini YENIDEN kuran karar -- Mercek A'nin dogrudan ilgi alani
     (bir docstring garantisi), bu yuzden BAGIMSIZ, coklu-blokli, uctan-uca
     (`normalize()` uzerinden, `_should_group` degil) bir zincirle sinandi.
  6. TUR 1'de "kirilmadi" diye rapor edilen alanlar (K7, K6, K5, saflik)
     AYNEN korunuyor -- regresyon TUR 2'nin birinci onceligi.

Sabit tohum (K13 ruhuyla, rastgele/kapsamli ornekleme icin): SEED = 20260909.
TUR 1'deki fuzz testinde preset'e ozgu tohum ofseti `hash(preset.value)`
ile turetiliyordu -- bu, CPython'da str hash randomizasyonuna
(`PYTHONHASHSEED`) BAGLI oldugu icin SURECLER ARASI reproduzibl DEGILDI
(ayni surec icinde sabitti, ama farkli bir calistirmada -- farkli bir
`PYTHONHASHSEED` ile -- FARKLI bir tohum uretebilirdi; bu modulun kendisinin
determinizm ihlali DEGIL, bu TEST DOSYASININ kendi kusuruydu). TUR 2'de bu
duzeltildi: ofset artik `sum(ord(c) for c in preset.value)` ile SABIT
(PYTHONHASHSEED'den TAMAMEN bagimsiz).
"""
from __future__ import annotations

import copy
import math
import random

import pytest

from src.contracts.models import OcrPreset, Rect, Segment, TextBlock
from src.ocr.normalizer import _Item, _should_group, normalize
from src.ocr.presets import SPEAKER_LABEL_SEPARATORS, get_params

SEED = 20260909


def blk(text: str, *, x: int = 0, y: int = 0, w: int = 200, h: int = 20, conf: float = 0.9) -> TextBlock:
    return TextBlock(text=text, bbox=Rect(x=x, y=y, w=w, h=h), confidence=conf)


# =============================================================================
# 1 -- K16 (tur 2): yozlasmis yukseklik/genislikte gruplama KOSULSUZ yok.
#      GOREV MADDESI 1: "Tur 1 kusuru gercekten gitti mi?"
# =============================================================================


def test_r2_feedback_a_exact_repro_zero_height_now_rejects_grouping() -> None:
    """feedback-A.md Bulgu 1'in HARFI HARFINE kurulumu (x=0,y=0,w=100,h=0
    iki blok icin de) -- TUR 1'de bu 1 Segment'e birlesiyordu (docstring'in
    "gruplama yok" vaadine RAGMEN). TUR 2 (K16) ile ARTIK 2 Segment --
    vaat artik bu girdi icin de tutuyor."""
    a = TextBlock(text="Merhaba", bbox=Rect(x=0, y=0, w=100, h=0), confidence=0.9)
    b = TextBlock(text="dunya", bbox=Rect(x=0, y=0, w=100, h=0), confidence=0.9)
    out = normalize([a, b], OcrPreset.DIALOGUE)
    assert len(out) == 2
    assert [s.text for s in out] == ["Merhaba", "dunya"]


def test_k16_fix_verified_zero_height_touching_blocks_no_longer_group() -> None:
    """TUR 1'de bu test (o zamanki adiyla
    `..._DOES_group_contradicting_docstring`) BILEREK docstring'in
    iddiasini assert ediyordu ve KIRMIZI (basarisiz) geciyordu -- kod
    docstring'i ihlal ediyordu. TUR 2'de assertion AYNI (docstring hala
    ayni seyi vaat ediyor -- K16 sonrasi hala "gruplama yok"), ama
    kod duzeldigi icin ARTIK YESIL. Bu FONKSIYONUN kendisi degisti
    (isim + aciklama), DAVRANIS BEKLENTISI degismedi -- bu TAM OLARAK
    "duzeltilmis davranisi dogrulayacak sekilde guncelle" talebinin
    karsiligi."""
    a = TextBlock(text="Merhaba", bbox=Rect(x=0, y=0, w=100, h=0), confidence=0.9)
    b = TextBlock(text="dunya", bbox=Rect(x=0, y=0, w=100, h=0), confidence=0.9)
    out = normalize([a, b], OcrPreset.DIALOGUE)
    assert len(out) == 2, (
        "K16 (tur 2): ref_height<=0 iken gruplama KOSULSUZ reddedilmeliydi; "
        f"gercek sonuc {len(out)} segment (1 ise hala TUR 1'in kusuru var demektir)."
    )


def test_k16_fix_verified_negative_height_touching_blocks_no_longer_group() -> None:
    """Ayni kok neden, negatif yukseklik icin de (TUR 1'de
    `..._also_groups_same_root_cause` idi -- kaldi; TUR 2'de gecmeli)."""
    item_low = TextBlock(text="AAA", bbox=Rect(x=0, y=-15, w=100, h=20), confidence=0.9)
    item_deg = TextBlock(text="BBB", bbox=Rect(x=0, y=0, w=100, h=-10), confidence=0.9)
    out = normalize([item_low, item_deg], OcrPreset.DIALOGUE)
    assert len(out) == 2, (
        f"negatif h + gap<=0 -> K16'ya gore 'gruplama yok' beklenir, gercek {len(out)} segment dondu"
    )


def test_bbox_zero_width_never_groups_matches_docstring() -> None:
    """K16 oncesinde de dogru olan yari (w==0): sifir genislikli bir
    kutunun bir baskasiyla pozitif yatay ortusmesi geometrik olarak
    imkansizdir -- bu hala tutuyor mu (regresyon)?"""
    a = TextBlock(text="AAA", bbox=Rect(x=0, y=0, w=0, h=20), confidence=0.9)
    b = TextBlock(text="BBB", bbox=Rect(x=0, y=15, w=100, h=20), confidence=0.9)
    out = normalize([a, b], OcrPreset.DIALOGUE)
    assert len(out) == 2


# -- Kapsamli izgara: TEK bir (h, gap) noktasina degil, K16'nin
# KOSULSUZ iddiasina (ref_height<=0 -> HER gap degeri icin red) genis bir
# uzayda saldir. Sef'in "yanlis kurulmus sonda hatanin yoklugunu
# kanitlamaz" dersini (sef_karari-tur2.md) ciddiye alarak: 9x9 boyut x 9
# gap = 729 kombinasyon, hepsi `_should_group` ile DOGRUDAN sinanir.

_DEGENERATE_GRID: tuple[int, ...] = (-1000, -100, -10, -1, 0, 1, 10, 100, 1000)
_GAP_GRID: tuple[int, ...] = (-500, -50, -10, -1, 0, 1, 10, 50, 500)


def test_k16_exhaustive_height_grid_ref_height_le_0_never_groups() -> None:
    """K16'nin KOSULSUZ iddiasi: `ref_height = min(a.h, b.h) <= 0` olan
    HER (h_a, h_b, gap) uclusunde gruplama REDDEDILMELI -- `gap`'in
    degeri (negatif/sifir/pozitif, kucuk/buyuk) ONEMSIZ olmali. Genislik
    sabit ve tam ortusmeli tutulur ki SADECE yukseklik dali sinansin."""
    params = get_params(OcrPreset.DIALOGUE)
    violations: list[tuple[int, int, int, object]] = []
    for h_a in _DEGENERATE_GRID:
        for h_b in _DEGENERATE_GRID:
            if min(h_a, h_b) > 0:
                continue  # bu testin konusu degil (pozitif tarafta K11'in normal esigi gecerli)
            for gap in _GAP_GRID:
                a = _Item(text="a", bbox=Rect(x=0, y=0, w=100, h=h_a), speaker=None, source_blocks=(0,))
                b = _Item(text="b", bbox=Rect(x=0, y=h_a + gap, w=100, h=h_b), speaker=None, source_blocks=(1,))
                result = _should_group(a, b, params)
                if result is not False:
                    violations.append((h_a, h_b, gap, result))
    assert not violations, (
        f"K16 ihlali -- ref_height<=0 iken gruplama REDDEDILMEDI (ilk 10 ornek): "
        f"{violations[:10]!r} (toplam {len(violations)} ihlal / kombinasyon taranan alan icinde)"
    )


def test_k16_exhaustive_width_grid_ref_width_le_0_never_groups() -> None:
    """Ayni izgara, genislik dali icin: `ref_width = min(a.w, b.w) <= 0`
    olan HER (w_a, w_b, x_shift) uclusunde gruplama REDDEDILMELI.
    Yukseklik sabit, dikeyde bitisik (gap=0, esik icinde) tutulur ki
    SADECE genislik dali sinansin."""
    params = get_params(OcrPreset.DIALOGUE)
    violations: list[tuple[int, int, int, object]] = []
    for w_a in _DEGENERATE_GRID:
        for w_b in _DEGENERATE_GRID:
            if min(w_a, w_b) > 0:
                continue
            for x_shift in _GAP_GRID:
                a = _Item(text="a", bbox=Rect(x=0, y=0, w=w_a, h=20), speaker=None, source_blocks=(0,))
                b = _Item(text="b", bbox=Rect(x=x_shift, y=0, w=w_b, h=20), speaker=None, source_blocks=(1,))
                result = _should_group(a, b, params)
                if result is not False:
                    violations.append((w_a, w_b, x_shift, result))
    assert not violations, (
        f"K16 ihlali -- ref_width<=0 iken gruplama REDDEDILMEDI (ilk 10 ornek): "
        f"{violations[:10]!r} (toplam {len(violations)} ihlal)"
    )


def test_k16_positive_geometry_still_groups_sanity_check() -> None:
    """K16'nin `<= 0` erken-cikisi asiri genisletilip POZITIF gecerli
    geometriyi de bozmus olabilir (asiri-duzeltme riski) -- bunu da
    kontrol et: h=20 (pozitif), gap=5 (dialogue esigi 0.8*20=16 icinde)
    -> gruplanmali."""
    params = get_params(OcrPreset.DIALOGUE)
    a = _Item(text="a", bbox=Rect(x=0, y=0, w=100, h=20), speaker=None, source_blocks=(0,))
    b = _Item(text="b", bbox=Rect(x=0, y=25, w=100, h=20), speaker=None, source_blocks=(1,))
    assert _should_group(a, b, params) is True, (
        "K16 duzeltmesi pozitif/gecerli geometriyi de yanlislikla reddetmemeli (asiri-duzeltme kontrolu)"
    )


@pytest.mark.parametrize(
    "preset", [OcrPreset.DIALOGUE, OcrPreset.MENU, OcrPreset.TOOLTIP, OcrPreset.SUBTITLE]
)
def test_k16_fuzz_seeded_degenerate_geometry_never_groups_and_never_crashes(preset: OcrPreset) -> None:
    """SABIT TOHUM rastgele fuzz: 4 on ayarin HER BIRINDE, agirlikli
    olarak yozlasmis (h/w sifir veya negatif) bbox'li 200 komsu-cift
    uzerinde -- cokme YOK ve `ref_height<=0 veya ref_width<=0` olan HER
    ciftte gruplama YOK (dogrudan `_should_group` ile, geometri disinda
    baska hicbir sey -- konusmaci, max_group_chars -- karismasin diye
    ikisi de sabit/uyumlu tutulur)."""
    offset = sum(ord(c) for c in preset.value)  # PYTHONHASHSEED'den BAGIMSIZ
    rng = random.Random(SEED + offset)
    params = get_params(preset)
    dims = [-500, -100, -10, -1, 0, 1, 10, 100, 500]
    for _ in range(200):
        h_a, h_b = rng.choice(dims), rng.choice(dims)
        w_a, w_b = rng.choice(dims), rng.choice(dims)
        gap = rng.randint(-200, 200)
        x_shift = rng.randint(-200, 200)
        a = _Item(text="a", bbox=Rect(x=0, y=0, w=w_a, h=h_a), speaker=None, source_blocks=(0,))
        b = _Item(text="b", bbox=Rect(x=x_shift, y=h_a + gap, w=w_b, h=h_b), speaker=None, source_blocks=(1,))
        result = _should_group(a, b, params)  # cokmemeli
        if min(h_a, h_b) <= 0 or min(w_a, w_b) <= 0:
            assert result is False, (
                f"{preset}: h=({h_a},{h_b}) w=({w_a},{w_b}) gap={gap} x_shift={x_shift} -> "
                f"K16 ihlali, gruplama reddedilmedi"
            )


# =============================================================================
# 2 -- Regresyon (GOREV MADDESI 2, birinci oncelik): TUR 1'de ayakta kalan
#      her sey hala ayakta mi -- K7, K6, K5, saflik/determinizm.
# =============================================================================

# --- K7 -- confidence -------------------------------------------------------


def test_k7_exact_threshold_survives_all_four_presets() -> None:
    thresholds = {
        OcrPreset.DIALOGUE: 0.60,
        OcrPreset.MENU: 0.55,
        OcrPreset.TOOLTIP: 0.65,
        OcrPreset.SUBTITLE: 0.55,
    }
    for preset, th in thresholds.items():
        out = normalize([blk("tam esikte metin", conf=th)], preset)
        assert len(out) == 1, f"{preset}: esige esit confidence dusurulmemeliydi (K7)"


def test_k7_just_below_threshold_drops() -> None:
    out = normalize([blk("dusecek", conf=0.6 - 1e-9)], OcrPreset.DIALOGUE)
    assert out == []


@pytest.mark.parametrize(
    "bad_conf",
    [float("nan"), float("inf"), float("-inf"), -0.5, 1.5, -1e-9, 1.0 + 1e-9],
    ids=["nan", "inf", "-inf", "-0.5", "1.5", "just-below-0", "just-above-1"],
)
def test_k7_out_of_domain_confidence_raises_valueerror(bad_conf: float) -> None:
    with pytest.raises(ValueError):
        normalize([blk("x", conf=bad_conf)], OcrPreset.DIALOGUE)


def test_k7_nan_does_not_silently_survive_as_kept_block() -> None:
    with pytest.raises(ValueError):
        normalize([blk("gizli-nan", conf=float("nan")), blk("saglam", conf=0.9, y=30)], OcrPreset.DIALOGUE)


def test_k7_first_bad_confidence_in_original_order_reported() -> None:
    blocks = [
        blk("saglam-once", conf=0.9, y=100),
        blk("bozuk", conf=1.7, y=0),
    ]
    with pytest.raises(ValueError, match=r"\[1\]"):
        normalize(blocks, OcrPreset.DIALOGUE)


# --- K6 -- yer tutucu semantigi ---------------------------------------------


def test_k6_duplicate_placeholders_kept_in_order_no_dedup() -> None:
    out = normalize([blk("%s ve %s")], OcrPreset.DIALOGUE)
    assert len(out) == 1
    assert out[0].placeholders == ("%s", "%s"), "tekillestirme YAPILMAMALI (K6)"
    assert out[0].text == "%s ve %s", "text birebir korunmali (K6)"


def test_k6_bare_percent_number_not_a_placeholder() -> None:
    out = normalize([blk("Saldiri gucu 50% arttirildi")], OcrPreset.DIALOGUE)
    assert out[0].placeholders == ()
    assert "50%" in out[0].text


def test_k6_percent_letter_pattern_is_a_placeholder() -> None:
    out = normalize([blk("Deger: 50%s tamamlandi")], OcrPreset.DIALOGUE)
    assert out[0].placeholders == ("%s",)


def test_k6_50_percent_vs_50_percent_s_do_not_collide() -> None:
    out_bare = normalize([blk("50%")], OcrPreset.DIALOGUE)
    out_fmt = normalize([blk("50%s")], OcrPreset.DIALOGUE)
    assert out_bare[0].placeholders == ()
    assert out_fmt[0].placeholders == ("%s",)


def test_k6_adjacent_placeholders_both_captured_in_order() -> None:
    out = normalize([blk("{0}{1} arasi")], OcrPreset.DIALOGUE)
    assert out[0].placeholders == ("{0}", "{1}")


def test_k6_nested_braces_only_innermost_matches_documented_limitation() -> None:
    out = normalize([blk("{a{b}c} disinda")], OcrPreset.DIALOGUE)
    assert out[0].placeholders == ("{b}",)


def test_k6_numbers_never_enter_placeholders_various_forms() -> None:
    samples = ["42", "3.14", "%42", "sayilar 1 2 3 burada", "-17", "1000000"]
    for s in samples:
        out = normalize([blk(s)], OcrPreset.DIALOGUE)
        if out:
            assert out[0].placeholders == (), f"sayi/metin {s!r} placeholder uretmemeli"


def test_k6_placeholder_split_across_block_boundary_produces_malformed_token() -> None:
    """Bilgi amacli (bloke edici degil) TUR 1 bulgusu -- davranis TUR
    2'de DEGISTIRILMEDI (sef_karari-tur2.md "bozmadan koru" listesinde
    yok ama "bloke etmeyen gozlemler" bolumunde aynen kalmasi istendi).
    Bu test hala GECMELI (regresyon)."""
    b1 = blk("Deger {0", y=0)
    b2 = blk("} birimdir", y=15)
    out = normalize([b1, b2], OcrPreset.DIALOGUE)
    assert len(out) == 1
    assert out[0].placeholders == ("{0 }",)
    assert out[0].text == "Deger {0 } birimdir"


# --- K5 -- hyphen ------------------------------------------------------------


def test_k5_midword_hyphen_untouched() -> None:
    out = normalize([blk("This is well-known fact")], OcrPreset.DIALOGUE)
    assert out[0].text == "This is well-known fact"


def test_k5_intraline_newline_hyphen_merges() -> None:
    out = normalize([blk("keli-\nme")], OcrPreset.DIALOGUE)
    assert out[0].text == "kelime"


def test_k5_cross_block_hyphen_merges_when_next_lowercase() -> None:
    b1 = blk("tra-", y=0)
    b2 = blk("dition devam ediyor", y=15)
    out = normalize([b1, b2], OcrPreset.DIALOGUE)
    assert len(out) == 1
    assert out[0].text == "tradition devam ediyor"
    assert out[0].source_blocks == (0, 1)


def test_k5_cross_block_hyphen_NOT_dropped_when_next_uppercase() -> None:
    b1 = blk("tra-", y=0)
    b2 = blk("Dition Continues", y=15)
    out = normalize([b1, b2], OcrPreset.DIALOGUE)
    assert len(out) == 1
    assert out[0].text == "tra- Dition Continues", (
        f"buyuk harfle baslayan sonraki satirda tire DUSMEMELIYDI, gercek: {out[0].text!r}"
    )


@pytest.mark.parametrize(
    "dash,name",
    [("‐", "hyphen"), ("–", "en-dash"), ("—", "em-dash"), ("−", "minus-sign")],
)
def test_k5_unicode_dash_variants_not_treated_as_ascii_hyphen(dash: str, name: str) -> None:
    b1 = blk(f"wa{dash}", y=0)
    b2 = blk("iting room", y=15)
    out = normalize([b1, b2], OcrPreset.DIALOGUE)
    assert len(out) == 1
    assert out[0].text != f"wa{dash}iting room".replace(dash, "")
    assert out[0].text == f"wa{dash} iting room", f"{name}: beklenmedik birlesim {out[0].text!r}"


# --- Saflik / determinizm ----------------------------------------------------


def test_purity_repeated_calls_are_value_equal() -> None:
    blocks = [blk("Ayse: Merhaba", y=0), blk("nasilsin?", y=15), blk("{0} gun oldu", y=30)]
    r1 = normalize(blocks, OcrPreset.DIALOGUE)
    r2 = normalize(blocks, OcrPreset.DIALOGUE)
    assert r1 == r2
    assert r1 is not r2, "ayni liste NESNESI donmemeli (yeniden hesaplaniyor olmali)"


def test_purity_mutating_returned_list_does_not_contaminate_next_call() -> None:
    blocks = [blk("A", y=0), blk("B", y=30)]
    r1 = normalize(blocks, OcrPreset.DIALOGUE)
    baseline = copy.deepcopy(r1)
    mutated = normalize(blocks, OcrPreset.DIALOGUE)
    mutated.append(Segment(text="ENJEKTE", bbox=Rect(x=0, y=0, w=1, h=1)))
    fresh = normalize(blocks, OcrPreset.DIALOGUE)
    assert fresh == baseline, "onceki cagridan sizan mutasyon, yeni cagriyi kirletmemeli"


def test_purity_mutating_input_blocks_sequence_object_is_isolated() -> None:
    blocks = [blk("sabit metin", y=0)]
    r1 = normalize(blocks, OcrPreset.DIALOGUE)
    blocks.append(blk("sonradan eklenen", y=50))
    assert len(r1) == 1, "daha once donmus sonuc, girdi listesinin SONRADAN mutasyonundan etkilenmemeli"


def test_purity_no_module_level_cache_across_different_inputs() -> None:
    out_a = normalize([blk("ILK", y=0)], OcrPreset.DIALOGUE)
    out_b = normalize([blk("IKINCI", y=0)], OcrPreset.DIALOGUE)
    assert out_a[0].text == "ILK"
    assert out_b[0].text == "IKINCI"
    out_a_again = normalize([blk("ILK", y=0)], OcrPreset.DIALOGUE)
    assert out_a_again == out_a


def test_finding_leading_trailing_whitespace_silently_stripped_even_without_newline() -> None:
    out = normalize([blk("   Merhaba dunya   ")], OcrPreset.DIALOGUE)
    assert out[0].text == "Merhaba dunya", (
        "MEVCUT (TUR 1'den beri degismeyen) davranis: tek-satirlik bir "
        "blogun bas/son boslugu da sessizce siliniyor. K6'yi ihlal etmez."
    )


# =============================================================================
# 3 -- K15 (tur 2): konusmaci matrisi -- K9'un "iki farkli konusmaci ASLA
#      birlesmez" garantisi, yeni matrisle birlikte hala tutuyor mu?
#      (Mercek A'nin ilgi alani: bu bir DOCSTRING GARANTISI, K16/K17/K18
#      ile ayni turde bir "soz -- her girdi icin tutuyor mu" sorusu.)
# =============================================================================


def _matrix_pair(a_speaker: str | None, b_speaker: str | None) -> tuple[_Item, _Item]:
    a = _Item(text="oge-a", bbox=Rect(x=0, y=0, w=150, h=20), speaker=a_speaker, source_blocks=(10,))
    b = _Item(text="oge-b", bbox=Rect(x=0, y=18, w=150, h=20), speaker=b_speaker, source_blocks=(11,))
    return a, b


@pytest.mark.parametrize(
    "a_sp,b_sp,expected,row",
    [
        ("Kaan", "Kaan", True, "X/X"),
        ("Kaan", None, True, "X/None (devam satiri)"),
        (None, None, True, "None/None"),
        (None, "Zeynep", False, "None/Y (yeni konusmaci basliyor)"),
        ("Kaan", "Zeynep", False, "X/Y (konusmaci siniri)"),
    ],
)
def test_k15_matrix_all_five_rows_independent_geometry(
    a_sp: str | None, b_sp: str | None, expected: bool, row: str
) -> None:
    """K15 tablosunun BES satirinin HER BIRI, resmi test dosyasindan
    FARKLI isim/geometri ile (bagimsizligini korumak icin) dogrudan
    `_should_group` uzerinden sinanir."""
    a, b = _matrix_pair(a_sp, b_sp)
    params = get_params(OcrPreset.DIALOGUE)
    assert _should_group(a, b, params) is expected, f"K15 satiri {row!r} beklenen {expected}"


def test_k15_end_to_end_three_speaker_chain_none_y_transition_never_merges_ascii() -> None:
    """UCTAN UCA (normalize() ile, _should_group DEGIL) coklu-konusmacili
    bir zincir: Ada'nin 2 govde-blogu (X/None devam satiri -- BIRLESMELI)
    ARDINDAN Efe'nin etiketi + govdesi (None/Y gecisi -- ASLA BIRLESMEMELI,
    K15'in DEGISTIRMEDIGI satir). Bu, env.md'nin ozellikle vurguladigi
    'K15'in duzeltmesi None/Y ve X/Y satirlarini gevsetmis olabilir' riskini
    dogrudan bir uretim-benzeri (3+ konusmacili diyalog) senaryosunda sinar."""
    blocks = [
        blk("Ada:", y=0),
        blk("Birinci satir", y=20),
        blk("ikinci satir devam", y=40),  # Ada'nin DEVAM satiri (X/None) -- birlesmeli
        blk("Efe:", y=60),
        blk("Ucuncu konusmaci satiri", y=80),  # YENI konusmaci (None/Y sonra X/Y) -- birlesmemeli
    ]
    out = normalize(blocks, OcrPreset.DIALOGUE)
    assert len(out) == 2, f"Ada'nin devam satiri Efe'nin repligiyle YANLISLIKLA birlesmis olabilir: {out!r}"
    assert out[0].speaker == "Ada"
    assert out[0].text == "Birinci satir ikinci satir devam"
    assert out[0].source_blocks == (0, 1, 2)
    assert out[1].speaker == "Efe"
    assert out[1].text == "Ucuncu konusmaci satiri"
    assert out[1].source_blocks == (3, 4)


def test_k15_end_to_end_three_speaker_chain_japonca_fullwidth_separator() -> None:
    """Ayni senaryo, Japonca VE fullwidth ayirac (K17) ile -- K15'in
    duzeltmesinin dilden BAGIMSIZ oldugunu (env.md: 'Japonca'da BIREBIR
    ayni') VE K17'nin yeni ayiracinin K15 ile DOGRU calistigini birlikte
    dogrular."""
    blocks = [
        blk("勇者：", y=0),
        blk("この町はとても", y=20),
        blk("大きいですね", y=40),
        blk("村人：", y=60),
        blk("そうですね", y=80),
    ]
    out = normalize(blocks, OcrPreset.DIALOGUE)
    assert len(out) == 2
    assert out[0].speaker == "勇者"
    assert out[0].text == "この町はとても 大きいですね"
    assert out[0].source_blocks == (0, 1, 2)
    assert out[1].speaker == "村人"
    assert out[1].text == "そうですね"
    assert out[1].source_blocks == (3, 4)


# =============================================================================
# 4 -- YENI YUZEY: K17 (ayirac kumesi) garanti alani.
#      GOREV MADDESI 3: docstring K17 icin ne iddia ediyor, kabul edilen
#      HER girdi icin tutuyor mu?
# =============================================================================


def test_k17_separator_set_contains_documented_members() -> None:
    """Docstring (presets.py) EN AZ ASCII `:` ve fullwidth `：` iddia
    ediyor -- adlandirilmis sabit gercekten bunlari iceriyor mu?"""
    assert ":" in SPEAKER_LABEL_SEPARATORS
    assert "：" in SPEAKER_LABEL_SEPARATORS  # ：


def test_k17_fullwidth_separator_single_block_extracts_speaker() -> None:
    out = normalize([blk("勇者：こんにちは")], OcrPreset.DIALOGUE)
    assert len(out) == 1
    assert out[0].speaker == "勇者"
    assert out[0].text == "こんにちは"


def test_k17_separator_in_middle_of_text_still_recognized_ascii() -> None:
    """Docstring: ayirac metnin EN SOLUNDAKI konumu -- yalniz metnin
    BASINDAKI bir 'Isim:' kalibi degil, metin ICINDE herhangi bir yerde
    gecen (ilk) ayirac da adaydir (isim kosullarini karsiliyorsa)."""
    out = normalize([blk("Bu bir cumle: devami burada")], OcrPreset.DIALOGUE)
    assert len(out) == 1
    assert out[0].speaker == "Bu bir cumle"
    assert out[0].text == "devami burada"


def test_k17_separator_in_middle_of_text_still_recognized_fullwidth_cjk() -> None:
    """Ayni davranis, TUR 2'nin yeni ayiraciyla VE CJK metinde -- metnin
    ORTASINDA (bloğun ilk karakterinde DEGIL) gecen `：` de yakalanmali."""
    out = normalize([blk("これはテスト：確認")], OcrPreset.DIALOGUE)
    assert len(out) == 1
    assert out[0].speaker == "これはテスト"
    assert out[0].text == "確認"


def test_k17_multiple_separators_leftmost_wins_fullwidth_then_ascii() -> None:
    """Birden fazla ayirac (FARKLI turlerden) ayni metinde -- EN SOLDAKI
    kazanmali, sonraki ayirac(lar) 'rest' icinde DOKUNULMADAN kalmali
    (ikinci bir bolme YAPILMAZ)."""
    out = normalize([blk("Ada：Efe: Selam")], OcrPreset.DIALOGUE)
    assert len(out) == 1
    assert out[0].speaker == "Ada"
    assert out[0].text == "Efe: Selam", "ikinci ayirac (ASCII ':') METIN icinde AYNEN kalmali"


def test_k17_multiple_separators_leftmost_wins_ascii_then_fullwidth() -> None:
    """Ters sira: ASCII ONCE, fullwidth SONRA -- yine EN SOLDAKI (ASCII)
    kazanmali. Bu iki test birlikte 'kume icindeki hicbir uye digerinden
    daha oncelikli DEGIL, yalnizca KONUM onemli' iddiasini kanitlar."""
    out = normalize([blk("Ada:Efe：Selam")], OcrPreset.DIALOGUE)
    assert len(out) == 1
    assert out[0].speaker == "Ada"
    assert out[0].text == "Efe：Selam", "ikinci ayirac (fullwidth '：') METIN icinde AYNEN kalmali"


def test_k17_block_starting_with_ascii_separator_is_not_a_speaker_label() -> None:
    """Ayiracla BASLAYAN blok (':Merhaba', idx==0): docstring/kod
    `idx <= 0` ise reddediyor (bos isim gecersiz) -- bu blok konusmaci
    ETIKETI SAYILMAMALI, metin OLDUGU GIBI kalmali."""
    out = normalize([blk(":Merhaba")], OcrPreset.DIALOGUE)
    assert len(out) == 1
    assert out[0].speaker is None
    assert out[0].text == ":Merhaba"


def test_k17_block_starting_with_fullwidth_separator_is_not_a_speaker_label() -> None:
    """Ayni kural, TUR 2'nin yeni fullwidth ayiraciyla da GECERLI olmali
    -- yeni ayirac eklenirken bos-isim korumasi UNUTULMAMIS mi?"""
    out = normalize([blk("：Merhaba")], OcrPreset.DIALOGUE)
    assert len(out) == 1
    assert out[0].speaker is None
    assert out[0].text == "：Merhaba"


def test_k17_digit_guard_extends_to_fullwidth_separator() -> None:
    """K9'un mevcut korumasi ('12:30' saat metni konusmaci SAYILMAZ,
    isimde rakam OLAMAZ) -- fullwidth ayirac EKLENIRKEN bu koruma
    DARALTILMAMIS mi? '12：30' de ayni sekilde korunmus olmali."""
    out = normalize([blk("12：30")], OcrPreset.DIALOGUE)
    assert len(out) == 1
    assert out[0].speaker is None
    assert out[0].text == "12：30"


def test_k17_max_name_length_guard_extends_to_fullwidth_separator() -> None:
    """`_MAX_SPEAKER_NAME_LEN` (40) siniri -- fullwidth ayiracla da
    GECERLI mi (41 karakter -> REDDEDILMELI, 40 karakter -> KABUL)?"""
    too_long = ("A" * 41) + "：selam"
    exactly_max = ("A" * 40) + "：selam"
    out_long = normalize([blk(too_long)], OcrPreset.DIALOGUE)
    out_max = normalize([blk(exactly_max)], OcrPreset.DIALOGUE)
    assert out_long[0].speaker is None, "41 karakterlik isim REDDEDILMELIYDI"
    assert out_max[0].speaker == "A" * 40, "TAM 40 karakterlik isim KABUL EDILMELIYDI"


def test_k17_label_only_block_with_trailing_whitespace_fullwidth_alone_produces_no_segment() -> None:
    """K9 + K17 birlesimi: fullwidth ayiractan SONRA yalniz bosluk kalan
    bir blok (strip sonrasi BOS) -- TEK BASINA hicbir segment
    URETMEMELI (K9'un 'liste burada biterse etiket dusiyor' kurali,
    yeni ayiracla da AYNI calismali)."""
    out = normalize([blk("勇者：   ")], OcrPreset.DIALOGUE)
    assert out == []


def test_k17_label_only_block_fullwidth_carries_to_next_item() -> None:
    """Ayni durum ama bir SONRAKI blok varsa -- etiket ona TASINMALI
    (K9 + K17)."""
    out = normalize([blk("勇者：   ", y=0), blk("こんにちは", y=22)], OcrPreset.DIALOGUE)
    assert len(out) == 1
    assert out[0].speaker == "勇者"
    assert out[0].text == "こんにちは"
    assert out[0].source_blocks == (0, 1)


# =============================================================================
# 5 -- YENI YUZEY: K18 (NFKC istisnasi) garanti alani.
#      "NFKC'nin ?/! DISINDA neyi eslediginde ne oluyor" -- istisna
#      GENISLEMIYOR mu (docstring'in ACIKCA iddia ettigi sey)?
# =============================================================================


def test_k18_fullwidth_question_and_exclamation_preserved_regression() -> None:
    out = normalize([blk("？", y=0), blk("！", y=30)], OcrPreset.MENU)
    assert [s.text for s in out] == ["？", "！"]


def test_k18_presentation_form_small_question_mark_preserved_by_nfkc_equivalence() -> None:
    """env.md'nin ACIKCA ADINI VERDIGI prob: `﹖` (U+FE56, SMALL QUESTION
    MARK -- dikey/presentation-form varyanti). NFKC bunu `?`'ye acar
    (dogrulandi: `unicodedata.normalize('NFKC','\\ufe56') == '?'`).
    Docstring'in iddiasi 'NFKC DENKLIGI' oldugu (belirli bir liste degil)
    icin bu karakter de OTOMATIK kapsanmali -- kod bir liste kullanmis
    olsaydi bu FARKLI bir karakter oldugu icin (U+FE56 != U+FF1F) kacardi."""
    out = normalize([blk("﹖")], OcrPreset.MENU)  # ﹖
    assert [s.text for s in out] == ["﹖"]


def test_k18_presentation_form_small_exclamation_mark_preserved_by_nfkc_equivalence() -> None:
    """Ayni prob, unlem icin: `﹗` (U+FE57)."""
    out = normalize([blk("﹗")], OcrPreset.MENU)  # ﹗
    assert [s.text for s in out] == ["﹗"]


def test_k18_double_question_mark_NOT_preserved_exception_does_not_widen() -> None:
    """env.md'nin ADINI VERDIGI ikinci prob: `⁇` (U+2047, DOUBLE QUESTION
    MARK). NFKC bunu TEK degil IKI karaktere acar (`'??'`, len=2) --
    docstring'in 'NFKC('?','!')'ye ACILMAYAN baska hicbir karakter
    istisnadan yararlanmaz, istisna GENISLEMEZ' iddiasi bunun icin
    dogru mu? `'??' in ('?','!')` False oldugu icin bu karakter SEMBOL
    sinifinda kalip SILINMELI (tek-karakter gurultu)."""
    out = normalize([blk("⁇")], OcrPreset.MENU)  # ⁇
    assert out == [], "K18 istisnasi cok-karakterli NFKC acilimina GENISLEMEMELI"


def test_k18_question_exclamation_ligature_not_preserved() -> None:
    """`‽`'in kompozisyon-benzeri kuzenleri: U+2048 (QUESTION EXCLAMATION
    MARK) NFKC ile '?!' (len=2) acilir -- ayni gerekceyle SILINMELI."""
    out = normalize([blk("⁈")], OcrPreset.MENU)  # ⁈
    assert out == []


def test_k18_fullwidth_colon_alone_is_still_noise_not_an_accidental_exception() -> None:
    """K17 ayirac kumesine `：` EKLENDI diye, K18'in ?/! istisnasi
    YANLISLIKLA bunu da kapsar hale GELMEMELI -- tek basina `：` hala
    S*/P* sinifinda ve NFKC(`：`) == ':' , bu `('?','!')` icinde DEGIL,
    yani tek-karakter gurultu olarak SILINMELI."""
    out = normalize([blk("：")], OcrPreset.MENU)  # ：
    assert out == [], "fullwidth ayirac, TEK BASINA bir blokken K4/K18 tarafindan noise sayilmali"


def test_k18_ideographic_full_stop_alone_is_noise() -> None:
    """CJK metinde COK yaygin baska bir tek-karakter noktalama (`。`,
    IDEOGRAPHIC FULL STOP) -- istisna kapsaminda DEGIL, silinmeli."""
    out = normalize([blk("。")], OcrPreset.MENU)  # 。
    assert out == []


def test_k18_fullwidth_full_stop_alone_is_noise() -> None:
    out = normalize([blk("．")], OcrPreset.MENU)  # ．
    assert out == []


def test_k18_inverted_question_mark_alone_is_noise() -> None:
    """Ispanyolca `¿` (U+00BF) -- NFKC kendisine acilir (`'¿'`), `?`'ye
    DEGIL (farkli bir karakter, Unicode'un KENDI tanimi geregi denk
    SAYILMIYOR) -- bu yuzden istisna GENISLEMEMELI, silinmeli."""
    out = normalize([blk("¿")], OcrPreset.MENU)  # ¿
    assert out == []


def test_k18_black_question_mark_ornament_emoji_like_symbol_alone_is_noise() -> None:
    """`❓` (U+2753, BLACK QUESTION MARK ORNAMENT -- emoji-benzeri, So
    kategorisi) -- gorunuste 'soru isareti' ama NFKC kendisine acilir,
    ASCII `?`'ye DEGIL -- istisna GENISLEMEMELI."""
    out = normalize([blk("❓")], OcrPreset.MENU)  # ❓
    assert out == []


def test_k18_ascii_question_and_exclamation_baseline_unaffected() -> None:
    """K18 duzeltmesi ASCII orijinal davranisi BOZMAMALI (regresyon)."""
    out = normalize([blk("?", y=0), blk("!", y=30)], OcrPreset.MENU)
    assert [s.text for s in out] == ["?", "!"]


# =============================================================================
# 6 -- Birlesik saflik/determinizm fuzz: TUM tur-2 yuzeyini (K15+K16+K17+
#      K18) BIRLIKTE, sabit tohumla, purity_check.py'den BAGIMSIZ bir
#      yontemle sina -- cokme yok + iki cagri bit-bit ayni + K8/K9
#      degismezleri (artan/tekrarsiz/ayrik source_blocks, bos metin sizmaz).
# =============================================================================


def _random_block_r2(rng: random.Random) -> TextBlock:
    text_choices = [
        "Merhaba dunya", "力", "well-known", "kelime", "{0} adet %s",
        "  bosluklu  ", "A" * 50, "50%", "50%s", "Ada: selam", "勇者：こんにちは",
        "?", "!", "？", "！", "﹖", "⁇", "：", "。",
        "", "   ", "keli-\nme", ":Merhaba", "12：30", "Efe: cumle: devam",
    ]
    w = rng.choice([-100, -10, -1, 0, 1, 5, 50, 500])
    h = rng.choice([-100, -10, -1, 0, 1, 5, 50, 500])
    x = rng.randint(-100, 1000)
    y = rng.randint(-100, 1000)
    conf = rng.uniform(0.0, 1.0)
    return TextBlock(text=rng.choice(text_choices), bbox=Rect(x=x, y=y, w=w, h=h), confidence=conf)


@pytest.mark.parametrize("preset", [OcrPreset.DIALOGUE, OcrPreset.MENU, OcrPreset.TOOLTIP, OcrPreset.SUBTITLE])
def test_r2_fuzz_seeded_full_surface_no_crash_deterministic_invariants_hold(preset: OcrPreset) -> None:
    """SABIT TOHUM (SEED=20260909, PYTHONHASHSEED'den BAGIMSIZ ofset):
    K15-K18'in TUMUNU tetikleyebilecek metin/geometri karisimiyla 80
    bloklu girdi, 4 on ayarin HER BIRINDE -- cokme YOK, iki cagri
    BIT-BIT AYNI, K8 (artan+tekrarsiz+ayrik source_blocks) ve K9 (bos
    metinli Segment sizmaz) degismezleri hala tutuyor."""
    offset = sum(ord(c) for c in preset.value)
    rng = random.Random(SEED + offset + 7)
    blocks = [_random_block_r2(rng) for _ in range(80)]
    r1 = normalize(blocks, preset)
    r2 = normalize(blocks, preset)
    assert r1 == r2
    seen: set[int] = set()
    for seg in r1:
        assert seg.text.strip() != "", "K9: bos/yalniz-bosluk metinli Segment SIZMAMALI"
        assert list(seg.source_blocks) == sorted(set(seg.source_blocks)), "K8: artan + tekrarsiz"
        for b in seg.source_blocks:
            assert b not in seen, f"blok {b} birden fazla segmentte -- K8 ayriklik ihlali"
            seen.add(b)
