"""`src/ocr/normalizer.py::normalize` icin birim testleri.

T-004 packet.md'deki ON DORT SEF KARARININ (K1-K14) HER BIRI icin en az
bir test burada. Her test fonksiyonunun ust yorumu hangi K-kararini
sinadigini belirtir. Ayrica: yozlasmis girdiler (bbox w/h==0, negatif
w/h, tek blok, bos liste, 30'dan cok blok, farkli monitor_index) ve
paket.md'nin "Test etmen gerekenler" listesindeki ozel senaryolar
(iki satira bolunmus cumle, kesme cizgili kelime, gercek tireli
`well-known`, K2 sirasini sinayan esik-alti orta blok, tek kanji/hangul,
"%s ve %s" tekrari, "50%", yalniz "Ada:" blogu, dialogue'da iki farkli
konusmacili komsu blok, dort on ayar) kapsanir.

TUR 2 (duzeltme turu -- `.agents/tasks/T-004/sef_karari-tur2.md`): dosya
sonunda DORT YENI karar (K15-K18) icin, her biri o hatayi DOGRUDAN
yakalayan REGRESYON testleriyle genisletildi -- bkz. `# --- TUR 2 ---`
basligindan sonraki blok.

TUR 5 (duzeltme turu -- `.agents/tasks/T-004/sef_karari-tur5.md`): dosya
sonunda BES YENI karar (K23-K27) icin regresyon/denetim testleri
eklendi -- bkz. `# --- TUR 5 ---` basligindan sonraki blok. K23 icin
`_normalize_impl` (normalizer.py'nin ozel, GENEL API'YE SIZMAYAN test
kancasi) DOGRUDAN import edilir.
"""
from __future__ import annotations

import math
import statistics
import time
import unicodedata
from random import Random

import pytest

from src.contracts.models import OcrPreset, Rect, Segment, TextBlock
from src.ocr.normalizer import _Item, _group_rejection_reason, _normalize_impl, _should_group, normalize
from src.ocr.presets import SPEAKER_LABEL_SEPARATORS, get_params


def blk(
    text: str,
    x: int,
    y: int,
    *,
    w: int = 300,
    h: int = 20,
    confidence: float = 0.9,
    monitor_index: int = 0,
    dpi_scale: float = 1.0,
    line_boxes: tuple[Rect, ...] = (),
) -> TextBlock:
    """Test fixture yardimcisi: kisa parametrelerle bir `TextBlock` kurar."""
    return TextBlock(
        text=text,
        bbox=Rect(x=x, y=y, w=w, h=h, monitor_index=monitor_index, dpi_scale=dpi_scale),
        confidence=confidence,
        line_boxes=line_boxes,
    )


def _all_texts_non_empty(segments: list[Segment]) -> bool:
    return all(s.text.strip() for s in segments)


# ---------------------------------------------------------------------------
# K1 -- "satir" tanimi: satir = TextBlock; line_boxes okunmaz; \n blok-ici
# birlestirme kurallariyla tek Segment'e iner.
# ---------------------------------------------------------------------------


def test_k1_line_boxes_bos_ve_dolu_ayni_sonucu_verir() -> None:
    dolu = blk("Merhaba", 10, 10, line_boxes=(Rect(10, 10, 300, 20),))
    bos = blk("Merhaba", 10, 10, line_boxes=())
    out_dolu = normalize([dolu], OcrPreset.DIALOGUE)
    out_bos = normalize([bos], OcrPreset.DIALOGUE)
    assert out_dolu == out_bos


def test_k1_blok_ici_newline_tek_segmente_iner() -> None:
    b = blk("Merhaba\ndunya", 10, 10)
    out = normalize([b], OcrPreset.DIALOGUE)
    assert len(out) == 1
    assert out[0].text == "Merhaba dunya"
    assert out[0].source_blocks == (0,)


# ---------------------------------------------------------------------------
# K2 -- islem sirasi: esik filtresi -> gurultu -> birlestirme -> konusmaci
# -> gruplama -> yer tutucu. Ortadaki esik-alti blok, sira geregi hic
# var olmamis gibi davranilmasina yol acar.
# ---------------------------------------------------------------------------


def test_k2_esik_alti_orta_blok_komsulari_birlestirir() -> None:
    # idx0 "-" ile biter, idx1 (ARADA, esik-alti) duser, idx2 kucuk harfle
    # baslar. Filtreleme birlestirmeden ONCE oldugu icin (K2), idx0 ve
    # idx2 -- idx1 hic yokmus gibi -- birbirine hyphen kurali ile birlesir.
    b0 = blk("kelime-", 10, 0, confidence=0.9)
    b1 = blk("ARA", 10, 24, confidence=0.1)  # menu esigi 0.55 altinda -> duser
    b2 = blk("lenmis", 10, 48, confidence=0.9)
    out = normalize([b0, b1, b2], OcrPreset.MENU)
    assert len(out) == 1
    assert out[0].text == "kelimelenmis"
    assert out[0].source_blocks == (0, 2)


# ---------------------------------------------------------------------------
# K3 -- cikti sirasi: bbox.y artan, esitlikte bbox.x artan.
# ---------------------------------------------------------------------------


def test_k3_cikti_okuma_sirasinda_donuyor() -> None:
    alt = blk("Alt satir", 10, 200)
    ust = blk("Ust satir", 10, 10)
    orta = blk("Orta satir", 10, 100)
    out = normalize([alt, ust, orta], OcrPreset.MENU)
    assert [s.text for s in out] == ["Ust satir", "Orta satir", "Alt satir"]


def test_k3_ayni_y_de_x_artan() -> None:
    sag = blk("Sag", 500, 10, w=100)
    sol = blk("Sol", 10, 10, w=100)
    out = normalize([sag, sol], OcrPreset.MENU)
    assert [s.text for s in out] == ["Sol", "Sag"]


# ---------------------------------------------------------------------------
# K4 -- tek karakter kurali: SINIF tabanli (L*/N* korunur; ?/! istisnasiyla
# S*/P* atilir). Beyaz liste YOK -- kanji/hangul/kiril/rakam testleriyle
# kanitlanir.
# ---------------------------------------------------------------------------


def test_k4_tek_kanji_korunur() -> None:
    out = normalize([blk("力", 10, 10)], OcrPreset.MENU)  # 力
    assert [s.text for s in out] == ["力"]


def test_k4_tek_hangul_korunur() -> None:
    out = normalize([blk("가", 10, 10)], OcrPreset.MENU)  # 가
    assert [s.text for s in out] == ["가"]


def test_k4_tek_kiril_harfi_korunur_beyaz_liste_yok() -> None:
    # {"I","a","1","?"} gibi sabit bir liste kullanilsaydi bu harf silinirdi.
    out = normalize([blk("Ж", 10, 10)], OcrPreset.MENU)  # Ж
    assert [s.text for s in out] == ["Ж"]


def test_k4_tek_rakam_korunur() -> None:
    out = normalize([blk("7", 10, 10)], OcrPreset.MENU)
    assert [s.text for s in out] == ["7"]


def test_k4_tek_sembol_atilir() -> None:
    out = normalize([blk("#", 10, 10)], OcrPreset.MENU)
    assert out == []


def test_k4_soru_ve_unlem_istisnasi_korunur() -> None:
    out = normalize([blk("?", 10, 10), blk("!", 500, 10)], OcrPreset.MENU)
    assert [s.text for s in out] == ["?", "!"]


# ---------------------------------------------------------------------------
# K5 -- hyphen kurali: yalniz satir SONUNDAKI '-' + kucuk harfle baslayan
# sonraki satir birlesir (bosluksuz); satir ORTASINDAKI tire dokunulmaz;
# hyphen kurali on-ayardan bagimsizdir (MENU ile de calisir).
# ---------------------------------------------------------------------------


def test_k5_kesme_cizgili_kelime_birlesir_on_ayardan_bagimsiz() -> None:
    b0 = blk("tra-", 10, 0)
    b1 = blk("dition", 10, 24)
    out = normalize([b0, b1], OcrPreset.MENU)  # MENU gruplamaz -- yine de birlesir
    assert len(out) == 1
    assert out[0].text == "tradition"
    assert out[0].source_blocks == (0, 1)


def test_k5_gercek_tire_dokunulmuyor() -> None:
    out = normalize([blk("well-known", 10, 10)], OcrPreset.DIALOGUE)
    assert [s.text for s in out] == ["well-known"]


def test_k5_buyuk_harfle_baslayan_sonraki_satir_birlesmez() -> None:
    b0 = blk("End-", 10, 0)
    b1 = blk("Next Sentence", 10, 24)
    out = normalize([b0, b1], OcrPreset.MENU)
    assert [s.text for s in out] == ["End-", "Next Sentence"]


def test_iki_satira_bolunmus_cumle_dialogue_ile_gruplanip_birlesir() -> None:
    b0 = blk("Bu uzun bir", 10, 0)
    b1 = blk("cumledir.", 10, 22)  # kucuk bosluk -> dialogue gruplar
    out = normalize([b0, b1], OcrPreset.DIALOGUE)
    assert len(out) == 1
    assert out[0].text == "Bu uzun bir cumledir."
    assert out[0].source_blocks == (0, 1)


# ---------------------------------------------------------------------------
# K6 -- yer tutucular: metin degismez, placeholders sirali+tekrarli
# toplanir; sayilar (ör. "50%") placeholders'a girmez.
# ---------------------------------------------------------------------------


def test_k6_placeholder_sira_ve_tekrar_korunur() -> None:
    out = normalize([blk("Merhaba %s ve %s nasilsin", 10, 10)], OcrPreset.DIALOGUE)
    assert len(out) == 1
    assert out[0].text == "Merhaba %s ve %s nasilsin"
    assert out[0].placeholders == ("%s", "%s")


