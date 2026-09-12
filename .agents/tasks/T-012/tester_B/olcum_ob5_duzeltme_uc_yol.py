"""Tester-B tur 2: O-B5 duzeltmesinin del+gc / deleteLater+del / kapat+del yollarinda cokme uretmedigi. Offscreen."""
import gc, sys, weakref, os
os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, os.getcwd())
from PySide6 import QtCore, QtWidgets
from PySide6.QtTest import QTest
from shiboken6 import isValid
from src.ui.kabuk import AnaPencere
app = QtWidgets.QApplication([]); app.setQuitOnLastWindowClosed(False)
def bekle(ms):
    son = QtCore.QDeadlineTimer(ms)
    while not son.hasExpired(): app.processEvents(); QTest.qWait(5)
# duzeltmeyle del+gc yolu: cift silme / cokme yok mu
for yol in ("del_gc", "deleteLater_del", "kapat_sonra_del"):
    p = AnaPencere(tepsi_kullanilabilir=True); p.show(); bekle(50); p.kenara_al(); bekle(100)
    p.destroyed.connect(p.sekme.deleteLater)
    wr = weakref.ref(p.sekme)
    if yol == "del_gc": del p; gc.collect(); bekle(200)
    elif yol == "deleteLater_del": p.deleteLater(); del p; bekle(300); gc.collect(); bekle(100)
    else: p.kapat(); del p; gc.collect(); bekle(200)
    s = wr()
    print(f"{yol}: sekme sarmalayici canli={s is not None} cpp gecerli={bool(s is not None and isValid(s))} gorunur ust-duzey={[type(w).__name__ for w in QtWidgets.QApplication.topLevelWidgets() if w.isVisible()]}")
print("OK cokme yok")
