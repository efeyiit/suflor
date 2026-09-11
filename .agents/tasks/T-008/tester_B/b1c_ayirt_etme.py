"""B1c -- AYIRT ETME (tur 2): kacan 3 mutant (M23, M37, M40) x {teslim testleri, mercek-B testleri}
ayna agacinda. Beklenen: teslim `.` (kitle tutarli), mercek-B `X` (hazir olcu var);
mutasyonsuz tabanda ikisi de gecer (yanlis pozitif yok).
Kosum: T008_TB_SCRATCH=<dizin> python .agents/tasks/T-008/tester_B/b1c_ayirt_etme.py
"""
from __future__ import annotations
import os, shutil, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import mutant_kiti as kit

KACANLAR = ("M23", "M37", "M40")  # tur 2: M41 yakalaniyor (T2-2), M37 (-idx) kaciyor
TB = ".agents/tasks/T-008/tester_B"

def kos(argv):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1"); env.pop("PYTHONIOENCODING", None)
    r = subprocess.run(argv, cwd=str(kit.KOK), capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=600)
    son = [l for l in (r.stdout or "").splitlines() if l.strip()][-1:] or [""]
    return r.returncode, son[0][:90], [l.strip()[:120] for l in (r.stdout or "").splitlines() if l.startswith("FAILED")]

kit._ayna_kur()
shutil.copytree(kit.DEPO / TB, kit.KOK / TB, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
TESLIM = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-rfE", kit.TEST]
MERCEK = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-rfE", TB, "--deselect",
          f"{TB}/test_mercek_B.py::test_b5_sefin_bariyeri_teslim_dosyasi_kosarken_her_testte_aktif"]  # ayri surec testi aynada da calisir ama yavas; disarida
print(f"ayna: {kit.KOK}")
rc1, s1, _ = kos(TESLIM); rc2, s2, _ = kos(MERCEK)
print(f"TABAN  teslim exit={rc1} ({s1}) | mercek-B exit={rc2} ({s2})")
assert rc1 == 0 and rc2 == 0, "taban gecmedi"
print()
print(f"{'mid':5s} {'teslim':8s} {'mercek-B':9s} dusen mercek-B testleri")
for mid in KACANLAR:
    mut = next(m for m in kit.MUTANTLAR if m.mid == mid)
    kit._uygula(mut)
    try:
        rc1, _, _ = kos(TESLIM); rc2, _, dus = kos(MERCEK)
        print(f"{mid:5s} {'X' if rc1 else '.':8s} {'X' if rc2 else '.':9s} {'; '.join(d.split('::')[-1] for d in dus)}")
    finally:
        kit._geri_al()
