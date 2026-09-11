"""Suflor -- satir birlestirici (`satirlari_birlestir`), T-008.

Ayni satirdaki yatay komsu OCR kutularini tek `TextBlock`'a birlestirir.
Pipeline'da `normalize`'dan HEMEN ONCE, BIR KEZ cagrilir. Neden var
(olgular S1-S3): Korece tespit modeli KELIME kutusu verir (dlg_KR: 17
kutu, 4 satir); normalizer yatayda birlestirmez (T-004 K11 "yatay
ortusme" DIKEY gruplamanin on kosuludur, ayni satirdaki kelimeler yatayda
ortusmez) -> 16 segment -> kelime kelime ceviri. Satir-duzeyi girdide
(JP/EN: 4 kutu, 1 kutu/satir) ETKISIZDIR (birebir gecer).

Bu docstring, gorev paketindeki (T-008 packet.md surum 2) K1-K8
kararlarinin bu modulde nasil uygulandigini belgeler. Her kararin yaninda
onu olcen test adi vardir (`tests/unit/ocr/test_satir_birlestirici.py`)
ya da `[ÖLÇÜLMÜYOR]` damgasi. Tester `known_gaps`i OKUMAZ; garanti alani
burasidir.

Yapi
-----
Saf fonksiyon `satirlari_birlestir(blocks) -> list[TextBlock]` + iki
modul sabiti `DIKEY_ORTUSME_ESIGI = 0.5`, `YATAY_BOSLUK_ESIGI = 0.75`.
Ic yardimcilar: `_yozlasmis`, `_dikey_ortusme_yeterli`, `_yatay_komsu`,
`_satirlara_bol`, `_gruplara_bol`, `_grubu_birlestir`,
`_metinleri_birlestir`, `_betik_cjk_mi`. Yalniz stdlib (`math`,
`unicodedata`) ve `src.contracts.models` (MUTLAK import; `src/__init__.py`
yoktur). Kardes modul import edilmez.

## K1 -- saf ve deterministik; 1000 blok < 50 ms

I/O yok, global durum yok, modul duzeyi mutable yok (`__all__` demet),
rastgelelik/zaman yok. Girdi dizisi ve `TextBlock`'lar DEGISTIRILMEZ
(frozen; ic islemler yeni listeler kurar). Ayni girdi -> esit cikti.
Karmasiklik: `O(n log n)` (uc siralama + dogrusal gecisler); 1000 blok
bu makinede ~3 ms. Olcu: `test_k1_*`; `real_check.py` #5 (saflik AST)
ve #6 (1000 blok medyan < 50 ms).

## K2 -- ayni satir ve komsuluk geometriyle

DEGISMEZ (paketle ayni): iki kutu ayni satirdadir <=> dikey ortusmeleri
`>= DIKEY_ORTUSME_ESIGI * min(h)`; ayni satirda komsudur <=> `x`
ilerliyor VE bosluk `<= YATAY_BOSLUK_ESIGI * min(h)`. Esikler HER ZAMAN
iki OZGUN kutunun yuksekligiyle hesaplanir, birlesik yukseklikle DEGIL
(KRT Y2: birlesik `h` buyuyunce daha once komsu olmayan kutu komsu
oluyordu). Karsilastirmalar CARPMA ile (`bosluk <= oran * h`), bolme
yok. Farkli `monitor_index` ASLA birlesmez; farkli `dpi_scale` de
birlesmez (KARAR, paket sessizdi: normalizer K10 `_union_rect` farkli
`dpi_scale`'i `ValueError` ile reddeder, burada sessiz kopyalama olmasin
diye birlestirme yuzeyi `(monitor_index, dpi_scale)` ile bolunur -- K5'in
"ilk parcadan" cumlesi boylece her zaman dogru kalir). `h <= 0` ya da
`w <= 0` (sifir VE negatif) kutu HICBIR SEYLE birlesmez, bolumlemeye hic
girmez ve okuma sirasinda AYNEN (ayni nesne) gecer -- araya girdigi iki
komsuyu da AYIRMAZ. `x ilerliyor` = `aday.x > son.x` (KESIN buyuk): ayni
`x`'teki ikinci kutu (cift tespit) yeni grup acar; `x` ilerleyen ic ice
kutu ise BIRLESIR ve metin cogalir (S6'nin "yapisal olarak imkansiz"
cumlesi GERI CEKILDI -- bilinen sinir, `test_k2_ic_ice_*` ile
SABITLENDI). Satir gecisi (satir sonu -> sonraki satirin basi) cogunlukla
negatiftir ama her zaman degil; uzun kutu koprusu icin bkz. asagida
"grup icinde dikey referans".

ALGORITMA -- ITIRAZ (paket v2 K2'nin lafzindan sapma, olculdu):
Paket "girdi `(y, x, idx)` ile siralanir; TEK GECIS: her blok acik grubun
ILK bloguyla dikey ortusuyor VE SON bloguna gore `x` ilerliyor VE bosluk
esik altindaysa gruba eklenir, aksi halde yeni grup" der. Bu lafiz gercek
KR geometrisinde 17 -> 9 verir, 4 degil (`evidence/olcum-1-k2-lafzi-vs-
uygulama-gercek-ocr.txt`; birim izi `test_itiraz_paket_lafzi_*`): ayni
satirdaki kelime kutularinin `y`'si 1-4 px titrer (satir 3: 212/209/209/
208/210), `(y, x)` sirasi kelimeleri x=386,225,305,467,82 dizer, `x
ilerliyor` kosulu satiri parcalar. Paketin dayandigi "`(y,x)` sirasi =
satir ici x sirasi" varsayimi gercek OCR'da tutmaz. Uygulama, AYNI
degismezleri su yapiyla gerceklestirir (hepsi `O(n log n)`):

  1. `(y, x, idx)` ile sirala (T-004 K28 okuma sirasi; `idx` = girdi
     indeksi, `(y,x)` baglarini cozer -- K6).
  2. Yozlasmis kutulari ayir (aynen gecerler). Kalanlari
     `(monitor_index, dpi_scale)` yuzeylerine ayir.
  3. SATIR BOLUMLEME (yuzey basina, tek gecis): blok, acik satirin ILK
     bloguyla dikey ortusuyorsa (`>= 0.5 * min(h_ilk, h_blok)`) satira
     eklenir; aksi halde yeni satir acilir. Uyelik SATIRIN ILK BLOGUYLA
     olculur, bir oncekiyle degil: merdiven (her kutu bir oncekiyle
     ortusur, ilkiyle ortusmez) tek satir DEGILDIR
     (`test_k2_satir_bolumleme_satirin_ilk_bloguna_gore`).
  4. Satir icinde `(x, y, idx)` ile sirala; tek gecis: blok, acik grubun
     ILK bloguyla dikey ortusuyor (`>= 0.5 * min(h)`) VE grubun SON
     bloguna gore `x` ilerliyor VE bosluk `<= 0.75 * min(h_son, h_blok)`
     ise gruba eklenir; aksi halde yeni grup. Grup son bloga gore
     ilerledigi icin komsuluk GECISLIDIR (A-B, B-C komsu, A-C degil ->
     tek blok; `test_k2_zincir_gecisli_tek_blok`).
  5. Her grup tek `TextBlock` (K5); cikti `(y, x, en kucuk girdi
     indeksi)` ile siralanir (K6).

Grup icinde dikey referans: adim 4'te dikey ortusme GRUBUN ilk bloguyla
olculur (paketin lafzi). Uzun kutu koprusu T(60,0,40,60) a(0,5,50,20)
c(110,40,50,20): ucu ayni satirda (T referans), x sirasinda a-T
birlesir, c grubun ilk blogu a ile ortusmez (-15) -> ayri
(`test_k2_grup_icinde_dikey_ortusme_grubun_ilk_bloguyla`). Cok satiri
tek kutuda veren bir tespit yine de o satirlari ayni SATIRA toplayabilir
(adim 3) -- ciktinin gruplari bu durumda kutu geometrisine bagli,
`[ÖLÇÜLMÜYOR]` gercek OCR'da (fixture yok).

Esik 0.75 (KRT Y3): KR kelime boslugu en cok `0.57 x h` (S6), gercek
1-em bosluk sinifi `0.78-1.14 x h` (kendi olcumum, `evidence/olcum-2-*`:
JP ideografik-bosluklu secim satiri 1.03, JP 1-em 1.14, KR etiket|deger
1.06 ve 0.78); v1'in `1.0`'i bu sinifin icindeydi (1.0 KR 0.78'i
birlestirir: 4 -> 3). 0.75 dort 1-em fixture'inda kutu sayisini korur;
2.0 ve 10.0 hepsini birlestirir. Gri bolge `[0.6, 0.95] x h`
`[ÖLÇÜLMÜYOR]` sinif olarak; olculen iki ornek: menu fixture'inda "120 /
150" icindeki `/`-`150` boslugu `1.04` -> AYRILIR; KR 1-em etiket|deger
`0.78` -> AYRILIR ama esige `0.03 x h` (~1 px) mesafede -- font/olcek
degisince donebilir (belgeli).

KAPI NOTU (olcum 1, `evidence/olcum-1-*`): `real_check` #4b menu
fixture'inda etiket|deger boslugu `13.1-16.3 x h`; `YATAY_BOSLUK_ESIGI
= 10.0` mutanti orada DUSMEZ (13 > 10), paketin "10.0 burada birlestirir
ve duser" cumlesi olculmemisti. Kapinin gercek ayirt penceresi (0.57,
13.1): 0.57 -> dlg_KR 5 blok (#1 IHLAL), 0.75/1.0/2.0/10.0 -> #1 ve #4b
"ok". 0.75'i 1.0/2.0/10.0'dan ayiran olcu birim testleri (0.76 -> ayri,
3 x h -> ayri; mutant kiti M01 9 testle yakalar) ve olcum 2'dir.

Olcu: `test_k2_*` -- ortusme 0.49/0.50/0.51 (sinirda `>=`), bosluk
0.74/0.75/0.76 (sinirda `<=`), `min(h)` kisa kutuyla, Y2 fixture'i
(orijinal h), cakisma (-5) komsu, `monitor_index` 0/1, `dpi_scale`,
yozlasmis (w/h sifir ve negatif, araya girince komsulugu bozmaz),
zincir, cift tespit, ic ice, iki satir, y-titresimli satir 3 (itiraz),
KR 17 -> [2,5,5,5], merdiven, uzun kutu koprusu. Gercek OCR:
`real_check.py` #1 (KR 17 -> 4, `[2,5,5,5]`), #2 (JP/EN no-op), #4b
(menu: etiket|deger 13.1-16.3 x h birlesmez -- yalniz `>= 13.1` esikleri
eler, bkz. KAPI NOTU); olcum 2 (1-em sinifi, dort fixture).

## K3 -- birlestirme karakteri BETIKLE, dille degil

Komsu iki parcanin arasina: ikisi de CJK ise HIC, aksi halde (Hangul,
Latin, rakam, karisik) TEK bosluk. Parcanin betigi = strip sonrasi
metindeki ILK HARFIN (`str.isalpha()`) `unicodedata.name`'i; adi
`HIRAGANA`, `KATAKANA` (yarim genislik ve `ー` dahil), `CJK UNIFIED
IDEOGRAPH` ya da `CJK COMPATIBILITY IDEOGRAPH` iceriyorsa CJK, degilse
LATIN sayilir (KARAR: paket "Hiragana/Katakana/CJK Unified" yazar;
yarim genislik katakana ve uyumluluk ideograflari da CJK'dir, ayni
degismezin alt kumesi). Harf ICERMEYEN parca (`。`, `！？`, salt rakam)
LATIN sayilir -> bosluk (`待って` + `。` -> `待って 。`; `42` + `点` ->
`42 点`) -- bilinen sinir, testte SABITLENDI. `々`/`〆` (IDEOGRAPHIC
... MARK) ve Bopomofo LATIN sayilir `[ÖLÇÜLMÜYOR]` (nadir). Dil
parametresi YOK: JP satirinda `HP` olabilir (`HP` + `が` -> `HP が`).
Her parca `strip()` edilir (bastaki/sondaki bosluk KORUNMAZ; ic bosluk
ve `\\n` aynen); strip sonrasi BOS parca `text`e ne kendini ne ayirici
ekler ama `bbox`/`line_boxes`/`confidence` hesabina girer (KARAR, paket
sessizdi; gercek motor bos metin vermez -- T-006 K5). Hepsi bos -> `""`.
Olcu: `test_k3_*` (13 satirlik tablo, uc parca, bos parca).

## K4 -- TEK uygulama; yeniden uygulama sabit nokta DEGIL

Fonksiyon pipeline'da BIR KEZ cagrilir (`normalize`'dan hemen once).
Ikinci uygulama TANIMSIZDIR: birlesik blogun `h`'si parcalarin
maksimumu olur, `min(h)` buyur ve daha once komsu olmayan kutu komsu
olur -- `f(f(x)) == f(x)` genel olarak TUTMAZ (KRT: 4000 rastgele
girdide 115 ihlal; Y2 fixture'inda 2 -> 1). Bu bir garanti DEGILDIR,
`[ÖLÇÜLMÜYOR]` degismez olarak; yalniz belge + pozitif kontrol
`test_k4_ikinci_uygulama_sabit_nokta_degil_pozitif_kontrol`.
Docstring'de yasak sozcuk yok: `test_k4_docstring_*`.

## K5 -- birlesik blogun alanlari

`bbox` = parcalarin eksen hizali birlesimi (`x=min x`, `y=min y`,
`w = max right - min x`, `h = max bottom - min y`; parcalar `int` ise
dort alan `type is int` -- ek donusum YOK), `monitor_index`/`dpi_scale`
ilk parcadan (yuzey bolumlemesi geregi hepsinde ayni). `confidence =
min(NaN olmayan parcalar)`, hepsi NaN -> NaN (K8). `line_boxes` =
parcalarin `bbox`'lari X SIRASINDA (parcalarin kendi `line_boxes`'lari
DEGIL; T-006 bos demet verir). Tek parcali grup: girdideki NESNE AYNEN
(`is`), `line_boxes` dokunulmaz. `text` K3'e gore. Olcu: `test_k5_*`
(3 parca karisik girdi, `json.dumps(asdict(bbox))`, tek parca `is`,
negatif koordinat).

## K6 -- okuma sirasi (T-004 K28 tanimi)

Cikti `(bbox.y, bbox.x)` artan; bag, parcalarin EN KUCUK girdi
indeksiyle cozulur (yozlasmis/tek blokta kendi indeksi). Girdi sirasi
onemsizdir: `(y,x)` bagi olmayan girdide her permutasyon AYNI listeyi
verir (17 KR kutusu 5 karisik sirada; 4 kutu 24 permutasyon). Iki
kutu ayni `(y,x)`'teyse cikti girdi sirasina baglidir -- K6'nin siniri,
`test_k6_bagli_durum_*` ile SABITLENDI (monitorler arasi bagda da girdi
indeksi, isleme sirasi degil; bagli iki kutudan girdide ONCE gelen
satirin referans blogu olur -- yukseklikleri farkliysa sonraki
kutularin satir uyeligi buna baglidir,
`test_k6_bagli_durumda_satir_referansi_ilk_girdi_blogu`). Ayni
satirdaki iki grubun sirasi da `(y,x)`'e goredir: sagdaki grubun
`min y` daha kucukse ONCE gelir
(`test_k6_cikti_y_x_sirasinda_satir_icinde_de`; normalizer zaten
`(y,x)` ile yeniden siralar). Olcu: `test_k6_*`.

## K7 -- iki sutunlu duzen

Ayni satirda bosluk `> 0.75 x min(h)` -> ayri blok (menu sutunlari).
Olcu: `test_k7_*` (3 x h; 2 sutun x 3 satir -> 6 blok); gercek:
`real_check.py` #4b (`fixtures/menu_KR_EN.png`, etiket|deger 13.1-16.3
x h, KR 13 -> 9 blok ve her satir >= 2 blok, EN 8 -> 8; yalniz `>= 13.1`
esikleri eler) ve olcum 2 (1-em sinifi 0.78-1.14 x h: 0.75 ayirir, 1.0
KR 0.78'i birlestirir).

## K8 -- yozlasmis girdi

Bos -> `[]`. Tek blok -> `[ayni nesne]`. `confidence` NaN: `min` NaN
OLMAYANLAR uzerinden ACIK suzgecle (`math.isnan`; Python `min` NaN'da
sira bagimlidir -- KRT olctu), hepsi NaN -> NaN; NaN'in x sirasinda ilk/
son olmasi sonucu degistirmez. Negatif koordinat normal. `h < 0` /
`w < 0` -> `h = 0` gibi (birlesmez, aynen gecer). Tip denetimi YOK
(numpy dahil; T-006 `int` garantili, paket bilincli). `confidence`
araligi ([0,1]) denetlenmez -- normalizer K7'nin isi. Olcu: `test_k8_*`.
"""
from __future__ import annotations

