"""MERCEK C/1 -- `seq` TAM matrisi (K2).

*Cagri sirasi neyi bozuyor?*

K2 uc sey soyler ve ucu de bir SIRA iddiasidir:

  1. bir ornekte basarili her yakalama `seq`'i tam **1** artirir, ilki `0`;
  2. K6'nin uc hata sinifinin **hicbiri** `seq` tuketmez;
  3. `refresh_monitors()` `seq`'i **sifirlamaz**; yeni ornek `0`'dan baslar.

Depodaki `test_k2_*` bunlari ayri ayri, her biri TEK bir hata olayiyla
olcuyor. Bir sira hatasi (ornegin "iki ardisik hatadan sonra sayac kayiyor",
"refresh'ten sonraki ilk basarida atlama var", "sinif b'nin ic dongusu
sayaca dokunuyor") tek olayli bir olcunun goremeyecegi bir seydir. Burada
alfabe `{S, a, b, c, R}` uzerinde uzunluk 1-4'un **butun** permutasyonlari
kosulur (780 dizi) ve her dizide gorulen `seq` listesi `range(basari
sayisi)`'na birebir esitlenir.
"""
from __future__ import annotations

import itertools
import random

import pytest

from src.capture.service import CaptureService
from src.contracts.errors import CaptureError
from src.contracts.models import Rect

from _ortak import (  # noqa: E402  (pytest basedir'i sys.path'e koyar)
    DISARIDA,
    GERCEK_DUZEN,
    IYI,
    M_SAG,
    M_SOL,
    TASAN,
    Yonlendirici,
    ham_liste,
    kur,
    saat,
)

ALFABE = ("S", "a", "b", "c", "R")
"""S=basari · a=K6(a) dogrulama · b=K6(b) istisna · c=K6(c) gecersiz cikti
· R=`refresh_monitors()`"""


def _olay(servis: CaptureService, y: Yonlendirici, ad: str) -> int | None:
    """Diziden bir olayi uygular; `S` icin gorulen `seq`'i dondurur."""
    if ad == "S":
        y.mod = "ok"
        return servis.capture_region(IYI).seq
    if ad == "a":
        y.mod = "ok"
        with pytest.raises(CaptureError):
            servis.capture_region(DISARIDA)
        return None
    if ad == "b":
        y.mod = "b"
        with pytest.raises(CaptureError):
            servis.capture_region(IYI)
        return None
    if ad == "c":
        y.mod = "c"
        with pytest.raises(CaptureError):
            servis.capture_region(IYI)
        return None
    if ad == "R":
        servis.refresh_monitors()
        return None
    raise AssertionError(f"bilinmeyen olay: {ad}")


def _diziyi_kos(dizi: tuple[str, ...]) -> list[int]:
    y = Yonlendirici()
    servis, _ = kur(image_factory=y)
    gorulen: list[int] = []
    for ad in dizi:
        s = _olay(servis, y, ad)
        if s is not None:
            gorulen.append(s)
    return gorulen


@pytest.mark.parametrize("uzunluk", [1, 2, 3])
def test_c1_seq_tam_permutasyon_matrisi(uzunluk: int) -> None:
    """`{S,a,b,c,R}`'nin uzunluk 1-3 BUTUN permutasyonlarinda `seq`.

    Beklenen: dizideki basari sayisi `k` ise gorulen `seq` listesi tam olarak
    `[0, 1, ..., k-1]`. Yani hata sinifleri ve `refresh` sayaci ne TUKETIR ne
    SIFIRLAR, ne de atlatir.
    """
    kirik: list[tuple[tuple[str, ...], list[int], list[int]]] = []
    for dizi in itertools.product(ALFABE, repeat=uzunluk):
        beklenen = list(range(sum(1 for a in dizi if a == "S")))
        gorulen = _diziyi_kos(dizi)
        if gorulen != beklenen:
            kirik.append((dizi, gorulen, beklenen))
    assert not kirik, f"{len(kirik)} dizide seq bozuldu: {kirik[:10]}"


def test_c1_seq_permutasyon_uzunluk_4() -> None:
    """Uzunluk 4 (625 dizi) -- iki ardisik hatadan sonra kayma yakalanir."""
    kirik: list[tuple[tuple[str, ...], list[int], list[int]]] = []
    for dizi in itertools.product(ALFABE, repeat=4):
        beklenen = list(range(sum(1 for a in dizi if a == "S")))
        gorulen = _diziyi_kos(dizi)
        if gorulen != beklenen:
            kirik.append((dizi, gorulen, beklenen))
    assert not kirik, f"{len(kirik)} dizide seq bozuldu: {kirik[:10]}"


