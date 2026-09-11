"""B2 -- teslim testindeki KR_GEOMETRI (17 kutu) gercek OCR ciktisiyla AYNI mi?
Referans turetme sorusu: birim testin fixture'i gercek fixture'dan mi geliyor, yoksa
uygulamanin ciktisina gore mi uydurulmus? Ayri surec, gercek motor; METIN BASILMAZ
(yalniz kutu geometrisi ve sayim).
Kosum: python .agents/tasks/T-008/tester_B/b2_kr_geometri_gercek_ocr.py
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

img = np.array(Image.open(DEPO / ".agents/tasks/T-006/fixtures/dlg_KR.png").convert("RGB"))[:, :, ::-1].copy()
kr = RapidOcrEngine(language=OcrLanguage.KOREAN, threads=8).recognize(Frame(image=img, rect=Rect(0, 0, 1200, 400), captured_at=0.0, seq=0), OcrPreset.DIALOGUE)
gercek = [(b.bbox.x, b.bbox.y, b.bbox.w, b.bbox.h) for b in kr]
agac = ast.parse((DEPO / "tests/unit/ocr/test_satir_birlestirici.py").read_text(encoding="utf-8"))
(kg,) = [n for n in agac.body if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.target.id == "KR_GEOMETRI"]
sabit = list(ast.literal_eval(kg.value))
print(f"gercek OCR kutu sayisi {len(gercek)}; KR_GEOMETRI kutu sayisi {len(sabit)}")
print(f"birebir esit (girdi sirasinda): {gercek == sabit}")
print(f"kume olarak esit: {sorted(gercek) == sorted(sabit)}")
if gercek != sabit:
    for i, (g, s) in enumerate(zip(gercek, sabit)):
        if g != s:
            print(f"  fark idx {i}: gercek {g} sabit {s}")
# bos metin / bosluklu metin var mi (K3 strip kararinin erisilebilirligi) -- yalniz sayim
print(f"metni bos olan kutu: {sum(1 for b in kr if not b.text.strip())}; bas/son boslugu olan: {sum(1 for b in kr if b.text != b.text.strip())}; ic boslugu olan: {sum(1 for b in kr if ' ' in b.text.strip())}")
print(f"confidence NaN: {sum(1 for b in kr if b.confidence != b.confidence)}; line_boxes bos: {sum(1 for b in kr if not b.line_boxes)}/{len(kr)}")
print(f"ayni (y,x) cifti: {len(gercek) - len({(y, x) for x, y, _, _ in gercek})}; ayni x farkli y cifti (satir ici, M41 sinifi): "
      f"{sum(1 for i in range(len(gercek)) for j in range(i+1, len(gercek)) if gercek[i][0] == gercek[j][0] and abs(gercek[i][1]-gercek[j][1]) < 20)}")
