"""KRT-1 / madde 4+6 (devam) -- GERCEK OS tikiyla odak: NoFocus sekme vs odak-alan varyant (real_check [3] pozitif kontrol).

    python .agents/tasks/T-012/krt_kosumlari/k5b_tik_odak.py

k5 O2: Windows platformunda HER Tool pencere show() ile SW_SHOWNOACTIVATE gosterilir -> activeWindow None; yani
real_check [3] NoFocus/ShowWithoutActivating olmayan uygulamada da gecer (yapisal). Odak farki TIKTA ortaya cikar:
  T1 sahne (normal pencere) on planda; NoFocus+SWA sekmeye GERCEK sol tik -> GetForegroundWindow degisti mi (degismemeli)
  T2 ayni tik, NoFocus/SWA OLMAYAN Tool sekme -> on plan sekmeye gecti mi (gecmeli: pozitif kontrol)
  T3 T1 sekmesinde panel dugmesi (QPushButton cocuk) gercek tik -> clicked geldi mi, on plan degisti mi
Imlec altindaki pencere bizim degilse tik atlanir. Ham cikti: k5b_tik_odak.txt
"""
from __future__ import annotations

import ctypes
import sys
import time
from ctypes import wintypes
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

CIKTI = Path(__file__).resolve().parent / "k5b_tik_odak.txt"
satirlar: list[str] = []
u32 = ctypes.windll.user32; k32 = ctypes.windll.kernel32
u32.WindowFromPoint.restype = wintypes.HWND; u32.WindowFromPoint.argtypes = [wintypes.POINT]
u32.GetForegroundWindow.restype = wintypes.HWND
BAYRAK = (QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.Tool
          | QtCore.Qt.WindowType.WindowStaysOnTopHint | QtCore.Qt.WindowType.WindowDoesNotAcceptFocus)


def olgu(m: str) -> None:
    satirlar.append(m); print(" ", m)


def bekle(ms: int) -> None:
    son = time.perf_counter() + ms / 1000
    while time.perf_counter() < son:
        QtWidgets.QApplication.processEvents(); time.sleep(0.004)


def pid_of(hwnd: int) -> int:
    pid = wintypes.DWORD(0); u32.GetWindowThreadProcessId(wintypes.HWND(hwnd), ctypes.byref(pid)); return int(pid.value)


def on_plan(adlar: dict[int, str]) -> str:
    h = int(u32.GetForegroundWindow() or 0)
    return adlar.get(h, "BIZIM:diger" if pid_of(h) == k32.GetCurrentProcessId() else "baska-surec")


def bizim_mi(p: QtCore.QPoint) -> bool:
    h = int(u32.WindowFromPoint(wintypes.POINT(p.x(), p.y())) or 0)
    return pid_of(h) == k32.GetCurrentProcessId()


def gercek_sol_tik(p: QtCore.QPoint) -> bool:
    QtGui.QCursor.setPos(p); bekle(80)
    if not bizim_mi(p):
        olgu(f"    (tik ATLANDI: imlec altindaki pencere bizim degil @ {p.x()},{p.y()})"); return False
    u32.mouse_event(0x0002, 0, 0, 0, 0); bekle(30); u32.mouse_event(0x0004, 0, 0, 0, 0); bekle(250)
    return True


def dolu_sekme(bayrak, swa: bool, y: int) -> QtWidgets.QWidget:
    class S(QtWidgets.QWidget):
        def paintEvent(self, e):
            p = QtGui.QPainter(self); p.fillRect(self.rect(), QtGui.QColor(22, 27, 33, 235)); p.end()
    w = S(None, bayrak); w.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
    if swa:
        w.setAttribute(QtCore.Qt.WidgetAttribute.WA_ShowWithoutActivating)
    g = QtGui.QGuiApplication.primaryScreen().availableGeometry()
    w.setGeometry(g.right() - 25, y, 26, 52); w.show(); return w


