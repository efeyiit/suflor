"""T-012 K2 -- `src.ui.geometri`: saf, ekran-bagimsiz sekme geometrisi.

Ekran yaratilmaz; `QRect/QSize/QPoint` ile calisir. Paket K2 OLCU tablosu:
3 ekran dikdortgeni x 2 kenar x 5 `y` -> kapali/acik dikdortgen her zaman
ekran icinde; kapali sag/sol kenara bitisik; acik panel kenara bitisik ve
sekme dikdortgenini kapsar; `y_sinirla` monoton; U2 birebir; `sekme_icinde`
disk testi (kose disarida) ve acik panel dikdortgeni.
"""
from __future__ import annotations

import itertools

import pytest
from PySide6.QtCore import QPoint, QRect, QSize

from src.ui.geometri import (
    PANEL_BOYUTU,
    Kenar,
    sekme_acik_dikdortgeni,
    sekme_icinde,
    sekme_kapali_dikdortgeni,
    y_sinirla,
)

YARICAP = 26
EKRANLAR: dict[str, QRect] = {
    "birincil_2560x1392": QRect(0, 0, 2560, 1392),
    "sol_-2560_2560x1440": QRect(-2560, 0, 2560, 1440),
    "sol_-2560_2048x1152_dpr1.25": QRect(-2560, 0, 2048, 1152),
}
Y_DEGERLERI = (-1000, 0, 400, 1339, 9999)
KENARLAR = (Kenar.SAG, Kenar.SOL)
IZGARA = list(itertools.product(EKRANLAR.items(), KENARLAR, Y_DEGERLERI))
IZGARA_KIMLIK = [f"{ad}-{k.value}-y{y}" for (ad, _), k, y in IZGARA]


# -- sabitler ve enum -----------------------------------------------------------------------------


def test_k2_kenar_strenum_degerleri() -> None:
    assert str(Kenar.SAG) == "sag" and str(Kenar.SOL) == "sol" and Kenar.SAG.value == "sag"
    assert Kenar("sag") is Kenar.SAG and Kenar("sol") is Kenar.SOL
    assert len(Kenar) == 2


def test_k2_panel_boyutu_urun_degeri() -> None:
    assert PANEL_BOYUTU == QSize(200, 132)


# -- y_sinirla ---------------------------------------------------------------------------------


@pytest.mark.parametrize(("ad", "ekran"), list(EKRANLAR.items()), ids=list(EKRANLAR))
def test_k2_y_sinirla_araligi(ad: str, ekran: QRect) -> None:
    alt = ekran.bottom() - 2 * YARICAP + 1
    assert y_sinirla(ekran, -10_000, YARICAP) == ekran.top()
    assert y_sinirla(ekran, ekran.top(), YARICAP) == ekran.top()
    assert y_sinirla(ekran, alt, YARICAP) == alt
    assert y_sinirla(ekran, alt + 1, YARICAP) == alt
    assert y_sinirla(ekran, 10_000, YARICAP) == alt
    orta = ekran.top() + 400
    assert y_sinirla(ekran, orta, YARICAP) == orta


def test_k2_y_sinirla_birincil_araligi_paketle_ayni() -> None:
    ekran = EKRANLAR["birincil_2560x1392"]
    assert y_sinirla(ekran, -1, YARICAP) == 0
    assert y_sinirla(ekran, 5000, YARICAP) == 1340


@pytest.mark.parametrize(("ad", "ekran"), list(EKRANLAR.items()), ids=list(EKRANLAR))
def test_k2_y_sinirla_monoton(ad: str, ekran: QRect) -> None:
    degerler = [y_sinirla(ekran, y, YARICAP) for y in range(ekran.top() - 100, ekran.bottom() + 100, 7)]
    assert all(a <= b for a, b in zip(degerler, degerler[1:], strict=False))


def test_k2_y_sinirla_ekran_sekmeden_kisa_ise_ust_kenar() -> None:
    """Yozlasmis ekran (yukseklik < 2*yaricap): sekme ekranin ustune hizalanir, asla ustune tasmaz."""
    ekran = QRect(0, 0, 100, 30)
    assert y_sinirla(ekran, 0, YARICAP) == 0
    assert y_sinirla(ekran, 500, YARICAP) == 0
    assert y_sinirla(ekran, -5, YARICAP) == 0


# -- kapali / acik dikdortgen: izgara -------------------------------------------------------------


@pytest.mark.parametrize(("ekran_kaydi", "kenar", "y"), IZGARA, ids=IZGARA_KIMLIK)
def test_k2_izgara_kapali_ekran_icinde_ve_kenara_bitisik(ekran_kaydi: tuple[str, QRect], kenar: Kenar, y: int) -> None:
    _, ekran = ekran_kaydi
    k = sekme_kapali_dikdortgeni(ekran, y, YARICAP, kenar)
    assert ekran.contains(k), (k, ekran)
    assert k.size() == QSize(YARICAP, 2 * YARICAP)
    if kenar is Kenar.SAG:
        assert k.right() == ekran.right() and k.x() == ekran.right() - YARICAP + 1
    else:
        assert k.left() == ekran.left()
    assert k.y() == y_sinirla(ekran, y, YARICAP)


