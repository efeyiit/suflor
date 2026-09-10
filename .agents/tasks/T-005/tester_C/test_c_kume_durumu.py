"""MERCEK C/3 -- monitor kumesi bir DURUM'dur (K5/K4/K9).

*Cagri sirasi neyi bozuyor; hangi durum hic test edilmemis?*

Servisin gorunmeyen durumu uctur: `_seq`, `_monitors` ve `MssBackend`'in
tutamaci. Bu dosya ikincisini olcer:

  * bos kume -- servis KURULUR ama her yakalama `CaptureError`, cagri 0;
  * `refresh_monitors()` hata yolu -- firlatir **ve eski kume korunur**;
  * kume degisimi -- SAYI degisimi (bolge PARTIAL/OUTSIDE olur) ve SIRA
    degisimi (kirpma geometrisi DEGISMEZ, yalniz `monitor_index` degisir);
  * `capture_full` indeks araligi -- negatif, `len`, bos kumede.

`refresh` hata yolunun kritik yani yalnizca "firlatti mi" degil, hatadan
SONRAKI yakalamanin eski kumeyle dogru calisip calismadigidir: yarim
guncellenmis bir durum (`_monitors` bozulmus ama exception atilmis) burada
gorunur.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pytest

from src.capture.monitors import union_bbox
from src.capture.service import CaptureService, FakeBackend
from src.contracts.errors import CaptureError
from src.contracts.models import Rect

from _ortak import (
    DISARIDA,
    GERCEK_DUZEN,
    IYI,
    M_SAG,
    M_SOL,
    TASAN,
    ham_liste,
    iyi_dizi,
    kur,
    saat,
)

# =========================================================================
# 3. BOS monitor kumesi
# =========================================================================


def test_c3_bos_kumede_servis_KURULUR() -> None:
    servis, fb = kur(monitors=())
    assert servis.monitors == ()
    assert fb.monitors_calls == 1
    assert union_bbox(servis.monitors) is None


@pytest.mark.parametrize(
    "bolge",
    [IYI, TASAN, DISARIDA, Rect(0, 0, 1, 1), Rect(-2560, 0, 5120, 1440)],
    ids=["inside", "partial", "outside", "1x1", "birlesim"],
)
def test_c3_bos_kumede_capture_region_hata_ve_cagri_0(bolge: Rect) -> None:
    servis, fb = kur(monitors=())
    with pytest.raises(CaptureError):
        servis.capture_region(bolge)
    assert fb.grab_calls == 0


@pytest.mark.parametrize("i", [-99, -1, 0, 1, 99])
def test_c3_bos_kumede_capture_full_hata_ve_cagri_0(i: int) -> None:
    servis, fb = kur(monitors=())
    with pytest.raises(CaptureError):
        servis.capture_full(i)
    assert fb.grab_calls == 0


def test_c3_bos_kumede_monitors_cagrisi_ARTMAZ() -> None:
    """Bos kumede bile sicak yol `backend.monitors()`'a DONMEZ (K5)."""
    servis, fb = kur(monitors=())
    for _ in range(50):
        with pytest.raises(CaptureError):
            servis.capture_region(IYI)
        with pytest.raises(CaptureError):
            servis.capture_full(0)
    assert fb.monitors_calls == 1


def test_c3_bos_kume_OUTSIDE_ten_ayirt_edilebilir() -> None:
    """Bos kume ayri bir DURUMDUR: mesaji OUTSIDE'in mesajindan FARKLI olmali.

    Bu, paketin lafzinin bir adim otesidir ve bilincli bir tester karari
    olarak kayda gecirilir (PROTOKOL §6): K4/K5 "bos kume" ile "bolge disarida"
    durumlarini AYRI ele aliyor, ama gozlemlenebilir tek fark mesajdir --
    ikisinde de `CaptureError` ve backend cagrisi 0. Bos kume denetimini
    silen bir uygulama davranissal olarak AYIRT EDILEMEZ hale gelir (olculdu:
    ayni `Rect(0,0,10,10)` icin iki durum da birebir ayni mesaji verir), yani
    o savunma satirini korumanin tek olcusu budur. Mesajin ICERIGI degil,
    yalnizca FARKLI olmasi aranir -- ifade secimi implementer'a aittir.
    """
    bolge = Rect(0, 0, 10, 10)
    bos_servis, bos_fb = kur(monitors=())
    uzak_servis, uzak_fb = kur(monitors=(Rect(10_000, 10_000, 10, 10),))

    with pytest.raises(CaptureError) as bos_ex:
        bos_servis.capture_region(bolge)
    with pytest.raises(CaptureError) as uzak_ex:
        uzak_servis.capture_region(bolge)

    assert bos_fb.grab_calls == 0 and uzak_fb.grab_calls == 0
    assert str(bos_ex.value) != str(uzak_ex.value), (
        "bos kume durumu OUTSIDE'tan ayirt edilemiyor"
    )


