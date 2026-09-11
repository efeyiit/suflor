"""TESTER-B (T-008, mercek B: test kalitesi / saflik / kapsam durustlugu / bariyer).

B2 Totoloji     -- 68 testte assert'siz, sabit ya da yalniz kendi ciktisina bagli test var mi;
                   esik fixture'lari SINIRDA mi; ikinci parametre noktasi (h=20, h=33) var mi.
B3 Saflik       -- AST (bagimsiz uygulama), girdi degismezligi (`id` + `==`), determinizm
                   (100 rastgele x 2; iki ayri surec farkli PYTHONHASHSEED), 1000 blok < 50 ms,
                   1k -> 10k -> 100k olcekleme (n log n mi, n^2 mi), dusmanca yerlesimler.
B4 Kapsam       -- pragma yok, .coveragerc yok, her test ciktiya bakan bir assert tasiyor.
B5 Bariyer      -- kendi bariyerim atesliyor (`match="K1 bariyeri"`); sefin bariyeri teslim
                   dosyasi kosarken 68/68 setup'ta aktif (ayri surec, gozlem eklentisi);
                   modul yasak kok import etmiyor.

Sentetik `TextBlock`; OCR yok; metin basilmaz. `tests/`, `src/`, `real_check.py` yazilmaz.
"""
from __future__ import annotations

import ast
import copy
import importlib
import itertools
import json
import os
import random
import statistics
import subprocess
import sys
import time
from pathlib import Path

import pytest

import tb_bariyer
from src.contracts.models import Rect, TextBlock
from src.ocr import satir_birlestirici as modul
from src.ocr.satir_birlestirici import DIKEY_ORTUSME_ESIGI, YATAY_BOSLUK_ESIGI, satirlari_birlestir

DEPO = tb_bariyer._KOK
KAYNAK = DEPO / "src" / "ocr" / "satir_birlestirici.py"
TESLIM_TEST = DEPO / "tests" / "unit" / "ocr" / "test_satir_birlestirici.py"
REAL_CHECK = DEPO / ".agents" / "tasks" / "T-008" / "real_check.py"
BU_DIZIN = Path(__file__).resolve().parent


def _b(x: int, y: int, w: int, h: int, text: str = "a", conf: float = 0.9, mon: int = 0, dpi: float = 1.0) -> TextBlock:
    return TextBlock(text=text, bbox=Rect(x, y, w, h, monitor_index=mon, dpi_scale=dpi), confidence=conf)


def _test_fonksiyonlari(agac: ast.Module) -> list[ast.FunctionDef]:
    return [n for n in agac.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]


def _teslim_agaci() -> ast.Module:
    return ast.parse(TESLIM_TEST.read_text(encoding="utf-8"))


