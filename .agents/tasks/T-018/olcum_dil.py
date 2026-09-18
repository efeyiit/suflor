"""T-018 olcum 1 -- dil algilama sinyali: 4 tanima modeli x 4 dil paneli (gercek RapidOCR).

    python .agents/tasks/T-018/olcum_dil.py

Soru: hangi olcut dogru dili ayirt eder? T-006 olgusu O2: `ch` modeli Japonca'da 0.90 guvenle YANLIS metin
uretir -> guven tek basina yetmez. Aday sinyaller: ortalama guven, karakter sayisi, ciktinin yazi sistemi
dagilimi (Hangul / kana / Han / Latin), ve bunlarin carpimi. Ayrica maliyet: tam kare x4 vs kirpik x4.
Stdout ASCII.
"""
from __future__ import annotations

import statistics
import sys
import time
import unicodedata
from pathlib import Path

KOK = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(KOK)); sys.path.insert(0, str(KOK / ".agents/tasks/T-017"))

import numpy as np  # noqa: E402
from fixture import sentetik_kare  # noqa: E402

from src.contracts.models import Frame, OcrPreset, Rect, TextBlock  # noqa: E402
from src.ocr.rapid_engine import OcrLanguage, RapidOcrEngine  # noqa: E402

DILLER = [("KR", OcrLanguage.KOREAN), ("JP", OcrLanguage.JAPAN), ("ZH", OcrLanguage.CHINESE), ("EN", OcrLanguage.ENGLISH)]


def yazi_sistemi(ch: str) -> str:
    if ch.isspace() or not ch.isalpha():
        return "-"
    ad = unicodedata.name(ch, "")
    if ad.startswith("HANGUL"):
        return "hangul"
    if ad.startswith(("HIRAGANA", "KATAKANA")):
        return "kana"
    if ad.startswith("CJK"):
        return "han"
    if ad.startswith("LATIN"):
        return "latin"
    return "diger"


def ozet(bloklar: list[TextBlock]) -> dict[str, float]:
    metin = "".join(b.text for b in bloklar)
    harfler = [c for c in metin if yazi_sistemi(c) != "-"]
    n = max(1, len(harfler))
    sayim = {k: sum(1 for c in harfler if yazi_sistemi(c) == k) / n for k in ("hangul", "kana", "han", "latin")}
    guven = [b.confidence for b in bloklar] or [0.0]
    return {"blok": len(bloklar), "harf": len(harfler), "guven": statistics.mean(guven), "guven_min": min(guven), **sayim}


def kirp(kare: Frame, bloklar: list[TextBlock], pay: int = 24) -> Frame:
    x1 = max(0, min(b.bbox.x for b in bloklar) - pay); y1 = max(0, min(b.bbox.y for b in bloklar) - pay)
    x2 = min(kare.rect.w, max(b.bbox.x + b.bbox.w for b in bloklar) + pay); y2 = min(kare.rect.h, max(b.bbox.y + b.bbox.h for b in bloklar) + pay)
    return Frame(image=np.ascontiguousarray(kare.image[y1:y2, x1:x2]), rect=Rect(x1, y1, x2 - x1, y2 - y1), captured_at=kare.captured_at, seq=kare.seq)


def main() -> int:
    t0 = time.perf_counter()
    motorlar = {dil: RapidOcrEngine(language=dil, threads=8, allow_download=True) for _, dil in DILLER}
    kareler = {ad: sentetik_kare(ad, 2560, 1440, adim_orani=2.0)[0] for ad, _ in DILLER}
    for m in motorlar.values():
        m.recognize(kareler["EN"], OcrPreset.DIALOGUE)   # isinma (kurulum)
    print(f"4 motor kurulum + isinma: {(time.perf_counter() - t0) * 1000:.0f} ms")
    print()
    print("=== A) TAM KARE: her panel x her model")
    print(f"{'panel':5} {'model':8} {'blok':>4} {'harf':>4} {'guven':>6} {'gmin':>6} {'hangul':>6} {'kana':>6} {'han':>6} {'latin':>6} {'ms':>6}")
    for ad, _ in DILLER:
        kare = kareler[ad]
        for mad, mdil in DILLER:
            t = time.perf_counter(); bl = motorlar[mdil].recognize(kare, OcrPreset.DIALOGUE); ms = (time.perf_counter() - t) * 1000
            o = ozet(bl)
            print(f"{ad:5} {mad:8} {o['blok']:4.0f} {o['harf']:4.0f} {o['guven']:6.3f} {o['guven_min']:6.3f} {o['hangul']:6.2f} {o['kana']:6.2f} {o['han']:6.2f} {o['latin']:6.2f} {ms:6.0f}")
        print()
    print("=== B) KIRPIK: mevcut motor (KR) tespit eder -> kirpik -> 4 model kirpikte")
    print(f"{'panel':5} {'model':8} {'blok':>4} {'harf':>4} {'guven':>6} {'gmin':>6} {'hangul':>6} {'kana':>6} {'han':>6} {'latin':>6} {'ms':>6}")
    for ad, _ in DILLER:
        kare = kareler[ad]
        t = time.perf_counter(); ilk = motorlar[OcrLanguage.KOREAN].recognize(kare, OcrPreset.DIALOGUE); ilk_ms = (time.perf_counter() - t) * 1000
        if not ilk:
            print(f"{ad}: KR motoru hic kutu vermedi"); continue
        k = kirp(kare, ilk)
        print(f"{ad}: ilk okuma {len(ilk)} kutu {ilk_ms:.0f} ms; kirpik {k.rect.w}x{k.rect.h}")
        for mad, mdil in DILLER:
            t = time.perf_counter(); bl = motorlar[mdil].recognize(k, OcrPreset.DIALOGUE); ms = (time.perf_counter() - t) * 1000
            o = ozet(bl)
            print(f"{ad:5} {mad:8} {o['blok']:4.0f} {o['harf']:4.0f} {o['guven']:6.3f} {o['guven_min']:6.3f} {o['hangul']:6.2f} {o['kana']:6.2f} {o['han']:6.2f} {o['latin']:6.2f} {ms:6.0f}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
