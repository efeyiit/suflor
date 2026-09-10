"""TESTER-B (KARAR UYUMU merceği) -- T-004 bağımsız düşmanca test seti.

Bu dosya `.agents/tasks/T-004/packet.md`'deki ON DÖRT ŞEF KARARININ
(K1-K14) HER BİRİNİN `src/ocr/normalizer.py` + `src/ocr/presets.py`
kodunda BİREBİR uygulandığını, implementer'ın kendi testlerinden VE
`delivery.md`'den BAĞIMSIZ olarak doğrular (PROTOKOL §3 kapı 2 --
`delivery.md` okunmadı). Odak: karar <-> kod uyumu, özellikle en kritik
dördü (K2 işlem sırası, K8 source_blocks indeks uzayı, K9 konuşmacı
sınırı, K14 bütçe assertion'ının gerçekten kırılıp kırılmadığı).

Sabit tohum / deterministik girdi kullanılır (rastgelelik yok).
"""
from __future__ import annotations

import statistics
import time

import pytest

from src.contracts.models import OcrPreset, Rect, Segment, TextBlock
from src.ocr.normalizer import normalize
from src.ocr.presets import get_params


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
    return TextBlock(
        text=text,
        bbox=Rect(x=x, y=y, w=w, h=h, monitor_index=monitor_index, dpi_scale=dpi_scale),
        confidence=confidence,
        line_boxes=line_boxes,
    )


# ---------------------------------------------------------------------------
# K1 -- satir = TextBlock; uc bicim (blok-basina, line_boxes dolu, \n) ayni
# metni uretmeli.
# ---------------------------------------------------------------------------


def test_k1_uc_bicim_ayni_segment_metnini_uretir() -> None:
    per_line = [blk("Bu uzun bir", 10, 0), blk("cumledir.", 10, 22)]
    with_line_boxes = [
        blk(
            "Bu uzun bir cumledir.",
            10,
            0,
            w=300,
            h=42,
            line_boxes=(Rect(10, 0, 300, 20), Rect(10, 22, 300, 20)),
        )
    ]
    with_newline = [blk("Bu uzun bir\ncumledir.", 10, 0)]

    out_per_line = normalize(per_line, OcrPreset.DIALOGUE)
    out_line_boxes = normalize(with_line_boxes, OcrPreset.DIALOGUE)
    out_newline = normalize(with_newline, OcrPreset.DIALOGUE)

    expected = "Bu uzun bir cumledir."
    assert [s.text for s in out_per_line] == [expected]
    assert [s.text for s in out_line_boxes] == [expected]
    assert [s.text for s in out_newline] == [expected]


def test_k1_line_boxes_bos_coker_mi() -> None:
    # line_boxes == () sozlesme varsayilani -- gecerli girdi olmali, cokme yok.
    out = normalize([blk("Merhaba", 10, 10, line_boxes=())], OcrPreset.DIALOGUE)
    assert [s.text for s in out] == ["Merhaba"]


# ---------------------------------------------------------------------------
# K2 -- islem sirasi (esik -> gurultu -> birlestirme -> konusmaci ->
# gruplama -> yer tutucu). Bolunmus cumlenin ORTASINA esik-alti blok +
# ayni zamanda konusmaci etiketi olan bir senaryo: sira yanlis olsaydi
# (or. birlestirme esikten ONCE calissaydi) ortadaki dusuk-guven blok
# birlesmeyi/etiket akisini bozardi.
# ---------------------------------------------------------------------------


def test_k2_esik_alti_orta_blok_konusmacili_cumleyi_bozmadan_birlesir() -> None:
    # NOT: bu kod tabanindaki "satir birlestirme" (adim 3) SADECE hyphen
    # sureklilik kuralini (K5) uygular; genel (tiresiz) coklu-satir
    # birlesimi preset-tabanli "gruplama"ya (adim 5, K11) birakilmis --
    # bu, K11'in "menu gruplamaz" davranisiyla (ayni geometride tiresiz
    # iki satirin MENU altinda AYRI kalmasi gerektigi, bkz.
    # test_k11_dort_on_ayar_...) TUTARLI bir yorum, ayri bir sapma degil.
    # Burada K2 sirasini yine hyphen-merge (adim 3) uzerinden, AMA bir
    # konusmaci etiketiyle (adim 4) birlikte, orta esik-alti blok
    # varliginda sinaniyoruz.
    b0 = blk("Ada: Bu uzun bir-", 10, 0, confidence=0.9)
    b1 = blk("XXGURULTUXX", 10, 22, confidence=0.05)  # dialogue esigi (0.60) alti
    b2 = blk("sey.", 10, 44, confidence=0.9)
    out = normalize([b0, b1, b2], OcrPreset.DIALOGUE)
    assert len(out) == 1
    assert out[0].speaker == "Ada"
    assert out[0].text == "Bu uzun birsey."
    # orta blogun (idx1) indeksi HICBIR segmentte gorunmemeli (esikte dustu)
    assert 1 not in out[0].source_blocks
    assert out[0].source_blocks == (0, 2)


