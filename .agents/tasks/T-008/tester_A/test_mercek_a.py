"""Tester-A — mercek A (geometri, betik, sözleşme), T-008 tur 1. KÖR: yalnız
packet.md v2 + modül docstring'i + sentetik `TextBlock`.

Bölümler: A0 bariyer · A1 K2 geometri/eşik sınırları · A2 satır bölümleme vs
satır içi sıralama · A3 K3 betik · A4 K5 alanlar · A5 K6 okuma sırası.
Ürünü bozan ölçülmüş sınıf (uzun kutu köprüsü, gerçek OCR geometrisi) AYRI
dosyada: `test_ret_a_uzun_kutu_koprusu.py` (şu an KIRMIZI — ret kanıtı).
"""
from __future__ import annotations

import itertools
import json
import math
import random
from dataclasses import asdict

import pytest

from src.contracts.models import Rect, TextBlock
from src.ocr import satir_birlestirici as modul
from src.ocr.satir_birlestirici import (
    DIKEY_ORTUSME_ESIGI,
    YATAY_BOSLUK_ESIGI,
    satirlari_birlestir,
)


def B(
    x: int, y: int, w: int, h: int, t: str = "a", c: float = 1.0,
    m: int = 0, d: float = 1.0, lb: tuple[Rect, ...] = (),
) -> TextBlock:
    return TextBlock(text=t, bbox=Rect(x, y, w, h, m, d), confidence=c, line_boxes=lb)


def metinler(cikti: list[TextBlock]) -> list[str]:
    return [b.text for b in cikti]


def parca_x(b: TextBlock) -> list[int]:
    return [r.x for r in b.line_boxes]


# ---------------------------------------------------------------------------
# A0 — bariyer pozitif kontrolü (§4.6/10)
# ---------------------------------------------------------------------------
def test_a0_bariyer_atesliyor() -> None:
    with pytest.raises(RuntimeError, match="K1 bariyeri"):
        import rapidocr  # noqa: F401
    with pytest.raises(RuntimeError, match="K1 bariyeri"):
        import onnxruntime  # type: ignore[import-untyped]  # noqa: F401


def test_a0_sabitler_paket_degerinde() -> None:
    assert DIKEY_ORTUSME_ESIGI == 0.5
    assert YATAY_BOSLUK_ESIGI == 0.75
    assert modul.__all__ == ("satirlari_birlestir", "DIKEY_ORTUSME_ESIGI", "YATAY_BOSLUK_ESIGI")


# ---------------------------------------------------------------------------
# A1 — K2 geometri, eşik sınırları
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("ortusme, beklenen", [(49, 2), (50, 1), (51, 1)])
def test_a1_dikey_esik_sinirda_h100(ortusme: int, beklenen: int) -> None:
    """Örtüşme `>= 0.5*min(h)`: 49 ayrı, 50 ve 51 birleşik (boşluk 0)."""
    a = B(0, 0, 100, 100, "a")
    b = B(100, 100 - ortusme, 100, 100, "b")
    assert len(satirlari_birlestir([a, b])) == beklenen


@pytest.mark.parametrize("bosluk, beklenen", [(74, 1), (75, 1), (76, 2)])
def test_a1_yatay_esik_sinirda_h100(bosluk: int, beklenen: int) -> None:
    """Boşluk `<= 0.75*min(h)`: 74/75 birleşik, 76 ayrı."""
    a = B(0, 0, 100, 100, "a")
    b = B(100 + bosluk, 0, 100, 100, "b")
    assert len(satirlari_birlestir([a, b])) == beklenen


@pytest.mark.parametrize("bosluk, beklenen", [(7, 1), (8, 2)])
def test_a1_yatay_esik_min_h_kucuk_kutuyla(bosluk: int, beklenen: int) -> None:
    """min(h)=10 → 0.75*10 = 7.5: 7 birleşir, 8 ayrılır (büyük kutu h=40 belirlemez)."""
    a = B(0, 0, 50, 40, "A")
    b = B(50 + bosluk, 5, 20, 10, "b")
    assert len(satirlari_birlestir([a, b])) == beklenen


