# Şef Kararı — T-004, Tur 2

Üç tester bağımsız çalıştı. **B onay, A ret, C ret.** Protokol gereği bir ret = görev reddedilir.

Şef üç raporu **ayrı ayrı** okudu ve her iddiayı kendi eliyle yeniden üretti. Aşağıdaki dört bulgu doğrulanmıştır.

---

## Bulgu 1 — KRİTİK · Konuşmacı etiketli çok satırlı replik ikiye bölünüyor

**Bulan:** Tester-C · **Şef doğrulaması:** yeniden üretildi, ASCII ve Japonca'da birebir aynı

```
girdi : ['Ada:', 'Bu uzun bir', 'cumledir.']
cikti : speaker='Ada'  text='Bu uzun bir'
        speaker=None   text='cumledir.'      <- cumle ikiye bolundu

kontrol: ['Ada:', 'Bu tek satirlik.']  ->  1 segment, dogru
```

Bu, tasarım dokümanı §5.2'nin modülün **varlık sebebi** olarak verdiği hatanın ta kendisi: *"OCR iki satıra bölünmüş bir cümle verir; bunu iki ayrı cümle olarak çevirirsek sonuç bozuk çıkar."*

### Kök sebep — şefin paket hatası

```python
def _should_group(a, b, params):
    if a.speaker != b.speaker:
        return False
```

K9'da iki kural yazmıştım ve ikisi birlikte imkânsız bir durum üretiyor:

1. *"Gruplama konuşmacı sınırını asla aşmaz"*
2. *"Etiket bir sonraki bloğa taşınır"*

Etiket ikinci bloğa taşınıyor (`speaker="Ada"`), üçüncü blok etiketsiz kalıyor (`speaker=None`), ve `"Ada" != None` olduğu için gruplama reddediliyor. Implementer **iki kurala da sadakatle uydu**; hata kuralların kendisinde.

### K15 (YENİ KARAR) · `None` "farklı konuşmacı" değil, "devam" demektir

`_should_group`'daki konuşmacı kontrolü şu mantıkla değişecek:

| `a.speaker` | `b.speaker` | Gruplama | Grubun `speaker` değeri |
|---|---|---|---|
| `X` | `X` | **evet** | `X` |
| `X` | `None` | **evet** — devam satırı | `X` (miras alır) |
| `None` | `None` | **evet** | `None` |
| `None` | `Y` | **hayır** — yeni konuşmacı başlıyor | — |
| `X` | `Y` (≠X) | **hayır** — konuşmacı sınırı | — |

K9'un gerçek niyeti korunuyor: **iki farklı konuşmacı asla birleşmez.** Düzeltilen tek şey, etiketsiz bir devam satırının "farklı konuşmacı" sayılması.

Docstring'de bu tablo aynen yer alacak.

---

## Bulgu 2 — BLOKE EDİCİ · `h == 0` ve negatif `h` docstring'e rağmen gruplanıyor

**Bulan:** Tester-A · **Şef doğrulaması:** yeniden üretildi

Modül docstring'i (K10 bölümü) **koşulsuz** iddia ediyor:

> *"`bbox.h == 0` veya `bbox.w == 0` durumunda ilgili koşul basitçe 'gruplama yok' tarafına düşer"*

Bu yalnızca `w == 0` için doğru. `_should_group` yozlaşmış dalı sadece `gap > 0` ise reddediyor; kutular dikeyde değiyor veya çakışıyorsa (`gap <= 0`) yatay örtüşme kontrolüne düşüp **gruplayabiliyor**.

```
h=0,  ayni y (gap=0)                   -> 1 segment   (docstring 2 vaat ediyor)
h=0,  gap>0                            -> 2 segment   dogru
a: y=-15 h=20 (bottom=5), b: y=0 h=-10 -> 1 segment   (docstring 2 vaat ediyor)
w=0,  gap=2                            -> 2 segment   dogru
```

> **Şefin sonda hatası, kayıt için.** İlk denememde iki bloğu da `h=-5` ve aynı `y`'ye koydum; negatif yükseklikte `bottom = y + h` olduğu için `gap` pozitif çıktı ve hatalı dal hiç tetiklenmedi. Tester-A'yı yanlış sandım. A'nın kurulumu doğruydu. **Yanlış kurulmuş bir sonda, hatanın yokluğunu kanıtlamaz** — PROTOKOL §3 kapı 6, ikinci kez şefin üzerinde doğrulandı.

### K16 (YENİ KARAR) · Yozlaşmış yükseklikte gruplama yok

`ref_height <= 0` olduğunda gruplama **koşulsuz reddedilecek** — `gap` değerine bakılmaksızın. Böylece docstring'in mevcut iddiası kodun tamamı için doğru hale gelir.

Alternatif (iddiayı daraltmak) **kabul edilmiyor**: yozlaşmış geometride gruplama kararı verilemez, çünkü karar için gereken ölçü yok. Gürültülü bir OCR kutusunun komşusunu yutması, sessiz bir metin bozulmasıdır.

