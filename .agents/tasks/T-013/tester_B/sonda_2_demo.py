"""T-013 Tester-B sonda 2 -- kullanici istegi 'arka planda calisirken kisayol': demo/kabuk.py GERCEK cagiran, gercek ekran.

    python .agents/tasks/T-013/tester_B/sonda_2_demo.py

Bolum A (surec ici, urunun servisiyle: `calistir(calistirici=_bagla sarmali)` -- demo/kabuk.py `main()` ile ayni yol):
  A1 gorunurken Ctrl+Alt+R -> SecimKatmani gorunur + on planda; Esc -> kapanir, iptal 1
  A2 tepsiye al; on plan baska pencere; Ctrl+Alt+R -> katman; Esc; Ctrl+Alt+D -> pencere geri + on planda (demo goster())
  A3 kenara al; Ctrl+Alt+D -> pencere geri, sekme gizli
  A4 dugme etiketleri / tepsi ipucu kayitli kombinasyonu gosteriyor
  A5 kapat() -> exec donus 0, D/R serbest
Bolum B (KARA KUTU: `python demo/kabuk.py` ayri surec; pencere EnumWindows ile bulunur):
  B1 Ctrl+Alt+R -> surecte yeni gorunur ust-duzey pencere (katman); Esc -> gider
  B2 tepsi dugmesine tik (PostMessage WM_LBUTTONDOWN/UP; olmazsa gercek fare) -> pencere gizli
  B3 tepsideyken Ctrl+Alt+R -> katman; Esc; Ctrl+Alt+D -> pencere gorunur + on planda
  B4 WM_CLOSE -> surec cikis 0; D/R serbest
Stdout ASCII.
"""
from __future__ import annotations

import ctypes
import os
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path

os.environ.pop("SUFLOR_GERCEK_KISAYOL_YASAK", None)
KOK = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(KOK))

from PySide6 import QtCore, QtWidgets  # noqa: E402

u32 = ctypes.windll.user32
k32 = ctypes.windll.kernel32
u32.GetForegroundWindow.restype = wintypes.HWND
VK_CONTROL, VK_MENU, VK_ESCAPE, KEYUP = 0x11, 0x12, 0x1B, 0x2
MOD_NOREPEAT, CA = 0x4000, 0x3
WM_CLOSE, WM_LBUTTONDOWN, WM_LBUTTONUP, WM_MOUSEMOVE, MK_LBUTTON = 0x0010, 0x0201, 0x0202, 0x0200, 0x0001
ihlaller: list[str] = []
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)


def olgu(m: str, ok: bool | None = None) -> None:
    on = "  " if ok is None else ("  ok     " if ok else "  IHLAL  ")
    print(on + m, flush=True)
    if ok is False:
        ihlaller.append(m)


def bekle(ms: int) -> None:
    son = time.perf_counter() + ms / 1000
    while time.perf_counter() < son:
        QtWidgets.QApplication.processEvents()
        time.sleep(0.002)


def uyu(ms: int) -> None:
    time.sleep(ms / 1000)


def tus(vk: int) -> None:
    u32.keybd_event(VK_CONTROL, 0, 0, 0)
    u32.keybd_event(VK_MENU, 0, 0, 0)
    u32.keybd_event(vk, 0, 0, 0)
    u32.keybd_event(vk, 0, KEYUP, 0)
    u32.keybd_event(VK_MENU, 0, KEYUP, 0)
    u32.keybd_event(VK_CONTROL, 0, KEYUP, 0)


def esc() -> None:
    u32.keybd_event(VK_ESCAPE, 0, 0, 0)
    u32.keybd_event(VK_ESCAPE, 0, KEYUP, 0)


def bos_mu(vk: int) -> bool:
    ok = bool(u32.RegisterHotKey(None, 0xBFE1, CA | MOD_NOREPEAT, vk))
    if ok:
        u32.UnregisterHotKey(None, 0xBFE1)
    return ok


def on_plan() -> tuple[int, str]:
    h = u32.GetForegroundWindow()
    buf = ctypes.create_unicode_buffer(128)
    u32.GetClassNameW(h, buf, 128)
    return int(h or 0), buf.value


