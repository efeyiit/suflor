"""T-014 -- AnlikPencere K1-K7 (offscreen; kare sentetik, pipeline yok)."""
from __future__ import annotations

import time
from collections.abc import Iterator

import numpy as np
import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from pytestqt.qtbot import QtBot

from src.contracts.models import Frame, Rect, Segment, TextBlock
from src.ui.anlik_pencere import TIK_ESIGI_PX, AnlikDurumu, AnlikPencere


def kare(w: int = 800, h: int = 600, x: int = 0, y: int = 0) -> Frame:
    img = np.zeros((h, w, 3), dtype=np.uint8)
    img[:, :, 0] = 30
    return Frame(image=img, rect=Rect(x, y, w, h), captured_at=1.0, seq=1)


def blok(metin: str, x: int, y: int, w: int = 120, h: int = 24) -> TextBlock:
    return TextBlock(text=metin, bbox=Rect(x, y, w, h), confidence=0.9)


BLOKLAR = [blok("bir", 100, 100), blok("iki", 100, 200), blok("uc", 400, 300)]


@pytest.fixture
def pencere(qtbot: QtBot) -> Iterator[AnlikPencere]:
    ekran = QGuiApplication.primaryScreen()
    p = AnlikPencere(ekran, kare(ekran.geometry().width(), ekran.geometry().height()))
    qtbot.addWidget(p)
    p.show()
    qtbot.waitExposed(p)
    yield p


def merkez(p: AnlikPencere, b: TextBlock) -> QPoint:
    return p._pencereye(b.bbox).center()


# ---------------------------------------------------------------- K1 geometri
def test_k1_pencere_ekranla_birebir_ve_cercevesiz_ustte(pencere: AnlikPencere) -> None:
    g = QGuiApplication.primaryScreen().geometry()
    assert pencere.geometry() == g
    b = pencere.windowFlags()
    assert bool(b & Qt.WindowType.FramelessWindowHint) and bool(b & Qt.WindowType.WindowStaysOnTopHint)


def test_k1_kare_ofseti_ve_olcek_pencere_koordinatina(qtbot: QtBot) -> None:
    ekran = QGuiApplication.primaryScreen()
    g = ekran.geometry()
    # kare ekranin iki kati cozunurlukte (dpr 2 benzeri) ve ofsetli -> olcek 0.5, ofset dusuluyor
    p = AnlikPencere(ekran, kare(g.width() * 2, g.height() * 2, x=1000, y=500))
    qtbot.addWidget(p)
    r = p._pencereye(Rect(1000 + 200, 500 + 100, 400, 60))
    assert (r.x(), r.y(), r.width(), r.height()) == (100, 50, 200, 30)


# ---------------------------------------------------------------- K2 durumlar
def test_k2_durum_akisi_ve_metinleri(pencere: AnlikPencere) -> None:
    assert pencere.durum == AnlikDurumu.OKUNUYOR and "okunuyor" in pencere.durum_metni
    QTest.keyClick(pencere, Qt.Key.Key_Return)             # blok gelmeden Enter: hicbir sey
    assert pencere.durum == AnlikDurumu.OKUNUYOR
    pencere.bloklari_goster(BLOKLAR)
    assert pencere.durum == AnlikDurumu.SECIM and "3" in pencere.durum_metni
    QTest.keyClick(pencere, Qt.Key.Key_Return)             # bos secimle Enter: ipucu, sinyal yok
    assert pencere.durum == AnlikDurumu.SECIM and "seç" in pencere.durum_metni


def test_k2_bos_blok_listesi_metin_bulunamadi(pencere: AnlikPencere) -> None:
    pencere.bloklari_goster([])
    assert pencere.durum == AnlikDurumu.SECIM and "bulunamadı" in pencere.durum_metni


def test_k2_hata_durum_satirina_sinif_adi_ve_yeniden_denenebilir(pencere: AnlikPencere, qtbot: QtBot) -> None:
    pencere.bloklari_goster(BLOKLAR)
    QTest.mouseClick(pencere, Qt.MouseButton.LeftButton, pos=merkez(pencere, BLOKLAR[0]))
    with qtbot.waitSignal(pencere.cevir_istendi, timeout=1000):
        QTest.keyClick(pencere, Qt.Key.Key_Return)
    assert pencere.durum == AnlikDurumu.CEVRILIYOR
    pencere.hata_goster("ProviderUnavailable")
    assert "ProviderUnavailable" in pencere.durum_metni and pencere.durum == AnlikDurumu.SECIM
    with qtbot.waitSignal(pencere.cevir_istendi, timeout=1000):   # yeniden deneme
        QTest.keyClick(pencere, Qt.Key.Key_Return)


