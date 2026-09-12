"""T-012 Tester-B (kor) -- TUR 2: paket v3 ▲▲ maddeleri satir satir, demo v3 kotu kullanim, tur-1 bulgulari ters cevrilmis.

Offscreen (pytest-qt). Bolumler:
  H  tur-1 bulgularinin TERS CEVRILMIS dogrulamasi (O-B1 `kapandi`, D-B6 mandal, Y-B1 Esc, O-B2 secimde sekme gizli)
  I  ▲▲ satir satir: K1 omur (del+gc / deleteLater / ref dusurulmeden deleteLater) + `kapandi` (close yayar, hide yaymaz),
     K4 mandal (uc dugme, sag tik, surukleme, hide/show), K5 balon (surec basina bir kez; ikinci ornek; tepsisiz sayac),
     ust sinir `ValueError` (Qt nesnesi yaratilmadan; mesaj gerekce iceriyor), `PANEL_BOYUTU` ve lambda AST bekcileri (pozitif kontrollu)
  J  demo/kabuk.py v3 -- gercek cagiran: `SecimKatmani` press-Esc-release (`_basla` sifirlanmiyor), `bitti()` cift cagri,
     `bolge_izle` gorunur durumdan (sekme.show() cagrilmaz), `cikis_istendi` pencereleri kapatir, `kapandi` demo akisinda
Beklentiler paketten/istekten literal; ozel mekanizma (`_yokla`, `_ac`, `_cikis_bekleniyor`) KANCALANMAZ (§4.6/7).
"""
from __future__ import annotations

import ast
import gc
import os
import subprocess
import sys
import weakref
from collections.abc import Iterator
from pathlib import Path

import pytest
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest

from src.ui.geometri import PANEL_BOYUTU, Kenar, sekme_icinde, sekme_kapali_dikdortgeni
from src.ui.kabuk import AnaPencere, KabukDurumu, Tepsi
from src.ui.kenar_sekmesi import KenarSekmesi

KOK = Path(__file__).resolve().parents[4]
UI = KOK / "src" / "ui"
R, ACILMA, KAPANMA, YOKLAMA = 26, 120, 450, 60
UZAK = QPoint(5, 5)
UST = ACILMA + 2 * YOKLAMA + 300
ORTAM = {**os.environ, "QT_QPA_PLATFORM": "offscreen", "PYTHONIOENCODING": "utf-8"}


class Imlec:
    def __init__(self, p: QPoint = UZAK) -> None:
        self.p = QPoint(p)
        self.sayac = 0

    def __call__(self) -> QPoint:
        self.sayac += 1
        return QPoint(self.p)


def uclu(p: AnaPencere) -> tuple[bool, bool, bool]:
    return (p.isVisible(), p.sekme.isVisible(), p.tepsi.gorunur())


def merkez(s: KenarSekmesi) -> QPoint:
    g = s.frameGeometry()
    return QPoint(g.right() - 3, g.top() + s.yaricap) if s.kenar is Kenar.SAG else QPoint(g.left() + 3, g.top() + s.yaricap)


def ac(qtbot, s: KenarSekmesi, imlec: Imlec) -> None:
    """Mandal-farkinda acma: once disari (bir yoklama), sonra diske; paket K4 ▲▲ 'diskten cikana kadar' kurali."""
    imlec.p = UZAK
    qtbot.wait(2 * YOKLAMA)
    imlec.p = merkez(s)
    qtbot.waitUntil(lambda: s.acik, timeout=UST)


def kenar_ucu(s: KenarSekmesi, dugme: QtWidgets.QPushButton) -> tuple[QPoint, QPoint] | None:
    """Dugmenin KAPALI diskin icinde kalan bir noktasi (yerel, global) -- disk merkezine en yakin; yoksa None
    (o dugmeden dogal tik mandal sinifina giremez)."""
    kapali = sekme_kapali_dikdortgeni(s.ekran_dikdortgeni, s.y, s.yaricap, s.kenar)
    merkez_x = kapali.right() + 1 if s.kenar is Kenar.SAG else kapali.left()
    merkez_y = kapali.top() + s.yaricap
    en_iyi: tuple[int, QPoint, QPoint] | None = None
    for yx in range(dugme.width()):  # tam dikdortgen (kenar pikselleri dahil): implementer'in kesisim yardimcisiyla ayni evren
        for yy in range(dugme.height()):
            yerel = QPoint(yx, yy)
            kuresel = dugme.mapToGlobal(yerel)
            if sekme_icinde(kapali, kuresel, s.yaricap, s.kenar):
                d2 = (kuresel.x() - merkez_x) ** 2 + (kuresel.y() - merkez_y) ** 2
                if en_iyi is None or d2 < en_iyi[0]:
                    en_iyi = (d2, yerel, kuresel)
    return None if en_iyi is None else (en_iyi[1], en_iyi[2])


def gorunur_ust_duzey() -> list[QtWidgets.QWidget]:
    return [w for w in QtWidgets.QApplication.topLevelWidgets() if w.isVisible()]


def taze_surec(kod: str, zaman_asimi: float = 40.0) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", "import sys; sys.path.insert(0, r'%s')\n" % str(KOK) + kod],
        cwd=str(KOK), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=zaman_asimi, env=ORTAM,
    )


@pytest.fixture
def imlec() -> Imlec:
    return Imlec()


@pytest.fixture
def pencere(qtbot, imlec: Imlec) -> Iterator[AnaPencere]:
    p = AnaPencere(tepsi_kullanilabilir=True, imlec_konumu=imlec)
    qtbot.addWidget(p)
    p.show()
    qtbot.waitExposed(p)
    yield p
    p.kapat()


@pytest.fixture
def pencere_tepsisiz(qtbot, imlec: Imlec) -> Iterator[AnaPencere]:
    p = AnaPencere(tepsi_kullanilabilir=False, imlec_konumu=imlec)
    qtbot.addWidget(p)
    p.show()
    qtbot.waitExposed(p)
    yield p
    p.kapat()


@pytest.fixture
def sekme(qtbot, imlec: Imlec) -> Iterator[KenarSekmesi]:
    s = KenarSekmesi(QtGui.QGuiApplication.primaryScreen(), imlec_konumu=imlec)
    qtbot.addWidget(s)
    s.show()
    qtbot.waitExposed(s)
    yield s
    s.hide()


@pytest.fixture
def balon_sifir(monkeypatch: pytest.MonkeyPatch) -> None:
    """Sinif sayacini test basinda sifirlar; test bitince monkeypatch geri alir (onceki testlerin tuketimi bu testi etkilemez)."""
    monkeypatch.setattr(AnaPencere, "_balon_gosterildi", False)


