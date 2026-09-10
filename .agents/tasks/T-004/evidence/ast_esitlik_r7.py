"""T7-1'in SALT DOKUMANTASYON oldugunun makine kaniti (T-004, tur 7).

HEAD'deki `src/ocr/normalizer.py` ile calisma kopyasindaki surumun AST'leri,
TUM ciplak string ifadeleri (modul/sinif/fonksiyon docstring'leri VE
oznitelik docstring'leri) CIKARILDIKTAN sonra BIREBIR ayni mi?

Kullanim (depo kokunden):  python .agents/tasks/T-004/evidence/ast_esitlik_r7.py
Cikis: 0 = kod ozdes (yalniz docstring degisti), 1 = KOD DA degismis
"""
from __future__ import annotations

import ast
import subprocess
import sys


def govde_ast(src: str) -> str:
    agac = ast.parse(src)
    for d in ast.walk(agac):
        govde = getattr(d, "body", None)
        if not isinstance(govde, list):
            continue
        d.body = [st for st in govde
                  if not (isinstance(st, ast.Expr) and isinstance(st.value, ast.Constant)
                          and isinstance(st.value.value, str))] or [ast.Pass()]
    return ast.dump(agac, annotate_fields=True, include_attributes=False)


head = subprocess.run(["git", "show", "HEAD:src/ocr/normalizer.py"],
                      capture_output=True, text=True, encoding="utf-8").stdout
simdi = open("src/ocr/normalizer.py", encoding="utf-8").read()

a, b = govde_ast(head), govde_ast(simdi)
print("HEAD  kaynak uzunlugu:", len(head))
print("SIMDI kaynak uzunlugu:", len(simdi))
print("docstring'siz AST BIREBIR AYNI MI:", a == b)
print()
print("Docstring metinlerinde fark VAR MI (beklenen: VAR -- T7-1):",
      ast.get_docstring(ast.parse(head)) != ast.get_docstring(ast.parse(simdi)))
sys.exit(0 if a == b else 1)
