"""Suflör — ürün kabuğu: kısayollar, Anlık Çeviri ve otomatik Bölge İzleme.

Çalıştır:  python demo/kabuk.py [japan|korean|chinese|english] [sag|sol]
           (argüman verilmezse %APPDATA%/Suflor/ayarlar.json — ⚙ düğmesiyle düzenlenir; dil/sözlük değişince
            motorlar arka planda yeniden yüklenir)

Sağ üstteki üç düğme (kullanıcı isteği, 11 Eylül 2026):
  ✕  Kapat        — uygulama tamamen kapanır (tepside kalıntı yok)
  ▾  Tepsiye al   — pencere gizlenir, uygulama sistem tepsisinde çalışır; tepsi ikonuna tık → geri gelir
  ◐  Kenara al    — masaüstünde pencere görünmez; ekran kenarında küçük YARIM DAİRE durur.
                    İmleç üstüne gelince açılır: "Anlık çeviri" ve "Bölge izle" seçenekleri.

Kısayollar (tepsideyken/kenardayken de): Ctrl+Alt+D anlık çeviri · Ctrl+Alt+R bölge izle.

Anlık çeviri (Snapshot): imlecin bulunduğu monitör DONAR (yakalanan kare tam ekran), OCR metin bloklarını
çerçeveler; tıkla/sürükle ile seç → seçim KENDİLİĞİNDEN tek bir metin olarak Türkçe'ye çevrilir (satır satır
değil — T-017), yanına yazılır; sağ tık / Enter beklemeden çevirir; seçimi değiştirince yeniden çevrilir; Esc kapatır. OCR + çeviri arka plan thread'inde (UI donmaz). Modeller açılışta arka planda yüklenir.
Bölge izle: dikdörtgen çiz → alan değişince otomatik OCR ve Türkçe çeviri. Üstte kalan kompakt şeritte
çeviri görünür; kaynak metin isteğe bağlı açılır; duraklatma, alanı değiştirme ve kapatma doğrudan erişilebilir.

Dil (T-018): Ayarlar'da "Otomatik" (varsayılan) ise OCR modeli oyundan ALGILANIR — ilk Snapshot'ta mevcut dilin
(son algılanan / İngilizce) okuması güvenliyse başka model denenmez; değilse diğer üç model sırayla denenir, kazanan
oturum boyunca kalır (sonraki Snapshot tek okuma). Diğer modeller açılıştan sonra arka planda ısıtılır. Snapshot
penceresinde dil rozeti; emin değilse "Korece? (⚙ Ayarlar'dan seç)". Sabit dil seçilirse algılama yok.

Model: models/nllb-200-distilled-600M-ct2-int8/ (yoksa durum satırında ModelMissingError; kabuk çalışır).
Hiçbir OCR/çeviri metni konsola/diske yazılmaz.
"""

from __future__ import annotations

import ctypes
import sqlite3
import sys
import threading
from ctypes import wintypes
from collections.abc import Sequence
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6 import QtCore, QtGui, QtWidgets  # noqa: E402

from demo.bolge_izle import SecimKatmani  # noqa: E402
from src.capture.monitors import union_bbox  # noqa: E402
from src.capture.service import CaptureService, MssBackend  # noqa: E402
from src.contracts.errors import TranslatorError  # noqa: E402
from src.contracts.models import Frame, Rect  # noqa: E402
from src.ocr.rapid_engine import OcrLanguage  # noqa: E402
from src.pipeline.anlik import AnlikAkisi  # noqa: E402
from src.pipeline.dil_secici import DilSecici  # noqa: E402
from src.ayarlar import Ayarlar, AyarlarDeposu  # noqa: E402
from src.pipeline.motorlar import MotorDeposu, gercek_fabrikalar  # noqa: E402
from src.model_yonetimi.kalite_modeli import KaliteModeliYoneticisi  # noqa: E402
from src.model_yonetimi.indirici import KaliteModeliIndirici  # noqa: E402
from src.store.translation_memory import TranslationMemory  # noqa: E402
from src.translate.hedef_duzeltici import HedefDuzeltici  # noqa: E402
from src.ui.anlik_pencere import AnlikPencere  # noqa: E402
from src.ui.bolge_pencere import BolgePenceresi  # noqa: E402
from src.ui.geometri import Kenar  # noqa: E402
from src.ui.kabuk import AnaPencere, KabukDurumu  # noqa: E402
from src.ui.uygulama import calistir  # noqa: E402
from src.ui.yakalama_gizliligi import YakalamaGizliligi  # noqa: E402

