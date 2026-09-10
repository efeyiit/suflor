"""MERCEK A -- takma ad (view/copy), paylasilan mutable durum, disaridan mutasyon.

*Docstring "kopya" diyor; gercekten kopya mi, yoksa bir gorunum mu? Disaridan
mutasyon neyi bozuyor?*

Bes saldiri noktasi (env.md, MERCEK A):

A1  `Frame.image` sahipligi DORT yonde: 3 kanal x 4 kanal, yazilabilir kaynak x
    salt-okunur kaynak. Artı: arena gorunumu ve broadcast (0-strided) kaynak.
A2  `monitors()` donusu -- donen listeyi cagiran bozarsa sonraki cagri etkilenir mi.
A3  `raw_override` canliligi -- atama ve YERINDE mutasyon sonraki cagrida gorunur mu.
A4  Servisin monitor onbellegi -- disaridan bozulma, `refresh` hatasinda eski kume.
A5  `Rect`/`Frame` gercekten dondurulmus mu; `compare=False` esitligi ne kaciriyor.

OLCU DISIPLINI (A5'te kanitlanir): `Frame.__eq__` `image`'i **gormez**. Bu
yuzden hicbir sahiplik iddiasi `==` uzerine kurulmaz; hepsi
`np.shares_memory` / `np.array_equal` / `flags` uzerinden olculur. `_TUZAK`
testleri her sahiplik iddiasinin gercekten ayirt ettigini kanitlar.
"""
from __future__ import annotations

import dataclasses
import json
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
import pytest

from src.capture.service import CaptureService, FakeBackend
from src.contracts.errors import CaptureError
from src.contracts.models import Frame, Rect

# Bu makinenin gercek duzeni (env.md): M0 birincil DEGIL ve x'i NEGATIF.
M0 = Rect(-2560, 0, 2560, 1440, monitor_index=0, dpi_scale=1.0)
M1 = Rect(0, 0, 2560, 1440, monitor_index=1, dpi_scale=1.0)
DUZEN = (M0, M1)


def _ham(rects: Sequence[Rect]) -> list[dict[str, object]]:
    """Ham `mss` listesi: `[0]` birlesim girdisi + monitorler."""
    if rects:
        x = min(r.x for r in rects)
        y = min(r.y for r in rects)
        sag = max(r.right for r in rects)
        alt = max(r.bottom for r in rects)
    else:
        x = y = sag = alt = 0
    kok: dict[str, object] = {"left": x, "top": y, "width": sag - x, "height": alt - y}
    return [kok] + [
        {"left": r.x, "top": r.y, "width": r.w, "height": r.h} for r in rects
    ]


def _kur(
    image_factory: Any = None,
    monitors: tuple[Rect, ...] = DUZEN,
) -> tuple[CaptureService, FakeBackend]:
    fb = (
        FakeBackend(monitors)
        if image_factory is None
        else FakeBackend(monitors, image_factory=image_factory)
    )
    return CaptureService(fb, clock=lambda: 1.0), fb


def _sabit(dizi: np.ndarray) -> Any:
    return lambda _rect: dizi


# ===========================================================================
# A1 -- Frame.image sahipligi DORT yonde
# ===========================================================================

# (ad, kanal, salt_okunur) -- dort yon
_YONLER = [
    ("3ch-yazilabilir", 3, False),
    ("4ch-yazilabilir", 4, False),
    ("3ch-salt-okunur", 3, True),
    ("4ch-salt-okunur", 4, True),
]


def _kaynak(kanal: int, salt_okunur: bool, h: int = 20, w: int = 10) -> np.ndarray:
    """Backend dizisi uretir.

    Salt-okunur vaka `np.frombuffer(bytes(...))` ile kurulur -- gercek `mss`
    yolunda `np.frombuffer(shot.bgra, ...)` tam olarak bunu uretir.
    """
    desen = bytes(range(1, kanal + 1)) * (h * w)
    if salt_okunur:
        return np.frombuffer(bytes(desen), dtype=np.uint8).reshape(h, w, kanal)
    return np.frombuffer(bytearray(desen), dtype=np.uint8).reshape(h, w, kanal).copy()


