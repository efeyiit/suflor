"""T-012 K1/K5/K6/K7/K8 -- `src.ui.kabuk`: `AnaPencere`, `Tepsi`, `KabukDurumu` (pytest-qt, offscreen).

Durum uclusu = (pencere gorunur, sekme gorunur, tepsi ikonu gorunur):
  gorunur (T,F,F) · tepsi (F,F,T) · kenar (F,T,T) · kenar (tepsi yok) (F,T,F)
`kapat()` sonrasi (F,F,F) ve `cikis_istendi` tam bir kez. Fixture teardown'da
`kapat()` cagirir (sekme ebeveynsiz `Tool` pencere -- KRT O6 sira kirliligi).
"""
from __future__ import annotations

import ast
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtTest import QTest
from pytestqt.qtbot import QtBot

import src.ui
from src.ui.geometri import Kenar
from src.ui.kabuk import AnaPencere, KabukDurumu, Tepsi
from src.ui.kenar_sekmesi import KenarSekmesi

Qt = QtCore.Qt
SOL_DUGME = Qt.MouseButton.LeftButton
Uclu = tuple[bool, bool, bool]
GORUNUR: Uclu = (True, False, False)
TEPSI: Uclu = (False, False, True)
KENAR: Uclu = (False, True, True)
KENAR_TEPSI_YOK: Uclu = (False, True, False)
KAPALI: Uclu = (False, False, False)
UI_DIZINI = Path(src.ui.__file__).resolve().parent



def _bas(w: QtWidgets.QWidget, dugme: QtCore.Qt.MouseButton, pos: QtCore.QPoint) -> None:
    QTest.mousePress(w, dugme, QtCore.Qt.KeyboardModifier.NoModifier, pos)


def _birak(w: QtWidgets.QWidget, dugme: QtCore.Qt.MouseButton, pos: QtCore.QPoint) -> None:
    QTest.mouseRelease(w, dugme, QtCore.Qt.KeyboardModifier.NoModifier, pos)


def _tasi(w: QtWidgets.QWidget, pos: QtCore.QPoint) -> None:
    QTest.mouseMove(w, pos)


def _tikla(w: QtWidgets.QWidget, dugme: QtCore.Qt.MouseButton) -> None:
    QTest.mouseClick(w, dugme, QtCore.Qt.KeyboardModifier.NoModifier, w.rect().center())


class SahteImlec:
    def __init__(self) -> None:
        self.nokta = QtCore.QPoint(5, 5)
        self.sayac = 0

    def __call__(self) -> QtCore.QPoint:
        self.sayac += 1
        return QtCore.QPoint(self.nokta)


def uclu(p: AnaPencere) -> Uclu:
    return (p.isVisible(), p.sekme.isVisible(), p.tepsi.gorunur())


def _gorunur_ust_duzey() -> list[str]:
    return [type(w).__name__ for w in QtWidgets.QApplication.topLevelWidgets() if w.isVisible()]


def _yeni(qtbot: QtBot, **kw: object) -> AnaPencere:
    kw.setdefault("tepsi_kullanilabilir", True)
    kw.setdefault("imlec_konumu", SahteImlec())
    p = AnaPencere(**kw)  # type: ignore[arg-type]
    qtbot.addWidget(p)
    qtbot.addWidget(p.sekme)
    return p


@pytest.fixture
def pencere(qtbot: QtBot, qapp: QtWidgets.QApplication) -> Iterator[AnaPencere]:
    eski = qapp.quitOnLastWindowClosed()
    qapp.setQuitOnLastWindowClosed(False)  # urun ayari (`uygulama.calistir`)
    p = _yeni(qtbot)
    p.show()
    yield p
    p.kapat()
    qapp.setQuitOnLastWindowClosed(eski)


@pytest.fixture
def cikis(pencere: AnaPencere) -> list[int]:
    sayac: list[int] = []
    pencere.cikis_istendi.connect(lambda: sayac.append(1))
    return sayac


# -- K1 durum makinesi -----------------------------------------------------------------------


def test_k1_kabuk_durumu_uc_uye() -> None:
    assert [d.value for d in KabukDurumu] == ["gorunur", "tepsi", "kenar"]
    assert KabukDurumu("kenar") is KabukDurumu.KENAR and str(KabukDurumu.TEPSI) == "tepsi"


