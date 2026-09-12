"""KRT-1 / madde 4 -- GERCEK exec() dongusunde (windows platformu) davranislar; her senaryo ayri surec.

    python .agents/tasks/T-012/krt_kosumlari/k4_gercek_dongu.py            # hepsini kosar, k4_gercek_dongu.txt yazar
    python .agents/tasks/T-012/krt_kosumlari/k4_gercek_dongu.py <senaryo>  # tek senaryo (alt surec)

Senaryolar:
  A  quitOnLastWindowClosed=True (varsayilan): ana close(), ebeveynsiz Tool sekme GORUNUR -> exec() doner mi
  B  quitOnLastWindowClosed=True: ana close(), sekme gizli (gorunur durum, Alt+F4 esdegeri) -> exec() doner mi
  C  quitOnLastWindowClosed=False: ana close(), sekme gizli, tepsi gosterilmemis -> surec yasar mi (zombi)
  D  quitOnLastWindowClosed=True: ana hide() (tepsiye al) -> exec() doner mi
  E  60 ms QCursor.pos() yoklamasi bosta CPU: 5 s process_time / duvar (yoklama var / yok)
  F  windows platformunda repaint(): 26x52 katmanli sekme ve 200x132 panel, 100 kare medyan
Kilitli oturumda da kosar (pencere gorunmez ama DWM/katman yolu ayni).
"""
from __future__ import annotations

import statistics
import subprocess
import sys
import time
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

CIKTI = Path(__file__).resolve().parent / "k4_gercek_dongu.txt"
BAYRAK = (QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.Tool
          | QtCore.Qt.WindowType.WindowStaysOnTopHint | QtCore.Qt.WindowType.WindowDoesNotAcceptFocus)