@pytest.mark.parametrize("ad,kanal,salt_okunur", _YONLER, ids=[y[0] for y in _YONLER])
def test_a1_sahiplik_dort_yon(ad: str, kanal: int, salt_okunur: bool) -> None:
    """Kopya KOSULSUZ: dort yonun her birinde bellek paylasimi YOK."""
    kaynak = _kaynak(kanal, salt_okunur)
    assert kaynak.flags.writeable is (not salt_okunur), "kaynak kurulumu hatali"

    servis, _ = _kur(image_factory=_sabit(kaynak))
    kare = servis.capture_region(Rect(0, 0, 10, 20))

    assert np.shares_memory(kare.image, kaynak) is False, f"{ad}: takma ad!"
    assert kare.image.flags.writeable is True, f"{ad}: Frame.image yazilamiyor"
    assert kare.image.shape == (20, 10, 3)
    assert kare.image.dtype == np.uint8


@pytest.mark.parametrize("ad,kanal,salt_okunur", _YONLER, ids=[y[0] for y in _YONLER])
def test_a1_sahiplik_gizli_referans_yok(ad: str, kanal: int, salt_okunur: bool) -> None:
    """Kopya kaynak tamponunu CANLI TUTMAZ: `base is None`, `owndata` True.

    `base` dolu bir dizi, 5120x1440'lik bir arenayi tek bir 64x16'lik kare
    yuzunden bellekte tutar; `shares_memory` bunu her zaman yakalamaz.
    """
    kaynak = _kaynak(kanal, salt_okunur)
    servis, _ = _kur(image_factory=_sabit(kaynak))
    kare = servis.capture_region(Rect(0, 0, 10, 20))

    assert kare.image.base is None, f"{ad}: Frame.image bir gorunum (base dolu)"
    assert kare.image.flags.owndata is True, f"{ad}: Frame.image belleginin sahibi degil"


@pytest.mark.parametrize("ad,kanal,salt_okunur", _YONLER, ids=[y[0] for y in _YONLER])
def test_a1_frame_i_bozmak_backend_i_bozmaz(
    ad: str, kanal: int, salt_okunur: bool
) -> None:
    """`Frame.image`'i YERINDE bozmak backend dizisini degistirmemeli."""
    kaynak = _kaynak(kanal, salt_okunur)
    once = np.array(kaynak, copy=True)
    servis, _ = _kur(image_factory=_sabit(kaynak))
    kare = servis.capture_region(Rect(0, 0, 10, 20))

    kare.image[:] = 200
    assert bool(np.array_equal(kaynak, once)), f"{ad}: Frame.image backend dizisini bozdu"


@pytest.mark.parametrize("kanal", [3, 4])
def test_a1_backend_i_bozmak_onceki_frame_i_bozmaz(kanal: int) -> None:
    """Backend dizisi sonradan degisirse ONCEKI `Frame` degismemeli."""
    kaynak = _kaynak(kanal, salt_okunur=False)
    servis, _ = _kur(image_factory=_sabit(kaynak))
    kare = servis.capture_region(Rect(0, 0, 10, 20))
    goruntu_once = np.array(kare.image, copy=True)

    kaynak[:] = 99
    assert bool(np.array_equal(kare.image, goruntu_once)), (
        f"{kanal} kanal: backend dizisi onceki Frame'i bozdu"
    )


@pytest.mark.parametrize("kanal", [3, 4])
def test_a1_salt_okunur_gorunum_altindaki_bellek_degisirse(kanal: int) -> None:
    """Salt-okunur GORUNUM, altinda CANLI ve yazilabilir bellek olabilir.

    `np.frombuffer(bytes(...))` olu bir tampondur; bu vaka daha sertidir:
    backend salt-okunur bir gorunum verir ama tamponun sahibi onu yazmaya
    devam eder (mss'in `bytearray`'ini yeniden kullanan bir DXGI yolu tam
    boyle davranirdi). Kopya alinmamissa `Frame` sessizce kayar.
    """
    arena = np.zeros((20, 10, kanal), dtype=np.uint8)
    arena[:] = 5
    gorunum = arena[:]
    gorunum.flags.writeable = False
    assert gorunum.flags.writeable is False
    assert np.shares_memory(gorunum, arena) is True, "vaka kurulumu hatali"

    servis, _ = _kur(image_factory=_sabit(gorunum))
    kare = servis.capture_region(Rect(0, 0, 10, 20))
    assert np.shares_memory(kare.image, arena) is False
    assert kare.image.flags.writeable is True

    arena[:] = 99
    assert bool(np.all(kare.image == 5)), f"{kanal} kanal: canli arena Frame'i bozdu"


