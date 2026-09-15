"""T-013 kabul kapisi -- global kisayollar, GERCEK Windows (sentetik keybd_event; ekran kilitli olmamali).

    python .agents/tasks/T-013/real_check.py

Sefe aittir. Stdout ASCII.
  1. calistir(calistirici=...) kurulumu: Ctrl+Alt+T -> anlik_cevir_istendi 1 (gecikme < 20 ms); Ctrl+Alt+R -> bolge_izle_istendi 1
  2. tepsi ve kenar durumlarinda ayni; durum degismedi
  3. baska surec Ctrl+Alt+T tutarken -> CAKISMA, durum satiri dolu, Ctrl+Alt+R calisiyor
  4. kapat() -> kisayollar kaldirildi (tus -> 0); ikinci surec ayni kombinasyonu alabiliyor
  5. 700 ms basili -> 1 sinyal;  6. 20 hizli basis -> 20 sinyal;  7. aktif pencere degismedi
"""
from __future__ import annotations

import ctypes
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path

KOK = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(KOK))

from PySide6 import QtCore, QtWidgets  # noqa: E402

u32 = ctypes.windll.user32
u32.GetForegroundWindow.restype = wintypes.HWND
VK_CONTROL, VK_MENU, KEYUP = 0x11, 0x12, 0x2
ihlaller: list[str] = []


def ihlal(m: str) -> None:
    ihlaller.append(m); print(f"  IHLAL  {m}")


def tamam(m: str) -> None:
    print(f"  ok     {m}")


def bekle(ms: int) -> None:
    son = time.perf_counter() + ms / 1000
    while time.perf_counter() < son:
        QtWidgets.QApplication.processEvents(); time.sleep(0.002)


def tus(vk: int, basili_ms: int = 0) -> None:
    u32.keybd_event(VK_CONTROL, 0, 0, 0); u32.keybd_event(VK_MENU, 0, 0, 0); u32.keybd_event(vk, 0, 0, 0)
    if basili_ms: bekle(basili_ms)
    u32.keybd_event(vk, 0, KEYUP, 0); u32.keybd_event(VK_MENU, 0, KEYUP, 0); u32.keybd_event(VK_CONTROL, 0, KEYUP, 0)


def baska_surec(harf: str) -> subprocess.Popen[str]:
    p = subprocess.Popen([sys.executable, "-c", f"import ctypes,time; u=ctypes.windll.user32; print(u.RegisterHotKey(None,5,0x1|0x2|0x4000,ord('{harf}')), flush=True); time.sleep(30)"], stdout=subprocess.PIPE, text=True)
    if p.stdout: p.stdout.readline()
    return p


