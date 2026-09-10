"""Suflor -- TextNormalizer: OCR ham bloklarini cevrilmeye hazir Segment'lere
cevirir.

Tasarim dokumani 5.2: "Ceviri kalitesinin yarisi burada belirlenir." OCR iki
satira bolunmus bir cumleyi iki AYRI blok olarak dondurebilir; bunlari iki
ayri cumle olarak cevirirsek sonuc bozuk cikar. Bu modulun tek girisi
`normalize()` alti sorumlulugu SIRAYLA uygular (bkz. fonksiyon docstring'i):
satir birlestirme + hyphen cozumu, guven esigi, gurultu eleme, on ayara gore
gruplama, konusmaci etiketi ayirma, yer tutucu koruma.

Tamamen SAF: I/O yok, global durum yok, rastgelelik yok. Esikler burada
SABIT KODLANMAZ -- hepsi `src/ocr/presets.py`'den (`NormalizerPreset`)
okunur; bu modul yalnizca ALGORITMAYI, presets.py ise SAYISAL DEGERLERI
tutar (gorev paketinin ayrimi).
"""
from __future__ import annotations

import re
from collections.abc import Sequence

from src.contracts.models import OcrPreset, Rect, Segment, TextBlock
from src.ocr.presets import NormalizerPreset, get_preset

__all__ = ["normalize"]


# ---------------------------------------------------------------------------
# gurultu eleme -- tek karakterlik bloklar
# ---------------------------------------------------------------------------

NOISE_ALWAYS_KEEP_SINGLE_CHARS: frozenset[str] = frozenset({"?", "!"})
"""Tek basina anlamli olabilen, alfanumerik OLMAYAN karakterler -- her
zaman KORUNUR. Gerekce: oyunlarda "?" ve "!" karakter basi ustunde tek
basina beliren STANDART tepki/uyari baloncuklaridir (tasarim dokumani 3.2,
"HUD/uyari: Anlik, kaybolan" satirina yakin bir kullanim) -- bunlar
gercek icerik tasir, susleme degildir. Bu kume KASITLI OLARAK KUCUK
tutuldu: baska hicbir tek-karakter noktalama isareti (ornegin '.', '-',
'_', '~', '|', ',', ''', '"') bu listede degildir ve asagidaki kurala
gore ELENIR."""


def _is_noise_single_char(stripped_text: str) -> bool:
    """`stripped_text` (baştaki/sondaki boşluk zaten alınmış) TEK bir
    karakterse VE bu karakter gürültü sayılıyorsa `True`.

    Kural (dil BAGIMSIZ, Python'un Unicode-farkinda `str.isalnum()`'una
    dayanir -- Latin, Kiril, CJK ideogramlari, Hangul hecelerinin HEPSI
    icin `isalnum()` `True` doner, ozel bir dil/alfabe listesi gerekmez):

      1. Uzunluk 1 DEGILSE -> gurultu DEGIL (bu fonksiyon yalnizca TEK
         karakterlik bloklarla ilgilenir; coklu-karakter bloklar farkli
         bir kararla -- confidence/bos-string -- elenir/tutulur).
      2. Karakter `NOISE_ALWAYS_KEEP_SINGLE_CHARS` icindeyse -> KORUNUR
         (gurultu DEGIL), `isalnum()` sonucundan BAGIMSIZ.
      3. `char.isalnum()` `True` ise -> KORUNUR (harf VEYA rakam --
         `I`, `a`, `1`, `力`, `가`, `Я` hepsi burada KORUNUR).
      4. Yukaridakilerin HICBIRI degilse (alfanumerik olmayan VE
         korunacaklar listesinde olmayan tek karakter, ör. '.', '·',
         '_', '~', '|', '`') -> GURULTU sayilir, ELENIR.

    Bu, PAKETIN acikca istedigi ayrimdir: "I, a, 1, ? anlamli olabilir"
    -- ucu de bu kuralla KORUNUR (1-3. maddeler); geri kalan susleme/
    ayrac karakterleri (4. madde) ELENIR.
    """
    if len(stripped_text) != 1:
        return False
    char = stripped_text
    if char in NOISE_ALWAYS_KEEP_SINGLE_CHARS:
        return False
    if char.isalnum():
        return False
    return True