@pytest.mark.parametrize("kanal", [3, 4])
def test_a1_arena_gorunumu_arenayi_paylasmaz(kanal: int) -> None:
    """Backend buyuk bir arenanin BITISIK gorunumunu verirse.

    Tuzagin en sert bicimi: `np.ascontiguousarray(v[:, :, :3])` bitisik bir
    3 kanalli gorunumde ARENANIN KENDISINI dondurur.
    """
    arena = np.full((20, 10, kanal), 7, dtype=np.uint8)
    gorunum = arena[:]
    assert gorunum.flags["C_CONTIGUOUS"] is True

    servis, _ = _kur(image_factory=_sabit(gorunum))
    kare = servis.capture_region(Rect(0, 0, 10, 20))

    assert np.shares_memory(kare.image, arena) is False
    assert np.shares_memory(kare.image, gorunum) is False


def test_a1_broadcast_sifir_adimli_kaynak() -> None:
    """0-adimli (broadcast) salt-okunur kaynak -- kopya gercek adimlar uretmeli."""
    tek = np.array([[[1, 2, 3, 255]]], dtype=np.uint8)
    yayilan = np.broadcast_to(tek, (20, 10, 4))
    assert yayilan.flags.writeable is False

    servis, _ = _kur(image_factory=_sabit(yayilan))
    kare = servis.capture_region(Rect(0, 0, 10, 20))

    assert np.shares_memory(kare.image, tek) is False
    assert kare.image.flags.writeable is True
    assert list(kare.image[0, 0]) == [1, 2, 3]
    kare.image[0, 0, 0] = 250
    assert kare.image[1, 1, 0] == 1, "0-adim korundu: tek pikseli yazmak hepsini yazdi"


def test_a1_iki_kare_birbirini_paylasmaz() -> None:
    """Ayni backend dizisinden uretilen iki `Frame` birbirini paylasmamali."""
    kaynak = np.full((20, 10, 4), 3, dtype=np.uint8)
    servis, _ = _kur(image_factory=_sabit(kaynak))
    k1 = servis.capture_region(Rect(0, 0, 10, 20))
    k2 = servis.capture_region(Rect(0, 0, 10, 20))

    assert np.shares_memory(k1.image, k2.image) is False
    k2.image[:] = 111
    assert bool(np.all(k1.image == 3)), "ikinci kare birincisini bozdu"


def test_a1_capture_full_ve_capture_region_paylasmaz() -> None:
    """`capture_full` yolu da kopyalamali (ayni backend dizisi)."""
    kaynak = np.full((1440, 2560, 4), 4, dtype=np.uint8)
    servis, _ = _kur(image_factory=_sabit(kaynak))
    kf = servis.capture_full(1)
    kr = servis.capture_region(M1)

    assert np.shares_memory(kf.image, kaynak) is False
    assert np.shares_memory(kr.image, kaynak) is False
    assert np.shares_memory(kf.image, kr.image) is False


def test_a1_partial_kirpma_yolunda_da_kopya() -> None:
    """PARTIAL (kirpma) yolu ayri bir kod dali -- sahiplik orada da olculmeli."""
    arena = np.full((100, 60, 3), 8, dtype=np.uint8)
    gorunum = arena[:]
    gorunum.flags.writeable = False
    servis, _ = _kur(image_factory=_sabit(gorunum))

    kare = servis.capture_region(Rect(-2600, 0, 100, 100))  # sol tasma -> (−2560,0,60,100)
    assert kare.rect == Rect(-2560, 0, 60, 100, monitor_index=0, dpi_scale=1.0)
    assert np.shares_memory(kare.image, arena) is False
    assert kare.image.flags.writeable is True
    arena[:] = 42
    assert bool(np.all(kare.image == 8)), "PARTIAL yolunda takma ad"


# --- TUZAK: iddialarin ayirt etme gucunun kaniti --------------------------


def _tuzak_kopyala(ham: np.ndarray) -> np.ndarray:
    """Sefin olctugu tuzak: 4 kanalda kopyalar, 3 kanalda TAKMA AD dondurur."""
    return np.ascontiguousarray(ham[:, :, :3])


def test_tuzak_ascontiguousarray_3_kanalda_takma_ad_verir() -> None:
    """Yalniz 4 kanalli bir sahiplik testi YESIL kalir -- iste kaniti."""
    dort = np.zeros((20, 10, 4), dtype=np.uint8)
    uc = np.zeros((20, 10, 3), dtype=np.uint8)

    assert np.shares_memory(_tuzak_kopyala(dort), dort) is False, "4 kanal: kopyalar"
    assert np.shares_memory(_tuzak_kopyala(uc), uc) is True, "3 kanal: TAKMA AD"


