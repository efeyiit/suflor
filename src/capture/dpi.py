"""Suflor -- DPI ve monitor koordinat donusumleri (saf matematik).

Tasarim dokumani 5.1 (`CaptureService`, DPI farkindaligi), 5.6 ("bolge
gecersiz" hata satiri) ve 8.3 A2 kabul kriterlerinin (%100/%150/%200
donusum testleri) karsiligi. Bu modul **tamamen saf fonksiyonlardan**
olusur: sinif yok, durum yok, I/O yok, Windows API cagrisi yok. Monitor
bilgisi her zaman parametre olarak gelir -- boylece headless ve
deterministik test edilebilir.

`Rect` (src/contracts/models.py) dondurulmus sozlesmedir, burada yalnizca
kullanilir. Sozlesmenin kendi dokumantasyonu: "Koordinatlar fiziksel
piksel cinsindendir; `dpi_scale` mantiksal koordinata cevirmek isteyen
tarafin isidir." Bu modul o donusumu ve komsu iki tuzagi (negatif sanal
masaustu koordinatlari, birden fazla monitore yayilan bolgeler) saglar.

Monitor temsili
----------------
Ayri bir "Monitor" sinifi yok -- gorev paketinin de belirttigi gibi
`Rect` zaten yeterli: bir monitorun sanal masaustundeki siniri
(x, y, w, h) ve o monitorun `dpi_scale`'i. `Monitor` asagida yalnizca
okunabilirlik icin bir `TypeAlias`'tir; calisma zamaninda `Rect`'ten
farksizdir.

Yuvarlama sozlesmesi -- bilincli secim
----------------------------------------
Python'un yerlesik `round()` fonksiyonu "yariya en yakin CIFT sayi"
kuralini kullanir (`round(0.5) == 0`, `round(2.5) == 2`) -- ekran/grafik
baglaminda sasirtici ve asimetriktir. Bu modul bunun yerine **sifirdan
uzaga yuvarlama** (round-half-away-from-zero) kullanir: `2.5 -> 3`,
`-2.5 -> -3`. Bu kural negatif sanal masaustu koordinatlarinda simetrik
davranir ve en sezgisel secimdir (bkz. `_round_half_away_from_zero`).

Kabul edilen deger alani -- dpi_scale >= 1.0 ZORUNLUDUR (tur 2 duzeltmesi)
------------------------------------------------------------------------
`logical_to_physical` ve `physical_to_logical`, `dpi_scale < 1.0` olan
bir `Rect`'i **`ValueError` ile reddeder** (yalnizca `dpi_scale <= 0`
degil -- bu, tur 1'de kor tester'in buldugu ve sefin bagimsiz dogruladigi
bir bosluktu: `0 < dpi_scale < 1` sessizce kabul ediliyordu ama round-trip
garantisi o aralikta tutmuyordu, ornegin `Rect(x=3,y=3,w=3,h=3,
dpi_scale=0.5)` icin `3 -> 2 -> 4`). Gerekce iki katmanli:

  1. Gercekcilik: Windows'ta DPI olcegi hicbir zaman %100'un altina
     inmez (%100, %125, %150, %175, %200, ...) -- `dpi_scale < 1.0`
     gecerli bir isletim sistemi metadata'si degildir, sessizce kabul
     edilmemelidir.
  2. Matematiksel zorunluluk: asagidaki round-trip ispati yalnizca
     `s >= 1` icin gecerlidir. `s < 1` icin yuvarlama hatasi (mutlak
     degerde en fazla 0.5) fizikselden mantiksala donerken `s`'e
     BOLUNMEK yerine ondan daha da BUYUYEREK etkir, bu yuzden ispatin
     "hata < 0.5" adimi cokuyor ve round-trip sistematik olarak
     bozuluyor.

Bu iki kisit -- validasyonun reddettigi alan ile ispatin varsaydigi alan
-- **birebir ortusur**. Sonuc: asagidaki round-trip iddiasi artik
modulun FIILEN kabul ettigi HER girdi icin, istisnasiz dogrudur; iddia
ile davranis arasinda bosluk kalmadi.

Round-trip kararliligi -- ne garanti edilir, ne edilmez
---------------------------------------------------------
`logical_to_physical` ve `physical_to_logical` birbirinin tersi GIBI
gorunur ama matematiksel olarak SIMETRIK DEGILDIR:

  * `physical_to_logical(logical_to_physical(r)) == r`  -- modulun kabul
    ettigi HER `r` icin (yani `r.dpi_scale >= 1.0` -- daha kucugu
    `ValueError` ile reddedilir) HER ZAMAN dogru.
  * `logical_to_physical(physical_to_logical(r)) == r`  -- GENEL OLARAK
    yanlis (guvercin yuvasi ilkesi: dpi_scale > 1 icin fiziksel piksel
    uzayi mantiksaldan daha yogundur, coklu fiziksel deger ayni mantiksal
    degere yuvarlanabilir).

  Ispat taslagi (ilk yon icin): L tam sayi, s >= 1 olcek olsun -- modul
  `s < 1`'i zaten reddettigi icin bu on kosul kabul edilen HER girdide
  otomatik saglanir.
  P = round_away(L * s) ise |P - L*s| <= 0.5 (yuvarlamanin tanimi geregi).
  L' = round_away(P / s) hesaplanirken hata |P/s - L| <= 0.5/s. s > 1
  icin bu kesinlikle 0.5'ten kucuktur, yani P/s degeri L'ye, L'nin HER
  komsu tam sayisindan daha yakindir -> L' = L garantidir. s == 1 icin
  zaten hic yuvarlama gerekmez (esitlik tam, iki yon de kararlidir).
  Ters yonde (fizikselden baslayarak)ayni analiz gecerli degildir cunku
  baslangic degeri bir L'den turetilmis olmak ZORUNDA degildir.

  Sonuc: bu modulu kullanan kod, bir bolgeyi MANTIKSAL olarak tanimlayip
  fizikselde yakaladiginda (v1'in tipik kullanimi -- kullanici bir bolge
  secer, capture o bolgeyi fiziksel piksellerde okur) round-trip HER ZAMAN
  kararlidir -- KOSULSUZ, cunku artik validasyonun kabul alani ile
  ispatin varsaydigi alan (`s >= 1`) birebir ortusuyor. Fizikselden
  mantiksala gidip geri donmek (ornegin capture edilen bir kareyi
  mantiksallastirip tekrar fizikselletirmek) kararlilik GARANTISI
  TASIMAZ; bu durumu test dosyasi ayri iki testle belgeler.

Negatif genislik/yukseklik -- guvenli ele alinir, cokme yok
---------------------------------------------------------------
`w < 0` veya `h < 0` tasiyan bir `Rect` hicbir fonksiyonda istisnaya yol
acmaz. `intersect` ve `clamp_to_monitor` bunu tutarli bicimde "kesisim
yok" (`None`) sayar, `classify_region` ise "alani yok" (`OUTSIDE`) sayar
-- negatif alan, sifir alan gibi davranir. `logical_to_physical` ve
`physical_to_logical` ise negatif `w`/`h`'yi oldugu gibi olcekler (isaret
korunur); bu degerin cagiran baglamda anlamli olup olmadigini
degerlendirmek bu modulun degil, cagiran kodun sorumlulugudur.

x/y/w/h bagimsiz yuvarlanir
-----------------------------
`right`/`bottom` kenarlari `x+w`/`y+h` olarak TUReTiLiR (Rect sozlesmesi).
Bu modul x, y, w, h degerlerini birbirinden BAGIMSIZ olcekleyip yuvarlar;
sonucta `scaled.right`, `round_away(original.right * scale)` degerine tam
esit OLMAYABILIR (en fazla 1 fiziksel piksel fark). Bu, DPI-olcekli
arayuzlerin standart davranisidir (Windows'un kendisi dahil) ve yukaridaki
round-trip garantisini ETKILEMEZ -- round-trip yalnizca (x, y, w, h)
dortlusunun kendisi icin taahhut edilir.
"""
from __future__ import annotations