def test_k6_yuzde_sayisi_placeholder_degil() -> None:
    out = normalize([blk("Toplam 50% tamamlandi", 10, 10)], OcrPreset.DIALOGUE)
    assert len(out) == 1
    assert out[0].placeholders == ()
    assert out[0].text == "Toplam 50% tamamlandi"


def test_k6_farkli_desen_turleri_sirayla_toplanir() -> None:
    text = "Merhaba {0}, saglik <color=red>dusuk</color> ve [Envanter] doldu"
    out = normalize([blk(text, 10, 10)], OcrPreset.DIALOGUE)
    assert len(out) == 1
    assert out[0].text == text
    assert out[0].placeholders == ("{0}", "<color=red>", "</color>", "[Envanter]")


# ---------------------------------------------------------------------------
# K7 -- guven esigi: esik ALTI duser, esige ESIT kalir; NaN/alan-disi
# ValueError.
# ---------------------------------------------------------------------------


def test_k7_esige_esit_kalir() -> None:
    params = get_params(OcrPreset.DIALOGUE)
    out = normalize([blk("Merhaba dunya", 10, 10, confidence=params.confidence_threshold)], OcrPreset.DIALOGUE)
    assert [s.text for s in out] == ["Merhaba dunya"]


def test_k7_esik_altinda_duser() -> None:
    params = get_params(OcrPreset.DIALOGUE)
    out = normalize(
        [blk("Merhaba dunya", 10, 10, confidence=params.confidence_threshold - 0.01)],
        OcrPreset.DIALOGUE,
    )
    assert out == []


def test_k7_nan_confidence_value_error() -> None:
    with pytest.raises(ValueError):
        normalize([blk("Merhaba", 10, 10, confidence=math.nan)], OcrPreset.DIALOGUE)


@pytest.mark.parametrize("bad", [1.5, -0.1, 1.0001])
def test_k7_alan_disi_confidence_value_error(bad: float) -> None:
    with pytest.raises(ValueError):
        normalize([blk("Merhaba", 10, 10, confidence=bad)], OcrPreset.DIALOGUE)


# ---------------------------------------------------------------------------
# K8 -- source_blocks: ORIJINAL indeksler, artan sirada, segmentler arasi
# AYRIK.
# ---------------------------------------------------------------------------


def test_k8_source_blocks_orijinal_indeks_ve_artan_sira() -> None:
    # idx1 dusuyor (esik alti); idx0/idx2/idx3 zincirleme hyphen ile
    # birlesiyor. Sonuc TEK segmentin source_blocks'u (0,2,3) olmali --
    # (0,1,2) DEGIL (filtre-sonrasi sikistirilmis indeks olsaydi boyle
    # cikardi).
    b0 = blk("abc-", 10, 0, confidence=0.9)
    b1 = blk("ZZZ", 10, 24, confidence=0.1)
    b2 = blk("def-", 10, 48, confidence=0.9)
    b3 = blk("ghi", 10, 72, confidence=0.9)
    out = normalize([b0, b1, b2, b3], OcrPreset.MENU)
    assert len(out) == 1
    assert out[0].text == "abcdefghi"
    assert out[0].source_blocks == (0, 2, 3)
    # artan sira:
    assert list(out[0].source_blocks) == sorted(out[0].source_blocks)


def test_k8_source_blocks_segmentler_arasi_ayrik() -> None:
    b0 = blk("Merhaba", 10, 0)
    b1 = blk("Gunaydin", 10, 500)  # cok uzak -- MENU zaten gruplamaz
    out = normalize([b0, b1], OcrPreset.MENU)
    assert len(out) == 2
    all_indices = [i for s in out for i in s.source_blocks]
    assert sorted(all_indices) == [0, 1]
    assert len(set(all_indices)) == len(all_indices)  # tekrarsiz -> ayrik


# ---------------------------------------------------------------------------
# K9 -- konusmaci: yalniz-etiket blok kendi segmentini uretmez, sonrakine
# tasinir (yoksa duser); farkli konusmacili komsu bloklar asla gruplanmaz;
# bos/yalniz-bosluk metinli Segment ASLA uretilmez.
# ---------------------------------------------------------------------------


def test_k9_yalniz_etiket_sonraki_bloga_tasinir() -> None:
    etiket = blk("Ada:", 10, 0)
    icerik = blk("Merhaba nasilsin", 10, 22)
    out = normalize([etiket, icerik], OcrPreset.DIALOGUE)
    assert len(out) == 1
    assert out[0].speaker == "Ada"
    assert out[0].text == "Merhaba nasilsin"
    assert out[0].source_blocks == (0, 1)  # etiket-blok da katkida bulundu


def test_k9_yalniz_etiket_sonraki_yoksa_duser() -> None:
    out = normalize([blk("Ada:", 10, 0)], OcrPreset.DIALOGUE)
    assert out == []


def test_k9_dialogue_farkli_konusmacili_komsu_bloklar_ayri_kalir() -> None:
    ada = blk("Ada: Merhaba", 10, 0)
    efe = blk("Efe: Selam", 10, 22)  # cok yakin -- gruplanmaya aday geometri
    out = normalize([ada, efe], OcrPreset.DIALOGUE)
    assert len(out) == 2
    assert (out[0].speaker, out[0].text) == ("Ada", "Merhaba")
    assert (out[1].speaker, out[1].text) == ("Efe", "Selam")


def test_k9_bos_metinli_segment_asla_uretilmez() -> None:
    bloklar = [blk("Ada:", 10, 0), blk("   ", 10, 22), blk("#", 10, 44)]
    out = normalize(bloklar, OcrPreset.DIALOGUE)
    assert _all_texts_non_empty(out)


# ---------------------------------------------------------------------------
# K10 -- bbox birlesimi: kapsayici dikdortgen; farkli monitor_index/
# dpi_scale -> ValueError.
# ---------------------------------------------------------------------------


def test_k10_bbox_birlesimi_kapsayici() -> None:
    b0 = blk("Bu uzun bir", 10, 0, w=200, h=20)
    b1 = blk("cumledir.", 50, 22, w=260, h=18)
    out = normalize([b0, b1], OcrPreset.DIALOGUE)
    assert len(out) == 1
    bbox = out[0].bbox
    assert bbox.x == 10
    assert bbox.y == 0
    assert bbox.right == max(b0.bbox.right, b1.bbox.right)
    assert bbox.bottom == max(b0.bbox.bottom, b1.bbox.bottom)


def test_k10_farkli_monitor_index_value_error() -> None:
    b0 = blk("tra-", 10, 0, monitor_index=0)
    b1 = blk("dition", 10, 22, monitor_index=1)
    with pytest.raises(ValueError):
        normalize([b0, b1], OcrPreset.MENU)


def test_k10_farkli_dpi_scale_value_error() -> None:
    b0 = blk("tra-", 10, 0, dpi_scale=1.0)
    b1 = blk("dition", 10, 22, dpi_scale=1.25)
    with pytest.raises(ValueError):
        normalize([b0, b1], OcrPreset.MENU)


# ---------------------------------------------------------------------------
# K11 -- gruplama: menu gruplamaz, digerleri gruplar; preset farklari
# SADECE presets.py'deki sayisal parametreler (guven esigi, dikey bosluk
# orani, maksimum grup uzunlugu).
# ---------------------------------------------------------------------------


def test_k11_menu_gruplamaz_dialogue_gruplar_ayni_geometri() -> None:
    b0 = blk("Bu uzun bir", 10, 0)
    b1 = blk("cumledir.", 10, 22)
    menu_out = normalize([b0, b1], OcrPreset.MENU)
    dialogue_out = normalize([b0, b1], OcrPreset.DIALOGUE)
    assert len(menu_out) == 2
    assert len(dialogue_out) == 1


def test_k11_dikey_bosluk_orani_preset_farkini_degistirir() -> None:
    # h=20; dialogue esigi 0.8*20=16, tooltip esigi 0.3*20=6. gap=10:
    # dialogue'da gruplanir, tooltip'te gruplanmaz.
    b0 = blk("Bu uzun bir", 10, 0, h=20)
    b1 = blk("cumledir.", 10, 30, h=20)  # gap = 30-20 = 10
    dialogue_out = normalize([b0, b1], OcrPreset.DIALOGUE)
    tooltip_out = normalize([b0, b1], OcrPreset.TOOLTIP)
    assert len(dialogue_out) == 1
    assert len(tooltip_out) == 2


def test_k11_guven_esigi_preset_farkini_degistirir_dialogue_tooltip() -> None:
    dialogue_th = get_params(OcrPreset.DIALOGUE).confidence_threshold
    tooltip_th = get_params(OcrPreset.TOOLTIP).confidence_threshold
    assert dialogue_th < tooltip_th
    c = (dialogue_th + tooltip_th) / 2  # dialogue'yu gecer, tooltip'i gecmez
    b = blk("Merhaba dunya", 10, 10, confidence=c)
    assert normalize([b], OcrPreset.DIALOGUE) != []
    assert normalize([b], OcrPreset.TOOLTIP) == []


def test_k11_guven_esigi_preset_farkini_degistirir_dialogue_subtitle() -> None:
    dialogue_th = get_params(OcrPreset.DIALOGUE).confidence_threshold
    subtitle_th = get_params(OcrPreset.SUBTITLE).confidence_threshold
    assert subtitle_th < dialogue_th
    c = (dialogue_th + subtitle_th) / 2  # subtitle'i gecer, dialogue'yu gecmez
    b = blk("Merhaba dunya", 10, 10, confidence=c)
    assert normalize([b], OcrPreset.SUBTITLE) != []
    assert normalize([b], OcrPreset.DIALOGUE) == []