# =====================================================================================
# H · tur-1 bulgulari TERS CEVRILDI (kod artik paket v3 ▲▲ / sef duzeltmesi gibi davraniyor mu)
# =====================================================================================

@pytest.mark.parametrize("tepsili", [True, False])
def test_h1_ob1_sekme_dis_close_kenar_durumunda_gorunure_doner(qtbot, imlec: Imlec, tepsili: bool) -> None:
    """Tur-1 x1/x2 (xfail) ters: `sekme.close()` kenar durumunda -> `kapandi` 1, `goster()` -> durum GORUNUR, uclu (T,F,F);
    `AnaPencere.kapandi` False, `cikis_istendi` 0 (kapatma DEGIL, geri donus). Tepsisiz konfigurasyonda da (zombi yok)."""
    p = AnaPencere(tepsi_kullanilabilir=tepsili, imlec_konumu=imlec)
    qtbot.addWidget(p)
    p.show(); qtbot.waitExposed(p)
    try:
        cikis: list[int] = []; kapandi: list[int] = []
        p.cikis_istendi.connect(lambda: cikis.append(1))
        p.sekme.kapandi.connect(lambda: kapandi.append(1))
        p.kenara_al(); qtbot.wait(30)
        assert uclu(p) == (False, True, tepsili)
        p.sekme.close(); qtbot.wait(50)
        assert kapandi == [1]
        assert p.durum is KabukDurumu.GORUNUR and uclu(p) == (True, False, False), (p.durum, uclu(p))
        assert p.kapandi is False and cikis == []
        assert p.sekme.yokluyor is False
        # geri donus tam: kenara al yeniden calisir (sekme `close()` sonrasi yeniden gosterilebilir)
        p.kenara_al(); qtbot.wait(30)
        assert uclu(p) == (False, True, tepsili) and p.sekme.yokluyor
    finally:
        p.kapat()


def test_h2_ob1_kapandi_close_yayar_hide_yaymaz(qtbot, sekme: KenarSekmesi) -> None:
    """Paket K1 ▲▲: `close()` -> `kapandi`; kabugun kendi yolu `hide()` YAYMAZ. Qt olcumu (belge): `hide()` ile gizlenmis sekmeye
    `close()` YAYAR (Qt gizli pencereye de closeEvent gonderir; j5 kabuk tarafi); `close()` ile kapanmis sekmeye ikinci `close()`
    YAYMAZ; yeniden `show()` sonrasi `close()` yine yayar."""
    s = sekme
    sayac: list[int] = []
    s.kapandi.connect(lambda: sayac.append(1))
    s.hide(); qtbot.wait(20)
    assert sayac == [], "hide() kapandi yaymamali"
    s.close(); qtbot.wait(20)
    assert sayac == [1], "hide() ile gizlenmis sekmeye close() closeEvent alir (Qt)"
    s.show(); qtbot.wait(20)
    s.close(); qtbot.wait(20)
    assert sayac == [1, 1] and not s.isVisible() and not s.yokluyor
    s.close(); qtbot.wait(20)
    assert sayac == [1, 1], "close() ile kapanmis sekmeye ikinci close() yaymaz (Qt is_closing/QWindow yolu; belge)"
    s.show(); qtbot.wait(20); s.close(); qtbot.wait(20)
    assert sayac == [1, 1, 1]


@pytest.mark.parametrize("dugme_adi", ["dugme_anlik", "dugme_bolge", "dugme_goster"])
def test_h3_db6_mandal_mod_tiki_sonrasi_diskte_kalan_imlec_yeniden_acmaz(qtbot, pencere: AnaPencere, imlec: Imlec, dugme_adi: str) -> None:
    """Tur-1 c7 (D-B6) ters: tik noktasi kapali diskin ICINDE (dugmenin kenar ucu); sinyal aninda panel kapali;
    imlec orada kalirsa `acilma_ms + 3*yoklama` sonra HALA kapali (paket K4 ▲▲); diskten cikip girince acilir (pozitif kontrol)."""
    p = pencere
    p.kenara_al(); qtbot.wait(20)
    s = p.sekme
    ac(qtbot, s, imlec)
    d: QtWidgets.QPushButton = getattr(s, dugme_adi)
    nokta = kenar_ucu(s, d)
    if nokta is None:
        pytest.skip(f"{dugme_adi}: dugmenin hicbir pikseli kapali diskin icinde degil -> mandal sinifi bu dugmeden dogmaz")
    yerel, kuresel = nokta
    print(f"BILGI {dugme_adi}: disk ici tik noktasi yerel=({yerel.x()},{yerel.y()}) dugme={d.width()}x{d.height()} (kenardan {min(yerel.x(), yerel.y(), d.width()-1-yerel.x(), d.height()-1-yerel.y())} px iceride)")
    imlec.p = kuresel
    sinyal = {"dugme_anlik": s.anlik_cevir, "dugme_bolge": s.bolge_izle, "dugme_goster": s.pencereyi_goster}[dugme_adi]
    aninda: list[bool] = []
    sinyal.connect(lambda: aninda.append(s.acik))
    if dugme_adi == "dugme_goster":
        p.sekme.pencereyi_goster.disconnect(p.goster)  # kabuk sekmeyi gizlerdi; mandalin kendisini olcmek icin ayir
    QTest.mouseClick(d, Qt.MouseButton.LeftButton, pos=yerel)
    assert aninda == [False]
    assert s.frameGeometry().size() == QtCore.QSize(R, 2 * R)
    qtbot.wait(ACILMA + 3 * YOKLAMA)
    assert s.acik is False, "mandal: imlec diskte kalsa da yeniden acilmamali"
    n0 = imlec.sayac
    qtbot.wait(2 * YOKLAMA)
    assert imlec.sayac > n0, "yoklayici mandal sirasinda da calisiyor (imlec okunuyor)"
    imlec.p = UZAK; qtbot.wait(2 * YOKLAMA)
    imlec.p = kuresel
    qtbot.waitUntil(lambda: s.acik, timeout=UST)


