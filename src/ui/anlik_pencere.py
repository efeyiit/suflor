"""Suflor -- Anlik ceviri (Snapshot) penceresi, T-014.

Tasarim 2 / Mod 1: kisayola basilir, ekran DONAR (yakalanan kare tam ekran gosterilir), OCR'nin buldugu
metin bloklari cerceveyle isaretlenir, kullanici istediklerini secer, Enter -> secilenler cevrilir, ceviri
bloklarin yanina yazilir. Esc kapatir. Bu pencere pipeline BILMEZ: bloklari `bloklari_goster` ile alir,
secimi `cevir_istendi` ile verir, ceviriyi `ceviriyi_goster` ile alir (baglama `src/pipeline/anlik.py` +
cagiran).

## Sozlesme (K1-K7, olcu: tests/unit/ui/test_anlik_pencere.py)

K1 Geometri: pencere verilen `QScreen.geometry()` ile birebir (tam ekran, cerçevesiz, ustte); kare
   ekranin mantiksal boyutuna olceklenir (dpr 1.0'da 1:1). Blok kutulari kare pikselinden pencere
   koordinatina `_pencereye(rect)` ile cevrilir (kare.rect ofseti + olcek).
K8 (T-018) `dil_goster(dil_degeri, belirsiz)`: durum seridinin solunda dil rozeti ("Japonca" ya da belirsizse
   "Korece?" + ipucu); durum degistirmez. Rozet yoksa (kabuk sabit dil) cizilmez.
K2 Durumlar: `okunuyor` -> (`bloklari_goster`) `secim` -> (secim/Enter/sag tik) `cevriliyor` -> (`ceviriyi_goster`)
   `sonuc` -> (secim degisir) `cevriliyor` ... ; `hata_goster` durum satirina sinif adini yazar, `cevriliyor`u
   `secim`e dondurur. Blok gelmeden Enter hicbir sey yapmaz; bos secimle Enter ipucu yazar, sinyal yok.
K3 Secim: tik (hareket < 4 px) tiklanan blogu ACAR/KAPAR; surukleme dikdortgeni kesisen bloklari EKLER;
   Ctrl+A hepsini secer; secim sirasi = blok listesindeki sira (`secili_bloklar()`).
   T-017 (kullanici: "Enter yerine daha pratik bir sey"): her secim degisikliginden `OTOMATIK_CEVIRI_MS` sonra
   `cevir_istendi` KENDILIGINDEN yayilir (art arda tiklar tek istekte toplanir); SAG TIK ve Enter beklemeden
   yayar. Secim `sonuc`/`cevriliyor` durumunda da duzenlenebilir: degisiklik yeni ceviri ister, eski sonuclar
   silinir (akis eski ceviriyi seq ile dusurur). Secim bosalirsa sinyal yok, sonuclar temizlenir.
K4 Sonuc: `ceviriyi_goster(segmentler, ceviriler)` -> her segment icin Turkce metin, segmentin `bbox`unun
   (kare koordinati; normalizer kaynak bloklarin birlesimini verir) ALTINA (yer yoksa ustune) yarim saydam
   kutuda yazilir; `sonuclar()` -> list[tuple[str, str]] (kaynak, ceviri). Ctrl+C
   ceviri metnini panoya kopyalar (kullanici istegi; pano kullanicinin kendi eylemidir).
K5 Kapanis: Esc ya da `close()` -> `iptal` sinyali TAM BIR KEZ, pencere kapanir; kare/metin diske
   yazilmaz, loglanmaz.
K6 Cizim: `paintEvent` tek karede kare + kutular + sonuclar; 2560x1440 karede < 16 ms (real_check).
   Kare QImage'i `__init__`te bir kez kopyalanir (`Format_BGR888`, `.copy()` -- numpy tamponu serbest kalir).
K7 Klavye odagi: pencere odak ALIR (Esc/Enter icin) -- kenar sekmesinin aksine oyunun odagini bilerek
   calar; kapaninca odak Windows'a doner (oyun kendi pencere sirasina).
"""
from __future__ import annotations

from collections.abc import Sequence

from PySide6.QtCore import QPoint, QRect, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QGuiApplication, QImage, QKeyEvent, QMouseEvent, QPainter, QPaintEvent, QPen, QPixmap, QScreen
from PySide6.QtWidgets import QWidget

from src.contracts.models import Frame, Rect, Segment, TextBlock

__all__ = ["AnlikDurumu", "AnlikPencere"]

