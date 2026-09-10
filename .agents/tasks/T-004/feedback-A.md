# Tester-A → Implementer · T-004 · TUR 5

**Mercek:** Garanti alanı. **Karar:** RET — **tek** bloke edici bulgu.

Kötü haber tek bir yerde. İyi haberi önce yazıyorum çünkü ne yapmayacağını
bilmen gerekiyor:

- **K23 bölümleme değişmezi kusursuz.** Kendi üreticimle (hyphen-yoğun,
  farklı tohum, farklı dağılım) 3200 girdi × 4 ön ayar = 12.800 koşum ve
  devraldığım 2520 girdilik derlem: **tek bir bölümleme farkı yok**. Miras da
  gerçekten tetikleniyor (8117 segmentin `speaker`'ı değişiyor), yani "0 fark"
  boş bir sonuç değil. İki-geçişli yapıyı **bozma** — değişmezi yapı gereği
  sağlıyor, mekanizmayla değil.
- `apply_inheritance` sızmıyor, `normalize`'ın imzası doğru, `tail` her
  durumda tanımlı, K5/K6/K7/K15/K16/K17/K18 regresyonu temiz.

---

## BULGU R5-1 · `yuksek` · `tail` "grubun son **HAM** öğesi" değil

**İhlal edilen:** K24 (*"sol taraf, kapanan grubun okuma sırasındaki **son
kaynak öğesidir** — birikmiş grubun birleşik `bbox`'ı **değil**"*) ve onun
üzerinden **K19 tablosu** (*"geometrik boşluk → `None` **kalır**"*).

**Yeniden üretim (tek komut):**

```
python .agents/tasks/T-004/tester_A/sonda_r5_bulgu.py
```

Ham çıktı: `tester_A_evidence/r5-bulgu-R5-1-sonda.txt`.
xfail maskesi kapalı assertion çıktısı:
`tester_A_evidence/r5-bulgu-R5-1-runxfail.txt`.

### Ne oluyor

`_group`'un `tail`'i, `_group`'a **giren** son öğedir. Ama `_group`'a giren
öğeler **ham blok değil**: adım 3 (`_merge_hyphenated`, K5) tire kuralıyla
birleşen blokları **tek** bir `_Item`'e indirir ve o öğenin `bbox`'ı bir
**birleşim**dir (`_union_rect`). Böyle bir öğe grubun `tail`'i olduğunda,
K24'ün `current` için kaldırdığı artifakt **aynen** geri gelir — bu kez
step-5 değil, **step-3** üzerinden.

`_merge_hyphenated` hiçbir geometrik kontrol yapmaz (K5 bilinçli olarak salt
tipografiktir), yani birleşik kutu istediği kadar büyüyebilir.

### Üç bağımsız geometrik yol — **ikisi monotonik**

Bunu vurguluyorum çünkü ilk bakışta "egzotik geometri" gibi görünüyor.
Değil: yolların ikisinde dikey uzanım okuma sırasına **tamamen uygun**
(`bottom` doğru!), tek başına `min(h)` / `overlap`+`min(w)` şişmesi yetiyor.

| Yol | Mekanizma | Monotonik | Ham son satırın verdiği sebep |
|---|---|---|---|
| **A** | birleşik kutunun `bottom`'u — ilk parça daha aşağı uzanıyor | hayır | `"gap"` |
| **B** | `min(h)` şişmesi — devam satırı **kısa** (`h=5`) | **evet** | `"gap"` |
| **C** | `overlap` + `min(w)` şişmesi — devam satırı **kaydırılmış/dar** | **evet** | `"overlap"` |

Yol B'nin birebir girdisi (dört blok, `dialogue`):

```python
TextBlock("Ada: " + "X"*130, Rect(0, -20, 240, 18), 0.9)
TextBlock("Y"*90 + " son-",  Rect(0,   0, 240, 18), 0.9)   # tire ile bitiyor
TextBlock("raki",            Rect(0,  30, 240,  5), 0.9)   # kucuk harf -> adim 3'te BIRLESIR
TextBlock("Z"*140,           Rect(0,  40, 240, 18), 0.9)
```

```
tail (adim 3'te birlesmis oge) : src=(1, 2)  bbox=(x=0, y=0,  w=240, h=35)   <- BIRLESIK, bottom=35
grubun HAM son metin satiri    :             bbox=(x=0, y=30, w=240, h=5)    <- bottom=35 (AYNI!)

sinir sebebi (current, nxt)                     : 'length'
KODUN sorgusu (tail, nxt, ignore_length=True)   : None    -> gap 5 < 0.8*min(35,18)=14.4  ARTIFAKT
K24 IFADESI   (ham son satir, ignore_length)    : 'gap'   -> gap 5 < 0.8*min( 5,18)= 4.0  GERCEK KOPUS

normalize()             : [((0,1,2),'Ada'), ((3,),'Ada')]   <- K19 tablosu IHLAL
beklenen                : [((0,1,2),'Ada'), ((3,), None )]
apply_inheritance=False : [((0,1,2),'Ada'), ((3,), None )]
```

`bottom` **doğru** (35 = 35). Ayrışmayı tek başına `min(h)` yapıyor: gerçek
son metin satırı 5 px yüksek, birleşik kutu 35 px. Eşik `0.8 × min(h)`
olduğu için birleşik kutu eşiği **3,5 kat** şişiriyor.

### Ölçüm — tek elle kurulmuş nokta değil

Makine denetimi: her uzunluk sınırında kodun `tail` sorgusu ile K24'ün
ifadesinin birebir okunuşu (grubun okuma sırasındaki **son ham bloğu**)
karşılaştırılıyor.

| | |
|---|---|
| Girdi (hyphen-yoğun üretici, 4 tohum) | 3200 |
| İncelenen uzunluk sınırı (3 gruplayan ön ayar) | **30.174** |
| **kod MİRAS VER / ham son satır MİRAS YOK** | **1561 (%5,2)** |
| — bunlardan **monotonik** (`bottom` artifaktı **yok**) | **1473** |
| kod MİRAS YOK / ham son satır MİRAS VER | 27 |
| **Uçtan uca `speaker`'ı yanlış çıkan segment** | **1004** |
| Etkilenen girdi | **383 / 3200** |
| **Bölümleme farkı** | **0** — K23 ihlal edilmiyor |

Karışık derlemde (`tester_A` içindeki testin kendi derlemi, tek tohum, 630
girdi) aynı denetim: 6552 sınırda **79** ihlal.

### Neden bloke edici

1. Docstring **koşulsuz** iddia ediyor: `_group` docstring'i `tail`'i *"grubun
   okuma-sirasindaki SON (birlesime en son katilan) **HAM** ogesi"* diye
   tanımlıyor ve K24 bölümü *"`tail` KULLANMAK bunu **ONLER**"* diyor. İkisi
   de bu girdi ailesi için **yanlış**. Benim merceğim tam olarak bu: koşulsuz
   iddia + dar geçerlilik — T-003'ün kırıldığı hata sınıfı.
2. Semptom, tur 3→4'te şefin **bloke edici** saydığı semptomun **aynısı**:
   *"MIRAS ALDI, ama arada gerçek geometrik kopuş var."* Aynı yasak (K19
   tablosu), aynı sonuç, farklı kapı.
3. K19'un gerekçesi: *"geometrik boşluk metnin kendisinden gelen bir sinyal;
   oraya konuşmacı atfetmek **uydurma** olur."* Kod 1004 segmentte uyduruyor.

### Ne yapmanı öneriyorum (karar şefin)

Şef K23'ü **değişmez** olarak yazdığında yöntemi değiştirdi. Aynı yöntem
burada da işe yarar; K24'ü **mekanizma** ("`tail` kullan") yerine **değişmez**
olarak okumak:

> Miras uygunluk sorgusunun **sol tarafının geometrisi**, grubun okuma
> sırasındaki **son ham OCR bloğunun** geometrisidir — hiçbir birleşimden
> geçmemiş olanı.

Uygulamanın en dar yolu: `_Item`'a birleşimden **etkilenmeyen** bir "son ham
blok geometrisi" taşımak (ör. `last_raw_bbox: Rect`) ve `_union_rect` ile
birleşen her yerde (`_merge_hyphenated` **ve** `_group`) bunu **sağdaki**
öğeden devralmak; K21'in `ignore_length=True` sorgusunda sol tarafa bu
`Rect`'i geçirmek. Sondamda referans boru hattını böyle kurdum
(`sonda_r5_bulgu.py` → `group_ref`) ve bölümleme farkı **0** çıktı, yani bu
düzeltme **K23'ü bozmuyor**.

Diğer dokunulan yer olmadan geçmesi gereken şeyler: `_should_group`'un dış
imzası, `_group_rejection_reason`'ın dönüş tipi ve `ignore_length`
verilmediğindeki davranışı, iki geçişli yapı, K15 matrisi, K16, K10'un
"birleşik bbox kapsayıcı dikdörtgendir" tanımı (`Segment.bbox` **değişmemeli**
— değişirse K23'ün `bbox` maddesi kırılır).

### Bu bulguyu bağlayan testler (`.agents/tasks/T-004/tester_A/`)

| Test | Durum |
|---|---|
| `test_r51_mekanizma_hyphen_birlesik_tail_ham_son_satirdan_ayrisiyor[A/B/C]` | **yeşil** — mekanizmayı sabitler (sorgu düzeyi) |
| `test_r51_kuyruk_gercek_geometrik_kopusun_otesine_speaker_atfetmiyor[A/B/C]` | `xfail(strict=True)` — uçtan uca beklenen davranış |
| `test_r51_makine_denetimi_ham_son_blok_kuralinda_sifir_ayrisma` | `xfail(strict=True)` — derlem geneli, 0 ayrışma bekler |

`strict=True` **kasıtlı**: düzelttiğinde bu dört test **XPASS ile kırılır** ve
işaretleri kaldırmak zorunda kalırsın. Bulgu sessizce kapanamaz.

---

## Bloke etmeyen, ama kaydedilmesini istediğim üç şey

1. **K24'ün zorunlu testi tek yönlü.** `tests/unit/ocr/test_normalizer.py::
   test_k24_kuyruk_ile_birlesik_bbox_farkli_sonuc_verir` yalnızca "birleşik
   kutu izin verir / `tail` reddeder" yönünü sınıyor. Ters yön yok — bu
   yüzden `current` kullanan bir kod bile o testi geçebilir. Ters yönü kendi
   paketimde ekledim (`test_k24_ayrisma_yonu_2_...`); `tests/` altında da
   durması iyi olur.
2. **Zincirleme miras lehine hiçbir test yok.** `_group` docstring'i soldan
   sağa geçişin zincirlemeyi kasıtlı olarak mümkün kıldığını söylüyor ve
   "hiçbir mevcut test bunun tersini beklemiyor" diyor — ama **lehine** de
   test yok, yani ileride sessizce kaybolabilir. Dört öğeli monologda kendi
   paketimde sabitledim.
3. **`_merge_hyphenated` geometriye hiç bakmıyor.** Belgeli ve bu turda karar
   konusu değil; ama R5-1'in kökü burada. 400 px arayla duran iki blok da,
   biri tire ile bitip diğeri küçük harfle başlıyorsa tek öğe oluyor ve o
   öğenin birleşik kutusu **grup kararlarına** giriyor. K24'ü değişmez olarak
   okursan bu ayrıca bir karar gerektirmez; mekanizma olarak okursan
   gerektirir.
