"""ŞEFE AİT — T-012 test ortamı.

Qt testleri ekransız koşar: `QT_QPA_PLATFORM=offscreen` Qt import edilmeden ÖNCE ayarlanır
(pytest-qt `qapp` bunu görür). Gerçek ekran davranışı (odak, tepsi, süreler) yalnız
`.agents/tasks/T-012/real_check.py` ile ayrı süreçte ölçülür.

K7 ("kabuk pipeline bilmez") burada meta_path bariyeriyle ÖLÇÜLMEZ: tam takım koşumunda
`src.capture`/`src.translate` başka testler tarafından zaten import edilmiş olur ve bariyer
ateşleyemez (şef ölçtü: 9 düşen / 4 toplama hatası). K7'nin ölçüsü implementer'ın AST testidir
(`src/ui` kaynağında import listesi). **Dokunma.**
"""
from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
# T-013 Y1 emniyet kemeri: offscreen'de de Win32 dagitici calisir ve RegisterHotKey GERCEK kayit yapar
# (KRT olctu: paralel pytest 1409). Birim testler asla gercek kisayol kaydetmez; servis bu degiskeni gorunce
# `gercek_win32=True` kurulumunu RuntimeError ile reddeder. `real_check.py` ayri surec, degisken yok.
os.environ.setdefault("SUFLOR_GERCEK_KISAYOL_YASAK", "1")