def test_h3b_mandal_surukleme_ile_kalkmaz_hide_show_sifirlar_sag_tik_koymaz(qtbot, sekme: KenarSekmesi, imlec: Imlec) -> None:
    """Mandal yalniz diskten cikisla kalkar: ayni noktada bas/birak (surukleme) kaldirmaz; `hide()/show()` sifirlar
    (demo secim akisi: hide -> ... -> show, imlec hala diskteyse panel acilir -- hover davranisi, belge);
    sag tik mandal koymaz (kapali sekmeye sag tik + imlec diskte -> panel acilir)."""
    s = sekme
    ac(qtbot, s, imlec)
    nokta = kenar_ucu(s, s.dugme_anlik)
    assert nokta is not None
    yerel, kuresel = nokta
    imlec.p = kuresel
    QTest.mouseClick(s.dugme_anlik, Qt.MouseButton.LeftButton, pos=yerel)
    qtbot.wait(ACILMA + 3 * YOKLAMA)
    assert s.acik is False
    # ayni noktada bas/birak -- surukleme sinifi; mandal kalkmaz
    yerel_s = s.mapFromGlobal(kuresel)
    QTest.mousePress(s, Qt.MouseButton.LeftButton, pos=yerel_s); qtbot.wait(YOKLAMA)
    QTest.mouseRelease(s, Qt.MouseButton.LeftButton, pos=yerel_s)
    qtbot.wait(ACILMA + 3 * YOKLAMA)
    assert s.acik is False and s.surukleniyor is False
    # hide/show sifirlar: imlec hala diskte -> acilir
    s.hide(); qtbot.wait(20); s.show()
    qtbot.waitUntil(lambda: s.acik, timeout=UST)
    # sag tik mandal koymaz
    imlec.p = UZAK
    qtbot.waitUntil(lambda: not s.acik, timeout=KAPANMA + 2 * YOKLAMA + 300)
    imlec.p = merkez(s)
    with qtbot.waitSignal(s.pencereyi_goster, timeout=500):
        QTest.mouseClick(s, Qt.MouseButton.RightButton, pos=s.mapFromGlobal(merkez(s)))
    qtbot.waitUntil(lambda: s.acik, timeout=UST)


def test_h4_c2x10_app_quit_kenar_durumunda_artik_kabugu_temiz_kapatir() -> None:
    """Tur-1 c2x10 ters (O-B1 yan etkisi, OLUMLU): `app.quit()` -> closeAllWindows -> sekme.close() -> `kapandi` -> `goster()`
    -> ana pencere GORUNUR olur -> closeAllWindows ana pencereyi de kapatir -> `kapat()` -> cikis 1, uclu (F,F,F).
    Tur 1'de ana pencere gizli kaldigi icin closeEvent almiyordu (cikis 0, tepsi ikonu kaliyordu)."""
    kod = "\n".join([
        "from PySide6.QtCore import QTimer",
        "from PySide6.QtWidgets import QApplication",
        "from src.ui.kabuk import AnaPencere",
        "app = QApplication([]); app.setQuitOnLastWindowClosed(False)",
        "p = AnaPencere(tepsi_kullanilabilir=True); p.show(); p.kenara_al()",
        "cikis = []; p.cikis_istendi.connect(lambda: cikis.append(1))",
        "QTimer.singleShot(100, app.quit)",
        "QTimer.singleShot(3000, lambda: (print('ZAMAN_ASIMI'), app.exit(9)))",
        "rc = app.exec()",
        "print('RC', rc, 'UCLU', p.isVisible(), p.sekme.isVisible(), p.tepsi.gorunur(), 'KAPANDI', p.kapandi, 'CIKIS', len(cikis), 'DURUM', str(p.durum))",
        "",
    ])
    r = taze_surec(kod)
    assert r.returncode == 0, (r.returncode, r.stderr[-800:])
    assert "RC 0 UCLU False False False KAPANDI True CIKIS 1 DURUM gorunur" in r.stdout, (r.stdout, r.stderr[-800:])


DEMO_KURULUM = (
    "import os\n"
    "from PySide6 import QtCore, QtWidgets\n"
    "from PySide6.QtTest import QTest\n"
    "from src.ui.kabuk import AnaPencere\n"
    "from src.ui.uygulama import calistir\n"
    "from demo.kabuk import _bagla\n"
    "from demo.bolge_izle import IzlemePenceresi, SecimKatmani\n"
    "durum = {}\n"
    "def katmanlar():\n"
    "    return [w for w in QtWidgets.QApplication.topLevelWidgets() if isinstance(w, SecimKatmani) and w.isVisible()]\n"
    "def izlemeler():\n"
    "    return [w for w in QtWidgets.QApplication.topLevelWidgets() if isinstance(w, IzlemePenceresi)]\n"
    "def sarici(app, pencere):\n"
    "    durum['p'] = pencere\n"
    "    pencere.cikis_istendi.connect(lambda: durum.__setitem__('cikis', durum.get('cikis', 0) + 1))\n"
    "    QtCore.QTimer.singleShot(200, lambda: adimlar(app, pencere))\n"
    "    QtCore.QTimer.singleShot(8000, lambda: (print('ZAMAN_ASIMI'), app.exit(9)))\n"
    "    return _bagla(app, pencere)\n"
)


def test_h5_yb1_ob2_demo_esc_uygulamayi_kapatmaz_secimde_sekme_gizli_sonra_geri() -> None:
    """Tur-1 f1 ters (sef duzeltmesi): kenar durumunda 'Bolge izle' -> katman acik, SEKME GIZLI (O-B2); Esc -> katman kapanir,
    `iptal` -> `bitti()` -> sekme GERI gelir, durum kenar, izleme penceresi YOK, surec YASAR (exec donmez);
    ardindan `kapat()` -> exec 0, kapandi True, cikis 1."""
    kod = DEMO_KURULUM + (
        "def adimlar(app, pencere):\n"
        "    pencere.kenara_al()\n"
        "    QtCore.QTimer.singleShot(100, lambda: pencere.sekme.bolge_izle.emit())\n"
        "    def esc():\n"
        "        print('KATMAN', len(katmanlar()), 'UCLU', pencere.isVisible(), pencere.sekme.isVisible(), 'YOKLUYOR', pencere.sekme.yokluyor)\n"
        "        if katmanlar(): QTest.keyClick(katmanlar()[0], QtCore.Qt.Key.Key_Escape)\n"
        "    QtCore.QTimer.singleShot(400, esc)\n"
        "    def sonra():\n"
        "        print('ESC_SONRASI KATMAN', len(katmanlar()), 'IZLEME', len(izlemeler()), 'UCLU', pencere.isVisible(), pencere.sekme.isVisible(), 'DURUM', str(pencere.durum), 'YOKLUYOR', pencere.sekme.yokluyor)\n"
        "        pencere.kapat()\n"
        "    QtCore.QTimer.singleShot(900, sonra)\n"
        "rc = calistir([], calistirici=sarici)\n"
        "p = durum['p']\n"
        "print('RC', rc, 'KAPANDI', p.kapandi, 'CIKIS', durum.get('cikis', 0))\n"
    )
    r = taze_surec(kod)
    assert r.returncode == 0, (r.returncode, r.stderr[-1500:])
    assert "KATMAN 1 UCLU False False YOKLUYOR False" in r.stdout, (r.stdout, r.stderr[-800:])
    assert "ESC_SONRASI KATMAN 0 IZLEME 0 UCLU False True DURUM kenar YOKLUYOR True" in r.stdout, (r.stdout, r.stderr[-800:])
    assert "ZAMAN_ASIMI" not in r.stdout
    assert "RC 0 KAPANDI True CIKIS 1" in r.stdout, (r.stdout, r.stderr[-800:])


