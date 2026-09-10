# -*- coding: utf-8 -*-
"""T-004 Tester-C -- MERCEK: sinir, kotu kullanim ve dil -- TUR 6.

Kaynak: `env.md` TUR 6 / MERCEK C, `sef_karari-tur6.md` (surum 8) K28-K32
ve kararin "kitin bilinen sinirlari" tablosu.

Bu dosya TUR 6'da EKLENDI. Tur 5 dosyasi (`test_cjk_misuse_scale.py`)
DEGISTIRILMEDI -- oradaki 125 test regresyon avi olarak oldugu gibi kosar.

## Neden bu dosya var

Sef, olcu kitinin (`olcu_kiti.py`, surum 3) derleminin BES girdi sinifini
HIC uretmedigini olctu; besi de hem kite hem 1174 kor teste GORUNMEZ
(karar: "Bes girdi sinifi ... M14 -- Tester-C"). Bu dosyanin 1-5.
bolumleri TAM OLARAK o bes sinifi kurar:

  1. emoji / astral karakterler ve ZWJ dizileri
  2. `monitor_index != 0` tasiyan `Rect`'ler
  3. `dpi_scale != 1.0` tasiyan `Rect`'ler
  4. >=40 bloklu girdi
  5. ASCII-disi konusmaci adi (CJK / RTL / Indic / Tayca)

6-10. bolumler kararin C'ye acikca biraktiği kalan maddeleri kapatir:
K32 (NFC/NFD), K31 (a)/(b), yozlasmis geometri, kotu-kullanim yuzeyi ve
K28'in SOL tarafinda "yalniz-etiket blogu" yuzeyi.

## Olcek

Olcek olcumu bu dosyada TEST olarak YOKTUR. Gerekce: sef, tur 5'ten kalan
`test_olcek_tur2_*` / `test_olcek_tur4_*` testlerinin TAM TAKIM YUKU
altinda kararsiz oldugunu olctu (uc kosumda 1/1/0 kirik). Olcum bu turda
TEK BASINA kosuldu ve ham cikti
`tester_C_evidence/r6-06-olcek-tek-basina.txt` altindadir; sonuc
verdict-C.md'dedir. Kararsiz bir zamanlama testini COGALTMAK kapiyi
gurultulendirmekten baska bir sey yapmaz.

## Belirlenimcilik

Rastgelelik kullanan testler SABIT tohumla calisir. Zaman olcumu YOK.

Calistirma:
    python -m pytest .agents/tasks/T-004/tester_C -q
"""
from __future__ import annotations

import inspect
import random
import sys
import unicodedata
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import src.ocr.normalizer as N  # noqa: E402
from src.contracts.models import OcrPreset, Rect, Segment, TextBlock  # noqa: E402
from src.ocr.normalizer import (  # noqa: E402
    _group,
    _Item,
    _normalize_impl,
    _raw_query_pair,
    _split_speaker_label,
    normalize,
)
from src.ocr.presets import get_params  # noqa: E402

GRUPLAYAN = (OcrPreset.DIALOGUE, OcrPreset.TOOLTIP, OcrPreset.SUBTITLE)
DORT_ON_AYAR = (*GRUPLAYAN, OcrPreset.MENU)

# ZWJ aile: TEK gorunur grapheme, BES codepoint.
ZWJ_AILE = "\U0001F468‍\U0001F469‍\U0001F467"
BAYRAK_TR = "\U0001F1F9\U0001F1F7"
ASTRAL_KANJI = "\U0002000B"          # CJK ext-B, kategori Lo, TEK codepoint
ASTRAL_BOLD_A = "\U0001D400"         # matematiksel bold A, kategori Lu


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
) -> TextBlock:
    return TextBlock(
        text=text,
        bbox=Rect(x=x, y=y, w=w, h=h, monitor_index=monitor_index, dpi_scale=dpi_scale),
        confidence=confidence,
    )


def bolumleme(segs: list[Segment]) -> list[tuple[int, ...]]:
    """K23'un ve K8'in denetledigi sey: SADECE `source_blocks` dizisi."""
    return [s.source_blocks for s in segs]


def derlem(n: int, *, tohum: int, monitor_index: int = 0, dpi_scale: float = 1.0) -> list[TextBlock]:
    """Sirasiz, cok konusmaculu, degisken geometrili derlem.

    `monitor_index`/`dpi_scale` BLOK BASINA SABIT verilir -- amac K10'un
    birlesim yasagini tetiklemek DEGIL, bu iki alanin BOLUMLEMEYE ve
    MIRASA hic karismadigini olcmektir.

    ZINCIRLEME HYPHEN zorunlu: blocklarin ~%45'i, adim 3'te (K5) TEK bir
    cok bloklu `_Item`'a birlesen 2-4 bloklu zincirler halinde uretilir ve
    zincir icindeki yukseklikler KASITLI olarak farklidir. Bu olmadan
    `_raw_query_pair`'in ham ikamesi NO-OP olur (tek bloklu bir ogenin
    birlesik kutusu zaten kendi kutusudur) ve derlem, ikameyi bir kosula
    KAPILAYAN mutantlari AYIRT EDEMEZ -- olculdu, bkz.
    `tester_C_evidence/r6-13-mutasyon-denetimi.txt` (ilk surumde MC4/MC5
    dissizdi)."""
    r = random.Random(tohum)
    bl: list[TextBlock] = []
    y = 0
    i = 0
    while len(bl) < n:
        if r.random() < 0.45:
            k = r.randint(2, 4)
            for j in range(k):
                son = j == k - 1
                metin = ("Ada: " if (i % 5 == 0 and j == 0) else "")
                metin += "kelime" * r.randint(3, 9) + ("" if son else "-")
                h = r.choice([6, 12, 20, 40])
                bl.append(
                    blk(metin, r.choice([10, 12]), y, w=r.choice([200, 300]), h=h,
                        monitor_index=monitor_index, dpi_scale=dpi_scale)
                )
                y += h + r.choice([1, 2, 4])
            y += r.choice([2, 6, 14, 30])
        else:
            metin = ("Ada: " if i % 5 == 0 else "") + "kelime" * r.randint(1, 12)
            h = r.choice([12, 18, 20, 30])
            bl.append(
                blk(metin, r.choice([10, 12, 15]), y, w=r.choice([200, 300, 320]), h=h,
                    monitor_index=monitor_index, dpi_scale=dpi_scale)
            )
            y += h + r.choice([2, 5, 9, 40])
        i += 1
    r.shuffle(bl)
    return bl


# ===========================================================================
# 1. M14/1 -- EMOJI, ASTRAL KARAKTERLER, ZWJ DIZILERI
#    Kit bu sinifi HIC uretmiyor (sef_karari-tur6.md "bilinen sinirlar").
# ===========================================================================


@pytest.mark.parametrize(
    "ad,metin",
    [
        ("ZWJ aile (5 cp, 1 grapheme)", ZWJ_AILE),
        ("bayrak dizisi TR (2 cp)", BAYRAK_TR),
        ("varyasyon secici U+FE0F (2 cp)", "☀️"),
        ("ten tonu modifikatoru (2 cp)", "\U0001F44B\U0001F3FB"),
        ("keycap dizisi (3 cp)", "1️⃣"),
        ("astral kanji U+2000B (1 cp, Lo)", ASTRAL_KANJI),
        ("astral bold A U+1D400 (1 cp, Lu)", ASTRAL_BOLD_A),
    ],
)
def test_m14_emoji_astral_zwj_blogu_silinmez(ad: str, metin: str) -> None:
    """K4 + K12: cok kod noktali emoji/ZWJ/bayrak dizileri ve ASTRAL
    harfler tek basina bir blokta gelirse SILINMEMELI.

    K4'un tek-karakter kurali `len(stripped) != 1` ile korunur; ZWJ/bayrak/
    varyasyon dizileri BIRDEN COK codepoint tasidigi icin kurala HIC
    girmez, astral HARFLER ise (`Lo`/`Lu`) tek codepoint olsalar da L*
    dalindan gecer. Bu sinif kite ve kor takima gorunmez -- burada
    olculur."""
    cikti = normalize([blk(metin, 10, 10)], OcrPreset.MENU)
    assert [s.text for s in cikti] == [metin], f"{ad}: blok silindi (K4 ihlali)"


