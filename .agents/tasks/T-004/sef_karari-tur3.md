# Şef Kararı — T-004, Tur 3

Tur 2'de **üç tester de onay verdi.** Şef üç raporu ayrı okudu, her iddiayı kendi eliyle yeniden üretti ve dört düzeltmenin dördünü de doğruladı. Regresyon yok, 758 test yeşil.

**Buna rağmen görev kapatılmıyor.** Tester-C'nin "bloke etmeyen" saydığı iki notu şef inceledi ve birini yeniden sınıflandırdı.

---

## K19 (YENİ) · Uzunluk sınırı yüzünden bölünen grubun kuyruğu konuşmacıyı miras alır

**Bulan:** Tester-C (bloke etmeyen olarak) · **Şef doğrulaması:** yeniden üretildi · **Şef yeniden sınıflandırdı: bloke edici**

```
girdi : "Ada:" + 5 uzun govde blogu
cikti : speaker='Ada'  src=(0,1,2,3)  len=275
        speaker=None   src=(4,5)      len=183   <- Ada'nin devami, bilgi kayip
```

### Neden bloke edici

C haklı olarak "hiçbir K kararı aksini vaat etmiyor" dedi. Ama ölçüt bu değil. Ölçüt şu: **modül var olma sebebini yerine getiriyor mu?**

Tasarım §5.2: *"OCR iki satıra bölünmüş bir cümle verir; bunu iki ayrı cümle olarak çevirirsek sonuç bozuk çıkar."* Konuşmacı bağlamını kaybetmek aynı ailenin hatası — çeviri katmanı "kim konuşuyor" bilgisi olmadan zamir, hitap ve nezaket seviyesini yanlış seçer. Japonca'da bu belirleyicidir.

Aşağı akış `speaker=None` gördüğünde "konuşmacısı yok" ile "öncekinin devamı"nı **ayırt edemiyor**. Bilgi sessizce kayboluyor — sessiz kayıp, bu projede en ağır hata sınıfı.

### Karar

| Bölünme sebebi | Kuyruk segmentin `speaker` değeri |
|---|---|
| `max_group_chars` aşıldı | **miras alır** — aynı konuşmacının repliğinin devamı, kesin |
| Geometrik boşluk / farklı `speaker` / yozlaşmış bbox | **`None` kalır** — yeni bağlam olabilir, atfetmek spekülasyon |

Ayrım gerekçesi: uzunluk sınırı **bizim** koyduğumuz yapay bir sınır, metinde bir kopuş yok. Geometrik boşluk ise metnin kendisinden gelen bir sinyal; oraya konuşmacı atfetmek uydurma olur.

Docstring bu tabloyu aynen taşıyacak ve `None`'ın iki anlamını (**"etiket yok"** vs **"bilinmiyor"**) açıkça ayıracak. Ayırt edilemiyorsa bunu da yazacak.

**Sözleşme değişikliği yapılmayacak.** `Segment` dondurulmuş; `continues_previous` gibi bir alan eklemek tüm tüketicileri etkiler. Miras alma çözümü mevcut sözleşme içinde yeterli.

---

## K20 (YENİ) · NFKC iddiası olgusal olarak düzeltilecek

**Bulan:** Tester-C · **Şef doğrulaması:** tüm Unicode taraması yapıldı

`normalizer.py` satır ~85-86 şunu iddia ediyor:

> *"ayrıca başka hiçbir karakter NFKC ile `?`/`!`ye AÇILMADIĞI için istisna GENİŞLEMEZ, DARALMAZ."*

**Yanlış.** Şefin tam Unicode taraması (0x0–0x10FFFF), ASCII dışı altı karakter buldu:

```
U+FE15  PRESENTATION FORM FOR VERTICAL EXCLAMATION MARK
U+FE16  PRESENTATION FORM FOR VERTICAL QUESTION MARK
U+FE56  SMALL QUESTION MARK
U+FE57  SMALL EXCLAMATION MARK
U+FF01  FULLWIDTH EXCLAMATION MARK
U+FF1F  FULLWIDTH QUESTION MARK
```

Davranış **doğru** — altısı da zararsız `Po` noktalama, korunmaları isabetli. Yanlış olan tek şey docstring'in olgusal iddiası.

### Neden bloke edici

