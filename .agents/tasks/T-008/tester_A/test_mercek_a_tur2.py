"""Tester-A — mercek A, T-008 **tur 2** (A2-1 … A2-3). KÖR: yalnız `sef_karari-tur2.md`,
modül docstring'i (garanti alanı), kod ve sentetik `TextBlock`; gerçek OCR yalnız
`a6_tur2_gercek_ocr.py` (ayrı süreç; geometriler oradan gömüldü, `--geometri` çıktısı
`tester_A_evidence/r2-10-*.txt`, `r2-12-*.txt`).

Değişmez (satır bütünlüğü, çizilen satırlar referans kanalı — §4.6/8): hiçbir çıktı bloğu
iki çizilen satırdan KELİME kutusu içermez VE her çizilen satırın kelime kutuları tam olarak
BİR çıktı bloğundadır (etiket kutusu serbest: ayrı ya da bir satıra yapışık).

Bölümler: R1 gerçek OCR etiket varyantları (sağda, merdiven, 3 satır, iki etiket, 1.2×/1.5×)
· R2 sentetik tarama (etiket h × dy × pitch × konum × titreşim) · R3 "en kısa referans"
sınırı: sarkan kısa kutu (yanlış birleşme ⇒ satırlar fiziksel iç içe) ve üst konumlu minik
kutu (yanlış bölünme, sentetik pozitif kontrol; gerçek OCR'da erişilemez, r2-12) · R4 T2-2
aynı-x çifti + K6 daraltılmış cümle fuzz (yükseklikler değişken) · R5 belge sınırları.
"""
from __future__ import annotations

import itertools
import random
from collections.abc import Sequence

import pytest

from src.contracts.models import Rect, TextBlock
from src.ocr.satir_birlestirici import satirlari_birlestir

Kutu = tuple[int, int, int, int]


def B(x: int, y: int, w: int, h: int, t: str = "a") -> TextBlock:
    return TextBlock(text=t, bbox=Rect(x, y, w, h), confidence=0.9)


def metinler(cikti: list[TextBlock]) -> list[str]:
    return [b.text for b in cikti]


def satir_dagilimi(cikti: Sequence[TextBlock], satirlar: Sequence[Sequence[Kutu]]) -> list[set[int]]:
    """Her çizilen satır için: satırın kelime kutularını içeren çıktı bloklarının indeks kümesi.
    Kutular GEOMETRİYLE eşlenir (metinle değil); etiket kutuları listede yoksa sayılmaz."""
    kutu_satir = {Rect(*k): i for i, satir in enumerate(satirlar) for k in satir}
    dagilim: list[set[int]] = [set() for _ in satirlar]
    for b_idx, blok in enumerate(cikti):
        for r in blok.line_boxes or (blok.bbox,):
            if r in kutu_satir:
                dagilim[kutu_satir[r]].add(b_idx)
    return dagilim


def satir_butunlugu(cikti: Sequence[TextBlock], satirlar: Sequence[Sequence[Kutu]]) -> tuple[bool, list[set[int]]]:
    d = satir_dagilimi(cikti, satirlar)
    her_satir_tek_blokta = all(len(s) == 1 for s in d)
    bloklar_ayrik = all(a.isdisjoint(b) for a, b in itertools.combinations(d, 2))
    return her_satir_tek_blokta and bloklar_ayrik, d


