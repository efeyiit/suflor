"""TESTER-B -- T-006 mercek B, tur 2: teslim edilen `_k7_kanal_olcusu`nun SINIRLARI.

Teslimdeki olcu fonksiyonu DOSYADAN yuklenir (tests/ paket degil) ve gercek
motor sinifi / kacis-yolu sahteleriyle ayni fonksiyondan gecirilir. Her test
bir soruya cevap verir:

  * B2-2  : gercek `RapidOcrEngine` sinifi + kanala yazan TANIYICI -> olcu DUSER mi
            (sahte motor sinifi degil, gercek motor + enjekte tanıyıcı; src'ye
            dokunmadan "olcu gercek motorda atesliyor" kaniti)
  * B2-1  : R05 (`RapidOCR` handler'larinin `.stream`ine dogrudan yazma) teslim
            kurulumuyla neden KACIYOR: `_kutuphane_gibi_kur` gercek kutuphanenin
            `StreamHandler()`ini eklemiyor. Eklenince ayni olcu yakaliyor.
  * B2-1  : R04 (kok handler `.stream`) -- `.records` gormez, `caplog.text` gorur.
  * B2-1  : BOS kare noktasi -- olcu orada kosmuyor; kossaydi atesler miydi.

Kosum: python -m pytest .agents/tasks/T-006/tester_B/test_mercek_B_r2.py -v -p no:cacheprovider
"""
from __future__ import annotations

import importlib.util
import logging
import os
import sys
import types
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

import tb_bariyer as tb_conftest
from src.contracts.interfaces import OcrEngine
from src.contracts.models import Frame, OcrPreset, TextBlock

DEPO = tb_conftest._KOK
TEST_KAYNAK = DEPO / "tests" / "unit" / "ocr" / "test_rapid_engine.py"
LOGGER_ADI = "RapidOCR"


def _teslim_modulu() -> types.ModuleType:
    """Teslim edilen test dosyasini duz modul olarak yukler (fixture kaydi yok, assert-rewrite yok)."""
    spec = importlib.util.spec_from_file_location("t006_teslim_test_modulu", TEST_KAYNAK)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


T = _teslim_modulu()
NOB: tuple[str, str] = T.NOBETCILER
OLCU = T._k7_kanal_olcusu


@pytest.fixture
def rapidocr_logger_geri_al() -> Iterator[None]:
    lg = logging.getLogger(LOGGER_ADI)
    eski = (lg.level, lg.propagate, list(lg.handlers))
    yield
    lg.setLevel(eski[0])
    lg.propagate = eski[1]
    lg.handlers[:] = eski[2]


def _blok(metin: str) -> TextBlock:
    return T._blok(metin)


# ---------------------------------------------------------------------------
# B2-2 -- olcu GERCEK motor sinifinda atesliyor mu (sahte motor sinifi DEGIL)
# ---------------------------------------------------------------------------


def _gercek_motor_su_taniyiciyla(tmp_path: Path, tani: Any) -> Any:
    f = T.SahteFabrika(taniyici=tani, kurulumda=T._kutuphane_gibi_kur)
    return T.motor(tmp_path, f)


def test_r2_b22_gercek_motor_stdout_yazan_taniyici_olcu_duser(
    tmp_path: Path, capfd: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture, rapidocr_logger_geri_al: None
) -> None:
    def _tani(_img: Any) -> Any:
        sys.stdout.write(NOB[0])
        return T._nobetci_ciktisi()

    with pytest.raises(AssertionError, match="stdout'a"):
        OLCU(_gercek_motor_su_taniyiciyla(tmp_path, _tani), capfd, caplog)
    capfd.readouterr()


def test_r2_b22_gercek_motor_fd2_yazan_taniyici_olcu_duser(
    tmp_path: Path, capfd: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture, rapidocr_logger_geri_al: None
) -> None:
    def _tani(_img: Any) -> Any:
        os.write(2, NOB[1].encode("utf-8"))  # sys.stderr atlanir
        return T._nobetci_ciktisi()

    with pytest.raises(AssertionError, match="stderr'e"):
        OLCU(_gercek_motor_su_taniyiciyla(tmp_path, _tani), capfd, caplog)
    capfd.readouterr()


def test_r2_b22_gercek_motor_rapidocr_logger_ERROR_seviyesi_olcu_duser(
    tmp_path: Path, capfd: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture, rapidocr_logger_geri_al: None
) -> None:
    """R17 sinifi: motor logger'i ERROR'a cekse de `.error(...)` gecer; olcu seviyeden bagimsiz gormeli."""

    def _tani(_img: Any) -> Any:
        logging.getLogger(LOGGER_ADI).error("blok %s", NOB[1])
        return T._nobetci_ciktisi()

    with pytest.raises(AssertionError, match="log kaydina"):
        OLCU(_gercek_motor_su_taniyiciyla(tmp_path, _tani), capfd, caplog)
    caplog.clear()


def test_r2_b22_gercek_motor_sessiz_taniyici_olcu_gecer(
    tmp_path: Path, capfd: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture, rapidocr_logger_geri_al: None
) -> None:
    """Negatif kontrol: ayni duzenek, yazmayan tanıyıcı -> gecer (yanlis pozitif yok)."""
    bloklar = OLCU(_gercek_motor_su_taniyiciyla(tmp_path, lambda _img: T._nobetci_ciktisi()), capfd, caplog)
    assert [b.text for b in bloklar] == list(NOB)