def pencereler(pid: int) -> list[tuple[int, str, str]]:
    sonuc: list[tuple[int, str, str]] = []

    def cb(h: int, _: int) -> bool:
        p = wintypes.DWORD()
        u32.GetWindowThreadProcessId(h, ctypes.byref(p))
        if p.value == pid and u32.IsWindowVisible(h):
            b = ctypes.create_unicode_buffer(256)
            u32.GetWindowTextW(h, b, 256)
            c = ctypes.create_unicode_buffer(128)
            u32.GetClassNameW(h, c, 128)
            sonuc.append((int(h), b.value, c.value))
        return True

    u32.EnumWindows(EnumWindowsProc(cb), 0)
    return sonuc


def katmanlar() -> list[QtWidgets.QWidget]:
    return [w for w in QtWidgets.QApplication.topLevelWidgets() if type(w).__name__ == "SecimKatmani" and w.isVisible()]


def bolum_a() -> dict[str, object]:
    from demo.kabuk import _bagla
    from src.ui.kabuk import AnaPencere, KabukDurumu
    from src.ui.uygulama import calistir

    bilgi: dict[str, object] = {}

    def calistirici(app: QtWidgets.QApplication, pencere: AnaPencere) -> int:
        sayac = {"bolge": 0, "anlik": 0, "iptal": 0}
        pencere.bolge_izle_istendi.connect(lambda: sayac.__setitem__("bolge", sayac["bolge"] + 1))
        pencere.anlik_cevir_istendi.connect(lambda: sayac.__setitem__("anlik", sayac["anlik"] + 1))
        T = QtCore.QTimer.singleShot
        g = pencere.dugme_tepsi.geometry()
        dpr = pencere.devicePixelRatio()
        bilgi["tepsi_dugme_merkez"] = (round(g.center().x() * dpr), round(g.center().y() * dpr))  # FIZIKSEL piksel (125%: x1.25)
        bilgi["pencere_boyut"] = (pencere.width(), pencere.height())
        bilgi["dpr"] = dpr

        def a0() -> None:
            olgu(f"A4 anlik dugme={pencere.dugme_anlik.text().splitlines()[0]!r} bolge dugme={pencere.dugme_bolge.text().splitlines()[0]!r}",
                 "Ctrl+Alt+D" in pencere.dugme_anlik.text() and "Ctrl+Alt+R" in pencere.dugme_bolge.text())
            olgu(f"A4 tepsi ipucu={pencere.tepsi.ikon.toolTip()!r} durum satiri={pencere.durum_metni()!r}",
                 "Ctrl+Alt+D" in pencere.tepsi.ikon.toolTip() and "Ctrl+Alt+R" in pencere.tepsi.ikon.toolTip() and pencere.durum_metni() == "")
            h, cls = on_plan()
            olgu(f"A1 on plan bizim pencere={h == int(pencere.winId())} ({cls}); Ctrl+Alt+R")
            tus(ord("R"))

        def a1() -> None:
            ks = katmanlar()
            h, cls = on_plan()
            olgu(f"A1 Ctrl+Alt+R -> bolge_izle_istendi={sayac['bolge']} katman={len(ks)} on plan katman={bool(ks) and h == int(ks[0].winId())} sekme gizli={not pencere.sekme.isVisible()}",
                 sayac["bolge"] == 1 and len(ks) == 1 and h == int(ks[0].winId()))
            for k in ks:
                k.iptal.connect(lambda: sayac.__setitem__("iptal", sayac["iptal"] + 1))
            esc()

        def a1b() -> None:
            olgu(f"A1 Esc -> iptal={sayac['iptal']} katman={len(katmanlar())} durum={pencere.durum}", sayac["iptal"] == 1 and not katmanlar() and pencere.durum is KabukDurumu.GORUNUR)
            pencere.tepsiye_al()

        def a2() -> None:
            h, cls = on_plan()
            olgu(f"A2 tepsi: durum={pencere.durum} gorunur={pencere.isVisible()} tepsi ikonu={pencere.tepsi.gorunur()} on plan class={cls} bizim={h == int(pencere.winId())}",
                 pencere.durum is KabukDurumu.TEPSI and not pencere.isVisible())
            tus(ord("R"))

        def a2b() -> None:
            ks = katmanlar()
            h, cls = on_plan()
            olgu(f"A2 tepsideyken Ctrl+Alt+R -> bolge={sayac['bolge']} katman={len(ks)} on plan katman={bool(ks) and h == int(ks[0].winId())} durum={pencere.durum}",
                 sayac["bolge"] == 2 and len(ks) == 1 and h == int(ks[0].winId()) and pencere.durum is KabukDurumu.TEPSI)
            for k in ks:
                k.iptal.connect(lambda: sayac.__setitem__("iptal", sayac["iptal"] + 1))
            esc()

        def a2c() -> None:
            olgu(f"A2 Esc -> iptal={sayac['iptal']} katman={len(katmanlar())} durum={pencere.durum} pencere gorunur={pencere.isVisible()}",
                 sayac["iptal"] == 2 and not katmanlar() and pencere.durum is KabukDurumu.TEPSI and not pencere.isVisible())
            tus(ord("D"))

        def a2d() -> None:
            h, cls = on_plan()
            olgu(f"A2 tepsideyken Ctrl+Alt+D -> anlik={sayac['anlik']} durum={pencere.durum} gorunur={pencere.isVisible()} on plan bizim={h == int(pencere.winId())} ({cls}) tepsi ikonu={pencere.tepsi.gorunur()}",
                 sayac["anlik"] == 1 and pencere.durum is KabukDurumu.GORUNUR and pencere.isVisible() and h == int(pencere.winId()))
            pencere.kenara_al()

        def a3() -> None:
            olgu(f"A3 kenar: durum={pencere.durum} sekme gorunur={pencere.sekme.isVisible()} pencere gorunur={pencere.isVisible()}", pencere.durum is KabukDurumu.KENAR and pencere.sekme.isVisible())
            tus(ord("D"))

        def a3b() -> None:
            h, cls = on_plan()
            olgu(f"A3 kenardayken Ctrl+Alt+D -> anlik={sayac['anlik']} durum={pencere.durum} gorunur={pencere.isVisible()} sekme gizli={not pencere.sekme.isVisible()} on plan bizim={h == int(pencere.winId())}",
                 sayac["anlik"] == 2 and pencere.durum is KabukDurumu.GORUNUR and not pencere.sekme.isVisible() and h == int(pencere.winId()))
            pencere.kapat()

        T(800, a0)
        T(1800, a1)
        T(2600, a1b)
        T(3400, a2)
        T(4400, a2b)
        T(5200, a2c)
        T(6000, a2d)
        T(6800, a3)
        T(7600, a3b)
        return _bagla(app, pencere)

    rc = calistir([], calistirici=calistirici)
    bekle(300)
    olgu(f"A5 exec donus={rc}; D bos={bos_mu(ord('D'))} R bos={bos_mu(ord('R'))}", rc == 0 and bos_mu(ord("D")) and bos_mu(ord("R")))
    return bilgi


