"""T-009 kabul kapisi -- Korece PP-OCRv5 ile noktalar ve uctan uca ceviri.

    python .agents/tasks/T-009/real_check.py

Sefe aittir. Stdout yalniz ASCII, metin basilmaz.
  1. dlg_KR: 17 blok, toplam '.' >= 3   (v4'te 0 -- pozitif kontrol)
  2. uctan uca: KR -> birlestir -> normalize -> NMT -> >= 12 kelime, uc anahtar
  3. KR OCR suresi: medyan <= 400 ms (v5 332 olculdu; v4 1099)
"""

from __future__ import annotations

import statistics
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

KOK = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(KOK))

from src.contracts.models import Frame, OcrPreset, Rect, TranslationRequest  # noqa: E402

FIX = KOK / ".agents" / "tasks" / "T-006" / "fixtures"
MODEL = KOK / "models" / "nllb-200-distilled-600M-ct2-int8"
ihlaller: list[str] = []


def ihlal(m: str) -> None:
    ihlaller.append(m); print(f"  IHLAL  {m}")


def tamam(m: str) -> None:
    print(f"  ok     {m}")


def main() -> int:
    print("T-009 real_check -- Korece v5")
    from src.ocr.normalizer import normalize
    from src.ocr.rapid_engine import OcrLanguage, RapidOcrEngine
    from src.ocr.satir_birlestirici import satirlari_birlestir
    from src.translate.local_nmt import LocalNmtProvider

    img = np.array(Image.open(FIX / "dlg_KR.png").convert("RGB"))[:, :, ::-1].copy()
    f = Frame(image=img, rect=Rect(0, 0, 1200, 400), captured_at=0.0, seq=0)
    m = RapidOcrEngine(language=OcrLanguage.KOREAN, threads=8, allow_download=False)
    bl = m.recognize(f, OcrPreset.DIALOGUE)
    nokta = sum(b.text.count(".") for b in bl)
    (tamam if len(bl) == 17 and nokta >= 3 else ihlal)(f"[1] KR {len(bl)} blok, '.' sayisi {nokta} (>= 3; v4'te 0)")

    segs = normalize(satirlari_birlestir(bl), OcrPreset.DIALOGUE)
    if (MODEL / "model.bin").exists() and segs:
        p = LocalNmtProvider(model_dir=MODEL, threads=8)
        r = p.translate(TranslationRequest(segments=tuple(segs), source_lang="kor_Hang", target_lang="tr"))
        c = " ".join(r.translations).lower().replace("ğ", "g").replace("ü", "u").replace("ş", "s")
        kelime = len(c.split())
        anahtar = ("bekliyor" in c, "dogu" in c, "gunes" in c or "gun" in c)
        (tamam if kelime >= 12 and all(anahtar) else ihlal)(
            f"[2] uctan uca: {len(segs)} segment -> {kelime} kelime, bekliyor/dogu/gunes={anahtar}  (v4: 6 kelime, yalniz bekliyor)")
        p.close()
    else:
        ihlal("[2] NMT modeli yok ya da segment yok")

    m.recognize(f, OcrPreset.DIALOGUE)
    s = []
    for _ in range(5):
        t0 = time.perf_counter(); m.recognize(f, OcrPreset.DIALOGUE); s.append((time.perf_counter() - t0) * 1000)
    med = statistics.median(s)
    (tamam if med <= 400 else ihlal)(f"[3] KR OCR medyan {med:.0f} ms (<= 400; v4 ~1099)")
    m.close()

    print()
    if ihlaller:
        print(f"REAL_CHECK: {len(ihlaller)} IHLAL"); return 1
    print("REAL_CHECK: TEMIZ"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
