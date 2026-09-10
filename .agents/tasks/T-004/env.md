# Koşum Ortamı — T-004

Ortam Ajanı ürünü. **Üç tester** var; her biri farklı mercekle çalışır ve **kendi raporunu ayrı yazar**. Birleştirilmiş özet yoktur.

## Doğrulanmış ortam

| | |
|---|---|
| Python | 3.12.10 · pytest 9.1.1 · mypy · numpy 2.4.6 |
| Çalışma dizini | depo kökü |

Ağ, GPU, ekran gerektirmez — hedef modül tamamen saf fonksiyonlardan oluşur.

## Koşum komutları

```bash
python -m mypy --strict src/ocr/normalizer.py src/ocr/presets.py
python -m pytest tests/unit/ocr/test_normalizer.py -q
python .agents/tasks/T-004/purity_check.py
```

Kendi testlerin:
```bash
python -m pytest .agents/tasks/T-004/tester_<MERCEK>/ -q
```

## Okumaman gerekenler

- `.agents/tasks/T-004/delivery.md` — **okuma**
- `.agents/tasks/T-004/evidence/` — **okuma**
- `.agents/tasks/T-004/iptal-tur0/` — **okuma** (iptal edilmiş turun kodu, yanlış varsayımlar içerir)
- Diğer tester'ların `tester_*` dizinleri — **okuma**, bağımsızlığını bozar

Okuyacakların: `packet.md` (14 şef kararı burada), bu dosya, `src/ocr/normalizer.py`, `src/ocr/presets.py`, `tests/unit/ocr/test_normalizer.py`, `src/contracts/models.py`, tasarım dokümanı §5.2 / §3.2.

## Şefin notu — tur 1 harness hatası

Implementer `status: kismi` bildirdi çünkü `purity_check.py` çıkış 1 veriyordu. Sebep implementer'ın kodu **değil**, şefin yazdığı harness dosyasındaki bir hataydı (`OcrPreset.dialogue` yerine `OcrPreset.DIALOGUE` olmalıydı). Şef düzeltti; üç kabul komutu da artık geçiyor. Implementer sahte geçiş iddia etmeyip dürüst raporladığı için bu bir kusur sayılmaz.

---

# TUR 5 — ne değişti, neye bakılacak

Tur 4'te implementer K21/K22'yi doğru uyguladı, ama **karar kırmızı takımı** şefin kararlarında 12 bulgu çıkardı (3 yüksek). Şef üçünü de yeniden üretti. `sef_karari-tur5.md` içinde K23–K27; **oku**.

En kritiği **K23 — bir değişmez, mekanizma değil:** *miras, bölümlemeyi değiştiremez.* `source_blocks` dizisi miras açıkken ve kapalıyken birebir aynı olmalı; miras yalnızca `speaker`'ı değiştirebilir.

| Karar | Ne değişti |
|---|---|
| **K23** | `_group` iki geçişe bölündü: (1) bölümleme — yalnızca özgün OCR `speaker` değerleriyle, hiç mutasyon yok; (2) görünüm — bölümleme bittikten sonra sadece `speaker` güncellenir, gruplamaya geri beslenmez. Test kancası: `_normalize_impl(blocks, preset, *, apply_inheritance=True)`; `normalize` buna sabit `True` ile delege eder |
| **K24** | Miras-uygunluk sorgusu (`ignore_length=True` ikinci çağrı) artık `tail` (grubun **son ham öğesi**) ile yapılıyor, `current` (birleşik bbox) ile değil — birleşik kutu gerçek boşluğu yanlış ölçüyordu |
| **K25** | Seçenek 1 (`ignore_length` parametresi) korundu |
| **K26** | K22'nin olgusal hatası düzeltildi: altı karakterin **altısı da** uyumluluk formu (2×`<wide>`, 2×`<small>`, 2×`<vertical>`) |
| **K27** | `menu` ön ayarı K19/K21/K23 kapsamı dışı — açıkça belgelendi |

Şef, B1 senaryosunu kendi eliyle sınadı: tur 4'te `(2,3)` birleşiyordu, şimdi `(2,),(3,)` ayrı ve miras açık/kapalı bölümleme birebir aynı.

## Tur 5 mercekleri — tur 4 kırmızı takımının önerdiği sekiz maddeden