def bolum_b(bilgi: dict[str, object]) -> None:
    p = subprocess.Popen([sys.executable, "demo/kabuk.py"], cwd=str(KOK), stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    try:
        ana = 0
        for _ in range(60):
            uyu(100)
            for h, baslik, cls in pencereler(p.pid):
                if baslik.startswith("Sufl"):
                    ana = h
            if ana:
                break
        olgu(f"B0 demo surec pid={p.pid} ana pencere bulundu={bool(ana)} gorunur pencereler={[(c, b) for _, b, c in pencereler(p.pid)]}", bool(ana))
        uyu(800)
        olgu(f"B0 D bos={bos_mu(ord('D'))} R bos={bos_mu(ord('R'))} (demo tutuyor -> False/False)", not bos_mu(ord("D")) and not bos_mu(ord("R")))
        n0 = len(pencereler(p.pid))
        tus(ord("R"))
        uyu(1000)
        w = pencereler(p.pid)
        h, cls = on_plan()
        yeni = [x for x in w if x[0] != ana]
        olgu(f"B1 Ctrl+Alt+R -> gorunur pencere {n0} -> {len(w)}; yeni={[(c) for _, _, c in yeni]}; on plan yeni pencerede={any(h == x[0] for x in yeni)}", len(w) == n0 + 1 and any(h == x[0] for x in yeni))
        esc()
        uyu(800)
        olgu(f"B1 Esc -> gorunur pencere {len(pencereler(p.pid))} ({n0})", len(pencereler(p.pid)) == n0)
        # B2 tepsi dugmesi
        cx, cy = bilgi["tepsi_dugme_merkez"]  # type: ignore[misc]
        lp = (int(cy) << 16) | (int(cx) & 0xFFFF)
        u32.PostMessageW(ana, WM_MOUSEMOVE, 0, lp)
        u32.PostMessageW(ana, WM_LBUTTONDOWN, MK_LBUTTON, lp)
        u32.PostMessageW(ana, WM_LBUTTONUP, 0, lp)
        uyu(800)
        gizli = not u32.IsWindowVisible(ana)
        yol = "PostMessage"
        if not gizli:
            r = wintypes.RECT()
            u32.GetWindowRect(ana, ctypes.byref(r))
            sx, sy = r.left + int(cx), r.top + int(cy)
            u32.SetCursorPos(sx, sy)
            uyu(100)
            u32.mouse_event(0x0002, 0, 0, 0, 0)
            u32.mouse_event(0x0004, 0, 0, 0, 0)
            uyu(800)
            gizli = not u32.IsWindowVisible(ana)
            yol = "gercek fare"
        olgu(f"B2 tepsi dugmesi ({yol}) -> ana pencere gizli={gizli} gorunur pencereler={[(c) for _, _, c in pencereler(p.pid)]}", gizli)
        if gizli:
            uyu(2500)  # balon
            n0 = len(pencereler(p.pid))
            tus(ord("R"))
            uyu(1000)
            w = pencereler(p.pid)
            h, cls = on_plan()
            olgu(f"B3 tepsideyken Ctrl+Alt+R -> gorunur {n0} -> {len(w)} on plan yeni={any(h == x[0] for x in w)} ({cls})", len(w) == n0 + 1 and any(h == x[0] for x in w))
            esc()
            uyu(800)
            olgu(f"B3 Esc -> gorunur {len(pencereler(p.pid))} ({n0}); ana gizli={not u32.IsWindowVisible(ana)}", len(pencereler(p.pid)) == n0 and not u32.IsWindowVisible(ana))
            tus(ord("D"))
            uyu(1000)
            h, cls = on_plan()
            olgu(f"B3 tepsideyken Ctrl+Alt+D -> ana gorunur={bool(u32.IsWindowVisible(ana))} on plan ana={h == ana} ({cls})", bool(u32.IsWindowVisible(ana)) and h == ana)
        u32.PostMessageW(ana, WM_CLOSE, 0, 0)
        try:
            rc = p.wait(10)
        except subprocess.TimeoutExpired:
            rc = None
        uyu(300)
        olgu(f"B4 WM_CLOSE -> surec cikis={rc}; D bos={bos_mu(ord('D'))} R bos={bos_mu(ord('R'))}", rc == 0 and bos_mu(ord("D")) and bos_mu(ord("R")))
        err = p.stderr.read() if p.stderr else ""
        olgu(f"B4 demo stderr {len(err)} karakter" + (f": {err[-300:]!r}" if err else ""))
    finally:
        if p.poll() is None:
            p.kill()


def main() -> int:
    sys.stdout.reconfigure(encoding="ascii", errors="backslashreplace")  # type: ignore[union-attr]
    app = QtWidgets.QApplication(sys.argv)
    buf = ctypes.create_unicode_buffer(16)
    u32.GetKeyboardLayoutNameW(buf)
    olgu(f"ortam: platform={app.platformName()} duzen={buf.value} on kosul D bos={bos_mu(ord('D'))} R bos={bos_mu(ord('R'))} tepsi var={QtWidgets.QSystemTrayIcon.isSystemTrayAvailable()}")
    print("-- Bolum A (surec ici, demo _bagla + urun servisi)")
    bilgi = bolum_a()
    print(f"-- Bolum B (kara kutu: python demo/kabuk.py) tepsi dugme merkezi (fiziksel)={bilgi.get('tepsi_dugme_merkez')} pencere (mantiksal)={bilgi.get('pencere_boyut')} dpr={bilgi.get('dpr')}")
    bolum_b(bilgi)
    print()
    print(f"SONDA_2: {len(ihlaller)} IHLAL" if ihlaller else "SONDA_2: TEMIZ")
    return 1 if ihlaller else 0


if __name__ == "__main__":
    raise SystemExit(main())
