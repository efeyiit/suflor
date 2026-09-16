"""T-013 Tester-B (kor) -- mercek: kotu kullanim + sartname v2 uyumu + test kalitesi (offscreen bolumu).

pytest-qt, offscreen, `SUFLOR_GERCEK_KISAYOL_YASAK=1` (conftest). Gercek Windows sondalari ayri surec: `sonda_*.py`.
Bolumler:
  A  kotu kullanim (servis): ad yeniden kaydi baska adin kombinasyonuna, sonuc yok sayma, ayni kombinasyon iki ada,
     bilinmeyen ad, dinleyici istisnasi, ebeveynsiz/ebeveynli referans dusurme, `deleteLater` + referans (O-B5 sinifi),
     `calistir` x2 ayni surec, servis yeniden kullanimi
  B  sartname v2 <-> kod satir satir: arayuz, K1 durum makinesi + kimlik, K2 filtre, K3 dilbilgisi (bagimsiz tablo),
     AltGr, K5 metinler, K6 AST + thread
  C  kabuk etiketleri / kullanici istegi: dugme metinleri, tepsi ipucu, durum satiri, cikis kodu, ozel `kisayollar`
Sahte Win32 (`SahteWin32`) gercek `RegisterHotKey`in surec-disi davranisini taklit eder: ayni (mod, vk) ikinci kayit
`False` + 1409 -- sahte, servislerin ARASINDA paylasilir (OS gibi). Beklentiler paket v2 / docstring lafzindan literal;
ozel mekanizma kancalanmaz (§4.6/7); referanslar uygulamadan turetilmez (§4.6/8).
"""
from __future__ import annotations

import ast
import ctypes
import gc
import threading
import weakref
from collections.abc import Iterator
from ctypes import wintypes
from pathlib import Path

import pytest
from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import QByteArray

from src.ui import kisayol as km
from src.ui.kabuk import AnaPencere, KabukDurumu
from src.ui.kisayol import (
    MOD_ALT,
    MOD_CONTROL,
    MOD_NOREPEAT,
    MOD_SHIFT,
    WM_HOTKEY,
    GecersizKombinasyon,
    KayitSonucu,
    KisayolServisi,
    kombinasyonu_coz,
    kombinasyonu_yaz,
)
from src.ui.uygulama import VARSAYILAN_KISAYOLLAR, calistir, kayit_sebebi

KOK = Path(__file__).resolve().parents[4]
UI = KOK / "src" / "ui"
OLAY_TIPI = QByteArray(b"windows_generic_MSG")
CA = MOD_CONTROL | MOD_ALT
DEVAM = "Pencere düğmeleri ve tepsi menüsü çalışmaya devam eder."
KISAYOL_YOK = "(kısayol yok)"


class SahteWin32:
    """OS'un kayit tablosunu taklit eder: (mod, vk) dolu ise `False` + 1409. `dolu` = 'baska surec' tutuyor."""

    def __init__(self, dolu: set[tuple[int, int]] | None = None, hata: int = 1409) -> None:
        self.kayitlar: list[tuple[int, int, int]] = []
        self.kaldirilar: list[int] = []
        self.dolu: set[tuple[int, int]] = set(dolu or ())
        self.hata = hata
        self.tutulan: dict[int, tuple[int, int]] = {}
        self.altgr: dict[int, str] = {}
        self.altgr_sorgulari: list[int] = []
        self.son_hata = 0

    def kayit(self, kimlik: int, mod: int, vk: int) -> bool:
        self.kayitlar.append((kimlik, mod, vk))
        anahtar = (mod & ~MOD_NOREPEAT, vk)
        if anahtar in self.dolu or anahtar in self.tutulan.values() or kimlik in self.tutulan:
            self.son_hata = self.hata
            return False
        self.tutulan[kimlik] = anahtar
        return True

    def kaldir(self, kimlik: int) -> bool:
        self.kaldirilar.append(kimlik)
        return self.tutulan.pop(kimlik, None) is not None

    def hata_kodu(self) -> int:
        return self.son_hata

    def altgr_karakteri(self, vk: int) -> str:
        self.altgr_sorgulari.append(vk)
        return self.altgr.get(vk, "")

    def servis(self, ebeveyn: QtCore.QObject | None = None) -> KisayolServisi:
        return KisayolServisi(ebeveyn, kayit_fn=self.kayit, kaldir_fn=self.kaldir, hata_kodu_fn=self.hata_kodu,
                              altgr_karakteri_fn=self.altgr_karakteri)


def mesaj(kimlik: int, message: int = WM_HOTKEY) -> wintypes.MSG:
    m = wintypes.MSG()
    m.message = message
    m.wParam = kimlik
    return m


def ates(servis: KisayolServisi, kimlik: int) -> tuple[bool, int]:
    m = mesaj(kimlik)
    return servis.filtre.nativeEventFilter(OLAY_TIPI, ctypes.addressof(m))


def kimlik_of(sahte: SahteWin32, mod: int, vk: int) -> int:
    return next(k for k, (m, v) in sahte.tutulan.items() if (m, v) == (mod, vk))


@pytest.fixture
def sahte(qapp: QtWidgets.QApplication) -> SahteWin32:
    return SahteWin32()


@pytest.fixture
def pencereler(qapp: QtWidgets.QApplication) -> Iterator[list[AnaPencere]]:
    liste: list[AnaPencere] = []
    yield liste
    for p in liste:
        p.kapat()
        p.deleteLater()


def kur(sahte: SahteWin32, pencereler: list[AnaPencere], kisayollar: dict[str, str] | None = None,
        cikis: int = 0) -> tuple[AnaPencere, KisayolServisi, int]:
    tutulan: dict[str, object] = {}
    servis = sahte.servis()

    def calistirici(app: QtWidgets.QApplication, pencere: AnaPencere) -> int:
        tutulan["p"] = pencere
        return cikis

    rc = calistir([], calistirici=calistirici, kisayollar=kisayollar, kisayol_servisi=servis)
    p = tutulan["p"]
    assert isinstance(p, AnaPencere)
    pencereler.append(p)
    return p, servis, rc