@pytest.mark.parametrize(
    "ad,metin",
    [
        ("tek emoji U+1F44D (So)", "\U0001F44D"),
        ("varyasyon secicisiz gunes U+2600 (So)", "☀"),
    ],
)
def test_m14_tek_kod_noktali_emoji_sembol_olarak_atilir(ad: str, metin: str) -> None:
    """K4'un SIMETRIGI: tek codepoint'lik bir emoji `So` (sembol)
    kategorisindedir, `L*`/`N*` DEGILDIR ve NFKC ile `?`/`!`ye ACILMAZ --
    dolayisiyla tek-karakter gurultu kuralina TAKILIR ve atilir.

    Bu, yukaridaki testin TERSI degil TAMAMLAYICISIDIR: kural SINIF
    tabanlidir (K4), "emoji" diye bir beyaz/kara liste YOKTUR. Test bunu
    kategori iddiasiyla birlikte pinler."""
    assert unicodedata.category(metin) == "So"
    assert len(metin) == 1
    assert normalize([blk(metin, 10, 10)], OcrPreset.MENU) == []


def test_m14_zwj_dizisi_codepoint_sayisi_max_group_chars_i_sisiriyor() -> None:
    """K11 x K32 ETKILESIMI, emoji yuzeyinde: `max_group_chars` `len()`
    ile olculur ve `len()` CODEPOINT sayar -- GRAPHEME degil.

    AYNI SAYIDA gorunur karakter iceren iki govde, biri ZWJ dizilerinden
    (grapheme basina 5 codepoint) biri ASCII'den kurulunca FARKLI
    bolumleniyor. Bu, K32'nin belgeledigi "codepoint sayar" mekanizmasinin
    NFC/NFD DISINDAKI ikinci yuzeyidir; davranisi BELGELER, duzeltmez.

    TOOLTIP `max_group_chars=200`; 20 grapheme -> ZWJ'de 100 cp, ASCII'de
    20 cp."""
    zwj_govde = ZWJ_AILE * 20        # 20 grapheme, 100 codepoint
    ascii_govde = "x" * 20           # 20 grapheme,  20 codepoint
    assert len(zwj_govde) == 100 and len(ascii_govde) == 20

    def kur(govde: str) -> list[TextBlock]:
        return [blk("Ada: " + govde, 10, 0, h=20), blk(govde, 10, 25, h=20)]

    zwj = normalize(kur(zwj_govde), OcrPreset.TOOLTIP)
    asc = normalize(kur(ascii_govde), OcrPreset.TOOLTIP)
    assert bolumleme(asc) == [(0, 1)], "ASCII govde TEK segment olmali"
    assert bolumleme(zwj) == [(0,), (1,)], "ZWJ govde codepoint sisirmesiyle BOLUNMELI"


@pytest.mark.parametrize(
    "metin,beklenen",
    [
        ("\U0001F468: merhaba", None),          # So -> isalpha() False
        ("Ada\U0001F44D: merhaba", None),       # ad icinde emoji -> reddedilir
        (ASTRAL_BOLD_A + "\U0001D401" + ": merhaba", "\U0001D400\U0001D401"),
        (ASTRAL_KANJI + ": merhaba", ASTRAL_KANJI),
    ],
)
def test_m14_emoji_ve_astral_konusmaci_adi_sinif_tabanli(metin: str, beklenen: str | None) -> None:
    """K9 ad suzgeci ASTRAL duzlemde de CODEPOINT SINIFINA gore calisir:
    astral HARF (`Lu`/`Lo`) ad olabilir, emoji (`So`) olamaz. Ad icinde
    TEK bir emoji tum etiketi dusurur (etiket metinde kalir -- K31/b
    yolu)."""
    assert _split_speaker_label(metin)[0] == beklenen


def test_m14_emoji_iceren_govdede_miras_speakeri_codepoint_duzeyinde_korur() -> None:
    """Gorunum gecisi (K19/K21/K23) `speaker` string'ini KOPYALAR, yeniden
    URETMEZ -- emoji/astral govdeyle birlikte de codepoint BIREBIRLIGI
    korunmali. `_raw_query_pair`'in `replace(...)` ikamesi YALNIZ `bbox`'a
    dokunur (K28), `speaker`'a DEGIL; bu test onun urun yuzeyindeki
    sonucudur."""
    govde = (ZWJ_AILE + "あ" * 20) * 7   # 175 codepoint; 175+1+175 > 280 (DIALOGUE)
    assert len(govde) == 175
    bl = [blk("勇者：" + govde, 10, 0, h=20), blk(govde, 10, 25, h=20)]
    segs = normalize(bl, OcrPreset.DIALOGUE)
    assert len(segs) == 2, "uzunluk siniri dogmali"
    assert [s.speaker for s in segs] == ["勇者", "勇者"]
    for s in segs:
        assert [ord(c) for c in (s.speaker or "")] == [0x52C7, 0x8005]


def test_m14_yalniz_vekil_kod_noktasi_cokme_uretmez() -> None:
    """KOTU KULLANIM: UTF-16 tabanli bir OCR motoru YALNIZ VEKIL (lone
    surrogate) sizdirabilir. `normalize` bunda COKMEZ -- `unicodedata`
    cagrilari `Cs` kategorisini sorunsuz doner. (Metin daha sonra
    `encode()` edilirse patlar; bu T-004'un DISINDA ama sessiz bir
    bozulma DEGIL.)"""
    vekil = "\ud83d"
    assert unicodedata.category(vekil) == "Cs"
    cikti = normalize([blk(vekil, 10, 10), blk(vekil + "abc", 10, 40)], OcrPreset.MENU)
    assert [s.text for s in cikti] == [vekil + "abc"]


# ===========================================================================
# 2. M14/2 -- monitor_index != 0
# ===========================================================================


@pytest.mark.parametrize("monitor_index", [1, 7, -3])
@pytest.mark.parametrize("preset", DORT_ON_AYAR)
def test_m14_monitor_index_bolumlemeyi_degistirmez(monitor_index: int, preset: OcrPreset) -> None:
    """`monitor_index` bir KIMLIK alanidir, GEOMETRI degil: ayni derlem
    `monitor_index=0` ve `!= 0` ile BIREBIR ayni bolumlenmeli. Kit bu
    alani hic doldurmuyor; farkli davranan bir uygulama (ör. monitor
    indeksini bir kapi kosuluna sokan) kite ve kor takima gorunmez."""
    taban = derlem(40, tohum=13, monitor_index=0)
    baska = derlem(40, tohum=13, monitor_index=monitor_index)
    assert bolumleme(normalize(taban, preset)) == bolumleme(normalize(baska, preset))
    assert [s.speaker for s in normalize(taban, preset)] == [
        s.speaker for s in normalize(baska, preset)
    ]


def test_m14_birlesmis_segment_monitor_index_i_tasir() -> None:
    """K10: birlesik bbox `monitor_index`/`dpi_scale`'i KAYNAKTAN alir --
    varsayilan `0`'a SESSIZCE dusmez."""
    segs = normalize(
        [blk("Ada: bir", 10, 0, monitor_index=4), blk("iki", 10, 25, monitor_index=4)],
        OcrPreset.DIALOGUE,
    )
    assert bolumleme(segs) == [(0, 1)]
    assert segs[0].bbox.monitor_index == 4
    assert segs[0].bbox.dpi_scale == 1.0


def test_m14_karisik_monitor_birlesme_denenirse_value_error(
) -> None:
    """K10 REGRESYONU (tur 1'den beri): birlesecek iki blok farkli
    `monitor_index` tasiyorsa `ValueError` -- sessiz kopyalama yok."""
    with pytest.raises(ValueError, match="monitor_index/dpi_scale"):
        normalize(
            [blk("Ada: bir", 10, 0, monitor_index=0), blk("iki", 10, 25, monitor_index=1)],
            OcrPreset.DIALOGUE,
        )


