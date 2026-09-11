"""Ayna sondasi -- verilen depo kokundeki `src.ocr.rapid_engine` ile GERCEK model, dort dil.

    python t009_ayna_sonda.py --kok <ayna_koku> --etiket M1

Her dil icin: istisna sinifi (varsa) ya da (blok, '.' sayisi, birebir satir).
KR icin ayrica kelime dogrulugu 17/17 ve OCR medyan suresi. Metin basilmaz.
"""
from __future__ import annotations

import argparse
import statistics
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument("--kok", required=True)
ap.add_argument("--etiket", default="")
args = ap.parse_args()
KOK = Path(args.kok).resolve()
sys.path.insert(0, str(KOK))

from src.contracts.models import Frame, OcrPreset, Rect  # noqa: E402

GERCEK = Path(__file__).resolve().parents[4]
FIX = GERCEK / ".agents" / "tasks" / "T-006" / "fixtures"
BEKLENEN = {
    "JP": ["長老マルクス", "村の長老があなたを待っています。",
           "水車小屋を過ぎて東の道を行きなさい。", "日が暮れたら道を外れないように。"],
    "EN": ["ELDER MARCUS", "The village elder is waiting for you.",
           "Take the eastern road past the mill,", "and do not stray after dark."],
    "KR": ["장로 마르쿠스", "마을 장로가 당신을 기다리고 있습니다.",
           "방앗간을 지나 동쪽 길로 가십시오.", "해가 지면 길을 벗어나지 마십시오."],
}
KR_KELIMELER = [k for s in BEKLENEN["KR"] for k in s.split()]


def bosluksuz(s: str) -> str:
    return "".join(s.split())


def kare(ad: str) -> Frame:
    img = np.array(Image.open(FIX / f"dlg_{ad}.png").convert("RGB"))[:, :, ::-1].copy()
    return Frame(image=img, rect=Rect(0, 0, 1200, 400), captured_at=0.0, seq=0)


def main() -> int:
    import src.ocr.rapid_engine as re_mod
    from src.ocr.rapid_engine import OcrLanguage, RapidOcrEngine

    yol = Path(re_mod.__file__).resolve()
    ayna_mi = KOK in yol.parents
    print(f"[{args.etiket}] modul={yol}  ayna_icinde={ayna_mi}")
    if not ayna_mi:
        print("  HATA: modul aynadan yuklenmedi"); return 2

    import rapidocr
    from rapidocr import OCRVersion  # noqa: F401
    yakalanan: dict[str, dict[str, object]] = {}
    _G = rapidocr.RapidOCR

    class _S(_G):  # type: ignore[misc,valid-type]
        def __init__(self, params=None, **kw):  # type: ignore[no-untyped-def]
            yakalanan[getattr(params.get("Rec.lang_type"), "value", "?")] = dict(params)
            super().__init__(params=params, **kw)

    rapidocr.RapidOCR = _S

    for ad, dil, fx in (("JAPAN", OcrLanguage.JAPAN, "JP"), ("ENGLISH", OcrLanguage.ENGLISH, "EN"),
                        ("KOREAN", OcrLanguage.KOREAN, "KR"), ("CHINESE", OcrLanguage.CHINESE, "JP")):
        m = RapidOcrEngine(language=dil, threads=8, allow_download=False)
        f = kare(fx)
        try:
            bl = m.recognize(f, OcrPreset.DIALOGUE)
        except Exception as e:  # noqa: BLE001
            neden = type(e.__cause__).__name__ if e.__cause__ is not None else "-"
            print(f"  {ad:8s} ISTISNA {type(e).__name__} (cause {neden}): {str(e)[:110]}")
            continue
        okunan = {bosluksuz(b.text) for b in bl}
        birebir = sum(1 for s in BEKLENEN[fx] if bosluksuz(s) in okunan)
        nokta = sum(b.text.count(".") for b in bl)
        satir = f"  {ad:8s} {len(bl):2d} blok  '.'={nokta}  birebir {birebir}/4 (fixture {fx})"
        p = yakalanan.get(dil.value if dil is not OcrLanguage.CHINESE else "ch") or yakalanan.get(
            {"japan": "japan", "korean": "korean", "english": "en", "chinese": "ch"}[dil.value], {})
        rv, dv = p.get("Rec.ocr_version"), p.get("Det.ocr_version")
        satir += f"  rec={getattr(rv, 'name', rv)} det={getattr(dv, 'name', dv)}"
        satir += f"  rec_dosya={Path(str(p.get('Rec.model_path'))).name} det_dosya={Path(str(p.get('Det.model_path'))).name}"
        if ad == "KOREAN":
            dogru = sum(1 for b in bl if b.text.strip() in KR_KELIMELER)
            s = []
            for _ in range(5):
                t0 = time.perf_counter(); m.recognize(f, OcrPreset.DIALOGUE); s.append((time.perf_counter() - t0) * 1000)
            satir += f"  kelime {dogru}/17  medyan {statistics.median(s):.0f} ms"
        print(satir)
        m.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
