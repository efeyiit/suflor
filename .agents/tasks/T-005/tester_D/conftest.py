"""TESTER-D kosum kosullari.

Mercek D testleri iki katmanda calisir:

1. **Yerinde** (hizli): `src/capture` ve `headless_check.py` KAYNAK METNI uzerinde
   ve canli nesneler uzerinde olcum. Hicbir dosya degistirilmez.
2. **Ayna agacinda** (yavas): deponun gecici bir kopyasi kurulur, mutasyon ORADA
   yapilir ve bes kabul komutu ayna agacinda kosturulur. `src/` ASLA yazilmaz.

Gercek `mss` burada da yasaktir (K1): oturum basinda `sys.modules["mss"]`
engellenir. Mercek D `MssBackend`'i yalnizca **tembellik** (yapim `mss`'e
dokunmaz) icin canli kullanir.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import types
from collections.abc import Iterator, Sequence
from pathlib import Path

import pytest

DEPO = Path(__file__).resolve().parents[4]
if str(DEPO) not in sys.path:
    sys.path.insert(0, str(DEPO))

AYNALANAN = ("src", "tests")
KAPI_DOSYASI = Path(".agents") / "tasks" / "T-005" / "headless_check.py"

# Paketin BES kabul komutu, birebir (packet.md `acceptance`).
KABUL_KOMUTLARI: list[tuple[str, list[str]]] = [
    ("G1-mypy", [sys.executable, "-m", "mypy", "--strict", "--explicit-package-bases",
                 "src/capture/service.py", "src/capture/monitors.py"]),
    ("G2-pytest", [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                   "tests/unit/capture/test_service.py",
                   "tests/unit/capture/test_monitors.py"]),
    ("G3-headless", [sys.executable, str(KAPI_DOSYASI)]),
    ("G4-kapsam", [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                   "tests/unit/capture/test_service.py",
                   "tests/unit/capture/test_monitors.py",
                   "--cov=src.capture.service", "--cov=src.capture.monitors",
                   "--cov-fail-under=95", "--cov-report=term-missing"]),
    ("G5-tumdizin", [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                     "tests/unit/capture"]),
]


def _gercek_mss_cagrildi(*_a: object, **_k: object) -> object:
    raise AssertionError("gercek mss tester_D testinde de yasak (K1)")


@pytest.fixture(scope="session", autouse=True)
def mss_engeli() -> Iterator[None]:
    """K1: mercek D de gercek ekrana dokunmaz."""
    onceki = sys.modules.get("mss")
    engel = types.ModuleType("mss")
    engel.MSS = _gercek_mss_cagrildi        # type: ignore[attr-defined]
    engel.mss = _gercek_mss_cagrildi        # type: ignore[attr-defined]
    sys.modules["mss"] = engel
    try:
        yield
    finally:
        if onceki is None:
            sys.modules.pop("mss", None)
        else:
            sys.modules["mss"] = onceki


class Ayna:
    """Deponun gecici kopyasi: mutasyon burada yapilir, `src/` yazilmaz."""

    def __init__(self, kok: Path) -> None:
        self.kok = kok

    def yaz(self, rel: str, yamalar: Sequence[tuple[str, str]]) -> None:
        p = self.kok / rel
        metin = (DEPO / rel).read_text(encoding="utf-8")
        for eski, yeni in yamalar:
            assert eski in metin, f"yama hedefi bulunamadi ({rel}): {eski[:120]!r}"
            metin = metin.replace(eski, yeni, 1)
        p.write_text(metin, encoding="utf-8")

    def geri_al(self) -> None:
        for rel in ("src/capture/service.py", "src/capture/monitors.py",
                    "tests/unit/capture/conftest.py"):
            shutil.copyfile(DEPO / rel, self.kok / rel)

    def kapilar(self, hangi: Sequence[str] | None = None) -> dict[str, int]:
        """Bes kabul komutunu ayna agacinda kosar; {kapi_adi: exit_code}."""
        sonuc: dict[str, int] = {}
        for ad, argv in KABUL_KOMUTLARI:
            if hangi is not None and ad not in hangi:
                continue
            r = subprocess.run(argv, cwd=str(self.kok), capture_output=True,
                               text=True, encoding="utf-8", errors="replace")
            sonuc[ad] = r.returncode
            sonuc[f"{ad}::cikti"] = (r.stdout or "") + (r.stderr or "")  # type: ignore[assignment]
        return sonuc


@pytest.fixture(scope="session")
def ayna() -> Iterator[Ayna]:
    tmp = Path(tempfile.mkdtemp(prefix="tester_d_ayna_"))
    try:
        for ad in AYNALANAN:
            shutil.copytree(DEPO / ad, tmp / ad,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc",
                                                          ".pytest_cache"))
        (tmp / KAPI_DOSYASI.parent).mkdir(parents=True, exist_ok=True)
        shutil.copyfile(DEPO / KAPI_DOSYASI, tmp / KAPI_DOSYASI)
        yield Ayna(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
