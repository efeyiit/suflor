# -*- coding: utf-8 -*-
"""TUR 5 / Tester-C probe 3: cap'i GERCEKTEN asan JP senaryolari."""
from __future__ import annotations

import sys
sys.path.insert(0, r"C:\Users\pc\Desktop\efe\çeviri uygulaması")

from src.contracts.models import OcrPreset, Rect, TextBlock
from src.ocr.normalizer import _normalize_impl, normalize
from src.ocr.presets import get_params


def blk(text, x, y, *, w=300, h=20, conf=0.9):
    return TextBlock(text=text, bbox=Rect(x=x, y=y, w=w, h=h), confidence=conf)


def dump(title, blocks, preset=OcrPreset.DIALOGUE):
    print("=" * 74)
    print(title)
    print("-" * 74)
    for i, b in enumerate(blocks):
        print(f"  b{i}: y={b.bbox.y:5d} len={len(b.text):3d} {b.text[:34]!r}")
    for flag in (True, False):
        out = _normalize_impl(blocks, preset, apply_inheritance=flag)
        print(f"  --- apply_inheritance={flag} -> {len(out)} segment")
        for s in out:
            print(f"      speaker={s.speaker!r:10} src={s.source_blocks} len={len(s.text)}")
    a = _normalize_impl(blocks, preset, apply_inheritance=True)
    b = _normalize_impl(blocks, preset, apply_inheritance=False)
    same = ([s.source_blocks for s in a] == [s.source_blocks for s in b]
            and [s.text for s in a] == [s.text for s in b]
            and [s.bbox for s in a] == [s.bbox for s in b]
            and [s.placeholders for s in a] == [s.placeholders for s in b]
            and len(a) == len(b))
    print(f"  K23 BIREBIR (src+text+bbox+ph+sayi): {same}")
    print()


CAP = get_params(OcrPreset.DIALOGUE).max_group_chars
JP = "これは非常に長い台詞であり物語の核心に触れる重要な部分である。"  # 31
N = 10  # 10 x 31 + bosluklar = 319 > 280 -> KESIN boluner
print(f"cap={CAP}  govde blok sayisi={N}  toplam~{N*len(JP)+N-1}")
print()

body = [blk(JP, 10, 22 + 22 * i) for i in range(N)]
ylast = 22 + 22 * N

# S12: cap ASILIYOR, son blok KENDI 勇者： etiketiyle -> AYRI kalmali mi?
dump("S12 -- cap ASILIYOR; son blok KENDI 勇者： etiketli (B1'in JP yuzeyi)",
     [blk("勇者：", 10, 0)] + body + [blk("勇者：これは全く新しい台詞です。", 10, ylast)])

# S13: ayni, son blok ETIKETSIZ -> miras BEKLENIR
dump("S13 -- cap ASILIYOR; son blok ETIKETSIZ -> MIRAS beklenir",
     [blk("勇者：", 10, 0)] + body + [blk("これは未ラベルの続き行です。", 10, ylast)])

# S14: ayni, son blok FARKLI etiketli -> ASLA birlesmez, miras YOK
dump("S14 -- cap ASILIYOR; son blok 魔王： etiketli -> miras YOK",
     [blk("勇者：", 10, 0)] + body + [blk("魔王：愚かな人間よ。", 10, ylast)])

# S15: UC konusmaculu zincir, HER BIRI cap'i asacak kadar COK SATIRLI
blocks = []
y = 0
for name in ("勇者", "魔王", "村人"):
    blocks.append(blk(f"{name}：", 10, y)); y += 22
    for _ in range(N):
        blocks.append(blk(JP, 10, y)); y += 22
dump("S15 -- UC konusmaculu zincir, HER BIRI cap'i ASIYOR (ic uzunluk bolunmesi)",
     blocks)

# S16: C1 iddiasi -- iki AYRI kendi-etiketli replik, cap ASILMIYOR
dump("S16 -- iki AYRI 勇者： etiketli KISA replik (K15 satir-1 X/X)",
     [blk("勇者：こんにちは、村人さん。", 10, 0),
      blk("勇者：今日はいい天気ですね。", 10, 22)])

# S17: ayni ama GEOMETRIK olarak AYRI kutularda (gercek oyun senaryosu)
dump("S17 -- iki AYRI 勇者： replik, GERCEK dikey bosluk (ayri diyalog kutulari)",
     [blk("勇者：こんにちは、村人さん。", 10, 0),
      blk("勇者：今日はいい天気ですね。", 10, 400)])

# S18: menu on ayarinda ayni girdi (K27 kapsam disi)
dump("S18 -- S13 girdisi MENU on ayariyla (K27: _group HIC cagirilmaz)",
     [blk("勇者：", 10, 0)] + body[:3] + [blk("これは未ラベルの続き行です。", 10, 88)],
     OcrPreset.MENU)
