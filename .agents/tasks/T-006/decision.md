---
task: T-006
role: sef
round: 2
decision: kabul
---

# T-006 — RapidOcrEngine: KABUL

İki tur. Görev kapandı. **Dalga 1 tamamlandı.**

## Ne teslim edildi

`src/ocr/rapid_engine.py` (~700 satır). `RapidOcrEngine(language, threads, allow_download, model_dir, recognizer_factory)` — `OcrEngine` sözleşmesinin v1 uygulaması. Dil açık (JAPAN/KOREAN/CHINESE/ENGLISH), iş parçacığı aralık denetimli, kütüphanenin 0.5 süzgeci zorla kapalı, `bbox` ekran koordinatında düz `int`, dil başına sabit v4-mobile model tablosu, tembel import, hiçbir kanala OCR metni yazmaz.

`tests/unit/ocr/test_rapid_engine.py` — **110 test**, tümü K1 bariyeri altında (gerçek model yüklenemez). Kör tester takımı A+B — **154 test**.

**Gerçek modelle (`real_check.py`, 16/16):** Japonca 4/4 birebir **187 ms** · İngilizce 4/4 235 ms · Korece 0.971 (17 kutu, 41 ms/kutu) · Çince modeli Japonca'da 0/4 (dil ölçüsü ateşliyor) · süzgeç-kapalı kanıtı (17 bloktan 8'i `<0.5` döndü) · bbox iki noktada kaydırma tam · model yok → `ModelMissingError`. `demo/canli_oku.py` ve `demo/canli_cevir.py` bu motoru gerçek ekranda canlı kullanıyor.

## Kapanış ölçümleri (şefin kendi koşumu)

```
mypy --strict                          exit 0
pytest birim                           110 passed
real_check.py                          TEMİZ 16/16  (cp1254 altında da)
kapsam                                 %98.94 (188 ifade, 2 eksik — yapısal olarak erişilemez)
pytest tests (tam takım)               1100 passed
kör takım A / B / A+B                  106 / 48 / 154 passed
şefin mutantları (M1–M4, R16)          hepsi yakalandı
B'nin kiti (47 davranış + 4 kontrol)   47 yakalandı, 4 kontrol kaçtı
```

## Tur kaydı

| Tur | Ne oldu |
|---|---|
| paket | Ön ölçüm (O1–O6) → sürüm 1 → **tek** kırmızı takım geçişi (§4.6/9): 7 yüksek, şef üçünü üretti → sürüm 2 |
| 1 | Implementer teslim; `real_check`'in 2 ihlali **kapıda** çıktı (round-kova, imkânsız `y<0`), şef düzeltti. **A onay · B ret** — K7 ölçüsü `print` **adını** sayıyordu; `sys.stdout.write` mutantı 95 testten geçti |
| 2 | K7 ölçüsü davranışa kancalandı (capfd + kök caplog + warnings, iki nokta, 7 pozitif kontrol). **B onay** |

Paket **1** kırmızı takım turu gördü (T-005: 8). Tester **2** mercek (T-005: 4). İki turda kapandı (T-005: 3). Kalite kapısı yerinde, daha dar.

## Kalite kanıtı