def test_k2_gec_gelen_okuma_secimi_bozmaz(pencere: AnlikPencere, qtbot: QtBot) -> None:
    pencere.bloklari_goster(BLOKLAR)
    QTest.mouseClick(pencere, Qt.MouseButton.LeftButton, pos=merkez(pencere, BLOKLAR[1]))
    with qtbot.waitSignal(pencere.cevir_istendi, timeout=1000):
        QTest.keyClick(pencere, Qt.Key.Key_Return)
    pencere.bloklari_goster([blok("baska", 0, 0)])    # cevriliyor'da gelen okuma yok sayilir
    assert pencere.durum == AnlikDurumu.CEVRILIYOR and pencere.bloklar == BLOKLAR


# ---------------------------------------------------------------- K3 secim
def test_k3_tik_acar_kapar(pencere: AnlikPencere) -> None:
    pencere.bloklari_goster(BLOKLAR)
    QTest.mouseClick(pencere, Qt.MouseButton.LeftButton, pos=merkez(pencere, BLOKLAR[2]))
    assert pencere.secili_indeksler() == [2]
    QTest.mouseClick(pencere, Qt.MouseButton.LeftButton, pos=merkez(pencere, BLOKLAR[2]))
    assert pencere.secili_indeksler() == []
    QTest.mouseClick(pencere, Qt.MouseButton.LeftButton, pos=QPoint(700, 550))   # bos alan: degisim yok
    assert pencere.secili_indeksler() == []


def test_k3_surukleme_kesisenleri_ekler_sira_blok_sirasi(pencere: AnlikPencere) -> None:
    pencere.bloklari_goster(BLOKLAR)
    # once uc'u tikla, sonra bir+iki'yi kapsayan dikdortgen surukle -> hepsi, blok sirasiyla
    QTest.mouseClick(pencere, Qt.MouseButton.LeftButton, pos=merkez(pencere, BLOKLAR[2]))
    QTest.mousePress(pencere, Qt.MouseButton.LeftButton, pos=QPoint(90, 90))
    QTest.mouseMove(pencere, QPoint(240, 230))
    QTest.mouseRelease(pencere, Qt.MouseButton.LeftButton, pos=QPoint(240, 230))
    assert pencere.secili_indeksler() == [0, 1, 2]
    assert [b.text for b in pencere.secili_bloklar()] == ["bir", "iki", "uc"]


def test_k3_kisa_surukleme_tik_sayilir(pencere: AnlikPencere) -> None:
    pencere.bloklari_goster(BLOKLAR)
    m = merkez(pencere, BLOKLAR[0])
    QTest.mousePress(pencere, Qt.MouseButton.LeftButton, pos=m)
    QTest.mouseRelease(pencere, Qt.MouseButton.LeftButton, pos=m + QPoint(TIK_ESIGI_PX - 1, 0))
    assert pencere.secili_indeksler() == [0]


