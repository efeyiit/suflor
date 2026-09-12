"""T-012 kabul kapisi -- UI kabugu GERCEK ekranda (offscreen degil).

    python .agents/tasks/T-012/real_check.py

Sefe aittir. Stdout ASCII. Ekran goruntuleri temsili arka plan uzerinde (masaustu yok).
  1. tepsi var; tepsiye al -> pencere gizli, ikon var; goster -> geri
  2. kenara al -> kapali sekme ekranin sag kenarina bitisik, dikey ortada; bayraklar
  3. sekme gosterilince aktif pencere None (odak calinmaz)
  4. imlec ustune -> acilma <= acilma_ms + 2*yoklama_ms + 50; ayrilinca kapanma <= kapanma_ms + 2*yoklama_ms + 50
  5. surukleme alt sinira kilitlenir; sag tik -> pencere gorunur
  6. kapat -> gorunur ust-duzey widget 0, tepsi ikonu yok, cikis_istendi 1 kez
  7. paintEvent 100 kare medyan < 16 ms
"""
from __future__ import annotations

import statistics
import sys
import time
from pathlib import Path

KOK = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(KOK))

from PySide6 import QtCore, QtGui, QtWidgets  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402

CIKTI = Path(__file__).resolve().parent / "sef_dogrulama"
ihlaller: list[str] = []


def ihlal(m: str) -> None:
    ihlaller.append(m); print(f"  IHLAL  {m}")


def tamam(m: str) -> None:
    print(f"  ok     {m}")


def bekle(ms: int) -> None:
    son = time.perf_counter() + ms / 1000
    while time.perf_counter() < son:
        QtWidgets.QApplication.processEvents()
        time.sleep(0.004)


