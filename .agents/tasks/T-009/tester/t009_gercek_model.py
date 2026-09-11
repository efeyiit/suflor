"""T-009 kor tester -- GERCEK modelle dort dil (ayri surec; birim testten BAGIMSIZ).

    python .agents/tasks/T-009/tester/t009_gercek_model.py [--kok <depo_koku>]

Stdout yalniz ASCII, OCR metni basilmaz (PROTOKOL 7). Beklenen metinler sabit;
cikti yalniz karsilastirmada kullanilir.

  [G1] JAPAN  dlg_JP -> 4/4 satir birebir
  [G2] ENGLISH dlg_EN -> 4/4
  [G3] KOREAN dlg_KR -> 17 blok, '.' == 3, birlesik benzerlik >= 0.95,
       kelime dogrulugu 17/17 (bosluksuz blok metni beklenen kelime kumesinde)
  [G4] CHINESE modeli dlg_JP'de 0/4 (K2 pozitif kontrolu; CHINESE fixture yok)
  [G5] KR OCR suresi medyan (<= 400 ms; rapor)
  [G6] Gercek fabrika yolunda kutuphaneye giden `params`: enum uyeleri
       (Rec.ocr_version KOREAN -> OCRVersion.PPOCRV5, digerleri PPOCRV4;
       Det hep PPOCRV4; Rec.model_path dosya adi tabloyla ayni).
       `rapidocr.RapidOCR` sarilarak yakalanir (kutuphane cagrilmadan once).
  [G7] KOREAN'da her blok metni beklenen kelimelerden biriyle BIREBIR (nokta dahil)
"""

from __future__ import annotations

import argparse
import difflib
import statistics
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument("--kok", default=None)
ap.add_argument("--etiket", default="")
args = ap.parse_args()

KOK = Path(args.kok).resolve() if args.kok else Path(__file__).resolve().parents[4]
sys.path.insert(0, str(KOK))

from src.contracts.models import Frame, OcrPreset, Rect, TextBlock  # noqa: E402

FIX = Path(__file__).resolve().parents[2] / "T-006" / "fixtures"

BEKLENEN = {
    "JP": ["長老マルクス", "村の長老があなたを待っています。",
           "水車小屋を過ぎて東の道を行きなさい。", "日が暮れたら道を外れないように。"],
    "EN": ["ELDER MARCUS", "The village elder is waiting for you.",
           "Take the eastern road past the mill,", "and do not stray after dark."],
    "KR": ["장로 마르쿠스", "마을 장로가 당신을 기다리고 있습니다.",
           "방앗간을 지나 동쪽 길로 가십시오.", "해가 지면 길을 벗어나지 마십시오."],
}
KR_KELIMELER = [k for s in BEKLENEN["KR"] for k in s.split()]  # 17 kelime, noktalar dahil

ihlaller: list[str] = []


def ihlal(m: str) -> None:
    ihlaller.append(m); print(f"  IHLAL  {m}")


def tamam(m: str) -> None:
    print(f"  ok     {m}")


def kare(ad: str) -> Frame:
    img = np.array(Image.open(FIX / f"dlg_{ad}.png").convert("RGB"))[:, :, ::-1].copy()
    return Frame(image=img, rect=Rect(0, 0, 1200, 400), captured_at=0.0, seq=0)


def bosluksuz(s: str) -> str:
    return "".join(s.split())


def satir_esle(bl: list[TextBlock], beklenen: list[str]) -> int:
    okunan = {bosluksuz(b.text) for b in bl}
    return sum(1 for s in beklenen if bosluksuz(s) in okunan)


def okuma_sirasi(bl: list[TextBlock]) -> list[TextBlock]:
    if not bl:
        return []
    ys = sorted(bl, key=lambda b: b.bbox.y)
    satirlar: list[list[TextBlock]] = [[ys[0]]]
    for b in ys[1:]:
        if b.bbox.y - satirlar[-1][0].bbox.y > 20:
            satirlar.append([b])
        else:
            satirlar[-1].append(b)
    return [b for s in satirlar for b in sorted(s, key=lambda b: b.bbox.x)]


