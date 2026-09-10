"""D6 -- Testler totoloji mi? Her iddia GERCEKTEN kirilabiliyor mu?

Yontem: bir iddiayi kiran ama digerlerini kirmayan girdi/uygulama kur ve o
iddianin BAGIMSIZ ayirt etme gucu olup olmadigini olc.

Ele alinan iki somut soru (env.md MERCEK D/6):
  * `writeable` iddiasinin `shares_memory` iddiasindan BAGIMSIZ gucu var mi?
  * K3'un `==` olcusu numpy sizintisini gorebiliyor mu? (goremez -- gosterilir)

Ayrica mekanik totoloji taramasi: sahipli iki test dosyasindaki her test
fonksiyonu en az bir gercek iddia tasiyor mu; sabit-dogru (`assert True`,
`assert 1`) iddia var mi.
"""
from __future__ import annotations

import ast
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from src.capture.service import CaptureService, FakeBackend
from src.contracts.models import Rect

DEPO = Path(__file__).resolve().parents[4]
SAHIPLI_TESTLER = [
    DEPO / "tests" / "unit" / "capture" / "test_service.py",
    DEPO / "tests" / "unit" / "capture" / "test_monitors.py",
]
DUZEN = (Rect(-2560, 0, 2560, 1440), Rect(0, 0, 2560, 1440))


# --------------------------------------------------------------------------
# (a) `writeable` iddiasinin BAGIMSIZ gucu
# --------------------------------------------------------------------------


def test_d6_writeable_iddiasinin_BAGIMSIZ_gucu_var() -> None:
    """Bellek paylasmayan AMA salt-okunur bir kopya kurulabiliyor mu?

    Kurulabiliyorsa `writeable` iddiasi `shares_memory` iddiasinin bir sonucu
    DEGILDIR; ikisi ayri seyi olcer. (`np.frombuffer(...tobytes())` gercekci bir
    "kopya" uygulamasidir ve salt-okunur uretir.)
    """
    kaynak = np.full((20, 10, 4), 6, dtype=np.uint8)
    sahte_kopya = np.frombuffer(
        np.ascontiguousarray(kaynak[:, :, :3]).tobytes(), dtype=np.uint8
    ).reshape(20, 10, 3)
    assert np.shares_memory(sahte_kopya, kaynak) is False, (
        "ornek gecersiz: kopya bellek paylasiyor"
    )
    assert sahte_kopya.flags.writeable is False, (
        "ornek gecersiz: kopya yazilabilir"
    )
    # -> `shares_memory` iddiasi bu uygulamayi AKLAR, `writeable` iddiasi YAKALAR.


def test_d6_teslim_edilen_kopya_her_iki_iddiayi_da_saglar() -> None:
    kaynak = np.frombuffer(bytes(b"\x04" * (20 * 10 * 4)),
                           dtype=np.uint8).reshape(20, 10, 4)
    assert kaynak.flags.writeable is False
    fb = FakeBackend(DUZEN, lambda r: kaynak)
    kare = CaptureService(fb, lambda: 0.0).capture_region(Rect(0, 0, 10, 20))
    assert np.shares_memory(kare.image, kaynak) is False
    assert kare.image.flags.writeable is True


# --------------------------------------------------------------------------
# (b) K3'un `==` olcusu numpy sizintisini GORMEZ
# --------------------------------------------------------------------------


def test_d6_esitlik_olcusu_numpy_sizintisini_GOREMEZ() -> None:
    """`Rect` esitligi, hash'i, demet karsilastirmasi ve kume uyeligi KOR."""
    a = Rect(np.int64(100), np.int64(200), np.int64(300), np.int64(150))
    b = Rect(100, 200, 300, 150)
    assert a == b
    assert hash(a) == hash(b)
    assert (a.x, a.y, a.w, a.h) == (100, 200, 300, 150)
    assert {(a.x, a.y, a.w, a.h)} == {(100, 200, 300, 150)}
    # Ayirt eden TEK kanal tip kimligi (ve serilestirme):
    assert type(a.x) is not int
    with pytest.raises(TypeError):
        json.dumps(asdict(a))


