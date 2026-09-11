---
task: T-006
role: tester
round: 1
lens: "A — sözleşme uyumu ve sayısal doğruluk"
decision: onay
checks:
  - name: "taban: mypy --strict temiz"
    cmd: "python -m mypy --strict --explicit-package-bases src/ocr/rapid_engine.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/taban-mypy.txt
  - name: "taban: implementer birim testleri 95 passed"
    cmd: "python -m pytest tests/unit/ocr/test_rapid_engine.py -q"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/taban-pytest.txt
  - name: "taban: real_check gerçek model TEMİZ 16/16 (JAPAN 185 ms, ENGLISH 236 ms, KOREAN 685 ms/17 kutu, KR 0.971)"
    cmd: "python .agents/tasks/T-006/real_check.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/taban-real_check.txt
  - name: "taban: kapsam %98.94 (188 ifade, 2 eksik: 337, 346)"
    cmd: "python -m pytest tests/unit/ocr/test_rapid_engine.py -q --cov=src.ocr.rapid_engine --cov-fail-under=90 --cov-report=term-missing"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/taban-cov.txt
  - name: "taban: tam takım 1085 passed"
    cmd: "python -m pytest tests -q"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/taban-pytest-tum.txt
  - name: "tester-A: 106 kör test, kendi bariyeri altında tek başına (A0 pozitif kontrol dahil)"
    cmd: "python -m pytest .agents/tasks/T-006/tester_A -q -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/testerA-pytest.txt
  - name: "tester-A: şefin dizini + tester_A birlikte 329 passed (iki bariyer çakışmıyor)"
    cmd: "python -m pytest tests/unit/ocr .agents/tasks/T-006/tester_A -q -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/testerA-birlikte-pytest.txt
  - name: "tester-A mutant kiti: 17/17 yakalandı, davranış-eşdeğer kontrol kaçtı; 3 mutant implementer takımından kaçıp yalnız tester-A'da düştü"
    cmd: "python .agents/tasks/T-006/tester_A/mutant_kiti_A.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/mutant-A.txt
  - name: "A6/A4 gerçek model (ayrı süreç): küçük/büyük görüntü, bitişik-olmayan/salt-okunur dizi, çevrimdışı indirme yolu, gerçek oturum iş parçacığı, K11 keskinlik"
    cmd: "python .agents/tasks/T-006/tester_A/a6_gercek_model.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/a6-gercek-model.txt
  - name: "A6 takip: dört dilde allow_download=True + ağ KAPALI (K11 tablosu gerçek çözücüyle), süre/boyut ilişkisi"
    cmd: "python .agents/tasks/T-006/tester_A/a6b_takip.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/a6b-takip.txt
  - name: "A6 takip: dört dilde allow_download=False + ağ KAPALI -> kurulur (cls sha denetimi yerel)"
    cmd: "python .agents/tasks/T-006/tester_A/a6c_agsiz_false.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/a6c-agsiz-false.txt
blocking_issues: []
---

# T-006 · Tester-A (mercek A: sözleşme uyumu ve sayısal doğruluk) · tur 1 · **ONAY**

Şefin tabanı birebir yeniden üretildi (mypy 0 · 95 passed · real_check TEMİZ 16/16 · %98.94 · 1085 passed). Üstüne 106 kör test, 17+1 mutant ve 12 gerçek-model deneyi koştu. **Sözleşmeyi ihlal eden ya da ürünü bozan ölçülmüş bir sınıf bulunmadı.** Aşağıdaki bulguların hepsi *ölçü keskinliği* ya da *kayıt* niteliğindedir; hiçbiri ret eşiğini geçmez. Depoya yazılmadı: `git status --short -- src tests` boş.

## 1. Saldırı noktaları — ölçülen sonuç

