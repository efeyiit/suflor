"""Suflör -- global kisayol servisi (`KisayolServisi`), T-013 K1/K2/K3/K6 (paket surum 2).

Win32 `RegisterHotKey(hwnd=NULL)` + `QAbstractNativeEventFilter` (`WM_HOTKEY`): kisayol, kabuk tepsideyken /
kenardayken / hicbir pencere gorunmezken de gelir (on olcum U3, KRT k6). Bu docstring, paketin K1-K6
degismezlerinin bu modulde nasil uygulandigini belgeler; her kararin yaninda onu olcen test adi vardir
(`tests/unit/ui/test_kisayol.py`) ya da `[ÖLÇÜLMÜYOR]` damgasi.

Arayuz (baglayici): `KisayolServisi(ebeveyn=None, *, gercek_win32=False, kayit_fn=None, kaldir_fn=None,
hata_kodu_fn=None, altgr_karakteri_fn=None)`; `kaydet(ad, kombinasyon) -> KayitSonucu`; `kaldir(ad)`;
`hepsini_kaldir()`; `kayitli() -> Mapping[str, str]` (ad -> kanonik kombinasyon, KOPYA); `son_hata_kodu: int`;
sinyal `tetiklendi(str)`; `filtre` (kurulu `QAbstractNativeEventFilter`); sinif yontemi
`kombinasyonu_coz(metin) -> (mod, vk)`; modul fonksiyonlari `kombinasyonu_coz`, `kombinasyonu_yaz(mod, vk)`,
`altgr_karakteri(vk) -> str` (gercek `ToUnicodeEx`). Enjekte imzalari: `kayit_fn(id, mod, vk) -> bool`
(`mod` `MOD_NOREPEAT` DAHIL), `kaldir_fn(id) -> bool`, `hata_kodu_fn() -> int`, `altgr_karakteri_fn(vk) -> str`;
`hwnd` daima NULL.

## Y1 -- gercek Win32 yalniz acikca istenince (emniyet kemeri)

Offscreen'de de olay dagiticisi `QEventDispatcherWin32`dir ve `RegisterHotKey` GERCEK kayit yapar (KRT k1 o2/o4:
paralel pytest 1409). Koruma platformdan degil ENJEKSIYONDAN gelir: `gercek_win32=False` (varsayilan) iken dort
fonksiyonun HEPSI verilmek zorundadir, eksikse `RuntimeError` (eksik parametrenin adi mesajda;
`test_k2_gercek_win32_false_fn_eksikse_runtimeerror`, pozitif kontrol `..._fnler_verilince_kurulur`).
`gercek_win32=True` iken verilmeyenler gercek ince sarmalayicilardir (`_win32_kaydet`, `_win32_kaldir`,
`_win32_hata_kodu`, `altgr_karakteri`; `# pragma: no cover` -- offscreen'de kosulmaz, `real_check` olcer); ama
`SUFLOR_GERCEK_KISAYOL_YASAK` ortam degiskeni varken (sefin `conftest.py`si koyar) `gercek_win32=True` kurulumu
`RuntimeError` verir -- fn'ler verilmis olsa da (`test_k2_gercek_win32_yasak_degiskeni_varken_runtimeerror`;
pozitif kontrol: degisken silinince kurulur, `kaydet` cagrilmaz). `calistir` ve `real_check` `gercek_win32=True`
kullanir. `QCoreApplication` yoksa `RuntimeError` (`test_k2_uygulama_yoksa_runtimeerror`).

## K1 -- kayit/kaldirma durum makinesi

`kaydet(ad, kombinasyon)`: (1) ana thread denetimi (K6); (2) dilbilgisi (K3) -- `ValueError` /
`GecersizKombinasyon` -> `GECERSIZ`, Win32 CAGRILMAZ; (3) `Ctrl+Alt+<tus>` (Shift'siz) ise `altgr_karakteri_fn(vk)`
sorulur, bos degilse `ALTGR_CAKISMA`, Win32 CAGRILMAZ (Y2); (4) ayni `ad` kayitliysa ONCE eski kayit kaldirilir
(`kaldir_fn(eski id)`), yeni kayit YENI kimlik alir (`test_k1_ayni_ad_yeniden_kaydet_once_kaldir_sonra_kaydet`) --
(2)/(3) once geldigi icin gecersiz yeni kombinasyon eski kaydi bozmaz
(`test_k1_ayni_ad_gecersiz_yeni_kombinasyon_eski_kayit_korunur`); (5) ayni kombinasyon baska bir `ad` altinda
kayitliysa `CAKISMA`, Win32 CAGRILMAZ, `son_hata_kodu` degismez
(`test_k1_ayni_kombinasyon_baska_ad_servis_ici_cakisma_win32_cagrilmaz`); (6) `kayit_fn(id, mod | MOD_NOREPEAT, vk)`:
`True` -> `OK`, `son_hata_kodu = 0`; `False` -> `son_hata_kodu = hata_kodu_fn()`, 1409 -> `CAKISMA`, baska -> `HATA`;
basarisiz kayit `kayitli()`de YOKTUR (`test_k1_1409_cakisma_kayitlida_yok`, `test_k1_diger_hata_kodu_hata`).
Her kayit `MOD_NOREPEAT` tasir (`test_k1_kaydet_ok_cagri_dizisi_ve_norepeat`; gercek ayirt edici olcu `real_check`
[5]: 5 DOWN -> 1, NOREPEAT'siz 5). Win32 1409 SONRASI eski kayit geri GELMEZ (ayni ad yeniden kaydinda eski
kaldirilmis, yenisi reddedilmistir) -- belgeli, `[ÖLÇÜLMÜYOR]` (v2: geri alma).
`kaldir(ad)`: bilinmeyen ad SESSIZ; kayitliysa `kaldir_fn(id)` + tablodan silme (`test_k1_kaldir_*`).
`hepsini_kaldir()`: her kayit icin `kaldir`, IDEMPOTENT (`test_k1_hepsini_kaldir_idempotent`).
`kayitli()`: `dict` KOPYASI; disaridan mutasyon servisi etkilemez (`test_k1_kayitli_kopya_*`).

▲ KIMLIK SUREC GENELINDE BENZERSIZ (O4): Win32 `id` modul duzeyi sayactan gelir (`_sonraki_kimlik`, 1..0xBFFF
uygulama araligi, ustte 1'e sarar) ve CANLI bir kimlik yeniden verilmez (`_canli_kimlikler`); ayni surecte iki
servisin kimlik kumeleri ayriktir ve her servis yalniz KENDI kimliklerini kaldirir (KRT g5: ayni id iki kayit
aliyor, `UnregisterHotKey` ikisini birden siliyor; `test_k1_kimlik_surec_genelinde_benzersiz_iki_servis`,
`test_k1_kimlik_sayaci_ust_sinirda_sarar_ve_canli_kimligi_atlar`, `test_k1_kimlik_ust_siniri_0xbfff`).

▲ YIKIM (Y3): `self.destroyed.connect(functools.partial(_yikimda_temizle, kimlik_tablosu, kaldir_fn, filtre,
app.removeNativeEventFilter))` -- alici `self`i YAKALAMAYAN serbest fonksiyon; PySide6 6.11'de
`self.destroyed.connect(self.<yontem>)` HICBIR yolda kosmaz (KRT k5b A 4/4; on olcum o1: partial 0 ek argumanla
cagrilir). Paylasilan kimlik tablosu (`dict[int, str]`, yerinde degistirilir, hic yeniden baglanmaz), `kaldir_fn`,
filtre nesnesi ve `removeNativeEventFilter` bagli yontemi ARGUMAN olarak gecer. `del`+gc ve `deleteLater` yollarinda
sahte `kaldir_fn` her kimlik icin cagrilir, filtre sokulur (`test_k1_yikim_kayitlar_kaldirilir_filtre_sokulur[del_gc|deleteLater]`,
ebeveyn yolu `test_k1_yikim_ebeveyn_silinince_cocuk_servis_temizler`, `hepsini_kaldir` sonrasi cift kaldirma yok);
pozitif kontrol (kural 10): bagli yontemli kopya iki yolda da KOSMAZ, partial kosar
(`test_k1_yikim_pozitif_kontrol_bagli_yontem_kosmaz_partial_kosar`); yapisal bekci
`test_k1_kaynakta_destroyed_alicisi_self_yontemi_degil_ast`. Filtre servise `weakref` ile ulasir (sinyali yaymak
icin); `installNativeEventFilter` Python sarmalayicisini canli TUTMAZ (on olcum o3) -> servis `_filtre` guclu
referansini kendi tutar. Cikista (`QApplication` yikimi widget'lari, onlar cocuk servisi silerken) temizleyici
kosar, cokme yok (on olcum, `evidence/olcum-on-pyside-davranislari.txt`). `real_check` [9]: `del`+gc sonrasi
`Ctrl+Alt+D` yeniden alinabilir; `deleteLater` yolu kapida `[ÖLÇÜLMÜYOR]` (`bekle()` `DeferredDelete` islemez),
birim testte olculur.

## K2 -- olay yolu: WM_HOTKEY -> `tetiklendi(ad)` yalniz bizim kimlikler icin

`_Filtre.nativeEventFilter(eventType, message)`: `bytes(eventType) != b"windows_generic_MSG"` -> mesaja
DOKUNMADAN `False` (KRT O7: yapi Windows `MSG` olmayabilir; `test_k2_yanlis_event_type_false_mesaja_dokunmaz`);
`wintypes.MSG.from_address(int(message))` -- adres YALNIZ Qt'den (ya da testte gercek `MSG` + `addressof`) gelir,
sifir/bozuk adres sureci oldurur (KRT k9), olcusu YOK `[ÖLÇÜLMÜYOR]`; `message != WM_HOTKEY` -> `False`;
`wParam` tabloda yoksa `False` (Qt filtreleri SON kurulan once cagirir, `True` keser -- eski servis yeni servisin
olayini yutmaz; `test_k2_filtre_sirasi_*`); bilinen kimlik -> `tetiklendi(ad)` + `(True, 0)`
(`test_k2_bilinen_kimlik_sinyal_ve_true`, `test_k2_iki_kayit_dogru_ad`, `test_k2_kaldirilan_kimlik_artik_bilinmiyor`).
Filtre yapicida BIR kez kurulur, yikimda sokulur (`test_k2_filtre_bir_kez_kurulur_ve_ayni_nesne`). Gecikme: bosta
< 20 ms (on olcum 1.9 ms, KRT p1 medyan 1.3-4.3 ms; offscreen filtre dagitimi
`evidence/olcum-filtre-gecikme-offscreen.txt`); GIL'i tutan surec ici thread'ler altinda `[ÖLÇÜLMÜYOR]`
(KRT: 200+ ms -- pipeline entegrasyon gorevinin yukumlulugu). Gercek `WM_HOTKEY` yalniz `real_check` [1]/[2]/[6].

## K3 -- kombinasyon dilbilgisi saf ve kati (▲ O3, Y2)

`kombinasyonu_coz(metin) -> (mod, vk)` SAF: `+` ile ayrilir, bosluk/harf durumu serbest ("ctrl + alt + d" ==
"Alt+Ctrl+D"), yalniz ASCII. Degistiriciler `Ctrl`/`Control`, `Alt`, `Shift`; `Win`/`Meta`/`Windows`/`Super` ->
`GecersizKombinasyon` (Windows rezerve, KRT 34/36 1409). Tus tablosu: `A`-`Z`, `0`-`9`, `F1`-`F11` (`F12` ->
`GecersizKombinasyon`: hata ayiklayici), `Space`, `Esc`/`Escape`, `Tab`, `Enter`/`Return`, `Backspace`,
`Delete`/`Del`, `Insert`/`Ins`, `Home`, `End`, `PageUp`/`PgUp`, `PageDown`/`PgDn`, `Left`/`Up`/`Right`/`Down`.
Degistirici kurali: `F1`-`F11` icin >= 1; DIGER HER TUS icin kume ⊇ {Ctrl,Alt} ya da ⊇ {Ctrl,Shift} ya da
⊇ {Alt,Shift} (tek degistirici, `Shift`-tek, degistiricisiz -> `GecersizKombinasyon`; KRT g3: `Shift+T` buyuk T'yi
yutuyor). Paket bu kurali "harf/rakam/Space" icin yazar; Tab/Enter/Esc/Delete/ok tuslari da yazma/gezinme tuslari
oldugundan AYNI kural uygulanir (paketin bir adim otesi; belgeli). Kara liste (tam esleme) -> `GecersizKombinasyon`:
`Alt+Tab`, `Alt+F4`, `Alt+Esc`, `Alt+Space`, `Ctrl+Esc`, `Ctrl+Alt+Delete`, `Ctrl+Shift+Esc`. Bozuk metin (bos,
bos parca, tekrar eden degistirici, iki tus, tus yok, bilinmeyen/ASCII disi parca) -> duz `ValueError`;
`GecersizKombinasyon` `ValueError`nin ALT SINIFIDIR (`test_k3_dilbilgisi_tablosu` >= 40 ornek,
`test_k3_gecersiz_bozuk_ayrimi`). `kombinasyonu_yaz(mod, vk)` kanonik metni uretir (`Ctrl+Alt+Shift+<Tus>` sirasi;
`test_k3_kombinasyonu_yaz_kanonik_ve_tersine`); `kayitli()` bu metni verir. `kaydet` her iki siniftan da `GECERSIZ`
doner (K5: hata durum satirina; istisna kabuga ulasmaz; `test_k3_kaydet_gecersiz_ve_bozuk_metin_gecersiz_win32_cagrilmaz`).
▲ AltGr (Y2): Turkce Q'da `Ctrl+Alt` = AltGr; `Ctrl+Alt+T` kayitliyken ₺ hicbir uygulamada yazilamaz (KRT g4).
`kaydet`, kombinasyon `Ctrl+Alt+<tus>` (Shift'siz) ise `altgr_karakteri_fn(vk)` sorar; bos degilse
`ALTGR_CAKISMA` (Win32 cagrilmaz); Shift'li ya da Ctrl+Alt'siz kombinasyonda SORULMAZ
(`test_k3_altgr_cakismasi_ctrl_alt_shiftsiz`, `test_k3_altgr_shiftli_ve_ctrl_altsiz_sorulmaz`). Gercek
`altgr_karakteri(vk)`: `ToUnicodeEx(vk, tarama kodu, Ctrl+LCtrl+Alt+RAlt basili durum, ..., GetKeyboardLayout(0))`
-- bu thread'in kayit anindaki duzeni; olu tus (`< 0`) donerse duzenin bekleyen durumu bos durumla `Space`
sorgusuyla temizlenir (yan etki) ve olu tus karakteri doner (AltGr o tusu kullaniyor -> cakisma). TR-Q: A E I Q S T
0-5 7-9 dolu; harf/rakam disindaki tablo tuslari bos (on olcum o5). `real_check` [8] `T -> "₺"`, `D -> ""`.
Duzen calisirken degisirse `[ÖLÇÜLMÜYOR]` (kayit anindaki duzen); TR-F ve baska duzenler `[ÖLÇÜLMÜYOR]`.

## K4 -- tepside/kenardayken calisir (`hwnd=NULL`)

Servis kabuk durumundan habersizdir; yalniz sinyal yayar, alici karar verir (`src.ui.uygulama.calistir`
`tetiklendi -> AnaPencere.kisayol_tetiklendi`). Gercek: `real_check` [2].

## K6 -- metin yok, blok yok, thread

`print`/`logging`/`warnings`/`time.sleep`/`processEvents` yok (AST `test_k6_k7_kaynak_yasak_ad_ve_import_icermez[kisayol.py]`,
`test_k1_sinyal_baglantilarinda_lambda_yok_ast`). `kaydet`/`kaldir`/`hepsini_kaldir` YALNIZ ana thread:
`QThread.currentThread() is app.thread()` degilse `RuntimeError`, Win32 cagrilmaz (KRT p6: baska thread'den
`RegisterHotKey` basarili ama `WM_HOTKEY` o thread'in kuyrugunda kaybolur; k7: kimlik olcusu calisir;
`test_k6_baska_threadden_*`). Paket yalniz `kaydet` icin yazar; `kaldir` de ayni thread'e baglidir
(`UnregisterHotKey` baska thread'den 1419), kural ucune de uygulanir (bir adim otesi). Yikim temizleyicisi
denetlemez (nesne hangi thread'de silinirse). Ince sarmalayicilar `# pragma: no cover`
(`test_k6_ince_sarmalayicilar_pragma_no_cover_ve_ctypes_yalniz_orada`).
"""
from __future__ import annotations

