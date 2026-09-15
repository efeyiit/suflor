"""T-013 K1/K2/K3/K6 -- `src.ui.kisayol`: `KisayolServisi`, `KayitSonucu`, `kombinasyonu_coz` (pytest-qt, offscreen).

Hicbir test gercek `RegisterHotKey` CAGIRMAZ (Y1): dort Win32 fonksiyonu `SahteWin32` ile enjekte edilir; sefin
`conftest.py`si `SUFLOR_GERCEK_KISAYOL_YASAK=1` koyar ve `gercek_win32=True` kurulumu `RuntimeError` verir
(`test_k2_gercek_win32_yasak_degiskeni_varken_runtimeerror`). Olay yolu (K2) gercek `ctypes.wintypes.MSG` yapisi ve
`ctypes.addressof` ile filtreye DOGRUDAN verilir; sifir/bozuk adres testi YOK (KRT k9: sureci oldurur).
Omur testleri (`test_k1_yikim_*`) sahte uygulama nesnesinde `removeNativeEventFilter` sayar; pozitif kontrol
(kural 10): `self`in bagli yontemiyle bagli `destroyed` alicisi PySide6 6.11'de KOSMAZ (KRT k5b A).
"""
from __future__ import annotations

import ast
import ctypes
import functools
import gc
import threading
import weakref
from collections.abc import Callable, Iterator
from ctypes import wintypes
from pathlib import Path

import pytest
from PySide6 import QtCore, QtWidgets
from pytestqt.qtbot import QtBot

import src.ui
from src.ui import kisayol
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

UI_DIZINI = Path(src.ui.__file__).resolve().parent
OLAY_TIPI = b"windows_generic_MSG"
CA = MOD_CONTROL | MOD_ALT
CS = MOD_CONTROL | MOD_SHIFT
AS = MOD_ALT | MOD_SHIFT
CAS = MOD_CONTROL | MOD_ALT | MOD_SHIFT
VK = {"Space": 0x20, "Esc": 0x1B, "Tab": 0x09, "Enter": 0x0D, "Backspace": 0x08, "Delete": 0x2E, "Insert": 0x2D,
      "Home": 0x24, "End": 0x23, "PageUp": 0x21, "PageDown": 0x22, "Left": 0x25, "Up": 0x26, "Right": 0x27, "Down": 0x28}


class SahteWin32:
    """Enjekte edilen dort fonksiyon: cagri kaydi + ayarlanabilir sonuc. `reddet[(mod, vk)] = hata kodu` (mod NOREPEAT'siz)."""

    def __init__(self) -> None:
        self.kayitlar: list[tuple[int, int, int]] = []
        self.kaldirmalar: list[int] = []
        self.sira: list[tuple[str, int]] = []
        self.reddet: dict[tuple[int, int], int] = {}
        self.altgr: dict[int, str] = {}
        self.altgr_sorgular: list[int] = []
        self.son_hata = 0

    def kayit(self, kimlik: int, mod: int, vk: int) -> bool:
        self.kayitlar.append((kimlik, mod, vk))
        self.sira.append(("kayit", kimlik))
        kod = self.reddet.get((mod & ~MOD_NOREPEAT, vk))
        if kod is None:
            return True
        self.son_hata = kod
        return False

    def kaldir(self, kimlik: int) -> bool:
        self.kaldirmalar.append(kimlik)
        self.sira.append(("kaldir", kimlik))
        return True

    def hata_kodu(self) -> int:
        return self.son_hata

    def altgr_karakteri(self, vk: int) -> str:
        self.altgr_sorgular.append(vk)
        return self.altgr.get(vk, "")

    def servis(self, ebeveyn: QtCore.QObject | None = None) -> KisayolServisi:
        return KisayolServisi(ebeveyn, kayit_fn=self.kayit, kaldir_fn=self.kaldir, hata_kodu_fn=self.hata_kodu,
                              altgr_karakteri_fn=self.altgr_karakteri)

    @property
    def kayitli_idler(self) -> set[int]:
        return {k for k, _, _ in self.kayitlar} - set(self.kaldirmalar)


class SahteUygulama:
    """`kisayol._uygulama()` yerine: `installNativeEventFilter`/`removeNativeEventFilter` sayar, gercek uygulamaya iletir."""

    def __init__(self, gercek: QtCore.QCoreApplication) -> None:
        self._gercek = gercek
        self.kurulan: list[QtCore.QAbstractNativeEventFilter] = []
        self.kaldirilan: list[QtCore.QAbstractNativeEventFilter] = []

    def installNativeEventFilter(self, filtre: QtCore.QAbstractNativeEventFilter) -> None:  # noqa: N802
        self.kurulan.append(filtre)
        self._gercek.installNativeEventFilter(filtre)

    def removeNativeEventFilter(self, filtre: QtCore.QAbstractNativeEventFilter) -> None:  # noqa: N802
        self.kaldirilan.append(filtre)
        self._gercek.removeNativeEventFilter(filtre)

    def thread(self) -> QtCore.QThread:
        return self._gercek.thread()


def _mesaj(mesaj: int, wparam: int) -> wintypes.MSG:
    m = wintypes.MSG()
    m.hwnd = None
    m.message = mesaj
    m.wParam = wparam
    m.lParam = 0
    return m


def _filtreye_ver(servis: KisayolServisi, mesaj: int, wparam: int, tip: bytes | QtCore.QByteArray = OLAY_TIPI) -> object:
    m = _mesaj(mesaj, wparam)
    return servis.filtre.nativeEventFilter(tip, ctypes.addressof(m))