# ---------------------------------------------------------------------------
# satir birlestirme -- geometrik "ayni paragraf" testi
# ---------------------------------------------------------------------------


def _vertical_gap_ok(a: Rect, b: Rect, cfg: NormalizerPreset) -> bool:
    """`a` (onceki, okuma sirasinda) ile `b` (sonraki) arasindaki dikey
    bosluk, `cfg.max_vertical_gap_ratio` / `cfg.max_vertical_overlap_ratio`
    penceresi icinde mi?

    Referans satir yuksekligi `min(a.h, b.h)` -- kucuk olan blok esas
    alinir, boylece buyuk bir blogun yaninda kalan kucuk bir blok, olmasi
    gerekenden fazla "bosluk toleransi" KAZANMAZ.

    GUVENLI SIFIR-BOLME: `min(a.h, b.h) <= 0` (sifir veya negatif
    yukseklikli bbox -- yozlasmis girdi) ise bu fonksiyon HER ZAMAN
    `False` doner (birlesme adayi DEGIL) -- ne istisna, ne NaN/inf.
    Geometrisi tanimsiz olan bir blok, baskasiyla "ayni paragraf"
    sayilamaz; bu, cokmemek icin en guvenli varsayilan davranistir.
    """
    line_height = min(a.h, b.h)
    if line_height <= 0:
        return False
    gap = b.y - a.bottom
    lower_bound = -cfg.max_vertical_overlap_ratio * line_height
    upper_bound = cfg.max_vertical_gap_ratio * line_height
    return lower_bound <= gap <= upper_bound


def _horizontal_overlap_ok(a: Rect, b: Rect, cfg: NormalizerPreset) -> bool:
    """`a` ile `b`'nin yatay kesisim orani (dar kenara gore) esigi
    karsiliyor mu?

    GUVENLI SIFIR-BOLME: `min(a.w, b.w) <= 0` ise `False` doner (bkz.
    `_vertical_gap_ok` ile ayni gerekce -- genisligi olmayan bir blogun
    "ortusme orani" tanimsizdir, guvenli varsayilan: birlesme YOK).
    """
    min_width = min(a.w, b.w)
    if min_width <= 0:
        return False
    overlap = min(a.right, b.right) - max(a.x, b.x)
    if overlap <= 0:
        return False
    return (overlap / min_width) >= cfg.min_horizontal_overlap_ratio


def _should_merge(a: TextBlock, b: TextBlock, cfg: NormalizerPreset) -> bool:
    """`a` ve `b` (okuma sirasinda ARDISIK, `a` once) "ayni paragrafin
    devami" sayilir mi?

    GARANTI (kabul edilen HER `a`, `b`, `cfg` icin -- cokme YOK): saf bir
    bool hesabidir, hicbir zaman istisna firlatmaz (sifir/negatif
    boyutlu bbox dahil -- bkz. `_vertical_gap_ok`/`_horizontal_overlap_ok`).

    Iki sart da (VE ile) saglanmalidir -- gorev paketinin kendi ornegi:
    "dikey bosluk satir yuksekliginin X katindan kucuk VE yatay ortusme
    %Y'den buyukse birlesir".
    """
    return _vertical_gap_ok(a.bbox, b.bbox, cfg) and _horizontal_overlap_ok(
        a.bbox, b.bbox, cfg
    )


# ---------------------------------------------------------------------------
# hyphen / kesme cizgisi cozumu
# ---------------------------------------------------------------------------

HYPHEN_CHARS: frozenset[str] = frozenset({"-", "‐", "‑"})
"""Satir-sonu kesmesi ADAYI sayilan karakterler: ASCII kisa cizgi (U+002D),
Unicode HYPHEN (U+2010), Unicode NON-BREAKING HYPHEN (U+2011). EN-DASH
(U+2013) ve EM-DASH (U+2014) BILINCLI OLARAK DISARIDA -- bunlar neredeyse
HER ZAMAN gercek noktalama tiresidir (cumle arasi kesme), kelime bolme
kurali icin aday DEGILDIR."""