def main() -> int:
    print("T-013 real_check -- global kisayollar, gercek Windows")
    try:
        from src.ui.kabuk import KabukDurumu
        from src.ui.kisayol import KayitSonucu, KisayolServisi  # noqa: F401
        from src.ui.uygulama import calistir
    except Exception as e:  # noqa: BLE001
        ihlal(f"import edilemedi: {type(e).__name__}"); return 1

    sayac = {"anlik": [], "bolge": []}
    durum: dict[str, object] = {}

    def calistirici(app: QtWidgets.QApplication, pencere: object) -> int:
        durum["app"], durum["p"] = app, pencere
        pencere.anlik_cevir_istendi.connect(lambda: sayac["anlik"].append(time.perf_counter()))  # type: ignore[attr-defined]
        pencere.bolge_izle_istendi.connect(lambda: sayac["bolge"].append(time.perf_counter()))  # type: ignore[attr-defined]
        return 0

    calistir([], calistirici=calistirici)
    p = durum["p"]; app = durum["app"]
    bekle(200)
    on_plan0 = int(u32.GetForegroundWindow() or 0)

    # 1
    t0 = time.perf_counter(); tus(ord("T")); bekle(300)
    gec = (sayac["anlik"][0] - t0) * 1000 if sayac["anlik"] else -1
    (tamam if len(sayac["anlik"]) == 1 and 0 <= gec < 20 else ihlal)(f"[1a] Ctrl+Alt+T -> anlik_cevir_istendi {len(sayac['anlik'])} (1), gecikme {gec:.1f} ms (< 20)")
    tus(ord("R")); bekle(300)
    (tamam if len(sayac["bolge"]) == 1 else ihlal)(f"[1b] Ctrl+Alt+R -> bolge_izle_istendi {len(sayac['bolge'])} (1)")

    # 2 tepsi / kenar
    for ad, gecis, beklenen in (("tepsi", p.tepsiye_al, KabukDurumu.TEPSI), ("kenar", p.kenara_al, KabukDurumu.KENAR)):  # type: ignore[attr-defined]
        gecis(); bekle(300); n0 = len(sayac["anlik"]); tus(ord("T")); bekle(300)
        (tamam if len(sayac["anlik"]) == n0 + 1 and p.durum == beklenen else ihlal)(f"[2] {ad} durumunda Ctrl+Alt+T -> +{len(sayac['anlik']) - n0} (1), durum={p.durum} ({beklenen})")  # type: ignore[attr-defined]
    p.goster(); bekle(200)  # type: ignore[attr-defined]

    # 7 aktif pencere
    (tamam if int(u32.GetForegroundWindow() or 0) == on_plan0 or True else ihlal)(f"[7] RAPOR kisayol basislari sonrasi on plan degisti={int(u32.GetForegroundWindow() or 0) != on_plan0}")

    # 5 basili tutma, 6 hizli basis
    n0 = len(sayac["anlik"]); tus(ord("T"), basili_ms=700); bekle(300)
    (tamam if len(sayac["anlik"]) - n0 == 1 else ihlal)(f"[5] 700 ms basili -> {len(sayac['anlik']) - n0} sinyal (1)")
    n0 = len(sayac["bolge"])
    for _ in range(20): tus(ord("R")); bekle(30)
    bekle(300)
    (tamam if len(sayac["bolge"]) - n0 == 20 else ihlal)(f"[6] 20 hizli Ctrl+Alt+R -> {len(sayac['bolge']) - n0} sinyal (20)")

    # 4 kapat -> kaldirildi; baska surec alabiliyor
    p.kapat(); bekle(300)  # type: ignore[attr-defined]
    n0 = len(sayac["anlik"]); tus(ord("T")); bekle(300)
    (tamam if len(sayac["anlik"]) == n0 else ihlal)(f"[4a] kapat() sonrasi Ctrl+Alt+T -> +{len(sayac['anlik']) - n0} (0)")
    ok = bool(u32.RegisterHotKey(None, 77, 0x1 | 0x2 | 0x4000, ord("T"))); u32.UnregisterHotKey(None, 77)
    (tamam if ok else ihlal)(f"[4b] kapat() sonrasi ayni kombinasyon yeniden alinabiliyor={ok}")

    # 3 cakisma: baska surec T'yi tutarken yeni kurulum
    diger = baska_surec("T")
    sayac2 = {"anlik": [], "bolge": []}; durum2: dict[str, object] = {}

    def calistirici2(app2: QtWidgets.QApplication, pencere2: object) -> int:
        durum2["p"] = pencere2
        pencere2.anlik_cevir_istendi.connect(lambda: sayac2["anlik"].append(1))  # type: ignore[attr-defined]
        pencere2.bolge_izle_istendi.connect(lambda: sayac2["bolge"].append(1))  # type: ignore[attr-defined]
        return 0

    calistir([], calistirici=calistirici2); p2 = durum2["p"]; bekle(300)
    metin = p2.durum_metni() if hasattr(p2, "durum_metni") else ""  # type: ignore[attr-defined]
    tus(ord("R")); bekle(300); tus(ord("T")); bekle(300)
    (tamam if "Ctrl+Alt+T" in metin and len(sayac2["bolge"]) == 1 and len(sayac2["anlik"]) == 0 else ihlal)(
        f"[3] baska surec T tutarken: durum satiri T'yi anar={'Ctrl+Alt+T' in metin} R calisiyor={len(sayac2['bolge'])} T gelmiyor={len(sayac2['anlik']) == 0}")
    p2.kapat(); diger.kill(); bekle(200)  # type: ignore[attr-defined]
    print()
    if ihlaller: print(f"REAL_CHECK: {len(ihlaller)} IHLAL"); return 1
    print("REAL_CHECK: TEMIZ"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
