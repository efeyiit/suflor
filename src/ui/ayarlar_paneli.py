"""Suflor -- Ayarlar paneli (T-016): dil, kisayollar, sozluk dosyasi, kenar, baslangic durumu.

Kucuk, cercevesiz, MODAL OLMAYAN pencere (tasarim A7: modal yok); ana pencerenin yanina acilir. Alanlar canli
dogrulanir (`Ayarlar.dogrula` + kisayol icin AltGr uyarisi); "Kaydet" yalniz gecerliyken etkin; kaydedince
`kaydedildi(Ayarlar)` yayar ve kapanir. Dosya secimi non-modal `QFileDialog.open()` ile.

## Sozlesme (K1-K4, olcu: tests/unit/ui/test_ayarlar_paneli.py)

K1 Panel `Ayarlar` ile acilir, alanlar onu yansitir; `ayarlar()` o anki alanlardan yeni `Ayarlar` uretir.
K2 Canli dogrulama: her degisiklikte `dogrula()`; sorun varsa durum satiri ilk sorunu gosterir ve Kaydet
   devre disi; ayrica `Ctrl+Alt+<tus>` icin `altgr_karakteri` bos degilse UYARI (kaydetmeyi engellemez --
   servis kayitta zaten `ALTGR_CAKISMA` verir ve kabuk bildirir).
K3 Kaydet -> `kaydedildi(Ayarlar)` tam bir kez, pencere kapanir; Vazgec/Esc -> `vazgecildi`, kapanir,
   sinyal yok. Kaydedilen `Ayarlar.dogrula() == []` (garanti).
K4 Modal yok: `QDialog.exec`/`QMessageBox` yok; dosya secici `open()` (non-modal); panel `Tool` pencere,
   ana pencereyi bloklamaz.
"""
from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (QComboBox, QFileDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QRadioButton,
                               QVBoxLayout, QWidget)

from src.ayarlar import Ayarlar

__all__ = ["AyarlarPaneli"]

_DILLER = [("korean", "Korece"), ("japan", "Japonca"), ("chinese", "Çince"), ("english", "İngilizce")]
_BASLANGIC = [("gorunur", "Pencere açık"), ("tepsi", "Tepside"), ("kenar", "Kenarda (yarım daire)")]
_STIL = (
    "QWidget{background:#0d1116; color:#d8e2ee; font-family:'Segoe UI'; font-size:13px;}"
    "QLineEdit, QComboBox{background:#161b21; border:1px solid #2a3138; border-radius:6px; padding:5px 8px; min-width:220px;}"
    "QLineEdit[gecersiz='true']{border-color:#c0392b;}"
    "QPushButton{background:#161b21; border:1px solid #2a3138; border-radius:6px; padding:6px 14px;}"
    "QPushButton:hover{border-color:#5ec6ff;} QPushButton:disabled{color:#5a6772;}"
    "QPushButton#kaydet{background:#1f4d33; border-color:#2e7d4f;}"
    "QLabel#baslik{font-size:16px; font-weight:600; color:#5ec6ff;} QLabel#durum{color:#f0b35a; font-size:12px;}"
    "QRadioButton{spacing:6px;} QRadioButton::indicator{width:14px; height:14px; border:1px solid #5ec6ff; border-radius:8px; background:#161b21;}"
    "QRadioButton::indicator:checked{background:#5ec6ff;}")


