"""Tester-A sonda 02b -- O-A2 duzeltme onerisi dogrulamasi (alt sinifla; src/ui degismez).

    python .agents/tasks/T-012/tester_A/sonda_a_02b_duzeltme_onerisi.py [offscreen|windows]     (depo kokunden; stdout ASCII)

`Duzeltilmis.showEvent -> _konumlan()` her iki platformda 26x52; `DuzeltilmisB` (hide sonrasi 0 ms ertelemeli) ISE YARAMAZ.
"""
import os, sys
os.environ["QT_QPA_PLATFORM"] = sys.argv[1] if len(sys.argv) > 1 else "offscreen"
sys.path.insert(0, os.getcwd())
from PySide6 import QtCore, QtWidgets
from PySide6.QtGui import QGuiApplication
from src.ui.kenar_sekmesi import KenarSekmesi

def dongu(ms):
    l = QtCore.QEventLoop(); QtCore.QTimer.singleShot(ms, l.quit); l.exec()

class Duzeltilmis(KenarSekmesi):
    def showEvent(self, e):
        self._konumlan()  # oneri: gosterilirken durumdan geometri yeniden uygulanir
        super().showEvent(e)

class DuzeltilmisB(KenarSekmesi):
    def closeEvent(self, e):
        super().closeEvent(e)
    def hideEvent(self, e):
        super().hideEvent(e)
        QtCore.QTimer.singleShot(0, self._konumlan)  # alternatif: hide sonrasi 0 ms'de yeniden uygula

app = QtWidgets.QApplication([]); app.setQuitOnLastWindowClosed(False)
e = QGuiApplication.primaryScreen()
konum = [QtCore.QPoint(-10000, -10000)]
for K in (KenarSekmesi, Duzeltilmis, DuzeltilmisB):
    for yol in ("close", "closeAllWindows"):
        s = K(e, acilma_ms=20, kapanma_ms=30, yoklama_ms=10, imlec_konumu=lambda: konum[0]); s.show(); dongu(20)
        kapali = s.frameGeometry(); konum[0] = kapali.center(); dongu(120); assert s.acik
        konum[0] = QtCore.QPoint(-10000, -10000)
        s.close() if yol == "close" else QtWidgets.QApplication.closeAllWindows()
        dongu(50); s.show(); dongu(50)
        print(f"{K.__name__:14s} {yol:16s} yeniden show boyut={s.frameGeometry().width()}x{s.frameGeometry().height()} {'ok' if s.frameGeometry().size()==kapali.size() else 'BAYAT'}")
        s.hide(); del s
