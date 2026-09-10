"""TESTER-D tur 2 -- `capture_region` docstring'inin TASMA iddialarini BAGIMSIZ olcer.

Docstring uc zarar kipi ve iki sayi iddia ediyor. Bu betik hicbirini
`evidence/t2-2-tasma-olcumu.txt`'den okumaz; olculeni kendi kurar.

PROTOKOL §4.6/10: olumsuz iddia ("derin INSIDE'da ayrisma SIFIR") ancak
POZITIF KONTROLLE anlam tasir -- ayni olcu, sinifin dogabildigi kenar
grid'inde ATESLENDIGI gosterilerek. Ikisi de asagida kosuyor.

Yontem: `CaptureService._hedef_dikdortgen` iki kez cagrilir --
  (A) DUZLESTIRILMIS `Rect` ile  (urunun gercek yolu: `_duzlestir` -> ...)
  (B) HAM numpy `Rect` ile       (duzlestirme OLMASAYDI olacak yol)
ve ciktilar karsilastirilir. `src/` YAZILMAZ.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

DEPO = Path(__file__).resolve().parents[4]
if str(DEPO) not in sys.path:
    sys.path.insert(0, str(DEPO))

import numpy as np  # noqa: E402

from src.capture.service import CaptureService, FakeBackend  # noqa: E402
from src.contracts.errors import CaptureError  # noqa: E402
from src.contracts.models import Rect  # noqa: E402

GERCEK_DUZEN = (Rect(-2560, 0, 2560, 1440), Rect(0, 0, 2560, 1440))
L_DUZEN = (Rect(0, 0, 100, 100), Rect(100, 100, 100, 100))
TIPLER = (np.uint8, np.uint16, np.uint32, np.uint64)


def _servis(monitorler: tuple[Rect, ...]) -> CaptureService:
    return CaptureService(FakeBackend(monitorler))


def _sonuc(servis: CaptureService, r: Rect) -> tuple[str, object]:
    """`_hedef_dikdortgen`in sonucunu siniflandirir."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            h = servis._hedef_dikdortgen(r)
        return ("ok", (int(h.x), int(h.y), int(h.w), int(h.h)))
    except CaptureError as exc:
        return ("CaptureError", str(exc)[:60])
    except Exception as exc:  # K6 taksonomisi DISI -- ciplak istisna
        return (f"CIPLAK:{type(exc).__name__}", str(exc)[:60])


def _ham_rect(tip: type, x: int, y: int, w: int, h: int) -> Rect | None:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            return Rect(tip(x), tip(y), tip(w), tip(h))  # type: ignore[arg-type]
    except (OverflowError, ValueError):
        return None  # deger tipe SIGMIYOR


def grid_kos(baslik: str, monitorler: tuple[Rect, ...], xs, ys, whs) -> None:
    servis = _servis(monitorler)
    print(f"\n### {baslik}")
    print(f"grid: x={list(xs)[:3]}..{list(xs)[-1]} ({len(list(xs))} nokta) | "
          f"y={list(ys)[:3]}..{list(ys)[-1]} ({len(list(ys))} nokta) | w,h in {tuple(whs)}")
    print(f"kombinasyon/tip = {len(list(xs)) * len(list(ys)) * len(whs) ** 2}")
    print("| tip | temsil edilemez | ayni | ok->HATA (gurultulu red) | "
          "HATA->ok (gecersiz bolge kabul) | SESSIZ (farkli geometri) | CIPLAK istisna |")
    print("|---|---|---|---|---|---|---|")
    for tip in TIPLER:
        sayac = dict(sigmaz=0, ayni=0, ok_hata=0, hata_ok=0, sessiz=0, ciplak=0)
        for x in xs:
            for y in ys:
                for w in whs:
                    for h in whs:
                        ham = _ham_rect(tip, x, y, w, h)
                        if ham is None:
                            sayac["sigmaz"] += 1
                            continue
                        duz = Rect(x, y, w, h)
                        a = _sonuc(servis, duz)
                        b = _sonuc(servis, ham)
                        if a == b:
                            sayac["ayni"] += 1
                        elif b[0].startswith("CIPLAK"):
                            sayac["ciplak"] += 1
                        elif a[0] == "ok" and b[0] == "CaptureError":
                            sayac["ok_hata"] += 1
                        elif a[0] == "CaptureError" and b[0] == "ok":
                            sayac["hata_ok"] += 1
                        elif a[0] == "ok" and b[0] == "ok":
                            sayac["sessiz"] += 1
                        else:
                            sayac["ayni"] += 1
        print(f"| {tip.__name__} | {sayac['sigmaz']} | {sayac['ayni']} | {sayac['ok_hata']} | "
              f"{sayac['hata_ok']} | **{sayac['sessiz']}** | {sayac['ciplak']} |")


