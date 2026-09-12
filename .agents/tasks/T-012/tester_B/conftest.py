"""Tester-B (T-012) test ortami: offscreen Qt + depo koku sys.path'te. Sefin conftest'ine dokunmaz."""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
KOK = Path(__file__).resolve().parents[4]
if str(KOK) not in sys.path:
    sys.path.insert(0, str(KOK))
