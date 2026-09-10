# -*- coding: utf-8 -*-
"""TUR 5 / Tester-C probe 2: cap GERCEKTEN asilan JP senaryosu + miras
Unicode birebirligi + karisik script + K24 tail + kotu kullanim yuzeyi."""
from __future__ import annotations

import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, r"C:\Users\pc\Desktop\efe\çeviri uygulaması")

import src.ocr.normalizer as N
from src.contracts.models import OcrPreset, Rect, TextBlock
from src.ocr.normalizer import _group_rejection_reason, _Item, _normalize_impl, normalize
from src.ocr.presets import get_params


def blk(text, x, y, *, w=300, h=20, conf=0.9):
    return TextBlock(text=text, bbox=Rect(x=x, y=y, w=w, h=h), confidence=conf)


def dump(title, blocks, preset=OcrPreset.DIALOGUE):
    print("=" * 74)
    print(title)
    print("-" * 74)
    for i, b in enumerate(blocks):
        print(f"  b{i}: y={b.bbox.y:5d} len={len(b.text):3d} {b.text[:40]!r}")
    for flag in (True, False):
        out = _normalize_impl(blocks, preset, apply_inheritance=flag)
        print(f"  --- apply_inheritance={flag} -> {len(out)} segment")
        for s in out:
            print(f"      speaker={s.speaker!r:10} src={s.source_blocks} len={len(s.text)} text={s.text[:46]!r}")
    a = _normalize_impl(blocks, preset, apply_inheritance=True)
    b = _normalize_impl(blocks, preset, apply_inheritance=False)
    same = ([s.source_blocks for s in a] == [s.source_blocks for s in b]
            and [s.text for s in a] == [s.text for s in b]
            and [s.bbox for s in a] == [s.bbox for s in b]
            and [s.placeholders for s in a] == [s.placeholders for s in b])
    print(f"  K23 (bolumleme+text+bbox+placeholders) BIREBIR: {same}")
    print()


CAP = get_params(OcrPreset.DIALOGUE).max_group_chars  # 280
JP = "これは非常に長い台詞であり物語の核心に触れる重要な部分である。"  # 30 kar

# ---- S4: cap GERCEKTEN asiliyor + ucuncu blok KENDI 勇者： etiketiyle ----
gov = [JP] * 5   # 5 x 30 = 150 ... birlesince cap'i asacak
blocks = [blk("勇者：", 10, 0)] + [blk(t, 10, 22 + 22 * i) for i, t in enumerate(gov)]
blocks.append(blk("勇者：これは全く新しい台詞です。", 10, 22 + 22 * len(gov)))
dump(f"S4 -- JP cap={CAP} GERCEKTEN asiliyor; son blok KENDI 勇者： etiketli", blocks)

# ---- S5: ayni ama son blok ETIKETSIZ (miras adayi) --------------------
blocks2 = [blk("勇者：", 10, 0)] + [blk(t, 10, 22 + 22 * i) for i, t in enumerate(gov)]
blocks2.append(blk("これは未ラベルの続き行です。", 10, 22 + 22 * len(gov)))
dump("S5 -- ayni ama son blok ETIKETSIZ (miras BEKLENIR)", blocks2)

# ---- S6: son blok FARKLI konusmaci etiketli ---------------------------
blocks3 = [blk("勇者：", 10, 0)] + [blk(t, 10, 22 + 22 * i) for i, t in enumerate(gov)]
blocks3.append(blk("魔王：愚かな人間よ。", 10, 22 + 22 * len(gov)))
dump("S6 -- son blok FARKLI (魔王：) etiketli -> ASLA birlesmemeli", blocks3)

# ---- MIRAS UNICODE BIREBIRLIGI ---------------------------------------
print("=" * 74)
print("S7 -- MIRAS ALINAN speaker Unicode BIREBIR mi? (fullwidth ： ayrac)")
print("-" * 74)
adaylar = [
    ("勇者", "："),          # kanji + fullwidth
    ("魔王", ":"),            # kanji + ascii
    ("김철수", "："),         # hangul + fullwidth
    ("Пётр", "："),           # kiril + fullwidth (kombine yok, precomposed ё)
    ("Ayşe", ":"),            # turkce
    ("María", "："),          # aksanli latin (precomposed)
    ("Mari\u0301a", ":"),     # KOMBINE aksan (NFD) -- normalizasyon sizarsa gorunur
    ("ｱｲｳ", ":"),             # halfwidth katakana -- NFKC uygulanirsa DEGISIR
    ("ＡＢＣ", ":"),          # fullwidth latin -- NFKC uygulanirsa ASCII olur
    ("あい", "："),           # hiragana
]
for name, sep in adaylar:
    bs = [
        blk(f"{name}{sep}", 10, 0),
        blk("一行目の本文です。", 10, 22),
        blk("二行目の未ラベル本文です。", 10, 44),
    ]
    out = normalize(bs, OcrPreset.DIALOGUE)
    got = out[0].speaker
    ok = got == name
    nfkc = unicodedata.normalize("NFKC", name)
    print(f"  isim={name!r:16} sep={sep!r} -> speaker={got!r:16} BIREBIR={ok} "
          f"cp_in={[hex(ord(c)) for c in name]} cp_out={[hex(ord(c)) for c in (got or '')]}"
          f"{'  <== NFKC farkli: ' + repr(nfkc) if nfkc != name else ''}")
