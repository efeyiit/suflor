"""T-012 Tester-B (kor) -- EK testler (oturum 2): yeniden giris, demo entegrasyonu (gercek cagiran), ekran degisimi.

Bolumler:
  C2 kotu kullanim devami (`test_c2x_*`): sinyal dinleyicisi icinden `kapat()`/`kenara_al()`; surukleme sirasinda
     sag tik; `availableGeometryChanged` panel ACIKKEN; kapat sonrasi `show()`; `cikis_istendi` dinleyicisi yeniden
     `kapat()`; tepsi `bildir` kapat sonrasi.
  F  demo/kabuk.py -- sefin entegrasyonu, urun kabugunun GERCEK cagirani (`test_f_*`): taze surecte `calistir` +
     `_bagla` ile kabuk ayakta; `SecimKatmani` Esc -> `QApplication.quit()` (kabuk `kapat()` cagrilmadan surec biter mi).
  G  taze surecte istek maddeleri: "arkaplanda calistirma" (tepsideyken surec yasiyor), "kapatma" (surec biter),
     `python -m src.ui` giris noktasi; WM_CLOSE'un `calistir` baglantisiyla sureci bitirmesi (offscreen: `close()`).
"""
from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from PySide6 import QtGui, QtWidgets
from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtTest import QTest

from src.ui.geometri import PANEL_BOYUTU, Kenar
from src.ui.kabuk import AnaPencere, KabukDurumu
from src.ui.kenar_sekmesi import KenarSekmesi

KOK = Path(__file__).resolve().parents[4]
R, ACILMA, KAPANMA, YOKLAMA = 26, 120, 450, 60
UZAK = QPoint(5, 5)
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
    imlec.p = merkez(s)
    qtbot.waitUntil(lambda: s.acik, timeout=ACILMA + 2 * YOKLAMA + 300)


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


def taze_surec(kod: str, timeout: int = 90) -> subprocess.CompletedProcess[str]:
    on = "import sys; sys.path.insert(0, %r)\n" % str(KOK)
    return subprocess.run([sys.executable, "-c", on + kod], capture_output=True, text=True, timeout=timeout, env=ORTAM, cwd=str(KOK))


# =====================================================================================
# C2 · kotu kullanim devami
# =====================================================================================

def test_c2x1_mod_sinyali_dinleyicisi_kapat_cagirir_yeniden_giris(qtbot, pencere: AnaPencere, imlec: Imlec) -> None:
    """`anlik_cevir_istendi -> kapat()` (kullanici 'ceviriyi baslat ve kabugu kapat' baglayabilir): `_mod_tiki` icinden
    `kapat()` -> `sekme.hide()` -> `hideEvent` -> `_kapat()` yeniden girer. Beklenti: hata yok, (F,F,F), cikis 1."""
    p = pencere
    sayac: list[int] = []
    p.cikis_istendi.connect(lambda: sayac.append(1))
    p.anlik_cevir_istendi.connect(p.kapat)
    p.kenara_al(); qtbot.wait(20)
    ac(qtbot, p.sekme, imlec)
    with qtbot.capture_exceptions() as yakalanan:
        p.sekme.dugme_anlik.click(); qtbot.wait(30)
    assert yakalanan == []
    assert uclu(p) == (False, False, False) and sayac == [1] and p.kapandi
    assert p.sekme.acik is False and p.sekme.yokluyor is False


def test_c2x2_pencere_mod_dugmesi_dinleyicisi_kenara_al_cagirir(qtbot, pencere: AnaPencere) -> None:
    """Pencere 'Anlik ceviri' tiki -> dinleyici `kenara_al()` (ceviri baslayinca pencere kenara cekilsin): gecis tutarli."""
    p = pencere
    p.anlik_cevir_istendi.connect(p.kenara_al)
    p.dugme_anlik.click(); qtbot.wait(30)
    assert (p.durum, uclu(p)) == (KabukDurumu.KENAR, (False, True, True))
    assert p.sekme.yokluyor


