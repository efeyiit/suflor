# -*- coding: utf-8 -*-
"""TUR 5 / Tester-C probe 4: K24 tail (CJK), K23 fuzz (Tester-C KENDI
tohumu/dagilimi -- CJK agirlikli), K26 etiket dagilimi."""
from __future__ import annotations

import random
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, r"C:\Users\pc\Desktop\efe\çeviri uygulaması")

from src.contracts.models import OcrPreset, Rect, TextBlock
from src.ocr.normalizer import _group_rejection_reason, _Item, _normalize_impl, normalize
from src.ocr.presets import get_params


def blk(text, x, y, *, w=300, h=20, conf=0.9, mon=0, dpi=1.0):
    return TextBlock(text=text, bbox=Rect(x=x, y=y, w=w, h=h, monitor_index=mon,
                                          dpi_scale=dpi), confidence=conf)


# ================= K24: tail vs current, CJK govdede ====================
print("=" * 74)
print("K24 -- `tail` ile `current` (birlesik bbox) CJK govdede ayrisiyor mu?")
print("-" * 74)
P = get_params(OcrPreset.DIALOGUE)
JP = "これは非常に長い台詞であり物語の核心に触れる重要な部分である。"  # 31

# Grubun BASINDA cok ASAGI uzanan bir oge (h buyuk) -> birlesik bottom onu tasir
a1 = _Item(text=JP, bbox=Rect(x=10, y=0, w=300, h=400), speaker="勇者", source_blocks=(0,))
a2 = _Item(text=JP, bbox=Rect(x=10, y=10, w=300, h=20), speaker=None, source_blocks=(1,))
# current = a1 + a2 birlesigi: y=0, bottom=max(400, 30)=400
cur = _Item(text=a1.text + " " + a2.text,
            bbox=Rect(x=10, y=0, w=300, h=400),
            speaker="勇者", source_blocks=(0, 1))
tail = a2
# aday: tail'in (bottom=30) COK altinda ama current'in (bottom=400) USTUNDE
nxt = _Item(text=JP * 8, bbox=Rect(x=10, y=200, w=300, h=20), speaker=None, source_blocks=(2,))
print(f"  cur.bbox.bottom={cur.bbox.bottom}  tail.bbox.bottom={tail.bbox.bottom}  nxt.y={nxt.bbox.y}")
print(f"  reason(cur, nxt)                 = {_group_rejection_reason(cur, nxt, P)!r}")
print(f"  reason(cur, nxt, ignore_length=T) = {_group_rejection_reason(cur, nxt, P, ignore_length=True)!r}")
print(f"  reason(tail, nxt, ignore_length=T)= {_group_rejection_reason(tail, nxt, P, ignore_length=True)!r}")
print("  -> K24: tail GERCEK kopusu goruyor, current GIZLIYOR" )
print()

# ================= K26: alti karakter uyumluluk formu ====================
print("=" * 74)
print("K26 -- alti karakterin decomposition ETIKET dagilimi")
print("-" * 74)
alti = (0xFE15, 0xFE16, 0xFE56, 0xFE57, 0xFF01, 0xFF1F)
from collections import Counter
etiketler = []
for cp in alti:
    d = unicodedata.decomposition(chr(cp))
    tag = d.split()[0] if d.startswith("<") else "(YOK)"
    etiketler.append(tag)
    print(f"  U+{cp:04X}  decomposition={d!r:18} etiket={tag}")
print(f"  dagilim = {dict(Counter(etiketler))}")
print(f"  hepsi uyumluluk formu mu: {all(unicodedata.decomposition(chr(c)).startswith('<') for c in alti)}")
print(f"  unidata_version = {unicodedata.unidata_version}")
print()

# ================= K23 FUZZ -- Tester-C'nin KENDI tohumu ================
print("=" * 74)
print("K23 DEGISMEZ FUZZ -- Tester-C tohumu 20250910, CJK agirlikli, n=2600")
print("-" * 74)

