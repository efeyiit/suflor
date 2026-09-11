---
task: T-009
role: implementer
round: 1
status: tamamlandi
files_written:
  - src/ocr/rapid_engine.py
  - tests/unit/ocr/test_rapid_engine.py
  - .agents/tasks/T-009/delivery.md
  - .agents/tasks/T-009/evidence/pozitif-kontrol-real_check-v4-oncesi.txt
  - .agents/tasks/T-009/evidence/tdd-kirmizi-testler-kod-oncesi.txt
  - .agents/tasks/T-009/evidence/mypy.txt
  - .agents/tasks/T-009/evidence/pytest.txt
  - .agents/tasks/T-009/evidence/real_check-T009.txt
  - .agents/tasks/T-009/evidence/real_check-T006.txt
  - .agents/tasks/T-009/evidence/pytest-tum.txt
  - .agents/tasks/T-009/evidence/mypy-test-dosyasi.txt
  - .agents/tasks/T-009/evidence/pytest-cp1254.txt
  - .agents/tasks/T-009/evidence/mutant-kiti.py
  - .agents/tasks/T-009/evidence/mutant-ayirt-etme.txt
  - .agents/tasks/T-009/evidence/olcum-1-surum-mu-dosya-mi-baskin.py
  - .agents/tasks/T-009/evidence/olcum-1-surum-mu-dosya-mi-baskin.txt
  - .agents/tasks/T-009/evidence/bayatlayan-T006-tester-testleri.txt
commands:
  - cmd: "python -m mypy --strict --explicit-package-bases src/ocr/rapid_engine.py"
    exit_code: 0
    evidence: evidence/mypy.txt
  - cmd: "python -m pytest tests/unit/ocr/test_rapid_engine.py -q"
    exit_code: 0
    evidence: evidence/pytest.txt
  - cmd: "python .agents/tasks/T-009/real_check.py"
    exit_code: 0
    evidence: evidence/real_check-T009.txt
  - cmd: "python .agents/tasks/T-006/real_check.py"
    exit_code: 0
    evidence: evidence/real_check-T006.txt
  - cmd: "python -m pytest tests -q"
    exit_code: 0
    evidence: evidence/pytest-tum.txt
  - cmd: "python .agents/tasks/T-009/real_check.py  (POZITIF KONTROL: kod degismeden once, v4 -- 3/3 IHLAL beklenir)"
    exit_code: 1
    evidence: evidence/pozitif-kontrol-real_check-v4-oncesi.txt
  - cmd: "python -m pytest tests/unit/ocr/test_rapid_engine.py -q  (TDD KIRMIZI: testler yazildi, kaynak degismedi -- 8 dusen beklenir)"
    exit_code: 1
    evidence: evidence/tdd-kirmizi-testler-kod-oncesi.txt
  - cmd: "python .agents/tasks/T-009/evidence/mutant-kiti.py --gercek  (T009_AYNA=<scratchpad>/t009_ayna; 4 mutant + 1 kontrol, birim + gercek kapi, ayna agaci)"
    exit_code: 0
    evidence: evidence/mutant-ayirt-etme.txt
  - cmd: "python .agents/tasks/T-009/evidence/olcum-1-surum-mu-dosya-mi-baskin.py  (gercek model; Rec.ocr_version mi Rec.model_path mi baskin, 6 nokta)"
    exit_code: 0
    evidence: evidence/olcum-1-surum-mu-dosya-mi-baskin.txt
  - cmd: "python -m pytest tests/unit/ocr/test_rapid_engine.py -q -p no:cacheprovider  (PYTHONIOENCODING YOK, stdout cp1254)"
    exit_code: 0
    evidence: evidence/pytest-cp1254.txt
  - cmd: "python -m mypy --strict --explicit-package-bases tests/unit/ocr/test_rapid_engine.py  (kabul disi; 1 hata HEAD'de de var, bkz. known_gaps)"
    exit_code: 1
    evidence: evidence/mypy-test-dosyasi.txt
  - cmd: "python -m pytest .agents/tasks/T-006/tester_A/test_a_sozlesme_sayisal.py .agents/tasks/T-006/tester_B/test_mercek_B.py -q  (SALT OKUNUR; sahipligim disi bayatlayanlari listelemek icin)"
    exit_code: 1
    evidence: evidence/bayatlayan-T006-tester-testleri.txt
