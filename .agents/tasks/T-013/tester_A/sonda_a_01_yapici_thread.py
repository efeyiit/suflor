"""Sonda A-01 (O-A3): `KisayolServisi` yapicisi thread denetlemez. Baska thread'de kurulup ana thread'den kullanilan servis:
`kaydet` OK doner ama `tetiklendi` sinyali olu thread'e kuyruklanir -> alici HIC kosmaz (sessiz kayip, K6'nin korudugu sinif);
yikim + olay dongusu bir kosumda erisim ihlali (0xC0000005) verdi. Ayri surecte kosulur; stdout ASCII.

    python .agents/tasks/T-013/tester_A/sonda_a_01_yapici_thread.py [ana]

`ana` verilirse pozitif kontrol: ayni akis, yapici ANA thread'de -> sinyal 1.
"""
from __future__ import annotations

import ctypes
import gc
import os
import sys
import threading
from ctypes import wintypes
from pathlib import Path

os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["SUFLOR_GERCEK_KISAYOL_YASAK"] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from PySide6.QtCore import QEventLoop, QTimer  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from src.ui.kisayol import WM_HOTKEY, KisayolServisi  # noqa: E402


def main() -> int:
    ana = len(sys.argv) > 1 and sys.argv[1] == "ana"
    app = QApplication([])
    u32 = ctypes.WinDLL("user32", use_last_error=True)
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    u32.PostThreadMessageW.argtypes = [wintypes.DWORD, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    tid = int(k32.GetCurrentThreadId())
    kayitlar: list[int] = []
    kutu: dict[str, object] = {}

    def kur() -> None:
        try:
            kutu["s"] = KisayolServisi(kayit_fn=lambda i, m, v: kayitlar.append(i) or True, kaldir_fn=lambda i: True,
                                       hata_kodu_fn=lambda: 0, altgr_karakteri_fn=lambda v: "")
            kutu["istisna"] = None
        except Exception as e:  # noqa: BLE001
            kutu["istisna"] = type(e).__name__

    if ana:
        kur()
    else:
        t = threading.Thread(target=kur)
        t.start()
        t.join()
    print(f"yapici_thread={'ana' if ana else 'baska'} yapici_istisna={kutu.get('istisna')}")
    s = kutu.get("s")
    if not isinstance(s, KisayolServisi):
        return 2
    alinan: list[str] = []
    s.tetiklendi.connect(alinan.append)
    print(f"kaydet={s.kaydet('a', 'Ctrl+Alt+D')} servis_thread_ana={s.thread() is app.thread()}")
    u32.PostThreadMessageW(tid, WM_HOTKEY, kayitlar[-1], 0)
    loop = QEventLoop()
    QTimer.singleShot(100, loop.quit)
    loop.exec()
    print(f"sinyal={len(alinan)}")
    s.hepsini_kaldir()
    del s
    kutu.clear()
    gc.collect()
    loop2 = QEventLoop()
    QTimer.singleShot(50, loop2.quit)
    loop2.exec()
    print("yikim_sonrasi_dongu=tamam")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
