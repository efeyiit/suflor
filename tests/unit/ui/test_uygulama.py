"""T-012 K1 (▲ Y1) -- `src.ui.uygulama.calistir` giris noktasi ve `python -m src.ui`.

`calistir` `QApplication` kurar (varsa yeniden kullanir), `setQuitOnLastWindowClosed(False)`,
`AnaPencere` gosterir, `cikis_istendi -> app.quit` baglar ve `calistirici(app, pencere)`yi
calistirir (varsayilan `app.exec()`). Testte calistirici ENJEKTE edilir; `quit` baglantisi
gercek `app.exec()` ile olculur (`kapat()` 0 ms sonra -> exec 3000 ms guvenlik siniri
dolmadan doner).
"""
from __future__ import annotations

import runpy
import time

import pytest
from PySide6 import QtCore, QtWidgets
from pytestqt.qtbot import QtBot

from src.ui import uygulama
from src.ui.geometri import Kenar
from src.ui.kabuk import AnaPencere, KabukDurumu
from src.ui.uygulama import calistir


def test_calistir_uygulamayi_kurar_ve_calistiriciyi_cagirir(qtbot: QtBot, qapp: QtWidgets.QApplication) -> None:
    eski = qapp.quitOnLastWindowClosed()
    gorulen: list[tuple[QtWidgets.QApplication, AnaPencere, bool]] = []

    def calistirici(app: QtWidgets.QApplication, pencere: AnaPencere) -> int:
        gorulen.append((app, pencere, app.quitOnLastWindowClosed()))
        assert pencere.isVisible() and pencere.durum is KabukDurumu.GORUNUR
        assert pencere.sekme.kenar is Kenar.SOL
        pencere.kapat()
        return 42

    try:
        assert calistir(["suflor"], kenar=Kenar.SOL, calistirici=calistirici) == 42
    finally:
        qapp.setQuitOnLastWindowClosed(eski)
    assert len(gorulen) == 1
    app, pencere, quit_on_last = gorulen[0]
    assert app is qapp and quit_on_last is False
    assert pencere.kapandi is True and not pencere.isVisible() and not pencere.sekme.isVisible()


def test_calistir_cikis_istendi_quit_baglar_gercek_exec(qtbot: QtBot, qapp: QtWidgets.QApplication) -> None:
    eski = qapp.quitOnLastWindowClosed()
    sure: list[float] = []

    def calistirici(app: QtWidgets.QApplication, pencere: AnaPencere) -> int:
        QtCore.QTimer.singleShot(0, pencere.kapat)  # cikis_istendi -> quit bagli ise exec hemen doner
        QtCore.QTimer.singleShot(3000, app.quit)  # guvenlik: bagli degilse 3 s sonra doner
        t0 = time.perf_counter()
        rc = app.exec()
        sure.append((time.perf_counter() - t0) * 1000)
        return rc

    try:
        assert calistir(None, calistirici=calistirici) == 0
    finally:
        qapp.setQuitOnLastWindowClosed(eski)
    assert sure and sure[0] < 2000, sure
    qtbot.wait(10)  # exec sonrasi olay dongusu hala calisiyor (quitNow sifirlandi)


def test_calistir_varsayilan_kenar_sag(qtbot: QtBot, qapp: QtWidgets.QApplication) -> None:
    eski = qapp.quitOnLastWindowClosed()
    kenarlar: list[Kenar] = []

    def calistirici(app: QtWidgets.QApplication, pencere: AnaPencere) -> int:
        kenarlar.append(pencere.sekme.kenar)
        pencere.kapat()
        return 0

    try:
        calistir(calistirici=calistirici)
    finally:
        qapp.setQuitOnLastWindowClosed(eski)
    assert kenarlar == [Kenar.SAG]


def test_main_modulu_calistir_i_cagirir(monkeypatch: pytest.MonkeyPatch) -> None:
    cagrilar: list[object] = []

    def sahte(argv: object = None, **kw: object) -> int:
        cagrilar.append(argv)
        return 7

    monkeypatch.setattr(uygulama, "calistir", sahte)
    with pytest.raises(SystemExit) as hata:
        runpy.run_module("src.ui", run_name="__main__", alter_sys=True)
    assert hata.value.code == 7 and len(cagrilar) == 1
