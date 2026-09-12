"""T-012 Tester-B gercek ekran sondasi 1a -- oturum kilidinden BAGIMSIZ olculer (fare girdisi yok).

    python .agents/tasks/T-012/tester_B/sonda_1a_kilitten_bagimsiz.py

Stdout ASCII, mutlak yol yok, ekran goruntusu yok (goruntuler sonda_1b, kilit acikken, temsili sahne uzerinde).
  S1 Alt-Tab/gorev cubugu adayi (EnumWindows + IsWindowVisible + sahipsiz + !WS_EX_TOOLWINDOW; kendi sahnemiz haric) uc durumda
  S2 Tepsi ikonu var/yok -- Shell_NotifyIconGetRect (Qt'den BAGIMSIZ kanal, kural 8): taze/tepsi/goster/kenar/kapat
  S5 WM_CLOSE uc durumda (taze AnaPencere x3) -> cikis 1, uclu (F,F,F), Shell'de ikon yok, gorunur ust-duzey 0
  S6 Z-sirasi (EnumWindows): sekmeden SONRA gosterilen topmost 'oyun' ve Tool+topmost 'secim katmani'; _ac() raise_()
  S7 DPI != 1 monitor (bugun birincil %125): fiziksel sag kenar vs monitor calisma alani (GetWindowRect / GetMonitorInfo),
     panel fiziksel dikdortgeni monitor icinde; sol kenar; ikinci monitor varsa ayni
Cikis kodu 0.
"""
from __future__ import annotations

import ctypes
import os
import sys
import time
from ctypes import wintypes
from pathlib import Path

os.environ.pop("QT_QPA_PLATFORM", None)
KOK = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(KOK))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from PySide6 import QtCore, QtGui, QtWidgets  # noqa: E402

from oturum import kilitli  # noqa: E402

u32 = ctypes.windll.user32
k32 = ctypes.windll.kernel32
sh = ctypes.windll.shell32
u32.GetWindow.restype = wintypes.HWND
u32.GetWindowLongW.restype = ctypes.c_long
u32.MonitorFromWindow.restype = wintypes.HANDLE
WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
GWL_EXSTYLE = -20
WS_EX_TOOLWINDOW = 0x80
WS_EX_TOPMOST = 0x8
WS_EX_NOACTIVATE = 0x08000000
GW_OWNER = 4
WM_CLOSE = 0x0010
PID = k32.GetCurrentProcessId()
bulgular: list[str] = []


class GUID(ctypes.Structure):
    _fields_ = [("Data1", wintypes.DWORD), ("Data2", wintypes.WORD), ("Data3", wintypes.WORD), ("Data4", wintypes.BYTE * 8)]


class NII(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("hWnd", wintypes.HWND), ("uID", wintypes.UINT), ("guidItem", GUID)]


class MONITORINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", wintypes.RECT), ("rcWork", wintypes.RECT), ("dwFlags", wintypes.DWORD)]


def ok(m: str) -> None:
    print(f"  ok     {m}")


def bulgu(m: str) -> None:
    bulgular.append(m); print(f"  BULGU  {m}")


def bekle(ms: int) -> None:
    son = time.perf_counter() + ms / 1000
    while time.perf_counter() < son:
        QtWidgets.QApplication.processEvents(); time.sleep(0.004)


def sinif(h: int) -> str:
    buf = ctypes.create_unicode_buffer(256); u32.GetClassNameW(wintypes.HWND(h), buf, 256); return buf.value


def surec_pencereleri(sadece_gorunur: bool = False) -> list[int]:
    out: list[int] = []

    def cb(h: int, _l: int) -> bool:
        pid = wintypes.DWORD(); u32.GetWindowThreadProcessId(h, ctypes.byref(pid))
        if pid.value == PID and (not sadece_gorunur or u32.IsWindowVisible(h)):
            out.append(h)
        return True

    u32.EnumWindows(WNDENUMPROC(cb), 0)
    return out


def tum_pencereler_gorunur() -> list[int]:
    out: list[int] = []

    def cb(h: int, _l: int) -> bool:
        if u32.IsWindowVisible(h):
            out.append(h)
        return True

    u32.EnumWindows(WNDENUMPROC(cb), 0)
    return out


def alt_tab_adaylari(haric: set[int]) -> list[str]:
    ad: list[str] = []
    for h in surec_pencereleri(sadece_gorunur=True):
        if h in haric:
            continue
        ex = u32.GetWindowLongW(wintypes.HWND(h), GWL_EXSTYLE) & 0xFFFFFFFF
        if not u32.GetWindow(wintypes.HWND(h), GW_OWNER) and not (ex & WS_EX_TOOLWINDOW):
            ad.append(sinif(h))
    return ad