def test_c1_uzun_rastgele_yuruyus() -> None:
    """500 olaylik deterministik rastgele yuruyus -- kume degisimleri DAHIL.

    Permutasyon matrisinin goremedigi sey: uzun bir omurde kume kucultup
    buyutmek, bos kumeye dusup geri donmek ve PARTIAL/OUTSIDE gecisleri
    `seq`'e sizar mi. Tohum sabittir (yeniden uretilebilir).
    """
    rasgele = random.Random(20260910)
    y = Yonlendirici()
    servis, fb = kur(image_factory=y)
    beklenen_seq = 0
    kumeler = [GERCEK_DUZEN, (M_SAG, M_SOL), (M_SAG,), (), GERCEK_DUZEN]

    for adim in range(500):
        secim = rasgele.randrange(8)
        if secim == 0:  # kume degistir
            fb.raw_override = ham_liste(rasgele.choice(kumeler))
            servis.refresh_monitors()
        elif secim == 1:  # bozuk sozlukle refresh -> firlar, kume korunur
            eski = servis.monitors
            fb.raw_override = [
                {"left": 0, "top": 0, "width": 1, "height": 1},
                {"left": None, "top": 0, "width": 10, "height": 10},
            ]
            with pytest.raises(CaptureError):
                servis.refresh_monitors()
            assert servis.monitors == eski, f"adim {adim}: refresh hatasi kumeyi bozdu"
            fb.raw_override = None
        elif secim == 2:  # K6 (a)
            y.mod = "ok"
            with pytest.raises(CaptureError):
                servis.capture_region(DISARIDA)
        elif secim == 3:  # K6 (b)
            y.mod = "b"
            with pytest.raises(CaptureError):
                servis.capture_region(IYI)
        elif secim == 4:  # K6 (c)
            y.mod = "c"
            with pytest.raises(CaptureError):
                servis.capture_region(IYI)
        elif secim == 5:  # capture_full -- gecerli ya da aralik disi
            y.mod = "ok"
            i = rasgele.randrange(-2, 3)
            if 0 <= i < len(servis.monitors):
                assert servis.capture_full(i).seq == beklenen_seq, f"adim {adim}"
                beklenen_seq += 1
            else:
                with pytest.raises(CaptureError):
                    servis.capture_full(i)
        else:  # capture_region -- kumeye gore basari ya da hata
            y.mod = "ok"
            bolge = rasgele.choice([IYI, TASAN])
            if not servis.monitors:
                with pytest.raises(CaptureError):
                    servis.capture_region(bolge)
            else:
                try:
                    kare = servis.capture_region(bolge)
                except CaptureError:
                    continue  # kume kuculdu, bolge OUTSIDE oldu -- seq tuketilmez
                assert kare.seq == beklenen_seq, f"adim {adim}: seq atladi"
                beklenen_seq += 1

    y.mod = "ok"
    fb.raw_override = None
    servis.refresh_monitors()
    assert servis.capture_region(IYI).seq == beklenen_seq


def test_c1_refresh_seq_i_sifirlamaz_100_kez() -> None:
    """Ardisik 100 `refresh_monitors()` sayaca DOKUNMAZ (K2)."""
    servis, _ = kur()
    for _ in range(3):
        servis.capture_region(IYI)
    for _ in range(100):
        servis.refresh_monitors()
    assert servis.capture_region(IYI).seq == 3


def test_c1_yeni_ornek_ayni_backend_ile_sifirdan_baslar() -> None:
    """`seq` ornek-yereldir: AYNI backend'le kurulan ikinci servis `0`'dan.

    K2'nin alan uyarisi tam bu: pipeline servis ornegini degistirirse
    karsilastirma tabanini sifirlamak zorundadir.
    """
    servis, fb = kur()
    for _ in range(5):
        servis.capture_region(IYI)
    ikinci = CaptureService(fb, saat())
    assert ikinci.capture_region(IYI).seq == 0
    assert servis.capture_region(IYI).seq == 5  # ilk ornek ETKILENMEZ


def test_c1_iki_ornek_seq_leri_bagimsiz_ilerler() -> None:
    """Ic ice kullanimda iki servisin sayaclari birbirine SIZMAZ."""
    a, fb = kur()
    b = CaptureService(fb, saat())
    assert [a.capture_region(IYI).seq for _ in range(3)] == [0, 1, 2]
    assert [b.capture_region(IYI).seq for _ in range(2)] == [0, 1]
    assert a.capture_region(IYI).seq == 3


