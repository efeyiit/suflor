"""Suflör — uygulama gösterimi: ürün kabuğu (T-012) + kısayollar (T-013) + Anlık çeviri (T-014) + Bölge izle (T-005).

Çalıştır:  python demo/kabuk.py [japan|korean|chinese|english] [sag|sol]

Sağ üstteki üç düğme (kullanıcı isteği, 11 Eylül 2026):
  ✕  Kapat        — uygulama tamamen kapanır (tepside kalıntı yok)
  ▾  Tepsiye al   — pencere gizlenir, uygulama sistem tepsisinde çalışır; tepsi ikonuna tık → geri gelir
  ◐  Kenara al    — masaüstünde pencere görünmez; ekran kenarında küçük YARIM DAİRE durur.
                    İmleç üstüne gelince açılır: "Anlık çeviri" ve "Bölge izle" seçenekleri.

Kısayollar (tepsideyken/kenardayken de): Ctrl+Alt+D anlık çeviri · Ctrl+Alt+R bölge izle.

Anlık çeviri (Snapshot): imlecin bulunduğu monitör DONAR (yakalanan kare tam ekran), OCR metin bloklarını
çerçeveler, tıkla/sürükle ile seç, Enter → seçilenler Türkçe'ye çevrilir ve blokların altına yazılır;
Esc kapatır. OCR + çeviri arka plan thread'inde (UI donmaz). Modeller açılışta arka planda yüklenir.
Bölge izle: dikdörtgen çiz → canlı bölge görünümü (T-005; OCR/çeviri için demo/canli_cevir.py).

Model: models/nllb-200-distilled-600M-ct2-int8/ (yoksa durum satırında ModelMissingError; kabuk çalışır).
Hiçbir OCR/çeviri metni konsola/diske yazılmaz.
"""

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6 import QtGui, QtWidgets  # noqa: E402

from demo.bolge_izle import IzlemePenceresi, SecimKatmani  # noqa: E402
from src.capture.monitors import union_bbox  # noqa: E402
from src.capture.service import CaptureService, MssBackend  # noqa: E402
from src.contracts.errors import TranslatorError  # noqa: E402
from src.contracts.models import Rect  # noqa: E402
from src.ocr.rapid_engine import OcrLanguage  # noqa: E402
from src.pipeline.anlik import AnlikAkisi  # noqa: E402
from src.pipeline.motorlar import MotorDeposu, gercek_fabrikalar  # noqa: E402
from src.ui.anlik_pencere import AnlikPencere  # noqa: E402
from src.ui.geometri import Kenar  # noqa: E402
from src.ui.kabuk import AnaPencere, KabukDurumu  # noqa: E402
from src.ui.uygulama import calistir  # noqa: E402

KOK = Path(__file__).resolve().parent.parent
MODEL_DIZINI = KOK / "models" / "nllb-200-distilled-600M-ct2-int8"
SOZLUK = KOK / "demo" / "sozluk_ornek.json"
NLLB_KODU = {OcrLanguage.JAPAN: "jpn_Jpan", OcrLanguage.KOREAN: "kor_Hang", OcrLanguage.CHINESE: "zho_Hans", OcrLanguage.ENGLISH: "eng_Latn"}


def _fiziksel_imlec() -> tuple[int, int]:
    """İmlecin FİZİKSEL piksel konumu (monitör dikdörtgenleri fiziksel; QCursor.pos mantıksal)."""
    p = wintypes.POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(p))
    return int(p.x), int(p.y)