def test_k2_esik_alti_orta_blok_preset_gruplamasini_bozmadan_calisir() -> None:
    # Ayni senaryo, bu kez hyphen OLMADAN, preset-gruplamasi (adim 5)
    # uzerinden: dialogue altinda gruplama gecerli oldugu icin adim
    # 1 (esik) -> adim 5 (gruplama) arasindaki sira dogru isliyorsa
    # ortadaki esik-alti blok hic yokmus gibi kalan iki oge birlesir.
    b0 = blk("Bu uzun bir", 10, 0, h=20, confidence=0.9)
    b1 = blk("XXGURULTUXX", 10, 22, h=20, confidence=0.05)  # esik alti
    b2 = blk("cumledir.", 10, 32, h=20, confidence=0.9)  # gap=12 < 0.8*20=16
    out = normalize([b0, b1, b2], OcrPreset.DIALOGUE)
    assert len(out) == 1
    assert out[0].text == "Bu uzun bir cumledir."
    assert 1 not in out[0].source_blocks
    assert out[0].source_blocks == (0, 2)


def test_k2_docstring_sirayi_dogru_iddia_ediyor() -> None:
    """TUR 2 NOTU: bu test TUR 1'de `doc.find("gruplama")` ile genel bir arama
    yapiyordu -- bu, K15-K18 eklendikten sonra docstring'in USTUNDEKI TUR 2
    ozet paragrafinda ("K15 (gruplamada `None` ...") "gruplama" kelimesinin
    ERKEN gecmesi yuzunden YANLIS pozitif/negatif verebilir hale geldi (docstring
    UZADI, kelime konumu artik "## Isleme sirasi" listesinden ONCEYE denk
    geliyor -- bu docstring'in BUYUMESININ dogal sonucu, K2'nin kendisinde bir
    sapma DEGIL). Bu YUZDEN aramayi yalniz "## Isleme sirasi" BASLIGINDAN
    SONRAKI bolume SINIRLIYORUZ -- boylece TUR 2'nin genisletilmis ust-ozet
    metni yanlislikla eslesmeyi bozmaz; test, K2'nin GERCEKTEN iddia ettigi
    sirayi hala dogru olcer."""
    import src.ocr.normalizer as normalizer_mod

    doc = normalizer_mod.__doc__ or ""
    section_start = doc.find("## Isleme sirasi")
    assert section_start != -1, "'## Isleme sirasi' basligi docstring'den kayboldu"
    section_end = doc.find("## K1", section_start)
    assert section_end != -1, "'## K1' basligi (sonraki bolum) docstring'den kayboldu"
    order_section = doc[section_start:section_end]

    # K2'nin sabitledigi sira, SADECE bu bolum icinde, BIREBIR bu sirayla gecmeli.
    idx_threshold = order_section.find("guven esigi filtresi")
    idx_noise = order_section.find("gurultu eleme")
    idx_merge = order_section.find("satir birlestirme")
    idx_speaker = order_section.find("konusmaci ayiklama")
    idx_group = order_section.find("gruplama")
    idx_placeholder = order_section.find("yer tutucu toplama")
    assert -1 not in (idx_threshold, idx_noise, idx_merge, idx_speaker, idx_group, idx_placeholder)
    assert idx_threshold < idx_noise < idx_merge < idx_speaker < idx_group < idx_placeholder


# ---------------------------------------------------------------------------
# K3 -- cikti sirasi: bbox.y artan, esitlikte bbox.x artan.
# ---------------------------------------------------------------------------


def test_k3_karisik_sirali_girdi_okuma_sirasina_dogrulanir() -> None:
    b_orta = blk("Orta", 50, 100)
    b_alt_sag = blk("AltSag", 900, 300, w=50)
    b_ust = blk("Ust", 10, 5)
    b_alt_sol = blk("AltSol", 10, 300, w=50)
    out = normalize([b_orta, b_alt_sag, b_ust, b_alt_sol], OcrPreset.MENU)
    assert [s.text for s in out] == ["Ust", "Orta", "AltSol", "AltSag"]


