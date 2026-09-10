"""D3 -- Olcu, parametre uzayinin KAC NOKTASINDA kosuyor?

PROTOKOL §4.6/7 ikinci cumle: "her davranissal olcu, kararin kapsadigi
parametre/on ayar uzayinin en az IKI noktasinda kosar; tek noktada kalan olcu,
o noktaya kapili bir uygulamayi goremez."

Olculen kacis (Y7-1): §3'un `grab_args` denetimi bir zamanlar TEK noktadaydi
(`Rect(10,20,64,16)`, hepsi pozitif). Bu makinenin gercek duzeninde sol monitor
`x=-2560`; kutuyu `max(0, ...)` ile kirpan bir uygulama her yakalamada yanlis
piksel verirken bes kapidan da geciyordu.
"""
from __future__ import annotations

import ast
from pathlib import Path

import numpy as np
import pytest

from src.capture.service import CaptureService, FakeBackend
from src.contracts.models import Rect

DEPO = Path(__file__).resolve().parents[4]
KAPI = DEPO / ".agents" / "tasks" / "T-005" / "headless_check.py"
KAPI_METNI = KAPI.read_text(encoding="utf-8")
SERVICE = "src/capture/service.py"

M_SOL = Rect(-2560, 0, 2560, 1440)
M_SAG = Rect(0, 0, 2560, 1440)
DUZEN = (M_SOL, M_SAG)


def test_d3_kapi_grab_kutusunu_EN_AZ_IKI_NOKTADA_olcuyor() -> None:
    """§3'un bekledigi kutu listesi en az iki AYRI nokta ve biri NEGATIF olmali."""
    agac = ast.parse(KAPI_METNI, filename=str(KAPI))
    bekle_dugumu = None
    for n in ast.walk(agac):
        if isinstance(n, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "bekle" for t in n.targets
        ):
            bekle_dugumu = n.value
            break
    assert bekle_dugumu is not None, "§3'te `bekle` kutu listesi bulunamadi"
    kutular = ast.literal_eval(bekle_dugumu)
    tekil = {tuple(sorted(k.items())) for k in kutular}
    assert len(tekil) >= 2, (
        f"§3 grab kutusunu TEK noktada olcuyor ({len(tekil)} tekil nokta) -> "
        "kirpan/kaydiran bir uygulama gorunmez (Y7-1)"
    )
    assert any(k["left"] < 0 or k["top"] < 0 for k in kutular), (
        "§3'un olcum noktalarinin hicbiri NEGATIF sanal-masaustu koordinati "
        "tasimiyor; bu makinede sol monitor x=-2560"
    )


def test_d3_kutuyu_KIRPAN_grab_kapidan_GECEMEZ(ayna) -> None:  # type: ignore[no-untyped-def]
    """M05: `max(0, rect.x)` ile kirpan grab. Yalniz IKINCI nokta yakalar."""
    ayna.geri_al()
    ayna.yaz(SERVICE, [(
        'kutu = {"left": rect.x, "top": rect.y, "width": rect.w, "height": rect.h}',
        'kutu = {"left": max(0, rect.x), "top": max(0, rect.y), '
        '"width": rect.w, "height": rect.h}',
    )])
    try:
        s = ayna.kapilar(["G3-headless"])
        assert s["G3-headless"] != 0, "kirpan grab §3'ten GECTI -> Y7-1 gerilemesi"
        assert "-2600" in s["G3-headless::cikti"], (
            "ihlal mesaji NEGATIF noktayi bildirmiyor -> ihlali uretenin ikinci "
            "olcum noktasi oldugu dogrulanamiyor"
        )
    finally:
        ayna.geri_al()


@pytest.mark.parametrize("olcek", [1.0, 1.25, 1.5, 2.0])
@pytest.mark.parametrize(
    "bolge",
    [Rect(-2560, 0, 64, 16), Rect(-2600, 0, 100, 100), Rect(0, 0, 2560, 1440),
     Rect(2500, 1400, 200, 200)],
    ids=["sol_kenar", "sol_tasan", "sag_tam", "sag_alt_tasan"],
)
def test_d3_K3_dort_olcek_x_dort_bolge(olcek: float, bolge: Rect) -> None:
    """K3 olcusunu paketin dort olceginin OTESINDE dort geometride kosar.

    Paketteki `test_k3_*` yalnizca INSIDE noktalarda olcuyordu; PARTIAL
    yolunda `dpi_scale`'in kutuyu degistirmedigi ayrica olculur.
    """
    fb = FakeBackend(DUZEN)
    servis = CaptureService(fb, lambda: 0.0)
    servis.capture_region(Rect(bolge.x, bolge.y, bolge.w, bolge.h, 7, olcek))
    (giden,) = fb.grab_rects
    fb2 = FakeBackend(DUZEN)
    servis2 = CaptureService(fb2, lambda: 0.0)
    servis2.capture_region(Rect(bolge.x, bolge.y, bolge.w, bolge.h, 7, 1.0))
    (temel,) = fb2.grab_rects
    assert (giden.x, giden.y, giden.w, giden.h) == (temel.x, temel.y, temel.w, temel.h), (
        "dpi_scale backend'e giden kutuyu degistirdi (K3)"
    )


@pytest.mark.parametrize("kanal", [3, 4], ids=["3kanal", "4kanal"])
@pytest.mark.parametrize("yazilabilir", [True, False], ids=["yazilabilir", "salt_okunur"])
def test_d3_sahiplik_kanal_x_yazilabilirlik_dort_nokta(kanal: int, yazilabilir: bool) -> None:
    """K7 sahiplik olcusu 2x2 uzayin DORT noktasinda da tutmali."""
    h, w = 20, 10
    if yazilabilir:
        kaynak = np.full((h, w, kanal), 5, dtype=np.uint8)
    else:
        kaynak = np.frombuffer(bytes(b"\x05" * (h * w * kanal)),
                               dtype=np.uint8).reshape(h, w, kanal)
        assert kaynak.flags.writeable is False
    fb = FakeBackend(DUZEN, lambda r: kaynak)
    servis = CaptureService(fb, lambda: 0.0)
    kare = servis.capture_region(Rect(0, 0, w, h))
    assert np.shares_memory(kare.image, kaynak) is False
    assert kare.image.flags.writeable is True
    assert kare.image.shape == (h, w, 3)
