"""T-001 -- cekirdek veri modelleri.

Tasarim dokumani 5.3'teki model tanimlarini dogrular:
  - hepsi @dataclass(frozen=True)
  - alan adlari, sirasi ve tipleri
  - varsayilan degerler ve None kabul eden alanlar
"""
from __future__ import annotations

import dataclasses
from typing import Any, get_type_hints

import numpy as np
import pytest

from src.contracts.models import (
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

ALL_MODELS: tuple[type, ...] = (
    Rect,
    Frame,
    TextBlock,
    Segment,
    TermHit,
    Pair,
    TranslationRequest,
    TranslationResult,
)


# --------------------------------------------------------------------------
# yardimcilar
# --------------------------------------------------------------------------

def rect() -> Rect:
    return Rect(x=10, y=20, w=300, h=40, monitor_index=0, dpi_scale=1.5)


def image(value: int = 7) -> ImageArray:
    return np.full((2, 3, 3), value, dtype=np.uint8)


def sample(model: type) -> Any:
    """Her model icin gecerli bir ornek uretir."""
    if model is Rect:
        return rect()
    if model is Frame:
        return Frame(image=image(), rect=rect(), captured_at=1.5, seq=3)
    if model is TextBlock:
        return TextBlock(text="Merhaba", bbox=rect(), confidence=0.9,
                         line_boxes=(rect(),))
    if model is Segment:
        return Segment(text="Merhaba", bbox=rect(), speaker="Ana",
                       placeholders=("{0}",), source_blocks=(0, 1))
    if model is TermHit:
        return TermHit(source_term="Estus", target_term="Estus Sisesi",
                       start=0, end=5)
    if model is Pair:
        return Pair(source="hello", target="merhaba", score=0.8)
    if model is TranslationRequest:
        return TranslationRequest(segments=(sample(Segment),),
                                  source_lang=None, target_lang="tr")
    if model is TranslationResult:
        return TranslationResult(translations=("merhaba",),
                                 provider_id="fake", latency_ms=0.0)
    raise AssertionError(f"ornek uretilemedi: {model!r}")


# --------------------------------------------------------------------------
# degismezlik (frozen)
# --------------------------------------------------------------------------

@pytest.mark.parametrize("model", ALL_MODELS, ids=lambda m: m.__name__)
def test_model_is_frozen_dataclass(model: type) -> None:
    assert dataclasses.is_dataclass(model)
    params = model.__dataclass_params__  # type: ignore[attr-defined]
    assert params.frozen is True, f"{model.__name__} frozen degil"


@pytest.mark.parametrize("model", ALL_MODELS, ids=lambda m: m.__name__)
def test_assignment_raises_frozen_instance_error(model: type) -> None:
    """Testin varligi yetmez; davranisi dogrula."""
    instance = sample(model)
    first_field = dataclasses.fields(instance)[0].name
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(instance, first_field, None)


@pytest.mark.parametrize("model", ALL_MODELS, ids=lambda m: m.__name__)
def test_new_attribute_cannot_be_added(model: type) -> None:
    instance = sample(model)
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(instance, "yeni_alan", 1)


@pytest.mark.parametrize("model", ALL_MODELS, ids=lambda m: m.__name__)
def test_field_cannot_be_deleted(model: type) -> None:
    instance = sample(model)
    first_field = dataclasses.fields(instance)[0].name
    with pytest.raises(dataclasses.FrozenInstanceError):
        delattr(instance, first_field)


# --------------------------------------------------------------------------
# alan adlari ve sirasi (5.3 ile birebir)
# --------------------------------------------------------------------------

EXPECTED_FIELDS: dict[type, tuple[str, ...]] = {
    Rect: ("x", "y", "w", "h", "monitor_index", "dpi_scale"),
    Frame: ("image", "rect", "captured_at", "seq"),
    TextBlock: ("text", "bbox", "confidence", "line_boxes"),
    Segment: ("text", "bbox", "speaker", "placeholders", "source_blocks"),
    TermHit: ("source_term", "target_term", "start", "end",
              "segment_index", "note"),
    Pair: ("source", "target", "score"),
    TranslationRequest: (
        "segments", "source_lang", "target_lang", "glossary_hits",
        "tm_examples", "style_profile", "image_crops",
    ),
    TranslationResult: (
        "translations", "provider_id", "latency_ms", "from_cache",
        "detected_lang", "partial",
    ),
}


@pytest.mark.parametrize(("model", "names"), list(EXPECTED_FIELDS.items()),
                         ids=[m.__name__ for m in EXPECTED_FIELDS])
def test_field_names_and_order(model: type, names: tuple[str, ...]) -> None:
    actual = tuple(f.name for f in dataclasses.fields(model))
    assert actual == names


def test_every_documented_model_is_covered() -> None:
    assert set(EXPECTED_FIELDS) == set(ALL_MODELS)


# --------------------------------------------------------------------------
# alan tipleri
# --------------------------------------------------------------------------

def test_rect_field_types() -> None:
    assert get_type_hints(Rect) == {
        "x": int, "y": int, "w": int, "h": int,
        "monitor_index": int, "dpi_scale": float,
    }


def test_frame_field_types() -> None:
    hints = get_type_hints(Frame)
    assert hints["image"] == ImageArray
    assert hints["rect"] is Rect
    assert hints["captured_at"] is float
    assert hints["seq"] is int


def test_text_block_field_types() -> None:
    hints = get_type_hints(TextBlock)
    assert hints["text"] is str
    assert hints["bbox"] is Rect
    assert hints["confidence"] is float
    assert hints["line_boxes"] == tuple[Rect, ...]


def test_segment_field_types() -> None:
    hints = get_type_hints(Segment)
    assert hints["text"] is str
    assert hints["bbox"] is Rect
    assert hints["speaker"] == (str | None)
    assert hints["placeholders"] == tuple[str, ...]
    assert hints["source_blocks"] == tuple[int, ...]


def test_translation_request_field_types() -> None:
    hints = get_type_hints(TranslationRequest)
    assert hints["segments"] == tuple[Segment, ...]
    assert hints["source_lang"] == (str | None)
    assert hints["target_lang"] is str
    assert hints["glossary_hits"] == tuple[TermHit, ...]
    assert hints["tm_examples"] == tuple[Pair, ...]
    assert hints["style_profile"] == (str | None)
    assert hints["image_crops"] == (tuple[ImageArray, ...] | None)


def test_translation_result_field_types() -> None:
    hints = get_type_hints(TranslationResult)
    assert hints["translations"] == tuple[str, ...]
    assert hints["provider_id"] is str
    assert hints["latency_ms"] is float
    assert hints["from_cache"] is bool
    assert hints["detected_lang"] == (str | None)
    assert hints["partial"] is bool


def test_term_hit_and_pair_field_types() -> None:
    term = get_type_hints(TermHit)
    assert term["source_term"] is str
    assert term["target_term"] is str
    assert term["start"] is int
    assert term["end"] is int
    assert term["segment_index"] == (int | None)
    assert term["note"] == (str | None)

    pair = get_type_hints(Pair)
    assert pair["source"] is str
    assert pair["target"] is str
    assert pair["score"] is float


# --------------------------------------------------------------------------
# davranis: varsayilanlar, tureyen alanlar, image_crops
# --------------------------------------------------------------------------

def test_rect_defaults_and_derived_edges() -> None:
    r = Rect(x=10, y=20, w=300, h=40)
    assert r.monitor_index == 0
    assert r.dpi_scale == 1.0
    assert r.right == 310
    assert r.bottom == 60


def test_optional_collection_defaults() -> None:
    assert TextBlock(text="a", bbox=rect(), confidence=1.0).line_boxes == ()
    seg = Segment(text="a", bbox=rect())
    assert seg.speaker is None
    assert seg.placeholders == ()
    assert seg.source_blocks == ()
    hit = TermHit(source_term="a", target_term="b", start=0, end=1)
    assert hit.segment_index is None
    assert hit.note is None
    assert Pair(source="a", target="b").score == 1.0


def test_translation_request_optional_defaults() -> None:
    req = TranslationRequest(segments=(), source_lang=None, target_lang="tr")
    assert req.glossary_hits == ()
    assert req.tm_examples == ()
    assert req.style_profile is None
    assert req.image_crops is None


def test_image_crops_accepts_arrays() -> None:
    """5.3: vision motorlari icin bugun eklenmis alan."""
    crops = (image(1), image(2))
    req = TranslationRequest(
        segments=(sample(Segment),),
        source_lang="en",
        target_lang="tr",
        image_crops=crops,
    )
    assert req.image_crops is not None
    assert len(req.image_crops) == 2
    assert req.image_crops[0].dtype == np.uint8


def test_translation_result_defaults() -> None:
    res = TranslationResult(translations=("a",), provider_id="fake",
                            latency_ms=1.0)
    assert res.from_cache is False
    assert res.detected_lang is None
    assert res.partial is False


# --------------------------------------------------------------------------
# esitlik / hash: ndarray tasiyan modeller patlamamali
# --------------------------------------------------------------------------

def test_rect_is_hashable_and_value_comparable() -> None:
    assert rect() == rect()
    assert len({rect(), rect()}) == 1


def test_frame_equality_and_hash_do_not_raise_on_ndarray() -> None:
    a = Frame(image=image(1), rect=rect(), captured_at=1.5, seq=3)
    b = Frame(image=image(2), rect=rect(), captured_at=1.5, seq=3)
    assert bool(a == b) is True          # goruntu karsilastirmaya girmez
    assert hash(a) == hash(b)
    assert Frame(image=image(), rect=rect(), captured_at=1.5, seq=4) != a


def test_translation_request_equality_does_not_raise_with_crops() -> None:
    segs = (sample(Segment),)
    a = TranslationRequest(segments=segs, source_lang="en", target_lang="tr",
                           image_crops=(image(1),))
    b = TranslationRequest(segments=segs, source_lang="en", target_lang="tr",
                           image_crops=(image(2),))
    assert bool(a == b) is True
    assert hash(a) == hash(b)


def test_frame_repr_does_not_dump_pixels() -> None:
    text = repr(Frame(image=image(), rect=rect(), captured_at=1.5, seq=3))
    assert "seq=3" in text
    assert "[[[" not in text


# --------------------------------------------------------------------------
# OcrPreset
# --------------------------------------------------------------------------

def test_ocr_preset_values_match_profile_schema() -> None:
    """3.1: ocr_preset = dialogue | menu | tooltip | subtitle."""
    assert {p.value for p in OcrPreset} == {
        "dialogue", "menu", "tooltip", "subtitle"}


def test_ocr_preset_is_str_subclass() -> None:
    assert isinstance(OcrPreset.DIALOGUE, str)
    assert OcrPreset("menu") is OcrPreset.MENU
