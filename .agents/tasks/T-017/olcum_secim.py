"""T-017 olcum 1 -- gercek OCR bloklarinda `normalize` (eski yol) vs `secimi_birlestir` (yeni yol) segment sayisi.

    python .agents/tasks/T-017/olcum_secim.py

Stdout ASCII. Beklenti (kullanici sikayetini yeniden uretir): eski yol >= 3 parca, yeni yol 1 govde (+1 konusmaci).
"""
from __future__ import annotations

import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(KOK)); sys.path.insert(0, str(Path(__file__).resolve().parent))

from fixture import METIN, sentetik_kare  # noqa: E402
import difflib  # noqa: E402

from src.contracts.models import OcrPreset  # noqa: E402
from src.ocr.normalizer import normalize  # noqa: E402
from src.ocr.rapid_engine import OcrLanguage, RapidOcrEngine  # noqa: E402
from src.ocr.satir_birlestirici import satirlari_birlestir  # noqa: E402
from src.pipeline.anlik import ikinci_gecis  # noqa: E402
from src.pipeline.secim import secimi_birlestir  # noqa: E402


def main() -> int:
    for dil, ocr_dil in (("KR", "korean"), ("JP", "japan")):
      ocr = RapidOcrEngine(language=OcrLanguage(ocr_dil), threads=8, allow_download=True)
      for adim in (2.0, 2.4, 2.8):
        print(f"--- {dil} satir adimi {adim} x punto")
        kare, _, govde = sentetik_kare(dil, 2560, 1440, adim_orani=adim)
        bloklar = list(satirlari_birlestir(ocr.recognize(kare, OcrPreset.DIALOGUE)))
        secim = [b for b in bloklar if b.bbox.y >= govde.y - 10 and b.bbox.y + b.bbox.h <= govde.y + govde.h + 10]
        siki = ikinci_gecis(ocr, kare, secim, OcrPreset.DIALOGUE)
        eski = normalize(siki, OcrPreset.DIALOGUE)
        yeni = secimi_birlestir(siki)
        hs = [b.bbox.h for b in siki]
        bosluklar = [siki[i + 1].bbox.y - (siki[i].bbox.y + siki[i].bbox.h) for i in range(len(siki) - 1)] if len(siki) > 1 else []
        print(f"[{dil}] tam kare {len(bloklar)} satir; govde secimi {len(secim)} satir; ikinci gecis {len(siki)} satir; "
              f"h={hs} bosluk={bosluklar}")
        print(f"[{dil}] ESKI normalize: {len(eski)} segment, uzunluklar {[len(s.text) for s in eski]}")
        print(f"[{dil}] YENI secimi_birlestir: {len(yeni)} segment, uzunluklar {[len(s.text) for s in yeni]}")
        print(f"[{dil}] yeni metin tum satirlari iceriyor: {all(b.text.strip() in ' '.join(s.text for s in yeni) for b in siki)}")
        beklenen = (" " if dil == "KR" else "").join(METIN[dil][1])
        oran = difflib.SequenceMatcher(None, " ".join(s.text for s in yeni), beklenen).ratio()
        print(f"[{dil}] yeni metin ~ beklenen govde (sira dahil) benzerlik {oran:.3f} (> 0.9 = sira dogru)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
