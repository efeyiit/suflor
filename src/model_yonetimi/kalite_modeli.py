"""Qwen3 kalite modeli ve llama.cpp çalıştırıcısı için doğrulamalı indirme."""
from __future__ import annotations

import hashlib
import importlib.util
import shutil
import stat
import sys
import urllib.request
import zipfile
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import BinaryIO, cast

from src.contracts.errors import ProviderUnavailable

__all__ = ["DosyaTanimi", "KaliteModeliDurumu", "KaliteModeliYoneticisi", "MODEL_DOSYASI", "RUNTIME_DOSYASI"]


@dataclass(frozen=True)
class DosyaTanimi:
    url: str
    size: int
    sha256: str
    filename: str


MODEL_DOSYASI = DosyaTanimi(
    "https://huggingface.co/Qwen/Qwen3-4B-GGUF/resolve/"
    "bc640142c66e1fdd12af0bd68f40445458f3869b/Qwen3-4B-Q4_K_M.gguf?download=true",
    2_497_280_256,
    "7485fe6f11af29433bc51cab58009521f205840f5b4ae3a32fa7f92e8534fdf5",
    "Qwen3-4B-Q4_K_M.gguf",
)
RUNTIME_DOSYASI = DosyaTanimi(
    "https://github.com/ggml-org/llama.cpp/releases/download/b10964/llama-b10964-bin-win-vulkan-x64.zip",
    31_674_542,
    "1ee3ad952f4ba71f438bd6d7bebef19e1c7af04adcaa35d08b4ddabb27d4c642",
    "llama-b10964-bin-win-vulkan-x64.zip",
)

Progress = Callable[[int, int], None]
Opener = Callable[[str], BinaryIO]

_CRT_DOSYALARI = ("msvcp140.dll", "vcruntime140.dll", "vcruntime140_1.dll")


class KaliteModeliDurumu(StrEnum):
    EKSIK = "eksik"
    HAZIR = "hazir"


def _url_ac(url: str) -> BinaryIO:
    return cast(BinaryIO, urllib.request.urlopen(url, timeout=60))  # sabit manifest URL'leri


def _dogrulanmis_indir(
    spec: DosyaTanimi,
    hedef: Path,
    opener: Opener,
    progress: Progress,
    *,
    chunk_size: int = 1024 * 1024,
) -> None:
    """Akışla `.part` dosyasına indir, boyut/hash doğrula ve atomik taşı."""
    if chunk_size < 1:
        raise ValueError("chunk_size pozitif olmalı")
    hedef.parent.mkdir(parents=True, exist_ok=True)
    part = hedef.with_suffix(hedef.suffix + ".part")
    ozet = hashlib.sha256()
    yazilan = 0
    try:
        with opener(spec.url) as kaynak, part.open("wb") as cikti:
            while True:
                parca = kaynak.read(chunk_size)
                if not parca:
                    break
                cikti.write(parca)
                ozet.update(parca)
                yazilan += len(parca)
                progress(yazilan, spec.size)
        if yazilan != spec.size or ozet.hexdigest().casefold() != spec.sha256.casefold():
            raise ProviderUnavailable("indirilen dosyanın boyut veya SHA-256 doğrulaması başarısız")
        part.replace(hedef)
    except ProviderUnavailable:
        part.unlink(missing_ok=True)
        raise
    except Exception as e:
        part.unlink(missing_ok=True)
        raise ProviderUnavailable(f"model indirme başarısız: {type(e).__name__}") from e


def _guvenli_cikar(arsiv: Path, hedef: Path) -> None:
    """ZIP üyelerini hedef dışına çıkmadan ve sembolik bağ kabul etmeden açar."""
    hedef.mkdir(parents=True, exist_ok=True)
    kok = hedef.resolve()
    try:
        with zipfile.ZipFile(arsiv) as z:
            for uye in z.infolist():
                cikti = (hedef / uye.filename).resolve()
                kip = (uye.external_attr >> 16) & 0o170000
                if not cikti.is_relative_to(kok) or stat.S_ISLNK(kip):
                    raise ProviderUnavailable("çalıştırıcı arşivi güvenli olmayan dosya yolu içeriyor")
            for uye in z.infolist():
                cikti = hedef / uye.filename
                if uye.is_dir():
                    cikti.mkdir(parents=True, exist_ok=True)
                    continue
                cikti.parent.mkdir(parents=True, exist_ok=True)
                with z.open(uye) as kaynak, cikti.open("wb") as dosya:
                    shutil.copyfileobj(kaynak, dosya)
    except ProviderUnavailable:
        raise
    except (OSError, zipfile.BadZipFile) as e:
        raise ProviderUnavailable(f"çalıştırıcı arşivi açılamadı: {type(e).__name__}") from e


