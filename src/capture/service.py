"""Suflor -- ekran/bolge yakalama servisi (`CaptureService`).

Tasarim dokumani 5.1 (bilesen 1), 5.5 (esszamanlilik/`seq`), 5.6 (hata
yonetimi), 5.7 (performans butcesi), 6 (teknoloji secimi: `mss`) ve 8.3-A2
(kabul kriterleri) karsiligi. Mod 2 canli dongusunun ILK halkasi; Mod 1'in
donmus ekranini da bu uretir.

Yapi
-----
`CaptureBackend` (Protocol) · `MssBackend` (gercek ekran) · `FakeBackend`
(headless test) · `CaptureService` (dogrulama + kirpma + sahiplik + `Frame`).

Backend ENJEKTE edilir: servis `mss`'i kendisi kurmaz, boylece butun test
paketi gercek ekrana dokunmadan kosar (8.3-A2: "Qt'ye sifir bagimlilik,
headless test edilebilir"). `clock` de enjekte edilir ki `Frame.captured_at`
deterministik olsun.

Protokol uyumu MAKINEYLE dogrulanir
-------------------------------------
Modul sonundaki `_uyum_fake: CaptureBackend = FakeBackend(())` ve
`_uyum_mss: CaptureBackend = MssBackend()` satirlari, iki somut backend'in
`CaptureBackend`'e uydugunu `mypy --strict`'e **dogrulattirir**. Satirlar
silinirse ya da degeri olmayan ciplak bir ek aciklamaya donerse mypy hicbir
sey dogrulamaz -- bu yuzden `headless_check.py` §4 varliklarini AST ile
denetler. `FakeBackend.grab`'in donusu `ImageArray` **kalir** (protokole
uyar) ve ureticinin `None` donusu `# type: ignore[return-value]` ile gecer;
imzayi `-> ImageArray | None` yapmak mypy'yi gecer ama `FakeBackend` artik
`CaptureBackend` **degildir**.

`mss` yan etkileri -- ENTEGRASYON KISITI (A6/A7)
-------------------------------------------------
Process icindeki **ilk** `mss.MSS()` kurulumu -- yani `MssBackend`'in ilk
`monitors()` veya `grab()` cagrisi -- process DPI politikasini kalici olarak
`PER_MONITOR_DPI_AWARE` yapar (`0 -> 2`, GERI ALINAMAZ; sef olctu) ve Qt'nin
olceklemesini etkiler. **`MssBackend` metotlari `QApplication` kurulmadan
ONCE cagrilmamalidir.** (`MssBackend()` yapiminin kendisi zararsizdir: tembel
oldugu icin `mss`'e hic dokunmaz -- modul duzeyindeki `_uyum_mss` ornegi de
bu yuzden guvenlidir.)

Ayrica `mss`'te `__del__` **yoktur**: kapatilmayan her `MSS()` ornegi bir
window DC + memory DC sizdirir ve **5001. kapatilmamis ornekte**
`GetWindowDC` kalici olarak basarisiz olur (sef olctu; `with` ile 12.000
ornek sorunsuz). Bu yuzden `monitors()` her cagrida `with mss.MSS() as ...`
kullanir ve `grab()` icin tutulan uzun omurlu tutamac `close()` ile
kapatilir (`MssBackend` bir baglam yoneticisidir).

Performans -- butce SIMDIDEN ASILIYOR (kapsam disi, belgelenir)
-----------------------------------------------------------------
Servisin **kendi ek yuku** (dogrulama + kirpma + kopya + `Frame` kurma)
5.7'nin 10 ms butcesinin cok altindadir (olculdu, 200 cagri, 600x200 bolge:
medyan 0.43 ms, p95 0.51 ms -- `evidence/budget.txt`). Ancak
gercek `mss.grab` medyani **13.5 ms**'dir ve 600x200 ile 100x50 icin
AYNIDIR -- yani bolge boyutundan bagimsiz SABIT maliyet (sef olctu). 5.7'nin
"Capture <= 10 ms" butcesi `mss` ile **zaten asiliyor**; bu T-005'in kapsami
disindadir ve DXGI Desktop Duplication icin ayri gorev acilmistir.

Thread guvenligi -- YOKTUR
----------------------------
`CaptureService` thread-safe **degildir**: `seq` sayaci ve monitor onbellegi
kilitsizdir. 5.5 geregi tek bir worker thread'den kullanilir. Eszamanlilik
testi A6'nin (pipeline) kapsamindadir; burada olculmez.

`seq` yalnizca TEK ORNEK icinde karsilastirilabilir (A6 kisiti)
-----------------------------------------------------------------
`seq` her `CaptureService` orneginde 0'dan baslar. 5.5'in "kucuk `seq`'i yok
say" kurali ornekler ARASINDA calismaz: pipeline servis ornegini
degistirirse karsilastirma tabanini **sifirlamak zorundadir**, aksi halde
yeni kareler eski sanilip atilir ve ceviri sessizce donar.

Import bicimi
--------------
`src/__init__.py` yoktur. Kardes moduller **relatif** import edilir
(`from . import dpi`); mutlak `from src.capture...` bicimi mypy'yi "Source
file found twice under different module names" ile kirar (sef olctu).
`src.contracts` ise mutlak import edilir.
"""
from __future__ import annotations

