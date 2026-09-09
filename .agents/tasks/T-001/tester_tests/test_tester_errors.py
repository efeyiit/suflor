"""TESTER -- bagimsiz hata hiyerarsisi dogrulamasi.

env.md #4: "Hata hiyerarsisi dogru mu? Alti hata sinifinin hepsi
TranslatorError'dan turemeli; issubclass ile dogrula."

Beklenen alti sinif, implementer'in test dosyasi OKUNMADAN dogrudan tasarim
dokumani 5.3'ten transkribe edilmistir:
    CaptureError, ModelMissingError, OcrError, ProviderUnavailable,
    ProviderTimeout, ContractViolation
"""
from __future__ import annotations

import pytest

from src.contracts import errors as errors_module
from src.contracts.errors import (
    CaptureError,
    ContractViolation,
    ModelMissingError,
    OcrError,
    ProviderTimeout,
    ProviderUnavailable,
    TranslatorError,
)

# Tasarim dokumani 5.3'ten BAGIMSIZ transkribe edilen beklenen kume.
EXPECTED_SUBCLASS_NAMES = {
    "CaptureError", "ModelMissingError", "OcrError",
    "ProviderUnavailable", "ProviderTimeout", "ContractViolation",
}

EXPECTED_SUBCLASSES: tuple[type[TranslatorError], ...] = (
    CaptureError, ModelMissingError, OcrError,
    ProviderUnavailable, ProviderTimeout, ContractViolation,
)


def test_translator_error_is_root_exception_subclass() -> None:
    assert issubclass(TranslatorError, Exception)


def test_exactly_six_subclasses_exist_no_more_no_less() -> None:
    """Fazladan uydurulmus 7. bir hata sinifi ya da eksik biri var mi?
    `__subclasses__()` dogrudan TranslatorError'dan tureyenleri sayar."""
    direct_children = {c.__name__ for c in TranslatorError.__subclasses__()}
    assert direct_children == EXPECTED_SUBCLASS_NAMES, (
        f"beklenen: {EXPECTED_SUBCLASS_NAMES}, bulunan: {direct_children}"
    )


@pytest.mark.parametrize("err_cls", EXPECTED_SUBCLASSES,
                         ids=lambda c: c.__name__)
def test_issubclass_of_translator_error(err_cls: type[TranslatorError]) -> None:
    assert issubclass(err_cls, TranslatorError)


@pytest.mark.parametrize("err_cls", EXPECTED_SUBCLASSES,
                         ids=lambda c: c.__name__)
def test_root_does_not_derive_from_children(
    err_cls: type[TranslatorError],
) -> None:
    """Kok, kendi cocugunun alt sinifi olamaz (dongusel hiyerarsi kontrolu)."""
    assert not issubclass(TranslatorError, err_cls)
    assert err_cls is not TranslatorError


def test_hierarchy_is_flat_no_sibling_inherits_from_sibling() -> None:
    """5.6: ProviderTimeout ile ProviderUnavailable farkli davranis
    tetikler (biri geri cekilme/backoff, digeri iptal). Ic ice tureselerdi
    bir except digerini yutardi -- bu yuzden hiyerarsi kasitli olarak duz."""
    for a in EXPECTED_SUBCLASSES:
        for b in EXPECTED_SUBCLASSES:
            if a is not b:
                assert not issubclass(a, b), (
                    f"{a.__name__} yanlislikla {b.__name__}'den turemis"
                )


@pytest.mark.parametrize("err_cls", EXPECTED_SUBCLASSES,
                         ids=lambda c: c.__name__)
def test_each_error_catchable_via_single_root_except(
    err_cls: type[TranslatorError],
) -> None:
    """Orkestratorun 'hicbir hata pipeline'i durdurmaz' ilkesi tek bir
    `except TranslatorError` blogunun HER alt sinifi yakalamasina dayanir."""
    caught = False
    try:
        raise err_cls("adversarial-mesaj")
    except TranslatorError as exc:
        caught = True
        assert isinstance(exc, err_cls)
        assert "adversarial-mesaj" in str(exc)
    assert caught, f"{err_cls.__name__} genel TranslatorError ile yakalanamadi"


@pytest.mark.parametrize("err_cls", EXPECTED_SUBCLASSES,
                         ids=lambda c: c.__name__)
def test_error_instantiates_with_zero_arguments(
    err_cls: type[TranslatorError],
) -> None:
    """5.6 pipeline'in genel kurtarma yolu icin argumansiz olusturulabilmeli."""
    instance = err_cls()
    assert isinstance(instance, TranslatorError)


@pytest.mark.parametrize("err_cls", EXPECTED_SUBCLASSES,
                         ids=lambda c: c.__name__)
def test_error_is_not_accidentally_a_builtin_exception_alias(
    err_cls: type[TranslatorError],
) -> None:
    """Her sinif GERCEKTEN kendine ait bir tip olmali -- birine baska bir
    ismin takma adi (alias) verilmis olabilir mi?"""
    assert err_cls.__module__ == "src.contracts.errors"
    # Her biri farkli bir sinif nesnesi olmali (ayni siniftan iki farkli
    # isim degil).
    others = [c for c in EXPECTED_SUBCLASSES if c is not err_cls]
    assert err_cls not in others
    assert all(err_cls.__name__ != o.__name__ for o in others)


def test_module_all_matches_expected_taxonomy_exactly() -> None:
    exported = set(errors_module.__all__)
    assert exported == EXPECTED_SUBCLASS_NAMES | {"TranslatorError"}


def test_no_sensitive_content_leak_helpers_in_module() -> None:
    """PROTOKOL 6.7: hata mesajlarina OCR/ceviri/API anahtari asla loglanmaz.
    Bu statik bir tasarim kurali oldugundan modulun kendisinin herhangi bir
    otomatik loglama / print yan etkisi tasimadigini denetliyoruz."""
    import inspect
    source = inspect.getsource(errors_module)
    assert "print(" not in source
    assert "logging" not in source
