"""T-012 K2/K3/K4/K6/K8 -- `src.ui.kenar_sekmesi.KenarSekmesi` (pytest-qt, offscreen).

Imlec ENJEKTE edilir (`SahteImlec`: cagri sayan callable). Zaman sinirlari
gevsek ust sinir (`acilma_ms + 2*yoklama_ms + 300`) + deterministik alt
sinir (`qtbot.wait(acilma_ms // 2)` sonra hala kapali: QTimer erken
ateslemez). Sikı sayilar yalniz gercek ekranda (`real_check.py`).
"""
from __future__ import annotations

import gc
import statistics
import time
import weakref
from collections.abc import Callable, Iterator

import pytest
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtTest import QTest
from pytestqt.qtbot import QtBot

from src.ui.geometri import PANEL_BOYUTU, Kenar, sekme_acik_dikdortgeni, sekme_icinde, sekme_kapali_dikdortgeni, y_sinirla
from src.ui.kenar_sekmesi import KenarSekmesi

Qt = QtCore.Qt
SOL_DUGME = Qt.MouseButton.LeftButton
SAG_DUGME = Qt.MouseButton.RightButton
UZAK = QtCore.QPoint(5, 5)  # sekmeden uzak bir nokta (ekranin sol ustu)



def _bas(w: QtWidgets.QWidget, dugme: QtCore.Qt.MouseButton, pos: QtCore.QPoint) -> None:
    QTest.mousePress(w, dugme, QtCore.Qt.KeyboardModifier.NoModifier, pos)


def _birak(w: QtWidgets.QWidget, dugme: QtCore.Qt.MouseButton, pos: QtCore.QPoint) -> None:
    QTest.mouseRelease(w, dugme, QtCore.Qt.KeyboardModifier.NoModifier, pos)


def _tasi(w: QtWidgets.QWidget, pos: QtCore.QPoint) -> None:
    QTest.mouseMove(w, pos)


def _tikla(w: QtWidgets.QWidget, dugme: QtCore.Qt.MouseButton) -> None:
    QTest.mouseClick(w, dugme, QtCore.Qt.KeyboardModifier.NoModifier, w.rect().center())


class SahteImlec:
    """Enjekte edilen imlec: `nokta`yi dondurur, her cagriyi sayar."""

    def __init__(self) -> None:
        self.nokta = QtCore.QPoint(UZAK)
        self.sayac = 0

    def __call__(self) -> QtCore.QPoint:
        self.sayac += 1
        return QtCore.QPoint(self.nokta)

    def git(self, nokta: QtCore.QPoint) -> None:
        self.nokta = QtCore.QPoint(nokta)


def _ekran() -> QtGui.QScreen:
    ekran = QtGui.QGuiApplication.primaryScreen()
    assert ekran is not None
    return ekran


def _ust_sinir(s: KenarSekmesi, acilma: bool) -> int:
    return (s.acilma_ms if acilma else s.kapanma_ms) + 2 * s.yoklama_ms + 300


def _merkez(s: KenarSekmesi) -> QtCore.QPoint:
    fg = s.frameGeometry()
    x = fg.right() - 3 if s.kenar is Kenar.SAG else fg.left() + 3
    return QtCore.QPoint(x, fg.center().y())


@pytest.fixture
def sekme(qtbot: QtBot) -> Iterator[tuple[KenarSekmesi, SahteImlec]]:
    imlec = SahteImlec()
    s = KenarSekmesi(_ekran(), imlec_konumu=imlec)
    qtbot.addWidget(s)
    s.show()
    yield s, imlec
    s.hide()


def _ac(qtbot: QtBot, s: KenarSekmesi, imlec: SahteImlec) -> None:
    imlec.git(_merkez(s))
    qtbot.waitUntil(lambda: s.acik, timeout=_ust_sinir(s, True))


# -- yapici, sabitler, dogrulama -----------------------------------------------------------------


def test_k2_varsayilan_sabitler_urun_degerleri(sekme: tuple[KenarSekmesi, SahteImlec]) -> None:
    s, _ = sekme
    assert (s.yaricap, s.acilma_ms, s.kapanma_ms, s.yoklama_ms) == (26, 120, 450, 60)
    assert s.kenar is Kenar.SAG and s.acik is False and s.surukleniyor is False


