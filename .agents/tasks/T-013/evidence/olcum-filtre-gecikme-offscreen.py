"""T-013 K2 gecikme olcumu -- OFFSCREEN, sahte Win32, GERCEK `ctypes.wintypes.MSG` yapisi (kayit YOK).

    python .agents/tasks/T-013/evidence/olcum-filtre-gecikme-offscreen.py

Olculen: `nativeEventFilter(b"windows_generic_MSG", addressof(MSG{WM_HOTKEY, wParam=id}))` cagrisindan
`tetiklendi(ad)` alicisina kadar gecen sure (dogrudan cagri; Qt dagiticisi ve Windows kuyrugu DAHIL DEGIL --
o kisim `real_check` [1a]: 1.6 ms). g1 1000 bilinen kimlik; g2 1000 bilinmeyen kimlik (sinyal yok, `False`);
g3 1000 yanlis eventType (mesaja dokunmadan `False`); g4 iki servis kuruluyken eski servisin filtresi yeni
kimligi gorunce `False` (KRT p2 sirasi). Stdout ASCII; medyan/max mikrosaniye.
"""
from __future__ import annotations

import ctypes
import os
import statistics
import sys
import time
from ctypes import wintypes

os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ.setdefault("SUFLOR_GERCEK_KISAYOL_YASAK", "1")
sys.path.insert(0, os.getcwd())

from PySide6 import QtWidgets  # noqa: E402

from src.ui.kisayol import WM_HOTKEY, KisayolServisi  # noqa: E402


class Sahte:
    def __init__(self) -> None:
        self.idler: list[int] = []

    def kayit(self, kimlik: int, mod: int, vk: int) -> bool:
        self.idler.append(kimlik)
        return True

    def kaldir(self, kimlik: int) -> bool:
        return True

    def hata(self) -> int:
        return 0

    def altgr(self, vk: int) -> str:
        return ""

    def servis(self) -> KisayolServisi:
        return KisayolServisi(None, kayit_fn=self.kayit, kaldir_fn=self.kaldir, hata_kodu_fn=self.hata, altgr_karakteri_fn=self.altgr)


def olc(ad: str, n: int, cagri: "object", beklenen_sinyal: int, alinan: list[float]) -> None:
    sureler: list[float] = []
    alinan.clear()
    for _ in range(n):
        t0 = time.perf_counter()
        cagri()  # type: ignore[operator]
        t1 = alinan[-1] if alinan and alinan[-1] >= t0 else time.perf_counter()
        sureler.append((t1 - t0) * 1e6)
    print(f"{ad}: n={n} sinyal={len(alinan)} (beklenen {beklenen_sinyal}) medyan={statistics.median(sureler):.1f} us max={max(sureler):.1f} us")


def main() -> int:
    app = QtWidgets.QApplication(sys.argv)
    sahte = Sahte()
    s = sahte.servis()
    alinan: list[float] = []
    s.tetiklendi.connect(lambda ad: alinan.append(time.perf_counter()))
    s.kaydet("anlik_cevir", "Ctrl+Alt+D")
    kimlik = sahte.idler[0]
    m_bilinen = wintypes.MSG(); m_bilinen.message = WM_HOTKEY; m_bilinen.wParam = kimlik
    m_bilinmeyen = wintypes.MSG(); m_bilinmeyen.message = WM_HOTKEY; m_bilinmeyen.wParam = kimlik + 7
    a_bilinen, a_bilinmeyen = ctypes.addressof(m_bilinen), ctypes.addressof(m_bilinmeyen)
    olc("g1 bilinen kimlik -> tetiklendi", 1000, lambda: s.filtre.nativeEventFilter(b"windows_generic_MSG", a_bilinen), 1000, alinan)
    olc("g2 bilinmeyen kimlik -> False", 1000, lambda: s.filtre.nativeEventFilter(b"windows_generic_MSG", a_bilinmeyen), 0, alinan)
    olc("g3 yanlis eventType -> False (mesaja dokunmaz)", 1000, lambda: s.filtre.nativeEventFilter(b"xcb_generic_event_t", a_bilinen), 0, alinan)
    s2 = sahte.servis()
    s2.kaydet("anlik_cevir", "Ctrl+Alt+F")
    kimlik2 = sahte.idler[1]
    m2 = wintypes.MSG(); m2.message = WM_HOTKEY; m2.wParam = kimlik2
    a2 = ctypes.addressof(m2)
    olc("g4 eski servis, yeni servisin kimligi -> False", 1000, lambda: s.filtre.nativeEventFilter(b"windows_generic_MSG", a2), 0, alinan)
    print(f"dagitici={type(app.eventDispatcher()).__name__} platform={app.platformName()} kayit_fn cagrisi={len(sahte.idler)} (sahte; gercek RegisterHotKey YOK)")
    s.hepsini_kaldir(); s2.hepsini_kaldir()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