# =====================================================================================================
# A -- kotu kullanim
# =====================================================================================================
class TestA_KotuKullanim:
    def test_a1_ayni_ad_baska_adin_kombinasyonuna_yeniden_kayit_eski_kayit_kaybolur(self, sahte: SahteWin32) -> None:
        """Docstring K1 (5): 'ayni kombinasyon baska ad -> CAKISMA, Win32 CAGRILMAZ'; (4) once eski kayit kaldirilir.
        Olcu: b=R kayitliyken kaydet(b, D) -> CAKISMA ama b'nin R kaydi da GITTI (kaldir_fn cagrildi)."""
        s = sahte.servis()
        assert s.kaydet("a", "Ctrl+Alt+D") is KayitSonucu.OK
        assert s.kaydet("b", "Ctrl+Alt+R") is KayitSonucu.OK
        n_kaldir = len(sahte.kaldirilar)
        sonuc = s.kaydet("b", "Ctrl+Alt+D")
        assert sonuc is KayitSonucu.CAKISMA
        # OLCULEN davranis (bulgu): b'nin R kaydi kayboldu, Win32 kaldir CAGRILDI
        assert "b" not in s.kayitli()
        assert len(sahte.kaldirilar) == n_kaldir + 1
        assert (CA, ord("R")) not in sahte.tutulan.values()

    @pytest.mark.xfail(strict=True, reason="BULGU: docstring 'Win32 CAGRILMAZ' / 'gecersiz yeni kombinasyon eski kaydi bozmaz' -- servis ici CAKISMA yolunda eski kayit KAYBOLUYOR")
    def test_a1b_servis_ici_cakisma_eski_kaydi_korumali_docstring_lafzi(self, sahte: SahteWin32) -> None:
        s = sahte.servis()
        s.kaydet("a", "Ctrl+Alt+D")
        s.kaydet("b", "Ctrl+Alt+R")
        n_kaldir = len(sahte.kaldirilar)
        assert s.kaydet("b", "Ctrl+Alt+D") is KayitSonucu.CAKISMA
        assert s.kayitli() == {"a": "Ctrl+Alt+D", "b": "Ctrl+Alt+R"}
        assert len(sahte.kaldirilar) == n_kaldir

    def test_a1c_ayni_ad_gecersiz_ve_altgr_yeni_kombinasyon_eski_kaydi_korur(self, sahte: SahteWin32) -> None:
        sahte.altgr[ord("T")] = "₺"
        s = sahte.servis()
        assert s.kaydet("a", "Ctrl+Alt+D") is KayitSonucu.OK
        n = len(sahte.kaldirilar)
        assert s.kaydet("a", "Shift+T") is KayitSonucu.GECERSIZ
        assert s.kaydet("a", "Ctrl+Alt+T") is KayitSonucu.ALTGR_CAKISMA
        assert s.kaydet("a", "bozuk metin") is KayitSonucu.GECERSIZ
        assert s.kayitli() == {"a": "Ctrl+Alt+D"}
        assert len(sahte.kaldirilar) == n

    def test_a1d_ayni_ad_win32_1409_sonrasi_eski_kayit_geri_gelmez_belgeli(self, sahte: SahteWin32) -> None:
        """Docstring: 'Win32 1409 SONRASI eski kayit geri GELMEZ' -- belgeli davranis olculdu (v2 geri alma)."""
        sahte.dolu.add((CA, ord("X")))
        s = sahte.servis()
        assert s.kaydet("a", "Ctrl+Alt+D") is KayitSonucu.OK
        assert s.kaydet("a", "Ctrl+Alt+X") is KayitSonucu.CAKISMA
        assert s.son_hata_kodu == 1409
        assert s.kayitli() == {}
        assert sahte.tutulan == {}

    def test_a2_kaydet_sonucu_yok_sayilirsa_kayitli_ve_etiket_dogru_soyler(self, sahte: SahteWin32, pencereler: list[AnaPencere]) -> None:
        sahte.dolu.add((CA, ord("D")))
        p, s, _ = kur(sahte, pencereler)
        assert s.kayitli() == {"bolge_izle": "Ctrl+Alt+R"}
        assert KISAYOL_YOK in p.dugme_anlik.text()
        assert "Ctrl+Alt+R" in p.dugme_bolge.text()

    def test_a3_kisayollar_ayni_kombinasyon_iki_ada_ikincisi_cakisma_ilki_calisir(self, sahte: SahteWin32, pencereler: list[AnaPencere]) -> None:
        p, s, _ = kur(sahte, pencereler, {"anlik_cevir": "Ctrl+Alt+D", "bolge_izle": "Ctrl+Alt+D"})
        assert s.kayitli() == {"anlik_cevir": "Ctrl+Alt+D"}
        assert len(sahte.kayitlar) == 1  # ikinci Win32'ye gitmedi (servis ici)
        metin = p.durum_metni()
        assert metin.startswith("Ctrl+Alt+D kaydedilemedi: başka bir uygulama kullanıyor")
        assert KISAYOL_YOK in p.dugme_bolge.text() and "Ctrl+Alt+D" in p.dugme_anlik.text()
        sayac: list[int] = []
        p.anlik_cevir_istendi.connect(lambda: sayac.append(1))
        assert ates(s, kimlik_of(sahte, CA, ord("D"))) == (True, 0)
        assert sayac == [1]

    def test_a4_bilinmeyen_ad_kaydedilir_ama_gorunmez_ve_alicisiz(self, sahte: SahteWin32, pencereler: list[AnaPencere]) -> None:
        """Kotu kullanim: `kisayollar={"foo": ...}` -> kombinasyon Win32'de ALINIR (sistem genelinde yutulur), hicbir dugme/
        ipucu/durum satiri gostermez, sinyal yok. Olculen davranis (bulgu, dusuk)."""
        p, s, _ = kur(sahte, pencereler, {"foo": "Ctrl+Alt+X"})
        assert s.kayitli() == {"foo": "Ctrl+Alt+X"}
        assert (CA, ord("X")) in sahte.tutulan.values()
        assert p.durum_metni() == ""
        assert KISAYOL_YOK in p.dugme_anlik.text() and KISAYOL_YOK in p.dugme_bolge.text()
        assert "Ctrl+Alt+X" not in p.tepsi.ikon.toolTip()
        sayac: list[int] = []
        p.anlik_cevir_istendi.connect(lambda: sayac.append(1))
        p.bolge_izle_istendi.connect(lambda: sayac.append(2))
        assert ates(s, kimlik_of(sahte, CA, ord("X"))) == (True, 0)  # olay YUTULDU
        assert sayac == []

    @pytest.mark.qt_no_exception_capture
    def test_a5_dinleyici_istisna_atarsa_filtre_true_doner_sonraki_olaylar_gelir_stderr_metin(self, sahte: SahteWin32, capfd: pytest.CaptureFixture[str]) -> None:
        """Qt istisnayi yutar ve stderr'e basar (KRT U5): servis kendisi yazmaz; ikinci olay hala gelir.
        (pytest-qt'nin istisna yakalayicisi kapali: uretimdeki davranis olculur.)"""
        s = sahte.servis()
        s.kaydet("a", "Ctrl+Alt+D")
        kimlik = kimlik_of(sahte, CA, ord("D"))
        sayac: list[int] = []

        def patlak(ad: str) -> None:
            sayac.append(1)
            raise RuntimeError("dinleyici patladi")

        s.tetiklendi.connect(patlak)
        capfd.readouterr()
        assert ates(s, kimlik) == (True, 0)
        assert ates(s, kimlik) == (True, 0)
        assert sayac == [1, 1]
        err = capfd.readouterr().err
        assert "dinleyici patladi" in err  # Qt/PySide stderr'e yazdi -- K6 'metin yok' servisin degil PySide'in davranisi (belge)

    def test_a6_ebeveynsiz_servis_referans_dusunce_kayitlar_kalkar(self, sahte: SahteWin32) -> None:
        s = sahte.servis()
        s.kaydet("a", "Ctrl+Alt+D")
        s.kaydet("b", "Ctrl+Alt+R")
        kimlikler = set(sahte.tutulan)
        wr = weakref.ref(s)
        del s
        gc.collect()
        assert wr() is None
        assert set(sahte.kaldirilar) >= kimlikler
        assert sahte.tutulan == {}

    def test_a6b_ebeveynli_servis_python_referansi_dusunce_kayit_ve_sinyal_yasar(self, sahte: SahteWin32, qtbot) -> None:
        """`calistir` deseni: `KisayolServisi(pencere, ...)` yerel degiskeni `calistir` donunce duser. Filtre servise weakref
        ile ulasir -> sarmalayici olurse kayit yasar ama sinyal YAYILMAZ (sessiz yutma). Olcu: sarmalayici ebeveyn yasadikca yasar."""
        ebeveyn = QtWidgets.QWidget()
        qtbot.addWidget(ebeveyn)
        s = sahte.servis(ebeveyn)
        s.kaydet("a", "Ctrl+Alt+D")
        kimlik = kimlik_of(sahte, CA, ord("D"))
        sayac: list[str] = []
        s.tetiklendi.connect(sayac.append)
        filtre = s.filtre
        wr = weakref.ref(s)
        del s
        gc.collect()
        assert wr() is not None, "ebeveynli servis sarmalayicisi oldu: kayit yasiyor, sinyal yayilamaz"
        m = mesaj(kimlik)
        assert filtre.nativeEventFilter(OLAY_TIPI, ctypes.addressof(m)) == (True, 0)
        assert sayac == ["a"]
        assert sahte.tutulan  # kayit hala Win32'de

    def test_a6c_ebeveyn_silinince_cocuk_servis_temizler(self, sahte: SahteWin32, qtbot) -> None:
        ebeveyn = QtWidgets.QWidget()
        s = sahte.servis(ebeveyn)
        s.kaydet("a", "Ctrl+Alt+D")
        s.kaydet("b", "Ctrl+Alt+R")
        kimlikler = set(sahte.tutulan)
        ebeveyn.deleteLater()
        qtbot.wait(50)
        assert set(sahte.kaldirilar) >= kimlikler and sahte.tutulan == {}

    def test_a6d_deleteLater_referans_tutulurken_kayitlar_kalkar_ob5_sinifi(self, sahte: SahteWin32, qtbot) -> None:
        """T-012 O-B5 sinifi: `deleteLater()` + Python referansi tutulur -> C++ olur; temizleyici `self`siz oldugu icin KOSMALI."""
        s = sahte.servis()
        s.kaydet("a", "Ctrl+Alt+D")
        kimlikler = set(sahte.tutulan)
        s.deleteLater()
        qtbot.wait(50)
        assert sahte.tutulan == {} and set(sahte.kaldirilar) >= kimlikler
        del s
        gc.collect()
        assert len(sahte.kaldirilar) == len(kimlikler)  # cift kaldirma yok

    def test_a6f_yikim_canli_kimlikleri_serbest_birakir(self, sahte: SahteWin32) -> None:
        """Yikim temizleyicisi kimlikleri surec genelindeki canli kumeden de dusurmeli (aksi halde her servis omru
        1..0xBFFF araligindan kimlik sizdirir; MB4)."""
        canli0 = len(km._canli_kimlikler)
        s = sahte.servis()
        s.kaydet("a", "Ctrl+Alt+D")
        s.kaydet("b", "Ctrl+Alt+R")
        assert len(km._canli_kimlikler) == canli0 + 2
        del s
        gc.collect()
        assert len(km._canli_kimlikler) == canli0

    def test_a6e_hepsini_kaldir_sonrasi_yikim_cift_kaldirma_yapmaz(self, sahte: SahteWin32) -> None:
        s = sahte.servis()
        s.kaydet("a", "Ctrl+Alt+D")
        s.hepsini_kaldir()
        assert len(sahte.kaldirilar) == 1
        del s
        gc.collect()
        assert len(sahte.kaldirilar) == 1

    def test_a7_calistir_iki_kez_ilk_pencere_acikken_ikincisi_cakisma_kapatinca_alinir(self, sahte: SahteWin32, pencereler: list[AnaPencere]) -> None:
        """Ayni surecte iki `calistir` (gercek: iki servis, ayni OS tablosu): ikinci pencere iki kombinasyonu da 'baska bir
        uygulama' diye bildirir (kendimiziz ama mekanizma ayiramaz); ilk `kapat()` -> ucuncu calistir alir."""
        p1, s1, _ = kur(sahte, pencereler)
        p2, s2, _ = kur(sahte, pencereler)
        assert s1.kayitli() == dict(VARSAYILAN_KISAYOLLAR)
        assert s2.kayitli() == {}
        assert s2.son_hata_kodu == 1409
        m = p2.durum_metni()
        assert "Ctrl+Alt+D kaydedilemedi: başka bir uygulama kullanıyor" in m and "Ctrl+Alt+R kaydedilemedi" in m
        assert m.endswith(". " + DEVAM) and m.count(DEVAM) == 1
        assert KISAYOL_YOK in p2.dugme_anlik.text() and KISAYOL_YOK in p2.dugme_bolge.text()
        p1.kapat()
        assert s1.kayitli() == {} and sahte.tutulan == {}
        p3, s3, _ = kur(sahte, pencereler)
        assert s3.kayitli() == dict(VARSAYILAN_KISAYOLLAR) and p3.durum_metni() == ""

    def test_a7b_ayni_servis_iki_calistir_cift_dagitim(self, sahte: SahteWin32, pencereler: list[AnaPencere]) -> None:
        """Kotu kullanim: ayni servis nesnesi iki `calistir`a verilirse `tetiklendi` her iki pencereye baglanir -> bir basis
        iki sinyal (ilk pencere `kapat()` edilse de yayar: kabuk docstring 'kapat() sonrasi da yayar')."""
        servis = sahte.servis()
        tutulan: list[AnaPencere] = []

        def c(app: QtWidgets.QApplication, pencere: AnaPencere) -> int:
            tutulan.append(pencere)
            return 0

        calistir([], calistirici=c, kisayol_servisi=servis)
        calistir([], calistirici=c, kisayol_servisi=servis)
        pencereler.extend(tutulan)
        assert servis.kayitli() == dict(VARSAYILAN_KISAYOLLAR)  # ayni ad yeniden kayit: kaldir + kaydet
        assert len(sahte.kayitlar) == 4 and len(sahte.kaldirilar) == 2
        sayac: list[int] = []
        tutulan[0].anlik_cevir_istendi.connect(lambda: sayac.append(1))
        tutulan[1].anlik_cevir_istendi.connect(lambda: sayac.append(2))
        tutulan[0].kapat()
        servis.tetiklendi.emit("anlik_cevir")
        assert sorted(sayac) == [1, 2]

    def test_a8_kaldir_bilinmeyen_sessiz_hepsini_kaldir_idempotent_bos_serviste(self, sahte: SahteWin32) -> None:
        s = sahte.servis()
        s.kaldir("yok")
        s.hepsini_kaldir()
        s.hepsini_kaldir()
        assert sahte.kaldirilar == [] and sahte.kayitlar == []
        assert s.kayitli() == {}

    def test_a9_kayitli_kopyasi_disaridan_degistirilemez(self, sahte: SahteWin32) -> None:
        s = sahte.servis()
        s.kaydet("a", "Ctrl+Alt+D")
        k = s.kayitli()
        k["a"] = "Ctrl+Alt+Z"
        k["b"] = "Ctrl+Alt+R"
        assert s.kayitli() == {"a": "Ctrl+Alt+D"}

    def test_a10_altgr_fn_istisna_atarsa_kaydet_istisnayi_gecirir_win32_cagrilmaz(self, qapp: QtWidgets.QApplication) -> None:
        """Enjekte fn patlarsa servis onu yutmaz (gercek `ToUnicodeEx` sarmalayicisi istisna atmaz; sahte icin belge)."""
        kayitlar: list[int] = []

        def patlak(vk: int) -> str:
            raise OSError("duzen yok")

        s = KisayolServisi(kayit_fn=lambda i, m, v: kayitlar.append(i) or True, kaldir_fn=lambda i: True,
                           hata_kodu_fn=lambda: 0, altgr_karakteri_fn=patlak)
        with pytest.raises(OSError):
            s.kaydet("a", "Ctrl+Alt+D")
        assert kayitlar == [] and s.kayitli() == {}

    def test_a11_bos_ad_kabul_edilir_kabukta_yok_sayilir(self, sahte: SahteWin32, pencereler: list[AnaPencere]) -> None:
        p, s, _ = kur(sahte, pencereler, {"": "Ctrl+Alt+X"})
        assert s.kayitli() == {"": "Ctrl+Alt+X"}
        sayac: list[int] = []
        p.anlik_cevir_istendi.connect(lambda: sayac.append(1))
        ates(s, kimlik_of(sahte, CA, ord("X")))
        assert sayac == []


