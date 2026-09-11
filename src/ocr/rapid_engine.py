"""Suflor -- yerel ONNX OCR motoru (`RapidOcrEngine`), T-006.

`OcrEngine` sozlesmesinin (`src/contracts/interfaces.py`) v1 uygulamasi:
`Frame` -> `list[TextBlock]`. Altta `rapidocr` 3.9.2 + onnxruntime; dil
ACIK secilir (JP/KR/ZH/EN), is parcacigi sayisi ACIK verilir, aci
siniflandirici (cls) KAPALIDIR, kutuphanenin guven suzgeci KAPATILIR.

Bu docstring, gorev paketindeki (T-006 packet.md surum 2) K1-K11
kararlarinin bu modulde nasil uygulandigini belgeler. Her kararin yaninda
onu olcen test adi vardir (`tests/unit/ocr/test_rapid_engine.py`) ya da
`[ÖLÇÜLMÜYOR]` damgasi. Tester `known_gaps`i OKUMAZ; garanti alani burasidir.

Yapi
-----
`OcrLanguage` (StrEnum) · `TanımaÇıktısı` (Protocol: rapidocr ciktisinin
bize gereken yuzu) · `Tanıyıcı` / `TanıyıcıFabrikası` (tip takma adlari)
· `RapidOcrEngine` (dogrulama + tembel kurulum + donusum).

Kutuphane ENJEKTE edilir: `recognizer_factory` `params` sozlugunu alir ve
bir tanıyıcı (`ImageArray -> TanımaÇıktısı`) dondurur. `None` ise gercek
kutuphaneyi kuran `_varsayilan_fabrika` kullanilir. Butun birim testleri
sahte fabrikayla kosar; gercek model yalniz
`.agents/tasks/T-006/real_check.py` ile (ayri surec) olculur.

Import bicimi (K1)
-------------------
`rapidocr` yalniz `_varsayilan_fabrika` GOVDESINDE import edilir; modul
duzeyinde ne `rapidocr` ne `onnxruntime` ne de `LangRec`/`LangDet` adi
gecer. Sefin `tests/unit/ocr/conftest.py` bariyeri test surecinde bu
import'lari `RuntimeError` ile keser; bu yuzden testlerde calisan HICBIR
yol kutuphaneye dokunamaz -- model dizini cozumlemesi ve dosya adi
tablosu da dahil (asagida K6/K11). Olcu: `test_k1_*`.

`src/__init__.py` yoktur; `src.contracts` MUTLAK import edilir (T-005'in
"Source file found twice" olcumu). Bu modul kardes modul import etmez.

## K2 -- dil ACIK secilir; guven puani dil hatasini goremez

`language` ZORUNLU ve keyword-only, varsayilani YOK. Gerekce (olgular O2):
`ch` modeli Japonca diyalogda 0.90 guvenle YANLIS metin uretir; on
ayarlarin guven esigi (0.60) bunu suzemez. Motor dili TAHMIN ETMEZ.
`OcrLanguage(language)` ile dogrulanir: uye ya da degeri (`"japan"`) kabul,
baska her sey `ValueError` (yapimda). Olcu: `test_k2_*`;
`real_check.py` #1/#2 (JAPAN 4/4, ayni goruntu CHINESE <4 -- pozitif
kontrol, yalniz K11 tablosuyla ateslenir).

## K3 -- is parcacigi ACIK; "otomatik" hicbir yoldan girmez

`threads` in `[1, os.cpu_count()]`; `None` -> `min(8, os.cpu_count() or 1)`.
Aralik disi (`0`, `-1`, `cpu_count+1`) -> `ValueError` YAPIMDA. Tam sayi
olmayan (`bool`, `float`, `str`) -> `TypeError` (KARAR: paket sessizdi;
`True == 1` sessizce gecmesin diye `bool` de reddedilir; `numbers.Integral`
-- ornegin `np.int64` -- kabul edilip DUZ `int`e duzlestirilir, cunku
onnxruntime oturum secenegine numpy skaleri gitmemeli). Deger
`EngineConfig.onnxruntime.intra_op_num_threads` VE `inter_op_num_threads`
anahtarlarina AYNEN gider; `Global.use_cls = False`.

Neden ust sinir: kutuphane `threads > cpu_count` verilirse degeri SESSIZCE
yok sayar ve onnxruntime "otomatik"e (0,0) doner (KRT olctu, sef dogruladi);
"otomatik" 32 cekirdekli makinede 6 KAT yavas (olgular O3: 1450 ms vs 195
ms). Ust siniri motor kendisi uygular ki sessiz otomatik hicbir yoldan
girmesin. `os.cpu_count()` `None` donerse 1 sayilir. Olcu: `test_k3_*`
(4 ve 8 iki noktada; `cpu_count=6` yamasiyla 8 -> `ValueError`, `None` ->
6, 4 -> gecer; 0/-1 -> `ValueError`); `real_check.py` oturum seceneklerini
dogrudan okumaz -- `[ÖLÇÜLMÜYOR]` gercek oturumda; sefin olcum-3'u (evidence)
8/8 gosterdi.

## K4 -- `bbox` ekran koordinatinda, duz `int`, eksen hizali

rapidocr `(N,4,2)` float32 cokgen dondurur, GORUNTU-YEREL. `TextBlock.bbox`
= cokgenin eksen hizali sinir kutusu, `frame.rect.x/y` kadar KAYDIRILMIS:
`x=floor(min_x)+rect.x`, `y=floor(min_y)+rect.y`, `w=ceil(max_x)-floor(min_x)`,
`h=ceil(max_y)-floor(min_y)`. Dort alan da `type(v) is int`.
`monitor_index`/`dpi_scale` `frame.rect`ten aynen. Tam sayi koseli cokgen
fazla piksel VERMEZ (`[[10,20],[50,20],[50,40],[10,40]]` -> `w=40,h=20`).
Goruntu disina tasan cokgen KIRPILMAZ, yalniz kaydirilir. Dejenere cokgen
(`w=0` ya da `h=0`) MUMKUNDUR ve oldugu gibi gecer -- eleme normalizer'in
isidir. Kutu SIRASI rapidocr'un sirasidir; yeniden siralama YOK.
`line_boxes` bos demettir (normalizer okumuyor -- T-004 K1).

`frame.rect.x/y/monitor_index` duz `int` degilse (numpy skaleri)
`ContractViolation` (KARAR: aksi halde toplam numpy tipine sizar ve K4
`type is int` bozulur; `CaptureService` zaten duzlestirilmis `Rect` verir).
Olcu: `test_k4_*` (iki frame: `(0,0)` ve `(-2600,-50, monitor_index=0)`;
egik cokgen; tam sayi koseli cokgen; tasan cokgen; dejenere cokgen);
`real_check.py` #6 (iki nokta farki tam `(-2600,-50)`).

## K5 -- guven SUZULMEZ; kutuphanenin kendi suzgeci KAPATILIR

Sozlesme: motor esik uygulamaz. rapidocr'un `Global.text_score`
varsayilani 0.5'tir ve altinda kalan bloklari SESSIZCE dusurur (KRT Y1,
sef dogruladi; bu makinede yeniden olculdu: KR fixture + JAPAN modeli,
`text_score=0.5` -> 9 kutu, `0.0` -> 17 kutu, 8'i 0.5 altinda --
`evidence/olcum-3-gercek-motor-davranisi.txt` #9). Motor `Global.text_score
= 0.0` gecer. Her `(kutu, metin, puan)` uclusu bire bir `TextBlock`;
`confidence = float(puan)` (`NaN` aynen, numpy skaleri duz `float`a);
`text` DEGISTIRILMEZ (strip yok, bos string ve bosluklu metin aynen).

Bos sonuc: rapidocr `None` DONDURMEZ; `boxes/txts/scores` alanlari `None`
olan bir nesne dondurur (olcum-3 #5: `RapidOCROutput(boxes=None, ...)`)
-> `[]`, istisna YOK. `boxes is None` iken `txts` bos-olmayan bir dizi ise
bu "kutusuz metin"dir -> `OcrError` (gercek motor bunu uretmez; sahte
icin gurultulu). Kutuphane, tanima metni `strip()` sonrasi bos olan
satirlari BIZDEN ONCE eler (KRT D3) -- bu bir guven suzgeci degildir ve
kapatilamaz; belgelenir. Olcu: `test_k5_*`; `real_check.py` #8 (pozitif
kontrol: KR fixture + JAPAN dili -> en az 1 blok `confidence < 0.5`).

## K6 -- hata siniflandirmasi ve indirme denetimi

rapidocr'un `Det.model_dir`/`Rec.model_dir` anahtarlari YOK SAYILIR (sef
olctu; olcum-3 #8b yeniden uretti: `Det.model_dir` verilince model
`Global.model_root_dir`e INDIRILDI). Isleyen tek yol `*.model_path`
(acik dosya) ve `Global.model_root_dir` (kok; dosya yoksa INDIRIR).

* `allow_download=False` (varsayilan): motor det ve rec icin ACIK
  `Det.model_path` / `Rec.model_path` = `model_dir / <ad>` gecer. Dosya
  yoksa kutuphane CAGRILMADAN `ModelMissingError` (mesajda eksik dosya
  adlari; `__cause__` yok -- dosya sistemi kontrolu bizim).
  `Global.model_root_dir` GECILMEZ: cls modeli kutuphanenin kendi
  `models/` dizininden cozulur.
* `allow_download=True`: `*.model_path` gecilmez; kutuphane ilk kurulumda
  indirir (olgular O4: 2.3 + 9.3 MB). `model_dir` verilmisse
  `Global.model_root_dir = model_dir` gecilir ki indirme CAGIRANIN dizinine
  insin (KARAR: paket sessizdi; verilmezse site-packages icine yazar).
  Cevrimdisi -> kutuphanenin indirme istisnasi -> `ModelMissingError`
  (`__cause__` ozgun) -- `[ÖLÇÜLMÜYOR]`: ag kesmek kapinin isi degil.
* `model_dir=None` -> kutuphanenin kendi `models/` dizini. Dizin
  `importlib.metadata` ile bulunur, `import rapidocr` ile DEGIL: bariyer
  altinda `import rapidocr`, `import rapidocr.inference_engine.base` ve
  `importlib.util.find_spec("rapidocr")` UCU DE `RuntimeError` verir;
  `importlib.metadata.distribution("rapidocr").locate_file(...)` ayni yolu
  kutuphaneyi YUKLEMEDEN verir (olcum-1). Dagitim yoksa `ModelMissingError`.
* Beklenen dosya adlari SABIT tablodadir (`beklenen_model_dosyalari`),
  paketin dedigi gibi kutuphanenin cozucusunden CANLI okunmaz -- ayni
  bariyer nedeniyle (itiraz, `known_gaps`). Tablo, kutuphanenin
  `InferSession.get_model_url(FileInfo(...))` ciktisiyla dort dil x det/rec
  icin birebir eslendi (olcum-2 (a)).
* Cls modeli YONETILMEZ: `Global.use_cls=False` ama kutuphane cls
  oturumunu yine de kurar; dosya wheel ile geliyor (RECORD'da olculdu,
  olcum-2 (d)). Silinmisse kutuphane indirir -- `[ÖLÇÜLMÜYOR]`, belgelenir.
* (b) Motor kuruldu, tanıyıcı istisna firlatti -> `OcrError`
  (`__cause__` ozgun). Fabrika (kurulum) istisnasi: `TranslatorError`
  OLDUGU GIBI gecer; `FileNotFoundError` -> `ModelMissingError`; baska her
  `Exception` -> `OcrError` (Y2: desteklenmeyen dil/surum `ValueError`
  dahil). Kurulum basarisizsa ornek tutulmaz; sonraki `recognize`
  kurulumu YENIDEN dener (otomatik yeniden deneme YOK, cagiran ister).
* (c) `frame` bir `Frame` degilse; `frame.image` `np.ndarray`, `ndim==3`,
  `shape[2]==3`, `uint8` ve `h>0, w>0` degilse `ContractViolation`, motor
  CAGRILMAZ (kapali motorda once `OcrError` gelir, K10 sirasi). `0x0` ve
  `h=0` gercek motorda `ZeroDivisionError` verir (olcum-3 #7). Baglantililik
  (C-contiguous) ve `image.shape` ile `rect.w/h` tutarliligi DENETLENMEZ
  (`CaptureService` K7 garanti eder); cv2 hatasi `OcrError` olarak yuzeye
  cikar. Goruntu KOPYALANMAZ; kutuphane girdiyi degistirmiyor (KRT D2,
  olcum-3 #6 yeniden uretti).
* Bozuk cikti (uzunluk farki, `txts`/`scores` `None` iken `boxes` var,
  `txts` dizi degil duz `str`/`bytes`, `txts` icinde `None`/`bytes`, puan
  sayi degil, cokgen `(k,2)` degil ya da sonlu degil, uzunlugu okunamayan
  alan, alanlari olmayan nesne) -> `OcrError`; hata metni blok METNINI
  TASIMAZ.

Olcu: `test_k6_*`; `real_check.py` #7 (bos dizin -> `ModelMissingError`).

## K7 -- motor OCR metnini loglamaz; kutuphane logu kurulumdan SONRA susturulur

DEGISMEZ (kanal-bagimsiz, tur 2 T2-1): `recognize` suresince OCR metni
HICBIR cikis kanalina yazilmaz -- stdout, stderr, herhangi bir `logging`
logger'i (ad ve seviye ne olursa olsun), `warnings`. Bu modulde `print`
yok, `sys.std*`/`os.write` yok, `logging` YAYIMI yok (yalniz
`getLogger(...).setLevel`).

Kutuphane `"RapidOCR"` logger'ini KURULUMDA kendisi seviyelendirir
(olcum-3 #2: kurulum oncesi ERROR -> kurulum sonrasi INFO). Bu yuzden motor
seviyeyi `ERROR`a fabrika DONDUKTEN SONRA ceker; ayrica params'a
`Global.log_level="error"` koyar ki kurulum SIRASINDAKI INFO satirlari
(motor adi, model yolu) da basilmasin (olcum-3 #3). `WARNING` yetmez:
metinsiz her karede WARNING basiliyor. Motor seviyeye yalniz kurulumda
dokunur; uygulama sonradan o logger'i acarsa (debug modu) kutuphanenin
kendi satirlari gecer -- bu ust katman karari, motor degil.

Olcu (DAVRANIS, tur 2): `test_k7_soguk_motor_*` ve `test_k7_sicak_motor_*`
-- iki nobetci metinli (Latin + CJK) sahte tanıyıcıyla `recognize`;
`capfd` ile fd duzeyinde stdout/stderr `== ""` (sifir bayt; `sys.stdout.write`,
`os.write(1)`, `sys.__stderr__` hepsi gorunur), kok logger DEBUG'da
`caplog` + `RapidOCR` logger'ina DOGRUDAN takili handler (propagate=False
kor birakmasin) altinda hicbir kayit nobetci icermez, `warnings` kanali
temiz. Iki nokta: soguk (kurulum + tanima) ve sicak (kurulumdan SONRA
kutuphane logger'i acilmis). Pozitif kontrol: her kanala nobetci yazan
test ici sahte motorlarla ayni olcu DUSER (`test_k7_pozitif_kontrol_kanal_*`).
AST ikincil: `print`/`sys.stdout.write`/`sys.stderr.write`/`os.write` ve
log yayimi 0 (`test_k7_ast_*`). Sira olcusu: fabrika seviyeyi INFO'ya
sifirlar -> recognize sonrasi ERROR (`test_k7_logger_seviyesi_*`).

## K8 -- `preset` kabul edilir ama v1'de motoru DEGISTIRMEZ `[ÖLÇÜLMÜYOR]`

Dort `OcrPreset` de ayni sonucu verir; `preset` hicbir params anahtarina
girmez. Tasarim 3.2'nin on ayar bazli olcekleme/kontrast on islemesi
OLCULMEDEN YAZILMAZ: `[ÖLÇÜLMÜYOR]` -- ayri gorev. Olcu:
`test_k8_dort_preset_ayni_cikti`.

## K9 -- sure kutu sayisina baglidir; olcu DISARIDAN, tek butce

Motor sure TUTMAZ (`last_timing` yok). Butce tek yerde: `budget_ms: 300`
= JAPAN, 1200x400 4 satir, v4-mobile, 8 parcacik. Diger diller
`real_check.py` #5'te RAPORLANIR. `[ÖLÇÜLMÜYOR]` birim testte.

## K10 -- tembel kurulum, tek ornek, kapatma

`__init__` kutuphaneye ve dosya sistemine DOKUNMAZ (yalniz argüman
dogrulama). Ilk `recognize` model dosyalarini denetler, fabrikayi cagirir;
sonrakiler ayni tanıyıcıyı kullanir. `close()` idempotent; tanıyıcı
referansi BIRAKILIR (`_taniyici = None` -- gercek yolda det+rec ONNX
oturumlari; dil degisiminde eski motor bellekte kalmasin, T2-2); sonrasi
`recognize` -> `OcrError`, fabrika yeniden CAGRILMAZ. Baglam yoneticisi
DEGIL (T-005 dersi). `recognize` sirasi: kapali mi -> kare dogrulama ->
tembel kurulum -> tanıma -> donusum. Kurulum (fabrika) hata verirse ornek
TUTULMAZ; bir sonraki `recognize` kurulumu yeniden dener (K6 b). Olcu:
`test_k10_*` (weakref: `close()` + `gc.collect()` sonrasi tanıyıcı olu).

## K11 -- model tablosu dil basina SABIT (T-009: tanima surumu DILE OZEL)

Kutuphane varsayilani PP-OCRv6-small KULLANILMAZ (KOREAN'da `ValueError`,
JAPAN'da 2x yavas, CH/EN/JAPAN ayni dosyaya cozulup K2 pozitif kontrolunu
dusurur). Her dil icin gecilen tablo (`Det/Rec.engine_type="onnxruntime"`,
`Det/Rec.model_type="mobile"`, `Det.ocr_version="PP-OCRv4"` ortak;
`Rec.ocr_version` dile ozel):

    JAPAN   Det.lang_type="multi"  Rec.lang_type="japan"   Rec.ocr_version="PP-OCRv4"
    KOREAN  Det.lang_type="multi"  Rec.lang_type="korean"  Rec.ocr_version="PP-OCRv5"
    CHINESE Det.lang_type="ch"     Rec.lang_type="ch"      Rec.ocr_version="PP-OCRv4"
    ENGLISH Det.lang_type="ch"     Rec.lang_type="en"      Rec.ocr_version="PP-OCRv4"

Det iki farkli: `multi` det Ingilizce'yi 22 kelime kutusuna boler, `ch`
det Korece bosluklarini yitirir (KRT Y3).

Neden KOREAN rec v5 (T-009 K1/K4): v4 Korece tanima modeli cumle sonu
noktasini HIC vermiyor (dlg_KR: kaynakta 3 nokta, 17 blokta 0; tespit
degil TANIMA -- uc det modelinde de kutu metnin sonuna kadar uzuyor).
Noktasiz govde T-007'de bolunemez ve NMT icerik yitirir (6 kelime vs 15).
v5 mobile ucunu de verir, ayni kelime dogrulugu (17/17), 3x hizli (332 vs
1099 ms). Dosya: `korean_PP-OCRv5_rec_mobile.onnx` (`_MODEL_DOSYALARI`).
`Det.ocr_version` her dilde v4 kalir (det degismedi).

Neden digerleri v4 (T-009 K5): JAPAN'da v5 YOK (kutuphane `ValueError`);
ENGLISH v5 mumkun (4/4, %25 hizli) ama KR'deki gibi olculmus bir kusur
yok -- ACIK KALEM, T-009 kapsam disi; CHINESE olculmedi. Olcu: iki nokta
(KOREAN v5 / JAPAN v4), `test_k11_t009_*`.

Hangisi belirleyici (T-009 olcum-1, gercek model): `allow_download=False`
yolunda motor `Rec.model_path`i ACIK verir ve kutuphane O dosyayi yukler;
`Rec.ocr_version` dosya secimine KATILMAZ (v5 dosya + v4 etiketi -> yine
3 nokta). Yani urun yolunda belirleyici olan `_MODEL_DOSYALARI`dir.
`Rec.ocr_version` indirme yolunda (`allow_download=True`, model_path yok)
dosyayi secer (v5 -> 3 nokta / 384 ms, v4 -> 0 nokta / 1539 ms); iki
tablo bu yuzden TUTARLI tutulur. Sonucu: JAPAN'a sizan bir v5 indirme
yolunda `ValueError` verir ama acik v4 dosya yoluyla SESSIZCE v4 kosar
(4/4) -- urun yolunda JAPAN v4 birim testi (`test_k11_t009_japan_ikisi_de_v4`)
tek bekcidir, gercek kapi onu goremez.

Degerler `params`ta STRING tasinir; `_varsayilan_fabrika` bunlari kutuphane
enum uyelerine cevirir (`LangDet("multi") is LangDet.MULTI` vb. -- olcum-2
(c)). Neden string: kutuphanenin enum'larini `params`a koymak icin
`rapidocr` import edilmeli, bariyer altinda bu `RuntimeError`dur; yani
sahte fabrika enum uyesi GOREMEZ (itiraz, `known_gaps`). Kutuphane
`engine_type/model_type/ocr_version` icin enum ZORUNLU kilar (string ->
`TypeError`, olcum-2 (b)); donusum bu yuzden fabrikanin icindedir ve gercek
yolda `real_check.py` #1-#4 ile olculur. Olcu: `test_k11_*` (dort dil x
alti anahtar; anahtar kumesi sabit; `Rec.ocr_version` dil basina),
`test_k11_t009_*` (KOREAN v5 / JAPAN v4 iki nokta; v5 dosya adi
`ModelMissingError` mesajinda, v4 dosyasina dusulmez), T-009
`real_check.py` #1-#3 (gercek modelde noktalar, uctan uca, sure).

Windows tuzaklari (belgelenir)
-------------------------------
`cv2.imread` ASCII-disi yolda `None` doner (bu depo yolu `çeviri` icerir);
motor kutuphaneye YALNIZ numpy dizi verir, asla yol. cp1254 konsolda
Japonca metin `UnicodeEncodeError` verir; motor OCR metnini stdout'a
yazmaz (K7).
"""
from __future__ import annotations

