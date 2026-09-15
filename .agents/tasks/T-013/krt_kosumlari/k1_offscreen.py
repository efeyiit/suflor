"""KRT k1 -- QT_QPA_PLATFORM=offscreen altinda RegisterHotKey(NULL) + native filtre GERCEK keybd_event aliyor mu?

    python .agents/tasks/T-013/krt_kosumlari/k1_offscreen.py

o1 offscreen olay dagiticisi sinifi (Win32 mi?)
o2 offscreen'de RegisterHotKey + keybd_event -> WM_HOTKEY sayisi, gecikme
o3 offscreen surec Ctrl+Alt+T tutarken IKINCI offscreen surec (pytest gibi) -> 1409
o4 gercek pytest (pytest-qt qapp, offscreen) icinde ayni sey: iki pytest sureci paralel -> biri 1409
Stdout ASCII, mutlak yol yok.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

os.environ["QT_QPA_PLATFORM"] = "offscreen"

import ctypes  # noqa: E402
from ctypes import wintypes  # noqa: E402

from PySide6 import QtCore, QtWidgets  # noqa: E402

u32 = ctypes.windll.user32
k32 = ctypes.windll.kernel32
WM_HOTKEY = 0x0312
MOD_ALT, MOD_CONTROL, MOD_NOREPEAT = 0x1, 0x2, 0x4000
VK_CONTROL, VK_MENU, KEYUP = 0x11, 0x12, 0x2


def bekle(ms: int) -> None:
    son = time.perf_counter() + ms / 1000
    while time.perf_counter() < son:
        QtWidgets.QApplication.processEvents(); time.sleep(0.002)


def tus(vk: int) -> None:
    u32.keybd_event(VK_CONTROL, 0, 0, 0); u32.keybd_event(VK_MENU, 0, 0, 0); u32.keybd_event(vk, 0, 0, 0)
    u32.keybd_event(vk, 0, KEYUP, 0); u32.keybd_event(VK_MENU, 0, KEYUP, 0); u32.keybd_event(VK_CONTROL, 0, KEYUP, 0)


class Filtre(QtCore.QAbstractNativeEventFilter):
    def __init__(self) -> None:
        super().__init__(); self.olaylar: list[tuple[int, float]] = []

    def nativeEventFilter(self, eventType, message):  # type: ignore[override]
        msg = wintypes.MSG.from_address(int(message))
        if msg.message == WM_HOTKEY:
            self.olaylar.append((int(msg.wParam), time.perf_counter())); return True, 0
        return False, 0


PYTEST_DOSYA = '''
import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"
import ctypes, time, sys
from ctypes import wintypes
from PySide6 import QtCore, QtWidgets
u32 = ctypes.windll.user32; k32 = ctypes.windll.kernel32

class F(QtCore.QAbstractNativeEventFilter):
    def __init__(self): super().__init__(); self.n = 0
    def nativeEventFilter(self, t, m):
        msg = wintypes.MSG.from_address(int(m))
        if msg.message == 0x312: self.n += 1; return True, 0
        return False, 0

def test_offscreen_gercek_hotkey(qapp, qtbot):
    f = F(); qapp.installNativeEventFilter(f)
    ok = bool(u32.RegisterHotKey(None, 1, 0x1 | 0x2 | 0x4000, ord("T"))); err = k32.GetLastError() if not ok else 0
    print(f"\\nPYTEST pid={os.getpid()} platform={qapp.platformName()} kayit={ok} err={err}", flush=True)
    if ok:
        u32.keybd_event(0x11, 0, 0, 0); u32.keybd_event(0x12, 0, 0, 0); u32.keybd_event(ord("T"), 0, 0, 0)
        u32.keybd_event(ord("T"), 0, 2, 0); u32.keybd_event(0x12, 0, 2, 0); u32.keybd_event(0x11, 0, 2, 0)
        qtbot.wait(300)
        print(f"PYTEST pid={os.getpid()} WM_HOTKEY={f.n}", flush=True)
        time.sleep(2.5)  # diger pytest sureci bu sirada kayit denesin
        u32.UnregisterHotKey(None, 1)
    qapp.removeNativeEventFilter(f)
    assert True
'''


def main() -> int:
    app = QtWidgets.QApplication(sys.argv)
    d = QtCore.QAbstractEventDispatcher.instance()
    print(f"o1 platform={app.platformName()} dispatcher={d.metaObject().className() if d else None}")
    f = Filtre(); app.installNativeEventFilter(f)
    ok = bool(u32.RegisterHotKey(None, 1, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, ord("T")))
    print(f"o2 offscreen RegisterHotKey(NULL, Ctrl+Alt+T) ok={ok} err={0 if ok else k32.GetLastError()}")
    t0 = time.perf_counter(); tus(ord("T")); bekle(300)
    gec = (f.olaylar[0][1] - t0) * 1000 if f.olaylar else -1
    print(f"o2 offscreen keybd_event Ctrl+Alt+T -> WM_HOTKEY olay={len(f.olaylar)} id={[o[0] for o in f.olaylar]} gecikme={gec:.1f} ms")
    # o3 ikinci offscreen surec
    kod = ("import os; os.environ['QT_QPA_PLATFORM']='offscreen'; import ctypes, sys; from PySide6 import QtWidgets; "
           "a=QtWidgets.QApplication(sys.argv); u=ctypes.windll.user32; k=ctypes.windll.kernel32; "
           "ok=u.RegisterHotKey(None,1,0x1|0x2|0x4000,ord('T')); print('cocuk offscreen kayit ok=%d err=%d' % (ok, 0 if ok else k.GetLastError()), flush=True)")
    r = subprocess.run([sys.executable, "-c", kod], capture_output=True, text=True, timeout=30)
    print(f"o3 biz Ctrl+Alt+T tutarken ikinci offscreen surec: {r.stdout.strip()}")
    u32.UnregisterHotKey(None, 1); app.removeNativeEventFilter(f)
    # o4 gercek pytest x2 paralel
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "test_krt_offscreen_hotkey.py"; p.write_text(PYTEST_DOSYA, encoding="utf-8")
        (Path(tmp) / "conftest.py").write_text("", encoding="utf-8")
        cmd = [sys.executable, "-m", "pytest", str(p), "-q", "-s", "-p", "no:cacheprovider", "--rootdir", tmp]
        a = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=tmp)
        time.sleep(1.0)
        b = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=tmp)
        oa, _ = a.communicate(timeout=60); ob, _ = b.communicate(timeout=60)
        for ad, o in (("A", oa), ("B", ob)):
            for s in o.splitlines():
                if s.startswith("PYTEST") or "passed" in s or "failed" in s or "error" in s.lower():
                    print(f"o4 pytest-{ad}: {s.strip()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