def test_c2x3_surukleme_sirasinda_sag_tik_pencereyi_goster_ve_surukleme_biter(qtbot, pencere: AnaPencere, imlec: Imlec) -> None:
    """Sol basili (surukleme) iken sag tik: `pencereyi_goster` -> `goster()` -> sekme gizlenir; `surukleniyor` False;
    yeniden `kenara_al()` sonrasi sekme kapali, surukleme yok, imlec disaridayken acilmaz."""
    p = pencere
    p.kenara_al(); qtbot.wait(20)
    s = p.sekme
    QTest.mousePress(s, Qt.MouseButton.LeftButton, pos=QPoint(R - 3, R))
    assert s.surukleniyor
    with qtbot.waitSignal(s.pencereyi_goster, timeout=300):
        QTest.mousePress(s, Qt.MouseButton.RightButton, pos=QPoint(R - 3, R))
    qtbot.wait(20)
    assert (p.durum, uclu(p)) == (KabukDurumu.GORUNUR, (True, False, False))
    assert s.surukleniyor is False
    p.kenara_al(); qtbot.wait(ACILMA + 3 * YOKLAMA)
    assert s.isVisible() and s.acik is False and s.surukleniyor is False


def test_c2x4_available_geometry_changed_panel_acikken(qtbot, pencere: AnaPencere, imlec: Imlec) -> None:
    """Gorev cubugu tasinirken panel acik: yeni dikdortgen icinde, boyut PANEL, `acik` degismez; kapaninca yeni kenar."""
    p = pencere
    p.kenara_al(); qtbot.wait(20)
    s = p.sekme
    ac(qtbot, s, imlec)
    yeni = QRect(0, 0, 1200, 700)
    s._ekran.availableGeometryChanged.emit(yeni)  # sahte sinyal (paket olcusu deseni)
    qtbot.wait(10)
    assert s.acik and yeni.contains(s.frameGeometry()) and s.frameGeometry().size() == PANEL_BOYUTU
    assert s.frameGeometry().right() == yeni.right()
    imlec.p = UZAK
    qtbot.waitUntil(lambda: not s.acik, timeout=KAPANMA + 2 * YOKLAMA + 300)
    assert s.frameGeometry().right() == yeni.right() and yeni.contains(s.frameGeometry())


def test_c2x5_kapat_sonrasi_dogrudan_show_dugmeler_olu(qtbot, pencere: AnaPencere) -> None:
    """Belge (dusuk): `kapat()` sonrasi `pencere.show()` (QWidget API) pencereyi getirir ama `dugme_kapat` artik sinyal
    uretmez (kapandi); `close()` gizler. Sonraki ajan kapat sonrasi kabugu yeniden KULLANAMAZ -- yeni `AnaPencere` kurar."""
    p = pencere
    sayac: list[int] = []
    p.cikis_istendi.connect(lambda: sayac.append(1))
    p.kapat(); qtbot.wait(10)
    p.show(); qtbot.wait(10)
    assert p.isVisible() and p.kapandi
    p.dugme_kapat.click(); p.dugme_tepsi.click(); p.dugme_kenar.click(); qtbot.wait(10)
    assert sayac == [1] and p.isVisible() and not p.sekme.isVisible() and not p.tepsi.gorunur()
    assert p.close() is True and not p.isVisible() and sayac == [1]


def test_c2x6_cikis_dinleyicisi_yeniden_kapat_ve_bildir(qtbot, pencere: AnaPencere) -> None:
    """`cikis_istendi` dinleyicisi `kapat()`/`bildir()` cagirirsa: tek sinyal, hata yok (demo `cikis_istendi` -> pencereleri kapatir)."""
    p = pencere
    sayac: list[int] = []

    def dinle() -> None:
        sayac.append(1)
        p.kapat()
        p.tepsi.bildir("kapaniyor", "x", 100)
        p.goster()

    p.cikis_istendi.connect(dinle)
    with qtbot.capture_exceptions() as yakalanan:
        p.dugme_kapat.click(); qtbot.wait(20)
    assert yakalanan == [] and sayac == [1] and uclu(p) == (False, False, False)