import importlib.metadata
import logging
import math
import numbers
import os
from collections.abc import Callable, Sequence
from enum import StrEnum
from pathlib import Path
from typing import Final, Protocol

import numpy as np

from src.contracts.errors import (
    ContractViolation,
    ModelMissingError,
    OcrError,
    TranslatorError,
)
from src.contracts.interfaces import OcrEngine
from src.contracts.models import Frame, ImageArray, OcrPreset, Rect, TextBlock

__all__ = [
    "OcrLanguage",
    "TanımaÇıktısı",
    "Tanıyıcı",
    "TanıyıcıFabrikası",
    "RapidOcrEngine",
    "beklenen_model_dosyalari",
    "varsayilan_model_dizini",
]


class OcrLanguage(StrEnum):
    """Motorun ACIK secilen tanima dili (K2). `StrEnum`: profil JSON'una yazilir."""

    JAPAN = "japan"
    KOREAN = "korean"
    CHINESE = "chinese"
    ENGLISH = "english"


class TanımaÇıktısı(Protocol):
    """Kutuphane ciktisinin (`RapidOCROutput`) bize gereken yuzu (Y4).

    Uc alan da `None` olabilir: bos sonuc `boxes=None, txts=None,
    scores=None` biciminde gelir (olcum-3 #5). Salt-okunur ozellik olarak
    tanimlanir ki `Optional[np.ndarray]` / `Optional[tuple[str]]` tasiyan
    gercek sinif yapisal olarak uysun (duz oznitelik olsaydi mypy degismez
    tip isterdi).
    """

    @property
    def boxes(self) -> object | None: ...  # ndarray float32 (N,4,2) ya da None

    @property
    def txts(self) -> Sequence[str] | None: ...

    @property
    def scores(self) -> Sequence[float] | None: ...