def _join_texts(left: str, right: str) -> str:
    """Iki (zaten `.strip()` edilmis) blok metnini, satir-sonu hyphen
    sezgiseline gore birlestirir.

    KURAL: `left`, `HYPHEN_CHARS` icinde bir karakterle bitiyorsa VE bu
    karakterden hemen ONCEKI karakter bir HARFSE (`str.isalpha()`) VE
    `right` bos degilse VE `right`'in ILK karakteri KUCUK harfse
    (`str.islower()`) -> "satir-sonu kesmesi" sayilir: tire SILINIR,
    iki metin BOSLUKSUZ birlestirilir (`left[:-1] + right`).
    AKSI HALDE (tire yok, veya tireden once harf yok, veya `right` bos/
    kucuk-harfle baslamiyor) -> iki metin TEK BOSLUKLA birlestirilir,
    varsa tire OLDUGU GIBI KALIR (silinmez).

    GARANTI EDILEN ALAN (bu fonksiyonun KABUL ETTIGI HER `left`, `right`
    dizesi icin, hicbir on kosul YOK -- bos dize dahil KOSULSUZ):
      * Cokme/istisna YOK (bos `left`/`right`, tek karakterli `left` dahil
        -- `left[-2]` erisiminden once `len(left) >= 2` KONTROL EDILIR).
      * `left`'in SONUNDAKI hyphen DISINDA hicbir karakter DEGISTIRILMEZ
        veya SILINMEZ -- ozellikle `left`'in ORTASINDAKI bir tire (ör.
        tek blok icinde geçen "well-known") bu fonksiyona hic
        UGRAMAZ (yalnizca birlesme NOKTASINDAKI son karakter incelenir).

    GARANTI EDILMEYEN (SINIRLI) ALAN -- KRITIK, T-004 gorev paketinin
    "well-known / keli-me" ornegi tam olarak burasi: bu kural DILBILIMSEL
    DEGIL, salt YUZEYSEL bir sezgiseldir (tire + kucuk-harf-devam). Gercek
    bir BILESIK KELIME tiresi (ör. "well-") tesaduf eseri SATIR SONUNA
    denk gelir VE bir sonraki satir kucuk harfle baslarsa (ör. "known"),
    bu fonksiyon onu da "kesme" sanip SILER -> "wellknown" (YANLIS).
    Sozluk veya dil modeli olmadan bu iki durum ("kelime bolme" vs
    "satir sonuna denk gelen bilesik kelime tiresi") YUZEYSEL OLARAK
    AYIRT EDILEMEZ -- bu, sessizce gizlenmis bir varsayim DEGIL, acikca
    burada ve delivery.md `known_gaps` altinda belgelenmis bir SINIRDIR.
    Buyuk/harfsiz-script (CJK, vb.) devam metinlerinde `str.islower()`
    scriptin case ayrimi olmadigi icin HER ZAMAN `False` doner -> bu
    bransta hicbir zaman tetiklenmez, tire (varsa) her zaman KORUNUR ve
    bosluklu birlesme uygulanir (CJK'da satir-sonu tire-bolme YOK zaten
    bir yazim gelenegi degildir).
    """
    if not left:
        return right
    if not right:
        return left
    ends_with_hyphen = (
        left[-1] in HYPHEN_CHARS and len(left) >= 2 and left[-2].isalpha()
    )
    starts_lowercase = right[0].islower()
    if ends_with_hyphen and starts_lowercase:
        return left[:-1] + right
    return f"{left} {right}"


# ---------------------------------------------------------------------------
# konusmaci etiketi
# ---------------------------------------------------------------------------

_SPEAKER_LABEL_MAX_TOKENS = 3
_SPEAKER_LABEL_MAX_TOKEN_CHARS = 24

