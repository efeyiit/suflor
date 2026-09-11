---
task: T-009
role: tester
round: 1
decision: onay
checks:
  - name: "mypy --strict rapid_engine.py temiz"
    cmd: "python -m mypy --strict --explicit-package-bases src/ocr/rapid_engine.py"
    exit_code: 0
    result: gecti
    evidence: tester_evidence/01-mypy.txt
  - name: "sefin 119 birim testi"
    cmd: "python -m pytest tests/unit/ocr/test_rapid_engine.py -q -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_evidence/02-pytest-119.txt
  - name: "T-009 real_check (gercek model): 17 blok '.'=3, uctan uca 15 kelime + uc anahtar, 335 ms"
    cmd: "python .agents/tasks/T-009/real_check.py"
    exit_code: 0
    result: gecti
    evidence: tester_evidence/03-real_check-T009.txt
  - name: "T-006 real_check (gercek model): 16/16, KR benzerlik 1.000, EN 364 ms UYARI (T-009 oncesi de esik ustu)"
    cmd: "python .agents/tasks/T-006/real_check.py"
    exit_code: 0
    result: gecti
    evidence: tester_evidence/04-real_check-T006.txt
  - name: "tester'in 41 kor birim testi (kendi bariyeri; K11 dort dil x surum/dosya adi/ModelMissingError)"
    cmd: "python -m pytest .agents/tasks/T-009/tester -q -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_evidence/07-tester-birim.txt
  - name: "sefin 119 + tester 41 birlikte (iki bariyer yan yana): 160"
    cmd: "python -m pytest tests/unit/ocr/test_rapid_engine.py .agents/tasks/T-009/tester -q -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_evidence/08-tester-birlikte-119.txt
  - name: "gercek model dort dil (ayri surec): JP 4/4, EN 4/4, KR 17 blok '.'=3 benzerlik 1.000 kelime 17/17, CHINESE dlg_JP 0/4, KR 327 ms, gercek yolda enum uyeleri + dosya adi dort dilde dogru"
    cmd: "python .agents/tasks/T-009/tester/t009_gercek_model.py"
    exit_code: 0
    result: gecti
    evidence: tester_evidence/09-gercek-model-dort-dil.txt
  - name: "KR OCR suresi varyansi: 3 surec x 3 tekrar, medyan 324-340 ms"
    cmd: "for i in 1 2 3; do python .agents/tasks/T-009/tester/t009_kr_sure.py; done"
    exit_code: 0
    result: gecti
    evidence: tester_evidence/10-kr-sure-varyans.txt
  - name: "mutant kontrolleri C0/C1 (ayna kurulumu dogru, olcu bosa ateslemiyor)"
    cmd: "python .agents/tasks/T-009/tester/t009_mutant_kiti.py --ayna <scratchpad>/ayna --yalniz C0,C1"
    exit_code: 0
    result: gecti
    evidence: tester_evidence/11a-mutant-kontroller.txt
  - name: "mutantlar M1-M4 (KR dosya v4 / JP dosya v5 / Det v5 / KR etiket v4): birim + tester + gercek model"
    cmd: "python .agents/tasks/T-009/tester/t009_mutant_kiti.py --ayna <scratchpad>/ayna --yalniz M1,M2,M3,M4"
    exit_code: 0
    result: gecti
    evidence: tester_evidence/11b-mutant-M1-M4.txt
  - name: "mutantlar M5-M7 (tam geri alma / EN dosya v5 / KR det ch)"
    cmd: "python .agents/tasks/T-009/tester/t009_mutant_kiti.py --ayna <scratchpad>/ayna --yalniz M5,M6,M7"
    exit_code: 0
    result: gecti
    evidence: tester_evidence/11c-mutant-M5-M7.txt
  - name: "mutant M8 (JP etiket v5, dosya v4): acik yolda sessiz v4, yalniz birim yakalar"
    cmd: "python .agents/tasks/T-009/tester/t009_mutant_kiti.py --ayna <scratchpad>/ayna --yalniz M8"
    exit_code: 0
    result: gecti
    evidence: tester_evidence/11d-mutant-M8.txt
  - name: "M7 ek olcum: ch det + KR v5 rec -> 4 satir blogu, bosluklar korunmus, 4/4 birebir (gozlem, kapsam disi)"
    cmd: "python - <ayna>/M7  (t009 ek olcum, metin basilmaz)"
    exit_code: 0
    result: gecti
    evidence: tester_evidence/12-M7-ch-det-kr-bosluk.txt
  - name: "kutuphane model haritasi (indirmeden): multi det v5 YOK, ch det v5 VAR, KR rec v5 = korean_PP-OCRv5_rec_mobile.onnx, JP rec v5 YOK"
    cmd: "PYTHONIOENCODING=utf-8 python - (InferSession.get_model_url x 14 nokta)"
    exit_code: 0
    result: gecti
    evidence: tester_evidence/13-kutuphane-model-haritasi-det-v5.txt
  - name: "diskteki korean v5/v4 rec + multi det SHA256 kutuphane haritasiyla ESLESIYOR"
    cmd: "python - (hashlib.sha256 x 3 dosya)"
    exit_code: 0
    result: gecti
    evidence: tester_evidence/14-korean-v5-sha256.txt
  - name: "regresyon: T-007 real_check TEMIZ (1 uyari: JP batch 506 ms, T-009'dan bagimsiz)"
    cmd: "python .agents/tasks/T-007/real_check.py"
    exit_code: 0
    result: gecti
    evidence: tester_evidence/15-real_check-T007.txt
  - name: "regresyon: T-008 real_check TEMIZ (KR 17 -> 4 blok, 2 segment, NMT bekliyor/dogu)"
    cmd: "python .agents/tasks/T-008/real_check.py"
    exit_code: 0
    result: gecti
    evidence: tester_evidence/16-real_check-T008.txt
  - name: "regresyon: tam takim 1444 passed, dusen yok (T-008 tur 2 commit'inden once)"
    cmd: "python -m pytest tests -q -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_evidence/17-pytest-tam-takim.txt
  - name: "regresyon: tam takim 1444 passed, dusen yok (T-008 tur 2 commit'i ef397e3 sonrasi)"
    cmd: "python -m pytest tests -q -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_evidence/17b-pytest-tam-takim-T008tur2-sonrasi.txt
  - name: "T-006 tester_A kiti: 1 bayat (test_a5_k11_dort_dil_alti_anahtar_birebir[korean]), 105 gecti"
    cmd: "python -m pytest .agents/tasks/T-006/tester_A -q -p no:cacheprovider"
    exit_code: 1
    result: gecti
    evidence: tester_evidence/05-T006-testerA-bayat.txt
  - name: "T-006 tester_B kiti: 4 bayat (b3, b5 x2, b6), 44 gecti; dordu de KOREAN v5 dosya adi"
    cmd: "python -m pytest .agents/tasks/T-006/tester_B -q -p no:cacheprovider"
    exit_code: 1
    result: gecti
    evidence: tester_evidence/06-T006-testerB-bayat.txt
  - name: "T-006 tester_B mutant kiti: 4 ikame hedefi (M04, M05, M06, M08) mevcut kaynakta yok (delivery 2 diyor)"
    cmd: "python - (mutant_kiti.py AST: her _y(eski, ...) icin eski in kaynak)"
    exit_code: 0
    result: gecti
    evidence: tester_evidence/20-T006-testerB-mutant-kiti-ikame-noktalari.txt
  - name: "T-006 tester_B mutant kiti M04'te SystemExit ile duruyor (kit tumden bloke)"
    cmd: "python .agents/tasks/T-006/tester_B/mutant_kiti.py M04"
    exit_code: 1
    result: gecti
    evidence: tester_evidence/21-T006-testerB-kiti-M04-bayat.txt
  - name: "tester_A yeniden nisan denemesi (kopya): YALNIZ dosya adi v5 -> [korean] yine duser (ORTAK ocr_version Rec icin v4)"
    cmd: "cd <scratchpad>/t006A_nisan && python -m pytest .agents/tasks/T-006/tester_A -q"
    exit_code: 1
    result: gecti
    evidence: tester_evidence/22-T006-testerA-yalniz-dosya-adi-nisan.txt
  - name: "tester_B yeniden nisan denemesi (kopya): YALNIZ DOSYALAR[KOREAN] v5 -> 48/48"
    cmd: "cd <scratchpad>/t006B_nisan && python -m pytest .agents/tasks/T-006/tester_B -q"
    exit_code: 0
    result: gecti
    evidence: tester_evidence/23-T006-testerB-yalniz-dosya-adi-nisan.txt
  - name: "mypy test dosyasi: 1 hata (satir 321 unused-ignore) -- T-009 ONCESI de var (a618a1a satir 310), kabul komutu degil"
    cmd: "python -m mypy --strict --explicit-package-bases tests/unit/ocr/test_rapid_engine.py  (+ ayni komut a618a1a kopyasinda)"
    exit_code: 1
    result: gecti
    evidence: tester_evidence/18b-mypy-test-dosyasi-T009-oncesi.txt
  - name: "mypy tester dosyalari temiz"
    cmd: "python -m mypy --strict --explicit-package-bases .agents/tasks/T-009/tester/test_t009_k11_tablosu.py .agents/tasks/T-009/tester/conftest.py"
    exit_code: 0
    result: gecti
    evidence: tester_evidence/19-mypy-tester.txt