def test_d6_backend_e_giden_kutunun_TIPI_hicbir_iddiada_gecmiyor() -> None:
    """`test_k3_*` yalnizca `==` olcuyor; tip kimligi olcusu yok.

    Bu, K3 olcusunun sizintiyi goremeyecegini KAYNAKTAN dogrular. (Teslim
    edilen uygulama dogru: kutuya duz `int` gidiyor -- asagida olculuyor.)
    """
    metin = (DEPO / "tests" / "unit" / "capture" / "test_service.py").read_text(
        encoding="utf-8"
    )
    agac = ast.parse(metin)
    k3_govdeleri = [
        ast.unparse(n) for n in ast.walk(agac)
        if isinstance(n, ast.FunctionDef) and n.name.startswith("test_k3_")
    ]
    assert k3_govdeleri, "test_k3_* bulunamadi"
    assert not any("type(" in g and "grab_rects" in g for g in k3_govdeleri), (
        "beklenmedik: K3 testleri artik tip kimligi olcuyor -- bu not guncellenmeli"
    )


@pytest.mark.parametrize("tip", [np.int64, np.int32, np.uint8, np.uint16],
                         ids=["int64", "int32", "uint8", "uint16"])
def test_d6_backend_e_giden_kutu_duz_int(tip: Any) -> None:
    """K3'un `==` olcusunun goremedigi seyi TIP KIMLIGIYLE olc.

    Degerler uint8 tavaninin (255) altinda tutulur ki ayni geometri dort tipte
    de kurulabilsin.
    """
    fb = FakeBackend(DUZEN)
    CaptureService(fb, lambda: 0.0).capture_region(
        Rect(tip(100), tip(200), tip(30), tip(15))
    )
    (giden,) = fb.grab_rects
    for alan in ("x", "y", "w", "h"):
        assert type(getattr(giden, alan)) is int, (
            f"backend'e giden kutuda `{alan}` numpy skaleri "
            f"({type(getattr(giden, alan)).__name__}); `==` olcusu bunu GORMEZ"
        )


# --------------------------------------------------------------------------
# (c) mekanik totoloji taramasi
# --------------------------------------------------------------------------


def _test_fonksiyonlari(p: Path) -> list[ast.FunctionDef]:
    agac = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
    return [n for n in ast.walk(agac)
            if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]


@pytest.mark.parametrize("yol", SAHIPLI_TESTLER, ids=lambda p: p.name)
def test_d6_her_test_gercek_bir_IDDIA_tasiyor(yol: Path) -> None:
    """Iddiasiz test = yesil ama olcmeyen kapi."""
    iddiasiz: list[str] = []
    for fn in _test_fonksiyonlari(yol):
        govde = ast.unparse(fn)
        if "assert " not in govde and "pytest.raises" not in govde and "pytest.fail" not in govde:
            iddiasiz.append(fn.name)
    assert not iddiasiz, f"{yol.name}: iddiasiz testler -> {iddiasiz}"


@pytest.mark.parametrize("yol", SAHIPLI_TESTLER, ids=lambda p: p.name)
def test_d6_sabit_dogru_iddia_yok(yol: Path) -> None:
    """`assert True` / `assert 1` gibi hicbir zaman kirilmayan iddia var mi?"""
    sabitler: list[str] = []
    agac = ast.parse(yol.read_text(encoding="utf-8"), filename=str(yol))
    for n in ast.walk(agac):
        if isinstance(n, ast.Assert) and isinstance(n.test, ast.Constant):
            if n.test.value:
                sabitler.append(f"{yol.name}:{n.lineno} assert {n.test.value!r}")
    assert not sabitler, f"sabit-dogru iddialar -> {sabitler}"


@pytest.mark.parametrize("yol", SAHIPLI_TESTLER, ids=lambda p: p.name)
def test_d6_pytest_raises_bos_govdeyle_kullanilmiyor(yol: Path) -> None:
    """`with pytest.raises(...): pass` bir sey olcmez."""
    kotu: list[str] = []
    agac = ast.parse(yol.read_text(encoding="utf-8"), filename=str(yol))
    for n in ast.walk(agac):
        if not isinstance(n, ast.With):
            continue
        cagri = [i.context_expr for i in n.items
                 if isinstance(i.context_expr, ast.Call)
                 and "raises" in ast.unparse(i.context_expr.func)]
        if cagri and all(isinstance(s, ast.Pass) for s in n.body):
            kotu.append(f"{yol.name}:{n.lineno}")
    assert not kotu, f"bos `pytest.raises` govdeleri -> {kotu}"