import ctypes
import functools
import os
import weakref
from collections.abc import Callable, Mapping
from ctypes import wintypes
from enum import StrEnum
from typing import Final

from PySide6.QtCore import QAbstractNativeEventFilter, QByteArray, QCoreApplication, QObject, QThread, Signal

__all__ = [
    "GERCEK_KISAYOL_YASAK_DEGISKENI",
    "MOD_ALT",
    "MOD_CONTROL",
    "MOD_NOREPEAT",
    "MOD_SHIFT",
    "WM_HOTKEY",
    "GecersizKombinasyon",
    "KayitSonucu",
    "KisayolServisi",
    "altgr_karakteri",
    "kombinasyonu_coz",
    "kombinasyonu_yaz",
]

WM_HOTKEY: Final = 0x0312
MOD_ALT: Final = 0x0001
MOD_CONTROL: Final = 0x0002
MOD_SHIFT: Final = 0x0004
MOD_WIN: Final = 0x0008
MOD_NOREPEAT: Final = 0x4000
ERROR_HOTKEY_ALREADY_REGISTERED: Final = 1409
GERCEK_KISAYOL_YASAK_DEGISKENI: Final = "SUFLOR_GERCEK_KISAYOL_YASAK"
_OLAY_TIPI: Final = b"windows_generic_MSG"
_KIMLIK_ILK: Final = 1
_KIMLIK_SON: Final = 0xBFFF  # RegisterHotKey docs: uygulama araligi 0x0000-0xBFFF

