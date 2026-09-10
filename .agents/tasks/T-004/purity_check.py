"""Normalizer saflik denetimi (Ortam Ajani urunu).

src/ocr/normalizer.py ve src/ocr/presets.py tamamen saf olmali:
I/O yok, global mutable durum yok, rastgelelik yok, zaman bagimliligi yok.
Kabul komutlarindan biridir; ajan yorumuna birakilmaz.

Ayrica determinizmi SURECLER ARASI dogrular: farkli PYTHONHASHSEED
degerleriyle ayni ciktinin uretildigini kontrol eder (set/dict iterasyon
sirasina bagimli kod bu testte yakalanir).

Kullanim:  python .agents/tasks/T-004/purity_check.py
Cikis:     0 = temiz, 1 = ihlal var
"""
from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
TARGETS = [REPO / "src" / "ocr" / "normalizer.py", REPO / "src" / "ocr" / "presets.py"]

FORBIDDEN_IMPORTS = {
    "os", "io", "sys", "random", "time", "datetime", "pathlib", "socket",
    "requests", "httpx", "urllib", "subprocess", "threading", "asyncio",
    "sqlite3", "logging", "tempfile", "shutil", "pickle", "secrets",
}
FORBIDDEN_CALLS = {"open", "input", "eval", "exec", "compile", "__import__"}


def check_static(path: Path, errs: list[str]) -> None:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    for node in ast.walk(tree):
        # yasak import
        mods: list[str] = []
        if isinstance(node, ast.Import):
            mods = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and not node.level:
            mods = [node.module or ""]
        for m in mods:
            if m.split(".")[0] in FORBIDDEN_IMPORTS:
                errs.append(f"{path.name}:{node.lineno}  yasak import -> {m}")

        # yasak cagri
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in FORBIDDEN_CALLS:
                errs.append(f"{path.name}:{node.lineno}  yasak cagri -> {node.func.id}()")

    # modul duzeyinde mutable global
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for t in targets:
                if not isinstance(t, ast.Name):
                    continue
                val = node.value
                if t.id == "__all__":
                    continue  # evrensel deyim, mutasyona ugramaz
                if isinstance(val, (ast.List, ast.Dict, ast.Set)):
                    errs.append(
                        f"{path.name}:{node.lineno}  modul duzeyinde MUTABLE global -> "
                        f"{t.id} ({type(val).__name__}); tuple/frozenset kullan")


