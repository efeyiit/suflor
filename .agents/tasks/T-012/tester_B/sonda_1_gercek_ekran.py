"""T-012 Tester-B gercek ekran sondasi 1 (ILK SURUM, YERINI sonda_1a + sonda_1b ALDI).

Ilk kosum oturum KILITLIYKEN yapildi (on plan LockApp.exe) -> gercek girdi kalemleri gecersiz
(`tester_B_evidence/sonda1-ILK-KOSUM-oturum-kilitli-gecersiz.txt`); ayrica S1 kendi sahne penceremi de
sayiyordu (1a duzeltti). Kayit icin tutuluyor.

Ozgun aciklama: istek/urun uyumu + kotu kullanim (Win32 bagimsiz kanallar).

    python .agents/tasks/T-012/evidence/real_check-on-plan-sarici.py .agents/tasks/T-012/tester_B/sonda_1_gercek_ekran.py

Sarici: fare 6 s bosta -> surec on plana alinir (gercek tik) -> bu betik cocuk surec. Stdout ASCII, mutlak yol yok.
Ekran goruntuleri yalniz TEMSILI arka plan (kendi sahne penceremiz) uzerinde.
  S1 Alt-Tab/gorev cubugu adayi (EnumWindows + IsWindowVisible + sahipsiz + !WS_EX_TOOLWINDOW) uc durumda
  S2 Tepsi ikonu var/yok -- Shell_NotifyIconGetRect (Qt'den BAGIMSIZ kanal, kural 8): taze/tepsi/goster/kenar/kapat
  S3 Tepsi ikonuna GERCEK tik -> pencere geri + on plan (GetForegroundWindow)
  S4 Sekmeye GERCEK sag tik -> pencere geri + on plan
  S5 WM_CLOSE uc durumda (taze AnaPencere x3) -> cikis 1, uclu (F,F,F), ikon yok
  S6 Z-sirasi: sekmeden SONRA gosterilen topmost 'oyun' ve Tool+topmost 'secim katmani' -> sekme nerede; _ac() raise_()
  S7 Ikinci monitor (dpr != 1): fiziksel kenar, +1 px sutunu kime gider (WindowFromPoint), panel monitor icinde, goruntu
  S8 Tepsi balonu: `bildir(ms=1000)` gercek sure (Windows.UI.Core.CoreWindow gorunurlugu)
  S9 Tepsi ikonu gorunur tepside mi, tasma (overflow) menusunde mi -- ilk kullanim ipucu sorusu
Cikis kodu: 0 (olcum gecerli), 2 (fare oynadi: olcum gecersiz -> sarici tekrar dener).
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
from PySide6 import QtCore, QtGui, QtWidgets  # noqa: E402

CIKTI = KOK / ".agents" / "tasks" / "T-012" / "tester_B_evidence"
u32 = ctypes.windll.user32
k32 = ctypes.windll.kernel32
sh = ctypes.windll.shell32
u32.GetForegroundWindow.restype = wintypes.HWND
u32.WindowFromPoint.restype = wintypes.HWND
u32.WindowFromPoint.argtypes = [wintypes.POINT]
u32.GetWindow.restype = wintypes.HWND
u32.GetWindowLongW.restype = ctypes.c_long
u32.FindWindowW.restype = wintypes.HWND
u32.FindWindowExW.restype = wintypes.HWND
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


def imlec() -> tuple[int, int]:
    pt = wintypes.POINT(); u32.GetCursorPos(ctypes.byref(pt)); return (pt.x, pt.y)


def sinif(h: int) -> str:
    buf = ctypes.create_unicode_buffer(256); u32.GetClassNameW(h, buf, 256); return buf.value


def on_plan() -> int:
    return int(u32.GetForegroundWindow() or 0)


def gercek_tik(p: QtCore.QPoint, sag: bool = False) -> None:
    QtGui.QCursor.setPos(p); bekle(80)
    asagi, yukari = (0x0008, 0x0010) if sag else (0x0002, 0x0004)
    u32.mouse_event(asagi, 0, 0, 0, 0); bekle(30); u32.mouse_event(yukari, 0, 0, 0, 0); bekle(300)


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


def alt_tab_adaylari() -> list[str]:
    """Gorunur, sahipsiz, TOOLWINDOW olmayan ust-duzey pencereler (Alt-Tab / gorev cubugu kurali)."""
    ad: list[str] = []
    for h in surec_pencereleri(sadece_gorunur=True):
        ex = u32.GetWindowLongW(h, GWL_EXSTYLE) & 0xFFFFFFFF
        if not u32.GetWindow(h, GW_OWNER) and not (ex & WS_EX_TOOLWINDOW):
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


def z_indeks(hwnds: dict[str, int]) -> dict[str, int]:
    sira = tum_pencereler_gorunur()
    return {ad: (sira.index(h) if h in sira else -1) for ad, h in hwnds.items()}


def main() -> int:  # noqa: C901
    from src.ui.geometri import Kenar
    from src.ui.kabuk import AnaPencere, KabukDurumu

    app = QtWidgets.QApplication(sys.argv); app.setQuitOnLastWindowClosed(False)
    CIKTI.mkdir(exist_ok=True)
    ekran = QtGui.QGuiApplication.primaryScreen(); g = ekran.availableGeometry()
    print(f"sonda_1: birincil {g.width()}x{g.height()} dpr={ekran.devicePixelRatio()} tepsi={QtWidgets.QSystemTrayIcon.isSystemTrayAvailable()} on_plan_bizim={on_plan() in surec_pencereleri()}")

    sahne = QtWidgets.QLabel("temsili oyun penceresi (Tester-B sonda)")
    sahne.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
    sahne.setStyleSheet("background:#12203a; color:#5a7aa8; font:16px 'Segoe UI'; padding:20px;")
    sahne.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignLeft)
    sahne.setGeometry(g.right() - 700, g.y() + 200, 701, 900); sahne.show(); bekle(200)
    sahne_hwnd = int(sahne.winId())

    # ---------------- S1 / S2 -------------------------------------------------------------
    print("S1/S2 Alt-Tab adaylari ve tepsi ikonu (bagimsiz kanal)")
    p = AnaPencere(ekran); cikis: list[int] = []; p.cikis_istendi.connect(lambda: cikis.append(1))
    p.move(g.x() + 200, g.y() + 200); p.show(); bekle(300)
    p_hwnd = int(p.winId())
    (ok if ikon_rect() is None else bulgu)(f"[S2a] taze gorunur: tepsi ikonu Shell'de yok={ikon_rect() is None}")
    (ok if alt_tab_adaylari() == ["Qt6112QWindowIcon"] or len(alt_tab_adaylari()) == 1 else bulgu)(f"[S1a] gorunur: Alt-Tab adaylari={alt_tab_adaylari()} (1 beklenir)")
    p.tepsiye_al(); bekle(400)
    r_ikon = ikon_rect()
    (ok if r_ikon is not None else bulgu)(f"[S2b] tepsi: ikon Shell'de var={r_ikon is not None} rect={r_ikon}")
    (ok if alt_tab_adaylari() == [] else bulgu)(f"[S1b] tepsi: Alt-Tab adaylari={alt_tab_adaylari()} (0 beklenir)")
    # S9 tasma
    tray = u32.FindWindowW("Shell_TrayWnd", None); notify = u32.FindWindowExW(tray, None, "TrayNotifyWnd", None) if tray else 0
    tasma = u32.FindWindowW("NotifyIconOverflowWindow", None)
    tasma_gorunur = bool(tasma and u32.IsWindowVisible(tasma))
    notify_r = win_rect(notify) if notify else None
    icinde = notify_r is not None and r_ikon is not None and notify_r[0] <= (r_ikon[0] + r_ikon[2]) // 2 <= notify_r[2]
    altinda = None
    if r_ikon is not None:
        cx, cy = (r_ikon[0] + r_ikon[2]) // 2, (r_ikon[1] + r_ikon[3]) // 2
        altinda = sinif(int(u32.WindowFromPoint(wintypes.POINT(cx, cy)) or 0))
    print(f"  bilgi  [S9] ikon rect={r_ikon} TrayNotifyWnd={notify_r} ikon TrayNotify icinde={icinde} tasma penceresi gorunur={tasma_gorunur} rect merkezindeki pencere sinifi={altinda!r}")
    # ---------------- S3 tepsi ikonuna gercek tik -------------------------------------------
    print("S3 tepsi ikonuna gercek tik")
    if r_ikon is not None:
        cx, cy = (r_ikon[0] + r_ikon[2]) // 2, (r_ikon[1] + r_ikon[3]) // 2
        # rect fiziksel px; birincil dpr 1.0 -> mantiksal ayni
        gercek_tik(QtCore.QPoint(cx, cy)); bekle(500)
        (ok if uclu(p) == (True, False, False) and p.durum == KabukDurumu.GORUNUR else bulgu)(f"[S3a] tepsi ikonuna sol tik: uclu={uclu(p)} durum={p.durum} (T,F,F gorunur beklenir)")
        (ok if on_plan() == p_hwnd else bulgu)(f"[S3b] tik sonrasi on plan ana pencere={on_plan() == p_hwnd} (on plan sinifi={sinif(on_plan())!r})")
        if not p.isVisible():
            p.goster(); bekle(300)
    else:
        bulgu("[S3] ikon rect yok, tik olculemedi")
    (ok if ikon_rect() is None else bulgu)(f"[S2c] goster sonrasi ikon Shell'de yok={ikon_rect() is None}")
    # ---------------- S4 kenara al + sag tik ----------------------------------------------
    print("S4 kenar: Alt-Tab, ikon, sag tik on plan")
    sahne.raise_(); sahne.activateWindow(); bekle(300)
    p.kenara_al(); bekle(400)
    s = p.sekme; s_hwnd = int(s.winId()); ex = u32.GetWindowLongW(s_hwnd, GWL_EXSTYLE) & 0xFFFFFFFF
    (ok if alt_tab_adaylari() == [] else bulgu)(f"[S1c] kenar: Alt-Tab adaylari={alt_tab_adaylari()} (0 beklenir); sekme exstyle TOOLWINDOW={bool(ex & WS_EX_TOOLWINDOW)} TOPMOST={bool(ex & WS_EX_TOPMOST)} NOACTIVATE={bool(ex & WS_EX_NOACTIVATE)}")
    (ok if ikon_rect() is not None else bulgu)(f"[S2d] kenar: ikon Shell'de var={ikon_rect() is not None}")
    (ok if on_plan() == sahne_hwnd else bulgu)(f"[S4a] kenara al sonrasi on plan sahne={on_plan() == sahne_hwnd}")
    fg = s.frameGeometry()
    gercek_tik(QtCore.QPoint(fg.right() - 4, fg.center().y()), sag=True); bekle(400)
    (ok if uclu(p) == (True, False, False) else bulgu)(f"[S4b] sekmeye gercek sag tik: uclu={uclu(p)} (T,F,F)")
    (ok if on_plan() == p_hwnd else bulgu)(f"[S4c] sag tik sonrasi on plan ana pencere={on_plan() == p_hwnd} (sinif={sinif(on_plan())!r})")
    QtGui.QCursor.setPos(QtCore.QPoint(g.x() + 100, g.y() + 100)); bekle(300)
    # ---------------- S5 WM_CLOSE uc durumda ------------------------------------------------
    print("S5 WM_CLOSE uc durumda")
    p.kapat(); bekle(300)
    (ok if ikon_rect() is None and cikis == [1] else bulgu)(f"[S2e] kapat: ikon Shell'de yok={ikon_rect() is None} cikis={len(cikis)}")
    for durum_adi in ("gorunur", "tepsi", "kenar"):
        q = AnaPencere(ekran); qc: list[int] = []; q.cikis_istendi.connect(lambda: qc.append(1))
        q.move(g.x() + 200, g.y() + 200); q.show(); bekle(300)
        {"gorunur": lambda: None, "tepsi": q.tepsiye_al, "kenar": q.kenara_al}[durum_adi](); bekle(300)
        before = (uclu(q), q.durum)
        u32.PostMessageW(wintypes.HWND(int(q.winId())), WM_CLOSE, 0, 0); bekle(600)
        gorunur = [w for w in QtWidgets.QApplication.topLevelWidgets() if w.isVisible() and w is not sahne]
        (ok if qc == [1] and uclu(q) == (False, False, False) and ikon_rect() is None and not gorunur else bulgu)(
            f"[S5 {durum_adi}] once={before} -> WM_CLOSE: cikis={len(qc)} uclu={uclu(q)} ikon yok={ikon_rect() is None} gorunur ust-duzey={len(gorunur)} yokluyor={q.sekme.yokluyor}")
        q.kapat(); bekle(100)
    # ---------------- S6 z-sirasi ------------------------------------------------------------
    print("S6 z-sirasi: sekmeden sonra gosterilen topmost oyun / Tool+topmost secim katmani")
    p = AnaPencere(ekran); p.move(g.x() + 200, g.y() + 200); p.show(); bekle(300)
    p.kenara_al(); bekle(300); s = p.sekme; s_hwnd = int(s.winId()); fg = s.frameGeometry()
    oyun = QtWidgets.QLabel("temsili TOPMOST oyun (sekmeden sonra gosterildi)")
    oyun.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.WindowStaysOnTopHint)
    oyun.setStyleSheet("background:#2a1a3a; color:#9a7ac8; font:16px 'Segoe UI'; padding:20px;")
    oyun.setGeometry(g.right() - 500, fg.y() - 200, 501, 500); oyun.show(); bekle(400)
    oyun_hwnd = int(oyun.winId())
    z1 = z_indeks({"sekme": s_hwnd, "oyun": oyun_hwnd})
    altinda = int(u32.WindowFromPoint(wintypes.POINT(fg.right() - 4, fg.center().y())) or 0)
    print(f"  bilgi  [S6a] topmost oyun sekmeden sonra: z (kucuk=ustte) {z1}; sekme merkezindeki pencere={'sekme' if altinda == s_hwnd else ('oyun' if altinda == oyun_hwnd else sinif(altinda))} (belgeli sinir: oyun ustte)")
    QtGui.QCursor.setPos(QtCore.QPoint(fg.right() - 4, fg.center().y()))
    t0 = time.perf_counter()
    while not s.acik and time.perf_counter() - t0 < 2: bekle(5)
    bekle(150)
    z2 = z_indeks({"sekme": s_hwnd, "oyun": oyun_hwnd})
    print(f"  bilgi  [S6b] imlec sekmede: acik={s.acik} ({(time.perf_counter() - t0) * 1000:.0f} ms) -> z {z2}; _ac() raise_() sekmeyi ustune aldi mi={z2['sekme'] < z2['oyun'] if s.acik else None}")
    if not s.acik:
        bulgu("[S6b] topmost oyun altinda kalan sekme: imlec uzerine gelince ACILMADI (WindowFromPoint oyun -> yoklayici yine de acmali; acilmadiysa neden?)")
    QtGui.QCursor.setPos(QtCore.QPoint(g.x() + 100, g.y() + 100)); bekle(700)
    oyun.hide(); bekle(200)
    # secim katmani benzeri: Tool + StaysOnTop + translucent, tum ekran
    katman = QtWidgets.QWidget()
    katman.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.WindowStaysOnTopHint | QtCore.Qt.WindowType.Tool)
    katman.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
    katman.setStyleSheet("background: rgba(0,0,0,110);")
    katman.setGeometry(g); katman.show(); katman.activateWindow(); bekle(400)
    katman_hwnd = int(katman.winId())
    z3 = z_indeks({"sekme": s_hwnd, "katman": katman_hwnd})
    QtGui.QCursor.setPos(QtCore.QPoint(fg.right() - 4, fg.center().y()))
    t0 = time.perf_counter()
    while not s.acik and time.perf_counter() - t0 < 2: bekle(5)
    bekle(150)
    z4 = z_indeks({"sekme": s_hwnd, "katman": katman_hwnd})
    print(f"  bilgi  [S6c] demo SecimKatmani benzeri (Tool+topmost, tum ekran) sekmeden sonra: z {z3}; imlec sekmede acik={s.acik} -> z {z4}; panel katmanin USTUNE cikti={z4['sekme'] < z4['katman'] if s.acik else None}")
    if s.acik and z4["sekme"] < z4["katman"]:
        bulgu("[S6c] bolge secimi sirasinda (katman acik) imlec sekme diskine girerse panel KATMANIN USTUNE cikar (_ac raise_) -- demo entegrasyonu: secim sirasinda sekme gizlenmeli/yoklayici durmali")
    QtGui.QCursor.setPos(QtCore.QPoint(g.x() + 100, g.y() + 100)); bekle(700)
    katman.hide(); bekle(100)
    p.kapat(); bekle(200)
    # ---------------- S7 ikinci monitor ---------------------------------------------------
    print("S7 ikinci monitor (dpr != 1)")
    ekranlar = QtGui.QGuiApplication.screens()
    digerleri = [e for e in ekranlar if e is not ekran]
    if digerleri:
        e2 = sorted(digerleri, key=lambda e: -abs(e.devicePixelRatio() - 1.0))[0]
        g2 = e2.availableGeometry()
        sahne2 = QtWidgets.QLabel("temsili oyun penceresi -- ikinci monitor (Tester-B sonda)")
        sahne2.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
        sahne2.setStyleSheet("background:#1a2a1a; color:#6a9a6a; font:16px 'Segoe UI'; padding:20px;")
        sahne2.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignLeft)
        sahne2.setGeometry(g2); sahne2.show(); bekle(300)
        p2 = AnaPencere(e2); p2.move(g2.x() + 100, g2.y() + 100); p2.show(); bekle(300)
        p2.kenara_al(); bekle(400)
        s2 = p2.sekme; h2 = int(s2.winId()); fg2 = s2.frameGeometry()
        r = win_rect(h2)
        mi = MONITORINFO(); mi.cbSize = ctypes.sizeof(MONITORINFO); u32.GetMonitorInfoW(u32.MonitorFromWindow(wintypes.HWND(h2), 2), ctypes.byref(mi))
        fark = r[2] - mi.rcWork.right
        print(f"  bilgi  [S7a] e2 dpr={e2.devicePixelRatio()} mantiksal avail={g2.x()},{g2.y()},{g2.width()},{g2.height()} sekme mantiksal=({fg2.x()},{fg2.y()},{fg2.width()},{fg2.height()}) fiziksel={r} monitor calisma sag={mi.rcWork.right} fark={fark:+d}")
        (ok if fg2.right() == g2.right() and g2.contains(fg2) else bulgu)(f"[S7b] mantiksal: sag kenara bitisik={fg2.right() == g2.right()} ekran icinde={g2.contains(fg2)}")
        # +1 px sutunu kime gider? fiziksel (r.right-1, orta) ve (r.right, orta)
        oy = (r[1] + r[3]) // 2
        w_ic = int(u32.WindowFromPoint(wintypes.POINT(r[2] - 1, oy)) or 0)
        w_dis = int(u32.WindowFromPoint(wintypes.POINT(r[2], oy)) or 0)
        w_tasma = int(u32.WindowFromPoint(wintypes.POINT(mi.rcWork.right, oy)) or 0) if fark > 0 else 0
        adla = lambda h: "sekme" if h == h2 else ("sahne2" if h == int(sahne2.winId()) else ("sahne" if h == sahne_hwnd else sinif(h)))  # noqa: E731
        print(f"  bilgi  [S7c] WindowFromPoint fiziksel: son sutun (x={r[2] - 1})={adla(w_ic)}; bir otesi (x={r[2]})={adla(w_dis)}; monitorun otesi (x={mi.rcWork.right})={adla(w_tasma) if w_tasma else '-'}")
        if fark > 0 and w_tasma == h2:
            bulgu(f"[S7c] sekme {fark} fiziksel px komsu monitore tasiyor: o sutundaki tik SEKMEYE gider (oyuna degil)")
        # hover ac
        QtGui.QCursor.setPos(QtCore.QPoint(fg2.right() - 4, fg2.center().y()))
        t0 = time.perf_counter()
        while not s2.acik and time.perf_counter() - t0 < 2: bekle(5)
        bekle(200)
        fg3 = s2.frameGeometry(); r3 = win_rect(h2)
        (ok if s2.acik and g2.contains(fg3) and fg3.right() == g2.right() else bulgu)(f"[S7d] panel acildi={s2.acik} ({(time.perf_counter() - t0) * 1000:.0f} ms) mantiksal=({fg3.x()},{fg3.y()},{fg3.width()},{fg3.height()}) ekran icinde={g2.contains(fg3)} fiziksel={r3} monitor sag={mi.rcMonitor.right}")
        e2.grabWindow(0, fg3.x() - 40, fg3.y() - 40, fg3.width() + 80, fg3.height() + 80).save(str(CIKTI / "sonda1-s7-ikinci-monitor-panel-acik.png"))
        QtGui.QCursor.setPos(QtCore.QPoint(g2.x() + 100, g2.y() + 100)); bekle(800)
        fg4 = s2.frameGeometry()
        e2.grabWindow(0, fg4.x() - 120, fg4.y() - 60, fg4.width() + 160, fg4.height() + 120).save(str(CIKTI / "sonda1-s7-ikinci-monitor-sekme-kapali.png"))
        # sol kenar ayni monitorde
        s2.kenar = Kenar.SOL; bekle(200); fg5 = s2.frameGeometry(); r5 = win_rect(h2)
        print(f"  bilgi  [S7e] kenar=SOL: mantiksal=({fg5.x()},{fg5.y()},{fg5.width()},{fg5.height()}) fiziksel={r5} monitor calisma sol={mi.rcWork.left} fark={r5[0] - mi.rcWork.left:+d}")
        (ok if fg5.left() == g2.left() else bulgu)(f"[S7e] sol kenara bitisik={fg5.left() == g2.left()}")
        e2.grabWindow(0, fg5.x() - 40, fg5.y() - 60, fg5.width() + 160, fg5.height() + 120).save(str(CIKTI / "sonda1-s7-ikinci-monitor-sol-kenar.png"))
        p2.kapat(); bekle(200); sahne2.close()
    else:
        print("  bilgi  [S7] ikinci monitor yok -- atlandi")
    # ---------------- S8 balon suresi -----------------------------------------------------
    print("S8 tepsi balonu suresi (bildir ms=1000)")
    p = AnaPencere(ekran); p.move(g.x() + 200, g.y() + 200); p.show(); bekle(300)
    p.tepsiye_al(); bekle(400)

    def toast_var() -> bool:
        for h in tum_pencereler_gorunur():
            if sinif(h) == "Windows.UI.Core.CoreWindow":
                rr = win_rect(h)
                if rr[2] - rr[0] < 700 and rr[3] - rr[1] < 400 and rr[2] > g.right() - 600 and rr[3] > g.bottom() - 500:
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
    print(f"  bilgi  [S8] oncesinde toast var={onceden}; gorundu={ilk is not None} ({(ilk or 0) * 1000:.0f} ms) kayboldu={son is not None} ({(son or 0) * 1000:.0f} ms) -> gorunur sure ~{((son or 0) - (ilk or 0)) * 1000:.0f} ms (istenen 1000)")
    p.kapat(); bekle(300)
    sahne.close()
    print()
    print(f"SONDA_1: {len(bulgular)} bulgu")
    for b in bulgular: print(f"  - {b}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