def _kabul(sonuc: object) -> bool:
    """Filtre donusu: `(bool, int)` ya da bool -> yutuldu mu."""
    if isinstance(sonuc, tuple):
        return bool(sonuc[0])
    return bool(sonuc)


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
def alinan(servis: KisayolServisi) -> list[str]:
    kutu: list[str] = []
    servis.tetiklendi.connect(kutu.append)
    return kutu


# -- K1 kayit/kaldirma durum makinesi -------------------------------------------------------------


def test_k1_kayit_sonucu_uyeleri() -> None:
    assert [s.value for s in KayitSonucu] == ["ok", "cakisma", "altgr_cakisma", "gecersiz", "hata"]
    assert KayitSonucu("cakisma") is KayitSonucu.CAKISMA and str(KayitSonucu.OK) == "ok"


def test_k1_kaydet_ok_cagri_dizisi_ve_norepeat(sahte: SahteWin32, servis: KisayolServisi) -> None:
    assert servis.kaydet("anlik", "Ctrl+Alt+D") is KayitSonucu.OK
    assert len(sahte.kayitlar) == 1
    kimlik, mod, vk = sahte.kayitlar[0]
    assert 1 <= kimlik <= 0xBFFF and vk == ord("D")
    assert mod & MOD_NOREPEAT == MOD_NOREPEAT, "her kayit MOD_NOREPEAT tasir (K1)"
    assert mod & ~MOD_NOREPEAT == CA
    assert servis.kayitli() == {"anlik": "Ctrl+Alt+D"} and servis.son_hata_kodu == 0
    assert sahte.kaldirmalar == []


def test_k1_1409_cakisma_kayitlida_yok(sahte: SahteWin32, servis: KisayolServisi) -> None:
    sahte.reddet[(CA, ord("D"))] = 1409
    assert servis.kaydet("anlik", "Ctrl+Alt+D") is KayitSonucu.CAKISMA
    assert servis.kayitli() == {} and servis.son_hata_kodu == 1409
    assert len(sahte.kayitlar) == 1 and sahte.kaldirmalar == []
    assert servis.kaydet("bolge", "Ctrl+Alt+R") is KayitSonucu.OK, "diger kisayol calismaya devam eder (K5)"
    assert servis.kayitli() == {"bolge": "Ctrl+Alt+R"} and servis.son_hata_kodu == 0


def test_k1_diger_hata_kodu_hata(sahte: SahteWin32, servis: KisayolServisi) -> None:
    sahte.reddet[(CA, ord("D"))] = 87
    assert servis.kaydet("anlik", "Ctrl+Alt+D") is KayitSonucu.HATA
    assert servis.son_hata_kodu == 87 and servis.kayitli() == {}


def test_k1_ayni_ad_yeniden_kaydet_once_kaldir_sonra_kaydet(sahte: SahteWin32, servis: KisayolServisi) -> None:
    servis.kaydet("anlik", "Ctrl+Alt+D")
    ilk = sahte.kayitlar[0][0]
    assert servis.kaydet("anlik", "Ctrl+Alt+F") is KayitSonucu.OK
    assert sahte.sira == [("kayit", ilk), ("kaldir", ilk), ("kayit", sahte.kayitlar[1][0])]
    assert sahte.kayitlar[1][0] != ilk, "yeni kayit yeni kimlik alir"
    assert servis.kayitli() == {"anlik": "Ctrl+Alt+F"}


def test_k1_ayni_ad_ayni_kombinasyon_yeniden_kaydet(sahte: SahteWin32, servis: KisayolServisi) -> None:
    servis.kaydet("anlik", "Ctrl+Alt+D")
    assert servis.kaydet("anlik", "Ctrl+Alt+D") is KayitSonucu.OK
    assert [t for t, _ in sahte.sira] == ["kayit", "kaldir", "kayit"]
    assert servis.kayitli() == {"anlik": "Ctrl+Alt+D"}


def test_k1_ayni_ad_gecersiz_yeni_kombinasyon_eski_kayit_korunur(sahte: SahteWin32, servis: KisayolServisi) -> None:
    """Dilbilgisi/AltGr denetimi Win32'den ONCE: yeni kombinasyon gecersizse eski kayit dokunulmadan kalir."""
    servis.kaydet("anlik", "Ctrl+Alt+D")
    assert servis.kaydet("anlik", "Win+D") is KayitSonucu.GECERSIZ
    assert servis.kaydet("anlik", "bos+") is KayitSonucu.GECERSIZ
    sahte.altgr[ord("T")] = "₺"
    assert servis.kaydet("anlik", "Ctrl+Alt+T") is KayitSonucu.ALTGR_CAKISMA
    assert servis.kayitli() == {"anlik": "Ctrl+Alt+D"} and sahte.kaldirmalar == [] and len(sahte.kayitlar) == 1


def test_k1_ayni_kombinasyon_baska_ad_servis_ici_cakisma_win32_cagrilmaz(sahte: SahteWin32, servis: KisayolServisi) -> None:
    servis.kaydet("anlik", "Ctrl+Alt+D")
    assert servis.kaydet("bolge", "alt + ctrl + d") is KayitSonucu.CAKISMA
    assert len(sahte.kayitlar) == 1 and servis.kayitli() == {"anlik": "Ctrl+Alt+D"}
    assert servis.son_hata_kodu == 0, "servis ici tekrar Win32'ye gitmez, hata kodu yok"


def test_k1_kaldir_bilinmeyen_sessiz(sahte: SahteWin32, servis: KisayolServisi) -> None:
    servis.kaldir("yok")
    servis.kaydet("anlik", "Ctrl+Alt+D")
    servis.kaldir("yok")
    assert sahte.kaldirmalar == [] and servis.kayitli() == {"anlik": "Ctrl+Alt+D"}


