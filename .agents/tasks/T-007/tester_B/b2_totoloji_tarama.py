"""TESTER-B B2 -- teslim test dosyasinin totoloji / sahte-yesil taramasi (AST, kosmaz).

    python .agents/tasks/T-007/tester_B/b2_totoloji_tarama.py

Her test fonksiyonu icin:
  * assert'siz (ne `assert`, ne `pytest.raises`, ne `approx`) -> TOTOLOJI ADAYI
  * sabit assert (`assert True`, `assert 1`) -> SAHTE
  * `pytest.raises` blogunda >1 ifade -> onceki ifade istisnayi uretebilir (yanlis sebeple yesil)
  * `with pytest.raises(...)` `match=` kullanmiyor -> genis (bilgi)
  * beklenen degeri DENETLENEN modulun kendisinden tureten assert (`assert f(x) == f(x)` bicimi)
  * yalniz `__doc__` iceren (davranissiz, damga) testler
  * `hasattr`-yalniz testler
  * private (`local_nmt._...`) erisimi olan testler (mekanizma kancasi -- bilgi)
Sonuc: sayimlar + adlar. Karar verilmez; verdict-B yorumlar.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
DOSYA = KOK / "tests" / "unit" / "translate" / "test_local_nmt.py"


def _asserts(f: ast.FunctionDef) -> list[ast.Assert]:
    return [d for d in ast.walk(f) if isinstance(d, ast.Assert)]


def _raises(f: ast.FunctionDef) -> list[ast.With]:
    out = []
    for d in ast.walk(f):
        if isinstance(d, ast.With):
            for item in d.items:
                if isinstance(item.context_expr, ast.Call) and ast.unparse(item.context_expr.func) == "pytest.raises":
                    out.append(d)
    return out


def _sabit_assert(a: ast.Assert) -> bool:
    return isinstance(a.test, ast.Constant)


def _turetilmis(a: ast.Assert) -> bool:
    """`assert X == Y` ve iki taraf da denetlenen modulun bir cagrisini iceriyorsa (referans bagimsiz degil)."""
    if not isinstance(a.test, ast.Compare) or len(a.test.comparators) != 1:
        return False
    def modul_cagrisi(n: ast.AST) -> bool:
        for d in ast.walk(n):
            if isinstance(d, ast.Call):
                ad = ast.unparse(d.func)
                if ad.startswith(("local_nmt.", "p.", "saglayici(")) or ad in ("cumlelere_bol", "modele_gider", "kaynak_dili_coz", "hedef_dili_coz", "zorunlu_model_dosyalari"):
                    return True
        return False
    return modul_cagrisi(a.test.left) and modul_cagrisi(a.test.comparators[0])


def main() -> int:
    agac = ast.parse(DOSYA.read_text(encoding="utf-8"))
    testler = [d for d in agac.body if isinstance(d, ast.FunctionDef) and d.name.startswith("test_")]
    param_sayisi = 0
    for t in testler:
        n = 1
        for dec in t.decorator_list:
            if isinstance(dec, ast.Call) and ast.unparse(dec.func) == "pytest.mark.parametrize":
                arg = dec.args[1]
                if isinstance(arg, (ast.List, ast.Tuple)):
                    n *= len(arg.elts)
                elif isinstance(arg, ast.Call) and ast.unparse(arg.func) == "list":
                    n *= 4  # list(KAYNAK_BICIMLERI) -> 4 dil
                elif isinstance(arg, ast.BinOp):
                    n *= 8  # HEDEF_BICIMLERI + upper -> 8
                else:
                    n *= 1
        param_sayisi += n

    assertsiz, sabit, cok_ifadeli, matchsiz, turetilmis, damga, hasattr_yalniz, private = [], [], [], [], [], [], [], []
    for t in testler:
        A, R = _asserts(t), _raises(t)
        src = ast.unparse(t)
        if not A and not R and "approx" not in src:
            assertsiz.append(t.name)
        if any(_sabit_assert(a) for a in A):
            sabit.append(t.name)
        for w in R:
            if len(w.body) > 1:
                cok_ifadeli.append(f"{t.name} ({len(w.body)} ifade)")
            call = w.items[0].context_expr
            assert isinstance(call, ast.Call)
            if not any(kw.arg == "match" for kw in call.keywords):
                matchsiz.append(t.name)
        if any(_turetilmis(a) for a in A):
            turetilmis.append(t.name)
        if "__doc__" in src and "translate(" not in src and "LocalNmtProvider(" not in src and "ast.walk" not in src:
            damga.append(t.name)
        if A and all("hasattr" in ast.unparse(a) for a in A) and not R:
            hasattr_yalniz.append(t.name)
        if re.search(r"local_nmt\._[a-z]", src):  # `__doc__` degil, `_varsayilan_fabrika` gibi
            private.append(t.name)

    print(f"dosya: {DOSYA.relative_to(KOK)}")
    print(f"test fonksiyonu: {len(testler)}   parametreli ornek (AST yaklasik): {param_sayisi}; pytest sayimi icin taban-2 kanitina bak (tur 1: 210, tur 2: 255)")
    print()
    for baslik, liste in [
        ("ASSERT'SIZ (totoloji adayi)", assertsiz),
        ("SABIT assert", sabit),
        ("pytest.raises blogunda >1 ifade", cok_ifadeli),
        ("beklenen deger denetlenen modulden turetilmis (assert f(x) == g(x))", turetilmis),
        ("yalniz __doc__ (damga, davranissiz)", damga),
        ("yalniz hasattr", hasattr_yalniz),
        ("private erisim (local_nmt._*)", private),
    ]:
        print(f"{baslik}: {len(liste)}")
        for ad in liste:
            print(f"    {ad}")
    print(f"pytest.raises match= KULLANMAYAN test: {len(set(matchsiz))} / raises kullanan {len({t.name for t in testler if _raises(t)})}  (bilgi: tip yeter, mesaj sozlesme degil)")
    print()
    print("SONUC:", "assert'siz 0, sabit 0" if not assertsiz and not sabit else "BULGU VAR")
    return 0


if __name__ == "__main__":
    sys.exit(main())