def test_a1_esik_orijinal_yukseklikle_y2_fixture() -> None:
    """KRT Y2: A(0,0,100,40)+b(105,10,15,20)+C(150,0,100,40). b–C boşluğu 30 >
    0.75*min(20,40)=15 → C ayrı. Birleşik h=40 kullanılsaydı 30 <= 30 → birleşirdi."""
    cikti = satirlari_birlestir([B(0, 0, 100, 40, "A"), B(105, 10, 15, 20, "b"), B(150, 0, 100, 40, "C")])
    assert metinler(cikti) == ["A b", "C"]


def test_a1_esit_x_yeni_grup_acar_iki_yonde() -> None:
    """`x` KESİN ilerlemeli: aynı x'teki ikinci kutu (çift tespit) ayrı kalır, girdi sırasından bağımsız."""
    a, b = B(0, 0, 100, 20, "a"), B(0, 0, 50, 20, "b")
    assert len(satirlari_birlestir([a, b])) == 2
    assert len(satirlari_birlestir([b, a])) == 2


@pytest.mark.parametrize("bosluk", [-1, -20, -40])
def test_a1_cakisma_negatif_bosluk_komsudur(bosluk: int) -> None:
    """Negatif boşluk (−1, −h, −2h) komşudur; bbox birleşimi doğru."""
    a = B(0, 0, 100, 20, "a")
    b = B(100 + bosluk, 0, 100, 20, "b")
    cikti = satirlari_birlestir([a, b])
    assert metinler(cikti) == ["a b"]
    assert cikti[0].bbox == Rect(0, 0, 200 + bosluk, 20)


def test_a1_ic_ice_kutu_x_ilerliyorsa_birlesir_belgeli_sinir() -> None:
    """Docstring: iç içe kutu x ilerliyorsa BİRLEŞİR ve metin çoğalır (bilinen sınır)."""
    cikti = satirlari_birlestir([B(0, 0, 200, 20, "dis"), B(50, 2, 40, 16, "ic")])
    assert metinler(cikti) == ["dis ic"]
    assert cikti[0].bbox == Rect(0, 0, 200, 20)


def test_a1_ic_ice_kutu_ayni_x_ayri_kalir() -> None:
    cikti = satirlari_birlestir([B(0, 0, 200, 20, "dis"), B(0, 2, 40, 16, "ic")])
    assert metinler(cikti) == ["dis", "ic"]


def test_a1_uzun_kutu_koprusu_T_ortada_implementer_fixture() -> None:
    """Docstring fixture'ı: a(0,5) T(60,0,h60) c(110,40) → 'a T', 'c'."""
    cikti = satirlari_birlestir([B(0, 5, 50, 20, "a"), B(60, 0, 40, 60, "T"), B(110, 40, 50, 20, "c")])
    assert metinler(cikti) == ["a T", "c"]


def test_a1_uzun_kutu_koprusu_T_solda_iki_satiri_tek_bloga_alir_SINIF() -> None:
    """AYNI fixture, T en solda ve en üstte: T(0,0,40,60) a(50,5) c(110,40) → 'T a c' TEK
    blok — a ve c FARKLI satırlar. Docstring bunu `[ÖLÇÜLMÜYOR]` bırakıyor; sentetik
    kayıt burada, gerçek OCR karşılığı `test_ret_a_uzun_kutu_koprusu.py` + `a6-gercek-ocr.txt`.
    Bu test MEVCUT davranışı sabitler (pozitif kontrol: T'siz a ve c ayrı)."""
    ile = satirlari_birlestir([B(0, 0, 40, 60, "T"), B(50, 5, 50, 20, "a"), B(110, 40, 50, 20, "c")])
    assert metinler(ile) == ["T a c"]
    siz = satirlari_birlestir([B(50, 5, 50, 20, "a"), B(110, 40, 50, 20, "c")])
    assert metinler(siz) == ["a", "c"]


