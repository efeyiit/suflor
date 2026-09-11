"""T-008 -- `satirlari_birlestir` birim testleri (sentetik `TextBlock`, OCR YOK).

Her test adi paketteki degismez numarasini tasir (`test_kN_*`). Girdiler
sentetik `TextBlock`'lardir; `rapidocr`/`onnxruntime` HIC import edilmez
(sefin `conftest.py` bariyeri zaten keser). Gercek OCR yalniz
`.agents/tasks/T-008/real_check.py` ile (ayri surec) olculur.

Metin icerikleri sentetiktir (`k0`, `a`, ...); gercek OCR metni burada yok.
"""
from __future__ import annotations

import ast
import itertools
import json
import math
import random
import statistics
import time
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path

import pytest

from src.contracts.models import Rect, TextBlock
from src.ocr import satir_birlestirici as modul
from src.ocr.satir_birlestirici import (
    DIKEY_ORTUSME_ESIGI,
    YATAY_BOSLUK_ESIGI,
    satirlari_birlestir,
)

KAYNAK_DOSYA = Path(modul.__file__)


# ---------------------------------------------------------------------------
# yardimcilar
# ---------------------------------------------------------------------------
def _blok(
    x: int,
    y: int,
    w: int,
    h: int,
    text: str = "a",
    conf: float = 1.0,
    mon: int = 0,
    dpi: float = 1.0,
    lb: tuple[Rect, ...] = (),
) -> TextBlock:
    return TextBlock(
        text=text,
        bbox=Rect(x=x, y=y, w=w, h=h, monitor_index=mon, dpi_scale=dpi),
        confidence=conf,
        line_boxes=lb,
    )


def _xler(b: TextBlock) -> list[int]:
    return [r.x for r in b.line_boxes]


# Gercek KR fixture'inin GEOMETRISI (dlg_KR.png, gercek OCR, sef/KRT olctu;
# metin yok -- yalniz kutular). 17 kutu, 4 satir: [2,5,5,5]. Satir 3'te y
# 212/209/209/208/210 -- `(y,x)` sirasi x sirasi DEGIL (paket K2 lafzinin
# dustugu nokta; bkz. modul docstring'i "## K2 -- ITIRAZ").
KR_GEOMETRI: tuple[tuple[int, int, int, int], ...] = (
    (78, 97, 52, 29),
    (141, 99, 101, 26),
    (79, 154, 67, 40),
    (158, 156, 102, 37),
    (274, 157, 98, 35),
    (390, 158, 130, 33),
    (538, 158, 137, 33),
    (82, 212, 131, 34),
    (225, 209, 72, 40),
    (305, 209, 69, 39),
    (386, 208, 70, 41),
    (467, 210, 141, 37),
    (78, 264, 71, 37),
    (155, 262, 71, 41),
    (240, 263, 67, 39),
    (322, 265, 127, 36),
    (469, 265, 140, 35),
)


def _kr_bloklari() -> list[TextBlock]:
    return [_blok(x, y, w, h, text=f"k{i}") for i, (x, y, w, h) in enumerate(KR_GEOMETRI)]


def _satir3() -> list[TextBlock]:
    """KR satir 3 (indeks 7..11): y titresimli bes kelime kutusu."""
    return [_blok(x, y, w, h, text=f"s{i}") for i, (x, y, w, h) in enumerate(KR_GEOMETRI[7:12])]


# ---------------------------------------------------------------------------
# K1 -- saf, deterministik, butce
# ---------------------------------------------------------------------------
def test_k1_sabitler_paketteki_degerlerde() -> None:
    assert DIKEY_ORTUSME_ESIGI == 0.5
    assert YATAY_BOSLUK_ESIGI == 0.75
    assert modul.__all__ == ("satirlari_birlestir", "DIKEY_ORTUSME_ESIGI", "YATAY_BOSLUK_ESIGI")


def test_k1_girdi_listesi_ve_bloklar_degismez() -> None:
    girdi = _kr_bloklari()
    kopya = list(girdi)
    satirlari_birlestir(girdi)
    assert girdi == kopya
    assert all(a is b for a, b in zip(girdi, kopya))