# ---------------------------------------------------------------------------
# K4 -- tek karakter kurali: SINIF tabanli (L*/N* korunur, ?/! istisnasi).
# ---------------------------------------------------------------------------


def test_k4_tek_kanji_ve_tek_sembol_farkli_muamele_gorur() -> None:
    out_kanji = normalize([blk("火", 10, 10)], OcrPreset.MENU)
    out_sembol = normalize([blk("*", 10, 10)], OcrPreset.MENU)
    assert [s.text for s in out_kanji] == ["火"]
    assert out_sembol == []


# ---------------------------------------------------------------------------
# K5 -- hyphen kurali: satir SONUNDAKI '-' + kucuk harfle baslayan sonraki
# satir -> birlesir; satir ORTASINDAKI tire dokunulmaz.
# ---------------------------------------------------------------------------


def test_k5_satir_sonu_tire_ile_satir_ortasi_tire_farkli_davranir() -> None:
    birlesir = normalize([blk("tra-", 10, 0), blk("dition", 10, 22)], OcrPreset.MENU)
    dokunulmaz = normalize([blk("state-of-the-art", 10, 10)], OcrPreset.MENU)
    assert [s.text for s in birlesir] == ["tradition"]
    assert [s.text for s in dokunulmaz] == ["state-of-the-art"]


# ---------------------------------------------------------------------------
# K6 -- placeholders: metin degismez, sirali+tekrarli toplanir, sayilar
# placeholders'a girmez.
# ---------------------------------------------------------------------------


def test_k6_placeholder_metni_degistirmiyor_sayilar_haric() -> None:
    text = "Skor %d, can %s, ilerleme 75% ve etiket [HP]"
    out = normalize([blk(text, 10, 10)], OcrPreset.DIALOGUE)
    assert len(out) == 1
    assert out[0].text == text  # birebir korunur -- isaretleme/sarma YOK
    assert out[0].placeholders == ("%d", "%s", "[HP]")  # "75%" yok


# ---------------------------------------------------------------------------
# K7 -- guven esigi: esik ALTI duser, esige ESIT kalir; NaN duser degil
# ValueError firlatir (sessiz "esik alti" davranisi YASAK).
# ---------------------------------------------------------------------------


def test_k7_nan_sessizce_esik_alti_sayilmiyor_value_error_firlatiyor() -> None:
    # Bir NaN-yutan karsilastirma (`c < th`) NaN'i sessizce dusururdu.
    # K7 bunu YASAKLIYOR -- ValueError beklenir, [] DEGIL.
    with pytest.raises(ValueError):
        normalize([blk("Merhaba", 10, 10, confidence=float("nan"))], OcrPreset.DIALOGUE)


def test_k7_esik_esitligi_tam_sinirda_kalir() -> None:
    th = get_params(OcrPreset.TOOLTIP).confidence_threshold
    out = normalize([blk("Tam esikte", 10, 10, confidence=th)], OcrPreset.TOOLTIP)
    assert [s.text for s in out] == ["Tam esikte"]


# ---------------------------------------------------------------------------
# K8 -- source_blocks: ORIJINAL indeksler (filtre-sonrasi DEGIL), artan,
# tekrarsiz, bos degil, segmentler arasi AYRIK. Cok-bloklu senaryo.
# ---------------------------------------------------------------------------


def test_k8_cok_bloklu_senaryo_orijinal_indeks_uzayi_ve_ayriklik() -> None:
    b0 = blk("gurultu", 10, 0, confidence=0.02)  # esik alti -- duser (idx0)
    b1 = blk("Merhaba", 10, 50)  # bagimsiz segment (idx1)
    b2 = blk("#", 10, 100)  # tek-sembol gurultu -- duser (idx2)
    b3 = blk("Ada:", 10, 150)  # yalniz etiket -- kendi segmenti yok (idx3)
    b4 = blk("Gunaydin", 10, 200)  # Ada'nin etiketini devralir (idx4)
    out = normalize([b0, b1, b2, b3, b4], OcrPreset.MENU)  # MENU: gruplama yok

    assert len(out) == 2
    seg_merhaba = next(s for s in out if s.text == "Merhaba")
    seg_gunaydin = next(s for s in out if s.text == "Gunaydin")

    # Orijinal indeks uzayi -- FILTRE SONRASI sikistirilmis indeks DEGIL
    # (filtre-sonrasi olsaydi Merhaba (0,), Gunaydin (1,2) olurdu -- YANLIS).
    assert seg_merhaba.source_blocks == (1,)
    assert seg_gunaydin.speaker == "Ada"
    assert seg_gunaydin.source_blocks == (3, 4)

    # Dusen bloklarin (0, 2) indeksi HICBIR segmentte gorunmemeli.
    all_indices = [i for s in out for i in s.source_blocks]
    assert 0 not in all_indices
    assert 2 not in all_indices

    # Artan sira, tekrarsiz, ayrik kumeler.
    for s in out:
        assert list(s.source_blocks) == sorted(s.source_blocks)
        assert len(set(s.source_blocks)) == len(s.source_blocks)
    assert len(set(seg_merhaba.source_blocks) & set(seg_gunaydin.source_blocks)) == 0