def test_a1_uzun_kutu_solda_iki_kelimelik_satirlari_parcalar_SINIF() -> None:
    """T solda, sağında 2 satır × 2 kelime: T'siz 2 blok, T ile 4 blok ('T a1', 'a2', 'c1', 'c2') —
    satırlar PARÇALANIR (kelime-kelime çeviri sınıfı S3). Mevcut davranış sabitlenir."""
    satirlar = [B(50, 5, 50, 20, "a1"), B(110, 5, 50, 20, "a2"), B(50, 40, 50, 20, "c1"), B(110, 40, 50, 20, "c2")]
    assert metinler(satirlari_birlestir(satirlar)) == ["a1 a2", "c1 c2"]
    ile = satirlari_birlestir([B(0, 0, 40, 60, "T")] + satirlar)
    assert metinler(ile) == ["T a1", "a2", "c1", "c2"]


@pytest.mark.parametrize("w, h", [(50, 0), (0, 20), (50, -5), (-5, 20), (0, 0), (-1, -1)])
def test_a1_yozlasmis_kutu_aynen_gecer_ve_komsulugu_bozmaz(w: int, h: int) -> None:
    a, z, b = B(0, 0, 50, 20, "a"), B(55, 0, w, h, "z"), B(60, 0, 50, 20, "b")
    cikti = satirlari_birlestir([a, z, b])
    assert metinler(cikti) == ["a b", "z"]
    assert cikti[1] is z


def test_a1_farkli_monitor_ve_dpi_birlesmez() -> None:
    assert len(satirlari_birlestir([B(0, 0, 50, 20, "a", m=0), B(55, 0, 50, 20, "b", m=1)])) == 2
    assert len(satirlari_birlestir([B(0, 0, 50, 20, "a", d=1.0), B(55, 0, 50, 20, "b", d=1.25)])) == 2
    # pozitif kontrol: aynı yüzey → birleşir
    assert len(satirlari_birlestir([B(0, 0, 50, 20, "a", m=1, d=1.25), B(55, 0, 50, 20, "b", m=1, d=1.25)])) == 1


def test_a1_iki_monitorde_ayni_koordinat_ayri_yuzey_cikti_sirasi_girdi_indeksi() -> None:
    a = B(0, 0, 50, 20, "a", m=1)
    b = B(0, 0, 50, 20, "b", m=0)
    assert metinler(satirlari_birlestir([a, b])) == ["a", "b"]
    assert metinler(satirlari_birlestir([b, a])) == ["b", "a"]


def test_a1_zincir_gecisli_a_c_komsu_degil_tek_blok() -> None:
    """A–B komşu (boşluk 10), B–C komşu (10), A–C değil (boşluk 70 > 15) → tek blok."""
    cikti = satirlari_birlestir([B(0, 0, 50, 20, "A"), B(60, 0, 50, 20, "B"), B(120, 0, 50, 20, "C")])
    assert metinler(cikti) == ["A B C"]


def test_a1_dar_satir_araligi_0p45h_iki_satir_korunur() -> None:
    """h=20, pitch 11 → örtüşme 9 < 10 → iki satır ayrı, her biri birleşik."""
    l1 = [B(0, 0, 50, 20, "a1"), B(60, 0, 50, 20, "a2"), B(120, 0, 50, 20, "a3")]
    l2 = [B(0, 11, 50, 20, "b1"), B(60, 11, 50, 20, "b2"), B(120, 11, 50, 20, "b3")]
    assert metinler(satirlari_birlestir(l1 + l2)) == ["a1 a2 a3", "b1 b2 b3"]


def test_a1_dar_satir_araligi_0p55h_capraz_birlesme_belgeli_sinir() -> None:
    """h=20, pitch 9 → örtüşme 11 >= 10 → tek 'satır'; x sırasında çapraz birleşme.
    Gerçek düzende pitch < 0.5×kutu h yok (A6: 1.0×font pitch'te bile satırlar korundu)."""
    l1 = [B(0, 0, 50, 20, "a1"), B(60, 0, 50, 20, "a2"), B(120, 0, 50, 20, "a3")]
    l2 = [B(0, 9, 50, 20, "b1"), B(60, 9, 50, 20, "b2"), B(120, 9, 50, 20, "b3")]
    cikti = satirlari_birlestir(l1 + l2)
    assert len(cikti) == 4
    assert "b1 a2" in metinler(cikti)


# ---------------------------------------------------------------------------
# A2 — satır bölümleme vs satır içi sıralama
# ---------------------------------------------------------------------------
KR_SATIR3 = ((82, 212, 131, 34), (225, 209, 72, 40), (305, 209, 69, 39), (386, 208, 70, 41), (467, 210, 141, 37))


