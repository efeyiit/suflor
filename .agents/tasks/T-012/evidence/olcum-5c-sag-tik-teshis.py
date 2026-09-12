"""T-012 [5c] teshisi -- surukleme sonrasi gercek OS sag tiki neden pencereyi getirmiyor? (implementer delili)

    python .agents/tasks/T-012/evidence/olcum-5c-sag-tik-teshis.py

Kapi (`real_check.py`) dizisi dort varyantta tekrarlanir; her varyantta sag tik ONCESI ve SONRASI
bagimsiz kanallar okunur (Win32: GetCursorPos / WindowFromPoint / GetWindowRect / GetCapture;
Qt: sekme uzerine olay suzgeci + yerel WM_* ileti suzgeci). Amac: hangi asamada ne kayboluyor.
  V1  kenara al -> surukleme -> sag tik                           (kapinin dogrudan kosumu: [3]/[4a] atlanmisti, [5c] GECTI)
  V2  kenara al -> hover ac / uzaklas kapat -> surukleme -> sag tik
  V3  kenara al -> gercek sol tik sekme -> hover ac -> gercek sol tik panel dugmesi -> surukleme -> sag tik
  V4  tam dizi: V3 + hover ac/kapat ([4a]/[4b]) + surukleme + sag tik  (kapinin sarici kosumu: [5c] IHLAL)
  V5  V1 + sag tik oncesi imlec 700 ms sekmede bekletilir (panel ACIKKEN sag tik) -- kontrol
  V6  kapinin BIREBIR dizisi: tepsi/goster/QTest kenar > sahne on plana (activateWindow) > V4 adimlari
      (sahnenin on plana gelmesi icin `real_check-on-plan-sarici.py <bu betik>` ile kosulur)
  V7  V1 + sahne on planda (yalniz on plan farki)
Fare `IDLE_S` s hareketsiz kalana kadar beklenir (kullanici faresi olcumu bozar). Stdout ASCII; mutlak yol yok.
"""
from __future__ import annotations

import ctypes
import os
import sys
import time
from ctypes import wintypes
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(KOK))
os.environ.pop("QT_QPA_PLATFORM", None)

from PySide6 import QtCore, QtGui, QtWidgets  # noqa: E402

u32 = ctypes.windll.user32
k32 = ctypes.windll.kernel32
u32.GetForegroundWindow.restype = wintypes.HWND
u32.WindowFromPoint.restype = wintypes.HWND
u32.WindowFromPoint.argtypes = [wintypes.POINT]
u32.GetCapture.restype = wintypes.HWND
IDLE_S = 6.0
WM_ADLARI = {
    0x0200: "WM_MOUSEMOVE", 0x0201: "WM_LBUTTONDOWN", 0x0202: "WM_LBUTTONUP", 0x0204: "WM_RBUTTONDOWN",
    0x0205: "WM_RBUTTONUP", 0x007B: "WM_CONTEXTMENU", 0x0215: "WM_CAPTURECHANGED", 0x02A3: "WM_MOUSELEAVE",
    0x0245: "WM_POINTERUPDATE", 0x0246: "WM_POINTERDOWN", 0x0247: "WM_POINTERUP", 0x0021: "WM_MOUSEACTIVATE",
    0x0006: "WM_ACTIVATE", 0x001C: "WM_ACTIVATEAPP", 0x0047: "WM_WINDOWPOSCHANGED",
}


def bekle(ms: int) -> None:
    son = time.perf_counter() + ms / 1000
    while time.perf_counter() < son:
        QtWidgets.QApplication.processEvents()
        time.sleep(0.004)


def imlec() -> tuple[int, int]:
    pt = wintypes.POINT()
    u32.GetCursorPos(ctypes.byref(pt))
    return (pt.x, pt.y)


def bosta_bekle() -> float:
    t0 = time.perf_counter()
    son_konum = imlec()
    son_hareket = time.perf_counter()
    while time.perf_counter() - t0 < 900:
        time.sleep(0.1)
        su = imlec()
        if su != son_konum:
            son_konum, son_hareket = su, time.perf_counter()
        elif time.perf_counter() - son_hareket >= IDLE_S:
            return time.perf_counter() - t0
    return time.perf_counter() - t0


def sinif_adi(h: int) -> str:
    buf = ctypes.create_unicode_buffer(128)
    u32.GetClassNameW(wintypes.HWND(h), buf, 128)
    return buf.value


def pid_of(h: int) -> int:
    pid = wintypes.DWORD(0)
    u32.GetWindowThreadProcessId(wintypes.HWND(h), ctypes.byref(pid))
    return pid.value


def pencere_rect(h: int) -> tuple[int, int, int, int]:
    r = wintypes.RECT()
    u32.GetWindowRect(wintypes.HWND(h), ctypes.byref(r))
    return (r.left, r.top, r.right, r.bottom)


