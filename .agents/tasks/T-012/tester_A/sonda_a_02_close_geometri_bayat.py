"""Tester-A sonda 02 -- O-A2: panel ACIKKEN `sekme.close()` / `closeAllWindows()` sonrasi kapali sekmenin geometrisi 200x132 kalir.

    python .agents/tasks/T-012/tester_A/sonda_a_02_close_geometri_bayat.py [offscreen|windows]     (varsayilan offscreen; stdout ASCII)

Olcum: dort kapatma yolu (hide / close / QCloseEvent sendEvent / closeAllWindows) x panel acik: kapatma sonrasi ve yeniden
`show()` sonrasi `frameGeometry()`; bayat 200x132 ise saydam alanda (kapali dikdortgende disk disi nokta) hover panel acar.
Pozitif kontrol: `hide()` ve dogrudan QCloseEvent yollari 26x52 verir. AnaPencere yolu: kenar -> acik -> close -> kenara_al.
Kilit acikken `windows` argumaniyla gercek platformda da kosulur (tester kilitliyken kostu: ayni sonuc).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ["QT_QPA_PLATFORM"] = sys.argv[1] if len(sys.argv) > 1 else "offscreen"
KOK = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(KOK))

from PySide6 import QtCore, QtWidgets  # noqa: E402
from PySide6.QtGui import QCloseEvent, QGuiApplication  # noqa: E402

from src.ui.geometri import Kenar, sekme_icinde  # noqa: E402
from src.ui.kabuk import AnaPencere  # noqa: E402
from src.ui.kenar_sekmesi import KenarSekmesi  # noqa: E402

ihlal: list[str] = []


def dongu(ms: int) -> None:
    loop = QtCore.QEventLoop()
    QtCore.QTimer.singleShot(ms, loop.quit)
    loop.exec()


def g(s: KenarSekmesi) -> str:
    fg = s.frameGeometry()
    wh = s.windowHandle()
    return f"frame=({fg.x()},{fg.y()},{fg.width()},{fg.height()}) geo=({s.geometry().width()},{s.geometry().height()}) win={wh.geometry().size() if wh is not None else None}"


def main() -> int:
    print(f"T-012 tester-A sonda 02 -- close + acik panel geometri (platform={os.environ['QT_QPA_PLATFORM']})")
    app = QtWidgets.QApplication([])
    app.setQuitOnLastWindowClosed(False)
    ekran = QGuiApplication.primaryScreen()
    konum = [QtCore.QPoint(-10000, -10000)]

    for yol in ("hide", "close", "closeEvent_sendEvent", "closeAllWindows"):
        s = KenarSekmesi(ekran, acilma_ms=20, kapanma_ms=30, yoklama_ms=10, imlec_konumu=lambda: konum[0])
        s.show()
        dongu(20)
        kapali = s.frameGeometry()
        konum[0] = kapali.center()
        dongu(120)
        print(f"[{yol}] acik={s.acik} {g(s)}")
        konum[0] = QtCore.QPoint(-10000, -10000)
        if yol == "hide":
            s.hide()
        elif yol == "close":
            s.close()
        elif yol == "closeEvent_sendEvent":
            QtWidgets.QApplication.sendEvent(s, QCloseEvent())
        else:
            QtWidgets.QApplication.closeAllWindows()
        dongu(50)
        print(f"[{yol}] sonra: acik={s.acik} gorunur={s.isVisible()} {g(s)}")
        s.show()
        dongu(50)
        print(f"[{yol}] yeniden show: acik={s.acik} {g(s)} kapali_beklenen=({kapali.x()},{kapali.y()},{kapali.width()},{kapali.height()})")
        fg = s.frameGeometry()
        nokta = QtCore.QPoint(fg.left() + 5, fg.top() + 5)  # ekranin ic tarafi ust kosesi: saydam, disk disi
        print(f"[{yol}] nokta ({nokta.x()},{nokta.y()}) sekme_icinde={sekme_icinde(fg, nokta, 26, Kenar.SAG)} (kapali 26x52 dikdortgende olsaydi disk disi: False beklenir)")
        konum[0] = nokta
        dongu(120)
        bayat = s.frameGeometry().size() != kapali.size()
        print(f"  {'IHLAL' if bayat else 'ok   '} [{yol}] yeniden show sonrasi boyut {s.frameGeometry().width()}x{s.frameGeometry().height()} (26x52 beklenir); saydam noktada 120 ms hover acik={s.acik}")
        if bayat:
            ihlal.append(yol)
        konum[0] = QtCore.QPoint(-10000, -10000)
        dongu(80)
        s.hide()
        del s
        print()

    # AnaPencere yolu: kenar -> panel acik -> sekme.close() (kapandi -> goster) -> kenara_al
    p = AnaPencere(ekran, tepsi_kullanilabilir=True, imlec_konumu=lambda: konum[0])
    p.show()
    p.kenara_al()
    dongu(20)
    s = p.sekme
    kapali = s.frameGeometry()
    konum[0] = kapali.center()
    dongu(300)
    print(f"[AnaPencere] acik={s.acik} {g(s)}")
    konum[0] = QtCore.QPoint(-10000, -10000)
    s.close()
    dongu(50)
    print(f"[AnaPencere] close sonra: durum={p.durum} acik={s.acik} {g(s)}")
    p.kenara_al()
    dongu(100)
    print(f"[AnaPencere] kenara_al sonra: {g(s)} kapali_beklenen=({kapali.x()},{kapali.y()},{kapali.width()},{kapali.height()})")
    fg = s.frameGeometry()
    nokta = QtCore.QPoint(fg.left() + 5, fg.top() + 5)
    konum[0] = nokta
    dongu(120 + 3 * 60)
    print(f"[AnaPencere] saydam noktada hover (urun sayaclari): acik={s.acik}")
    if s.acik:
        ihlal.append("AnaPencere: kenara_al sonrasi saydam alanda hover panel acti")
    konum[0] = QtCore.QPoint(-10000, -10000)
    dongu(700)
    print(f"[AnaPencere] imlec disari 700 ms: acik={s.acik} {g(s)}  (bir acilip kapanma kendini toparlar)")
    p.kapat()
    print()
    if ihlal:
        print(f"SONDA: {len(ihlal)} IHLAL (O-A2): {ihlal}")
        return 1
    print("SONDA: TEMIZ")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
