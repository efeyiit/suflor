"""Tester-A sonda 01 -- Y-A1: `KenarSekmesi` hic toplanmiyor; kenar durumundaki AnaPencere dusurulunce ZOMBI sekme.

    python .agents/tasks/T-012/tester_A/sonda_a_01_omur_zombi.py     (offscreen, ayri surec; stdout ASCII)

Iddia (kabuk.py docstring K1): "Sekme EBEVEYNSIZ Tool penceredir (Python sahipligi: AnaPencere silinince silinir, KRT o6)".
Olcum: weakref + gc.collect + gorunur ust-duzey sayimi; mekanizma: kenar_sekmesi.py yapicisindaki uc
`clicked.connect(lambda: self._mod_tiki(...))` kapanisi Qt baglantisinda `self`i tutar (C++ tarafinda, gc gormez).
Pozitif kontrol: ayni kaliba sahip minimal QWidget -- lambda baglantili toplanmaz, bagli yontemli toplanir.
"""
from __future__ import annotations

import gc
import os
import sys
import weakref
from pathlib import Path

os.environ["QT_QPA_PLATFORM"] = "offscreen"
KOK = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(KOK))

from PySide6 import QtCore, QtWidgets  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402

from src.ui.kabuk import AnaPencere  # noqa: E402
from src.ui.kenar_sekmesi import KenarSekmesi  # noqa: E402

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
    print("T-012 tester-A sonda 01 -- omur / zombi sekme (offscreen)")
    app = QtWidgets.QApplication([])
    app.setQuitOnLastWindowClosed(False)
    ekran = QGuiApplication.primaryScreen()

    # [1] kenar durumunda son referans dusuruluyor (deleteLater yok)
    p = AnaPencere(ekran, tepsi_kullanilabilir=True)
    p.show(); p.kenara_al(); dongu(20)
    wp, ws = weakref.ref(p), weakref.ref(p.sekme)
    del p; gc.collect(); dongu(30)
    s = ws()
    rapor(wp() is None, f"[1] AnaPencere sarmalayicisi toplandi={wp() is None}")
    rapor(s is None, f"[1] sekme silindi={s is None}; gorunur ust-duzey={gorunur()}")
    if s is not None:
        n: list[int] = []
        s.pencereyi_goster.connect(lambda: n.append(1))
        QTest.mouseClick(s, QtCore.Qt.MouseButton.RightButton, pos=QtCore.QPoint(s.width() - 3, s.height() // 2)); dongu(20)
        print(f"         [1] zombi: gorunur={s.isVisible()} yokluyor={s.yokluyor} sag tik sinyal={len(n)} (alici pencere yok) -> geri donus yolu yok")
        s.hide()

    # [2] deleteLater + referans dusurme
    p = AnaPencere(ekran, tepsi_kullanilabilir=True)
    p.show(); p.kenara_al(); dongu(20)
    wp, ws = weakref.ref(p), weakref.ref(p.sekme)
    p.deleteLater(); del p; dongu(50); gc.collect(); dongu(30)
    s = ws()
    rapor(wp() is None and s is None, f"[2] deleteLater: AnaPencere toplandi={wp() is None} sekme silindi={s is None} gorunur={gorunur()}")
    if s is not None:
        s.hide()

    # [3] tek basina KenarSekmesi
    k = KenarSekmesi(ekran); k.show(); dongu(20)
    wk = weakref.ref(k)
    del k; gc.collect(); dongu(30)
    rapor(wk() is None, f"[3] tek basina KenarSekmesi son referans dusunce silindi={wk() is None} gorunur={gorunur()}")
    if wk() is not None:
        wk().hide()

    # [4] kapat() sonrasi dusurme: gizli sizinti (bilgi)
    p = AnaPencere(ekran, tepsi_kullanilabilir=True)
    p.show(); p.kenara_al(); dongu(20); p.kapat()
    ws = weakref.ref(p.sekme)
    del p; gc.collect(); dongu(30)
    print(f"  bilgi  [4] kapat()+dusurme: sekme yasiyor={ws() is not None} gorunur={ws() is not None and ws().isVisible()} (gizli sizinti, zombi degil)")

    # [5] pozitif kontrol -- mekanizma
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

    sonuc = {}
    for K in (BagliYontem, Lambdali):
        w = K(); w.show(); dongu(10)
        r = weakref.ref(w)
        del w; gc.collect(); dongu(10)
        sonuc[K.__name__] = r() is not None
        if r() is not None:
            r().hide()
    rapor(sonuc == {"BagliYontem": False, "Lambdali": True}, f"[5] pozitif kontrol: lambda baglantili canli kaldi={sonuc['Lambdali']}, bagli yontemli canli kaldi={sonuc['BagliYontem']}")

    print()
    if ihlal:
        print(f"SONDA: {len(ihlal)} IHLAL (Y-A1)")
        return 1
    print("SONDA: TEMIZ")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