def main() -> int:
    print(f"T-009 tester gercek model  kok={KOK}  {args.etiket}")
    import src.ocr.rapid_engine as re_mod
    from src.ocr.rapid_engine import OcrLanguage, RapidOcrEngine

    print(f"  modul: {Path(re_mod.__file__).resolve()}")

    # [G6] gercek fabrika yolunda kutuphaneye giden params'i yakala
    import rapidocr
    from rapidocr import OCRVersion
    yakalanan: dict[str, dict[str, object]] = {}
    _Gercek = rapidocr.RapidOCR

    class _Sargi(_Gercek):  # type: ignore[misc,valid-type]
        def __init__(self, params=None, **kw):  # type: ignore[no-untyped-def]
            yakalanan[getattr(params.get("Rec.lang_type"), "value", str(params.get("Rec.lang_type")))] = dict(params)
            super().__init__(params=params, **kw)

    rapidocr.RapidOCR = _Sargi  # `_varsayilan_fabrika` `from rapidocr import RapidOCR` -> sargi

    motorlar = {d: RapidOcrEngine(language=d, threads=8, allow_download=False) for d in OcrLanguage}
    f_jp, f_en, f_kr = kare("JP"), kare("EN"), kare("KR")

    b_jp = motorlar[OcrLanguage.JAPAN].recognize(f_jp, OcrPreset.DIALOGUE)
    n = satir_esle(b_jp, BEKLENEN["JP"])
    (tamam if n == 4 else ihlal)(f"[G1] JAPAN {n}/4 ({len(b_jp)} blok)")

    b_en = motorlar[OcrLanguage.ENGLISH].recognize(f_en, OcrPreset.DIALOGUE)
    n = satir_esle(b_en, BEKLENEN["EN"])
    (tamam if n == 4 else ihlal)(f"[G2] ENGLISH {n}/4 ({len(b_en)} blok)")

    b_kr = motorlar[OcrLanguage.KOREAN].recognize(f_kr, OcrPreset.DIALOGUE)
    nokta = sum(b.text.count(".") for b in b_kr)
    o = bosluksuz("".join(b.text for b in okuma_sirasi(b_kr)))
    bz = difflib.SequenceMatcher(None, o, bosluksuz("".join(BEKLENEN["KR"]))).ratio()
    dogru_kelime = sum(1 for b in b_kr if b.text.strip() in KR_KELIMELER)
    (tamam if len(b_kr) == 17 and nokta == 3 and bz >= 0.95 else ihlal)(
        f"[G3] KOREAN {len(b_kr)} blok, '.'={nokta} (==3), benzerlik {bz:.3f} (>=0.95)")
    (tamam if dogru_kelime == 17 else ihlal)(f"[G7] KOREAN kelime dogrulugu {dogru_kelime}/17 (blok metni == beklenen kelime, nokta dahil)")
    # noktali uc blok tam olarak cumle sonlari mi
    noktali = sorted(b.text.strip() for b in b_kr if "." in b.text)
    beklenen_noktali = sorted(k for k in KR_KELIMELER if "." in k)
    (tamam if noktali == beklenen_noktali else ihlal)(f"[G3b] noktali bloklar beklenen uc cumle sonuyla birebir: {noktali == beklenen_noktali}")

    b_zh = motorlar[OcrLanguage.CHINESE].recognize(f_jp, OcrPreset.DIALOGUE)
    n = satir_esle(b_zh, BEKLENEN["JP"])
    (tamam if n < 4 else ihlal)(f"[G4] CHINESE modeli dlg_JP'de {n}/4 (4 OLMAMALI; {len(b_zh)} blok)")

    m = motorlar[OcrLanguage.KOREAN]
    m.recognize(f_kr, OcrPreset.DIALOGUE)
    s = []
    for _ in range(7):
        t0 = time.perf_counter(); m.recognize(f_kr, OcrPreset.DIALOGUE); s.append((time.perf_counter() - t0) * 1000)
    med = statistics.median(s)
    (tamam if med <= 400 else ihlal)(f"[G5] KR OCR medyan {med:.0f} ms (min {min(s):.0f}, max {max(s):.0f}; <= 400)")

    # [G6]
    beklenen_rec = {"japan": OCRVersion.PPOCRV4, "korean": OCRVersion.PPOCRV5, "ch": OCRVersion.PPOCRV4, "en": OCRVersion.PPOCRV4}
    beklenen_dosya = {"japan": "japan_PP-OCRv4_rec_mobile.onnx", "korean": "korean_PP-OCRv5_rec_mobile.onnx",
                      "ch": "ch_PP-OCRv4_rec_mobile.onnx", "en": "en_PP-OCRv4_rec_mobile.onnx"}
    ok6 = len(yakalanan) == 4
    for rec_dil, p in yakalanan.items():
        rv, dv = p.get("Rec.ocr_version"), p.get("Det.ocr_version")
        ad = Path(str(p.get("Rec.model_path"))).name
        iyi = (rv is beklenen_rec.get(rec_dil)) and (dv is OCRVersion.PPOCRV4) and ad == beklenen_dosya.get(rec_dil)
        ok6 = ok6 and iyi
        print(f"         {rec_dil:7s} Rec.ocr_version={getattr(rv, 'name', rv)} Det.ocr_version={getattr(dv, 'name', dv)} rec_dosya={ad} {'ok' if iyi else 'YANLIS'}")
    (tamam if ok6 else ihlal)(f"[G6] gercek yolda enum uyeleri + dosya adi dort dilde tabloyla ayni ({len(yakalanan)} yakalama)")

    for mm in motorlar.values():
        mm.close()
    print()
    if ihlaller:
        print(f"TESTER_GERCEK: {len(ihlaller)} IHLAL"); return 1
    print("TESTER_GERCEK: TEMIZ"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