def test_k1_baslangic_gorunur(pencere: AnaPencere) -> None:
    assert pencere.durum is KabukDurumu.GORUNUR and uclu(pencere) == GORUNUR
    assert pencere.kapandi is False
    assert isinstance(pencere.sekme, KenarSekmesi) and isinstance(pencere.tepsi, Tepsi)


def test_k1_gorunur_to_tepsi(pencere: AnaPencere) -> None:
    pencere.tepsiye_al()
    assert pencere.durum is KabukDurumu.TEPSI and uclu(pencere) == TEPSI


def test_k1_tepsi_to_gorunur(pencere: AnaPencere) -> None:
    pencere.tepsiye_al()
    pencere.goster()
    assert pencere.durum is KabukDurumu.GORUNUR and uclu(pencere) == GORUNUR


def test_k1_gorunur_to_kenar(pencere: AnaPencere) -> None:
    pencere.kenara_al()
    assert pencere.durum is KabukDurumu.KENAR and uclu(pencere) == KENAR
    assert pencere.sekme.yokluyor is True


def test_k1_kenar_to_gorunur_tepsi_ikonu_da_gizlenir(pencere: AnaPencere) -> None:
    pencere.kenara_al()
    pencere.goster()
    assert pencere.durum is KabukDurumu.GORUNUR and uclu(pencere) == GORUNUR
    assert pencere.sekme.yokluyor is False


def test_k1_tepsi_to_kenar_tepsi_menusu(pencere: AnaPencere) -> None:
    pencere.tepsiye_al()
    pencere.tepsi.kenara_al_istendi.emit()
    assert pencere.durum is KabukDurumu.KENAR and uclu(pencere) == KENAR


def test_k1_kenar_to_tepsi_yolu_yok(pencere: AnaPencere) -> None:
    """`kenar -> tepsi` gecisi tanimli degil: kenar durumunda `tepsiye_al()` cagrisi kenari korur."""
    pencere.kenara_al()
    pencere.tepsiye_al()
    assert pencere.durum is KabukDurumu.KENAR and uclu(pencere) == KENAR


def test_k1_gorunur_yollari_hepsi_ayni_uclu(pencere: AnaPencere) -> None:
    yollar: list[Callable[[], object]] = [
        lambda: pencere.tepsi.goster_istendi.emit(),
        lambda: pencere.sekme.pencereyi_goster.emit(),
        lambda: pencere.sekme.dugme_goster.click(),
        lambda: pencere.tepsi.ikon.activated.emit(QtWidgets.QSystemTrayIcon.ActivationReason.Trigger),
        lambda: pencere.tepsi.ikon.activated.emit(QtWidgets.QSystemTrayIcon.ActivationReason.DoubleClick),
    ]
    for i, yol in enumerate(yollar):
        pencere.kenara_al() if i % 2 else pencere.tepsiye_al()
        yol()
        assert pencere.durum is KabukDurumu.GORUNUR and uclu(pencere) == GORUNUR, i


def test_k1_tepsiye_al_iki_kez_idempotent(pencere: AnaPencere) -> None:
    pencere.tepsiye_al()
    pencere.tepsiye_al()
    assert pencere.durum is KabukDurumu.TEPSI and uclu(pencere) == TEPSI


def test_k1_kenara_al_iki_kez_idempotent(pencere: AnaPencere) -> None:
    pencere.kenara_al()
    pencere.kenara_al()
    assert pencere.durum is KabukDurumu.KENAR and uclu(pencere) == KENAR
    pencere.goster()
    pencere.goster()
    assert uclu(pencere) == GORUNUR


def test_k1_kapat_gorunur_durumundan(pencere: AnaPencere, cikis: list[int]) -> None:
    pencere.kapat()
    assert uclu(pencere) == KAPALI and pencere.kapandi is True
    assert pencere.tepsi.gorunur() is False and pencere.sekme.yokluyor is False
    assert cikis == [1]
    assert _gorunur_ust_duzey() == []


def test_k1_kapat_iki_kez_tek_sinyal(pencere: AnaPencere, cikis: list[int]) -> None:
    pencere.kapat()
    pencere.kapat()
    assert cikis == [1] and uclu(pencere) == KAPALI


