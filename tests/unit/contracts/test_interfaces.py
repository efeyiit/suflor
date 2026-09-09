"""T-001 -- soyut arayuzler ve sahte referans implementasyonlari.

Bu dosyanin en kritik testi FakeProvider'in hizalama sozlesmesidir:
len(result.translations) == len(request.segments), her zaman.
Diger butun ajanlar testlerini bu sahtelerin uzerine kuracak; sahteler
bozuksa butun test paketi sessizce yalan soyler.
"""
from __future__ import annotations

import abc
import inspect

import numpy as np
import pytest

from src.contracts.errors import ContractViolation, ProviderUnavailable
from src.contracts.interfaces import (
    FakeOcrEngine,
    FakeProvider,
    OcrEngine,
    TranslationProvider,
    ensure_aligned,
)
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

RECT = Rect(x=0, y=0, w=100, h=20)


def image(value: int = 1) -> ImageArray:
    return np.full((2, 2, 3), value, dtype=np.uint8)


def frame(seq: int = 0) -> Frame:
    return Frame(image=image(), rect=RECT, captured_at=float(seq), seq=seq)


def block(text: str) -> TextBlock:
    return TextBlock(text=text, bbox=RECT, confidence=0.95)


def segments(count: int) -> tuple[Segment, ...]:
    return tuple(Segment(text=f"line {i}", bbox=RECT) for i in range(count))


def request(count: int, **kwargs: object) -> TranslationRequest:
    params: dict[str, object] = {
        "segments": segments(count),
        "source_lang": "en",
        "target_lang": "tr",
    }
    params.update(kwargs)
    return TranslationRequest(**params)  # type: ignore[arg-type]


# --------------------------------------------------------------------------
# soyutluk
# --------------------------------------------------------------------------

@pytest.mark.parametrize("iface", [OcrEngine, TranslationProvider],
                         ids=lambda c: c.__name__)
def test_interface_is_abstract(iface: type) -> None:
    assert issubclass(iface, abc.ABC)
    assert inspect.isabstract(iface)
    with pytest.raises(TypeError):
        iface()  # type: ignore[abstract]


def test_ocr_engine_requires_recognize() -> None:
    assert "recognize" in OcrEngine.__abstractmethods__

    class Bos(OcrEngine):
        pass

    with pytest.raises(TypeError):
        Bos()  # type: ignore[abstract]


def test_translation_provider_requires_translate_and_id() -> None:
    assert OcrEngine.__abstractmethods__ == frozenset({"recognize"})
    assert TranslationProvider.__abstractmethods__ == frozenset(
        {"translate", "provider_id"})


def test_recognize_signature_matches_design_doc() -> None:
    sig = inspect.signature(OcrEngine.recognize)
    assert list(sig.parameters) == ["self", "frame", "preset"]


def test_translate_signature_matches_design_doc() -> None:
    sig = inspect.signature(TranslationProvider.translate)
    assert list(sig.parameters) == ["self", "request"]


# --------------------------------------------------------------------------
# ensure_aligned -- sozlesmenin makineyle korunmasi
# --------------------------------------------------------------------------

def test_ensure_aligned_accepts_matching_counts() -> None:
    req = request(3)
    res = TranslationResult(translations=("a", "b", "c"), provider_id="x",
                            latency_ms=0.0)
    ensure_aligned(req, res)  # yukselmemeli


@pytest.mark.parametrize(("n_seg", "n_tr"), [(3, 2), (0, 1), (1, 0), (2, 5)])
def test_ensure_aligned_raises_contract_violation(n_seg: int,
                                                  n_tr: int) -> None:
    req = request(n_seg)
    res = TranslationResult(translations=tuple("x" * n_tr),
                            provider_id="x", latency_ms=0.0)
    with pytest.raises(ContractViolation) as info:
        ensure_aligned(req, res)
    message = str(info.value)
    assert str(n_seg) in message and str(n_tr) in message


# --------------------------------------------------------------------------
# FakeOcrEngine
# --------------------------------------------------------------------------

def test_fake_ocr_engine_is_a_concrete_ocr_engine() -> None:
    engine = FakeOcrEngine()
    assert isinstance(engine, OcrEngine)
    assert not inspect.isabstract(FakeOcrEngine)


def test_fake_ocr_engine_without_script_returns_empty() -> None:
    engine = FakeOcrEngine()
    assert engine.recognize(frame(0), OcrPreset.DIALOGUE) == []
    assert engine.recognize(frame(1), OcrPreset.MENU) == []