import numbers
import time
from collections.abc import Callable, Mapping, Sequence
from typing import TYPE_CHECKING, Protocol

import numpy as np

from src.contracts.errors import CaptureError
from src.contracts.models import Frame, ImageArray, Rect

from . import dpi
from .monitors import list_monitors, union_bbox

if TYPE_CHECKING:  # calisma zamani etkisi SIFIR -- `mss` yalnizca tip icin
    import mss

__all__ = ["CaptureBackend", "MssBackend", "FakeBackend", "CaptureService"]

_DENEME_SAYISI = 3
"""K6 (b): backend istisna firlatirsa en fazla bu kadar cagri yapilir."""


class CaptureBackend(Protocol):
    """Yakalama arka ucu -- servisin ekranla tek temasi.

    `monitors()` **ham `mss` biciminde** sozluk listesi dondurur: `[0]` sanal
    masaustu birlesimi, `[1:]` gercek monitorler (bkz. `monitors.py`).
    `grab(rect)` `(h, w, 3|4)` `uint8` bir `np.ndarray` dondurur; kanal
    duzeni BGR(A)'dir.
    """

    def monitors(self) -> Sequence[Mapping[str, object]]: ...

    def grab(self, rect: Rect) -> ImageArray: ...


# ---------------------------------------------------------------------------
# gercek ekran
# ---------------------------------------------------------------------------