# ---------------------------------------------------------------------------
# B2-1 -- R05: `RapidOCR` handler `.stream`ine DOGRUDAN yazma
# ---------------------------------------------------------------------------


class _RapidocrHandlerStreamineYazan(OcrEngine):
    def recognize(self, frame: Frame, preset: OcrPreset) -> list[TextBlock]:
        for h in logging.getLogger(LOGGER_ADI).handlers:
            if hasattr(h, "stream"):
                h.stream.write(NOB[0])
        return [_blok(NOB[0])]


def test_r2_b21_R05_teslim_kurulumuyla_KACAR_cunku_streamhandler_yok(
    capfd: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture, rapidocr_logger_geri_al: None
) -> None:
    """Teslimdeki `_kutuphane_gibi_kur`: INFO + propagate=False, handler YOK.

    Olcu `caplog.handler`i takar; sahte onun `.stream`ine (StringIO) yazar -> ne fd'de
    ne `.records`ta gorunur -> olcu GECER (kacis). Ama `caplog.text` tasir.
    """
    T._kutuphane_gibi_kur()
    assert logging.getLogger(LOGGER_ADI).handlers == []  # teslimdeki kurulumun durumu
    OLCU(_RapidocrHandlerStreamineYazan(), capfd, caplog)  # gecti = kacis
    assert NOB[0] in caplog.text  # tek satirlik keskinlestirme burada yakalardi


def test_r2_b21_R05_gercek_kutuphane_gibi_streamhandler_eklenince_YAKALANIR(
    capfd: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture, rapidocr_logger_geri_al: None
) -> None:
    """rapidocr/utils/log.py: `StreamHandler()` (stderr) + INFO + propagate=False. Ayni olcu, ayni sahte -> DUSER."""
    T._kutuphane_gibi_kur()
    logging.getLogger(LOGGER_ADI).addHandler(logging.StreamHandler())  # gercek kutuphane boyle kurar
    with pytest.raises(AssertionError, match="stderr'e"):
        OLCU(_RapidocrHandlerStreamineYazan(), capfd, caplog)
    capfd.readouterr()


def test_r2_b21_M28b_streamhandler_varken_iki_kanaldan_gorunur(
    capfd: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture, rapidocr_logger_geri_al: None
) -> None:
    """Gercek kurulumda `RapidOCR.info(metin)` hem handler->stderr hem caplog'a duser; olcu ilk assert'te (stderr) durur."""
    T._kutuphane_gibi_kur()
    logging.getLogger(LOGGER_ADI).addHandler(logging.StreamHandler())

    class _M28b(OcrEngine):
        def recognize(self, frame: Frame, preset: OcrPreset) -> list[TextBlock]:
            logging.getLogger(LOGGER_ADI).info("blok %s", NOB[1])
            return [_blok(NOB[1])]

    with pytest.raises(AssertionError, match="stderr'e"):
        OLCU(_M28b(), capfd, caplog)
    capfd.readouterr()
    caplog.clear()


# ---------------------------------------------------------------------------
# B2-1 -- R04: KOK handler `.stream`ine dogrudan yazma
# ---------------------------------------------------------------------------


class _KokHandlerStreamineYazan(OcrEngine):
    def recognize(self, frame: Frame, preset: OcrPreset) -> list[TextBlock]:
        for h in logging.getLogger().handlers:
            if hasattr(h, "stream"):
                h.stream.write(NOB[0])
        return [_blok(NOB[0])]


def test_r2_b21_R04_kok_handler_stream_records_gormez_caplog_text_gorur(
    capfd: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture
) -> None:
    kok_handlerlar = [type(h).__name__ for h in logging.getLogger().handlers]
    OLCU(_KokHandlerStreamineYazan(), capfd, caplog)  # gecti = kacis
    assert NOB[0] in caplog.text, kok_handlerlar  # `.text` kontrolu eklenseydi yakalanirdi


# ---------------------------------------------------------------------------
# B2-1 -- BOS kare noktasi (olcu bu noktada kosmuyor; kossaydi?)
# ---------------------------------------------------------------------------


def test_r2_b21_bos_kare_noktasi_gercek_motor_temiz(
    tmp_path: Path, capfd: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture, rapidocr_logger_geri_al: None
) -> None:
    bloklar = OLCU(_gercek_motor_su_taniyiciyla(tmp_path, lambda _img: T.SahteCikti()), capfd, caplog)
    assert bloklar == []


def test_r2_b21_bos_kare_noktasinda_yazan_taniyici_olcu_duser(
    tmp_path: Path, capfd: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture, rapidocr_logger_geri_al: None
) -> None:
    """R10b sinifi: bos karede fd 2'ye yazma. Olcu bos kare noktasinda kossaydi yakalardi (ucuncu nokta ucuz)."""

    def _tani(_img: Any) -> Any:
        open(2, "w", closefd=False, encoding="utf-8").write("bos kare\n")
        return T.SahteCikti()

    with pytest.raises(AssertionError, match="stderr'e"):
        OLCU(_gercek_motor_su_taniyiciyla(tmp_path, _tani), capfd, caplog)
    capfd.readouterr()
