"""TESTER-B conftest (T-007) -- K1 bariyerini KENDI BASINA kurar (sefin conftest'ine bagimli degil).

Bu dizin `tests/unit/translate` disinda oldugu icin sefin
`tests/unit/translate/conftest.py` bariyeri burada YUKLENMEZ. Bariyerin
kendisi `tb_bariyer.py`de: import edilince `sys.meta_path`in basina bulucu
koyar ve depo kokunu `sys.path`e ekler. Testler ayni modul nesnesini
`import tb_bariyer` ile gorur (pytest prepend modu bu dizini sys.path'e koyar).
"""
from __future__ import annotations

import tb_bariyer  # noqa: F401  -- import etkisi: bariyer + sys.path kurulumu
