"""Bağlamı kullanan yerel Qwen3 çeviri sağlayıcısı.

Bu modül model sürecini bilmez. Yalnızca mevcut ``TranslationRequest``
bağlamını deterministik bir JSON isteğine çevirir ve ``ChatClient`` üzerinden
üretilen katı JSON sonucunu doğrular.
"""
from __future__ import annotations

import json
import re
import time
from typing import Protocol

from src.contracts.errors import ContractViolation, ProviderUnavailable, TranslatorError
from src.contracts.interfaces import TranslationProvider, ensure_aligned
from src.contracts.models import TranslationRequest, TranslationResult

__all__ = ["ChatClient", "LlamaLocalProvider"]

_SAGLAYICI = "local-llama-qwen3-4b"
_SISTEM = (
    "Sen deneyimli bir oyun yerelleştirme çevirmenisin. Kaynak metni bağlam, konuşmacı, "
    "zorunlu terimler ve önceki çeviri örnekleriyle birlikte doğal Türkçeye çevir. Anlamı, "
    "mantıksal ilişkileri, özel adları, değişkenleri ve satır sırasını koru. Her giriş segmenti "
    "için tamamen Türkçe, tam bir çeviri üret; çeviri alanlarında İngilizce cümle bırakma. "
    "⟦ ve ⟧ arasındaki Türkçe terimleri aynen koru, yalnızca gereken Türkçe ekleri dışına ekle. "
    "Yalnızca şu biçimde geçerli JSON döndür: "
    '{"translations":["..."]}. Açıklama, Markdown veya ek anahtar yazma.'
)


class ChatClient(Protocol):
    def complete(self, system: str, user: str, max_tokens: int) -> str: ...
    def close(self) -> None: ...


def _kullanici_istegi(request: TranslationRequest) -> str:
    terimler = sorted(request.glossary_hits, key=lambda hit: len(hit.source_term), reverse=True)

    def terimleri_yerlestir(metin: str) -> str:
        sonuc = metin
        for hit in terimler:
            kaynak = " ".join(hit.source_term.split())
            hedef = " ".join(hit.target_term.split())
            if kaynak:
                sonuc = re.sub(re.escape(kaynak), lambda _eslesme: f"⟦{hedef}⟧", sonuc, flags=re.IGNORECASE)
        return sonuc

    veri: dict[str, object] = {
        "source_language": request.source_lang or "auto",
        "target_language": request.target_lang,
        "style": request.style_profile or "Doğal, kısa ve akıcı oyun Türkçesi.",
        "glossary": [
            {"source": hit.source_term, "target": hit.target_term, "note": hit.note}
            for hit in request.glossary_hits
        ],
        "translation_memory": [
            {"source": pair.source, "target": pair.target, "similarity": round(pair.score, 4)}
            for pair in request.tm_examples
        ],
        "segments": [
            {"id": i, "speaker": segment.speaker, "text": terimleri_yerlestir(segment.text)}
            for i, segment in enumerate(request.segments)
        ],
    }
    kurallar = ""
    if request.glossary_hits:
        eslemeler = "\n".join(
            f"- {' '.join(hit.source_term.split())} => {' '.join(hit.target_term.split())}"
            for hit in request.glossary_hits
        )
        yasaklar = " ".join(
            f"Çıktıda '{' '.join(hit.source_term.split())}' yazmak YASAKTIR."
            for hit in request.glossary_hits
        )
        zorunlular = " ".join(
            f"Çıktı ancak '{' '.join(hit.target_term.split())}' ifadesini içerirse geçerlidir."
            for hit in request.glossary_hits
        )
        kurallar = (
            "ZORUNLU TERİM KURALLARI (kaynakta geçen her terim hedefte tam karşılığıyla kullanılmalı):\n"
            f"{eslemeler}\n{yasaklar} {zorunlular} "
            "Ekleri Türkçe dilbilgisine göre hedef terime ekle.\n\n"
        )
    return f"{kurallar}GİRDİ JSON:\n{json.dumps(veri, ensure_ascii=False, separators=(',', ':'))}"


def _cevirileri_coz(ham: str, beklenen: int) -> tuple[str, ...]:
    if ham.lstrip().startswith("```"):
        raise ProviderUnavailable("kalite motoru JSON yerine Markdown döndürdü")
    try:
        veri = json.loads(ham)
    except (json.JSONDecodeError, TypeError) as e:
        raise ProviderUnavailable("kalite motoru geçerli JSON döndürmedi") from e
    if not isinstance(veri, dict) or set(veri) != {"translations"}:
        raise ProviderUnavailable("kalite motoru beklenmeyen sonuç şeması döndürdü")
    ceviriler = veri.get("translations")
    if not isinstance(ceviriler, list) or len(ceviriler) != beklenen or not all(isinstance(x, str) for x in ceviriler):
        raise ProviderUnavailable("kalite motoru segmentlerle hizalı çeviri döndürmedi")
    return tuple(ceviri.replace("⟦", "").replace("⟧", "") for ceviri in ceviriler)


class LlamaLocalProvider(TranslationProvider):
    """Yerel sohbet modelini bağlamlı oyun çevirmeni olarak kullanır."""

    def __init__(self, client: ChatClient) -> None:
        self._client = client
        self._kapali = False

    @property
    def provider_id(self) -> str:
        return _SAGLAYICI

    def translate(self, request: TranslationRequest) -> TranslationResult:
        if self._kapali:
            raise ProviderUnavailable("kalite sağlayıcısı kapatıldı")
        if not isinstance(request, TranslationRequest):
            raise ContractViolation(f"translate TranslationRequest bekler, gelen: {type(request).__name__}")
        baslangic = time.perf_counter()
        if not request.segments:
            return TranslationResult((), _SAGLAYICI, (time.perf_counter() - baslangic) * 1000.0,
                                     detected_lang=request.source_lang)
        kullanici = _kullanici_istegi(request)
        azami = min(2048, max(128, sum(len(segment.text) for segment in request.segments) * 2))
        try:
            ham = self._client.complete(_SISTEM, kullanici, azami)
        except TranslatorError:
            raise
        except Exception as e:
            raise ProviderUnavailable(f"kalite motoru çalışmadı: {type(e).__name__}") from e
        ceviriler = _cevirileri_coz(ham, len(request.segments))
        sonuc = TranslationResult(
            translations=ceviriler,
            provider_id=_SAGLAYICI,
            latency_ms=(time.perf_counter() - baslangic) * 1000.0,
            detected_lang=request.source_lang,
        )
        ensure_aligned(request, sonuc)
        return sonuc

    def close(self) -> None:
        if self._kapali:
            return
        self._kapali = True
        self._client.close()