**İmplementer'a giden kod hatası: sıfır.** `src` mantığı tur 1'den beri değişmedi (tur 2 diff'i AST ile docstring-only doğrulandı). Implementer pakete **üç** gerekçeli itiraz yazdı (K6/K11 ↔ K1 çelişkisi, `capsys`→`capfd`, `recwarn`→`catch_warnings`); üçü de haklıydı.

Şefin bu görevde ölçülmüş hataları:

| # | Hata | Yakalayan |
|---|---|---|
| 1 | Paket K5: kütüphanenin `text_score=0.5` süzgecini görmedi — sözleşme ihlali (17→9 kutu) | KRT-1 |
| 2 | Paket: model sürümü sabitlenmemiş; varsayılan v6 KOREAN'da çöker, JAPAN 2× yavaş | KRT-1 |
| 3 | Paket K3: `threads > cpu_count` sessizce otomatiğe döner, denetim yoktu | KRT-1 |
| 4 | Paket K1: bariyer fixture'da tarif edilmiş; modül düzeyi import'u görmez | KRT-1 |
| 5 | Paket K6/K11: canlı çözücü + enum karşılaştırması K1 bariyeriyle çelişiyor | Implementer |
| 6 | `real_check` `round(y/25)` kova sınırı satırı bölüyor (0.932 vs 0.971) | Implementer |
| 7 | `real_check` `[6a] y<0` yapısal olarak imkânsız (satır y=93, kaydırma −50) | Implementer |
| 8 | Paket K7 ölçüsü mekanizma adına kancalı (`print`, `.text`, logger adı) — §4.6/7'nin üçüncü tekrarı | Tester-B |
| 9 | `real_check`'e `≈` eklendi; paketin uyardığı cp1254 tuzağına kapı düştü | Tester-B |
| 10 | Karar T2-2 "bir satır src" — satır zaten vardı, eksik olan ölçüydü | Implementer |
| 11 | `real_check` #2 pozitif kontrolünün gerekçesi yanlış: `lang_type` değil dosya-adı tablosu ateşliyor | Tester-A |
| 12 | Paket K9 "süre kutu sayısına bağlı" eksik: tespit görüntü boyutuyla ölçekleniyor | Tester-A |
| 13 | Şefin harness'ı "1 error during collection"ı "0 failed" okudu (M4) | şef |
| 14 | Şefin M2 mutantı docstring'e isabet etti, kod değişmedi | şef |

## Açık kalemler

| Kalem | Neden ertelendi | Sahip |
|---|---|---|
| `preset` v1'de motoru değiştirmiyor; ön ayar bazlı ölçekleme/kontrast `[ÖLÇÜLMÜYOR]` | Ölçülmeden yazılmaz; küçük yazı (14 px) deneyi gerekir | yeni görev |
| Cls modeli silinmişse `allow_download=False` altında kütüphane yine indiriyor | Kütüphane davranışı; v1'de cls paketle geliyor | kayıt |
| `lang_type` yalnız `allow_download=True` yolunda ölçülür; `real_check`'e A'nın D10 biçimi eklenmeli | Kapı keskinliği | şef |
| `real_check` bayt düzeyinde stdout/stderr ölçmüyor (zaman-penceresi sınıfı) | B'nin Ş2'si; birim testte var | şef |
| B'nin bariyer testleri `match="tester-B K1 bariyeri"` — şefin conftest'iyle birlikte koşunca 9 kırık (iki bariyer de çalışıyor, test yalnız kendi mesajını arıyor) | Test altyapısı; ürün etkilenmez | Tester-B |
| `dpi_scale` numpy ise denetlenmiyor (x/y/monitor_index denetleniyor) | `CaptureService` düzleştiriyor; üretimde erişilemez | kayıt |
| Handler `.stream`'e doğrudan yazma (R04/R05) ölçüde kör | `recognize` içinde makul yol değil | kayıt |
| JP/KR modelleri ilk kullanımda 11.6 MB indirir; "ilk açılışta tamamen çevrimdışı" iddiası bu diller için tutmuyor | Tasarım metni ya da kurulum paketi kararı | **kullanıcı** |
| Model kaynağı modelscope.cn (resmi dağıtım) | Erişilebilirlik riski; ModelManager'da yansı/checksum | T-0xx |

## Karar

**T-006 KABUL.** İki tester onayı (A tur 1, B tur 2), beş kabul komutu exit 0, gerçek modelle 16/16, 1100 test yeşil, gerçek ekranda canlı çalışıyor.

**Dalga 1 tamamlandı:** sözleşmeler (T-001) · değişim tespiti (T-002) · DPI (T-003) · normalizer (T-004) · yakalama (T-005) · OCR (T-006). Zincir uçtan uca gerçek ekranda doğrulandı (`demo/canli_oku.py`).
