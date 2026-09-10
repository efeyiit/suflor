"""T-004 -- TextNormalizer: satir birlestirme, gurultu eleme, gruplama,
konusmaci ayirma, yer tutucu koruma.

Tasarim dokumani 5.2 ("Ceviri kalitesinin yarisi burada belirlenir") ve
gorev paketi T-004'un alti sorumlulugunu dogrular. Gercek OCR ciktisina
benzer girdilerle: iki satira bolunmus cumle, kesme cizgili kelime,
gercek tireli kelime, dusuk guvenli blok, tek karakterlik gurultu,
anlamli tek karakter, konusmaci etiketli diyalog, yer tutucu icren
tooltip, dort on ayarin dordu, ve yozlasmis girdiler (bos liste, tek
blok, hepsi esik alti, sifir boyutlu bbox).
"""
from __future__ import annotations

from collections.abc import Sequence

import pytest

from src.contracts.models import OcrPreset, Rect, Segment, TextBlock
from src.ocr.normalizer import normalize
from src.ocr.presets import (
    DIALOGUE_PRESET,
    MENU_PRESET,
    SUBTITLE_PRESET,
    TOOLTIP_PRESET,
)

# ---------------------------------------------------------------------------
# yardimcilar
# ---------------------------------------------------------------------------


def rect(x: int, y: int, w: int, h: int) -> Rect:
    return Rect(x=x, y=y, w=w, h=h, monitor_index=0, dpi_scale=1.0)


def block(
    text: str,
    *,
    x: int = 0,
    y: int = 0,
    w: int = 100,
    h: int = 30,
    confidence: float = 0.9,
) -> TextBlock:
    return TextBlock(text=text, bbox=rect(x, y, w, h), confidence=confidence)


def texts(segments: Sequence[Segment]) -> list[str]:
    return [s.text for s in segments]


# ---------------------------------------------------------------------------
# 1. yozlasmis girdiler -- cokme yok
# ---------------------------------------------------------------------------


def test_empty_block_list_returns_empty_list() -> None:
    assert normalize([], OcrPreset.DIALOGUE) == []


def test_single_surviving_block_returns_single_segment() -> None:
    blocks = [block("Merhaba dunya")]
    result = normalize(blocks, OcrPreset.DIALOGUE)
    assert len(result) == 1
    assert result[0].text == "Merhaba dunya"
    assert result[0].source_blocks == (0,)


def test_all_blocks_below_confidence_threshold_returns_empty_list() -> None:
    blocks = [
        block("dusuk guven bir", confidence=0.01),
        block("ikinci dusuk guven", y=40, confidence=0.02),
    ]
    assert normalize(blocks, OcrPreset.DIALOGUE) == []


def test_zero_size_bbox_does_not_crash() -> None:
    blocks = [
        TextBlock(text="sifir yukseklik", bbox=rect(0, 0, 100, 0), confidence=0.9),
        TextBlock(text="sifir genislik", bbox=rect(0, 40, 0, 30), confidence=0.9),
        block("normal blok", y=80),
    ]
    result = normalize(blocks, OcrPreset.DIALOGUE)
    # cokme yok; en azindan gecerli boyutlu blok segment olarak doner
    assert any(s.text == "normal blok" for s in result)


def test_all_whitespace_only_text_is_dropped() -> None:
    blocks = [block("   "), block("\t\n")]
    assert normalize(blocks, OcrPreset.DIALOGUE) == []


# ---------------------------------------------------------------------------
# 2. satir birlestirme (ayni paragraf, gorev paketinin kendi esigi)
# ---------------------------------------------------------------------------


def test_two_line_sentence_merges_into_one_segment_dialogue() -> None:
    # iki blok: dikey bosluk 2px (line_height=30, esik 1.5*30=45 -> icinde)
    # yatay ortusme tam (%100 >= %60 esigi)
    blocks = [
        block("Bu cumle iki satira", x=100, y=200, w=400, h=30),
        block("bolunmus durumda.", x=100, y=232, w=380, h=30),
    ]
    result = normalize(blocks, OcrPreset.DIALOGUE)
    assert len(result) == 1
    assert result[0].text == "Bu cumle iki satira bolunmus durumda."
    assert result[0].source_blocks == (0, 1)


def test_merged_segment_bbox_is_union_of_source_blocks() -> None:
    blocks = [
        block("ilk satir", x=100, y=200, w=400, h=30),
        block("ikinci satir", x=90, y=232, w=420, h=30),
    ]
    result = normalize(blocks, OcrPreset.DIALOGUE)
    assert len(result) == 1
    merged = result[0].bbox
    assert merged.x == 90
    assert merged.y == 200
    assert merged.right == max(100 + 400, 90 + 420)
    assert merged.bottom == 232 + 30


