"""MERCEK C kesif sondasi 1 -- seq matrisi + K6 dizileri."""
import sys, types, itertools, json
sys.path.insert(0, r"C:\Users\pc\Desktop\efe\çeviri uygulaması")

# K1 engeli
_m = types.ModuleType("mss")
def _yasak(*a, **k):
    raise AssertionError("gercek mss yasak")
_m.MSS = _yasak
_m.mss = _yasak
sys.modules["mss"] = _m

import numpy as np
from src.capture.service import CaptureService, FakeBackend
from src.contracts.errors import CaptureError
from src.contracts.models import Rect

M_SOL = Rect(-2560, 0, 2560, 1440)
M_SAG = Rect(0, 0, 2560, 1440)
DUZEN = (M_SOL, M_SAG)
IYI = Rect(0, 0, 10, 10)
DISARIDA = Rect(-99999, 0, 10, 10)


class Yonlendirici:
    """image_factory: her cagrida `mod`a gore davranir."""
    def __init__(self):
        self.mod = "ok"
        self.cagri = 0
    def __call__(self, rect):
        self.cagri += 1
        if self.mod == "b":
            raise RuntimeError(f"backend coktu #{self.cagri}")
        if self.mod == "c":
            return None
        return np.zeros((rect.h, rect.w, 4), dtype=np.uint8)


def kur():
    y = Yonlendirici()
    fb = FakeBackend(DUZEN, y)
    return CaptureService(fb, lambda: 1234.5), fb, y


# ---- 1. seq tam matrisi: {basari, a, b, c, refresh} dizilerinin permutasyonlari
def olay(servis, fb, y, ad):
    if ad == "S":
        y.mod = "ok"
        return servis.capture_region(IYI).seq
    if ad == "a":
        y.mod = "ok"
        try:
            servis.capture_region(DISARIDA)
        except CaptureError:
            return None
        raise SystemExit("a: CaptureError beklendi")
    if ad == "b":
        y.mod = "b"
        try:
            servis.capture_region(IYI)
        except CaptureError:
            return None
        raise SystemExit("b: CaptureError beklendi")
    if ad == "c":
        y.mod = "c"
        try:
            servis.capture_region(IYI)
        except CaptureError:
            return None
        raise SystemExit("c: CaptureError beklendi")
    if ad == "R":
        servis.refresh_monitors()
        return None
    raise SystemExit(ad)


ALFABE = ["S", "a", "b", "c", "R"]
kirik = []
toplam = 0
for n in (1, 2, 3):
    for dizi in itertools.product(ALFABE, repeat=n):
        servis, fb, y = kur()
        gorulen = []
        beklenen_seq = 0
        for ad in dizi:
            s = olay(servis, fb, y, ad)
            if ad == "S":
                gorulen.append(s)
        beklenen = list(range(sum(1 for a in dizi if a == "S")))
        toplam += 1
        if gorulen != beklenen:
            kirik.append((dizi, gorulen, beklenen))
print(f"[1] seq permutasyon matrisi: {toplam} dizi denendi, {len(kirik)} kirik")
for k in kirik[:20]:
    print("    KIRIK", k)

# ---- 2. K6 3x3 + karisik diziler
def olc(uretici, rect=IYI, monitors=DUZEN):
    fb = FakeBackend(monitors, uretici)
    servis = CaptureService(fb, lambda: 1234.5)
    try:
        kare = servis.capture_region(rect)
        return {"sonuc": "kare", "seq": kare.seq, "grab": fb.grab_calls,
                "cause": None, "context": None, "servis": servis, "fb": fb}
    except CaptureError as e:
        return {"sonuc": "hata", "seq": None, "grab": fb.grab_calls,
                "cause": type(e.__cause__).__name__ if e.__cause__ else None,
                "cause_msg": str(e.__cause__) if e.__cause__ else None,
                "context": type(e.__context__).__name__ if e.__context__ else None,
                "servis": servis, "fb": fb}


def sirali(*davranislar):
    """i. cagrida davranislar[i] uygulanir; sonrasi son eleman."""
    sayac = [0]
    def u(rect):
        i = sayac[0]
        sayac[0] += 1
        d = davranislar[i] if i < len(davranislar) else davranislar[-1]
        if d == "b":
            raise RuntimeError(f"istisna-{i+1}")
        if d == "c":
            return None
        if d == "c2":
            return np.zeros((3, 3, 3), dtype=np.uint8)
        return np.zeros((rect.h, rect.w, 4), dtype=np.uint8)
    return u


senaryolar = {
    "b_b_b": sirali("b", "b", "b"),
    "b_b_S": sirali("b", "b", "ok"),
    "b_S":   sirali("b", "ok"),
    "b_c":   sirali("b", "c"),
    "b_b_c": sirali("b", "b", "c"),
    "c_S":   sirali("c", "ok"),
    "S":     sirali("ok"),
    "c":     sirali("c"),
}
print("[2] K6 dizileri:")
for ad, u in senaryolar.items():
    r = olc(u)
    print(f"    {ad:8s} -> sonuc={r['sonuc']:5s} grab={r['grab']} seq={r['seq']} "
          f"cause={r['cause']}({r.get('cause_msg')}) context={r['context']}")

# ---- 2b. (a) sinifinda grab sayisi ve cause
fb = FakeBackend(DUZEN)
servis = CaptureService(fb, lambda: 1234.5)
try:
    servis.capture_region(DISARIDA)
except CaptureError as e:
    print(f"    a(OUTSIDE) -> grab={fb.grab_calls} cause={e.__cause__} context={e.__context__}")

# ---- 3. b sinifi: yeniden deneme sayaci CAGRI BASINA sifirlanir mi
sayac = [0]
def u3(rect):
    sayac[0] += 1
    if sayac[0] <= 5:
        raise RuntimeError("x")
    return np.zeros((rect.h, rect.w, 4), dtype=np.uint8)
fb = FakeBackend(DUZEN, u3)
servis = CaptureService(fb, lambda: 1234.5)
sonuclar = []
for i in range(3):
    try:
        sonuclar.append(("kare", servis.capture_region(IYI).seq))
    except CaptureError:
        sonuclar.append(("hata", None))
print(f"[3] arka arkaya 3 capture (backend ilk 5 cagride patliyor): {sonuclar} grab={fb.grab_calls}")

# ---- 4. saat istisnasi seq tuketir mi (taksonomi disi)
class PatlayanSaat:
    def __init__(self):
        self.n = 0
    def __call__(self):
        self.n += 1
        if self.n == 2:
            raise RuntimeError("saat coktu")
        return 1.0
fb = FakeBackend(DUZEN)
servis = CaptureService(fb, PatlayanSaat())
print("[4] saat istisnasi:")
print("    1.", servis.capture_region(IYI).seq)
try:
    servis.capture_region(IYI)
except Exception as e:
    print("    2. istisna:", type(e).__name__, e)
print("    3.", servis.capture_region(IYI).seq, "(2 ise seq TUKETILDI)")