KOK = Path(__file__).resolve().parent.parent
MODEL_DIZINI = KOK / "models" / "nllb-200-distilled-600M-ct2-int8"
KALITE_YONETICISI = KaliteModeliYoneticisi(KOK / "models", KOK / "runtime")
SOZLUK = KOK / "demo" / "sozluk_ornek.json"
NLLB_KODU = {OcrLanguage.JAPAN: "jpn_Jpan", OcrLanguage.KOREAN: "kor_Hang", OcrLanguage.CHINESE: "zho_Hans", OcrLanguage.ENGLISH: "eng_Latn"}
DIL_ADI = {OcrLanguage.JAPAN: "Japonca", OcrLanguage.KOREAN: "Korece", OcrLanguage.CHINESE: "Çince", OcrLanguage.ENGLISH: "İngilizce"}
OTOMATIK_BASLANGIC = OcrLanguage.ENGLISH  # ilk kurulumda en yaygin oyun dili; kazanan oturum boyunca hatirlanir


def _guvenli_tam_yakala(
    servis: CaptureService,
    monitor_index: int,
    gizlilik: YakalamaGizliligi,
    pencereler: Sequence[QtWidgets.QWidget],
) -> Frame:
    """Tam ekran yakalamayi Suflor pencereleri disarida kalacak sekilde yapar."""
    return gizlilik.yakala(lambda: servis.capture_full(monitor_index), pencereler)


def _fiziksel_imlec() -> tuple[int, int]:
    """İmlecin FİZİKSEL piksel konumu (monitör dikdörtgenleri fiziksel; QCursor.pos mantıksal)."""
    p = wintypes.POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(p))
    return int(p.x), int(p.y)


