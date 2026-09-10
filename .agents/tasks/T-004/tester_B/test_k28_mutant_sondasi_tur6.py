"""TESTER-B (KARAR UYUMU) -- T-004 TUR 6 -- K28 MUTANT SONDASI (M3-M15).

`test_k23_mutant_sondasi_tur5.py` K23/K24 denetimlerinin disli oldugunu
gosteriyordu. Bu dosya TUR 6'nin asil yukumlulugunu tasir: sefin
`sef_karari-tur6.md` (surum 8) "kitin bilinen sinirlari" tablosunda
ACIKCA "kit bunu OLCMUYOR" dedigi mutant siniflarini KENDI sondamla
yakalamak -- ve sefin her iddiasini (hem "kit gormez" hem "su kadar
ayrisma") KENDIM yeniden uretmek.

Yontem (`src/` ALTINA HICBIR SEY YAZILMAZ -- sef kurali): repo'nun `src/`,
`tests/` agaclari ve sefin kiti (`olcu_kiti.py` + iki `conftest.py`)
`tmp_path` altina KOPYALANIR, kopyadaki `normalizer.py`ye tek bir cerrahi
mutasyon uygulanir, ve AYRI alt sureclerde UC bagimsiz olcum yapilir:

  1. DAVRANISSAL DIFERANSIYEL -- kendi ureticim (sabit tohum, tur 5'ten ve
     kitin derleminden FARKLI), 3000 girdi x DORT on ayar x IKI kip
     (`normalize` = miras ACIK, `_normalize_impl(..., False)` = miras
     KAPALI) = 24.000 kosum. Referans, AYNI harness'ta kosan MUTASYONSUZ
     kontrol kopyasidir. MENU on ayari ve miras-kapali kip BILEREK
     dahildir: kit ikisini de kosmuyor (M13).
  2. SEFIN KITI -- mutant agacinda `olcu6_kos` UC on ayarda kosar; bes
     kanalin (geo/kimlik/kapsam/sira/sayi) hangisi kirildigi kaydedilir.
     "Kit bunu gormez" iddiasi boylece KOR KABUL EDILMEZ, OLCULUR.
  3. URUN OLCULERI -- mutant agacinda `pytest tests/unit/ocr/
     test_normalizer.py` kosar; KIRILAN test adlari toplanir. Sefin
     "olcu N kirilmali" cumlelerinin dogrulanma yeri burasidir.

Mutantlar (sef_karari-tur6.md, tur 6 MERCEK B listesi):

  M3   `tail` -> `current` (sef "esdeger mutant" dedi; iddia OLCULUR)
  M4   `_raw_query_pair`'de okuma sirasi yerine INDEKS sirasi
  M5   sag tarafi `nxt` birakan (ham ilk bloga cevirmeyen)
  M11  goruntu gecisini TERS yonde isleyen           <- kit GORMEZ
  M12  adim 3'un yardimcisini degistiren (`islower` -> `isalpha`)
       -- kitin `adim1_4`'u mutantla BIRLIKTE kayar  <- kit GORMEZ
  M13a yalniz MENU on ayarinda bozulan               <- kit KOSMUYOR
  M13b yalniz `apply_inheritance=False` yolunda bozulan  <- kit KOSMUYOR
  M15  miras sorgusunu YANLIS `params` ile soran     <- kit GORMEZ

KONTROL kosumu (mutasyon YOK) ayni harness'tan gecer: davranis
diferansiyeli 0, kit UC on ayarda TEMIZ, urun olculeri 0 kirik. Kontrol,
sondanin kendisinin yanlis pozitif uretmedigini kanitlar.

Sayilar bu dosyada SABIT DEGERE PINLENMEZ (yon ve sifir-olmama pinlenir):
tam sayilar ureticiye baglidir ve ham ciktisi
`tester_B_evidence/r6-mutant-sondasi.txt` altindadir.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import src.ocr.normalizer as normalizer_mod

REPO_KOK = Path(normalizer_mod.__file__).resolve().parents[2]
KIT_DIZINI = REPO_KOK / ".agents" / "tasks" / "T-004"

ON_AYAR_ADLARI = ("DIALOGUE", "MENU", "TOOLTIP", "SUBTITLE")
KIT_ON_AYARLARI = ("DIALOGUE", "TOOLTIP", "SUBTITLE")
KIPLER = ("acik", "kapali")

# ---------------------------------------------------------------------------
# Alt surecte kosan OLCUM betigi. Betik mutant agacinin KOKUNE yazilir, yani
# `sys.path[0]` o dizindir: `import src.ocr.normalizer` KOPYAYI cozer. Sefin
# kiti `src` ZATEN import edildikten SONRA import edilir -- kitin kendi
# `sys.path.insert(0, REPO)` satiri (REPO = mutant agacinin koku) zararsizdir,
# cunku modul nesneleri artik `sys.modules`tedir.
# ---------------------------------------------------------------------------
OLCUM_BETIGI = r'''
# -*- coding: utf-8 -*-
import hashlib, json, random, sys
from pathlib import Path

KOK = Path(__file__).resolve().parent
if str(KOK) not in sys.path:
    sys.path.insert(0, str(KOK))

from src.contracts.models import OcrPreset, Rect, TextBlock
from src.ocr.normalizer import _normalize_impl, normalize

sys.path.append(str(KOK / ".agents" / "tasks" / "T-004"))
import olcu_kiti as KIT

PRESETS = (OcrPreset.DIALOGUE, OcrPreset.MENU, OcrPreset.TOOLTIP, OcrPreset.SUBTITLE)
ADLAR = ("Ada", "Bora", "Efe", "勇者", "魔王")
SEPS = (":", "：")


def gen(rng):
    """Kendi uretici (kitin derleminden ve tur 5 sondasindan FARKLI).

    Bilerek uretilen siniflar -- her biri bir mutant sinifini gorunur kilar:
      * ard arda UZUNLUK-tek-engelli sinirler (>=3 grup) -> ZINCIRLEME miras
        (M11: goruntu gecisi ters yonde islenirse zincir kirilir)
      * tire ile biten satir + devami BUYUK harfle baslayan satir
        (M12: `islower` -> `isalpha` ancak boyle bir cift varsa ayrisir)
      * esik civarinda dagilmis dikey bosluklar: gap = dy - h, dy 18..40
        arasindan secilir -> gap 0..22. Esikler: TOOLTIP 5.4, MENU 9.0,
        DIALOGUE 14.4, SUBTITLE 18.0 -- dordu de STRADDLE edilir
        (M15: sorgu YANLIS `params` ile sorulursa esik kayar)
      * yalniz-etiket bloklari, ikinci konusmaci, esik-alti bloklar,
        yozlasmis (`w<=0`/`h<=0`) geometri, negatif koordinat
      * girdilerin ~yarisi SHUFFLE edilir (K3: girdi okuma sirasinda DEGIL)
        -> INDEKS sirasi ile OKUMA sirasi ayrisir (M4)
    """
    bs = []
    y = 0
    neg = rng.random() < 0.15
    x0 = -400 if neg else 0
    bs.append(TextBlock("Ada" + rng.choice(SEPS) + " " + "X" * rng.randint(80, 170),
                        Rect(x0, y, 240, 18), 0.9))
    y += rng.choice([20, 22, 26, 30])
    for _ in range(rng.randint(4, 12)):
        r = rng.random()
        h = rng.choice([18, 18, 18, 5, 50])
        w = rng.choice([240, 240, 240, 8, 308])
        if rng.random() < 0.06:
            h = rng.choice([0, -4])
        if rng.random() < 0.05:
            w = 0
        conf = 0.45 if rng.random() < 0.10 else 0.9
        if r < 0.22:
            # tire ile biten satir + devam satiri (KUCUK ya da BUYUK harf)
            bs.append(TextBlock(rng.choice("YZW") * rng.randint(20, 60) + " son-",
                                Rect(x0 + rng.choice([0, 0, 100]), y, w, h), conf))
            y += rng.choice([18, 20, 22, 26, 30, 36, 40])
            dev = (rng.choice("abc") if rng.random() < 0.5 else rng.choice("ABC"))
            bs.append(TextBlock(dev * rng.randint(20, 70),
                                Rect(x0 + rng.choice([0, 0, 100]), y,
                                     rng.choice([240, 8, 308]), rng.choice([18, 5, 50])), 0.9))
        elif r < 0.32:
            bs.append(TextBlock(rng.choice(ADLAR[1:]) + rng.choice(SEPS) + " "
                                + "Q" * rng.randint(60, 150), Rect(x0, y, 240, 18), 0.9))
        elif r < 0.40:
            bs.append(TextBlock("Ada" + rng.choice(SEPS), Rect(x0, y, 240, 12), 0.9))
        else:
            bs.append(TextBlock(rng.choice("YZWV") * rng.randint(40, 160),
                                Rect(x0 + rng.choice([0, 0, 100]), y, w, h), conf))
        y += rng.choice([18, 20, 22, 24, 26, 28, 30, 32, 36, 40])
    bs.append(TextBlock("Z" * rng.randint(60, 170), Rect(x0, y, 240, 18), 0.9))
    if rng.random() < 0.5:
        rng.shuffle(bs)
    return bs


def anahtar(segs):
    return "|".join(
        "%s~%s~%d~%d,%d,%d,%d~%s" % (s.source_blocks, s.speaker, len(s.text),
                                     s.bbox.x, s.bbox.y, s.bbox.w, s.bbox.h, s.placeholders)
        for s in segs
    )


def ozet(segs):
    return hashlib.md5(anahtar(segs).encode("utf-8")).hexdigest()[:12]


rng = random.Random(60604006)
GIRDILER = [gen(rng) for _ in range(3000)]

sonuc = {"girdi_sayisi": len(GIRDILER)}

# --- 1. DAVRANISSAL DIFERANSIYEL (4 on ayar x 2 kip) -----------------------
davranis = {}
for preset in PRESETS:
    acik, kapali = [], []
    for bl in GIRDILER:
        try:
            acik.append(ozet(normalize(bl, preset)))
        except Exception as exc:
            acik.append("EXC:" + type(exc).__name__)
        try:
            kapali.append(ozet(_normalize_impl(bl, preset, apply_inheritance=False)))
        except Exception as exc:
            kapali.append("EXC:" + type(exc).__name__)
    davranis[preset.name] = {"acik": acik, "kapali": kapali}
sonuc["davranis"] = davranis

# --- 2. SEFIN KITI (uc on ayar, kitin KENDI derlemi) ----------------------
kit = {}
try:
    derlem = KIT.derlem()
    for pr in KIT.ON_AYARLAR:
        r = KIT.olcu6_kos(pr, derlem)
        kit[pr.name] = {
            "temiz": bool(r.temiz), "geo": r.ayrisma, "kimlik": r.kimlik_ihlali,
            "kapsam": r.kapsam_ihlali, "sira": r.sira_ihlali, "sayi": r.sayi_ihlali,
            "kimlik_kosulamadi": r.kimlik_kosulamadi, "patlama": r.patlama,
            "eksik_sinirlar": list(r.eksik_sinirlar), "sinir": r.sinir,
            "ilk_fark": r.ilk_fark[:200],
        }
except Exception as exc:
    kit["HATA"] = "%s: %s" % (type(exc).__name__, exc)
sonuc["kit"] = kit

(KOK / "sonuc.json").write_text(json.dumps(sonuc), encoding="utf-8")
print("OK", len(GIRDILER))
'''


# ---------------------------------------------------------------------------
# Mutasyonlar -- her biri (ARANAN, YERINE) ikilisi. Desen kaynakta TAM BIR KEZ
# bulunmali; bulunmazsa sonda BAYATLAMISTIR ve gurultulu kirilir.
# ---------------------------------------------------------------------------
_SORGU_SATIRI = """                and _group_rejection_reason(
                    *_raw_query_pair(tail, nxt, blocks), params, ignore_length=True
                )
