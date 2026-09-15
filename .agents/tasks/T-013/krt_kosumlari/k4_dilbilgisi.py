"""KRT k4 -- K3 dilbilgisinin izin verdigi kombinasyonlar Windows'ta ne yapiyor? (gercek Windows, TR-Q duzeni)

    python .agents/tasks/T-013/krt_kosumlari/k4_dilbilgisi.py

g1 rezerve kombinasyonlar: RegisterHotKey donusu + GetLastError (yalniz kayit; tehlikeli olanlar ATESLENMEZ)
g2 Alt+Tab kayit + ates: yakalaniyor mu (gorev degistirici bozulur mu)
g3 Shift+T: kayit + ates; odakli QLineEdit'e 'T' ulasiyor mu (kayitli / kayitsiz pozitif kontrol)
g4 AltGr (VK_RMENU) + T: TR-Q duzeninde Ctrl+Alt+T kisayolunu ATESLIYOR mu; ToUnicodeEx AltGr+T ne uretir; QLineEdit'e ulasiyor mu
g5 ayni id iki kayit (docs: 'maintained along with the new hot key'): ates ve UnregisterHotKey(id) hangisini kaldiriyor
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
MOD_ALT, MOD_CONTROL, MOD_SHIFT, MOD_WIN, MOD_NOREPEAT = 0x1, 0x2, 0x4, 0x8, 0x4000
VK_CONTROL, VK_MENU, VK_SHIFT, VK_LWIN, VK_RMENU, VK_LCONTROL, KEYUP = 0x11, 0x12, 0x10, 0x5B, 0xA5, 0xA2, 0x2
VK_TAB, VK_DELETE, VK_ESCAPE, VK_F4, VK_SPACE, VK_F12, VK_SNAPSHOT = 0x09, 0x2E, 0x1B, 0x73, 0x20, 0x7B, 0x2C
u32.GetForegroundWindow.restype = wintypes.HWND
u32.GetKeyboardLayout.restype = wintypes.HKL
u32.ToUnicodeEx.argtypes = [wintypes.UINT, wintypes.UINT, ctypes.POINTER(ctypes.c_ubyte), wintypes.LPWSTR, ctypes.c_int, wintypes.UINT, wintypes.HKL]


def bekle(ms: int) -> None:
    son = time.perf_counter() + ms / 1000
    while time.perf_counter() < son:
        QtWidgets.QApplication.processEvents(); time.sleep(0.002)


def dizi(*adimlar: tuple[int, bool]) -> None:
    for vk, up in adimlar:
        u32.keybd_event(vk, 0, KEYUP if up else 0, 0)


class Filtre(QtCore.QAbstractNativeEventFilter):
    def __init__(self) -> None:
        super().__init__(); self.olaylar: list[int] = []

    def nativeEventFilter(self, eventType, message):  # type: ignore[override]
        msg = wintypes.MSG.from_address(int(message))
        if msg.message == WM_HOTKEY:
            self.olaylar.append(int(msg.wParam)); return True, 0
        return False, 0


def kayit_dene(ad: str, mod: int, vk: int, kimlik: int = 50) -> str:
    k32.SetLastError(0)
    ok = bool(u32.RegisterHotKey(None, kimlik, mod | MOD_NOREPEAT, vk)); err = k32.GetLastError()
    if ok: u32.UnregisterHotKey(None, kimlik)
    return f"{ad}: kayit={ok} err={err}"


def to_unicode(vk: int, ctrl: bool, alt: bool, shift: bool = False) -> str:
    st = (ctypes.c_ubyte * 256)()
    if ctrl: st[VK_CONTROL] = 0x80; st[VK_LCONTROL] = 0x80
    if alt: st[VK_MENU] = 0x80; st[VK_RMENU] = 0x80
    if shift: st[VK_SHIFT] = 0x80
    buf = ctypes.create_unicode_buffer(8); hkl = u32.GetKeyboardLayout(0)
    n = u32.ToUnicodeEx(vk, u32.MapVirtualKeyW(vk, 0), st, buf, 8, 0, hkl)
    return repr(buf.value[:max(n, 0)]) + f" (n={n})"


def main() -> int:
    sys.stdout.reconfigure(encoding="ascii", errors="backslashreplace")  # ASCII disi -> \uXXXX
    app = QtWidgets.QApplication(sys.argv)
    f = Filtre(); app.installNativeEventFilter(f)
    buf = ctypes.create_unicode_buffer(16); u32.GetKeyboardLayoutNameW(buf)
    print(f"platform={app.platformName()} klavye duzeni={buf.value} (0000041F = Turkce Q)")

    # g1 rezerve kombinasyonlar -- yalniz kayit
    print("g1 rezerve kombinasyonlar (yalniz kayit, ates YOK):")
    for ad, mod, vk in (
        ("Win+L", MOD_WIN, ord("L")), ("Win+Tab", MOD_WIN, VK_TAB), ("Win+D", MOD_WIN, ord("D")), ("Win+E", MOD_WIN, ord("E")),
        ("Win+R", MOD_WIN, ord("R")), ("Win+T", MOD_WIN, ord("T")), ("Win+X", MOD_WIN, ord("X")), ("Win+Space", MOD_WIN, VK_SPACE),
        ("Win+G", MOD_WIN, ord("G")), ("Win+Shift+S", MOD_WIN | MOD_SHIFT, ord("S")), ("Win+1", MOD_WIN, ord("1")),
        ("Ctrl+Alt+Del", MOD_CONTROL | MOD_ALT, VK_DELETE), ("Ctrl+Shift+Esc", MOD_CONTROL | MOD_SHIFT, VK_ESCAPE),
        ("Alt+Tab", MOD_ALT, VK_TAB), ("Alt+F4", MOD_ALT, VK_F4), ("Alt+Esc", MOD_ALT, VK_ESCAPE), ("Ctrl+Esc", MOD_CONTROL, VK_ESCAPE),
        ("Alt+Space", MOD_ALT, VK_SPACE), ("Ctrl+Alt+F12", MOD_CONTROL | MOD_ALT, VK_F12), ("Alt+PrintScreen", MOD_ALT, VK_SNAPSHOT),
        ("Shift+T", MOD_SHIFT, ord("T")), ("Shift+Space", MOD_SHIFT, VK_SPACE), ("Ctrl+C", MOD_CONTROL, ord("C")), ("Ctrl+Alt+T", MOD_CONTROL | MOD_ALT, ord("T")),
    ):
        print("   " + kayit_dene(ad, mod, vk))

    # g2 Alt+Tab ates
    ok = bool(u32.RegisterHotKey(None, 51, MOD_ALT | MOD_NOREPEAT, VK_TAB)); f.olaylar.clear()
    on0 = int(u32.GetForegroundWindow() or 0)
    dizi((VK_MENU, False), (VK_TAB, False), (VK_TAB, True), (VK_MENU, True)); bekle(400)
    on1 = int(u32.GetForegroundWindow() or 0); u32.UnregisterHotKey(None, 51)
    print(f"g2 Alt+Tab kayit={ok}: ates -> olay={len(f.olaylar)} (1 ise gorev degistirici BIZE geldi, Windows'a gitmedi) on plan degisti={on0 != on1}")

    # g3 Shift+T + odakli QLineEdit
    w = QtWidgets.QWidget(); w.setWindowTitle("KRT k4"); le = QtWidgets.QLineEdit(w); w.resize(300, 80); w.show(); w.raise_(); w.activateWindow(); le.setFocus(); bekle(500)
    odakta = int(u32.GetForegroundWindow() or 0) == int(w.winId())
    le.clear(); dizi((VK_SHIFT, False), (ord("T"), False), (ord("T"), True), (VK_SHIFT, True)); bekle(300)
    print(f"g3 pozitif kontrol (kayitsiz) Shift+T -> QLineEdit metni={le.text()!r} (on planda={odakta}; 'T' beklenir)")
    ok = bool(u32.RegisterHotKey(None, 52, MOD_SHIFT | MOD_NOREPEAT, ord("T"))); f.olaylar.clear(); le.clear()
    dizi((VK_SHIFT, False), (ord("T"), False), (ord("T"), True), (VK_SHIFT, True)); bekle(300)
    print(f"g3 Shift+T kayitli={ok}: olay={len(f.olaylar)} QLineEdit metni={le.text()!r} (kisayol harfi YUTAR: buyuk T yazilamaz)")
    u32.UnregisterHotKey(None, 52)

    # g4 AltGr + T (TR-Q: AltGr+T = Turk lirasi isareti)
    print(f"g4 ToUnicodeEx T: duz={to_unicode(ord('T'), False, False)} Ctrl+Alt(AltGr)={to_unicode(ord('T'), True, True)}  R: AltGr={to_unicode(ord('R'), True, True)}  Q: AltGr={to_unicode(ord('Q'), True, True)}")
    le.clear(); dizi((VK_RMENU, False), (ord("T"), False), (ord("T"), True), (VK_RMENU, True)); bekle(300)
    print(f"g4 pozitif kontrol (kayitsiz) AltGr+T -> QLineEdit metni={le.text()!r} (Turk lirasi beklenir; ASCII disi ise 'U+20BA' yazilir)".replace("₺", "U+20BA"))
    ok = bool(u32.RegisterHotKey(None, 53, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, ord("T"))); f.olaylar.clear(); le.clear()
    dizi((VK_RMENU, False), (ord("T"), False), (ord("T"), True), (VK_RMENU, True)); bekle(300)
    m = le.text().replace("₺", "U+20BA")
    print(f"g4 Ctrl+Alt+T kayitli={ok}: AltGr+T (yalniz VK_RMENU) -> olay={len(f.olaylar)} QLineEdit metni={m!r}")
    f.olaylar.clear(); le.clear()
    dizi((VK_LCONTROL, False), (VK_RMENU, False), (ord("T"), False), (ord("T"), True), (VK_RMENU, True), (VK_LCONTROL, True)); bekle(300)
    m = le.text().replace("₺", "U+20BA")
    print(f"g4 Ctrl+Alt+T kayitli: LCtrl+RMenu+T (donanim AltGr dizisi) -> olay={len(f.olaylar)} QLineEdit metni={m!r}")
    # AltGr durumunda Ctrl'nin async durumu
    dizi((VK_RMENU, False)); bekle(50); ctrl_async = int(u32.GetAsyncKeyState(VK_CONTROL)) & 0x8000; lctrl = int(u32.GetAsyncKeyState(VK_LCONTROL)) & 0x8000; dizi((VK_RMENU, True)); bekle(50)
    print(f"g4 VK_RMENU basiliyken GetAsyncKeyState(VK_CONTROL) basili={bool(ctrl_async)} LCONTROL={bool(lctrl)} (duzenin AltGr bayragi Ctrl sentezliyor mu)")
    u32.UnregisterHotKey(None, 53)
    # Ctrl+Alt+R ve AltGr+R
    ok = bool(u32.RegisterHotKey(None, 54, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, ord("R"))); f.olaylar.clear(); le.clear()
    dizi((VK_RMENU, False), (ord("R"), False), (ord("R"), True), (VK_RMENU, True)); bekle(300)
    print(f"g4 Ctrl+Alt+R kayitli={ok}: AltGr+R -> olay={len(f.olaylar)} QLineEdit metni={le.text()!r}")
    u32.UnregisterHotKey(None, 54)
    w.close()

    # g5 ayni id iki kayit
    ok1 = bool(u32.RegisterHotKey(None, 60, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, ord("T")))
    k32.SetLastError(0); ok2 = bool(u32.RegisterHotKey(None, 60, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, ord("Y"))); err2 = k32.GetLastError()
    f.olaylar.clear(); dizi((VK_CONTROL, False), (VK_MENU, False), (ord("T"), False), (ord("T"), True), (VK_MENU, True), (VK_CONTROL, True)); bekle(250)
    dizi((VK_CONTROL, False), (VK_MENU, False), (ord("Y"), False), (ord("Y"), True), (VK_MENU, True), (VK_CONTROL, True)); bekle(250)
    print(f"g5 id=60 Ctrl+Alt+T kayit={ok1}; id=60 Ctrl+Alt+Y kayit={ok2} err={err2}; ates T,Y -> olaylar={f.olaylar}")
    u1 = bool(u32.UnregisterHotKey(None, 60)); f.olaylar.clear()
    dizi((VK_CONTROL, False), (VK_MENU, False), (ord("T"), False), (ord("T"), True), (VK_MENU, True), (VK_CONTROL, True)); bekle(250)
    dizi((VK_CONTROL, False), (VK_MENU, False), (ord("Y"), False), (ord("Y"), True), (VK_MENU, True), (VK_CONTROL, True)); bekle(250)
    print(f"g5 UnregisterHotKey(60) x1={u1} -> ates T,Y -> olaylar={f.olaylar}")
    u2 = bool(u32.UnregisterHotKey(None, 60)); f.olaylar.clear()
    dizi((VK_CONTROL, False), (VK_MENU, False), (ord("T"), False), (ord("T"), True), (VK_MENU, True), (VK_CONTROL, True)); bekle(250)
    dizi((VK_CONTROL, False), (VK_MENU, False), (ord("Y"), False), (ord("Y"), True), (VK_MENU, True), (VK_CONTROL, True)); bekle(250)
    print(f"g5 UnregisterHotKey(60) x2={u2} -> ates T,Y -> olaylar={f.olaylar}")
    u3 = bool(u32.UnregisterHotKey(None, 60)); print(f"g5 UnregisterHotKey(60) x3={u3} err={k32.GetLastError()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