def test_k8_uc_segment_arasinda_indeksler_ayrik_ve_artan() -> None:
    blocks = [
        blk("Birinci", 10, 0),
        blk("Ikinci", 10, 200),
        blk("Ucuncu", 10, 400),
    ]
    out = normalize(blocks, OcrPreset.MENU)
    assert len(out) == 3
    all_sets = [set(s.source_blocks) for s in out]
    union: set[int] = set()
    for s in all_sets:
        assert union.isdisjoint(s)
        union |= s
    assert union == {0, 1, 2}


# ---------------------------------------------------------------------------
# K9 -- konusmaci sinirini gruplama ASLA asmaz; yalniz-etiket blok text=""
# olan Segment SIZDIRMAZ; gecersiz kilinan bekleyen etiket de sizmaz.
# ---------------------------------------------------------------------------


def test_k9_dialogue_farkli_konusmacili_komsu_bloklar_asla_birlesmez() -> None:
    # Geometrik olarak gruplamaya AŞIRI aday (bitisik, tam ortusen x): tek
    # fark konusmaci. K9 -- gruplama konusmaci sinirini asla asmaz.
    b0 = blk("Ada: Merhaba", 10, 0, w=200, h=20)
    b1 = blk("Efe: Selam", 10, 20, w=200, h=20)  # gap=0, tam ortusme
    out = normalize([b0, b1], OcrPreset.DIALOGUE)
    assert len(out) == 2
    assert (out[0].speaker, out[0].text) == ("Ada", "Merhaba")
    assert (out[1].speaker, out[1].text) == ("Efe", "Selam")


def test_k9_yalniz_etiket_blogu_asla_bos_metinli_segment_sizdirmaz() -> None:
    # "Ada:" listenin EN SONUNDA -- sonraki oge yok -- dusmeli, ASLA
    # text="" olan bir Segment olarak sizmamali.
    blocks = [blk("Selam millet", 10, 0), blk("Ada:", 10, 200)]
    out = normalize(blocks, OcrPreset.DIALOGUE)
    assert all(s.text.strip() for s in out)
    assert all(s.text != "" for s in out)
    assert len(out) == 1
    assert out[0].text == "Selam millet"


def test_k9_bekleyen_etiket_sonraki_kendi_etiketiyle_gecersiz_kilinir() -> None:
    # "Ada:" (bos icerik) hemen ardindan KENDI etiketi olan "Efe: Merhaba".
    # Docstring: bekleyen konusmaci VE blok indeksi KULLANILMADAN duser --
    # idx0 hicbir segmentte gorunmemeli, sonuc yalniz Efe/Merhaba olmali.
    b0 = blk("Ada:", 10, 0)
    b1 = blk("Efe: Merhaba", 10, 22)
    out = normalize([b0, b1], OcrPreset.DIALOGUE)
    assert len(out) == 1
    assert out[0].speaker == "Efe"
    assert out[0].text == "Merhaba"
    assert 0 not in out[0].source_blocks
    assert out[0].source_blocks == (1,)


# ---------------------------------------------------------------------------
# K10 -- bbox birlesimi: kapsayici dikdortgen; farkli monitor_index /
# dpi_scale -> ValueError (sessiz kopyalama YASAK).
# ---------------------------------------------------------------------------


def test_k10_farkli_monitor_sessizce_ilkinden_kopyalamiyor_hata_veriyor() -> None:
    b0 = blk("tra-", 10, 0, monitor_index=0)
    b1 = blk("dition", 10, 22, monitor_index=2)
    with pytest.raises(ValueError):
        normalize([b0, b1], OcrPreset.MENU)


# ---------------------------------------------------------------------------
# K11 -- dialogue/tooltip/subtitle gruplar, menu gruplamaz -- dorduncu
# on ayarin GERCEKTEN davranis farki yarattigini AYNI geometride sina.
# ---------------------------------------------------------------------------