**A · Garanti alanı**
- **Bölümleme kararlılığı (K23):** implementer'ın 2500 girdilik denetimine güvenme, **kendi** üreticinle (farklı tohum, farklı geometri dağılımı) sına. Özellikle: 3+ konuşmacı zinciri, iç içe uzunluk+geometri bölünmeleri, aynı `y`'de yan yana bloklar, `h` çok küçük bloklar.
- **`apply_inheritance` bayrağının alanı:** `False` iken çıktı, hiç miras mekanizması olmasaydı üretilecek çıktıyla **birebir** aynı mı? Yoksa bayrak yalnızca son adımı mı atlıyor?
- **`_normalize_impl` sızıntısı:** genel API'ye çıkmış mı? `__all__`'da var mı? `normalize`'ın imzası değişmiş mi?
- **K24 "son ham öğe" alanı:** `tail` her zaman tanımlı mı — tek öğeli grup, ilk grup, boş grup? `tail` ile `current` hangi geometrilerde ayrışıyor, hangilerinde aynı?

**B · Karar uyumu**
- **K1–K27, yirmi yedi kararın tamamı**, tek tek. Özellikle K23'ün iki-geçiş yapısı gerçekten kodda var mı — yoksa tek geçişte "mutasyon yapmadan" taklit mi ediliyor?
- **`_should_group` ↔ `_group_rejection_reason` ayrışmazlığı** hâlâ tek satırlık devretme mi?
- **`speaker`-önce sırası** korunmuş mu?
- **Reason kodları** (`ignore_length` verilmeden) tur 3–4 ile birebir aynı mı?
- **Docstring ofset testleri** (tur 3 tester_B) hâlâ yeşil mi — docstring büyüdü.

**C · Sınır, kötü kullanım, dil**
- **B1 Japonca'da:** `勇者：` etiketli uzun replik + hemen ardından yeni `勇者：` etiketli replik — iki sözce ayrı mı kalıyor? Üç konuşmacılı zincir (`勇者`/`魔王`/`村人`) ile.
- **Görünüm geçişinin CJK yüzeyi:** miras, `speaker` alanına özgün string'i mi kopyalıyor yoksa normalize edilmiş bir kopyasını mı? Fullwidth ayraçlı etiket miras alındığında bozuluyor mu?
- **Kötü kullanım:** `_normalize_impl` bir sonraki ajanı doğrudan çağırmaya davet ediyor mu? `apply_inheritance=False` "üretimde kullanma" diye işaretli mi?
- **Ölçek:** n=500/1000/2000 — iki-geçiş yapısı ölçeği kötüleştirdi mi? Tur 4: 2.744/7.032/20.138 ms.

---

# TUR 3 — ne değişti, neye bakılacak

Tur 2'de **üçü de onay verdi.** Şef, Tester-C'nin "bloke etmeyen" saydığı iki nottan birini **yeniden sınıflandırdı**; ikisi de düzeltildi. `sef_karari-tur3.md` içinde K19 ve K20 var; **oku**.

| Karar | Ne değişti |
|---|---|
| **K19** | *Davranış.* Grup `max_group_chars` yüzünden bölündüğünde kuyruk segment konuşmacıyı **miras alır**. Geometrik boşluk / farklı konuşmacı / yozlaşmış bbox yüzünden bölündüyse `None` **kalır**. Uygulama: `_group_rejection_reason()` sebebi döndürüyor, `_should_group` tek satırlık devredici oldu |
| **K20** | *Salt dokümantasyon.* NFKC iddiası olgusal olarak yanlıştı ("başka hiçbir karakter açılmaz") — altı karakterin tam listesiyle değiştirildi. **Kod değişmedi.** |

**Bu turda iki mercek koşuyor, üç değil.** Tester-A koşmuyor: garanti-alanı merceği tur 2'de ızgara + fuzz ile tükendi ve K19/K20 yeni garanti alanı açmıyor (K20 mevcut iddiayı **daraltıyor**). Gerekçe `sef_karari-tur3.md`'de. PROTOKOL §4.5'e eklenen kural: azaltma yalnızca şefin yetkisinde ve gerekçesi yazılmak zorunda.

## En yüksek regresyon riski

K19 **gruplama yoluna dokunuyor** — K15 matrisinin beş satırı ve K16'nın yozlaşmış geometri reddi aynı fonksiyonda. Özellikle:

- `_should_group` ile `_group_rejection_reason` **birbiriyle tutarlı mı**? İkisi ayrışırsa miras yanlış yerde tetiklenir.
- Miras yalnızca `"length"` sebebinde mi çalışıyor, yoksa başka sebeplere de sızmış mı?
- `X/Y` (iki farklı konuşmacı) durumunda miras **kesinlikle** olmamalı — olursa K9'un asıl yasağı çiğnenir.

---

# TUR 2 — ne değişti, neye bakılacak

Tur 1'de **A ve C reddetti, B onay verdi.** Dört bloke edici bulgu düzeltildi. Şef kararları `sef_karari-tur2.md` içinde (K15–K18); onu **oku**.

