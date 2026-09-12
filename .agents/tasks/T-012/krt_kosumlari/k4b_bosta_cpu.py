"""KRT-1 / madde 4 (devam) -- 60 ms QCursor.pos() yoklamasinin BOSTA CPU'su, isinma sonrasi, windows platformu.

    python .agents/tasks/T-012/krt_kosumlari/k4b_bosta_cpu.py

k4 E'de ilk 5 s pencere kurulumunu iceriyordu (yoklama=True %2.18 vs E2 %0.31 tutarsiz). Burada: sekme gosterilir,
1 s isinma, sonra 5 s olcum; yoklama 60 / 30 / yok; process_time/duvar ve yoklama basina CPU. exec() dongusu.
Ham cikti: k4b_bosta_cpu.txt
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

CIKTI = Path(__file__).resolve().parent / "k4b_bosta_cpu.txt"
BAYRAK = (QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.Tool
          | QtCore.Qt.WindowType.WindowStaysOnTopHint | QtCore.Qt.WindowType.WindowDoesNotAcceptFocus)


class S(QtWidgets.QWidget):
    def paintEvent(self, e):
        p = QtGui.QPainter(self); p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        p.setPen(QtGui.QPen(QtGui.QColor("#5ec6ff"), 2)); p.setBrush(QtGui.QColor(22, 27, 33, 235))
        p.drawEllipse(QtCore.QPointF(26, 26), 24.5, 24.5); p.end()


def main() -> int:
    app = QtWidgets.QApplication(sys.argv); app.setQuitOnLastWindowClosed(False)
    g = QtGui.QGuiApplication.primaryScreen().availableGeometry()
    s = S(None, BAYRAK); s.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground); s.setAttribute(QtCore.Qt.WidgetAttribute.WA_ShowWithoutActivating)
    s.setGeometry(g.right() - 25, g.top() + g.height() // 2 - 26, 26, 52); s.show()
    satirlar = ["KRT-1 madde 4 (devam) -- bosta CPU, isinma sonrasi 5 s, windows platformu", ""]
    planlar = [60, 30, 0]; sonuc = {}

    def kos(i: int):
        if i >= len(planlar):
            for ms, (cpu, n) in sonuc.items():
                satirlar.append(f"yoklama={ms or 'yok'} ms: CPU %{cpu:.2f} (process_time/duvar, 5 s) yoklama sayisi={n} CPU/yoklama={(cpu/100*5000/n) if n else 0:.3f} ms")
            CIKTI.write_text("\n".join(satirlar) + "\n", encoding="utf-8"); print("\n".join(satirlar[2:])); app.quit(); return
        ms = planlar[i]; sayac = [0]; t = None
        if ms:
            t = QtCore.QTimer(s, interval=ms)
            t.timeout.connect(lambda: (sayac.__setitem__(0, sayac[0] + 1), s.frameGeometry().contains(QtGui.QCursor.pos())))
            t.start()
        durum = {}

        def basla():
            durum["c0"], durum["w0"] = time.process_time(), time.perf_counter(); sayac[0] = 0
            QtCore.QTimer.singleShot(5000, bitir)

        def bitir():
            c1, w1 = time.process_time(), time.perf_counter()
            sonuc[ms] = (100 * (c1 - durum["c0"]) / (w1 - durum["w0"]), sayac[0])
            if t: t.stop(); t.deleteLater()
            QtCore.QTimer.singleShot(200, lambda: kos(i + 1))
        QtCore.QTimer.singleShot(1000, basla)   # isinma
    QtCore.QTimer.singleShot(300, lambda: kos(0))
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
