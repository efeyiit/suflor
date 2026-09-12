"""T-012 Tester-B (kor) -- mercek: kotu kullanim + istek/sartname (paket v2) uyumu + test kalitesi.

Offscreen (pytest-qt). Gercek ekran sondalari ayri betiklerde (`sonda_*.py`).
Bolumler:
  A  istek.md satir satir (kullanicinin sozleri)  -> `test_a_*`
  B  K1 durum makinesi (v2 ▲) + tablo disi ucluler   -> `test_b_*`
  C  kotu kullanim (sonraki ajan = pipeline baglayici) -> `test_c_*`
  D  K2..K8 v2 ▲ maddeleri satir satir               -> `test_d_*`
  X  xfail(strict): olculmus bulgu -- kod bugun boyle davraniyor, beklenti paket/istek
Beklentiler paketten/istekten literal; uygulamanin ozel mekanizmasi (`_yokla`, `_ac`) KANCALANMAZ (§4.6/7).
"""
from __future__ import annotations

import ast
import statistics
import subprocess
import sys
import time
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import QPoint, QRect, QSize, Qt, QTimer
from PySide6.QtTest import QTest

from src.ui.geometri import PANEL_BOYUTU, Kenar, sekme_acik_dikdortgeni, sekme_icinde, sekme_kapali_dikdortgeni, y_sinirla
from src.ui.kabuk import AnaPencere, KabukDurumu, Tepsi
from src.ui.kenar_sekmesi import KenarSekmesi

KOK = Path(__file__).resolve().parents[4]
UI = KOK / "src" / "ui"
R, ACILMA, KAPANMA, YOKLAMA = 26, 120, 450, 60
UZAK = QPoint(5, 5)


class Imlec:
    """Enjekte imlec: konum yazilir, cagri sayilir (paket K4: `imlec_konumu` callable)."""

    def __init__(self, p: QPoint = UZAK) -> None:
        self.p = QPoint(p)
        self.sayac = 0

    def __call__(self) -> QPoint:
        self.sayac += 1
        return QPoint(self.p)


def uclu(p: AnaPencere) -> tuple[bool, bool, bool]:
    return (p.isVisible(), p.sekme.isVisible(), p.tepsi.gorunur())


def merkez(s: KenarSekmesi) -> QPoint:
    """Kapali sekmenin yarim daire merkezine yakin, disk ICINDE bir nokta."""
    g = s.frameGeometry()
    return QPoint(g.right() - 3, g.top() + s.yaricap) if s.kenar is Kenar.SAG else QPoint(g.left() + 3, g.top() + s.yaricap)


def ac(qtbot, s: KenarSekmesi, imlec: Imlec) -> None:
    """Tur 2 (paket v3 K4 mandal): mod tiki sonrasi imlec diskten BIR KEZ cikmadan panel acilmaz -> once disari, sonra diske."""
    imlec.p = UZAK
    qtbot.wait(2 * YOKLAMA)
    imlec.p = merkez(s)
    qtbot.waitUntil(lambda: s.acik, timeout=ACILMA + 2 * YOKLAMA + 300)


@pytest.fixture
def imlec() -> Imlec:
    return Imlec()


@pytest.fixture
def pencere(qtbot, imlec: Imlec) -> Iterator[AnaPencere]:
    """Tepsi ZORLA var (offscreen'de isSystemTrayAvailable False); teardown `kapat()` (paket K1 olcu notu)."""
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


# =====================================================================================
# A · ISTEK satir satir -- "3 pencere dugmesi olsun sag uste: ..."
# =====================================================================================

def test_a1_sag_ustte_uc_dugme_sirali_ve_mod_dugmelerinin_ustunde(pencere: AnaPencere) -> None:
    """'3 pencere dugmesi olsun sag uste': uc ust dugme pencere ust seridinde (y < 44), sagda (x > w/2),
    soldan saga kenar-tepsi-kapat; kapat en sagda; hepsi iki mod dugmesinin USTUNDE ve gorunur."""
    p = pencere
    ustler = [p.dugme_kenar, p.dugme_tepsi, p.dugme_kapat]
    for d in ustler:
        assert d.isVisible() and d.geometry().bottom() < 44, (d.accessibleName(), d.geometry())
        assert d.geometry().left() > p.width() // 2, (d.accessibleName(), d.geometry())
    xs = [d.geometry().left() for d in ustler]
    assert xs == sorted(xs), xs
    assert p.dugme_kapat.geometry().right() == max(d.geometry().right() for d in ustler)
    assert p.dugme_kapat.geometry().right() >= p.width() - 12, (p.dugme_kapat.geometry(), p.width())
    for mod in (p.dugme_anlik, p.dugme_bolge):
        assert mod.geometry().top() > max(d.geometry().bottom() for d in ustler)
    assert [d.accessibleName() for d in ustler] == ["Kenara al", "Tepsiye al", "Kapat"]


def test_a2_kapat_dugmesi_uygulamayi_tamamen_kapatir_kalinti_yok(qtbot, pencere: AnaPencere) -> None:
    """'biri uygulama kapatma': tik -> cikis_istendi 1, uclu (F,F,F), tepsi QSystemTrayIcon gizli,
    sekme yoklayicisi durmus, gorunur ust-duzey 0."""
    p = pencere
    p.kenara_al(); qtbot.wait(20)
    assert p.sekme.yokluyor
    with qtbot.waitSignal(p.cikis_istendi, timeout=1000):
        p.dugme_kapat.click()
    assert uclu(p) == (False, False, False)
    assert p.tepsi.ikon.isVisible() is False
    assert p.sekme.yokluyor is False
    assert p.kapandi is True
    assert [w for w in QtWidgets.QApplication.topLevelWidgets() if w.isVisible()] == []


def test_a3_tepsiye_al_uygulama_arka_planda_calisir(qtbot, pencere: AnaPencere) -> None:
    """'biri arkaplanda calistirma': tik -> pencere gizli, tepsi ikonu gorunur; surec/olay dongusu yasiyor
    (bagimsiz bir QTimer tik atmaya devam eder) ve mod sinyali tepsideyken de calisir."""
    p = pencere
    tik: list[int] = []
    t = QTimer(); t.setInterval(10); t.timeout.connect(lambda: tik.append(1)); t.start()
    p.dugme_tepsi.click()
    assert uclu(p) == (False, False, True) and p.durum is KabukDurumu.TEPSI
    n0 = len(tik)
    qtbot.wait(120)
    assert len(tik) > n0 + 3, "olay dongusu tepsideyken de donmeli"
    t.stop()
    # tepsideyken de sinyal yolu acik (kisayol servisi baglanacak): dinleyici alir
    with qtbot.waitSignal(p.anlik_cevir_istendi, timeout=500):
        p.dugme_anlik.click()


