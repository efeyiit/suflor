---
task: T-006
role: tester
round: 1
decision: ret
checks:
  - name: "taban 1 -- mypy --strict temiz"
    cmd: "python -m mypy --strict --explicit-package-bases src/ocr/rapid_engine.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/taban-1-mypy.txt
  - name: "taban 2 -- birim testleri (95 passed)"
    cmd: "python -m pytest tests/unit/ocr/test_rapid_engine.py -q -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/taban-2-pytest.txt
  - name: "taban 3 -- real_check, stdout dosyaya yonlendirilmis (cp1254): KAPI COKUYOR (UnicodeEncodeError, U+2248), motor kusuru degil"
    cmd: "python .agents/tasks/T-006/real_check.py > taban-3-real_check.txt 2>&1"
    exit_code: 1
    result: kaldi
    evidence: tester_B_evidence/taban-3-real_check.txt
  - name: "taban 3b -- real_check UTF-8 stdout ile: TEMIZ 16/16"
    cmd: "PYTHONIOENCODING=utf-8 python .agents/tasks/T-006/real_check.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/taban-3b-real_check-utf8.txt
  - name: "taban 4 -- kapsam %98.94 (188 ifade, eksik 337/346)"
    cmd: "python -m pytest tests/unit/ocr/test_rapid_engine.py -q -p no:cacheprovider --cov=src.ocr.rapid_engine --cov-fail-under=90 --cov-report=term-missing"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/taban-4-kapsam.txt
  - name: "taban 5 -- tam takim 1085 passed"
    cmd: "python -m pytest tests -q -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/taban-5-tum-takim.txt
  - name: "B1 -- mutant kiti: 47 davranis mutanti + 4 kontrol x 5 kapi; 4 mutant HICBIR kapida yakalanmadi (M25b, M28b, M28c, M32); kontrollerin hepsi kacti"
    cmd: "PYTHONIOENCODING=utf-8 python .agents/tasks/T-006/tester_B/mutant_kiti.py"
    exit_code: 0
    result: kaldi
    evidence: tester_B_evidence/B1-mutant-kiti.txt
  - name: "B1b -- mercek B testlerinin ayirt etme gucu: kacan 4 mutantin 4'u yakalaniyor, 4 kontrol kaciyor"
    cmd: "TESTER_B_SCRATCH=<ayri dizin> PYTHONIOENCODING=utf-8 python .agents/tasks/T-006/tester_B/mercekB_mutant_ayirt_etme.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/B1b-mercekB-ayirt-etme.txt
  - name: "B1c -- M25b'nin urun etkisi olculdu: cp1254'te UnicodeEncodeError, sys.stdout=None'da AttributeError"
    cmd: "python - < (tester_B_evidence/B1c-M25b-urun-etkisi.txt icindeki betik; ayna agaci)"
    exit_code: 0
    result: kaldi
    evidence: tester_B_evidence/B1c-M25b-urun-etkisi.txt
  - name: "B -- mercek B testleri (38 passed; kendi bariyeri altinda)"
    cmd: "PYTHONIOENCODING=utf-8 python -m pytest .agents/tasks/T-006/tester_B -v -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/B-mercek-testleri.txt
  - name: "B2 -- totoloji/sahte-yesil AST taramasi (56 fonksiyon / 95 ornek; assert'siz 0, sabit 0, cok-ifadeli raises 0)"
    cmd: "PYTHONIOENCODING=utf-8 python .agents/tasks/T-006/tester_B/b2_totoloji_tarama.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/B2-totoloji-tarama.txt
  - name: "B3 -- bariyer bes kosum biciminde olculdu (pytest tests / tek dosya / dizin / karisik / --noconftest)"
    cmd: "PYTHONPATH=.agents/tasks/T-006/tester_B TB_GOZLEM_CIKTI=... python -m pytest <hedef> -q -p no:cacheprovider -p tb_gozlem_plugin"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/B3-bariyer-kosum-bicimleri.txt
  - name: "B4 -- gercek model, ayri surec: import+yapim+recognize stdout 0 / stderr 0 bayt; cikti bicimi olculdu"
    cmd: "PYTHONIOENCODING=utf-8 python .agents/tasks/T-006/tester_B/b4_gercek_surec_sondasi.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/B4-gercek-surec-sondasi.txt
