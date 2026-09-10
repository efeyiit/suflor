# Ajan Protokolü

Suflör'ü inşa edecek yapay zekâ ajanlarının işleyiş kuralları. Bu dosya **tek yetkili kaynaktır**; çelişki durumunda burası geçerlidir.

| | |
|---|---|
| **Taşıma** | Alt-ajan (orkestra şefi ana oturumdur, işçileri kendi içinde başlatır) |
| **Protokol** | Dosya — her mesaj `.agents/tasks/<T-id>/` altında bir dosyadır |
| **Granülerlik** | Test-birimi: bağımsız koşulabilir kabul testi yazılabilen en küçük iş |
| **Kilitlenme eşiği** | 3 tur, sonra Hakem |
| **Paralellik tavanı** | Pilotta 4 eşzamanlı görev |

---

## 1. Roller

| Rol | Seviye | Yazma yetkisi | Görevi |
|---|---|---|---|
| **Orkestra Şefi** | A | `.agents/**`, `src/contracts/**` | Görev üretir, kapıları işletir, birleştirir, yeni rol açar |
| **Paket Kırmızı Takımı** | A | Yalnızca `.agents/tasks/<id>/redteam.md` | Şefin paketini denetler — belirsizlik ve alanı belirtilmemiş garanti avlar |
| **Implementer** | B | Yalnızca görevin `owns` dizini | Kodu ve testini yazar |
| **Tester** (×3, farklı mercek) | B | Yalnızca `.agents/tasks/<id>/` | Bağımsız doğrular, **ayrı ayrı** rapor verir |
| **Ortam Ajanı** | B | `tests/harness/**`, `tests/fixtures/**` | Tester'ların koşum ortamını kurar, mercekleri tanımlar |
| **Entegrasyon Ajanı** | B | `tests/integration/**` | Dalga sonunda modülleri birlikte sınar |
| **Hakem** | A | Yalnızca `.agents/tasks/<id>/ruling.md` | 3 turda çözülmeyen anlaşmazlığı karara bağlar |

**Seviye A** = en güçlü akıl yürütme modeli · **Seviye B** = dengeli üretim modeli · **Seviye C** = hafif/mekanik iş.

### Güncel model ataması (2026-09-10, kullanıcı kararı)

| Rol | Model | Gerekçe |
|---|---|---|
| Orkestra Şefi | **Fable 5.1** | Yalnızca bu oturum. 5 bloke edici hatanın 3'ü + 3 yanlış sonda buradan çıktı |
| Kırmızı takım (paket + karar) | **Seviye A** | En yüksek kaldıraç; testerların onayladığı bir hatayı yakaladı |
| Tester ×3 | **Seviye A** | Seviye B'de iyiydi ama tur 4'te bölümleme hatasını onayladı |
| Hakem | **Seviye A** | Kilitlenme kararı, nadir ama kritik |
| Implementer | **Seviye A** — *T-005'te ölçülüyor* | Bahis: tur sayısını düşürürse kendini öder (bir tur ≈ 600–800k) |
| Ortam Ajanı / Entegrasyon | **Seviye B** | Mekanik iş: env.md, harness, birlikte koşum raporu |

**T-005 ölçümü:** Seviye A implementer'ın tur sayısı T-004'ün 5 turuyla karşılaştırılacak. Düşerse kalıcı; düşmezse implementer Seviye B'ye döner.

Limit dolumuna göre yeniden ayarlanır; seviye tablosu geçerliliğini korur, yalnızca eşleme değişir.

### Rol açma kuralı

Yeni rol **yalnızca orkestra şefi** açabilir. Her yeni rol şunlarla gelmek zorundadır: tüzük (ne yapar, ne yapamaz), sahiplik dizini, koşulabilir kabul kriteri, seviye ataması. Şef rol sayısında sınırlı değildir.

**Ajan ajan açamaz.** Özyineleme kapalıdır; aksi hâlde ajan üretimi kontrolden çıkar.

---

## 2. Görev döngüsü

