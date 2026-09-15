"""T-012 K1 (▲ Y1) + T-013 K4/K5 -- `src.ui.uygulama.calistir` giris noktasi ve `python -m src.ui`.

`calistir` `QApplication` kurar (varsa yeniden kullanir), `setQuitOnLastWindowClosed(False)`,
`AnaPencere` gosterir, `cikis_istendi -> app.quit` baglar ve `calistirici(app, pencere)`yi
calistirir (varsayilan `app.exec()`). Testte calistirici ENJEKTE edilir; `quit` baglantisi
gercek `app.exec()` ile olculur (`kapat()` 0 ms sonra -> exec 3000 ms guvenlik siniri
dolmadan doner).

T-013 (▲ Y1): `kisayol_servisi` verilmezse `calistir` GERCEK Win32'li servis kurar (`gercek_win32=True`) --
sefin `conftest.py`si `SUFLOR_GERCEK_KISAYOL_YASAK=1` koydugu icin bu testlerde `RuntimeError`
(`test_k4_kisayol_servisi_verilmezse_gercek_servis_kurulur_kemer_ateslenir`); her test sahte fn'li servisi
ENJEKTE eder (`_sahte_servis`). Hicbir test gercek `RegisterHotKey` cagirmaz.
"""
from __future__ import annotations

import gc
import runpy
import time
import weakref
from collections.abc import Iterator, Mapping

import pytest
from PySide6 import QtCore, QtWidgets
from pytestqt.qtbot import QtBot

from src.ui import uygulama
from src.ui.geometri import Kenar
from src.ui.kabuk import AnaPencere, KabukDurumu
from src.ui.kisayol import MOD_ALT, MOD_CONTROL, MOD_NOREPEAT, KayitSonucu, KisayolServisi
from src.ui.uygulama import VARSAYILAN_KISAYOLLAR, calistir

CA = MOD_CONTROL | MOD_ALT


class SahteWin32:
    def __init__(self) -> None:
        self.kayitlar: list[tuple[int, int, int]] = []
        self.kaldirmalar: list[int] = []
        self.reddet: dict[tuple[int, int], int] = {}
        self.altgr: dict[int, str] = {}
        self._son_hata = 0

    def kayit(self, kimlik: int, mod: int, vk: int) -> bool:
        self.kayitlar.append((kimlik, mod, vk))
        kod = self.reddet.get((mod & ~MOD_NOREPEAT, vk))
        if kod is None:
            return True
        self._son_hata = kod
        return False

    def kaldir(self, kimlik: int) -> bool:
        self.kaldirmalar.append(kimlik)
        return True

    def hata_kodu(self) -> int:
        return self._son_hata

    def altgr_karakteri(self, vk: int) -> str:
        return self.altgr.get(vk, "")

    def servis(self) -> KisayolServisi:
        return KisayolServisi(None, kayit_fn=self.kayit, kaldir_fn=self.kaldir, hata_kodu_fn=self.hata_kodu,
                              altgr_karakteri_fn=self.altgr_karakteri)


@pytest.fixture
def sahte(qapp: QtWidgets.QApplication) -> SahteWin32:
    return SahteWin32()


@pytest.fixture
def servis(sahte: SahteWin32, qtbot: QtBot) -> Iterator[KisayolServisi]:
    s = sahte.servis()
    yield s
    s.hepsini_kaldir()
    s.deleteLater()
    qtbot.wait(10)


@pytest.fixture
def quit_korumasi(qapp: QtWidgets.QApplication) -> Iterator[None]:
    eski = qapp.quitOnLastWindowClosed()
    yield
    qapp.setQuitOnLastWindowClosed(eski)


def _kur(servis: KisayolServisi, kisayollar: Mapping[str, str] | None = None, kenar: Kenar = Kenar.SAG) -> tuple[AnaPencere, int]:
    """`calistir`i hemen donen calistiriciyla kosar; pencereyi ACIK tutar (test kapatir)."""
    kutu: list[AnaPencere] = []

    def calistirici(app: QtWidgets.QApplication, pencere: AnaPencere) -> int:
        kutu.append(pencere)
        return 5

    rc = calistir(["suflor"], kenar=kenar, calistirici=calistirici, kisayollar=kisayollar, kisayol_servisi=servis)
    return kutu[0], rc


