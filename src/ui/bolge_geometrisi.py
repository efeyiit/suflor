"""Seçilen ekran alanına yapışık çeviri şeridi geometrisi."""
from __future__ import annotations

from src.contracts.models import Rect

__all__ = ["SERIT_EN_AZ", "SERIT_YUKSEKLIK", "serit_dikdortgeni"]

SERIT_EN_AZ = 280
SERIT_YUKSEKLIK = 112


def serit_dikdortgeni(
    bolge: Rect,
    ekran: Rect,
    *,
    yukseklik: int = SERIT_YUKSEKLIK,
    bosluk: int = 8,
) -> Rect:
    """Şeridi önce bölgenin üstüne, sığmazsa altına ve ekran içine yerleştirir."""
    if ekran.w <= 0 or ekran.h <= 0 or yukseklik <= 0 or bosluk < 0:
        raise ValueError("ekran ve şerit boyutları pozitif, boşluk negatif olmamalı")

    genislik = min(ekran.w, max(SERIT_EN_AZ, bolge.w))
    ortalanmis_x = bolge.x + (bolge.w - genislik) // 2
    x = min(max(ortalanmis_x, ekran.x), ekran.right - genislik)

    ust = bolge.y - bosluk - yukseklik
    alt = bolge.bottom + bosluk
    if ust >= ekran.y:
        y = ust
    elif alt + yukseklik <= ekran.bottom:
        y = alt
    else:
        y = min(max(ust, ekran.y), ekran.bottom - yukseklik)

    return Rect(x, y, genislik, min(yukseklik, ekran.h), ekran.monitor_index, ekran.dpi_scale)