# =====================================================================================================
# B -- sartname v2 <-> kod
# =====================================================================================================
class TestB_Arayuz:
    def test_b1_kayit_sonucu_uyeleri_ve_strenum(self) -> None:
        assert [m.name for m in KayitSonucu] == ["OK", "CAKISMA", "ALTGR_CAKISMA", "GECERSIZ", "HATA"]
        assert all(isinstance(m, str) for m in KayitSonucu)

    def test_b1b_yapici_imzasi_yalniz_anahtar_sozcuklu(self, sahte: SahteWin32) -> None:
        with pytest.raises(TypeError):
            KisayolServisi(None, False, sahte.kayit)  # type: ignore[misc]
        s = KisayolServisi(None, gercek_win32=False, kayit_fn=sahte.kayit, kaldir_fn=sahte.kaldir,
                           hata_kodu_fn=sahte.hata_kodu, altgr_karakteri_fn=sahte.altgr_karakteri)
        assert s.son_hata_kodu == 0 and s.kayitli() == {}
        assert KisayolServisi.kombinasyonu_coz("Ctrl+Alt+D") == (CA, ord("D"))

    @pytest.mark.parametrize("eksik", ["kayit_fn", "kaldir_fn", "hata_kodu_fn", "altgr_karakteri_fn"])
    def test_b1c_gercek_win32_false_fn_eksikse_runtimeerror_adiyla(self, sahte: SahteWin32, eksik: str) -> None:
        fnler = {"kayit_fn": sahte.kayit, "kaldir_fn": sahte.kaldir, "hata_kodu_fn": sahte.hata_kodu, "altgr_karakteri_fn": sahte.altgr_karakteri}
        fnler.pop(eksik)
        with pytest.raises(RuntimeError, match=eksik):
            KisayolServisi(**fnler)  # type: ignore[arg-type]

    def test_b1d_yasak_degiskeni_varken_gercek_win32_true_runtimeerror_fnler_verilse_de(self, sahte: SahteWin32, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SUFLOR_GERCEK_KISAYOL_YASAK", "1")
        with pytest.raises(RuntimeError, match="SUFLOR_GERCEK_KISAYOL_YASAK"):
            KisayolServisi(gercek_win32=True, kayit_fn=sahte.kayit, kaldir_fn=sahte.kaldir, hata_kodu_fn=sahte.hata_kodu,
                           altgr_karakteri_fn=sahte.altgr_karakteri)
        assert sahte.kayitlar == []
        # pozitif kontrol: degisken yokken fn'ler verilmisse kurulur ve gercek Win32'ye DOKUNMAZ
        monkeypatch.delenv("SUFLOR_GERCEK_KISAYOL_YASAK")
        s = KisayolServisi(gercek_win32=True, kayit_fn=sahte.kayit, kaldir_fn=sahte.kaldir, hata_kodu_fn=sahte.hata_kodu,
                           altgr_karakteri_fn=sahte.altgr_karakteri)
        assert s.kaydet("a", "Ctrl+Alt+D") is KayitSonucu.OK and len(sahte.kayitlar) == 1
        s.hepsini_kaldir()

    def test_b1e_calistir_kisayol_servisi_verilmezse_yasak_altinda_runtimeerror(self, qapp: QtWidgets.QApplication) -> None:
        with pytest.raises(RuntimeError, match="SUFLOR_GERCEK_KISAYOL_YASAK"):
            calistir([], calistirici=lambda app, p: 0)

    def test_b1f_calistir_imzasi_anahtar_sozcuklu(self, sahte: SahteWin32) -> None:
        with pytest.raises(TypeError):
            calistir([], None, lambda a, p: 0)  # type: ignore[misc]


class TestB_K1_DurumMakinesi:
    def test_b2_kaydet_ok_cagri_dizisi_norepeat_ve_hwnd_yok(self, sahte: SahteWin32) -> None:
        s = sahte.servis()
        assert s.kaydet("a", "Ctrl+Alt+D") is KayitSonucu.OK
        (kimlik, mod, vk), = sahte.kayitlar
        assert mod == CA | MOD_NOREPEAT and vk == ord("D") and 1 <= kimlik <= 0xBFFF
        assert s.son_hata_kodu == 0
        assert s.kayitli() == {"a": "Ctrl+Alt+D"}

    def test_b2b_ayni_ad_yeniden_once_kaldir_sonra_kaydet_yeni_kimlik(self, sahte: SahteWin32) -> None:
        s = sahte.servis()
        s.kaydet("a", "Ctrl+Alt+D")
        k1 = sahte.kayitlar[0][0]
        assert s.kaydet("a", "Ctrl+Alt+R") is KayitSonucu.OK
        assert sahte.kaldirilar == [k1]
        k2 = sahte.kayitlar[1][0]
        assert k2 != k1 and s.kayitli() == {"a": "Ctrl+Alt+R"}
        # sira: kaldir, sonra kayit (sahte tablosunda D yok, R var)
        assert list(sahte.tutulan.values()) == [(CA, ord("R"))]

    def test_b2c_1409_cakisma_kayitlida_yok_son_hata_1409(self, sahte: SahteWin32) -> None:
        sahte.dolu.add((CA, ord("D")))
        s = sahte.servis()
        assert s.kaydet("a", "Ctrl+Alt+D") is KayitSonucu.CAKISMA
        assert s.son_hata_kodu == 1409 and s.kayitli() == {}
        assert s.kaydet("b", "Ctrl+Alt+R") is KayitSonucu.OK and s.son_hata_kodu == 0

    def test_b2d_diger_hata_kodu_hata(self, sahte: SahteWin32) -> None:
        sahte.dolu.add((CA, ord("D")))
        sahte.hata = 5
        s = sahte.servis()
        assert s.kaydet("a", "Ctrl+Alt+D") is KayitSonucu.HATA and s.son_hata_kodu == 5
        assert kayit_sebebi(KayitSonucu.HATA, 5) == "Windows hata kodu 5"

    def test_b2e_kaldir_yalniz_kendi_kimligi_hepsini_kaldir_idempotent(self, sahte: SahteWin32) -> None:
        s = sahte.servis()
        s.kaydet("a", "Ctrl+Alt+D")
        s.kaydet("b", "Ctrl+Alt+R")
        ka = kimlik_of(sahte, CA, ord("D"))
        s.kaldir("a")
        assert sahte.kaldirilar == [ka] and s.kayitli() == {"b": "Ctrl+Alt+R"}
        s.hepsini_kaldir()
        s.hepsini_kaldir()
        assert len(sahte.kaldirilar) == 2 and s.kayitli() == {} and sahte.tutulan == {}

    def test_b2f_iki_servis_kimlik_kumeleri_ayrik_ve_kaldir_yalniz_kendininki(self, sahte: SahteWin32) -> None:
        s1, s2 = sahte.servis(), sahte.servis()
        s1.kaydet("a", "Ctrl+Alt+D")
        s2.kaydet("a", "Ctrl+Alt+R")
        s1.kaydet("b", "Ctrl+Alt+X")
        k1 = {k for k, _, _ in sahte.kayitlar if k in sahte.tutulan and sahte.tutulan[k] != (CA, ord("R"))}
        k2 = {k for k, _, _ in sahte.kayitlar if sahte.tutulan.get(k) == (CA, ord("R"))}
        assert k1.isdisjoint(k2) and len(k1) == 2 and len(k2) == 1
        s1.hepsini_kaldir()
        assert set(sahte.kaldirilar) == k1
        assert s2.kayitli() == {"a": "Ctrl+Alt+R"}
        s2.hepsini_kaldir()

    def test_b2g_iki_servis_ayni_kombinasyon_ikincisi_win32_1409(self, sahte: SahteWin32) -> None:
        """Servis ici degil servisler arasi: Win32'ye gider, OS 1409 verir -> CAKISMA (gercek ile ayni sinif)."""
        s1, s2 = sahte.servis(), sahte.servis()
        assert s1.kaydet("a", "Ctrl+Alt+D") is KayitSonucu.OK
        assert s2.kaydet("a", "Ctrl+Alt+D") is KayitSonucu.CAKISMA and s2.son_hata_kodu == 1409
        assert len(sahte.kayitlar) == 2
        s1.hepsini_kaldir()
        assert s2.kaydet("a", "Ctrl+Alt+D") is KayitSonucu.OK
        s2.hepsini_kaldir()

    def test_b2h_basarisiz_kaydin_kimligi_yeniden_kullanilabilir(self, sahte: SahteWin32) -> None:
        """Basarisiz kayit kimligi canli sayilmamali: 1409 sonrasi bir sonraki OK kayit ayni kimligi alabilir ya da
        ardisik -- olcu: canli kimlik sayisi kayitli sayisina esit (sizinti yok)."""
        sahte.dolu.add((CA, ord("D")))
        s = sahte.servis()
        canli0 = len(km._canli_kimlikler)
        for _ in range(50):
            assert s.kaydet("a", "Ctrl+Alt+D") is KayitSonucu.CAKISMA
        assert len(km._canli_kimlikler) == canli0, "basarisiz kayit kimligi canli kumesinde kaldi (sizinti; MB2)"
        assert s.kaydet("b", "Ctrl+Alt+R") is KayitSonucu.OK
        assert len(sahte.tutulan) == 1 and len(km._canli_kimlikler) == canli0 + 1
        s.hepsini_kaldir()
        assert len(km._canli_kimlikler) == canli0


class TestB_K2_Filtre:
    def test_b3_bilinen_kimlik_sinyal_ve_true(self, sahte: SahteWin32) -> None:
        s = sahte.servis()
        s.kaydet("a", "Ctrl+Alt+D")
        s.kaydet("b", "Ctrl+Alt+R")
        alinan: list[str] = []
        s.tetiklendi.connect(alinan.append)
        assert ates(s, kimlik_of(sahte, CA, ord("R"))) == (True, 0)
        assert ates(s, kimlik_of(sahte, CA, ord("D"))) == (True, 0)
        assert alinan == ["b", "a"]

    def test_b3b_bilinmeyen_kimlik_ve_hotkey_disi_false(self, sahte: SahteWin32) -> None:
        s = sahte.servis()
        s.kaydet("a", "Ctrl+Alt+D")
        alinan: list[str] = []
        s.tetiklendi.connect(alinan.append)
        assert ates(s, 0xBFFE) == (False, 0)
        m = mesaj(kimlik_of(sahte, CA, ord("D")), message=0x0100)  # WM_KEYDOWN
        assert s.filtre.nativeEventFilter(OLAY_TIPI, ctypes.addressof(m)) == (False, 0)
        assert alinan == []

    @pytest.mark.parametrize("tip", [QByteArray(b"xcb_generic_event_t"), b"mac_generic_NSEvent", QByteArray(b""), bytearray(b"windows_generic_MSG_"), memoryview(b"windows_dispatcher_MSG")])
    def test_b3c_yanlis_event_type_mesaja_dokunmadan_false(self, sahte: SahteWin32, tip: object) -> None:
        """message=0 (NULL): dokunulsaydi surec olurdu (KRT k9)."""
        s = sahte.servis()
        s.kaydet("a", "Ctrl+Alt+D")
        assert s.filtre.nativeEventFilter(tip, 0) == (False, 0)  # type: ignore[arg-type]

    def test_b3d_event_type_bytes_ve_qbytearray_ikisi_de_calisir(self, sahte: SahteWin32) -> None:
        s = sahte.servis()
        s.kaydet("a", "Ctrl+Alt+D")
        m = mesaj(kimlik_of(sahte, CA, ord("D")))
        assert s.filtre.nativeEventFilter(b"windows_generic_MSG", ctypes.addressof(m)) == (True, 0)
        assert s.filtre.nativeEventFilter(QByteArray(b"windows_generic_MSG"), ctypes.addressof(m)) == (True, 0)

    def test_b3e_kaldirilan_kimlik_artik_bilinmiyor(self, sahte: SahteWin32) -> None:
        s = sahte.servis()
        s.kaydet("a", "Ctrl+Alt+D")
        k = kimlik_of(sahte, CA, ord("D"))
        s.kaldir("a")
        alinan: list[str] = []
        s.tetiklendi.connect(alinan.append)
        assert ates(s, k) == (False, 0) and alinan == []

    def test_b3f_filtre_ayni_nesne_ve_iki_servis_birbirinin_olayini_yutmaz(self, sahte: SahteWin32) -> None:
        s1, s2 = sahte.servis(), sahte.servis()
        assert s1.filtre is s1.filtre and s1.filtre is not s2.filtre
        s1.kaydet("a", "Ctrl+Alt+D")
        s2.kaydet("b", "Ctrl+Alt+R")
        k1, k2 = kimlik_of(sahte, CA, ord("D")), kimlik_of(sahte, CA, ord("R"))
        a1: list[str] = []
        a2: list[str] = []
        s1.tetiklendi.connect(a1.append)
        s2.tetiklendi.connect(a2.append)
        assert ates(s2, k1) == (False, 0)  # yeni servis eski servisin olayini yutmaz
        assert ates(s1, k1) == (True, 0)
        assert ates(s1, k2) == (False, 0)
        assert ates(s2, k2) == (True, 0)
        assert a1 == ["a"] and a2 == ["b"]

    def test_b3g_filtre_servis_oldukten_sonra_sinyal_yaymaz_cokmez(self, sahte: SahteWin32) -> None:
        s = sahte.servis()
        s.kaydet("a", "Ctrl+Alt+D")
        k = kimlik_of(sahte, CA, ord("D"))
        f = s.filtre
        del s
        gc.collect()
        m = mesaj(k)
        assert f.nativeEventFilter(OLAY_TIPI, ctypes.addressof(m)) == (False, 0)  # kimlik tablosu bosaltildi


class TestB_K3_Dilbilgisi:
    GECERLI = {
        "Ctrl+Alt+D": (CA, 0x44), "ctrl + alt + d": (CA, 0x44), "Alt+Ctrl+D": (CA, 0x44), "CONTROL+ALT+r": (CA, 0x52),
        "Ctrl+Shift+T": (MOD_CONTROL | MOD_SHIFT, 0x54), "Alt+Shift+T": (MOD_ALT | MOD_SHIFT, 0x54),
        "Ctrl+Alt+Shift+D": (CA | MOD_SHIFT, 0x44), "Shift+Alt+Ctrl+9": (CA | MOD_SHIFT, 0x39), "Ctrl+Alt+0": (CA, 0x30),
        "Ctrl+Alt+Space": (CA, 0x20), "Ctrl+Shift+Space": (MOD_CONTROL | MOD_SHIFT, 0x20),
        "Ctrl+F1": (MOD_CONTROL, 0x70), "Alt+F11": (MOD_ALT, 0x7A), "Shift+F10": (MOD_SHIFT, 0x79), "Ctrl+Alt+F5": (CA, 0x74),
        "Ctrl+F4": (MOD_CONTROL, 0x73), "Ctrl+Alt+F4": (CA, 0x73), "Ctrl+Alt+Esc": (CA, 0x1B), "Ctrl+Alt+Escape": (CA, 0x1B),
        "Ctrl+Alt+Tab": (CA, 0x09), "Ctrl+Shift+Tab": (MOD_CONTROL | MOD_SHIFT, 0x09), "Alt+Shift+Tab": (MOD_ALT | MOD_SHIFT, 0x09),
        "Ctrl+Alt+Enter": (CA, 0x0D), "Ctrl+Alt+Return": (CA, 0x0D), "Ctrl+Alt+Backspace": (CA, 0x08),
        "Ctrl+Shift+Delete": (MOD_CONTROL | MOD_SHIFT, 0x2E), "Ctrl+Alt+Del": (CA, 0x2E) if False else None,
        "Ctrl+Alt+Shift+Delete": (CA | MOD_SHIFT, 0x2E), "Alt+Shift+Del": (MOD_ALT | MOD_SHIFT, 0x2E),
        "Ctrl+Alt+Insert": (CA, 0x2D), "Ctrl+Alt+Ins": (CA, 0x2D), "Ctrl+Alt+Home": (CA, 0x24), "Ctrl+Alt+End": (CA, 0x23),
        "Ctrl+Alt+PageUp": (CA, 0x21), "Ctrl+Alt+PgUp": (CA, 0x21), "Ctrl+Alt+PageDown": (CA, 0x22), "Ctrl+Alt+PgDn": (CA, 0x22),
        "Ctrl+Alt+Left": (CA, 0x25), "Ctrl+Alt+Up": (CA, 0x26), "Ctrl+Alt+Right": (CA, 0x27), "Ctrl+Alt+Down": (CA, 0x28),
        "Ctrl+Alt+Shift+Esc": (CA | MOD_SHIFT, 0x1B), "Alt+Shift+F4": (MOD_ALT | MOD_SHIFT, 0x73), "Alt+Shift+Esc": (MOD_ALT | MOD_SHIFT, 0x1B),
        "Ctrl+Alt+F": (CA, 0x46), "Ctrl+Alt+f": (CA, 0x46),
    }
    GECERSIZ = [
        "Win+D", "Meta+D", "Windows+D", "Super+D", "Ctrl+Win+D", "Win+Shift+S",
        "F12", "Ctrl+F12", "Ctrl+Alt+F12", "Ctrl+Alt+Shift+F12",
        "Shift+T", "Ctrl+C", "Alt+D", "Ctrl+D", "Shift+Space", "Ctrl+Space", "Alt+Space", "T", "Space", "Ctrl+1", "Shift+9",
        "Alt+Tab", "Alt+F4", "Alt+Esc", "Alt+Escape", "Ctrl+Esc", "Ctrl+Alt+Delete", "Ctrl+Alt+Del", "Ctrl+Shift+Esc",
        "Ctrl+Tab", "Alt+Enter", "Ctrl+Enter", "Shift+Tab", "Alt+Left", "Ctrl+Backspace", "Shift+Delete", "Alt+Home", "F1", "Esc", "Tab",
    ]
    BOZUK = ["", "+", "Ctrl+", "+D", "Ctrl+Alt+", "Ctrl+Alt+D+R", "Ctrl+Ctrl+D", "Ctrl+Control+D", "Ctrl+Alt", "Alt", "Ctrl+Alt+F0",
             "Ctrl+Alt+F13", "Ctrl+Alt+Numpad0", "Ctrl+Alt+PrintScreen", "Ctrl+Alt+Ş", "Ctrl+Alt+₺", "Ctrl-Alt-D", "Ctrl Alt D",
             "Ctrl+Alt+DD", "Ctrl+Alt+d+", "Ctrl+Alt+ ", "Ctrl+Alt+F14"]

    @pytest.mark.parametrize("metin,beklenen", [(m, b) for m, b in GECERLI.items() if b is not None])
    def test_b4_gecerli_tablo(self, metin: str, beklenen: tuple[int, int]) -> None:
        assert kombinasyonu_coz(metin) == beklenen
        assert not (beklenen[0] & MOD_NOREPEAT)

    @pytest.mark.parametrize("metin", GECERSIZ)
    def test_b4b_gecersiz_tablo_gecersizkombinasyon(self, metin: str) -> None:
        with pytest.raises(GecersizKombinasyon):
            kombinasyonu_coz(metin)

    @pytest.mark.parametrize("metin", BOZUK)
    def test_b4c_bozuk_tablo_duz_valueerror(self, metin: str) -> None:
        with pytest.raises(ValueError) as e:
            kombinasyonu_coz(metin)
        assert not isinstance(e.value, GecersizKombinasyon), metin

    def test_b4d_kanonik_yazim_ve_tersine(self) -> None:
        for metin, beklenen in (("shift+alt+ctrl+d", "Ctrl+Alt+Shift+D"), ("alt+ctrl+r", "Ctrl+Alt+R"), ("ctrl+shift+space", "Ctrl+Shift+Space"),
                                ("alt+shift+pgdn", "Ctrl+Alt+Shift+PageDown".replace("Ctrl+", "")), ("ctrl+f11", "Ctrl+F11"), ("alt+shift+return", "Alt+Shift+Enter")):
            mod, vk = kombinasyonu_coz(metin)
            assert kombinasyonu_yaz(mod, vk) == beklenen
            assert kombinasyonu_coz(beklenen) == (mod, vk)
        with pytest.raises(ValueError):
            kombinasyonu_yaz(0x8 | CA, ord("D"))
        with pytest.raises(ValueError):
            kombinasyonu_yaz(CA, 0x7B)

    def test_b4e_kaydet_gecersiz_ve_bozuk_ikisi_de_gecersiz_win32_ve_altgr_sorulmaz(self, sahte: SahteWin32) -> None:
        s = sahte.servis()
        for m in ("Shift+T", "Win+D", "Alt+F4", "", "Ctrl+Alt+D+R", "Ctrl+Alt+Ş"):
            assert s.kaydet("a", m) is KayitSonucu.GECERSIZ, m
        assert sahte.kayitlar == [] and sahte.altgr_sorgulari == [] and s.son_hata_kodu == 0
        assert kayit_sebebi(KayitSonucu.GECERSIZ, 0) == "geçersiz kombinasyon"

    def test_b4f_kara_liste_tam_esleme_ust_kumeler_serbest(self) -> None:
        """Paket: kara liste tam esleme -> `Ctrl+Alt+Shift+Delete`, `Ctrl+Alt+Tab`, `Alt+Shift+Tab` dilbilgisinden gecer
        (Windows'ta ne olduklari sonda_2 ile olculur)."""
        for m in ("Ctrl+Alt+Shift+Delete", "Ctrl+Alt+Tab", "Alt+Shift+Tab", "Ctrl+Shift+Tab", "Ctrl+Alt+Shift+Esc"):
            kombinasyonu_coz(m)


class TestB_K3_AltGr:
    def test_b5_ctrl_alt_shiftsiz_altgr_dolu_ise_altgr_cakisma_win32_cagrilmaz(self, sahte: SahteWin32) -> None:
        sahte.altgr.update({ord("T"): "₺", ord("S"): "ß", ord("2"): "£", 0x20: "x"})
        s = sahte.servis()
        assert s.kaydet("a", "Ctrl+Alt+T") is KayitSonucu.ALTGR_CAKISMA
        assert s.kaydet("a", "Alt+Ctrl+s") is KayitSonucu.ALTGR_CAKISMA
        assert s.kaydet("a", "Ctrl+Alt+2") is KayitSonucu.ALTGR_CAKISMA
        assert s.kaydet("a", "Ctrl+Alt+Space") is KayitSonucu.ALTGR_CAKISMA
        assert sahte.kayitlar == [] and s.kayitli() == {} and s.son_hata_kodu == 0
        assert sahte.altgr_sorgulari == [ord("T"), ord("S"), ord("2"), 0x20]
        assert s.kaydet("a", "Ctrl+Alt+R") is KayitSonucu.OK and s.kaydet("d", "Ctrl+Alt+D") is KayitSonucu.OK
        assert kayit_sebebi(KayitSonucu.ALTGR_CAKISMA, 0) == "bu klavye düzeninde AltGr ile çakışıyor"

    def test_b5b_shiftli_ve_ctrl_altsiz_kombinasyonda_altgr_sorulmaz(self, sahte: SahteWin32) -> None:
        sahte.altgr[ord("T")] = "₺"
        s = sahte.servis()
        assert s.kaydet("a", "Ctrl+Alt+Shift+T") is KayitSonucu.OK
        assert s.kaydet("b", "Ctrl+Shift+T") is KayitSonucu.OK
        assert s.kaydet("c", "Alt+Shift+T") is KayitSonucu.OK
        assert s.kaydet("d", "Ctrl+F1") is KayitSonucu.OK
        assert sahte.altgr_sorgulari == []
        assert s.kaydet("e", "Ctrl+Alt+F1") is KayitSonucu.OK  # Ctrl+Alt+F: sorulur, bos -> OK
        assert sahte.altgr_sorgulari == [0x70]

    def test_b5c_altgr_karakteri_modul_fonksiyonu_var_ve_pragma_no_cover(self) -> None:
        assert callable(km.altgr_karakteri)
        kaynak = (UI / "kisayol.py").read_text(encoding="utf-8")
        assert "def altgr_karakteri(vk: int) -> str:  # pragma: no cover" in kaynak


class TestB_K5_Metinler:
    def test_b6_cakisma_metni_literal_ve_ayarlardan_yok(self, sahte: SahteWin32, pencereler: list[AnaPencere]) -> None:
        sahte.dolu.add((CA, ord("D")))
        p, s, rc = kur(sahte, pencereler, cikis=7)
        assert rc == 7
        assert p.durum_metni() == "Ctrl+Alt+D kaydedilemedi: başka bir uygulama kullanıyor. " + DEVAM
        assert "ayarlar" not in p.durum_metni().lower()
        assert "Ctrl+Alt+R" in p.dugme_bolge.text() and KISAYOL_YOK in p.dugme_anlik.text()

    def test_b6b_altgr_metni_ve_gecersiz_metni(self, sahte: SahteWin32, pencereler: list[AnaPencere]) -> None:
        sahte.altgr[ord("T")] = "₺"
        p, s, _ = kur(sahte, pencereler, {"anlik_cevir": "Ctrl+Alt+T", "bolge_izle": "Win+R"})
        m = p.durum_metni()
        assert "Ctrl+Alt+T kaydedilemedi: bu klavye düzeninde AltGr ile çakışıyor" in m
        assert "Win+R kaydedilemedi: geçersiz kombinasyon" in m
        assert m.endswith(". " + DEVAM) and "ayarlar" not in m.lower()
        assert KISAYOL_YOK in p.dugme_anlik.text() and KISAYOL_YOK in p.dugme_bolge.text()
        assert sahte.kayitlar == []

    def test_b6c_hata_metni_windows_kodu(self, sahte: SahteWin32, pencereler: list[AnaPencere]) -> None:
        sahte.dolu.add((CA, ord("R")))
        sahte.hata = 87
        p, s, _ = kur(sahte, pencereler)
        assert p.durum_metni() == "Ctrl+Alt+R kaydedilemedi: Windows hata kodu 87. " + DEVAM

    def test_b6d_ast_uygulama_ve_kabukta_modal_yok(self) -> None:
        for dosya in ("uygulama.py", "kabuk.py", "kisayol.py"):
            agac = ast.parse((UI / dosya).read_text(encoding="utf-8"))
            adlar = {n.id for n in ast.walk(agac) if isinstance(n, ast.Name)} | {n.attr for n in ast.walk(agac) if isinstance(n, ast.Attribute)}
            assert not adlar & {"QMessageBox", "QDialog", "QInputDialog", "QErrorMessage"}, dosya
            for n in ast.walk(agac):
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in ("exec", "exec_"):
                    assert dosya == "uygulama.py" and isinstance(n.func.value, ast.Name) and n.func.value.id == "app"

    def test_b6e_basari_durum_satiri_bos_kalir(self, sahte: SahteWin32, pencereler: list[AnaPencere]) -> None:
        p, s, _ = kur(sahte, pencereler)
        assert p.durum_metni() == ""


class TestB_K4_Baglanti:
    @pytest.mark.parametrize("gecis", ["gorunur", "tepsi", "kenar"])
    def test_b7_tetiklendi_uc_durumda_sinyal_durum_degismez(self, sahte: SahteWin32, pencereler: list[AnaPencere], gecis: str, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(AnaPencere, "_balon_gosterildi", True)
        p, s, _ = kur(sahte, pencereler)
        {"gorunur": p.goster, "tepsi": p.tepsiye_al, "kenar": p.kenara_al}[gecis]()
        durum0 = p.durum
        uclu0 = (p.isVisible(), p.sekme.isVisible(), p.tepsi.gorunur())
        a: list[int] = []
        b: list[int] = []
        p.anlik_cevir_istendi.connect(lambda: a.append(1))
        p.bolge_izle_istendi.connect(lambda: b.append(1))
        assert ates(s, kimlik_of(sahte, CA, ord("D"))) == (True, 0)
        assert ates(s, kimlik_of(sahte, CA, ord("R"))) == (True, 0)
        s.tetiklendi.emit("bilinmeyen")
        assert a == [1] and b == [1]
        assert p.durum == durum0 and (p.isVisible(), p.sekme.isVisible(), p.tepsi.gorunur()) == uclu0

    def test_b7b_cikis_istendi_hepsini_kaldirir_ve_cikis_kodu(self, sahte: SahteWin32, pencereler: list[AnaPencere]) -> None:
        p, s, _ = kur(sahte, pencereler)
        kimlikler = set(sahte.tutulan)
        assert len(kimlikler) == 2
        p.kapat()
        assert s.kayitli() == {} and set(sahte.kaldirilar) == kimlikler and sahte.tutulan == {}
        p.kapat()
        assert len(sahte.kaldirilar) == 2

    def test_b7c_calistir_baglantisi_lambda_degil_pencere_toplanabilir(self, sahte: SahteWin32) -> None:
        servis = sahte.servis()
        tutulan: list[weakref.ref[AnaPencere]] = []

        def c(app: QtWidgets.QApplication, pencere: AnaPencere) -> int:
            tutulan.append(weakref.ref(pencere))
            pencere.kapat()
            return 0

        calistir([], calistirici=c, kisayol_servisi=servis)
        gc.collect()
        assert tutulan[0]() is None

    def test_b7d_kisayol_tetiklendi_kapat_sonrasi_da_yayar_diriltmez(self, sahte: SahteWin32, pencereler: list[AnaPencere]) -> None:
        p, s, _ = kur(sahte, pencereler)
        p.kapat()
        a: list[int] = []
        p.anlik_cevir_istendi.connect(lambda: a.append(1))
        p.kisayol_tetiklendi("anlik_cevir")
        assert a == [1] and p.kapandi and not p.isVisible()


class TestB_K6_Thread_AST:
    def test_b8_ast_yasak_adlar_kisayol_ve_uygulama(self) -> None:
        for dosya in ("kisayol.py", "uygulama.py"):
            agac = ast.parse((UI / dosya).read_text(encoding="utf-8"))
            adlar = {n.id for n in ast.walk(agac) if isinstance(n, ast.Name)} | {n.attr for n in ast.walk(agac) if isinstance(n, ast.Attribute)}
            modüller = {a.name.split(".")[0] for n in ast.walk(agac) if isinstance(n, ast.Import) for a in n.names} | {
                (n.module or "").split(".")[0] for n in ast.walk(agac) if isinstance(n, ast.ImportFrom)}
            assert not adlar & {"print", "sleep", "processEvents", "warn", "getLogger", "basicConfig"}, dosya
            assert not modüller & {"logging", "warnings", "time"}, dosya

    @pytest.mark.parametrize("islem", ["kaydet", "kaldir", "hepsini_kaldir"])
    def test_b8b_baska_threadden_runtimeerror_win32_cagrilmaz(self, sahte: SahteWin32, islem: str) -> None:
        s = sahte.servis()
        s.kaydet("a", "Ctrl+Alt+D")
        n_kayit, n_kaldir = len(sahte.kayitlar), len(sahte.kaldirilar)
        sonuc: list[object] = []

        def kos() -> None:
            try:
                if islem == "kaydet":
                    sonuc.append(s.kaydet("b", "Ctrl+Alt+R"))
                elif islem == "kaldir":
                    sonuc.append(s.kaldir("a"))
                else:
                    sonuc.append(s.hepsini_kaldir())
            except BaseException as e:  # noqa: BLE001
                sonuc.append(e)

        t = threading.Thread(target=kos)
        t.start()
        t.join(5)
        assert len(sonuc) == 1 and isinstance(sonuc[0], RuntimeError), sonuc
        assert (len(sahte.kayitlar), len(sahte.kaldirilar)) == (n_kayit, n_kaldir)
        assert s.kayitli() == {"a": "Ctrl+Alt+D"}
        s.hepsini_kaldir()

    def test_b8c_pozitif_kontrol_ana_threadden_ayni_islem_calisir(self, sahte: SahteWin32) -> None:
        s = sahte.servis()
        s.kaydet("a", "Ctrl+Alt+D")
        assert s.kaydet("b", "Ctrl+Alt+R") is KayitSonucu.OK
        s.kaldir("a")
        s.hepsini_kaldir()
        assert s.kayitli() == {} and len(sahte.kaldirilar) == 2

    def test_b8d_destroyed_alicisi_self_yontemi_degil_ast_bagimsiz(self) -> None:
        agac = ast.parse((UI / "kisayol.py").read_text(encoding="utf-8"))
        baglantilar = [n for n in ast.walk(agac) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "connect"
                       and isinstance(n.func.value, ast.Attribute) and n.func.value.attr == "destroyed"]
        assert len(baglantilar) == 1
        arg = baglantilar[0].args[0]
        assert isinstance(arg, ast.Call) and isinstance(arg.func, ast.Attribute) and arg.func.attr == "partial"
        assert not any(isinstance(a, ast.Name) and a.id == "self" for a in arg.args)
        assert not any(isinstance(n, ast.Lambda) for n in ast.walk(arg))


# =====================================================================================================
# C -- kabuk etiketleri / kullanici istegi
# =====================================================================================================
class TestC_Kabuk:
    def test_c1_baslangic_etiketleri_kisayol_yok_sabit_ctrl_alt_t_yok(self, qtbot) -> None:
        p = AnaPencere(tepsi_kullanilabilir=False)
        qtbot.addWidget(p)
        for d in (p.dugme_anlik, p.dugme_bolge):
            assert KISAYOL_YOK in d.text() and KISAYOL_YOK in d.toolTip()
            assert "Ctrl+Alt+T" not in d.text() and "Ctrl+Alt" not in d.toolTip()
        assert p.tepsi.ikon.toolTip().startswith("Suflör")
        assert p.tepsi.ikon.toolTip().count(KISAYOL_YOK) == 2

    def test_c2_calistir_sonrasi_dugmeler_ve_tepsi_ipucu_kayitli_kombinasyonu_gosterir(self, sahte: SahteWin32, pencereler: list[AnaPencere]) -> None:
        p, s, _ = kur(sahte, pencereler)
        assert "Ctrl+Alt+D" in p.dugme_anlik.text() and "Ctrl+Alt+D" in p.dugme_anlik.toolTip()
        assert "Ctrl+Alt+R" in p.dugme_bolge.text() and "Ctrl+Alt+R" in p.dugme_bolge.toolTip()
        assert "Anlık çeviri" in p.dugme_anlik.text() and "Bölge izle" in p.dugme_bolge.text()
        ip = p.tepsi.ikon.toolTip()
        assert "Ctrl+Alt+D" in ip and "Ctrl+Alt+R" in ip and ip.startswith("Suflör")
        assert KISAYOL_YOK not in ip and "Ctrl+Alt+T" not in ip
        assert p.dugme_anlik.accessibleName() == "Anlık çeviri" and p.dugme_bolge.accessibleName() == "Bölge izle"

    def test_c2b_kanonik_metin_gosterilir_kullanicinin_yazdigi_degil(self, sahte: SahteWin32, pencereler: list[AnaPencere]) -> None:
        p, s, _ = kur(sahte, pencereler, {"anlik_cevir": "alt + ctrl + d", "bolge_izle": "shift+ctrl+f5"})
        assert "Ctrl+Alt+D" in p.dugme_anlik.text() and "alt + ctrl" not in p.dugme_anlik.text()
        assert "Ctrl+Shift+F5" in p.dugme_bolge.text()

    def test_c3_cakismada_yalniz_o_dugme_kisayol_yok_tepsi_ipucu_da(self, sahte: SahteWin32, pencereler: list[AnaPencere]) -> None:
        sahte.dolu.add((CA, ord("D")))
        p, s, _ = kur(sahte, pencereler)
        assert KISAYOL_YOK in p.dugme_anlik.text() and KISAYOL_YOK in p.dugme_anlik.toolTip()
        assert "Ctrl+Alt+R" in p.dugme_bolge.text() and KISAYOL_YOK not in p.dugme_bolge.text()
        ip = p.tepsi.ikon.toolTip()
        assert KISAYOL_YOK in ip and "Ctrl+Alt+R" in ip and "Ctrl+Alt+D" not in ip

    def test_c4_kisayol_etiketleri_bos_dict_bilinmeyen_ad_yeniden_cagri_biriktirmez(self, qtbot) -> None:
        p = AnaPencere(tepsi_kullanilabilir=False)
        qtbot.addWidget(p)
        p.kisayol_etiketleri({"anlik_cevir": "Ctrl+Alt+D", "bolge_izle": "Ctrl+Alt+R", "foo": "Ctrl+Alt+X"})
        assert "Ctrl+Alt+X" not in p.dugme_anlik.text() + p.dugme_bolge.text() + p.tepsi.ikon.toolTip()
        p.kisayol_etiketleri({"anlik_cevir": "Ctrl+Shift+F5"})
        assert "Ctrl+Shift+F5" in p.dugme_anlik.text() and "Ctrl+Alt+D" not in p.dugme_anlik.text()
        assert KISAYOL_YOK in p.dugme_bolge.text() and "Ctrl+Alt+R" not in p.dugme_bolge.text()
        p.kisayol_etiketleri({})
        assert p.dugme_anlik.text().count(KISAYOL_YOK) == 1 and p.dugme_bolge.text().count(KISAYOL_YOK) == 1
        assert p.tepsi.ikon.toolTip().count(KISAYOL_YOK) == 2 and "Ctrl" not in p.tepsi.ikon.toolTip()
        p.kisayol_etiketleri({"anlik_cevir": "", "bolge_izle": None})  # type: ignore[dict-item]
        assert p.dugme_anlik.text().count(KISAYOL_YOK) == 1 and p.dugme_bolge.text().count(KISAYOL_YOK) == 1

    def test_c5_ozel_kisayollar_yalniz_verilen_kaydedilir_durum_bos(self, sahte: SahteWin32, pencereler: list[AnaPencere]) -> None:
        p, s, _ = kur(sahte, pencereler, {"bolge_izle": "Ctrl+Shift+F5"})
        assert s.kayitli() == {"bolge_izle": "Ctrl+Shift+F5"} and p.durum_metni() == ""
        assert KISAYOL_YOK in p.dugme_anlik.text() and "Ctrl+Shift+F5" in p.dugme_bolge.text()
        b: list[int] = []
        p.bolge_izle_istendi.connect(lambda: b.append(1))
        ates(s, kimlik_of(sahte, MOD_CONTROL | MOD_SHIFT, 0x74))
        assert b == [1]

    def test_c6_varsayilanlar_d_ve_r_salt_okunur(self) -> None:
        assert dict(VARSAYILAN_KISAYOLLAR) == {"anlik_cevir": "Ctrl+Alt+D", "bolge_izle": "Ctrl+Alt+R"}
        with pytest.raises(TypeError):
            VARSAYILAN_KISAYOLLAR["anlik_cevir"] = "Ctrl+Alt+T"  # type: ignore[index]

    def test_c7_kabuk_durum_satiri_sarili_ve_pencere_genislemez(self, sahte: SahteWin32, pencereler: list[AnaPencere], qtbot) -> None:
        """Offscreen font metrikleri farkli (Segoe UI yok: bos pencere 936 px); olcu GORELI: iki cakisma metni genisligi
        degistirmez. Gercek platformda 520 (sonda_1 ile ayrica olculur)."""
        bos = AnaPencere(tepsi_kullanilabilir=False)
        qtbot.addWidget(bos)
        bos.show()
        g0 = (bos.width(), bos.height())
        sahte.dolu.update({(CA, ord("D")), (CA, ord("R"))})
        p, s, _ = kur(sahte, pencereler)
        assert len(p.durum_metni()) > 120 and p.durum_metni().count("kaydedilemedi") == 2
        assert (p.width(), p.height()) == g0


class TestC_Durum:
    def test_c8_kisayol_sinyali_kenar_durumunda_sekme_kapali_kalir(self, sahte: SahteWin32, pencereler: list[AnaPencere], monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(AnaPencere, "_balon_gosterildi", True)
        p, s, _ = kur(sahte, pencereler)
        p.kenara_al()
        ates(s, kimlik_of(sahte, CA, ord("R")))
        assert p.durum is KabukDurumu.KENAR and p.sekme.isVisible() and not p.isVisible()