_SPEAKER_PATTERN = re.compile(
    r"^(?P<label>[^\s:：]{1,"
    + str(_SPEAKER_LABEL_MAX_TOKEN_CHARS)
    + r"}(?:[ \t][^\s:：]{1,"
    + str(_SPEAKER_LABEL_MAX_TOKEN_CHARS)
    + r"}){0,"
    + str(_SPEAKER_LABEL_MAX_TOKENS - 1)
    + r"})[:：][ \t]*(?P<body>\S.*)$",
    re.DOTALL,
)
"""Tanınan desen: satır başında EN FAZLA 3 boşlukla-ayrılmış "kelime"
(her biri en fazla 24 karakter, kendi içinde boşluk/':'/'：' YOK), ardından
ASCII iki nokta (`:`) VEYA tam-genişlik iki nokta (`：` -- CJK metinlerde
yaygın), ardından İSTEĞE BAĞLI yatay boşluk, ardından EN AZ bir boşluk-dışı
karakterle başlayan gövde metni."""


def _extract_speaker(text: str) -> tuple[str | None, str]:
    """`text`'in basinda bir "konusmaci etiketi" (`Ad:` / `Ad：`) var mi?

    TANINAN durumda: `(etiket, geri_kalan_govde)` doner, `text`'ten
    etiket VE ayirici KESILMIS olur.

    TANINMAYAN durumda -- asagidaki HERHANGI biri gecerliyse -- `(None,
    text)` doner, yani `text` OLDUGU GIBI, HICBIR KARAKTERI DEGISMEDEN
    kalir:
      * Satirda hic ':' veya '：' yok, VEYA ilk ':'/'：'den once
        `_SPEAKER_LABEL_MAX_TOKENS` (3) kelimeden fazla / bir kelime
        `_SPEAKER_LABEL_MAX_TOKEN_CHARS` (24) karakterden uzun (ör. "The
        rules of engagement are as follows: ..." -- bu bir konusma
        cumlesi, isim degildir).
      * Etiket TAMAMEN rakamlardan olusuyor (ör. saat "12:30", oran
        "3:1") -- en az bir HARF icermeyen etiket asla konusmaci
        SAYILMAZ (`any(ch.isalpha() ...)` kontrolu).
      * ':'/'：'den sonra hicbir sey yok veya yalnizca bosluk var (ör.
        "Not:" tek basina) -- gövde EN AZ bir bosluk-disi karakterle
        BASLAMALI.

    Bu fonksiyon KASITLI OLARAK MUHAFAZAKARDIR: yanlis-pozitif (asiri
    esleme, gercek olmayan bir "konusmaci" uydurma) riskini, yanlis-
    negatif (gercek bir etiketi kacirma) riskine TERCIH EDER -- cunku
    yanlis-pozitif, cevrilecek METNI BOZAR (govdeden gercek bir kelime
    kopar), yanlis-negatif ise sadece etiketi ayri alanina COKEMEMEK
    demektir (metin BUTUNLUGU bozulmaz).
    """
    match = _SPEAKER_PATTERN.match(text)
    if match is None:
        return None, text
    label = match.group("label")
    if not any(ch.isalpha() for ch in label):
        return None, text
    return label, match.group("body")


# ---------------------------------------------------------------------------
# yer tutucu koruma
# ---------------------------------------------------------------------------