def test_k11_maksimum_grup_karakteri_preset_farkini_degistirir() -> None:
    tooltip_cap = get_params(OcrPreset.TOOLTIP).max_group_chars
    dialogue_cap = get_params(OcrPreset.DIALOGUE).max_group_chars
    assert tooltip_cap < dialogue_cap
    # birlesik uzunluk tooltip capinin USTUNDE, dialogue capinin ALTINDA
    half_len = (tooltip_cap + 10) // 2
    text_a = ("ke" * half_len)[:half_len]
    text_b = ("le" * half_len)[:half_len]
    assert tooltip_cap < len(text_a) + 1 + len(text_b) <= dialogue_cap
    b0 = blk(text_a, 10, 0)
    b1 = blk(text_b, 10, 22)
    dialogue_out = normalize([b0, b1], OcrPreset.DIALOGUE)
    tooltip_out = normalize([b0, b1], OcrPreset.TOOLTIP)
    assert len(dialogue_out) == 1
    assert len(tooltip_out) == 2


def test_k11_yatay_ortusme_yetersizse_gruplanmiyor() -> None:
    b0 = blk("Sol taraf", 0, 0, w=100, h=20)
    b1 = blk("Sag taraf", 400, 10, w=100, h=20)  # dikeyde yakin, yatayda ortusme yok
    out = normalize([b0, b1], OcrPreset.DIALOGUE)
    assert len(out) == 2


# ---------------------------------------------------------------------------
# K12 -- bos sonuclar: bos girdi, tum bloklar esik alti, gurultu sonrasi
# hicbir sey kalmadi -> hepsi [].
# ---------------------------------------------------------------------------


def test_k12_bos_girdi_bos_liste() -> None:
    assert normalize([], OcrPreset.DIALOGUE) == []


def test_k12_tum_bloklar_esik_alti_bos_liste() -> None:
    out = normalize([blk("Merhaba", 10, 10, confidence=0.01)], OcrPreset.DIALOGUE)
    assert out == []


def test_k12_gurultu_sonrasi_hicbir_sey_kalmadi_bos_liste() -> None:
    out = normalize([blk("#", 10, 10), blk("   ", 200, 10)], OcrPreset.DIALOGUE)
    assert out == []


# ---------------------------------------------------------------------------
# K14 -- performans butcesi: 30 blok, ~40 karakter/blok, dialogue,
# deterministik girdi, 50 cagri, medyan <= 5 ms. AŞIMDA KIRILIR.
# ---------------------------------------------------------------------------


def _budget_blocks() -> list[TextBlock]:
    """Deterministik 30 bloklu girdi -- tester ayni olcumu tekrar edebilir."""
    return [
        blk(f"Bu diyalog metni numara {i:02d} icin ornek satirdir.", 10, i * 22, confidence=0.9)
        for i in range(30)
    ]


def test_k14_normalizasyon_butcesi_5ms_medyan() -> None:
    blocks = _budget_blocks()
    assert len(blocks) == 30
    assert all(38 <= len(b.text) <= 60 for b in blocks)

    durations_ms: list[float] = []
    for _ in range(50):
        start = time.perf_counter()
        normalize(blocks, OcrPreset.DIALOGUE)
        durations_ms.append((time.perf_counter() - start) * 1000.0)

    median_ms = statistics.median(durations_ms)
    assert median_ms <= 5.0, f"medyan {median_ms:.3f} ms > 5 ms butcesi (K14)"


# ---------------------------------------------------------------------------
# Yozlasmis girdiler -- hicbiri cokmez (§5.6, packet.md).
# ---------------------------------------------------------------------------


def test_yozlasmis_bbox_genislik_sifir_cokmez() -> None:
    out = normalize([blk("Merhaba", 10, 10, w=0)], OcrPreset.DIALOGUE)
    assert [s.text for s in out] == ["Merhaba"]


def test_yozlasmis_bbox_yukseklik_sifir_cokmez() -> None:
    b0 = blk("Bu uzun bir", 10, 0, h=0)
    b1 = blk("cumledir.", 10, 0, h=0)
    out = normalize([b0, b1], OcrPreset.DIALOGUE)
    assert _all_texts_non_empty(out)


def test_yozlasmis_negatif_genislik_yukseklik_cokmez() -> None:
    out = normalize([blk("Merhaba", 10, 10, w=-5, h=-5)], OcrPreset.DIALOGUE)
    assert [s.text for s in out] == ["Merhaba"]


def test_yozlasmis_bos_ve_yalniz_bosluk_metin_cokmez() -> None:
    out = normalize([blk("", 10, 10), blk("   ", 200, 10)], OcrPreset.DIALOGUE)
    assert out == []


def test_yozlasmis_tek_blok_cokmez() -> None:
    out = normalize([blk("Tek blok", 10, 10)], OcrPreset.DIALOGUE)
    assert [s.text for s in out] == ["Tek blok"]


def test_yozlasmis_otuzdan_cok_blok_cokmez() -> None:
    bloklar = [blk(f"Satir {i}", 10, i * 22) for i in range(45)]
    out = normalize(bloklar, OcrPreset.MENU)
    assert len(out) == 45


# ---------------------------------------------------------------------------
# --- TUR 2 (duzeltme turu) -- K15-K18 regresyon testleri -------------------
# ---------------------------------------------------------------------------
# Kaynak: `.agents/tasks/T-004/sef_karari-tur2.md`. Her test asagida, TUR
# 1'de tester-A/tester-C tarafindan bulunan VE sef tarafindan bagimsiz
# yeniden uretilen dort bulgudan birini DOGRUDAN yakalar -- yani bu
# testler eski (tur 1) koda karsi calistirilirsa KIRMIZI cikar (bkz.
# evidence/pytest-red-r2.txt), yeni koda karsi YESIL (evidence/pytest-r2.txt).


# --- K15 -- Bulgu 1 (KRITIK, Tester-C): etiket + coklu govde blogu -----


def test_k15_kritik_etiketli_coklu_govde_birlesir_ascii() -> None:
    """Tasarim dokumani S5.2'nin modulun VAR OLMA SEBEBI olarak verdigi
    ornegin ta kendisi: `['Ada:', 'Bu uzun bir', 'cumledir.']` TUR 1'de
    2 segmente bolunuyordu (ikincisi `speaker=None`, cumle KOPUYORDU).
    K15 ile 1 segmente birlesir, konusmaci VE cumle butunlugu korunur."""
    etiket = blk("Ada:", 10, 0)
    satir1 = blk("Bu uzun bir", 10, 22)
    satir2 = blk("cumledir.", 10, 44)
    out = normalize([etiket, satir1, satir2], OcrPreset.DIALOGUE)
    assert len(out) == 1
    assert out[0].speaker == "Ada"
    assert out[0].text == "Bu uzun bir cumledir."
    assert out[0].source_blocks == (0, 1, 2)


def test_k15_kritik_etiketli_coklu_govde_birlesir_japonca() -> None:
    """Ayni senaryo, Japonca'da BIREBIR ayni sekilde bozuluyordu (TUR 1)
    ve BIREBIR ayni sekilde duzeliyor (TUR 2, K15). Etiket ASCII `:` ile
    (K17'nin fullwidth ayraci burada devrede degil -- ayri test:
    `test_k17_fullwidth_iki_nokta_konusmaci_ayiklanir`)."""
    etiket = blk("勇者:", 10, 0)
    satir1 = blk("この町はとても", 10, 22)
    satir2 = blk("大きいですね。", 10, 44)
    out = normalize([etiket, satir1, satir2], OcrPreset.DIALOGUE)
    assert len(out) == 1
    assert out[0].speaker == "勇者"
    assert out[0].text == "この町はとても 大きいですね。"
    assert out[0].source_blocks == (0, 1, 2)


# --- K15 -- gruplama konusmaci matrisinin BES satirinin HER BIRI -------
# `_should_group` DOGRUDAN cagrilir: geometri SABIT tutulur (tam dikey
# komsuluk + tam yatay ortusme, DIALOGUE esikleri icinde), boylece TEK
# degisken konusmaci ciftidir -- sonuc SADECE K15 matrisini yansitir.


def _matrix_items(a_speaker: str | None, b_speaker: str | None) -> tuple[_Item, _Item]:
    a = _Item(text="a", bbox=Rect(x=0, y=0, w=100, h=20), speaker=a_speaker, source_blocks=(0,))
    b = _Item(text="b", bbox=Rect(x=0, y=20, w=100, h=20), speaker=b_speaker, source_blocks=(1,))
    return a, b


def test_k15_matris_x_x_gruplanir() -> None:
    """a.speaker=X, b.speaker=X (ayni) -> EVET, grubun speaker'i X."""
    a, b = _matrix_items("Ada", "Ada")
    assert _should_group(a, b, get_params(OcrPreset.DIALOGUE)) is True


def test_k15_matris_x_none_gruplanir_devam_satiri() -> None:
    """a.speaker=X, b.speaker=None -> EVET (devam satiri, K15'in asil
    duzelttigi satir) -- X MIRAS ALINIR."""
    a, b = _matrix_items("Ada", None)
    assert _should_group(a, b, get_params(OcrPreset.DIALOGUE)) is True


def test_k15_matris_none_none_gruplanir() -> None:
    """a.speaker=None, b.speaker=None -> EVET (iki etiketsiz oge normal
    sekilde gruplanir -- TUR 1'de de dogruydu, K15 bunu BOZMADI)."""
    a, b = _matrix_items(None, None)
    assert _should_group(a, b, get_params(OcrPreset.DIALOGUE)) is True


def test_k15_matris_none_y_gruplanmaz_yeni_konusmaci() -> None:
    """a.speaker=None, b.speaker=Y -> HAYIR (b YENI bir konusmaci
    basliyor -- a'nin "devam"i olamaz, yon ONEMLI)."""
    a, b = _matrix_items(None, "Efe")
    assert _should_group(a, b, get_params(OcrPreset.DIALOGUE)) is False


