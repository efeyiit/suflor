"""Mercek B testlerinin (`test_mercek_B.py`) AYIRT ETME GUCU -- kitin mutantlarina karsi.

`mutant_kiti.py`nin tanimlarini yeniden kullanir; ayni ayna agacinda secili
mutantlari uygular ve YALNIZ `.agents/tasks/T-006/tester_B` testlerini kosar.
Amac: bes kapidan kacan (ya da yalniz zayif yakalanan) mutantlari mercek B'nin
kendi testleri yakaliyor mu -- olculur (PROTOKOL 4.6/10: olcunun ateslendigi
gosterilmeden "kacan yok" yazilamaz).

Kosum: python .agents/tasks/T-006/tester_B/mercekB_mutant_ayirt_etme.py [mutant_id ...]
Varsayilan kume: kacma adayi + birkac yakalanan karsilastirma.
"""
from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

BURASI = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("mutant_kiti", BURASI / "mutant_kiti.py")
assert spec is not None and spec.loader is not None
mk = importlib.util.module_from_spec(spec)
sys.modules["mutant_kiti"] = mk
spec.loader.exec_module(mk)

VARSAYILAN = ["M25", "M25b", "M26", "M28a", "M28b", "M28c", "M32", "M29", "M30", "M31", "C01", "C02", "C03", "C04"]
TESTER_B_REL = ".agents/tasks/T-006/tester_B"


def main() -> None:
    secilen = sys.argv[1:] or VARSAYILAN
    mk._ayna_kur()
    hedef = mk.KOK / TESTER_B_REL
    if hedef.exists():
        shutil.rmtree(hedef)
    shutil.copytree(BURASI, hedef, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    mk._geri_al()
    argv = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", TESTER_B_REL]
    print(f"ayna: {mk.KOK}")
    rc, ozet, _ = mk._kapi_kos(argv)
    print(f"TABAN mercek B: exit={rc}  {ozet.strip().splitlines()[-1][:80]}")
    if rc != 0:
        raise SystemExit("taban gecmedi")
    print()
    for mut in mk.MUTANTLAR:
        if mut.mid not in secilen:
            continue
        mk._uygula(mut)
        try:
            rc, ozet, _ = mk._kapi_kos(argv)
            son = ozet.strip().splitlines()[-1][:80] if ozet.strip() else ""
            failed = [ln.strip()[:140] for ln in ozet.splitlines() if ln.startswith("FAILED")]
            etiket = "KACTI" if rc == 0 else "YAKALANDI"
            if mut.kontrol:
                etiket += " (kontrol: kacmali)" if rc == 0 else " *** KONTROL YAKALANDI = YANLIS POZITIF ***"
            print(f"{mut.mid:5s} mercekB={'X' if rc else '.'}  {etiket}  -- {mut.aciklama}")
            print(f"       {son}")
            for f in failed[:4]:
                print(f"       | {f}")
        finally:
            mk._geri_al()


if __name__ == "__main__":
    main()