def test_k1_kaldir_kayitli_win32_ve_tablo(sahte: SahteWin32, servis: KisayolServisi) -> None:
    servis.kaydet("anlik", "Ctrl+Alt+D")
    servis.kaydet("bolge", "Ctrl+Alt+R")
    kimlik_anlik = sahte.kayitlar[0][0]
    servis.kaldir("anlik")
    assert sahte.kaldirmalar == [kimlik_anlik] and servis.kayitli() == {"bolge": "Ctrl+Alt+R"}
    servis.kaldir("anlik")
    assert sahte.kaldirmalar == [kimlik_anlik], "ikinci kaldir sessiz"
    assert servis.kaydet("x", "Ctrl+Alt+D") is KayitSonucu.OK, "kaldirilan kombinasyon yeniden alinabilir"


def test_k1_hepsini_kaldir_idempotent(sahte: SahteWin32, servis: KisayolServisi) -> None:
    servis.hepsini_kaldir()
    servis.kaydet("anlik", "Ctrl+Alt+D")
    servis.kaydet("bolge", "Ctrl+Alt+R")
    idler = [k for k, _, _ in sahte.kayitlar]
    servis.hepsini_kaldir()
    servis.hepsini_kaldir()
    assert sorted(sahte.kaldirmalar) == sorted(idler) and servis.kayitli() == {}


def test_k1_kayitli_kopya_disaridan_mutasyon_servisi_etkilemez(servis: KisayolServisi) -> None:
    servis.kaydet("anlik", "Ctrl+Alt+D")
    k = servis.kayitli()
    assert isinstance(k, dict)
    k["bolge"] = "Ctrl+Alt+R"
    k.pop("anlik")
    assert servis.kayitli() == {"anlik": "Ctrl+Alt+D"}


def test_k1_kimlik_surec_genelinde_benzersiz_iki_servis(sahte: SahteWin32, qtbot: QtBot) -> None:
    """Iki servis ayni surecte: kimlik kumeleri AYRIK, her `kaldir` yalniz kendi kimliklerini cagirir (KRT g5: ayni id iki kayit)."""
    a, b = sahte.servis(), sahte.servis()
    try:
        a.kaydet("anlik", "Ctrl+Alt+D")
        a.kaydet("bolge", "Ctrl+Alt+R")
        b.kaydet("anlik", "Ctrl+Alt+F")
        b.kaydet("bolge", "Ctrl+Alt+G")
        a_idler = {k for k, _, _ in sahte.kayitlar[:2]}
        b_idler = {k for k, _, _ in sahte.kayitlar[2:]}
        assert len(a_idler) == 2 and len(b_idler) == 2 and a_idler.isdisjoint(b_idler)
        b.hepsini_kaldir()
        assert set(sahte.kaldirmalar) == b_idler, "b yalniz kendi kimliklerini kaldirir"
        assert a.kayitli() == {"anlik": "Ctrl+Alt+D", "bolge": "Ctrl+Alt+R"}
        a.hepsini_kaldir()
        assert set(sahte.kaldirmalar) == a_idler | b_idler
    finally:
        a.deleteLater()
        b.deleteLater()
        qtbot.wait(10)


def test_k1_kimlik_sayaci_ust_sinirda_sarar_ve_canli_kimligi_atlar(sahte: SahteWin32, servis: KisayolServisi, monkeypatch: pytest.MonkeyPatch) -> None:
    servis.kaydet("a", "Ctrl+Alt+A")
    canli = sahte.kayitlar[0][0]
    monkeypatch.setattr(kisayol, "_sonraki_kimlik", 0xBFFF)
    servis.kaydet("b", "Ctrl+Alt+B")
    assert sahte.kayitlar[1][0] == 0xBFFF
    monkeypatch.setattr(kisayol, "_sonraki_kimlik", canli)
    servis.kaydet("c", "Ctrl+Alt+C")
    assert sahte.kayitlar[2][0] not in {canli, 0xBFFF}, "canli kimlik yeniden verilmez"
    assert 1 <= sahte.kayitlar[2][0] <= 0xBFFF
    assert kisayol._sonraki_kimlik <= 0xBFFF


