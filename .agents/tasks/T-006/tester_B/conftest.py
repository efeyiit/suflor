"""TESTER-B conftest -- K1 bariyerini KENDI BASINA kurar (sefin conftest'ine bagimli degil).

Bu dizin `tests/unit/ocr` disinda oldugu icin sefin `tests/unit/ocr/conftest.py`
bariyeri burada YUKLENMEZ. Bariyerin kendisi `tb_bariyer.py`de: import edilince
`sys.meta_path`in basina bulucu koyar. Testler ayni modul nesnesini
`import tb_bariyer` ile gorur (pytest prepend modu bu dizini sys.path'e koyar).
"""
from __future__ import annotations

import tb_bariyer  # noqa: F401  -- import etkisi: bariyer + sys.path kurulumu