def test_tuzak_salt_okunur_kaynagi_yazilabilir_yapmaz() -> None:
    """`ascontiguousarray` salt-okunur 3 kanalli kaynagi salt-okunur birakir.

    Yani `writeable` iddiasinin BAGIMSIZ ayirt etme gucu vardir: bu vakada
    `shares_memory` de duser ama 3 kanal + salt-okunur kombinasyonunda ikisi
    ayri ayri ihlal edilir.
    """
    uc = np.frombuffer(bytes(b"\x01" * (20 * 10 * 3)), dtype=np.uint8).reshape(20, 10, 3)
    tuzak = _tuzak_kopyala(uc)
    assert tuzak.flags.writeable is False
    assert np.shares_memory(tuzak, uc) is True


def test_tuzak_arena_gorunumunde_arenayi_sizdirir() -> None:
    arena = np.zeros((20, 10, 3), dtype=np.uint8)
    tuzak = _tuzak_kopyala(arena[:])
    assert np.shares_memory(tuzak, arena) is True


# ===========================================================================
# A2 -- monitors() donusu: cagiran bozarsa sonraki cagri etkilenir mi
# ===========================================================================


def test_a2_donen_liste_her_cagrida_yeni_nesne() -> None:
    fb = FakeBackend(DUZEN)
    m1 = fb.monitors()
    m2 = fb.monitors()
    assert m1 is not m2
    assert list(m1) == list(m2)


def test_a2_donen_listeyi_bozmak_sonraki_cagriyi_etkilemez() -> None:
    """K10 bunu bir KAPI degil uygulama tercihi sayiyor; yine de olculur."""
    fb = FakeBackend(DUZEN)
    m1 = list(fb.monitors())
    assert len(m1) == 3  # [0] birlesim + iki monitor

    donen = fb.monitors()
    donen.clear()  # type: ignore[attr-defined]
    ikinci = fb.monitors()
    assert len(ikinci) == 3, "donen listeyi temizlemek sonraki cagriyi bozdu"
    assert list(ikinci) == m1


def test_a2_donen_sozlugu_bozmak_sonraki_cagriyi_etkilemez() -> None:
    fb = FakeBackend(DUZEN)
    donen = fb.monitors()
    donen[1]["left"] = 999_999  # type: ignore[index]
    ikinci = fb.monitors()
    assert ikinci[1]["left"] == -2560, "donen sozlugu bozmak sonraki cagriyi bozdu"


def test_a2_raw_override_yolunda_donen_nesne_CANLIDIR() -> None:
    """Belgelenen asimetri: override yolunda `monitors()` CANLI nesneyi verir.

    Bu bir kusur degil, K1'in mutasyon arayuzunun dogal sonucudur: tester'in
    tek kancasi `raw_override`tir ve `monitors()` onu **o anki haliyle**
    okumak zorundadir. Kaydedilir ki teslimin iki yolu ayri davrandigi
    bilinsin.
    """
    ov = _ham(DUZEN)
    fb = FakeBackend(DUZEN, raw_override=ov)
    donen = fb.monitors()
    assert donen is ov
    donen[1]["left"] = 777  # type: ignore[index]
    assert fb.monitors()[1]["left"] == 777


def test_a2_servis_kumesi_backend_listesinden_BAGIMSIZ() -> None:
    """Yapimdan sonra ham listeyi bozmak servisin onbellegini etkilememeli."""
    ov = _ham(DUZEN)
    fb = FakeBackend(DUZEN, raw_override=ov)
    servis = CaptureService(fb, clock=lambda: 1.0)
    once = servis.monitors
    assert once == DUZEN

    ov[1]["left"] = 123_456
    ov[2]["width"] = 1
    del ov[2]
    assert servis.monitors == once, "servis ham listeyi takma adliyor"
    assert servis.monitors is once


# ===========================================================================
# A3 -- raw_override canliligi
# ===========================================================================


def test_a3_public_oznitelik_ve_ayni_nesne() -> None:
    """`self._raw_override` gibi ozel bir ad kullanilirsa mutasyon KAYBOLUR."""
    ov = _ham(DUZEN)
    fb = FakeBackend(DUZEN, raw_override=ov)
    assert "raw_override" in vars(fb), "raw_override ornek uzerinde public degil"
    assert fb.raw_override is ov, "raw_override yapimda KOPYALANMIS (anlik goruntu)"
    assert not hasattr(fb, "_raw_override"), "gizli ikinci bir saklama alani var"


