"""T7-1 olcumu: `### K24` bolumunu KENDIM dilimleyip sayarim.

Sefin sayisi 8 / 3 (tur basinda 0/0). Bagimsiz olcum.
"""
from __future__ import annotations

import re
import subprocess
import sys

sys.path.insert(0, ".")
from src.ocr import normalizer as N  # noqa: E402

BASLIK = "### K24 -- K21'in TEK gecerli ifadesi (esdegerlik IPTAL)"


def bolum_al(ds: str, baslik: str) -> str:
    """Bolumu baslik metninden BIR SONRAKI ayni-veya-ust duzey basliga kadar dilimler."""
    i = ds.find(baslik)
    if i < 0:
        return ""
    govde = ds[i + len(baslik):]
    # bir sonraki `## ` ya da `### ` satiri (satir basinda)
    m = re.search(r"^#{2,3} ", govde, re.M)
    return govde[: m.start()] if m else govde


def olc(ds: str, etiket: str) -> None:
    kac_baslik = ds.count(BASLIK)
    bolum = bolum_al(ds, BASLIK)
    print(f"[{etiket}]")
    print(f"  bolum VAR MI          : {'EVET' if bolum else 'HAYIR'}")
    print(f"  baslik metni kac kez  : {kac_baslik}")
    print(f"  bolum satir sayisi    : {len(bolum.splitlines())}")
    print(f"  bolumde 'K28'         : {bolum.count('K28')}")
    print(f"  bolumde '_raw_query_pair': {bolum.count('_raw_query_pair')}")
    print(f"  bolumde 'DEVREDILDI'  : {bolum.count('DEVREDILDI')}")
    print(f"  bolumde 'NEDEN CURUDU': {bolum.count('NEDEN CURUDU')}")
    print(f"  bolumde 'TARIHCE'     : {bolum.count('TARIHCE')}")
    # K28 bolumunde K24'e devralma capasi
    k28 = bolum_al(ds, "## K28 (tur 6) -- miras-uygunluk sorgusunun IKI tarafi da OZGUN bloktan")
    print(f"  K28 bolumu satir      : {len(k28.splitlines())}")
    print(f"  K28'de 'DEVRALINDI'   : {k28.count('DEVRALINDI')}")
    print(f"  K28'de 'K24'          : {k28.count('K24')}")
    print()


olc(N.__doc__ or "", "SIMDIKI (tur 7, HEAD)")

onceki = subprocess.run(
    ["git", "show", "0de4546:src/ocr/normalizer.py"],
    capture_output=True, text=True, encoding="utf-8", check=True,
).stdout
import ast  # noqa: E402
onceki_ds = ast.get_docstring(ast.parse(onceki)) or ""
olc(onceki_ds, "ONCEKI (tur 6, 0de4546)")
