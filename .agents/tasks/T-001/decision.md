---
task: T-001
role: orkestra-sefi
round: 1
decision: kabul
contracts_frozen: true
---

# Şef Kararı — T-001

**Kabul.** Sözleşmeler donduruldu. Dalga 1 başlayabilir.

## Bağımsız doğrulama

Ne implementer'ın ne tester'ın raporuna güvenildi; kapılar şef tarafından yeniden işletildi.

| Kontrol | Sonuç |
|---|---|
| `delivery.md` şema + kanıt + sahiplik | Geçti |
| `verdict.md` şema + kanıt + sahiplik | Geçti |
| Tester testleri şef tarafından koşuldu | 140 geçti, çıkış 0 |
| Kabul komutları üçüncü kez koşuldu | mypy temiz · 114 test geçti · saflık temiz |
| Sahiplik ihlali taraması | Temiz — hiçbir ajan `owns` dışına yazmadı |

## Tester körlüğü — ölçüldü

Körlük kuralının işe yarayıp yaramadığı, tester'ın beyanına değil ölçüme dayandırıldı:

| Ölçüm | Değer |
|---|---|
| Implementer test fonksiyonu | 56 |
| Tester test fonksiyonu | 53 |
| **Aynı isimli fonksiyon** | **0** |
| 3 satırlık özdeş blok örtüşmesi | %5 |

%5'lik örtüşmenin tamamı şablon satır (`from __future__ import annotations`, `import pytest`) ve alan adı listeleri. Mantık kopyası yok. **Tester bağımsız çalıştı.**

## Bildirilen üç boşluğa karar

Implementer, tasarım dokümanının sessiz kaldığı üç yerde karar verdi ve gizlemek yerine bildirdi. Üçü de kabul edildi:

**1 · `TermHit` / `Pair` alan şemaları** — §5.1 imzalarından türetildi. Kabul, ancak bunlar bir tahmindir ve tüketicileri A4 (translate) ile A5 (store)'dur. O ajanlar farklı bir şekle ihtiyaç duyarsa **sözleşme değişiklik talebi** açarlar; protokol bunun için var. Şimdi spekülatif olarak değiştirilmez.

**2 · `OcrPreset` enum** — §5.3'te yoktu ama `recognize(frame, preset)` imzası bir tip gerektiriyordu; değerler §3.2'deki dört metin türünden alındı. Kabul, doğru türetme.

**3 · `Frame.image` ve `TranslationRequest.image_crops` eşitlik/hash dışında** — ndarray'in `==` operatörü dizi döndürdüğü için dataclass'ın üretilmiş `__eq__`'ü çalışma zamanında patlıyordu. Gerçek bir hata sınıfı, çözüm doğru. Tester bunu davranışsal olarak da doğruladı (farklı piksel içerikli iki `Frame` ile `==`, `hash()`, küme üyeliği). Kabul.

## Tester'ın bildirdiği kapsam sınırı

Tester, §5.3'ün `TermHit`/`Pair` için tam alan şeması vermediğini ve bu yüzden bunları katı alan-listesi karşılaştırmasıyla doğrulayamadığını **kendisi bildirdi** — gizlemek yerine `verdict.md` içine yazdı. Doğru davranış; bu bir eksiklik değil, dürüst kapsam beyanı.

## Sonuç

`src/contracts/` **donduruldu**. Bundan sonra hiçbir implementer ajanı bu dizine yazamaz. Değişiklik gerekirse `contract_change_request: true` ile talep açılır, kararı şef verir.

Dalga 1 (T-002 ChangeDetector, T-003 DPI dönüşümleri) başlatılabilir.