def test_k1_ayni_girdi_ayni_cikti() -> None:
    girdi = tuple(_kr_bloklari())
    assert satirlari_birlestir(girdi) == satirlari_birlestir(girdi)


def test_k1_girdi_demet_de_olabilir() -> None:
    demet: tuple[TextBlock, ...] = (_blok(0, 0, 50, 20), _blok(55, 0, 50, 20))
    assert len(satirlari_birlestir(demet)) == 1


def test_k1_saflik_ast_yasak_cagri_modul_ve_mutable_yok() -> None:
    agac = ast.parse(KAYNAK_DOSYA.read_text(encoding="utf-8"))
    cagrilar = {
        n.func.id for n in ast.walk(agac) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
    }
    assert not cagrilar & {"open", "print", "input", "exec", "eval"}
    moduller: set[str] = set()
    for n in ast.walk(agac):
        if isinstance(n, ast.Import):
            moduller |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            moduller.add(n.module.split(".")[0])
    assert not moduller & {"random", "time", "os", "sys", "io", "pathlib", "logging", "subprocess"}
    # modul duzeyi mutable yok (list/dict/set literal ya da yapici)
    for dugum in agac.body:
        hedefler: list[ast.expr] = []
        deger: ast.expr | None = None
        if isinstance(dugum, ast.Assign):
            hedefler, deger = dugum.targets, dugum.value
        elif isinstance(dugum, ast.AnnAssign):
            hedefler, deger = [dugum.target], dugum.value
        if deger is None:
            continue
        assert not isinstance(deger, (ast.List, ast.Dict, ast.Set, ast.ListComp, ast.DictComp, ast.SetComp)), (
            ast.dump(dugum)
        )
        if isinstance(deger, ast.Call) and isinstance(deger.func, ast.Name):
            assert deger.func.id not in {"list", "dict", "set"}, ast.dump(dugum)
    # __all__ demet
    (all_dugumu,) = [
        d for d in agac.body if isinstance(d, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__all__" for t in d.targets)
    ]
    assert isinstance(all_dugumu.value, ast.Tuple)


def test_k1_1000_blok_50_ms_altinda() -> None:
    rnd = random.Random(7)
    cok = [
        _blok(rnd.randrange(0, 2000), rnd.randrange(0, 1400) // 40 * 40, 60, 36, text=f"w{i}")
        for i in range(1000)
    ]
    satirlari_birlestir(cok)  # isinma
    sureler: list[float] = []
    for _ in range(5):
        t0 = time.perf_counter()
        satirlari_birlestir(cok)
        sureler.append((time.perf_counter() - t0) * 1000)
    assert statistics.median(sureler) < 50


# ---------------------------------------------------------------------------
# K2 -- ayni satir + komsuluk geometriyle
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("ortusme_orani", "beklenen"),
    [(0.49, 2), (0.50, 1), (0.51, 1)],
    ids=["0.49-ayri", "0.50-sinirda-birlesir", "0.51-birlesir"],
)
def test_k2_dikey_ortusme_esigi_sinirda(ortusme_orani: float, beklenen: int) -> None:
    h = 100
    kaydirma = h - int(round(ortusme_orani * h))  # ortusme = h - kaydirma
    a = _blok(0, 0, 50, h, text="a")
    b = _blok(55, kaydirma, 50, h, text="b")
    assert len(satirlari_birlestir([a, b])) == beklenen


@pytest.mark.parametrize(
    ("bosluk_orani", "beklenen"),
    [(0.74, 1), (0.75, 1), (0.76, 2)],
    ids=["0.74-birlesir", "0.75-sinirda-birlesir", "0.76-ayri"],
)
def test_k2_yatay_bosluk_esigi_sinirda(bosluk_orani: float, beklenen: int) -> None:
    h = 100
    bosluk = int(round(bosluk_orani * h))
    a = _blok(0, 0, 50, h, text="a")
    b = _blok(50 + bosluk, 0, 50, h, text="b")
    assert len(satirlari_birlestir([a, b])) == beklenen


def test_k2_esik_min_h_ile_kucuk_kutu_belirler() -> None:
    """`min(h)`: kisa kutu (h=20) esigi belirler -- 0.75*20 = 15; bosluk 16 ayirir."""
    a = _blok(0, 0, 100, 40, text="a")
    b = _blok(116, 10, 15, 20, text="b")
    assert len(satirlari_birlestir([a, b])) == 2
    b2 = _blok(115, 10, 15, 20, text="b")
    assert len(satirlari_birlestir([a, b2])) == 1


def test_k2_esik_orijinal_yukseklikle_birlesik_degil_y2() -> None:
    """KRT Y2 fixture'i: A(0,0,100,40) + b(105,10,15,20) + C(150,0,100,40).

    b-C boslugu 30 > 0.75*min(20,40)=15 -> AYRI. Birlesik yukseklikle (Ab h=40)
    esik 30 olur ve C birlesirdi -- mutant bu testte duser.
    """
    a = _blok(0, 0, 100, 40, text="A")
    b = _blok(105, 10, 15, 20, text="b")
    c = _blok(150, 0, 100, 40, text="C")
    cikti = satirlari_birlestir([a, b, c])
    assert [x.text for x in cikti] == ["A b", "C"]


def test_k2_cakisan_kutu_komsudur() -> None:
    a = _blok(0, 0, 50, 20, text="a")
    b = _blok(45, 0, 50, 20, text="b")  # bosluk -5
    assert [x.text for x in satirlari_birlestir([a, b])] == ["a b"]


def test_k2_farkli_monitor_index_birlesmez() -> None:
    a = _blok(0, 0, 50, 20, mon=0, text="a")
    b = _blok(55, 0, 50, 20, mon=1, text="b")
    assert len(satirlari_birlestir([a, b])) == 2
    assert len(satirlari_birlestir([_blok(0, 0, 50, 20, mon=1), _blok(55, 0, 50, 20, mon=1)])) == 1


def test_k2_farkli_dpi_scale_birlesmez() -> None:
    """KARAR (paket sessiz): normalizer K10 `_union_rect` farkli `dpi_scale`'i
    `ValueError` ile reddeder; burada da birlesmez -- sessiz kopyalama yok."""
    a = _blok(0, 0, 50, 20, dpi=1.0, text="a")
    b = _blok(55, 0, 50, 20, dpi=1.5, text="b")
    assert len(satirlari_birlestir([a, b])) == 2


@pytest.mark.parametrize(
    ("w", "h"),
    [(0, 20), (50, 0), (-5, 20), (50, -5), (0, 0)],
    ids=["w0", "h0", "w-neg", "h-neg", "w0h0"],
)
def test_k2_yozlasmis_kutu_hicbir_seyle_birlesmez_ve_aynen_gecer(w: int, h: int) -> None:
    a = _blok(0, 0, 50, 20, text="a")
    z = _blok(52, 0, w, h, text="z")
    b = _blok(54, 0, 50, 20, text="b")
    cikti = satirlari_birlestir([a, z, b])
    assert any(c is z for c in cikti)
    # yozlasmis kutu araya girse de A ve B'nin komsulugunu BOZMAZ (bosluk 4 <= 15)
    assert sorted(c.text for c in cikti) == ["a b", "z"]
    # pozitif kontrol: ayni yerde SAGLAM bir kutu olsaydi ucu birlesirdi
    s = _blok(52, 0, 1, 20, text="s")
    assert [c.text for c in satirlari_birlestir([a, s, b])] == ["a s b"]


def test_k2_zincir_gecisli_tek_blok() -> None:
    """A-B komsu, B-C komsu, A-C degil -> grup son bloga gore ilerler -> TEK blok."""
    a = _blok(0, 0, 50, 20, text="a")
    b = _blok(60, 0, 50, 20, text="b")
    c = _blok(120, 0, 50, 20, text="c")
    cikti = satirlari_birlestir([a, b, c])
    assert len(cikti) == 1
    assert cikti[0].text == "a b c"
    assert _xler(cikti[0]) == [0, 60, 120]


def test_k2_x_ilerlemeyen_kutu_yeni_grup_acar() -> None:
    """Ayni x'te ikinci kutu (cift tespit) `x ilerliyor` kosulunu SAGLAMAZ."""
    a = _blok(0, 0, 50, 20, text="a")
    a2 = _blok(0, 0, 50, 20, text="a2")
    cikti = satirlari_birlestir([a, a2])
    assert len(cikti) == 2
    assert [c.text for c in cikti] == ["a", "a2"]


def test_k2_ic_ice_kutu_x_ilerliyorsa_birlesir_belgeli() -> None:
    """S6 geri cekildi: ic ice kutu (x ilerliyor, bosluk negatif) BIRLESIR --
    metin cogalir. Bilinen sinir, testte SABITLENDI."""
    dis = _blok(0, 0, 100, 20, text="ab")
    ic = _blok(10, 2, 30, 16, text="a")
    cikti = satirlari_birlestir([dis, ic])
    assert [c.text for c in cikti] == ["ab a"]


def test_k2_iki_satir_x_geri_sarar_ayri_bloklar() -> None:
    s1 = [_blok(0, 0, 50, 20, text="a"), _blok(55, 0, 50, 20, text="b")]
    s2 = [_blok(0, 30, 50, 20, text="c"), _blok(55, 30, 50, 20, text="d")]
    cikti = satirlari_birlestir(s1 + s2)
    assert [c.text for c in cikti] == ["a b", "c d"]


def test_k2_y_titresimli_satir_x_sirasinda_birlesir_itiraz() -> None:
    """ITIRAZ olcusu: KR satir 3 geometrisi (y 212/209/209/208/210).

    Paketin K2 lafzi -- `(y,x,idx)` sirala + tek gecis + son bloga gore x
    ilerleme -- burada 5 kutuyu 4 gruba boler (x sirasi 386,225,305,467,82).
    Gercek satir tek bloktur; `line_boxes` x sirasinda.
    """
    for girdi in (_satir3(), list(reversed(_satir3()))):
        cikti = satirlari_birlestir(girdi)
        assert len(cikti) == 1, [c.text for c in cikti]
        assert _xler(cikti[0]) == [82, 225, 305, 386, 467]
        assert cikti[0].text == "s0 s1 s2 s3 s4"


def test_k2_kr_geometrisi_17_kutu_4_satir_2_5_5_5() -> None:
    cikti = satirlari_birlestir(_kr_bloklari())
    assert [len(c.line_boxes) for c in cikti] == [2, 5, 5, 5]
    assert all(" " in c.text for c in cikti)
    for c in cikti:
        assert _xler(c) == sorted(_xler(c))


def test_k2_satir_bolumleme_satirin_ilk_bloguna_gore() -> None:
    """Satir uyeligi `(y,x,idx)` sirasindaki ILK blokla olculur, bir
    oncekiyle DEGIL. Merdiven: a(0,0) b(100,10) c(50,20), h=20 -- b a ile
    ortusur (10), c b ile ortusur (10) ama a ile ORTUSMEZ (0) -> c ayri
    satir. "Bir oncekiyle" uyelik c'yi satira alir, x sirasinda c(50) b(100)
    onune gecer ve c-b birlesirdi ("c b") -- mutant M17 burada duser."""
    a = _blok(0, 0, 50, 20, text="a")
    b = _blok(100, 10, 50, 20, text="b")
    c = _blok(50, 20, 50, 20, text="c")
    cikti = satirlari_birlestir([a, b, c])
    assert [x.text for x in cikti] == ["a", "b", "c"]
    # pozitif kontrol: c'yi 10 px yukari al -> a ile ortusme 10 >= 10 -> ayni satir;
    # x sirasinda a(0) c(50) b(100): a-c bitisik (bosluk 0), c-b bitisik -> ucu birlesir
    c2 = _blok(50, 10, 50, 20, text="c")
    assert [x.text for x in satirlari_birlestir([a, b, c2])] == ["a c b"]


def test_k2_grup_icinde_dikey_ortusme_grubun_ilk_bloguyla() -> None:
    """Uzun kutu koprusu (KRT O2): T(60,0,40,60) satirin ilk blogu (en kucuk y);
    a(0,5,50,20) ve c(110,40,50,20) T ile ortusur -> ucu AYNI SATIRDA. x
    sirasinda a-T birlesir (ortusme 20, bosluk 10); c grubun ILK blogu a ile
    ortusmez (-15) -> ayri. Referans SON blok (T) olsaydi c de birlesirdi
    ("a T c", iki satir tek metin) -- mutant M18 burada duser."""
    a = _blok(0, 5, 50, 20, text="a")
    t = _blok(60, 0, 40, 60, text="T")
    c = _blok(110, 40, 50, 20, text="c")
    cikti = satirlari_birlestir([a, t, c])
    assert [x.text for x in cikti] == ["a T", "c"]
    # pozitif kontrol: c'yi a ile ortusecek kadar yukari al -> ucu birlesir
    c2 = _blok(110, 10, 50, 20, text="c")
    assert [x.text for x in satirlari_birlestir([a, t, c2])] == ["a T c"]


# ---------------------------------------------------------------------------
# K3 -- birlestirme karakteri betikle
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("sol", "sag", "beklenen"),
    [
        ("村の", "長老", "村の長老"),
        ("장로", "마르쿠스", "장로 마르쿠스"),
        ("elder", "is", "elder is"),
        ("HP", "が", "HP が"),
        ("42", "点", "42 点"),
        ("「マルクス」", "と", "「マルクス」と"),  # ilk HARF katakana (tirnak degil)
        ("ｶﾀｶﾅ", "が", "ｶﾀｶﾅが"),  # yarim genislik katakana da CJK
        ("ー", "ん", "ーん"),  # uzatma isareti (Lm) CJK
        ("待って", "。", "待って 。"),  # harfsiz parca LATIN sayilir -> bosluk (belgeli sinir)
        ("ＨＰ", "が", "ＨＰ が"),  # tam genislik Latin LATIN
        ("  elder ", " is  ", "elder is"),  # bastaki/sondaki bosluk korunmaz
        ("村の ", " 長老", "村の長老"),
        ("a\nb", "c", "a\nb c"),  # ic bosluk/yeni satir aynen
    ],
)
def test_k3_betik_tablosu(sol: str, sag: str, beklenen: str) -> None:
    a = _blok(0, 0, 50, 20, text=sol)
    b = _blok(55, 0, 50, 20, text=sag)
    (c,) = satirlari_birlestir([a, b])
    assert c.text == beklenen


