# -*- coding: utf-8 -*-
"""Tester-C, TUR 6 -- OLCEK, TEK BASINA kosulur.

Sef olctu: `test_olcek_tur2_*` / `test_olcek_tur4_*` TAM TAKIM YUKU altinda
KARARSIZ (uc kosumda 1/1/0 kirik), tek basina kararli. Bu yuzden olcum
BURADA, tek basina, uc tekrarla yapilir.

Kosum:  python .agents/tasks/T-004/tester_C_evidence/r6-06-olcek-tek-basina.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

_KOK = Path(__file__).resolve().parents[4]
if str(_KOK) not in sys.path:
    sys.path.insert(0, str(_KOK))

from src.contracts.models import OcrPreset, Rect, TextBlock
from src.ocr.normalizer import normalize


def blk(text, x, y, *, w=300, h=20, conf=0.9):
    return TextBlock(text=text, bbox=Rect(x=x, y=y, w=w, h=h), confidence=conf)


def sure(blocks, preset, tekrar=5):
    en_iyi = float("inf")
    for _ in range(tekrar):
        t0 = time.perf_counter()
        normalize(blocks, preset)
        en_iyi = min(en_iyi, (time.perf_counter() - t0) * 1000.0)
    return en_iyi


def a_derlem(n):
    """TUR 2/3/4/5 ile AYNI veri sekli: `kelime{i}-`, ust uste bloklar."""
    return [blk(f"kelime{i}-", 10, i * 5, w=300, h=20) for i in range(n)]


def b_derlem(n):
    """`_group`'u GERCEKTEN yukleyen yol: CJK, hyphen'siz, her 4. blok etiketli."""
    out = []
    y = 0
    for i in range(n):
        metin = ("勇者：" if i % 4 == 0 else "") + "あ" * 30
        out.append(blk(metin, 10, y, w=300, h=20))
        y += 22
    return out


def c_derlem(n):
    """K28'in EN AGIR yolu: her sinirda COK BLOKLU tail (zincirleme hyphen)."""
    out = []
    y = 0
    for i in range(n):
        son = i % 4 == 3
        metin = ("Ada: " if i % 8 == 0 else "") + "kelime" * 12 + ("" if son else "-")
        h = 6 if i % 3 == 0 else 20
        out.append(blk(metin, 10, y, w=300, h=h))
        y += h + 2
    return out


print("=== A) TUR 2/3/4/5 ile AYNI veri sekli: `kelime{i}-`, ust uste ===")
print("    (TUR2 3.443/9.271/27.069 · TUR3 3.673/9.234/26.461 · "
      "TUR4 2.744/7.032/20.138 · TUR5 3.199/8.429/24.866)")
for k in range(1, 4):
    parcalar = []
    for n in (500, 1000, 2000):
        parcalar.append(f"n={n}: {sure(a_derlem(n), OcrPreset.DIALOGUE):7.3f} ms")
    print(f"    kosum {k}: " + "  ".join(parcalar))

print()
print("=== B) `_group`'u GERCEKTEN yukleyen yol (CJK, hyphen'siz, her 4. blok etiketli) ===")
print("    (TUR5: 3.330 / 6.420 / 13.418 ms)")
for k in range(1, 4):
    parcalar = []
    for n in (500, 1000, 2000):
        parcalar.append(f"n={n}: {sure(b_derlem(n), OcrPreset.DIALOGUE):7.3f} ms")
    print(f"    kosum {k}: " + "  ".join(parcalar))

print()
print("=== C) K28'in EN AGIR yolu: her sinirda COK BLOKLU tail (zincirleme hyphen) ===")
for n in (500, 1000, 2000, 4000):
    print(f"    n={n}: {sure(c_derlem(n), OcrPreset.DIALOGUE):8.3f} ms")