Tanıyıcı = Callable[[ImageArray], TanımaÇıktısı]
"""Bir goruntu alir, kutuphane bicimli cikti dondurur."""

TanıyıcıFabrikası = Callable[[dict[str, object]], Tanıyıcı]
"""`params` sozlugunu alir, tanıyıcı kurar. Tek enjeksiyon dikisi (K1)."""


_VARSAYILAN_PARCACIK: Final = 8
"""K3: `threads=None` -> `min(8, cpu_count)` (olgular O3: 8 parcacik 195 ms)."""

_LOGGER_ADI: Final = "RapidOCR"
"""Kutuphanenin kendi logger adi (K7)."""

_MOTOR: Final = "onnxruntime"
_MODEL_TIPI: Final = "mobile"
_TESPIT_SURUMU: Final = "PP-OCRv4"
"""K11: `Det.ocr_version` -- her dilde ayni (T-009: yalniz tanima surumu dile ozel)."""
_CLS_DOSYASI: Final = "ch_ppocr_mobile_v2.0_cls_mobile.onnx"
"""Yonetilmez (K6); yalniz belge: wheel ile gelir, `use_cls=False`."""

_DIL_TABLOSU: Final[tuple[tuple[OcrLanguage, str, str, str], ...]] = (
    (OcrLanguage.JAPAN, "multi", "japan", "PP-OCRv4"),  # v5 YOK (ValueError, T-009 K5)
    (OcrLanguage.KOREAN, "multi", "korean", "PP-OCRv5"),  # v4 noktayi vermiyor (T-009 K1/K4)
    (OcrLanguage.CHINESE, "ch", "ch", "PP-OCRv4"),
    (OcrLanguage.ENGLISH, "ch", "en", "PP-OCRv4"),  # v5 mumkun, kapsam disi (T-009 K5)
)
"""K11: `(dil, Det.lang_type, Rec.lang_type, Rec.ocr_version)` -- kutuphane enum DEGERLERI."""

