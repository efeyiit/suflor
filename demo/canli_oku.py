"""Suflör — canlı okuma gösterimi: Dalga 1'in tüm zinciri tek pencerede.

Çalıştır:  python demo/canli_oku.py [japan|korean|chinese|english]

1. Ekran kararır, fareyle bir dikdörtgen çiz (Esc = vazgeç).
2. Üstte kalan pencere o bölgeyi canlı gösterir.
3. Bölgedeki içerik DEĞİŞİNCE (ve yalnız o zaman) OCR koşar; okunan satırlar
   yeşil kutularla işaretlenir, altta ham bloklar ve normalize edilmiş
   segmentler listelenir.

Zincir:  CaptureService (T-005) → ChangeDetector (T-002) → RapidOcrEngine (T-006)
         → TextNormalizer (T-004).  Çeviri henüz yok — sıradaki dalga.

Bu bir GÖSTERİMDİR, ürünün arayüzü değil. Hiçbir OCR metni konsola yazılmaz
(PROTOKOL §7); yalnız pencerede gösterilir.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6 import QtCore, QtGui, QtWidgets  # noqa: E402

from demo.bolge_izle import SecimKatmani, _frame_to_qimage  # noqa: E402
from src.capture.change_detector import ChangeDetector  # noqa: E402
from src.capture.monitors import union_bbox  # noqa: E402
from src.capture.service import CaptureService, MssBackend  # noqa: E402
from src.contracts.errors import ModelMissingError, OcrError  # noqa: E402
from src.contracts.models import Frame, OcrPreset, Rect, Segment, TextBlock  # noqa: E402
from src.ocr.normalizer import normalize  # noqa: E402
from src.ocr.rapid_engine import OcrLanguage, RapidOcrEngine  # noqa: E402

YENILEME_MS = 100


class OkumaIsi(QtCore.QObject):
    """OCR'ı ayrı iş parçacığında koşar; arayüz donmaz."""

    bitti = QtCore.Signal(object, object, float)  # bloklar, segmentler, ms

    def __init__(self, motor: RapidOcrEngine, preset: OcrPreset) -> None:
        super().__init__()
        self._motor = motor
        self._preset = preset

    @QtCore.Slot(object)
    def oku(self, kare: Frame) -> None:
        t0 = time.perf_counter()
        try:
            bloklar = self._motor.recognize(kare, self._preset)
            segmentler = normalize(bloklar, self._preset)
        except (OcrError, ModelMissingError) as hata:
            bloklar, segmentler = [], [Segment(text=f"[hata] {hata}", bbox=kare.rect)]
        self.bitti.emit(bloklar, segmentler, (time.perf_counter() - t0) * 1000.0)