import math
import unicodedata
from collections.abc import Sequence
from typing import Final

from src.contracts.models import Rect, TextBlock

__all__ = ("satirlari_birlestir", "DIKEY_ORTUSME_ESIGI", "YATAY_BOSLUK_ESIGI")

DIKEY_ORTUSME_ESIGI: Final[float] = 0.5
"""K2 -- ayni satir: dikey ortusme `>= oran * min(h_ilk, h_aday)` (S6:
olculen 1.00; sik dizilmis KR'de satirlar arasi ortusme 0.03-0.10 h)."""

YATAY_BOSLUK_ESIGI: Final[float] = 0.75
"""K2/K7 -- komsuluk: `aday.x - son.right <= oran * min(h_son, h_aday)`
(KR kelime boslugu <= 0.57 h; 1-em bosluk sinifi >= 0.97 h; KRT Y3)."""

_CJK_AD_PARCALARI: Final[tuple[str, ...]] = (
    "HIRAGANA",
    "KATAKANA",
    "CJK UNIFIED IDEOGRAPH",
    "CJK COMPATIBILITY IDEOGRAPH",
)
"""K3 -- `unicodedata.name` icinde bunlardan biri geciyorsa harf CJK'dir."""

_Anahtar = tuple[int, int, int]
"""Okuma sirasi anahtari: `(bbox.y, bbox.x, girdi indeksi)` (K6)."""