---

## Bulgu 3 — BLOKE EDİCİ · Fullwidth iki nokta (`：`) konuşmacı etiketi tanınmıyor

**Bulan:** Tester-C · **Şef doğrulaması:** yeniden üretildi

```
'Ada: Merhaba'      -> speaker='Ada'  text='Merhaba'     dogru
'勇者：こんにちは'   -> speaker=None   text=degismedi     ETIKET KAYIP
```

Kod yalnız ASCII `:` arıyor. **JP/KR oyunlarında konuşmacı etiketi standart olarak `：` (U+FF1A) ile yazılır.** Suflör'ün birincil hedefi bu oyunlar; yani özellik ana kullanım senaryosunda çalışmıyor.

### K17 (YENİ KARAR) · Ayraç kümesi genişletilecek

Konuşmacı ayracı olarak en az şunlar tanınacak: `:` (U+003A), `：` (U+FF1A). Kod bunları `presets.py`'de **adlandırılmış sabit** olarak tutacak (sabit kodlama yok) ve docstring tam listeyi yazacak.

---

## Bulgu 4 — BLOKE EDİCİ · Fullwidth `？`/`！` tek karakterli bloklar siliniyor

**Bulan:** Tester-C · **Şef doğrulaması:** yeniden üretildi

```
ASCII ?          korundu: True
ASCII !          korundu: True
fullwidth ？     korundu: False    <- sessizce siliniyor
fullwidth ！     korundu: False    <- sessizce siliniyor
```

K4 tek-karakter kuralının `?`/`!` istisnası ASCII'ye özel yazılmış. Fullwidth karşılıkları JP metninde yaygındır ve tek başına bir diyalog bloğu olabilir.

### K18 (YENİ KARAR) · İstisna Unicode denkliğine göre tanımlanacak

`?`/`!` istisnası, karakterin **Unicode NFKC normalizasyonu** `?` veya `!` ise geçerli olacak — böylece `？`/`！` ve diğer uyumluluk varyantları otomatik kapsanır. Beyaz liste yine yasak.

---

## Bloke etmeyen, kayda geçen gözlemler

**Tester-A:** blok sınırına bölünmüş yer tutucu (`"{0"` + `"} birimdir"`) `placeholders`'a bozuk `"{0 }"` olarak giriyor — belgelenmemiş, K6 ihlali değil. Tek satırlık bloklarda baştaki/sondaki boşluk `\n` olmadan da kırpılıyor — makul ama üst özet listesinde yazmıyor. **İkisini de docstring'de belgele, davranışı değiştirme.**

**Tester-C:** üst üste binen bloklarda ölçek O(n)'den kötü (n=500 → ~3.5 ms, n=1000 → ~9.3 ms, n=2000 → ~26.7 ms). Hedef aralıkta (≤500 blok) sorun değil. **Düzeltme zorunlu değil**; `known_gaps`'te kayda geç.

**Tester-B:** hyphen'siz satır birleşimi gruplamaya bırakılmış, K2'nin literal okumasından farklı ama K11 ile tutarlı ve belgelenmiş. Şef sondası dört ön ayarda da doğru davrandığını doğruladı. **Sorun yok.**

---

## Neyin doğru olduğu — bozmadan koru

Üç tester bağımsız olarak şunları sınadı ve hepsi ayakta kaldı. Tur 2'de bunlarda **regresyon olmayacak**:

- **K7 confidence** — `NaN`/`inf`/alan dışı → `ValueError` (açık `math.isnan`, NaN yutan karşılaştırma yok), tam eşik dört ön ayarda da korunuyor
- **K6 yer tutucu** — `"%s ve %s"` tekrar/sıra korunuyor, `"50%"` ile `"50%s"` doğru ayrışıyor
- **K5 hyphen** — `well-known` korunuyor, `keli-\nme` birleşiyor, dört Unicode tire varyantı ASCII kuralından doğru şekilde dışlanmış
- **K8 `source_blocks`** — orijinal indeks uzayı (şef bağımsız doğruladı: `(1,), (3,), (4,)`)
- **K4 sınıf tabanlı tek karakter** — `unicodedata.category(ch)[0] in ("L","N")`, beyaz liste yok; tek kanji/hangul/hiragana/Kiril/Arapça/Devanagari hepsi korunuyor
- **K10 `bbox` birleşimi** — `monitor_index`/`dpi_scale` uyuşmazlığında `ValueError`
- **K14 bütçe** — gerçek `assert`, medyan 0.176 ms, `skip`/`xfail` yok
- **K13 determinizm** — süreçler arası, `purity_check.py` doğruluyor
- **Asıl iş** — hyphen'siz bölünmüş cümle `dialogue`/`tooltip`/`subtitle`'da birleşiyor, `menu`'de birleşmiyor (şef sondası)
