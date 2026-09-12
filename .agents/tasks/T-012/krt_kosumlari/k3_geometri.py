"""KRT-1 / madde 3 -- K2 geometri formulleri: cok monitor, DPI, gorev cubugu konumu.

    python .agents/tasks/T-012/krt_kosumlari/k3_geometri.py

G1 bu makinenin ekranlari (mantiksal geometri, availableGeometry, dpr) ve monitörler arasi MANTIKSAL bosluk
G2 paketin K2 formulleri: sag/sol kenar, y siniri, acik panel -- 3 ekran x 2 kenar x 5 y (paketin OLCU tablosu)
G3 gorev cubugu sagda/solda/ustte simulasyonu: availableGeometry ile 'kenara bitisik' fiziksel kenara bitisik mi
G4 sol monitorde (dpr 1.25) gercek pencere: mantiksal geometri, GetWindowRect fiziksel, QCursor.setPos -> contains
G5 QGuiApplication.screenAt() mantiksal boslukta None mu (imlec haritalamasi)
"""
from __future__ import annotations

import ctypes
import sys
import time
from ctypes import wintypes
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

CIKTI = Path(__file__).resolve().parent / "k3_geometri.txt"
satirlar: list[str] = []


def olgu(m: str) -> None:
    satirlar.append(m); print(" ", m)


def bekle(ms: int) -> None:
    son = time.perf_counter() + ms / 1000
    while time.perf_counter() < son:
        QtWidgets.QApplication.processEvents(); time.sleep(0.004)


# --- paketin K2 formulleri (lafzina gore) ---
def y_sinirla(ekran: QtCore.QRect, y: int, r: int) -> int:
    return min(max(ekran.top(), y), ekran.bottom() - 2 * r + 1)


def kapali(ekran: QtCore.QRect, y: int, r: int, kenar: str) -> QtCore.QRect:
    y = y_sinirla(ekran, y, r)
    x = ekran.right() - r + 1 if kenar == "sag" else ekran.left()
    return QtCore.QRect(x, y, r, 2 * r)


