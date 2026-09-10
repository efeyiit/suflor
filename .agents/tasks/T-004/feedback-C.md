# Tester-C Feedback -- T-004, Tur 3

Mercek: sinir, kotu kullanim ve dil. Karar: **RET**.

K19 ve K20'nin kendileri **dogru uygulanmis**. Ret, K19'un mekanizmasindaki
(daha once hic test edilmemis) bir **sinir durumuna** dayaniyor -- iki ayri
"bloke etmeyen" gozlem de asagida ayrica not edildi.

---

## BLOKE EDICI BULGU -- `_group_rejection_reason` oncelik sirasi, K19'un
kendi tablosunu ihlal ediyor (uzunluk + geometri AYNI ANDA)

### Neyi test ettim

Gorev tanimi K19 icin acikca "uzunluk VE geometrik bolunme ayni zincirde
ARKA ARKAYA olursa ne oluyor" sorusunu sordu. Ardisik ciftleri test ederken
(bkz. `tester_C/test_cjk_misuse_scale.py::test_k19_uzunluk_sonra_geometrik_
bolunme_ZINCIR_KOPAR` -- bu DOGRU calisiyor, zincir dogru kopuyor) daha ilginc
bir varyant buldum: **AYNI ciftte, AYNI ANDA hem uzunluk siniri hem gercek
bir geometrik sinir** varsa ne oluyor?

`_group_rejection_reason` (normalizer.py satir 774-793) kontrolleri SABIT
bir oncelik sirasinda calistirir: `speaker` -> `length` -> `height` -> `gap`
-> `width` -> `overlap`, ve YALNIZ ILK basarisiz kontrolun reason kodunu
dondurur. `length`, TUM geometrik kontrollerden ONCE gelir.

### Somut repro

```
Ada: + (cap-5 karakterlik govde, etikete cok yakin -- henuz asmiyor)
     + (50 karakterlik govde, ONCEKINDEN 500+ piksel asagida -- GERCEK,
        buyuk bir dikey bosluk, max_vertical_gap_ratio esiginin COK
        uzerinde)

Kontrol: bu son cift, uzunluk siniri devre disi birakilsa (KISA metinlerle
test edilse) bile YINE reddedilir -- yani aralarinda GERCEK, uzunluktan
BAGIMSIZ bir geometrik kopus var (_group_rejection_reason -> "gap").

Ama gercek (uzun) metinle: _group_rejection_reason -> "length" (gap
kontrolune HIC ulasilmiyor, cunku length daha ONCE kontrol ediliyor ve
o cift zaten uzunlugu da asiyor). K19 bu yuzden YANLISLIKLA miras
uyguluyor: son parca "Ada" olarak etiketleniyor.
```

Ayni durum K16'nin yozlasmis-yukseklik (`ref_height<=0`) kosulu icin de
gecerli -- `height` kontrolu de `length`'ten SONRA calisiyor.

Ikisi de `tester_C/test_cjk_misuse_scale.py` bolum 14'te testlerle
sabitlendi (`test_BULGU_BLOKE_EDICI_k19_uzunluk_VE_buyuk_geometrik_
bosluk_AYNI_ANDA_ise_YANLISLIKLA_miras_alir`,
`test_BULGU_BLOKE_EDICI_k19_uzunluk_VE_yozlasmis_yukseklik_AYNI_ANDA_ise_
YANLISLIKLA_miras_alir`) -- her ikisi de su an YESIL (mevcut, hatali
davranisi PIN ediyor, ayrintili repro icin `tester_C_evidence/r3-k19-
compound-reason-repro*.py/.txt` ve `r3-k19-compound-gap-repro*.py/.txt`).

### Neden bloke edici

sef_karari-tur3.md'nin K19 tablosu:

| Bolunme sebebi | Kuyruk segmentin `speaker` degeri |
|---|---|
| `max_group_chars` asildi | **MIRAS ALIR** |
| Geometrik bosluk / farkli `speaker` / yozlasmis bbox | **`None` kalir** |

Yukaridaki senaryoda bolunmenin GERCEK sebebi GEOMETRIK BOSLUKTUR -- uzunluk
siniri kalksa/buyutulse bile bu iki parca YINE birlesmezdi (kontrol testim
bunu kanitliyor: kisa metinle bile reddediliyor). Ama kod `"length"`
reason'ina rastladigi icin (SIRALAMA kazasi, geometri kontrolune hic
BAKILMADAN) miras uyguluyor. Bu, tablonun ikinci satirinin (`None kalir`)
DOGRUDAN ihlalidir.

Daha da onemlisi, bu K19'un KENDI gerekcesini gecersiz kilan bir durumda
oluyor: K19'un mirasi haklı cikaran gerekce "`max_group_chars` BIZIM
koydugumuz YAPAY bir sinir, metnin KENDISINDE bir kopus YOK" idi. Ama bu
senaryoda metnin/geometrinin KENDISINDE GERCEK bir kopus VAR (500+ piksellik
bosluk) -- yapay sinir GERCEK sinirin ustune BINIYOR ve kod ikisini ayirt
edemiyor.

