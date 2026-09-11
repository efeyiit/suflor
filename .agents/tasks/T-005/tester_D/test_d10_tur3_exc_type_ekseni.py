"""D10 -- TUR 3: `exc_type` ekseni GERCEKTEN kapandi mi?

Sef T3-1'de "cikis yolu ekseni tam 2 ayrik sinif alir, ucuncu varyant yok,
iki parametre ekseni TAMAMEN kapatir" dedi. Bu dosya o iddiayi UC parcaya
ayirip her birini ayri olcer:

  (1) CIKIS YOLU ekseni 2 sinifa cokuyor            -> DOGRU (yapisal olcum)
  (2) parametrizasyon eski kapsami KAYBETMEDI       -> DOGRU (bacak basina)
  (3) "iki parametre ekseni TAMAMEN kapatir"        -> YANLIS (deger ekseni)

(3) bloke DEGIL: uygulama dogru, kacan sinif urunun hicbir cagri yerinde
erisilebilir degil (uretimde `with MssBackend()` yok). `xfail(strict)` ile
ADLANDIRILMIS TESTER YUKUMLULUGU olarak isaretli -- kapi kapanirsa XPASS
verir ve kasitli olarak kirilir.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

DEPO = Path(__file__).resolve().parents[4]
SERVICE = "src/capture/service.py"
TEST = "tests/unit/capture/test_service.py"
NODE = TEST + "::test_k10_exit_uzun_omurlu_tutamaci_kapatir"

EXIT_ESKI = "    def __exit__(self, *_: object) -> None:\n        self.close()"
IMZA3 = (
    "    def __exit__(\n"
    "        self,\n"
    "        exc_type: type[BaseException] | None,\n"
    "        exc: BaseException | None,\n"
    "        tb: object,\n"
    "    ) -> "
)


def _exit3(donus: str, govde: str) -> list[tuple[str, str]]:
    return [(EXIT_ESKI, IMZA3 + donus + ":\n" + govde)]


M12 = [(EXIT_ESKI, "    def __exit__(self, *_: object) -> None:\n        return None")]
M50 = [(EXIT_ESKI, "    def __exit__(self, *_: object) -> None:\n        self._tutamac = None")]
M53 = [(EXIT_ESKI, "    def __exit__(self, *_: object) -> None:\n"
                   "        if not _ or _[0] is None:\n            self.close()")]
M53T = [(EXIT_ESKI, "    def __exit__(self, *_: object) -> None:\n"
                    "        if _ and _[0] is not None:\n            self.close()")]
M63 = [(EXIT_ESKI, "    def __exit__(self, *_: object) -> bool:\n"
                   "        self.close()\n        return True")]
M61 = _exit3("None", "        if exc_type is None or exc_type is CaptureError:\n"
                     "            self.close()")
M62 = _exit3("None", "        if exc_type is None or issubclass(exc_type, Exception):\n"
                     "            self.close()")
M64 = _exit3("bool", "        self.close()\n"
                     "        return exc_type is not None and not issubclass(\n"
                     "            exc_type, CaptureError\n        )")
M66_KONTROL = [(EXIT_ESKI, "    def __exit__(self, *_: object) -> None:\n"
                           "        if self._tutamac is not None:\n"
                           "            self._tutamac.close()\n"
                           "            self._tutamac = None")]
S1_ENTER_ONCEDEN_KAPATIR = [(
    "    def __enter__(self) -> MssBackend:\n        return self",
    "    def __enter__(self) -> MssBackend:\n        self.close()\n        return self",
)]


# --------------------------------------------------------------------------
# (1) CIKIS YOLU ekseni -- yapisal olcum
# --------------------------------------------------------------------------


class _Sonda:
    def __init__(self) -> None:
        self.tipler: list[object] = []

    def __enter__(self) -> _Sonda:
        return self

    def __exit__(self, t: object, v: object, tb: object) -> None:
        self.tipler.append(t)


def _yollar(s: _Sonda) -> dict[str, object]:
    from src.contracts.errors import CaptureError

    goruldu: dict[str, object] = {}

    with s:
        pass
    goruldu["normal"] = s.tipler[-1]

    def f_return() -> int:
        with s:
            return 1
        return 0  # pragma: no cover
    f_return()
    goruldu["return"] = s.tipler[-1]

    for _ in range(2):
        with s:
            break
    goruldu["break"] = s.tipler[-1]

    for _ in range(1):
        with s:
            continue
    goruldu["continue"] = s.tipler[-1]

    try:
        with s:
            raise CaptureError("x")
    except CaptureError:
        pass
    goruldu["CaptureError"] = s.tipler[-1]

    try:
        with s:
            raise KeyboardInterrupt
    except KeyboardInterrupt:
        pass
    goruldu["KeyboardInterrupt"] = s.tipler[-1]

    def g() -> Any:
        with s:
            yield 1
    it = g()
    next(it)
    it.close()
    goruldu["generator.close()"] = s.tipler[-1]

    def g2() -> Any:
        with s:
            yield 1
    it2 = g2()
    next(it2)
    try:
        next(it2)
    except StopIteration:
        pass
    goruldu["uretec tuketildi"] = s.tipler[-1]

    return goruldu


def test_d10_cikis_yolu_ekseni_IKI_sinifa_cokuyor() -> None:
    """Sefin (A) iddiasi: return/break/continue -> None; istisna/GeneratorExit -> tip."""
    goruldu = _yollar(_Sonda())
    none_sinifi = {k for k, v in goruldu.items() if v is None}
    istisna_sinifi = {k for k, v in goruldu.items() if v is not None}
    assert none_sinifi == {"normal", "return", "break", "continue", "uretec tuketildi"}
    assert istisna_sinifi == {"CaptureError", "KeyboardInterrupt", "generator.close()"}
    assert goruldu["generator.close()"] is GeneratorExit
    # ucuncu bir SINIF yok: her yol ya None ya bir tip
    assert all(v is None or isinstance(v, type) for v in goruldu.values())


def test_d10_exc_type_DEGER_ekseni_iki_DEGIL() -> None:
    """(3)'un yapisal yarisi: `exc_type` degeri `None` + her BaseException alt sinifi."""
    goruldu = _yollar(_Sonda())
    ayrik = {v for v in goruldu.values() if v is not None}
    assert len(ayrik) >= 3, "tek koşumda bile en az 3 ayrik istisna TIPI gorulur"
    # None disinda gorulen her deger BaseException'in bir alt sinifi
    assert all(issubclass(v, BaseException) for v in ayrik)  # type: ignore[arg-type]