# -- T-012 K1 (kisayol servisi enjekte edilerek guncellendi) -------------------------------------


def test_calistir_uygulamayi_kurar_ve_calistiriciyi_cagirir(qtbot: QtBot, qapp: QtWidgets.QApplication, servis: KisayolServisi, quit_korumasi: None) -> None:
    gorulen: list[tuple[QtWidgets.QApplication, AnaPencere, bool]] = []

    def calistirici(app: QtWidgets.QApplication, pencere: AnaPencere) -> int:
        gorulen.append((app, pencere, app.quitOnLastWindowClosed()))
        assert pencere.isVisible() and pencere.durum is KabukDurumu.GORUNUR
        assert pencere.sekme.kenar is Kenar.SOL
        pencere.kapat()
        return 42

    assert calistir(["suflor"], kenar=Kenar.SOL, calistirici=calistirici, kisayol_servisi=servis) == 42
    assert len(gorulen) == 1
    app, pencere, quit_on_last = gorulen[0]
    assert app is qapp and quit_on_last is False
    assert pencere.kapandi is True and not pencere.isVisible() and not pencere.sekme.isVisible()


def test_calistir_cikis_istendi_quit_baglar_gercek_exec(qtbot: QtBot, qapp: QtWidgets.QApplication, servis: KisayolServisi, quit_korumasi: None) -> None:
    sure: list[float] = []

    def calistirici(app: QtWidgets.QApplication, pencere: AnaPencere) -> int:
        QtCore.QTimer.singleShot(0, pencere.kapat)  # cikis_istendi -> quit bagli ise exec hemen doner
        QtCore.QTimer.singleShot(3000, app.quit)  # guvenlik: bagli degilse 3 s sonra doner
        t0 = time.perf_counter()
        rc = app.exec()
        sure.append((time.perf_counter() - t0) * 1000)
        return rc

    assert calistir(None, calistirici=calistirici, kisayol_servisi=servis) == 0
    assert sure and sure[0] < 2000, sure
    qtbot.wait(10)  # exec sonrasi olay dongusu hala calisiyor (quitNow sifirlandi)


def test_calistir_varsayilan_kenar_sag(qtbot: QtBot, qapp: QtWidgets.QApplication, servis: KisayolServisi, quit_korumasi: None) -> None:
    kenarlar: list[Kenar] = []

    def calistirici(app: QtWidgets.QApplication, pencere: AnaPencere) -> int:
        kenarlar.append(pencere.sekme.kenar)
        pencere.kapat()
        return 0

    calistir(calistirici=calistirici, kisayol_servisi=servis)
    assert kenarlar == [Kenar.SAG]


def test_main_modulu_calistir_i_cagirir(monkeypatch: pytest.MonkeyPatch) -> None:
    cagrilar: list[object] = []

    def sahte(argv: object = None, **kw: object) -> int:
        cagrilar.append(argv)
        return 7

    monkeypatch.setattr(uygulama, "calistir", sahte)
    with pytest.raises(SystemExit) as hata:
        runpy.run_module("src.ui", run_name="__main__", alter_sys=True)
    assert hata.value.code == 7 and len(cagrilar) == 1


# -- T-013 K4: kisayol -> kabuk sinyali; tepsi/kenar durumundan bagimsiz --------------------------


def test_k4_varsayilan_kisayollar_ctrl_alt_d_ve_r_norepeat(sahte: SahteWin32, servis: KisayolServisi, quit_korumasi: None) -> None:
    """▲ Y2: varsayilan `Ctrl+Alt+D` (TR-Q AltGr'de bos) + `Ctrl+Alt+R`; `Ctrl+Alt+T` (₺) YOK."""
    assert dict(VARSAYILAN_KISAYOLLAR) == {"anlik_cevir": "Ctrl+Alt+D", "bolge_izle": "Ctrl+Alt+R"}
    p, rc = _kur(servis)
    try:
        assert rc == 5
        assert [(m & ~MOD_NOREPEAT, vk) for _, m, vk in sahte.kayitlar] == [(CA, ord("D")), (CA, ord("R"))]
        assert all(m & MOD_NOREPEAT for _, m, _ in sahte.kayitlar)
        assert servis.kayitli() == {"anlik_cevir": "Ctrl+Alt+D", "bolge_izle": "Ctrl+Alt+R"}
        assert p.durum_metni() == "", "hepsi OK -> durum satiri bos"
    finally:
        p.kapat()


