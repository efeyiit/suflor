"""TESTER-B conftest (T-008) -- K1 bariyerini KENDI BASINA kurar (sefin conftest'ine bagimli degil).

Bariyerin kendisi `tb_bariyer.py`de: import edilince `sys.meta_path`in basina
bulucu koyar ve depo kokunu `sys.path`e ekler. Testler `match="K1 bariyeri"`
ile dogrular (sefin `_T006Bariyer` mesaji da ayni alt dizeyi tasir).
"""
from __future__ import annotations

import tb_bariyer  # noqa: F401  -- import etkisi: bariyer + sys.path kurulumu
