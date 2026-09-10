"""Suflör — bölge izleme gösterimi (Mod 2 iskeleti).

Çalıştır:  python demo/bolge_izle.py

1. Ekran kararır, fareyle bir dikdörtgen çiz (Esc = vazgeç).
2. Küçük, üstte kalan bir pencere o bölgeyi canlı gösterir.
3. Alt şerit: yakalama süresi, kare numarası ve DEĞİŞİM tespiti.

Bu bir GÖSTERİMDİR, ürünün arayüzü değil. Amacı `CaptureService` (T-005) ile
`ChangeDetector` (T-002) bileşenlerinin gerçek ekranda çalıştığını göstermek.
Çeviri ve metin okuma henüz yok — onlar sıradaki görevler.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6 import QtCore, QtGui, QtWidgets  # noqa: E402

from src.capture.change_detector import ChangeDetector  # noqa: E402
from src.capture.monitors import union_bbox  # noqa: E402
from src.capture.service import CaptureService, MssBackend  # noqa: E402
from src.contracts.errors import CaptureError  # noqa: E402
from src.contracts.models import Frame, Rect  # noqa: E402

YENILEME_MS = 100  # 10 Hz; gerçek yakalama ~13.5 ms sürüyor (ölçüldü)


def _frame_to_qimage(frame: Frame) -> QtGui.QImage:
    """`Frame.image` (BGR, uint8, C-bitişik) -> `QImage`.

    `CaptureService` her karede koşulsuz kopya döndürür (K7), bu yüzden
    tampon bize aittir; yine de `copy()` ile Qt'ye ayrı bir ömür veriyoruz.
    """
    goruntu = frame.image
    h, w = goruntu.shape[0], goruntu.shape[1]
    kanal = goruntu.shape[2]
    bicim = QtGui.QImage.Format.Format_BGR888 if kanal == 3 else QtGui.QImage.Format.Format_ARGB32
    return QtGui.QImage(goruntu.data, w, h, goruntu.strides[0], bicim).copy()


class SecimKatmani(QtWidgets.QWidget):
    """Tüm sanal masaüstünü kaplayan yarı saydam seçim katmanı."""

    secildi = QtCore.Signal(Rect)

    def __init__(self, birlesim: Rect) -> None:
        super().__init__()
        self._birlesim = birlesim
        self._basla: QtCore.QPoint | None = None
        self._bitir: QtCore.QPoint | None = None

        self.setWindowFlags(
            QtCore.Qt.WindowType.FramelessWindowHint
            | QtCore.Qt.WindowType.WindowStaysOnTopHint
            | QtCore.Qt.WindowType.Tool
        )
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(QtCore.Qt.CursorShape.CrossCursor)
        self.setGeometry(birlesim.x, birlesim.y, birlesim.w, birlesim.h)

    def paintEvent(self, _event: QtGui.QPaintEvent) -> None:
        p = QtGui.QPainter(self)
        p.fillRect(self.rect(), QtGui.QColor(0, 0, 0, 110))

        if self._basla is not None and self._bitir is not None:
            kutu = QtCore.QRect(self._basla, self._bitir).normalized()
            p.setCompositionMode(QtGui.QPainter.CompositionMode.CompositionMode_Clear)
            p.fillRect(kutu, QtCore.Qt.GlobalColor.transparent)
            p.setCompositionMode(QtGui.QPainter.CompositionMode.CompositionMode_SourceOver)
            p.setPen(QtGui.QPen(QtGui.QColor(90, 200, 255), 2))
            p.drawRect(kutu)
            etiket = f"{kutu.width()} x {kutu.height()}"
            p.setPen(QtGui.QColor(230, 240, 255))
            p.setFont(QtGui.QFont("Segoe UI", 10))
            p.drawText(kutu.left(), max(14, kutu.top() - 6), etiket)
        else:
            p.setPen(QtGui.QColor(220, 230, 245))
            p.setFont(QtGui.QFont("Segoe UI", 15))
            p.drawText(
                self.rect(),
                QtCore.Qt.AlignmentFlag.AlignCenter,
                "İzlemek istediğin alanı fareyle çiz   ·   Esc = çık",
            )

    def mousePressEvent(self, e: QtGui.QMouseEvent) -> None:
        self._basla = e.position().toPoint()
        self._bitir = self._basla
        self.update()

    def mouseMoveEvent(self, e: QtGui.QMouseEvent) -> None:
        if self._basla is not None:
            self._bitir = e.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, e: QtGui.QMouseEvent) -> None:
        if self._basla is None:
            return
        self._bitir = e.position().toPoint()
        kutu = QtCore.QRect(self._basla, self._bitir).normalized()
        if kutu.width() < 8 or kutu.height() < 8:
            self._basla = self._bitir = None
            self.update()
            return
        # Katmanın sol-üstü birleşimin sol-üstünde; fiziksel koordinata çeviriyoruz.
        self.secildi.emit(
            Rect(
                x=self._birlesim.x + kutu.left(),
                y=self._birlesim.y + kutu.top(),
                w=kutu.width(),
                h=kutu.height(),
            )
        )
        self.close()

    def keyPressEvent(self, e: QtGui.QKeyEvent) -> None:
        if e.key() == QtCore.Qt.Key.Key_Escape:
            QtWidgets.QApplication.quit()


class IzlemePenceresi(QtWidgets.QWidget):
    """Seçilen bölgeyi canlı gösteren, üstte kalan pencere."""

    def __init__(self, servis: CaptureService, bolge: Rect) -> None:
        super().__init__()
        self._servis = servis
        self._bolge = bolge
        self._dedektor = ChangeDetector()
        self._son_degisim = 0.0
        self._sureler: list[float] = []

        self.setWindowTitle("Suflör — bölge izleme")
        self.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)

        self._ekran = QtWidgets.QLabel(alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        self._ekran.setMinimumSize(360, 120)
        self._ekran.setStyleSheet("background:#101418; border:1px solid #2a3138;")

        self._serit = QtWidgets.QLabel()
        self._serit.setStyleSheet(
            "color:#cfe3f5; background:#161b21; padding:7px 10px;"
            "font-family:Consolas,monospace; font-size:12px;"
        )

        self._rozet = QtWidgets.QLabel("sabit")
        self._rozet.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._rozet.setFixedWidth(150)
        self._rozet_stil("#243041", "#8fa8c0")

        alt = QtWidgets.QHBoxLayout()
        alt.setContentsMargins(0, 0, 0, 0)
        alt.setSpacing(0)
        alt.addWidget(self._serit, 1)
        alt.addWidget(self._rozet)

        duzen = QtWidgets.QVBoxLayout(self)
        duzen.setContentsMargins(0, 0, 0, 0)
        duzen.setSpacing(0)
        duzen.addWidget(self._ekran, 1)
        duzen.addLayout(alt)
        self.setStyleSheet("background:#0d1116;")

        self._zamanlayici = QtCore.QTimer(self)
        self._zamanlayici.timeout.connect(self._tik)
        self._zamanlayici.start(YENILEME_MS)

    def _rozet_stil(self, zemin: str, yazi: str) -> None:
        self._rozet.setStyleSheet(
            f"color:{yazi}; background:{zemin}; padding:7px 10px;"
            "font-family:Consolas,monospace; font-size:12px; font-weight:bold;"
        )

    def _tik(self) -> None:
        t0 = time.perf_counter()
        try:
            kare = self._servis.capture_region(self._bolge)
        except CaptureError as hata:
            self._serit.setText(f"  yakalama hatası: {hata}")
            self._zamanlayici.stop()
            return
        gecen = (time.perf_counter() - t0) * 1000.0
        self._sureler.append(gecen)
        del self._sureler[:-60]

        degisti = self._dedektor.has_changed(kare)
        simdi = time.perf_counter()
        if degisti:
            self._son_degisim = simdi
        taze = (simdi - self._son_degisim) < 0.8 if self._son_degisim else False
        if taze:
            self._rozet.setText("DEĞİŞTİ")
            self._rozet_stil("#1d4d2b", "#7ef2a4")
        else:
            self._rozet.setText("sabit")
            self._rozet_stil("#243041", "#8fa8c0")

        resim = _frame_to_qimage(kare)
        self._ekran.setPixmap(
            QtGui.QPixmap.fromImage(resim).scaled(
                self._ekran.size(),
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation,
            )
        )

        ort = sum(self._sureler) / len(self._sureler)
        r = kare.rect
        self._serit.setText(
            f"  bölge {r.w}x{r.h} @ ({r.x},{r.y})   monitör {r.monitor_index}   "
            f"kare #{kare.seq}   yakalama {gecen:5.1f} ms (ort {ort:4.1f})"
        )


def main() -> int:
    uygulama = QtWidgets.QApplication(sys.argv)

    servis = CaptureService(MssBackend())
    monitorler = servis.monitors
    birlesim = union_bbox(monitorler)
    print(f"monitörler: {[(m.x, m.y, m.w, m.h) for m in monitorler]}")
    print(f"birleşim   : ({birlesim.x}, {birlesim.y}, {birlesim.w}, {birlesim.h})")

    pencereler: list[QtWidgets.QWidget] = []

    def bolge_secildi(bolge: Rect) -> None:
        print(f"seçilen bölge: ({bolge.x}, {bolge.y}, {bolge.w}, {bolge.h})")
        izleme = IzlemePenceresi(servis, bolge)
        izleme.resize(max(420, min(900, bolge.w)), max(220, min(560, bolge.h + 40)))
        izleme.show()
        pencereler.append(izleme)

    katman = SecimKatmani(birlesim)
    katman.secildi.connect(bolge_secildi)
    katman.show()
    katman.activateWindow()
    pencereler.append(katman)

    return uygulama.exec()


if __name__ == "__main__":
    raise SystemExit(main())