def test_fake_ocr_engine_walks_the_script_in_order() -> None:
    engine = FakeOcrEngine([[block("bir")], [block("iki"), block("uc")]])
    first = engine.recognize(frame(0), OcrPreset.DIALOGUE)
    second = engine.recognize(frame(1), OcrPreset.DIALOGUE)
    assert [b.text for b in first] == ["bir"]
    assert [b.text for b in second] == ["iki", "uc"]


def test_fake_ocr_engine_repeats_last_entry_when_script_exhausted() -> None:
    engine = FakeOcrEngine([[block("bir")]])
    for seq in range(4):
        assert [b.text for b in engine.recognize(frame(seq),
                                                 OcrPreset.SUBTITLE)] == ["bir"]


def test_fake_ocr_engine_is_deterministic() -> None:
    script = [[block("a")], [block("b")]]
    a, b = FakeOcrEngine(script), FakeOcrEngine(script)
    for seq in range(5):
        assert a.recognize(frame(seq), OcrPreset.MENU) == b.recognize(
            frame(seq), OcrPreset.MENU)


def test_fake_ocr_engine_returns_fresh_lists() -> None:
    engine = FakeOcrEngine([[block("a")]])
    out = engine.recognize(frame(0), OcrPreset.MENU)
    out.clear()
    assert [b.text for b in engine.recognize(frame(1), OcrPreset.MENU)] == ["a"]


def test_fake_ocr_engine_records_calls() -> None:
    engine = FakeOcrEngine()
    assert engine.call_count == 0
    engine.recognize(frame(7), OcrPreset.TOOLTIP)
    assert engine.call_count == 1
    assert engine.calls[0][0].seq == 7
    assert engine.calls[0][1] is OcrPreset.TOOLTIP


# --------------------------------------------------------------------------
# FakeProvider -- hizalama sozlesmesi
# --------------------------------------------------------------------------

def test_fake_provider_is_a_concrete_translation_provider() -> None:
    provider = FakeProvider()
    assert isinstance(provider, TranslationProvider)
    assert provider.provider_id == "fake"


@pytest.mark.parametrize("count", [0, 1, 2, 3, 10])
def test_fake_provider_translations_align_with_segments(count: int) -> None:
    req = request(count)
    res = FakeProvider().translate(req)
    assert len(res.translations) == len(req.segments) == count
    ensure_aligned(req, res)


def test_fake_provider_result_is_deterministic() -> None:
    req = request(3)
    first = FakeProvider().translate(req)
    second = FakeProvider().translate(req)
    assert first == second
    assert first.latency_ms == 0.0
    assert first.from_cache is False
    assert first.partial is False


def test_fake_provider_marks_target_language_per_segment() -> None:
    res = FakeProvider().translate(request(2))
    assert res.translations == ("[tr] line 0", "[tr] line 1")


def test_fake_provider_uses_scripted_table_when_given() -> None:
    provider = FakeProvider(translations={"line 1": "ikinci satir"})
    res = provider.translate(request(3))
    assert res.translations == ("[tr] line 0", "ikinci satir", "[tr] line 2")
    assert len(res.translations) == 3


def test_fake_provider_reports_its_own_id() -> None:
    provider = FakeProvider(provider_id="fake-nmt")
    assert provider.provider_id == "fake-nmt"
    assert provider.translate(request(1)).provider_id == "fake-nmt"


def test_fake_provider_detected_lang_follows_source_lang() -> None:
    provider = FakeProvider(detected_lang="de")
    assert provider.translate(request(1)).detected_lang == "en"
    auto = request(1, source_lang=None)
    assert provider.translate(auto).detected_lang == "de"


def test_fake_provider_records_requests_for_assertions() -> None:
    provider = FakeProvider()
    hit = TermHit(source_term="Estus", target_term="Estus Sisesi",
                  start=0, end=5)
    example = Pair(source="hi", target="selam", score=0.9)
    req = request(1, glossary_hits=(hit,), tm_examples=(example,),
                  style_profile="resmi")
    provider.translate(req)
    assert provider.call_count == 1
    assert provider.requests[0].glossary_hits == (hit,)
    assert provider.requests[0].tm_examples == (example,)
    assert provider.requests[0].style_profile == "resmi"


def test_fake_provider_accepts_image_crops() -> None:
    req = request(2, image_crops=(image(1), image(2)))
    res = FakeProvider().translate(req)
    assert len(res.translations) == 2


def test_fake_provider_can_inject_a_failure() -> None:
    provider = FakeProvider(error=ProviderUnavailable("OOM"))
    with pytest.raises(ProviderUnavailable):
        provider.translate(request(1))


def test_fake_provider_latency_is_configurable_but_fixed() -> None:
    provider = FakeProvider(latency_ms=12.5)
    assert provider.translate(request(1)).latency_ms == 12.5
    assert provider.translate(request(2)).latency_ms == 12.5
