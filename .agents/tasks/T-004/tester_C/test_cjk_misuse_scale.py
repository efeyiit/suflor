# -*- coding: utf-8 -*-
"""T-004 Tester-C -- MERCEK: sinir, kotu kullanim ve dil -- TUR 5.

Soru: "Latin disi metinde ne oluyor, ve bu API bir sonraki ajani hangi
yanlisa davet ediyor?"

TUR 5 (bu dosyanin GUNCEL hali -- kaynak: sef_karari-tur5.md K23-K27,
sef_karari-tur4.md K21-K22, env.md TUR 5 / MERCEK C):

  - TUR 3'te BLOKE EDICI olarak raporladigim iki test (bolum 14 sonu,
    `test_BULGU_BLOKE_EDICI_k19_*`) K21 (tur 4) ile DUZELTILDI --
    ikisi de `test_DUZELDI_K21_*` olarak YENIDEN YAZILDI, assertion'lar
    TERS CEVRILDI (artik miras UYGULANMADIGINI dogruluyorlar).
  - YENI bolum 16 (TUR 5): B1'in JAPONCA yuzeyi (kendi `勇者：` etiketiyle
    gelen YENI replik AYRI kaliyor mu; uc konusmaculu `勇者`/`魔王`/`村人`
    zinciri, her biri cok satirli VE cap'i asan), gorunum gecisinin CJK
    yuzeyi (`speaker` Unicode BIREBIRLIGI -- halfwidth katakana ve
    fullwidth latin dahil, U+3000 bosluk artigi), karisik-script zinciri,
    `_normalize_impl`/`apply_inheritance` kotu-kullanim yuzeyi, K24 `tail`
    alani, K26 uyumluluk-formu etiket dagilimi, K27 dort on ayar, ve K23
    DEGISMEZI icin Tester-C'nin KENDI fuzz'i (FARKLI tohum, FARKLI
    geometri/metin dagilimi, CJK agirlikli, B1 desenini KASITLI kuran
    "SAHNE" modu).
  - MUTASYON DENETIMI (tester_C_evidence/r5-mutation-check.txt): bolum
    16'nin testleri, `src/` hic degistirilmeden monkeypatch ile kurulan
    TUR 4 (HATALI) `_group` mekanizmasina karsi kosuldu -- B1 testi VE
    K23 fuzz'i KIRILDI, mevcut kodda ikisi de temiz. Yani bu testler
    totoloji DEGIL. (Fuzz ureticisinin ILK hali mutantta SIFIR ihlal
    buluyordu; SAHNE modu eklenerek 48/2600'e cikarildi.)
  - IKI BLOKE ETMEYEN GOZLEM kayda gecti (ayrinti verdict-C.md):
    (a) sefin B1 URUN ETKISI cumlesi ("iki ayri sozce TEK Segment
    oluyor") MIRAS HIC devreye girmeden de olusabilir -- iki replik
    KENDI etiketlerini tasiyip AYNI ada sahipse K15 satir-1
    (`X/X -> EVET`) onlari birlestirir. K23 IHLAL EDILMIYOR (bolumleme
    miras acik/kapali BIREBIR ayni); K23'un degismezi bu yolu
    KAPSAMIYOR. K15 sefin kendi karari ve kod onu birebir uyguluyor ->
    BLOKE ETMIYOR. (b) NFD (kombine aksanli) isimler konusmaci olarak
    TANINMIYOR (`isalpha()` kombine isareti kabul etmez); K9'un lafzina
    UYGUN ama BELGELENMEMIS bir daraltma -> BLOKE ETMIYOR.
  - Olcek TUR 4 taban degerleriyle (2.744/7.032/20.138 ms) karsilastirildi
    VE olcum gurultusu ayrica olculdu (r5-scale_noise.txt).

TUR 3 (kaynak: sef_karari-tur3.md, env.md TUR 3
bolumu): tur 2'de UCU DE onay verdi, ama sef bu dosyanin (tester_C, tur 2)
"bloke etmeyen" saydigi IKI nottan BIRINI (K19) yeniden bloke edici olarak
siniflandirdi -- ikisi de (K19 davranis, K20 dokumantasyon) duzeltildi.
Bu turda:
  - TUR 2'DE "bloke etmeyen" olarak BULUNAN test (bolum 11, asagida
    `test_DUZELDI_K19_...` olarak YENIDEN ADLANDIRILDI) artik DUZELTILMIS
    davranisi (miras alma) dogruluyor -- eski assertion (`speaker is None`)
    TERS CEVRILDI, cunku sef bu senaryoyu BLOKE EDICI ilan edip duzeltti.
  - K19'un SINIRLARI arandi (bolum 14): 3+ parcaya bolunen govdede HER
    kuyruk mu miras aliyor yoksa sadece ilki mi; uzunluk+geometrik bolunme
    ayni zincirde ARKA ARKAYA olursa zincir nerede KOPUYOR; Japonca'da
    (karakter basina daha yogun anlam, max_group_chars daha cabuk doluyor)
    davranis hala dogru mu (bolunme HER ZAMAN blok sinirinda mi, cumle/
    karakter ortasinda DEGIL mi).
  - K20'nin alti karakterlik listesi BAGIMSIZ bir tam Unicode taramasiyla
    (0x0-0x10FFFF) yeniden dogrulandi (bolum 3, guncellendi).
  - YENI BLOKE EDICI BULGU (bolum 14 sonu): `_group_rejection_reason`
    kontrolleri SABIT bir oncelik sirasinda calisiyor (speaker -> length ->
    height -> gap -> width -> overlap) ve yalnizca ILK basarisiz kontrolun
    REASON kodunu donduruyor. Bir cift AYNI ANDA hem `max_group_chars`'i
    asiyor HEM DE gercek bir geometrik sinira (buyuk dikey bosluk VEYA
    yozlasmis h/w) sahipse, kod `"length"` REASON'INI donduruyor (cunku
    length kontrolu geometri kontrollerinden ONCE calisiyor) ve K19
    YANLISLIKLA miras uyguluyor -- TAM OLARAK sef_karari-tur3.md'nin
    tablosunun "Geometrik bosluk ... None kalir" satirinin YASAKLADIGI
    durum. Ayrintili repro ve gerekce asagida ilgili testlerde.
  - TUR 1/2'de ayakta kalan her sey (K4, karisik script/RTL/emoji/ZWJ, K10,
    presets genisletilebilirligi, K15/K16/K17/K18) DEGISTIRILMEDEN yeniden
    kosuluyor (regresyon avi -- gorev tanimin "birinci oncelik" dedigi sey)
  - Olcek (bolum 12) TUR 2'nin r2-scale_timing.txt degerleriyle (n=500/
    1000/2000 -> 3.443/9.271/27.069 ms) KARSILASTIRILDI.

Bu dosya packet.md (14 sef karari) + sef_karari-tur2.md (K15-K18) +
sef_karari-tur3.md (K19-K20) + sef_karari-tur4.md (K21-K22) +
sef_karari-tur5.md (K23-K27) + env.md MERCEK C saldiri listesine karsi kod
uzerinde bagimsiz, kor (delivery.md, evidence/, iptal-tur0/ ve diger
tester dizinleri OKUNMADAN) yazilmistir. Rastgelelik kullanan TEK test
(bolum 16.8 K23 fuzz'i) SABIT tohumla (20250910) calisir -- deterministik.

Calistirma:
    python -m pytest .agents/tasks/T-004/tester_C -q
"""
from __future__ import annotations

import sys
import time
import unicodedata
from pathlib import Path

import pytest

# Depo koku sys.path'e eklenir (bu dosya .agents/ altinda, pytest rootdir
# depo koku degil olabilir) -- src.* importlari icin.
_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.contracts.models import OcrPreset, Rect, TextBlock  # noqa: E402
from src.ocr.normalizer import (  # noqa: E402
    _group,
    _Item,
    _find_speaker_separator,
    _group_rejection_reason,
    _normalize_impl,
    _should_group,
    _union_rect,
    normalize,
)
from src.ocr.presets import (  # noqa: E402
    SPEAKER_LABEL_SEPARATORS,
    NormalizerParams,
    get_params,
)


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


def item(text: str, speaker: str | None, *, x: int = 10, y: int = 0, w: int = 300, h: int = 20) -> _Item:
    """`_should_group` testleri icin dogrudan `_Item` kurar (pipeline'in
    ic temsili) -- gruplama mantigini konusmaci-ayiklamadan BAGIMSIZ sinar."""
    return _Item(text=text, bbox=Rect(x=x, y=y, w=w, h=h), speaker=speaker, source_blocks=(0,))


# ---------------------------------------------------------------------------
# 1. K4 -- CJK tek karakter: SINIF tabanli mi, liste mi? (TUR 1'den DEGISMEDI
#    -- regresyon avi, env.md'nin "birinci oncelik" dedigi sey)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "ch,label",
    [
        ("力", "kanji-guc"),
        ("火", "kanji-ates"),
        ("東", "kanji-dogu"),
        ("한", "hangul-han"),
        ("あ", "hiragana-a"),
        ("ｦ", "halfwidth-katakana-wo"),
        ("Ж", "kiril-zhe"),
        ("ه", "arapca-heh"),
        ("א", "ibranice-alef"),
        ("ก", "tay-ko-kai"),
        ("अ", "devanagari-a"),
    ],
)
def test_regresyon_k4_cjk_ve_rtl_tek_harf_kategori_L_korunur(ch: str, label: str) -> None:
    """K4: Unicode kategorisi L* olan HER tek karakter korunmali -- yalniz
    bir avuc 'bilinen' CJK karakteri degil. TUR 2'de _is_single_char_noise
    DEGISTI (K18 -- NFKC istisnasi eklendi) ama L*/N* dali AYNI kaldi;
    bu test o dalin bozulmadigini dogrular."""
    assert unicodedata.category(ch)[0] == "L", f"test verisi hatali: {label}"
    out = normalize([blk(ch, 10, 10)], OcrPreset.MENU)
    assert [s.text for s in out] == [ch], (
        f"{label} ({ch!r}) tek karakterlik blok silindi -- K4 REGRESYONU"
    )


def test_regresyon_k4_tek_rakam_benzeri_fullwidth_rakam_korunur() -> None:
    ch = "５"  # FULLWIDTH DIGIT FIVE
    assert unicodedata.category(ch)[0] == "N"
    out = normalize([blk(ch, 10, 10)], OcrPreset.MENU)
    assert [s.text for s in out] == [ch]


def test_regresyon_menude_tek_kanjilik_blok_diger_bloklarla_birlikte_hayatta_kalir() -> None:
    guc = blk("力", 10, 0)
    hp = blk("HP", 10, 30)
    degeri = blk("42", 10, 60)
    out = normalize([guc, hp, degeri], OcrPreset.MENU)
    assert [s.text for s in out] == ["力", "HP", "42"]


# ---------------------------------------------------------------------------
# 2. Karisik script + emoji + ZWJ + kombine aksan -- cokme/sessiz saçmalik?
#    (TUR 1'den DEGISMEDI -- regresyon avi)
# ---------------------------------------------------------------------------


def test_regresyon_japonca_ve_latin_karisik_tek_blok_cokmez_ve_metni_korur() -> None:
    text = "レベルUP! HP+10"
    out = normalize([blk(text, 10, 10)], OcrPreset.DIALOGUE)
    assert [s.text for s in out] == [text]


def test_regresyon_korece_ve_latin_karisik_iki_blok_birlesir() -> None:
    b0 = blk("안녕하세요, this is a", 10, 0)
    b1 = blk("mixed sentence 입니다.", 10, 22)
    out = normalize([b0, b1], OcrPreset.DIALOGUE)
    assert len(out) == 1
    assert out[0].text == "안녕하세요, this is a mixed sentence 입니다."


def test_regresyon_rtl_arapca_blok_cokmez() -> None:
    text = "مرحبا بالعالم"
    out = normalize([blk(text, 10, 10)], OcrPreset.DIALOGUE)
    assert [s.text for s in out] == [text]


def test_regresyon_ibranice_blok_cokmez() -> None:
    text = "שלום עולם"
    out = normalize([blk(text, 10, 10)], OcrPreset.DIALOGUE)
    assert [s.text for s in out] == [text]


def test_regresyon_emoji_zwj_aile_sekans_coklu_kodnoktali_tek_blok_cokmez() -> None:
    family = "\U0001f468‍\U0001f469‍\U0001f467"
    assert len(family) > 1
    out = normalize([blk(family, 10, 10)], OcrPreset.DIALOGUE)
    assert [s.text for s in out] == [family]


def test_regresyon_tek_basina_emoji_tek_karakter_kurulmuslugu_sembol_olarak_atilir() -> None:
    """K18 (NFKC istisnasi) emoji'yi ETKILEMEMELI -- ates emojisi NFKC
    altinda kendine esler (?/! DEGIL), bu yuzden hala atilmali."""
    assert unicodedata.category("\U0001f525")[0] == "S"
    assert unicodedata.normalize("NFKC", "\U0001f525") not in ("?", "!")
    out = normalize([blk("\U0001f525", 10, 10)], OcrPreset.MENU)
    assert out == []


def test_regresyon_tek_basina_kombine_aksan_atilir_cokmez() -> None:
    out = normalize([blk("́", 10, 10)], OcrPreset.DIALOGUE)
    assert out == []


def test_regresyon_zwj_tek_basina_atilir_cokmez() -> None:
    out = normalize([blk("‍", 10, 10)], OcrPreset.DIALOGUE)
    assert out == []


# ---------------------------------------------------------------------------
# 3. K4 + K18 -- tam genisli noktalama: Bulgu 4 (Tester-C, tur 1) DUZELDI Mİ?
# ---------------------------------------------------------------------------


def test_DUZELDI_tam_genisli_unlem_artik_korunuyor() -> None:
    """TUR 1 BULGUSU: fullwidth '！' (U+FF01) ASCII '!' ile ayni Po
    kategorisinde olmasina ragmen istisnadan yararlanamiyor, sessizce
    siliniyordu. K18 (NFKC denkligi) bunu duzeltir -- bu test artik
    DUZELTILMIS davranisi dogrular (TUR 1'de tam tersini sabitliyordu)."""
    fullwidth = "！"
    ascii_version = "!"
    assert unicodedata.category(fullwidth) == unicodedata.category(ascii_version) == "Po"
    assert unicodedata.normalize("NFKC", fullwidth) == ascii_version

    out_full = normalize([blk(fullwidth, 10, 10)], OcrPreset.MENU)
    out_ascii = normalize([blk(ascii_version, 10, 10)], OcrPreset.MENU)

    assert [s.text for s in out_full] == [fullwidth], "Bulgu 4 hala DUZELMEMIS (fullwidth '！' siliniyor)"
    assert [s.text for s in out_ascii] == [ascii_version]


def test_DUZELDI_tam_genisli_soru_isareti_artik_korunuyor() -> None:
    fullwidth = "？"
    out = normalize([blk(fullwidth, 10, 10)], OcrPreset.MENU)
    assert [s.text for s in out] == [fullwidth], "Bulgu 4 hala DUZELMEMIS (fullwidth '？' siliniyor)"


def test_k18_sinir_diger_fullwidth_noktalama_hala_atilir_istisna_genislememis() -> None:
    """K18'in NFKC istisnasi SADECE '?'/'!'ye acilan karakterleri kapsamali
    -- baska fullwidth noktalama (virgul, nokta, iki nokta, unlem-soru
    DISI) YINE atilmali. Bu, istisnanin sessizce genislemedigini (K4'un
    'beyaz liste yasak' + 'sadece ?/! istisna' kuralinin ihlal edilmedigini)
    dogrudan sinar."""
    for ch, name in [
        ("、", "fullwidth virgul"),
        ("。", "fullwidth nokta"),
        ("：", "fullwidth iki nokta (K17 ayiraci ama TEK BASINA blok olarak gurultu)"),
        ("・", "fullwidth orta nokta"),
        ("～", "fullwidth tilde"),
    ]:
        assert unicodedata.normalize("NFKC", ch) not in ("?", "!"), f"test verisi hatali: {name}"
        out = normalize([blk(ch, 10, 10)], OcrPreset.MENU)
        assert out == [], f"{name} ({ch!r}) artik korunuyor -- K18 istisnasi SESSIZCE genislemis olabilir"


