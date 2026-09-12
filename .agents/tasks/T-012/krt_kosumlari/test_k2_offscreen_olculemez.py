"""KRT-1 / madde 2, 4, 6, 7 -- offscreen'de neler olculemez, kapi neyi ateşleyemez.

    QT_QPA_PLATFORM=offscreen python -m pytest .agents/tasks/T-012/krt_kosumlari/test_k2_offscreen_olculemez.py -q -rA -p no:cacheprovider

Her test OLGU basar (assert cogu zaman `True` -- amac olcum, kabul degil). Ham cikti: k2_offscreen.txt
"""
from __future__ import annotations

import gc
import os
import statistics
import threading
import time
from typing import Callable

import pytest
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtTest import QTest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

SEKME_BAYRAK = (QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.Tool
                | QtCore.Qt.WindowType.WindowStaysOnTopHint | QtCore.Qt.WindowType.WindowDoesNotAcceptFocus)


def olgu(m: str) -> None:
    print("OLGU " + m)


def sekme_gibi(bayrak=SEKME_BAYRAK, translucent=True, show_without_activating=True) -> QtWidgets.QWidget:
    w = QtWidgets.QWidget(None, bayrak)
    if translucent:
        w.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
    if show_without_activating:
        w.setAttribute(QtCore.Qt.WidgetAttribute.WA_ShowWithoutActivating)
    w.setGeometry(2534, 670, 26, 52)
    return w


# ---------------------------------------------------------------- madde 2: offscreen'de hep gecenler
def test_o1_platform_ve_tepsi(qapp):
    olgu(f"platform={qapp.platformName()} isSystemTrayAvailable={QtWidgets.QSystemTrayIcon.isSystemTrayAvailable()} supportsMessages={QtWidgets.QSystemTrayIcon.supportsMessages()}")
    ekranlar = QtGui.QGuiApplication.screens()
    olgu(f"ekran sayisi={len(ekranlar)} birincil avail={tuple(ekranlar[0].availableGeometry().getRect())} dpr={ekranlar[0].devicePixelRatio()}")


@pytest.mark.parametrize("ad,bayrak,swa", [
    ("tam-sekme (NoFocus+SWA)", SEKME_BAYRAK, True),
    ("NoFocus yok, SWA var", SEKME_BAYRAK & ~QtCore.Qt.WindowType.WindowDoesNotAcceptFocus, True),
    ("NoFocus var, SWA yok", SEKME_BAYRAK, False),
    ("ikisi de yok (odak calan varyant)", SEKME_BAYRAK & ~QtCore.Qt.WindowType.WindowDoesNotAcceptFocus, False),
    ("duz QWidget (Tool degil, hicbir sey yok)", QtCore.Qt.WindowType.Widget, False),
])
def test_o2_activeWindow_offscreen(qtbot, ad, bayrak, swa):
    """K3 OLCU: 'show() sonrasi QApplication.activeWindow() degismez (offscreen'de None kalir)'.
    Ates edebilmesi icin odak CALAN bir varyantta None olmamasi gerekir."""
    w = sekme_gibi(bayrak, True, swa); qtbot.addWidget(w)
    onceki = QtWidgets.QApplication.activeWindow()
    w.show(); qtbot.wait(50)
    sonra = QtWidgets.QApplication.activeWindow()
    olgu(f"activeWindow [{ad}]: once={onceki} sonra={type(sonra).__name__ if sonra else None} isActiveWindow={w.isActiveWindow()}")
    w.hide()


def test_o2b_activeWindow_pozitif_kontrol_activateWindow(qtbot):
    """Offscreen'de activateWindow() ile odak alinabiliyor mu (yani platform odak destekliyor mu)."""
    w = QtWidgets.QWidget(); qtbot.addWidget(w); w.show(); w.activateWindow(); qtbot.wait(50)
    olgu(f"duz widget show()+activateWindow(): activeWindow={type(QtWidgets.QApplication.activeWindow()).__name__ if QtWidgets.QApplication.activeWindow() else None}")
    s = sekme_gibi(); qtbot.addWidget(s); s.show(); s.activateWindow(); qtbot.wait(50)
    a = QtWidgets.QApplication.activeWindow()
    olgu(f"sekme(NoFocus) show()+activateWindow(): activeWindow={type(a).__name__ if a else None} (sekme mi={a is s})")