_PLACEHOLDER_PATTERN = re.compile(
    r"\{[^{}]*\}"  # 1) .NET/JSON tarzi: {0}, {playerName}, {}
    r"|<[^<>]+>"  # 2) XML/HTML tarzi bicim/renk etiketi: <color=red>, </b>
    r"|\[[^\[\]]+\]"  # 3) BBCode tarzi etiket: [color=red], [b], [/b]
    r"|%(?:\d+\$)?[-+0 #]*\d*(?:\.\d+)?[sdfxXoeEgGc%]"  # 4) printf: %s %d %.2f %1$s %%
    r"|\b\d+(?:[.,]\d+)?%"  # 5) yuzde degeri: 50%, 12.5%
    r"|\b\d+(?:[.,]\d+)?\b"  # 6) duz sayi: 50, 12.5, 3
)
"""Kapsanan desenler (paket: "Hangi desenleri kapsadığını listele"):

  1. `{...}`         -- .NET/ICU tarzi degisken yer tutucu
  2. `<...>`          -- XML/HTML/Unity zengin-metin bicim-renk etiketi
  3. `[...]`          -- BBCode tarzi bicim-renk etiketi
  4. printf bicimi    -- `%s`, `%d`, `%.2f`, `%1$s`, `%%`
  5. yuzde degeri     -- `50%`, `12.5%` (sayidan SONRA yuzde isareti)
  6. duz sayi         -- `50`, `12.5`, `3` (`\\b` sinirlariyla -- "L33T"
                          gibi harf-rakam karisimi bir kimlik icindeki
                          rakamlar YAKALANMAZ, cunku iki rakam arasinda
                          veya bir harfle bir rakam arasinda Unicode kelime
                          siniri YOKTUR)

  Alternatifler bu SIRAYLA denenir ve `re.finditer` CAKISMAYAN eslesmeler
  uretir -- ornegin "50%" butunuyle 5. alternatifle eslenir, 6.
  alternatif (duz sayi) o araligi bir daha DENEMEZ (cakisma yok, cift
  sayim yok).

  KAPSAM DISI (bilincli, dokumante): Turkce yazim gelenegindeki
  "yuzde-once" bicimi (`%20`, sayidan ONCE isaret) ayri bir desen
  DEGILDIR -- bu modul OCR KAYNAK metnini isler (cevrilecek dil, HEDEF
  Turkce degil bu asamada), bu yuzden kapsam disi birakildi. `%20`
  gorulurse `%` yakalanmaz, yalniz "20" 6. alternatifle (duz sayi)
  yakalanir -- metin YINE DE degismedigi icin bu bir veri kaybi DEGIL,
  yalnizca `placeholders` listesinde '%' isaretinin sayiya "yapisik"
  gorunmemesi anlamina gelir."""


def _extract_placeholders(text: str) -> tuple[str, ...]:
    """`text` icindeki korunacak alt-dizeleri, GORULME SIRASINA gore,
    OLDUKLARI GIBI (degistirilmeden) toplar.

    GARANTI: donen tuple'daki HER dize, `text` icinde TAM OLARAK (aynen)
    bir alt-dize olarak BULUNUR -- bu fonksiyon `text`'i asla DEGISTIRMEZ,
    yalnizca OKUR; `normalize()` de cagirdiktan sonra segment metnini bu
    ayiklamaya gore DEGISTIRMEZ (bkz. modul docstring'i, adim 6)."""
    return tuple(m.group(0) for m in _PLACEHOLDER_PATTERN.finditer(text))


# ---------------------------------------------------------------------------
# bbox birlesimi
# ---------------------------------------------------------------------------


def _union_bbox(rects: Sequence[Rect]) -> Rect:
    """`rects` dizisini kapsayan EN KUCUK dikdortgeni doner.

    `monitor_index`/`dpi_scale`, dizideki ILK elemandan alinir -- bu
    modulun tum kullanim alaninda (tek bir OCR karesinden gelen bloklar)
    grup icindeki TUM bloklarin AYNI monitorden/AYNI dpi_scale'den
    geldigi varsayilir (tek capture/OCR gecisi); bu varsayim, TextBlock
    sozlesmesinin kendisinde ZORLANMAZ, burada da DOGRULANMAZ -- yalnizca
    en makul varsayilan olarak KULLANILIR."""
    first = rects[0]
    left = min(r.x for r in rects)
    top = min(r.y for r in rects)
    right = max(r.right for r in rects)
    bottom = max(r.bottom for r in rects)
    return Rect(
        x=left,
        y=top,
        w=right - left,
        h=bottom - top,
        monitor_index=first.monitor_index,
        dpi_scale=first.dpi_scale,
    )


# ---------------------------------------------------------------------------
# ana giris noktasi
# ---------------------------------------------------------------------------