def test_BULGU_BLOKE_ETMEYEN_miras_monitor_sinirini_asiyor() -> None:
    """BULGU (bloke ETMIYOR) -- BELGELEYEN test, duzelten degil.

    AYNI iki blok, metin KISA ise `ValueError` (birlesme denenir, K10),
    metin UZUN ise (`max_group_chars` asilir -> reason `"length"`) SESSIZCE
    gecer VE ikinci segment birincinin `speaker`'ini MIRAS alir -- yani
    konusmaci atfi MONITOR SINIRINI asar. Miras-uygunluk sorgusu iki
    FARKLI ekrandaki kutular arasinda `gap`/`overlap` hesaplar; bu
    geometri KIYASLANABILIR DEGILDIR.

    Neden bloke etmiyor: K10'un lafzi BIRLESIM icindir ("iki oge
    BIRLESTIGINDE ... `ValueError`") ve burada birlesim YOK -- segmentler
    kendi `bbox`'lariyla ayri kaliyor, sessiz bir kutu kopyalamasi
    olmuyor. Ayrica gercekci boru hattinda tek `Frame` tek monitordendir.
    Yine de sonucun YALNIZCA METIN UZUNLUGUNA bagli olmasi (ayni cift ya
    patlar ya sessizce miras verir) `known_gaps`'e yazilmaya deger;
    ayrinti verdict-C.md."""
    uzun = "a" * 270
    segs = normalize(
        [
            blk("Ada: " + uzun, 10, 0, h=20, monitor_index=0),
            blk("b" * 20, 10, 25, h=20, monitor_index=1),
        ],
        OcrPreset.DIALOGUE,
    )
    assert bolumleme(segs) == [(0,), (1,)]
    assert [s.speaker for s in segs] == ["Ada", "Ada"], "BUGUNKU davranis pinlenir"
    assert [s.bbox.monitor_index for s in segs] == [0, 1]

    with pytest.raises(ValueError):
        normalize(
            [
                blk("Ada: kisa", 10, 0, h=20, monitor_index=0),
                blk("metin", 10, 25, h=20, monitor_index=1),
            ],
            OcrPreset.DIALOGUE,
        )


# ===========================================================================
# 3. M14/3 -- dpi_scale != 1.0
# ===========================================================================


@pytest.mark.parametrize("dpi_scale", [1.25, 1.5, 2.0, 0.5])
@pytest.mark.parametrize("preset", DORT_ON_AYAR)
def test_m14_dpi_scale_bolumlemeyi_degistirmez(dpi_scale: float, preset: OcrPreset) -> None:
    """`dpi_scale` de KIMLIK alanidir: `Rect` docstring'i "koordinatlar
    FIZIKSEL pikseldir; `dpi_scale` mantiksal koordinata cevirmek isteyen
    tarafin isidir" der -- yani `normalize` onu OKUMAZ. Ayni derlem farkli
    `dpi_scale` ile BIREBIR ayni bolumlenmeli."""
    taban = derlem(40, tohum=13, dpi_scale=1.0)
    baska = derlem(40, tohum=13, dpi_scale=dpi_scale)
    assert bolumleme(normalize(taban, preset)) == bolumleme(normalize(baska, preset))
    assert [s.speaker for s in normalize(taban, preset)] == [
        s.speaker for s in normalize(baska, preset)
    ]


@pytest.mark.parametrize("k", [2, 3, 4])
@pytest.mark.parametrize("preset", GRUPLAYAN)
def test_m14_geometri_dpi_ile_olceklenirse_bolumleme_degismez(k: int, preset: OcrPreset) -> None:
    """DPI'nin GERCEK yuzeyi: yuksek DPI'de OCR kutulari BUYUR. Butun
    geometrik esikler CARPMA ile ve ORAN olarak yazildigi icin (`gap <
    oran * min(h)`, `overlap > oran * min(w)`) tum koordinatlari `k` ile
    olceklemek bolumlemeyi DEGISTIRMEMELI. Boleme dayali bir uygulama ya
    da mutlak piksel esigi tasiyan bir uygulama burada ayrisir."""
    taban = derlem(40, tohum=13)
    olcekli = [
        TextBlock(
            text=b.text,
            bbox=Rect(
                x=b.bbox.x * k,
                y=b.bbox.y * k,
                w=b.bbox.w * k,
                h=b.bbox.h * k,
                monitor_index=b.bbox.monitor_index,
                dpi_scale=float(k),
            ),
            confidence=b.confidence,
        )
        for b in taban
    ]
    assert bolumleme(normalize(taban, preset)) == bolumleme(normalize(olcekli, preset))


def test_BULGU_BLOKE_ETMEYEN_nan_dpi_scale_kendi_kendine_esit_degil() -> None:
    """BULGU (bloke ETMIYOR) -- TANI YUZEYI.

    `Rect.dpi_scale` K7'nin `confidence` denetimine BENZER bir on
    dogrulamadan GECMEZ. `NaN` bir `dpi_scale`, `a.dpi != b.dpi`
    karsilastirmasinda KENDISIYLE bile esit olmadigi icin, AYNI `NaN`
    degerini tasiyan iki blok birlesmeye calistiginda `ValueError`
    yukselir -- ve mesaj IKI TARAFI DA `nan` olarak yazar, yani "degerler
    uyusmuyor: (0, nan) != (0, nan)" gibi KENDI ICINDE CELISKILI
    gorunen bir tani cikti uretir.

    Neden bloke etmiyor: sonuc SESSIZ DEGIL (patliyor) ve K10'un lafzini
    ihlal etmiyor. Yalnizca mesaj yanilticidir; K7'nin `confidence` icin
    yaptigi gibi bir on denetim (`math.isnan`) tani kalitesini
    duzeltirdi. Ayrinti verdict-C.md."""
    nan = float("nan")
    with pytest.raises(ValueError) as bilgi:
        normalize(
            [blk("Ada: bir", 10, 0, dpi_scale=nan), blk("iki", 10, 25, dpi_scale=nan)],
            OcrPreset.DIALOGUE,
        )
    mesaj = str(bilgi.value)
    assert "nan) != (" in mesaj and mesaj.count("nan") == 2, mesaj


@pytest.mark.parametrize("a_dpi,b_dpi", [(1, 1.0), (-0.0, 0.0)])
def test_m14_dpi_scale_sayisal_esdeglik_birlesmeyi_engellemez(a_dpi: float, b_dpi: float) -> None:
    """`1` ile `1.0`, `-0.0` ile `0.0` Python'da ESITTIR; K10 kontrolu
    `!=` ile yazildigi icin bu ciftler birlesmeyi ENGELLEMEZ. (`is` ya da
    `repr` karsilastirmasina kayan bir uygulama burada ayrisir.)"""
    segs = normalize(
        [blk("Ada: bir", 10, 0, dpi_scale=a_dpi), blk("iki", 10, 25, dpi_scale=b_dpi)],
        OcrPreset.DIALOGUE,
    )
    assert bolumleme(segs) == [(0, 1)]


# ===========================================================================
# 4. M14/4 -- >=40 BLOKLU GIRDI
# ===========================================================================


@pytest.mark.parametrize("n", [40, 63, 120])
@pytest.mark.parametrize("preset", DORT_ON_AYAR)
def test_m14_kirk_ve_uzeri_blokta_k8_k3_k23_birlikte_tutar(n: int, preset: OcrPreset) -> None:
    """Kitin derlemi >=16 bloga cikiyor, >=40'a CIKMIYOR. Bu boy sinifinda
    UC degismez ayni anda denetlenir:
      K8  -- `source_blocks` artan, tekrarsiz, AYRIK, aralik icinde;
      K3  -- cikti `(bbox.y, bbox.x)` artan;
      K23 -- miras acik/kapali BOLUMLEME birebir ayni."""
    bl = derlem(n, tohum=n)
    segs = normalize(bl, preset)

    gorulen: set[int] = set()
    for s in segs:
        sb = s.source_blocks
        assert sb, "bos source_blocks (K8)"
        assert list(sb) == sorted(set(sb)), f"artan/tekrarsiz degil: {sb}"
        assert not (gorulen & set(sb)), f"segmentler AYRIK degil: {sb}"
        assert 0 <= min(sb) and max(sb) < len(bl), f"indeks araligi disi: {sb}"
        gorulen |= set(sb)

    anahtarlar = [(s.bbox.y, s.bbox.x) for s in segs]
    assert anahtarlar == sorted(anahtarlar), "K3 cikti sirasi bozuk"

    assert bolumleme(_normalize_impl(bl, preset, apply_inheritance=True)) == bolumleme(
        _normalize_impl(bl, preset, apply_inheritance=False)
    ), "K23 IHLALI"


