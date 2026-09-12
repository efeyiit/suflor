"""KRT-1 / madde 4+6 -- TAZE baslangicta (tepsi hic gosterilmemis) ana pencereye WM_CLOSE (Alt+F4 / gorev cubugu 'kapat').

    python .agents/tasks/T-012/krt_kosumlari/k6_wm_close_taze.py

demo/kabuk.py closeEvent tanimlamaz; main() setQuitOnLastWindowClosed(False) der. Sonuc: surec yasar mi, kullanici
hangi yoldan ulasir? Ham cikti: k6_wm_close_taze.txt
"""
from __future__ import annotations
import ctypes, sys, time
from ctypes import wintypes
from pathlib import Path
KOK = Path(__file__).resolve().parents[4]; sys.path.insert(0, str(KOK))
from PySide6 import QtCore, QtGui, QtWidgets
from demo.kabuk import AnaPencere
from src.capture.service import CaptureService, MssBackend
CIKTI = Path(__file__).resolve().parent / "k6_wm_close_taze.txt"
u32 = ctypes.windll.user32
def main() -> int:
    app = QtWidgets.QApplication(sys.argv); app.setQuitOnLastWindowClosed(False)   # demo main() ile ayni
    g = QtGui.QGuiApplication.primaryScreen().availableGeometry()
    p = AnaPencere(CaptureService(MssBackend())); p.move(g.x() + 200, g.y() + 200); p.show()
    sat = ["KRT-1 -- taze baslangic + WM_CLOSE (demo/kabuk.py, quitOnLastWindowClosed=False)", ""]
    def kapat_gonder():
        sat.append(f"once: pencere={p.isVisible()} tepsi={p._tepsi.isVisible()} sekme={p._sekme.isVisible()}")
        u32.PostMessageW(wintypes.HWND(int(p.winId())), 0x0010, 0, 0)
    def olc():
        gorunur = [type(w).__name__ for w in QtWidgets.QApplication.topLevelWidgets() if w.isVisible()]
        sat.append(f"WM_CLOSE +700 ms: exec() hala donuyor=True pencere={p.isVisible()} tepsi={p._tepsi.isVisible()} sekme={p._sekme.isVisible()} gorunur ust-duzey={gorunur} yoklayici={p._sekme._yoklayici.isActive()}")
        sat.append(f"-> kullanicinin ulasabilecegi yol (tepsi ikonu / sekme / pencere) var mi: {p.isVisible() or p._tepsi.isVisible() or p._sekme.isVisible()}")
        CIKTI.write_text("\n".join(sat) + "\n", encoding="utf-8"); print("\n".join(sat[2:])); app.quit()
    QtCore.QTimer.singleShot(400, kapat_gonder); QtCore.QTimer.singleShot(1100, olc)
    t0 = time.perf_counter(); rc = app.exec()
    print(f"exec() {1000*(time.perf_counter()-t0):.0f} ms sonra dondu rc={rc} (1100 ms'de quit; daha erkense kendiliginden cikti)")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
