"""MERCEK C/6 -- `MssBackend`'in OMRU (K10).

*Hangi durum hic test edilmemis?*

`MssBackend`'in gizli durumu tek bir alandir: uzun omurlu `grab` tutamaci.
Onun durum makinesi `yok -> kurulu -> kapali` uclusudur ve gecisleri
`grab()`, `close()`, `__enter__`/`__exit__` yapar. Bu makine test paketiyle
OLCULEMEZ (K1: gercek ekran yasak), bu yuzden burada `headless_check.py`
§3'un yontemi kullanilir: alt-surecte `sys.modules["mss"]`'e SAYACLI bir
casus modul konur. `headless_check` §3 dort noktayi olcuyor (tembellik,
cagri basina kur+kapat, tutamacin tekligi, `close` idempotansi); bu dosya
onun ATLADIGI gecisleri olcer:

  * `monitors()` 5001 cagri -- sefin olctugu olum noktasi; kurulum sayisi
    kapatma sayisina esit mi, AYNI ANDA acik ornek sayisi 1'i asiyor mu;
  * `close()` SONRASI `grab()` -- kapali tutamac yeniden kullaniliyor mu
    (gercek `mss` "kapatilan MSS tekrar kullanilamaz" der) yoksa yenisi mi
    kuruluyor;
  * IC ICE `with` -- ic cikis tutamaci kapatirken dis blok ne goruyor;
  * `with` govdesinde istisna -- `__exit__` yutuyor mu, kapatiyor mu;
  * `monitors()` ile `grab()` tutamaclarinin BAGIMSIZLIGI.

Casus, gercek `mss` gibi davranir: `MSS.monitors` ornek uzerinde memoize
edilir, `close()` idempotenttir, `ScreenShot.__array_interface__` ham
tampon nesnesini tasir.
"""
from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any

import pytest

KOK = Path(__file__).resolve().parents[4]

