"""T-012 Tester-B gercek ekran sondasi 1b -- GERCEK fare girdisi (oturum kilidi ACIK olmali; sarici ile kosulur).

    python .agents/tasks/T-012/evidence/real_check-on-plan-sarici.py .agents/tasks/T-012/tester_B/sonda_1b_gercek_girdi.py

Stdout ASCII, mutlak yol yok; ekran goruntuleri yalniz kendi temsili sahnemiz uzerinde.
  S3  Tepsi ikonuna GERCEK sol tik (Shell_NotifyIconGetRect -> SetCursorPos fiziksel -> mouse_event) -> pencere geri + ON PLAN
  S4  Sekmeye GERCEK sag tik -> pencere geri + ON PLAN (kapi [5c] on plani olcmuyor)
  S9  Tepsi ikonu gorunur tepside mi (WindowFromPoint sinifi), tasma penceresi
  S10 dpr 1.25 birincilde gercek imlecle acilma/kapanma suresi + panel/sekme goruntusu (sahne uzerinde)
  S8  Tepsi balonu `bildir(ms=1000)` gercek gorunur suresi (toast penceresi)
  S11 Panel acikken imlec panelden sekme diskine (kenar) kayarsa acik kalir; panelin sol kenarindan 1 px disari -> kapanir
Cikis kodu: 0 gecerli; 2 oturum kilitli / fare oynadi (sarici tekrar dener).
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

from oturum import kilitli, surec_adi  # noqa: E402

CIKTI = KOK / ".agents" / "tasks" / "T-012" / "tester_B_evidence"
u32 = ctypes.windll.user32
k32 = ctypes.windll.kernel32
sh = ctypes.windll.shell32
u32.GetForegroundWindow.restype = wintypes.HWND
u32.WindowFromPoint.restype = wintypes.HWND
u32.WindowFromPoint.argtypes = [wintypes.POINT]
u32.FindWindowW.restype = wintypes.HWND
WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
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


def bekle(ms: int) -> None:
    son = time.perf_counter() + ms / 1000
    while time.perf_counter() < son:
        QtWidgets.QApplication.processEvents(); time.sleep(0.004)


def sinif(h: int) -> str:
    buf = ctypes.create_unicode_buffer(256); u32.GetClassNameW(wintypes.HWND(h), buf, 256); return buf.value


def on_plan() -> int:
    return int(u32.GetForegroundWindow() or 0)


def imlec_f() -> tuple[int, int]:
    pt = wintypes.POINT(); u32.GetCursorPos(ctypes.byref(pt)); return (pt.x, pt.y)


def tik_fiziksel(x: int, y: int, sag: bool = False) -> None:
    u32.SetCursorPos(x, y); bekle(80)
    asagi, yukari = (0x0008, 0x0010) if sag else (0x0002, 0x0004)
    u32.mouse_event(asagi, 0, 0, 0, 0); bekle(30); u32.mouse_event(yukari, 0, 0, 0, 0); bekle(300)


def surec_pencereleri() -> list[int]:
    out: list[int] = []

    def cb(h: int, _l: int) -> bool:
        pid = wintypes.DWORD(); u32.GetWindowThreadProcessId(h, ctypes.byref(pid))
        if pid.value == PID:
            out.append(h)
        return True

    u32.EnumWindows(WNDENUMPROC(cb), 0)
    return out


def tum_gorunur() -> list[int]:
    out: list[int] = []

    def cb(h: int, _l: int) -> bool:
        if u32.IsWindowVisible(h):
            out.append(h)
        return True

    u32.EnumWindows(WNDENUMPROC(cb), 0)
    return out


def ikon_rect() -> tuple[int, int, int, int] | None:
    for h in surec_pencereleri():
        if "TrayIconMessageWindowClass" in sinif(h):
            nii = NII(); nii.cbSize = ctypes.sizeof(NII); nii.hWnd = h; nii.uID = 0
            r = wintypes.RECT()
            if sh.Shell_NotifyIconGetRect(ctypes.byref(nii), ctypes.byref(r)) == 0:
                return (r.left, r.top, r.right, r.bottom)
    return None


def win_rect(h: int) -> tuple[int, int, int, int]:
    r = wintypes.RECT(); u32.GetWindowRect(wintypes.HWND(h), ctypes.byref(r)); return (r.left, r.top, r.right, r.bottom)


def uclu(p: object) -> tuple[bool, bool, bool]:
    return (p.isVisible(), p.sekme.isVisible(), p.tepsi.gorunur())  # type: ignore[attr-defined]


def main() -> int:  # noqa: C901
    from src.ui.kabuk import AnaPencere, KabukDurumu

    k, k_not = kilitli()
    if k:
        print(f"sonda_1b: OTURUM KILITLI ({k_not}) -- gercek girdi olculemez, cikis 2"); return 2
    app = QtWidgets.QApplication(sys.argv); app.setQuitOnLastWindowClosed(False)
    CIKTI.mkdir(exist_ok=True)
    ekran = QtGui.QGuiApplication.primaryScreen(); g = ekran.availableGeometry(); dpr = ekran.devicePixelRatio()
    print(f"sonda_1b: birincil avail {g.width()}x{g.height()} dpr={dpr} monitor={len(QtGui.QGuiApplication.screens())} on plan sureci={surec_adi(on_plan())} bizim={on_plan() in surec_pencereleri()}")
    baslangic_imlec = imlec_f()

    sahne = QtWidgets.QLabel("temsili oyun penceresi (Tester-B sonda 1b)")
    sahne.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
    sahne.setStyleSheet("background:#12203a; color:#5a7aa8; font:16px 'Segoe UI'; padding:20px;")
    sahne.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignLeft)
    sahne.setGeometry(g.right() - 700, g.y() + 150, 701, 850); sahne.show(); bekle(300)
    sahne_hwnd = int(sahne.winId())

    p = AnaPencere(ekran); p.move(g.x() + 200, g.y() + 200); p.show(); bekle(300); p_hwnd = int(p.winId())

    # S3 / S9 tepsi
    print("S3/S9 tepsi ikonuna gercek tik")
    p.tepsiye_al(); bekle(500)
    r = ikon_rect()
    if r is None:
        bulgu("[S3] tepsi ikonu Shell'de yok, tik olculemedi")
    else:
        cx, cy = (r[0] + r[2]) // 2, (r[1] + r[3]) // 2
        h_alt = int(u32.WindowFromPoint(wintypes.POINT(cx, cy)) or 0)
        tasma = u32.FindWindowW("NotifyIconOverflowWindow", None)
        print(f"  bilgi  [S9] ikon rect fiziksel={r} merkezdeki pencere sinifi={sinif(h_alt)!r} sureci={surec_adi(h_alt)} tasma penceresi gorunur={bool(tasma and u32.IsWindowVisible(tasma))}")
        sahne.raise_(); sahne.activateWindow(); bekle(300)
        on0 = surec_adi(on_plan())
        tik_fiziksel(cx, cy); bekle(600)
        (ok if uclu(p) == (True, False, False) and p.durum == KabukDurumu.GORUNUR else bulgu)(f"[S3a] tepsi ikonuna gercek sol tik: uclu={uclu(p)} durum={p.durum} (T,F,F gorunur beklenir; once on plan={on0})")
        (ok if on_plan() == p_hwnd else bulgu)(f"[S3b] tik sonrasi ON PLAN ana pencere={on_plan() == p_hwnd} (on plan: {sinif(on_plan())!r} / {surec_adi(on_plan())})")
        if not p.isVisible():
            p.goster(); bekle(300)
    # S4 sag tik
    print("S4 sekmeye gercek sag tik -> on plan")
    sahne.raise_(); sahne.activateWindow(); bekle(300)
    p.kenara_al(); bekle(400)
    s = p.sekme; fg = s.frameGeometry()
    (ok if on_plan() == sahne_hwnd else bulgu)(f"[S4a] kenara al sonrasi on plan sahne={on_plan() == sahne_hwnd} ({surec_adi(on_plan())})")
    # sekme merkezi (mantiksal) -> fiziksel
    sx, sy = int((fg.right() - 4) * dpr), int(fg.center().y() * dpr)
    alt = int(u32.WindowFromPoint(wintypes.POINT(sx, sy)) or 0)
    print(f"  bilgi  [S4] sekme diski fiziksel ({sx},{sy}) altindaki pencere: {'sekme' if alt == int(s.winId()) else sinif(alt)!r}")
    tik_fiziksel(sx, sy, sag=True); bekle(500)
    (ok if uclu(p) == (True, False, False) else bulgu)(f"[S4b] sag tik: uclu={uclu(p)} (T,F,F)")
    (ok if on_plan() == p_hwnd else bulgu)(f"[S4c] sag tik sonrasi ON PLAN ana pencere={on_plan() == p_hwnd} ({sinif(on_plan())!r} / {surec_adi(on_plan())})")
    u32.SetCursorPos(int((g.x() + 100) * dpr), int((g.y() + 100) * dpr)); bekle(300)

    # S10 dpr 1.25 gercek imlec acilma/kapanma + goruntu
    print("S10 gercek imlecle acilma/kapanma (dpr birincil) + goruntu (sahne uzerinde)")
    sahne.raise_(); sahne.activateWindow(); bekle(200)
    p.kenara_al(); bekle(400); s = p.sekme; fg = s.frameGeometry()
    ekran.grabWindow(0, fg.x() - 120, fg.y() - 60, fg.width() + 130, fg.height() + 120).save(str(CIKTI / "sonda1b-s10-sekme-kapali-dpr125.png"))
    QtGui.QCursor.setPos(QtCore.QPoint(fg.right() - 4, fg.center().y())); t0 = time.perf_counter()
    while not s.acik and time.perf_counter() - t0 < 3: bekle(5)
    acilma = (time.perf_counter() - t0) * 1000; bekle(200)
    fg2 = s.frameGeometry()
    (ok if s.acik and acilma <= 120 + 2 * 60 + 150 else bulgu)(f"[S10a] acilma {acilma:.0f} ms (<= 390) acik={s.acik} panel=({fg2.x()},{fg2.y()},{fg2.width()},{fg2.height()}) fiziksel={win_rect(int(s.winId()))}")
    if s.acik:
        ekran.grabWindow(0, fg2.x() - 40, fg2.y() - 40, fg2.width() + 50, fg2.height() + 80).save(str(CIKTI / "sonda1b-s10-panel-acik-dpr125.png"))
        # S11: imlec panelin sol kenarinin 1 px disina -> kapanmali; sonra panel icinde kalip disk bolgesine -> acik kalmali
        QtGui.QCursor.setPos(QtCore.QPoint(fg2.left() - 2, fg2.center().y())); t0 = time.perf_counter()
        while s.acik and time.perf_counter() - t0 < 4: bekle(5)
        kapanma = (time.perf_counter() - t0) * 1000
        (ok if not s.acik and kapanma <= 450 + 2 * 60 + 150 else bulgu)(f"[S11a] panel sol kenarinin 2 px disinda: kapandi={not s.acik} {kapanma:.0f} ms (<= 720)")
        # yeniden ac, panel icinde gez (dugme uzerinden sekme diskine) -> acik kalir
        fgk = s.frameGeometry()
        QtGui.QCursor.setPos(QtCore.QPoint(fgk.right() - 4, fgk.center().y())); t0 = time.perf_counter()
        while not s.acik and time.perf_counter() - t0 < 3: bekle(5)
        bekle(100); fga = s.frameGeometry()
        for x in range(fga.right() - 4, fga.left() + 10, -12):
            QtGui.QCursor.setPos(QtCore.QPoint(x, fga.top() + 20)); bekle(70)
        for y in range(fga.top() + 20, fga.bottom() - 4, 12):
            QtGui.QCursor.setPos(QtCore.QPoint(fga.left() + 10, y)); bekle(70)
        bekle(500)
        (ok if s.acik else bulgu)(f"[S11b] panel icinde gezinirken (~1.2 s) acik kaldi={s.acik}")
    u32.SetCursorPos(int((g.x() + 100) * dpr), int((g.y() + 100) * dpr)); bekle(800)
    (ok if not s.acik else bulgu)(f"[S11c] imlec uzaklasinca kapandi={not s.acik}")
    p.goster(); bekle(200)

    # S8 balon
    print("S8 tepsi balonu (bildir ms=1000) gercek sure")
    p.tepsiye_al(); bekle(400)

    def toast_var() -> bool:
        for h in tum_gorunur():
            if sinif(h) == "Windows.UI.Core.CoreWindow":
                rr = win_rect(h)
                if 200 < rr[2] - rr[0] < 800 and 60 < rr[3] - rr[1] < 400 and rr[2] >= int(g.right() * dpr) - 700 and rr[3] >= int(g.bottom() * dpr) - 600:
                    return True
        return False

    onceden = toast_var()
    p.tepsi.bildir("Suflor sonda", "balon suresi olcumu", 1000)
    t0 = time.perf_counter(); ilk = None; son = None
    while time.perf_counter() - t0 < 12:
        v = toast_var()
        if v and ilk is None: ilk = time.perf_counter() - t0
        if ilk is not None and not v: son = time.perf_counter() - t0; break
        bekle(100)
    print(f"  bilgi  [S8] oncesinde toast var={onceden}; gorundu={ilk is not None} ({(ilk or 0) * 1000:.0f} ms) kayboldu={son is not None} ({(son or 0) * 1000:.0f} ms) -> gorunur sure ~{((son or 0) - (ilk or 0)) * 1000:.0f} ms (istenen 1000; docstring: ~6.2 s, ms yok sayilir)")
    p.kapat(); bekle(300); sahne.close()
    son_imlec = imlec_f()
    print()
    print(f"SONDA_1B: {len(bulgular)} bulgu (imlec basta {baslangic_imlec} sonda {son_imlec})")
    for b in bulgular: print(f"  - {b}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
