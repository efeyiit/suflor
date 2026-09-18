"""Suflor pencerelerini Windows ekran yakalamasinin disinda tutar.

Windows 10 2004 ve sonrasinda ``WDA_EXCLUDEFROMCAPTURE`` pencereyi sistem
yakalamalarindan cikarir. API kullanilamiyorsa yakalama boyunca yalnizca
o anda gorunen Suflor pencereleri gizlenir ve her durumda geri getirilir.
"""
from __future__ import annotations

import ctypes
import sys
from collections.abc import Callable, Sequence
from ctypes import wintypes
from typing import TypeVar

from PySide6 import QtCore, QtWidgets

__all__ = ["WDA_EXCLUDEFROMCAPTURE", "YakalamaGizliligi"]

WDA_EXCLUDEFROMCAPTURE = 0x11

T = TypeVar("T")
AffinitySetter = Callable[[int, int], bool]


def _windows_affinity(hwnd: int, deger: int) -> bool:
    if sys.platform != "win32":
        return False
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    fonksiyon = user32.SetWindowDisplayAffinity
    fonksiyon.argtypes = (wintypes.HWND, wintypes.DWORD)
    fonksiyon.restype = wintypes.BOOL
    return bool(fonksiyon(wintypes.HWND(hwnd), wintypes.DWORD(deger)))


def _kompozitoru_bekle() -> None:
    app = QtWidgets.QApplication.instance()
    if app is not None:
        app.processEvents(QtCore.QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)
    if sys.platform == "win32":
        try:
            ctypes.WinDLL("dwmapi").DwmFlush()
        except OSError:
            pass


class YakalamaGizliligi(QtCore.QObject):
    """Pencere korumasini ve gorunurluk-korumali yakalamayi yonetir."""

    def __init__(
        self,
        *,
        set_affinity: AffinitySetter | None = None,
        compositor_wait: Callable[[], None] | None = None,
    ) -> None:
        super().__init__()
        self._set_affinity = set_affinity or _windows_affinity
        self._compositor_wait = compositor_wait or _kompozitoru_bekle

    def uygulamaya_kur(self, app: QtWidgets.QApplication) -> None:
        """Mevcut ve daha sonra gosterilecek tum ust-duzey pencereleri korur."""
        if self.parent() is app:
            return
        self.setParent(app)
        app.installEventFilter(self)
        for pencere in app.topLevelWidgets():
            self.koru(pencere)

    def eventFilter(self, izlenen: QtCore.QObject, olay: QtCore.QEvent) -> bool:
        if olay.type() is QtCore.QEvent.Type.Show and isinstance(izlenen, QtWidgets.QWidget) and izlenen.isWindow():
            self.koru(izlenen)
        return False

    def koru(self, pencere: QtWidgets.QWidget) -> bool:
        """Bir ust-duzey pencereyi yakalamadan cikar; destek yoksa ``False``."""
        if not pencere.isWindow():
            pencere = pencere.window()
        try:
            return bool(self._set_affinity(int(pencere.winId()), WDA_EXCLUDEFROMCAPTURE))
        except (OSError, TypeError, ValueError):
            return False

    def yakala(self, capture: Callable[[], T], pencereler: Sequence[QtWidgets.QWidget]) -> T:
        """Koruma basarisizsa gorunen pencereleri gecici gizleyerek ``capture`` calistirir."""
        tekil: list[QtWidgets.QWidget] = []
        kimlikler: set[int] = set()
        for pencere in pencereler:
            ust = pencere if pencere.isWindow() else pencere.window()
            kimlik = id(ust)
            if kimlik not in kimlikler:
                kimlikler.add(kimlik)
                tekil.append(ust)

        if all(self.koru(pencere) for pencere in tekil):
            return capture()

        gorunen = [pencere for pencere in tekil if pencere.isVisible()]
        for pencere in gorunen:
            pencere.hide()
        self._compositor_wait()
        try:
            return capture()
        finally:
            for pencere in gorunen:
                pencere.show()
