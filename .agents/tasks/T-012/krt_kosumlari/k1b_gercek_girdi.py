"""KRT-1 / madde 1+4+6 (devam) -- demo/kabuk.py prototipi, GERCEK OS girdisiyle (kilit tespiti duzeltildi).

    python .agents/tasks/T-012/krt_kosumlari/k1b_gercek_girdi.py

k1_prototip_surus.py'nin `oturum_kilitli()` fonksiyonu WTSINFOEXW yerlesimini yanlis okuyordu (`Data` 8 hizali,
betik 4'te okudu -> `SessionState=WTSActive(0)` "kilit" sanildi) ve gercek girdi hic kosmadi. Burada kilit tespiti
`OpenInputDesktop` adiyla yapilir ("Default" = acik, "Winlogon" = kilitli).

  P0 kilit tespiti (iki yontem yan yana)
  P8 hit-test: kapali sekmenin saydam kosesi (alpha 0) ve dolu merkezi -> WindowFromPoint bizim mi; yabanci ise sinif adi
  P1 GERCEK OS surukleme (mouse_event) +150 px -> y degisti mi; surukleme sirasinda panel acildi mi
  P9 QTest.mousePress / mouseMove windows platformunda GERCEK imleci oynatiyor mu (real_check [5a] yan etkisi)
  P5 GERCEK sol tik panel dugmesine -> sinyal; GetForegroundWindow degisti mi (NoFocus etkisi)
  P4 GERCEK sag tik -> pencere gorunur mu; ana pencere ON PLANA geldi mi (foreground kilidi)
  P10 WM_CLOSE (Alt+F4 esdegeri) gorunur durumda -> ne kalir (closeEvent yok: zombi mi)
Ekran goruntusu alinmaz. Stdout ASCII. Ham cikti: k1b_gercek_girdi.txt
"""
from __future__ import annotations

import ctypes
import sys
import time
from ctypes import wintypes
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(KOK))

from PySide6 import QtCore, QtGui, QtWidgets  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402

from demo.kabuk import KAPANMA_MS, YARICAP, AnaPencere  # noqa: E402
from src.capture.service import CaptureService, MssBackend  # noqa: E402

CIKTI = Path(__file__).resolve().parent / "k1b_gercek_girdi.txt"
satirlar: list[str] = []
u32 = ctypes.windll.user32
k32 = ctypes.windll.kernel32
u32.WindowFromPoint.restype = wintypes.HWND
u32.WindowFromPoint.argtypes = [wintypes.POINT]
u32.GetForegroundWindow.restype = wintypes.HWND
MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP = 0x0002, 0x0004
MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP = 0x0008, 0x0010
WM_CLOSE = 0x0010


def olgu(m: str) -> None:
    satirlar.append(m); print(" ", m.encode("ascii", "replace").decode("ascii"))


def giris_masaustu() -> str:
    h = u32.OpenInputDesktop(0, False, 0x0001)
    if not h:
        return f"ACILAMADI(err={k32.GetLastError()})"
    buf = ctypes.create_unicode_buffer(256); n = wintypes.DWORD()
    u32.GetUserObjectInformationW(h, 2, buf, 512, ctypes.byref(n)); u32.CloseDesktop(h)
    return buf.value


def eski_kilit_tespiti() -> int:
    """k1_prototip_surus.py'deki (hatali yerlesimli) okuma -- karsilastirma icin."""
    class L1(ctypes.Structure):
        _fields_ = [("SessionId", wintypes.DWORD), ("State", ctypes.c_int), ("SessionFlags", wintypes.LONG), ("pad", ctypes.c_byte * 400)]

    class EX(ctypes.Structure):
        _fields_ = [("Level", wintypes.DWORD), ("Data", L1)]
    buf = ctypes.c_void_p(); n = wintypes.DWORD()
    if not ctypes.windll.wtsapi32.WTSQuerySessionInformationW(None, 0xFFFFFFFF, 25, ctypes.byref(buf), ctypes.byref(n)):
        return -1
    return int(ctypes.cast(buf, ctypes.POINTER(EX)).contents.Data.SessionFlags)


def bekle(ms: int) -> None:
    son = time.perf_counter() + ms / 1000
    while time.perf_counter() < son:
        QtWidgets.QApplication.processEvents()
        time.sleep(0.004)


def fiziksel(p: QtCore.QPoint) -> tuple[int, int]:
    e = QtGui.QGuiApplication.screenAt(p) or QtGui.QGuiApplication.primaryScreen()
    dpr = e.devicePixelRatio(); g = e.geometry()
    return int(g.x() + (p.x() - g.x()) * dpr), int(g.y() + (p.y() - g.y()) * dpr)


def hwnd_altinda(p: QtCore.QPoint) -> int:
    x, y = fiziksel(p)
    return int(u32.WindowFromPoint(wintypes.POINT(x, y)) or 0)


def pid_of(hwnd: int) -> int:
    pid = wintypes.DWORD(0)
    u32.GetWindowThreadProcessId(wintypes.HWND(hwnd), ctypes.byref(pid))
    return int(pid.value)


