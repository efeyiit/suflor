"""KRT k5 -- kapi (real_check) ve Qt/PySide tuzaklari (gercek Windows).

    python .agents/tasks/T-013/krt_kosumlari/k5_kapi.py

p1 [1a] gecikme: kapinin 2 ms'lik bekle() dongusuyle 30 basis yuksuz / CPU yuku altinda (8 mesgul surec) -> medyan/max/>20 ms sayisi
p2 ayni filtre nesnesi iki kez installNativeEventFilter -> kac cagri; iki filtre, ilki True donerse ikincisi gorur mu (calistir x2 = iki servis + iki filtre)
p3 PySide sahiplik: filtre nesnesinin Python referansi dusurulup gc yapilinca WM_HOTKEY -> cokme mu? (alt surecte, cikis kodu)
p4 QObject servisi + destroyed -> removeNativeEventFilter: destroyed isleyicisinde filtre kaldirilabiliyor mu (Python sarmalayici hala var mi)
p5 [4a] kapat() sonrasi sentetik Ctrl+Alt+T ON PLANDAKI pencereye ulasir (kayit yokken tus sizdirma) -- QLineEdit ile
p6 baska threadden RegisterHotKey(NULL): kayit basarili mi, WM_HOTKEY ana threadin kuyruguna mi geliyor (K6 'yalniz ana thread' gercekten gerekli mi)
Stdout ASCII.
"""
from __future__ import annotations

import ctypes
import gc
import os
import statistics
import subprocess
import sys
import threading
import time
from ctypes import wintypes

from PySide6 import QtCore, QtWidgets

u32 = ctypes.windll.user32
k32 = ctypes.windll.kernel32
WM_HOTKEY = 0x0312
MOD_ALT, MOD_CONTROL, MOD_NOREPEAT = 0x1, 0x2, 0x4000
VK_CONTROL, VK_MENU, KEYUP = 0x11, 0x12, 0x2
u32.GetForegroundWindow.restype = wintypes.HWND


def bekle(ms: int) -> None:
    son = time.perf_counter() + ms / 1000
    while time.perf_counter() < son:
        QtWidgets.QApplication.processEvents(); time.sleep(0.002)


def tus(vk: int) -> None:
    u32.keybd_event(VK_CONTROL, 0, 0, 0); u32.keybd_event(VK_MENU, 0, 0, 0); u32.keybd_event(vk, 0, 0, 0)
    u32.keybd_event(vk, 0, KEYUP, 0); u32.keybd_event(VK_MENU, 0, KEYUP, 0); u32.keybd_event(VK_CONTROL, 0, KEYUP, 0)


class Filtre(QtCore.QAbstractNativeEventFilter):
    def __init__(self, ad: str = "f", yut: bool = True) -> None:
        super().__init__(); self.ad = ad; self.yut = yut; self.olaylar: list[tuple[int, float]] = []

    def nativeEventFilter(self, eventType, message):  # type: ignore[override]
        msg = wintypes.MSG.from_address(int(message))
        if msg.message == WM_HOTKEY:
            self.olaylar.append((int(msg.wParam), time.perf_counter())); return self.yut, 0
        return False, 0


P3_KOD = r'''
import ctypes, gc, sys, time
from ctypes import wintypes
from PySide6 import QtCore, QtWidgets
u32 = ctypes.windll.user32
class F(QtCore.QAbstractNativeEventFilter):
    def __init__(self): super().__init__(); self.n = 0
    def nativeEventFilter(self, t, m):
        msg = wintypes.MSG.from_address(int(m))
        if msg.message == 0x312: self.n += 1; return True, 0
        return False, 0
app = QtWidgets.QApplication(sys.argv)
def kur():
    f = F(); app.installNativeEventFilter(f)   # referans TUTULMUYOR
    return None
kur(); gc.collect()
u32.RegisterHotKey(None, 1, 0x1 | 0x2 | 0x4000, ord("T"))
for _ in range(3):
    u32.keybd_event(0x11,0,0,0); u32.keybd_event(0x12,0,0,0); u32.keybd_event(ord("T"),0,0,0)
    u32.keybd_event(ord("T"),0,2,0); u32.keybd_event(0x12,0,2,0); u32.keybd_event(0x11,0,2,0)
    son = time.perf_counter() + 0.3
    while time.perf_counter() < son: app.processEvents(); time.sleep(0.002)
# ayrica 1000 bos mesaj: bir pencere gosterip gizle
w = QtWidgets.QWidget(); w.show(); son = time.perf_counter() + 0.3
while time.perf_counter() < son: app.processEvents(); time.sleep(0.002)
u32.UnregisterHotKey(None, 1)
print("P3 alt surec sagkaldi (cokme yok)", flush=True)
'''


