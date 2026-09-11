"""D9 (tur 2) -- `capture_region` docstring'inin TASMA iddialari.

Tur 2'de degisen tek `src/` kalemi bu docstring metnidir. Metin uc zarar kipi,
iki sayi ve BIR OLUMSUZ IDDIA tasiyor. PROTOKOL §4.6/10 (bu turda eklendi):
"'Sifir ihlal' bir olcum degildir -- olcunun ATESLEYEBILDIGI gosterilmeden
yazilamaz. Olumsuz bir iddia POZITIF KONTROLLE anlam tasir."

Bu dosya her iddiayi bagimsiz olcer. Referans hicbir yerde teslimin kendi
kanit dosyasindan turetilmez (§4.6/8): `dpi.classify_region` ve
`CaptureService._hedef_dikdortgen` DUZLESTIRILMIS ve HAM girdiyle iki kez
kosulur, karsilastirilan sey bu iki bagimsiz koşumdur.
"""
from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pytest

from src.capture import dpi
from src.capture.service import CaptureService, FakeBackend
from src.contracts.errors import CaptureError
from src.contracts.models import Rect

DEPO = Path(__file__).resolve().parents[4]
M0 = Rect(-2560, 0, 2560, 1440)
M1 = Rect(0, 0, 2560, 1440)
DUZEN = (M0, M1)
ISARETSIZ = (np.uint8, np.uint16, np.uint32, np.uint64)


def _servis() -> CaptureService:
    return CaptureService(FakeBackend(DUZEN), lambda: 0.0)


def _sonuc(servis: CaptureService, r: Rect) -> tuple[str, object]:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        try:
            h = servis._hedef_dikdortgen(r)
        except CaptureError:
            return ("CaptureError", None)
        except Exception as exc:
            return (f"CIPLAK:{type(exc).__name__}", None)
    return ("ok", (int(h.x), int(h.y), int(h.w), int(h.h)))


def _docstring() -> str:
    from src.capture.service import CaptureService as CS
    return CS.capture_region.__doc__ or ""


# --------------------------------------------------------------------------
# 1) "tasma DORT tipin dordunde de var, her birinde RuntimeWarning"
# --------------------------------------------------------------------------


@pytest.mark.parametrize("tip", ISARETSIZ, ids=[t.__name__ for t in ISARETSIZ])
def test_d9_dort_isaretsiz_tipte_de_tasma_ve_RuntimeWarning(tip: type) -> None:
    ham = Rect(tip(100), tip(100), tip(100), tip(100))  # type: ignore[arg-type]
    with warnings.catch_warnings(record=True) as uy:
        warnings.simplefilter("always")
        sinif = dpi.classify_region(ham, DUZEN)
    uyarilar = [u for u in uy if issubclass(u.category, RuntimeWarning)]
    assert uyarilar, f"{tip.__name__}: docstring 'RuntimeWarning doguyor' diyor, dogmadi"
    assert "overflow" in str(uyarilar[0].message)
    assert dpi.classify_region(Rect(100, 100, 100, 100), DUZEN) is dpi.RegionValidity.INSIDE
    assert sinif is not dpi.RegionValidity.INSIDE, (
        f"{tip.__name__}: docstring 'dort tipin dordu de tasar' diyor ama tasma yok"
    )


# --------------------------------------------------------------------------
# 2) zarar kipi A -- GURULTULU RED (docstring'in kanonik ornegi)
# --------------------------------------------------------------------------


def test_d9_gurultulu_red_kanonik_ornegi_dogru() -> None:
    """`Rect(uint16(100)x4)` INSIDE'dir ama ham yolda `outside` cikar."""
    servis = _servis()
    ham = Rect(np.uint16(100), np.uint16(100), np.uint16(100), np.uint16(100))  # type: ignore[arg-type]
    assert _sonuc(servis, Rect(100, 100, 100, 100)) == ("ok", (100, 100, 100, 100))
    assert _sonuc(servis, ham) == ("CaptureError", None)


# --------------------------------------------------------------------------
# 3) zarar kipi B -- SESSIZ YANLIS (docstring'in kanonik ornegi)
# --------------------------------------------------------------------------