def test_k1_kimlik_ust_siniri_0xbfff(sahte: SahteWin32, servis: KisayolServisi, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(kisayol, "_sonraki_kimlik", 0xBFFF)
    servis.kaydet("a", "Ctrl+Alt+A")
    servis.kaydet("b", "Ctrl+Alt+B")
    assert [k for k, _, _ in sahte.kayitlar] == [0xBFFF, 1], "0xBFFF sonrasi 1'e sarar (uygulama araligi)"


def _sahte_uygulama(monkeypatch: pytest.MonkeyPatch, qapp: QtWidgets.QApplication) -> SahteUygulama:
    su = SahteUygulama(qapp)
    monkeypatch.setattr(kisayol, "_uygulama", lambda: su)
    return su


@pytest.mark.parametrize("yol", ["del_gc", "deleteLater"])
def test_k1_yikim_kayitlar_kaldirilir_filtre_sokulur(qtbot: QtBot, qapp: QtWidgets.QApplication, monkeypatch: pytest.MonkeyPatch, yol: str) -> None:
    """K1 ▲ Y3: `destroyed` alicisi `self`siz; `del`+gc VE `deleteLater` yollarinda sahte `kaldir_fn` her kimlik icin cagrilir,
    `removeNativeEventFilter` sahte uygulamada 1 kez sayilir."""
    su = _sahte_uygulama(monkeypatch, qapp)
    sahte = SahteWin32()
    s = sahte.servis()
    assert len(su.kurulan) == 1 and su.kaldirilan == []
    s.kaydet("anlik", "Ctrl+Alt+D")
    s.kaydet("bolge", "Ctrl+Alt+R")
    idler = [k for k, _, _ in sahte.kayitlar]
    ws = weakref.ref(s)
    if yol == "del_gc":
        del s
        gc.collect()
        assert ws() is None, "servis sarmalayicisi toplanmadi (filtre/partial self tutuyor)"
    else:
        s.deleteLater()
        qtbot.wait(50)
    qtbot.wait(10)
    assert sorted(sahte.kaldirmalar) == sorted(idler), "yikimda her kimlik icin kaldir_fn"
    assert len(su.kaldirilan) == 1 and su.kaldirilan[0] is su.kurulan[0], "filtre yikimda sokulur"


def test_k1_yikim_ebeveyn_silinince_cocuk_servis_temizler(qtbot: QtBot, qapp: QtWidgets.QApplication, monkeypatch: pytest.MonkeyPatch) -> None:
    """`calistir` deseni: servis pencerenin cocugu; ebeveyn `del`+gc ile gidince kayitlar kaldirilir."""
    su = _sahte_uygulama(monkeypatch, qapp)
    sahte = SahteWin32()
    ebeveyn = QtCore.QObject()
    s = sahte.servis(ebeveyn)
    s.kaydet("anlik", "Ctrl+Alt+D")
    kimlik = sahte.kayitlar[0][0]
    del s
    del ebeveyn
    gc.collect()
    qtbot.wait(10)
    assert sahte.kaldirmalar == [kimlik] and len(su.kaldirilan) == 1


def test_k1_yikim_hepsini_kaldir_sonrasi_cift_kaldirma_yok(qtbot: QtBot, qapp: QtWidgets.QApplication, monkeypatch: pytest.MonkeyPatch) -> None:
    su = _sahte_uygulama(monkeypatch, qapp)
    sahte = SahteWin32()
    s = sahte.servis()
    s.kaydet("anlik", "Ctrl+Alt+D")
    s.hepsini_kaldir()
    del s
    gc.collect()
    qtbot.wait(10)
    assert len(sahte.kaldirmalar) == 1 and len(su.kaldirilan) == 1


def test_k1_yikim_pozitif_kontrol_bagli_yontem_kosmaz_partial_kosar(qtbot: QtBot) -> None:
    """Olcu ateslenebilir (kural 10; KRT k5b A/B): `self.destroyed.connect(self._temizle)` PySide6 6.11'de her iki yolda
    KOSMAZ; `functools.partial(serbest_fn, ...)` kosar. Servisin deseni ikincisidir."""
    log: list[str] = []

    def serbest(etiket: str) -> None:
        log.append(etiket)

    class BagliYontem(QtCore.QObject):
        def __init__(self) -> None:
            super().__init__()
            self.destroyed.connect(self._temizle)

        def _temizle(self) -> None:
            log.append("bagli")

    class Partialli(QtCore.QObject):
        def __init__(self) -> None:
            super().__init__()
            self.destroyed.connect(functools.partial(serbest, "partial"))

    sonuc: dict[str, list[str]] = {}
    for K in (BagliYontem, Partialli):
        log.clear()
        a = K()
        del a
        gc.collect()
        b = K()
        b.deleteLater()
        qtbot.wait(50)
        sonuc[K.__name__] = list(log)
    assert sonuc == {"BagliYontem": [], "Partialli": ["partial", "partial"]}


def test_k1_kaynakta_destroyed_alicisi_self_yontemi_degil_ast() -> None:
    """Yapisal (Y3): `kisayol.py`de `self.destroyed.connect(...)` argumani `self.<yontem>` DEGIL, `functools.partial(...)`."""
    agac = ast.parse((UI_DIZINI / "kisayol.py").read_text(encoding="utf-8"))
    baglantilar = [
        d for d in ast.walk(agac)
        if isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) and d.func.attr == "connect"
        and isinstance(d.func.value, ast.Attribute) and d.func.value.attr == "destroyed"
    ]
    assert len(baglantilar) == 1
    arg = baglantilar[0].args[0]
    assert isinstance(arg, ast.Call) and isinstance(arg.func, ast.Attribute) and arg.func.attr == "partial"
    assert not any(isinstance(a, ast.Name) and a.id == "self" for a in ast.walk(arg)), "partial `self` yakalamamali"


# -- K2 olay yolu: WM_HOTKEY -> tetiklendi(ad) yalniz bizim kimlikler icin ---------------------------


def test_k2_bilinen_kimlik_sinyal_ve_true(sahte: SahteWin32, servis: KisayolServisi, alinan: list[str]) -> None:
    servis.kaydet("anlik", "Ctrl+Alt+D")
    kimlik = sahte.kayitlar[0][0]
    assert _kabul(_filtreye_ver(servis, WM_HOTKEY, kimlik)) is True
    assert alinan == ["anlik"]
    assert _kabul(_filtreye_ver(servis, WM_HOTKEY, kimlik, QtCore.QByteArray(OLAY_TIPI))) is True
    assert alinan == ["anlik", "anlik"]


def test_k2_iki_kayit_dogru_ad(sahte: SahteWin32, servis: KisayolServisi, alinan: list[str]) -> None:
    servis.kaydet("anlik", "Ctrl+Alt+D")
    servis.kaydet("bolge", "Ctrl+Alt+R")
    ida, idb = (k for k, _, _ in sahte.kayitlar)
    _filtreye_ver(servis, WM_HOTKEY, idb)
    _filtreye_ver(servis, WM_HOTKEY, ida)
    assert alinan == ["bolge", "anlik"]