@pytest.mark.parametrize("durum", ["tepsi", "kenar"])
def test_k1_kapat_her_durumdan(pencere: AnaPencere, cikis: list[int], durum: str) -> None:
    pencere.tepsiye_al() if durum == "tepsi" else pencere.kenara_al()
    pencere.kapat()
    assert uclu(pencere) == KAPALI and cikis == [1] and pencere.sekme.yokluyor is False
    assert _gorunur_ust_duzey() == []


def test_k1_close_event_gorunur_durumunda_kapat_ile_esdeger(pencere: AnaPencere, cikis: list[int]) -> None:
    assert pencere.close() is True
    assert uclu(pencere) == KAPALI and cikis == [1] and pencere.kapandi is True
    assert _gorunur_ust_duzey() == []


def test_k1_close_event_ignore_edilmez(qtbot: QtBot, pencere: AnaPencere, cikis: list[int]) -> None:
    olay = QtGui.QCloseEvent()
    pencere.closeEvent(olay)
    assert olay.isAccepted() is True and cikis == [1] and uclu(pencere) == KAPALI


def test_k1_close_sonra_kapat_ikinci_sinyal_yok(pencere: AnaPencere, cikis: list[int]) -> None:
    pencere.close()
    pencere.kapat()
    assert cikis == [1]


def test_k1_kapat_sonra_close_ikinci_sinyal_yok(pencere: AnaPencere, cikis: list[int]) -> None:
    pencere.kapat()
    pencere.close()
    assert cikis == [1]


@pytest.mark.parametrize("durum", ["tepsi", "kenar"])
def test_k1_close_gizli_durumlarda_da_kapatir(pencere: AnaPencere, cikis: list[int], durum: str) -> None:
    pencere.tepsiye_al() if durum == "tepsi" else pencere.kenara_al()
    pencere.close()
    assert uclu(pencere) == KAPALI and cikis == [1]


def test_k1_kapat_sonrasi_dirilme_yok(pencere: AnaPencere, cikis: list[int]) -> None:
    pencere.kapat()
    pencere.goster()
    assert uclu(pencere) == KAPALI
    pencere.tepsiye_al()
    assert uclu(pencere) == KAPALI
    pencere.kenara_al()
    assert uclu(pencere) == KAPALI
    assert cikis == [1] and _gorunur_ust_duzey() == []


def test_k1_dugmeler_gecisleri_tetikler(qtbot: QtBot, pencere: AnaPencere, cikis: list[int]) -> None:
    _tikla(pencere.dugme_tepsi, SOL_DUGME)
    assert uclu(pencere) == TEPSI
    pencere.goster()
    _tikla(pencere.dugme_kenar, SOL_DUGME)
    assert uclu(pencere) == KENAR
    pencere.goster()
    _tikla(pencere.dugme_kapat, SOL_DUGME)
    assert uclu(pencere) == KAPALI and cikis == [1]


def test_k1_tepsi_cikis_menusu_kapatir(pencere: AnaPencere, cikis: list[int]) -> None:
    pencere.tepsiye_al()
    pencere.tepsi.cikis_istendi.emit()
    assert uclu(pencere) == KAPALI and cikis == [1]


def test_k1_kabuk_qapplication_quit_cagirmaz(qtbot: QtBot, qapp: QtWidgets.QApplication, pencere: AnaPencere) -> None:
    """`kapat()` sonrasi olay dongusu calismaya devam eder (quit cagrilsaydi exec disinda etkisiz olurdu; AST ile de olculur)."""
    pencere.kapat()
    qtbot.wait(20)
    agac = ast.parse((UI_DIZINI / "kabuk.py").read_text(encoding="utf-8"))
    adlar = [d.attr for d in ast.walk(agac) if isinstance(d, ast.Attribute)] + [d.id for d in ast.walk(agac) if isinstance(d, ast.Name)]
    assert "quit" not in adlar and "exit" not in adlar


# -- K5 tepsi ------------------------------------------------------------------------------------