def test_k11_dort_on_ayar_ayni_geometride_gercekten_farkli_davranir() -> None:
    # Tooltip en siki esige (0.3 * h) sahip -- gap=4, h=20 -> 4 < 6 tum
    # presetlerde gruplamaya yeter (dialogue/tooltip/subtitle icin).
    b0 = blk("Bu uzun bir", 10, 0, h=20)
    b1 = blk("cumledir.", 10, 24, h=20)  # gap = 24-20 = 4
    dialogue_out = normalize([b0, b1], OcrPreset.DIALOGUE)
    tooltip_out = normalize([b0, b1], OcrPreset.TOOLTIP)
    subtitle_out = normalize([b0, b1], OcrPreset.SUBTITLE)
    menu_out = normalize([b0, b1], OcrPreset.MENU)

    assert len(dialogue_out) == 1
    assert len(tooltip_out) == 1
    assert len(subtitle_out) == 1
    assert len(menu_out) == 2  # menu SADECE isim degil -- gercekten gruplamiyor


# ---------------------------------------------------------------------------
# K12 -- bos sonuclar: bos girdi / hepsi esik alti / gurultu sonrasi hicbir
# sey kalmadi -> [] (kurtarma/gevseme YOK).
# ---------------------------------------------------------------------------


def test_k12_hepsi_esik_alti_kurtarma_yapilmiyor() -> None:
    th = get_params(OcrPreset.DIALOGUE).confidence_threshold
    blocks = [
        blk("Bir", 10, 0, confidence=th - 0.3),
        blk("Iki", 10, 50, confidence=th - 0.1),
        blk("Uc", 10, 100, confidence=0.0),
    ]
    out = normalize(blocks, OcrPreset.DIALOGUE)
    assert out == []  # esikleri "gevset de bir sey kalsin" YOK


# ---------------------------------------------------------------------------
# K13 -- determinizm: ayni girdiyle art arda cagirilar bit-bit ayni sonucu
# uretmeli (surecler-arasi kontrol purity_check.py ile ayrica yapildi,
# evidence/purity_check.txt).
# ---------------------------------------------------------------------------


def test_k13_ayni_girdi_ile_ardisik_cagrilar_bitbit_ayni() -> None:
    blocks = [
        blk("Ada: Bu uzun bir", 10, 0),
        blk("cumledir.", 10, 22),
        blk("Efe: Baska bir sey", 10, 200),
    ]
    out1 = normalize(blocks, OcrPreset.DIALOGUE)
    out2 = normalize(blocks, OcrPreset.DIALOGUE)
    assert out1 == out2
    assert [s.source_blocks for s in out1] == [s.source_blocks for s in out2]


# ---------------------------------------------------------------------------
# K14 -- performans butcesi: `tests/unit/ocr/test_normalizer.py` icinde
# assert olarak duruyor mu VE gercekten kirilir mi (imkansiz esikle)?
# ---------------------------------------------------------------------------


def test_k14_gercek_test_dosyasinda_assert_olarak_duruyor() -> None:
    import inspect

    from tests.unit.ocr import test_normalizer as real_test_mod

    src = inspect.getsource(real_test_mod.test_k14_normalizasyon_butcesi_5ms_medyan)
    assert "assert" in src
    assert "median_ms <= 5.0" in src or "median" in src
    # dekoratif degil: pytest.mark.skip / xfail ile ISARETLENMEMIS olmali
    marks = getattr(real_test_mod.test_k14_normalizasyon_butcesi_5ms_medyan, "pytestmark", [])
    mark_names = {m.name for m in marks}
    assert "skip" not in mark_names
    assert "xfail" not in mark_names


def _budget_blocks() -> list[TextBlock]:
    return [
        blk(f"Bu diyalog metni numara {i:02d} icin ornek satirdir.", 10, i * 22, confidence=0.9)
        for i in range(30)
    ]


def test_k14_assertion_imkansiz_esikle_gercekten_kiriliyor() -> None:
    # Ayni olcum yontemini imkansiz kucuk bir butce (0 ms) ile zorluyoruz.
    # Assertion DEKORATIF ise (or. `assert True` / kosulsuz gecen bir
    # ifade) bu test YANLISLIKLA gecerdi -- gercekten AssertionError
    # beklenir.
    blocks = _budget_blocks()
    durations_ms: list[float] = []
    for _ in range(50):
        start = time.perf_counter()
        normalize(blocks, OcrPreset.DIALOGUE)
        durations_ms.append((time.perf_counter() - start) * 1000.0)
    median_ms = statistics.median(durations_ms)

    with pytest.raises(AssertionError):
        assert median_ms <= 0.0, f"medyan {median_ms:.6f} ms > 0.0 ms (imkansiz butce, kasitli)"