_MODEL_DOSYALARI: Final[tuple[tuple[OcrLanguage, str, str], ...]] = (
    (OcrLanguage.JAPAN, "multi_PP-OCRv3_det_mobile.onnx", "japan_PP-OCRv4_rec_mobile.onnx"),
    (OcrLanguage.KOREAN, "multi_PP-OCRv3_det_mobile.onnx", "korean_PP-OCRv5_rec_mobile.onnx"),  # T-009 K1
    (OcrLanguage.CHINESE, "ch_PP-OCRv4_det_mobile.onnx", "ch_PP-OCRv4_rec_mobile.onnx"),
    (OcrLanguage.ENGLISH, "ch_PP-OCRv4_det_mobile.onnx", "en_PP-OCRv4_rec_mobile.onnx"),
)
"""K6: `(dil, det dosyasi, rec dosyasi)` -- kutuphanenin cozucusuyle eslendi (olcum-2 (a))."""


# ---------------------------------------------------------------------------
# yardimcilar (dil / model / parcacik)
# ---------------------------------------------------------------------------


def _dil_satiri(language: OcrLanguage) -> tuple[str, str, str]:
    """`(Det.lang_type, Rec.lang_type, Rec.ocr_version)` -- K11 satiri."""
    for dil, det, rec, rec_surumu in _DIL_TABLOSU:
        if dil is language:
            return det, rec, rec_surumu
    raise ValueError(f"tabloda olmayan dil: {language!r}")  # yapisal olarak erisilemez