# ---------------------------------------------------------------------------
# R1 — gerçek OCR geometrileri (A2-1 varyantları; r2-10-a2-gercek-ocr.txt)
# ---------------------------------------------------------------------------
# (ad, etiket kutuları, çizilen satırlar [kelime kutuları])
GERCEK_VARYANTLAR: list[tuple[str, list[Kutu], list[list[Kutu]]]] = [
    (
        "sagda",  # etiket SAĞDA, dikey ortalı 60 px
        [(608, 62, 119, 62)],
        [[(61, 64, 60, 35), (234, 65, 87, 33), (132, 66, 89, 31), (468, 66, 116, 32), (337, 67, 113, 30)],
         [(364, 109, 59, 35), (292, 110, 60, 34), (221, 111, 62, 32), (62, 112, 146, 31), (437, 112, 115, 31)]],
    ),
    (
        "merdiven",  # satır 0 etiketin SOLUNDA, satır 1 SAĞINDA (implementer'ın 'a T | c' düzeni, gerçek)
        [(213, 59, 122, 67)],
        [[(61, 64, 60, 35), (131, 64, 60, 35)],
         [(361, 110, 88, 33), (463, 111, 117, 32)]],
    ),
    (
        "3satir",  # etiket ÜÇ satırı kaplıyor (96 px); tur 1 kodu: [11,5] — satır 0+1 fermuar (r2-11)
        [(49, 41, 210, 126)],
        [[(278, 64, 59, 35), (450, 65, 88, 33), (348, 66, 88, 32), (685, 67, 114, 30), (554, 68, 112, 29)],
         [(579, 108, 61, 37), (507, 110, 61, 33), (277, 111, 149, 33), (438, 111, 61, 32), (653, 112, 115, 30)],
         [(419, 154, 59, 36), (277, 155, 62, 33), (346, 155, 60, 34), (493, 157, 112, 31), (623, 157, 114, 31)]],
    ),
    (
        "iki_etiket",  # sol + sağ etiket
        [(60, 59, 119, 66), (752, 62, 119, 62)],
        [[(205, 63, 60, 37), (275, 65, 90, 33), (379, 65, 87, 33), (611, 66, 117, 32), (481, 68, 113, 29)],
         [(507, 109, 60, 35), (436, 110, 60, 34), (205, 111, 148, 32), (365, 111, 63, 32), (582, 112, 114, 31)]],
    ),
    (
        "1p2_ust",  # etiket 1.2× satır, üst hizalı (esik ustu, sarkmaz)
        [(60, 66, 72, 40)],
        [[(158, 64, 59, 35), (228, 66, 89, 32), (331, 66, 86, 32), (563, 66, 117, 32), (432, 67, 115, 29)],
         [(460, 109, 59, 35), (387, 110, 61, 34), (318, 111, 60, 32), (532, 111, 117, 33), (158, 112, 147, 31)]],
    ),
    (
        "1p2_orta",  # etiket 1.2×, iki satırın ortasında (hiçbiriyle yeterince örtüşmez -> tek başına)
        [(60, 87, 72, 41)],
        [[(158, 64, 59, 35), (228, 66, 89, 32), (331, 66, 86, 32), (563, 66, 117, 32), (432, 67, 115, 29)],
         [(460, 109, 59, 35), (387, 110, 61, 34), (318, 111, 60, 32), (532, 111, 117, 33), (158, 112, 147, 31)]],
    ),
    (
        "1p5_ust",
        [(62, 68, 86, 47)],
        [[(175, 63, 60, 37), (245, 65, 91, 33), (349, 66, 87, 32), (582, 66, 115, 32), (451, 67, 114, 30)],
         [(478, 109, 60, 35), (335, 110, 62, 33), (406, 110, 60, 34), (176, 111, 147, 32), (551, 111, 115, 32)]],
    ),
    (
        "1p5_orta",
        [(61, 82, 87, 48)],
        [[(176, 64, 58, 35), (245, 65, 91, 33), (349, 66, 87, 32), (582, 66, 115, 32), (451, 67, 113, 29)],
         [(478, 109, 60, 35), (335, 110, 62, 33), (406, 110, 60, 34), (176, 111, 147, 32), (551, 111, 115, 32)]],
    ),
]


def _bloklar(etiketler: list[Kutu], satirlar: list[list[Kutu]], etiketli: bool = True) -> list[TextBlock]:
    bl = [B(*e, f"E{i}") for i, e in enumerate(etiketler)] if etiketli else []
    bl += [B(*k, f"s{i}w{j}") for i, satir in enumerate(satirlar) for j, k in enumerate(satir)]
    return bl