blocking_issues: []
---

# T-009 tur 1 — kör tester (tek mercek: K11 tablosu · gerçek model · regresyon): **ONAY**

Ürünü bozan ölçülmüş sınıf yok. Beş kabul komutu benim elimde de exit 0; iki gerçek kapı TEMİZ; 41 kör test + 160 birlikte; 8 mutant + 2 kontrol aynada; T-006/T-007/T-008 kapıları ve 1444'lük tam takım düşen yok. Aşağıda ölçülen olgular, delivery.md'ye iki düzeltme ve şefe yükümlülük önerileri.

**Körlük notu.** Şefin talimatıyla `delivery.md` okundu, ama **1–3 ve 5 numaralı bölümlerin tüm ölçümleri bittikten sonra**; oradaki iddialar (olcum-1 tablosu, bayat test listesi) benim mutant/kit sonuçlarımla *sonradan* karşılaştırıldı. Sonuçlar §4'te.

## 1 · K11 tablosu dört dilde (sahte fabrika, kendi bariyerim) — 41 test, hepsi yeşil

Referanslar bağımsız kanaldan (packet K1 + olgular K4/K5 + T-006 packet K11 + kütüphane çözücüsü, kanıt 13). Ölçülenler (`tester_evidence/07`):

| Ölçü | JP | KR | ZH | EN |
|---|---|---|---|---|
| `Det.ocr_version` (açık yol **ve** indirme yolu, iki nokta) | v4 | v4 | v4 | v4 |
| `Rec.ocr_version` (açık yol **ve** indirme yolu) | v4 | **v5** | v4 | v4 |
| `beklenen_model_dosyalari` + `*.model_path` tam yol | v3 det / v4 rec | v3 det / **v5 rec** | v4/v4 | v4/v4 |
| boş dizin → `ModelMissingError`: det+rec adı mesajda, başka dilin adı yok, v4 KR adı yok, fabrika 0 çağrı, `__cause__ None` | ✓ | ✓ | ✓ | ✓ |
| yalnız rec / yalnız det eksik → mesajda yalnız o ad | ✓ | ✓ | ✓ | ✓ |