class MssBackend:
    """`mss` tabanli gercek ekran arka ucu (v1 secimi, tasarim 6).

    Omur yonetimi iki AYRI kuraldan olusur, cunku iki cagrinin ihtiyaci
    farklidir:

    * `monitors()` **canli** kume ister. `mss.MSS.monitors` ornek uzerinde
      **memoize** edilir (`s.monitors is s.monitors` -> True; sef olctu), yani
      ayni ornekten tekrar okumak bayat liste verir. Bu yuzden her cagri
      **yeni** bir `mss.MSS()` kurar, `with` ile **kapatir** ve ham listeyi
      (`[0]` birlesim girdisi dahil) **oldugu gibi** dondurur. Donen sozlukler
      `dict(...)` ile kopyalanir -- bu bir savunma tercihidir, bir degismez
      degil: her cagri yeni bir ornek kurdugu icin bir listeyi bozmanin
      sonrakine etkisi zaten yoktur (sef olctu).
    * `grab()` **hiz** ister. Kurulum + `monitors` okumasi ~1.09 ms'dir; sicak
      yolda her karede odenemez. Bu yuzden tek bir uzun omurlu tutamac
      tutulur, **tembel** kurulur (ilk `grab()`'de, `__init__`'te DEGIL) ve
      `close()` ile kapatilir. `close()` idempotenttir.

    `__init__` `mss`'e **hic dokunmaz**; bu yuzden K1 engeli altinda bile
    kurulabilir ve modul duzeyindeki `_uyum_mss` ornegi zararsizdir.
    `mss.mss()` **kullanimdan kalkmistir** (`DeprecationWarning`, mss 10.2.0);
    bu sinif yalnizca `mss.MSS()` cagirir.

    Tutamac tipi olarak `mss.MSS | None` secildi (paketin sundugu iki
    secenekten biri; digeri `object | None`): `mss` bir `py.typed` isaretcisi
    tasidigi icin gercek tip mypy tarafindan cozulebiliyor ve `cast`/`Any`
    kacisi gerekmiyor.
    """

    def __init__(self) -> None:
        self._tutamac: mss.MSS | None = None

    def __enter__(self) -> MssBackend:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def monitors(self) -> Sequence[Mapping[str, object]]:  # pragma: no cover -- K1: gercek ekran, headless_check §3 ile denetleniyor
        import mss

        with mss.MSS() as oturum:
            return [dict(ham) for ham in oturum.monitors]

    def grab(self, rect: Rect) -> ImageArray:  # pragma: no cover -- K1: gercek ekran, headless_check §3 ile denetleniyor
        import mss

        if self._tutamac is None:
            self._tutamac = mss.MSS()
        kutu = {"left": rect.x, "top": rect.y, "width": rect.w, "height": rect.h}
        return np.asarray(self._tutamac.grab(kutu), dtype=np.uint8)

    def close(self) -> None:  # pragma: no cover -- K1: gercek ekran, headless_check §3 ile denetleniyor
        if self._tutamac is not None:
            self._tutamac.close()
            self._tutamac = None


# ---------------------------------------------------------------------------
# test arka ucu
# ---------------------------------------------------------------------------


def _varsayilan_uretici(rect: Rect) -> ImageArray:
    """Varsayilan `image_factory`: `(rect.h, rect.w, 4)` sifir dizi (BGRA)."""
    return np.zeros((rect.h, rect.w, 4), dtype=np.uint8)


class FakeBackend:
    """Headless test arka ucu -- gercek ekrana ve `mss`'e hic dokunmaz (K1).

    Args:
        monitors: Monitor `Rect` demeti. `monitors()` bunlardan **ham `mss`
            bicimi** uretir ve `[0]` **birlesim girdisini de** koyar -- `[0]`'i
            unutan bir sahte backend ilk monitoru sessizce yutardi.
        image_factory: `grab` icin dizi ureticisi. **`None` dondururse**
            backend `None` dondurmus sayilir (K6 sinif c). **Istisna
            firlatirsa** o istisna `grab`'den **oldugu gibi** yayilir (K6
            sinif b). Varsayilani `(h, w, 4)` sifir dizi.
        raw_override: Verilirse `monitors()` ham listeyi bunun yerine
            dondurur.

    `raw_override` **ayni adla PUBLIC bir ozniteliktir** ve `monitors()` her
    cagrida onu **o anki haliyle** okur -- yapimda anlik goruntu ALINMAZ.
    Testler ile uygulama arasindaki tek mutasyon arayuzu budur: bozuk sozluk,
    kume sayi/sira degisimi ve canlilik vakalari yalnizca bu yolla kurulabilir.
    Ozel bir ad (`self._raw_override`) kullanilsaydi testin `fb.raw_override =
    [...]` atamasi yeni bir oznitelik yaratir ve mutasyon sessizce kaybolurdu.

    Gozlem oznitelikleri (paket bunlarin adlarini belirtmiyordu -- burada
    tanimlanir):

    * ``monitors_calls`` -- `monitors()` cagri sayaci (K5 sicak yol olcusu).
    * ``grab_calls`` -- `grab()` cagri sayaci; **uretici patlasa da artar**
      (K6'nin cagri sayisi hucreleri bunu gerektirir).
    * ``grab_rects`` -- `grab()`'e ulasan `Rect`'lerin sirali listesi (K3/K9).
    * ``monitor_rects`` -- yapimda verilen monitor demeti. Ad `monitors`
      OLAMAZ: `monitors` bu sinifta bir **metottur**, ayni adli bir oznitelik
      onu golgeler ve protokol uyumu calisma zamaninda cokerdi.
    """

    def __init__(
        self,
        monitors: tuple[Rect, ...],
        image_factory: Callable[[Rect], ImageArray | None] = _varsayilan_uretici,
        raw_override: Sequence[Mapping[str, object]] | None = None,
    ) -> None:
        self.monitor_rects = monitors
        self.image_factory = image_factory
        self.raw_override = raw_override
        self.monitors_calls = 0
        self.grab_calls = 0
        self.grab_rects: list[Rect] = []

    def monitors(self) -> Sequence[Mapping[str, object]]:
        self.monitors_calls += 1
        if self.raw_override is not None:
            return self.raw_override
        birlesim = union_bbox(self.monitor_rects)
        bos = Rect(0, 0, 0, 0)
        kok = birlesim if birlesim is not None else bos
        ham: list[Mapping[str, object]] = [_ham_sozluk(kok)]
        ham.extend(_ham_sozluk(r) for r in self.monitor_rects)
        return ham

    def grab(self, rect: Rect) -> ImageArray:
        self.grab_calls += 1
        self.grab_rects.append(rect)
        return self.image_factory(rect)  # type: ignore[return-value]