def satirlari_birlestir(blocks: Sequence[TextBlock]) -> list[TextBlock]:
    """Ayni satirdaki yatay komsu kutulari tek `TextBlock`'a birlestirir.

    Tam davranis sozlesmesi modulun UST docstring'indedir (K1-K8). Saf:
    girdi degismez, I/O yok. BIR KEZ cagrilir; ciktiyi yeniden vermek
    tanimsizdir (K4). Cikti `(y, x, girdi indeksi)` okuma sirasindadir.
    """
    sirali = sorted(enumerate(blocks), key=lambda c: (c[1].bbox.y, c[1].bbox.x, c[0]))

    sonuc: list[tuple[_Anahtar, TextBlock]] = []
    yuzeyler: dict[tuple[int, float], list[tuple[int, TextBlock]]] = {}
    for idx, blok in sirali:
        if _yozlasmis(blok.bbox):
            sonuc.append(((blok.bbox.y, blok.bbox.x, idx), blok))
            continue
        anahtar = (blok.bbox.monitor_index, blok.bbox.dpi_scale)
        yuzeyler.setdefault(anahtar, []).append((idx, blok))

    for yuzey in yuzeyler.values():
        for satir in _satirlara_bol(yuzey):
            for grup in _gruplara_bol(satir):
                sonuc.append(_grubu_birlestir(grup))

    sonuc.sort(key=lambda c: c[0])
    return [blok for _, blok in sonuc]


