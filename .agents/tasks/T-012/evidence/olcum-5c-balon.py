"""T-012 [5c] kok neden olcumu -- `tepsiye_al()` bildirim balonu (toast) sekmenin alt-sag konumunu orter mi, ne kadar?

    python .agents/tasks/T-012/evidence/olcum-5c-balon.py

Teshis (`olcum-5c-sag-tik-teshis*.txt`): kapinin birebir dizisinde (V6) sag tik oncesi `WindowFromPoint` sekme degil
`Windows.UI.Core.CoreWindow` (baska surec) veriyordu; V6'yi gecen V4'ten ayiran tek adim [1a] tepsiye al. Bu betik:
  (1) `tepsiye_al()` sonrasi 12 s boyunca 100 ms'de bir, sekmenin SURUKLEME SONRASI konumundaki noktada
      (`g.right()-4`, alt sinir + yaricap) hangi pencere var: sinif / baslik / dikdortgen / surec; gecisler zamanla.
  (2) Ayni olcum `bildir` KAPALI (negatif kontrol): nokta hep bizim mi.
  (3) Balon dikdortgeni ile kapali sekmenin alt-sinir dikdortgeninin kesisimi.
Stdout ASCII; mutlak yol yok. Fare kullanilmaz (yalniz GetCursorPos okunur); pencere tiklanmaz.
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
u32.WindowFromPoint.restype = wintypes.HWND
u32.WindowFromPoint.argtypes = [wintypes.POINT]
u32.GetAncestor.restype = wintypes.HWND


def bekle(ms: int) -> None:
    son = time.perf_counter() + ms / 1000
    while time.perf_counter() < son:
        QtWidgets.QApplication.processEvents()
        time.sleep(0.004)


def sinif_adi(h: int) -> str:
    buf = ctypes.create_unicode_buffer(128)
    u32.GetClassNameW(wintypes.HWND(h), buf, 128)
    return buf.value


def baslik(h: int) -> str:
    buf = ctypes.create_unicode_buffer(256)
    u32.GetWindowTextW(wintypes.HWND(h), buf, 256)
    return buf.value.encode("ascii", "replace").decode()


def pid_of(h: int) -> int:
    pid = wintypes.DWORD(0)
    u32.GetWindowThreadProcessId(wintypes.HWND(h), ctypes.byref(pid))
    return pid.value


def rect(h: int) -> tuple[int, int, int, int]:
    r = wintypes.RECT()
    u32.GetWindowRect(wintypes.HWND(h), ctypes.byref(r))
    return (r.left, r.top, r.right, r.bottom)


def kesisir(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def kim(p: QtCore.QPoint, sekme_hwnd: int) -> str:
    h = int(u32.WindowFromPoint(wintypes.POINT(p.x(), p.y())) or 0)
    if h == sekme_hwnd:
        return "SEKME"
    kok = int(u32.GetAncestor(wintypes.HWND(h), 2) or h)  # GA_ROOT
    bizim = pid_of(h) == k32.GetCurrentProcessId()
    return f"{'BIZIM' if bizim else 'BASKA'} sinif={sinif_adi(h)!r} baslik={baslik(kok)!r} rect={rect(kok)}"


def izle(etiket: str, bildir_acik: bool, sure_s: float = 12.0) -> None:
    from src.ui.kabuk import AnaPencere

    ekran = QtGui.QGuiApplication.primaryScreen()
    g = ekran.availableGeometry()
    p = AnaPencere(ekran)
    if not bildir_acik:
        p.tepsi.bildir = lambda *a: None  # type: ignore[method-assign]  # negatif kontrol: balon yok
    p.move(g.x() + 200, g.y() + 200); p.show(); bekle(300)
    s = p.sekme
    yar = s.yaricap
    alt = g.bottom() - 2 * yar + 1
    nokta = QtCore.QPoint(g.right() - 4, alt + yar)  # kapinin [5c] tik noktasi (surukleme sonrasi sekme merkezi)
    sekme_alt_rect = (g.right() - yar + 1, alt, g.right() + 1, alt + 2 * yar)
    print(f"\n[{etiket}] bildir={'ACIK' if bildir_acik else 'KAPALI'}; tik noktasi=({nokta.x()},{nokta.y()}); kapali sekme alt-sinir rect={sekme_alt_rect}")
    t0 = time.perf_counter()
    p.tepsiye_al(); bekle(100)
    p.kenara_al(); bekle(100)
    s.y = alt  # sekme alt sinira (surukleme sonrasi konum), fare kullanilmadan
    bekle(100)
    print(f"    kenara al + y=alt: acik={s.acik} frameGeometry=({s.frameGeometry().x()},{s.frameGeometry().y()},{s.frameGeometry().width()},{s.frameGeometry().height()}) GetWindowRect={rect(int(s.winId()))}")
    hwnd = int(s.winId())
    onceki = None
    ilk_balon: float | None = None
    son_balon: float | None = None
    balon_rect = None
    while time.perf_counter() - t0 < sure_s:
        k = kim(nokta, hwnd)
        if k != onceki:
            print(f"    t={time.perf_counter() - t0:6.2f} s  nokta altinda: {k}")
            onceki = k
        if k.startswith("BASKA"):
            son_balon = time.perf_counter() - t0
            if ilk_balon is None:
                ilk_balon = son_balon
                h = int(u32.WindowFromPoint(wintypes.POINT(nokta.x(), nokta.y())) or 0)
                balon_rect = rect(int(u32.GetAncestor(wintypes.HWND(h), 2) or h))
        bekle(100)
    if ilk_balon is None:
        print(f"    SONUC: {sure_s:.0f} s boyunca nokta hep bizim/masaustu; orten pencere YOK")
    else:
        print(f"    SONUC: orten pencere t={ilk_balon:.2f}..{son_balon:.2f} s (omur ~{(son_balon or 0) - ilk_balon:.1f} s); rect={balon_rect};"
              f" sekme alt-sinir rect ile kesisir={kesisir(balon_rect, sekme_alt_rect) if balon_rect else None}")
    p.kapat(); bekle(200)


def main() -> int:
    print("T-012 [5c] balon olcumu -- gercek ekran")
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    print(f"tepsi kullanilabilir={QtWidgets.QSystemTrayIcon.isSystemTrayAvailable()} bildirim destegi={QtWidgets.QSystemTrayIcon.supportsMessages()}")
    izle("A", bildir_acik=True)
    izle("B", bildir_acik=False)
    izle("C", bildir_acik=True)  # tekrar: omur kararli mi
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
