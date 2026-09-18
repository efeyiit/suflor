"""Bağlamlı yerel LLM çeviri sağlayıcısı."""
from __future__ import annotations

import json

import pytest

from src.contracts.errors import ProviderTimeout, ProviderUnavailable
from src.contracts.models import Pair, Rect, Segment, TermHit, TranslationRequest
from src.translate.llama_local import LlamaLocalProvider


class SahteSohbet:
    def __init__(self, cevap: str = '{"translations":["Batı kapısını aç."]}', hata: Exception | None = None) -> None:
        self.cevap = cevap
        self.hata = hata
        self.cagrilar: list[tuple[str, str, int]] = []
        self.kapandi = 0

    def complete(self, system: str, user: str, max_tokens: int) -> str:
        self.cagrilar.append((system, user, max_tokens))
        if self.hata is not None:
            raise self.hata
        return self.cevap

    def close(self) -> None:
        self.kapandi += 1


def istek() -> TranslationRequest:
    return TranslationRequest(
        segments=(Segment("Open the west door.", Rect(0, 0, 200, 30), speaker="Simon"),),
        source_lang="eng_Latn",
        target_lang="tr",
        glossary_hits=(TermHit("West Door", "Batı Kapısı", 0, 9, note="özel oda adı"),),
        tm_examples=(Pair("Open the east door.", "Doğu kapısını aç.", 0.92),),
        style_profile="Blue Prince: doğal, kısa oyun Türkçesi; oda adlarını koru.",
    )


def test_baglam_sozluk_hafiza_stil_konusmaci_ve_butun_segmentleri_tasir() -> None:
    sohbet = SahteSohbet()
    saglayici = LlamaLocalProvider(sohbet)

    sonuc = saglayici.translate(istek())

    assert sonuc.translations == ("Batı kapısını aç.",)
    assert sonuc.provider_id == "local-llama-qwen3-4b" and sonuc.detected_lang == "eng_Latn"
    sistem, kullanici, azami = sohbet.cagrilar[0]
    veri = json.loads(kullanici)
    assert "yalnızca" in sistem.casefold() and azami >= 128
    assert veri["style"] == "Blue Prince: doğal, kısa oyun Türkçesi; oda adlarını koru."
    assert veri["glossary"] == [{"source": "West Door", "target": "Batı Kapısı", "note": "özel oda adı"}]
    assert veri["translation_memory"][0]["target"] == "Doğu kapısını aç."
    assert veri["segments"] == [{"id": 0, "speaker": "Simon", "text": "Open the west door."}]


def test_coklu_segment_json_dizisiyle_birebir_hizalanir() -> None:
    sohbet = SahteSohbet('{"translations":["Birinci.","İkinci."]}')
    saglayici = LlamaLocalProvider(sohbet)
    req = TranslationRequest(
        segments=(Segment("First.", Rect(0, 0, 10, 10)), Segment("Second.", Rect(0, 20, 10, 10))),
        source_lang="en", target_lang="tr",
    )

    assert saglayici.translate(req).translations == ("Birinci.", "İkinci.")


@pytest.mark.parametrize(
    "cevap",
    [
        '```json\n{"translations":["x"]}\n```',
        '{"translations":[]}',
        '{"translations":[4]}',
        '{"translations":["x"],"explanation":"y"}',
        'not json',
    ],
)
def test_bozuk_veya_hizalanmayan_model_ciktisi_reddedilir(cevap: str) -> None:
    with pytest.raises(ProviderUnavailable) as hata:
        LlamaLocalProvider(SahteSohbet(cevap)).translate(istek())
    assert "Open the west door" not in str(hata.value) and cevap not in str(hata.value)


def test_bos_istek_modeli_cagirmadan_bos_sonuc_dondurur() -> None:
    sohbet = SahteSohbet()
    sonuc = LlamaLocalProvider(sohbet).translate(TranslationRequest((), "en", "tr"))
    assert sonuc.translations == () and sohbet.cagrilar == []


def test_saglayici_hatasi_sinifini_korur_baska_hatayi_sarmalar() -> None:
    with pytest.raises(ProviderTimeout):
        LlamaLocalProvider(SahteSohbet(hata=ProviderTimeout("timeout"))).translate(istek())
    with pytest.raises(ProviderUnavailable) as hata:
        LlamaLocalProvider(SahteSohbet(hata=RuntimeError("secret source text"))).translate(istek())
    assert "secret source text" not in str(hata.value)


def test_close_sohbet_istemcisini_bir_kez_kapatir() -> None:
    sohbet = SahteSohbet()
    saglayici = LlamaLocalProvider(sohbet)
    saglayici.close()
    saglayici.close()
    assert sohbet.kapandi == 1

