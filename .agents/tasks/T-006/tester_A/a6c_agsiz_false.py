"""D12: allow_download=False + ag KAPALI (requests.get yamali) -> dort dil kurulur mu? (cls sha denetimi yerel mi)"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np, requests
from PIL import Image
KOK = Path(__file__).resolve().parents[4]; sys.path.insert(0, str(KOK)); sys.stdout.reconfigure(encoding="utf-8")
from src.contracts.models import Frame, OcrPreset, Rect
from src.ocr.rapid_engine import OcrLanguage, RapidOcrEngine
FIX = KOK / ".agents/tasks/T-006/fixtures"
def _kapali(*a, **k): raise requests.ConnectionError("tester-A: ag kapali")
requests.get = _kapali
img = np.array(Image.open(FIX / "dlg_JP.png").convert("RGB"))[:, :, ::-1].copy()
for dil in OcrLanguage:
    m = RapidOcrEngine(language=dil, threads=8, allow_download=False)
    try:
        bl = m.recognize(Frame(image=img, rect=Rect(0,0,1200,400), captured_at=0.0, seq=0), OcrPreset.DIALOGUE)
        print(f"D12 {dil.value} allow_download=False ag KAPALI: kuruldu, {len(bl)} blok (ag gerekmedi)")
    except Exception as e:
        print(f"D12 {dil.value}: {type(e).__name__} cause={type(e.__cause__).__name__}")
