"""Tester-B yardimci: oturum kilit tespiti (KRT k1 hatasindan ders: WTSINFOEX hizalama yerine on plan sureci + giris masaustu)."""
from __future__ import annotations

import ctypes
import time
from ctypes import wintypes

u32 = ctypes.windll.user32
k32 = ctypes.windll.kernel32
u32.GetForegroundWindow.restype = wintypes.HWND
u32.OpenInputDesktop.restype = wintypes.HANDLE
u32.OpenInputDesktop.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
u32.CloseDesktop.argtypes = [wintypes.HANDLE]


def surec_adi(h: int) -> str:
    pid = wintypes.DWORD(); u32.GetWindowThreadProcessId(wintypes.HWND(h), ctypes.byref(pid))
    hp = k32.OpenProcess(0x1000, False, pid.value)
    if not hp:
        return f"pid{pid.value}"
    buf = ctypes.create_unicode_buffer(1024); n = wintypes.DWORD(1024)
    k32.QueryFullProcessImageNameW(hp, 0, buf, ctypes.byref(n)); k32.CloseHandle(hp)
    return buf.value.split("\\")[-1].lower()


def giris_masaustu() -> str:
    h = u32.OpenInputDesktop(0, False, 0x0001)
    if not h:
        return "(acilamadi: guvenli masaustu)"
    buf = ctypes.create_unicode_buffer(256); n = wintypes.DWORD()
    u32.GetUserObjectInformationW(h, 2, buf, 512, ctypes.byref(n)); u32.CloseDesktop(h)
    return buf.value


def kilitli() -> tuple[bool, str]:
    fg = int(u32.GetForegroundWindow() or 0)
    ad = surec_adi(fg) if fg else "(on plan yok)"
    masa = giris_masaustu()
    k = ad in ("lockapp.exe", "logonui.exe") or masa != "Default" or not fg
    return k, f"on plan sureci={ad} giris masaustu={masa}"


def kilit_bekle(azami_s: float, aralik_s: float = 5.0) -> bool:
    """Kilit acilana kadar bekler; acildiysa True."""
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < azami_s:
        k, _ = kilitli()
        if not k:
            return True
        time.sleep(aralik_s)
    return not kilitli()[0]