# =============================================================================
# B2 -- totoloji
# =============================================================================
def test_b2_teslim_68_test_topluyor() -> None:
    r = subprocess.run([sys.executable, "-m", "pytest", str(TESLIM_TEST), "-q", "-p", "no:cacheprovider", "--collect-only"],
                       cwd=str(DEPO), capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert r.returncode == 0, r.stdout[-800:]
    assert "68 tests collected" in r.stdout, r.stdout[-300:]


def test_b2_her_test_fonksiyonunda_assert_ya_da_raises_var() -> None:
    eksik: list[str] = []
    for f in _test_fonksiyonlari(_teslim_agaci()):
        assertler = [n for n in ast.walk(f) if isinstance(n, ast.Assert)]
        raises = [n for n in ast.walk(f) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "raises"]
        if not assertler and not raises:
            eksik.append(f.name)
    assert eksik == [], eksik


def test_b2_sabit_ya_da_kendine_esit_assert_yok() -> None:
    """`assert True`, `assert 1 == 1`, `assert X == X` (iki taraf ayni AST) yok."""
    kotu: list[str] = []
    for f in _test_fonksiyonlari(_teslim_agaci()):
        for n in ast.walk(f):
            if not isinstance(n, ast.Assert):
                continue
            t = n.test
            if isinstance(t, ast.Constant):
                kotu.append(f"{f.name}: sabit assert")
            elif isinstance(t, ast.Compare) and len(t.comparators) == 1:
                if ast.dump(t.left) == ast.dump(t.comparators[0]) and not any(
                    isinstance(m, ast.Call) for m in ast.walk(t.left)
                ):
                    # iki AYRI cagri (`f(x) == f(x)`) determinizm olcusudur, totoloji degil
                    kotu.append(f"{f.name}: X == X")
                elif isinstance(t.left, ast.Constant) and isinstance(t.comparators[0], ast.Constant):
                    kotu.append(f"{f.name}: sabit == sabit")
    assert kotu == [], kotu


def _yalniz_kendine_bagli(f: ast.FunctionDef) -> bool:
    """Testin TUM assert'leri `satirlari_birlestir` ciktisini yine `satirlari_birlestir`
    ciktisiyla karsilastiriyor mu (bagimsiz cipa yok)?"""
    cikti_adlari: set[str] = set()
    for n in ast.walk(f):
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Name) and n.value.func.id == "satirlari_birlestir":
            for t in n.targets:
                if isinstance(t, ast.Name):
                    cikti_adlari.add(t.id)
    assertler = [n for n in ast.walk(f) if isinstance(n, ast.Assert)]
    if not assertler:
        return False

    def _cikti_mi(e: ast.expr) -> bool:
        if isinstance(e, ast.Name) and e.id in cikti_adlari:
            return True
        return isinstance(e, ast.Call) and isinstance(e.func, ast.Name) and e.func.id == "satirlari_birlestir"

    for a in assertler:
        t = a.test
        if isinstance(t, ast.Compare) and len(t.comparators) == 1 and _cikti_mi(t.left) and _cikti_mi(t.comparators[0]):
            continue
        return False
    return True


def test_b2_yalniz_kendine_bagli_testler_listesi_ve_cipalari() -> None:
    """Determinizm/permutasyon testleri dogal olarak kendine baglidir (f(x) == f(perm x)).
    Tek basina totolojidirler (`return []` gecer). Kabul edilebilirlik: ayni fixture'i
    BAGIMSIZ bir referansla olcen baska test var mi? KR_GEOMETRI -> `test_k2_kr_geometrisi_17_kutu_4_satir_2_5_5_5`
    ([2,5,5,5]). Dort kutuluk `temel_g` fixture'i icin bagimsiz cipa YOK (bulgu, bloke etmez):
    bu test o listeyi SABITLER -- yeni bir kendine-bagli test eklenirse burada gorunur."""
    adlar = sorted(f.name for f in _test_fonksiyonlari(_teslim_agaci()) if _yalniz_kendine_bagli(f))
    assert adlar == [
        "test_k1_ayni_girdi_ayni_cikti",
        "test_k6_bagsiz_kucuk_girdi_tum_permutasyonlar_ayni",
        "test_k6_kr_geometrisi_permutasyonlarda_ayni_cikti",
    ], adlar
    # `temel_g` fixture'inin bagimsiz cipasi (teslimde yok; burada olculur): "a b", "c", "d"
    temel_g = [_b(0, 0, 50, 20, "a"), _b(55, 2, 50, 20, "b"), _b(0, 40, 50, 20, "c"), _b(300, 41, 50, 20, "d")]
    assert [c.text for c in satirlari_birlestir(temel_g)] == ["a b", "c", "d"]


def test_b2_esik_sinir_noktalari_teslimde_var() -> None:
    """0.49/0.50/0.51 ve 0.74/0.75/0.76 sabitleri test dosyasinda gecer (sinirda, uzakta degil)."""
    sabitler = {n.value for n in ast.walk(_teslim_agaci()) if isinstance(n, ast.Constant) and isinstance(n.value, float)}
    assert {0.49, 0.50, 0.51, 0.74, 0.75, 0.76} <= sabitler, sorted(sabitler)