@pytest.mark.parametrize(("ekran_kaydi", "kenar", "y"), IZGARA, ids=IZGARA_KIMLIK)
def test_k2_izgara_acik_ekran_icinde_bitisik_ve_sekmeyi_kapsar(ekran_kaydi: tuple[str, QRect], kenar: Kenar, y: int) -> None:
    _, ekran = ekran_kaydi
    k = sekme_kapali_dikdortgeni(ekran, y, YARICAP, kenar)
    a = sekme_acik_dikdortgeni(ekran, y, YARICAP, PANEL_BOYUTU, kenar)
    assert ekran.contains(a), (a, ekran)
    assert a.size() == PANEL_BOYUTU
    if kenar is Kenar.SAG:
        assert a.right() == ekran.right()
    else:
        assert a.left() == ekran.left()
    assert a.contains(k), (a, k)  # imlec sekmeden panele gecerken disari dusmez


def test_k2_acik_panel_sekmenin_dikey_merkezine_hizali_sikismadiginda() -> None:
    ekran = EKRANLAR["birincil_2560x1392"]
    k = sekme_kapali_dikdortgeni(ekran, 670, YARICAP, Kenar.SAG)
    a = sekme_acik_dikdortgeni(ekran, 670, YARICAP, PANEL_BOYUTU, Kenar.SAG)
    assert a.center().y() == k.center().y() == 695


def test_k2_acik_panel_ust_ve_alt_sinirda_ekrana_sikistirilir() -> None:
    ekran = EKRANLAR["birincil_2560x1392"]
    ust = sekme_acik_dikdortgeni(ekran, -1000, YARICAP, PANEL_BOYUTU, Kenar.SAG)
    alt = sekme_acik_dikdortgeni(ekran, 9999, YARICAP, PANEL_BOYUTU, Kenar.SAG)
    assert ust.top() == ekran.top()
    assert alt.bottom() == ekran.bottom()


def test_k2_u2_birebir_2534_670_26_52() -> None:
    ekran = EKRANLAR["birincil_2560x1392"]
    y = ekran.top() + ekran.height() // 2 - YARICAP
    assert sekme_kapali_dikdortgeni(ekran, y, YARICAP, Kenar.SAG) == QRect(2534, 670, 26, 52)
    assert sekme_acik_dikdortgeni(ekran, y, YARICAP, PANEL_BOYUTU, Kenar.SAG) == QRect(2360, 630, 200, 132)


def test_k2_negatif_koordinatli_monitor_sag_kenar() -> None:
    ekran = EKRANLAR["sol_-2560_2560x1440"]
    assert sekme_kapali_dikdortgeni(ekran, -1000, YARICAP, Kenar.SAG) == QRect(-26, 0, 26, 52)
    assert sekme_acik_dikdortgeni(ekran, -1000, YARICAP, PANEL_BOYUTU, Kenar.SAG) == QRect(-200, 0, 200, 132)
    assert sekme_kapali_dikdortgeni(ekran, 9999, YARICAP, Kenar.SOL) == QRect(-2560, 1388, 26, 52)


def test_k2_kucuk_ekran_1280x720_kenarlar() -> None:
    ekran = QRect(0, 0, 1280, 720)
    assert sekme_kapali_dikdortgeni(ekran, 9999, YARICAP, Kenar.SAG) == QRect(1254, 668, 26, 52)
    assert sekme_acik_dikdortgeni(ekran, 9999, YARICAP, PANEL_BOYUTU, Kenar.SOL) == QRect(0, 588, 200, 132)


def test_k2_farkli_yaricap_ve_panel_boyutu_parametrik() -> None:
    """Formuller sabitlere kapili degil: yaricap 40, panel 300x100."""
    ekran = QRect(100, 50, 1000, 600)
    k = sekme_kapali_dikdortgeni(ekran, 300, 40, Kenar.SAG)
    assert k == QRect(1099 - 40 + 1, 300, 40, 80)
    a = sekme_acik_dikdortgeni(ekran, 300, 40, QSize(300, 100), Kenar.SAG)
    assert a == QRect(1099 - 300 + 1, 340 - 50, 300, 100)
    assert y_sinirla(ekran, 9999, 40) == 649 - 80 + 1


def test_k2_kenar_dize_olarak_da_kabul() -> None:
    ekran = EKRANLAR["birincil_2560x1392"]
    assert sekme_kapali_dikdortgeni(ekran, 670, YARICAP, Kenar("sol")).left() == 0


def test_k2_girdi_dikdortgenleri_degistirilmez() -> None:
    ekran = QRect(0, 0, 2560, 1392)
    kopya = QRect(ekran)
    sekme_kapali_dikdortgeni(ekran, 670, YARICAP, Kenar.SAG)
    sekme_acik_dikdortgeni(ekran, 670, YARICAP, PANEL_BOYUTU, Kenar.SOL)
    assert ekran == kopya and PANEL_BOYUTU == QSize(200, 132)