Ek: v5 kümesi rec'te tam `{korean}`, det'te boş · KR dizinde yalnız v4 varsa düşülmez, v5 sonradan gelince **aynı motor** kurulur · v4 **ve** v5 birlikte varsa v5 seçilir (gerçek makine durumu) · kaynakta/docstring'de `korean_PP-OCRv4` adı yok · iki tablo yapısal olarak tam (her dil bir kez, 4'lü/3'lü) · dosya adındaki sürüm ile `Rec.ocr_version` etiketi dört dilde tutarlı · sahte fabrikayla dört dil × iki yol kütüphaneyi yüklemiyor (bariyer sayaçlı, pozitif kontrol `match="K1 bariyeri"`).

## 2 · Gerçek modelle dört dil (ayrı süreç, `tester_evidence/09`, `10`)

JP **4/4** · EN **4/4** · KR **17 blok, `.`=3, benzerlik 1.000, kelime 17/17 (nokta dahil birebir), noktalı üç blok tam olarak üç cümle sonu** · CHINESE modeli `dlg_JP`'de **0/4** (K2 pozitif kontrolü hâlâ ateşliyor) · KR OCR medyan **327 ms** (3 süreç × 3 tekrar: 324–340; bütçe 400).

**G6 — gerçek yolda enum yakalama (birim testlerin göremediği katman):** `rapidocr.RapidOCR` sarılarak `_varsayilan_fabrika`'nın kütüphaneye verdiği `params` yakalandı: KR `Rec.ocr_version is OCRVersion.PPOCRV5`, diğer üçü `PPOCRV4`; `Det` dördünde `PPOCRV4`; `Rec.model_path` dosya adı dört dilde tabloyla aynı. String→enum çevirisi v5 için de çalışıyor.

Dürüstlük notu: bu betiğin **ilk** koşumu 437 ms verdi (makinede %52 dış CPU yükü — T-008 tur 2 eşzamanlı koşuyordu) ve G6'da benim anahtar hatam vardı (`str(LangRec.X)`); düzeltip yeniden koştum, ilk çıktı diskte **yok** (üzerine yazıldı). 437 tek gözlem, nedeni ölçülmedi; ardından 10 ölçümün hepsi 324–340. Bütçe payı ~%15 — dış yük altında aşılabilir, ihlal değil, kayıt.