```
Şef ──packet.md──> Paket Kırmızı Takımı ──redteam.md──> Şef paketi düzeltir
                                                              │
                                                              v
                                                        Implementer
                                                              │ delivery.md + evidence/
                                                              v
                       ┌──────────────────────────────────────┼──────────────────┐
                       v                                      v                  v
                  Tester-1                               Tester-2           Tester-3
                 (mercek A)                             (mercek B)         (mercek C)
                       │ verdict-1.md                         │                  │
                       └──────────────────────────────────────┼──────────────────┘
                                                              │
                              Üçü de AYRI rapor verir. Birleştirilmiş özet YOK.
                                                              │
                                                              v
                                          Şef her raporu ayrı okur ve her iddiayı
                                          KENDİ ELİYLE yeniden üretir  ← şef sondası
                                                              │
                                            ┌─────────────────┴─────────────────┐
                                     herhangi biri RET                    üçü de ONAY
                                            │                                   │
                                      feedback.md                          decision.md
                                            │                                   │
                                            v                                   v
                                   Implementer (tur+1)                  sıradaki görev
                                            │
                                    3. turda hâlâ ret
                                            │
                                            v
                                  Hakem ──ruling.md──> bağlayıcı karar
```

Dalga sonunda: **Entegrasyon Ajanı** modülleri birlikte sınar. Geçmeden dalga kapanmaz.

### Dosya düzeni

```
.agents/
  PROTOKOL.md            bu dosya
  state/board.json       tüm görevlerin durumu
  tasks/T-001/
    packet.md            şef       -> implementer   (ne yapılacak)
    env.md               ortam aj. -> tester        (nasıl koşulur)
    delivery.md          impl.     -> şef           (TESTER OKUMAZ)
    evidence/            ham komut çıktıları
    verdict.md           tester    -> şef
    feedback.md          tester    -> implementer   (yalnızca ret hâlinde)
    ruling.md            hakem     -> bağlayıcı     (yalnızca kilitlenmede)
    decision.md          şef       -> nihai karar
    round.json           tur sayacı
```

---

## 3. Halüsinasyonu sıfırlayan dört kapı

Bunlar tartışmaya kapalıdır. Bir ajan bunlardan birini ihlal ederse teslim **otomatik reddedilir**, içeriğine bakılmaz.

**1 · Ajanın sözü delil değildir.** "Testler geçiyor" cümlesi hiçbir şey ifade etmez. Yalnızca çalıştırılmış komut ve **ham çıktı** kabul edilir. Çıktı `evidence/` altında dosya olarak durmalıdır. Kanıt yoksa iş teslim edilmemiştir.

**2 · Tester kör çalışır.** Tester `delivery.md` dosyasını **okumaz**. Yalnızca `packet.md` (ne yapılmalıydı), `env.md` (nasıl koşulur) ve kodun kendisini görür. Testlerini kendi yazar, kendi koşar. Implementer'ın raporunu okursa ona demirler ve aynı yanılgıyı onaylar.

**3 · Sözleşmeler makineyle denetlenir.** `mypy --strict`, şema doğrulama, arayüz uyum testleri. Ajan yorumuna bırakılan sınır yoktur.

**4 · Tester de delil zorunda.** Tester "bu bozuk" diyemez; **yeniden üretilebilir komut + ham hata çıktısı** vermek zorundadır. Aksi hâlde tester'ın halüsinasyonu implementer'ı kilitler.

**5 · Sentez katmanı yasak.** Şefe hiçbir zaman *birleştirilmiş* bir sonuç gelmez. Üç tester üç ayrı rapor yazar; şef üçünü ayrı okur. Raporları tekilleştiren, oylayan veya özetleyen bir ara katman, ajan raporlarına güvenmeme ilkesini bir kat yukarıda yeniden ihlal eder — şef o zaman kanıtı değil, kanıt hakkındaki bir iddiayı okumuş olur.

**6 · Şef sondası.** Tester'lar onay verse bile şef modüle kendi saldırısını yapar ve **her iddiayı kendi eliyle yeniden üretir**. Pilotta bu adım iki kez işe yaradı: T-003'te kusurun bildirilenden geniş olduğu (%68.6), T-002'de tester'ın söylemediği 4×4 çökmesi böyle bulundu. Üçüncü kez ise şefin **kendi** sondasının hatalı olduğu ortaya çıktı — dar bölgeleri bozuk sanmıştı, testi debounce'a takılıyordu. Kural şefe de uygulanır: iddia, doğru kurulmuş kanıtla geçerlidir.

---

## 4. Rapor şeması (zorunlu)

