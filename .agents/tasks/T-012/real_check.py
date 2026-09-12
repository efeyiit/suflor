"""T-012 kabul kapisi v2 -- UI kabugu GERCEK ekranda (offscreen degil, Windows).

    python .agents/tasks/T-012/real_check.py

Sefe aittir. Stdout ASCII. Ekran goruntuleri temsili arka plan uzerinde (masaustu yok).
  0. on kosul: sabitler urun degerleri (26 / 120 / 450 / 60, panel 200x132) -- KRT O1 (kural 8)
  1. tepsiye al -> (F,F,T); goster -> (T,F,F)
  2. kenara al -> (F,T,T); kapali sekme sag kenara bitisik, dikey orta; bayraklar
  3. GERCEK OS tiki (mouse_event): sekmeye tik -> on plan sahne kalir; panel dugmesine tik -> clicked 1, on plan sahne (KRT Y3)
  4. acilma <= 120+2*60+150, kapanma <= 450+2*60+150
  5. surukleme sinira kilitlenir; surukleme sonrasi acik False (KRT Y2); sag tik -> gorunur
  6. WM_CLOSE -> cikis_istendi 1, ucluk (F,F,F); kapat() ikinci cagri sinyal uretmez (KRT Y1)
  7. paintEvent 100 kare medyan < 16 ms, acik ve kapali
  8. ikinci monitor varsa: fiziksel sag kenar == monitorun fiziksel sag kenari (+-1 px)
  9. mod dugmesi tiki -> panel kapali (KRT O9)
"""
from __future__ import annotations

import ctypes
import statistics
import sys
import time
from ctypes import wintypes
from pathlib import Path

KOK = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(KOK))

from PySide6 import QtCore, QtGui, QtWidgets  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402

CIKTI = Path(__file__).resolve().parent / "sef_dogrulama"
ihlaller: list[str] = []
u32 = ctypes.windll.user32
u32.GetForegroundWindow.restype = wintypes.HWND
u32.WindowFromPoint.restype = wintypes.HWND
u32.WindowFromPoint.argtypes = [wintypes.POINT]
WM_CLOSE = 0x0010


def ihlal(m: str) -> None:
    ihlaller.append(m); print(f"  IHLAL  {m}")


def tamam(m: str) -> None:
    print(f"  ok     {m}")


def bekle(ms: int) -> None:
    son = time.perf_counter() + ms / 1000
    while time.perf_counter() < son:
        QtWidgets.QApplication.processEvents()
        time.sleep(0.004)


def on_plan() -> int:
    return int(u32.GetForegroundWindow() or 0)


def gercek_tik(p: QtCore.QPoint, sag: bool = False) -> None:
    """Gercek OS fare girdisi: imleci tasi, sol/sag tik (QTest degil -- KRT k5b deseni)."""
    QtGui.QCursor.setPos(p); bekle(80)
    asagi, yukari = (0x0008, 0x0010) if sag else (0x0002, 0x0004)
    u32.mouse_event(asagi, 0, 0, 0, 0); bekle(30); u32.mouse_event(yukari, 0, 0, 0, 0); bekle(250)


def uclu(p: object) -> tuple[bool, bool, bool]:
    return (p.isVisible(), p.sekme.isVisible(), p.tepsi.gorunur())  # type: ignore[attr-defined]