Bütünlük (kanıt 14): diskteki `korean_PP-OCRv5_rec_mobile.onnx` SHA256'sı kütüphanenin model haritasındakiyle **eşleşiyor** (v4 ve multi det de).

## 3 · Mutantlar (ayna: depo kopyası, gerçek dosyaya dokunulmadı; `tester_evidence/11a–11d`)

Her mutant için üç ölçü: (a) şefin 119 birim testi, (b) benim 41'im, (c) gerçek model dört dil. C0 (değişiklik yok) → 119/41 yeşil, aynadan yüklendiği kanıtlı; C1 (yalnız yorum) → yeşil.

| # | Mutant | (a) 119 | (b) 41 | (c) gerçek model |
|---|---|---|---|---|
| M1 | KR **dosya** v4, etiket v5 | X 7 | X 14 | **DÜŞER**: `.`=0, 1123 ms, nokta taşıyan 3 kelime yitik (14/17) — kapı ateşliyor |
| M2 | JP dosya v5 (**diskte yok**) | X 58 | X 10 | **`ModelMissingError`** (`__cause__` yok, kütüphane çağrılmadı) — sessiz DEĞİL |
| M3 | `Det.ocr_version` v5 (her dil) | X 8 | X 10 | **SESSİZ**: JP 4/4, EN 4/4, KR 17/`.`=3; açık `Det.model_path` v3/v4 dosyayı yüklüyor |
| M4 | KR **etiket** v4, dosya v5 | X 4 | X 5 | **SESSİZ v5**: `.`=3, 17/17, 338 ms — implementer'ın iddiası doğrulandı |
| M5 | KR dosya v4 **ve** etiket v4 (tam geri alma) | X 7 | X 15 | DÜŞER (`.`=0, 1177 ms) |
| M6 | EN dosya v5 (`en_PP-OCRv5` **diskte var**) | X 5 | X 9 | **SESSİZ**: EN 4/4 ile v5 koşuyor — gerçek kapı göremez |
| M7 | KR det dosyası `ch` | X 6 | X 10 | KR **4 blok**, `.`=3 (T-009 kapısı 17 blok ister → düşer); bkz. §6 gözlem |
| M8 | JP etiket v5, dosya v4 | X 3 | X 4 | **SESSİZ v4**: 4/4 — implementer'ın F ölçümüyle aynı |

Okuma: ürün yolunda (`allow_download=False`) belirleyici olan **yalnız `_MODEL_DOSYALARI`**; `Det/Rec.ocr_version` etiketleri **inert** (M3, M4, M8 gerçek kapıdan geçiyor). Etiketler için tek bekçi birim testler — hem şefin K11 testleri hem benimkiler her üçünü yakalıyor. M6 ayrı bir sınıf: dosya adı tablosu **diskte var olan** bir dosyaya kayarsa (EN v5 gibi) gerçek kapı 4/4 ile geçer; yine yalnız birim test yakalar. Kütüphane haritası (kanıt 13): `multi` det v5 **yok** → M3 indirme yolunda JP/KR için `ValueError`→`OcrError`, ama `ch` det v5 **var** → ZH/EN'de sessizce v5 det inerdi `[ÖLÇÜLMÜYOR]` (ağ). Bunlar hata değil; §7 yükümlülük.

## 4 · Bayatlayan T-006 tester testleri — delivery'ye iki düzeltme

Kendi koşumum (`05`, `06`): tester_A **1** düşen, tester_B **4** düşen — implementer'ın listesiyle aynı 5 test, beşi de `ModelMissingError: korean_PP-OCRv5_rec_mobile.onnx` ya da `DOSYALAR[KOREAN]` eşitliği (gerçekten bayat, başka bir şey değil). Ama:

**Düzeltme 1 — tester_A'nın testi iki noktada bayat, bir değil.** Kopyada yalnız dosya adını v5'e çevirdim (`22`): `[korean]` yine düşüyor — `AssertionError: ('korean', 'Rec', 'ocr_version')`. `ORTAK = {..., "ocr_version": "PP-OCRv4"}` Det **ve** Rec için döngüde uygulanıyor. Yeniden nişan: `MODEL_ADLARI["korean"]` rec → v5 **ve** `ORTAK`'tan `ocr_version`'ı çıkarıp `Det` sabit v4 / `Rec` dil→sürüm sözlüğü.