def kanonik_ornekler() -> None:
    print("\n### Docstring'in KANONIK ornekleri (birebir)")
    servis = _servis(GERCEK_DUZEN)

    # (1) sessiz yanlis
    ham = Rect(np.uint32(2500), np.uint32(100), np.uint32(200), np.uint32(100))  # type: ignore[arg-type]
    with warnings.catch_warnings(record=True) as uyarilar:
        warnings.simplefilter("always")
        a = _sonuc(servis, Rect(2500, 100, 200, 100))
        b = _sonuc(servis, ham)
    print(f"Rect(uint32(2500),uint32(100),uint32(200),uint32(100))")
    print(f"  DUZLESTIRILMIS (urunun yolu): {a}")
    print(f"  HAM numpy (duzlestirme olmasa): {b}")
    print(f"  uyarilar: {[str(u.message)[:60] for u in uyarilar]}")
    kare = servis.capture_region(ham)
    print(f"  URUNUN GERCEK CIKTISI: Frame.rect = "
          f"({kare.rect.x}, {kare.rect.y}, {kare.rect.w}, {kare.rect.h}) "
          f"tipler={[type(getattr(kare.rect, ad)).__name__ for ad in ('x', 'y', 'w', 'h')]}")

    # (2) gurultulu red
    ham2 = Rect(np.uint16(100), np.uint16(100), np.uint16(100), np.uint16(100))  # type: ignore[arg-type]
    print("\nRect(uint16(100),uint16(100),uint16(100),uint16(100))")
    print(f"  DUZLESTIRILMIS: {_sonuc(servis, Rect(100, 100, 100, 100))}")
    print(f"  HAM numpy:      {_sonuc(servis, ham2)}")

    # (3) dort tipte de RuntimeWarning
    print("\nRuntimeWarning: overflow -- dort isaretsiz tipte de var mi?")
    for tip in TIPLER:
        ham3 = _ham_rect(tip, 100, 100, 100, 100)
        if ham3 is None:
            print(f"  {tip.__name__}: deger tipe sigmiyor")
            continue
        with warnings.catch_warnings(record=True) as uyarilar:
            warnings.simplefilter("always")
            try:
                servis._hedef_dikdortgen(ham3)
            except Exception as exc:
                sonuc = f"{type(exc).__name__}"
            else:
                sonuc = "ok"
        mesajlar = [str(u.message) for u in uyarilar if issubclass(u.category, RuntimeWarning)]
        print(f"  {tip.__name__}: sonuc={sonuc} | RuntimeWarning x{len(mesajlar)} "
              f"| ornek: {mesajlar[0][:55] if mesajlar else '-'}")

    # (4) K6 DISI ciplak OverflowError -- kucuk (L) duzen, uint8
    print("\nK6 taksonomisi DISI ciplak istisna avi (L duzeni A=(0,0,100,100) B=(100,100,100,100), uint8):")
    servis_l = _servis(L_DUZEN)
    bulunan: list[str] = []
    for x in range(0, 200, 10):
        for y in range(0, 200, 10):
            for w in (1, 20, 60, 200):
                for h in (1, 20, 60, 200):
                    ham4 = _ham_rect(np.uint8, x, y, w, h)
                    if ham4 is None:
                        continue
                    s = _sonuc(servis_l, ham4)
                    if s[0].startswith("CIPLAK"):
                        bulunan.append(f"Rect(uint8({x}),uint8({y}),uint8({w}),uint8({h})) -> {s}")
    print(f"  ciplak istisna sayisi: {len(bulunan)}")
    for satir in bulunan[:5]:
        print(f"    {satir}")


if __name__ == "__main__":
    print("TESTER-D tur 2 -- docstring tasma iddialarinin BAGIMSIZ olcumu")
    print(f"monitorler (gercek duzen): {GERCEK_DUZEN}")
    kanonik_ornekler()
    # POZITIF KONTROL (PROTOKOL §4.6/10): sinifin DOGABILDIGI kenar grid'i.
    grid_kos("KENAR GRID -- docstring'in sayilarinin grid'i (x 0..2600, y 0..1400, w/h in {1,50,200,500})",
             GERCEK_DUZEN, range(0, 2601, 100), range(0, 1401, 100), (1, 50, 200, 500))
    # OLUMSUZ IDDIA: derin INSIDE'da ayrisma sifir (ayni olcu, baska grid).
    grid_kos("DERIN INSIDE GRID -- monitorun ic bolgesi (x 100..1100, y 100..800, w/h in {1,50,200,500})",
             GERCEK_DUZEN, range(100, 1101, 100), range(100, 801, 100), (1, 50, 200, 500))
    grid_kos("DERIN INSIDE, uint8'e SIGAN grid (x 0..200, y 0..200, w/h in {1,20,50})",
             GERCEK_DUZEN, range(0, 201, 50), range(0, 201, 50), (1, 20, 50))