def test_m14_altmis_bloklu_zincirde_miras_sonuna_kadar_tasinir() -> None:
    """K19/K21 zincirleme mirasi, kararin `tests/` altinda pinledigi UC
    segmentlik zincirden COK daha uzun bir zincirde de tutmali. Gorunum
    gecisi ILERI yonde ilerledigi icin (`groups[i-1]` ONCE guncellenir,
    sonra `groups[i]` ondan okur) 60 segmentin 60'i da etiketi almali --
    donguyu TERS yonde isleyen bir uygulama burada ilk sinirdan sonra
    `None` uretir."""
    govde = "kelime" * 45  # 270 cp; DIALOGUE cap 280 -> her sinir YALNIZ-UZUNLUK
    bl = [blk("Ada: " + govde, 10, 0, h=20)]
    y = 25
    for _ in range(59):
        bl.append(blk(govde, 10, y, h=20))
        y += 25

    segs = normalize(bl, OcrPreset.DIALOGUE)
    assert len(segs) == 60
    assert [s.speaker for s in segs] == ["Ada"] * 60


def test_m14_kirk_uzeri_sirasiz_cjk_girdide_k23_fuzz() -> None:
    """K23 degismezi, >=40 bloklu SIRASIZ + CJK + yozlasmis geometrili
    girdide de tutmali. Tester-C'nin KENDI ureticisi (farkli tohum,
    farkli dagilim) -- kitin derlemi bu boy/dil karisimini uretmiyor."""
    ihlal = 0
    for t in range(60):
        r = random.Random(90000 + t)
        n = r.randint(40, 70)
        bl = []
        y = 0
        for i in range(n):
            metin = ("勇者：" if i % 7 == 0 else "") + "あ" * r.randint(3, 60)
            h = r.choice([0, 5, 12, 18, 20, 30])
            bl.append(
                blk(
                    metin,
                    r.choice([0, 10, 200]),
                    y,
                    w=r.choice([0, 50, 300]),
                    h=h,
                    confidence=r.choice([0.9, 0.5, 0.62]),
                )
            )
            y += max(h, 1) + r.choice([1, 3, 8, 50])
        r.shuffle(bl)
        for preset in GRUPLAYAN:
            if bolumleme(_normalize_impl(bl, preset, apply_inheritance=True)) != bolumleme(
                _normalize_impl(bl, preset, apply_inheritance=False)
            ):
                ihlal += 1
    assert ihlal == 0, f"K23 ihlali: {ihlal}/180"


# ===========================================================================
# 5. M14/5 -- ASCII-DISI KONUSMACI ADI
# ===========================================================================


@pytest.mark.parametrize(
    "ad,metin,beklenen_speaker,beklenen_kalan",
    [
        ("japonca kanji + fullwidth ayrac", "勇者：こんにちは", "勇者", "こんにちは"),
        ("japonca kanji + ASCII ayrac", "魔王: こんにちは", "魔王", "こんにちは"),
        ("japonca hiragana", "むらびと：やあ", "むらびと", "やあ"),
        ("korece hangul", "용사: 안녕", "용사", "안녕"),
        ("cince", "王小明：你好", "王小明", "你好"),
        ("kiril", "Ада: привет", "Ада", "привет"),
        ("yunanca", "Αδα: γεια", "Αδα", "γεια"),
        ("arapca (harekesiz)", "مرحبا: أهلا", "مرحبا", "أهلا"),
        ("ibranice (nikudsuz)", "שלום: היי", "שלום", "היי"),
        ("halfwidth katakana", "ｶﾞﾝ: やあ", "ｶﾞﾝ", "やあ"),
        ("vietnamca (NFC)", "Đức: xin chào", "Đức", "xin chào"),
    ],
)
def test_m14_ascii_disi_konusmaci_adi_taniniyor(
    ad: str, metin: str, beklenen_speaker: str, beklenen_kalan: str
) -> None:
    """K9 + K17: ad suzgeci `isalpha()` tabanlidir, ASCII'ye kapili
    DEGILDIR. On bir yazi sisteminde etiket AYIKLANMALI ve `speaker`
    CODEPOINT duzeyinde ayni kalmali (`ｶﾞﾝ` halfwidth katakana NFKC ile
    ACILMAZ -- ad suzgeci normalizasyon YAPMAZ)."""
    isim, kalan = _split_speaker_label(metin)
    assert isim == beklenen_speaker
    assert [ord(c) for c in (isim or "")] == [ord(c) for c in beklenen_speaker]
    assert kalan == beklenen_kalan


@pytest.mark.parametrize(
    "ad,isim",
    [
        ("devanagari (basit ad, matra iceriyor)", "राम"),
        ("devanagari (virama iceriyor)", "नमस्ते"),
        ("tayca (sara/vokal isareti iceriyor)", "สวัสดี"),
        ("arapca + hareke", "مَرحبا"),
        ("ibranice + nikud", "שָלוֹם"),
    ],
)
def test_BULGU_BLOKE_ETMEYEN_nfc_olan_indic_tayca_ve_harekeli_adlar_taninmiyor(
    ad: str, isim: str
) -> None:
    """BULGU (bloke ETMIYOR) -- K32'nin BELGELEDIGI KAPSAM DAR.

    K32 kapsami "NFD adlar (birlesik aksan)" diye tarif ediyor ve cozumu
    T-006'nin NFC uretmesine baglıyor. Olculdu: asagidaki adlarin HEPSI
    ZATEN NFC-normaldir (`unicodedata.is_normalized("NFC", ad) is True`
    ve NFC == NFD) -- cunku Devanagari matra/virama, Tayca vokal isareti,
    Arapca hareke ve Ibranice nikud NFC ile TASIYICI harfe BIRLESMEZ.
    Buna ragmen `isalpha()` bu `Mn`/`Mc` isaretlerini reddettigi icin
    ETIKET AYIKLANMIYOR ve metinde kaliyor (K31/b yolu).

    Yani T-006'nin NFC uretmesi bu sinifi KAPATMAZ. Davranis K9'un
    lafzina uygundur (kod dogru), eksik olan K32'nin KAPSAM cumlesidir.

    Neden bloke etmiyor: metin KAYBOLMUYOR (etiket metinde kaliyor, K31/b
    ile ayni ve BELGELI yol), cokme yok, bolumleme bozulmuyor -- yalniz
    `speaker` alani `None` kaliyor. Onerilen K32 duzeltmesi
    verdict-C.md'de."""
    assert unicodedata.is_normalized("NFC", isim), f"{ad}: test verisi NFC degil"
    assert unicodedata.normalize("NFC", isim) == unicodedata.normalize("NFD", isim), (
        f"{ad}: bu ad NFC/NFD ile DEGISIYOR -- test verisi yanlis secilmis"
    )
    assert _split_speaker_label(isim + ": govde") == (None, isim + ": govde")


@pytest.mark.parametrize(
    "ad,metin",
    [
        ("RTL isareti U+200F ad icinde", "مرحبا‏: أهلا"),
        ("LTR isareti U+200E ad icinde", "‎Ada: merhaba"),
    ],
)
def test_BULGU_BLOKE_ETMEYEN_yonelim_isaretleri_adi_dusuruyor(ad: str, metin: str) -> None:
    """BULGU (bloke ETMIYOR) -- ayni sinif, farkli kaynak: RTL/LTR
    yonelim isaretleri (`Cf`) GORUNMEZDIR ve OCR/kaynak metin bunlari
    tasiyabilir. Ad suzgecinden gecemezler, etiket sessizce metinde
    kalir. K32'nin kapsam cumlesi bunu da kapsamali."""
    assert _split_speaker_label(metin)[0] is None


@pytest.mark.parametrize("etiket,ayrac", [("勇者", "："), ("魔王", ":"), ("Ада", ":"), ("مرحبا", ":")])
def test_m14_ascii_disi_adla_miras_zinciri_uc_segmentte_korunur(etiket: str, ayrac: str) -> None:
    """Kararın `tests/` altinda pinledigi zincirleme miras testi ASCII
    (`Ada`). Ayni zincir ASCII-DISI adla da tutmali -- `_raw_query_pair`
    `replace(...)` ile `speaker`'i AYNEN tasiyor (K28), yeniden
    kodlamiyor."""
    govde = "あ" * 150
    bl = [
        blk(etiket + ayrac + govde, 10, 0, h=20),
        blk(govde, 10, 25, h=20),
        blk(govde, 10, 50, h=20),
    ]
    segs = normalize(bl, OcrPreset.DIALOGUE)
    assert bolumleme(segs) == [(0,), (1,), (2,)]
    assert [s.speaker for s in segs] == [etiket] * 3


