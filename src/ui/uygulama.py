"""Suflör -- UI giris noktasi (`calistir`), T-012 K1 (▲ KRT Y1: "uygulama karar verir").

`calistir(argv=None, *, kenar=Kenar.SAG, calistirici=None) -> int`:
  1. `QApplication`: mevcut bir ornek varsa YENIDEN KULLANILIR (pytest-qt
     `qapp`), yoksa `QApplication(list(argv) ya da sys.argv)` kurulur.
  2. `app.setQuitOnLastWindowClosed(False)` -- tepsi/kenar halinde hicbir
     pencere gorunmezken surec yasamali (KRT k4 D); `AnaPencere.kapat()`
     (dugme, tepsi "Çıkış", Alt+F4/WM_CLOSE) `cikis_istendi` yayar ve
     BURADA `app.quit`e baglanir -- kabuk kendisi `quit()` cagirmaz (K1).
  3. `AnaPencere(kenar=kenar)` gosterilir; `calistirici(app, pencere)`
     calistirilir (varsayilan `app.exec()`), donusu cikis kodudur.
`calistirici` ENJEKTE edilebilir: birim testi `exec()` cagirmadan kurulumu
sinar; `quit` baglantisi gercek `app.exec()` + 0 ms sonra `kapat()` ile
olculur (`tests/unit/ui/test_uygulama.py`). Pipeline baglanmaz; o is
`demo/kabuk.py`nindir (sefe ait) ve bu modulu kullanir.
"""
from __future__ import annotations

import sys
from collections.abc import Callable, Sequence

from PySide6.QtWidgets import QApplication

from src.ui.geometri import Kenar
from src.ui.kabuk import AnaPencere

__all__ = ["Calistirici", "calistir"]

Calistirici = Callable[[QApplication, AnaPencere], int]


def _uygulama(argv: Sequence[str] | None) -> QApplication:
    mevcut = QApplication.instance()
    if isinstance(mevcut, QApplication):
        return mevcut
    return QApplication(list(argv) if argv is not None else sys.argv)


def _varsayilan_calistirici(app: QApplication, pencere: AnaPencere) -> int:
    return app.exec()


def calistir(argv: Sequence[str] | None = None, *, kenar: Kenar = Kenar.SAG, calistirici: Calistirici | None = None) -> int:
    """`QApplication` + `AnaPencere`; `cikis_istendi -> app.quit`; `calistirici(app, pencere)` donusu."""
    app = _uygulama(argv)
    app.setQuitOnLastWindowClosed(False)
    pencere = AnaPencere(kenar=kenar)
    pencere.cikis_istendi.connect(app.quit)
    pencere.show()
    return (calistirici if calistirici is not None else _varsayilan_calistirici)(app, pencere)
