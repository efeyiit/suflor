"""T-016: ayarlar panelinin gercek ekran goruntusu (sentetik; masaustu yok -- yalniz panel grab)."""
import sys
from pathlib import Path
KOK = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(KOK))
from PySide6 import QtWidgets
from src.ayarlar import Ayarlar
from src.ui.ayarlar_paneli import AyarlarPaneli
from src.ui.kisayol import altgr_karakteri
app = QtWidgets.QApplication(sys.argv)
p = AyarlarPaneli(Ayarlar(dil="korean", sozluk_yolu="demo/sozluk_ornek.json"), altgr_karakteri=altgr_karakteri)
p.show(); app.processEvents()
p.kisayol_anlik.setText("Ctrl+Alt+T"); app.processEvents()   # AltGr uyarisini goster
p.grab().save(str(Path(__file__).resolve().parent / "ayarlar_paneli.png"))
p.close(); print("kaydedildi")
