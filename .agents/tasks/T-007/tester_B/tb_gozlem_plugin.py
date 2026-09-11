"""TESTER-B B3 gozlem eklentisi -- `pytest tests` (depo koku) kosumunda K1 bariyeri GERCEKTEN kurulu mu, NE ZAMAN?

    PYTHONPATH=.agents/tasks/T-007/tester_B TB_GOZLEM=<dosya> python -m pytest tests -q -p tb_gozlem_plugin

Kaydeder:
  * toplama bitiminde: sys.meta_path'teki bariyer siniflari ve indeksleri; sys.modules'ta yasak kok var mi
  * her `tests/unit/translate/` testinin SETUP aninda: bariyer meta_path[0] mi (bir kez ozetlenir)
  * oturum sonunda: yasak kok sys.modules'a girdi mi (0 olmali)
Bariyerin kendisini KURMAZ; yalniz gozler.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

YASAK = ("ctranslate2", "sentencepiece")
CIKTI = Path(os.environ.get("TB_GOZLEM", "tb_gozlem.txt"))
_satirlar: list[str] = []
_translate_setup: dict[str, int] = {"toplam": 0, "bariyer_basta": 0, "bariyer_yok": 0}


def _bariyerler() -> list[str]:
    return [f"[{i}] {type(f).__name__}" for i, f in enumerate(sys.meta_path) if "Bariyer" in type(f).__name__]


def _yasak_moduller() -> list[str]:
    return sorted(k for k in sys.modules if k.split(".", 1)[0] in YASAK)


def pytest_sessionstart(session: pytest.Session) -> None:
    _satirlar.append(f"oturum basi: meta_path bariyerleri={_bariyerler()}  yasak sys.modules={_yasak_moduller()}  cwd={os.getcwd()}")


def pytest_collection_finish(session: pytest.Session) -> None:
    _satirlar.append(f"toplama sonu: meta_path bariyerleri={_bariyerler()}  yasak sys.modules={_yasak_moduller()}  toplanan={len(session.items)}")


def pytest_runtest_setup(item: pytest.Item) -> None:
    yol = str(item.fspath).replace("\\", "/")
    if "/tests/unit/translate/" in yol:
        _translate_setup["toplam"] += 1
        adlar = [type(f).__name__ for f in sys.meta_path]
        if adlar and "Bariyer" in adlar[0]:
            _translate_setup["bariyer_basta"] += 1
        if not any("Bariyer" in a for a in adlar):
            _translate_setup["bariyer_yok"] += 1


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    _satirlar.append(f"translate testleri: {_translate_setup}")
    _satirlar.append(f"oturum sonu: meta_path bariyerleri={_bariyerler()}  yasak sys.modules={_yasak_moduller()}  exit={exitstatus}")
    CIKTI.write_text("\n".join(_satirlar) + "\n", encoding="utf-8")