def test_a4_kenara_al_masaustunde_pencere_yok_kenarda_kucuk_yarim_daire(qtbot, pencere: AnaPencere) -> None:
    """'masaustunde gozukmeyecek ama ekranin bir kenarinda kucuk bir yarim daire': ana pencere gizli;
    yalniz sekme gorunur; boyut 26x52 (istek notu 24-28 px yaricap); sag kenara bitisik; dikey orta;
    cizim: kenar tarafi opak, ic koseler saydam (yarim daire)."""
    p = pencere
    g = p.sekme.ekran_dikdortgeni
    p.dugme_kenar.click(); qtbot.wait(30)
    assert uclu(p) == (False, True, True) and p.durum is KabukDurumu.KENAR
    gorunur = [w for w in QtWidgets.QApplication.topLevelWidgets() if w.isVisible()]
    assert gorunur == [p.sekme], gorunur
    fg = p.sekme.frameGeometry()
    assert (fg.width(), fg.height()) == (R, 2 * R)
    assert 24 <= p.sekme.yaricap <= 28
    assert fg.right() == g.right()
    assert abs(fg.center().y() - g.center().y()) <= 1
    img = p.sekme.grab().toImage()
    assert img.pixelColor(0, 0).alpha() == 0, "ic ust kose saydam olmali"
    assert img.pixelColor(0, 2 * R - 1).alpha() == 0, "ic alt kose saydam olmali"
    assert img.pixelColor(R - 2, R).alpha() > 200, "kenar tarafi opak olmali"
    assert img.pixelColor(R // 2, R).alpha() > 200, "merkez yakini opak olmali"


def test_a5_imlec_gelince_iki_ceviri_secenegi_cikar(qtbot, pencere: AnaPencere, imlec: Imlec) -> None:
    """'imlecle oraya gidince cevirme secenegi cikacak, iki tane': panel acilinca gorunen QPushButton'lar:
    TAM iki buyuk mod dugmesi (Anlik ceviri / Bolge izle) + paket v2 K8'in ekledigi kucuk `dugme_goster`
    (22x20, istek disi ama paket karari). Ikisi de sinyal yayar; imlec ayrilinca kapanir."""
    p = pencere
    p.kenara_al(); qtbot.wait(30)
    s = p.sekme
    ac(qtbot, s, imlec)
    dugmeler = [d for d in s.findChildren(QtWidgets.QPushButton) if d.isVisible()]
    assert len(dugmeler) == 3, [d.text() for d in dugmeler]
    buyuk = [d for d in dugmeler if d.width() >= 100]
    kucuk = [d for d in dugmeler if d.width() < 100]
    assert len(buyuk) == 2 and len(kucuk) == 1, [(d.text(), d.width(), d.height()) for d in dugmeler]
    assert kucuk[0] is s.dugme_goster and kucuk[0].width() <= 24 and kucuk[0].height() <= 22, kucuk[0].size()
    assert {d.accessibleName() for d in buyuk} == {"Anlık çeviri", "Bölge izle"}
    assert s.frameGeometry().size() == PANEL_BOYUTU
    with qtbot.waitSignal(p.anlik_cevir_istendi, timeout=500):
        s.dugme_anlik.click()
    ac(qtbot, s, imlec)
    with qtbot.waitSignal(p.bolge_izle_istendi, timeout=500):
        s.dugme_bolge.click()
    imlec.p = UZAK
    qtbot.waitUntil(lambda: not s.acik, timeout=KAPANMA + 2 * YOKLAMA + 300)


def test_a6_kenar_durumunda_ana_pencere_gorev_cubugu_adayi_degil(qtbot, pencere: AnaPencere) -> None:
    """Kenar/tepsi durumunda ana pencere gizli (`isVisible` False) -> gorev cubugu/Alt-Tab adayi degil;
    sekme `Tool` (Alt-Tab disi, gercek ekranda WS_EX_TOOLWINDOW sonda_1 ile)."""
    p = pencere
    p.kenara_al(); qtbot.wait(20)
    assert not p.isVisible() and bool(p.sekme.windowFlags() & Qt.WindowType.Tool)
    p.goster(); qtbot.wait(20)
    p.tepsiye_al(); qtbot.wait(20)
    assert not p.isVisible() and not p.sekme.isVisible()


# =====================================================================================
# B · K1 durum makinesi (v2 ▲) -- tablo, gecisler, kapat idempotent, tablo DISI ucluler
# =====================================================================================

TABLO = {
    KabukDurumu.GORUNUR: (True, False, False),
    KabukDurumu.TEPSI: (False, False, True),
    KabukDurumu.KENAR: (False, True, True),
}


@pytest.mark.parametrize("yol", ["dugme", "yontem", "tepsi_menu", "sekme_sag_tik", "panel_dugme_goster", "tepsi_trigger", "tepsi_doubleclick"])
def test_b1_gorunura_her_yoldan_ayni_uclu(qtbot, pencere: AnaPencere, imlec: Imlec, yol: str) -> None:
    """K1 ▲ 'gorunur'a hangi yoldan gelinirse gelinsin (T,F,F) -- tepsi ikonu DA gizli."""
    p = pencere
    if yol in ("tepsi_menu", "tepsi_trigger", "tepsi_doubleclick"):
        p.tepsiye_al(); assert uclu(p) == TABLO[KabukDurumu.TEPSI]
    else:
        p.kenara_al(); qtbot.wait(20); assert uclu(p) == TABLO[KabukDurumu.KENAR]
    if yol == "dugme":
        p.goster()
    elif yol == "yontem":
        p.goster()
    elif yol == "tepsi_menu":
        [a for a in p.tepsi.menu.actions() if a.text() == "Pencereyi göster"][0].trigger()
    elif yol == "sekme_sag_tik":
        QTest.mouseClick(p.sekme, Qt.MouseButton.RightButton, pos=QPoint(R - 3, R))
    elif yol == "panel_dugme_goster":
        ac(qtbot, p.sekme, imlec); p.sekme.dugme_goster.click()
    elif yol == "tepsi_trigger":
        p.tepsi.ikon.activated.emit(QtWidgets.QSystemTrayIcon.ActivationReason.Trigger)
    elif yol == "tepsi_doubleclick":
        p.tepsi.ikon.activated.emit(QtWidgets.QSystemTrayIcon.ActivationReason.DoubleClick)
    qtbot.wait(20)
    assert uclu(p) == TABLO[KabukDurumu.GORUNUR] and p.durum is KabukDurumu.GORUNUR
    assert p.sekme.acik is False and p.sekme.yokluyor is False


def test_b2_gecis_tablosu_tam(qtbot, pencere: AnaPencere) -> None:
    """gorunur<->tepsi, gorunur<->kenar, tepsi->kenar (menu); kenar->tepsi YOK (kenar korunur); x2 idempotent."""
    p = pencere
    p.tepsiye_al(); assert (p.durum, uclu(p)) == (KabukDurumu.TEPSI, TABLO[KabukDurumu.TEPSI])
    p.tepsiye_al(); assert (p.durum, uclu(p)) == (KabukDurumu.TEPSI, TABLO[KabukDurumu.TEPSI])
    [a for a in p.tepsi.menu.actions() if a.text() == "Kenara al"][0].trigger(); qtbot.wait(20)
    assert (p.durum, uclu(p)) == (KabukDurumu.KENAR, TABLO[KabukDurumu.KENAR])
    p.kenara_al(); qtbot.wait(20)
    assert (p.durum, uclu(p)) == (KabukDurumu.KENAR, TABLO[KabukDurumu.KENAR])
    p.tepsiye_al(); qtbot.wait(20)
    assert (p.durum, uclu(p)) == (KabukDurumu.KENAR, TABLO[KabukDurumu.KENAR]), "kenar -> tepsi yolu yok"
    p.goster(); qtbot.wait(20)
    assert (p.durum, uclu(p)) == (KabukDurumu.GORUNUR, TABLO[KabukDurumu.GORUNUR])
    p.kenara_al(); qtbot.wait(20); p.goster(); qtbot.wait(20)
    assert (p.durum, uclu(p)) == (KabukDurumu.GORUNUR, TABLO[KabukDurumu.GORUNUR])


@pytest.mark.parametrize("baslangic", ["gorunur", "tepsi", "kenar", "kenar_panel_acik"])
def test_b3_kapat_her_durumdan_fff_ve_tek_sinyal(qtbot, pencere: AnaPencere, imlec: Imlec, baslangic: str) -> None:
    p = pencere
    if baslangic == "tepsi":
        p.tepsiye_al()
    elif baslangic.startswith("kenar"):
        p.kenara_al(); qtbot.wait(20)
        if baslangic == "kenar_panel_acik":
            ac(qtbot, p.sekme, imlec)
    sayac: list[int] = []
    p.cikis_istendi.connect(lambda: sayac.append(1))
    p.kapat(); qtbot.wait(20)
    assert uclu(p) == (False, False, False) and sayac == [1]
    assert p.sekme.yokluyor is False and p.sekme.acik is False
    p.kapat(); p.close(); qtbot.wait(20)
    assert sayac == [1]
    # dirilme yok
    p.goster(); p.tepsiye_al(); p.kenara_al(); qtbot.wait(20)
    assert uclu(p) == (False, False, False) and sayac == [1]


@pytest.mark.parametrize("baslangic", ["gorunur", "tepsi", "kenar"])
def test_b4_close_event_her_durumda_kapat_ile_esdeger(qtbot, pencere: AnaPencere, baslangic: str) -> None:
    """K1 ▲ closeEvent (Alt+F4/WM_CLOSE) `kapat()` ile esdeger; gizli pencereye `close()` de ayni."""
    p = pencere
    {"gorunur": lambda: None, "tepsi": p.tepsiye_al, "kenar": p.kenara_al}[baslangic]()
    qtbot.wait(20)
    sayac: list[int] = []
    p.cikis_istendi.connect(lambda: sayac.append(1))
    assert p.close() is True
    qtbot.wait(20)
    assert uclu(p) == (False, False, False) and sayac == [1] and p.kapandi
    p.kapat(); assert sayac == [1]


def test_b5_tepsi_menusu_cikis_kapat(qtbot, pencere: AnaPencere) -> None:
    p = pencere
    p.tepsiye_al()
    with qtbot.waitSignal(p.cikis_istendi, timeout=500):
        [a for a in p.tepsi.menu.actions() if a.text() == "Çıkış"][0].trigger()
    assert uclu(p) == (False, False, False)


def test_b6_tepsi_yokken_tepsiye_al_kenara_duser_uclu_ftf(qtbot, pencere_tepsisiz: AnaPencere) -> None:
    """K5 ▲ `kenar (tepsi yok)` = (F,T,F); `gorunur()` daima False (offscreen show() True doner -- olcu ateslenebilir)."""
    p = pencere_tepsisiz
    p.tepsiye_al(); qtbot.wait(20)
    assert (p.durum, uclu(p)) == (KabukDurumu.KENAR, (False, True, False))
    p.tepsi.goster()
    assert p.tepsi.gorunur() is False
    p.goster(); qtbot.wait(20)
    assert uclu(p) == (True, False, False)


def test_b7_kapat_sonrasi_durum_son_durumu_gosterir_kapandi_ayirt_eder(qtbot, pencere: AnaPencere) -> None:
    """Belgeli 'bir adim otesi': kapat() sonrasi `durum` KENAR kalir ama uclu (F,F,F) -- K1 tablosunun DISI;
    ayirt edici bayrak `kapandi`. Sonraki ajan `durum`a bakarak 'sekme gorunur' varsayamaz."""
    p = pencere
    p.kenara_al(); qtbot.wait(20); p.kapat()
    assert p.durum is KabukDurumu.KENAR and uclu(p) == (False, False, False) and p.kapandi


def test_x1_sekmeye_close_durum_ile_uclu_ayrismaz_TUR2_TERS(qtbot, pencere: AnaPencere) -> None:
    """TUR 1 xfail (O-B1) -> TUR 2 TERS: `KenarSekmesi.closeEvent` -> `kapandi` -> `AnaPencere.goster()`: `durum` GORUNUR,
    uclu (T,F,F) = tablo satiri; durum ile uclu ayrismaz."""
    p = pencere
    p.kenara_al(); qtbot.wait(20)
    p.sekme.close(); qtbot.wait(20)
    assert p.durum is KabukDurumu.GORUNUR and uclu(p) == TABLO[p.durum] == (True, False, False), (p.durum, uclu(p))


def test_x2_tepsisizken_sekmeye_close_zombi_degil_TUR2_TERS(qtbot, pencere_tepsisiz: AnaPencere) -> None:
    """TUR 1 xfail (O-B1 tepsisiz zombi) -> TUR 2 TERS: (T,F,F), kapandi False, cikis 0 -- geri donus var."""
    p = pencere_tepsisiz
    sayac: list[int] = []
    p.cikis_istendi.connect(lambda: sayac.append(1))
    p.kenara_al(); qtbot.wait(20)
    p.sekme.close(); qtbot.wait(20)
    assert uclu(p) == (True, False, False) and p.durum is KabukDurumu.GORUNUR and not p.kapandi and sayac == [], (p.durum, uclu(p), p.kapandi, sayac)


# =====================================================================================
# C · KOTU KULLANIM -- sonraki ajan (`demo/kabuk.py` / pipeline baglayici) neye davet ediliyor
# =====================================================================================

def test_c1_sinyal_dinleyicisi_istisna_atarsa_kabuk_yasar(qtbot, pencere: AnaPencere) -> None:
    """Slot istisnasi: kabuk/olay dongusu ayakta kalir; sonraki `kapat()` calisir (pytest-qt istisnayi yakalar)."""
    p = pencere

    def patlak() -> None:
        raise RuntimeError("dinleyici patladi")

    p.anlik_cevir_istendi.connect(patlak)
    with qtbot.capture_exceptions() as yakalanan:
        p.dugme_anlik.click()
        qtbot.wait(20)
    assert len(yakalanan) == 1 and yakalanan[0][0] is RuntimeError
    assert p.isVisible()
    with qtbot.waitSignal(p.cikis_istendi, timeout=500):
        p.dugme_kapat.click()


def test_c1b_taze_surecte_slot_istisnasi_sureci_dusurmez() -> None:
    """Ayni soru gercek `app.exec()` icinde (pytest-qt yakalayicisi yok): PySide6 6.11 slot istisnasini basar,
    surec DUSMEZ (cikis kodu 0), sonraki tik islenir. Belge: kabuk bunu engelleyemez; baglayan taraf sarmali."""
    kod = (
        "import sys; sys.path.insert(0, %r)\n"
        "from PySide6.QtCore import QTimer\n"
        "from PySide6.QtWidgets import QApplication\n"
        "from src.ui.kabuk import AnaPencere\n"
        "app = QApplication([]); app.setQuitOnLastWindowClosed(False)\n"
        "p = AnaPencere(tepsi_kullanilabilir=False); p.show()\n"
        "n = []\n"
        "def patlak():\n    n.append(1); raise RuntimeError('dinleyici patladi')\n"
        "p.anlik_cevir_istendi.connect(patlak)\n"
        "QTimer.singleShot(50, p.dugme_anlik.click)\n"
        "QTimer.singleShot(150, p.dugme_anlik.click)\n"
        "QTimer.singleShot(400, lambda: (print('TIK', len(n), 'GORUNUR', p.isVisible()), app.quit()))\n"
        "raise SystemExit(app.exec())\n"
    ) % str(KOK)
    r = subprocess.run([sys.executable, "-c", kod], capture_output=True, text=True, timeout=60,
                       env={**__import__("os").environ, "QT_QPA_PLATFORM": "offscreen", "PYTHONIOENCODING": "utf-8"})
    assert r.returncode == 0, (r.returncode, r.stderr[-800:])
    assert "TIK 2 GORUNUR True" in r.stdout, (r.stdout, r.stderr[-800:])
    assert "dinleyici patladi" in r.stderr


def test_c2_uzun_dinleyici_ui_ipligini_bloklar_yoklayici_durur(qtbot, pencere: AnaPencere, imlec: Imlec) -> None:
    """Mod sinyali UI ipliginde yayilir: 300 ms suren dinleyici boyunca yoklayici/sayaclar TIK ATMAZ
    (tasarim 5.5 'UI thread bloklamaz' sorumlulugu baglayan tarafta). Sinyal oncesi panel kapali (K4 ▲)
    oldugu icin blok suresince ekranda panel metni kalmaz -- olculuyor."""
    p = pencere
    p.kenara_al(); qtbot.wait(20)
    s = p.sekme
    ac(qtbot, s, imlec)
    n0 = imlec.sayac
    durumlar: list[bool] = []

    def uzun() -> None:
        durumlar.append(s.acik)
        son = time.perf_counter() + 0.3
        while time.perf_counter() < son:
            pass
        durumlar.append(s.acik)

    s.anlik_cevir.connect(uzun)
    s.dugme_anlik.click()
    assert durumlar == [False, False]
    assert imlec.sayac == n0, "blok suresince yoklama olmadi (UI ipligi)"


def test_c3_calistir_iki_kez_ve_mevcut_qapplication(qtbot, qapp) -> None:
    """`calistir()` mevcut QApplication'i yeniden kullanir ve `setQuitOnLastWindowClosed(False)` yapar (ev sahibi
    uygulamaya YAN ETKI); iki kez cagri iki pencere + iki tepsi kurar (kabuk tekil degil) -- belge."""
    from src.ui.uygulama import calistir

    onceki = qapp.quitOnLastWindowClosed()
    qapp.setQuitOnLastWindowClosed(True)
    pencereler: list[AnaPencere] = []

    def kur(app: QtWidgets.QApplication, p: AnaPencere) -> int:
        pencereler.append(p); return 7

    try:
        assert calistir([], calistirici=kur) == 7
        assert calistir([], kenar=Kenar.SOL, calistirici=kur) == 7
        assert qapp.quitOnLastWindowClosed() is False
        assert len(pencereler) == 2 and all(p.isVisible() for p in pencereler)
        assert pencereler[1].sekme.kenar is Kenar.SOL
        gorunur = [w for w in QtWidgets.QApplication.topLevelWidgets() if w.isVisible() and isinstance(w, AnaPencere)]
        assert len(gorunur) == 2
    finally:
        for p in pencereler:
            p.kapat()
        qapp.setQuitOnLastWindowClosed(onceki)


@pytest.mark.parametrize("kenar", [Kenar.SOL, "sol", "sag", Kenar.SAG])
def test_c4_kenar_parametresi_enum_ve_dize(qtbot, imlec: Imlec, kenar: object) -> None:
    p = AnaPencere(kenar=kenar, tepsi_kullanilabilir=False, imlec_konumu=imlec)  # type: ignore[arg-type]
    qtbot.addWidget(p)
    p.show(); p.kenara_al(); qtbot.wait(20)
    g = p.sekme.ekran_dikdortgeni
    fg = p.sekme.frameGeometry()
    if Kenar(kenar) is Kenar.SOL:  # type: ignore[arg-type]
        assert fg.left() == g.left()
    else:
        assert fg.right() == g.right()
    p.kapat()


@pytest.mark.parametrize("kotu", ["left", "", "SAG", 1, None])
def test_c4b_gecersiz_kenar_yapimda_valueerror(kotu: object) -> None:
    with pytest.raises(ValueError):
        AnaPencere(kenar=kotu, tepsi_kullanilabilir=False)  # type: ignore[arg-type]


def test_c5_y_ozelligi_gecersiz_deger_ve_golgeleme(qtbot, sekme: KenarSekmesi) -> None:
    """`sekme.y` sinirlanir; `'abc'` ValueError, None TypeError, 3.7 -> 3; `sekme.y()` cagrisi TypeError
    (QWidget.y golgelenmis -- belgeli tuzak, `pos()` kullanilir)."""
    s = sekme
    g = s.ekran_dikdortgeni
    alt = g.bottom() - 2 * R + 1
    s.y = 10**9; assert s.y == alt and s.frameGeometry().top() == alt
    s.y = -10**9; assert s.y == g.top()
    s.y = 3.7; assert s.y == 3  # type: ignore[assignment]
    with pytest.raises(ValueError):
        s.y = "abc"  # type: ignore[assignment]
    with pytest.raises(TypeError):
        s.y = None  # type: ignore[assignment]
    with pytest.raises(TypeError):
        s.y()  # type: ignore[operator]
    assert s.pos().y() == 3


def test_c6_bildir_sik_cagri_offscreen_hata_vermez(qtbot, pencere: AnaPencere) -> None:
    for i in range(20):
        pencere.tepsi.bildir("b", f"m{i}", 1)
    pencere.tepsi.bildir("", "", 0)
    pencere.tepsi.bildir("x", "y", -5)


def test_c7_mod_tiki_sonrasi_imlec_disk_icinde_kalsa_da_panel_yeniden_ACILMAZ_TUR2_TERS(qtbot, pencere: AnaPencere, imlec: Imlec) -> None:
    """TUR 1 (D-B6: yeniden aciliyordu) -> TUR 2 TERS (paket v3 K4 mandal): tik noktasi kapali diskin icindeyse ve imlec
    orada kalirsa panel `acilma_ms + 3*yoklama` sonra HALA kapali; diskten cikip girince acilir; merkez tiki zaten disk disi."""
    p = pencere
    p.kenara_al(); qtbot.wait(20)
    s = p.sekme
    ac(qtbot, s, imlec)
    d = s.dugme_anlik
    tik_noktasi = d.mapToGlobal(QPoint(d.width() - 4, d.height() // 2))
    kapali = sekme_kapali_dikdortgeni(s.ekran_dikdortgeni, s.y, R, Kenar.SAG)
    assert sekme_icinde(kapali, tik_noktasi, R, Kenar.SAG), "dugmenin kenar ucu kapali diskin icinde"
    imlec.p = tik_noktasi
    aninda: list[bool] = []
    s.anlik_cevir.connect(lambda: aninda.append(s.acik))
    QTest.mouseClick(d, Qt.MouseButton.LeftButton, pos=QPoint(d.width() - 4, d.height() // 2))
    assert aninda == [False]
    qtbot.wait(ACILMA + 3 * YOKLAMA)
    assert s.acik is False, "mandal: imlec diskte kalsa da yeniden acilmamali (tur 1'de aciliyordu)"
    ac(qtbot, s, imlec)  # diskten cik -> gir: acilir (pozitif kontrol)
    # merkez tiki (kullanicinin dogal tiki) diskin DISINDA: mandal hemen kalkar, imlec disarida -> kapali kalir
    imlec.p = d.mapToGlobal(d.rect().center())
    assert not sekme_icinde(kapali, imlec.p, R, Kenar.SAG)
    s.dugme_anlik.click()
    qtbot.wait(ACILMA + 3 * YOKLAMA)
    assert s.acik is False


def test_c8_qwidget_show_hide_dogrudan_cagrisi_tabloyu_atlar(qtbot, pencere: AnaPencere) -> None:
    """Kabuk `show()/hide()`yi ozel API'nin arkasina saklamiyor: tepsideyken `pencere.show()` -> (T,F,T) durum TEPSI;
    gorunurken `pencere.hide()` -> (F,F,F) durum GORUNUR, kapandi False (kullanici yolu yok). Belge (D-B?)."""
    p = pencere
    p.tepsiye_al(); p.show(); qtbot.wait(20)
    assert uclu(p) == (True, False, True) and p.durum is KabukDurumu.TEPSI
    p.goster(); p.hide(); qtbot.wait(20)
    assert uclu(p) == (False, False, False) and p.durum is KabukDurumu.GORUNUR and not p.kapandi
    p.goster(); qtbot.wait(20)
    assert uclu(p) == (True, False, False)


def test_c9_imlec_callable_istisna_atarsa_yoklayici_yasar(qtbot, pencere: AnaPencere) -> None:
    p = pencere
    n = [0]

    def imlec_patlak() -> QPoint:
        n[0] += 1
        if n[0] % 2:
            raise RuntimeError("imlec yok")
        return QPoint(5, 5)

    p2 = AnaPencere(tepsi_kullanilabilir=False, imlec_konumu=imlec_patlak)
    qtbot.addWidget(p2)
    p2.show(); p2.kenara_al()
    with qtbot.capture_exceptions() as yakalanan:
        qtbot.wait(4 * YOKLAMA)
    assert len(yakalanan) >= 1 and p2.sekme.yokluyor and p2.sekme.isVisible()
    p2.kapat()


@pytest.mark.parametrize("args", [dict(yaricap=0), dict(yaricap=-1), dict(acilma_ms=-1), dict(kapanma_ms=-1), dict(yoklama_ms=0)])
def test_c10_gecersiz_parametre_valueerror(args: dict[str, int]) -> None:
    with pytest.raises(ValueError):
        KenarSekmesi(QtGui.QGuiApplication.primaryScreen(), **args)


def test_c11_acilma_ms_sifir_ve_yoklama_bir_ms_calisir(qtbot, imlec: Imlec) -> None:
    """Sinir: acilma_ms=0/kapanma_ms=0 -> bir yoklamada acilir/kapanir; yoklama_ms=1 asiri ama gecerli."""
    s = KenarSekmesi(QtGui.QGuiApplication.primaryScreen(), acilma_ms=0, kapanma_ms=0, yoklama_ms=1, imlec_konumu=imlec)
    qtbot.addWidget(s); s.show(); qtbot.waitExposed(s)
    imlec.p = merkez(s)
    qtbot.waitUntil(lambda: s.acik, timeout=300)
    imlec.p = UZAK
    qtbot.waitUntil(lambda: not s.acik, timeout=300)
    s.hide()


def test_c12_kenar_setter_gecersiz_durumu_bozmaz(qtbot, sekme: KenarSekmesi) -> None:
    s = sekme
    with pytest.raises(ValueError):
        s.kenar = "ust"  # type: ignore[assignment]
    assert s.kenar is Kenar.SAG and s.frameGeometry().right() == s.ekran_dikdortgeni.right()
    s.kenar = "sol"  # type: ignore[assignment]
    assert s.kenar is Kenar.SOL and s.frameGeometry().left() == s.ekran_dikdortgeni.left()


def test_c13_kenar_degisince_acik_panel_de_yeniden_konumlanir(qtbot, sekme: KenarSekmesi, imlec: Imlec) -> None:
    s = sekme
    ac(qtbot, s, imlec)
    s.kenar = Kenar.SOL
    g = s.ekran_dikdortgeni
    assert s.acik and s.frameGeometry().left() == g.left() and s.frameGeometry().size() == PANEL_BOYUTU
    imlec.p = UZAK
    qtbot.waitUntil(lambda: not s.acik, timeout=KAPANMA + 2 * YOKLAMA + 300)
    assert s.frameGeometry() == sekme_kapali_dikdortgeni(g, s.y, R, Kenar.SOL)


def test_c14_ekran_dikdortgeni_kopya_disaridan_mutasyon_etkisiz(sekme: KenarSekmesi) -> None:
    g = sekme.ekran_dikdortgeni
    g.setRight(10)
    assert sekme.ekran_dikdortgeni.right() != 10


def test_c15_tepsi_bagimsiz_kullanim_ve_menu_sirasi(qtbot) -> None:
    """`Tepsi(ikon, None, kullanilabilir=True)` ebeveynsiz; menu: Pencereyi goster, Kenara al, ---, Cikis; sinyaller."""
    t = Tepsi(QtGui.QIcon(), None, kullanilabilir=True)
    acts = t.menu.actions()
    assert [a.text() for a in acts] == ["Pencereyi göster", "Kenara al", "", "Çıkış"]
    assert acts[2].isSeparator()
    for ad, sinyal in (("Pencereyi göster", t.goster_istendi), ("Kenara al", t.kenara_al_istendi), ("Çıkış", t.cikis_istendi)):
        with qtbot.waitSignal(sinyal, timeout=300):
            [a for a in acts if a.text() == ad][0].trigger()
    for sebep in (QtWidgets.QSystemTrayIcon.ActivationReason.Context, QtWidgets.QSystemTrayIcon.ActivationReason.MiddleClick,
                  QtWidgets.QSystemTrayIcon.ActivationReason.Unknown):
        with qtbot.assertNotEmitted(t.goster_istendi, wait=50):
            t.ikon.activated.emit(sebep)
    t.goster(); assert t.gorunur() is True
    t.gizle(); assert t.gorunur() is False


def test_c16_mod_sinyali_kenar_durumunu_degistirmez_demo_goster_cagirir(qtbot, pencere: AnaPencere, imlec: Imlec) -> None:
    """K7: mod sinyali durumu degistirmez; `demo/kabuk.py` `anlik_cevir` dinleyicisi `pencere.goster()` cagiriyor ->
    o durumda kenar -> gorunur gecisi dinleyici tarafinda olur; kabuk buna izin verir (durum tutarli)."""
    p = pencere
    p.kenara_al(); qtbot.wait(20)
    ac(qtbot, p.sekme, imlec)
    p.sekme.dugme_anlik.click()
    assert p.durum is KabukDurumu.KENAR and uclu(p) == (False, True, True)
    p.anlik_cevir_istendi.connect(p.goster)
    ac(qtbot, p.sekme, imlec)
    p.sekme.dugme_anlik.click(); qtbot.wait(20)
    assert p.durum is KabukDurumu.GORUNUR and uclu(p) == (True, False, False)


def test_c17_ikinci_ekran_sahte_ve_negatif_koordinat_saf_geometri() -> None:
    """Negatif koordinatli monitor + sol kenar (paket K2 'negatif koordinatli monitor destek')."""
    e = QRect(-2560, 0, 2560, 1440)
    k = sekme_kapali_dikdortgeni(e, 700, R, Kenar.SOL)
    assert k == QRect(-2560, 700, R, 2 * R)
    a = sekme_acik_dikdortgeni(e, 700, R, PANEL_BOYUTU, Kenar.SOL)
    assert a.left() == -2560 and e.contains(a) and a.contains(k)
    assert sekme_icinde(k, QPoint(-2560, 726), R, Kenar.SOL)
    assert not sekme_icinde(k, QPoint(-2560 + R - 1, 700), R, Kenar.SOL)
    assert not sekme_icinde(k, QPoint(-2561, 726), R, Kenar.SOL), "ekran otesi (komsu monitor) icinde degil"


# =====================================================================================
# D · K2..K8 v2 ▲ maddeleri satir satir
# =====================================================================================

def test_d1_k2_available_geometry_changed_yeni_x_ve_y_sikistirma(qtbot, sekme: KenarSekmesi) -> None:
    s = sekme
    s.y = 10**6
    eski_alt = s.y
    yeni = QRect(0, 0, 1000, 500)
    s._ekran.availableGeometryChanged.emit(yeni)  # sahte sinyal (paket olcusu)
    qtbot.wait(10)
    assert s.ekran_dikdortgeni == yeni
    assert s.frameGeometry().right() == yeni.right()
    assert s.y == yeni.bottom() - 2 * R + 1 < eski_alt


def test_d2_k2_sol_kenar_cizim_aynali(qtbot, imlec: Imlec) -> None:
    s = KenarSekmesi(QtGui.QGuiApplication.primaryScreen(), kenar=Kenar.SOL, imlec_konumu=imlec)
    qtbot.addWidget(s); s.show(); qtbot.waitExposed(s)
    img = s.grab().toImage()
    assert img.pixelColor(1, R).alpha() > 200 and img.pixelColor(R - 1, 0).alpha() == 0 and img.pixelColor(R - 1, 2 * R - 1).alpha() == 0
    s.kenar = Kenar.SAG; qtbot.wait(20)
    img = s.grab().toImage()
    assert img.pixelColor(R - 2, R).alpha() > 200 and img.pixelColor(0, 0).alpha() == 0
    s.hide()


def test_d3_k3_bayraklar_yapisal_ve_panel_dugmeleri_nofocus(sekme: KenarSekmesi) -> None:
    b = sekme.windowFlags()
    for bayrak in (Qt.WindowType.FramelessWindowHint, Qt.WindowType.Tool, Qt.WindowType.WindowStaysOnTopHint, Qt.WindowType.WindowDoesNotAcceptFocus):
        assert b & bayrak, bayrak
    assert sekme.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    assert sekme.testAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
    assert sekme.focusPolicy() == Qt.FocusPolicy.NoFocus
    for d in (sekme.dugme_anlik, sekme.dugme_bolge, sekme.dugme_goster):
        assert d.focusPolicy() == Qt.FocusPolicy.NoFocus


def test_d4_k4_surukleme_sirasinda_acilmaz_birakinca_sifirdan(qtbot, sekme: KenarSekmesi, imlec: Imlec) -> None:
    s = sekme
    imlec.p = merkez(s)
    QTest.mousePress(s, Qt.MouseButton.LeftButton, pos=QPoint(R - 3, R))
    assert s.surukleniyor
    qtbot.wait(ACILMA + 3 * YOKLAMA)
    assert s.acik is False
    y0 = s.y
    QTest.mouseMove(s, pos=QPoint(R - 3, R + 100))
    assert s.y == y0 + 100 and s.acik is False
    imlec.p = merkez(s)
    QTest.mouseRelease(s, Qt.MouseButton.LeftButton, pos=QPoint(R - 3, R))
    assert not s.surukleniyor
    qtbot.wait(ACILMA // 2)
    assert s.acik is False, "birakinca sayac SIFIRDAN"
    qtbot.waitUntil(lambda: s.acik, timeout=ACILMA + 2 * YOKLAMA + 300)


def test_d4b_k4_acikken_sol_tik_surukleme_baslatmaz(qtbot, sekme: KenarSekmesi, imlec: Imlec) -> None:
    s = sekme
    ac(qtbot, s, imlec)
    QTest.mousePress(s, Qt.MouseButton.LeftButton, pos=QPoint(5, 5))
    assert not s.surukleniyor and s.acik
    QTest.mouseRelease(s, Qt.MouseButton.LeftButton, pos=QPoint(5, 5))


def test_d4c_k4_surukleme_sinira_kilitlenir(qtbot, sekme: KenarSekmesi, imlec: Imlec) -> None:
    s = sekme
    g = s.ekran_dikdortgeni
    QTest.mousePress(s, Qt.MouseButton.LeftButton, pos=QPoint(R - 3, R))
    QTest.mouseMove(s, pos=QPoint(R - 3, R + 10**5))
    assert s.y == g.bottom() - 2 * R + 1
    QTest.mouseMove(s, pos=QPoint(R - 3, R - 10**5))
    assert s.y == g.top()
    QTest.mouseRelease(s, Qt.MouseButton.LeftButton, pos=QPoint(R - 3, R))


def test_d4d_k4_yoklayici_yalniz_gorunurken_ve_imlec_yalniz_callable(qtbot, sekme: KenarSekmesi, imlec: Imlec) -> None:
    s = sekme
    n0 = imlec.sayac
    qtbot.wait(3 * YOKLAMA)
    assert imlec.sayac > n0
    s.hide(); n1 = imlec.sayac
    qtbot.wait(3 * YOKLAMA)
    assert imlec.sayac == n1 and not s.yokluyor
    # QCursor.setPos ile yazilan konum kullanilmaz (callable UZAK diyor)
    s.show(); qtbot.waitExposed(s)
    QtGui.QCursor.setPos(merkez(s))
    qtbot.wait(ACILMA + 3 * YOKLAMA)
    assert s.acik is False


def test_d5_k4_mod_tiki_once_panel_kapanir_sonra_sinyal_uc_dugme(qtbot, sekme: KenarSekmesi, imlec: Imlec) -> None:
    s = sekme
    for d, sinyal in ((s.dugme_anlik, s.anlik_cevir), (s.dugme_bolge, s.bolge_izle), (s.dugme_goster, s.pencereyi_goster)):
        ac(qtbot, s, imlec)
        kayit: list[tuple[bool, QSize]] = []
        sinyal.connect(lambda: kayit.append((s.acik, s.frameGeometry().size())))
        imlec.p = UZAK
        with qtbot.waitSignal(sinyal, timeout=500):
            d.click()
        assert kayit == [(False, QSize(R, 2 * R))], (d.accessibleName(), kayit)


def test_d6_k4_iceri_disari_iceri_titremesi_acik_kalir_ve_alt_sinir(qtbot, sekme: KenarSekmesi, imlec: Imlec) -> None:
    s = sekme
    imlec.p = merkez(s)
    qtbot.wait(ACILMA // 2)
    assert s.acik is False, "deterministik alt sinir"
    qtbot.waitUntil(lambda: s.acik, timeout=ACILMA + 2 * YOKLAMA + 300)
    imlec.p = UZAK; qtbot.wait(100); imlec.p = QPoint(s.frameGeometry().center())
    qtbot.wait(KAPANMA + 2 * YOKLAMA)
    assert s.acik, "iceri-disari-iceri (100 ms) -> acik kalir"
    imlec.p = UZAK
    qtbot.wait(KAPANMA // 2)
    assert s.acik, "kapanma alt siniri"
    qtbot.waitUntil(lambda: not s.acik, timeout=KAPANMA + 2 * YOKLAMA + 300)


def test_d7_k5_menu_ve_tepsi_dallari(qtbot, pencere: AnaPencere) -> None:
    acts = pencere.tepsi.menu.actions()
    assert [a.text() for a in acts if not a.isSeparator()] == ["Pencereyi göster", "Kenara al", "Çıkış"]
    assert pencere.tepsi.kullanilabilir is True
    assert Tepsi(QtGui.QIcon(), None).kullanilabilir is False, "offscreen: isSystemTrayAvailable False"


YASAK_ADLAR = {"QMessageBox", "QDialog", "QInputDialog", "QFileDialog", "print", "logging", "warnings", "sleep", "processEvents", "quit", "exit"}
YASAK_MODULLER = ("src.capture", "src.ocr", "src.translate", "logging", "warnings", "time")


def _taramalar(kaynak: str) -> tuple[set[str], set[str]]:
    agac = ast.parse(kaynak)
    adlar: set[str] = set()
    moduller: set[str] = set()
    for n in ast.walk(agac):
        if isinstance(n, ast.Name):
            adlar.add(n.id)
        elif isinstance(n, ast.Attribute):
            adlar.add(n.attr)
        elif isinstance(n, ast.Import):
            moduller.update(a.name for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            moduller.add(n.module)
    return adlar, moduller


@pytest.mark.parametrize("dosya", sorted(p.name for p in UI.glob("*.py")))
def test_d8_k6_k7_ast_yasak_ad_ve_import_yok(dosya: str) -> None:
    adlar, moduller = _taramalar((UI / dosya).read_text(encoding="utf-8"))
    ihlal_ad = adlar & YASAK_ADLAR
    if dosya == "uygulama.py":
        ihlal_ad -= {"quit", "exit"}  # `cikis_istendi -> app.quit` burada baglanir (paket)
    assert not ihlal_ad, (dosya, ihlal_ad)
    assert not [m for m in moduller if m == "time" or any(m == y or m.startswith(y + ".") for y in YASAK_MODULLER)], (dosya, moduller)


def test_d8b_ast_pozitif_kontrol() -> None:
    adlar, moduller = _taramalar("import time\nfrom src.capture import x\nfrom PySide6.QtWidgets import QMessageBox\nQMessageBox.warning(None,'a','b'); app.quit(); time.sleep(1)\n")
    assert adlar & YASAK_ADLAR == {"QMessageBox", "quit", "sleep"} and {"time", "src.capture"} <= moduller


def test_d8c_k7_taze_surecte_src_ui_pipeline_modulu_yuklemez() -> None:
    kod = "import sys; sys.path.insert(0, %r); import src.ui.uygulama, src.ui.kabuk; print(sorted(m for m in sys.modules if m.startswith('src.')))" % str(KOK)
    r = subprocess.run([sys.executable, "-c", kod], capture_output=True, text=True, timeout=60,
                       env={**__import__("os").environ, "QT_QPA_PLATFORM": "offscreen"})
    assert r.returncode == 0, r.stderr
    assert "src.capture" not in r.stdout and "src.ocr" not in r.stdout and "src.translate" not in r.stdout, r.stdout


def test_d9_k8_surukleme_ve_erisilebilirlik(qtbot, pencere: AnaPencere) -> None:
    p = pencere
    p0 = p.pos()
    QTest.mousePress(p, Qt.MouseButton.LeftButton, pos=QPoint(100, 20))
    QTest.mouseMove(p, pos=QPoint(140, 50))
    QTest.mouseRelease(p, Qt.MouseButton.LeftButton, pos=QPoint(140, 50))
    assert p.pos() == p0 + QPoint(40, 30)
    p1 = p.pos()
    QTest.mousePress(p, Qt.MouseButton.LeftButton, pos=QPoint(100, 200))  # govde
    QTest.mouseMove(p, pos=QPoint(150, 250))
    QTest.mouseRelease(p, Qt.MouseButton.LeftButton, pos=QPoint(150, 250))
    assert p.pos() == p1
    d = p.dugme_kapat
    QTest.mousePress(d, Qt.MouseButton.LeftButton, pos=QPoint(3, 3))
    QTest.mouseMove(d, pos=QPoint(40, 40))
    assert p.pos() == p1
    QTest.mouseRelease(d, Qt.MouseButton.LeftButton, pos=QPoint(40, 40))
    for b in (p.dugme_kapat, p.dugme_tepsi, p.dugme_kenar, p.dugme_anlik, p.dugme_bolge):
        assert b.toolTip() and b.accessibleName()
    assert "Sağ tık: pencereyi göster" in p.sekme.toolTip()
    for b in (p.sekme.dugme_anlik, p.sekme.dugme_bolge, p.sekme.dugme_goster):
        assert b.toolTip() and b.accessibleName()


def test_d10_k6_paint_100_kare_medyani(qtbot, sekme: KenarSekmesi, imlec: Imlec) -> None:
    s = sekme
    t_k = []
    for _ in range(100):
        t0 = time.perf_counter(); s.repaint(); t_k.append((time.perf_counter() - t0) * 1000)
    ac(qtbot, s, imlec)
    t_a = []
    for _ in range(100):
        t0 = time.perf_counter(); s.repaint(); t_a.append((time.perf_counter() - t0) * 1000)
    assert statistics.median(t_k) < 16 and statistics.median(t_a) < 16, (statistics.median(t_k), statistics.median(t_a))


@pytest.mark.parametrize("ekran", [QRect(0, 0, 2560, 1392), QRect(-2560, 0, 2560, 1440), QRect(-2560, 0, 2048, 1152), QRect(0, 0, 640, 100)])
@pytest.mark.parametrize("kenar", [Kenar.SAG, Kenar.SOL])
def test_d11_k2_geometri_izgara_ve_kisa_ekran(ekran: QRect, kenar: Kenar) -> None:
    ys = [-10**6, ekran.top(), ekran.center().y(), ekran.bottom(), 10**6]
    onceki = None
    for y in ys:
        k = sekme_kapali_dikdortgeni(ekran, y, R, kenar)
        a = sekme_acik_dikdortgeni(ekran, y, R, PANEL_BOYUTU, kenar)
        assert k.size() == QSize(R, 2 * R) and a.size() == PANEL_BOYUTU
        assert (k.right() == ekran.right()) if kenar is Kenar.SAG else (k.left() == ekran.left())
        assert (a.right() == ekran.right()) if kenar is Kenar.SAG else (a.left() == ekran.left())
        assert ekran.contains(k) and a.contains(k), (ekran, kenar, y)  # sekme her ekranda sigar (h >= 2r), panel sekmeyi kapsar
        if ekran.height() >= PANEL_BOYUTU.height():
            assert ekran.contains(a), (ekran, kenar, y)
        else:
            # 100 px ekran: panel (132) sigmaz; paket 'ekran icine sikistirilmis' lafzi TUTMAZ, uste yaslanir alt tasar (docstring belgeli)
            assert a.top() == ekran.top() and a.bottom() > ekran.bottom()
        ys_ = y_sinirla(ekran, y, R)
        assert onceki is None or ys_ >= onceki
        onceki = ys_


# =====================================================================================
# E · Kapi (real_check v2) yapisal denetim -- kural 8/10 (okuma; gercek kosum sarici ile ayri)
# =====================================================================================

def test_e1_kapi_sabitleri_uygulamadan_turetilmiyor_ve_9_kapi_3_dalinda() -> None:
    kaynak = (KOK / ".agents" / "tasks" / "T-012" / "real_check.py").read_text(encoding="utf-8")
    assert "sabit != (26, 120, 450, 60, 200, 132)" in kaynak
    assert "ust = 120 + 2 * 60 + 150" in kaynak and "ust_k = 450 + 2 * 60 + 150" in kaynak
    # [9] yalniz [3] on kosulu ve panel acilmasi saglaninca olculur; ikisi de ihlal uretir -> sessiz atlanmaz
    assert kaynak.count("[9]") == 1 and 'ihlal("[3b] panel acilmadi' in kaynak
    # [5c] sag tik: uclu olculur, ON PLAN olculmez (KRT olctu, kapi olcmuyor) -> sonda_1 olcer
    sag_tik_satiri = [l for l in kaynak.splitlines() if "[5c] sag tik" in l][0]
    assert "on_plan" not in sag_tik_satiri