def _ham_sozluk(rect: Rect) -> Mapping[str, object]:
    """`Rect` -> ham `mss` sozlugu (yalnizca `FakeBackend` icin)."""
    return {"left": rect.x, "top": rect.y, "width": rect.w, "height": rect.h}


# ---------------------------------------------------------------------------
# giris kabul kapisi + duzlestirme (K8)
# ---------------------------------------------------------------------------


def _kabul_ve_duzlestir(ad: str, deger: object) -> int:
    """Giris degerini KABUL ET, sonra duz `int`'e duzlestir.

    Duzlestirme bir **donusumdur**, bir dogrulama degil -- bu yuzden onune
    kabul kapisi konur. Ciplak `int()` (sef olctu): `10.9` -> sessizce `10`,
    `'10'` ve `True` -> sessizce kabul, `inf`/`nan` -> K6 taksonomisi disinda
    `OverflowError`/`ValueError`. Yani gurultulu bir hata sessiz bir yanlisa
    donusurdu; ustelik K5 ayni degerleri monitor sozlugunde acikca reddediyor.

    Kabul: `numbers.Integral` (`bool` haric) **ya da** tam sayi degerli bir
    `float`/`np.floating` (`10.0`, `np.float64(10.0)`). Ret: `'10'`, `True`,
    `10.9`, `nan`, `inf`, `np.float32(10.5)`.
    """
    if isinstance(deger, bool):
        raise CaptureError(f"bolge alani '{ad}' tamsayi olmali, gelen: {deger!r}")
    if isinstance(deger, numbers.Integral):
        return int(deger)
    if isinstance(deger, (float, np.floating)):
        sayi = float(deger)
        if sayi.is_integer():
            return int(sayi)
    raise CaptureError(f"bolge alani '{ad}' tamsayi olmali, gelen: {deger!r}")


def _kabul_ve_duzlestir_olcek(deger: object) -> float:
    """`dpi_scale`'i duz `float`'a duzlestirir.

    `np.float64` `float`'in ALT SINIFI oldugu icin serilesir, ama
    **`np.float32` serilesmez** (sef olctu) -- bu yuzden `float()` kosulsuz
    uygulanir. Sayi olmayan bir deger (`'1.5'` gibi) sessizce cevrilmez.
    """
    if isinstance(deger, bool) or not isinstance(deger, (int, float, np.floating, np.integer)):
        raise CaptureError(f"bolge alani 'dpi_scale' sayi olmali, gelen: {deger!r}")
    return float(deger)