def main() -> int:
    app = QtWidgets.QApplication(sys.argv); app.setQuitOnLastWindowClosed(False)
    g = QtGui.QGuiApplication.primaryScreen().availableGeometry()
    imlec0 = QtGui.QCursor.pos()
    sahne = QtWidgets.QLabel("temsili oyun"); sahne.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
    sahne.setStyleSheet("background:#1b2a41;"); sahne.setGeometry(g.right() - 640, g.y() + 300, 641, 800); sahne.show(); bekle(200)
    sahne.raise_(); sahne.activateWindow(); bekle(300)
    adlar = {int(sahne.winId()): "sahne"}
    olgu(f"on plan baslangic={on_plan(adlar)} (sahne beklenir)")

    # T1 NoFocus + SWA
    s1 = dolu_sekme(BAYRAK, True, g.center().y() - 26); bekle(250); adlar[int(s1.winId())] = "sekme_NoFocus"
    olgu(f"T1 show() sonrasi on plan={on_plan(adlar)} activeWindow={type(QtWidgets.QApplication.activeWindow()).__name__ if QtWidgets.QApplication.activeWindow() else None}")
    r = s1.frameGeometry(); hedef = QtCore.QPoint(r.x() + 13, r.y() + 26)
    t = gercek_sol_tik(hedef)
    olgu(f"T1 NoFocus+SWA sekmeye gercek tik: basildi={t} on plan sonra={on_plan(adlar)} (sahne kalmali) activeWindow={type(QtWidgets.QApplication.activeWindow()).__name__ if QtWidgets.QApplication.activeWindow() else None}")

    # T2 pozitif kontrol: NoFocus yok, SWA yok
    sahne.raise_(); sahne.activateWindow(); bekle(200)
    s2 = dolu_sekme(BAYRAK & ~QtCore.Qt.WindowType.WindowDoesNotAcceptFocus, False, g.center().y() + 120); bekle(250); adlar[int(s2.winId())] = "sekme_odakAlan"
    olgu(f"T2 odak-alan varyant show() sonrasi on plan={on_plan(adlar)} activeWindow={type(QtWidgets.QApplication.activeWindow()).__name__ if QtWidgets.QApplication.activeWindow() else None} (show() ile ayrismiyorsa [3] yapisal)")
    r2 = s2.frameGeometry(); hedef2 = QtCore.QPoint(r2.x() + 13, r2.y() + 26)
    t2 = gercek_sol_tik(hedef2)
    olgu(f"T2 odak-alan sekmeye gercek tik: basildi={t2} on plan sonra={on_plan(adlar)} (sekme_odakAlan beklenir: pozitif kontrol) activeWindow={type(QtWidgets.QApplication.activeWindow()).__name__ if QtWidgets.QApplication.activeWindow() else None}")
    s2.close()

    # T3 NoFocus sekmede QPushButton cocuk
    sahne.raise_(); sahne.activateWindow(); bekle(200)
    s1.setGeometry(g.right() - 199, g.center().y() - 66, 200, 132)
    b = QtWidgets.QPushButton("Anlik ceviri", s1); b.setGeometry(10, 40, 180, 40); b.show(); bekle(250)
    tik = []; b.clicked.connect(lambda: tik.append(1))
    hedef3 = b.mapToGlobal(b.rect().center())
    t3 = gercek_sol_tik(hedef3)
    olgu(f"T3 NoFocus sekmede panel dugmesine gercek tik: basildi={t3} clicked={len(tik)} on plan sonra={on_plan(adlar)} (sahne kalmali, clicked=1)")

    QtGui.QCursor.setPos(imlec0); s1.close(); sahne.close()
    CIKTI.write_text("KRT-1 madde 4/6 (devam) -- gercek tik ile odak\n\n" + "\n".join(satirlar) + "\n", encoding="utf-8")
    print("yazildi: k5b_tik_odak.txt"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
