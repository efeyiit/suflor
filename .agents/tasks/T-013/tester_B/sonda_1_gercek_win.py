"""T-013 Tester-B sonda 1 -- GERCEK Windows, ayri surec (YASAK degiskeni KALDIRILIR), sentetik keybd_event, ekran kilitsiz.

    python .agents/tasks/T-013/tester_B/sonda_1_gercek_win.py

Kombinasyonlar Tester-A ile cakisirsa 1409 gorulebilir; her adim on kosulunu yazar. Stdout ASCII.
S1  gercek servis: Ctrl+Alt+D -> tetiklendi 1, gecikme (10 basis medyan)
S2  GERCEK AltGr dizisi (yalniz VK_RMENU + D; LCtrl+RMenu+D) -> tetiklenir mi (TR-Q: AltGr = Ctrl+Alt; D bos -> zararsiz, belge)
S3  Ctrl+Alt+R kayitli: Ctrl+Alt+Shift+R -> 0 (tetiklememeli); pozitif kontrol Ctrl+Alt+R -> 1
S4  Ctrl+Alt+D kayitli: Ctrl+D -> 0, Alt+D -> 0 (odak bizim QLineEdit'te; menu modu?)
S5  ayni surecte iki servis (D, R) -> dogru servise
S6  baska surec R tutarken kaydet -> CAKISMA + son_hata_kodu 1409; surec olunce OK
S7  surec cikisi (sys.exit / os._exit / app.quit sonrasi normal donus) -> Windows kaydi serbest birakiyor mu
S8  dilbilgisinden gecen sistem kombinasyonlari Windows'ta aliniyor mu (yalniz kayit, ATES YOK) + Ctrl+Tab (GECERSIZ) Windows'ta alinir mi
S8b Ctrl+Shift+Tab kayitli: ates -> bize gelir mi (tarayici sekme gezintisi sistem genelinde yutulur)
S9  altgr_karakteri BAGIMSIZ referansla (VkKeyScanW: karakter -> (vk, shift); shift==6 = Ctrl+Alt) tablo tuslarinin hepsinde capraz
S9b altgr_karakteri baska thread'den (tek duzen: ayni sonuc bekl.; istisna yok)
S10 deleteLater yolu GERCEK dongude (app.exec + QTimer.quit): ebeveyn deleteLater / servis deleteLater+ref -> D yeniden alinabiliyor
S11 dinleyici istisnasi gercek WM_HOTKEY dagitiminda: stderr'e metin, ikinci basis gelir, surec yasar
S12 calistir x2 ayni surec (gercek): ikinci pencere 'baska bir uygulama'; p1.kapat() -> ucuncu OK
S13 gercek platformda pencere genisligi iki cakisma metniyle degismez (520)
"""
from __future__ import annotations

import ctypes
import gc
import io
import os
import statistics
import subprocess
import sys
import threading
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
u32.VkKeyScanW.argtypes = [wintypes.WCHAR]
u32.VkKeyScanW.restype = ctypes.c_short
VK_CONTROL, VK_MENU, VK_SHIFT, VK_LCONTROL, VK_RMENU, KEYUP = 0x11, 0x12, 0x10, 0xA2, 0xA5, 0x2
MOD_ALT, MOD_CONTROL, MOD_SHIFT, MOD_NOREPEAT = 0x1, 0x2, 0x4, 0x4000
CA = MOD_CONTROL | MOD_ALT
GUI_INMENUMODE = 0x4
satirlar: list[str] = []
ihlaller: list[str] = []


class _GUITHREADINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("flags", wintypes.DWORD), ("hwndActive", wintypes.HWND), ("hwndFocus", wintypes.HWND),
                ("hwndCapture", wintypes.HWND), ("hwndMenuOwner", wintypes.HWND), ("hwndMoveSize", wintypes.HWND), ("hwndCaret", wintypes.HWND),
                ("rcCaret", wintypes.RECT)]


