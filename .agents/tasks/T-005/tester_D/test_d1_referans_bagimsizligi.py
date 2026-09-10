"""D1 -- Olcu, denetledigi uygulamanin URETTIGI veriden referans turetiyor mu?

PROTOKOL §4.6/8. Gecmisteki kacis (Y6-2): `headless_check` §3 `grab` donusunu
`np.asarray` ile olcuyordu; yani K7'nin YASAKLADIGI sessiz donusumu
denetleyicinin icinde yaparak ham `ScreenShot` donduren bir `MssBackend.grab`'i
akliyordu.

Burada iki sey olculur:
  (a) statik: §3 kaydinda `grab_isinstance` BEKLENTISI var ve `np.asarray`
      yalnizca isinstance ihlali kaydedildikten SONRA kullaniliyor;
  (b) davranissal: gercekten ham `ScreenShot` donduren bir `grab` ayna
      agacinda §3'u DUSURUYOR mu.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import numpy as np
import pytest

from src.capture.service import CaptureService, FakeBackend
from src.contracts.errors import CaptureError
from src.contracts.models import Rect

DEPO = Path(__file__).resolve().parents[4]
KAPI_METNI = (DEPO / ".agents" / "tasks" / "T-005" / "headless_check.py").read_text(
    encoding="utf-8"
)
SERVICE = "src/capture/service.py"

# Olcu YALNIZCA §3'un casus sonda METNINDE aranir; modul docstring'i eski
# hatalari ANLATTIGI icin (`np.asarray(a1)` orada da geciyor) tum dosyada
# arama yanlis sonuc verir.
_i = KAPI_METNI.index("_SPY_PROBE = ")
_j = KAPI_METNI.index("def check_3_spy_backend")
SONDA_METNI = KAPI_METNI[_i:_j]

M_SOL = Rect(-2560, 0, 2560, 1440)
M_SAG = Rect(0, 0, 2560, 1440)
DUZEN = (M_SOL, M_SAG)


def test_d1_kapi_tip_denetimini_donusumden_ONCE_yapiyor() -> None:
    """§3'te `isinstance` olcusu `np.asarray`'den ONCE gelmeli."""
    i_isinstance = SONDA_METNI.index("out['grab_isinstance']")
    i_asarray = SONDA_METNI.index("np.asarray(a1)")
    assert i_isinstance < i_asarray, (
        "§3 once np.asarray yapiyor -> denetleyici K7'nin yasakladigi donusumu "
        "kendi icinde yapip ham ScreenShot donduren bir grab'i aklar (Y6-2)"
    )
    assert '"grab_isinstance": (True,' in KAPI_METNI, (
        "§3 `grab_isinstance` beklentisini KAYDA yazmiyor -> olcum kaydediliyor "
        "ama ihlal uretmiyor"
    )


def test_d1_kapi_icerik_referansi_CASUSUN_baytlarindan_geliyor() -> None:
    """Icerik referansi uygulamanin ciktisindan degil, casusun desenli baytlarindan."""
    m = re.search(r"PATTERN\s*=\s*b'([^']*)'", SONDA_METNI)
    assert m is not None, "§3'te PATTERN sabiti yok -> icerik referansi yok"
    # Alt-surece giden kaynakta ciftlenmis kacislar var; desenin DORT baytini
    # sirasiyla tasidigini dogrula (01 02 03 FF).
    baytlar = [p.lower() for p in re.findall(r"x([0-9a-fA-F]{2})", m.group(1))]
    assert baytlar == ["01", "02", "03", "ff"], (
        f"§3 casusunun deseni beklenen 01 02 03 FF degil: {m.group(1)!r} -> "
        "icerik olcusu kanal sirasini ayirt edemez"
    )
    assert "want = np.frombuffer(PATTERN, dtype=np.uint8)" in KAPI_METNI, (
        "§3 icerik referansini casusun PATTERN'inden turetmiyor -> olcu yalnizca "
        "'kendi icinde tutarli mi' sorar"
    )


def test_d1_ham_screenshot_donduren_grab_kapidan_GECEMEZ(ayna) -> None:  # type: ignore[no-untyped-def]
    """M06: `MssBackend.grab` np.asarray yapmadan ham ScreenShot dondurur."""
    ayna.geri_al()
    ayna.yaz(SERVICE, [(
        "return np.asarray(self._tutamac.grab(kutu), dtype=np.uint8)",
        "return self._tutamac.grab(kutu)  # type: ignore[return-value]",
    )])
    try:
        s = ayna.kapilar(["G3-headless"])
        assert s["G3-headless"] != 0, (
            "ham ScreenShot donduren grab §3'ten GECTI -> olcu kendi icinde "
            "sessiz donusum yapiyor demektir (Y6-2 gerilemesi)"
        )
        assert "grab_isinstance" in s["G3-headless::cikti"]
    finally:
        ayna.geri_al()


def test_d1_ekrani_OKUMAYAN_grab_kapidan_GECEMEZ(ayna) -> None:  # type: ignore[no-untyped-def]
    """Dogru sekil/dtype ureten ama ekrani hic okumayan grab §3'te dusmeli."""
    ayna.geri_al()
    ayna.yaz(SERVICE, [(
        "return np.asarray(self._tutamac.grab(kutu), dtype=np.uint8)",
        "self._tutamac.grab(kutu)\n"
        "        return np.zeros((rect.h, rect.w, 4), dtype=np.uint8)",
    )])
    try:
        s = ayna.kapilar(["G3-headless"])
        assert s["G3-headless"] != 0, (
            "ekrani okumayan grab §3'ten GECTI -> icerik olcusu bos"
        )
        assert "grab_content_ok" in s["G3-headless::cikti"]
    finally:
        ayna.geri_al()