def tepsi_hwnd() -> int:
    for h in surec_pencereleri():
        if "TrayIconMessageWindowClass" in sinif(h):
            return h
    return 0


def ikon_rect() -> tuple[int, int, int, int] | None:
    h = tepsi_hwnd()
    if not h:
        return None
    nii = NII(); nii.cbSize = ctypes.sizeof(NII); nii.hWnd = h; nii.uID = 0
    r = wintypes.RECT()
    hr = sh.Shell_NotifyIconGetRect(ctypes.byref(nii), ctypes.byref(r))
    return (r.left, r.top, r.right, r.bottom) if hr == 0 else None


def uclu(p: object) -> tuple[bool, bool, bool]:
    return (p.isVisible(), p.sekme.isVisible(), p.tepsi.gorunur())  # type: ignore[attr-defined]


def win_rect(h: int) -> tuple[int, int, int, int]:
    r = wintypes.RECT(); u32.GetWindowRect(wintypes.HWND(h), ctypes.byref(r)); return (r.left, r.top, r.right, r.bottom)


def monitor_bilgi(h: int) -> MONITORINFO:
    mi = MONITORINFO(); mi.cbSize = ctypes.sizeof(MONITORINFO)
    u32.GetMonitorInfoW(u32.MonitorFromWindow(wintypes.HWND(h), 2), ctypes.byref(mi)); return mi


def z_indeks(hwnds: dict[str, int]) -> dict[str, int]:
    sira = tum_pencereler_gorunur()
    return {ad: (sira.index(h) if h in sira else -1) for ad, h in hwnds.items()}


def dpi_olc(e: QtGui.QScreen, etiket: str, sahne_ref: list[QtWidgets.QWidget]) -> None:
    from src.ui.geometri import Kenar
    from src.ui.kabuk import AnaPencere

    g = e.availableGeometry()
    p = AnaPencere(e); p.move(g.x() + 100, g.y() + 100); p.show(); bekle(300)
    p.kenara_al(); bekle(400)
    s = p.sekme; h = int(s.winId()); fg = s.frameGeometry(); r = win_rect(h); mi = monitor_bilgi(h)
    fark = r[2] - mi.rcWork.right
    print(f"  bilgi  [S7 {etiket}] dpr={e.devicePixelRatio()} avail=({g.x()},{g.y()},{g.width()},{g.height()}) sekme mantiksal=({fg.x()},{fg.y()},{fg.width()},{fg.height()}) fiziksel={r} monitor calisma=({mi.rcWork.left},{mi.rcWork.top},{mi.rcWork.right},{mi.rcWork.bottom}) monitor=({mi.rcMonitor.left},{mi.rcMonitor.top},{mi.rcMonitor.right},{mi.rcMonitor.bottom}) sag fark={fark:+d} px")
    (ok if fg.right() == g.right() and g.contains(fg) else bulgu)(f"[S7 {etiket}] mantiksal: sag kenara bitisik={fg.right() == g.right()} ekran icinde={g.contains(fg)}")
    (ok if abs(fark) <= 1 else bulgu)(f"[S7 {etiket}] fiziksel sag kenar farki {fark:+d} (|.|<=1 kabul)")
    if fark > 0:
        bulgu(f"[S7 {etiket}] sekme {fark} fiziksel px monitorun OTESINE tasiyor (KRT G4 sinifi)")
    # panel: _ac() dogrudan (fare yok) -- geometri saf, acik dikdortgen
    s._ac(); bekle(250)  # noqa: SLF001  (kilitli oturumda imlec ile acilamaz; yalniz geometri olculur)
    fg2 = s.frameGeometry(); r2 = win_rect(h)
    icinde_f = mi.rcWork.left <= r2[0] and r2[2] <= mi.rcWork.right + 1 and mi.rcWork.top <= r2[1] and r2[3] <= mi.rcWork.bottom
    (ok if s.acik and g.contains(fg2) and fg2.right() == g.right() and icinde_f else bulgu)(f"[S7 {etiket}] panel mantiksal=({fg2.x()},{fg2.y()},{fg2.width()},{fg2.height()}) icinde={g.contains(fg2)} fiziksel={r2} monitor icinde(+1 tolerans)={icinde_f} sag fark={r2[2] - mi.rcWork.right:+d}")
    s._kapat(); bekle(100)  # noqa: SLF001
    s.kenar = Kenar.SOL; bekle(200); fg3 = s.frameGeometry(); r3 = win_rect(h)
    (ok if fg3.left() == g.left() and abs(r3[0] - mi.rcWork.left) <= 1 else bulgu)(f"[S7 {etiket}] SOL: mantiksal=({fg3.x()},{fg3.y()},{fg3.width()},{fg3.height()}) fiziksel={r3} sol fark={r3[0] - mi.rcWork.left:+d}")
    p.kapat(); bekle(200)


