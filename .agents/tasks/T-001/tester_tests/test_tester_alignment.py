"""TESTER -- bagimsiz hizalama (alignment) ve sahte (fake) motor dogrulamasi.

env.md #2: "FakeProvider hizali mi? 1, 3 ve 0 segmentle cagir; donen
translations uzunlugu her seferinde segments uzunluguna esit olmali."

Bu dosya `ensure_aligned`'i FakeProvider'dan BAGIMSIZ olarak da dogrudan
sinar (elle uydurulmus TranslationResult ile) -- boylece hizalama
denetiminin FakeProvider'in "iyi davranisina" degil, gercekten kendi
mantigina dayandigini kanitlar.
"""
from __future__ import annotations

import numpy as np
import pytest

from src.contracts.errors import ContractViolation, ProviderTimeout
from src.contracts.interfaces import FakeOcrEngine, FakeProvider, ensure_aligned
from src.contracts.models import (
    Frame,
    ImageArray,
    OcrPreset,
    Rect,
    Segment,
    TextBlock,
    TranslationRequest,
    TranslationResult,
)

RECT = Rect(x=0, y=0, w=50, h=10)


def _segments(n: int) -> tuple[Segment, ...]:
    return tuple(Segment(text=f"seg-{i}", bbox=RECT) for i in range(n))


def _request(n: int, **kw: object) -> TranslationRequest:
    base: dict[str, object] = {
        "segments": _segments(n), "source_lang": "en", "target_lang": "tr",
    }
    base.update(kw)
    return TranslationRequest(**base)  # type: ignore[arg-type]


# --------------------------------------------------------------------------
# FakeProvider: 0 / 1 / 3 segment (env.md'nin acikca istedigi) + ek sinirlar
# --------------------------------------------------------------------------

@pytest.mark.parametrize("n", [0, 1, 3, 2, 17])
def test_fake_provider_translation_count_matches_segment_count(n: int) -> None:
    req = _request(n)
    result = FakeProvider().translate(req)
    assert len(result.translations) == len(req.segments)
    assert len(result.translations) == n
    # ensure_aligned kendisi de sikayet etmemeli
    ensure_aligned(req, result)


def test_fake_provider_zero_segments_returns_empty_tuple_not_error() -> None:
    req = _request(0)
    result = FakeProvider().translate(req)
    assert result.translations == ()


def test_fake_provider_output_order_matches_input_order() -> None:
    """Siralama karismis olabilir -- her segmentin cevirisi doğru sirada mi?"""
    req = _request(5)
    result = FakeProvider().translate(req)
    for i, translation in enumerate(result.translations):
        assert translation == f"[tr] seg-{i}"


def test_fake_provider_duplicate_segment_texts_still_align() -> None:
    """Ayni metinli birden fazla segment olsa bile hizalama (sayica) korunmali."""
    segs = tuple(Segment(text="ayni metin", bbox=RECT) for _ in range(4))
    req = TranslationRequest(segments=segs, source_lang="en", target_lang="tr")
    result = FakeProvider().translate(req)
    assert len(result.translations) == 4
    assert all(t == "[tr] ayni metin" for t in result.translations)


def test_fake_provider_does_not_silently_drop_request_data() -> None:
    provider = FakeProvider()
    req = _request(3)
    provider.translate(req)
    assert provider.call_count == 1
    assert provider.requests[0] is req


# --------------------------------------------------------------------------
# ensure_aligned: FakeProvider'dan BAGIMSIZ, elle kurulmus (request, result)
# ciftleriyle dogrudan sinama
# --------------------------------------------------------------------------

@pytest.mark.parametrize(("n_seg", "n_tr"), [
    (0, 0), (1, 1), (3, 3), (10, 10),
])
def test_ensure_aligned_passes_when_counts_match(n_seg: int, n_tr: int) -> None:
    req = _request(n_seg)
    res = TranslationResult(
        translations=tuple(f"x{i}" for i in range(n_tr)),
        provider_id="manuel", latency_ms=0.0,
    )
    ensure_aligned(req, res)  # exception firlatmamali