Pratik etki: uzun bir replik, konusmaci karakter sinirina (max_group_chars)
YAKIN bir noktada biterken, konusmaciyla HICBIR ILGISI OLMAYAN, cok
uzaktaki (ör. yeni bir diyalog kutusu, sahne gecisi, farkli bir UI ogesi)
bir blok YANLISLIKLA ayni konusmaciya atfedilir. Bu TAM OLARAK S5.2'nin/
sef_karari-tur3.md'nin K19'u yaratma gerekcesi olan hata sinifi (Japonca
gibi dillerde yanlis zamir/hitap secimi), ama TERS yonde: K19 SESSIZ
KAYBI (round 2 bulgusu) SESSIZ UYDURMAYA (bu bulgu) cevirdi -- ayni
karakter icin bir speaker daha ONCE HIC atfedilmiyordu, simdi YANLIS
atfediliyor. Ikisi de sessiz ve gercek.

### Onerilen duzeltme (sef'e birakiyorum, dar ve iyi tanimli)

`_group_rejection_reason`'da geometrik kontrolleri (`height`/`gap`/`width`/
`overlap`) `length`'ten ONCE calistirmak -- yani bir cift AYNI ANDA hem
uzunluk hem geometri tarafindan reddediliyorsa reason bir geometrik kod
olsun, `"length"` degil. Bu, K19'un `reason == "length"` kontrolunu
DEGISTIRMEDEN (mekanizma ayni kalir), yalniz reason'in DOGRU (ilk/gercek)
sebebi yansitmasini saglar. Kucuk, izole bir degisiklik -- `_should_group`
davranisini (bool sonucu) ETKILEMEZ, yalniz K19'un HANGI reason'a
baktigini duzeltir.

---

## Bloke etmeyen gozlem -- K20 docstring'inde kucuk bir ifade tutarsizligi

`normalizer.py` satir ~98-103: *"ASCII/fullwidth DISINDA ALTI karakter
daha buldu"* diyor, ama hemen altindaki listenin ICINDE U+FF01 VE U+FF1F
(fullwidth unlem/soru) VAR -- yani "fullwidth disinda" ifadesiyle "fullwidth
listenin icinde" birbiriyle CELISIYOR. sef_karari-tur3.md'nin kendi metni
sadece *"ASCII disi alti karakter"* diyor (fullwidth'i haric TUTMUYOR),
implementer'in eklemis oldugu "/fullwidth" ifadesi FAZLADAN ve YANLIS.

Bagimsiz tam Unicode taramam (satir bazinda `tester_C_evidence/r3-nfkc-
scan.txt`, testte `test_k20_bagimsiz_tam_unicode_taramasi_docstringteki_
alti_karakterle_TAM_ORTUSUR`) alti karakterin KENDISININ (liste + eslenen
karakterler) **tamamen dogru ve eksiksiz** oldugunu kanitliyor -- yalniz
bu bir GEÇİŞ CÜMLESİNİN ifadesi, asil garanti (liste + "kod NFKC ile
karar verir, liste bilgi amaclidir") ETKILENMIYOR. Bloke etmiyorum cunku
(a) liste + davranis %100 dogru, (b) okuyan listenin kendisini okudugunda
celiski kendiliginden cozuluyor. Ama K20'nin TUM amaci "docstring'in
olgusal ifadesini duzelt" oldugu icin, ayni duzeltmenin icine yeni bir
ifade belirsizligi sizmis olmasi ironik -- kucuk bir kelime duzeltmesiyle
("ASCII/fullwidth DISINDA" -> "ASCII DISINDA") giderilebilir.

---

## Regresyon: bulunmadi

Round 2'nin tam test bataryasi (K4 sinif-tabanli tek karakter/11 yazi
sistemi, karisik script/RTL/emoji-ZWJ/kombine aksan, K10 `bbox`
`ValueError`, K17 ayrac kumesi, K18 NFKC istisnasi, presets
genisletilebilirligi) YENIDEN kosuldu -- yalniz K19'un DOGRUDAN duzelttigi
tek test (round 2'nin "YENI_BULGU" testi) beklendigi gibi TERS CEVRILDI
(artik DUZELTILMIS davranisi dogruluyor); geri kalan HERSEY degismeden
gecti.

## Olcek: kotulesmedi

n=500/1000/2000 icin TUR 3 medyanlari (3.673/9.234/26.461 ms) TUR 2'nin
degerlerine (3.443/9.271/27.069 ms) COK yakin (%1-3 fark, olcum
gurultusu). K19'un ekledigi ekstra fonksiyon cagrisi olculebilir bir
kotulesmeye yol acmamis. Ayrinti: `tester_C_evidence/r3-scale_timing.txt`.

## `speaker`'in yeni anlami: belgeleniyor

K19 sonrasi `Segment.speaker=None` iki farkli anlam tasiyabiliyor
("etiket yok" / "bilinmiyor-atfedilemez") ve normalizer.py docstring'i
(K19 bolumu son paragraf) bu ikisini ACIKCA, ayri maddeler halinde
ayiriyor -- bu iyi. Yukaridaki bloke edici bulgu bu ayrimin KENDISIYLE
ilgili degil; ayrimin DOGRU UYGULANIP UYGULANMADIGIYLA ilgili (compound
durumda "bilinmiyor" kategorisine girmesi gereken bir segment yanlislikla
"biliniyor (Ada)" kategorisine dusuyor).