def test_k5_tepsi_yoksa_tepsiye_al_kenara_duser(qtbot: QtBot, qapp: QtWidgets.QApplication) -> None:
    p = _yeni(qtbot, tepsi_kullanilabilir=False)
    p.show()
    p.tepsiye_al()
    assert p.durum is KabukDurumu.KENAR and uclu(p) == KENAR_TEPSI_YOK
    assert p.tepsi.kullanilabilir is False and p.tepsi.gorunur() is False
    p.goster()
    assert uclu(p) == GORUNUR
    p.kenara_al()
    assert uclu(p) == KENAR_TEPSI_YOK
    p.kapat()
    assert uclu(p) == KAPALI


def test_k5_tepsi_yokken_gorunur_daima_false(qtbot: QtBot) -> None:
    t = Tepsi(QtGui.QIcon(), None, kullanilabilir=False)
    t.goster()
    assert t.gorunur() is False and t.ikon.isVisible() is False
    t.bildir("a", "b", 10)  # sessiz, hata yok
    t.gizle()
    assert t.gorunur() is False


def test_k5_tepsi_varken_goster_gizle(qtbot: QtBot) -> None:
    t = Tepsi(QtGui.QIcon(), None, kullanilabilir=True)
    assert t.gorunur() is False
    t.goster()
    assert t.gorunur() is True  # offscreen'de show() -> isVisible() True (KRT o12)
    t.gizle()
    assert t.gorunur() is False
    t.goster()
    t.bildir("Suflör", "deneme", 10)
    t.gizle()


def test_k5_kullanilabilir_none_platforma_sorar(qtbot: QtBot, monkeypatch: pytest.MonkeyPatch) -> None:
    assert QtWidgets.QSystemTrayIcon.isSystemTrayAvailable() is False  # offscreen olgusu
    assert Tepsi(QtGui.QIcon(), None).kullanilabilir is False
    monkeypatch.setattr(QtWidgets.QSystemTrayIcon, "isSystemTrayAvailable", staticmethod(lambda: True))
    assert Tepsi(QtGui.QIcon(), None).kullanilabilir is True  # pozitif kontrol
    p = AnaPencere(imlec_konumu=SahteImlec())
    qtbot.addWidget(p)
    qtbot.addWidget(p.sekme)
    assert p.tepsi.kullanilabilir is True
    p.kapat()


def test_k5_ana_pencere_varsayilan_offscreen_tepsi_yok(qtbot: QtBot) -> None:
    p = AnaPencere(imlec_konumu=SahteImlec())
    qtbot.addWidget(p)
    qtbot.addWidget(p.sekme)
    p.show()
    assert p.tepsi.kullanilabilir is False
    p.tepsiye_al()
    assert uclu(p) == KENAR_TEPSI_YOK
    p.kapat()


def test_k5_menu_eylem_adlari(pencere: AnaPencere) -> None:
    eylemler = pencere.tepsi.menu.actions()
    assert [a.text() for a in eylemler if not a.isSeparator()] == ["Pencereyi göster", "Kenara al", "Çıkış"]
    assert [a.isSeparator() for a in eylemler] == [False, False, True, False]
    assert pencere.tepsi.ikon.contextMenu() is pencere.tepsi.menu


def test_k5_menu_eylemleri_sinyal_yayar(qtbot: QtBot) -> None:
    t = Tepsi(QtGui.QIcon(), None, kullanilabilir=True)
    goster, kenar, cikis = [a for a in t.menu.actions() if not a.isSeparator()]
    with qtbot.waitSignal(t.goster_istendi, timeout=500):
        goster.trigger()
    with qtbot.waitSignal(t.kenara_al_istendi, timeout=500):
        kenar.trigger()
    with qtbot.waitSignal(t.cikis_istendi, timeout=500):
        cikis.trigger()


@pytest.mark.parametrize("sebep", ["Trigger", "DoubleClick"])
def test_k5_ikona_tik_goster(qtbot: QtBot, pencere: AnaPencere, sebep: str) -> None:
    pencere.tepsiye_al()
    pencere.tepsi.ikon.activated.emit(getattr(QtWidgets.QSystemTrayIcon.ActivationReason, sebep))
    assert pencere.durum is KabukDurumu.GORUNUR and uclu(pencere) == GORUNUR