@pytest.mark.parametrize("ad, etiketler, satirlar", GERCEK_VARYANTLAR, ids=[g[0] for g in GERCEK_VARYANTLAR])
def test_r1_gercek_geometri_etiket_varyanti_satirlar_butun(ad: str, etiketler: list[Kutu], satirlar: list[list[Kutu]]) -> None:
    """Etiketle: her çizilen satırın kelimeleri TEK blokta, hiçbir blok iki satırdan kelime içermez;
    girdi sırası (ters, karışık) sonucu değiştirmez. Etiketsiz pozitif kontrol: aynı."""
    bl = _bloklar(etiketler, satirlar)
    cikti = satirlari_birlestir(bl)
    ok, d = satir_butunlugu(cikti, satirlar)
    assert ok, f"{ad}: satır -> bloklar {d}; parça {[len(c.line_boxes) or 1 for c in cikti]}"
    for c in cikti:  # satır içi x sıralı
        xs = [r.x for r in c.line_boxes]
        assert xs == sorted(xs)
    assert satirlari_birlestir(list(reversed(bl))) == cikti
    rnd = random.Random(7)
    for _ in range(5):
        p = bl[:]
        rnd.shuffle(p)
        assert satirlari_birlestir(p) == cikti
    siz = satirlari_birlestir(_bloklar(etiketler, satirlar, etiketli=False))
    assert satir_butunlugu(siz, satirlar)[0]
    assert len(siz) == len(satirlar)


def test_r1_3satir_etiket_satir0a_yapisik_6_5_5() -> None:
    """3 satırlık etiket: etiket satır 0'a yapışır, [6,5,5]. (Tur 1 kodu aynı geometride [11,5]:
    satır 0 ve 1 x sırasında iç içe — r2-11 ayna kanıtı.)"""
    _, et, sat = GERCEK_VARYANTLAR[2]
    cikti = satirlari_birlestir(_bloklar(et, sat))
    assert [len(c.line_boxes) for c in cikti] == [6, 5, 5]


def test_r1_1p2_orta_etiket_tek_basina_5_1_5() -> None:
    """1.2× etiket iki satırın ORTASINDA: hiçbir satırla `>= 0.5*min(h)` örtüşmez -> kendi bloğu."""
    _, et, sat = GERCEK_VARYANTLAR[5]
    cikti = satirlari_birlestir(_bloklar(et, sat))
    assert [len(c.line_boxes) or 1 for c in cikti] == [5, 1, 5]
    assert cikti[1].bbox == Rect(*et[0])


