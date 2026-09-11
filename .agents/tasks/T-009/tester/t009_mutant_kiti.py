"""T-009 kor tester -- mutant kiti (AYNA: depo kopyasi, gercek dosyaya dokunmaz).

    python .agents/tasks/T-009/tester/t009_mutant_kiti.py --ayna <bos_dizin>

Her mutant icin ayri bir depo kopyasi (`src/`, `tests/unit/ocr/`, `.agents/tasks/T-009/tester/`)
kurulur, `src/ocr/rapid_engine.py` uzerinde TEK metin degisikligi yapilir ve uc olcu kosulur:
  (a) sefin 119 birim testi              (ayna kokunde `pytest tests/unit/ocr/test_rapid_engine.py`)
  (b) tester'in 41 testi                 (ayna kokunde `pytest .agents/tasks/T-009/tester`)
  (c) gercek model sondasi (dort dil)    (`t009_ayna_sonda.py --kok <ayna>`)
Cikti ASCII; OCR metni yok.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

GERCEK = Path(__file__).resolve().parents[4]
SONDA = Path(__file__).resolve().parent / "t009_ayna_sonda.py"

MUTANTLAR: list[tuple[str, str, str, str]] = [
    # (etiket, aciklama, eski, yeni)
    ("C0", "KONTROL: degisiklik yok (ayna kurulumu dogru mu)", "", ""),
    ("C1", "KONTROL: yalniz yorum satiri (olcu bosa ateslemiyor mu)",
     "# T-009 K1\n", "# T-009 K1 (ayna kontrolu)\n"),
    ("M1", "KOREAN rec dosya adi v4'e (surum etiketi v5 kalir)",
     '"korean_PP-OCRv5_rec_mobile.onnx"),  # T-009 K1', '"korean_PP-OCRv4_rec_mobile.onnx"),  # T-009 K1'),
    ("M2", "JAPAN rec dosya adi v5'e (dosya diskte YOK)",
     '"japan_PP-OCRv4_rec_mobile.onnx"),', '"japan_PP-OCRv5_rec_mobile.onnx"),'),
    ("M3", "Det.ocr_version her dilde v5 (det dosyasi degismedi)",
     '_TESPIT_SURUMU: Final = "PP-OCRv4"', '_TESPIT_SURUMU: Final = "PP-OCRv5"'),
    ("M4", "KOREAN Rec.ocr_version etiketi v4, dosya v5 kalir",
     '(OcrLanguage.KOREAN, "multi", "korean", "PP-OCRv5"),', '(OcrLanguage.KOREAN, "multi", "korean", "PP-OCRv4"),'),
    ("M5", "KOREAN dosya v4 VE etiket v4 (T-009 oncesi durum: tam geri alma)",
     "", ""),  # ozel: iki degisiklik
    ("M6", "ENGLISH rec dosya adi v5'e (en_PP-OCRv5 diskte VAR -- sessiz sizinti sinifi)",
     '"en_PP-OCRv4_rec_mobile.onnx"),', '"en_PP-OCRv5_rec_mobile.onnx"),'),
    ("M7", "KOREAN det dosyasi ch det'e (KRT Y3: ch det Korece bosluklarini yitirir)",
     '(OcrLanguage.KOREAN, "multi_PP-OCRv3_det_mobile.onnx", "korean_PP-OCRv5_rec_mobile.onnx"),',
     '(OcrLanguage.KOREAN, "ch_PP-OCRv4_det_mobile.onnx", "korean_PP-OCRv5_rec_mobile.onnx"),'),
    ("M8", "JAPAN Rec.ocr_version etiketi v5 (kutuphanede JP v5 YOK), dosya v4 kalir -- acik yolda sessiz mi?",
     '(OcrLanguage.JAPAN, "multi", "japan", "PP-OCRv4"),  # v5 YOK', '(OcrLanguage.JAPAN, "multi", "japan", "PP-OCRv5"),  # v5 YOK'),
]


def ayna_kur(hedef: Path) -> None:
    if hedef.exists():
        shutil.rmtree(hedef)
    hedef.mkdir(parents=True)
    shutil.copytree(GERCEK / "src", hedef / "src", ignore=shutil.ignore_patterns("__pycache__"))
    (hedef / "tests" / "unit").mkdir(parents=True)
    shutil.copytree(GERCEK / "tests" / "unit" / "ocr", hedef / "tests" / "unit" / "ocr",
                    ignore=shutil.ignore_patterns("__pycache__"))
    for p in (hedef / "tests" / "unit" / "ocr").iterdir():
        if p.name not in ("conftest.py", "test_rapid_engine.py", "test_conftest_bariyer.py"):
            p.unlink()
    (hedef / ".agents" / "tasks" / "T-004").mkdir(parents=True)
    t = hedef / ".agents" / "tasks" / "T-009" / "tester"
    t.mkdir(parents=True)
    for p in (GERCEK / ".agents" / "tasks" / "T-009" / "tester").glob("*.py"):
        if p.name in ("conftest.py", "test_t009_k11_tablosu.py"):
            shutil.copy(p, t / p.name)


def uygula(kok: Path, etiket: str, eski: str, yeni: str) -> None:
    dosya = kok / "src" / "ocr" / "rapid_engine.py"
    s = dosya.read_text(encoding="utf-8")
    degisiklikler = [(eski, yeni)] if eski else []
    if etiket == "M5":
        degisiklikler = [
            ('"korean_PP-OCRv5_rec_mobile.onnx"),  # T-009 K1', '"korean_PP-OCRv4_rec_mobile.onnx"),  # T-009 K1'),
            ('(OcrLanguage.KOREAN, "multi", "korean", "PP-OCRv5"),', '(OcrLanguage.KOREAN, "multi", "korean", "PP-OCRv4"),'),
        ]
    for e, y in degisiklikler:
        assert s.count(e) == 1, (etiket, e, s.count(e))
        s = s.replace(e, y)
    dosya.write_text(s, encoding="utf-8")


def pytest_say(kok: Path, hedef: str) -> str:
    r = subprocess.run([sys.executable, "-m", "pytest", hedef, "-q", "-p", "no:cacheprovider", "--tb=no", "-o", "console_output_style=classic"],
                       cwd=str(kok), capture_output=True, text=True, timeout=600)
    satirlar = [l for l in r.stdout.splitlines() if l.strip()]
    ozet = satirlar[-1] if satirlar else "(cikti yok)"
    dusenler = [l.split("::", 1)[1].split(" ")[0] for l in r.stdout.splitlines() if l.startswith("FAILED")]
    return f"exit={r.returncode} {ozet}" + (f"  dusen: {', '.join(dusenler)}" if dusenler else "")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ayna", required=True)
    ap.add_argument("--yalniz", default="")
    args = ap.parse_args()
    ayna_kok = Path(args.ayna).resolve()
    secim = set(args.yalniz.split(",")) if args.yalniz else None
    for etiket, aciklama, eski, yeni in MUTANTLAR:
        if secim and etiket not in secim:
            continue
        kok = ayna_kok / etiket
        ayna_kur(kok)
        uygula(kok, etiket, eski, yeni)
        print(f"=== {etiket}: {aciklama}")
        print(f"  (a) birim 119 : {pytest_say(kok, 'tests/unit/ocr/test_rapid_engine.py')}")
        print(f"  (b) tester 41 : {pytest_say(kok, '.agents/tasks/T-009/tester')}")
        r = subprocess.run([sys.executable, str(SONDA), "--kok", str(kok), "--etiket", etiket],
                           capture_output=True, text=True, timeout=600, cwd=str(GERCEK))
        print("  (c) gercek model:")
        for l in (r.stdout or "").splitlines():
            print("      " + l)
        if r.returncode != 0:
            print(f"      exit={r.returncode} stderr: {(r.stderr or '').strip()[-300:]}")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