def test_a2_y_titresimli_satir_her_permutasyonda_x_sirasinda_tek_blok() -> None:
    bl = [B(x, y, w, h, f"s{i}") for i, (x, y, w, h) in enumerate(KR_SATIR3)]
    for perm in itertools.permutations(bl):
        cikti = satirlari_birlestir(list(perm))
        assert len(cikti) == 1
        assert parca_x(cikti[0]) == [82, 225, 305, 386, 467]
        assert cikti[0].text == "s0 s1 s2 s3 s4"


def test_a2_y_titresimi_tam_yarim_h_birlesir_ustu_ayrilir() -> None:
    """h=20: titreşim 10 (örtüşme 10 >= 10) → tek blok; titreşim 11 (örtüşme 9) → iki satır."""
    on = [B(i * 55, (i % 2) * 10, 50, 20, f"t{i}") for i in range(5)]
    assert len(satirlari_birlestir(on)) == 1
    onbir = [B(i * 55, (i % 2) * 11, 50, 20, f"t{i}") for i in range(5)]
    cikti = satirlari_birlestir(onbir)
    assert len(cikti) == 5, metinler(cikti)  # y=0'lar ile y=11'ler ayrı satır; x zincirleri kopuk


def test_a2_satir_ilk_blogu_kisa_ustte_ayni_satir() -> None:
    """Satırın (y,x)-ilk bloğu kısa (h=12, tırnak/noktalama) → sonrakiler 0.5*12=6 ile ölçülür, satır bütün."""
    cikti = satirlari_birlestir([B(0, 200, 20, 12, "q"), B(25, 200, 60, 40, "a"), B(90, 201, 60, 40, "b")])
    assert metinler(cikti) == ["q a b"]


def test_a2_kisa_ilk_blok_sonraki_satiri_cekmez() -> None:
    cikti = satirlari_birlestir([
        B(0, 200, 20, 12, "q"), B(25, 200, 60, 40, "a"), B(90, 201, 60, 40, "b"),
        B(0, 232, 60, 40, "c"), B(65, 232, 60, 40, "d"),
    ])
    assert metinler(cikti) == ["q a b", "c d"]


def test_a2_kr_17_kutu_2_5_5_5_ve_her_satir_x_sirali() -> None:
    geom = (
        (78, 97, 52, 29), (141, 99, 101, 26),
        (79, 154, 67, 40), (158, 156, 102, 37), (274, 157, 98, 35), (390, 158, 130, 33), (538, 158, 137, 33),
        (82, 212, 131, 34), (225, 209, 72, 40), (305, 209, 69, 39), (386, 208, 70, 41), (467, 210, 141, 37),
        (78, 264, 71, 37), (155, 262, 71, 41), (240, 263, 67, 39), (322, 265, 127, 36), (469, 265, 140, 35),
    )
    bl = [B(x, y, w, h, f"k{i}") for i, (x, y, w, h) in enumerate(geom)]
    rnd = random.Random(11)
    for _ in range(20):
        p = bl[:]
        rnd.shuffle(p)
        cikti = satirlari_birlestir(p)
        assert [len(c.line_boxes) for c in cikti] == [2, 5, 5, 5]
        assert [c.bbox.y for c in cikti] == sorted(c.bbox.y for c in cikti)
        for c in cikti:
            assert parca_x(c) == sorted(parca_x(c))


