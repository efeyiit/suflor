# -*- coding: utf-8 -*-
"""Tester-C, TUR 6 -- sefin adlandirdigi "EK YUZEY": sirasiz girdide
`source_blocks[-1]` YALNIZ-ETIKET blogunu gosterebilir (sef_karari-tur6.md,
"Sefin hata analizi"). K28 okuma sirasina gectigi icin bu yuzey KAPANDI MI?

Iki soru:
  (1) miras sorgusunun SOL tarafi hic yalniz-etiket blogu olabiliyor mu?
  (2) SAG tarafi olabiliyor mu?
Ve ASCII-DISI etiketle SIRASIZ girdide `[-1]` ile okuma sirasi AYRISIYOR mu
(kitin ve kor takimin uretmedigi sinif).

Kosum:  python .agents/tasks/T-004/tester_C_evidence/r6-10-etiket-blogu-sol-taraf-sonda.py
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

_KOK = Path(__file__).resolve().parents[4]
if str(_KOK) not in sys.path:
    sys.path.insert(0, str(_KOK))

import src.ocr.normalizer as N
from src.contracts.models import OcrPreset, Rect, TextBlock
from src.ocr.normalizer import _split_speaker_label, normalize
from src.ocr.presets import get_params


def blk(text, x, y, *, w=300, h=20, conf=0.9):
    return TextBlock(text=text, bbox=Rect(x=x, y=y, w=w, h=h), confidence=conf)


def basliki(s):
    print()
    print("=" * 78)
    print(s)
    print("=" * 78)


# --- KANCA: `_raw_query_pair` cagrilarini kaydet (URUN KODU DEGISMEZ) -------
KAYIT: list[tuple[tuple[int, ...], int, tuple[int, ...], int]] = []
_ORIJINAL = N._raw_query_pair


def _kancali(tail, nxt, blocks):
    sol, sag = _ORIJINAL(tail, nxt, blocks)
    sol_idx = next(i for i in tail.source_blocks if blocks[i].bbox == sol.bbox)
    sag_idx = next(i for i in nxt.source_blocks if blocks[i].bbox == sag.bbox)
    KAYIT.append((tail.source_blocks, sol_idx, nxt.source_blocks, sag_idx))
    return sol, sag


basliki("1. FUZZ -- SOL/SAG taraf hic YALNIZ-ETIKET blogu oluyor mu?")

N._raw_query_pair = _kancali
try:
    sol_etiket = sag_etiket = 0
    sol_indeks_ayrisma = 0
    toplam = 0
    for t in range(600):
        r = random.Random(31000 + t)
        n = r.randint(4, 22)
        bl = []
        y = 0
        etiket_idx: set[int] = set()
        for i in range(n):
            tur = r.random()
            if tur < 0.25:
                metin = r.choice(["勇者：", "魔王:", "Ада:", "むらびと："])
                etiket_idx.add(i)
            elif tur < 0.45:
                metin = r.choice(["勇者：", "Ада:"]) + "あ" * r.randint(20, 120)
            else:
                metin = "あ" * r.randint(20, 140)
            h = r.choice([12, 18, 20, 30])
            bl.append(blk(metin, r.choice([0, 10, 12]), y, w=r.choice([200, 300]), h=h))
            y += h + r.choice([1, 3, 8, 45])
        r.shuffle(bl)
        # yalniz-etiket bloklarinin YENI indeksleri
        yalniz_etiket = {
            i for i, b in enumerate(bl)
            if (lambda p: p[0] is not None and not p[1])(_split_speaker_label(b.text))
        }
        for preset in (OcrPreset.DIALOGUE, OcrPreset.TOOLTIP, OcrPreset.SUBTITLE):
            KAYIT.clear()
            normalize(bl, preset)
            for sol_sb, sol_idx, sag_sb, sag_idx in KAYIT:
                toplam += 1
                if sol_idx in yalniz_etiket:
                    sol_etiket += 1
                if sag_idx in yalniz_etiket:
                    sag_etiket += 1
                if sol_idx != max(sol_sb):     # `[-1]` (indeks sirasi) ile ayrisma
                    sol_indeks_ayrisma += 1
    print(f"  gozlenen miras sorgusu           : {toplam}")
    print(f"  SOL taraf yalniz-etiket blogu    : {sol_etiket}")
    print(f"  SAG taraf yalniz-etiket blogu    : {sag_etiket}")
    print(f"  SOL: okuma-sirasi-son != max(idx): {sol_indeks_ayrisma}  "
          f"(K28'in `[-1]` YASAGININ olculebilir etkisi)")
finally:
    N._raw_query_pair = _ORIJINAL


basliki("2. KURULU VAKA -- ASCII-disi yalniz-etiket, SIRASIZ, uzunluk siniri")
# Girdi indeksleri: idx0 = govde (y=25), idx1 = devam (y=50), idx2 = ETIKET (y=0)
# `source_blocks` INDEKS sirali -> tail.source_blocks = (0, 2), `[-1]` = 2 = ETIKET
# OKUMA sirasi (y,x,i)          -> etiket(y=0) ONCE, govde(y=25) SON -> son = 0
UZ = "あ" * 270
bl = [
    blk(UZ, 10, 25, w=300, h=20),        # idx0  govde   (bottom=45)
    blk("い" * 20, 10, 50, w=300, h=20),  # idx1  devam   (y=50)
    blk("勇者：", 10, 0, w=300, h=20),    # idx2  ETIKET  (bottom=20)
]
segs = normalize(bl, OcrPreset.DIALOGUE)
print(f"  cikti: {[(s.speaker, s.source_blocks, s.text[:8]) for s in segs]!r}")
print("  okuma-sirasi-son  = idx0 (govde, bottom=45) -> gap = 50-45 =  5 < 16 -> MIRAS")
print("  `[-1]` indeks-son = idx2 (etiket, bottom=20) -> gap = 50-20 = 30 > 16 -> MIRAS YOK")
print(f"  ==> gozlenen ikinci speaker = {segs[1].speaker!r} "
      f"(K28 okuma sirasi DOGRULANDI; `[-1]` uygulamasi burada AYRISIRDI)")

print()
print("  -- ayni sekil, ETIKET bloğu indeks olarak ONDE (kontrol) --")
bl2 = [
    blk("勇者：", 10, 0, w=300, h=20),
    blk(UZ, 10, 25, w=300, h=20),
    blk("い" * 20, 10, 50, w=300, h=20),
]
segs2 = normalize(bl2, OcrPreset.DIALOGUE)
print(f"  cikti: {[(s.speaker, s.source_blocks) for s in segs2]!r}")

print()
print("SONDA BITTI.")
