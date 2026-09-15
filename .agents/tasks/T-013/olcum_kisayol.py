"""T-013 ön ölçüm: Windows global kısayol (RegisterHotKey) Qt olay döngüsünde çalışır mı?

    python .agents/tasks/T-013/olcum_kisayol.py

U1 RegisterHotKey(hwnd=NULL) + QAbstractNativeEventFilter WM_HOTKEY alıyor mu (sentetik keybd_event ile) · gecikme
U2 çakışma: aynı kombinasyon ikinci kez → False, GetLastError 1409; başka süreç tutarken de
U3 bütün pencereler gizliyken (tepsi durumu) kısayol geliyor mu
U4 UnregisterHotKey sonrası tuş → olay yok; yeniden kayıt çalışıyor
U5 handler istisnası uygulamayı düşürmüyor (nativeEventFilter içinde)
U6 MOD_NOREPEAT: tuş basılı tutulunca tek olay
U7 bu makinede Ctrl+Alt+T / Ctrl+Alt+R boş mu
Stdout ASCII.
"""
from __future__ import annotations

import ctypes
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path

from PySide6 import QtCore, QtWidgets

u32 = ctypes.windll.user32
k32 = ctypes.windll.kernel32
WM_HOTKEY = 0x0312
MOD_ALT, MOD_CONTROL, MOD_SHIFT, MOD_NOREPEAT = 0x1, 0x2, 0x4, 0x4000
VK_CONTROL, VK_MENU = 0x11, 0x12
KEYEVENTF_KEYUP = 0x2
CIKTI = Path(__file__).resolve().parent
satirlar: list[str] = []


def olgu(m: str) -> None:
    satirlar.append(m); print(" ", m)


def bekle(ms: int) -> None:
    son = time.perf_counter() + ms / 1000
    while time.perf_counter() < son:
        QtWidgets.QApplication.processEvents()
        time.sleep(0.002)


def tus_bas(vk: int, ctrl: bool = True, alt: bool = True, basili_ms: int = 0) -> None:
    if ctrl: u32.keybd_event(VK_CONTROL, 0, 0, 0)
    if alt: u32.keybd_event(VK_MENU, 0, 0, 0)
    u32.keybd_event(vk, 0, 0, 0)
    if basili_ms: bekle(basili_ms)
    u32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
    if alt: u32.keybd_event(VK_MENU, 0, KEYEVENTF_KEYUP, 0)
    if ctrl: u32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)


class Filtre(QtCore.QAbstractNativeEventFilter):
    def __init__(self) -> None:
        super().__init__()
        self.olaylar: list[tuple[int, float]] = []
        self.patlat = False

    def nativeEventFilter(self, eventType: QtCore.QByteArray | bytes, message: int) -> tuple[bool, int]:  # type: ignore[override]
        msg = ctypes.wintypes.MSG.from_address(int(message))
        if msg.message == WM_HOTKEY:
            self.olaylar.append((int(msg.wParam), time.perf_counter()))
            if self.patlat:
                raise RuntimeError("handler istisnasi (U5)")
            return True, 0
        return False, 0