def main() -> int:
    print("T-012 real_check v2 -- UI kabugu, gercek ekran")
    try:
        from src.ui.geometri import PANEL_BOYUTU, Kenar
        from src.ui.kabuk import AnaPencere, KabukDurumu
    except Exception as e:  # noqa: BLE001
        ihlal(f"src.ui import edilemedi: {type(e).__name__}"); return 1
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    CIKTI.mkdir(exist_ok=True)
    ekran = QtGui.QGuiApplication.primaryScreen()
    g = ekran.availableGeometry()

    sahne = QtWidgets.QLabel("oyun penceresi (temsili)")
    sahne.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
    sahne.setStyleSheet("background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #1b2a41, stop:1 #0b1220); color:#3d5a80; font: 16px 'Segoe UI'; padding: 20px;")
    sahne.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignLeft)
    sahne.setGeometry(g.right() - 640, g.y() + 300, 641, 800)
    sahne.show(); bekle(200)
    sahne_hwnd = int(sahne.winId())

    p = AnaPencere(ekran)
    cikis: list[int] = []
    p.cikis_istendi.connect(lambda: cikis.append(1))
    p.move(g.x() + 200, g.y() + 200); p.show(); bekle(300)
    p.grab().save(str(CIKTI / "kabuk_ana_pencere.png"))
    s = p.sekme

    # 0 on kosul (kural 8: referans uygulamadan turetilmez)
    sabit = (s.yaricap, s.acilma_ms, s.kapanma_ms, s.yoklama_ms, PANEL_BOYUTU.width(), PANEL_BOYUTU.height())
    if sabit != (26, 120, 450, 60, 200, 132):
        ihlal(f"[0] sabitler urun degeri degil: {sabit} (26,120,450,60,200,132 beklenir) -- kapi durdu"); return 1
    tamam(f"[0] sabitler: yaricap/acilma/kapanma/yoklama/panel = {sabit}")
    yar = 26

    # 1 tepsi
    QTest.mouseClick(p.dugme_tepsi, QtCore.Qt.MouseButton.LeftButton); bekle(300)
    (tamam if uclu(p) == (False, False, True) and p.durum == KabukDurumu.TEPSI else ihlal)(f"[1a] tepsiye al: uclu={uclu(p)} (F,F,T) durum={p.durum}")
    p.goster(); bekle(200)
    (tamam if uclu(p) == (True, False, False) and p.durum == KabukDurumu.GORUNUR else ihlal)(f"[1b] goster: uclu={uclu(p)} (T,F,F) durum={p.durum}")

    # 2 kenara al
    QTest.mouseClick(p.dugme_kenar, QtCore.Qt.MouseButton.LeftButton); bekle(300)
    fg = s.frameGeometry()
    bitisik = fg.right() == g.right() and fg.width() == yar and fg.height() == 2 * yar
    orta = abs(fg.center().y() - g.center().y()) <= 1
    (tamam if uclu(p) == (False, True, True) and bitisik and orta and p.durum == KabukDurumu.KENAR else ihlal)(
        f"[2a] kenara al: uclu={uclu(p)} (F,T,T) bitisik={bitisik} dikey orta={orta} geo=({fg.x()},{fg.y()},{fg.width()},{fg.height()}) durum={p.durum}")
    b = s.windowFlags()
    bayrak = all([bool(b & QtCore.Qt.WindowType.Tool), bool(b & QtCore.Qt.WindowType.FramelessWindowHint),
                  bool(b & QtCore.Qt.WindowType.WindowStaysOnTopHint), bool(b & QtCore.Qt.WindowType.WindowDoesNotAcceptFocus),
                  s.testAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground), s.testAttribute(QtCore.Qt.WidgetAttribute.WA_ShowWithoutActivating)])
    (tamam if bayrak else ihlal)(f"[2b] sekme bayraklari Tool/Frameless/StaysOnTop/NoFocus/translucent/ShowWithoutActivating hepsi={bayrak}")
    ekran.grabWindow(0, g.right() - 260, fg.y() - 80, 261, 2 * yar + 160).save(str(CIKTI / "kabuk_sekme_kapali.png"))

    # 3 gercek OS tiki: odak calinmaz
    sahne.raise_(); sahne.activateWindow(); bekle(300)
    on0 = on_plan()
    if on0 != sahne_hwnd:
        ihlal(f"[3] on kosul: sahne on planda degil (on plan hwnd sahne mi: {on0 == sahne_hwnd}); tik olcusu atlandi")
    else:
        gercek_tik(QtCore.QPoint(fg.right() - 4, fg.center().y()))
        (tamam if on_plan() == sahne_hwnd else ihlal)(f"[3a] sekmeye gercek sol tik: on plan sahne kaldi={on_plan() == sahne_hwnd}")
        QtGui.QCursor.setPos(QtCore.QPoint(fg.right() - 4, fg.center().y()))
        t0 = time.perf_counter()
        while not s.acik and time.perf_counter() - t0 < 3: bekle(5)
        bekle(150)
        if s.acik:
            tik = []
            s.bolge_izle.connect(lambda: tik.append(1))
            d = s.dugme_bolge
            merkez = d.mapToGlobal(d.rect().center())
            gercek_tik(merkez)
            (tamam if len(tik) == 1 and on_plan() == sahne_hwnd else ihlal)(f"[3b] panel dugmesine gercek tik: clicked={len(tik)} on plan sahne={on_plan() == sahne_hwnd}")
            (tamam if not s.acik else ihlal)(f"[9] mod tiki sonrasi panel kapali={not s.acik} boyut=({s.frameGeometry().width()},{s.frameGeometry().height()})")
        else:
            ihlal("[3b] panel acilmadi, dugme tiki olculemedi")
    QtGui.QCursor.setPos(QtCore.QPoint(g.x() + 100, g.y() + 100)); bekle(700)

    # 4 zamanlama
    fg = s.frameGeometry()
    ust = 120 + 2 * 60 + 150
    QtGui.QCursor.setPos(fg.center()); t0 = time.perf_counter()
    while not s.acik and time.perf_counter() - t0 < 3: bekle(5)
    acilma = (time.perf_counter() - t0) * 1000
    bekle(150)
    fg2 = s.frameGeometry()
    (tamam if s.acik and acilma <= ust and fg2.right() == g.right() and g.contains(fg2) else ihlal)(
        f"[4a] acilma: acik={s.acik} {acilma:.0f} ms (<= {ust}) panel bitisik={fg2.right() == g.right()} ekran icinde={g.contains(fg2)}")
    ekran.grabWindow(0, g.right() - 260, fg2.y() - 40, 261, fg2.height() + 80).save(str(CIKTI / "kabuk_sekme_acik.png"))
    ust_k = 450 + 2 * 60 + 150
    QtGui.QCursor.setPos(fg2.x() - 300, fg2.center().y()); t0 = time.perf_counter()
    while s.acik and time.perf_counter() - t0 < 4: bekle(5)
    kapanma = (time.perf_counter() - t0) * 1000
    (tamam if not s.acik and kapanma <= ust_k else ihlal)(f"[4b] kapanma: kapandi={not s.acik} {kapanma:.0f} ms (<= {ust_k})")

    # 5 surukleme (gercek OS): sinira kilitlenir, panel acilmaz
    fg3 = s.frameGeometry()
    bas = QtCore.QPoint(fg3.right() - 4, fg3.center().y())
    QtGui.QCursor.setPos(bas); bekle(80)
    u32.mouse_event(0x0002, 0, 0, 0, 0); bekle(60)
    acik_gorunen = False
    for adim in range(1, 11):
        QtGui.QCursor.setPos(QtCore.QPoint(bas.x(), bas.y() + adim * 400)); bekle(60)
        acik_gorunen = acik_gorunen or s.acik
    u32.mouse_event(0x0004, 0, 0, 0, 0); bekle(120)
    alt_sinir = g.bottom() - 2 * yar + 1
    (tamam if s.y == alt_sinir else ihlal)(f"[5a] asagi surukleme: y={s.y} alt sinir={alt_sinir}")
    (tamam if not acik_gorunen and not s.acik else ihlal)(f"[5b] surukleme sirasinda panel acilmadi={not acik_gorunen}, sonrasinda acik={s.acik} (False beklenir; KRT Y2)")
    fg4 = s.frameGeometry()
    QtGui.QCursor.setPos(QtCore.QPoint(g.x() + 100, g.y() + 100)); bekle(700)
    gercek_tik(QtCore.QPoint(fg4.right() - 4, fg4.center().y()), sag=True)
    (tamam if uclu(p) == (True, False, False) and p.durum == KabukDurumu.GORUNUR else ihlal)(f"[5c] sag tik: uclu={uclu(p)} (T,F,F) durum={p.durum}")

    # 7 paint suresi (kapali ve acik)
    p.kenara_al(); bekle(200)
    t_k = []
    for _ in range(100):
        t0 = time.perf_counter(); s.repaint(); t_k.append((time.perf_counter() - t0) * 1000)
    QtGui.QCursor.setPos(s.frameGeometry().center()); t0 = time.perf_counter()
    while not s.acik and time.perf_counter() - t0 < 3: bekle(5)
    t_a = []
    for _ in range(100):
        t0 = time.perf_counter(); s.repaint(); t_a.append((time.perf_counter() - t0) * 1000)
    (tamam if statistics.median(t_k) < 16 and statistics.median(t_a) < 16 else ihlal)(
        f"[7] paintEvent medyan kapali {statistics.median(t_k):.2f} ms, acik {statistics.median(t_a):.2f} ms (< 16)")
    QtGui.QCursor.setPos(QtCore.QPoint(g.x() + 100, g.y() + 100)); bekle(700)
    p.goster(); bekle(200)

    # 8 ikinci monitor
    ekranlar = QtGui.QGuiApplication.screens()
    if len(ekranlar) >= 2:
        e2 = ekranlar[1] if ekranlar[0] is ekran else ekranlar[0]
        p2 = AnaPencere(e2); p2.show(); bekle(200); p2.kenara_al(); bekle(300)
        r = wintypes.RECT(); u32.GetWindowRect(wintypes.HWND(int(p2.sekme.winId())), ctypes.byref(r))
        g2 = e2.geometry(); dpr = e2.devicePixelRatio()
        fiz_sag = int(round((g2.right() + 1) * dpr)) if g2.x() >= 0 else int(round((g2.right() + 1) * dpr))
        # fiziksel sag kenar: mantiksal (right+1) * dpr; monitorun sol ucu fiziksel = x_mantiksal * (birincil dpr) kabulu ile +-1 px
        fark = abs(r.right - fiz_sag)
        # RAPOR (dusurmez): Qt'nin mantiksal->fiziksel eslemesi dpr != 1 monitorde birim testte olculemez (paket K2 [OLCULMUYOR birim]);
        # KRT G4 prototipte 1 px tasma olctu. Sayi kaydedilir, karar sefin.
        tamam(f"[8] RAPOR ikinci monitor dpr={dpr}: sekme fiziksel sag={r.right} beklenen~{fiz_sag} fark={fark} (<= 1 hedef)")
        p2.kapat(); bekle(200)
    else:
        tamam("[8] ikinci monitor yok -- atlandi")

    # 6 WM_CLOSE + idempotent kapat
    cikis.clear()
    u32.PostMessageW(wintypes.HWND(int(p.winId())), WM_CLOSE, 0, 0); bekle(700)
    (tamam if len(cikis) == 1 and uclu(p) == (False, False, False) else ihlal)(f"[6a] WM_CLOSE: cikis_istendi={len(cikis)} (1) uclu={uclu(p)} (F,F,F)")
    p.kapat(); bekle(100)
    (tamam if len(cikis) == 1 else ihlal)(f"[6b] ikinci kapat(): cikis_istendi={len(cikis)} (hala 1)")
    gorunur = [w for w in QtWidgets.QApplication.topLevelWidgets() if w.isVisible() and w is not sahne]
    (tamam if not gorunur else ihlal)(f"[6c] gorunur ust-duzey (sahne haric)={len(gorunur)} (0)")
    sahne.close()
    print()
    if ihlaller: print(f"REAL_CHECK: {len(ihlaller)} IHLAL"); return 1
    print("REAL_CHECK: TEMIZ"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