def test_k3_uc_parca_karisik_betik() -> None:
    p = [_blok(0, 0, 50, 20, text="村の"), _blok(55, 0, 50, 20, text="長老"), _blok(110, 0, 50, 20, text="HP")]
    (c,) = satirlari_birlestir(p)
    assert c.text == "村の長老 HP"


def test_k3_bos_parca_metne_katilmaz_kutusu_katilir() -> None:
    """KARAR (paket sessiz): strip sonrasi bos parca `text`e ne kendini ne
    ayirici ekler; `bbox`/`line_boxes`/`confidence` hesabina yine girer."""
    p = [_blok(0, 0, 50, 20, text="a", conf=0.9), _blok(55, 0, 50, 20, text="   ", conf=0.3), _blok(110, 0, 50, 20, text="b")]
    (c,) = satirlari_birlestir(p)
    assert c.text == "a b"
    assert len(c.line_boxes) == 3
    assert c.confidence == 0.3
    assert c.bbox == Rect(0, 0, 160, 20)


def test_k3_hepsi_bos_metin_bos() -> None:
    (c,) = satirlari_birlestir([_blok(0, 0, 50, 20, text=""), _blok(55, 0, 50, 20, text=" ")])
    assert c.text == ""


# ---------------------------------------------------------------------------
# K4 -- tek uygulama; sabit nokta DEGIL (belge)
# ---------------------------------------------------------------------------
def test_k4_docstring_yasak_sozcuk_yok_ve_bir_kez_uyarisi_var() -> None:
    doc = ast.get_docstring(ast.parse(KAYNAK_DOSYA.read_text(encoding="utf-8"))) or ""
    assert "idempoten" not in doc.lower()
    assert "bir kez" in doc.lower()  # pozitif kontrol: uyari gercekten var
    assert "[ÖLÇÜLMÜYOR]" in doc