def test_m14_yalniz_etiketli_cjk_blok_bir_sonrakine_tasinir() -> None:
    """K9: yalniz-etiket blogu (`勇者：`) segment URETMEZ; etiket VE
    `source_blocks` bir SONRAKI ogeye tasinir -- geometrik olarak COK UZAK
    olsa bile (burada 180px)."""
    segs = normalize([blk("勇者：", 10, 0, h=20), blk("こんにちは", 10, 200, h=20)], OcrPreset.DIALOGUE)
    assert len(segs) == 1
    assert segs[0].text == "こんにちは"
    assert segs[0].speaker == "勇者"
    assert segs[0].source_blocks == (0, 1)


# ===========================================================================
# 6. K32 -- NFC / NFD
# ===========================================================================


def test_k32_nfd_govde_segment_sayisini_degistirir_bagimsiz_govde() -> None:
    """K32: `max_group_chars` CODEPOINT sayar, dolayisiyla AYNI GORUNEN
    govde NFD geldiginde BOLUMLEME degisir.

    Kararin `tests/` altindaki testi kendi govdesini (`"áéíóú"*18`)
    pinliyor. Bu test BAGIMSIZ bir govde kullanir (dogal Ispanyolca cumle,
    80 cp NFC / 92 cp NFD) -- olcum tek bir sihirli govdeye BAGLI
    olmamali. Bu test davranisi BELGELER, duzeltmez."""
    govde_nfc = "María dijo qué así canción María dijo qué así canción María dijo qué así canción"
    govde_nfd = unicodedata.normalize("NFD", govde_nfc)
    assert len(govde_nfc) == 80 and len(govde_nfd) == 92
    assert unicodedata.normalize("NFC", govde_nfd) == govde_nfc

    def kur(etiket: str, govde: str) -> list[TextBlock]:
        return [
            blk(etiket + ": " + govde, 10, 0, h=20),
            blk(govde, 10, 25, h=20),
            blk(govde, 10, 50, h=20),
        ]

    nfc = normalize(kur("María", govde_nfc), OcrPreset.DIALOGUE)
    nfd = normalize(kur(unicodedata.normalize("NFD", "María"), govde_nfd), OcrPreset.DIALOGUE)

    assert bolumleme(nfc) == [(0, 1, 2)]
    assert [s.speaker for s in nfc] == ["María"]
    assert bolumleme(nfd) == [(0, 1), (2,)], "NFD govde BOLUMLEMEYI degistirmeli"
    assert [s.speaker for s in nfd] == [None, None]


def test_k32_yalniz_etiket_nfd_ise_segment_sayisi_ayni_speaker_none() -> None:
    """K32'nin ikinci yarisi, COK BLOKLU govdede: yalnizca ETIKET
    aksanliysa segment SAYISI degismez -- ama `speaker` `None`'a duser ve
    etiket METINDE kalir. (Kararin testi TEK bloklu govde kullaniyor;
    burada iki blok var, yani gruplama yolu da kosuluyor.)"""
    def kur(etiket: str) -> list[TextBlock]:
        return [blk(etiket + ": " + "hola " * 8, 10, 0, h=20), blk("adios " * 8, 10, 25, h=20)]

    nfc = normalize(kur("María"), OcrPreset.DIALOGUE)
    nfd = normalize(kur(unicodedata.normalize("NFD", "María")), OcrPreset.DIALOGUE)

    assert len(nfc) == len(nfd) == 1
    assert bolumleme(nfc) == bolumleme(nfd) == [(0, 1)]
    assert nfc[0].speaker == "María"
    assert nfd[0].speaker is None
    assert nfd[0].text.startswith(unicodedata.normalize("NFD", "María") + ":")


def test_k32_ayrac_kumesi_nfd_den_etkilenmez() -> None:
    """K32: "Ayrac kumesi (`:`/`：`, K17) ETKILENMEZ" -- olculur: her iki
    ayrac da NFD altinda DEGISMEZ, yani etiket TESPITI NFD'de de calisir
    (duşen sey ADIN kendisidir, ayrac degil)."""
    for ayrac in (":", "："):
        assert unicodedata.normalize("NFD", ayrac) == ayrac
    metin = unicodedata.normalize("NFD", "María") + "：hola"
    assert N._find_speaker_separator(metin) == len(unicodedata.normalize("NFD", "María"))
    assert _split_speaker_label(metin)[0] is None, "ayrac bulunur ama AD reddedilir"


def test_k32_max_speaker_name_len_de_codepoint_sayar() -> None:
    """K32'nin `_MAX_SPEAKER_NAME_LEN` (K9) yarisi: 40 codepoint TAM
    SINIRDA kabul edilen bir ad, NFD'de 41 cp'ye cikip REDDEDILIR --
    aksan `Mn` oldugu icin zaten reddedilirdi, bu yuzden ayrimi ACIKCA
    gosteren ikinci bir olcum de yapilir: SALT ASCII 40 vs 41 cp."""
    assert N._MAX_SPEAKER_NAME_LEN == 40
    assert _split_speaker_label("a" * 40 + ": x")[0] == "a" * 40
    assert _split_speaker_label("a" * 41 + ": x")[0] is None

    karma_nfc = "á" + "b" * 39
    assert len(karma_nfc) == 40
    assert _split_speaker_label(karma_nfc + ": x")[0] == karma_nfc
    karma_nfd = unicodedata.normalize("NFD", karma_nfc)
    assert len(karma_nfd) == 41
    assert _split_speaker_label(karma_nfd + ": x")[0] is None


# ===========================================================================
# 7. K31 (a) / (b)
# ===========================================================================


def test_k31a_ayni_ad_iki_etiket_birleşir_etiket_metinden_duser() -> None:
    """K31 (a): ikinci etiket K9'a gore TANINIYORSA ve ad AYNIYSA etiket
    METINDEN DUSER, iki blok TEK segmentte birlesir ve segment TEK
    `speaker` tasir."""
    segs = normalize(
        [blk("Ada: merhaba", 10, 0, h=20), blk("Ada: nasilsin", 10, 25, h=20)],
        OcrPreset.DIALOGUE,
    )
    assert len(segs) == 1
    assert segs[0].text == "merhaba nasilsin"
    assert segs[0].speaker == "Ada"
    assert segs[0].source_blocks == (0, 1)
    assert "Ada:" not in segs[0].text


def test_k31b_taninmayan_ikinci_etiket_metinde_kalir_ilk_konusmaciya_atfedilir() -> None:
    """K31 (b): ikinci etiket K9'un ad suzgecinden GECEMIYORSA (rakamli
    ad) o blok `speaker=None` KALIR, K15'in `X/None` satiriyla bloklar
    YINE birlesir, ETIKET METNIN ICINDE KALIR ve segment ILK konusmaciya
    atfedilir. (b) urun etkisi olarak (a)'dan kotudur ve BILINCLI
    sinirdir."""
    segs = normalize(
        [blk("Ada: merhaba", 10, 0, h=20), blk("Ada2: nasilsin", 10, 25, h=20)],
        OcrPreset.DIALOGUE,
    )
    assert len(segs) == 1
    assert segs[0].text == "merhaba Ada2: nasilsin"
    assert "Ada2:" in segs[0].text
    assert segs[0].speaker == "Ada"
    assert segs[0].source_blocks == (0, 1)


def test_k31_iki_farkli_TANINAN_ad_birlesmez_cjk_dahil() -> None:
    """K31'in KONTROL satiri: iki FARKLI TANINAN ad ASLA birlesmez (K15
    `X/Y` satiri) -- ASCII'de de CJK'da da. Bu K9'un asil yasagidir."""
    segs = normalize(
        [blk("Ada: merhaba", 10, 0, h=20), blk("Bora: nasilsin", 10, 25, h=20)],
        OcrPreset.DIALOGUE,
    )
    assert bolumleme(segs) == [(0,), (1,)]
    assert [s.speaker for s in segs] == ["Ada", "Bora"]

    segs = normalize(
        [blk("勇者：こんにちは", 10, 0, h=20), blk("魔王：ふふふ", 10, 25, h=20)],
        OcrPreset.DIALOGUE,
    )
    assert bolumleme(segs) == [(0,), (1,)]
    assert [s.speaker for s in segs] == ["勇者", "魔王"]