# ---------------------------------------------------------------------------
# R2 — sentetik tarama: etiket h × dy × pitch × konum × titreşim (A2-1 "E fixture'ı mı kapattı?")
# ---------------------------------------------------------------------------
def _sahne(rnd: random.Random, h: int, pitch: int, etiket_h: int, etiket_dy: int, konum: str,
           n_satir: int = 2, n_kelime: int = 4, titresim: int = 3) -> tuple[list[Kutu], list[list[Kutu]]]:
    """n_satir satır × n_kelime kelime (w 50-120, boşluk 8-14 px, y titreşimi ±titresim, h ±2);
    etiket: konum sol/sağ/orta, üst = satır 0 üstü + etiket_dy."""
    satirlar: list[list[Kutu]] = []
    x0 = 200 if konum == "sol" else 20
    en_sag = 0
    for i in range(n_satir):
        x = x0
        satir: list[Kutu] = []
        for _ in range(n_kelime):
            w = rnd.randint(50, 120)
            hh = h + rnd.randint(-2, 2)
            y = i * pitch + rnd.randint(-titresim, titresim)
            satir.append((x, y, w, hh))
            x += w + rnd.randint(8, 14)
        en_sag = max(en_sag, x)
        satirlar.append(satir)
    if konum == "sol":
        ex = 20
    elif konum == "sag":
        ex = en_sag + 20
    else:  # orta: satırların ortasındaki bir boşluğa etiket; kelimeleri sağa kaydır
        ex = 20
        kaydir = 20 + 120 + 24
        satirlar = [[(kx + kaydir if j >= n_kelime // 2 else kx, ky, kw, kh) for j, (kx, ky, kw, kh) in enumerate(s)] for s in satirlar]
        ilk_sag = max(s[n_kelime // 2 - 1][0] + s[n_kelime // 2 - 1][2] for s in satirlar)
        ex = ilk_sag + 24
    etiket: Kutu = (ex, etiket_dy, 120, etiket_h)
    return [etiket], satirlar


@pytest.mark.parametrize("konum", ["sol", "sag", "orta"])
def test_r2_sentetik_tarama_etiket_koprusu_satirlar_butun(konum: str) -> None:
    """Etiket h ∈ {1.2,1.4,…,3.0}×h; dy: etiket üstü satır 0 üstünden −0.5h … +0.5h; pitch ∈
    {1.05,1.1,1.2,1.3,1.5}×h; titreşim ±3; 2 ve 3 satır. Değişmez: satır bütünlüğü (kelimeler),
    'orta' konumda satır başına ≤ 2 blok (K7 boşluk kuralı beklenen) ve bloklar ayrık.
    Sayaç: en az bir konfigürasyonda etiket satır 0'a yapışır (pozitif: köprü geometrisi gerçekten
    kuruluyor) ve en az birinde etiket satır 1'e de sarkar."""
    rnd = random.Random(20240911)
    h = 34
    kopru_kurulan = 0
    toplam = 0
    for oran in (1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.5, 3.0):
        for p_oran in (1.05, 1.1, 1.2, 1.3, 1.5):
            pitch = int(round(p_oran * h))
            for dy in range(-h // 2, h // 2 + 1, 4):
                for n_satir in (2, 3):
                    etiket_h = int(round(oran * h))
                    et, sat = _sahne(rnd, h, pitch, etiket_h, dy, konum, n_satir=n_satir)
                    bl = _bloklar(et, sat)
                    cikti = satirlari_birlestir(bl)
                    d = satir_dagilimi(cikti, sat)
                    toplam += 1
                    izin = 2 if konum == "orta" else 1
                    assert all(len(s) <= izin for s in d), (konum, oran, p_oran, dy, n_satir, d)
                    assert all(a.isdisjoint(b) for a, b in itertools.combinations(d, 2)), (konum, oran, p_oran, dy, n_satir, d)
                    e = Rect(*et[0])
                    s1 = Rect(*sat[1][0])
                    if e.y <= min(k[1] for k in sat[0]) and min(e.bottom, s1.bottom) - max(e.y, s1.y) >= 0.5 * min(e.h, s1.h):
                        kopru_kurulan += 1
    assert toplam == 8 * 5 * 9 * 2
    assert kopru_kurulan >= 100, kopru_kurulan  # köprü sınıfı taramada bol (sol: 142/720 ölçüldü)


# ---------------------------------------------------------------------------
# R3 — "en kısa referans" sınırı (A2-2)
# ---------------------------------------------------------------------------
def _sarkan_sahne(h_kisa: int, sarkma: int, aralik: int, h: int = 30) -> tuple[list[list[Kutu]], Kutu]:
    """Satır 0: w1 w2 (0..h); kısa kutu p: alt kenarı satır 0'ın altından `sarkma` px aşağıda;
    satır 1: n1 n2, üstü satır 0'ın altından `aralik` px aşağıda (aralik <= 0: satırlar iç içe)."""
    p: Kutu = (110, h + sarkma - h_kisa, 8, h_kisa)
    s0: list[Kutu] = [(0, 0, 50, h), (55, 0, 50, h)]
    s1: list[Kutu] = [(0, h + aralik, 50, h), (55, h + aralik, 50, h)]
    return [s0, s1], p


def test_r3_sarkan_kisa_kutu_butunluk_bozulmasi_yalniz_satirlar_ic_iceyken() -> None:
    """Türetim: p [t0,t1] satır 0'a katılmak için a1 - t0 >= 0.5*h_p, satır 1'in p ile örtüşmesi
    için t1 - b0 >= 0.5*h_p; toplam: h_p - g >= h_p  =>  g <= 0. Yani sarkan kısa kutu iki satırı
    ANCAK satır kutuları fiziksel olarak iç içeyse (aralık <= 0) aynı satıra toplayabilir; görünür
    belirti parçalanma (x sırası satırları karıştırır, gruplar bölünür) ya da çapraz birleşme.
    Tarama h_p ∈ [4,24], sarkma ∈ [0,20], aralık ∈ [-6, 8] (1386 sahne): satır bütünlüğü
    bozuldu ⇒ aralık <= 0 (pozitif kontrol: aralık < 0'da bozulma VAR). Gerçek OCR'da aralık
    >= 2 px (pitch 1.05×h, r2-10 [B]) -> sınıf gerçek düzende kapalı."""
    bozulan_araliklar: set[int] = set()
    sahne_sayisi = 0
    for h_p in range(4, 25, 2):
        for sarkma in range(0, 21, 2):
            for aralik in range(-6, 9):
                sat, p = _sarkan_sahne(h_p, sarkma, aralik)
                bl = _bloklar([], sat) + [B(*p, "p")]
                cikti = satirlari_birlestir(bl)
                ok, d = satir_butunlugu(cikti, sat)
                sahne_sayisi += 1
                if not ok:
                    bozulan_araliklar.add(aralik)
                    assert aralik <= 0, (h_p, sarkma, aralik, d, metinler(cikti))
    assert sahne_sayisi == 11 * 11 * 15
    assert bozulan_araliklar and max(bozulan_araliklar) <= 0
    assert min(bozulan_araliklar) < 0  # pozitif kontrol: sınıf ateşliyor


def test_r3_sarkan_kisa_kutu_ayrilma_penceresi_tur2_vs_tur1_belgeli() -> None:
    """Gerçek OCR (r2-10 [B1], token h=17): sarkma 8 px'te tur 2 token'ı AYRI blok bırakır
    (referans en kısa kelime: örtüşme 7 < 8.5), tur 1 satıra yapıştırırdı (ilk kelime: 9 >= 8.5).
    Cümle bütün kalır; ürün etkisi: küçük ek token ayrı çevrilir. Sentetik karşılığı:
    satır 0 kelimeleri h 35/30 (ilk uzun, en kısa 2 px yukarıda biter), token h=17 sarkma 8."""
    s0 = [B(0, 0, 50, 35, "w1"), B(55, 2, 50, 30, "w2")]  # w2: 2..32, w1: 0..35 -> en kısa w2
    token = B(110, 35 + 8 - 17, 19, 17, "x2")  # 26..43: w1 ile 9 (>= 8.5), w2 ile 6 (< 8.5)
    s1 = [B(0, 37, 50, 35, "n1"), B(55, 37, 50, 35, "n2")]  # aralık 2
    cikti = satirlari_birlestir(s0 + [token] + s1)
    assert metinler(cikti) == ["w1 w2", "x2", "n1 n2"]  # tur 2: token ayrı (tur 1: "w1 w2 x2")
    token4 = B(110, 35 + 4 - 17, 19, 17, "x2")  # sarkma 4: w2 ile 10 >= 8.5 -> yapışır
    assert metinler(satirlari_birlestir(s0 + [token4] + s1)) == ["w1 w2 x2", "n1 n2"]


def test_r3_ust_konumlu_minik_kutu_yanlis_bolunme_sentetik_pozitif_kontrol() -> None:
    """Yanlış BÖLÜNME sınıfı (tur 2'ye özgü, sentetik): minik kutu t (h=8) satıra katılıp
    referans olur; ondan SONRA işlenen (y'si büyük) aynı-satır kelimesi b, t ile
    `>= 0.5*8 = 4` örtüşmezse yeni satır açar -> satır ikiye bölünür. a(0,0,50,34)
    t(55,2,10,8) b(70,7,50,34): t 2..10, b 7..41 -> örtüşme 3 < 4 -> ["a t", "b"].
    Gerekli titreşim: b.y - t.y > 0.5*h_t. Gerçek OCR (r2-12 [D]): minik kutular kelime
    üstünden 1-9 px AŞAĞIDA, h >= 13 -> hep kelimelerden SONRA işleniyor; bölünme için
    >= 12 px titreşim gerekir (gözlenen <= 5). `[ÖLÇÜLMÜYOR]` gerçek OCR'da erişilemedi."""
    a, t, b = B(0, 0, 50, 34, "a"), B(55, 2, 10, 8, "t"), B(70, 7, 50, 34, "b")
    assert metinler(satirlari_birlestir([a, t, b])) == ["a t", "b"]
    # pozitif kontrol: b 2 px yukarı (5..39): örtüşme 5 >= 4 -> tek satır, tek blok
    b2 = B(70, 5, 50, 34, "b")
    assert metinler(satirlari_birlestir([a, t, b2])) == ["a t b"]
    # t kelimelerden SONRA işlenirse (y >= 7) bölünme yok: gerçek OCR düzeni
    t2 = B(55, 8, 10, 8, "t")
    assert metinler(satirlari_birlestir([a, t2, b])) == ["a t b"]


@pytest.mark.parametrize("h_t, gerekli_titresim", [(6, 3), (8, 4), (12, 6), (16, 8)])
def test_r3_yanlis_bolunme_esigi_titresim_yarim_h_minik(h_t: int, gerekli_titresim: int) -> None:
    """Sınır formülü: bölünme <=> (b.y - t.y) > 0.5*h_t (t satırın üstünde, b sonra işleniyor).
    Yatay boşluklar 3 px (K2 `0.75*min(h)` eşiği h_t=6'da 4.5 px: boşluk kuralı karışmasın)."""
    a = B(0, 0, 50, 34, "a")
    t = B(53, 0, 10, h_t, "t")
    for tit in range(0, 12):
        b = B(66, tit, 50, 34, "b")
        cikti = metinler(satirlari_birlestir([a, t, b]))
        beklenen = ["a t", "b"] if tit > gerekli_titresim else ["a t b"]
        assert cikti == beklenen, (h_t, tit, cikti)


# ---------------------------------------------------------------------------
# R4 — T2-2 aynı-x çifti; K6 daraltılmış cümle (A2-3)
# ---------------------------------------------------------------------------
def test_r4_t2_2_ayni_x_farkli_y_6_permutasyon_ayni() -> None:
    p, q, r = B(0, 0, 50, 20, "p"), B(0, 10, 50, 20, "q"), B(55, 10, 50, 20, "r")
    for perm in itertools.permutations([p, q, r]):
        assert metinler(satirlari_birlestir(list(perm))) == ["p", "q r"], [b.text for b in perm]


def test_r4_t2_2_ayni_x_uc_kutu_ve_sag_komsu_y_sirasi() -> None:
    """Aynı x'te üç kutu (y 0/8/16, h 20) + sağda r(55,16): satır içi `(x,y,idx)` -> açık grup
    her zaman y'si en büyük olan (16); r ona katılır. 24 permütasyon aynı."""
    a, b, c, r = B(0, 0, 50, 20, "a"), B(0, 8, 50, 20, "b"), B(0, 16, 50, 20, "c"), B(55, 16, 50, 20, "r")
    for perm in itertools.permutations([a, b, c, r]):
        assert metinler(satirlari_birlestir(list(perm))) == ["a", "b", "c r"], [x.text for x in perm]


def test_r4_k6_daraltilmis_cumle_fuzz_yukseklikler_degisken() -> None:
    """K6 (T2-3): 'iki ÇIKTI bloğunun (y,x)'i eşit olmadıkça her permütasyon aynı liste'.
    6000 rastgele girdi (2-8 kutu; h 4-60 -- uzun/kısa karışık, T2-1 referans mantığını
    zorlar; (y,x) girdide bağsız): permütasyon çıktıyı değiştiriyorsa çıktı anahtarında
    (y,x) bağı VARDIR ve bloklar kümesi aynıdır (yalnız sıra). Pozitif kontrol: en az bir
    bağ örneği çıkar."""
    rnd = random.Random(2)
    farkli = 0
    for _ in range(6000):
        n = rnd.randint(2, 8)
        seen: set[tuple[int, int]] = set()
        bl: list[TextBlock] = []
        for i in range(n):
            while True:
                x, y = rnd.randint(0, 80), rnd.randint(0, 40)
                if (y, x) not in seen:
                    seen.add((y, x))
                    break
            bl.append(B(x, y, rnd.randint(5, 40), rnd.randint(4, 60), f"t{i}"))
        ref = satirlari_birlestir(bl)
        ref_k = [(o.text, o.bbox) for o in ref]
        for _ in range(4):
            p = bl[:]
            rnd.shuffle(p)
            got = satirlari_birlestir(p)
            got_k = [(o.text, o.bbox) for o in got]
            if got_k != ref_k:
                farkli += 1
                anahtarlar = [(o.bbox.y, o.bbox.x) for o in ref]
                assert len(anahtarlar) != len(set(anahtarlar)), ("permütasyon farkı, çıktı bağı olmadan", bl)
                assert sorted(ref_k) == sorted(got_k), ("küme farklı", bl)
                break
    assert farkli >= 1


def test_r4_satir_referansi_en_kisa_girdi_sirasindan_bagimsiz_uzun_kisa_bagli() -> None:
    """Aynı (y,x)'te uzun (h=60) ve kısa (h=20) kutu + alt satır c(60,30): hangi sırada
    gelirse gelsin referans kısa olur, c satıra girmez; çıktı sırası bağla (girdi) belirlenir."""
    kisa, uzun, c = B(0, 0, 50, 20, "k"), B(0, 0, 50, 60, "u"), B(60, 30, 50, 20, "c")
    assert metinler(satirlari_birlestir([kisa, uzun, c])) == ["k", "u", "c"]
    assert metinler(satirlari_birlestir([uzun, kisa, c])) == ["u", "k", "c"]
    # referans "ilk girdi" olsaydı [uzun, kisa, c] -> c satıra girer, x sırasında k-u-c: u(0..60) ile c
    # (30..50) grup-ilk örtüşmesi 20 >= 10 ve u.right=50 -> c.x=60 boşluk 10 <= 15 -> "u c" olurdu.


# ---------------------------------------------------------------------------
# R5 — belge sınırları (ret dışı; docstring kesinliği)
# ---------------------------------------------------------------------------
def test_r5_ayni_x_y_farkli_w_cift_tespit_bolumleme_girdi_sirasina_bagli_SINIR() -> None:
    """Docstring K6: 'bağ yalnız çıktı SIRASINI etkiler, satır üyeliğini DEĞİL'. Aynı (x,y)'de
    iki kutu (çift tespit) FARKLI genişlikte: p(0,0,50,20) P(0,0,80,20) r(55,0,50,20) —
    satır içi `(x,y,idx)` bağı idx ile çözülür; hangisi açık grup olursa r ONA katılır:
    [p,P,r] -> ['p', 'P r'] · [P,p,r] -> ['P', 'p r']. Satır üyeliği aynı, ama GRUP
    bölümlemesi (blok kümesi) girdi sırasına bağlı — cümle 'sıra' demekle dar. Ürün: çift
    tespit gerçek tespitçide yok (A6 tur 1: iç içe/çakışan çift yok); belge kesinliği."""
    p, P, r = B(0, 0, 50, 20, "p"), B(0, 0, 80, 20, "P"), B(55, 0, 50, 20, "r")
    bir = metinler(satirlari_birlestir([p, P, r]))
    iki = metinler(satirlari_birlestir([P, p, r]))
    assert bir == ["p", "P r"]
    assert iki == ["P", "p r"]
    assert sorted(bir) != sorted(iki)  # küme de farklı (yalnız sıra değil)


def test_r5_minik_kutu_min_h_bosluk_esigi_satiri_parcalar_K2_sinifi_tur1_ile_ayni() -> None:
    """r2-12 [D] gerçek geometri (tm_f30): minik ™ kutuları (h 13/14) satırdadır ama K2 boşluk
    eşiği `0.75*min(h)` ≈ 10 px, kelime boşluğu 11-12 px -> satır 5 bloğa parçalanır. Bu K2'nin
    `min(h)` kuralı (paket), T2-1 değil; tur 1 kodu aynı çıktıyı verir (r2-11/r2-12). Belge."""
    geo = [(61, 64, 60, 35), (166, 66, 91, 32), (270, 66, 87, 31), (406, 67, 115, 30), (538, 67, 115, 30),
           (368, 69, 23, 14), (132, 70, 22, 13)]
    cikti = satirlari_birlestir([B(*g, f"g{i}") for i, g in enumerate(geo)])
    assert len(cikti) == 5
    # aynı satır (tek "satır"a girdi): hepsinin y'si 64..70, hiçbiri başka satırla karışmadı
    assert all(64 <= c.bbox.y <= 70 for c in cikti)
