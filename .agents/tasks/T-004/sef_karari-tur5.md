# Şef Kararı — T-004, Tur 5

Tur 4'te implementer K21/K22'yi doğru uyguladı ve şef doğruladı. Ama **karar kırmızı takımı** — şefin kararlarını denetlemek için bu turda ilk kez devreye alındı — 12 bulgu çıkardı, üçü yüksek şiddetli.

Şef üç yüksek bulguyu ve bir orta bulguyu kendi eliyle yeniden üretti. **Hepsi doğru.**

---

## Kök teşhis — kapı eksikliği değil, yöntem hatası

Kırmızı takımın cümlesi:

> *"Desen değişmedi: kurallar tek tek doğru, etkileşimleri denetlenmemiş."*

| Karar | Ne yazdım | Görünmeyen etkileşim |
|---|---|---|
| **K9** | "Gruplama konuşmacı sınırını aşmaz" + "etiket sonraki bloğa taşınır" | İkisi birlikte çok satırlı repliği birleşemez yaptı |
| **K19** | "`reason == length` ise miras al" | `length`, geometri kontrollerinden önce sıralıydı |
| **K21** | "Uzunluk tek engelse miras al" | Miras, sonraki gruplama kararına **girdi** oluyor |
| **K22** | "İkisi fullwidth, dördü uyumluluk formu" | Altısı da uyumluluk formu — olgusal hata düzeltirken olgusal hata |

Dördü de **mekanizma** olarak yazıldı ("şu koşulda şunu yap"), **değişmez** olarak değil ("şu her zaman doğru olmalı").

Mekanizmanın etkileşimleri görünmez; değişmezin ihlali **makineyle ölçülebilir**. Bundan sonra şef kararları önce değişmez olarak yazılacak, mekanizma ancak değişmezi sağlamak için seçilecek.

---

## Bulgu B1 · `yuksek` — Miras bölümlemeyi değiştiriyor

**Şef doğrulaması:** birebir yeniden üretildi

```
VARYANT A (onceki sinir uzunluk-tek -> miras VAR):
   speaker='Ada'  src=(0, 1)
   speaker='Ada'  src=(2, 3)      <- b2 ve b3 BIRLESTI

VARYANT B (onceki sinir bilesik -> miras YOK):
   speaker='Ada'  src=(0, 1)
   speaker=None   src=(2,)        <- ayri kaldi
   speaker='Ada'  src=(3,)
```

b2↔b3 geometrisi ve metni iki varyantta da **aynı**. Tek fark önceki sınırdaki miras kararı.

**Mekanizma:** miras, uydurduğu `speaker` değerini bir sonraki `_should_group` çağrısına **girdi** yapıyor. K15 matrisinde `None/Y → hayır` satırı, sol taraf `None`'dan `Ada`'ya çevrildiği için `Ada/Ada → evet` satırına dönüşüyor. Kural atlatılıyor.

**Ürün etkisi:** kendi `Ada:` etiketi olan **yeni bir replik**, önceki repliğin kuyruğuna yapışıyor. İki ayrı sözce tek `Segment` oluyor. JP/KR oyunlarında her replik satırı konuşmacı adıyla yeniden etiketlendiği için bu **birincil hedef kitlede standart senaryo**.

Şefin tur 4 "Bozmadan koru" listesi K15'in beş satırının korunduğunu iddia ediyordu. Fonksiyon korundu, **kural atlatıldı**.

---

## K23 (YENİ) · DEĞİŞMEZ — Miras bölümlemeyi değiştiremez

Bu bir mekanizma değil, bir **değişmez**. Uygulama yöntemi implementer'a ait; değişmezin sağlanması zorunlu.

> **DEĞİŞMEZ:** Herhangi bir girdi için, `normalize` çıktısının **bölümlemesi** — yani `Segment.source_blocks` demetlerinin dizisi — miras mekanizması açıkken ve kapalıyken **birebir aynı** olmalıdır.
>
> Miras **yalnızca** `Segment.speaker` alanının değerini değiştirebilir. `text`, `bbox`, `source_blocks`, `placeholders` ve segment **sayısı** miras kararından etkilenemez.