# =====================================================================================
# I · ▲▲ satir satir
# =====================================================================================

def test_i1_k1_omur_kenar_durumunda_del_gc_sekme_tepsi_menu_silinir_yoklama_durur(qtbot, imlec: Imlec) -> None:
    """K1 ▲▲: `AnaPencere` son referansi dusunce (`del` + gc) sekme, tepsi ve menu SILINIR (weakref None), gorunur ust-duzey 0,
    enjekte imlec bir daha OKUNMAZ (yoklayici durdu). Bagimsiz olcum: implementer'in fixture'i yok, qtbot'a eklenmez."""
    p = AnaPencere(tepsi_kullanilabilir=True, imlec_konumu=imlec)
    p.show(); qtbot.waitExposed(p)
    p.kenara_al(); qtbot.wait(3 * YOKLAMA)
    assert p.sekme.isVisible() and imlec.sayac > 0
    wr_s, wr_t, wr_m = weakref.ref(p.sekme), weakref.ref(p.tepsi), weakref.ref(p.tepsi.menu)
    wr_p = weakref.ref(p)
    del p
    gc.collect(); qtbot.wait(300)
    assert wr_p() is None, "AnaPencere sarmalayicisi canli kaldi"
    assert wr_s() is None, "sekme canli kaldi (ZOMBI, Y-A1 sinifi)"
    assert wr_t() is None and wr_m() is None, "tepsi/menu canli kaldi"
    assert gorunur_ust_duzey() == []
    n0 = imlec.sayac
    qtbot.wait(4 * YOKLAMA)
    assert imlec.sayac == n0, "yoklayici olu sekme uzerinden imlec okumaya devam ediyor"


def test_i1b_k1_omur_pozitif_kontrol_lambda_baglantili_widget_canli_kalir(qtbot) -> None:
    """Kural 10: olcu ateslenebiliyor -- `clicked.connect(lambda: self...)` bagli minimal pencere `del`+gc sonrasi CANLI ve gorunur;
    ayni pencere bagli yontemle toplanir."""
    class W(QtWidgets.QWidget):
        def __init__(self, lambda_ile: bool) -> None:
            super().__init__(None, Qt.WindowType.Tool)
            self.d = QtWidgets.QPushButton("x", self)
            self.n = 0
            if lambda_ile:
                self.d.clicked.connect(lambda: setattr(self, "n", self.n + 1))
            else:
                self.d.clicked.connect(self._tik)

        def _tik(self) -> None:
            self.n += 1

    sonuc: dict[bool, bool] = {}
    for lambda_ile in (True, False):
        w = W(lambda_ile); w.show(); qtbot.waitExposed(w)
        wr = weakref.ref(w)
        del w; gc.collect(); qtbot.wait(100)
        sonuc[lambda_ile] = wr() is not None
        if wr() is not None:
            wr().hide(); wr().deleteLater(); qtbot.wait(50)
    assert sonuc == {True: True, False: False}, sonuc


def test_i2_k1_omur_deleteLater_ref_dusurulunce_silinir(qtbot, imlec: Imlec) -> None:
    """K1 ▲▲ `deleteLater` yolu (paketin lafzi): `p.deleteLater(); del p` -> sekme silinir, gorunur 0, imlec okunmaz."""
    p = AnaPencere(tepsi_kullanilabilir=True, imlec_konumu=imlec)
    p.show(); qtbot.waitExposed(p)
    p.kenara_al(); qtbot.wait(2 * YOKLAMA)
    wr_s = weakref.ref(p.sekme)
    p.deleteLater(); del p
    qtbot.wait(300); gc.collect(); qtbot.wait(100)
    assert wr_s() is None and gorunur_ust_duzey() == []
    n0 = imlec.sayac; qtbot.wait(4 * YOKLAMA)
    assert imlec.sayac == n0


@pytest.mark.xfail(strict=True, reason="BULGU O-B5: `deleteLater()` + Python referansi tutuluyor -> C++ AnaPencere olu, sekme GORUNUR+YOKLUYOR (zombi, Y-A1 sinifi, ikinci yol); 1 satir: `self.destroyed.connect(self._sekme.deleteLater)` (olculdu, uc yolda cokme yok)")
def test_i2b_k1_omur_KOTU_KULLANIM_deleteLater_python_referansi_dusurulmeden(qtbot, imlec: Imlec) -> None:
    """KOTU KULLANIM (sonraki ajan: `self.pencere.deleteLater()` deyip ozniteligi tutar -- Qt'de yaygin desen):
    C++ `AnaPencere` silinir ama Python sarmalayicisi (ve `__dict__`teki `_sekme`) yasar -> sekme ne olur? OLCUM.
    Beklenti (paket K1 ▲▲ 'AnaPencere dusurulunce sekme silinir'): sekme gorunur kalmamali, yoklayici durmali."""
    p = AnaPencere(tepsi_kullanilabilir=True, imlec_konumu=imlec)
    p.show(); qtbot.waitExposed(p)
    p.kenara_al(); qtbot.wait(2 * YOKLAMA)
    wr_s = weakref.ref(p.sekme)
    p.deleteLater()
    qtbot.wait(300); gc.collect(); qtbot.wait(100)
    cpp_olu = False
    try:
        p.isVisible()
    except RuntimeError:
        cpp_olu = True
    n0 = imlec.sayac; qtbot.wait(4 * YOKLAMA); okuma_devam = imlec.sayac > n0
    sekme_canli = wr_s() is not None
    sekme_gorunur = bool(sekme_canli and wr_s().isVisible())
    gorunurler = [type(w).__name__ for w in gorunur_ust_duzey()]
    try:
        assert cpp_olu, "C++ AnaPencere deleteLater ile silinmedi (olcum on kosulu)"
        assert not sekme_gorunur and not okuma_devam, (
            f"ZOMBI: C++ AnaPencere olu, sekme canli={sekme_canli} gorunur={sekme_gorunur} yoklayici okuyor={okuma_devam} gorunur ust-duzey={gorunurler}")
    finally:
        if wr_s() is not None:
            wr_s().hide(); wr_s().deleteLater()
        del p; gc.collect(); qtbot.wait(100)


