"""T-012 Tester-B TUR 2 gercek ekran sondasi 2a -- oturum kilidinden BAGIMSIZ olculer (fare girdisi yok).

    python .agents/tasks/T-012/tester_B/sonda_2a_tur2_kilitten_bagimsiz.py

Stdout ASCII, mutlak yol yok, ekran goruntusu yok.
  S8  SEKME hwnd'sine gercek WM_CLOSE (PostMessage) kenar durumunda -> `kapandi` 1, ana pencere GORUNUR (IsWindowVisible), durum gorunur,
      Shell'de tepsi ikonu yok (goster() ikonu gizler); tepsisiz konfigurasyonda ayni (O-B1 duzeltmesi, gercek OS yolu)
  S9  Win32 capture semantigi (D-B10'un gercek OS'te gecerliligi): Qt penceresine WM_LBUTTONDOWN gercek hwnd'ye PostMessage ->
      Qt SetCapture yapar mi; ardindan `hide()` -> GetCapture hala o hwnd mi (evet ise OS release'i gizli katmana teslim eder)
  S10 `deleteLater()` + Python referansi tutuluyor (O-B5) gercek ekranda: EnumWindows'ta sekme hwnd'si GORUNUR kaliyor mu;
      onerilen tek satirla (`destroyed.connect(sekme.deleteLater)`) gidiyor mu
  S11 K5 balon: gercek tepside `tepsiye_al()` -> Shell'de ikon var; balon penceresi kilitli oturumda olculemez (bilgi)
Cikis kodu 0.
"""
from __future__ import annotations

import ctypes
import gc
import os
import sys
import time
import weakref
from ctypes import wintypes
from pathlib import Path

os.environ.pop("QT_QPA_PLATFORM", None)
KOK = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(KOK))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from PySide6 import QtCore, QtGui, QtWidgets  # noqa: E402
from shiboken6 import isValid  # noqa: E402

from oturum import kilitli  # noqa: E402

u32 = ctypes.windll.user32
k32 = ctypes.windll.kernel32
sh = ctypes.windll.shell32
u32.GetCapture.restype = wintypes.HWND
u32.SetCapture.restype = wintypes.HWND
WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
WM_CLOSE = 0x0010
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
MK_LBUTTON = 0x0001
PID = k32.GetCurrentProcessId()
bulgular: list[str] = []


class GUID(ctypes.Structure):
    _fields_ = [("Data1", wintypes.DWORD), ("Data2", wintypes.WORD), ("Data3", wintypes.WORD), ("Data4", wintypes.BYTE * 8)]


class NII(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("hWnd", wintypes.HWND), ("uID", wintypes.UINT), ("guidItem", GUID)]


def ok(m: str) -> None:
    print(f"  ok     {m}")


def bulgu(m: str) -> None:
    bulgular.append(m); print(f"  BULGU  {m}")


def bilgi(m: str) -> None:
    print(f"  bilgi  {m}")


def bekle(ms: int) -> None:
    """QEventLoop tabanli (dongu seviyesi 1): `deleteLater` (DeferredDelete) ISLENIR -- dongu seviyesi 0'da `processEvents()` islemez
    (ilk kosumda S10 bu yuzden gecersizdi: C++ AnaPencere hic silinmemisti, S11'e tepsi ikonu sizmisti)."""
    dongu = QtCore.QEventLoop()
    QtCore.QTimer.singleShot(ms, dongu.quit)
    dongu.exec()


def sinif(h: int) -> str:
    buf = ctypes.create_unicode_buffer(256); u32.GetClassNameW(wintypes.HWND(h), buf, 256); return buf.value


def surec_pencereleri(sadece_gorunur: bool = False) -> list[int]:
    out: list[int] = []

    def cb(h: wintypes.HWND, _l: wintypes.LPARAM) -> bool:
        pid = wintypes.DWORD(); u32.GetWindowThreadProcessId(h, ctypes.byref(pid))
        if pid.value == PID and (not sadece_gorunur or u32.IsWindowVisible(h)):
            out.append(int(h))
        return True

    u32.EnumWindows(WNDENUMPROC(cb), 0)
    return out


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


