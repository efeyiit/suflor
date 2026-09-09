"""TESTER -- bagimsiz dondurulmuslik (frozen) dogrulamasi.

env.md #1: "Gercekten frozen mi? Her modelin bir ornegini olusturup alanina
atama yapmayi dene -- FrozenInstanceError firlatmali. Testin var olmasi
yetmez, davranisi dogrula."

Bu dosya implementer'in kendi test dosyasi OKUNMADAN, sadece packet.md +
tasarim dokumani 5.3 + kaynak kod okunarak yazilmistir. implementer'in
sample() yardimcisindan bagimsiz kendi ornek fabrikasini kurar ve --
implementer'in aksine -- yalnizca ilk alani degil TUM alanlari, hem de
birden fazla farkli deger tipiyle dener.
"""
from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from src.contracts.models import (
    Frame,
    ImageArray,
    Pair,
    Rect,
    Segment,
    TermHit,
    TextBlock,
    TranslationRequest,
    TranslationResult,
)


def _img() -> ImageArray:
    return np.zeros((2, 2, 3), dtype=np.uint8)


def _rect() -> Rect:
    return Rect(x=1, y=2, w=3, h=4, monitor_index=1, dpi_scale=1.25)


def _segment() -> Segment:
    return Segment(text="merhaba", bbox=_rect(), speaker="X",
                   placeholders=("{0}",), source_blocks=(0,))


# Her model icin (ornek, {alan_adi: deneme_degeri}) -- TUM alanlar kapsanir.
INSTANCES: list[tuple[object, dict[str, object]]] = [
    (_rect(), {"x": 99, "y": 99, "w": 99, "h": 99,
               "monitor_index": 9, "dpi_scale": 9.9}),
    (Frame(image=_img(), rect=_rect(), captured_at=1.0, seq=1),
     {"image": _img(), "rect": _rect(), "captured_at": 2.0, "seq": 2}),
    (TextBlock(text="a", bbox=_rect(), confidence=0.5, line_boxes=(_rect(),)),
     {"text": "b", "bbox": _rect(), "confidence": 0.9, "line_boxes": ()}),
    (_segment(),
     {"text": "x", "bbox": _rect(), "speaker": None,
      "placeholders": (), "source_blocks": ()}),
    (TermHit(source_term="a", target_term="b", start=0, end=1),
     {"source_term": "z", "target_term": "z", "start": 5, "end": 6,
      "segment_index": 3, "note": "n"}),
    (Pair(source="a", target="b", score=0.5),
     {"source": "z", "target": "z", "score": 1.0}),
    (TranslationRequest(segments=(_segment(),), source_lang="en",
                        target_lang="tr"),
     {"segments": (), "source_lang": None, "target_lang": "en",
      "glossary_hits": (), "tm_examples": (), "style_profile": "s",
      "image_crops": None}),
    (TranslationResult(translations=("a",), provider_id="p", latency_ms=1.0),
     {"translations": (), "provider_id": "q", "latency_ms": 2.0,
      "from_cache": True, "detected_lang": "tr", "partial": True}),
]


def _ids() -> list[str]:
    return [type(inst).__name__ for inst, _ in INSTANCES]


@pytest.mark.parametrize(("instance", "field_values"), INSTANCES, ids=_ids())
def test_every_field_rejects_assignment(
    instance: object, field_values: dict[str, object]
) -> None:
    """Testin var olmasi yetmez: HER alan icin fiilen dene."""
    assert field_values, "test verisi bos olamaz"
    for field_name, new_value in field_values.items():
        with pytest.raises(dataclasses.FrozenInstanceError):
            setattr(instance, field_name, new_value)


@pytest.mark.parametrize(("instance", "field_values"), INSTANCES, ids=_ids())
def test_every_field_rejects_deletion(
    instance: object, field_values: dict[str, object]
) -> None:
    for field_name in field_values:
        with pytest.raises(dataclasses.FrozenInstanceError):
            delattr(instance, field_name)


@pytest.mark.parametrize(("instance", "field_values"), INSTANCES, ids=_ids())
def test_unknown_attribute_rejected(
    instance: object, field_values: dict[str, object]
) -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(instance, "__tester_injected__", 1)


@pytest.mark.parametrize(("instance", "field_values"), INSTANCES, ids=_ids())
def test_dataclasses_replace_is_the_escape_hatch(
    instance: object, field_values: dict[str, object]
) -> None:
    """Frozen olmasina ragmen `dataclasses.replace` ile yeni kopya uretilebilmeli
    (dogru sekilde bir @dataclass oldugunu, ozel bir __setattr__ hack'i
    olmadigini dogrular)."""
    first_field = dataclasses.fields(instance)[0].name
    original_value = getattr(instance, first_field)
    new_value = field_values[first_field]
    copy = dataclasses.replace(instance, **{first_field: new_value})
    assert copy is not instance
    # `image` gibi ndarray alanlar `==` ile skaler bool uretmez (Frame.image).
    if isinstance(new_value, np.ndarray):
        assert np.array_equal(getattr(copy, first_field), new_value)
        assert np.array_equal(getattr(instance, first_field), original_value)
    else:
        assert getattr(copy, first_field) == new_value
        # orijinal degismemis olmali
        assert getattr(instance, first_field) == original_value


@pytest.mark.parametrize("model", [
    Rect, Frame, TextBlock, Segment, TermHit, Pair,
    TranslationRequest, TranslationResult,
], ids=lambda m: m.__name__)
def test_dataclass_params_report_frozen_true(model: type) -> None:
    """`@dataclass(frozen=True)` fiilen uygulanmis mi -- dekorator parametresini
    dogrudan denetle (davranissal testin yani sira, bildirimsel dogrulama)."""
    assert dataclasses.is_dataclass(model)
    params = model.__dataclass_params__  # type: ignore[attr-defined]
    assert params.frozen is True


def test_object_dunder_setattr_bypass_is_python_limitation_not_a_bug() -> None:
    """Bilgi amacli sinir testi: `object.__setattr__` frozen korumasini
    atlatabilir -- bu CPython'un frozen dataclass semantiginin bilinen
    bir siniridir, implementasyon hatasi degildir. Burada dogruluyoruz ki
    normal `setattr` (yani gercek dunya kullanimi) bunu YAPAMAZ."""
    r = _rect()
    with pytest.raises(dataclasses.FrozenInstanceError):
        r.x = 5  # noqa: normal atama -- bu satir raise etmeli