def test_i3_k1_kapandi_del_sirasinda_dis_dinleyiciye_yayilir_mi(qtbot, imlec: Imlec) -> None:
    """Belge olcumu: kenar durumunda `del p` -> sekme C++ yikilirken Qt gorunur pencereye closeEvent gonderir mi
    (`kapandi` dis dinleyiciye ulasir mi)? Sonraki ajan `kapandi`ya 'kullanici sekmeyi kapatti' anlami yuklerse yikimda da alir."""
    p = AnaPencere(tepsi_kullanilabilir=True, imlec_konumu=imlec)
    p.show(); qtbot.waitExposed(p)
    p.kenara_al(); qtbot.wait(2 * YOKLAMA)
    sayac: list[int] = []
    p.sekme.kapandi.connect(lambda: sayac.append(1))
    wr_s = weakref.ref(p.sekme)
    del p; gc.collect(); qtbot.wait(200)
    assert wr_s() is None
    print(f"BILGI kapandi yikimda dis dinleyiciye ulasti={len(sayac)}")
    assert len(sayac) in (0, 1)


@pytest.mark.parametrize("args, gecerli", [
    (dict(yaricap=66), True), (dict(yaricap=67), False), (dict(yaricap=1), True), (dict(yaricap=0), False),
    (dict(acilma_ms=2**31 - 1), True), (dict(acilma_ms=2**31), False), (dict(kapanma_ms=2**31), False), (dict(acilma_ms=0), True),
    (dict(yoklama_ms=2**31 - 1), True), (dict(yoklama_ms=0), False), (dict(yoklama_ms=1), True),
])
def test_i4_ust_sinirlar_valueerror_qt_nesnesi_yaratilmadan_ve_mesaj_gerekceli(qtbot, args: dict[str, int], gecerli: bool) -> None:
    """Ust sinirlar (yaricap 66 = PANEL_BOYUTU.h//2, ms 2**31-1): sinir degeri KABUL, bir otesi `ValueError`; hata ANINDA hicbir
    ust-duzey widget yaratilmaz; mesaj sinir degerini ve (yaricap icin) gerekceyi ('panel') icerir -- cagiran icin tuzak degil."""
    n0 = len(QtWidgets.QApplication.topLevelWidgets())
    if gecerli:
        s = KenarSekmesi(QtGui.QGuiApplication.primaryScreen(), **args)
        qtbot.addWidget(s)
        for ad, deger in args.items():
            assert getattr(s, ad) == deger
        if "yaricap" in args:
            s.show(); qtbot.waitExposed(s)
            assert s.frameGeometry().size() == QtCore.QSize(args["yaricap"], 2 * args["yaricap"])
            s.hide()
        return
    with pytest.raises(ValueError) as hata:
        KenarSekmesi(QtGui.QGuiApplication.primaryScreen(), **args)
    assert len(QtWidgets.QApplication.topLevelWidgets()) == n0, "ValueError oncesi Qt nesnesi yaratildi"
    mesaj = str(hata.value)
    ad = next(iter(args))
    assert str(args[ad]) in mesaj and ad.split("_")[0] in mesaj, mesaj
    if ad == "yaricap":
        assert "66" in mesaj and "panel" in mesaj.lower(), mesaj
    else:
        assert str(2**31 - 1) in mesaj or "1 <=" in mesaj, mesaj


def test_i4b_yaricap_ust_siniri_panel_boyutuna_bagli_ve_66_panel_sekmeyi_kapsar(qtbot, imlec: Imlec) -> None:
    """Gerekce dogrulamasi: yaricap=66'da acik panel kapali sekme dikdortgenini KAPSAR (imlec diskten panele gecerken disari dusmez);
    67 olsaydi 2r=134 > panel.h=132 (kapsama bozulur) -- ust sinir keyfi degil, PANEL_BOYUTU'ndan turemis."""
    assert PANEL_BOYUTU.height() // 2 == 66
    s = KenarSekmesi(QtGui.QGuiApplication.primaryScreen(), yaricap=66, imlec_konumu=imlec)
    qtbot.addWidget(s); s.show(); qtbot.waitExposed(s)
    kapali = s.frameGeometry()
    imlec.p = UZAK; qtbot.wait(2 * YOKLAMA)
    imlec.p = QPoint(kapali.right() - 2, kapali.top() + 66)
    qtbot.waitUntil(lambda: s.acik, timeout=UST)
    assert s.frameGeometry().contains(kapali), (s.frameGeometry(), kapali)
    s.hide()


def test_i5_k5_balon_surec_basina_bir_kez_literal_argumanlar(qtbot, monkeypatch: pytest.MonkeyPatch, balon_sifir: None, imlec: Imlec) -> None:
    """K5 ▲▲: ilk `tepsiye_al()` -> `bildir("Suflör arka planda", ..., 2500)` TAM BIR KEZ; ayni ornekte goster/tepsiye_al x3 -> hala 1;
    IKINCI ornek -> 0 (surec basina). Casus: `Tepsi.bildir` sinif duzeyinde (kabugun cagri yolu), `showMessage` degil."""
    cagrilar: list[tuple[str, str, int]] = []
    monkeypatch.setattr(Tepsi, "bildir", lambda self, baslik, metin, ms: cagrilar.append((baslik, metin, ms)))
    p = AnaPencere(tepsi_kullanilabilir=True, imlec_konumu=imlec)
    qtbot.addWidget(p); p.show(); qtbot.waitExposed(p)
    try:
        p.tepsiye_al()
        assert cagrilar == [("Suflör arka planda", "Tepsi ikonuna tıklayınca pencere geri gelir.", 2500)]
        assert uclu(p) == (False, False, True)
        p.tepsiye_al(); p.goster(); p.tepsiye_al(); p.goster(); p.tepsiye_al()
        assert len(cagrilar) == 1
        assert AnaPencere._balon_gosterildi is True
        q = AnaPencere(tepsi_kullanilabilir=True, imlec_konumu=imlec)
        qtbot.addWidget(q); q.show(); qtbot.waitExposed(q)
        q.tepsiye_al()
        assert len(cagrilar) == 1, "ikinci ornek balon gosterdi (paket: surec basina bir kez)"
        q.kapat()
    finally:
        p.kapat()


