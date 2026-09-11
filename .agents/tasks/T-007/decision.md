---
task: T-007
role: sef
round: 2
decision: kabul
---

# T-007 — LocalNmtProvider: KABUL

İki tur. Görev kapandı. **Dalga 2'nin ilk bileşeni — projede ilk Türkçe.**

## Ne teslim edildi

`src/translate/local_nmt.py` (~760 satır). `LocalNmtProvider(model_dir, threads, beam_size, repetition_penalty, motor_fabrikasi)` — `TranslationProvider` Katman 1 uygulaması, NLLB-200-distilled-600M CT2 int8. Cümle bölme noktalamaya göre (altı işaret, her biri ayrı ölçülü) + tek batch; harf içermeyen ve yalnız-yer-tutucu parçalar modele gitmez; yer tutucu sayım onarımı; üç biçimli dil kodu; dört zorunlu model dosyası; sentencepiece bayt ile; hiçbir kanala metin yazmaz.

`tests/unit/translate/test_local_nmt.py` — **255 test** (K1 bariyeri altında). Kör tester A+B — **427 test**.

**Gerçek modelle (`real_check.py`, 13/13, cp1254'te de):** JP 4 cümle 311 ms (78 ms/cümle, tasarım 4.2 aralığında) · KR tek segment 2 cümle · JP 3-cümlelik paragraf → 3 cümle (tek girdide 2. cümle eriyordu) · yalnız-noktalama aynen · yer tutucu onarımı · ASCII-dışı `model_dir` · `ModelMissingError` / `ProviderUnavailable`. `demo/canli_cevir.py` bu sağlayıcıyı gerçek ekranda kullanıyor.

## Kapanış ölçümleri (şefin kendi koşumu)

```
mypy --strict                          exit 0
pytest birim                           255 passed
real_check.py                          TEMIZ 13/13
kapsam                                 %100
pytest tests (tam takım)               1359 passed
kör takım A / B                        265 (3 bayat*) / 162 passed
şefin mutantları (M1–M4, K3-03)        hepsi yakalandı
B'nin kiti tur 2                       53+6 → 53 yakalandı, 6 kontrol kaçtı; T2-2 8/8, 3/3 kontrol
```

\* A'nın 3 kırığı T2-2'nin kaçınılmaz bayatlaması (`modele_gider` imzası değişti; A'nın mutant sondası eski imzayı yamalıyor) — A'nın yükümlülüğü.

## Tur kaydı

| Tur | Ne oldu |
|---|---|
| ölçüm | Dokuz ön ölçüm (C1–C9): model 647 MB, hız tutuyor, JP/KR kalitesi tek başına yetmiyor, tekrar cezası halüsinasyon, cümle bölme şart, JP'de yer tutucu kayboluyor, sentencepiece ASCII-dışı yol |
| paket | v1 → **tek** KRT geçişi: 3 yüksek (bölme dile göre yazılmış — KR ASCII nokta, hiç bölünmüyordu; yalnız-noktalama parçası uydurma; 200 ms bütçesi uydurma) → v2 |
| 1 | Implementer teslim. **A onay** (K-1: `{PLAYER}!` uydurma) · **B ret** (`?`/`！` terminatörleri 6 noktanın 4'ünde ölçülü; `?` çıkarılınca beş kapı yeşil, üründe ilk cümle kayıp) |
| 2 | Altı terminatör ayrı ayrı; yer tutucu çıkarıldıktan sonra süzgeç; hata mesajı nöbetçisi + `match=`. **B onay** |

## Kalite kanıtı

**İmplementer'a giden kod hatası: bir** (T2-2 — yalnız-yer-tutucu cümle; paketin Y2 kuralının doğal uzantısıydı, paket eksik yazmıştı). Implementer üç gerekçeli itiraz yazdı (K5 sayım, K6 boyut, K10 `Logger.handle`); üçü de kabul.

Şefin ölçülmüş hataları:

| # | Hata | Yakalayan |
|---|---|---|
| 1 | Bölme kuralı dile göre (`。！？`); Korece ASCII nokta kullanır — KR hiç bölünmüyor, 2. cümle kayıp | KRT-1 |
| 2 | Yalnız-noktalama parçası modele gidince "Hayır, hayır." uyduruluyor; "kayıpsızlık" ölçüsü bunu geçiriyordu | KRT-1 |
| 3 | 200 ms bütçesi ölçülmeden yazıldı; beam=4'te 316 | KRT-1 |
| 4 | K3 terminatör ölçüsü paketin kendisinde de altı noktada değildi | Tester-B |
| 5 | `sef_karari-tur2.md` `real_check #4c`'ye atıf yaptı; öyle bir kontrol yok | Tester-B |
| 6 | Tamamlayıcı B ajanı başlatarak aynı dizine iki süreç yazdırdım (B eşzamanlı yazımı fark etti) | Tester-B |

## Açık kalemler

| Kalem | Neden ertelendi | Sahip |
|---|---|---|
| **KR tanıma modeli cümle sonu noktasını düşürüyor** → KR 3 cümle tek girdi, içerik kaybı | Model sınırlaması; T-008 KRT bulду | **T-009** |
| Kapanış işareti kümesi (9) tek noktada ölçülü; `．` ve `\n` terminatör değil | Keskinlik; kayıp/uydurma yok | Tester-B (hazır ölçü `test_mercek_B_r2.py`) |
| Yer tutucu **bozulması** (`[Mill]`→`[Mill'de]`) sayımla görünmez; çift üretim olası | Katman 0/2'nin işi | yeni görev |
| Tekrar dejenerasyonu (KR "Doğu'ya doğru Doğu'ya doğru"); ceza halüsinasyon üretiyor | Altın set yok | tasarım 12 |
| `glossary_hits`/`tm_examples`/`style_profile` kabul edilir, uygulanmaz | NMT kısıt almaz | Katman 0 |
| `translate/` dizininden `pytest .` → `src` import edilemiyor (conftest kökü eklemiyor) | Test altyapısı | şef |
| A'nın 3 bayat testi | T2-2 imza değişikliği | Tester-A |
| Model kaynağı topluluk dönüşümü; üretimde resmi + checksum | ModelManager | **kullanıcı kararı** |

## Karar

**T-007 KABUL.** İki tester onayı (A tur 1, B tur 2), beş kabul komutu exit 0, gerçek modelle 13/13, 1359 test yeşil, gerçek ekranda Türkçe.