def menu_modu() -> bool:
    g = _GUITHREADINFO()
    g.cbSize = ctypes.sizeof(_GUITHREADINFO)
    return bool(u32.GetGUIThreadInfo(0, ctypes.byref(g))) and bool(g.flags & GUI_INMENUMODE)


def olgu(m: str, ok: bool | None = None) -> None:
    on = "  " if ok is None else ("  ok     " if ok else "  IHLAL  ")
    satirlar.append(on + m)
    print(on + m, flush=True)
    if ok is False:
        ihlaller.append(m)


def bekle(ms: int) -> None:
    son = time.perf_counter() + ms / 1000
    while time.perf_counter() < son:
        QtWidgets.QApplication.processEvents()
        time.sleep(0.002)


def dizi(*adimlar: tuple[int, bool]) -> None:
    for vk, up in adimlar:
        u32.keybd_event(vk, 0, KEYUP if up else 0, 0)


def tus(vk: int, ctrl: bool = True, alt: bool = True, shift: bool = False) -> None:
    on: list[tuple[int, bool]] = []
    if ctrl:
        on.append((VK_CONTROL, False))
    if alt:
        on.append((VK_MENU, False))
    if shift:
        on.append((VK_SHIFT, False))
    dizi(*on, (vk, False), (vk, True), *[(v, True) for v, _ in reversed(on)])


def bos_mu(mod: int, vk: int) -> tuple[bool, int]:
    k32.SetLastError(0)
    ok = bool(u32.RegisterHotKey(None, 0xBFE0, mod | MOD_NOREPEAT, vk))
    err = k32.GetLastError()
    if ok:
        u32.UnregisterHotKey(None, 0xBFE0)
    return ok, err


def baska_surec(harf: str) -> subprocess.Popen[str]:
    p = subprocess.Popen([sys.executable, "-c", f"import ctypes,time; u=ctypes.windll.user32; print(u.RegisterHotKey(None,5,0x1|0x2|0x4000,ord('{harf}')), flush=True); time.sleep(30)"],
                         stdout=subprocess.PIPE, text=True)
    if p.stdout:
        p.stdout.readline()
    return p


