"""Suflor bolge izleme penceresi: degisen oyun alanini otomatik olarak cevirir.

Pencere ekran yakalama ve kullanici etkilesimini yonetir. OCR/ceviri isi `AnlikAkisi`nin
isci thread'inde kalir. Aynı anda tek kare islenir; is surerken yeni, kararli bir degisim
gelirse yalnizca en son kare saklanir. Boylece yavas bir ceviri kuyrugu buyutmez.
"""
from __future__ import annotations

from collections.abc import Sequence

from PySide6 import QtCore, QtGui, QtWidgets

from src.capture.change_detector import ChangeDetector
from src.capture.service import CaptureService
from src.contracts.errors import CaptureError
from src.contracts.models import Frame, Rect, Segment, TextBlock
from src.pipeline.anlik import AnlikAkisi
from src.ui.bolge_geometrisi import SERIT_YUKSEKLIK, serit_dikdortgeni

__all__ = ["BolgePenceresi"]

YENILEME_MS = 100

_DIL_ADI = {
    "japan": "Japonca",
    "korean": "Korece",
    "chinese": "Çince",
    "english": "İngilizce",
}


class BolgePenceresi(QtWidgets.QWidget):
    """Secilen bolgeyi izleyen, ustte kalan kompakt ceviri seridi."""

    yeniden_sec_istendi = QtCore.Signal()
    kapatildi = QtCore.Signal()

    def __init__(
        self,
        servis: CaptureService,
        bolge: Rect,
        akis: AnlikAkisi,
        *,
        dedektor: ChangeDetector | None = None,
        yenileme_ms: int = YENILEME_MS,
        ekran_siniri: Rect | None = None,
        otomatik_baslat: bool = True,
    ) -> None:
        super().__init__()
        self._servis = servis
        self._bolge = bolge
        self._akis = akis
        self._dedektor = dedektor or ChangeDetector()
        self._mesgul = False
        self._duraklatildi = False
        self._bekleyen: Frame | None = None
        self._kapandi = False
        self._son_cevrilen_kaynak: str | None = None
        self._ekran_siniri = ekran_siniri or self._bolgenin_ekrani(bolge)

        self.setWindowTitle("Suflör — Bölge İzleme")
        self.setWindowFlags(
            QtCore.Qt.WindowType.FramelessWindowHint
            | QtCore.Qt.WindowType.WindowStaysOnTopHint
            | QtCore.Qt.WindowType.Tool
        )
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setStyleSheet("background:transparent; color:#edf4fb;")

        self._ceviri = QtWidgets.QLabel("Seçilen alan okunuyor…")
        self._ceviri.setObjectName("ceviri")
        self._ceviri.setWordWrap(True)
        self._ceviri.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        self._ceviri.setAlignment(QtCore.Qt.AlignmentFlag.AlignVCenter | QtCore.Qt.AlignmentFlag.AlignLeft)
        self._ceviri.setStyleSheet(
            "QLabel#ceviri { background:transparent; border:none; padding:10px 12px;"
            " font:600 16px 'Segoe UI'; }"
        )

        self._kaynak = QtWidgets.QLabel()
        self._kaynak.setObjectName("kaynak")
        self._kaynak.setWordWrap(True)
        self._kaynak.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        self._kaynak.setStyleSheet(
            "QLabel#kaynak { color:#aebdcb; background:#0d1218; border-radius:5px;"
            " padding:6px 10px; font:12px 'Segoe UI'; }"
        )
        self._kaynak.hide()

        self._durum = QtWidgets.QLabel("Hazırlanıyor…")
        self._durum.setStyleSheet("color:#91a4b8; padding:2px 4px;")
        self._dil = QtWidgets.QLabel("Dil: otomatik")
        self._dil.setStyleSheet("color:#8fd3ff; padding:2px 6px; font-weight:600;")

        self._duraklat = QtWidgets.QPushButton("Ⅱ")
        self._duraklat.setAccessibleName("Bölge izlemeyi duraklat")
        self._duraklat.setToolTip("Duraklat")
        self._kaynak_dugmesi = QtWidgets.QPushButton("Kaynak")
        self._kaynak_dugmesi.setAccessibleName("Kaynak metni göster veya gizle")
        self._kaynak_dugmesi.setToolTip("Kaynak metni göster")
        self._yeniden_sec = QtWidgets.QPushButton("↗")
        self._yeniden_sec.setAccessibleName("İzlenen alanı yeniden seç")
        self._yeniden_sec.setToolTip("Alanı değiştir")
        self._kapat = QtWidgets.QPushButton("×")
        self._kapat.setAccessibleName("Bölge izlemeyi kapat")
        self._kapat.setToolTip("Kapat")
        for dugme in (self._duraklat, self._kaynak_dugmesi, self._yeniden_sec, self._kapat):
            dugme.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
            dugme.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
            dugme.setStyleSheet(
                "QPushButton { background:#243241; border:1px solid #3b5064; border-radius:5px;"
                " padding:3px 7px; min-height:20px; } QPushButton:hover { background:#30455a; }"
            )

        self._araclar = QtWidgets.QFrame()
        arac_duzeni = QtWidgets.QHBoxLayout(self._araclar)
        arac_duzeni.setContentsMargins(8, 2, 8, 6)
        arac_duzeni.setSpacing(5)
        arac_duzeni.addWidget(self._durum, 1)
        arac_duzeni.addWidget(self._dil)
        arac_duzeni.addWidget(self._duraklat)
        arac_duzeni.addWidget(self._kaynak_dugmesi)
        arac_duzeni.addWidget(self._yeniden_sec)
        arac_duzeni.addWidget(self._kapat)
        self._araclar.hide()

        self._govde = QtWidgets.QFrame()
        self._govde.setObjectName("govde")
        self._govde.setStyleSheet(
            "QFrame#govde { background:rgba(16,21,28,238); border:1px solid #3b5064; border-radius:10px; }"
        )
        govde_duzeni = QtWidgets.QVBoxLayout(self._govde)
        govde_duzeni.setContentsMargins(0, 0, 0, 0)
        govde_duzeni.setSpacing(0)
        govde_duzeni.addWidget(self._ceviri, 1)
        govde_duzeni.addWidget(self._kaynak)
        govde_duzeni.addWidget(self._araclar)

        duzen = QtWidgets.QVBoxLayout(self)
        duzen.setContentsMargins(0, 0, 0, 0)
        duzen.addWidget(self._govde)
        self._konumlan()

        self._duraklat.clicked.connect(self.duraklat_devam_et)
        self._kaynak_dugmesi.clicked.connect(self.kaynagi_degistir)
        self._yeniden_sec.clicked.connect(self._yeniden_sec_tiklandi)
        self._kapat.clicked.connect(self.close)
        self._akis.bloklar_hazir.connect(self._bloklar_hazir)
        self._akis.ceviri_hazir.connect(self._ceviri_hazir)
        self._akis.hata.connect(self._hata)
        self._akis.dil_algilandi.connect(self.dil_goster)

        self._zamanlayici = QtCore.QTimer(self)
        self._zamanlayici.setInterval(max(25, int(yenileme_ms)))
        self._zamanlayici.timeout.connect(self._tik)
        if otomatik_baslat:
            self._zamanlayici.start()

    @property
    def duraklatildi(self) -> bool:
        return self._duraklatildi

    @property
    def mesgul(self) -> bool:
        return self._mesgul

    @property
    def araclar_gorunur(self) -> bool:
        return not self._araclar.isHidden()

    @staticmethod
    def _bolgenin_ekrani(bolge: Rect) -> Rect:
        merkez = QtCore.QPoint(bolge.x + bolge.w // 2, bolge.y + bolge.h // 2)
        ekran = QtGui.QGuiApplication.screenAt(merkez) or QtGui.QGuiApplication.primaryScreen()
        if ekran is None:
            return Rect(bolge.x, bolge.y, max(bolge.w, 1), max(bolge.h, SERIT_YUKSEKLIK))
        g = ekran.availableGeometry()
        return Rect(g.x(), g.y(), g.width(), g.height(), bolge.monitor_index, bolge.dpi_scale)

    def _konumlan(self) -> None:
        yukseklik = 190 if not self._kaynak.isHidden() else SERIT_YUKSEKLIK
        g = serit_dikdortgeni(self._bolge, self._ekran_siniri, yukseklik=yukseklik)
        self.setGeometry(g.x, g.y, g.w, g.h)

    @QtCore.Slot()
    def _tik(self) -> None:
        if self._duraklatildi or self._kapandi:
            return
        try:
            kare = self._servis.capture_region(self._bolge)
        except CaptureError:
            self._durum.setText("Ekran alanı yakalanamadı")
            self._durum.setStyleSheet("color:#ff9b9b; padding:2px 4px;")
            return
        if not self._dedektor.has_changed(kare):
            return
        if self._mesgul:
            self._bekleyen = kare
            return
        self._isle(kare)

    def _isle(self, kare: Frame) -> None:
        self._mesgul = True
        self._durum.setText("Metin okunuyor…")
        self._durum.setStyleSheet("color:#91a4b8; padding:2px 4px;")
        self._akis.oku(kare)

    @QtCore.Slot(object)
    def _bloklar_hazir(self, bloklar: Sequence[TextBlock]) -> None:
        if self._kapandi:
            return
        liste = list(bloklar)
        if not liste:
            self._kaynak.clear()
            self._ceviri.setText("Bu alanda okunabilir metin bulunamadı.")
            self._tamamla("Metin bekleniyor")
            return
        kaynak = "\n".join(b.text.strip() for b in liste if b.text.strip())
        self._kaynak.setText(kaynak)
        if self._metin_anahtari(kaynak) == self._son_cevrilen_kaynak:
            self._tamamla("Alan izleniyor")
            return
        self._durum.setText("Türkçeye çevriliyor…")
        self._akis.cevir(liste)

    @QtCore.Slot(object, object)
    def _ceviri_hazir(self, segmentler: Sequence[Segment], ceviriler: Sequence[str]) -> None:
        if self._kapandi:
            return
        kaynak = "\n".join(s.text.strip() for s in segmentler if s.text.strip())
        if kaynak:
            self._kaynak.setText(kaynak)
            self._son_cevrilen_kaynak = self._metin_anahtari(kaynak)
        sonuc = "\n".join(c.strip() for c in ceviriler if c.strip())
        self._ceviri.setText(sonuc or "Çeviri üretilemedi.")
        self._tamamla("Alan izleniyor")

    @staticmethod
    def _metin_anahtari(metin: str) -> str:
        return " ".join(metin.split()).casefold()

    @QtCore.Slot(str)
    def _hata(self, sinif: str) -> None:
        if self._kapandi:
            return
        self._ceviri.setText("Çeviri şu anda tamamlanamadı. Alan değişince yeniden denenecek.")
        self._tamamla(f"Geçici hata · {sinif}", hata=True)

    def _tamamla(self, durum: str, *, hata: bool = False) -> None:
        self._mesgul = False
        self._durum.setText(durum)
        self._durum.setStyleSheet(f"color:{'#ff9b9b' if hata else '#83d6a0'}; padding:2px 4px;")
        if self._bekleyen is not None and not self._duraklatildi:
            kare, self._bekleyen = self._bekleyen, None
            QtCore.QTimer.singleShot(0, lambda: self._isle(kare) if not self._kapandi else None)

    @QtCore.Slot(str, bool)
    def dil_goster(self, kod: str, belirsiz: bool) -> None:
        ad = _DIL_ADI.get(kod, kod)
        self._dil.setText(f"Dil: {ad}" + ("?" if belirsiz else ""))
        self._dil.setToolTip("Dil kesin belirlenemedi; Ayarlar'dan seçebilirsin." if belirsiz else "Otomatik algılandı")

    @QtCore.Slot()
    def duraklat_devam_et(self) -> None:
        self._duraklatildi = not self._duraklatildi
        if self._duraklatildi:
            self._zamanlayici.stop()
            self._duraklat.setText("Devam et")
            self._duraklat.setAccessibleName("Bölge izlemeye devam et")
            self._durum.setText("Duraklatıldı")
        else:
            self._zamanlayici.start()
            self._duraklat.setText("Ⅱ")
            self._duraklat.setAccessibleName("Bölge izlemeyi duraklat")
            self._durum.setText("Alan izleniyor")
            if self._bekleyen is not None and not self._mesgul:
                kare, self._bekleyen = self._bekleyen, None
                self._isle(kare)

    @QtCore.Slot()
    def kaynagi_degistir(self) -> None:
        gorunecek = self._kaynak.isHidden()
        self._kaynak.setVisible(gorunecek)
        self._kaynak_dugmesi.setText("Kaynağı gizle" if gorunecek else "Kaynağı göster")
        self._konumlan()

    @QtCore.Slot()
    def _yeniden_sec_tiklandi(self) -> None:
        self.yeniden_sec_istendi.emit()
        self.close()

    def enterEvent(self, event: QtGui.QEnterEvent) -> None:
        self._araclar.show()
        super().enterEvent(event)

    def leaveEvent(self, event: QtCore.QEvent) -> None:
        if self._kaynak.isHidden():
            self._araclar.hide()
        super().leaveEvent(event)

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        self._konumlan()
        super().showEvent(event)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        if not self._kapandi:
            self._kapandi = True
            self._zamanlayici.stop()
            self._akis.iptal()
            self._akis.kapat()
            self.kapatildi.emit()
        super().closeEvent(event)
