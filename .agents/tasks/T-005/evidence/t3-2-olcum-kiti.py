"""T3-2 olcum kiti -- docstring'in "derin INSIDE'da ayrisma sifirdir"
iddiasinin sinanmasi.

Olcum noktasi: `CaptureService._hedef_dikdortgen(rect)` -- yani
DUZLESTIRMEDEN SONRAKI yol. Ham (duzlestirilmemis) numpy `Rect` dogrudan
bu metoda verilirse, duzlestirme YOKMUS gibi davranilmis olur; ayni
degerlerin duz `int` hali referanstir. Ikisi ayrisiyorsa duzlestirme o
noktada bir zarari onluyor demektir.

Referans, denetlenen uygulamanin urettigi veriden TUREMEZ (PROTOKOL
§4.6/8): referans, ayni geometrinin duz Python `int` ile hesaplanmis
halidir -- bagimsiz kanal.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np

# Depo kokunu sys.path'e ekler -- kit her calisma dizininden kosulabilsin diye:
#   python .agents/tasks/T-005/evidence/t3-2-olcum-kiti.py
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from src.capture.service import CaptureService, FakeBackend  # noqa: E402
from src.contracts.errors import CaptureError  # noqa: E402
from src.contracts.models import Rect  # noqa: E402

M0 = Rect(-2560, 0, 2560, 1440, monitor_index=0, dpi_scale=1.0)
M1 = Rect(0, 0, 2560, 1440, monitor_index=1, dpi_scale=1.0)
IKI_MONITOR = (M0, M1)
TEK_MONITOR = (Rect(0, 0, 2560, 1440, monitor_index=0, dpi_scale=1.0),)

TIPLER = {
    "uint8": np.uint8,
    "uint16": np.uint16,
    "uint32": np.uint32,
    "uint64": np.uint64,
}


def servis(monitorler: tuple[Rect, ...]) -> CaptureService:
    return CaptureService(FakeBackend(monitorler))


def ham_sonuc(s: CaptureService, x, y, w, h):
    """`_hedef_dikdortgen`i DUZLESTIRMEDEN cagirir -> (durum, deger)."""
    try:
        with warnings.catch_warnings(record=True) as yakalanan:
            warnings.simplefilter("always")
            r = s._hedef_dikdortgen(Rect(x, y, w, h))
        uyari = len([u for u in yakalanan if issubclass(u.category, RuntimeWarning)])
        return ("ok", (int(r.x), int(r.y), int(r.w), int(r.h)), uyari)
    except CaptureError as e:
        return ("CaptureError", str(e), 0)
    except Exception as e:  # noqa: BLE001 -- taksonomi disi kipleri de gormek icin
        return (type(e).__name__, str(e), 0)


def baslik(metin: str) -> None:
    print()
    print("=" * 74)
    print(metin)
    print("=" * 74)


# ---------------------------------------------------------------------------
baslik("A -- KANONIK KARSI ORNEK: Rect(1000, 600, 1000, 200), IKI MONITOR")
# ---------------------------------------------------------------------------
print(f"monitorler: M0={M0.x},{M0.y},{M0.w},{M0.h}  M1={M1.x},{M1.y},{M1.w},{M1.h}")
print("bolge M1'in TAMAMEN icinde. kenar uzakliklari:")
print("  sol(M0/M1 dikisine) 1000 | ust 600 | sag 2560-2000=560 | alt 1440-800=640")
s2 = servis(IKI_MONITOR)
for ad in ["int", *TIPLER]:
    donusum = int if ad == "int" else TIPLER[ad]
    try:
        vals = [donusum(1000), donusum(600), donusum(1000), donusum(200)]
    except OverflowError as e:
        print(f"  {ad:<7}: TEMSIL EDILEMEZ -> {type(e).__name__}: {e}")
        continue
    print(f"  {ad:<7}: {ham_sonuc(s2, *vals)}")

print()
print("URUNUN KENDI YOLU (duzlestirme DEVREDE) -- ayni girdiler:")
for ad in ["int", *TIPLER]:
    donusum = int if ad == "int" else TIPLER[ad]
    try:
        vals = [donusum(1000), donusum(600), donusum(1000), donusum(200)]
    except OverflowError:
        print(f"  {ad:<7}: TEMSIL EDILEMEZ")
        continue
    try:
        f = s2.capture_region(Rect(*vals))
        print(f"  {ad:<7}: ok {(f.rect.x, f.rect.y, f.rect.w, f.rect.h)} "
              f"tipler={[type(v).__name__ for v in (f.rect.x, f.rect.y, f.rect.w, f.rect.h)]}")
    except Exception as e:  # noqa: BLE001
        print(f"  {ad:<7}: {type(e).__name__}: {e}")

# ---------------------------------------------------------------------------
baslik("B -- KOMSU TABLOSU: ayrisma kenar uzakligiyla DEGIL x==w ile geliyor mu")
# ---------------------------------------------------------------------------
print(f"{'x':>6} {'w':>6} {'x==w':>5} | {'int':>26} | {'uint32':>26}")
print("-" * 74)
for x, w in [(1000, 1000), (1000, 1001), (999, 1000), (500, 500), (300, 300),
             (1200, 1200), (100, 100), (2000, 500), (500, 2000)]:
    duz = ham_sonuc(s2, x, 600, w, 200)
    u32 = ham_sonuc(s2, np.uint32(x), np.uint32(600), np.uint32(w), np.uint32(200))
    duz_s = f"{duz[0]}{duz[1] if duz[0] == 'ok' else ''}"[:26]
    u32_s = f"{u32[0]}{u32[1] if u32[0] == 'ok' else ''}"[:26]
    ayr = "AYRISMA" if duz[:2] != u32[:2] else ""
    print(f"{x:>6} {w:>6} {str(x == w):>5} | {duz_s:>26} | {u32_s:>26}  {ayr}")

# ---------------------------------------------------------------------------
baslik("C -- DERIN INSIDE GRID: x==w ailesini URETEBILEN grid (POZITIF KONTROL)")
# ---------------------------------------------------------------------------
XS = [100, 200, 300, 500, 700, 999, 1000, 1001, 1200]
YS = [100, 600]
WS = [100, 200, 300, 500, 700, 999, 1000, 1001, 1200]
HS = [1, 50, 200]

for monitor_ad, monitorler in (("IKI MONITOR (M0 negatif x)", IKI_MONITOR),
                               ("TEK MONITOR (yalniz M1 geometrisi)", TEK_MONITOR)):
    s = servis(monitorler)
    print()
    print(f"-- {monitor_ad}")
    print(f"{'tip':<8} {'temsil edilebilir':>18} {'AYRISMA':>9} {'x==w olan ayrisma':>19} {'x!=w olan ayrisma':>19}")
    for ad, tip in TIPLER.items():
        toplam = 0
        ayrisan = 0
        ayrisan_xw = 0
        ayrisan_xnew = 0
        ornekler: list[str] = []
        for x in XS:
            for y in YS:
                for w in WS:
                    for h in HS:
                        # derin INSIDE dogrulamasi: bolge M1'in tamamen icinde mi
                        if not (0 < x and 0 < y and x + w <= 2560 and y + h <= 1440):
                            continue
                        try:
                            hv = [tip(x), tip(y), tip(w), tip(h)]
                        except OverflowError:
                            continue
                        toplam += 1
                        duz = ham_sonuc(s, x, y, w, h)
                        ham = ham_sonuc(s, *hv)
                        if duz[:2] != ham[:2]:
                            ayrisan += 1
                            if x == w:
                                ayrisan_xw += 1
                            else:
                                ayrisan_xnew += 1
                                if len(ornekler) < 6:
                                    ornekler.append(
                                        f"x={x},y={y},w={w},h={h} duz={duz[0]} ham={ham[0]}"
                                    )
        print(f"{ad:<8} {toplam:>18} {ayrisan:>9} {ayrisan_xw:>19} {ayrisan_xnew:>19}")
        for o in ornekler:
            print(f"           x!=w ayrisma ornegi: {o}")

# ---------------------------------------------------------------------------
baslik("D -- POZITIF KONTROL: olcunun ATESLEDIGI acikca gosterilir")
# ---------------------------------------------------------------------------
print("Bir 'ayrisma yok' sayimi ancak olcunun ateslenebildigi gosterilirse")
print("anlam tasir (PROTOKOL §4.6/10). Ayni olcu, ayni kod yolu:")
kontrol = [
    ("derin INSIDE x==w", np.uint32, 1000, 600, 1000, 200),
    ("kenardan tasan (PARTIAL)", np.uint32, 2500, 100, 200, 100),
    ("derin INSIDE x!=w", np.uint32, 999, 600, 1000, 200),
]
for etiket, tip, x, y, w, h in kontrol:
    duz = ham_sonuc(s2, x, y, w, h)
    ham = ham_sonuc(s2, tip(x), tip(y), tip(w), tip(h))
    print(f"  {etiket:<26} duz={str(duz[:2]):<44} ham={str(ham[:2])[:44]:<44} "
          f"-> {'ATESLEDI' if duz[:2] != ham[:2] else 'ateslemedi'}")

# ---------------------------------------------------------------------------
baslik("C2 -- AYRISAN AILE x==w ILE SINIRLI MI? (hedefli sonda)")
# ---------------------------------------------------------------------------
print("C'deki grid'de ayrisanlarin TAMAMI x==w cikti. Bu, ailenin x==w'den")
print("IBARET oldugunu gostermez -- yalnizca o grid'in baska uye URETMEDIGINI.")
print("Iki-monitor duzeninde, x != w olan uyeler icin hedefli tarama:")
print(f"{'tip':<8} {'x':>6} {'y':>6} {'w':>6} {'h':>6} | {'duz int':>26} | {'ham':>26}")
print("-" * 92)
bulunan = 0
for ad, tip in TIPLER.items():
    for h in [1, 2, 4, 16, 64, 128, 256, 512]:
        for x in [100, 300, 500, 700]:
            for w in [x + h, x + 2 * h, x + 256, x + 512, x + 1024]:
                if x == w or not (x + w <= 2560 and 600 + h <= 1440):
                    continue
                try:
                    hv = [tip(x), tip(600), tip(w), tip(h)]
                except OverflowError:
                    continue
                duz = ham_sonuc(s2, x, 600, w, h)
                ham = ham_sonuc(s2, *hv)
                if duz[:2] != ham[:2]:
                    bulunan += 1
                    if bulunan <= 8:
                        duz_s = f"{duz[0]}{duz[1] if duz[0] == 'ok' else ''}"[:26]
                        ham_s = f"{ham[0]}{ham[1] if ham[0] == 'ok' else ''}"[:26]
                        print(f"{ad:<8} {x:>6} {600:>6} {w:>6} {h:>6} | {duz_s:>26} | {ham_s:>26}")
print(f"-> x != w olan ayrisan uye sayisi (bu hedefli taramada): {bulunan}")

# ---------------------------------------------------------------------------
baslik("E -- L DUZENINDE uint8: K6 TAKSONOMISI DISI CIPLAK OverflowError")
# ---------------------------------------------------------------------------
print("kucuk L duzeni A=(0,0,100,100) B=(100,100,100,100), uint8")
sl = servis((Rect(0, 0, 100, 100, monitor_index=0, dpi_scale=1.0),
             Rect(100, 100, 100, 100, monitor_index=1, dpi_scale=1.0)))
for x, y, w, h in [(0, 0, 201, 201), (0, 0, 255, 255), (50, 50, 200, 200),
                   (90, 50, 20, 20)]:
    duz = ham_sonuc(sl, x, y, w, h)
    ham = ham_sonuc(sl, np.uint8(x), np.uint8(y), np.uint8(w), np.uint8(h))
    print(f"  uint8 x={x} y={y} w={w} h={h}: duz={str(duz[:2])[:44]:<44} ham={str(ham[:2])[:56]}")

print()
print("BITTI")