blocking_issues:
  - "K7 olcusu mekanizma adiyla kancali (print adi, .text/txts alt dizgisi, yalniz RapidOCR logger'i). Motora blok metnini yazdiran uc mutant (M25b sys.stdout.write, M28b RapidOCR logger INFO, M28c uygulama logger'i DEBUG) bes kabul kapisinin BESINDEN de geciyor. M25b'nin urun etkisi olculdu: cp1254 stdout'ta UnicodeEncodeError (ham), pencereli pakette (sys.stdout=None) her recognize AttributeError. Sefin esigi: 'urunu bozan mutant bes kapidan geciyor VE sinif uruende erisilebilir' -> ret. Duzeltme yalniz test dosyasinda (feedback-B.md, ayirt etme gucu olculdu: 4/4 yakaliyor, kontroller kaciyor)."
---

# T-006 · Tester-B · mercek B (test kalitesi, K1 bariyeri, ömür, loglama) · tur 1

**Karar: RET** — motor kodu doğru, **ölçü** bir ürün-bozan sınıfa kör. Düzeltme tek dosyada (`tests/unit/ocr/test_rapid_engine.py`), `feedback-B.md`'de tarifli ve ayırt etme gücü ölçüldü. Kök sebep paketin K7 ölçüsünde (şefin lafzı: "AST — `print` çağrısı 0; `logging` argümanlarında `.text`/`txts` yok; caplog `logger="RapidOCR"`") — implementer bunu birebir uyguladı; kusur lafızda.

Bütün sayılar bu makinede koşuldu; ham çıktılar `tester_B_evidence/` altında. `src`, `tests`, `real_check.py`, `conftest.py`'ye yazılmadı (`git status --short -- src tests` boş). Mutasyonlar scratchpad'deki ayna ağacında yapıldı.

## 0 · Şefin tabanı — birebir yeniden üretildi

| kapı | şef | ben |
|---|---|---|
| mypy | 0 | 0 (`taban-1`) |
| birim | 95 passed | 95 passed (`taban-2`) |
| real_check | TEMİZ 16/16 | **UTF-8 stdout ile** TEMİZ 16/16 (`taban-3b`); **cp1254'e yönlendirilince exit 1** — aşağıda Ş1 |
| kapsam | %99, 337/346 eksik | %98.94, 337/346 (`taban-4`) |
| tam takım | 1085 | 1085 (`taban-5`) |

## B1 · Mutant kiti — 47 davranış mutantı + 4 kontrol × 5 kapı

`tester_B/mutant_kiti.py`, ayna ağacı; taban 5/5 yeşil doğrulandıktan sonra koşuldu. Tam tablo `B1-mutant-kiti.txt` sonunda. Sınıflar şefin listesindeki gibi: K5 (5), K11 dört dilde ayrı ayrı + dosya tablosu (6), K3 (7), K4 (6), K6 (8), K7 (8), K10 (4), K1 (2), K2 (1), kontrol (4).

**Kapı başına yakalama (47 davranış mutantı):** mypy **0** · birim **43** · real_check **9** · kapsam 43 (= birim) · tam takım 43 (= birim). Yük taşıyan kapı birim testleri; real_check yalnız gerçek yola yansıyanları görüyor (M01/M02/M03/M03b K5, M08/M09 dosya tablosu, M16/M17 kaydırma, M19 hata sınıfı).

**Hiçbir kapının yakalamadığı 4 mutant:**