def test_k4_ikinci_uygulama_sabit_nokta_degil_pozitif_kontrol() -> None:
    """Belge olcusu (degismez DEGIL): Y2 fixture'inda f(f(x)) != f(x)."""
    a = _blok(0, 0, 100, 40, text="A")
    b = _blok(105, 10, 15, 20, text="b")
    c = _blok(150, 0, 100, 40, text="C")
    bir = satirlari_birlestir([a, b, c])
    iki = satirlari_birlestir(bir)
    assert len(bir) == 2 and len(iki) == 1


# ---------------------------------------------------------------------------
# K5 -- birlesik blogun alanlari
# ---------------------------------------------------------------------------
def test_k5_uc_parcali_bbox_birlesim_confidence_min_line_boxes_x_sirali() -> None:
    p1 = _blok(10, 5, 40, 20, text="a", conf=0.9, mon=2, dpi=1.25)
    p2 = _blok(55, 3, 30, 24, text="b", conf=0.5, mon=2, dpi=1.25)
    p3 = _blok(90, 6, 50, 18, text="c", conf=0.7, mon=2, dpi=1.25)
    (c,) = satirlari_birlestir([p3, p1, p2])  # karisik girdi
    assert c.bbox == Rect(x=10, y=3, w=130, h=24, monitor_index=2, dpi_scale=1.25)
    assert all(type(v) is int for v in (c.bbox.x, c.bbox.y, c.bbox.w, c.bbox.h))
    assert c.confidence == 0.5
    assert c.line_boxes == (p1.bbox, p2.bbox, p3.bbox)
    assert c.text == "a b c"
    json.dumps(asdict(c.bbox))


