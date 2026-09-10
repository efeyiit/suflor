"""Suflor -- monitor listeleme yardimcilari (saf fonksiyonlar).

Tasarim dokumani 5.1 (`CaptureService`, monitor farkindaligi) ve 8.3-A2'nin
"monitor kaybi simulasyon testi" kriterinin tabani. `dpi.py` gibi bu modul de
**tamamen saftir**: sinif yok, durum yok, I/O yok, `mss` import'u yok
(`headless_check.py` §2 bunu AST ile denetler). Ham monitor bilgisi her zaman
parametre olarak gelir; boylece headless ve deterministik test edilebilir.

Ham `mss` bicimi -- sefin bu makinede OLCTUGU liste
------------------------------------------------------
`mss.MSS().monitors` bir sozluk listesidir ve **`[0]` sanal masaustunun
BIRLESIMIDIR**, gercek monitor degildir; gercek monitorler `[1:]`'dir::

    [{'left': -2560, 'top': 0, 'width': 5120, 'height': 1440},
     {'left': -2560, 'top': 0, 'width': 2560, 'height': 1440,
      'is_primary': False, 'name': ..., 'unique_id': ...},
     {'left': 0, 'top': 0, 'width': 2560, 'height': 1440,
      'is_primary': True, ...}]

Iki tuzak burada gorunur: (1) `[0]`'i monitor sanmak butun indeksleri
kaydirir; (2) sol monitorun `left` degeri **NEGATIFTIR** ve **birincil
degildir** -- Windows'ta sanal masaustu koordinatlari negatif olabilir.

DPI olcegi -- `mss` TASIMAZ (sef olctu)
-----------------------------------------
Ham sozluklerde yalnizca `left/top/width/height/is_primary/name/unique_id`
vardir; **DPI/scale anahtari yoktur**. Bu yuzden `rects_from_mss_monitors`
her monitore `dpi_scale=1.0` yazar ve servisin monitor kumesindeki her
`Rect`'in olcegi daima 1.0'dir. Olcegi yalnizca cagiran bilebilir (A7'nin
Qt'den okudugu `devicePixelRatio`).

Duzlestirme -- `Rect` alanlarina numpy skaleri YAZILMAZ
---------------------------------------------------------
Kabul edilen her deger `int(v)` ile duz `int`'e cevrilir. Gerekce (sef
olctu): sizinti **esitlikle gorulemez** (`Rect(np.int64(10), ...) ==
Rect(10, ...)` -> True, hash esit, `right`/`bottom` aritmetigi dogru); zarar
serilestirmede cikar (`json.dumps(asdict(rect))` -> `TypeError: Object of
type int64 is not JSON serializable`) ve karisik isaretli aritmetikte
(`np.uint64 - np.int64 -> float64`). `typing.cast(int, v)` ile `mypy`'yi
susturmak bu yuzden YASAKTIR: mypy'yi gecer, skaleri sizdirir.

Monitor kimligi -- KONUMSAL ve KARARSIZ (kabul edilen eksiklik)
-----------------------------------------------------------------
`monitor_index` yalnizca `mss`'in dondurdugu SIRADIR. `mss` `is_primary` ve
`unique_id` veriyor ama dondurulmus `Rect` sozlesmesi bu alanlari tasiyamaz.
Duzen degisiminde (monitor takilip cikarilinca) eski `Rect`'ler sessizce
baska bir monitore isaret edebilir. Tasarim 5.6'nin "seridi birincil
monitore tasi" satiri, `Rect`'e kimlik alani eklenmeden uygulanamaz -- v1
kapsami disinda, A7 icin sozlesme degisikligi adayi.
"""
from __future__ import annotations

import numbers
from collections.abc import Mapping, Sequence
from typing import Protocol

from src.contracts.errors import CaptureError
from src.contracts.models import Rect

__all__ = [
    "MonitorKaynagi",
    "rects_from_mss_monitors",
    "list_monitors",
    "union_bbox",
]

_ANAHTARLAR = ("left", "top", "width", "height")


class MonitorKaynagi(Protocol):
    """`list_monitors`'in tek ihtiyaci: ham `mss` listesi veren bir nesne.

    `service.py`'deki `CaptureBackend` bu protokole YAPISAL olarak uyar.
    Ayri bir protokol tanimlanmasinin nedeni dairesel import'tan kacinmaktir:
    `service.py` bu modulu import eder, bu modul `service.py`'yi ETMEZ --
    boylece `monitors.py` saf kalir (`headless_check.py` §2).
    """

    def monitors(self) -> Sequence[Mapping[str, object]]: ...


