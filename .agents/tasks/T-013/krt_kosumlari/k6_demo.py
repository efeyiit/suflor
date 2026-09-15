"""KRT k6 -- demo/kabuk.py + kisayol prototipi: Ctrl+Alt+R secim katmanini aciyor mu, katman odak aliyor mu, Esc kapatiyor mu;
Ctrl+Alt+T -> demo `anlik_cevir` -> pencere.goster() on plana gelebiliyor mu (foreground kilidi); tepsideyken de.

    python .agents/tasks/T-013/krt_kosumlari/k6_demo.py          (gercek ekran; ~12 s; katman Esc ile ya da dogrudan kapatilir)

Servis henuz yok: KRT'nin kendi minimal filtresi WM_HOTKEY -> pencere sinyali yayar; gerisi demonun `_bagla`si.
Stdout ASCII.
"""
from __future__ import annotations

import ctypes
import sys
import time
from ctypes import wintypes
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(KOK))

from PySide6 import QtCore, QtWidgets  # noqa: E402

u32 = ctypes.windll.user32
k32 = ctypes.windll.kernel32
WM_HOTKEY = 0x0312
MOD_ALT, MOD_CONTROL, MOD_NOREPEAT = 0x1, 0x2, 0x4000
VK_CONTROL, VK_MENU, VK_ESCAPE, KEYUP = 0x11, 0x12, 0x1B, 0x2
u32.GetForegroundWindow.restype = wintypes.HWND
satir: list[str] = []


def olgu(m: str) -> None:
    satir.append(m); print("  " + m, flush=True)


def tus(vk: int, ctrl: bool = True, alt: bool = True) -> None:
    if ctrl: u32.keybd_event(VK_CONTROL, 0, 0, 0)
    if alt: u32.keybd_event(VK_MENU, 0, 0, 0)
    u32.keybd_event(vk, 0, 0, 0); u32.keybd_event(vk, 0, KEYUP, 0)
    if alt: u32.keybd_event(VK_MENU, 0, KEYUP, 0)
    if ctrl: u32.keybd_event(VK_CONTROL, 0, KEYUP, 0)


def on_plan() -> tuple[int, str]:
    h = u32.GetForegroundWindow(); buf = ctypes.create_unicode_buffer(128); u32.GetClassNameW(h, buf, 128); return int(h or 0), buf.value


def katmanlar() -> list[QtWidgets.QWidget]:
    return [w for w in QtWidgets.QApplication.topLevelWidgets() if type(w).__name__ == "SecimKatmani" and w.isVisible()]


class Filtre(QtCore.QAbstractNativeEventFilter):
    def __init__(self, pencere: QtWidgets.QWidget) -> None:
        super().__init__(); self.p = pencere; self.n = 0

    def nativeEventFilter(self, eventType, message):  # type: ignore[override]
        msg = wintypes.MSG.from_address(int(message))
        if msg.message == WM_HOTKEY:
            self.n += 1
            if msg.wParam == 1: self.p.anlik_cevir_istendi.emit()
            elif msg.wParam == 2: self.p.bolge_izle_istendi.emit()
            return True, 0
        return False, 0


def main() -> int:
    from demo.kabuk import _bagla
    from src.ui.kabuk import AnaPencere, KabukDurumu
    from src.ui.uygulama import calistir

    durum: dict[str, object] = {}

    def calistirici(app: QtWidgets.QApplication, pencere: AnaPencere) -> int:
        f = Filtre(pencere); app.installNativeEventFilter(f); durum["f"] = f
        ok1 = bool(u32.RegisterHotKey(None, 1, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, ord("T")))
        ok2 = bool(u32.RegisterHotKey(None, 2, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, ord("R")))
        olgu(f"kurulum: Ctrl+Alt+T kayit={ok1} Ctrl+Alt+R kayit={ok2} pencere hwnd={int(pencere.winId())}")
        sayac = {"bolge": 0, "anlik": 0, "iptal": 0}
        pencere.bolge_izle_istendi.connect(lambda: sayac.__setitem__("bolge", sayac["bolge"] + 1))
        pencere.anlik_cevir_istendi.connect(lambda: sayac.__setitem__("anlik", sayac["anlik"] + 1))
        T = QtCore.QTimer.singleShot

        def adim1() -> None:  # on plan baska pencere (terminal) iken Ctrl+Alt+R
            h, cls = on_plan(); olgu(f"adim1 on plan class={cls} (bizim pencere mi={h == int(pencere.winId())}); Ctrl+Alt+R gonderiliyor")
            tus(ord("R"))

        def adim2() -> None:
            ks = katmanlar(); h, cls = on_plan()
            olgu(f"adim2 (1 s sonra) bolge_izle_istendi={sayac['bolge']} gorunur SecimKatmani={len(ks)} sekme gizli={not pencere.sekme.isVisible()} on plan katman={bool(ks) and h == int(ks[0].winId())} (class={cls})")
            for k in ks: k.iptal.connect(lambda: sayac.__setitem__("iptal", sayac["iptal"] + 1))

        def adim3() -> None:  # Esc
            olgu("adim3 (5 s) Esc gonderiliyor"); u32.keybd_event(VK_ESCAPE, 0, 0, 0); u32.keybd_event(VK_ESCAPE, 0, KEYUP, 0)

        def adim4() -> None:
            ks = katmanlar(); olgu(f"adim4 Esc sonrasi: iptal={sayac['iptal']} gorunur katman={len(ks)} (0 beklenir; Esc katmana ulasmadiysa katman ACIK KALIR)")
            for k in ks: olgu("adim4 katman dogrudan kapatiliyor (temizlik)"); k.close()

        def adim5() -> None:  # Ctrl+Alt+T -> demo anlik_cevir -> pencere.goster()
            pencere.tepsiye_al(); QtCore.QTimer.singleShot(400, lambda: (olgu(f"adim5 tepsi durumu={pencere.durum} on plan class={on_plan()[1]}; Ctrl+Alt+T gonderiliyor"), tus(ord("T"))))

        def adim6() -> None:
            h, cls = on_plan()
            olgu(f"adim6 Ctrl+Alt+T sonrasi: anlik_cevir_istendi={sayac['anlik']} durum={pencere.durum} pencere gorunur={pencere.isVisible()} on plan bizim pencere={h == int(pencere.winId())} (class={cls}) -- demo goster() cagiriyor; foreground kilidi?")

        def adim7() -> None:  # tepsideyken Ctrl+Alt+R -> katman
            pencere.tepsiye_al(); QtCore.QTimer.singleShot(400, lambda: tus(ord("R")))

        def adim8() -> None:
            ks = katmanlar(); h, cls = on_plan()
            olgu(f"adim8 tepsideyken Ctrl+Alt+R: bolge_izle_istendi={sayac['bolge']} katman={len(ks)} durum={pencere.durum} on plan katman={bool(ks) and h == int(ks[0].winId())}")
            for k in ks: k.close()

        def son() -> None:
            olgu(f"son: WM_HOTKEY toplam={f.n}; kapat()"); u32.UnregisterHotKey(None, 1); u32.UnregisterHotKey(None, 2); pencere.kapat()

        T(800, adim1); T(1800, adim2); T(5000, adim3); T(5600, adim4); T(6200, adim5); T(7400, adim6); T(8000, adim7); T(9200, adim8); T(10000, son)
        return _bagla(app, pencere)

    rc = calistir([], calistirici=calistirici)
    print(f"exec donus={rc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