def _varsayilan_bagimlilik_dizinleri() -> tuple[Path, ...]:
    """Paketli ve geliştirme kurulumlarında MSVC çalışma kitaplıklarını bulur."""
    adaylar: list[Path] = []
    pyside = importlib.util.find_spec("PySide6")
    if pyside is not None and pyside.origin:
        adaylar.append(Path(pyside.origin).resolve().parent)
    adaylar.append(Path(sys.executable).resolve().parent)
    paket_koku = getattr(sys, "_MEIPASS", None)
    if paket_koku:
        adaylar.append(Path(paket_koku).resolve())
    return tuple(dict.fromkeys(adaylar))


def _crt_yerlestir(hedef_dizin: Path, kaynak_dizinler: Sequence[Path]) -> None:
    """llama.cpp için gereken MSVC DLL'lerini çalıştırıcının yanına kopyalar."""
    if not hedef_dizin.is_dir():
        return
    for ad in _CRT_DOSYALARI:
        hedef = hedef_dizin / ad
        if hedef.is_file():
            continue
        for kaynak_dizin in kaynak_dizinler:
            kaynak = Path(kaynak_dizin) / ad
            if kaynak.is_file():
                shutil.copy2(kaynak, hedef)
                break


class KaliteModeliYoneticisi:
    def __init__(
        self,
        model_root: Path,
        runtime_root: Path,
        *,
        model_spec: DosyaTanimi = MODEL_DOSYASI,
        runtime_spec: DosyaTanimi = RUNTIME_DOSYASI,
        opener: Opener = _url_ac,
        dependency_dirs: Sequence[Path] | None = None,
    ) -> None:
        self._model_spec = model_spec
        self._runtime_spec = runtime_spec
        self._opener = opener
        self._model_dir = Path(model_root) / "qwen3-4b"
        self._runtime_dir = Path(runtime_root) / "llama-b10964-vulkan"
        self._dependency_dirs = tuple(dependency_dirs) if dependency_dirs is not None else _varsayilan_bagimlilik_dizinleri()
        if self.executable_path.is_file():
            _crt_yerlestir(self._runtime_dir, self._dependency_dirs)

    @property
    def model_path(self) -> Path:
        return self._model_dir / self._model_spec.filename

    @property
    def executable_path(self) -> Path:
        return self._runtime_dir / "llama-server.exe"

    @property
    def hazir_mi(self) -> bool:
        return (
            self.executable_path.is_file()
            and all((self._runtime_dir / ad).is_file() for ad in _CRT_DOSYALARI)
            and self.model_path.is_file()
            and self.model_path.stat().st_size == self._model_spec.size
        )

    @property
    def durum(self) -> KaliteModeliDurumu:
        return KaliteModeliDurumu.HAZIR if self.hazir_mi else KaliteModeliDurumu.EKSIK

    @property
    def toplam_boyut(self) -> int:
        return self._runtime_spec.size + self._model_spec.size

    def indir(self, progress: Progress) -> None:
        toplam = self.toplam_boyut
        yapilan = 0
        if not self.executable_path.is_file():
            arsiv = self._runtime_dir.parent / self._runtime_spec.filename
            _dogrulanmis_indir(
                self._runtime_spec,
                arsiv,
                self._opener,
                lambda anlik, _boyut: progress(yapilan + anlik, toplam),
            )
            _guvenli_cikar(arsiv, self._runtime_dir)
            arsiv.unlink(missing_ok=True)
            if not self.executable_path.is_file():
                raise ProviderUnavailable("çalıştırıcı arşivinde llama-server.exe bulunamadı")
            _crt_yerlestir(self._runtime_dir, self._dependency_dirs)
            yapilan += self._runtime_spec.size
        else:
            _crt_yerlestir(self._runtime_dir, self._dependency_dirs)
            yapilan += self._runtime_spec.size

        if not all((self._runtime_dir / ad).is_file() for ad in _CRT_DOSYALARI):
            raise ProviderUnavailable("llama.cpp için gereken Microsoft çalışma kitaplıkları bulunamadı")

        if not (self.model_path.is_file() and self.model_path.stat().st_size == self._model_spec.size):
            _dogrulanmis_indir(
                self._model_spec,
                self.model_path,
                self._opener,
                lambda anlik, _boyut: progress(yapilan + anlik, toplam),
            )
        progress(toplam, toplam)
