"""TESTER-D tur 3 -- docstring artik GATELENEBILIR mi?

Sefin T3-2 kararinin degismezi:

    "Docstring OLUMSUZ EVRENSEL IDDIA yazmaz ('hic', 'sifir', 'yalnizca ...
     durumunda'). Olculen uyeler sayilir; kumenin tamami karakterize
     edilmediyse `[OLCULMUYOR]` damgasi tasir (§4.6/2)."

Bu dosya UC sey yapar:

  A. MEKANIK TARAMA -- `src/capture/*.py` docstring'lerindeki her olumsuz
     evrensel belirteci ("hic", "sifir", "asla", "yalniz", "sadece",
     "her zaman", "tamamen", "yoktur", "degildir") satir satir cikarir ve
     iki sinifa ayirir:
       (i)  ACIK GIRDI KUMESI uzerinde evrensel  -> YASAK sinif
       (ii) KAPALI/DENETLENEBILIR kume uzerinde  -> gatelenebilir
     Ayrim keyfi degil: (ii) sinifi sonlu ve makineyle sayilabilir bir
     alan hakkindadir (kendi kodunun akisi, dort hata kosulu, bir modulun
     ozniteligi); (i) sinifi sinirsiz bir girdi uzayinin HIC ugranmamis
     bolgesi hakkindadir -- §4.6/10'un yasakladigi sey budur.

  B. KALAN OLUMLU IDDIALARIN BAGIMSIZ DOGRULANMASI -- tur 3'te yazilan her
     sayi ve her karsi ornek BURADAN yeniden uretilir.

  C. KAPALI-KUME EVRENSELLERININ OLCUMU -- "bunlarin hicbirinde backend
     cagrilmaz" ve "kirpma her zaman birlesime karsi" iddialari kosulur.

`src/` YAZILMAZ.
Kosum:  python -X utf8 .agents/tasks/T-005/tester_D/t3_docstring_denetimi.py
"""
from __future__ import annotations

import ast
import re
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

BELIRTECLER = [
    "hicbir", "hiçbir", "hic ", "hiç ", "sifir", "sıfır", "asla",
    "yalniz", "yalnız", "sadece", "her zaman", "tamamen", "yoktur",
    "hep ", "tumu", "tümü", "dordu de", "dördü de", "kosulsuz", "koşulsuz",
]


# ---------------------------------------------------------------------------
# A. mekanik tarama
# ---------------------------------------------------------------------------

