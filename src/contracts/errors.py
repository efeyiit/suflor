"""Suflor hata taksonomisi -- SOZLESME.

Tasarim dokumani 5.3. Tek bir kok (`TranslatorError`) altinda toplanan duz bir
hiyerarsi: pipeline'in "hicbir hata pipeline'i durdurmaz" ilkesi, orkestratorun
tek bir `except TranslatorError` ile toparlanabilmesine dayanir.

Hiyerarsi bilerek **duzdur** -- kardes siniflar birbirinden turemez. Ornegin
`ProviderTimeout` bir `ProviderUnavailable` degildir: 5.6'ya gore zaman asimi
istegi iptal edip bir sonraki kareyi bekler, kullanilamazlik ise motor
dususu tetikler. Ic ice tureseler bu iki davranis birbirini yutardi.

Not: hata mesajlarina OCR metni, ceviri icerigi veya API anahtari konmaz
(PROTOKOL 6.7).
"""
from __future__ import annotations

__all__ = [
    "TranslatorError",
    "CaptureError",
    "ModelMissingError",
    "OcrError",
    "ProviderUnavailable",
    "ProviderTimeout",
    "ContractViolation",
]


class TranslatorError(Exception):
    """Suflor'un firlattigi butun hatalarin koku."""


class CaptureError(TranslatorError):
    """Yakalama basarisiz: bolge gecersiz, monitor yok, korumali icerik."""


class ModelMissingError(TranslatorError):
    """Gerekli model dosyasi diskte yok; indirme gerekiyor."""


class OcrError(TranslatorError):
    """OCR motoru calisamadi veya sonuc uretemedi."""


class ProviderUnavailable(TranslatorError):
    """Ceviri saglayicisi kullanilamiyor: OOM, ag hatasi, kota asimi."""


class ProviderTimeout(TranslatorError):
    """Ceviri saglayicisi butce icinde cevap vermedi."""


class ContractViolation(TranslatorError):
    """Sozlesme ihlali: donen ceviri sayisi segment sayisiyla uyusmadi."""
