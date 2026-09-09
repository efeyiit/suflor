---
task: T-002
title: "ChangeDetector: algısal hash + kararlılık (debounce)"
role: implementer
level: B
wave: 1
owns:
  - "src/capture/change_detector.py"
  - "tests/unit/capture/test_change_detector.py"
forbidden:
  - "src/contracts/**"
  - "src/capture/__init__.py"
  - "src/capture/dpi.py"
  - "tests/unit/contracts/**"
  - "diğer tüm dizinler"
depends_on: ["T-001"]
acceptance:
  - "python -m mypy --strict src/capture/change_detector.py"
  - "python -m pytest tests/unit/capture/test_change_detector.py -q"
budget_ms: 5
---

# Görev

Mod 2'nin canlı döngüsünde CPU ve maliyeti kurtaran bileşen. Her tick'te yakalanan bölgenin **değişip değişmediğine** karar verir; değişmemişse pipeline hiç çalışmaz.

Tasarım dokümanı §2.2 (adım 4-5), §5.1 ve §5.7 bu bileşeni tanımlıyor: `docs/superpowers/specs/2026-09-09-suflor-design.md`. **Oku ve uygula.**

## Yazılacak

`src/capture/change_detector.py` içinde `ChangeDetector` sınıfı.

**Ana sözleşme:** `has_changed(frame: Frame) -> bool`

`Frame` ve `Rect` **dondurulmuş sözleşmelerdir**, `src/contracts/models.py` içinde. Şu imzalara sahipler:

```
Rect(x: int, y: int, w: int, h: int, monitor_index: int = 0, dpi_scale: float = 1.0)
     + right, bottom (property)
Frame(image: ImageArray, rect: Rect, captured_at: float, seq: int)
```

`ImageArray` = numpy ndarray (BGR, uint8). Bunlara **dokunma**, yalnızca kullan.

## Davranış

**1 · Algısal hash.** Görüntüden dHash veya aHash hesapla (küçült → gri tonla → komşu piksel karşılaştır → bit dizisi). Kriter: piksel-piksel karşılaştırma **kullanma** — sıkıştırma gürültüsü ve tek piksellik oynamalar yanlış pozitif üretir.

**2 · Eşik.** İki hash arasındaki Hamming mesafesi bir eşiğin altındaysa "değişmedi" say. Eşik yapılandırılabilir olsun, makul bir varsayılanı olsun.

**3 · Kararlılık / debounce.** Tasarım §2.2 adım 5: metin harf harf yazılıyorsa yarısını okuyup çöp çeviri üretmemek için **2 ardışık aynı hash** beklenir. Yani bir değişiklik ancak *kararlı hâle geldikten sonra* bildirilir. Bu, bileşenin en kritik davranışı ve en kolay yanlış yapılan kısmı — dikkatli düşün ve testle.

**4 · Durum sıfırlama.** Bölge değiştiğinde (yeni `Rect`) geçmiş hash geçersizdir; ilk frame her zaman "değişti" sayılır.

## Performans bütçesi: ≤ 5 ms

Tasarım §5.7'de yazılı. **Ölç ve kanıtla.** Testinde gerçekçi bir bölge boyutuyla (örn. 600×200) zamanla ve bütçeyi aşarsa test kırılsın. Bütçe aşımı bir bug'dır, gözlem değil.

## Kritik kısıtlar

- **Saf ol.** Ekran yakalama yapma, Windows API çağırma, dosya okuma. Yalnızca verilen `Frame` nesnesi üzerinde çalış. Bu sayede headless test edilebilir.
- **`src/capture/__init__.py` dosyasına dokunma** — o şefe ait, T-003 ajanı da aynı anda çalışıyor.
- **`src/contracts/` dondurulmuştur.** Eksik bir şey görürsen değiştirme; `contract_change_request: true` ile talep aç.
- Yalnızca stdlib + numpy kullan. Yeni bağımlılık için şef onayı gerekir.

## Yöntem ve teslim

TDD: önce başarısız test, sonra implementasyon. Kabul komutlarının ikisini de gerçekten çalıştır, **ham çıktıyı** `.agents/tasks/T-002/evidence/` altına yaz. Bütçe ölçümünü de kanıt olarak bırak.

`.agents/tasks/T-002/delivery.md` dosyasını `.agents/PROTOKOL.md` §4 şemasına birebir uygun yaz, `task: T-002` ile.

`.agents/PROTOKOL.md` §6'daki dokuz değişmez kural geçerlidir.