class CanliOkumaPenceresi(QtWidgets.QWidget):
    _oku_istegi = QtCore.Signal(object)

    def __init__(self, servis: CaptureService, motor: RapidOcrEngine, bolge: Rect, dil: str) -> None:
        super().__init__()
        self._servis = servis
        self._bolge = bolge
        self._dedektor = ChangeDetector()
        self._son_bloklar: list[TextBlock] = []
        self._okuyor = False
        self._ilk = True

        self.setWindowTitle(f"Suflör — canlı okuma ({dil})")
        self.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet("background:#0d1116; color:#d8e2ee;")

        self._ekran = QtWidgets.QLabel(alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        self._ekran.setMinimumSize(420, 140)
        self._ekran.setStyleSheet("background:#101418; border:1px solid #2a3138;")

        self._ham = QtWidgets.QPlainTextEdit(readOnly=True)
        self._seg = QtWidgets.QPlainTextEdit(readOnly=True)
        for w, baslik in ((self._ham, "ham OCR blokları"), (self._seg, "normalize edilmiş segmentler")):
            w.setPlaceholderText(baslik)
            w.setStyleSheet(
                "QPlainTextEdit{background:#12171d; border:1px solid #232a33; padding:6px;"
                "font-family:'Yu Gothic UI','Malgun Gothic','Segoe UI'; font-size:13px;}"
            )

        metinler = QtWidgets.QHBoxLayout()
        metinler.setSpacing(6)
        metinler.addWidget(self._ham, 1)
        metinler.addWidget(self._seg, 1)

        self._serit = QtWidgets.QLabel("  bekleniyor…")
        self._serit.setStyleSheet(
            "color:#cfe3f5; background:#161b21; padding:7px 10px;"
            "font-family:Consolas,monospace; font-size:12px;"
        )

        duzen = QtWidgets.QVBoxLayout(self)
        duzen.setContentsMargins(0, 0, 0, 0)
        duzen.setSpacing(6)
        duzen.addWidget(self._ekran, 3)
        duzen.addLayout(metinler, 2)
        duzen.addWidget(self._serit)

        # OCR iş parçacığı
        self._is_parcacigi = QtCore.QThread(self)
        self._is = OkumaIsi(motor, OcrPreset.DIALOGUE)
        self._is.moveToThread(self._is_parcacigi)
        self._oku_istegi.connect(self._is.oku)
        self._is.bitti.connect(self._okuma_bitti)
        self._is_parcacigi.start()

        self._zamanlayici = QtCore.QTimer(self)
        self._zamanlayici.timeout.connect(self._tik)
        self._zamanlayici.start(YENILEME_MS)

    def closeEvent(self, e: QtGui.QCloseEvent) -> None:
        self._zamanlayici.stop()
        self._is_parcacigi.quit()
        self._is_parcacigi.wait(2000)
        super().closeEvent(e)

    def _tik(self) -> None:
        kare = self._servis.capture_region(self._bolge)
        degisti = self._dedektor.has_changed(kare)
        if (degisti or self._ilk) and not self._okuyor:
            self._ilk = False
            self._okuyor = True
            self._serit.setText("  okunuyor…")
            self._oku_istegi.emit(kare)
        self._ciz(kare)

    @QtCore.Slot(object, object, float)
    def _okuma_bitti(self, bloklar: list[TextBlock], segmentler: list[Segment], ms: float) -> None:
        self._okuyor = False
        self._son_bloklar = bloklar
        self._ham.setPlainText("\n".join(f"[{b.confidence:.2f}] {b.text}" for b in bloklar))
        self._seg.setPlainText(
            "\n\n".join((f"{s.speaker}: " if s.speaker else "") + s.text for s in segmentler)
        )
        self._serit.setText(
            f"  bölge {self._bolge.w}x{self._bolge.h} @ ({self._bolge.x},{self._bolge.y})   "
            f"OCR {ms:5.0f} ms   {len(bloklar)} blok → {len(segmentler)} segment"
        )

    def _ciz(self, kare: Frame) -> None:
        pix = QtGui.QPixmap.fromImage(_frame_to_qimage(kare))
        if self._son_bloklar:
            p = QtGui.QPainter(pix)
            p.setPen(QtGui.QPen(QtGui.QColor(120, 235, 170), 2))
            for b in self._son_bloklar:
                r = b.bbox
                p.drawRect(r.x - kare.rect.x, r.y - kare.rect.y, r.w, r.h)
            p.end()
        self._ekran.setPixmap(
            pix.scaled(
                self._ekran.size(),
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation,
            )
        )


def main() -> int:
    dil_adi = (sys.argv[1] if len(sys.argv) > 1 else "japan").lower()
    try:
        dil = OcrLanguage(dil_adi)
    except ValueError:
        print(f"dil tanınmadı: {dil_adi!r}; seçenekler: {[d.value for d in OcrLanguage]}")
        return 2

    uygulama = QtWidgets.QApplication(sys.argv)
    servis = CaptureService(MssBackend())
    motor = RapidOcrEngine(language=dil, threads=8, allow_download=True)
    birlesim = union_bbox(servis.monitors)
    pencereler: list[QtWidgets.QWidget] = []

    def secildi(bolge: Rect) -> None:
        pencere = CanliOkumaPenceresi(servis, motor, bolge, dil.value)
        pencere.resize(max(560, min(1000, bolge.w + 40)), max(420, min(760, bolge.h + 300)))
        pencere.show()
        pencereler.append(pencere)

    katman = SecimKatmani(birlesim)
    katman.secildi.connect(secildi)
    katman.show()
    katman.activateWindow()
    pencereler.append(katman)
    return uygulama.exec()


if __name__ == "__main__":
    raise SystemExit(main())