| Nokta | Ölçü | Sonuç |
|---|---|---|
| **A1 K4 kutu matematiği** | tam sayı / `.5` / negatif / `-0.0` / tek nokta (tam sayı → `w=h=0`, kesirli → `w=h=1`) / yatay çizgi `h=0` / saat yönü ters + karışık köşe sırası / `float32(2600.0000001)==2600.0` / `float32(1199.9999)`→ceil 1200 / dtype ∈ {f32,f64,i64,i32,f16} / liste biçimli `boxes` / 2559.7→2560 sınırı | Hepsi `floor(min)`/`ceil(max)` lafzıyla birebir; dört alan **`type is int`**, `json.dumps(asdict(bbox))` geçer. `test_a1_*` (13 test). |
| **A2 kaydırma / frame alanları** | `rect=(-2600,-50)`, `(-1,-1, monitor_index=-1, dpi=1.25)`, `(2560,0, mi=1, dpi=2.0)`; üç nokta farkı; `rect.x/y/monitor_index` `np.int64`/`np.uint16`/`bool` | Kaydırma tam `rect.x/y`; `w/h` frame'den bağımsız; **`monitor_index=-1` (birleşim — `CaptureService._monitor_indeksi` bunu üretir) aynen geçiyor**; numpy/bool alan → `ContractViolation`, fabrika sayacı 0, `__cause__` None. `test_a2_*`. |
| **A3 K5 süzülmeme** | 13 puan tipi/değeri (`0.0, NaN, -0.1, 1.5, 0.123456789, np.float32/64/16, np.int64, 0, 1`); `""`, `" "`, `"\t\n"`, tam genişlik boşluk; 50 blok (17'si 0.0); `scores` ndarray; 8 uzunluk/None uyuşmazlığı | **Hiçbir blok kaybolmuyor, hiçbir yolda `float` dışı tip çıkmıyor, yuvarlama yok** (`0.123456789` aynen). Uyuşmazlık → `OcrError`, kısmi sonuç yok, mesajda blok metni yok. `test_a3_*`. |
| **A4 K6 taksonomi + `__cause__`** | 13 biçim-dışı görüntü (int32, uint16, bool, f64, 2/4 kanal, 0×0, 0×w, h×0, 4B, liste, bytes, None) · tanıyıcı 5 istisna sınıfı · fabrika FNF/ValueError/PermissionError/ModelMissingError · `KeyboardInterrupt` · kapalı motor · model yok + bozuk kare | Biçim-dışı → `ContractViolation`, sayaç 0, `__cause__` None, **`ModelMissingError`'ın önünde**. Tanıyıcı istisnası → `OcrError` `__cause__ is` özgün; FNF → `ModelMissingError` `__cause__` özgün; `BaseException` sarılmıyor. `test_a4_*`. |
| **A5 K3 aralık · K11 tablo** | `True/False/8.0/np.float64(8.0)/"8"/b"8"/4.5/complex/[8]/np.array(8)` → `TypeError`; `np.int64(8)`, `np.int32(4)`, `np.uint8(2)`, `IntEnum` → düz `int`; `0/-1/-8/np.int64(0)/2**63` → `ValueError`; `cpu_count=6` ile `np.int64(8)` → `ValueError`, `np.int64(6)` geçer; `cpu_count=2` ile `None`→2; yapımda dondurulan değer sonraki `cpu_count` değişiminden etkilenmiyor. Dört dil × altı anahtar bağımsız tabloyla birebir; diller arası det/rec ayrımı. | Hepsi geçti. Tek dili yanlış eşleyen mutant (MA-06 KOREAN det→ch) implementer'da `test_k11_dil_tablosu_alti_anahtar[korean]`, bende `test_a5_k11_dort_dil_alti_anahtar_birebir[korean]` **ve** `test_a5_k11_diller_arasi_det_ve_rec_ayrimi` ile düşüyor. |
| **A6 gerçek model** (ayrı süreç) | 300×80 14 px ve 10 px EN; 2560×1440 tek satır JP/EN 40 px; boş 2560×1440 | Bkz. §3. Sözleşmeye göre hepsi geçerli. |

## 2. Mutant kiti — ayırt etme gücü (`tester_A_evidence/mutant-A.txt`)

17 mutant **17/17 yakalandı**, davranış-eşdeğer kontrol (`zip(strict=True)`→`zip`) doğru biçimde **kaçtı**. Üç mutant implementer'ın 95 testinden **kaçıp yalnız tester-A'da düştü** — ürün doğru, ölçü keskinliği bulgusu (§4.6/4):

| Mutant | Ne yapar | impl 95 | tester-A 106 | Neden kaçtı |
|---|---|---|---|---|
| **MA-08** | `confidence = round(float(p), 2)` | **geçti** | düştü (`test_a3_puanlar_suzulmez_hepsi_float`, `…yuksek_hassasiyetli_puan_aynen`) | Fixture puanları hep ≤2 ondalık (`0.05/0.99/0.60/0.25/0.4/0.9`) |
| **MA-13** | `x0 = floor(noktalar[0,0])` (min yerine **ilk köşe**) | **geçti** | düştü (`test_a1_kose_sirasi_ters_ayni_kutu`) | `EGIK` fixture'ında ilk köşe zaten min-x (10.6); x ekseninde "min" ile "ilk köşe" ayrışmıyor (y'de ayrışıyor, x'te değil) |
| **MA-17** | tek noktalı çokgende `h+1` | **geçti** | düştü (`test_a1_tek_noktali_*`) | Dejenere fixture 4 köşeli; tek nokta yok |

## 3. Gerçek-model bulguları (rapor; ret değil) — `a6-gercek-model.txt`, `a6b-takip.txt`, `a6c-agsiz-false.txt`

**B1 · `[ÖLÇÜLMÜYOR]` denen iki yol ölçüldü ve geçiyor.** (D6) `requests.get` yamalanıp `allow_download=True` + boş `model_dir` → `ModelMissingError → DownloadFileException → ConnectionError` zinciri, dizin boş kalıyor (yarım dosya yok). (D7) Gerçek onnxruntime oturumu det **ve** rec'de `threads=4` → intra/inter 4/4, `threads=8` → 8/8 (iki nokta, §4.6/7); `text_score=0.0`, `use_cls=False` gerçek örnekte. Şef isterse damgaları kaldırıp `real_check`'e aynı yamayla ekleyebilir — ağ kesmeden ölçülebiliyor.

**B2 · K11 lafzı gerçek yolda YANLIŞ TABLOYU ölçüyor (şefe bulgu, §4.6/4-/7).** (D8) Açık `Det/Rec.model_path` varken `Rec.lang_type`'ı `ch`/`en`/`korean`, `Det.lang_type`'ı `ch` vermek çıktıyı **hiç değiştirmiyor** (JP fixture 4/4 kalıyor; sözlük ONNX'in içinde). Yani `allow_download=False` yolunda — `real_check`'in koştuğu tek yol — K11'in `lang_type` tablosu **etkisiz**, belirleyici olan `_MODEL_DOSYALARI` dosya-adı tablosu. Paketteki "`real_check` #1–#4 bu tabloyla geçer; #2 pozitif kontrolü **yalnız** bu tabloyla ateşler" cümlesi dosya tablosu için doğru, `lang_type` tablosu için değil: `_DIL_TABLOSU`'nu bozan bir mutant `real_check` 16/16'yı geçer, yalnız birim testte düşer. `lang_type` tablosunun gerçek ölçüsü **`allow_download=True` yolu**: (D10) dört dil, ağ KAPALI, `allow_download=True` → kütüphanenin kendi çözücüsü tabloyu yerel dosyaya çözüyor: JAPAN 4/4, ENGLISH 4/4, KOREAN 17 blok / 0.971, **CHINESE-on-JP 0/4 (pozitif kontrol bu yolda da ateşliyor)**. Öneri: `real_check`'e D10 biçiminde bir kontrol (dört dil, `allow_download=True`, `requests.get` yamalı) — K11'i mekanizma değil değişmez düzeyinde kancalar. Implementer'ın ITIRAZ-3 çözümü (sabit ad tablosu + string params + fabrikada enum dönüşümü) bu ölçümle **doğrulanmış** sayılır.

**B3 · K9 "süre kutu sayısına bağlı" eksik bir model** (D11, tek satır EN, 8 parçacık): 300×80 14 px **280 ms**, 600×160 246 ms, 1200×400 184 ms, 2560×1440 253 ms; 1200×400 **dört satırlık** fixture 247 ms. Yani tek kutulu küçük bir tooltip, dört kutulu diyalogdan **yavaş** — süre kutu sayısının yanında tespit ön işlemesinin ölçeklemesine de bağlı. Bütçe yalnız JP fixture'ına tanımlı olduğu için ihlal yok; ama tooltip/küçük bölge bütçesi konacaksa bu sayı bilinmeli.

**B4 · Küçük/büyük görüntü sözleşmeye uygun** (D1–D3): 300×80'de 14 px ve 10 px İngilizce **birebir** (1 blok, 0.966/0.974, kutu görüntü içinde, tipler düz); 2560×1440 tek satır EN birebir (0.992); JP 40 px msgothic 1 karakter hatalı (0.938; 28 px'te birebir) — model davranışı, sözleşme dışı. `rect.x=-2560` ile büyük görüntüde kutu `x=-2259` → görüntü-yerel 301 (çizim noktası 300). Boş 2560×1440 → `[]`, istisna yok.

**B5 · Bitişik olmayan / salt-okunur `uint8 (h,w,3)`** (D4): dilim görünümü, Fortran sırası, salt-okunur, **BGRA dilimi `[:,:,:3]`** — hepsi gerçek kütüphanede istisnasız 4/4. Motorun "bağlantılılık denetlenmez" boşluğu pratikte zararsız; motor bu dizileri kopyasız geçiriyor (`test_a4_bitisik_olmayan_*` sabitler). Aynalı görünüm 0/4 (beklenen, içerik aynalı).

**B6 · `allow_download=False` + ağ KAPALI dört dilde kuruluyor** (D12): cls sha256 denetimi yerel; dosya varken ağ gerekmiyor. ITIRAZ-4'ün "cls silinmişse indirir" deliğini ben ölçmedim (site-packages'a müdahale gerekir); implementer'ın `model_root_dir` ölçümü inandırıcı, açık kalem olarak kalsın.

