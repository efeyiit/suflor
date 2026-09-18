"""Suflor pencerelerinin ekran yakalamalarinda gorunmemesi."""
from __future__ import annotations

import pytest
from PySide6 import QtWidgets
from pytestqt.qtbot import QtBot

from demo.kabuk import _guvenli_tam_yakala
from src.ui.yakalama_gizliligi import WDA_EXCLUDEFROMCAPTURE, YakalamaGizliligi


def test_koru_windows_exclude_from_capture_degerini_kullanir(qtbot: QtBot) -> None:
    cagrilar: list[tuple[int, int]] = []
    gizlilik = YakalamaGizliligi(set_affinity=lambda hwnd, deger: cagrilar.append((hwnd, deger)) or True)
    pencere = QtWidgets.QWidget()
    qtbot.addWidget(pencere)
    pencere.show()

    assert gizlilik.koru(pencere)
    assert cagrilar == [(int(pencere.winId()), WDA_EXCLUDEFROMCAPTURE)]
    assert WDA_EXCLUDEFROMCAPTURE == 0x11


def test_uygulamaya_kur_sonradan_acilan_ust_pencereyi_de_korur(
    qtbot: QtBot, qapp: QtWidgets.QApplication
) -> None:
    cagrilar: list[int] = []
    gizlilik = YakalamaGizliligi(set_affinity=lambda hwnd, _deger: cagrilar.append(hwnd) or True)
    gizlilik.uygulamaya_kur(qapp)
    pencere = QtWidgets.QWidget()
    qtbot.addWidget(pencere)

    pencere.show()
    qtbot.waitUntil(lambda: int(pencere.winId()) in cagrilar)

    assert int(pencere.winId()) in cagrilar


def test_yakala_koruma_basarisizsa_gorunenleri_gizleyip_geri_getirir(qtbot: QtBot) -> None:
    pencere = QtWidgets.QWidget()
    gizli = QtWidgets.QWidget()
    qtbot.addWidget(pencere)
    qtbot.addWidget(gizli)
    pencere.show()
    beklemeler: list[bool] = []
    gizlilik = YakalamaGizliligi(set_affinity=lambda *_: False, compositor_wait=lambda: beklemeler.append(True))

    sonuc = gizlilik.yakala(lambda: (pencere.isVisible(), gizli.isVisible()), [pencere, gizli])

    assert sonuc == (False, False)
    assert pencere.isVisible() and not gizli.isVisible()
    assert beklemeler == [True]


def test_yakala_hata_olsa_da_onceki_gorunurlugu_geri_yukler(qtbot: QtBot) -> None:
    pencere = QtWidgets.QWidget()
    qtbot.addWidget(pencere)
    pencere.show()
    gizlilik = YakalamaGizliligi(set_affinity=lambda *_: False, compositor_wait=lambda: None)

    def patla() -> object:
        assert not pencere.isVisible()
        raise RuntimeError("capture failed")

    with pytest.raises(RuntimeError, match="capture failed"):
        gizlilik.yakala(patla, [pencere])
    assert pencere.isVisible()


def test_butun_pencereler_korunuyorsa_gizlemeden_yakalar(qtbot: QtBot) -> None:
    pencere = QtWidgets.QWidget()
    qtbot.addWidget(pencere)
    pencere.show()
    beklemeler: list[bool] = []
    gizlilik = YakalamaGizliligi(set_affinity=lambda *_: True, compositor_wait=lambda: beklemeler.append(True))

    assert gizlilik.yakala(lambda: pencere.isVisible(), [pencere]) is True
    assert pencere.isVisible() and beklemeler == []


def test_kabuk_tam_ekran_yakalamayi_gizlilik_servisinden_gecirir() -> None:
    class Servis:
        def __init__(self) -> None:
            self.indeksler: list[int] = []

        def capture_full(self, indeks: int) -> str:
            self.indeksler.append(indeks)
            return "kare"

    class Gizlilik:
        def __init__(self) -> None:
            self.pencereler: list[object] = []

        def yakala(self, capture: object, pencereler: object) -> object:
            self.pencereler = list(pencereler)  # type: ignore[arg-type]
            return capture()  # type: ignore[operator]

    servis, gizlilik = Servis(), Gizlilik()
    pencereler = [object(), object()]

    assert _guvenli_tam_yakala(servis, 2, gizlilik, pencereler) == "kare"  # type: ignore[arg-type]
    assert servis.indeksler == [2] and gizlilik.pencereler == pencereler