def test_c3_dolu_bos_dolu_gecisi_seq_i_korur() -> None:
    """Kume bosalip geri dolunca sayac ne sifirlanir ne atlar."""
    servis, fb = kur()
    assert servis.capture_region(IYI).seq == 0

    fb.raw_override = ham_liste([])
    assert servis.refresh_monitors() == ()
    with pytest.raises(CaptureError):
        servis.capture_region(IYI)

    fb.raw_override = None
    assert len(servis.refresh_monitors()) == 2
    assert servis.capture_region(IYI).seq == 1


def test_c3_bos_kumeyle_kurulup_sonradan_dolan_servis() -> None:
    """Bos kumeyle KURULAN servis, `refresh` ile calisir hale gelir."""
    fb = FakeBackend(())
    servis = CaptureService(fb, saat())
    with pytest.raises(CaptureError):
        servis.capture_region(IYI)

    fb.raw_override = ham_liste(GERCEK_DUZEN)
    servis.refresh_monitors()
    kare = servis.capture_region(IYI)
    assert kare.seq == 0 and kare.rect.monitor_index == 1


def test_c3_bos_ham_liste_ile_tamamen_bos_dizi() -> None:
    """`raw_override = []` (girdi hic yok) -> `()`; hata DEGIL."""
    servis, fb = kur()
    fb.raw_override = []
    assert servis.refresh_monitors() == ()
    with pytest.raises(CaptureError):
        servis.capture_region(IYI)


# =========================================================================
# 4. `refresh_monitors()` HATA YOLU
# =========================================================================

BOZUK_HAM: dict[str, list[dict[str, Any]]] = {
    "anahtar_eksik": [
        {"left": 0, "top": 0, "width": 1, "height": 1},
        {"top": 0, "width": 100, "height": 100},
    ],
    "deger_None": [
        {"left": 0, "top": 0, "width": 1, "height": 1},
        {"left": None, "top": 0, "width": 100, "height": 100},
    ],
    "deger_str": [
        {"left": 0, "top": 0, "width": 1, "height": 1},
        {"left": 0, "top": 0, "width": "2560", "height": 100},
    ],
    "deger_bool": [
        {"left": 0, "top": 0, "width": 1, "height": 1},
        {"left": 0, "top": 0, "width": 100, "height": True},
    ],
    "deger_float": [
        {"left": 0, "top": 0, "width": 1, "height": 1},
        {"left": 0, "top": 1.5, "width": 100, "height": 100},
    ],
    "deger_np_bool": [
        {"left": 0, "top": 0, "width": 1, "height": 1},
        {"left": np.bool_(True), "top": 0, "width": 100, "height": 100},
    ],
    "ikinci_monitor_bozuk": [
        {"left": 0, "top": 0, "width": 1, "height": 1},
        {"left": 0, "top": 0, "width": 100, "height": 100},
        {"left": 0, "top": 0, "width": None, "height": 100},
    ],
}


@pytest.mark.parametrize("ad", sorted(BOZUK_HAM))
def test_c4_refresh_hatasi_eski_kumeyi_KORUR(ad: str) -> None:
    """Firlatir **ve** eski kume degismeden kalir; sonraki yakalama eskiyle calisir.

    "Yarim guncelleme" (once ata, sonra dogrula) tam burada gorunurdu:
    `_monitors` bozuk kumeye kayar, `CaptureError` yine firlar ve depodaki
    tek vakali olcu bunu goremeyebilirdi.
    """
    servis, fb = kur()
    eski = servis.monitors
    assert servis.capture_region(IYI).seq == 0

    fb.raw_override = BOZUK_HAM[ad]
    with pytest.raises(CaptureError):
        servis.refresh_monitors()

    assert servis.monitors == eski
    assert fb.monitors_calls == 2, "hatali refresh backend'i cagirmis olmali"

    # eski kume GERCEKTEN calisiyor: PARTIAL kirpmasi eski birlesime gore
    fb.raw_override = None
    kare = servis.capture_region(TASAN)
    assert (kare.rect.x, kare.rect.y, kare.rect.w, kare.rect.h) == (-2560, 0, 60, 100)
    assert kare.rect.monitor_index == 0
    assert kare.seq == 1, "basarisiz refresh seq TUKETTI"