def main() -> int:  # noqa: C901
    from src.ui.kabuk import AnaPencere, KabukDurumu

    app = QtWidgets.QApplication(sys.argv); app.setQuitOnLastWindowClosed(False)
    ekran = QtGui.QGuiApplication.primaryScreen(); g = ekran.availableGeometry()
    k, k_not = kilitli()
    print(f"sonda_2a: birincil avail {g.width()}x{g.height()} dpr={ekran.devicePixelRatio()} tepsi={QtWidgets.QSystemTrayIcon.isSystemTrayAvailable()} oturum kilitli={k} ({k_not})")

    print("S8 sekme hwnd'sine gercek WM_CLOSE (kenar durumunda) -> goster()")
    for tepsili in (True, False):
        p = AnaPencere(ekran, tepsi_kullanilabilir=tepsili); kapandi: list[int] = []; cikis: list[int] = []
        p.sekme.kapandi.connect(lambda: kapandi.append(1)); p.cikis_istendi.connect(lambda: cikis.append(1))
        p.move(g.x() + 200, g.y() + 200); p.show(); bekle(300); p.kenara_al(); bekle(400)
        s_hwnd = int(p.sekme.winId()); p_hwnd = int(p.winId())
        once = (uclu(p), str(p.durum), bool(u32.IsWindowVisible(wintypes.HWND(s_hwnd))), ikon_rect() is not None)
        u32.PostMessageW(wintypes.HWND(s_hwnd), WM_CLOSE, 0, 0); bekle(600)
        sonra = (uclu(p), str(p.durum), bool(u32.IsWindowVisible(wintypes.HWND(p_hwnd))), bool(u32.IsWindowVisible(wintypes.HWND(s_hwnd))), ikon_rect() is not None)
        iyi = kapandi == [1] and cikis == [] and not p.kapandi and p.durum is KabukDurumu.GORUNUR and uclu(p) == (True, False, False) and sonra[2] and not sonra[3] and sonra[4] is False and not p.sekme.yokluyor
        (ok if iyi else bulgu)(f"[S8 tepsili={tepsili}] once uclu/durum/sekme-hwnd-gorunur/Shell-ikon={once} -> WM_CLOSE(sekme): kapandi={len(kapandi)} cikis={len(cikis)} durum={p.durum} uclu={uclu(p)} ana-hwnd gorunur={sonra[2]} sekme-hwnd gorunur={sonra[3]} Shell ikon var={sonra[4]} yokluyor={p.sekme.yokluyor}")
        p.kenara_al(); bekle(300)
        s_hwnd2 = int(p.sekme.winId())  # close() (QWindow::event Close -> destroy()) platform penceresini YIKAR; yeniden show yeni hwnd yaratir
        (ok if uclu(p) == (False, True, tepsili) and p.sekme.yokluyor and bool(u32.IsWindowVisible(wintypes.HWND(s_hwnd2))) else bulgu)(f"[S8 tepsili={tepsili}] yeniden kenara al: uclu={uclu(p)} yokluyor={p.sekme.yokluyor} yeni sekme-hwnd gorunur={bool(u32.IsWindowVisible(wintypes.HWND(s_hwnd2)))} hwnd degisti={s_hwnd2 != s_hwnd} (eski hwnd yikildi; hwnd onbellekleyen cagiran icin belge)")
        p.kapat(); bekle(200)

    print("S9 Win32 capture: gercek hwnd'ye WM_LBUTTONDOWN -> Qt SetCapture? -> hide() -> GetCapture?")
    w = QtWidgets.QWidget()
    w.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.Tool | QtCore.Qt.WindowType.WindowStaysOnTopHint)
    w.setGeometry(g.x() + 300, g.y() + 300, 200, 200); w.show(); bekle(300)
    w_hwnd = int(w.winId())
    basildi: list[int] = []; birakildi: list[int] = []
    w.mousePressEvent = lambda e: basildi.append(1)  # type: ignore[method-assign]
    w.mouseReleaseEvent = lambda e: birakildi.append(1)  # type: ignore[method-assign]
    u32.PostMessageW(wintypes.HWND(w_hwnd), WM_LBUTTONDOWN, MK_LBUTTON, (50 << 16) | 50); bekle(200)
    cap_basili = int(u32.GetCapture() or 0)
    w.hide(); bekle(200)
    cap_gizli = int(u32.GetCapture() or 0)
    u32.PostMessageW(wintypes.HWND(w_hwnd), WM_LBUTTONUP, 0, (60 << 16) | 60); bekle(200)
    bilgi(f"[S9] press geldi={len(basildi)} -> GetCapture==hwnd (Qt capture aldi)={cap_basili == w_hwnd}; hide() sonrasi GetCapture={'hwnd' if cap_gizli == w_hwnd else cap_gizli} (0 ise OS SW_HIDE'da capture'i birakir); gizli pencereye POST edilen release Qt'ye ulasti={len(birakildi)}")
    if cap_basili == w_hwnd and cap_gizli == w_hwnd:
        bulgu("[S9] hide() capture'i BIRAKMIYOR: OS, Esc sonrasi gercek release'i gizli SecimKatmani'na teslim eder -> D-B10 gercek ekranda da gecerli")
    elif cap_basili == w_hwnd:
        ok("[S9] hide() capture'i birakiyor: gercek release gizli katmana OS tarafindan gitmez (D-B10 yalniz Qt-ici/QTest yolunda; belge)")
    else:
        bilgi("[S9] Qt PostMessage ile capture almadi (gercek girdi degil) -- olcu belirsiz; kilit acilinca gercek fare ile")
    w.close(); bekle(100)

    print("S10 deleteLater + Python referansi tutuluyor (O-B5) gercek ekranda")
    for duzeltme in (False, True):
        p = AnaPencere(ekran); p.move(g.x() + 200, g.y() + 200); p.show(); bekle(300); p.kenara_al(); bekle(400)
        if duzeltme:
            p.destroyed.connect(p.sekme.deleteLater)
        s_hwnd = int(p.sekme.winId()); wr = weakref.ref(p.sekme)
        p.deleteLater(); bekle(400); gc.collect(); bekle(200)
        s = wr(); s = s if (s is not None and isValid(s)) else None
        hwnd_gorunur = s_hwnd in surec_pencereleri(sadece_gorunur=True)
        ikon = ikon_rect() is not None
        cpp_olu = not isValid(p)
        durum = f"[S10 duzeltme={duzeltme}] C++ AnaPencere olu={cpp_olu} sekme sarmalayici canli={s is not None} sekme hwnd EnumWindows'ta GORUNUR={hwnd_gorunur} yokluyor={bool(s is not None and s.yokluyor)} Shell ikon var={ikon}"
        if duzeltme:
            (ok if cpp_olu and s is None and not hwnd_gorunur else bulgu)(durum)
        else:
            (bulgu if hwnd_gorunur else ok)(durum + " -> ZOMBI: ana pencere yok, ikon yok, yarim daire ekranda")
        if s is not None:
            s.hide(); s.deleteLater()
        del p; gc.collect(); bekle(200)

    print("S11 K5 balon (gercek tepsi)")
    AnaPencere._balon_gosterildi = False  # noqa: SLF001  (surec basi durumu)
    p = AnaPencere(ekran); p.move(g.x() + 200, g.y() + 200); p.show(); bekle(300)
    p.tepsiye_al(); bekle(500)
    bilgi(f"[S11] tepsiye_al: Shell ikon var={ikon_rect() is not None} balon bayragi={AnaPencere._balon_gosterildi} (balon penceresi kilitli oturumda gorulemez -- sef kilit acikken: balon ~6 s, sag alt)")  # noqa: SLF001
    p.goster(); bekle(200); p.tepsiye_al(); bekle(200)
    bilgi(f"[S11] ikinci tepsiye_al: ikon var={ikon_rect() is not None} (balon bir daha gosterilmez: bayrak {AnaPencere._balon_gosterildi})")  # noqa: SLF001
    p.kapat(); bekle(300)
    (ok if ikon_rect() is None else bulgu)(f"[S11] kapat: Shell'de ikon yok={ikon_rect() is None}")

    print()
    print(f"SONDA_2A: {len(bulgular)} bulgu")
    for b in bulgular:
        print(f"  - {b}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