def a_tarama() -> list[tuple[str, int, str]]:
    print("=" * 78)
    print("A. MEKANIK TARAMA -- docstring'lerde olumsuz/evrensel belirtec")
    print("=" * 78)
    bulgular: list[tuple[str, int, str]] = []
    for yol in sorted((DEPO / "src" / "capture").glob("*.py")):
        agac = ast.parse(yol.read_text(encoding="utf-8"))
        for dugum in ast.walk(agac):
            if not isinstance(dugum, (ast.Module, ast.ClassDef,
                                      ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            ds = ast.get_docstring(dugum, clean=False)
            if not ds:
                continue
            ad = getattr(dugum, "name", "<modul>")
            # cumleye bol
            duz = re.sub(r"\s+", " ", ds)
            for cumle in re.split(r"(?<=[.:])\s+", duz):
                dusuk = cumle.lower()
                if any(b in dusuk for b in BELIRTECLER):
                    bulgular.append((f"{yol.name}::{ad}", 0, cumle.strip()))
    print(f"  toplam belirtec tasiyan cumle: {len(bulgular)}")
    print()
    for kaynak, _n, cumle in bulgular:
        print(f"  [{kaynak}]")
        print(f"     {cumle[:300]}")
    print()
    return bulgular


# ---------------------------------------------------------------------------
# B. kalan olumlu iddialarin bagimsiz dogrulanmasi
# ---------------------------------------------------------------------------

def _olc(servis: CaptureService, r: Rect) -> tuple[str, object, int]:
    """HAM yol: `_hedef_dikdortgen` duzlestirmeden ONCEKI hesabi yapar."""
    with warnings.catch_warnings(record=True) as uy:
        warnings.simplefilter("always")
        try:
            h = servis._hedef_dikdortgen(r)
            sonuc: tuple[str, object] = ("ok", (int(h.x), int(h.y), int(h.w), int(h.h)))
        except CaptureError as exc:
            sonuc = ("CaptureError", str(exc)[:50])
        except Exception as exc:  # noqa: BLE001
            sonuc = (f"CIPLAK:{type(exc).__name__}", str(exc)[:50])
    return (*sonuc, sum(1 for u in uy if issubclass(u.category, RuntimeWarning)))


def b_iddialar() -> dict[str, bool]:
    print("=" * 78)
    print("B. TUR 3 DOCSTRING'ININ OLUMLU IDDIALARI -- bagimsiz olcum")
    print("=" * 78)
    s = CaptureService(FakeBackend(GERCEK_DUZEN))
    sonuc: dict[str, bool] = {}

    # --- B1: derin INSIDE karsi ornegi -----------------------------------
    print("B1. `Rect(1000, 600, 1000, 200)` derin INSIDE + ham yolda CaptureError")
    r_duz = Rect(1000, 600, 1000, 200)
    print(f"    duz int          -> {_olc(s, r_duz)}")
    b1 = True
    for tip in (np.uint16, np.uint32, np.uint64):
        c = _olc(s, Rect(tip(1000), tip(600), tip(1000), tip(200)))  # type: ignore[arg-type]
        print(f"    ham {tip.__name__:8s}     -> {c}")
        b1 = b1 and c[0] == "CaptureError"
    # kenar uzakligi
    m1 = Rect(0, 0, 2560, 1440)
    uzak = min(r_duz.x - m1.x, r_duz.y - m1.y,
               (m1.x + m1.w) - (r_duz.x + r_duz.w),
               (m1.y + m1.h) - (r_duz.y + r_duz.h))
    print(f"    M1 kenarina EN KISA uzaklik = {uzak} px  (docstring: '>= 560 px')")
    b1 = b1 and uzak >= 560 and _olc(s, r_duz)[0] == "ok"
    sonuc["B1 derin INSIDE karsi ornegi"] = b1
    print(f"    -> {'TUTUYOR' if b1 else 'TUTMUYOR'}")
    print()

    # --- B2: `x == w` uyeleri + POZITIF KONTROL (komsular) ----------------
    print("B2. `x == w` uyeleri ayrisiyor; `x=1000,w=1001` ve `x=999,w=1000` AYRISMIYOR")
    print("    (docstring bunu 'olcu o noktalarda ATESLENEBILIR durumdadir' diye yaziyor)")
    b2 = True
    for x, w in ((100, 100), (300, 300), (500, 500), (1000, 1000), (1200, 1200)):
        c = _olc(s, Rect(np.uint16(x), np.uint16(600), np.uint16(w), np.uint16(200)))  # type: ignore[arg-type]
        d = _olc(s, Rect(x, 600, w, 200))
        ayr = c[:2] != d[:2]
        print(f"    x={x:5d} w={w:5d}  ham={str(c[0]):14s} duz={str(d[0]):4s}  "
              f"ayrisma={'EVET' if ayr else 'hayir'}")
        b2 = b2 and ayr
    print("    -- POZITIF KONTROL (ayrismamasi beklenen komsular):")
    for x, w in ((1000, 1001), (999, 1000)):
        c = _olc(s, Rect(np.uint16(x), np.uint16(600), np.uint16(w), np.uint16(200)))  # type: ignore[arg-type]
        d = _olc(s, Rect(x, 600, w, 200))
        ayr = c[:2] != d[:2]
        print(f"    x={x:5d} w={w:5d}  ham={str(c[0]):14s} duz={str(d[0]):4s}  "
              f"ayrisma={'EVET' if ayr else 'hayir'}")
        b2 = b2 and not ayr
    sonuc["B2 x==w uyeleri + komsu pozitif kontrolu"] = b2
    print(f"    -> {'TUTUYOR' if b2 else 'TUTMUYOR'}")
    print()

    # --- B3: `x != w` uyesi ----------------------------------------------
    print("B3. `x != w` uyesi: uint16, `Rect(100, 600, 1124, 64)` -- CaptureError")
    c = _olc(s, Rect(np.uint16(100), np.uint16(600), np.uint16(1124), np.uint16(64)))  # type: ignore[arg-type]
    d = _olc(s, Rect(100, 600, 1124, 64))
    print(f"    ham uint16 -> {c}")
    print(f"    duz int    -> {d}")
    derinlik = min(100 - 0, 600 - 0, 2560 - (100 + 1124), 1440 - (600 + 64))
    print(f"    M1 kenarina EN KISA uzaklik = {derinlik} px  (INSIDE mi: "
          f"{'EVET' if derinlik >= 0 else 'HAYIR'})")
    b3 = c[0] == "CaptureError" and d[0] == "ok" and 100 != 1124 and derinlik >= 0
    sonuc["B3 x != w uyesi (aile x==w ile SINIRLI DEGIL)"] = b3
    print(f"    -> {'TUTUYOR' if b3 else 'TUTMUYOR'}")
    print()

    # --- B4: kenar grid'i 1108 / 240 --------------------------------------
    print("B4. Kenar grid'i (x 0..2600, y 0..1400, w/h in {1,50,200,500}):")
    print("    uint32/uint64 icin 6480 kombinasyonun 1108'i SESSIZ farkli geometri,")
    print("    240'i SESSIZCE kabul edilen GECERSIZ bolge")
    b4 = True
    for tip in (np.uint32, np.uint64):
        toplam = sessiz = gecersiz = 0
        for x in range(0, 2601, 100):
            for y in range(0, 1401, 100):
                for w in (1, 50, 200, 500):
                    for h in (1, 50, 200, 500):
                        try:
                            ham_r = Rect(tip(x), tip(y), tip(w), tip(h))  # type: ignore[arg-type]
                        except (OverflowError, ValueError):
                            continue
                        toplam += 1
                        ch = _olc(s, ham_r)
                        cd = _olc(s, Rect(x, y, w, h))
                        if ch[0] == "ok" and cd[0] == "ok" and ch[1] != cd[1]:
                            sessiz += 1
                        if ch[0] == "ok" and cd[0] == "CaptureError":
                            gecersiz += 1
        print(f"    {tip.__name__:8s}: toplam={toplam}  sessiz-farkli={sessiz}  "
              f"sessizce-kabul-edilen-gecersiz={gecersiz}")
        b4 = b4 and toplam == 6480 and sessiz == 1108 and gecersiz == 240
    sonuc["B4 kenar grid'i 6480 / 1108 / 240"] = b4
    print(f"    -> {'TUTUYOR' if b4 else 'TUTMUYOR'}")
    print()

    # --- B5: L duzeninde uint8 ciplak OverflowError ------------------------
    print("B5. L duzeni A=(0,0,100,100) B=(100,100,100,100), uint8 `Rect(0,0,201,201)`")
    print("    -> K6 taksonomisi DISINDA ciplak OverflowError")
    sL = CaptureService(FakeBackend((Rect(0, 0, 100, 100), Rect(100, 100, 100, 100))))
    try:
        rl = Rect(np.uint8(0), np.uint8(0), np.uint8(201), np.uint8(201))  # type: ignore[arg-type]
        cl = _olc(sL, rl)
    except (OverflowError, ValueError) as exc:
        cl = (f"KURULUMDA:{type(exc).__name__}", str(exc)[:60], 0)
    print(f"    ham uint8 -> {cl}")
    print(f"    duz int   -> {_olc(sL, Rect(0, 0, 201, 201))}")
    b5 = str(cl[0]).startswith("CIPLAK:OverflowError")
    sonuc["B5 L duzeni uint8 ciplak OverflowError"] = b5
    print(f"    -> {'TUTUYOR' if b5 else 'TUTMUYOR'}")
    print()

    # --- B6: atif verilen ham cikti dosyalari -----------------------------
    print("B6. Docstring'in ATIF VERDIGI ham cikti dosyalari diskte VAR ve DOLU mu?")
    b6 = True
    for rel in (".agents/tasks/T-005/evidence/t3-2-derin-inside-ayrisma.txt",
                ".agents/tasks/T-005/evidence/t2-2-tasma-olcumu.txt"):
        p = DEPO / rel
        var = p.is_file()
        boyut = p.stat().st_size if var else 0
        print(f"    {rel}: {'VAR' if var else 'YOK'}  {boyut} bayt")
        b6 = b6 and var and boyut > 0
    sonuc["B6 atif dosyalari var ve dolu"] = b6
    print(f"    -> {'TUTUYOR' if b6 else 'TUTMUYOR'}")
    print()
    return sonuc


# ---------------------------------------------------------------------------
# C. kapali-kume evrensellerinin olcumu
# ---------------------------------------------------------------------------

def c_kapali_kume() -> dict[str, bool]:
    print("=" * 78)
    print("C. KAPALI-KUME EVRENSELLERI -- gerçekten kosuluyorlar mi?")
    print("=" * 78)
    sonuc: dict[str, bool] = {}

    print("C1. 'bunlarin HICBIRINDE backend cagrilmaz' (K6 sinif a, dort kosul)")
    kosullar: list[tuple[str, tuple[Rect, ...], Rect]] = [
        ("tamsayi olmayan alan", GERCEK_DUZEN, Rect(0, 0, 10, 10)),
        ("alan sifir", GERCEK_DUZEN, Rect(10, 10, 0, 10)),
        ("alan negatif", GERCEK_DUZEN, Rect(10, 10, -5, 10)),
        ("monitor kumesi bos", (), Rect(10, 10, 10, 10)),
        ("bolge OUTSIDE", GERCEK_DUZEN, Rect(999999, 999999, 10, 10)),
    ]
    c1 = True
    for ad, duzen, r in kosullar:
        fb = FakeBackend(duzen)
        srv = CaptureService(fb)
        if ad == "tamsayi olmayan alan":
            r = Rect(0.5, 0, 10, 10)  # type: ignore[arg-type]
        try:
            srv.capture_region(r)
            durum = "ISTISNA YOK (!)"
            ok = False
        except CaptureError as exc:
            durum = f"CaptureError: {str(exc)[:38]}"
            ok = fb.grab_calls == 0
        except Exception as exc:  # noqa: BLE001
            durum = f"CIPLAK {type(exc).__name__}: {str(exc)[:30]}"
            ok = False
        print(f"    {ad:24s} grab_calls={fb.grab_calls}  {durum}")
        c1 = c1 and ok
    sonuc["C1 K6 sinif a: hicbirinde backend cagrilmaz"] = c1
    print(f"    -> {'TUTUYOR' if c1 else 'TUTMUYOR'}")
    print()

    print("C2. 'Kirpma HER ZAMAN union_bbox'a karsi, ASLA tek monitore karsi degil'")
    print("    iki monitore yayilan 5300w bolge:")
    srv = CaptureService(FakeBackend(GERCEK_DUZEN))
    fr = srv.capture_region(Rect(-2600, 100, 5300, 200))
    tek = 2560
    birlesim = 5120
    print(f"    Frame.rect = {(fr.rect.x, fr.rect.y, fr.rect.w, fr.rect.h)}")
    print(f"    tek monitore karsi olsaydi w={tek}, birlesime karsi w={birlesim}")
    c2 = fr.rect.w == birlesim
    sonuc["C2 kirpma birlesime karsi"] = c2
    print(f"    -> {'TUTUYOR' if c2 else 'TUTMUYOR'}")
    print()
    return sonuc


def main() -> None:
    a_tarama()
    b = b_iddialar()
    c = c_kapali_kume()
    print("=" * 78)
    print("OZET")
    print("=" * 78)
    hepsi = {**b, **c}
    for ad, ok in hepsi.items():
        print(f"  {'TUTUYOR ' if ok else 'TUTMUYOR'}  {ad}")
    print()
    print(f"  {sum(hepsi.values())}/{len(hepsi)} iddia bagimsiz olcumle dogrulandi")


if __name__ == "__main__":
    main()