def test_k2_bilinmeyen_kimlik_false_sinyal_yok(sahte: SahteWin32, servis: KisayolServisi, alinan: list[str]) -> None:
    servis.kaydet("anlik", "Ctrl+Alt+D")
    kimlik = sahte.kayitlar[0][0]
    assert _kabul(_filtreye_ver(servis, WM_HOTKEY, kimlik + 1)) is False
    assert _kabul(_filtreye_ver(servis, WM_HOTKEY, 0)) is False
    assert alinan == []


def test_k2_kaldirilan_kimlik_artik_bilinmiyor(sahte: SahteWin32, servis: KisayolServisi, alinan: list[str]) -> None:
    servis.kaydet("anlik", "Ctrl+Alt+D")
    kimlik = sahte.kayitlar[0][0]
    servis.kaldir("anlik")
    assert _kabul(_filtreye_ver(servis, WM_HOTKEY, kimlik)) is False and alinan == []


def test_k2_wm_hotkey_disi_false(sahte: SahteWin32, servis: KisayolServisi, alinan: list[str]) -> None:
    servis.kaydet("anlik", "Ctrl+Alt+D")
    kimlik = sahte.kayitlar[0][0]
    for mesaj in (0x0100, 0x0101, 0x0312 + 1, 0x0000):
        assert _kabul(_filtreye_ver(servis, mesaj, kimlik)) is False, hex(mesaj)
    assert alinan == []


def test_k2_yanlis_event_type_false_mesaja_dokunmaz(sahte: SahteWin32, servis: KisayolServisi, alinan: list[str]) -> None:
    """eventType `windows_generic_MSG` degilse mesaj OKUNMADAN `False` (KRT O7: yapi Windows MSG olmayabilir)."""
    servis.kaydet("anlik", "Ctrl+Alt+D")
    kimlik = sahte.kayitlar[0][0]
    for tip in (b"xcb_generic_event_t", b"windows_generic_MSG ", b"", QtCore.QByteArray(b"mac_generic_NSEvent")):
        assert _kabul(_filtreye_ver(servis, WM_HOTKEY, kimlik, tip)) is False, tip
    assert alinan == []


def test_k2_filtre_bir_kez_kurulur_ve_ayni_nesne(qapp: QtWidgets.QApplication, monkeypatch: pytest.MonkeyPatch, qtbot: QtBot) -> None:
    su = _sahte_uygulama(monkeypatch, qapp)
    sahte = SahteWin32()
    s = sahte.servis()
    try:
        s.kaydet("anlik", "Ctrl+Alt+D")
        s.kaydet("bolge", "Ctrl+Alt+R")
        s.hepsini_kaldir()
        s.kaydet("anlik", "Ctrl+Alt+D")
        assert len(su.kurulan) == 1 and su.kurulan[0] is s.filtre and su.kaldirilan == []
        assert isinstance(s.filtre, QtCore.QAbstractNativeEventFilter)
    finally:
        s.hepsini_kaldir()
        s.deleteLater()
        qtbot.wait(10)


def test_k2_filtre_sirasi_eski_servis_yeni_servisin_olayini_yutmaz(sahte: SahteWin32, qtbot: QtBot) -> None:
    """Qt filtreleri SON kurulan once cagirir (KRT p2); bilinmeyen kimlikte `False` bu yuzden zorunlu."""
    eski, yeni = sahte.servis(), sahte.servis()
    try:
        alinan_eski: list[str] = []
        alinan_yeni: list[str] = []
        eski.tetiklendi.connect(alinan_eski.append)
        yeni.tetiklendi.connect(alinan_yeni.append)
        eski.kaydet("anlik", "Ctrl+Alt+D")
        yeni.kaydet("anlik", "Ctrl+Alt+F")
        kimlik_yeni = sahte.kayitlar[1][0]
        assert _kabul(_filtreye_ver(eski, WM_HOTKEY, kimlik_yeni)) is False
        assert _kabul(_filtreye_ver(yeni, WM_HOTKEY, kimlik_yeni)) is True
        assert alinan_eski == [] and alinan_yeni == ["anlik"]
    finally:
        eski.hepsini_kaldir()
        yeni.hepsini_kaldir()
        eski.deleteLater()
        yeni.deleteLater()
        qtbot.wait(10)


@pytest.mark.parametrize("eksik", ["kayit_fn", "kaldir_fn", "hata_kodu_fn", "altgr_karakteri_fn"])
def test_k2_gercek_win32_false_fn_eksikse_runtimeerror(sahte: SahteWin32, eksik: str) -> None:
    """Y1: offscreen'de de Win32 dagitici calisir -> sahte fn'ler verilmeden servis KURULAMAZ."""
    fnler: dict[str, Callable[..., object]] = {"kayit_fn": sahte.kayit, "kaldir_fn": sahte.kaldir,
                                                "hata_kodu_fn": sahte.hata_kodu, "altgr_karakteri_fn": sahte.altgr_karakteri}
    fnler.pop(eksik)
    with pytest.raises(RuntimeError, match=eksik):
        KisayolServisi(None, **fnler)  # type: ignore[arg-type]
    with pytest.raises(RuntimeError):
        KisayolServisi()


def test_k2_gercek_win32_false_fnler_verilince_kurulur_pozitif_kontrol(sahte: SahteWin32, qtbot: QtBot) -> None:
    s = KisayolServisi(None, gercek_win32=False, kayit_fn=sahte.kayit, kaldir_fn=sahte.kaldir, hata_kodu_fn=sahte.hata_kodu,
                       altgr_karakteri_fn=sahte.altgr_karakteri)
    try:
        assert s.kaydet("anlik", "Ctrl+Alt+D") is KayitSonucu.OK and len(sahte.kayitlar) == 1
    finally:
        s.hepsini_kaldir()
        s.deleteLater()
        qtbot.wait(10)


