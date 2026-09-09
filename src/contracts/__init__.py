"""Suflor sozlesme paketi -- butun bilesenlerin ortak dili.

Bu paket **dondurulmustur**. Diger ajanlar buraya yazmaz; eksik bir alan
gerekiyorsa `contract_change_request: true` ile talep acilir.

Icerik:
  - `models`     : degismez veri modelleri (tasarim dokumani 5.3)
  - `interfaces` : `OcrEngine` / `TranslationProvider` + deterministik sahteler
  - `errors`     : `TranslatorError` kokunden hata taksonomisi
"""
from __future__ import annotations

from .errors import (
    CaptureError,
    ContractViolation,
    ModelMissingError,
    OcrError,
    ProviderTimeout,
    ProviderUnavailable,
    TranslatorError,
)
from .interfaces import (
    FakeOcrEngine,
    FakeProvider,
    OcrEngine,
    TranslationProvider,
    ensure_aligned,
)
from .models import (
    Frame,
    ImageArray,
    OcrPreset,
    Pair,
    Rect,
    Segment,
    TermHit,
    TextBlock,
    TranslationRequest,
    TranslationResult,
)

__all__ = [
    # models
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
    # interfaces
    "OcrEngine",
    "TranslationProvider",
    "ensure_aligned",
    "FakeOcrEngine",
    "FakeProvider",
    # errors
    "TranslatorError",
    "CaptureError",
    "ModelMissingError",
    "OcrError",
    "ProviderUnavailable",
    "ProviderTimeout",
    "ContractViolation",
]