def test_a3_yapimdan_sonra_atama_sonraki_cagrida_gorunur() -> None:
    fb = FakeBackend(DUZEN)
    assert fb.raw_override is None
    assert len(fb.monitors()) == 3

    fb.raw_override = _ham([Rect(0, 0, 800, 600)])
    donen = fb.monitors()
    assert len(donen) == 2
    assert donen[1]["width"] == 800, "atama sonraki cagrida GORUNMEDI"


def test_a3_YERINDE_mutasyon_sonraki_cagrida_gorunur() -> None:
    """Yapimda anlik goruntu alan bir uygulama burada duser."""
    ov = _ham([Rect(0, 0, 800, 600)])
    fb = FakeBackend(DUZEN, raw_override=ov)
    assert len(fb.monitors()) == 2

    ov.append({"left": 0, "top": 600, "width": 800, "height": 600})
    assert len(fb.monitors()) == 3, "yerinde append gorunmedi (anlik goruntu alinmis)"

    ov[1]["width"] = 1234
    assert fb.monitors()[1]["width"] == 1234, "yerinde sozluk mutasyonu gorunmedi"

    del ov[2]
    assert len(fb.monitors()) == 2, "yerinde silme gorunmedi"


def test_a3_None_a_donunce_monitor_rects_yoluna_dusulur() -> None:
    """Icerikle ayirt edilir -- uzunluk tesadufen esit olabilir."""
    fb = FakeBackend(DUZEN)
    fb.raw_override = _ham([Rect(11, 22, 33, 44)])
    assert fb.monitors()[1]["left"] == 11

    fb.raw_override = None
    donen = fb.monitors()
    assert len(donen) == 3
    assert [d["left"] for d in donen[1:]] == [-2560, 0], "monitor_rects yoluna donmedi"


def test_a3_refresh_monitors_CANLI_degeri_gorur() -> None:
    servis, fb = _kur()
    assert servis.monitors == DUZEN

    fb.raw_override = _ham([Rect(0, 0, 1920, 1080)])
    assert servis.monitors == DUZEN, "refresh olmadan onbellek degisti"

    yeni = servis.refresh_monitors()
    assert yeni == (Rect(0, 0, 1920, 1080, monitor_index=0, dpi_scale=1.0),)
    assert servis.monitors == yeni


# ===========================================================================
# A4 -- servisin monitor onbellegi
# ===========================================================================


def test_a4_monitors_degismez_bir_yapi_dondurur() -> None:
    """Public yoldan onbellegi bozmak MUMKUN OLMAMALI."""
    servis, _ = _kur()
    kume = servis.monitors
    assert isinstance(kume, tuple)
    assert all(dataclasses.is_dataclass(r) for r in kume)
    with pytest.raises(TypeError):
        kume[0] = Rect(0, 0, 1, 1)  # type: ignore[index]
    with pytest.raises(dataclasses.FrozenInstanceError):
        kume[0].x = 0  # type: ignore[misc]


def test_a4_tutulan_referans_KARARLI_bir_anlik_goruntudur() -> None:
    """Basarili bir `refresh` cagiranin elindeki demeti degistirmemeli."""
    servis, fb = _kur()
    elde = servis.monitors
    fb.raw_override = _ham([Rect(0, 0, 640, 480)])
    servis.refresh_monitors()

    assert elde == DUZEN, "cagiranin elindeki demet refresh ile degisti"
    assert servis.monitors != elde


def test_a4_backend_kumesini_bozmak_onbellegi_etkilemez() -> None:
    servis, fb = _kur()
    once = servis.monitors
    fb.monitor_rects = (Rect(0, 0, 100, 100),)
    assert servis.monitors is once
    kare = servis.capture_region(Rect(0, 0, 10, 20))
    assert kare.rect.monitor_index == 1, "onbellek yerine backend okundu"


def test_a4_refresh_hatasi_eski_kumeyi_KORUR() -> None:
    """K5 durum degismezi: atama yalnizca basarili donusumden sonra."""
    servis, fb = _kur()
    eski = servis.monitors

    fb.raw_override = [
        {"left": 0, "top": 0, "width": 1, "height": 1},
        {"left": None, "top": 0, "width": 10, "height": 10},
    ]
    with pytest.raises(CaptureError):
        servis.refresh_monitors()

    assert servis.monitors is eski, "hata sonrasi kume nesnesi degisti"
    assert servis.monitors == DUZEN

    fb.raw_override = None
    kare = servis.capture_region(Rect(0, 0, 10, 20))
    assert kare.rect.monitor_index == 1, "hata sonrasi eski kumeyle calismiyor"