| # | mutant | üründe | mercek B testi |
|---|---|---|---|
| **M25b** | `recognize` sonunda `sys.stdout.write(bloklar[0].text)` | cp1254 stdout → `UnicodeEncodeError` (ham; **ölçüldü**, `B1c`); `sys.stdout=None` → `AttributeError` (**ölçüldü**) | X |
| **M28b** | `logging.getLogger("RapidOCR").info("blok %s", metin)` | uygulama o logger'ı açarsa metin stderr'e (propagate=False + StreamHandler) | X |
| **M28c** | `logging.getLogger("suflor.ocr").debug("blok %s", metin)` | kök DEBUG açılınca OCR metni log dosyasına (§6.7) | X |
| **M32** | `close()` `_taniyici = None` yapmaz | det+rec+cls oturumları close sonrası canlı (bellek); dışarıdan görünmez | X (weakref) |

Neden kaçıyorlar: `test_k7_ast_print_yok_logging_metin_yok` yalnız `print` **adını** sayıyor ve `logging` çağrısında `.text`/`txts` **alt dizgisini** arıyor (döngü değişkeni `metin` görünmez); `test_k7_nobetci_metin_loga_dusmez` `caplog.at_level(DEBUG, logger="RapidOCR")` ile yalnız o logger'ı açıyor — motor kurulumdan sonra onu ERROR'a çekiyor, kök/uygulama logger'ı ve stdout/stderr (`capsys` yok) gözlenmiyor. K10'da `close()`nun bıraktığı hiçbir testte ölçülmüyor (`recognize → OcrError` yeterli sanılıyor).

**Kontrol mutantları (4/4 kaçtı, yanlış pozitif yok):** `is`→`==`, `asarray`→`array`, tip ek açıklaması, sözlük anahtar sırası.

