"""T-013 kabul kapisi v2 -- global kisayollar, GERCEK Windows (sentetik keybd_event; ekran kilitli olmamali).

    python .agents/tasks/T-013/real_check.py

Sefe aittir. Stdout ASCII. Kayitli kombinasyonlar Ctrl+Alt+D (anlik) ve Ctrl+Alt+R (bolge) -- TR-Q'da AltGr'de bos.
  1. calistir(calistirici=...) gercek servis: Ctrl+Alt+D -> anlik_cevir_istendi 1 (< 20 ms); Ctrl+Alt+R -> bolge_izle_istendi 1
  2. tepsi ve kenar durumlarinda ayni; durum degismedi
  3. baska surec Ctrl+Alt+D tutarken -> durum satiri D + "baska bir uygulama", R calisiyor, dugme etiketi "(kisayol yok)"
  4. kapat() -> sinyal 0; ayni kombinasyon yeniden alinabiliyor
  5. pozitif kontrollu tekrar: 5 DOWN (UP'siz) -> NOREPEAT 1 / NOREPEAT'siz 5
  6. 20 hizli basis -> 20
  7. RAPOR: on plan hwnd ve menu modu degismedi
  8. altgr_karakteri: T -> '₺' (TR-Q) ya da bos (baska duzen); D -> ''; kaydet(Ctrl+Alt+T) -> ALTGR_CAKISMA (T doluysa)
  9. del+gc: servis dusurulunce Ctrl+Alt+D yeniden alinabiliyor
"""
from __future__ import annotations

import ctypes
import gc
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path

KOK = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(KOK))

from PySide6 import QtWidgets  # noqa: E402

u32 = ctypes.windll.user32
u32.GetForegroundWindow.restype = wintypes.HWND
VK_CONTROL, VK_MENU, KEYUP = 0x11, 0x12, 0x2
MOD_CA, MOD_NOREPEAT = 0x1 | 0x2, 0x4000
GUI_INMENUMODE = 0x4
ihlaller: list[str] = []


class _GUITHREADINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("flags", wintypes.DWORD), ("hwndActive", wintypes.HWND), ("hwndFocus", wintypes.HWND),
                ("hwndCapture", wintypes.HWND), ("hwndMenuOwner", wintypes.HWND), ("hwndMoveSize", wintypes.HWND), ("hwndCaret", wintypes.HWND),
                ("rcCaret", wintypes.RECT)]


def menu_modu() -> bool:
    g = _GUITHREADINFO(); g.cbSize = ctypes.sizeof(_GUITHREADINFO)
    return bool(u32.GetGUIThreadInfo(0, ctypes.byref(g))) and bool(g.flags & GUI_INMENUMODE)


def ihlal(m: str) -> None:
    ihlaller.append(m); print(f"  IHLAL  {m}")


def tamam(m: str) -> None:
    print(f"  ok     {m}")


def bekle(ms: int) -> None:
    son = time.perf_counter() + ms / 1000
    while time.perf_counter() < son:
        QtWidgets.QApplication.processEvents(); time.sleep(0.002)


def tus(vk: int) -> None:
    u32.keybd_event(VK_CONTROL, 0, 0, 0); u32.keybd_event(VK_MENU, 0, 0, 0); u32.keybd_event(vk, 0, 0, 0)
    u32.keybd_event(vk, 0, KEYUP, 0); u32.keybd_event(VK_MENU, 0, KEYUP, 0); u32.keybd_event(VK_CONTROL, 0, KEYUP, 0)


def tus_5_down(vk: int) -> None:
    u32.keybd_event(VK_CONTROL, 0, 0, 0); u32.keybd_event(VK_MENU, 0, 0, 0)
    for _ in range(5): u32.keybd_event(vk, 0, 0, 0); bekle(40)
    u32.keybd_event(vk, 0, KEYUP, 0); u32.keybd_event(VK_MENU, 0, KEYUP, 0); u32.keybd_event(VK_CONTROL, 0, KEYUP, 0)


def baska_surec(harf: str) -> subprocess.Popen[str]:
    p = subprocess.Popen([sys.executable, "-c", f"import ctypes,time; u=ctypes.windll.user32; print(u.RegisterHotKey(None,5,0x1|0x2|0x4000,ord('{harf}')), flush=True); time.sleep(30)"], stdout=subprocess.PIPE, text=True)
    if p.stdout: p.stdout.readline()
    return p