def _bagla(app: QtWidgets.QApplication, pencere: AnaPencere, dil: OcrLanguage) -> int:
    servis = CaptureService(MssBackend())
    depo = MotorDeposu(gercek_fabrikalar(dil, MODEL_DIZINI, SOZLUK if SOZLUK.exists() else None))
    pencereler: list[QtWidgets.QWidget] = []
    acik_katman: list[SecimKatmani] = []
    acik_anlik: list[tuple[AnlikPencere, AnlikAkisi]] = []

    pencere.durum_goster("modeller yükleniyor…")
    depo.hazir.connect(lambda: pencere.durum_goster(""))
    depo.hata.connect(lambda sinif: pencere.durum_goster(f"model yüklenemedi: {sinif} — models/ dizinini kontrol et"))
    depo.baslat()

    # -- Anlık çeviri (Snapshot) ---------------------------------------------------------------
    def anlik_cevir() -> None:
        if acik_anlik and acik_anlik[0][0].isVisible():
            return   # zaten açık
        acik_anlik.clear()
        if not depo.hazir_mi:
            pencere.durum_goster("modeller henüz yüklenmedi — birkaç saniye sonra tekrar dene")
            return
        fx, fy = _fiziksel_imlec()
        monitorler = servis.monitors
        idx = next((i for i, m in enumerate(monitorler) if m.x <= fx < m.x + m.w and m.y <= fy < m.y + m.h), 0)
        ekran = QtGui.QGuiApplication.screenAt(QtGui.QCursor.pos()) or QtGui.QGuiApplication.primaryScreen()
        try:
            kare = servis.capture_full(idx)
        except TranslatorError as hata:
            pencere.durum_goster(f"yakalama hatası: {type(hata).__name__}")
            return
        sekme_gizlendi = pencere.sekme.isVisible()
        if sekme_gizlendi:
            pencere.sekme.hide()
        akis = AnlikAkisi(depo.ocr, depo.cevirici, depo.sozluk, kaynak_dili=NLLB_KODU[dil])
        anlik = AnlikPencere(ekran, kare)
        akis.bloklar_hazir.connect(anlik.bloklari_goster)
        akis.ceviri_hazir.connect(anlik.ceviriyi_goster)
        akis.hata.connect(anlik.hata_goster)
        anlik.cevir_istendi.connect(akis.cevir)

        def kapandi() -> None:
            akis.iptal()
            akis.kapat()
            if sekme_gizlendi and pencere.durum == KabukDurumu.KENAR and not pencere.kapandi:
                pencere.sekme.show()

        anlik.iptal.connect(kapandi)
        acik_anlik.append((anlik, akis))
        anlik.show()
        anlik.activateWindow()
        anlik.setFocus()
        akis.oku(kare)

    # -- Bölge izle ----------------------------------------------------------------------------
    def bolge_izle() -> None:
        if acik_katman and acik_katman[0].isVisible():
            acik_katman[0].activateWindow()
            return
        acik_katman.clear()
        birlesim = union_bbox(servis.monitors)
        if birlesim is None:
            return
        katman = SecimKatmani(birlesim)
        acik_katman.append(katman)
        sekme_gizlendi = pencere.sekme.isVisible()
        if sekme_gizlendi:
            pencere.sekme.hide()

        def bitti() -> None:
            if sekme_gizlendi and pencere.durum == KabukDurumu.KENAR and not pencere.kapandi:
                pencere.sekme.show()

        def secildi(bolge: Rect) -> None:
            izleme = IzlemePenceresi(servis, bolge)
            izleme.resize(max(420, min(900, bolge.w)), max(220, min(560, bolge.h + 40)))
            izleme.show()
            pencereler.append(izleme)
            bitti()

        katman.secildi.connect(secildi)
        katman.iptal.connect(bitti)
        katman.show()
        katman.activateWindow()
        pencereler.append(katman)

    def cikis() -> None:
        for w in pencereler:
            w.close()
        for anlik, _ in acik_anlik:
            anlik.close()
        depo.kapat()

    pencere.anlik_cevir_istendi.connect(anlik_cevir)
    pencere.bolge_izle_istendi.connect(bolge_izle)
    pencere.cikis_istendi.connect(cikis)
    return app.exec()


def main() -> int:
    args = [a.lower() for a in sys.argv[1:]]
    dil = next((OcrLanguage(a) for a in args if a in {d.value for d in OcrLanguage}), OcrLanguage.KOREAN)
    kenar = Kenar.SOL if "sol" in args else Kenar.SAG
    return calistir(sys.argv, kenar=kenar, calistirici=lambda app, p: _bagla(app, p, dil))


if __name__ == "__main__":
    raise SystemExit(main())