### Neden değişmez olarak yazıldı

Mekanizma olarak yazsaydım ("miras alınan değer sonraki karara girdi olmasın") implementer bunu uygular ama **başka bir yoldan** aynı sızıntı tekrar doğabilir. Değişmez, sızıntının **her biçimini** yakalar ve makineyle ölçülebilir.

### Zorunlu makine denetimi

`normalize`'ı miras kapalı çalıştıracak bir test kancası olacak (örn. modül-içi bir bayrak veya ayrı bir iç fonksiyon — genel API'ye sızmayacak). Test, **rastgele ve kapsamlı** girdi kümesi üzerinde (sabit tohum, ≥2000 girdi, dört ön ayar, yozlaşmış geometri dâhil) iki koşunun bölümlemesini karşılaştıracak ve **tek bir fark bile** testi kıracak.

Bu denetim `tests/unit/ocr/test_normalizer.py` içinde yaşayacak ve kalıcı olacak.

### Uygulama sonucu

Değişmezi sağlamanın doğrudan yolu: gruplama kararları öğenin **OCR'dan gelen özgün** `speaker` değerini kullanacak; miras yalnızca kapanan grubun `Segment`'i üretilirken uygulanacak. Başka bir yol bulursan, değişmezi sağladığını denetimle kanıtla.

---

## Bulgu B2/B3 · `yuksek` — K21'in ifadesi iki türlü okunabilir

**B2:** Şef "denk" ilan ettiği iki ifade **denk değil**. Kırmızı takımın ölçümü: 4000 rastgele girdi, 11.656 ardışık segment çifti, **~%2 ayrışma**.

**B3:** *"Bu çift"* tanımsız — birikmiş grubun birleşik `bbox`'ı mı, grubun son bloğu mu? Kırmızı takım zıt sonuç ürettiğini gösterdi (birleşik kutu `bottom = max(bottom)` taşıdığı için negatif `gap` üretiyor, "kopuş yok" diyor — artifakt).

### K24 (YENİ) · Kuralın tek geçerli ifadesi

K21'in "denk ve daha kolay uygulanabilir ifade" cümlesi **iptal edilmiştir**. Geçerli tek ifade:

> Aynı `(a, b)` çifti, `_should_group`'un uyguladığı kontrollerden **yalnızca uzunluk kontrolü çıkarılarak** yeniden değerlendirilir. Başka hiçbir kontrol reddetmiyorsa uzunluk tek engeldir.
>
> Bu değerlendirmede **sol taraf, kapanan grubun okuma sırasındaki SON kaynak öğesidir** — birikmiş grubun birleşik `bbox`'ı değil. Birleşik kutu grubun en alta uzanan öğesinin `bottom`'unu taşıdığı için gerçek satır arası boşluğu ölçmez.

`max_group_chars`'ı sonsuz kabul eden **ikinci bir boru hattı koşusu değildir** — o koşu farklı bir bölümleme üretir.

**Zorunlu test:** en az bir öğesi sonrakilerden daha aşağı uzanan çok bloklu bir grubun kuyruğunda bu ayrımı sabitle.

---

## K25 (YENİ) · Uygulama seçeneği 1 zorunludur

Tur 4 iki seçenek sunmuştu. Kırmızı takım ölçtü: miras kararında **denkler** (160.000 çift, 0 ayrışma). Ama seçenek 2 `_group_rejection_reason`'ın dönüş tipini değiştiriyor ve **hâlihazırda yeşil olan** tester assertion'larını kırıyor (`tester_B/test_karar_uyumu_tur3.py:356,361,366`, `tester_C/test_cjk_misuse_scale.py:1138`).

**Seçenek 1 zorunlu.** Regresyon tabanı korunacak.

---

## K26 (YENİ) · K22'nin olgusal hatası düzeltilecek

K22 şunu diyordu: *"ikisi fullwidth, dördü uyumluluk formu."* **Yanlış.** Şefin ölçümü:

```
U+FE15 <vertical>   U+FE56 <small>   U+FF01 <wide>
U+FE16 <vertical>   U+FE57 <small>   U+FF1F <wide>
hepsi uyumluluk formu mu: True
```

