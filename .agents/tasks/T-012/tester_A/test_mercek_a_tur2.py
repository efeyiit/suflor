"""T-012 Tester-A tur 2 mercek testleri: paket v3'un ▲▲ eklerine saldiri (omur, `kapandi`, mandal, balon, ust sinirlar).

Kor testler: delivery.md / evidence / sef_dogrulama / implementer testleri OKUNMADAN yazildi.
Garanti alani = src/ui/*.py v3 docstring'leri + packet.md v3 (K1 ▲▲ omur + `kapandi`, K4 ▲▲ mandal, K5 ▲▲ balon).
Tur 1 dosyasi (`test_mercek_a.py`) ayrica v3'e karsi kosar; 6 pin orada `_v3` olarak ters cevrildi.

Bolumler:
  A  K1 ▲▲ omur: del+gc / deleteLater / close() / kapat() sonrasi dusurme x 5 durum; yoklayici durur (enjekte sayac);
     iki AnaPencere; Tepsi omru (tek basina + menu); N dongu sizinti (topLevelWidgets + allWidgets); ekran sinyali
     dusurmeden sonra; imlec_konumu dongusu; panel acikken / suruklerken dusurme; pozitif kontroller (lambda, partial)
  B  K1 ▲▲ `kapandi`: sekme.close() x 5 durum (+ kapat sonrasi), acikken/suruklerken, hide() yaymaz, sayim,
     closeAllWindows x 5 durum [ÖLÇÜLMÜYOR -> olculdu], iki AnaPencere, yeniden giris (kapandi dinleyicisi)
  C  K1 tablo genislemesi (sekme_close / close_all_windows eylemleri) + rastgele yuruyus v3 (+ balon <= 1, + omur)
  D  K4 ▲▲ mandal: diskte kal -> acilmaz; cik-gir -> acilir; uc dugme; hide/show sifirlar; surukleme sifirlamaz (PIN);
     sag tik mandal koymaz; acilma_ms=0; AnaPencere duzeyinde dugme_goster
  E  K5 ▲▲ balon: showMessage casusu; x3 -> 1; iki ornek (surec basina); tepsisiz tuketmez; kenar/kapat sonrasi yok;
     dugme yolu; sinyal aninda uclu; bildir dallari (pozitif kontrol)
  F  Yeni ust sinirlar (66/67, ms 2**31-1 / 2**31) + PANEL_BOYUTU degismezligi + `_YARICAP_AZAMI` turetimi
  G  Yapisal: `.connect(lambda` / `partial` yok (kendi bekcim, pozitif kontrollu); crash-guvenli senaryolar ayri surecte
"""
from __future__ import annotations

import ast
import functools
import gc
import json
import os
import random
import subprocess
import sys
import weakref
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
import shiboken6
from PySide6.QtCore import QPoint, QRect, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QCloseEvent, QGuiApplication, QIcon, QScreen
from PySide6.QtWidgets import QApplication, QMenu, QPushButton, QSystemTrayIcon, QWidget

from src.ui.geometri import PANEL_BOYUTU, Kenar, sekme_acik_dikdortgeni, sekme_icinde, sekme_kapali_dikdortgeni
from src.ui.kabuk import AnaPencere, KabukDurumu, Tepsi
from src.ui.kenar_sekmesi import KenarSekmesi

KOK = Path(__file__).resolve().parents[4]
SRC_UI = KOK / "src" / "ui"
DISARI = QPoint(-10_000, -10_000)
HIZLI = dict(acilma_ms=20, kapanma_ms=30, yoklama_ms=10)
URUN = dict(acilma_ms=120, kapanma_ms=450, yoklama_ms=60)

Uclu = tuple[bool, bool, bool]
SATIRLAR = ("G", "T", "K", "K0", "G0")
UCLU_TABLO: dict[str, Uclu] = {"G": (True, False, False), "T": (False, False, True), "K": (False, True, True), "K0": (False, True, False), "G0": (True, False, False)}
DURUM_TABLO = {"G": KabukDurumu.GORUNUR, "T": KabukDurumu.TEPSI, "K": KabukDurumu.KENAR, "K0": KabukDurumu.KENAR, "G0": KabukDurumu.GORUNUR}


def uclu(p: AnaPencere) -> Uclu:
    return (p.isVisible(), p.sekme.isVisible(), p.tepsi.gorunur())


def gorunur_ust_duzey() -> list[QWidget]:
    return [w for w in QApplication.topLevelWidgets() if w.isVisible()]


def ust_duzey_turleri() -> list[str]:
    return sorted(type(w).__name__ for w in QApplication.topLevelWidgets())


def tum_widget_sayisi() -> int:
    return len(QApplication.allWidgets())


# ---------------------------------------------------------------- fixture'lar --------------------------------------
@pytest.fixture
def ekran(qapp: QApplication) -> QScreen:
    e = QGuiApplication.primaryScreen()
    assert e is not None
    return e


@pytest.fixture
def imlec() -> list[QPoint]:
    """`imlec[0]` konum; `imlec[1].x()` cagri sayaci."""
    return [QPoint(DISARI), QPoint(0, 0)]


@pytest.fixture
def balon(monkeypatch) -> list[tuple[bool, tuple[object, ...]]]:
    """`QSystemTrayIcon.showMessage` casusu: (ikon gorunur mu, argumanlar); surec sayacini sifirlar (docstring: testler sifirlar)."""
    kayit: list[tuple[bool, tuple[object, ...]]] = []
    orijinal = QSystemTrayIcon.showMessage

    def casus(self: QSystemTrayIcon, *a: object, **k: object) -> None:
        kayit.append((self.isVisible(), a))
        orijinal(self, *a, **k)

    monkeypatch.setattr(QSystemTrayIcon, "showMessage", casus)
    monkeypatch.setattr(AnaPencere, "_balon_gosterildi", False)
    return kayit


@pytest.fixture
def pencere_fab(qtbot, ekran: QScreen, imlec: list[QPoint], monkeypatch) -> Iterator[Callable[..., AnaPencere]]:
    """AnaPencere fabrikasi; teardown'da her (gecerli) pencereye `kapat()`. Balon sayaci her test icin sifir."""
    monkeypatch.setattr(AnaPencere, "_balon_gosterildi", False)
    yapilanlar: list[AnaPencere] = []

    def konum() -> QPoint:
        imlec[1].setX(imlec[1].x() + 1)
        return QPoint(imlec[0])

    def yap(**kw: object) -> AnaPencere:
        kw.setdefault("tepsi_kullanilabilir", True)
        kw.setdefault("imlec_konumu", konum)
        p = AnaPencere(ekran, **kw)  # type: ignore[arg-type]
        yapilanlar.append(p)
        return p

    yield yap
    for p in yapilanlar:
        if shiboken6.isValid(p):
            p.kapat()
    qtbot.wait(20)


@pytest.fixture
def sekme_fab(qtbot, ekran: QScreen, imlec: list[QPoint]) -> Iterator[Callable[..., KenarSekmesi]]:
    yapilanlar: list[KenarSekmesi] = []

    def konum() -> QPoint:
        imlec[1].setX(imlec[1].x() + 1)
        return QPoint(imlec[0])

    def yap(**kw: object) -> KenarSekmesi:
        kw.setdefault("imlec_konumu", konum)
        s = KenarSekmesi(ekran, **kw)  # type: ignore[arg-type]
        yapilanlar.append(s)
        return s

    yield yap
    for s in yapilanlar:
        if shiboken6.isValid(s):
            s.hide()
    qtbot.wait(20)


def kur(fab: Callable[..., AnaPencere], satir: str) -> AnaPencere:
    p = fab(tepsi_kullanilabilir=satir in ("G", "T", "K"))
    p.show()
    if satir == "T":
        p.tepsiye_al()
    elif satir in ("K", "K0"):
        p.kenara_al()
    assert uclu(p) == UCLU_TABLO[satir] and p.durum is DURUM_TABLO[satir], f"kurulum {satir}: {uclu(p)} {p.durum}"
    return p


def _kur_ham(ekran: QScreen, satir: str, konum: Callable[[], QPoint]) -> AnaPencere:
    """Fabrikasiz kurulum (omur testleri: fabrika listesi referans tutmasin)."""
    p = AnaPencere(ekran, tepsi_kullanilabilir=satir in ("G", "T", "K"), imlec_konumu=konum)
    p.show()
    if satir == "T":
        p.tepsiye_al()
    elif satir in ("K", "K0"):
        p.kenara_al()
    assert uclu(p) == UCLU_TABLO[satir]
    return p


def _menu_eylem(p: AnaPencere, metin: str) -> None:
    eylem = [a for a in p.tepsi.menu.actions() if a.text() == metin]
    assert len(eylem) == 1
    eylem[0].trigger()


