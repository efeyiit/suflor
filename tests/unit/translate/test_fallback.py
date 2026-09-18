"""Bağlamlı kalite motorunun hızlı NLLB yedeği."""
from __future__ import annotations

import pytest

from src.contracts.errors import ContractViolation, ModelMissingError, ProviderTimeout, ProviderUnavailable
from src.contracts.interfaces import FakeProvider
from src.contracts.models import Rect, Segment, TranslationRequest
from src.translate.fallback import QualityFallbackProvider


def istek() -> TranslationRequest:
    return TranslationRequest((Segment("Open.", Rect(0, 0, 10, 10)),), "en", "tr")


@pytest.mark.parametrize("hata", [ProviderUnavailable("x"), ProviderTimeout("x"), ModelMissingError("x")])
def test_kalite_kullanilamazsa_nllb_yedegine_doner(hata: Exception) -> None:
    birincil = FakeProvider(provider_id="quality", error=hata)  # type: ignore[arg-type]
    yedek = FakeProvider(provider_id="nllb", translations={"Open.": "Aç."})
    sonuc = QualityFallbackProvider(birincil, yedek).translate(istek())
    assert sonuc.translations == ("Aç.",) and sonuc.provider_id == "nllb"
    assert birincil.call_count == 1 and yedek.call_count == 1


def test_kalite_basariliysa_yedek_cagrilmaz() -> None:
    birincil = FakeProvider(provider_id="quality", translations={"Open.": "Aç."})
    yedek = FakeProvider(provider_id="nllb")
    sonuc = QualityFallbackProvider(birincil, yedek).translate(istek())
    assert sonuc.provider_id == "quality" and yedek.call_count == 0


def test_sozlesme_ihlali_yedege_dusmez() -> None:
    birincil = FakeProvider(error=ContractViolation("bad"))
    yedek = FakeProvider()
    with pytest.raises(ContractViolation):
        QualityFallbackProvider(birincil, yedek).translate(istek())
    assert yedek.call_count == 0


def test_close_iki_saglayiciyi_bir_kez_kapatir() -> None:
    kapanan: list[str] = []

    class Kapanan(FakeProvider):
        def close(self) -> None:
            kapanan.append(self.provider_id)

    saglayici = QualityFallbackProvider(Kapanan(provider_id="quality"), Kapanan(provider_id="nllb"))
    saglayici.close(); saglayici.close()
    assert kapanan == ["quality", "nllb"]

