"""T-012 Tester-A mercek testleri: durum makinesi + sinir + takma ad/omur.

Kor testler: delivery.md / evidence / sef_dogrulama / implementer testleri OKUNMADAN yazildi.
Garanti alani = src/ui/*.py docstring'leri + packet.md v2 (K1-K8).
Tur 2 (paket v3): 6 test `_v3` olarak ters cevrildi (Y-A1 gizli sizinti, O-A1 mandal, D-A1 showNormal, D-A3/D-A4 ust sinir);
3 Y-A1 DOCSTRING testi degismeden yesile dondu. Yeni ▲▲ testleri `test_mercek_a_tur2.py`de.

Bolumler:
  A  K1 durum makinesi -- 5 baslangic satiri x 22 eylem tablosu (uclu + durum + cikis sayisi + yoklayici)
  B  K1 diziler: idempotenlik, kapat sonrasi dirilme, dis show()/hide()/showMinimized() (taban sinif delikleri)
  C  K1 rastgele yuruyus (fuzz): ulasilamaz uclu yok, kapandi => (F,F,F), yoklayici == sekme gorunur
  D  Omur / takma ad: deleteLater, iki AnaPencere, tek basina KenarSekmesi, imlec_konumu istisnasi, ekran=None,
     ekran_dikdortgeni kopya, PANEL_BOYUTU mutasyonu, kenar/y atomik atama
  E  Sinir -- geometri (saf): yaricap 1/0/negatif/ekrandan buyuk, bos/negatif QRect, panel > ekran, y tipleri,
     availableGeometryChanged sonrasi sinir, kenar degisimi acikken
  F  Sinir -- zaman: acilma_ms=0, kapanma_ms=0, kapanma < yoklama, 2**31, hide/show yoklayici, surukleme + hide,
     surukleme + sag tik, surukleme sinira kilitlenir, yoklama_ms=1 CPU
  G  Sinyaller: cikis_istendi her yoldan tam bir kez, dinleyicisiz mod sinyalleri, K4 sirasi, yeniden giris
  H  K6/K7 AST (pozitif kontrollu) + taze surec import olcusu
"""
from __future__ import annotations

import ast
import gc
import os
import random
import subprocess
import sys
import time
import weakref
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
import shiboken6
from PySide6.QtCore import QCoreApplication, QEvent, QPoint, QRect, QSize, Qt, QTimer
from PySide6.QtGui import QCloseEvent, QGuiApplication, QIcon, QScreen
from PySide6.QtWidgets import QApplication, QPushButton, QSystemTrayIcon, QWidget

from src.ui.geometri import PANEL_BOYUTU, Kenar, sekme_acik_dikdortgeni, sekme_icinde, sekme_kapali_dikdortgeni, y_sinirla
from src.ui.kabuk import AnaPencere, KabukDurumu, Tepsi
from src.ui.kenar_sekmesi import KenarSekmesi

KOK = Path(__file__).resolve().parents[4]
SRC_UI = KOK / "src" / "ui"
DISARI = QPoint(-10_000, -10_000)
HIZLI = dict(acilma_ms=20, kapanma_ms=30, yoklama_ms=10)  # durum testleri icin kisa sayaclar (urun degerleri ayrica olculur)

Uclu = tuple[bool, bool, bool]


def uclu(p: AnaPencere) -> Uclu:
    return (p.isVisible(), p.sekme.isVisible(), p.tepsi.gorunur())


def gorunur_ust_duzey() -> list[QWidget]:
    return [w for w in QApplication.topLevelWidgets() if w.isVisible()]


# ---------------------------------------------------------------- fixture'lar --------------------------------------
@pytest.fixture
def ekran(qapp: QApplication) -> QScreen:
    e = QGuiApplication.primaryScreen()
    assert e is not None
    return e


@pytest.fixture
def imlec() -> list[QPoint]:
    """Enjekte imlec: `imlec[0]` yazilarak konum degistirilir; `imlec[1]` cagri sayacidir (QPoint x alani)."""
    return [QPoint(DISARI), QPoint(0, 0)]


@pytest.fixture
def pencere_fab(qtbot, ekran: QScreen, imlec: list[QPoint]) -> Iterator[Callable[..., AnaPencere]]:
    """AnaPencere fabrikasi; teardown'da her pencereye `kapat()` (KRT O6: gorunur ust-duzey kirliligi)."""
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


# =============================================================== A. K1 DURUM TABLOSU ===============================
# Baslangic satirlari: G (gorunur, tepsi var) · T (tepsi) · K (kenar, tepsi var) · K0 (kenar, tepsi yok) · G0 (gorunur, tepsi yok)
BASLANGIC = ("G", "T", "K", "K0", "G0")
UCLU_TABLO: dict[str, Uclu] = {"G": (True, False, False), "T": (False, False, True), "K": (False, True, True), "K0": (False, True, False), "G0": (True, False, False)}
DURUM_TABLO = {"G": KabukDurumu.GORUNUR, "T": KabukDurumu.TEPSI, "K": KabukDurumu.KENAR, "K0": KabukDurumu.KENAR, "G0": KabukDurumu.GORUNUR}


def kur(fab: Callable[..., AnaPencere], satir: str) -> AnaPencere:
    p = fab(tepsi_kullanilabilir=satir in ("G", "T", "K"))
    p.show()
    if satir == "T":
        p.tepsiye_al()
    elif satir in ("K", "K0"):
        p.kenara_al()
    assert uclu(p) == UCLU_TABLO[satir] and p.durum is DURUM_TABLO[satir], f"kurulum {satir}: {uclu(p)} {p.durum}"
    return p


def _menu_eylem(p: AnaPencere, metin: str) -> None:
    eylem = [a for a in p.tepsi.menu.actions() if a.text() == metin]
    assert len(eylem) == 1, f"menu eylemi bulunamadi: {metin!r}"
    eylem[0].trigger()