KayitFn = Callable[[int, int, int], bool]
KaldirFn = Callable[[int], bool]
HataKoduFn = Callable[[], int]
AltgrKarakteriFn = Callable[[int], str]

# -- surec genelinde kimlik (K1 ▲ O4) ---------------------------------------------------------------
_sonraki_kimlik: int = _KIMLIK_ILK
_canli_kimlikler: set[int] = set()


def _yeni_kimlik() -> int:
    global _sonraki_kimlik
    for _ in range(_KIMLIK_SON - _KIMLIK_ILK + 1):
        aday = _sonraki_kimlik
        _sonraki_kimlik = aday + 1 if aday < _KIMLIK_SON else _KIMLIK_ILK
        if aday not in _canli_kimlikler:
            _canli_kimlikler.add(aday)
            return aday
    raise RuntimeError("kisayol kimlikleri tukendi (1..0xBFFF hepsi canli)")  # pragma: no cover


# -- dilbilgisi (K3) --------------------------------------------------------------------------------
class GecersizKombinasyon(ValueError):
    """Ayristirilabilir ama yasak kombinasyon (Win, F12, tek degistirici, kara liste) -> `kaydet` `GECERSIZ`."""


_DEGISTIRICILER: Final[Mapping[str, int]] = {
    "CTRL": MOD_CONTROL, "CONTROL": MOD_CONTROL, "ALT": MOD_ALT, "SHIFT": MOD_SHIFT,
    "WIN": MOD_WIN, "META": MOD_WIN, "WINDOWS": MOD_WIN, "SUPER": MOD_WIN,
}
_TUS_ADLARI: Final[Mapping[str, tuple[str, int]]] = {
    "SPACE": ("Space", 0x20), "ESC": ("Esc", 0x1B), "ESCAPE": ("Esc", 0x1B), "TAB": ("Tab", 0x09),
    "ENTER": ("Enter", 0x0D), "RETURN": ("Enter", 0x0D), "BACKSPACE": ("Backspace", 0x08),
    "DELETE": ("Delete", 0x2E), "DEL": ("Delete", 0x2E), "INSERT": ("Insert", 0x2D), "INS": ("Insert", 0x2D),
    "HOME": ("Home", 0x24), "END": ("End", 0x23), "PAGEUP": ("PageUp", 0x21), "PGUP": ("PageUp", 0x21),
    "PAGEDOWN": ("PageDown", 0x22), "PGDN": ("PageDown", 0x22),
    "LEFT": ("Left", 0x25), "UP": ("Up", 0x26), "RIGHT": ("Right", 0x27), "DOWN": ("Down", 0x28),
}
_VK_F1: Final = 0x70
_VK_F11: Final = 0x7A
_VK_F12: Final = 0x7B
_VK_TAB, _VK_ESC, _VK_SPACE, _VK_DELETE, _VK_F4 = 0x09, 0x1B, 0x20, 0x2E, 0x73
_KARA_LISTE: Final[frozenset[tuple[int, int]]] = frozenset({
    (MOD_ALT, _VK_TAB), (MOD_ALT, _VK_F4), (MOD_ALT, _VK_ESC), (MOD_ALT, _VK_SPACE), (MOD_CONTROL, _VK_ESC),
    (MOD_CONTROL | MOD_ALT, _VK_DELETE), (MOD_CONTROL | MOD_SHIFT, _VK_ESC),
})
_VK_ADLARI: Final[Mapping[int, str]] = {
    **{ord(h): h for h in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"},
    **{_VK_F1 + i: f"F{i + 1}" for i in range(11)},
    **{vk: ad for ad, vk in _TUS_ADLARI.values()},
}


def _tusu_coz(parca: str) -> int:
    if len(parca) == 1 and parca in _VK_ADLARI.values():
        return ord(parca)
    if parca in _TUS_ADLARI:
        return _TUS_ADLARI[parca][1]
    if len(parca) >= 2 and parca[0] == "F" and parca[1:].isdigit():
        n = int(parca[1:])
        if n == 12:
            raise GecersizKombinasyon("F12 hata ayiklayiciya ayrilmis")
        if 1 <= n <= 11:
            return _VK_F1 + n - 1
    raise ValueError(f"bilinmeyen tus: {parca!r}")


def kombinasyonu_coz(metin: str) -> tuple[int, int]:
    """SAF: `"Ctrl+Alt+D"` -> `(MOD_CONTROL | MOD_ALT, 0x44)`. Bozuk metin `ValueError`; yasak kombinasyon
    `GecersizKombinasyon` (`ValueError` alt sinifi). `MOD_NOREPEAT` icermez (modul docstring'i K3)."""
    parcalar = [p.strip() for p in metin.split("+")]
    if any(not p or not p.isascii() for p in parcalar):
        raise ValueError(f"bos ya da ASCII disi parca: {metin!r}")
    mod = 0
    tuslar: list[int] = []
    for parca in (p.upper() for p in parcalar):
        bit = _DEGISTIRICILER.get(parca)
        if bit is not None:
            if mod & bit:
                raise ValueError(f"tekrar eden degistirici: {metin!r}")
            mod |= bit
        else:
            tuslar.append(_tusu_coz(parca))
    if len(tuslar) != 1:
        raise ValueError(f"tam bir tus gerekir ({len(tuslar)} verildi): {metin!r}")
    vk = tuslar[0]
    if mod & MOD_WIN:
        raise GecersizKombinasyon("Win/Meta Windows'a ayrilmis")
    if _VK_F1 <= vk <= _VK_F11:
        if mod == 0:
            raise GecersizKombinasyon("F tusu icin en az bir degistirici gerekir")
    elif bin(mod).count("1") < 2:
        raise GecersizKombinasyon("en az iki degistirici gerekir (Ctrl+Alt, Ctrl+Shift ya da Alt+Shift)")
    if (mod, vk) in _KARA_LISTE:
        raise GecersizKombinasyon("sistem kombinasyonu (kara liste)")
    return mod, vk


def kombinasyonu_yaz(mod: int, vk: int) -> str:
    """`(mod, vk)` -> kanonik metin `Ctrl+Alt+Shift+<Tus>`; dilbilgisi disi girdi `ValueError`."""
    if mod & ~(MOD_CONTROL | MOD_ALT | MOD_SHIFT) or vk not in _VK_ADLARI:
        raise ValueError(f"dilbilgisi disi: mod={mod:#x} vk={vk:#x}")
    parcalar = [ad for bit, ad in ((MOD_CONTROL, "Ctrl"), (MOD_ALT, "Alt"), (MOD_SHIFT, "Shift")) if mod & bit]
    return "+".join([*parcalar, _VK_ADLARI[vk]])


# -- gercek Win32 ince sarmalayicilari (yalniz gercek_win32=True; offscreen'de kosulmaz, real_check olcer) ----
_VK_CONTROL, _VK_LCONTROL, _VK_MENU, _VK_RMENU = 0x11, 0xA2, 0x12, 0xA5
_u32: ctypes.WinDLL | None = None


def _kullanici32() -> ctypes.WinDLL:  # pragma: no cover
    global _u32
    if _u32 is None:
        u32 = ctypes.WinDLL("user32", use_last_error=True)
        u32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
        u32.RegisterHotKey.restype = wintypes.BOOL
        u32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
        u32.UnregisterHotKey.restype = wintypes.BOOL
        u32.GetKeyboardLayout.argtypes = [wintypes.DWORD]
        u32.GetKeyboardLayout.restype = wintypes.HKL
        u32.MapVirtualKeyW.argtypes = [wintypes.UINT, wintypes.UINT]
        u32.MapVirtualKeyW.restype = wintypes.UINT
        u32.ToUnicodeEx.argtypes = [wintypes.UINT, wintypes.UINT, ctypes.POINTER(ctypes.c_ubyte), wintypes.LPWSTR,
                                    ctypes.c_int, wintypes.UINT, wintypes.HKL]
        u32.ToUnicodeEx.restype = ctypes.c_int
        _u32 = u32
    return _u32


def _win32_kaydet(kimlik: int, mod: int, vk: int) -> bool:  # pragma: no cover
    return bool(_kullanici32().RegisterHotKey(None, kimlik, mod, vk))


def _win32_kaldir(kimlik: int) -> bool:  # pragma: no cover
    return bool(_kullanici32().UnregisterHotKey(None, kimlik))


def _win32_hata_kodu() -> int:  # pragma: no cover
    return int(ctypes.get_last_error())


def altgr_karakteri(vk: int) -> str:  # pragma: no cover
    """Etkin duzende (bu thread, `GetKeyboardLayout(0)`) Ctrl+Alt (= AltGr) basiliyken `vk` hangi karakteri uretir;
    `""` = karakter yok. Olu tus donerse bekleyen durum temizlenir ve olu tus karakteri doner (modul docstring'i K3)."""
    u32 = _kullanici32()
    hkl = u32.GetKeyboardLayout(0)
    durum = (ctypes.c_ubyte * 256)()
    for tus in (_VK_CONTROL, _VK_LCONTROL, _VK_MENU, _VK_RMENU):
        durum[tus] = 0x80
    tampon = ctypes.create_unicode_buffer(8)
    n = int(u32.ToUnicodeEx(vk, u32.MapVirtualKeyW(vk, 0), durum, tampon, 8, 0, hkl))
    if n < 0:
        bos_durum = (ctypes.c_ubyte * 256)()
        bos_tampon = ctypes.create_unicode_buffer(8)
        u32.ToUnicodeEx(_VK_SPACE, u32.MapVirtualKeyW(_VK_SPACE, 0), bos_durum, bos_tampon, 8, 0, hkl)
        return str(tampon[0]) if tampon[0] != "\x00" else ""
    return str(tampon.value[:n]) if n > 0 else ""


# -- servis -----------------------------------------------------------------------------------------
class KayitSonucu(StrEnum):
    OK = "ok"
    CAKISMA = "cakisma"
    ALTGR_CAKISMA = "altgr_cakisma"
    GECERSIZ = "gecersiz"
    HATA = "hata"


def _uygulama() -> QCoreApplication:
    app = QCoreApplication.instance()
    if app is None:
        raise RuntimeError("KisayolServisi icin once QApplication kurulmali")
    return app


class _Filtre(QAbstractNativeEventFilter):
    """`WM_HOTKEY` -> `tetiklendi(ad)` (modul docstring'i K2). Servise `weakref` ile ulasir (yikim: K1 ▲ Y3)."""

    def __init__(self, kimlikler: dict[int, str], servis: weakref.ref[KisayolServisi]) -> None:
        super().__init__()
        self._kimlikler = kimlikler
        self._servis = servis

    def nativeEventFilter(self, eventType: QByteArray | bytes | bytearray | memoryview, message: int) -> tuple[bool, int]:
        ham = eventType.data() if isinstance(eventType, QByteArray) else bytes(eventType)
        if ham != _OLAY_TIPI:
            return False, 0
        mesaj = wintypes.MSG.from_address(int(message))
        if mesaj.message != WM_HOTKEY:
            return False, 0
        ad = self._kimlikler.get(int(mesaj.wParam))
        if ad is None:
            return False, 0
        servis = self._servis()
        if servis is not None:
            servis.tetiklendi.emit(ad)
        return True, 0


def _yikimda_temizle(kimlikler: dict[int, str], kaldir_fn: KaldirFn, filtre: _Filtre,
                     filtreyi_sok: Callable[[QAbstractNativeEventFilter], None], *_: object) -> None:
    """`destroyed` alicisi: `self` YOK (K1 ▲ Y3). Kalan kayitlari kaldirir, kimlikleri serbest birakir, filtreyi soker."""
    for kimlik in list(kimlikler):
        kaldir_fn(kimlik)
        _canli_kimlikler.discard(kimlik)
    kimlikler.clear()
    filtreyi_sok(filtre)


class KisayolServisi(QObject):
    """Global kisayollar: `kaydet`/`kaldir`/`hepsini_kaldir`/`kayitli`, sinyal `tetiklendi(ad)` (modul docstring'i)."""

    tetiklendi = Signal(str)

    def __init__(
        self,
        ebeveyn: QObject | None = None,
        *,
        gercek_win32: bool = False,
        kayit_fn: KayitFn | None = None,
        kaldir_fn: KaldirFn | None = None,
        hata_kodu_fn: HataKoduFn | None = None,
        altgr_karakteri_fn: AltgrKarakteriFn | None = None,
    ) -> None:
        if gercek_win32:
            if os.environ.get(GERCEK_KISAYOL_YASAK_DEGISKENI):
                raise RuntimeError(f"{GERCEK_KISAYOL_YASAK_DEGISKENI} ayarli: bu surecte gercek Win32 kisayol kaydi yasak (Y1)")
            kayit_fn = kayit_fn or _win32_kaydet
            kaldir_fn = kaldir_fn or _win32_kaldir
            hata_kodu_fn = hata_kodu_fn or _win32_hata_kodu
            altgr_karakteri_fn = altgr_karakteri_fn or altgr_karakteri
        for ad, fn in (("kayit_fn", kayit_fn), ("kaldir_fn", kaldir_fn), ("hata_kodu_fn", hata_kodu_fn),
                       ("altgr_karakteri_fn", altgr_karakteri_fn)):
            if fn is None:
                raise RuntimeError(f"gercek_win32=False iken {ad} verilmek zorunda (Y1: offscreen'de de gercek kayit olur)")
        assert kayit_fn is not None and kaldir_fn is not None and hata_kodu_fn is not None and altgr_karakteri_fn is not None
        app = _uygulama()
        super().__init__(ebeveyn)
        self._kayit_fn = kayit_fn
        self._kaldir_fn = kaldir_fn
        self._hata_kodu_fn = hata_kodu_fn
        self._altgr_karakteri_fn = altgr_karakteri_fn
        self._son_hata_kodu = 0
        kimlikler: dict[int, str] = {}  # id -> ad; filtre ve yikim temizleyicisiyle PAYLASILIR, yerinde degisir, yeniden baglanmaz
        filtre = _Filtre(kimlikler, weakref.ref(self))
        self._kimlikler = kimlikler
        self._kayitlar: dict[str, tuple[int, int, int]] = {}  # ad -> (id, mod, vk)
        self._filtre = filtre  # Qt sarmalayiciyi tutmaz (on olcum o3): guclu referans burada
        app.installNativeEventFilter(filtre)
        # K1 ▲ Y3: alici `self`siz -- bagli yontem PySide6 6.11'de kosmaz (KRT k5b A); `self` argumanlarda YOK.
        self.destroyed.connect(functools.partial(_yikimda_temizle, kimlikler, kaldir_fn, filtre, app.removeNativeEventFilter))

    # -- ozellikler ------------------------------------------------------------------------------
    @property
    def son_hata_kodu(self) -> int:
        """Son basarisiz `kayit_fn` sonrasi `hata_kodu_fn()`; basarili kayitta 0."""
        return self._son_hata_kodu

    @property
    def filtre(self) -> QAbstractNativeEventFilter:
        return self._filtre

    @staticmethod
    def kombinasyonu_coz(metin: str) -> tuple[int, int]:
        return kombinasyonu_coz(metin)

    def kayitli(self) -> dict[str, str]:
        """ad -> kanonik kombinasyon; KOPYA."""
        return {ad: kombinasyonu_yaz(mod, vk) for ad, (_, mod, vk) in self._kayitlar.items()}

    # -- islemler --------------------------------------------------------------------------------
    def kaydet(self, ad: str, kombinasyon: str) -> KayitSonucu:
        self._ana_thread_denetimi()
        try:
            mod, vk = kombinasyonu_coz(kombinasyon)
        except ValueError:
            return KayitSonucu.GECERSIZ
        if mod & (MOD_CONTROL | MOD_ALT) == MOD_CONTROL | MOD_ALT and not mod & MOD_SHIFT and self._altgr_karakteri_fn(vk):
            return KayitSonucu.ALTGR_CAKISMA
        self.kaldir(ad)
        if any((m, v) == (mod, vk) for _, m, v in self._kayitlar.values()):
            return KayitSonucu.CAKISMA
        kimlik = _yeni_kimlik()
        if not self._kayit_fn(kimlik, mod | MOD_NOREPEAT, vk):
            _canli_kimlikler.discard(kimlik)
            self._son_hata_kodu = int(self._hata_kodu_fn())
            return KayitSonucu.CAKISMA if self._son_hata_kodu == ERROR_HOTKEY_ALREADY_REGISTERED else KayitSonucu.HATA
        self._son_hata_kodu = 0
        self._kayitlar[ad] = (kimlik, mod, vk)
        self._kimlikler[kimlik] = ad
        return KayitSonucu.OK

    def kaldir(self, ad: str) -> None:
        self._ana_thread_denetimi()
        kayit = self._kayitlar.pop(ad, None)
        if kayit is None:
            return
        kimlik = kayit[0]
        self._kimlikler.pop(kimlik, None)
        _canli_kimlikler.discard(kimlik)
        self._kaldir_fn(kimlik)

    def hepsini_kaldir(self) -> None:
        self._ana_thread_denetimi()
        for ad in list(self._kayitlar):
            self.kaldir(ad)

    def _ana_thread_denetimi(self) -> None:
        if QThread.currentThread() is not _uygulama().thread():
            raise RuntimeError("KisayolServisi yalniz ana (GUI) thread'den kullanilir (K6)")