import math
from collections.abc import Sequence
from enum import StrEnum
from typing import TypeAlias

from src.contracts.models import Rect

__all__ = [
    "Monitor",
    "RegionValidity",
    "logical_to_physical",
    "physical_to_logical",
    "to_monitor_relative",
    "to_virtual_desktop",
    "intersect",
    "clamp_to_monitor",
    "classify_region",
]


Monitor: TypeAlias = Rect
"""Bir monitorun sanal masaustundeki siniri + dpi_scale'i.

Ayri bir tip yok -- `Rect` zaten (x, y, w, h, monitor_index, dpi_scale)
alanlariyla bir monitoru temsil etmek icin yeterli (bkz. modul
dokumantasyonu). Bu sadece imza okunabilirligi icin bir takma addir.
"""


class RegionValidity(StrEnum):
    """`classify_region` sonucu -- tasarim dokumani 5.6 "bolge gecersiz"
    durumunun temel tasi. Bu enum yalnizca SINIFLANDIRIR; hangi durumda
    izlemenin duraklatilacagina UI/pipeline katmani karar verir (bu
    fonksiyonun sorumlulugu degil -- saf siniflandirma)."""

    INSIDE = "inside"
    """Bolge, verilen monitorlerin BIRLESIMI (union) tarafindan tamamen
    kapsaniyor (tek bir monitorde olabilir ya da birden fazla monitore
    kesintisiz yayilmis olabilir)."""
    PARTIAL = "partial"
    """Bolgenin bir kismi en az bir monitorun icinde, bir kismi hicbir
    monitorde degil (ornegin sanal masaustunun disina tasan bir pencere)."""
    OUTSIDE = "outside"
    """Bolge, verilen monitorlerin hicbiriyle kesismiyor (sifir alan
    dahil -- genisligi veya yuksekligi sifir olan bir bolge de OUTSIDE'tir)."""