def test_i5b_k5_tepsisiz_tepsiye_al_sayaci_tuketmez_sonra_tepsili_gosterir(qtbot, monkeypatch: pytest.MonkeyPatch, balon_sifir: None, imlec: Imlec) -> None:
    cagrilar: list[int] = []
    monkeypatch.setattr(Tepsi, "bildir", lambda self, baslik, metin, ms: cagrilar.append(1))
    p = AnaPencere(tepsi_kullanilabilir=False, imlec_konumu=imlec)
    qtbot.addWidget(p); p.show(); qtbot.waitExposed(p)
    p.tepsiye_al()
    assert p.durum is KabukDurumu.KENAR and cagrilar == [] and AnaPencere._balon_gosterildi is False
    p.kapat()
    q = AnaPencere(tepsi_kullanilabilir=True, imlec_konumu=imlec)
    qtbot.addWidget(q); q.show(); qtbot.waitExposed(q)
    q.tepsiye_al()
    assert cagrilar == [1]
    q.kapat()


def test_i5c_k5_balon_kapali_tepside_bildir_sessiz_ve_messageClicked_bagli_degil(qtbot, monkeypatch: pytest.MonkeyPatch, balon_sifir: None, imlec: Imlec) -> None:
    """Belge: balon `QSystemTrayIcon.showMessage` ile gider (tepsi yoksa sessiz); balona TIK (`messageClicked`) hicbir seye bagli DEGIL:
    'Tepsi ikonuna tiklayinca pencere geri gelir' balonuna tiklayan kullanici pencereyi geri ALAMAZ (dusuk, oneri)."""
    gosterilen: list[tuple[str, str]] = []
    monkeypatch.setattr(QtWidgets.QSystemTrayIcon, "showMessage", lambda self, baslik, metin, ikon, ms: gosterilen.append((baslik, str(ms))))
    p = AnaPencere(tepsi_kullanilabilir=True, imlec_konumu=imlec)
    qtbot.addWidget(p); p.show(); qtbot.waitExposed(p)
    p.tepsiye_al()
    assert gosterilen == [("Suflör arka planda", "2500")]
    p.tepsi.ikon.messageClicked.emit(); qtbot.wait(20)
    assert p.durum is KabukDurumu.TEPSI and uclu(p) == (False, False, True), "balona tik pencereyi getirmiyor (belge)"
    t = Tepsi(QtGui.QIcon(), None, kullanilabilir=False)
    t.bildir("a", "b", 1)
    assert len(gosterilen) == 1, "tepsisiz bildir showMessage cagirmamali"
    p.kapat()


def _ast_panel_boyutu_mutasyonu(kaynak: str) -> list[str]:
    """`PANEL_BOYUTU.setX(...)`/`PANEL_BOYUTU = ...`/`PANEL_BOYUTU += ...` / `X = PANEL_BOYUTU; X.setW` (takma ad tek adim) bulur."""
    agac = ast.parse(kaynak)
    takma = {"PANEL_BOYUTU"}
    for d in ast.walk(agac):
        if isinstance(d, ast.Assign) and isinstance(d.value, ast.Name) and d.value.id == "PANEL_BOYUTU":
            takma |= {t.id for t in d.targets if isinstance(t, ast.Name)}
    bulgu: list[str] = []
    for d in ast.walk(agac):
        if isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) and isinstance(d.func.value, ast.Name):
            if d.func.value.id in takma and d.func.attr.startswith(("set", "scale", "transpose", "grow", "shrink")):
                bulgu.append(f"{d.lineno}: {d.func.value.id}.{d.func.attr}()")
        if isinstance(d, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
            hedefler = d.targets if isinstance(d, ast.Assign) else [d.target]
            for t in hedefler:
                if isinstance(t, ast.Name) and t.id == "PANEL_BOYUTU" and not (isinstance(d, ast.AnnAssign) and d.value is not None and isinstance(d.value, ast.Call)):
                    bulgu.append(f"{d.lineno}: PANEL_BOYUTU yeniden atandi")
    return bulgu


def _ast_lambda_connect(kaynak: str) -> list[str]:
    agac = ast.parse(kaynak)
    return [f"{d.lineno}" for d in ast.walk(agac)
            if isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) and d.func.attr == "connect"
            and any(isinstance(a, ast.Lambda) for a in d.args)]


@pytest.mark.parametrize("dosya", sorted(p.name for p in UI.glob("*.py")))
def test_i6_ast_bekciler_panel_boyutu_mutasyonu_ve_lambda_connect_yok(dosya: str) -> None:
    kaynak = (UI / dosya).read_text(encoding="utf-8")
    assert _ast_panel_boyutu_mutasyonu(kaynak) == [], dosya
    assert _ast_lambda_connect(kaynak) == [], dosya
    # functools.partial de self'i tutar (docstring 'KULLANILMAZ'): import bile yok
    agac = ast.parse(kaynak)
    assert not any(isinstance(d, (ast.Import, ast.ImportFrom)) and "functools" in ast.dump(d) for d in ast.walk(agac)), dosya


def test_i6b_ast_bekciler_pozitif_kontrol() -> None:
    assert _ast_panel_boyutu_mutasyonu("from src.ui.geometri import PANEL_BOYUTU\nPANEL_BOYUTU.setWidth(300)\n") == ["2: PANEL_BOYUTU.setWidth()"]
    assert _ast_panel_boyutu_mutasyonu("P = PANEL_BOYUTU\nP.setHeight(1)\n") == ["2: P.setHeight()"]
    assert _ast_panel_boyutu_mutasyonu("PANEL_BOYUTU = QSize(1, 1)\n") == ["1: PANEL_BOYUTU yeniden atandi"]
    assert _ast_panel_boyutu_mutasyonu("PANEL_BOYUTU: Final[QSize] = QSize(200, 132)\nx = PANEL_BOYUTU.width()\n") == []
    assert _ast_lambda_connect("s.clicked.connect(lambda: self.x())\n") == ["1"]
    assert _ast_lambda_connect("s.clicked.connect(self.x)\n") == []