@pytest.mark.parametrize("h", [20, 33, 100], ids=["h20", "h33-tek", "h100"])
def test_b2_yatay_esik_ikinci_parametre_noktasi(h: int) -> None:
    """Teslim yalniz h=100 ile olcuyor; h=20 ve TEK sayi h=33'te (0.75*33 = 24.75) sinir:
    bosluk floor(0.75h) birlesir, floor(0.75h)+1 ayrilir (carpma, bolme yok)."""
    esik = int(YATAY_BOSLUK_ESIGI * h)
    a = _b(0, 0, 50, h, "a")
    assert len(satirlari_birlestir([a, _b(50 + esik, 0, 50, h, "b")])) == 1
    assert len(satirlari_birlestir([a, _b(50 + esik + 1, 0, 50, h, "b")])) == 2


@pytest.mark.parametrize("h", [20, 33, 100], ids=["h20", "h33-tek", "h100"])
def test_b2_dikey_esik_ikinci_parametre_noktasi(h: int) -> None:
    """ortusme >= 0.5*h: h=33 -> 16.5: ortusme 17 birlesir, 16 ayrilir."""
    gerek = DIKEY_ORTUSME_ESIGI * h
    yeter = int(gerek) if gerek == int(gerek) else int(gerek) + 1
    a = _b(0, 0, 50, h, "a")
    assert len(satirlari_birlestir([a, _b(55, h - yeter, 50, h, "b")])) == 1
    assert len(satirlari_birlestir([a, _b(55, h - yeter + 1, 50, h, "b")])) == 2


def test_b2_real_check_model_pinli_sabitler_belgelendi() -> None:
    """real_check gercek OCR sayilarina PINLI: `== 17`, `[2, 5, 5, 5]`, `== 4`. OCR modeli degisirse
    kapi dogru uygulamada da duser (kirilganlik). Birim testler ise KR_GEOMETRI ile model-bagimsiz.
    Bu test kirilganligi SABITLER: pin kaldirilirsa/degisirse burada gorunur."""
    kaynak = REAL_CHECK.read_text(encoding="utf-8")
    assert "len(kr) == 17" in kaynak
    assert "[2, 5, 5, 5]" in kaynak
    assert "len(mb) == 4 and len(mc) == 4" in kaynak
    # birim test dosyasi OCR'a bagimli DEGIL
    teslim = TESLIM_TEST.read_text(encoding="utf-8")
    assert "KR_GEOMETRI" in teslim
    assert "rapidocr" not in teslim.replace("`rapidocr`/`onnxruntime` HIC import edilmez", "")
    assert "import rapidocr" not in teslim and "import onnxruntime" not in teslim


# =============================================================================
# B3 -- saflik
# =============================================================================
def test_b3_ast_saflik_bagimsiz_denetim() -> None:
    agac = ast.parse(KAYNAK.read_text(encoding="utf-8"))
    yasak_ad = {"open", "print", "input", "exec", "eval", "compile", "__import__", "globals", "setattr", "delattr", "vars"}
    cagri = {n.func.id for n in ast.walk(agac) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    assert not (cagri & yasak_ad), cagri & yasak_ad
    moduller: set[str] = set()
    for n in ast.walk(agac):
        if isinstance(n, ast.Import):
            moduller |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            moduller.add(n.module.split(".")[0])
    assert moduller == {"__future__", "math", "unicodedata", "collections", "typing", "src"}, moduller
    assert not [n for n in ast.walk(agac) if isinstance(n, (ast.Global, ast.Nonlocal))]
    # mutable varsayilan arguman yok
    for f in ast.walk(agac):
        if isinstance(f, ast.FunctionDef):
            for d in f.args.defaults + f.args.kw_defaults:
                assert not isinstance(d, (ast.List, ast.Dict, ast.Set, ast.Call)), (f.name, ast.dump(d))
    # modul duzeyi: yalniz sabit (Final) demet/str/float atamalari; list/dict/set yok; nitelik yazimi yok
    for d in agac.body:
        if isinstance(d, (ast.Assign, ast.AnnAssign)) and d.value is not None:
            for n in ast.walk(d.value):
                assert not isinstance(n, (ast.List, ast.Dict, ast.Set, ast.ListComp, ast.DictComp, ast.SetComp)), ast.dump(d)
            hedefler = d.targets if isinstance(d, ast.Assign) else [d.target]
            for t in hedefler:
                assert isinstance(t, ast.Name), ast.dump(t)
    # `sys.`/`os.` nitelik erisimi yok
    for n in ast.walk(agac):
        if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name):
            assert n.value.id not in {"sys", "os", "io", "builtins"}, ast.dump(n)


