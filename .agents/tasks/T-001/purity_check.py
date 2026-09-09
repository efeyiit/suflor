"""Sozlesme saflik denetimi (Ortam Ajani urunu).

src/contracts/ hicbir somut kutuphaneyi import etmemeli. Sozlesmeler somut
bir teknolojiye baglanirsa, o teknolojiyi degistirmek tum ajanlarin isini
kirar. Bu denetim makineyle calisir; ajan yorumuna birakilmaz.

Kullanim:  python .agents/tasks/T-001/purity_check.py
Cikis:     0 = temiz, 1 = ihlal var
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
TARGET = REPO / "src" / "contracts"

# Yalnizca bunlara izin var: stdlib + numpy (sadece tip anotasyonu icin)
ALLOWED_TOP = {
    "abc", "dataclasses", "enum", "typing", "types", "collections",
    "__future__", "numpy", "np", "pathlib", "datetime", "decimal",
}

# Bunlar kesinlikle yasak - somut teknoloji baglantisi
FORBIDDEN = {
    "onnxruntime", "rapidocr_onnxruntime", "paddleocr", "cv2",
    "PySide6", "PyQt5", "PyQt6", "qtpy",
    "sqlite3", "sqlalchemy",
    "ctranslate2", "llama_cpp", "transformers", "torch",
    "requests", "httpx", "aiohttp", "urllib",
    "mss", "win32api", "win32gui", "pywintypes",
}


def main() -> None:
    if not TARGET.exists():
        print(f"IHLAL: {TARGET} yok - sozlesme dosyalari yazilmamis")
        sys.exit(1)

    files = sorted(TARGET.rglob("*.py"))
    if not files:
        print(f"IHLAL: {TARGET} altinda .py dosyasi yok")
        sys.exit(1)

    violations: list[str] = []
    for f in files:
        try:
            tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
        except SyntaxError as exc:
            violations.append(f"{f.name}: sozdizimi hatasi -> {exc}")
            continue

        for node in ast.walk(tree):
            mods: list[str] = []
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.level:      # goreli import (from . import x) serbest
                    continue
                mods = [node.module or ""]

            for m in mods:
                top = m.split(".")[0]
                if not top:
                    continue
                if top in FORBIDDEN:
                    violations.append(
                        f"{f.name}:{node.lineno}  YASAK somut kutuphane -> {m}")
                elif top not in ALLOWED_TOP:
                    violations.append(
                        f"{f.name}:{node.lineno}  izinsiz import -> {m} "
                        f"(izinliler: stdlib + numpy)")

    print(f"denetlenen dosya: {len(files)}")
    for f in files:
        print(f"  - {f.relative_to(REPO)}")

    if violations:
        print(f"\nIHLAL ({len(violations)}):")
        for v in violations:
            print(f"  {v}")
        sys.exit(1)

    print("\nTEMIZ: sozlesmeler hicbir somut kutuphaneye bagli degil")
    sys.exit(0)


if __name__ == "__main__":
    main()