**Düzeltme 2 — tester_B mutant kitinde 4 ikame hedefi bayat, 2 değil** (`20`): M04 ve M05 (`_DIL_TABLOSU` JAPAN/KOREAN 3'lü satırları — artık 4'lü), M06 (`_OCR_SURUMU` → `_TESPIT_SURUMU`), M08 (KOREAN v4 dosya satırı). Kit `count(eski) != 1` → `SystemExit`; **M04'te duruyor, tümü bloke** (`21`). `r2_mutant_kiti.py` etkilenmiyor (0/0). Yeniden nişan: dört `_y(eski, ...)` hedefini mevcut satırlara taşımak; M08'in yeni'si `japan_PP-OCRv4_rec_mobile.onnx` kalabilir (diskte var, sessiz yanlış model sınıfı korunur).

tester_B'nin 4 testi tek satırla (`DOSYALAR[KOREAN]` v5) **48/48** (`23`). Hiçbir T-006 dosyasına yazmadım; öneriler şefe.

## 5 · Regresyon

T-006 real_check 16/16 (KR **1.000**; EN 364 ms uyarısı T-009 öncesi de vardı) · T-007 real_check TEMİZ (JP batch 506 ms uyarısı, NMT — T-009 dışı) · T-008 real_check TEMİZ (KR 17→4 blok, 2 segment, NMT bekliyor/doğu) · tam takım **1444 passed / 0 failed**, hem T-008 tur 2 commit'i (`ef397e3`) öncesi hem sonrası · `git status --short -- src/ocr/rapid_engine.py tests/unit/ocr/test_rapid_engine.py` **boş** · mypy `rapid_engine.py` 0 · test dosyasında 1 `unused-ignore` (satır 321) — `a618a1a` kopyasında da aynı hata (satır 310), T-009'un eklemediği satır, kabul komutu değil (`18b`).

## 6 · Gözlem (kapsam dışı, hata değil; şefe açık kalem önerisi)

M7 ek ölçümü (`12`): **`ch` det + KR v5 rec**, `dlg_KR`'de **4 satır bloğu**, her blokta boşluklar korunmuş (1/4/4/4 boşluk = beklenen kelime sayısı−1), dört satır **boşluklu birebir**, `.`=3, güven 0.985–0.997, ~314 ms. T-006 KRT Y3'ün "`ch` det Korece boşluklarını yitirir" bulgusu **v4 rec ile** ölçülmüştü; v5 rec ile bu fixture'da tutmuyor. Sonucu: KR'de `multi` det'in 17 kelime kutusu + T-008 birleştirme yerine `ch` det'in satır kutuları olabilir. **Tek fixture, tek ölçüm** — menü fixture'ları (T-008 4b/4c) ve küçük yazı ölçülmeden tabloya yazılmaz; T-009 kapsamı dışında, kayıt.

## 7 · Şefe yükümlülük önerileri (karara işlenmeli, §4.6/2 damgasıyla)

1. **`Det/Rec.ocr_version` etiketleri ürün yolunda `[ÖLÇÜLMÜYOR]`** — gerçek kapı M3/M4/M8'i göremez; bekçi yalnız `test_k11_*` + `test_k11_t009_*` (docstring bunu JP için söylüyor, Det için söylemiyor). Karar bunu adlandırsın.
2. **Dosya adı tablosunun "diskte var olan yanlış dosyaya" kayması `[ÖLÇÜLMÜYOR]` gerçek kapıda** (M6 EN v5, tester_B'nin M08 JP dosyası KR'ye) — yalnız birim test yakalar.
3. KR bütçe 400 ms'nin payı ~%15 (324–340 ölçüldü); eşzamanlı yük altında aşılabilir. Kapı tek başına koşulmalı ya da pay genişletilmeli — şefin kararı.
4. T-006 tester kitleri §4'teki nişanla güncellenmeli (5 test + 4 ikame hedefi), yoksa kapalı görevin mutant kiti sessizce ölü kalır.

## Dosyalar

- Testler: `.agents/tasks/T-009/tester/` — `conftest.py` (kendi bariyer, `match="K1 bariyeri"`), `test_t009_k11_tablosu.py` (41), `t009_gercek_model.py`, `t009_kr_sure.py`, `t009_ayna_sonda.py`, `t009_mutant_kiti.py`.
- Kanıtlar: `.agents/tasks/T-009/tester_evidence/01–23`.
- Yazılmayan: `src/`, `tests/`, `real_check.py`, `packet.md`, T-006 dizinleri. `git commit` yok. Metin basılmadı.
