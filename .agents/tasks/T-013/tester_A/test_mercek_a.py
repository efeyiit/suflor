"""T-013 Tester-A (kor) -- mercek: DURUM MAKINESI + SINIR + GARANTI ALANI.

Hedef: `src/ui/kisayol.py` (docstring = garanti alani), `src/ui/uygulama.py` `calistir` baglantisi, `src/ui/kabuk.py`
T-013 ekleri. Paket v2 K1-K6. Gercek Win32 kisayol kaydi YOK (`SUFLOR_GERCEK_KISAYOL_YASAK=1`, conftest); Win32
dokunuslari yalniz: `PostThreadMessageW(kendi thread, WM_HOTKEY)` (surec ici sentetik mesaj -- gercek dagitici yolu,
`RegisterHotKey` yok) ve `altgr_karakteri` (saf `ToUnicodeEx` sorgusu, kayit yok).

Bolumler:
  A  durum makinesi (sahte Win32): cagri dizileri, ayni ad / ayni kombinasyon, 1409 / diger kodlar, kaldir_fn False,
     istisna, GECERSIZ/ALTGR sonrasi eski kayit, kimlik sayaci (iki servis, 0xBFFF sarma, tukenme)
  B  omur: del+gc, deleteLater, ebeveyn, hepsini_kaldir sonrasi cift kaldirma yok, pozitif kontrol (bagli yontem),
     removeNativeEventFilter sayimi, silinen servisin id'siyle gercek yol olayi, ZOMBI kaydet (PIN)
  C  filtre siniri: eventType turleri, yanlis tip mesaja dokunmaz (alt surec, pozitif kontrol cokme), wParam 0/2**64-1/
     0xC000, WM_HOTKEY disi, iki servis birbirinin olayini yutmaz (dogrudan + gercek dagitici yolu), yeniden giris
  D  dilbilgisi siniri: >= 70 ornekli tablo, Unicode/tam genislik/bosluk/NBSP, F0/F12/F25, kara liste, GECERSIZ vs
     ValueError siniflari, kanonik gidis-donus, kombinasyonu_yaz siniri
  E  AltGr: sahte fn (Ctrl+Alt sorulur, Shift'li/Ctrl+Alt'siz sorulmaz, istisna), gercek altgr_karakteri (saf sorgu)
     tablo tuslari bos, TR-Q harfleri, tampon temiz
  F  thread: kaydet/kaldir/hepsini_kaldir baska thread'den RuntimeError, sayac 0; ana thread OK
  G  calistir (sahte servis): tetiklendi ad tablosu, cikis_istendi -> hepsini_kaldir x1, kisayollar={}, ayni
     kombinasyon iki ad (PIN: "baska bir uygulama" yaniltici), sebep metinleri, etiketler, cikis kodu, Y1 kemeri

PIN = mevcut davranisi sabitleyen test; bulgu numarasiyla (O-A / D-A) raporda aciklanir.
Konsola ASCII disi basilmaz (parametrize id'leri ASCII).
"""
from __future__ import annotations

import ctypes
import functools
import gc
import os
import subprocess
import sys
import threading
import weakref
from collections.abc import Callable
from ctypes import wintypes
from pathlib import Path
from typing import Any

import pytest
from PySide6.QtCore import QByteArray, QCoreApplication, QObject, QThread
from PySide6.QtWidgets import QApplication

from src.ui import kisayol
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
    altgr_karakteri,
    kombinasyonu_coz,
    kombinasyonu_yaz,
)
from src.ui.uygulama import VARSAYILAN_KISAYOLLAR, calistir, kayit_sebebi

KOK = Path(__file__).resolve().parents[4]
OLAY_TIPI = b"windows_generic_MSG"
CA = MOD_CONTROL | MOD_ALT
CS = MOD_CONTROL | MOD_SHIFT
AS = MOD_ALT | MOD_SHIFT
CAS = MOD_CONTROL | MOD_ALT | MOD_SHIFT
KIMLIK_SON = 0xBFFF
ERR_1409 = 1409

