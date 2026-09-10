"""D5 -- Olcum noktasi IHLAL EDILEBILIR mi? (bos kapi avi)

PROTOKOL §4.6/2: olculmeyen degismez `[OLCULMUYOR]` damgasi tasir. §4.6/7:
mekanizmayi kancalayan bir olcu, o mekanizmayi atlayan uygulamada SESSIZCE
bosalir -- kayit bos kalir ve denetim "ihlal yok" der.

Paket K8'in `capture_full` bacagini `[OLCULMUYOR]` damgalamisti. Bu dosya
BASKA bos olcum noktalari ariyor. Yontem: degismezi ihlal eden bir mutant kur,
BES kabul komutunu ayna agacinda kostur ve **hicbirinin dusmedigini** gor.

Bulunanlar (xfail(strict=True) ile isaretli): mutant kapilardan geciyor.
Kapi kapatilirsa bu testler XPASS verir ve kasitli olarak kirilir.
"""
from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

DEPO = Path(__file__).resolve().parents[4]
SERVICE = "src/capture/service.py"

M12_EXIT = [("    def __exit__(self, *_: object) -> None:\n        self.close()",
             "    def __exit__(self, *_: object) -> None:\n        return None")]
M13_CLOSE = [("        if self._tutamac is not None:\n"
              "            self._tutamac.close()\n"
              "            self._tutamac = None",
              "        if self._tutamac is not None:\n"
              "            self._tutamac.close()")]
M33_FULL = [
    ("        return self.capture_region(self._monitors[monitor_index])",
     "        m = self._monitors[monitor_index]\n"
     "        return self.capture_region(Rect(_np64(m.x), _np64(m.y), "
     "_np64(m.w), _np64(m.h), m.monitor_index, m.dpi_scale))"),
    ("def _ham_sozluk(rect: Rect) -> Mapping[str, object]:",
     "def _np64(v: int) -> int:\n"
     "    return np.int64(v)  # type: ignore[return-value]\n\n\n"
     "def _ham_sozluk(rect: Rect) -> Mapping[str, object]:"),
]


def _tum_kapilar(ayna, yamalar) -> dict[str, int]:  # type: ignore[no-untyped-def]
    ayna.geri_al()
    ayna.yaz(SERVICE, yamalar)
    try:
        s = ayna.kapilar()
        return {k: v for k, v in s.items() if not k.endswith("::cikti")}
    finally:
        ayna.geri_al()


# --------------------------------------------------------------------------
# BULGU 1 -- K10 `__exit__` -> close() degismezinin olcusu BOS
# --------------------------------------------------------------------------


def test_d5_uygulama_exit_close_cagiriyor() -> None:
    """Once uygulamanin DOGRU oldugunu goster: sorun kodda degil, kapida."""
    kod = """
        import sys, json, types
        sys.path.insert(0, r'{repo}')
        durum = {{'MSS': 0, 'close': 0}}
        class _M:
            def __init__(self, **k): durum['MSS'] += 1; self._k = False
            @property
            def monitors(self): return [{{'left':0,'top':0,'width':1,'height':1}}]
            def grab(self, box):
                import numpy as np
                class S:
                    __array_interface__ = {{'shape': (box['height'], box['width'], 4),
                                            'typestr': '|u1',
                                            'data': bytearray(box['height']*box['width']*4),
                                            'version': 3}}
                return S()
            def close(self):
                if not self._k: durum['close'] += 1; self._k = True
            def __enter__(self): return self
            def __exit__(self, *a): self.close(); return False
        m = types.ModuleType('mss'); m.MSS = _M
        sys.modules['mss'] = m
        from src.capture.service import MssBackend
        from src.contracts.models import Rect
        with MssBackend() as b:
            b.grab(Rect(0, 0, 2, 2))
            ic_kurulum, ic_kapatma = durum['MSS'], durum['close']
        print('JSON=' + json.dumps({{'ic_kurulum': ic_kurulum, 'ic_kapatma': ic_kapatma,
                                    'son_kapatma': durum['close']}}))
    """.format(repo=DEPO)
    r = subprocess.run([sys.executable, "-X", "utf8", "-c", textwrap.dedent(kod)],
                       cwd=str(DEPO), capture_output=True, text=True, encoding="utf-8")
    satir = next((s for s in r.stdout.splitlines() if s.startswith("JSON=")), None)
    assert satir is not None, f"sonda patladi:\n{r.stderr}"
    o = json.loads(satir[5:])
    assert o["ic_kurulum"] == 1, "grab uzun omurlu tutamaci kurmadi"
    assert o["ic_kapatma"] == 0, "`with` govdesi icinde tutamac zaten kapanmis"
    assert o["son_kapatma"] == 1, (
        "`__exit__` uzun omurlu MSS()'i KAPATMADI -> her `with` blogu bir window DC "
        "sizdirir (K10: 5001. kapatilmamis ornekte GetWindowDC kalici olarak duser)"
    )


@pytest.mark.xfail(
    strict=True,
    reason="BULGU D-1: K10'un `__exit__` -> close() degismezini BES kabul komutundan "
           "hicbiri olcmuyor. §3 casusu `with b:` kullanmiyor (yalniz b.close()), "
           "ve tek birim testi (`test_k1_mss_backend_yapimi_mss_e_dokunmaz`) "
           "sadece `ic is b` iddiasinda bulunuyor -- tutamac None oldugu icin "
           "close() zaten etkisiz. Olcum noktasi YAPISAL OLARAK BOS ve "
           "`[OLCULMUYOR]` damgasi TASIMIYOR (PROTOKOL §4.6/2).",
)
def test_d5_BULGU_exit_close_cagirmayan_uygulama_kapiya_takilmali(ayna) -> None:  # type: ignore[no-untyped-def]
    kapilar = _tum_kapilar(ayna, M12_EXIT)
    assert any(rc != 0 for rc in kapilar.values()), (
        f"`__exit__` close() cagirmiyor ama BES kapinin hepsi temiz: {kapilar}"
    )


