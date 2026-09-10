"""tester_B tur 6 -- yeni karar-uyumu dosyasinin DISLERI: her mutant agacinda
`test_karar_uyumu_tur6.py` kosar, kirilan test adlari listelenir.
(`git`-tabanli tarihsel testler mutant agacinda SKIP olur -- depo kopyasi degil.)"""
import os
import shutil
import tempfile
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]  # tester_B_evidence/ -> T-004 -> tasks -> .agents -> depo koku
SCRATCH = Path(tempfile.mkdtemp(prefix="tb6_dis_"))

metin = (REPO / ".agents/tasks/T-004/tester_B/test_k28_mutant_sondasi_tur6.py").read_text(encoding="utf-8")
ns: dict = {}
exec(metin[metin.index("_SORGU_SATIRI = "): metin.index("KIT_GORMEZ = ")], ns)
MUT = ns["MUTANTLAR"]

yoksay = shutil.ignore_patterns("__pycache__", "*.pyc")
print("mutant agacinda `test_karar_uyumu_tur6.py` -- kirilan testler\n")
for ad in ["KONTROL", *MUT]:
    hedef = SCRATCH / ad
    hedef.mkdir()
    shutil.copytree(REPO / "src", hedef / "src", ignore=yoksay)
    shutil.copytree(REPO / "tests", hedef / "tests", ignore=yoksay)
    kd = hedef / ".agents" / "tasks" / "T-004"
    kd.mkdir(parents=True)
    for f in ("olcu_kiti.py", "conftest.py"):
        shutil.copy2(REPO / ".agents/tasks/T-004" / f, kd / f)
    tb = kd / "tester_B"
    tb.mkdir()
    shutil.copy2(REPO / ".agents/tasks/T-004/tester_B/test_karar_uyumu_tur6.py",
                 tb / "test_karar_uyumu_tur6.py")
    norm = hedef / "src" / "ocr" / "normalizer.py"
    src = norm.read_text(encoding="utf-8")
    if ad != "KONTROL":
        aranan, yerine = MUT[ad]
        assert src.count(aranan) == 1, ad
        norm.write_text(src.replace(aranan, yerine), encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTHONHASHSEED")}
    env["PYTHONIOENCODING"] = "utf-8"
    p = subprocess.run(
        [sys.executable, "-m", "pytest", ".agents/tasks/T-004/tester_B/test_karar_uyumu_tur6.py",
         "-q", "--tb=no", "-rf", "-p", "no:randomly", "-p", "no:cacheprovider"],
        cwd=str(hedef), capture_output=True, text=True, encoding="utf-8", errors="replace", env=env,
    )
    kirik = sorted({l.split(" ", 1)[1].split(" ")[0].split("::", 1)[-1]
                    for l in p.stdout.splitlines() if l.startswith("FAILED ")})
    ozet = [l for l in p.stdout.splitlines() if " passed" in l or " failed" in l]
    print(f"{ad:30s} {ozet[-1] if ozet else p.stdout[-200:]}")
    for t in kirik:
        print("      -", t)