def test_k5_line_boxes_parcalarin_bbox_i_kendi_line_boxes_i_degil() -> None:
    ic = (Rect(0, 0, 1, 1), Rect(2, 2, 1, 1))
    a = _blok(0, 0, 50, 20, text="a", lb=ic)
    b = _blok(55, 0, 50, 20, text="b", lb=ic)
    (c,) = satirlari_birlestir([a, b])
    assert c.line_boxes == (a.bbox, b.bbox)


def test_k5_tek_parca_ayni_nesne_line_boxes_dokunulmaz() -> None:
    lb = (Rect(1, 1, 1, 1),)
    a = _blok(0, 0, 50, 20, text="a", lb=lb)
    (c,) = satirlari_birlestir([a])
    assert c is a
    assert c.line_boxes is lb
    # birlesmeyen komsu da ayni nesne
    b = _blok(500, 0, 50, 20, text="b", lb=lb)
    c1, c2 = satirlari_birlestir([a, b])
    assert c1 is a and c2 is b


def test_k5_negatif_koordinat_normal() -> None:
    a = _blok(-100, -50, 40, 20, text="a")
    b = _blok(-55, -50, 40, 20, text="b")
    (c,) = satirlari_birlestir([a, b])
    assert c.bbox == Rect(-100, -50, 85, 20)
    assert c.text == "a b"