**Sınıf başına keskinlik (yakalanan):** K5 5/5 (dördü real_check'te de) · K11 lang_type/version/type dört dilde 4/4 yalnız birim (gerçek yolda `model_path` açık verildiği için bu anahtarlar **etkisiz**, bkz. Ş3) + dosya tablosu 2/2 birim+real · K3 7/7 · K4 6/6 (floor→round, ceil→floor, ters işaret, yalnız-x kaydırma, +1 piksel, ceil(max−min) — EGİK fixture ayrıştırıyor) · K6 8/8 (MME→OcrError, ContractViolation kaldırma ve sıra, `__cause__` düşürme, FNF sınıfı, TranslatorError sarma, allow_download, (h,w,4)) · K7 5/8 · K10 3/4 · K1 2/2 (modül düzeyi import, dizin çözümünde import) · K2 1/1.

**Kit notu (ölçüldü):** real_check cp1254'te çöktüğü için kit her kapıyı `PYTHONIOENCODING=utf-8` ile koşar; aksi hâlde 51 mutantın 51'i "real_check X" görünürdü (yanlış pozitif).

## B2 · Totoloji ve sahte-yeşil — bulgu yok, iki not

AST taraması (`B2-totoloji-tarama.txt`): 56 fonksiyon → 95 örnek; assert'siz **0**, sabit-doğru/kendine-eşit **0**, çok-ifadeli `pytest.raises` gövdesi **0**, `except` **1** (`pytest.skip` — dağıtım yoksa; bu makinede 0 skipped). Adında "gerçek" geçen test yok.

Sahte fabrika biçimi gerçekle **ölçülerek** eşleştirildi (`B4-…` [E]): gerçek çıktı `RapidOCROutput`, `boxes` ndarray float32 `(4,4,2)`, `txts` `tuple[str]`, `scores` `tuple[float]` (Python `float`, `type is float` True), boş kare (1200×400 gri **ve** 1×1) üç alan `None`. Implementer'ın `cikti()` aynı biçimi üretiyor. **Not 1:** kütüphanenin boşluk-only satırları elediği yolda (`main.py:181-189`, `filter_by_indices`) `txts`/`scores` **liste**, `boxes` fancy-index'li ndarray — sahte bunu hiç üretmiyor; motorun listeyi kabul ettiğini ben ölçtüm (`test_b2_bosluk_suzgeci_sonrasi_liste_bicimi_de_kabul`). **Not 2:** `test_k7_pozitif_kontrol_seviye_dusurulmezse_uyari_gecer` motora dokunmuyor (caplog'un çalıştığını gösteriyor); K7 ölçüsünün motor üzerinde ateşlediğini gösteren asıl kontrol M26 (WARNING'e çekme, yakalandı).

## B3 · K1 bariyeri — kaçış yolları ölçüldü

Kendi bariyerim `tester_B/tb_bariyer.py` (conftest import eder), sorguları kaydeder. Ölçümler (`B-mercek-testleri.txt`, `B3-bariyer-kosum-bicimleri.txt`):

| yol | sonuç |
|---|---|
| `importlib.import_module` (rapidocr, .main, .inference_engine.base, onnxruntime) | RuntimeError, `sys.modules`a girmez |
| `__import__("rapidocr")`, `__import__("onnxruntime.capi")` | RuntimeError |
| `importlib.util.find_spec` | RuntimeError |
| `spec_from_file_location(<paket>/__init__.py)` + `exec_module` | **RuntimeError** — bulucu atlanır ama `__init__` alt modül import eder, o import `meta_path`ten geçer (rapidocr ve onnxruntime ikisi de) |
| `sys.modules["rapidocr"] = ModuleType(...)` önceden dolu | `import rapidocr` **kaçar** (bulucu sorulmaz) — ama gerçek model yüklenmez; `rapidocr.main` yine kesilir. Conftest yüklenirken yasak kök `sys.modules`ta **yoktu** (ölçüldü, `ONCEDEN_YUKLU == ()`) |
| alt süreç | serbest (bariyer süreç-yerel; real_check'in bilerek kullandığı yol). Motor ve test dosyası AST'de `subprocess`/`spec_from_file_location`/`__import__`/`import_module`/`runpy`/`sys.modules[..]=` **kullanmıyor** |
| `pytest tests` (kökten) | capture/contracts toplanırken bariyer henüz yok (onlar kütüphaneye dokunmuyor); `test_rapid_engine.py` toplanmadan **önce** var; oturum sonu yasak kök yüklü değil, bariyer sayısı 1 |
| tek dosya / `tests/unit/ocr` / karışık sıra | hepsinde toplama öncesi bariyer var |
| `--noconftest tests/unit/ocr/test_rapid_engine.py` | bariyer **kurulmuyor**, 95 passed ve yasak kök **yine yüklenmiyor** — testler bariyersiz de kütüphaneye dokunmuyor |

Şefin pozitif kontrolü (`test_conftest_bariyer.py`) yalnız `import_module` yolunu sınıyor; `spec_from_file_location`/`__import__`/`find_spec`/alt süreç sınanmıyor (belgeleme bulgusu, ölçtüm — üçü de tutuyor, dördüncüsü tasarım gereği açık). Paket K1 metni "`sys.modules`a nöbetçi + `meta_path` sayaç" diyor; şefin conftest'i **yalnız** `meta_path` bulucu (sayaç yok, nöbetçi yok) — daha güçlü yol, ama paket metniyle uyuşmuyor (Ş4).

## B4 · K7 loglama — sahte ve gerçek

**Sahte, gerçek logger yapılandırmasıyla** (`RapidOCR`: INFO, `propagate=False`, StreamHandler — kütüphanenin `utils/log.py`sinin aynısı): kurulumdan sonra kök + `RapidOCR` + 7 olası logger DEBUG/INFO/WARNING/ERROR'a açılıp ikinci `recognize` koşuldu — caplog boş, `capsys` stdout/stderr boş (4 seviye). Pozitif kontrol: metni loglayan sahte tanıyıcıda hem caplog hem stderr nöbetçiyi görüyor. Motor fabrikadan sonra `RapidOCR`'u ERROR'a çekiyor (INFO'ya ve DEBUG'a sıfırlayan fabrikayla ölçüldü); boş karede kütüphanenin `warning("The text detection result is empty")` stderr'e düşmüyor, seviye WARNING'e alınınca düşüyor (ölçü ateşliyor). Hata yolunda istisna zinciri, loglar ve stdout/stderr nöbetçi taşımıyor.

**Gerçek model, ayrı süreç, `PYTHONIOENCODING` verilmeden** (`B4-gercek-surec-sondasi.txt`): import + yapım → 0/0 bayt; + JP×2 (0,0 ve −2600,−50), 1200×400 gri, 1×1, KR fixture (JAPAN) → **stdout 0, stderr 0 bayt**; kök logger DEBUG'a açık uygulama modunda 333 bayt stderr — hepsi `PIL` (benim fixture yükleyicim), motor/kütüphane 0. `RapidOCR` logger'ı: ERROR, propagate False, `StreamHandler:INFO`. Logger envanteri: yalnız `RapidOCR` — küçük harf `rapidocr` ya da `RapidOCR.det` **yok** (ölçüldü). **Uygulama `RapidOCR` logger'ını kurulumdan sonra DEBUG'a açarsa** boş karede kütüphanenin WARNING'i stderr'e düşer (103 bayt, metinsiz) — motor seviyeyi yalnız kurulumda çekiyor (Y1 yükümlülüğü aşağıda).

## B5 · K10 ömür — bulgu M32 dışında yok

`close()`×2 sessiz, sonra `recognize`×3 → `OcrError`, fabrika sayacı 1 kalıyor; kurulmamış motorda close → sayaç 0. `close()` tanıyıcıyı **bırakıyor** (weakref, gc sonrası ölü) — teslimde doğru, ölçüsü yoktu (M32). Fabrika ilk çağrıda fırlatırsa: örnek tutulmuyor, her sonraki `recognize` yeniden deniyor (2., 3. çağrıda sayaç 2, 3), başarılı kurulumdan sonra tek örnek; `ModelMissingError` sonrası dosyalar diske konunca aynı motor kendini kuruyor. **Paket bu konuda sessiz** (K6'daki "yeniden deneme yok" (c) kare doğrulamasına ait) — docstring'le tutarlı, şef isterse pakete yazılmalı (Y2). Kurulum hatasından sonra `close()` → kapalı, fabrika yeniden çağrılmıyor. İki motor aynı fabrikayı paylaşınca durum karışmıyor (sayaç 2, params dil/threads'e göre ayrı, birinin close'u diğerini etkilemiyor, yalnız onun tanıyıcısı ölüyor). Tanıma sırasındaki kütüphane hatası örneği düşürmüyor (sonraki çağrı aynı tanıyıcıyla başarılı). Kapalı motorda bozuk kare → `OcrError` (belgelendiği gibi). `parametreler()` kapalılıkla ilgisiz (paket sessiz).

## B6 · Kapsam dürüstlüğü — bulgu yok

Eksik iki ifade `_dil_satiri` ve `beklenen_model_dosyalari`'ndaki "yapısal olarak erişilemez" `raise ValueError` — her enum üyesi tabloda, üye olmayan değer tabloya varmadan `OcrLanguage(...)`da patlıyor (ölçtüm); **pragma almamışlar** (dürüst: rapor eksik gösteriyor, gizlenmiyor). Tek `# pragma: no cover` `_varsayilan_fabrika` `def` satırında, gerekçeli (K1: bariyer altında koşamaz), gerçek yol real_check'te 4 dilde koşuyor. İçindeki iki dal hiçbir kapıda koşmuyor: `DownloadFileException → ModelMissingError` docstring'de `[ÖLÇÜLMÜYOR]` damgalı; `not isinstance(cikti, RapidOCROutput) → OcrError` damgasız — kütüphane kaynağını okudum, `TextDetOutput` dönüşü `rec_res.txts is None` gerektiriyor ve `TextRecognizer.__call__` boş olmayan kırpma listesinde `txts`'i hep tuple veriyor → pratikte erişilemez, savunma amaçlı (Y3: damga). Kapsam için yazılmış davranış ölçmeyen test bulamadım.

## Şefe bulgular (kapı) — Ş

- **Ş1 · real_check cp1254'te çöküyor.** Şefin düzelttiği `[6a]` mesajındaki `≈` (U+2248), `[3]/[8]`deki `≥`, `[7]`deki `→` cp1254'te yok; stdout dosyaya/boruya yönlendirilince Python konsol kodlamasını seçiyor → `[1]`den sonra `UnicodeEncodeError`, exit 1 (`taban-3`). Şef UTF-8 terminalde koştuğu için görmedi; KRT O4 `sys.stdout.reconfigure(encoding="utf-8")` önermişti. Kabul komutu #3 bu hâliyle makineye bağlı.
- **Ş2 · real_check stdout/stderr baytını ölçmüyor.** K7'nin gerçek-yol ölçüsü yok; `b4_gercek_surec_sondasi.py`'nin A/B farkı (0 bayt) real_check'e taşınabilir — M25b'yi gerçek yolda da yakalar.
- **Ş3 · K11'in `lang_type/ocr_version/model_type` anahtarları `allow_download=False` yolunda etkisiz.** `model_path` açık verilince kütüphane bu anahtarları model seçiminde kullanmıyor (M04–M07 real_check'te `.`; M08/M09 dosya tablosu `X`). Gerçek yolda K11'i taşıyan şey `_MODEL_DOSYALARI`; `allow_download=True` yolunda ise anahtarlar belirleyici ve o yol hiçbir kapıda koşmuyor (`[ÖLÇÜLMÜYOR]` olarak belgeli). Paketin "K11 tablosu real_check #1–#4 ile ölçülür" cümlesi yalnız dosya tablosu için doğru.
- **Ş4 · Paket K1 metni ile şefin conftest'i uyuşmuyor** (nöbetçi/sayaç yok; yalnız bulucu). Bulucu daha güçlü; metin güncellenmeli. Pozitif kontrol yalnız `import_module`.
- **Ş5 · mypy kapısı 47 mutantın 0'ını yakaladı** — beklenen (davranış mutantları tip-temiz); protokol uyum satırı `_uyum_fabrika` var. Bilgi.

## Adlandırılmış yükümlülükler (onaydan bağımsız, `[ÖLÇÜLMÜYOR]`)

- **Y1 (uygulama/entegrasyon):** motor `RapidOCR` logger seviyesini yalnız kurulumda çekiyor; uygulama o logger'ı sonradan açarsa kütüphane boş karede WARNING basar (metinsiz). Ya motor her `recognize`te yeniden çekmeli ya da uygulama logger yapılandırması bu adı dışlamalı — şef karar versin.
- **Y2 (paket):** kurulum hatasından sonra yeniden deneme politikası pakete yazılsın (bugün: örnek tutulmaz, her çağrı yeniden dener, otomatik tekrar yok).
- **Y3 (implementer, tur 2'de küçük):** `_varsayilan_fabrika` içindeki `isinstance` dalına docstring'de `[ÖLÇÜLMÜYOR]` damgası.
- **Y4 (tester sınıfı, ölçülmüyor):** `allow_download=True` gerçek indirme yolu ve `DownloadFileException` sınıflandırması (paket zaten damgalı).

## Dosyalar

`tester_B/`: `mutant_kiti.py` (51 mutant), `mercekB_mutant_ayirt_etme.py`, `test_mercek_B.py` (38 test), `conftest.py` + `tb_bariyer.py` (bağımsız bariyer), `tb_gozlem_plugin.py`, `b2_totoloji_tarama.py`, `b4_gercek_surec_sondasi.py`. `tester_B_evidence/`: taban-1…5, B1, B1b, B1c, B, B2, B3, B4. `feedback-B.md`: implementer için düzeltme + yeniden üretim.
