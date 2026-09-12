"""Suflör -- kenar sekmesi geometrisi (saf), T-012 K2.

Ekran ya da pencere YARATMAZ; `QRect/QSize/QPoint` alir, `QRect`/`int`/`bool`
dondurur. `KenarSekmesi` her konumlandirmada bu fonksiyonlari cagirir; birim
testleri (`tests/unit/ui/test_geometri.py`) uc ekran dikdortgeni x iki kenar
x bes `y` izgarasinda hicbir pencere acmadan olcer.

Koordinatlar MANTIKSAL pikseldir (Qt `QScreen.availableGeometry()` birimi);
negatif koordinatli monitor (`QRect(-2560, 0, 2560, 1440)`) desteklenir.
`ekran` = `availableGeometry()` (KARAR, K2 / KRT O7): gorev cubuguyla
cakismaz; cubuk sagda/solda ise sekme FIZIKSEL kenara bitisik DEGILDIR
(`known_gaps`). DPI != 1.0 monitorde fiziksel kenar yuvarlamasi (KRT G4:
1 px) burada `[ÖLÇÜLMÜYOR birim]`; `real_check.py` [8] ikinci monitorde
+-1 px ile raporlar.

Tanimlar (`yaricap` = r, kapali sekme r x 2r, yarim dairenin merkezi ekran
KENARI uzerinde):
  - `y_sinirla(ekran, y, r)` -> `[ekran.top(), ekran.bottom() - 2r + 1]`
    araligina sikistirir (monoton). Ekran 2r'den kisaysa `ekran.top()`
    (sekme asla ekranin ustune tasmaz; alt tasmayi kabul eder).
  - `sekme_kapali_dikdortgeni`: `sag` -> `x = ekran.right() - r + 1`,
    `sol` -> `x = ekran.left()`; `w = r`, `h = 2r`, `y` sinirlanmis.
  - `sekme_acik_dikdortgeni`: panel kenara bitisik (`sag` ->
    `x = ekran.right() - panel.w + 1`, `sol` -> `ekran.left()`), dikeyde
    sekmenin merkezine (`y + r`) hizali, ekran icine sikistirilmis. Panel
    her `y`de kapali sekme dikdortgenini KAPSAR (imlec sekmeden panele
    gecerken "disari" dusmez) -- panel.h >= 2r oldugu surece.
  - `sekme_icinde(dikdortgen, nokta, r, kenar)`: dikdortgen kapali sekme
    boyutundaysa (`r x 2r`) YARIM DAIRE testi: `dikdortgen.contains(nokta)`
    VE piksel merkezinin (`x + 0.5, y + 0.5`) daire merkezine uzakligi <= r
    (merkez surekli koordinatta: `sag` icin `(left + r, top + r)` = widget'in
    sag siniri, `sol` icin `(left, top + r)` = sol siniri -- cizimdeki
    `drawEllipse` merkeziyle ayni; tam sayi aritmetik `(2dx)^2 + (2dy)^2 <=
    (2r)^2`). Ekranin ic tarafindaki saydam koseler (alfa 0) boylece "icinde"
    SAYILMAZ (KRT D1: kosede tik oyuna gider, hover panel acmamali); kenar
    tarafindaki koseler kalem cizgisi ustundedir (gorunur) ve icindedir. Ekranin otesindeki noktalar (ikinci monitor, disk icinde
    ama dikdortgen disinda) da icinde sayilmaz. Baska boyutta (acik panel)
    duz `contains`. Boyuta gore ayrim: panel boyutu `r x 2r` olamaz
    (`PANEL_BOYUTU` 200x132) -- belgeli varsayim.

Sabitler URUN DEGERLERIDIR (paket v2 "on kosul"; `real_check.py` [0] sorar):
`PANEL_BOYUTU = QSize(200, 132)`; `yaricap=26`, `acilma_ms=120`,
`kapanma_ms=450`, `yoklama_ms=60` `KenarSekmesi` varsayilanlaridir.
"""
from __future__ import annotations

from enum import StrEnum
from typing import Final

from PySide6.QtCore import QPoint, QRect, QSize

__all__ = [
    "PANEL_BOYUTU",
    "Kenar",
    "sekme_acik_dikdortgeni",
    "sekme_icinde",
    "sekme_kapali_dikdortgeni",
    "y_sinirla",
]


class Kenar(StrEnum):
    """Sekmenin durdugu ekran kenari."""

    SAG = "sag"
    SOL = "sol"


PANEL_BOYUTU: Final[QSize] = QSize(200, 132)


def y_sinirla(ekran: QRect, y: int, yaricap: int) -> int:
    """`y`yi `[ekran.top(), ekran.bottom() - 2*yaricap + 1]` araligina sikistirir (monoton)."""
    alt = ekran.bottom() - 2 * yaricap + 1
    return max(ekran.top(), min(y, alt))


def sekme_kapali_dikdortgeni(ekran: QRect, y: int, yaricap: int, kenar: Kenar) -> QRect:
    """Kapali sekme: `yaricap x 2*yaricap`, `kenar`a bitisik, `y` sinirlanmis."""
    x = ekran.right() - yaricap + 1 if Kenar(kenar) is Kenar.SAG else ekran.left()
    return QRect(x, y_sinirla(ekran, y, yaricap), yaricap, 2 * yaricap)


def sekme_acik_dikdortgeni(ekran: QRect, y: int, yaricap: int, panel: QSize, kenar: Kenar) -> QRect:
    """Acik panel: `kenar`a bitisik, sekmenin dikey merkezine hizali, ekran icine sikistirilmis."""
    merkez_y = y_sinirla(ekran, y, yaricap) + yaricap
    ust = merkez_y - panel.height() // 2
    ust = max(ekran.top(), min(ust, ekran.bottom() - panel.height() + 1))
    x = ekran.right() - panel.width() + 1 if Kenar(kenar) is Kenar.SAG else ekran.left()
    return QRect(x, ust, panel.width(), panel.height())


def sekme_icinde(dikdortgen: QRect, nokta: QPoint, yaricap: int, kenar: Kenar) -> bool:
    """Kapali halde yarim daire (dikdortgen ∩ disk), acik halde panel dikdortgeni testi."""
    if not dikdortgen.contains(nokta):
        return False
    if dikdortgen.size() != QSize(yaricap, 2 * yaricap):
        return True
    merkez_x = dikdortgen.left() + yaricap if Kenar(kenar) is Kenar.SAG else dikdortgen.left()
    # piksel merkezi (x + 0.5, y + 0.5) ile merkez arasi uzaklik <= r; tam sayi: (2dx)^2 + (2dy)^2 <= (2r)^2
    dx2 = 2 * (nokta.x() - merkez_x) + 1
    dy2 = 2 * (nokta.y() - dikdortgen.top() - yaricap) + 1
    return dx2 * dx2 + dy2 * dy2 <= 4 * yaricap * yaricap
