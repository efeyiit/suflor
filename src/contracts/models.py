"""Suflor cekirdek veri modelleri -- SOZLESME.

Tasarim dokumani 5.3'un birebir uygulamasi. Butun bilesenler bu modellere
bagimlidir; yalnizca Sozlesme Ajani (A1) degistirebilir. Eksik bir alan
gorursen kendin ekleme -- `contract_change_request: true` ile talep ac.

Kurallar:
  - Her model `@dataclass(frozen=True)`. Degismezlik, pipeline'in yaris
    kosullarina karsi ilk savunmasidir: bir asama elindeki nesneyi
    degistirerek diger asamayi bozamaz.
  - Bu modul hicbir somut kutuphaneyi import etmez. Yalnizca stdlib ve
    numpy (sadece tip anotasyonu icin). `purity_check.py` bunu denetler.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TypeAlias

import numpy as np
import numpy.typing as npt

__all__ = [
    "ImageArray",
    "OcrPreset",
    "Rect",
    "Frame",
    "TextBlock",
    "Segment",
    "TermHit",
    "Pair",
    "TranslationRequest",
    "TranslationResult",
]


ImageArray: TypeAlias = npt.NDArray[np.uint8]
"""BGR duzeninde, uint8 goruntu dizisi -- (yukseklik, genislik, 3)."""


class OcrPreset(StrEnum):
    """Oyun metni turune gore OCR on ayari (tasarim dokumani 3.1 / 3.2).

    On ayar; blok gruplama, guven esigi, olcekleme faktoru ve kontrast on
    islemesini degistirir. `StrEnum` oldugu icin uyeler ayni zamanda `str`'dir:
    profil JSON'una dogrudan yazilabilir, `OcrPreset("dialogue")` ile geri
    okunabilir.
    """

    DIALOGUE = "dialogue"
    MENU = "menu"
    TOOLTIP = "tooltip"
    SUBTITLE = "subtitle"


@dataclass(frozen=True)
class Rect:
    """Ekran uzerinde bir dikdortgen; monitor ve DPI farkindaligiyla.

    Koordinatlar fiziksel piksel cinsindendir; `dpi_scale` mantiksal
    koordinata cevirmek isteyen tarafin isidir.
    """

    x: int
    y: int
    w: int
    h: int
    monitor_index: int = 0
    dpi_scale: float = 1.0

    @property
    def right(self) -> int:
        return self.x + self.w

    @property
    def bottom(self) -> int:
        return self.y + self.h


@dataclass(frozen=True)
class Frame:
    """Yakalanmis tek bir goruntu karesi.

    `image` esitlik ve hash disindadir (`compare=False`): ndarray'in `==`
    islemi skaler degil dizi dondurur, bu da dataclass'in uretilmis
    `__eq__`/`__hash__` metodlarini patlatirdi. Bir karenin kimligi zaten
    `seq` alanidir. `repr=False` ise piksel yiginini loga dokmemek icindir.
    """

    image: ImageArray = field(repr=False, compare=False)
    rect: Rect
    captured_at: float
    """`time.monotonic()` okumasi -- duvar saati degil."""
    seq: int
    """Monoton artan kare numarasi; geciken sonuclari elemek icin."""


@dataclass(frozen=True)
class TextBlock:
    """OCR motorunun dondurdugu ham metin blogu."""

    text: str
    bbox: Rect
    confidence: float
    line_boxes: tuple[Rect, ...] = ()


@dataclass(frozen=True)
class Segment:
    """Normalize edilmis, cevrilmeye hazir metin parcasi."""

    text: str
    bbox: Rect
    speaker: str | None = None
    placeholders: tuple[str, ...] = ()
    """Korunacak yer tutucular: `{0}`, `%s`, renk etiketleri..."""
    source_blocks: tuple[int, ...] = ()
    """Bu segmenti ureten `TextBlock` indeksleri."""


@dataclass(frozen=True)
class TermHit:
    """Terim sozlugunde bulunan ve cevirisi zorunlu kilinan bir esleme."""

    source_term: str
    target_term: str
    start: int
    """Metindeki baslangic indeksi."""
    end: int
    """Metindeki bitis indeksi (haric)."""
    segment_index: int | None = None
    """Hangi segmentte gectigi. `GlossaryStore.lookup(text)` tek bir metin
    uzerinde calistigi icin bunu dolduramaz; iliskilendirmeyi pipeline yapar.
    `None` = belirli bir segmente baglanmamis."""
    note: str | None = None
    """Cevirmene serbest metin talimati."""


@dataclass(frozen=True)
class Pair:
    """Ceviri bellegindeki kaynak/hedef ciftini temsil eder."""

    source: str
    target: str
    score: float = 1.0
    """Fuzzy benzerlik, 0..1. `find_similar` doldurur; `add` ile eklenen
    kesin kayitlar icin 1.0."""


@dataclass(frozen=True)
class TranslationRequest:
    """Bir `TranslationProvider`'a giden istek.

    `image_crops` bugun yalnizca vision tabanli motorlarin isine yarar ama
    sozlesmeye bugun konur: sonradan eklemek kirici degisiklik olurdu.
    `image` gibi o da esitlik/hash disindadir.
    """

    segments: tuple[Segment, ...]
    source_lang: str | None
    """`None` = otomatik algila."""
    target_lang: str
    glossary_hits: tuple[TermHit, ...] = ()
    tm_examples: tuple[Pair, ...] = ()
    style_profile: str | None = None
    image_crops: tuple[ImageArray, ...] | None = field(
        default=None, repr=False, compare=False
    )
    """Vision motorlari icin segment goruntu kirpintilari."""


@dataclass(frozen=True)
class TranslationResult:
    """Bir `TranslationProvider`'in donusu.

    `translations`, istegin `segments` alani ile **birebir hizali** olmak
    zorundadir. Bu sozlesme `interfaces.ensure_aligned` ile denetlenir ve
    ihlali `ContractViolation` ile sonuclanir.
    """

    translations: tuple[str, ...]
    provider_id: str
    latency_ms: float
    from_cache: bool = False
    detected_lang: str | None = None
    partial: bool = False
    """Streaming ara sonucu mu -- `True` ise sonuc henuz nihai degil."""