# ---------------------------------------------------------------------------
# A3 — K3 betik (unicodedata.name, ilk HARF)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "sol, sag, beklenen",
    [
        ("ｶﾀｶﾅ", "ｶﾅ", "ｶﾀｶﾅｶﾅ"),  # yarım genişlik katakana: boşsuz
        ("ＨＰ", "が", "ＨＰ が"),  # tam genişlik Latin ＨＰ + が: boşluk
        ("ᄀ", "ᄂ", "ᄀ ᄂ"),  # Hangul Jamo: boşluk (Hangul sınıfı)
        ("ㄱ", "ㄴ", "ㄱ ㄴ"),  # uyumluluk Jamo: boşluk
        ("豈", "x", "豈 x"),  # CJK uyumluluk ideografı + Latin: boşluk
        ("豈", "村", "豈村"),  # uyumluluk ideografı + CJK: boşsuz
        ("\U0001F600", "村", "\U0001F600 村"),  # emoji harfsiz → LATIN → boşluk
        ("\U0001F468\u200d\U0001F469", "a", "\U0001F468\u200d\U0001F469 a"),  # ZWJ dizisi, harfsiz
        ("「マルクス」", "と", "「マルクス」と"),  # 「マルクス」+と: ilk HARF マ
        ("第３章", "開始", "第３章開始"),  # 第３章 + 開始
        ("村の", "HP", "村の HP"),  # karışık: CJK + Latin → boşluk
        ("HPが", "減った", "HPが 減った"),  # ilk harf Latin → boşluk (K3 tanımı)
        ("ー", "村", "ー村"),  # ー (Lm, KATAKANA-HIRAGANA PROLONGED) CJK
        ("々", "村", "々 村"),  # 々 LATIN sayılır (docstring [ÖLÇÜLMÜYOR])
        ("。", "村", "。 村"),  # harfsiz → LATIN → boşluk (belgeli sınır)
        ("村", "。", "村 。"),
        ("한글", "漢字", "한글 漢字"),  # Hangul + CJK: boşluk
        ("Ⅻ", "村", "Ⅻ 村"),  # Roma rakamı (Nl, isalpha False) → LATIN
        ("\u200b村", "の", "\u200b村の"),  # ZWSP strip edilmez, ilk harf CJK
        ("a\nb", "c", "a\nb c"),  # iç \n korunur
        ("  x  ", "  y  ", "x y"),  # baş/son boşluk strip
    ],
)
def test_a3_betik_tablosu(sol: str, sag: str, beklenen: str) -> None:
    cikti = satirlari_birlestir([B(0, 0, 50, 20, sol), B(55, 0, 50, 20, sag)])
    assert cikti[0].text == beklenen


@pytest.mark.parametrize("bos", ["", "   ", "\t\n", "　"])
def test_a3_bos_parca_metne_katilmaz_kutusu_katilir(bos: str) -> None:
    cikti = satirlari_birlestir([B(0, 0, 50, 20, "村"), B(55, 0, 50, 20, bos), B(110, 0, 50, 20, "の")])
    assert cikti[0].text == "村の"
    assert len(cikti[0].line_boxes) == 3
    assert cikti[0].bbox == Rect(0, 0, 160, 20)


def test_a3_hepsi_bos_metin_bos_string() -> None:
    cikti = satirlari_birlestir([B(0, 0, 50, 20, ""), B(55, 0, 50, 20, "  ")])
    assert cikti[0].text == ""


def test_a3_bos_parca_betik_baglamini_tasimaz() -> None:
    """CJK, (boş), Latin → 'CJK Latin' (boşluk); CJK, (boş), CJK → boşsuz."""
    assert satirlari_birlestir([B(0, 0, 50, 20, "村"), B(55, 0, 50, 20, ""), B(110, 0, 50, 20, "HP")])[0].text == "村 HP"
    assert satirlari_birlestir([B(0, 0, 50, 20, "村"), B(55, 0, 50, 20, ""), B(110, 0, 50, 20, "の")])[0].text == "村の"


# ---------------------------------------------------------------------------
# A4 — K5 alanlar
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "guvenler, beklenen",
    [
        ([math.nan, 0.5, 0.7], 0.5), ([0.5, math.nan, 0.7], 0.5), ([0.5, 0.7, math.nan], 0.5),
        ([math.inf, 0.5], 0.5), ([0.5, math.inf], 0.5), ([-1.0, 0.5], -1.0), ([-math.inf, 0.5], -math.inf),
        ([math.nan, math.inf], math.inf),
    ],
)
def test_a4_confidence_min_nan_disi_sira_bagimsiz(guvenler: list[float], beklenen: float) -> None:
    bl = [B(i * 55, 0, 50, 20, f"t{i}", c=c) for i, c in enumerate(guvenler)]
    assert satirlari_birlestir(bl)[0].confidence == beklenen