def p1(app: QtWidgets.QApplication) -> None:
    f = Filtre(); app.installNativeEventFilter(f)
    assert u32.RegisterHotKey(None, 1, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, ord("T"))

    def olc(n: int) -> list[float]:
        out = []
        for _ in range(n):
            f.olaylar.clear(); t0 = time.perf_counter(); tus(ord("T")); bekle(120)
            out.append((f.olaylar[0][1] - t0) * 1000 if f.olaylar else float("nan"))
        return out

    yuksuz = olc(30)
    yuk = [subprocess.Popen([sys.executable, "-c", "while True: pass"]) for _ in range(max(8, (os.cpu_count() or 4)))]
    time.sleep(0.5)
    try:
        yuklu = olc(30)
    finally:
        for y in yuk: y.kill()
    # ayrica: ana thread'in kendisi mesgulken (GIL) -- 3 python thread sonsuz dongude
    dur = threading.Event()
    def mesgul() -> None:
        while not dur.is_set(): sum(range(2000))
    ths = [threading.Thread(target=mesgul, daemon=True) for _ in range(3)]
    for t in ths: t.start()
    try:
        gil = olc(30)
    finally:
        dur.set()
    for ad, d in (("yuksuz", yuksuz), ("CPU yuku (mesgul surecler)", yuklu), ("surec ici 3 thread (GIL)", gil)):
        d2 = [x for x in d if x == x]
        print(f"p1 [1a] gecikme {ad}: n={len(d2)}/30 medyan={statistics.median(d2):.1f} max={max(d2):.1f} ms  >20 ms: {sum(1 for x in d2 if x >= 20)}  kayip: {30 - len(d2)}")
    u32.UnregisterHotKey(None, 1); app.removeNativeEventFilter(f)


def p2(app: QtWidgets.QApplication) -> None:
    f = Filtre("a"); app.installNativeEventFilter(f); app.installNativeEventFilter(f)
    assert u32.RegisterHotKey(None, 1, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, ord("T"))
    f.olaylar.clear(); tus(ord("T")); bekle(300)
    print(f"p2 ayni filtre 2x install -> WM_HOTKEY cagri sayisi={len(f.olaylar)} (1: Qt tekilliyor / 2: iki kez)")
    app.removeNativeEventFilter(f)
    a = Filtre("ilk", yut=True); b = Filtre("ikinci", yut=True); app.installNativeEventFilter(a); app.installNativeEventFilter(b)
    a.olaylar.clear(); b.olaylar.clear(); tus(ord("T")); bekle(300)
    print(f"p2 iki filtre (ilk kurulan True donuyor): ilk={len(a.olaylar)} ikinci={len(b.olaylar)}  -> hangisi gordu? (calistir x2: ESKI servisin filtresi bilinmeyen id'de True donerse YENI servis olayi ALAMAZ)")
    a.yut = False; a.olaylar.clear(); b.olaylar.clear(); tus(ord("T")); bekle(300)
    print(f"p2 ilk False donunce: ilk={len(a.olaylar)} ikinci={len(b.olaylar)}")
    app.removeNativeEventFilter(a); app.removeNativeEventFilter(b); u32.UnregisterHotKey(None, 1)


def p3() -> None:
    r = subprocess.run([sys.executable, "-c", P3_KOD], capture_output=True, text=True, timeout=60)
    print(f"p3 filtre referansi dusurulmus alt surec: cikis={r.returncode} ({'cokme (0xC0000005 = erisim ihlali)' if r.returncode not in (0,) else 'sagkaldi'}) stdout={r.stdout.strip()!r} stderr_son={r.stderr.strip().splitlines()[-1] if r.stderr.strip() else ''!r}")


