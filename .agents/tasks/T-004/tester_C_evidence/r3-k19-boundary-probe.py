# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, r"C:\Users\pc\Desktop\efe\çeviri uygulaması")

from src.contracts.models import OcrPreset, Rect, TextBlock
from src.ocr.normalizer import normalize
from src.ocr.presets import get_params


def blk(text, x, y, *, w=300, h=20, confidence=0.9, monitor_index=0, dpi_scale=1.0):
    return TextBlock(
        text=text,
        bbox=Rect(x=x, y=y, w=w, h=h, monitor_index=monitor_index, dpi_scale=dpi_scale),
        confidence=confidence,
    )


def show(label, out):
    print(f"--- {label} ---")
    for s in out:
        print(f"  speaker={s.speaker!r:8} len={len(s.text):4} src={s.source_blocks} text[:40]={s.text[:40]!r}")
    print(f"  num groups: {len(out)}")
    print()


print("=" * 70)
print("TEST 1: 3+ way split, ALL via length only (tight geometry)")
print("=" * 70)
cap = get_params(OcrPreset.DIALOGUE).max_group_chars
print("max_group_chars(dialogue) =", cap)
etiket = blk("Ada:", 10, 0)
govde_metni = "x" * 60
n = (cap // 60) * 2 + 5  # should force >= 2 length-splits -> >= 3 groups
govde = [blk(govde_metni, 10, 22 * (i + 1)) for i in range(n)]
out = normalize([etiket, *govde], OcrPreset.DIALOGUE)
show("3-way length-only split", out)
print("ALL speakers == 'Ada'?", all(s.speaker == "Ada" for s in out))
print()

print("=" * 70)
print("TEST 2: length split first, THEN geometric split -- chain should BREAK")
print("=" * 70)
params = get_params(OcrPreset.DIALOGUE)
etiket = blk("Ada:", 10, 0)
# body1 long enough that etiket+body1 already near cap so body1+body2 triggers length split
long_body = "y" * (cap - 10)
b1 = blk(long_body, 10, 22, h=20)
b2 = blk("kisa govde parcasi", 10, 44, h=20)  # this pushes over cap -> length split; b2 should inherit Ada
gap_y = 44 + 20 + int(params.max_vertical_gap_ratio * 20) + 200
b3 = blk("uzak parca - buyuk bosluk sonrasi", 10, gap_y, h=20)  # geometric split from b2 -> should NOT inherit further(stays as b2's inherited value... wait check)
out2 = normalize([etiket, b1, b2, b3], OcrPreset.DIALOGUE)
show("length-then-geometric", out2)

print("=" * 70)
print("TEST 3: geometric split first (X/None over gap), THEN internal length split in group2")
print("=" * 70)
etiket = blk("Ada:", 10, 0)
b1 = blk("kisa ilk parca", 10, 22, h=20)
gap_y = 22 + 20 + int(params.max_vertical_gap_ratio * 20) + 200
# group2 starts unlabeled (own speaker None) after geometric split, then itself grows past cap
long_chunks = [blk("z" * 60, 10, gap_y + 22 * i, h=20) for i in range((cap // 60) * 2 + 5)]
out3 = normalize([etiket, b1, *long_chunks], OcrPreset.DIALOGUE)
show("geometric-then-internal-length", out3)
print("Expect: first seg speaker=Ada; ALL subsequent segs speaker=None (no info to inherit)")
print()

print("=" * 70)
print("TEST 4: two different speakers (Ada, Efe), Efe's body has its OWN internal length split")
print("=" * 70)
etiket_ada = blk("Ada:", 10, 0)
govde_ada = blk("Ada govdesi kisa", 10, 22, h=20)
etiket_efe = blk("Efe:", 10, 44, h=20)
n2 = (cap // 60) * 2 + 5
govde_efe = [blk("q" * 60, 10, 66 + 22 * i, h=20) for i in range(n2)]
out4 = normalize([etiket_ada, govde_ada, etiket_efe, *govde_efe], OcrPreset.DIALOGUE)
show("two-speakers-with-internal-split", out4)
print("Expect: seg0 speaker=Ada; all remaining segs speaker=Efe (never leaks back to Ada)")
print()

print("=" * 70)
print("TEST 5: Japanese text, real sentence content (not repeated char), TOOLTIP preset (smaller cap)")
print("=" * 70)
cap_tt = get_params(OcrPreset.TOOLTIP).max_group_chars
print("max_group_chars(tooltip) =", cap_tt)
etiket_jp = blk("勇者:", 10, 0)
sentences = [
    "こんにちは、世界。今日はいい天気ですね。",
    "魔王を倒すために、私たちは旅を続けなければならない。",
    "この剣は伝説の武器であり、多くの勇者がこれを求めてきた。",
    "東京から遠く離れたこの土地で、私たちは新たな仲間と出会った。",
    "力を合わせれば、どんな困難も乗り越えられるだろう。",
    "火の国の王は、古の言い伝えを信じていなかった。",
]
govde_jp = [blk(s, 10, 22 * (i + 1), h=20) for i, s in enumerate(sentences)]
total_len = sum(len(s) for s in sentences)
print(f"total content length (codepoints) = {total_len}, vs cap={cap_tt}")
out5 = normalize([etiket_jp, *govde_jp], OcrPreset.TOOLTIP)
show("japanese-real-sentences-tooltip", out5)
print("ALL speakers == '勇者'?", all(s.speaker == "勇者" for s in out5))
print()

print("=" * 70)
print("TEST 6: consistency check -- _should_group vs _group_rejection_reason on inherited item")
print("=" * 70)
from src.ocr.normalizer import _Item, _should_group, _group_rejection_reason
a = _Item(text="a"*50, bbox=Rect(x=0,y=0,w=100,h=20), speaker="Ada", source_blocks=(0,))
b = _Item(text="b"*50, bbox=Rect(x=0,y=20,w=100,h=20), speaker=None, source_blocks=(1,))
params_d = get_params(OcrPreset.DIALOGUE)
print("reason:", _group_rejection_reason(a,b,params_d), "should_group:", _should_group(a,b,params_d))
