"""T7-1: degisiklik GERCEKTEN salt dokumantasyon mu? Iki KADEMELI olcum.

Kademe 1 (sefin olctugu): TUM docstring'ler cikarilmis AST dump'lari esit mi.
Kademe 2 (daha DAR, benim ekim): yeni dosyanin MODUL docstring'i eskisiyle
  degistirilirse, kalan HER SEY -- diger docstring'ler DAHIL -- birebir esit mi.
  Kademe 1 tek basina, bir FONKSIYON docstring'inin de degistigini GIZLERDI;
  karar T7-1'i MODUL docstring'iyle sinirli tarif ediyor.
Kademe 3: bayt duzeyinde, degisen satirlarin HEPSI modul docstring araliginda mi.
"""
from __future__ import annotations

import ast
import subprocess
import sys

ESKI_REV, YENI_REV = "0de4546", "HEAD"
YOL = "src/ocr/normalizer.py"


def goster(rev: str) -> str:
    return subprocess.run(
        ["git", "show", f"{rev}:{YOL}"],
        capture_output=True, text=True, encoding="utf-8", check=True,
    ).stdout


def docstringsiz(kaynak: str) -> ast.Module:
    agac = ast.parse(kaynak)
    for d in ast.walk(agac):
        if isinstance(d, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            govde = d.body
            if (govde and isinstance(govde[0], ast.Expr)
                    and isinstance(govde[0].value, ast.Constant)
                    and isinstance(govde[0].value.value, str)):
                d.body = govde[1:] or [ast.Pass()]
    return agac


eski, yeni = goster(ESKI_REV), goster(YENI_REV)
cikis = 0

# --- Kademe 1 -------------------------------------------------------------
d1 = ast.dump(docstringsiz(eski), indent=None)
d2 = ast.dump(docstringsiz(yeni), indent=None)
print(f"KADEME 1  tum docstring'ler cikarilmis AST : {'AYNI' if d1 == d2 else 'FARKLI'}")
print(f"          (dump uzunluklari {len(d1)} / {len(d2)})")
if d1 != d2:
    cikis = 1

# --- Kademe 2 -------------------------------------------------------------
eski_agac, yeni_agac = ast.parse(eski), ast.parse(yeni)
eski_ds = ast.get_docstring(eski_agac, clean=False)
# yeni agacin MODUL docstring'ini eskisiyle degistir
assert isinstance(yeni_agac.body[0], ast.Expr)
assert isinstance(yeni_agac.body[0].value, ast.Constant)
yeni_agac.body[0].value.value = eski_ds
e2 = ast.dump(eski_agac, indent=None)
y2 = ast.dump(yeni_agac, indent=None)
ayni2 = e2 == y2
print(f"KADEME 2  modul docstring GERI konunca AST : {'AYNI' if ayni2 else 'FARKLI'}")
print("          -> yani MODUL docstring'i DISINDA hicbir sey degismedi"
      if ayni2 else "          -> BASKA bir yer de degismis!")
if not ayni2:
    cikis = 1
    # nerede farkli oldugunu goster
    import difflib
    for satir in list(difflib.unified_diff(
            e2.split(","), y2.split(","), lineterm="", n=1))[:40]:
        print("            " + satir)

# --- Kademe 3 -------------------------------------------------------------
# modul docstring'inin KAYNAK aralik satirlari (yeni dosyada)
ds_dugum = yeni_agac.body[0]
ds_bas, ds_son = ds_dugum.lineno, ds_dugum.end_lineno
print(f"KADEME 3  yeni dosyada modul docstring satirlari: {ds_bas}-{ds_son}")
diff = subprocess.run(
    ["git", "diff", "-U0", f"{ESKI_REV}..{YENI_REV}", "--", YOL],
    capture_output=True, text=True, encoding="utf-8", check=True,
).stdout
import re  # noqa: E402
disarda = []
for m in re.finditer(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", diff, re.M):
    bas = int(m.group(1))
    adet = int(m.group(2) or 1)
    if adet and not (ds_bas <= bas and bas + adet - 1 <= ds_son):
        disarda.append((bas, adet))
print(f"          docstring ARALIGI DISINDA degisen hunk: {disarda if disarda else 'YOK'}")
if disarda:
    cikis = 1

print()
print("SONUC: SALT DOKUMANTASYON (modul docstring'i)" if cikis == 0 else "SONUC: DAVRANIS/KOD DEGISIKLIGI VAR")
sys.exit(cikis)