def test_o3_bayraklar_platformdan_bagimsiz(qtbot):
    """K3 bayrak testi: windowFlags() yalnizca saklanan degeri dondurur; offscreen/gercek fark etmez."""
    w = sekme_gibi(); qtbot.addWidget(w); w.show(); qtbot.wait(20)
    b = w.windowFlags()
    olgu(f"bayraklar show() sonrasi: Tool={bool(b & QtCore.Qt.WindowType.Tool)} StaysOnTop={bool(b & QtCore.Qt.WindowType.WindowStaysOnTopHint)} NoFocus={bool(b & QtCore.Qt.WindowType.WindowDoesNotAcceptFocus)} translucent={w.testAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)} -> bu test yalnizca 'bayrak set edildi mi' der, ustte kalma DAVRANISINI olcmez")


def test_o4_QCursor_offscreen(qtbot):
    """Offscreen'de QCursor.setPos/pos calisiyor mu? Calisiyorsa 'imlec_konumu' enjeksiyonu olmadan da test yazilir
    ve enjeksiyonu atlayan (dogrudan QCursor.pos okuyan) uygulama testlerde ayrismaz."""
    QtGui.QCursor.setPos(2547, 696); qtbot.wait(20)
    p = QtGui.QCursor.pos()
    olgu(f"QCursor.setPos(2547,696) -> pos=({p.x()},{p.y()}) calisiyor={p == QtCore.QPoint(2547, 696)}")
    QtGui.QCursor.setPos(-100, -100); qtbot.wait(20); p2 = QtGui.QCursor.pos()
    olgu(f"QCursor.setPos(-100,-100) (ekran disi) -> pos=({p2.x()},{p2.y()})")


# ---------------------------------------------------------------- madde 4: quitOnLastWindowClosed / omur
def test_o5_quitOnLastWindowClosed_ve_hide_close(qtbot, qapp):
    sayac = []
    qapp.lastWindowClosed.connect(lambda: sayac.append(1))
    olgu(f"pytest-qt qapp.quitOnLastWindowClosed varsayilan={qapp.quitOnLastWindowClosed()}")
    ana = QtWidgets.QWidget(None, QtCore.Qt.WindowType.FramelessWindowHint); qtbot.addWidget(ana)
    s = sekme_gibi(); qtbot.addWidget(s)
    ana.show(); s.show(); qtbot.wait(20)
    ana.hide(); qtbot.wait(20)
    olgu(f"ana.hide() (tepsiye al gibi): lastWindowClosed={len(sayac)}")
    s.hide(); qtbot.wait(20)
    olgu(f"sekme.hide(): lastWindowClosed={len(sayac)}")
    ana.show(); s.show(); qtbot.wait(20)
    ana.close(); qtbot.wait(20)
    olgu(f"ana.close() (sekme hala gorunur, ebeveynsiz Tool): lastWindowClosed={len(sayac)}")
    s.close(); qtbot.wait(20)
    olgu(f"sekme.close(): lastWindowClosed={len(sayac)} -> ebeveynsiz Tool pencere 'son pencere' sayiliyor mu: {len(sayac) == 1}")
    # nested loop hala calisiyor mu (quit() etkisi)?
    t0 = time.perf_counter(); qtbot.wait(100); dt = (time.perf_counter() - t0) * 1000
    olgu(f"close sonrasi qtbot.wait(100) gercek sure={dt:.0f} ms (100'un altindaysa quit() ic dongüyü kirdi)")
    qapp.lastWindowClosed.disconnect()