@pytest.mark.parametrize("ad", sorted(BOZUK_HAM))
def test_c4_ardisik_bes_hatali_refresh_kumeyi_bozmaz(ad: str) -> None:
    servis, fb = kur()
    eski = servis.monitors
    fb.raw_override = BOZUK_HAM[ad]
    for _ in range(5):
        with pytest.raises(CaptureError):
            servis.refresh_monitors()
        assert servis.monitors == eski


def test_c4_refresh_hatasi_capture_full_u_de_bozmaz() -> None:
    servis, fb = kur()
    fb.raw_override = BOZUK_HAM["deger_None"]
    with pytest.raises(CaptureError):
        servis.refresh_monitors()
    fb.raw_override = None
    assert servis.capture_full(0).rect.x == -2560
    assert servis.capture_full(1).rect.x == 0


def test_c4_backend_monitors_istisnasi_SARMALANMAZ_ve_kume_korunur() -> None:
    """Backend'in kendi hatasi (surucu/DC) `CaptureError`'a cevrilmez (K5).

    K6 taksonomisi yalnizca YAKALAMA cagrilarini kapsar; monitor okuma
    hatasi onun disindadir ve oldugu gibi yayilir.
    """

    class Patlayan(FakeBackend):
        def __init__(self, monitors: tuple[Rect, ...]) -> None:
            super().__init__(monitors)
            self.patla = False

        def monitors(self) -> Any:
            if self.patla:
                self.monitors_calls += 1
                raise OSError("surucu coktu")
            return super().monitors()

    fb = Patlayan(GERCEK_DUZEN)
    servis = CaptureService(fb, saat())
    eski = servis.monitors
    assert servis.capture_region(IYI).seq == 0

    fb.patla = True
    with pytest.raises(OSError):
        servis.refresh_monitors()
    assert servis.monitors == eski

    fb.patla = False
    assert servis.capture_region(IYI).seq == 1


def test_c4_yapimda_backend_istisnasi_da_SARMALANMAZ() -> None:
    class HemenPatlayan(FakeBackend):
        def monitors(self) -> Any:
            raise OSError("yapimda surucu coktu")

    with pytest.raises(OSError):
        CaptureService(HemenPatlayan(GERCEK_DUZEN), saat())


def test_c4_basarili_refresh_yeni_kumeyi_DONDURUR_ve_atar() -> None:
    servis, fb = kur()
    fb.raw_override = ham_liste([M_SAG])
    yeni = servis.refresh_monitors()
    assert yeni == servis.monitors
    assert yeni == (Rect(0, 0, 2560, 1440, monitor_index=0, dpi_scale=1.0),)


# =========================================================================
# 5. KUME DEGISIMI -- sira ve sayi
# =========================================================================