def test_k2_gercek_win32_yasak_degiskeni_varken_runtimeerror(qapp: QtWidgets.QApplication) -> None:
    """Sefin conftest'i `SUFLOR_GERCEK_KISAYOL_YASAK=1` koyar; birim testte gercek servis kurulamaz (emniyet kemeri)."""
    import os

    assert os.environ.get(kisayol.GERCEK_KISAYOL_YASAK_DEGISKENI) == "1"
    with pytest.raises(RuntimeError, match=kisayol.GERCEK_KISAYOL_YASAK_DEGISKENI):
        KisayolServisi(gercek_win32=True)
    sahte = SahteWin32()
    with pytest.raises(RuntimeError):
        KisayolServisi(gercek_win32=True, kayit_fn=sahte.kayit, kaldir_fn=sahte.kaldir, hata_kodu_fn=sahte.hata_kodu,
                       altgr_karakteri_fn=sahte.altgr_karakteri)


def test_k2_gercek_win32_yasak_degiskeni_yokken_kurulur_kayit_yapmaz_pozitif_kontrol(qapp: QtWidgets.QApplication, monkeypatch: pytest.MonkeyPatch, qtbot: QtBot) -> None:
    """Kemerin kaynagi ortam degiskenidir: degisken kaldirilinca `gercek_win32=True` KURULUR (ince sarmalayicilar baglanir);
    `kaydet` CAGRILMAZ -- gercek `RegisterHotKey` bu testte de yok."""
    monkeypatch.delenv(kisayol.GERCEK_KISAYOL_YASAK_DEGISKENI)
    s = KisayolServisi(gercek_win32=True)
    try:
        assert s.kayitli() == {}
        assert s.filtre is not None
    finally:
        s.deleteLater()
        qtbot.wait(10)


def test_k2_uygulama_yoksa_runtimeerror(monkeypatch: pytest.MonkeyPatch, sahte: SahteWin32) -> None:
    monkeypatch.setattr(QtCore.QCoreApplication, "instance", staticmethod(lambda *_: None))
    with pytest.raises(RuntimeError, match="QApplication"):
        sahte.servis()


# -- K3 kombinasyon dilbilgisi: saf ve kati ----------------------------------------------------------

_TABLO: list[tuple[str, object]] = [
    # gecerli: (mod, vk)
    ("Ctrl+Alt+D", (CA, ord("D"))),
    ("ctrl + alt + d", (CA, ord("D"))),
    ("Alt+Ctrl+D", (CA, ord("D"))),
    ("Control+Alt+R", (CA, ord("R"))),
    ("CTRL+ALT+r", (CA, ord("R"))),
    ("Ctrl+Shift+T", (CS, ord("T"))),
    ("Alt+Shift+T", (AS, ord("T"))),
    ("Shift+Alt+Ctrl+T", (CAS, ord("T"))),
    ("Ctrl+Alt+0", (CA, ord("0"))),
    ("Ctrl+Alt+9", (CA, ord("9"))),
    ("Ctrl+Shift+Space", (CS, VK["Space"])),
    ("Ctrl+Alt+Space", (CA, VK["Space"])),
    ("Ctrl+Alt+Tab", (CA, VK["Tab"])),
    ("Ctrl+Alt+Enter", (CA, VK["Enter"])),
    ("Ctrl+Alt+Return", (CA, VK["Enter"])),
    ("Ctrl+Alt+Backspace", (CA, VK["Backspace"])),
    ("Ctrl+Shift+Delete", (CS, VK["Delete"])),
    ("Ctrl+Alt+Insert", (CA, VK["Insert"])),
    ("Ctrl+Alt+Home", (CA, VK["Home"])),
    ("Ctrl+Alt+End", (CA, VK["End"])),
    ("Ctrl+Alt+PageUp", (CA, VK["PageUp"])),
    ("Ctrl+Alt+PgDn", (CA, VK["PageDown"])),
    ("Ctrl+Alt+Left", (CA, VK["Left"])),
    ("Ctrl+Alt+Up", (CA, VK["Up"])),
    ("Ctrl+Alt+Right", (CA, VK["Right"])),
    ("Ctrl+Alt+Down", (CA, VK["Down"])),
    ("Ctrl+Alt+Esc", (CA, VK["Esc"])),
    ("Ctrl+Alt+Escape", (CA, VK["Esc"])),
    ("Ctrl+F1", (MOD_CONTROL, 0x70)),
    ("Alt+F11", (MOD_ALT, 0x7A)),
    ("Shift+F5", (MOD_SHIFT, 0x74)),
    ("Ctrl+Alt+F11", (CA, 0x7A)),
    ("Ctrl+Alt+Shift+F1", (CAS, 0x70)),
    # GECERSIZ sinifi: ayristirilabilir ama yasak -> GecersizKombinasyon (ValueError alt sinifi)
    ("Ctrl+D", GecersizKombinasyon),
    ("Alt+D", GecersizKombinasyon),
    ("Shift+T", GecersizKombinasyon),
    ("Shift+Space", GecersizKombinasyon),
    ("Ctrl+C", GecersizKombinasyon),
    ("Alt+Enter", GecersizKombinasyon),
    ("Ctrl+Tab", GecersizKombinasyon),
    ("D", GecersizKombinasyon),
    ("F1", GecersizKombinasyon),
    ("Win+D", GecersizKombinasyon),
    ("Meta+D", GecersizKombinasyon),
    ("Win+Shift+S", GecersizKombinasyon),
    ("Ctrl+Alt+Win+D", GecersizKombinasyon),
    ("Ctrl+Alt+F12", GecersizKombinasyon),
    ("Ctrl+F12", GecersizKombinasyon),
    ("Alt+Tab", GecersizKombinasyon),
    ("Alt+F4", GecersizKombinasyon),
    ("Alt+Esc", GecersizKombinasyon),
    ("Alt+Space", GecersizKombinasyon),
    ("Ctrl+Esc", GecersizKombinasyon),
    ("Ctrl+Alt+Delete", GecersizKombinasyon),
    ("Ctrl+Alt+Del", GecersizKombinasyon),
    ("Alt+Ctrl+Delete", GecersizKombinasyon),
    ("Ctrl+Shift+Esc", GecersizKombinasyon),
    ("Shift+Ctrl+Escape", GecersizKombinasyon),
    # ValueError sinifi: bozuk metin
    ("", ValueError),
    ("   ", ValueError),
    ("+", ValueError),
    ("Ctrl+", ValueError),
    ("+D", ValueError),
    ("Ctrl++D", ValueError),
    ("Ctrl+Alt++D", ValueError),
    ("Ctrl+ +D", ValueError),
    ("Ctrl+Alt", ValueError),
    ("Ctrl+Ctrl+D", ValueError),
    ("Ctrl+Control+D", ValueError),
    ("Ctrl+Alt+D+R", ValueError),
    ("Ctrl+Alt+DR", ValueError),
    ("Ctrl+Alt+F13", ValueError),
    ("Ctrl+Alt+F0", ValueError),
    ("Ctrl+Alt+Kapat", ValueError),
    ("Ctrl+Alt+ı", ValueError),
    ("Ctrl+Alt+ş", ValueError),
    ("Ctrl-Alt-D", ValueError),
    ("Ctrl Alt D", ValueError),
    ("Ctrl+Alt+PrintScreen", ValueError),
    ("Ctrl+Alt+NumLock", ValueError),
]