"""

_IKAME_DONUSU = """    left_idx = reading_order(tail.source_blocks)[-1]
    right_idx = reading_order(nxt.source_blocks)[0]
    return (replace(tail, bbox=blocks[left_idx].bbox), replace(nxt, bbox=blocks[right_idx].bbox))
"""

_GORUNUM_GECISI = """        for i, pure_length in enumerate(pure_length_boundaries, start=1):
            if pure_length and groups[i - 1].speaker is not None:
                groups[i] = replace(groups[i], speaker=groups[i - 1].speaker)
"""

_ADIM5 = """    grouped = (
        _group(items, params, blocks=blocks, apply_inheritance=apply_inheritance)
        if params.should_group
        else items
    )
"""

MUTANTLAR: dict[str, tuple[str, str]] = {
    # --- sefin "esdeger mutant" iddiasi (K24'un tail kurali, K28 biciminde) ---
    "M3_tail_yerine_current": (
        _SORGU_SATIRI,
        """                and _group_rejection_reason(
                    *_raw_query_pair(current, nxt, blocks), params, ignore_length=True
                )
""",
    ),
    # --- kitin GORDUGU iki mutant ------------------------------------------
    "M4_indeks_sirasi": (
        _IKAME_DONUSU,
        """    left_idx = max(tail.source_blocks)  # MUTANT M4: OKUMA degil INDEKS sirasi
    right_idx = min(nxt.source_blocks)  # MUTANT M4
    return (replace(tail, bbox=blocks[left_idx].bbox), replace(nxt, bbox=blocks[right_idx].bbox))
