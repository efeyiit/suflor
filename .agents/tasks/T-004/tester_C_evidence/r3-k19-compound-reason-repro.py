# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r"C:\Users\pc\Desktop\efe\çeviri uygulaması")

from src.contracts.models import OcrPreset, Rect, TextBlock
from src.ocr.normalizer import normalize, _Item, _group_rejection_reason
from src.ocr.presets import get_params

params = get_params(OcrPreset.DIALOGUE)
cap = params.max_group_chars
print("cap =", cap)

# Construct a pair where BOTH length is exceeded AND ref_height<=0 (degenerate).
a = _Item(text="Ada'nin sozu " + "x" * (cap - 5), bbox=Rect(x=0, y=0, w=100, h=20), speaker="Ada", source_blocks=(0,))
b = _Item(text="y" * 50, bbox=Rect(x=0, y=20, w=100, h=0), speaker=None, source_blocks=(1,))  # h=0 degenerate AND would exceed length too

reason = _group_rejection_reason(a, b, params)
print("reason when BOTH length-exceeded AND h=0 degenerate simultaneously:", reason)
print("(if 'length' -> K19 will INHERIT speaker despite geometry ALSO being broken)")
print("(if 'height' -> K19 will NOT inherit, geometry priority wins)")
print()

# confirm through full pipeline
etiket = TextBlock(text="Ada:", bbox=Rect(x=0, y=-22, w=100, h=20), confidence=0.9)
b0 = TextBlock(text="Ada'nin sozu " + "x" * (cap - 5), bbox=Rect(x=0, y=0, w=100, h=20), confidence=0.9)
b1 = TextBlock(text="y" * 50, bbox=Rect(x=0, y=20, w=100, h=0), confidence=0.9)  # degenerate h=0
out = normalize([etiket, b0, b1], OcrPreset.DIALOGUE)
for s in out:
    print(f"  speaker={s.speaker!r} len={len(s.text)} src={s.source_blocks} text[:30]={s.text[:30]!r}")