def _bagla(app: QtWidgets.QApplication, pencere: AnaPencere, dil: OcrLanguage | None, sozluk_yolu: Path | None) -> int:
    """`dil=None` -> otomatik algilama (T-018)."""
    servis = CaptureService(MssBackend())
    gizlilik = YakalamaGizliligi()
    gizlilik.uygulamaya_kur(app)
    try:
        hafiza: TranslationMemory | None = TranslationMemory()
    except (OSError, sqlite3.Error):
        hafiza = None
        pencere.durum_goster("çeviri hafızası açılamadı — uygulama hafızasız devam ediyor")
    pencereler: list[QtWidgets.QWidget] = []
    acik_katman: list[SecimKatmani] = []
    acik_anlik: list[tuple[AnlikPencere, AnlikAkisi]] = []
    acik_bolge: list[BolgePenceresi] = []
    motor: dict[str, object] = {}   # depo, duzeltici, dil, secici -- ayar degisince yeniden kurulur
    sozluk_kutusu: list[Path | None] = [sozluk_yolu]

    def ocr_fabrikasi(d: OcrLanguage) -> object:
        from src.ocr.rapid_engine import RapidOcrEngine
        return RapidOcrEngine(language=d, threads=8, allow_download=True)

    def motorlari_kur(yeni_dil: OcrLanguage | None, yeni_sozluk: Path | None) -> None:
        eski = motor.get("depo")
        if isinstance(eski, MotorDeposu):
            eski.kapat()
        sozluk = yeni_sozluk if yeni_sozluk is not None and yeni_sozluk.exists() else None
        kalite_yollari = (
            (KALITE_YONETICISI.executable_path, KALITE_YONETICISI.model_path)
            if KALITE_YONETICISI.hazir_mi else None
        )
        if yeni_dil is None:
            onceki = motor.get("secici")
            baslangic = onceki.mevcut if isinstance(onceki, DilSecici) else OTOMATIK_BASLANGIC
            secici = DilSecici(ocr_fabrikasi, NLLB_KODU, baslangic=baslangic)   # type: ignore[arg-type]
            motor["secici"] = secici
            ocr_f, cev_f, soz_f = gercek_fabrikalar(
                baslangic, MODEL_DIZINI, sozluk, kalite_yollari=kalite_yollari
            )
            fabrikalar = (lambda: secici.motor(secici.mevcut), cev_f, soz_f)   # depo OCR'i = secicinin motoru (tek kopya)
        else:
            motor.pop("secici", None)
            fabrikalar = gercek_fabrikalar(
                yeni_dil, MODEL_DIZINI, sozluk, kalite_yollari=kalite_yollari
            )
        depo = MotorDeposu(fabrikalar)
        motor["depo"], motor["dil"] = depo, yeni_dil
        motor["duzeltici"] = HedefDuzeltici.dosyadan(sozluk) if sozluk is not None else HedefDuzeltici()   # T-015
        pencere.durum_goster("modeller yükleniyor…")

        def hazir() -> None:
            pencere.durum_goster("")
            secici = motor.get("secici")
            if isinstance(secici, DilSecici) and motor.get("depo") is depo:
                digerleri = [d for d in OcrLanguage if d is not secici.mevcut]
                threading.Thread(target=secici.isit, args=(digerleri,), daemon=True, name="suflor-dil-isitma").start()

        depo.hazir.connect(hazir)
        depo.hata.connect(lambda sinif: pencere.durum_goster(f"model yüklenemedi: {sinif} — models/ dizinini kontrol et"))
        depo.baslat()

    indirici = KaliteModeliIndirici(KALITE_YONETICISI.indir, pencere)

    def kalite_ilerleme(yapilan: object, toplam: object) -> None:
        pencere.kalite_modeli_durumu("indiriliyor", int(yapilan), int(toplam))

    def kalite_hazir() -> None:
        pencere.kalite_modeli_durumu("hazir")
        mevcut_dil = motor.get("dil")
        motorlari_kur(mevcut_dil if isinstance(mevcut_dil, OcrLanguage) else None, sozluk_kutusu[0])

    def kalite_hata(_sinif: str) -> None:
        pencere.kalite_modeli_durumu("hata")

    def kalite_indir() -> None:
        if KALITE_YONETICISI.hazir_mi:
            kalite_hazir()
            return
        pencere.kalite_modeli_durumu("indiriliyor", 0, KALITE_YONETICISI.toplam_boyut)
        indirici.baslat()

    indirici.ilerleme.connect(kalite_ilerleme)
    indirici.hazir.connect(kalite_hazir)
    indirici.hata.connect(kalite_hata)
    pencere.kalite_modeli_indir_istendi.connect(kalite_indir)
    pencere.kalite_modeli_durumu("hazir" if KALITE_YONETICISI.hazir_mi else "eksik")

    motorlari_kur(dil, sozluk_yolu)

    def ayarlar_degisti(a: object) -> None:
        if isinstance(a, Ayarlar):
            yol = Path(a.sozluk_yolu) if a.sozluk_yolu else None
            yeni_dil = None if a.dil == "auto" else OcrLanguage(a.dil)
            if yeni_dil != motor["dil"] or yol != sozluk_kutusu[0]:
                sozluk_kutusu[0] = yol
                motorlari_kur(yeni_dil, yol)

    pencere.ayarlar_degisti.connect(ayarlar_degisti)

    # -- Anlık çeviri (Snapshot) ---------------------------------------------------------------
    def anlik_cevir() -> None:
        if acik_bolge and acik_bolge[0].isVisible():
            pencere.durum_goster("Bölge izleme açık — önce onu kapat veya duraklat")
            acik_bolge[0].activateWindow()
            return
        if acik_anlik and acik_anlik[0][0].isVisible():
            return   # zaten açık
        acik_anlik.clear()
        depo = motor["depo"]
        assert isinstance(depo, MotorDeposu)
        duzeltici = motor["duzeltici"]
        assert isinstance(duzeltici, HedefDuzeltici)
        secici = motor.get("secici")
        dil = secici.mevcut if isinstance(secici, DilSecici) else motor["dil"]
        assert isinstance(dil, OcrLanguage)
        if not depo.hazir_mi:
            pencere.durum_goster("modeller henüz yüklenmedi — birkaç saniye sonra tekrar dene")
            return
        fx, fy = _fiziksel_imlec()
        monitorler = servis.monitors
        idx = next((i for i, m in enumerate(monitorler) if m.x <= fx < m.x + m.w and m.y <= fy < m.y + m.h), 0)
        ekran = QtGui.QGuiApplication.screenAt(QtGui.QCursor.pos()) or QtGui.QGuiApplication.primaryScreen()
        try:
            kare = _guvenli_tam_yakala(servis, idx, gizlilik, app.topLevelWidgets())
        except TranslatorError as hata:
            pencere.durum_goster(f"yakalama hatası: {type(hata).__name__}")
            return
        sekme_gizlendi = pencere.sekme.isVisible()
        if sekme_gizlendi:
            pencere.sekme.hide()
        akis = AnlikAkisi(secici.motor(dil) if isinstance(secici, DilSecici) else depo.ocr, depo.cevirici, depo.sozluk,
                          kaynak_dili=NLLB_KODU[dil], duzeltici=duzeltici,
                          dil_secici=secici if isinstance(secici, DilSecici) else None, hafiza=hafiza)
        anlik = AnlikPencere(ekran, kare)
        akis.dil_algilandi.connect(anlik.dil_goster)

        def dil_bildir(kod: str, belirsiz: bool) -> None:
            ad = DIL_ADI.get(OcrLanguage(kod), kod)
            pencere.durum_goster(f"dil: {ad}" + (" (emin değil — ⚙ Ayarlar'dan seç)" if belirsiz else " (algılandı)"))

        akis.dil_algilandi.connect(dil_bildir)
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
        if acik_anlik and acik_anlik[0][0].isVisible():
            pencere.durum_goster("Anlık çeviri açık — önce onu kapat")
            acik_anlik[0][0].activateWindow()
            return
        if acik_bolge and acik_bolge[0].isVisible():
            acik_bolge[0].activateWindow()
            return
        acik_bolge.clear()
        if acik_katman and acik_katman[0].isVisible():
            acik_katman[0].activateWindow()
            return
        acik_katman.clear()
        depo = motor["depo"]
        assert isinstance(depo, MotorDeposu)
        if not depo.hazir_mi:
            pencere.durum_goster("modeller henüz yüklenmedi — birkaç saniye sonra tekrar dene")
            return
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
            duzeltici = motor["duzeltici"]
            assert isinstance(duzeltici, HedefDuzeltici)
            secici = motor.get("secici")
            dil = secici.mevcut if isinstance(secici, DilSecici) else motor["dil"]
            assert isinstance(dil, OcrLanguage)
            akis = AnlikAkisi(
                secici.motor(dil) if isinstance(secici, DilSecici) else depo.ocr,
                depo.cevirici,
                depo.sozluk,
                kaynak_dili=NLLB_KODU[dil],
                duzeltici=duzeltici,
                dil_secici=secici if isinstance(secici, DilSecici) else None,
                hafiza=hafiza,
            )
            izleme = BolgePenceresi(servis, bolge, akis)
            acik_bolge.append(izleme)

            def yeniden_sec() -> None:
                QtCore.QTimer.singleShot(0, bolge_izle)

            izleme.yeniden_sec_istendi.connect(yeniden_sec)
            izleme.kapatildi.connect(lambda: acik_bolge.clear())
            akis.dil_algilandi.connect(
                lambda kod, belirsiz: pencere.durum_goster(
                    f"bölge izleme · dil: {DIL_ADI.get(OcrLanguage(kod), kod)}"
                    + (" (emin değil)" if belirsiz else "")
                )
            )
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
        for bolge in acik_bolge:
            bolge.close()
        depo = motor.get("depo")
        if isinstance(depo, MotorDeposu):
            depo.kapat()
        if hafiza is not None:
            hafiza.close()

    pencere.anlik_cevir_istendi.connect(anlik_cevir)
    pencere.bolge_izle_istendi.connect(bolge_izle)
    pencere.cikis_istendi.connect(cikis)
    return app.exec()


def main() -> int:
    args = [a.lower() for a in sys.argv[1:]]
    depo = AyarlarDeposu()                      # %APPDATA%/Suflor/ayarlar.json
    ayarlar = depo.yukle().ayarlar
    dil: OcrLanguage | None = next((OcrLanguage(a) for a in args if a in {d.value for d in OcrLanguage}),
                                   None if ayarlar.dil == "auto" else OcrLanguage(ayarlar.dil))
    kenar = Kenar.SOL if "sol" in args else (Kenar.SAG if "sag" in args else Kenar(ayarlar.kenar))
    sozluk_yolu = Path(ayarlar.sozluk_yolu) if ayarlar.sozluk_yolu else (SOZLUK if SOZLUK.exists() else None)
    return calistir(sys.argv, kenar=kenar, calistirici=lambda app, p: _bagla(app, p, dil, sozluk_yolu), ayarlar_deposu=depo)


if __name__ == "__main__":
    raise SystemExit(main())