def altindaki(p: QtCore.QPoint) -> str:
    h = int(u32.WindowFromPoint(wintypes.POINT(p.x(), p.y())) or 0)
    bizim = pid_of(h) == k32.GetCurrentProcessId()
    w = QtWidgets.QWidget.find(h) if bizim else None
    return f"hwnd={'BIZIM:' + (type(w).__name__ if w else 'hwnd') if bizim else 'BASKA'} sinif={sinif_adi(h)!r}"


class OlaySuzgeci(QtCore.QObject):
    def __init__(self) -> None:
        super().__init__()
        self.kayit: list[str] = []

    def eventFilter(self, obj: QtCore.QObject, ev: QtCore.QEvent) -> bool:
        t = ev.type()
        if t in (QtCore.QEvent.Type.MouseButtonPress, QtCore.QEvent.Type.MouseButtonRelease, QtCore.QEvent.Type.ContextMenu):
            if isinstance(ev, QtGui.QMouseEvent):
                self.kayit.append(f"{t.name}:{ev.button().name}@{ev.globalPosition().toPoint().x()},{ev.globalPosition().toPoint().y()}")
            else:
                self.kayit.append(t.name)
        return False


class YerelSuzgec(QtCore.QAbstractNativeEventFilter):
    def __init__(self) -> None:
        super().__init__()
        self.kayit: list[str] = []
        self.hedef = 0

    def nativeEventFilter(self, tur: object, ileti: object) -> tuple[bool, int]:
        msg = wintypes.MSG.from_address(int(ileti))  # type: ignore[arg-type]
        if int(msg.hWnd or 0) == self.hedef and msg.message in WM_ADLARI and msg.message != 0x0200:
            self.kayit.append(WM_ADLARI[msg.message])
        return (False, 0)


def durum(p, s, etiket: str) -> None:  # type: ignore[no-untyped-def]
    fg = s.frameGeometry()
    h = int(s.winId())
    print(f"    {etiket}: acik={s.acik} surukleniyor={s.surukleniyor} yokluyor={s.yokluyor} y={s.y} durum={p.durum}"
          f" frameGeometry=({fg.x()},{fg.y()},{fg.width()},{fg.height()}) GetWindowRect={pencere_rect(h)}"
          f" GetCapture={'sekme' if int(u32.GetCapture() or 0) == h else int(u32.GetCapture() or 0)} imlec={imlec()}")


def gercek_tik(p: QtCore.QPoint, sag: bool = False) -> None:
    QtGui.QCursor.setPos(p); bekle(80)
    asagi, yukari = (0x0008, 0x0010) if sag else (0x0002, 0x0004)
    u32.mouse_event(asagi, 0, 0, 0, 0); bekle(30); u32.mouse_event(yukari, 0, 0, 0, 0); bekle(250)


def surukle(s, g) -> None:  # type: ignore[no-untyped-def]
    fg3 = s.frameGeometry()
    bas = QtCore.QPoint(fg3.right() - 4, fg3.center().y())
    QtGui.QCursor.setPos(bas); bekle(80)
    u32.mouse_event(0x0002, 0, 0, 0, 0); bekle(60)
    for adim in range(1, 11):
        QtGui.QCursor.setPos(QtCore.QPoint(bas.x(), bas.y() + adim * 400)); bekle(60)
    u32.mouse_event(0x0004, 0, 0, 0, 0); bekle(120)


