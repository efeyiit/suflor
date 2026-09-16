"""Pipeline testleri ekransiz (offscreen) Qt ile kosar; gercek motor yok (Fake* + K1 bariyerleri)."""
from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
