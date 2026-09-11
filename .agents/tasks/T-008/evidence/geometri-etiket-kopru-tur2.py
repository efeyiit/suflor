"""T-008 tur 2 -- `fixtures/etiket_kopru_KR.png` gercek OCR kutu GEOMETRISI.

Metin BASILMAZ (yalniz kutular + satir/blok sayilari). Cikti, implementer'in
test dosyasina gomulen `ETIKET_KOPRU_GEOMETRI` sabitinin bagimsiz kaynagi
(§4.6/8: referans uygulamanin ciktisindan degil, tespitciden gelir).

    python .agents/tasks/T-008/evidence/geometri-etiket-kopru-tur2.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

KOK = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(KOK))

from src.contracts.models import Frame, OcrPreset, Rect  # noqa: E402


def main() -> int:
    from src.ocr.rapid_engine import OcrLanguage, RapidOcrEngine
    from src.ocr.satir_birlestirici import satirlari_birlestir

    yol = KOK / ".agents" / "tasks" / "T-008" / "fixtures" / "etiket_kopru_KR.png"
    img = np.array(Image.open(yol).convert("RGB"))[:, :, ::-1].copy()
    frame = Frame(image=img, rect=Rect(0, 0, img.shape[1], img.shape[0]), captured_at=0.0, seq=0)
    kutular = RapidOcrEngine(language=OcrLanguage.KOREAN, threads=8).recognize(frame, OcrPreset.DIALOGUE)
    print(f"fixture: {yol.name}  boyut: {img.shape[1]}x{img.shape[0]}  kutu: {len(kutular)}")
    print("# (x, y, w, h) -- tespitci sirasi (metin yok)")
    for b in kutular:
        r = b.bbox
        print(f"    ({r.x}, {r.y}, {r.w}, {r.h}),")
    cikti = satirlari_birlestir(kutular)
    print(f"mevcut satirlari_birlestir: {len(kutular)} -> {len(cikti)} blok, parca {[len(c.line_boxes) or 1 for c in cikti]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