# ---------------------------------------------------------------------------
# K6 -- okuma sirasi
# ---------------------------------------------------------------------------
def test_k6_uc_satir_uc_kutu_karisik() -> None:
    bloklar: list[TextBlock] = []
    for s in range(3):
        for k in range(3):
            bloklar.append(_blok(k * 60, s * 40, 50, 20, text=f"s{s}k{k}"))
    rnd = random.Random(3)
    rnd.shuffle(bloklar)
    cikti = satirlari_birlestir(bloklar)
    assert [c.text for c in cikti] == ["s0k0 s0k1 s0k2", "s1k0 s1k1 s1k2", "s2k0 s2k1 s2k2"]
    assert [c.bbox.y for c in cikti] == [0, 40, 80]


def test_k6_kr_geometrisi_permutasyonlarda_ayni_cikti() -> None:
    temel = satirlari_birlestir(_kr_bloklari())
    rnd = random.Random(11)
    for _ in range(5):
        g = _kr_bloklari()
        rnd.shuffle(g)
        assert satirlari_birlestir(g) == temel


def test_k6_bagsiz_kucuk_girdi_tum_permutasyonlar_ayni() -> None:
    temel_g = [_blok(0, 0, 50, 20, text="a"), _blok(55, 2, 50, 20, text="b"), _blok(0, 40, 50, 20, text="c"), _blok(300, 41, 50, 20, text="d")]
    temel = satirlari_birlestir(temel_g)
    for perm in itertools.permutations(temel_g):
        assert satirlari_birlestir(list(perm)) == temel


