"""MERCEK C kesif sondasi 2 -- refresh hata yolu, bos kume, kume degisimi, capture_full."""
import sys, types
sys.path.insert(0, r"C:\Users\pc\Desktop\efe\çeviri uygulaması")
_m = types.ModuleType("mss")
def _yasak(*a, **k):
    raise AssertionError("gercek mss yasak")
_m.MSS = _yasak; _m.mss = _yasak
sys.modules["mss"] = _m

import numpy as np
from src.capture.service import CaptureService, FakeBackend
from src.capture.monitors import union_bbox
from src.contracts.errors import CaptureError
from src.contracts.models import Rect

M_SOL = Rect(-2560, 0, 2560, 1440)
M_SAG = Rect(0, 0, 2560, 1440)
DUZEN = (M_SOL, M_SAG)
IYI = Rect(0, 0, 10, 10)


def ham(rects):
    if not rects:
        return [{"left": 0, "top": 0, "width": 0, "height": 0}]
    x = min(r.x for r in rects); y = min(r.y for r in rects)
    sag = max(r.right for r in rects); alt = max(r.bottom for r in rects)
    out = [{"left": x, "top": y, "width": sag - x, "height": alt - y}]
    out += [{"left": r.x, "top": r.y, "width": r.w, "height": r.h} for r in rects]
    return out


def kur(monitors=DUZEN):
    fb = FakeBackend(monitors)
    return CaptureService(fb, lambda: 1234.5), fb


# ---- 1. refresh hata yolu: bozuk sozlugun HER varyanti + eski kume korunuyor mu
BOZUK = {
    "left_eksik":  [{"left": 0, "top": 0, "width": 1, "height": 1}, {"top": 0, "width": 100, "height": 100}],
    "left_None":   [{"left": 0, "top": 0, "width": 1, "height": 1}, {"left": None, "top": 0, "width": 100, "height": 100}],
    "width_str":   [{"left": 0, "top": 0, "width": 1, "height": 1}, {"left": 0, "top": 0, "width": "2560", "height": 100}],
    "height_bool": [{"left": 0, "top": 0, "width": 1, "height": 1}, {"left": 0, "top": 0, "width": 100, "height": True}],
    "top_float":   [{"left": 0, "top": 0, "width": 1, "height": 1}, {"left": 0, "top": 1.5, "width": 100, "height": 100}],
    "np_bool":     [{"left": 0, "top": 0, "width": 1, "height": 1}, {"left": np.bool_(True), "top": 0, "width": 100, "height": 100}],
    "ikinci_bozuk":[{"left": 0, "top": 0, "width": 1, "height": 1},
                    {"left": 0, "top": 0, "width": 100, "height": 100},
                    {"left": 0, "top": 0, "width": None, "height": 100}],
}
print("[1] refresh_monitors() hata yolu -- eski kume korunuyor mu:")
for ad, raw in BOZUK.items():
    servis, fb = kur()
    eski = servis.monitors
    servis.capture_region(IYI)          # seq 0 tuketildi
    fb.raw_override = raw
    try:
        servis.refresh_monitors()
        durum = "FIRLATMADI"
    except CaptureError as e:
        durum = "CaptureError"
    fb.raw_override = None
    korundu = servis.monitors == eski
    # eski kumeyle calisiyor mu
    kare = servis.capture_region(Rect(-2600, 0, 100, 100))
    print(f"    {ad:13s} {durum:12s} korundu={korundu} sonraki_kirpma=({kare.rect.x},{kare.rect.w}) "
          f"mi={kare.rect.monitor_index} seq={kare.seq} monitors_calls={fb.monitors_calls}")

# ---- 1b. backend.monitors() KENDISI istisna firlatirsa
class Patlayan(FakeBackend):
    def __init__(self, monitors):
        super().__init__(monitors)
        self.patla = False
    def monitors(self):
        if self.patla:
            self.monitors_calls += 1
            raise OSError("surucu coktu")
        return super().monitors()

fb = Patlayan(DUZEN)
servis = CaptureService(fb, lambda: 1234.5)
eski = servis.monitors
servis.capture_region(IYI)
fb.patla = True
try:
    servis.refresh_monitors()
    print("[1b] FIRLATMADI")
except CaptureError as e:
    print("[1b] CaptureError (sarmalandi!):", e)
except OSError as e:
    print(f"[1b] OSError oldugu gibi yayildi: {e}; korundu={servis.monitors == eski}")
fb.patla = False
print(f"     sonraki capture seq={servis.capture_region(IYI).seq}")

# ---- 2. bos kume: kurulur, her cagri CaptureError, backend cagrisi 0
servis, fb = kur(())
print(f"[2] bos kume: kuruldu, monitors={servis.monitors}")
for ad, cagri in (("capture_region", lambda: servis.capture_region(IYI)),
                  ("capture_full(0)", lambda: servis.capture_full(0)),
                  ("capture_full(-1)", lambda: servis.capture_full(-1)),
                  ("capture_full(99)", lambda: servis.capture_full(99))):
    try:
        cagri(); print(f"    {ad}: FIRLATMADI")
    except CaptureError as e:
        print(f"    {ad}: CaptureError('{e}') grab={fb.grab_calls}")