# ---------------------------------------------------------------------------
# servis
# ---------------------------------------------------------------------------


class CaptureService:
    """Ekranin tamamini ya da bir bolgesini yakalayip `Frame` uretir.

    Args:
        backend: `CaptureBackend`; gercek ekran icin `MssBackend`, test icin
            `FakeBackend`.
        clock: `captured_at` icin saat okuyucu. Varsayilan `time.monotonic`
            (duvar saati DEGIL -- tasarim 5.3). Enjekte edilebilir olmasi
            `captured_at`'i deterministik test edilebilir kilar.

    Raises:
        CaptureError: yapimda monitor kumesi okunamazsa (bozuk ham sozluk).
            Bu, K6'nin yakalama taksonomisinin DISINDADIR: K6 yalnizca
            `capture_region`/`capture_full` cagrilarini kapsar.

    Servis DPI'ye **kordur** (K3): `capture_region(rect)` icindeki `rect`
    fiziksel piksel, sanal masaustu koordinatlarindadir. Servis olcekleme
    yapmaz ve `rect.dpi_scale`'i **hicbir kararda kullanmaz** -- yalnizca
    `Frame.rect`'e tasir. `rect.monitor_index` de hicbir kararda kullanilmaz:
    bolge yalnizca `x, y, w, h` ile degerlendirilir. (Bu makinede `Rect`'in
    varsayilani `monitor_index=0` birincil OLMAYAN sol monitordur; varsayilana
    gore kirpmak gecerli bolgeleri reddederdi.)

    **Servis DPI olcegi URETEMEZ.** `mss` monitor sozlukleri olcek anahtari
    tasimaz (sef olctu), bu yuzden monitor kumesindeki her `Rect`'in olcegi
    daima `1.0`'dir. `Frame.rect.dpi_scale` **cagiranin beyanidir**;
    `capture_full` icin `1.0`'dir. Olcek bilgisi A7'de (Qt
    `devicePixelRatio`) uretilir ve `Rect`'e cagiran tarafindan yazilir.
    `dpi.intersect` ciktisinin metadata'si **kullanilmaz**: `intersect` donen
    `Rect`'in `monitor_index`/`dpi_scale`'ini **ikinci argumandan** alir
    (sef olctu), yani PARTIAL kirpmasinda cagiranin `1.5`'i birlesimin
    `1.0`'ina ezilirdi.
    """

    def __init__(
        self,
        backend: CaptureBackend,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._backend = backend
        self._clock = clock
        self._seq = -1
        self._monitors: tuple[Rect, ...] = list_monitors(backend)

    # -- monitor kumesi ----------------------------------------------------

    @property
    def monitors(self) -> tuple[Rect, ...]:
        """Servisin ONBELLEKTEKI monitor kumesi (yapimda/`refresh` ile okunur).

        `capture_region`/`capture_full` `backend.monitors()`'i **hic**
        cagirmaz: 5.7'nin sicak yolunda her karede monitor sorgulamak
        `mss`'te ~1.09 ms'lik bir kurulum demektir. Degisimi ogrenmenin yolu
        `refresh_monitors()`'tir.
        """
        return self._monitors

    def refresh_monitors(self) -> tuple[Rect, ...]:
        """Monitor kumesini backend'den yeniden okur ve yeni kumeyi dondurur.

        `seq`'i **sifirlamaz** (K2). Bozuk sozlukte `CaptureError` firlatir ve
        bu durumda servisin **eski kumesi degismeden kalir** -- atama yalnizca
        basarili donusumden sonra yapilir; yarim guncellenmis bir durum
        olusmaz.

        Donen deger: yeni kume. (Paket donusu belirtmiyordu; `None` yerine
        kumeyi dondurmek cagiranin ikinci bir okuma yapmasini gereksiz kilar.)
        """
        yeni = list_monitors(self._backend)
        self._monitors = yeni
        return yeni

    # -- yakalama ----------------------------------------------------------

    def capture_region(self, rect: Rect) -> Frame:
        """Verilen bolgeyi yakalar.

        Akis: giris kabul kapisi + duzlestirme -> alan denetimi -> BIRLESIME
        gore siniflandirma -> (gerekirse) BIRLESIME gore kirpma -> backend
        cagrisi (K6 yeniden deneme) -> bicim dogrulama -> **kosulsuz kopya**
        -> `Frame`.

        Duzlestirme `capture_region`'in **girisinde** yapilir, `Frame.rect`
        kurulumunda degil: dondurulmus `dpi.py` isaretsiz numpy tamsayilarinda
        **tasar** (`np.uint16`/`np.uint32` ile `classify_region` `inside`
        yerine `partial` verir ve uc `RuntimeWarning: overflow` doğurur -- sef
        olctu), yani `monitor_index` sessizce yanlis cikardi. `classify_region`,
        `intersect` ve `monitor_index` hesabi **yalniz duzlestirilmis** `Rect`
        gorur.

        Kirpma **her zaman** `union_bbox(monitors)`'a karsi yapilir, **asla**
        tek bir monitore karsi degil. (`dpi.intersect` ve `dpi.clamp_to_monitor`
        birebir ayni govdedir; yanlislik fonksiyon adinda degil ikinci
        argumandadir. Sef olctu: iki monitore yayilan 5300w bolge tek monitore
        karsi 2560w, birlesime karsi 5120w verir -- dogru cevap 5120w.)

        Raises:
            CaptureError: bolge tamsayi olmayan alan tasiyorsa; alani sifir ya
                da negatifse; monitor kumesi bossa; bolge `OUTSIDE` ise
                (bunlarin **hicbirinde backend cagrilmaz**, K6 sinif a);
                backend uc denemede de istisna firlatirsa (sinif b); ya da
                backend'in ciktisi K7 bicimine uymuyorsa (sinif c, yeniden
                deneme YOK).

        Kabul edilen sinir: L seklinde bir duzende birlesim dikdortgeni
        hicbir monitore dusmeyen "olu" alan icerebilir ve `mss` orayi siyah
        doldurur. v1 bunu tespit etmez, belgeler.
        """
        duz = self._duzlestir(rect)
        hedef = self._hedef_dikdortgen(duz)
        goruntu = self._backend_dan_al(hedef)
        self._seq += 1
        return Frame(image=goruntu, rect=hedef, captured_at=self._clock(), seq=self._seq)

    def capture_full(self, monitor_index: int) -> Frame:
        """`monitor_index` numarali monitorun **tamamini** yakalar.

        `capture_region(self.monitors[monitor_index])` ile **ayni backend
        cagrisini** uretir; `Frame.rect`, goruntu icerigi ve -- enjekte sabit
        saatle -- `captured_at` birebir aynidir. `seq` K2 geregi **artar**, bu
        yuzden iki `Frame` **esit degildir** (`seq` karsilastirmaya dahildir).

        Sanal masaustunun TAMAMI bu metotla yakalanmaz: onun yolu
        `capture_region(union_bbox(monitors))`'tir (o bolge `INSIDE`
        siniflanir). `capture_full` yalnizca tek bir monitoru hedefler.

        Raises:
            CaptureError: `monitor_index` aralik disiysa (negatifler dahil --
                Python'un negatif indekslemesi burada **bilerek** devre
                disidir, yoksa `capture_full(-1)` sessizce son monitoru
                verirdi) ya da monitor kumesi bossa. Backend cagrilmaz.
        """
        if not 0 <= monitor_index < len(self._monitors):
            raise CaptureError(
                f"monitor indeksi aralik disi: {monitor_index} "
                f"(kume boyutu {len(self._monitors)})"
            )
        return self.capture_region(self._monitors[monitor_index])

    # -- ic yardimcilar ----------------------------------------------------

    def _duzlestir(self, rect: Rect) -> Rect:
        """Giris `Rect`'ini kabul kapisindan gecirip duz `int`/`float` yapar."""
        return Rect(
            x=_kabul_ve_duzlestir("x", rect.x),
            y=_kabul_ve_duzlestir("y", rect.y),
            w=_kabul_ve_duzlestir("w", rect.w),
            h=_kabul_ve_duzlestir("h", rect.h),
            monitor_index=rect.monitor_index,
            dpi_scale=_kabul_ve_duzlestir_olcek(rect.dpi_scale),
        )

    def _hedef_dikdortgen(self, duz: Rect) -> Rect:
        """Dogrulama + kirpma; backend'e gidecek ve `Frame.rect` olacak `Rect`.

        `dpi_scale` cagiranin beyanidir (INSIDE ve PARTIAL yollarinda AYNI);
        `monitor_index` ise **hesaplanir** (K8), cagiranin degeri yok sayilir.
        """
        if duz.w <= 0 or duz.h <= 0:
            raise CaptureError(
                f"bolgenin alani yok: w={duz.w}, h={duz.h} (ikisi de pozitif olmali)"
            )
        if not self._monitors:
            raise CaptureError("monitor kumesi bos: yakalanacak ekran yok")

        sinif = dpi.classify_region(duz, self._monitors)
        if sinif is dpi.RegionValidity.OUTSIDE:
            raise CaptureError(
                f"bolge hicbir monitorle kesismiyor: "
                f"x={duz.x}, y={duz.y}, w={duz.w}, h={duz.h}"
            )

        geometri = duz
        if sinif is dpi.RegionValidity.PARTIAL:
            birlesim = union_bbox(self._monitors)
            if birlesim is None:  # yapisal olarak erisilemez (kume bos degil)
                raise CaptureError("birlesim dikdortgeni hesaplanamadi")
            kirpik = dpi.intersect(duz, birlesim)
            if kirpik is None:  # yapisal olarak erisilemez (PARTIAL => kesisim var)
                raise CaptureError("birlesime kirpma bos sonuc verdi")
            geometri = kirpik

        x, y, w, h = int(geometri.x), int(geometri.y), int(geometri.w), int(geometri.h)
        aday = Rect(x=x, y=y, w=w, h=h, monitor_index=0, dpi_scale=duz.dpi_scale)
        return Rect(
            x=x, y=y, w=w, h=h,
            monitor_index=self._monitor_indeksi(aday),
            dpi_scale=duz.dpi_scale,
        )

    def _monitor_indeksi(self, hedef: Rect) -> int:
        """K8: yakalanan dikdortgenle **pozitif alanli** kesisimi olan monitor
        sayisi tam 1 ise o monitorun indeksi, aksi halde `-1`.

        `-1` "tek monitore atfedilemez" demektir ve `union_bbox`'in `-1`'iyle
        **ayni anlamdadir**. Bolgenin o monitorun tamamen icinde olmasi
        gerekmez (L duzeninde olu alan icerebilir). Kural, monitorlerin
        ORTUSMEDIGI varsayimi altindadir (`dpi.classify_region`'in belgeledigi
        varsayim); klon/ic ice duzende kural geregi `-1` doner, ama Windows
        klon modu tek monitor bildirdigi icin bu uretimde erisilemez.
        """
        kesisen = [
            m.monitor_index for m in self._monitors if dpi.intersect(hedef, m) is not None
        ]
        return kesisen[0] if len(kesisen) == 1 else -1

    def _backend_dan_al(self, hedef: Rect) -> ImageArray:
        """K6 yeniden deneme taksonomisi + K7 bicim dogrulama + kopya.

        (b) backend **istisna** firlatirsa en fazla `_DENEME_SAYISI` cagri
        yapilir ve son istisna `__cause__` olarak baglanir. (c) backend
        **donduğu halde cikti gecersizse** yeniden **denenmez** ve `__cause__`
        `None` kalir -- bozuk bir bicim ikinci denemede duzelmez, yalnizca
        13.5 ms daha harcanirdi.
        """
        son_istisna: BaseException | None = None
        for deneme in range(1, _DENEME_SAYISI + 1):
            try:
                ham = self._backend.grab(hedef)
            except Exception as exc:  # sinif (b) -- backend'in kendi hatasi
                son_istisna = exc
                continue
            self._bicimi_dogrula(ham, hedef, deneme)
            return self._kopyala(ham)
        raise CaptureError(
            f"yakalama {_DENEME_SAYISI} denemede de basarisiz: "
            f"x={hedef.x}, y={hedef.y}, w={hedef.w}, h={hedef.h}"
        ) from son_istisna

    @staticmethod
    def _bicimi_dogrula(ham: object, hedef: Rect, deneme: int) -> None:
        """K7: bicim kurali **TIP DUZEYINDEDIR**, girdi sayarak yazilmaz.

        `isinstance(ham, np.ndarray)` degilse `CaptureError`; hicbir
        `np.asarray` / `np.array` / `hasattr` donusumu yapilmaz. Girdi
        **sayan** bir kural kacinilmaz olarak anahtar deligi acar: en az dort
        ayrisan bicim (`__array_interface__` tasiyan nesne -- gercek
        `mss.ScreenShot` tam olarak boyledir --, `__array__` metotlu nesne,
        3 boyuta `cast` edilmis `memoryview`, PEP 688 `__buffer__` tasiyan
        nesne) `np.asarray` ile `(h, w, 4) uint8` verir ve sessizce kabul
        edilirdi.
        """
        if not isinstance(ham, np.ndarray):
            raise CaptureError(
                f"backend np.ndarray dondurmedi: {type(ham).__name__} "
                f"(deneme {deneme}); sessiz donusum yapilmaz"
            )
        if ham.ndim != 3:
            raise CaptureError(f"goruntu 3 boyutlu olmali, gelen ndim={ham.ndim}")
        if ham.shape[2] not in (3, 4):
            raise CaptureError(f"kanal sayisi 3 ya da 4 olmali, gelen {ham.shape[2]}")
        if ham.dtype != np.uint8:
            raise CaptureError(f"goruntu uint8 olmali, gelen {ham.dtype}")
        if ham.shape[0] != hedef.h or ham.shape[1] != hedef.w:
            raise CaptureError(
                f"boyut uyusmuyor: beklenen ({hedef.h}, {hedef.w}), "
                f"gelen ({ham.shape[0]}, {ham.shape[1]})"
            )

    @staticmethod
    def _kopyala(ham: ImageArray) -> ImageArray:
        """BGR(A) -> BGR, **kosulsuz kopya** (K7 sahiplik).

        `np.asarray(ScreenShot)` `mss`'in `bytearray`'ini **takma adlar** ve
        dizi `writeable`'dir (sef olctu): kopyalanmazsa `Frame.image` uzerinde
        yerinde bir degisiklik backend nesnesini bozar. Kopya 3 kanalda da,
        4 kanalda da yapilir -- `np.ascontiguousarray(a[:, :, :3])` 4 kanalda
        kopyalar ama **3 kanalda takma ad dondurur** (sef dogruladi). Kopya
        ayrica salt-okunur bir kaynaktan (`np.frombuffer(shot.bgra, ...)`)
        **yazilabilir** bir dizi uretir.
        """
        return np.array(ham[:, :, :3], dtype=np.uint8, copy=True, order="C")


# ---------------------------------------------------------------------------
# protokol uyum satirlari -- mypy --strict bunlari DOGRULAR (K1/O-F)
# ---------------------------------------------------------------------------

_uyum_fake: CaptureBackend = FakeBackend(())
_uyum_mss: CaptureBackend = MssBackend()