# -- sekme_icinde: disk (kapali) / dikdortgen (acik) ---------------------------------------------


@pytest.mark.parametrize("kenar", KENARLAR, ids=[k.value for k in KENARLAR])
def test_k2_sekme_icinde_kapali_merkez_icerde_kose_disarida(kenar: Kenar) -> None:
    ekran = EKRANLAR["birincil_2560x1392"]
    k = sekme_kapali_dikdortgeni(ekran, 670, YARICAP, kenar)
    kenar_x = k.right() if kenar is Kenar.SAG else k.left()
    assert sekme_icinde(k, QPoint(kenar_x, k.center().y()), YARICAP, kenar)
    assert sekme_icinde(k, k.center(), YARICAP, kenar)
    # ekranin IC tarafindaki koseler saydamdir (alfa 0, KRT D1) -> icinde SAYILMAZ
    ic_koseler = (k.topLeft(), k.bottomLeft()) if kenar is Kenar.SAG else (k.topRight(), k.bottomRight())
    for kose in ic_koseler:
        assert not sekme_icinde(k, kose, YARICAP, kenar), kose
    # kenar tarafindaki koseler dairenin kalem cizgisi ustundedir (gorunur) -> icinde
    kenar_koseleri = (k.topRight(), k.bottomRight()) if kenar is Kenar.SAG else (k.topLeft(), k.bottomLeft())
    for kose in kenar_koseleri:
        assert sekme_icinde(k, kose, YARICAP, kenar), kose


def test_k2_sekme_icinde_kapali_disk_kenar_ustunde_merkezli() -> None:
    """Merkez ekran kenarinda: SAG icin (right+1, orta), SOL icin (left, orta). Disk ∩ dikdortgen."""
    ekran = EKRANLAR["birincil_2560x1392"]
    k = sekme_kapali_dikdortgeni(ekran, 670, YARICAP, Kenar.SAG)
    orta = k.top() + YARICAP
    # dikey dogrultuda: kenar sutununda |dy| <= yaricap iceride, otesi disarida
    assert sekme_icinde(k, QPoint(k.right(), orta - YARICAP + 1), YARICAP, Kenar.SAG)
    assert not sekme_icinde(k, QPoint(k.right(), orta - YARICAP - 1), YARICAP, Kenar.SAG)
    # yatay: kenardan yaricap kadar iceride (dx = -yaricap) hala iceride, bir otesi dikdortgen disi
    assert sekme_icinde(k, QPoint(k.left(), orta), YARICAP, Kenar.SAG)
    assert not sekme_icinde(k, QPoint(k.left() - 1, orta), YARICAP, Kenar.SAG)
    # dikdortgen disi ama disk ici (ekranin otesi, ikinci monitor): iceride SAYILMAZ
    assert not sekme_icinde(k, QPoint(k.right() + 5, orta), YARICAP, Kenar.SAG)
    s = sekme_kapali_dikdortgeni(ekran, 670, YARICAP, Kenar.SOL)
    assert sekme_icinde(s, QPoint(s.right(), orta), YARICAP, Kenar.SOL)
    assert not sekme_icinde(s, QPoint(s.right(), s.top()), YARICAP, Kenar.SOL)
    assert not sekme_icinde(s, QPoint(s.left() - 1, orta), YARICAP, Kenar.SOL)


def test_k2_sekme_icinde_kapali_yarim_daire_alani_dikdortgenden_kucuk() -> None:
    """Pozitif kontrol: disk testi dikdortgen testinden gercekten ayrisir (alan orani ~pi/4)."""
    k = QRect(2534, 670, 26, 52)
    icerde = sum(
        sekme_icinde(k, QPoint(x, y), YARICAP, Kenar.SAG)
        for x in range(k.left(), k.right() + 1)
        for y in range(k.top(), k.bottom() + 1)
    )
    toplam = k.width() * k.height()
    assert 0.70 * toplam < icerde < 0.90 * toplam, (icerde, toplam)


@pytest.mark.parametrize("kenar", KENARLAR, ids=[k.value for k in KENARLAR])
def test_k2_sekme_icinde_acik_panel_dikdortgeni(kenar: Kenar) -> None:
    ekran = EKRANLAR["birincil_2560x1392"]
    a = sekme_acik_dikdortgeni(ekran, 670, YARICAP, PANEL_BOYUTU, kenar)
    assert sekme_icinde(a, a.topLeft(), YARICAP, kenar)  # panel acikken kose iceride
    assert sekme_icinde(a, a.bottomRight(), YARICAP, kenar)
    assert sekme_icinde(a, a.center(), YARICAP, kenar)
    assert not sekme_icinde(a, QPoint(a.left() - 1, a.center().y()), YARICAP, kenar)
    assert not sekme_icinde(a, QPoint(a.center().x(), a.bottom() + 1), YARICAP, kenar)
