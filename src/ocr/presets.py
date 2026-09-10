"""OCR on ayarina gore normalizasyon parametreleri.

Tasarim dokumani S3.2: `ocr_preset` blok gruplama, guven esigi, olcekleme
faktoru ve kontrast on islemesini degistirir. **Bu turda (T-004) yalnizca
normalizasyon parametreleri** burada tutulur -- `olcekleme faktoru` ve
`kontrast on islemesi` alanlari bilincli olarak disaridadir (S3.2'nin OCR
motoru gorevine ait; motor henuz yok). Yapı bu genislemeyi kaldıracak
sekilde kuruludur: `NormalizerParams` on ayar basina TEK dataclass ornegidir
(dort ayri sinif degil) -- sonraki gorev yeni alanlari bu SINIFA ekleyebilir,
yeni bir tur acmasi gerekmez.

known_gap (T-004 delivery.md'de de yer alir): `scale_factor` ve
`contrast_preprocessing` bu dosyaya eklenmedi -- kapsam disi, kendim ekleme
demedim.

TUR 2 (duzeltme turu, sef_karari-tur2.md): `SPEAKER_LABEL_SEPARATORS`
adlandirilmis sabiti eklendi (K17 -- konusmaci ayiraci kumesi, ASCII `:`
+ fullwidth `：`). Bu turda `NormalizerParams`'da SAYISAL bir alan
degisikligi YOK; K15/K16/K18 tamamen `normalizer.py` icindeki mantik
duzeltmeleridir.

Modul duzeyinde MUTABLE global (list/dict/set) YOK -- `purity_check.py` bunu
statik olarak denetliyor. Preset -> parametre eslemesi bir `match` ifadesiyle
yapilir; `NormalizerParams` `frozen=True` oldugu icin modul duzeyindeki dort
sabit ornek zaten degismezdir.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from src.contracts.models import OcrPreset

__all__ = ("NormalizerParams", "get_params", "SPEAKER_LABEL_SEPARATORS")
"""Tuple -- liste degil: `purity_check.py` modul duzeyinde MUTABLE global
(list/dict/set) arar; bkz. `normalizer.py` ayni not."""


SPEAKER_LABEL_SEPARATORS: Final[tuple[str, ...]] = (":", "：")
"""K17 (sef_karari-tur2.md, TUR 2) -- konusmaci etiketi (`Isim<ayirac>`)
tespitinde ayirac olarak taninan karakterler. `normalizer.py`
`_find_speaker_separator` metin icinde bu kumedeki HERHANGI birinin EN
SOL konumunu arar (ilk eslesme kazanir, kume icindeki SIRA onemli
degildir):

  - `:`  ASCII iki nokta ust uste (U+003A)
  - `：` TAM GENISLIK (fullwidth) iki nokta ust uste (U+FF1A) -- JP/KR
    oyunlarinda konusmaci etiketi STANDART olarak boyle yazilir; TUR 1'de
    bu KAPSANMIYORDU (`'勇者：こんにちは'` gibi bir blok konusmacisiz
    kaliyordu -- Bulgu 3, Tester-C, sef_karari-tur2.md).