def test_c2x7_imlec_callable_qpoint_degil_tuple_donerse(qtbot) -> None:
    """`imlec_konumu` `(x, y)` tuple donerse (kolay hata): her yoklamada TypeError (pytest-qt yakalar), sekme calismaya
    devam eder ama HIC acilmaz -- sessiz degil (istisna basilir), belge."""
    p = AnaPencere(tepsi_kullanilabilir=False, imlec_konumu=lambda: (5, 5))  # type: ignore[arg-type,return-value]
    qtbot.addWidget(p)
    p.show(); p.kenara_al()
    with qtbot.capture_exceptions() as yakalanan:
        qtbot.wait(3 * YOKLAMA)
    assert len(yakalanan) >= 1 and all(e[0] is TypeError for e in yakalanan)
    assert p.sekme.isVisible() and p.sekme.acik is False
    p.kapat()


def test_c2x8_tepsi_menusu_kenara_al_gorunurken(qtbot, pencere: AnaPencere) -> None:
    """Tepsi menusu yalniz tepsi durumunda erisilir ama sinyal her durumda bagli: gorunurken `kenara_al_istendi` -> kenar."""
    p = pencere
    p.tepsi.kenara_al_istendi.emit(); qtbot.wait(20)
    assert (p.durum, uclu(p)) == (KabukDurumu.KENAR, (False, True, True))


def test_c2x9_kenar_sol_ana_pencere_ve_panel_sol_kenarda(qtbot, imlec: Imlec) -> None:
    """`AnaPencere(kenar=SOL)` -> kenara al: sekme sol kenarda; panel acilinca sol kenara bitisik; sol tarafta opak."""
    p = AnaPencere(kenar=Kenar.SOL, tepsi_kullanilabilir=False, imlec_konumu=imlec)
    qtbot.addWidget(p)
    p.show(); p.kenara_al(); qtbot.wait(20)
    s = p.sekme
    g = s.ekran_dikdortgeni
    assert s.frameGeometry().left() == g.left()
    ac(qtbot, s, imlec)
    assert s.frameGeometry().left() == g.left() and s.frameGeometry().size() == PANEL_BOYUTU
    assert s.dugme_anlik.isVisible() and s.dugme_bolge.isVisible()
    p.kapat()


def test_c2x10_app_quit_kenar_durumunda_kabugu_temiz_kapatir_TUR2_TERS() -> None:
    """TUR 1: `app.quit()` kenar durumunda gizli ana pencere closeEvent almiyordu (cikis 0, ikon kaliyordu). TUR 2 (O-B1 yan etkisi):
    closeAllWindows -> sekme.close() -> `kapandi` -> `goster()` (ana pencere gorunur) -> closeAllWindows onu da kapatir -> `kapat()`
    -> cikis 1, uclu (F,F,F), kapandi True. Taze surec."""
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


# =====================================================================================
# F · demo/kabuk.py -- gercek cagiran (sefin entegrasyonu); taze surec, offscreen
# =====================================================================================

DEMO_KURULUM = (
    "import os\n"
    "from PySide6 import QtCore, QtWidgets\n"
    "from PySide6.QtTest import QTest\n"
    "from src.ui.kabuk import AnaPencere\n"
    "from src.ui.uygulama import calistir\n"
    "from demo.kabuk import _bagla\n"
    "from demo.bolge_izle import SecimKatmani\n"
    "durum = {}\n"
    "def sarici(app, pencere):\n"
    "    durum['p'] = pencere\n"
    "    pencere.cikis_istendi.connect(lambda: durum.__setitem__('cikis', durum.get('cikis', 0) + 1))\n"
    "    QtCore.QTimer.singleShot(200, lambda: adimlar(app, pencere))\n"
    "    QtCore.QTimer.singleShot(8000, lambda: (print('ZAMAN_ASIMI'), app.exit(9)))\n"
    "    return _bagla(app, pencere)\n"
)