def test_b3_girdi_listesi_ve_bloklar_degismez_id_ve_esitlik() -> None:
    rnd = random.Random(21)
    girdi = [_b(rnd.randrange(0, 600), rnd.randrange(0, 200) // 30 * 30 + rnd.randrange(0, 4), 50, 20 + rnd.randrange(0, 5), f"t{i}",
                conf=rnd.random(), mon=rnd.randrange(0, 2), dpi=rnd.choice([1.0, 1.25]))
             for i in range(60)]
    girdi.append(_b(0, 0, 0, 20, "z"))  # yozlasmis
    kimlikler = [id(b) for b in girdi]
    derin = copy.deepcopy(girdi)
    lb_kimlik = [id(b.line_boxes) for b in girdi]
    cikti = satirlari_birlestir(girdi)
    assert [id(b) for b in girdi] == kimlikler
    assert girdi == derin
    assert [id(b.line_boxes) for b in girdi] == lb_kimlik
    assert len(girdi) == 61
    # cikti girdiyi paylasmiyor: birlesik bloklar YENI nesne, tek parcalilar AYNI nesne
    girdi_kume = {id(b) for b in girdi}
    for c in cikti:
        if len(c.line_boxes) >= 2 and c.line_boxes[0] in {b.bbox for b in girdi}:
            assert id(c) not in girdi_kume
    # ikinci cagri da girdiyi bozmuyor ve esit
    assert satirlari_birlestir(girdi) == cikti
    assert girdi == derin


def _rastgele_girdi(rnd: random.Random, n: int, bagsiz: bool) -> list[TextBlock]:
    bloklar: list[TextBlock] = []
    gorulen: set[tuple[int, int]] = set()
    while len(bloklar) < n:
        x, y = rnd.randrange(0, 900), rnd.randrange(0, 300) // 35 * 35 + rnd.randrange(0, 5)
        if bagsiz and (y, x) in gorulen:
            continue
        gorulen.add((y, x))
        bloklar.append(_b(x, y, rnd.randrange(20, 120), rnd.randrange(18, 42), f"t{len(bloklar)}",
                          conf=rnd.choice([rnd.random(), float("nan")]), mon=rnd.randrange(0, 2)))
    return bloklar


def test_b3_deterministik_100_rastgele_girdi_x2_ve_permutasyon() -> None:
    rnd = random.Random(5)
    for _ in range(100):
        g = _rastgele_girdi(rnd, rnd.randrange(0, 40), bagsiz=True)
        a = satirlari_birlestir(g)
        b = satirlari_birlestir(list(g))
        assert [(c.text, c.bbox, len(c.line_boxes), c.confidence != c.confidence) for c in a] == \
               [(c.text, c.bbox, len(c.line_boxes), c.confidence != c.confidence) for c in b]
        k = list(g)
        rnd.shuffle(k)
        c2 = satirlari_birlestir(k)
        assert [(c.text, c.bbox, c.line_boxes) for c in c2] == [(c.text, c.bbox, c.line_boxes) for c in a]