def _sekme_sag_tik(qtbot, p: AnaPencere) -> None:
    s = p.sekme
    if s.isVisible():
        qtbot.mouseClick(s, Qt.MouseButton.RightButton, pos=QPoint(s.width() - 3, s.height() // 2))
    else:
        s.pencereyi_goster.emit()  # gizli sekme: programatik yol


# eylem adi -> (uygulayici, sinif)   sinif: goster | tepsi | kenar | kapat | yok
EYLEMLER: dict[str, tuple[Callable[[object, AnaPencere], None], str]] = {
    "goster": (lambda qb, p: p.goster(), "goster"),
    "tepsiye_al": (lambda qb, p: p.tepsiye_al(), "tepsi"),
    "kenara_al": (lambda qb, p: p.kenara_al(), "kenar"),
    "kapat": (lambda qb, p: p.kapat(), "kapat"),
    "close": (lambda qb, p: p.close(), "kapat"),
    "closeEvent": (lambda qb, p: QApplication.sendEvent(p, QCloseEvent()), "kapat"),
    "dugme_kapat": (lambda qb, p: p.dugme_kapat.click(), "kapat"),
    "dugme_tepsi": (lambda qb, p: p.dugme_tepsi.click(), "tepsi"),
    "dugme_kenar": (lambda qb, p: p.dugme_kenar.click(), "kenar"),
    "tepsi_trigger": (lambda qb, p: p.tepsi.ikon.activated.emit(QSystemTrayIcon.ActivationReason.Trigger), "goster"),
    "tepsi_doubleclick": (lambda qb, p: p.tepsi.ikon.activated.emit(QSystemTrayIcon.ActivationReason.DoubleClick), "goster"),
    "tepsi_context": (lambda qb, p: p.tepsi.ikon.activated.emit(QSystemTrayIcon.ActivationReason.Context), "yok"),
    "tepsi_middle": (lambda qb, p: p.tepsi.ikon.activated.emit(QSystemTrayIcon.ActivationReason.MiddleClick), "yok"),
    "tepsi_unknown": (lambda qb, p: p.tepsi.ikon.activated.emit(QSystemTrayIcon.ActivationReason.Unknown), "yok"),
    "menu_goster": (lambda qb, p: _menu_eylem(p, "Pencereyi göster"), "goster"),
    "menu_kenar": (lambda qb, p: _menu_eylem(p, "Kenara al"), "kenar"),
    "menu_cikis": (lambda qb, p: _menu_eylem(p, "Çıkış"), "kapat"),
    "sekme_sag_tik": (_sekme_sag_tik, "goster"),
    "sekme_dugme_goster": (lambda qb, p: p.sekme.dugme_goster.click(), "goster"),
    "sekme_dugme_anlik": (lambda qb, p: p.sekme.dugme_anlik.click(), "yok"),
    "sekme_dugme_bolge": (lambda qb, p: p.sekme.dugme_bolge.click(), "yok"),
    "dugme_anlik": (lambda qb, p: p.dugme_anlik.click(), "yok"),
    "dugme_bolge": (lambda qb, p: p.dugme_bolge.click(), "yok"),
}


def beklenen(satir: str, sinif: str) -> tuple[KabukDurumu, Uclu, int]:
    tepsi_var = satir in ("G", "T", "K")
    if sinif == "goster":
        return KabukDurumu.GORUNUR, (True, False, False), 0
    if sinif == "kenar" or (sinif == "tepsi" and (not tepsi_var or satir == "K")):
        return KabukDurumu.KENAR, (False, True, tepsi_var), 0
    if sinif == "tepsi":
        return KabukDurumu.TEPSI, (False, False, True), 0
    if sinif == "kapat":
        return DURUM_TABLO[satir], (False, False, False), 1  # docstring: `durum` son durumu gosterir
    return DURUM_TABLO[satir], UCLU_TABLO[satir], 0


@pytest.mark.parametrize("eylem", list(EYLEMLER))
@pytest.mark.parametrize("satir", BASLANGIC)
def test_a_k1_gecis_tablosu(qtbot, pencere_fab, satir: str, eylem: str) -> None:
    """Her (baslangic satiri x eylem) icin: durum, uclu, cikis_istendi sayisi, kapandi, yoklayici == sekme gorunur, panel kapali."""
    p = kur(pencere_fab, satir)
    cikis: list[int] = []
    p.cikis_istendi.connect(lambda: cikis.append(1))
    mod: list[str] = []
    p.anlik_cevir_istendi.connect(lambda: mod.append("anlik"))
    p.bolge_izle_istendi.connect(lambda: mod.append("bolge"))
    uygula, sinif = EYLEMLER[eylem]
    uygula(qtbot, p)
    qtbot.wait(30)
    b_durum, b_uclu, b_cikis = beklenen(satir, sinif)
    assert (p.durum, uclu(p), len(cikis)) == (b_durum, b_uclu, b_cikis), f"{satir}+{eylem}: {p.durum} {uclu(p)} cikis={len(cikis)}"
    assert p.kapandi is (sinif == "kapat")
    assert p.sekme.yokluyor is p.sekme.isVisible(), "yoklayici yalniz sekme gorunurken calisir"
    assert p.sekme.acik is False and p.sekme.frameGeometry().size() == QSize(26, 52)
    if eylem in ("sekme_dugme_anlik", "dugme_anlik"):
        assert mod == ["anlik"]
    elif eylem in ("sekme_dugme_bolge", "dugme_bolge"):
        assert mod == ["bolge"]
    else:
        assert mod == []
    # ikinci kapat hicbir sey yapmaz; kapanmis pencere kapat-disi eylemlerde de (F,F,F) kalir
    if sinif == "kapat":
        p.kapat()
        p.close()
        assert len(cikis) == 1 and uclu(p) == (False, False, False)


def test_a_k1_kurulum_satirlari_pozitif_kontrol(pencere_fab) -> None:
    """Tablo satirlari birbirinden ayrisir (ayni uclu iki farkli durumda yalnizca gorunur/gorunur-tepsi-yok)."""
    goruldu = {satir: (kur(pencere_fab, satir).durum, UCLU_TABLO[satir]) for satir in BASLANGIC}
    assert len({v for v in goruldu.values()}) == 4  # G ve G0 ayni (T,F,F)/gorunur; digerleri farkli
    assert goruldu["K"] != goruldu["K0"]


# =============================================================== B. K1 DIZILER ======================================
@pytest.mark.parametrize("satir", BASLANGIC)
def test_b_k1_kapat_sonrasi_dirilme_yok_ve_tek_sinyal(qtbot, pencere_fab, satir: str) -> None:
    p = kur(pencere_fab, satir)
    n: list[int] = []
    p.cikis_istendi.connect(lambda: n.append(1))
    p.kapat()
    for eylem in ("goster", "tepsiye_al", "kenara_al", "kapat", "close", "dugme_kapat", "menu_cikis", "tepsi_trigger", "sekme_dugme_goster", "sekme_sag_tik", "closeEvent"):
        EYLEMLER[eylem][0](qtbot, p)
        qtbot.wait(5)
        assert uclu(p) == (False, False, False), f"{satir}: kapat sonrasi {eylem} diriltti: {uclu(p)}"
        assert len(n) == 1, f"{satir}: {eylem} ikinci sinyal uretti"
        assert p.sekme.yokluyor is False
    assert p.durum is DURUM_TABLO[satir]  # docstring: son durum korunur


@pytest.mark.parametrize("satir", BASLANGIC)
def test_b_k1_gorunur_ust_duzey_kapat_sonrasi_sifir(qtbot, pencere_fab, satir: str) -> None:
    once = set(id(w) for w in gorunur_ust_duzey())
    p = kur(pencere_fab, satir)
    yeni = [w for w in gorunur_ust_duzey() if id(w) not in once]
    assert len(yeni) == (1 if satir in ("G", "G0") else 1 if satir in ("K", "K0") else 0)  # pozitif kontrol: kurulum gorunur birakir
    p.kapat()
    qtbot.wait(10)
    assert [w for w in gorunur_ust_duzey() if id(w) not in once] == []


def test_b_k1_idempotent_x2_ve_ucgen(qtbot, pencere_fab) -> None:
    p = kur(pencere_fab, "G")
    n: list[int] = []
    p.cikis_istendi.connect(lambda: n.append(1))
    p.goster(); p.goster()
    assert (p.durum, uclu(p)) == (KabukDurumu.GORUNUR, (True, False, False))
    p.tepsiye_al(); p.tepsiye_al()
    assert (p.durum, uclu(p)) == (KabukDurumu.TEPSI, (False, False, True))
    p.kenara_al(); p.kenara_al()
    assert (p.durum, uclu(p)) == (KabukDurumu.KENAR, (False, True, True))
    assert p.sekme.yokluyor is True
    p.tepsiye_al()  # kenar -> tepsi yolu YOK
    assert (p.durum, uclu(p)) == (KabukDurumu.KENAR, (False, True, True))
    p.goster()
    assert (p.durum, uclu(p)) == (KabukDurumu.GORUNUR, (True, False, False))
    p.kenara_al(); p.goster(); p.tepsiye_al(); p.goster()
    assert (p.durum, uclu(p), n) == (KabukDurumu.GORUNUR, (True, False, False), [])


def test_b_k1_dis_hide_gorunur_durumunda_uc_gizli_kapandi_degil_PIN(qtbot, pencere_fab) -> None:
    """[PIN/bilgi] Taban sinif `hide()` disaridan cagrilirsa (F,F,F) + kapandi False + durum gorunur: docstring'in
    'ulasilamaz' dedigi uclu programatik olarak ulasilir (kullanici yolu yok; `calistir` yalniz `show()` kullanir).
    Pozitif kontrol: `goster()` geri getirir."""
    p = kur(pencere_fab, "G")
    p.hide()
    qtbot.wait(10)
    assert uclu(p) == (False, False, False) and p.kapandi is False and p.durum is KabukDurumu.GORUNUR
    p.goster()
    assert uclu(p) == (True, False, False)


def test_b_k1_dis_show_tepsi_durumunda_tablo_disi_uclu_PIN(qtbot, pencere_fab) -> None:
    """[PIN/bilgi] tepsi durumunda disaridan `show()` -> (T,F,T), durum tepsi: tabloda olmayan uclu (programatik).
    `goster()` toparlar (T,F,F)."""
    p = kur(pencere_fab, "T")
    p.show()
    qtbot.wait(10)
    assert uclu(p) == (True, False, True) and p.durum is KabukDurumu.TEPSI
    p.goster()
    assert uclu(p) == (True, False, False) and p.durum is KabukDurumu.GORUNUR


def test_b_k1_kapat_sonrasi_dis_show_pencereyi_gosterir_ama_kapandi_kalir_PIN(qtbot, pencere_fab) -> None:
    """[PIN/bilgi] `kapat()` sonrasi taban sinif `show()` pencereyi gorunur yapar (T,F,F) -- docstring yalniz
    goster/tepsiye_al/kenara_al icin 'diriltmez' der. Ikinci `close()` yine sinyal uretmez (1 kalir)."""
    p = kur(pencere_fab, "G")
    n: list[int] = []
    p.cikis_istendi.connect(lambda: n.append(1))
    p.kapat()
    p.show()
    qtbot.wait(10)
    assert uclu(p) == (True, False, False) and p.kapandi is True and len(n) == 1
    p.close()
    assert uclu(p) == (False, False, False) and len(n) == 1


def test_b_k1_show_minimized_sonra_tepsi_sonra_goster_normale_doner_v3(qtbot, pencere_fab) -> None:
    """[v3 -- tur 1 PIN ters cevrildi, D-A1 duzeltildi] Pencere kucultulmusken (Win+D sinifi) `tepsiye_al()` -> `goster()`
    ve `kenara_al()` -> `goster()`: `showNormal()` ile geri gelir, isMinimized False. Tur 1'de True kaliyordu."""
    for ara in ("tepsiye_al", "kenara_al"):
        p = kur(pencere_fab, "G")
        assert p.isMinimized() is False
        p.showMinimized()
        qtbot.wait(20)
        assert p.isMinimized() is True and p.isVisible() is True  # pozitif kontrol: kucultme offscreen'de olculuyor
        getattr(p, ara)()
        p.goster()
        qtbot.wait(20)
        assert uclu(p) == (True, False, False) and p.durum is KabukDurumu.GORUNUR
        assert p.isMinimized() is False, ara  # v3: showNormal
        p.showMinimized()
        qtbot.wait(20)
        p.goster()  # dogrudan gorunur durumda da
        qtbot.wait(20)
        assert p.isMinimized() is False and p.isVisible() is True
        p.kapat()


def test_b_k1_kenar_durumunda_panel_acikken_goster_ve_kapat(qtbot, pencere_fab, imlec) -> None:
    for son in ("goster", "kapat"):
        p = kur(pencere_fab, "K")
        imlec[0] = p.sekme.frameGeometry().center()
        qtbot.waitUntil(lambda: p.sekme.acik, timeout=120 + 2 * 60 + 300)
        getattr(p, son)()
        qtbot.wait(20)
        assert p.sekme.isVisible() is False and p.sekme.acik is False and p.sekme.yokluyor is False
        assert p.sekme.frameGeometry().size() == QSize(26, 52)
        imlec[0] = QPoint(DISARI)
        if son == "goster":
            p.kenara_al()
            qtbot.wait(20)
            assert p.sekme.acik is False and p.sekme.frameGeometry().size() == QSize(26, 52)
            p.kapat()


def test_b_k1_kapat_sirasinda_surukleme_yarida(qtbot, pencere_fab) -> None:
    p = kur(pencere_fab, "K")
    s = p.sekme
    qtbot.mousePress(s, Qt.MouseButton.LeftButton, pos=QPoint(s.width() - 3, s.height() // 2))
    assert s.surukleniyor is True
    p.kapat()
    assert s.surukleniyor is False and uclu(p) == (False, False, False)


# =============================================================== C. RASTGELE YURUYUS ===============================
KAMU_EYLEMLER = [e for e in EYLEMLER if e not in ("closeEvent",)]


@pytest.mark.parametrize("tohum", [1, 2, 3, 4, 5, 6, 7, 8])
def test_c_k1_rastgele_yuruyus_ulasilamaz_uclu_yok(qtbot, pencere_fab, tohum: int) -> None:
    """40 rastgele kamu eylemi: her adimda uclu tabloda (kapanmamis) ya da (F,F,F) (kapanmis); yoklayici == sekme gorunur;
    cikis_istendi <= 1 ve kapandi ile tutarli; durum enum uyesi."""
    rnd = random.Random(tohum)
    tepsi_var = rnd.random() < 0.7
    p = pencere_fab(tepsi_kullanilabilir=tepsi_var)
    p.show()
    n: list[int] = []
    p.cikis_istendi.connect(lambda: n.append(1))
    izin = {KabukDurumu.GORUNUR: {(True, False, False)}, KabukDurumu.TEPSI: {(False, False, True)}, KabukDurumu.KENAR: {(False, True, tepsi_var)}}
    gecmis: list[str] = []
    for _ in range(40):
        eylem = rnd.choice(KAMU_EYLEMLER)
        gecmis.append(eylem)
        EYLEMLER[eylem][0](qtbot, p)
        if p.kapandi:
            assert uclu(p) == (False, False, False) and len(n) == 1, gecmis
        else:
            assert uclu(p) in izin[p.durum] and len(n) == 0, f"{gecmis}: durum={p.durum} uclu={uclu(p)}"
        assert p.sekme.yokluyor is p.sekme.isVisible() and p.sekme.acik is False, gecmis
        assert p.durum in KabukDurumu
        if not tepsi_var:
            assert p.durum is not KabukDurumu.TEPSI, gecmis


def test_c_k1_rastgele_yuruyus_pozitif_kontrol_ihlal_yakalanir(qtbot, pencere_fab) -> None:
    """Olcunun ateslendigi gosterilir: disaridan `hide()` (taban sinif) uclu tablosunu bozar ve iddia yakalar."""
    p = kur(pencere_fab, "G")
    p.hide()
    assert uclu(p) not in {(True, False, False)}


# =============================================================== D. OMUR / TAKMA AD ================================
def test_d_omur_delete_later_python_referansi_tutulurken_sekme_zombi_PIN(qtbot, pencere_fab) -> None:
    """[PIN/dusuk] AnaPencere C++ nesnesi `deleteLater` ile silinir ama Python sarmalayicisi tutulursa: ebeveynsiz sekme
    GORUNUR ve YOKLAMAYA devam eder (sinyal aliciya baglanamaz -> pencereye donus yolu yok). Docstring 'AnaPencere
    silinince silinir' der (Python sahipligi) -- sarmalayici yasadikca silinmez. Referans birakilinca silinir (asagidaki test)."""
    p = kur(pencere_fab, "K")
    s = p.sekme
    p.deleteLater()
    qtbot.wait(50)  # qtbot.wait gercek dongu: DeferredDelete islenir
    assert shiboken6.isValid(p) is False
    assert shiboken6.isValid(s) is True and s.isVisible() is True and s.yokluyor is True  # PIN
    n: list[int] = []
    s.pencereyi_goster.connect(lambda: n.append(1))
    qtbot.mouseClick(s, Qt.MouseButton.RightButton, pos=QPoint(s.width() - 3, s.height() // 2))
    assert n == [1]  # sinyal yayilir, alici yok
    s.hide()


def test_d_omur_delete_later_referans_birakilinca_sekme_silinir_DOCSTRING(qtbot, ekran, imlec) -> None:
    """Docstring K1: 'Sekme EBEVEYNSIZ Tool penceredir (Python sahipligi: AnaPencere silinince silinir)'.
    OLCUM: AnaPencere `deleteLater` + referans birakma + gc -> sekme yasiyor ve GORUNUR (Y-A1)."""
    once = set(id(w) for w in gorunur_ust_duzey())
    p = AnaPencere(ekran, tepsi_kullanilabilir=True, imlec_konumu=lambda: QPoint(imlec[0]))
    p.show()
    p.kenara_al()
    assert len([w for w in gorunur_ust_duzey() if id(w) not in once]) == 1
    wp, ws = weakref.ref(p), weakref.ref(p.sekme)
    p.deleteLater()
    del p
    qtbot.wait(50)
    gc.collect()
    qtbot.wait(20)
    assert wp() is None  # AnaPencere sarmalayicisi toplandi (C++ de silindi)
    try:
        assert ws() is None, "sekme sarmalayicisi hala canli"
        assert [w for w in gorunur_ust_duzey() if id(w) not in once] == []
    finally:
        if ws() is not None:
            ws().hide()


def test_d_omur_ana_pencere_referansi_dusunce_sekme_silinir_DOCSTRING(qtbot, ekran, imlec) -> None:
    """Ayni iddia, deleteLater'siz: kenar durumundaki AnaPencere'nin son Python referansi dusuruldugunde (Python
    sahipligi -> C++ AnaPencere silinir) sekme de silinmeli. OLCUM: sekme yasiyor, gorunur, yokluyor; sag tik sinyali
    aliciya ulasmaz (pencere yok) -> geri donus yolu olmayan ZOMBI ust-duzey pencere (Y-A1)."""
    once = set(id(w) for w in gorunur_ust_duzey())
    p = AnaPencere(ekran, tepsi_kullanilabilir=True, imlec_konumu=lambda: QPoint(imlec[0]))
    p.show()
    p.kenara_al()
    wp, ws = weakref.ref(p), weakref.ref(p.sekme)
    del p
    gc.collect()
    qtbot.wait(30)
    assert wp() is None
    s = ws()
    try:
        assert s is None, f"sekme canli: gorunur={s.isVisible()} yokluyor={s.yokluyor}"
        assert [w for w in gorunur_ust_duzey() if id(w) not in once] == []
    finally:
        if s is not None:
            s.hide()


def test_d_omur_kapat_sonrasi_dusurulen_ana_pencere_sekme_silinir_v3(qtbot, ekran, imlec) -> None:
    """[v3 -- tur 1 PIN ters cevrildi, Y-A1 gizli sizinti yuzu] `kapat()` + referans dusurme: sekme de (gizli olsa da)
    toplanir; tur 1'de Python/C++ nesnesi yasiyordu (her ornek sizardi)."""
    p = AnaPencere(ekran, tepsi_kullanilabilir=True, imlec_konumu=lambda: QPoint(imlec[0]))
    p.show()
    p.kenara_al()
    p.kapat()
    ws, wt = weakref.ref(p.sekme), weakref.ref(p.tepsi)
    del p
    gc.collect()
    qtbot.wait(30)
    assert ws() is None and wt() is None  # v3


def test_d_omur_mekanizma_pozitif_kontrol_lambda_baglantisi_sarmalayiciyi_tutar(qtbot) -> None:
    """Olcunun ateslenebildigi ve ayristigi gosterilir: `clicked.connect(lambda: self...)` olan QWidget referans
    dusurulunce toplanmaz (gorunur kalir); `clicked.connect(self.yontem)` olan toplanir (kaybolur)."""

    class Lambdali(QWidget):
        def __init__(self) -> None:
            super().__init__(None, Qt.WindowType.Tool)
            self.b = QPushButton("x", self)
            self.b.clicked.connect(lambda: self._tik())

        def _tik(self) -> None:
            pass

    class BagliYontem(QWidget):
        def __init__(self) -> None:
            super().__init__(None, Qt.WindowType.Tool)
            self.b = QPushButton("x", self)
            self.b.clicked.connect(self._tik)

        def _tik(self) -> None:
            pass

    sonuc: dict[str, bool] = {}
    for K in (BagliYontem, Lambdali):
        once = set(id(w) for w in gorunur_ust_duzey())
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
    assert sonuc == {"BagliYontem": False, "Lambdali": True}


def test_d_omur_tepsi_ikonu_ana_pencere_silinince_gecersiz(qtbot, pencere_fab) -> None:
    p = kur(pencere_fab, "T")
    t, ikon = p.tepsi, p.tepsi.ikon
    p.deleteLater()
    qtbot.wait(50)
    assert shiboken6.isValid(t) is False and shiboken6.isValid(ikon) is False  # C++ ebeveynlik: tepsi ikonu zombi degil


def test_d_omur_iki_ana_pencere_bagimsiz(qtbot, pencere_fab) -> None:
    a, b = kur(pencere_fab, "K"), kur(pencere_fab, "T")
    na: list[int] = []
    nb: list[int] = []
    a.cikis_istendi.connect(lambda: na.append(1))
    b.cikis_istendi.connect(lambda: nb.append(1))
    assert a.sekme is not b.sekme and a.tepsi is not b.tepsi and a.tepsi.menu is not b.tepsi.menu
    a.kapat()
    assert (uclu(a), na, uclu(b), b.durum, nb) == ((False, False, False), [1], (False, False, True), KabukDurumu.TEPSI, [])
    b.goster()
    assert uclu(b) == (True, False, False) and uclu(a) == (False, False, False)
    b.tepsi.ikon.activated.emit(QSystemTrayIcon.ActivationReason.Trigger)
    assert uclu(a) == (False, False, False)


def test_d_omur_kenar_sekmesi_tek_basina_calisir(qtbot, ekran, imlec) -> None:
    s = KenarSekmesi(ekran, imlec_konumu=lambda: QPoint(imlec[0]), **HIZLI)
    s.show()
    try:
        n: list[int] = []
        s.pencereyi_goster.connect(lambda: n.append(1))
        imlec[0] = s.frameGeometry().center()
        qtbot.waitUntil(lambda: s.acik, timeout=500)
        s.dugme_goster.click()
        assert n == [1] and s.acik is False and s.yokluyor is True
    finally:
        s.hide()


def test_d_omur_kenar_sekmesi_tek_basina_referans_dusunce_silinir_DOCSTRING(qtbot, ekran, imlec) -> None:
    """Python sahipligi iddiasinin en yalin hali: ebeveynsiz KenarSekmesi'nin son referansi dusunce silinmeli.
    OLCUM: `__init__` icindeki `clicked.connect(lambda: self._mod_tiki(...))` kapanislari Qt baglantisinda self'i
    tutar -> sarmalayici hic toplanmaz, pencere gorunur kalir (Y-A1 koku)."""
    once = set(id(w) for w in gorunur_ust_duzey())
    s = KenarSekmesi(ekran, imlec_konumu=lambda: QPoint(imlec[0]), **HIZLI)
    s.show()
    ws = weakref.ref(s)
    del s
    gc.collect()
    qtbot.wait(20)
    try:
        assert ws() is None, "KenarSekmesi sarmalayicisi toplanmadi"
        assert [w for w in gorunur_ust_duzey() if id(w) not in once] == []
    finally:
        if ws() is not None:
            ws().hide()


def test_d_omur_imlec_konumu_istisna_atarsa_yoklayici_calisir_durum_degismez_PIN(qtbot, ekran) -> None:
    """[PIN/bilgi] Enjekte callable istisna atarsa istisna Qt yuvasindan sizar (pytest-qt yakalar), yoklayici
    durmaz, `acik` False kalir. Docstring iddiasi yok; kotu kullanim. Pozitif kontrol: atmayan callable ile acilir."""
    def kotu() -> QPoint:
        raise RuntimeError("imlec yok")

    s = KenarSekmesi(ekran, imlec_konumu=kotu, **HIZLI)
    with qtbot.captureExceptions() as yakalanan:
        s.show()
        qtbot.wait(60)
    assert len(yakalanan) >= 2 and all(e[0] is RuntimeError for e in yakalanan)
    assert s.yokluyor is True and s.acik is False
    s.hide()
    merkez = [QPoint(DISARI)]
    s2 = KenarSekmesi(ekran, imlec_konumu=lambda: merkez[0], **HIZLI)
    s2.show()
    merkez[0] = s2.frameGeometry().center()
    qtbot.waitUntil(lambda: s2.acik, timeout=500)
    s2.hide()


def test_d_omur_ekran_none_birincil_ekran(qtbot, pencere_fab, ekran) -> None:
    p = AnaPencere(None, tepsi_kullanilabilir=True)
    try:
        assert p.sekme.ekran_dikdortgeni == ekran.availableGeometry()
    finally:
        p.kapat()


def test_d_omur_ekran_none_ve_birincil_yoksa_runtime_error(monkeypatch, qtbot) -> None:
    once = set(id(w) for w in gorunur_ust_duzey())
    monkeypatch.setattr(QGuiApplication, "primaryScreen", staticmethod(lambda: None))
    with pytest.raises(RuntimeError):
        AnaPencere(None, tepsi_kullanilabilir=True)
    monkeypatch.undo()
    assert QGuiApplication.primaryScreen() is not None
    assert [w for w in gorunur_ust_duzey() if id(w) not in once] == []


def test_d_takma_ad_ekran_dikdortgeni_kopya(sekme_fab) -> None:
    s = sekme_fab()
    r = s.ekran_dikdortgeni
    r.setWidth(1)
    assert s.ekran_dikdortgeni.width() > 1 and s.ekran_dikdortgeni == s.ekran_dikdortgeni


def test_d_takma_ad_panel_boyutu_final_ama_mutable_PIN(qtbot, sekme_fab, imlec) -> None:
    """[PIN/dusuk] `PANEL_BOYUTU: Final[QSize]` yalniz tip duzeyinde sabittir; `setWidth` ile degistirilirse acik panel
    boyutu degisir (global paylasilan mutable). Geri alinir."""
    s = sekme_fab(**HIZLI)
    s.show()
    imlec[0] = s.frameGeometry().center()
    qtbot.waitUntil(lambda: s.acik, timeout=500)
    assert s.frameGeometry().size() == QSize(200, 132)
    s.hide()
    PANEL_BOYUTU.setWidth(300)
    try:
        s.show()
        qtbot.waitUntil(lambda: s.acik, timeout=500)
        assert s.frameGeometry().size() == QSize(300, 132)  # PIN
    finally:
        PANEL_BOYUTU.setWidth(200)
        s.hide()
    assert PANEL_BOYUTU == QSize(200, 132)


def test_d_takma_ad_kenar_ve_y_atamasi_atomik(sekme_fab) -> None:
    s = sekme_fab()
    s.kenar = "sol"  # type: ignore[assignment]  # str kabul (StrEnum)
    assert s.kenar is Kenar.SOL and s.frameGeometry().left() == s.ekran_dikdortgeni.left()
    with pytest.raises(ValueError):
        s.kenar = "orta"  # type: ignore[assignment]
    assert s.kenar is Kenar.SOL
    y0 = s.y
    for kotu in ("abc", None, [1], object()):
        with pytest.raises((ValueError, TypeError)):
            s.y = kotu  # type: ignore[assignment]
        assert s.y == y0


def test_d_takma_ad_ana_pencere_kenar_str_ve_gecersiz(qtbot, pencere_fab, ekran) -> None:
    p = pencere_fab(kenar="sol")
    assert p.sekme.kenar is Kenar.SOL
    p.kenara_al()
    assert p.sekme.frameGeometry().left() == ekran.availableGeometry().left()
    once = set(id(w) for w in gorunur_ust_duzey())
    with pytest.raises(ValueError):
        AnaPencere(ekran, kenar="orta", tepsi_kullanilabilir=True)  # type: ignore[arg-type]
    assert [w for w in gorunur_ust_duzey() if id(w) not in once] == []


def test_d_omur_calistir_enjekte_calistirici_ile_quit_baglantisi_ve_temizlik(qtbot, qapp) -> None:
    from src.ui.uygulama import calistir

    once = set(id(w) for w in gorunur_ust_duzey())
    tut: list[AnaPencere] = []

    def calistirici(app: QApplication, p: AnaPencere) -> int:
        tut.append(p)
        assert p.isVisible() and app.quitOnLastWindowClosed() is False
        QTimer.singleShot(0, p.kapat)
        return app.exec()  # cikis_istendi -> app.quit baglanmis olmali, yoksa asilir

    assert calistir([], calistirici=calistirici) == 0
    p = tut[0]
    assert p.kapandi and uclu(p) == (False, False, False) and p.sekme.yokluyor is False
    del tut[0], p
    gc.collect()
    qtbot.wait(20)
    assert [w for w in gorunur_ust_duzey() if id(w) not in once] == []


# =============================================================== E. SINIR -- GEOMETRI ==============================
EKRANLAR = [QRect(0, 0, 2560, 1392), QRect(-2560, 0, 2560, 1440), QRect(-2560, 0, 2048, 1152), QRect(0, 0, 800, 800), QRect(100, 50, 640, 480)]


@pytest.mark.parametrize("ekran_r", EKRANLAR, ids=[f"e{i}" for i in range(len(EKRANLAR))])
@pytest.mark.parametrize("kenar", [Kenar.SAG, Kenar.SOL])
def test_e_geometri_yaricap_1_sinir(ekran_r: QRect, kenar: Kenar) -> None:
    for y in (ekran_r.top() - 5, ekran_r.top(), ekran_r.center().y(), ekran_r.bottom() - 1, ekran_r.bottom() + 99):
        k = sekme_kapali_dikdortgeni(ekran_r, y, 1, kenar)
        assert k.size() == QSize(1, 2) and ekran_r.contains(k)
        assert (k.right() == ekran_r.right()) if kenar is Kenar.SAG else (k.left() == ekran_r.left())
        assert sekme_icinde(k, k.topLeft(), 1, kenar) and sekme_icinde(k, k.bottomLeft(), 1, kenar)  # her iki piksel disk icinde
        a = sekme_acik_dikdortgeni(ekran_r, y, 1, PANEL_BOYUTU, kenar)
        assert ekran_r.contains(a) and a.contains(k)


@pytest.mark.parametrize("yaricap", [0, -1, -26])
def test_e_geometri_saf_fonksiyonlar_sifir_negatif_yaricap_cokmez(yaricap: int) -> None:
    """Saf fonksiyonlar alan disi yaricapta cokmez (dogrulama KenarSekmesi yapicisinda); yaricap 0: 'icinde' asla True."""
    e = QRect(0, 0, 800, 800)
    k = sekme_kapali_dikdortgeni(e, 100, yaricap, Kenar.SAG)
    assert k.width() == yaricap and k.height() == 2 * yaricap
    sonuc = sekme_icinde(k, k.center(), yaricap, Kenar.SAG)
    assert isinstance(sonuc, bool) and (sonuc is False if yaricap == 0 else True)
    assert y_sinirla(e, 100, yaricap) == 100 and y_sinirla(e, 10_000, yaricap) == e.bottom() - 2 * yaricap + 1
    a = sekme_acik_dikdortgeni(e, 100, yaricap, PANEL_BOYUTU, Kenar.SAG)
    assert e.contains(a)


@pytest.mark.parametrize("yaricap", [0, -1])
def test_e_kenar_sekmesi_yaricap_sifir_negatif_valueerror(ekran, yaricap: int) -> None:
    once = set(id(w) for w in gorunur_ust_duzey())
    with pytest.raises(ValueError):
        KenarSekmesi(ekran, yaricap=yaricap)
    assert [w for w in gorunur_ust_duzey() if id(w) not in once] == []


def test_e_kenar_sekmesi_yaricap_1_calisir(qtbot, sekme_fab, imlec) -> None:
    s = sekme_fab(yaricap=1, **HIZLI)
    s.show()
    assert s.frameGeometry().size() == QSize(1, 2) and s.frameGeometry().right() == s.ekran_dikdortgeni.right()
    imlec[0] = s.frameGeometry().topLeft()
    qtbot.waitUntil(lambda: s.acik, timeout=500)
    assert s.frameGeometry().size() == PANEL_BOYUTU and s.frameGeometry().contains(imlec[0])


def test_e_geometri_yaricap_ekrandan_buyuk_y_ust_kenara_v3(qtbot, ekran) -> None:
    """Docstring: ekran 2r'den kisaysa y = top; sekme ustten tasmaz, alt tasmayi kabul eder."""
    e = QRect(ekran.availableGeometry())
    r = e.height()  # 2r = 2*height > height
    for y in (-10, 0, e.center().y(), 10**6):
        assert y_sinirla(e, y, r) == e.top()
        k = sekme_kapali_dikdortgeni(e, y, r, Kenar.SAG)
        assert k.top() == e.top() and k.right() == e.right() and k.bottom() > e.bottom()
    with pytest.raises(ValueError):  # v3: yaricap > 66 yapicida reddedilir (D-A3/D-A4 ust siniri); saf fonksiyon kabul eder
        KenarSekmesi(ekran, yaricap=r)
    # ayni sinif KenarSekmesi'nde: ekran 2r'den kisa (sahte availableGeometryChanged 30x30, r=66) -> y = top, alt tasma
    s = KenarSekmesi(ekran, yaricap=66)
    try:
        s.show()
        minik = QRect(0, 0, 30, 30)
        ekran.availableGeometryChanged.emit(minik)
        qtbot.wait(10)
        assert s.y == minik.top() and s.frameGeometry().top() == minik.top() and s.frameGeometry().right() == minik.right()
        assert s.frameGeometry().bottom() > minik.bottom()
        s.y = 10**6
        assert s.y == minik.top()
    finally:
        ekran.availableGeometryChanged.emit(e)
        qtbot.wait(10)
        s.hide()


def test_e_geometri_ust_sinir_valueerror_ayri_surec_v3() -> None:
    """[v3 -- tur 1 PIN ters cevrildi, D-A4 duzeltildi] Ust sinirlar dogrulanir: yaricap 67 / 2**30 / 2**31, acilma/kapanma/yoklama
    2**31 -> `ValueError` (OverflowError degil); tam sinir degerleri (66, 2**31-1) kabul; basarisiz yapimdan sonra
    `availableGeometryChanged` yayimi stderr'e HICBIR SEY yazmaz (yarim kurulu nesne sinyale bagli kalmadi). Ayri surec:
    tur 1'de bu sinif kaliciydi; simdi temiz oldugunu ayni sekilde olcuyoruz."""
    kod = "\n".join([
        "import os, sys, json; os.environ['QT_QPA_PLATFORM']='offscreen'; sys.path.insert(0, sys.argv[1])",
        "from PySide6 import QtGui, QtWidgets, QtCore",
        "from src.ui.kenar_sekmesi import KenarSekmesi",
        "app = QtWidgets.QApplication([]); e = QtGui.QGuiApplication.primaryScreen(); r = {}",
        "for ad, kw in (('yaricap_67', dict(yaricap=67)), ('yaricap_2_30', dict(yaricap=2**30)), ('yaricap_2_31', dict(yaricap=2**31)),"
        " ('acilma_2_31', dict(acilma_ms=2**31)), ('yoklama_2_31', dict(yoklama_ms=2**31)), ('kapanma_2_31', dict(kapanma_ms=2**31))):",
        "    try: KenarSekmesi(e, **kw); r[ad] = 'kabul'",
        "    except Exception as x: r[ad] = type(x).__name__",
        "r['ust_duzey'] = len(QtWidgets.QApplication.topLevelWidgets()); r['tum'] = len(QtWidgets.QApplication.allWidgets())",
        "s = KenarSekmesi(e, yaricap=66, acilma_ms=2**31-1, kapanma_ms=2**31-1, yoklama_ms=2**31-1); s.show()",
        "r['sinir_geo'] = [s.frameGeometry().width(), s.frameGeometry().height(), s.yokluyor]",
        "e.availableGeometryChanged.emit(QtCore.QRect(0, 0, 500, 500))",
        "r['sinyal_sonrasi'] = [s.frameGeometry().right(), s.ekran_dikdortgeni.width()]",
        "print(json.dumps(r))",
    ])
    import json
    ortam = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
    r = subprocess.run([sys.executable, "-c", kod, str(KOK)], capture_output=True, text=True, timeout=120, env=ortam, cwd=str(KOK))
    assert r.returncode == 0, r.stderr[-800:]
    sonuc = json.loads(r.stdout.strip().splitlines()[-1])
    for ad in ("yaricap_67", "yaricap_2_30", "yaricap_2_31", "acilma_2_31", "yoklama_2_31", "kapanma_2_31"):
        assert sonuc[ad] == "ValueError", (ad, sonuc[ad])
    assert sonuc["ust_duzey"] == 0 and sonuc["tum"] == 0  # basarisiz yapim hicbir Qt nesnesi birakmadi
    assert sonuc["sinir_geo"] == [66, 132, True]
    assert sonuc["sinyal_sonrasi"] == [499, 500]
    assert "OverflowError" not in r.stderr and "RuntimeError" not in r.stderr and "Traceback" not in r.stderr, r.stderr[-800:]


def test_e_geometri_bos_ve_negatif_qrect_cokmez() -> None:
    for e in (QRect(), QRect(0, 0, -10, -10), QRect(5, 5, 0, 0), QRect(0, 0, 1, 1)):
        assert y_sinirla(e, 50, 26) == e.top()
        k = sekme_kapali_dikdortgeni(e, 50, 26, Kenar.SAG)
        assert k.size() == QSize(26, 52) and k.top() == e.top() and k.right() == e.right()
        a = sekme_acik_dikdortgeni(e, 50, 26, PANEL_BOYUTU, Kenar.SOL)
        assert a.size() == PANEL_BOYUTU and a.left() == e.left() and a.top() == e.top()
        assert sekme_icinde(k, QPoint(0, 0), 26, Kenar.SAG) in (True, False)


def test_e_geometri_panel_ekrandan_buyuk_kenara_bitisik_ust_kenar() -> None:
    """Panel (200x132) ekrandan buyukse: `sag` -> sag kenara bitisik (sola tasar), `sol` -> sol kenara; ust = top.
    Docstring 'ekran icine sikistirilmis' bu sinifta karsilanamaz; davranis pinlenir (bilgi)."""
    e = QRect(0, 0, 100, 100)
    a = sekme_acik_dikdortgeni(e, 20, 26, PANEL_BOYUTU, Kenar.SAG)
    assert a.right() == e.right() and a.top() == e.top() and a.left() < e.left() and not e.contains(a)
    a = sekme_acik_dikdortgeni(e, 20, 26, PANEL_BOYUTU, Kenar.SOL)
    assert a.left() == e.left() and a.top() == e.top() and a.right() > e.right()
    # pozitif kontrol: panel sigan ekranda icerde
    e2 = QRect(0, 0, 200, 132)
    assert e2.contains(sekme_acik_dikdortgeni(e2, 0, 26, PANEL_BOYUTU, Kenar.SAG))


def test_e_geometri_y_sinirla_monoton_idempotent_ve_uclar() -> None:
    for e in EKRANLAR:
        alt = e.bottom() - 2 * 26 + 1
        onceki = None
        for y in range(e.top() - 100, e.bottom() + 100, 7):
            v = y_sinirla(e, y, 26)
            assert e.top() <= v <= alt and y_sinirla(e, v, 26) == v
            assert onceki is None or v >= onceki
            onceki = v
        assert y_sinirla(e, alt, 26) == alt and y_sinirla(e, alt + 1, 26) == alt
        assert y_sinirla(e, e.top(), 26) == e.top() and y_sinirla(e, e.top() - 1, 26) == e.top()
        k = sekme_kapali_dikdortgeni(e, alt, 26, Kenar.SAG)
        assert k.bottom() == e.bottom()  # tam sinirda alt kenar ekranin alt kenari


@pytest.mark.parametrize("kenar", [Kenar.SAG, Kenar.SOL])
def test_e_geometri_sekme_icinde_kose_ve_kenar_pikselleri(kenar: Kenar) -> None:
    e = QRect(0, 0, 800, 800)
    k = sekme_kapali_dikdortgeni(e, 300, 26, kenar)
    ic_x = k.left() if kenar is Kenar.SAG else k.right()  # ekranin ic tarafi
    dis_x = k.right() if kenar is Kenar.SAG else k.left()  # ekran kenari tarafi
    assert sekme_icinde(k, QPoint(ic_x, k.top()), 26, kenar) is False
    assert sekme_icinde(k, QPoint(ic_x, k.bottom()), 26, kenar) is False
    assert sekme_icinde(k, QPoint(dis_x, k.top()), 26, kenar) is True
    assert sekme_icinde(k, QPoint(dis_x, k.bottom()), 26, kenar) is True
    assert sekme_icinde(k, QPoint(ic_x, k.center().y()), 26, kenar) is True  # ic kenarin ortasi (uzaklik ~25.5)
    assert sekme_icinde(k, k.center(), 26, kenar) is True
    # dikdortgen disindaki noktalar disk icinde olsa da disarida (ekranin otesi)
    assert sekme_icinde(k, QPoint(dis_x + (1 if kenar is Kenar.SAG else -1), k.center().y()), 26, kenar) is False
    assert sekme_icinde(k, QPoint(ic_x, k.top() - 1), 26, kenar) is False
    # acik panel: duz contains (kose dahil)
    a = sekme_acik_dikdortgeni(e, 300, 26, PANEL_BOYUTU, kenar)
    assert sekme_icinde(a, a.topLeft(), 26, kenar) and sekme_icinde(a, a.bottomRight(), 26, kenar)
    assert sekme_icinde(a, QPoint(a.left() - 1, a.top()), 26, kenar) is False
    # kenar str olarak da kabul; gecersiz -> ValueError
    assert sekme_icinde(k, k.center(), 26, kenar.value) is True  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        sekme_icinde(k, k.center(), 26, "orta")  # type: ignore[arg-type]


def test_e_geometri_sekme_icinde_disk_sayimi_yarim_daire_alani() -> None:
    """Bagimsiz referans: kapali dikdortgende 'icinde' sayilan piksel sayisi ~ yarim daire alani (pi r^2 / 2)."""
    k = sekme_kapali_dikdortgeni(QRect(0, 0, 800, 800), 300, 26, Kenar.SAG)
    sayi = sum(sekme_icinde(k, QPoint(x, y), 26, Kenar.SAG) for x in range(k.left(), k.right() + 1) for y in range(k.top(), k.bottom() + 1))
    import math
    alan = math.pi * 26 * 26 / 2
    assert abs(sayi - alan) < 0.06 * alan, (sayi, alan)
    assert sayi < 26 * 52  # pozitif kontrol: duz contains olsaydi tum dikdortgen sayilirdi


def test_e_sinir_y_tipleri(sekme_fab) -> None:
    s = sekme_fab()
    e = s.ekran_dikdortgeni
    alt = e.bottom() - 52 + 1
    for v, b in ((12.7, 12), ("13", 13), (True, 1), (-5, e.top()), (10**9, alt), (alt, alt), (alt + 1, alt), (float("-inf"), None)):
        if b is None:
            with pytest.raises((OverflowError, ValueError)):
                s.y = v  # type: ignore[assignment]
            continue
        s.y = v  # type: ignore[assignment]
        assert s.y == b and s.frameGeometry().top() == b
    with pytest.raises(TypeError):
        s.y()  # type: ignore[operator]  # docstring: ozellik yontemi golgeler


def test_e_sinir_available_geometry_changed_y_sinir_disi_kalinca_sikistirilir(qtbot, sekme_fab, ekran) -> None:
    s = sekme_fab(**HIZLI)
    s.show()
    e = s.ekran_dikdortgeni
    s.y = 10**6
    assert s.y == e.bottom() - 52 + 1
    kucuk = QRect(e.left(), e.top(), e.width() - 100, e.height() // 2)
    ekran.availableGeometryChanged.emit(kucuk)
    qtbot.wait(10)
    try:
        assert s.ekran_dikdortgeni == kucuk and s.y == kucuk.bottom() - 52 + 1
        assert s.frameGeometry().right() == kucuk.right() and kucuk.contains(s.frameGeometry())
        buyuk = QRect(e.left(), e.top(), e.width() + 400, e.height() + 400)
        ekran.availableGeometryChanged.emit(buyuk)
        qtbot.wait(10)
        assert s.y == kucuk.bottom() - 52 + 1 and s.frameGeometry().right() == buyuk.right()  # y buyuyunce degismez
        minik = QRect(0, 0, 30, 30)  # 2r'den kisa: y = top
        ekran.availableGeometryChanged.emit(minik)
        qtbot.wait(10)
        assert s.y == 0 and s.frameGeometry() == QRect(30 - 26, 0, 26, 52)
    finally:
        ekran.availableGeometryChanged.emit(e)
        qtbot.wait(10)
    assert s.ekran_dikdortgeni == e


def test_e_sinir_available_geometry_changed_panel_acikken(qtbot, sekme_fab, ekran, imlec) -> None:
    s = sekme_fab(**HIZLI)
    s.show()
    e = s.ekran_dikdortgeni
    imlec[0] = s.frameGeometry().center()
    qtbot.waitUntil(lambda: s.acik, timeout=500)
    yeni = QRect(e.left(), e.top(), e.width() - 120, e.height())
    ekran.availableGeometryChanged.emit(yeni)
    qtbot.wait(10)
    try:
        assert s.acik is True and s.frameGeometry().right() == yeni.right() and s.frameGeometry().size() == PANEL_BOYUTU
        assert s.dugme_anlik.isVisible()
    finally:
        ekran.availableGeometryChanged.emit(e)
        qtbot.wait(10)


def test_e_sinir_kenar_degisimi_panel_acikken(qtbot, sekme_fab, imlec) -> None:
    s = sekme_fab(**HIZLI)
    s.show()
    e = s.ekran_dikdortgeni
    imlec[0] = s.frameGeometry().center()
    qtbot.waitUntil(lambda: s.acik, timeout=500)
    s.kenar = Kenar.SOL
    assert s.acik is True and s.frameGeometry().left() == e.left() and s.frameGeometry().size() == PANEL_BOYUTU
    assert s.frameGeometry().contains(imlec[0]) is False  # imlec sag panelde kaldi -> kapanmali
    qtbot.waitUntil(lambda: not s.acik, timeout=500)
    assert s.frameGeometry() == QRect(e.left(), s.y, 26, 52)
    s.kenar = Kenar.SAG
    assert s.frameGeometry().right() == e.right()


def test_e_sinir_yaricap_panel_yuksekliginin_yarisi_ust_sinir_salinim_yok_v3(qtbot, ekran) -> None:
    """[v3 -- tur 1 PIN ters cevrildi, D-A3 duzeltildi] yaricap > 66 (= PANEL_BOYUTU.height()//2) artik `ValueError`;
    66 ve 26'da disk icindeki her nokta acik panelin de icindedir -> tur 1'in salinim noktasinda (disk kosesi) panel
    acilir ve ACIK KALIR (0 gecis). Pozitif kontrol: olcu tur 1'de yaricap 80'de >= 4 gecis sayiyordu."""
    with pytest.raises(ValueError):
        KenarSekmesi(ekran, yaricap=80)
    for yaricap in (66, 26, 1):
        konum = [QPoint(DISARI)]
        s = KenarSekmesi(ekran, yaricap=yaricap, acilma_ms=20, kapanma_ms=20, yoklama_ms=10, imlec_konumu=lambda: konum[0])
        s.show()
        try:
            k = s.frameGeometry()
            konum[0] = QPoint(k.right(), k.top())  # disk kosesi (kenar tarafi): en uzak nokta
            assert sekme_icinde(k, konum[0], yaricap, Kenar.SAG) is True
            assert sekme_acik_dikdortgeni(s.ekran_dikdortgeni, s.y, yaricap, PANEL_BOYUTU, Kenar.SAG).contains(konum[0])
            qtbot.waitUntil(lambda: s.acik, timeout=500)
            degisim, onceki = 0, s.acik
            for _ in range(40):
                qtbot.wait(10)
                if s.acik != onceki:
                    degisim, onceki = degisim + 1, s.acik
            assert degisim == 0 and s.acik is True, (yaricap, degisim)
        finally:
            s.hide()


# =============================================================== F. SINIR -- ZAMAN =================================
def test_f_zaman_acilma_0_kapanma_0(qtbot, sekme_fab, imlec) -> None:
    s = sekme_fab(acilma_ms=0, kapanma_ms=0, yoklama_ms=10)
    s.show()
    assert (s.acilma_ms, s.kapanma_ms) == (0, 0)
    imlec[0] = s.frameGeometry().center()
    qtbot.waitUntil(lambda: s.acik, timeout=200)
    imlec[0] = QPoint(DISARI)
    qtbot.waitUntil(lambda: not s.acik, timeout=200)
    assert s.frameGeometry().size() == QSize(26, 52)


def test_f_zaman_kapanma_yoklamadan_kisa(qtbot, sekme_fab, imlec) -> None:
    s = sekme_fab(acilma_ms=5, kapanma_ms=5, yoklama_ms=50)
    s.show()
    imlec[0] = s.frameGeometry().center()
    qtbot.waitUntil(lambda: s.acik, timeout=400)
    imlec[0] = QPoint(DISARI)
    t0 = time.perf_counter()
    qtbot.waitUntil(lambda: not s.acik, timeout=400)
    assert (time.perf_counter() - t0) * 1000 <= 50 + 5 + 150


def test_f_zaman_cok_buyuk_acilma_hic_acilmaz(qtbot, sekme_fab, imlec) -> None:
    s = sekme_fab(acilma_ms=2**31 - 1, kapanma_ms=2**31 - 1, yoklama_ms=10)
    s.show()
    imlec[0] = s.frameGeometry().center()
    qtbot.wait(150)
    assert s.acik is False and s.yokluyor is True


def test_f_zaman_yoklama_0_valueerror_ve_1_calisir(qtbot, ekran, sekme_fab, imlec) -> None:
    with pytest.raises(ValueError):
        KenarSekmesi(ekran, yoklama_ms=0)
    with pytest.raises(ValueError):
        KenarSekmesi(ekran, acilma_ms=-1)
    with pytest.raises(ValueError):
        KenarSekmesi(ekran, kapanma_ms=-1)
    olcum: dict[int, tuple[int, float]] = {}
    for yoklama in (1, 60):
        imlec[1].setX(0)
        s = sekme_fab(acilma_ms=0, kapanma_ms=0, yoklama_ms=yoklama)
        s.show()
        t_cpu0, t0 = time.process_time(), time.perf_counter()
        qtbot.wait(400)
        cpu = (time.process_time() - t_cpu0) / (time.perf_counter() - t0)
        olcum[yoklama] = (imlec[1].x(), cpu)
        s.hide()
    print(f"\n[bilgi] 400 ms: yoklama_ms=1 -> {olcum[1][0]} cagri, CPU {olcum[1][1]:.3f}; yoklama_ms=60 -> {olcum[60][0]} cagri, CPU {olcum[60][1]:.3f}")
    assert olcum[1][0] > olcum[60][0] >= 4  # pozitif kontrol: kisa yoklama daha cok cagri
    assert olcum[1][0] < 100  # PIN/bilgi: Windows kaba sayac ~15.6 ms; yoklama_ms=1 ~26 cagri/400 ms (1 ms degil)
    assert olcum[1][1] < 0.9  # mesgul dongu degil


def test_f_zaman_hide_show_yoklayici_ve_cagri_sayaci(qtbot, sekme_fab, imlec) -> None:
    s = sekme_fab()  # urun degerleri (60 ms)
    assert s.yokluyor is False and imlec[1].x() == 0
    s.show()
    assert s.yokluyor is True
    qtbot.wait(5 * 60)
    n1 = imlec[1].x()
    assert n1 >= 3  # pozitif kontrol: gorunurken sayac artar
    s.hide()
    assert s.yokluyor is False
    qtbot.wait(5 * 60)
    assert imlec[1].x() == n1  # gizliyken artmaz
    s.setVisible(True)
    assert s.yokluyor is True
    qtbot.wait(3 * 60)
    assert imlec[1].x() > n1
    s.setVisible(False)
    assert s.yokluyor is False


def test_f_zaman_hide_acilma_sayacini_sifirlar(qtbot, sekme_fab, imlec) -> None:
    s = sekme_fab(acilma_ms=200, kapanma_ms=30, yoklama_ms=10)
    s.show()
    imlec[0] = s.frameGeometry().center()
    qtbot.wait(150)  # sayac calisiyor (200'e 50 kaldi)
    assert s.acik is False
    s.hide()
    qtbot.wait(100)
    s.show()
    assert s.acik is False
    qtbot.wait(100)  # sayac sifirdan basladiysa hala kapali (150+100+100 > 200 olsaydi acilirdi)
    assert s.acik is False
    qtbot.waitUntil(lambda: s.acik, timeout=200 + 2 * 10 + 300)


def test_f_zaman_surukleme_birakilmadan_hide(qtbot, sekme_fab, imlec) -> None:
    s = sekme_fab(**HIZLI)
    s.show()
    qtbot.mousePress(s, Qt.MouseButton.LeftButton, pos=QPoint(s.width() - 3, s.height() // 2))
    assert s.surukleniyor is True
    s.hide()
    assert s.surukleniyor is False
    s.show()
    assert s.surukleniyor is False and s.acik is False
    imlec[0] = s.frameGeometry().center()
    qtbot.waitUntil(lambda: s.acik, timeout=500)  # yoklama surukleme bayragina takilmiyor


def test_f_zaman_surukleme_sirasinda_sag_tik(qtbot, sekme_fab, pencere_fab) -> None:
    s = sekme_fab(**HIZLI)
    s.show()
    n: list[int] = []
    s.pencereyi_goster.connect(lambda: n.append(1))
    pos = QPoint(s.width() - 3, s.height() // 2)
    qtbot.mousePress(s, Qt.MouseButton.LeftButton, pos=pos)
    qtbot.mousePress(s, Qt.MouseButton.RightButton, pos=pos)
    assert n == [1] and s.surukleniyor is True
    qtbot.mouseRelease(s, Qt.MouseButton.RightButton, pos=pos)
    qtbot.mouseRelease(s, Qt.MouseButton.LeftButton, pos=pos)
    assert s.surukleniyor is False
    # AnaPencere ile: sag tik goster() -> sekme gizlenir -> surukleme temizlenir
    p = kur(pencere_fab, "K")
    ps = p.sekme
    qtbot.mousePress(ps, Qt.MouseButton.LeftButton, pos=pos)
    qtbot.mousePress(ps, Qt.MouseButton.RightButton, pos=pos)
    assert uclu(p) == (True, False, False) and ps.surukleniyor is False


@pytest.mark.parametrize("sayaclar", [HIZLI, dict(acilma_ms=120, kapanma_ms=450, yoklama_ms=60)], ids=["hizli", "urun"])
def test_f_zaman_surukleme_sinira_kilitlenir_ve_acik_degismez(qtbot, sekme_fab, imlec, sayaclar: dict[str, int]) -> None:
    s = sekme_fab(**sayaclar)
    s.show()
    e = s.ekran_dikdortgeni
    alt = e.bottom() - 52 + 1
    pos = QPoint(s.width() - 3, s.height() // 2)
    imlec[0] = s.frameGeometry().center()
    qtbot.mousePress(s, Qt.MouseButton.LeftButton, pos=pos)
    qtbot.mouseMove(s, pos=QPoint(pos.x(), pos.y() + 100_000))
    assert s.y == alt and s.frameGeometry().bottom() == e.bottom()
    qtbot.mouseMove(s, pos=QPoint(pos.x(), pos.y() - 100_000))
    assert s.y == e.top() and s.frameGeometry().top() == e.top()
    hedef = e.top() + 123
    qtbot.mouseMove(s, pos=QPoint(pos.x(), pos.y() + (hedef - s.y)))
    assert s.y == hedef
    imlec[0] = s.frameGeometry().center()
    qtbot.wait(s.acilma_ms + 3 * s.yoklama_ms)
    assert s.acik is False and s.surukleniyor is True
    qtbot.mouseRelease(s, Qt.MouseButton.LeftButton, pos=pos)
    assert s.surukleniyor is False
    qtbot.waitUntil(lambda: s.acik, timeout=s.acilma_ms + 2 * s.yoklama_ms + 300)
    assert s.frameGeometry().contains(imlec[0])


def test_f_zaman_acik_panelde_sol_tik_surukleme_baslatmaz(qtbot, sekme_fab, imlec) -> None:
    s = sekme_fab(**HIZLI)
    s.show()
    imlec[0] = s.frameGeometry().center()
    qtbot.waitUntil(lambda: s.acik, timeout=500)
    y0 = s.y
    qtbot.mousePress(s, Qt.MouseButton.LeftButton, pos=QPoint(2, 2))  # panel cercevesi (dugme degil)
    assert s.surukleniyor is False
    qtbot.mouseMove(s, pos=QPoint(2, 300))
    assert s.y == y0 and s.acik is True
    qtbot.mouseRelease(s, Qt.MouseButton.LeftButton, pos=QPoint(2, 300))


# =============================================================== G. SINYALLER ======================================
@pytest.mark.parametrize("yol", ["kapat", "close", "closeEvent", "dugme_kapat", "menu_cikis"])
@pytest.mark.parametrize("satir", ["G", "T", "K", "K0"])
def test_g_cikis_istendi_her_yoldan_tam_bir_kez(qtbot, pencere_fab, satir: str, yol: str) -> None:
    p = kur(pencere_fab, satir)
    n: list[int] = []
    p.cikis_istendi.connect(lambda: n.append(1))
    EYLEMLER[yol][0](qtbot, p)
    qtbot.wait(10)
    for ikinci in ("kapat", "close", "closeEvent", "dugme_kapat", "menu_cikis"):
        EYLEMLER[ikinci][0](qtbot, p)
    qtbot.wait(10)
    assert n == [1] and uclu(p) == (False, False, False)


def test_g_mod_sinyalleri_dinleyicisiz_hata_vermez_ve_durum_degismez(qtbot, pencere_fab) -> None:
    p = kur(pencere_fab, "K")
    for d in (p.dugme_anlik, p.dugme_bolge, p.sekme.dugme_anlik, p.sekme.dugme_bolge):
        d.click()
    assert (p.durum, uclu(p)) == (KabukDurumu.KENAR, (False, True, True))
    n: list[str] = []
    p.anlik_cevir_istendi.connect(lambda: n.append("a"))
    p.bolge_izle_istendi.connect(lambda: n.append("b"))
    for d in (p.dugme_anlik, p.sekme.dugme_anlik, p.dugme_bolge, p.sekme.dugme_bolge):
        d.click()
    assert n == ["a", "a", "b", "b"]  # pozitif kontrol: pencere ve sekme dugmesi ayni sinyal


@pytest.mark.parametrize("dugme", ["dugme_anlik", "dugme_bolge", "dugme_goster"])
def test_g_k4_sirasi_sinyal_aninda_panel_kapali(qtbot, sekme_fab, imlec, dugme: str) -> None:
    s = sekme_fab()  # urun degerleri
    s.show()
    imlec[0] = s.frameGeometry().center()
    qtbot.waitUntil(lambda: s.acik, timeout=120 + 2 * 60 + 300)
    d = getattr(s, dugme)
    assert d.isVisible()
    goruldu: list[tuple[bool, QSize, bool]] = []
    sinyal = {"dugme_anlik": s.anlik_cevir, "dugme_bolge": s.bolge_izle, "dugme_goster": s.pencereyi_goster}[dugme]
    sinyal.connect(lambda: goruldu.append((s.acik, s.frameGeometry().size(), d.isVisible())))
    imlec[0] = QPoint(DISARI)
    d.click()
    assert goruldu == [(False, QSize(26, 52), False)]


def test_g_k4_sirasi_ana_pencere_duzeyinde(qtbot, pencere_fab, imlec) -> None:
    p = kur(pencere_fab, "K")
    s = p.sekme
    imlec[0] = s.frameGeometry().center()
    qtbot.waitUntil(lambda: s.acik, timeout=120 + 2 * 60 + 300)
    goruldu: list[tuple[bool, Uclu]] = []
    p.anlik_cevir_istendi.connect(lambda: goruldu.append((s.acik, uclu(p))))
    imlec[0] = QPoint(DISARI)
    s.dugme_anlik.click()
    assert goruldu == [(False, (False, True, True))] and p.durum is KabukDurumu.KENAR


def test_g_k4_mod_tiki_sonrasi_imlec_disk_icindeyse_panel_yeniden_acilmaz_v3(qtbot, sekme_fab, imlec) -> None:
    """[v3 -- tur 1 PIN ters cevrildi, O-A1 duzeltildi] Mod tikinda imlec kapali diskin icinde kalsa da (dugmenin kenara
    yakin ucu) panel `acilma_ms + 4*yoklama_ms` sonra HALA kapali; disk disinda da kapali; diskten cikip girince acilir
    (pozitif kontrol: mandal tek atimlik). Urun sayaclari."""
    s = sekme_fab()  # urun degerleri
    s.show()
    k = s.frameGeometry()
    for nokta in (QPoint(k.right() - 4, k.center().y()), QPoint(k.right() - 100, k.center().y())):
        imlec[0] = k.center()
        qtbot.waitUntil(lambda: s.acik, timeout=120 + 2 * 60 + 300)
        assert s.frameGeometry().contains(nokta)  # nokta acik paneldedir (tiklanabilir)
        imlec[0] = nokta
        n: list[int] = []
        s.anlik_cevir.connect(lambda: n.append(1))
        s.dugme_anlik.click()
        assert n == [1] and s.acik is False
        qtbot.wait(120 + 4 * 60)
        assert s.acik is False, (nokta, s.acik)  # v3: mandal
        s.anlik_cevir.disconnect()
        imlec[0] = QPoint(DISARI)
        qtbot.wait(3 * 60)
        assert s.acik is False
    imlec[0] = k.center()  # pozitif kontrol: diskten ciktiktan sonra girince acilir
    qtbot.waitUntil(lambda: s.acik, timeout=120 + 2 * 60 + 300)
    imlec[0] = QPoint(DISARI)
    qtbot.waitUntil(lambda: not s.acik, timeout=450 + 2 * 60 + 300)


def test_g_yeniden_giris_mod_dinleyicisi_goster_kapat_kenara_al(qtbot, pencere_fab, imlec) -> None:
    for tepki, b_uclu, b_cikis in (("goster", (True, False, False), 0), ("kapat", (False, False, False), 1), ("kenara_al", (False, True, True), 0)):
        p = kur(pencere_fab, "K")
        n: list[int] = []
        p.cikis_istendi.connect(lambda: n.append(1))
        p.anlik_cevir_istendi.connect(getattr(p, tepki))
        imlec[0] = p.sekme.frameGeometry().center()
        qtbot.waitUntil(lambda: p.sekme.acik, timeout=120 + 2 * 60 + 300)
        imlec[0] = QPoint(DISARI)
        p.sekme.dugme_anlik.click()
        qtbot.wait(20)
        assert (uclu(p), len(n)) == (b_uclu, b_cikis), tepki
        assert p.sekme.acik is False and p.sekme.yokluyor is p.sekme.isVisible()
        p.kapat()


def test_g_yeniden_giris_cikis_dinleyicisi_kapat_close_goster(qtbot, pencere_fab) -> None:
    p = kur(pencere_fab, "G")
    n: list[int] = []

    def dinleyici() -> None:
        n.append(1)
        p.kapat()
        p.close()
        p.goster()
        p.kenara_al()

    p.cikis_istendi.connect(dinleyici)
    p.dugme_kapat.click()
    qtbot.wait(10)
    assert n == [1] and uclu(p) == (False, False, False)


def test_g_tepsi_yokken_tepsi_sinyalleri_yine_calisir(qtbot, pencere_fab) -> None:
    p = kur(pencere_fab, "K0")
    assert p.tepsi.kullanilabilir is False and p.tepsi.gorunur() is False
    p.tepsi.goster()
    assert p.tepsi.gorunur() is False
    _menu_eylem(p, "Pencereyi göster")
    assert uclu(p) == (True, False, False)
    _menu_eylem(p, "Kenara al")
    assert uclu(p) == (False, True, False)
    assert [a.text() for a in p.tepsi.menu.actions() if not a.isSeparator()] == ["Pencereyi göster", "Kenara al", "Çıkış"]
    assert [a.isSeparator() for a in p.tepsi.menu.actions()] == [False, False, True, False]


def test_g_tepsi_kullanilabilir_pozitif_kontrol(qtbot, qapp) -> None:
    t = Tepsi(QIcon(), None, kullanilabilir=True)
    t.goster()
    assert t.gorunur() is True  # offscreen'de isVisible True doner (KRT o12) -> olcu ateslenebilir
    t.gizle()
    assert t.gorunur() is False
    t.bildir("a", "b", 10)  # hata yok
    t0 = Tepsi(QIcon(), None, kullanilabilir=False)
    t0.goster()
    assert t0.gorunur() is False and t0.ikon.isVisible() is False
    t0.bildir("a", "b", 10)
    t0.gizle()


# =============================================================== H. K6 / K7 AST ====================================
YASAK_ADLAR = {"QMessageBox", "QDialog", "QInputDialog", "QFileDialog", "print", "logging", "warnings", "sleep", "processEvents", "quit", "exit", "exec"}
YASAK_MODULLER = ("src.capture", "src.ocr", "src.translate", "logging", "warnings", "time")


def _adlar(agac: ast.AST) -> set[str]:
    bulunan: set[str] = set()
    for dugum in ast.walk(agac):
        if isinstance(dugum, ast.Name):
            bulunan.add(dugum.id)
        elif isinstance(dugum, ast.Attribute):
            bulunan.add(dugum.attr)
    return bulunan


def _importlar(agac: ast.AST) -> set[str]:
    m: set[str] = set()
    for dugum in ast.walk(agac):
        if isinstance(dugum, ast.Import):
            m.update(a.name for a in dugum.names)
        elif isinstance(dugum, ast.ImportFrom) and dugum.module:
            m.add(dugum.module)
    return m


@pytest.mark.parametrize("dosya", ["kabuk.py", "kenar_sekmesi.py", "geometri.py", "__init__.py", "__main__.py", "uygulama.py"])
def test_h_k6_k7_ast_yasak_ad_ve_import_yok(dosya: str) -> None:
    agac = ast.parse((SRC_UI / dosya).read_text(encoding="utf-8"))
    izin = {"exec", "quit"} if dosya == "uygulama.py" else set()  # calistir: app.exec(), cikis_istendi -> app.quit
    ihlal = (_adlar(agac) & YASAK_ADLAR) - izin
    assert ihlal == set(), f"{dosya}: {sorted(ihlal)}"
    kotu = {m for m in _importlar(agac) if m.startswith(YASAK_MODULLER)}
    assert kotu == set(), f"{dosya}: {sorted(kotu)}"


def test_h_k6_ast_pozitif_kontrol() -> None:
    ornek = "import logging\nfrom src.capture import x\nclass A:\n    def f(self):\n        print(1); QMessageBox.warning(); time.sleep(1); app.processEvents(); QApplication.quit()\n"
    agac = ast.parse(ornek)
    assert {"print", "QMessageBox", "sleep", "processEvents", "quit"} <= (_adlar(agac) & YASAK_ADLAR)
    assert {"logging", "src.capture"} <= {m for m in _importlar(agac) if m.startswith(YASAK_MODULLER)}


def test_h_k7_taze_surecte_pipeline_modulu_yuklenmez() -> None:
    kod = (
        "import sys; sys.path.insert(0, sys.argv[1]); import src.ui.kabuk, src.ui.uygulama; "
        "print(sorted(m for m in sys.modules if m.startswith(('src.capture', 'src.ocr', 'src.translate'))))"
    )
    ortam = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
    r = subprocess.run([sys.executable, "-c", kod, str(KOK)], capture_output=True, text=True, timeout=120, env=ortam, cwd=str(KOK))
    assert r.returncode == 0, r.stderr[-500:]
    assert r.stdout.strip() == "[]"


def test_h_k7_taze_surec_pozitif_kontrol() -> None:
    kod = "import sys; sys.path.insert(0, sys.argv[1]); import src.capture.monitors; print(sorted(m for m in sys.modules if m.startswith('src.capture')))"
    r = subprocess.run([sys.executable, "-c", kod, str(KOK)], capture_output=True, text=True, timeout=120, cwd=str(KOK))
    assert r.returncode == 0 and r.stdout.strip() != "[]"


def test_h_enum_uyeleri_baglayici() -> None:
    assert [m.value for m in KabukDurumu] == ["gorunur", "tepsi", "kenar"] and [m.value for m in Kenar] == ["sag", "sol"]
    assert KabukDurumu("kenar") is KabukDurumu.KENAR and str(KabukDurumu.TEPSI) == "tepsi"
    assert PANEL_BOYUTU == QSize(200, 132)
    s = KenarSekmesi(QGuiApplication.primaryScreen())
    try:
        assert (s.yaricap, s.acilma_ms, s.kapanma_ms, s.yoklama_ms) == (26, 120, 450, 60)
        with pytest.raises(AttributeError):
            s.yaricap = 5  # type: ignore[misc]
        with pytest.raises(AttributeError):
            s.acik = True  # type: ignore[misc]
    finally:
        s.hide()