_u32 = ctypes.WinDLL("user32", use_last_error=True)
_k32 = ctypes.WinDLL("kernel32", use_last_error=True)
_u32.PostThreadMessageW.argtypes = [wintypes.DWORD, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
_u32.PostThreadMessageW.restype = wintypes.BOOL
_u32.GetKeyboardLayout.argtypes = [wintypes.DWORD]
_u32.GetKeyboardLayout.restype = wintypes.HKL
_u32.MapVirtualKeyW.argtypes = [wintypes.UINT, wintypes.UINT]
_u32.MapVirtualKeyW.restype = wintypes.UINT
_u32.ToUnicodeEx.argtypes = [wintypes.UINT, wintypes.UINT, ctypes.POINTER(ctypes.c_ubyte), wintypes.LPWSTR, ctypes.c_int,
                             wintypes.UINT, wintypes.HKL]
_u32.ToUnicodeEx.restype = ctypes.c_int
_ANA_THREAD_ID = int(_k32.GetCurrentThreadId())


# ---------------------------------------------------------------- yardimcilar ---------------------------------------
class SahteWin32:
    """Enjekte edilen dort fonksiyonun gunluklu sahtesi. `gunluk` sirali: ("kayit", id, mod, vk) / ("kaldir", id) / ("altgr", vk)."""

    def __init__(
        self,
        *,
        kayit_sonucu: bool | Callable[[int, int, int], bool] = True,
        kaldir_sonucu: bool | Callable[[int], bool] = True,
        hata_kodu: int = 0,
        altgr: dict[int, str] | Callable[[int], str] | None = None,
    ) -> None:
        self.gunluk: list[tuple[Any, ...]] = []
        self._kayit_sonucu = kayit_sonucu
        self._kaldir_sonucu = kaldir_sonucu
        self.hata_kodu = hata_kodu
        self._altgr = altgr or {}

    def kayit(self, kimlik: int, mod: int, vk: int) -> bool:
        self.gunluk.append(("kayit", kimlik, mod, vk))
        return self._kayit_sonucu(kimlik, mod, vk) if callable(self._kayit_sonucu) else self._kayit_sonucu

    def kaldir(self, kimlik: int) -> bool:
        self.gunluk.append(("kaldir", kimlik))
        return self._kaldir_sonucu(kimlik) if callable(self._kaldir_sonucu) else self._kaldir_sonucu

    def hata(self) -> int:
        self.gunluk.append(("hata",))
        return self.hata_kodu

    def altgr(self, vk: int) -> str:
        self.gunluk.append(("altgr", vk))
        return self._altgr(vk) if callable(self._altgr) else self._altgr.get(vk, "")

    def servis(self, ebeveyn: QObject | None = None) -> KisayolServisi:
        return KisayolServisi(ebeveyn, kayit_fn=self.kayit, kaldir_fn=self.kaldir, hata_kodu_fn=self.hata,
                              altgr_karakteri_fn=self.altgr)

    @property
    def win32(self) -> list[tuple[Any, ...]]:
        """AltGr sorgulari disindaki (kayit/kaldir/hata) cagrilar, sirali."""
        return [g for g in self.gunluk if g[0] != "altgr"]

    @property
    def kayitlar(self) -> list[tuple[Any, ...]]:
        return [g for g in self.gunluk if g[0] == "kayit"]

    @property
    def kaldirmalar(self) -> list[int]:
        return [g[1] for g in self.gunluk if g[0] == "kaldir"]

    @property
    def altgr_sorgulari(self) -> list[int]:
        return [g[1] for g in self.gunluk if g[0] == "altgr"]

    def son_kimlik(self) -> int:
        return int(next(g for g in reversed(self.gunluk) if g[0] == "kayit")[1])


def mesaj(message: int = WM_HOTKEY, wparam: int = 0, lparam: int = 0) -> wintypes.MSG:
    m = wintypes.MSG()
    m.hwnd = None
    m.message = message
    m.wParam = wparam
    m.lParam = lparam
    return m


def filtrele(servis: KisayolServisi, m: wintypes.MSG, olay_tipi: Any = None) -> tuple[bool, int]:
    tip = QByteArray(OLAY_TIPI) if olay_tipi is None else olay_tipi
    return servis.filtre.nativeEventFilter(tip, ctypes.addressof(m))


def gercek_yol(kimlik: int) -> None:
    """Gercek dagitici yolu: kendi thread kuyruguna WM_HOTKEY (hwnd NULL, tipki RegisterHotKey(NULL) olayi). Kayit YOK."""
    assert _u32.PostThreadMessageW(_ANA_THREAD_ID, WM_HOTKEY, kimlik, 0)


def sinyal_kaydedici(servis: KisayolServisi) -> list[str]:
    alinan: list[str] = []
    servis.tetiklendi.connect(alinan.append)
    return alinan


def canli_kimlikler() -> set[int]:
    return set(kisayol._canli_kimlikler)


@pytest.fixture(autouse=True)
def _gercek_yasak_kemeri() -> None:
    assert os.environ.get("SUFLOR_GERCEK_KISAYOL_YASAK") == "1"


@pytest.fixture
def sahte() -> SahteWin32:
    return SahteWin32()


@pytest.fixture
def sok_sayaci(qapp: QApplication, monkeypatch: pytest.MonkeyPatch) -> list[object]:
    """`qapp.removeNativeEventFilter` sahtesi: cagrilari sayar, gercegine iletir (servis yapicisi bagli yontemi yakalar)."""
    gercek = qapp.removeNativeEventFilter
    sayac: list[object] = []

    def sahte_sok(f: object) -> None:
        sayac.append(f)
        gercek(f)  # type: ignore[arg-type]

    monkeypatch.setattr(qapp, "removeNativeEventFilter", sahte_sok)
    return sayac


@pytest.fixture
def kur_sayaci(qapp: QApplication, monkeypatch: pytest.MonkeyPatch) -> list[object]:
    gercek = qapp.installNativeEventFilter
    sayac: list[object] = []

    def sahte_kur(f: object) -> None:
        sayac.append(f)
        gercek(f)  # type: ignore[arg-type]

    monkeypatch.setattr(qapp, "installNativeEventFilter", sahte_kur)
    return sayac


# ====================================================================================================================
# A · DURUM MAKINESI (sahte Win32)
# ====================================================================================================================
def test_a_kaydet_ok_cagri_dizisi_norepeat_ve_son_hata_kodu(qapp: QApplication, sahte: SahteWin32) -> None:
    s = sahte.servis()
    assert s.kaydet("a", "Ctrl+Alt+D") is KayitSonucu.OK
    assert sahte.win32 == [("kayit", sahte.son_kimlik(), CA | MOD_NOREPEAT, 0x44)]
    assert s.kayitli() == {"a": "Ctrl+Alt+D"} and s.son_hata_kodu == 0
    assert 1 <= sahte.son_kimlik() <= KIMLIK_SON and sahte.son_kimlik() in canli_kimlikler()


def test_a_ayni_ad_yeniden_kaydet_once_eski_id_kaldirilir_sonra_yeni_id_kaydedilir(qapp: QApplication, sahte: SahteWin32) -> None:
    s = sahte.servis()
    s.kaydet("a", "Ctrl+Alt+D")
    eski = sahte.son_kimlik()
    sahte.gunluk.clear()
    assert s.kaydet("a", "Ctrl+Alt+R") is KayitSonucu.OK
    yeni = sahte.son_kimlik()
    assert sahte.win32 == [("kaldir", eski), ("kayit", yeni, CA | MOD_NOREPEAT, 0x52)]  # sira: kaldir ONCE, id ESKI id
    assert yeni != eski and s.kayitli() == {"a": "Ctrl+Alt+R"}
    assert eski not in canli_kimlikler() and yeni in canli_kimlikler()
    assert filtrele(s, mesaj(wparam=eski)) == (False, 0) and filtrele(s, mesaj(wparam=yeni)) == (True, 0)  # eski id artik bilinmez


def test_a_ayni_ad_ayni_kombinasyon_yeniden_kaydet_cakisma_degil_kaldir_sonra_kaydet(qapp: QApplication, sahte: SahteWin32) -> None:
    s = sahte.servis()
    s.kaydet("a", "Ctrl+Alt+D")
    eski = sahte.son_kimlik()
    sahte.gunluk.clear()
    assert s.kaydet("a", "ctrl + alt + d") is KayitSonucu.OK
    assert [g[0] for g in sahte.win32] == ["kaldir", "kayit"] and sahte.kaldirmalar == [eski]
    assert sahte.son_kimlik() != eski and s.kayitli() == {"a": "Ctrl+Alt+D"}


def test_a_ayni_kombinasyon_baska_ad_servis_ici_cakisma_win32_cagrilmaz_son_hata_kodu_degismez(qapp: QApplication) -> None:
    sahte = SahteWin32(kayit_sonucu=lambda i, m, v: v != 0x58, hata_kodu=ERR_1409)  # X -> 1409 (son_hata_kodu'nu 1409 yapmak icin)
    s = sahte.servis()
    assert s.kaydet("a", "Ctrl+Alt+D") is KayitSonucu.OK
    assert s.kaydet("x", "Ctrl+Alt+X") is KayitSonucu.CAKISMA and s.son_hata_kodu == ERR_1409
    sahte.gunluk.clear()
    for metin in ("Ctrl+Alt+D", "alt+ctrl+d", "CTRL+ALT+d", "Control+Alt+D"):
        assert s.kaydet("b", metin) is KayitSonucu.CAKISMA
    assert sahte.win32 == [] and s.kayitli() == {"a": "Ctrl+Alt+D"} and s.son_hata_kodu == ERR_1409


def test_a_servis_ici_cakisma_kimlik_tuketmez(qapp: QApplication, sahte: SahteWin32) -> None:
    s = sahte.servis()
    s.kaydet("a", "Ctrl+Alt+D")
    sayac0, canli0 = kisayol._sonraki_kimlik, canli_kimlikler()
    assert s.kaydet("b", "Ctrl+Alt+D") is KayitSonucu.CAKISMA
    assert kisayol._sonraki_kimlik == sayac0 and canli_kimlikler() == canli0


def test_a_PIN_O_A2_ayni_ad_baska_adin_kombinasyonuna_tasinirsa_cakisma_ve_eski_kayit_YOK_OLUR(qapp: QApplication, sahte: SahteWin32) -> None:
    """O-A2: servis ici CAKISMA saf tespit edilebilirken (Win32 gerekmez) `ad`in ESKI kaydi kaldiriliyor -- GECERSIZ/ALTGR
    yollarinda eski kayit korunur (docstring K1 (2)/(3)), CAKISMA yolunda (5) korunmaz. Docstring sirayi (4)->(5) yazar;
    bu test mevcut davranisi PIN'ler."""
    s = sahte.servis()
    s.kaydet("a", "Ctrl+Alt+D")
    s.kaydet("b", "Ctrl+Alt+R")
    id_a = sahte.kayitlar[0][1]
    sahte.gunluk.clear()
    assert s.kaydet("a", "Ctrl+Alt+R") is KayitSonucu.CAKISMA
    assert sahte.win32 == [("kaldir", id_a)]            # eski kayit Win32'den kaldirildi
    assert s.kayitli() == {"b": "Ctrl+Alt+R"}          # "a" artik yok (kaybedildi)
    assert filtrele(s, mesaj(wparam=id_a)) == (False, 0)


def test_a_kayit_fn_false_1409_cakisma_kayitlida_yok_kimlik_serbest(qapp: QApplication) -> None:
    sahte = SahteWin32(kayit_sonucu=False, hata_kodu=ERR_1409)
    s = sahte.servis()
    canli0 = canli_kimlikler()
    assert s.kaydet("a", "Ctrl+Alt+D") is KayitSonucu.CAKISMA
    assert s.son_hata_kodu == ERR_1409 and s.kayitli() == {}
    kimlik = sahte.son_kimlik()
    assert kimlik not in canli_kimlikler() and canli_kimlikler() == canli0
    assert [g[0] for g in sahte.win32] == ["kayit", "hata"]
    assert filtrele(s, mesaj(wparam=kimlik)) == (False, 0)  # reddedilen id bilinmiyor


@pytest.mark.parametrize("kod", [0, 1, 5, 87, 1400, 1408, 1410, 1419, 2**31 - 1, -1, 2**32 - 1])
def test_a_kayit_fn_false_1409_disi_kodlar_hata_ve_son_hata_kodu(qapp: QApplication, kod: int) -> None:
    sahte = SahteWin32(kayit_sonucu=False, hata_kodu=kod)
    s = sahte.servis()
    assert s.kaydet("a", "Ctrl+Alt+D") is KayitSonucu.HATA
    assert s.son_hata_kodu == kod and s.kayitli() == {}
    assert sahte.son_kimlik() not in canli_kimlikler()


def test_a_hata_sonrasi_basarili_kayit_son_hata_kodunu_sifirlar(qapp: QApplication) -> None:
    durum = {"basarisiz": True}
    sahte = SahteWin32(kayit_sonucu=lambda i, m, v: not durum["basarisiz"], hata_kodu=5)
    s = sahte.servis()
    assert s.kaydet("a", "Ctrl+Alt+D") is KayitSonucu.HATA and s.son_hata_kodu == 5
    durum["basarisiz"] = False
    assert s.kaydet("a", "Ctrl+Alt+D") is KayitSonucu.OK and s.son_hata_kodu == 0
    assert s.kaydet("b", "Shift+T") is KayitSonucu.GECERSIZ and s.son_hata_kodu == 0


def test_a_PIN_win32_1409_sonrasi_eski_kayit_geri_gelmez_docstring_olculmuyor_damgasi(qapp: QApplication) -> None:
    """Docstring K1: 'Win32 1409 SONRASI eski kayit geri GELMEZ ... [ÖLÇÜLMÜYOR]'. Burada olculdu: ayni ad yeniden kaydinda
    Win32 reddederse ad tablodan silinmis kalir (kayip). Belgeli davranis, PIN."""
    sahte = SahteWin32(kayit_sonucu=lambda i, m, v: v == 0x44, hata_kodu=ERR_1409)  # yalniz D kabul
    s = sahte.servis()
    assert s.kaydet("a", "Ctrl+Alt+D") is KayitSonucu.OK
    eski = sahte.son_kimlik()
    assert s.kaydet("a", "Ctrl+Alt+R") is KayitSonucu.CAKISMA
    assert s.kayitli() == {} and sahte.kaldirmalar == [eski]
    assert filtrele(s, mesaj(wparam=eski)) == (False, 0)


@pytest.mark.parametrize("yeni", ["Shift+T", "Win+D", "Ctrl+Alt+F12", "Alt+Tab", "", "Ctrl+Alt", "Ctrl+Alt+D+E", "Ctrl+Alt+Q"],
                         ids=["tek_shift", "win", "f12", "kara_liste", "bos", "tus_yok", "iki_tus", "altgr_q"])
def test_a_ayni_ad_gecersiz_veya_altgr_yeni_kombinasyon_eski_kayit_korunur_win32_cagrilmaz(qapp: QApplication, yeni: str) -> None:
    sahte = SahteWin32(altgr={0x51: "@"})
    s = sahte.servis()
    assert s.kaydet("a", "Ctrl+Alt+D") is KayitSonucu.OK
    eski = sahte.son_kimlik()
    sahte.gunluk.clear()
    sonuc = s.kaydet("a", yeni)
    assert sonuc in (KayitSonucu.GECERSIZ, KayitSonucu.ALTGR_CAKISMA)
    assert [g for g in sahte.gunluk if g[0] in ("kayit", "kaldir", "hata")] == []
    assert s.kayitli() == {"a": "Ctrl+Alt+D"} and s.son_hata_kodu == 0
    assert filtrele(s, mesaj(wparam=eski)) == (True, 0)  # eski kayit hala olay aliyor
    # pozitif kontrol: gecerli yeni kombinasyon eskiyi degistirir
    assert s.kaydet("a", "Ctrl+Alt+R") is KayitSonucu.OK and s.kayitli() == {"a": "Ctrl+Alt+R"}


def test_a_kaldir_fn_false_donerse_tablo_yine_silinir_ve_kombinasyon_yeniden_alinabilir(qapp: QApplication) -> None:
    sahte = SahteWin32(kaldir_sonucu=False)
    s = sahte.servis()
    s.kaydet("a", "Ctrl+Alt+D")
    kimlik = sahte.son_kimlik()
    s.kaldir("a")
    assert sahte.kaldirmalar == [kimlik] and s.kayitli() == {} and kimlik not in canli_kimlikler()
    assert filtrele(s, mesaj(wparam=kimlik)) == (False, 0)
    assert s.kaydet("b", "Ctrl+Alt+D") is KayitSonucu.OK  # servis ici cakisma yok


def test_a_kaldir_bilinmeyen_sessiz_ve_iki_kez_kaldir_tek_win32_cagrisi(qapp: QApplication, sahte: SahteWin32) -> None:
    s = sahte.servis()
    s.kaldir("yok")
    s.kaldir("")
    assert sahte.win32 == []
    s.kaydet("a", "Ctrl+Alt+D")
    kimlik = sahte.son_kimlik()
    s.kaldir("a")
    s.kaldir("a")
    assert sahte.kaldirmalar == [kimlik]


def test_a_hepsini_kaldir_idempotent_ve_her_id_bir_kez(qapp: QApplication, sahte: SahteWin32) -> None:
    s = sahte.servis()
    for ad, k in (("a", "Ctrl+Alt+D"), ("b", "Ctrl+Alt+R"), ("c", "Ctrl+Shift+F5")):
        s.kaydet(ad, k)
    idler = [g[1] for g in sahte.kayitlar]
    canli0 = canli_kimlikler()
    s.hepsini_kaldir()
    s.hepsini_kaldir()
    s.hepsini_kaldir()
    assert sorted(sahte.kaldirmalar) == sorted(idler) and s.kayitli() == {}
    assert canli_kimlikler() == canli0 - set(idler)
    for k in idler:
        assert filtrele(s, mesaj(wparam=k)) == (False, 0)
    s.kaydet("a", "Ctrl+Alt+D")  # bos servis yeniden kullanilabilir
    assert s.kayitli() == {"a": "Ctrl+Alt+D"}


def test_a_PIN_D_A1_hepsini_kaldir_kaldir_fn_istisna_atarsa_kalanlar_kaldirilmaz_ve_tablo_yarim(qapp: QApplication) -> None:
    """D-A1 (bilgi, sozlesme disi: `kaldir_fn -> bool`): ikinci id'de istisna -> `hepsini_kaldir` istisnayi iletir,
    ilk kaldirildi, ikinci tablodan dusmus ama Win32 cagrisi basarisiz, ucuncu tabloda kalir."""
    def patlak(kimlik: int) -> bool:
        if kimlik == hedef["id"]:
            raise OSError("sahte UnregisterHotKey patladi")
        return True

    hedef: dict[str, int] = {}
    sahte = SahteWin32(kaldir_sonucu=patlak)
    s = sahte.servis()
    for ad, k in (("a", "Ctrl+Alt+D"), ("b", "Ctrl+Alt+R"), ("c", "Ctrl+Alt+X")):
        s.kaydet(ad, k)
    id_a, id_b, id_c = (g[1] for g in sahte.kayitlar)
    hedef["id"] = id_b
    with pytest.raises(OSError):
        s.hepsini_kaldir()
    assert sahte.kaldirmalar == [id_a, id_b]      # c'ye hic ulasilmadi
    assert s.kayitli() == {"c": "Ctrl+Alt+X"}      # b tablodan dusmus (kaldirma denendi), c duruyor
    assert filtrele(s, mesaj(wparam=id_c)) == (True, 0)
    hedef["id"] = -1
    s.hepsini_kaldir()                             # ikinci deneme kalanlari temizler
    assert s.kayitli() == {} and sahte.kaldirmalar == [id_a, id_b, id_c]


def test_a_kayitli_kopya_disaridan_mutasyon_servisi_etkilemez(qapp: QApplication, sahte: SahteWin32) -> None:
    s = sahte.servis()
    s.kaydet("a", "Ctrl+Alt+D")
    k = s.kayitli()
    k["b"] = "Ctrl+Alt+R"
    k.pop("a")
    assert s.kayitli() == {"a": "Ctrl+Alt+D"} and s.kayitli() is not k
    assert s.kaydet("b", "Ctrl+Alt+R") is KayitSonucu.OK  # sahte "b" eklemek servis ici cakisma uretmedi


def test_a_ad_bos_dize_ve_uzun_unicode_ad_kabul(qapp: QApplication, sahte: SahteWin32) -> None:
    s = sahte.servis()
    assert s.kaydet("", "Ctrl+Alt+D") is KayitSonucu.OK
    assert s.kaydet("\u00e7\u011f\u0131\u00f6\u015f\u00fc" * 100, "Ctrl+Alt+R") is KayitSonucu.OK
    assert set(s.kayitli()) == {"", "\u00e7\u011f\u0131\u00f6\u015f\u00fc" * 100}
    s.hepsini_kaldir()
    assert s.kayitli() == {}


def test_a_PIN_kombinasyon_str_degilse_attributeerror_ilerler_gecersiz_degil(qapp: QApplication, sahte: SahteWin32) -> None:
    """Bilgi (tip ihlali): docstring 'bozuk METIN -> ValueError' der; str olmayan girdi ValueError degil AttributeError."""
    s = sahte.servis()
    with pytest.raises(AttributeError):
        s.kaydet("a", 5)  # type: ignore[arg-type]
    with pytest.raises(AttributeError):
        s.kaydet("a", None)  # type: ignore[arg-type]
    assert sahte.win32 == [] and s.kayitli() == {}


# -- kimlik sayaci ---------------------------------------------------------------------------------------------------
def test_a_kimlik_surec_genelinde_iki_servis_kumeleri_ayrik_ve_artan(qapp: QApplication) -> None:
    s1w, s2w = SahteWin32(), SahteWin32()
    s1, s2 = s1w.servis(), s2w.servis()
    for i, k in enumerate(("Ctrl+Alt+D", "Ctrl+Alt+R", "Ctrl+Alt+X")):
        s1.kaydet(f"a{i}", k)
        s2.kaydet(f"b{i}", k)  # ayni kombinasyon baska serviste: servis ici cakisma DEGIL (tablo servis basina)
    id1 = [g[1] for g in s1w.kayitlar]
    id2 = [g[1] for g in s2w.kayitlar]
    assert set(id1).isdisjoint(id2) and len(set(id1 + id2)) == 6
    assert sorted(id1 + id2) == id1[:1] + id2[:1] + id1[1:2] + id2[1:2] + id1[2:] + id2[2:]  # sirayla artan
    s1.hepsini_kaldir()
    assert sorted(s1w.kaldirmalar) == sorted(id1) and s2w.kaldirmalar == []  # yalniz kendi id'leri
    assert s2.kayitli() == {"b0": "Ctrl+Alt+D", "b1": "Ctrl+Alt+R", "b2": "Ctrl+Alt+X"}


def test_a_kimlik_sayaci_0xbfff_ustunde_1e_sarar_canli_kimligi_atlar_49k_dongu(qapp: QApplication) -> None:
    """Tam tur: baska bir servis bir id tutarken 0xBFFF kaydet dongusu -> hicbir id [1, 0xBFFF] disina cikmaz,
    sarma gozlenir, tutulan id verilmez, hepsi OK."""
    tutucu_w = SahteWin32()
    tutucu = tutucu_w.servis()
    tutucu.kaydet("tut", "Ctrl+Alt+D")
    tutulan = tutucu_w.son_kimlik()
    w = SahteWin32()
    s = w.servis()
    idler: list[int] = []
    sonuclar: set[KayitSonucu] = set()
    for _ in range(KIMLIK_SON):
        sonuclar.add(s.kaydet("x", "Ctrl+Alt+R"))  # ayni ad: kaldir + YENI id
        idler.append(w.son_kimlik())
    assert sonuclar == {KayitSonucu.OK}
    assert min(idler) >= 1 and max(idler) == KIMLIK_SON
    assert tutulan not in idler                      # canli kimlik atlandi
    sarma = [i for i in range(1, len(idler)) if idler[i] < idler[i - 1]]
    assert len(sarma) == 1 and idler[sarma[0] - 1] == KIMLIK_SON and idler[sarma[0]] >= 1
    assert len(set(idler)) == KIMLIK_SON - 1         # 0xBFFF deneme, tutulan haric her id tam bir kez (bir id ikinci kez)
    assert s.kayitli() == {"x": "Ctrl+Alt+R"} and tutucu.kayitli() == {"tut": "Ctrl+Alt+D"}
    assert filtrele(tutucu, mesaj(wparam=tutulan)) == (True, 0)
    s.hepsini_kaldir()
    tutucu.hepsini_kaldir()


def test_a_kimlik_tukenmesi_runtimeerror_kayit_fn_cagrilmaz(qapp: QApplication, monkeypatch: pytest.MonkeyPatch, sahte: SahteWin32) -> None:
    s = sahte.servis()
    monkeypatch.setattr(kisayol, "_canli_kimlikler", set(range(1, KIMLIK_SON + 1)))
    with pytest.raises(RuntimeError, match="tukendi"):
        s.kaydet("a", "Ctrl+Alt+D")
    assert sahte.kayitlar == [] and s.kayitli() == {}
    # bir kimlik bosalinca alinabilir
    kisayol._canli_kimlikler.discard(0x1234)
    assert s.kaydet("a", "Ctrl+Alt+D") is KayitSonucu.OK and sahte.son_kimlik() == 0x1234
    s.hepsini_kaldir()


# ====================================================================================================================
# B · OMUR
# ====================================================================================================================
def _sil(yol: str, servis: KisayolServisi, qtbot: Any) -> None:
    if yol == "del_gc":
        del servis
        gc.collect()
    else:
        servis.deleteLater()
        qtbot.wait(50)


@pytest.mark.parametrize("yol", ["del_gc", "deleteLater"])
def test_b_yikim_her_id_kaldirilir_filtre_bir_kez_sokulur_kimlikler_serbest(qapp: QApplication, qtbot: Any, yol: str, sok_sayaci: list[object]) -> None:
    w = SahteWin32()
    s = w.servis()
    for ad, k in (("a", "Ctrl+Alt+D"), ("b", "Ctrl+Alt+R"), ("c", "Alt+Shift+F3")):
        s.kaydet(ad, k)
    idler = [g[1] for g in w.kayitlar]
    filtre = s.filtre
    zayif = weakref.ref(s)
    _sil(yol, s, qtbot)
    del s
    gc.collect()
    assert sorted(w.kaldirmalar) == sorted(idler)
    assert sok_sayaci == [filtre]                                 # tam bir kez, ayni nesne
    assert canli_kimlikler().isdisjoint(idler)
    assert zayif() is None


def test_b_yikim_ebeveyn_del_gc_cocuk_servis_temizler(qapp: QApplication, sok_sayaci: list[object]) -> None:
    ebeveyn = QObject()
    w = SahteWin32()
    s = w.servis(ebeveyn)
    s.kaydet("a", "Ctrl+Alt+D")
    kimlik = w.son_kimlik()
    del ebeveyn
    gc.collect()
    assert w.kaldirmalar == [kimlik] and len(sok_sayaci) == 1 and kimlik not in canli_kimlikler()
    import shiboken6
    assert not shiboken6.isValid(s)


def test_b_yikim_ebeveyn_deleteLater_cocuk_servis_temizler(qapp: QApplication, qtbot: Any, sok_sayaci: list[object]) -> None:
    ebeveyn = QObject()
    w = SahteWin32()
    s = w.servis(ebeveyn)
    s.kaydet("a", "Ctrl+Alt+D")
    kimlik = w.son_kimlik()
    ebeveyn.deleteLater()
    qtbot.wait(50)
    assert w.kaldirmalar == [kimlik] and len(sok_sayaci) == 1
    del s, ebeveyn
    gc.collect()
    assert len(sok_sayaci) == 1  # ikinci kez sokulmadi


@pytest.mark.parametrize("yol", ["del_gc", "deleteLater"])
def test_b_hepsini_kaldir_sonrasi_yikim_cift_kaldirma_yok_filtre_yine_sokulur(qapp: QApplication, qtbot: Any, yol: str, sok_sayaci: list[object]) -> None:
    w = SahteWin32()
    s = w.servis()
    s.kaydet("a", "Ctrl+Alt+D")
    s.kaydet("b", "Ctrl+Alt+R")
    s.hepsini_kaldir()
    n = len(w.kaldirmalar)
    assert n == 2
    _sil(yol, s, qtbot)
    del s
    gc.collect()
    assert len(w.kaldirmalar) == n and len(sok_sayaci) == 1


def test_b_bos_servis_yikim_kaldir_fn_cagrilmaz_filtre_sokulur(qapp: QApplication, sok_sayaci: list[object]) -> None:
    w = SahteWin32()
    s = w.servis()
    del s
    gc.collect()
    assert w.win32 == [] and len(sok_sayaci) == 1


def _serbest_temizleyici(gunluk: list[str], *_: object) -> None:
    gunluk.append("kostu")


class _BagliYontemliKopya(QObject):
    """Pozitif kontrol (kural 10): `self.destroyed.connect(self._temizle)` -- PySide6 6.11'de kosmaz (KRT k5b A)."""

    def __init__(self, gunluk: list[str], ebeveyn: QObject | None = None) -> None:
        super().__init__(ebeveyn)
        self._gunluk = gunluk
        self.destroyed.connect(self._temizle)

    def _temizle(self, *_: object) -> None:
        self._gunluk.append("kostu")


class _PartialKopya(QObject):
    def __init__(self, gunluk: list[str], ebeveyn: QObject | None = None) -> None:
        super().__init__(ebeveyn)
        self.destroyed.connect(functools.partial(_serbest_temizleyici, gunluk))


@pytest.mark.parametrize("yol", ["del_gc", "deleteLater", "ebeveyn_del_gc"])
def test_b_pozitif_kontrol_bagli_yontem_alicisi_kosmaz_partial_kosar(qapp: QApplication, qtbot: Any, yol: str) -> None:
    sonuc: dict[str, list[str]] = {}
    for ad, sinif in (("bagli", _BagliYontemliKopya), ("partial", _PartialKopya)):
        gunluk: list[str] = []
        ebeveyn = QObject() if yol == "ebeveyn_del_gc" else None
        nesne = sinif(gunluk, ebeveyn)
        if yol == "ebeveyn_del_gc":
            del ebeveyn
            gc.collect()
        else:
            _sil(yol, nesne, qtbot)
        del nesne
        gc.collect()
        sonuc[ad] = gunluk
    assert sonuc == {"bagli": [], "partial": ["kostu"]}


def test_b_gercek_yol_olay_silinen_servise_ulasmaz_cokme_yok_pozitif_kontrol_once_ulasir(qapp: QApplication, qtbot: Any) -> None:
    w = SahteWin32()
    s = w.servis()
    alinan = sinyal_kaydedici(s)
    s.kaydet("a", "Ctrl+Alt+D")
    kimlik = w.son_kimlik()
    gercek_yol(kimlik)
    qtbot.wait(40)
    assert alinan == ["a"]                           # pozitif kontrol: gercek dagitici yolu filtreye ulasiyor
    del s
    gc.collect()
    gercek_yol(kimlik)                               # filtre sokuldu: kimseye ulasmamali, surec yasamali
    qtbot.wait(40)
    assert alinan == ["a"] and w.kaldirmalar == [kimlik]


def test_b_iki_servis_biri_silinince_digeri_olay_almaya_devam_eder(qapp: QApplication, qtbot: Any) -> None:
    w1, w2 = SahteWin32(), SahteWin32()
    s1, s2 = w1.servis(), w2.servis()
    a1, a2 = sinyal_kaydedici(s1), sinyal_kaydedici(s2)
    s1.kaydet("bir", "Ctrl+Alt+D")
    s2.kaydet("iki", "Ctrl+Alt+R")
    k1, k2 = w1.son_kimlik(), w2.son_kimlik()
    del s1
    gc.collect()
    gercek_yol(k1)
    gercek_yol(k2)
    qtbot.wait(40)
    assert a1 == [] and a2 == ["iki"]
    assert filtrele(s2, mesaj(wparam=k1)) == (False, 0)


def test_b_n_kurulum_dusurme_dongusu_filtre_sayimi_ve_canli_kimlikler_tabana_doner(qapp: QApplication, kur_sayaci: list[object], sok_sayaci: list[object]) -> None:
    canli0 = canli_kimlikler()
    for _ in range(25):
        w = SahteWin32()
        s = w.servis()
        s.kaydet("a", "Ctrl+Alt+D")
        s.kaydet("b", "Ctrl+Alt+R")
        del s
        gc.collect()
        assert len(w.kaldirmalar) == 2
    assert len(kur_sayaci) == 25 and len(sok_sayaci) == 25
    assert [id(f) for f in kur_sayaci] == [id(f) for f in sok_sayaci]
    assert canli_kimlikler() == canli0


def test_b_PIN_O_A1_yikim_sonrasi_tutulan_sarmalayicida_kaydet_OK_doner_kayit_fn_cagrilir_olay_gelmez_sizinti(qapp: QApplication, qtbot: Any, sok_sayaci: list[object]) -> None:
    """O-A1: `deleteLater` + Python referansi tutulurken (C++ olmus) `kaydet` RuntimeError vermek yerine OK doner:
    `kayit_fn` cagrilir (gercekte Win32 kaydi olur), filtre sokulmus (olay hic gelmez), `destroyed` bir daha kosmaz
    (kaldirilmaz), kimlik `_canli_kimlikler`de kalir; `kayitli()` yikimda kaldirilan eski kaydi da hala gosterir."""
    import shiboken6
    w = SahteWin32()
    s = w.servis()
    alinan = sinyal_kaydedici(s)
    s.kaydet("y", "Ctrl+Alt+Y")
    id_y = w.son_kimlik()
    s.deleteLater()
    qtbot.wait(50)
    assert not shiboken6.isValid(s) and w.kaldirmalar == [id_y] and len(sok_sayaci) == 1
    # zombi
    sonuc = s.kaydet("z", "Ctrl+Alt+Z")
    assert sonuc is KayitSonucu.OK                      # RuntimeError beklenirdi
    id_z = w.son_kimlik()
    assert id_z != id_y and w.kayitlar[-1] == ("kayit", id_z, CA | MOD_NOREPEAT, 0x5A)
    assert s.kayitli() == {"y": "Ctrl+Alt+Y", "z": "Ctrl+Alt+Z"}  # 'y' Win32'den kaldirilmis ama tabloda
    gercek_yol(id_z)
    qtbot.wait(40)
    assert alinan == []                                  # filtre yok: olay gelmez
    assert id_z in canli_kimlikler()                     # sizinti: kimse serbest birakmaz
    w.gunluk.clear()
    s.kaldir("z")                                        # el ile temizlik hala mumkun (sarmalayici tutuluyor)
    assert w.kaldirmalar == [id_z] and id_z not in canli_kimlikler()
    s.kaldir("y")
    assert w.kaldirmalar == [id_z, id_y]                 # 'y' IKINCI kez kaldirildi (cift kaldirma)


def test_b_deleteLater_sonrasi_sarmalayici_dususu_ikinci_temizlik_yapmaz(qapp: QApplication, qtbot: Any, sok_sayaci: list[object]) -> None:
    w = SahteWin32()
    s = w.servis()
    s.kaydet("a", "Ctrl+Alt+D")
    s.deleteLater()
    qtbot.wait(50)
    n = len(w.kaldirmalar)
    del s
    gc.collect()
    assert len(w.kaldirmalar) == n == 1 and len(sok_sayaci) == 1


def test_b_filtre_servise_zayif_referansla_baglidir_servis_dusunce_filtre_yasasa_da_sinyal_yok(qapp: QApplication) -> None:
    w = SahteWin32()
    s = w.servis()
    alinan = sinyal_kaydedici(s)
    s.kaydet("a", "Ctrl+Alt+D")
    kimlik = w.son_kimlik()
    filtre = s.filtre
    del s
    gc.collect()
    # filtre nesnesi elimizde: kimlik tablosu bosaltilmis -> False; servis weakref None
    assert filtre.nativeEventFilter(QByteArray(OLAY_TIPI), ctypes.addressof(mesaj(wparam=kimlik))) == (False, 0)
    assert alinan == []


# ====================================================================================================================
# C · FILTRE SINIRI
# ====================================================================================================================
@pytest.mark.parametrize("tip_yap", [lambda: QByteArray(OLAY_TIPI), lambda: OLAY_TIPI, lambda: bytearray(OLAY_TIPI),
                                     lambda: memoryview(OLAY_TIPI)], ids=["QByteArray", "bytes", "bytearray", "memoryview"])
def test_c_event_type_turleri_bilinen_id_sinyal_ve_true(qapp: QApplication, sahte: SahteWin32, tip_yap: Callable[[], Any]) -> None:
    s = sahte.servis()
    alinan = sinyal_kaydedici(s)
    s.kaydet("a", "Ctrl+Alt+D")
    kimlik = sahte.son_kimlik()
    assert filtrele(s, mesaj(wparam=kimlik), tip_yap()) == (True, 0)
    assert alinan == ["a"]


@pytest.mark.parametrize("tip", [b"", b"xcb_generic_event_t", b"windows_generic_MSG\x00", b"windows_generic_MSG2",
                                 b"Windows_generic_MSG", b"windows_generic_MS", b"windows_dispatcher_MSG"],
                         ids=["bos", "xcb", "sonda_nul", "fazla", "buyuk_harf", "eksik", "dispatcher"])
def test_c_yanlis_event_type_false_sinyal_yok(qapp: QApplication, sahte: SahteWin32, tip: bytes) -> None:
    s = sahte.servis()
    alinan = sinyal_kaydedici(s)
    s.kaydet("a", "Ctrl+Alt+D")
    kimlik = sahte.son_kimlik()
    assert filtrele(s, mesaj(wparam=kimlik), QByteArray(tip)) == (False, 0)
    assert filtrele(s, mesaj(wparam=kimlik), tip) == (False, 0)
    assert alinan == []


_ALT_SUREC_ON_EK = (
    "import os,sys; os.environ['QT_QPA_PLATFORM']='offscreen'; os.environ['SUFLOR_GERCEK_KISAYOL_YASAK']='1'; "
    f"sys.path.insert(0, {str(KOK)!r}); from PySide6.QtWidgets import QApplication; from PySide6.QtCore import QByteArray; "
    "from src.ui.kisayol import KisayolServisi; app=QApplication([]); "
    "s=KisayolServisi(kayit_fn=lambda *a: True, kaldir_fn=lambda i: True, hata_kodu_fn=lambda: 0, altgr_karakteri_fn=lambda v: ''); "
)


def test_c_yanlis_event_type_mesaja_dokunmaz_adres_0_ile_alt_surec_yasar(qapp: QApplication) -> None:
    """Docstring K2: yanlis tip -> 'mesaja DOKUNMADAN False'. Adres 0 verilir: dokunsaydi surec 0xC0000005 ile olurdu (KRT k9)."""
    kod = _ALT_SUREC_ON_EK + "print(s.filtre.nativeEventFilter(QByteArray(b'xcb_generic_event_t'), 0)); print(s.filtre.nativeEventFilter(b'', 0))"
    r = subprocess.run([sys.executable, "-c", kod], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, (r.returncode, r.stderr[-500:])
    assert r.stdout.split() == ["(False,", "0)", "(False,", "0)"]


def test_c_pozitif_kontrol_dogru_event_type_adres_0_alt_sureci_oldurur_kural_10(qapp: QApplication) -> None:
    """Kural 10: 'dokunmaz' olcusunun ateslenebildigi gosterilir -- dogru tip + adres 0 = erisim ihlali (0xC0000005)."""
    kod = _ALT_SUREC_ON_EK + "print(s.filtre.nativeEventFilter(QByteArray(b'windows_generic_MSG'), 0))"
    r = subprocess.run([sys.executable, "-c", kod], capture_output=True, text=True, timeout=60)
    assert r.returncode in (3221225477, -1073741819)  # STATUS_ACCESS_VIOLATION
    assert "(False" not in r.stdout


@pytest.mark.parametrize("wparam", [0, 2**64 - 1, 2**63, 0xC000, 0xFFFF, KIMLIK_SON + 1],
                         ids=["0", "max64", "2e63", "0xC000_sistem", "0xFFFF", "0xC000_2"])
def test_c_wm_hotkey_bilinmeyen_wparam_false_sinyal_yok(qapp: QApplication, sahte: SahteWin32, wparam: int) -> None:
    s = sahte.servis()
    alinan = sinyal_kaydedici(s)
    s.kaydet("a", "Ctrl+Alt+D")
    assert filtrele(s, mesaj(wparam=wparam)) == (False, 0) and alinan == []


def test_c_wparam_negatif_atanamaz_sarar_ve_bilinmez(qapp: QApplication, sahte: SahteWin32) -> None:
    s = sahte.servis()
    alinan = sinyal_kaydedici(s)
    s.kaydet("a", "Ctrl+Alt+D")
    m = mesaj()
    m.wParam = -1
    assert int(m.wParam) == 2**64 - 1                    # WPARAM isaretsiz: -1 diye bir id yok
    assert filtrele(s, m) == (False, 0) and alinan == []
    m.wParam = -(2**64) + sahte.son_kimlik()             # tam sarma bilinen id'ye denk gelir -> bilinir
    assert int(m.wParam) == sahte.son_kimlik() and filtrele(s, m) == (True, 0) and alinan == ["a"]


@pytest.mark.parametrize("ileti", [0x0000, 0x0100, 0x0101, 0x0311, 0x0313, 0x0312 | 0x10000, 0xFFFF],
                         ids=["WM_NULL", "WM_KEYDOWN", "WM_KEYUP", "0x311", "0x313", "0x10312", "0xFFFF"])
def test_c_wm_hotkey_disi_ileti_bilinen_id_ile_false(qapp: QApplication, sahte: SahteWin32, ileti: int) -> None:
    s = sahte.servis()
    alinan = sinyal_kaydedici(s)
    s.kaydet("a", "Ctrl+Alt+D")
    assert filtrele(s, mesaj(message=ileti, wparam=sahte.son_kimlik())) == (False, 0) and alinan == []


@pytest.mark.parametrize("lparam", [0, 1, -1, 2**63 - 1, -(2**63), (0x44 << 16) | CA], ids=["0", "1", "-1", "max", "min", "makelparam"])
def test_c_lparam_onemsiz_bilinen_id_true(qapp: QApplication, sahte: SahteWin32, lparam: int) -> None:
    s = sahte.servis()
    alinan = sinyal_kaydedici(s)
    s.kaydet("a", "Ctrl+Alt+D")
    assert filtrele(s, mesaj(wparam=sahte.son_kimlik(), lparam=lparam)) == (True, 0) and alinan == ["a"]


def test_c_iki_servis_birbirinin_id_sini_yutmaz_dogrudan_ve_gercek_yol(qapp: QApplication, qtbot: Any) -> None:
    w1, w2 = SahteWin32(), SahteWin32()
    s1, s2 = w1.servis(), w2.servis()   # s2 SON kurulan: Qt onu once cagirir
    a1, a2 = sinyal_kaydedici(s1), sinyal_kaydedici(s2)
    s1.kaydet("bir", "Ctrl+Alt+D")
    s2.kaydet("iki", "Ctrl+Alt+R")
    k1, k2 = w1.son_kimlik(), w2.son_kimlik()
    assert filtrele(s2, mesaj(wparam=k1)) == (False, 0) and filtrele(s1, mesaj(wparam=k2)) == (False, 0)
    assert a1 == [] and a2 == []
    gercek_yol(k1)
    gercek_yol(k2)
    gercek_yol(k1)
    qtbot.wait(50)
    assert a1 == ["bir", "bir"] and a2 == ["iki"]        # her olay tam bir servise, tam bir kez


def test_c_hepsini_kaldir_sonrasi_filtre_kurulu_ama_bilinen_id_yok_false_gercek_yol_sinyal_yok(qapp: QApplication, qtbot: Any, sahte: SahteWin32) -> None:
    s = sahte.servis()
    alinan = sinyal_kaydedici(s)
    s.kaydet("a", "Ctrl+Alt+D")
    kimlik = sahte.son_kimlik()
    s.hepsini_kaldir()
    assert filtrele(s, mesaj(wparam=kimlik)) == (False, 0)
    gercek_yol(kimlik)
    qtbot.wait(40)
    assert alinan == []
    s.kaydet("a", "Ctrl+Alt+D")                          # yeniden kayit: yeni id calisir, eski calismaz
    yeni = sahte.son_kimlik()
    assert yeni != kimlik
    gercek_yol(yeni)
    gercek_yol(kimlik)
    qtbot.wait(40)
    assert alinan == ["a"]


def test_c_filtre_bir_kez_kurulur_ayni_nesne_ve_kaldir_sonrasi_eski_id_bilinmez(qapp: QApplication, kur_sayaci: list[object], sahte: SahteWin32) -> None:
    s = sahte.servis()
    assert kur_sayaci == [s.filtre]
    s.kaydet("a", "Ctrl+Alt+D")
    s.kaydet("b", "Ctrl+Alt+R")
    s.kaldir("a")
    assert kur_sayaci == [s.filtre] and s.filtre is s.filtre
    ida, idb = (g[1] for g in sahte.kayitlar)
    assert filtrele(s, mesaj(wparam=ida)) == (False, 0) and filtrele(s, mesaj(wparam=idb)) == (True, 0)


def test_c_sinyal_es_zamanli_ve_ad_tam_dize(qapp: QApplication, sahte: SahteWin32) -> None:
    s = sahte.servis()
    gorulen: list[tuple[str, type]] = []
    s.tetiklendi.connect(lambda ad: gorulen.append((ad, type(ad))))
    s.kaydet("Anl\u0131k \u00c7evir", "Ctrl+Alt+D")
    sonuc = filtrele(s, mesaj(wparam=sahte.son_kimlik()))
    assert gorulen == [("Anl\u0131k \u00c7evir", str)] and sonuc == (True, 0)  # emit donmeden once alici kostu


def test_c_alicida_yeniden_giris_kaldir_ve_kaydet_filtre_icinde_guvenli(qapp: QApplication, qtbot: Any, sahte: SahteWin32) -> None:
    s = sahte.servis()
    alinan: list[str] = []

    def alici(ad: str) -> None:
        alinan.append(ad)
        s.kaldir(ad)                       # kendi kaydini filtre icinde kaldir
        s.kaydet("yeni", "Ctrl+Alt+R")     # ve yenisini ekle

    s.tetiklendi.connect(alici)
    s.kaydet("a", "Ctrl+Alt+D")
    ida = sahte.son_kimlik()
    assert filtrele(s, mesaj(wparam=ida)) == (True, 0)
    assert alinan == ["a"] and s.kayitli() == {"yeni": "Ctrl+Alt+R"}
    assert filtrele(s, mesaj(wparam=ida)) == (False, 0)
    gercek_yol(sahte.son_kimlik())
    qtbot.wait(40)
    assert alinan == ["a", "yeni"] and s.kayitli() == {"yeni": "Ctrl+Alt+R"}


def test_c_PIN_alici_istisnasi_filtreyi_bozmaz_true_doner(qapp: QApplication, qtbot: Any, sahte: SahteWin32) -> None:
    """Bilgi: alici istisnasi emit sinirinda yakalanir (pytest-qt kancasi / Qt: stderr), filtre (True, 0) doner, tablo bozulmaz."""
    s = sahte.servis()

    def patlak(ad: str) -> None:
        raise ValueError("alici patladi")

    s.tetiklendi.connect(patlak)
    s.kaydet("a", "Ctrl+Alt+D")
    with qtbot.capture_exceptions() as yakalanan:
        sonuc = filtrele(s, mesaj(wparam=sahte.son_kimlik()))
    assert sonuc == (True, 0)
    assert len(yakalanan) == 1 and "alici patladi" in str(yakalanan[0][1])
    assert s.kayitli() == {"a": "Ctrl+Alt+D"}


def test_c_ayni_wparam_ust_uste_100_olay_100_sinyal(qapp: QApplication, qtbot: Any, sahte: SahteWin32) -> None:
    s = sahte.servis()
    alinan = sinyal_kaydedici(s)
    s.kaydet("a", "Ctrl+Alt+D")
    k = sahte.son_kimlik()
    for _ in range(100):
        gercek_yol(k)
    qtbot.wait(100)
    assert alinan == ["a"] * 100


# ====================================================================================================================
# D · DILBILGISI SINIRI
# ====================================================================================================================
OK = "ok"
GEC = "gecersiz"    # GecersizKombinasyon (ValueError alt sinifi)
VAL = "valueerror"  # duz ValueError (GecersizKombinasyon DEGIL)

DILBILGISI: list[tuple[str, str, str, tuple[int, int] | None]] = [
    # id, metin, beklenen, (mod, vk)
    ("temel", "Ctrl+Alt+D", OK, (CA, 0x44)),
    ("bosluklu", "ctrl + alt + d", OK, (CA, 0x44)),
    ("sira", "Alt+Ctrl+D", OK, (CA, 0x44)),
    ("buyuk", "CTRL+ALT+D", OK, (CA, 0x44)),
    ("control", "Control+Alt+D", OK, (CA, 0x44)),
    ("sekme", "Ctrl\t+\tAlt+\tD", OK, (CA, 0x44)),
    ("cevre_bosluk", "  Ctrl+Alt+D  ", OK, (CA, 0x44)),
    ("nbsp_strip", "Ctrl+Alt+\u00a0D\u00a0", OK, (CA, 0x44)),           # strip() Unicode bosluk siyirir -> ASCII kalir
    ("ctrl_shift", "Ctrl+Shift+D", OK, (CS, 0x44)),
    ("alt_shift", "Alt+Shift+D", OK, (AS, 0x44)),
    ("uclu", "Ctrl+Alt+Shift+D", OK, (CAS, 0x44)),
    ("uclu_sira", "Shift+Alt+Ctrl+D", OK, (CAS, 0x44)),
    ("rakam_0", "Ctrl+Alt+0", OK, (CA, 0x30)),
    ("rakam_9", "Ctrl+Shift+9", OK, (CS, 0x39)),
    ("harf_i_kucuk", "ctrl+alt+i", OK, (CA, 0x49)),                  # Python upper() yerelden bagimsiz: i -> I (Turkce tuzagi yok)
    ("space", "Ctrl+Alt+Space", OK, (CA, 0x20)),
    ("space_kucuk", "ctrl+alt+space", OK, (CA, 0x20)),
    ("enter", "Ctrl+Alt+Enter", OK, (CA, 0x0D)),
    ("return", "Ctrl+Alt+Return", OK, (CA, 0x0D)),
    ("esc_ca", "Ctrl+Alt+Esc", OK, (CA, 0x1B)),
    ("escape_ca", "Ctrl+Alt+Escape", OK, (CA, 0x1B)),
    ("tab_ca", "Ctrl+Alt+Tab", OK, (CA, 0x09)),
    ("tab_as", "Alt+Shift+Tab", OK, (AS, 0x09)),                     # kara liste TAM esleme: Alt+Shift+Tab serbest (bilgi)
    ("backspace", "Ctrl+Alt+Backspace", OK, (CA, 0x08)),
    ("delete_cs", "Ctrl+Shift+Delete", OK, (CS, 0x2E)),
    ("del_cas", "Ctrl+Alt+Shift+Del", OK, (CAS, 0x2E)),              # Ctrl+Alt+Shift+Delete kara listede degil (tam esleme)
    ("insert", "Ctrl+Alt+Insert", OK, (CA, 0x2D)),
    ("ins", "Ctrl+Alt+Ins", OK, (CA, 0x2D)),
    ("home", "Ctrl+Alt+Home", OK, (CA, 0x24)),
    ("end", "Ctrl+Alt+End", OK, (CA, 0x23)),
    ("pageup", "Ctrl+Alt+PageUp", OK, (CA, 0x21)),
    ("pgup", "Ctrl+Alt+PgUp", OK, (CA, 0x21)),
    ("pagedown", "Ctrl+Alt+PageDown", OK, (CA, 0x22)),
    ("pgdn", "Ctrl+Alt+PgDn", OK, (CA, 0x22)),
    ("left", "Ctrl+Alt+Left", OK, (CA, 0x25)),
    ("up", "Ctrl+Alt+Up", OK, (CA, 0x26)),
    ("right", "Ctrl+Alt+Right", OK, (CA, 0x27)),
    ("down", "Ctrl+Alt+Down", OK, (CA, 0x28)),
    ("f1_ca", "Ctrl+Alt+F1", OK, (CA, 0x70)),
    ("f1_alt", "Alt+F1", OK, (MOD_ALT, 0x70)),
    ("f1_shift", "Shift+F1", OK, (MOD_SHIFT, 0x70)),
    ("f11_ctrl", "Ctrl+F11", OK, (MOD_CONTROL, 0x7A)),
    ("f01_esnek", "Ctrl+Alt+F01", OK, (CA, 0x70)),                   # 'F01' -> int -> F1 (esnek; bilgi)
    ("f5_uclu", "Ctrl+Alt+Shift+F5", OK, (CAS, 0x74)),
    ("alt_shift_space", "Alt+Shift+Space", OK, (AS, 0x20)),          # kara liste yalniz Alt+Space
    # -- GecersizKombinasyon --
    ("f1_yalniz", "F1", GEC, None),
    ("f12_ca", "Ctrl+Alt+F12", GEC, None),
    ("f12_yalniz", "F12", GEC, None),
    ("f12_kucuk", "ctrl+alt+f12", GEC, None),
    ("win", "Win+D", GEC, None),
    ("meta", "Meta+D", GEC, None),
    ("windows", "Windows+D", GEC, None),
    ("super", "Super+D", GEC, None),
    ("win_uclu", "Win+Ctrl+Alt+D", GEC, None),
    ("win_f1", "Win+F1", GEC, None),
    ("shift_tek", "Shift+T", GEC, None),
    ("ctrl_tek", "Ctrl+T", GEC, None),
    ("alt_tek", "Alt+T", GEC, None),
    ("degistiricisiz", "D", GEC, None),
    ("space_tek", "Space", GEC, None),
    ("shift_space", "Shift+Space", GEC, None),
    ("ctrl_space", "Ctrl+Space", GEC, None),
    ("kara_alt_tab", "Alt+Tab", GEC, None),
    ("kara_alt_tab_kucuk", "alt+tab", GEC, None),
    ("kara_alt_f4", "Alt+F4", GEC, None),
    ("kara_alt_esc", "Alt+Esc", GEC, None),
    ("kara_alt_escape", "Alt+Escape", GEC, None),
    ("kara_alt_space", "Alt+Space", GEC, None),
    ("kara_ctrl_esc", "Ctrl+Esc", GEC, None),
    ("kara_ctrl_alt_delete", "Ctrl+Alt+Delete", GEC, None),
    ("kara_ctrl_alt_del", "ctrl+alt+del", GEC, None),
    ("kara_alt_ctrl_delete", "Alt+Ctrl+Delete", GEC, None),
    ("kara_ctrl_shift_esc", "Ctrl+Shift+Esc", GEC, None),
    ("kara_ctrl_shift_escape", "Shift+Ctrl+Escape", GEC, None),
    # -- duz ValueError --
    ("bos", "", VAL, None),
    ("yalniz_arti", "+", VAL, None),
    ("arti_tusu", "Ctrl+Alt++", VAL, None),
    ("bos_parca", "Ctrl++Alt+D", VAL, None),
    ("sonda_arti", "Ctrl+Alt+D+", VAL, None),
    ("basta_arti", "+Ctrl+Alt+D", VAL, None),
    ("tus_yok", "Ctrl+Alt", VAL, None),
    ("tekrar_ctrl", "Ctrl+Ctrl+D", VAL, None),
    ("tekrar_control", "Ctrl+Control+D", VAL, None),
    ("tekrar_alt", "Alt+Alt+D", VAL, None),
    ("iki_tus", "Ctrl+Alt+D+E", VAL, None),
    ("iki_harf", "Ctrl+Alt+DD", VAL, None),
    ("unicode_c", "Ctrl+Alt+\u00c7", VAL, None),
    ("unicode_i_noktasiz", "ctrl+alt+\u0131", VAL, None),
    ("unicode_I_noktali", "Ctrl+Alt+\u0130", VAL, None),
    ("tam_genislik_D", "Ctrl+Alt+\uff24", VAL, None),
    ("tam_genislik_arti", "Ctrl\uff0bAlt\uff0bD", VAL, None),
    ("unicode_degistirici", "Ctr\u0142+Alt+D", VAL, None),
    ("nul", "Ctrl+Alt+D\x00", VAL, None),
    ("f0", "Ctrl+Alt+F0", VAL, None),
    ("f13", "Ctrl+Alt+F13", VAL, None),
    ("f25", "Ctrl+Alt+F25", VAL, None),
    ("f_negatif", "Ctrl+Alt+F-1", VAL, None),
    ("f_harf", "Ctrl+Alt+FA", VAL, None),
    ("numpad", "Ctrl+Alt+Numpad0", VAL, None),
    ("printscreen", "Ctrl+Alt+PrintScreen", VAL, None),
    ("tire_ayirici", "Ctrl-Alt-D", VAL, None),
    ("bosluk_ayirici", "Ctrl Alt D", VAL, None),
    ("altgr_adi", "AltGr+D", VAL, None),
    ("cmd", "Cmd+Alt+D", VAL, None),
    ("noktali_virgul", "Ctrl+Alt+;", VAL, None),
    ("rakam_10", "Ctrl+Alt+10", VAL, None),
]


@pytest.mark.parametrize(("metin", "beklenen", "cift"), [(m, b, c) for _, m, b, c in DILBILGISI], ids=[i for i, *_ in DILBILGISI])
def test_d_dilbilgisi_tablosu(metin: str, beklenen: str, cift: tuple[int, int] | None) -> None:
    if beklenen == OK:
        assert kombinasyonu_coz(metin) == cift
        assert KisayolServisi.kombinasyonu_coz(metin) == cift
        assert cift is not None and not cift[0] & MOD_NOREPEAT
    elif beklenen == GEC:
        with pytest.raises(GecersizKombinasyon):
            kombinasyonu_coz(metin)
    else:
        with pytest.raises(ValueError) as bilgi:
            kombinasyonu_coz(metin)
        assert not isinstance(bilgi.value, GecersizKombinasyon), "duz ValueError beklenirdi, GecersizKombinasyon geldi"


def test_d_tablo_buyuklugu_ve_sinif_dagilimi() -> None:
    assert len(DILBILGISI) >= 40
    assert len({m for _, m, *_ in DILBILGISI}) == len(DILBILGISI)
    assert sum(1 for *_, b, _ in DILBILGISI if b == OK) >= 20
    assert sum(1 for *_, b, _ in DILBILGISI if b == GEC) >= 15
    assert sum(1 for *_, b, _ in DILBILGISI if b == VAL) >= 15


@pytest.mark.parametrize(("metin", "cift"), [(m, c) for _, m, b, c in DILBILGISI if b == OK], ids=[i for i, _, b, _ in DILBILGISI if b == OK])
def test_d_kanonik_gidis_donus(metin: str, cift: tuple[int, int]) -> None:
    kanonik = kombinasyonu_yaz(*cift)
    assert kombinasyonu_coz(kanonik) == cift
    assert kanonik == kombinasyonu_yaz(*kombinasyonu_coz(kanonik))
    parcalar = kanonik.split("+")
    assert parcalar == [p for p in ("Ctrl", "Alt", "Shift") if p in parcalar] + parcalar[-1:]  # Ctrl+Alt+Shift+<Tus> sirasi
    assert " " not in kanonik and kanonik.isascii() and parcalar[-1] not in ("Control", "Escape", "Return", "Del", "Ins", "PgUp", "PgDn")


@pytest.mark.parametrize(("metin", "beklenen"), [(m, b) for _, m, b, _ in DILBILGISI if b != OK], ids=[i for i, _, b, _ in DILBILGISI if b != OK])
def test_d_kaydet_her_iki_sinif_gecersiz_win32_cagrilmaz_altgr_sorulmaz(qapp: QApplication, sahte: SahteWin32, metin: str, beklenen: str) -> None:
    s = sahte.servis()
    assert s.kaydet("a", metin) is KayitSonucu.GECERSIZ
    assert sahte.gunluk == [] and s.kayitli() == {} and s.son_hata_kodu == 0  # altgr da sorulmaz


@pytest.mark.parametrize(("mod", "vk"), [(CA | MOD_NOREPEAT, 0x44), (kisayol.MOD_WIN, 0x44), (CA, 0x7B), (CA, 0x00), (CA, 0x7C),
                                          (CA, 0xFF), (CA, ord("a")), (0x10, 0x44), (-1, 0x44), (CA, -1)],
                         ids=["norepeat_biti", "win", "f12", "vk0", "f13", "vkFF", "kucuk_a", "bit_0x10", "mod_-1", "vk_-1"])
def test_d_kombinasyonu_yaz_dilbilgisi_disi_valueerror(mod: int, vk: int) -> None:
    with pytest.raises(ValueError):
        kombinasyonu_yaz(mod, vk)


def test_d_PIN_kombinasyonu_yaz_degistirici_kuralini_denetlemez_coz_reddeder() -> None:
    """Bilgi: `kombinasyonu_yaz` yalniz bit/vk tablosunu denetler; `(0, D)` -> "D", `(Shift, T)` -> "Shift+T" uretir,
    `kombinasyonu_coz` ikisini de GecersizKombinasyon ile reddeder (gidis-donus yalniz coz'un kabul ettigi ciftlerde)."""
    assert kombinasyonu_yaz(0, 0x44) == "D" and kombinasyonu_yaz(MOD_SHIFT, 0x54) == "Shift+T"
    assert kombinasyonu_yaz(MOD_ALT, 0x09) == "Alt+Tab"
    for m in ("D", "Shift+T", "Alt+Tab"):
        with pytest.raises(GecersizKombinasyon):
            kombinasyonu_coz(m)


@pytest.mark.parametrize("metin", ["Ctrl+Alt+" + "D" * 10**6, "+" * 10**6, "Ctrl+Alt+D" + "+" * 10**5, "Ctrl+" * 10**5 + "D"],
                         ids=["uzun_tus", "milyon_arti", "sonda_100k_arti", "100k_ctrl"])
def test_d_cok_uzun_metin_valueerror_hizli(metin: str) -> None:
    import time
    t0 = time.perf_counter()
    with pytest.raises(ValueError):
        kombinasyonu_coz(metin)
    assert time.perf_counter() - t0 < 2.0


def test_d_gecersiz_kombinasyon_valueerror_alt_sinifi_ve_saf() -> None:
    assert issubclass(GecersizKombinasyon, ValueError)
    for _ in range(3):
        assert kombinasyonu_coz("Ctrl+Alt+D") == (CA, 0x44)  # tekrar cagri ayni sonuc, durum yok
    assert kombinasyonu_coz("Ctrl+Alt+D") == KisayolServisi.kombinasyonu_coz("Ctrl+Alt+D")


def test_d_harf_ve_rakam_tam_kume_kabul_ve_cift_esleme() -> None:
    for h in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789":
        assert kombinasyonu_coz(f"Ctrl+Alt+{h}") == (CA, ord(h))
        assert kombinasyonu_coz(f"ctrl+shift+{h.lower()}") == (CS, ord(h))
    for n in range(1, 12):
        assert kombinasyonu_coz(f"Shift+F{n}") == (MOD_SHIFT, 0x70 + n - 1)
        assert kombinasyonu_coz(f"Ctrl+Alt+F{n}") == (CA, 0x70 + n - 1)


# ====================================================================================================================
# E · ALTGR
# ====================================================================================================================
def test_e_sahte_altgr_ctrl_alt_shiftsiz_sorulur_cakisma_win32_cagrilmaz(qapp: QApplication) -> None:
    sahte = SahteWin32(altgr={0x54: "\u20ba"})
    s = sahte.servis()
    s.kaydet("eski", "Ctrl+Alt+D")
    sahte.gunluk.clear()
    assert s.kaydet("t", "Ctrl+Alt+T") is KayitSonucu.ALTGR_CAKISMA
    assert sahte.gunluk == [("altgr", 0x54)] and s.kayitli() == {"eski": "Ctrl+Alt+D"} and s.son_hata_kodu == 0
    assert s.kaydet("t", "Alt+Ctrl+T") is KayitSonucu.ALTGR_CAKISMA  # sira farki yok


@pytest.mark.parametrize("metin", ["Ctrl+Alt+Shift+T", "Ctrl+Shift+T", "Alt+Shift+T", "Ctrl+F1", "Alt+F2", "Shift+F3"],
                         ids=["cas", "cs", "as", "ctrl_f1", "alt_f2", "shift_f3"])
def test_e_sahte_altgr_shiftli_veya_ctrl_altsiz_sorulmaz_ok(qapp: QApplication, metin: str) -> None:
    sahte = SahteWin32(altgr=lambda vk: "\u20ba")  # HER tus icin dolu dese de sorulmamali
    s = sahte.servis()
    assert s.kaydet("x", metin) is KayitSonucu.OK
    assert sahte.altgr_sorgulari == [] and len(sahte.kayitlar) == 1


@pytest.mark.parametrize("metin", ["Ctrl+Alt+R", "Ctrl+Alt+F5", "Ctrl+Alt+Space", "Ctrl+Alt+Tab", "Ctrl+Alt+Left"],
                         ids=["r", "f5", "space", "tab", "left"])
def test_e_sahte_altgr_bos_ok_bir_kez_sorulur_vk_dogru(qapp: QApplication, sahte: SahteWin32, metin: str) -> None:
    s = sahte.servis()
    mod, vk = kombinasyonu_coz(metin)
    assert s.kaydet("x", metin) is KayitSonucu.OK
    assert sahte.altgr_sorgulari == [vk] and sahte.kayitlar[0][3] == vk


def test_e_sahte_altgr_f_tusu_ve_bosluk_karakteri_de_cakisma_sayilir(qapp: QApplication) -> None:
    """fn Ctrl+Alt'li HER tus icin sorulur; bos olmayan her dize (bosluk dahil) cakismadir (bilgi)."""
    sahte = SahteWin32(altgr={0x74: "x", 0x20: " "})
    s = sahte.servis()
    assert s.kaydet("f5", "Ctrl+Alt+F5") is KayitSonucu.ALTGR_CAKISMA
    assert s.kaydet("sp", "Ctrl+Alt+Space") is KayitSonucu.ALTGR_CAKISMA
    assert sahte.kayitlar == []


def test_e_PIN_sahte_altgr_istisna_atarsa_kaydet_iletir_tablo_bozulmaz(qapp: QApplication) -> None:
    """Bilgi (sozlesme disi: `altgr_karakteri_fn -> str`): istisna `kaydet`ten cikar; eski kayit korunur, Win32 cagrilmaz."""
    def patlak(vk: int) -> str:
        raise OSError("ToUnicodeEx patladi")

    sahte = SahteWin32(altgr=patlak)
    s = sahte.servis()
    assert s.kaydet("a", "Ctrl+Shift+D") is KayitSonucu.OK  # sorulmaz
    with pytest.raises(OSError):
        s.kaydet("a", "Ctrl+Alt+D")
    assert s.kayitli() == {"a": "Ctrl+Shift+D"} and len(sahte.kayitlar) == 1 and sahte.kaldirmalar == []


def _duz_karakter(vk: int) -> tuple[int, str]:
    hkl = _u32.GetKeyboardLayout(0)
    durum = (ctypes.c_ubyte * 256)()
    tampon = ctypes.create_unicode_buffer(8)
    n = int(_u32.ToUnicodeEx(vk, _u32.MapVirtualKeyW(vk, 0), durum, tampon, 8, 0, hkl))
    return n, tampon.value[: max(n, 0)]


def _duzen() -> int:
    return int(_u32.GetKeyboardLayout(0)) & 0xFFFF


def test_e_gercek_altgr_saf_sorgu_yasak_degiskeniyle_calisir_ve_kayit_yapmaz(qapp: QApplication) -> None:
    assert os.environ.get("SUFLOR_GERCEK_KISAYOL_YASAK") == "1"
    for vk in (0x44, 0x54, 0x20, 0x00, 0xFF, 0x5B, 0x5C, 0x11, 0x12, 0x10, 0xA5, 0x100, 0xFFFF, 2**32 - 1):
        assert isinstance(altgr_karakteri(vk), str)  # cokmedi, str dondu (tablo disi vk: bos ya da str)
    assert altgr_karakteri(0x44) == altgr_karakteri(0x44)  # tekrar cagri kararli


def test_e_gercek_altgr_tablo_tuslari_bos_docstring_iddiasi() -> None:
    """Docstring K3: 'harf/rakam disindaki tablo tuslari bos' -- Space, Esc, Tab, Enter, Backspace, Delete, Insert, Home, End,
    PageUp/Down, oklar, F1-F11 gercek `ToUnicodeEx` ile olculur (etkin duzen)."""
    dolu = {}
    for _, (ad, vk) in kisayol._TUS_ADLARI.items():
        k = altgr_karakteri(vk)
        if k:
            dolu[ad] = k
    for i in range(11):
        k = altgr_karakteri(0x70 + i)
        if k:
            dolu[f"F{i + 1}"] = k
    assert dolu == {}, f"duzen={_duzen():#06x} dolu={dolu!r}"


def test_e_gercek_altgr_tr_q_harf_rakam_kumesi_ve_tampon_temiz() -> None:
    duzen = _duzen()
    dolu = {h: altgr_karakteri(ord(h)) for h in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" if altgr_karakteri(ord(h))}
    if duzen == 0x041F:  # Turkce Q (KRT k4b ile ayni makine)
        assert set(dolu) == set("AEIQST012345789"), dolu
        assert dolu["T"] == "\u20ba" and altgr_karakteri(0x44) == "" and altgr_karakteri(0x52) == ""
    else:
        pytest.skip(f"etkin duzen {duzen:#06x} TR-Q degil; TR-Q kumesi [ÖLÇÜLMÜYOR] bu makinede")
    # tampon: her altgr sorgusundan sonra bos durumla A -> 'a' (olu tus kalintisi yok)
    kirli = []
    for h in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789":
        altgr_karakteri(ord(h))
        if _duz_karakter(0x41) != (1, "a"):
            kirli.append(h)
    assert kirli == []


def test_e_gercek_altgr_ile_servis_kaydet_ctrl_alt_t_cakisma_d_ok_sahte_win32(qapp: QApplication) -> None:
    """Gercek `altgr_karakteri` + SAHTE kayit fn: TR-Q'da Ctrl+Alt+T ALTGR_CAKISMA (Win32 cagrilmaz), Ctrl+Alt+D OK."""
    if _duzen() != 0x041F:
        pytest.skip("TR-Q degil")
    w = SahteWin32()
    s = KisayolServisi(kayit_fn=w.kayit, kaldir_fn=w.kaldir, hata_kodu_fn=w.hata, altgr_karakteri_fn=altgr_karakteri)
    assert s.kaydet("t", "Ctrl+Alt+T") is KayitSonucu.ALTGR_CAKISMA and w.kayitlar == []
    assert s.kaydet("e", "Ctrl+Alt+E") is KayitSonucu.ALTGR_CAKISMA and s.kaydet("iki", "Ctrl+Alt+2") is KayitSonucu.ALTGR_CAKISMA
    assert s.kaydet("d", "Ctrl+Alt+D") is KayitSonucu.OK and s.kaydet("r", "Ctrl+Alt+R") is KayitSonucu.OK
    assert s.kaydet("t2", "Ctrl+Alt+Shift+T") is KayitSonucu.OK and s.kaydet("t3", "Ctrl+Shift+T") is KayitSonucu.OK
    assert VARSAYILAN_KISAYOLLAR == {"anlik_cevir": "Ctrl+Alt+D", "bolge_izle": "Ctrl+Alt+R"}
    s.hepsini_kaldir()


# ====================================================================================================================
# F · THREAD
# ====================================================================================================================
def _baska_threadde(fn: Callable[[], object]) -> BaseException | object:
    kutu: list[BaseException | object] = []

    def hedef() -> None:
        try:
            kutu.append(fn())
        except BaseException as e:  # noqa: BLE001
            kutu.append(e)

    t = threading.Thread(target=hedef)
    t.start()
    t.join(10)
    assert not t.is_alive()
    return kutu[0]


def test_f_baska_threadden_kaydet_runtimeerror_sayac_0(qapp: QApplication, sahte: SahteWin32) -> None:
    s = sahte.servis()
    r = _baska_threadde(lambda: s.kaydet("a", "Ctrl+Alt+D"))
    assert isinstance(r, RuntimeError) and "thread" in str(r).lower()
    assert sahte.gunluk == [] and s.kayitli() == {}  # altgr bile sorulmadi: thread denetimi en once
    assert s.kaydet("a", "Ctrl+Alt+D") is KayitSonucu.OK  # pozitif kontrol: ana thread


def test_f_baska_threadden_kaldir_ve_hepsini_kaldir_runtimeerror_kayit_korunur(qapp: QApplication, sahte: SahteWin32) -> None:
    s = sahte.servis()
    s.kaydet("a", "Ctrl+Alt+D")
    sahte.gunluk.clear()
    assert isinstance(_baska_threadde(lambda: s.kaldir("a")), RuntimeError)
    assert isinstance(_baska_threadde(lambda: s.kaldir("bilinmeyen")), RuntimeError)  # sessiz yol bile thread'e bagli
    assert isinstance(_baska_threadde(s.hepsini_kaldir), RuntimeError)
    assert sahte.gunluk == [] and s.kayitli() == {"a": "Ctrl+Alt+D"}
    assert filtrele(s, mesaj(wparam=int(s._kayitlar["a"][0]))) == (True, 0)
    s.hepsini_kaldir()
    assert len(sahte.kaldirmalar) == 1


def test_f_baska_threadden_gecersiz_metin_bile_runtimeerror_thread_denetimi_once(qapp: QApplication, sahte: SahteWin32) -> None:
    assert isinstance(_baska_threadde(lambda: sahte.servis().kaydet("a", "")), RuntimeError) or True  # yapici da thread'de: asagida ayri
    s = sahte.servis()
    assert isinstance(_baska_threadde(lambda: s.kaydet("a", "")), RuntimeError)  # GECERSIZ degil, RuntimeError


def test_f_saf_dilbilgisi_ve_kayitli_baska_threadden_calisir(qapp: QApplication, sahte: SahteWin32) -> None:
    s = sahte.servis()
    s.kaydet("a", "Ctrl+Alt+D")
    assert _baska_threadde(lambda: kombinasyonu_coz("Ctrl+Alt+D")) == (CA, 0x44)
    assert _baska_threadde(s.kayitli) == {"a": "Ctrl+Alt+D"}  # okuma serbest
    assert _baska_threadde(lambda: s.son_hata_kodu) == 0


def test_f_ana_thread_kimligi_qt_ile_tutarli(qapp: QApplication) -> None:
    assert QThread.currentThread() is qapp.thread()
    assert _baska_threadde(lambda: QThread.currentThread() is qapp.thread()) is False


# ====================================================================================================================
# G · CALISTIR BAGLANTISI (sahte servis)
# ====================================================================================================================
class _SayanServis(KisayolServisi):
    """`hepsini_kaldir` cagrilarini sayan sahte-fn'li servis."""

    def __init__(self, w: SahteWin32) -> None:
        super().__init__(None, kayit_fn=w.kayit, kaldir_fn=w.kaldir, hata_kodu_fn=w.hata, altgr_karakteri_fn=w.altgr)
        self.hepsini_kaldir_sayisi = 0

    def hepsini_kaldir(self) -> None:
        self.hepsini_kaldir_sayisi += 1
        super().hepsini_kaldir()


@pytest.fixture
def kabuk_kur(qapp: QApplication, qtbot: Any, monkeypatch: pytest.MonkeyPatch) -> Callable[..., tuple[AnaPencere, KisayolServisi, SahteWin32, int]]:
    """`calistir(calistirici=..., kisayol_servisi=sahte)` kurar; (pencere, servis, sahte, cikis kodu) verir; testin sonunda kapatir."""
    monkeypatch.setattr(AnaPencere, "_balon_gosterildi", False)
    acik: list[AnaPencere] = []

    def kur(kisayollar: Any = None, *, w: SahteWin32 | None = None, servis: KisayolServisi | None = None, donus: int = 0) -> tuple[AnaPencere, KisayolServisi, SahteWin32, int]:
        w = w or SahteWin32()
        srv = servis if servis is not None else w.servis()
        tut: list[AnaPencere] = []

        def calistirici(app: QApplication, p: AnaPencere) -> int:
            tut.append(p)
            return donus

        kod = calistir([], calistirici=calistirici, kisayollar=kisayollar, kisayol_servisi=srv)
        acik.append(tut[0])
        return tut[0], srv, w, kod

    yield kur
    for p in acik:
        p.kapat()
        p.deleteLater()
    qtbot.wait(30)


def _sayaclar(p: AnaPencere) -> dict[str, list[int]]:
    c: dict[str, list[int]] = {"anlik": [], "bolge": [], "cikis": []}
    p.anlik_cevir_istendi.connect(lambda: c["anlik"].append(1))
    p.bolge_izle_istendi.connect(lambda: c["bolge"].append(1))
    p.cikis_istendi.connect(lambda: c["cikis"].append(1))
    return c


def test_g_varsayilan_kisayollar_kaydedilir_etiketler_ve_ipuclari(kabuk_kur: Any) -> None:
    p, s, w, kod = kabuk_kur()
    assert kod == 0 and s.kayitli() == {"anlik_cevir": "Ctrl+Alt+D", "bolge_izle": "Ctrl+Alt+R"}
    assert [(g[2], g[3]) for g in w.kayitlar] == [(CA | MOD_NOREPEAT, 0x44), (CA | MOD_NOREPEAT, 0x52)]
    assert "Ctrl+Alt+D" in p.dugme_anlik.text() and "Ctrl+Alt+R" in p.dugme_bolge.text()
    assert "Ctrl+Alt+D" in p.dugme_anlik.toolTip() and "Ctrl+Alt+R" in p.dugme_bolge.toolTip()
    assert "Ctrl+Alt+D" in p.tepsi.ikon.toolTip() and "Ctrl+Alt+R" in p.tepsi.ikon.toolTip()
    assert "(k\u0131sayol yok)" not in p.dugme_anlik.text() and p.durum_metni() == ""


@pytest.mark.parametrize("ad", ["anlik_cevir", "bolge_izle", "bilinmeyen", "", "ANLIK_CEVIR", "anlik_cevir "], ids=["anlik", "bolge", "bilinmeyen", "bos", "buyuk", "bosluklu"])
def test_g_tetiklendi_ad_tablosu_uc_durumda_durum_degismez(kabuk_kur: Any, ad: str) -> None:
    p, s, w, _ = kabuk_kur()
    c = _sayaclar(p)
    beklenen = {"anlik_cevir": ("anlik", 1), "bolge_izle": ("bolge", 1)}.get(ad)
    durumlar: list[KabukDurumu] = []
    for gecis in (p.goster, p.kenara_al, p.tepsiye_al):   # tepsi offscreen'de yok -> kenar (K5 istisnasi)
        gecis()
        once = p.durum
        s.tetiklendi.emit(ad)
        assert p.durum is once
        durumlar.append(once)
    assert set(durumlar) >= {KabukDurumu.GORUNUR, KabukDurumu.KENAR}
    if beklenen is None:
        assert c == {"anlik": [], "bolge": [], "cikis": []}
    else:
        assert len(c[beklenen[0]]) == 3 and len(c["anlik"]) + len(c["bolge"]) == 3 and c["cikis"] == []


def test_g_gercek_yol_olayi_calistir_baglantisiyla_pencereye_ulasir(kabuk_kur: Any, qtbot: Any) -> None:
    p, s, w, _ = kabuk_kur()
    c = _sayaclar(p)
    id_d, id_r = (g[1] for g in w.kayitlar)
    p.kenara_al()
    gercek_yol(id_d)
    gercek_yol(id_r)
    gercek_yol(id_d)
    qtbot.wait(50)
    assert len(c["anlik"]) == 2 and len(c["bolge"]) == 1 and p.durum is KabukDurumu.KENAR


def test_g_cikis_istendi_hepsini_kaldir_tam_bir_kez_kapat_idempotent(kabuk_kur: Any) -> None:
    w = SahteWin32()
    srv = _SayanServis(w)
    p, s, _, _ = kabuk_kur(w=w, servis=srv)
    assert srv.hepsini_kaldir_sayisi == 0 and len(w.kayitlar) == 2
    p.kapat()
    assert srv.hepsini_kaldir_sayisi == 1 and sorted(w.kaldirmalar) == sorted(g[1] for g in w.kayitlar) and s.kayitli() == {}
    p.kapat()
    p.close()
    assert srv.hepsini_kaldir_sayisi == 1 and len(w.kaldirmalar) == 2
    # kapat() sonrasi tetiklendi: durum degismez, sinyal yine yayilir (kabuk docstring: diriltmez)
    c = _sayaclar(p)
    s.tetiklendi.emit("anlik_cevir")
    assert len(c["anlik"]) == 1 and p.kapandi and not p.isVisible()


def test_g_kisayollar_bos_hic_kayit_yok_etiketler_kisayol_yok_durum_bos(kabuk_kur: Any) -> None:
    p, s, w, kod = kabuk_kur({})
    assert kod == 0 and w.gunluk == [] and s.kayitli() == {}  # altgr da sorulmadi
    assert "(k\u0131sayol yok)" in p.dugme_anlik.text() and "(k\u0131sayol yok)" in p.dugme_bolge.text()
    assert p.dugme_anlik.toolTip().endswith("(k\u0131sayol yok)") and p.tepsi.ikon.toolTip().count("(k\u0131sayol yok)") == 2
    assert p.durum_metni() == ""
    c = _sayaclar(p)
    s.tetiklendi.emit("anlik_cevir")   # kayit yok ama baglanti var: sinyal yine iletilir
    assert len(c["anlik"]) == 1


def test_g_PIN_D_A2_ayni_kombinasyon_iki_ada_ikincisi_cakisma_mesaj_baska_uygulama_yaniltici(kabuk_kur: Any) -> None:
    """D-A2: servis ici cakismada (ayni surec, ayni servis) durum satiri 'baska bir uygulama kullaniyor' der -- yanlis sebep."""
    p, s, w, kod = kabuk_kur({"anlik_cevir": "Ctrl+Alt+D", "bolge_izle": "ctrl+alt+d"})
    assert kod == 0 and len(w.kayitlar) == 1 and s.kayitli() == {"anlik_cevir": "Ctrl+Alt+D"}
    m = p.durum_metni()
    assert m.startswith("ctrl+alt+d kaydedilemedi: ba\u015fka bir uygulama kullan\u0131yor. ")
    assert m.endswith("Pencere d\u00fc\u011fmeleri ve tepsi men\u00fcs\u00fc \u00e7al\u0131\u015fmaya devam eder.")
    assert "Ctrl+Alt+D" in p.dugme_anlik.text() and "(k\u0131sayol yok)" in p.dugme_bolge.text()


def test_g_1409_ilk_kisayol_durum_metni_ve_etiketler_ikinci_calisir(kabuk_kur: Any) -> None:
    w = SahteWin32(kayit_sonucu=lambda i, m, v: v != 0x44, hata_kodu=ERR_1409)
    p, s, _, kod = kabuk_kur(w=w, donus=7)
    assert kod == 7                                              # cikis kodu degismez
    m = p.durum_metni()
    assert "Ctrl+Alt+D kaydedilemedi: ba\u015fka bir uygulama kullan\u0131yor" in m and "Ctrl+Alt+R" not in m
    assert "ayarlar" not in m.lower() and m.count("Pencere d\u00fc\u011fmeleri") == 1
    assert s.kayitli() == {"bolge_izle": "Ctrl+Alt+R"}
    assert "(k\u0131sayol yok)" in p.dugme_anlik.text() and "Ctrl+Alt+R" in p.dugme_bolge.text()
    assert "anl\u0131k \u00e7eviri: (k\u0131sayol yok)" in p.tepsi.ikon.toolTip() and "b\u00f6lge izle: Ctrl+Alt+R" in p.tepsi.ikon.toolTip()
    c = _sayaclar(p)
    gercek_yol(w.kayitlar[-1][1])
    s.tetiklendi.emit("bolge_izle")
    assert len(c["bolge"]) >= 1


@pytest.mark.parametrize(("kisayollar", "w_yap", "sebep"), [
    ({"anlik_cevir": "Ctrl+Alt+T", "bolge_izle": "Ctrl+Alt+R"}, lambda: SahteWin32(altgr={0x54: "\u20ba"}), "bu klavye d\u00fczeninde AltGr ile \u00e7ak\u0131\u015f\u0131yor"),
    ({"anlik_cevir": "Shift+T", "bolge_izle": "Ctrl+Alt+R"}, SahteWin32, "ge\u00e7ersiz kombinasyon"),
    ({"anlik_cevir": "", "bolge_izle": "Ctrl+Alt+R"}, SahteWin32, "ge\u00e7ersiz kombinasyon"),
    ({"anlik_cevir": "Ctrl+Alt+D", "bolge_izle": "Ctrl+Alt+R"}, lambda: SahteWin32(kayit_sonucu=lambda i, m, v: v != 0x44, hata_kodu=5), "Windows hata kodu 5"),
], ids=["altgr", "gecersiz_shift_t", "gecersiz_bos", "hata_5"])
def test_g_sebep_metinleri_ve_ikinci_kisayol_calisir(kabuk_kur: Any, kisayollar: dict[str, str], w_yap: Callable[[], SahteWin32], sebep: str) -> None:
    p, s, w, kod = kabuk_kur(kisayollar, w=w_yap())
    m = p.durum_metni()
    ilk = kisayollar["anlik_cevir"]
    assert m == f"{ilk} kaydedilemedi: {sebep}. Pencere d\u00fc\u011fmeleri ve tepsi men\u00fcs\u00fc \u00e7al\u0131\u015fmaya devam eder."
    assert s.kayitli() == {"bolge_izle": "Ctrl+Alt+R"} and "(k\u0131sayol yok)" in p.dugme_anlik.text() and kod == 0


def test_g_ikisi_de_basarisiz_parcalar_noktali_virgulle_devam_notu_bir_kez(kabuk_kur: Any) -> None:
    w = SahteWin32(kayit_sonucu=False, hata_kodu=ERR_1409)
    p, s, _, kod = kabuk_kur(w=w)
    m = p.durum_metni()
    assert m == ("Ctrl+Alt+D kaydedilemedi: ba\u015fka bir uygulama kullan\u0131yor; Ctrl+Alt+R kaydedilemedi: ba\u015fka bir uygulama kullan\u0131yor. "
                 "Pencere d\u00fc\u011fmeleri ve tepsi men\u00fcs\u00fc \u00e7al\u0131\u015fmaya devam eder.")
    assert s.kayitli() == {} and kod == 0 and p.tepsi.ikon.toolTip().count("(k\u0131sayol yok)") == 2


def test_g_kanonik_olmayan_metin_etikette_kanonik_gorunur(kabuk_kur: Any) -> None:
    p, s, _, _ = kabuk_kur({"anlik_cevir": "alt + ctrl + d", "bolge_izle": "SHIFT+CTRL+f5"})
    assert s.kayitli() == {"anlik_cevir": "Ctrl+Alt+D", "bolge_izle": "Ctrl+Shift+F5"}
    assert "Ctrl+Alt+D" in p.dugme_anlik.text() and "Ctrl+Shift+F5" in p.dugme_bolge.text() and "alt + ctrl" not in p.dugme_anlik.text()


def test_g_bilinmeyen_ad_kaydedilir_ama_etiketlenmez_ve_tetiklendi_yok_sayilir(kabuk_kur: Any) -> None:
    p, s, w, _ = kabuk_kur({"baska": "Ctrl+Alt+B", "anlik_cevir": "Ctrl+Alt+D"})
    assert s.kayitli() == {"baska": "Ctrl+Alt+B", "anlik_cevir": "Ctrl+Alt+D"} and p.durum_metni() == ""
    assert "(k\u0131sayol yok)" in p.dugme_bolge.text() and "Ctrl+Alt+B" not in p.tepsi.ikon.toolTip()
    c = _sayaclar(p)
    s.tetiklendi.emit("baska")
    assert c == {"anlik": [], "bolge": [], "cikis": []}
    p.kapat()
    assert s.kayitli() == {}  # bilinmeyen ad da cikista kaldirilir


def test_g_kisayol_servisi_verilmezse_yasak_degiskeniyle_runtimeerror_pencere_gosterilmez(qapp: QApplication, qtbot: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(AnaPencere, "_balon_gosterildi", False)
    once = {w for w in QApplication.topLevelWidgets() if w.isVisible()}
    kosuldu: list[int] = []
    with pytest.raises(RuntimeError, match="SUFLOR_GERCEK_KISAYOL_YASAK"):
        calistir([], calistirici=lambda app, p: kosuldu.append(1) or 0)
    gc.collect()
    qtbot.wait(20)
    assert kosuldu == [] and {w for w in QApplication.topLevelWidgets() if w.isVisible()} == once
    # pozitif kontrol: enjekte servisle kurulur
    w = SahteWin32()
    tut: list[AnaPencere] = []
    assert calistir([], calistirici=lambda app, p: tut.append(p) or 3, kisayol_servisi=w.servis()) == 3
    assert len(w.kayitlar) == 2
    tut[0].kapat()
    tut[0].deleteLater()
    qtbot.wait(20)


def test_g_ana_pencere_ebeveynli_servis_pencere_dusunce_temizlenir(qapp: QApplication, qtbot: Any, monkeypatch: pytest.MonkeyPatch, sok_sayaci: list[object]) -> None:
    """`calistir`in urun yolu: servis `AnaPencere`nin cocugu; pencere `del`+gc ile dusunce kayitlar kalkar, filtre sokulur."""
    monkeypatch.setattr(AnaPencere, "_balon_gosterildi", False)
    p = AnaPencere()
    w = SahteWin32()
    s = w.servis(p)
    s.tetiklendi.connect(p.kisayol_tetiklendi)
    p.cikis_istendi.connect(s.hepsini_kaldir)
    s.kaydet("anlik_cevir", "Ctrl+Alt+D")
    kimlik = w.son_kimlik()
    zayif = weakref.ref(p)
    del p, s
    gc.collect()
    qtbot.wait(30)
    assert zayif() is None and w.kaldirmalar == [kimlik] and len(sok_sayaci) == 1 and kimlik not in canli_kimlikler()


def test_g_PIN_O_A3_yapici_thread_denetimi_yok_baska_threadde_kurulan_servis_olaylari_sessizce_kaybeder_alt_surec() -> None:
    """O-A3: K6 yalniz kaydet/kaldir/hepsini_kaldir'i ana thread'e baglar; YAPICI baglamaz. Baska thread'de kurulan servis:
    yapici RuntimeError vermez, ana thread'den `kaydet` OK, ama `tetiklendi` olu thread'e kuyruklanir -> alici hic kosmaz
    (sessiz kayip: K6'nin korudugu sinif). Pozitif kontrol: ayni akis ana thread'de -> sinyal 1. Ayri surec (yikimda bir
    kosumda erisim ihlali gorulmustu; izole sondada 8/8 temiz -- rapora yazildi)."""
    sonda = str(Path(__file__).with_name("sonda_a_01_yapici_thread.py"))
    baska = subprocess.run([sys.executable, sonda], capture_output=True, text=True, timeout=60)
    ana = subprocess.run([sys.executable, sonda, "ana"], capture_output=True, text=True, timeout=60)
    assert baska.returncode == 0 and ana.returncode == 0, (baska.returncode, ana.returncode)
    assert "yapici_istisna=None" in baska.stdout and "kaydet=ok servis_thread_ana=False" in baska.stdout and "sinyal=0" in baska.stdout
    assert "kaydet=ok servis_thread_ana=True" in ana.stdout and "sinyal=1" in ana.stdout


def test_g_varsayilan_kisayollar_salt_okunur_ve_kayit_sebebi_tablosu() -> None:
    with pytest.raises(TypeError):
        VARSAYILAN_KISAYOLLAR["anlik_cevir"] = "Ctrl+Alt+T"  # type: ignore[index]
    assert kayit_sebebi(KayitSonucu.OK, 0) == "" and kayit_sebebi(KayitSonucu.OK, 1409) == ""
    assert kayit_sebebi(KayitSonucu.CAKISMA, 0) == "ba\u015fka bir uygulama kullan\u0131yor"   # hata kodundan bagimsiz
    assert kayit_sebebi(KayitSonucu.HATA, 0) == "Windows hata kodu 0"
    assert kayit_sebebi(KayitSonucu.HATA, -1) == "Windows hata kodu -1"
    assert "ayar" not in " ".join(kayit_sebebi(s, 1409) for s in KayitSonucu).lower()


def test_g_kisayol_etiketleri_bos_deger_ve_yeniden_cagri_biriktirmez(qapp: QApplication, qtbot: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(AnaPencere, "_balon_gosterildi", False)
    p = AnaPencere()
    try:
        p.kisayol_etiketleri({"anlik_cevir": "", "bolge_izle": "Ctrl+Alt+R"})
        assert "(k\u0131sayol yok)" in p.dugme_anlik.text() and "Ctrl+Alt+R" in p.dugme_bolge.text()
        for _ in range(5):
            p.kisayol_etiketleri({"anlik_cevir": "Ctrl+Alt+D"})
        assert p.dugme_anlik.text().count("Ctrl+Alt+D") == 1 and p.dugme_anlik.text().count("\n") == 1
        assert "(k\u0131sayol yok)" in p.dugme_bolge.text() and p.tepsi.ikon.toolTip().count("Ctrl+Alt+D") == 1
        p.kisayol_etiketleri({})
        assert p.dugme_anlik.text().count("(k\u0131sayol yok)") == 1 and "Ctrl+Alt+D" not in p.tepsi.ikon.toolTip()
    finally:
        p.kapat()
        p.deleteLater()
        qtbot.wait(20)


def test_g_uygulama_yoksa_servis_runtimeerror_alt_surec() -> None:
    kod = ("import os,sys; os.environ['QT_QPA_PLATFORM']='offscreen'; os.environ['SUFLOR_GERCEK_KISAYOL_YASAK']='1'; "
           f"sys.path.insert(0, {str(KOK)!r}); from src.ui.kisayol import KisayolServisi\n"
           "try:\n    KisayolServisi(kayit_fn=lambda *a: True, kaldir_fn=lambda i: True, hata_kodu_fn=lambda: 0, altgr_karakteri_fn=lambda v: '')\n"
           "except RuntimeError as e:\n    print('RuntimeError', 'QApplication' in str(e))\n")
    r = subprocess.run([sys.executable, "-c", kod], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0 and r.stdout.strip() == "RuntimeError True", (r.stdout, r.stderr[-300:])


@pytest.mark.parametrize("eksik", ["kayit_fn", "kaldir_fn", "hata_kodu_fn", "altgr_karakteri_fn"])
def test_g_gercek_win32_false_eksik_fn_runtimeerror_adi_mesajda_filtre_kurulmaz(qapp: QApplication, kur_sayaci: list[object], eksik: str) -> None:
    fnler: dict[str, Any] = {"kayit_fn": lambda *a: True, "kaldir_fn": lambda i: True, "hata_kodu_fn": lambda: 0, "altgr_karakteri_fn": lambda v: ""}
    fnler.pop(eksik)
    with pytest.raises(RuntimeError, match=eksik):
        KisayolServisi(**fnler)
    assert kur_sayaci == []


def test_g_gercek_win32_true_yasak_degiskeniyle_runtimeerror_fnler_verilse_de(qapp: QApplication, kur_sayaci: list[object], sahte: SahteWin32) -> None:
    with pytest.raises(RuntimeError, match="SUFLOR_GERCEK_KISAYOL_YASAK"):
        KisayolServisi(gercek_win32=True, kayit_fn=sahte.kayit, kaldir_fn=sahte.kaldir, hata_kodu_fn=sahte.hata, altgr_karakteri_fn=sahte.altgr)
    assert kur_sayaci == [] and sahte.gunluk == []
