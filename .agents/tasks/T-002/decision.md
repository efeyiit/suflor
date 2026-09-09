---
task: T-002
role: orkestra-sefi
round: 2
decision: kabul
---

# Şef Kararı — T-002

**Kabul.** 2 turda kapandı.

## Tur 1 — RET

Kör tester bir **çökme hatası** buldu. Şef bağımsız olarak yeniden üretti ve kusurun bildirilenden geniş olduğunu gördü.

**Kusur:** `_block_mean_resize` içindeki `np.add.reduceat`, bölge hash ızgarasından küçük olduğunda patlıyordu.

| Bölge | Tur 1 davranışı |
|---|---|
| 1×1, 3×3, **4×4** | `IndexError` — çöküyor |
| 5×5 – 8×8 | Çalışıyor ama `divide by zero` → sessiz NaN |
| 16×16+ | Sağlam |

Tasarım §2.2 kullanıcının bölgeyi serbestçe yeniden boyutlandırmasına izin veriyor. Yani **küçük bölge çizen kullanıcı uygulamayı çökertiyordu.** Teslim edilen 25 testin hiçbiri bunu yakalamamıştı.

Bu kusuru bulduran şey `env.md`'ye yazdığım 6. saldırı noktasıydı: *"çok küçük bölge (1×1, 3×3)"*. Ortam Ajanı rolünün somut faydası.

## Şef kararı

Çökme ve sessiz NaN kabul edilemez. Küçük bölge geçerli bir kullanıcı davranışıdır (küçük sayaç, rozet, tek satırlık etiket). İlke: **`has_changed()` her bölge boyutu için tanımlı ve doğru bir sonuç döndürmeli.** Yöntem implementer'a bırakıldı, sonuç şartları sabitlendi: çökme yok, NaN yok, davranış belgelenecek, büyük bölgelerde regresyon olmayacak.

## Tur 2 — ONAY

Seçilen çözüm: hash ızgarasını bölgeye sığdıracak şekilde daraltmak (`min(out, n)`). Büyük bölgelerde tek bir `min()` karşılaştırmasından ibaret — davranış değişmiyor.

| Kontrol | Sonuç |
|---|---|
| Boyut taraması | 1×1'den 24×24'e 576 kombinasyon + 5 uç oran = **581 boyut**, `warnings=error` altında sıfır çökme/uyarı |
| Regresyon | Debounce, livelock, eşik, bölge sıfırlama, determinizm, saflık — hepsi yeniden doğrulandı |
| Bütçe | max 1.61 ms (sınır 5 ms) |
| Test sayısı | 25 → **434** |

## Şefin kendi sondaması ve bir düzeltme

Şef ilk sondasında dar bölgelerin hep `False` döndüğünü gördü ve bunu hata sandı. **Sonda hatalıydı:** rastgele kare besleniyordu, hiçbir şey kararlı olmadığı için debounce zaten onay vermez. Doğru sınamada (kararlı A,A,A → B,B,B dizisi) yatay desenli içerikte 2×40'a kadar her boyut algılıyor.

Bu, sistemin kendi kuralının şefe de uygulandığı bir an oldu: iddia kanıtla değil, **doğru kurulmuş** kanıtla geçerlidir.

## İki davranışsal sınır — kabul edildi, belgelendi

**1 · `w = 1` hiçbir yükseklikte algılamıyor.** dHash yatay komşu farkına bakar; tek sütunlu görüntüde 0 bit üretir. Yapısal, kaçınılmaz. Docstring'de doğru belgelenmiş.

**2 · Düz renk geçişi hiçbir boyutta algılanmıyor.** Düz koyu → düz parlak, 600×200 gibi büyük boyutta bile görünmez. Düz görüntüde tüm yatay farklar sıfırdır.

İkincisi ciddiye alındı ve tester'a **bloke edici kriter** olarak verildi: docstring'de açık ve doğru belgelenmemişse reddedilecekti. Tester bağımsız olarak 64×50 ve 600×200'de doğruladı ve belgelemenin eksiksiz olduğunu, "yalnızca küçük bölgelere özgüymüş gibi" yanlış sunulmadığını teyit etti.

Ürün açısından savunulabilir: metin her zaman yatay kenar üretir, dolayısıyla diyalog/menü değişimi algılanır. Kör nokta yalnızca "düz renk → başka düz renk" ki orada çevrilecek yazı zaten yoktur.

**Tester'ın eklediği incelik:** varsayılan `threshold=4` ile hem yükseklik hem genişlik çok küçükse (h≤4 ve w 2-4 bandı) bit bütçesi eşiği hiçbir içerikle aşamıyor. Docstring'de yazmıyor; bloke edici sayılmadı çünkü böyle bölgeler zaten OCR'a uygun değil. **Yol haritasına not:** bölge seçim arayüzü (A7) kullanıcıyı çok küçük bölge seçmekten caydırmalı.

## Şefin bağımsız doğrulaması

`mypy --strict` temiz · teslim testleri 434 geçti · tester testleri 629 geçti · tüm depo 697 geçti · sahiplik temiz.

## Sonuç

`src/capture/change_detector.py` **kabul edildi**. Dalga 1 kapandı.
