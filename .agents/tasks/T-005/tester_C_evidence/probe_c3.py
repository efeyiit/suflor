"""MERCEK C kesif sondasi 3 -- MssBackend OMRU (casus modul, alt surec).

headless_check.py §3'un yaptigini yapar ama BASKA noktalari olcer:
close() sonrasi grab(), ic ice `with`, N cagrilik sizinti dengesi,
__exit__'in istisnayi yutmamasi, tutamac kimligi.
"""
import sys, types, json
sys.path.insert(0, r"C:\Users\pc\Desktop\efe\çeviri uygulaması")
import numpy as np

RAW = [
    {'left': -2560, 'top': 0, 'width': 5120, 'height': 1440},
    {'left': -2560, 'top': 0, 'width': 2560, 'height': 1440, 'is_primary': False},
    {'left': 0, 'top': 0, 'width': 2560, 'height': 1440, 'is_primary': True},
]
PATTERN = b'\x01\x02\x03\xff'
state = {'raw': RAW, 'MSS': 0, 'close': 0, 'canli': 0, 'ornekler': [],
         'kapat_patlat': False}


class _Shot:
    def __init__(self, box):
        self.width, self.height = box['width'], box['height']
        self.size = (self.width, self.height)
        self.raw = bytearray(PATTERN * (self.width * self.height))
        self.bgra = bytes(self.raw)
    @property
    def __array_interface__(self):
        return {'shape': (self.height, self.width, 4), 'typestr': '|u1',
                'data': self.raw, 'version': 3}


class _FakeMSS:
    def __init__(self, **kw):
        state['MSS'] += 1
        state['canli'] += 1
        state['ornekler'].append(self)
        self.no = state['MSS']
        self._closed = False
        self._monitors = None
    @property
    def monitors(self):
        if self._monitors is None:
            self._monitors = [dict(m) for m in state['raw']]
        return self._monitors
    def grab(self, box):
        if self._closed:
            raise OSError("kapali MSS uzerinde grab")
        return _Shot(box)
    def close(self):
        if state['kapat_patlat']:
            raise OSError("close patladi")
        if not self._closed:
            state['close'] += 1
            state['canli'] -= 1
            self._closed = True
    def __enter__(self):
        return self
    def __exit__(self, *a):
        self.close(); return False


spy = types.ModuleType('mss'); spy.MSS = _FakeMSS
def _dep(*a, **k):
    raise AssertionError("mss.mss() cagrildi")
spy.mss = _dep
sys.modules['mss'] = spy

sys.path.insert(0, r"C:\Users\pc\Desktop\efe\çeviri uygulaması")
from src.capture.service import MssBackend
from src.contracts.models import Rect

R = Rect(10, 20, 64, 16)

# --- A. monitors() N cagri: kurulum == kapatma, canli sayisi hic 1'i asmiyor mu
b = MssBackend()
N = 200
zirve = 0
for i in range(N):
    b.monitors()
    zirve = max(zirve, state['canli'])
print(f"[A] {N} x monitors(): MSS={state['MSS']} close={state['close']} "
      f"canli={state['canli']} zirve_canli={zirve}")
print(f"    kurulum==kapatma: {state['MSS'] == state['close']}  "
      f"sizinti={state['MSS'] - state['close']}")

# --- B. grab(): tek uzun omurlu tutamac; kimlik sabit mi
onceki_mss = state['MSS']
b.grab(R); ilk_tutamac = state['ornekler'][-1]
b.grab(R); b.grab(R)
print(f"[B] 3 x grab(): +MSS={state['MSS']-onceki_mss} (1 olmali) "
      f"tutamac_kimligi_sabit={state['ornekler'][-1] is ilk_tutamac} canli={state['canli']}")

# --- C. close() idempotent + close() sonrasi grab()
b.close()
c1 = state['close']
b.close()
c2 = state['close']
print(f"[C] close() x2: +{c1 - (c1-1)} sonra +{c2-c1} (ikinci 0 olmali) canli={state['canli']}")
onceki = state['MSS']
try:
    a = b.grab(R)
    print(f"    close() SONRASI grab(): calisti, YENI MSS kuruldu (+{state['MSS']-onceki}), "
          f"shape={np.asarray(a).shape} -> tutamac YENIDEN DOGDU, canli={state['canli']}")
except Exception as e:
    print(f"    close() sonrasi grab(): {type(e).__name__}: {e}")
b.close()

# --- D. baglam yoneticisi: ic ice `with`
state['MSS'] = state['close'] = state['canli'] = 0
b2 = MssBackend()
with b2 as x1:
    b2.grab(R)
    ic_kurulum = state['MSS']
    with b2 as x2:
        b2.grab(R)
    orta_close = state['close']
    orta_canli = state['canli']
    # DIS `with` hala aciktir ama tutamac IC cikista kapandi
    try:
        b2.grab(R)
        yeniden = state['MSS'] - ic_kurulum
    except Exception as e:
        yeniden = f"{type(e).__name__}"
son_close = state['close']
print(f"[D] ic ice with: x1 is b2={x1 is b2} x2 is b2={x2 is b2} "
      f"ic_cikista_close={orta_close} (1) canli={orta_canli} "
      f"-> dis blokta grab YENI tutamac kurdu mu: +{yeniden}; son_close={son_close}")
print(f"    cikista sizinti={state['MSS'] - state['close']}")

# --- E. `with` icinde istisna: yutuluyor mu, tutamac kapaniyor mu
state['MSS'] = state['close'] = state['canli'] = 0
yutuldu = None
try:
    with MssBackend() as b3:
        b3.grab(R)
        raise ValueError("blok icinde patlama")
except ValueError:
    yutuldu = False
except BaseException as e:
    yutuldu = f"baska: {type(e).__name__}"
else:
    yutuldu = True
print(f"[E] with icinde ValueError: yutuldu={yutuldu} (False olmali) "
      f"close={state['close']} (1) canli={state['canli']} (0)")

# --- F. hic grab yapilmadan close()/__exit__
state['MSS'] = state['close'] = state['canli'] = 0
b4 = MssBackend()
b4.close()
with MssBackend() as b5:
    pass
print(f"[F] grab yapilmadan close()/with: MSS={state['MSS']} (0) close={state['close']} (0)")

# --- G. tutamacin close()'u patlarsa close() hala idempotent mi
state['MSS'] = state['close'] = state['canli'] = 0
b6 = MssBackend()
b6.grab(R)
state['kapat_patlat'] = True
try:
    b6.close()
    print("[G] 1. close(): sessiz")
except Exception as e:
    print(f"[G] 1. close(): {type(e).__name__}: {e}")
try:
    b6.close()
    print("    2. close(): sessiz (idempotent)")
except Exception as e:
    print(f"    2. close(): {type(e).__name__}: {e}  -> IDEMPOTENT DEGIL")
state['kapat_patlat'] = False
b6.close()
print(f"    3. close() (patlatma kapali): close={state['close']} canli={state['canli']}")

# --- H. monitors() casus listeyi CANLI okuyor mu + donen liste kopya mi
state['MSS'] = state['close'] = 0
b7 = MssBackend()
m1 = b7.monitors()
state['raw'] = RAW[:2]
m2 = b7.monitors()
state['raw'] = RAW
m1[0]['left'] = 999999
m3 = b7.monitors()
print(f"[H] canlilik: len(m1)={len(m1)} len(m2)={len(m2)} len(m3)={len(m3)}; "
      f"m1 bozuldu -> m3[0]['left']={m3[0]['left']} (-2560 olmali)")