def varyant(ad: str, adimlar: str, g, yerel: YerelSuzgec, sahne: QtWidgets.QWidget) -> None:  # type: ignore[no-untyped-def]
    from PySide6.QtTest import QTest

    from src.ui.kabuk import AnaPencere

    print(f"\n[{ad}] {adimlar}")
    p = AnaPencere(QtGui.QGuiApplication.primaryScreen())
    p.move(g.x() + 200, g.y() + 200); p.show(); bekle(300)
    s = p.sekme
    suzgec = OlaySuzgeci()
    s.installEventFilter(suzgec)
    if not adimlar.startswith("tepsi"):
        p.kenara_al(); bekle(300)
    yerel.hedef = int(s.winId()); yerel.kayit.clear()
    for adim in adimlar.split(">"):
        adim = adim.strip()
        fg = s.frameGeometry()
        if adim == "tepsi":
            QTest.mouseClick(p.dugme_tepsi, QtCore.Qt.MouseButton.LeftButton); bekle(300)
            p.goster(); bekle(200)
            QTest.mouseClick(p.dugme_kenar, QtCore.Qt.MouseButton.LeftButton); bekle(300)
            print(f"    tepsi > goster > QTest kenar: durum={p.durum} uclu={(p.isVisible(), s.isVisible(), p.tepsi.gorunur())}")
        elif adim == "sahneonplan":
            sahne.raise_(); sahne.activateWindow(); bekle(300)
            print(f"    sahne on planda={int(u32.GetForegroundWindow() or 0) == int(sahne.winId())}")
        elif adim == "soltik":
            gercek_tik(QtCore.QPoint(fg.right() - 4, fg.center().y()))
            print(f"    sol tik sonrasi: acik={s.acik} surukleniyor={s.surukleniyor}")
        elif adim == "hoverac":
            QtGui.QCursor.setPos(QtCore.QPoint(fg.right() - 4, fg.center().y())); t0 = time.perf_counter()
            while not s.acik and time.perf_counter() - t0 < 3: bekle(5)
            bekle(150)
            print(f"    hover ac: acik={s.acik} {1000 * (time.perf_counter() - t0):.0f} ms")
        elif adim == "paneltik":
            tik: list[int] = []
            s.bolge_izle.connect(lambda: tik.append(1))
            d = s.dugme_bolge
            gercek_tik(d.mapToGlobal(d.rect().center()))
            print(f"    panel dugmesi gercek tik: clicked={len(tik)} acik={s.acik}")
        elif adim == "uzaklas":
            QtGui.QCursor.setPos(QtCore.QPoint(g.x() + 100, g.y() + 100)); bekle(700)
            print(f"    uzaklas 700 ms: acik={s.acik}")
        elif adim == "hoverkapat":
            QtGui.QCursor.setPos(fg.x() - 300, fg.center().y()); t0 = time.perf_counter()
            while s.acik and time.perf_counter() - t0 < 4: bekle(5)
            print(f"    hover kapat: acik={s.acik} {1000 * (time.perf_counter() - t0):.0f} ms")
        elif adim == "surukle":
            suzgec.kayit.clear(); yerel.kayit.clear()
            surukle(s, g)
            print(f"    surukleme: y={s.y} (alt sinir {g.bottom() - 2 * s.yaricap + 1}) acik={s.acik} surukleniyor={s.surukleniyor}")
            print(f"      Qt olaylari: {suzgec.kayit}")
            print(f"      WM iletileri: {yerel.kayit}")
        elif adim == "beklesekmede":
            QtGui.QCursor.setPos(QtCore.QPoint(fg.right() - 4, fg.center().y())); bekle(700)
            print(f"    imlec sekmede 700 ms: acik={s.acik}")
        elif adim == "sagtik":
            hedef = QtCore.QPoint(fg.right() - 4, fg.center().y())
            QtGui.QCursor.setPos(hedef); bekle(80)
            durum(p, s, "sag tik ONCESI")
            print(f"    hedef=({hedef.x()},{hedef.y()}) altindaki pencere: {altindaki(hedef)}")
            suzgec.kayit.clear(); yerel.kayit.clear()
            u32.mouse_event(0x0008, 0, 0, 0, 0); bekle(30); u32.mouse_event(0x0010, 0, 0, 0, 0); bekle(250)
            uclu = (p.isVisible(), s.isVisible(), p.tepsi.gorunur())
            sonuc = "OK" if uclu == (True, False, False) else "IHLAL"
            onp = int(u32.GetForegroundWindow() or 0)
            print(f"    sag tik SONRASI: {sonuc} uclu={uclu} durum={p.durum} on plan={'sahne' if onp == int(sahne.winId()) else ('AnaPencere' if onp == int(p.winId()) else 'baska')}")
            print(f"      Qt olaylari: {suzgec.kayit}")
            print(f"      WM iletileri: {yerel.kayit}")
        else:
            raise ValueError(adim)
    QtGui.QCursor.setPos(QtCore.QPoint(g.x() + 100, g.y() + 100)); bekle(200)
    p.kapat(); bekle(200)


def main() -> int:
    print("T-012 [5c] teshis -- gercek ekran")
    beklenen = bosta_bekle()
    print(f"fare bosta bekleme {beklenen:.1f} s")
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    yerel = YerelSuzgec()
    app.installNativeEventFilter(yerel)
    g = QtGui.QGuiApplication.primaryScreen().availableGeometry()
    imlec0 = imlec()
    sahne = QtWidgets.QLabel("oyun penceresi (temsili)")
    sahne.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
    sahne.setStyleSheet("background:#1b2a41; color:#3d5a80; font: 16px 'Segoe UI'; padding: 20px;")
    sahne.setGeometry(g.right() - 640, g.y() + 300, 641, 800)
    sahne.show(); bekle(200)
    secim = sys.argv[1] if len(sys.argv) > 1 else "hepsi"
    if secim in ("hepsi", "onplansiz"):
        varyant("V1", "surukle > uzaklas > sagtik", g, yerel, sahne)
        varyant("V2", "hoverac > hoverkapat > surukle > uzaklas > sagtik", g, yerel, sahne)
        varyant("V3", "soltik > hoverac > paneltik > uzaklas > surukle > uzaklas > sagtik", g, yerel, sahne)
        varyant("V4", "soltik > hoverac > paneltik > uzaklas > hoverac > hoverkapat > surukle > uzaklas > sagtik", g, yerel, sahne)
        varyant("V5", "surukle > uzaklas > beklesekmede > sagtik", g, yerel, sahne)
    if secim in ("hepsi", "onplan"):
        varyant("V6", "tepsi > sahneonplan > soltik > hoverac > paneltik > uzaklas > hoverac > hoverkapat > surukle > uzaklas > sagtik", g, yerel, sahne)
        varyant("V7", "sahneonplan > surukle > uzaklas > sagtik", g, yerel, sahne)
    sahne.close()
    QtGui.QCursor.setPos(QtCore.QPoint(*imlec0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
