"""Suflör — canlı ÇEVİRİ gösterimi: ekrandan yakala → oku → birleştir → Türkçe'ye çevir.

Çalıştır:  python demo/canli_cevir.py [japan|korean|chinese|english] [sözlük.json | -]

Zincir:  CaptureService (T-005) → ChangeDetector (T-002) → RapidOcrEngine (T-006)
         → SatırBirleştirici (T-008) → TextNormalizer (T-004)
         → GlossaryStore + terimleri_gom (T-011, Katman 0) → yerel NMT (NLLB-200 600M int8, CTranslate2)

Çeviri adımı ürünün kendi bileşeni `LocalNmtProvider` (T-007) ile yapılır.
Model `models/nllb-200-distilled-600M-ct2-int8/` altında olmalı.

Sözlük (T-011): ikinci argüman JSON yolu; verilmezse `demo/sozluk_ornek.json`, `-` ise sözlük yok.
Eşleşen terimler kaynağa hedef biçimiyle gömülür (`방앗간을` → `Değirmen을`); kaynak panosu
modele giden gömülü metni gösterir, Türkçe panoda gömülen terimler kalın yazılır.

Hiçbir OCR/çeviri metni konsola yazılmaz (PROTOKOL §7); yalnız pencerede.
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
from src.contracts.errors import ModelMissingError, OcrError, TranslatorError  # noqa: E402
from src.contracts.models import Frame, OcrPreset, Rect, Segment, TextBlock, TranslationRequest  # noqa: E402
from src.ocr.normalizer import normalize  # noqa: E402
from src.ocr.satir_birlestirici import satirlari_birlestir  # noqa: E402
from src.ocr.rapid_engine import OcrLanguage, RapidOcrEngine  # noqa: E402
from src.translate.local_nmt import LocalNmtProvider  # noqa: E402
from src.translate.sozluk import GlossaryStore, terimleri_gom  # noqa: E402

YENILEME_MS = 100
MODEL_DIZINI = Path(__file__).resolve().parent.parent / "models" / "nllb-200-distilled-600M-ct2-int8"
VARSAYILAN_SOZLUK = Path(__file__).resolve().parent / "sozluk_ornek.json"
NLLB_KODU = {
    OcrLanguage.JAPAN: "jpn_Jpan",
    OcrLanguage.KOREAN: "kor_Hang",
    OcrLanguage.CHINESE: "zho_Hans",
    OcrLanguage.ENGLISH: "eng_Latn",
}


class GosterimCevirici:
    """`LocalNmtProvider` (T-007) üzerinde ince sarmalayıcı: segment listesi -> Türkçe listesi.

    Sözlük verilmişse T-011 zinciri çeviriden ÖNCE koşar: `lookup_segments` -> `terimleri_gom`;
    motor gömülü metni görür. Dönüş: (gömülü segmentler, çeviriler, gömülen hedef terimler).
    """

    def __init__(self, kaynak_kodu: str, sozluk: GlossaryStore | None = None) -> None:
        self._saglayici = LocalNmtProvider(model_dir=MODEL_DIZINI, threads=8)
        self._kaynak = kaynak_kodu
        self._sozluk = sozluk

    def cevir(self, segmentler: list[Segment]) -> tuple[list[Segment], list[str], list[str]]:
        if not segmentler:
            return [], [], []
        gomulu, terimler = list(segmentler), []
        if self._sozluk is not None:
            hits = self._sozluk.lookup_segments(segmentler)
            gomulu = list(terimleri_gom(segmentler, hits))
            terimler = [h.target_term for h in hits if h.target_term != h.source_term]  # kimlik cipasi sayilmaz
        istek = TranslationRequest(segments=tuple(gomulu), source_lang=self._kaynak, target_lang="tr")
        return gomulu, list(self._saglayici.translate(istek).translations), terimler

class CeviriIsi(QtCore.QObject):
    bitti = QtCore.Signal(object, object, object, object, float, float)  # bloklar, gömülü segmentler, çeviriler, terimler, ocr_ms, cev_ms

    def __init__(self, motor: RapidOcrEngine, cevirici: GosterimCevirici, preset: OcrPreset) -> None:
        super().__init__()
        self._motor, self._cevirici, self._preset = motor, cevirici, preset

    @QtCore.Slot(object)
    def isle(self, kare: Frame) -> None:
        t0 = time.perf_counter()
        try:
            bloklar = self._motor.recognize(kare, self._preset)
            segmentler = normalize(satirlari_birlestir(bloklar), self._preset)  # T-008: kelime kutulari -> satir
        except (OcrError, ModelMissingError) as hata:
            self.bitti.emit([], [Segment(text=f"[hata] {hata}", bbox=kare.rect)], [""], [], 0.0, 0.0)
            return
        t1 = time.perf_counter()
        try:
            gomulu, ceviriler, terimler = self._cevirici.cevir(list(segmentler))  # T-011: sözlük çeviriden önce
        except TranslatorError as hata:  # sözlük/çeviri sözleşme hatası: pencere donmasın, göster
            self.bitti.emit(bloklar, segmentler, [f"[çeviri hatası] {type(hata).__name__}"] * len(segmentler), [],
                            (t1 - t0) * 1000, 0.0)
            return
        t2 = time.perf_counter()
        self.bitti.emit(bloklar, gomulu, ceviriler, terimler, (t1 - t0) * 1000, (t2 - t1) * 1000)


class CanliCeviriPenceresi(QtWidgets.QWidget):
    _istek = QtCore.Signal(object)

    def __init__(self, servis: CaptureService, motor: RapidOcrEngine, cevirici: GosterimCevirici,
                 bolge: Rect, dil: str) -> None:
        super().__init__()
        self._servis, self._bolge = servis, bolge
        self._dedektor = ChangeDetector()
        self._son_bloklar: list[TextBlock] = []
        self._isliyor, self._ilk = False, True

        self.setWindowTitle(f"Suflör — canlı çeviri ({dil} → Türkçe)")
        self.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet("background:#0d1116; color:#d8e2ee;")

        self._ekran = QtWidgets.QLabel(alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        self._ekran.setMinimumSize(420, 120)
        self._ekran.setStyleSheet("background:#101418; border:1px solid #2a3138;")

        self._kaynak = QtWidgets.QPlainTextEdit(readOnly=True)
        self._kaynak.setPlaceholderText("kaynak (normalize edilmiş, sözlük terimleri gömülü)")
        self._kaynak.setStyleSheet(
            "QPlainTextEdit{background:#12171d; border:1px solid #232a33; padding:8px;"
            "font-family:'Yu Gothic UI','Malgun Gothic','Segoe UI'; font-size:13px; color:#9fb3c8;}")

        self._turkce = QtWidgets.QPlainTextEdit(readOnly=True)
        self._turkce.setPlaceholderText("Türkçe")
        self._turkce.setStyleSheet(
            "QPlainTextEdit{background:#0f1a14; border:1px solid #1f4d33; padding:8px;"
            "font-family:'Segoe UI'; font-size:15px; color:#e6f5ea;}")

        metinler = QtWidgets.QHBoxLayout()
        metinler.setSpacing(6)
        metinler.addWidget(self._kaynak, 2)
        metinler.addWidget(self._turkce, 3)

        self._serit = QtWidgets.QLabel("  bekleniyor…")
        self._serit.setStyleSheet(
            "color:#cfe3f5; background:#161b21; padding:7px 10px;"
            "font-family:Consolas,monospace; font-size:12px;")

        duzen = QtWidgets.QVBoxLayout(self)
        duzen.setContentsMargins(0, 0, 0, 0)
        duzen.setSpacing(6)
        duzen.addWidget(self._ekran, 3)
        duzen.addLayout(metinler, 2)
        duzen.addWidget(self._serit)

        self._ip = QtCore.QThread(self)
        self._is = CeviriIsi(motor, cevirici, OcrPreset.DIALOGUE)
        self._is.moveToThread(self._ip)
        self._istek.connect(self._is.isle)
        self._is.bitti.connect(self._bitti)
        self._ip.start()

        self._zamanlayici = QtCore.QTimer(self)
        self._zamanlayici.timeout.connect(self._tik)
        self._zamanlayici.start(YENILEME_MS)

    def closeEvent(self, e: QtGui.QCloseEvent) -> None:
        self._zamanlayici.stop()
        self._ip.quit()
        self._ip.wait(2000)
        super().closeEvent(e)

    def _tik(self) -> None:
        kare = self._servis.capture_region(self._bolge)
        if (self._dedektor.has_changed(kare) or self._ilk) and not self._isliyor:
            self._ilk, self._isliyor = False, True
            self._serit.setText("  okunuyor ve çevriliyor…")
            self._istek.emit(kare)
        self._ciz(kare)

    @QtCore.Slot(object, object, object, object, float, float)
    def _bitti(self, bloklar: list[TextBlock], segmentler: list[Segment], ceviriler: list[str],
               terimler: list[str], ocr_ms: float, cev_ms: float) -> None:
        self._isliyor = False
        self._son_bloklar = bloklar
        self._kaynak.setPlainText("\n\n".join((f"{s.speaker}: " if s.speaker else "") + s.text for s in segmentler))
        self._turkce.setPlainText("\n\n".join(
            (f"{s.speaker}: " if s.speaker else "") + c for s, c in zip(segmentler, ceviriler)))
        self._terimleri_vurgula(terimler)
        sozluk = f"   sözlük {len(terimler)} terim" if terimler else ""
        self._serit.setText(
            f"  bölge {self._bolge.w}x{self._bolge.h} @ ({self._bolge.x},{self._bolge.y})   "
            f"OCR {ocr_ms:4.0f} ms   çeviri {cev_ms:4.0f} ms   {len(bloklar)} blok → {len(segmentler)} segment{sozluk}")

    def _terimleri_vurgula(self, terimler: list[str]) -> None:
        """Türkçe panoda gömülen hedef terimlerin geçişlerini kalın + sarı yapar (yalnız görsel)."""
        belge = self._turkce.document()
        bicim = QtGui.QTextCharFormat()
        bicim.setFontWeight(QtGui.QFont.Weight.Bold)
        bicim.setForeground(QtGui.QColor(255, 214, 102))
        for terim in set(terimler):
            imlec = belge.find(terim)
            while not imlec.isNull():
                imlec.mergeCharFormat(bicim)
                imlec = belge.find(terim, imlec)

    def _ciz(self, kare: Frame) -> None:
        pix = QtGui.QPixmap.fromImage(_frame_to_qimage(kare))
        if self._son_bloklar:
            p = QtGui.QPainter(pix)
            p.setPen(QtGui.QPen(QtGui.QColor(120, 235, 170), 2))
            for b in self._son_bloklar:
                p.drawRect(b.bbox.x - kare.rect.x, b.bbox.y - kare.rect.y, b.bbox.w, b.bbox.h)
            p.end()
        self._ekran.setPixmap(pix.scaled(self._ekran.size(), QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                                         QtCore.Qt.TransformationMode.SmoothTransformation))


def main() -> int:
    dil_adi = (sys.argv[1] if len(sys.argv) > 1 else "japan").lower()
    try:
        dil = OcrLanguage(dil_adi)
    except ValueError:
        print(f"dil tanınmadı: {dil_adi!r}; seçenekler: {[d.value for d in OcrLanguage]}")
        return 2
    sozluk_arg = sys.argv[2] if len(sys.argv) > 2 else str(VARSAYILAN_SOZLUK)
    sozluk = None if sozluk_arg == "-" else GlossaryStore(Path(sozluk_arg))  # şema hatası -> ValueError, açık
    uygulama = QtWidgets.QApplication(sys.argv)
    servis = CaptureService(MssBackend())
    motor = RapidOcrEngine(language=dil, threads=8, allow_download=True)
    cevirici = GosterimCevirici(NLLB_KODU[dil], sozluk)
    birlesim = union_bbox(servis.monitors)
    pencereler: list[QtWidgets.QWidget] = []

    def secildi(bolge: Rect) -> None:
        p = CanliCeviriPenceresi(servis, motor, cevirici, bolge, dil.value)
        p.resize(max(640, min(1100, bolge.w + 60)), max(460, min(800, bolge.h + 320)))
        p.show()
        pencereler.append(p)

    katman = SecimKatmani(birlesim)
    katman.secildi.connect(secildi)
    katman.show()
    katman.activateWindow()
    pencereler.append(katman)
    return uygulama.exec()


if __name__ == "__main__":
    raise SystemExit(main())