def beklenen_model_dosyalari(language: OcrLanguage) -> tuple[str, str]:
    """`(det, rec)` dosya adlari -- `allow_download=False` yolunda aranan adlar (K6)."""
    dil = OcrLanguage(language)
    for d, det, rec in _MODEL_DOSYALARI:
        if d is dil:
            return det, rec
    raise ValueError(f"tabloda olmayan dil: {dil!r}")  # yapisal olarak erisilemez


def varsayilan_model_dizini() -> Path:
    """Kutuphanenin kendi `models/` dizini, KUTUPHANEYI YUKLEMEDEN (K6).

    `importlib.metadata` dagitim kaydini okur; `sys.meta_path` bulucularina
    "rapidocr" adi icin sormaz, bu yuzden K1 bariyeri altinda da calisir
    (olcum-1: `import`/`find_spec` `RuntimeError`, bu yol ayni dizini verir).

    Raises:
        ModelMissingError: dagitim kurulu degilse (model dizini yok).
    """
    try:
        dagitim = importlib.metadata.distribution("rapidocr")
    except importlib.metadata.PackageNotFoundError as e:
        raise ModelMissingError(
            "OCR kutuphanesinin dagitimi bulunamadi; varsayilan model dizini yok"
        ) from e
    return Path(str(dagitim.locate_file("rapidocr"))).resolve() / "models"