def normalize(blocks: Sequence[TextBlock], preset: OcrPreset) -> list[Segment]:
    """OCR ham bloklarini cevrilmeye hazir `Segment`'lere donusturur.

    Tasarim dokumani 5.2: "Ceviri kalitesinin yarisi burada belirlenir."
    Adimlar SIRAYLA uygulanir:

      1. Bos (yalnizca bosluk) / guven-esigi-alti / tek-karakter-gurultu
         bloklari ELE (bkz. `_is_noise_single_char`,
         `NormalizerPreset.confidence_threshold`).
      2. Kalan bloklari OKUMA SIRASINA sok: `(bbox.y, bbox.x)` artan --
         bkz. asagida "Okuma sirasi varsayimi", SINIRLI bir varsayimdir.
      3. Ardisik bloklari, `preset.line_grouping_enabled` acikken,
         geometrik teste gore (bkz. `_should_merge`) ZINCIRLEME GRUPLA:
         A-B birlesirse VE B-C birlesirse, A-B-C TEK segment olur (gecisli
         zincir; A-C dogrudan test EDILMEZ). `line_grouping_enabled`
         kapaliyken (yalnizca `menu`) HER blok kendi tek-elemanli grubunu
         olusturur.
      4. Grup icindeki (baştan/sondan boşluğu alınmış) metinleri hyphen-
         farkinda BIRLESTIR (bkz. `_join_texts` -- SINIRLI GARANTI, kendi
         docstring'inde detaylandirilir).
      5. Birlesmis metnin basindan konusmaci etiketini AYIR -- YALNIZCA
         `preset.speaker_label_enabled` acikken (bkz. `_extract_speaker`).
      6. Kalan gövde metninden yer tutuculari CIKAR (bkz.
         `_extract_placeholders`) -- metni DEGISTIRMEDEN, yalnizca
         `Segment.placeholders` alanina LISTELER.

    GARANTILER -- bu fonksiyonun KABUL ETTIGI HER girdi icin (yani `blocks:
    Sequence[TextBlock]` ve `preset: OcrPreset` tur sozlesmesine uyan HER
    girdi icin -- bu fonksiyon hicbir ValueError/ozel istisna firlatmaz,
    dolayisiyla "kabul edilen alan" tur sistemiyle AYNI genisliktedir):

      * COKME YOK. Bos liste, tek blok, hepsi esik alti, sifir/negatif
        boyutlu bbox (`w<=0` veya `h<=0`) dahil HICBIR girdi istisna
        firlatmaz; en kotu durumda `[]` doner.
      * DETERMINIZM: ayni `blocks` + ayni `preset` -> HER ZAMAN bitebir
        ayni cikti (yalnizca stdlib/salt hesap; I/O yok, rastgelelik yok,
        global/mutable durum yok, girdi `blocks` MUTATE EDILMEZ).
      * `source_blocks`: her `Segment.source_blocks`, o segmenti ureten
        bloklarin `blocks` icindeki ORIJINAL indeksini (0-tabanli, girdi
        sirasina gore, ARTAN) tasir. ELENEN bloklarin indeksi HICBIR
        segmentte GORUNMEZ; TUM dönen `source_blocks` degerlerinin
        BIRLESIMI, `blocks`'un elenmemis alt-kumesinin indeksleriyle
        TAM ORTUSUR (ne eksik ne fazla).
      * `segment.text` BOS STRING OLAMAZ (bos/yalnizca-bosluk metin
        ureten bloklar zaten 1. adimda elenir; bu yuzden hicbir grup bos
        metinle SONUCLANAMAZ -- grup en az bir NON-EMPTY bloktan olusur).
      * `segment.placeholders` icindeki HER dize, `segment.text` icinde
        TAM OLARAK bir alt-dize olarak BULUNUR (adim 6 metni degistirmez).
      * `segment.bbox`, o segmenti ureten TUM kaynak bloklarin bbox'larini
        KAPSAYAN dikdortgendir (bkz. `_union_bbox`).

    GARANTI EDILMEYEN / ACIKCA SINIRLI ALANLI DAVRANISLAR ("genelde
    calisir" DEGIL -- ya kapsam yazilir ya iddia edilmez, T-004 gorev
    paketinin ZORUNLU kuralı):

      * Okuma sirasi varsayimi (adim 2): `(y, x)` artana gore siralama,
        SOLDAN-SAGA / YUKARIDAN-ASAGIYA (Latin, Kiril, CJK YATAY-satir)
        okuma yonunu varsayar. SAGDAN-SOLA yazi sistemleri (Arapca,
        Ibranice) veya DIKEY CJK sutun yazisi icin bu siralama YANLIS
        gruplamaya yol ACABILIR -- bu modul bu iki yazim yonunu
        DESTEKLEMEZ (kapsam disi, bkz. delivery.md `known_gaps`).
      * Hyphen ayrimi (adim 4): bkz. `_join_texts` docstring'i -- gercek
        bilesik-kelime tiresi satir sonuna denk gelirse (ör.
        "well-\\nknown") bu sezgisel YANLISLIKLA kaldirabilir; sozluk
        olmadan bu durum GEOMETRIDEN AYIRT EDILEMEZ.
      * Konusmaci etiketi (adim 5): yalnizca `_SPEAKER_PATTERN`'e uyan
        satir-basi `Ad:`/`Ad：` deseni TANINIR; TANINMAYAN her durumda
        (desen uymaz, etiket salt rakam, ikinokta sonrasi bos)
        `speaker=None` doner ve metin OLDUGU GIBI kalir -- EKSIK-esleme
        yonunde MUHAFAZAKAR, asiri-esleme YAPMAZ (bkz. `_extract_speaker`
        docstring'i, "HP: 100" / "Damage: 10-15" ornekleri).
      * Yer tutucu deseni (adim 6): yalnizca `_PLACEHOLDER_PATTERN`'in
        listeledigi 6 desen kapsanir (bkz. o sabitin docstring'i); baska
        bicimler (ornegin Turkce "%20" yuzde-once yazimi) YAKALANMAZ --
        metin yine de BOZULMAZ, yalnizca o alt-dize `placeholders`
        listesine GIRMEZ.

    Args:
        blocks: OCR motorunun dondurdugu ham bloklar (herhangi bir sirada
            olabilir -- bu fonksiyon kendi ic okuma-sirasi siralamasini
            yapar, `blocks`'un KENDISI mutate EDILMEZ).
        preset: hangi `NormalizerPreset`'in (bkz. `src/ocr/presets.py`)
            kullanilacagini belirler.

    Returns:
        Okuma sirasina gore siralanmis, sifir veya daha fazla `Segment`.
    """
    cfg = get_preset(preset)

    kept: list[tuple[int, TextBlock]] = []
    for index, current_block in enumerate(blocks):
        stripped = current_block.text.strip()
        if not stripped:
            continue
        if current_block.confidence < cfg.confidence_threshold:
            continue
        if _is_noise_single_char(stripped):
            continue
        kept.append((index, current_block))

    if not kept:
        return []

    kept.sort(key=lambda pair: (pair[1].bbox.y, pair[1].bbox.x))

    groups: list[list[tuple[int, TextBlock]]] = []
    current_group: list[tuple[int, TextBlock]] = [kept[0]]
    for prev_pair, next_pair in zip(kept, kept[1:]):
        _, prev_block = prev_pair
        _, next_block = next_pair
        if cfg.line_grouping_enabled and _should_merge(prev_block, next_block, cfg):
            current_group.append(next_pair)
        else:
            groups.append(current_group)
            current_group = [next_pair]
    groups.append(current_group)

    segments: list[Segment] = []
    for group in groups:
        source_indices = tuple(index for index, _ in group)
        block_texts = [b.text.strip() for _, b in group]
        merged_text = block_texts[0]
        for next_text in block_texts[1:]:
            merged_text = _join_texts(merged_text, next_text)

        if cfg.speaker_label_enabled:
            speaker, body = _extract_speaker(merged_text)
        else:
            speaker, body = None, merged_text

        placeholders = _extract_placeholders(body)
        bbox = _union_bbox([b.bbox for _, b in group])

        segments.append(
            Segment(
                text=body,
                bbox=bbox,
                speaker=speaker,
                placeholders=placeholders,
                source_blocks=source_indices,
            )
        )

    return segments