def test_k4_varsayilan_kisayollar_degistirilemez() -> None:
    with pytest.raises(TypeError):
        VARSAYILAN_KISAYOLLAR["anlik_cevir"] = "Ctrl+Alt+T"  # type: ignore[index]


@pytest.mark.parametrize("durum", ["gorunur", "tepsi", "kenar"])
def test_k4_tetiklendi_ad_tablosuyla_sinyal_durum_degismez(qtbot: QtBot, monkeypatch: pytest.MonkeyPatch, servis: KisayolServisi, quit_korumasi: None, durum: str) -> None:
    monkeypatch.setattr(QtWidgets.QSystemTrayIcon, "isSystemTrayAvailable", staticmethod(lambda: True))  # offscreen'de tepsi yok
    p, _ = _kur(servis)
    try:
        anlik: list[int] = []
        bolge: list[int] = []
        p.anlik_cevir_istendi.connect(lambda: anlik.append(1))
        p.bolge_izle_istendi.connect(lambda: bolge.append(1))
        if durum == "tepsi":
            p.tepsiye_al()
        elif durum == "kenar":
            p.kenara_al()
        beklenen = {"gorunur": KabukDurumu.GORUNUR, "tepsi": KabukDurumu.TEPSI, "kenar": KabukDurumu.KENAR}[durum]
        assert p.durum is beklenen
        uclu0 = (p.isVisible(), p.sekme.isVisible(), p.tepsi.gorunur())
        servis.tetiklendi.emit("anlik_cevir")
        assert anlik == [1] and bolge == []
        servis.tetiklendi.emit("bolge_izle")
        servis.tetiklendi.emit("bolge_izle")
        assert anlik == [1] and bolge == [1, 1]
        servis.tetiklendi.emit("bilinmeyen")
        servis.tetiklendi.emit("")
        assert anlik == [1] and bolge == [1, 1], "bilinmeyen ad yok sayilir"
        assert p.durum is beklenen and (p.isVisible(), p.sekme.isVisible(), p.tepsi.gorunur()) == uclu0, "sinyal durumu degistirmez (alici karar verir)"
    finally:
        p.kapat()


def test_k4_ozel_kisayollar_ve_bilinmeyen_ad_kaydedilir_ama_sinyal_yok(sahte: SahteWin32, servis: KisayolServisi, quit_korumasi: None) -> None:
    p, _ = _kur(servis, {"bolge_izle": "Ctrl+Shift+B", "anlik_cevir": "Alt+Shift+A", "ekstra": "Ctrl+Alt+E"})
    try:
        assert servis.kayitli() == {"bolge_izle": "Ctrl+Shift+B", "anlik_cevir": "Alt+Shift+A", "ekstra": "Ctrl+Alt+E"}
        assert "Ctrl+Shift+B" in p.dugme_bolge.text() and "Alt+Shift+A" in p.dugme_anlik.text()
        sayac: list[int] = []
        p.anlik_cevir_istendi.connect(lambda: sayac.append(1))
        p.bolge_izle_istendi.connect(lambda: sayac.append(2))
        servis.tetiklendi.emit("ekstra")
        assert sayac == []
    finally:
        p.kapat()


def test_k4_bos_kisayol_tablosu_kayit_yok_etiketler_kisayol_yok(sahte: SahteWin32, servis: KisayolServisi, quit_korumasi: None) -> None:
    p, _ = _kur(servis, {})
    try:
        assert sahte.kayitlar == [] and servis.kayitli() == {}
        assert "(kısayol yok)" in p.dugme_anlik.text() and "(kısayol yok)" in p.dugme_bolge.text()
        assert p.durum_metni() == ""
    finally:
        p.kapat()


def test_k4_cikis_istendi_hepsini_kaldirir(sahte: SahteWin32, servis: KisayolServisi, quit_korumasi: None) -> None:
    p, _ = _kur(servis)
    idler = [k for k, _, _ in sahte.kayitlar]
    p.kapat()
    assert sorted(sahte.kaldirmalar) == sorted(idler) and servis.kayitli() == {}
    p.kapat()
    assert len(sahte.kaldirmalar) == 2, "ikinci kapat: cikis_istendi yayilmaz, kaldirma tekrar etmez"


