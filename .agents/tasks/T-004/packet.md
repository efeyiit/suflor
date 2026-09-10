---
task: T-004
title: "TextNormalizer: satır birleştirme, gürültü eleme, gruplama, yer tutucu koruma"
role: implementer
level: B
wave: 2
owns:
  - "src/ocr/normalizer.py"
  - "src/ocr/presets.py"
  - "tests/unit/ocr/test_normalizer.py"
forbidden:
  - "src/contracts/**"
  - "src/ocr/__init__.py"
  - "src/capture/**"
  - "tests/unit/contracts/**"
  - "tests/unit/capture/**"
  - ".agents/tasks/T-004/iptal-tur0/**"
  - "diğer tüm dizinler"
depends_on: ["T-001"]
acceptance:
  - "python -m mypy --strict src/ocr/normalizer.py src/ocr/presets.py"
  - "python -m pytest tests/unit/ocr/test_normalizer.py -q"
  - "python .agents/tasks/T-004/purity_check.py"
budget_ms: 5
---

# Görev

Tasarım dokümanı §5.2: **"Çeviri kalitesinin yarısı burada belirlenir."** OCR iki satıra bölünmüş bir cümle verir; ayrı ayrı çevirirsek sonuç bozuk çıkar.

`docs/superpowers/specs/2026-09-09-suflor-design.md` §5.2 ve §3.2'yi **oku**.

