---
task: T-009
role: sef
round: 1
decision: kabul
---

# T-009 — Korece tanıma PP-OCRv5: KABUL

Tek tur. Görev kapandı. **Korece zinciri uçtan uca çalışıyor.**

## Ne teslim edildi

`src/ocr/rapid_engine.py` K11 tablosu: `Rec.ocr_version` dile özel (KOREAN → v5, diğerleri v4), `Det` v4 sabit, KOREAN rec dosyası `korean_PP-OCRv5_rec_mobile.onnx`. 110 → 119 test (8 yeni, 2 yeniden nişan). Kör tester — 41 test, 8 mutant, dört dil gerçek model.

**Gerçek modelle:** KR 17 blok, **3 nokta** (v4: 0), kelime 17/17, **~330 ms** (v4: 1099). Uçtan uca (T-008 + T-009): 17 kutu → 2 segment → 3 cümle → çeviri **15 kelime**, "bekliyor/doğu/güneş" üçü de var (v4: 6 kelime, yalnız "bekliyor"). T-006 kapısı 16/16, KR benzerlik 0.971 → **1.000**. `demo/canli_cevir.py korean` canlı doğrulandı (`korece_uctan_uca.png`).

## Kapanış ölçümleri (şefin koşumu)

```
mypy --strict                          exit 0
pytest birim                           119 passed
T-009 real_check                       TEMİZ 3/3   (v4 kodla 3/3 ihlal — pozitif kontrol)
T-006 real_check                       TEMİZ 16/16 (1 uyarı: EN 365 ms, T-009'dan bağımsız)
pytest tests                           1444 passed
tester                                 41 passed
şefin mutantı (dosya adı v5→v4)        birim 8, kapı 3/3 yakalandı
```

## Neden tek tur, KRT yok
Yeni değişmez yok; K11'in bir hücresi ölçümle değişti (K4: v5 noktaları verir, 3× hızlı; K5: JP'de v5 yok). §4.5 gerekçeli azaltma; bir tester.

## Kalite kanıtı
**İmplementer'a giden kod hatası: sıfır.** Implementer ölçülü itiraz etti ve haklıydı: açık `model_path` verilince kütüphane sürüm etiketini dosya seçiminde kullanmıyor — belirleyici **dosya adı** (T-006 tester A'nın `lang_type` bulgusuyla aynı sınıf; şef bunu iki görev önce öğrenmişti, paketin K2 pozitif kontrol tarifi zaten doğruydu ama implementer talimatındaki "sürüm v4'e geri → kapı düşmeli" cümlesi yanlıştı — **şef hatası**).

## Açık kalemler

| Kalem | Not | Sahip |
|---|---|---|
| **`ch` det + KR v5 rec `dlg_KR`'de 4 satır kutusu, boşluklar korunmuş, 4/4, `.`=3, ~314 ms** — T-008 birleştirmesine KR'de gerek kalmayabilir | Tek fixture; menü fixture'larıyla ölçülmeden tabloya girmez. KRT Y3 "ch det boşluk yitirir" v4 ile ölçülmüştü | yeni görev (ölçüm) |
| EN v5: 4/4, %25 hızlı | Değişiklik ölçüm ister; kusur yok | açık |
| Sürüm etiketi ürün yolunda inert; JP'ye sızan v5 → `ModelMissingError` (sessiz değil), Det v5 / etiket mutantları yalnız birim yakalar | Belgeli | kayıt |
| T-006 tester A'nın 1 testi **iki** noktada bayat, tester B kitinde **4** ikame hedefi bayat (kit M04'te `SystemExit`) | Kapalı görevin tester dosyaları | T-006 A/B |
| T-009 tester'ın `import conftest` ürün conftest'iyle çakışıyor (birlikte koşumda 2 kırık) | T-006 B ile aynı sınıf; ürün etkilenmez | tester |
| Süre bütçesi payı ~%15; %52 dış yük altında 437 ms ölçüldü | Makineye bağlı | kayıt |

## Karar
**T-009 KABUL.**
