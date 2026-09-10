"""TESTER-B (KARAR UYUMU) -- T-004 TUR 5 -- K23/K24 MUTANT SONDASI.

`test_karar_uyumu_tur5.py` K23 degismezini ve K24'un `tail` kuralini
DOGRULUYOR. Ama bir denetimin YESIL olmasi, o denetimin DISLERI oldugunu
KANITLAMAZ: K23 degismezi "acik == kapali" bicimindedir ve bu bicim,
miras mekanizmasi HIC CALISMASA da yesil kalir. Bu dosya sondayi tersten
kurar:

  **Kodu K23/K24'ten SAPTIRAN bir mutasyon, denetimi GERCEKTEN kiriyor mu?**

Yontem (`src/` ALTINA HICBIR SEY YAZILMAZ -- sef kurali): repo'nun `src/`
agaci `tmp_path` altina KOPYALANIR, kopyadaki `normalizer.py`ye tek bir
cerrahi mutasyon uygulanir, ve AYRI bir alt surecte (kopyanin dizini
`sys.path[0]` olur) dort olcum yapilir:

  `k23_ihlal`        -- kendi (monolog agirlikli, sabit tohumlu) ureticimle
                        bulunan K23 ihlali SAYISI (bolumleme miras acik/
                        kapali FARKLI cikan kosum sayisi)
  `b1_src`           -- sef_karari-tur5.md B1 senaryosunun bolumlemesi
  `k24_kuyruk_speaker` -- K24'un zorunlu geometrisinde kuyruk segmentin
                        `speaker`i (`None` olmali; birlesik-bbox artifakti
                        yanlislikla `"Ada"` verir)
  `k2_speakers`      -- esik-alti orta blok fixture'inda (K21: uzunluk TEK
                        engel DEGIL) speaker dizisi

Uc mutant:

  M1 (B1 sizintisi)  -- miras, bolumleme gecisinde `nxt`e uygulanir ve
                        bir SONRAKI gruplama kararina GIRDI olur (tur 4'un
                        gercek hatasi). K23 ihlali BEKLENIR.
  M2 (K24/K21 sorgusu kaldirilir) -- `ignore_length=True` ikinci sorgusu
                        `True` ile degistirilir (tur 3'un K19 mekanizmasi).
                        K23 ihlal ETMEZ (bolumleme degismez) ama K24 ve
                        K21 olcumleri BOZULUR.
  M3 (`tail` -> `current`) -- K24'un TAM OLARAK yasakladigi degisiklik.
                        Yine K23 ihlali YOK; SADECE `k24_kuyruk_speaker`
                        bozulur -- yani K23 ve K24 denetimleri BIRBIRINDEN
                        BAGIMSIZ olarak disli.

KONTROL kosumu (mutasyon YOK) ayni harness ile calisir: hepsi temiz
cikmali. Kontrol, sondanin kendisinin bozuk olmadigini kanitlar.
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

# ---------------------------------------------------------------------------
# Alt surecte kosan OLCUM betigi -- kopyalanan (muhtemelen MUTE) `src/`
# agacini import eder. Betik `tmp_path` icine yazildigi icin `sys.path[0]`
# o dizindir; yani `import src.ocr.normalizer` KOPYAYI cozer.
# ---------------------------------------------------------------------------
OLCUM_BETIGI = r'''
# -*- coding: utf-8 -*-
import json, random, sys

from src.contracts.models import OcrPreset, Rect, TextBlock
from src.ocr.normalizer import _normalize_impl, normalize
from src.ocr.presets import get_params

PRESETS = (OcrPreset.DIALOGUE, OcrPreset.MENU, OcrPreset.TOOLTIP, OcrPreset.SUBTITLE)
NAMES = ("Ada", "Efe", "Zoe", "勇者", "魔王")
SEPS = (":", "：")


def blk(text, x, y, w=300, h=20, confidence=0.9):
    return TextBlock(text=text, bbox=Rect(x=x, y=y, w=w, h=h), confidence=confidence)


def key(segments):
    return [
        (
            s.source_blocks,
            s.text,
            (s.bbox.x, s.bbox.y, s.bbox.w, s.bbox.h),
            s.placeholders,
        )
        for s in segments
    ]


def gen(rng):
    """Monolog agirlikli: uzunluk-kaynakli bolunme SIK (miras GERCEKTEN
    tetiklenir), araya KENDI etiketiyle gelen replikler serpilir -- B1'in
    dogal habitati."""
    blocks = []
    y = 0
    h = 20
    for _ in range(rng.randint(3, 14)):
        r = rng.random()
        if r < 0.20:
            text = rng.choice(NAMES) + rng.choice(SEPS)
        elif r < 0.40:
            text = rng.choice(NAMES) + rng.choice(SEPS) + " " + "g" * rng.randint(40, 120)
        else:
            text = rng.choice("xyzw") * rng.randint(40, 120)
        blocks.append(TextBlock(text=text, bbox=Rect(x=0, y=y, w=300, h=h), confidence=0.95))
        y += rng.choices([22, 22, 24, 400], weights=[60, 20, 10, 10])[0]
        h = 20 if rng.random() > 0.06 else rng.choice([0, -4, 1])
    return blocks


sonuc = {}

# --- 1. K23 degismezi (kendi ureticim, sabit tohum) ------------------------
ihlal = 0
ilk_ihlal = None
rng = random.Random(20240510)
kosum = 0
for _ in range(400):
    blocks = gen(rng)
    for preset in PRESETS:
        kosum += 1
        acik = _normalize_impl(blocks, preset, apply_inheritance=True)
        kapali = _normalize_impl(blocks, preset, apply_inheritance=False)
        if key(acik) != key(kapali):
            ihlal += 1
            if ilk_ihlal is None:
                ilk_ihlal = {
                    "preset": preset.value,
                    "acik": [list(s.source_blocks) for s in acik],
                    "kapali": [list(s.source_blocks) for s in kapali],
                }
sonuc["kosum"] = kosum
sonuc["k23_ihlal"] = ihlal
sonuc["k23_ilk_ihlal"] = ilk_ihlal

# --- 2. B1 senaryosu (sef_karari-tur5.md) ---------------------------------
cap = get_params(OcrPreset.DIALOGUE).max_group_chars
b1 = [
    blk("Ada:", 10, 0, h=12),
    blk("a" * (cap - 30), 10, 14),
    blk("b" * 60, 10, 36),
    blk("Ada: " + "c" * 60, 10, 58),
]
b1_out = normalize(b1, OcrPreset.DIALOGUE)
sonuc["b1_src"] = [list(s.source_blocks) for s in b1_out]
sonuc["b1_speakers"] = [s.speaker for s in b1_out]

# --- 3. K24 zorunlu geometrisi (grubun BASI en alta uzaniyor) -------------
k24 = [
    blk("Ada:", 0, -30, h=12),
    blk("A" * 150, 0, 0, w=200, h=120),
    blk("B" * 120, 0, 10, w=200, h=12),
    blk("C" * 120, 0, 60, w=200, h=12),
]
k24_out = normalize(k24, OcrPreset.DIALOGUE)
sonuc["k24_src"] = [list(s.source_blocks) for s in k24_out]
sonuc["k24_kuyruk_speaker"] = k24_out[-1].speaker

# --- 4. K2/K21: esik-alti orta blok GEOMETRIK bosluk BIRAKIR --------------
body = "x" * 60
n = (cap // 60) + 3
k2_blocks = [blk("Ada:", 10, 0)]
y = 22
for i in range(n):
    k2_blocks.append(blk(body, 10, y))
    y += 22
    if i == n // 2:
        k2_blocks.append(blk("GURULTU", 10, y, confidence=0.05))
        y += 22
k2_out = normalize(k2_blocks, OcrPreset.DIALOGUE)
sonuc["k2_speakers"] = [s.speaker for s in k2_out]

print(json.dumps(sonuc, ensure_ascii=False))
'''


# ---------------------------------------------------------------------------
# Mutasyonlar -- her biri (ad, ARANAN, YERINE) ucluse.
# ---------------------------------------------------------------------------
# TUR 6'DA YENIDEN NISANLANDI (sef_karari-tur6.md, K28). Miras-sorgusu satiri
# `_group_rejection_reason(tail, nxt, params, ignore_length=True)` olmaktan cikip
# `_group_rejection_reason(*_raw_query_pair(tail, nxt, blocks), params,
# ignore_length=True)` bicimine gecti. M1'in aradigi `_ANA_BLOK` deseni bu satiri
# ICERDIGI icin M1 ve M2 desenleri KACINILMAZ olarak bayatladi -- sefin §4.6/5
# listesinde ONCEDEN adlandirilmisti. Desenler yeni satira nisanlandi; `_olc`
# icindeki "TEK KEZ bulunmali" assertion'i bayatlamayi GURULTULU kirmaya devam eder.
_MIRAS_SORGUSU = """                and _group_rejection_reason(
                    *_raw_query_pair(tail, nxt, blocks), params, ignore_length=True
                )
                is None