def test_k3_ctrl_a_hepsi_ve_enter_secimi_yayar_ikinci_enter_yaymaz(pencere: AnlikPencere, qtbot: QtBot) -> None:
    pencere.bloklari_goster(BLOKLAR)
    QTest.keyClick(pencere, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
    assert pencere.secili_indeksler() == [0, 1, 2]
    with qtbot.waitSignal(pencere.cevir_istendi, timeout=1000) as s:
        QTest.keyClick(pencere, Qt.Key.Key_Return)
    assert s.args[0] == BLOKLAR and pencere.durum == AnlikDurumu.CEVRILIYOR
    gelen: list[object] = []
    pencere.cevir_istendi.connect(gelen.append)
    QTest.keyClick(pencere, Qt.Key.Key_Return)
    QTest.mouseClick(pencere, Qt.MouseButton.LeftButton, pos=merkez(pencere, BLOKLAR[0]))   # cevriliyor'da tik etkisiz
    assert gelen == [] and pencere.secili_indeksler() == [0, 1, 2]


# ---------------------------------------------------------------- K4 sonuc
def secime_gec(p: AnlikPencere, qtbot: QtBot, indeksler: list[int]) -> None:
    p.bloklari_goster(BLOKLAR)
    for i in indeksler:
        QTest.mouseClick(p, Qt.MouseButton.LeftButton, pos=merkez(p, BLOKLAR[i]))
    with qtbot.waitSignal(p.cevir_istendi, timeout=1000):
        QTest.keyClick(p, Qt.Key.Key_Return)


def test_k4_ceviri_sonuclari_ve_yerlesim(pencere: AnlikPencere, qtbot: QtBot) -> None:
    secime_gec(pencere, qtbot, [0, 1])
    seg = Segment(text="bir iki", bbox=Rect(100, 100, 120, 124), source_blocks=(0, 1))
    pencere.ceviriyi_goster([seg], ["one two"])
    assert pencere.durum == AnlikDurumu.SONUC and pencere.sonuclar() == [("bir iki", "one two")]
    kutu = pencere._sonuclar[0][2]
    assert kutu.top() == 100 and kutu.bottom() >= 200   # iki blogun birlesimi (secim listesindeki 0 ve 1)
    assert "1 çeviri" in pencere.durum_metni
    pencere.grab()   # cizim cokmuyor


def test_k4_ctrl_c_ceviriyi_panoya_kopyalar(pencere: AnlikPencere, qtbot: QtBot) -> None:
    secime_gec(pencere, qtbot, [2])
    pencere.ceviriyi_goster([Segment(text="uc", bbox=BLOKLAR[2].bbox, source_blocks=(0,))], ["three"])
    QTest.keyClick(pencere, Qt.Key.Key_C, Qt.KeyboardModifier.ControlModifier)
    assert QApplication.clipboard().text() == "three" and pencere.durum_metni == "kopyalandı"


def test_k4_secim_disinda_ceviri_yok_sayilir(pencere: AnlikPencere) -> None:
    pencere.bloklari_goster(BLOKLAR)
    pencere.ceviriyi_goster([Segment(text="x", bbox=Rect(0, 0, 1, 1))], ["y"])   # cevriliyor degil
    assert pencere.durum == AnlikDurumu.SECIM and pencere.sonuclar() == []


def test_k4_bos_ceviri_listesi(pencere: AnlikPencere, qtbot: QtBot) -> None:
    secime_gec(pencere, qtbot, [0])
    pencere.ceviriyi_goster([], [])
    assert pencere.durum == AnlikDurumu.SONUC and "yok" in pencere.durum_metni


# ---------------------------------------------------------------- K5 kapanis
def test_k5_esc_iptal_bir_kez_ve_kapanir(pencere: AnlikPencere, qtbot: QtBot) -> None:
    gelen: list[int] = []
    pencere.iptal.connect(lambda: gelen.append(1))
    QTest.keyClick(pencere, Qt.Key.Key_Escape)
    qtbot.waitUntil(lambda: not pencere.isVisible(), timeout=1000)
    pencere.close()
    assert gelen == [1]


def test_k5_close_iptal_yayar(pencere: AnlikPencere, qtbot: QtBot) -> None:
    with qtbot.waitSignal(pencere.iptal, timeout=1000):
        pencere.close()


# ---------------------------------------------------------------- K6 cizim
def test_k6_paint_tum_durumlarda_cokmez_ve_hizli(pencere: AnlikPencere, qtbot: QtBot) -> None:
    pencere.grab()
    pencere.bloklari_goster(BLOKLAR)
    QTest.mousePress(pencere, Qt.MouseButton.LeftButton, pos=QPoint(50, 50))
    QTest.mouseMove(pencere, QPoint(300, 300))
    pencere.grab()   # surukleme dikdortgeni ciziliyor
    QTest.mouseRelease(pencere, Qt.MouseButton.LeftButton, pos=QPoint(300, 300))
    with qtbot.waitSignal(pencere.cevir_istendi, timeout=1000):
        QTest.keyClick(pencere, Qt.Key.Key_Return)
    pencere.ceviriyi_goster([Segment(text="bir", bbox=BLOKLAR[0].bbox, source_blocks=(0,))], ["cok uzun bir ceviri metni " * 8])
    sureler = []
    for _ in range(5):
        t0 = time.perf_counter(); pencere.grab(); sureler.append((time.perf_counter() - t0) * 1000)
    assert min(sureler) < 200   # offscreen tam ekran grab; gercek < 16 ms real_check'te


def test_k7_odak_alir(pencere: AnlikPencere) -> None:
    assert pencere.focusPolicy() == Qt.FocusPolicy.StrongFocus