# ---------------------------------------------------------------------------
# yuvarlama
# ---------------------------------------------------------------------------


def _round_half_away_from_zero(value: float) -> int:
    """Sifirdan uzaga yuvarlama: `2.5 -> 3`, `-2.5 -> -3`.

    Python'un yerlesik `round()`'u yariya-en-yakin-CIFT kullanir; bu
    fonksiyon bunun yerine simetrik ve sezgisel bir kural uygular (bkz.
    modul dokumantasyonu, "Yuvarlama sozlesmesi").
    """
    if value >= 0:
        return math.floor(value + 0.5)
    return math.ceil(value - 0.5)


def _scale_rect(rect: Rect, factor: float) -> Rect:
    """x, y, w, h degerlerini `factor` ile BAGIMSIZ olcekleyip yuvarlar.

    `monitor_index` ve `dpi_scale` degismeden tasinir: bu iki alan
    rect'in hangi monitore ait oldugunu tarif eden metadata'dir, x/y/w/h
    degerlerinin su an mantiksal mi fiziksel mi oldugundan bagimsizdir.
    """
    return Rect(
        x=_round_half_away_from_zero(rect.x * factor),
        y=_round_half_away_from_zero(rect.y * factor),
        w=_round_half_away_from_zero(rect.w * factor),
        h=_round_half_away_from_zero(rect.h * factor),
        monitor_index=rect.monitor_index,
        dpi_scale=rect.dpi_scale,
    )


# ---------------------------------------------------------------------------
# 1. mantiksal <-> fiziksel piksel
# ---------------------------------------------------------------------------


def logical_to_physical(rect: Rect) -> Rect:
    """Mantiksal (DPI-bagimsiz) pikselden fiziksel piksele.

    `rect.dpi_scale` ile carpar (%100 = 1.0, %150 = 1.5, %200 = 2.0, ...).
    Round-trip: `physical_to_logical` ile geri alindiginda HER ZAMAN
    orijinali verir (bkz. modul dokumantasyonu, ispat taslagi) -- bu,
    `dpi_scale < 1.0`'in asagida reddedilmesi sayesinde KOSULSUZ dogrudur.

    Raises:
        ValueError: `rect.dpi_scale < 1.0` ise. Windows'ta DPI olcegi
            hicbir zaman %100'un altina inmez (gecerli metadata degil) VE
            `s < 1` icin round-trip garantisi matematiksel olarak
            tutmaz (bkz. modul dokumantasyonu) -- bu yuzden sessizce
            kabul edilmek yerine acikca reddedilir.
    """
    if rect.dpi_scale < 1.0:
        raise ValueError(
            "dpi_scale >= 1.0 olmali (Windows olcekleri %100'un altina "
            "inmez ve s < 1 icin round-trip garantisi tutmaz), gelen: "
            f"{rect.dpi_scale!r}"
        )
    return _scale_rect(rect, rect.dpi_scale)


