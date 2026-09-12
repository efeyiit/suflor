"""KRT-1 / madde 1 -- demo/kabuk.py prototipini GERCEK ekranda surer ve kirmaya calisir.

    python .agents/tasks/T-012/krt_kosumlari/k1_prototip_surus.py

Olculenler (stdout ASCII, ham cikti k1_prototip_surus.txt):
  P1 kenara al -> geometri; QTest surukleme (sentetik) ve GERCEK OS girdisiyle surukleme (mouse_event)
  P2 hizli iceri-disari (50 ms periyot, 10 kez) -> panel acildi mi / titredi mi
  P3 acikken iceri-disari-iceri (100 ms disari) -> acik kalir mi
  P4 gercek OS sag tik -> pencere gelir mi; GetForegroundWindow sekme oldu mu (odak calinmasi)
  P5 gercek OS sol tik panel dugmesine -> odak; dugme sinyali
  P6 tepsi menusu eylem adlari; tepsi ikonu gorunurlugu her durumda
  P7 gorunur durumda close() (Alt+F4 esdegeri) -> ne kalir (zombi sureci)
  P8 saydam kose hit-test: WindowFromPoint kose vs merkez
Ekran goruntusu alinmaz (masaustu depoya girmesin).
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

CIKTI = Path(__file__).resolve().parent / "k1_prototip_surus.txt"
satirlar: list[str] = []
u32 = ctypes.windll.user32
u32.WindowFromPoint.restype = wintypes.HWND
u32.WindowFromPoint.argtypes = [wintypes.POINT]
u32.GetForegroundWindow.restype = wintypes.HWND
KILITLI = False
MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP = 0x0002, 0x0004
MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP = 0x0008, 0x0010


def olgu(m: str) -> None:
    satirlar.append(m); print(" ", m.encode("ascii", "replace").decode("ascii"))


def oturum_kilitli() -> bool:
    """WTSQuerySessionInformation(WTSSessionInfoEx): SessionFlags 0 = WTS_SESSIONSTATE_LOCK."""
    class L1(ctypes.Structure):
        _fields_ = [("SessionId", wintypes.DWORD), ("State", ctypes.c_int), ("SessionFlags", wintypes.LONG), ("pad", ctypes.c_byte * 400)]

    class EX(ctypes.Structure):
        _fields_ = [("Level", wintypes.DWORD), ("Data", L1)]
    buf = ctypes.c_void_p(); n = wintypes.DWORD()
    if not ctypes.windll.wtsapi32.WTSQuerySessionInformationW(None, 0xFFFFFFFF, 25, ctypes.byref(buf), ctypes.byref(n)):
        return False
    return ctypes.cast(buf, ctypes.POINTER(EX)).contents.Data.SessionFlags == 0


def bekle(ms: int) -> None:
    son = time.perf_counter() + ms / 1000
    while time.perf_counter() < son:
        QtWidgets.QApplication.processEvents()
        time.sleep(0.004)


def fiziksel(p: QtCore.QPoint) -> tuple[int, int]:
    """Mantiksal -> fiziksel (birincil ekran dpr=1 oldugu icin ayni; genel olsun diye)."""
    e = QtGui.QGuiApplication.screenAt(p) or QtGui.QGuiApplication.primaryScreen()
    dpr = e.devicePixelRatio(); g = e.geometry()
    return int(g.x() * 1 + (p.x() - g.x()) * dpr), int(g.y() + (p.y() - g.y()) * dpr)


def hwnd_altinda(p: QtCore.QPoint) -> int:
    x, y = fiziksel(p)
    return int(u32.WindowFromPoint(wintypes.POINT(x, y)))


def pid_of(hwnd: int) -> int:
    pid = wintypes.DWORD(0)
    u32.GetWindowThreadProcessId(wintypes.HWND(hwnd), ctypes.byref(pid))
    return int(pid.value)


def bizim_mi(p: QtCore.QPoint) -> bool:
    return pid_of(hwnd_altinda(p)) == ctypes.windll.kernel32.GetCurrentProcessId()


def gercek_tik(p: QtCore.QPoint, sag: bool = False) -> bool:
    """Gercek OS fare tiki; yalnizca imlecin altindaki pencere BU surece aitse basar."""
    QtGui.QCursor.setPos(p); bekle(40)
    if KILITLI:
        olgu("    (gercek tik ATLANDI: oturum kilitli, OS girdisi gonderilmez)")
        return False
    if not bizim_mi(p):
        olgu(f"    (gercek tik ATLANDI: imlec altindaki pencere bizim degil @ {p.x()},{p.y()})")
        return False
    if sag:
        u32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0); bekle(30); u32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
    else:
        u32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0); bekle(30); u32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    bekle(150)
    return True


def on_plan() -> str:
    h = int(u32.GetForegroundWindow())
    if pid_of(h) == ctypes.windll.kernel32.GetCurrentProcessId():
        w = QtWidgets.QWidget.find(h)
        return f"BIZIM:{type(w).__name__ if w else 'hwnd'}"
    return "baska-surec"


def main() -> int:
    global KILITLI
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    KILITLI = oturum_kilitli()
    olgu(f"oturum kilitli (WTS_SESSIONSTATE_LOCK)={KILITLI} -> kilitliyse gercek OS girdisi atlanir, on-plan/hit-test kilit ekranini gorur")
    ekran = QtGui.QGuiApplication.primaryScreen(); g = ekran.availableGeometry()
    olgu(f"ekran avail=({g.x()},{g.y()},{g.width()},{g.height()}) dpr={ekran.devicePixelRatio()} ekranlar={len(QtGui.QGuiApplication.screens())}")
    sahne = QtWidgets.QLabel("temsili oyun")
    sahne.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.Tool)
    sahne.setStyleSheet("background:#1b2a41; color:#3d5a80; font: 16px 'Segoe UI';")
    sahne.setGeometry(g.right() - 640, g.y() + 300, 641, 800); sahne.show(); bekle(200)
    p = AnaPencere(CaptureService(MssBackend()))
    p.move(g.x() + 200, g.y() + 200); p.show(); bekle(400)
    s = p._sekme
    olgu(f"on-plan (ana pencere gosterildi): {on_plan()}")

    # P1 kenara al + surukleme
    QTest.mouseClick(p._b_kenar, QtCore.Qt.MouseButton.LeftButton); bekle(300)
    fg = s.frameGeometry()
    olgu(f"P1 kenara al: sekme=({fg.x()},{fg.y()},{fg.width()},{fg.height()}) on-plan={on_plan()} tepsi={p._tepsi.isVisible()}")
    y0 = s._y
    QtGui.QCursor.setPos(fg.x() - 300, fg.center().y()); bekle(100)
    QTest.mousePress(s, QtCore.Qt.MouseButton.LeftButton, pos=QtCore.QPoint(YARICAP // 2, YARICAP)); bekle(30)
    QTest.mouseMove(s, QtCore.QPoint(YARICAP // 2, YARICAP + 200)); bekle(30)
    QTest.mouseRelease(s, QtCore.Qt.MouseButton.LeftButton, pos=QtCore.QPoint(YARICAP // 2, YARICAP)); bekle(100)
    olgu(f"P1 QTest surukleme +200: y {y0} -> {s._y} (beklenen {y0 + 200}) acik={s._acik}")
    # gercek OS surukleme: bas, 5 adimda 150 px asagi, birak
    fg = s.frameGeometry(); merkez = fg.center()
    QtGui.QCursor.setPos(merkez); bekle(60)
    altinda = bizim_mi(merkez) and not KILITLI
    olgu(f"P1 gercek surukleme oncesi imlec altinda bizim pencere={bizim_mi(merkez)} kilitli={KILITLI}")
    if altinda:
        y1 = s._y
        u32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0); bekle(40)
        for i in range(1, 6):
            QtGui.QCursor.setPos(merkez.x(), merkez.y() + 30 * i); bekle(40)
        u32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0); bekle(150)
        olgu(f"P1 gercek OS surukleme +150: y {y1} -> {s._y} (beklenen {y1 + 150}) acik={s._acik} on-plan={on_plan()}")
        # ustune geldik, acilma tetiklenmis olabilir; disari cik ve kapanmasini bekle
        QtGui.QCursor.setPos(s.frameGeometry().x() - 300, merkez.y()); bekle(KAPANMA_MS + 300)
        olgu(f"P1 sonrasi: acik={s._acik}")

    # P2 hizli iceri-disari (imlec 50 ms icerde, 50 ms disarda, 10 kez)
    fg = s.frameGeometry(); ic = fg.center(); dis = QtCore.QPoint(fg.x() - 300, fg.center().y())
    acilma_sayisi = 0; onceki = s._acik
    for _ in range(10):
        QtGui.QCursor.setPos(ic); bekle(50)
        if s._acik and not onceki: acilma_sayisi += 1
        onceki = s._acik
        QtGui.QCursor.setPos(dis); bekle(50)
        if s._acik and not onceki: acilma_sayisi += 1
        onceki = s._acik
    olgu(f"P2 hizli iceri-disari 10x50/50 ms: acilma sayisi={acilma_sayisi} son acik={s._acik} acilma_timer_aktif={s._acilma.isActive()}")
    bekle(KAPANMA_MS + 200)
    olgu(f"P2 sonrasi bekleme: acik={s._acik}")

    # P3 acikken iceri-disari-iceri (100 ms disari)
    QtGui.QCursor.setPos(ic); t0 = time.perf_counter()
    while not s._acik and time.perf_counter() - t0 < 2: bekle(5)
    olgu(f"P3 acildi={s._acik} {1000*(time.perf_counter()-t0):.0f} ms")
    fg2 = s.frameGeometry(); ic2 = fg2.center()
    dis2 = QtCore.QPoint(fg2.x() - 300, fg2.center().y())
    QtGui.QCursor.setPos(dis2); bekle(100); QtGui.QCursor.setPos(ic2); bekle(KAPANMA_MS + 100)
    olgu(f"P3 iceri-disari(100ms)-iceri: acik kaldi={s._acik}")
    # panel geometrisi & dugme
    dugmeler = s._panel.findChildren(QtWidgets.QPushButton)
    olgu(f"P3 panel=({fg2.x()},{fg2.y()},{fg2.width()},{fg2.height()}) dugme sayisi={len(dugmeler)} metinler={[d.text().strip() for d in dugmeler]}")

    # P5 gercek OS sol tik panel dugmesine (Anlik ceviri) -> odak
    alindi = []
    s.anlik_cevir.connect(lambda: alindi.append(1))
    b1 = dugmeler[0]; hedef = b1.mapToGlobal(b1.rect().center())
    onp = on_plan()
    tik = gercek_tik(hedef)
    olgu(f"P5 gercek sol tik panel dugmesi: basildi={tik} sinyal={len(alindi)} on-plan once={onp} sonra={on_plan()} acik={s._acik}")
    bekle(300)

    # P8 saydam kose hit-test (kapali sekme): sol-ust kose (alpha 0) vs merkez
    QtGui.QCursor.setPos(dis2); bekle(KAPANMA_MS + 300)
    fg = s.frameGeometry()
    kose = QtCore.QPoint(fg.x() + 1, fg.y() + 1); merkez = QtCore.QPoint(fg.x() + YARICAP - 4, fg.y() + YARICAP)
    QtGui.QCursor.setPos(kose); bekle(60)
    olgu(f"P8 hit-test: kose(alpha0) bizim={bizim_mi(kose)} hwnd={hwnd_altinda(kose):#x} | merkez bizim={bizim_mi(merkez)} hwnd={hwnd_altinda(merkez):#x} sekme_hwnd={int(s.winId()):#x} sahne_hwnd={int(sahne.winId()):#x}")
    olgu(f"P8 kose imlecteyken yoklayici 'icinde' sayar mi: frameGeometry.contains={s.frameGeometry().contains(QtGui.QCursor.pos())} acilma_timer={s._acilma.isActive()}")
    QtGui.QCursor.setPos(dis2); bekle(200)

    # P4 gercek OS sag tik -> pencere gelir mi, odak
    fg = s.frameGeometry(); merkez = QtCore.QPoint(fg.x() + YARICAP - 4, fg.y() + YARICAP)
    tik = gercek_tik(merkez, sag=True)
    bekle(300)
    olgu(f"P4 gercek sag tik: basildi={tik} pencere gorunur={p.isVisible()} sekme gorunur={s.isVisible()} on-plan={on_plan()}")

    # P6 tepsi menusu
    menu = p._tepsi.contextMenu()
    olgu(f"P6 tepsi menusu: {[a.text() or '---' for a in menu.actions()]} tepsi gorunur (gorunur durumda)={p._tepsi.isVisible()}")
    QTest.mouseClick(p._b_tepsi, QtCore.Qt.MouseButton.LeftButton); bekle(300)
    olgu(f"P6 tepsiye al: pencere={p.isVisible()} tepsi={p._tepsi.isVisible()} sekme={s.isVisible()} supportsMessages={QtWidgets.QSystemTrayIcon.supportsMessages()}")
    p.goster(); bekle(300)
    olgu(f"P6 goster: pencere={p.isVisible()} tepsi={p._tepsi.isVisible()} on-plan={on_plan()}")

    # P7 gorunur durumda close() (Alt+F4 esdegeri)
    p.close(); bekle(300)
    gorunur = [type(w).__name__ for w in QtWidgets.QApplication.topLevelWidgets() if w.isVisible() and w is not sahne]
    olgu(f"P7 close() gorunur durumda: gorunur ust-duzey={gorunur} tepsi={p._tepsi.isVisible()} sekme={s.isVisible()} yoklayici calisiyor={s._yoklayici.isActive()} -> kullanici hicbir yerden ulasamaz={not gorunur and not p._tepsi.isVisible()}")

    p.kapat()  # QApplication.quit() cagirir; exec yok -> etkisiz
    sahne.close()
    CIKTI.write_text("KRT-1 madde 1 -- demo/kabuk.py gercek ekran surusu\n\n" + "\n".join(satirlar) + "\n", encoding="utf-8")
    print("yazildi: k1_prototip_surus.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