def sekme_gibi(cizim: bool = False) -> QtWidgets.QWidget:
    class S(QtWidgets.QWidget):
        def paintEvent(self, e):
            if not cizim:
                return
            p = QtGui.QPainter(self); p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
            p.setPen(QtGui.QPen(QtGui.QColor("#5ec6ff"), 2)); p.setBrush(QtGui.QColor(22, 27, 33, 235))
            p.drawEllipse(QtCore.QPointF(26, 26), 24.5, 24.5); p.setPen(QtGui.QColor("#d8e2ee"))
            p.setFont(QtGui.QFont("Segoe UI", 11, QtGui.QFont.Weight.Bold))
            p.drawText(QtCore.QRect(0, 0, 26, 52), QtCore.Qt.AlignmentFlag.AlignCenter, "S"); p.end()
    w = S(None, BAYRAK)
    w.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
    w.setAttribute(QtCore.Qt.WidgetAttribute.WA_ShowWithoutActivating)
    g = QtGui.QGuiApplication.primaryScreen().availableGeometry()
    w.setGeometry(g.right() - 25, g.top() + g.height() // 2 - 26, 26, 52)
    return w


def senaryo(ad: str) -> None:
    app = QtWidgets.QApplication(sys.argv)
    g = QtGui.QGuiApplication.primaryScreen().availableGeometry()
    if ad in "ABCD":
        app.setQuitOnLastWindowClosed(ad != "C")
        ana = QtWidgets.QWidget(None, QtCore.Qt.WindowType.FramelessWindowHint); ana.resize(300, 200); ana.move(g.x() + 100, g.y() + 100)
        ana.sekme = sekme_gibi()
        ana.show()
        if ad == "A":
            ana.hide(); ana.sekme.show()
        def eylem():
            if ad == "D":
                ana.hide()
            else:
                ana.close()
            QtCore.QTimer.singleShot(700, lambda: print(f"{ad}: 700 ms sonra surec HALA YASIYOR; gorunur ust-duzey={[type(w).__name__ for w in QtWidgets.QApplication.topLevelWidgets() if w.isVisible()]} -> app.quit()") or app.quit())
        QtCore.QTimer.singleShot(300, eylem)
        t0 = time.perf_counter(); rc = app.exec()
        print(f"{ad}: exec() dondu {1000*(time.perf_counter()-t0):.0f} ms sonra (300 ms'de eylem; <=600 ise kendiliginden cikti) rc={rc}")
    elif ad == "E":
        app.setQuitOnLastWindowClosed(False)
        sonuc = {}
        def olc(yoklama: bool, sonra):
            s = sekme_gibi(True); s.show()
            sayac = [0]
            if yoklama:
                t = QtCore.QTimer(s, interval=60)
                t.timeout.connect(lambda: (sayac.__setitem__(0, sayac[0] + 1), s.frameGeometry().contains(QtGui.QCursor.pos())))
                t.start()
            c0, w0 = time.process_time(), time.perf_counter()
            def bitir():
                c1, w1 = time.process_time(), time.perf_counter()
                sonuc[yoklama] = (100 * (c1 - c0) / (w1 - w0), sayac[0], w1 - w0)
                s.close(); sonra()
            QtCore.QTimer.singleShot(5000, bitir)
        def ikinci():
            olc(False, app.quit)
        olc(True, ikinci)
        app.exec()
        for y, (cpu, n, dt) in sonuc.items():
            print(f"E: yoklama={y}: CPU %{cpu:.2f} (process_time/duvar, {dt:.1f} s) yoklama sayisi={n}")
    elif ad == "F":
        app.setQuitOnLastWindowClosed(False)
        s = sekme_gibi(True); s.show()
        def olc():
            t = []
            for _ in range(100):
                t0 = time.perf_counter(); s.repaint(); t.append((time.perf_counter() - t0) * 1000)
            print(f"F: windows platformu repaint 26x52 katmanli: medyan={statistics.median(t):.3f} ms max={max(t):.2f} ms")
            s.setGeometry(g.right() - 199, g.top() + 600, 200, 132)
            panel = QtWidgets.QFrame(s); panel.setStyleSheet("QFrame{background:#161b21;border:1px solid #2a3138;border-radius:10px;} QPushButton{background:#1e2630;color:#d8e2ee;border:1px solid #2a3138;border-radius:6px;padding:8px 12px;font:13px 'Segoe UI';}")
            d = QtWidgets.QVBoxLayout(panel); d.addWidget(QtWidgets.QLabel("Suflor")); d.addWidget(QtWidgets.QPushButton("Anlik ceviri")); d.addWidget(QtWidgets.QPushButton("Bolge izle"))
            panel.setGeometry(s.rect()); panel.show()
            QtCore.QTimer.singleShot(200, olc2)
        def olc2():
            t = []
            for _ in range(100):
                t0 = time.perf_counter(); s.repaint(); t.append((time.perf_counter() - t0) * 1000)
            print(f"F: windows platformu repaint 200x132 panel: medyan={statistics.median(t):.3f} ms max={max(t):.2f} ms")
            app.quit()
        QtCore.QTimer.singleShot(300, olc)
        app.exec()


def main() -> int:
    if len(sys.argv) > 1:
        senaryo(sys.argv[1]); return 0
    satirlar = ["KRT-1 madde 4 -- gercek exec() dongusu, windows platformu (oturum kilitli olabilir)", ""]
    for ad in "ABCDEF":
        t0 = time.perf_counter()
        try:
            r = subprocess.run([sys.executable, __file__, ad], capture_output=True, text=True, timeout=30)
            cikti = (r.stdout.strip() or "(cikti yok)") + (("\nstderr: " + r.stderr.strip()[-300:]) if r.stderr.strip() else "")
            satirlar.append(f"[{ad}] rc={r.returncode} sure={time.perf_counter()-t0:.1f}s\n{cikti}")
        except subprocess.TimeoutExpired:
            satirlar.append(f"[{ad}] ZAMAN ASIMI 30 s -> surec kendiliginden cikmadi")
        print(satirlar[-1])
    CIKTI.write_text("\n".join(satirlar) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
