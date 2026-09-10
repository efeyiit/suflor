"""ŞEFE AİT — T-004 ölçü kitinin (`olcu_kiti.py`) içe aktarılabilmesi için.

İmplementer ve üç tester `from olcu_kiti import ...` yazar. Kit
`.agents/tasks/T-004/` altında ve şefe aittir; hiçbir görevin `owns`
kapsamında değildir. Bu dosya da şefe aittir — **dokunma**.

Neden gerekli: depoda `pytest.ini`/`pyproject.toml` yok ve `tests/unit/ocr`
bir paket değil, bu yüzden kitin dizini `sys.path`'e kendiliğinden girmiyor
(ölçüldü: `ModuleNotFoundError: No module named 'olcu_kiti'`). Test dosyası
içine `sys.path.insert` yazmak çalışır ama toplama sırasına bağlıdır: tester
dizini tek başına koşulduğunda patlar, birlikte koşulduğunda çalışır.
"""
from __future__ import annotations

import sys
from pathlib import Path

_KOK = Path(__file__).resolve()
while _KOK.name and not (_KOK / ".agents").is_dir():
    _KOK = _KOK.parent
_KIT = _KOK / ".agents" / "tasks" / "T-004"
for _yol in (str(_KOK), str(_KIT)):
    if _yol not in sys.path:
        sys.path.insert(0, _yol)
