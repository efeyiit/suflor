"""Suflor -- Anlik ceviri (Snapshot) akisi, T-014.

Tasarim 5.4 Mod 1:  kare -> OCR -> satir birlestir -> [kullanici secer] -> secimi birlestir -> sozluk -> ceviri.
Bu modul UI cizmez; UI (`src/ui/anlik_pencere.py`) sinyalleri dinler. Butun agir is (OCR, ceviri)
`AnlikAkisi`nin kendi `QThread`inde kosar; UI thread'i yalnizca sinyal alir (K1).

## Sozlesme (K1-K6, olcu: tests/unit/pipeline/test_anlik.py)

K1 UI thread bloklanmaz: `oku(kare)` ve `cevir(bloklar)` hemen doner; is `_Isci` nesnesinde, ayri thread'de.
   `oku`/`cevir` yalniz sinyal kuyruklar (QueuedConnection). Olcu: cagri suresi < 5 ms, sonuc sonra gelir.
K2 Sira korumasi (tasarim 5.5 `seq`): her `oku` ve her `cevir` yeni bir `seq` alir; eski bir okumanin ya da
   onceki bir cevirinin sonucu YAYILMAZ (dusurulur) -- T-017: secim degisince yeniden ceviri, eski ceviri gec
   gelse bile ekrana basilmaz. `iptal()` sonrasi gelen sonuc dusurulur. Olcu: yavas sahte OCR + ikinci `oku` -> yalniz ikincinin bloklari gelir.
K3 Zincir: `oku` -> `recognize(kare, preset)` -> `satirlari_birlestir` -> `bloklar_hazir(list[TextBlock])`.
   `cevir(bloklar)` -> IKINCI GECIS: secilen bloklarin birlesik kutusu (+kenar payi) son kareden kirpilir ve
   yeniden `recognize` edilir (olculdu: tam kare tespiti kutulari gevsek veriyor -- 2560 px kare icin dedektor
   kucultuyor; gevsek kutular normalizer'in konusmaci satirini paragrafa yapistirmasina yol aciyordu; kirpilmis
   gecis bolge yakalamayla ayni siki kutulari verir) -> `satirlari_birlestir` -> `secimi_birlestir`
   (T-017: secim = metin; satirlar okuma sirasinda TEK segmente birlesir, yalniz buyuk dikey bosluk ve
   konusmaci satiri boler -- gercek oyunda satir satir ceviri metnin butunlugunu bozuyordu; `normalize` yerine)
   -> sozluk varsa `lookup_segments` + `terimleri_gom` -> `translate(TranslationRequest(gomulu, kaynak_dili, "tr"))`
   -> `duzeltici` varsa ciktida `HedefDuzeltici.duzelt` (T-015: "Elder Marcus" -> "İhtiyar Marcus")
   -> `ceviri_hazir(segmentler, ceviriler)`; segment `bbox`leri KARE koordinatinda (UI yerlesim icin bunu kullanir).
   Kare yoksa (`oku` yapilmadan `cevir`) ikinci gecis atlanir, verilen bloklar kullanilir.
   `ceviri_hazir`daki segmentler GOMULU DEGIL, birlestirme ciktisi (UI kaynak metni kullaniciya gosterir);
   gomme yalniz modele giden istekte. Bos secim -> `ceviri_hazir([], [])` hemen (model cagrilmaz).
K4 Hata: `TranslatorError` (OcrError, ModelMissingError, ProviderUnavailable, ...) -> `hata(sinif_adi)`;
   metin, kare ya da ceviri ASLA sinyal disina/loga cikmaz (PROTOKOL 7). Baska istisna da `hata` olur
   (sinif adi), thread yasamaya devam eder (bir hata akisi oldurmez).
K5 Kapanis: `kapat()` thread'i durdurur ve bekler (<= 2000 ms); ikinci `kapat()` sessiz. Nesne silinirken de.
K6 Motorlar enjekte: `OcrEngine`, `TranslationProvider`, `GlossaryStore | None`; akis dosya/ag bilmez.

Thread notu: `_Isci` motorlari kendi thread'inde cagirir; RapidOCR/CTranslate2 inference GIL'i birakir
(tasarim 5.5). Motor nesneleri akisa verilmeden once UI thread'inde kurulmus olabilir -- kullanim tek
thread'den (isci) yapildigi icin guvenlidir; ayni motor nesnesini iki akisa verme.
"""
from __future__ import annotations

from collections.abc import Sequence

from PySide6.QtCore import QObject, Qt, QThread, Signal, Slot

from src.contracts.errors import TranslatorError
from src.contracts.interfaces import OcrEngine, TranslationProvider
from src.contracts.models import Frame, OcrPreset, Rect, Segment, TextBlock, TranslationRequest
from src.pipeline.secim import secimi_birlestir
from src.ocr.satir_birlestirici import satirlari_birlestir
from src.translate.hedef_duzeltici import HedefDuzeltici
from src.translate.sozluk import GlossaryStore, terimleri_gom