def test_k18_nfkc_taramasi_tam_genisli_disinda_4_karakter_daha_esliyor() -> None:
    """SORU (gorev tanimi madde 1): '？'/'！' disinda NFKC ile '?'/'!'ye
    ACILAN baska karakter var mi, ve bunlardan ISTENMEYEN bir sey sizdi mi?

    TUM Unicode kod noktalari taranarak (0..0x10FFFF) NFKC('?') / NFKC('!')
    veren kume BULUNDU: '？'/'！' disinda TAM OLARAK 4 karakter daha var --
    U+FE15/U+FE16 (dikey sunum bicimleri) ve U+FE56/U+FE57 (kucuk bicimler).
    Docstring'in K4 bolumu ('ayrica baska hicbir karakter NFKC ile ?/!'ye
    ACILMADIGI icin istisna GENISLEMEZ') bu yuzden KATI ANLAMDA YANLIS --
    tam olarak 4 karakter daha aciliyor, sifir degil. PRATIKTE zararsiz:
    hepsi ayni Po kategorisinde, CJK metinlerde gorulebilecek MESRU '?'/'!'
    sunum varyantlari (dikey yazim / kucuk-bicim noktalama) -- yani
    'istenmeyen' bir sey SIZMIYOR (L*/N* kontrolu NFKC kontrolunden ONCE
    calistigi icin bir harf/rakamin yanlislikla '?'/'!' sayilip silinmesi
    de mumkun degil). Ama docstring'in 'hic baska yok' iddiasi hala
    duzeltilmeli -- 'sifir' ile 'dort tane, hepsi zararsiz CJK varyanti'
    arasindaki fark, bir sonraki okuyucunun (implementer/tester) net bir
    sayiya guvenip guvenemeyecegini belirler."""
    hits = []
    for cp in range(0x110000):
        ch = chr(cp)
        n = unicodedata.normalize("NFKC", ch)
        if n in ("?", "!") and ch not in ("?", "!"):
            hits.append((cp, ch, unicodedata.category(ch)))
    codepoints = sorted(cp for cp, _, _ in hits)
    assert codepoints == [0xFE15, 0xFE16, 0xFE56, 0xFE57, 0xFF01, 0xFF1F], (
        f"beklenmedik NFKC->?/! kumesi: {[hex(c) for c in codepoints]} -- "
        "K18 istisnasinin fiili kapsami degismis olabilir"
    )
    # Hepsi Po (noktalama) -- L*/N* DEGIL, yani K4'un 'beyaz liste yok'
    # kuralini ihlal eden bir 'harf sizmasi' yok:
    assert all(cat[0] == "P" for _, _, cat in hits)
    # Ve pratikte de bu 4 fazladan karakter dogru calisir (korunur):
    for cp in (0xFE15, 0xFE16, 0xFE56, 0xFE57):
        out = normalize([blk(chr(cp), 10, 10)], OcrPreset.MENU)
        assert [s.text for s in out] == [chr(cp)]


# ---------------------------------------------------------------------------
# 4. K9 + K17 -- fullwidth iki nokta (：) ile konusmaci: Bulgu 3 DUZELDI Mİ?
# ---------------------------------------------------------------------------


def test_DUZELDI_tam_genisli_iki_nokta_ile_konusmaci_artik_AYIKLANIYOR() -> None:
    """TUR 1 BULGUSU: 'アダ：こんにちは' (fullwidth iki nokta) konusmaci
    ayiklamasindan hic gecmiyordu. K17 (SPEAKER_LABEL_SEPARATORS'a '：'
    eklendi) bunu duzeltir."""
    etiket_ascii = blk("Ada:", 10, 0)
    icerik_ascii = blk("Merhaba nasilsin", 10, 22)
    out_ascii = normalize([etiket_ascii, icerik_ascii], OcrPreset.DIALOGUE)
    assert out_ascii[0].speaker == "Ada"

    tek_blok = blk("アダ：こんにちは", 10, 0)
    out_jp = normalize([tek_blok], OcrPreset.DIALOGUE)
    assert len(out_jp) == 1
    assert out_jp[0].speaker == "アダ", "Bulgu 3 hala DUZELMEMIS (fullwidth '：' ayiklanamiyor)"
    assert out_jp[0].text == "こんにちは", "etiket govdeden TEMIZLENMEMIS"


def test_DUZELDI_tam_genisli_iki_nokta_iki_ayri_blokta_da_calisir() -> None:
    etiket = blk("アダ：", 10, 0)
    icerik = blk("こんにちは", 10, 22)
    out = normalize([etiket, icerik], OcrPreset.DIALOGUE)
    assert len(out) == 1
    assert out[0].speaker == "アダ"
    assert out[0].text == "こんにちは"


def test_k17_sinir_baska_iki_nokta_varyantlari_hala_TANINMIYOR() -> None:
    """SORU (gorev tanimi madde 1): K17 ayrac kumesi ':' ve '：' ile
    SINIRLI. Docstring bunu ACIKCA soyluyor mu, yoksa gelistirici genis
    kapsam mi sanir? -- presets.py SPEAKER_LABEL_SEPARATORS docstring'i
    '﹕' (U+FE55) ve 'dikey yazimda gorulen ayiraclar'i ACIKCA KAPSAM DISI
    sayiyor. Bu test o sinirin fiilen dogru oldugunu (kod SESSIZCE daha
    genis davranmiyor) kod uzerinde dogrudan sinar -- ':' / '：' DISINDA
    HICBIR varyant ayirac olarak TANINMAMALI."""
    assert SPEAKER_LABEL_SEPARATORS == (":", "："), (
        "K17 ayirac kumesi degismis -- asagidaki 'tanınmiyor' iddialari "
        "yeniden degerlendirilmeli"
    )
    diger_varyantlar = [
        ("∶", "RATIO U+2236"),
        ("﹕", "SMALL COLON U+FE55 -- docstring'de ACIKCA belirtilen kapsam-disi ornek"),
        ("ː", "MODIFIER LETTER TRIANGLE COLON U+02D0 (IPA uzunluk isareti)"),
        ("﹕", "presentation form colon"),
        ("：", "-- KONTROL: bu TANINMALI (K17 icinde)"),
    ]
    for sep, label in diger_varyantlar[:-1]:
        assert _find_speaker_separator(f"İsim{sep}govde") == -1, (
            f"{label} ({sep!r}) beklenmedik sekilde ayirac olarak TANINDI -- "
            "K17 kapsami sessizce genislemis olabilir"
        )
    # Kontrol: gercekten kapsamdaki karakter tanınıyor mu (test verisinin
    # kendisinin gecerli oldugunu dogrulamak icin):
    assert _find_speaker_separator("İsim：govde") != -1


def test_k17_sinir_metin_ortasinda_gecen_ayirac_ilk_eslesmeyi_kullanir() -> None:
    """Coklu ayirac: 'Ada: kime: mesaj' -- EN SOLDAKI (ilk) eslesme
    kazanmali (docstring'in '_find_speaker_separator' aciklamasi)."""
    idx = _find_speaker_separator("Ada: kime: mesaj")
    assert idx == 3  # 'Ada' uzunlugu -- ilk ':' konumu

    out = normalize([blk("Ada: kime: mesaj", 10, 0)], OcrPreset.DIALOGUE)
    assert out[0].speaker == "Ada"
    assert out[0].text == "kime: mesaj"  # ikinci ':' govdede AYNEN kalir (K6: birebir korunur)


def test_k17_sinir_metin_ortasindaki_fullwidth_ayirac_da_ilk_eslesme() -> None:
    """Karisik ASCII+fullwidth ayirac: ilk (en soldaki) HANGISI olursa
    olsun kazanmali -- ayiracin TURU degil, KONUMU belirleyici."""
    idx = _find_speaker_separator("İsim：ic metin: devami")
    name_len = len("İsim")
    assert idx == name_len

    out = normalize([blk("İsim：ic metin: devami", 10, 0)], OcrPreset.DIALOGUE)
    assert out[0].speaker == "İsim"
    assert out[0].text == "ic metin: devami"


def test_k17_sinir_bosluk_yalniz_ayirac_ile_baslayan_blok_isim_bos_sayilir() -> None:
    """Ayirac metnin EN BASINDA (idx==0) ise -- isim yok -- etiket
    sayilmamali (`_split_speaker_label`: `idx <= 0` -> None)."""
    out = normalize([blk(": bos isim govdesi", 10, 0)], OcrPreset.DIALOGUE)
    assert out[0].speaker is None
    assert out[0].text == ": bos isim govdesi"

    out_fw = normalize([blk("：フルワイド先頭govde", 10, 0)], OcrPreset.DIALOGUE)
    assert out_fw[0].speaker is None


def test_k17_sinir_fullwidth_rakamli_saat_metni_konusmaci_SAYILMAZ() -> None:
    """ASCII '12:30' saat metninin konusmaci sayilmamasi paketin kendi
    test listesinde var (K9, `_MAX_SPEAKER_NAME_LEN` + isalpha kontrolu).
    K17 ayirac kumesini genislettigi icin AYNI riskin fullwidth-rakamli
    JP saat gosterimi ('１２：３０') icin de gecerli olup olmadigini
    ACIKCA sinamak gerekir -- fullwidth rakam kategori Nd, isalpha() False
    dondurur, bu yuzden 'İsim' regex'i reddetmeli."""
    out = normalize([blk("１２：３０", 10, 10)], OcrPreset.DIALOGUE)
    assert out[0].speaker is None
    assert out[0].text == "１２：３０"


# ---------------------------------------------------------------------------
# 5. K10 -- bbox birlesimi (TUR 1'den DEGISMEDI -- regresyon avi)
# ---------------------------------------------------------------------------


def test_regresyon_k10_farkli_monitor_index_cjk_metinde_de_value_error() -> None:
    b0 = blk("東京は", 10, 0, monitor_index=0)
    b1 = blk("大きい街です。", 10, 20, monitor_index=1)
    with pytest.raises(ValueError):
        normalize([b0, b1], OcrPreset.DIALOGUE)


def test_regresyon_k10_farkli_dpi_scale_hyphen_birlesiminde_de_value_error() -> None:
    b0 = blk("tra-", 10, 0, dpi_scale=1.0)
    b1 = blk("dition", 10, 20, dpi_scale=1.5)
    with pytest.raises(ValueError):
        normalize([b0, b1], OcrPreset.MENU)


def test_regresyon_k10_ayni_monitor_farkli_dpi_uc_blok_zincirinde_ucuncude_patlar() -> None:
    b0 = blk("abc-", 10, 0, dpi_scale=1.0)
    b1 = blk("def-", 10, 20, dpi_scale=1.0)
    b2 = blk("ghi", 10, 40, dpi_scale=1.25)
    with pytest.raises(ValueError):
        normalize([b0, b1, b2], OcrPreset.MENU)


# ---------------------------------------------------------------------------
# 6. K10 + K16 -- yozlasmis geometride gruplama: TUR 1'de Tester-A'nin
#    bulgusu (Bulgu 2), TUR 2'de K16 ile duzeltildi -- Tester-C
#    merceginden BAGIMSIZ tekrar dogrulanir (regresyon + garanti alani).
# ---------------------------------------------------------------------------


def test_DUZELDI_k16_h_esittir_sifir_ayni_y_artik_GRUPLANMIYOR() -> None:
    """sef_karari-tur2.md Bulgu 2: h=0, ayni y (gap=0) -- eski kod
    docstring'in vaadinin AKSINE gruplyordu. K16 bunu duzeltti."""
    a = blk("parca1", 10, 10, h=0)
    b = blk("parca2", 10, 10, h=0)
    out = normalize([a, b], OcrPreset.DIALOGUE)
    assert len(out) == 2, "K16 regresyonu: h=0 ayni-y hala gruplaniyor"
    assert [s.text for s in out] == ["parca1", "parca2"]


def test_DUZELDI_k16_negatif_yukseklikte_deger_gruplanmiyor() -> None:
    """sef_karari-tur2.md Bulgu 2'nin ikinci sondasi: a: y=-15 h=20
    (bottom=5), b: y=0 h=-10 -- negatif h ile `bottom = y+h` hesabi
    gap'i pozitif gosterebiliyordu ONCEKI sef sondasinda (hatali kurulum);
    DOGRU kurulan bu senaryoda eski kod gruplayabiliyordu, K16 engeller."""
    a = blk("parca1", 10, -15, h=20)
    b = blk("parca2", 10, 0, h=-10)
    out = normalize([a, b], OcrPreset.DIALOGUE)
    assert len(out) == 2, "K16 regresyonu: negatif h ile gruplama hala oluyor"


def test_regresyon_k16_w_esittir_sifir_hala_gruplanmiyor() -> None:
    """w==0 dali TUR 1'de zaten (matematiksel olarak) dogru davraniyordu
    -- K16 sadece KOSULSUZ hale getirdi. Regresyon: hala dogru mu?"""
    a = blk("parca1", 10, 0, w=0)
    b = blk("parca2", 10, 22, w=0)
    out = normalize([a, b], OcrPreset.DIALOGUE)
    assert len(out) == 2


def test_k16_sinir_should_group_dogrudan_ref_height_sifir_reddeder() -> None:
    """`_should_group`'u DOGRUDAN (pipeline'dan bagimsiz) cagirarak K16'nin
    iddia ettigi 'ref_height <= 0 -> KOSULSUZ False' davranisini sinar --
    ayni konusmaci, ayni gap=0, farkli h degerleri (0 ve pozitif; min=0)."""
    params = get_params(OcrPreset.DIALOGUE)
    a = item("a", None, y=0, h=0)
    b = item("b", None, y=0, h=20)  # ref_height = min(0, 20) = 0
    assert _should_group(a, b, params) is False


def test_k16_sinir_should_group_pozitif_ref_height_normal_calisir() -> None:
    """Kontrol: K16 SADECE yozlasmis (<=0) durumda devreye girmeli --
    pozitif ref_height'ta normal geometrik kural (gap < oran*h) gecerli
    olmaya DEVAM etmeli (K16 asiri genis bir 'hicbir zaman gruplama'
    kuraliyla YANLISLIKLA degistirilmemis)."""
    params = get_params(OcrPreset.DIALOGUE)
    a = item("a", None, y=0, h=20)
    b = item("b", None, y=25, w=300, h=20)  # gap=5, 5 < 0.8*20=16 -> gruplanmali
    assert _should_group(a, b, params) is True


# ---------------------------------------------------------------------------
# 7. K9 + K15 -- konusmaci+gruplama: Bulgu 1 (KRITIK) DUZELDI Mİ?
#    Tasarim dokumani S5.2'nin modulun VAR OLMA SEBEBI ornegi.
# ---------------------------------------------------------------------------


def test_DUZELDI_KRITIK_etiketli_2_bloklu_govde_tek_segmente_birlesiyor_ASCII() -> None:
    etiket = blk("Ada:", 10, 0)
    satir1 = blk("Bu uzun bir", 10, 22)
    satir2 = blk("cumledir.", 10, 44)
    out = normalize([etiket, satir1, satir2], OcrPreset.DIALOGUE)
    assert len(out) == 1, f"Bulgu 1 hala DUZELMEMIS: {[(s.text, s.speaker) for s in out]}"
    assert out[0].speaker == "Ada"
    assert out[0].text == "Bu uzun bir cumledir."
    assert out[0].source_blocks == (0, 1, 2)


def test_DUZELDI_KRITIK_japonca_2_bloklu_govde_tek_segmente_birlesiyor() -> None:
    etiket = blk("勇者:", 10, 0)
    satir1 = blk("この町はとても", 10, 22)
    satir2 = blk("大きいですね。", 10, 44)
    out = normalize([etiket, satir1, satir2], OcrPreset.DIALOGUE)
    assert len(out) == 1
    assert out[0].speaker == "勇者"
    assert out[0].text == "この町はとても 大きいですね。"