"""

_ANA_BLOK = """            pure_length_boundaries.append(
                reason == "length"
                and nxt.speaker is None
                # K28 (TUR 6): sorgunun IKI tarafi da OZGUN bloklardan --
                # ikame `_raw_query_pair`'in ICINDEDIR, bu dongude DEGIL
                # (bolumleme gecisi hicbir `replace(...)` yazmaz).
""" + _MIRAS_SORGUSU + """            )
            current = nxt
            tail = nxt
"""

_M1_YERINE = """            _sizinti = (
                reason == "length"
                and nxt.speaker is None
""" + _MIRAS_SORGUSU + """            )
            pure_length_boundaries.append(_sizinti)
            if apply_inheritance and _sizinti and current.speaker is not None:
                nxt = replace(nxt, speaker=current.speaker)  # MUTANT M1: sizinti
            current = nxt
            tail = nxt
"""

# M3 (`tail` -> `current`) BU DOSYADAN KALDIRILDI. Sef (sef_karari-tur6.md) K28
# bicimi altinda onu "esdeger mutant" sayip cikarilmasini istedi. Iddiayi KOR
# KABUL ETMEDIM: `test_k28_mutant_sondasi_tur6.py::test_r6_m3_tail_yerine_current_
# davranissal_esdeger_ama_yapisal_yakalaniyor` icinde KENDIM olctum -- 3000 girdi
# x 4 on ayar x 2 kip = 24.000 kosumda 0 DAVRANISSAL ayrisma (sefin "esdeger"
# nitelemesi DOGRU), ama kitin KIMLIK kanali (2387/1350/826) ve 10 urun olcusu
# onu YINE DE kiriyor (sefin "yeniden nisanlanirsa OLU mutant olur" nitelemesi
# EKSIK). Ham cikti: `tester_B_evidence/r6-mutant-sondasi.txt`.
MUTANTLAR: dict[str, tuple[str, str]] = {
    "M1_bolumlemeye_sizinti": (_ANA_BLOK, _M1_YERINE),
    "M2_k24_sorgusu_kaldirildi": (
        _MIRAS_SORGUSU,
        "                and True  # MUTANT M2: K21/K24/K28 ikinci sorgusu YOK\n",
    ),
}


def _olc(tmp_path: Path, mutant: str | None) -> dict[str, object]:
    """`src/` agacini kopyala, (varsa) mutasyonu uygula, olcum betigini
    AYRI bir surecte kostur ve JSON sonucunu dondur."""
    hedef = tmp_path / (mutant or "kontrol")
    hedef.mkdir(parents=True, exist_ok=True)
    shutil.copytree(REPO_KOK / "src", hedef / "src")

    norm = hedef / "src" / "ocr" / "normalizer.py"
    kaynak = norm.read_text(encoding="utf-8")
    if mutant is not None:
        aranan, yerine = MUTANTLAR[mutant]
        assert kaynak.count(aranan) == 1, (
            f"{mutant}: mutasyon deseni kaynakta TEK KEZ bulunmali "
            f"({kaynak.count(aranan)} bulundu) -- `_group` yeniden yazilmis, sonda BAYATLADI"
        )
        norm.write_text(kaynak.replace(aranan, yerine), encoding="utf-8")
        assert norm.read_text(encoding="utf-8") != kaynak
    else:
        assert kaynak == (REPO_KOK / "src" / "ocr" / "normalizer.py").read_text(encoding="utf-8")

    betik = hedef / "_olcum.py"
    betik.write_text(OLCUM_BETIGI, encoding="utf-8")

    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTHONHASHSEED")}
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, str(betik)],
        cwd=str(hedef),
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        timeout=300,
    )
    assert proc.returncode == 0, f"olcum betigi patladi ({mutant}):\n{proc.stderr[-3000:]}"
    sonuc = json.loads(proc.stdout.strip().splitlines()[-1])
    assert isinstance(sonuc, dict)
    return sonuc


# ---------------------------------------------------------------------------
# KONTROL -- mutasyon YOK. Harness'in kendisi saglam mi?
# ---------------------------------------------------------------------------


def test_r5_mutant_sonda_kontrol_kosumu_temiz(tmp_path: Path) -> None:
    """Mutasyonsuz kopya: K23 ihlali SIFIR, B1 ayri, K24 kuyrugu `None`,
    K2 fixture'inda kuyruk `None` (K21: uzunluk TEK engel degil).
    Bu kosum, asagidaki mutant kosumlarinin ANLAMLI olmasinin sartidir --
    sonda kendi harness'inda yanlis pozitif URETMIYOR."""
    s = _olc(tmp_path, None)
    assert s["kosum"] == 1600
    assert s["k23_ihlal"] == 0, s["k23_ilk_ihlal"]
    assert s["b1_src"] == [[0, 1], [2], [3]], s["b1_src"]
    assert s["b1_speakers"] == ["Ada", "Ada", "Ada"], s["b1_speakers"]
    assert s["k24_src"] == [[0, 1, 2], [3]], s["k24_src"]
    assert s["k24_kuyruk_speaker"] is None
    assert s["k2_speakers"] == ["Ada", None], s["k2_speakers"]


