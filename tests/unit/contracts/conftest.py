"""Depo kokunu sys.path'e ekler.

Testler sozlesmeleri `src.contracts...` yolu ile import eder. `python -m pytest`
zaten calisma dizinini sys.path'e koyar; bu conftest, testlerin depo kokunden
baska bir dizinden koslmasi durumunda da import'un cozulmesini garanti eder.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
