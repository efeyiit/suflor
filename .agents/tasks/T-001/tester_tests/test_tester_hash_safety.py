"""TESTER -- ndarray tasiyan frozen modellerin esitlik/hash guvenligi.

`Frame.image` ve `TranslationRequest.image_crops` numpy dizileridir.
`@dataclass(frozen=True)` varsayilan `__eq__`/`__hash__` uretimi TUM alanlari
karsilastirmaya/hash'e katar; bir ndarray alani bundan haric tutulmazsa
`==` skaler degil dizi dondurur ve `bool(a == b)` veya `hash(a)` calisirken
`ValueError`/`TypeError` firlatir. Bu, davranissal olarak calistirilmadan
(yalnizca kodu okuyarak `compare=False` gorup gecerli saymakla) yakalanamayacak
turden bir hata sinifidir -- bu yuzden burada FIILEN calistiriyoruz.
"""
from __future__ import annotations

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

RECT = Rect(x=0, y=0, w=10, h=10)


def _img(fill: int) -> ImageArray:
    return np.full((3, 3, 3), fill, dtype=np.uint8)


def test_frame_equality_with_different_pixels_does_not_raise() -> None:
    a = Frame(image=_img(1), rect=RECT, captured_at=1.0, seq=5)
    b = Frame(image=_img(255), rect=RECT, captured_at=1.0, seq=5)
    # Bu satir kendisi bir denetimdir: patlarsa test FAIL olur (exception).
    outcome = a == b
    assert isinstance(outcome, bool), (
        "Frame.__eq__ skaler bool degil bir sey dondurdu -- ndarray alani "
        "karsilastirmaya sizmis olabilir"
    )
    assert outcome is True  # image compare disi oldugu icin esit sayilmali


def test_frame_hash_is_stable_and_ignores_pixel_content() -> None:
    a = Frame(image=_img(1), rect=RECT, captured_at=1.0, seq=5)
    b = Frame(image=_img(255), rect=RECT, captured_at=1.0, seq=5)
    assert hash(a) == hash(b)


def test_frame_with_different_seq_is_not_equal() -> None:
    a = Frame(image=_img(1), rect=RECT, captured_at=1.0, seq=5)
    b = Frame(image=_img(1), rect=RECT, captured_at=1.0, seq=6)
    assert (a == b) is False


def test_frame_usable_as_dict_key_and_set_member() -> None:
    """hash()'in gercekten patlamadan calistigini set/dict baglaminda
    dogrula -- pipeline'in cache/dedup katmanlari bunu varsayacak."""
    a = Frame(image=_img(1), rect=RECT, captured_at=1.0, seq=1)
    b = Frame(image=_img(9), rect=RECT, captured_at=1.0, seq=1)  # a ile esit
    c = Frame(image=_img(1), rect=RECT, captured_at=1.0, seq=2)  # farkli
    s = {a, b, c}
    assert len(s) == 2
    d = {a: "birinci"}
    d[b] = "ikinci-ama-esdeger"
    assert len(d) == 1
    assert d[a] == "ikinci-ama-esdeger"


def test_translation_request_equality_with_different_crops_does_not_raise() -> None:
    req_a = TranslationRequest(segments=(), source_lang="en", target_lang="tr",
                               image_crops=(_img(1),))
    req_b = TranslationRequest(segments=(), source_lang="en", target_lang="tr",
                               image_crops=(_img(200),))
    outcome = req_a == req_b
    assert isinstance(outcome, bool)
    assert outcome is True
    assert hash(req_a) == hash(req_b)


def test_translation_request_hashable_when_image_crops_is_none() -> None:
    req = TranslationRequest(segments=(), source_lang=None, target_lang="tr",
                             image_crops=None)
    assert isinstance(hash(req), int)


# --------------------------------------------------------------------------
# Diger butun modeller (ndarray icermeyenler) de temelde hashlenebilir olmali
# -- ic ice frozen dataclass (Rect -> TextBlock/Segment) zincirinin hash
# uretimini kirmadigini dogrula.
# --------------------------------------------------------------------------

def test_rect_textblock_segment_termhit_pair_result_are_all_hashable() -> None:
    values: list[object] = [
        RECT,
        TextBlock(text="a", bbox=RECT, confidence=0.5, line_boxes=(RECT,)),
        Segment(text="a", bbox=RECT, speaker=None, placeholders=(),
                source_blocks=()),
        TermHit(source_term="a", target_term="b", start=0, end=1),
        Pair(source="a", target="b"),
        TranslationResult(translations=("a", "b"), provider_id="p",
                          latency_ms=1.0),
    ]
    for v in values:
        # hash() patlamamali; ayni degerli iki ornek ayni hash'e sahip olmali
        assert isinstance(hash(v), int), f"{type(v).__name__} hashlenemedi"


@pytest.mark.parametrize("build", [
    lambda: TextBlock(text="a", bbox=RECT, confidence=0.5),
    lambda: Segment(text="a", bbox=RECT),
    lambda: TermHit(source_term="a", target_term="b", start=0, end=1),
    lambda: Pair(source="a", target="b"),
    lambda: TranslationResult(translations=("a",), provider_id="p",
                              latency_ms=1.0),
])
def test_equal_value_instances_share_hash(build: object) -> None:
    x1 = build()  # type: ignore[operator]
    x2 = build()  # type: ignore[operator]
    assert x1 == x2
    assert hash(x1) == hash(x2)
