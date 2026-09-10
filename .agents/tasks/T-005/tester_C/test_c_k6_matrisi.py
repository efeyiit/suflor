"""MERCEK C/2 -- K6'nin 3x3 matrisi + KARISIK diziler.

*Hangi durum hic test edilmemis?*

K6 uc sinif tanimlar ve her sinif icin uc olcu ister:
`{a, b, c} x {cagri sayisi, seq, __cause__}` -- dokuz hucre. Depoda dokuz
hucrenin karsiligi var, ama olculer TEK noktadan yazilmis: (b)'nin
`__cause__`'u hep AYNI mesajla firlatan bir uretici ile olculuyor, yani
"son istisna mi ILK istisna mi baglanmis" sorusu **olculemiyor**. Burada
uretici her denemede FARKLI mesaj verir; matris ayrica `b->c`,
`b->basari`, `b->b->b`, `b->b->basari`, `b->b->c` dizileriyle ve
`__context__` (ortuk zincirleme) ile genisletilir.

`c` sinifi TERMINALDIR: yeniden deneme yok, yani `c->...` diye bir dizi
tek bir `capture_region` icinde KURULAMAZ -- bu, matrisin "bos gorunen"
ama aslinda yapisal olarak dolu bir hucresidir; asagida `c` sonrasi
uretici degisse bile ikinci cagri OLMADIGI olculur.
"""
from __future__ import annotations

from typing import Any

import pytest

from src.capture.service import CaptureService, FakeBackend
from src.contracts.errors import CaptureError
from src.contracts.models import Rect

from _ortak import (
    DISARIDA,
    GERCEK_DUZEN,
    IYI,
    iyi_dizi,
    kur,
    saat,
    sirali_uretici,
)

DENEME_SAYISI = 3
"""K6 (b): en fazla 3 backend cagrisi."""


def _olc(uretici: Any, bolge: Rect = IYI) -> dict[str, Any]:
    """Bir `capture_region` cagrisinin BUTUN durum ciktilarini toplar."""
    fb = FakeBackend(GERCEK_DUZEN, uretici)
    servis = CaptureService(fb, saat())
    veri: dict[str, Any] = {"servis": servis, "fb": fb}
    try:
        kare = servis.capture_region(bolge)
    except CaptureError as e:
        veri.update(
            sonuc="hata",
            seq=None,
            cause=e.__cause__,
            context=e.__context__,
            mesaj=str(e),
        )
    else:
        veri.update(sonuc="kare", seq=kare.seq, cause=None, context=None, mesaj="")
    veri["grab"] = fb.grab_calls
    # hata sonrasi sayac tuketilmedi mi: bir sonraki BASARILI yakalama
    return veri


def _sonraki_seq(veri: dict[str, Any]) -> int:
    """Olcumden sonra saglam bir uretici takip ilk basarinin `seq`'ini verir."""
    fb: FakeBackend = veri["fb"]
    fb.image_factory = iyi_dizi
    servis: CaptureService = veri["servis"]
    return servis.capture_region(IYI).seq


# =========================================================================
# 3x3 matris -- {a, b, c} x {cagri sayisi, seq, __cause__}
# =========================================================================

MATRIS = {
    # sinif: (uretici, bolge, beklenen_grab, beklenen_cause_tipi)
    "a": (None, DISARIDA, 0, None),
    "b": (sirali_uretici("b"), IYI, DENEME_SAYISI, RuntimeError),
    "c": (sirali_uretici("c"), IYI, 1, None),
}


@pytest.mark.parametrize("sinif", ["a", "b", "c"])
def test_c2_matris_cagri_sayisi(sinif: str) -> None:
    uretici, bolge, beklenen, _ = MATRIS[sinif]
    veri = _olc(uretici if uretici is not None else iyi_dizi, bolge)
    assert veri["sonuc"] == "hata"
    assert veri["grab"] == beklenen


@pytest.mark.parametrize("sinif", ["a", "b", "c"])
def test_c2_matris_seq_tuketilmez(sinif: str) -> None:
    uretici, bolge, _, _ = MATRIS[sinif]
    veri = _olc(uretici if uretici is not None else iyi_dizi, bolge)
    assert veri["sonuc"] == "hata"
    assert _sonraki_seq(veri) == 0, "hata sinifi seq TUKETTI"


@pytest.mark.parametrize("sinif", ["a", "b", "c"])
def test_c2_matris_cause(sinif: str) -> None:
    uretici, bolge, _, beklenen_tip = MATRIS[sinif]
    veri = _olc(uretici if uretici is not None else iyi_dizi, bolge)
    if beklenen_tip is None:
        assert veri["cause"] is None
    else:
        assert isinstance(veri["cause"], beklenen_tip)