> **Bu paket bir kırmızı takım denetiminden geçti.** İlk sürümünde 19 belirsizlik bulundu (11'i yüksek şiddetli) ve o sürümle başlatılan tur iptal edildi. Aşağıdaki kararlar artık **şef tarafından verilmiştir** — senin uydurmana bırakılmamıştır. Bir kararı teknik olarak imkânsız buluyorsan uygula deme, `known_gaps` altında bildir.
>
> `iptal-tur0/` dizininde iptal edilen turun kodu duruyor. **Okuma ve kullanma** — yanlış varsayımlar içeriyor, seni yanıltır.

## Yazılacak

**`src/ocr/normalizer.py`**

```
normalize(blocks: Sequence[TextBlock], preset: OcrPreset) -> list[Segment]
```

**`src/ocr/presets.py`** — ön ayar başına parametreler.

Dondurulmuş sözleşmeler (`src/contracts/models.py`) — **kullan, değiştirme**:

```
TextBlock(text: str, bbox: Rect, confidence: float, line_boxes: tuple[Rect,...] = ())
Segment(text: str, bbox: Rect, speaker: str|None = None,
        placeholders: tuple[str,...] = (), source_blocks: tuple[int,...] = ())
Rect(x, y, w, h, monitor_index=0, dpi_scale=1.0)  + right, bottom (property)
OcrPreset: dialogue | menu | tooltip | subtitle
```

---

# ŞEFİN VERDİĞİ KARARLAR

Bunlar tartışmaya kapalıdır. Her biri, açık bırakıldığında iki farklı ve savunulabilir uygulamaya yol açtığı için sabitlenmiştir.

## K1 · "Satır" nedir

Bu bileşende **satır = bir `TextBlock`**. OCR motoru satır başına bir blok döndürür; birleştirme **bloklar arası** yapılır.

`line_boxes` doluysa blok-içi satır geometrisi için kullanılabilir ama **zorunlu değildir**. `line_boxes == ()` (sözleşme varsayılanı) her zaman geçerli girdidir ve davranışı değiştirmez.

`text` içinde `\n` geçerse: satırlara böl, aynı blok-içi birleştirme kurallarını uygula, tek `Segment`'e indir.

## K2 · İşlem sırası — değiştirilemez

```
1. güven eşiği filtresi
2. gürültü eleme
3. satır birleştirme + hyphen çözme
4. konuşmacı ayıklama
5. gruplama (ön ayara göre)
6. yer tutucu toplama
```

Sıra çıktıyı değiştirdiği için sabitlenmiştir. Farklı bir sıra teknik olarak zorunluysa `known_gaps` altında gerekçelendir; kendi başına değiştirme.

## K3 · Çıktı sırası

Segmentler **okuma sırasında** döner: `bbox.y` artan, eşitlikte `bbox.x` artan. Girdi blokları sırasız gelebilir; sıralamayı sen yaparsın.

`source_blocks` içindeki indeksler de **artan** sırada.

## K4 · Tek karakter kararı — sınıf tabanlı, liste tabanlı değil

Unicode kategorisi **harf (`L*`) veya rakam (`N*`)** olan tek karakterler **her zaman korunur.** Bu, tek-kanji (`力`, `火`) ve tek-hangul metni güvenceye alır.

Yalnızca **sembol/noktalama** (`S*`, `P*`) sınıfındaki tek karakterler atılır. `?` ve `!` bu kuralın belgelenmiş **istisnasıdır** — korunur.

**Beyaz liste yasak.** `{"I","a","1","?"}` gibi bir küme yazarsan tek karakterli her CJK metni silinir ve testlerin bunu göremez.

## K5 · Hyphen kuralı — dilden bağımsız, geometrik/tipografik

`normalize` dil bilgisi almaz ve **alamaz** (sözleşme dondurulmuş, `OcrPreset` metin türüdür, dil değil).

Kural: tire **satırın son karakteriyse** ve sonraki satır **küçük harfle** başlıyorsa → birleştir, tireyi düş. Tire satır ortasındaysa (`well-known`) → **dokunma**.

Dil-koşullu bir kural gerekli görüyorsan kendin uydurma; `contract_change_request: true` ile `normalize`'a `lang: str | None` parametresi talep et.

## K6 · Yer tutucular

`Segment.text` **orijinal yer tutucuları birebir korur.** İşaretleme, sarma, değiştirme **yapılmaz** — sözleşmede konum bilgisi taşıyacak alan yoktur, dolayısıyla geri koyma güvenli değildir.

`placeholders`, metinde **geçtikleri sırayla ve tekrarları korunarak** doldurulur. **Tekilleştirme yapılmaz** (`"%s ve %s"` iki kayıt üretir).

**Sayılar `placeholders`'a girmez.** Yalnızca değişken yer tutucuları (`{n}`, `%s`, `%d`) ve biçim/renk etiketleri (`<...>`, `[...]`) girer. §3.2 "sayılar korunmalı" derken *değiştirilmemeli* diyor, sarılmalı demiyor.

Kapsadığın desenlerin tam listesini docstring'e yaz.

## K7 · Güven eşiği

- `confidence < threshold` → **düşer**
- `confidence == threshold` → **kalır** (bunu bir testle sabitle)
- `confidence` `NaN` veya `[0,1]` dışı → **`ValueError` fırlat**

Sözleşmede `confidence: float` kısıtsızdır. "Gerçekte olmaz" gerekçesi kabul edilmez; fonksiyonun kabul ettiği her girdi için bir cevabın olmalı. (Bu, T-003'ün kırıldığı deliğin birebir aynısı.)

## K8 · `source_blocks`

- **Orijinal** `blocks` dizisindeki 0-tabanlı indeksler — filtreleme sonrası indeksler **değil**
- Artan sırada, tekrarsız, **boş olmayacak**
- Farklı segmentlerin `source_blocks` kümeleri **ayrık** olacak

Bir blok birden çok segmente katkı veriyorsa `known_gaps`'te bildir. İki koşulu (orijinal uzay + ayrıklık) açık birer testle sabitle.

## K9 · Konuşmacı

Gruplama **konuşmacı sınırını asla aşmaz.** Farklı `speaker` tespit edilen komşu bloklar ayrı segmentlerde kalır — `Segment.speaker` tek değerlidir, birleştirmek bilgi kaybıdır.

Konuşmacı etiketi çıkarıldıktan sonra metni boş kalan blok **segment üretmez**; etiketi bir sonraki bloğa taşınır, sonraki blok yoksa blok düşer.

**`normalize` hiçbir koşulda `text` alanı boş veya yalnız boşluk olan bir `Segment` döndürmez.**

## K10 · `bbox` birleşimi

Birleşik `bbox` kaynak blokların kapsayıcı dikdörtgenidir. `monitor_index` ve `dpi_scale` kaynak blokların **hepsinde aynı olmak zorundadır**; farklıysa **`ValueError`**.

(Tek bir izlenen bölgeden gelen bloklar zaten aynı monitördedir; sessiz bozulma yerine gürültülü hata tercih edilir.)

## K11 · Gruplama davranışı

- `dialogue`, `tooltip`, `subtitle` → **gruplar**
- `menu` → **gruplamaz** (her öğe ayrı segment)

Dört ön ayar arasındaki diğer fark yalnızca `presets.py`'deki **sayısal parametrelerdir** (güven eşiği, dikey boşluk oranı, maksimum grup uzunluğu). Her ön ayar için en az bir test, o ön ayarın parametresinin çıktıyı **gerçekten değiştirdiğini** göstersin.

## K12 · Boş sonuçlar

- Boş girdi → `[]`
- Tüm bloklar eşik altında → `[]` (**kurtarma/gevşetme yapılmaz**)
- Gürültü elendikten sonra hiçbir şey kalmadı → `[]`

Üçünü de birer testle sabitle.

## K13 · Determinizm — süreçler arası

`set`/`dict` iterasyon sırasına bağımlı çıktı üretilmez. `purity_check.py` bunu farklı `PYTHONHASHSEED` değerleriyle makineyle denetliyor.

## K14 · Performans bütçesi — testi kırar

`tests/unit/ocr/test_normalizer.py` içinde bütçe testi olacak ve **aşımda kırılacak** (`assert`).

Ölçüm şartnamesi: 30 bloklu, blok başına ~40 karakterli, `dialogue` ön ayarlı **deterministik** girdi; `normalize` 50 kez çağrılır; **medyan** süre ≤ 5 ms.

Girdi üreticisi deterministik olacak ki tester aynı ölçümü tekrar edebilsin. Şartname §5.7 ve §9: *"bütçe aşımı testi kırar. Bütçe bir gözlem değil, bir sözleşmedir."*

---

# Yozlaşmış girdiler — hiçbiri çökmeyecek

Her biri için **ne yaptığını docstring'de yaz.** "Çökmez" bir davranış tarifi değildir.

`w == 0` veya `h == 0` bbox · negatif `w`/`h` · boş veya yalnız-boşluk `text` · `line_boxes == ()` · `confidence` `NaN`/alan dışı (→ K7) · tek blok · boş liste · 30'dan çok blok · farklı `monitor_index` (→ K10)

Not: satır yüksekliğine **bölen** bir eşik formülü kullanıyorsan `h == 0` çöker. §5.6: *"hiçbir hata pipeline'ı durdurmaz."*

---

# Kararlarını nereye yazacaksın — İKİ YERE

`known_gaps`, `delivery.md`'nin alanıdır ve **tester onu okumaz** (PROTOKOL §3 kapı 2). Yalnızca oraya yazılan karar, kapıyı işleten kişiye ulaşmaz.

Her kararını **iki yere** yaz:

**(a) İlgili fonksiyonun/sabitin docstring'ine** — tester yalnızca burayı görür; **garanti alanı burada durmalıdır**
**(b) `delivery.md`'nin `known_gaps` alanına** — şef burayı görür

Yalnızca `known_gaps`'e yazılan karar **denetlenmemiş** sayılır.

---

# Diğer kısıtlar

- **Tamamen saf.** I/O yok, global mutable durum yok, rastgelelik yok, zaman bağımlılığı yok. `purity_check.py` denetliyor.
- Eşikler `presets.py`'de **adlandırılmış sabit** olacak, docstring'de gerekçelendirilecek. "Blokları birleştirir" değil; "dikey boşluk satır yüksekliğinin X katından küçük **ve** yatay örtüşme %Y'den büyükse birleştirir".
- `presets.py` bu turda **yalnız normalizasyon parametrelerini** içerir. §3.2'nin `ölçekleme faktörü` ve `kontrast ön işlemesi` alanları bilinçli olarak sonraki göreve bırakılmıştır — yapıyı bu genişlemeyi kaldıracak biçimde kur (ön ayar başına tek dataclass), docstring'de belirt, **kendin ekleme**.
- §8.3 A3'ün "altın görüntü seti" kriteri bu görevin **kapsamı dışındadır** (altın set A9'un dizinine bağlı, OCR motoru henüz yok). Fixture'lar test dosyasının içinde elle kurulur. `known_gaps`'e yaz.
- `src/contracts/` **dondurulmuş**. Eksik görürsen `contract_change_request: true`.
- Yalnızca stdlib + numpy. Yeni bağımlılık şef onayı gerektirir.
- Ön bilgideki `wave: 2` pilottaki **görev sırasını** gösterir, §8.8'in ajan dalgalarını değil.

# Test etmen gerekenler

Yukarıdaki 14 kararın **her biri** için en az bir test. Ayrıca: iki satıra bölünmüş cümle · kesme çizgili kelime · gerçek tireli `well-known` · bölünmüş cümlenin **ortasında** eşik altı blok (K2 sırasını sınar) · tek kanji (`力`) ve tek hangul · `"%s ve %s"` tekrarı · `"50%"` · yalnız `"Ada:"` içeren blok · `dialogue`'da iki farklı konuşmacılı komşu blok · dört ön ayar · yozlaşmış girdilerin hepsi.

# Yöntem ve teslim

TDD: önce başarısız test, sonra implementasyon. Kırmızı fazın çıktısını `evidence/pytest-red.txt` altına bırak.

Üç kabul komutunu da **gerçekten çalıştır**, ham çıktıyı `.agents/tasks/T-004/evidence/` altına yaz. Bütçe ölçümünü `evidence/budget.txt` altına.

`.agents/tasks/T-004/delivery.md`, `task: T-004`, `round: 1`, PROTOKOL §4 şemasına birebir uygun.

`.agents/PROTOKOL.md` §6'daki dokuz değişmez kural geçerlidir.
