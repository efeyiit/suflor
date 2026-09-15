"""KRT k9 -- K2 OLCU 'mesaj yapisi bozuksa False': nativeEventFilter'a dogrudan bozuk/sifir adres verilirse ne olur? (alt surec, cikis kodu)
    python .agents/tasks/T-013/krt_kosumlari/k9_bozuk_msg.py   (offscreen)
(`int(message)` gercek dispatcher ile calisiyor: k1/k2 filtreleri.)
"""
import os, subprocess, sys
os.environ["QT_QPA_PLATFORM"] = "offscreen"
KOD = r'''
import os, sys, ctypes; os.environ["QT_QPA_PLATFORM"]="offscreen"
from ctypes import wintypes
from PySide6 import QtCore, QtWidgets
class F(QtCore.QAbstractNativeEventFilter):
    def __init__(self): super().__init__(); self.tip = None
    def nativeEventFilter(self, e, m):
        if self.tip is None: self.tip = (type(m).__name__, bytes(e))
        msg = wintypes.MSG.from_address(int(m))
        if msg.message == 0x312: return True, 0
        return False, 0
app = QtWidgets.QApplication(sys.argv); f = F(); app.installNativeEventFilter(f)
w = QtWidgets.QWidget(); w.show(); t = QtCore.QTimer(); t.start(10)
import time; son = time.perf_counter() + 0.3
while time.perf_counter() < son: app.processEvents(); time.sleep(0.002)
print("offscreen 300 ms timer pompasi sirasinda filtreye gelen mesaj:", f.tip, "(None: hicbir native mesaj filtreye ugramadi)", flush=True)
print("dogrudan cagri: adres=0 ->", flush=True)
r = f.nativeEventFilter(QtCore.QByteArray(b"windows_generic_MSG"), 0)   # 'bozuk mesaj'
print("donus", r, flush=True)
'''
r = subprocess.run([sys.executable, "-c", KOD], capture_output=True, text=True, timeout=60)
print(r.stdout.strip())
print(f"alt surec cikis kodu={r.returncode} ({'COKME: erisim ihlali 0xC0000005' if r.returncode == 3221225477 else ('istisna' if r.returncode == 1 else 'temiz')}) stderr_son={(r.stderr.strip().splitlines() or [''])[-1]!r}")