`delivery.md` ve `verdict.md` **YAML ön bilgisiyle** başlamak zorundadır. Şef, ön bilgiyi ayrıştıramazsa raporu **okumadan reddeder** — biçimsel olarak bozuk cevap kapıdan geçemez.

### `delivery.md` ön bilgisi

```yaml
---
task: T-001
role: implementer
round: 1
status: tamamlandi | kismi | bloke
files_written:
  - src/contracts/models.py
commands:
  - cmd: "python -m mypy --strict src/contracts"
    exit_code: 0
    evidence: evidence/mypy.txt
  - cmd: "python -m pytest tests/unit/contracts -q"
    exit_code: 0
    evidence: evidence/pytest.txt
contract_change_request: false
known_gaps: []
---
```

### `verdict.md` ön bilgisi

```yaml
---
task: T-001
role: tester
round: 1
decision: onay | ret
checks:
  - name: "mypy --strict temiz"
    cmd: "python -m mypy --strict src/contracts"
    exit_code: 0
    result: gecti | kaldi
    evidence: evidence/tester-mypy.txt
blocking_issues: []
---
```

### Şef doğrulaması

Şef bir raporu kabul etmeden önce **makineyle** kontrol eder:

1. YAML ön bilgi ayrıştırılabiliyor mu
2. Zorunlu alanlar var mı
3. `commands` / `checks` altındaki her `evidence` dosyası **gerçekten diskte var mı**
4. Kanıt dosyası boş değil mi
5. `files_written` içindeki her yol görevin `owns` dizini içinde mi (sahiplik ihlali kontrolü)

Bunlardan biri başarısızsa rapor reddedilir; içeriği okunmaz.

---

## 4.5 Tester mercekleri

Görev başına **üç tester**, üçü de farklı mercekle. Mercek seçimi rastgele değil, görevin hata yüzeyine göre yapılır. Her tester diğerlerinin varlığından habersizdir ve kendi raporunu yazar.

Mercek havuzu — şef görev tipine göre üç tane seçer:

| Mercek | Neye bakar |
|---|---|
| **Sınır** | Yozlaşmış ve uç girdiler: sıfır, negatif, tek eleman, tam sınırda, çok büyük |
| **Garanti alanı** | Docstring/tip ne söz veriyor, kabul edilen **her** girdi için tutuyor mu |
| **Sayısal** | Yuvarlama, float kesinliği, tamsayı/dtype taşması, NaN/inf, sıfıra bölme |
| **Durum makinesi** | Çağrı sırası, sıfırlama, ulaşılamayan durum, kilitlenme |
| **Takma ad** | View/copy, paylaşılan mutable durum, dışarıdan mutasyon |
| **Test kalitesi** | Testler totoloji mi, assertion gerçekten kırılıyor mu, ne hiç test edilmemiş |
| **Şartname uyumu** | Tasarım dokümanıyla satır satır karşılaştırma; eksik ve uydurulmuş davranış |
| **Kötü kullanım** | Sonraki ajan bu API'yi hangi yanlışı yapmaya davet ediliyor |

Seçim örnekleri: saf matematik modülü → sınır + garanti alanı + sayısal · durum tutan bileşen → durum makinesi + takma ad + sınır · metin işleyen saf fonksiyon → garanti alanı + şartname uyumu + kötü kullanım.

Ortam Ajanı, `env.md` içinde her merceğe **somut saldırı noktaları** yazar. Pilotta iki hatayı da bulduran şey buydu: T-002'nin çökmesi `env.md`'deki *"çok küçük bölge (1×1, 3×3)"* satırı sayesinde bulundu. Tester'a nereye saldıracağını söylemek, rastgele aramadan belirgin şekilde verimli.

**Üç tester'dan biri ret verirse görev reddedilir.** Onay için üçünün de onayı gerekir.

### Kapı risk yüzeyine göre ölçeklenir

Üç mercek **varsayılandır**. Bir düzeltme turu yalnızca dar ve iyi tanımlı bir yüzeye dokunuyorsa şef mercek sayısını azaltabilir — ama **gerekçesini karar belgesine yazmak zorundadır**: hangi mercek neden koşmuyor, o merceğin kapsadığı hata sınıfı bu turda neden açılmıyor.

Azaltma yalnızca şefin yetkisindedir ve varsayılan her zaman üçtür. Gerekçesiz azaltma, kapıyı sessizce gevşetmektir.

## 4.6 Şef kararlarının biçimi — değişmez + ölçü + olgu kanıtı

