"""D7 -- Kapsam yalani: fazladan `# pragma: no cover` esigi kirmiyor.

K13: `# pragma: no cover` yalnizca `MssBackend.monitors/grab/close` govdelerinde
serbest; baska her yer YASAK. Bu **makinenin gormedigi** bir kuraldir:
`--cov-fail-under=95` fazladan pragmayi goremez, cunku pragma kapsanmayan
satiri "eksik" degil "yok" sayar -- payda kucululur, oran DUSER ama esik tutar.

Burada iki sey olculur:
  (a) mekanizma: fazladan pragma esigi gercekten kirmiyor mu (ayna agacinda);
  (b) teslim: `src/capture` altinda K13'un izin verdiginden BASKA pragma var mi.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

DEPO = Path(__file__).resolve().parents[4]
SERVICE_YOL = DEPO / "src" / "capture" / "service.py"
MONITORS_YOL = DEPO / "src" / "capture" / "monitors.py"
SERVICE = "src/capture/service.py"

IZINLI = {"monitors", "grab", "close"}       # yalnizca MssBackend govdelerinde
FAZLADAN = [
    ("    def capture_full(self, monitor_index: int) -> Frame:",
     "    def capture_full(self, monitor_index: int) -> Frame:  # pragma: no cover"),
    ("    def _monitor_indeksi(self, hedef: Rect) -> int:",
     "    def _monitor_indeksi(self, hedef: Rect) -> int:  # pragma: no cover"),
    ("    def _backend_dan_al(self, hedef: Rect) -> ImageArray:",
     "    def _backend_dan_al(self, hedef: Rect) -> ImageArray:  # pragma: no cover"),
    ("    def refresh_monitors(self) -> tuple[Rect, ...]:",
     "    def refresh_monitors(self) -> tuple[Rect, ...]:  # pragma: no cover"),
]


def test_d7_fazladan_pragma_ESIGI_KIRMIYOR(ayna) -> None:  # type: ignore[no-untyped-def]
    """Mekanizma dogrulamasi: dort fazladan pragma -> kapsam komutu yine exit 0."""
    ayna.geri_al()
    ayna.yaz(SERVICE, FAZLADAN)
    try:
        s = ayna.kapilar(["G4-kapsam"])
        cikti = s["G4-kapsam::cikti"]
        assert s["G4-kapsam"] == 0, (
            "beklenmedik: fazladan pragma esigi kirdi -- bu not guncellenmeli"
        )
        m = re.search(r"Total coverage: ([\d.]+)%", cikti)
        assert m, cikti[-500:]
        oran = float(m.group(1))
        assert oran >= 95.0
        # Payda kuculuyor: ifade sayisi DUSUYOR.
        sm = re.search(r"service\.py\s+(\d+)\s+", cikti)
        assert sm, cikti[-500:]
        assert int(sm.group(1)) < 137, (
            f"pragma ifade sayisini dusurmedi ({sm.group(1)}); mekanizma gecersiz"
        )
    finally:
        ayna.geri_al()


@pytest.mark.parametrize("yol", [SERVICE_YOL, MONITORS_YOL], ids=lambda p: p.name)
def test_d7_teslimde_IZINSIZ_pragma_yok(yol: Path) -> None:
    """K13'un elle denetlenen kurali: baska `no cover` yasak."""
    metin = yol.read_text(encoding="utf-8")
    agac = ast.parse(metin, filename=str(yol))
    satirlar = metin.splitlines()
    pragma_satirlari = {i + 1 for i, s in enumerate(satirlar) if "pragma: no cover" in s}

    izinli_satirlar: set[int] = set()
    for n in ast.walk(agac):
        if isinstance(n, ast.ClassDef) and n.name == "MssBackend":
            for f in n.body:
                if isinstance(f, ast.FunctionDef) and f.name in IZINLI:
                    izinli_satirlar.add(f.lineno)
    izinsiz = sorted(pragma_satirlari - izinli_satirlar)
    assert not izinsiz, (
        f"{yol.name}: K13 disi `# pragma: no cover` satirlari -> {izinsiz} "
        f"(izinli: yalnizca MssBackend.monitors/grab/close)"
    )


def test_d7_izinli_pragmalarin_yaninda_gerekce_yorumu_var() -> None:
    """K13: her isaretin yaninda `# K1: gercek ekran, ...` yorumu olmali."""
    metin = SERVICE_YOL.read_text(encoding="utf-8")
    satirlar = [s for s in metin.splitlines() if "pragma: no cover" in s]
    assert len(satirlar) == 3, f"beklenen 3 pragma, bulunan {len(satirlar)}"
    for s in satirlar:
        assert "K1" in s and "headless_check" in s, f"gerekce yorumu eksik: {s.strip()}"


def test_d7_gizli_kapsam_yapilandirmasi_yok() -> None:
    """`.coveragerc`/`setup.cfg`/`pyproject.toml` ile `exclude_lines` eklenmemis."""
    for ad in (".coveragerc", "setup.cfg", "tox.ini", "pyproject.toml"):
        p = DEPO / ad
        if p.exists():
            metin = p.read_text(encoding="utf-8")
            assert "exclude_lines" not in metin, (
                f"{ad} kapsam disi birakma kurali tasiyor -> esik yaniltilabilir"
            )


def test_d7_MssBackend_disi_govdeler_gercekten_KAPSANIYOR() -> None:
    """`__init__`/`__enter__`/`__exit__` pragma ALMAZ -- kapsanmalari sart (K13)."""
    metin = SERVICE_YOL.read_text(encoding="utf-8")
    agac = ast.parse(metin, filename=str(SERVICE_YOL))
    satirlar = metin.splitlines()
    for n in ast.walk(agac):
        if isinstance(n, ast.ClassDef) and n.name == "MssBackend":
            for f in n.body:
                if isinstance(f, ast.FunctionDef) and f.name in {"__init__", "__enter__", "__exit__"}:
                    assert "pragma: no cover" not in satirlar[f.lineno - 1], (
                        f"MssBackend.{f.name} pragma almis -- K13 bunu yasakliyor"
                    )
