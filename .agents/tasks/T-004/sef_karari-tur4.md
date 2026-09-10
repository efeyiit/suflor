# Şef Kararı — T-004, Tur 4

Tur 3'te **B onay, C ret.** Şef C'nin bulgusunu kendi eliyle yeniden üretti ve doğruladı.

**Bulgu, şefin K19 kararındaki bir hatadan kaynaklanıyor** — implementer K19'u birebir doğru uyguladı.

---

## Bulgu · Bileşik sınırda miras yanlış tetikleniyor

**Bulan:** Tester-C · **Şef doğrulaması:** yeniden üretildi

```
_group_rejection_reason ciktilari:
  sadece uzunluk (yakin bloklar)   -> 'length'
  uzunluk + BUYUK dikey bosluk     -> 'length'    <- geometrik kopus gorunmez
  uzunluk + h=0 (yozlasmis bbox)   -> 'length'    <- ayni

tam pipeline (ucuncu blok 458px asagida):
  speaker='Ada'  src=(0,1)
  speaker='Ada'  src=(2,)
  speaker='Ada'  src=(3,)    <- MIRAS ALDI, ama arada gercek geometrik kopus var
```

K19 tablosu açıkça *"geometrik boşluk / farklı `speaker` / yozlaşmış bbox → `None` **kalır**"* diyor. İhlal edildi.

### Kök sebep — şefin K19 hatası

`_group_rejection_reason` **ilk** başarısız kontrolün kodunu döndürüyor. Sıra sabit:

```
speaker -> length -> height -> gap -> width -> overlap
```

`length`, **tüm geometri kontrollerinden önce**. Bir çift hem uzunluk sınırını aşıyor hem geometrik olarak kopuksa, kod `'length'` döndürüyor ve K19 miras uyguluyor.

K19'u yazarken red sebeplerinin **birbirini dışladığını** varsaydım. Dışlamıyorlar — bir çift aynı anda birden çok kontrolden kalabilir.

Bu, K19'un **kendi gerekçesini** de çürütüyor. Gerekçe şuydu: *"uzunluk sınırı bizim koyduğumuz yapay bir sınır, metinde kopuş yok."* Bileşik durumda metinde **gerçek bir kopuş var** — sadece uzunluk kontrolü sırada önce olduğu için görünmüyor.

---

## K21 (YENİ) · Miras, uzunluk **tek** engel olduğunda uygulanır

Kural, "ilk başarısız kontrol" üzerinden değil, **başarısız kontrollerin kümesi** üzerinden tanımlanır:

> Kuyruk segment konuşmacıyı **yalnızca** `max_group_chars` sınırı **tek başına** gruplamayı engelliyorsa miras alır. Başka herhangi bir kontrol de (geometri, konuşmacı, yozlaşmış bbox) başarısızsa **miras yok**.

Denk ve daha kolay uygulanabilir ifade:

> `max_group_chars` sonsuz olsaydı bu çift gruplanır mıydı? **Evet** ise tek engel uzunluktur → miras al. **Hayır** ise gerçek bir kopuş var → `speaker=None` kalır.

### Uygulama notu

Sebep kodunu döndüren mevcut yapı korunabilir; ama miras kararı **`length` kodunun varlığına bakarak verilemez.** İki seçenek — hangisini seçtiğini docstring'de yaz:

1. `_group_rejection_reason`'a "uzunluk kontrolünü atla" seçeneği ekle; miras kararı için ikinci kez çağır.
2. Fonksiyonu **tüm** başarısız sebepleri döndürecek şekilde değiştir; miras yalnızca küme tam olarak `{"length"}` ise uygulanır.

**Kısıt:** `_should_group`'un dış imzası (`(_Item, _Item, NormalizerParams) -> bool`) **değişmeyecek** — K15 matris testleri onu doğrudan çağırıyor. `_should_group` ile miras mantığının **yapısal olarak ayrışamaz** kalması da korunacak; tur 3'teki tek satırlık devretme deseni iyi bir çözümdü, bozma.

### Zorunlu testler