def acik(ekran: QtCore.QRect, y: int, r: int, panel: QtCore.QSize, kenar: str) -> QtCore.QRect:
    y = y_sinirla(ekran, y, r)
    py = min(max(ekran.top(), y - panel.height() // 2 + r), ekran.bottom() - panel.height() + 1)
    x = ekran.right() - panel.width() + 1 if kenar == "sag" else ekran.left()
    return QtCore.QRect(x, py, panel.width(), panel.height())


def main() -> int:
    app = QtWidgets.QApplication(sys.argv)
    ekranlar = QtGui.QGuiApplication.screens()
    olgu("G1 ekranlar (mantiksal):")
    for e in ekranlar:
        g, a = e.geometry(), e.availableGeometry()
        olgu(f"   {e.name()!s:14} geometry={tuple(g.getRect())} avail={tuple(a.getRect())} dpr={e.devicePixelRatio()} fiziksel={int(g.width()*e.devicePixelRatio())}x{int(g.height()*e.devicePixelRatio())} birincil={e is QtGui.QGuiApplication.primaryScreen()}")
    sol = [e for e in ekranlar if e.geometry().x() < 0]
    if sol:
        s = sol[0]; g = s.geometry(); b = QtGui.QGuiApplication.primaryScreen().geometry()
        olgu(f"G1 sol monitor mantiksal sag kenari={g.right()} birincil sol kenari={b.left()} -> mantiksal BOSLUK={b.left() - g.right() - 1} px (dpr {s.devicePixelRatio()} ile fiziksel sag kenar={g.x() + int(g.width()*s.devicePixelRatio()) - 1})")

    olgu("G2 paket OLCU tablosu (3 ekran x 2 kenar x 5 y), r=26, panel 200x132:")
    P = QtCore.QSize(200, 132); r = 26
    ekran_listesi = {"birincil 2560x1392": QtCore.QRect(0, 0, 2560, 1392), "sol -2560 (paket: 2560x1440)": QtCore.QRect(-2560, 0, 2560, 1440),
                     "sol -2560 (GERCEK mantiksal, dpr1.25: 2048x1104)": QtCore.QRect(-2560, 0, 2048, 1104), "1280x720": QtCore.QRect(0, 0, 1280, 720)}
    ihlal = 0
    for ad, ek in ekran_listesi.items():
        for kenar in ("sag", "sol"):
            for y in (ek.top(), ek.center().y() - r, ek.bottom() - 2 * r + 1, -1000, 9999):
                k = kapali(ek, y, r, kenar); a = acik(ek, y, r, P, kenar)
                ok = ek.contains(k) and ek.contains(a) and ((k.right() == ek.right() and a.right() == ek.right()) if kenar == "sag" else (k.left() == ek.left() and a.left() == ek.left()))
                ihlal += not ok
                if not ok or y in (-1000, 9999):
                    olgu(f"   {ad} {kenar} y={y}: kapali={tuple(k.getRect())} acik={tuple(a.getRect())} icinde={ek.contains(k) and ek.contains(a)} bitisik={ok}")
    olgu(f"G2 ihlal={ihlal} (paketin formulleri kendi icinde tutarli); U2 ile birebir: {tuple(kapali(QtCore.QRect(0,0,2560,1392), 670, 26, 'sag').getRect())} == (2534,670,26,52)")
    # y_sinirla monoton + panel hizasi
    ek = QtCore.QRect(0, 0, 2560, 1392)
    ys = [y_sinirla(ek, y, r) for y in range(-100, 1500, 7)]
    olgu(f"G2 y_sinirla monoton={all(a <= b for a, b in zip(ys, ys[1:]))} aralik=[{min(ys)},{max(ys)}] (paket: [0, {ek.bottom()-2*r+1}])")
    a_orta = acik(ek, 670, r, P, "sag"); k_orta = kapali(ek, 670, r, "sag")
    olgu(f"G2 panel merkez y={a_orta.center().y()} sekme merkez y={k_orta.center().y()} fark={a_orta.center().y()-k_orta.center().y()} (U3 paneli (2360,630,200,132) ile ayni: {tuple(a_orta.getRect())==(2360,630,200,132)})")
    # en ustte: panel sekmeyle hizali kalamaz
    a_ust = acik(ek, 0, r, P, "sag"); k_ust = kapali(ek, 0, r, "sag")
    olgu(f"G2 y=0'da panel={tuple(a_ust.getRect())} sekme={tuple(k_ust.getRect())} -> panel sekmenin merkezine hizali DEGIL (sikistirildi), imlec sekmeden panele gecerken dikdortgen degisir")

    olgu("G3 gorev cubugu konumu simulasyonu (birincil fiziksel 2560x1440, cubuk 48 px):")
    tam = QtCore.QRect(0, 0, 2560, 1440)
    for ad, av in {"altta (bu makine)": QtCore.QRect(0, 0, 2560, 1392), "SAGDA": QtCore.QRect(0, 0, 2512, 1440), "SOLDA": QtCore.QRect(48, 0, 2512, 1440), "ustte": QtCore.QRect(0, 48, 2560, 1392)}.items():
        ks = kapali(av, av.center().y() - r, r, "sag"); kl = kapali(av, av.center().y() - r, r, "sol")
        olgu(f"   cubuk {ad:18} avail={tuple(av.getRect())}: sag sekme x-araligi=[{ks.left()},{ks.right()}] fiziksel sag kenar={tam.right()} -> FIZIKSEL kenara bitisik={ks.right()==tam.right()} | sol sekme [{kl.left()},{kl.right()}] fiziksel sol kenar=0 -> bitisik={kl.left()==tam.left()}")
    olgu("G3 not: cubuk sagdayken 'kenara at' hareketi cubuga varir, sekmeye degil (cubuk kendi ustte-kalan bandi); paket geometry() mi availableGeometry() mi secimini yalniz 'mantiksal piksel' diye gecer")

    # G4 sol monitorde gercek pencere
    if sol:
        s = sol[0]; av = s.availableGeometry()
        w = QtWidgets.QWidget(None, QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.Tool | QtCore.Qt.WindowType.WindowStaysOnTopHint | QtCore.Qt.WindowType.WindowDoesNotAcceptFocus)
        w.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground); w.setAttribute(QtCore.Qt.WidgetAttribute.WA_ShowWithoutActivating)
        w.setScreen(s)
        k = kapali(av, av.center().y() - r, r, "sag"); w.setGeometry(k); w.show(); bekle(300)
        fg = w.frameGeometry()
        rc = wintypes.RECT(); ctypes.windll.user32.GetWindowRect(wintypes.HWND(int(w.winId())), ctypes.byref(rc))
        olgu(f"G4 sol monitor (dpr {s.devicePixelRatio()}) sag kenar sekmesi: istenen={tuple(k.getRect())} frameGeometry={tuple(fg.getRect())} ekran={w.screen().name()} GetWindowRect fiziksel=({rc.left},{rc.top},{rc.right},{rc.bottom}) -> fiziksel sag kenar {rc.right-1} == -1 (birincile bitisik): {rc.right - 1 == -1}")
        hedef = fg.center(); QtGui.QCursor.setPos(hedef); bekle(80); p = QtGui.QCursor.pos()
        olgu(f"G4 QCursor.setPos({hedef.x()},{hedef.y()}) -> pos=({p.x()},{p.y()}) frameGeometry.contains={fg.contains(p)} screenAt={QtGui.QGuiApplication.screenAt(p).name() if QtGui.QGuiApplication.screenAt(p) else None}")
        # birincilin sol kenarina 1 px: mantiksal (0, y) -> bu, sol monitorun sekmesinin 'hemen sagi'
        QtGui.QCursor.setPos(0, hedef.y()); bekle(80); p2 = QtGui.QCursor.pos()
        olgu(f"G4 imlec birincil (0,{hedef.y()}) -> pos=({p2.x()},{p2.y()}) sekme contains={fg.contains(p2)}; fiziksel olarak sekmeye 1 px mesafede ama mantiksal fark={p2.x()-fg.right()} px")
        w.close()
    # G5 boslukta screenAt
    for x in (-600, -512, -300, -1, 0):
        e = QtGui.QGuiApplication.screenAt(QtCore.QPoint(x, 500))
        olgu(f"G5 screenAt(({x},500)) = {e.name() if e else None}")
    CIKTI.write_text("KRT-1 madde 3 -- geometri\n\n" + "\n".join(satirlar) + "\n", encoding="utf-8")
    print("yazildi: k3_geometri.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