@pytest.mark.parametrize(("metin", "beklenen"), _TABLO, ids=[repr(m) for m, _ in _TABLO])
def test_k3_dilbilgisi_tablosu(metin: str, beklenen: object) -> None:
    if isinstance(beklenen, tuple):
        assert kombinasyonu_coz(metin) == beklenen
        assert KisayolServisi.kombinasyonu_coz(metin) == beklenen
    else:
        assert isinstance(beklenen, type)
        with pytest.raises(beklenen) as hata:
            kombinasyonu_coz(metin)
        assert type(hata.value) is beklenen, "sinif ayrimi: bozuk metin DUZ ValueError, yasak kombinasyon GecersizKombinasyon"
        with pytest.raises(ValueError):
            KisayolServisi.kombinasyonu_coz(metin)


def test_k3_tablo_en_az_kirk_ornek_ve_siniflar() -> None:
    assert len(_TABLO) >= 40
    assert sum(1 for _, b in _TABLO if isinstance(b, tuple)) >= 20
    assert sum(1 for _, b in _TABLO if b is GecersizKombinasyon) >= 12
    assert sum(1 for _, b in _TABLO if b is ValueError) >= 8
    assert issubclass(GecersizKombinasyon, ValueError)


def test_k3_gecersiz_bozuk_ayrimi() -> None:
    """GECERSIZ sinifi `GecersizKombinasyon`; bozuk metin DUZ `ValueError` (alt sinif degil)."""
    with pytest.raises(GecersizKombinasyon):
        kombinasyonu_coz("Alt+Tab")
    try:
        kombinasyonu_coz("Ctrl+Ctrl+D")
    except ValueError as hata:
        assert not isinstance(hata, GecersizKombinasyon)
    else:  # pragma: no cover
        pytest.fail("ValueError bekleniyordu")


def test_k3_kombinasyonu_yaz_kanonik_ve_tersine() -> None:
    assert kombinasyonu_yaz(CA, ord("D")) == "Ctrl+Alt+D"
    assert kombinasyonu_yaz(CAS, ord("T")) == "Ctrl+Alt+Shift+T"
    assert kombinasyonu_yaz(MOD_SHIFT | MOD_CONTROL, VK["PageDown"]) == "Ctrl+Shift+PageDown"
    assert kombinasyonu_yaz(MOD_ALT, 0x7A) == "Alt+F11"
    for metin, beklenen in _TABLO:
        if isinstance(beklenen, tuple):
            mod, vk = beklenen
            assert kombinasyonu_coz(kombinasyonu_yaz(mod, vk)) == (mod, vk), metin
    with pytest.raises(ValueError):
        kombinasyonu_yaz(CA, 0x7B)  # F12 tabloda yok
    with pytest.raises(ValueError):
        kombinasyonu_yaz(CA | MOD_NOREPEAT, ord("D"))  # NOREPEAT dilbilgisinin parcasi degil
    with pytest.raises(ValueError):
        kombinasyonu_yaz(0x8 | MOD_CONTROL, ord("D"))  # Win


def test_k3_kayitli_kanonik_metin(servis: KisayolServisi) -> None:
    servis.kaydet("a", "shift + alt + ctrl + pgdn")
    servis.kaydet("b", "alt+f11")
    assert servis.kayitli() == {"a": "Ctrl+Alt+Shift+PageDown", "b": "Alt+F11"}