""",
    ),
    "M5_sag_taraf_nxt_kalir": (
        _IKAME_DONUSU,
        """    left_idx = reading_order(tail.source_blocks)[-1]
    return (replace(tail, bbox=blocks[left_idx].bbox), nxt)  # MUTANT M5: sag taraf HAM DEGIL
""",
    ),
    # --- kitin GORMEDIGI/KOSMADIGI dort sinif (sefin "bilinen sinirlar" tablosu) ---
    "M11_goruntu_gecisi_ters_yon": (
        _GORUNUM_GECISI,
        """        for i in range(len(pure_length_boundaries), 0, -1):  # MUTANT M11: TERS yon
            pure_length = pure_length_boundaries[i - 1]
            if pure_length and groups[i - 1].speaker is not None:
                groups[i] = replace(groups[i], speaker=groups[i - 1].speaker)
""",
    ),
    "M12_adim3_yardimcisi": (
        '        if buffer.text.endswith("-") and nxt.text[:1].islower():\n',
        '        if buffer.text.endswith("-") and nxt.text[:1].isalpha():  # MUTANT M12\n',
    ),
    "M13a_yalniz_menu": (
        _ADIM5,
        """    grouped = (
        _group(items, params, blocks=blocks, apply_inheritance=apply_inheritance)
        if params.should_group
        else [replace(it, speaker=None) for it in items]  # MUTANT M13a: YALNIZ menu yolu
    )
