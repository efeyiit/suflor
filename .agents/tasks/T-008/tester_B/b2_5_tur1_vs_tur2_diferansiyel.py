"""B2-5 -- T2-1 etki alani (kosum: python .agents/tasks/T-008/tester_B/b2_5_tur1_vs_tur2_diferansiyel.py [tur1_kaynak.py]): tur 1 (fe01641) vs tur 2 (HEAD) -- etiketsiz rastgele yerlesimlerde ayrisma 0 mi
(regresyon), sol uzun etiketli yerlesimlerde ayrisma var mi (pozitif kontrol, §4.6/10)."""
import sys, random, importlib.util, subprocess, tempfile, os
sys.path.insert(0, ".")
if len(sys.argv) < 2:  # tur 1 kaynagi (commit fe01641) gecici dosyaya
    _t1 = os.path.join(os.environ.get("T008_TB_SCRATCH", tempfile.gettempdir()), "sb_tur1_fe01641.py")
    open(_t1, "w", encoding="utf-8").write(subprocess.run(["git", "show", "fe01641:src/ocr/satir_birlestirici.py"], capture_output=True, text=True, encoding="utf-8").stdout)
    sys.argv.append(_t1)
from src.contracts.models import Rect, TextBlock
from src.ocr import satir_birlestirici as t2
spec = importlib.util.spec_from_file_location("sb_tur1", sys.argv[1]); t1 = importlib.util.module_from_spec(spec); spec.loader.exec_module(t1)

def b(x, y, w, h, t): return TextBlock(text=t, bbox=Rect(x, y, w, h), confidence=0.9)
def cikti(m, g): return [(c.text, c.bbox.x, c.bbox.y, c.bbox.w, c.bbox.h) for c in m.satirlari_birlestir(g)]

def yerlesim(rnd, etiket):
    """2-4 satir, satir basi 2-6 kelime; h 26-41 titresimli (KR sinifi), satir araligi >= 10 px."""
    g = []; y = rnd.randint(50, 80); satir_h = 34
    n_satir = rnd.randint(2, 4); x0 = rnd.randint(60, 220)
    for s in range(n_satir):
        x = x0
        for k in range(rnd.randint(2, 6)):
            h = rnd.randint(26, 41); w = rnd.randint(50, 150); yy = y + rnd.randint(-3, 3)
            g.append(b(x, yy, w, h, f"s{s}k{k}"))
            x += w + rnd.randint(4, 18)   # kelime boslugu <= 0.57*h
        y += satir_h + rnd.randint(10, 24)
    if etiket:
        g.insert(0, b(x0 - rnd.randint(60, 150), g[0].bbox.y - rnd.randint(5, 12), rnd.randint(60, 130), 2 * satir_h + rnd.randint(4, 12), "T"))
    rnd.shuffle(g)
    return g

rnd = random.Random(2026)
for etiket in (False, True):
    ayr = 0; N = 3000
    for _ in range(N):
        g = yerlesim(rnd, etiket)
        if cikti(t1, g) != cikti(t2, g): ayr += 1
    print(f"{'ETIKETLI (pozitif kontrol)' if etiket else 'ETIKETSIZ (regresyon)'}: {N} rastgele yerlesim, tur1 != tur2: {ayr}")
# gercek geometriler: KR 17 ve etiket 11 (test dosyasindaki sabitler) -- tur1 == tur2?
import ast
agac = ast.parse(open("tests/unit/ocr/test_satir_birlestirici.py", encoding="utf-8").read())
sab = {n.target.id: ast.literal_eval(n.value) for n in agac.body if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.target.id in ("KR_GEOMETRI", "ETIKET_KOPRU_GEOMETRI")}
for ad, geo in sab.items():
    g = [b(x, y, w, h, f"k{i}") for i, (x, y, w, h) in enumerate(geo)]
    c1, c2 = t1.satirlari_birlestir(g), t2.satirlari_birlestir(g)
    print(f"{ad}: tur1 parca {[len(c.line_boxes) or 1 for c in c1]} | tur2 parca {[len(c.line_boxes) or 1 for c in c2]} | ayni: {cikti(t1, g) == cikti(t2, g)}")

# --- DEGISMEZ taramasi (tur 2): etiketli 3000 yerlesimde hicbir cikti blogu iki satirdan kelime tasimaz;
#     her satirin kelimeleri TEK blokta (etiket satir 0'a yapisabilir). Tur 1'de ayni olcu (pozitif kontrol).
def ihlal(m, g):
    karisik = butun_degil = 0
    satir_blok = {}
    for bi, c in enumerate(m.satirlari_birlestir(g)):
        satirlar = {t[1] for t in c.text.split() if t.startswith("s")}
        if len(satirlar) > 1: karisik += 1
        for s in satirlar: satir_blok.setdefault(s, set()).add(bi)
    butun_degil = sum(1 for v in satir_blok.values() if len(v) > 1)
    return karisik, butun_degil
rnd = random.Random(99)
for ad, m in (("tur1", t1), ("tur2", t2)):
    k_top = b_top = yerl = 0
    rnd = random.Random(99)
    for _ in range(3000):
        k, bb = ihlal(m, yerlesim(rnd, True))
        k_top += k; b_top += bb; yerl += 1 if (k or bb) else 0
    print(f"{ad} ETIKETLI 3000: iki satir karisan blok {k_top}, parcalanan satir {b_top}, ihlalli yerlesim {yerl}")