JP_PARCA = ["これは長い台詞である。", "そして物語は続く。", "勇者は旅立った。",
            "魔王が現れた。", "村人は逃げ出した。", "剣を抜いた。"]
KR_PARCA = ["이것은 긴 대사입니다.", "그리고 이야기는 계속된다.", "용사가 떠났다."]
LAT_PARCA = ["This is a long line of text.", "and it continues here.",
             "well-known term", "value is {0} and %s here"]
ISIMLER = ["勇者", "魔王", "村人", "김철수", "이영희", "Ada", "Efe", "Пётр", "Ayşe", "ＡＢＣ"]
SEPS = ("：", ":")

rnd = random.Random(20250910)
PRESETS = (OcrPreset.DIALOGUE, OcrPreset.TOOLTIP, OcrPreset.SUBTITLE, OcrPreset.MENU)

ihlal = 0
denetlenen = 0
sifir_h = 0
etiketli = 0
for case in range(2600):
    n = rnd.randint(0, 9)
    preset = PRESETS[case % 4]
    blocks = []
    y = rnd.randint(-5, 40)
    for i in range(n):
        r = rnd.random()
        if r < 0.22:
            name = rnd.choice(ISIMLER)
            sep = rnd.choice(SEPS)
            text = f"{name}{sep}" if rnd.random() < 0.5 else f"{name}{sep}{rnd.choice(JP_PARCA)}"
            etiketli += 1
        elif r < 0.55:
            text = "".join(rnd.choice(JP_PARCA) for _ in range(rnd.randint(1, 5)))
        elif r < 0.75:
            text = "".join(rnd.choice(KR_PARCA) for _ in range(rnd.randint(1, 4)))
        else:
            text = " ".join(rnd.choice(LAT_PARCA) for _ in range(rnd.randint(1, 6)))
        # yozlasmis geometri: sifir/negatif w/h
        gr = rnd.random()
        if gr < 0.10:
            w, h = rnd.choice([(300, 0), (0, 20), (300, -5), (-10, 20)])
            sifir_h += 1
        else:
            w, h = rnd.randint(40, 400), rnd.randint(1, 60)
        blocks.append(blk(text, rnd.randint(0, 60), y, w=w, h=h,
                          conf=round(rnd.uniform(0.5, 1.0), 3)))
        y += rnd.choice([1, 5, 12, 18, 22, 60, 300, 900])
    on = _normalize_impl(blocks, preset, apply_inheritance=True)
    off = _normalize_impl(blocks, preset, apply_inheritance=False)
    denetlenen += 1
    if (len(on) != len(off)
            or [s.source_blocks for s in on] != [s.source_blocks for s in off]
            or [s.text for s in on] != [s.text for s in off]
            or [s.bbox for s in on] != [s.bbox for s in off]
            or [s.placeholders for s in on] != [s.placeholders for s in off]):
        ihlal += 1
        if ihlal <= 3:
            print(f"  IHLAL case={case} preset={preset}")
            print(f"    ON : {[(s.source_blocks, s.speaker) for s in on]}")
            print(f"    OFF: {[(s.source_blocks, s.speaker) for s in off]}")
    # miras YALNIZCA speaker'i degistirebilir: speaker DISINDA hersey ayni ise
    # ve miras acikken speaker ya AYNI ya da None'dan bir DEGERE gecmis olmali
    for so, sf in zip(on, off):
        assert so.speaker == sf.speaker or (sf.speaker is None and so.speaker is not None), \
            f"case={case}: miras bir DEGERI DEGISTIRDI/SILDI: {sf.speaker!r} -> {so.speaker!r}"

print(f"  denetlenen girdi = {denetlenen}, etiketli blok ~{etiketli}, "
      f"yozlasmis geometri ~{sifir_h}")
print(f"  K23 BOLUMLEME IHLALI = {ihlal}")
print(f"  miras YALNIZCA None -> deger yonunde degisti: dogrulandi (assert)")
print()