def _tamsayi(deger: object, monitor_indeksi: int, anahtar: str) -> int:
    """Ham sozluk degerini kabul et ve duz `int`'e DUZLESTIR.

    Kabul kurali: `isinstance(v, numbers.Integral) and not isinstance(v, bool)`.
    `int` ve `numpy.int64/int32/uint8` **kabul**; `bool`/`None`/`str`/`float`
    **ret**. (`np.bool_` `numbers.Integral` DEGILDIR -- sef olctu -- bu yuzden
    ayrica elenmesine gerek yok; `bool` ise `int` alt sinifi oldugu icin
    acikca elenir.)

    Gercek `mss` duz `int` verir; numpy tamsayilari DXGI Desktop Duplication
    gorevi ve numpy tabanli sahte backend'ler icin kabul edilir.
    """
    if isinstance(deger, bool) or not isinstance(deger, numbers.Integral):
        raise CaptureError(
            f"monitor {monitor_indeksi} (ham indeks {monitor_indeksi + 1}): "
            f"'{anahtar}' tamsayi degil -> {deger!r}"
        )
    return int(deger)


def rects_from_mss_monitors(dicts: Sequence[Mapping[str, object]]) -> tuple[Rect, ...]:
    """Ham `mss` monitor listesini `Rect` demetine cevirir (SAF).

    `[0]` sanal masaustu BIRLESIMIDIR ve **atilir**; `[1:]` sirayla
    `monitor_index=0..n-1`, `dpi_scale=1.0` ile `Rect`'e cevrilir. Sozlukteki
    fazladan anahtarlar (`is_primary`, `name`, `unique_id`, ...) **yok
    sayilir**. Bos liste ve yalnizca birlesim girdisi tasiyan liste -> `()`.

    Raises:
        CaptureError: `[1:]` icindeki bir sozlukte `left/top/width/height`
            anahtarlarindan biri **eksikse** ya da degeri **tamsayi degilse**.
            Mesaj hangi monitorde ve hangi anahtarda bozuldugunu bildirir.
    """
    sonuc: list[Rect] = []
    for i, ham in enumerate(dicts[1:]):
        degerler: list[int] = []
        for anahtar in _ANAHTARLAR:
            if anahtar not in ham:
                raise CaptureError(
                    f"monitor {i} (ham indeks {i + 1}): '{anahtar}' anahtari yok"
                )
            degerler.append(_tamsayi(ham[anahtar], i, anahtar))
        sol, ust, genislik, yukseklik = degerler
        sonuc.append(
            Rect(x=sol, y=ust, w=genislik, h=yukseklik, monitor_index=i, dpi_scale=1.0)
        )
    return tuple(sonuc)


def list_monitors(backend: MonitorKaynagi) -> tuple[Rect, ...]:
    """`backend.monitors()`'i `rects_from_mss_monitors`'a verir.

    `backend.monitors()`'in firlattigi istisna **oldugu gibi yayilir**,
    sarmalanmaz: backend'in kendi hatasi (surucu, DC tukenmesi, ...) K6
    taksonomisinin (b) sinifi degildir -- K6 yalnizca YAKALAMA cagrilarini
    kapsar. Bozuk sozluk hatasi ise `CaptureError`'dur (yukariya bakiniz).
    """
    return rects_from_mss_monitors(backend.monitors())


def union_bbox(monitors: Sequence[Rect]) -> Rect | None:
    """Monitor kumesinin BIRLESIM sinirlayici dikdortgeni; bos kume -> `None`.

    Donen `Rect` kumedeki her monitoru **kapsar** ve bundan **daha buyuk
    degildir**: `x=min(x)`, `y=min(y)`, `right=max(right)`, `bottom=max(bottom)`.
    Siraya duyarsizdir.

    `monitor_index=-1` ve `dpi_scale=1.0` yazilir. `-1`, K8'in
    `Frame.rect.monitor_index` kuralindaki `-1` ile **ayni anlamdadir**:
    "tek bir monitore atfedilemez". Boylece birlesim dikdortgeni yanlislikla
    0. monitor sanilamaz -- bu makinede 0. monitor birincil bile degildir.

    UYARI (kabul edilen sinir): L seklinde bir duzende birlesim dikdortgeni
    hicbir monitore dusmeyen "olu" alan icerebilir; `mss` o alani siyah
    doldurur. v1 bunu tespit etmez, belgeler.
    """
    if not monitors:
        return None
    x = min(m.x for m in monitors)
    y = min(m.y for m in monitors)
    sag = max(m.right for m in monitors)
    alt = max(m.bottom for m in monitors)
    return Rect(x=x, y=y, w=sag - x, h=alt - y, monitor_index=-1, dpi_scale=1.0)
