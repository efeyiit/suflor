"""Tester-A tur 2 -- mutant ayirt etme kiti (ayna agaci; depo `src/` DOKUNULMAZ).

    python .agents/tasks/T-008/tester_A/mutant_kiti_tur2.py

Her mutant icin scratchpad altinda `src/` kopyasi kurulur, `_satirlara_bol` /
`_gruplara_bol` / ana siralama tek satirla degistirilir ve DORT test kumesi kosulur:
  impl : tests/unit/ocr/test_satir_birlestirici.py (76) -- ayna icinde (conftest kopyasi)
  ret  : tester_A/test_ret_a_uzun_kutu_koprusu.py (6)
  a1   : tester_A/test_mercek_a.py (84, tur 1 + 2 yeniden nisan)
  a2   : tester_A/test_mercek_a_tur2.py (26)
Tester-A dosyalari `TESTER_A_KOK=<ayna>` ile aynadan import eder (conftest).
Cikti: mutant -> kume basina dusen test sayisi. Kontrol mutanti (M04 `-idx`, davranis-esdeger
olmasi beklenir) 0 dusmeli; gercek mutantlar en az bir kumede dusmeli.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
SCRATCH = Path(os.environ.get("T008_AYNA") or (Path(os.environ["LOCALAPPDATA"]) / "Temp" / "scratch" / "C--Users-pc-Desktop-efe--eviri-uygulamas-" / "d52c967f-bd19-4db3-b5e9-77e6cd08b889" / "scratchpad" / "t008_testerA_mutant_tur2"))
MODUL = "src/ocr/satir_birlestirici.py"
TESTER_A = KOK / ".agents" / "tasks" / "T-008" / "tester_A"

ORIJ_REF = "            if kutu.h < referans.h:\n                referans = kutu\n"
ORIJ_GRUP_SIRA = "    x_sirali = sorted(satir, key=lambda c: (c[1].bbox.x, c[1].bbox.y, c[0]))\n"
ORIJ_ANA_SIRA = "    sirali = sorted(enumerate(blocks), key=lambda c: (c[1].bbox.y, c[1].bbox.x, c[0]))\n"

MUTANTLAR: dict[str, tuple[str, str, str]] = {
    "K-0 kontrol (degisiklik yok)": ("", "", ""),
    "M-ilk: referans = satirin ILK blogu (tur 1 kodu)": (ORIJ_REF, "", ""),
    "M-enuzun: referans = EN UZUN blok": (ORIJ_REF, "            if kutu.h > referans.h:\n                referans = kutu\n", ""),
    "M-son: referans = SON eklenen blok": (ORIJ_REF, "            referans = kutu\n", ""),
    "M-le: bag `<=` (esit yukseklikte son kisa)": (ORIJ_REF, "            if kutu.h <= referans.h:\n                referans = kutu\n", ""),
    "M-xidx: satir ici sira (x, idx) -- y yok": (ORIJ_GRUP_SIRA, "    x_sirali = sorted(satir, key=lambda c: (c[1].bbox.x, c[0]))\n", ""),
    "M-xy: satir ici sira (x, y) -- idx yok": (ORIJ_GRUP_SIRA, "    x_sirali = sorted(satir, key=lambda c: (c[1].bbox.x, c[1].bbox.y))\n", ""),
    "K-04 kontrol: ana sirada -idx (bag ters) -- davranis-esdeger beklenir": (ORIJ_ANA_SIRA, "    sirali = sorted(enumerate(blocks), key=lambda c: (c[1].bbox.y, c[1].bbox.x, -c[0]))\n", ""),
}


def kur(ad: str, eski: str, yeni: str) -> Path:
    ayna = SCRATCH / ad.split(":")[0].split(" ")[0].replace("-", "_")
    if ayna.exists():
        shutil.rmtree(ayna)
    (ayna / "tests" / "unit" / "ocr").mkdir(parents=True)
    shutil.copytree(KOK / "src", ayna / "src", ignore=shutil.ignore_patterns("__pycache__"))
    for f in ("conftest.py", "test_satir_birlestirici.py"):
        shutil.copy(KOK / "tests" / "unit" / "ocr" / f, ayna / "tests" / "unit" / "ocr" / f)
    # conftest `.agents` dizinini arayarak koku bulur: aynada bos bir `.agents` ac
    (ayna / ".agents").mkdir()
    if eski:
        p = ayna / MODUL
        s = p.read_text(encoding="utf-8")
        assert s.count(eski) == 1, (ad, s.count(eski))
        p.write_text(s.replace(eski, yeni), encoding="utf-8")
    return ayna


def kos(cmd: list[str], cwd: Path, env: dict[str, str]) -> tuple[int, str]:
    r = subprocess.run(cmd, cwd=str(cwd), env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, r.stdout + r.stderr


def sayim(cikti: str) -> str:
    satir = [ln for ln in cikti.splitlines() if " passed" in ln or " failed" in ln or "error" in ln.lower()]
    return satir[-1].strip("= ") if satir else cikti.strip().splitlines()[-1] if cikti.strip() else "?"


def main() -> int:
    SCRATCH.mkdir(parents=True, exist_ok=True)
    print(f"ayna koku: {SCRATCH}")
    print()
    sonuc: list[tuple[str, dict[str, str]]] = []
    for ad, (eski, yeni, _) in MUTANTLAR.items():
        ayna = kur(ad, eski, yeni)
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        env.pop("PYTHONPATH", None)
        kumeler: dict[str, str] = {}
        rc, out = kos([sys.executable, "-m", "pytest", "tests/unit/ocr/test_satir_birlestirici.py", "-q", "-p", "no:cacheprovider", "--no-header"], ayna, env)
        kumeler["impl"] = sayim(out)
        env["TESTER_A_KOK"] = str(ayna)
        for kume, dosya in (("ret", "test_ret_a_uzun_kutu_koprusu.py"), ("a1", "test_mercek_a.py"), ("a2", "test_mercek_a_tur2.py")):
            rc, out = kos([sys.executable, "-m", "pytest", str(TESTER_A / dosya), "-q", "-p", "no:cacheprovider", "--no-header", "-rf"], KOK, env)
            kumeler[kume] = sayim(out)
            dusen = [ln.split("::")[-1].split(" ")[0] for ln in out.splitlines() if ln.startswith("FAILED")]
            if dusen:
                kumeler[kume + "_dusen"] = ", ".join(dusen[:12]) + (" ..." if len(dusen) > 12 else "")
        sonuc.append((ad, kumeler))
        print(f"[{ad}]")
        for k, v in kumeler.items():
            print(f"    {k:9s} {v}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