def test_k31_a_ve_b_cjk_yuzeyinde_de_ayni_davraniyor() -> None:
    """K31 (a)/(b) CJK'da: kararin metni ASCII ornekleriyle yazilmis; ayni
    iki alt durum fullwidth ayracli CJK etiketle de aynen olusmali --
    (a) `勇者：`/`勇者：` birleşir, etiket duser; (b) `勇者2：` taninmaz,
    metinde kalir."""
    a = normalize(
        [blk("勇者：こんにちは", 10, 0, h=20), blk("勇者：げんきですか", 10, 25, h=20)],
        OcrPreset.DIALOGUE,
    )
    assert len(a) == 1 and a[0].speaker == "勇者"
    assert a[0].text == "こんにちは げんきですか"

    b = normalize(
        [blk("勇者：こんにちは", 10, 0, h=20), blk("勇者2：げんきですか", 10, 25, h=20)],
        OcrPreset.DIALOGUE,
    )
    assert len(b) == 1 and b[0].speaker == "勇者"
    assert b[0].text == "こんにちは 勇者2：げんきですか"


def test_k31b_nfd_ad_ikinci_etikette_de_metinde_kalir() -> None:
    """K31 (b)'nin K32'ye baglanan yolu: "K32'deki NFD adlar" da ayni
    davranir -- ikinci etiket NFD ise taninmaz, metinde kalir, segment ilk
    konusmaciya atfedilir."""
    nfd_ad = unicodedata.normalize("NFD", "Ádá")
    segs = normalize(
        [blk("Ada: merhaba", 10, 0, h=20), blk(nfd_ad + ": nasilsin", 10, 25, h=20)],
        OcrPreset.DIALOGUE,
    )
    assert len(segs) == 1
    assert segs[0].speaker == "Ada"
    assert nfd_ad + ":" in segs[0].text


# ===========================================================================
# 8. YOZLASMIS GEOMETRI
# ===========================================================================


@pytest.mark.parametrize(
    "ad,w,h", [("h=0", 300, 0), ("h=-5", 300, -5), ("w=0", 0, 20), ("w=-7", -7, 20), ("w=0,h=0", 0, 0)]
)
@pytest.mark.parametrize("preset", GRUPLAYAN)
def test_k16_yozlasmis_blok_gruplanmaz_ama_segment_uretir(
    ad: str, w: int, h: int, preset: OcrPreset
) -> None:
    """K16: `ref_height <= 0` ya da `ref_width <= 0` ise gruplama KOSULSUZ
    reddedilir -- ama blok YOK EDILMEZ, kendi segmentini uretir (K12'nin
    "kurtarma yok" kurali metin KAYBI anlamina gelmez)."""
    segs = normalize(
        [blk("Ada: bir", 10, 0, w=300, h=20), blk("iki", 10, 25, w=w, h=h)], preset
    )
    assert bolumleme(segs) == [(0,), (1,)], f"{ad}: yozlasmis blok GRUPLANDI"
    assert [s.text for s in segs] == ["bir", "iki"]
    assert segs[1].speaker is None, f"{ad}: yozlasmis sinirda MIRAS uygulanmis"


def test_k16_x_k28_birlesik_aday_ham_ilk_satirin_h_sifirini_gizlemez() -> None:
    """K28'in SAG TARAF regresyon testi, yozlasmis geometri sinifinda
    (kararin "olcu 2 / A2 varyanti" sinifi -- Tester-C merceğine acikca
    verildi).

    Aday (`nxt`) adim 3'te hyphen ile BIRLESMIS bir `_Item`'dir; birlesik
    kutu `h=25` gosterir ve `gap=5 < 0.8*20=16` verir -> BIRLESIK kutuyla
    bakan bir uygulama MIRAS uygular. Ham ILK satirin `h`'si `0`'dir ->
    `ref_height=0` -> `"height"` -> K16 uyarinca miras UYGULANMAZ.
    Kontrol vakasi (ham ilk satir `h=20`) mirasin gercekten
    uygulanabildigini gosterir, yani test totoloji degildir."""
    uzun = "a" * 270
    bozuk = normalize(
        [
            blk("Ada: " + uzun, 10, 0, w=300, h=20),
            blk("keli-", 10, 25, w=300, h=0),        # HAM ilk satir h=0
            blk("me devam", 10, 30, w=300, h=20),
        ],
        OcrPreset.DIALOGUE,
    )
    assert bolumleme(bozuk) == [(0,), (1, 2)]
    assert [s.speaker for s in bozuk] == ["Ada", None], "K16 gizlendi -- K28 SAG TARAF REGRESYONU"

    saglam = normalize(
        [
            blk("Ada: " + uzun, 10, 0, w=300, h=20),
            blk("keli-", 10, 25, w=300, h=20),
            blk("me devam", 10, 30, w=300, h=20),
        ],
        OcrPreset.DIALOGUE,
    )
    assert bolumleme(saglam) == [(0,), (1, 2)]
    assert [s.speaker for s in saglam] == ["Ada", "Ada"], "kontrol vakasi miras VERMELI"


@pytest.mark.parametrize("preset", DORT_ON_AYAR)
def test_ayni_y_x_cifti_tasiyan_bloklar_kararli_sirada_islenir(preset: OcrPreset) -> None:
    """K3 + K28: adim 1 `sorted(enumerate(blocks), key=(y, x))` KARARLIDIR
    (esitlikte GIRDI INDEKSI kazanir); `_raw_query_pair`'in okuma sirasi
    ise ucuncu bilesen olarak indeksi ACIKCA yazar. Ikisi AYNI sirayi
    vermeli -- aksi halde ayni `(y,x)`'li bloklarda sorgu yanlis tarafa
    bakar."""
    bl = [
        blk("ucuncu", 10, 100, h=20),
        blk("Ada: bir", 10, 100, h=20),
        blk("ikinci", 10, 100, h=20),
    ]
    segs = normalize(bl, preset)
    assert [s.text for s in segs][0] == "ucuncu"
    assert all(list(s.source_blocks) == sorted(s.source_blocks) for s in segs)


def test_okuma_sirasi_esit_anahtarlarda_adim1_ile_uyusur_fuzz() -> None:
    """Yukaridaki testin MAKINE denetimi: 500 sirasiz/esit-anahtarli
    girdide adim 1'in kararli `(y, x)` siralamasi ile kitin/`_raw_query_
    pair`'in `(y, x, indeks)` siralamasi BIREBIR ayni olmali."""
    r = random.Random(4242)
    uyusmazlik = 0
    for _ in range(500):
        n = r.randint(3, 9)
        bloklar = [
            blk("m" * r.randint(1, 5), r.choice([0, 0, 10]), r.choice([0, 0, 10, 10, 25]),
                h=r.choice([0, 10, 20]))
            for _ in range(n)
        ]
        adim1 = [i for i, _ in sorted(enumerate(bloklar), key=lambda p: (p[1].bbox.y, p[1].bbox.x))]
        okuma = sorted(range(n), key=lambda i: (bloklar[i].bbox.y, bloklar[i].bbox.x, i))
        uyusmazlik += adim1 != okuma
    assert uyusmazlik == 0


@pytest.mark.parametrize(
    "ch,korunur",
    [("力", True), ("a", True), ("1", True), ("?", True), ("？", True), ("。", False), ("-", False)],
)
def test_k4_tek_karakterli_blok_karari_yozlasmis_geometriden_bagimsiz(ch: str, korunur: bool) -> None:
    """K4 kararı SALT SOZLUKSELDIR: `w=0, h=0` gibi tamamen yozlasmis bir
    kutu tek-karakter kararini DEGISTIRMEMELI (adim 2, adim 5'ten once
    calisir ve geometriye BAKMAZ)."""
    cikti = normalize([blk(ch, 10, 0, w=0, h=0)], OcrPreset.MENU)
    assert ([s.text for s in cikti] == [ch]) is korunur