def test_o6_ebeveynsiz_sekme_omru(qtbot):
    """AnaPencere silinince ebeveynsiz KenarSekmesi + yoklama QTimer'i yasamaya devam eder mi."""
    tik = []

    class Ana(QtWidgets.QWidget):
        def __init__(self):
            super().__init__(None, QtCore.Qt.WindowType.FramelessWindowHint)
            self.sekme = sekme_gibi()                     # ebeveynsiz (demo ile ayni)
            self.yok = QtCore.QTimer(self.sekme, interval=10)
            self.yok.timeout.connect(lambda: tik.append(1))
            self.yok.start()
    a = Ana(); a.show(); a.sekme.show(); qtbot.wait(50)
    n_once = len([w for w in QtWidgets.QApplication.topLevelWidgets() if w.isVisible()])
    a.close(); a.deleteLater(); del a; qtbot.wait(50); gc.collect(); qtbot.wait(50)
    ustler = [type(w).__name__ for w in QtWidgets.QApplication.topLevelWidgets() if w.isVisible()]
    n1 = len(tik); qtbot.wait(100); n2 = len(tik)
    olgu(f"Ana close+deleteLater+del+gc: once gorunur={n_once} sonra gorunur ust-duzey={ustler} yoklayici hala atiyor={n2 > n1} ({n2 - n1} tik/100ms)")
    for w in QtWidgets.QApplication.topLevelWidgets():
        w.close(); w.deleteLater()
    qtbot.wait(20)


def test_o6b_ebeveynli_sekme_omru(qtbot):
    """Ayni kurulum, sekme ebeveyni AnaPencere (Qt cocuk pencere) -> ebeveyn silinince silinir mi; bayraklar korunur mu."""
    tik = []
    ana = QtWidgets.QWidget(None, QtCore.Qt.WindowType.FramelessWindowHint)
    s = QtWidgets.QWidget(ana, SEKME_BAYRAK)
    s.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground); s.setGeometry(2534, 670, 26, 52)
    t = QtCore.QTimer(s, interval=10); t.timeout.connect(lambda: tik.append(1)); t.start()
    ana.show(); s.show(); qtbot.wait(50)
    olgu(f"ebeveynli sekme: isWindow={s.isWindow()} gorunur={s.isVisible()} geometri={tuple(s.frameGeometry().getRect())} Tool={bool(s.windowFlags() & QtCore.Qt.WindowType.Tool)}")
    ana.hide(); qtbot.wait(20)
    olgu(f"ana.hide() -> ebeveynli sekme gorunur={s.isVisible()} (kenara al: ana gizli, sekme gorunur OLMALI)")
    ana.close(); ana.deleteLater(); qtbot.wait(50); gc.collect(); qtbot.wait(50)
    n1 = len(tik); qtbot.wait(100); n2 = len(tik)
    olgu(f"ana silindi -> yoklayici atiyor={n2 > n1} gorunur ust-duzey={[type(w).__name__ for w in QtWidgets.QApplication.topLevelWidgets() if w.isVisible()]}")


# ---------------------------------------------------------------- madde 6: kapi kontrolleri
def test_o7_QTest_mouseMove_dugme_durumu(qtbot):
    """real_check [5a]: QTest.mouseMove mouseMoveEvent'i gercekten tetikliyor mu (dugme basiliyken / degilken)."""
    olaylar = []

    class W(QtWidgets.QWidget):
        def mouseMoveEvent(self, e):
            olaylar.append((int(e.position().y()), int(e.globalPosition().y()), int(e.buttons().value)))
    w = W(None, SEKME_BAYRAK); w.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
    w.setGeometry(2534, 670, 26, 52); qtbot.addWidget(w); w.show(); qtbot.wait(20)
    QTest.mouseMove(w, QtCore.QPoint(13, 26 + 5000)); qtbot.wait(20)
    olgu(f"mouseMove DUGME BASILI DEGIL (mouseTracking={w.hasMouseTracking()}): mouseMoveEvent sayisi={len(olaylar)} QCursor.pos=({QtGui.QCursor.pos().x()},{QtGui.QCursor.pos().y()})")
    olaylar.clear()
    QTest.mousePress(w, QtCore.Qt.MouseButton.LeftButton, pos=QtCore.QPoint(13, 26))
    QTest.mouseMove(w, QtCore.QPoint(13, 26 + 5000)); qtbot.wait(20)
    QTest.mouseRelease(w, QtCore.Qt.MouseButton.LeftButton, pos=QtCore.QPoint(13, 26))
    olgu(f"mouseMove DUGME BASILI: mouseMoveEvent sayisi={len(olaylar)} olay={olaylar[:1]} -> (pos.y, globalPos.y, buttons)")