def test_far_apart_blocks_do_not_merge() -> None:
    blocks = [
        block("ilk paragraf", x=100, y=200, w=400, h=30),
        block("ikinci paragraf", x=100, y=600, w=400, h=30),
    ]
    result = normalize(blocks, OcrPreset.DIALOGUE)
    assert len(result) == 2
    assert texts(result) == ["ilk paragraf", "ikinci paragraf"]


def test_side_by_side_columns_do_not_merge_low_horizontal_overlap() -> None:
    # ayni y'de, yatayda neredeyse hic ortusmeyen iki sutun
    blocks = [
        block("sol sutun", x=0, y=200, w=100, h=30),
        block("sag sutun", x=500, y=200, w=100, h=30),
    ]
    result = normalize(blocks, OcrPreset.DIALOGUE)
    assert len(result) == 2


def test_chained_three_line_paragraph_merges_into_one_segment() -> None:
    blocks = [
        block("birinci satir", x=100, y=0, w=300, h=30),
        block("ikinci satir", x=100, y=32, w=300, h=30),
        block("ucuncu satir.", x=100, y=64, w=300, h=30),
    ]
    result = normalize(blocks, OcrPreset.DIALOGUE)
    assert len(result) == 1
    assert result[0].text == "birinci satir ikinci satir ucuncu satir."
    assert result[0].source_blocks == (0, 1, 2)


# ---------------------------------------------------------------------------
# 3. hyphen / kesme cizgisi cozumu
# ---------------------------------------------------------------------------


def test_line_break_hyphen_is_resolved_and_removed() -> None:
    # "keli-" + "me." -> "kelime." (kesme cizgisi, kucuk harfle devam)
    blocks = [
        block("Bu uzun bir keli-", x=50, y=0, w=200, h=30),
        block("me.", x=50, y=32, w=60, h=30),
    ]
    result = normalize(blocks, OcrPreset.DIALOGUE)
    assert len(result) == 1
    assert result[0].text == "Bu uzun bir kelime."


def test_real_hyphen_inside_single_block_is_never_touched() -> None:
    # "well-known" TEK blok icinde -- birlesme noktasi degil, dokunulmaz.
    blocks = [block("This creature is well-known here.")]
    result = normalize(blocks, OcrPreset.DIALOGUE)
    assert result[0].text == "This creature is well-known here."


def test_hyphen_heuristic_known_limitation_compound_word_at_line_break() -> None:
    """Belgelenmis SINIR: gercek bilesik-kelime tiresi, satir sonuna denk
    gelirse (ör. "well-\\nknown"), bu sezgisel de-hyphenation kurali
    onu kesme-cizgisi sanip KALDIRIR. Bu bir HATA degil, geometri +
    kucuk-harf-kontrolunden baska sinyali olmayan sezgiselin BILINEN ve
    BELGELENMIS yanlis-pozitif sinifidir (bkz. normalizer.py docstring,
    delivery.md known_gaps). Test, bu davranisi SESSIZCE degil ACIKCA
    sabitler."""
    blocks = [
        block("This town is well-", x=50, y=0, w=250, h=30),
        block("known for its markets.", x=50, y=32, w=300, h=30),
    ]
    result = normalize(blocks, OcrPreset.DIALOGUE)
    assert len(result) == 1
    assert result[0].text == "This town is wellknown for its markets."


def test_hyphen_followed_by_uppercase_is_not_treated_as_line_break() -> None:
    # buyuk harfle devam eden bir sonraki blok -> gercek tire/dash sayilir,
    # bosluklu birlestirilir, tire SILINMEZ.
    blocks = [
        block("Bir cumle burada biter -", x=50, y=0, w=250, h=30),
        block("Yeni cumle burada baslar.", x=50, y=32, w=300, h=30),
    ]
    result = normalize(blocks, OcrPreset.DIALOGUE)
    assert result[0].text == "Bir cumle burada biter - Yeni cumle burada baslar."


# ---------------------------------------------------------------------------
# 4. guven esigi
# ---------------------------------------------------------------------------


def test_low_confidence_block_is_dropped_others_kept() -> None:
    blocks = [
        block("iyi blok", x=0, y=0, confidence=0.9),
        block("kotu blok", x=0, y=400, confidence=0.05),
    ]
    result = normalize(blocks, OcrPreset.DIALOGUE)
    assert texts(result) == ["iyi blok"]