def test_k6_bagli_durum_girdi_sirasi_korunur_sinir() -> None:
    """Iki kutu ayni `(y,x)`: bag girdi indeksiyle cozulur -> girdi sirasi (K6'nin siniri)."""
    a = _blok(0, 0, 50, 20, text="a")
    b = _blok(0, 0, 50, 20, text="b")
    assert [c.text for c in satirlari_birlestir([a, b])] == ["a", "b"]
    assert [c.text for c in satirlari_birlestir([b, a])] == ["b", "a"]


def test_k6_bagli_durumda_satir_referansi_ilk_girdi_blogu() -> None:
    """Ayni `(y,x)`'te iki kutu (a h=20, b h=60): satirin referansi girdide
    ONCE gelen olur. [a,b,c]: referans a, c(60,30) a ile ortusmez -> uc ayri.
    Bag TERS cozulseydi referans b olur, c satira girer ve b-c birlesirdi
    ("a", "b c") -- mutant M04 burada duser. [b,a,c] girdisi K6 sinirinin
    kaydi: referans b, c satira girer ama x sirasinda a'nin grubu araya
    girdigi icin yine ayri kalir; cikti sirasi girdi sirasini izler."""
    a = _blok(0, 0, 50, 20, text="a")
    b = _blok(0, 0, 50, 60, text="b")
    c = _blok(60, 30, 50, 20, text="c")
    assert [x.text for x in satirlari_birlestir([a, b, c])] == ["a", "b", "c"]
    assert [x.text for x in satirlari_birlestir([b, a, c])] == ["b", "a", "c"]


def test_k6_bagli_durum_farkli_monitorlerde_de_girdi_indeksi() -> None:
    """Bag cozumu monitor bolumlemesinin isleme sirasina DEGIL girdi indeksine bagli."""
    b0 = _blok(0, 0, 50, 20, mon=1, text="m1")
    b1 = _blok(0, -5, 50, 20, mon=0, text="m0-ust")
    b2 = _blok(0, 0, 50, 20, mon=0, text="m0")
    assert [c.text for c in satirlari_birlestir([b0, b1, b2])] == ["m0-ust", "m1", "m0"]


def test_k6_cikti_y_x_sirasinda_satir_icinde_de() -> None:
    """Ayni satirda iki grup: sagdaki grubun min y daha kucukse (y,x) sirasinda ONCE gelir."""
    g1 = [_blok(0, 5, 50, 20, text="a"), _blok(55, 5, 50, 20, text="b")]
    g2 = [_blok(300, 3, 50, 20, text="c"), _blok(355, 5, 50, 20, text="d")]
    cikti = satirlari_birlestir(g1 + g2)
    assert [c.text for c in cikti] == ["c d", "a b"]
    assert [(c.bbox.y, c.bbox.x) for c in cikti] == sorted((c.bbox.y, c.bbox.x) for c in cikti)


# ---------------------------------------------------------------------------
# K7 -- iki sutun
# ---------------------------------------------------------------------------
def test_k7_uc_h_bosluk_ayri_blok() -> None:
    h = 30
    a = _blok(0, 0, 100, h, text="etiket")
    b = _blok(100 + 3 * h, 0, 60, h, text="deger")
    assert len(satirlari_birlestir([a, b])) == 2


def test_k7_iki_sutun_uc_satir_alti_blok() -> None:
    bloklar = [_blok(0, s * 40, 80, 30, text=f"e{s}") for s in range(3)] + [
        _blok(400, s * 40, 60, 30, text=f"d{s}") for s in range(3)
    ]
    cikti = satirlari_birlestir(bloklar)
    assert [c.text for c in cikti] == ["e0", "d0", "e1", "d1", "e2", "d2"]