def main() -> int:
    app = QtWidgets.QApplication(sys.argv)
    f = Filtre(); app.installNativeEventFilter(f)
    # U7 bosluk
    bos = {}
    for kimlik, vk, ad in ((1, ord("T"), "Ctrl+Alt+T"), (2, ord("R"), "Ctrl+Alt+R")):
        ok = bool(u32.RegisterHotKey(None, kimlik, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, vk))
        bos[ad] = ok; olgu(f"U7 {ad} kayit={ok} (False ise baska uygulama tutuyor, hata={k32.GetLastError() if not ok else 0})")
    # U1 sentetik tus -> WM_HOTKEY + gecikme
    f.olaylar.clear(); t0 = time.perf_counter(); tus_bas(ord("T")); bekle(300)
    gec = (f.olaylar[0][1] - t0) * 1000 if f.olaylar else -1
    olgu(f"U1 Ctrl+Alt+T sentetik: WM_HOTKEY olay sayisi={len(f.olaylar)} id={[o[0] for o in f.olaylar]} gecikme={gec:.1f} ms")
    # U2 cakisma: ayni kombinasyon ikinci kez (ayni surec, farkli id)
    ok2 = bool(u32.RegisterHotKey(None, 9, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, ord("T"))); hata2 = k32.GetLastError()
    olgu(f"U2a ayni kombinasyon ikinci kayit: ok={ok2} GetLastError={hata2} (1409 = ERROR_HOTKEY_ALREADY_REGISTERED beklenir)")
    # U2b baska surec tutarken: cocuk surec Ctrl+Alt+Y'yi alsin, biz deneyelim
    cocuk = subprocess.Popen([sys.executable, "-c", "import ctypes,time; u=ctypes.windll.user32; print(u.RegisterHotKey(None,5,0x1|0x2|0x4000,ord('Y')), flush=True); time.sleep(6)"], stdout=subprocess.PIPE, text=True)
    cocuk_ok = cocuk.stdout.readline().strip() if cocuk.stdout else "?"
    ok3 = bool(u32.RegisterHotKey(None, 3, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, ord("Y"))); hata3 = k32.GetLastError()
    olgu(f"U2b baska surec Ctrl+Alt+Y tutarken ({cocuk_ok}): bizim kayit ok={ok3} GetLastError={hata3}")
    cocuk.kill()
    bekle(200)
    ok3b = bool(u32.RegisterHotKey(None, 3, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, ord("Y")))
    olgu(f"U2c diger surec olunce ayni kombinasyon: ok={ok3b}"); u32.UnregisterHotKey(None, 3)
    # U3 pencere yokken
    w = QtWidgets.QWidget(); w.show(); bekle(100); w.hide(); bekle(100)
    f.olaylar.clear(); tus_bas(ord("R")); bekle(300)
    olgu(f"U3 tum pencereler gizliyken Ctrl+Alt+R: olay={len(f.olaylar)} id={[o[0] for o in f.olaylar]}")
    # U6 basili tutma
    f.olaylar.clear(); tus_bas(ord("T"), basili_ms=700); bekle(300)
    olgu(f"U6 tus 700 ms basili (MOD_NOREPEAT): olay sayisi={len(f.olaylar)} (1 beklenir)")
    ok_nr = bool(u32.UnregisterHotKey(None, 1)) and bool(u32.RegisterHotKey(None, 1, MOD_CONTROL | MOD_ALT, ord("T")))
    f.olaylar.clear(); tus_bas(ord("T"), basili_ms=700); bekle(300)
    olgu(f"U6b NOREPEAT olmadan 700 ms basili: olay sayisi={len(f.olaylar)} (>1 beklenir: tekrar) kayit={ok_nr}")
    # U5 handler istisnasi
    f.patlat = True; f.olaylar.clear(); tus_bas(ord("T")); bekle(300); f.patlat = False
    olgu(f"U5 filtre icinde istisna: uygulama yasiyor=True olay kaydedildi={len(f.olaylar)} (istisna Qt tarafinda yutuldu mu: stderr'e bak)")
    # U4 unregister
    u32.UnregisterHotKey(None, 1); u32.UnregisterHotKey(None, 2)
    f.olaylar.clear(); tus_bas(ord("T")); bekle(300)
    olgu(f"U4 UnregisterHotKey sonrasi Ctrl+Alt+T: olay={len(f.olaylar)} (0 beklenir)")
    ok4 = bool(u32.RegisterHotKey(None, 1, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, ord("T")))
    f.olaylar.clear(); tus_bas(ord("T")); bekle(300)
    olgu(f"U4b yeniden kayit ok={ok4}, olay={len(f.olaylar)}")
    u32.UnregisterHotKey(None, 1)
    (CIKTI / "olgular.txt").write_text("T-013 ON OLCUM -- global kisayol (RegisterHotKey + Qt native event filter), gercek Windows\n\n" + "\n".join(satirlar) + "\n", encoding="utf-8")
    print("yazildi: olgular.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