@pytest.mark.parametrize("sebep", ["Context", "MiddleClick", "Unknown"])
def test_k5_ikona_diger_tik_gostermez(qtbot: QtBot, pencere: AnaPencere, sebep: str) -> None:
    pencere.tepsiye_al()
    pencere.tepsi.ikon.activated.emit(getattr(QtWidgets.QSystemTrayIcon.ActivationReason, sebep))
    assert pencere.durum is KabukDurumu.TEPSI and uclu(pencere) == TEPSI


def test_k5_tepsi_ikonu_ve_ipucu(pencere: AnaPencere) -> None:
    assert isinstance(pencere.tepsi.ikon, QtWidgets.QSystemTrayIcon)
    assert pencere.tepsi.ikon.toolTip() != "" and not pencere.tepsi.ikon.icon().isNull()
    assert not pencere.windowIcon().isNull()


def test_k5_tepsiye_al_bildirim_balonu_gostermez(pencere: AnaPencere, monkeypatch: pytest.MonkeyPatch) -> None:
    """real_check [5c] kok nedeni (tur 1): `tepsiye_al()` balonu (Windows bildirimi, baska surecin penceresi,
    sag altta 396x153 px, ~6.2 s; `ms` yok sayilir) sekmenin alt-sag konumunu ortuyor, gercek sag tik balona
    gidiyordu (`evidence/olcum-5c-balon.txt`). Karar: `tepsiye_al()` balon GOSTERMEZ; `Tepsi.bildir` API'si kalir."""
    cagri: list[tuple[object, ...]] = []
    monkeypatch.setattr(pencere.tepsi.ikon, "showMessage", lambda *a, **k: cagri.append(a))
    pencere.tepsiye_al()
    assert uclu(pencere) == TEPSI and cagri == []
    pencere.goster()
    pencere.tepsiye_al()
    assert cagri == []
    pencere.tepsi.bildir("a", "b", 10)  # pozitif kontrol: casus ateslenebilir (kural 10)
    assert len(cagri) == 1


# -- K6 / K7 AST: modal yok, metin yok, blok yok, pipeline importu yok ---------------------------

_YASAK_ADLAR = {"QMessageBox", "QDialog", "QInputDialog", "QFileDialog", "print", "logging", "warnings", "sleep",
                "processEvents", "input"}
_YASAK_MODULLER = ("src.capture", "src.ocr", "src.translate", "logging", "warnings", "time")


def _ihlaller(kaynak: str, *, exec_serbest: bool = False) -> list[str]:
    agac = ast.parse(kaynak)
    bulgular: list[str] = []
    for dugum in ast.walk(agac):
        if isinstance(dugum, ast.Name) and dugum.id in _YASAK_ADLAR:
            bulgular.append(dugum.id)
        elif isinstance(dugum, ast.Attribute) and dugum.attr in _YASAK_ADLAR:
            bulgular.append(dugum.attr)
        elif isinstance(dugum, ast.Attribute) and dugum.attr in {"exec", "exec_"} and not exec_serbest:
            bulgular.append(dugum.attr)
        elif isinstance(dugum, ast.Import):
            bulgular.extend(a.name for a in dugum.names if a.name.startswith(_YASAK_MODULLER))
        elif isinstance(dugum, ast.ImportFrom) and dugum.module and dugum.module.startswith(_YASAK_MODULLER):
            bulgular.append(dugum.module)
    return bulgular


@pytest.mark.parametrize("dosya", ["__init__.py", "__main__.py", "uygulama.py", "kabuk.py", "kenar_sekmesi.py", "geometri.py"])
def test_k6_k7_kaynak_yasak_ad_ve_import_icermez(dosya: str) -> None:
    kaynak = (UI_DIZINI / dosya).read_text(encoding="utf-8")
    assert _ihlaller(kaynak, exec_serbest=dosya == "uygulama.py") == []


def test_k6_k7_ast_olcusu_pozitif_kontrol() -> None:
    assert _ihlaller("from PySide6.QtWidgets import QMessageBox\nQMessageBox.warning(None, 'a', 'b')\n") != []
    assert _ihlaller("import src.capture.dpi\n") == ["src.capture.dpi"]
    assert _ihlaller("from src.translate import sozluk\n") == ["src.translate"]
    assert _ihlaller("print('x')\n") == ["print"]
    assert _ihlaller("import time\ntime.sleep(1)\n") == ["time", "sleep"]
    assert _ihlaller("app.processEvents()\n") == ["processEvents"]
    assert _ihlaller("d.exec()\n") == ["exec"] and _ihlaller("d.exec()\n", exec_serbest=True) == []
    assert _ihlaller("ikon.showMessage('a', 'b')\n") == []  # QSystemTrayIcon.showMessage serbest
    assert _ihlaller("from PySide6.QtCore import QTimer\n") == []


