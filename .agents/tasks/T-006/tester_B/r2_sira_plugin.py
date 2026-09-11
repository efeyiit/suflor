"""TESTER-B tur 2 / B2-3 -- toplama sirasini degistiren eklenti (ters / rastgele / K7 once / K7 sona).

TB_SIRA=ters        -> items ters cevrilir
TB_SIRA=rastgele:N  -> random.Random(N).shuffle(items)
TB_SIRA=k7once      -> `test_k7_` ile baslayanlar basa, kalan ayni sirada
TB_SIRA=k7sona      -> `test_k7_` ile baslayanlar sona

Kosum: PYTHONPATH=.agents/tasks/T-006/tester_B TB_SIRA=ters python -m pytest ... -p r2_sira_plugin
"""
from __future__ import annotations

import os
import random

import pytest


def pytest_collection_modifyitems(session: pytest.Session, config: pytest.Config, items: list[pytest.Item]) -> None:
    sira = os.environ.get("TB_SIRA", "")
    if sira == "ters":
        items.reverse()
    elif sira.startswith("rastgele:"):
        random.Random(int(sira.split(":", 1)[1])).shuffle(items)
    elif sira == "k7once":
        k7 = [i for i in items if i.name.startswith("test_k7_")]
        kalan = [i for i in items if not i.name.startswith("test_k7_")]
        items[:] = k7 + kalan
    elif sira == "k7sona":
        k7 = [i for i in items if i.name.startswith("test_k7_")]
        kalan = [i for i in items if not i.name.startswith("test_k7_")]
        items[:] = kalan + k7
    config._tb_sira_ilk = [i.name for i in items[:3]]  # type: ignore[attr-defined]


def pytest_report_header(config: pytest.Config) -> list[str]:
    return [f"TB_SIRA={os.environ.get('TB_SIRA', '(yok)')}"]


def pytest_collection_finish(session: pytest.Session) -> None:
    ilk = [i.name for i in session.items[:3]]
    son = [i.name for i in session.items[-3:]]
    print(f"\n[r2_sira_plugin] ilk 3: {ilk}\n[r2_sira_plugin] son 3: {son}")