def test_f1_demo_bagla_bolge_izle_secim_katmani_esc_uygulamayi_KAPATMAZ_TUR2_TERS() -> None:
    """TUR 1 (Y-B1: Esc -> quit, surec bitiyordu) -> TUR 2 TERS (sef duzeltmesi): Esc -> `iptal` -> katman kapanir, surec YASAR
    (exec donmez, 1.5 s sonra bizim exit(9)), kabuk kapatilmamis (kapandi False), sekme GERI gelmis (O-B2), durum kenar."""
    kod = DEMO_KURULUM + (
        "def adimlar(app, pencere):\n"
        "    pencere.kenara_al()\n"
        "    QtCore.QTimer.singleShot(100, lambda: pencere.sekme.bolge_izle.emit())\n"
        "    def esc():\n"
        "        katmanlar = [w for w in QtWidgets.QApplication.topLevelWidgets() if isinstance(w, SecimKatmani) and w.isVisible()]\n"
        "        print('KATMAN', len(katmanlar), 'UCLU', pencere.isVisible(), pencere.sekme.isVisible())\n"
        "        if katmanlar: QTest.keyClick(katmanlar[0], QtCore.Qt.Key.Key_Escape)\n"
        "    QtCore.QTimer.singleShot(400, esc)\n"
        "    QtCore.QTimer.singleShot(1500, lambda: (print('YASIYOR'), app.exit(9)))\n"
        "rc = calistir([], calistirici=sarici)\n"
        "p = durum['p']\n"
        "print('RC', rc, 'KAPANDI', p.kapandi, 'CIKIS', durum.get('cikis', 0), 'SEKME_GORUNUR', p.sekme.isVisible(), 'DURUM', str(p.durum))\n"
    )
    r = taze_surec(kod)
    assert r.returncode == 0, (r.returncode, r.stderr[-1500:])
    assert "KATMAN 1 UCLU False False" in r.stdout, (r.stdout, r.stderr[-800:])  # secim boyunca sekme gizli (O-B2)
    assert "YASIYOR" in r.stdout and "ZAMAN_ASIMI" not in r.stdout, r.stdout
    assert "RC 9 KAPANDI False CIKIS 0 SEKME_GORUNUR True DURUM kenar" in r.stdout, (r.stdout, r.stderr[-800:])


def test_f2_demo_bagla_anlik_cevir_kenardan_pencereyi_getirir_ve_kapat_cikar() -> None:
    """Demo `anlik_cevir` dinleyicisi `pencere.goster()`: kenar -> gorunur (T,F,F); ardindan `dugme_kapat` -> exec doner 0."""
    kod = DEMO_KURULUM + (
        "def adimlar(app, pencere):\n"
        "    pencere.kenara_al()\n"
        "    QtCore.QTimer.singleShot(100, lambda: pencere.sekme.anlik_cevir.emit())\n"
        "    def kontrol():\n"
        "        print('UCLU', pencere.isVisible(), pencere.sekme.isVisible(), pencere.tepsi.gorunur(), 'DURUM', str(pencere.durum))\n"
        "        pencere.dugme_kapat.click()\n"
        "    QtCore.QTimer.singleShot(300, kontrol)\n"
        "rc = calistir([], calistirici=sarici)\n"
        "p = durum['p']\n"
        "print('RC', rc, 'KAPANDI', p.kapandi, 'CIKIS', durum.get('cikis', 0))\n"
    )
    r = taze_surec(kod)
    assert r.returncode == 0, (r.returncode, r.stderr[-1500:])
    assert "UCLU True False False DURUM gorunur" in r.stdout, (r.stdout, r.stderr[-800:])
    assert "RC 0 KAPANDI True CIKIS 1" in r.stdout, (r.stdout, r.stderr[-800:])


# =====================================================================================
# G · istek maddeleri taze surecte (offscreen): arka planda yasama, kapatma, giris noktasi
# =====================================================================================

