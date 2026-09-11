**Türkçe** · [English](README.en.md)

# Suflör

**Ekrandaki yazıyı yakalayıp tanıyan ve çeviren Windows masaüstü uygulaması.**
Oyun için tasarlandı, her uygulamada çalışır. Ücretsiz ve offline.

---

> [!NOTE]
> **Durum: tasarım aşaması.** Henüz kod yok. Bu depo şu an yalnızca tasarım
> dokümanını barındırıyor. Uygulama planı çıkarıldıktan sonra geliştirme başlayacak.

## İki mod

**1 · Snapshot Modu** — Kısayola bas, ekran donar. Tespit edilen metin blokları
çerçevelenir, istediklerini seçersin, seçilenler görsel bağlamıyla birlikte çevrilir.

**2 · Bölge İzleme Modu** — Ekranda bir dikdörtgen çiz. O alanda çıkan her yazı
otomatik ve sürekli çevrilir; çeviri bölgeye yapışık yarı-şeffaf bir şeritte akar.
Şeridi koparıp ikinci monitöre atabilirsin.

## Üç temel duruş

**Ücretsiz ve offline varsayılan.** İlk açılışta API anahtarı sorulmaz. Yerel OCR ve
yerel çeviri motorları indirilir, uygulama çalışır durumda gelir. Bulut sağlayıcı,
isteyenin ayarlardan açtığı opsiyonel bir yükseltmedir — zorunlu değil, varsayılan değil.

**Anti-cheat açısından güvenli.** Hiçbir process injection, DLL enjeksiyonu, API hook
veya memory okuma yok. Sadece Windows'un kendi ekran yakalama yolları ve normal bir
üst-katman pencere — yani OBS'in yaptığından daha azı. Oyun hesabının banlanma riski
sıfır olmalı; bu bir kısıt değil, bilinçli mimari duruş.

**Hiçbir hata akışı durdurmaz.** Kalıcı hatalar durum çubuğunda tek satır olarak
görünür. Oyun oynayan birinin ekranına modal dialog atmak affedilemez.

## Çeviri zekâsı: dört katman

| Katman | Ne | Durum |
|---|---|---|
| **0** | Oyuna özel terim sözlüğü + çeviri hafızası (TM) | v1 |
| **1** | Yerel NMT (CTranslate2, int8) — hızlı, Mod 2 varsayılanı | v1 |
| **2** | Yerel küçük LLM (4B, vision) — bağlamlı, Mod 1 varsayılanı | v1 |
| **3** | Oyun diyaloguna ince ayarlanmış kendi modeli (QLoRA) | yol haritası |
| — | Bulut sağlayıcılar (Gemini / DeepL / diğer) | v1, opsiyonel |

Katman 0 en yüksek getiriyi veren katman: vasat bir motoru bile o oyuna özel
hissettiren şey oyun başına sözlük ve çeviri hafızasıdır, ve maliyeti sadece koddur.

## Oyun tarafı

- **Oyun profilleri** — oyun başına bölge, dil, motor, sözlük, üslup ve OCR ön ayarı.
  Aktif pencerenin exe adına göre otomatik önerilir, `.json` olarak paylaşılabilir.
- **Metin türü ön ayarları** — diyalog kutusu, menü, tooltip, altyazı; her biri farklı
  blok gruplama ve debounce davranışı gerektirir.
- **Exclusive fullscreen** — overlay bu modda görünmez (Windows kısıtı). Uygulama bunu
  tespit eder ve açıkça söyler: borderless'a geç ya da şeridi ikinci monitöre al.

## Teknoloji

Python 3.12 · PySide6 (Qt 6) · RapidOCR (ONNX Runtime) · CTranslate2 · llama.cpp ·
SQLite · PyInstaller

Hedef: Mod 2'de uçtan uca ≤ 160 ms (cache isabeti) / ≤ 320 ms (cache ıskası),
oyun FPS düşüşü ≤ %3.

## Kurulum ve çalıştırma

```bash
pip install -r requirements-dev.txt
python -m pytest tests -q            # tam takım (model gerekmez)
python demo/kabuk.py                 # UI kabuğu: üç düğme, tepsi, kenar sekmesi
python demo/canli_cevir.py korean    # ekrandan yakala → OCR → sözlük → Türkçe (model gerekir)
```

Çeviri modeli (`models/nllb-200-distilled-600M-ct2-int8/`, ~650 MB) depoya dahil değildir; JP/KR OCR
modelleri ilk çalıştırmada indirilir. `demo/` altındaki gösterimler kabul edilen bileşenleri
uçtan uca gösterir; `.agents/tasks/` altında her bileşenin ölçümleri, paketleri ve kararları vardır.

## Dokümantasyon

| | |
|---|---|
| **Tasarım dokümanı (Markdown)** | [`docs/superpowers/specs/2026-09-09-suflor-design.md`](docs/superpowers/specs/2026-09-09-suflor-design.md) |
| **Tasarım dokümanı (PDF, 28 sayfa)** | [`docs/superpowers/specs/2026-09-09-suflor-design.pdf`](docs/superpowers/specs/2026-09-09-suflor-design.pdf) |
| **Ajan iletişim ağı — karşılaştırma (Markdown)** | [`docs/superpowers/specs/2026-09-09-ajan-iletisim-agi-karsilastirma.md`](docs/superpowers/specs/2026-09-09-ajan-iletisim-agi-karsilastirma.md) |
| **Ajan iletişim ağı — karşılaştırma (PDF, 8 sayfa)** | [`docs/superpowers/specs/2026-09-09-ajan-iletisim-agi-karsilastirma.pdf`](docs/superpowers/specs/2026-09-09-ajan-iletisim-agi-karsilastirma.pdf) |

Doküman 12 bölüm: ürün ve iki mod, oyun-özel detaylar, dört katmanlı çeviri zekâsı,
runtime mimari (bileşenler, sözleşmeler, eşzamanlılık, hata yönetimi, performans
bütçesi), geliştirme ajanları ve orkestrasyon, test stratejisi, riskler, yol haritası,
açık sorular ve karar kaydı.

> Tasarım dokümanı şu an yalnızca Türkçe. İngilizce çevirisi planlanıyor.

## Lisans

Henüz lisans seçilmedi — yasal varsayılan olarak tüm hakları saklıdır.
Katkı veya yeniden dağıtım için açık bir lisans eklenecek (bkz. tasarım dokümanı §12.6).