def test_DUZELDI_gorevin_istedigi_UC_VE_DAHA_FAZLA_satirda_calisir_ASCII() -> None:
    """Gorev tanimi acikca 3+ satiri istiyor -- bu, orijinal 3-bloklu
    ('Ada:'+2 icerik) repro'dan farkli olarak 4 VE 5 icerik blogunu
    (toplam 5 ve 6 blok) sinar, K15'in _group ICINDE 'current.speaker'in
    miras zincirini KOPARMADAN tasidigini dogrudan kanitlar."""
    etiket = blk("Ada:", 10, 0)
    satirlar = [blk(f"satir{i}", 10, 22 + i * 22) for i in range(4)]  # 4 icerik blogu
    out = normalize([etiket, *satirlar], OcrPreset.DIALOGUE)
    assert len(out) == 1
    assert out[0].speaker == "Ada"
    assert out[0].text == "satir0 satir1 satir2 satir3"
    assert out[0].source_blocks == (0, 1, 2, 3, 4)


def test_DUZELDI_gorevin_istedigi_UC_VE_DAHA_FAZLA_satirda_calisir_japonca() -> None:
    etiket = blk("勇者:", 10, 0)
    satirlar = [blk(f"文章{i}", 10, 22 + i * 22) for i in range(5)]  # 5 icerik blogu
    out = normalize([etiket, *satirlar], OcrPreset.DIALOGUE)
    assert len(out) == 1
    assert out[0].speaker == "勇者"
    assert out[0].text == "文章0 文章1 文章2 文章3 文章4"
    assert out[0].source_blocks == (0, 1, 2, 3, 4, 5)


def test_gercekci_japonca_diyalog_sahnesi_uctan_uca() -> None:
    etiket = blk("勇者:", 10, 0)
    govde = blk("この町はとても大きいですね。", 10, 22)
    hud_hp = blk("力", 10, 900)
    out = normalize([etiket, govde, hud_hp], OcrPreset.DIALOGUE)
    metinler = {s.text: s for s in out}
    assert "力" in metinler
    diyalog = [s for s in out if s.speaker == "勇者"]
    assert len(diyalog) == 1
    assert diyalog[0].text == "この町はとても大きいですね。"


def test_KOTU_KULLANIM_konusmaci_etiketi_ayni_satirdaki_ALAKASIZ_bloga_sizar() -> None:
    """TUR 1'den DEGISMEDI (K9'un tanimli davranisinin dogal sonucu,
    K15 bunu etkilemedi -- regresyon avi): normalize()'e TEK bir mantiksal
    UI bolgesi VERILMELI varsayimi hala BELGELENMEMIS bir on-kosul."""
    etiket = blk("勇者:", 10, 0)
    hud_ayni_satirda = blk("HP99", 500, 0)
    diyalog_govdesi = blk("この町はとても大きいですね。", 10, 22)
    out = normalize([etiket, hud_ayni_satirda, diyalog_govdesi], OcrPreset.DIALOGUE)
    hud_segment = next(s for s in out if "HP99" in s.text)
    diyalog_segment = next(s for s in out if "この町" in s.text)
    assert hud_segment.speaker == "勇者"
    assert diyalog_segment.speaker is None


# ---------------------------------------------------------------------------
# 8. K15 matrisi -- BESİ AYRI satirin `_should_group` uzerinde DOGRUDAN
#    dogrulanmasi (env.md: "K15 tablosunun bes satiri da AYRI AYRI
#    sinanacak, ozellikle None/Y ve X/Y"). Pipeline'dan bagimsiz, en
#    hassas regresyon agidir.
# ---------------------------------------------------------------------------


def test_k15_matris_X_X_ayni_konusmaci_gruplanir() -> None:
    params = get_params(OcrPreset.DIALOGUE)
    a = item("satir1", "Ada", y=0, h=20)
    b = item("satir2", "Ada", y=10, h=20)
    assert _should_group(a, b, params) is True


def test_k15_matris_X_None_devam_satiri_gruplanir_ve_X_MIRAS_ALINIR() -> None:
    params = get_params(OcrPreset.DIALOGUE)
    a = item("satir1", "Ada", y=0, h=20)
    b = item("satir2", None, y=10, h=20)
    assert _should_group(a, b, params) is True
    # Miras: gerçek `_group` cagrisiyla teyit (current.speaker kullanilir):
    out = normalize(
        [blk("Ada:", 10, 0), blk("satir1", 10, 20), blk("satir2", 10, 30, w=300)],
        OcrPreset.DIALOGUE,
    )
    assert out[0].speaker == "Ada"


def test_k15_matris_None_None_gruplanir_speaker_None_kalir() -> None:
    params = get_params(OcrPreset.DIALOGUE)
    a = item("satir1", None, y=0, h=20)
    b = item("satir2", None, y=10, h=20)
    assert _should_group(a, b, params) is True


def test_k15_matris_None_Y_YENI_konusmaci_ASLA_gruplanmaz() -> None:
    """ENV.MD'NIN OZELLIKLE VURGULADIGI SATIR: etiketsiz bir oge + hemen
    ardindan ACIKCA etiketli bir oge -- 'None' asla 'gelecek konusmaci'
    anlamina GELMEMELI, K15 bunu GEVSETMEMIS olmali."""
    params = get_params(OcrPreset.DIALOGUE)
    a = item("etiketsiz satir", None, y=0, h=20)
    b = item("govde", "Mia", y=10, h=20)
    assert _should_group(a, b, params) is False, (
        "K15 REGRESYONU: None/Y (yeni konusmaci basliyor) artik YANLISLIKLA gruplaniyor"
    )


def test_k15_matris_X_Y_iki_FARKLI_konusmaci_ASLA_gruplanmaz() -> None:
    """ENV.MD'NIN OZELLIKLE VURGULADIGI SATIR: K9'un ASIL yasakladigi
    durum -- iki FARKLI, ADLANDIRILMIS konusmaci ASLA birlesmemeli."""
    params = get_params(OcrPreset.DIALOGUE)
    a = item("Ada'nin sozu", "Ada", y=0, h=20)
    b = item("Mia'nin sozu", "Mia", y=10, h=20)
    assert _should_group(a, b, params) is False, (
        "K15 REGRESYONU: X/Y (iki farkli konusmaci) artik YANLISLIKLA gruplaniyor"
    )


def test_k15_matris_ucdan_uca_None_Y_pipeline_uzerinde_de_dogrulanir() -> None:
    """Pipeline seviyesinde: baslangicta etiketsiz bir cumle, hemen
    ardindan yeni bir konusmaci etiketi -- ikisi ASLA birlesmemeli."""
    b0 = blk("Sistem mesaji, etiketsiz.", 10, 0)
    b1 = blk("Mia: Merhaba!", 10, 22)
    out = normalize([b0, b1], OcrPreset.DIALOGUE)
    assert len(out) == 2
    assert out[0].speaker is None
    assert out[1].speaker == "Mia"


def test_k15_matris_ucdan_uca_X_Y_pipeline_uzerinde_de_dogrulanir() -> None:
    """Pipeline seviyesinde, dialogue'da: ard arda IKI FARKLI etiketli
    konusmaci -- K9'un yasakladigi 'ikinci konusmaciyi yutma' senaryosu."""
    b0 = blk("Ada: İlk cumle.", 10, 0)
    b1 = blk("Mia: İkinci cumle.", 10, 22)
    out = normalize([b0, b1], OcrPreset.DIALOGUE)
    assert len(out) == 2
    assert out[0].speaker == "Ada"
    assert out[1].speaker == "Mia"
    assert "İlk cumle" in out[0].text
    assert "İkinci cumle" in out[1].text
    # Ikinci konusmaci YUTULMADI -- ayri, dogru metniyle var:
    assert out[1].text == "İkinci cumle."


# ---------------------------------------------------------------------------
# 9. K10 + K16 -- yozlasmis girdi bbox'unun BASKA bir ogeyle KOMSU olma
#    disinda TEK BASINA (gruplama disi) davranisi -- cokme yok, ic-degeri
#    degismiyor.
# ---------------------------------------------------------------------------


def test_yozlasmis_h_sifir_tek_basina_blok_normal_islenir() -> None:
    out = normalize([blk("tek blok", 10, 10, h=0)], OcrPreset.MENU)
    assert [s.text for s in out] == ["tek blok"]


def test_yozlasmis_negatif_w_tek_basina_blok_cokmez() -> None:
    out = normalize([blk("tek blok", 10, 10, w=-5)], OcrPreset.MENU)
    assert [s.text for s in out] == ["tek blok"]


# ---------------------------------------------------------------------------
# 10. Kotu kullanim -- bir sonraki ajan hangi yanlisa davet ediliyor?
#     (TUR 1'den DEGISMEDI + K15'in YENI belirsizligi asagida bolum 11'de)
# ---------------------------------------------------------------------------


def test_regresyon_line_boxes_doldurmak_YANLIS_beklentiyi_teyit_eder_sessizce_yok_sayilir() -> None:
    celisen_line_boxes = (Rect(9999, 9999, 1, 1, monitor_index=5, dpi_scale=9.9),)
    b_celisen = blk("Merhaba", 10, 10, line_boxes=celisen_line_boxes)
    b_normal = blk("Merhaba", 10, 10, line_boxes=())
    out_celisen = normalize([b_celisen], OcrPreset.DIALOGUE)
    out_normal = normalize([b_normal], OcrPreset.DIALOGUE)
    assert out_celisen == out_normal


def test_regresyon_preset_stringini_dogrudan_str_ile_cagirmak_calisir_ama_belgelenmemis() -> None:
    out_enum = normalize([blk("Test", 10, 10)], OcrPreset.DIALOGUE)
    out_str = normalize([blk("Test", 10, 10)], "dialogue")  # type: ignore[arg-type]
    assert out_enum == out_str


def test_regresyon_normalize_girdi_listesi_YAN_ETKI_ile_degismez() -> None:
    blocks = [blk("Bir", 10, 0), blk("Iki", 10, 30)]
    snapshot = list(blocks)
    normalize(blocks, OcrPreset.MENU)
    assert blocks == snapshot


def test_regresyon_ayni_girdiyle_iki_cagri_bitbit_ayni_sonucu_verir_onbellek_yok() -> None:
    blocks = [
        blk("アダ:", 10, 0),
        blk("Merhaba %s ve %s, 50% tamamlandi <color=red>力</color>", 10, 22),
    ]
    out1 = normalize(blocks, OcrPreset.DIALOGUE)
    out2 = normalize(blocks, OcrPreset.DIALOGUE)
    assert out1 == out2


# ---------------------------------------------------------------------------
# 11. KOTU KULLANIM YUZEYI (TUR 2'de BULUNDU, TUR 3'te K19 ILE KISMEN
#     DUZELTILDI) -- K15'in "None = devam" kurali `Segment.speaker=None`
#     alanini IKI FARKLI anlam icin asiri yukluyordu: (a) bu satirin
#     GERCEKTEN hic konusmacisi yok, (b) bu satir aslinda BIR ONCEKI
#     konusmacinin devami ama baska bir kisitlama yuzunden ayri bir
#     Segment'e dusmus. K19, YALNIZCA `max_group_chars` (uzunluk) kaynakli
#     durumda bu ikisini ARTIK AYIRT EDIYOR (miras alarak) -- ilk testin
#     assertion'i bu yuzden TUR 3'te TERS CEVRILDI. Geometrik kopukluk
#     kaynakli belirsizlik (ikinci test) K19 SONRASI da KASITLI olarak
#     `None` kaliyor (docstring bunu ACIKCA "iki anlam" olarak belgeliyor,
#     bkz. normalizer.py K19 bolumu son paragraf) -- bu artik bir
#     BELGELENMEMIS bilgi kaybi degil, BILINEN ve KABUL EDILMIS bir sinir.
# ---------------------------------------------------------------------------


def test_DUZELDI_K19_max_group_chars_asimi_devam_satirinin_konusmacisini_ARTIK_KAYBETMIYOR() -> None:
    """TUR 2 BULGUSU (bu dosyanin tur 2 hali, "bloke etmeyen" olarak
    raporlanmisti; sef sef_karari-tur3.md'de bunu YENIDEN SINIFLANDIRDI --
    bloke edici) -- SOMUT REPRO: `Ada:` etiketli, TOPLAM metni
    `max_group_chars`'i (dialogue: 280) asan cok-bloklu bir govde -- ilk
    grup Ada'ya baglanir, grup 280 karakteri astiginda YENI bir grup
    baslar. TUR 2'DE bu YENI grubun ilk ogesi `speaker=None` TASIYORDU
    (SESSIZ bilgi kaybi -- asagi akis 'konusmacisi yok' ile 'Ada'nin
    devami' ayirt edemiyordu). K19 (sef_karari-tur3.md) bunu duzeltir:
    bolunme sebebi TAM OLARAK `"length"` ise (`_group_rejection_reason`)
    kuyruk `Ada`'yi MIRAS alir.

    Bu test artik DUZELTILMIS davranisi dogrular -- eski (tur 2) assertion
    (`speaker is None`) TERS CEVRILDI."""
    etiket = blk("Ada:", 10, 0)
    # 8 icerik blogu, her biri ~40 karakter -> toplam ~320+ karakter,
    # dialogue'un max_group_chars=280'ini asar (deterministik, ayni
    # sef_karari-tur2.md'nin K14 olcum sartnamesindeki 'blok basina ~40
    # karakter' bicemiyle):
    satirlar = [blk(f"satir numarasi {i:02d} biraz uzunca bir metin", 10, 22 + i * 22) for i in range(8)]
    out = normalize([etiket, *satirlar], OcrPreset.DIALOGUE)

    assert len(out) >= 2, "test varsayimi gecersiz -- max_group_chars asilmadi, senaryoyu ayarla"
    assert out[0].speaker == "Ada"
    # K19: kuyruk (devam) segment ARTIK Ada'yi miras aliyor -- bilgi kaybi YOK:
    ikinci_devam_segment = out[1]
    assert ikinci_devam_segment.speaker == "Ada", (
        "K19 REGRESYONU: ikinci parca hala speaker=None -- uzunluk-kaynakli "
        "miras calismiyor"
    )
    # Asagi-akis artik bu segmenti bagimsiz, etiketsiz bir cumleden AYIRT
    # EDEBILIYOR (ikisi de once speaker=None DONERDI, artik degil):
    bagimsiz_cumle = normalize([blk("Bagimsiz, etiketsiz bir cumle.", 10, 0)], OcrPreset.DIALOGUE)
    assert bagimsiz_cumle[0].speaker is None
    assert ikinci_devam_segment.speaker != bagimsiz_cumle[0].speaker


def test_TUR3_saf_geometrik_bosluk_bolunmesinde_speaker_None_KALMASI_KASITLI() -> None:
    """TUR 2'de bu test 'ayni belirsizligin ikinci uretim yolu' basligiyla
    bir GOZLEM olarak duruyordu. TUR 3'te K19, bolunme SEBEBINE gore ayrim
    yapiyor -- SAF geometrik bosluk (uzunluk sinirinin HIC devreye
    girmedigi, kisa metinli bu senaryo) icin `None` kalmasi artik KASITLI
    ve DOGRU davranistir (sef_karari-tur3.md tablosunun ikinci satiri --
    'Geometrik bosluk ... None kalir, atfetmek spekulasyon olur'), bir
    bilgi kaybi DEGIL. Bu, K19'un `test_k19_geometrik_bosluk_bolunmesinde_
    kuyruk_speaker_none_kalir` testiyle (asagida, bolum 14) AYNI davranisi
    farkli bir kurulumla dogrulayan bir REGRESYON testidir."""
    etiket = blk("Ada:", 10, 0)
    satir1 = blk("İlk parca.", 10, 22, h=20)
    # Cok buyuk dikey bosluk -- max_vertical_gap_ratio (dialogue: 0.8) *
    # ref_height (20) = 16'dan cok daha fazla, gruplama REDDEDILIR. Metin
    # cok kisa oldugu icin max_group_chars (280) BURADA HIC devreye
    # girmiyor -- bu SAF (compound olmayan) bir geometrik bolunme:
    satir2 = blk("Devam parcasi.", 10, 500, h=20)
    out = normalize([etiket, satir1, satir2], OcrPreset.DIALOGUE)
    assert len(out) == 2
    assert out[0].speaker == "Ada"
    assert out[1].speaker is None  # K19: SAF geometrik bolunme -- miras YOK (dogru)


# ---------------------------------------------------------------------------
# 12. Olcek -- K19 (yeni fonksiyon cagrisi: `_group_rejection_reason`,
#     gruplama yolunda) sonrasi buyume kotulesti mi? (TUR 2 ile karsilastirma)
# ---------------------------------------------------------------------------


