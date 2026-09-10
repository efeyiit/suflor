# -*- coding: utf-8 -*-
"""Tester-C, TUR 6 -- K32'nin KAPSAM olcumu.

Soru: K32 "NFD adlar konusmaci sayilmaz" diyor ve cozumu T-006'nin NFC
uretmesine bagliyor. NFC ureten bir motor bu sinifi GERCEKTEN kapatir mi?

Olculen: adin NFC-normal OLUP OLMADIGI, NFC ile NFD'nin AYNI olup olmadigi,
ve ad suzgecinin NFC bicimini kabul edip etmedigi.

Kosum:  python .agents/tasks/T-004/tester_C_evidence/r6-11-nfc-yetmez-taramasi.py
"""
from __future__ import annotations

import sys
import unicodedata as u
from pathlib import Path

_KOK = Path(__file__).resolve().parents[4]
if str(_KOK) not in sys.path:
    sys.path.insert(0, str(_KOK))

from src.ocr.normalizer import _split_speaker_label

ORNEKLER = [
    ("devanagari राम", "राम"),
    ("devanagari नमस्ते", "नमस्ते"),
    ("tayca สวัสดี", "สวัสดี"),
    ("arapca+hareke مَرحبا", "مَرحبا"),
    ("ibranice+nikud שָלוֹם", "שָלוֹם"),
    ("korece 용사", "용사"),
    ("japonca 勇者", "勇者"),
    ("vietnamca Đức", "Đức"),
]

print(f"{'ad':28s} {'NFC-normal?':12s} {'NFC==NFD?':10s} {'NFC ile taniniyor?'}")
for ad, s in ORNEKLER:
    nfc = u.normalize("NFC", s)
    taniniyor = _split_speaker_label(nfc + ": x")[0] is not None
    print(
        f"{ad:28s} {str(u.is_normalized('NFC', s)):12s} "
        f"{str(nfc == u.normalize('NFD', s)):10s} {str(taniniyor):6s}  "
        f"NFC cp={len(nfc)} NFD cp={len(u.normalize('NFD', s))}"
    )

print()
print("KOMBINE ISARETLERIN kategorileri (neden `isalpha()` reddediyor):")
for ad, ornek in (
    ("devanagari virama U+094D", "्"),
    ("devanagari matra AA U+093E", "ा"),
    ("devanagari e-matra U+0947", "े"),
    ("tayca sara-i U+0E34", "ิ"),
    ("arapca fatha U+064E", "َ"),
    ("ibranice kamats U+05B8", "ָ"),
    ("birlesen akut U+0301", "́"),
    ("RTL isareti U+200F", "‏"),
    ("LTR isareti U+200E", "‎"),
):
    print(f"  {ad:30s} kategori={u.category(ornek)} isalpha={ornek.isalpha()}")
