"""T-012 ön ölçüm: demo/kabuk.py kabuğunu gerçek ekranda sürer, olguları ve ekran görüntülerini kaydeder.

    python .agents/tasks/T-012/olcum_kabuk.py

U1 tepsi var mı · U2 kenar sekmesi geometrisi/bayrakları · U3 imleçle açılma/kapanma süreleri ·
U4 sağ tık → pencere · U5 odak: sekme gösterilince aktif pencere değişiyor mu · U6 sürükleme sınırı.
Stdout ASCII.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

KOK = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(KOK))

from PySide6 import QtCore, QtGui, QtWidgets  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402

from demo.kabuk import YARICAP, AnaPencere  # noqa: E402
from src.capture.service import CaptureService, MssBackend  # noqa: E402

CIKTI = Path(__file__).resolve().parent
satirlar: list[str] = []


def olgu(m: str) -> None:
    satirlar.append(m); print(" ", m)


def bekle(ms: int) -> None:
    son = time.perf_counter() + ms / 1000
    while time.perf_counter() < son:
        QtWidgets.QApplication.processEvents()
        time.sleep(0.005)


def ekran_al(ekran: QtGui.QScreen, r: QtCore.QRect, ad: str) -> None:
    ekran.grabWindow(0, r.x(), r.y(), r.width(), r.height()).save(str(CIKTI / ad))


def main() -> int:
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    ekran = QtGui.QGuiApplication.primaryScreen()
    g = ekran.availableGeometry()
    olgu(f"U0 birincil ekran availableGeometry: x={g.x()} y={g.y()} w={g.width()} h={g.height()} dpr={ekran.devicePixelRatio()}")
    # temsili oyun arka plani: ekran goruntuleri masaustunu/baska pencereleri icermesin (depo herkese acik)
    sahne = QtWidgets.QLabel("oyun penceresi (temsili)")
    sahne.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.Tool)
    sahne.setStyleSheet("background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #1b2a41, stop:1 #0b1220); color:#3d5a80; font: 16px 'Segoe UI'; padding: 20px;")
    sahne.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignLeft)
    sahne.setGeometry(g.right() - 640, g.y() + 300, 641, 800)
    sahne.show(); bekle(200)
    p = AnaPencere(CaptureService(MssBackend()))
    p.move(g.x() + 200, g.y() + 200)
    p.show(); bekle(400)
    p.grab().save(str(CIKTI / "kabuk_ana_pencere.png"))
    olgu(f"U1 QSystemTrayIcon.isSystemTrayAvailable = {QtWidgets.QSystemTrayIcon.isSystemTrayAvailable()}")

    # kenara al
    QTest.mouseClick(p._b_kenar, QtCore.Qt.MouseButton.LeftButton); bekle(300)
    s = p._sekme
    fg = s.frameGeometry()
    olgu(f"U2 kenara al: ana pencere gorunur={p.isVisible()} sekme gorunur={s.isVisible()} sekme geometri=({fg.x()},{fg.y()},{fg.width()},{fg.height()}) ekran sag kenari={g.right()}")
    olgu(f"U2 sekme sag kenara bitisik={fg.right() == g.right()} dikey orta={abs(fg.center().y() - g.center().y()) <= 1}")
    bayraklar = s.windowFlags()
    olgu(f"U2 bayraklar: Tool={bool(bayraklar & QtCore.Qt.WindowType.Tool)} Frameless={bool(bayraklar & QtCore.Qt.WindowType.FramelessWindowHint)} StaysOnTop={bool(bayraklar & QtCore.Qt.WindowType.WindowStaysOnTopHint)} NoFocus={bool(bayraklar & QtCore.Qt.WindowType.WindowDoesNotAcceptFocus)} translucent={s.testAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)}")
    olgu(f"U5 odak: sekme gosterilince aktif pencere = {type(QtWidgets.QApplication.activeWindow()).__name__ if QtWidgets.QApplication.activeWindow() else None} (None beklenir: oyunun odagi calinmaz)")
    bolge = QtCore.QRect(g.right() - 260, fg.y() - 80, 261, 2 * YARICAP + 160)
    ekran_al(ekran, bolge, "kabuk_sekme_kapali.png")

    # imlec ustune: acilma suresi
    QtGui.QCursor.setPos(fg.center()); t0 = time.perf_counter()
    while not s._acik and time.perf_counter() - t0 < 2: bekle(10)
    acilma = (time.perf_counter() - t0) * 1000
    bekle(150)
    fg2 = s.frameGeometry()
    olgu(f"U3 imlec ustunde: acildi={s._acik} sure={acilma:.0f} ms (ayar 120) panel geometri=({fg2.x()},{fg2.y()},{fg2.width()},{fg2.height()}) sag kenara bitisik={fg2.right() == g.right()}")
    ekran_al(ekran, QtCore.QRect(g.right() - 260, fg2.y() - 40, 261, fg2.height() + 80), "kabuk_sekme_acik.png")

    # imlec uzaklasinca: kapanma
    QtGui.QCursor.setPos(fg2.x() - 300, fg2.center().y()); t0 = time.perf_counter()
    while s._acik and time.perf_counter() - t0 < 3: bekle(10)
    kapanma = (time.perf_counter() - t0) * 1000
    olgu(f"U3 imlec ayrilinca: kapandi={not s._acik} sure={kapanma:.0f} ms (ayar 450)")

    # surukleme siniri: en alta surukle
    QtGui.QCursor.setPos(s.frameGeometry().center())
    bekle(50)
    QTest.mousePress(s, QtCore.Qt.MouseButton.LeftButton, pos=QtCore.QPoint(YARICAP // 2, YARICAP)); bekle(30)
    QTest.mouseMove(s, QtCore.QPoint(YARICAP // 2, YARICAP + 5000)); bekle(30)
    QTest.mouseRelease(s, QtCore.QMouseButton.LeftButton if hasattr(QtCore, "QMouseButton") else QtCore.Qt.MouseButton.LeftButton, pos=QtCore.QPoint(YARICAP // 2, YARICAP)); bekle(100)
    fg3 = s.frameGeometry()
    olgu(f"U6 asagi surukleme sonrasi y={fg3.y()} alt sinir={g.bottom() - 2 * YARICAP + 1} (esit beklenir); acik={s._acik}")

    # sag tik -> ana pencere
    QtGui.QCursor.setPos(fg3.x() - 300, fg3.center().y()); bekle(600)
    QTest.mouseClick(s, QtCore.Qt.MouseButton.RightButton, pos=QtCore.QPoint(YARICAP // 2, YARICAP)); bekle(300)
    olgu(f"U4 sag tik: ana pencere gorunur={p.isVisible()} sekme gorunur={s.isVisible()}")

    # tepsiye al
    QTest.mouseClick(p._b_tepsi, QtCore.Qt.MouseButton.LeftButton); bekle(300)
    olgu(f"U1 tepsiye al: ana pencere gorunur={p.isVisible()} tepsi ikonu gorunur={p._tepsi.isVisible()} sekme gorunur={s.isVisible()}")
    p.goster(); bekle(200)
    olgu(f"U1 goster: ana pencere gorunur={p.isVisible()}")

    p.kapat()
    (CIKTI / "olgular.txt").write_text("T-012 ON OLCUM -- demo/kabuk.py, gercek ekran\n\n" + "\n".join(satirlar) + "\n", encoding="utf-8")
    print("yazildi: olgular.txt +", len(list(CIKTI.glob("kabuk_*.png"))), "png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