## 4. Düşük bulgular — `known_gaps` yükümlülüğü

**D-A2 · `dpi_scale` düzleştirme asimetrisi.** Motor `rect.x/y/monitor_index` numpy ise `ContractViolation` veriyor ama **`dpi_scale`'i denetlemiyor**: `Rect(…, dpi_scale=np.float32(1.5))` → `bbox.dpi_scale` `np.float32`, `json.dumps(asdict(bbox))` **düşer** (`test_a2_rect_dpi_scale_np_float32_sizar_json_duser` sabitler). `CaptureService._kabul_ve_duzlestir_olcek` `float()` uyguladığı için üretimde erişilemez; ama implementer'ın KARAR gerekçesi ("numpy tipi toplama sızmasın") `dpi_scale` için de geçerli. Tur 2'de tek satır (`type(r.dpi_scale) is not float` → `ContractViolation`) ya da docstring'e "dpi_scale aynen, denetlenmez" — ikisi de kabul.

**D-A4a · `Frame.rect` `Rect` değilse çıplak `AttributeError`** (K6 taksonomisi dışında; fabrika çağrılmıyor). `test_a4_rect_rect_degilse_gozlem` sabitler. Üretimde erişilemez (`CaptureService` her zaman `Rect`). Belgelenir.

**D-A4b · Tanıyıcı kardeş `TranslatorError` (`CaptureError`) fırlatırsa aynen geçer** — `OcrEngine.Raises` listesinde yok. Yalnız enjekte sahteyle mümkün; gerçek tanıyıcı yalnız `OcrError` üretir. Belgelenir.