def test_i7_k1_available_geometry_changed_baglantisi_yapicinin_son_satiri(qtbot) -> None:
    """Docstring iddiasi (Tester-A D-A4): `availableGeometryChanged.connect` yapicinin SON ifadesidir -> yapici tasarsa yarim kurulu
    nesne ekran sinyaline bagli kalmaz. AST: `__init__` govdesinin son ifadesi bu cagri. (Mutant C-4 bu bekciyle yakalanir.)"""
    agac = ast.parse((UI / "kenar_sekmesi.py").read_text(encoding="utf-8"))
    init = next(f for c in ast.walk(agac) if isinstance(c, ast.ClassDef) and c.name == "KenarSekmesi"
                for f in c.body if isinstance(f, ast.FunctionDef) and f.name == "__init__")
    son = init.body[-1]
    assert isinstance(son, ast.Expr) and isinstance(son.value, ast.Call)
    f = son.value.func
    assert isinstance(f, ast.Attribute) and f.attr == "connect" and isinstance(f.value, ast.Attribute) and f.value.attr == "availableGeometryChanged", ast.dump(son)


# =====================================================================================
# J · demo/kabuk.py v3 -- gercek cagiran; kotu kullanim
# =====================================================================================

@pytest.mark.xfail(strict=True, reason="BULGU D-B10 (sef, demo): Esc `_basla`yi sifirlamiyor; Esc'ten SONRA gelen release `secildi` yayar -> iptal edilen secim izleme penceresi acar (Qt olay yolu: QTest ile olculdu; gercek OS'te capture SW_HIDE ile birakiliyor mu -> sonda_2a S9)")
def test_j1_secim_katmani_press_esc_release_secildi_yayar_mi(qtbot) -> None:
    """KOTU KULLANIM (sef, demo): kullanici surukleme SIRASINDA Esc basar, sonra fareyi birakir. `keyPressEvent` `_basla`yi
    SIFIRLAMIYOR; `iptal` + `close()` (gizlenir). Ardindan release olayi gelirse `secildi` yayilir mi -> iptal edilen secim
    yine de izleme penceresi acar. Iki kanal: (a) QTest (Qt olay yolu), (b) dogrudan `mouseReleaseEvent` (OS teslim ederse)."""
    from demo.bolge_izle import SecimKatmani
    from src.contracts.models import Rect

    k = SecimKatmani(Rect(x=0, y=0, w=600, h=400))
    qtbot.addWidget(k); k.show(); qtbot.waitExposed(k)
    secildi: list[Rect] = []; iptal: list[int] = []
    k.secildi.connect(lambda r: secildi.append(r)); k.iptal.connect(lambda: iptal.append(1))
    QTest.mousePress(k, Qt.MouseButton.LeftButton, pos=QPoint(20, 20))
    QTest.mouseMove(k, QPoint(200, 150)); qtbot.wait(20)
    QTest.keyClick(k, Qt.Key.Key_Escape); qtbot.wait(20)
    assert iptal == [1] and not k.isVisible()
    QTest.mouseRelease(k, Qt.MouseButton.LeftButton, pos=QPoint(200, 150)); qtbot.wait(20)
    qtest_yolu = list(secildi)
    secildi.clear()
    ev = QtGui.QMouseEvent(QtCore.QEvent.Type.MouseButtonRelease, QtCore.QPointF(200, 150), QtCore.QPointF(200, 150),
                           Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier)
    k.mouseReleaseEvent(ev); qtbot.wait(20)
    dogrudan = list(secildi)
    print(f"BILGI Esc sonrasi release: QTest yolu secildi={len(qtest_yolu)} dogrudan olay secildi={len(dogrudan)} _basla sifirlandi={k._basla is None}")  # noqa: SLF001
    assert qtest_yolu == [] and dogrudan == [], f"Esc ile iptal edilen secim release'te yine de secildi: QTest={qtest_yolu} dogrudan={dogrudan}"


def test_j2_demo_bagla_secim_akisi_sekme_gizli_sonra_geri_izleme_acilir_cikis_pencereleri_kapatir() -> None:
    """Gercek cagiran, mutlu yol: kenar -> 'Bolge izle' -> katman (sekme GIZLI, yoklayici durdu) -> fareyle secim ->
    `IzlemePenceresi` gorunur + sekme GERI (yokluyor) + durum kenar -> `kapat()` -> `cikis_istendi` izleme/katman pencerelerini
    kapatir (demo lambda), exec 0."""
    kod = DEMO_KURULUM + (
        "def adimlar(app, pencere):\n"
        "    pencere.kenara_al()\n"
        "    QtCore.QTimer.singleShot(100, lambda: pencere.sekme.bolge_izle.emit())\n"
        "    def sec():\n"
        "        print('KATMAN', len(katmanlar()), 'SEKME', pencere.sekme.isVisible(), 'YOKLUYOR', pencere.sekme.yokluyor)\n"
        "        k = katmanlar()[0]\n"
        "        QTest.mousePress(k, QtCore.Qt.MouseButton.LeftButton, pos=QtCore.QPoint(40, 40))\n"
        "        QTest.mouseMove(k, QtCore.QPoint(300, 260))\n"
        "        QTest.mouseRelease(k, QtCore.Qt.MouseButton.LeftButton, pos=QtCore.QPoint(300, 260))\n"
        "    QtCore.QTimer.singleShot(400, sec)\n"
        "    def kontrol():\n"
        "        iz = izlemeler()\n"
        "        print('SECIM_SONRASI IZLEME', len(iz), 'GORUNUR', all(w.isVisible() for w in iz), 'KATMAN', len(katmanlar()), 'UCLU', pencere.isVisible(), pencere.sekme.isVisible(), 'DURUM', str(pencere.durum), 'YOKLUYOR', pencere.sekme.yokluyor)\n"
        "        durum['iz'] = iz\n"
        "        pencere.kapat()\n"
        "    QtCore.QTimer.singleShot(1200, kontrol)\n"
        "rc = calistir([], calistirici=sarici)\n"
        "p = durum['p']\n"
        "print('RC', rc, 'KAPANDI', p.kapandi, 'CIKIS', durum.get('cikis', 0), 'IZLEME_GORUNUR', [w.isVisible() for w in durum.get('iz', [])], 'SEKME', p.sekme.isVisible())\n"
    )
    r = taze_surec(kod)
    assert r.returncode == 0, (r.returncode, r.stderr[-1500:])
    assert "KATMAN 1 SEKME False YOKLUYOR False" in r.stdout, (r.stdout, r.stderr[-800:])
    assert "SECIM_SONRASI IZLEME 1 GORUNUR True KATMAN 0 UCLU False True DURUM kenar YOKLUYOR True" in r.stdout, (r.stdout, r.stderr[-800:])
    assert "RC 0 KAPANDI True CIKIS 1 IZLEME_GORUNUR [False] SEKME False" in r.stdout, (r.stdout, r.stderr[-800:])
    assert "ZAMAN_ASIMI" not in r.stdout