def test_k4_kisayol_servisi_verilmezse_gercek_servis_kurulur_kemer_ateslenir(qapp: QtWidgets.QApplication, quit_korumasi: None) -> None:
    """▲ Y1: enjeksiyonsuz `calistir` GERCEK servis kurar (`gercek_win32=True`); testte kemer `RuntimeError` verir.
    Pencere yaratilmis olabilir -> temizlik."""
    with pytest.raises(RuntimeError, match="SUFLOR_GERCEK_KISAYOL_YASAK"):
        calistir(["suflor"], calistirici=lambda app, pencere: 0)
    for w in QtWidgets.QApplication.topLevelWidgets():
        if isinstance(w, AnaPencere) and not w.kapandi:
            w.kapat()


def test_k4_kisayol_servisi_verilmezse_yapici_argumanlari(monkeypatch: pytest.MonkeyPatch, sahte: SahteWin32, quit_korumasi: None, qtbot: QtBot) -> None:
    """Varsayilan kurulum: `KisayolServisi(pencere, gercek_win32=True)` -- ebeveyn pencere (omur), gercek Win32."""
    gorulen: list[tuple[object, bool]] = []
    kutu: list[KisayolServisi] = []

    class Casus(KisayolServisi):
        def __init__(self, ebeveyn: QtCore.QObject | None = None, *, gercek_win32: bool = False, **kw: object) -> None:
            gorulen.append((ebeveyn, gercek_win32))
            super().__init__(ebeveyn, kayit_fn=sahte.kayit, kaldir_fn=sahte.kaldir, hata_kodu_fn=sahte.hata_kodu,
                             altgr_karakteri_fn=sahte.altgr_karakteri)
            kutu.append(self)

    monkeypatch.setattr(uygulama, "KisayolServisi", Casus)
    kutu_p: list[AnaPencere] = []

    def calistirici(app: QtWidgets.QApplication, pencere: AnaPencere) -> int:
        kutu_p.append(pencere)
        return 0

    calistir(["suflor"], calistirici=calistirici)
    p = kutu_p[0]
    try:
        assert len(gorulen) == 1 and gorulen[0][0] is p and gorulen[0][1] is True
        assert kutu[0].parent() is p
        assert len(sahte.kayitlar) == 2
    finally:
        p.kapat()
        qtbot.wait(10)


def test_k4_calistir_sonrasi_pencere_toplanabilir_baglanti_pencereyi_tutmaz(qtbot: QtBot, servis: KisayolServisi, quit_korumasi: None) -> None:
    """T-012 Y-A1 sinifi: `tetiklendi -> kisayol_tetiklendi` bagli yontemdir; `del`+gc sonrasi pencere toplanir,
    sinyal alicisiz yayilabilir."""
    p, _ = _kur(servis)
    p.kapat()
    wp = weakref.ref(p)
    del p
    gc.collect()
    qtbot.wait(50)
    assert wp() is None, "calistir baglantisi pencereyi tutuyor (partial/lambda?)"
    servis.tetiklendi.emit("anlik_cevir")


# -- T-013 K5: cakisma acikca bildirilir, kisayollar gorunur, modal yok ---------------------------


def test_k5_cakisma_durum_satiri_ve_etiketler(sahte: SahteWin32, servis: KisayolServisi, quit_korumasi: None) -> None:
    sahte.reddet[(CA, ord("D"))] = 1409
    p, rc = _kur(servis)
    try:
        assert rc == 5, "cikis kodu degismez"
        metin = p.durum_metni()
        assert "Ctrl+Alt+D" in metin and "başka bir uygulama" in metin and "kaydedilemedi" in metin
        assert "Pencere düğmeleri ve tepsi menüsü çalışmaya devam eder." in metin
        assert "ayar" not in metin.lower(), "ayar yok (v2): 'ayarlardan degistirin' yazilmaz"
        assert "Ctrl+Alt+R" not in metin
        assert servis.kayitli() == {"bolge_izle": "Ctrl+Alt+R"}
        assert "(kısayol yok)" in p.dugme_anlik.text() and "Ctrl+Alt+D" not in p.dugme_anlik.text()
        assert "Ctrl+Alt+R" in p.dugme_bolge.text()
        ipucu = p.tepsi.ikon.toolTip()
        assert "Ctrl+Alt+R" in ipucu and "(kısayol yok)" in ipucu and "Ctrl+Alt+D" not in ipucu
    finally:
        p.kapat()


