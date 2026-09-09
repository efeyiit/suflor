"""T-001 -- hata taksonomisi.

Tasarim dokumani 5.3: TranslatorError kokunden turemis alti alt sinif.
Pipeline'in "hicbir hata pipeline'i durdurmaz" ilkesi tek bir kok yakalamaya
dayanir; hiyerarsi bozulursa yakalama delinir.
"""
from __future__ import annotations

import pytest

from src.contracts.errors import (
    CaptureError,
    ContractViolation,
    ModelMissingError,
    OcrError,
    ProviderTimeout,
    ProviderUnavailable,
    TranslatorError,
)

SUBCLASSES: tuple[type[TranslatorError], ...] = (
    CaptureError,
    ModelMissingError,
    OcrError,
    ProviderUnavailable,
    ProviderTimeout,
    ContractViolation,
)


def test_root_is_an_exception() -> None:
    assert issubclass(TranslatorError, Exception)


@pytest.mark.parametrize("err", SUBCLASSES, ids=lambda e: e.__name__)
def test_every_error_derives_from_root(err: type[TranslatorError]) -> None:
    assert issubclass(err, TranslatorError)
    assert err is not TranslatorError


@pytest.mark.parametrize("err", SUBCLASSES, ids=lambda e: e.__name__)
def test_error_can_be_raised_and_caught_as_root(
    err: type[TranslatorError],
) -> None:
    with pytest.raises(TranslatorError) as info:
        raise err("mesaj")
    assert isinstance(info.value, err)
    assert str(info.value) == "mesaj"


@pytest.mark.parametrize("err", SUBCLASSES, ids=lambda e: e.__name__)
def test_error_accepts_no_arguments(err: type[TranslatorError]) -> None:
    assert isinstance(err(), TranslatorError)


def test_subclasses_are_distinct_types() -> None:
    assert len(set(SUBCLASSES)) == len(SUBCLASSES)


def test_siblings_do_not_catch_each_other() -> None:
    """ProviderTimeout, ProviderUnavailable'in alt sinifi olmamali."""
    for a in SUBCLASSES:
        for b in SUBCLASSES:
            if a is not b:
                assert not issubclass(a, b), f"{a.__name__} <- {b.__name__}"


def test_exported_names_are_exactly_the_taxonomy() -> None:
    from src.contracts import errors

    assert set(errors.__all__) == {
        "TranslatorError",
        "CaptureError",
        "ModelMissingError",
        "OcrError",
        "ProviderUnavailable",
        "ProviderTimeout",
        "ContractViolation",
    }