def main() -> int:
    sys.stdout.reconfigure(encoding="ascii", errors="backslashreplace")  # type: ignore[union-attr]
    app = QtWidgets.QApplication(sys.argv)
    from src.ui.kabuk import AnaPencere
    from src.ui.kisayol import KayitSonucu, KisayolServisi, altgr_karakteri, kombinasyonu_coz
    from src.ui.uygulama import calistir

    buf = ctypes.create_unicode_buffer(16)
    u32.GetKeyboardLayoutNameW(buf)
    olgu(f"ortam: platform={app.platformName()} duzen={buf.value} (0000041F=TR-Q) YASAK={os.environ.get('SUFLOR_GERCEK_KISAYOL_YASAK')!r}")
    for ad in "DRX":
        ok, err = bos_mu(CA, ord(ad))
        olgu(f"on kosul Ctrl+Alt+{ad} bos={ok} err={err}")

    # yakalayici pencere: sentetik tuslar kayitsizken buraya gelsin (terminale degil)
    yak = QtWidgets.QWidget()
    yak.setWindowTitle("Tester-B yakalayici")
    le = QtWidgets.QLineEdit(yak)
    yak.resize(320, 80)
    yak.show()
    yak.raise_()
    yak.activateWindow()
    le.setFocus()
    bekle(400)
    on_planda = int(u32.GetForegroundWindow() or 0) == int(yak.winId())
    olgu(f"yakalayici on planda={on_planda}")

    # S1
    s = KisayolServisi(gercek_win32=True)
    alinan: list[tuple[str, float]] = []
    s.tetiklendi.connect(lambda ad: alinan.append((ad, time.perf_counter())))
    r = s.kaydet("anlik_cevir", "Ctrl+Alt+D")
    olgu(f"S1 kaydet(Ctrl+Alt+D)={r} son_hata={s.son_hata_kodu} kayitli={s.kayitli()}", r is KayitSonucu.OK)
    gecikmeler: list[float] = []
    for _ in range(10):
        n0 = len(alinan)
        t0 = time.perf_counter()
        tus(ord("D"))
        bekle(150)
        if len(alinan) == n0 + 1:
            gecikmeler.append((alinan[-1][1] - t0) * 1000)
    olgu(f"S1 10 basis -> {len(alinan)} sinyal; gecikme medyan={statistics.median(gecikmeler) if gecikmeler else -1:.1f} ms max={max(gecikmeler) if gecikmeler else -1:.1f} ms", len(alinan) == 10)

    # S2 gercek AltGr dizisi
    for etiket, adimlar in (("yalniz VK_RMENU + D", ((VK_RMENU, False), (ord("D"), False), (ord("D"), True), (VK_RMENU, True))),
                            ("LCtrl+RMenu+D (donanim AltGr)", ((VK_LCONTROL, False), (VK_RMENU, False), (ord("D"), False), (ord("D"), True), (VK_RMENU, True), (VK_LCONTROL, True)))):
        n0 = len(alinan)
        le.clear()
        dizi(*adimlar)
        bekle(300)
        olgu(f"S2 {etiket} -> tetiklendi +{len(alinan) - n0} (AltGr+D Snapshot'i acar; D AltGr'de bos -> metin kaybi yok) QLineEdit={le.text()!r} menu modu={menu_modu()}")

    # S4 Ctrl+D / Alt+D
    for etiket, kw in (("Ctrl+D", dict(ctrl=True, alt=False)), ("Alt+D", dict(ctrl=False, alt=True)), ("Shift+D", dict(ctrl=False, alt=False, shift=True)), ("Ctrl+Alt+Shift+D", dict(shift=True))):
        n0 = len(alinan)
        le.clear()
        tus(ord("D"), **kw)  # type: ignore[arg-type]
        bekle(250)
        mm = menu_modu()
        if mm:
            dizi((0x1B, False), (0x1B, True))
            bekle(100)
        olgu(f"S4 {etiket} -> tetiklendi +{len(alinan) - n0} (0) QLineEdit={le.text()!r} menu modu={mm}", len(alinan) == n0)
    n0 = len(alinan)
    tus(ord("D"))
    bekle(250)
    olgu(f"S4 pozitif kontrol Ctrl+Alt+D -> +{len(alinan) - n0} (1)", len(alinan) == n0 + 1)

    # S3 Ctrl+Alt+R kayitli, Ctrl+Alt+Shift+R
    r = s.kaydet("bolge_izle", "Ctrl+Alt+R")
    olgu(f"S3 kaydet(Ctrl+Alt+R)={r}", r is KayitSonucu.OK)
    n0 = len(alinan)
    le.clear()
    tus(ord("R"), shift=True)
    bekle(250)
    olgu(f"S3 Ctrl+Alt+Shift+R -> tetiklendi +{len(alinan) - n0} (0) QLineEdit={le.text()!r}", len(alinan) == n0)
    n0 = len(alinan)
    tus(ord("R"))
    bekle(250)
    olgu(f"S3 pozitif kontrol Ctrl+Alt+R -> +{len(alinan) - n0} (1) ad={alinan[-1][0] if len(alinan) > n0 else None}", len(alinan) == n0 + 1 and alinan[-1][0] == "bolge_izle")

    # S5 iki servis
    s.kaldir("bolge_izle")
    s2 = KisayolServisi(gercek_win32=True)
    alinan2: list[str] = []
    s2.tetiklendi.connect(alinan2.append)
    r2 = s2.kaydet("bolge_izle", "Ctrl+Alt+R")
    n0 = len(alinan)
    tus(ord("D"))
    bekle(200)
    tus(ord("R"))
    bekle(200)
    olgu(f"S5 iki servis: s2.kaydet(R)={r2}; D -> s1 +{len(alinan) - n0} s2 {len(alinan2)}; R -> s2 {alinan2}", r2 is KayitSonucu.OK and len(alinan) == n0 + 1 and alinan2 == ["bolge_izle"])
    n0 = len(alinan)
    n2 = len(alinan2)
    s2.hepsini_kaldir()
    tus(ord("R"))
    bekle(200)
    olgu(f"S5 s2.hepsini_kaldir sonrasi R -> s1 +{len(alinan) - n0} s2 +{len(alinan2) - n2} (0/0); s1 kayitli={s.kayitli()}", len(alinan) == n0 and len(alinan2) == n2)
    del s2
    gc.collect()

    # S6 baska surec R tutarken
    diger = baska_surec("R")
    try:
        bekle(100)
        r = s.kaydet("bolge_izle", "Ctrl+Alt+R")
        olgu(f"S6 baska surec R tutarken kaydet(R)={r} son_hata_kodu={s.son_hata_kodu} kayitli={s.kayitli()}", r is KayitSonucu.CAKISMA and s.son_hata_kodu == 1409 and "bolge_izle" not in s.kayitli())
        n0 = len(alinan)
        tus(ord("R"))
        bekle(200)
        olgu(f"S6 R basisi bize gelmedi +{len(alinan) - n0} (0); D hala calisiyor:", len(alinan) == n0)
        n0 = len(alinan)
        tus(ord("D"))
        bekle(200)
        olgu(f"S6 D -> +{len(alinan) - n0} (1)", len(alinan) == n0 + 1)
    finally:
        diger.kill()
        diger.wait(5)
    bekle(200)
    r = s.kaydet("bolge_izle", "Ctrl+Alt+R")
    olgu(f"S6 surec olunce kaydet(R)={r} son_hata={s.son_hata_kodu}", r is KayitSonucu.OK and s.son_hata_kodu == 0)
    s.hepsini_kaldir()
    olgu(f"S6 hepsini_kaldir -> D bos={bos_mu(CA, ord('D'))[0]} R bos={bos_mu(CA, ord('R'))[0]}", bos_mu(CA, ord("D"))[0] and bos_mu(CA, ord("R"))[0])

    # S7 surec cikisi
    cocuk_kod = (
        "import os,sys; sys.path.insert(0, os.getcwd()); os.environ.pop('SUFLOR_GERCEK_KISAYOL_YASAK', None)\n"
        "from PySide6 import QtWidgets, QtCore; app=QtWidgets.QApplication([])\n"
        "from src.ui.kisayol import KisayolServisi\n"
        "s=KisayolServisi(gercek_win32=True); print(s.kaydet('a','Ctrl+Alt+D'), flush=True)\n"
        "sys.stdin.readline()\n"
        "{cikis}\n")
    for etiket, cikis in (("sys.exit(0)", "sys.exit(0)"), ("os._exit(0)", "os._exit(0)"), ("app.quit+exec donus", "QtCore.QTimer.singleShot(0, app.quit); app.exec()"),
                          ("raise (islenmemis istisna)", "raise RuntimeError('x')")):
        p = subprocess.Popen([sys.executable, "-c", cocuk_kod.format(cikis=cikis)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, cwd=str(KOK))
        assert p.stdout and p.stdin
        kayit = p.stdout.readline().strip()
        dolu_iken = bos_mu(CA, ord("D"))
        p.stdin.write("\n")
        p.stdin.flush()
        p.wait(20)
        bekle(200)
        sonra = bos_mu(CA, ord("D"))
        olgu(f"S7 cocuk {etiket}: kayit={kayit} cocuk yasarken D bos={dolu_iken[0]} err={dolu_iken[1]}; cikis kodu={p.returncode}; sonra D bos={sonra[0]}",
             kayit.endswith("ok") and not dolu_iken[0] and sonra[0])

    # S8 dilbilgisinden gecen sistem kombinasyonlari -- yalniz kayit
    tablo = [("Ctrl+Alt+Tab", CA, 0x09), ("Alt+Shift+Tab", MOD_ALT | MOD_SHIFT, 0x09), ("Ctrl+Shift+Tab", MOD_CONTROL | MOD_SHIFT, 0x09),
             ("Ctrl+Alt+Shift+Tab", CA | MOD_SHIFT, 0x09), ("Ctrl+Alt+Shift+Delete", CA | MOD_SHIFT, 0x2E), ("Ctrl+Alt+Shift+Esc", CA | MOD_SHIFT, 0x1B),
             ("Ctrl+Alt+Esc", CA, 0x1B), ("Alt+Shift+Esc", MOD_ALT | MOD_SHIFT, 0x1B), ("Ctrl+F4", MOD_CONTROL, 0x73), ("Shift+F10", MOD_SHIFT, 0x79),
             ("Ctrl+Alt+Enter", CA, 0x0D), ("Alt+Shift+Enter", MOD_ALT | MOD_SHIFT, 0x0D), ("Ctrl+Shift+Enter", MOD_CONTROL | MOD_SHIFT, 0x0D),
             ("Ctrl+Alt+Space", CA, 0x20), ("Ctrl+Shift+Space", MOD_CONTROL | MOD_SHIFT, 0x20), ("Ctrl+Alt+Backspace", CA, 0x08),
             ("Ctrl+Alt+Left", CA, 0x25), ("Ctrl+Alt+Up", CA, 0x26), ("Ctrl+Alt+Right", CA, 0x27), ("Ctrl+Alt+Down", CA, 0x28),
             ("Ctrl+Alt+Home", CA, 0x24), ("Ctrl+Alt+End", CA, 0x23), ("Ctrl+Alt+Insert", CA, 0x2D), ("Alt+Shift+F4", MOD_ALT | MOD_SHIFT, 0x73),
             ("Ctrl+Alt+F4", CA, 0x73), ("Alt+F1", MOD_ALT, 0x70), ("Ctrl+F1", MOD_CONTROL, 0x70), ("Ctrl+F5", MOD_CONTROL, 0x74)]
    for ad, mod, vk in tablo:
        try:
            kombinasyonu_coz(ad)
            dil = "GECERLI"
        except ValueError as e:
            dil = f"GECERSIZ({type(e).__name__})"
        ok, err = bos_mu(mod, vk)
        olgu(f"S8 {ad:22s} dilbilgisi={dil:10s} Windows kayit={ok} err={err}")
    for ad, mod, vk in (("Ctrl+Tab", MOD_CONTROL, 0x09), ("Shift+Tab", MOD_SHIFT, 0x09), ("Alt+Enter", MOD_ALT, 0x0D), ("Ctrl+Enter", MOD_CONTROL, 0x0D), ("Alt+Left", MOD_ALT, 0x25), ("Ctrl+Backspace", MOD_CONTROL, 0x08)):
        try:
            kombinasyonu_coz(ad)
            dil = "GECERLI"
        except ValueError as e:
            dil = f"GECERSIZ({type(e).__name__})"
        ok, err = bos_mu(mod, vk)
        olgu(f"S8 {ad:22s} dilbilgisi={dil:10s} Windows kayit={ok} err={err}  (alinabiliyorsa GECERSIZ karari sistem genelinde yutmayi ONLER)")
    # S8b Ctrl+Shift+Tab ates (odak bizim QLineEdit'te; tarayici yok)
    s8 = KisayolServisi(gercek_win32=True)
    al8: list[str] = []
    s8.tetiklendi.connect(al8.append)
    r8 = s8.kaydet("x", "Ctrl+Shift+Tab")
    le.clear()
    dizi((VK_CONTROL, False), (VK_SHIFT, False), (0x09, False), (0x09, True), (VK_SHIFT, True), (VK_CONTROL, True))
    bekle(250)
    olgu(f"S8b servis kaydet(Ctrl+Shift+Tab)={r8}; ates -> tetiklendi={al8} (1 ise sistem genelinde sekme gezintisi YUTULUR: dilbilgisi izin veriyor)")
    s8.hepsini_kaldir()
    r8b = s8.kaydet("x", "Ctrl+Alt+Tab")
    olgu(f"S8b servis kaydet(Ctrl+Alt+Tab)={r8b} (ates yok: kalici gorev degistirici)")
    s8.hepsini_kaldir()
    del s8
    gc.collect()

    # S9 altgr_karakteri bagimsiz referans: VkKeyScanW
    ref: dict[int, str] = {}
    for kod in list(range(0x20, 0x250)) + list(range(0x2000, 0x20D0)) + list(range(0x2100, 0x2200)):
        ch = chr(kod)
        r = int(u32.VkKeyScanW(ch))
        if r == -1:
            continue
        vk, shift = r & 0xFF, (r >> 8) & 0xFF
        if shift == 6:  # Ctrl+Alt = AltGr
            ref.setdefault(vk, ch)
    from src.ui.kisayol import _VK_ADLARI  # tablo tuslari (yalniz anahtar kumesi icin)
    uyumsuz: list[str] = []
    dolu: list[str] = []
    for vk, ad in sorted(_VK_ADLARI.items()):
        urun = altgr_karakteri(vk)
        beklenen = ref.get(vk, "")
        if urun != beklenen:
            uyumsuz.append(f"{ad}: urun={urun!r} ref={beklenen!r}")
        if urun:
            dolu.append(f"{ad}={urun!r}")
    t_ref = int(u32.VkKeyScanW("₺"))
    olgu(f"S9 VkKeyScanW(U+20BA)=(vk={t_ref & 0xFF:#x} shift={(t_ref >> 8) & 0xFF}) (0x54, 6 beklenir: T, Ctrl+Alt); referans AltGr tablosu {len(ref)} tus")
    olgu(f"S9 altgr_karakteri x {len(_VK_ADLARI)} tablo tusu <-> VkKeyScanW: uyumsuz={uyumsuz} dolu={dolu}", not uyumsuz and (t_ref & 0xFF) == 0x54 and ((t_ref >> 8) & 0xFF) == 6)
    olgu(f"S9 pozitif kontrol: altgr_karakteri(T)={altgr_karakteri(ord('T'))!r} D={altgr_karakteri(ord('D'))!r} R={altgr_karakteri(ord('R'))!r} Q={altgr_karakteri(ord('Q'))!r}",
         altgr_karakteri(ord("T")) == "₺" and altgr_karakteri(ord("D")) == "" and altgr_karakteri(ord("R")) == "")
    # Ctrl+Alt+T gercek servis -> ALTGR_CAKISMA, Win32'ye gitmedi (T bos kaldi)
    s9 = KisayolServisi(gercek_win32=True)
    r9 = s9.kaydet("t", "Ctrl+Alt+T")
    olgu(f"S9 gercek kaydet(Ctrl+Alt+T)={r9}; T Windows'ta bos={bos_mu(CA, ord('T'))[0]} (Win32 cagrilmadi)", r9 is KayitSonucu.ALTGR_CAKISMA and bos_mu(CA, ord("T"))[0])
    r9s = s9.kaydet("t", "Ctrl+Alt+Shift+T")
    olgu(f"S9 gercek kaydet(Ctrl+Alt+Shift+T)={r9s} (Shift'li: AltGr sorulmaz)", r9s is KayitSonucu.OK)
    s9.hepsini_kaldir()
    # S9b baska thread
    sonuc: list[object] = []

    def kos() -> None:
        try:
            sonuc.append((altgr_karakteri(ord("T")), altgr_karakteri(ord("D")), int(u32.GetKeyboardLayout(0))))
        except BaseException as e:  # noqa: BLE001
            sonuc.append(e)

    th = threading.Thread(target=kos)
    th.start()
    th.join(5)
    olgu(f"S9b baska thread: {sonuc!r} ana thread hkl={int(u32.GetKeyboardLayout(0)):#x} (tek duzen: ayni; cok duzenli [OLCULMUYOR])")

    # S10 deleteLater gercek dongude
    ebeveyn = QtWidgets.QWidget()
    s10 = KisayolServisi(ebeveyn, gercek_win32=True)
    r10 = s10.kaydet("d", "Ctrl+Alt+D")
    once = bos_mu(CA, ord("D"))[0]
    ebeveyn.deleteLater()
    QtCore.QTimer.singleShot(100, app.quit)
    app.exec()
    sonra = bos_mu(CA, ord("D"))[0]
    olgu(f"S10 ebeveyn.deleteLater + gercek exec: kayit={r10} once D bos={once} sonra D bos={sonra}", r10 is KayitSonucu.OK and not once and sonra)
    s10b = KisayolServisi(gercek_win32=True)
    s10b.kaydet("d", "Ctrl+Alt+D")
    s10b.deleteLater()  # referans TUTULUYOR (O-B5 sinifi)
    QtCore.QTimer.singleShot(100, app.quit)
    app.exec()
    sonra_b = bos_mu(CA, ord("D"))[0]
    olgu(f"S10 servis.deleteLater + referans tutulur + gercek exec: sonra D bos={sonra_b}", sonra_b)
    del s10b
    gc.collect()

    # S11 dinleyici istisnasi gercek dagitimda
    s11 = KisayolServisi(gercek_win32=True)
    al11: list[str] = []

    def patlak(ad: str) -> None:
        al11.append(ad)
        raise RuntimeError("tester-b dinleyici patladi")

    s11.tetiklendi.connect(patlak)
    s11.kaydet("d", "Ctrl+Alt+D")
    eski = sys.stderr
    tampon = io.StringIO()
    sys.stderr = tampon
    try:
        tus(ord("D"))
        bekle(200)
        tus(ord("D"))
        bekle(200)
    finally:
        sys.stderr = eski
    err = tampon.getvalue()
    olgu(f"S11 dinleyici istisnasi: 2 basis -> {len(al11)} cagri, surec yasiyor, stderr'de traceback={'tester-b dinleyici patladi' in err} ({len(err)} karakter)", len(al11) == 2)
    s11.hepsini_kaldir()
    del s11
    gc.collect()

    # S12 calistir x2 gercek
    tutulan: list[AnaPencere] = []

    def c(app_: QtWidgets.QApplication, pencere: AnaPencere) -> int:
        tutulan.append(pencere)
        return 0

    calistir([], calistirici=c)
    bekle(200)
    calistir([], calistirici=c)
    bekle(200)
    p1, p2 = tutulan
    m2 = p2.durum_metni()
    olgu(f"S12 ikinci calistir durum satiri={m2!r} anlik dugme kisayol yok={'(k' in p2.dugme_anlik.text()}", "Ctrl+Alt+D kaydedilemedi: ba" in m2 and "Ctrl+Alt+R kaydedilemedi" in m2 and "ayarlar" not in m2.lower())
    olgu(f"S12 gercek platformda p1 genislik={p1.width()} p2 (iki cakisma metni) genislik={p2.width()} (520)", p1.width() == 520 and p2.width() == 520)
    p1.kapat()
    bekle(200)
    olgu(f"S12 p1.kapat() sonrasi D bos={bos_mu(CA, ord('D'))[0]} R bos={bos_mu(CA, ord('R'))[0]}", bos_mu(CA, ord("D"))[0])
    calistir([], calistirici=c)
    bekle(200)
    p3 = tutulan[2]
    olgu(f"S12 ucuncu calistir durum satiri={p3.durum_metni()!r} anlik dugme={p3.dugme_anlik.text().splitlines()[0]!r}", p3.durum_metni() == "" and "Ctrl+Alt+D" in p3.dugme_anlik.text())
    for p in (p2, p3):
        p.kapat()
    bekle(200)
    olgu(f"S12 hepsi kapali: D bos={bos_mu(CA, ord('D'))[0]} R bos={bos_mu(CA, ord('R'))[0]}", bos_mu(CA, ord("D"))[0] and bos_mu(CA, ord("R"))[0])
    yak.close()
    bekle(100)
    print()
    print(f"SONDA_1: {len(ihlaller)} IHLAL" if ihlaller else "SONDA_1: TEMIZ")
    return 1 if ihlaller else 0


if __name__ == "__main__":
    raise SystemExit(main())
