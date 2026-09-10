# Şef Kararı — T-004, Tur 6 (sürüm 7 — altı KRT geçişi; ölçüler **kod**, kit sürüm 2)

Tur 5'te **A ret** verdi, **B onay**, **C onay**. K23 değişmezi **sağlandı** (A: 12.800 koşumda 0 bölümleme farkı; implementer: 2500'de 0). Kalan: K24'te yeni bir etkileşim hatası (R5-1) ve B/C'nin belgeleme bulguları.

> **Sürüm 7 neden var — ve "sonuncusu" demenin bedeli.** Sürüm 6, ölçüleri koda taşıyıp "bu sonuncusu" demişti. Altıncı geçiş **kiti kırdı**: 26 yeni mutantın 13'ü kitin üç ön ayarını da `TEMİZ` geçti, yedisi ayrıca 478 kör testte doğru uygulamayla birebir aynı çıktı verdi. Kök sebep kitin **kendi tasarımındaydı** ve şef onu doğruladı: `referans_cifti` referansı **mutantın kendi verdiği `source_blocks`'tan** türetiyordu. Kit yalnızca *"verdiğin bbox verdiğin `source_blocks` ile tutarlı mı"* diye soruyordu; *"doğru öğeyi mi verdin, doğru yerde mi sordun"* diye sormuyordu.
>
> Ölçüyü koda taşımak doğru hamleydi ama yetmedi: **kod da yanlış şeyi ölçebiliyor.** Kit sürüm 2 üç kanal ekliyor:
> 1. **Bağımsız kimlik kanalı** — kit adım 1–4'ü kendi yeniden türetir (`adim1_4`) ve her sorguda sol tarafın bir **öğenin** `source_blocks`'u, sağ tarafın onu **hemen izleyen** öğe olduğunu doğrular. Mutantın verdiği veriye güvenmez.
> 2. **Kapsam denetimi** — `ignore_length=False` (bölümleme) çağrıları da kaydedilir ve bunlarda bbox'ın `source_blocks`'un **birleşik** kutusu olduğu, yani ham ikamenin o yola **sızmadığı** doğrulanır. K28'in kapsam cümlesinin ölçüsü budur.
> 3. **Altı yeni girdi sınıfı** — ASCII-dışı (CJK/RTL), `w<=0`/`h<=0`, negatif koordinat, ≥16 bloklu girdi, iki konuşmacı, ≥5 bloklu derin zincir; her birinin **kendi alt sınırı**. Sürüm 1'in derlemi bunların hiçbirini üretmiyordu.
>
> **Şefin kit sürüm 2 doğrulaması** (13 kaçan mutant, ön ayar başına 2500 girdi):
> ```
> mutant  ne yapiyor                         surum 1   surum 2
> n06     tail birlesim dalinda guncellenmiyor TEMIZ    KIMLIK 2615/1542/930
> n08     taraflar takas                       TEMIZ    KIMLIK 3700/6449/8047 + fixture
> n10     bir onceki oge                       TEMIZ    KIMLIK 3367/4893/5900 + eksik derin_sol
> n19     kapsam ihlali (bolumleme sorgusu)    TEMIZ    KAPSAM 5990/5664/5519
> n20     ayni ihlal, yalniz coklu kuyrukta    TEMIZ    KAPSAM 4992/4679/4485
> n11     ASCII-disi metinde ikame atlanir     TEMIZ    geo 308/353/358
> n13     derin zincirde atlanir               TEMIZ    geo 264/286/288
> n14     buyuk girdide atlanir                TEMIZ    geo 734/1073/1241
> n15     negatif koordinatta atlanir          TEMIZ    geo 135/337/430
> n17     iki konusmaci varsa atlanir          TEMIZ    geo 125/315/398
> n05     takma adla ham-ikamesiz karar        TEMIZ    olcu3 fixture KIRIK
> n22/n24 (KRT: davranissal olarak ESDEGER)    TEMIZ    TEMIZ   <- dogru, isaretlenmemeli
> dogru uygulama                               TEMIZ    TEMIZ
> ```
> **Kapanmayan iki mutant — ölçülmüş sınır, gizlenmiyor:** `n18` (doğru sorgu + fazladan `ignore_length=False` koşulu) ve `n23` (görünüm geçişi ters yönde) kit sürüm 2'yi de geçiyor. İkisi de sorgu **yapısında** değil **davranışta** ayrışıyor; yakalamak kitin `_group`'un miras kararını **yeniden uygulamasını** gerektirir ve şefin kendi yeniden uygulaması yanlış olursa kapı sessizce bozulur. Bu yüzden kite eklenmiyor, **Tester-B'nin mutant yükümlülüğüne** çevriliyor (aşağıda M10/M11). Kararın §4.6/2 dürüstlüğü gereği: bu iki sınıf **kit tarafından ölçülmüyor**.
>
> **Sürüm 6'nın iki olgusal hatası düzeltildi:** (a) "O2: kapsam ihlali yalnız ölçü 7'yle görünür" — yanlıştı, ölçü 7 bunu **yapı gereği göremez** (bölümleme geçişi `apply_inheritance`'ı hiç okumaz); doğru kapı kitin **kapsam kanalı**dır. (b) "M26 → ölçü 3b kırılmalı" — yanlıştı; `olcu3b` fixture'ı K28 **öncesi de yeşil**, ayırt ediciliği yalnız sorgu çiftinde. Zorunlu test artık çıktıyı değil **sorgu çiftini** assert eder.
>
> **Sürüm 6 neden vardı.** Beşinci geçiş 2 yüksek daha verdi ve ikisi de yine **ölçülerdeydi**, değişmezde değil:
> **(V1)** Kararın **hiçbir** fixture'ında ve ölçü 6'nın derleminde kapanan grubun kuyruğu **2 bloktan büyük değildi**. İki elemanlı bir kümede `sirali[-1]` ile `sirali[1]` **aynı şeydir** — şef ölçtü: `(0,2)` için ikisi de `2`; `(0,2,5)` için `5` ve `2`, ayrışıyorlar. Sıradan bir off-by-one (`m26`) sekiz ölçüyü **ve** 478 kör testi geçiyordu (2943 ayrışma).
> **(V2)** Ölçü 6'nın kancası `(a, b, params)` görüyor; `tail`/`nxt` kimliği imzada **yok** (şef AST ile doğruladı: üç çağrının üçü de üç konumlu argüman). Referans yalnız `a.source_blocks`'tan geri kazanılabiliyor, ama K28 o alanın korunmasını **şart koşmuyordu** — davranışsal olarak eşdeğer iki uygulama ölçüde zıt hüküm alıyordu.
>
> **Beş geçişte örüntü net:** değişmez sürüm 3'ten beri sabit; her geçişte kırılan **ölçünün düzyazı tarifi** oldu (geçiş 2 ayırt etmeyen fixture, geçiş 3 tek ön ayar, geçiş 4 mekanizmaya kancalanmış ölçü, geçiş 5 iki-eleman tavanı + kimlik kanalı). Düzyazı her turda yeniden yorumlanabildiği için döngü kapanmadı. Sürüm 6 bunu yapısal olarak bitiriyor: **ölçüler artık `.agents/tasks/T-004/olcu_kiti.py`'de kod olarak duruyor** — referans türetimi, derlem, alt sınırlar ve fixture'lar tek yerde, şef tarafından mutantlara karşı doğrulanmış halde. İmplementer ve tester onu **içe aktarır, değiştirmez**.
>
> **Kitin şef doğrulaması** (10 kum uygulaması, ön ayar başına 2500 girdi):
> ```
> uygulama                     DIALOGUE  TOOLTIP  SUBTITLE   fixture'lar
> dogru (K28 uygulanmis)        ayr=0     ayr=0    ayr=0      hepsi OK      <- alt sinirlarin hepsi tutuyor
> m26 off-by-one sirali[1]      2295      3173     3616       -             <- V1: 8 duzyazi olcusunu geciyordu
> m8s subtitle-kapili           0         0        6707       -             <- W1
> m9  suzulmus blocks       207+638pat  122+875  51+983       -             <- W2
> m4  indeks sirasi             1429      2425     2881       olcu3 KIRIK
> m5  sag taraf nxt kalir       1735      3464     4204       -
> m8k dialogue-kapili           0         5572     6707       olcu3T KIRIK
> m22 source_blocks yeniden yazar  uclu_sol=0 (alt sinir ihlali, gurultulu kirilir)   <- V2 onkosulu
> m10 speaker/text de ikame     0         0        0          hepsi OK      <- ESDEGER, dogru sekilde isaretlenmiyor
> m14 ikili anahtar             0         0        0          hepsi OK      <- ESDEGER, dogru sekilde isaretlenmiyor
> ```
> Kitin kendi alt sınırları (ön ayar başına): `sinir` 3273/5796/7081, `coklu_sol` 2775/3860/4443, **`uclu_sol` 2311/3196/3642**, `coklu_sag` 1808/3625/4430, `esik_alti` 1084.
>
> Şefin sürüm-5 hatası yine §4.6/4: fixture'lar mekanizmanın değişmezden ayrıştığı girdiyi (3+ bloklu kuyruk) içermiyordu.
>
> **Sürüm 5 neden vardı.** Dördüncü geçiş **11 bulgu** verdi (2 yüksek). İkisi de şef tarafından yeniden üretildi:
> **(W1)** Ölçü 3'ün `dialogue`+`tooltip` parametrizasyonu **yetmiyor**: kapıyı bir kademe gevşetip `subtitle`'a kapayan mutantlar (üç varyant — `max_group_chars >= 200`, `confidence_threshold >= 0.60`, `max_vertical_gap_ratio <= 0.8`; hepsi `dialogue` ve `tooltip`'te **doğru**) sekiz ölçünün **hiçbirine** takılmıyor. Şef KRT'nin diferansiyel sürücüsünü kendi eliyle koştu (4000 girdi/ön ayar, referans = doğru uygulama):
> ```
> mutant      DIALOGUE   TOOLTIP  SUBTITLE      MENU
> base            1273      1554      1698         0
> m8s                0         0      1698         0   <- sekiz olcuyu de geciyor
> m8s_conf           0         0      1698         0
> m8s_gap            0         0      1698         0
> ```
> Kök sebep yapısal: ölçü 6'nın kancası `_raw_query_pair`'e takılıyor, kapı kapalıyken o fonksiyon **hiç çağrılmıyor**, kayıt boş kalıyor ve "ayrışma 0" çıkıyor. Ölçü artık **mekanizmayı değil değişmezi** kancalıyor (aşağıda).
> **(W2)** *"M9 → ölçü 6 kırılmalı"* iddiası **yanlıştı**: ölçü 6'nın derleminde **tek bir eşik-altı blok yok** (şef doğruladı: derlemin her bloğu `confidence=0.9`), dolayısıyla süzülmüş `blocks` indeks kaydırmıyor ve mutant ölçü 6'yı geçiyor. Aynı yanlış iddia implementer'ın **ürün docstring'ine** yazılacaktı.
>
> Aynı koşumda üç "eşdeğer mutant" iddiası da bağımsız doğrulandı: `m14` (ikili anahtar), `m15` (`tail`→`current`), `m10` (`speaker`/`text` de ikame) — üçü de dört ön ayarda **0 ayrışma**.
>
> Şefin sürüm-4 hatası yine §4.6/3: iki "ölçüldü" iddiası (dayanıklılık penceresi, "96 kırık hepsi `IndexError`") ham çıktısı olmadan yazılmıştı ve ikisi de yanlıştı.
>
> **Sürüm 4 neden vardı.** Sürüm 3 üçüncü geçişten **11 bulguyla** döndü (3 yüksek). Üçü de şef tarafından yeniden üretildi, üçü de doğru:
> **(Z1)** *"`normalize` içinde `apply_inheritance=True` açıkça yazılır"* maddesi **10. bir testi kırıyor** ve §4.6/5 listesinde yoktu. `tester_B::test_r5_k23_normalize_gercekten_miras_ACIK_yola_delege_ediyor` şıkkı (b), anahtar kelimenin **yokluğunu** bilerek pinliyor: *"delegasyon anahtar kelimeyi GEÇMEDİĞİ için ürün davranışı TAM OLARAK bu varsayılana bağlı"* (şef testin gövdesini okudu). Madde **geri çekiliyor** — varsayılan zaten `True` ve B'nin testi bunu hem yapısal hem davranışsal pinliyor; şefin eklemesi kapıyı iyileştirmiyor, yalnız bir kapı aletini kırıyordu.
> **(Z2)** Sekiz ölçünün **hiçbirinin kırmadığı** bir mutant var: ham ikameyi yalnız `max_group_chars >= 280` iken uygulayan (yani `dialogue`'a kapılı) uygulama. Sebep: ölçü 1–6 ve 8'in **tüm** fixture'ları `dialogue`, ölçü 7 ise speaker'dan bağımsız. KRT ölçtü: 22.000 koşumda 687 satır ayrışıyor — 306 `tooltip`, 381 `subtitle`, 0 `dialogue`. R5-1'in kökü (`_merge_hyphenated`) ön ayardan bağımsız olduğu için bu gerçek bir açık.
> **(Z3)** *"İkili anahtar kullanan bir uygulama eşitlikte ayrışır"* cümlesi **ölçümle yanlış**. Şef koştu: 200.000 örnekte 69.721'i eşit `(y,x)` çifti içeriyor, ikili ile üçlü anahtarın sıralaması **0 kez** ayrışıyor — çünkü `source_blocks` K8 gereği artan ve `sorted` kararlı, yani eşitlikte ikili anahtar zaten girdi indeksine düşüyor. Üçüncü bileşen davranışsal bir **no-op**. Aynı kökten: K24'ün "`current` değil `tail`" kuralı sürüm 3'te **anlamını yitiriyor** (bbox artık `source_blocks`'tan geliyor, `current.source_blocks ⊇ tail.source_blocks` ve okuma-sırası-son ikisinde de aynı) — B'ye verilen "M3'ü yeniden nişanla" talimatı **ölü mutant** üretirdi.
>
> Şefin sürüm-3 hatası §4.6/3 sınıfı: Z3'te "ölçtüm" diye yazdığı sayı (`sorted(...)[-1]=1` / `max(...)=0`) **başka bir şeyi** ölçüyordu — okuma sırası ile indeks sırasını, ikili ile üçlü anahtarı değil.
>
> **Sürüm 3 neden vardı.** Sürüm 2 ikinci geçişten **12 bulguyla** döndü (3 yüksek). Üçü de şef tarafından yeniden üretildi ve üçü de doğru çıktı:
> **(Y1)** Sürüm 2'nin ölçü-3 fixture'ı (Q,P,R) hiçbir şey ölçmüyordu — şef koştu: fixture taban, doğru uygulama ve mutantın **üçünde de** `[((0,1,2),'Ada')]` veriyor, yani tek segment; kararın yazdığı "son segment `speaker=None`" beklentisi **hiçbirinde** tutmuyor. İmplementer o testi yazsaydı asla geçiremezdi. Düzeltilmiş fixture (aşağıda) üçünü ayırıyor.
> **(Y2)** "Varsayılansız `_Item` alanı, unutulan inşa noktasını gürültülü kırar" gerekçesi **ölçümle çürüdü**: şef koştu — o seçenek kör tester takımında **70 kırık** (123 `TypeError` satırı) üretiyor ve `tester_A`'nın `except (ValueError, TypeError)` blokları (6 yer) bunları **yutup** testleri yeşil-ama-boş bırakıyor; sürüm 1'in reddettiği seçenek, `blocks` **keyword-only ve varsayılanlı** yazıldığında yalnız **9 kırık** veriyor ve `tester_C`'nin `_group([], params)` çağrısını **kırmıyor** (sürüm 1 o seçeneği "zorunlu konumsal parametre" varyantıyla ölçmüştü — yanlış varyant).
> **(Y3)** Sürüm 2'nin adım-5 `first_raw_bbox`/`last_raw_bbox` yayılım kuralı **ölçülemezdi**: `tail` daima adım-4 çıktısı ham bir öğedir (`tail` değişkeninin üç atamasının üçü de `items[0]` ya da `nxt` — şef AST ile doğruladı), birikmiş `current` sorguya hiç girmez; yayılımı tamamen ters çeviren bir mutant 478 testin hiçbirine takılmıyordu.
>
> Y2'nin ölçümü tasarımı da sadeleştirdi: `_Item`'a alan eklenmediği için taşınacak bir şey kalmıyor — okuma sırasındaki ilk/son blok **sorgu anında** `source_blocks` üzerinden türetiliyor. Bu Y3'ü kaynağında yok ediyor.
>
> Şefin sürüm-2 hatası, aynı belgede eklediği PROTOKOL §4.6/4 kuralının ihlaliydi: fixture, mekanizmanın değişmezden ayrıştığı bir girdi içermiyordu.
>
> **Sürüm 2 neden vardı.** Sürüm 1'in K28'i karar kırmızı takımından (KRT) **13 bulguyla** döndü (4 yüksek). Özü: K28'in formülü (`source_blocks[-1]`) **yanlıştı** — `source_blocks` indeks sıralı, okuma sırası `(y, x)`; K3 girdiyi sırasız kabul ettiği için ikisi aynı şey değil ve formül bugün doğru olan bir noktada regresyon üretiyordu. K28 **sağ tarafı** hiç tanımlamıyordu; ölçüsü yanlış uygulamayı doğrudan ayıramıyordu; "dört xfail XPASS olur" iddiası ölçülmemişti ve yanlıştı; K29'un kapısı kendi iki hedef ihlaliyle yeşildi. Şef 13 bulgunun **hepsini kendi eliyle yeniden üretti** (KRT sondaları `scratchpad/krt6/`, şef koşumları bu belgeye işlendi). Şefin sürüm-1 hatası K24'ünkiyle aynı sınıf: **mekanizma yazıp değişmez sandı** ("`source_blocks[-1]`" mekanizmadır; "okuma sırasındaki son ham blok" değişmezdir).

---

## Bulgu R5-1 · `tail`, adım 3'ten sonra "ham" değil — ve `nxt` de değil

**Bulan:** Tester-A (sol taraf) · KRT (sağ taraf) · **Şef doğrulaması:** `sonda_r5_bulgu.py` (sol, 3 varyant); KRT `sonda2_k28_sag_taraf.py` şef koşumu (sağ, 3 varyant)

K24: *"sol taraf, kapanan grubun okuma sırasındaki SON HAM öğesidir."* Uygulama `tail = nxt` ile bunu yaptı. Ama K2'nin sırasında **adım 3** (`_merge_hyphenated`, K5) **adım 5**'ten (`_group`) önce çalışır ve hyphen'li satırları tek `_Item`'a birleştirir — o `_Item`'ın bbox'ı **birleşik kutu**. `_group` bunu `nxt` olarak alıp `tail` yapınca K24'ün kaldırdığı artifakt adım 3 üzerinden geri gelir. **Aynı şey sağ tarafta da olur:** aday (`nxt`) adım 3'ten birleşik gelirse `ref_height`/`ref_width`/`overlap` birleşik kutudan hesaplanır ve sorgu gevşer.

```
SOL (A):   A non-monotonik: tail h=50 (birlesik), ham son satir h=18 -> sorgu None, gercek 'gap'
           B monotonik    : tail h=35 (birlesik), ham son satir h=5  -> sorgu None, gercek 'gap'
           C monotonik    : tail w=308 (birlesik), ham son satir w=8 -> sorgu None, gercek 'overlap'
SAG (KRT): A2 monotonik   : aday ham ilk satir h=0, birlesik h=18   -> sorgu None, gercek 'height' (K16 ihlali gizleniyor)
           B monotonik    : aday birlesik h=50, ham ilk h=5         -> sorgu None, gercek 'gap'
           C monotonik    : aday birlesik w=308/x=0, ham ilk w=8/x=300 -> sorgu None, gercek 'overlap'
sonuc (altisinda da): speaker='Ada' gercek kopusun otesine atfedildi
```

A'nın ölçümü (sol): 30.174 sınırın %5,2'si. KRT'nin ölçümü (sağ): birleşik aday içeren 2065 sınırın 242'si ayrışıyor, 239'u tehlikeli yönde (%11,6). Altı yolun beşi monotonik — "egzotik geometri" savunması kapalı.

### Şefin hata analizi (iki tur)

Tur-6 sürüm 1'de şef R5-1'i "sol taraf" sanıp `source_blocks[-1]` yazdı. İki hata: (1) sağ tarafı hiç düşünmedi; (2) "K8 gereği `source_blocks` artan sırada → `[-1]` son ham blok" çıkarımı **indeks sırası ile okuma sırasını** karıştırdı. K3 *"girdi blokları sırasız gelebilir"* diyor; `_normalize_impl` gerçekten `sorted(enumerate(blocks), key=(y, x))` yapıyor (şef doğruladı). KRT ölçtü, şef yeniden üretti: Q,P,R dizilişinde (`blocks[0]=y10`, `blocks[1]=y0 etiketli h100`, `blocks[2]=y45`) `current.source_blocks=(0,1)` → `[-1]=1` ama okuma sırasındaki son blok **0**; K28-birebir sol taraf `bbox(y=0,h=100)` → gap **-55px** → miras **açılır**; ham gerçek gap **17px > 14.4** → gerçek kopuş, miras **olmamalı**. Bugün kod doğru; K28 birebir uygulansa yanlış olurdu. A'nın derleminde 25.460 sınırın 823'ünde (%3,2) `[-1]` ≠ okuma-sonu; sırasız girdilerde %8,5. Ek yüzey: sırasız girdide `[-1]` **etiket bloğunu** (segment üretmeyen, K9 ile taşınmış) gösterebilir.

**Kök (A'nın tur-5 gözlemi 3, KRT B11):** `_merge_hyphenated` hiçbir geometrik kontrol yapmıyor; R5-1'in kökü adım 3'ün **çok bloklu `_Item`** üretmesidir. K28 semptomu kapatır; kök **bilinçli olarak açık bırakılır** — adım 3 salt tipografiktir (K5) ve öyle kalır. `known_gaps`'e yazılır (aşağıda).

---

## K28 (sürüm 3) · DEĞİŞMEZ — Miras-uygunluk sorgusunun İKİ tarafı da özgün bloktan gelir

> **DEĞİŞMEZ:** Bir grup kapanırken miras-uygunluk sorgusuna (`_group_rejection_reason(..., ignore_length=True)` çağrısı) verilen **iki** geometri de `normalize`'a verilen **özgün** `TextBlock` listesinden gelir:
> - **sol taraf** `bbox` = kapanan grubun kaynak blokları arasında **okuma sırasındaki son** bloğun bbox'ı;
> - **sağ taraf** `bbox` = adayın (`nxt`) kaynak blokları arasında **okuma sırasındaki ilk** bloğun bbox'ı.
>
> **Okuma sırası** = `(bbox.y, bbox.x, girdi indeksi)` artan — `_normalize_impl`'in **adım 1**'de kullandığı kararlı `sorted(enumerate(blocks), key=(y, x))` çağrısıyla **aynı** (tam tanım ve gerekçe aşağıda). Hiçbir birleşik `_Item` bbox'ı (adım 3'ten veya adım 5'ten) bu sorguya girmez. Sorgunun `speaker`/`text` alanları sırasıyla `tail` ve `nxt`'ten alınır; **yalnızca `bbox` ikame edilir** — bu alt kural **`[ÖLÇÜLMÜYOR]`**: çağrı `nxt.speaker is None` ile kısa devre olduğu ve `ignore_length=True` uzunluk kontrolünü atladığı için `speaker`/`text` bu çağrı noktasında **ölü alanlardır**; ikisini de ham bloktan alan bir uygulama davranışsal olarak eşdeğerdir (şef ölçtü: dört ön ayar × 4000 girdi, 0 ayrışma). Kural okunabilirlik ve `ignore_length` bir gün kaldırılırsa doğruluk içindir.
>
> **`source_blocks[-1]` / `[0]` KULLANILMAZ:** `source_blocks` K8 gereği artan **indeks** sırasındadır; K3 gereği girdi listesi okuma sırasında olmak zorunda değildir; en büyük indeks ile okuma sırasındaki son blok **aynı şey değildir** (ölçüm yukarıda).
>
> **Ölçünün önkoşulu (V2):** ham ikame `dataclasses.replace(...)` ile yapılır; `speaker`, `text` **ve `source_blocks`** aynen korunur, yalnız `bbox` değişir. `source_blocks`'un korunması ürün davranışı için **ölü** bir alandır (yeniden yazan uygulama 16.000 koşumda 0 ayrışma verir) ama **ölçünün önkoşuludur**: kanca yalnızca `(a, b, params)` görür — `tail`/`nxt` kimliği başka hiçbir kanaldan geri kazanılamaz (şef AST ile doğruladı). Yeniden yazan bir uygulama ölçü 6'yı `uclu_sol=0` alt sınır ihlaliyle **gürültülü** kırar; sessiz geçmez.
>
> **Kapsam (K24'ten devralınır):** bu değişmez YALNIZCA miras-uygunluk sorgusu içindir. `_group`'un ana birleştirme kararı (bölümleme geçişi) K10/K11 uyarınca `current`'ın **birleşik** bbox'ını kullanmaya devam eder; K23'ün iki-geçiş yapısı değişmez.

### Uygulama — ölçülmüş seçim

Sürüm 1 seçimi implementer'a bıraktı, sürüm 2 yanlış seçeneği ölçmeden seçti. Şef ikisini de kum havuzunda koştu (kör tester takımı: `tests/unit/ocr` + `tester_A/B/C`, taban **474 passed, 4 xfailed**):

```
repo_base  (K28 yok)                                474 passed, 4 xfailed     TypeError satiri: 0
repo_i     (surum 2: varsayilansiz _Item alani)      70 failed, 407 passed    TypeError satiri: 123
repo_opt1  (_group(..., *, blocks=()) )               9 failed, 468 passed    TypeError satiri: 0
```

Kör tester dosyaları `_Item(...)`'ı **103 kez** doğrudan kuruyor (A: 23, B: 66, C: 14) ve `tester_A` altı yerde `except (ValueError, TypeError)` ile yutuyor — yani `_Item`'a alan eklemek yalnız çok kırmakla kalmıyor, bir kısmını **sessizce boşaltıyor**. Karar:

- **`_Item` DEĞİŞMEZ.** Yeni alan yok, adım 3/adım 5 yayılımı yok, taşınacak geometri yok.
- `_group` imzası: `_group(items, params, *, blocks: Sequence[TextBlock] = (), apply_inheritance: bool = True)` — `blocks` **keyword-only ve varsayılanlı**; `tester_C`'nin `_group([], params)` doğrudan çağrısı kırılmaz.
- Modül düzeyinde yardımcı: `_raw_query_pair(tail: _Item, nxt: _Item, blocks: Sequence[TextBlock]) -> tuple[_Item, _Item]` — her iki tarafın kaynak indekslerini **okuma sırası anahtarıyla** sıralayıp `replace(tail, bbox=blocks[son].bbox)`, `replace(nxt, bbox=blocks[ilk].bbox)` döndürür. Geometri **sorgu anında** türetilir; saklanan ve bayatlayabilecek bir kopya yoktur.
- Miras sorgusu görünüm geçişinde: `_group_rejection_reason(*_raw_query_pair(tail, nxt, blocks), params, ignore_length=True)`. `_group`'un bölümleme döngüsü içinde `replace(...)` **yazılmaz** (`tester_B::test_r5_k23_bolumleme_gecisinde_hicbir_speaker_mutasyonu_yok` **her** `replace` çağrısını yasaklıyor — şef AST'sini okudu, kapsam doğrulandı).
- **`_should_group` imzası ve tek satırlık devretme deseni değişmez.**
- `_normalize_impl` `_group`'u çağırırken `blocks=blocks` geçmek **zorundadır**; varsayılan `()` yalnız doğrudan çağıran testler içindir. Bu, ölçü 5'in AST yarısıyla pinlenir.
- **`_raw_query_pair` sözleşmesi — docstring'e:** `blocks`, `normalize`'a verilen **özgün** listedir (adım 1'de elenen bloklar dahil; indeksler özgün indekslerdir). Sıkıştırılmış/süzülmüş bir liste geçirmek indeks kaymasına yol açar; bunu **ölçü 5'in AST yarısı** (`blocks=blocks` yazılı mı) ve — yalnız derlem eşik-altı blok içerdiğinde — **ölçü 6** yakalar. `_group`'un `blocks=()` varsayılanı yalnızca `items` boşken ya da **uzunluk-tek sınır doğmayan** doğrudan çağrılar için geçerlidir; aksi hâlde `IndexError` yükselir. Bu **bilinçlidir**: sessiz yanlış üretmez, ama patlama gecikmelidir (yalnız `reason == "length" and nxt.speaker is None` sınırında) — KRT ölçtü: `blocks=` hiç geçirilmezse kör tester takımında **96 kırık — 90'ı `IndexError`, 6'sı zaten §4.6/5'te bayat sayılan kapı aletlerinin `AssertionError`'ı**.

**ÖLÇÜ — `.agents/tasks/T-004/olcu_kiti.py` (şefe ait; içe aktarılır, değiştirilmez).**

Kit şunları sağlar ve implementer ile üç tester **aynı** kaynaktan kullanır:

| Kitten gelen | Ne | Neyi kapatıyor |
|---|---|---|
| `okuma_sirasi(blocks, idxs)` | `(bbox.y, bbox.x, girdi indeksi)` artan sıra | tanımın tek kaynağı |
| `referans_cifti(blocks, sol_sb, sag_sb)` | sorgunun **alması gereken** `(sol.bbox, sag.bbox)` | geçiş 5 V2 |
| `sorgu_kaydi()` | `ignore_length=True` gelen **her** `_group_rejection_reason` çağrısını kaydeden bağlam yöneticisi | geçiş 4 W1 (değişmezi kancalar, mekanizmayı değil) |
| `derlem(n=2500)` | zincirleme hyphen (3+ bloklu kuyruk), eşik-altı bloklar (`conf=0.50`, üç ön ayarın da altında), `shuffle` | geçiş 5 V1, geçiş 4 W2, O1 |
| `olcu6_kos(preset)` | ön ayar başına denetim + alt sınırlar | geçiş 3 Z2, geçiş 4 W1 |
| `OLCU6_ALT_SINIRLAR` | `sinir≥1, coklu_sol≥500, uclu_sol≥200, coklu_sag≥500, esik_alti≥500` | totolojik denetimi imkânsız kılar |
| `olcu3_fixture` / `OLCU3_BEKLENEN` | sırasız girdi, **çift** bloklu kuyruk, `dialogue`+`tooltip` beklentileri | geçiş 2 Y1, geçiş 3 Z2 |
| `olcu3b_fixture` / `OLCU3B_BEKLENEN` | zincirleme hyphen, **üç** bloklu kuyruk (`tail.source_blocks=(1,2,3)`) | geçiş 5 V1 |
| `adim1_4(blocks, preset)` | `_group`'a giren öğe listesinin **bağımsız** yeniden türetimi | geçiş 6 Y1 (kimlik kanalı) |
| `birlesik_kutu(blocks, sb)` | bölümleme sorgusunun beklenen bbox'ı | geçiş 6 (kapsam kanalı) |
| `olcu5_fixture` | iki sınır, ikisinde de çok bloklu kuyruk | geçiş 4 O6 |

**Kitin içe aktarılması — şef çözdü, implementer'ın işi değil.** Depoda `pytest.ini`/`pyproject.toml` yok ve `tests/unit/ocr` bir paket değil; şef ölçtü: `from olcu_kiti import ...` → `ModuleNotFoundError`. Test dosyası içine `sys.path.insert` yazmak toplama sırasına bağlıdır (tester dizini **tek başına** koşulduğunda patlar). Şef iki **kendine ait** `conftest.py` teslim etti — `tests/unit/ocr/conftest.py` ve `.agents/tasks/T-004/conftest.py` — depo kökünü ve kit dizinini `sys.path`'e ekliyorlar. **İkisi de hiçbir görevin `owns`'ında değildir; implementer ve testerlar dokunmaz.** Şef doğruladı: `tests/unit/ocr` tek başına 98 passed, `tester_B` tek başına 117 passed, tam takım 795 passed (regresyon yok).

`python .agents/tasks/T-004/olcu_kiti.py` kitin **kendi sağlığını** sınar (derlem alt sınırları üretiyor mu, fixture'lar gerekli şekli veriyor mu, kanca kayıt tutuyor mu) — ürünün doğruluğunu değil. Şef koştu: `KIT: TEMIZ`.

**Zorunlu testler (`tests/unit/ocr/test_normalizer.py`):**
1. **Sol taraf** — A'nın üç varyantı: son segment `speaker=None`, bölümleme pinli.
2. **Sağ taraf** — üç varyant: adayın ham ilk satırı `h=0` iken birleşik kutu bunu gizler (**K16 regresyon testi**); birleşik `h` şişmesi; birleşik `w/x` şişmesi. Üçünde de son segment `speaker=None`, bölümleme `[((0,1),'Ada'), ((2,3),None)]` pinli.
3. **Sırasız girdi + çift bloklu kuyruk** — `olcu3_fixture()`, `dialogue` **ve** `tooltip` ile parametrize; beklenti `OLCU3_BEKLENEN`. Eşik dayanıklılığı (KRT ölçtü): `_DIALOGUE.max_group_chars` **227–367** aralığında doğru uygulamada geçer (368'de kırılır; `_TOOLTIP.max_group_chars = 200` sabit tutulduğunda — tablo birlikte ölçeklenirse pencere %81–%113'e daralır). İki ön ayarlı parametrizasyon M4'ü `max_vertical_gap_ratio`'nun **tüm 0,15–1,00 penceresinde** ayırt eder; yalnız `dialogue` ile bakılsaydı bant 0,67–1,00 olurdu (D1).
3b. **Zincirleme hyphen + ÜÇ bloklu kuyruk** — `olcu3b_fixture()`, beklenti `OLCU3B_BEKLENEN`. **Ölçü 3 tek başına yetmez:** iki elemanlı kuyrukta `sirali[-1]` ile `sirali[1]` aynıdır.
4. **İki yön** — ham geometriyle miras **uygulanması gereken** ama birleşik geometriyle uygulanmayacak bir vaka; bölümleme pinli.
5. **Yapısal test (iki taraf ayrı koşumlarda, artı AST)** — `olcu5_fixture()` ile `sorgu_kaydi()`; mutasyon (i) okuma-sırası-son ham blok, (ii) okuma-sırası-ilk ham blok; ikisinde de gözlenen çift **değişmeli**, birleşik `bbox` bozulduğunda **değişmemeli**; `gözlenen_sınır >= 2`. AST yarısı: `_normalize_impl` içindeki `_group(...)` çağrısı `blocks=` taşır **ve değeri `blocks` adının kendisidir** (`ast.unparse(kw["blocks"]) == "blocks"`).
3b. **(düzeltildi — geçiş 6)** `olcu3b`'nin zorunlu testi **çıktıyı değil sorgu çiftini** assert eder: `sorgu_kaydi()` ile alınan miras sorgusunda `sol_sb == (1,2,3)` ve `sol_bbox == blocks[3].bbox` (okuma sırasında son ham blok). Çıktı assert'i K28 **öncesi de yeşildi**, yani hiçbir şey ölçmüyordu (§4.6/4).
6. **Makine denetimi** — üç ön ayar için ayrı ayrı `olcu6_kos(preset)`; `r.temiz` (yani `ayrisma == 0`, **`kimlik_ihlali == 0`**, **`kapsam_ihlali == 0`**, `sira_ihlali == 0`, `patlama == 0`, `eksik_sinirlar == []`). (Kit alt sınırları kendi kontrol eder; test `r.temiz` ile assert eder ve `r.ilk_fark`'ı mesaj olarak verir.) Kitin eşik-altı güven değeri `ESIK_ALTI_CONF = 0.50` — **üç ön ayarın da eşiğinin altında** (SUBTITLE 0.55 < DIALOGUE 0.60 < TOOLTIP 0.65); ön ayar-bağımsız yazılsaydı `0.58` seçen bir derlem `subtitle` koşumunda eşik-altı blok üretmez ve M9 oradan geçerdi (O1).
7. **K23 korunur** — miras açık/kapalı bölümleme farkı 0, **üç ön ayarda ayrı ayrı**. *(Sürüm 6 burada "kapsam ihlalini yalnız bu koşum görür" diyordu; **yanlıştı** — bölümleme geçişi `apply_inheritance`'ı hiç okumadığı için ölçü 7 kapsam ihlalini **yapı gereği göremez**. Doğru kapı kitin **kapsam kanalı**dır, ölçü 6'nın içinde.)*
8. **Zincirleme miras** — `Ada: a` / `b` / `c` üç ayrı segmentte `['Ada','Ada','Ada']`.

**Tester-A'nın dört `strict=True` xfail'i (KRT iki geçişte de ölçtü):** parametrize edilmiş **üç** varyant düzeltme sonrası **XPASS ile kırılır** — A bunları yeşil testlere çevirir. **Dördüncüsü** (`test_r51_makine_denetimi_ham_son_blok_kuralinda_sifir_ayrisma`) `_group`'u/`normalize`'ı **hiç çağırmaz** (şef doğruladı: `_group_rejection_reason`'ı doğrudan çağırıyor, satır 811–825), gruplama döngüsünü test içinde kurar ve adım 3'ün ürettiği öğe yapısını ölçer — `_group`'taki hiçbir düzeltme onu XPASS yapamaz. A onu tur 6'da `normalize`/`_group` üzerinden geçen, sırasız girdi de içeren yeni bir makine denetimiyle **yeniden yazar**; tur 6 kapısı yeni denetimin yeşiline bakar.

**Tester-B'ye — kitin ölçmediği iki mutant sınıfı (zorunlu, M10/M11):** kit sürüm 2 sorgunun **kimliğini, kapsamını ve geometrisini** ölçer; sorgu **sayısı ve sırası** anomalilerini ölçmez. B bu ikisini mutant olarak taşır ve davranışsal diferansiyelle (≥3000 girdi × 3 ön ayar, doğru uygulamaya karşı) yakalar:
- **M10** — miras kararına fazladan bir koşul ekleyen mutant (ör. bölümleme sorgusunun sonucunu da şart koşan); KRT ölçtü: 4363 dar-diff ayrışma, kit `TEMİZ`.
- **M11** — görünüm geçişini ters yönde işleyen mutant (zincirleme mirası bozar); KRT ölçtü: 1322 ayrışma, kit `TEMİZ`.
B'nin diferansiyeli bu iki sınıfı **kırmak zorundadır**; kıramıyorsa B'nin sondası dişsizdir ve bu bir ret nedenidir.

**Tester-B'ye ve Tester-A'ya not (zorunlu — PROTOKOL §4.6/5):** K28 `_group`'un miras-sorgusu satırını değiştirdiği için şunlar **kaçınılmaz olarak bayatlar** (şef ölçtü, doğru uygulamada `-k k23` **5 kırık** veriyor):
- `tester_B/test_karar_uyumu_tur5.py:567` — `args[0] == "tail"` AST beklentisi;
- `tester_B/test_k23_mutant_sondasi_tur5.py` — **M1, M2 ve M3**'ün mutasyon desenleri (M1'in aradığı `_ANA_BLOK` deseni miras-sorgusu satırını **içeriyor**; sürüm 2 yalnız M2/M3 diyordu, eksikti);
- `tester_B/test_karar_uyumu_tur5.py::test_r5_k23_normalize_impl_bayragi_yalniz_group_cagrisina_iletir` — `_group` çağrısı artık `blocks=` de taşıyor;
- `tester_B/test_k23_mutant_sondasi_tur5.py::test_r5_mutant_m2_k21_ayrimini_da_bozuyor` — M2 desenini ayrıca arayan **dördüncü** test (sürüm 3 yalnız "M2 deseni" diyordu, testi ada göre saymıyordu).

`tester_A/test_r5_partition_invariant.py:401`'in kör-sonda testi **kırılmaz** ama sessizce bayatlar: kendi yerel `_group_tur4` kopyasını ölçtüğü için yeni sorgu biçimini hiç görmez. A onu yeni biçime nişanlar — kırılmadığı için kendiliğinden fark edilmez, bu yüzden burada yazılıdır.

**K23'ün değişmezi korunur** (ölçü 7); korunmayan, K23'ün **denetim aparatı**dır. B tur 6'da: (a) AST beklentisini `_raw_query_pair(tail, nxt, blocks)` biçimine göre yeniden yazar; (b) **M1 ve M2'yi** yeni satıra nişanlar (M3 için aşağıya bakınız); (c) **M4** ekler — `_raw_query_pair` içinde okuma sırası anahtarı yerine **indeks sırası** (`max(idxs)` ya da `sorted(idxs)[-1]`) kullanan mutant → **ölçü 3 ve 6 kırılmalı**; (d) **M5** ekler — sağ tarafı `nxt` olarak bırakan (ham ilk bloğa çevirmeyen) mutant → **ölçü 2, 5 ve 6 kırılmalı**; (e) **M8** ekler — ham ikameyi ön ayara kapılayan **iki** mutant: `dialogue`-kapılı (`params.max_group_chars >= 280`) → **ölçü 3'ün `tooltip` parametresi** kırılmalı; **`subtitle`-kapılı** (`params.max_group_chars >= 200`) → **ölçü 6'nın `subtitle` koşumu** kırılmalı (şef ölçtü: 4000 girdide 1698 ayrışma, `dialogue` ve `tooltip`'te 0 — sürüm 4'ün sekiz ölçüsünün hiçbiri bunu görmüyordu); (f) **M9** ekler — `blocks=` yerine süzülmüş/sıkıştırılmış liste geçiren mutant (indeks kayması) → **ölçü 5'in AST yarısı** kırılmalı, **ve** ölçü 6'nın eşik-altı bloklu derlemi kırılmalı (şef ölçtü: ayrışma + 638/875/983 `IndexError`); (g) **M26** ekler — `okuma_sirasi(...)[-1]` yerine `[min(1, len-1)]` (off-by-one) → **ölçü 3b** ve ölçü 6 kırılmalı (şef ölçtü: 2295/3173/3616 ayrışma; sürüm 5'in sekiz düzyazı ölçüsünün ve 478 kör testin **hiçbiri** görmüyordu).

B, mutantlarını **kitin `olcu6_kos`'una karşı** koşar; kit şefin doğruladığı tek ölçü kaynağıdır ve B onu **değiştirmez**. **M3 (`tail`→`current`) KALDIRILIR** — sürüm 3'ün biçiminde eşdeğer mutanttır (yukarıda, "K24'ün `tail` kuralının kapsamı"); yeniden nişanlanırsa ölü mutant olur. A `:401`'i yeni sorgu biçimine nişanlar. `test_r5_k23_bolumleme_gecisinde_hicbir_speaker_mutasyonu_yok` **değiştirilmez** — uygulama ona uyar.

**`known_gaps`'e ve `_merge_hyphenated` docstring'ine zorunlu:** "Adım 3 salt tipografiktir (K5) ve geometrik kontrol yapmaz; R5-1'in kökü budur ve bilinçli olarak açık bırakılmıştır. Birleşik öğe geometrisi adım 5'in miras kararına hiç girmez — sorgu anında `_raw_query_pair` onun yerine özgün blokları koyar; bölümleme kararına ise birleşik bbox ile girer (K10/K11)."

---

## Tester-B (tur 5): ONAY — 27/27; üç not zorunlu düzeltmeye dönüştü

B, K23'ün iki-geçiş yapısını AST ile ispatladı, mutant sondasıyla K23 ve K24 denetimlerinin birbirinden bağımsız dişli olduğunu gösterdi, ve `normalize ≡ _normalize_impl(..., True)` bağını pinledi.

### K29 · Docstring'de anılan her test adı var olmalı — kapı yeniden yazıldı

B'nin bulgusu: `normalizer.py:92` `test_k2_esik_alti_blok_ortada`'yı (gerçek ad `test_k2_esik_alti_orta_blok_komsulari_birlestirir`), `:203–204` K26'nın zorunlu testini `test_k26_alti_karakterin_hepsi_uyumluluk_formu_ve_etiket_dagilimi_dogru` diye anıyor (gerçek ad `..._formu_ve_etiket_dogru`) — **ikisi de yok.** PROTOKOL §4.6 kural 2 ihlali.

KRT'nin bulgusu (B5, şef doğruladı): şefin sürüm-1 kapısı bu iki ihlalin **birini** görmüyordu — docstring satır sarması adı `_` üzerinden bölüyor, kapı bölünmüş kuyruğu "ön-ek" sayıp geçiriyordu; cümle sonu noktası da adı maskeliyordu. Şef kapıyı yeniden yazdı: satır-sonu bölünmeleri taramadan önce birleştirilir, `.py` dosya adları dışlanır, ön-ek **yalnızca açık `*`** ile kabul edilir (çıplak `_` sonlu ad ihlaldir), ve kapı **kendini sınar** (`python purity_check.py --selftest`; ana koşum da kendini-sınamayı önce koşar). Yeni kapı iki gerçek ihlali de raporluyor.

**DEĞİŞMEZ:** `normalizer.py`/`presets.py` docstring'lerinde `test_` ile başlayan her tanımlayıcı, `tests/unit/ocr/test_normalizer.py` içinde `def <ad>(` olarak **var**; ön-ek atfı yalnızca `test_x_*` biçiminde.
**ÖLÇÜ:** `python .agents/tasks/T-004/purity_check.py` — tur 6 kabul komutudur, **exit 0 şart**. İmplementer iki bayat adı düzeltir; varsa çıplak `_` sonlu ön-ek atıflarına `*` ekler.

### K30 · K2 × K19/K21 etkileşimi — koşullu cümleyle belgelenecek

B'nin bulgusu: monoloğun ortasında eşik-altı bir satır düşünce (adım 1) yerinde gerçek bir geometrik boşluk kalıyor. KRT ölçtü, şef yeniden üretti (B8): sonuç **artık boşluğun büyüklüğüne** bağlı — 22px (> 14.4 eşik) → miras kesilir; 4px (< 14.4) → miras korunur. Şefin sürüm-1 cümlesi koşulsuzdu; yanlıştı.

**Zorunlu — `_group` docstring'ine ve `known_gaps`'e:** "Adım 1'de düşen bir blok, adım 5'te geride **gerçek bir geometrik boşluk** bırakır — K2 bölümündeki 'o blok hiç var olmamış gibi çalışır' ifadesi metin/hyphen için doğrudur, geometri için değil. Bu artık boşluk `max_vertical_gap_ratio × min(h)` eşiğini **aşarsa** sınır artık yalnız-uzunluk sınırı değildir ve K21 uyarınca miras uygulanmaz; **aşmazsa** miras korunur. İkisi de K2 sırasının bilinçli sonucudur." **Test:** iki yol da birer testle sabitlenir (B'nin `test_r3_k2_*`'si ilk yolu; implementer ikinci yolu ekler).

B'nin üçüncü notu (`normalize` "sabit `True`" der ama kodda `True` yazılı değil) **geri çekildi.** Sürüm 3 bunu "açıkça yaz, bir satır" diye zorunlu kılmıştı; KRT ölçtü ve şef doğruladı: o satır `tester_B::test_r5_k23_normalize_gercekten_miras_ACIK_yola_delege_ediyor`'u kırar — testin (b) şıkkı anahtar kelimenin **yokluğunu** bilerek pinliyor (*"delegasyon anahtar kelimeyi GEÇMEDİĞİ için ürün davranışı TAM OLARAK bu varsayılana bağlı"*). Varsayılan zaten `True` ve B'nin testi bağı yapısal + davranışsal pinliyor. **`normalize`'ın gövdesi değişmez.**

---

## Tester-C (tur 5): ONAY — 125/125, B1 Japonca'da kapalı, mutasyon denetimi dişli

C, tur 4'ün hatalı `_group`'unu monkeypatch ile kurup kendi testlerini onun üzerinde koştu: B1 testi kırıldı, K23 fuzz'ı 48/2600 ihlal buldu — C'nin testleri ayırt ediyor. `speaker` Unicode codepoint düzeyinde korunuyor. Ölçek 2000 blokta 24.9 ms.

### K31 · Bitişik iki repliğin birleşmesi — iki alt durum, ikisi de belgelenecek

Şef sondası (a): `["Ada: merhaba", "Ada: nasilsin"]` → tek segment `'merhaba nasilsin'`, `speaker='Ada'`. KRT sondası, şef yeniden üretti (b): ikinci etiket K9 süzgecinden geçmiyorsa (`"Ada2: nasilsin"`, rakam) → `'merhaba Ada2: nasilsin'`, `speaker='Ada'` — **etiket metinde kalır, segment ilk konuşmacıya atfedilir.** (b) ürün etkisi olarak (a)'dan kötü; sürüm-1 cümlesi yalnız (a)'yı anlatıyordu.

Şef ikisini de **değiştirmiyor**: utterance sınırı olarak ikinci bloğun etiket taşıması kullanılmaz — K15'in bilinçli sınırı.

**Zorunlu — `_group` docstring'ine ve `known_gaps`'e:** "K15 uyarınca geometrik olarak bitişik iki replik, **ikinci bloğun konuşmacısı birinciyle aynı ya da `None` ise** tek segmentte birleşir (iki **farklı tanınan** ad birleşmez — şef doğruladı: `['Ada: merhaba', 'Bora: nasilsin']` → iki ayrı segment); ikinci bloğun etiket taşıması utterance sınırı sayılmaz. **(a)** İkinci etiket K9'a göre tanınıyorsa ve ad aynıysa etiket metinden düşer, segment tek `speaker` taşır. **(b)** İkinci etiket K9'un ad süzgecinden geçemiyorsa (rakam içeren ad, K32'deki NFD adlar) o blok `speaker=None` kalır, K15 `X/None` satırıyla bloklar yine birleşir, **etiket metnin içinde kalır** ve segment ilk konuşmacıya atfedilir. İkisi de bilinçli sınırdır." **Test:** (a) ve (b) birer testle.

### K32 · Girdi NFC varsayımı — modül düzeyinde, yalnız ad süzgecinde değil

Şef sondası: `'María: hola'` NFC → `speaker='María'`; NFD → `speaker=None`. KRT ölçtü, şef yeniden üretti (B10): NFD duyarlılığı `_split_speaker_label`'la sınırlı değil — `len()` codepoint saydığı için `max_group_chars` (K11) ve `_MAX_SPEAKER_NAME_LEN` (K9) da etkilenir: aynı 3 bloklu gövde NFC'de **1 segment**, NFD'de **3 segment**. Ayraç kümesi (`:`/`：`) etkilenmez.

Şef tur 6'da davranışı **değiştirmiyor** (K9/K11 sözlüksel kurallarına dokunmak yeni kapı turu; OCR çıktısı NFC olacak — T-006 paketine "çıktı NFC" maddesi şef ekler).

**Zorunlu — `normalizer.py` MODÜL üst docstring'ine, `_split_speaker_label` docstring'ine ve `known_gaps`'e (aynı kapsamla):** "`normalize` girdinin **NFC** olduğunu varsayar. Ad süzgeci codepoint bazlı `isalpha()`; NFD adlar (birleşik aksan) konuşmacı sayılmaz, etiket metinde kalır (K31/b). Bu varsayım süzgeçle sınırlı değildir: `max_group_chars` ve `_MAX_SPEAKER_NAME_LEN` codepoint sayar; aynı görünen metin NFD gelirse **bölümleme de değişir** (ölçüm: 3 blok NFC'de 1 segment, NFD'de 3). NFC normalizasyonu T-006 çıkış sözleşmesine adaydır." **Test:** NFC/NFD aynı gövde → segment sayısı farkı bir testle sabitlenir (davranışı **belgeleyen** test, düzelten değil). **Gövde pinlenir:** segment sayısı farkı yalnız **gövdesi de aksanlı** metinde doğar (şef ölçtü: yalnız etiket aksanlıysa NFC 1 / NFD 1 segment; gövde de aksanlıysa ve blok başına ~85–92 codepoint ise NFC 1 / NFD 3). Test bu gövdeyi kullanır. **Ayrıca:** yalnız etiket aksanlı durumda segment sayısı aynı kalsa da `speaker` `'María'` → `None`'a düşer; test bunu da sabitler (yoksa yalnız-sayı assert'i ayrımı kaçırır).

---

## Tur 6 — implementer'a giden liste

| # | Ne | Kaynak | Tür |
|---|---|---|---|
| K28 | `_group(..., *, blocks=())` + `_raw_query_pair(tail, nxt, blocks)`; geometri sorgu anında `source_blocks`'tan okuma sırasıyla türetilir; `_Item` değişmez; 8 ölçü | A · R5-1, KRT 1. geçiş B1–B3/B6, 2. geçiş Y1–Y3 | **kod** + test + docstring |
| K28-kök | Adım 3'ün geometrik kontrol yapmadığı bilinçli sınır | A gözlem 3, KRT B11 | docstring + `known_gaps` |
| K29 | `:92` ve `:203` bayat adlar düzeltilir; `purity_check.py` exit 0 (kapı sürüm 3: satır-sonu **ve** satır-başı `_` sarması birleştirilir, attribute docstring'ler de taranır, kendini sınar) | B, KRT B5 + D1 | docstring |
| K30 | K2×K19/K21 **koşullu** cümle + ikinci yol testi | B, KRT B8 | docstring + `known_gaps` + test |
| — | ~~`normalize` içinde `apply_inheritance=True` açıkça~~ **GERİ ÇEKİLDİ** (KRT 3. geçiş Z1: `tester_B`'nin testi anahtar kelimenin yokluğunu pinliyor) | B | — |
| K31 | (a)/(b) iki alt durum | C, KRT B9 | docstring + `known_gaps` + 2 test |
| K32 | NFC varsayımı modül düzeyinde; bölümleme etkisi | C, KRT B10 | docstring ×2 + `known_gaps` + test |
| — | Zincirleme miras `tests/` altında pinlenir | A gözlem 2 | test |

**Kabul komutları:** tur 5 ile aynı **artı** `python .agents/tasks/T-004/purity_check.py` (exit 0 şart) **artı** `python .agents/tasks/T-004/olcu_kiti.py` (kitin kendi sağlığı; exit 0 şart).

**Tabanın kararsızlığı — tur 6 kapısına (O3).** Kör tester takımı **deterministik değil**: şef üç kez koştu, `1 failed / 1 failed / 0 failed` aldı. Kırılan `tester_C::test_olcek_tur4_ile_karsilastirma_iki_gecisli_group_kotulesmemis` (ve kardeşi `test_olcek_tur2_*`) — ölçek testleri tam takım yükü altında rastgele kırılıyor; `tester_C` **tek başına** koşulduğunda 125/125 kararlı (şef dört kez ölçtü). Tur 6 kapısı bu iki testi **ayrı koşar**; tam takımdaki tek kırıkları hayalet regresyon sayılmaz.

**Tester merceği — üç mercek korunur:** **A** (garanti alanı: ölçü 1–8, xfail dönüşümü, yeni makine denetimi), **B** (karar uyumu: K28 yapısal, K23 hâlâ iki-geçiş, M4/M5 mutantları, `_should_group` deseni), **C** (sınır-dil: K32 NFD/NFC bölümleme etkisi, K31/b, sağ taraf A2 varyantının K16 sınıfı yozlaşmış geometri regresyonu, `_group([], params)` doğrudan çağrısı). Sürüm 1 C'yi düşürmüştü; KRT haklı olarak itiraz etti (K32 dil yüzeyidir, B2/A2 yozlaşmış geometridir).

## Kapı

Dört geçiş: 13 (4 yüksek), 12 (3), 11 (3), 11 (2) = **47 bulgu, 12'si yüksek**.

**Yeniden üretim kaydı — düzeltme.** Sürüm 4 "36 bulgunun tamamı şef tarafından yeniden üretildi" diyordu; KRT haklı olarak itiraz etti (§4.6/3): `sef_dogrulama/` altındaki ham çıktı bunu karşılamıyordu. Doğrusu: **12 yüksek bulgunun 12'si de** şef tarafından kendi eliyle yeniden üretildi ve ham çıktıları `sef_dogrulama/krt6b_sef_kosumlari.txt` ile bu belgedeki kod bloklarında duruyor. Orta ve düşük bulguların çoğu **KRT'nin kanıtına dayanılarak** kabul edildi; bunlar karar metninde "KRT ölçtü" diye işaretlidir ve "şef ölçtü" ibaresi **yalnızca** şefin kendi koştuğu kalemlerde kullanılır. Sürüm 4'ün iki "ölçüldü" iddiası (dayanıklılık penceresi, "96 kırık hepsi `IndexError`") bu ayrım yapılmadığı için yanlış geçmişti; sürüm 5'te ikisi de düzeltildi.

Beş geçiş: 13 (4 yüksek), 12 (3), 11 (3), 11 (2), 8 (2) = **55 bulgu, 14'ü yüksek**; 14 yüksek bulgunun 14'ü de şef tarafından yeniden üretildi.

Altı geçiş. Altıncısı kiti kırdı ve kit sürüm 2'ye çıktı; **yedinci geçiş kit sürüm 2'yi çürütmeye bakacak.** Bulduğu her mutant kite eklenir (düzyazıya değil) ya da — kitin ölçemeyeceği bir sınıfsa — Tester-B'nin mutant yükümlülüğüne çevrilir ve kararda **açıkça ölçülmüyor** diye işaretlenir. Yüksek bulgu kalmazsa tur 6 implementer'ı başlar.

**Kaç turdur aynı yerde dönüldüğünün açık kaydı:** değişmez (K28'in kendisi) sürüm 3'ten beri **değişmedi**. Değişen hep ölçü oldu: düzyazı fixture → tek ön ayar → mekanizmaya kancalanmış ölçü → iki-eleman tavanı → kimlik kanalı yokluğu. Ölçüyü koda taşımak sınıfı daralttı ama bitirmedi; kod da yanlış şeyi ölçebiliyor. Bu turun dersi PROTOKOL'e yazılacak: **bir ölçü, denetlediği uygulamanın ürettiği veriden referans türetemez.**

**Şefin üç turluk hata kaydı — kayda geçer:**
| sürüm | hata | ihlal edilen kural |
|---|---|---|
| 1 | mekanizma yazdı, değişmez sandı (`source_blocks[-1]`); sağ tarafı hiç düşünmedi | §4.6/1 |
| 2 | ölçüyü ayırt edici kurmadı (fixture üç uygulamada da aynı çıktıyı veriyordu); iki seçenekten pahalı olanı **yanlış varyantını** ölçerek seçti | §4.6/4, §4.6/2 |
| 3 | "ölçtüm" dediği sayı başka bir şeyi ölçüyordu (ikili/üçlü anahtar yerine okuma/indeks sırası); ölçülerin tamamını tek ön ayarda bıraktı; bir kapı aletini kıran bir madde ekledi | §4.6/3, §4.6/2, §4.6/5 |
| 4 | ölçüyü **mekanizmaya** kancaladı (`_raw_query_pair`), böylece mekanizma atlandığında ölçü sessizce boşaldı; iki "ölçüldü" iddiasını kendi koşmadan yazdı ve ikisi de yanlış çıktı | §4.6/1, §4.6/3 |
| 6 | kiti yazdı ama referansı **denetlenen uygulamanın kendi verdiği veriden** türetti; kitin derlemi altı girdi sınıfını hiç üretmiyordu; iki olgusal hata (ölçü 7'nin kapsamı, M26→ölçü 3b) | §4.6/4, §4.6/7 |
| 5 | fixture'ların hiçbiri 2 bloktan büyük kuyruk üretmiyordu (off-by-one görünmezdi); ölçünün kimlik kanalını (`source_blocks`) önkoşul olarak yazmamıştı | §4.6/4, §4.6/2 |

**Beş turun asıl dersi — sürüm 6'nın yapısal cevabı:** hata sınıfı hep aynıydı ve hep düzyazıdaydı. Bir ölçü düzyazıyla tarif edildiği sürece her turda yeniden yorumlanır; kod olarak yazıldığında yorumlanamaz. Ölçüler artık `olcu_kiti.py`'de ve mutantlara karşı doğrulanmış durumda. Bu, PROTOKOL §4.6/2'nin ("her değişmezin yanında onu ölçen kabul komutu ve test adı yazılır") pratikteki üst sınırıdır: **ölçü, koşulabilir bir artefakt olarak teslim edilir.**

Üçü de kırmızı takım tarafından **kod koşularak** yakalandı, üçü de şef tarafından yeniden üretildi. Kapının değeri buradadır: bu turda implementer'a giden hiçbir hata implementer'ın hatası değildi — üçü de şefin kararındaydı ve implementer'a hiç ulaşmadı.
