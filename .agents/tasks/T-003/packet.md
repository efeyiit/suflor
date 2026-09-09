---
task: T-003
title: "DPI ve monitör koordinat dönüşümleri (saf matematik)"
role: implementer
level: B
wave: 1
owns:
  - "src/capture/dpi.py"
  - "tests/unit/capture/test_dpi.py"
forbidden:
  - "src/contracts/**"
  - "src/capture/__init__.py"
  - "src/capture/change_detector.py"
  - "tests/unit/contracts/**"
  - "diğer tüm dizinler"
depends_on: ["T-001"]
acceptance:
  - "python -m mypy --strict src/capture/dpi.py"
  - "python -m pytest tests/unit/capture/test_dpi.py -q"
budget_ms: null
---

# Görev

Çoklu monitör ve karışık DPI ortamında koordinatları doğru çevirmek. Bu bileşen bozuksa izlenen bölge yanlış yerden yakalanır ve çeviri şeridi yanlış yere çizilir — kullanıcının gördüğü en sinir bozucu hata sınıfı.

Tasarım dokümanı §5.1 (`CaptureService`, DPI farkındalığı), §5.6 (monitör/DPI değişimi hata satırı) ve §8.3 A2 (kabul kriterleri: %100/%150/%200 dönüşüm testleri) ilgili: `docs/superpowers/specs/2026-09-09-suflor-design.md`.

## Yazılacak

`src/capture/dpi.py` — **tamamen saf fonksiyonlar**. Sınıf, durum, I/O yok.

`Rect` **dondurulmuş sözleşmedir**, `src/contracts/models.py` içinde:

```
Rect(x: int, y: int, w: int, h: int, monitor_index: int = 0, dpi_scale: float = 1.0)
     + right, bottom (property)
```

Buna **dokunma**, yalnızca kullan. Dönüşümler yeni `Rect` döndürür (frozen olduğu için mutasyon zaten imkânsız).

## Gereken dönüşümler

En az şunlar; isimlendirmeyi sen netleştir ama davranış bu olsun:

1. **Mantıksal ↔ fiziksel piksel.** `dpi_scale` ile ölçekleme (%100 = 1.0, %150 = 1.5, %200 = 2.0). Yuvarlama davranışını **bilinçli seç ve belgele** — bir dikdörtgeni ölçekleyip geri çevirdiğinde ±1 piksel kayması olmamalı (round-trip kararlılığı).

2. **Monitöre göreli ↔ sanal masaüstü.** Windows'ta sanal masaüstü koordinatları **negatif olabilir** (birincil monitörün solundaki/üstündeki monitörler). Bu, bu alanın en klasik tuzağı; testinde negatif koordinatlı monitör senaryosu **mutlaka** olsun.

3. **Bölge geçerliliği.** Verilen bir `Rect`, verilen monitör kümesinin içinde mi? Kısmen taşıyorsa? Hiç kesişmiyorsa? Tasarım §5.6 "bölge geçersiz" durumunu bu fonksiyona dayandırıyor.

4. **Monitöre kırpma (clamp).** Taşan bir dikdörtgeni monitör sınırına sığdır; boyut sıfıra düşerse bunu açıkça bildir.

Monitörü temsil etmek için `Rect` yeterli (sanal masaüstü koordinatlarında sınırlar + `dpi_scale`). Ek bir tip gerekiyorsa `dpi.py` içinde tanımla — `src/contracts/` dondurulmuştur, oraya ekleme yapma.

## Kritik kısıtlar

- **Saf fonksiyonlar.** Windows API çağırma, gerçek monitör listeleme yapma, `ctypes`/`win32` kullanma. Monitör bilgisi **parametre olarak gelir**. Bu sayede headless ve deterministik test edilir.
- **`src/capture/__init__.py` dosyasına dokunma** — şefe ait, T-002 ajanı aynı anda çalışıyor.
- **`src/contracts/` dondurulmuştur.** Eksik görürsen `contract_change_request: true` ile talep aç.
- Yalnızca stdlib + numpy.

## Test etmen gerekenler

- %100 / %125 / %150 / %175 / %200 ölçeklerinde dönüşüm
- **Round-trip:** mantıksal → fiziksel → mantıksal, orijinaline eşit olmalı (veya sapma sınırı belgelenmiş olmalı)
- **Negatif koordinatlı monitör** (birincilin solunda/üstünde)
- Karışık DPI: iki monitör farklı `dpi_scale` ile
- Sınır durumları: sıfır genişlik, monitör dışında tamamen kalan dikdörtgen, tam sınırda oturan dikdörtgen

## Yöntem ve teslim

TDD: önce başarısız test, sonra implementasyon. Kabul komutlarının ikisini de gerçekten çalıştır, **ham çıktıyı** `.agents/tasks/T-003/evidence/` altına yaz.

`.agents/tasks/T-003/delivery.md` dosyasını `.agents/PROTOKOL.md` §4 şemasına birebir uygun yaz, `task: T-003` ile.

`.agents/PROTOKOL.md` §6'daki dokuz değişmez kural geçerlidir.