def test_k7_src_ui_pipeline_modullerini_yuklemez_taze_surec() -> None:
    """Tam takimda baska testler pipeline modullerini yuklemis olur (sef olctu); olcu taze surectedir."""
    import os
    import subprocess
    import sys

    kod = (
        "import sys; import src.ui.kabuk, src.ui.uygulama, src.ui.kenar_sekmesi, src.ui.geometri; "
        "print(sorted(m for m in sys.modules if m.startswith(('src.capture', 'src.ocr', 'src.translate'))))"
    )
    ortam = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    sonuc = subprocess.run([sys.executable, "-c", kod], cwd=UI_DIZINI.parents[1], env=ortam, capture_output=True, text=True, timeout=60)
    assert sonuc.returncode == 0, sonuc.stderr
    assert sonuc.stdout.strip() == "[]"


def test_k7_pencere_ve_sekme_dugmeleri_ayni_sinyali_yayar(qtbot: QtBot, pencere: AnaPencere) -> None:
    for pencere_dugmesi, sekme_dugmesi, sinyal in (
        (pencere.dugme_anlik, pencere.sekme.dugme_anlik, pencere.anlik_cevir_istendi),
        (pencere.dugme_bolge, pencere.sekme.dugme_bolge, pencere.bolge_izle_istendi),
    ):
        with qtbot.waitSignal(sinyal, timeout=1000):
            pencere_dugmesi.click()
        pencere.kenara_al()
        with qtbot.waitSignal(sinyal, timeout=1000):
            sekme_dugmesi.click()
        assert uclu(pencere) == KENAR  # mod sinyali durumu degistirmez
        pencere.goster()


def test_k7_dinleyicisiz_tiklama_hata_vermez(qtbot: QtBot, pencere: AnaPencere) -> None:
    pencere.dugme_anlik.click()
    pencere.dugme_bolge.click()
    pencere.kenara_al()
    pencere.sekme.dugme_anlik.click()
    pencere.sekme.dugme_bolge.click()
    assert uclu(pencere) == KENAR


# -- K8 cercevesiz pencere: surukleme, erisilebilirlik ------------------------------------------


