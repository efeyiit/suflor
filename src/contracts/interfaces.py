"""Suflor soyut arayuzleri ve sahte referans implementasyonlari -- SOZLESME.

Tasarim dokumani 5.1 / 5.3. Iki dikis burada cizilir:

  - `OcrEngine`      -> RapidOcrEngine, PaddleOcrEngine, FakeOcrEngine
  - `TranslationProvider` -> LocalNmtProvider, LocalLlmProvider, CloudProvider,
                             FakeProvider

`FakeOcrEngine` ve `FakeProvider` sadece ornek degil, **butun ajanlarin test
altyapisidir**. Bu yuzden ikisi de tamamen deterministiktir: rastgelelik yok,
saat okuma yok, I/O yok. Ayni girdi her zaman ayni cikti.

Bu modul hicbir somut kutuphaneyi import etmez (purity_check.py denetler).
"""
from __future__ import annotations

import abc
from collections.abc import Mapping, Sequence

from .errors import ContractViolation, TranslatorError
from .models import (
    Frame,
    OcrPreset,
    TextBlock,
    TranslationRequest,
    TranslationResult,
)

__all__ = [
    "OcrEngine",
    "TranslationProvider",
    "ensure_aligned",
    "FakeOcrEngine",
    "FakeProvider",
]


# ---------------------------------------------------------------------------
# sozlesme denetimi
# ---------------------------------------------------------------------------

def ensure_aligned(
    request: TranslationRequest, result: TranslationResult
) -> None:
    """`result.translations` ile `request.segments` hizali mi -- denetle.

    Sozlesmenin en kritik maddesi budur: hizalama bozulursa cevirilerin
    hangi segmente ait oldugu kaybolur ve ekrana yanlis metin basilir.
    5.6'ya gore dogru davranis sonucu atip tek tek yeniden denemektir; bu
    fonksiyon o dallanmayi tetikleyen sinyali uretir.

    Raises:
        ContractViolation: sayilar uyusmuyorsa.
    """
    expected = len(request.segments)
    actual = len(result.translations)
    if expected != actual:
        raise ContractViolation(
            "ceviri sayisi segment sayisiyla uyusmuyor: "
            f"segments={expected}, translations={actual} "
            f"(provider={result.provider_id!r})"
        )


# ---------------------------------------------------------------------------
# arayuzler
# ---------------------------------------------------------------------------

class OcrEngine(abc.ABC):
    """Goruntu -> metin bloklari."""

    @abc.abstractmethod
    def recognize(self, frame: Frame, preset: OcrPreset) -> list[TextBlock]:
        """`frame` uzerinde OCR calistirir.

        Uygulamalar dusuk guvenli sonuclari **elemez** -- esik uygulamak
        `TextNormalizer`'in isidir. Bos sonuc gecerlidir ve hata degildir.

        Raises:
            ModelMissingError: motor model dosyasi olmadan calisamiyorsa.
            OcrError: motor calisti ama basarisiz oldu.
        """


class TranslationProvider(abc.ABC):
    """Segmentleri ceviren motor."""

    @property
    @abc.abstractmethod
    def provider_id(self) -> str:
        """Kararli, log ve cache anahtarinda kullanilan motor kimligi."""

    @abc.abstractmethod
    def translate(self, request: TranslationRequest) -> TranslationResult:
        """`request.segments`'i cevirir.

        Donen `TranslationResult.translations` **her zaman** `segments` ile
        birebir hizali olmalidir; uygulamalar donmeden once
        `ensure_aligned` cagirmalidir.

        Raises:
            ProviderUnavailable: OOM, ag hatasi, kota asimi.
            ProviderTimeout: butce icinde cevap gelmedi.
            ContractViolation: motor hizalamayi bozdu.
        """


# ---------------------------------------------------------------------------
# sahte (deterministik) referans implementasyonlari
# ---------------------------------------------------------------------------

class FakeOcrEngine(OcrEngine):
    """Betige gore sonuc donduren deterministik OCR motoru.

    `script` her `recognize` cagrisi icin bir blok listesi tasir; cagrilar
    betikte sirayla ilerler. Betik tukendiginde son adim tekrarlanir --
    boylece canli mod testlerinde N tick calistirmak icin N adim yazmak
    gerekmez. Betik bos ise her cagri bos liste dondurur.

    Ornek:
        engine = FakeOcrEngine([[block_a], [block_b, block_c]])
    """

    def __init__(self, script: Sequence[Sequence[TextBlock]] = ()) -> None:
        self._script: tuple[tuple[TextBlock, ...], ...] = tuple(
            tuple(step) for step in script
        )
        self.calls: list[tuple[Frame, OcrPreset]] = []
        """Gelen (frame, preset) ciftleri -- testler bunun uzerinden dogrular."""

    @property
    def call_count(self) -> int:
        return len(self.calls)

    def recognize(self, frame: Frame, preset: OcrPreset) -> list[TextBlock]:
        index = len(self.calls)
        self.calls.append((frame, preset))
        if not self._script:
            return []
        step = self._script[min(index, len(self._script) - 1)]
        return list(step)  # cagiran mutasyon yaparsa betik bozulmasin


class FakeProvider(TranslationProvider):
    """Hizalama sozlesmesini her kosulda saglayan deterministik saglayici.

    Varsayilan davranis: her segment `"[<target_lang>] <metin>"` olur.
    `translations` sozlugu verilirse o metinler icin sozlukteki karsilik
    kullanilir; kalanlar varsayilan bicime duser. Ceviri sayisi her zaman
    segment sayisina esittir -- sifir segment icin bos demet doner.

    Kontrollu hata uretmek icin `error` verilir; `translate` o hatayi
    firlatir. Boylece saglayici hata yollari (5.6) sahte bir motorla
    deterministik olarak sinanabilir.
    """

    def __init__(
        self,
        *,
        provider_id: str = "fake",
        translations: Mapping[str, str] | None = None,
        detected_lang: str = "en",
        latency_ms: float = 0.0,
        error: TranslatorError | None = None,
    ) -> None:
        self._provider_id = provider_id
        self._table: dict[str, str] = dict(translations or {})
        self._detected_lang = detected_lang
        self._latency_ms = latency_ms
        self._error = error
        self.requests: list[TranslationRequest] = []
        """Gelen istekler -- testler sozluk/TM aktariminini burada dogrular."""

    @property
    def provider_id(self) -> str:
        return self._provider_id

    @property
    def call_count(self) -> int:
        return len(self.requests)

    def translate(self, request: TranslationRequest) -> TranslationResult:
        self.requests.append(request)
        if self._error is not None:
            raise self._error

        translations = tuple(
            self._table.get(
                segment.text, f"[{request.target_lang}] {segment.text}"
            )
            for segment in request.segments
        )
        detected = (
            request.source_lang
            if request.source_lang is not None
            else self._detected_lang
        )
        result = TranslationResult(
            translations=translations,
            provider_id=self._provider_id,
            latency_ms=self._latency_ms,
            from_cache=False,
            detected_lang=detected,
            partial=False,
        )
        ensure_aligned(request, result)
        return result