def test_a4_confidence_hepsi_nan_nan() -> None:
    bl = [B(i * 55, 0, 50, 20, f"t{i}", c=math.nan) for i in range(3)]
    assert math.isnan(satirlari_birlestir(bl)[0].confidence)


def test_a4_bbox_alanlari_int_ve_json() -> None:
    cikti = satirlari_birlestir([B(3, 7, 50, 20, "a"), B(58, 5, 50, 22, "b"), B(112, 6, 50, 20, "c")])
    r = cikti[0].bbox
    assert all(type(v) is int for v in (r.x, r.y, r.w, r.h))
    assert r == Rect(3, 5, 159, 22)
    json.dumps(asdict(r))
    assert isinstance(cikti[0].line_boxes, tuple) and len(cikti[0].line_boxes) == 3


def test_a4_negatif_koordinat_ikinci_monitor() -> None:
    cikti = satirlari_birlestir([B(-2600, -50, 50, 20, "a", m=1), B(-2545, -50, 50, 20, "b", m=1)])
    assert cikti[0].bbox == Rect(-2600, -50, 105, 20, monitor_index=1)


def test_a4_tek_parca_ayni_nesne_line_boxes_dokunulmaz() -> None:
    lb = (Rect(0, 0, 10, 10), Rect(20, 0, 10, 10))
    a = B(0, 0, 50, 20, "a", lb=lb)
    b = B(500, 0, 50, 20, "b")
    cikti = satirlari_birlestir([a, b])
    assert cikti[0] is a and cikti[0].line_boxes is lb
    assert cikti[1] is b and cikti[1].line_boxes == ()


def test_a4_onceden_birlesik_girdi_line_boxes_parcalarin_bbox_i_olur() -> None:
    """Girdi zaten `line_boxes` dolu (ikinci uygulama): yeni `line_boxes` = parçaların bbox'ları,
    iç yapı KAYBOLUR (K4 'bir kez çağır', K5 'parçaların kendi line_boxes'ları değil')."""
    on = satirlari_birlestir([B(0, 0, 50, 20, "a"), B(55, 0, 50, 20, "b")])[0]
    assert len(on.line_boxes) == 2
    tekrar = satirlari_birlestir([on, B(110, 0, 50, 20, "c")])
    assert tekrar[0].text == "a b c"
    assert [r.x for r in tekrar[0].line_boxes] == [0, 110]
    assert tekrar[0].line_boxes[0] == on.bbox


def test_a4_girdi_degismez_ve_deterministik() -> None:
    bl = [B(0, 0, 50, 20, "a", c=0.9), B(55, 1, 50, 20, "b", c=0.5)]
    kopya = list(bl)
    c1 = satirlari_birlestir(bl)
    c2 = satirlari_birlestir(bl)
    assert bl == kopya and all(x is y for x, y in zip(bl, kopya))
    assert c1 == c2
    assert isinstance(c1, list)


def test_a4_girdi_demet_ve_uretec_disi_dizi() -> None:
    bl = (B(0, 0, 50, 20, "a"), B(55, 0, 50, 20, "b"))
    assert metinler(satirlari_birlestir(bl)) == ["a b"]
    assert satirlari_birlestir([]) == []
    tek = B(0, 0, 50, 20, "a")
    assert satirlari_birlestir([tek])[0] is tek


def test_a4_monitor_dpi_ilk_parcadan_yuzey_geregi_hepsinde_ayni() -> None:
    cikti = satirlari_birlestir([B(0, 0, 50, 20, "a", m=2, d=1.5), B(55, 0, 50, 20, "b", m=2, d=1.5)])
    assert cikti[0].bbox.monitor_index == 2 and cikti[0].bbox.dpi_scale == 1.5


# ---------------------------------------------------------------------------
# A5 — K6 okuma sırası
# ---------------------------------------------------------------------------
def test_a5_uc_satir_uc_kutu_tum_permutasyonlar_ayni() -> None:
    bl = [B(cx, cy, 40, 20, f"{r}{c}") for r, cy in enumerate((0, 40, 80)) for c, cx in enumerate((0, 50, 100))]
    ref = satirlari_birlestir(bl)
    assert metinler(ref) == ["00 01 02", "10 11 12", "20 21 22"]
    rnd = random.Random(5)
    for _ in range(50):
        p = bl[:]
        rnd.shuffle(p)
        assert satirlari_birlestir(p) == ref


