"""B3 -- pytest gozlem eklentisi: bariyer `tests` kokunden kosulunca da kuruluyor mu? OLCULUR.

`python -m pytest <hedef> -p tb_gozlem_plugin` (PYTHONPATH'te bu dizin) ile kosulur.
Kaydettikleri (TB_GOZLEM_CIKTI dosyasina):
  * `test_rapid_engine.py` TOPLANMADAN hemen once `sys.meta_path`te sefin `_T006Bariyer`
    ornegi var miydi (toplama sirasinda modul import edilir; bariyer o anda yoksa gec kalmistir)
  * her toplanan test dosyasi icin o andaki bariyer durumu
  * oturum sonunda sys.modules'ta rapidocr*/onnxruntime* var mi; bariyer sayisi
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_KAYIT: list[str] = []


def _bariyer_var() -> bool:
    return any(type(f).__name__ == "_T006Bariyer" for f in sys.meta_path)


def _yasak() -> list[str]:
    return sorted({k.split(".", 1)[0] for k in sys.modules if k.split(".", 1)[0] in ("rapidocr", "onnxruntime")})


def pytest_collect_file(file_path: Path, parent: object) -> None:  # noqa: ARG001
    if file_path.name.startswith("test_") and file_path.suffix == ".py":
        _KAYIT.append(f"toplama-oncesi {file_path.name:32s} bariyer={_bariyer_var()} yasak_yuklu={_yasak()}")


def pytest_sessionfinish(session: object, exitstatus: int) -> None:  # noqa: ARG001
    n = sum(1 for f in sys.meta_path if type(f).__name__ == "_T006Bariyer")
    _KAYIT.append(f"oturum-sonu bariyer_sayisi={n} yasak_yuklu={_yasak()} exitstatus={exitstatus}")
    hedef = os.environ.get("TB_GOZLEM_CIKTI")
    if hedef:
        Path(hedef).write_text("\n".join(_KAYIT) + "\n", encoding="utf-8")