# ---------------------------------------------------------------------------
# M1 -- mirasi bolumlemeye SIZDIRAN mutasyon K23'u GERCEKTEN kiriyor mu?
# ---------------------------------------------------------------------------


def test_r5_mutant_m1_bolumlemeye_sizinti_k23u_kiriyor(tmp_path: Path) -> None:
    """K23 SONDASI: miras `nxt`e bolumleme gecisinde uygulanip bir sonraki
    gruplama kararina GIRDI yapilirsa (tur 4'un gercek hatasi), K23
    degismezi KIRILMALI -- hem kendi ureticimde COK sayida ihlal, hem B1
    senaryosunda `(2, 3)` birlesmesi (sefin VARYANT A'si) geri gelmeli."""
    s = _olc(tmp_path, "M1_bolumlemeye_sizinti")
    assert s["k23_ihlal"] > 0, (
        "M1 mutanti K23 denetimimi KIRMADI -- denetim DISSIZ (miras acik/kapali "
        "bolumleme farki uretmeyen bir sizinti mi, yoksa ureticim bu deseni hic "
        "uretmiyor mu?)"
    )
    ilk = s["k23_ilk_ihlal"]
    assert isinstance(ilk, dict) and ilk["acik"] != ilk["kapali"]
    # sefin B1'i: VARYANT A geri geldi -- kendi etiketli replik kuyruga yapisti
    assert [2, 3] in s["b1_src"], s["b1_src"]
    assert s["b1_src"] != [[0, 1], [2], [3]]


