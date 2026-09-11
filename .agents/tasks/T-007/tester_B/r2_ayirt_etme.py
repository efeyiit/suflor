"""TESTER-B tur 2 -- kacan R2 mutantlari icin AYIRT ETME: mercek-B tur 2 testleri onlari yakaliyor mu?

    TESTER_B_SCRATCH=<dizin> python .agents/tasks/T-007/tester_B/r2_ayirt_etme.py [mutant_id ...]

Ayna agaci `t007_tester_B_ayirt` (models/ yok, yalniz birim kapisi): `src`, `tests`,
fixtures + `tester_B/` kopyalanir (tb_bariyer koku `.agents` olan ilk dizini bulur ->
ayna koku). Her mutant icin (1) teslim test dosyasi, (2) `test_mercek_B_r2.py` kosulur.
Beklenen: teslim `.` (kacti, kitle tutarli), mercek-B r2 `X` (onerilen olcu ayirt ediyor);
mutasyonsuz taban ikisinde de yesil (yanlis pozitif yok).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mutant_kiti as MK  # noqa: E402

DEPO = MK.DEPO
SCRATCH = Path(os.environ.get("TESTER_B_SCRATCH", tempfile.gettempdir()))
KOK = SCRATCH / "t007_tester_B_ayirt"
TESLIM = "tests/unit/translate/test_local_nmt.py"
MERCEK = ".agents/tasks/T-007/tester_B/test_mercek_B_r2.py"
VARSAYILAN = ["R2-K3-16", "R2-K3-17", "R2-K3-18a", "R2-K3-18b", "R2-K3-18c", "R2-K3-18d", "R2-K3-18e", "R2-K3-18f", "R2-K3-18g", "R2-K3-18h",
              "R2-YT-12", "R2-K10-10", "R2-K10-11"]


def _ayna() -> None:
    if KOK.exists():
        shutil.rmtree(KOK, ignore_errors=True)
    yoksay = shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache", ".mypy_cache")
    for ad in ("src", "tests", ".agents/tasks/T-007/fixtures", ".agents/tasks/T-007/tester_B"):
        shutil.copytree(DEPO / ad, KOK / ad, ignore=yoksay)


def _kos(hedef: str) -> tuple[int, str]:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    env.pop("PYTHONIOENCODING", None)
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-rfE", hedef],
                       cwd=str(KOK), capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=600)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def _ozet(c: str) -> str:
    son = [ln for ln in c.strip().splitlines() if ln.strip()][-1:]
    dusen = [ln.split(" - ")[0].replace("FAILED ", "").split("::")[-1][:90] for ln in c.splitlines() if ln.startswith("FAILED")]
    return (son[0] if son else "?") + (("  | " + "; ".join(dusen[:4]) + (" ..." if len(dusen) > 4 else "")) if dusen else "")


def main() -> None:
    secilen = sys.argv[1:] or VARSAYILAN
    MK.KOK = KOK  # kitin _uygula/_geri_al'i bu aynada calissin
    _ayna()
    print(f"ayna: {KOK}")
    print("TABAN (mutasyonsuz):")
    for ad, hedef in (("teslim", TESLIM), ("mercek-B r2", MERCEK)):
        rc, c = _kos(hedef)
        print(f"  {ad:12s} exit={rc}  {_ozet(c)}")
    print()
    for mid in secilen:
        mut = next(m for m in MK.MUTANTLAR if m.mid == mid)
        MK._uygula(mut)
        try:
            sonuc = []
            for ad, hedef in (("teslim", TESLIM), ("mercek-B r2", MERCEK)):
                rc, c = _kos(hedef)
                sonuc.append(f"{ad}: {'X' if rc else '.'} {_ozet(c)}")
        finally:
            MK._geri_al()
        print(f"{mid:10s} {mut.aciklama[:110]}")
        for s in sonuc:
            print(f"    {s}")


if __name__ == "__main__":
    main()
