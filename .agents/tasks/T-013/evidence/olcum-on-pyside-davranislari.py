"""T-013 implementer on olcumu -- tasarim kararlarindan ONCE PySide6 6.11 / Win32 olgulari (offscreen + gercek ToUnicodeEx).

    python .agents/tasks/T-013/evidence/olcum-on-pyside-davranislari.py

o1 `destroyed.connect(functools.partial(fn, ...))`: PySide partial'i kac argumanla cagiriyor (`*_` ile guvenli mi)
o2 `nativeEventFilter` eventType: QByteArray == bytes karsilastirmasi ve `bytes(QByteArray)`
o3 `installNativeEventFilter` Python sarmalayicisini canli tutuyor mu; `removeNativeEventFilter` sonrasi birakiyor mu
o4 filtre -> servis weakref yolu: servis `del`+gc ile toplanir mi (filtre kurulu iken), destroyed partial'i kosar mi
o5 gercek ToUnicodeEx (Ctrl+Alt durumu, etkin duzen): harf/rakam disindaki tablo tuslari (Space, Tab, Enter, Esc,
   Backspace, Delete, F1, Home, Left) karakter uretiyor mu -- `ALTGR_CAKISMA` sorgusunun hangi tuslarda anlamli oldugu
o6 QThread.currentThread() is app.thread(): ana thread True, Python thread False (KRT k7 tekrar)
Kayit YAPILMAZ (RegisterHotKey cagrilmaz). Stdout ASCII.
"""
from __future__ import annotations

import ctypes
import functools
import gc
import os
import sys
import threading
import weakref
from ctypes import wintypes

os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.stdout.reconfigure(encoding="ascii", errors="backslashreplace")  # type: ignore[union-attr]

from PySide6 import QtCore, QtWidgets  # noqa: E402

log: list[object] = []


def serbest(etiket: str, *args: object) -> None:
    log.append((etiket, len(args)))


class Servis(QtCore.QObject):
    def __init__(self) -> None:
        super().__init__()
        self.destroyed.connect(functools.partial(serbest, "partial"))


class Filtre(QtCore.QAbstractNativeEventFilter):
    def __init__(self, servis: weakref.ref[QtCore.QObject]) -> None:
        super().__init__()
        self.servis = servis

    def nativeEventFilter(self, eventType: object, message: int) -> tuple[bool, int]:  # type: ignore[override]
        return False, 0


def main() -> int:
    app = QtWidgets.QApplication(sys.argv)
    # o1
    s = Servis(); del s; gc.collect()
    print(f"o1 destroyed -> partial(serbest, 'partial') cagrildi: {log}  (('partial', n): n = PySide'in gecirdigi ek arguman sayisi)")
    # o2
    qba = QtCore.QByteArray(b"windows_generic_MSG")
    print(f"o2 QByteArray == bytes: {qba == b'windows_generic_MSG'}; bytes(QByteArray) == bytes: {bytes(qba) == b'windows_generic_MSG'}; "
          f"bytes(b'..') gecer: {bytes(b'windows_generic_MSG') == b'windows_generic_MSG'}; farkli: {bytes(QtCore.QByteArray(b'xcb')) == b'windows_generic_MSG'}")
    # o3
    f = Filtre(weakref.ref(app)); wf = weakref.ref(f); app.installNativeEventFilter(f); del f; gc.collect()
    canli_kurulu = wf() is not None
    f2 = wf()
    if f2 is not None:
        app.removeNativeEventFilter(f2); del f2
    gc.collect()
    print(f"o3 installNativeEventFilter sonrasi Python referansi dusuruldu: sarmalayici canli={canli_kurulu}; removeNativeEventFilter + gc sonrasi canli={wf() is not None}")
    # o4
    s2 = Servis(); ws = weakref.ref(s2); f3 = Filtre(weakref.ref(s2)); app.installNativeEventFilter(f3)
    s2.destroyed.connect(functools.partial(app.removeNativeEventFilter, f3))
    log.clear(); del s2; gc.collect()
    print(f"o4 filtre weakref(servis) tutarken servis del+gc: sarmalayici None={ws() is None}; destroyed partial kostu={log}; filtre weakref cagrisi None={f3.servis() is None}")
    # o5 gercek ToUnicodeEx
    u32 = ctypes.WinDLL("user32", use_last_error=True)
    u32.GetKeyboardLayout.restype = wintypes.HKL
    u32.ToUnicodeEx.argtypes = [wintypes.UINT, wintypes.UINT, ctypes.POINTER(ctypes.c_ubyte), wintypes.LPWSTR, ctypes.c_int, wintypes.UINT, wintypes.HKL]
    u32.ToUnicodeEx.restype = ctypes.c_int
    ad = ctypes.create_unicode_buffer(16); u32.GetKeyboardLayoutNameW(ad)
    hkl = u32.GetKeyboardLayout(0)

    def altgr(vk: int) -> tuple[str, int]:
        st = (ctypes.c_ubyte * 256)()
        for k in (0x11, 0xA2, 0x12, 0xA5):
            st[k] = 0x80
        b = ctypes.create_unicode_buffer(8)
        n = u32.ToUnicodeEx(vk, u32.MapVirtualKeyW(vk, 0), st, b, 8, 0, hkl)
        if n < 0:
            st2 = (ctypes.c_ubyte * 256)(); b2 = ctypes.create_unicode_buffer(8)
            u32.ToUnicodeEx(0x20, u32.MapVirtualKeyW(0x20, 0), st2, b2, 8, 0, hkl)
        return (b.value[:n] if n > 0 else (b[0] if n < 0 else "")), n

    print(f"o5 duzen={ad.value}")
    for isim, vk in (("Space", 0x20), ("Tab", 0x09), ("Enter", 0x0D), ("Esc", 0x1B), ("Backspace", 0x08), ("Delete", 0x2E), ("Insert", 0x2D),
                     ("Home", 0x24), ("End", 0x23), ("PageUp", 0x21), ("PageDown", 0x22), ("Left", 0x25), ("Up", 0x26), ("Right", 0x27), ("Down", 0x28),
                     ("F1", 0x70), ("F11", 0x7A), ("D", ord("D")), ("R", ord("R")), ("T", ord("T")), ("6", ord("6")), ("2", ord("2"))):
        kar, n = altgr(vk)
        print(f"o5 Ctrl+Alt+{isim}: n={n} karakter={kar!r} (kontrol karakteri={bool(kar) and ord(kar[0]) < 0x20})")
    # o6
    son: dict[str, bool] = {}

    def th() -> None:
        son["is"] = QtCore.QThread.currentThread() is app.thread()

    t = threading.Thread(target=th); t.start(); t.join()
    print(f"o6 ana thread currentThread() is app.thread(): {QtCore.QThread.currentThread() is app.thread()}; python thread: {son['is']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