@pytest.mark.parametrize("sinif", ["a", "b", "c"])
def test_c2_matris_ortuk_zincir_context(sinif: str) -> None:
    """`__context__` de olculur: (a) ve (c)'de ortuk zincir de OLMAMALI.

    `__cause__ is None` iddiasi tek basina zayiftir -- `raise X` bir `except`
    govdesi icinde yapilirsa `__cause__` `None` kalir ama `__context__`
    dolar ve traceback yine iki hatayi birlikte gosterir.
    """
    uretici, bolge, _, beklenen_tip = MATRIS[sinif]
    veri = _olc(uretici if uretici is not None else iyi_dizi, bolge)
    if beklenen_tip is None:
        assert veri["context"] is None


# =========================================================================
# (b) -- deneme sayisi ve baglanan istisnanin KIMLIGI
# =========================================================================


def test_c2_b_baglanan_istisna_SONUNCUSUDUR() -> None:
    """`__cause__` ILK degil SON backend istisnasidir.

    Depodaki olcu hep ayni mesajla firlatan bir uretici kullaniyor; ilk ile
    son istisnayi ayirt edemez. Burada uretici her denemede farkli mesaj
    verir.
    """
    veri = _olc(sirali_uretici("b", "b", "b"))
    assert veri["grab"] == 3
    assert isinstance(veri["cause"], RuntimeError)
    assert str(veri["cause"]) == "istisna-3", "ILK istisna baglanmis olabilir"


def test_c2_b_b_b_sonra_CaptureError_ve_seq_tuketilmez() -> None:
    """`b->b->b` -> 3 cagri, `CaptureError`, `seq` tuketilmez."""
    veri = _olc(sirali_uretici("b", "b", "b"))
    assert (veri["sonuc"], veri["grab"]) == ("hata", 3)
    assert _sonraki_seq(veri) == 0


def test_c2_b_b_basari_uc_cagri_ve_seq_tuketilir() -> None:
    """`b->b->basari` -> 3 cagri (son deneme), `seq` TUKETILIR."""
    veri = _olc(sirali_uretici("b", "b", "ok"))
    assert (veri["sonuc"], veri["grab"], veri["seq"]) == ("kare", 3, 0)


def test_c2_b_sonra_basari_iki_cagri_ve_seq_tuketilir() -> None:
    """`b->basari` -> 2 cagri, `seq` TUKETILIR."""
    veri = _olc(sirali_uretici("b", "ok"))
    assert (veri["sonuc"], veri["grab"], veri["seq"]) == ("kare", 2, 0)


def test_c2_b_dorduncu_deneme_YOK() -> None:
    """Dorduncu denemede duzelen backend'e SIRA GELMEZ (tavan tam 3)."""
    veri = _olc(sirali_uretici("b", "b", "b", "ok"))
    assert (veri["sonuc"], veri["grab"]) == ("hata", 3)


def test_c2_b_mesaji_deneme_SAYISINI_icerir() -> None:
    """Mesajda `3` gecmeli -- ve bu `3` rect degerlerinden GELMEMELI.

    `Rect(11, 22, 33, 44)` ile olcen bir iddia totolojidir: `33` zaten `"3"`
    icerir. Burada rect'in hicbir alaninda `3` rakami yok.
    """
    servis, _ = kur(image_factory=sirali_uretici("b"))
    with pytest.raises(CaptureError) as ex:
        servis.capture_region(Rect(11, 22, 44, 55))
    mesaj = str(ex.value)
    assert "11" in mesaj and "22" in mesaj and "44" in mesaj and "55" in mesaj
    assert "3" in mesaj.replace("11", "").replace("22", "").replace("44", "").replace("55", "")


def test_c2_b_deneme_sayaci_HER_CAGRIDA_sifirlanir() -> None:
    """Tukenen bir (b) sonraki cagrinin deneme butcesini KISALTMAZ."""
    servis, fb = kur(
        image_factory=sirali_uretici("b", "b", "b", "b", "b", "b", "ok")
    )
    with pytest.raises(CaptureError):
        servis.capture_region(IYI)
    assert fb.grab_calls == 3
    with pytest.raises(CaptureError):
        servis.capture_region(IYI)
    assert fb.grab_calls == 6, "ikinci cagri da TAM 3 deneme almali"
    assert servis.capture_region(IYI).seq == 0
    assert fb.grab_calls == 7


# =========================================================================
# (c) -- TERMINAL: yeniden deneme yok
# =========================================================================


def test_c2_c_terminaldir_ikinci_deneme_yok() -> None:
    """Ikinci denemede duzelecek bir uretici bile CAGRILMAZ."""
    veri = _olc(sirali_uretici("c", "ok"))
    assert (veri["sonuc"], veri["grab"]) == ("hata", 1)


@pytest.mark.parametrize(
    "bozuk",
    ["c", "c2"],
    ids=["None_donusu", "boyut_uyusmuyor"],
)
def test_c2_c_her_bozuk_bicim_tek_cagri(bozuk: str) -> None:
    veri = _olc(sirali_uretici(bozuk, "ok"))
    assert (veri["sonuc"], veri["grab"], veri["cause"]) == ("hata", 1, None)


# =========================================================================
# KARISIK diziler
# =========================================================================


