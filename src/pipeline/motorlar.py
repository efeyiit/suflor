"""Suflor -- motor deposu: OCR + ceviri + sozluk motorlarini UI'yi bloklamadan arka planda kurar (T-014).

Model yuklemesi agirdir (NMT 647 MB ~1.5 s, OCR ilk cagri ~1 s); kisayola basildiginda kullaniciyi
bekletmemek icin uygulama acilirken bir kez arka planda kurulur. `hazir` sinyali gelmeden `ocr`/`cevirici`
okunursa `RuntimeError` (yarim motor kullanilmaz). Kurulum hatasi `hata(sinif_adi)` ile bildirilir
(ModelMissingError: model dizini yok). `kapat()` saglayiciyi kapatir ve thread'i bekler.

Fabrikalar enjekte edilir (test: sahte motorlar, dosya yok); varsayilan fabrikalar gercek motorlari kurar.
"""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal

from src.contracts.interfaces import OcrEngine, TranslationProvider
from src.translate.sozluk import GlossaryStore

__all__ = ["MotorDeposu", "MotorFabrikalari", "gercek_fabrikalar"]

MotorFabrikalari = tuple[Callable[[], OcrEngine], Callable[[], TranslationProvider], Callable[[], GlossaryStore | None]]


def gercek_fabrikalar(
    ocr_dili: object,
    model_dizini: Path,
    sozluk_yolu: Path | None,
    threads: int = 8,
    kalite_yollari: tuple[Path, Path] | None = None,
) -> MotorFabrikalari:
    """Gercek motor fabrikalari (import'lar gecikmeli: pipeline testleri OCR/NMT kutuphanelerini yuklemez)."""
    def ocr() -> OcrEngine:
        from src.ocr.rapid_engine import OcrLanguage, RapidOcrEngine
        return RapidOcrEngine(language=OcrLanguage(str(ocr_dili)), threads=threads, allow_download=True)

    def cevirici() -> TranslationProvider:
        from src.translate.local_nmt import LocalNmtProvider
        nmt = LocalNmtProvider(model_dir=model_dizini, threads=threads)
        if kalite_yollari is None or not all(yol.is_file() for yol in kalite_yollari):
            return nmt
        from src.translate.fallback import QualityFallbackProvider
        from src.translate.llama_local import LlamaLocalProvider
        from src.translate.llama_server import LlamaServer
        executable, model = kalite_yollari
        return QualityFallbackProvider(LlamaLocalProvider(LlamaServer(executable, model)), nmt)

    def sozluk() -> GlossaryStore | None:
        return GlossaryStore(sozluk_yolu) if sozluk_yolu is not None else None

    return ocr, cevirici, sozluk


class _Kurucu(QThread):
    def __init__(self, fabrikalar: MotorFabrikalari) -> None:
        super().__init__()
        self._fabrikalar = fabrikalar
        self.ocr: OcrEngine | None = None
        self.cevirici: TranslationProvider | None = None
        self.sozluk: GlossaryStore | None = None
        self.hata_sinifi: str | None = None

    def run(self) -> None:
        try:
            self.ocr = self._fabrikalar[0]()
            self.cevirici = self._fabrikalar[1]()
            self.sozluk = self._fabrikalar[2]()
        except Exception as e:  # noqa: BLE001 -- sinif adi disari, metin degil
            self.hata_sinifi = type(e).__name__


class MotorDeposu(QObject):
    """Arka planda kurulan motorlar. `baslat()` -> ... -> `hazir` ya da `hata(sinif)`."""

    hazir = Signal()
    hata = Signal(str)

    def __init__(self, fabrikalar: MotorFabrikalari, ebeveyn: QObject | None = None) -> None:
        super().__init__(ebeveyn)
        self._kurucu = _Kurucu(fabrikalar)
        self._kurucu.finished.connect(self._bitti)
        self._hazir = False
        self._kapandi = False

    def baslat(self) -> None:
        if not self._kurucu.isRunning() and not self._hazir:
            self._kurucu.start()

    @property
    def hazir_mi(self) -> bool:
        return self._hazir

    @property
    def ocr(self) -> OcrEngine:
        if not self._hazir or self._kurucu.ocr is None:
            raise RuntimeError("motorlar hazir degil")
        return self._kurucu.ocr

    @property
    def cevirici(self) -> TranslationProvider:
        if not self._hazir or self._kurucu.cevirici is None:
            raise RuntimeError("motorlar hazir degil")
        return self._kurucu.cevirici

    @property
    def sozluk(self) -> GlossaryStore | None:
        if not self._hazir:
            raise RuntimeError("motorlar hazir degil")
        return self._kurucu.sozluk

    def _bitti(self) -> None:
        if self._kurucu.hata_sinifi is not None:
            self.hata.emit(self._kurucu.hata_sinifi)
            return
        self._hazir = True
        self.hazir.emit()

    def kapat(self) -> None:
        if self._kapandi:
            return
        self._kapandi = True
        self._kurucu.wait(5000)
        kapat = getattr(self._kurucu.cevirici, "close", None)
        if callable(kapat):
            kapat()