_SONDA = r"""
import sys, types, json
sys.path.insert(0, r'{kok}')
import numpy as np

RAW = [
    {{'left': -2560, 'top': 0, 'width': 5120, 'height': 1440}},
    {{'left': -2560, 'top': 0, 'width': 2560, 'height': 1440, 'is_primary': False}},
    {{'left': 0, 'top': 0, 'width': 2560, 'height': 1440, 'is_primary': True}},
]
PATTERN = b'\x01\x02\x03\xff'
d = {{'raw': RAW, 'MSS': 0, 'close': 0, 'canli': 0, 'zirve': 0,
      'mss_dep': 0, 'son': None, 'kapat_patlat': False, 'kapali_grab': 0}}

class _Shot:
    def __init__(self, box):
        self.width, self.height = box['width'], box['height']
        self.size = (self.width, self.height)
        self.raw = bytearray(PATTERN * (self.width * self.height))
        self.bgra = bytes(self.raw)
    @property
    def __array_interface__(self):
        return {{'shape': (self.height, self.width, 4), 'typestr': '|u1',
                'data': self.raw, 'version': 3}}

class _FakeMSS:
    def __init__(self, **kw):
        d['MSS'] += 1
        d['canli'] += 1
        d['zirve'] = max(d['zirve'], d['canli'])
        d['son'] = self
        self._closed = False
        self._monitors = None
    @property
    def monitors(self):
        if self._monitors is None:
            self._monitors = [dict(m) for m in d['raw']]
        return self._monitors
    def grab(self, box):
        if self._closed:
            d['kapali_grab'] += 1
            raise OSError('kapali MSS uzerinde grab')
        return _Shot(box)
    def close(self):
        if d['kapat_patlat']:
            raise OSError('close patladi')
        if not self._closed:
            d['close'] += 1
            d['canli'] -= 1
            self._closed = True
    def __enter__(self):
        return self
    def __exit__(self, *a):
        self.close(); return False

def _dep(*a, **k):
    d['mss_dep'] += 1
    return _FakeMSS()

spy = types.ModuleType('mss'); spy.MSS = _FakeMSS; spy.mss = _dep
sys.modules['mss'] = spy

from src.capture.service import MssBackend
from src.contracts.models import Rect

R = Rect(10, 20, 64, 16)
out = {{}}

def sifirla():
    d.update(MSS=0, close=0, canli=0, zirve=0, kapali_grab=0)

# --- A: monitors() 5001 cagri -- sefin olctugu olum noktasi
sifirla()
b = MssBackend()
out['A_init_MSS'] = d['MSS']
N = 5001
for _ in range(N):
    b.monitors()
out['A_N'] = N
out['A_MSS'] = d['MSS']
out['A_close'] = d['close']
out['A_canli'] = d['canli']
out['A_zirve'] = d['zirve']
b.close()
out['A_close_sonrasi'] = d['close']

# --- B: grab tutamaci TEK ve kimligi sabit
sifirla()
b = MssBackend()
b.grab(R); ilk = d['son']
b.grab(R); b.grab(R); b.grab(R)
out['B_MSS'] = d['MSS']
out['B_kimlik_sabit'] = bool(d['son'] is ilk)
out['B_canli'] = d['canli']

# --- B2: monitors() grab tutamacini KULLANMAZ / BOZMAZ
b.monitors()
out['B2_MSS'] = d['MSS']
out['B2_close'] = d['close']
b.grab(R)
out['B2_grab_sonrasi_MSS'] = d['MSS']
b.close()
out['B2_son_close'] = d['close']
out['B2_son_canli'] = d['canli']

# --- C: close() idempotent + close() SONRASI grab()
sifirla()
b = MssBackend()
b.grab(R); kapatilan = d['son']
b.close(); out['C_close1'] = d['close']
b.close(); out['C_close2'] = d['close']
try:
    a = b.grab(R)
    out['C_grab_sonrasi'] = 'calisti'
    out['C_yeni_MSS'] = d['MSS']
    out['C_kapaliyi_kullandi'] = bool(d['kapali_grab'] > 0)
    out['C_shape'] = list(np.asarray(a).shape)
except Exception as e:
    out['C_grab_sonrasi'] = type(e).__name__
    out['C_yeni_MSS'] = d['MSS']
    out['C_kapaliyi_kullandi'] = bool(d['kapali_grab'] > 0)
b.close()
out['C_son_canli'] = d['canli']
out['C_son_sizinti'] = d['MSS'] - d['close']

# --- D: IC ICE with
sifirla()
b = MssBackend()
with b as x1:
    b.grab(R)
    ic_MSS = d['MSS']
    with b as x2:
        b.grab(R)
    out['D_ic_cikis_close'] = d['close']
    out['D_ic_cikis_canli'] = d['canli']
    b.grab(R)
    out['D_dis_grab_yeni_MSS'] = d['MSS'] - ic_MSS
out['D_x1_self'] = bool(x1 is b)
out['D_x2_self'] = bool(x2 is b)
out['D_son_close'] = d['close']
out['D_sizinti'] = d['MSS'] - d['close']

# --- E: with govdesinde istisna
sifirla()
try:
    with MssBackend() as b:
        b.grab(R)
        raise ValueError('blok icinde patlama')
except ValueError:
    out['E_yutuldu'] = False
except BaseException as e:
    out['E_yutuldu'] = 'baska:' + type(e).__name__
else:
    out['E_yutuldu'] = True
out['E_close'] = d['close']
out['E_canli'] = d['canli']

# --- F: tembellik -- grab yoksa mss'e HIC dokunulmaz
sifirla()
b = MssBackend()
b.close()
with MssBackend():
    pass
out['F_MSS'] = d['MSS']
out['F_close'] = d['close']

# --- G: tutamacin close()'u firlatirsa idempotans
sifirla()
b = MssBackend()
b.grab(R)
d['kapat_patlat'] = True
try:
    b.close(); out['G_1'] = 'sessiz'
except Exception as e:
    out['G_1'] = type(e).__name__
try:
    b.close(); out['G_2'] = 'sessiz'
except Exception as e:
    out['G_2'] = type(e).__name__
d['kapat_patlat'] = False
b.close()
out['G_3_close'] = d['close']
out['G_3_canli'] = d['canli']

# --- H: monitors() CANLI + donen liste sonraki cagriyi etkilemiyor
sifirla()
b = MssBackend()
m1 = b.monitors()
d['raw'] = RAW[:2]
m2 = b.monitors()
d['raw'] = RAW
try:
    m1[0]['left'] = 999999
    m1_bozuldu = True
except Exception:
    m1_bozuldu = False
m3 = b.monitors()
out['H_len'] = [len(m1), len(m2), len(m3)]
out['H_m1_bozulabildi'] = m1_bozuldu
out['H_m3_left'] = m3[0]['left']
out['H_MSS'] = d['MSS']
out['H_close'] = d['close']
out['H_canli'] = d['canli']

out['DEP_mss'] = d['mss_dep']
print('JSON=' + json.dumps(out))
"""