Altısının **tamamı** Unicode uyumluluk formudur; fark yalnızca ayrıştırma etiketidir. Implementer bu ifadeyi docstring'e taşıdı (*"dördü **diğer** uyumluluk formu"*) — "diğer" hatayı kesinleştiriyor.

**Doğru ifade:**

> Altı karakterin tamamı ASCII dışıdır ve **altısı da Unicode uyumluluk (compatibility) formudur**; ayrıştırma etiketleri farklıdır: ikisi `<wide>` (fullwidth `！`/`？`), ikisi `<small>`, ikisi `<vertical>`. Sayı Python'un Unicode sürümüne bağlıdır (bu ölçüm: Unicode 15.0.0).

**Zorunlu test:** `unicodedata.decomposition` ile altısının da uyumluluk formu olduğunu ve etiket dağılımını sabitle. Bu, olgusal iddianın bir daha sessizce bayatlamasını önler.

---

## K27 (YENİ) · `menu` ön ayarı kapsam dışıdır — açıkça

Kırmızı takım (B7): `menu`'de `should_group=False` → `_group` çağrılmıyor → K19/K21 hiç devreye girmiyor. Karşı-olgusal soru orada **iyi tanımlı değil**, ve K19'un gidermeyi iddia ettiği sessiz kayıp `menu`'de aynen duruyor.

> K19/K21/K23 **yalnızca `should_group=True` olan ön ayarlarda** tanımlıdır. `menu`'de gruplama olmadığı için uzunluk kaynaklı bölünme kavramı yoktur; etiketsiz devam blokları `speaker=None` kalır ve bu **bilinçli, belgelenmiş bir kapsam dışıdır**.

Dört ön ayarın her biri için birer test bunu sabitleyecek.

---

## Kapı — tur 5'te ÜÇ mercek

Şefin tur 4'teki "Tester-A koşmasın" gerekçesi **yanlıştı** (kırmızı takım B9). Gerekçe *"K21 yeni bir garanti alanı açmıyor"* idi; açıyordu:

- Karşı-olgusal yüklemin alanı (B2, B3 tam olarak bu)
- `ignore_length` varsayılanının geriye dönük eşdeğerliği — hiçbir testle bağlı değil
- Ve B1 uyarınca miras, `speaker` daraltması değil **bölümleme değişikliği**

Üstelik B2'yi bulan yöntem (4000 girdilik ızgara/fuzz) tam olarak **A'nın merceğidir**. Şef, en büyük deliği bulacak merceği kapatmıştı.

**Tur 5'te A, B ve C koşacak.** Mercek listesi kırmızı takımın önerdiği sekiz maddeden türetilecek; en kritik üçü:

1. **Bölümleme kararlılığı** (K23 değişmezi) — A
2. **Karşı-olgusal alan ve "bu çift" tanımı** (K24) — A
3. **Zincir ve ön ayar alanı** (K27, geçişken miras, miras zincirinin geometrik kopuşta kesilmesi) — B ve C

---

## Bozmadan koru

K21'in doğru çalışan kısmı (bileşik sınırda miras yok — kırmızı takım 200.000 çiftte 0 ihlal ölçtü) · `_should_group` gövdesinin tek satırlık devretme deseni · `speaker` kontrolünün `length`'ten önce gelmesi · K15 matrisinin beş satırı · K16 · K17 · K18/K20 · K7 · K6 · K5 · K8 · K4 · K10 · K14 bütçe assertion'ı · K13 determinizm · asıl iş · ölçek

---

## Şefin kaydı

Karar kırmızı takımı **ilk koşusunda** üç yüksek şiddetli hata buldu — ikisi tester'ların ve şefin doğrulamasının kaçırdığı, biri (B1) uçtan uca çalıştırılarak gösterilen bir ürün hatası.

Bu, kapının değerini kanıtlıyor. Ama asıl ders kapı değil **yöntem**: bundan sonra şef kararları **önce değişmez olarak** yazılacak. K23 bu yeni biçimin ilk örneğidir.