Adlandirilmis sabit olarak BURADA tutulur (normalizer.py icinde sabit
kodlama YOK -- packet.md'nin "esikler presets.py'de adlandirilmis sabit
olacak" kuraliyla ayni ilke). Her iki karakter de TEK codepoint (str
uzunlugu 1); `_find_speaker_separator` bunu varsayarak `idx + 1` ile
diliyor. Baska CJK ayirac varyantlari (ör. `﹕` U+FE55, dikey yazimda
gorulen ayiraclar) bu turde BILINCLI olarak KAPSAM DISI -- delivery.md
`known_gaps`'te de belirtilir.
"""


@dataclass(frozen=True)
class NormalizerParams:
    """Tek bir `OcrPreset` icin normalizasyon esikleri.

    Alanlarin hepsi `normalizer.py` tarafindan **carpma ile** kullanilir
    (`gap < ratio * height` bicimde), **bolme ile degil** -- boylece
    `bbox.h == 0` veya `bbox.w == 0` gibi yozlasmis girdilerde bolme
    hatasi olusmaz (bkz. normalizer.py `_should_group`).
    """

    confidence_threshold: float
    """[0,1] araligi. Bu esigin ALTINDAKI blok duser; esige ESIT olan blok
    KALIR (`confidence < threshold` -> duser, `confidence == threshold` ->
    kalir). Degerler ampirik degil, tur-bazli gerekce ile secildi:
    dialogue/menu sabit UI, orta guven yeterli; tooltip kucuk fontlu ve
    kisa oldugu icin daha yuksek esik gurultuyu eler; subtitle video
    uzerine bindigi icin OCR guveni dusuk gelir, esik en gevsek olan budur.
    """

    max_vertical_gap_ratio: float
    """Gruplama (K11) icin: iki komsu ogenin dikey boslugu, iki ogeden
    kisa olaninin yuksekliginin bu kat SAYISINDAN KUCUKSE, komsu satirlar
    ayni segmente birlestirilebilir (diger kosullarla birlikte). `menu`
    icin `should_group=False` oldugundan bu alan hic okunmaz; yine de
    tutarlilik icin `menu`'nun kisa-oge karakterine uygun mutedil bir
    deger tasir.
    """

    max_group_chars: int
    """Bir grubun (birlesmis metnin) asamayacagi en fazla karakter
    sayisi. Eklenecek bir sonraki oge, mevcut grup metni + 1 (ayirici
    bosluk) + oge metni bu degeri asiyorsa gruplama durur ve yeni bir
    grup baslar. `dialogue` en genis (uzun diyalog kutulari), `tooltip`
    ve `subtitle` daha dar (kisa, oz metin) degerler tasir.
    """

    should_group: bool
    """K11: `dialogue`/`tooltip`/`subtitle` -> `True` (komsu ogeler
    gruplanir); `menu` -> `False` (her oge ayri segment; envanter/menu
    satirlari birbirinden bagimsiz cevrilmelidir)."""


_DIALOGUE: Final[NormalizerParams] = NormalizerParams(
    confidence_threshold=0.60,
    max_vertical_gap_ratio=0.8,
    max_group_chars=280,
    should_group=True,
)

_MENU: Final[NormalizerParams] = NormalizerParams(
    confidence_threshold=0.55,
    max_vertical_gap_ratio=0.5,
    max_group_chars=120,
    should_group=False,
)

_TOOLTIP: Final[NormalizerParams] = NormalizerParams(
    confidence_threshold=0.65,
    max_vertical_gap_ratio=0.3,
    max_group_chars=200,
    should_group=True,
)

_SUBTITLE: Final[NormalizerParams] = NormalizerParams(
    confidence_threshold=0.55,
    max_vertical_gap_ratio=1.0,
    max_group_chars=160,
    should_group=True,
)


def get_params(preset: OcrPreset) -> NormalizerParams:
    """`preset` icin donmuş `NormalizerParams` ornegini dondurur.

    Saf: I/O yok, global mutasyon yok. `OcrPreset` kapali bir `StrEnum`
    oldugu icin `match` her uyeyi kapsar; tanimsiz bir deger (teorik
    olarak baska bir enum turetilirse) `ValueError` ile sinyal edilir --
    sessizce yanlis parametreye dusmek yerine.
    """
    match preset:
        case OcrPreset.DIALOGUE:
            return _DIALOGUE
        case OcrPreset.MENU:
            return _MENU
        case OcrPreset.TOOLTIP:
            return _TOOLTIP
        case OcrPreset.SUBTITLE:
            return _SUBTITLE
        case _:
            raise ValueError(f"bilinmeyen OcrPreset: {preset!r}")
