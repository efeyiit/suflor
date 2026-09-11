"""Suflör — UI KABUĞU gösterimi (T-012 ön çalışma): ana pencere + üç düğme + tepsi + kenar sekmesi.

Çalıştır:  python demo/kabuk.py

Sağ üstteki üç düğme (kullanıcı isteği, 11 Eylül 2026):
  ✕  Kapat        — uygulama tamamen kapanır (tepside kalıntı yok)
  ▾  Tepsiye al   — pencere gizlenir, uygulama sistem tepsisinde çalışır; tepsi ikonuna tık → geri gelir
  ◐  Kenara al    — masaüstünde pencere görünmez; ekranın sağ kenarında küçük YARIM DAİRE durur.
                    İmleç üstüne gelince açılır: "Anlık çeviri" ve "Bölge izle" seçenekleri.
                    Yarım daire dikeyde sürüklenebilir; sağ tık → ana pencere geri gelir.

"Bölge izle" bu gösterimde gerçek T-005 seçim katmanını açar (demo/bolge_izle.py); "Anlık çeviri"
(Snapshot modu) henüz yok — bilgi balonu gösterir. Model yüklenmez; kabuğun kendisi ölçülür.
Hiçbir OCR/çeviri metni konsola yazılmaz.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6 import QtCore, QtGui, QtWidgets  # noqa: E402

from demo.bolge_izle import IzlemePenceresi, SecimKatmani  # noqa: E402
from src.capture.monitors import union_bbox  # noqa: E402
from src.capture.service import CaptureService, MssBackend  # noqa: E402
from src.contracts.models import Rect  # noqa: E402

ARKA = "#0d1116"
YUZEY = "#161b21"
KENAR = "#2a3138"
YAZI = "#d8e2ee"
VURGU = "#5ec6ff"
YARICAP = 26            # yarım dairenin yarıçapı (px)
ACILMA_MS = 120         # imleç üstüne gelince açılma gecikmesi
KAPANMA_MS = 450        # imleç ayrılınca kapanma gecikmesi


def _ikon() -> QtGui.QIcon:
    """Tepsi ve pencere ikonu: koyu daire içinde 'S'."""
    pix = QtGui.QPixmap(64, 64)
    pix.fill(QtCore.Qt.GlobalColor.transparent)
    p = QtGui.QPainter(pix)
    p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
    p.setBrush(QtGui.QColor(VURGU))
    p.setPen(QtCore.Qt.PenStyle.NoPen)
    p.drawEllipse(2, 2, 60, 60)
    p.setPen(QtGui.QColor(ARKA))
    f = QtGui.QFont("Segoe UI", 30, QtGui.QFont.Weight.Bold)
    p.setFont(f)
    p.drawText(pix.rect(), QtCore.Qt.AlignmentFlag.AlignCenter, "S")
    p.end()
    return QtGui.QIcon(pix)


class KenarSekmesi(QtWidgets.QWidget):
    """Ekranın sağ kenarında yarım daire; imleç gelince iki seçenekli panele açılır.

    Odak almaz (`WindowDoesNotAcceptFocus`, `WA_ShowWithoutActivating`) — oyunun odağını çalmaz.
    Kapalı hâl: YARICAP x 2*YARICAP; açık hâl: panel. Dikeyde sürüklenebilir. Sağ tık → `pencereyi_goster`.
    """

    anlik_cevir = QtCore.Signal()
    bolge_izle = QtCore.Signal()
    pencereyi_goster = QtCore.Signal()

    def __init__(self, ekran: QtGui.QScreen) -> None:
        super().__init__(None, QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.Tool
                         | QtCore.Qt.WindowType.WindowStaysOnTopHint | QtCore.Qt.WindowType.WindowDoesNotAcceptFocus)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setMouseTracking(True)
        self._ekran = ekran
        self._acik = False
        self._surukleme: int | None = None
        g = ekran.availableGeometry()
        self._y = g.top() + g.height() // 2 - YARICAP     # yarım dairenin üst y'si (dikey orta)

        self._panel = QtWidgets.QFrame(self)
        self._panel.setStyleSheet(
            f"QFrame{{background:{YUZEY}; border:1px solid {KENAR}; border-radius:10px;}}"
            f"QPushButton{{background:#1e2630; color:{YAZI}; border:1px solid {KENAR}; border-radius:6px;"
            f" padding:8px 12px; font:13px 'Segoe UI'; text-align:left;}}"
            f"QPushButton:hover{{border-color:{VURGU}; color:{VURGU};}}"
            f"QLabel{{color:#8fa3b8; font:11px 'Segoe UI'; border:none;}}")
        duzen = QtWidgets.QVBoxLayout(self._panel)
        duzen.setContentsMargins(10, 8, 10, 8)
        duzen.setSpacing(6)
        baslik = QtWidgets.QLabel("Suflör")
        b1 = QtWidgets.QPushButton("⚡  Anlık çeviri")
        b1.setToolTip("Ekran donar, metin blokları çerçevelenir, seçtiklerin çevrilir (Ctrl+Alt+T)")
        b2 = QtWidgets.QPushButton("▭  Bölge izle")
        b2.setToolTip("Dikdörtgen çiz; bölge sürekli çevrilir (Ctrl+Alt+R)")
        b1.clicked.connect(self.anlik_cevir)
        b2.clicked.connect(self.bolge_izle)
        for w in (baslik, b1, b2):
            duzen.addWidget(w)
        self._panel.hide()

        self._acilma = QtCore.QTimer(self, singleShot=True, interval=ACILMA_MS)
        self._acilma.timeout.connect(self._ac)
        self._kapanma = QtCore.QTimer(self, singleShot=True, interval=KAPANMA_MS)
        self._kapanma.timeout.connect(self._kapat)
        # enter/leave bazı üst-katman pencerelerde güvenilmez; imleç konumunu da 60 ms'de bir yokla
        self._yoklayici = QtCore.QTimer(self, interval=60)
        self._yoklayici.timeout.connect(self._yokla)
        self._yoklayici.start()
        self._kapat()

    # -- geometri --------------------------------------------------------------------------------
    def _kapali_geometri(self) -> QtCore.QRect:
        g = self._ekran.availableGeometry()
        return QtCore.QRect(g.right() - YARICAP + 1, self._y, YARICAP, 2 * YARICAP)

    def _acik_geometri(self) -> QtCore.QRect:
        g = self._ekran.availableGeometry()
        w, h = 200, 132
        y = min(max(g.top(), self._y - h // 2 + YARICAP), g.bottom() - h + 1)
        return QtCore.QRect(g.right() - w + 1, y, w, h)

    def _ac(self) -> None:
        if self._acik:
            return
        self._acik = True
        self.setGeometry(self._acik_geometri())
        self._panel.setGeometry(self.rect())
        self._panel.show()
        self.update()

    def _kapat(self) -> None:
        self._acik = False
        self._panel.hide()
        self.setGeometry(self._kapali_geometri())
        self.update()

    def _yokla(self) -> None:
        if not self.isVisible():
            return
        icinde = self.frameGeometry().contains(QtGui.QCursor.pos())
        if icinde:
            self._kapanma.stop()
            if not self._acik and not self._acilma.isActive():
                self._acilma.start()
        else:
            self._acilma.stop()
            if self._acik and not self._kapanma.isActive() and self._surukleme is None:
                self._kapanma.start()

    # -- çizim -----------------------------------------------------------------------------------
    def paintEvent(self, e: QtGui.QPaintEvent) -> None:
        if self._acik:
            return
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        p.setPen(QtGui.QPen(QtGui.QColor(VURGU), 2))
        p.setBrush(QtGui.QColor(22, 27, 33, 235))
        # merkez ekranın sağ kenarında: yalnız sol yarım görünür
        p.drawEllipse(QtCore.QPointF(YARICAP, YARICAP), YARICAP - 1.5, YARICAP - 1.5)
        p.setPen(QtGui.QColor(YAZI))
        p.setFont(QtGui.QFont("Segoe UI", 11, QtGui.QFont.Weight.Bold))
        p.drawText(QtCore.QRect(0, 0, YARICAP, 2 * YARICAP), QtCore.Qt.AlignmentFlag.AlignCenter, "S")
        p.end()

    # -- fare ------------------------------------------------------------------------------------
    def mousePressEvent(self, e: QtGui.QMouseEvent) -> None:
        if e.button() == QtCore.Qt.MouseButton.RightButton:
            self.pencereyi_goster.emit()
        elif e.button() == QtCore.Qt.MouseButton.LeftButton and not self._acik:
            self._surukleme = int(e.globalPosition().y()) - self._y

    def mouseMoveEvent(self, e: QtGui.QMouseEvent) -> None:
        if self._surukleme is not None:
            g = self._ekran.availableGeometry()
            self._y = min(max(g.top(), int(e.globalPosition().y()) - self._surukleme), g.bottom() - 2 * YARICAP + 1)
            self.setGeometry(self._kapali_geometri())

    def mouseReleaseEvent(self, e: QtGui.QMouseEvent) -> None:
        self._surukleme = None


class AnaPencere(QtWidgets.QWidget):
    """Çerçevesiz ana pencere; sağ üstte üç düğme: Kapat · Tepsiye al · Kenara al."""

    def __init__(self, servis: CaptureService) -> None:
        super().__init__(None, QtCore.Qt.WindowType.FramelessWindowHint)
        self._servis = servis
        self._pencereler: list[QtWidgets.QWidget] = []
        self._surukleme: QtCore.QPoint | None = None
        self.setWindowTitle("Suflör")
        self.setWindowIcon(_ikon())
        self.resize(520, 340)
        self.setStyleSheet(
            f"QWidget{{background:{ARKA}; color:{YAZI}; font-family:'Segoe UI';}}"
            f"QPushButton#mod{{background:{YUZEY}; border:1px solid {KENAR}; border-radius:10px; padding:18px; font-size:15px; text-align:left;}}"
            f"QPushButton#mod:hover{{border-color:{VURGU};}}"
            f"QPushButton#ust{{background:transparent; border:none; color:#9fb3c8; font-size:15px; min-width:36px; min-height:28px;}}"
            f"QPushButton#ust:hover{{background:#222a33; color:{YAZI};}}"
            f"QPushButton#kapat:hover{{background:#c0392b; color:white;}}"
            f"QLabel#baslik{{font-size:18px; font-weight:600; color:{VURGU};}}"
            f"QLabel#not{{color:#8fa3b8; font-size:12px;}}")

        baslik = QtWidgets.QLabel("Suflör", objectName="baslik")
        self._b_kenar = QtWidgets.QPushButton("◐", objectName="ust", toolTip="Kenara al — masaüstünde görünmez, sağ kenarda yarım daire")
        self._b_tepsi = QtWidgets.QPushButton("▾", objectName="ust", toolTip="Tepsiye al — arka planda çalışır")
        self._b_kapat = QtWidgets.QPushButton("✕", objectName="ust", toolTip="Kapat — uygulama tamamen kapanır")
        self._b_kapat.setObjectName("kapat")
        self._b_kapat.setStyleSheet(f"QPushButton{{background:transparent; border:none; color:#9fb3c8; font-size:15px; min-width:36px; min-height:28px;}} QPushButton:hover{{background:#c0392b; color:white;}}")
        ust = QtWidgets.QHBoxLayout()
        ust.setContentsMargins(14, 8, 8, 0)
        ust.addWidget(baslik)
        ust.addStretch(1)
        for b in (self._b_kenar, self._b_tepsi, self._b_kapat):
            ust.addWidget(b)

        self._m_anlik = QtWidgets.QPushButton("⚡  Anlık çeviri\nEkranı dondur, blokları seç, çevir      Ctrl+Alt+T", objectName="mod")
        self._m_bolge = QtWidgets.QPushButton("▭  Bölge izle\nDikdörtgen çiz, sürekli çevir             Ctrl+Alt+R", objectName="mod")
        notu = QtWidgets.QLabel("Çevrimdışı · yerel OCR + yerel çeviri · hiçbir metin diske ya da ağa gitmez", objectName="not")
        self._durum = QtWidgets.QLabel("", objectName="not")

        govde = QtWidgets.QVBoxLayout()
        govde.setContentsMargins(18, 10, 18, 14)
        govde.setSpacing(10)
        govde.addWidget(self._m_anlik)
        govde.addWidget(self._m_bolge)
        govde.addStretch(1)
        govde.addWidget(notu)
        govde.addWidget(self._durum)

        duzen = QtWidgets.QVBoxLayout(self)
        duzen.setContentsMargins(0, 0, 0, 0)
        duzen.addLayout(ust)
        duzen.addLayout(govde)

        # tepsi
        self._tepsi = QtWidgets.QSystemTrayIcon(_ikon(), self)
        self._tepsi.setToolTip("Suflör — arka planda")
        menu = QtWidgets.QMenu()
        menu.addAction("Pencereyi göster", self.goster)
        menu.addAction("Kenara al", self.kenara_al)
        menu.addSeparator()
        menu.addAction("Çıkış", self.kapat)
        self._tepsi.setContextMenu(menu)
        self._tepsi.activated.connect(self._tepsi_tik)

        # kenar sekmesi
        ekran = QtGui.QGuiApplication.primaryScreen()
        self._sekme = KenarSekmesi(ekran)
        self._sekme.pencereyi_goster.connect(self.goster)
        self._sekme.anlik_cevir.connect(self.anlik_cevir)
        self._sekme.bolge_izle.connect(self.bolge_izle)

        self._b_kapat.clicked.connect(self.kapat)
        self._b_tepsi.clicked.connect(self.tepsiye_al)
        self._b_kenar.clicked.connect(self.kenara_al)
        self._m_anlik.clicked.connect(self.anlik_cevir)
        self._m_bolge.clicked.connect(self.bolge_izle)

    # -- üç düğme --------------------------------------------------------------------------------
    def kapat(self) -> None:
        self._tepsi.hide()
        self._sekme.close()
        QtWidgets.QApplication.quit()

    def tepsiye_al(self) -> None:
        self._sekme.hide()
        self._tepsi.show()
        self.hide()
        self._tepsi.showMessage("Suflör arka planda", "Tepsi ikonuna tıklayınca pencere geri gelir.",
                                QtWidgets.QSystemTrayIcon.MessageIcon.NoIcon, 2500)

    def kenara_al(self) -> None:
        self._tepsi.show()          # tepside de kalır: kullanıcı sekmeyi bulamazsa oradan dönebilir
        self.hide()
        self._sekme.show()

    def goster(self) -> None:
        self._sekme.hide()
        self.show()
        self.raise_()
        self.activateWindow()

    def _tepsi_tik(self, sebep: QtWidgets.QSystemTrayIcon.ActivationReason) -> None:
        if sebep in (QtWidgets.QSystemTrayIcon.ActivationReason.Trigger, QtWidgets.QSystemTrayIcon.ActivationReason.DoubleClick):
            self.goster()

    # -- iki mod ---------------------------------------------------------------------------------
    def anlik_cevir(self) -> None:
        self._durum.setText("Anlık çeviri (Snapshot modu) henüz bağlı değil — sıradaki görev.")
        if self._sekme.isVisible():
            self._tepsi.show()
            self._tepsi.showMessage("Anlık çeviri", "Snapshot modu henüz bağlı değil.", QtWidgets.QSystemTrayIcon.MessageIcon.NoIcon, 2000)

    def bolge_izle(self) -> None:
        birlesim = union_bbox(self._servis.monitors)
        if birlesim is None:
            return
        katman = SecimKatmani(birlesim)

        def secildi(bolge: Rect) -> None:
            izleme = IzlemePenceresi(self._servis, bolge)
            izleme.resize(max(420, min(900, bolge.w)), max(220, min(560, bolge.h + 40)))
            izleme.show()
            self._pencereler.append(izleme)
            self._durum.setText(f"Bölge izleniyor: {bolge.w}×{bolge.h} @ ({bolge.x},{bolge.y})")

        katman.secildi.connect(secildi)
        katman.show()
        katman.activateWindow()
        self._pencereler.append(katman)

    # -- çerçevesiz pencereyi sürükleme ----------------------------------------------------------
    def mousePressEvent(self, e: QtGui.QMouseEvent) -> None:
        if e.button() == QtCore.Qt.MouseButton.LeftButton and e.position().y() < 44:
            self._surukleme = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e: QtGui.QMouseEvent) -> None:
        if self._surukleme is not None:
            self.move(e.globalPosition().toPoint() - self._surukleme)

    def mouseReleaseEvent(self, e: QtGui.QMouseEvent) -> None:
        self._surukleme = None


def main() -> int:
    uygulama = QtWidgets.QApplication(sys.argv)
    uygulama.setQuitOnLastWindowClosed(False)   # tepsi/kenar hâlinde pencere yokken yaşamalı
    servis = CaptureService(MssBackend())
    pencere = AnaPencere(servis)
    pencere.show()
    return uygulama.exec()


if __name__ == "__main__":
    raise SystemExit(main())
