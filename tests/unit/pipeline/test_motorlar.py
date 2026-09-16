"""T-014 -- MotorDeposu: arka planda kurulum, hazir/hata sinyalleri, hazir olmadan erisim reddi."""
from __future__ import annotations

import time

import pytest
from pytestqt.qtbot import QtBot

from src.contracts.errors import ModelMissingError
from src.contracts.interfaces import FakeOcrEngine, FakeProvider
from src.pipeline.motorlar import MotorDeposu


def yavas_ocr() -> FakeOcrEngine:
    time.sleep(0.15)
    return FakeOcrEngine()


def test_hazir_sinyali_ve_erisim(qtbot: QtBot) -> None:
    d = MotorDeposu((yavas_ocr, FakeProvider, lambda: None))
    assert not d.hazir_mi
    with pytest.raises(RuntimeError):
        _ = d.ocr
    t0 = time.perf_counter(); d.baslat(); sure = (time.perf_counter() - t0) * 1000
    assert sure < 20   # UI bloklanmadi
    with qtbot.waitSignal(d.hazir, timeout=3000):
        pass
    assert d.hazir_mi and isinstance(d.ocr, FakeOcrEngine) and isinstance(d.cevirici, FakeProvider) and d.sozluk is None
    d.baslat()   # ikinci baslat sessiz
    d.kapat(); d.kapat()


def test_kurulum_hatasi_sinif_adiyla(qtbot: QtBot) -> None:
    def patlar() -> FakeOcrEngine:
        raise ModelMissingError("gizli yol")

    d = MotorDeposu((patlar, FakeProvider, lambda: None))
    with qtbot.waitSignal(d.hata, timeout=3000) as s:
        d.baslat()
    assert s.args == ["ModelMissingError"] and not d.hazir_mi
    with pytest.raises(RuntimeError):
        _ = d.cevirici
    d.kapat()


def test_kapat_saglayiciyi_kapatir(qtbot: QtBot) -> None:
    kapandi: list[int] = []

    class Kapanan(FakeProvider):
        def close(self) -> None:
            kapandi.append(1)

    d = MotorDeposu((FakeOcrEngine, Kapanan, lambda: None))
    with qtbot.waitSignal(d.hazir, timeout=3000):
        d.baslat()
    d.kapat()
    assert kapandi == [1]
