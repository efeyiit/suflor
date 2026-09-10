"""Suflor -- TextNormalizer on ayar parametreleri (esikler, gruplama bayraklari).

Tasarim dokumani 5.2 ve 3.2, gorev paketi T-004. Bu modul, `normalizer.py`
icindeki ALGORITMANIN kendisini degil, o algoritmanin dort `OcrPreset`
uyesi (`dialogue`, `menu`, `tooltip`, `subtitle`) icin aldigi SAYISAL
esikleri ve acik/kapali BAYRAKLARI tutar. Gorev paketinin acik talimati:
"Esiklerini presets.py icinde adlandirilmis sabit yap, docstring'de
gerekcelendir" -- asagidaki her alan ve her preset ornegi bunu yapar.

Bu modul TAMAMEN saftir: fonksiyon disi hicbir yan etki yok, sadece
donmus (`frozen=True`) veri.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.contracts.models import OcrPreset

__all__ = ["NormalizerPreset", "get_preset", "PRESETS"]


@dataclass(frozen=True)
class NormalizerPreset:
    """Bir `OcrPreset` uyesi icin normalizasyon esikleri ve bayraklari.

    Butun alanlar `src/ocr/normalizer.py` tarafindan salt okunur tuketilir;
    bu esikler baska HICBIR yerde sabit kodlanmaz -- degistirmek isteyen
    yalnizca bu dosyayi degistirir.
    """

    confidence_threshold: float
    """`TextBlock.confidence` bu degerin KESIN OLARAK ALTINDA (`<`, esitlik
    DAHIL DEGIL) olan bloklar dusurulur. Yani `confidence == esik` olan bir
    blok KORUNUR -- esik bir "asagi yuvarlama sinirini" degil, disari
    birakilan acik alt siniri belirtir."""

    line_grouping_enabled: bool
    """`False` ise (yalnizca `menu`) hicbir blok baska bir blokla
    BIRLESTIRILMEZ -- gorev paketi: "menu: gruplama yok, her oge ayri
    segment". `True` ise asagidaki UC geometrik esik, ardisik (okuma
    sirasina sokulmus) blok CIFTLERINE uygulanir; ucu de (VE ile) birden
    saglanmalidir (bkz. `normalizer._should_merge`)."""

    max_vertical_gap_ratio: float
    """Ardisik iki blok arasindaki DIKEY BOSLUK (`sonraki.y -
    onceki.bottom`), `min(onceki.h, sonraki.h) * bu deger` degerinden
    KUCUK YA DA ESIT ise "ayni paragrafin devami" adayidir. Ornek: deger
    1.5 ve iki blok da 30 piksel yuksekliginde ise, aralarinda EN FAZLA 45
    piksel bosluk olan bloklar birlesme adayidir. `line_grouping_enabled
    = False` oldugunda bu alan hic OKUNMAZ (kullanilmaz)."""

    max_vertical_overlap_ratio: float
    """Iki blok DIKEYDE en fazla `min(onceki.h, sonraki.h) * bu deger`
    kadar ORTUSEBILIR (yani `sonraki.y - onceki.bottom` EN FAZLA bu kadar
    NEGATIF olabilir) ve yine birlesme adayi sayilir -- OCR kutusunun
    piksel duzeyinde tasmasina/eksik olcmesine tolerans. Bunun USTUNDE bir
    dikey ortusme (ör. ayni satirda yan yana duran iki sutun, ya da iki
    ayri satirin degil iki ayri SUTUNUN blogu) birlesmeyi REDDEDER.
    `line_grouping_enabled = False` oldugunda okunmaz."""

    min_horizontal_overlap_ratio: float
    """Iki blogun yatay KESISIM genisligi, `min(onceki.w, sonraki.w)`
    degerinin EN AZ bu orani kadar olmalidir (birlesmenin IKINCI sarti;
    dikey testle VE ile birlesir). Bu, ayni sutunda ust uste duran satirlari
    (yuksek ortusme) yan yana duran alakasiz bloklardan (dusuk/sifir
    ortusme) ayirir. `line_grouping_enabled = False` oldugunda okunmaz."""

    speaker_label_enabled: bool
    """`True` ise birlesmis segment metninin BASINDA `Ad:` / `Ad：` deseni
    aranir ve `Segment.speaker`'a ayrilir (bkz.
    `normalizer._extract_speaker`). `menu` ve `tooltip` icin BILINCLI
    OLARAK `False`: bu iki tur metinde "Etiket: deger" bicimi cok yaygin
    (`HP: 100`, `Damage: 10-15`, `Sure: 30sn`) ve bu, konusmaci etiketiyle
    YUZEYSEL OLARAK AYIRT EDILEMEZ -- acarsak "HP" veya "Damage" yanlislikla
    konusmaci sanilir ve deger kismindan kopar. Kapali tutmak EKSIK
    (bazi gercek konusmaci etiketleri menu/tooltip'te kacirilabilir, ama
    bu iki turde zaten cok nadir) ama GUVENLI taraftir."""


# ---------------------------------------------------------------------------
# ön ayarlar -- her biri, tasarim dokumani 3.2'deki tur tarifine dayanir
# ---------------------------------------------------------------------------

DIALOGUE_PRESET = NormalizerPreset(
    # Diyalog kutusu genelde net render edilir ama karakter isim etiketi
    # ve stilize/gölgeli fontlar güveni düşürebilir; orta-tolerant esik.
    confidence_threshold=0.45,
    line_grouping_enabled=True,
    # Gorev paketinin kendi ornegi ("dikey bosluk satir yuksekliginin 1.5
    # katindan kucukse... yatay ortusme %60'tan buyukse birlesir") BIREBIR
    # burada kullanildi -- dialogue, paket ornegine denk gelen kanonik
    # preset.
    max_vertical_gap_ratio=1.5,
    max_vertical_overlap_ratio=0.3,
    min_horizontal_overlap_ratio=0.6,
    # "isim etiketi ayri bolge olarak izlenmeli" (tasarim 3.2) -- ayri
    # bolge TAKIP etmek pipeline/capture katmaninin isi; bu modul, ayni
    # blok icine sizmis "Ad:" onekini AYIKLAMAKLA sorumlu.
    speaker_label_enabled=True,
)

MENU_PRESET = NormalizerPreset(
    # Menu/envanter fontu genelde kucuk ama temiz/vektorel render edilir;
    # kisa dizeler oldugu icin bir tek yanlis karakter butun ogeyi bozar --
    # bu yuzden diger preset'lerden daha SIKI (yuksek) esik.
    confidence_threshold=0.55,
    # Tasarim dokumani 3.2 ve gorev paketi acikca: "menu: gruplama yok ->
    # her oge ayri segment". Asagidaki uc oran alani bu yuzden HIC
    # OKUNMAZ; degerler yalnizca "bu preset'te sifir tolerans" niyetini
    # gorunur kilmak icin 0.0/1.0 (en siki) birakildi.
    line_grouping_enabled=False,
    max_vertical_gap_ratio=0.0,
    max_vertical_overlap_ratio=0.0,
    min_horizontal_overlap_ratio=1.0,
    # bkz. NormalizerPreset.speaker_label_enabled dokumantasyonu:
    # "HP: 100" gibi istatistik satirlarini konusmaci sanmamak icin kapali.
    speaker_label_enabled=False,
)

TOOLTIP_PRESET = NormalizerPreset(
    # Tooltip metni kucuk punto ve yogun oldugu icin OCR hata orani daha
    # yuksektir; icerik butunlugu (eksik kelime kaybetmemek) burada
    # dogruluktan daha kritik -- diger preset'lerden daha TOLERANSLI esik.
    confidence_threshold=0.40,
    line_grouping_enabled=True,
    # Tooltip satir araligi (leading) genelde dar -- dialogue'a gore daha
    # siki bir dikey bosluk siniri.
    max_vertical_gap_ratio=1.3,
    max_vertical_overlap_ratio=0.3,
    # Sola-hizali uzun aciklama metninde satirlar farkli uzunlukta olur
    # (ozellikle paragrafin son satiri kisadir); yatay ortusme oranini
    # (kisa kenara gore) dusuk tutmak bu dogal degisimi tolere eder.
    min_horizontal_overlap_ratio=0.3,
    speaker_label_enabled=False,  # bkz. yukarida "Damage: 10-15" gerekcesi
)

SUBTITLE_PRESET = NormalizerPreset(
    # Altyazi fontu genelde okunurluk icin dis-hat/golge tasir; bu OCR
    # guvenini hafifce dusurur ama menu kadar temiz degildir -- orta esik.
    confidence_threshold=0.50,
    line_grouping_enabled=True,
    # Altyazilar genelde 1-2 satir ve okunurluk icin biraz daha genis
    # satir araligi kullanir.
    max_vertical_gap_ratio=1.6,
    max_vertical_overlap_ratio=0.3,
    # Merkeze hizali kisa satirlar: metrik (kesisim / dar-kenar) hizalama
    # bicimden bagimsizdir (kisa satir uzun satirin ic sinirlarinda
    # kaldigi surece oran hala yuksek cikar); tooltip'le ayni deger.
    min_horizontal_overlap_ratio=0.3,
    # Sinematik altyazilarda "AD: replik" bicimi gorulebilir (tasarim 3.2,
    # "Diyalog kutusu" satiriyla ayni gerekce).
    speaker_label_enabled=True,
)

PRESETS: dict[OcrPreset, NormalizerPreset] = {
    OcrPreset.DIALOGUE: DIALOGUE_PRESET,
    OcrPreset.MENU: MENU_PRESET,
    OcrPreset.TOOLTIP: TOOLTIP_PRESET,
    OcrPreset.SUBTITLE: SUBTITLE_PRESET,
}
"""`OcrPreset`'in DORT uyesinin TAMAMINI kapsar (`get_preset` bunu varsayar)."""


def get_preset(preset: OcrPreset) -> NormalizerPreset:
    """`preset` icin `NormalizerPreset` degerlerini dondurur.

    `OcrPreset` kapali bir `StrEnum` (dort uye) oldugu VE `PRESETS`
    dordunu de kapsadigi icin bu fonksiyon KABUL ETTIGI HER `OcrPreset`
    degeri icin bir sonuc doner -- KeyError firlatma olasiligi yoktur.
    """
    return PRESETS[preset]