def test_a4_refresh_backend_istisnasinda_da_eski_kume_korunur() -> None:
    """Bozuk sozluk disinda, backend'in KENDI istisnasinda da korunmali."""

    class PatlayanBackend(FakeBackend):
        patla = False

        def monitors(self) -> Sequence[Mapping[str, object]]:
            if self.patla:
                raise RuntimeError("surucu kayboldu")
            return super().monitors()

    fb = PatlayanBackend(DUZEN)
    servis = CaptureService(fb, clock=lambda: 1.0)
    eski = servis.monitors

    fb.patla = True
    with pytest.raises(RuntimeError):
        servis.refresh_monitors()
    assert servis.monitors is eski

    fb.patla = False
    kare = servis.capture_region(Rect(0, 0, 10, 20))
    assert kare.rect.monitor_index == 1


def test_a4_yakalama_yolu_backend_monitors_u_HIC_cagirmaz() -> None:
    """Onbellek tek okuma noktasidir; sicak yolda takma ad sorusu dogmaz."""
    servis, fb = _kur()
    assert fb.monitors_calls == 1
    for _ in range(25):
        servis.capture_region(Rect(0, 0, 10, 20))
    servis.capture_full(1)
    assert fb.monitors_calls == 1
    servis.refresh_monitors()
    assert fb.monitors_calls == 2


def test_a4_ozel_alanin_disaridan_bozulmasi_BELGELENIR() -> None:
    """`_monitors` ozel bir alandir; disaridan yeniden baglanirsa yakalama onu izler.

    Bu bir kusur DEGILDIR (public yol degismez bir demet verir); olculur ve
    kaydedilir cunku mercek A'nin dordunc maddesi bunu soruyor.
    """
    servis, _ = _kur()
    servis._monitors = ()  # type: ignore[attr-defined]
    with pytest.raises(CaptureError):
        servis.capture_region(Rect(0, 0, 10, 20))

    servis._monitors = (M1,)  # type: ignore[attr-defined]
    kare = servis.capture_region(Rect(0, 0, 10, 20))
    assert kare.rect.monitor_index == 1


# ===========================================================================
# A5 -- Rect / Frame gercekten dondurulmus mu; esitlik neyi kaciriyor
# ===========================================================================

_RECT_ALANLARI = ["x", "y", "w", "h", "monitor_index", "dpi_scale"]
_FRAME_ALANLARI = ["image", "rect", "captured_at", "seq"]


@pytest.mark.parametrize("alan", _RECT_ALANLARI)
def test_a5_rect_dondurulmus(alan: str) -> None:
    r = Rect(1, 2, 3, 4)
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(r, alan, 0)


