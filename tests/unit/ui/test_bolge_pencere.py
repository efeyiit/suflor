"""Bölge izleme ürün penceresinin kullanıcı akışı."""
from __future__ import annotations

import numpy as np
from PySide6 import QtCore, QtWidgets
from pytestqt.qtbot import QtBot

from src.capture.change_detector import ChangeDetector
from src.contracts.models import Frame, Rect, Segment, TextBlock
from src.ui.bolge_pencere import BolgePenceresi


def kare(seq: int, deger: int = 0) -> Frame:
    goruntu = np.zeros((80, 220, 3), dtype=np.uint8)
    if deger:
        goruntu[:, 110:, :] = deger
    return Frame(goruntu, Rect(10, 20, 220, 80), 1.0, seq)


class SahteServis:
    def __init__(self, kareler: list[Frame]) -> None:
        self.kareler = kareler
        self.cagri = 0

    def capture_region(self, _bolge: Rect) -> Frame:
        sonuc = self.kareler[min(self.cagri, len(self.kareler) - 1)]
        self.cagri += 1
        return sonuc


class SahteAkis(QtCore.QObject):
    bloklar_hazir = QtCore.Signal(object)
    ceviri_hazir = QtCore.Signal(object, object)
    hata = QtCore.Signal(str)
    dil_algilandi = QtCore.Signal(str, bool)

    def __init__(self) -> None:
        super().__init__()
        self.okunan: list[Frame] = []
        self.cevrilen: list[list[TextBlock]] = []
        self.iptal_sayisi = 0
        self.kapat_sayisi = 0

    def oku(self, frame: Frame) -> None:
        self.okunan.append(frame)

    def cevir(self, bloklar: list[TextBlock]) -> None:
        self.cevrilen.append(bloklar)

    def iptal(self) -> None:
        self.iptal_sayisi += 1

    def kapat(self) -> None:
        self.kapat_sayisi += 1


def test_degisen_alani_okur_ve_ceviriyi_gosterir(qtbot: QtBot) -> None:
    akis = SahteAkis()
    pencere = BolgePenceresi(SahteServis([kare(1)]), Rect(10, 20, 220, 80), akis, otomatik_baslat=False)  # type: ignore[arg-type]
    qtbot.addWidget(pencere)

    pencere._tik()
    assert [k.seq for k in akis.okunan] == [1] and pencere.mesgul
    blok = TextBlock("Open the west door.", Rect(15, 25, 180, 20), 0.98)
    akis.bloklar_hazir.emit([blok])
    assert akis.cevrilen == [[blok]]
    segment = Segment("Open the west door.", Rect(15, 25, 180, 20))
    akis.ceviri_hazir.emit([segment], ["Batı kapısını aç."])

    assert pencere._ceviri.text() == "Batı kapısını aç."
    assert pencere._kaynak.text() == "Open the west door."
    assert not pencere.mesgul and pencere._durum.text() == "Alan izleniyor"


def test_pencere_bolgeye_yapisik_cercevesiz_saydam_serittir(qtbot: QtBot) -> None:
    akis = SahteAkis()
    pencere = BolgePenceresi(
        SahteServis([kare(1)]),
        Rect(100, 300, 500, 100),
        akis,
        ekran_siniri=Rect(0, 0, 1920, 1080),
        otomatik_baslat=False,
    )  # type: ignore[arg-type]
    qtbot.addWidget(pencere)
    pencere.show()

    assert pencere.geometry() == QtCore.QRect(100, 180, 500, 112)
    assert pencere.windowFlags() & QtCore.Qt.WindowType.FramelessWindowHint
    assert pencere.windowFlags() & QtCore.Qt.WindowType.WindowStaysOnTopHint
    assert pencere.testAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
    assert pencere._ceviri.isVisible()
    assert not pencere.araclar_gorunur


def test_araclar_yalniz_fare_uzerindeyken_gorunur(qtbot: QtBot) -> None:
    pencere = BolgePenceresi(
        SahteServis([kare(1)]), Rect(100, 300, 500, 100), SahteAkis(),
        ekran_siniri=Rect(0, 0, 1920, 1080), otomatik_baslat=False,
    )  # type: ignore[arg-type]
    qtbot.addWidget(pencere)
    pencere.show()

    QtWidgets.QApplication.sendEvent(pencere, QtCore.QEvent(QtCore.QEvent.Type.Enter))
    assert pencere.araclar_gorunur and pencere._ceviri.isVisible()
    QtWidgets.QApplication.sendEvent(pencere, QtCore.QEvent(QtCore.QEvent.Type.Leave))
    assert not pencere.araclar_gorunur and pencere._ceviri.isVisible()


def test_is_sururken_yalniz_en_son_degisen_kare_bekler(qtbot: QtBot) -> None:
    akis = SahteAkis()
    servis = SahteServis([kare(1, 0), kare(2, 255), kare(3, 255)])
    pencere = BolgePenceresi(servis, Rect(10, 20, 220, 80), akis,
                             dedektor=ChangeDetector(threshold=0, stable_frames=1), otomatik_baslat=False)  # type: ignore[arg-type]
    qtbot.addWidget(pencere)
    pencere._tik()
    pencere._tik()
    assert [k.seq for k in akis.okunan] == [1]
    akis.bloklar_hazir.emit([])
    qtbot.waitUntil(lambda: len(akis.okunan) == 2)
    assert [k.seq for k in akis.okunan] == [1, 2]


def test_duraklat_kaynak_ve_dil_kontrolleri(qtbot: QtBot) -> None:
    akis = SahteAkis()
    pencere = BolgePenceresi(SahteServis([kare(1)]), Rect(10, 20, 220, 80), akis, otomatik_baslat=False)  # type: ignore[arg-type]
    qtbot.addWidget(pencere)
    pencere.duraklat_devam_et()
    pencere._tik()
    assert pencere.duraklatildi and akis.okunan == [] and pencere._duraklat.text() == "Devam et"
    pencere.kaynagi_degistir()
    assert not pencere._kaynak.isHidden() and pencere._kaynak_dugmesi.text() == "Kaynağı gizle"
    pencere.dil_goster("english", True)
    assert pencere._dil.text() == "Dil: İngilizce?"


def test_kapanis_akisi_durdurur_yeniden_sec_sinyali_verir(qtbot: QtBot) -> None:
    akis = SahteAkis()
    pencere = BolgePenceresi(SahteServis([kare(1)]), Rect(10, 20, 220, 80), akis, otomatik_baslat=False)  # type: ignore[arg-type]
    qtbot.addWidget(pencere)
    yeniden: list[bool] = []
    pencere.yeniden_sec_istendi.connect(lambda: yeniden.append(True))
    pencere._yeniden_sec.click()
    assert yeniden == [True] and akis.iptal_sayisi == 1 and akis.kapat_sayisi == 1