def test_yozlasmis_geometri_ve_kirk_blok_birlikte_cokme_uretmez() -> None:
    """Bes sinifin KESISIMI: >=40 blok + yozlasmis genislik/yukseklik +
    negatif koordinat + sirasiz + esik-alti bloklar. Cokme YOK ve K23
    tutuyor."""
    ihlal = 0
    for t in range(40):
        r = random.Random(70000 + t)
        n = r.randint(40, 60)
        bl = [
            blk(
                ("Ada: " if i % 6 == 0 else "") + "x" * r.randint(1, 90),
                r.choice([-20, 0, 10, 500]),
                r.randint(0, 400),
                w=r.choice([-5, 0, 1, 300]),
                h=r.choice([-3, 0, 1, 20]),
                confidence=r.choice([0.9, 0.44, 0.6]),
            )
            for i in range(n)
        ]
        r.shuffle(bl)
        for preset in DORT_ON_AYAR:
            acik = bolumleme(_normalize_impl(bl, preset, apply_inheritance=True))
            kapali = bolumleme(_normalize_impl(bl, preset, apply_inheritance=False))
            ihlal += acik != kapali
    assert ihlal == 0


# ===========================================================================
# 9. KOTU KULLANIM YUZEYI (K28'in yeni parametresi dahil)
# ===========================================================================


def test_kotu_kullanim_group_blocks_verilmezse_uzunluk_sinirinda_gurultulu_kirilir() -> None:
    """K28'in BILINCLI takasi: `_group`'un `blocks=()` varsayilani
    `IndexError` uretir -- SESSIZ YANLIS URETMEZ. Patlama GECIKMELIDIR
    (yalniz `reason == "length" and nxt.speaker is None` sinirinda), bu
    yuzden IKI yol da pinlenir: sinir DOGARSA patlar, DOGMAZSA calisir."""
    params = get_params(OcrPreset.DIALOGUE)
    uzun = _Item(text="a" * 270, bbox=Rect(x=10, y=0, w=300, h=20), speaker="Ada", source_blocks=(0,))
    devam = _Item(text="b" * 20, bbox=Rect(x=10, y=25, w=300, h=20), speaker=None, source_blocks=(1,))
    with pytest.raises(IndexError):
        _group([uzun, devam], params)

    kisa = _Item(text="kisa", bbox=Rect(x=10, y=0, w=300, h=20), speaker="Ada", source_blocks=(0,))
    uzak = _Item(text="metin", bbox=Rect(x=10, y=500, w=300, h=20), speaker=None, source_blocks=(1,))
    assert [i.text for i in _group([kisa, uzak], params)] == ["kisa", "metin"]


def test_kotu_kullanim_suzulmus_blocks_sessiz_yanlis_degil_indexerror() -> None:
    """`_raw_query_pair` sozlesmesi: `blocks` OZGUN listedir. Bir sonraki
    ajanin klasik hatasi -- esik filtresinden GECMIS listeyi gecirmek --
    indeks kaymasi uretir. Olculdu: sessizce YANLIS sonuc degil,
    `IndexError`."""
    params = get_params(OcrPreset.DIALOGUE)
    tam = [blk("x", 10, 0, h=20), blk("Ada: " + "a" * 270, 10, 25, h=20), blk("b" * 20, 10, 50, h=20)]
    items = [
        _Item(text="a" * 270, bbox=tam[1].bbox, speaker="Ada", source_blocks=(1,)),
        _Item(text="b" * 20, bbox=tam[2].bbox, speaker=None, source_blocks=(2,)),
    ]
    dogru = _group(list(items), params, blocks=tam)
    assert [i.speaker for i in dogru] == ["Ada", "Ada"]
    with pytest.raises(IndexError):
        _group(list(items), params, blocks=tam[1:])


def test_kotu_kullanim_genel_api_sizmasi_yok() -> None:
    """K23'un test kancasi ve K28'in `blocks` parametresi GENEL API'ye
    SIZMAMALI: `__all__` yalniz `normalize`; `normalize`'in imzasi iki
    parametreli; ic fonksiyonlar `_` on ekli ve keyword-only ek
    parametreler VARSAYILANLI (dolayisiyla mevcut cagiranlari kirmiyor)."""
    assert N.__all__ == ("normalize",)
    assert list(inspect.signature(N.normalize).parameters) == ["blocks", "preset"]

    p_impl = inspect.signature(N._normalize_impl).parameters
    assert p_impl["apply_inheritance"].kind is inspect.Parameter.KEYWORD_ONLY
    assert p_impl["apply_inheritance"].default is True

    p_group = inspect.signature(N._group).parameters
    assert p_group["blocks"].kind is inspect.Parameter.KEYWORD_ONLY
    assert p_group["blocks"].default == ()
    assert p_group["apply_inheritance"].kind is inspect.Parameter.KEYWORD_ONLY


def test_kotu_kullanim_apply_inheritance_bayragi_uretim_disi_diye_isaretli() -> None:
    """`apply_inheritance=False` bir sonraki ajani "mirasi kapatabilirim"
    diye DAVET ETMEMELI. Docstring bunu ACIKCA denetim kancasi ilan
    ediyor mu, ve bayrak gercekten YALNIZCA `speaker`'i mi degistiriyor
    (bolumleme birebir ayni)?"""
    d = N._normalize_impl.__doc__ or ""
    for anahtar in ("SADECE K23", "MAKINE DENETIMI", "DISARIYA", "SIZMAZ"):
        assert anahtar in d, f"docstring {anahtar!r} demiyor"

    bl = [blk("Ada: " + "a" * 270, 10, 0, h=20), blk("b" * 20, 10, 25, h=20)]
    acik = _normalize_impl(bl, OcrPreset.DIALOGUE, apply_inheritance=True)
    kapali = _normalize_impl(bl, OcrPreset.DIALOGUE, apply_inheritance=False)
    assert bolumleme(acik) == bolumleme(kapali)
    assert [s.text for s in acik] == [s.text for s in kapali]
    assert [s.bbox for s in acik] == [s.bbox for s in kapali]
    assert [s.speaker for s in acik] == ["Ada", "Ada"]
    assert [s.speaker for s in kapali] == ["Ada", None]


def test_raw_query_pair_sinir_durumlari() -> None:
    """`_raw_query_pair`: `bbox` DISINDAKI her alan AYNEN korunur
    (`speaker`, `text`, `source_blocks` -- sonuncusu olcunun onkosulu);
    yetersiz `blocks` ya da BOS `source_blocks` `IndexError` verir."""
    sol_oge = _Item(text="a", bbox=Rect(x=0, y=0, w=10, h=10), speaker="勇者", source_blocks=(0,))
    sag_oge = _Item(text="b", bbox=Rect(x=0, y=20, w=10, h=10), speaker=None, source_blocks=(1,))
    bloklar = [blk("a", 0, 0, w=10, h=10), blk("b", 0, 20, w=10, h=10)]

    sol, sag = _raw_query_pair(sol_oge, sag_oge, bloklar)
    assert (sol.speaker, sol.text, sol.source_blocks) == ("勇者", "a", (0,))
    assert (sag.speaker, sag.text, sag.source_blocks) == (None, "b", (1,))
    assert sol.bbox == bloklar[0].bbox and sag.bbox == bloklar[1].bbox

    with pytest.raises(IndexError):
        _raw_query_pair(sol_oge, sag_oge, ())
    with pytest.raises(IndexError):
        _raw_query_pair(_Item("a", Rect(0, 0, 1, 1), None, ()), sag_oge, bloklar)


def test_group_bos_ve_tek_ogeli_dogrudan_cagri_kirilmaz() -> None:
    """K28 imza secimi (`blocks` KEYWORD-ONLY ve VARSAYILANLI) tam olarak
    bu cagri bicimini korumak icin yapildi -- pinlenir."""
    params = get_params(OcrPreset.DIALOGUE)
    assert _group([], params) == []
    tek = _Item(text="tek", bbox=Rect(x=0, y=0, w=10, h=10), speaker=None, source_blocks=(0,))
    assert [i.text for i in _group([tek], params)] == ["tek"]


# ===========================================================================
# 10. K28 SOL TARAF -- "yalniz-etiket blogu" yuzeyi (sefin adlandirdigi EK YUZEY)
# ===========================================================================


