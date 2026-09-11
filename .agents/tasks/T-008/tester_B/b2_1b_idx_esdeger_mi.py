"""B2-1b -- `-idx` (ilk siralamada bag TERS; implementer C-3) davranis-esdeger mi? (kosum: python .agents/tasks/T-008/tester_B/b2_1b_idx_esdeger_mi.py) Ayni (y,x), farkli h cift + komsu satir."""
import sys, importlib
sys.path.insert(0, ".")
from src.contracts.models import Rect, TextBlock
from src.ocr import satir_birlestirici as m

def b(x, y, w, h, t):
    return TextBlock(text=t, bbox=Rect(x, y, w, h), confidence=0.9)

# R(0,0,95,20) satir 1; D(160,0,50,20) satir 1 sagda; a(100,15,50,20) uzun, s(100,15,50,8) kisa: AYNI (y,x)
R, D = b(0, 0, 95, 20, "R"), b(160, 0, 50, 20, "D")
a, s = b(100, 15, 50, 20, "a"), b(100, 15, 50, 8, "s")

def kos(girdi):
    return [c.text for c in m.satirlari_birlestir(girdi)]

print("ORIJINAL kod:")
print("  [R, s, a, D] ->", kos([R, s, a, D]))
print("  [R, a, s, D] ->", kos([R, a, s, D]))
# -idx mutanti: kaynak metnini yamala, ayri modul olarak yukle
src = open("src/ocr/satir_birlestirici.py", encoding="utf-8").read()
eski = "key=lambda c: (c[1].bbox.y, c[1].bbox.x, c[0]))"
assert src.count(eski) == 1
mut = src.replace(eski, "key=lambda c: (c[1].bbox.y, c[1].bbox.x, -c[0]))")
ns = {"__name__": "mut_idx"}
code = compile(mut, "mut_idx.py", "exec")
import types
mm = types.ModuleType("mut_idx"); mm.__dict__["__file__"] = "mut_idx.py"
exec(code, mm.__dict__)
def kos2(girdi):
    return [c.text for c in mm.satirlari_birlestir(girdi)]
print("-idx MUTANT:")
print("  [R, s, a, D] ->", kos2([R, s, a, D]))
print("  [R, a, s, D] ->", kos2([R, a, s, D]))
print()
print("ESDEGER DEGIL:", kos([R, s, a, D]) != kos2([R, s, a, D]) or kos([R, a, s, D]) != kos2([R, a, s, D]))
print("ORIJINALDE bag sirasi SATIR UYELIGINI degistiriyor (docstring K6 'satir uyeligini DEGIL' iddiasi):",
      kos([R, s, a, D]) != kos([R, a, s, D]))
# rastgele tarama: ayni (y,x) cift + komsu satir siniflarinda kac ayrisma
import random
rnd = random.Random(7)
ayrisma = 0; N = 3000
for _ in range(N):
    y2 = rnd.randint(8, 24); hk = rnd.randint(2, 12); hu = rnd.randint(16, 30)
    xr = rnd.randint(0, 40); wr = rnd.randint(40, 100)
    g = [b(xr, 0, wr, 20, "R"), b(100, y2, 50, hu, "a"), b(100, y2, 50, hk, "s"), b(rnd.randint(150, 200), 0, 50, 20, "D")]
    rnd.shuffle(g)
    if kos(g) != kos2(g):
        ayrisma += 1
print(f"rastgele {N} (ayni (y,x) cift, farkli h, komsu satir): -idx ayrisma = {ayrisma}")