def physical_to_logical(rect: Rect) -> Rect:
    """Fiziksel pikselden mantiksal (DPI-bagimsiz) piksele.

    `rect.dpi_scale`'e boler. UYARI -- bu donusum KAYIPLI olabilir:
    sonucu tekrar `logical_to_physical` ile fizikselletirmek orijinali
    geri getirecegini GARANTI ETMEZ (bkz. modul dokumantasyonu).

    Raises:
        ValueError: `rect.dpi_scale < 1.0` ise. Windows'ta DPI olcegi
            hicbir zaman %100'un altina inmez (gecerli metadata degil) VE
            `s < 1` icin round-trip garantisi matematiksel olarak
            tutmaz (bkz. modul dokumantasyonu) -- bu yuzden sessizce
            kabul edilmek yerine acikca reddedilir.
    """
    if rect.dpi_scale < 1.0:
        raise ValueError(
            "dpi_scale >= 1.0 olmali (Windows olcekleri %100'un altina "
            "inmez ve s < 1 icin round-trip garantisi tutmaz), gelen: "
            f"{rect.dpi_scale!r}"
        )
    return _scale_rect(rect, 1.0 / rect.dpi_scale)


# ---------------------------------------------------------------------------
# 2. monitore-relatif <-> sanal masaustu
# ---------------------------------------------------------------------------


def to_monitor_relative(rect: Rect, monitor: Monitor) -> Rect:
    """Sanal masaustu koordinatindaki `rect`'i, `monitor`'un sol-ust
    kosesine gore RELATIF koordinata cevirir.

    Salt tam sayi toplama/cikarma -- yuvarlama yok, HER ZAMAN kayipsiz ve
    `to_virtual_desktop` ile round-trip kararlidir. Sonuc negatif
    olabilir (`rect`, `monitor`'un solunda/ustunde basliyorsa) -- bu
    matematiksel olarak gecerli bir durumdur; bolgenin fiilen o monitorde
    olup olmadigi `classify_region` ile ayrica degerlendirilir.

    Donen Rect, `monitor.monitor_index` ve `monitor.dpi_scale`'i tasir:
    artik hangi monitore gore konumlandigi belli oldugu icin o monitorun
    metadata'si otoriter kabul edilir.
    """
    return Rect(
        x=rect.x - monitor.x,
        y=rect.y - monitor.y,
        w=rect.w,
        h=rect.h,
        monitor_index=monitor.monitor_index,
        dpi_scale=monitor.dpi_scale,
    )


def to_virtual_desktop(rect: Rect, monitor: Monitor) -> Rect:
    """`to_monitor_relative`'in tersi: monitore-relatif koordinati sanal
    masaustu koordinatina cevirir.

    Windows'ta sanal masaustu koordinatlari NEGATIF olabilir (birincil
    monitorun solundaki/ustundeki monitorler icin `monitor.x`/`monitor.y`
    negatiftir -- bu alanin en klasik tuzagi). Bu fonksiyon bunu dogrudan
    destekler; ozel bir isaret veya durum kontrolu gerekmez, cunku salt
    toplama negatif tabanlarda da doganal olarak dogru sonucu verir.
    """
    return Rect(
        x=rect.x + monitor.x,
        y=rect.y + monitor.y,
        w=rect.w,
        h=rect.h,
        monitor_index=monitor.monitor_index,
        dpi_scale=monitor.dpi_scale,
    )