@pytest.mark.parametrize(("n_seg", "n_tr"), [
    (0, 1), (1, 0), (3, 2), (3, 4), (1, 100), (5, 1),
])
def test_ensure_aligned_raises_on_every_mismatch_shape(
    n_seg: int, n_tr: int
) -> None:
    """FakeProvider'i devre disi birakip dogrudan bozuk bir sonuc uydur --
    ensure_aligned kendi basina gercekten yakaliyor mu?"""
    req = _request(n_seg)
    res = TranslationResult(
        translations=tuple(f"x{i}" for i in range(n_tr)),
        provider_id="bozuk-motor", latency_ms=0.0,
    )
    with pytest.raises(ContractViolation):
        ensure_aligned(req, res)


def test_ensure_aligned_error_message_contains_actionable_numbers() -> None:
    req = _request(3)
    res = TranslationResult(translations=("a",), provider_id="p",
                            latency_ms=0.0)
    with pytest.raises(ContractViolation) as info:
        ensure_aligned(req, res)
    msg = str(info.value)
    assert "3" in msg and "1" in msg


def test_contract_violation_is_a_translator_error_subclass_via_ensure() -> None:
    from src.contracts.errors import TranslatorError
    req = _request(2)
    res = TranslationResult(translations=(), provider_id="p", latency_ms=0.0)
    with pytest.raises(TranslatorError):
        ensure_aligned(req, res)  # kok siniftan da yakalanabilmeli


# --------------------------------------------------------------------------
# FakeProvider: determinizm ve hata enjeksiyonu
# --------------------------------------------------------------------------

def test_fake_provider_is_deterministic_across_independent_instances() -> None:
    req = _request(4)
    a = FakeProvider().translate(req)
    b = FakeProvider().translate(req)
    assert a == b


def test_fake_provider_error_injection_still_records_and_raises() -> None:
    provider = FakeProvider(error=ProviderTimeout("cok yavas"))
    with pytest.raises(ProviderTimeout):
        provider.translate(_request(2))
    assert provider.call_count == 1  # istek yine de kaydedilmeli


def test_fake_provider_source_lang_none_falls_back_to_detected_lang() -> None:
    provider = FakeProvider(detected_lang="ja")
    req = _request(1, source_lang=None)
    result = provider.translate(req)
    assert result.detected_lang == "ja"


# --------------------------------------------------------------------------
# FakeOcrEngine: determinizm + script disi davranis
# --------------------------------------------------------------------------

def _img() -> ImageArray:
    return np.zeros((2, 2, 3), dtype=np.uint8)


def _frame(seq: int) -> Frame:
    return Frame(image=_img(), rect=RECT, captured_at=float(seq), seq=seq)


def test_fake_ocr_engine_empty_script_never_raises_and_always_empty() -> None:
    engine = FakeOcrEngine()
    for seq in range(10):
        assert engine.recognize(_frame(seq), OcrPreset.DIALOGUE) == []


def test_fake_ocr_engine_two_independent_engines_agree() -> None:
    """Ayni betikle kurulan iki ayri motor -- ayni girdi icin ayni cikti mi?"""
    script = [
        [TextBlock(text="a", bbox=RECT, confidence=0.9)],
        [TextBlock(text="b", bbox=RECT, confidence=0.8)],
    ]
    e1 = FakeOcrEngine(script)
    e2 = FakeOcrEngine(script)
    for seq in range(6):  # betik uzunlugunu asip tekrar moduna da girer
        r1 = e1.recognize(_frame(seq), OcrPreset.MENU)
        r2 = e2.recognize(_frame(seq), OcrPreset.MENU)
        assert [b.text for b in r1] == [b.text for b in r2]


def test_fake_ocr_engine_mutating_returned_list_does_not_corrupt_script() -> None:
    engine = FakeOcrEngine([[TextBlock(text="sabit", bbox=RECT,
                                       confidence=1.0)]])
    first = engine.recognize(_frame(0), OcrPreset.TOOLTIP)
    first.append(TextBlock(text="enjekte", bbox=RECT, confidence=1.0))
    second = engine.recognize(_frame(1), OcrPreset.TOOLTIP)
    assert [b.text for b in second] == ["sabit"]