@pytest.mark.parametrize(
    "kur",
    [
        lambda e: KenarSekmesi(e, yaricap=0),
        lambda e: KenarSekmesi(e, yaricap=-3),
        lambda e: KenarSekmesi(e, acilma_ms=-1),
        lambda e: KenarSekmesi(e, kapanma_ms=-1),
        lambda e: KenarSekmesi(e, yoklama_ms=0),
        lambda e: KenarSekmesi(e, yaricap=PANEL_BOYUTU.height() // 2 + 1),
        lambda e: KenarSekmesi(e, yaricap=2**30),
        lambda e: KenarSekmesi(e, yaricap=2**31),
        lambda e: KenarSekmesi(e, acilma_ms=2**31),
        lambda e: KenarSekmesi(e, kapanma_ms=2**31),
        lambda e: KenarSekmesi(e, yoklama_ms=2**31),
    ],
    ids=["yaricap0", "yaricap-3", "acilma-1", "kapanma-1", "yoklama0",
         "yaricap67-panel-kapsamaz", "yaricap2^30-overflow", "yaricap2^31", "acilma2^31", "kapanma2^31", "yoklama2^31"],
)
def test_k4_gecersiz_parametre_valueerror(qtbot: QtBot, kur: Callable[[QtGui.QScreen], KenarSekmesi]) -> None:
    """Alt VE ust sinirlar `ValueError` (Tester-A D-A3: `2*yaricap <= PANEL_BOYUTU.height()` yoksa panel
    sekmeyi kapsamaz -> salinim; D-A4: `>= 2**30/2**31` `OverflowError` sinifi disiydi)."""
    with pytest.raises(ValueError):
        kur(_ekran())


def test_k4_yaricap_ust_sinir_tam_degeri_kabul(qtbot: QtBot) -> None:
    """`yaricap == PANEL_BOYUTU.height() // 2` (66) kabul: panel kapali sekmeyi tam kapsar."""
    s = KenarSekmesi(_ekran(), yaricap=PANEL_BOYUTU.height() // 2, imlec_konumu=SahteImlec())
    qtbot.addWidget(s)
    g = s.ekran_dikdortgeni
    assert s.yaricap == 66 and s.frameGeometry().size() == QtCore.QSize(66, 132)
    assert sekme_acik_dikdortgeni(g, s.y, s.yaricap, PANEL_BOYUTU, Kenar.SAG).contains(s.frameGeometry())


def test_k4_parametreler_kabul_ve_salt_okunur(qtbot: QtBot) -> None:
    s = KenarSekmesi(_ekran(), kenar=Kenar.SOL, yaricap=30, acilma_ms=10, kapanma_ms=20, yoklama_ms=5)
    qtbot.addWidget(s)
    assert (s.yaricap, s.acilma_ms, s.kapanma_ms, s.yoklama_ms, s.kenar) == (30, 10, 20, 5, Kenar.SOL)
    with pytest.raises(AttributeError):
        s.yaricap = 3  # type: ignore[misc]
    with pytest.raises(AttributeError):
        s.acik = True  # type: ignore[misc]


# -- K3 bayraklar (yapisal; activeWindow offscreen'de OLCULMUYOR) -------------------------------


def test_k3_bayraklar_ve_oznitelikler(sekme: tuple[KenarSekmesi, SahteImlec]) -> None:
    s, _ = sekme
    b = s.windowFlags()
    for bayrak in (Qt.WindowType.FramelessWindowHint, Qt.WindowType.Tool, Qt.WindowType.WindowStaysOnTopHint,
                   Qt.WindowType.WindowDoesNotAcceptFocus):
        assert b & bayrak, bayrak
    assert s.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    assert s.testAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
    assert s.focusPolicy() == Qt.FocusPolicy.NoFocus


def test_k3_kapali_ve_acik_boyutlar(qtbot: QtBot, sekme: tuple[KenarSekmesi, SahteImlec]) -> None:
    s, imlec = sekme
    assert s.frameGeometry().size() == QtCore.QSize(s.yaricap, 2 * s.yaricap)
    _ac(qtbot, s, imlec)
    assert s.frameGeometry().size() == PANEL_BOYUTU


# -- K2 konum: kenara bitisik, dikey orta, sinirlar, sol kenar, availableGeometryChanged --------


def test_k2_kapali_sag_kenara_bitisik_dikey_orta(sekme: tuple[KenarSekmesi, SahteImlec]) -> None:
    s, _ = sekme
    g = _ekran().availableGeometry()
    fg = s.frameGeometry()
    assert fg == sekme_kapali_dikdortgeni(g, g.top() + g.height() // 2 - s.yaricap, s.yaricap, Kenar.SAG)
    assert fg.right() == g.right()
    assert abs(fg.center().y() - g.center().y()) <= 1
    assert s.ekran_dikdortgeni == g


def test_k2_sol_kenar_yapicidan(qtbot: QtBot) -> None:
    s = KenarSekmesi(_ekran(), kenar=Kenar.SOL, imlec_konumu=SahteImlec())
    qtbot.addWidget(s)
    s.show()
    g = _ekran().availableGeometry()
    assert s.frameGeometry().left() == g.left()
    assert s.frameGeometry().size() == QtCore.QSize(26, 52)
    s.hide()


def test_k2_kenar_degisince_yeniden_konumlanir(qtbot: QtBot, sekme: tuple[KenarSekmesi, SahteImlec]) -> None:
    s, imlec = sekme
    g = _ekran().availableGeometry()
    s.kenar = Kenar.SOL
    assert s.kenar is Kenar.SOL and s.frameGeometry().left() == g.left()
    s.kenar = Kenar("sag")
    assert s.kenar is Kenar.SAG and s.frameGeometry().right() == g.right()
    _ac(qtbot, s, imlec)
    s.kenar = Kenar.SOL  # acikken de: panel sol kenara
    assert s.acik and s.frameGeometry() == sekme_acik_dikdortgeni(g, s.y, s.yaricap, PANEL_BOYUTU, Kenar.SOL)


def test_k2_y_yazilinca_sinirlanir_ve_tasinir(sekme: tuple[KenarSekmesi, SahteImlec]) -> None:
    s, _ = sekme
    g = _ekran().availableGeometry()
    s.y = -10_000
    assert s.y == g.top() and s.frameGeometry().top() == g.top()
    s.y = 10_000
    alt = g.bottom() - 2 * s.yaricap + 1
    assert s.y == alt and s.frameGeometry().bottom() == g.bottom()
    s.y = g.top() + 100
    assert s.y == g.top() + 100 and s.frameGeometry().top() == g.top() + 100


def test_k2_acik_panel_ekran_icinde_ust_ve_alt_sinirda(qtbot: QtBot, sekme: tuple[KenarSekmesi, SahteImlec]) -> None:
    s, imlec = sekme
    g = _ekran().availableGeometry()
    for y in (-10_000, 10_000):
        s.y = y
        _ac(qtbot, s, imlec)
        assert g.contains(s.frameGeometry()) and s.frameGeometry().right() == g.right()
        imlec.git(UZAK)
        qtbot.waitUntil(lambda: not s.acik, timeout=_ust_sinir(s, False))


def test_k2_available_geometry_changed_sahte_sinyal_yeni_x(qtbot: QtBot, sekme: tuple[KenarSekmesi, SahteImlec]) -> None:
    ekran = _ekran()
    s, _ = sekme
    eski_y = s.y
    yeni = QtCore.QRect(0, 0, 600, 500)
    assert yeni != ekran.availableGeometry()
    ekran.availableGeometryChanged.emit(yeni)
    assert s.ekran_dikdortgeni == yeni
    assert s.frameGeometry().right() == yeni.right() == 599
    assert s.y == y_sinirla(yeni, eski_y, s.yaricap)
    assert yeni.contains(s.frameGeometry())
    dar = QtCore.QRect(0, 0, 300, 200)  # y yeni sinira sikisir
    ekran.availableGeometryChanged.emit(dar)
    assert s.y == dar.bottom() - 2 * s.yaricap + 1 and dar.contains(s.frameGeometry())
    ekran.availableGeometryChanged.emit(ekran.availableGeometry())  # geri al (paylasilan ekran nesnesi)


# -- K2 cizim: sol kenarda aynali -----------------------------------------------------------------


def _alfa(s: KenarSekmesi, x: int, y: int) -> int:
    return s.grab().toImage().pixelColor(x, y).alpha()


def test_k2_cizim_sag_kenar_sol_kose_saydam(sekme: tuple[KenarSekmesi, SahteImlec]) -> None:
    s, _ = sekme
    r = s.yaricap
    assert _alfa(s, 2, 2) == 0 and _alfa(s, 2, 2 * r - 3) == 0  # ekranin ic tarafindaki koseler saydam
    assert _alfa(s, r - 3, 2) > 0 and _alfa(s, r - 2, r) > 0  # kenar tarafi opak


def test_k2_cizim_sol_kenar_aynali(qtbot: QtBot) -> None:
    s = KenarSekmesi(_ekran(), kenar=Kenar.SOL, imlec_konumu=SahteImlec())
    qtbot.addWidget(s)
    s.show()
    r = s.yaricap
    assert _alfa(s, r - 3, 2) == 0 and _alfa(s, r - 3, 2 * r - 3) == 0  # sag koseler saydam
    assert _alfa(s, 2, 2) > 0 and _alfa(s, 1, r) > 0  # sol (kenar) tarafi opak
    s.hide()


def test_k2_cizim_kenar_degisince_ayna_degisir(sekme: tuple[KenarSekmesi, SahteImlec]) -> None:
    s, _ = sekme
    r = s.yaricap
    assert _alfa(s, 2, 2) == 0 and _alfa(s, r - 3, 2) > 0
    s.kenar = Kenar.SOL
    assert _alfa(s, 2, 2) > 0 and _alfa(s, r - 3, 2) == 0


# -- K4 acilma / kapanma zamanlamasi ------------------------------------------------------------


def test_k4_iceri_gelince_acilir_alt_sinir_deterministik(qtbot: QtBot, sekme: tuple[KenarSekmesi, SahteImlec]) -> None:
    s, imlec = sekme
    imlec.git(_merkez(s))
    qtbot.wait(s.acilma_ms // 2)
    assert s.acik is False  # QTimer erken ateslemez: acilma_ms dolmadan acilamaz
    qtbot.waitUntil(lambda: s.acik, timeout=_ust_sinir(s, True))
    g = _ekran().availableGeometry()
    assert s.frameGeometry() == sekme_acik_dikdortgeni(g, s.y, s.yaricap, PANEL_BOYUTU, Kenar.SAG)


def test_k4_disari_cikinca_kapanir_alt_sinir_deterministik(qtbot: QtBot, sekme: tuple[KenarSekmesi, SahteImlec]) -> None:
    s, imlec = sekme
    _ac(qtbot, s, imlec)
    imlec.git(UZAK)
    qtbot.wait(s.kapanma_ms // 2)
    assert s.acik is True
    qtbot.waitUntil(lambda: not s.acik, timeout=_ust_sinir(s, False))
    assert s.frameGeometry().size() == QtCore.QSize(s.yaricap, 2 * s.yaricap)


def test_k4_iceri_disari_iceri_titremesi_acik_kalir(qtbot: QtBot, sekme: tuple[KenarSekmesi, SahteImlec]) -> None:
    s, imlec = sekme
    _ac(qtbot, s, imlec)
    for _ in range(3):
        imlec.git(UZAK)
        qtbot.wait(100)
        assert s.acik is True
        imlec.git(_merkez(s))
        qtbot.wait(100)
        assert s.acik is True
    qtbot.wait(_ust_sinir(s, False))
    assert s.acik is True  # icerideyken kapanma sayaci durmus olmali


def test_k4_panel_uzerinde_gezinirken_acik_kalir(qtbot: QtBot, sekme: tuple[KenarSekmesi, SahteImlec]) -> None:
    s, imlec = sekme
    _ac(qtbot, s, imlec)
    imlec.git(s.frameGeometry().topLeft())  # panelin sol ust kosesi: kapali diskin disinda ama panelin icinde
    qtbot.wait(_ust_sinir(s, False))
    assert s.acik is True


def test_k4_saydam_kosede_acilmaz_merkezde_acilir(qtbot: QtBot, sekme: tuple[KenarSekmesi, SahteImlec]) -> None:
    s, imlec = sekme
    imlec.git(s.frameGeometry().topLeft())  # alfa 0 kose (KRT D1)
    qtbot.wait(_ust_sinir(s, True))
    assert s.acik is False
    imlec.git(_merkez(s))
    qtbot.waitUntil(lambda: s.acik, timeout=_ust_sinir(s, True))


def test_k4_imlec_yalniz_enjekte_edilen_callable_ile_okunur(qtbot: QtBot, sekme: tuple[KenarSekmesi, SahteImlec]) -> None:
    s, imlec = sekme
    QtGui.QCursor.setPos(_merkez(s))  # gercek imlec sekmede, sahte imlec uzakta
    assert QtGui.QCursor.pos() == _merkez(s)
    qtbot.wait(_ust_sinir(s, True))
    assert s.acik is False
    QtGui.QCursor.setPos(UZAK)
    imlec.git(_merkez(s))  # sahte imlec sekmede, gercek imlec uzakta
    qtbot.waitUntil(lambda: s.acik, timeout=_ust_sinir(s, True))


def test_k4_varsayilan_imlec_qcursor_pos(qtbot: QtBot) -> None:
    """`imlec_konumu=None` -> `QCursor.pos` (offscreen'de setPos calisir, KRT o4)."""
    s = KenarSekmesi(_ekran())
    qtbot.addWidget(s)
    QtGui.QCursor.setPos(UZAK)
    s.show()
    QtGui.QCursor.setPos(_merkez(s))
    qtbot.waitUntil(lambda: s.acik, timeout=_ust_sinir(s, True))
    QtGui.QCursor.setPos(UZAK)
    qtbot.waitUntil(lambda: not s.acik, timeout=_ust_sinir(s, False))
    s.hide()


def test_k4_yoklayici_yalniz_gorunurken(qtbot: QtBot) -> None:
    imlec = SahteImlec()
    s = KenarSekmesi(_ekran(), imlec_konumu=imlec)
    qtbot.addWidget(s)
    qtbot.wait(3 * s.yoklama_ms)
    assert imlec.sayac == 0 and s.yokluyor is False  # show() oncesi yoklama yok
    s.show()
    qtbot.waitUntil(lambda: imlec.sayac > 0, timeout=3 * s.yoklama_ms + 300)
    assert s.yokluyor is True
    s.hide()
    assert s.yokluyor is False
    n = imlec.sayac
    qtbot.wait(4 * s.yoklama_ms)
    assert imlec.sayac == n  # hide() sonrasi artmaz
    s.show()
    qtbot.waitUntil(lambda: imlec.sayac > n, timeout=3 * s.yoklama_ms + 300)
    s.hide()


def test_k4_acikken_gizlenirse_kapali_olarak_geri_gelir(qtbot: QtBot, sekme: tuple[KenarSekmesi, SahteImlec]) -> None:
    s, imlec = sekme
    _ac(qtbot, s, imlec)
    s.hide()
    assert s.acik is False and s.frameGeometry().size() == QtCore.QSize(s.yaricap, 2 * s.yaricap)
    imlec.git(UZAK)
    s.show()
    qtbot.wait(2 * s.yoklama_ms)
    assert s.acik is False and s.frameGeometry().size() == QtCore.QSize(s.yaricap, 2 * s.yaricap)


# -- K4 surukleme -------------------------------------------------------------------------------


def test_k4_surukleme_sirasinda_sayac_baslamaz(qtbot: QtBot, sekme: tuple[KenarSekmesi, SahteImlec]) -> None:
    s, imlec = sekme
    imlec.git(_merkez(s))
    _bas(s, SOL_DUGME, QtCore.QPoint(s.yaricap - 4, s.yaricap))
    assert s.surukleniyor is True
    qtbot.wait(s.acilma_ms + 3 * s.yoklama_ms)
    assert s.acik is False and s.surukleniyor is True
    _birak(s, SOL_DUGME, QtCore.QPoint(s.yaricap - 4, s.yaricap))
    assert s.surukleniyor is False
    qtbot.waitUntil(lambda: s.acik, timeout=_ust_sinir(s, True))  # birakinca imlec icerideyse sifirdan baslar


def test_k4_surukleme_calisan_acilma_sayacini_durdurur(qtbot: QtBot, sekme: tuple[KenarSekmesi, SahteImlec]) -> None:
    s, imlec = sekme
    imlec.git(_merkez(s))
    qtbot.wait(s.yoklama_ms + 30)  # en az bir yoklama gecti: acilma sayaci calisiyor
    assert s.acik is False
    _bas(s, SOL_DUGME, QtCore.QPoint(s.yaricap - 4, s.yaricap))
    qtbot.wait(s.acilma_ms + 3 * s.yoklama_ms)
    assert s.acik is False
    _birak(s, SOL_DUGME, QtCore.QPoint(s.yaricap - 4, s.yaricap))
    qtbot.wait(s.acilma_ms // 2)
    assert s.acik is False  # sifirdan: birakildiktan acilma_ms/2 sonra hala kapali
    qtbot.waitUntil(lambda: s.acik, timeout=_ust_sinir(s, True))


def test_k4_surukleme_y_tasir_ve_sinira_kilitlenir(qtbot: QtBot, sekme: tuple[KenarSekmesi, SahteImlec]) -> None:
    s, imlec = sekme
    g = _ekran().availableGeometry()
    y0 = s.y
    bas = QtCore.QPoint(s.yaricap - 4, s.yaricap)
    _bas(s, SOL_DUGME, bas)
    _tasi(s, QtCore.QPoint(bas.x(), bas.y() + 100))
    assert s.y == y0 + 100 and s.frameGeometry().top() == y0 + 100
    assert s.frameGeometry().right() == g.right()  # x degismez
    _tasi(s, QtCore.QPoint(bas.x(), bas.y() + 100_000))
    assert s.y == g.bottom() - 2 * s.yaricap + 1  # alt sinira kilitlenir
    _tasi(s, QtCore.QPoint(bas.x(), bas.y() - 100_000))
    assert s.y == g.top()
    _birak(s, SOL_DUGME, bas)
    assert s.surukleniyor is False


def test_k4_acikken_sol_tik_surukleme_baslatmaz(qtbot: QtBot, sekme: tuple[KenarSekmesi, SahteImlec]) -> None:
    s, imlec = sekme
    _ac(qtbot, s, imlec)
    _bas(s, SOL_DUGME, QtCore.QPoint(3, 3))
    assert s.surukleniyor is False and s.acik is True
    _birak(s, SOL_DUGME, QtCore.QPoint(3, 3))


def test_k4_dugme_basili_degilken_hareket_tasimaz(qtbot: QtBot, sekme: tuple[KenarSekmesi, SahteImlec]) -> None:
    s, _ = sekme
    y0 = s.y
    _tasi(s, QtCore.QPoint(10, 500))
    assert s.y == y0


# -- K4/O9 mod tiki: once panel kapanir, sonra sinyal --------------------------------------------


@pytest.mark.parametrize("dugme_adi", ["dugme_anlik", "dugme_bolge"])
def test_k4_mod_tiki_once_panel_kapanir_sonra_sinyal(qtbot: QtBot, sekme: tuple[KenarSekmesi, SahteImlec], dugme_adi: str) -> None:
    s, imlec = sekme
    sinyal = s.anlik_cevir if dugme_adi == "dugme_anlik" else s.bolge_izle
    dugme: QtWidgets.QPushButton = getattr(s, dugme_adi)
    _ac(qtbot, s, imlec)
    aninda: list[tuple[bool, QtCore.QSize]] = []
    sinyal.connect(lambda: aninda.append((s.acik, s.frameGeometry().size())))
    with qtbot.waitSignal(sinyal, timeout=1000):
        dugme.click()
    assert aninda == [(False, QtCore.QSize(s.yaricap, 2 * s.yaricap))]  # sinyal aninda panel kapali
    assert s.acik is False and s.frameGeometry().size() == QtCore.QSize(s.yaricap, 2 * s.yaricap)


def test_k4_mod_tiki_sonrasi_kapanma_sayaci_paneli_tekrar_acmaz(qtbot: QtBot, sekme: tuple[KenarSekmesi, SahteImlec]) -> None:
    s, imlec = sekme
    _ac(qtbot, s, imlec)
    imlec.git(s.dugme_bolge.mapToGlobal(s.dugme_bolge.rect().center()))  # imlec dugmede (kapali diskin disinda)
    s.dugme_bolge.click()
    qtbot.wait(_ust_sinir(s, False))
    assert s.acik is False


def _disk_icinde_dugme_noktasi(s: KenarSekmesi, dugme: QtWidgets.QPushButton) -> QtCore.QPoint:
    """Panel acikken dugmenin kenara yakin ucu: KAPALI diskin icinde kalan gercek bir tik noktasi (Tester-A O-A1)."""
    kapali = sekme_kapali_dikdortgeni(s.ekran_dikdortgeni, s.y, s.yaricap, s.kenar)
    d = QtCore.QRect(dugme.mapToGlobal(QtCore.QPoint(0, 0)), dugme.size()).intersected(kapali)
    merkez = QtCore.QPoint(kapali.right() if s.kenar is Kenar.SAG else kapali.left(), kapali.top() + s.yaricap)
    adaylar = [
        QtCore.QPoint(x, y)
        for x in range(d.left(), d.right() + 1)
        for y in range(d.top(), d.bottom() + 1)
        if sekme_icinde(kapali, QtCore.QPoint(x, y), s.yaricap, s.kenar)
    ]
    assert adaylar, "dugme ile kapali disk kesismiyor (Tester-A O-A1 on kosulu)"
    return min(adaylar, key=lambda n: (n.x() - merkez.x()) ** 2 + (n.y() - merkez.y()) ** 2)  # diske en derin nokta


@pytest.mark.parametrize("dugme_adi", ["dugme_anlik", "dugme_bolge"])
def test_k4_mod_tiki_sonrasi_imlec_diskte_kalsa_da_yeniden_acilmaz_ciktiktan_sonra_acilir(
    qtbot: QtBot, sekme: tuple[KenarSekmesi, SahteImlec], dugme_adi: str
) -> None:
    """K4 ▲▲ (Tester-A O-A1): mod tikinda imlec kapali diskin icinde kaliyorsa (dugmenin kenara yakin ucu)
    panel `acilma_ms` sonra YENIDEN ACILMAZ -- imlec diskten cikana kadar. Pozitif kontrol: disari -> iceri -> acilir."""
    s, imlec = sekme
    dugme: QtWidgets.QPushButton = getattr(s, dugme_adi)
    _ac(qtbot, s, imlec)
    imlec.git(_disk_icinde_dugme_noktasi(s, dugme))
    dugme.click()
    assert s.acik is False
    qtbot.wait(s.acilma_ms + 3 * s.yoklama_ms)
    assert s.acik is False and s.frameGeometry().size() == QtCore.QSize(s.yaricap, 2 * s.yaricap)
    qtbot.wait(s.acilma_ms + 3 * s.yoklama_ms)
    assert s.acik is False  # mandal kalici: imlec diskte kaldigi surece
    imlec.git(UZAK)
    qtbot.wait(2 * s.yoklama_ms)
    assert s.acik is False
    imlec.git(_merkez(s))
    qtbot.waitUntil(lambda: s.acik, timeout=_ust_sinir(s, True))  # pozitif kontrol: cikis sonrasi normal acilma


def test_k4_mod_tiki_mandali_gizlenip_gosterilince_sifirlanir(qtbot: QtBot, sekme: tuple[KenarSekmesi, SahteImlec]) -> None:
    """Mod tiki -> `hide()` -> `show()`: yeniden gosterilen sekme taze baslar; imlec diskteyse acilir."""
    s, imlec = sekme
    _ac(qtbot, s, imlec)
    imlec.git(_disk_icinde_dugme_noktasi(s, s.dugme_anlik))
    s.dugme_anlik.click()
    s.hide()
    imlec.git(_merkez(s))
    s.show()
    qtbot.waitUntil(lambda: s.acik, timeout=_ust_sinir(s, True))


# -- K1 ▲▲ omur ve dis close() (Tester-A Y-A1, Tester-B O-B1) -----------------------------------


def _gorunur_ust_duzey() -> list[str]:
    return [type(w).__name__ for w in QtWidgets.QApplication.topLevelWidgets() if w.isVisible()]


@pytest.mark.parametrize("yol", ["del_gc", "deleteLater"])
def test_k1_omur_son_referans_dusunce_silinir_gorunur_kalmaz(qtbot: QtBot, yol: str) -> None:
    """Tek basina `KenarSekmesi`: son Python referansi dusunce (`del`+gc / `deleteLater`) silinir --
    `weakref` None, gorunur ust-duzey listesinde kalmaz, yoklayici durur. Fixture/`addWidget` KULLANILMAZ
    (guclu referans). Tester-A Y-A1: lambda baglantilari yuzunden hic silinmiyordu."""
    imlec = SahteImlec()
    s = KenarSekmesi(_ekran(), imlec_konumu=imlec)
    s.show()
    qtbot.wait(20)
    assert "KenarSekmesi" in _gorunur_ust_duzey() and s.yokluyor is True
    ws = weakref.ref(s)
    if yol == "deleteLater":
        s.deleteLater()
    del s
    gc.collect()
    qtbot.wait(300)
    try:
        assert ws() is None, "sekme silinmedi"
        assert "KenarSekmesi" not in _gorunur_ust_duzey()
        n = imlec.sayac
        qtbot.wait(3 * 60)
        assert imlec.sayac == n  # yoklayici durdu (silinen sekme imleci okumaz)
    finally:
        artik = ws()
        if artik is not None:
            artik.hide()


def test_k1_kapandi_sinyali_close_ile_yayilir_hide_ile_yayilmaz(qtbot: QtBot, sekme: tuple[KenarSekmesi, SahteImlec]) -> None:
    """`close()` (dis kapatma: WM_CLOSE, `closeAllWindows`) -> `kapandi` sinyali; sekme gizli, yoklayici durur,
    panel kapali. `hide()` (kabugun kendi yolu) `kapandi` YAYMAZ (ayirt edici)."""
    s, imlec = sekme
    _ac(qtbot, s, imlec)
    sayac: list[int] = []
    s.kapandi.connect(lambda: sayac.append(1))
    with qtbot.waitSignal(s.kapandi, timeout=1000):
        assert s.close() is True
    assert sayac == [1] and s.isVisible() is False and s.yokluyor is False and s.acik is False
    imlec.git(UZAK)
    s.show()
    s.hide()
    assert sayac == [1]
    s.show()
    s.close()
    assert sayac == [1, 1]


def test_k4_gercek_tik_ile_dugme_sinyali(qtbot: QtBot, sekme: tuple[KenarSekmesi, SahteImlec]) -> None:
    s, imlec = sekme
    _ac(qtbot, s, imlec)
    with qtbot.waitSignal(s.anlik_cevir, timeout=1000):
        _tikla(s.dugme_anlik, SOL_DUGME)
    assert s.acik is False


# -- K8 kesfedilebilirlik: tooltip, dugme_goster, sag tik ---------------------------------------


def test_k8_tooltip_sag_tik_ipucu(sekme: tuple[KenarSekmesi, SahteImlec]) -> None:
    s, _ = sekme
    assert "Sağ tık: pencereyi göster" in s.toolTip()


def test_k8_sag_tik_pencereyi_goster(qtbot: QtBot, sekme: tuple[KenarSekmesi, SahteImlec]) -> None:
    s, _ = sekme
    with qtbot.waitSignal(s.pencereyi_goster, timeout=1000):
        _bas(s, SAG_DUGME, QtCore.QPoint(s.yaricap - 4, s.yaricap))
    _birak(s, SAG_DUGME, QtCore.QPoint(s.yaricap - 4, s.yaricap))
    assert s.surukleniyor is False


def test_k8_sag_tik_acikken_de_pencereyi_goster(qtbot: QtBot, sekme: tuple[KenarSekmesi, SahteImlec]) -> None:
    s, imlec = sekme
    _ac(qtbot, s, imlec)
    with qtbot.waitSignal(s.pencereyi_goster, timeout=1000):
        _bas(s, SAG_DUGME, QtCore.QPoint(3, 3))
    _birak(s, SAG_DUGME, QtCore.QPoint(3, 3))


def test_k8_panelde_dugme_goster(qtbot: QtBot, sekme: tuple[KenarSekmesi, SahteImlec]) -> None:
    s, imlec = sekme
    _ac(qtbot, s, imlec)
    assert isinstance(s.dugme_goster, QtWidgets.QPushButton)
    assert s.dugme_goster.toolTip() != "" and s.dugme_goster.accessibleName() != ""
    with qtbot.waitSignal(s.pencereyi_goster, timeout=1000):
        s.dugme_goster.click()
    assert s.acik is False


def test_k8_panel_dugmeleri_metin_ve_erisilebilirlik(sekme: tuple[KenarSekmesi, SahteImlec]) -> None:
    s, _ = sekme
    for d in (s.dugme_anlik, s.dugme_bolge, s.dugme_goster):
        assert isinstance(d, QtWidgets.QPushButton) and d.accessibleName() != "" and d.toolTip() != ""
    assert "Anlık çeviri" in s.dugme_anlik.text() and "Bölge izle" in s.dugme_bolge.text()
    assert s.dugme_anlik.focusPolicy() == Qt.FocusPolicy.NoFocus


# -- K6 paint butcesi: 100 kare medyani iki halde -------------------------------------------------


def _paint_medyani(s: KenarSekmesi) -> float:
    sureler: list[float] = []
    for _ in range(100):
        t0 = time.perf_counter()
        s.repaint()
        sureler.append((time.perf_counter() - t0) * 1000)
    return statistics.median(sureler)


def test_k6_paint_100_kare_medyani_kapali_ve_acik(qtbot: QtBot, sekme: tuple[KenarSekmesi, SahteImlec]) -> None:
    s, imlec = sekme
    qtbot.wait(30)  # pencere platformda gosterilsin (repaint erken donmesin)
    kapali = _paint_medyani(s)
    _ac(qtbot, s, imlec)
    acik = _paint_medyani(s)
    assert kapali < 16 and acik < 16, (kapali, acik)