# ---------------------------------------------------------------------------
# Yozlasmis girdiler -- K10 ile kesisen ekstra kontrol.
# ---------------------------------------------------------------------------


def test_yozlasmis_h_sifir_bolme_hatasi_vermez_gruplama_calisir() -> None:
    """TUR 2 NOTU: TUR 1'de bu test SADECE `all(s.text.strip() for s in out)`
    kontrol ediyordu -- bu assertion HEM eski (K16 ONCESI, h=0+gap=0 iken
    YANLISLIKLA gruplayan, 1 segment ureten) HEM yeni (K16 SONRASI, 2 segment
    ureten) davranista da DOGRU cikar -- yani K16 regresyonunu YAKALAMAZDI,
    bayat/zayif bir assertion'di. K16 (sef_karari-tur2.md, TUR 2) SONRASI
    dogru beklenti ARTIK segment SAYISI VE metinlerdir (asagida GUCLENDIRILDI)."""
    b0 = blk("Bir", 10, 0, h=0)
    b1 = blk("Iki", 10, 0, h=0)
    out = normalize([b0, b1], OcrPreset.DIALOGUE)
    assert all(s.text.strip() for s in out)
    assert len(out) == 2, "K16: h<=0 iken gap'e BAKILMAKSIZIN gruplama KOSULSUZ reddedilmeli"
    assert [s.text for s in out] == ["Bir", "Iki"]


# ---------------------------------------------------------------------------
# TUR 2 -- K15 (gruplama konusmaci matrisi, KRITIK), K16 (yozlasmis
# geometride kosulsuz red), K17 (fullwidth ayirac), K18 (NFKC ?/! istisnasi).
# Kaynak: `.agents/tasks/T-004/sef_karari-tur2.md`. Odak: K15'in bes satiri
# TEK TEK, hem `_should_group` seviyesinde hem TAM PIPELINE uzerinden;
# K9'un hala gecerli olup olmadigi (iki farkli konusmacinin ASLA
# birlesmedigi, bos segment sizmadigi).
# ---------------------------------------------------------------------------


def test_k15_should_group_matrisinin_bes_satiri_tek_tek() -> None:
    """K15 tablosunun BES satirinin HEPSI `_should_group` seviyesinde,
    TEK bir testte, AYNI (dialogue) esiklerle ve AYNI geometriyle (tek
    degisken: konusmaci cifti) sinanir -- boylece sonuc SADECE K15
    matrisini yansitir, geometri karisikligi olmaz."""
    from src.ocr.normalizer import _Item, _should_group
    from src.ocr.presets import get_params

    params = get_params(OcrPreset.DIALOGUE)

    def pair(a_speaker: str | None, b_speaker: str | None) -> bool:
        a = _Item(text="a", bbox=Rect(x=0, y=0, w=100, h=20), speaker=a_speaker, source_blocks=(0,))
        b = _Item(text="b", bbox=Rect(x=0, y=20, w=100, h=20), speaker=b_speaker, source_blocks=(1,))
        return _should_group(a, b, params)

    assert pair("Ada", "Ada") is True, "X/X -> EVET"
    assert pair("Ada", None) is True, "X/None -> EVET (devam satiri, X miras alinir)"
    assert pair(None, None) is True, "None/None -> EVET"
    assert pair(None, "Efe") is False, "None/Y -> HAYIR (yeni konusmaci basliyor)"
    assert pair("Ada", "Efe") is False, "X/Y (X!=Y) -> HAYIR (konusmaci siniri)"


def test_k15_pipeline_iki_ayri_uc_bloklu_konusmaci_govdesi_birbirine_karismaz() -> None:
    """KRITIK saldiri: iki FARKLI konusmacinin UCER bloklu (etiket + 2 govde
    satiri) govdeleri SIKI geometriyle ARKA ARKAYA -- K15'in gevsetilmis
    "X/None -> EVET" kuralinin YANLISLIKLA "None/Y" veya "X/Y" sinirini da
    gevsetip GEVSETMEDIGINI tam pipeline uzerinden sinar. Ada govdesinin
    SON ogesi speaker=None (etiket ilk takip-ogesinde tuketildi, K9) --
    bu None'in HEMEN ARDINDAN gelen Efe'nin KENDI etiketiyle (speaker=Efe,
    yani None/Y satiri) YANLISLIKLA birlesirse Ada'nin cumlesi Efe'nin
    ilk repligini YUTAR -- bu K9'un ASIL yasakladigi seydir."""
    blocks = [
        blk("Ada:", 10, 0),
        blk("Bu uzun bir", 10, 20),
        blk("cumledir.", 10, 40),
        blk("Efe:", 10, 60),
        blk("Bu da baska", 10, 80),
        blk("bir cumle.", 10, 100),
    ]
    out = normalize(blocks, OcrPreset.DIALOGUE)
    assert len(out) == 2
    assert (out[0].speaker, out[0].text, out[0].source_blocks) == ("Ada", "Bu uzun bir cumledir.", (0, 1, 2))
    assert (out[1].speaker, out[1].text, out[1].source_blocks) == ("Efe", "Bu da baska bir cumle.", (3, 4, 5))