@pytest.fixture(scope="module")
def olcum() -> dict[str, Any]:
    """Casus modulu alt-surecte kosar ve butun omur olcumlerini dondurur."""
    r = subprocess.run(
        [sys.executable, "-X", "utf8", "-c", textwrap.dedent(_SONDA).format(kok=KOK)],
        cwd=str(KOK),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    satir = next(
        (ln for ln in r.stdout.splitlines() if ln.startswith("JSON=")), None
    )
    assert r.returncode == 0 and satir is not None, (
        f"casus sondasi tamamlanamadi (exit {r.returncode})\n"
        f"STDOUT:\n{r.stdout[-2000:]}\nSTDERR:\n{r.stderr[-2000:]}"
    )
    return dict(json.loads(satir[5:]))


# =========================================================================
# A -- 5001 cagri: sefin olctugu olum noktasi
# =========================================================================


def test_c6_monitors_5001_cagride_kurulum_kapatmaya_ESIT(olcum: dict[str, Any]) -> None:
    """Sefin olctugu tam esikte sizinti sifir olmali.

    `mss`'te `__del__` yoktur: kapatilmayan her `MSS()` bir window DC +
    memory DC sizdirir ve **5001.** ornekte `GetWindowDC` kalici olarak
    duser. Cagri basina TAM 1 kurulum + TAM 1 kapatma degismezi tam bunu
    engeller.
    """
    assert olcum["A_MSS"] == olcum["A_N"]
    assert olcum["A_close"] == olcum["A_N"]
    assert olcum["A_MSS"] - olcum["A_close"] == 0


def test_c6_monitors_ayni_anda_acik_ornek_1_i_asmaz(olcum: dict[str, Any]) -> None:
    """5001 cagri boyunca AYNI ANDA acik `MSS` sayisi hic 1'i asmadi.

    Toplam sayacin esitlenmesi yetmez: en sonda kapatan bir uygulama da
    esitlenirdi ama arada 5001 tutamaci ayni anda acik tutardi. Olculen
    sey zirve degeridir.
    """
    assert olcum["A_zirve"] <= 1
    assert olcum["A_canli"] == 0


def test_c6_monitors_grab_tutamacini_KURMAZ(olcum: dict[str, Any]) -> None:
    """5001 `monitors()` sonrasi `close()` kapatacak bir sey BULMAZ."""
    assert olcum["A_close_sonrasi"] == olcum["A_close"]


def test_c6_yapim_mss_e_dokunmaz(olcum: dict[str, Any]) -> None:
    assert olcum["A_init_MSS"] == 0
    assert olcum["F_MSS"] == 0 and olcum["F_close"] == 0


def test_c6_kullanimdan_kalkmis_mss_mss_cagrilmaz(olcum: dict[str, Any]) -> None:
    assert olcum["DEP_mss"] == 0


# =========================================================================
# B -- uzun omurlu grab tutamaci
# =========================================================================


def test_c6_grab_tutamaci_TEK_ve_kimligi_sabit(olcum: dict[str, Any]) -> None:
    assert olcum["B_MSS"] == 1
    assert olcum["B_kimlik_sabit"] is True
    assert olcum["B_canli"] == 1


def test_c6_monitors_grab_tutamacini_BOZMAZ(olcum: dict[str, Any]) -> None:
    """`grab` ile `monitors` iki AYRI omur: aralarina giren `monitors()`
    cagrisi ne tutamaci kapatir ne de sonraki `grab`'i yeni kuruluma zorlar."""
    assert olcum["B2_MSS"] == 2  # 1 grab tutamaci + 1 monitors oturumu
    assert olcum["B2_close"] == 1  # yalniz monitors oturumu kapandi
    assert olcum["B2_grab_sonrasi_MSS"] == 2  # grab YENI kurulum yapmadi
    assert olcum["B2_son_close"] == 2 and olcum["B2_son_canli"] == 0


# =========================================================================
# C -- close() sonrasi durum
# =========================================================================


def test_c6_close_idempotent(olcum: dict[str, Any]) -> None:
    assert olcum["C_close1"] == 1
    assert olcum["C_close2"] == 1


def test_c6_close_sonrasi_grab_KAPALI_tutamaci_KULLANMAZ(olcum: dict[str, Any]) -> None:
    """Gercek `mss`: "kapatilan MSS tekrar kullanilamaz".

    Olculen degismez budur: `close()` sonrasi bir `grab()` kapali tutamaca
    DONMEZ. Uygulamanin secimi yeni bir tutamac kurmak (yeniden dogus);
    paket bu gecisi tanimlamiyor, davranis burada kayda gecer ve sizinti
    birakmadigi ayrica olculur.
    """
    assert olcum["C_kapaliyi_kullandi"] is False
    assert olcum["C_grab_sonrasi"] == "calisti"
    assert olcum["C_yeni_MSS"] == 2
    assert olcum["C_shape"] == [16, 64, 4]


def test_c6_yeniden_dogan_tutamac_da_kapanir(olcum: dict[str, Any]) -> None:
    assert olcum["C_son_canli"] == 0
    assert olcum["C_son_sizinti"] == 0


def test_c6_tutamacin_close_u_firlarsa_idempotans_KAYBOLUR(
    olcum: dict[str, Any],
) -> None:
    """[BULGU-NOT] `close()`, alttaki tutamacin `close()`'u firlatirsa
    ikinci cagrida da firlatir.

    `close()` `self._tutamac = None` atamasini yalnizca basarili kapatmadan
    SONRA yapar, bu yuzden hatali bir tutamacta idempotans sozu tutmaz.
    GERCEK `mss` bu durumu uretmez -- `mss/base.py` `close()`'u kendi icinde
    idempotenttir ve "safe to call this multiple times" der -- bu yuzden bu
    bir ret gerekcesi DEGILDIR; yeniden deneme imkani veren savunulabilir
    bir tercihtir. Davranis degisirse gorunsun diye olculur.
    """
    assert olcum["G_1"] == "OSError"
    assert olcum["G_2"] == "OSError"
    assert olcum["G_3_close"] == 1
    assert olcum["G_3_canli"] == 0


# =========================================================================
# D/E -- baglam yoneticisi
# =========================================================================


def test_c6_baglam_yoneticisi_kendini_dondurur(olcum: dict[str, Any]) -> None:
    assert olcum["D_x1_self"] is True and olcum["D_x2_self"] is True


def test_c6_ic_ice_with_ic_cikista_tutamaci_KAPATIR(olcum: dict[str, Any]) -> None:
    """[KAYIT] `MssBackend` YENIDEN GIRISLI (reentrant) DEGILDIR.

    Ic `with`'in cikisi tutamaci kapatir; dis blok hala aciktir. Olculen
    sonuc: dis bloktaki bir sonraki `grab()` sessizce YENI bir tutamac kurar
    ve dis cikis onu kapatir -- yani cokme yok, SIZINTI yok, ama ic ice
    kullanim bir kurulum maliyeti odetir. Paket ic ice kullanimi
    tanimlamiyor.
    """
    assert olcum["D_ic_cikis_close"] == 1
    assert olcum["D_ic_cikis_canli"] == 0
    assert olcum["D_dis_grab_yeni_MSS"] == 1
    assert olcum["D_son_close"] == 2
    assert olcum["D_sizinti"] == 0


def test_c6_with_govdesindeki_istisna_YUTULMAZ_ve_tutamac_kapanir(
    olcum: dict[str, Any],
) -> None:
    """`__exit__` `None` dondurur (falsy) -- istisnayi bastirmaz."""
    assert olcum["E_yutuldu"] is False
    assert olcum["E_close"] == 1
    assert olcum["E_canli"] == 0


# =========================================================================
# H -- monitors() canliligi
# =========================================================================


def test_c6_monitors_CANLI_kumeyi_dondurur(olcum: dict[str, Any]) -> None:
    """Casusun listesi 3 -> 2 -> 3 degistiginde her cagri YENISINI gorur."""
    assert olcum["H_len"] == [3, 2, 3]


def test_c6_monitors_donusu_sonraki_cagriyi_ETKILEMEZ(olcum: dict[str, Any]) -> None:
    """Donen listeyi bozmak sonraki cagriyi kirletmiyor (K10: tercih, kapi degil)."""
    assert olcum["H_m1_bozulabildi"] is True
    assert olcum["H_m3_left"] == -2560


def test_c6_monitors_her_cagrida_kur_ve_kapat(olcum: dict[str, Any]) -> None:
    assert olcum["H_MSS"] == 3
    assert olcum["H_close"] == 3
    assert olcum["H_canli"] == 0
