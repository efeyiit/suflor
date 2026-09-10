"""TESTER-D tur 2 -- docstring'in IKI ayri iddiasini nokta atisi olcer.

(1) "sessiz yanlis ... uyari disinda gorunur iz yok" -- kanonik ornekte
    GERCEKTEN RuntimeWarning doguyor mu? (Birinci betikte ic `catch_warnings`
    uyariyi yutuyordu; burada yutulmuyor.)
(2) "Kenardan uzak (derin INSIDE) bolgelerde ise dort tipte de ayrisma
    SIFIRDIR" -- olumsuz iddia. PROTOKOL §4.6/10: ayrisan ornek ARANIR.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

DEPO = Path(__file__).resolve().parents[4]
if str(DEPO) not in sys.path:
    sys.path.insert(0, str(DEPO))

import numpy as np  # noqa: E402

from src.capture import dpi  # noqa: E402
from src.capture.service import CaptureService, FakeBackend  # noqa: E402
from src.contracts.errors import CaptureError  # noqa: E402
from src.contracts.models import Rect  # noqa: E402

GERCEK_DUZEN = (Rect(-2560, 0, 2560, 1440), Rect(0, 0, 2560, 1440))
servis = CaptureService(FakeBackend(GERCEK_DUZEN))


def olc(r: Rect) -> tuple[str, object, int]:
    with warnings.catch_warnings(record=True) as uy:
        warnings.simplefilter("always")
        try:
            h = servis._hedef_dikdortgen(r)
            sonuc: tuple[str, object] = ("ok", (int(h.x), int(h.y), int(h.w), int(h.h)))
        except CaptureError as exc:
            sonuc = ("CaptureError", str(exc)[:55])
        except Exception as exc:
            sonuc = (f"CIPLAK:{type(exc).__name__}", str(exc)[:55])
    return (*sonuc, sum(1 for u in uy if issubclass(u.category, RuntimeWarning)))


print("== (1) KANONIK SESSIZ ORNEK: uyari SAYISI (yutulmadan) ==")
ham = Rect(np.uint32(2500), np.uint32(100), np.uint32(200), np.uint32(100))  # type: ignore[arg-type]
print(f"  HAM  uint32(2500,100,200,100) -> {olc(ham)}")
print(f"  DUZ  int(2500,100,200,100)    -> {olc(Rect(2500, 100, 200, 100))}")
print("  (son alan = RuntimeWarning sayisi)")
with warnings.catch_warnings(record=True) as uy:
    warnings.simplefilter("always")
    sinif = dpi.classify_region(ham, GERCEK_DUZEN)
print(f"  dpi.classify_region(HAM) = {sinif}  | RuntimeWarning x"
      f"{sum(1 for u in uy if issubclass(u.category, RuntimeWarning))}")
with warnings.catch_warnings(record=True) as uy:
    warnings.simplefilter("always")
    sinif2 = dpi.classify_region(Rect(2500, 100, 200, 100), GERCEK_DUZEN)
print(f"  dpi.classify_region(DUZ) = {sinif2}  | RuntimeWarning x"
      f"{sum(1 for u in uy if issubclass(u.category, RuntimeWarning))}")

print("\n== (2) DERIN INSIDE'DA AYRISMA: olumsuz iddianin sinanmasi ==")
print("iddia: 'Kenardan uzak (derin INSIDE) bolgelerde dort tipte de ayrisma SIFIRDIR'")
for tip in (np.uint8, np.uint16, np.uint32, np.uint64):
    ayrisan: list[str] = []
    toplam = 0
    for x in range(100, 1101, 100):
        for y in range(100, 801, 100):
            for w in (1, 50, 200, 500):
                for h in (1, 50, 200, 500):
                    try:
                        r = Rect(tip(x), tip(y), tip(w), tip(h))  # type: ignore[arg-type]
                    except (OverflowError, ValueError):
                        continue
                    toplam += 1
                    a, av, _ = olc(Rect(x, y, w, h))
                    b, bv, _ = olc(r)
                    if (a, av) != (b, bv):
                        ayrisan.append(f"Rect({tip.__name__}({x}),{y},{w},{h}): "
                                       f"DUZ={a}{av} HAM={b}{bv}")
    print(f"\n  {tip.__name__}: {len(ayrisan)} ayrisma / {toplam} temsil edilebilir kombinasyon")
    for s in ayrisan[:4]:
        print(f"    {s}")
    if len(ayrisan) > 4:
        print(f"    ... (+{len(ayrisan) - 4})")

print("\n== (3) DERIN INSIDE ayrisanlarin ORTAK yapisi ==")
print("hipotez: sol monitorle (x=-2560) yapilan isaretsiz cikarma tasiyor;")
print("bolge INSIDE olsa bile classify_region 'outside' verir (gurultulu red).")
r_duz = Rect(500, 300, 200, 200)
r_ham = Rect(np.uint32(500), np.uint32(300), np.uint32(200), np.uint32(200))  # type: ignore[arg-type]
print(f"  DUZ  Rect(500,300,200,200)          -> {olc(r_duz)}")
print(f"  HAM  Rect(uint32(500),300,200,200)  -> {olc(r_ham)}")
print(f"  TEK MONITOR (yalniz M1) ile ayni ham rect:")
servis2 = CaptureService(FakeBackend((Rect(0, 0, 2560, 1440),)))
with warnings.catch_warnings(record=True) as uy:
    warnings.simplefilter("always")
    try:
        h2 = servis2._hedef_dikdortgen(r_ham)
        s2: object = ("ok", (int(h2.x), int(h2.y), int(h2.w), int(h2.h)))
    except Exception as exc:
        s2 = (type(exc).__name__, str(exc)[:55])
print(f"    {s2} | RuntimeWarning x{sum(1 for u in uy if issubclass(u.category, RuntimeWarning))}")