def test_d1_servis_K7_dogrulamasinda_donusum_YAPMIYOR() -> None:
    """Uygulama tarafi: `_bicimi_dogrula` kaynaginda np.asarray/np.array yok."""
    kaynak = (DEPO / SERVICE).read_text(encoding="utf-8")
    agac = ast.parse(kaynak)
    for n in ast.walk(agac):
        if isinstance(n, ast.FunctionDef) and n.name == "_bicimi_dogrula":
            gorunur = list(n.body)
            if (gorunur and isinstance(gorunur[0], ast.Expr)
                    and isinstance(gorunur[0].value, ast.Constant)):
                gorunur = gorunur[1:]          # docstring ESKI HATAYI anlatiyor
            govde = chr(10).join(ast.unparse(s) for s in gorunur)
            assert "asarray" not in govde and "np.array(" not in govde, (
                "K7 dogrulamasi icinde sessiz donusum var"
            )
            assert "isinstance" in govde
            break
    else:  # pragma: no cover -- fonksiyon her zaman var
        pytest.fail("_bicimi_dogrula bulunamadi")


def test_d1_servis_ham_screenshot_benzerini_REDDEDER() -> None:
    """Canli olcu: `__array_interface__` tasiyan nesne -> CaptureError."""

    class _Shot:
        def __init__(self, h: int, w: int) -> None:
            self._h, self._w = h, w
            self._t = bytearray(b"\x01\x02\x03\xff" * (h * w))

        @property
        def __array_interface__(self) -> dict[str, object]:
            return {"shape": (self._h, self._w, 4), "typestr": "|u1",
                    "data": self._t, "version": 3}

    # Bagimsiz kanal: np.asarray onu SESSIZCE (h,w,4) uint8 yapiyor.
    kontrol = np.asarray(_Shot(4, 6))
    assert kontrol.shape == (4, 6, 4) and kontrol.dtype == np.uint8

    fb = FakeBackend(DUZEN, lambda r: _Shot(r.h, r.w))
    servis = CaptureService(fb, lambda: 0.0)
    with pytest.raises(CaptureError):
        servis.capture_region(Rect(0, 0, 6, 4))
    assert fb.grab_calls == 1
