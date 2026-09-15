"""KRT k3 -- odak/on plan senaryolari (gercek Windows, sentetik keybd_event).

    python .agents/tasks/T-013/krt_kosumlari/k3_odak.py

f1 BASKA surecte tam ekran (borderless, topmost) Qt penceresi on plandayken Ctrl+Alt+T -> bize WM_HOTKEY geliyor mu
f2 YUKSELTILMIS (auto-elevate: taskmgr) pencere on plandayken Ctrl+Alt+T -> geliyor mu; SendInput donusu (UIPI)
f3 Alt yan etkisi: klasik Win32 menu cubuklu pencere (baska surec) on plandayken
     - pozitif kontrol: yalniz Alt bas/birak -> GUI_INMENUMODE?
     - Ctrl+Alt+T kisayolu (kayitli) -> menu modu? ; Alt+T kisayolu (kayitli) -> menu modu? ; on plan degisti mi
Stdout ASCII, mutlak yol yok.
"""
from __future__ import annotations

import ctypes
import subprocess
import sys
import time
from ctypes import wintypes

from PySide6 import QtCore, QtWidgets

u32 = ctypes.windll.user32
k32 = ctypes.windll.kernel32
adv = ctypes.windll.advapi32
WM_HOTKEY = 0x0312
MOD_ALT, MOD_CONTROL, MOD_NOREPEAT = 0x1, 0x2, 0x4000
VK_CONTROL, VK_MENU, VK_ESCAPE, KEYUP = 0x11, 0x12, 0x1B, 0x2
GUI_INMENUMODE, GUI_SYSTEMMENUMODE, GUI_POPUPMENUMODE = 0x4, 0x8, 0x10
INPUT_KEYBOARD = 1
ULONG_PTR = ctypes.c_size_t
u32.GetForegroundWindow.restype = wintypes.HWND
u32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD), ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]


class _U(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("pad", ctypes.c_byte * 32)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("u", _U)]


class GUITHREADINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("flags", wintypes.DWORD), ("hwndActive", wintypes.HWND), ("hwndFocus", wintypes.HWND), ("hwndCapture", wintypes.HWND), ("hwndMenuOwner", wintypes.HWND), ("hwndMoveSize", wintypes.HWND), ("hwndCaret", wintypes.HWND), ("rcCaret", wintypes.RECT)]


u32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
u32.SendInput.restype = wintypes.UINT


def bekle(ms: int) -> None:
    son = time.perf_counter() + ms / 1000
    while time.perf_counter() < son:
        QtWidgets.QApplication.processEvents(); time.sleep(0.002)


def tus(vk: int, ctrl: bool = True, alt: bool = True) -> None:
    if ctrl: u32.keybd_event(VK_CONTROL, 0, 0, 0)
    if alt: u32.keybd_event(VK_MENU, 0, 0, 0)
    u32.keybd_event(vk, 0, 0, 0); u32.keybd_event(vk, 0, KEYUP, 0)
    if alt: u32.keybd_event(VK_MENU, 0, KEYUP, 0)
    if ctrl: u32.keybd_event(VK_CONTROL, 0, KEYUP, 0)


def sendinput_tus(vk: int) -> tuple[int, int]:
    """SendInput ile Ctrl+Alt+vk; (eklenen olay sayisi, GetLastError)."""
    dizi = [(VK_CONTROL, 0), (VK_MENU, 0), (vk, 0), (vk, KEYUP), (VK_MENU, KEYUP), (VK_CONTROL, KEYUP)]
    arr = (INPUT * len(dizi))()
    for i, (v, fl) in enumerate(dizi):
        arr[i].type = INPUT_KEYBOARD; arr[i].u.ki = KEYBDINPUT(v, 0, fl, 0, 0)
    k32.SetLastError(0)
    n = u32.SendInput(len(dizi), arr, ctypes.sizeof(INPUT)); return int(n), int(k32.GetLastError())


def on_plan() -> tuple[int, int, str]:
    h = u32.GetForegroundWindow(); pid = wintypes.DWORD(0)
    u32.GetWindowThreadProcessId(h, ctypes.byref(pid)); buf = ctypes.create_unicode_buffer(128); u32.GetClassNameW(h, buf, 128)
    return int(h or 0), int(pid.value), buf.value


