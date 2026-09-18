"""Uzun model indirmesini Qt arayüzünden ayıran küçük iş parçacığı köprüsü."""
from __future__ import annotations

import threading
from collections.abc import Callable

from PySide6 import QtCore

Progress = Callable[[int, int], None]
IndirFonksiyonu = Callable[[Progress], None]

__all__ = ["KaliteModeliIndirici"]


class KaliteModeliIndirici(QtCore.QObject):
    ilerleme = QtCore.Signal(object, object)
    hazir = QtCore.Signal()
    hata = QtCore.Signal(str)

    def __init__(self, indir: IndirFonksiyonu, parent: QtCore.QObject | None = None) -> None:
        super().__init__(parent)
        self._indir = indir
        self._kilit = threading.Lock()
        self._calisiyor = False

    @property
    def calisiyor(self) -> bool:
        with self._kilit:
            return self._calisiyor

    def baslat(self) -> bool:
        with self._kilit:
            if self._calisiyor:
                return False
            self._calisiyor = True
        threading.Thread(target=self._calis, daemon=True, name="suflor-kalite-modeli-indir").start()
        return True

    def _ilerleme(self, yapilan: int, toplam: int) -> None:
        self.ilerleme.emit(yapilan, toplam)

    def _calis(self) -> None:
        try:
            self._indir(self._ilerleme)
        except Exception as e:  # noqa: BLE001 -- kullanıcıya yalnız sınıf adı çıkar
            with self._kilit:
                self._calisiyor = False
            self.hata.emit(type(e).__name__)
            return
        with self._kilit:
            self._calisiyor = False
        self.hazir.emit()