# --------------------------------------------------------------------------
# BULGU 2 -- K10 close() idempotens olcusu (§3 `c2_close`) BOS
# --------------------------------------------------------------------------


def test_d5_uygulama_close_tutamaci_sifirliyor() -> None:
    """Uygulama dogru: close() sonrasi tutamac None, sonraki grab YENI kurar."""
    kod = """
        import sys, json, types
        sys.path.insert(0, r'{repo}')
        durum = {{'MSS': 0, 'close': 0}}
        class _M:
            def __init__(self, **k): durum['MSS'] += 1; self._k = False
            def grab(self, box):
                class S:
                    __array_interface__ = {{'shape': (box['height'], box['width'], 4),
                                            'typestr': '|u1',
                                            'data': bytearray(box['height']*box['width']*4),
                                            'version': 3}}
                return S()
            def close(self):
                if not self._k: durum['close'] += 1; self._k = True
            def __enter__(self): return self
            def __exit__(self, *a): self.close(); return False
        m = types.ModuleType('mss'); m.MSS = _M
        sys.modules['mss'] = m
        from src.capture.service import MssBackend
        from src.contracts.models import Rect
        b = MssBackend()
        b.grab(Rect(0, 0, 2, 2))
        b.close()
        tutamac_none = b._tutamac is None
        b.close()
        b.grab(Rect(0, 0, 2, 2))          # kapatildiktan SONRA
        print('JSON=' + json.dumps({{'tutamac_none': tutamac_none,
                                    'MSS': durum['MSS'], 'close': durum['close']}}))
    """.format(repo=DEPO)
    r = subprocess.run([sys.executable, "-X", "utf8", "-c", textwrap.dedent(kod)],
                       cwd=str(DEPO), capture_output=True, text=True, encoding="utf-8")
    satir = next((s for s in r.stdout.splitlines() if s.startswith("JSON=")), None)
    assert satir is not None, f"sonda patladi:\n{r.stderr}"
    o = json.loads(satir[5:])
    assert o["tutamac_none"] is True, (
        "close() tutamaci None yapmadi -> mss belgesi: 'Once the MSS object is "
        "closed, it may not be used again' (kapatilmis tutamacla grab)"
    )
    assert o["MSS"] == 2, "close() sonrasi grab YENI tutamac kurmadi"
    assert o["close"] == 1


@pytest.mark.xfail(
    strict=True,
    reason="BULGU D-2: §3'un `c2_close` olcusu YAPISAL OLARAK DUSEMEZ. Casus "
           "`_FakeMSS.close()` kendi icinde `self._closed` ile korunuyor (gercek "
           "`mss.MSS.close()` gibi), bu yuzden `MssBackend.close()` tutamaci "
           "sifirlamasa da sayac artmaz. `close() idempotenttir` degismezinin "
           "yanindaki OLCU sessizdir; gercek zarar KAPATILMIS TUTAMACLA GRAB'dir "
           "ve o hicbir kapida olculmez (PROTOKOL §4.6/7).",
)
def test_d5_BULGU_idempotent_olmayan_close_kapiya_takilmali(ayna) -> None:  # type: ignore[no-untyped-def]
    kapilar = _tum_kapilar(ayna, M13_CLOSE)
    assert any(rc != 0 for rc in kapilar.values()), (
        f"close() tutamaci sifirlamiyor ama BES kapinin hepsi temiz: {kapilar}"
    )


# --------------------------------------------------------------------------
# DOGRULAMA -- paketin `[OLCULMUYOR]` damgasi DURUST mu?
# --------------------------------------------------------------------------


def test_d5_capture_full_OLCULMUYOR_damgasi_durust(ayna) -> None:  # type: ignore[no-untyped-def]
    """K8'in `capture_full` duzlestirme bacagi gercekten ayirt etme gucu SIFIR mi?

    Paket bu bacagi `[OLCULMUYOR]` damgaladi (Y7-8). Damga durustse, o bacagi
    ihlal eden bir mutant BES kapidan da gecmeli -- ve gecti. Damga dogru.
    """
    kapilar = _tum_kapilar(ayna, M33_FULL)
    assert all(rc == 0 for rc in kapilar.values()), (
        f"damga yanlis: bacak aslinda olculuyor -> {kapilar}"
    )


def test_d5_gercek_kod_yolunda_capture_full_numpy_TASIYAMAZ() -> None:
    """Damganin gerekcesi: `_monitors` K5 tarafindan zaten duzlestirilmis."""
    from src.capture.monitors import rects_from_mss_monitors

    import numpy as np

    ham = [{"left": 0, "top": 0, "width": 100, "height": 100},
           {"left": np.int64(0), "top": np.int64(0),
            "width": np.uint32(100), "height": np.int32(100)}]
    (m,) = rects_from_mss_monitors(ham)
    assert type(m.x) is int and type(m.w) is int, (
        "K5 duzlestirmesi olmasaydi capture_full bacagi ihlal EDILEBILIR olurdu"
    )