| Karar | Ne değişti |
|---|---|
| **K15** | `_should_group`'daki konuşmacı kontrolü. `speaker=None` artık "farklı konuşmacı" değil, **"devam"** demek. Beş satırlık tablo: X/X evet · X/None evet (miras) · None/None evet · None/Y hayır · X/Y hayır |
| **K16** | `ref_height <= 0` (ve `ref_width <= 0`) olduğunda gruplama **koşulsuz reddediliyor**, `gap` değerine bakılmıyor |
| **K17** | Konuşmacı ayracı kümesi `presets.py`'de adlandırılmış sabit: `:` ve `：` (U+FF1A) |
| **K18** | Tek-karakter `?`/`!` istisnası artık **NFKC normalizasyonuna** göre — `？`/`！` otomatik kapsanıyor |

**K15, K9'un davranışını değiştirdi.** Yani tur 1'de doğrulanmış olan konuşmacı-sınırı davranışı artık farklı bir kural kümesine tabi — yeniden doğrulanmalı.

## Tur 2'de her mercek şunu ekleyecek

**Regresyon avı birinci öncelik.** Tur 1'de üç tester bağımsız olarak şunları sınadı ve hepsi ayakta kaldı; düzeltme bunlardan birini bozduysa bu bloke edicidir:

K7 confidence (`NaN`→`ValueError`, tam eşik korunur) · K6 yer tutucu (tekrar/sıra, `"50%"` vs `"50%s"`) · K5 hyphen (`well-known` korunur, `keli-\nme` birleşir, Unicode tire varyantları dışlanır) · K8 `source_blocks` orijinal indeks uzayı · K4 sınıf tabanlı tek karakter (kanji/hangul/Kiril/Devanagari korunur) · K10 `bbox` `ValueError` · K14 bütçe assertion'ı · K13 süreçler arası determinizm · **asıl iş** (hyphen'siz bölünmüş cümle dialogue/tooltip/subtitle'da birleşir, menu'de birleşmez) · K12 boş sonuçlar

**K15 tablosunun beş satırı da ayrı ayrı sınanacak** — özellikle `None/Y` (yeni konuşmacı başlıyor, birleşmemeli) ve `X/Y` (iki farklı konuşmacı, asla birleşmemeli). K15'in düzeltmesi bu iki satırı gevşetmiş olabilir; gevşettiyse iki farklı kişinin repliği birleşir ve bu K9'un asıl yasakladığı şeydir.

**Yeni yüzey:** K17'nin ayraç kümesi ve K18'in NFKC kuralı yeni kod yolları. Bunların kendi sınırları var — örneğin metnin **ortasında** geçen `：`, birden çok ayraç, ayraçla başlayan blok, NFKC'nin `?`/`!` dışında neyi eşlediği.

---

# Üç mercek

Bu paket bir kırmızı takım denetiminden geçti ve 19 belirsizlik düzeltildi. Mercekler, **düzeltilmiş paketin hâlâ geçirebileceği** hatalara göre seçildi.

## MERCEK A — Garanti alanı

*"Docstring ne söz veriyor ve bu söz, fonksiyonun kabul ettiği **her** girdi için tutuyor mu?"*

Bu, T-003'ün kırıldığı hata sınıfı: koşulsuz iddia, dar geçerlilik.

1. **`confidence` alanı (K7).** `NaN`, `-0.5`, `1.5`, `inf` ve **tam eşik değeri**. K7 diyor ki: `< threshold` düşer, `== threshold` **kalır**, `NaN`/alan dışı → `ValueError`. Kod bunu yapıyor mu? `NaN` ile `if c < th` **düşürmez** (NaN karşılaştırması daima False) — kod hangi biçimi kullanmış?
2. **Yer tutucu semantiği (K6).** `"%s ve %s"` (tekrar), `"50%"` ile `"50%s"` (çakışma), bitişik `"{0}{1}"`, satır sınırına bölünmüş `{0}`. `placeholders` sıralı ve **tekrarlı** mı? `text` orijinali **birebir** koruyor mu? Sayılar `placeholders`'a **girmiyor** mu?
3. **Yozlaşmış bbox (K10, paket "yozlaşmış girdiler" bölümü).** `h == 0`, `w == 0`, negatif `w`/`h`. Satır yüksekliğine bölen bir formül varsa `h == 0` çöker. Docstring bu girdiler için ne iddia ediyor, kod onu mu yapıyor?
4. **Hyphen alanı (K5).** `well-known` (satır ortası tire) korunuyor mu? `keli-\nme` birleşiyor mu? Sonraki satır **büyük** harfle başlıyorsa ne oluyor? Unicode tire çeşitleri (`‐`, `–`, `—`) kapsamda mı, docstring bunu söylüyor mu?
5. **Saflık ve determinizm.** `purity_check.py`'den bağımsız olarak kendi yönteminle sına: aynı girdiyle art arda iki çağrı bit-bit aynı mı? Çağrılar arası önbellek var mı?