def test_k15_matris_x_y_gruplanmaz_konusmaci_siniri() -> None:
    """a.speaker=X, b.speaker=Y (X != Y) -> HAYIR (K9'un asil niyeti:
    iki FARKLI adlandirilmis konusmaci ASLA birlesmez -- K15 SONRASI da
    degismedi)."""
    a, b = _matrix_items("Ada", "Efe")
    assert _should_group(a, b, get_params(OcrPreset.DIALOGUE)) is False


# --- K16 -- Bulgu 2 (BLOKE EDICI, Tester-A): yozlasmis yukseklikte -----
# gruplama artik KOSULSUZ reddedilir (gap degerine BAKILMAKSIZIN)


def test_k16_yukseklik_sifir_gap_sifir_iki_segment() -> None:
    """h=0 VE gap=0 (iki blok AYNI y'de, ikisi de h=0) -- TUR 1'de
    docstring'in "gruplama yok" vaadine RAGMEN 1 segmente birlesiyordu
    (`gap > 0` degilse eski kod reddetmiyordu); K16 ile HER ZAMAN 2
    segment."""
    b0 = blk("Merhaba", 10, 0, h=0)
    b1 = blk("dunya", 10, 0, h=0)
    out = normalize([b0, b1], OcrPreset.DIALOGUE)
    assert len(out) == 2
    assert [s.text for s in out] == ["Merhaba", "dunya"]


def test_k16_negatif_yukseklik_iki_segment() -> None:
    """a: y=-15 h=20 (bottom=5), b: y=0 h=-10 (bottom=-10) -> gap=-5
    (kutular cakisiyor); ref_height=min(20,-10)=-10 <= 0 -> K16 ile
    KOSULSUZ reddedilir, 2 segment (TUR 1'de 1 segmente birlesiyordu --
    sef'in ILK sondasi da bunu yanlis kurup dogrulayamamisti, PROTOKOL
    S3 kapi 6)."""
    b0 = blk("Merhaba", 10, -15, h=20)
    b1 = blk("dunya", 10, 0, h=-10)
    out = normalize([b0, b1], OcrPreset.DIALOGUE)
    assert len(out) == 2
    assert [s.text for s in out] == ["Merhaba", "dunya"]


# --- K17 -- Bulgu 3 (BLOKE EDICI, Tester-C): fullwidth iki nokta -------


def test_k17_fullwidth_iki_nokta_konusmaci_ayiklanir() -> None:
    """`'勇者：こんにちは'` (fullwidth `：` U+FF1A ile) -- TUR 1'de bu
    ayirac taninmiyordu, blok konusmacisiz KALIYORDU; K17 ile konusmaci
    dogru ayiklanir (JP/KR oyunlarinda STANDART yazim bicimi)."""
    out = normalize([blk("勇者：こんにちは", 10, 0)], OcrPreset.DIALOGUE)
    assert len(out) == 1
    assert out[0].speaker == "勇者"
    assert out[0].text == "こんにちは"


def test_k17_ayirac_kumesi_ascii_ve_fullwidth_icerir() -> None:
    """K17 karari: adlandirilmis ayirac sabiti (`presets.py`) EN AZ ASCII
    `:` VE fullwidth `：` icermeli."""
    assert ":" in SPEAKER_LABEL_SEPARATORS
    assert "：" in SPEAKER_LABEL_SEPARATORS


# --- K18 -- Bulgu 4 (BLOKE EDICI, Tester-C): fullwidth ?/! tek karakter -


def test_k18_fullwidth_soru_unlem_tek_karakter_korunur() -> None:
    """Tek-karakterli fullwidth `？` (U+FF1F) VE `！` (U+FF01) bloklari --
    TUR 1'de SESSIZCE siliniyordu (ASCII `?`/`!` zaten korunuyordu, bkz.
    `test_k4_soru_ve_unlem_istisnasi_korunur`); K18 (NFKC denkligi) ile
    ARTIK korunuyor."""
    out = normalize([blk("？", 10, 10), blk("！", 500, 10)], OcrPreset.MENU)
    assert [s.text for s in out] == ["？", "！"]


# ---------------------------------------------------------------------------
# --- TUR 3 (duzeltme turu) -- K19-K20 regresyon testleri -------------------
# ---------------------------------------------------------------------------
# Kaynak: `.agents/tasks/T-004/sef_karari-tur3.md`. Tur 2'de UCU DE tester
# onay verdi; sef Tester-C'nin "bloke etmeyen" saydigi IKI notu inceledi ve
# BIRINI (K19) yeniden siniflandirdi -- ikisi de bu turde duzeltiliyor.
# Asagidaki testler eski (tur 2) koda karsi calistirilirsa K19 testleri
# KIRMIZI cikar (bkz. evidence/pytest-red-r3.txt), yeni koda karsi YESIL.


# --- K19 -- uzunluk sinirindan bolunen kuyruk konusmaciyi MIRAS alir ----


