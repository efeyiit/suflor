"""Tester-B tur 2: K5 balon sonrasi kapat() -> Shell ikon kalintisi var mi (gercek tepsi, kilitten bagimsiz). Depo kokunden kosulur."""
import ctypes, os, sys, time
from ctypes import wintypes
from pathlib import Path
os.environ.pop("QT_QPA_PLATFORM", None)
KOK = Path(os.getcwd()); sys.path.insert(0, str(KOK)); sys.path.insert(0, str(KOK / ".agents/tasks/T-012/tester_B"))
from PySide6 import QtCore, QtGui, QtWidgets
from sonda_2a_tur2_kilitten_bagimsiz import ikon_rect, tepsi_hwnd, surec_pencereleri, sinif, bekle
from src.ui.kabuk import AnaPencere
app = QtWidgets.QApplication(sys.argv); app.setQuitOnLastWindowClosed(False)
ekran = QtGui.QGuiApplication.primaryScreen()

def durum(etiket, p):
    print(f"  {etiket}: Shell ikon rect={ikon_rect()} tray-hwnd sayisi={sum(1 for h in surec_pencereleri() if 'TrayIcon' in sinif(h))} QSystemTrayIcon.isVisible={p.tepsi.ikon.isVisible()}")

for balon in (False, True):
    AnaPencere._balon_gosterildi = not balon
    print(f"senaryo balon={balon}")
    p = AnaPencere(ekran); p.show(); bekle(300)
    durum("taze", p)
    p.tepsiye_al(); bekle(400); durum("tepsiye_al", p)
    p.kapat(); bekle(300); durum("kapat +0.3s", p)
    for t in (1, 3, 7, 10):
        bekle(1000 if t == 1 else 2000 if t == 3 else 4000 if t == 7 else 3000); durum(f"kapat +{t}s", p)
    del p; bekle(300)
    print(f"  del sonrasi: Shell ikon rect={ikon_rect()}")
