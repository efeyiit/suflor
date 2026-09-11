"""ÖLÇÜM 5 — real_check [6a] "ilk blok bbox.y < 0" neden düşüyor? Pozitif kontrolle.

JP fixture'ında ilk satırın çokgeni görüntü-yerel y=93'te başlıyor (olcum-3 #6:
[[82,95],[229,93],[229,115],[82,116]] → min_y=93). Frame.rect.y=-50 ile
93-50=43 ≥ 0: koşul bu fixture'la SAĞLANAMAZ. Aynı motor, rect.y=-100 ile
y=-7 < 0 verir (kırpma/sıfıra sabitleme YOK) — ölçünün ateşleyebildiği gösterilir.
OCR metni yazdırılmaz.

Koşum: python .agents/tasks/T-006/evidence/olcum-5-real-check-6a-teshis.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")
KOK = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(KOK))
from src.contracts.models import Frame, OcrPreset, Rect  # noqa: E402
from src.ocr.rapid_engine import OcrLanguage, RapidOcrEngine  # noqa: E402

FIX = KOK / ".agents" / "tasks" / "T-006" / "fixtures"
img = np.array(Image.open(FIX / "dlg_JP.png").convert("RGB"))[:, :, ::-1].copy()
jp = RapidOcrEngine(language=OcrLanguage.JAPAN, threads=8, allow_download=False)

def ilk(rect: Rect):
    bl = jp.recognize(Frame(image=img, rect=rect, captured_at=0.0, seq=0), OcrPreset.DIALOGUE)
    return sorted(bl, key=lambda b: (round(b.bbox.y / 25), b.bbox.x))[0].bbox

for r in (Rect(0, 0, 1200, 400), Rect(-2600, -50, 1200, 400), Rect(-2600, -93, 1200, 400),
          Rect(-2600, -94, 1200, 400), Rect(-2600, -100, 1200, 400)):
    b = ilk(r)
    print(f"rect=({r.x:6d},{r.y:5d}) -> ilk blok bbox=({b.x:6d},{b.y:5d}) w={b.w} h={b.h}  y<0: {b.y < 0}")
print("Sonuç: görüntü-yerel ilk satır y=93; rect.y=-50 ile 43 → [6a]'nın y<0 koşulu bu fixture'da sağlanamaz;")
print("        rect.y<=-94 ile negatif oluyor → motor y'yi sıfıra sabitlemiyor (pozitif kontrol).")
