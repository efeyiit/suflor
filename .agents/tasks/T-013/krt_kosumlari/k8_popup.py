"""KRT k8 -- tepsi menusu (QMenu.exec, ic ice olay dongusu) ACIKKEN WM_HOTKEY filtreye ulasiyor mu (K4 'kabuk durumundan bagimsiz').
    python .agents/tasks/T-013/krt_kosumlari/k8_popup.py   (gercek ekran; menu 600 ms acik kalir)
"""
import ctypes, sys, time
from ctypes import wintypes
from PySide6 import QtCore, QtWidgets
u32 = ctypes.windll.user32
class F(QtCore.QAbstractNativeEventFilter):
    def __init__(self): super().__init__(); self.n = 0; self.t = []
    def nativeEventFilter(self, e, m):
        msg = wintypes.MSG.from_address(int(m))
        if msg.message == 0x312: self.n += 1; self.t.append(time.perf_counter()); return True, 0
        return False, 0
app = QtWidgets.QApplication(sys.argv); f = F(); app.installNativeEventFilter(f)
assert u32.RegisterHotKey(None, 1, 0x1 | 0x2 | 0x4000, ord("T"))
menu = QtWidgets.QMenu(); menu.addAction("Pencereyi goster"); menu.addAction("Cikis")
def tus():
    u32.keybd_event(0x11,0,0,0); u32.keybd_event(0x12,0,0,0); u32.keybd_event(ord("T"),0,0,0)
    u32.keybd_event(ord("T"),0,2,0); u32.keybd_event(0x12,0,2,0); u32.keybd_event(0x11,0,2,0)
durum = {}
def gonder():
    durum["t0"] = time.perf_counter(); tus()
QtCore.QTimer.singleShot(200, gonder); QtCore.QTimer.singleShot(600, menu.close)
menu.exec(QtCore.QPoint(300, 300))  # ic ice dongu (tepsi sag tik ile ayni)
gec = (f.t[0] - durum["t0"]) * 1000 if f.t else -1
print(f"QMenu.exec acikken Ctrl+Alt+T -> WM_HOTKEY={f.n} gecikme={gec:.1f} ms (menu hala acik miydi: kapanis 600 ms'de)")
u32.UnregisterHotKey(None, 1)
