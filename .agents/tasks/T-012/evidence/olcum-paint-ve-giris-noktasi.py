"""T-012 delil olcumu: (1) offscreen paintEvent 100 kare medyani (kapali/acik, 5 tekrar);
(2) taze surecte `calistir` gercek `QApplication` kurar + `exec()` + `kapat()` -> cikis 0;
(3) taze surecte `python -m src.ui` (offscreen) ayakta kalir (baslangic hatasi yok).

    python .agents/tasks/T-012/evidence/olcum-paint-ve-giris-noktasi.py

Stdout ASCII; mutlak yol basilmaz.
"""
from __future__ import annotations

import os
import statistics
import subprocess
import sys
import time
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(KOK))


def paint_olcumu() -> None:
    from PySide6 import QtCore, QtGui, QtWidgets

    from src.ui.kenar_sekmesi import KenarSekmesi

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    ekran = QtGui.QGuiApplication.primaryScreen()
    nokta = QtCore.QPoint(0, 0)
    s = KenarSekmesi(ekran, imlec_konumu=lambda: QtCore.QPoint(nokta))
    s.show()
    for _ in range(10):
        app.processEvents()
        time.sleep(0.01)
    sayac = [0]
    orijinal = s.paintEvent

    def sayan(e: QtGui.QPaintEvent) -> None:
        sayac[0] += 1
        orijinal(e)

    s.paintEvent = sayan  # type: ignore[method-assign]

    def medyan() -> float:
        t: list[float] = []
        for _ in range(100):
            t0 = time.perf_counter()
            s.repaint()
            t.append((time.perf_counter() - t0) * 1000)
        return statistics.median(t)

    kapali = [medyan() for _ in range(5)]
    kapali_paint_sayisi = sayac[0]
    fg = s.frameGeometry()
    nokta = QtCore.QPoint(fg.right() - 3, fg.center().y())
    son = time.perf_counter() + 2
    while not s.acik and time.perf_counter() < son:
        app.processEvents()
        time.sleep(0.005)
    acik = [medyan() for _ in range(5)]
    print(f"(1) paint 100 kare medyani (offscreen, 5 tekrar) kapali={[round(x, 3) for x in kapali]} ms acik={[round(x, 3) for x in acik]} ms; acik mi={s.acik}; hepsi < 16: {max(kapali + acik) < 16}; paintEvent cagri sayisi kapali={kapali_paint_sayisi} toplam={sayac[0]} (500 + 500 beklenir: repaint gercekten ciziyor)")
    s.hide()


def giris_noktasi_taze_surec() -> None:
    kod = (
        "import time; from PySide6.QtCore import QTimer; from PySide6.QtWidgets import QApplication; "
        "from src.ui.uygulama import calistir\n"
        "def kos(app, p):\n"
        "    QTimer.singleShot(300, p.kapat); QTimer.singleShot(5000, app.quit); t0 = time.perf_counter(); rc = app.exec()\n"
        "    print('QApplication yeni kuruldu:', QApplication.instance() is app, 'quitOnLastWindowClosed:', app.quitOnLastWindowClosed(), "
        "'exec suresi ms: %.0f' % ((time.perf_counter() - t0) * 1000), 'kapandi:', p.kapandi, 'gorunur ust-duzey:', "
        "[type(w).__name__ for w in QApplication.topLevelWidgets() if w.isVisible()]); return rc\n"
        "raise SystemExit(calistir(['suflor'], calistirici=kos))\n"
    )
    ortam = dict(os.environ, QT_QPA_PLATFORM="offscreen", PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, "-c", kod], cwd=KOK, env=ortam, capture_output=True, text=True, timeout=60)
    print(f"(2) taze surec calistir(): rc={r.returncode} stdout={r.stdout.strip()!r} stderr_bos={not r.stderr.strip()}")


def modul_taze_surec() -> None:
    ortam = dict(os.environ, QT_QPA_PLATFORM="offscreen", PYTHONIOENCODING="utf-8")
    p = subprocess.Popen([sys.executable, "-m", "src.ui"], cwd=KOK, env=ortam, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    time.sleep(2.0)
    ayakta = p.poll() is None
    p.terminate()
    try:
        _, err = p.communicate(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
        _, err = p.communicate()
    print(f"(3) python -m src.ui (offscreen): 2 s sonra ayakta={ayakta} stderr_bos={not err.strip()} (sonra terminate edildi)")


if __name__ == "__main__":
    paint_olcumu()
    giris_noktasi_taze_surec()
    modul_taze_surec()