""",
    ),
    "M13b_yalniz_miras_kapali": (
        "    if apply_inheritance:\n",
        """    if (
        not apply_inheritance
        and pure_length_boundaries
        and pure_length_boundaries[0]
        and groups[0].speaker is not None
    ):
        # MUTANT M13b: miras KAPALI yola SIZINTI -- K23'un makine denetimi
        # (`apply_inheritance=False`) artik gercegi soylemiyor.
        groups[1] = replace(groups[1], speaker=groups[0].speaker)
    if apply_inheritance:
""",
    ),
    "M15_yanlis_params": (
        _SORGU_SATIRI,
        """                and _group_rejection_reason(
                    *_raw_query_pair(tail, nxt, blocks),
                    get_params(OcrPreset.MENU),  # MUTANT M15: YANLIS params
                    ignore_length=True,
                )
""",
    ),
}

KIT_GORMEZ = ("M11_goruntu_gecisi_ters_yon", "M12_adim3_yardimcisi",
              "M13a_yalniz_menu", "M13b_yalniz_miras_kapali", "M15_yanlis_params")


# ---------------------------------------------------------------------------
# Harness
# ---------------------------------------------------------------------------
def _agac_kur(kok: Path, mutant: str | None) -> Path:
    """Mutant agacini kurar: `src/` (mute), `tests/`, ve sefin kiti."""
    hedef = kok / (mutant or "kontrol")
    hedef.mkdir(parents=True, exist_ok=True)
    yoksay = shutil.ignore_patterns("__pycache__", "*.pyc")
    shutil.copytree(REPO_KOK / "src", hedef / "src", ignore=yoksay, dirs_exist_ok=True)
    shutil.copytree(REPO_KOK / "tests", hedef / "tests", ignore=yoksay, dirs_exist_ok=True)
    kit_hedef = hedef / ".agents" / "tasks" / "T-004"
    kit_hedef.mkdir(parents=True, exist_ok=True)
    for ad in ("olcu_kiti.py", "conftest.py"):
        shutil.copy2(KIT_DIZINI / ad, kit_hedef / ad)

    norm = hedef / "src" / "ocr" / "normalizer.py"
    kaynak = norm.read_text(encoding="utf-8")
    if mutant is None:
        assert kaynak == (REPO_KOK / "src" / "ocr" / "normalizer.py").read_text(encoding="utf-8")
    else:
        aranan, yerine = MUTANTLAR[mutant]
        assert kaynak.count(aranan) == 1, (
            f"{mutant}: mutasyon deseni kaynakta TAM BIR KEZ bulunmali "
            f"({kaynak.count(aranan)} bulundu) -- kod yeniden yazilmis, sonda BAYATLADI"
        )
        yeni = kaynak.replace(aranan, yerine)
        assert yeni != kaynak
        norm.write_text(yeni, encoding="utf-8")
    return hedef


def _kos(hedef: Path, argv: list[str], timeout: int = 900) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTHONHASHSEED")}
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, *argv], cwd=str(hedef), capture_output=True, text=True,
        encoding="utf-8", errors="replace", env=env, timeout=timeout,
    )


def _urun_olculeri(hedef: Path) -> list[str]:
    """Mutant agacinda urun test dosyasini kostur, KIRILAN test adlarini dondur."""
    proc = _kos(hedef, ["-m", "pytest", "tests/unit/ocr/test_normalizer.py",
                        "-q", "--tb=no", "-rf", "-p", "no:randomly", "-p", "no:cacheprovider"])
    kirik: list[str] = []
    for satir in proc.stdout.splitlines():
        if satir.startswith("FAILED ") or satir.startswith("ERROR "):
            ad = satir.split(" ", 1)[1].split(" ")[0]
            kirik.append(ad.split("::", 1)[-1])
    if proc.returncode not in (0, 1) and not kirik:
        raise AssertionError(f"urun olculeri kosulamadi:\n{proc.stdout[-3000:]}\n{proc.stderr[-2000:]}")
    return sorted(set(kirik))


_ONBELLEK: dict[str, dict[str, object]] = {}


@pytest.fixture(scope="session")
def sonda(tmp_path_factory: pytest.TempPathFactory):  # type: ignore[no-untyped-def]
    kok = tmp_path_factory.mktemp("sonda6")

    def al(mutant: str | None) -> dict[str, object]:
        anahtar = mutant or "kontrol"
        if anahtar not in _ONBELLEK:
            hedef = _agac_kur(kok, mutant)
            (hedef / "_olcum6.py").write_text(OLCUM_BETIGI, encoding="utf-8")
            proc = _kos(hedef, ["_olcum6.py"])
            assert proc.returncode == 0, (
                f"olcum betigi patladi ({anahtar}):\n{proc.stdout[-2000:]}\n{proc.stderr[-3000:]}"
            )
            veri = json.loads((hedef / "sonuc.json").read_text(encoding="utf-8"))
            veri["urun_kirik"] = _urun_olculeri(hedef)
            _ONBELLEK[anahtar] = veri
        return _ONBELLEK[anahtar]

    return al


def _fark(kontrol: dict, mutant: dict) -> dict[str, int]:
    """(on ayar, kip) basina ayrisan girdi sayisi + toplam."""
    out: dict[str, int] = {}
    toplam = 0
    for ad in ON_AYAR_ADLARI:
        for kip in KIPLER:
            a = kontrol["davranis"][ad][kip]
            b = mutant["davranis"][ad][kip]
            assert len(a) == len(b)
            n = sum(1 for x, y in zip(a, b) if x != y)
            out[f"{ad}.{kip}"] = n
            toplam += n
    out["TOPLAM"] = toplam
    return out


def _kit_ozeti(veri: dict) -> str:
    return " ".join(
        f"{ad[:4]}[geo={veri['kit'][ad]['geo']},kim={veri['kit'][ad]['kimlik']},"
        f"kap={veri['kit'][ad]['kapsam']},sir={veri['kit'][ad]['sira']},"
        f"say={veri['kit'][ad]['sayi']}]"
        for ad in KIT_ON_AYARLARI
    )


def _rapor(ad: str, veri: dict, farklar: dict[str, int] | None) -> None:
    print(f"\n[{ad}]")
    if farklar is not None:
        print("  davranis: " + " ".join(f"{k}={v}" for k, v in farklar.items()))
    print("  kit     : " + _kit_ozeti(veri)
          + "  temiz=" + str([veri["kit"][a]["temiz"] for a in KIT_ON_AYARLARI]))
    print(f"  urun    : {len(veri['urun_kirik'])} kirik {veri['urun_kirik'][:6]}")


# ===========================================================================
# 0. KONTROL -- sonda kendi harness'inda yanlis pozitif URETMIYOR
# ===========================================================================


def test_r6_sonda_kontrol_kosumu_temiz(sonda) -> None:  # type: ignore[no-untyped-def]
    """Mutasyonsuz kopya UC olcumden de TEMIZ gecmeli:
      - kendi diferansiyelim kendisiyle 0 ayrisma (deterministik),
      - sefin kiti UC on ayarda `temiz` (bes kanalin hepsi 0),
      - urun olculeri 0 kirik.
    Bu kosum asagidaki mutant iddialarinin ANLAMLI olmasinin SARTIDIR."""
    k = sonda(None)
    _rapor("KONTROL", k, _fark(k, k))
    assert k["girdi_sayisi"] == 3000
    assert "HATA" not in k["kit"], k["kit"]
    for ad in KIT_ON_AYARLARI:
        assert k["kit"][ad]["temiz"] is True, (ad, k["kit"][ad])
        assert k["kit"][ad]["sinir"] > 0
    assert k["urun_kirik"] == [], k["urun_kirik"]
    # deterministiklik: ayni agac iki kez okundugunda ayni ozetler
    assert _fark(k, k)["TOPLAM"] == 0


# ===========================================================================
# 1. M3 -- sefin "esdeger mutant" iddiasi OLCULUR (kor kabul edilmez)
# ===========================================================================


def test_r6_m3_tail_yerine_current_davranissal_esdeger_ama_yapisal_yakalaniyor(sonda) -> None:  # type: ignore[no-untyped-def]
    """Sef (sef_karari-tur6.md): "M3 (`tail`->`current`) KALDIRILIR --
    surum 3'un biciminde ESDEGER mutanttir; yeniden nisanlanirsa OLU
    mutant olur."

    Iddiayi KOR KABUL ETMIYORUM, olcuyorum. Sonuc IKI PARCALI:
      (a) sefin nitelemesi DAVRANISSAL olarak DOGRU -- 24.000 kosumda 0
          ayrisma (`current.source_blocks` uzerinde okuma-sirasi-son,
          `tail.source_blocks` uzerindekiyle ayni bloga duser);
      (b) ama "olu mutant" nitelemesi EKSIK -- kitin KIMLIK kanali ve urun
          olculeri onu YINE DE kiriyor, cunku sol tarafin `source_blocks`'u
          artik hicbir OGENIN `source_blocks`'u degil (birlesik kume).

    Yani M3'u `test_k23_mutant_sondasi_tur5.py`den cikarmak DOGRU (davranis
    sondasi icin olu), ama K28'in kimlik onkosulu onu yapisal olarak
    yakalamaya devam ediyor -- bu, K28'in `source_blocks` KORUMA sartinin
    (V2 onkosulu) gercekten dis oldugunun kanitidir."""
    k, m = sonda(None), sonda("M3_tail_yerine_current")
    f = _fark(k, m)
    _rapor("M3_tail_yerine_current", m, f)
    assert f["TOPLAM"] == 0, (
        "M3 DAVRANISSAL olarak ayrisiyor -- sefin 'esdeger mutant' nitelemesi "
        f"YANLIS olurdu: {f}"
    )
    kirik_kanal = [ad for ad in KIT_ON_AYARLARI if not m["kit"][ad]["temiz"]]
    assert kirik_kanal == list(KIT_ON_AYARLARI), m["kit"]
    assert all(m["kit"][ad]["kimlik"] > 0 for ad in KIT_ON_AYARLARI), m["kit"]
    assert m["urun_kirik"], "M3 hicbir urun olcusunu kirmiyor -- gercekten OLU mutant"


# ===========================================================================
# 2. M4 / M5 -- kitin GORDUGU iki mutant. Sefin "kirilmali" cumleleri.
# ===========================================================================


def test_r6_m4_indeks_sirasi_kiti_ve_olcu3u_kiriyor(sonda) -> None:  # type: ignore[no-untyped-def]
    """M4: `_raw_query_pair` okuma sirasi (`(y, x, i)`) yerine INDEKS
    sirasi (`max`/`min`) kullaniyor.

    Beklenti (sef_karari-tur6.md, MERCEK B/1): kitin `geo` kanali ve
    URUN olcu 3 kirilmali. `olcu3_fixture` girdisi OKUMA SIRASINDA
    DEGILDIR (idx0 y=40, idx1 y=0, idx2 y=20) -- indeks sirasiyla son 2,
    okuma sirasiyla son 0.

    OLCUM NOTU (sefin cumlesinden sapma, bulgu olarak raporlanir): ayni
    beklenti "olcu 3b" icin de yazilmisti, ama `olcu3b_fixture`'in bloklari
    indeks sirasi = okuma sirasi olacak sekilde dizilidir (y=0,20,40,60,90),
    yani M4 orada AYRISMAZ. Testin kendisi olcup raporlar; 3b'nin kirilip
    kirilmadigi assert edilmez, cunku kirilmamasi FIXTURE'in ozelligidir,
    uygulamanin degil."""
    k, m = sonda(None), sonda("M4_indeks_sirasi")
    f = _fark(k, m)
    _rapor("M4_indeks_sirasi", m, f)
    assert f["TOPLAM"] > 0, "M4 hicbir davranis ayrismasi uretmiyor -- ureticim dissiz"
    assert all(m["kit"][ad]["geo"] > 0 for ad in KIT_ON_AYARLARI), m["kit"]
    assert all(not m["kit"][ad]["temiz"] for ad in KIT_ON_AYARLARI)
    olcu3 = [t for t in m["urun_kirik"] if "olcu3_" in t]
    assert olcu3, f"olcu 3 M4'u yakalamiyor: {m['urun_kirik']}"
    olcu6 = [t for t in m["urun_kirik"] if "olcu6" in t]
    assert olcu6, f"olcu 6 M4'u yakalamiyor: {m['urun_kirik']}"


def test_r6_m5_sag_taraf_nxt_kalirsa_olcu2_kiriliyor(sonda) -> None:  # type: ignore[no-untyped-def]
    """M5: sag taraf `nxt` olarak birakiliyor (ham ILK bloga cevrilmiyor)
    -- K28'in sag taraf cumlesi tam olarak bunu yasakliyor.

    Beklenti (sef): URUN olcu 2 kirilmali (uc varyantin ucu de: `height`
    = K16 regresyonu, `gap`, `overlap`). Kitin `geo` kanali da gormeli."""
    k, m = sonda(None), sonda("M5_sag_taraf_nxt_kalir")
    f = _fark(k, m)
    _rapor("M5_sag_taraf_nxt_kalir", m, f)
    assert f["TOPLAM"] > 0
    assert all(m["kit"][ad]["geo"] > 0 for ad in KIT_ON_AYARLARI), m["kit"]
    olcu2 = [t for t in m["urun_kirik"] if "olcu2" in t]
    assert len(olcu2) >= 3, f"olcu 2'nin uc varyanti da kirilmali: {m['urun_kirik']}"


# ===========================================================================
# 3. KITIN GORMEDIGI DORT SINIF -- bu turun ASIL yukumlulugu.
#    Her testte IKI iddia ayri ayri olculur:
#      (a) mutant GERCEKTEN bozuk mu  -> davranissal diferansiyel > 0
#      (b) sefin "kit gormez" iddiasi dogru mu -> kit UC on ayarda TEMIZ mi
# ===========================================================================


def test_r6_m11_goruntu_gecisi_ters_yon_kite_gorunmez_sondam_yakaliyor(sonda) -> None:  # type: ignore[no-untyped-def]
    """M11 (sefin "bilinen sinirlar" tablosu, `n23` sinifi): goruntu gecisi
    SOLDAN SAGA degil SAGDAN SOLA isleniyor -- ZINCIRLEME miras kirilir
    (`Ada: a` / `b` / `c` -> `['Ada','Ada',None]`), ama sorgu SIRASI
    bozulmaz (goruntu dongusu hic sorgu uretmez), bu yuzden kitin `sira`
    kanali da dahil BES kanalin hicbiri gormez.

    Sef olctu: 1322 ayrisma, kit TEMIZ. IKISINI DE KENDIM yeniden
    uretiyorum."""
    k, m = sonda(None), sonda("M11_goruntu_gecisi_ters_yon")
    f = _fark(k, m)
    _rapor("M11_goruntu_gecisi_ters_yon", m, f)
    assert f["TOPLAM"] > 0, (
        "M11 sondamda hic ayrisma uretmedi -- ZINCIRLEME miras ureten girdi "
        "sinifim yok, sondam DISSIZ"
    )
    # miras KAPALI kipte hicbir goruntu gecisi kosmaz -> ayrisma OLMAMALI
    assert all(f[f"{ad}.kapali"] == 0 for ad in ON_AYAR_ADLARI), f
    # MENU'de `_group` hic cagirilmaz -> goruntu gecisi de yok
    assert f["MENU.acik"] == 0, f
    assert all(m["kit"][ad]["temiz"] for ad in KIT_ON_AYARLARI), (
        "sefin 'kit bunu GORMEZ' iddiasi YANLIS cikti -- kit M11'i yakaliyor: " + _kit_ozeti(m)
    )


def test_r6_m12_adim3_yardimcisi_kimlik_kanalini_bosaltiyor(sonda) -> None:  # type: ignore[no-untyped-def]
    """M12 (sefin "bilinen sinirlar" tablosu, `adim1_4` bagimsiz degil):
    adim 3'un hyphen kosulu `islower()` -> `isalpha()` yapiliyor; artik
    BUYUK harfle baslayan devam satirlari da birlesiyor.

    Kitin KIMLIK kanali bunu GOREMEZ, cunku kitin referans oge listesi
    (`adim1_4`) DENETLENEN modulun `_merge_hyphenated`'ini cagirir --
    mutantla BIRLIKTE kayar (PROTOKOL S4.6/8 ihlali; sef bunu bilerek
    yapti ve tester yukumlulugune cevirdi).

    Sef olctu: n27 3672 ayrisma, kit TEMIZ."""
    k, m = sonda(None), sonda("M12_adim3_yardimcisi")
    f = _fark(k, m)
    _rapor("M12_adim3_yardimcisi", m, f)
    assert f["TOPLAM"] > 0, (
        "M12 sondamda hic ayrisma uretmedi -- tire ile biten satir + BUYUK harfle "
        "baslayan devam satiri cifti ureticimde yok, sondam DISSIZ"
    )
    # adim 3 on ayardan BAGIMSIZ: dort on ayarin DORDU de ayrismali
    for ad in ON_AYAR_ADLARI:
        assert f[f"{ad}.acik"] > 0, (ad, f)
    assert all(m["kit"][ad]["temiz"] for ad in KIT_ON_AYARLARI), (
        "sefin 'kit bunu GORMEZ' iddiasi YANLIS cikti -- kit M12'yi yakaliyor: " + _kit_ozeti(m)
    )


def test_r6_m13a_yalniz_menu_yolunda_bozuk_kit_menuyu_hic_kosmuyor(sonda) -> None:  # type: ignore[no-untyped-def]
    """M13a (sefin "bilinen sinirlar" tablosu): bozulma YALNIZ `menu` on
    ayarinin yolunda (`params.should_group is False` dali) -- menu
    segmentlerinin `speaker` alani dusuruluyor.

    Kit UC on ayar kosar (DIALOGUE/TOOLTIP/SUBTITLE); `menu` DORDUNCUDUR ve
    kit onu HIC kosmaz. Sef olctu: n36 2422 ayrisma, kit TEMIZ."""
    k, m = sonda(None), sonda("M13a_yalniz_menu")
    f = _fark(k, m)
    _rapor("M13a_yalniz_menu", m, f)
    assert f["MENU.acik"] > 0 and f["MENU.kapali"] > 0, f
    for ad in ("DIALOGUE", "TOOLTIP", "SUBTITLE"):
        assert f[f"{ad}.acik"] == 0 and f[f"{ad}.kapali"] == 0, (ad, f)
    assert all(m["kit"][ad]["temiz"] for ad in KIT_ON_AYARLARI), (
        "kit M13a'yi yakaliyor -- 'menu kosulmuyor' iddiasi YANLIS: " + _kit_ozeti(m)
    )


def test_r6_m13b_yalniz_miras_kapali_yolda_bozuk_kit_o_kipi_kosmuyor(sonda) -> None:  # type: ignore[no-untyped-def]
    """M13b (sefin "bilinen sinirlar" tablosu, `n37` = "K23 kancasi"):
    bozulma YALNIZ `apply_inheritance=False` yolunda -- miras KAPALI iken
    ilk sinirda YINE DE miras uygulaniyor.

    Bu, K23'un MAKINE DENETIMINI (olcu 7) yalanci yapan siniftir: kapali
    kip ACIK kipe yaklastigi icin "acik == kapali" denetimi DAHA KOLAY
    yesil kalir. Kit yalnizca `normalize` (yani daima `True`) cagirir,
    bu yolu HIC kosmaz. Sef olctu: 12 ayrisma, kit TEMIZ."""
    k, m = sonda(None), sonda("M13b_yalniz_miras_kapali")
    f = _fark(k, m)
    _rapor("M13b_yalniz_miras_kapali", m, f)
    assert f["TOPLAM"] > 0, "M13b sondamda hic ayrisma uretmedi -- miras KAPALI kipi kosmuyorum"
    for ad in ON_AYAR_ADLARI:
        assert f[f"{ad}.acik"] == 0, (
            f"M13b miras ACIK yolu da degistirdi ({ad}) -- mutant izole degil: {f}"
        )
    assert any(f[f"{ad}.kapali"] > 0 for ad in ON_AYAR_ADLARI), f
    assert all(m["kit"][ad]["temiz"] for ad in KIT_ON_AYARLARI), (
        "kit M13b'yi yakaliyor -- '`apply_inheritance=False` kosulmuyor' iddiasi YANLIS: "
        + _kit_ozeti(m)
    )


def test_r6_m15_yanlis_params_kit_params_kimligini_kaydetmiyor(sonda) -> None:  # type: ignore[no-untyped-def]
    """M15 (sefin "bilinen sinirlar" tablosu): miras-uygunluk sorgusu DOGRU
    ogelerle ama YANLIS `params` ile soruluyor (`MENU`nun tablosu;
    `max_vertical_gap_ratio` 0.5 -- DIALOGUE 0.8, TOOLTIP 0.3, SUBTITLE 1.0).

    Kitin kancasi `(a, b, params)` gorur ama `params`i KAYDETMEZ; sorgunun
    iki tarafi da DOGRU ham bloklardan geldigi icin geo/kimlik/kapsam/sira/
    sayi kanallarinin hicbiri kirilmaz. Sef olctu: 398/516 ayrisma, kit
    TEMIZ ve kor takimda ek kirik 0."""
    k, m = sonda(None), sonda("M15_yanlis_params")
    f = _fark(k, m)
    _rapor("M15_yanlis_params", m, f)
    assert f["TOPLAM"] > 0, (
        "M15 sondamda hic ayrisma uretmedi -- dikey boslugu MENU esigi (0.5*h) ile "
        "diger on ayarlarin esigi arasinda birakan girdi uretmiyorum, sondam DISSIZ"
    )
    # bozulma miras kararindadir: bolumleme (kapali kip) AYNI kalmali
    assert all(f[f"{ad}.kapali"] == 0 for ad in ON_AYAR_ADLARI), (
        f"M15 BOLUMLEMEYI degistirdi -- K23 ihlali olurdu, beklenmiyordu: {f}"
    )
    assert all(m["kit"][ad]["temiz"] for ad in KIT_ON_AYARLARI), (
        "kit M15'i yakaliyor -- '`params` kimligi kaydedilmiyor' iddiasi YANLIS: "
        + _kit_ozeti(m)
    )


# ===========================================================================
# 4. TOPLU KAPI -- sefin yukumlulugu: "B'nin diferansiyeli bu siniflari
#    KIRMAK ZORUNDADIR; kiramiyorsa B'nin sondasi dissizdir."
# ===========================================================================


def test_r6_bes_kit_korlugunun_hepsini_kendi_sondam_yakaliyor(sonda) -> None:  # type: ignore[no-untyped-def]
    """Sefin M11/M12/M13/M15 yukumlulugunun TEK kapisi: kitin gormedigi
    BES mutantin BESI de benim davranissal diferansiyelimde ayrisiyor.

    Ayrica kaydedilir: bu bes mutantin URUN olculerinde kac kirik urettigi
    -- kitin gormedigi bir sinifi urun testlerinin gorup gormedigi ayri bir
    bilgidir ve verdict'e girer."""
    k = sonda(None)
    satirlar = []
    for ad in KIT_GORMEZ:
        m = sonda(ad)
        f = _fark(k, m)
        kit_temiz = all(m["kit"][p]["temiz"] for p in KIT_ON_AYARLARI)
        satirlar.append((ad, f["TOPLAM"], kit_temiz, len(m["urun_kirik"]), m["urun_kirik"]))
    print("\n--- kitin GORMEDIGI bes sinif ---")
    for ad, toplam, kit_temiz, n_urun, urun in satirlar:
        print(f"  {ad:32s} davranis={toplam:6d}  kit_temiz={kit_temiz!s:5s}  urun_kirik={n_urun} {urun[:4]}")
    dissiz = [ad for ad, toplam, _, _, _ in satirlar if toplam == 0]
    assert not dissiz, f"sondam su mutantlari KIRAMIYOR (dissiz): {dissiz}"
    gormeyen = [ad for ad, _, kit_temiz, _, _ in satirlar if not kit_temiz]
    assert not gormeyen, (
        "sefin 'kit bu siniflari gormez' iddiasi su mutantlar icin YANLIS cikti "
        f"(kit onlari YAKALIYOR): {gormeyen}"
    )