**D-A3 · `txts` numpy `<U` dizisiyse `text` `np.str_`** (`str` alt sınıfı; gerçek kütüphane `tuple[str]` verir, olcum-3 #6). Belgelenir.

## 5. Implementer'ın paket itirazları — bu mercekten görünüm

* **ITIRAZ-1/2 (real_check kova ve `y<0`)**: şef kapıyı düzeltmiş; güncel `real_check` 16/16 bende de geçti. Kapanmış.
* **ITIRAZ-3 (K6/K11 ↔ K1 çelişkisi → sabit tablo + string)**: B2/D10 ile **ölçülerek doğrulandı** — hem dosya tablosu (`allow_download=False`, 4 dil, D12) hem `lang_type` tablosu (`allow_download=True`, 4 dil, D10) gerçek çözücüyle doğru dosyaya çözülüyor. Ek: `lang_type` tablosu açık `model_path` yolunda etkisiz (B2) — şef paketin K11 ölçü cümlesini buna göre düzeltmeli.
* **ITIRAZ-4 (cls indirme deliği)**: ölçmedim; açık kalem.

## 6. Kapsam dışı / ölçülmedi

* Cls dosyası silinmiş durumda `allow_download=False` davranışı (site-packages müdahalesi).
* Thread-safety (tasarım 5.5 tek worker).
* Gerçek `DownloadFileException` **ağ gerçekten kesikken** — D6 `requests.get` yamasıyla ölçtü; gerçek soket kesintisi aynı istisna sınıfını (`requests.RequestException` alt sınıfı) üretir, mekanizma aynı.