print(f"    union_bbox(()) = {union_bbox(())}")

# ---- 2b. dolu -> bos -> dolu gecisi; seq korunur mu
servis, fb = kur()
print(f"[2b] dolu->bos->dolu: s1={servis.capture_region(IYI).seq}")
fb.raw_override = ham([])
servis.refresh_monitors()
print(f"     bos kume: {servis.monitors}")
try:
    servis.capture_region(IYI)
except CaptureError as e:
    print(f"     bosta capture: CaptureError('{e}')")
fb.raw_override = None
servis.refresh_monitors()
print(f"     geri dolu: {len(servis.monitors)} monitor, s2={servis.capture_region(IYI).seq} (1 olmali)")

# ---- 3. kume degisimi: SIRA degisimi (INSIDE ve PARTIAL yollari)
servis, fb = kur()
for ad, bolge in (("PARTIAL_sol", Rect(-2600, 0, 100, 100)),
                  ("INSIDE_sag", Rect(100, 100, 50, 50)),
                  ("INSIDE_yayilan", Rect(-50, 0, 100, 100)),
                  ("PARTIAL_ust", Rect(100, -50, 100, 100))):
    servis, fb = kur()
    a = servis.capture_region(bolge)
    fb.raw_override = ham([M_SAG, M_SOL])
    servis.refresh_monitors()
    b = servis.capture_region(bolge)
    ayni_geo = (a.rect.x, a.rect.y, a.rect.w, a.rect.h) == (b.rect.x, b.rect.y, b.rect.w, b.rect.h)
    print(f"[3] {ad:15s} geo_ayni={ayni_geo} geo={(a.rect.x,a.rect.y,a.rect.w,a.rect.h)} "
          f"mi: {a.rect.monitor_index} -> {b.rect.monitor_index}  "
          f"grab_kutu_ayni={(fb.grab_rects[0].x,fb.grab_rects[0].w)==(fb.grab_rects[1].x,fb.grab_rects[1].w)}")

# ---- 3b. SAYI degisimi: 2 -> 1 (bolge OUTSIDE/PARTIAL olur mu)
for ad, bolge, beklenen in (("tam_sol->OUTSIDE", Rect(-2000, 0, 100, 100), "outside"),
                            ("yayilan->PARTIAL", Rect(-50, 0, 100, 100), "partial")):
    servis, fb = kur()
    a = servis.capture_region(bolge)
    fb.raw_override = ham([M_SAG])
    servis.refresh_monitors()
    try:
        b = servis.capture_region(bolge)
        print(f"[3b] {ad:20s} once=({a.rect.x},{a.rect.w},mi={a.rect.monitor_index}) "
              f"sonra=({b.rect.x},{b.rect.w},mi={b.rect.monitor_index})")
    except CaptureError as e:
        print(f"[3b] {ad:20s} once=({a.rect.x},{a.rect.w}) sonra=CaptureError('{e}')")

# ---- 3c. sira degisimi capture_full'un HEDEFINI degistirir mi (K5 konumsal kimlik)
servis, fb = kur()
a = servis.capture_full(0)
fb.raw_override = ham([M_SAG, M_SOL])
servis.refresh_monitors()
b = servis.capture_full(0)
print(f"[3c] capture_full(0) sira degisiminden ONCE x={a.rect.x} SONRA x={b.rect.x} "
      f"-> ayni fiziksel monitor mu: {a.rect.x == b.rect.x}")

# ---- 4. capture_full aralik: her sinir + backend cagrisi + seq
servis, fb = kur()
servis.capture_region(IYI)  # seq 0
for i in (-100, -2, -1, 0, 1, 2, 3, 99):
    onceki_grab = fb.grab_calls
    try:
        k = servis.capture_full(i)
        print(f"[4] capture_full({i:4d}) -> kare seq={k.seq} x={k.rect.x} mi={k.rect.monitor_index} "
              f"grab+{fb.grab_calls-onceki_grab}")
    except CaptureError as e:
        print(f"[4] capture_full({i:4d}) -> CaptureError grab+{fb.grab_calls-onceki_grab} ('{e}')")

# ---- 5. sifir alanli monitor kumede: servis kurulur mu, capture_full ne yapar
fb = FakeBackend((Rect(0, 0, 100, 100),))
fb.raw_override = [{"left": 0, "top": 0, "width": 100, "height": 100},
                   {"left": 0, "top": 0, "width": 0, "height": 1440}]
try:
    servis = CaptureService(fb, lambda: 1234.5)
    print(f"[5] sifir genislikli monitor kabul edildi: {servis.monitors}")
    try:
        servis.capture_full(0)
    except CaptureError as e:
        print(f"    capture_full(0) -> CaptureError('{e}') grab={fb.grab_calls}")
except CaptureError as e:
    print(f"[5] yapimda CaptureError: {e}")
