"""T-013 demo ekran goruntusu -- GERCEK windows platformu, gercek servis (`calistir` varsayilan yolu).

    python .agents/tasks/T-013/evidence/demo-ekran-goruntusu.py

1. `kabuk_kisayollar.png`: iki kisayol kayitli -> mod dugmelerinde "Ctrl+Alt+D" / "Ctrl+Alt+R", durum satiri bos.
2. `kabuk_kisayol_cakisma.png`: baska surec Ctrl+Alt+D tutarken -> anlik dugmesi "(kısayol yok)", durum satiri
   cakisma metni; Ctrl+Alt+R kayitli. Cocuk surec `try/finally` ile oldurulur. Stdout ASCII.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(KOK))
CIKTI = Path(__file__).resolve().parent

from PySide6 import QtCore, QtWidgets  # noqa: E402

from src.ui.kabuk import AnaPencere  # noqa: E402
from src.ui.uygulama import calistir  # noqa: E402


def goruntu(ad: str) -> int:
    kutu: list[AnaPencere] = []

    def calistirici(app: QtWidgets.QApplication, pencere: AnaPencere) -> int:
        kutu.append(pencere)
        return 0

    calistir([], calistirici=calistirici)
    p = kutu[0]
    for _ in range(20):
        QtWidgets.QApplication.processEvents()
        QtCore.QThread.msleep(20)
    ok = p.grab().save(str(CIKTI / ad))
    durum = p.durum_metni()
    print(f"{ad}: yazildi={ok} anlik='{p.dugme_anlik.text().splitlines()[0].encode('ascii', 'replace').decode()}' "
          f"bolge='{p.dugme_bolge.text().splitlines()[0].encode('ascii', 'replace').decode()}' durum_satiri_bos={durum == ''}")
    p.kapat()
    for _ in range(5):
        QtWidgets.QApplication.processEvents()
    return 0


def main() -> int:
    app = QtWidgets.QApplication(sys.argv)
    goruntu("kabuk_kisayollar.png")
    diger = subprocess.Popen([sys.executable, "-c", "import ctypes,time; u=ctypes.windll.user32; print(u.RegisterHotKey(None,5,0x1|0x2|0x4000,ord('D')), flush=True); time.sleep(30)"],
                             stdout=subprocess.PIPE, text=True)
    try:
        if diger.stdout:
            print(f"baska surec Ctrl+Alt+D tutuyor: kayit={diger.stdout.readline().strip()}")
        goruntu("kabuk_kisayol_cakisma.png")
    finally:
        diger.kill()
    del app
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