def test_b3_ayri_surec_farkli_hash_tohumu_ayni_cikti() -> None:
    """dict/set sirasina gizli bagimlilik: iki surec, PYTHONHASHSEED 1 ve 2, 50 rastgele girdi."""
    betik = (
        "import json, random, sys\n"
        f"sys.path.insert(0, {str(DEPO)!r})\n"
        "from src.contracts.models import Rect, TextBlock\n"
        "from src.ocr.satir_birlestirici import satirlari_birlestir\n"
        "rnd = random.Random(77)\n"
        "out = []\n"
        "for _ in range(50):\n"
        "    g = [TextBlock(text=f't{i}', bbox=Rect(rnd.randrange(0, 900), rnd.randrange(0, 300)//35*35 + rnd.randrange(0,5), rnd.randrange(20,120), rnd.randrange(18,42), monitor_index=rnd.randrange(0,2)), confidence=rnd.random()) for i in range(rnd.randrange(0, 40))]\n"
        "    out.append([(c.text, c.bbox.x, c.bbox.y, c.bbox.w, c.bbox.h, c.bbox.monitor_index, c.confidence, len(c.line_boxes)) for c in satirlari_birlestir(g)])\n"
        "print(json.dumps(out))\n"
    )
    sonuclar = []
    for tohum in ("1", "2"):
        env = dict(os.environ, PYTHONHASHSEED=tohum)
        r = subprocess.run([sys.executable, "-c", betik], capture_output=True, text=True, encoding="utf-8", env=env, cwd=str(DEPO))
        assert r.returncode == 0, r.stderr[-500:]
        sonuclar.append(json.loads(r.stdout))
    assert sonuclar[0] == sonuclar[1]
    assert sum(len(x) for x in sonuclar[0]) > 0