def _parcacik_sayisi(threads: object) -> int:
    """K3: kabul kapisi + duzlestirme + aralik denetimi `[1, cpu_count]`."""
    cekirdek = os.cpu_count() or 1
    if threads is None:
        return min(_VARSAYILAN_PARCACIK, cekirdek)
    if isinstance(threads, bool) or not isinstance(threads, numbers.Integral):
        raise TypeError(f"threads tam sayi olmali, gelen: {threads!r}")
    n = int(threads)
    if not 1 <= n <= cekirdek:
        raise ValueError(
            f"threads aralik disi: {n} (izinli [1, {cekirdek}]; -1/'otomatik' YASAK, "
            "cpu_count ustu sessizce otomatige duserdi)"
        )
    return n


# ---------------------------------------------------------------------------
# gercek kutuphane fabrikasi (K1: import yalniz burada)
# ---------------------------------------------------------------------------


def _varsayilan_fabrika(params: dict[str, object]) -> Tanıyıcı:  # pragma: no cover -- K1: gercek model, real_check.py ile denetleniyor
    """`params`i kutuphane enum'larina cevirir, motoru kurar, tanıyıcı dondurur.

    String -> enum donusumu ZORUNLUDUR: kutuphane `engine_type/model_type/
    ocr_version` icin enum ister (string -> `TypeError`, olcum-2 (b));
    `lang_type` string kabul eder ama tutarlilik icin o da cevrilir.
    Cevrimdisi indirme hatasi -> `ModelMissingError`; diger istisnalar
    motora yayilir ve orada siniflandirilir (K6).

    `[ÖLÇÜLMÜYOR]` -- tanıyıcıdaki `isinstance(cikti, RapidOCROutput)` dali:
    kutuphane `RapidOCROutput` disinda bir tip dondurdugunde (`TextDetOutput`
    gibi) `OcrError` uretir; birim testte kutuphane yuklenmez (K1 bariyeri),
    `real_check.py`nin uc fixture'i bu dali TETIKLEMEZ (uc dilde de
    `RapidOCROutput` donuyor). Gercek tetikleyici bilinmiyor; belgelenir.
    Motorun genel "beklenmeyen tip -> OcrError" yolu sahte tanıyıcıyla
    olculur (`test_k6_taniyici_sozlesme_hatasi_oldugu_gibi_gecer`).
    """
    from rapidocr import EngineType, LangCls, LangDet, LangRec, ModelType, OCRVersion, RapidOCR
    from rapidocr.utils.download_file import DownloadFileException
    from rapidocr.utils.output import RapidOCROutput

    dil_enum = {"Det": LangDet, "Rec": LangRec, "Cls": LangCls}
    alan_enum = {"engine_type": EngineType, "model_type": ModelType, "ocr_version": OCRVersion}

    hazir: dict[str, object] = {}
    for anahtar, deger in params.items():
        bolum = anahtar.split(".", 1)[0]
        alan = anahtar.rsplit(".", 1)[-1]
        if alan == "lang_type" and bolum in dil_enum:
            hazir[anahtar] = dil_enum[bolum](deger)
        elif alan in alan_enum:
            hazir[anahtar] = alan_enum[alan](deger)
        else:
            hazir[anahtar] = deger

    try:
        motor = RapidOCR(params=hazir)
    except DownloadFileException as e:
        raise ModelMissingError("model indirilemedi (cevrimdisi ya da kaynak erisilemez)") from e

    def taniyici(img: ImageArray) -> TanımaÇıktısı:
        cikti = motor(img)
        if not isinstance(cikti, RapidOCROutput):
            raise OcrError(f"kutuphane beklenmeyen cikti tipi verdi: {type(cikti).__name__}")
        return cikti

    return taniyici


# ---------------------------------------------------------------------------
# dogrulama + donusum
# ---------------------------------------------------------------------------


def _kareyi_dogrula(frame: Frame) -> None:
    """K6 (c): bicim kurali TIP duzeyindedir; sessiz donusum yok."""
    if not isinstance(frame, Frame):
        raise ContractViolation(f"recognize Frame bekler, gelen: {type(frame).__name__}")
    img = frame.image
    if not isinstance(img, np.ndarray):
        raise ContractViolation(
            f"Frame.image np.ndarray olmali, gelen: {type(img).__name__}"
        )
    if img.ndim != 3 or img.shape[2] != 3:
        raise ContractViolation(
            f"Frame.image (h, w, 3) olmali, gelen shape={tuple(img.shape)}"
        )
    if img.dtype != np.uint8:
        raise ContractViolation(f"Frame.image uint8 olmali, gelen {img.dtype}")
    if img.shape[0] == 0 or img.shape[1] == 0:
        raise ContractViolation(
            f"Frame.image sifir boyutlu: shape={tuple(img.shape)} (motor 0x0'da coker)"
        )
    r = frame.rect
    for ad in ("x", "y", "monitor_index"):
        if type(getattr(r, ad)) is not int:
            raise ContractViolation(
                f"Frame.rect.{ad} duz int olmali, gelen: {type(getattr(r, ad)).__name__}"
            )