temizle_log: list[str] = []


class Servis(QtCore.QObject):
    def __init__(self, app: QtWidgets.QApplication, ad: str, ebeveyn: QtCore.QObject | None = None) -> None:
        super().__init__(ebeveyn)
        self._filtre = Filtre(ad); self._app = app; self._ad = ad
        app.installNativeEventFilter(self._filtre)
        self.destroyed.connect(self._temizle)  # bagli yontem (T-012 deseni)

    def _temizle(self) -> None:
        temizle_log.append(self._ad); self._app.removeNativeEventFilter(self._filtre); u32.UnregisterHotKey(None, 1)


def _kur(app: QtWidgets.QApplication, ad: str, ebeveyn: QtCore.QObject | None) -> tuple[Servis, Filtre]:
    s = Servis(app, ad, ebeveyn); assert u32.RegisterHotKey(None, 1, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, ord("T")), "kayit"
    return s, s._filtre


def _olay(f: Filtre) -> int:
    f.olaylar.clear(); tus(ord("T")); bekle(250); return len(f.olaylar)


def p4(app: QtWidgets.QApplication) -> None:
    import shiboken6
    # a) ebeveyn.deleteLater + processEvents dongusu (real_check bekle() tarzi)
    eb = QtCore.QObject(); s, f = _kur(app, "a", eb); temizle_log.clear()
    eb.deleteLater(); bekle(200); ran_pe = "a" in temizle_log; n_pe = _olay(f)
    QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete); bekle(50); ran_spe = "a" in temizle_log; n_spe = _olay(f)
    print(f"p4a ebeveyn.deleteLater + processEvents dongusu: destroyed isleyicisi kostu={ran_pe} olay={n_pe}; sendPostedEvents(DeferredDelete) sonrasi kostu={ran_spe} olay={n_spe} (real_check bekle() deleteLater'i ISLEMEZ mi?)")
    if not ran_spe: app.removeNativeEventFilter(f); u32.UnregisterHotKey(None, 1)
    # b) ebeveyn.deleteLater + ic ice QEventLoop (qtbot.wait tarzi)
    eb = QtCore.QObject(); s, f = _kur(app, "b", eb); temizle_log.clear()
    eb.deleteLater(); loop = QtCore.QEventLoop(); QtCore.QTimer.singleShot(100, loop.quit); loop.exec()
    ran = "b" in temizle_log; n = _olay(f)
    print(f"p4b ebeveyn.deleteLater + ic ice QEventLoop.exec (qtbot.wait): destroyed isleyicisi kostu={ran} olay={n} (0 beklenir) servis C++ gecerli={shiboken6.isValid(s)}")
    if not ran: app.removeNativeEventFilter(f); u32.UnregisterHotKey(None, 1)
    # c) ebeveynsiz servis: del + gc
    s, f = _kur(app, "c", None); temizle_log.clear(); zs = None
    import weakref; zs = weakref.ref(s)
    del s; gc.collect(); bekle(100); ran = "c" in temizle_log; n = _olay(f)
    print(f"p4c ebeveynsiz servis del+gc: destroyed isleyicisi kostu={ran} olay={n} (0 beklenir) sarmalayici weakref None={zs() is None}")
    if not ran: app.removeNativeEventFilter(f); u32.UnregisterHotKey(None, 1)
    # d) ebeveyn Python referansi dusuruldu (ebeveynsiz QObject ebeveyn)
    eb = QtCore.QObject(); s, f = _kur(app, "d", eb); temizle_log.clear(); zs = weakref.ref(s)
    del eb; gc.collect(); bekle(100); ran = "d" in temizle_log; n = _olay(f)
    print(f"p4d ebeveyn del+gc (cocuk servis): destroyed isleyicisi kostu={ran} olay={n} (0 beklenir) servis C++ gecerli={shiboken6.isValid(s)}")
    if not ran: app.removeNativeEventFilter(f); u32.UnregisterHotKey(None, 1)
    # e) AnaPencere benzeri: QWidget ebeveyn, kapat() sonra deleteLater + ic ice loop
    w = QtWidgets.QWidget(); s, f = _kur(app, "e", w); temizle_log.clear()
    w.show(); bekle(100); w.hide(); w.deleteLater(); loop = QtCore.QEventLoop(); QtCore.QTimer.singleShot(100, loop.quit); loop.exec()
    ran = "e" in temizle_log; n = _olay(f); ok_yeniden = bool(u32.RegisterHotKey(None, 1, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, ord("T"))); u32.UnregisterHotKey(None, 1)
    print(f"p4e QWidget ebeveyn deleteLater + ic ice loop: kostu={ran} olay={n} Ctrl+Alt+T yeniden alinabiliyor={ok_yeniden}")
    if not ran: app.removeNativeEventFilter(f); u32.UnregisterHotKey(None, 1)


