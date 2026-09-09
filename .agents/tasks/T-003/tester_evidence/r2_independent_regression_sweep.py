"""T-003 -- TUR 2 tester'in BAGIMSIZ regresyon taramasi (dpi.py).

Amac: implementer'in tur-1 kusurunu (0 < dpi_scale < 1 sessizce kabul)
duzelttigini dogruladiktan SONRA, bu duzeltmenin dpi_scale >= 1.0 icin
tur-1'de dogrulanmis her seyi BOZMADIGINI bagimsiz olarak (kendi rastgele
orneklememle, implementer'in / tur-1 tester'in ornek verilerinden farkli,
sabit tohum) yeniden sinamak. Bu dosya bir pytest paketi DEGIL -- duz bir
betik, tester_evidence altina ham cikti birakmak icin. Kalici regresyon
korumasi zaten tester_tests/test_dpi_adversarial.py icinde (guncellendi,
bkz. o dosya).
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from src.capture.dpi import (  # noqa: E402
    RegionValidity,
    _round_half_away_from_zero,
    clamp_to_monitor,
    classify_region,
    intersect,
    logical_to_physical,
    physical_to_logical,
    to_monitor_relative,
    to_virtual_desktop,
)
from src.contracts.models import Rect  # noqa: E402

SEED = 424242  # round-1'den FARKLI tohum -- bagimsizlik icin
FAILURES: list[str] = []


def check(condition: bool, msg: str) -> None:
    if not condition:
        FAILURES.append(msg)


# ---------------------------------------------------------------------------
# 0. KUSUR GERCEKTEN GITTI Mİ -- (0,1) araliginda sessizce kabul yok
# ---------------------------------------------------------------------------

print("== 0. (0,1) araliginda sessiz kabul kaldi mi? ==")
rng = random.Random(SEED)
silent_accepts = 0
n_checked = 20_000
for _ in range(n_checked):
    scale = rng.uniform(1e-6, 0.999999)
    x = rng.randint(-500_000, 500_000)
    y = rng.randint(-500_000, 500_000)
    w = rng.randint(0, 500_000)
    h = rng.randint(0, 500_000)
    r = Rect(x=x, y=y, w=w, h=h, dpi_scale=scale)
    try:
        logical_to_physical(r)
        silent_accepts += 1
        if silent_accepts <= 5:
            print(f"  SESSIZ KABUL (logical_to_physical): {r}")
    except ValueError:
        pass
    try:
        physical_to_logical(r)
        silent_accepts += 1
        if silent_accepts <= 5:
            print(f"  SESSIZ KABUL (physical_to_logical): {r}")
    except ValueError:
        pass
check(silent_accepts == 0, f"(0,1) araliginda {silent_accepts} sessiz kabul bulundu (n={n_checked * 2})")
print(f"  sonuc: {silent_accepts} sessiz kabul / {n_checked * 2} deneme (0 beklenir)")

# ---------------------------------------------------------------------------
# 0b. Sinir: tam 1.0 kabul, 0.999999 ve komsu float'lar reddedilir
# ---------------------------------------------------------------------------

print("\n== 0b. Sinir degeri: dpi_scale == 1.0 ve komsulari ==")
r_one = Rect(x=5, y=5, w=5, h=5, dpi_scale=1.0)
try:
    p = logical_to_physical(r_one)
    l = physical_to_logical(p)
    check(l == r_one, f"dpi_scale=1.0 round-trip basarisiz: {l} != {r_one}")
    print(f"  dpi_scale=1.0 KABUL edildi (dogru): {r_one} -> {p} -> {l}")
except ValueError as e:
    check(False, f"dpi_scale=1.0 REDDEDILDI (yanlis, kabul edilmeli): {e}")

for near_below in (0.999999, 0.9999999999, 1.0 - 1e-9):
    r = Rect(x=1, y=1, w=1, h=1, dpi_scale=near_below)
    try:
        logical_to_physical(r)
        check(False, f"dpi_scale={near_below!r} KABUL edildi (yanlis, reddedilmeli)")
        print(f"  HATA: dpi_scale={near_below!r} kabul edildi!")
    except ValueError:
        print(f"  dpi_scale={near_below!r} REDDEDILDI (dogru)")

# 1.0000001 (1.0'in az ustu) kabul edilmeli
r_above = Rect(x=1, y=1, w=1, h=1, dpi_scale=1.0000001)
try:
    logical_to_physical(r_above)
    print("  dpi_scale=1.0000001 KABUL edildi (dogru)")
except ValueError:
    check(False, "dpi_scale=1.0000001 REDDEDILDI (yanlis, s>=1.0 oldugu icin kabul edilmeli)")

# ---------------------------------------------------------------------------
# 0c. Hata mesaji "neden" aciklamasi tasiyor mu?
# ---------------------------------------------------------------------------

print("\n== 0c. ValueError mesaji aciklayici mi? ==")
try:
    logical_to_physical(Rect(x=0, y=0, w=1, h=1, dpi_scale=0.5))
    check(False, "beklenen ValueError firlamadi")
except ValueError as e:
    msg = str(e)
    print(f"  mesaj: {msg!r}")
    has_number = "0.5" in msg
    has_reason_word = any(w in msg for w in ("olmali", "inmez", "tutmaz", ">="))
    check(has_number, f"hata mesaji gelen degeri icermiyor: {msg!r}")
    check(has_reason_word, f"hata mesaji sadece 'invalid' degil, NEDEN aciklamiyor gibi gorunuyor: {msg!r}")
    check(len(msg) > 20, f"hata mesaji cok kisa / anlamsiz: {msg!r}")

# ---------------------------------------------------------------------------
# 1. ROUND-TRIP (s >= 1.0) -- genis, tur-1'den farkli rastgele ornekleme
# ---------------------------------------------------------------------------

print("\n== 1. Round-trip (dpi_scale >= 1.0), genis rastgele ornekleme ==")
rng = random.Random(SEED + 1)
rt_failures = 0
n_rt = 300_000
for _ in range(n_rt):
    x = rng.randint(-1_000_000, 1_000_000)
    y = rng.randint(-1_000_000, 1_000_000)
    w = rng.randint(0, 1_000_000)
    h = rng.randint(0, 1_000_000)
    # 1.0'dan cok az buyuk degerler dahil, tam sayi olmayan genis aralik
    scale = 1.0 + rng.random() * 9.0  # [1.0, 10.0)
    original = Rect(x=x, y=y, w=w, h=h, dpi_scale=scale)
    physical = logical_to_physical(original)
    recovered = physical_to_logical(physical)
    if recovered != original:
        rt_failures += 1
        if rt_failures <= 5:
            print(f"  BASARISIZ: {original} -> {physical} -> {recovered}")
check(rt_failures == 0, f"round-trip {rt_failures}/{n_rt} durumda basarisiz (s>=1.0 icin 0 beklenir)")
print(f"  sonuc: {rt_failures} basarisizlik / {n_rt} deneme")

# ---------------------------------------------------------------------------
# 2. Yuvarlama simetrisi (kod degismedi ama bagimsiz teyit)
# ---------------------------------------------------------------------------

print("\n== 2. Yuvarlama simetrisi ==")
rng = random.Random(SEED + 2)
sym_failures = 0
n_sym = 100_000
for _ in range(n_sym):
    v = rng.uniform(-1_000_000, 1_000_000)
    if _round_half_away_from_zero(v) != -_round_half_away_from_zero(-v):
        sym_failures += 1
check(sym_failures == 0, f"yuvarlama asimetrisi {sym_failures}/{n_sym} durumda")
print(f"  sonuc: {sym_failures} asimetri / {n_sym} deneme")

# ---------------------------------------------------------------------------
# 3. Negatif koordinatli monitor (sol, ust, sol-ust) -- iki yonlu round-trip
# ---------------------------------------------------------------------------

print("\n== 3. Negatif koordinatli monitor round-trip ==")
monitors = [
    Rect(x=-2560, y=0, w=2560, h=1440, monitor_index=1, dpi_scale=1.0),
    Rect(x=0, y=-1440, w=2560, h=1440, monitor_index=2, dpi_scale=1.75),
    Rect(x=-1920, y=-1080, w=1920, h=1080, monitor_index=3, dpi_scale=2.25),
]
rng = random.Random(SEED + 3)
mon_failures = 0
n_mon = 2000
for m in monitors:
    for _ in range(n_mon):
        x = rng.randint(-10_000, 10_000)
        y = rng.randint(-10_000, 10_000)
        w = rng.randint(0, 5000)
        h = rng.randint(0, 5000)
        original = Rect(x=x, y=y, w=w, h=h)
        rel = to_monitor_relative(original, m)
        back = to_virtual_desktop(rel, m)
        if (back.x, back.y, back.w, back.h) != (x, y, w, h):
            mon_failures += 1
check(mon_failures == 0, f"negatif-koordinat monitor round-trip {mon_failures} durumda basarisiz")
print(f"  sonuc: {mon_failures} basarisizlik / {len(monitors) * n_mon} deneme")

# ---------------------------------------------------------------------------
# 4. Karisik DPI izolasyonu
# ---------------------------------------------------------------------------

print("\n== 4. Karisik DPI izolasyonu ==")
mons = {
    "a": Rect(x=0, y=0, w=1000, h=1000, monitor_index=0, dpi_scale=1.0),
    "b": Rect(x=1000, y=0, w=1000, h=1000, monitor_index=1, dpi_scale=1.75),
    "c": Rect(x=2000, y=0, w=1000, h=1000, monitor_index=2, dpi_scale=2.25),
}
logical = Rect(x=17, y=23, w=333, h=71)
sizes = {}
for key, mon in mons.items():
    phys = logical_to_physical(Rect(x=logical.x, y=logical.y, w=logical.w, h=logical.h, dpi_scale=mon.dpi_scale))
    sizes[key] = (phys.w, phys.h)
check(sizes["a"] != sizes["b"] != sizes["c"] and sizes["a"] != sizes["c"], f"karisik DPI sizmasi: {sizes}")
print(f"  boyutlar: {sizes} (hepsi farkli olmali)")

# clamp_to_monitor rect'in kendi (yanlis) dpi_scale'ini degil, monitorunkini kullanmali
stale = Rect(x=1050, y=50, w=100, h=100, dpi_scale=42.0, monitor_index=99)  # mons["b"] icinde (x:1000..2000)
clamped = clamp_to_monitor(stale, mons["b"])
check(clamped is not None and clamped.dpi_scale == 1.75 and clamped.monitor_index == 1,
      f"clamp_to_monitor yanlis metadata tasidi: {clamped}")
print(f"  clamp metadata: {clamped}")

# ---------------------------------------------------------------------------
# 5. classify_region sinir matrisi (tur-1'den farkli duzen)
# ---------------------------------------------------------------------------

print("\n== 5. classify_region sinir matrisi ==")
top = Rect(x=0, y=0, w=800, h=600, monitor_index=0)
bottom = Rect(x=0, y=600, w=800, h=600, monitor_index=1)  # dikey bitisik
gap_right = Rect(x=1200, y=0, w=800, h=600, monitor_index=2)  # 800..1200 bosluk
all_m = [top, bottom, gap_right]

cases = [
    (Rect(x=100, y=100, w=100, h=100), RegionValidity.INSIDE, "tek monitor icinde"),
    (Rect(x=100, y=550, w=100, h=100), RegionValidity.INSIDE, "dikey dikisi asan, bitisik -> INSIDE"),
    (Rect(x=700, y=100, w=600, h=100), RegionValidity.PARTIAL, "bosluga tasan -> PARTIAL"),
    (Rect(x=5000, y=5000, w=10, h=10), RegionValidity.OUTSIDE, "tamamen disarida"),
    (Rect(x=800, y=0, w=10, h=10), RegionValidity.OUTSIDE, "top'un sagina deger ama kesismez"),
    (Rect(x=0, y=0, w=0, h=0), RegionValidity.OUTSIDE, "sifir alan"),
]
for rect, expected, label in cases:
    got = classify_region(rect, all_m)
    check(got == expected, f"classify_region yanlis [{label}]: {rect} -> {got}, beklenen {expected}")
    print(f"  [{label}] {rect} -> {got} (beklenen {expected}) {'OK' if got == expected else 'FAIL'}")

# ---------------------------------------------------------------------------
# 6. Saflik / determinizm (bagimsiz teyit)
# ---------------------------------------------------------------------------

print("\n== 6. Determinizm ==")
r = Rect(x=-77, y=88, w=201, h=59, dpi_scale=1.6)
m = Rect(x=-300, y=-300, w=900, h=900, dpi_scale=1.4)
det_ok = (
    logical_to_physical(r) == logical_to_physical(r)
    and physical_to_logical(r) == physical_to_logical(r)
    and to_monitor_relative(r, m) == to_monitor_relative(r, m)
    and to_virtual_desktop(r, m) == to_virtual_desktop(r, m)
    and intersect(r, m) == intersect(r, m)
    and clamp_to_monitor(r, m) == clamp_to_monitor(r, m)
    and classify_region(r, [m]) == classify_region(r, [m])
)
check(det_ok, "determinizm bozuldu -- ayni girdi farkli sonuc verdi")
print(f"  determinizm: {'OK' if det_ok else 'FAIL'}")

# ---------------------------------------------------------------------------
# 7. Sozlesme degismezligi (frozen Rect, yeni nesne donusu)
# ---------------------------------------------------------------------------

print("\n== 7. Sozlesme degismezligi ==")
r = Rect(x=10, y=10, w=100, h=100, dpi_scale=1.5)
mutation_blocked = False
try:
    r.x = 999  # type: ignore[misc]
except Exception:
    mutation_blocked = True
check(mutation_blocked, "Rect mutasyona ACIK -- frozen sozlesmesi ihlal edildi")
p = logical_to_physical(r)
check(p is not r, "logical_to_physical girdiyle AYNI nesneyi donuyor -- yeni Rect donmesi gerekir")
check(r == Rect(x=10, y=10, w=100, h=100, dpi_scale=1.5), "girdi rect DEGISTI (yan etki)")
print(f"  mutasyon engellendi: {mutation_blocked}, yeni nesne: {p is not r}, girdi degismedi: OK")

# ---------------------------------------------------------------------------
# SONUC
# ---------------------------------------------------------------------------

print("\n" + "=" * 70)
if FAILURES:
    print(f"TOPLAM {len(FAILURES)} BASARISIZLIK:")
    for f in FAILURES:
        print(f"  - {f}")
    sys.exit(1)
else:
    print("TUM BAGIMSIZ REGRESYON KONTROLLERI GECTI (0 basarisizlik).")
    sys.exit(0)