# ---------------------------------------------------------------------------
# K8 -- yozlasmis girdi
# ---------------------------------------------------------------------------
def test_k8_bos_girdi_bos_liste() -> None:
    assert satirlari_birlestir([]) == []
    assert satirlari_birlestir(()) == []


def test_k8_tek_blok_ayni_nesne() -> None:
    a = _blok(0, 0, 50, 20)
    (c,) = satirlari_birlestir([a])
    assert c is a
    z = _blok(0, 0, 0, 0)
    (cz,) = satirlari_birlestir([z])
    assert cz is z


def test_k8_confidence_nan_nan_olmayanlarin_min_i_sira_bagimsiz() -> None:
    nan = _blok(0, 0, 50, 20, text="n", conf=math.nan)
    a = _blok(55, 0, 50, 20, text="a", conf=0.8)
    b = _blok(110, 0, 50, 20, text="b", conf=0.6)
    (c1,) = satirlari_birlestir([nan, a, b])  # NaN x sirasinda ILK
    assert c1.confidence == 0.6
    nan2 = _blok(165, 0, 50, 20, text="n", conf=math.nan)
    (c2,) = satirlari_birlestir([a, b, nan2])  # NaN SON
    assert c2.confidence == 0.6
    (c3,) = satirlari_birlestir([a, nan2, b][::-1])
    assert c3.confidence == 0.6


def test_k8_confidence_hepsi_nan_nan() -> None:
    p = [_blok(0, 0, 50, 20, conf=math.nan), _blok(55, 0, 50, 20, conf=math.nan)]
    (c,) = satirlari_birlestir(p)
    assert math.isnan(c.confidence)


def test_k8_yozlasmis_kutular_okuma_sirasinda_yerinde() -> None:
    z = _blok(60, 0, 0, 20, text="z")
    a = _blok(0, 0, 50, 20, text="a")
    b = _blok(0, 40, 50, 20, text="b")
    assert [c.text for c in satirlari_birlestir([b, z, a])] == ["a", "z", "b"]


def test_k8_yozlasmis_iki_kutu_birbiriyle_de_birlesmez() -> None:
    z1 = _blok(0, 0, 0, 20, text="z1")
    z2 = _blok(0, 0, 0, 20, text="z2")
    assert len(satirlari_birlestir([z1, z2])) == 2


# ---------------------------------------------------------------------------
# Kontrol: paket K2 lafzi bu geometride 17 -> 9 verir (itirazin birim izi)
# ---------------------------------------------------------------------------
def _paket_lafzi(blocks: Sequence[TextBlock]) -> list[list[TextBlock]]:
    """Paket v2 K2'nin LAFZI: `(y,x,idx)` sirala, tek gecis, grubun ilk
    bloguyla dikey ortusme, son bloguna gore x ilerleme + bosluk. Yalniz
    itiraz olcusu icin -- uygulama DEGIL."""
    sirali = sorted(enumerate(blocks), key=lambda c: (c[1].bbox.y, c[1].bbox.x, c[0]))
    gruplar: list[list[TextBlock]] = []
    for _, b in sirali:
        r = b.bbox
        if gruplar:
            ilk = gruplar[-1][0].bbox
            son = gruplar[-1][-1].bbox
            ort = min(ilk.bottom, r.bottom) - max(ilk.y, r.y)
            if (
                ort >= DIKEY_ORTUSME_ESIGI * min(ilk.h, r.h)
                and r.x > son.x
                and (r.x - son.right) <= YATAY_BOSLUK_ESIGI * min(son.h, r.h)
            ):
                gruplar[-1].append(b)
                continue
        gruplar.append([b])
    return gruplar


def test_itiraz_paket_lafzi_kr_geometrisinde_dokuz_grup_verir() -> None:
    lafzi = _paket_lafzi(_kr_bloklari())
    assert len(lafzi) == 9
    assert [len(g) for g in lafzi] == [2, 5, 1, 2, 1, 1, 2, 1, 2]
    assert len(satirlari_birlestir(_kr_bloklari())) == 4