__all__ = ["AnlikAkisi", "cevir_yap", "ikinci_gecis", "oku_yap"]

_KAPANIS_BEKLEME_MS = 2000


class _Isci(QObject):
    """Isci thread'inde yasayan nesne: OCR ve ceviriyi kosar, ham sonucu seq ile geri yayar."""

    okundu = Signal(int, object)          # seq, list[TextBlock]
    cevrildi = Signal(int, object, object)  # seq, list[Segment], list[str]
    hata = Signal(int, str)               # seq, istisna sinif adi

    def __init__(self, ocr: OcrEngine, cevirici: TranslationProvider, sozluk: GlossaryStore | None,
                 kaynak_dili: str, preset: OcrPreset, duzeltici: HedefDuzeltici | None = None) -> None:
        super().__init__()
        self._ocr, self._cevirici, self._sozluk = ocr, cevirici, sozluk
        self._kaynak_dili, self._preset, self._duzeltici = kaynak_dili, preset, duzeltici
        self._son_kare: Frame | None = None

    @Slot(int, object)
    def oku(self, seq: int, kare: Frame) -> None:
        self._son_kare = kare
        try:
            bloklar = oku_yap(self._ocr, kare, self._preset)
        except Exception as e:  # noqa: BLE001 -- K4: her istisna sinif adiyla sinyal, thread yasar
            self.hata.emit(seq, type(e).__name__)
            return
        self.okundu.emit(seq, bloklar)

    @Slot(int, object)
    def cevir(self, seq: int, bloklar: Sequence[TextBlock]) -> None:
        try:
            segmentler, ceviriler = cevir_yap(self._cevirici, self._sozluk, bloklar, self._kaynak_dili, self._preset,
                                              ocr=self._ocr, kare=self._son_kare, duzeltici=self._duzeltici)
        except Exception as e:  # noqa: BLE001
            self.hata.emit(seq, type(e).__name__)
            return
        self.cevrildi.emit(seq, segmentler, ceviriler)


def oku_yap(ocr: OcrEngine, kare: Frame, preset: OcrPreset) -> list[TextBlock]:
    """K3 okuma zinciri (saf, thread-bagimsiz): recognize -> satirlari_birlestir."""
    return list(satirlari_birlestir(ocr.recognize(kare, preset)))


KIRPMA_PAYI_PX = 16


def ikinci_gecis(ocr: OcrEngine, kare: Frame, bloklar: Sequence[TextBlock], preset: OcrPreset) -> list[TextBlock]:
    """Secilen bloklarin birlesik kutusunu (+pay) kareden kirpip yeniden okur; sonuc kare koordinatinda.

    Kirpma kare disina tasmaz; kirpik bos kalirsa (0 piksel) ya da yeniden okuma bos donerse verilen bloklar
    aynen kullanilir (secim kaybolmaz).
    """
    if not bloklar:
        return []
    x1 = max(kare.rect.x, min(b.bbox.x for b in bloklar) - KIRPMA_PAYI_PX)
    y1 = max(kare.rect.y, min(b.bbox.y for b in bloklar) - KIRPMA_PAYI_PX)
    x2 = min(kare.rect.x + kare.rect.w, max(b.bbox.x + b.bbox.w for b in bloklar) + KIRPMA_PAYI_PX)
    y2 = min(kare.rect.y + kare.rect.h, max(b.bbox.y + b.bbox.h for b in bloklar) + KIRPMA_PAYI_PX)
    if x2 - x1 < 8 or y2 - y1 < 8:
        return list(bloklar)
    ox, oy = x1 - kare.rect.x, y1 - kare.rect.y
    kirpik = kare.image[oy:oy + (y2 - y1), ox:ox + (x2 - x1)]
    alt_kare = Frame(image=kirpik.copy(), rect=Rect(x1, y1, x2 - x1, y2 - y1), captured_at=kare.captured_at, seq=kare.seq)
    yeni = list(satirlari_birlestir(ocr.recognize(alt_kare, preset)))
    return yeni or list(bloklar)


def cevir_yap(cevirici: TranslationProvider, sozluk: GlossaryStore | None, bloklar: Sequence[TextBlock],
              kaynak_dili: str, preset: OcrPreset, *, ocr: OcrEngine | None = None, kare: Frame | None = None,
              duzeltici: HedefDuzeltici | None = None) -> tuple[list[Segment], list[str]]:
    """K3 ceviri zinciri (saf): [ikinci gecis] -> secimi_birlestir -> sozluk gomme (yalniz modele) -> translate -> [duzelt].

    `ocr` ve `kare` verilirse secim kirpigi yeniden okunur (siki kutular). Bos secim -> ([], []).
    """
    if ocr is not None and kare is not None:
        bloklar = ikinci_gecis(ocr, kare, bloklar, preset)
    segmentler = secimi_birlestir(list(bloklar))
    if not segmentler:
        return [], []
    gomulu: Sequence[Segment] = segmentler
    if sozluk is not None:
        gomulu = terimleri_gom(segmentler, sozluk.lookup_segments(segmentler))
    istek = TranslationRequest(segments=tuple(gomulu), source_lang=kaynak_dili, target_lang="tr")
    sonuc = cevirici.translate(istek)
    ceviriler = list(sonuc.translations)
    if duzeltici is not None:
        ceviriler = duzeltici.hepsini_duzelt(ceviriler)
    return list(segmentler), ceviriler