- Uzunluk **tek** engel → miras **var** (ASCII + Japonca)
- Uzunluk **+ büyük dikey boşluk** → miras **yok**
- Uzunluk **+ `h=0`** → miras **yok**
- Uzunluk **+ `w=0`** → miras **yok**
- Uzunluk **+ yetersiz yatay örtüşme** → miras **yok**
- Uzunluk **+ farklı konuşmacı** → miras **yok** (zaten `speaker` sırada önce, ama açıkça sabitle)
- Üç ve daha fazla parçaya bölünen zincirde her bölünme noktası **kendi** sebebine göre değerlendiriliyor

---

## K22 (YENİ) · K20 docstring ifade çelişkisi

**Bulan:** Tester-C (bloke etmeyen)

Docstring "ASCII/fullwidth dışında altı karakter" diyor ama listenin kendisi fullwidth `！`/`？`'yi **içeriyor**. İfade kendi listesiyle çelişiyor.

Düzeltme: sayı ve kapsam ifadesi listeyle tutarlı hale getirilecek. Altı karakterin **tamamı** ASCII dışıdır; ikisi fullwidth, dördü uyumluluk formu.

---

## Bozmadan koru — tur 4'te de geçerli

K19'un doğru çalışan kısmı (uzunluk tek engelse miras) · K15 matrisinin beş satırı · K16 yozlaşmış geometride koşulsuz red · `_should_group` ↔ `_group_rejection_reason` **yapısal ayrışmazlığı** (tur 3'te AST ile ispatlandı, 3000 çiftlik şef sondasıyla da doğrulandı) · `speaker` kontrolünün `length`'ten **önce** gelmesi · K17 ayraç kümesi · K18/K20 NFKC istisnası ve altı karakter · K7 confidence · K6 yer tutucu · K5 hyphen · K8 orijinal indeks uzayı · K4 sınıf tabanlı tek karakter · K10 `bbox` `ValueError` · K14 bütçe assertion'ı · K13 determinizm · asıl iş · ölçek (n=2000 → ~26-27 ms)

---

## Kapı — tur 4'te iki mercek

**Tester-C** koşacak: bulguyu kendisi buldu, düzeltmesini ve sınırlarını doğrulayacak; CJK yüzeyi ve ölçek regresyonu da onun merceğinde.

**Tester-B** koşacak: K21 gruplama yolunun **karar mantığına** dokunuyor; K1–K22 uyumu ve K15/K16 regresyonu onun merceğinde. Tur 3'te yapısal ispat yöntemini kurdu — K21 sonrası aynı ayrışmazlık hâlâ geçerli mi, onu doğrulayacak.

**Tester-A koşmayacak.** Gerekçe: garanti alanı merceği tur 2'de ızgara + fuzz ile tükendi; K21 yeni bir *garanti alanı* açmıyor, mevcut bir kuralı **daraltıyor** (miras daha az durumda uygulanacak). K22 salt ifade düzeltmesi. PROTOKOL §4.5 gereği gerekçe burada kayıtlı.

---

## Şefin kayda geçen özeleştirisi

T-004'ün dört turunda bulunan bloke edici hataların kaynak dağılımı:

| Tur | Bulgu | Kaynak |
|---|---|---|
| 0 | 19 belirsizlik | **Şefin paketi** (kırmızı takım buldu) |
| 1 | Etiket + çok bloklu gövde bölünmesi | **Şefin K9 kuralı** (iki kural çarpışması) |
| 1 | `h==0` yozlaşmış dal | Implementer |
| 1 | Fullwidth `：` ve `？`/`！` | Implementer |
| 3 | Bileşik sınırda yanlış miras | **Şefin K19 kararı** (sebeplerin dışlayıcı sanılması) |

Beş bloke edici bulgunun **üçü** şefin kendi kararlarından doğdu. Ayrıca şef üç kez sondasını yanlış kurdu.

Desen açık: **implementer'ın hatası azalıyor, şefin hatası azalmıyor.** Kırmızı takım kapısı paket için var ama **karar belgeleri** (`sef_karari-tur2/3.md`) hiç denetlenmiyor — K19 oradan çıktı ve hiçbir kapıdan geçmedi.

**Protokol eksiği olarak kaydedilir:** tur içinde verilen yeni şef kararları da, tıpkı paket gibi, kırmızı takımdan geçmeli. Bu tur için geriye dönük uygulanmıyor (K21 dar ve iyi tanımlı), ama T-005'ten itibaren zorunlu olacak.
