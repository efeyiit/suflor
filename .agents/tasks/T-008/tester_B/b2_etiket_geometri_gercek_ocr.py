"""B2-2 (tur 2) -- teslim testindeki ETIKET_KOPRU_GEOMETRI (11 kutu) gercek OCR ciktisiyla AYNI mi?
Referans turetme sorusu (§4.6/8): gomulu geometri gercek motordan mi (bagimsiz kanal), yoksa
uygulamanin ciktisina gore mi? Implementer `evidence/geometri-etiket-kopru-tur2.py` ile aldi;
burada BAGIMSIZ betikle YENIDEN uretilir. Ayri surec, gercek motor; METIN BASILMAZ.

Ayrica beklenen `[6,5]` ve satir kumeleri (1..5 / 6..10) GEOMETRIDEN bagimsiz turetilir
(y-kumeleme; uygulama cagrilmadan): etiket iki satiri kapsiyor mu, satirlar birbirine giriyor mu.
Kosum: python .agents/tasks/T-008/tester_B/b2_etiket_geometri_gercek_ocr.py
"""
from __future__ import annotations
import ast, sys
from pathlib import Path
import numpy as np
from PIL import Image
DEPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(DEPO))
from src.contracts.models import Frame, OcrPreset, Rect
from src.ocr.rapid_engine import OcrLanguage, RapidOcrEngine

yol = DEPO / ".agents/tasks/T-008/fixtures/etiket_kopru_KR.png"
img = np.array(Image.open(yol).convert("RGB"))[:, :, ::-1].copy()
h_img, w_img = img.shape[:2]
kr = RapidOcrEngine(language=OcrLanguage.KOREAN, threads=8).recognize(
    Frame(image=img, rect=Rect(0, 0, w_img, h_img), captured_at=0.0, seq=0), OcrPreset.DIALOGUE)
gercek = [(b.bbox.x, b.bbox.y, b.bbox.w, b.bbox.h) for b in kr]
agac = ast.parse((DEPO / "tests/unit/ocr/test_satir_birlestirici.py").read_text(encoding="utf-8"))
(kg,) = [n for n in agac.body if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.target.id == "ETIKET_KOPRU_GEOMETRI"]
sabit = list(ast.literal_eval(kg.value))
(ks,) = [n for n in agac.body if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.target.id == "ETIKET_KOPRU_SATIRLAR"]
print(f"fixture {yol.name} {w_img}x{h_img}; gercek OCR kutu sayisi {len(gercek)}; ETIKET_KOPRU_GEOMETRI kutu sayisi {len(sabit)}")
print(f"birebir esit (tespitci sirasinda): {gercek == sabit}")
print(f"kume olarak esit: {sorted(gercek) == sorted(sabit)}")
if gercek != sabit:
    for i, (g, s) in enumerate(zip(gercek, sabit)):
        if g != s:
            print(f"  fark idx {i}: gercek {g} sabit {s}")
print(f"metni bos: {sum(1 for b in kr if not b.text.strip())}; bas/son boslugu: {sum(1 for b in kr if b.text != b.text.strip())}; "
      f"NaN: {sum(1 for b in kr if b.confidence != b.confidence)}; line_boxes bos: {sum(1 for b in kr if not b.line_boxes)}/{len(kr)}")
print(f"ayni (y,x) cifti: {len(gercek) - len({(y, x) for x, y, _, _ in gercek})}; ayni x farkli y cifti: "
      f"{sum(1 for i in range(len(gercek)) for j in range(i+1, len(gercek)) if gercek[i][0] == gercek[j][0])}")

# --- beklenen [6,5] ve satir kumeleri GEOMETRIDEN, uygulama cagrilmadan ---------------------------
# satir = y araligi orta noktasina gore kumele (bosluk > 20 px yeni satir); etiket = h en buyuk kutu
h_sirali = sorted(range(len(gercek)), key=lambda i: gercek[i][3], reverse=True)
etiket = h_sirali[0]
kelimeler = [i for i in range(len(gercek)) if i != etiket]
ortalar = sorted(kelimeler, key=lambda i: gercek[i][1] + gercek[i][3] / 2)
satirlar: list[list[int]] = [[ortalar[0]]]
for i in ortalar[1:]:
    onceki = satirlar[-1][-1]
    if abs((gercek[i][1] + gercek[i][3] / 2) - (gercek[onceki][1] + gercek[onceki][3] / 2)) > 20:
        satirlar.append([i])
    else:
        satirlar[-1].append(i)
kumeler = [frozenset(s) for s in satirlar]
teslim_kumeler = list(eval(ast.unparse(ks.value), {"__builtins__": {}}, {"frozenset": frozenset, "range": range}))  # test dosyasindaki sabit ifade
print(f"etiket indeksi (en yuksek h): {etiket}; satir kumeleri (y-orta kumeleme, uygulamasiz): {[sorted(s) for s in kumeler]}")
print(f"teslimin ETIKET_KOPRU_SATIRLAR'i ile ayni: {kumeler == teslim_kumeler}")
ex, ey, ew, eh = gercek[etiket]
for k, s in enumerate(kumeler):
    ys = [gercek[i][1] for i in s]; alts = [gercek[i][1] + gercek[i][3] for i in s]; hs = [gercek[i][3] for i in s]
    ort = min(ey + eh, max(alts)) - max(ey, min(ys))
    print(f"  satir {k}: y {min(ys)}-{max(ys)}, alt {min(alts)}-{max(alts)}, h {min(hs)}-{max(hs)}; etiketle dikey ortusme {ort} (>= 0.5*min h {0.5*min(hs)}: {ort >= 0.5*min(hs)})")
s0_alt = max(gercek[i][1] + gercek[i][3] for i in kumeler[0]); s1_ust = min(gercek[i][1] for i in kumeler[1])
print(f"  satirlar arasi bosluk (satir0 alt {s0_alt} -> satir1 ust {s1_ust}): {s1_ust - s0_alt} px (birbirine girmiyor: {s1_ust > s0_alt})")
print(f"  etiket (x={ex}) satirlarin solunda: {all(ex < gercek[i][0] for i in kelimeler)}; etiket y={ey} en kucuk: {ey == min(y for _, y, _, _ in gercek)}")
print(f"beklenen parca sayilari (etiket satir 0'a yapisik kuraliyla): {[len(kumeler[0]) + 1, len(kumeler[1])]}; etiketsiz: {[len(kumeler[0]), len(kumeler[1])]}")