def butunluk(pid: int) -> str:
    """Surecin butunluk duzeyi (S-1-16-x RID): 0x1000 dusuk, 0x2000 orta, 0x3000 yuksek."""
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    hp = k32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not hp: return f"OpenProcess err={k32.GetLastError()}"
    tok = wintypes.HANDLE()
    if not adv.OpenProcessToken(hp, 8, ctypes.byref(tok)): return f"OpenProcessToken err={k32.GetLastError()}"
    n = wintypes.DWORD(0); adv.GetTokenInformation(tok, 25, None, 0, ctypes.byref(n))  # TokenIntegrityLevel
    buf = ctypes.create_string_buffer(n.value)
    if not adv.GetTokenInformation(tok, 25, buf, n, ctypes.byref(n)): return f"GetTokenInformation err={k32.GetLastError()}"
    psid = ctypes.cast(buf, ctypes.POINTER(ctypes.c_void_p))[0]
    adv.GetSidSubAuthorityCount.restype = ctypes.POINTER(ctypes.c_ubyte); adv.GetSidSubAuthorityCount.argtypes = [ctypes.c_void_p]
    adv.GetSidSubAuthority.restype = ctypes.POINTER(wintypes.DWORD); adv.GetSidSubAuthority.argtypes = [ctypes.c_void_p, wintypes.DWORD]
    cnt = adv.GetSidSubAuthorityCount(psid)[0]; rid = adv.GetSidSubAuthority(psid, cnt - 1)[0]
    k32.CloseHandle(tok); k32.CloseHandle(hp)
    return {0x1000: "dusuk", 0x2000: "orta", 0x3000: "yuksek", 0x4000: "sistem"}.get(rid, hex(rid))


def menu_modu(hwnd: int) -> tuple[int, int]:
    tid = u32.GetWindowThreadProcessId(hwnd, None)
    g = GUITHREADINFO(); g.cbSize = ctypes.sizeof(GUITHREADINFO)
    ok = u32.GetGUIThreadInfo(tid, ctypes.byref(g)); return (int(g.flags) if ok else -1, int(g.hwndMenuOwner or 0))


class Filtre(QtCore.QAbstractNativeEventFilter):
    def __init__(self) -> None:
        super().__init__(); self.olaylar: list[int] = []

    def nativeEventFilter(self, eventType, message):  # type: ignore[override]
        msg = wintypes.MSG.from_address(int(message))
        if msg.message == WM_HOTKEY:
            self.olaylar.append(int(msg.wParam)); return True, 0
        return False, 0


TAM_EKRAN = (
    "import sys, ctypes; from PySide6 import QtCore, QtWidgets; a=QtWidgets.QApplication(sys.argv); w=QtWidgets.QWidget(); "
    "w.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint|QtCore.Qt.WindowType.WindowStaysOnTopHint); w.setStyleSheet('background:#123'); "
    "w.showFullScreen(); w.raise_(); w.activateWindow(); QtCore.QTimer.singleShot(400, lambda: print(int(w.winId()), flush=True)); "
    "QtCore.QTimer.singleShot(6000, a.quit); a.exec()"
)

