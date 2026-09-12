"""ŞEFE AİT — test ortamı pozitif kontrolü: offscreen platform gerçekten etkin mi."""
from __future__ import annotations

import os

from PySide6 import QtGui, QtWidgets


def test_offscreen_platform_ayarli() -> None:
    assert os.environ.get("QT_QPA_PLATFORM") == "offscreen"


def test_qapp_offscreen_ekran_veriyor(qapp: QtWidgets.QApplication) -> None:
    ekran = QtGui.QGuiApplication.primaryScreen()
    assert ekran is not None and ekran.availableGeometry().width() > 0
    assert qapp.platformName() == "offscreen"
