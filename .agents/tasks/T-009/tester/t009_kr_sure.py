"""KR OCR suresi -- tek motor, ayri surec, 3 tekrar x 7 olcum (varyans kaydi)."""
from __future__ import annotations
import statistics, sys, time
from pathlib import Path
import numpy as np
from PIL import Image
KOK = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(KOK))
from src.contracts.models import Frame, OcrPreset, Rect
from src.ocr.rapid_engine import OcrLanguage, RapidOcrEngine
FIX = KOK / ".agents/tasks/T-006/fixtures"
img = np.array(Image.open(FIX / "dlg_KR.png").convert("RGB"))[:, :, ::-1].copy()
f = Frame(image=img, rect=Rect(0, 0, 1200, 400), captured_at=0.0, seq=0)
m = RapidOcrEngine(language=OcrLanguage.KOREAN, threads=8, allow_download=False)
m.recognize(f, OcrPreset.DIALOGUE); m.recognize(f, OcrPreset.DIALOGUE)
for tekrar in range(3):
    s = []
    for _ in range(7):
        t0 = time.perf_counter(); bl = m.recognize(f, OcrPreset.DIALOGUE); s.append((time.perf_counter() - t0) * 1000)
    print(f"tekrar {tekrar}: medyan {statistics.median(s):.0f} ms  min {min(s):.0f}  max {max(s):.0f}  ({len(bl)} kutu)")
m.close()