MENU_PENCERE = r'''
import ctypes, sys, time
from ctypes import wintypes
u=ctypes.windll.user32; k=ctypes.windll.kernel32
WNDPROC=ctypes.WINFUNCTYPE(ctypes.c_ssize_t, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
u.DefWindowProcW.restype=ctypes.c_ssize_t; u.DefWindowProcW.argtypes=[wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
def wp(h,m,w,l):
    if m==0x2: u.PostQuitMessage(0); return 0
    return u.DefWindowProcW(h,m,w,l)
cb=WNDPROC(wp)
class WNDCLASSW(ctypes.Structure):
    _fields_=[("style",wintypes.UINT),("lpfnWndProc",WNDPROC),("cbClsExtra",ctypes.c_int),("cbWndExtra",ctypes.c_int),("hInstance",wintypes.HINSTANCE),("hIcon",wintypes.HICON),("hCursor",wintypes.HANDLE),("hbrBackground",wintypes.HBRUSH),("lpszMenuName",wintypes.LPCWSTR),("lpszClassName",wintypes.LPCWSTR)]
wc=WNDCLASSW(); wc.lpfnWndProc=cb; wc.lpszClassName="KrtMenuPencere"; wc.hbrBackground=6; wc.hInstance=k.GetModuleHandleW(None)
u.RegisterClassW(ctypes.byref(wc))
menu=u.CreateMenu(); alt=u.CreatePopupMenu(); u.AppendMenuW(alt,0,101,"&Ac"); u.AppendMenuW(alt,0,102,"&Kapat")
u.AppendMenuW(menu,0x10,alt,"&Dosya"); u.AppendMenuW(menu,0x10,u.CreatePopupMenu(),"&Yardim")
u.CreateWindowExW.restype=wintypes.HWND
h=u.CreateWindowExW(0,"KrtMenuPencere","KRT menu penceresi",0x00CF0000,200,200,520,320,None,menu,wc.hInstance,None)
u.ShowWindow(h,5); u.SetForegroundWindow(h)
print(int(h), flush=True)
msg=wintypes.MSG(); t0=time.time()
u.SetTimer(h,1,100,None)
while u.GetMessageW(ctypes.byref(msg),None,0,0)>0:
    u.TranslateMessage(ctypes.byref(msg)); u.DispatchMessageW(ctypes.byref(msg))
    if time.time()-t0>25: break
'''