## MERCEK B — Karar uyumu

*"Paketteki 14 şef kararı kodda gerçekten var mı, birebir mi?"*

Paket kararları numaralandırdı. Her birini koda karşı **tek tek** doğrula. Kararla kod arasındaki her sapma bulgudur.

1. **K2 işlem sırası.** Bölünmüş bir cümlenin **ortasına** eşik altı bir blok koy. Sıra `eşik → gürültü → birleştirme → konuşmacı → gruplama → yer tutucu` ise sonuç şu olmalı; kod o sırayı mı uyguluyor? Docstring hangi sırayı iddia ediyor?
2. **K1 satır tanımı.** Aynı metni üç biçimde ver: (a) satır başına bir `TextBlock`, (b) tek blok + dolu `line_boxes`, (c) tek blok + `text` içinde `\n`. Üçünde de aynı segment mi çıkıyor? `line_boxes == ()` çöküyor mu?
3. **K8 `source_blocks` indeks uzayı.** Girdinin **başına** eşik altı bir blok koy. Kalan segmentin `source_blocks`'u kaydı mı (filtre sonrası uzay — **yanlış**) yoksa orijinal indeksi mi koruyor? Artan mı, tekrarsız mı, boş olmayan mı? İki segmentin kümeleri **ayrık** mı?
4. **K9 konuşmacı sınırı.** `dialogue`'da iki **farklı** konuşmacılı komşu blok tek segmentte birleşip ikinci konuşmacıyı yutuyor mu? Yalnız `"Ada:"` içeren blok ne üretiyor — `text=""` olan bir `Segment` sızıyor mu? K9 bunu **kesin olarak yasaklıyor**.
5. **K3 çıktı sırası.** Blokları karışık sırada ver. Segmentler `bbox.y` artan, eşitlikte `bbox.x` artan mı dönüyor?
6. **K11 ön ayar davranışı.** `dialogue`/`tooltip`/`subtitle` **gruplar**, `menu` **gruplamaz**. Dördü de aynı girdide gerçekten farklı mı davranıyor, yoksa `tooltip`/`subtitle` yalnızca isim mi?
7. **K12 boş sonuçlar.** Boş girdi → `[]`? Hepsi eşik altında → `[]`? Kurtarma/gevşetme yapılmıyor mu?
8. **K14 bütçe.** Ölçüm test dosyasında **`assert`** olarak mı duruyor, yoksa yalnızca `evidence/` altında bir sayı mı? Assertion'ı geçici olarak imkânsız bir eşikle zorla — gerçekten kırılıyor mu?

## MERCEK C — Sınır, kötü kullanım ve dil

*"Bu API bir sonraki ajanı hangi yanlışa davet ediyor, ve Latin dışı metinde ne oluyor?"*

1. **CJK tek karakter (K4).** Tek kanji (`力`, `火`, `東`), tek hangul (`한`), tek hiragana (`あ`). K4 diyor ki karar **Unicode sınıfına** göre verilecek, beyaz liste **yasak**. Kod liste mi kullanmış sınıf mı? Tek kanjili blok siliniyor mu? — Bu, sessizce Japonca oyun metnini yok eden hata sınıfı.
2. **Karışık script.** Aynı blokta Japonca + Latin, RTL karakterler, emoji, sıfır genişlikli birleştirici, kombine aksan. Çökme veya sessiz saçmalık var mı?
3. **`bbox` birleşimi (K10).** Farklı `monitor_index` / farklı `dpi_scale` taşıyan iki blok → K10 `ValueError` diyor. Kod sessizce ilkinden mi kopyalıyor?
4. **Kötü kullanım.** Bir sonraki ajan (OCR motoru, pipeline) bu API'yi kullanırken hangi yanlışı yapmaya davet ediliyor? Yanıltıcı isim, belgelenmemiş zorunlu çağrı sırası, sessizce yanlış sonuç döndüren çağrı biçimi, kolay yanlış anlaşılan varsayılan?
5. **Ölçek.** 1 blok · 500 blok · 10.000 karakterlik tek blok · hepsi aynı `bbox`'ta üst üste binen bloklar. Çökme, kuadratik yavaşlama veya bellek patlaması var mı?
6. **`presets.py` genişletilebilirliği.** Paket, `ölçekleme faktörü` ve `kontrast ön işlemesi` alanlarının sonraki göreve bırakıldığını söylüyor. Yapı bu genişlemeyi kaldırıyor mu, yoksa sonraki ajan dosyayı yeniden mi yazmak zorunda kalacak?
