"""Bağlamlı kalite sağlayıcısı için hızlı yerel sağlayıcı yedeği."""
from __future__ import annotations

from src.contracts.errors import ModelMissingError, ProviderTimeout, ProviderUnavailable
from src.contracts.interfaces import TranslationProvider
from src.contracts.models import TranslationRequest, TranslationResult

__all__ = ["QualityFallbackProvider"]


class QualityFallbackProvider(TranslationProvider):
    def __init__(self, primary: TranslationProvider, fallback: TranslationProvider) -> None:
        self._primary = primary
        self._fallback = fallback
        self._kapali = False
        self._primary_disabled = False

    @property
    def provider_id(self) -> str:
        return f"quality-fallback:{self._primary.provider_id}->{self._fallback.provider_id}"

    def translate(self, request: TranslationRequest) -> TranslationResult:
        if not self._primary_disabled:
            try:
                return self._primary.translate(request)
            except (ModelMissingError, ProviderUnavailable):
                self._primary_disabled = True
            except ProviderTimeout:
                pass
        return self._fallback.translate(request)

    def close(self) -> None:
        if self._kapali:
            return
        self._kapali = True
        for saglayici in (self._primary, self._fallback):
            kapat = getattr(saglayici, "close", None)
            if callable(kapat):
                kapat()