def test_d9_sessiz_yanlis_kanonik_ornegi_dogru() -> None:
    """`Rect(uint32(2500),100,200,100)`: dogru `w=60`, ham yolda `w=200`, istisna YOK."""
    servis = _servis()
    ham = Rect(np.uint32(2500), np.uint32(100), np.uint32(200), np.uint32(100))  # type: ignore[arg-type]
    assert _sonuc(servis, Rect(2500, 100, 200, 100)) == ("ok", (2500, 100, 60, 100))
    assert _sonuc(servis, ham) == ("ok", (2500, 100, 200, 100)), (
        "docstring 'kirpma atlanir, w=200 cikar, istisna yok' diyor"
    )
    kare = servis.capture_region(ham)
    assert (kare.rect.x, kare.rect.y, kare.rect.w, kare.rect.h) == (2500, 100, 60, 100), (
        "URUNUN kendi yolu dogru olmali (duzlestirme girise konuldugu icin)"
    )
    assert all(type(getattr(kare.rect, a)) is int for a in ("x", "y", "w", "h"))


# --------------------------------------------------------------------------
# 4) zarar kipi C -- K6 DISI ciplak OverflowError
# --------------------------------------------------------------------------


def test_d9_ucuncu_kip_ciplak_overflowerror_dogru() -> None:
    """Kucuk (L) duzende `uint8` ile K6 taksonomisi disinda `OverflowError`."""
    servis = CaptureService(FakeBackend((Rect(0, 0, 100, 100), Rect(100, 100, 100, 100))),
                            lambda: 0.0)
    ham = Rect(np.uint8(50), np.uint8(50), np.uint8(200), np.uint8(200))  # type: ignore[arg-type]
    sonuc = _sonuc(servis, ham)
    assert sonuc[0] == "CIPLAK:OverflowError", (
        f"docstring 'ciplak OverflowError firlatiyor' diyor; olculen {sonuc[0]}"
    )
    assert _sonuc(servis, Rect(50, 50, 200, 200))[0] == "ok"


# --------------------------------------------------------------------------
# 5) docstring'in SAYILARI -- 6480 kombinasyonun 1108'i / 240'i
# --------------------------------------------------------------------------


@pytest.mark.parametrize("tip", [np.uint32, np.uint64], ids=["uint32", "uint64"])
def test_d9_kenar_grid_sayilari_dogru(tip: type) -> None:
    servis = _servis()
    sessiz = hata_ok = 0
    n = 0
    for x in range(0, 2601, 100):
        for y in range(0, 1401, 100):
            for w in (1, 50, 200, 500):
                for h in (1, 50, 200, 500):
                    n += 1
                    a = _sonuc(servis, Rect(x, y, w, h))
                    b = _sonuc(servis, Rect(tip(x), tip(y), tip(w), tip(h)))  # type: ignore[arg-type]
                    if a == b:
                        continue
                    if a[0] == "ok" and b[0] == "ok":
                        sessiz += 1
                    elif a[0] == "CaptureError" and b[0] == "ok":
                        hata_ok += 1
    assert n == 6480, f"docstring 6480 kombinasyon diyor, grid {n} uretti"
    assert sessiz == 1108, f"docstring 1108 sessiz geometri diyor, olculen {sessiz}"
    assert hata_ok == 240, f"docstring 240 gecersiz-bolge-kabulu diyor, olculen {hata_ok}"


# --------------------------------------------------------------------------
# 6) OLUMSUZ IDDIA -- "kenardan uzak (derin INSIDE) bolgelerde ayrisma SIFIR"
#    PROTOKOL §4.6/10: pozitif kontrol ARANIR.
# --------------------------------------------------------------------------


@pytest.mark.parametrize("tip", [np.uint16, np.uint32, np.uint64],
                         ids=["uint16", "uint32", "uint64"])
