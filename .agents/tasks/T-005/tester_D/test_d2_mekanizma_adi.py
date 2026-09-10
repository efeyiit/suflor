"""D2 -- Olcu MEKANIZMANIN ADINI mi kancaliyor, degismezi mi?

PROTOKOL §4.6/7. Uyum satirlari (`_uyum_fake`/`_uyum_mss`) bir MEKANIZMADIR:
mypy'ye "bu iki sinif `CaptureBackend`'e uyuyor" dedirtmenin yolu. Mekanizmayi
silen/bosaltan bir uygulama, degismezi (protokol uyumu) ihlal etmeden once
OLCUYU bosaltir.

Uc kacis yolu ayri ayri denenir:
  M09  satirlar silinir
  M10  satirlar ciplak ek aciklamaya (deger yok) doner
  M11  `FakeBackend.grab` dekoratorle sarmalanir -> mypy imzayi `Any`'ye duşurur
"""
from __future__ import annotations

from pathlib import Path

DEPO = Path(__file__).resolve().parents[4]
SERVICE = "src/capture/service.py"

SILME = [("_uyum_fake: CaptureBackend = FakeBackend(())\n"
          "_uyum_mss: CaptureBackend = MssBackend()",
          "# uyum satirlari silindi")]
CIPLAK = [("_uyum_fake: CaptureBackend = FakeBackend(())\n"
           "_uyum_mss: CaptureBackend = MssBackend()",
           "_uyum_fake: CaptureBackend\n_uyum_mss: CaptureBackend")]
DEKORATOR = [
    ("    def grab(self, rect: Rect) -> ImageArray:\n        self.grab_calls += 1",
     "    @_gecirgen\n    def grab(self, rect: Rect) -> ImageArray:\n        self.grab_calls += 1"),
    ("def _ham_sozluk(rect: Rect) -> Mapping[str, object]:",
     "def _gecirgen(f: Any) -> Any:\n    return f\n\n\n"
     "def _ham_sozluk(rect: Rect) -> Mapping[str, object]:"),
    ("from typing import TYPE_CHECKING, Protocol",
     "from typing import TYPE_CHECKING, Any, Protocol"),
]


def _kapi_dusuyor_mu(ayna, yamalar) -> tuple[int, str]:  # type: ignore[no-untyped-def]
    ayna.geri_al()
    ayna.yaz(SERVICE, yamalar)
    try:
        s = ayna.kapilar(["G3-headless"])
        return s["G3-headless"], s["G3-headless::cikti"]
    finally:
        ayna.geri_al()


def test_d2_uyum_satirlari_SILINIRSE_kapi_duser(ayna) -> None:  # type: ignore[no-untyped-def]
    rc, cikti = _kapi_dusuyor_mu(ayna, SILME)
    assert rc != 0, "uyum satirlari silindi ama §3/§4 gecti -> Y5-1 gerilemesi"
    assert "_uyum_fake" in cikti and "_uyum_mss" in cikti


def test_d2_uyum_satirlari_CIPLAK_ek_aciklamaya_donerse_kapi_duser(ayna) -> None:  # type: ignore[no-untyped-def]
    rc, cikti = _kapi_dusuyor_mu(ayna, CIPLAK)
    assert rc != 0, "ciplak ek aciklama kapiyi gecti -> Y6-1 gerilemesi (mypy hicbir sey dogrulamaz)"
    assert "ciplak ek aciklama" in cikti


def test_d2_grab_DEKORATORLENIRSE_kapi_duser(ayna) -> None:  # type: ignore[no-untyped-def]
    rc, cikti = _kapi_dusuyor_mu(ayna, DEKORATOR)
    assert rc != 0, "dekoratorlu grab kapiyi gecti -> Y7-5 gerilemesi"
    assert "DEKORATORLU" in cikti


def test_d2_uygulama_uyum_satirlarini_TASIYOR() -> None:
    """Teslim edilen kodda iki uyum satiri da CAGRI degeriyle var."""
    metin = (DEPO / SERVICE).read_text(encoding="utf-8")
    assert "_uyum_fake: CaptureBackend = FakeBackend(())" in metin
    assert "_uyum_mss: CaptureBackend = MssBackend()" in metin