@pytest.mark.parametrize(
    ("ad", "bolge", "geo", "mi_once", "mi_sonra"),
    [
        ("partial_sol", TASAN, (-2560, 0, 60, 100), 0, 1),
        ("partial_ust", Rect(100, -50, 100, 100), (100, 0, 100, 50), 1, 0),
        ("inside_sag", Rect(100, 100, 50, 50), (100, 100, 50, 50), 1, 0),
        ("inside_sol", Rect(-2000, 100, 50, 50), (-2000, 100, 50, 50), 0, 1),
        ("inside_yayilan", Rect(-50, 0, 100, 100), (-50, 0, 100, 100), -1, -1),
    ],
)
def test_c5_sira_degisimi_GEOMETRIYI_degistirmez(
    ad: str,
    bolge: Rect,
    geo: tuple[int, int, int, int],
    mi_once: int,
    mi_sonra: int,
) -> None:
    """K5 sira degismezi: kirpma birlesime goredir, siraya DUYARSIZ.

    Degisen tek sey `Frame.rect.monitor_index`'tir. Backend'e giden kutu da
    birebir aynidir -- yani sira degisimi tek bir pikseli bile kaydirmaz.
    """
    servis, fb = kur()
    once = servis.capture_region(bolge)
    assert (once.rect.x, once.rect.y, once.rect.w, once.rect.h) == geo
    assert once.rect.monitor_index == mi_once

    fb.raw_override = ham_liste([M_SAG, M_SOL])  # SIRA ters
    servis.refresh_monitors()
    sonra = servis.capture_region(bolge)

    assert (sonra.rect.x, sonra.rect.y, sonra.rect.w, sonra.rect.h) == geo
    assert sonra.rect.monitor_index == mi_sonra
    g1, g2 = fb.grab_rects
    assert (g1.x, g1.y, g1.w, g1.h) == (g2.x, g2.y, g2.w, g2.h)
    assert sonra.seq == 1


def test_c5_sira_degisimi_dpi_scale_i_TASIR() -> None:
    """Sira degisimi cagiranin `dpi_scale` beyanini etkilemez (K8)."""
    servis, fb = kur()
    once = servis.capture_region(Rect(-2600, 0, 100, 100, dpi_scale=1.5))
    fb.raw_override = ham_liste([M_SAG, M_SOL])
    servis.refresh_monitors()
    sonra = servis.capture_region(Rect(-2600, 0, 100, 100, dpi_scale=1.5))
    assert once.rect.dpi_scale == sonra.rect.dpi_scale == 1.5


def test_c5_sira_degisimi_capture_full_un_HEDEFINI_degistirir() -> None:
    """[KAYIT] Monitor kimligi KONUMSALDIR: `capture_full(0)` baska ekrana kayar.

    K5'in `known_gaps`'e yazdigi kabul edilen eksiklik budur ve `refresh`
    sonrasi gozlemlenebilir: ayni indeks, farkli fiziksel monitor. Ret
    gerekcesi degil; belgelenmis eksikligin OLCUSUDUR.
    """
    servis, fb = kur()
    once = servis.capture_full(0)
    fb.raw_override = ham_liste([M_SAG, M_SOL])
    servis.refresh_monitors()
    sonra = servis.capture_full(0)
    assert once.rect.x == -2560
    assert sonra.rect.x == 0, "kimlik konumsal degil -- known_gaps guncellenmeli"


@pytest.mark.parametrize(
    ("ad", "bolge", "beklenen"),
    [
        ("sol_monitor_kaybolur", Rect(-2000, 0, 100, 100), "hata"),
        ("yayilan_bolge_kirpilir", Rect(-50, 0, 100, 100), (0, 0, 50, 100)),
        ("sag_bolge_etkilenmez", Rect(100, 100, 50, 50), (100, 100, 50, 50)),
    ],
)
def test_c5_sayi_degisimi_2_den_1_e(
    ad: str, bolge: Rect, beklenen: Any
) -> None:
    """Monitor kaybi: eski bolge OUTSIDE olur ya da PARTIAL'e duser."""
    servis, fb = kur()
    servis.capture_region(bolge)  # eski kumede gecerli
    fb.raw_override = ham_liste([M_SAG])
    servis.refresh_monitors()

    if beklenen == "hata":
        with pytest.raises(CaptureError):
            servis.capture_region(bolge)
        assert fb.grab_calls == 1  # ikinci cagri backend'e ULASMADI
    else:
        kare = servis.capture_region(bolge)
        assert (kare.rect.x, kare.rect.y, kare.rect.w, kare.rect.h) == beklenen
        assert kare.seq == 1


def test_c5_sayi_degisimi_1_den_3_e_indeksler_yeniden_numaralanir() -> None:
    A = Rect(0, 0, 100, 100)
    B = Rect(100, 0, 100, 100)
    C = Rect(200, 0, 100, 100)
    servis, fb = kur(monitors=(A,))
    assert servis.capture_region(Rect(10, 10, 10, 10)).rect.monitor_index == 0
    fb.raw_override = ham_liste([A, B, C])
    assert len(servis.refresh_monitors()) == 3
    assert servis.capture_region(Rect(210, 10, 10, 10)).rect.monitor_index == 2
    assert servis.capture_full(2).rect.x == 200


