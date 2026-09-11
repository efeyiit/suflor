"""ÖLÇÜM 3 — gerçek motorun, motorumuzun geçeceği params ile davranışı.

Ölçülenler: kurulum süresi; logger seviyesi (params'ta log_level VARKEN ve
YOKKEN, kurulum öncesi/sonrası); oturum iş parçacığı seçenekleri; boş karede
çıktı biçimi; JP fixture'ında çıktı tipleri; 1×1 ve 0×0 kare; girdi
mutasyonu; `Global.model_root_dir` str kabulü; text_score=0 ile süzgeç.
OCR METNİ YAZDIRILMAZ (PROTOKOL §7) — yalnız tip/uzunluk/sayı.

Koşum: python .agents/tasks/T-006/evidence/olcum-3-gercek-motor-davranisi.py
"""
from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")
KOK = Path(__file__).resolve().parents[4]
FIX = KOK / ".agents" / "tasks" / "T-006" / "fixtures"

from rapidocr import EngineType, LangDet, LangRec, ModelType, OCRVersion, RapidOCR  # noqa: E402

M = Path(RapidOCR.__module__ and __import__("rapidocr").__file__).parent / "models"

def params(log_level: bool, threads: int = 8) -> dict:
    p = {
        "Global.text_score": 0.0,
        "Global.use_cls": False,
        "EngineConfig.onnxruntime.intra_op_num_threads": threads,
        "EngineConfig.onnxruntime.inter_op_num_threads": threads,
        "Det.engine_type": EngineType.ONNXRUNTIME, "Det.ocr_version": OCRVersion.PPOCRV4,
        "Det.model_type": ModelType.MOBILE, "Det.lang_type": LangDet.MULTI,
        "Det.model_path": str(M / "multi_PP-OCRv3_det_mobile.onnx"),
        "Rec.engine_type": EngineType.ONNXRUNTIME, "Rec.ocr_version": OCRVersion.PPOCRV4,
        "Rec.model_type": ModelType.MOBILE, "Rec.lang_type": LangRec.JAPAN,
        "Rec.model_path": str(M / "japan_PP-OCRv4_rec_mobile.onnx"),
    }
    if log_level:
        p["Global.log_level"] = "error"
    return p

lg = logging.getLogger("RapidOCR")
print("1  kurulum ÖNCESİ logger seviyesi:", logging.getLevelName(lg.level), "| propagate:", lg.propagate, "| handler sayısı:", len(lg.handlers))
lg.setLevel(logging.ERROR)
t0 = time.perf_counter(); eng = RapidOCR(params=params(log_level=False)); dt = (time.perf_counter()-t0)*1000
print(f"2  log_level PARAMS'TA YOK: kurulum {dt:.0f} ms; kurulum SONRASI seviye:", logging.getLevelName(lg.level), "(ERROR'a çekmiştik -> kütüphane sıfırladı mı?)")
lg.setLevel(logging.ERROR)
t0 = time.perf_counter(); eng2 = RapidOCR(params=params(log_level=True)); dt = (time.perf_counter()-t0)*1000
print(f"3  log_level='error' PARAMS'TA: kurulum {dt:.0f} ms; kurulum SONRASI seviye:", logging.getLevelName(lg.level))

so = eng2.text_det.session.session.get_session_options()
print("4  det oturumu intra/inter:", so.intra_op_num_threads, so.inter_op_num_threads)
so = eng2.text_rec.session.session.get_session_options()
print("   rec oturumu intra/inter:", so.intra_op_num_threads, so.inter_op_num_threads)
print("   text_score:", eng2.text_score, "| use_cls:", eng2.use_cls)

bos = np.full((400, 1200, 3), 128, np.uint8)
out = eng2(bos)
print("5  boş kare -> tip:", type(out).__name__, "| boxes:", out.boxes, "| txts:", out.txts, "| scores:", out.scores, "| len:", len(out))

img = np.array(Image.open(FIX / "dlg_JP.png").convert("RGB"))[:, :, ::-1].copy()
kopya = img.copy()
out = eng2(img)
print("6  JP fixture -> tip:", type(out).__name__, "| boxes:", type(out.boxes).__name__, out.boxes.dtype, out.boxes.shape,
      "| txts tipi:", type(out.txts).__name__, "| n:", len(out.txts),
      "| scores tipi:", type(out.scores).__name__, "| puan tipi:", type(out.scores[0]).__name__,
      "| min puan:", round(min(out.scores), 3))
print("   girdi mutasyona uğradı mı:", not np.array_equal(img, kopya), "| boxes köşe kesirli mi:", bool(np.any(out.boxes != np.round(out.boxes))))
print("   ilk kutu (koordinatlar, metin değil):", out.boxes[0].tolist())

for ad, k in (("1x1", np.zeros((1, 1, 3), np.uint8)), ("5x5", np.zeros((5, 5, 3), np.uint8)),
              ("0x0", np.zeros((0, 0, 3), np.uint8)), ("h=0", np.zeros((0, 10, 3), np.uint8)),
              ("4 kanal", np.zeros((40, 40, 4), np.uint8)), ("2B gri", np.zeros((40, 40), np.uint8)),
              ("float32", np.zeros((40, 40, 3), np.float32))):
    try:
        o = eng2(k)
        print(f"7  {ad:8s} -> {type(o).__name__} boxes={'None' if o.boxes is None else o.boxes.shape}")
    except Exception as e:  # noqa: BLE001
        print(f"7  {ad:8s} -> {type(e).__name__}: {str(e)[:70]}")

# 8. Global.model_root_dir str ile kabul + Det.model_dir gerçekten yok sayılıyor mu
import tempfile  # noqa: E402
d = tempfile.mkdtemp()
try:
    p = params(True); p["Global.model_root_dir"] = d
    RapidOCR(params=p)  # det/rec açık yol, cls -> d içinde YOK -> indirmeye kalkar
    print("8  Global.model_root_dir=boş tmp + cls açık yol yok -> KURULDU (cls indirildi?)", sorted(x.name for x in Path(d).iterdir()))
except Exception as e:  # noqa: BLE001
    print("8  Global.model_root_dir=boş tmp + cls açık yol yok ->", type(e).__name__, str(e)[:80])
try:
    p = params(True); del p["Det.model_path"]; p["Det.model_dir"] = str(M)
    p["Global.model_root_dir"] = d
    RapidOCR(params=p)
    print("8b Det.model_dir verildi, model_path yok -> kuruldu; tmp içeriği:", sorted(x.name for x in Path(d).iterdir()))
except Exception as e:  # noqa: BLE001
    print("8b Det.model_dir verildi, model_path yok ->", type(e).__name__, str(e)[:100])

# 9. text_score=0 ile KR fixture + JAPAN modeli: 0.5 altı blok sayısı (real_check #8)
kr = np.array(Image.open(FIX / "dlg_KR.png").convert("RGB"))[:, :, ::-1].copy()
o = eng2(kr)
print("9  KR+JAPAN text_score=0 -> n:", len(o), "| <0.5 olan:", sum(1 for s in o.scores if s < 0.5), "| min:", round(min(o.scores), 3))
p = params(True); p["Global.text_score"] = 0.5
o5 = RapidOCR(params=p)(kr)
print("   KR+JAPAN text_score=0.5 -> n:", len(o5), "(kütüphane varsayılanı; fark = sessizce elenen)")
