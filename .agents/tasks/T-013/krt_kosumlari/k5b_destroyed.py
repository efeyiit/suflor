"""KRT k5b -- PySide6 6.11.2: `self.destroyed.connect(<slot>)` hangi alici turunde GERCEKTEN calisiyor?

    python .agents/tasks/T-013/krt_kosumlari/k5b_destroyed.py

Her varyant icin: (i) ebeveynli servis, ebeveyn.deleteLater + ic ice QEventLoop; (ii) ebeveynsiz servis, del + gc.collect.
Varyantlar: A self'in bagli yontemi (K1'in dogal uygulamasi) · B modul duzeyi serbest fonksiyon (partial ile filtre/id) ·
C BASKA bir QObject'in bagli yontemi (T-012 sekme deseni) · D lambda (self yakalamaz) · E `__del__`
Stdout ASCII.
"""
from __future__ import annotations
import functools, gc, sys, weakref
from PySide6 import QtCore, QtWidgets
import shiboken6

log: list[str] = []


def serbest(ad: str) -> None:
    log.append(ad)


class Temizleyici(QtCore.QObject):
    def __init__(self, ad: str) -> None:
        super().__init__(); self.ad = ad
    def temizle(self) -> None:
        log.append(self.ad)


class Servis(QtCore.QObject):
    def __init__(self, varyant: str, ebeveyn: QtCore.QObject | None) -> None:
        super().__init__(ebeveyn); self.ad = varyant
        if varyant == "A":
            self.destroyed.connect(self._temizle)
        elif varyant == "B":
            self.destroyed.connect(functools.partial(serbest, varyant))
        elif varyant == "C":
            self._t = Temizleyici(varyant); self.destroyed.connect(self._t.temizle)
        elif varyant == "D":
            ad = varyant; self.destroyed.connect(lambda *_: log.append(ad))
    def _temizle(self) -> None:
        log.append(self.ad)
    def __del__(self) -> None:
        if self.ad == "E": log.append("E")


def ic_ice(ms: int) -> None:
    loop = QtCore.QEventLoop(); QtCore.QTimer.singleShot(ms, loop.quit); loop.exec()


def main() -> int:
    app = QtWidgets.QApplication(sys.argv)
    for v in "ABCDE":
        # (i) ebeveynli + deleteLater
        eb = QtCore.QObject(); s = Servis(v, eb); log.clear(); ws = weakref.ref(s)
        eb.deleteLater(); ic_ice(100)
        gecerli = shiboken6.isValid(s); i_kostu = v in log
        # (ii) ebeveynsiz + del + gc
        s2 = Servis(v, None); log.clear(); w2 = weakref.ref(s2); del s2; gc.collect(); ic_ice(50); ii_kostu = v in log
        # (iii) ebeveynli, ebeveyn Python referansi dusuruldu (del eb; gc)
        eb3 = QtCore.QObject(); s3 = Servis(v, eb3); log.clear(); del eb3; gc.collect(); ic_ice(50); iii_kostu = v in log; g3 = shiboken6.isValid(s3)
        # (iv) servis.deleteLater() referans tutulurken
        s4 = Servis(v, None); log.clear(); s4.deleteLater(); ic_ice(100); iv_kostu = v in log; g4 = shiboken6.isValid(s4)
        print(f"{v}: (i) ebeveyn.deleteLater -> kostu={i_kostu} (C++ gecerli={gecerli}) | (ii) del+gc -> kostu={ii_kostu} (sarmalayici None={w2() is None}) | (iii) del ebeveyn+gc -> kostu={iii_kostu} (C++ gecerli={g3}) | (iv) self.deleteLater ref tutulur -> kostu={iv_kostu} (C++ gecerli={g4})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