def _yozlasmis(r: Rect) -> bool:
    """K2/K8: `h <= 0` ya da `w <= 0` -- olcu yok, birlesme karari verilemez."""
    return r.h <= 0 or r.w <= 0


def _dikey_ortusme_yeterli(a: Rect, b: Rect) -> bool:
    """K2: dikey ortusme `>= DIKEY_ORTUSME_ESIGI * min(h)` (carpma, bolme yok)."""
    ortusme = min(a.bottom, b.bottom) - max(a.y, b.y)
    return ortusme >= DIKEY_ORTUSME_ESIGI * min(a.h, b.h)


def _yatay_komsu(son: Rect, aday: Rect) -> bool:
    """K2: `x` KESIN ilerliyor VE bosluk `<= YATAY_BOSLUK_ESIGI * min(h)`.

    `son` ve `aday` OZGUN kutulardir -- birlesik kutu HIC kullanilmaz (Y2).
    """
    if not aday.x > son.x:
        return False
    bosluk = aday.x - son.right
    return bosluk <= YATAY_BOSLUK_ESIGI * min(son.h, aday.h)


def _satirlara_bol(
    yuzey: Sequence[tuple[int, TextBlock]],
) -> list[list[tuple[int, TextBlock]]]:
    """K2 adim 3: `(y,x,idx)` sirali bloklari, satirin ILK bloguyla dikey
    ortusmeye gore satirlara boler (tek gecis)."""
    satirlar: list[list[tuple[int, TextBlock]]] = []
    for oge in yuzey:
        if satirlar and _dikey_ortusme_yeterli(satirlar[-1][0][1].bbox, oge[1].bbox):
            satirlar[-1].append(oge)
        else:
            satirlar.append([oge])
    return satirlar


