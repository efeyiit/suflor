"""T-016 -- AyarlarPaneli K1-K4 (offscreen)."""
from __future__ import annotations

import ast
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from pytestqt.qtbot import QtBot

from src.ayarlar import Ayarlar
from src.ui.ayarlar_paneli import AyarlarPaneli


def panel(qtbot: QtBot, a: Ayarlar | None = None, altgr: object = None) -> AyarlarPaneli:
    p = AyarlarPaneli(a or Ayarlar(), altgr_karakteri=altgr)  # type: ignore[arg-type]
    qtbot.addWidget(p)
    p.show()
    return p


def test_k1_alanlar_ayarlari_yansitir_ve_geri_uretir(qtbot: QtBot) -> None:
    a = Ayarlar(dil="japan", kisayol_anlik="Ctrl+Shift+F5", kisayol_bolge="Alt+Shift+R", sozluk_yolu="D:/s.json", kenar="sol", baslangic="tepsi")
    p = panel(qtbot, a)
    assert p.ayarlar() == a
    assert p.dil.currentText() == "Japonca" and p.kenar_sol.isChecked() and p.baslangic.currentData() == "tepsi"
    p.sozluk_yolu.setText("   ")
    assert p.ayarlar().sozluk_yolu is None   # bos = sozluk yok


def test_k2_canli_dogrulama_kaydeti_kapatir_ve_ilk_sorunu_gosterir(qtbot: QtBot) -> None:
    p = panel(qtbot)
    assert p.kaydet_dugmesi.isEnabled() and p.durum.text() == ""
    p.kisayol_anlik.setText("T")
    assert not p.kaydet_dugmesi.isEnabled() and p.durum.text().startswith("kisayol_anlik:")
    assert p.kisayol_anlik.property("gecersiz") == "true"
    p.kisayol_anlik.setText("Ctrl+Alt+D")
    assert p.kaydet_dugmesi.isEnabled() and p.kisayol_anlik.property("gecersiz") == "false"
    p.kisayol_bolge.setText("ctrl+alt+d")   # ayni kisayol
    assert not p.kaydet_dugmesi.isEnabled() and "aynı" in p.durum.text()


def test_k2_altgr_uyarisi_kaydetmeyi_engellemez(qtbot: QtBot) -> None:
    p = panel(qtbot, altgr=lambda vk: "₺" if vk == ord("T") else "")
    p.kisayol_anlik.setText("Ctrl+Alt+T")
    assert p.kaydet_dugmesi.isEnabled() and "AltGr" in p.durum.text() and "Anlık" in p.durum.text()
    p.kisayol_anlik.setText("Ctrl+Alt+Shift+T")   # Shift'li: AltGr sorulmaz
    assert p.durum.text() == ""


def test_k3_kaydet_sinyal_bir_kez_ve_kapanir(qtbot: QtBot) -> None:
    p = panel(qtbot)
    gelen: list[Ayarlar] = []
    vazgec: list[int] = []
    p.kaydedildi.connect(gelen.append)
    p.vazgecildi.connect(lambda: vazgec.append(1))
    p.dil.setCurrentIndex(p.dil.findData("english"))
    QTest.mouseClick(p.kaydet_dugmesi, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: not p.isVisible(), timeout=1000)
    p.close()
    assert len(gelen) == 1 and gelen[0].dil == "english" and gelen[0].dogrula() == [] and vazgec == []


def test_k3_enter_kaydeder_esc_vazgecer(qtbot: QtBot) -> None:
    p = panel(qtbot)
    with qtbot.waitSignal(p.kaydedildi, timeout=1000):
        QTest.keyClick(p, Qt.Key.Key_Return)
    p2 = panel(qtbot)
    with qtbot.waitSignal(p2.vazgecildi, timeout=1000):
        QTest.keyClick(p2, Qt.Key.Key_Escape)


def test_k3_gecersizken_enter_kaydetmez(qtbot: QtBot) -> None:
    p = panel(qtbot)
    p.kisayol_anlik.setText("Win+D")
    gelen: list[object] = []
    p.kaydedildi.connect(gelen.append)
    QTest.keyClick(p, Qt.Key.Key_Return)
    QTest.mouseClick(p.kaydet_dugmesi, Qt.MouseButton.LeftButton)
    assert gelen == [] and p.isVisible()


def test_k4_modal_yok_ast() -> None:
    kaynak = Path("src/ui/ayarlar_paneli.py").read_text(encoding="utf-8")
    agac = ast.parse(kaynak)
    cagrilar = {n.func.attr for n in ast.walk(agac) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    adlar = {n.id for n in ast.walk(agac) if isinstance(n, ast.Name)} | {n.attr for n in ast.walk(agac) if isinstance(n, ast.Attribute)}
    assert "exec" not in cagrilar and "exec_" not in cagrilar and "QMessageBox" not in adlar and "QDialog" not in adlar
    assert "open" in cagrilar   # non-modal dosya secici
    assert "print(" not in kaynak and "logging" not in kaynak


def test_k4_tool_penceresi(qtbot: QtBot) -> None:
    p = panel(qtbot)
    assert bool(p.windowFlags() & Qt.WindowType.Tool) and not p.isModal()