# --------------------------------------------------------------------------
# (2) parametrizasyon ESKI KAPSAMI kaybetti mi -- bacak basina olcum
# --------------------------------------------------------------------------


def _bacak(ayna: Any, yamalar: list[tuple[str, str]], secim: str) -> tuple[int, str]:
    ayna.geri_al()
    ayna.yaz(SERVICE, yamalar)
    try:
        argv = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", secim]
        r = subprocess.run(argv, cwd=str(ayna.kok), capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    finally:
        ayna.geri_al()


NONE_BACAK = NODE + "[exc_type=None]"
ISTISNA_BACAK = NODE + "[exc_type=CaptureError]"


def test_d10_taban_iki_bacak_da_tek_basina_geciyor(ayna: Any) -> None:
    for secim in (NONE_BACAK, ISTISNA_BACAK):
        rc, c = _bacak(ayna, [], secim)
        assert rc == 0 and "1 passed" in c, f"{secim}: {c[-300:]}"


@pytest.mark.parametrize("mid, yamalar", [("M12", M12), ("M50", M50), ("M53T", M53T)])
def test_d10_None_bacagi_TEK_BASINA_tur2_mutantlarini_yakaliyor(
    ayna: Any, mid: str, yamalar: list[tuple[str, str]]
) -> None:
    """Tur 2'nin TEKIL testinin gucu `exc_type=None` bacaginda BIREBIR duruyor."""
    rc, c = _bacak(ayna, yamalar, NONE_BACAK)
    assert rc != 0 and "1 failed" in c, f"{mid}: None bacagi ZAYIFLADI -- {c[-300:]}"


@pytest.mark.parametrize("mid, yamalar", [("M53", M53), ("M63", M63)])
def test_d10_istisna_bacagi_TEK_BASINA_yeni_siniflari_yakaliyor(
    ayna: Any, mid: str, yamalar: list[tuple[str, str]]
) -> None:
    rc, c = _bacak(ayna, yamalar, ISTISNA_BACAK)
    assert rc != 0 and "1 failed" in c, f"{mid}: istisna bacagi yakalamiyor -- {c[-300:]}"


def test_d10_bacaklar_TAMAMLAYICI_ikisi_de_yuk_tasiyor(ayna: Any) -> None:
    """M53 yalniz istisna bacaginda, M53T yalniz None bacaginda duser --
    yani hicbir bacak digerinin golgesinde degil."""
    rc_a, _ = _bacak(ayna, M53, NONE_BACAK)
    rc_b, _ = _bacak(ayna, M53T, ISTISNA_BACAK)
    assert rc_a == 0, "M53 None bacaginda dusmemeli (o bacak temiz cikisi olcer)"
    assert rc_b == 0, "M53T istisna bacaginda dusmemeli (o bacak istisna yolunu olcer)"


def test_d10_govde_ici_assert_pytest_raises_tarafindan_YUTULMUYOR(ayna: Any) -> None:
    """Istisna bacagindaki `assert t.kapatma == 0` govde icinde; `pytest.raises
    (CaptureError)` bir `AssertionError`'i yutsaydi assert olu olurdu."""
    for secim in (NONE_BACAK, ISTISNA_BACAK):
        rc, c = _bacak(ayna, S1_ENTER_ONCEDEN_KAPATIR, secim)
        assert rc != 0 and "1 failed" in c, f"{secim}: govde ici assert SESSIZ -- {c[-300:]}"


def test_d10_kontrol_mutanti_KACIYOR_yanlis_pozitif_yok(ayna: Any) -> None:
    """`__exit__` `close()` govdesini satir ici yapar (davranis ayni): olcu
    MEKANIZMAYI degil DEGISMEZI kancaliyor (§4.6/7)."""
    rc, c = _bacak(ayna, M66_KONTROL, NODE)
    assert rc == 0 and "2 passed" in c, f"kontrol mutanti KAPIYA TAKILDI: {c[-300:]}"


# --------------------------------------------------------------------------
# (3) "iki parametre ekseni TAMAMEN kapatir" -- YANLIS, ama bloke DEGIL
# --------------------------------------------------------------------------

_YUKUMLULUK = (
    "ADLANDIRILMIS TESTER YUKUMLULUGU (tur 3, bloke DEGIL): `exc_type` ekseni "
    "yalniz CIKIS YOLU bakimindan 2 siniftir; DEGER bakimindan `None` + her "
    "BaseException alt sinifidir. `exc_type`'in DEGERINE gore ayrisan bir "
    "`__exit__` iki parametreyi de gecer: M61 (yalniz None/CaptureError'da "
    "kapatir), M62 (BaseException'da kapatmaz), M64 (CaptureError disini "
    "YUTAR). Uygulama DOGRU (kosulsuz close), uretimde `with MssBackend()` "
    "cagri yeri YOK; sinif erisilebilir degil. Kapatilirsa XPASS verir."
)


@pytest.mark.xfail(strict=True, reason=_YUKUMLULUK)
@pytest.mark.parametrize("mid, yamalar", [("M61", M61), ("M62", M62), ("M64", M64)])
def test_d10_YUKUMLULUK_exc_type_DEGERINE_kapili_varyant_kapiya_takilmiyor(
    ayna: Any, mid: str, yamalar: list[tuple[str, str]]
) -> None:
    ayna.geri_al()
    ayna.yaz(SERVICE, yamalar)
    try:
        s = ayna.kapilar()
        kapilar = {k: v for k, v in s.items() if not k.endswith("::cikti")}
    finally:
        ayna.geri_al()
    assert any(rc != 0 for rc in kapilar.values()), (
        f"{mid}: exc_type degerine kapili varyant bes kapidan da geciyor: {kapilar}"
    )
