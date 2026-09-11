"""B2 -- `tests/unit/ocr/test_rapid_engine.py` totoloji / sahte-yesil taramasi (AST).

Her `test_*` fonksiyonu icin: assert sayisi, `pytest.raises` blogu sayisi,
raises govdesindeki ifade sayisi (>1 ise raise'den sonraki ifade hic kosmaz),
`try/except` varligi, sabit-dogru assert (`assert True`, `assert 1`), kendine
esitlik (`x == x`). Sonuc ham tablo olarak basilir; yorum verdict'te.

Kosum: python .agents/tasks/T-006/tester_B/b2_totoloji_tarama.py
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

DEPO = Path(__file__).resolve().parents[4]
HEDEF = DEPO / "tests" / "unit" / "ocr" / "test_rapid_engine.py"


def _raises_bloklari(fn: ast.FunctionDef) -> list[ast.With]:
    out: list[ast.With] = []
    for n in ast.walk(fn):
        if isinstance(n, ast.With):
            for it in n.items:
                src = ast.unparse(it.context_expr)
                if src.startswith("pytest.raises("):
                    out.append(n)
    return out


def _sabit_assert(a: ast.Assert) -> bool:
    t = a.test
    if isinstance(t, ast.Constant):
        return True
    if isinstance(t, ast.Compare) and len(t.comparators) == 1:
        return ast.unparse(t.left) == ast.unparse(t.comparators[0])
    return False


def main() -> int:
    agac = ast.parse(HEDEF.read_text(encoding="utf-8"))
    testler = [n for n in agac.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]
    print(f"dosya: {HEDEF.relative_to(DEPO)}")
    print(f"test fonksiyonu: {len(testler)}")
    print()
    print(f"{'test':62s} {'assert':>6s} {'raises':>6s} {'raises>1':>8s} {'except':>6s} {'sabit':>5s} {'param':>5s}")
    bayraklar: list[str] = []
    toplam_param = 0
    for fn in testler:
        assertler = [n for n in ast.walk(fn) if isinstance(n, ast.Assert)]
        raises = _raises_bloklari(fn)
        cok_ifadeli = [w for w in raises if len(w.body) > 1]
        excepts = [n for n in ast.walk(fn) if isinstance(n, ast.ExceptHandler)]
        sabit = [a for a in assertler if _sabit_assert(a)]
        # parametrize sayisi: her dekorator icin liste uzunlugu (kaba)
        param = 1
        for d in fn.decorator_list:
            if isinstance(d, ast.Call) and ast.unparse(d.func) == "pytest.mark.parametrize":
                arg = d.args[1]
                if isinstance(arg, (ast.List, ast.Tuple)):
                    param *= len(arg.elts)
                elif isinstance(arg, ast.Call) and ast.unparse(arg.func) == "list":
                    param *= 4  # list(OcrLanguage)
        toplam_param += param
        print(f"{fn.name:62s} {len(assertler):6d} {len(raises):6d} {len(cok_ifadeli):8d} {len(excepts):6d} {len(sabit):5d} {param:5d}")
        if not assertler and not raises:
            bayraklar.append(f"{fn.name}: ne assert ne pytest.raises var (ASSERT'SIZ)")
        if sabit:
            bayraklar.append(f"{fn.name}: sabit-dogru / kendine-esit assert: " + "; ".join(ast.unparse(a) for a in sabit))
        for w in cok_ifadeli:
            govde = [ast.unparse(s)[:70] for s in w.body]
            bayraklar.append(f"{fn.name}: pytest.raises govdesi {len(w.body)} ifadeli -> ilk firlatandan sonrakiler KOSMAZ: {govde}")
        for e in excepts:
            bayraklar.append(f"{fn.name}: except govdesi var: {ast.unparse(e)[:100]}")
    print()
    print(f"parametrize ile toplam test ornegi (kaba): {toplam_param}")
    print()
    print("BAYRAKLAR:")
    if not bayraklar:
        print("  (yok)")
    for b in bayraklar:
        print("  - " + b)
    # 'gercek' adli ama gercege dokunmayan test var mi?
    print()
    print("adinda 'gercek' gecen testler:")
    for fn in testler:
        if "gercek" in fn.name.lower():
            print("  -", fn.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