def test_j3_demo_bagla_gorunur_durumdan_bolge_izle_sekme_show_cagrilmaz() -> None:
    """Sef duzeltmesi denetimi: GORUNUR durumdan (pencere mod dugmesi) 'Bolge izle' -> sekme zaten gizli -> secim bitince
    `sekme.show()` CAGRILMAZ: durum gorunur kalir, sekme gizli, yoklayici kapali; ana pencere gorunur kalir (demo gizlemiyor)."""
    kod = DEMO_KURULUM + (
        "def adimlar(app, pencere):\n"
        "    QtCore.QTimer.singleShot(50, pencere.dugme_bolge.click)\n"
        "    def sec():\n"
        "        print('KATMAN', len(katmanlar()), 'UCLU', pencere.isVisible(), pencere.sekme.isVisible())\n"
        "        k = katmanlar()[0]\n"
        "        QTest.mousePress(k, QtCore.Qt.MouseButton.LeftButton, pos=QtCore.QPoint(40, 40))\n"
        "        QTest.mouseMove(k, QtCore.QPoint(300, 260))\n"
        "        QTest.mouseRelease(k, QtCore.Qt.MouseButton.LeftButton, pos=QtCore.QPoint(300, 260))\n"
        "    QtCore.QTimer.singleShot(400, sec)\n"
        "    def kontrol():\n"
        "        print('SONRA IZLEME', len(izlemeler()), 'UCLU', pencere.isVisible(), pencere.sekme.isVisible(), pencere.tepsi.gorunur(), 'DURUM', str(pencere.durum), 'YOKLUYOR', pencere.sekme.yokluyor)\n"
        "        pencere.kapat()\n"
        "    QtCore.QTimer.singleShot(1000, kontrol)\n"
        "rc = calistir([], calistirici=sarici)\n"
        "print('RC', rc)\n"
    )
    r = taze_surec(kod)
    assert r.returncode == 0, (r.returncode, r.stderr[-1500:])
    assert "KATMAN 1 UCLU True False" in r.stdout, (r.stdout, r.stderr[-800:])
    assert "SONRA IZLEME 1 UCLU True False False DURUM gorunur YOKLUYOR False" in r.stdout, (r.stdout, r.stderr[-800:])
    assert "RC 0" in r.stdout and "ZAMAN_ASIMI" not in r.stdout


def test_j4_demo_bagla_secim_sirasinda_tepsi_cikis_katman_kapanir_iptal_yayilmaz() -> None:
    """Secim acikken kullanici tepsi menusunden 'Cikis' -> `kapat()` -> `cikis_istendi`: `app.quit` + demo lambda katmani `close()`
    eder (`iptal` YAYILMAZ -> `bitti()` cagrilmaz -> olu kabukta `sekme.show()` denenmez); exec 0, gorunur ust-duzey 0."""
    kod = DEMO_KURULUM + (
        "def adimlar(app, pencere):\n"
        "    pencere.kenara_al()\n"
        "    QtCore.QTimer.singleShot(100, lambda: pencere.sekme.bolge_izle.emit())\n"
        "    def cikis():\n"
        "        k = katmanlar()[0]\n"
        "        k.iptal.connect(lambda: durum.__setitem__('iptal', durum.get('iptal', 0) + 1))\n"
        "        durum['k'] = k\n"
        "        pencere.tepsi.cikis_istendi.emit()\n"
        "    QtCore.QTimer.singleShot(400, cikis)\n"
        "rc = calistir([], calistirici=sarici)\n"
        "p = durum['p']\n"
        "gorunur = [type(w).__name__ for w in QtWidgets.QApplication.topLevelWidgets() if w.isVisible()]\n"
        "print('RC', rc, 'KAPANDI', p.kapandi, 'CIKIS', durum.get('cikis', 0), 'IPTAL', durum.get('iptal', 0), 'KATMAN_GORUNUR', durum['k'].isVisible(), 'SEKME', p.sekme.isVisible(), 'GORUNUR', gorunur)\n"
    )
    r = taze_surec(kod)
    assert r.returncode == 0, (r.returncode, r.stderr[-1500:])
    assert "RC 0 KAPANDI True CIKIS 1 IPTAL 0 KATMAN_GORUNUR False SEKME False GORUNUR []" in r.stdout, (r.stdout, r.stderr[-800:])


def test_j5_kapandi_demo_akisinda_hide_yaymaz_gizli_sekmeye_close_gostere_doner(qtbot, pencere: AnaPencere) -> None:
    """Demo `bolge_izle` sekmeyi `hide()` ile gizler: `kapandi` YAYILMAZ, durum KENAR kalir, pencere gizli kalir (surpriz yok);
    `show()` ile geri. Bir adim otesi (belge): kenar durumunda DISARIDAN gizlenmis sekmeye `close()` -> `kapandi` -> `goster()`:
    secim sirasinda birisi `sekme.close()` derse ana pencere secimin ortasinda gelir -- demo bunu yapmiyor."""
    p = pencere
    sayac: list[int] = []
    p.sekme.kapandi.connect(lambda: sayac.append(1))
    p.kenara_al(); qtbot.wait(20)
    p.sekme.hide(); qtbot.wait(20)
    assert sayac == [] and p.durum is KabukDurumu.KENAR and uclu(p) == (False, False, True) and not p.sekme.yokluyor
    p.sekme.show(); qtbot.wait(20)
    assert uclu(p) == (False, True, True) and p.sekme.yokluyor
    p.sekme.hide(); qtbot.wait(20)
    p.sekme.close(); qtbot.wait(20)
    assert sayac == [1] and p.durum is KabukDurumu.GORUNUR and uclu(p) == (True, False, False)


def test_j6_bitti_iki_kez_sekme_show_idempotent_yoklayici_tek(qtbot, pencere: AnaPencere, imlec: Imlec) -> None:
    """Demo `bitti()` iki kez cagrilsa (secildi + iptal ayni katmandan) `sekme.show()` x2: gorunur bir sekme, yoklama hizi tek
    (60 ms'de ~1 okuma; iki yoklayici olsaydi 2x)."""
    p = pencere
    p.kenara_al(); qtbot.wait(20)
    p.sekme.hide(); qtbot.wait(20)
    p.sekme.show(); p.sekme.show(); qtbot.wait(20)
    assert [w for w in gorunur_ust_duzey()] == [p.sekme]
    n0 = imlec.sayac; qtbot.wait(10 * YOKLAMA); n = imlec.sayac - n0
    assert 6 <= n <= 14, f"10 yoklama araliginda {n} okuma (tek yoklayici ~10 beklenir)"
