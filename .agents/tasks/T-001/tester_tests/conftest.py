"""Tester'in bagimsiz test paketi icin sys.path guvenligi.

Bu dosya `tests/unit/contracts/conftest.py`'den BAGIMSIZ yazilmistir (o dosya
okunmadan). `.agents/tasks/T-001/tester_tests/` depo agacinin disinda bir
dal oldugu icin pytest, `tests/` altindaki conftest'i otomatik toplamaz;
bu yuzden kendi guvenlik agimizi kuruyoruz.

`python -m pytest` zaten CWD'yi sys.path'e ekler (depo kokunden calistirilirsa
yeterlidir); bu dosya yalnizca farkli bir dizinden calistirilma ihtimaline
karsi bir ek guvencedir.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
