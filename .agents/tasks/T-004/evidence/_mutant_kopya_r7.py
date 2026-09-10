"""T-004 tur 7 -- M15 mutant kosumlari icin GECICI DEPO KOPYASI.

Mutantlar depoda DEGIL, `tempfile` ile acilan bir kopyada kurulur; kosum
bitince kopya SILINIR. Depo dosyalarina hicbir asamada dokunulmaz.

Kopyaya giren: `src/`, `tests/` ve kitin calisabilmesi icin
`.agents/tasks/T-004/{olcu_kiti.py, conftest.py, purity_check.py}`
(kitin `conftest.py`'si kokU `.agents` dizinini arayarak bulur).
"""
from __future__ import annotations

import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

DEPO = Path(__file__).resolve().parents[4]
KIT_DOSYALARI = ("olcu_kiti.py", "conftest.py", "purity_check.py")
SORGU_SATIRI = "*_raw_query_pair(tail, nxt, blocks), params, ignore_length=True"


@contextmanager
def kopya() -> Iterator[Path]:
    kok = Path(tempfile.mkdtemp(prefix="t004-tur7-mutant-"))
    try:
        for ad in ("src", "tests"):
            shutil.copytree(DEPO / ad, kok / ad,
                            ignore=shutil.ignore_patterns("__pycache__"))
        hedef = kok / ".agents" / "tasks" / "T-004"
        hedef.mkdir(parents=True)
        for ad in KIT_DOSYALARI:
            shutil.copy2(DEPO / ".agents" / "tasks" / "T-004" / ad, hedef / ad)
        yield kok
    finally:
        shutil.rmtree(kok, ignore_errors=True)
