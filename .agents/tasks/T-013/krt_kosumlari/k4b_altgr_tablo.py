"""KRT k4b -- etkin duzende (TR-Q) AltGr+<harf/rakam> hangi karakteri uretir (ToUnicodeEx, kayit YOK) + Win+ bos kombinasyon var mi.

    python .agents/tasks/T-013/krt_kosumlari/k4b_altgr_tablo.py
"""
from __future__ import annotations
import ctypes, string, sys
from ctypes import wintypes
sys.stdout.reconfigure(encoding="ascii", errors="backslashreplace")
u32 = ctypes.windll.user32; k32 = ctypes.windll.kernel32
u32.GetKeyboardLayout.restype = wintypes.HKL
u32.ToUnicodeEx.argtypes = [wintypes.UINT, wintypes.UINT, ctypes.POINTER(ctypes.c_ubyte), wintypes.LPWSTR, ctypes.c_int, wintypes.UINT, wintypes.HKL]
VK_CONTROL, VK_MENU, VK_LCONTROL, VK_RMENU, VK_SHIFT = 0x11, 0x12, 0xA2, 0xA5, 0x10
buf = ctypes.create_unicode_buffer(16); u32.GetKeyboardLayoutNameW(buf); print(f"duzen={buf.value}")
hkl = u32.GetKeyboardLayout(0)
def tu(vk, shift=False):
    st = (ctypes.c_ubyte * 256)(); st[VK_CONTROL] = st[VK_LCONTROL] = st[VK_MENU] = st[VK_RMENU] = 0x80
    if shift: st[VK_SHIFT] = 0x80
    b = ctypes.create_unicode_buffer(8); n = u32.ToUnicodeEx(vk, u32.MapVirtualKeyW(vk, 0), st, b, 8, 0, hkl)
    # olu tus durumunu temizle
    st2 = (ctypes.c_ubyte * 256)(); b2 = ctypes.create_unicode_buffer(8); u32.ToUnicodeEx(0x20, u32.MapVirtualKeyW(0x20, 0), st2, b2, 8, 0, hkl)
    return (b.value[:n] if n > 0 else ("OLU" if n < 0 else "")), n
dolu = []
for ch in string.ascii_uppercase + string.digits:
    s, n = tu(ord(ch))
    if s: dolu.append(f"{ch}={s!r}")
print("AltGr+<tus> dolu olanlar (Ctrl+Alt+<tus> kisayolu bunlari CALAR): " + "  ".join(dolu))
dolu_s = []
for ch in string.ascii_uppercase + string.digits:
    s, n = tu(ord(ch), shift=True)
    if s: dolu_s.append(f"{ch}={s!r}")
print("AltGr+Shift+<tus> dolu olanlar: " + "  ".join(dolu_s))
# Win+ bos kombinasyon var mi?
bos = []
for ch in string.ascii_uppercase + string.digits:
    k32.SetLastError(0); ok = bool(u32.RegisterHotKey(None, 70, 0x8 | 0x4000, ord(ch)))
    if ok: u32.UnregisterHotKey(None, 70); bos.append(ch)
print(f"Win+<harf/rakam> kayit EDILEBILEN (bos) olanlar: {bos}")
bos_f = []
for i in range(1, 13):
    k32.SetLastError(0); ok = bool(u32.RegisterHotKey(None, 70, 0x8 | 0x4000, 0x70 + i - 1))
    if ok: u32.UnregisterHotKey(None, 70); bos_f.append(f"F{i}")
print(f"Win+F1..F12 kayit edilebilen: {bos_f}")
# tek degistirici + harf hangi sistem kisayollarini calar (yalniz kayit donusu)
for mod, ad in ((0x2, "Ctrl"), (0x1, "Alt"), (0x4, "Shift")):
    alinan = []
    for ch in string.ascii_uppercase:
        k32.SetLastError(0); ok = bool(u32.RegisterHotKey(None, 71, mod | 0x4000, ord(ch)))
        if ok: u32.UnregisterHotKey(None, 71)
        else: alinan.append(f"{ch}:{k32.GetLastError()}")
    print(f"{ad}+<harf> kayit EDILEMEYEN: {alinan or 'yok -> 26 harfin hepsi kaydedilebilir (sistem geneli calinir)'}")
