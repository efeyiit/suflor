---
task: T-009
title: "Korece tanıma modeli PP-OCRv5: cümle sonu noktaları korunur (T-006 K11 düzeltmesi)"
role: implementer
level: B
wave: 2
packet_version: 1
owns:
  - "src/ocr/rapid_engine.py"
  - "tests/unit/ocr/test_rapid_engine.py"
  - ".agents/tasks/T-009/evidence/**"
  - ".agents/tasks/T-009/delivery.md"
forbidden:
  - "src/contracts/**"
  - "src/ocr/normalizer.py"
  - "src/ocr/satir_birlestirici.py"
  - "src/translate/**"
  - "tests/unit/ocr/conftest.py"
  - "tests/unit/ocr/test_normalizer.py"
  - "tests/unit/ocr/test_satir_birlestirici.py"
  - ".agents/tasks/T-006/**"
  - ".agents/tasks/T-009/real_check.py"
  - "demo/**"
  - "diğer tüm dizinler"
depends_on: ["T-006", "T-007", "T-008"]
acceptance:
  - "python -m mypy --strict --explicit-package-bases src/ocr/rapid_engine.py"
  - "python -m pytest tests/unit/ocr/test_rapid_engine.py -q"
  - "python .agents/tasks/T-009/real_check.py"
  - "python .agents/tasks/T-006/real_check.py"
  - "python -m pytest tests -q"
budget_ms: 400   # KR dlg fixture 17 kutu, v5 rec: ölçüldü 332 ms (v4: 1099)
---

> **Kapsam: T-006'nın K11 tablosunda tek satır + dosya adı.** `olgular.txt` K1–K5 ölçüldü. Kırmızı takım **yok** (§4.5 gerekçe: yeni değişmez yok, K11'in bir hücresi değişiyor, ölçü mevcut kapılarda). **Bir** tester.

# Neden

Korece PP-OCRv4 tanıma modeli cümle sonu noktalarını **hiç vermiyor** (K1: 3 noktadan 0, tespit değil tanıma). Sonuç: T-008 sonrası bile üç cümle tek segmentte noktasız → T-007 bölemez → NMT içerik yitirir ("doğu", "güneş" kayıp). **PP-OCRv5 Korece mobile** üç noktayı da veriyor, aynı kelime doğruluğu (17/17), **3× hızlı** (332 vs 1099 ms). Uçtan uca: 3 cümle → çeviri 15 kelime, üç anahtar da var (K4).

# Değişmezler

## K1 · Tanıma sürümü dile özel; Korece v5, diğerleri v4
**DEĞİŞMEZ:** `_DIL_TABLOSU` (ya da eşdeğeri) dil başına `Rec.ocr_version` taşır: KOREAN → `PPOCRV5`; JAPAN/CHINESE/ENGLISH → `PPOCRV4` (JP'de v5 **yok** — `ValueError`, K5; EN v5 mümkün ama kapsam dışı). `Det.ocr_version` her dilde `PPOCRV4` kalır. `_MODEL_DOSYALARI` KOREAN rec → `korean_PP-OCRv5_rec_mobile.onnx`.
**ÖLÇÜ:** Sahte fabrika `params`: KOREAN'da `Rec.ocr_version == OCRVersion.PPOCRV5`, `Det.ocr_version == PPOCRV4`; JAPAN'da ikisi de `PPOCRV4` (**iki nokta**). `allow_download=False` + `model_dir` KOREAN için `korean_PP-OCRv5_rec_mobile.onnx` arar (dosya yoksa `ModelMissingError` mesajında bu ad). Mevcut testlerden bayatlayanlar (KOREAN v4 dosya adı bekleyen) yeniden nişanlanır — **hangileri**, `delivery.md`'de listelenir.

## K2 · Korece çıktı noktaları korur (gerçek model)
**DEĞİŞMEZ:** `dlg_KR.png` → 17 blok, blok metinlerinde toplam `.` **≥ 3**.
**ÖLÇÜ:** `T-009/real_check.py` #1 (şefe ait). **Pozitif kontrol:** aynı kapı, `_MODEL_DOSYALARI`'nı v4'e geri çeviren mutantta `.` = 0 → düşer.

## K3 · Uçtan uca Korece
**ÖLÇÜ:** `T-009/real_check.py` #2: KR → `satirlari_birlestir` → `normalize` → `LocalNmtProvider` → çeviri ≥ 12 kelime **ve** "bekliyor" + ("doğu"|"dogu") + ("güneş"|"gunes"|"gün") üçü de var (K4'te 15 kelime ölçüldü; v4 ile 6 kelime, yalnız "bekliyor"). Bu, T-008 `real_check`'inden **kaldırılan** "doğu" beklentisinin doğru yeridir.

## K4 · T-006 kapısı bozulmaz
**ÖLÇÜ:** `python .agents/tasks/T-006/real_check.py` yine 16/16 (KR benzerlik artık ≥ 0.95'in üstünde, noktalar geldiği için **yükselir**; JP/EN/CHINESE değişmez). Not: T-006 `real_check`'in "#3 noktalar düşüyor, bilinen kayıp" yorumu bayatlar — **şef** günceller, implementer dokunmaz.

# Teslim
`delivery.md` — `validate.py`; `round: 1`; bayatlayan/yeniden nişanlanan testler listeli; K1 docstring K11 bölümü güncel (v4/v5 tablosu, K5 EN notu). **`git commit` atma.** Model dosyası (`korean_PP-OCRv5_rec_mobile.onnx`) diskte (şef indirdi). Metin basma; model/sağlayıcı/araç adı yazma.