def p5(app: QtWidgets.QApplication) -> None:
    w = QtWidgets.QWidget(); w.setWindowTitle("KRT k5"); le = QtWidgets.QLineEdit(w); w.resize(300, 80); w.show(); w.raise_(); w.activateWindow(); le.setFocus(); bekle(500)
    onde = int(u32.GetForegroundWindow() or 0) == int(w.winId())
    le.clear(); tus(ord("T")); bekle(300)
    print(f"p5 kayit YOKKEN sentetik Ctrl+Alt+T on plandaki pencereye ulasir: on planda={onde} QLineEdit metni={le.text()!r} (bos: Ctrl+Alt+T karakter uretmez ama tus olayi gitti; kapi [4a] sonrasi tuslar TERMINALE/EDITORE gider)")
    # Ctrl+Alt+T'nin Qt tarafinda gorulmesi
    class Gozcu(QtCore.QObject):
        def __init__(self) -> None: super().__init__(); self.n = 0
        def eventFilter(self, o, e):  # type: ignore[override]
            if e.type() == QtCore.QEvent.Type.KeyPress and e.key() == QtCore.Qt.Key.Key_T: self.n += 1
            return False
    g = Gozcu(); le.installEventFilter(g); tus(ord("T")); bekle(300)
    print(f"p5 kayit yokken Qt KeyPress(T) sayisi={g.n} (1: tus pencereye ulasti)")
    w.close()


def p6(app: QtWidgets.QApplication) -> None:
    f = Filtre(); app.installNativeEventFilter(f); sonuc: dict[str, object] = {}

    def th() -> None:
        ok = bool(u32.RegisterHotKey(None, 1, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, ord("T"))); sonuc["ok"] = ok; sonuc["err"] = 0 if ok else k32.GetLastError()
        # bu threadin kendi kuyrugunu boşaltma: 1.5 s bekle (mesaj dongusu yok)
        time.sleep(1.5); sonuc["kaldir"] = bool(u32.UnregisterHotKey(None, 1))
    t = threading.Thread(target=th); t.start(); time.sleep(0.3)
    f.olaylar.clear(); tus(ord("T")); bekle(500); t.join()
    print(f"p6 baska threadden RegisterHotKey(NULL): kayit={sonuc.get('ok')} err={sonuc.get('err')}; ana thread filtresine WM_HOTKEY={len(f.olaylar)} (0: olay o threadin kuyrugunda kayboldu -> K6 'yalniz ana thread' GEREKLI); UnregisterHotKey ayni threadden={sonuc.get('kaldir')}")
    app.removeNativeEventFilter(f)


def main() -> int:
    sys.stdout.reconfigure(encoding="ascii", errors="backslashreplace")
    app = QtWidgets.QApplication(sys.argv)
    print(f"platform={app.platformName()} cpu={os.cpu_count()}")
    secim = sys.argv[1:] or ["p1", "p2", "p3", "p4", "p5", "p6"]
    for ad in secim:
        {"p1": lambda: p1(app), "p2": lambda: p2(app), "p3": p3, "p4": lambda: p4(app), "p5": lambda: p5(app), "p6": lambda: p6(app)}[ad]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