def test_confidence_exactly_at_threshold_is_kept() -> None:
    blocks = [block("esikte", confidence=DIALOGUE_PRESET.confidence_threshold)]
    result = normalize(blocks, OcrPreset.DIALOGUE)
    assert texts(result) == ["esikte"]


# ---------------------------------------------------------------------------
# 5. gurultu eleme (tek karakter)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("noise_char", [".", "·", "_", "~", "|", "`"])
def test_single_char_ornamental_noise_is_dropped(noise_char: str) -> None:
    blocks = [block(noise_char, confidence=0.95)]
    assert normalize(blocks, OcrPreset.DIALOGUE) == []


@pytest.mark.parametrize("meaningful_char", ["I", "a", "1", "?", "!"])
def test_single_meaningful_char_is_kept(meaningful_char: str) -> None:
    blocks = [block(meaningful_char, confidence=0.95)]
    result = normalize(blocks, OcrPreset.DIALOGUE)
    assert texts(result) == [meaningful_char]


def test_single_cjk_character_is_kept_language_independent() -> None:
    # Japonca tek kanji anlamli olabilir (ör. "hayir" -> "no" anlaminda).
    blocks = [block("力", confidence=0.95)]
    result = normalize(blocks, OcrPreset.DIALOGUE)
    assert texts(result) == ["力"]


def test_noise_block_between_two_real_lines_does_not_break_merge() -> None:
    blocks = [
        block("gercek satir bir", x=100, y=0, w=300, h=30),
        block("·", x=100, y=32, w=10, h=10, confidence=0.9),
        block("gercek satir iki.", x=100, y=64, w=300, h=30),
    ]
    result = normalize(blocks, OcrPreset.DIALOGUE)
    assert len(result) == 1
    assert result[0].text == "gercek satir bir gercek satir iki."
    assert result[0].source_blocks == (0, 2)


# ---------------------------------------------------------------------------
# 6. on ayara gore gruplama
# ---------------------------------------------------------------------------


def test_menu_preset_never_groups_even_adjacent_blocks() -> None:
    blocks = [
        block("Kilic", x=100, y=0, w=100, h=20),
        block("Kalkan", x=100, y=22, w=100, h=20),
        block("Iksir", x=100, y=44, w=100, h=20),
    ]
    result = normalize(blocks, OcrPreset.MENU)
    assert texts(result) == ["Kilic", "Kalkan", "Iksir"]
    assert all(len(s.source_blocks) == 1 for s in result)


def test_dialogue_preset_groups_close_neighbors() -> None:
    blocks = [
        block("satir bir", x=100, y=0, w=300, h=30),
        block("satir iki", x=100, y=32, w=300, h=30),
    ]
    result = normalize(blocks, OcrPreset.DIALOGUE)
    assert len(result) == 1


def test_all_four_presets_produce_segments_for_basic_input() -> None:
    blocks = [block("Basit metin", x=0, y=0, w=200, h=30)]
    for preset in OcrPreset:
        result = normalize(blocks, preset)
        assert len(result) == 1
        assert result[0].text == "Basit metin"


# ---------------------------------------------------------------------------
# 7. konusmaci etiketi
# ---------------------------------------------------------------------------


def test_speaker_label_extracted_in_dialogue() -> None:
    blocks = [block("Ayse: Merhaba, nasilsin?")]
    result = normalize(blocks, OcrPreset.DIALOGUE)
    assert result[0].speaker == "Ayse"
    assert result[0].text == "Merhaba, nasilsin?"


def test_speaker_label_fullwidth_colon_cjk() -> None:
    blocks = [block("田中：こんにちは")]
    result = normalize(blocks, OcrPreset.DIALOGUE)
    assert result[0].speaker == "田中"
    assert result[0].text == "こんにちは"


def test_no_colon_means_no_speaker() -> None:
    blocks = [block("Bu satirda iki nokta yok")]
    result = normalize(blocks, OcrPreset.DIALOGUE)
    assert result[0].speaker is None
    assert result[0].text == "Bu satirda iki nokta yok"


def test_stat_line_in_tooltip_is_not_mistaken_for_speaker() -> None:
    blocks = [block("Damage: 10-15", confidence=0.9)]
    result = normalize(blocks, OcrPreset.TOOLTIP)
    assert result[0].speaker is None
    assert result[0].text == "Damage: 10-15"


def test_stat_line_in_menu_is_not_mistaken_for_speaker() -> None:
    blocks = [block("HP: 100", confidence=0.9)]
    result = normalize(blocks, OcrPreset.MENU)
    assert result[0].speaker is None
    assert result[0].text == "HP: 100"