def main() -> int:
    print("T-013 real_check v2 -- global kisayollar, gercek Windows")
    try:
        from src.ui.kabuk import KabukDurumu
        from src.ui.kisayol import KayitSonucu, KisayolServisi, altgr_karakteri
        from src.ui.uygulama import calistir
    except Exception as e:  # noqa: BLE001
        ihlal(f"import edilemedi: {type(e).__name__}"); return 1
    diger: subprocess.Popen[str] | None = None
    try:
        sayac: dict[str, list[float]] = {"anlik": [], "bolge": []}
        durum: dict[str, object] = {}

        def calistirici(app: QtWidgets.QApplication, pencere: object) -> int:
            durum["app"], durum["p"] = app, pencere
            pencere.anlik_cevir_istendi.connect(lambda: sayac["anlik"].append(time.perf_counter()))  # type: ignore[attr-defined]
            pencere.bolge_izle_istendi.connect(lambda: sayac["bolge"].append(time.perf_counter()))  # type: ignore[attr-defined]
            return 0

        calistir([], calistirici=calistirici); p = durum["p"]; bekle(200)
        on_plan0 = int(u32.GetForegroundWindow() or 0); menu0 = menu_modu()

        # 1
        t0 = time.perf_counter(); tus(ord("D")); bekle(300)
        gec = (sayac["anlik"][0] - t0) * 1000 if sayac["anlik"] else -1
        (tamam if len(sayac["anlik"]) == 1 and 0 <= gec < 20 else ihlal)(f"[1a] Ctrl+Alt+D -> anlik_cevir_istendi {len(sayac['anlik'])} (1), gecikme {gec:.1f} ms (< 20)")
        tus(ord("R")); bekle(300)
        (tamam if len(sayac["bolge"]) == 1 else ihlal)(f"[1b] Ctrl+Alt+R -> bolge_izle_istendi {len(sayac['bolge'])} (1)")

        # 2
        for ad, gecis, beklenen in (("tepsi", p.tepsiye_al, KabukDurumu.TEPSI), ("kenar", p.kenara_al, KabukDurumu.KENAR)):  # type: ignore[attr-defined]
            gecis(); bekle(300); n0 = len(sayac["anlik"]); tus(ord("D")); bekle(300)
            (tamam if len(sayac["anlik"]) == n0 + 1 and p.durum == beklenen else ihlal)(f"[2] {ad} durumunda Ctrl+Alt+D -> +{len(sayac['anlik']) - n0} (1), durum={p.durum} ({beklenen})")  # type: ignore[attr-defined]
        p.goster(); bekle(200)  # type: ignore[attr-defined]

        # 7 rapor
        tamam(f"[7] RAPOR on plan degisti={int(u32.GetForegroundWindow() or 0) != on_plan0} menu modu once/sonra={menu0}/{menu_modu()}")

        # 5 pozitif kontrollu tekrar
        n0 = len(sayac["anlik"]); tus_5_down(ord("D")); bekle(300)
        norepeat = len(sayac["anlik"]) - n0
        tekrar_olay: list[int] = []
        ok_t = bool(u32.RegisterHotKey(None, 0xBFF0, MOD_CA, ord("X")))   # NOREPEAT'siz gecici kayit (X: TR-Q AltGr bos)

        class _F(__import__("PySide6").QtCore.QAbstractNativeEventFilter):
            def nativeEventFilter(self, t: object, m: int) -> tuple[bool, int]:  # type: ignore[override]
                msg = wintypes.MSG.from_address(int(m))
                if msg.message == 0x0312 and int(msg.wParam) == 0xBFF0: tekrar_olay.append(1); return True, 0
                return False, 0

        f = _F(); app = durum["app"]; app.installNativeEventFilter(f)  # type: ignore[attr-defined]
        tus_5_down(ord("X")); bekle(300); app.removeNativeEventFilter(f); u32.UnregisterHotKey(None, 0xBFF0)  # type: ignore[attr-defined]
        (tamam if norepeat == 1 and ok_t and len(tekrar_olay) >= 2 else ihlal)(f"[5] 5 DOWN: NOREPEAT'li {norepeat} (1) / NOREPEAT'siz gecici kayit {len(tekrar_olay)} (>= 2, pozitif kontrol; kayit={ok_t})")

        # 6
        n0 = len(sayac["bolge"])
        for _ in range(20): tus(ord("R")); bekle(30)
        bekle(300)
        (tamam if len(sayac["bolge"]) - n0 == 20 else ihlal)(f"[6] 20 hizli Ctrl+Alt+R -> {len(sayac['bolge']) - n0} sinyal (20)")

        # 8 AltGr
        t_kar = altgr_karakteri(ord("T")); d_kar = altgr_karakteri(ord("D"))
        s_gecici = KisayolServisi(gercek_win32=True)
        sonuc_t = s_gecici.kaydet("deneme", "Ctrl+Alt+T"); s_gecici.hepsini_kaldir()
        beklenen = KayitSonucu.ALTGR_CAKISMA if t_kar else KayitSonucu.OK
        (tamam if d_kar == "" and sonuc_t == beklenen else ihlal)(f"[8] altgr: T karakter var={bool(t_kar)} (TR-Q'da evet) D bos={d_kar == ''}; kaydet(Ctrl+Alt+T)={sonuc_t} (beklenen {beklenen})")

        # 4 kapat
        p.kapat(); bekle(300)  # type: ignore[attr-defined]
        n0 = len(sayac["anlik"]); tus(ord("D")); bekle(300)
        (tamam if len(sayac["anlik"]) == n0 else ihlal)(f"[4a] kapat() sonrasi Ctrl+Alt+D -> +{len(sayac['anlik']) - n0} (0)")
        ok = bool(u32.RegisterHotKey(None, 0xBFF1, MOD_CA | MOD_NOREPEAT, ord("D"))); u32.UnregisterHotKey(None, 0xBFF1)
        (tamam if ok else ihlal)(f"[4b] kapat() sonrasi ayni kombinasyon yeniden alinabiliyor={ok}")

        # 9 del+gc
        s9 = KisayolServisi(gercek_win32=True); r9 = s9.kaydet("d", "Ctrl+Alt+D")
        del s9; gc.collect(); bekle(100)
        ok9 = bool(u32.RegisterHotKey(None, 0xBFF2, MOD_CA | MOD_NOREPEAT, ord("D"))); u32.UnregisterHotKey(None, 0xBFF2)
        (tamam if r9 == KayitSonucu.OK and ok9 else ihlal)(f"[9] del+gc sonrasi Ctrl+Alt+D yeniden alinabiliyor={ok9} (kayit={r9})")

        # 3 cakisma (baska surec D tutarken yeni kurulum)
        diger = baska_surec("D")
        sayac2: dict[str, list[int]] = {"anlik": [], "bolge": []}; durum2: dict[str, object] = {}

        def calistirici2(app2: QtWidgets.QApplication, pencere2: object) -> int:
            durum2["p"] = pencere2
            pencere2.anlik_cevir_istendi.connect(lambda: sayac2["anlik"].append(1))  # type: ignore[attr-defined]
            pencere2.bolge_izle_istendi.connect(lambda: sayac2["bolge"].append(1))  # type: ignore[attr-defined]
            return 0

        calistir([], calistirici=calistirici2); p2 = durum2["p"]; bekle(300)
        metin = p2.durum_metni()  # type: ignore[attr-defined]
        etiket = p2.dugme_anlik.text()  # type: ignore[attr-defined]
        tus(ord("R")); bekle(300); tus(ord("D")); bekle(300)
        (tamam if "Ctrl+Alt+D" in metin and "ba" in metin.lower() and len(sayac2["bolge"]) == 1 and len(sayac2["anlik"]) == 0 and "yok" in etiket.lower() else ihlal)(
            f"[3] baska surec D tutarken: durum satiri D'yi anar={'Ctrl+Alt+D' in metin} R calisiyor={len(sayac2['bolge'])} D gelmiyor={len(sayac2['anlik']) == 0} etiket 'kisayol yok'={'yok' in etiket.lower()}")
        p2.kapat(); bekle(200)  # type: ignore[attr-defined]
    finally:
        if diger is not None: diger.kill()
    print()
    if ihlaller: print(f"REAL_CHECK: {len(ihlaller)} IHLAL"); return 1
    print("REAL_CHECK: TEMIZ"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