print()

# ---- MIRAS ZINCIRI: miras alinan deger de BIREBIR mi? ------------------
print("=" * 74)
print("S8 -- UZUNLUK bolunmesinde MIRAS alinan speaker Unicode BIREBIR mi?")
print("-" * 74)
for name, sep in (("勇者", "："), ("김철수", "："), ("ＡＢＣ", ":")):
    bs = [blk(f"{name}{sep}", 10, 0)] + [blk(t, 10, 22 + 22 * i) for i, t in enumerate([JP] * 12)]
    out = normalize(bs, OcrPreset.DIALOGUE)
    print(f"  isim={name!r:10} -> {len(out)} segment, speakerlar={[s.speaker for s in out]}")
    for s in out:
        assert s.speaker is None or s.speaker == name, (s.speaker, name)
    print(f"      hepsi BIREBIR: {all(s.speaker == name for s in out)}  "
          f"cp={[[hex(ord(c)) for c in (s.speaker or '')] for s in out]}")
print()

# ---- BOSLUK ARTIGI: etiket ile ayrac arasinda bosluk -------------------
print("=" * 74)
print("S9 -- BOSLUK ARTIGI: '勇者 ： ' / '  勇者：  ' gibi bicimler")
print("-" * 74)
for raw in ("勇者：", "勇者 ：", " 勇者： ", "勇者　：", "勇者：　", "勇 者："):
    bs = [blk(raw, 10, 0), blk("本文です。", 10, 22), blk("未ラベル続き。", 10, 44)]
    out = normalize(bs, OcrPreset.DIALOGUE)
    print(f"  ham={raw!r:12} -> speaker={out[0].speaker!r:12} "
          f"cp={[hex(ord(c)) for c in (out[0].speaker or '')]}  seg={len(out)}")
print()

# ---- KARISIK SCRIPT ZINCIRI -------------------------------------------
print("=" * 74)
print("S10 -- KARISIK SCRIPT: JP etiket + Latin govde / KR etiket + JP govde")
print("-" * 74)
mix = [
    ("勇者：", ["This is the first line of an English body.",
                "and this is the unlabeled continuation line."]),
    ("김철수：", ["これは日本語の本文です。", "これは未ラベルの続きです。"]),
    ("Hero：", ["日本語とEnglishが混ざったmixed本文。", "続きのmixed行です。"]),
]
for label, bodies in mix:
    bs = [blk(label, 10, 0)] + [blk(t, 10, 22 + 22 * i) for i, t in enumerate(bodies)]
    out = normalize(bs, OcrPreset.DIALOGUE)
    print(f"  {label!r:10} -> {len(out)} seg  speakerlar={[s.speaker for s in out]}")
    for s in out:
        print(f"      text={s.text!r}")
print()

# ---- KOTU KULLANIM YUZEYI ----------------------------------------------
print("=" * 74)
print("S11 -- KOTU KULLANIM: _normalize_impl genel API'ye sizmis mi?")
print("-" * 74)
print(f"  normalizer.__all__ = {N.__all__!r}")
print(f"  '_normalize_impl' in __all__ : {'_normalize_impl' in N.__all__}")
print(f"  '_group' in __all__          : {'_group' in N.__all__}")
import inspect
print(f"  normalize imzasi   : {inspect.signature(N.normalize)}")
print(f"  _normalize_impl im.: {inspect.signature(N._normalize_impl)}")
d = N._normalize_impl.__doc__ or ""
for kelime in ("SADECE", "MAKINE DENETIMI", "test", "uretim", "URETIM", "sizmaz", "SIZMAZ", "ACMAZ"):
    print(f"  docstring'de {kelime!r:18}: {kelime in d}")
print(f"  '_' ile baslayan (PEP8 private) mi: {N._normalize_impl.__name__.startswith('_')}")
print()
