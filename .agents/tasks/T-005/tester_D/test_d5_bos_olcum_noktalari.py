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


def test_d5_TUR2_exit_close_cagirmayan_uygulama_kapiya_TAKILIYOR(ayna) -> None:  # type: ignore[no-untyped-def]
    """TUR 2'DE YENIDEN NISANLANDI (eski adi: `..._BULGU_...`, xfail(strict)).

    Tur 1'de bu test bir BULGU isaretcisiydi: M12 bes kapidan da geciyordu.
    Tur 2'de `test_service.py`'ye iki test eklendi; artik kapi kapali.
    """
    kapilar = _tum_kapilar(ayna, M12_EXIT)
    takilan = [ad for ad, rc in kapilar.items() if rc != 0]
    assert takilan, (
        f"GERILEME: `__exit__` close() cagirmiyor ama BES kapinin hepsi temiz: {kapilar}"
    )
    assert "G2-pytest" in takilan, (
        f"kapi kapali ama YANLIS katmanda: T2-1 olcusu `tests/` katmaninda "
        f"beklenir; takilan kapilar {takilan}"
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


def test_d5_TUR2_idempotent_olmayan_close_kapiya_TAKILIYOR(ayna) -> None:  # type: ignore[no-untyped-def]
    """TUR 2'DE YENIDEN NISANLANDI (eski adi: `..._BULGU_...`, xfail(strict))."""
    kapilar = _tum_kapilar(ayna, M13_CLOSE)
    takilan = [ad for ad, rc in kapilar.items() if rc != 0]
    assert takilan, (
        f"GERILEME: close() tutamaci sifirlamiyor ama BES kapinin hepsi temiz: {kapilar}"
    )
    assert "G2-pytest" in takilan, (
        f"kapi kapali ama YANLIS katmanda; takilan kapilar {takilan}"
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


# ==========================================================================
# TUR 2 -- duzeltme DEGISMEZI mi, YAZILDIGI BICIMI mi olcuyor?
# ==========================================================================

M53_EXIT_ISTISNA = [
    ("    def __exit__(self, *_: object) -> None:\n        self.close()",
     "    def __exit__(self, *_: object) -> None:\n"
     "        if not _ or _[0] is None:\n"
     "            self.close()"),
]
M54_ALAN_ADI = [
    ("    def __init__(self) -> None:\n        self._tutamac: mss.MSS | None = None",
     "    def __init__(self) -> None:\n        self._tutamac: mss.MSS | None = None\n"
     "        self._tutamac2: mss.MSS | None = None"),
    ("        if self._tutamac is None:\n"
     "            self._tutamac = mss.MSS()\n"
     '        kutu = {"left": rect.x, "top": rect.y, "width": rect.w, "height": rect.h}\n'
     "        return np.asarray(self._tutamac.grab(kutu), dtype=np.uint8)",
     "        if self._tutamac2 is None:\n"
     "            self._tutamac2 = mss.MSS()\n"
     '        kutu = {"left": rect.x, "top": rect.y, "width": rect.w, "height": rect.h}\n'
     "        return np.asarray(self._tutamac2.grab(kutu), dtype=np.uint8)"),
]

_ISTISNA_SONDASI = """
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
    try:
        with MssBackend() as b:
            b.grab(Rect(0, 0, 2, 2))
            raise RuntimeError('govde patladi')     # ISTISNA yolu
    except RuntimeError:
        pass
    print('JSON=' + json.dumps({{'MSS': durum['MSS'], 'close': durum['close'],
                                'tutamac_none': b._tutamac is None}}))
"""


def test_d5_TUR2_uygulama_ISTISNA_yolunda_da_kapatiyor() -> None:
    """POZITIF KONTROL: teslim edilen kod istisna yolunda da tutamaci kapatiyor.

    Yani asagidaki BULGU bir kod hatasi degil, bir KAPI deligidir: urun dogru,
    olcu o dali hic gormuyor.
    """
    r = subprocess.run(
        [sys.executable, "-X", "utf8", "-c", textwrap.dedent(_ISTISNA_SONDASI).format(repo=DEPO)],
        cwd=str(DEPO), capture_output=True, text=True, encoding="utf-8")
    satir = next((s for s in r.stdout.splitlines() if s.startswith("JSON=")), None)
    assert satir is not None, f"sonda patladi:\n{r.stderr}"
    o = json.loads(satir[5:])
    assert o["MSS"] == 1, "grab uzun omurlu tutamaci kurmadi"
    assert o["close"] == 1, (
        "ISTISNA ile cikilan `with` blogunda tutamac KAPATILMADI (urun hatasi olurdu)"
    )
    assert o["tutamac_none"] is True


@pytest.mark.xfail(
    strict=True,
    reason="BULGU D-2.1 (tur 2): T2-1'in eklendigi olcu `__exit__`'i YALNIZ "
           "istisnasiz cikista kosuyor. `__exit__`'i 'yalnizca exc_type is None "
           "ise close()' yapan bir uygulama (M53) BES kabul komutundan da temiz "
           "geciyor -- oysa K10 'her `with` blogu bir window DC sizdirir, 5001. "
           "kapatilmamis ornekte GetWindowDC kalici olarak duser' diyor ve "
           "`CaptureError` ile biten bir `with` govdesi urunun NORMAL hata "
           "yoludur (K6 sinif b/c). PROTOKOL §4.6/7: davranissal olcu, kapsadigi "
           "uzayin EN AZ IKI noktasinda kosmali; istisna/istisnasiz ekseninde "
           "tek nokta var. `[OLCULMUYOR]` damgasi da yok (§4.6/2).",
)
def test_d5_TUR2_BULGU_exit_ISTISNA_yolu_olculmuyor(ayna) -> None:  # type: ignore[no-untyped-def]
    kapilar = _tum_kapilar(ayna, M53_EXIT_ISTISNA)
    assert any(rc != 0 for rc in kapilar.values()), (
        f"`__exit__` istisna yolunda close() cagirmiyor ama BES kapi da temiz: {kapilar}"
    )


def test_d5_TUR2_enjekte_edilen_alan_URETIMIN_yazdigi_alan_mi(ayna) -> None:  # type: ignore[no-untyped-def]
    """TOTOLOJI SONDASI: yeni testler `_tutamac`'a DOGRUDAN yaziyor.

    Uretimin gercekten o alani kullandigini ne bagliyor? Sonda: `grab()`
    tutamaci BASKA bir alana (`_tutamac2`) yazsin, `close()`/`__exit__` yine
    `_tutamac`'a baksin. Enjeksiyon testleri bunu GOREMEZ (kendi enjekte
    ettikleri alani kapatiyorlar) -- ama bir kapi gormeli.
    """
    kapilar = _tum_kapilar(ayna, M54_ALAN_ADI)
    takilan = [ad for ad, rc in kapilar.items() if rc != 0]
    assert takilan, (
        "TOTOLOJI: sahte tutamac enjeksiyonu uretimin kurdugu duruma BAGLI DEGIL -- "
        f"alan adini degistiren uygulama bes kapidan da geciyor: {kapilar}"
    )
    assert takilan == ["G3-headless"], (
        f"bagi tutan kapi degisti (beklenen yalniz §3'un close sayaci): {takilan}"
    )