T-004 ve T-005'te ölçülen şef hataları, sekiz kuralı zorunlu kıldı:

**1 · Karar bir değişmezdir, mekanizma değil.** "Şu koşulda şunu yap" yerine "şu her zaman doğru olmalı". Mekanizmanın etkileşimleri görünmez; değişmezin ihlali ölçülebilir. (T-004 K9/K19/K21: üçü de mekanizmaydı, üçü de etkileşimde battı.)

**2 · Her değişmezin yanında onu ölçen kabul komutu ve test adı yazılır.** Ölçülmeyen değişmez `[ÖLÇÜLMÜYOR]` damgası taşır ve nedenini söyler. Değişmez yazmak "ölçülüyor" hissi verir; T-005 v1'de üç değişmez kusursuz yazılmış ve hiç ölçülmüyordu, biri ölçüldüğünü açıkça iddia ediyordu.

**3 · "Ölçülen gerçek" iddiası, ham çıktısı `sef_dogrulama/` altında dosyada durmadan yazılamaz.** Şef, hafızadan bir olguyu "ölçtüm" diye yazamaz. (T-005 v1: tampon yeniden kullanımı iddiası ölçülmemişti ve yanlıştı.)

**4 · Bir karar bir ifade adı veriyorsa (`x[-1]`, bir alan, bir çağrı), o ifadenin hangi değişmezi gerçeklediği ayrıca yazılır ve ölçü, ifadenin değişmezden **ayrıştığı** bir girdi içerir.** Aksi hâlde ölçü, yanlış mekanizmayı doğru olandan ayıramaz. (T-004 K28 sürüm 1: `source_blocks[-1]` "okuma sırasındaki son blok" sanıldı; `source_blocks` indeks sıralı, okuma sırası `(y,x)` — sırasız girdide ayrışıyorlar ve mevcut doğru davranışta regresyon üretiyorlardı. Depodaki 480 testin **hiçbiri** ikisini ayıramıyordu, çünkü her fixture sıralı girdi veriyordu.)