budget_ms_measured: 316-333   # T-009 real_check #3 medyan (butce 400; v4 1085-1096)
contract_change_request: false
known_gaps:
  - "ENGLISH v5 (K5): mumkun, %25 hizli, olculmus kusur yok -- ACIK KALEM, kapsam disi; tabloda v4."
  - "CHINESE v5: hic olculmedi; tabloda v4."
  - "Gercek kapi (T-009 real_check) yalniz `_MODEL_DOSYALARI`yi gorur; `Rec.ocr_version`in KOREAN'da v5 olmasi urun yolunda (allow_download=False) davranisi DEGISTIRMEZ (olcum-1 B). Surum yalniz indirme yolunda (allow_download=True) belirleyici (olcum-1 C/D). Bu yuzden `Rec.ocr_version` icin tek bekci birim testlerdir (`test_k11_t009_*`); JAPAN'a sizan v5 acik yolda sessizce v4 kosar (olcum-1 F, mutant M03)."
  - "T-006 tester dosyalari sahipligim disinda BAYATLADI (5 test, KOREAN v4 dosya adi bekliyor) ve T-006 tester_B mutant kiti 2 ikame noktasi (`_OCR_SURUMU`, KOREAN v4 satiri) artik bulunmuyor -- sef gunceller (paket K4 notuyla ayni sinif). `pytest tests` bunlari toplamaz; kabul etkilenmez."
  - "tests/unit/ocr/test_rapid_engine.py satir 321 (HEAD'de 310): kullanilmayan `type: ignore` -- mypy --strict 1 hata, HEAD'de de var, T-009'un eklemedigi bir satir; dokunulmadi (kapsam disi, kabul komutu degil)."
  - "T-006 real_check [5] ENGLISH medyan 365 ms > 350 UYARI (ihlal degil, exit 0): EN tablosu degismedi; olgular K5'te EN v4 zaten 376 ms -- T-009 oncesi de esigin ustunde."
---

# T-009 teslim — Korece tanıma modeli PP-OCRv5 (K11 tek satır + dosya adı), tur 1

## Ne değişti