def test_c1_seq_capture_full_ve_region_arasinda_TEK_sayactir() -> None:
    """`capture_full` ve `capture_region` AYNI sayaci tuketir (K2/K9)."""
    servis, _ = kur()
    gorulen = [
        servis.capture_region(IYI).seq,
        servis.capture_full(0).seq,
        servis.capture_region(IYI).seq,
        servis.capture_full(1).seq,
    ]
    assert gorulen == [0, 1, 2, 3]


def test_c1_ilk_olay_hata_ise_ilk_basari_yine_sifir() -> None:
    """Sayac -1'den baslar: once 10 hata olsa da ilk basari `seq=0` verir."""
    y = Yonlendirici()
    servis, _ = kur(image_factory=y)
    for _ in range(10):
        y.mod = "b"
        with pytest.raises(CaptureError):
            servis.capture_region(IYI)
        y.mod = "ok"
        with pytest.raises(CaptureError):
            servis.capture_region(DISARIDA)
    assert servis.capture_region(IYI).seq == 0


def test_c1_giris_kabul_kapisi_seq_tuketmez() -> None:
    """K8'in giris kapisi da bir (a) olayidir: `seq` TUKETMEZ, backend cagrilmaz.

    Bu kapi K6'nin taksonomisinde adi konmadan (a) sinifina girer; depodaki
    `test_k8_giris_*` yalnizca `CaptureError` firlatildigini olcuyor, sayaca
    ve cagri sayacina bakmiyor.
    """
    servis, fb = kur()
    assert servis.capture_region(IYI).seq == 0
    for bozuk in ("10", True, 10.9, float("nan"), float("inf")):
        with pytest.raises(CaptureError):
            servis.capture_region(Rect(bozuk, 0, 10, 10))  # type: ignore[arg-type]
    assert fb.grab_calls == 1
    assert servis.capture_region(IYI).seq == 1


def test_c1_yapim_hatasi_sonrasi_yeni_servis_sifirdan() -> None:
    """Yapimda `CaptureError` alan servis kullanilamaz; sonraki ornek `0`'dan.

    Yapim hatasi K6 taksonomisinin DISINDADIR (K5) -- burada olculen sey,
    basarisiz bir yapimin backend uzerinde `seq`'e benzer kalici bir iz
    birakmamasidir.
    """
    from src.capture.service import FakeBackend

    fb = FakeBackend(GERCEK_DUZEN)
    fb.raw_override = [
        {"left": 0, "top": 0, "width": 1, "height": 1},
        {"left": None, "top": 0, "width": 10, "height": 10},
    ]
    with pytest.raises(CaptureError):
        CaptureService(fb, saat())
    fb.raw_override = None
    saglam = CaptureService(fb, saat())
    assert saglam.capture_region(IYI).seq == 0


def test_c1_saat_istisnasi_seq_TUKETIR_taksonomi_disi() -> None:
    """[BULGU-NOT] Enjekte saat firlatirsa `seq` tuketilir ama `Frame` DOGMAZ.

    `capture_region` `self._seq += 1` satirini `Frame(...)` kurulumundan ONCE
    calistirir; `captured_at=self._clock()` ise `Frame` argumani olarak sonra
    degerlendirilir. Bu, K6'nin uc sinifinin DISINDA kalan tek `seq` sizinti
    yoludur ve paket bu yolu tanimlamaz (`clock` cagirandan gelir,
    `time.monotonic` firlatmaz). Ret gerekcesi DEGILDIR; davranis burada
    KAYDA gecirilir ki degisirse gorunsun.
    """
    durum = {"n": 0}

    def patlayan_saat() -> float:
        durum["n"] += 1
        if durum["n"] == 2:
            raise RuntimeError("saat coktu")
        return 1.0

    servis, _ = kur(clock=patlayan_saat)
    assert servis.capture_region(IYI).seq == 0
    with pytest.raises(RuntimeError):
        servis.capture_region(IYI)
    assert servis.capture_region(IYI).seq == 2, "davranis degisti -- notu guncelle"


def test_c1_ardisik_1000_yakalama_kesintisiz_artar() -> None:
    """Sicak yol: 1000 yakalamada `seq` 0..999, atlama/yineleme yok."""
    servis, fb = kur()
    diziler = [servis.capture_region(IYI).seq for _ in range(1000)]
    assert diziler == list(range(1000))
    assert fb.grab_calls == 1000
    assert fb.monitors_calls == 1