def main() -> int:
    print("T-012 real_check -- UI kabugu, gercek ekran")
    try:
        from src.ui.kabuk import AnaPencere, KabukDurumu
        from src.ui.kenar_sekmesi import KenarSekmesi  # noqa: F401
    except Exception as e:  # noqa: BLE001
        ihlal(f"src.ui import edilemedi: {type(e).__name__}: {e}"); return 1
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    CIKTI.mkdir(exist_ok=True)
    ekran = QtGui.QGuiApplication.primaryScreen()
    g = ekran.availableGeometry()

    sahne = QtWidgets.QLabel("oyun penceresi (temsili)")
    sahne.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.Tool)
    sahne.setStyleSheet("background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #1b2a41, stop:1 #0b1220); color:#3d5a80; font: 16px 'Segoe UI'; padding: 20px;")
    sahne.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignLeft)
    sahne.setGeometry(g.right() - 640, g.y() + 300, 641, 800)
    sahne.show(); bekle(200)

    p = AnaPencere(ekran)
    cikis = []
    p.cikis_istendi.connect(lambda: cikis.append(1))
    p.move(g.x() + 200, g.y() + 200); p.show(); bekle(300)
    p.grab().save(str(CIKTI / "kabuk_ana_pencere.png"))
    s = p.sekme
    yar = s.yaricap

    # 1 tepsi
    tepsi_var = QtWidgets.QSystemTrayIcon.isSystemTrayAvailable()
    QTest.mouseClick(p.dugme_tepsi, QtCore.Qt.MouseButton.LeftButton); bekle(300)
    (tamam if tepsi_var and not p.isVisible() and p.tepsi.gorunur() and p.durum == KabukDurumu.TEPSI else ihlal)(
        f"[1a] tepsiye al: tepsi var={tepsi_var} pencere gizli={not p.isVisible()} ikon={p.tepsi.gorunur()} durum={p.durum}")
    p.goster(); bekle(200)
    (tamam if p.isVisible() and p.durum == KabukDurumu.GORUNUR else ihlal)(f"[1b] goster: gorunur={p.isVisible()} durum={p.durum}")

    # 2 kenara al
    QTest.mouseClick(p.dugme_kenar, QtCore.Qt.MouseButton.LeftButton); bekle(300)
    fg = s.frameGeometry()
    bitisik = fg.right() == g.right() and fg.width() == yar and fg.height() == 2 * yar
    orta = abs(fg.center().y() - g.center().y()) <= 1
    (tamam if not p.isVisible() and s.isVisible() and bitisik and orta and p.durum == KabukDurumu.KENAR else ihlal)(
        f"[2a] kenara al: pencere gizli={not p.isVisible()} sekme={s.isVisible()} bitisik={bitisik} dikey orta={orta} geo=({fg.x()},{fg.y()},{fg.width()},{fg.height()}) durum={p.durum}")
    b = s.windowFlags()
    bayrak = all([bool(b & QtCore.Qt.WindowType.Tool), bool(b & QtCore.Qt.WindowType.FramelessWindowHint),
                  bool(b & QtCore.Qt.WindowType.WindowStaysOnTopHint), bool(b & QtCore.Qt.WindowType.WindowDoesNotAcceptFocus),
                  s.testAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground), s.testAttribute(QtCore.Qt.WidgetAttribute.WA_ShowWithoutActivating)])
    (tamam if bayrak else ihlal)(f"[2b] sekme bayraklari Tool/Frameless/StaysOnTop/NoFocus/translucent/ShowWithoutActivating hepsi={bayrak}")
    (tamam if p.tepsi.gorunur() else ihlal)(f"[2c] kenar durumunda tepsi ikonu da var={p.tepsi.gorunur()} (geri donus yolu)")
    ekran.grabWindow(0, g.right() - 260, fg.y() - 80, 261, 2 * yar + 160).save(str(CIKTI / "kabuk_sekme_kapali.png"))

    # 3 odak
    aktif = QtWidgets.QApplication.activeWindow()
    (tamam if aktif is None else ihlal)(f"[3] sekme gosterilince aktif pencere = {type(aktif).__name__ if aktif else None} (None beklenir)")

    # 4 zamanlama
    ust = s.acilma_ms + 2 * s.yoklama_ms + 50
    QtGui.QCursor.setPos(fg.center()); t0 = time.perf_counter()
    while not s.acik and time.perf_counter() - t0 < 3: bekle(5)
    acilma = (time.perf_counter() - t0) * 1000
    bekle(150)
    fg2 = s.frameGeometry()
    (tamam if s.acik and acilma <= ust and fg2.right() == g.right() and g.contains(fg2) else ihlal)(
        f"[4a] acilma: acik={s.acik} {acilma:.0f} ms (<= {ust}) panel bitisik={fg2.right() == g.right()} ekran icinde={g.contains(fg2)}")
    ekran.grabWindow(0, g.right() - 260, fg2.y() - 40, 261, fg2.height() + 80).save(str(CIKTI / "kabuk_sekme_acik.png"))
    ust_k = s.kapanma_ms + 2 * s.yoklama_ms + 50
    QtGui.QCursor.setPos(fg2.x() - 300, fg2.center().y()); t0 = time.perf_counter()
    while s.acik and time.perf_counter() - t0 < 4: bekle(5)
    kapanma = (time.perf_counter() - t0) * 1000
    (tamam if not s.acik and kapanma <= ust_k else ihlal)(f"[4b] kapanma: kapandi={not s.acik} {kapanma:.0f} ms (<= {ust_k})")

    # 5 surukleme siniri + sag tik
    QtGui.QCursor.setPos(fg2.x() - 300, fg2.center().y()); bekle(100)
    fg3 = s.frameGeometry()
    QTest.mousePress(s, QtCore.Qt.MouseButton.LeftButton, pos=QtCore.QPoint(yar // 2, yar)); bekle(30)
    QTest.mouseMove(s, QtCore.QPoint(yar // 2, yar + 5000)); bekle(30)
    QTest.mouseRelease(s, QtCore.Qt.MouseButton.LeftButton, pos=QtCore.QPoint(yar // 2, yar)); bekle(100)
    alt_sinir = g.bottom() - 2 * yar + 1
    (tamam if s.y == alt_sinir else ihlal)(f"[5a] asagi surukleme: y={s.y} alt sinir={alt_sinir}")
    QtGui.QCursor.setPos(fg3.x() - 300, fg3.center().y()); bekle(700)
    QTest.mouseClick(s, QtCore.Qt.MouseButton.RightButton, pos=QtCore.QPoint(yar // 2, yar)); bekle(300)
    (tamam if p.isVisible() and not s.isVisible() and p.durum == KabukDurumu.GORUNUR else ihlal)(f"[5b] sag tik: pencere={p.isVisible()} sekme={s.isVisible()} durum={p.durum}")

    # 7 paint suresi
    p.kenara_al(); bekle(200)
    t = []
    for _ in range(100):
        t0 = time.perf_counter(); s.repaint(); t.append((time.perf_counter() - t0) * 1000)
    (tamam if statistics.median(t) < 16 else ihlal)(f"[7] paintEvent 100 kare medyan {statistics.median(t):.2f} ms (< 16)")

    # 6 kapat
    QTest.mouseClick(p.dugme_kapat, QtCore.Qt.MouseButton.LeftButton) if p.isVisible() else p.kapat()
    bekle(300)
    gorunur = [w for w in QtWidgets.QApplication.topLevelWidgets() if w.isVisible() and w is not sahne]
    (tamam if not gorunur and not p.tepsi.gorunur() and len(cikis) == 1 else ihlal)(
        f"[6] kapat: gorunur ust-duzey={len(gorunur)} tepsi ikonu={p.tepsi.gorunur()} cikis_istendi={len(cikis)}")
    sahne.close()
    print()
    if ihlaller: print(f"REAL_CHECK: {len(ihlaller)} IHLAL"); return 1
    print("REAL_CHECK: TEMIZ"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