def test_k3_kaydet_gecersiz_ve_bozuk_metin_gecersiz_win32_cagrilmaz(sahte: SahteWin32, servis: KisayolServisi) -> None:
    for metin in ("Win+D", "Ctrl+Alt+F12", "Alt+Tab", "Shift+T", "", "Ctrl+Ctrl+D", "Ctrl+Alt+D+R"):
        assert servis.kaydet("x", metin) is KayitSonucu.GECERSIZ, metin
    assert sahte.kayitlar == [] and servis.kayitli() == {} and sahte.altgr_sorgular == []


def test_k3_altgr_cakismasi_ctrl_alt_shiftsiz(sahte: SahteWin32, servis: KisayolServisi) -> None:
    """▲ Y2: `Ctrl+Alt+<tus>` (Shift'siz) ve `altgr_karakteri(vk)` bos degil -> ALTGR_CAKISMA, Win32 CAGRILMAZ."""
    sahte.altgr[ord("T")] = "₺"
    sahte.altgr[ord("2")] = "£"
    assert servis.kaydet("x", "Ctrl+Alt+T") is KayitSonucu.ALTGR_CAKISMA
    assert servis.kaydet("y", "Ctrl+Alt+2") is KayitSonucu.ALTGR_CAKISMA
    assert sahte.kayitlar == [] and servis.kayitli() == {} and servis.son_hata_kodu == 0
    assert sahte.altgr_sorgular == [ord("T"), ord("2")]
    assert servis.kaydet("x", "Ctrl+Alt+R") is KayitSonucu.OK
    assert sahte.altgr_sorgular == [ord("T"), ord("2"), ord("R")], "R de soruldu, bos geldi -> OK"
    assert servis.kayitli() == {"x": "Ctrl+Alt+R"}


def test_k3_altgr_shiftli_ve_ctrl_altsiz_sorulmaz(sahte: SahteWin32, servis: KisayolServisi) -> None:
    sahte.altgr[ord("T")] = "₺"
    assert servis.kaydet("a", "Ctrl+Shift+T") is KayitSonucu.OK
    assert servis.kaydet("b", "Ctrl+Alt+Shift+T") is KayitSonucu.OK
    assert servis.kaydet("c", "Alt+Shift+T") is KayitSonucu.OK
    assert servis.kaydet("d", "Ctrl+F1") is KayitSonucu.OK
    assert sahte.altgr_sorgular == [], "AltGr yolu yalniz Ctrl+Alt (Shift'siz) icin"
    assert len(sahte.kayitlar) == 4


def test_k3_altgr_fonksiyonu_gercek_win32_ince_sarmalayici_imzasi() -> None:
    """`altgr_karakteri` modul fonksiyonu var, `str` doner (gercek ToUnicodeEx; degeri `real_check` [8] olcer)."""
    assert callable(kisayol.altgr_karakteri)
    assert kisayol.altgr_karakteri.__annotations__.get("return") in ("str", str)


# -- K6 metin yok, blok yok, thread ------------------------------------------------------------------


def test_k6_baska_threadden_kaydet_runtimeerror_win32_cagrilmaz(sahte: SahteWin32, servis: KisayolServisi) -> None:
    sonuc: dict[str, object] = {}

    def th() -> None:
        try:
            sonuc["deger"] = servis.kaydet("anlik", "Ctrl+Alt+D")
        except RuntimeError as hata:
            sonuc["hata"] = hata

    t = threading.Thread(target=th)
    t.start()
    t.join(5)
    assert not t.is_alive()
    assert isinstance(sonuc.get("hata"), RuntimeError) and "deger" not in sonuc
    assert sahte.kayitlar == [] and sahte.altgr_sorgular == [] and servis.kayitli() == {}
    assert servis.kaydet("anlik", "Ctrl+Alt+D") is KayitSonucu.OK, "ana threadde calisir (pozitif kontrol)"


def test_k6_baska_threadden_kaldir_ve_hepsini_kaldir_runtimeerror(sahte: SahteWin32, servis: KisayolServisi) -> None:
    servis.kaydet("anlik", "Ctrl+Alt+D")
    hatalar: list[str] = []

    def th() -> None:
        islemler: list[tuple[str, Callable[[], None]]] = [("kaldir", lambda: servis.kaldir("anlik")), ("hepsini_kaldir", servis.hepsini_kaldir)]
        for ad, f in islemler:
            try:
                f()
            except RuntimeError:
                hatalar.append(ad)

    t = threading.Thread(target=th)
    t.start()
    t.join(5)
    assert hatalar == ["kaldir", "hepsini_kaldir"]
    assert sahte.kaldirmalar == [] and servis.kayitli() == {"anlik": "Ctrl+Alt+D"}


def test_k6_ince_sarmalayicilar_pragma_no_cover_ve_ctypes_yalniz_orada() -> None:
    """Gercek Win32 ince sarmalayicilari `# pragma: no cover` (D4); `RegisterHotKey`/`UnregisterHotKey`/`ToUnicodeEx` adlari
    yalniz bu sarmalayicilarda gecer."""
    kaynak = (UI_DIZINI / "kisayol.py").read_text(encoding="utf-8")
    agac = ast.parse(kaynak)
    satirlar = kaynak.splitlines()
    sarmalayicilar = {d.name for d in ast.walk(agac) if isinstance(d, ast.FunctionDef) and "pragma: no cover" in satirlar[d.lineno - 1]}
    assert {"_win32_kaydet", "_win32_kaldir", "_win32_hata_kodu", "altgr_karakteri"} <= sarmalayicilar
    for d in ast.walk(agac):
        if isinstance(d, ast.FunctionDef) and d.name not in sarmalayicilar and d.name != "_kullanici32":
            for n in ast.walk(d):
                assert not (isinstance(n, ast.Attribute) and n.attr in {"RegisterHotKey", "UnregisterHotKey", "ToUnicodeEx"}), d.name