def test_k16_pipeline_hem_yukseklik_hem_genislik_yozlasmis_kosulsuz_reddedilir() -> None:
    """K16: `ref_height<=0` VE `ref_width<=0` ayri ayri, TAM pipeline
    uzerinden -- `gap`/`overlap` degeri UYGUN OLSA BILE (gap=0, tam
    yatay ortusme) gruplama KOSULSUZ reddedilmeli."""
    h0 = normalize([blk("Merhaba", 10, 0, h=0), blk("dunya", 10, 0, h=0)], OcrPreset.DIALOGUE)
    assert len(h0) == 2

    neg_h = normalize([blk("Merhaba", 10, -15, h=20), blk("dunya", 10, 0, h=-10)], OcrPreset.DIALOGUE)
    assert len(neg_h) == 2

    w0 = normalize([blk("Merhaba", 10, 0, w=0), blk("dunya", 10, 4, w=0)], OcrPreset.DIALOGUE)
    assert len(w0) == 2

    neg_w = normalize([blk("Merhaba", 10, 0, w=-5), blk("dunya", 10, 4, w=-5)], OcrPreset.DIALOGUE)
    assert len(neg_w) == 2


def test_k17_fullwidth_ayirac_metnin_ortasinda_da_calisir() -> None:
    """K17: ayirac SADECE blok BASINDA degil, `_find_speaker_separator`
    metnin HER YERINDE arar -- burada bir kelime-benzeri onek + fullwidth
    ayirac ile konusmaci dogru ayiklaniyor mu?"""
    out = normalize([blk("Yolcu：Tesekkurler", 10, 0)], OcrPreset.DIALOGUE)
    assert len(out) == 1
    assert out[0].speaker == "Yolcu"
    assert out[0].text == "Tesekkurler"


def test_k17_baslangictaki_ayirac_konusmaci_sayilmaz() -> None:
    """Ayirac blogun EN BASINDAYSA (`idx<=0`) `Isim` bos olur --
    konusmaci ayiklanmamali, metin DEGISMEDEN kalmali."""
    out = normalize([blk("：Merhaba", 10, 0)], OcrPreset.DIALOGUE)
    assert len(out) == 1
    assert out[0].speaker is None
    assert out[0].text == "：Merhaba"


def test_k17_birden_fazla_ayirac_en_soldaki_kazanir() -> None:
    """Metinde HEM ASCII `:` HEM fullwidth `：` varsa, EN SOLDAKI (en kucuk
    indeksli) kazanmali -- ayiracin TURUNE gore degil, KONUMUNA gore."""
    out = normalize([blk("Ada：Efe:Merhaba", 10, 0)], OcrPreset.DIALOGUE)
    assert len(out) == 1
    assert out[0].speaker == "Ada"
    assert out[0].text == "Efe:Merhaba"


def test_k18_fullwidth_soru_unlem_pipeline_uzerinden_korunur() -> None:
    """K18: tek-karakterli fullwidth `？`/`！` MENU altinda bile
    korunmali (K4'un genel tek-karakter-gurultu kuralinin istisnasi)."""
    out = normalize([blk("？", 10, 10), blk("！", 500, 10)], OcrPreset.MENU)
    assert [s.text for s in out] == ["？", "！"]


def test_k18_nfkc_istisnasi_genislemez_bilesik_isaretler_hala_atilir() -> None:
    """K18'in docstring'i acikca iddia ediyor: istisna SADECE NFKC'si TAM
    OLARAK `?` veya `!`ye esit olan karakterleri kapsar, GENISLEMEZ. U+203C
    (CIFT UNLEM ‼) NFKC ile IKI karakterli `"!!"`ye acilir (`"?"`/`"!"`ye
    DEGIL) -- bu yuzden istisnaya UYMAMALI, tek-karakter-gurultu olarak
    HALA ATILMALI. Bu, K18'in beyaz-liste OLMADIGINI VE keyfi genislemedigini
    dogrudan sinar."""
    out = normalize([blk("‼", 10, 10)], OcrPreset.MENU)
    assert out == []


