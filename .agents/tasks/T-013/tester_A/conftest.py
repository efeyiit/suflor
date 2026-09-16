"""Tester-A conftest (T-013): depo kokunu sys.path'e ekler, Qt'yi offscreen'e alir, gercek Win32 kisayol kaydini yasaklar.

Kosum: python -m pytest .agents/tasks/T-013/tester_A -q -p no:cacheprovider --import-mode=importlib

`SUFLOR_GERCEK_KISAYOL_YASAK=1`: offscreen'de de `RegisterHotKey` gercek kayit yapar (KRT k1); servis bu degiskeni
gorunce `gercek_win32=True` kurulumunu reddeder. Mercek testleri yalniz sahte fn'lerle calisir; tek Win32 dokunusu
`PostThreadMessageW(kendi thread, WM_HOTKEY)` (surec ici, kayit yok) ve `altgr_karakteri` (saf `ToUnicodeEx` sorgusu).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["SUFLOR_GERCEK_KISAYOL_YASAK"] = "1"

KOK = Path(__file__).resolve().parents[4]
if str(KOK) not in sys.path:
    sys.path.insert(0, str(KOK))
