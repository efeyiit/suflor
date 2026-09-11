"""ÖLÇÜM 2 — K11 tablosu → rapidocr çözücüsünün verdiği dosya adları; enum zorunluluğu.

(a) Dört dil × (det, rec) için `InferSession.get_model_url(FileInfo(...))`
    → `Path(url).name`. Motorun sabit tablosu BU çıktıyla eşlenir.
(b) `ParseParams.update_batch`: engine_type/model_type/ocr_version string
    verilirse TypeError; lang_type string kabul eder mi?
(c) String → enum dönüşümü tam olarak tablodaki üyeyi veriyor mu (`is`).

Koşum: python .agents/tasks/T-006/evidence/olcum-2-model-adlari-ve-enum.py
"""
from __future__ import annotations

from pathlib import Path

from rapidocr import EngineType, LangDet, LangRec, ModelType, OCRVersion
from rapidocr.inference_engine.base import FileInfo, InferSession
from rapidocr.utils.parse_parameters import ParseParams
from rapidocr.utils.typings import TaskType

TABLO = {
    "japan":   (LangDet.MULTI, LangRec.JAPAN),
    "korean":  (LangDet.MULTI, LangRec.KOREAN),
    "chinese": (LangDet.CH,    LangRec.CH),
    "english": (LangDet.CH,    LangRec.EN),
}

print("(a) K11 tablosu -> get_model_url dosya adları")
for dil, (det, rec) in TABLO.items():
    fd = FileInfo(EngineType.ONNXRUNTIME, OCRVersion.PPOCRV4, TaskType.DET, det, ModelType.MOBILE)
    fr = FileInfo(EngineType.ONNXRUNTIME, OCRVersion.PPOCRV4, TaskType.REC, rec, ModelType.MOBILE)
    nd = Path(InferSession.get_model_url(fd)["model_dir"]).name
    nr = Path(InferSession.get_model_url(fr)["model_dir"]).name
    print(f"    {dil:8s} det={det.value:6s} -> {nd:32s} rec={rec.value:7s} -> {nr}")

print("(b) update_batch string kabulü")
cfg = ParseParams.load(Path(__file__).resolve().parents[4] / "nonexistent.yaml") if False else None
import rapidocr.main as rm  # noqa: E402
cfg = ParseParams.load(rm.DEFAULT_CFG_PATH)
for k, v in [("Det.engine_type", "onnxruntime"), ("Det.model_type", "mobile"),
             ("Det.ocr_version", "PP-OCRv4"), ("Det.lang_type", "multi"),
             ("Rec.lang_type", "japan")]:
    try:
        ParseParams.update_batch(cfg, {k: v})
        print(f"    {k:18s} = {v!r:14s} -> KABUL  (cfg değeri tipi: {type(eval('cfg.'+k)).__name__})")
    except Exception as e:  # noqa: BLE001
        print(f"    {k:18s} = {v!r:14s} -> {type(e).__name__}: {e}")

print("(c) string -> enum dönüşümü tablodaki üyeyi veriyor mu")
print("    LangDet('multi') is LangDet.MULTI      :", LangDet("multi") is LangDet.MULTI)
print("    LangDet('ch') is LangDet.CH            :", LangDet("ch") is LangDet.CH)
print("    LangRec('japan') is LangRec.JAPAN      :", LangRec("japan") is LangRec.JAPAN)
print("    LangRec('korean') is LangRec.KOREAN    :", LangRec("korean") is LangRec.KOREAN)
print("    LangRec('ch') is LangRec.CH            :", LangRec("ch") is LangRec.CH)
print("    LangRec('en') is LangRec.EN            :", LangRec("en") is LangRec.EN)
print("    EngineType('onnxruntime') is ONNXRUNTIME:", EngineType("onnxruntime") is EngineType.ONNXRUNTIME)
print("    ModelType('mobile') is MOBILE           :", ModelType("mobile") is ModelType.MOBILE)
print("    OCRVersion('PP-OCRv4') is PPOCRV4       :", OCRVersion("PP-OCRv4") is OCRVersion.PPOCRV4)
print("(d) cls dosya adı (paketle geliyor mu -> RECORD'da var, bkz. olcum-2 .txt sonu)")
from rapidocr.utils.typings import LangCls  # noqa: E402
fc = FileInfo(EngineType.ONNXRUNTIME, OCRVersion.PPOCRV4, TaskType.CLS, LangCls.CH, ModelType.MOBILE)
print("    cls ->", Path(InferSession.get_model_url(fc)["model_dir"]).name)
import importlib.metadata as md  # noqa: E402
rec = [f for f in md.distribution("rapidocr").files or [] if "models/" in str(f).replace("\\", "/")]
print("    RECORD'daki model dosyaları:", [Path(str(f)).name for f in rec])