def test_k28_sol_taraf_sirasiz_girdide_okuma_sirasini_kullanir_indeks_sirasini_degil() -> None:
    """Sef, `source_blocks[-1]`'in (INDEKS sirasi) sirasiz girdide
    YALNIZ-ETIKET blogunu gosterebilecegini yazdi. K28 okuma sirasina
    gectigi icin bu yuzey kapanmali. Vaka ASCII-DISI etiketle kurulur
    (kitin uretmedigi sinif):

        idx0 = govde  (y=25, bottom=45)
        idx1 = devam  (y=50)
        idx2 = ETIKET `勇者：` (y=0, bottom=20)   <- INDEKS olarak SON

    tail.source_blocks = (0, 2):
      `[-1]` (indeks)      -> idx2 etiket, gap = 50-20 = 30 > 16 -> MIRAS YOK
      okuma sirasi (y,x,i) -> idx0 govde,  gap = 50-45 =  5 < 16 -> MIRAS

    Beklenen: MIRAS uygulanir."""
    uzun = "あ" * 270
    bl = [
        blk(uzun, 10, 25, w=300, h=20),
        blk("い" * 20, 10, 50, w=300, h=20),
        blk("勇者：", 10, 0, w=300, h=20),
    ]
    segs = normalize(bl, OcrPreset.DIALOGUE)
    assert bolumleme(segs) == [(0, 2), (1,)]
    assert [s.speaker for s in segs] == ["勇者", "勇者"], (
        "K28 SOL TARAF: okuma sirasi yerine indeks sirasi kullanilmis olabilir"
    )


def test_k28_miras_sorgusunun_hicbir_tarafi_yalniz_etiket_blogu_olmuyor() -> None:
    """Ayni yuzeyin MAKINE denetimi. `_raw_query_pair`'e kanca takilir
    (URUN KODU DEGISMEZ, `monkeypatch` ile geri alinir) ve ASCII-disi
    etiketli, sirasiz, yalniz-etiket bloklu bir derlemde her miras
    sorgusunun iki tarafi da kaydedilir.

    Iki iddia olculur:
      (1) sorgunun HICBIR tarafi yalniz-etiket blogu olmuyor;
      (2) SOL tarafta okuma-sirasi-son ile `max(indeks)` GERCEKTEN
          ayrisiyor (aksi halde (1) totolojik olurdu -- derlem `[-1]`
          uygulamasini ayirt edemiyor demektir)."""
    orijinal = N._raw_query_pair
    kayit: list[tuple[int, int]] = []
    ayrisma = 0

    def kancali(tail: _Item, nxt: _Item, blocks):  # type: ignore[no-untyped-def]
        nonlocal ayrisma
        sol, sag = orijinal(tail, nxt, blocks)
        sol_idx = next(i for i in tail.source_blocks if blocks[i].bbox == sol.bbox)
        sag_idx = next(i for i in nxt.source_blocks if blocks[i].bbox == sag.bbox)
        kayit.append((sol_idx, sag_idx))
        if sol_idx != max(tail.source_blocks):
            ayrisma += 1
        return sol, sag

    N._raw_query_pair = kancali  # type: ignore[assignment]
    try:
        sol_etiket = sag_etiket = 0
        for t in range(150):
            r = random.Random(31000 + t)
            n = r.randint(4, 22)
            bl = []
            y = 0
            for _ in range(n):
                tur = r.random()
                if tur < 0.25:
                    metin = r.choice(["勇者：", "魔王:", "Ада:", "むらびと："])
                elif tur < 0.45:
                    metin = r.choice(["勇者：", "Ада:"]) + "あ" * r.randint(20, 120)
                else:
                    metin = "あ" * r.randint(20, 140)
                h = r.choice([12, 18, 20, 30])
                bl.append(blk(metin, r.choice([0, 10, 12]), y, w=r.choice([200, 300]), h=h))
                y += h + r.choice([1, 3, 8, 45])
            r.shuffle(bl)
            yalniz_etiket = {
                i
                for i, b in enumerate(bl)
                if _split_speaker_label(b.text)[0] is not None
                and not _split_speaker_label(b.text)[1]
            }
            for preset in GRUPLAYAN:
                kayit.clear()
                normalize(bl, preset)
                for sol_idx, sag_idx in kayit:
                    sol_etiket += sol_idx in yalniz_etiket
                    sag_etiket += sag_idx in yalniz_etiket
    finally:
        N._raw_query_pair = orijinal  # type: ignore[assignment]

    assert sol_etiket == 0, f"SOL taraf {sol_etiket} kez yalniz-etiket blogu oldu"
    assert sag_etiket == 0, f"SAG taraf {sag_etiket} kez yalniz-etiket blogu oldu"
    assert ayrisma > 0, (
        "derlem `[-1]` uygulamasini AYIRT EDEMIYOR -- yukaridaki iki assert totolojik"
    )


# ===========================================================================
# 11. BES SINIFIN UZERINDE DEGISMEZ FUZZ'I
# ===========================================================================


def test_bes_sinif_birlikte_degismezleri_bozmuyor() -> None:
    """Bes sinifi AYNI girdide birlestiren fuzz (emoji/ZWJ/astral +
    `monitor_index != 0` + `dpi_scale != 1.0` + >=40 blok + ASCII-disi
    etiket + yalniz-etiket + sirasiz + esik-alti + yozlasmis kutu).

    Denetlenenler: cokme yok · K8 (artan/tekrarsiz/ayrik/aralikta) ·
    K3 (cikti sirasi) · K23 (miras acik/kapali bolumleme ayni) ·
    K12 (bos metinli segment yok) · `Segment.bbox`'in `monitor_index`/
    `dpi_scale`'i KAYNAK bloklarininkiyle AYNI."""
    adlar = ["勇者", "魔王", "용사", "Ада", "مرحبا", "María", "𝐀𝐁"]
    govdeler = [
        "こんにちは世界", "안녕하세요", "привет мир", "أهلا بالعالم",
        "hola qué tal", ZWJ_AILE + " aile", BAYRAK_TR + " bayrak",
        ASTRAL_KANJI + " astral", "☀️ gunes", "kelime-", "devam eden satir",
    ]
    for t in range(60):
        r = random.Random(500000 + t)
        n = r.randint(40, 70)
        mon = r.choice([0, 1, 2, 7])
        dpi = r.choice([1.0, 1.25, 1.5, 2.0])
        bl = []
        y = 0
        for _ in range(n):
            govde = " ".join(r.choice(govdeler) for _ in range(r.randint(1, 8)))
            tur = r.random()
            if tur < 0.18:
                metin = r.choice(adlar) + r.choice([":", "："]) + " " + govde
            elif tur < 0.26:
                metin = r.choice(adlar) + r.choice([":", "："])
            else:
                metin = govde
            h = r.choice([0, 1, 12, 18, 20, 30])
            bl.append(
                blk(metin, r.choice([-20, 0, 10, 12, 400]), y,
                    w=r.choice([0, 1, 200, 300, 320]), h=h,
                    confidence=r.choice([0.9, 0.9, 0.7, 0.44, 0.55, 0.60, 0.65]),
                    monitor_index=mon, dpi_scale=dpi)
            )
            y += max(h, 1) + r.choice([1, 3, 8, 50])
        r.shuffle(bl)

        for preset in DORT_ON_AYAR:
            segs = normalize(bl, preset)
            gorulen: set[int] = set()
            for s in segs:
                sb = s.source_blocks
                assert sb and list(sb) == sorted(set(sb))
                assert not (gorulen & set(sb))
                assert 0 <= min(sb) and max(sb) < len(bl)
                gorulen |= set(sb)
                assert s.text.strip(), "K12: bos metinli Segment sizdi"
                for i in sb:
                    assert bl[i].bbox.monitor_index == s.bbox.monitor_index
                    assert bl[i].bbox.dpi_scale == s.bbox.dpi_scale
            anahtarlar = [(s.bbox.y, s.bbox.x) for s in segs]
            assert anahtarlar == sorted(anahtarlar), "K3 sira bozuk"
            assert bolumleme(_normalize_impl(bl, preset, apply_inheritance=True)) == bolumleme(
                _normalize_impl(bl, preset, apply_inheritance=False)
            ), "K23 IHLALI"