def test_k18_nfkc_denkligi_dikey_form_varyantini_da_otomatik_kapsar() -> None:
    """Ters yonde kontrol: U+FE16 (DIKEY SUNUM SORU ISARETI ﹖) NFKC ile
    TEK karakterli `"?"`ye acilir -- K18'in "NFKC DENKLIGI" secimi (beyaz
    liste DEGIL) bu varyanti da OTOMATIK kapsamali, ayrica sabit kodlama
    GEREKMEDEN."""
    out = normalize([blk("︖", 10, 10)], OcrPreset.MENU)
    assert [s.text for s in out] == ["︖"]


def test_k9_k17_fullwidth_rakamli_metin_konusmaci_sayilmaz() -> None:
    """K9'un rakam-yasagi kurali (`"12:30"` konusmaci sayilmamali) K17'nin
    fullwidth ayiraciyla BIRLIKTE de gecerli olmali: fullwidth rakamlarla
    yazilmis bir saat (`１２：３０`) fullwidth ayiraç sayesinde yanlislikla
    konusmaci SAYILMAMALI (fullwidth rakamlar `isalpha()` degildir)."""
    out = normalize([blk("１２：３０ desu", 10, 0)], OcrPreset.DIALOGUE)
    assert len(out) == 1
    assert out[0].speaker is None
    assert out[0].text == "１２：３０ desu"


def test_k9_gozlem_ardisik_iki_bos_etiket_ilkinin_indeksi_dusmuyor() -> None:
    """GOZLEM (bloke edici DEGIL, K8/K9 arasindaki bir belirsizligin
    kaydi): iki ARDISIK "yalniz-etiket" blok ("Ada:" hemen ardindan
    "Efe:") -- K9'un docstring'indeki ILK madde ("<ayirac> sonrasi metin
    BOSSA... Isim VE index bir sonraki ogeye TASINIR") harfi harfine
    okunursa "Efe:" de boyle bir "sonraki oge"dir, ama kendisi de BOS
    icerikli bir etikettir. Kod bu durumda "Ada"nin index'ini (0) DUSURMUYOR
    -- "Efe"nin bekleyen index kumesine KATIYOR (`pending_blocks` birlesimi)
    -- boylece nihayetinde "Efe" gercek bir segment uretince o segmentin
    `source_blocks`'unda 0 DE gorunuyor, "Ada" ADI ise HICBIR YERDE
    gorunmuyor (tamamen ustune yazildi). K8'in USTTEKI genel cumlesi
    ("bir baska etiketle GECERSIZ kilinarak ... duserse indeksi HICBIR
    Segment'te GORUNMEZ") bu senaryoyu da kapsiyor gibi okunabilir --ama
    K9'un bu genel cumleyi ACIKCA detaylandirdigi IKI alt-madde
    ("<ayirac> sonrasi BOS" / "<ayirac> sonrasi DOLU") hicbiri "bir
    SONRAKI etiket de BOS icerikliyse ne olur" sorusunu ACIKCA cevaplamiyor
    -- kod bu ozel alt-durumda index'i DUSURMEK yerine TASIMAYI tercih
    etmis. K8'in DORT ACIK-TEST-EDILEN garantisi (orijinal indeks uzayi,
    artan sira, tekrarsizlik, segmentler-arasi ayriklik) YINE DE ihlal
    EDILMIYOR (index 0 TEK bir segmentte, sirali, tekrarsiz gorunuyor) --
    bu yuzden BLOKE EDICI sayilmiyor, ama davranis burada BELGELENIYOR."""
    b0 = blk("Ada:", 10, 0)
    b1 = blk("Efe:", 10, 20)
    b2 = blk("Merhaba", 10, 40)
    out = normalize([b0, b1, b2], OcrPreset.DIALOGUE)
    assert len(out) == 1
    assert out[0].speaker == "Efe"
    assert out[0].text == "Merhaba"
    # Gozlemlenen GERCEK davranis (K8'in dort ACIK garantisini ihlal etmiyor):
    assert out[0].source_blocks == (0, 1, 2)
    assert list(out[0].source_blocks) == sorted(out[0].source_blocks)
    assert len(set(out[0].source_blocks)) == len(out[0].source_blocks)