def sinif_adi(hwnd: int) -> str:
    buf = ctypes.create_unicode_buffer(128)
    u32.GetClassNameW(wintypes.HWND(hwnd), buf, 128)
    return buf.value


def bizim_mi(p: QtCore.QPoint) -> bool:
    return pid_of(hwnd_altinda(p)) == k32.GetCurrentProcessId()


def on_plan() -> str:
    h = int(u32.GetForegroundWindow() or 0)
    if pid_of(h) == k32.GetCurrentProcessId():
        w = QtWidgets.QWidget.find(h)
        return f"BIZIM:{type(w).__name__ if w else 'hwnd'}"
    return "baska-surec"


def gercek_tik(p: QtCore.QPoint, sag: bool = False) -> bool:
    QtGui.QCursor.setPos(p); bekle(60)
    if not bizim_mi(p):
        olgu(f"    (gercek tik ATLANDI: imlec altindaki pencere bizim degil @ {p.x()},{p.y()} sinif={sinif_adi(hwnd_altinda(p))!r})")
        return False
    if sag:
        u32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0); bekle(30); u32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
    else:
        u32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0); bekle(30); u32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    bekle(200)
    return True


def main() -> int:
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    md = giris_masaustu()
    olgu(f"P0 giris masaustu={md!r} (Default=acik) | eski betigin okudugu SessionFlags={eski_kilit_tespiti()} (0 -> 'kilitli' saymisti)")
    kilitli = md != "Default"
    ekran = QtGui.QGuiApplication.primaryScreen(); g = ekran.availableGeometry()
    olgu(f"ekran avail=({g.x()},{g.y()},{g.width()},{g.height()}) dpr={ekran.devicePixelRatio()} ekranlar={len(QtGui.QGuiApplication.screens())}")
    sahne = QtWidgets.QLabel("temsili oyun")
    sahne.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)          # normal pencere: odak alabilsin
    sahne.setStyleSheet("background:#1b2a41; color:#3d5a80; font: 16px 'Segoe UI';")
    sahne.setGeometry(g.right() - 640, g.y() + 300, 641, 800); sahne.show(); bekle(200)
    p = AnaPencere(CaptureService(MssBackend()))
    p.move(g.x() + 200, g.y() + 200); p.show(); bekle(400)
    s = p._sekme
    imlec0 = QtGui.QCursor.pos()
    olgu(f"on-plan (ana pencere gosterildi): {on_plan()}")

    # kenara al
    QTest.mouseClick(p._b_kenar, QtCore.Qt.MouseButton.LeftButton); bekle(300)
    fg = s.frameGeometry()
    olgu(f"kenara al: sekme=({fg.x()},{fg.y()},{fg.width()},{fg.height()}) on-plan={on_plan()} tepsi={p._tepsi.isVisible()}")
    # sahneyi on plana al (oyun odakta gibi)
    sahne.raise_(); sahne.activateWindow(); bekle(300)
    olgu(f"sahne activateWindow(): on-plan={on_plan()} (BIZIM:QLabel beklenir; degilse foreground kilidi)")

    # P8 hit-test
    dis = QtCore.QPoint(fg.x() - 300, fg.center().y())
    kose = QtCore.QPoint(fg.x() + 1, fg.y() + 1); merkez = QtCore.QPoint(fg.x() + YARICAP - 4, fg.y() + YARICAP)
    QtGui.QCursor.setPos(kose); bekle(80)
    hk = hwnd_altinda(kose)
    olgu(f"P8 kose(alpha0): bizim={bizim_mi(kose)} hwnd={hk:#x} sinif={sinif_adi(hk)!r} | sekme_hwnd={int(s.winId()):#x} sahne_hwnd={int(sahne.winId()):#x}")
    olgu(f"P8 kose imlecteyken yoklayici 'icinde' sayar mi: frameGeometry.contains={s.frameGeometry().contains(QtGui.QCursor.pos())} acilma_timer={s._acilma.isActive()}")
    QtGui.QCursor.setPos(merkez); bekle(80)
    hm = hwnd_altinda(merkez)
    olgu(f"P8 merkez(alpha235): bizim={bizim_mi(merkez)} hwnd={hm:#x} sinif={sinif_adi(hm)!r} (sekme beklenir)")
    QtGui.QCursor.setPos(dis); bekle(KAPANMA_MS + 300)

    # P1 gercek OS surukleme
    fg = s.frameGeometry(); merkez = QtCore.QPoint(fg.x() + YARICAP - 4, fg.y() + YARICAP)
    QtGui.QCursor.setPos(merkez); bekle(60)
    if bizim_mi(merkez) and not kilitli:
        y1 = s._y; acik_gorulen = False
        u32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0); bekle(40)
        for i in range(1, 6):
            QtGui.QCursor.setPos(merkez.x(), merkez.y() + 30 * i); bekle(60); acik_gorulen |= s._acik
        u32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0); bekle(150)
        olgu(f"P1 gercek OS surukleme +150: y {y1} -> {s._y} (beklenen {y1 + 150}) surukleme sirasinda acik gorundu={acik_gorulen} on-plan={on_plan()}")
        bekle(200)
        olgu(f"P1 surukleme bittikten 200 ms sonra (imlec hala sekmede): acik={s._acik} acilma_timer={s._acilma.isActive()}")
        QtGui.QCursor.setPos(s.frameGeometry().x() - 300, s.frameGeometry().center().y()); bekle(KAPANMA_MS + 300)
        olgu(f"P1 sonrasi: acik={s._acik}")
    else:
        olgu(f"P1 gercek surukleme ATLANDI: bizim={bizim_mi(merkez)} kilitli={kilitli}")

    # P9 QTest.mousePress/mouseMove gercek imleci oynatiyor mu
    fg = s.frameGeometry()
    QtGui.QCursor.setPos(fg.x() - 300, fg.center().y()); bekle(100)
    c0 = QtGui.QCursor.pos()
    QTest.mousePress(s, QtCore.Qt.MouseButton.LeftButton, pos=QtCore.QPoint(YARICAP // 2, YARICAP)); bekle(30)
    c1 = QtGui.QCursor.pos()
    QTest.mouseMove(s, QtCore.QPoint(YARICAP // 2, YARICAP + 5000)); bekle(30)
    c2 = QtGui.QCursor.pos()
    QTest.mouseRelease(s, QtCore.Qt.MouseButton.LeftButton, pos=QtCore.QPoint(YARICAP // 2, YARICAP)); bekle(100)
    c3 = QtGui.QCursor.pos()
    olgu(f"P9 QTest: imlec once=({c0.x()},{c0.y()}) press sonrasi=({c1.x()},{c1.y()}) mouseMove(+5000) sonrasi=({c2.x()},{c2.y()}) release sonrasi=({c3.x()},{c3.y()}) | sekme y={s._y} alt sinir={g.bottom() - 2 * YARICAP + 1} acik={s._acik}")
    olgu(f"P9 mouseMove sonrasi gercek imlec sekmenin icinde mi: {s.frameGeometry().contains(c2)} (ekran geometry.bottom={ekran.geometry().bottom()} avail.bottom={g.bottom()})")
    QtGui.QCursor.setPos(s.frameGeometry().x() - 300, s.frameGeometry().center().y()); bekle(KAPANMA_MS + 300)

    # P5 gercek sol tik panel dugmesine
    fg = s.frameGeometry(); ic = QtCore.QPoint(fg.x() + YARICAP - 4, fg.y() + YARICAP)
    QtGui.QCursor.setPos(ic); t0 = time.perf_counter()
    while not s._acik and time.perf_counter() - t0 < 2: bekle(5)
    olgu(f"P5 acildi={s._acik} {1000*(time.perf_counter()-t0):.0f} ms")
    dugmeler = s._panel.findChildren(QtWidgets.QPushButton)
    alindi: list[int] = []
    s.anlik_cevir.connect(lambda: alindi.append(1))
    b1 = dugmeler[0]; hedef = b1.mapToGlobal(b1.rect().center())
    onp = on_plan()
    tik = gercek_tik(hedef)
    olgu(f"P5 gercek sol tik panel dugmesi: basildi={tik} sinyal={len(alindi)} on-plan once={onp} sonra={on_plan()} acik={s._acik} (on-plan degismemeli: NoFocus)")
    QtGui.QCursor.setPos(fg.x() - 300, fg.center().y()); bekle(KAPANMA_MS + 300)

    # P4 gercek sag tik -> pencere gelir mi, on plana mi
    fg = s.frameGeometry(); merkez = QtCore.QPoint(fg.x() + YARICAP - 4, fg.y() + YARICAP)
    onp = on_plan()
    tik = gercek_tik(merkez, sag=True)
    bekle(400)
    olgu(f"P4 gercek sag tik: basildi={tik} pencere gorunur={p.isVisible()} sekme gorunur={s.isVisible()} on-plan once={onp} sonra={on_plan()} (BIZIM:AnaPencere beklenir)")
    QtGui.QCursor.setPos(imlec0)

    # P10 WM_CLOSE gorunur durumda (Alt+F4 / gorev cubugu 'pencereyi kapat' esdegeri)
    if not p.isVisible():
        p.goster(); bekle(200)
    u32.PostMessageW(wintypes.HWND(int(p.winId())), WM_CLOSE, 0, 0); bekle(300)
    gorunur = [type(w).__name__ for w in QtWidgets.QApplication.topLevelWidgets() if w.isVisible() and w is not sahne]
    olgu(f"P10 WM_CLOSE gorunur durumda: pencere gorunur={p.isVisible()} gorunur ust-duzey={gorunur} tepsi={p._tepsi.isVisible()} sekme={s.isVisible()} yoklayici={s._yoklayici.isActive()} -> ulasilabilir yol var mi={p._tepsi.isVisible() or s.isVisible()}")

    p._tepsi.hide(); s.close(); sahne.close()
    CIKTI.write_text("KRT-1 madde 1/4/6 (devam) -- gercek OS girdisi, kilit tespiti duzeltildi\n\n" + "\n".join(satirlar) + "\n", encoding="utf-8")
    print("yazildi: k1b_gercek_girdi.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