**`src/ocr/rapid_engine.py`**
- `_DIL_TABLOSU` 4'lü oldu: `(dil, Det.lang_type, Rec.lang_type, Rec.ocr_version)`. KOREAN → `"PP-OCRv5"`; JAPAN/CHINESE/ENGLISH → `"PP-OCRv4"`.
- `_OCR_SURUMU` → `_TESPIT_SURUMU` (`"PP-OCRv4"`, yalnız `Det.ocr_version`; artık "ortak" değil, adı da öyle söylemesin).
- `_MODEL_DOSYALARI` KOREAN rec → `korean_PP-OCRv5_rec_mobile.onnx` (diskte 13.49 MB, şef indirdi).
- `_dil_satiri` 3'lü döndürür; `parametreler()` `Rec.ocr_version`'ı satırdan alır, `Det.ocr_version` sabit v4.
- Enum'lar gerçek fabrikada, `params`'ta string (T-006 K1/K11 kararı değişmedi; `_varsayilan_fabrika`'ya dokunulmadı — `OCRVersion("PP-OCRv5")` çevirisi zaten oradaydı).
- K11 docstring: v4/v5 tablosu, neden KOREAN v5 (K1/K4 sayıları), neden diğerleri v4 (K5: JP'de `ValueError`, EN açık kalem), **hangisi belirleyici** (ölçüm-1, aşağıda), ölçü listesi.

**`tests/unit/ocr/test_rapid_engine.py`** (110 → 119 test)
- Bağımsız referanslar: `MODEL_ADLARI[KOREAN]` rec v5; yeni `TESPIT_SURUMU`, `TANIMA_SURUMU` (dil → sürüm), `KOREAN_ESKI_REC` (negatif referans).
- Yeni `test_k11_t009_*` (8): KOREAN rec v5 / det v4 (nokta 1); JAPAN ikisi v4 (nokta 2); CH/EN v4; v5 yalnız KOREAN; boş `model_dir` → `ModelMissingError` mesajında v5 adı, v4 adı YOK, fabrika çağrılmamış; dizinde yalnız v4 dosyası varsa yine `ModelMissingError` (v4'e düşülmez); v5 dosyası varsa açık yol; docstring K11 güncel.

## Bayatlayan / yeniden nişanlanan testler (paket K1)

Sahipliğimde, yeniden nişanlandı:
1. `test_k11_dil_tablosu_alti_anahtar[korean]` — `Rec.ocr_version == "PP-OCRv4"` bekliyordu → `TANIMA_SURUMU[dil]`; `Det` ayrıca `TESPIT_SURUMU`.
2. `test_k6_model_var_acik_yol_gecilir[korean]` — `MODEL_ADLARI` üzerinden v4 dosya adı bekliyordu → referans v5.

Sahipliğim dışında, **bayatladı, dokunmadım** (şefe): `.agents/tasks/T-006/tester_A/test_a_sozlesme_sayisal.py::test_a5_k11_dort_dil_alti_anahtar_birebir[korean]`; `.agents/tasks/T-006/tester_B/test_mercek_B.py::{test_b3_sahte_fabrikayla_tam_kosum_yasak_kok_yuklemez, test_b5_modelmissing_kurulumda_ornek_tutulmaz_dosya_gelince_kurulur, test_b5_iki_motor_ayni_fabrikayi_paylasirsa_durum_karismaz, test_b6_eksik_iki_satir_yapisal_olarak_erisilemez}` (5'i de KOREAN v4 dosya adı referansı); `.agents/tasks/T-006/tester_B/mutant_kiti.py` M06 (`_OCR_SURUMU` yok) ve KOREAN v4 satır ikamesi. Kanıt: `evidence/bayatlayan-T006-tester-testleri.txt`.

## TDD ve pozitif kontrol

- Kod değişmeden T-009 `real_check`: **3/3 ihlal** ('.'=0, 6 kelime yalnız "bekliyor", 1085 ms) — kapı ateşliyor.
- Testler yazıldı, kaynak değişmeden: **8 düşen / 111 geçen** (2 yeniden nişanlanan + 6 yeni; JAPAN/CH/EN v4 testleri zaten geçiyor).
- Kaynak değişti: mypy temiz, 119/119; T-009 `real_check` **TEMİZ** ('.'=3, 15 kelime, üç anahtar, medyan 316–333 ms ≤ 400); T-006 `real_check` **TEMİZ** (KOREAN benzerlik 0.95+ → **1.000**, noktalar geldi); tam takım 1444 geçti, düşen yok.

## Ayırt etme (ayna ağacı, `mutant-kiti.py --gercek`)

| mutant | birim | gerçek T-009 kapısı |
|---|---|---|
| M01 KOREAN `Rec.ocr_version` v5→v4 (dosya v5) | X (4) | **GEÇER** (ölçüldü; aşağıda) |
| M02 KOREAN dosya adı v5→v4 (sürüm v5) | X (7) | DÜŞER ('.'=0, 6 kelime, 1083 ms) |
| M01+M02 = T-009 öncesi kod (pozitif kontrol) | X (7) | DÜŞER (3/3) |
| M03 JAPAN v4→v5 (KOREAN da v5) | X (3) | JAPAN açık yolda **istisna yok**, 4 blok (aşağıda) |
| C-1 tablo satır sırası (eşdeğer kontrol) | . | — |

## Ölçümün görev metniyle çeliştiği yer (ölçüme uydum)

Görev "KOREAN v5 → v4 geri: T-009 real_check #1/#2 düşmeli" diyordu. **Yalnız `Rec.ocr_version`'ı geri alan mutant (M01) gerçek kapıyı geçti.** Sebep (ölçüm-1, kaynak değiştirilmeden fabrika sarmalayıcısıyla, gerçek model, dlg_KR):

| | allow_download | Rec.ocr_version | model_path | '.' | medyan |
|---|---|---|---|---|---|
| A ürün | False | v5 | v5 dosyası | 3 | 341 ms |
| B (M01) | False | **v4** | v5 dosyası | **3** | 385 ms |
| C | True | v5 | yok | 3 | 384 ms |
| D | True | v4 | yok | **0** | 1539 ms |
| E JAPAN | True | v5 | yok | `OcrError` ← `ValueError` | — |
| F JAPAN | False | v5 | v4 dosyası | istisna yok, 4 blok | 325 ms |

Yani: `allow_download=False` (ürün yolu) `Rec.model_path`'i açık verir, kütüphane o dosyayı yükler, `ocr_version` dosya seçimine katılmaz → belirleyici olan **`_MODEL_DOSYALARI`** (paket K2'nin pozitif kontrol tarifiyle uyumlu: "`_MODEL_DOSYALARI`'nı v4'e geri çeviren mutant"). `Rec.ocr_version` yalnız indirme yolunda dosyayı seçer (C/D). İkisi tutarlı tutuldu; `Rec.ocr_version` için tek bekçi birim testler. Ayrıca olgular K5'in "JP'de v5 → `ValueError`" olgusu **indirme yolunda** doğru (E), açık yolda JAPAN v5 etiketi sessizce v4 dosyasını koşar (F) — gerçek kapı M03'ü göremez; `test_k11_t009_japan_ikisi_de_v4` tek bekçidir. Bu üçü K11 docstring'ine yazıldı.

## Notlar
- `git commit` atılmadı; `pip install` yok; yasak dosyalara dokunulmadı (`git diff --stat`: yalnız `rapid_engine.py` ve `test_rapid_engine.py`; diğer iki dosya T-008'in).
- Kütüphane `Global.log_level="error"` altında ölçüm-1 E'de kendi ERROR satırını stderr'e bastı (desteklenmeyen kombinasyon açıklaması, OCR metni değil); kanıt dosyasında duruyor.
- Metin basılmadı; stdout ASCII.
