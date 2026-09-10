"""tester_B tur 6 -- TARIHSEL denetim: kararin "DEGISMEDI" dedigi her parca
gercekten degismemis mi?

K28 ONCESI surumle (74256d8, "olcu kiti surum 3; K28 implementer'a gidiyor")
docstring'SIZ govde karsilastirmasi. "docstring buyudu" ile "govde de degisti"
karistirilamasin diye govdeler `ast.unparse` ile normalize edilir.

Basari kosulu (betigin kendi karari): YENI tanim yalniz `_raw_query_pair`,
silinen tanim yok, govdesi degisen tanimlar TAM OLARAK {_group, _normalize_impl}.
"""
from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]  # tester_B_evidence/ -> T-004 -> tasks -> .agents -> depo koku
K28_ONCESI = "74256d8"


def kaynak(rev: str | None) -> str:
    if rev is None:
        return (REPO / "src/ocr/normalizer.py").read_text(encoding="utf-8")
    p = subprocess.run(["git", "show", f"{rev}:src/ocr/normalizer.py"], cwd=str(REPO),
                       capture_output=True, text=True, encoding="utf-8")
    if p.returncode != 0:
        print("git erisilemedi:", p.stderr[:300])
        sys.exit(2)
    return p.stdout


def parca(src: str, ad: str) -> tuple[str, str]:
    for n in ast.parse(src).body:
        if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name == ad:
            k = ast.parse(ast.unparse(n)).body[0]
            b = k.body  # type: ignore[attr-defined]
            if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) \
                    and isinstance(b[0].value.value, str):
                k.body = b[1:]  # type: ignore[attr-defined]
            return ast.unparse(k), (ast.get_docstring(n) or "")
    return "", ""


def adlar(src: str) -> list[str]:
    return [n.name for n in ast.parse(src).body if isinstance(n, (ast.FunctionDef, ast.ClassDef))]


print(f"K28 ONCESI ({K28_ONCESI}) ile SIMDIKI src/ocr/normalizer.py karsilastirmasi")
print("govde = docstring'siz, ast.unparse ile normalize edilmis\n")
o, s = kaynak(K28_ONCESI), kaynak(None)
yeni = sorted(set(adlar(s)) - set(adlar(o)))
silinen = sorted(set(adlar(o)) - set(adlar(s)))
print("YENI tanim:", yeni)
print("SILINEN   :", silinen, "\n")
degisen: list[str] = []
for ad in adlar(o):
    go, do = parca(o, ad)
    gs, ds = parca(s, ad)
    ayni = go == gs
    if not ayni:
        degisen.append(ad)
    ds_not = "ayni" if do == ds else f"buyudu +{len(ds) - len(do)} chr"
    print(f"{ad:26s} govde={'AYNI    ' if ayni else 'DEGISTI '} docstring={ds_not}")

hata = []
if yeni != ["_raw_query_pair"]:
    hata.append(f"YENI tanim beklenen ['_raw_query_pair'] degil: {yeni}")
if silinen:
    hata.append(f"tanim SILINMIS: {silinen}")
if set(degisen) != {"_group", "_normalize_impl"}:
    hata.append(f"govdesi degisen kume beklenenden farkli: {sorted(degisen)}")
print()
print("=== SONUC ===")
print("BASARILI: tur 6'nin kod degisikligi K28'in ilan ettigi UC noktayla sinirli"
      if not hata else "BASARISIZ: " + "; ".join(hata))
sys.exit(1 if hata else 0)
