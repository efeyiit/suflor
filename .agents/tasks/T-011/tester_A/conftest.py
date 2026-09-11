"""Tester-A conftest: depo kokunu sys.path'e ekler (--import-mode=importlib ile kosulur)."""
from __future__ import annotations

import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
if str(KOK) not in sys.path:
    sys.path.insert(0, str(KOK))