class AnlikAkisi(QObject):
    """Snapshot akisi: `oku(kare)` -> `bloklar_hazir`; `cevir(bloklar)` -> `ceviri_hazir`; hatalar `hata`.

    UI thread'inde yaratilir; agir is `_Isci`de (kendi QThread'i). `kapat()` cagirmayi unutma
    (`AnlikPencere` kapanirken cagirir); nesne silinirken de kapanir.
    """

    bloklar_hazir = Signal(object)          # list[TextBlock]
    ceviri_hazir = Signal(object, object)   # list[Segment], list[str]
    hata = Signal(str)                      # istisna sinif adi (metin yok)
    _oku_istegi = Signal(int, object)
    _cevir_istegi = Signal(int, object)

    def __init__(self, ocr: OcrEngine, cevirici: TranslationProvider, sozluk: GlossaryStore | None, *,
                 kaynak_dili: str, preset: OcrPreset = OcrPreset.DIALOGUE, duzeltici: HedefDuzeltici | None = None,
                 ebeveyn: QObject | None = None) -> None:
        super().__init__(ebeveyn)
        self._seq = 0
        self._iptal_edilen = -1
        self._kapandi = False
        self._thread = QThread(self)
        self._isci = _Isci(ocr, cevirici, sozluk, kaynak_dili, preset, duzeltici)
        self._isci.moveToThread(self._thread)
        self._oku_istegi.connect(self._isci.oku, Qt.ConnectionType.QueuedConnection)
        self._cevir_istegi.connect(self._isci.cevir, Qt.ConnectionType.QueuedConnection)
        self._isci.okundu.connect(self._okundu, Qt.ConnectionType.QueuedConnection)
        self._isci.cevrildi.connect(self._cevrildi, Qt.ConnectionType.QueuedConnection)
        self._isci.hata.connect(self._hata, Qt.ConnectionType.QueuedConnection)
        self._thread.start()
        self.destroyed.connect(_thread_durdur_fabrikasi(self._thread))

    # -- istekler (UI thread) ------------------------------------------------------------------
    @property
    def seq(self) -> int:
        """Su anki okuma numarasi (0 = henuz okuma yok)."""
        return self._seq

    @property
    def kapandi(self) -> bool:
        return self._kapandi

    def oku(self, kare: Frame) -> int:
        """Yeni kare: OCR baslar; onceki okumanin (varsa) gec gelen sonucu dusurulur. Yeni seq'i dondurur."""
        self._seq += 1
        self._oku_istegi.emit(self._seq, kare)
        return self._seq

    def cevir(self, bloklar: Sequence[TextBlock]) -> None:
        """Secilen bloklari cevir; yeni seq alir (onceki ucustaki ceviri dusurulur). `oku` yapilmadan da cagrilabilir."""
        self._seq += 1
        self._cevir_istegi.emit(self._seq, list(bloklar))

    def iptal(self) -> None:
        """Ucuşta olan okuma/ceviri sonuclarini dusur (K2). Isci calismaya devam eder, sonucu yayilmaz."""
        self._iptal_edilen = self._seq
        self._seq += 1

    def kapat(self) -> None:
        """Thread'i durdur ve bekle (<= 2 s). Idempotent."""
        if self._kapandi:
            return
        self._kapandi = True
        self._thread.quit()
        self._thread.wait(_KAPANIS_BEKLEME_MS)

    # -- sonuclar (UI thread) ------------------------------------------------------------------
    def _guncel(self, seq: int) -> bool:
        return seq == self._seq and seq != self._iptal_edilen and not self._kapandi

    @Slot(int, object)
    def _okundu(self, seq: int, bloklar: list[TextBlock]) -> None:
        if self._guncel(seq):
            self.bloklar_hazir.emit(bloklar)

    @Slot(int, object, object)
    def _cevrildi(self, seq: int, segmentler: list[Segment], ceviriler: list[str]) -> None:
        if self._guncel(seq):
            self.ceviri_hazir.emit(segmentler, ceviriler)

    @Slot(int, str)
    def _hata(self, seq: int, sinif: str) -> None:
        if self._guncel(seq):
            self.hata.emit(sinif)


def _thread_durdur_fabrikasi(thread: QThread) -> object:
    """`destroyed` alicisi: `self` yakalamaz (PySide6'da bagli yontem calismaz -- T-012/T-013 dersi)."""
    def durdur(*_: object) -> None:
        if thread.isRunning():
            thread.quit()
            thread.wait(_KAPANIS_BEKLEME_MS)
    return durdur


# TranslatorError disa aktarimi: UI `hata` sinif adini bu hiyerarsiyle eslestirebilir.
_ = TranslatorError