def test_o8_repaint_suresi_kucuk_ve_buyuk(qtbot):
    """real_check [7]: 26x52 saydam pencerede repaint() medyani; pozitif kontrol: 20 ms uyuyan paintEvent."""
    class S(QtWidgets.QWidget):
        uyu = 0.0
        def paintEvent(self, e):
            p = QtGui.QPainter(self); p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
            p.setPen(QtGui.QPen(QtGui.QColor("#5ec6ff"), 2)); p.setBrush(QtGui.QColor(22, 27, 33, 235))
            p.drawEllipse(QtCore.QPointF(26, 26), 24.5, 24.5); p.setPen(QtGui.QColor("#d8e2ee"))
            p.setFont(QtGui.QFont("Segoe UI", 11, QtGui.QFont.Weight.Bold))
            p.drawText(QtCore.QRect(0, 0, 26, 52), QtCore.Qt.AlignmentFlag.AlignCenter, "S"); p.end()
            if self.uyu: time.sleep(self.uyu)
    s = S(None, SEKME_BAYRAK); s.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
    s.setGeometry(2534, 670, 26, 52); qtbot.addWidget(s); s.show(); qtbot.wait(50)
    t = []
    for _ in range(100):
        t0 = time.perf_counter(); s.repaint(); t.append((time.perf_counter() - t0) * 1000)
    olgu(f"repaint 26x52 kapali sekme: medyan={statistics.median(t):.3f} ms max={max(t):.2f} ms (<16 esigi: {statistics.median(t)/16*100:.1f}% dolu)")
    # acik panel: 200x132 + QFrame stylesheet + 2 dugme + etiket
    s.setGeometry(2360, 630, 200, 132)
    panel = QtWidgets.QFrame(s); panel.setStyleSheet("QFrame{background:#161b21;border:1px solid #2a3138;border-radius:10px;} QPushButton{background:#1e2630;color:#d8e2ee;border:1px solid #2a3138;border-radius:6px;padding:8px 12px;font:13px 'Segoe UI';}")
    d = QtWidgets.QVBoxLayout(panel); d.addWidget(QtWidgets.QLabel("Suflor")); d.addWidget(QtWidgets.QPushButton("Anlik ceviri")); d.addWidget(QtWidgets.QPushButton("Bolge izle"))
    panel.setGeometry(s.rect()); panel.show(); qtbot.wait(50)
    t2 = []
    for _ in range(100):
        t0 = time.perf_counter(); s.repaint(); t2.append((time.perf_counter() - t0) * 1000)
    olgu(f"repaint 200x132 acik panel (stylesheet, 3 cocuk): medyan={statistics.median(t2):.3f} ms max={max(t2):.2f} ms")
    s.uyu = 0.020; t3 = []
    for _ in range(10):
        t0 = time.perf_counter(); s.repaint(); t3.append((time.perf_counter() - t0) * 1000)
    olgu(f"pozitif kontrol paintEvent 20 ms uyur: repaint medyan={statistics.median(t3):.1f} ms -> olcu ates eder mi={statistics.median(t3) >= 16}")