def test_olcek_tek_blok_cjk_cokmez() -> None:
    out = normalize([blk("力", 10, 10)], OcrPreset.DIALOGUE)
    assert [s.text for s in out] == ["力"]


def test_olcek_500_blok_cjk_cokmez_ve_hepsi_korunur() -> None:
    bloklar = [blk(f"項目{i:04d}", 10, i * 100) for i in range(500)]
    out = normalize(bloklar, OcrPreset.MENU)
    assert len(out) == 500
    assert out[0].text == "項目0000"
    assert out[-1].text == "項目0499"


def test_olcek_10000_karakterlik_tek_blok_cokmez() -> None:
    uzun_metin = "力火東京は大きい街です。" * 900
    assert len(uzun_metin) > 10_000
    out = normalize([blk(uzun_metin, 10, 10)], OcrPreset.DIALOGUE)
    assert len(out) == 1
    assert out[0].text == uzun_metin


def test_olcek_ust_uste_binen_500_blok_cokmez() -> None:
    bloklar = [blk(f"kelime{i}", 100, 100, w=50, h=20) for i in range(500)]
    out = normalize(bloklar, OcrPreset.DIALOGUE)
    assert out != []
    toplam_kaynak = sum(len(s.source_blocks) for s in out)
    assert toplam_kaynak == 500