def _puan(deger: object) -> float:
    """K5: `confidence = float(puan)`; sayi degilse `OcrError` (metin yok)."""
    if isinstance(deger, bool) or not isinstance(deger, numbers.Real):
        raise OcrError(f"guven puani sayi degil: {type(deger).__name__}")
    return float(deger)


def _cokgen_kutusu(kutu: object, rect: Rect) -> Rect:
    """K4: cokgen -> eksen hizali, `rect.x/y` kadar kaydirilmis, duz `int` `Rect`."""
    try:
        noktalar = np.asarray(kutu, dtype=np.float64)
    except (TypeError, ValueError) as e:
        raise OcrError("cokgen sayisal diziye cevrilemedi") from e
    if noktalar.ndim != 2 or noktalar.shape[1] != 2 or noktalar.shape[0] < 1:
        raise OcrError(f"cokgen (k, 2) bicimli olmali, gelen shape={noktalar.shape}")
    if not bool(np.all(np.isfinite(noktalar))):
        raise OcrError("cokgen kosesi sonlu degil (NaN/inf)")
    x0 = math.floor(float(noktalar[:, 0].min()))
    y0 = math.floor(float(noktalar[:, 1].min()))
    x1 = math.ceil(float(noktalar[:, 0].max()))
    y1 = math.ceil(float(noktalar[:, 1].max()))
    return Rect(
        x=x0 + rect.x,
        y=y0 + rect.y,
        w=x1 - x0,
        h=y1 - y0,
        monitor_index=rect.monitor_index,
        dpi_scale=rect.dpi_scale,
    )


def _bloklara_cevir(cikti: object, rect: Rect) -> list[TextBlock]:
    """K4/K5: kutuphane ciktisi -> `TextBlock` listesi; bozuk bicim -> `OcrError`.

    Hata mesajlari yalniz tip/uzunluk tasir, blok METNI asla (K7).
    """
    try:
        boxes, txts, scores = cikti.boxes, cikti.txts, cikti.scores  # type: ignore[attr-defined]
    except AttributeError as e:
        raise OcrError(
            f"tanıyıcı ciktisi boxes/txts/scores alanlarini tasimiyor: {type(cikti).__name__}"
        ) from e

    try:
        if boxes is None:
            if txts is not None and len(txts) > 0:
                raise OcrError(f"kutusuz metin: boxes=None, txts uzunlugu {len(txts)}")
            return []
        if txts is None or scores is None:
            raise OcrError("boxes var ama txts/scores None")
        if isinstance(txts, (str, bytes)):
            raise OcrError(f"txts dizi olmali, gelen: {type(txts).__name__}")
        n = len(boxes)
        if len(txts) != n or len(scores) != n:
            raise OcrError(
                f"uzunluklar uyusmuyor: boxes={n}, txts={len(txts)}, scores={len(scores)}"
            )
    except TypeError as e:  # `len()` olmayan bir alan (skaler vb.)
        raise OcrError("boxes/txts/scores uzunlugu okunamadi") from e

    bloklar: list[TextBlock] = []
    for kutu, metin, puan in zip(boxes, txts, scores, strict=True):
        if not isinstance(metin, str):
            raise OcrError(f"metin str degil: {type(metin).__name__}")
        bloklar.append(
            TextBlock(text=metin, bbox=_cokgen_kutusu(kutu, rect), confidence=_puan(puan))
        )
    return bloklar


# ---------------------------------------------------------------------------
# motor
# ---------------------------------------------------------------------------