def test_d9_derin_INSIDE_bolgede_de_AYRISMA_VAR(tip: type) -> None:
    """POZITIF KONTROL: iddianin sinifindan bir girdi ver, olcu atesliyor mu?

    `Rect(1000, 600, 1000, 200)`: M1'in TAMAMEN icinde, en yakin monitor
    kenarina 560 px (sag), 600 px (ust), 640 px (alt), M0/M1 dikisine 1000 px.
    Duzlestirme olmasa GECERLI bu bolge `CaptureError` alirdi.
    """
    servis = _servis()
    duz = Rect(1000, 600, 1000, 200)
    ham = Rect(tip(1000), tip(600), tip(1000), tip(200))  # type: ignore[arg-type]
    assert dpi.classify_region(duz, DUZEN) is dpi.RegionValidity.INSIDE
    assert _sonuc(servis, duz) == ("ok", (1000, 600, 1000, 200))
    assert _sonuc(servis, ham) == ("CaptureError", None), (
        f"{tip.__name__}: bu ornek docstring'in 'kenardan uzak bolgelerde dort "
        f"tipte de ayrisma SIFIRDIR' cumlesini curutur"
    )


def test_d9_derin_INSIDE_ayrisma_kenara_yakinlikla_ilgili_DEGIL() -> None:
    """Ayrisan aile `x == w`; kenara uzaklik ne olursa olsun ayrisiyor."""
    servis = _servis()
    ayrisan: list[int] = []
    for x in (100, 200, 300, 500, 700, 1000, 1200):
        duz = Rect(x, 600, x, 200)
        ham = Rect(np.uint32(x), np.uint32(600), np.uint32(x), np.uint32(200))  # type: ignore[arg-type]
        assert dpi.classify_region(duz, DUZEN) is dpi.RegionValidity.INSIDE
        if _sonuc(servis, duz) != _sonuc(servis, ham):
            ayrisan.append(x)
    assert ayrisan == [100, 200, 300, 500, 700, 1000, 1200], (
        f"'x == w' ailesinin tamami ayrismali; ayrisanlar {ayrisan}"
    )
    # KONTROL: x != w olan komsulari ayrismiyor -> olcu ayirt edici.
    for x, w in ((400, 200), (600, 300), (1000, 200)):
        duz2 = Rect(x, 600, w, 200)
        ham2 = Rect(np.uint32(x), np.uint32(600), np.uint32(w), np.uint32(200))  # type: ignore[arg-type]
        assert _sonuc(servis, duz2) == _sonuc(servis, ham2)


def test_d9_ayrismanin_kaynagi_NEGATIF_x_li_M0() -> None:
    """Tek monitorlu (M1) duzende ayni ham rect ayrismiyor -- sebep M0'in -2560'i."""
    tek = CaptureService(FakeBackend((M1,)), lambda: 0.0)
    ham = Rect(np.uint32(1000), np.uint32(600), np.uint32(1000), np.uint32(200))  # type: ignore[arg-type]
    assert _sonuc(tek, ham) == ("ok", (1000, 600, 1000, 200))
    assert _sonuc(_servis(), ham) == ("CaptureError", None)


def test_d9_TUR3_docstring_sifir_iddiasi_SILINDI_ve_damga_var() -> None:
    """TUR 3'te KAPANDI (tur 2 bulgusu D-2.2).

    Tur 2'de `xfail(strict)` ile BULGU olarak duruyordu; tur 3'te cumle
    silindi, yerine `[OLCULMUYOR]` damgasi + olculmus uyeler yazildi. XPASS
    oldu, yesil teste cevrildi. Uc sey birden olculur: (1) eski olumsuz
    evrensel cumle YOK, (2) damga VAR, (3) olculmus uyeler -- derin INSIDE
    karsi ornegi, `x != w` uyesi, L duzeni uint8 -- metinde ADLANDIRILMIS.
    """
    metin = _docstring()
    assert "ayrisma **sifirdir**" not in metin and "ayrisma sifirdir" not in metin, (
        "docstring hala olculmemis 'ayrisma sifirdir' iddiasini tasiyor"
    )
    assert "yalnizca monitor sinirlarina yaklasan" not in metin, (
        "docstring hala 'tasma yalnizca sinirlara yaklasan bolgelerde gozlemlenebilir' diyor"
    )
    assert "[OLCULMUYOR]" in metin, "ayrisma kumesi icin [OLCULMUYOR] damgasi yok (PROTOKOL §4.6/2)"
    for uye in ("Rect(1000, 600, 1000, 200)", "Rect(100, 600, 1124, 64)",
                "Rect(0, 0, 201, 201)", "sinirli degildir"):
        assert uye in metin, f"olculmus uye docstring'de adlandirilmamis: {uye}"