def _timed_normalize_ms(bloklar: list[TextBlock], preset: OcrPreset, tekrar: int = 7) -> float:
    sureler = []
    for _ in range(tekrar):
        start = time.perf_counter()
        normalize(bloklar, preset)
        sureler.append((time.perf_counter() - start) * 1000.0)
    sureler.sort()
    return sureler[len(sureler) // 2]


def test_olcek_kuadratik_degil_500_vs_2000_blok_olcekleme() -> None:
    """TUR 1'deki AYNI dumanli test -- K15/K16 sonrasi hala 20x'in
    ALTINDA mi (O(n^2)+ patlamasina karsi kaba muhafaza)?"""
    kucuk = [blk(f"kelime{i}-", 100, 100, w=50, h=20) for i in range(500)]
    buyuk = [blk(f"kelime{i}-", 100, 100, w=50, h=20) for i in range(2000)]

    t_kucuk = _timed_normalize_ms(kucuk, OcrPreset.DIALOGUE)
    t_buyuk = _timed_normalize_ms(buyuk, OcrPreset.DIALOGUE)

    oran = (t_buyuk + 0.05) / (t_kucuk + 0.05)
    assert oran < 20.0, (
        f"500->2000 blok (4x) icin sure orani {oran:.1f}x -- K15/K16 "
        f"olcegi KOTULESTIRMIS olabilir "
        f"(t_500={t_kucuk:.3f}ms, t_2000={t_buyuk:.3f}ms)"
    )


def test_olcek_tur1_ile_karsilastirma_n2000_belirgin_kotulesmemis() -> None:
    """DOGRUDAN KARSILASTIRMA: TUR 1'de (tester_C_evidence/scale_timing.txt,
    ust-uste-binen 2000 blok) medyan ~26.7 ms olculmustu. K15/K16 SADECE
    O(1) ek karsilastirma ekliyor (speaker esitligi + ref_height/ref_width
    kontrolu, ikisi de dongu basina sabit islem) -- büyüme SINIFINI
    DEGISTIRMEMELI. Gevsek bir ust sinir (TUR 1 degerinin ~2 kati, olcum
    gurultusune tolerans) ile bunu dogrudan sinar; asim K15/K16'nin
    beklenmedik bir O(n) UZERI maliyet eklendigine isaret eder."""
    ust_uste = [blk(f"kelime{i}", 100, 100, w=50, h=20) for i in range(2000)]
    t = _timed_normalize_ms(ust_uste, OcrPreset.DIALOGUE, tekrar=7)
    tur1_medyan_ms = 26.7
    assert t < tur1_medyan_ms * 2.0, (
        f"n=2000 ust-uste-binen blok icin TUR 2 medyan {t:.2f}ms, "
        f"TUR 1'in ({tur1_medyan_ms}ms) 2 katindan FAZLA -- K15/K16 "
        "olcegi belirgin sekilde kotulestirmis olabilir"
    )


def test_olcek_tur2_ile_karsilastirma_n500_1000_2000_K19_kotulesmemis() -> None:
    """TUR 3 DOGRUDAN KARSILASTIRMA (gorev tanimi madde 4): TUR 2'de
    (tester_C_evidence/r2-scale_timing.txt, `kelime{i}-` hyphen-sonekli,
    ust-uste-binen bloklar, DIALOGUE, 7 tekrar/medyan) olculen degerler:

        n=500  -> 3.443 ms
        n=1000 -> 9.271 ms
        n=2000 -> 27.069 ms

    K19, gruplama yoluna (`_group`) YENI bir fonksiyon cagrisi ekledi
    (`_group_rejection_reason` -- ki `_should_group` de zaten bunu
    cagiriyordu, K19 SADECE `_group`'un da onu bir kez daha cagirmasini
    +bazi cift-red durumlarinda bir `dataclasses.replace` ekliyor, ikisi
    de O(1)/dongu). Beklenti: buyume SINIFI degismez, sabit bir kat
    ekstra iş olabilir. Gevsek bir ust sinir (TUR 2 degerinin 1.5 kati)
    ile dogrudan sinanir -- AYNI veri sekli (`kelime{i}-`) kullanilir."""
    tur2_medyan_ms = {500: 3.443, 1000: 9.271, 2000: 27.069}
    olculen: dict[int, float] = {}
    for n in (500, 1000, 2000):
        bloklar = [blk(f"kelime{i}-", 100, 100, w=50, h=20) for i in range(n)]
        olculen[n] = _timed_normalize_ms(bloklar, OcrPreset.DIALOGUE, tekrar=7)

    for n, tur2_ms in tur2_medyan_ms.items():
        assert olculen[n] < tur2_ms * 1.5, (
            f"n={n} icin TUR 3 medyan {olculen[n]:.3f}ms, TUR 2'nin "
            f"({tur2_ms}ms) 1.5 katindan FAZLA -- K19 olcegi belirgin "
            f"sekilde kotulestirmis olabilir. Tum olculenler: {olculen}"
        )


def test_olcek_tur4_ile_karsilastirma_iki_gecisli_group_kotulesmemis() -> None:
    """TUR 5 DOGRUDAN KARSILASTIRMA (env.md TUR 5 / MERCEK C, "Olcek"):
    TUR 4'te AYNI yontemle (`kelime{i}-` hyphen-sonekli, ust-uste-binen
    bloklar, DIALOGUE, medyan) olculen degerler:

        n=500 -> 2.744 ms · n=1000 -> 7.032 ms · n=2000 -> 20.138 ms

    K23/K24 `_group`'u IKI GECISE bolduyordu (bolumleme + gorunum). Riski:
    (a) ikinci pas `groups` uzerinde EK bir O(g) dongu ekliyor (g = grup
    sayisi <= n), (b) `pure_length_boundaries` her sinirda EK bir
    `_group_rejection_reason(tail, nxt, ignore_length=True)` cagrisi
    yapiyor -- tur 4'te bu cagri `current.speaker is not None` kosuluyla
    korunuyordu, tur 5'te o kosul KALDIRILDI, yani cagri DAHA SIK olabilir.
    Beklenti: ikisi de O(1)/sinir, buyume SINIFI degismez.

    Gevsek ust sinir (TUR 4 degerinin 1.6 kati -- bu makinede n=2000
    olcumunun min/max yayilimi ~%10, tolerans onun ustunde)."""
    tur4_medyan_ms = {500: 2.744, 1000: 7.032, 2000: 20.138}
    olculen: dict[int, float] = {}
    for n in (500, 1000, 2000):
        bloklar = [blk(f"kelime{i}-", 100, 100, w=50, h=20) for i in range(n)]
        olculen[n] = _timed_normalize_ms(bloklar, OcrPreset.DIALOGUE, tekrar=7)

    for n, tur4_ms in tur4_medyan_ms.items():
        assert olculen[n] < tur4_ms * 1.6, (
            f"n={n} icin TUR 5 medyan {olculen[n]:.3f}ms, TUR 4'un "
            f"({tur4_ms}ms) 1.6 katindan FAZLA -- iki-gecisli `_group` "
            f"olcegi kotulestirmis olabilir. Tum olculenler: {olculen}"
        )


def test_olcek_CJK_gruplama_yolu_n2000_kuadratik_degil() -> None:
    """TUR 5 (yeni): yukaridaki olcum `kelime{i}-` kullaniyor, yani
    hyphen kurali (K5) TUM bloklari adim 3'te TEK ogeye indiriyor --
    `_group` (dolayisiyla K23/K24'un IKI gecisi) o veri seklinde neredeyse
    HIC calismaz. Bu test iki-gecisli `_group`'u GERCEKTEN yuklemek icin
    hyphen'siz, CJK, ust-uste-binen ve HER 4. blogu ETIKETLI (yani miras
    sorgusunu tetikleyen) bir girdi kullanir."""
    JP = "これは長い台詞であり折り返されている"
    olculen: dict[int, float] = {}
    for n in (500, 2000):
        bloklar = [
            blk(("勇者：" + JP) if i % 4 == 0 else JP, 100, 100 + i, w=300, h=20) for i in range(n)
        ]
        olculen[n] = _timed_normalize_ms(bloklar, OcrPreset.DIALOGUE, tekrar=5)
    oran = (olculen[2000] + 0.05) / (olculen[500] + 0.05)
    assert oran < 20.0, (
        f"CJK gruplama yolunda 500->2000 (4x blok) icin sure orani "
        f"{oran:.1f}x -- iki-gecisli `_group` kuadratik davranmis olabilir "
        f"(olculen={olculen})"
    )


# ---------------------------------------------------------------------------
# 13. presets.py genisletilebilirligi (TUR 1'den DEGISMEDI -- regresyon avi)
#     + K17'nin adlandirilmis sabiti dogru yerde/turde mi?
# ---------------------------------------------------------------------------


def test_regresyon_presets_tum_on_ayarlar_AYNI_dataclass_turunu_kullanir() -> None:
    turler = {type(get_params(p)) for p in OcrPreset}
    assert turler == {NormalizerParams}


def test_regresyon_presets_yeni_alan_eklemek_MEVCUT_ornekleri_BOZMADAN_mumkun() -> None:
    from dataclasses import fields, replace as dc_replace

    genisletilmis = dc_replace(get_params(OcrPreset.DIALOGUE))
    assert genisletilmis == get_params(OcrPreset.DIALOGUE)
    alan_adlari = {f.name for f in fields(NormalizerParams)}
    assert alan_adlari == {
        "confidence_threshold",
        "max_vertical_gap_ratio",
        "max_group_chars",
        "should_group",
    }
    assert "scale_factor" not in alan_adlari
    assert "contrast_preprocessing" not in alan_adlari


def test_regresyon_get_params_bilinmeyen_preset_degeri_icin_value_error_verir() -> None:
    with pytest.raises(ValueError):
        get_params("bilinmeyen-on-ayar")  # type: ignore[arg-type]


def test_k17_sabiti_tuple_tipinde_ve_purity_check_ile_tutarli() -> None:
    """K17'nin adlandirilmis sabiti `presets.py`de -- purity_check.py'nin
    'modul duzeyinde mutable global yok' denetimiyle tutarli olmasi icin
    `tuple` olmali, `list`/`set` DEGIL (bu modulun kendi docstring notu)."""
    assert isinstance(SPEAKER_LABEL_SEPARATORS, tuple)
    assert SPEAKER_LABEL_SEPARATORS == (":", "：")
    for sep in SPEAKER_LABEL_SEPARATORS:
        assert len(sep) == 1, "cagiran taraf (_find_speaker_separator) TEK codepoint varsayiyor"


# ---------------------------------------------------------------------------
# 14. TUR 3 -- K19 SINIRLARI + K20 bagimsiz dogrulama (gorev tanimi madde 1).
#     Zincirleme davranis, dil yogunlugu VE (bloke edici) yeni bir bulgu:
#     length reason'i geometri kontrollerinden ONCE calistigi icin, AYNI
#     ANDA hem uzunluk hem gercek bir geometrik sinir varsa kod yanlislikla
#     miras UYGULUYOR.
# ---------------------------------------------------------------------------


def test_k19_uc_parcaya_bolunen_govdede_HER_kuyruk_miras_alir_sadece_ilk_degil() -> None:
    """SINIR SORUSU (gorev tanimi madde 1): "uc ve daha fazla parcaya
    bolunen bir grupta HER kuyruk mu miras aliyor, yoksa sadece ilki mi?"
    Govdeyi, ust uste EN AZ IKI kez `max_group_chars`'i (dialogue: 280)
    asacak kadar uzatir (>= 3 grup zorunlu) -- gecen zincirdeki HER
    grubun (ilkinin disinda TUMU kuyruk) speaker'i 'Ada' MI kaliyor,
    yoksa zincir bir noktada kopup `None`'a mi doner?"""
    cap = get_params(OcrPreset.DIALOGUE).max_group_chars
    etiket = blk("Ada:", 10, 0)
    n = (cap // 60) * 2 + 5  # en az 2 uzunluk-bolunmesi -> en az 3 grup
    govde = [blk("x" * 60, 10, 22 * (i + 1)) for i in range(n)]
    out = normalize([etiket, *govde], OcrPreset.DIALOGUE)
    assert len(out) >= 3, f"test varsayimi gecersiz -- yalniz {len(out)} grup olustu, n'i artir"
    assert all(s.speaker == "Ada" for s in out), (
        f"K19 SINIRI IHLAL: {len(out)} gruptan bazilari 'Ada'yi miras almiyor -- "
        f"{[(s.speaker, len(s.text)) for s in out]}"
    )
    # K8: her blok TAM OLARAK bir segmente dagitilmis (ayrik, tekrarsiz, artan):
    all_src = sorted(i for s in out for i in s.source_blocks)
    assert all_src == list(range(n + 1))


def test_k19_uzunluk_sonra_geometrik_bolunme_ZINCIR_KOPAR() -> None:
    """SINIR SORUSU: uzunluk VE geometrik bolunme AYNI zincirde ARKA ARKAYA
    (ama AYNI ciftte DEGIL -- ayri, ardisik ciftlerde) olursa ne olur?
    1. cift: uzunluk asimi (miras -- Ada). 2. cift: (yeni, mirasli grup)
    ile bir SONRAKI oge arasinda GERCEK bir buyuk dikey bosluk -- bu
    saf bir geometrik red, zincir BURADA kopmali (miras YOK, `None`)."""
    params = get_params(OcrPreset.DIALOGUE)
    cap = params.max_group_chars
    etiket = blk("Ada:", 10, 0)
    b1 = blk("y" * (cap - 10), 10, 22, h=20)  # etiket+b1 -- uzunluga cok yakin
    b2 = blk("kisa govde parcasi", 10, 44, h=20)  # b1+b2 -- UZUNLUK asimi -> miras (Ada)
    gap_y = 44 + 20 + int(params.max_vertical_gap_ratio * 20) + 200
    b3 = blk("uzak parca, buyuk bosluk sonrasi", 10, gap_y, h=20)  # GEOMETRIK red -- miras YOK

    out = normalize([etiket, b1, b2, b3], OcrPreset.DIALOGUE)
    assert len(out) == 3
    assert out[0].speaker == "Ada"  # grup1: etiket+b1 (dogal)
    assert out[1].speaker == "Ada", "K19: b2 UZUNLUK-kaynakli miras almali"
    assert out[2].speaker is None, (
        "K19 SINIRI: b3, GEOMETRIK bir bosluktan sonra geliyor -- zincirin "
        "onceki (mirasli) speaker'ini TASIMAMALI, None KALMALI"
    )


def test_k19_geometrik_bolunme_sonrasi_grubun_KENDI_ic_uzunluk_bolunmesi_uydurma_URETMEZ() -> None:
    """SINIR SORUSU (tersi yon): bir grup GEOMETRIK bir bolunmeyle
    speaker=None olarak basladiktan SONRA, o grubun KENDI ICINDE ayrica
    bir UZUNLUK bolunmesi olursa -- K19 YOKTAN bir konusmaci UYDURMAMALI.
    current.speaker zaten None ise (`current.speaker is not None` sarti
    False), miras UYGULANMAZ -- zincirin devami da None kalmali."""
    cap = get_params(OcrPreset.DIALOGUE).max_group_chars
    params = get_params(OcrPreset.DIALOGUE)
    etiket = blk("Ada:", 10, 0)
    b0 = blk("kisa ilk parca", 10, 22, h=20)
    gap_y = 22 + 20 + int(params.max_vertical_gap_ratio * 20) + 200
    n = (cap // 60) * 2 + 5
    govde2 = [blk("z" * 60, 10, gap_y + 22 * i, h=20) for i in range(n)]

    out = normalize([etiket, b0, *govde2], OcrPreset.DIALOGUE)
    assert len(out) >= 4, "test varsayimi gecersiz -- ikinci govde yeterince bolunmedi"
    assert out[0].speaker == "Ada"
    assert all(s.speaker is None for s in out[1:]), (
        "K19 SINIRI IHLAL: geometrik-kaynakli None grubunun kendi ic uzunluk "
        f"bolunmeleri UYDURMA bir speaker uretmis -- {[(s.speaker, len(s.text)) for s in out[1:]]}"
    )


def test_k19_iki_farkli_konusmacinin_kendi_ic_uzunluk_bolunmeleri_KARISMAZ() -> None:
    """SINIR SORUSU: Ada VE Efe ardisik konusuyor, Efe'nin govdesi KENDI
    ICINDE uzunluk siniriyla bolunuyor -- Efe'nin kuyruklari 'Efe'yi miras
    almali, ASLA 'Ada'ya sizmamali (K9'un konusmaci sinirinin K19'un
    miras zincirini EZMEDIGini dogrudan sinar)."""
    cap = get_params(OcrPreset.DIALOGUE).max_group_chars
    etiket_ada = blk("Ada:", 10, 0)
    govde_ada = blk("Ada govdesi kisa", 10, 22, h=20)
    etiket_efe = blk("Efe:", 10, 44, h=20)
    n = (cap // 60) * 2 + 5
    govde_efe = [blk("q" * 60, 10, 66 + 22 * i, h=20) for i in range(n)]

    out = normalize([etiket_ada, govde_ada, etiket_efe, *govde_efe], OcrPreset.DIALOGUE)
    assert len(out) >= 4
    assert out[0].speaker == "Ada"
    assert all(s.speaker == "Efe" for s in out[1:]), (
        f"K19 SINIRI IHLAL: Efe govdesinin kuyruklari 'Efe' disinda bir deger "
        f"tasiyor -- {[s.speaker for s in out[1:]]} (Ada'ya sizma riski)"
    )


def test_k19_japonca_gercek_cumlelerle_zorunlu_coklu_bolunme_HER_ZAMAN_blok_sinirinda() -> None:
    """SINIR SORUSU (gorev tanimi madde 1, Japonca): karakter basina daha
    yogun anlam tasidigi icin `max_group_chars` Japonca'da daha CABUK
    doluyor -- bu, bolunme NOKTASININ bir cumlenin/karakterin ORTASINA
    denk gelmesine yol acar mi? HAYIR OLMALI: gruplama TextBlock (satir)
    GRANULERLIGINDE calisir (`_group_rejection_reason` `a`/`b` iki TAM
    oge/grup metnini karsilastirir, tek bir ogeyi asla BOLMEZ) -- bu
    yuzden her bolunme, ozgun bloklarin TAMAMI arasinda olmali, hicbir
    zaman bir cumlenin/karakterin icinde degil. Gercek (tekrarli) Japonca
    cumlelerle DIALOGUE cap'ini (280) BILINCLI olarak asarak dogrulanir."""
    cap = get_params(OcrPreset.DIALOGUE).max_group_chars
    etiket_jp = blk("勇者:", 10, 0)
    taban_cumleler = [
        "こんにちは、世界。今日はいい天気ですね。",
        "魔王を倒すために、私たちは旅を続けなければならない。",
        "この剣は伝説の武器であり、多くの勇者がこれを求めてきた。",
        "東京から遠く離れたこの土地で、私たちは新たな仲間と出会った。",
        "力を合わせれば、どんな困難も乗り越えられるだろう。",
        "火の国の王は、古の言い伝えを信じていなかった。",
    ]
    cumleler = (taban_cumleler * 4)[:20]
    govde = [blk(s, 10, 22 * (i + 1), h=20) for i, s in enumerate(cumleler)]
    toplam = sum(len(s) for s in cumleler) + (len(cumleler) - 1)
    assert toplam > cap * 1.5, "test varsayimi gecersiz -- yeterince uzun degil"

    out = normalize([etiket_jp, *govde], OcrPreset.DIALOGUE)
    assert len(out) >= 2, "test varsayimi gecersiz -- hic bolunme olusmadi"
    assert all(s.speaker == "勇者" for s in out), "K19 Japonca'da da HER kuyrukta calismali"

    # HER parca, orijinal cumlelerin TAM (bolunmemis) bir alt-dizisinin
    # bosluklarla birlestirilmis hali olmali -- hicbir fragman "yarim cumle"
    # OLMAMALI (splits HER ZAMAN blok/cumle sinirinda, asla karakter ortasinda):
    gecerli_parcalar = set(cumleler)
    for s in out:
        for parca in s.text.split(" "):
            if parca:
                assert parca in gecerli_parcalar, (
                    f"bolunme bir cumlenin ORTASINDAN gecti -- yarim fragman: {parca!r}"
                )


# --- TUR 3'UN BLOKE EDICI BULGUSU -- TUR 4'te (K21) DUZELTILDI -----------
# Asagidaki iki test TUR 3'te HATALI davranisi PIN ediyordu; K21 (sef_karari-
# tur4.md) `_group_rejection_reason`'a `ignore_length` parametresi ekleyerek
# bulguyu kapatti. Testler TUR 5'te YENIDEN YAZILDI: assertion'lar TERS
# CEVRILDI, artik DUZELMIS davranisi (bilesik sinirda MIRAS YOK) dogruluyorlar.


def test_DUZELDI_K21_uzunluk_VE_buyuk_geometrik_bosluk_AYNI_ANDA_ise_miras_ARTIK_YOK() -> None:
    """TUR 3'te BLOKE EDICI olarak raporladigim bulgunun DUZELDIGINI
    dogrular (K21, sef_karari-tur4.md; sef bulguyu kendi eliyle yeniden
    uretti).

    ESKI DAVRANIS (tur 3): `_group_rejection_reason` kontrolleri SABIT
    sirada (`speaker -> length -> height -> gap -> width -> overlap`)
    calisip YALNIZ ILK basarisiz kontrolun kodunu donduruyordu; `length`
    TUM geometri kontrollerinden ONCE geldigi icin, bir cift AYNI ANDA hem
    `max_group_chars`'i asiyor hem GERCEK bir geometrik kopusa sahipse kod
    `"length"` donduruyor ve K19 YANLISLIKLA miras uyguluyordu.

    YENI DAVRANIS (K21): `reason` HALA `"length"` (kontrol SIRASI
    BILINCLI olarak DEGISMEDI -- `speaker`'in `length`'ten once gelmesi
    K15'in son iki satiri icin gerekli), ama `_group` miras kararini artik
    `reason == "length"` KARSILASTIRMASIYLA VERMIYOR: ayni cifti
    `ignore_length=True` ile IKINCI KEZ degerlendiriyor. Uzunluk DISINDA
    bir engel de varsa (burada `"gap"`) MIRAS UYGULANMIYOR.

    Bu test hem MEKANIZMAYI (`ignore_length` ikinci cagrisi) hem UCTAN
    UCA davranisi (`normalize`) sabitler."""
    params = get_params(OcrPreset.DIALOGUE)
    cap = params.max_group_chars

    a = blk("Ada:", 10, -22, h=20)
    b0 = blk("x" * (cap - 5), 10, 0, h=20)
    huge_gap_y = 0 + 20 + int(params.max_vertical_gap_ratio * 20) + 500
    b1 = blk("y" * 50, 10, huge_gap_y, h=20)

    item_a = _Item(text="x" * (cap - 5), bbox=Rect(x=10, y=0, w=300, h=20), speaker="Ada", source_blocks=(1,))
    item_b = _Item(text="y" * 50, bbox=Rect(x=10, y=huge_gap_y, w=300, h=20), speaker=None, source_blocks=(2,))

    # Kontrol SIRASI degismedi -- ilk basarisiz kontrol HALA "length":
    assert _group_rejection_reason(item_a, item_b, params) == "length"
    # ...ama K21'in IKINCI (uzunluk-atlamali) sorgusu GERCEK kopusu GORUYOR:
    assert _group_rejection_reason(item_a, item_b, params, ignore_length=True) == "gap", (
        "K21 mekanizmasi: uzunluk kontrolu atlandiginda GERCEK engel (gap) "
        "gorunur olmali -- gorunmuyorsa BULGU geri dondu"
    )
    # Kontrol: ayni geometri KISA metinle de reddediyor (kopus GERCEK):
    item_a_kisa = _Item(text="kisa", bbox=Rect(x=10, y=0, w=300, h=20), speaker="Ada", source_blocks=(1,))
    item_b_kisa = _Item(text="kisa2", bbox=Rect(x=10, y=huge_gap_y, w=300, h=20), speaker=None, source_blocks=(2,))
    assert _group_rejection_reason(item_a_kisa, item_b_kisa, params) == "gap"

    # UCTAN UCA: b1 ARTIK Ada'ya atfedilmiyor.
    out = normalize([a, b0, b1], OcrPreset.DIALOGUE)
    assert len(out) == 2
    assert out[0].speaker == "Ada"
    assert out[1].speaker is None, (
        "TUR 3 BULGUSU GERI DONDU: bilesik sinirda (uzunluk + GERCEK dikey "
        "kopus) kuyruk YINE miras aliyor -- sef_karari-tur3.md tablosunun "
        "'Geometrik bosluk -> None kalir' satirinin ihlali"
    )
    # K23 (tur 5): bu senaryoda bolumleme miras acik/kapali BIREBIR ayni.
    off = _normalize_impl([a, b0, b1], OcrPreset.DIALOGUE, apply_inheritance=False)
    assert [s.source_blocks for s in out] == [s.source_blocks for s in off]


def test_DUZELDI_K21_uzunluk_VE_yozlasmis_yukseklik_AYNI_ANDA_ise_miras_ARTIK_YOK() -> None:
    """Ayni bulgunun ikinci varyantinin (K16 -- yozlasmis geometri)
    DUZELDIGINI dogrular. `reason` HALA `"length"` (sira degismedi) ama
    `ignore_length=True` ikinci sorgusu `"height"` donuyor ve miras
    UYGULANMIYOR -- K16'nin "yozlasmis geometride karar VERILEMEZ" ilkesi
    artik SPEAKER ATFINA da uygulaniyor."""
    params = get_params(OcrPreset.DIALOGUE)
    cap = params.max_group_chars

    item_a = _Item(text="x" * (cap - 5), bbox=Rect(x=10, y=0, w=300, h=20), speaker="Ada", source_blocks=(0,))
    item_b = _Item(text="y" * 50, bbox=Rect(x=10, y=20, w=300, h=0), speaker=None, source_blocks=(1,))
    assert _group_rejection_reason(item_a, item_b, params) == "length"
    assert _group_rejection_reason(item_a, item_b, params, ignore_length=True) == "height", (
        "K21 mekanizmasi: uzunluk atlandiginda yozlasmis yukseklik gorunur olmali"
    )

    etiket = TextBlock(text="Ada:", bbox=Rect(x=10, y=-22, w=300, h=20), confidence=0.9)
    b0 = TextBlock(text="x" * (cap - 5), bbox=Rect(x=10, y=0, w=300, h=20), confidence=0.9)
    b1 = TextBlock(text="y" * 50, bbox=Rect(x=10, y=20, w=300, h=0), confidence=0.9)
    out = normalize([etiket, b0, b1], OcrPreset.DIALOGUE)
    assert len(out) == 2
    assert out[1].speaker is None, (
        "TUR 3 BULGUSU GERI DONDU: yozlasmis-geometrili kuyruk YINE miras aliyor"
    )


# ---------------------------------------------------------------------------
# 15. K20 -- alti karakterlik NFKC listesinin BAGIMSIZ tam Unicode taramasi
#     (gorev tanimi madde 1: "listeyi kendi taramanla dogrula"). Bu, bolum
#     3'teki `test_k18_nfkc_taramasi_...` ile AYNI sonucu, TUR 3'un KENDI
#     bagimsiz taramasiyla (farkli kod, ayni sonuc) yeniden dogrular.
# ---------------------------------------------------------------------------


def test_k20_bagimsiz_tam_unicode_taramasi_docstringteki_alti_karakterle_TAM_ORTUSUR() -> None:
    """sef_karari-tur3.md'nin K20 karari, normalizer.py docstring'ine
    ALTI karakterlik bir liste koydu (U+FE15, FE16, FE56, FE57, FF01,
    FF1F). Bu test o listeyi, dosyanin BASKA HICBIR YERINDEKI koddan
    (bolum 3'teki tarama dahil) BAGIMSIZ, SIFIRDAN yazilmis bir tam
    Unicode taramasiyla (0x0-0x10FFFF, surrogate araligi haric) dogrular
    -- hem ASCII '?'/'!' HEM ONCEDEN bilinen fullwidth '？'/'！' de
    listenin ICINDE (docstring'in "ASCII/fullwidth DISINDA" ifadesi
    YANILTICI olabilir -- bkz. feedback-C.md, bu BLOKE EDICI degil ama
    kayda gecen bir gozlem)."""
    docstring_listesi = {0xFE15, 0xFE16, 0xFE56, 0xFE57, 0xFF01, 0xFF1F}
    bulunanlar: set[int] = set()
    for cp in range(0x110000):
        if 0xD800 <= cp <= 0xDFFF:  # surrogate -- gecerli skaler deger degil
            continue
        ch = chr(cp)
        norm = unicodedata.normalize("NFKC", ch)
        if norm in ("?", "!") and ch not in ("?", "!"):
            bulunanlar.add(cp)
    assert bulunanlar == docstring_listesi, (
        f"BAGIMSIZ tarama docstring'deki listeyle ORTUSMUYOR -- "
        f"fazladan: {sorted(hex(c) for c in bulunanlar - docstring_listesi)}, "
        f"eksik: {sorted(hex(c) for c in docstring_listesi - bulunanlar)}"
    )
    # Docstring'in "davranis DOGRU, hepsi zararsiz Po" iddiasini da dogrula:
    for cp in docstring_listesi:
        assert unicodedata.category(chr(cp))[0] == "P"
        out = normalize([blk(chr(cp), 10, 10)], OcrPreset.MENU)
        assert [s.text for s in out] == [chr(cp)]


# ---------------------------------------------------------------------------
# 16. TUR 5 -- MERCEK C'nin TUR 5 saldiri listesi (env.md "TUR 5 mercekleri /
#     C · Sinir, kotu kullanim, dil" + sef_karari-tur5.md K23-K27).
#
#     16.1 B1'in JAPONCA yuzeyi (K23 degismezinin URUN etkisi)
#     16.2 Gorunum gecisinin CJK yuzeyi -- `speaker` Unicode BIREBIRLIGI
#     16.3 Karisik script zinciri
#     16.4 Kotu kullanim yuzeyi (`_normalize_impl`, `apply_inheritance`)
#     16.5 K24 `tail` alani (CJK)
#     16.6 K26 uyumluluk formu etiket dagilimi
#     16.7 K27 dort on ayar
#     16.8 K23 degismezi -- TESTER-C'nin KENDI fuzz'i (farkli tohum,
#          farkli dagilim, CJK agirlikli)
#
#     Olcek (n=500/1000/2000, TUR 4 tabani) bolum 12'de.
# ---------------------------------------------------------------------------

# `dialogue` cap=280; 31 karakterlik JP blogu x 10 = 310 + bosluklar -> cap
# KESIN asilir, yani grup GERCEKTEN uzunluk yuzunden boluner. (Japonca'da
# karakter basina anlam yogunlugu yuksek oldugu icin bu, ekranda cok da uzun
# olmayan bir replige karsilik gelir -- senaryo GERCEKCIDIR.)
_JP_UZUN = "これは非常に長い台詞であり物語の核心に触れる重要な部分である。"
assert len(_JP_UZUN) == 31, len(_JP_UZUN)


def _jp_govde(n: int = 10, *, y0: int = 22, adim: int = 22) -> list[TextBlock]:
    """cap'i (280) KESIN asan `n` bloklu, SIKI aralikli JP govdesi."""
    return [blk(_JP_UZUN, 10, y0 + adim * i) for i in range(n)]


def _bolumleme(
    bloklar: list[TextBlock], preset: OcrPreset = OcrPreset.DIALOGUE
) -> tuple[list, list, list, list]:
    """K23'un tanimladigi "bolumleme"yi iki kosuda karsilastirilabilir hale
    getirir: miras ACIK ve KAPALI ciktilar + ikisinin `(source_blocks, text,
    bbox, placeholders)` izdusumleri. `speaker` BILEREK izdusumun DISINDA --
    K23 tam olarak "miras YALNIZCA `speaker`'i degistirebilir" der."""
    acik = _normalize_impl(bloklar, preset, apply_inheritance=True)
    kapali = _normalize_impl(bloklar, preset, apply_inheritance=False)

    def izdusum(ss: list) -> list:
        return [(s.source_blocks, s.text, s.bbox, s.placeholders) for s in ss]

    return acik, kapali, izdusum(acik), izdusum(kapali)


# --- 16.1 B1'in JAPONCA yuzeyi ---------------------------------------------


def test_k23_B1_JAPONCA_kendi_etiketiyle_gelen_YENI_replik_AYRI_KALIR() -> None:
    """MERCEK C'nin TUR 5 birinci sorusu, JAPONCA'da: `勇者：` etiketli
    UZUN bir replik (max_group_chars'i GERCEKTEN asan) + hemen ardindan
    KENDI `勇者：` etiketiyle gelen YENI bir replik -> IKI AYRI sozce mi
    kaliyor?

    Bu, sef_karari-tur5.md B1 bulgusunun BIREBIR japonca karsiligidir.
    TUR 4'un mekanizmasinda kuyruk segment mirasla `勇者` degerini
    TASIYIP bir SONRAKI gruplama kararina GIRDI oluyordu; K15 matrisinin
    `None/Y -> hayir` satiri yanlislikla `X/X -> evet` satirina donusuyor
    ve KENDI etiketi olan YENI replik oncekinin kuyruguna YAPISIYORDU.

    BEKLENTI (K23 sonrasi): b11 (kendi `勇者：` etiketli YENI replik)
    KENDI segmenti olarak AYRI kalir; bolumleme miras acik/kapali
    BIREBIR aynidir."""
    bloklar = (
        [blk("勇者：", 10, 0)]
        + _jp_govde(10)
        + [blk("勇者：これは全く新しい台詞です。", 10, 22 + 22 * 10)]
    )
    acik, kapali, iz_acik, iz_kapali = _bolumleme(bloklar)

    # (a) K23 DEGISMEZI: bolumleme miras acik/kapali BIREBIR ayni
    assert len(acik) == len(kapali), (
        f"K23 IHLALI -- segment SAYISI miras karariyla degisti: "
        f"{len(acik)} (acik) != {len(kapali)} (kapali)"
    )
    assert iz_acik == iz_kapali, "K23 IHLALI -- bolumleme miras karariyla degisti"

    # (b) YENI replik AYRI bir segment -- son segment YALNIZ b11'den olusur
    son = acik[-1]
    assert son.source_blocks == (11,), (
        f"kendi `勇者：` etiketli YENI replik oncekinin kuyruguna YAPISTI "
        f"(B1'in japonca yuzeyi): son segment src={son.source_blocks}"
    )
    assert son.text == "これは全く新しい台詞です。"
    assert son.speaker == "勇者"

    # (c) Senaryo SAHIDEN kuruldu mu: uzunluk siniri devrede oldugu icin
    #     govde EN AZ iki segmente bolundu, ustune b11 AYRI kaldi -> >= 3.
    #     (Bu assertion ayni zamanda B1'i yakalar: b11 yapissa 2 olurdu.)
    assert len(acik) >= 3, (
        f"beklenen bolunme olusmadi ({len(acik)} segment) -- ya cap asilmadi "
        f"(senaryo kurulmadi) ya da b11 onceki gruba YAPISTI (B1 nuksetti): "
        f"{[s.source_blocks for s in acik]}"
    )


def test_k23_B1_JAPONCA_etiketsiz_kuyruk_MIRAS_ALIR_ama_bolumleme_AYNI() -> None:
    """Ayni girdi, SON blok ETIKETSIZ (yani gercek bir "devam" satiri):
    K19/K21 uyarinca kuyruk `勇者`'yi MIRAS ALIR. K23: buna RAGMEN
    bolumleme miras kapaliyken BIREBIR ayni kalir -- degisen TEK sey
    `speaker` alanidir."""
    bloklar = (
        [blk("勇者：", 10, 0)]
        + _jp_govde(10)
        + [blk("これは未ラベルの続き行です。", 10, 22 + 22 * 10)]
    )
    acik, kapali, iz_acik, iz_kapali = _bolumleme(bloklar)

    assert len(acik) >= 2, "cap asilmamis"
    assert iz_acik == iz_kapali, "K23 IHLALI -- bolumleme miras karariyla degisti"

    # Miras ACIKKEN kuyruk `勇者`; KAPALIYKEN `None`
    assert acik[-1].speaker == "勇者", f"uzunluk-tek sinirda miras YOK: {acik[-1].speaker!r}"
    assert kapali[-1].speaker is None
    # Miras SADECE None -> deger yonunde; hicbir mevcut deger DEGISMEZ
    for s_acik, s_kapali in zip(acik, kapali):
        assert s_acik.speaker == s_kapali.speaker or s_kapali.speaker is None


def test_k23_B1_JAPONCA_FARKLI_konusmaci_etiketi_miras_ALMAZ() -> None:
    """Ayni girdi, SON blok FARKLI (`魔王：`) etiketli -> K9'un ASIL
    yasagi: iki FARKLI adlandirilmis konusmaci ASLA birlesmez, ve kuyruk
    `勇者`'yi MIRAS ALMAZ (kendi etiketi var)."""
    bloklar = (
        [blk("勇者：", 10, 0)]
        + _jp_govde(10)
        + [blk("魔王：愚かな人間よ。", 10, 22 + 22 * 10)]
    )
    acik, kapali, iz_acik, iz_kapali = _bolumleme(bloklar)

    assert iz_acik == iz_kapali
    assert acik[-1].source_blocks == (11,)
    assert acik[-1].speaker == "魔王"
    assert acik[-1].text == "愚かな人間よ。"
    # Metinler karismamis: 勇者'nin metni 魔王'ye, 魔王'nin metni 勇者'ye SIZMAMIS
    for s in acik:
        if s.speaker == "魔王":
            assert "台詞" not in s.text
        if s.speaker == "勇者":
            assert "愚か" not in s.text


def test_k23_UC_KONUSMACULU_zincir_her_biri_COK_SATIRLI_ve_cap_ASIYOR() -> None:
    """MERCEK C'nin ikinci sorusu: uc konusmaculu zincir (`勇者`/`魔王`/
    `村人`), HER BIRI COK SATIRLI **VE** her birinin govdesi cap'i ASIYOR
    (yani her konusmacinin ICINDE bir uzunluk-bolunmesi var).

    Bu, mirasin HER konusmaci icinde ZINCIRLENDIGI ama konusmacilar ARASI
    sinirin ASLA gecilmedigi en zor senaryo. K23: bolumleme miras
    acik/kapali BIREBIR ayni."""
    from collections import Counter

    bloklar: list[TextBlock] = []
    y = 0
    for isim in ("勇者", "魔王", "村人"):
        bloklar.append(blk(f"{isim}：", 10, y))
        y += 22
        for _ in range(10):
            bloklar.append(blk(_JP_UZUN, 10, y))
            y += 22

    acik, kapali, iz_acik, iz_kapali = _bolumleme(bloklar)

    assert iz_acik == iz_kapali, "K23 IHLALI -- uc konusmaculu zincirde"

    sayim = Counter(s.speaker for s in acik)
    # Her konusmaci EN AZ iki segment uretmis olmali (ic uzunluk bolunmesi)
    assert sayim["勇者"] >= 2 and sayim["魔王"] >= 2 and sayim["村人"] >= 2, (
        f"beklenen ic uzunluk-bolunmeleri olusmadi: {dict(sayim)}"
    )
    # Hicbir segment atfedilemez KALMAMIS (miras zinciri her konusmaci
    # icinde SAGLAM)
    assert None not in sayim, (
        f"miras ZINCIRI koptu, atfedilemez segment kaldi: {dict(sayim)}"
    )
    # Konusmacilar BIRBIRINE KARISMAMIS: cikti 勇者* 魔王* 村人* bloklari halinde
    sira = [s.speaker for s in acik]
    beklenen_sira = sorted(sira, key=lambda sp: ("勇者", "魔王", "村人").index(str(sp)))
    assert sira == beklenen_sira, f"konusmacilar KARISTI: {sira}"
    # Metin sizintisi yok: her segment TEK konusmacinin bloklarindan gelmis
    for s in acik:
        assert len(s.source_blocks) >= 1
    # Miras KAPALIYKEN kuyruklar None -- yani mekanizma GERCEKTEN devrede
    assert any(s.speaker is None for s in kapali)


def test_k23_UC_KONUSMACULU_zincir_KISA_replikler_konusmaci_SIZMAZ() -> None:
    """Ayni uc konusmaculu zincir, cap ASILMIYOR (kisa replikler): her
    konusmaci TEK segment, hicbir konusmaci digerinin metnini yutmuyor."""
    bloklar = [
        blk("勇者：", 10, 0),
        blk("魔王を倒すために旅を続けている。", 10, 22),
        blk("この村で情報を集めたいのだ。", 10, 44),
        blk("魔王：", 10, 66),
        blk("愚かな人間よ、よく来たな。", 10, 88),
        blk("お前の旅はここで終わりだ。", 10, 110),
        blk("村人：", 10, 132),
        blk("あの、勇者様、お願いがあります。", 10, 154),
        blk("村の東の洞窟に化け物が出るのです。", 10, 176),
    ]
    acik, kapali, iz_acik, iz_kapali = _bolumleme(bloklar)

    assert iz_acik == iz_kapali
    assert [s.speaker for s in acik] == ["勇者", "魔王", "村人"]
    assert [s.source_blocks for s in acik] == [(0, 1, 2), (3, 4, 5), (6, 7, 8)]
    assert acik[0].text == "魔王を倒すために旅を続けている。 この村で情報を集めたいのだ。"
    assert acik[1].text == "愚かな人間よ、よく来たな。 お前の旅はここで終わりだ。"
    assert acik[2].text == "あの、勇者様、お願いがあります。 村の東の洞窟に化け物が出るのです。"


def test_GOZLEM_iki_AYRI_kendi_etiketli_replik_K15_satir1_ile_BIRLESIR() -> None:
    """BLOKE ETMEYEN GOZLEM (kayda geciyorum; ayrinti verdict-C.md):

    sef_karari-tur5.md'nin B1 bulgusunun URUN ETKISI cumlesi -- *"kendi
    `Ada:` etiketi olan YENI bir replik, onceki repligin kuyruguna
    yapisiyor; iki AYRI sozce TEK `Segment` oluyor"* -- K23 bu etkinin
    MIRAS YOLUYLA olusan bicimini KESIN olarak kapatir (yukaridaki
    `test_k23_B1_JAPONCA_..._AYRI_KALIR`). Ama AYNI urun etkisi MIRAS HIC
    DEVREYE GIRMEDEN de olusabilir: iki replik KENDI etiketlerini tasiyor
    VE ayni ada sahipse cift `X/X` olur ve K15 matrisinin BIRINCI satiri
    (`X/X -> EVET`) onlari birlestirir.

    BLOKE ETMIYORUM, uc sebeple:
      1. Bu bir K23 IHLALI DEGILDIR -- bolumleme miras acik/kapali
         BIREBIR aynidir (assertion asagida); miras bu yolda HIC devreye
         girmez, birlesmeyi K15 satir-1 yapar.
      2. K15 satir-1 SEFIN KENDI kararidir ve tur 2'den beri
         DEGISMEMISTIR; kod onu BIREBIR uygular. Sapma YOK.
      3. Gecerlilik alani DAR: birlesme yalniz iki repligin GEOMETRIK
         olarak komsu oldugu durumda olur. Kontrol assertion'i asagida:
         gercek bir dikey bosluk (ayri diyalog kutulari) varsa AYRI
         kalirlar. Ve komsu olduklari durumda birlesme cogunlukla
         ISTENEN davranistir -- S5.2'nin modulun VARLIK SEBEBI olarak
         verdigi "cok satirli replik, her satir konusmaci adiyla yeniden
         etiketlenmis" senaryosu tam olarak budur.

    Kayda gecirmemin sebebi: K23'un DEGISMEZI bu yolu KAPSAMIYOR, yani
    B1'in URUN semptomu K23'ten sonra TAMAMEN ortadan kalkmiyor -- sadece
    MIRAS kaynakli (uydurma degerle olusan) bicimi kalkiyor. Sef B1'i
    "iki ayri sozce tek Segment oluyor" diye tarif ettigi icin bu ayrimi
    acikca yaziyorum."""
    komsu = [
        blk("勇者：こんにちは、村人さん。", 10, 0),
        blk("勇者：今日はいい天気ですね。", 10, 22),
    ]
    acik, kapali, iz_acik, iz_kapali = _bolumleme(komsu)

    # MEVCUT davranisi PIN ediyorum (kirik kirmizi test BIRAKMIYORUM):
    assert len(acik) == 1, "davranis DEGISTI -- bu gozlem yeniden okunmali"
    assert acik[0].source_blocks == (0, 1)
    assert acik[0].speaker == "勇者"
    assert acik[0].text == "こんにちは、村人さん。 今日はいい天気ですね。"
    # K23 IHLAL EDILMIYOR -- miras bu yolda HIC devreye girmiyor:
    assert iz_acik == iz_kapali
    assert kapali[0].speaker == "勇者"  # K15'in DOGAL mirasi, K19/K21 DEGIL

    # KONTROL: gercek bir dikey bosluk varsa AYRI kalirlar
    uzak = [
        blk("勇者：こんにちは、村人さん。", 10, 0),
        blk("勇者：今日はいい天気ですね。", 10, 400),
    ]
    out = normalize(uzak, OcrPreset.DIALOGUE)
    assert [s.source_blocks for s in out] == [(0,), (1,)]
    assert [s.speaker for s in out] == ["勇者", "勇者"]


# --- 16.2 Gorunum gecisinin CJK yuzeyi -- `speaker` Unicode BIREBIRLIGI ----


@pytest.mark.parametrize(
    ("isim", "ayirac", "etiket"),
    [
        ("勇者", "：", "kanji + FULLWIDTH ayirac"),
        ("魔王", ":", "kanji + ASCII ayirac"),
        ("あい", "：", "hiragana + fullwidth"),
        ("김철수", "：", "hangul (precomposed) + fullwidth"),
        ("이영희", ":", "hangul + ascii"),
        ("Пётр", "：", "kiril (precomposed yo) + fullwidth"),
        ("Ayşe", ":", "turkce s-cedilla"),
        ("María", "：", "precomposed aksanli latin"),
        ("ｱｲｳ", ":", "HALFWIDTH katakana -- NFKC uygulanirsa DEGISIR"),
        ("ＡＢＣ", ":", "FULLWIDTH latin -- NFKC uygulanirsa ASCII olur"),
    ],
)
def test_k23_gorunum_gecisi_speaker_UNICODE_BIREBIR_kopyalanir(
    isim: str, ayirac: str, etiket: str
) -> None:
    """MERCEK C'nin ucuncu sorusu: gorunum gecisi `speaker` alanina OZGUN
    string'i mi kopyaluyor, yoksa NORMALIZE edilmis bir kopyasini mi?

    Kritik vakalar HALFWIDTH katakana (`ｱｲｳ`) ve FULLWIDTH latin (`ＡＢＣ`)
    -- ikisinin de NFKC formu KENDISINDEN FARKLIDIR. Kod bir yerde NFKC
    uygulasa (K18'in tek-karakter istisnasi NFKC KULLANIYOR, yani modulde
    bu fonksiyon MEVCUT) bu iki vakada codepoint'ler DEGISIRDI.
    BIREBIRLIK codepoint duzeyinde sinanir."""
    bloklar = [
        blk(f"{isim}{ayirac}", 10, 0),
        blk("一行目の本文です。", 10, 22),
        blk("二行目の未ラベル本文です。", 10, 44),
    ]
    out = normalize(bloklar, OcrPreset.DIALOGUE)
    assert out, f"{etiket}: hic segment uretilmedi"
    got = out[0].speaker
    assert got == isim, f"{etiket}: speaker BIREBIR degil: {got!r} != {isim!r}"
    assert [ord(c) for c in (got or "")] == [ord(c) for c in isim], (
        f"{etiket}: codepoint dizisi DEGISTI -- "
        f"{[hex(ord(c)) for c in (got or '')]} != {[hex(ord(c)) for c in isim]}"
    )
    # NFKC UYGULANMADIGINI acikca sabitle (fark eden vakalarda)
    nfkc = unicodedata.normalize("NFKC", isim)
    if nfkc != isim:
        assert got != nfkc, f"{etiket}: speaker'a NFKC UYGULANMIS ({got!r})"


@pytest.mark.parametrize("isim", ["勇者", "김철수", "ＡＢＣ", "Пётр"])
def test_k23_MIRAS_ALINAN_speaker_de_UNICODE_BIREBIR(isim: str) -> None:
    """Yukaridakinin MIRAS yoluna karsiligi: uzunluk-bolunmesinde KUYRUK
    segmentin MIRAS ALDIGI `speaker` degeri de codepoint duzeyinde BIREBIR
    mi? (Gorunum gecisi `groups[i-1].speaker`'i DOGRUDAN mi tasiyor?)"""
    bloklar = [blk(f"{isim}：", 10, 0)] + _jp_govde(12)
    out = normalize(bloklar, OcrPreset.DIALOGUE)
    assert len(out) >= 2, f"cap asilmamis, miras yolu tetiklenmedi: {len(out)}"
    for s in out:
        assert s.speaker == isim, f"miras BIREBIR degil: {s.speaker!r}"
        assert [ord(c) for c in s.speaker] == [ord(c) for c in isim]
    # Miras KAPALIYKEN gercekten None -- yani deger MIRAS yoluyla geldi
    kapali = _normalize_impl(bloklar, OcrPreset.DIALOGUE, apply_inheritance=False)
    assert any(s.speaker is None for s in kapali)


@pytest.mark.parametrize(
    ("ham", "beklenen"),
    [
        ("勇者：", "勇者"),
        ("勇者 ：", "勇者"),          # ayirac ONCESI ASCII bosluk
        (" 勇者： ", "勇者"),         # bas/son bosluk
        ("勇者　：", "勇者"),     # IDEOGRAPHIC SPACE (U+3000) ONCE
        ("勇者：　", "勇者"),     # IDEOGRAPHIC SPACE SONRA
        ("勇 者：", "勇 者"),         # IC bosluk KORUNUR (K9 izin veriyor)
    ],
)
def test_k17_fullwidth_ayracli_etiket_BOSLUK_ARTIGI_BIRAKMAZ(
    ham: str, beklenen: str
) -> None:
    """MERCEK C: fullwidth `：` ile ayrilmis etiket MIRAS ALINDIGINDA
    karakter KAYBI / BOSLUK ARTIGI olusuyor mu? Ozellikle U+3000
    (IDEOGRAPHIC SPACE) -- CJK metinlerinde SIK gorulur ve Python
    `str.strip()` onu bosluk sayar; artik BIRAKMAMASI gerekir. Ayirac
    karakterinin KENDISI de `speaker`'a sizmamalidir."""
    bloklar = [blk(ham, 10, 0), blk("本文です。", 10, 22), blk("未ラベル続き。", 10, 44)]
    out = normalize(bloklar, OcrPreset.DIALOGUE)
    assert out
    got = out[0].speaker
    assert got == beklenen, f"ham={ham!r}: speaker={got!r} != {beklenen!r}"
    assert got is not None
    assert got == got.strip(), f"BOSLUK ARTIGI: {got!r}"
    assert "：" not in got and ":" not in got, f"AYIRAC speaker'a sizdi: {got!r}"
    assert "　" not in got, f"U+3000 ARTIGI: {got!r}"


def test_GOZLEM_k9_KOMBINE_AKSANLI_isim_konusmaci_SAYILMAZ() -> None:
    """BLOKE ETMEYEN GOZLEM (dil yuzeyi; ayrinti verdict-C.md):

    `_split_speaker_label` isim karakterleri icin `ch.isalpha() or ch in
    " '-"` sarti koyar. Unicode KOMBINE aksan (ör. U+0301 COMBINING ACUTE,
    kategori `Mn`) `isalpha()` testini GECMEZ -- bu yuzden AYNI ismin NFC
    bicimi (`María`, U+00ED) konusmaci olarak TANINIRKEN NFD bicimi
    (`Mari` + U+0301 + `a`) TANINMAZ: `speaker=None` kalir VE etiketin
    KENDISI segment METNINE karisir.

    K9'un lafzi ("kalan karakterler yalniz harf/bosluk/kesme/tire")
    birebir uygulanmis, sapma YOK -- bu yuzden BLOKE ETMIYORUM. Kayda
    gecirmemin sebebi: OCR motorlarinin hangi normalizasyon bicimini
    urettigi MOTORA BAGLIDIR, ve normalizer.py'nin K9 bolumu bu daraltmayi
    BELGELEMIYOR (K5'te Unicode tire varyantlari icin ACIKCA yapildigi
    gibi bir "kapsam disi" notu YOK). Kayip GUVENLI yonde: sessiz UYDURMA
    degil, sessiz KAYIP -- ve etiket metinde KALDIGI icin bilgi tamamen
    yok olmuyor."""
    nfc = "María:"                      # 'María:' (precomposed)
    nfd = "María:"                     # 'María:' (kombine aksan)
    assert unicodedata.normalize("NFC", nfd) == nfc
    assert nfc != nfd  # gercekten farkli codepoint dizileri

    govde = "body line one."
    out_nfc = normalize([blk(nfc, 10, 0), blk(govde, 10, 22)], OcrPreset.DIALOGUE)
    out_nfd = normalize([blk(nfd, 10, 0), blk(govde, 10, 22)], OcrPreset.DIALOGUE)

    # NFC: konusmaci AYIKLANIYOR
    assert out_nfc[0].speaker == nfc[:-1]
    assert out_nfc[0].text == govde
    # NFD: konusmaci AYIKLANMIYOR ve etiket METNE karisiyor (MEVCUT davranis)
    assert out_nfd[0].speaker is None, "davranis DEGISTI -- gozlem yeniden okunmali"
    assert out_nfd[0].text == f"{nfd} {govde}"
    # Sessiz UYDURMA yok, sessiz SILME yok -- kayip yalnizca `speaker` alaninda
    assert nfd[:-1] in out_nfd[0].text


# --- 16.3 Karisik script zinciri -------------------------------------------


@pytest.mark.parametrize(
    ("etiket", "govde", "aciklama"),
    [
        (
            "勇者：",
            [
                "This is the first line of an English body.",
                "and this is the unlabeled continuation line.",
            ],
            "JAPONCA etiket + LATIN govde",
        ),
        (
            "김철수：",
            ["これは日本語の本文です。", "これは未ラベルの続きです。"],
            "KORECE etiket + JAPONCA govde",
        ),
        (
            "Hero：",
            ["日本語とEnglishが混ざったmixed本文。", "続きのmixed行です。"],
            "LATIN etiket + FULLWIDTH ayirac + KARISIK govde",
        ),
        (
            "魔王:",
            ["Кириллица и 日本語 вместе.", "продолжение строки здесь."],
            "JAPONCA etiket + ASCII ayirac + KIRIL/JP karisik govde",
        ),
    ],
)
def test_karisik_script_zinciri_etiket_ve_govde_AYRI_YAZI_SISTEMLERINDE(
    etiket: str, govde: list[str], aciklama: str
) -> None:
    """MERCEK C: karisik script zinciri -- etiket bir yazi sisteminde,
    govde BASKA bir yazi sisteminde. Cokme, sessiz sacmalama, karakter
    kaybi veya konusmaci kaybi var mi? Bolumleme K23'e uyuyor mu?"""
    bloklar = [blk(etiket, 10, 0)] + [
        blk(t, 10, 22 + 22 * i) for i, t in enumerate(govde)
    ]
    acik, kapali, iz_acik, iz_kapali = _bolumleme(bloklar)

    assert len(acik) == 1, f"{aciklama}: {len(acik)} segment (1 beklenirdi)"
    beklenen_isim = etiket[:-1]
    assert acik[0].speaker == beklenen_isim, f"{aciklama}: {acik[0].speaker!r}"
    # Govde metni BIREBIR korunmus (yalniz K1/K5 blok-arasi birlestirmesi)
    assert acik[0].text == " ".join(govde), f"{aciklama}: {acik[0].text!r}"
    assert acik[0].source_blocks == (0, 1, 2)
    assert iz_acik == iz_kapali


def test_karisik_script_UZUNLUK_bolunmesinde_de_miras_calisir() -> None:
    """Karisik script + uzunluk bolunmesi BIRLIKTE: JP etiket + LATIN
    govde cap'i asiyor -> kuyruk JP ismi MIRAS ALIR ve Unicode BIREBIR
    kalir. (Etiketin ve govdenin AYRI yazi sistemlerinde olmasi miras
    yolunu ETKILEMEMELI.)"""
    lat = "This is a fairly long English sentence used to fill the character budget."
    bloklar = [blk("勇者：", 10, 0)] + [blk(lat, 10, 22 + 22 * i) for i in range(6)]
    acik, kapali, iz_acik, iz_kapali = _bolumleme(bloklar)

    assert len(acik) >= 2, f"cap asilmamis: {[len(s.text) for s in acik]}"
    assert iz_acik == iz_kapali
    assert all(s.speaker == "勇者" for s in acik), [s.speaker for s in acik]
    assert all(
        [ord(c) for c in (s.speaker or "")] == [0x52C7, 0x8005] for s in acik
    ), [s.speaker for s in acik]
    assert any(s.speaker is None for s in kapali)
    # LATIN govde metni bozulmamis
    assert all(lat.split()[0] in s.text for s in acik)


# --- 16.4 Kotu kullanim yuzeyi ---------------------------------------------


def test_kotu_kullanim_normalize_impl_GENEL_APIye_SIZMAMIS() -> None:
    """MERCEK C, kotu kullanim: K23'un test kancasi (`_normalize_impl`)
    GENEL API'ye SIZMIS mi? `__all__`'da var mi? `normalize`'in imzasi
    degismis mi? (sef_karari-tur5.md K23: "test kancasi ... genel API'ye
    SIZMAYACAK".)"""
    import inspect

    import src.ocr.normalizer as mod

    # (a) __all__ SADECE `normalize` icerir, tuple'dir (purity_check ile uyum)
    assert mod.__all__ == ("normalize",), mod.__all__
    assert isinstance(mod.__all__, tuple)
    assert "_normalize_impl" not in mod.__all__
    assert "_group" not in mod.__all__

    # (b) PEP8 private: alt cizgiyle basliyor -> `from ... import *` almaz
    assert mod._normalize_impl.__name__.startswith("_")

    # (c) `normalize`'in DIS imzasi TUR 5'te DEGISMEDI -- iki konumsal
    #     parametre, keyword-only parametre YOK, bayrak DISARIYA ACILMIYOR
    sig = inspect.signature(mod.normalize)
    assert list(sig.parameters) == ["blocks", "preset"], sig
    assert all(
        p.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
        for p in sig.parameters.values()
    ), sig
    with pytest.raises(TypeError):
        mod.normalize([], OcrPreset.DIALOGUE, apply_inheritance=False)  # type: ignore[call-arg]

    # (d) `_normalize_impl`'de bayrak KEYWORD-ONLY ve VARSAYILANI True --
    #     yani konumsal olarak yanlislikla `False` GECILEMEZ
    isig = inspect.signature(mod._normalize_impl)
    p = isig.parameters["apply_inheritance"]
    assert p.kind is inspect.Parameter.KEYWORD_ONLY, p.kind
    assert p.default is True
    with pytest.raises(TypeError):
        mod._normalize_impl([], OcrPreset.DIALOGUE, False)  # type: ignore[misc]

    # (e) `_group`'ta da ayni disiplin
    gsig = inspect.signature(mod._group)
    gp = gsig.parameters["apply_inheritance"]
    assert gp.kind is inspect.Parameter.KEYWORD_ONLY
    assert gp.default is True


def test_kotu_kullanim_apply_inheritance_YALNIZCA_DENETIM_ICIN_isaretli() -> None:
    """MERCEK C: `apply_inheritance=False` "yalnizca denetim icin" diye
    ISARETLI mi -- yoksa bir sonraki ajani (OCR motoru, pipeline) onu bir
    DAVRANIS DUGMESI sanmaya davet ediyor mu?"""
    import src.ocr.normalizer as mod

    impl_doc = mod._normalize_impl.__doc__ or ""
    normalize_doc = mod.normalize.__doc__ or ""
    group_doc = mod._group.__doc__ or ""

    # (a) `_normalize_impl` docstring'i bayragin amacini SINIRLANDIRIYOR
    assert "SADECE" in impl_doc
    assert "DENETIM" in impl_doc
    assert "K23" in impl_doc
    # (b) genel API'ye acilmadigi ACIKCA yaziyor
    assert "SIZMAZ" in impl_doc or "sizmaz" in impl_doc
    assert "ACMAZ" in impl_doc or "acmaz" in impl_doc
    # (c) mesru cagiran ADIYLA yaziyor -- kim cagirabilir, belirsiz DEGIL
    assert "test_normalizer.py" in impl_doc
    # (d) `normalize` docstring'i (bir sonraki ajanin OKUYACAGI yer)
    #     kancanin nerede oldugunu VE buraya sizmadigini soyluyor
    assert "_normalize_impl" in normalize_doc
    assert "SIZMAZ" in normalize_doc or "sizmaz" in normalize_doc
    # (e) `_group`'un IKI GECISI belgelenmis -- yanlis anlamaya davet yok
    assert "olumleme gecisi" in group_doc
    assert "oruntu gecisi" in group_doc


def test_kotu_kullanim_apply_inheritance_False_SESSIZCE_YANLIS_sonuc_VERMEZ() -> None:
    """Kotu kullanimin SONUCU: bir sonraki ajan yanlislikla
    `apply_inheritance=False` ile cagirsa ne KAYBEDER? Kayip SADECE
    `speaker` alaninda (bazi segmentler `None` kalir) olmali; metin, bbox,
    bolumleme ve placeholder DEGISMEMELI. Yani kotu kullanim SESSIZCE
    YANLIS bir sonuc degil, DAHA AZ bilgi tasiyan ama DOGRU bir sonuc
    uretir -- API bu yonde GUVENLI bozulur."""
    bloklar = (
        [blk("勇者：", 10, 0)]
        + _jp_govde(10)
        + [blk("これは未ラベルの続き行です。", 10, 22 + 22 * 10)]
    )
    acik, kapali, iz_acik, iz_kapali = _bolumleme(bloklar)
    assert iz_acik == iz_kapali
    farklar = [
        (i, a.speaker, k.speaker)
        for i, (a, k) in enumerate(zip(acik, kapali))
        if a.speaker != k.speaker
    ]
    assert farklar, "senaryo mirasi tetiklemedi -- test bir sey sinamiyor"
    for _i, a_sp, k_sp in farklar:
        assert k_sp is None and a_sp is not None, (a_sp, k_sp)


# --- 16.5 K24 `tail` alani (CJK) -------------------------------------------


def test_k24_CJK_tail_ile_BIRLESIK_bbox_ZIT_sonuc_verir() -> None:
    """K24'un alani, CJK govdede: grubun EN ALTA uzanan ogesi grubun
    BASINDA ise, birlesik `bbox`'in `bottom`'u kuyruktan COK asagidadir ve
    `gap` hesabi YANLISLIKLA kucuk/negatif cikar -- GERCEK kopusu GIZLER.
    `tail` ile ayni sorgu GERCEK kopusu GORUR. Iki sorgunun ZIT sonuc
    verdigini `_group_rejection_reason` duzeyinde SABITLER."""
    params = get_params(OcrPreset.DIALOGUE)
    # Grubun BASINDAKI oge COK asagi uzaniyor (h=400) -> birlesik bottom=400
    birlesik = _Item(
        text=_JP_UZUN * 2,
        bbox=Rect(x=10, y=0, w=300, h=400),
        speaker="勇者",
        source_blocks=(0, 1),
    )
    # Grubun KUYRUGU (birlesime en son katilan HAM oge) kisa ve YUKARIDA
    kuyruk = _Item(
        text=_JP_UZUN,
        bbox=Rect(x=10, y=10, w=300, h=20),
        speaker=None,
        source_blocks=(1,),
    )
    # Aday: kuyrugun COK altinda, ama birlesik kutunun ICINDE
    aday = _Item(
        text=_JP_UZUN * 8,
        bbox=Rect(x=10, y=200, w=300, h=20),
        speaker=None,
        source_blocks=(2,),
    )
    assert birlesik.bbox.bottom == 400 and kuyruk.bbox.bottom == 30

    # Ana birlestirme karari `current` (birlesik) ile verilir -> uzunluk reddi
    assert _group_rejection_reason(birlesik, aday, params) == "length"
    # YANLIS (tur 4) yontem: birlesik kutu -> kopus GORUNMEZ, miras UYGULANIRDI
    assert _group_rejection_reason(birlesik, aday, params, ignore_length=True) is None
    # DOGRU (K24) yontem: kuyruk -> GERCEK kopus GORULUR, miras UYGULANMAZ
    assert _group_rejection_reason(kuyruk, aday, params, ignore_length=True) == "gap"


def test_k24_tail_HER_ZAMAN_TANIMLI_bos_liste_tek_oge_ilk_grup() -> None:
    """K24'un `tail` degiskeninin ALANI: bos liste, TEK ogeli grup ve ILK
    grup dahil her durumda tanimli mi (IndexError/UnboundLocalError yok
    mu), ve `apply_inheritance` iki degerinde de ayni mi?"""
    params = get_params(OcrPreset.DIALOGUE)

    # (a) bos liste
    assert _group([], params) == []
    assert _group([], params, apply_inheritance=False) == []

    # (b) TEK ogeli grup -- `tail = items[0]`, dongu HIC calismaz
    tek = [
        _Item(
            text="勇者",
            bbox=Rect(x=0, y=0, w=10, h=10),
            speaker="勇者",
            source_blocks=(0,),
        )
    ]
    for bayrak in (True, False):
        out = _group(tek, params, apply_inheritance=bayrak)
        assert len(out) == 1 and out[0] is tek[0], (bayrak, out)

    # (c) HER oge YENI bir grup baslatiyor (her yeni grupta `tail`
    #     SIFIRLANIR) -- kopus sebebi FARKLI konusmaci
    uc = [
        _Item(text="あ" * 5, bbox=Rect(x=0, y=0, w=100, h=20), speaker="勇者", source_blocks=(0,)),
        _Item(text="い" * 5, bbox=Rect(x=0, y=22, w=100, h=20), speaker="魔王", source_blocks=(1,)),
        _Item(text="う" * 5, bbox=Rect(x=0, y=44, w=100, h=20), speaker="村人", source_blocks=(2,)),
    ]
    for bayrak in (True, False):
        out = _group(uc, params, apply_inheritance=bayrak)
        assert [g.speaker for g in out] == ["勇者", "魔王", "村人"], (bayrak, out)
        assert [g.source_blocks for g in out] == [(0,), (1,), (2,)]


# --- 16.6 K26 uyumluluk formu etiket dagilimi ------------------------------


def test_k26_ALTI_karakterin_HEPSI_uyumluluk_formu_ve_ETIKET_dagilimi() -> None:
    """K26 (sef_karari-tur5.md): K22 *"ikisi fullwidth, dordu DIGER
    uyumluluk formu"* diyordu -- "diger" sozcugu fullwidth ikilinin
    uyumluluk formu OLMADIGINI ima ediyordu, YANLIS. Bu test
    `unicodedata.decomposition` ile ALTISININ da uyumluluk formu OLDUGUNU
    ve etiket dagilimini (2x `<wide>`, 2x `<small>`, 2x `<vertical>`)
    BAGIMSIZ olarak sabitler -- olgusal iddianin bir daha SESSIZCE
    bayatlamasini onler."""
    from collections import Counter

    alti = (0xFE15, 0xFE16, 0xFE56, 0xFE57, 0xFF01, 0xFF1F)
    etiketler = []
    for cp in alti:
        d = unicodedata.decomposition(chr(cp))
        assert d, f"U+{cp:04X} ayristirmasi YOK -- uyumluluk formu DEGIL"
        assert d.startswith("<"), (
            f"U+{cp:04X} KANONIK ayristirma ({d!r}) -- uyumluluk formu DEGIL"
        )
        etiketler.append(d.split()[0])
    assert Counter(etiketler) == Counter(
        {"<wide>": 2, "<small>": 2, "<vertical>": 2}
    ), Counter(etiketler)
    # Etiket -> karakter eslemesi de K26'nin tablosuyla BIREBIR
    assert unicodedata.decomposition(chr(0xFF01)).split()[0] == "<wide>"
    assert unicodedata.decomposition(chr(0xFF1F)).split()[0] == "<wide>"
    assert unicodedata.decomposition(chr(0xFE56)).split()[0] == "<small>"
    assert unicodedata.decomposition(chr(0xFE57)).split()[0] == "<small>"
    assert unicodedata.decomposition(chr(0xFE15)).split()[0] == "<vertical>"
    assert unicodedata.decomposition(chr(0xFE16)).split()[0] == "<vertical>"
    # K26'nin "sayi Python'un Unicode surumune baglidir" iddiasini SABITLE
    assert unicodedata.unidata_version == "15.0.0", (
        f"Unicode surumu DEGISTI ({unicodedata.unidata_version}) -- K26'nin "
        "olcumu 15.0.0'a gore yapilmisti, ALTI karakterlik liste yeniden "
        "dogrulanmali"
    )


# --- 16.7 K27 dort on ayar ------------------------------------------------


@pytest.mark.parametrize(
    "preset",
    [OcrPreset.DIALOGUE, OcrPreset.TOOLTIP, OcrPreset.SUBTITLE, OcrPreset.MENU],
)
def test_k27_DORT_on_ayarda_ayni_JP_girdi_menu_KAPSAM_DISI(preset: OcrPreset) -> None:
    """K27 (sef_karari-tur5.md): `menu`'de `should_group=False` oldugu icin
    `_group` HIC cagirilmaz -> K19/K21/K23/K24 `menu`'de TANIMSIZ. Ayni JP
    fixture'i (etiket + SIKI gruplanan govde1 + etiketsiz govde2) DORT on
    ayarla da kosulur: gruplayan uc on ayarda govde2 grubun icine girer;
    `menu`'de AYRI segment KALIR ve `speaker=None` olur. K23 degismezi
    DORT on ayarda da tutar."""
    bloklar = [
        blk("勇者：", 10, 0),
        blk("一行目の本文です。", 10, 22),
        blk("二行目の未ラベル本文です。", 10, 44),
    ]
    acik, kapali, iz_acik, iz_kapali = _bolumleme(bloklar, preset)
    assert iz_acik == iz_kapali, f"{preset}: K23 IHLALI"

    if preset is OcrPreset.MENU:
        assert len(acik) == 2, f"menu GRUPLADI: {[s.source_blocks for s in acik]}"
        assert acik[0].source_blocks == (0, 1) and acik[0].speaker == "勇者"
        assert acik[1].source_blocks == (2,)
        assert acik[1].speaker is None, (
            "K27 KAPSAM DISI ihlal edildi -- menu'de miras/gruplama olmamali"
        )
    else:
        assert len(acik) == 1, f"{preset} GRUPLAMADI: {[s.source_blocks for s in acik]}"
        assert acik[0].source_blocks == (0, 1, 2)
        assert acik[0].speaker == "勇者"


# --- 16.8 K23 degismezi -- TESTER-C'nin KENDI fuzz'i ----------------------


def test_k23_DEGISMEZ_tester_C_KENDI_fuzzi_CJK_agirlikli_2600_girdi() -> None:
    """K23'un makine denetimini, implementer'in 2500 girdilik denetimine
    GUVENMEDEN, TESTER-C'nin KENDI ureticisiyle tekrarlar: FARKLI tohum
    (20250910), FARKLI metin dagilimi (JP/KR agirlikli, fullwidth VE ASCII
    ayirac, DORT farkli yazi sisteminden isim), FARKLI geometri dagilimi
    (yozlasmis w/h; y adimlari 1..900 arasi sicramalarla, yani hem SIKI hem
    KOPUK komsuluklar), DORT on ayar.

    DEGISMEZ (K23): `source_blocks` DIZISI + `text` + `bbox` +
    `placeholders` + segment SAYISI, miras ACIK ve KAPALI kosularda
    BIREBIR ayni olmali. Ek olarak (K23'un "miras YALNIZCA `speaker`
    degerini degistirebilir" cumlesinin ikinci yarisi): miras SADECE
    `None -> deger` yonunde degisiklik yapabilir; mevcut bir `speaker`
    degerini DEGISTIREMEZ veya SILEMEZ.

    URETICININ DUYARLILIGI OLCULDU (tester_C_evidence/r5-mutation-check.txt):
    ureticinin ILK hali (duz rastgele bloklar, kucuk n) TUR 4'un HATALI
    `_group`'unda **SIFIR** ihlal buluyordu -- yani B1 desenini HIC
    uretmiyordu ve YANLIS bir guvence veriyordu. Bu yuzden uretici, B1
    desenini KASITLI olarak kuran bir "SAHNE" moduyla yeniden yazildi:
    etiket + SIKI aralikli COK sayida ETIKETSIZ govde blogu (cap'i asacak
    kadar) + genellikle AYNI isimle KENDI etiketini tasiyan bir kapanis
    repligi. Bu haliyle uretici, `src/` hic degistirilmeden monkeypatch ile
    kurulan TUR 4 mekanizmasinda **48/2600 ihlal** buluyor, mevcut kodda
    **0**. Yani bu test TOTOLOJI DEGIL: bilinen hatayi GERCEKTEN yakalar."""
    import random

    jp_kisa = [
        "これは長い台詞である。",
        "そして物語は続く。",
        "勇者は旅立った。",
        "魔王が現れた。",
        "村人は逃げ出した。",
        "剣を抜いた。",
    ]
    kr = ["이것은 긴 대사입니다.", "그리고 이야기는 계속된다.", "용사가 떠났다."]
    lat = [
        "This is a long line of text.",
        "and it continues here.",
        "well-known term",
        "value is {0} and %s here",
    ]
    # KUCUK isim havuzu -- AYNI isim tekrar gorulsun; B1 deseni tam olarak
    # "onceki repligin kuyrugu" ile "yeni repligin KENDI etiketi"nin AYNI
    # ada sahip olmasini gerektirir.
    isimler = ["勇者", "魔王", "김철수", "Ada"]
    seps = ("：", ":")
    presetler = (
        OcrPreset.DIALOGUE,
        OcrPreset.TOOLTIP,
        OcrPreset.SUBTITLE,
        OcrPreset.MENU,
    )

    def uret(rnd: random.Random) -> list[TextBlock]:
        bloklar: list[TextBlock] = []
        y = rnd.randint(-5, 40)
        if rnd.random() < 0.60:
            # SAHNE modu -- B1 desenini KASITLI kurar
            for _ in range(rnd.randint(1, 3)):
                isim = rnd.choice(isimler)
                bloklar.append(
                    blk(f"{isim}{rnd.choice(seps)}", rnd.randint(0, 20), y, w=300, h=20)
                )
                y += 22
                for _ in range(rnd.randint(4, 16)):
                    metin = "".join(
                        rnd.choice(jp_kisa) for _ in range(rnd.randint(1, 4))
                    )
                    bloklar.append(blk(metin, rnd.randint(0, 20), y, w=300, h=20))
                    y += rnd.choice([20, 21, 22, 22, 22, 22, 22, 60, 400])
                if rnd.random() < 0.85:
                    isim2 = isim if rnd.random() < 0.8 else rnd.choice(isimler)
                    bloklar.append(
                        blk(
                            f"{isim2}{rnd.choice(seps)}{rnd.choice(jp_kisa)}",
                            rnd.randint(0, 20),
                            y,
                            w=300,
                            h=20,
                        )
                    )
                    y += rnd.choice([22, 22, 22, 22, 400])
            return bloklar
        # GENEL mod -- yozlasmis geometri ve karisik script agirlikli
        for _ in range(rnd.randint(0, 9)):
            r = rnd.random()
            if r < 0.22:
                isim = rnd.choice(isimler)
                ayr = rnd.choice(seps)
                metin = (
                    f"{isim}{ayr}"
                    if rnd.random() < 0.5
                    else f"{isim}{ayr}{rnd.choice(jp_kisa)}"
                )
            elif r < 0.55:
                metin = "".join(rnd.choice(jp_kisa) for _ in range(rnd.randint(1, 5)))
            elif r < 0.75:
                metin = "".join(rnd.choice(kr) for _ in range(rnd.randint(1, 4)))
            else:
                metin = " ".join(rnd.choice(lat) for _ in range(rnd.randint(1, 6)))
            if rnd.random() < 0.10:
                w, h = rnd.choice([(300, 0), (0, 20), (300, -5), (-10, 20)])
            else:
                w, h = rnd.randint(40, 400), rnd.randint(1, 60)
            bloklar.append(
                blk(
                    metin,
                    rnd.randint(0, 60),
                    y,
                    w=w,
                    h=h,
                    confidence=round(rnd.uniform(0.5, 1.0), 3),
                )
            )
            y += rnd.choice([1, 5, 12, 18, 22, 60, 300, 900])
        return bloklar

    rnd = random.Random(20250910)
    ihlaller: list[str] = []
    coklu_segment = 0
    yozlasmis_blok = 0

    for case in range(2600):
        preset = presetler[case % 4]
        bloklar = uret(rnd)
        yozlasmis_blok += sum(
            1 for b in bloklar if b.bbox.w <= 0 or b.bbox.h <= 0
        )

        acik = _normalize_impl(bloklar, preset, apply_inheritance=True)
        kapali = _normalize_impl(bloklar, preset, apply_inheritance=False)
        if len(acik) >= 3:
            coklu_segment += 1

        if len(acik) != len(kapali):
            ihlaller.append(
                f"case={case} preset={preset} SEGMENT SAYISI "
                f"{len(acik)}!={len(kapali)}"
            )
            continue
        for i, (a, k) in enumerate(zip(acik, kapali)):
            if a.source_blocks != k.source_blocks:
                ihlaller.append(
                    f"case={case} seg={i} src {a.source_blocks}!={k.source_blocks}"
                )
            if a.text != k.text:
                ihlaller.append(f"case={case} seg={i} text FARKLI")
            if a.bbox != k.bbox:
                ihlaller.append(f"case={case} seg={i} bbox FARKLI")
            if a.placeholders != k.placeholders:
                ihlaller.append(f"case={case} seg={i} placeholders FARKLI")
            if not (
                a.speaker == k.speaker
                or (k.speaker is None and a.speaker is not None)
            ):
                ihlaller.append(
                    f"case={case} seg={i} miras bir DEGERI degistirdi: "
                    f"{k.speaker!r} -> {a.speaker!r}"
                )

    # Uretici gercekten ilgili yollari gezdi mi (test bir sey siniyor mu)
    assert coklu_segment > 1000, (
        f"fuzz yeterince COK SEGMENTLI (yani bolunen) girdi uretmedi: "
        f"{coklu_segment}"
    )
    assert yozlasmis_blok > 200, (
        f"fuzz yeterince yozlasmis geometri uretmedi: {yozlasmis_blok}"
    )
    assert ihlaller == [], (
        f"K23 DEGISMEZI IHLAL EDILDI ({len(ihlaller)} ihlal) -- "
        f"ilk uc: {ihlaller[:3]}"
    )
