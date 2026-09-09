---
task: T-001
title: "Çekirdek sözleşmeler: veri modelleri, arayüzler, hata taksonomisi"
role: implementer
level: A
wave: 0
owns:
  - "src/contracts/**"
  - "tests/unit/contracts/**"
forbidden:
  - "src/capture/**"
  - "src/ocr/**"
  - "src/translate/**"
  - "src/store/**"
  - "src/pipeline/**"
  - "src/ui/**"
  - ".agents/**"
depends_on: []
acceptance:
  - "python -m mypy --strict src/contracts"
  - "python -m pytest tests/unit/contracts -q"
  - "python .agents/tasks/T-001/purity_check.py"
budget_ms: null
---

# Görev

Tüm sistemin ortak dilini yaz. Bu dosyalar **dondurulacak**: diğer her ajan bunlara bağımlı olacak ve hiçbiri değiştiremeyecek. Bu yüzden ileriye dönük düşün — bugün eksik bıraktığın bir alan, yarın kırıcı değişiklik demek.

Tasarım dokümanı §5.3 bu modelleri tanımlıyor: `docs/superpowers/specs/2026-09-09-suflor-design.md`. Onu **oku ve birebir uygula**; kendi kafandan model uydurma.

## Yazılacak dosyalar

**`src/contracts/models.py`** — `Rect`, `Frame`, `TextBlock`, `Segment`, `TermHit`, `Pair`, `TranslationRequest`, `TranslationResult`. Hepsi `@dataclass(frozen=True)`.

**`src/contracts/interfaces.py`** — `OcrEngine` ve `TranslationProvider` soyut arayüzleri (`abc.ABC`). Ayrıca her biri için `FakeOcrEngine` ve `FakeProvider` referans implementasyonu — **diğer ajanlar bunlarla test yazacak**, bu yüzden çalışır ve deterministik olmalılar.

**`src/contracts/errors.py`** — §5.3'teki hata taksonomisi: `TranslatorError` kökünden türeyen `CaptureError`, `ModelMissingError`, `OcrError`, `ProviderUnavailable`, `ProviderTimeout`, `ContractViolation`.

**`tests/unit/contracts/`** — her model için: değişmezlik (frozen) testi, alan tipleri testi, `FakeProvider`'ın segment sayısı ile çeviri sayısını hizalı döndürdüğü testi.

## Kritik kısıtlar

1. **`src/contracts/` hiçbir somut kütüphaneyi import etmez.** ONNX, Qt, SQLite, llama.cpp, CTranslate2 — hiçbiri. Yalnızca stdlib ve `numpy` (yalnızca tip anotasyonu için). Bu kural `purity_check.py` ile makineyle denetleniyor.
2. **Her model `frozen=True`.** Değişmezlik pipeline'ın yarış koşullarına karşı ilk savunması.
3. **`TranslationResult.translations` ile `TranslationRequest.segments` birebir hizalı olmak zorunda.** Bu sözleşme `ContractViolation` ile korunuyor; `FakeProvider` bunu doğru yapmalı.
4. **`image_crops` alanını bugün ekle** — şu an yalnızca vision motorları kullanacak ama sözleşmede olmazsa yarın kırıcı değişiklik olur.

## Yöntem

- **TDD**: önce başarısız test, sonra implementasyon.
- Kabul komutlarının **üçünü de** çalıştır, çıktılarını `.agents/tasks/T-001/evidence/` altına yaz.
- Bitince `.agents/tasks/T-001/delivery.md` dosyasını `.agents/PROTOKOL.md` §4'teki şemaya **birebir** uygun yaz.

## Değişmez kurallar

`.agents/PROTOKOL.md` §6'daki dokuz kural bu görev için de geçerli. Özellikle:

- `owns` dışına tek satır yazma — sahiplik ihlali otomatik ret
- Kanıt yoksa iş teslim edilmemiştir; "testler geçiyor" cümlesi kabul edilmez
- Çalışmayan bir şey varsa `status: kismi` yaz, gizleme