def test_o9_kapat_iki_kez_cikis_sayaci(qtbot):
    """real_check [6] 'cikis_istendi 1 kez': kapat() iki kez cagrilirsa (dugme + closeEvent) -- paket idempotentligi
    yalnizca 'tepsiye al x2' icin yazdi. Dogal uygulama: kapat() -> close() -> closeEvent -> kapat() -> 2 sinyal."""
    class Ana(QtWidgets.QWidget):
        cikis_istendi = QtCore.Signal()
        def kapat(self):
            self.cikis_istendi.emit(); self.close()
        def closeEvent(self, e):
            self.kapat(); e.accept()
    a = Ana(); qtbot.addWidget(a); n = []
    a.cikis_istendi.connect(lambda: n.append(1)); a.show(); qtbot.wait(10)
    a.kapat(); qtbot.wait(10)
    olgu(f"kapat() -> close() -> closeEvent -> kapat(): cikis_istendi={len(n)} (ozyineleme sonlandi: {len(n) < 10})")


# ---------------------------------------------------------------- madde 7: K4 deterministiklik / waitUntil payi
class Yoklayici(QtCore.QObject):
    """Paketin K4 mekanizmasinin minimal kopyasi: imlec_konumu enjekte, yoklama_ms'de bir QTimer."""

    def __init__(self, dik: QtCore.QRect, imlec: Callable[[], QtCore.QPoint], acilma_ms=120, kapanma_ms=450, yoklama_ms=60):
        super().__init__()
        self.dik, self.imlec, self.acik = dik, imlec, False
        self._ac = QtCore.QTimer(self, singleShot=True, interval=acilma_ms); self._ac.timeout.connect(self._acik_yap)
        self._kap = QtCore.QTimer(self, singleShot=True, interval=kapanma_ms); self._kap.timeout.connect(self._kapali_yap)
        self._yok = QtCore.QTimer(self, interval=yoklama_ms); self._yok.timeout.connect(self._yokla); self._yok.start()

    def _acik_yap(self): self.acik = True
    def _kapali_yap(self): self.acik = False

    def _yokla(self):
        if self.dik.contains(self.imlec()):
            self._kap.stop()
            if not self.acik and not self._ac.isActive(): self._ac.start()
        else:
            self._ac.stop()
            if self.acik and not self._kap.isActive(): self._kap.start()


@pytest.mark.parametrize("yuk", [False, True])
def test_o10_waitUntil_payi(qtbot, yuk):
    """K4 OLCU: acilma <= acilma_ms + 2*yoklama_ms (=240), kapanma <= 570. 30 tekrar; 'yuk' = 2 is parcacigi CPU yakiyor (CI titremesi)."""
    dur = threading.Event(); isciler = []
    if yuk:
        def yak():
            while not dur.is_set(): sum(i * i for i in range(2000))
        isciler = [threading.Thread(target=yak, daemon=True) for _ in range(2)]
        for t in isciler: t.start()
    imlec = QtCore.QPoint(0, 0)
    y = Yoklayici(QtCore.QRect(2534, 670, 26, 52), lambda: imlec)
    ac, kap = [], []
    try:
        for _ in range(30):
            imlec.setX(2547); imlec.setY(696); t0 = time.perf_counter()
            qtbot.waitUntil(lambda: y.acik, timeout=3000); ac.append((time.perf_counter() - t0) * 1000)
            imlec.setX(0); imlec.setY(0); t0 = time.perf_counter()
            qtbot.waitUntil(lambda: not y.acik, timeout=3000); kap.append((time.perf_counter() - t0) * 1000)
    finally:
        dur.set()
    olgu(f"waitUntil yuk={yuk}: acilma medyan={statistics.median(ac):.0f} max={max(ac):.0f} ms (sinir 240, asim={sum(1 for a in ac if a > 240)}/30) | kapanma medyan={statistics.median(kap):.0f} max={max(kap):.0f} ms (sinir 570, asim={sum(1 for k in kap if k > 570)}/30)")