@pytest.mark.parametrize("alan", _FRAME_ALANLARI)
def test_a5_frame_dondurulmus(alan: str) -> None:
    f = Frame(image=np.zeros((2, 2, 3), np.uint8), rect=Rect(0, 0, 2, 2), captured_at=1.0, seq=0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(f, alan, 0)


def test_a5_frame_rect_alanlari_silinemez() -> None:
    r = Rect(1, 2, 3, 4)
    with pytest.raises(dataclasses.FrozenInstanceError):
        del r.x


def test_a5_dataclasses_replace_calisir() -> None:
    r = Rect(1, 2, 3, 4)
    assert dataclasses.replace(r, x=10) == Rect(10, 2, 3, 4)
    assert r == Rect(1, 2, 3, 4)


def test_a5_replace_DISINDA_bir_yol_var_slots_yok() -> None:
    """Dondurulmusluk bir SOZLESME, bir kale degil -- olculur ve kaydedilir.

    `Rect`/`Frame` `__slots__` tasimadigi icin `object.__setattr__` ve
    `__dict__` ikisi de acik kapidir. Bu `src/contracts/` sozlesmesinin
    ozelligidir (T-005'in degil, dondurulmus dosya) ve T-005'i baglamaz;
    ama "gercekten dondurulmus mu" sorusunun dogru cevabi budur.
    """
    assert not hasattr(Rect, "__slots__")
    assert not hasattr(Frame, "__slots__")

    r = Rect(1, 2, 3, 4)
    object.__setattr__(r, "x", 9)
    assert r.x == 9

    r2 = Rect(1, 2, 3, 4)
    r2.__dict__["y"] = 42
    assert r2.y == 42


def test_a5_esitlik_goruntuyu_GORMEZ() -> None:
    """`image` `compare=False`: iki tamamen farkli kare ESIT ve HASH'i ayni.

    Sonuc: bir sahiplik gerilemesi `==` ile OLCULEMEZ. A1'in butun iddialari
    bu yuzden `shares_memory`/`flags`/`array_equal` uzerine kuruludur.
    """
    ortak = dict(rect=Rect(0, 0, 2, 2), captured_at=1.0, seq=0)
    siyah = Frame(image=np.zeros((2, 2, 3), np.uint8), **ortak)  # type: ignore[arg-type]
    beyaz = Frame(image=np.full((2, 2, 3), 255, np.uint8), **ortak)  # type: ignore[arg-type]

    assert siyah == beyaz
    assert hash(siyah) == hash(beyaz)
    assert not np.array_equal(siyah.image, beyaz.image)


def test_a5_dondurulmus_frame_in_goruntusu_YERINDE_degistirilebilir() -> None:
    """`frozen=True` `image`'in ICERIGINI korumaz -- K7 zaten `writeable` istiyor.

    Yani asagi akista bir asama, baska bir asamanin elindeki `Frame`'i
    bozabilir ve `==` bunu gormez. Servis kendi kopyasini verdigi icin bu
    T-005'in disindadir; A6 (pipeline) icin kaydedilir.
    """
    servis, _ = _kur()
    kare = servis.capture_region(Rect(0, 0, 10, 20))
    ikiz = Frame(image=np.array(kare.image, copy=True), rect=kare.rect,
                 captured_at=kare.captured_at, seq=kare.seq)

    kare.image[0, 0, 0] = 200
    assert kare == ikiz, "esitlik degisikligi gordu (beklenmiyordu)"
    assert not np.array_equal(kare.image, ikiz.image)


def test_a5_frame_rect_backend_e_giden_nesnenin_KENDISI() -> None:
    """Ayni `Rect` nesnesi hem backend'e gidiyor hem `Frame.rect` oluyor.

    Dondurulmus oldugu icin zararsiz; olculur ve kaydedilir (mercek A'nin
    besinci maddesi "paylasilan mutable durum" diyor -- burada paylasim VAR,
    mutable degil).
    """
    servis, fb = _kur()
    kare = servis.capture_region(Rect(0, 0, 10, 20))
    assert fb.grab_rects[-1] is kare.rect

    servis2, fb2 = _kur()
    giris = Rect(0, 0, 10, 20)
    kare2 = servis2.capture_region(giris)
    assert kare2.rect is not giris, "cagiranin Rect'i duzlestirilmeden tasindi"


def test_a5_frame_rect_serilesir() -> None:
    """Takma adin degil ama sizintinin gorunur zarari: serilestirme."""
    servis, _ = _kur()
    kare = servis.capture_region(Rect(-2600, 0, 100, 100, monitor_index=7, dpi_scale=1.5))
    metin = json.dumps(dataclasses.asdict(kare.rect))
    assert json.loads(metin) == {
        "x": -2560, "y": 0, "w": 60, "h": 100, "monitor_index": 0, "dpi_scale": 1.5,
    }


# ===========================================================================
# A1 (ek) -- egzotik kaynaklar: kopya gercekten KOSULSUZ mu
# ===========================================================================


@pytest.mark.parametrize("ad,kanal,salt_okunur", _YONLER, ids=[y[0] for y in _YONLER])
def test_a1_may_share_memory_de_False(ad: str, kanal: int, salt_okunur: bool) -> None:
    """`may_share_memory` KORUMACI (fazla tahmin eden) olcudur.

    `shares_memory` kesin cozer; `may_share_memory` adres araliklarina bakar.
    Ikincisinin de `False` olmasi, kopyanin kaynak tamponun araligina hic
    dokunmadigini gosterir -- daha guclu bir iddiadir.
    """
    kaynak = _kaynak(kanal, salt_okunur)
    servis, _ = _kur(image_factory=_sabit(kaynak))
    kare = servis.capture_region(Rect(0, 0, 10, 20))
    assert np.may_share_memory(kare.image, kaynak) is False, f"{ad}: aralik ortusuyor"


@pytest.mark.parametrize("ad,kanal,salt_okunur", _YONLER, ids=[y[0] for y in _YONLER])
def test_a1_kopya_bitisik_ve_duz_ndarray(ad: str, kanal: int, salt_okunur: bool) -> None:
    """"Kopya" iddiasinin bicim yuzu: C-bitisik, duz `np.ndarray`, dogal adimlar.

    Adimlari bozuk ya da alt sinif olan bir "kopya" asagi akista (OCR) sessiz
    yeniden duzenlemeye yol acardi.
    """
    kaynak = _kaynak(kanal, salt_okunur)
    servis, _ = _kur(image_factory=_sabit(kaynak))
    kare = servis.capture_region(Rect(0, 0, 10, 20))

    assert type(kare.image) is np.ndarray, f"{ad}: alt sinif sizdi"
    assert kare.image.flags["C_CONTIGUOUS"] is True
    assert kare.image.strides == (30, 3, 1)


def test_a1_ndarray_alt_sinifi_kaynak() -> None:
    """`isinstance` gecen bir ALT SINIF de kopyalanmali ve duz ndarray olmali."""

    class Alt(np.ndarray):
        pass

    taban = np.full((20, 10, 3), 5, dtype=np.uint8)
    alt = taban.view(Alt)
    servis, _ = _kur(image_factory=_sabit(alt))
    kare = servis.capture_region(Rect(0, 0, 10, 20))

    assert type(kare.image) is np.ndarray
    assert np.shares_memory(kare.image, taban) is False
    assert kare.image.flags.writeable is True


def test_a1_dilimlemeyi_yutan_alt_sinif() -> None:
    """`[:, :, :3]`'u YUTAN bir alt sinif bile takma ad sizdirmemeli.

    `np.ascontiguousarray` tabanli bir uygulama burada kaynagin KENDISINI
    dondururdu.
    """

    class Yalanci(np.ndarray):
        def __getitem__(self, anahtar: object) -> np.ndarray:
            return self

    sahte = np.full((20, 10, 3), 9, dtype=np.uint8).view(Yalanci)
    servis, _ = _kur(image_factory=_sabit(sahte))
    kare = servis.capture_region(Rect(0, 0, 10, 20))

    assert np.shares_memory(kare.image, sahte) is False
    assert kare.image.shape == (20, 10, 3)
    assert np.shares_memory(_tuzak_kopyala(sahte), sahte) is True  # tuzak burada duser


def test_a1_maskeli_dizi_kaynak() -> None:
    maskeli = np.ma.MaskedArray(np.full((20, 10, 4), 6, dtype=np.uint8), mask=False)
    servis, _ = _kur(image_factory=_sabit(maskeli))
    kare = servis.capture_region(Rect(0, 0, 10, 20))

    assert type(kare.image) is np.ndarray
    assert np.shares_memory(kare.image, maskeli.data) is False


def test_a1_fortran_duzenli_kaynak() -> None:
    fc = np.asfortranarray(np.full((20, 10, 4), 3, dtype=np.uint8))
    servis, _ = _kur(image_factory=_sabit(fc))
    kare = servis.capture_region(Rect(0, 0, 10, 20))

    assert np.shares_memory(kare.image, fc) is False
    assert kare.image.flags["C_CONTIGUOUS"] is True


def test_a1_capture_full_rect_onbellekteki_nesne_DEGIL() -> None:
    """`capture_full` onbellekteki `Rect`'i tasimaz, yenisini kurar."""
    servis, _ = _kur()
    kare = servis.capture_full(1)
    assert kare.rect is not servis.monitors[1]
    assert kare.rect == servis.monitors[1]


def test_a1_modul_duzeyinde_paylasilan_mutable_durum_KAYDEDILIR() -> None:
    """`_uyum_fake`/`_uyum_mss` process genelinde tek nesnedir.

    K1/O-F bu iki satiri ZORUNLU kiliyor ve K10 `MssBackend()` yapiminin
    zararsiz oldugunu belgeliyor. Yine de mercek A'nin "paylasilan mutable
    durum" basligi altinda olculur: `_uyum_fake` sayaclari ve `grab_rects`
    listesi modul omru boyunca yasar. Kimse kullanmadigi surece bos kalir.
    """
    import src.capture.service as modul

    assert isinstance(modul._uyum_fake, FakeBackend)
    assert modul._uyum_fake.grab_rects == []
    assert modul._uyum_fake.monitors_calls == 0
    assert modul._uyum_fake.grab_calls == 0
    assert modul._uyum_mss._tutamac is None, "modul duzeyinde acik bir mss tutamaci var"


# ===========================================================================
# K1 oz-denetim -- bu dizinin testleri de gercek ekrana dokunamaz
# ===========================================================================


def test_k1_engel_bu_dizinde_de_calisiyor() -> None:
    """Kendi `conftest.py`'mizin engeli gercekten kurulu mu."""
    import mss  # noqa: PLC0415

    assert getattr(mss, "__file__", None) is None
    assert not hasattr(mss, "base")
    with pytest.raises(AssertionError):
        mss.MSS()
    with pytest.raises(AssertionError):
        mss.mss()
