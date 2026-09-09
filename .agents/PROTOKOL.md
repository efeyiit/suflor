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
| **Implementer** | B | Yalnızca görevin `owns` dizini | Kodu ve testini yazar |
| **Tester** | B | Yalnızca `.agents/tasks/<id>/` | Bağımsız doğrular, karar verir |
| **Ortam Ajanı** | B | `tests/harness/**`, `tests/fixtures/**` | Tester'ların koşum ortamını kurar |
| **Hakem** | A | Yalnızca `.agents/tasks/<id>/ruling.md` | 3 turda çözülmeyen anlaşmazlığı karara bağlar |

**Seviye A** = en güçlü akıl yürütme modeli · **Seviye B** = dengeli üretim modeli · **Seviye C** = hafif/mekanik iş.

### Rol açma kuralı

Yeni rol **yalnızca orkestra şefi** açabilir. Her yeni rol şunlarla gelmek zorundadır: tüzük (ne yapar, ne yapamaz), sahiplik dizini, koşulabilir kabul kriteri, seviye ataması. Şef rol sayısında sınırlı değildir.

**Ajan ajan açamaz.** Özyineleme kapalıdır; aksi hâlde ajan üretimi kontrolden çıkar.

---

## 2. Görev döngüsü

```
Şef ──packet.md──> Implementer
                        │ delivery.md + evidence/
                        v
                     Tester  (packet.md ve kodu okur; delivery.md'yi OKUMAZ)
                        │
          ┌─────────────┴─────────────┐
        RET                          ONAY
          │                            │
    feedback.md                   verdict.md
          │                            │
          v                            v
    Implementer (tur+1)            Şef ──decision.md──> sıradaki görev
          │
    3. turda hâlâ ret
          │
          v
       Hakem ──ruling.md──> bağlayıcı karar
```

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
