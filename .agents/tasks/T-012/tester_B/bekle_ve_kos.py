"""Tester-B: oturum kilidi acilana kadar bekler, sonra sarici ile (1) sonda_1b (2) taban real_check kosar. Stdout ASCII.

    python .agents/tasks/T-012/tester_B/bekle_ve_kos.py [azami_dakika]
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from oturum import kilit_bekle, kilitli  # noqa: E402

KOK = Path(__file__).resolve().parents[4]
T = KOK / ".agents" / "tasks" / "T-012"
SARICI = T / "evidence" / "real_check-on-plan-sarici.py"
EV = T / "tester_B_evidence"


def kos(betik: Path | None, cikti: Path) -> int:
    cmd = [sys.executable, str(SARICI)] + ([str(betik)] if betik else [])
    r = subprocess.run(cmd, cwd=str(KOK), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800)
    metin = (r.stdout + r.stderr).replace(str(KOK), "<depo>")
    cikti.write_text(metin + f"\nexit={r.returncode}\n", encoding="utf-8")
    print(f"[bekle_ve_kos] {cikti.name}: rc={r.returncode}")
    return r.returncode


def main() -> int:
    azami = float(sys.argv[1]) if len(sys.argv) > 1 else 60.0
    t0 = time.perf_counter()
    k, n = kilitli()
    print(f"[bekle_ve_kos] baslangic: kilitli={k} ({n}); azami {azami:.0f} dk beklenecek")
    if k and not kilit_bekle(azami * 60):
        print("[bekle_ve_kos] kilit acilmadi; gercek girdi olculemedi"); return 3
    print(f"[bekle_ve_kos] kilit acik ({(time.perf_counter() - t0) / 60:.1f} dk sonra); 20 s sonra basliyor (kullanici yerlessin)")
    time.sleep(20)
    rc1 = kos(T / "tester_B" / "sonda_1b_gercek_girdi.py", EV / "sonda1b-gercek-girdi.txt")
    rc2 = kos(None, EV / "taban-3-real_check-sarici.txt")
    return 0 if rc1 == 0 and rc2 == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
