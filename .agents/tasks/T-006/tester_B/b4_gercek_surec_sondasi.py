"""B4/B2 -- GERCEK modelle AYRI SURECTE: stdout/stderr'e bir bayt yaziliyor mu? Cikti bicimi ne?

Bariyer surec-yerel oldugu icin bu dosya pytest ALTINDA KOSMAZ; alt surecler acar,
her birinin stdout/stderr'ini BAYT olarak yakalar (PYTHONIOENCODING verilmez:
gercek kosul). Alt surec sonucu JSON dosyasina yazar, stdout'a hicbir sey
yazmamasi beklenir. OCR metni hicbir yere basilmaz (yalniz uzunluk/tip).

Asamalar (her biri ayri surec):
  A  import + yapim (recognize yok)                       -> bayt sayisi
  B  A + JP x2, bos gri 1200x400, 1x1, KR fixture (JAPAN)  -> bayt sayisi (A ile fark = recognize'in yazdigi)
  C  B ama kok logger DEBUG'a acik (uygulama debug modu)  -> bayt sayisi
  D  B + kurulumdan SONRA RapidOCR logger'i DEBUG'a acilip bos kare (uygulama kutuphane logger'ini acarsa)
  E  gercek kutuphane ciktisinin bicimi (fabrika dogrudan cagrilir), logger envanteri, sys.modules izi

Kosum: python .agents/tasks/T-006/tester_B/b4_gercek_surec_sondasi.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

DEPO = Path(__file__).resolve().parents[4]
FIX = DEPO / ".agents" / "tasks" / "T-006" / "fixtures"

COCUK = r'''
import json, logging, sys, os
from pathlib import Path
asama, sonuc_yolu, depo, fix = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
sys.path.insert(0, depo)
import numpy as np
from PIL import Image
if asama == "C":
    logging.basicConfig(level=logging.DEBUG)  # uygulama debug modu: kok logger DEBUG + stderr handler
r = {"asama": asama}
from src.contracts.models import Frame, Rect, OcrPreset
from src.ocr import rapid_engine
from src.ocr.rapid_engine import RapidOcrEngine, OcrLanguage
r["import_sonrasi_rapidocr_yuklu"] = "rapidocr" in sys.modules
def kare(ad, rect=None):
    img = np.array(Image.open(Path(fix) / f"dlg_{ad}.png").convert("RGB"))[:, :, ::-1].copy()
    return Frame(image=img, rect=rect or Rect(0, 0, img.shape[1], img.shape[0]), captured_at=0.0, seq=0)
def gri(h, w):
    return Frame(image=np.full((h, w, 3), 128, np.uint8), rect=Rect(0, 0, w, h), captured_at=0.0, seq=0)
jp = RapidOcrEngine(language=OcrLanguage.JAPAN, threads=8, allow_download=False)
r["yapim_sonrasi_rapidocr_yuklu"] = "rapidocr" in sys.modules
if asama == "A":
    json.dump(r, open(sonuc_yolu, "w", encoding="utf-8")); sys.exit(0)
if asama == "E":
    params = jp.parametreler()
    tan = rapid_engine._varsayilan_fabrika(params)
    c = tan(kare("JP").image)
    r["cikti_tipi"] = type(c).__name__
    r["boxes_tipi"] = type(c.boxes).__name__; r["boxes_dtype"] = str(getattr(c.boxes, "dtype", None)); r["boxes_shape"] = list(getattr(c.boxes, "shape", ()))
    r["txts_tipi"] = type(c.txts).__name__; r["txts_eleman_tipi"] = type(c.txts[0]).__name__; r["txts_n"] = len(c.txts)
    r["scores_tipi"] = type(c.scores).__name__; r["scores_eleman_tipi"] = type(c.scores[0]).__name__
    r["scores_eleman_python_float"] = type(c.scores[0]) is float
    b = tan(gri(400, 1200).image)
    r["bos_cikti_tipi"] = type(b).__name__; r["bos_alanlar"] = [b.boxes is None, b.txts is None, b.scores is None]
    b1 = tan(gri(1, 1).image)
    r["1x1_alanlar"] = [b1.boxes is None, b1.txts is None, b1.scores is None]
    lg = logging.getLogger("RapidOCR")
    r["RapidOCR_level"] = logging.getLevelName(lg.level); r["RapidOCR_propagate"] = lg.propagate
    r["RapidOCR_handlers"] = [type(h).__name__ + ":" + logging.getLevelName(h.level) for h in lg.handlers]
    r["logger_envanteri"] = sorted(n for n in logging.Logger.manager.loggerDict if "rapid" in n.lower() or "onnx" in n.lower())
    r["sys_modules_rapid_onnx"] = sorted({k.split(".",1)[0] for k in sys.modules if k.split(".",1)[0] in ("rapidocr","onnxruntime")})
    json.dump(r, open(sonuc_yolu, "w", encoding="utf-8")); sys.exit(0)
# B / C / D
sayilar = []
sayilar.append(len(jp.recognize(kare("JP"), OcrPreset.DIALOGUE)))
sayilar.append(len(jp.recognize(kare("JP", Rect(-2600, -50, 1200, 400)), OcrPreset.DIALOGUE)))
sayilar.append(len(jp.recognize(gri(400, 1200), OcrPreset.DIALOGUE)))
sayilar.append(len(jp.recognize(gri(1, 1), OcrPreset.DIALOGUE)))
sayilar.append(len(jp.recognize(kare("KR"), OcrPreset.DIALOGUE)))
if asama == "D":
    logging.getLogger("RapidOCR").setLevel(logging.DEBUG)
    sayilar.append(len(jp.recognize(gri(400, 1200), OcrPreset.DIALOGUE)))
lg = logging.getLogger("RapidOCR")
r["blok_sayilari"] = sayilar
r["RapidOCR_level_sonda"] = logging.getLevelName(lg.level)
jp.close()
json.dump(r, open(sonuc_yolu, "w", encoding="utf-8")); sys.exit(0)
'''


def kos(asama: str) -> tuple[bytes, bytes, dict, int]:
    with tempfile.TemporaryDirectory() as d:
        sonuc = Path(d) / "sonuc.json"
        env = {k: v for k, v in os.environ.items() if k != "PYTHONIOENCODING"}
        r = subprocess.run([sys.executable, "-c", COCUK, asama, str(sonuc), str(DEPO), str(FIX)],
                           capture_output=True, cwd=str(DEPO), env=env, timeout=300)
        veri = json.loads(sonuc.read_text(encoding="utf-8")) if sonuc.exists() else {"HATA": "sonuc dosyasi yok"}
        return r.stdout, r.stderr, veri, r.returncode


def main() -> int:
    print("B4/B2 gercek surec sondasi -- PYTHONIOENCODING verilmedi, konsol kodlamasi gercek")
    ihlal = 0
    bayt: dict[str, tuple[int, int]] = {}
    for asama in ("A", "B", "C", "D", "E"):
        out, err, veri, rc = kos(asama)
        bayt[asama] = (len(out), len(err))
        print(f"\n[{asama}] exit={rc}  stdout={len(out)} bayt  stderr={len(err)} bayt")
        if out:
            print("   stdout ilk 300 bayt:", repr(out[:300]))
        if err:
            print("   stderr ilk 600 bayt:", repr(err[:600]))
        for k, v in veri.items():
            if k != "asama":
                print(f"   {k}: {v}")
        if rc != 0:
            ihlal += 1
    print()
    a, b, c = bayt["A"], bayt["B"], bayt["C"]
    print(f"recognize'in yazdigi (B - A): stdout {b[0]-a[0]} bayt, stderr {b[1]-a[1]} bayt")
    print(f"kok DEBUG altinda recognize (C - A): stdout {c[0]-a[0]} bayt, stderr {c[1]-a[1]} bayt")
    print(f"D (RapidOCR logger'i uygulama DEBUG'a acarsa, bos kare): stdout {bayt['D'][0]} stderr {bayt['D'][1]} bayt")
    if b != (0, 0) or c[0] != 0:
        print("BULGU: import/yapim/recognize yolunda stdout/stderr'e bayt yazildi (yukarida)")
    else:
        print("A/B/C: import + yapim + recognize sifir bayt (K7 gercek yolda tutuyor)")
    return 1 if ihlal else 0


if __name__ == "__main__":
    sys.exit(main())