def test_a5_bagli_y_x_esit_girdi_sirasi_korunur_sinir() -> None:
    a, b = B(0, 0, 50, 20, "a"), B(0, 0, 50, 20, "b")
    assert metinler(satirlari_birlestir([a, b])) == ["a", "b"]
    assert metinler(satirlari_birlestir([b, a])) == ["b", "a"]


def test_a5_cikti_y_x_artan_birlesik_y_min_y() -> None:
    """Aynı 'satırda' iki grup: sağdaki grubun min y daha küçükse önce gelir (belgeli)."""
    sol = [B(0, 105, 50, 20, "s1"), B(55, 100, 50, 20, "s2")]
    sag = [B(400, 98, 50, 20, "d1"), B(455, 100, 50, 20, "d2")]
    cikti = satirlari_birlestir(sol + sag)
    assert metinler(cikti) == ["d1 d2", "s1 s2"]
    assert [(c.bbox.y, c.bbox.x) for c in cikti] == sorted((c.bbox.y, c.bbox.x) for c in cikti)


def test_a5_girdide_bag_yok_ama_cikti_anahtari_bagli_permutasyona_bagli_POZITIF_KONTROL() -> None:
    """Docstring K6: '(y,x) bağı olmayan girdide her permütasyon AYNI listeyi verir'.
    Karşı örnek: C(0,0,10,30) A(0,10,10,20) B(20,0,10,20) — girdide (y,x) bağı YOK,
    ama A+B birleşik bbox'ı (0,0) olur ve C'nin (0,0)'ı ile ÇIKTIDA bağ doğar; sıra
    min girdi indeksiyle çözülür → permütasyon çıktıyı değiştirir. Docstring'in
    cümlesi çıktı anahtarı üzerinden yazılmalı (yükümlülük; ürün etkisi yok —
    normalizer (y,x) ile yeniden sıralar). Bu test AYRIŞMAYI sabitler."""
    C, A, Bb = B(0, 0, 10, 30, "C"), B(0, 10, 10, 20, "A"), B(20, 0, 10, 20, "B")
    girdiler = [C, A, Bb]
    assert len({(b.bbox.y, b.bbox.x) for b in girdiler}) == 3  # girdide bağ yok
    cab = metinler(satirlari_birlestir([C, A, Bb]))
    abc = metinler(satirlari_birlestir([A, Bb, C]))
    assert cab == ["C", "A B"]
    assert abc == ["A B", "C"]
    assert cab != abc


def test_a5_rastgele_bagsiz_girdi_permutasyon_farki_yalniz_cikti_bagindan() -> None:
    """3000 rastgele küçük girdi: permütasyona bağlı çıktı varsa, çıktı anahtarında
    (y,x) bağı VARDIR (yukarıdaki sınıf); başka bir kaynaktan permütasyon farkı yok."""
    rnd = random.Random(3)
    farkli = 0
    for _ in range(3000):
        n = rnd.randint(2, 6)
        seen: set[tuple[int, int]] = set()
        bl = []
        for i in range(n):
            while True:
                x, y = rnd.randint(0, 60), rnd.randint(0, 30)
                if (y, x) not in seen:
                    seen.add((y, x))
                    break
            bl.append(B(x, y, rnd.randint(5, 40), rnd.randint(5, 30), f"t{i}"))
        ref = satirlari_birlestir(bl)
        ref_k = [(o.text, o.bbox) for o in ref]
        for _ in range(4):
            p = bl[:]
            rnd.shuffle(p)
            got = satirlari_birlestir(p)
            if [(o.text, o.bbox) for o in got] != ref_k:
                farkli += 1
                anahtarlar = [(o.bbox.y, o.bbox.x) for o in ref]
                assert len(anahtarlar) != len(set(anahtarlar)), "permütasyon farkı, çıktı bağı olmadan"
                assert sorted(ref_k) == sorted((o.text, o.bbox) for o in got)  # küme aynı, sıra farklı
                break
    assert farkli >= 1  # pozitif kontrol: sınıf gerçekten ateşliyor