def test_c5_kume_degisimi_capture_full_araligini_daraltir() -> None:
    """`capture_full(1)` gecerliyken kume 1'e duserse ARALIK DISI olur."""
    servis, fb = kur()
    assert servis.capture_full(1).rect.x == 0
    fb.raw_override = ham_liste([M_SAG])
    servis.refresh_monitors()
    with pytest.raises(CaptureError):
        servis.capture_full(1)
    assert servis.capture_full(0).rect.x == 0


def test_c5_kume_degisimi_seq_i_tuketmez_ve_sifirlamaz() -> None:
    servis, fb = kur()
    servis.capture_region(IYI)
    servis.capture_region(IYI)
    for kume in ([M_SAG], [M_SAG, M_SOL], [], list(GERCEK_DUZEN)):
        fb.raw_override = ham_liste(kume)
        servis.refresh_monitors()
    assert servis.capture_region(IYI).seq == 2


# =========================================================================
# 7. `capture_full` INDEKS ARALIGI
# =========================================================================


@pytest.mark.parametrize("i", [-100, -3, -2, -1, 2, 3, 99, 1000])
def test_c7_capture_full_aralik_disi_cagri_0_ve_seq_korunur(i: int) -> None:
    """Negatif indeksleme BILEREK devre disi: `-1` son monitoru VERMEZ."""
    servis, fb = kur()
    assert servis.capture_region(IYI).seq == 0
    with pytest.raises(CaptureError) as ex:
        servis.capture_full(i)
    assert fb.grab_calls == 1  # yalniz ilk capture_region
    assert ex.value.__cause__ is None
    assert str(i) in str(ex.value) and "2" in str(ex.value)
    assert servis.capture_region(IYI).seq == 1


@pytest.mark.parametrize("n", [1, 2, 3, 5])
def test_c7_capture_full_sinirlari_n_monitorde(n: int) -> None:
    """`0..n-1` gecerli, `-1` ve `n` gecersiz -- her kume boyutunda."""
    kume = tuple(Rect(i * 100, 0, 100, 100) for i in range(n))
    servis, fb = kur(monitors=kume)
    for i in range(n):
        kare = servis.capture_full(i)
        assert kare.rect.x == i * 100
        assert kare.rect.monitor_index == i
    for kotu in (-1, n, n + 1):
        with pytest.raises(CaptureError):
            servis.capture_full(kotu)
    assert fb.grab_calls == n


def test_c7_capture_full_bool_indeksi() -> None:
    """[KAYIT] `bool` `int` alt sinifidir: `capture_full(True)` == `(1)`.

    K5/K8 girislerinde `bool` acikca reddediliyor; `capture_full`'un indeksi
    icin paket bir kural yazmiyor ve `0 <= i < n` karsilastirmasi `True`'yu
    `1` olarak kabul ediyor. Zararsiz (indeks disaridan gelen bir kullanici
    degeri degil, `enumerate` cikti alanidir) ama kayda gecer.
    """
    servis, _ = kur()
    assert servis.capture_full(True).rect.x == servis.monitors[1].x
    assert servis.capture_full(False).rect.x == servis.monitors[0].x


def test_c7_capture_full_sifir_alanli_monitorde_backend_i_cagirmaz() -> None:
    """Ham sozluk `width=0` verirse monitor kumeye GIRER ama yakalanamaz."""
    fb = FakeBackend((Rect(0, 0, 100, 100),))
    fb.raw_override = [
        {"left": 0, "top": 0, "width": 100, "height": 100},
        {"left": 0, "top": 0, "width": 0, "height": 1440},
    ]
    servis = CaptureService(fb, saat())
    assert servis.monitors == (Rect(0, 0, 0, 1440, monitor_index=0, dpi_scale=1.0),)
    with pytest.raises(CaptureError):
        servis.capture_full(0)
    assert fb.grab_calls == 0


def test_c7_capture_full_kume_okumaz_100_cagri() -> None:
    servis, fb = kur()
    for _ in range(100):
        servis.capture_full(0)
        servis.capture_full(1)
    assert fb.monitors_calls == 1
    assert fb.grab_calls == 200