def test_g1_tepsideyken_surec_yasar_kapat_bitirir_close_da_bitirir() -> None:
    """'arkaplanda calistirma': tepsiye al -> 1.2 s sonra exec hala donmemis (timer tik atiyor); `dugme_kapat` -> exec 0.
    Ikinci surec: arka plandayken `close()` (WM_CLOSE esdegeri) -> exec doner (zombi yok, KRT Y1). Offscreen'de tepsi
    yok: `calistir()` `tepsi_kullanilabilir` gecirmez -> arka plan = kenar (K5); gercek tepsi `sonda_2`de."""
    kod = (
        "from PySide6.QtCore import QTimer\n"
        "from src.ui.uygulama import calistir\n"
        "tik = []\n"
        "def sarici(app, p):\n"
        "    t = QTimer(); t.setInterval(50); t.timeout.connect(lambda: tik.append(1)); t.start()\n"
        "    QTimer.singleShot(100, p.dugme_tepsi.click)\n"
        "    QTimer.singleShot(1300, lambda: print('TEPSIDE', p.durum, 'TIK', len(tik) > 15, 'GORUNUR', p.isVisible()))\n"
        "    QTimer.singleShot(1400, %s)\n"
        "    QTimer.singleShot(6000, lambda: (print('ZAMAN_ASIMI'), app.exit(9)))\n"
        "    return app.exec()\n"
        "print('RC', calistir([], calistirici=sarici))\n"
    )
    r = taze_surec(kod % "p.dugme_kapat.click")
    # offscreen: sistem tepsisi yok -> `calistir` `tepsi_kullanilabilir` enjekte ETMEZ -> K5 dususu: durum `kenar` (gercek tepsi: sonda_2)
    assert r.returncode == 0 and "TEPSIDE kenar TIK True GORUNUR False" in r.stdout and "RC 0" in r.stdout and "ZAMAN_ASIMI" not in r.stdout, (r.stdout, r.stderr[-800:])
    r = taze_surec(kod % "p.close")
    assert r.returncode == 0 and "RC 0" in r.stdout and "ZAMAN_ASIMI" not in r.stdout, (r.stdout, r.stderr[-800:])


def test_g2_python_m_src_ui_giris_noktasi_acilir_ve_kapanir() -> None:
    """`python -m src.ui`: pencere acilir; disaridan mudahale icin QTimer enjekte edilemez -> `-c` ile `__main__` esdegeri
    `calistir()` cagrilip 300 ms sonra `QApplication.instance().activeWindow()`/topLevelWidgets uzerinden kapat tiklanir."""
    kod = (
        "from PySide6.QtCore import QTimer\n"
        "from PySide6.QtWidgets import QApplication\n"
        "from src.ui.kabuk import AnaPencere\n"
        "import src.ui.uygulama as u\n"
        "def kapat_sonra():\n"
        "    ps = [w for w in QApplication.topLevelWidgets() if isinstance(w, AnaPencere)]\n"
        "    print('PENCERE', len(ps), 'GORUNUR', ps[0].isVisible() if ps else None)\n"
        "    ps[0].dugme_kapat.click()\n"
        "app = QApplication([])\n"
        "QTimer.singleShot(300, kapat_sonra)\n"
        "QTimer.singleShot(6000, lambda: (print('ZAMAN_ASIMI'), app.exit(9)))\n"
        "print('RC', u.calistir())\n"
    )
    r = taze_surec(kod)
    assert r.returncode == 0 and "PENCERE 1 GORUNUR True" in r.stdout and "RC 0" in r.stdout, (r.stdout, r.stderr[-800:])
    # `python -m src.ui` `exec()` icinde bloklar (disaridan timer enjekte edilemez); icerigi kaynaktan dogrulanir
    kaynak = (KOK / "src" / "ui" / "__main__.py").read_text(encoding="utf-8")
    assert "raise SystemExit(calistir())" in kaynak