# ---------------------------------------------------------------------------
# 3 & 4. kesisim, bolge gecerliligi, monitore kirpma
# ---------------------------------------------------------------------------


def intersect(rect: Rect, monitor: Monitor) -> Rect | None:
    """`rect` ile `monitor`'un kesisimi; kesisim yoksa (veya alani sifir
    ya da negatifse) `None`.

    Yari-acik aralik varsayilir (`right = x + w`, `bottom = y + h` HARIC
    uctur) -- bu, `Rect.right`/`Rect.bottom` sozlesmesiyle birebir
    tutarlidir. Bu sayede iki komsu (bitisik, ortusmeyen) monitor
    arasindaki sinirin TAM UZERINDE oturan bir bolge, iki monitorun
    BIRLESIMI tarafindan dogru sekilde "tam kapsaniyor" sayilir; buna
    karsilik yalnizca bir kenari diger monitora DEGEN (ama ustune
    binmeyen) bir bolge kesismiyor sayilir (bkz. testler: "tam sinirda
    oturan" vs. "sinira deger ama kesismeyen").

    Donen Rect'in `monitor_index`/`dpi_scale` alanlari `monitor`'dan
    alinir: kesisim artik o monitorun sinirlari icinde kaldigindan, o
    monitorun metadata'si otoriter kabul edilir (bkz. `clamp_to_monitor`).
    """
    x1 = max(rect.x, monitor.x)
    y1 = max(rect.y, monitor.y)
    x2 = min(rect.right, monitor.right)
    y2 = min(rect.bottom, monitor.bottom)
    w = x2 - x1
    h = y2 - y1
    if w <= 0 or h <= 0:
        return None
    return Rect(
        x=x1, y=y1, w=w, h=h,
        monitor_index=monitor.monitor_index,
        dpi_scale=monitor.dpi_scale,
    )


def clamp_to_monitor(rect: Rect, monitor: Monitor) -> Rect | None:
    """Tasan `rect`'i `monitor` sinirlarina kirpar (clamp).

    Bilincli tasarim karari: eger kirpma sonucu boyut sifira (veya
    altina) duserse -- yani `rect`, `monitor` ile HIC kesismiyorsa --
    fonksiyon sessizce `w=0`/`h=0` gibi "gorunuse gore hala gecerli ama
    aslinda gorunmez" bir `Rect` DONDURMEZ; acikca `None` doner. Boylece
    cagiran kod, bos bir bolgeyi yanlislikla "yakalanabilir" saniyip
    kullanamaz (gorev paketi: "boyut sifira duserse acikca bildir").
    Donen deger `None` degilse, `w > 0` ve `h > 0` GARANTIDIR.
    """
    return intersect(rect, monitor)


def classify_region(rect: Rect, monitors: Sequence[Monitor]) -> RegionValidity:
    """`rect`, verilen `monitors` kumesinin BIRLESIMINE (union) gore nasil
    konumlanmis? bkz. `RegionValidity`.

    Varsayim (bilincli, belgelenmis): `monitors` kendi aralarinda
    ORTUSMEZ -- gercek Windows kurulumlarinda bu her zaman dogrudur
    (isletim sistemi, monitorlerin sanal masaustunde cakismasina izin
    vermez). Bu varsayim altinda, `rect` ile her monitorun kesisim
    alanlarinin TOPLAMI, `rect`'in birlesim tarafindan kapsanan gercek
    alanina esittir. Ortusen bir monitor kumesi verilirse kapsanan alan
    oldugundan fazla sayilabilir (INSIDE'a yanlis egilim); bu, pratikte
    olusmayan bir girdi sinifi oldugu icin bu fonksiyonun kapsami
    disinda birakilmistir.
    """
    total_area = rect.w * rect.h
    if total_area <= 0:
        return RegionValidity.OUTSIDE

    covered = 0
    for monitor in monitors:
        piece = intersect(rect, monitor)
        if piece is not None:
            covered += piece.w * piece.h

    if covered <= 0:
        return RegionValidity.OUTSIDE
    if covered >= total_area:
        return RegionValidity.INSIDE
    return RegionValidity.PARTIAL