Bu kod tabanının tüm disiplini şu ilkeye dayanıyor: **docstring bir garantidir.** T-003 bu yüzden reddedildi, T-004 tur 1 bu yüzden reddedildi. Yanlış bir olgusal iddia, ilkeyi tam da onu uygulamaya çalışan dosyanın içinde çürütür.

### Karar

İddia altı karakterin **tam listesiyle** değiştirilecek, ve listenin **türetilmiş** olduğu (sabit kodlanmış değil) belirtilecek — beyaz liste yasağı hâlâ geçerli, kod NFKC ile karar vermeye devam edecek. Docstring yalnızca *hangi karakterlerin bu denkliği sağladığını* bilgi olarak yazacak.

Sayı Unicode sürümüyle değişebileceği için docstring bunu da not edecek: *"Python'un Unicode sürümüne göre değişebilir; liste bilgi amaçlıdır, kod NFKC ile karar verir."*

---

## Protokol değişikliği — kapı risk yüzeyine göre ölçeklenir

Tur 3 yalnızca **iki iyi tanımlı değişiklik** içeriyor: biri küçük bir davranış değişikliği (K19), biri saf dokümantasyon (K20).

Üç mercekli tam kapıyı yeniden koşmak orantısız olurdu. Ama K19 bir davranış değişikliği ve `_should_group`/gruplama yoluna dokunuyor — yani regresyon riski **gerçek**.

**Karar:** Tur 3'te **iki tester** koşacak:

- **Tester-B (karar uyumu)** — K19/K20 kodda birebir var mı, ve K1–K18'de regresyon var mı. K15 matrisinin beş satırı yeniden doğrulanacak, çünkü K19 aynı yola dokunuyor.
- **Tester-C (sınır/dil)** — bulguları kendisi kaldırdı, düzeltmelerinin doğru olduğunu ve CJK yüzeyinin bozulmadığını doğrulayacak. K20'nin altı karakterini bağımsız olarak yeniden tarayacak.

**Tester-A koşmayacak.** Merceği (garanti alanı) tur 2'de kapsamlı ızgara + fuzz ile tükendi ve K19/K20 yeni bir garanti alanı açmıyor — K20 zaten mevcut bir iddiayı **daraltıyor**, genişletmiyor.

Bu, PROTOKOL §4.5'e eklenen kural: **görev başına üç mercek varsayılandır; bir düzeltme turu yalnızca dar ve iyi tanımlı bir yüzeye dokunuyorsa şef mercek sayısını azaltabilir, ama gerekçesini karar belgesine yazar.**

---

## Bozmadan koru — tur 3'te de geçerli

Tur 2'de üç tester bağımsız olarak doğruladı, K19/K20 bunları bozmayacak:

K15 matrisinin beş satırı (özellikle `None/Y` ve `X/Y` asla birleşmez) · K16 yozlaşmış geometride koşulsuz reddetme · K17 ayraç kümesi (`:` ve `：`, kapsam sınırı belgeli) · K18 NFKC istisnası · K7 confidence · K6 yer tutucu · K5 hyphen · K8 orijinal indeks uzayı · K4 sınıf tabanlı tek karakter (11 yazı sistemi) · K10 `bbox` `ValueError` · K14 bütçe assertion'ı · K13 süreçler arası determinizm · asıl iş (dört ön ayarda doğru gruplama) · ölçek (n=2000 → ~27 ms, kötüleşmeyecek)

---

## Şefin sonda hatası — üçüncü kez, kayıt için

Tur 2 doğrulamasında `h=1` için "birleşmeli" diye varsaydım, kod birleştirmedi, aşırı düzeltme sandım. Eşiği okuduğumda: `max_vertical_gap_ratio = 0.8`, `gap=1`, `1 < 0.8*1` yanlış — kod **doğru**, beklentim yanlıştı.

Aynı hatayı T-002'de (debounce) ve T-003'te (negatif yükseklik geometrisi) yapmıştım. Ortak desen: **beklentiyi kuralı okumadan yazmak.** Ajanlar bu hataya düşmüyor çünkü beklentiyi koddan ve şartnameden türetiyorlar.

Şef sondası kuralına ek: *beklenen değeri yazmadan önce ilgili parametreyi/kuralı oku.* Yanlış kurulmuş bir sonda, hatanın varlığını da yokluğunu da kanıtlamaz.
