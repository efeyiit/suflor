"""B5 -- gozlem eklentisi: teslim test dosyasi kosarken SEFIN bariyeri gercekten aktif mi?

`python -m pytest tests/unit/ocr/test_satir_birlestirici.py -p tb_gozlem_plugin`
(PYTHONPATH bu dizini icermeli). Her testin setup aninda:
  * `sys.meta_path[0]` sinif adi `_T006Bariyer` mi,
  * `importlib.import_module("rapidocr")` `RuntimeError("T-006 K1 bariyeri...")` veriyor mu,
  * `sys.modules` icinde yasak kok var mi
sayilir; oturum sonunda `TB_GOZLEM` ortam degiskenindeki dosyaya JSON yazilir.
Kendisi hicbir bariyer KURMAZ -- yalniz gozler.
"""
from __future__ import annotations

import importlib
import json
import os
import sys
from typing import Any

_SAYAC: dict[str, Any] = {"setup": 0, "basta_bariyer": 0, "rapidocr_kesildi": 0, "onnxruntime_kesildi": 0,
                          "yasak_kok_sys_modules": 0, "ilk_hata": ""}


def pytest_runtest_setup(item: Any) -> None:
    _SAYAC["setup"] += 1
    if sys.meta_path and type(sys.meta_path[0]).__name__ == "_T006Bariyer":
        _SAYAC["basta_bariyer"] += 1
    for kok, anahtar in (("rapidocr", "rapidocr_kesildi"), ("onnxruntime", "onnxruntime_kesildi")):
        sys.modules.pop(kok, None)
        try:
            importlib.import_module(kok)
        except RuntimeError as e:
            if "T-006 K1 bariyeri" in str(e):
                _SAYAC[anahtar] += 1
            elif not _SAYAC["ilk_hata"]:
                _SAYAC["ilk_hata"] = f"{kok}: RuntimeError ama mesaj farkli: {e}"
        except Exception as e:  # noqa: BLE001
            if not _SAYAC["ilk_hata"]:
                _SAYAC["ilk_hata"] = f"{kok}: {type(e).__name__}: {e}"
        else:
            if not _SAYAC["ilk_hata"]:
                _SAYAC["ilk_hata"] = f"{kok}: import BASARILI (bariyer bos)"
    if any(k.split(".", 1)[0] in ("rapidocr", "onnxruntime") for k in sys.modules):
        _SAYAC["yasak_kok_sys_modules"] += 1


def pytest_sessionfinish(session: Any, exitstatus: int) -> None:
    hedef = os.environ.get("TB_GOZLEM")
    _SAYAC["exitstatus"] = int(exitstatus)
    _SAYAC["yasak_kok_sonda"] = sorted(k for k in sys.modules if k.split(".", 1)[0] in ("rapidocr", "onnxruntime"))
    if hedef:
        with open(hedef, "w", encoding="utf-8") as f:
            json.dump(_SAYAC, f, ensure_ascii=True, indent=1)
