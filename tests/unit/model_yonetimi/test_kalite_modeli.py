"""Kalite modeli ve llama.cpp çalıştırıcısının doğrulamalı indirilmesi."""
from __future__ import annotations

import hashlib
import io
import zipfile
from pathlib import Path

import pytest

from src.contracts.errors import ProviderUnavailable
from src.model_yonetimi.kalite_modeli import (
    MODEL_DOSYASI,
    RUNTIME_DOSYASI,
    DosyaTanimi,
    KaliteModeliYoneticisi,
    _dogrulanmis_indir,
    _guvenli_cikar,
)


def tanim(ad: str, veri: bytes) -> DosyaTanimi:
    return DosyaTanimi(f"memory://{ad}", len(veri), hashlib.sha256(veri).hexdigest(), ad)


def test_dogrulanmis_indir_part_dosyadan_atomik_tasir_ve_ilerleme_bildirir(tmp_path: Path) -> None:
    veri = b"abcdefghij"
    hedef = tmp_path / "model.gguf"
    ilerleme: list[tuple[int, int]] = []

    _dogrulanmis_indir(
        tanim("model.gguf", veri), hedef, lambda _url: io.BytesIO(veri),
        lambda yapilan, toplam: ilerleme.append((yapilan, toplam)), chunk_size=3,
    )

    assert hedef.read_bytes() == veri
    assert not hedef.with_suffix(".gguf.part").exists()
    assert ilerleme[-1] == (len(veri), len(veri))


def test_yanlis_hash_hedefi_olusturmaz_ve_part_dosyayi_temizler(tmp_path: Path) -> None:
    veri = b"bozuk"
    spec = DosyaTanimi("memory://x", len(veri), "0" * 64, "x.bin")
    hedef = tmp_path / "x.bin"
    with pytest.raises(ProviderUnavailable):
        _dogrulanmis_indir(spec, hedef, lambda _url: io.BytesIO(veri), lambda *_: None)
    assert not hedef.exists() and not hedef.with_suffix(".bin.part").exists()


def test_yarida_kesilen_indirme_eski_gecerli_hedefi_bozmaz(tmp_path: Path) -> None:
    hedef = tmp_path / "x.bin"
    hedef.write_bytes(b"eski")

    class Patlayan(io.BytesIO):
        def read(self, size: int = -1) -> bytes:
            if self.tell() >= 2:
                raise OSError("network")
            return super().read(2)

    with pytest.raises(ProviderUnavailable):
        _dogrulanmis_indir(tanim("x.bin", b"yeni-veri"), hedef, lambda _url: Patlayan(b"yeni-veri"), lambda *_: None)
    assert hedef.read_bytes() == b"eski"


def test_zip_dizin_disina_cikamaz(tmp_path: Path) -> None:
    arsiv = tmp_path / "runtime.zip"
    with zipfile.ZipFile(arsiv, "w") as z:
        z.writestr("../kacis.exe", b"x")
    with pytest.raises(ProviderUnavailable):
        _guvenli_cikar(arsiv, tmp_path / "runtime")
    assert not (tmp_path / "kacis.exe").exists()


def test_yonetici_runtime_ve_modeli_dogrulayip_hazir_yapar(tmp_path: Path) -> None:
    runtime_buffer = io.BytesIO()
    with zipfile.ZipFile(runtime_buffer, "w") as z:
        z.writestr("llama-server.exe", b"runner")
        z.writestr("ggml-vulkan.dll", b"dll")
    runtime = runtime_buffer.getvalue()
    model = b"gguf-model"
    runtime_spec, model_spec = tanim("runtime.zip", runtime), tanim("model.gguf", model)
    veriler = {runtime_spec.url: runtime, model_spec.url: model}
    ilerleme: list[tuple[int, int]] = []
    yonetici = KaliteModeliYoneticisi(
        tmp_path / "models", tmp_path / "runtime", model_spec=model_spec, runtime_spec=runtime_spec,
        opener=lambda url: io.BytesIO(veriler[url]),
    )

    assert not yonetici.hazir_mi
    yonetici.indir(lambda yapilan, toplam: ilerleme.append((yapilan, toplam)))

    assert yonetici.hazir_mi
    assert yonetici.model_path.read_bytes() == model
    assert yonetici.executable_path.read_bytes() == b"runner"
    assert ilerleme[-1] == (len(runtime) + len(model), len(runtime) + len(model))


def test_sabit_manifest_pimli_kimlik_boyut_ve_hashleri_tasir() -> None:
    assert MODEL_DOSYASI.size == 2_497_280_256
    assert MODEL_DOSYASI.sha256 == "7485fe6f11af29433bc51cab58009521f205840f5b4ae3a32fa7f92e8534fdf5"
    assert "bc640142c66e1fdd12af0bd68f40445458f3869b" in MODEL_DOSYASI.url
    assert RUNTIME_DOSYASI.sha256 == "1ee3ad952f4ba71f438bd6d7bebef19e1c7af04adcaa35d08b4ddabb27d4c642"
    assert "b10964" in RUNTIME_DOSYASI.url