def test_k8_baslik_seridinden_surukleme_tasir(qtbot: QtBot, pencere: AnaPencere) -> None:
    pencere.move(100, 100)
    bas = QtCore.QPoint(pencere.width() // 2, 20)  # ust 44 px, dugmeler disinda
    _bas(pencere, SOL_DUGME, bas)
    _tasi(pencere, QtCore.QPoint(bas.x() + 60, bas.y() + 40))
    assert pencere.pos() == QtCore.QPoint(160, 140)
    _birak(pencere, SOL_DUGME, QtCore.QPoint(bas.x() + 60, bas.y() + 40))
    _tasi(pencere, QtCore.QPoint(bas.x() + 200, bas.y() + 200))
    assert pencere.pos() == QtCore.QPoint(160, 140)  # birakildiktan sonra tasinmaz


def test_k8_govdeden_surukleme_tasimaz(qtbot: QtBot, pencere: AnaPencere) -> None:
    pencere.move(100, 100)
    bas = QtCore.QPoint(pencere.width() // 2, pencere.height() - 10)
    _bas(pencere, SOL_DUGME, bas)
    _tasi(pencere, QtCore.QPoint(bas.x() + 60, bas.y() + 40))
    assert pencere.pos() == QtCore.QPoint(100, 100)
    _birak(pencere, SOL_DUGME, bas)


def test_k8_dugme_uzerinde_basinca_tasinmaz(qtbot: QtBot, pencere: AnaPencere) -> None:
    pencere.move(100, 100)
    d = pencere.dugme_kenar
    assert d.mapTo(pencere, d.rect().center()).y() < 44  # dugme baslik seridinde
    _bas(d, SOL_DUGME, d.rect().center())
    _tasi(d, QtCore.QPoint(d.width() + 300, d.height() + 300))
    assert pencere.pos() == QtCore.QPoint(100, 100)
    _birak(d, SOL_DUGME, QtCore.QPoint(d.width() + 300, d.height() + 300))  # dugme disinda: tik yok
    assert uclu(pencere) == GORUNUR


def test_k8_surukleme_sonrasi_sag_tik_pencereyi_getirir(qtbot: QtBot, pencere: AnaPencere) -> None:
    """real_check [5c] yolu offscreen: kenar durumunda sekme alt sinira suruklenir, sonra sekmeye SAG TIK
    (`qtbot.mouseClick`: press + release) -> `goster()`: uclu (T,F,F), durum gorunur, sekme kapali ve gizli."""
    pencere.kenara_al()
    s = pencere.sekme
    g = s.ekran_dikdortgeni
    bas = QtCore.QPoint(s.yaricap - 4, s.yaricap)
    _bas(s, SOL_DUGME, bas)
    _tasi(s, QtCore.QPoint(bas.x(), bas.y() + 100_000))
    _birak(s, SOL_DUGME, QtCore.QPoint(bas.x(), bas.y() + 100_000))
    assert s.y == g.bottom() - 2 * s.yaricap + 1 and s.surukleniyor is False and uclu(pencere) == KENAR
    qtbot.mouseClick(s, Qt.MouseButton.RightButton, pos=bas)  # type: ignore[no-untyped-call]  # pytest-qt 4.5 tipsiz
    assert pencere.durum is KabukDurumu.GORUNUR and uclu(pencere) == GORUNUR
    assert s.acik is False and s.surukleniyor is False


def test_k8_uc_dugme_tooltip_ve_accessible_name(pencere: AnaPencere) -> None:
    adlar = {d.accessibleName() for d in (pencere.dugme_kapat, pencere.dugme_tepsi, pencere.dugme_kenar)}
    assert adlar == {"Kapat", "Tepsiye al", "Kenara al"}
    for d in (pencere.dugme_kapat, pencere.dugme_tepsi, pencere.dugme_kenar, pencere.dugme_anlik, pencere.dugme_bolge):
        assert isinstance(d, QtWidgets.QPushButton) and d.toolTip() != ""
    assert pencere.dugme_kapat.accessibleName() == "Kapat"
    assert pencere.windowFlags() & Qt.WindowType.FramelessWindowHint
    assert pencere.windowTitle() == "Suflör"


# -- yapici secenekleri ----------------------------------------------------------------------


def test_k2_kenar_parametresi_sekmeye_gecer(qtbot: QtBot) -> None:
    p = _yeni(qtbot, kenar=Kenar.SOL)
    assert p.sekme.kenar is Kenar.SOL
    p.kenara_al()
    g = p.sekme.ekran_dikdortgeni
    assert p.sekme.frameGeometry().left() == g.left()
    p.kapat()


def test_k2_ekran_none_birincil(qtbot: QtBot) -> None:
    p = _yeni(qtbot)
    ekran = QtGui.QGuiApplication.primaryScreen()
    assert ekran is not None and p.sekme.ekran_dikdortgeni == ekran.availableGeometry()
    p2 = _yeni(qtbot, ekran=ekran)
    assert p2.sekme.ekran_dikdortgeni == ekran.availableGeometry()
    p.kapat()
    p2.kapat()


def test_k2_ekran_yoksa_runtimeerror(qtbot: QtBot, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(QtGui.QGuiApplication, "primaryScreen", staticmethod(lambda: None))
    with pytest.raises(RuntimeError):
        AnaPencere(imlec_konumu=SahteImlec())


def test_k4_imlec_konumu_sekmeye_enjekte_edilir(qtbot: QtBot) -> None:
    imlec = SahteImlec()
    p = _yeni(qtbot, imlec_konumu=imlec)
    p.show()
    p.kenara_al()
    qtbot.waitUntil(lambda: imlec.sayac > 0, timeout=3 * p.sekme.yoklama_ms + 300)
    p.goster()
    n = imlec.sayac
    qtbot.wait(3 * p.sekme.yoklama_ms)
    assert imlec.sayac == n  # sekme gizli: yoklama yok
    p.kapat()