def main() -> int:
    app = QtWidgets.QApplication(sys.argv)
    f = Filtre(); app.installNativeEventFilter(f)
    ok = bool(u32.RegisterHotKey(None, 1, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, ord("T")))
    print(f"kurulum: platform={app.platformName()} Ctrl+Alt+T kayit={ok} bizim IL={butunluk(k32.GetCurrentProcessId())}")

    # f1 tam ekran topmost baska surec
    p = subprocess.Popen([sys.executable, "-c", TAM_EKRAN], stdout=subprocess.PIPE, text=True)
    hwnd_oyun = int(p.stdout.readline().strip()) if p.stdout else 0
    bekle(500); h, pid, cls = on_plan()
    f.olaylar.clear(); tus(ord("T")); bekle(400)
    print(f"f1 tam ekran topmost baska surec on planda={h == hwnd_oyun} (on plan class={cls} pid={pid} oyun pid={p.pid}): Ctrl+Alt+T -> olay={len(f.olaylar)} (1 beklenir)")
    h2, _, _ = on_plan(); print(f"f1 kisayol sonrasi on plan hala oyun={h2 == hwnd_oyun}")
    p.terminate(); bekle(300)

    # f2 yukseltilmis pencere: taskmgr auto-elevate
    tm = None
    try:
        tm = subprocess.Popen(["taskmgr.exe"])
    except OSError as e:
        print(f"f2 taskmgr baslatilamadi: {type(e).__name__}")
    if tm is not None:
        hedef = 0
        for _ in range(60):
            bekle(100); h, pid, cls = on_plan()
            if pid and pid != k32.GetCurrentProcessId() and cls.startswith("TaskManagerWindow"):
                hedef = h; break
        h, pid, cls = on_plan()
        il = butunluk(pid) if pid else "?"
        f.olaylar.clear(); tus(ord("T")); bekle(400); n_kbd = len(f.olaylar)
        f.olaylar.clear(); n_si, err_si = sendinput_tus(ord("T")); bekle(400); n_si_olay = len(f.olaylar)
        print(f"f2 on plan class={cls} IL={il} (yuksek beklenir): keybd_event Ctrl+Alt+T -> olay={n_kbd}; SendInput eklenen={n_si}/6 err={err_si} -> olay={n_si_olay}")
        # kapatmayi dene (UIPI: dusuk IL'den yuksek IL pencereye WM_CLOSE engellenebilir)
        r = u32.PostMessageW(hedef or h, 0x10, 0, 0); print(f"f2 taskmgr'a WM_CLOSE PostMessage={bool(r)} err={k32.GetLastError() if not r else 0}")
        bekle(800); h3, pid3, cls3 = on_plan(); print(f"f2 sonra on plan class={cls3} (taskmgr hala acik olabilir; elle kapatilir)")
        try:
            tm.wait(timeout=1)
        except subprocess.TimeoutExpired:
            pass

    # f3 Alt yan etkisi: klasik Win32 menu cubuklu pencere
    m = subprocess.Popen([sys.executable, "-c", MENU_PENCERE], stdout=subprocess.PIPE, text=True)
    hwnd_menu = int(m.stdout.readline().strip()) if m.stdout else 0
    bekle(600); h, pid, cls = on_plan(); print(f"f3 menu penceresi on planda={h == hwnd_menu} class={cls}")
    # pozitif kontrol: yalniz Alt
    u32.keybd_event(VK_MENU, 0, 0, 0); u32.keybd_event(VK_MENU, 0, KEYUP, 0); bekle(300)
    fl, sahip = menu_modu(hwnd_menu); print(f"f3 pozitif kontrol yalniz Alt bas/birak: GUI flags={hex(fl)} INMENUMODE={bool(fl & GUI_INMENUMODE)} (True beklenir)")
    u32.keybd_event(VK_ESCAPE, 0, 0, 0); u32.keybd_event(VK_ESCAPE, 0, KEYUP, 0); bekle(300)
    fl, _ = menu_modu(hwnd_menu); print(f"f3 Esc sonrasi INMENUMODE={bool(fl & GUI_INMENUMODE)}")
    # Ctrl+Alt+T kayitli
    f.olaylar.clear(); tus(ord("T")); bekle(300); fl, _ = menu_modu(hwnd_menu); h2, _, _ = on_plan()
    print(f"f3 Ctrl+Alt+T (kayitli): olay={len(f.olaylar)} INMENUMODE={bool(fl & GUI_INMENUMODE)} on plan degisti={h2 != hwnd_menu}")
    if fl & GUI_INMENUMODE: u32.keybd_event(VK_ESCAPE, 0, 0, 0); u32.keybd_event(VK_ESCAPE, 0, KEYUP, 0); bekle(200)
    # Alt+T kayitli (K3 dilbilgisi izin veriyor)
    u32.UnregisterHotKey(None, 1); ok2 = bool(u32.RegisterHotKey(None, 2, MOD_ALT | MOD_NOREPEAT, ord("T")))
    f.olaylar.clear(); tus(ord("T"), ctrl=False, alt=True); bekle(300); fl, _ = menu_modu(hwnd_menu); h2, _, _ = on_plan()
    print(f"f3 Alt+T (kayitli={ok2}): olay={len(f.olaylar)} INMENUMODE={bool(fl & GUI_INMENUMODE)} on plan degisti={h2 != hwnd_menu}")
    if fl & GUI_INMENUMODE: u32.keybd_event(VK_ESCAPE, 0, 0, 0); u32.keybd_event(VK_ESCAPE, 0, KEYUP, 0); bekle(200)
    # Alt+T kayitsiz (pencereye gider: &... yok, T menu hizlandiricisi degil)
    u32.UnregisterHotKey(None, 2); f.olaylar.clear(); tus(ord("T"), ctrl=False, alt=True); bekle(300); fl, _ = menu_modu(hwnd_menu)
    print(f"f3 Alt+T (kayitsiz): olay={len(f.olaylar)} INMENUMODE={bool(fl & GUI_INMENUMODE)}")
    if fl & GUI_INMENUMODE: u32.keybd_event(VK_ESCAPE, 0, 0, 0); u32.keybd_event(VK_ESCAPE, 0, KEYUP, 0); bekle(200)
    # Shift+Alt? hayir. Ctrl+Alt+T kayitsizken: T pencereye gider, menu modu?
    f.olaylar.clear(); tus(ord("T")); bekle(300); fl, _ = menu_modu(hwnd_menu)
    print(f"f3 Ctrl+Alt+T (kayitsiz): INMENUMODE={bool(fl & GUI_INMENUMODE)}")
    u32.PostMessageW(hwnd_menu, 0x10, 0, 0); m.wait(timeout=5)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
