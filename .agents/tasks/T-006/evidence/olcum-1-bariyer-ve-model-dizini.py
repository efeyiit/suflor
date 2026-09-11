"""ÖLÇÜM 1 — K1 bariyeri altında model dizini nasıl bulunur?

Soru: `model_dir=None` iken rapidocr'un `models/` dizinini bulmak için
`import rapidocr` / `importlib.util.find_spec("rapidocr")` bariyer altında
çalışır mı? `importlib.metadata` çalışır mı? Sonuçlar aynı yolu mu verir?

Koşum: python .agents/tasks/T-006/evidence/olcum-1-bariyer-ve-model-dizini.py
"""
from __future__ import annotations

import importlib
import importlib.metadata
import importlib.util
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(KOK))

# --- A. bariyersiz referans: gerçek yol ------------------------------------
import rapidocr  # noqa: E402

referans = Path(rapidocr.__file__).resolve().parent / "models"
print("A  referans (Path(rapidocr.__file__).parent/'models'):", referans)
for m in [k for k in sys.modules if k.split(".")[0] in ("rapidocr", "onnxruntime")]:
    del sys.modules[m]

# --- B. şefin bariyerini kur (conftest'i modül olarak yükle) ---------------
spec = importlib.util.spec_from_file_location(
    "t006_conftest", KOK / "tests" / "unit" / "ocr" / "conftest.py"
)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print("B  bariyer kuruldu:", type(sys.meta_path[0]).__name__)

# --- C. bariyer altında üç yol ---------------------------------------------
def dene(ad: str, f):  # noqa: ANN001
    try:
        r = f()
        print(f"C  {ad:52s} -> OK   {r}")
        return r
    except Exception as e:  # noqa: BLE001
        print(f"C  {ad:52s} -> {type(e).__name__}: {str(e)[:60]}")
        return None

dene("import rapidocr", lambda: importlib.import_module("rapidocr"))
dene("import rapidocr.inference_engine.base", lambda: importlib.import_module("rapidocr.inference_engine.base"))
dene("importlib.util.find_spec('rapidocr')", lambda: importlib.util.find_spec("rapidocr"))
meta = dene(
    "importlib.metadata.distribution('rapidocr').locate_file",
    lambda: Path(importlib.metadata.distribution("rapidocr").locate_file("rapidocr")).resolve() / "models",
)
print("C  metadata yolu == referans yolu:", meta == referans)
print("C  sys.modules'ta rapidocr var mı (metadata yolu yükledi mi):", any(k.split('.')[0]=='rapidocr' for k in sys.modules))
print("C  modeller diskte:", sorted(p.name for p in referans.glob('*.onnx')))