def _yerlesim(ad: str, n: int, rnd: random.Random) -> list[TextBlock]:
    if ad == "rastgele":  # teslimin/real_check'in yerlesimi
        return [_b(rnd.randrange(0, 2000), rnd.randrange(0, 1400) // 40 * 40, 60, 36, f"w{i}") for i in range(n)]
    if ad == "tek-satir-zincir":  # hepsi ayni satirda, bitisik -> tek grup, uzun zincir
        return [_b(i * 70, 0, 60, 36, f"w{i}") for i in range(n)]
    if ad == "hepsi-bagli":  # hepsi ayni (y,x): siralama baglari, cift tespit
        return [_b(0, 0, 60, 36, f"w{i}") for i in range(n)]
    if ad == "sutun":  # her blok ayri satir (x geri sarmaz), satir sayisi n
        return [_b(0, i * 40, 60, 36, f"w{i}") for i in range(n)]
    raise ValueError(ad)


def _sure_ms(g: list[TextBlock], tekrar: int = 5) -> float:
    satirlari_birlestir(g)
    s = []
    for _ in range(tekrar):
        t0 = time.perf_counter()
        satirlari_birlestir(g)
        s.append((time.perf_counter() - t0) * 1000)
    return statistics.median(s)


@pytest.mark.parametrize("ad", ["rastgele", "tek-satir-zincir", "hepsi-bagli", "sutun"])
def test_b3_1000_blok_50_ms_altinda_dort_yerlesim(ad: str) -> None:
    g = _yerlesim(ad, 1000, random.Random(7))
    assert _sure_ms(g) < 50, ad


@pytest.mark.parametrize("ad", ["rastgele", "tek-satir-zincir", "hepsi-bagli", "sutun"])
def test_b3_olcekleme_n_log_n_1k_10k(ad: str) -> None:
    """10x girdi -> sure orani: n log n icin ~13, n^2 icin ~100. Sinir 40 (gurultu payi)."""
    rnd = random.Random(7)
    t1 = _sure_ms(_yerlesim(ad, 1000, rnd), tekrar=7)
    t10 = _sure_ms(_yerlesim(ad, 10000, rnd), tekrar=3)
    oran = t10 / max(t1, 0.05)
    assert oran < 40, f"{ad}: 1k {t1:.2f} ms, 10k {t10:.2f} ms, oran {oran:.1f}"


def test_b3_100k_blok_saniye_altinda() -> None:
    g = _yerlesim("rastgele", 100_000, random.Random(7))
    assert _sure_ms(g, tekrar=1) < 1000


# =============================================================================
# B4 -- kapsam durustlugu
# =============================================================================
def test_b4_pragma_ve_kapsam_yapilandirmasi_yok() -> None:
    for p in (KAYNAK, TESLIM_TEST):
        metin = p.read_text(encoding="utf-8")
        assert "pragma" not in metin and "no cover" not in metin, p.name
    for ad in (".coveragerc", "pyproject.toml", "setup.cfg", "tox.ini", "pytest.ini"):
        assert not (DEPO / ad).exists(), ad


def test_b4_her_test_ciktiya_ya_da_kaynaga_bakan_assert_tasiyor() -> None:
    """Kapsam icin yazilmis 'davranissiz' test yok: her test ya `satirlari_birlestir`/`_paket_lafzi`
    cagiriyor ya da kaynak dosyayi (AST) okuyor ve assert ediyor."""
    davranissiz: list[str] = []
    for f in _test_fonksiyonlari(_teslim_agaci()):
        cagrilar = {n.func.id for n in ast.walk(f) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        nitelikler = {n.attr for n in ast.walk(f) if isinstance(n, ast.Attribute)}
        adlar = {n.id for n in ast.walk(f) if isinstance(n, ast.Name)}
        davranis = bool(cagrilar & {"satirlari_birlestir", "_paket_lafzi"}) or "read_text" in nitelikler or "KAYNAK_DOSYA" in adlar
        sabit_kontrol = {"DIKEY_ORTUSME_ESIGI", "YATAY_BOSLUK_ESIGI"} & adlar and "modul" in adlar
        if not davranis and not sabit_kontrol:
            davranissiz.append(f.name)
    assert davranissiz == [], davranissiz


def test_b4_sabit_degerleri_testi_tek_basina_esik_mutantini_tutmuyor_belge() -> None:
    """`test_k1_sabitler_paketteki_degerlerde` sabiti pinler (davranisi degil). Mutant kiti:
    esik mutantlari (M01-M06) o test DISINDA da en az 2 davranis testiyle yakalaniyor
    (B1 tablosu). Burada yalniz sabitlerin paketle ayni oldugu tekrar olculur."""
    assert (DIKEY_ORTUSME_ESIGI, YATAY_BOSLUK_ESIGI) == (0.5, 0.75)
    assert modul.__all__ == ("satirlari_birlestir", "DIKEY_ORTUSME_ESIGI", "YATAY_BOSLUK_ESIGI")


# =============================================================================
# B5 -- bariyer
# =============================================================================
@pytest.mark.parametrize("ad", ["rapidocr", "rapidocr.main", "onnxruntime"])
def test_b5_kendi_bariyerim_atesliyor(ad: str) -> None:
    sys.modules.pop(ad, None)
    with pytest.raises(RuntimeError, match="K1 bariyeri"):
        importlib.import_module(ad)


def test_b5_modul_yasak_kok_import_etmiyor() -> None:
    assert tb_bariyer.ONCEDEN_YUKLU == ()
    assert not any(k.split(".", 1)[0] in tb_bariyer.YASAK_KOKLER for k in sys.modules)
    importlib.reload(modul)
    assert not any(k.split(".", 1)[0] in tb_bariyer.YASAK_KOKLER for k in sys.modules)


def test_b5_sefin_bariyeri_teslim_dosyasi_kosarken_68_68_aktif(tmp_path: Path) -> None:
    """Ayri surec: `pytest tests/unit/ocr/test_satir_birlestirici.py -p tb_gozlem_plugin`.
    Her setup'ta meta_path[0] `_T006Bariyer` ve `import rapidocr` -> RuntimeError('T-006 K1 bariyeri')."""
    hedef = tmp_path / "gozlem.json"
    env = dict(os.environ, TB_GOZLEM=str(hedef), PYTHONPATH=str(BU_DIZIN) + os.pathsep + os.environ.get("PYTHONPATH", ""))
    r = subprocess.run([sys.executable, "-m", "pytest", str(TESLIM_TEST), "-q", "-p", "no:cacheprovider", "-p", "tb_gozlem_plugin"],
                       cwd=str(DEPO), capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    assert r.returncode == 0, r.stdout[-800:]
    g = json.loads(hedef.read_text(encoding="utf-8"))
    assert g["setup"] == 68, g
    assert g["basta_bariyer"] == 68, g
    assert g["rapidocr_kesildi"] == 68 and g["onnxruntime_kesildi"] == 68, g
    assert g["yasak_kok_sys_modules"] == 0 and g["yasak_kok_sonda"] == [], g
    assert g["ilk_hata"] == "", g


def test_b5_bariyer_bu_dizin_sefin_diziniyle_birlikte_kosunca_da_tutar() -> None:
    """`match="K1 bariyeri"` iki bariyerin ortak alt dizesi (sef: 'T-006 K1 bariyeri', ben:
    'tester-B T-008 K1 bariyeri'): hangisi once ateslerse ateslesin tutar."""
    assert "K1 bariyeri" in tb_bariyer.BARIYER_MESAJI
    sef = (DEPO / "tests" / "unit" / "ocr" / "conftest.py").read_text(encoding="utf-8")
    assert "K1 bariyeri" in sef


# =============================================================================
# B1 ek -- kacan mutant siniflari icin HAZIR olculer (teslimde yok; sef isterse tasir)
# =============================================================================
def test_b1_ek_k6_ayni_x_farkli_y_permutasyon_bagimsiz() -> None:
    """M41 sinifi: ayni satirda ayni x, farkli y iki kutu + sag komsu -> her permutasyonda ayni cikti
    (bagsiz girdi: (y,x) ciftleri farkli). Teslimin permutasyon fixture'larinda ayni-x cifti yok."""
    a = _b(0, 0, 50, 20, "a")
    b = _b(0, 8, 50, 20, "b")
    c = _b(55, 4, 50, 20, "c")
    temel = [(x.text, x.bbox) for x in satirlari_birlestir([a, b, c])]
    assert [t for t, _ in temel] == ["a", "b c"]
    for perm in itertools.permutations([a, b, c]):
        assert [(x.text, x.bbox) for x in satirlari_birlestir(list(perm))] == temel


def test_b1_ek_k6_birlesik_grup_ile_tekil_blok_bagi_en_kucuk_indeks() -> None:
    """M40 sinifi: ayni (y,x)'te birlesik grup [p, q] ve tekil s (baska monitor). Bag, grubun EN KUCUK
    girdi indeksiyle cozulur (docstring): p idx0 < s idx1 -> once 'p q'."""
    p = _b(0, 0, 50, 20, "p", mon=0)
    s = _b(0, 0, 50, 20, "s", mon=1)
    q = _b(55, 0, 50, 20, "q", mon=0)
    assert [x.text for x in satirlari_birlestir([p, s, q])] == ["p q", "s"]
    assert [x.text for x in satirlari_birlestir([s, p, q])] == ["s", "p q"]


def test_b1_ek_k3_uyumluluk_ideografi_cjk() -> None:
    """M23 sinifi: docstring 'uyumluluk ideograflari da CJK'dir' der, tabloda ornek yok.
    KR v4 tanima sozlugunde 76 uyumluluk ideografi var (B1b-M23-erisilebilirlik kaniti)."""
    uyum, cjk = chr(0xF902), chr(0x8C48)
    (c,) = satirlari_birlestir([_b(0, 0, 50, 20, uyum + uyum), _b(55, 0, 50, 20, cjk + cjk)])
    assert " " not in c.text
    (d,) = satirlari_birlestir([_b(0, 0, 50, 20, cjk), _b(55, 0, 50, 20, uyum)])
    assert " " not in d.text