class AyarlarPaneli(QWidget):
    kaydedildi = Signal(object)   # Ayarlar
    vazgecildi = Signal()

    def __init__(self, mevcut: Ayarlar, *, altgr_karakteri: Callable[[int], str] | None = None,
                 ebeveyn: QWidget | None = None) -> None:
        super().__init__(ebeveyn, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self._altgr = altgr_karakteri
        self._kapanis_sinyali_yayildi = False
        self.setWindowTitle("Suflör — Ayarlar")
        self.setStyleSheet(_STIL)

        self.dil = QComboBox()
        for kod, ad in _DILLER:
            self.dil.addItem(ad, kod)
        self.kisayol_anlik = QLineEdit()
        self.kisayol_bolge = QLineEdit()
        self.sozluk_yolu = QLineEdit()
        self.sozluk_yolu.setPlaceholderText("boş = sözlük yok")
        self.gozat = QPushButton("Gözat…")
        self.kenar_sag = QRadioButton("Sağ")
        self.kenar_sol = QRadioButton("Sol")
        self.baslangic = QComboBox()
        for kod, ad in _BASLANGIC:
            self.baslangic.addItem(ad, kod)
        self.durum = QLabel("")
        self.durum.setObjectName("durum")
        self.durum.setWordWrap(True)
        self.kaydet_dugmesi = QPushButton("Kaydet")
        self.kaydet_dugmesi.setObjectName("kaydet")
        self.vazgec_dugmesi = QPushButton("Vazgeç")

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.addRow("Oyun dili", self.dil)
        form.addRow("Anlık çeviri kısayolu", self.kisayol_anlik)
        form.addRow("Bölge izle kısayolu", self.kisayol_bolge)
        yol_satiri = QHBoxLayout(); yol_satiri.addWidget(self.sozluk_yolu, 1); yol_satiri.addWidget(self.gozat)
        form.addRow("Sözlük dosyası", yol_satiri)
        kenar_satiri = QHBoxLayout(); kenar_satiri.addWidget(self.kenar_sag); kenar_satiri.addWidget(self.kenar_sol); kenar_satiri.addStretch(1)
        form.addRow("Yarım daire kenarı", kenar_satiri)
        form.addRow("Açılışta", self.baslangic)
        dugmeler = QHBoxLayout(); dugmeler.addStretch(1); dugmeler.addWidget(self.vazgec_dugmesi); dugmeler.addWidget(self.kaydet_dugmesi)
        baslik = QLabel("Ayarlar"); baslik.setObjectName("baslik")
        duzen = QVBoxLayout(self)
        duzen.setContentsMargins(18, 14, 18, 14); duzen.setSpacing(10)
        duzen.addWidget(baslik); duzen.addLayout(form); duzen.addWidget(self.durum); duzen.addLayout(dugmeler)

        self.yukle(mevcut)
        for w in (self.kisayol_anlik, self.kisayol_bolge, self.sozluk_yolu):
            w.textChanged.connect(self._dogrula)
        self.dil.currentIndexChanged.connect(self._dogrula)
        self.baslangic.currentIndexChanged.connect(self._dogrula)
        self.kenar_sag.toggled.connect(self._dogrula)
        self.gozat.clicked.connect(self._gozat)
        self.kaydet_dugmesi.clicked.connect(self._kaydet)
        self.vazgec_dugmesi.clicked.connect(self.close)
        self._dogrula()

    # -- model <-> alanlar -------------------------------------------------------------------------
    def yukle(self, a: Ayarlar) -> None:
        self.dil.setCurrentIndex(max(0, self.dil.findData(a.dil)))
        self.kisayol_anlik.setText(a.kisayol_anlik)
        self.kisayol_bolge.setText(a.kisayol_bolge)
        self.sozluk_yolu.setText(a.sozluk_yolu or "")
        (self.kenar_sol if a.kenar == "sol" else self.kenar_sag).setChecked(True)
        self.baslangic.setCurrentIndex(max(0, self.baslangic.findData(a.baslangic)))

    def ayarlar(self) -> Ayarlar:
        yol = self.sozluk_yolu.text().strip()
        return Ayarlar(dil=str(self.dil.currentData()), kisayol_anlik=self.kisayol_anlik.text().strip(),
                       kisayol_bolge=self.kisayol_bolge.text().strip(), sozluk_yolu=yol or None,
                       kenar="sol" if self.kenar_sol.isChecked() else "sag", baslangic=str(self.baslangic.currentData()))

    # -- dogrulama --------------------------------------------------------------------------------
    def _dogrula(self) -> None:
        a = self.ayarlar()
        sorunlar = a.dogrula()
        for alan, w in (("kisayol_anlik", self.kisayol_anlik), ("kisayol_bolge", self.kisayol_bolge), ("sozluk_yolu", self.sozluk_yolu)):
            w.setProperty("gecersiz", "true" if any(s.startswith(alan + ":") for s in sorunlar) else "false")
            w.style().unpolish(w); w.style().polish(w)
        uyari = ""
        if not sorunlar and self._altgr is not None:
            from src.ui.kisayol import KisayolServisi
            for etiket, metin in (("Anlık çeviri", a.kisayol_anlik), ("Bölge izle", a.kisayol_bolge)):
                mod, vk = KisayolServisi.kombinasyonu_coz(metin)
                if (mod & 0x3) == 0x3 and not (mod & 0x4) and self._altgr(vk):
                    uyari = f"{etiket} kısayolu bu klavye düzeninde AltGr ile çakışıyor ({metin}); başka bir tuş seç."
                    break
        self.durum.setText(sorunlar[0] if sorunlar else uyari)
        self.kaydet_dugmesi.setEnabled(not sorunlar)

    # -- eylemler ---------------------------------------------------------------------------------
    def _gozat(self) -> None:
        dlg = QFileDialog(self, "Sözlük dosyası", self.sozluk_yolu.text() or "", "JSON (*.json)")
        dlg.setFileMode(QFileDialog.FileMode.ExistingFile)
        dlg.setModal(False)
        dlg.fileSelected.connect(self.sozluk_yolu.setText)
        dlg.open()   # K4: non-modal

    def _kaydet(self) -> None:
        a = self.ayarlar()
        if a.dogrula():
            self._dogrula()
            return
        self._kapanis_sinyali_yayildi = True
        self.kaydedildi.emit(a)
        self.close()

    def keyPressEvent(self, e: QKeyEvent) -> None:
        if e.key() == Qt.Key.Key_Escape:
            self.close()
        elif e.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and self.kaydet_dugmesi.isEnabled():
            self._kaydet()
        else:
            super().keyPressEvent(e)

    def closeEvent(self, e: object) -> None:
        if not self._kapanis_sinyali_yayildi:
            self._kapanis_sinyali_yayildi = True
            self.vazgecildi.emit()
        super().closeEvent(e)  # type: ignore[arg-type]
