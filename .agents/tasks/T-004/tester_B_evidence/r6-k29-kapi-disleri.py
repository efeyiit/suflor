"""tester_B tur 6 -- K29 kapisinin DISLERI: docstring'e UC tur bayat atif
enjekte edilir (duz ad, satir-sarmali ad, ciplak `_` sonlu on-ek); hem KENDI
bagimsiz taramamin hem sefin `purity_check.py`sinin ucunu de gormesi beklenir."""
import os
import shutil
import tempfile
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]  # tester_B_evidence/ -> T-004 -> tasks -> .agents -> depo koku
S = Path(tempfile.mkdtemp(prefix="tb6_k29_"))
yoksay = shutil.ignore_patterns("__pycache__", "*.pyc")
shutil.copytree(REPO / "src", S / "src", ignore=yoksay)
shutil.copytree(REPO / "tests", S / "tests", ignore=yoksay)
kd = S / ".agents" / "tasks" / "T-004"
kd.mkdir(parents=True)
for f in ("olcu_kiti.py", "conftest.py", "purity_check.py"):
    shutil.copy2(REPO / ".agents/tasks/T-004" / f, kd / f)
tb = kd / "tester_B"
tb.mkdir()
shutil.copy2(REPO / ".agents/tasks/T-004/tester_B/test_karar_uyumu_tur6.py",
             tb / "test_karar_uyumu_tur6.py")

norm = S / "src" / "ocr" / "normalizer.py"
src = norm.read_text(encoding="utf-8")
enjekte = """## K12 -- bos sonuclar

Bkz. `test_k12_bu_test_hic_yok`, `test_k12_sarmali_bayat_
ad_da_yok` ve ciplak on-ek `test_k12_ciplak_onek_`."""
assert src.count("## K12 -- bos sonuclar") == 1
norm.write_text(src.replace("## K12 -- bos sonuclar", enjekte, 1), encoding="utf-8")

env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTHONHASHSEED")}
env["PYTHONIOENCODING"] = "utf-8"
print("=== KENDI BAGIMSIZ TARAMAM (tester_B) ===")
p = subprocess.run(
    [sys.executable, "-m", "pytest", ".agents/tasks/T-004/tester_B/test_karar_uyumu_tur6.py",
     "-q", "--tb=line", "-p", "no:randomly", "-p", "no:cacheprovider", "-k", "k29"],
    cwd=str(S), capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
print(p.stdout[-1800:])
print("=== SEFIN KAPISI (purity_check.py) ===")
p2 = subprocess.run([sys.executable, ".agents/tasks/T-004/purity_check.py"], cwd=str(S),
                    capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
print("exit", p2.returncode)
print(p2.stdout[-1200:])

# --- betigin KENDI karari: BASARI = her iki kapinin da UC ihlali de gormesi ---
BEKLENEN = ("test_k12_bu_test_hic_yok", "test_k12_sarmali_bayat_ad_da_yok", "test_k12_ciplak_onek_")
hata = []
if "1 failed" not in p.stdout:
    hata.append("tester_B taramasi enjekte edilen ihlalleri GORMEDI -- kapim dissiz")
for ad in BEKLENEN:
    if ad not in p.stdout:
        hata.append(f"tester_B taramasi `{ad}`i raporlamadi")
    if ad not in p2.stdout:
        hata.append(f"purity_check `{ad}`i raporlamadi")
if p2.returncode == 0:
    hata.append("purity_check enjeksiyonlu agacta exit 0 verdi -- sefin kapisi dissiz")
print()
print("=== SONUC ===")
print("BASARILI: iki kapi da uc ihlalin ucunu de gordu" if not hata else "BASARISIZ: " + "; ".join(hata))
sys.exit(1 if hata else 0)