# =============================================================== A. K1 ▲▲ OMUR ======================================
@pytest.mark.parametrize("yol", ["del_gc", "deleteLater", "close_del", "kapat_del"])
@pytest.mark.parametrize("satir", SATIRLAR)
def test_a_omur_ana_pencere_dusunce_sekme_tepsi_menu_silinir(qtbot, ekran, imlec, monkeypatch, satir: str, yol: str) -> None:
    """Docstring K1 ▲▲: son Python referansi dusunce (`del`+gc) ya da `deleteLater` ile silinince sekme SILINIR, tepsi ve menusu
    de gider, gorunur ust-duzey listesi eski haline doner, yoklayici durur (enjekte sayac artmaz). 5 durum x 4 yol."""
    monkeypatch.setattr(AnaPencere, "_balon_gosterildi", False)

    def konum() -> QPoint:
        imlec[1].setX(imlec[1].x() + 1)
        return QPoint(imlec[0])

    once_gorunur = {id(w) for w in gorunur_ust_duzey()}
    once_turler, once_tum = ust_duzey_turleri(), tum_widget_sayisi()
    p = _kur_ham(ekran, satir, konum)
    qtbot.wait(3 * 60)  # kenar satirlarinda en az iki yoklama gecsin (pozitif kontrol)
    wp, ws, wt, wm, wi = weakref.ref(p), weakref.ref(p.sekme), weakref.ref(p.tepsi), weakref.ref(p.tepsi.menu), weakref.ref(p.tepsi.ikon)
    wpanel, wd = weakref.ref(p.sekme.dugme_anlik.parentWidget()), weakref.ref(p.sekme.dugme_anlik)
    sekme_gorunurdu = p.sekme.isVisible()
    if yol == "close_del":
        p.close()
    elif yol == "kapat_del":
        p.kapat()
    if yol == "deleteLater":
        p.deleteLater()
    del p
    gc.collect()
    qtbot.wait(300)
    gc.collect()
    assert wp() is None and ws() is None and wt() is None and wm() is None and wi() is None and wpanel() is None and wd() is None, (satir, yol)
    assert [w for w in gorunur_ust_duzey() if id(w) not in once_gorunur] == []
    assert ust_duzey_turleri() == once_turler and tum_widget_sayisi() == once_tum
    n = imlec[1].x()
    qtbot.wait(5 * 60)
    assert imlec[1].x() == n, "yoklayici durmadi"  # (kenar satirlarinda pozitif kontrol: kurulumda sayac artmisti)
    if satir in ("K", "K0") and yol in ("del_gc", "deleteLater"):
        assert sekme_gorunurdu and n >= 1


def test_a_omur_kenar_durumunda_pozitif_kontrol_yoklayici_calisiyordu(qtbot, ekran, imlec) -> None:
    """Olcunun ateslenebildigi: kenar durumunda sekme canliyken sayac artar; sadece referans dusurmeden once."""
    def konum() -> QPoint:
        imlec[1].setX(imlec[1].x() + 1)
        return QPoint(imlec[0])

    p = _kur_ham(ekran, "K", konum)
    n0 = imlec[1].x()
    qtbot.wait(4 * 60)
    assert imlec[1].x() > n0
    p.kapat()


def test_a_omur_pozitif_kontrol_lambda_ve_partial_sarmalayiciyi_tutar_bagli_yontem_ve_emit_tutmaz(qtbot) -> None:
    """Kural 10: ayni kalipta minimal widget -- `clicked.connect(lambda: self._tik())` ve `functools.partial(self._tik)`
    toplanMAZ ve gorunur kalir; `clicked.connect(self._tik)` ve `clicked.connect(self.sig.emit)` toplanir. Docstring'in
    'partial de tutar' cumlesi olculur."""

    class Lambdali(QWidget):
        def __init__(self) -> None:
            super().__init__(None, Qt.WindowType.Tool)
            self.b = QPushButton("x", self)
            self.b.clicked.connect(lambda: self._tik())

        def _tik(self) -> None:
            pass

    class Partialli(QWidget):
        def __init__(self) -> None:
            super().__init__(None, Qt.WindowType.Tool)
            self.b = QPushButton("x", self)
            self.b.clicked.connect(functools.partial(self._tik))

        def _tik(self) -> None:
            pass

    class BagliYontem(QWidget):
        def __init__(self) -> None:
            super().__init__(None, Qt.WindowType.Tool)
            self.b = QPushButton("x", self)
            self.b.clicked.connect(self._tik)

        def _tik(self) -> None:
            pass

    class Emitli(QWidget):
        sig = Signal()

        def __init__(self) -> None:
            super().__init__(None, Qt.WindowType.Tool)
            self.b = QPushButton("x", self)
            self.b.clicked.connect(self.sig.emit)

    sonuc: dict[str, bool] = {}
    for K in (BagliYontem, Emitli, Lambdali, Partialli):
        once = {id(w) for w in gorunur_ust_duzey()}
        w = K()
        w.show()
        r = weakref.ref(w)
        del w
        gc.collect()
        qtbot.wait(20)
        sonuc[K.__name__] = r() is not None
        if r() is not None:
            assert [x for x in gorunur_ust_duzey() if id(x) not in once] != []
            r().hide()
    assert sonuc == {"BagliYontem": False, "Emitli": False, "Lambdali": True, "Partialli": True}