TIK_ESIGI_PX = 4
_KUTU = QColor(120, 235, 170)
_SECILI = QColor(255, 214, 102)
_SONUC_ARKA = QColor(13, 17, 22, 225)
_SONUC_YAZI = QColor(230, 245, 234)
_DURUM_ARKA = QColor(22, 27, 33, 230)
_IPUCU = "Tıkla / sürükle: seç → kendiliğinden çevirir   ·   Sağ tık / Enter: hemen çevir   ·   Ctrl+A: hepsi   ·   Ctrl+C: kopyala   ·   Esc: kapat"
OTOMATIK_CEVIRI_MS = 350
_DIL_ADLARI = {"korean": "Korece", "japan": "Japonca", "chinese": "Çince", "english": "İngilizce"}
_ROZET_ARKA = QColor(245, 200, 90, 230)


class AnlikDurumu:
    OKUNUYOR = "okunuyor"
    SECIM = "secim"
    CEVRILIYOR = "cevriliyor"
    SONUC = "sonuc"


class AnlikPencere(QWidget):
    """Donmus kare + blok secimi + ceviri gosterimi. Pipeline bilmez (sinyal/yontem arayuzu)."""

    cevir_istendi = Signal(object)   # list[TextBlock] (secim sirasinda)
    iptal = Signal()

    def __init__(self, ekran: QScreen, kare: Frame, ebeveyn: QWidget | None = None) -> None:
        super().__init__(ebeveyn, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self._ekran = ekran
        self._kare_rect = kare.rect
        g = ekran.geometry()
        self.setGeometry(g)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setMouseTracking(False)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        img = kare.image
        h, w = img.shape[0], img.shape[1]
        qimg = QImage(img.data, w, h, img.strides[0], QImage.Format.Format_BGR888).copy()   # K6: tampon serbest
        self._pix = QPixmap.fromImage(qimg)
        self._olcek_x = g.width() / w if w else 1.0
        self._olcek_y = g.height() / h if h else 1.0
        self._durum = AnlikDurumu.OKUNUYOR
        self._durum_metni = "okunuyor…"
        self._bloklar: list[TextBlock] = []
        self._secili: set[int] = set()
        self._son_secim: list[TextBlock] = []
        self._sonuclar: list[tuple[str, str, QRect]] = []   # kaynak, ceviri, cizim kutusu
        self._basla: QPoint | None = None
        self._surukle: QPoint | None = None
        self._iptal_yayildi = False
        self._otomatik = QTimer(self)
        self._otomatik.setSingleShot(True)
        self._otomatik.setInterval(OTOMATIK_CEVIRI_MS)
        self._otomatik.timeout.connect(self._cevir)
        self._dil_metni = ""

    # -- disa acik durum -----------------------------------------------------------------------
    @property
    def durum(self) -> str:
        return self._durum

    @property
    def durum_metni(self) -> str:
        return self._durum_metni

    @property
    def bloklar(self) -> list[TextBlock]:
        return list(self._bloklar)

    def secili_indeksler(self) -> list[int]:
        return sorted(self._secili)

    def secili_bloklar(self) -> list[TextBlock]:
        return [self._bloklar[i] for i in sorted(self._secili)]

    def sonuclar(self) -> list[tuple[str, str]]:
        return [(k, c) for k, c, _ in self._sonuclar]

    # -- pipeline'dan gelenler ---------------------------------------------------------------------
    def bloklari_goster(self, bloklar: Sequence[TextBlock]) -> None:
        if self._durum in (AnlikDurumu.CEVRILIYOR, AnlikDurumu.SONUC) or self._secili:
            return   # gec gelen okuma sonucu; secim yapilmis, dokunma
        self._bloklar = list(bloklar)
        self._secili.clear()
        self._durum = AnlikDurumu.SECIM
        self._durum_metni = f"{len(self._bloklar)} metin bloğu bulundu — tıkla ya da sürükle, kendiliğinden çevrilir" if self._bloklar else "metin bulunamadı — Esc ile kapat"
        self.update()

    def ceviriyi_goster(self, segmentler: Sequence[Segment], ceviriler: Sequence[str]) -> None:
        if self._durum != AnlikDurumu.CEVRILIYOR or self._otomatik.isActive():
            return   # beklenmeyen ya da secim degisti (yeni istek yolda): eski sonucu basma
        self._sonuclar = []
        for seg, cev in zip(segmentler, ceviriler):
            # yerlesim: segmentin kendi bbox'u (kare koordinatinda; normalizer kaynak bloklarin birlesimini verir).
            # Akis ikinci gecis yaptiysa source_blocks yeniden okunan listeye isaret eder -- secim listesine degil.
            self._sonuclar.append((seg.text, cev, self._pencereye(seg.bbox)))
        self._durum = AnlikDurumu.SONUC
        self._durum_metni = f"{len(self._sonuclar)} çeviri — Ctrl+C kopyala · Esc kapat" if self._sonuclar else "çevrilecek metin yok"
        self.update()

    def dil_goster(self, dil: str, belirsiz: bool) -> None:
        ad = _DIL_ADLARI.get(dil, dil)
        self._dil_metni = f"{ad}? (emin değil — ⚙ Ayarlar'dan seç)" if belirsiz else ad
        self.update()

    @property
    def dil_metni(self) -> str:
        return self._dil_metni

    def hata_goster(self, sinif: str) -> None:
        self._durum_metni = f"hata: {sinif} — Esc ile kapat"
        if self._durum == AnlikDurumu.CEVRILIYOR:
            self._durum = AnlikDurumu.SECIM   # yeniden denenebilir
        self.update()

    # -- koordinat ---------------------------------------------------------------------------------
    def _pencereye(self, r: Rect) -> QRect:
        return QRect(int((r.x - self._kare_rect.x) * self._olcek_x), int((r.y - self._kare_rect.y) * self._olcek_y),
                     max(1, int(r.w * self._olcek_x)), max(1, int(r.h * self._olcek_y)))

    def _blok_indeksi(self, p: QPoint) -> int | None:
        for i, b in enumerate(self._bloklar):
            if self._pencereye(b.bbox).adjusted(-2, -2, 2, 2).contains(p):
                return i
        return None

    # -- etkilesim ---------------------------------------------------------------------------------
    def mousePressEvent(self, e: QMouseEvent) -> None:
        if self._durum == AnlikDurumu.OKUNUYOR:
            return
        if e.button() == Qt.MouseButton.LeftButton:
            self._basla = e.position().toPoint()
            self._surukle = None
        elif e.button() == Qt.MouseButton.RightButton:
            self._otomatik.stop()
            self._cevir()

    def mouseMoveEvent(self, e: QMouseEvent) -> None:
        if self._basla is not None:
            self._surukle = e.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, e: QMouseEvent) -> None:
        if self._basla is None or e.button() != Qt.MouseButton.LeftButton:
            return
        son = e.position().toPoint()
        onceki = set(self._secili)
        if (son - self._basla).manhattanLength() < TIK_ESIGI_PX:
            i = self._blok_indeksi(son)
            if i is not None:
                self._secili ^= {i}
        else:
            kutu = QRect(self._basla, son).normalized()
            for i, b in enumerate(self._bloklar):
                if kutu.intersects(self._pencereye(b.bbox)):
                    self._secili.add(i)
        self._basla = self._surukle = None
        if self._secili != onceki:
            self._secim_degisti()
        self.update()

    def _secim_degisti(self) -> None:
        """T-017: secim degisti -> eski sonuclar silinir, otomatik ceviri sayaci (yeniden) baslar."""
        self._sonuclar = []
        if self._secili:
            self._durum = AnlikDurumu.SECIM
            self._durum_metni = f"{len(self._secili)} blok seçili — çevriliyor…"
            self._otomatik.start()
        else:
            self._otomatik.stop()
            self._durum = AnlikDurumu.SECIM
            self._durum_metni = "seçim boş — bir blok tıkla"
        self.update()

    def keyPressEvent(self, e: QKeyEvent) -> None:
        k, mods = e.key(), e.modifiers()
        if k == Qt.Key.Key_Escape:
            self.close()
        elif k in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._otomatik.stop()
            self._cevir()
        elif k == Qt.Key.Key_A and mods & Qt.KeyboardModifier.ControlModifier and self._durum != AnlikDurumu.OKUNUYOR:
            if self._secili != set(range(len(self._bloklar))):
                self._secili = set(range(len(self._bloklar)))
                self._secim_degisti()
            self.update()
        elif k == Qt.Key.Key_C and mods & Qt.KeyboardModifier.ControlModifier and self._sonuclar:
            QGuiApplication.clipboard().setText("\n".join(c for _, c, _ in self._sonuclar))
            self._durum_metni = "kopyalandı"
            self.update()
        else:
            super().keyPressEvent(e)

    def _cevir(self) -> None:
        if self._durum == AnlikDurumu.OKUNUYOR:
            return
        self._otomatik.stop()
        if not self._secili:
            self._durum_metni = "önce en az bir blok seç (tıkla ya da sürükle)"
            self.update()
            return
        if self._durum in (AnlikDurumu.CEVRILIYOR, AnlikDurumu.SONUC) and self._son_secim == self.secili_bloklar():
            return   # ayni secim icin istek zaten yolda ya da sonucu ekranda
        self._son_secim = self.secili_bloklar()
        self._durum = AnlikDurumu.CEVRILIYOR
        self._durum_metni = "çevriliyor…"
        self.update()
        self.cevir_istendi.emit(list(self._son_secim))

    def closeEvent(self, e: object) -> None:
        self._otomatik.stop()
        if not self._iptal_yayildi:
            self._iptal_yayildi = True
            self.iptal.emit()
        super().closeEvent(e)  # type: ignore[arg-type]

    # -- yerlesim ----------------------------------------------------------------------------------
    def _sonuc_yeri(self, fm: object, metin: str, kutu: QRect, engeller: Sequence[QRect]) -> QRect:
        """Ceviri kutusu icin yer: SAG (dar kutu) -> ALT -> UST -> SOL; secilen kaynak bloklarla ve onceki
        sonuclarla kesismeyen, ekran icinde kalan ilk aday; hicbiri degilse alt (ekrana sikistirilmis)."""
        def kutucuk(gen: int) -> tuple[int, int]:
            g = max(160, min(gen, self.width() - 40))
            r = fm.boundingRect(QRect(0, 0, g - 20, 10_000), int(Qt.TextFlag.TextWordWrap), metin)  # type: ignore[attr-defined]
            return g, r.height() + 16

        gen_yan, yuk_yan = kutucuk(360)
        gen_dik, yuk_dik = kutucuk(max(kutu.width(), 320))
        adaylar = [
            QRect(kutu.right() + 10, kutu.top(), gen_yan, yuk_yan),
            QRect(kutu.left(), kutu.bottom() + 8, gen_dik, yuk_dik),
            QRect(kutu.left(), kutu.top() - 8 - yuk_dik, gen_dik, yuk_dik),
            QRect(kutu.left() - 10 - gen_yan, kutu.top(), gen_yan, yuk_yan),
        ]
        ekran = self.rect()
        for aday in adaylar:
            if ekran.contains(aday) and not any(aday.intersects(e) for e in engeller if e != kutu):
                return aday
        alt = adaylar[1]
        alt.moveLeft(min(max(0, alt.left()), ekran.width() - alt.width()))
        alt.moveTop(min(max(0, alt.top()), ekran.height() - alt.height()))
        return alt

    # -- cizim -------------------------------------------------------------------------------------
    def paintEvent(self, e: QPaintEvent) -> None:
        p = QPainter(self)
        p.drawPixmap(self.rect(), self._pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        for i, b in enumerate(self._bloklar):
            r = self._pencereye(b.bbox)
            if i in self._secili:
                p.fillRect(r, QColor(_SECILI.red(), _SECILI.green(), _SECILI.blue(), 70))
                p.setPen(QPen(_SECILI, 2))
            else:
                p.setPen(QPen(_KUTU, 1))
            p.drawRect(r)
        if self._basla is not None and self._surukle is not None:
            p.setPen(QPen(_SECILI, 1, Qt.PenStyle.DashLine))
            p.drawRect(QRect(self._basla, self._surukle).normalized())
        yazi = QFont("Segoe UI", 12)
        p.setFont(yazi)
        fm = p.fontMetrics()
        engeller = [self._pencereye(b.bbox) for b in self._son_secim]   # secilen kaynak bloklarin ustune yazma
        cizilenler: list[QRect] = []
        for _, cev, kutu in self._sonuclar:
            arka = self._sonuc_yeri(fm, cev, kutu, engeller + cizilenler)
            cizilenler.append(arka)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(_SONUC_ARKA)
            p.drawRoundedRect(QRectF(arka), 8, 8)
            p.setPen(_SONUC_YAZI)
            p.drawText(QRectF(arka).adjusted(10, 8, -10, -8), int(Qt.TextFlag.TextWordWrap), cev)
        # durum seridi (ust orta) + ipucu (alt)
        p.setFont(QFont("Segoe UI", 11))
        durum = f"  {self._durum_metni}  "
        dw = p.fontMetrics().horizontalAdvance(durum) + 20
        serit = QRectF((self.width() - dw) / 2, 14, dw, 32)
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(_DURUM_ARKA); p.drawRoundedRect(serit, 8, 8)
        p.setPen(QColor(207, 227, 245)); p.drawText(serit, int(Qt.AlignmentFlag.AlignCenter), durum)
        if self._dil_metni:
            rozet = f"  {self._dil_metni}  "
            rw = p.fontMetrics().horizontalAdvance(rozet) + 12
            rk = QRectF(serit.left() - rw - 10, 14, rw, 32)
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(_ROZET_ARKA); p.drawRoundedRect(rk, 8, 8)
            p.setPen(QColor(12, 16, 22)); p.drawText(rk, int(Qt.AlignmentFlag.AlignCenter), rozet)
        p.setFont(QFont("Segoe UI", 9))
        iw = p.fontMetrics().horizontalAdvance(_IPUCU) + 24
        alt = QRectF((self.width() - iw) / 2, self.height() - 40, iw, 26)
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(_DURUM_ARKA); p.drawRoundedRect(alt, 6, 6)
        p.setPen(QColor(160, 180, 200)); p.drawText(alt, int(Qt.AlignmentFlag.AlignCenter), _IPUCU)
        p.end()

