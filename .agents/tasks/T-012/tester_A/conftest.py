"""Tester-A conftest (T-012): depo kokunu sys.path'e ekler, Qt'yi offscreen'e alir.

Kosum: python -m pytest .agents/tasks/T-012/tester_A -q -p no:cacheprovider --import-mode=importlib
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

KOK = Path(__file__).resolve().parents[4]
if str(KOK) not in sys.path:
    sys.path.insert(0, str(KOK))