def test_colon_with_nothing_after_is_not_a_speaker_label() -> None:
    blocks = [block("Not:")]
    result = normalize(blocks, OcrPreset.DIALOGUE)
    assert result[0].speaker is None
    assert result[0].text == "Not:"


def test_purely_numeric_label_is_not_a_speaker() -> None:
    blocks = [block("12:30 burada gosterilir")]
    result = normalize(blocks, OcrPreset.DIALOGUE)
    assert result[0].speaker is None


# ---------------------------------------------------------------------------
# 8. yer tutucu koruma
# ---------------------------------------------------------------------------


def test_brace_and_printf_placeholders_extracted_in_tooltip() -> None:
    blocks = [
        block(
            "Bu esya {0} kere kullanilabilir, %s hasar verir",
            confidence=0.9,
        )
    ]
    result = normalize(blocks, OcrPreset.TOOLTIP)
    assert result[0].placeholders == ("{0}", "%s")
    # metin degistirilmez -- yer tutucular metnin icinde aynen bulunur
    assert "{0}" in result[0].text
    assert "%s" in result[0].text


def test_percentage_and_plain_numbers_extracted() -> None:
    blocks = [block("Saldiri 50% artar, 3 tur surer", confidence=0.9)]
    result = normalize(blocks, OcrPreset.TOOLTIP)
    assert result[0].placeholders == ("50%", "3")


def test_color_and_bbcode_tags_extracted() -> None:
    blocks = [block("<color=red>Tehlike</color> [b]bolgesi[/b]", confidence=0.9)]
    result = normalize(blocks, OcrPreset.TOOLTIP)
    assert "<color=red>" in result[0].placeholders
    assert "</color>" in result[0].placeholders
    assert "[b]" in result[0].placeholders
    assert "[/b]" in result[0].placeholders


def test_placeholders_are_always_substrings_of_final_text() -> None:
    blocks = [block("Deger %d ve yuzde 25% ve {name}", confidence=0.9)]
    result = normalize(blocks, OcrPreset.TOOLTIP)
    for ph in result[0].placeholders:
        assert ph in result[0].text


def test_no_placeholders_gives_empty_tuple() -> None:
    blocks = [block("duz metin hic yer tutucu yok")]
    result = normalize(blocks, OcrPreset.DIALOGUE)
    assert result[0].placeholders == ()


# ---------------------------------------------------------------------------
# 9. source_blocks izlenebilirligi
# ---------------------------------------------------------------------------


def test_source_blocks_track_original_indices_with_drops_between() -> None:
    blocks = [
        block("tutulan ilk", x=100, y=0, w=300, h=30),  # 0 -> tutulur
        block("·", x=100, y=32, w=10, h=10, confidence=0.9),  # 1 -> gurultu, elenir
        block("cok dusuk guven", x=100, y=64, confidence=0.01),  # 2 -> elenir
        block("tutulan ikinci.", x=100, y=96, w=300, h=30),  # 3 -> tutulur, 0 ile birlesir mi?
    ]
    result = normalize(blocks, OcrPreset.DIALOGUE)
    all_indices = sorted(i for s in result for i in s.source_blocks)
    assert all_indices == [0, 3]


def test_menu_preset_source_blocks_are_singletons() -> None:
    blocks = [block("A", x=0, y=0), block("B", x=0, y=22)]
    result = normalize(blocks, OcrPreset.MENU)
    assert result[0].source_blocks == (0,)
    assert result[1].source_blocks == (1,)


# ---------------------------------------------------------------------------
# 10. saflik / determinizm
# ---------------------------------------------------------------------------


def test_normalize_is_pure_same_input_same_output() -> None:
    blocks = [
        block("satir bir", x=100, y=0, w=300, h=30),
        block("satir iki.", x=100, y=32, w=300, h=30),
    ]
    first = normalize(blocks, OcrPreset.DIALOGUE)
    second = normalize(blocks, OcrPreset.DIALOGUE)
    assert first == second


def test_normalize_does_not_mutate_input_blocks() -> None:
    original = block("degismemeli", x=0, y=0)
    blocks = [original]
    normalize(blocks, OcrPreset.DIALOGUE)
    assert blocks[0] is original
    assert blocks[0].text == "degismemeli"


# sanity: preset sabitleri import edilebiliyor ve dogru turde
def test_preset_constants_are_normalizer_preset_instances() -> None:
    for preset_obj in (DIALOGUE_PRESET, MENU_PRESET, TOOLTIP_PRESET, SUBTITLE_PRESET):
        assert isinstance(preset_obj.confidence_threshold, float)