# ---------------------------------------------------------------------------
# M2/M3 -- K24 sondasi. K23 degismezi bunlari GORMEZ (bolumleme degismez);
# gorevi K24 testlerinindir. Sonda bu is bolumunu de sabitler.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("mutant", ["M2_k24_sorgusu_kaldirildi"])
def test_r5_mutant_m2_m3_k24u_kiriyor_ama_k23u_kirmiyor(tmp_path: Path, mutant: str) -> None:
    """M2 (K21/K24/K28 ikinci sorgusu YOK) icin -- M3 TUR 6'da bu dosyadan
    KALDIRILDI (bkz. `MUTANTLAR` sozlugunun ustundeki not; olcum tur 6
    sondasinda):
      - K24'un zorunlu geometrisinde kuyruk segment YANLISLIKLA miras alir
        (`"Ada"`), yani `test_r5_k24_*` testlerim DISLI,
      - ama K23 degismezi ihlal EDILMEZ -- ikisi FARKLI hata siniflari."""
    s = _olc(tmp_path, mutant)
    assert s["k24_kuyruk_speaker"] == "Ada", (
        f"{mutant} K24 olcumumu bozmadi -- K24 testim dissiz olabilir: {s['k24_kuyruk_speaker']!r}"
    )
    assert s["k23_ihlal"] == 0, (
        f"{mutant} K23 degismezini de ihlal etti ({s['k23_ihlal']}) -- beklenmiyordu: "
        f"{s['k23_ilk_ihlal']}"
    )
    assert s["b1_src"] == [[0, 1], [2], [3]], s["b1_src"]


def test_r5_mutant_m2_k21_ayrimini_da_bozuyor(tmp_path: Path) -> None:
    """M2 ayrica K21'in KENDISINI (uzunluk TEK engel mi) kaldirdigi icin,
    esik-alti orta blok fixture'inda kuyruk segment tur 3 davranisina
    doner (`"Ada"`). Bu, `test_karar_uyumu_tur3.py::test_r3_k2_*`
    testinin TUR 5'te duzeltilen assertion'inin (bkz. o testin docstring'i)
    hangi mekanizmaya bagli oldugunu SABITLER: eski assertion tam olarak
    bu mutantla yesil kalirdi."""
    s = _olc(tmp_path, "M2_k24_sorgusu_kaldirildi")
    assert s["k2_speakers"] == ["Ada", "Ada"], s["k2_speakers"]
