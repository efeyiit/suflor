---
task: T-004
role: sef
round: 7
decision: kabul
---

# T-004 — TextNormalizer: KABUL

Yedi tur. Görev kapandı.

## Ne teslim edildi

`src/ocr/normalizer.py` (1.639 satır) ve `src/ocr/presets.py` (151 satır). `normalize(blocks, preset)` ham OCR bloklarını çeviriye hazır `Segment`'lere dönüştürür: satır içi `\n` collapse, hyphen çözme, güven eşiği filtresi, gürültü eleme, konuşmacı etiketi ayıklama, ön ayara göre gruplama, yer tutucu toplama.

`tests/unit/ocr/test_normalizer.py` — **125 test**. Kör tester takımı (`tester_A/B/C`) — **623 test**.

## Kapanış ölçümleri (şefin kendi koşumu)

```
mypy --strict                              exit 0
pytest tests/unit/ocr/test_normalizer.py   125 passed
purity_check.py                            exit 0   (saf, mutable global yok, deterministik)
olcu_kiti.py                               exit 0   KIT SAGLIGI: TEMIZ
pytest tests                               981 passed
kor tester takimi                          623 passed, 1 failed*
```

\* Tek kırık: `tester_A`'nın `strict=True` xfail'i, T7-1 düzeltilince XPASS'a döndü. **Kasıtlı olarak öyle kurulmuştu** — düzeltme yapılınca kendini duyursun diye. A onu yeşile çevirecek; regresyon değil.

## Tur kaydı

| Tur | Ne oldu |
|---|---|
| 1–4 | K1–K22 kararları; K9/K19/K21/K22 mekanizma olarak yazıldı ve etkileşimde battı |
| 5 | K23 iki-geçiş yapısı sağlandı (12.800 koşumda 0 bölümleme farkı); A **ret** — R5-1 |
| 6 | K28 uygulandı (miras sorgusunun iki tarafı da özgün bloktan); **üç tester de onay** |
| 7 | Kapanış: bayat `### K24` bölümü + M15 kapısı; **Tester-B onay** |

Tur 6'ya gelmeden **karar kırmızı takımı yedi geçiş** yaptı ve 55+ bulgu verdi. Değişmez (K28) üçüncü sürümden sonra hiç değişmedi; kırılan hep **ölçü** oldu. Kapı yedinci geçişte kapandı ve iş **iki saatte** bitti.

## Kalite kanıtı — sistem gerçekten işledi

**İmplementer'a giden hata sayısı: sıfır.** Her karar hatası kapıda kaldı.

Şefin kendi ölçülmüş hataları (hepsi kırmızı takım ya da tester tarafından yakalandı, hepsi şef tarafından yeniden üretildi):

| # | Hata | Yakalayan |
|---|---|---|
| 1 | `source_blocks[-1]` mekanizma yazıldı, değişmez sanıldı | KRT 1 |
| 2 | Ölçü fixture'ı üç uygulamada da aynı çıktıyı veriyordu — hiçbir şey ölçmüyordu | KRT 2 |
| 3 | İki uygulama seçeneğinden pahalı olanı **yanlış varyantını** ölçerek seçildi | KRT 2 |
| 4 | "Ölçtüm" denen sayı başka bir şeyi ölçüyordu | KRT 3 |
| 5 | Ölçülerin tamamı tek ön ayardaydı | KRT 3 |
| 6 | Ölçü **mekanizmaya** kancalanmıştı; mekanizma atlanınca sessizce boşalıyordu | KRT 4 |
| 7 | Hiçbir fixture 2 bloktan büyük kuyruk üretmiyordu — off-by-one görünmezdi | KRT 5 |
| 8 | Ölçü kiti referansı **denetlenen uygulamanın kendi verisinden** türetiyordu | KRT 6 |
| 9 | Kapı **doğru uygulamayı reddediyordu** (kapsam kanalı, iki sebep) | KRT 7 |
| 10 | Kabul komutu dört sayacı yazdırıyor ama **assert etmiyordu** | KRT 7 |
| 11 | K32'nin "NFC normalizasyonu çözer" varsayımı yanlış | Tester-C |
| 12 | "M5 → ölçü 5" tutmuyor (fixture'ın sağ tarafları tek bloklu) | Tester-B |
| 13 | `env.md` ile karar çelişiyordu (M4 → ölçü 3b) | Tester-B |
| 14 | `### K24` bölümü bayat mekanizma anlatıyordu | Tester-A |
| 15 | M15 ölçüsü tek ön ayarla körtü | Tester-B (tur 7) |

Bu tablo protokolün §4.6'sını doğurdu: **dokuz kural**, her biri yukarıdaki ölçülmüş bir hatadan.

## Açık kalemler (kapanışta kayda geçer, ayrı tur ister)

| Kalem | Neden ertelendi | Sahip |
|---|---|---|
| `Mn`/`Mc` taşıyan adlar konuşmacı sayılmıyor (Devanagari, İbranice, Arapça) | K9'un sözlüksel kuralını değiştirir — davranış değişikliği. **NFC normalizasyonu bu sınıfı kapatmaz** (şef ölçtü) | yeni görev |
| ZWJ/emoji: 1 grapheme = 5 codepoint, `max_group_chars` şişiyor | K11'in codepoint sayma kuralı | yeni görev |
| Miras `monitor_index`/`dpi_scale` sınırını aşıyor | Yeni değişmez gerektirir | yeni görev |
| `NaN` `dpi_scale` tanı mesajı kendi içinde çelişkili | Kozmetik | yeni görev |
| `olcu5_fixture`'ın sağ tarafları tek bloklu → ölçü 5 sağ ikameyi ölçemez | Kitin fixture'ı; ölçü kurgusuna dokunur | ölçü kiti |
| Kitin `adim1_4`'ü bağımsız değil (modülün kendi yardımcılarını çağırır) | §4.6/8'in kabul edilmiş ihlali; kit içinde yeniden yazmak yeni hata kaynağı | M12 → Tester-B |
| `n23` sınıfı (görünüm geçişi ters yön) kit tarafından ölçülmüyor | Kitin `_group` kararını yeniden uygulamasını gerektirir | M11 → Tester-B |
| MENU ve `apply_inheritance=False` kit tarafından koşulmuyor | — | M13 → Tester-B |
| `tester_C`'nin ölçek testleri tam takım yükü altında kararsız | Zamanlama; tek başına 125/125 kararlı | test altyapısı |

## Depo hijyeni notu

`f75d4d4` commit'i **temiz checkout'ta 2 toplama hatası** veriyor: başka bir görevin (T-005) kırmızı faz test dosyaları o commit'e süpürülmüş ama kaynak dosyaları henüz takipsizdi. Bir sonraki commit (`d81c913`) kapattı — **HEAD temiz, 981 passed**. Tarihte kırık bir nokta kaldı; `git bisect` orada takılır. Tester-B yakaladı. Ders PROTOKOL'e yazıldı: şef commit'i **açık yol listesiyle** atar, `git add -A` ile değil, ve paralel iş varken regresyonu kendi kapsamına daraltır.

## Karar

**T-004 KABUL.** Dört tester onayı (tur 6: A, B, C — tur 7: B), dört kabul komutu exit 0, 981 test yeşil, ürüne giren hata yok.