class RapidOcrEngine(OcrEngine):
    """Yerel ONNX OCR motoru -- `OcrEngine`'in v1 uygulamasi.

    Args:
        language: ZORUNLU tanima dili (K2). Uye ya da degeri; baska sey
            `ValueError`.
        threads: onnxruntime intra/inter is parcacigi sayisi (K3).
            `None` -> `min(8, cpu_count)`; `[1, cpu_count]` disi `ValueError`;
            tam sayi olmayan `TypeError`.
        allow_download: `False` (varsayilan) -> model dosyalari diskte olmali,
            yoksa `ModelMissingError`; `True` -> kutuphane indirir (K6).
            `bool` degilse `TypeError`.
        model_dir: model dizini; `None` -> kutuphanenin kendi `models/`
            dizini (K6). `str` de kabul edilir, `Path`e cevrilir.
        recognizer_factory: enjeksiyon dikisi (K1). `None` -> gercek
            kutuphane.

    Yapim kutuphaneye ve dosya sistemine DOKUNMAZ (K10); butun disaridan
    hatalar ilk `recognize`te dogar. Thread-safe DEGILDIR: tek worker
    thread'den kullanilir (tasarim 5.5).
    """

    def __init__(
        self,
        *,
        language: OcrLanguage,
        threads: int | None = None,
        allow_download: bool = False,
        model_dir: Path | None = None,
        recognizer_factory: TanıyıcıFabrikası | None = None,
    ) -> None:
        self._language = OcrLanguage(language)
        self._threads = _parcacik_sayisi(threads)
        if not isinstance(allow_download, bool):
            raise TypeError(f"allow_download bool olmali, gelen: {allow_download!r}")
        self._allow_download = allow_download
        self._model_dir: Path | None = None if model_dir is None else Path(model_dir)
        self._fabrika: TanıyıcıFabrikası = (
            recognizer_factory if recognizer_factory is not None else _varsayilan_fabrika
        )
        self._taniyici: Tanıyıcı | None = None
        self._kapali = False

    # -- gozlem -------------------------------------------------------------

    @property
    def language(self) -> OcrLanguage:
        return self._language

    @property
    def threads(self) -> int:
        """Duzlestirilmis, aralik icinde is parcacigi sayisi (K3)."""
        return self._threads

    def parametreler(self) -> dict[str, object]:
        """Fabrikaya gidecek `params` sozlugu -- her cagrida TAZE kopya.

        `allow_download=False` ise model dosyalarini denetler ve eksikte
        `ModelMissingError` firlatir (K6). Testler ve `real_check` bunu
        fabrikasiz da gozlemleyebilsin diye PUBLIC'tir (KARAR: paket
        sessizdi).
        """
        det_dil, rec_dil, rec_surumu = _dil_satiri(self._language)
        p: dict[str, object] = {
            "Global.text_score": 0.0,  # K5
            "Global.use_cls": False,  # K3 / O3
            "Global.log_level": "error",  # K7 (kurulum sirasi)
            "EngineConfig.onnxruntime.intra_op_num_threads": self._threads,  # K3
            "EngineConfig.onnxruntime.inter_op_num_threads": self._threads,  # K3
            "Det.engine_type": _MOTOR,  # K11
            "Det.ocr_version": _TESPIT_SURUMU,
            "Det.model_type": _MODEL_TIPI,
            "Det.lang_type": det_dil,
            "Rec.engine_type": _MOTOR,
            "Rec.ocr_version": rec_surumu,  # K11 / T-009 K1: dile ozel (KOREAN v5)
            "Rec.model_type": _MODEL_TIPI,
            "Rec.lang_type": rec_dil,
        }
        if self._allow_download:
            if self._model_dir is not None:
                p["Global.model_root_dir"] = self._model_dir
            return p

        dizin = self._model_dir if self._model_dir is not None else varsayilan_model_dizini()
        det_ad, rec_ad = beklenen_model_dosyalari(self._language)
        det_yol, rec_yol = dizin / det_ad, dizin / rec_ad
        eksik = [ad for ad, yol in ((det_ad, det_yol), (rec_ad, rec_yol)) if not yol.is_file()]
        if eksik:
            raise ModelMissingError(
                f"model dosyasi yok: {', '.join(eksik)} (dizin: {dizin}); "
                "allow_download=False oldugu icin indirilmedi"
            )
        p["Det.model_path"] = det_yol
        p["Rec.model_path"] = rec_yol
        return p

    # -- sozlesme -----------------------------------------------------------

    def recognize(self, frame: Frame, preset: OcrPreset) -> list[TextBlock]:
        """`frame` uzerinde OCR; sonuc ekran koordinatinda `TextBlock` listesi.

        `preset` KABUL EDILIR ama v1'de motoru DEGISTIRMEZ (K8): on ayar
        bazli olcekleme/kontrast on islemesi `[ÖLÇÜLMÜYOR]`, ayri gorev.

        Sira: kapali mi (K10) -> kare dogrulama (K6 c, motor cagrilmaz) ->
        tembel kurulum (K6 a, K10) -> tanıma (K6 b) -> donusum (K4/K5).

        Raises:
            OcrError: motor kapatilmissa; kurulum ya da tanıma kutuphane
                hatasi verdiyse; cikti bicimi bozuksa.
            ModelMissingError: `allow_download=False` ve model dosyasi yoksa
                (kutuphane cagrilmaz); indirme basarisizsa.
            ContractViolation: `frame.image` `(h, w, 3) uint8` ve pozitif
                boyutlu degilse; `frame.rect` alanlari duz `int` degilse.
        """
        if self._kapali:
            raise OcrError("motor kapatildi; close() sonrasi recognize cagrilamaz")
        _kareyi_dogrula(frame)
        taniyici = self._taniyici_al()
        try:
            cikti = taniyici(frame.image)
        except TranslatorError:
            raise
        except Exception as e:
            raise OcrError(f"tanıma basarisiz: {type(e).__name__}") from e
        return _bloklara_cevir(cikti, frame.rect)

    def close(self) -> None:
        """Tanıyıcıyı BIRAKIR (referans tutulmaz; weakref olu); idempotent.

        Sonrasi `recognize` -> `OcrError`, fabrika yeniden cagrilmaz (K10).
        Olcu: `test_k10_close_taniyiciyi_gercekten_birakir_weakref`.
        """
        self._taniyici = None
        self._kapali = True

    # -- ic yardimcilar ----------------------------------------------------

    def _taniyici_al(self) -> Tanıyıcı:
        """Tembel kurulum (K10) + kurulum hatasi siniflandirmasi (K6) + log (K7)."""
        if self._taniyici is not None:
            return self._taniyici
        params = self.parametreler()
        try:
            taniyici = self._fabrika(params)
        except TranslatorError:
            raise
        except FileNotFoundError as e:
            raise ModelMissingError("model dosyasi kurulum sirasinda bulunamadi") from e
        except Exception as e:
            raise OcrError(f"motor kurulamadi: {type(e).__name__}") from e
        # K7: kutuphane kurulumda seviyeyi sifirlar -> SONRA ceker.
        logging.getLogger(_LOGGER_ADI).setLevel(logging.ERROR)
        self._taniyici = taniyici
        return taniyici


# ---------------------------------------------------------------------------
# protokol uyum satiri -- mypy --strict bunu DOGRULAR
# ---------------------------------------------------------------------------

_uyum_fabrika: TanıyıcıFabrikası = _varsayilan_fabrika