def test_c2_karisik_b_sonra_c() -> None:
    """`b->c` -> 2 cagri, `CaptureError`, `__cause__ is None` (son olay c)."""
    veri = _olc(sirali_uretici("b", "c"))
    assert (veri["sonuc"], veri["grab"]) == ("hata", 2)
    assert veri["cause"] is None
    assert _sonraki_seq(veri) == 0


def test_c2_karisik_b_sonra_c_ortuk_zincir_de_yok() -> None:
    """`b->c`: `__context__` de `None` -- (b)'nin istisnasi SIZMAZ.

    Bu, `__cause__ is None` iddiasinin BAGIMSIZ gucunu olcer: uygulama
    bicim dogrulamasini `except` govdesinin ICINDE yapsaydi `__cause__`
    yine `None` kalir, `__context__` ise `RuntimeError` olurdu.
    """
    veri = _olc(sirali_uretici("b", "c"))
    assert veri["context"] is None, (
        f"ortuk zincirleme sizdi: {veri['context']!r}"
    )


def test_c2_karisik_b_b_sonra_c() -> None:
    """`b->b->c` -> 3 cagri, `__cause__ is None` (son olay yine c)."""
    veri = _olc(sirali_uretici("b", "b", "c"))
    assert (veri["sonuc"], veri["grab"], veri["cause"]) == ("hata", 3, None)
    assert veri["context"] is None


def test_c2_karisik_c_sonra_b_KURULAMAZ() -> None:
    """`c->b` tek cagrida kurulamaz: (c) terminal oldugu icin (b)'ye SIRA GELMEZ.

    Matrisin bu hucresi bos degil, YAPISAL olarak doludur -- olculen sey
    ikinci davranisin hic uygulanmadigidir.
    """
    sayac = [0]

    def uretici(rect: Rect) -> Any:
        sayac[0] += 1
        if sayac[0] == 1:
            return None
        raise RuntimeError("bu satira ulasilmamali")

    servis, fb = kur(image_factory=uretici)
    with pytest.raises(CaptureError) as ex:
        servis.capture_region(IYI)
    assert fb.grab_calls == 1 and sayac[0] == 1
    assert ex.value.__cause__ is None


def test_c2_sinif_gecisleri_CAGRILAR_ARASI_bagimsiz() -> None:
    """a -> b -> c -> basari: her cagri kendi sinifini uretir, sayac bozulmaz."""
    y_sayac = [0]
    plan = ["b", "b", "b", "c", "ok"]

    def uretici(rect: Rect) -> Any:
        i = y_sayac[0]
        y_sayac[0] += 1
        d = plan[i] if i < len(plan) else "ok"
        if d == "b":
            raise RuntimeError("x")
        if d == "c":
            return None
        return iyi_dizi(rect)

    servis, fb = kur(image_factory=uretici)
    with pytest.raises(CaptureError):
        servis.capture_region(DISARIDA)  # (a)
    assert fb.grab_calls == 0
    with pytest.raises(CaptureError):
        servis.capture_region(IYI)  # (b) x3
    assert fb.grab_calls == 3
    with pytest.raises(CaptureError):
        servis.capture_region(IYI)  # (c)
    assert fb.grab_calls == 4
    assert servis.capture_region(IYI).seq == 0
    assert fb.grab_calls == 5


def test_c2_b_sinifinda_BaseException_yakalanmaz() -> None:
    """`except Exception` -- `KeyboardInterrupt` yeniden DENENMEZ, yayilir.

    Kullanicinin Ctrl+C'si "backend hatasi" degildir; uc kez yeniden
    denenmesi (ve `CaptureError`'a sarmalanmasi) donmus bir uygulama
    demektir. Paket bunu yazmiyor; davranis burada kayda gecer.
    """
    def uretici(rect: Rect) -> Any:
        raise KeyboardInterrupt

    servis, fb = kur(image_factory=uretici)
    with pytest.raises(KeyboardInterrupt):
        servis.capture_region(IYI)
    assert fb.grab_calls == 1
    fb.image_factory = iyi_dizi
    assert servis.capture_region(IYI).seq == 0


def test_c2_a_sinifinin_HER_kapisi_backend_i_cagirmaz() -> None:
    """(a)'nin dort ayri kapisi: giris tipi, sifir/negatif alan, bos kume, OUTSIDE."""
    servis, fb = kur()
    vakalar: list[Rect] = [
        Rect("10", 0, 10, 10),  # type: ignore[arg-type]
        Rect(0, 0, 0, 10),
        Rect(0, 0, 10, -5),
        DISARIDA,
    ]
    for r in vakalar:
        with pytest.raises(CaptureError) as ex:
            servis.capture_region(r)
        assert ex.value.__cause__ is None
        assert ex.value.__context__ is None
    assert fb.grab_calls == 0

    bos_servis, bos_fb = kur(monitors=())
    with pytest.raises(CaptureError):
        bos_servis.capture_region(IYI)
    assert bos_fb.grab_calls == 0
