"""T-012 `real_check.py` on-plan sarici (implementer delili; kapiya DOKUNMAZ).

    python .agents/tasks/T-012/evidence/real_check-on-plan-sarici.py [baska_betik.py [betik_argumanlari...]]
    (argumansiz: kapi `real_check.py`; argumanli: verilen betik ayni on-plan kosuluyla kosulur -- [5c] teshisi icin)

Neden: kapi [3] "sahne on plana alinir" on kosulu `activateWindow()` ile calisir;
Windows on plan kilidi (SetForegroundWindow kurali) yalniz ON PLANDAKI surecin
BASLATTIGI cocuga izin verir. Arka plan ajan kabugundan dogrudan baslatilan
`real_check.py`de [3] on kosulu duser (olculdu: `real_check-dogrudan-kosum.txt`).
KRT ve sef etkilesimli terminalden (on plan) baslatmisti. Bu sarici:
  1. Fare `IDLE_S` saniye hareketsiz kalana kadar bekler (kapi imleci oynatir;
     kullanici fareyi kullanirken olcum bozulur -- olculdu: [4a] imlec kaydirildi).
  2. Kucuk bir Qt penceresi acar, ona GERCEK OS tiki (mouse_event) yapar ->
     surec on plana gecer (GetForegroundWindow == bizim hwnd) ->
     `AllowSetForegroundWindow(ASFW_ANY)`.
  3. `real_check.py`yi cocuk surec olarak kosar, ciktisini aynen yazar.
  4. Kapi TEMIZ degilse (fare oynadiysa) `DENEME` kez tekrar dener.
Stdout ASCII; mutlak yol basilmaz.
"""
from __future__ import annotations

import ctypes
import os
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
REAL_CHECK = KOK / ".agents" / "tasks" / "T-012" / "real_check.py"
IDLE_S = 6.0
AZAMI_BEKLEME_S = 900.0
DENEME = 3
u32 = ctypes.windll.user32
u32.GetForegroundWindow.restype = wintypes.HWND


def imlec() -> tuple[int, int]:
    pt = wintypes.POINT()
    u32.GetCursorPos(ctypes.byref(pt))
    return (pt.x, pt.y)


def bosta_bekle() -> float:
    """Fare IDLE_S saniye hareketsiz kalana kadar bekler; beklenen toplam sureyi dondurur."""
    t0 = time.perf_counter()
    son_konum = imlec()
    son_hareket = time.perf_counter()
    while time.perf_counter() - t0 < AZAMI_BEKLEME_S:
        time.sleep(0.1)
        su = imlec()
        if su != son_konum:
            son_konum = su
            son_hareket = time.perf_counter()
        elif time.perf_counter() - son_hareket >= IDLE_S:
            return time.perf_counter() - t0
    return time.perf_counter() - t0


def on_plani_al() -> bool:
    from PySide6 import QtCore, QtGui, QtWidgets

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    w = QtWidgets.QLabel("T-012 kapi")
    w.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.WindowStaysOnTopHint)
    w.setStyleSheet("background:#333; color:#ccc; padding:6px;")
    ekran = QtGui.QGuiApplication.primaryScreen()
    g = ekran.availableGeometry()
    w.setGeometry(g.x() + 40, g.y() + 40, 90, 40)
    w.show()
    son = time.perf_counter() + 0.3
    while time.perf_counter() < son:
        app.processEvents()
        time.sleep(0.005)
    hwnd = int(w.winId())
    merkez = w.mapToGlobal(w.rect().center())
    QtGui.QCursor.setPos(merkez)
    son = time.perf_counter() + 0.1
    while time.perf_counter() < son:
        app.processEvents()
        time.sleep(0.005)
    u32.mouse_event(0x0002, 0, 0, 0, 0)
    time.sleep(0.03)
    u32.mouse_event(0x0004, 0, 0, 0, 0)
    son = time.perf_counter() + 0.3
    while time.perf_counter() < son:
        app.processEvents()
        time.sleep(0.005)
    on_planda = int(u32.GetForegroundWindow() or 0) == hwnd
    if on_planda:
        u32.AllowSetForegroundWindow(wintypes.DWORD(0xFFFFFFFF))  # ASFW_ANY
    globals()["_tut"] = (app, w)  # pencere sarici yasadikca acik kalsin (on plan surecte kalir)
    return on_planda


def main() -> int:
    sys.stdout.reconfigure(errors="replace")  # type: ignore[union-attr]
    for deneme in range(1, DENEME + 1):
        beklenen = bosta_bekle()
        on_planda = on_plani_al()
        print(f"[sarici] deneme {deneme}: fare bosta bekleme {beklenen:.1f} s; sarici on planda={on_planda}")
        sys.stdout.flush()
        betik = [str(Path(sys.argv[1]).resolve()), *sys.argv[2:]] if len(sys.argv) > 1 else [str(REAL_CHECK)]
        ortam = {**os.environ, "PYTHONIOENCODING": "utf-8"}  # cocugun boru ciktisi utf-8 (depo yolu ASCII disi; cp1254 boru cozumu U+FFFD uretiyordu)
        r = subprocess.run([sys.executable, *betik], cwd=KOK, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300, env=ortam)
        cikti = (r.stdout + r.stderr).replace(str(KOK), "<depo>")
        print(cikti)
        print(f"[sarici] real_check rc={r.returncode}")
        sys.stdout.flush()
        if r.returncode == 0:
            return 0
        hareket = imlec()
        time.sleep(0.5)
        print(f"[sarici] kapi temiz degil; fare su an hareket ediyor mu={imlec() != hareket}; yeniden denenecek")
    return 1


if __name__ == "__main__":
    os.environ.pop("QT_QPA_PLATFORM", None)
    raise SystemExit(main())
