"""B3 -- olcekleme olcumu: 1k / 10k / 100k blok, dort yerlesim; oranlar. n log n mi, n^2 mi?
Kosum: python .agents/tasks/T-008/tester_B/b3_olcekleme.py
"""
from __future__ import annotations
import random, statistics, sys, time
from pathlib import Path
DEPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(DEPO))
from src.contracts.models import Rect, TextBlock
from src.ocr.satir_birlestirici import satirlari_birlestir

def _b(x, y, w, h, t): return TextBlock(text=t, bbox=Rect(x, y, w, h), confidence=0.9)
def yerlesim(ad, n, rnd):
    if ad == "rastgele": return [_b(rnd.randrange(0, 2000), rnd.randrange(0, 1400) // 40 * 40, 60, 36, f"w{i}") for i in range(n)]
    if ad == "tek-satir-zincir": return [_b(i * 70, 0, 60, 36, f"w{i}") for i in range(n)]
    if ad == "hepsi-bagli": return [_b(0, 0, 60, 36, f"w{i}") for i in range(n)]
    if ad == "sutun": return [_b(0, i * 40, 60, 36, f"w{i}") for i in range(n)]
def sure(g, k):
    satirlari_birlestir(g); s = []
    for _ in range(k):
        t0 = time.perf_counter(); satirlari_birlestir(g); s.append((time.perf_counter() - t0) * 1000)
    return statistics.median(s)
print(f"{'yerlesim':18s} {'1k ms':>8s} {'10k ms':>8s} {'100k ms':>9s} {'10k/1k':>7s} {'100k/10k':>9s}   (n log n: ~13 / ~12; n^2: ~100)")
for ad in ("rastgele", "tek-satir-zincir", "hepsi-bagli", "sutun"):
    rnd = random.Random(7)
    t1 = sure(yerlesim(ad, 1000, rnd), 7); t10 = sure(yerlesim(ad, 10_000, rnd), 3); t100 = sure(yerlesim(ad, 100_000, rnd), 1)
    print(f"{ad:18s} {t1:8.2f} {t10:8.2f} {t100:9.1f} {t10/t1:7.1f} {t100/t10:9.1f}")
