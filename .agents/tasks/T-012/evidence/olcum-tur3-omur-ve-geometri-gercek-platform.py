"""T-012 tur 3 -- O-B5 (deleteLater + tutulan referans) ve O-A2 (panel acikken close -> bayat geometri) GERCEK Windows
platforminda (offscreen degil), kilitten ve fareden BAGIMSIZ.

    python .agents/tasks/T-012/evidence/olcum-tur3-omur-ve-geometri-gercek-platform.py

Offscreen testler Python/PySide sarmalayici omrunu ve Qt geometrisini olcer; burada ayrica Win32 kanaliyla
(`IsWindow(hwnd)`, `GetWindowRect(hwnd)` -- Qt'den bagimsiz, kural 8) olculur:
  [1] kenar durumunda `p.deleteLater()` cagrilir, REFERANS TUTULUR (del yok): sekme hwnd yok edilir, C++ sekme/menu
      gecersiz (`shiboken6.isValid` False; sarmalayici `__dict__`te durdugu icin weakref None DEGIL), gorunur ust-duzey 0,
      `QMenu` ust-duzeyde yok, yoklayici imleci okumaz; referans birakilinca weakref'ler None.
  [2] AnaPencere yolu: kenar -> panel acik (sahte imlec) -> `sekme.close()` -> bir olay dongusu turu -> `kenara_al()`:
      Win32 `GetWindowRect` boyutu ilk kapali sekmenin boyutuna ESIT (aynı birim, DPI yuvarlamasi varsayimsiz),
      Qt `frameGeometry` r x 2r; saydam kosede hover panel acmaz.
  [3] tek basina KenarSekmesi: `close()` ve `closeAllWindows()` yollari, ayni olcu.
  [4] pozitif kontrol (olcu ateslenebilir): `destroyed -> deleteLater` baglantisi OLMAYAN alt sinif kalibi -> hwnd yasar.
Stdout ASCII; mutlak yol yok. Cikis 0 = temiz.
"""
from __future__ import annotations

import ctypes
import gc
import os
import sys
import weakref
from ctypes import wintypes
from pathlib import Path

os.environ.pop("QT_QPA_PLATFORM", None)
KOK = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(KOK))

from PySide6 import QtCore, QtGui, QtWidgets  # noqa: E402
from shiboken6 import isValid  # noqa: E402

from src.ui.geometri import sekme_icinde  # noqa: E402
from src.ui.kabuk import AnaPencere  # noqa: E402
from src.ui.kenar_sekmesi import KenarSekmesi  # noqa: E402

u32 = ctypes.windll.user32
u32.IsWindow.argtypes = [wintypes.HWND]
u32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
ihlal: list[str] = []


class Imlec:
    def __init__(self) -> None:
        self.nokta = QtCore.QPoint(-10000, -10000)
        self.sayac = 0

    def __call__(self) -> QtCore.QPoint:
        self.sayac += 1
        return QtCore.QPoint(self.nokta)


def dongu(ms: int) -> None:
    loop = QtCore.QEventLoop()
    QtCore.QTimer.singleShot(ms, loop.quit)
    loop.exec()


def gorunur() -> list[str]:
    return [type(w).__name__ for w in QtWidgets.QApplication.topLevelWidgets() if w.isVisible()]


def ust_duzey() -> list[str]:
    return sorted(type(w).__name__ for w in QtWidgets.QApplication.topLevelWidgets())


def win_boyut(w: QtWidgets.QWidget) -> tuple[int, int]:
    r = wintypes.RECT()
    u32.GetWindowRect(wintypes.HWND(int(w.winId())), ctypes.byref(r))
    return (r.right - r.left, r.bottom - r.top)


def rapor(ok: bool, m: str) -> None:
    print(("  ok     " if ok else "  IHLAL  ") + m)
    if not ok:
        ihlal.append(m)


def bekle_acilsin(s: KenarSekmesi, imlec: Imlec) -> bool:
    fg = s.frameGeometry()
    imlec.nokta = QtCore.QPoint(fg.right() - 3, fg.center().y())
    son = QtCore.QDeadlineTimer(s.acilma_ms + 2 * s.yoklama_ms + 600)
    while not son.hasExpired() and not s.acik:
        dongu(10)
    return s.acik


