"""KRT-1 / madde 4+6 -- Windows'ta z-sirasi (tam ekran pencere ustunde kalma) ve real_check [3] pozitif kontrolu.

    python .agents/tasks/T-012/krt_kosumlari/k5_zorder_odak.py

Z1 sekme (TOPMOST+NOACTIVATE) vs tam ekran NORMAL pencere (showFullScreen): EnumWindows sirasinda kim ustte
Z2 sekme vs tam ekran + WindowStaysOnTopHint (bazi borderless oyunlar 'her zaman ustte' yapar), SONRA gosterilen
Z3 sekme.raise_() sonrasi
O1 real_check [3] pozitif kontrolu: NoFocus+ShowWithoutActivating OLMAYAN sekme show() -> activeWindow None mi
   (oturum kilitliyken de None ise [3] kilitli oturumda ates edemez)
Ekran goruntusu yok; z-sirasi EnumWindows ile (gorsel gerekmez, kilitli oturumda da olculur).
"""
from __future__ import annotations

import ctypes
import sys
import time
from ctypes import wintypes
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

CIKTI = Path(__file__).resolve().parent / "k5_zorder_odak.txt"
satirlar: list[str] = []
u32 = ctypes.windll.user32
BAYRAK = (QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.Tool
          | QtCore.Qt.WindowType.WindowStaysOnTopHint | QtCore.Qt.WindowType.WindowDoesNotAcceptFocus)


def olgu(m: str) -> None:
    satirlar.append(m); print(" ", m)


def bekle(ms: int) -> None:
    son = time.perf_counter() + ms / 1000
    while time.perf_counter() < son:
        QtWidgets.QApplication.processEvents(); time.sleep(0.004)


def oturum_kilitli() -> bool:
    class L1(ctypes.Structure):
        _fields_ = [("SessionId", wintypes.DWORD), ("State", ctypes.c_int), ("SessionFlags", wintypes.LONG), ("pad", ctypes.c_byte * 400)]

    class EX(ctypes.Structure):
        _fields_ = [("Level", wintypes.DWORD), ("Data", L1)]
    buf = ctypes.c_void_p(); n = wintypes.DWORD()
    if not ctypes.windll.wtsapi32.WTSQuerySessionInformationW(None, 0xFFFFFFFF, 25, ctypes.byref(buf), ctypes.byref(n)):
        return False
    return ctypes.cast(buf, ctypes.POINTER(EX)).contents.Data.SessionFlags == 0


def z_sirasi(adlar: dict[int, str]) -> list[str]:
    """EnumWindows ust-alt sirasi; yalnizca verilen HWND'ler."""
    sira: list[str] = []
    CB = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

    def cb(h, _):
        if int(h) in adlar:
            sira.append(adlar[int(h)])
        return True
    u32.EnumWindows(CB(cb), 0)
    return sira


def main() -> int:
    app = QtWidgets.QApplication(sys.argv); app.setQuitOnLastWindowClosed(False)
    kilitli = oturum_kilitli()
    olgu(f"oturum kilitli={kilitli}")
    g = QtGui.QGuiApplication.primaryScreen().availableGeometry()
    s = QtWidgets.QWidget(None, BAYRAK); s.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground); s.setAttribute(QtCore.Qt.WidgetAttribute.WA_ShowWithoutActivating)
    s.setGeometry(g.right() - 25, g.center().y() - 26, 26, 52); s.show(); bekle(200)
    adlar = {int(s.winId()): "sekme"}

    oyun1 = QtWidgets.QLabel("tam ekran normal"); oyun1.setStyleSheet("background:#0b1220;")
    oyun1.showFullScreen(); bekle(400); adlar[int(oyun1.winId())] = "oyun1(fullscreen,normal)"
    ex1 = u32.GetWindowLongW(wintypes.HWND(int(oyun1.winId())), -20)
    olgu(f"Z1 oyun1 showFullScreen (TOPMOST={bool(ex1 & 8)}) -> z-sirasi ust->alt: {z_sirasi(adlar)}")
    oyun1.close(); bekle(200)

    oyun2 = QtWidgets.QLabel("tam ekran ustte"); oyun2.setStyleSheet("background:#0b1220;")
    oyun2.setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnTopHint, True)
    oyun2.showFullScreen(); bekle(400); adlar[int(oyun2.winId())] = "oyun2(fullscreen,StaysOnTop)"
    ex2 = u32.GetWindowLongW(wintypes.HWND(int(oyun2.winId())), -20)
    olgu(f"Z2 oyun2 showFullScreen+StaysOnTop (TOPMOST={bool(ex2 & 8)}) sekmeden SONRA -> z-sirasi: {z_sirasi(adlar)}")
    s.raise_(); bekle(200)
    olgu(f"Z3 sekme.raise_() -> z-sirasi: {z_sirasi(adlar)}")
    oyun2.raise_(); bekle(200)
    olgu(f"Z3b oyun2.raise_() (oyun kendini yeniden ustte tutarsa) -> z-sirasi: {z_sirasi(adlar)}")
    oyun2.close(); bekle(200)

    # O1 real_check [3] pozitif kontrolu
    ana = QtWidgets.QWidget(None, QtCore.Qt.WindowType.FramelessWindowHint); ana.resize(300, 200); ana.move(g.x() + 200, g.y() + 200); ana.show(); bekle(300)
    olgu(f"O1 ana pencere show(): activeWindow={type(QtWidgets.QApplication.activeWindow()).__name__ if QtWidgets.QApplication.activeWindow() else None} (kilitliyken odak alinamayabilir)")
    ana.hide(); bekle(100)
    kotu = QtWidgets.QWidget(None, BAYRAK & ~QtCore.Qt.WindowType.WindowDoesNotAcceptFocus)
    kotu.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)   # ShowWithoutActivating YOK, NoFocus YOK
    kotu.setGeometry(g.right() - 25, g.center().y() + 100, 26, 52); kotu.show(); bekle(300)
    a = QtWidgets.QApplication.activeWindow()
    olgu(f"O1 odak CALAN sekme varyanti show() -> activeWindow={type(a).__name__ if a else None} (sekme mi={a is kotu}) -> real_check [3] bu varyantta ates eder mi: {a is not None} [kilitli={kilitli}]")
    kotu.close(); s.close()
    CIKTI.write_text("KRT-1 madde 4/6 -- z-sirasi ve odak\n\n" + "\n".join(satirlar) + "\n", encoding="utf-8")
    print("yazildi: k5_zorder_odak.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