def test_o11_hizli_iceri_disari_ornekleme(qtbot):
    """K4: 50 ms iceri / 50 ms disari (yoklama 60 ms) -> ornekleme ortusmesi ile ACILIR mi (P2'de gercek ekranda 1/10 acildi)."""
    imlec = QtCore.QPoint(0, 0)
    y = Yoklayici(QtCore.QRect(2534, 670, 26, 52), lambda: imlec)
    acilma = 0; onceki = False
    for _ in range(20):
        imlec.setX(2547); imlec.setY(696); qtbot.wait(50)
        acilma += (y.acik and not onceki); onceki = y.acik
        imlec.setX(0); imlec.setY(0); qtbot.wait(50)
        acilma += (y.acik and not onceki); onceki = y.acik
    olgu(f"20x (50 ms iceri/50 ms disari), yoklama 60: acilma sayisi={acilma} (paket: 'titreme zamanlayicilari sifirlar' -> beklenen 0?)")


# ---------------------------------------------------------------- ek: tepsi offscreen, test izolasyonu, activeWindow kontrol
def test_o12_tepsi_offscreen_show_isVisible(qtbot):
    """K5 'tepsi yoksa Tepsi.gorunur() daima False': QSystemTrayIcon.show() tepsi YOKKEN isVisible() ne der?"""
    ikon = QtGui.QIcon(QtGui.QPixmap(16, 16))
    t = QtWidgets.QSystemTrayIcon(ikon)
    t.show(); qtbot.wait(20)
    olgu(f"offscreen tepsi: available={QtWidgets.QSystemTrayIcon.isSystemTrayAvailable()} show() sonrasi isVisible()={t.isVisible()} -> dogal 'gorunur = ikon.isVisible()' uygulamasi K5'i offscreen'de IHLAL eder mi: {t.isVisible()}")
    t.showMessage("b", "m", QtWidgets.QSystemTrayIcon.MessageIcon.NoIcon, 100); qtbot.wait(20)
    olgu("offscreen showMessage(): hata yok")
    t.hide()


def test_o13a_kenar_durumunda_biten_test(qtbot):
    """Onceki test 'kenar' durumunda bitti: sekme ebeveynsiz ve qtbot.addWidget'a verilmedi (AnaPencere icinde yaratildi)."""
    global _SIZAN
    ana = QtWidgets.QWidget(None, QtCore.Qt.WindowType.FramelessWindowHint); qtbot.addWidget(ana)
    ana.sekme = sekme_gibi()   # AnaPencere.__init__ icindeki ebeveynsiz KenarSekmesi gibi
    ana.show(); qtbot.wait(10); ana.hide(); ana.sekme.show(); qtbot.wait(10)
    _SIZAN = ana.sekme
    olgu(f"test A bitti: kenar durumunda, sekme gorunur={ana.sekme.isVisible()}")


def test_o13b_sonraki_testte_gorunur_ust_duzey(qtbot):
    """K1 OLCU 'kapat() sonrasi gorunur ust-duzey widget 0' -- onceki testten sizan sekme sayimi bozar mi."""
    ustler = [type(w).__name__ for w in QtWidgets.QApplication.topLevelWidgets() if w.isVisible()]
    olgu(f"test B basinda gorunur ust-duzey={ustler} (bos olmali; degilse K1 'gorunur ust-duzey 0' testi siraya bagli)")
    for w in QtWidgets.QApplication.topLevelWidgets():
        if w.isVisible(): w.close()


def test_o14_activeWindow_kontrol_sirali(qtbot):
    """Once duz pencere aktifken sekme show() -> aktif pencere sekmeye GECIYOR mu (offscreen)."""
    ana = QtWidgets.QWidget(); qtbot.addWidget(ana); ana.show(); ana.activateWindow(); qtbot.wait(30)
    a0 = QtWidgets.QApplication.activeWindow()
    s = sekme_gibi(); qtbot.addWidget(s); s.show(); qtbot.wait(30)
    a1 = QtWidgets.QApplication.activeWindow()
    olgu(f"offscreen: ana aktif={a0 is ana} -> sekme.show() sonrasi aktif=sekme: {a1 is s} (ana kaldi: {a1 is ana}) -> K3 olcusu 'degismez' offscreen'de {'GECER' if a1 is ana else 'KALIR (dogru kodda bile)'}")