def test_k19_uzunluk_bolunmesinde_kuyruk_speaker_miras_alir_ascii() -> None:
    """"Ada:" etiketini COK sayida (~60 karakterlik) govde bloğu takip
    ediyor -- birlikte `max_group_chars`'i (DIALOGUE) kesinlikle asiyor,
    bu yuzden en az bir UZUNLUK-kaynakli bolunme olusuyor. TUR 2'de (K15
    dahil) boyle bir bolunmenin kuyrugu speaker=None KALIYORDU (bilgi
    kaybi -- sef_karari-tur3.md ornegiyle BIREBIR ayni sinif hata); K19
    ile HER kuyruk segment Ada'yi MIRAS alir. Geometri (dikey bosluk=2px,
    tam yatay ortusme) gruplamayi KESMEYECEK kadar sikidir -- bolunmenin
    TEK sebebi uzunluktur."""
    cap = get_params(OcrPreset.DIALOGUE).max_group_chars
    etiket = blk("Ada:", 10, 0)
    govde_metni = "x" * 60
    n = (cap // 60) + 3  # cap'i kesinlikle asacak kadar govde blogu
    govde = [blk(govde_metni, 10, 22 * (i + 1)) for i in range(n)]
    out = normalize([etiket, *govde], OcrPreset.DIALOGUE)
    assert len(out) >= 2  # UZUNLUK siniri en az bir bolunme yaratti
    assert all(s.speaker == "Ada" for s in out)  # K19: HER kuyruk MIRAS aldi
    # K8: butun blok indeksleri (etiket dahil) segmentlere AYRIK dagitilmis
    all_src = sorted(i for s in out for i in s.source_blocks)
    assert all_src == list(range(n + 1))


def test_k19_uzunluk_bolunmesinde_kuyruk_speaker_miras_alir_japonca() -> None:
    """Ayni senaryo Japonca'da -- `len()` codepoint sayar, coklu-baytlik
    karakterlerde de K19 AYNI sekilde calisir (`normalize` zaten dil
    parametresi almaz, K5 gerekcesiyle AYNI ilke)."""
    cap = get_params(OcrPreset.DIALOGUE).max_group_chars
    etiket = blk("勇者:", 10, 0)
    govde_metni = "あ" * 60
    n = (cap // 60) + 3
    govde = [blk(govde_metni, 10, 22 * (i + 1)) for i in range(n)]
    out = normalize([etiket, *govde], OcrPreset.DIALOGUE)
    assert len(out) >= 2
    assert all(s.speaker == "勇者" for s in out)
    all_src = sorted(i for s in out for i in s.source_blocks)
    assert all_src == list(range(n + 1))


def test_k19_geometrik_bosluk_bolunmesinde_kuyruk_speaker_none_kalir() -> None:
    """Ayni etiketli govde, ama ARADA gruplamayi KESECEK kadar buyuk bir
    DIKEY BOSLUK var (uzunluk siniri BURADA devreye GIRMEDEN once
    geometri zaten reddediyor) -- K19 bu durumda MIRAS ALMAZ: kuyruk
    segment speaker=None KALIR (bolunme sebebi GEOMETRI, "yeni baglam
    OLABILIR" -- sef_karari-tur3.md, K19 tablosunun ikinci satiri)."""
    params = get_params(OcrPreset.DIALOGUE)
    etiket = blk("Ada:", 10, 0)
    govde1 = blk("ilk parca", 10, 22, h=20)
    # gap, esik olan (max_vertical_gap_ratio * ref_height)'i acikca asiyor
    buyuk_bosluk_y = 22 + 20 + int(params.max_vertical_gap_ratio * 20) + 50
    govde2 = blk("ikinci parca", 10, buyuk_bosluk_y, h=20)
    out = normalize([etiket, govde1, govde2], OcrPreset.DIALOGUE)
    assert len(out) == 2
    assert out[0].speaker == "Ada"
    assert out[0].text == "ilk parca"
    assert out[1].speaker is None  # K19: GEOMETRIK bolunme -- miras YOK
    assert out[1].text == "ikinci parca"


def test_k19_farkli_konusmaci_asla_birlesmez_miras_da_yok() -> None:
    """Uzunluk siniri devrede OLMASA bile, kuyruk KENDI etiketiyle
    (FARKLI bir konusmaci) geliyorsa K19'un miras mekanizmasi bunu
    EZMEZ -- K9/K15'in "iki farkli konusmaci ASLA birlesmez" ilkesi K19
    SONRASI da BIREBIR gecerlidir (K19 SADECE `_should_group` `False`
    dondukten SONRAKI adima dokunur, KARARIN KENDISINE degil)."""
    etiket_ada = blk("Ada:", 10, 0)
    govde_ada = blk("x" * 60, 10, 22)
    etiket_efe = blk("Efe:", 10, 44)
    govde_efe = blk("y" * 60, 10, 66)
    out = normalize([etiket_ada, govde_ada, etiket_efe, govde_efe], OcrPreset.DIALOGUE)
    assert len(out) == 2
    assert out[0].speaker == "Ada"
    assert out[1].speaker == "Efe"  # KENDI etiketi -- Ada'dan miras ALMADI


def test_k19_matris_x_none_length_disinda_miras_yok_kontrolu() -> None:
    """K15 matrisinin `X/None -> EVET (gruplanir)` satiri K19 SONRASI da
    degismedi -- `_should_group` HALA bool dondurur, `_group_rejection_
    reason` ile ayni sonucu verir (bu ikisi arasindaki tutarlilik,
    dogrudan `_should_group` cagiran K15 testlerinin K19 SONRASI da
    gecerli kalmasinin GUVENCESIDIR)."""
    from src.ocr.normalizer import _group_rejection_reason

    a = _Item(text="a", bbox=Rect(x=0, y=0, w=100, h=20), speaker="Ada", source_blocks=(0,))
    b = _Item(text="b", bbox=Rect(x=0, y=20, w=100, h=20), speaker=None, source_blocks=(1,))
    params = get_params(OcrPreset.DIALOGUE)
    assert _group_rejection_reason(a, b, params) is None
    assert _should_group(a, b, params) is True


# --- K20 -- NFKC ile acilan ALTI karakterin HEPSI tek-karakter blok -----
# olarak korunuyor (olgusal docstring duzeltmesi -- davranis DEGISMEDI).
# FF01/FF1F zaten K18 testinde kapsanmisti; burada ALTISI birlikte, sefin
# tam Unicode taramasindan (sef_karari-tur3.md) birebir alinan listeyle
# dogrulanir.


@pytest.mark.parametrize(
    "ch",
    [
        "︕",  # PRESENTATION FORM FOR VERTICAL EXCLAMATION MARK
        "︖",  # PRESENTATION FORM FOR VERTICAL QUESTION MARK
        "﹖",  # SMALL QUESTION MARK
        "﹗",  # SMALL EXCLAMATION MARK
        "！",  # FULLWIDTH EXCLAMATION MARK
        "？",  # FULLWIDTH QUESTION MARK
    ],
)
def test_k20_nfkc_ile_acilan_alti_karakterin_hepsi_korunur(ch: str) -> None:
    """sef_karari-tur3.md: sefin tam Unicode taramasinin (0x0-0x10FFFF)
    buldugu, NFKC ile `?`/`!`ye acilan ALTI karakterin HER BIRI tek-
    karakterli bir blok olarak KORUNUR (silinmez) -- K18'in davranisi
    DEGISMEDI, bu test yalniz listenin TAMAMINI (docstring'deki K20
    duzeltmesinin dayandigi liste) dogrular."""
    out = normalize([blk(ch, 10, 10)], OcrPreset.MENU)
    assert [s.text for s in out] == [ch]


# ---------------------------------------------------------------------------
# --- TUR 4 (duzeltme turu) -- K21 regresyon testleri ------------------------
# ---------------------------------------------------------------------------
# Kaynak: `.agents/tasks/T-004/sef_karari-tur4.md`, `.agents/tasks/T-004/
# feedback-C.md`. Tur 3'te Tester-B onay, Tester-C RET verdi; sef bulguyu
# kendi eliyle yeniden uretti ve dogruladi. Kok sebep: `_group_rejection_
# reason` SABIT sirada (`speaker -> length -> height -> gap -> width ->
# overlap`) calisir ve YALNIZ ILK basarisiz kontrolun kodunu dondurur --
# K19 (tur 3) bir ciftin AYNI ANDA hem uzunluk hem geometri tarafindan
# reddedilebilecegini (red sebeplerinin BIRBIRINI DISLAMADIGINI) gozden
# kacirmisti: boyle bir ciftte kod hep "length" donduruyor, gercek
# geometrik kopus GORUNMUYOR, K19 YANLISLIKLA miras uyguluyordu. K21
# duzeltmesi: miras SADECE `max_group_chars` TEK BASINA engelse uygulanir
# -- `_group_rejection_reason`'a eklenen `ignore_length` parametresiyle
# "uzunluk siniri sonsuz olsaydi bu cift gruplanir miydi?" sorusu DOGRUDAN
# sorulur. Asagidaki testler DUZELTME ONCESI (tur 3) koda karsi
# calistirilirsa bilesik-sinir testleri (h=0/w=0/gap/overlap ile uzunluk
# BIRLIKTE basarisiz olanlar) KIRMIZI cikar (bkz. evidence/pytest-red-r4.txt).


# --- Dusuk seviye: `_group_rejection_reason` `ignore_length` davranisi --
# Bu blokta HER cift ayni konusmaci-devam iliskisini tasir (a.speaker=
# "Ada", b.speaker=None) VE metinleri (150+1+150=301 karakter) DIALOGUE
# cap'ini (280) HER ZAMAN asar -- boylece orijinal (ignore_length=False)
# cagrida SIRA geregi HER ZAMAN "length" donmesi GARANTI; degisen tek sey
# GEOMETRIDIR, bu da `ignore_length=True` cagrisinin sonucunu belirler.


def test_k21_uzunluk_tek_engelse_ignore_length_none_doner_ascii() -> None:
    """Geometri SIKI (gap=2px < esik, TAM yatay ortusme) -- uzunluk
    disinda HICBIR kontrol reddetmiyor. Orijinal cagri "length" doner
    (SIRADAKI ilk basarisiz kontrol); `ignore_length=True` ile YENIDEN
    sorulunca `None` doner -- yani `max_group_chars` SONSUZ olsaydi bu
    cift GRUPLANIRDI: TEK engel uzunluktur, K21'in miras kosulu bu
    ciftte SAGLANIR."""
    params = get_params(OcrPreset.DIALOGUE)
    a = _Item(text="x" * 150, bbox=Rect(x=0, y=0, w=100, h=20), speaker="Ada", source_blocks=(0,))
    b = _Item(text="y" * 150, bbox=Rect(x=0, y=22, w=100, h=20), speaker=None, source_blocks=(1,))
    assert _group_rejection_reason(a, b, params) == "length"
    assert _group_rejection_reason(a, b, params, ignore_length=True) is None


def test_k21_uzunluk_tek_engelse_ignore_length_none_doner_japonca() -> None:
    """Ayni senaryo Japonca karakterlerle -- `len()` codepoint sayar,
    K21'in kontrolu dilden BAGIMSIZDIR (K5/K19 ile ayni ilke)."""
    params = get_params(OcrPreset.DIALOGUE)
    a = _Item(text="あ" * 150, bbox=Rect(x=0, y=0, w=100, h=20), speaker="Ada", source_blocks=(0,))
    b = _Item(text="い" * 150, bbox=Rect(x=0, y=22, w=100, h=20), speaker=None, source_blocks=(1,))
    assert _group_rejection_reason(a, b, params) == "length"
    assert _group_rejection_reason(a, b, params, ignore_length=True) is None


def test_k21_uzunluk_ve_buyuk_dikey_bosluk_miras_yok() -> None:
    """AYNI cift, ama `b` artik 1000px asagida -- GERCEK, uzunluktan
    BAGIMSIZ bir geometrik kopus var. Orijinal cagri YINE "length" doner
    (SIRA geregi, gap kontrolune hic ULASILMAZ) -- bu TAM OLARAK
    tur 3'un kusuruydu. `ignore_length=True` ile "gap" doner (`None`
    DEGIL): TEK engel uzunluk DEGIL, K21'in miras kosulu SAGLANMAZ."""
    params = get_params(OcrPreset.DIALOGUE)
    a = _Item(text="x" * 150, bbox=Rect(x=0, y=0, w=100, h=20), speaker="Ada", source_blocks=(0,))
    b = _Item(text="y" * 150, bbox=Rect(x=0, y=1000, w=100, h=20), speaker=None, source_blocks=(1,))
    assert _group_rejection_reason(a, b, params) == "length"
    assert _group_rejection_reason(a, b, params, ignore_length=True) == "gap"


def test_k21_uzunluk_ve_yukseklik_sifir_miras_yok() -> None:
    """`b.bbox.h == 0` (yozlasmis, K16) AYNI ANDA uzunluk siniri da
    asiliyor. Orijinal cagri "length" (SIRA geregi); `ignore_length=True`
    "height" doner -- yozlasmis geometride K16 KOSULSUZ reddi, K21
    SONRASI da uzunluk kontrolunun GOLGESINE DUSMEZ."""
    params = get_params(OcrPreset.DIALOGUE)
    a = _Item(text="x" * 150, bbox=Rect(x=0, y=0, w=100, h=20), speaker="Ada", source_blocks=(0,))
    b = _Item(text="y" * 150, bbox=Rect(x=0, y=22, w=100, h=0), speaker=None, source_blocks=(1,))
    assert _group_rejection_reason(a, b, params) == "length"
    assert _group_rejection_reason(a, b, params, ignore_length=True) == "height"


def test_k21_uzunluk_ve_genislik_sifir_miras_yok() -> None:
    """`b.bbox.w == 0` (yozlasmis, K16) AYNI ANDA uzunluk siniri da
    asiliyor. Orijinal cagri "length"; `ignore_length=True` "width"
    doner."""
    params = get_params(OcrPreset.DIALOGUE)
    a = _Item(text="x" * 150, bbox=Rect(x=0, y=0, w=100, h=20), speaker="Ada", source_blocks=(0,))
    b = _Item(text="y" * 150, bbox=Rect(x=0, y=22, w=0, h=20), speaker=None, source_blocks=(1,))
    assert _group_rejection_reason(a, b, params) == "length"
    assert _group_rejection_reason(a, b, params, ignore_length=True) == "width"


def test_k21_uzunluk_ve_yetersiz_yatay_ortusme_miras_yok() -> None:
    """`b` dikeyde YAKIN (gap kucuk) ama yatayda TAMAMEN farkli bir
    konumda (ortusme yok) -- AYNI ANDA uzunluk siniri da asiliyor.
    Orijinal cagri "length"; `ignore_length=True` "overlap" doner."""
    params = get_params(OcrPreset.DIALOGUE)
    a = _Item(text="x" * 150, bbox=Rect(x=0, y=0, w=100, h=20), speaker="Ada", source_blocks=(0,))
    b = _Item(text="y" * 150, bbox=Rect(x=300, y=22, w=100, h=20), speaker=None, source_blocks=(1,))
    assert _group_rejection_reason(a, b, params) == "length"
    assert _group_rejection_reason(a, b, params, ignore_length=True) == "overlap"


def test_k21_uzunluk_ve_farkli_konusmaci_reason_speaker_olur_length_degil() -> None:
    """`b` KENDI (FARKLI) bir etiketle geliyor -- metinler de
    `max_group_chars`'i asiyor (301 karakter). Konusmaci kontrolu HER
    ZAMAN uzunluktan ONCE calisir (K9/K15, K21 ile DEGISMEDI): reason
    dogrudan "speaker" olur, "length" YOLUNA hic GIRILMEZ -- bu yuzden
    `_group`'un K21 miras kontrolu (`reason == "length"`) bu ciftte HIC
    TETIKLENMEZ, ayri bir `ignore_length` kontrolune bile gerek kalmaz."""
    params = get_params(OcrPreset.DIALOGUE)
    a = _Item(text="x" * 150, bbox=Rect(x=0, y=0, w=100, h=20), speaker="Ada", source_blocks=(0,))
    b = _Item(text="y" * 150, bbox=Rect(x=0, y=22, w=100, h=20), speaker="Efe", source_blocks=(1,))
    assert _group_rejection_reason(a, b, params) == "speaker"


# --- Uctan uca: `normalize()` uzerinden, sef_karari-tur4.md/feedback-C.md --
# ornegiyle BIREBIR ayni sinif bilesik senaryo -----------------------------


def test_k21_bilesik_sinirda_gecmis_hatali_miras_artik_yok() -> None:
    """sef_karari-tur4.md / feedback-C.md ornegiyle BIREBIR ayni sinif:
    "Ada:" etiketini YAKIN bir govde blogu takip ediyor (etiketle
    gruplanir), ardindan GERCEK bir geometrik kopus (1000px asagida)
    OLAN, AYNI ZAMANDA (etiketli blokla birlikte) uzunluk sinirini da
    asan bir govde blogu geliyor. TUR 3'te (K19, duzeltme oncesi) bu
    kuyruk YANLISLIKLA "Ada"yi MIRAS ALIYORDU (kod "length" reason'ina
    rastladigi icin geometrik kopusu hic GORMEDEN); K21 SONRASI kuyruk
    `speaker=None` KALIR (gercek kopus GORULUR)."""
    etiket = blk("Ada:", 10, 0)
    govde1 = blk("x" * 150, 10, 22)
    # bilesik: HEM uzunluk (150+1+150=301 > cap=280) HEM buyuk dikey bosluk
    govde2 = blk("y" * 150, 10, 22 + 20 + 1000)
    out = normalize([etiket, govde1, govde2], OcrPreset.DIALOGUE)
    assert len(out) == 2
    assert out[0].speaker == "Ada"
    assert out[0].text == "x" * 150
    assert out[1].speaker is None  # K21: bilesik sinir -- miras YOK
    assert out[1].text == "y" * 150


def test_k21_bilesik_sinirda_yukseklik_sifir_ile_normalize_uzerinden_miras_yok() -> None:
    """Ayni bilesik durum, geometrik kopus yerine YOZLASMIS bbox
    (`h=0`, K16) ile -- uctan uca `normalize()` uzerinden de K21'in
    dogru calistigini dogrular (sadece dusuk seviye `_group_rejection_
    reason` degil)."""
    etiket = blk("Ada:", 10, 0)
    govde1 = blk("x" * 150, 10, 22)
    govde2 = blk("y" * 150, 10, 44, h=0)
    out = normalize([etiket, govde1, govde2], OcrPreset.DIALOGUE)
    assert len(out) == 2
    assert out[0].speaker == "Ada"
    assert out[1].speaker is None  # K21: uzunluk + h=0 bilesigi -- miras YOK


def test_k21_zincirde_her_bolunme_noktasi_kendi_sebebine_gore_degerlendirilir() -> None:
    """Uc parcaya bolunen bir zincirde IKI bolunme noktasi var ve HER
    BIRI KENDI sebebine gore degerlendiriliyor -- ayni zincirde biri
    MIRAS ALIYOR biri ALMIYOR:

        etiket "Ada:" + govde1 (yakin, etiketle gruplanir)
        govde1 -> govde2: SADECE uzunluk asiliyor (geometri SIKI)
                           -> 1. bolunme, MIRAS VAR (K21: tek engel uzunluk)
        govde2 -> govde3: uzunluk VE buyuk dikey bosluk AYNI ANDA
                           -> 2. bolunme, MIRAS YOK (K21: bilesik sinir)

    Ikinci bolunmenin MIRAS ALMAMASI, ilk bolunmede MIRAS ALINMIS
    OLMASINDAN etkilenmiyor -- her `_group_rejection_reason` cagrisi
    SADECE kendi cifti degerlendirir (K21 kok sebep: eski kod da her
    cifti ayri degerlendiriyordu, hata REASON'IN kendisindeydi, cagri
    sirasinda degil)."""
    etiket = blk("Ada:", 10, 0)
    govde1 = blk("x" * 150, 10, 22)  # etiketle SIKI gruplanir (kisa gap)
    govde2 = blk("y" * 150, 10, 44)  # govde1'e SIKI (gap=2) -- SADECE uzunluk asiyor
    govde3 = blk("z" * 150, 10, 44 + 20 + 1000)  # govde2'den 1000px asagida -- bilesik
    out = normalize([etiket, govde1, govde2, govde3], OcrPreset.DIALOGUE)
    assert len(out) == 3
    assert out[0].speaker == "Ada"
    assert out[0].text == "x" * 150
    assert out[1].speaker == "Ada"  # K21: 1. bolunme -- SADECE uzunluk -- MIRAS VAR
    assert out[1].text == "y" * 150
    assert out[2].speaker is None  # K21: 2. bolunme -- bilesik -- MIRAS YOK
    assert out[2].text == "z" * 150


# ---------------------------------------------------------------------------
# --- TUR 5 (duzeltme turu) -- K23-K27 regresyon/denetim testleri ----------
# ---------------------------------------------------------------------------
# Kaynak: `.agents/tasks/T-004/sef_karari-tur5.md`. Tur 4'te implementer
# K21/K22'yi DOGRU uyguladi ve sef DOGRULADI -- ama bu turde ILK KEZ
# devreye alinan KARAR KIRMIZI TAKIMI sefin KARARLARINDA (kodun kendisinde
# DEGIL) 12 bulgu cikardi, UCU yuksek siddetli. Sef ucunu de kendi eliyle
# yeniden uretti ve DOGRULADI. BES YENI karar: K23 (DEGISMEZ -- miras
# BOLUMLEMEYI degistiremez), K24 (K21'in TEK gecerli ifadesi -- "bu cift"
# grubun KUYRUGUDUR, birlesik bbox DEGIL), K25 (secenek 1 zorunlu --
# REGRESYON kanitidir, mevcut TUM K21 testlerinin degismeden gecmesiyle
# ZATEN saglanir, burada AYRICA test edilmez), K26 (K22'nin olgusal
# hatasi -- ALTISI DA uyumluluk formu) ve K27 (`menu` acikca kapsam disi).


# --- K23 -- DEGISMEZ: miras acik/kapali BOLUMLEME BIREBIR ayni ----------


_K23_SPEAKER_POOL = ("Ada", "Efe", "勇者", "王女")
_K23_BODY_ALPHABET = "xyzabc" "あいう" "가나다" "123"


def _k23_general_random_blocks(rng: Random, preset: OcrPreset) -> list[TextBlock]:
    """K23 fuzz denetiminin GENEL (yapisiz) uretici -- etiketli (ASCII VE
    fullwidth ayirac) VE etiketsiz govde bloklarinin, SIKI/KOPUK dikey
    boslugun, VE yozlasmis (sifir/negatif `w`/`h`) bbox'larin bir
    KARISIMI. Metin uzunlugu bazen `preset`in `max_group_chars`'ina
    KASITLI YAKIN secilir. `y` HER ZAMAN artan uretilir (okuma sirasi);
    liste SONRA KARISTIRILIR (orijinal indeks sirasindan BAGIMSIZLIGI da
    sinamak icin) -- `normalize` girdiyi KENDISI `(y, x)`'e gore sirali."""
    p = get_params(preset)
    n = rng.randint(0, 8)
    blocks: list[TextBlock] = []
    y = 0
    for _ in range(n):
        y += rng.choice([2, 4, 8, 16, 30, 60, 150, 900])
        roll = rng.random()
        if roll < 0.12:
            text = f"{rng.choice(_K23_SPEAKER_POOL)}:"
        elif roll < 0.20:
            text = f"{rng.choice(_K23_SPEAKER_POOL)}："
        else:
            length = rng.choice([3, 10, 40, 80, max(1, p.max_group_chars - 10), p.max_group_chars + 20])
            text = rng.choice(_K23_BODY_ALPHABET) * length
        w = rng.choice([100, 300, 0, -10])
        h = rng.choice([20, 30, 0, -5])
        x = rng.choice([0, 10, 50])
        blocks.append(
            TextBlock(
                text=text,
                bbox=Rect(x=x, y=y, w=w, h=h, monitor_index=0, dpi_scale=1.0),
                confidence=rng.uniform(0.0, 1.0),
            )
        )
    rng.shuffle(blocks)
    return blocks


def _k23_targeted_boundary_blocks(rng: Random, preset: OcrPreset) -> list[TextBlock]:
    """K23 fuzz denetiminin HEDEFLI (B1'in YAPISINI tasiyan, sayisal
    parametreleri RASTGELE) uretici -- "etiket + govde1 + govde2
    (etiketsiz, UZUNLUK sinirini govde1 ile BIRLIKTE asiyor -- SADECE
    uzunluk, SIKI geometri) + govde3 (KENDI etiketiyle, RASTGELE ayni VEYA
    farkli konusmaci adi)" kalibi -- B1'in (sef_karari-tur5.md) TAM OLARAK
    yakaladigi sizinti sinifidir: govde2 miras ALABILIR (govde1'den) ve
    ARDINDAN govde3'un KENDI etiketiyle GELMESI, mirasin bir SONRAKI
    gruplama kararina SIZIP SIZMADIGINI dogrudan sinar. GENEL (yapisiz)
    uretici bu KOMBINASYONU rastgele YAKALAMA olasiligi COK dusuk oldugu
    icin (birden fazla kosulun AYNI ANDA tutmasi gerekir) bu YAPILI
    uretici AYRICA (bkz. `_k23_random_blocks`, %50 karisim) eklendi --
    `test_k23_miras_acik_kapali_bolumleme_degismezi_fuzz`'in GERCEKTEN
    bu hata SINIFINI YAKALAYABILDIGI, KIRMIZI FAZDA (evidence/
    pytest-red-r5.txt) 959/1875 farkla AYRICA dogrulandi."""
    p = get_params(preset)
    cap = p.max_group_chars
    name = rng.choice(_K23_SPEAKER_POOL)
    other = name if rng.random() < 0.6 else rng.choice(_K23_SPEAKER_POOL)
    l1 = rng.randint(max(1, cap // 3), max(1, cap - 5))
    l2 = rng.randint(max(1, cap // 3), max(1, cap - 5))
    l3 = rng.randint(5, max(5, cap - l2 - 5)) if rng.random() < 0.7 else rng.randint(5, cap)
    gap = rng.choice([2, 2, 4, 10])  # cogunlukla SIKI -- uzunluk TEK engel olsun
    ayirac = ":" if rng.random() < 0.7 else "："
    y = 0
    etiket = TextBlock(text=f"{name}{ayirac}", bbox=Rect(10, y, 300, 20), confidence=0.9)
    y += 20 + gap
    b1 = TextBlock(
        text=rng.choice(_K23_BODY_ALPHABET) * l1, bbox=Rect(10, y, 300, 20), confidence=0.9
    )
    y += 20 + gap
    b2 = TextBlock(
        text=rng.choice(_K23_BODY_ALPHABET) * l2, bbox=Rect(10, y, 300, 20), confidence=0.9
    )
    y += 20 + gap
    b3 = TextBlock(
        text=f"{other}{ayirac} " + rng.choice(_K23_BODY_ALPHABET) * l3,
        bbox=Rect(10, y, 300, 20),
        confidence=0.9,
    )
    blocks = [etiket, b1, b2, b3]
    rng.shuffle(blocks)
    return blocks


def _k23_random_blocks(rng: Random, preset: OcrPreset) -> list[TextBlock]:
    """K23 fuzz denetiminin GIRDI ureticisi -- %50 GENEL (yapisiz,
    `_k23_general_random_blocks`), %50 HEDEFLI (B1'in yapisini tasiyan,
    `_k23_targeted_boundary_blocks`) karisim. Ikisi de sabit-tohumlu
    `rng`'den KENDI rastgeleligini ceker -- cagiri sirasi DETERMINISTIKTIR."""
    if rng.random() < 0.5:
        return _k23_targeted_boundary_blocks(rng, preset)
    return _k23_general_random_blocks(rng, preset)


def test_k23_miras_acik_kapali_bolumleme_degismezi_fuzz() -> None:
    """K23 DEGISMEZ, ZORUNLU makine denetimi (sef_karari-tur5.md): sabit
    tohum, >=2000 (burada 2500) rastgele girdi, DORT on ayarin HEPSI,
    yozlasmis geometri DAHIL -- `_normalize_impl(..., apply_inheritance=
    True)` ile `..., apply_inheritance=False)`'nin URETTIGI BOLUMLEME
    (`source_blocks` dizisi) VE `text`/`bbox`/`placeholders`/segment
    SAYISI **TEK BIR farkla bile** testi KIRAR; miras kararindan SADECE
    `speaker` alaninin degismesine IZIN VERILIR."""
    rng = Random(20260910)
    presets = (OcrPreset.DIALOGUE, OcrPreset.MENU, OcrPreset.TOOLTIP, OcrPreset.SUBTITLE)
    n_denenen = 2500
    n_farkli = 0
    ilk_fark: str | None = None
    for i in range(n_denenen):
        preset = presets[i % len(presets)]
        blocks = _k23_random_blocks(rng, preset)
        with_inherit = _normalize_impl(blocks, preset, apply_inheritance=True)
        without_inherit = _normalize_impl(blocks, preset, apply_inheritance=False)
        fark_bulundu = False
        if len(with_inherit) != len(without_inherit):
            fark_bulundu = True
            aciklama = f"segment SAYISI farkli ({len(with_inherit)} != {len(without_inherit)})"
        else:
            aciklama = ""
            for a, b in zip(with_inherit, without_inherit):
                if (a.text, a.bbox, a.placeholders, a.source_blocks) != (
                    b.text,
                    b.bbox,
                    b.placeholders,
                    b.source_blocks,
                ):
                    fark_bulundu = True
                    aciklama = f"source_blocks {a.source_blocks} != {b.source_blocks} (veya text/bbox/placeholders)"
                    break
        if fark_bulundu:
            n_farkli += 1
            if ilk_fark is None:
                ilk_fark = f"iterasyon {i} (preset={preset.value}): {aciklama}"
    assert n_denenen >= 2000
    assert n_farkli == 0, (
        f"K23 DEGISMEZI ihlal edildi -- {n_farkli}/{n_denenen} girdide bolumleme "
        f"miras acik/kapali FARKLI cikti. Ilk fark: {ilk_fark}"
    )


def test_k23_kendi_etiketiyle_gelen_kuyruk_mirastan_dolayi_yanlislikla_birlesmiyor() -> None:
    """B1 (yuksek siddetli, sef_karari-tur5.md -- kirmizi takim buldu, sef
    kendi eliyle yeniden uretti): tur 4'un mekanizmasinda miras, MUTE
    EDILMIS `speaker` degerini bir SONRAKI gruplama kararina GIRDI
    yapiyordu -- kendi `Ada:` etiketiyle gelen YENI bir replik (govde3),
    SADECE onceki (miras yoluyla "Ada" GORUNEN) segmentle AYNI ada sahip
    OLDUGU icin (X/X -> evet) YANLISLIKLA onun kuyruguna YAPISIYORDU:

        VARYANT A (tur 4, HATALI): speaker='Ada' src=(0,1); speaker='Ada' src=(2,3)  <- b2/b3 BIRLESTI
        VARYANT B (tur 5, DOGRU):  speaker='Ada' src=(0,1); speaker='Ada' src=(2,);  speaker='Ada' src=(3,)

    b2<->b3 GEOMETRISI/METNI iki varyantta AYNI -- TEK fark ONCEKI sinirin
    (govde2'nin) miras kararinin SONRAKI karara (govde2 vs govde3) SIZIP
    SIZMAMASIDIR. Tur 5 SONRASI 3 AYRI segment (VARYANT B) -- govde2
    GORUNUMDE "Ada"yi miras alsa da, BOLUMLEME karari onun OZGUN (None)
    speaker'ina gore ZATEN verilmis, GERIYE degismiyor."""
    etiket = blk("Ada:", 10, 0)
    govde1 = blk("x" * 150, 10, 22)  # etiketle SIKI gruplanir
    govde2 = blk("y" * 150, 10, 44)  # govde1'e SIKI -- govde1+govde2 DIALOGUE cap'ini (280) asar (SADECE uzunluk)
    govde3 = blk("Ada: " + "z" * 50, 10, 66)  # KENDI etiketiyle -- govde2+govde3 cap ICINDE kalir
    out = normalize([etiket, govde1, govde2, govde3], OcrPreset.DIALOGUE)
    assert len(out) == 3  # VARYANT B -- b2/b3 AYRI kalir (VARYANT A'da 2 olurdu, BIRLESIRLERDI)
    assert [s.source_blocks for s in out] == [(0, 1), (2,), (3,)]
    assert out[0].speaker == "Ada"
    assert out[1].speaker == "Ada"  # miras -- SADECE GORUNUM
    assert out[2].speaker == "Ada"  # KENDI etiketi -- miras DEGIL
    assert out[0].text == "x" * 150
    assert out[1].text == "y" * 150  # govde3 ile BIRLESMEDI
    assert out[2].text == "z" * 50


def test_k23_invariant_b1_senaryosunda_bolumleme_ayni_speaker_farkli() -> None:
    """K23 DEGISMEZININ, B1'in TAM senaryosunda (yukaridaki test) DOGRUDAN
    denetimi: `apply_inheritance=True`/`False` AYNI bolumlemeyi (`source_
    blocks`, `text`) uretir -- SADECE govde2'nin `speaker`'i degisir."""
    etiket = blk("Ada:", 10, 0)
    govde1 = blk("x" * 150, 10, 22)
    govde2 = blk("y" * 150, 10, 44)
    govde3 = blk("Ada: " + "z" * 50, 10, 66)
    blocks = [etiket, govde1, govde2, govde3]
    with_inherit = _normalize_impl(blocks, OcrPreset.DIALOGUE, apply_inheritance=True)
    without_inherit = _normalize_impl(blocks, OcrPreset.DIALOGUE, apply_inheritance=False)
    assert [s.source_blocks for s in with_inherit] == [s.source_blocks for s in without_inherit]
    assert [s.text for s in with_inherit] == [s.text for s in without_inherit]
    assert [s.speaker for s in with_inherit] == ["Ada", "Ada", "Ada"]
    assert [s.speaker for s in without_inherit] == ["Ada", None, "Ada"]


# --- K24 -- K21'in TEK gecerli ifadesi: "bu cift"in sol tarafi KUYRUKTUR -


def test_k24_kuyruk_ile_birlesik_bbox_farkli_sonuc_verir() -> None:
    """K24 (sef_karari-tur5.md): "bu cift"in SOL TARAFI kapanan grubun
    BIRLESIK bbox'i DEGIL, okuma-sirasindaki SON (kuyruk) ogesi olmalidir
    -- aksi halde birlesik kutu, grubun EN ALTA uzanan ogesinin
    `bottom`'unu tasiyip GERCEK boslugu YANLIS (kucuk) OLCEBILIR.

    Kurulum: `current_union` (BIRLESIK, iki ogeden -- biri derin `y=0
    h=500 -> bottom=500`, biri kuyruk `y=10 h=20 -> bottom=30` --
    olusmus, birlesik `bbox` derin ogeninkiyle AYNI) ile `govde_kuyruk`
    (SADECE kuyruk oge, `bottom=30`) AYNI `nxt`e (`y=505`) karsi
    `ignore_length=True` ile sorulunca ZIT sonuc verir."""
    params = get_params(OcrPreset.DIALOGUE)
    govde_kuyruk = _Item(text="b", bbox=Rect(x=10, y=10, w=300, h=20), speaker=None, source_blocks=(1,))
    current_union = _Item(
        text="a b",
        bbox=Rect(x=10, y=0, w=300, h=500),  # union: derin ogeden -- bottom=500, gap DEGIL
        speaker="Ada",
        source_blocks=(0, 1),
    )
    nxt = _Item(text="c", bbox=Rect(x=10, y=505, w=300, h=20), speaker=None, source_blocks=(2,))

    assert current_union.bbox.bottom == 500
    assert _group_rejection_reason(current_union, nxt, params, ignore_length=True) is None  # YANLIS -- gap KUCUK gorunur

    assert govde_kuyruk.bbox.bottom == 30
    assert _group_rejection_reason(govde_kuyruk, nxt, params, ignore_length=True) == "gap"  # DOGRU -- GERCEK kopus


def test_k24_normalize_uzerinden_kuyruk_temelli_kontrol_yanlis_mirasi_onler() -> None:
    """Ayni K24 senaryosu, uctan uca `normalize()` uzerinden: `govde_derin`
    (grubun BASINDA, en alta uzanan oge, `y=0 h=500`) ile `govde_kuyruk`
    (`y=10 h=20`, `govde_derin`in ICINE gomulu ama okuma sirasi SONRAKI)
    SIKI gruplanir; birlikte DIALOGUE cap'ini (280) da asarlar (SADECE
    uzunluk -- birlesik bbox'a gore). `govde3`, BIRLESIK bbox'a (bottom=
    500) gore YAKIN (gap=5, miras ALIRDI) ama KUYRUGA (`govde_kuyruk`,
    bottom=30) gore GERCEKTEN kopuktur (gap=475). K24 sonrasi -- kuyruk
    temelli kontrol -- miras UYGULANMAZ."""
    etiket = blk("Ada:", 10, -25)
    govde_derin = blk("x" * 200, 10, 0, h=500)  # y=0..500 -- grubun EN ALTA uzanan ogesi
    govde_kuyruk = blk("y" * 30, 10, 10, h=20)  # y=10..30 -- govde_derin'e gomulu, okuma sirasi SONRAKI (kuyruk)
    govde3 = blk("z" * 60, 10, 505, h=20)  # birlesik bbox'a gore gap=5 (YAKIN); kuyruga gore gap=475 (KOPUK)
    out = normalize([etiket, govde_derin, govde_kuyruk, govde3], OcrPreset.DIALOGUE)
    assert len(out) == 2
    assert out[0].speaker == "Ada"
    assert out[0].source_blocks == (0, 1, 2)
    assert out[1].speaker is None  # K24: KUYRUK temelli kontrol GERCEK kopusu gorur, miras YOK
    assert out[1].text == "z" * 60


# --- K26 -- K22'nin olgusal hatasi: ALTISI DA uyumluluk formu -----------


@pytest.mark.parametrize(
    ("ch", "beklenen_etiket"),
    [
        ("︕", "<vertical>"),  # U+FE15
        ("︖", "<vertical>"),  # U+FE16
        ("﹖", "<small>"),  # U+FE56
        ("﹗", "<small>"),  # U+FE57
        ("！", "<wide>"),  # U+FF01
        ("？", "<wide>"),  # U+FF1F
    ],
)
def test_k26_alti_karakterin_hepsi_uyumluluk_formu_ve_etiket_dogru(ch: str, beklenen_etiket: str) -> None:
    """K26 (sef_karari-tur5.md): K22'nin "ikisi fullwidth, dordu uyumluluk
    formu" ifadesi OLGUSAL olarak YANLISTI -- "diger" sozcugu fullwidth
    ikilinin uyumluluk formu OLMADIGINI ima ediyordu. Dogrusu: ALTISI DA
    Unicode uyumluluk (compatibility) formudur; `unicodedata.decomposition`
    her birinin basinda ayristirma ETIKETINI (`<...>`) tasir -- bu test
    HER karakterin dogru etikete sahip OLDUGUNU sabitler."""
    assert unicodedata.decomposition(ch).startswith(beklenen_etiket)


def test_k26_alti_karakterin_etiket_dagilimi_iki_iki_iki() -> None:
    """Etiket dagiliminin TAMAMI: 2x `<wide>`, 2x `<small>`, 2x
    `<vertical>` -- K22'nin "dordu uyumluluk formu" (yani ikisi DEGIL)
    ifadesinin de YANLIS oldugunu sabitler (dagilim 2/2/2'dir, 2/4 degil)."""
    chars = ["︕", "︖", "﹖", "﹗", "！", "？"]
    etiketler = sorted(unicodedata.decomposition(ch).split()[0] for ch in chars)
    assert etiketler == sorted(["<vertical>", "<vertical>", "<small>", "<small>", "<wide>", "<wide>"])
    for ch in chars:
        assert unicodedata.decomposition(ch) != ""  # ALTISI DA uyumluluk formu -- bos decomposition YOK


# --- K27 -- `menu` K19/K21/K23/K24'un KAPSAMI DISINDA, acikca -----------


def test_k27_dialogue_uzunluk_bolunmesinde_miras_calisir() -> None:
    """Gruplayan on ayar (dialogue): uzunluk-tek-engelli bolunmede miras
    CALISIR (K19/K21/K23 devrede) -- `menu` ile karsilastirmali okumak
    icin bkz. `test_k27_menu_gruplama_yok_miras_kavrami_yok`."""
    etiket = blk("Ada:", 10, 0)
    govde1 = blk("x" * 150, 10, 22)
    govde2 = blk("y" * 150, 10, 44)  # govde1+govde2 DIALOGUE cap'ini (280) asar
    out = normalize([etiket, govde1, govde2], OcrPreset.DIALOGUE)
    assert len(out) == 2
    assert out[1].speaker == "Ada"


def test_k27_tooltip_uzunluk_bolunmesinde_miras_calisir() -> None:
    """Gruplayan on ayar (tooltip): AYNI mekanizma, KENDI cap'iyle."""
    cap = get_params(OcrPreset.TOOLTIP).max_group_chars
    etiket = blk("Ada:", 10, 0)
    govde1 = blk("x" * (cap - 20), 10, 22)
    govde2 = blk("y" * 40, 10, 44)
    out = normalize([etiket, govde1, govde2], OcrPreset.TOOLTIP)
    assert len(out) == 2
    assert out[1].speaker == "Ada"


def test_k27_subtitle_uzunluk_bolunmesinde_miras_calisir() -> None:
    """Gruplayan on ayar (subtitle): AYNI mekanizma, KENDI cap'iyle."""
    cap = get_params(OcrPreset.SUBTITLE).max_group_chars
    etiket = blk("Ada:", 10, 0)
    govde1 = blk("x" * (cap - 20), 10, 22)
    govde2 = blk("y" * 40, 10, 44)
    out = normalize([etiket, govde1, govde2], OcrPreset.SUBTITLE)
    assert len(out) == 2
    assert out[1].speaker == "Ada"


def test_k27_menu_gruplama_yok_miras_kavrami_yok() -> None:
    """K27: `menu`'de `should_group=False` -> `_group` HIC cagirilmaz --
    K19/K21/K23/K24 TANIMSIZDIR. AYNI "etiket + govde1 (SIKI) + govde2
    (etiketsiz)" fixture'u -- diger UC on ayarda govde2 MIRAS alirken
    (yukaridaki uc test), `menu`'de govde2 KENDI (miras ALMAMIS, OZGUN)
    `None` speaker'iyla AYRI bir segment olarak kalir -- gruplama
    olmadigi icin "uzunluk yuzunden bolunme" kavraminin KENDISI yoktur."""
    etiket = blk("Ada:", 10, 0)
    govde1 = blk("x" * 30, 10, 22)
    govde2 = blk("y" * 30, 10, 44)
    out = normalize([etiket, govde1, govde2], OcrPreset.MENU)
    assert len(out) == 2  # gruplama YOK -- govde1 VE govde2 AYRI segment
    assert out[0].speaker == "Ada"  # K9 etiket-tasima HALA calisir (gruplamadan BAGIMSIZ)
    assert out[1].speaker is None  # K27: miras KAVRAMI YOK -- "devam" sayilmiyor
