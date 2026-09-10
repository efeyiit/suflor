"""MERCEK C -- ortak kurulum yardimcilari (durum makinesi olcumleri).

Bu makinenin GERCEK duzeni (sef olctu): sol monitor NEGATIF x'te ve birincil
DEGIL. `Rect`'in varsayilan `monitor_index=0` bu duzende sol monitoru
gosterir.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any

import numpy as np

from src.capture.service import CaptureService, FakeBackend
from src.contracts.models import Rect

M_SOL = Rect(-2560, 0, 2560, 1440)
M_SAG = Rect(0, 0, 2560, 1440)
GERCEK_DUZEN = (M_SOL, M_SAG)

SABIT_SAAT = 1234.5

IYI = Rect(0, 0, 10, 10)
"""INSIDE -- sag monitorun icinde."""
DISARIDA = Rect(-99999, 0, 10, 10)
"""OUTSIDE -- hicbir monitorle kesismiyor (K6 sinif a)."""
TASAN = Rect(-2600, 0, 100, 100)
"""PARTIAL -- birlesimin solundan 40 px tasar; kirpik (-2560, 0, 60, 100)."""


def saat(deger: float = SABIT_SAAT) -> Callable[[], float]:
    return lambda: deger


def ham_liste(rects: Sequence[Rect]) -> list[Mapping[str, object]]:
    """`rects`'ten ham `mss` listesi kurar -- `[0]` BIRLESIM girdisi dahil.

    Bos kume icin de `[0]`'i yazar: `[1:]` bos kalir, yani servis BOS bir
    monitor kumesiyle kurulur (K5).
    """
    if not rects:
        return [{"left": 0, "top": 0, "width": 0, "height": 0}]
    x = min(r.x for r in rects)
    y = min(r.y for r in rects)
    sag = max(r.right for r in rects)
    alt = max(r.bottom for r in rects)
    out: list[Mapping[str, object]] = [
        {"left": x, "top": y, "width": sag - x, "height": alt - y}
    ]
    out.extend({"left": r.x, "top": r.y, "width": r.w, "height": r.h} for r in rects)
    return out


def iyi_dizi(rect: Rect) -> Any:
    """Gecerli `(h, w, 4)` uint8 dizi."""
    return np.zeros((rect.h, rect.w, 4), dtype=np.uint8)


class Yonlendirici:
    """`image_factory` -- `mod` alanina gore K6 sinifi uretir.

    `mod == "b"` istisna firlatir (backend'in kendi hatasi),
    `mod == "c"` `None` dondurur (gecersiz cikti),
    aksi halde gecerli dizi.
    """

    def __init__(self) -> None:
        self.mod = "ok"
        self.cagri = 0

    def __call__(self, rect: Rect) -> Any:
        self.cagri += 1
        if self.mod == "b":
            raise RuntimeError(f"backend coktu #{self.cagri}")
        if self.mod == "c":
            return None
        return iyi_dizi(rect)


def sirali_uretici(*davranislar: str) -> Callable[[Rect], Any]:
    """i. `grab` cagrisinda `davranislar[i]`; sonrasi son eleman.

    `"b"` -> `RuntimeError("istisna-<n>")`, `"c"` -> `None`,
    `"c2"` -> boyutu uymayan dizi, `"ok"` -> gecerli dizi.
    """
    sayac = [0]

    def uretici(rect: Rect) -> Any:
        i = sayac[0]
        sayac[0] += 1
        d = davranislar[i] if i < len(davranislar) else davranislar[-1]
        if d == "b":
            raise RuntimeError(f"istisna-{i + 1}")
        if d == "c":
            return None
        if d == "c2":
            return np.zeros((3, 3, 3), dtype=np.uint8)
        return iyi_dizi(rect)

    return uretici


def kur(
    monitors: tuple[Rect, ...] = GERCEK_DUZEN,
    image_factory: Callable[[Rect], Any] | None = None,
    clock: Callable[[], float] | None = None,
) -> tuple[CaptureService, FakeBackend]:
    fb = (
        FakeBackend(monitors)
        if image_factory is None
        else FakeBackend(monitors, image_factory)
    )
    return CaptureService(fb, clock or saat()), fb