def _gruplara_bol(
    satir: Sequence[tuple[int, TextBlock]],
) -> list[list[tuple[int, TextBlock]]]:
    """K2 adim 4: satiri `(x, y, idx)` ile siralar; grubun ILK bloguyla
    dikey ortusme + SON bloguna gore komsuluk ile gruplara boler (tek gecis)."""
    x_sirali = sorted(satir, key=lambda c: (c[1].bbox.x, c[1].bbox.y, c[0]))
    gruplar: list[list[tuple[int, TextBlock]]] = []
    for oge in x_sirali:
        if gruplar:
            ilk = gruplar[-1][0][1].bbox
            son = gruplar[-1][-1][1].bbox
            if _dikey_ortusme_yeterli(ilk, oge[1].bbox) and _yatay_komsu(son, oge[1].bbox):
                gruplar[-1].append(oge)
                continue
        gruplar.append([oge])
    return gruplar


def _grubu_birlestir(grup: Sequence[tuple[int, TextBlock]]) -> tuple[_Anahtar, TextBlock]:
    """K5: grubu tek `TextBlock`'a indirger; tek parca -> ayni nesne.

    Donus: `(okuma sirasi anahtari, blok)`; anahtar `(y, x, en kucuk
    girdi indeksi)` (K6).
    """
    en_kucuk_idx = min(idx for idx, _ in grup)
    if len(grup) == 1:
        tek = grup[0][1]
        return (tek.bbox.y, tek.bbox.x, en_kucuk_idx), tek

    parcalar = [blok for _, blok in grup]
    ilk = parcalar[0].bbox
    x = min(p.bbox.x for p in parcalar)
    y = min(p.bbox.y for p in parcalar)
    sag = max(p.bbox.right for p in parcalar)
    alt = max(p.bbox.bottom for p in parcalar)
    bbox = Rect(
        x=x,
        y=y,
        w=sag - x,
        h=alt - y,
        monitor_index=ilk.monitor_index,
        dpi_scale=ilk.dpi_scale,
    )
    guvenler = [p.confidence for p in parcalar if not math.isnan(p.confidence)]
    confidence = min(guvenler) if guvenler else math.nan
    blok = TextBlock(
        text=_metinleri_birlestir([p.text for p in parcalar]),
        bbox=bbox,
        confidence=confidence,
        line_boxes=tuple(p.bbox for p in parcalar),
    )
    return (bbox.y, bbox.x, en_kucuk_idx), blok


def _metinleri_birlestir(parcalar: Sequence[str]) -> str:
    """K3: strip edilmis parcalari betige gore (CJK-CJK bossuz, aksi halde
    tek bosluk) birlestirir; bos parca atlanir."""
    sonuc = ""
    onceki_cjk = False
    for ham in parcalar:
        metin = ham.strip()
        if not metin:
            continue
        cjk = _betik_cjk_mi(metin)
        if sonuc and not (onceki_cjk and cjk):
            sonuc += " "
        sonuc += metin
        onceki_cjk = cjk
    return sonuc


def _betik_cjk_mi(metin: str) -> bool:
    """K3: metindeki ILK HARFIN betigi CJK mi; harf yoksa `False` (LATIN)."""
    for karakter in metin:
        if karakter.isalpha():
            ad = unicodedata.name(karakter, "")
            return any(parca in ad for parca in _CJK_AD_PARCALARI)
    return False
