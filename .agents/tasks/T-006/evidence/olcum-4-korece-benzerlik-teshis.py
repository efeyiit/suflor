"""ÖLÇÜM 4 — real_check #3 (KOREAN ≥0.95) neden 0.932 veriyor? METİNSİZ teşhis.

Yalnız geometri (bbox.y, okuma sırası kovası), puan, uzunluk ve difflib
opcode etiketleri yazdırılır; OCR metni HİÇBİR yere basılmaz (PROTOKOL §7).

Koşum: python .agents/tasks/T-006/evidence/olcum-4-korece-benzerlik-teshis.py
"""
from __future__ import annotations

import difflib
import sys
import unicodedata
from pathlib import Path

import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")
KOK = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(KOK))
from src.contracts.models import Frame, OcrPreset, Rect  # noqa: E402
from src.ocr.rapid_engine import OcrLanguage, RapidOcrEngine  # noqa: E402

FIX = KOK / ".agents" / "tasks" / "T-006" / "fixtures"
BEKLENEN_KR = ["장로 마르쿠스", "마을 장로가 당신을 기다리고 있습니다.",
               "방앗간을 지나 동쪽 길로 가십시오.", "해가 지면 길을 벗어나지 마십시오."]

img = np.array(Image.open(FIX / "dlg_KR.png").convert("RGB"))[:, :, ::-1].copy()
f = Frame(image=img, rect=Rect(-2600, -50, 1200, 400, monitor_index=0), captured_at=0.0, seq=0)
kr = RapidOcrEngine(language=OcrLanguage.KOREAN, threads=8, allow_download=False)
bl = kr.recognize(f, OcrPreset.DIALOGUE)

def bosluksuz(s: str) -> str:
    return "".join(s.split())

print(f"blok sayısı: {len(bl)}")
print("A  blok geometrisi (ham sıra): idx | y | x | h | kova=round(y/25) | uzunluk | puan | Hangul?")
for i, b in enumerate(bl):
    hangul = all(unicodedata.name(c, "").startswith("HANGUL") or c in ".,!? " for c in b.text)
    print(f"   {i:2d} | {b.bbox.y:4d} | {b.bbox.x:5d} | {b.bbox.h:3d} | {round(b.bbox.y/25):3d} | {len(b.text):2d} | {b.confidence:.3f} | {hangul}")

# real_check'in okuma sırası
sirali = sorted(bl, key=lambda b: (round(b.bbox.y / 25), b.bbox.x))
o = bosluksuz("".join(b.text for b in sirali))
e = bosluksuz("".join(BEKLENEN_KR))
sm = difflib.SequenceMatcher(None, o, e)
print(f"B  real_check okuma sırası ile benzerlik: {sm.ratio():.3f}  (okunan {len(o)} kr, beklenen {len(e)} kr)")
print("   opcode'lar (etiket, okunan aralık, beklenen aralık) — metin yok:")
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag != "equal":
        print(f"     {tag:8s} okunan[{i1}:{i2}] beklenen[{j1}:{j2}]")

# alternatif sıralamalar: satır kovasını daha kaba (y/60) ve satır merkeziyle
for ad, key in (("kova y//60", lambda b: (b.bbox.y // 60, b.bbox.x)),
                ("merkez y//60", lambda b: ((b.bbox.y + b.bbox.h // 2) // 60, b.bbox.x))):
    s2 = sorted(bl, key=key)
    o2 = bosluksuz("".join(b.text for b in s2))
    print(f"C  {ad:14s} benzerlik: {difflib.SequenceMatcher(None, o2, e).ratio():.3f}")

# satır satır: her beklenen satır, okunan bloklar arasında birebir var mı; en iyi eşleşme oranı
print("D  satır bazlı en iyi eşleşme (blokların kovaya göre birleşimi):")
kovalar: dict[int, list] = {}
for b in sirali:
    kovalar.setdefault(round(b.bbox.y / 25), []).append(b)
for k, bs in sorted(kovalar.items()):
    satir = bosluksuz("".join(b.text for b in sorted(bs, key=lambda b: b.bbox.x)))
    en_iyi = max(difflib.SequenceMatcher(None, satir, bosluksuz(s)).ratio() for s in BEKLENEN_KR)
    print(f"   kova {k:2d}: {len(bs):2d} blok, {len(satir):2d} kr, en iyi satır benzerliği {en_iyi:.3f}")