def main() -> int:
    app = QtWidgets.QApplication([])
    app.setQuitOnLastWindowClosed(False)
    print(f"T-012 tur 3 omur + geometri -- platform={app.platformName()} (gercek ekran; fare/on plan gerekmez)")
    ekran = QtGui.QGuiApplication.primaryScreen()
    assert ekran is not None

    # [1] deleteLater + referans tutulur
    imlec = Imlec()
    p = AnaPencere(ekran, tepsi_kullanilabilir=True, imlec_konumu=imlec)
    p.show(); p.kenara_al(); dongu(150)
    hwnd = wintypes.HWND(int(p.sekme.winId()))
    ws, wt, wm = weakref.ref(p.sekme), weakref.ref(p.tepsi), weakref.ref(p.tepsi.menu)
    canliydi = bool(u32.IsWindow(hwnd)) and p.sekme.isVisible() and imlec.sayac > 0
    p.deleteLater()  # REFERANS TUTULUYOR
    dongu(300)
    n = imlec.sayac; dongu(200); okuyor = imlec.sayac > n
    s = ws(); m = wm()
    cpp_sekme_olu = s is None or not isValid(s)
    cpp_menu_olu = m is None or not isValid(m)
    rapor(canliydi and not isValid(p) and cpp_sekme_olu and cpp_menu_olu and not u32.IsWindow(hwnd) and gorunur() == []
          and "QMenu" not in ust_duzey() and not okuyor,
          f"[1] deleteLater + referans tutulur: onceden hwnd canli={canliydi}; sonra C++ AnaPencere olu={not isValid(p)} "
          f"sekme C++ olu={cpp_sekme_olu} (weakref None={s is None}) menu C++ olu={cpp_menu_olu} sekme hwnd hala var={bool(u32.IsWindow(hwnd))} "
          f"gorunur ust-duzey={gorunur()} ust-duzey={ust_duzey()} yoklayici okuyor={okuyor}")
    wp = weakref.ref(p)
    del s, m  # yerel referanslar sarmalayiciyi tutmasin
    del p; gc.collect(); dongu(200)
    rapor(wp() is None and ws() is None and wt() is None and wm() is None,
          f"[1b] referans birakilinca: AnaPencere={wp() is None} sekme={ws() is None} tepsi={wt() is None} menu={wm() is None} (hepsi None beklenir)")
    if ws() is not None and isValid(ws()):
        ws().hide(); ws().deleteLater(); dongu(50)

    # [2] AnaPencere yolu: panel acikken close -> kenara_al -> GetWindowRect
    imlec = Imlec()
    p = AnaPencere(ekran, tepsi_kullanilabilir=True, imlec_konumu=imlec)
    p.show(); p.kenara_al(); dongu(150)
    s = p.sekme
    kapali = s.frameGeometry(); kapali_win = win_boyut(s)
    acildi = bekle_acilsin(s, imlec)
    acik_win = win_boyut(s)
    imlec.nokta = QtCore.QPoint(-10000, -10000)
    s.close(); dongu(50)
    durum_gorunur = str(p.durum) == "gorunur"
    p.kenara_al(); dongu(150)
    yeni = s.frameGeometry(); yeni_win = win_boyut(s)
    kose = QtCore.QPoint(kapali.left() + 5, kapali.top() + 5)
    disk_disi = not sekme_icinde(kapali, kose, s.yaricap, s.kenar)
    imlec.nokta = kose; dongu(s.acilma_ms + 3 * s.yoklama_ms)
    hover_acti = s.acik
    rapor(acildi and acik_win != kapali_win and durum_gorunur and yeni == kapali and yeni_win == kapali_win and disk_disi and not hover_acti,
          f"[2] AnaPencere: panel acildi={acildi} (win {acik_win}); close -> durum gorunur={durum_gorunur}; kenara_al sonrasi "
          f"Qt {yeni.width()}x{yeni.height()} (beklenen {kapali.width()}x{kapali.height()}) Win32 {yeni_win} (beklenen {kapali_win}); "
          f"saydam kose disk disi={disk_disi} hover panel acti={hover_acti}")
    p.kapat(); dongu(50)

    # [3] tek basina: close / closeAllWindows
    for yol in ("close", "closeAllWindows"):
        imlec = Imlec()
        k = KenarSekmesi(ekran, imlec_konumu=imlec); k.show(); dongu(150)
        kapali = k.frameGeometry(); kapali_win = win_boyut(k)
        acildi = bekle_acilsin(k, imlec)
        imlec.nokta = QtCore.QPoint(-10000, -10000)
        if yol == "close":
            k.close()
        else:
            QtWidgets.QApplication.closeAllWindows()
        dongu(50)
        k.show(); dongu(150)
        yeni = k.frameGeometry(); yeni_win = win_boyut(k)
        rapor(acildi and yeni == kapali and yeni_win == kapali_win,
              f"[3] tek basina {yol}: panel acildi={acildi}; yeniden show Qt {yeni.width()}x{yeni.height()} Win32 {yeni_win} (beklenen {kapali_win})")
        k.hide(); del k; gc.collect(); dongu(50)

    # [4] pozitif kontrol: destroyed -> deleteLater baglantisi olmayan sahip kalibi -> hwnd yasar
    class SahipsizKalip(QtWidgets.QWidget):
        def __init__(self) -> None:
            super().__init__(None, QtCore.Qt.WindowType.Tool)
            self.cocuk = KenarSekmesi(ekran)
            self.cocuk.show()

    class SahipliKalip(SahipsizKalip):
        def __init__(self) -> None:
            super().__init__()
            self.destroyed.connect(self.cocuk.deleteLater)

    sonuc: dict[str, bool] = {}
    for K in (SahipliKalip, SahipsizKalip):
        w = K(); dongu(100)
        hwnd = wintypes.HWND(int(w.cocuk.winId()))
        w.deleteLater(); dongu(300)  # referans tutulur
        sonuc[K.__name__] = bool(u32.IsWindow(hwnd))
        if isValid(w.cocuk):
            w.cocuk.hide(); w.cocuk.deleteLater(); dongu(50)
        del w; gc.collect(); dongu(50)
    rapor(sonuc == {"SahipliKalip": False, "SahipsizKalip": True},
          f"[4] pozitif kontrol (sekme hwnd yasiyor mu): destroyed->deleteLater baglantisiz={sonuc['SahipsizKalip']} baglantili={sonuc['SahipliKalip']}")

    print()
    if ihlal:
        print(f"TUR 3 GERCEK PLATFORM: {len(ihlal)} IHLAL"); return 1
    print("TUR 3 GERCEK PLATFORM: TEMIZ"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