def test_k5_altgr_cakismasi_metni(sahte: SahteWin32, servis: KisayolServisi, quit_korumasi: None) -> None:
    sahte.altgr[ord("T")] = "₺"
    p, _ = _kur(servis, {"anlik_cevir": "Ctrl+Alt+T", "bolge_izle": "Ctrl+Alt+R"})
    try:
        metin = p.durum_metni()
        assert "Ctrl+Alt+T" in metin and "AltGr" in metin and "klavye düzeni" in metin
        assert sahte.kayitlar and all(vk != ord("T") for _, _, vk in sahte.kayitlar)
        assert "(kısayol yok)" in p.dugme_anlik.text() and "Ctrl+Alt+R" in p.dugme_bolge.text()
    finally:
        p.kapat()


def test_k5_gecersiz_kombinasyon_metni(sahte: SahteWin32, servis: KisayolServisi, quit_korumasi: None) -> None:
    p, _ = _kur(servis, {"anlik_cevir": "Ctrl+Alt+D", "bolge_izle": "Alt+Tab"})
    try:
        metin = p.durum_metni()
        assert "Alt+Tab" in metin and "geçersiz kombinasyon" in metin
        assert "Ctrl+Alt+D" in p.dugme_anlik.text() and "(kısayol yok)" in p.dugme_bolge.text()
    finally:
        p.kapat()


def test_k5_win32_hata_kodu_metni(sahte: SahteWin32, servis: KisayolServisi, quit_korumasi: None) -> None:
    sahte.reddet[(CA, ord("R"))] = 87
    p, _ = _kur(servis)
    try:
        metin = p.durum_metni()
        assert "Ctrl+Alt+R" in metin and "87" in metin and "kaydedilemedi" in metin
    finally:
        p.kapat()


def test_k5_iki_cakisma_ikisi_de_anilir(sahte: SahteWin32, servis: KisayolServisi, quit_korumasi: None) -> None:
    sahte.reddet[(CA, ord("D"))] = 1409
    sahte.reddet[(CA, ord("R"))] = 1409
    p, _ = _kur(servis)
    try:
        metin = p.durum_metni()
        assert "Ctrl+Alt+D" in metin and "Ctrl+Alt+R" in metin
        assert metin.count("Pencere düğmeleri") == 1
        assert "(kısayol yok)" in p.dugme_anlik.text() and "(kısayol yok)" in p.dugme_bolge.text()
    finally:
        p.kapat()


def test_k5_cakisma_diger_kisayol_calisir(sahte: SahteWin32, servis: KisayolServisi, quit_korumasi: None) -> None:
    sahte.reddet[(CA, ord("D"))] = 1409
    p, _ = _kur(servis)
    try:
        bolge: list[int] = []
        p.bolge_izle_istendi.connect(lambda: bolge.append(1))
        servis.tetiklendi.emit("bolge_izle")
        assert bolge == [1]
    finally:
        p.kapat()


def test_k5_kayit_sonucu_sebep_tablosu_tum_uyeler() -> None:
    for sonuc in KayitSonucu:
        if sonuc is KayitSonucu.OK:
            continue
        assert uygulama.kayit_sebebi(sonuc, 1409) != ""
    assert uygulama.kayit_sebebi(KayitSonucu.CAKISMA, 1409) == "başka bir uygulama kullanıyor"
    assert uygulama.kayit_sebebi(KayitSonucu.ALTGR_CAKISMA, 0) == "bu klavye düzeninde AltGr ile çakışıyor"
    assert uygulama.kayit_sebebi(KayitSonucu.GECERSIZ, 0) == "geçersiz kombinasyon"
    assert "87" in uygulama.kayit_sebebi(KayitSonucu.HATA, 87)
    assert uygulama.kayit_sebebi(KayitSonucu.OK, 0) == ""