**5 · Bir karar mevcut yeşil testleri kaçınılmaz olarak bayatlatıyorsa, hangi testlerin neden bayatlayacağı ve kimin yeniden yazacağı karara yazılır.** Sessizce bayatlayan bir kapı aleti, kapının kendisini kapatır. (T-004 K28: tester'ın AST beklentisi ve mutant sondası kaçınılmaz bayatlıyordu; sürüm 1 bunu anmıyordu.)

**6 · Kırmızı takımın her bulgusu, şef tarafından kendi eliyle yeniden üretilmeden karara işlenmez.** Rapor da bir iddiadır. Şefin kendi koştuğu kalem **"şef ölçtü"**, yalnızca rapora dayanılarak kabul edilen kalem **"KRT ölçtü"** diye işaretlenir; ikisi karıştırılırsa kural 3 sessizce ihlal edilir. (T-005 paketinde 65, T-004 kararında 47 bulgu — toplam 112, 24'ü yüksek. Şef **24 yüksek bulgunun 24'ünü** kendi eliyle yeniden üretti; orta/düşüklerin bir kısmı KRT kanıtına dayanılarak kabul edildi. Karar sürüm 4'te "hepsinin tamamı yeniden üretildi" yazıldı, ham çıktı bunu karşılamıyordu ve iki "ölçüldü" iddiası yanlış çıktı — bu ayrım o yüzden zorunlu.)

**7 · Bir ölçü, değişmezi kancalar; mekanizmayı değil.** Kanca bir yardımcı fonksiyona takılırsa, o yardımcıyı atlayan uygulama ölçüyü sessizce **boşaltır** — kayıt boş kalır ve denetim "ihlal yok" der. Ayrıca her davranışsal ölçü, kararın kapsadığı **parametre/ön ayar uzayının en az iki noktasında** koşar; tek noktada kalan ölçü, o noktaya kapılı bir uygulamayı göremez. (T-004 K28: ölçülerin tamamı `dialogue` fixture'larıydı; ham ikameyi yalnız `dialogue`'da yapan uygulama sekiz ölçüyü de geçti. `tooltip` eklendi; bu kez `subtitle`'a kapılı üç varyant yine sekizini de geçti — 4000 girdide 1698 ayrışma. Kök sebep ikinci kez aynıydı: ölçü mekanizmayı (`_raw_query_pair`) kancalıyordu, kapı kapalıyken o fonksiyon hiç çağrılmıyordu.)

**8 · Bir ölçü, denetlediği uygulamanın ürettiği veriden referans türetemez.** Referans **bağımsız** bir kanaldan gelmelidir; aksi hâlde ölçü yalnızca "verdiğin şey kendi içinde tutarlı mı" diye sorar, "doğru şeyi mi verdin" diye sormaz. (T-004 K28 ölçü kiti sürüm 1: referans, sorgunun taşıdığı `source_blocks`'tan türetiliyordu; 26 mutantın 13'ü üç ön ayarda da temiz geçti, yedisi 478 kör testte de görünmezdi. Sürüm 2 girdiden bağımsız bir kimlik kanalı ekledi. Aynı sınıf T-005'te de çıktı: `headless_check` §3 `grab` dönüşünü `np.asarray` ile ölçüyordu — yani K7'nin yasakladığı dönüşümü denetleyicinin içinde yaparak ham `ScreenShot` döndüren bir uygulamayı aklıyordu.)

Kırmızı takım bu sekizini ayrıca denetler.

## 5. Görev paketi zorunlu alanları

```yaml
---
task: T-001
title: "Çekirdek veri modelleri ve arayüzler"
role: implementer
level: A
wave: 0
owns:            # yalnızca bu yollara yazabilir
  - src/contracts/**
forbidden:       # okuyabilir, yazamaz
  - "diğer tüm dizinler"
depends_on: []
acceptance:      # her biri koşulabilir komut
  - "python -m mypy --strict src/contracts"
  - "python -m pytest tests/unit/contracts -q"
budget_ms: null  # varsa performans bütçesi
---
```

---

## 6. Tüm ajanlar için değişmez kurallar

Her görev paketine kopyalanır.

1. **TDD.** Önce başarısız test, sonra implementasyon.
2. **Sözleşmeye dokunma.** `src/contracts/` yalnızca A1'in ve şefin yazabildiği alandır. Eksik varsa `contract_change_request: true` ile talep aç, kendin değiştirme.
3. **Dizinini terk etme.** `owns` dışına tek satır yazmak sahiplik ihlalidir; teslim otomatik reddedilir.
4. **Kanıt yapıştır.** Komutu gerçekten çalıştır, çıktıyı `evidence/` altına yaz.
5. **Bütçeyi aşma.** Performans bütçesi varsa ölç ve raporla.
6. **Bağımlılık için onay al.** Yeni paket = şef onayı (lisans + boyut + paketleme uyumu).
7. **Loglama disiplini.** OCR metni, çeviri içeriği, API anahtarı asla loglanmaz.
8. **Modal dialog yok.** Hata durum çubuğuna yazılır.
9. **Dürüst raporla.** Çalışmıyorsa `status: kismi` veya `bloke` yaz. Kısmi teslim kabul edilebilir; yanlış rapor edilemez.

---

## 7. Kilitlenme

`round.json` her turda artar. 3. turda tester hâlâ ret veriyorsa şef **Hakem**'i çağırır.

> **Pilot düzeltmesi (2026-09-09).** Bu bölüm önce "düzeltme paketi *aynı ajana* gider, böylece bağlam korunur" diyordu. **Bu ortamda mümkün değil:** alt-ajanlara mesaj gönderip devam ettirme aracı mevcut değil. Gerçek işleyiş: her düzeltme turu **taze bir ajanla** başlar ve bağlamı `feedback.md` üzerinden alır.
>
> Sonucu: `feedback.md` protokolün en kritik dosyası. Yeniden üretim komutu, ham hata çıktısı ve neyin beklendiği eksiksiz yazılmalı — düzeltme ajanının elinde bundan başka bir şey yok.
>
> Maliyet etkisi: her ret turu bağlamı sıfırdan kurduğu için ucuz değil. Pilotta T-003'ün 2. turu 107k, T-002'nin 2. turu 116k token'a mal oldu.

Hakem: `packet.md` + kod + tüm `evidence/` + implementer ile tester'ın gerekçelerini okur. `ruling.md` yazar: kim haklı, neden, ne yapılacak. Kararı bağlayıcıdır ve tur sayacı sıfırlanır.

Hakem "görev tanımı hatalı" derse görev şefe geri döner ve `packet.md` yeniden yazılır.
