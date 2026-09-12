"""T-012 tur 2 -- omur (Y-A1) GERCEK Windows platforminda (offscreen degil), kilitten ve fareden BAGIMSIZ.

    python .agents/tasks/T-012/evidence/olcum-tur2-omur-gercek-platform.py

Offscreen testler Python/PySide sarmalayici omrunu olcer; burada ayrica Win32 kanaliyla
(`IsWindow(hwnd)`, Qt'den bagimsiz -- kural 8) sekmenin PENCERESININ yok edildigi olculur:
  [1] kenar durumunda `del` + `gc.collect()` -> AnaPencere/sekme/tepsi weakref None, sekme hwnd yok, gorunur ust-duzey 0
  [2] `deleteLater` yolu ayni
  [3] tek basina KenarSekmesi ayni
  [4] pozitif kontrol: lambda baglantili minimal Tool widget -> hwnd YASAR (olcu ateslenebilir); bagli yontemli -> yok
Stdout ASCII; mutlak yol yok. Cikis 0 = temiz.
"""
from __future__ import annotations

import ctypes
import gc
import os
import sys
import weakref
from ctypes import wintypes
from pathlib import Path

os.environ.pop("QT_QPA_PLATFORM", None)
KOK = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(KOK))

from PySide6 import QtCore, QtGui, QtWidgets  # noqa: E402

from src.ui.kabuk import AnaPencere  # noqa: E402
from src.ui.kenar_sekmesi import KenarSekmesi  # noqa: E402

u32 = ctypes.windll.user32
u32.IsWindow.argtypes = [wintypes.HWND]
ihlal: list[str] = []


def dongu(ms: int) -> None:
    loop = QtCore.QEventLoop()
    QtCore.QTimer.singleShot(ms, loop.quit)
    loop.exec()


def gorunur() -> list[str]:
    return [type(w).__name__ for w in QtWidgets.QApplication.topLevelWidgets() if w.isVisible()]


def rapor(ok: bool, m: str) -> None:
    print(("  ok     " if ok else "  IHLAL  ") + m)
    if not ok:
        ihlal.append(m)


def main() -> int:
    app = QtWidgets.QApplication([])
    app.setQuitOnLastWindowClosed(False)
    print(f"T-012 tur 2 omur -- platform={app.platformName()} (gercek ekran; fare/on plan gerekmez)")
    ekran = QtGui.QGuiApplication.primaryScreen()

    for yol in ("del_gc", "deleteLater"):
        p = AnaPencere(ekran, tepsi_kullanilabilir=True)
        p.show(); p.kenara_al(); dongu(150)
        hwnd = wintypes.HWND(int(p.sekme.winId()))
        wp, ws, wt = weakref.ref(p), weakref.ref(p.sekme), weakref.ref(p.tepsi)
        canliydi = bool(u32.IsWindow(hwnd)) and p.sekme.isVisible()
        if yol == "deleteLater":
            p.deleteLater()
        del p
        gc.collect(); dongu(300)
        pencere_var = bool(u32.IsWindow(hwnd))
        etiket = "[1] del+gc" if yol == "del_gc" else "[2] deleteLater"
        rapor(canliydi and wp() is None and ws() is None and wt() is None and not pencere_var and gorunur() == [],
              f"{etiket}: onceden hwnd canli={canliydi}; sonra AnaPencere toplandi={wp() is None} sekme silindi={ws() is None} "
              f"tepsi silindi={wt() is None} sekme hwnd hala var={pencere_var} gorunur ust-duzey={gorunur()}")
        artik = ws()
        if artik is not None:
            artik.hide()

    k = KenarSekmesi(ekran); k.show(); dongu(150)
    hwnd = wintypes.HWND(int(k.winId())); wk = weakref.ref(k)
    del k; gc.collect(); dongu(300)
    rapor(wk() is None and not u32.IsWindow(hwnd), f"[3] tek basina KenarSekmesi: silindi={wk() is None} hwnd hala var={bool(u32.IsWindow(hwnd))} gorunur={gorunur()}")
    if wk() is not None:
        wk().hide()

    class Lambdali(QtWidgets.QWidget):
        def __init__(self) -> None:
            super().__init__(None, QtCore.Qt.WindowType.Tool)
            self.b = QtWidgets.QPushButton("x", self)
            self.b.clicked.connect(lambda: self._tik())

        def _tik(self) -> None:
            pass

    class BagliYontem(QtWidgets.QWidget):
        def __init__(self) -> None:
            super().__init__(None, QtCore.Qt.WindowType.Tool)
            self.b = QtWidgets.QPushButton("x", self)
            self.b.clicked.connect(self._tik)

        def _tik(self) -> None:
            pass

    sonuc: dict[str, bool] = {}
    for K in (BagliYontem, Lambdali):
        w = K(); w.setGeometry(ekran.availableGeometry().x() + 50, ekran.availableGeometry().y() + 50, 60, 40); w.show(); dongu(100)
        hwnd = wintypes.HWND(int(w.winId())); r = weakref.ref(w)
        del w; gc.collect(); dongu(100)
        sonuc[K.__name__] = bool(u32.IsWindow(hwnd))
        canli = r()
        if canli is not None:
            canli.hide(); canli.deleteLater(); dongu(50)
    rapor(sonuc == {"BagliYontem": False, "Lambdali": True},
          f"[4] pozitif kontrol (hwnd yasiyor mu): lambda baglantili={sonuc['Lambdali']} bagli yontemli={sonuc['BagliYontem']}")

    print()
    if ihlal:
        print(f"OMUR GERCEK PLATFORM: {len(ihlal)} IHLAL"); return 1
    print("OMUR GERCEK PLATFORM: TEMIZ"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
