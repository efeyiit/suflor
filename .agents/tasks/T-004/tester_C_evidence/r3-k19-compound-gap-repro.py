# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r"C:\Users\pc\Desktop\efe\çeviri uygulaması")

from src.contracts.models import OcrPreset, Rect, TextBlock
from src.ocr.normalizer import normalize, _Item, _group_rejection_reason
from src.ocr.presets import get_params

params = get_params(OcrPreset.DIALOGUE)
cap = params.max_group_chars
print("cap =", cap, "max_vertical_gap_ratio =", params.max_vertical_gap_ratio)

# Compound case: length ALSO exceeded AND a large geometric gap simultaneously present.
# a.text is long (near cap), b is far below (big gap) AND b.text pushes total over cap.
a = _Item(text="x" * (cap - 5), bbox=Rect(x=0, y=0, w=100, h=20), speaker="Ada", source_blocks=(0,))
huge_gap_y = 0 + 20 + int(params.max_vertical_gap_ratio * 20) + 500  # definitely exceeds gap threshold
b = _Item(text="y" * 50, bbox=Rect(x=0, y=huge_gap_y, w=100, h=20), speaker=None, source_blocks=(1,))

reason = _group_rejection_reason(a, b, params)
print("reason when BOTH length-exceeded AND HUGE gap simultaneously:", reason)
print("(K19 table says: gap -> None should remain. If 'length' wins due to check order, inheritance WRONGLY fires)")
print()

etiket = TextBlock(text="Ada:", bbox=Rect(x=0, y=-22, w=100, h=20), confidence=0.9)
b0 = TextBlock(text="x" * (cap - 5), bbox=Rect(x=0, y=0, w=100, h=20), confidence=0.9)
b1 = TextBlock(text="y" * 50, bbox=Rect(x=0, y=huge_gap_y, w=100, h=20), confidence=0.9)
out = normalize([etiket, b0, b1], OcrPreset.DIALOGUE)
for s in out:
    print(f"  speaker={s.speaker!r} len={len(s.text)} src={s.source_blocks} text[:20]={s.text[:20]!r}")
