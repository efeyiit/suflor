"""KRT k2 -- sentetik girdi ile donanim tekrari (autorepeat) uretilebilir mi? Kapi [5] neyi olcuyor?

    python .agents/tasks/T-013/krt_kosumlari/k2_tekrar.py     (gercek windows platformu)

r1 U6/U6b tekrari: keybd_event tek DOWN + 700 ms bekleme + UP  -> NOREPEAT'li / NOREPEAT'siz olay sayisi
r2 tekrar TAKLIDI: T DOWN x5 (UP yok, 30 ms arayla) -> NOREPEAT'li / NOREPEAT'siz olay sayisi  (pozitif kontrol adayi)
r3 ayni sey SendInput + KEYEVENTF_SCANCODE ile
r4 WH_KEYBOARD_LL kancasi: r1'de kac WM_KEYDOWN(T) goruluyor (donanim tekrari olsa >1 olurdu)
Stdout ASCII.
"""
from __future__ import annotations

import ctypes
import sys
import time
from ctypes import wintypes

from PySide6 import QtCore, QtWidgets

u32 = ctypes.windll.user32
k32 = ctypes.windll.kernel32
WM_HOTKEY = 0x0312
MOD_ALT, MOD_CONTROL, MOD_NOREPEAT = 0x1, 0x2, 0x4000
VK_CONTROL, VK_MENU, KEYUP = 0x11, 0x12, 0x2
INPUT_KEYBOARD = 1
KEYEVENTF_SCANCODE = 0x8
WH_KEYBOARD_LL = 13
WM_KEYDOWN, WM_SYSKEYDOWN = 0x100, 0x104
ULONG_PTR = ctypes.c_size_t


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD), ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]


class _U(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("pad", ctypes.c_byte * 32)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("u", _U)]


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [("vkCode", wintypes.DWORD), ("scanCode", wintypes.DWORD), ("flags", wintypes.DWORD), ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]


HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)
u32.SetWindowsHookExW.restype = wintypes.HHOOK
u32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD]
u32.CallNextHookEx.restype = ctypes.c_ssize_t
u32.CallNextHookEx.argtypes = [wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
u32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
u32.SendInput.restype = wintypes.UINT

kanca_kayit: list[tuple[int, int, int]] = []  # (msg, vk, flags)


def _kanca(nCode: int, wParam: int, lParam: int) -> int:
    if nCode >= 0:
        k = KBDLLHOOKSTRUCT.from_address(lParam)
        kanca_kayit.append((int(wParam), int(k.vkCode), int(k.flags)))
    return u32.CallNextHookEx(None, nCode, wParam, lParam)


_kanca_c = HOOKPROC(_kanca)


def bekle(ms: int) -> None:
    son = time.perf_counter() + ms / 1000
    while time.perf_counter() < son:
        QtWidgets.QApplication.processEvents(); time.sleep(0.002)


def sc_input(vk: int, up: bool = False, scancode: bool = False) -> None:
    inp = INPUT(); inp.type = INPUT_KEYBOARD
    if scancode:
        sc = u32.MapVirtualKeyW(vk, 0)
        inp.u.ki = KEYBDINPUT(0, sc, KEYEVENTF_SCANCODE | (KEYUP if up else 0), 0, 0)
    else:
        inp.u.ki = KEYBDINPUT(vk, 0, KEYUP if up else 0, 0, 0)
    n = u32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
    if n != 1:
        print(f"  SendInput basarisiz n={n} err={k32.GetLastError()}")


class Filtre(QtCore.QAbstractNativeEventFilter):
    def __init__(self) -> None:
        super().__init__(); self.olaylar: list[int] = []

    def nativeEventFilter(self, eventType, message):  # type: ignore[override]
        msg = wintypes.MSG.from_address(int(message))
        if msg.message == WM_HOTKEY:
            self.olaylar.append(int(msg.wParam)); return True, 0
        return False, 0


def kayit(norepeat: bool) -> bool:
    u32.UnregisterHotKey(None, 1)
    return bool(u32.RegisterHotKey(None, 1, MOD_CONTROL | MOD_ALT | (MOD_NOREPEAT if norepeat else 0), ord("T")))


def r1(f: Filtre, norepeat: bool) -> int:
    kayit(norepeat); f.olaylar.clear()
    u32.keybd_event(VK_CONTROL, 0, 0, 0); u32.keybd_event(VK_MENU, 0, 0, 0); u32.keybd_event(ord("T"), 0, 0, 0)
    bekle(700)
    u32.keybd_event(ord("T"), 0, KEYUP, 0); u32.keybd_event(VK_MENU, 0, KEYUP, 0); u32.keybd_event(VK_CONTROL, 0, KEYUP, 0)
    bekle(300); return len(f.olaylar)


def r2(f: Filtre, norepeat: bool, n_down: int, scancode: bool | None) -> int:
    kayit(norepeat); f.olaylar.clear()
    if scancode is None:
        u32.keybd_event(VK_CONTROL, 0, 0, 0); u32.keybd_event(VK_MENU, 0, 0, 0)
        for _ in range(n_down):
            u32.keybd_event(ord("T"), 0, 0, 0); bekle(30)
        u32.keybd_event(ord("T"), 0, KEYUP, 0); u32.keybd_event(VK_MENU, 0, KEYUP, 0); u32.keybd_event(VK_CONTROL, 0, KEYUP, 0)
    else:
        sc_input(VK_CONTROL, scancode=scancode); sc_input(VK_MENU, scancode=scancode)
        for _ in range(n_down):
            sc_input(ord("T"), scancode=scancode); bekle(30)
        sc_input(ord("T"), True, scancode); sc_input(VK_MENU, True, scancode); sc_input(VK_CONTROL, True, scancode)
    bekle(300); return len(f.olaylar)


def main() -> int:
    app = QtWidgets.QApplication(sys.argv)
    f = Filtre(); app.installNativeEventFilter(f)
    hk = u32.SetWindowsHookExW(WH_KEYBOARD_LL, _kanca_c, None, 0)
    print(f"platform={app.platformName()} LL kanca={'ok' if hk else 'yok'}")
    kanca_kayit.clear(); a = r1(f, True); n_t_down1 = sum(1 for m, vk, fl in kanca_kayit if vk == ord('T') and m in (WM_KEYDOWN, WM_SYSKEYDOWN))
    kanca_kayit.clear(); b = r1(f, False); n_t_down2 = sum(1 for m, vk, fl in kanca_kayit if vk == ord('T') and m in (WM_KEYDOWN, WM_SYSKEYDOWN))
    print(f"r1 keybd_event tek DOWN + 700 ms + UP: NOREPEAT olay={a}  NOREPEAT'siz olay={b}  (LL kancada T DOWN sayisi: {n_t_down1}/{n_t_down2} -> donanim tekrari YOK, kapi [5] ayristiramaz)")
    for sc, ad in ((None, "keybd_event"), (False, "SendInput vk"), (True, "SendInput SCANCODE")):
        a = r2(f, True, 5, sc); b = r2(f, False, 5, sc)
        print(f"r2 {ad}: T DOWN x5 (UP yok): NOREPEAT olay={a} (1 beklenir)  NOREPEAT'siz olay={b} (5 beklenir)")
    # r4: 5 DOWN dizisinde LL kanca 'onceki durum' bayragi (LLKHF yok; bayrak 0x80 = KF_UP, tekrar bayragi LL'de yok)
    kanca_kayit.clear(); r2(f, True, 3, None)
    print(f"r4 LL kanca T olaylari (msg, vk, flags): {[(hex(m), vk, fl) for m, vk, fl in kanca_kayit if vk == ord('T')]}")
    u32.UnregisterHotKey(None, 1)
    if hk: u32.UnhookWindowsHookEx(hk)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