def check_cross_process_determinism(errs: list[str]) -> None:
    """Ayni girdi, farkli PYTHONHASHSEED -> ayni cikti olmali."""
    snippet = (
        "import sys; sys.path.insert(0, r'%s')\n"
        "from src.contracts.models import TextBlock, Rect, OcrPreset\n"
        "from src.ocr.normalizer import normalize\n"
        "bs = [TextBlock(text='satir %%d' %% i, bbox=Rect(0, i*20, 100, 18),\n"
        "                confidence=0.9) for i in range(12)]\n"
        "out = normalize(bs, OcrPreset.DIALOGUE)\n"
        "print('|'.join(f'{s.text}~{s.bbox.x},{s.bbox.y}~{s.source_blocks}' for s in out))\n"
    ) % str(REPO)

    outs = []
    for seed in ("0", "1", "12345"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        r = subprocess.run([sys.executable, "-c", snippet], cwd=str(REPO),
                           capture_output=True, text=True, env=env)
        if r.returncode != 0:
            errs.append(f"determinizm kosumu HATA verdi (PYTHONHASHSEED={seed}): "
                        f"{r.stderr.strip()[:200]}")
            return
        outs.append(r.stdout.strip())

    if len(set(outs)) != 1:
        errs.append("SURECLER ARASI DETERMINIZM IHLALI: farkli PYTHONHASHSEED "
                    "degerleri farkli cikti uretti (set/dict iterasyon sirasina "
                    "bagimlilik). Ciktilar: " + " || ".join(o[:120] for o in outs))



def _k29_scan(doc: str, defined: set[str]) -> list[tuple[str, str, str]]:
    """K29 cekirdegi: docstring metnindeki `test_*` atiflarini denetler.

    Donus: (ad, tur, sorun) uclileri. Kurallar:
      - satir-sonunda `_` ile bolunmus adlar taramadan ONCE birlestirilir
        (docstring satir sarmasi adi `_` uzerinden bolebilir);
      - `test_x.py` bicimindeki dosya adlari dislanir;
      - `test_x_*` -> onek: en az bir test bu onekle baslamali;
      - `_` ile biten CIPLAK ad -> ihlal (ya tam ad yaz ya `*` ekle);
      - diger her ad -> `def <ad>(` olarak var olmali.
    """
    import re as _re
    doc = _re.sub(r"_[ \t]*\n[ \t]*", "_", doc)      # kuyruk `_` satir sonunda
    doc = _re.sub(r"[ \t]*\n[ \t]*_", "_", doc)      # kuyruk `_` satir basinda
    doc = _re.sub(r"\btest_\w+\.py\b", " ", doc)
    found: list[tuple[str, str, str]] = []
    for m in _re.finditer(r"\b(test_\w+)(\*?)", doc):
        name, star = m.group(1), m.group(2)
        if star:
            if not any(d.startswith(name) for d in defined):
                found.append((name + "*", "ONEK", "hicbir test bu onekle baslamiyor"))
        elif name.endswith("_"):
            found.append((name, "CIPLAK-ONEK", "'_' ile biten ad: ya tam ad yaz ya '*' ekle"))
        elif name not in defined:
            found.append((name, "AD", "test_normalizer.py'de yok"))
    return found


def selftest_k29() -> None:
    """K29 kapisinin kendini sinamasi: bilinen bozuk atiflar yakalanmali, dogrular gecmeli."""
    defined = {"test_a_b", "test_k26_uzun_ad_formu_dogru", "test_pre_x"}
    bad = ("Bkz `test_k26_uzun_ad_formu_\n    yanlis`. Ayrica test_yok_bu. Ve test_ciplak_ onek, "
           "test_a_b, test_pre_*, test_normalizer.py, test_hic_*.")
    got = {(n, t) for n, t, _ in _k29_scan(bad, defined)}
    want = {("test_k26_uzun_ad_formu_yanlis", "AD"), ("test_yok_bu", "AD"),
            ("test_ciplak_", "CIPLAK-ONEK"), ("test_hic_*", "ONEK")}
    assert got == want, f"K29 kendini-sinama KIRIK: {got} != {want}"
    good = "Bkz `test_k26_uzun_ad_formu_\n    dogru`. Ayrica test_a_b (test_normalizer.py), test_pre_*."
    assert _k29_scan(good, defined) == [], f"K29 kendini-sinama yanlis pozitif: {_k29_scan(good, defined)}"
    # satir BASINDA `_` ile sarma da yanlis pozitif uretmemeli (KRT 2. gecis D1)
    good2 = "Bkz test_pre\n    _x tam adi."
    assert _k29_scan(good2, {"test_pre_x"}) == [], f"K29 satir-basi sarma yanlis pozitif: {_k29_scan(good2, {"test_pre_x"})}"


def check_docstring_test_refs(errs: list[str]) -> None:
    """K29: docstring'lerde anilan her `test_*` adi test dosyasinda gercekten var olmali."""
    import re as _re
    test_src = (REPO / "tests" / "unit" / "ocr" / "test_normalizer.py").read_text(encoding="utf-8")
    defined = set(_re.findall(r"^def (test_\w+)\(", test_src, _re.M))
    seen: set[tuple[str, str]] = set()
    for path in TARGETS:
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src, filename=str(path))
        docs: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                d = ast.get_docstring(node)
                if d:
                    docs.append(d)
                # attribute docstring: Assign/AnnAssign'i izleyen ciplak string sabiti
                # (ast.get_docstring bunlari GORMEZ -- KRT 2. gecis D1)
                body = getattr(node, "body", [])
                for i, st in enumerate(body[:-1]):
                    nx = body[i + 1]
                    if (isinstance(st, (ast.Assign, ast.AnnAssign))
                            and isinstance(nx, ast.Expr)
                            and isinstance(nx.value, ast.Constant)
                            and isinstance(nx.value.value, str)):
                        docs.append(nx.value.value)
        for doc in docs:
            for name, kind, why in _k29_scan(doc, defined):
                if (path.name, name) in seen:
                    continue
                seen.add((path.name, name))
                pos = src.find(name.rstrip("*")[:16])
                ln = src[:pos].count("\n") + 1 if pos >= 0 else getattr(node, "lineno", 1)
                errs.append(f"{path.name}:{ln}  docstring HAYALI test aniyor ({kind}) -> {name} [K29: {why}]")

def main() -> None:
    selftest_k29()
    if "--selftest" in sys.argv[1:]:
        print("K29 kendini-sinama: TEMIZ"); sys.exit(0)
    errs: list[str] = []

    for p in TARGETS:
        if not p.exists():
            errs.append(f"dosya yok: {p.relative_to(REPO)}")
        else:
            try:
                check_static(p, errs)
            except SyntaxError as exc:
                errs.append(f"{p.name}: sozdizimi hatasi -> {exc}")

    check_docstring_test_refs(errs)

    if not errs:
        check_cross_process_determinism(errs)

    print(f"denetlenen: {', '.join(p.name for p in TARGETS)}")
    if errs:
        print(f"\nIHLAL ({len(errs)}):")
        for e in errs:
            print(f"  {e}")
        sys.exit(1)

    print("\nTEMIZ: saf, mutable global yok, surecler arasi deterministik")
    sys.exit(0)


if __name__ == "__main__":
    main()