def main() -> int:  # noqa: C901
    from src.ui.kabuk import AnaPencere, KabukDurumu

    app = QtWidgets.QApplication(sys.argv); app.setQuitOnLastWindowClosed(False)
    ekran = QtGui.QGuiApplication.primaryScreen(); g = ekran.availableGeometry()
    k, k_not = kilitli()
    ekranlar = QtGui.QGuiApplication.screens()
    print(f"sonda_1a: birincil avail {g.width()}x{g.height()} dpr={ekran.devicePixelRatio()} monitor sayisi={len(ekranlar)} tepsi={QtWidgets.QSystemTrayIcon.isSystemTrayAvailable()} oturum kilitli={k} ({k_not})")

    sahne = QtWidgets.QLabel("temsili oyun penceresi (Tester-B sonda)")
    sahne.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
    sahne.setStyleSheet("background:#12203a; color:#5a7aa8; font:16px 'Segoe UI'; padding:20px;")
    sahne.setGeometry(g.right() - 700, g.y() + 200, 701, 800); sahne.show(); bekle(200)
    sahne_hwnd = int(sahne.winId()); haric = {sahne_hwnd}

    print("S1/S2 Alt-Tab adaylari ve tepsi ikonu (bagimsiz kanal)")
    p = AnaPencere(ekran); cikis: list[int] = []; p.cikis_istendi.connect(lambda: cikis.append(1))
    p.move(g.x() + 200, g.y() + 200); p.show(); bekle(300)
    (ok if ikon_rect() is None else bulgu)(f"[S2a] taze gorunur: tepsi ikonu Shell'de yok={ikon_rect() is None}")
    (ok if len(alt_tab_adaylari(haric)) == 1 else bulgu)(f"[S1a] gorunur: Alt-Tab adaylari={alt_tab_adaylari(haric)} (1 beklenir)")
    p.tepsiye_al(); bekle(400)
    r_ikon = ikon_rect()
    (ok if r_ikon is not None else bulgu)(f"[S2b] tepsi: ikon Shell'de var={r_ikon is not None} rect={r_ikon}")
    (ok if alt_tab_adaylari(haric) == [] else bulgu)(f"[S1b] tepsi: Alt-Tab adaylari={alt_tab_adaylari(haric)} (0 beklenir)")
    p.goster(); bekle(300)
    (ok if ikon_rect() is None and uclu(p) == (True, False, False) else bulgu)(f"[S2c] goster: ikon Shell'de yok={ikon_rect() is None} uclu={uclu(p)}")
    p.kenara_al(); bekle(400)
    s = p.sekme; s_hwnd = int(s.winId()); ex = u32.GetWindowLongW(wintypes.HWND(s_hwnd), GWL_EXSTYLE) & 0xFFFFFFFF
    (ok if alt_tab_adaylari(haric) == [] and (ex & WS_EX_TOOLWINDOW) else bulgu)(f"[S1c] kenar: Alt-Tab adaylari={alt_tab_adaylari(haric)} (0 beklenir); sekme exstyle TOOLWINDOW={bool(ex & WS_EX_TOOLWINDOW)} TOPMOST={bool(ex & WS_EX_TOPMOST)} NOACTIVATE={bool(ex & WS_EX_NOACTIVATE)}")
    (ok if ikon_rect() is not None else bulgu)(f"[S2d] kenar: ikon Shell'de var={ikon_rect() is not None}")
    p.kapat(); bekle(300)
    (ok if ikon_rect() is None and cikis == [1] and alt_tab_adaylari(haric) == [] else bulgu)(f"[S2e] kapat: ikon Shell'de yok={ikon_rect() is None} cikis={len(cikis)} Alt-Tab adaylari={alt_tab_adaylari(haric)}")

    print("S5 WM_CLOSE uc durumda (PostMessage gercek hwnd)")
    for durum_adi in ("gorunur", "tepsi", "kenar"):
        q = AnaPencere(ekran); qc: list[int] = []; q.cikis_istendi.connect(lambda: qc.append(1))
        q.move(g.x() + 200, g.y() + 200); q.show(); bekle(300)
        {"gorunur": lambda: None, "tepsi": q.tepsiye_al, "kenar": q.kenara_al}[durum_adi](); bekle(300)
        before = (uclu(q), str(q.durum))
        u32.PostMessageW(wintypes.HWND(int(q.winId())), WM_CLOSE, 0, 0); bekle(600)
        gorunur = [w for w in QtWidgets.QApplication.topLevelWidgets() if w.isVisible() and w is not sahne]
        (ok if qc == [1] and uclu(q) == (False, False, False) and ikon_rect() is None and not gorunur and not q.sekme.yokluyor else bulgu)(
            f"[S5 {durum_adi}] once={before} -> WM_CLOSE: cikis={len(qc)} uclu={uclu(q)} Shell ikon yok={ikon_rect() is None} gorunur ust-duzey={len(gorunur)} yokluyor={q.sekme.yokluyor} durum={q.durum}")
        q.kapat(); bekle(100)
        (ok if qc == [1] else bulgu)(f"[S5 {durum_adi}] ikinci kapat(): cikis={len(qc)} (1)")

    print("S6 z-sirasi (EnumWindows; kucuk indeks = ustte)")
    p = AnaPencere(ekran); p.move(g.x() + 200, g.y() + 200); p.show(); bekle(300)
    p.kenara_al(); bekle(300); s = p.sekme; s_hwnd = int(s.winId()); fg = s.frameGeometry()
    oyun = QtWidgets.QLabel("temsili TOPMOST oyun (sekmeden sonra gosterildi)")
    oyun.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.WindowStaysOnTopHint)
    oyun.setStyleSheet("background:#2a1a3a; color:#9a7ac8; font:16px 'Segoe UI'; padding:20px;")
    oyun.setGeometry(g.right() - 500, fg.y() - 200, 501, 500); oyun.show(); bekle(400)
    oyun_hwnd = int(oyun.winId())
    z1 = z_indeks({"sekme": s_hwnd, "oyun": oyun_hwnd})
    print(f"  bilgi  [S6a] topmost oyun sekmeden sonra: z={z1} -> oyun ustte={z1['oyun'] < z1['sekme']} (belgeli sinir K3 [OLCULMUYOR])")
    s._ac(); bekle(200)  # noqa: SLF001  (imlec yerine dogrudan; _ac icindeki raise_ olculuyor)
    z2 = z_indeks({"sekme": s_hwnd, "oyun": oyun_hwnd})
    print(f"  bilgi  [S6b] _ac() sonrasi: z={z2} -> raise_ sekmeyi topmost oyunun ustune aldi={z2['sekme'] < z2['oyun']}")
    s._kapat(); bekle(200)  # noqa: SLF001
    z2b = z_indeks({"sekme": s_hwnd, "oyun": oyun_hwnd})
    print(f"  bilgi  [S6b'] _kapat() sonrasi: z={z2b} -> sekme hala ustte={z2b['sekme'] < z2b['oyun']} (kapali sekme oyunun ustunde kalir mi)")
    oyun.hide(); bekle(200)
    katman = QtWidgets.QWidget()
    katman.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.WindowStaysOnTopHint | QtCore.Qt.WindowType.Tool)
    katman.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
    katman.setGeometry(g); katman.show(); katman.activateWindow(); bekle(400)
    katman_hwnd = int(katman.winId())
    z3 = z_indeks({"sekme": s_hwnd, "katman": katman_hwnd})
    s._ac(); bekle(200)  # noqa: SLF001
    z4 = z_indeks({"sekme": s_hwnd, "katman": katman_hwnd})
    print(f"  bilgi  [S6c] demo SecimKatmani benzeri (Tool+topmost tum ekran) sekmeden sonra: z={z3} katman ustte={z3['katman'] < z3['sekme']}; panel acilinca z={z4} panel katmanin USTUNE cikti={z4['sekme'] < z4['katman']}")
    if z4["sekme"] < z4["katman"]:
        bulgu("[S6c] bolge secimi sirasinda imlec sekme diskine girerse panel SECIM KATMANININ USTUNE cikar (_ac raise_); demo/kabuk.py secim sirasinda sekmeyi gizlemiyor")
    s._kapat(); katman.hide(); bekle(100)  # noqa: SLF001
    p.kapat(); bekle(200)

    print("S7 DPI: birincil ve (varsa) diger monitorler")
    for i, e in enumerate(ekranlar):
        dpi_olc(e, f"ekran{i} {'birincil' if e is ekran else 'ikincil'}", [sahne])
    sahne.close()
    print()
    print(f"SONDA_1A: {len(bulgular)} bulgu")
    for b in bulgular: print(f"  - {b}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
