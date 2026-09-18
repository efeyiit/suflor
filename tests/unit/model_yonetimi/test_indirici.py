"""Kalite modeli indirmesinin arayüzü bloklamayan köprüsü."""
from __future__ import annotations

import threading

from pytestqt.qtbot import QtBot

from src.model_yonetimi.indirici import KaliteModeliIndirici


def test_arka_planda_ilerleme_ve_hazir_sinyali(qtbot: QtBot) -> None:
    ana_thread = threading.get_ident()
    calisan_thread: list[int] = []

    def indir(progress: object) -> None:
        calisan_thread.append(threading.get_ident())
        progress(5, 10)  # type: ignore[operator]

    kopru = KaliteModeliIndirici(indir)
    ilerleme: list[tuple[int, int]] = []
    kopru.ilerleme.connect(lambda a, b: ilerleme.append((a, b)))
    with qtbot.waitSignal(kopru.hazir, timeout=2000):
        assert kopru.baslat()
    assert calisan_thread[0] != ana_thread and ilerleme == [(5, 10)] and not kopru.calisiyor


def test_calisirken_ikinci_baslatma_reddedilir(qtbot: QtBot) -> None:
    devam = threading.Event()
    basladi = threading.Event()

    def indir(_progress: object) -> None:
        basladi.set(); devam.wait(2)

    kopru = KaliteModeliIndirici(indir)
    assert kopru.baslat()
    assert basladi.wait(1) and not kopru.baslat()
    with qtbot.waitSignal(kopru.hazir, timeout=2000):
        devam.set()


def test_hata_yalniz_sinif_adiyla_bildirilir(qtbot: QtBot) -> None:
    def indir(_progress: object) -> None:
        raise RuntimeError("gizli ağ adresi")

    kopru = KaliteModeliIndirici(indir)
    with qtbot.waitSignal(kopru.hata, timeout=2000) as sinyal:
        kopru.baslat()
    assert sinyal.args == ["RuntimeError"]

