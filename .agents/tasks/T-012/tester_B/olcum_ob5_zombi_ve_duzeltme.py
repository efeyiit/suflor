"""Tester-B tur 2: O-B5 -- deleteLater + Python referansi tutulunca zombi sekme; onerilen tek satir (destroyed -> sekme.deleteLater). Offscreen. python <bu dosya> (depo kokunden)."""
import gc, sys, weakref, os
os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, os.getcwd())
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtTest import QTest
from src.ui.kabuk import AnaPencere
from src.ui.kenar_sekmesi import KenarSekmesi

app = QtWidgets.QApplication([]); app.setQuitOnLastWindowClosed(False)
def bekle(ms):
    son = QtCore.QDeadlineTimer(ms)
    while not son.hasExpired(): app.processEvents(); QTest.qWait(5)

class Imlec:
    def __init__(self): self.p = QtCore.QPoint(5,5); self.n = 0
    def __call__(self): self.n += 1; return QtCore.QPoint(self.p)

def senaryo(duzeltme: bool):
    im = Imlec()
    p = AnaPencere(tepsi_kullanilabilir=True, imlec_konumu=im); p.show(); bekle(50); p.kenara_al(); bekle(100)
    if duzeltme:
        p.destroyed.connect(p.sekme.deleteLater)   # onerilen 1 satir: C++ AnaPencere yikilinca sekme de silinsin
    wr = weakref.ref(p.sekme)
    tik = []
    p.sekme.pencereyi_goster.connect(lambda: tik.append("emit"))
    p.deleteLater(); bekle(300); gc.collect(); bekle(100)
    s = wr()
    from shiboken6 import isValid
    if s is not None and not isValid(s): s = None
    gorunur = s is not None and s.isVisible()
    n0 = im.n; bekle(200); okuyor = im.n > n0
    sag_tik_hata = None
    if s is not None and gorunur:
        # zombi sekmeye sag tik: olu AnaPencere.goster slotu ne yapar?
        try:
            QTest.mouseClick(s, QtCore.Qt.MouseButton.RightButton, pos=QtCore.QPoint(20, 26)); bekle(50)
        except Exception as e:  # noqa: BLE001
            sag_tik_hata = type(e).__name__
        # hover -> panel acilir mi
        g = s.frameGeometry(); im.p = QtCore.QPoint(g.right()-3, g.top()+26); bekle(400)
        panel = s.acik
        s.hide(); s.deleteLater()
    else:
        panel = None
    print(f"duzeltme={duzeltme}: sekme canli={s is not None} gorunur={gorunur} yoklayici okuyor={okuyor} sag tik emit={len(tik)} hata={sag_tik_hata} hover panel acildi={panel}")
    bekle(100)

senaryo(False)
senaryo(True)