def test_a_omur_delete_later_sarmalayici_tutulurken_sekme_gorunur_kalir_ve_kapat_runtime_error_PIN(qtbot, pencere_fab) -> None:
    """[PIN/dusuk D-A9] `deleteLater` + Python sarmalayicisi TUTULURKEN: C++ AnaPencere silinir ama sekme (Python sahipligi
    sarmalayicida) GORUNUR ve yokluyor kalir; `p.kapat()` / `p.goster()` RuntimeError (tepsi C++ silindi); sag tik sinyali
    alicisiz. Docstring 'deleteLater ile silinince sekme de silinir' der -- sarmalayici birakilinca dogru (pozitif kontrol
    alt satirda), tutulurken degil. Cozum onerisi: `destroyed -> sekme.hide` baglantisi."""
    p = kur(pencere_fab, "K")
    s = p.sekme
    p.deleteLater()
    qtbot.wait(50)
    assert shiboken6.isValid(p) is False
    assert shiboken6.isValid(s) is True and s.isVisible() is True and s.yokluyor is True  # PIN
    n: list[int] = []
    s.pencereyi_goster.connect(lambda: n.append(1))
    with qtbot.captureExceptions() as yakalanan:
        qtbot.mouseClick(s, Qt.MouseButton.RightButton, pos=QPoint(s.width() - 3, s.height() // 2))
        qtbot.wait(10)
    assert n == [1] and yakalanan == [] and s.isVisible()  # sinyal yayilir; kabugun yuvasi C++ aliciyla dusmus: alici yok, donus yolu yok
    with pytest.raises(RuntimeError):
        p.goster()
    with pytest.raises(RuntimeError):
        p.kapat()  # `_kapandi=True` + `_sekme.hide()` sonra `_tepsi.gizle()` RuntimeError (yarim kapanis)
    assert s.isVisible() is False and p.kapandi is True
    ws = weakref.ref(s)
    del s
    gc.collect()
    qtbot.wait(20)
    assert shiboken6.isValid(p) is False and ws() is not None  # fabrika listesi p'yi tutuyor -> sekme yasiyor
    ws().hide()


def test_a_omur_iki_ana_pencere_biri_dusunce_digeri_saglam(qtbot, ekran, imlec, monkeypatch) -> None:
    monkeypatch.setattr(AnaPencere, "_balon_gosterildi", False)
    a = _kur_ham(ekran, "K", lambda: QPoint(imlec[0]))
    b = _kur_ham(ekran, "K", lambda: QPoint(imlec[0]))
    wa, wsa = weakref.ref(a), weakref.ref(a.sekme)
    sb = b.sekme
    del a
    gc.collect()
    qtbot.wait(30)
    assert wa() is None and wsa() is None
    assert uclu(b) == (False, True, True) and sb.yokluyor is True and shiboken6.isValid(sb)
    with qtbot.captureExceptions() as yakalanan:
        ekran.availableGeometryChanged.emit(ekran.availableGeometry())  # dusurulenin yuvasi cagrilmamali
        qtbot.wait(10)
    assert yakalanan == []
    imlec[0] = sb.frameGeometry().center()
    qtbot.waitUntil(lambda: sb.acik, timeout=120 + 2 * 60 + 300)
    n: list[int] = []
    b.pencereyi_goster_yolu = None  # type: ignore[attr-defined]
    b.anlik_cevir_istendi.connect(lambda: n.append(1))
    sb.dugme_anlik.click()
    assert n == [1]
    imlec[0] = QPoint(DISARI)
    b.goster()
    assert uclu(b) == (True, False, False)
    wb, wsb = weakref.ref(b), weakref.ref(sb)
    del b, sb
    gc.collect()
    qtbot.wait(30)
    assert wb() is None and wsb() is None


def test_a_omur_tepsi_tek_basina_ebeveynsiz_toplanir_menu_dahil(qtbot) -> None:
    """`Tepsi(ikon, None)`: ebeveynsiz; menu ebeveynsiz QMenu (gizli ust-duzey). Son referans dusunce tepsi + menu + ikon gider."""
    once = ust_duzey_turleri()
    t = Tepsi(QIcon(), None, kullanilabilir=True)
    t.goster()
    assert ust_duzey_turleri().count("QMenu") == once.count("QMenu") + 1  # pozitif kontrol: menu ust-duzeyde
    wt, wm, wi = weakref.ref(t), weakref.ref(t.menu), weakref.ref(t.ikon)
    del t
    gc.collect()
    qtbot.wait(20)
    assert wt() is None and wm() is None and wi() is None
    assert ust_duzey_turleri() == once


def test_a_omur_n_dongu_sizinti_yok_ust_duzey_ve_tum_widget_sayisi(qtbot, ekran, imlec, monkeypatch) -> None:
    """10 x (kur -> [kenar/tepsi/gorunur] -> dusur): `topLevelWidgets` tur listesi ve `allWidgets` sayisi taban degere doner.
    Pozitif kontrol: dongu icinde sayilar artar."""
    monkeypatch.setattr(AnaPencere, "_balon_gosterildi", False)
    once_turler, once_tum = ust_duzey_turleri(), tum_widget_sayisi()
    for i in range(10):
        satir = SATIRLAR[i % len(SATIRLAR)]
        p = _kur_ham(ekran, satir, lambda: QPoint(imlec[0]))
        assert tum_widget_sayisi() > once_tum and len(ust_duzey_turleri()) > len(once_turler)
        if i % 3 == 0:
            p.kapat()
        elif i % 3 == 1:
            p.deleteLater()
        del p
        gc.collect()
        qtbot.wait(20)
    gc.collect()
    qtbot.wait(20)
    assert ust_duzey_turleri() == once_turler and tum_widget_sayisi() == once_tum


def test_a_omur_kenar_sekmesi_dusunce_ekran_sinyali_yuvasi_cagrilmaz(qtbot, ekran, imlec) -> None:
    """`availableGeometryChanged` baglantisi: sekme dusurulunce (del+gc) yayim istisna uretmez; canliyken (pozitif kontrol)
    yeniden konumlar."""
    s = KenarSekmesi(ekran, imlec_konumu=lambda: QPoint(imlec[0]))
    s.show()
    e = s.ekran_dikdortgeni
    kucuk = QRect(e.left(), e.top(), e.width() - 100, e.height())
    ekran.availableGeometryChanged.emit(kucuk)
    qtbot.wait(10)
    assert s.frameGeometry().right() == kucuk.right()  # pozitif kontrol
    ekran.availableGeometryChanged.emit(e)
    qtbot.wait(10)
    ws = weakref.ref(s)
    del s
    gc.collect()
    qtbot.wait(20)
    assert ws() is None
    with qtbot.captureExceptions() as yakalanan:
        ekran.availableGeometryChanged.emit(kucuk)
        qtbot.wait(10)
        ekran.availableGeometryChanged.emit(e)
        qtbot.wait(10)
    assert yakalanan == []


def test_a_omur_imlec_konumu_pencereyi_kapatan_closure_dongusu_toplanir(qtbot, ekran, monkeypatch) -> None:
    """`imlec_konumu` closure'u AnaPencere'yi yakalarsa (p -> sekme -> callable -> p dongusu) gc yine toplar."""
    monkeypatch.setattr(AnaPencere, "_balon_gosterildi", False)
    tut: list[AnaPencere] = []

    def konum() -> QPoint:
        return tut[0].mapToGlobal(QPoint(0, 0)) if tut else QPoint(DISARI)

    p = AnaPencere(ekran, tepsi_kullanilabilir=True, imlec_konumu=konum)
    tut.append(p)
    p.show()
    p.kenara_al()
    qtbot.wait(30)
    wp, ws = weakref.ref(p), weakref.ref(p.sekme)
    del p
    gc.collect()
    assert wp() is not None  # tut listesi tutuyor (pozitif kontrol)
    tut.clear()
    gc.collect()
    qtbot.wait(30)
    assert wp() is None and ws() is None


@pytest.mark.parametrize("hal", ["acik", "surukleniyor", "mandal"])
def test_a_omur_panel_acikken_veya_suruklerken_dusurme(qtbot, ekran, imlec, monkeypatch, hal: str) -> None:
    """Panel acikken / surukleme basiliyken / mandal aktifken AnaPencere dusurulur -> sekme silinir, gorunur ust-duzey doner."""
    monkeypatch.setattr(AnaPencere, "_balon_gosterildi", False)
    once = {id(w) for w in gorunur_ust_duzey()}
    p = _kur_ham(ekran, "K", lambda: QPoint(imlec[0]))
    s = p.sekme
    if hal in ("acik", "mandal"):
        imlec[0] = s.frameGeometry().center()
        qtbot.waitUntil(lambda: s.acik, timeout=120 + 2 * 60 + 300)
        if hal == "mandal":
            imlec[0] = QPoint(s.frameGeometry().right() - 4, s.frameGeometry().center().y())
            s.dugme_bolge.click()
            assert s.acik is False
    else:
        qtbot.mousePress(s, Qt.MouseButton.LeftButton, pos=QPoint(s.width() - 3, s.height() // 2))
        assert s.surukleniyor is True
    wp, ws = weakref.ref(p), weakref.ref(s)
    del p, s
    gc.collect()
    qtbot.wait(300)
    assert wp() is None and ws() is None, hal
    assert [w for w in gorunur_ust_duzey() if id(w) not in once] == []


def test_a_omur_calistir_sonrasi_dusurme_temiz(qtbot, qapp, monkeypatch) -> None:
    from src.ui.uygulama import calistir

    monkeypatch.setattr(AnaPencere, "_balon_gosterildi", False)
    once_turler = ust_duzey_turleri()
    tut: list[AnaPencere] = []
    w: list[weakref.ref[AnaPencere]] = []

    def calistirici(app: QApplication, p: AnaPencere) -> int:
        tut.append(p)
        w.append(weakref.ref(p))
        p.kenara_al()
        QTimer.singleShot(50, p.kapat)
        return app.exec()

    assert calistir([], calistirici=calistirici) == 0
    tut.clear()
    gc.collect()
    qtbot.wait(30)
    assert w[0]() is None and ust_duzey_turleri() == once_turler


# =============================================================== B. K1 ▲▲ KAPANDI / DIS KAPATMA ====================
@pytest.mark.parametrize("satir", SATIRLAR)
def test_b_kapandi_sekme_close_her_durumda(qtbot, pencere_fab, satir: str) -> None:
    """Docstring K1 ▲▲: `sekme.close()` -> `kapandi` yayilir; KENAR durumundaysa `goster()` -> (T,F,F) (tepsisiz de);
    sekme gizliyken (gorunur/tepsi) durum makinesine dokunmaz. `cikis_istendi` 0; `kenara_al()` yeniden calisir."""
    p = kur(pencere_fab, satir)
    n: list[int] = []
    kap: list[int] = []
    p.cikis_istendi.connect(lambda: n.append(1))
    p.sekme.kapandi.connect(lambda: kap.append(1))
    assert p.sekme.close() is True
    qtbot.wait(20)
    if satir in ("K", "K0"):
        assert (p.durum, uclu(p)) == (KabukDurumu.GORUNUR, (True, False, False)), satir
    else:
        assert (p.durum, uclu(p)) == (DURUM_TABLO[satir], UCLU_TABLO[satir]), satir
    assert kap == [1] and n == [] and p.kapandi is False
    assert p.sekme.yokluyor is False and p.sekme.acik is False
    p.kenara_al()
    qtbot.wait(10)
    assert uclu(p) == (False, True, satir in ("G", "T", "K")) and p.sekme.yokluyor is True  # close silmedi (WA_DeleteOnClose yok)
    p.sekme.close()
    qtbot.wait(10)
    assert kap == [1, 1] and uclu(p) == (True, False, False) and n == []


@pytest.mark.parametrize("satir", SATIRLAR)
def test_b_kapandi_kapat_sonrasi_sekme_close_diriltmez(qtbot, pencere_fab, satir: str) -> None:
    p = kur(pencere_fab, satir)
    n: list[int] = []
    p.cikis_istendi.connect(lambda: n.append(1))
    p.kapat()
    kap: list[int] = []
    p.sekme.kapandi.connect(lambda: kap.append(1))
    p.sekme.close()
    QApplication.sendEvent(p.sekme, QCloseEvent())
    qtbot.wait(10)
    assert uclu(p) == (False, False, False) and n == [1] and kap == [1, 1] and p.durum is DURUM_TABLO[satir]


@pytest.mark.parametrize("hal", ["acik", "surukleniyor", "mandal"])
def test_b_kapandi_sekme_close_panel_acikken_suruklerken_mandalda(qtbot, pencere_fab, imlec, hal: str) -> None:
    p = kur(pencere_fab, "K")
    s = p.sekme
    if hal in ("acik", "mandal"):
        imlec[0] = s.frameGeometry().center()
        qtbot.waitUntil(lambda: s.acik, timeout=120 + 2 * 60 + 300)
        if hal == "mandal":
            imlec[0] = QPoint(s.frameGeometry().right() - 4, s.frameGeometry().center().y())
            s.dugme_anlik.click()
    else:
        qtbot.mousePress(s, Qt.MouseButton.LeftButton, pos=QPoint(s.width() - 3, s.height() // 2))
    s.close()
    qtbot.wait(20)
    assert (p.durum, uclu(p)) == (KabukDurumu.GORUNUR, (True, False, False))
    assert s.acik is False and s.surukleniyor is False
    if hal != "acik":
        assert s.frameGeometry().size() == QSize(26, 52)  # 'acik' varyanti: O-A2 (asagidaki PIN testi)
    # mandal sifirlandi mi: kenara al, imlec diskte -> acilir
    p.kenara_al()
    imlec[0] = s.frameGeometry().center()
    qtbot.waitUntil(lambda: s.acik, timeout=120 + 2 * 60 + 300)


@pytest.mark.parametrize("yol", ["close", "close_all_windows"])
def test_b_kapandi_panel_acikken_close_sonrasi_kapali_sekme_200x132_kalir_PIN(qtbot, pencere_fab, imlec, yol: str) -> None:
    """[PIN/orta O-A2] Panel ACIKKEN `sekme.close()` / `closeAllWindows()` (Qt6 `QWindow::close()` akisi): `acik` False olur ama
    widget geometrisi 200x132 KALIR (konum kapali sekmeninki, boyut panelinki); `kenara_al()` ile yeniden gosterilen KAPALI
    sekme 200x132 pencere: K2/K3 'kapali (yaricap, 2*yaricap)' ihlali; `sekme_icinde` boyuta gore panel sanip duz `contains`
    yapar -> saydam alanda hover panel acar (K4 disk testi devre disi), o alanda tik oyuna gitmez. Bir acilip kapanma
    (ya da `y`/`kenar` atamasi) kendini toparlar. Pozitif kontrol: `hide()` yolu ve panel kapaliyken close -> 26x52.
    Offscreen + gercek `windows` platformunda ayni (sonda_a_02)."""
    p = kur(pencere_fab, "K")
    s = p.sekme
    kapali = s.frameGeometry()
    assert kapali.size() == QSize(26, 52)
    imlec[0] = kapali.center()
    qtbot.waitUntil(lambda: s.acik, timeout=120 + 2 * 60 + 300)
    imlec[0] = QPoint(DISARI)
    if yol == "close":
        s.close()
    else:
        QApplication.closeAllWindows()
    qtbot.wait(50)
    if yol == "close":
        assert (p.durum, uclu(p)) == (KabukDurumu.GORUNUR, (True, False, False))
    else:
        assert uclu(p) == (False, False, False) and p.kapandi  # closeAllWindows pencereyi de kapatti; sekme geometrisi yine bayat
    assert s.acik is False
    assert s.frameGeometry().size() == QSize(200, 132) and s.frameGeometry().topLeft() == kapali.topLeft()  # PIN (O-A2)
    if yol == "close":
        p.kenara_al()
        qtbot.wait(20)
        assert s.isVisible() and s.acik is False and s.frameGeometry().size() == QSize(200, 132)  # PIN: kapali sekme 200x132
        saydam = QPoint(kapali.left() + 5, kapali.top() + 5)  # kapali 26x52 dikdortgende disk DISI (saydam kose)
        assert sekme_icinde(kapali, saydam, 26, Kenar.SAG) is False and sekme_icinde(s.frameGeometry(), saydam, 26, Kenar.SAG) is True
        imlec[0] = saydam
        qtbot.waitUntil(lambda: s.acik, timeout=120 + 2 * 60 + 300)  # PIN: saydam alanda hover panel acti
        imlec[0] = QPoint(DISARI)
        qtbot.waitUntil(lambda: not s.acik, timeout=450 + 2 * 60 + 300)
        assert s.frameGeometry() == kapali  # kendini toparladi
    # pozitif kontrol: hide() yolu (kabugun kendi yolu) ayni durumda 26x52 verir
    p2 = kur(pencere_fab, "K")
    s2 = p2.sekme
    imlec[0] = s2.frameGeometry().center()
    qtbot.waitUntil(lambda: s2.acik, timeout=120 + 2 * 60 + 300)
    imlec[0] = QPoint(DISARI)
    p2.goster()
    qtbot.wait(50)
    assert s2.acik is False and s2.frameGeometry().size() == QSize(26, 52)
    p2.kenara_al()
    qtbot.wait(20)
    assert s2.frameGeometry().size() == QSize(26, 52)


def test_b_kapandi_hide_yaymaz_close_yayar_kabuk_yollari_sifir(qtbot, pencere_fab) -> None:
    """Kabugun kendi yollari (`goster/tepsiye_al/kenara_al/kapat`, dugmeler, menu) `kapandi` YAYMAZ; `close()`/QCloseEvent yayar."""
    p = kur(pencere_fab, "G")
    kap: list[int] = []
    p.sekme.kapandi.connect(lambda: kap.append(1))
    p.kenara_al(); p.goster(); p.kenara_al(); p.tepsiye_al(); p.goster(); p.kenara_al()
    p.dugme_tepsi.click(); p.dugme_kenar.click(); _menu_eylem(p, "Pencereyi göster"); _menu_eylem(p, "Kenara al")
    p.sekme.hide(); p.sekme.show(); p.sekme.setVisible(False)
    qtbot.wait(10)
    assert kap == []
    p.kapat()
    assert kap == []
    QApplication.sendEvent(p.sekme, QCloseEvent())  # pozitif kontrol
    assert kap == [1]


@pytest.mark.parametrize("satir", SATIRLAR)
def test_b_close_all_windows_her_durumda_olculdu(qtbot, pencere_fab, satir: str) -> None:
    """[ÖLÇÜLMÜYOR -> OLCULDU] `QApplication.closeAllWindows()`: gorunur -> `closeEvent` -> `kapat()` -> cikis 1, (F,F,F);
    tepsi -> gorunur pencere yok, HICBIR SEY olmaz ((F,F,T), cikis 0, durum tepsi); kenar (tepsili/tepsisiz) -> sekme kapanir
    -> `kapandi` -> `goster()` -> pencere gorunur olur -> Qt listeyi yeniler, pencereyi de kapatir -> `kapat()` -> cikis TAM 1,
    (F,F,F), durum GORUNUR (goster'den), kapandi 1. Oturum kapanisi (`commitData` varsayilani) bu yoldan gecer."""
    p = kur(pencere_fab, satir)
    n: list[int] = []
    kap: list[int] = []
    p.cikis_istendi.connect(lambda: n.append(1))
    p.sekme.kapandi.connect(lambda: kap.append(1))
    QApplication.closeAllWindows()
    qtbot.wait(30)
    if satir == "T":
        assert (uclu(p), p.durum, len(n), len(kap), p.kapandi) == ((False, False, True), KabukDurumu.TEPSI, 0, 0, False)
        p.goster()  # hala calisir
        assert uclu(p) == (True, False, False)
    elif satir in ("K", "K0"):
        assert (uclu(p), p.durum, len(n), len(kap), p.kapandi) == ((False, False, False), KabukDurumu.GORUNUR, 1, 1, True)
    else:
        assert (uclu(p), p.durum, len(n), len(kap), p.kapandi) == ((False, False, False), KabukDurumu.GORUNUR, 1, 0, True)
    QApplication.closeAllWindows()  # ikinci cagri: kapanmis pencerede sinyal uretmez; T satirinda goster() sonrasi ilk kez kapatir
    qtbot.wait(10)
    assert len(n) == 1 and uclu(p) == (False, False, False)


def test_b_close_all_windows_iki_ana_pencere_kenar_ve_gorunur(qtbot, pencere_fab) -> None:
    a, b = kur(pencere_fab, "K"), kur(pencere_fab, "G")
    na: list[int] = []
    nb: list[int] = []
    a.cikis_istendi.connect(lambda: na.append(1))
    b.cikis_istendi.connect(lambda: nb.append(1))
    QApplication.closeAllWindows()
    qtbot.wait(30)
    assert (uclu(a), na, uclu(b), nb) == ((False, False, False), [1], (False, False, False), [1])
    assert [w for w in gorunur_ust_duzey() if isinstance(w, (AnaPencere, KenarSekmesi))] == []


def test_b_kapandi_dinleyicisi_kenara_al_cagirirsa_tablo_disi_uclu_PIN(qtbot, pencere_fab) -> None:
    """[PIN/dusuk D-A10] Dis `kapandi` dinleyicisi `kenara_al()` ile sekmeyi yeniden gosterirse Qt `close()` akisi
    (closeEvent SONRA hide) sekmeyi hemen gizler -> (F,F,T) ama `durum` KENAR: tablo disi uclu (yeniden giris; kabugun
    kendi yuvasi once kosar ve dogru calisir). `goster()` toparlar. Pozitif kontrol: dinleyici yokken (T,F,F)."""
    p = kur(pencere_fab, "K")
    p.sekme.kapandi.connect(p.kenara_al)
    p.sekme.close()
    qtbot.wait(20)
    assert uclu(p) == (False, False, True) and p.durum is KabukDurumu.KENAR  # PIN
    assert p.sekme.yokluyor is False
    p.goster()
    assert (p.durum, uclu(p)) == (KabukDurumu.GORUNUR, (True, False, False))
    p.sekme.kapandi.disconnect(p.kenara_al)
    p.kenara_al()
    p.sekme.close()
    qtbot.wait(20)
    assert uclu(p) == (True, False, False)


def test_b_kapandi_dinleyicisi_kapat_cagirirsa_tek_sinyal(qtbot, pencere_fab) -> None:
    p = kur(pencere_fab, "K")
    n: list[int] = []
    p.cikis_istendi.connect(lambda: n.append(1))
    p.sekme.kapandi.connect(p.kapat)
    p.sekme.close()
    qtbot.wait(20)
    assert n == [1] and uclu(p) == (False, False, False) and p.kapandi is True


def test_b_kapandi_sinyal_aninda_kabuk_yuvasi_once_kosmus(qtbot, pencere_fab) -> None:
    """Baglanti sirasi: `AnaPencere` yapicida baglanir, dis dinleyici sonra -> dis dinleyici `kapandi` aninda (T,F,F) gorur;
    tek basina sekmede ise sinyal aninda sekme HALA gorunur (Qt: closeEvent once, hide sonra) -- bilgi."""
    p = kur(pencere_fab, "K")
    goruldu: list[tuple[Uclu, KabukDurumu, bool]] = []
    p.sekme.kapandi.connect(lambda: goruldu.append((uclu(p), p.durum, p.sekme.yokluyor)))
    p.sekme.close()
    qtbot.wait(10)
    assert goruldu == [((True, False, False), KabukDurumu.GORUNUR, False)]
    s = KenarSekmesi(QGuiApplication.primaryScreen(), **HIZLI)  # type: ignore[arg-type]
    s.show()
    tek: list[tuple[bool, bool]] = []
    s.kapandi.connect(lambda: tek.append((s.isVisible(), s.yokluyor)))
    s.close()
    qtbot.wait(10)
    assert tek == [(True, True)] and s.isVisible() is False and s.yokluyor is False  # bilgi: sinyal hide'dan once


def test_b_sekme_dis_delete_later_kabugu_kirar_PIN(qtbot, pencere_fab) -> None:
    """[PIN/dusuk D-A11] Dis `sekme.deleteLater()` (paketin `close()` yolu DEGIL): `kapandi` yayilmaz, `durum` kenar, sekme
    yok, sonraki `goster()`/`kapat()` RuntimeError (`destroyed` dinlenmiyor). Kotu kullanim; pozitif kontrol: `close()` ayni
    yerde (T,F,F)."""
    p = kur(pencere_fab, "K")
    kap: list[int] = []
    p.sekme.kapandi.connect(lambda: kap.append(1))
    p.sekme.deleteLater()
    qtbot.wait(50)
    assert kap == [] and p.durum is KabukDurumu.KENAR and shiboken6.isValid(p.sekme) is False
    with pytest.raises(RuntimeError):
        p.goster()
    with pytest.raises(RuntimeError):
        p.kapat()
    p.hide()
    p.tepsi.gizle()
    p2 = kur(pencere_fab, "K")
    p2.sekme.close()
    qtbot.wait(10)
    assert uclu(p2) == (True, False, False)


# =============================================================== C. K1 TABLO GENISLEMESI + RASTGELE YURUYUS ========
EYLEMLER: dict[str, tuple[Callable[[AnaPencere], None], str]] = {
    "goster": (lambda p: p.goster(), "goster"),
    "tepsiye_al": (lambda p: p.tepsiye_al(), "tepsi"),
    "kenara_al": (lambda p: p.kenara_al(), "kenar"),
    "kapat": (lambda p: p.kapat(), "kapat"),
    "close": (lambda p: p.close(), "kapat"),
    "dugme_kapat": (lambda p: p.dugme_kapat.click(), "kapat"),
    "dugme_tepsi": (lambda p: p.dugme_tepsi.click(), "tepsi"),
    "dugme_kenar": (lambda p: p.dugme_kenar.click(), "kenar"),
    "tepsi_trigger": (lambda p: p.tepsi.ikon.activated.emit(QSystemTrayIcon.ActivationReason.Trigger), "goster"),
    "menu_goster": (lambda p: _menu_eylem(p, "Pencereyi göster"), "goster"),
    "menu_kenar": (lambda p: _menu_eylem(p, "Kenara al"), "kenar"),
    "menu_cikis": (lambda p: _menu_eylem(p, "Çıkış"), "kapat"),
    "sekme_sag_tik": (lambda p: p.sekme.pencereyi_goster.emit(), "goster"),
    "sekme_dugme_goster": (lambda p: p.sekme.dugme_goster.click(), "goster"),
    "sekme_dugme_anlik": (lambda p: p.sekme.dugme_anlik.click(), "yok"),
    "sekme_dugme_bolge": (lambda p: p.sekme.dugme_bolge.click(), "yok"),
    "sekme_close": (lambda p: p.sekme.close(), "sekme_close"),  # ▲▲ v3
    "sekme_close_event": (lambda p: QApplication.sendEvent(p.sekme, QCloseEvent()), "sekme_close"),  # ▲▲ v3 (WM_CLOSE esdegeri)
    "close_all_windows": (lambda p: QApplication.closeAllWindows(), "close_all"),  # ▲▲ v3 (olculdu)
}


def beklenen(satir: str, sinif: str) -> tuple[KabukDurumu, Uclu, int]:
    tepsi_var = satir in ("G", "T", "K")
    if sinif == "goster" or (sinif == "sekme_close" and satir in ("K", "K0")):
        return KabukDurumu.GORUNUR, (True, False, False), 0
    if sinif == "kenar" or (sinif == "tepsi" and (not tepsi_var or satir == "K")):
        return KabukDurumu.KENAR, (False, True, tepsi_var), 0
    if sinif == "tepsi":
        return KabukDurumu.TEPSI, (False, False, True), 0
    if sinif == "kapat":
        return DURUM_TABLO[satir], (False, False, False), 1
    if sinif == "close_all":
        if satir == "T":
            return KabukDurumu.TEPSI, (False, False, True), 0
        return KabukDurumu.GORUNUR, (False, False, False), 1
    return DURUM_TABLO[satir], UCLU_TABLO[satir], 0


@pytest.mark.parametrize("eylem", ["sekme_close", "sekme_close_event", "close_all_windows"])
@pytest.mark.parametrize("satir", SATIRLAR)
def test_c_k1_tablo_v3_eylemleri(qtbot, pencere_fab, satir: str, eylem: str) -> None:
    p = kur(pencere_fab, satir)
    n: list[int] = []
    p.cikis_istendi.connect(lambda: n.append(1))
    uygula, sinif = EYLEMLER[eylem]
    uygula(p)
    qtbot.wait(30)
    b_durum, b_uclu, b_cikis = beklenen(satir, sinif)
    assert (p.durum, uclu(p), len(n)) == (b_durum, b_uclu, b_cikis), f"{satir}+{eylem}: {p.durum} {uclu(p)} cikis={len(n)}"
    assert p.kapandi is (len(n) == 1)
    assert p.sekme.yokluyor is p.sekme.isVisible() and p.sekme.acik is False
    # ardindan her kamu eylemi hala tabloda
    for sonraki in ("goster", "kenara_al", "tepsiye_al", "sekme_close"):
        EYLEMLER[sonraki][0](p)
        qtbot.wait(5)
        if p.kapandi:
            assert uclu(p) == (False, False, False) and len(n) == 1
        else:
            assert uclu(p) in {(True, False, False), (False, False, True), (False, True, satir in ("G", "T", "K"))}


@pytest.mark.parametrize("tohum", [11, 12, 13, 14, 15, 16, 17, 18])
def test_c_k1_rastgele_yuruyus_v3_iki_ornek_balon_omur(qtbot, ekran, imlec, balon, tohum: int) -> None:
    """Iki AnaPencere, 40 rastgele kamu eylemi (v3 eylemleri dahil): her adimda uclu tabloda ya da (F,F,F); cikis <= 1 / ornek;
    balon toplam <= 1 (surec basina); yoklayici == sekme gorunur; sonunda ikisi de dusurulur -> toplanir."""
    rnd = random.Random(tohum)
    tepsi_var = [rnd.random() < 0.7, rnd.random() < 0.7]
    ps = [AnaPencere(ekran, tepsi_kullanilabilir=tepsi_var[i], imlec_konumu=lambda: QPoint(imlec[0])) for i in range(2)]
    for p in ps:
        p.show()
    n: list[list[int]] = [[], []]
    ps[0].cikis_istendi.connect(lambda: n[0].append(1))
    ps[1].cikis_istendi.connect(lambda: n[1].append(1))
    gecmis: list[str] = []
    for _ in range(40):
        i = rnd.randrange(2)
        eylem = rnd.choice(list(EYLEMLER))
        gecmis.append(f"{i}:{eylem}")
        EYLEMLER[eylem][0](ps[i])
        for j, p in enumerate(ps):
            izin = {KabukDurumu.GORUNUR: {(True, False, False)}, KabukDurumu.TEPSI: {(False, False, True)}, KabukDurumu.KENAR: {(False, True, tepsi_var[j])}}
            if p.kapandi:
                assert uclu(p) == (False, False, False) and len(n[j]) == 1, gecmis
            else:
                assert uclu(p) in izin[p.durum] and len(n[j]) == 0, f"{gecmis}: [{j}] durum={p.durum} uclu={uclu(p)}"
            assert p.sekme.yokluyor is p.sekme.isVisible() and p.sekme.acik is False, gecmis
            if not tepsi_var[j]:
                assert p.durum is not KabukDurumu.TEPSI, gecmis
        assert len(balon) <= 1, gecmis
    for p in ps:
        p.kapat()
    ws = [weakref.ref(p.sekme) for p in ps]
    wp = [weakref.ref(p) for p in ps]
    ps.clear()
    del p
    gc.collect()
    qtbot.wait(30)
    assert all(w() is None for w in ws + wp)


# =============================================================== D. K4 ▲▲ MANDAL ====================================
@pytest.mark.parametrize("dugme", ["dugme_anlik", "dugme_bolge", "dugme_goster"])
@pytest.mark.parametrize("sayaclar", [HIZLI, URUN], ids=["hizli", "urun"])
def test_d_mandal_diskte_kalinca_acilmaz_cikip_girince_acilir(qtbot, sekme_fab, imlec, dugme: str, sayaclar: dict[str, int]) -> None:
    """Docstring K4 ▲▲ (`_mod_tiki`den gecen UC dugme, iki sayac takimi): tik sonrasi imlec kapali diskin icindeyken
    `acilma_ms + 3*yoklama_ms` -> hala kapali; diskten cikip girince acilir (pozitif kontrol, tek atimlik)."""
    s = sekme_fab(**sayaclar)
    s.show()
    k = s.frameGeometry()
    imlec[0] = k.center()
    qtbot.waitUntil(lambda: s.acik, timeout=s.acilma_ms + 2 * s.yoklama_ms + 300)
    disk_ici = QPoint(k.right() - 3, k.center().y())
    assert sekme_icinde(k, disk_ici, s.yaricap, Kenar.SAG) and s.frameGeometry().contains(disk_ici)
    imlec[0] = disk_ici
    getattr(s, dugme).click()
    assert s.acik is False and s.frameGeometry() == k
    qtbot.wait(s.acilma_ms + 3 * s.yoklama_ms)
    assert s.acik is False
    qtbot.wait(s.acilma_ms + 3 * s.yoklama_ms)
    assert s.acik is False  # kalici: imlec ciktigi surece degil, cikana kadar
    imlec[0] = QPoint(DISARI)
    qtbot.wait(2 * s.yoklama_ms + 20)
    imlec[0] = disk_ici
    qtbot.wait(s.acilma_ms // 2)
    assert s.acik is False  # deterministik alt sinir
    qtbot.waitUntil(lambda: s.acik, timeout=s.acilma_ms + 2 * s.yoklama_ms + 300)


def test_d_mandal_bir_yoklama_disari_yeter(qtbot, sekme_fab, imlec) -> None:
    """Tek bir yoklamada disarida gorulmek mandali sifirlar (saydam kose de 'disari'dir)."""
    s = sekme_fab(**HIZLI)
    s.show()
    k = s.frameGeometry()
    imlec[0] = k.center()
    qtbot.waitUntil(lambda: s.acik, timeout=500)
    imlec[0] = QPoint(k.right() - 3, k.center().y())
    s.dugme_anlik.click()
    qtbot.wait(80)
    assert s.acik is False
    imlec[0] = QPoint(k.left(), k.top())  # dikdortgen icinde, disk disinda (saydam kose)
    qtbot.wait(2 * 10 + 5)
    imlec[0] = k.center()
    qtbot.waitUntil(lambda: s.acik, timeout=500)


def test_d_mandal_disk_disinda_tik_hemen_sifirlanir(qtbot, sekme_fab, imlec) -> None:
    """Tik aninda imlec disk DISINDAYSA (dugme ortasi) mandal ilk yoklamada duser -> sonraki giris normal sure ile acar."""
    s = sekme_fab(**HIZLI)
    s.show()
    k = s.frameGeometry()
    imlec[0] = k.center()
    qtbot.waitUntil(lambda: s.acik, timeout=500)
    imlec[0] = QPoint(k.right() - 100, k.center().y())
    s.dugme_bolge.click()
    qtbot.wait(80)
    assert s.acik is False
    imlec[0] = k.center()
    qtbot.waitUntil(lambda: s.acik, timeout=500)


def test_d_mandal_hide_show_sifirlar(qtbot, sekme_fab, imlec) -> None:
    """Docstring: gizlenip gosterilince mandal sifirlanir -> imlec diskte ise acilir (tur-1 `hide()` sayac sifirlama olcusu gibi)."""
    s = sekme_fab(**HIZLI)
    s.show()
    k = s.frameGeometry()
    imlec[0] = k.center()
    qtbot.waitUntil(lambda: s.acik, timeout=500)
    imlec[0] = QPoint(k.right() - 3, k.center().y())
    s.dugme_anlik.click()
    qtbot.wait(80)
    assert s.acik is False
    s.hide()
    s.show()
    qtbot.waitUntil(lambda: s.acik, timeout=500)  # imlec hic cikmadi; hide/show taze
    imlec[0] = QPoint(DISARI)
    qtbot.waitUntil(lambda: not s.acik, timeout=500)


def test_d_mandal_surukleme_sifirlamaz_PIN(qtbot, sekme_fab, imlec) -> None:
    """[PIN/bilgi] Mod tiki -> (imlec diskte) sol basili surukle -> birak: mandal SURER, panel acilmaz (K4 surukleme
    cumlesi 'birakilinca imlec icerideyse sayac sifirdan baslar' burada mandala yenilir); diskten cikinca normal.
    Pozitif kontrol: mandalsiz ayni surukleme birakinca acar."""
    s = sekme_fab(**HIZLI)
    s.show()
    pos = QPoint(s.width() - 3, s.height() // 2)
    for mandal in (True, False):
        k = s.frameGeometry()
        imlec[0] = k.center()
        qtbot.waitUntil(lambda: s.acik, timeout=500)
        imlec[0] = QPoint(k.right() - 3, k.center().y())
        if mandal:
            s.dugme_anlik.click()
        else:
            imlec[0] = QPoint(DISARI)
            qtbot.waitUntil(lambda: not s.acik, timeout=500)
        assert s.acik is False
        qtbot.mousePress(s, Qt.MouseButton.LeftButton, pos=pos)
        qtbot.mouseMove(s, pos=QPoint(pos.x(), pos.y() + 40))
        imlec[0] = QPoint(s.frameGeometry().right() - 3, s.frameGeometry().center().y())
        qtbot.mouseRelease(s, Qt.MouseButton.LeftButton, pos=pos)
        qtbot.wait(20 + 4 * 10)
        assert s.acik is (not mandal), mandal  # PIN: mandal surukleme ile sifirlanmaz
        imlec[0] = QPoint(DISARI)
        qtbot.wait(40)
        qtbot.waitUntil(lambda: not s.acik, timeout=500)


def test_d_mandal_sag_tik_mandal_koymaz(qtbot, sekme_fab, imlec) -> None:
    """Sag tik `_mod_tiki`den gecmez: kapali sekmeye sag tik sonrasi imlec diskte -> normal sure ile acilir (mandal yok)."""
    s = sekme_fab(**HIZLI)
    s.show()
    n: list[int] = []
    s.pencereyi_goster.connect(lambda: n.append(1))
    k = s.frameGeometry()
    imlec[0] = QPoint(k.right() - 3, k.center().y())
    qtbot.mouseClick(s, Qt.MouseButton.RightButton, pos=QPoint(s.width() - 3, s.height() // 2))
    assert n == [1] and s.acik is False
    qtbot.waitUntil(lambda: s.acik, timeout=500)


def test_d_mandal_acilma_0_ile(qtbot, sekme_fab, imlec) -> None:
    s = sekme_fab(acilma_ms=0, kapanma_ms=0, yoklama_ms=10)
    s.show()
    k = s.frameGeometry()
    imlec[0] = k.center()
    qtbot.waitUntil(lambda: s.acik, timeout=300)
    imlec[0] = QPoint(k.right() - 3, k.center().y())
    s.dugme_goster.click()
    qtbot.wait(60)
    assert s.acik is False
    imlec[0] = QPoint(DISARI)
    qtbot.wait(25)
    imlec[0] = k.center()
    qtbot.waitUntil(lambda: s.acik, timeout=300)


def test_d_mandal_ana_pencere_dugme_goster_sonra_kenara_al_taze(qtbot, pencere_fab, imlec) -> None:
    """AnaPencere: paneldeki `dugme_goster` -> `goster()` sekmeyi gizler (mandal hideEvent'te sifirlanir) -> `kenara_al()`
    -> imlec diskte ise acilir; mod dugmesi (`dugme_anlik`) sonrasi ise sekme gorunur kalir ve mandal surer."""
    p = kur(pencere_fab, "K")
    s = p.sekme
    k = s.frameGeometry()
    imlec[0] = k.center()
    qtbot.waitUntil(lambda: s.acik, timeout=120 + 2 * 60 + 300)
    imlec[0] = QPoint(k.right() - 3, k.center().y())
    s.dugme_goster.click()
    assert uclu(p) == (True, False, False) and s.acik is False
    p.kenara_al()
    qtbot.waitUntil(lambda: s.acik, timeout=120 + 2 * 60 + 300)
    s.dugme_anlik.click()
    assert uclu(p) == (False, True, True) and s.acik is False
    qtbot.wait(120 + 3 * 60)
    assert s.acik is False and uclu(p) == (False, True, True)
    imlec[0] = QPoint(DISARI)
    qtbot.wait(2 * 60 + 20)
    imlec[0] = QPoint(k.right() - 3, k.center().y())
    qtbot.waitUntil(lambda: s.acik, timeout=120 + 2 * 60 + 300)


def test_d_mandal_kenar_degisimi_ile_disk_disina_dusme(qtbot, sekme_fab, imlec) -> None:
    """Mandal aktifken `kenar` degistirilirse imlec eski diskte kalir = yeni diskin disinda -> mandal duser; yeni diske girince acilir."""
    s = sekme_fab(**HIZLI)
    s.show()
    k = s.frameGeometry()
    imlec[0] = k.center()
    qtbot.waitUntil(lambda: s.acik, timeout=500)
    imlec[0] = QPoint(k.right() - 3, k.center().y())
    s.dugme_anlik.click()
    qtbot.wait(60)
    assert s.acik is False
    s.kenar = Kenar.SOL
    qtbot.wait(40)
    assert s.acik is False
    imlec[0] = QPoint(s.frameGeometry().left() + 2, s.frameGeometry().center().y())
    qtbot.waitUntil(lambda: s.acik, timeout=500)
    assert s.frameGeometry().left() == s.ekran_dikdortgeni.left()


# =============================================================== E. K5 ▲▲ BALON =====================================
def test_e_balon_ilk_tepsiye_al_bir_kez_x3(qtbot, pencere_fab, balon) -> None:
    p = kur(pencere_fab, "G")
    for _ in range(3):
        p.tepsiye_al()
        p.goster()
    assert len(balon) == 1
    gorunurdu, args = balon[0]
    assert gorunurdu is True  # ikon gorunurken gosterildi (once tepsi.goster, sonra bildir)
    assert args[0] == "Suflör arka planda" and args[2] == QSystemTrayIcon.MessageIcon.NoIcon and args[3] == 2500
    assert isinstance(args[1], str) and args[1] != ""
    p.dugme_tepsi.click()
    _menu_eylem(p, "Pencereyi göster")
    p.dugme_tepsi.click()
    assert len(balon) == 1 and uclu(p) == (False, False, True)


def test_e_balon_surec_basina_iki_ornek(qtbot, pencere_fab, balon) -> None:
    """Paket v3 K5 ▲▲: SUREC basina bir kez -- ikinci AnaPencere de gostermez; ilk ornek dusurulup yenisi kurulsa da."""
    a, b = kur(pencere_fab, "G"), kur(pencere_fab, "G")
    b.tepsiye_al()
    assert len(balon) == 1
    a.tepsiye_al()
    assert len(balon) == 1
    a.goster(); b.goster(); a.tepsiye_al(); b.tepsiye_al()
    assert len(balon) == 1
    a.kapat()
    c = kur(pencere_fab, "G")
    c.tepsiye_al()
    assert len(balon) == 1 and AnaPencere._balon_gosterildi is True


def test_e_balon_tepsisiz_tuketmez_sonra_tepsili_gosterir(qtbot, pencere_fab, balon) -> None:
    p0 = kur(pencere_fab, "G0")
    p0.tepsiye_al()
    assert uclu(p0) == (False, True, False) and len(balon) == 0 and AnaPencere._balon_gosterildi is False
    p0.goster(); p0.dugme_tepsi.click()
    assert len(balon) == 0 and AnaPencere._balon_gosterildi is False
    p = kur(pencere_fab, "G")
    p.tepsiye_al()
    assert len(balon) == 1 and balon[0][0] is True


def test_e_balon_kenar_ve_kapat_sonrasi_tepsiye_al_gostermez_tuketmez(qtbot, pencere_fab, balon) -> None:
    p = kur(pencere_fab, "K")
    p.tepsiye_al()  # kenar -> tepsi yolu yok: erken donus
    assert uclu(p) == (False, True, True) and len(balon) == 0 and AnaPencere._balon_gosterildi is False
    p.kapat()
    p.tepsiye_al()
    assert len(balon) == 0 and AnaPencere._balon_gosterildi is False
    p2 = kur(pencere_fab, "T")  # kur icinde tepsiye_al
    assert len(balon) == 1 and uclu(p2) == (False, False, True)


def test_e_balon_sinyal_aninda_uclu_ve_durum(qtbot, pencere_fab, balon, monkeypatch) -> None:
    """Balon `hide()` ve `durum=TEPSI` SONRASINDA cagrilir (ikon gorunur, pencere gizli): casus icinde olculur."""
    p = kur(pencere_fab, "G")
    goruldu: list[tuple[Uclu, KabukDurumu]] = []
    orijinal = Tepsi.bildir

    def casus(self: Tepsi, baslik: str, metin: str, ms: int) -> None:
        goruldu.append((uclu(p), p.durum))
        orijinal(self, baslik, metin, ms)

    monkeypatch.setattr(Tepsi, "bildir", casus)
    p.tepsiye_al()
    assert goruldu == [((False, False, True), KabukDurumu.TEPSI)] and len(balon) == 1


def test_e_balon_bildir_dallari_pozitif_kontrol(qtbot, balon) -> None:
    t = Tepsi(QIcon(), None, kullanilabilir=True)
    t.bildir("a", "b", 10)
    assert len(balon) == 1 and balon[0][1] == ("a", "b", QSystemTrayIcon.MessageIcon.NoIcon, 10)
    t0 = Tepsi(QIcon(), None, kullanilabilir=False)
    t0.bildir("a", "b", 10)
    assert len(balon) == 1  # tepsisiz sessiz
    t.bildir("c", "d", 0)
    assert len(balon) == 2


def test_e_balon_menu_kenara_al_tepsiden_sonra_balon_yok(qtbot, pencere_fab, balon) -> None:
    """tepsi -> kenar (menu) gecisi ikinci balon uretmez; goster -> tepsi tekrar da uretmez."""
    p = kur(pencere_fab, "T")
    assert len(balon) == 1
    _menu_eylem(p, "Kenara al")
    assert uclu(p) == (False, True, True) and len(balon) == 1
    p.goster(); p.tepsiye_al()
    assert len(balon) == 1


# =============================================================== F. YENI UST SINIRLAR + PANEL_BOYUTU ===============
@pytest.mark.parametrize("kw, kabul", [
    (dict(yaricap=66), True), (dict(yaricap=67), False), (dict(yaricap=1), True), (dict(yaricap=0), False), (dict(yaricap=-1), False),
    (dict(acilma_ms=2**31 - 1), True), (dict(acilma_ms=2**31), False), (dict(acilma_ms=0), True), (dict(acilma_ms=-1), False),
    (dict(kapanma_ms=2**31 - 1), True), (dict(kapanma_ms=2**31), False), (dict(kapanma_ms=0), True), (dict(kapanma_ms=-1), False),
    (dict(yoklama_ms=2**31 - 1), True), (dict(yoklama_ms=2**31), False), (dict(yoklama_ms=1), True), (dict(yoklama_ms=0), False),
    (dict(yaricap=10**12), False), (dict(acilma_ms=10**12, kapanma_ms=10**12), False),
], ids=lambda v: str(v) if isinstance(v, bool) else "-".join(f"{k}={x}" for k, x in v.items()))
def test_f_ust_sinir_tam_sinir_kabul_otesi_valueerror_qt_nesnesi_yok(ekran, kw: dict[str, int], kabul: bool) -> None:
    once_turler, once_tum = ust_duzey_turleri(), tum_widget_sayisi()
    if kabul:
        s = KenarSekmesi(ekran, **kw)
        for ad, v in kw.items():
            assert getattr(s, ad) == v
        assert s.frameGeometry().size() == QSize(s.yaricap, 2 * s.yaricap)
        s.hide()
        del s
        gc.collect()
    else:
        with pytest.raises(ValueError) as bilgi:
            KenarSekmesi(ekran, **kw)
        assert "Overflow" not in type(bilgi.value).__name__
        assert ust_duzey_turleri() == once_turler and tum_widget_sayisi() == once_tum  # hicbir Qt nesnesi yaratilmadi
    assert ust_duzey_turleri() == once_turler and tum_widget_sayisi() == once_tum


@pytest.mark.parametrize("kenar", [Kenar.SAG, Kenar.SOL])
def test_f_ust_sinir_66_panel_her_y_de_sekmeyi_kapsar(kenar: Kenar) -> None:
    """Ust sinirin gerekcesi (docstring): yaricap=66'da panel (h=132) kapali sekmeyi (h=132) HER y'de kapsar; 67'de kapsamaz."""
    for e in (QRect(0, 0, 2560, 1392), QRect(-2560, 0, 2560, 1440), QRect(-2560, 0, 2048, 1152)):
        for y in (e.top() - 5, e.top(), e.center().y(), e.bottom() - 132, e.bottom() + 99):
            k = sekme_kapali_dikdortgeni(e, y, 66, kenar)
            a = sekme_acik_dikdortgeni(e, y, 66, PANEL_BOYUTU, kenar)
            assert a.contains(k) and e.contains(a) and e.contains(k), (e, y)
        k = sekme_kapali_dikdortgeni(e, e.center().y(), 67, kenar)  # pozitif kontrol: 67 kapsanmaz
        assert not sekme_acik_dikdortgeni(e, e.center().y(), 67, PANEL_BOYUTU, kenar).contains(k)


def test_f_ust_sinir_yaricap_66_tam_akis(qtbot, sekme_fab, imlec) -> None:
    s = sekme_fab(yaricap=66, **HIZLI)
    s.show()
    assert s.frameGeometry().size() == QSize(66, 132) and s.frameGeometry().right() == s.ekran_dikdortgeni.right()
    k = s.frameGeometry()
    imlec[0] = QPoint(k.right(), k.top())  # disk kosesi
    qtbot.waitUntil(lambda: s.acik, timeout=500)
    assert s.frameGeometry().size() == PANEL_BOYUTU and s.frameGeometry().contains(imlec[0])
    qtbot.wait(100)
    assert s.acik is True
    s.dugme_anlik.click()
    assert s.acik is False and s.frameGeometry().size() == QSize(66, 132)


def test_f_yaricap_bool_ve_float_kabul_tip_sozlesmesi_disi_PIN(ekran) -> None:
    """[PIN/bilgi] `yaricap=True` (==1) ve `yaricap=26.5` yapicidan gecer (aralik testi sayisal); float'ta dikdortgen 26x53 olur.
    Tip sozlesmesi `int` (mypy yakalar); dokumante sinir degil, bilgi."""
    s = KenarSekmesi(ekran, yaricap=True)  # type: ignore[arg-type]
    assert s.frameGeometry().size() == QSize(1, 2)
    s2 = KenarSekmesi(ekran, yaricap=26.5)  # type: ignore[arg-type]
    assert s2.frameGeometry().size() == QSize(26, 53)  # PIN
    del s, s2


def test_f_panel_boyutu_degismezligi_akis_boyunca_ve_ast_bekci() -> None:
    """`PANEL_BOYUTU` src/ui icinde yerinde DEGISTIRILMEZ: AST'de `PANEL_BOYUTU.set*/scale/transpose/+=` yok (pozitif kontrol);
    davranissal: 3 sekme + kenar degisimi + ekran sinyali sonrasi hala (200,132)."""
    MUTASYON = {"setWidth", "setHeight", "scale", "transpose", "shrunkBy", "grownBy", "boundedTo", "expandedTo", "setX", "setY"}

    def mutasyonlar(kaynak: str) -> set[str]:
        bulunan: set[str] = set()
        for d in ast.walk(ast.parse(kaynak)):
            if isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) and isinstance(d.func.value, ast.Name) and d.func.value.id == "PANEL_BOYUTU" and d.func.attr in MUTASYON:
                bulunan.add(d.func.attr)
            if isinstance(d, ast.AugAssign) and isinstance(d.target, ast.Name) and d.target.id == "PANEL_BOYUTU":
                bulunan.add("aug")
            if isinstance(d, (ast.Assign,)) and any(isinstance(t, ast.Name) and t.id == "PANEL_BOYUTU" for t in d.targets) and not kaynak.startswith('"""Suflör -- kenar sekmesi geometrisi'):
                bulunan.add("yeniden_atama")
        return bulunan

    for dosya in ("kabuk.py", "kenar_sekmesi.py", "uygulama.py", "geometri.py"):
        assert mutasyonlar((SRC_UI / dosya).read_text(encoding="utf-8")) == set(), dosya
    assert mutasyonlar("PANEL_BOYUTU.setWidth(300)\nPANEL_BOYUTU += 1\nPANEL_BOYUTU = QSize(1,1)\n") == {"setWidth", "aug", "yeniden_atama"}
    assert PANEL_BOYUTU == QSize(200, 132)


def test_f_panel_boyutu_akis_sonrasi_ayni(qtbot, sekme_fab, imlec, ekran) -> None:
    for kenar in (Kenar.SAG, Kenar.SOL):
        s = sekme_fab(kenar=kenar, **HIZLI)
        s.show()
        imlec[0] = s.frameGeometry().center()
        qtbot.waitUntil(lambda: s.acik, timeout=500)
        s.kenar = Kenar.SOL if kenar is Kenar.SAG else Kenar.SAG
        e = s.ekran_dikdortgeni
        ekran.availableGeometryChanged.emit(QRect(e.left(), e.top(), e.width() - 50, e.height() - 50))
        qtbot.wait(10)
        ekran.availableGeometryChanged.emit(e)
        qtbot.wait(10)
        s.y = 10**6
        s.hide()
        imlec[0] = QPoint(DISARI)
    assert PANEL_BOYUTU == QSize(200, 132) and PANEL_BOYUTU.width() == 200


def test_f_yaricap_azami_panel_boyutundan_turetilir_import_aninda_PIN() -> None:
    """[PIN/bilgi] `_YARICAP_AZAMI = PANEL_BOYUTU.height() // 2` import aninda hesaplanir; `PANEL_BOYUTU` disaridan degistirilirse
    (tanimsiz, docstring) ust sinir izlemez. Geri alinir."""
    import src.ui.kenar_sekmesi as m

    assert m._YARICAP_AZAMI == 66 == PANEL_BOYUTU.height() // 2
    PANEL_BOYUTU.setHeight(100)
    try:
        assert m._YARICAP_AZAMI == 66  # PIN: izlemez
    finally:
        PANEL_BOYUTU.setHeight(132)
    assert PANEL_BOYUTU == QSize(200, 132)


# =============================================================== G. YAPISAL + AYRI SUREC CRASH GUVENLIGI ===========
def _lambda_ve_partial_baglantilari(kaynak: str) -> list[str]:
    bulunan: list[str] = []
    for d in ast.walk(ast.parse(kaynak)):
        if isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) and d.func.attr == "connect":
            for a in d.args:
                if isinstance(a, ast.Lambda):
                    bulunan.append(f"lambda@{d.lineno}")
                if isinstance(a, ast.Call) and (getattr(a.func, "attr", None) == "partial" or getattr(a.func, "id", None) == "partial"):
                    bulunan.append(f"partial@{d.lineno}")
    return bulunan


@pytest.mark.parametrize("dosya", ["kabuk.py", "kenar_sekmesi.py", "uygulama.py", "geometri.py", "__init__.py", "__main__.py"])
def test_g_yapisal_connect_lambda_partial_yok(dosya: str) -> None:
    assert _lambda_ve_partial_baglantilari((SRC_UI / dosya).read_text(encoding="utf-8")) == [], dosya


def test_g_yapisal_bekci_pozitif_kontrol() -> None:
    ornek = "x.clicked.connect(lambda: self.f())\ny.clicked.connect(functools.partial(self.g, 1))\nz.clicked.connect(partial(self.h))\nw.clicked.connect(self.k)\n"
    assert _lambda_ve_partial_baglantilari(ornek) == ["lambda@1", "partial@2", "partial@3"]


def _ayri_surec(kod: str) -> dict[str, object]:
    ortam = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
    r = subprocess.run([sys.executable, "-c", kod, str(KOK)], capture_output=True, text=True, timeout=180, env=ortam, cwd=str(KOK))
    assert r.returncode == 0, f"rc={r.returncode}\n{r.stderr[-1500:]}"
    sonuc: dict[str, object] = json.loads(r.stdout.strip().splitlines()[-1])
    sonuc["stderr"] = r.stderr
    return sonuc


BASLIK = "\n".join([
    "import os, sys, json, gc, weakref; os.environ['QT_QPA_PLATFORM']='offscreen'; sys.path.insert(0, sys.argv[1])",
    "from PySide6 import QtGui, QtWidgets, QtCore",
    "from src.ui.kabuk import AnaPencere",
    "app = QtWidgets.QApplication([]); app.setQuitOnLastWindowClosed(False); e = QtGui.QGuiApplication.primaryScreen(); r = {}",
    "def dongu(ms):\n    l = QtCore.QEventLoop(); QtCore.QTimer.singleShot(ms, l.quit); l.exec()",
    "def gorunur(): return [type(w).__name__ for w in QtWidgets.QApplication.topLevelWidgets() if w.isVisible()]",
])


def test_g_ayri_surec_cikis_dinleyicisi_son_referansi_dusurur_cokme_yok() -> None:
    """`cikis_istendi` dinleyicisi (urun: `app.quit` + pencereyi birakma) AnaPencere'nin son referansini sinyal icinde dusurur
    -- gonderen (`dugme_kapat.clicked` zinciri) yayim sirasinda silinir: cokme yok, sekme toplanir, gorunur ust-duzey 0."""
    kod = BASLIK + "\n" + "\n".join([
        "tut = []",
        "def dinleyici():\n    tut.clear(); gc.collect()",
        "p = AnaPencere(e, tepsi_kullanilabilir=True); tut.append(p); p.show(); p.kenara_al(); dongu(30)",
        "ws = weakref.ref(p.sekme); wp = weakref.ref(p); p.cikis_istendi.connect(dinleyici)",
        "p.dugme_kapat.click(); del p; gc.collect(); dongu(50)",
        "r['toplandi'] = [wp() is None, ws() is None]; r['gorunur'] = gorunur()",
        "print(json.dumps(r))",
    ])
    s = _ayri_surec(kod)
    assert s["toplandi"] == [True, True] and s["gorunur"] == [] and "Traceback" not in str(s["stderr"])


def test_g_ayri_surec_mod_dinleyicisi_son_referansi_dusurur_cokme_yok() -> None:
    """`anlik_cevir_istendi` dinleyicisi kenar durumundaki AnaPencere'nin son referansini dusurur: sekmenin `_anlik_tiki`
    zinciri (dugme -> sekme -> AnaPencere.emit) yayim sirasinda sahibini kaybeder: cokme yok, sekme toplanir."""
    kod = BASLIK + "\n" + "\n".join([
        "tut = []",
        "def dinleyici():\n    tut.clear(); gc.collect()",
        "p = AnaPencere(e, tepsi_kullanilabilir=True); tut.append(p); p.show(); p.kenara_al(); dongu(30)",
        "s = p.sekme; ws = weakref.ref(s); wp = weakref.ref(p); p.anlik_cevir_istendi.connect(dinleyici); del p",
        "s.dugme_anlik.click(); del s; gc.collect(); dongu(50)",
        "r['toplandi'] = [wp() is None, ws() is None]; r['gorunur'] = gorunur()",
        "print(json.dumps(r))",
    ])
    s = _ayri_surec(kod)
    assert s["toplandi"] == [True, True] and s["gorunur"] == [] and "Traceback" not in str(s["stderr"])


def test_g_ayri_surec_kapandi_dinleyicisi_son_referansi_dusurur_cokme_yok() -> None:
    """`kapandi` dinleyicisi (sekme.close() icinde) AnaPencere'nin son referansini dusurur: Qt close akisi `QPointer` korumali,
    cokme yok; sekme de toplanir."""
    kod = BASLIK + "\n" + "\n".join([
        "tut = []",
        "def dinleyici():\n    tut.clear(); gc.collect()",
        "p = AnaPencere(e, tepsi_kullanilabilir=True); tut.append(p); p.show(); p.kenara_al(); dongu(30)",
        "ws = weakref.ref(p.sekme); wp = weakref.ref(p); p.sekme.kapandi.connect(dinleyici)",
        "p.sekme.close(); del p; gc.collect(); dongu(50)",
        "r['toplandi'] = [wp() is None, ws() is None]; r['gorunur'] = gorunur()",
        "print(json.dumps(r))",
    ])
    s = _ayri_surec(kod)
    assert s["toplandi"] == [True, True] and s["gorunur"] == [] and "Traceback" not in str(s["stderr"])


def test_g_ayri_surec_calistir_gercek_exec_kenar_close_all_windows_quit() -> None:
    """Urun yolu: `calistir` + gercek `app.exec()`; kenar durumunda 0 ms sonra `closeAllWindows()` -> sekme kapanir -> pencere
    gorunur -> kapanir -> `cikis_istendi` -> `app.quit` -> `calistir` 0 doner (oturum kapanisi simulasyonu)."""
    kod = "\n".join([
        "import os, sys, json; os.environ['QT_QPA_PLATFORM']='offscreen'; sys.path.insert(0, sys.argv[1])",
        "from PySide6 import QtWidgets, QtCore",
        "from src.ui.uygulama import calistir",
        "r = {}",
        "def calistirici(app, p):",
        "    p.kenara_al(); n = []; p.cikis_istendi.connect(lambda: n.append(1))",
        "    QtCore.QTimer.singleShot(30, QtWidgets.QApplication.closeAllWindows)",
        "    QtCore.QTimer.singleShot(3000, lambda: app.exit(99))",
        "    rc = app.exec(); r['n'] = len(n); r['uclu'] = [p.isVisible(), p.sekme.isVisible(), p.tepsi.gorunur()]; r['durum'] = str(p.durum); return rc",
        "r['rc'] = calistir([], calistirici=calistirici)",
        "print(json.dumps(r))",
    ])
    s = _ayri_surec(kod)
    assert s["rc"] == 0 and s["n"] == 1 and s["uclu"] == [False, False, False] and s["durum"] == "gorunur"
