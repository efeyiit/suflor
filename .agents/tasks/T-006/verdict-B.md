---
task: T-006
role: tester
round: 2
decision: onay
checks:
  - name: "taban 1 -- mypy --strict temiz (cp1254 konsol, PYTHONIOENCODING yok)"
    cmd: "python -m mypy --strict --explicit-package-bases src/ocr/rapid_engine.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-taban-1-mypy.txt
  - name: "taban 2 -- birim testleri 110 passed (cp1254)"
    cmd: "python -m pytest tests/unit/ocr/test_rapid_engine.py -q -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-taban-2-pytest.txt
  - name: "taban 3 -- real_check 16/16 TEMIZ, stdout dosyaya yonlendirilmis (cp1254), PYTHONIOENCODING YOK -- tur 1'de burada cokuyordu (S1 kapandi)"
    cmd: "python .agents/tasks/T-006/real_check.py > r2-taban-3-real_check-cp1254.txt 2>&1"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-taban-3-real_check-cp1254.txt
  - name: "taban 4 -- kapsam %98.94 (188 ifade, eksik 359/368)"
    cmd: "python -m pytest tests/unit/ocr/test_rapid_engine.py -q -p no:cacheprovider --cov=src.ocr.rapid_engine --cov-fail-under=90 --cov-report=term-missing"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-taban-4-kapsam.txt
  - name: "taban 5 -- tam takim 1100 passed"
    cmd: "python -m pytest tests -q -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-taban-5-tum-takim.txt
  - name: "src farki yalniz docstring (19222f9 vs HEAD, docstring'siz AST esit); close() govdesi tur 1'de de _taniyici=None; tur 1 kitinin 51 yama hedefi guncel src'de tekil"
    cmd: "python - (betik kanit dosyasinin basinda)"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-ast-esitligi-ve-yama-hedefleri.txt
  - name: "B2-4 -- tur 1 mutant kiti regresyonu: 47 davranis mutanti 47/47 YAKALANDI (tur 1: 43), M25b/M28b/M28c/M32 -> [.X.XX]; 4 kontrol 4/4 KACTI"
    cmd: "TESTER_B_SCRATCH=<scratch>/kit_tur1 PYTHONIOENCODING=utf-8 python .agents/tasks/T-006/tester_B/mutant_kiti.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-B1-tur1-kiti-regresyon.txt
  - name: "B2-1a -- kacis yollari kiti: 21 mutant x 5 kapi, kapilar cp1254 altinda (PYTHONIOENCODING SILINEREK); bes kapidan kacan bulgu adayi R04/R05 (handler .stream'e dogrudan yazma), davranis olcusunun yakaladigi kontrol YOK"
    cmd: "TESTER_B_SCRATCH=<scratch>/kit_r2 PYTHONIOENCODING=utf-8 python .agents/tasks/T-006/tester_B/r2_mutant_kiti.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-B2-1a-kacis-yollari-kiti.txt
  - name: "B2-1b/B2-2c -- mercek B tur 2 testleri (10): teslim olcusu dosyadan yuklenip GERCEK motor sinifi + kacis sahteleriyle kosuldu; R04/R05 kacis sebebi ve keskinlestirmenin ayirt etme gucu olculdu"
    cmd: "PYTHONIOENCODING=utf-8 python -m pytest .agents/tasks/T-006/tester_B/test_mercek_B_r2.py -v -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-B2-1b-mercekB-r2-testleri.txt
  - name: "B2-2a -- AST cagri grafigi: _k7_kanal_olcusu TEK tanim, dort cagiran (gercek motor x2, 7 sahte, FakeOcrEngine), govdede tip dali yok, m uzerinde yalniz .recognize"
    cmd: "PYTHONIOENCODING=utf-8 python .agents/tasks/T-006/tester_B/r2_b2_2_cagri_grafigi.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-B2-2a-ast-cagri-grafigi.txt
  - name: "B2-2b -- calisma zamani izi: 10 cagri, 1 kod nesnesi; 7 sahte 7 BEKLENEN kanal mesajiyla dusuyor; RapidOCR'da test sonrasi handler kalan test YOK"
    cmd: "PYTHONPATH=.agents/tasks/T-006/tester_B TB_IZ_CIKTI=<dosya> python -m pytest tests/unit/ocr/test_rapid_engine.py -q -p no:cacheprovider -p r2_izleme_plugin"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-B2-2b-calisma-zamani-izi.txt
  - name: "B2-3 -- sira/capture bicimleri: ters, 5 rastgele tohum, K7-once, K7-sona, -s, --capture=sys, tee-sys -> hepsi 110 passed; konsola sizan nobetci 0; tur 2 K7/K10 testleri tek basina da gecer"
    cmd: "PYTHONPATH=.agents/tasks/T-006/tester_B TB_SIRA=<ters|rastgele:N|k7once|k7sona> python -m pytest tests/unit/ocr/test_rapid_engine.py -q -p no:cacheprovider -p r2_sira_plugin -p r2_izleme_plugin ; ayrica -s / --capture=sys / --capture=tee-sys"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-B2-3a-sira-ve-capture-bicimleri.txt
  - name: "B2-4 -- tur 1 mercek B testleri (38) guncel koda karsi: 38 passed"
    cmd: "PYTHONIOENCODING=utf-8 python -m pytest .agents/tasks/T-006/tester_B -v -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-B2-4a-mercekB-38-regresyon.txt
  - name: "B2-4 -- totoloji/sahte-yesil AST taramasi, 110 testli dosya: 65 fonksiyon; assert'siz 0, sabit 0, cok-ifadeli raises 0; yeni testlerde bayrak yok"
    cmd: "PYTHONIOENCODING=utf-8 python .agents/tasks/T-006/tester_B/b2_totoloji_tarama.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-B2-4b-totoloji-tarama-110.txt
  - name: "tur 1 isaretlerinin yeniden nisani (S1 kapandi; Y2/Y3 kapandi; S2/S3/S4/Y1/Y4 acik, bloke etmez)"
    cmd: "python - (betik kanit dosyasinin basinda)"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-tur1-isaretleri-yeniden-nisan.txt
  - name: "AST ikincil kapisinin ad-kancasi kirilganligi (bilgi): math.log / x.error yanlis alarm; getattr(sys,'stdout') ve print takma adi gorunmez -- davranis olcusu asil kapi (R16 [.XXXX])"
    cmd: "python - (betik kanit dosyasinin basinda)"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-ast-sayac-kirilganligi.txt
  - name: "sahiplik: git status --short -- src tests BOS (ayna agaci kullanildi)"
    cmd: "git status --short -- src tests .agents/tasks/T-006/real_check.py tests/unit/ocr/conftest.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-git-status-src-tests.txt
blocking_issues: []
---

# T-006 · Tester-B · mercek B (test kalitesi, K1 bariyeri, ömür, loglama) · tur 2

**Karar: ONAY.** Tur 1'in ret gerekçesi kapandı: K7 ölçüsü artık **davranışı** kancalıyor. Beş kapıdan geçen ve ürünü bozan **ve** `recognize` içinde makul bir kod yolu olan sınıf **bulamadım**. Kalan boşluklar keskinlik sınıfı; hepsi ölçüldü, adlandırıldı ve ucuz keskinleştirmeleri ayırt etme gücüyle birlikte aşağıda. Bütün sayılar bu makinede koşuldu; ham çıktılar `tester_B_evidence/r2-*` altında. `src`, `tests`, `real_check.py`, `conftest.py`'ye yazılmadı (`r2-git-status-src-tests.txt`). Mutasyonlar iki ayrı ayna ağacında (`kit_tur1/`, `kit_r2/`).

Not (dürüstlük): bu turun `r2-taban-*`, `r2-B1-*`, `r2-ast-esitligi-*` dosyaları ve `r2_mutant_kiti.py` taslağı oturuma başladığımda **zaten vardı** (05:30–05:50 damgalı, aynı rolün kesilmiş bir önceki oturumu). Hiçbirine güvenmedim: **hepsini yeniden koştum ve üzerine yazdım** (07:38+ damgalı); kit taslağını iki mutant (R17, R19) ve kuru-koşum kipiyle genişlettim.

## 0 · Şefin tabanı — birebir, cp1254 altında (PYTHONIOENCODING yok)

| kapı | şef | ben |
|---|---|---|
| mypy | 0 | 0 |
| birim | 110 | 110 |
| real_check | 16/16, cp1254'te de | **16/16, stdout dosyaya yönlendirilmiş cp1254, exit 0** (tur 1'de exit 1 idi — Ş1 kapandı) |
| kapsam | %99 | %98.94, eksik 359/368 (tur 1 ile aynı iki yapısal `ValueError`) |
| tam takım | 1100 | 1100 |
| kitim M25b/M28b/M28c/M32 | `[.X.XX]` | `[.X.XX]` — düşen testler `test_k7_soguk_*`, `test_k7_sicak_*` (+AST), M32 → weakref testi |

`src` farkı 19222f9→HEAD: docstring'siz AST **eşit**; değişen yalnız modül, `_varsayilan_fabrika` ve `close` docstring'leri. `close()` gövdesi tur 1'de de `_taniyici = None` içeriyordu — implementer'ın T2-2 notu doğru; eklenen şey ölçü.

## B2-1 · Ölçü değişmezi mi kancalıyor? — 21 kaçış yolu × 5 kapı (`r2-B2-1a`)

Kit, tur 1 kitinin altyapısıyla ama kapıları **`PYTHONIOENCODING` silinerek** (cp1254) koşar — Ş1 düzeltmesi her mutantta 5 kapı × 21 kez yeniden sınandı, taban 5/5 yeşil. `beklenen` sütunu koşumdan **önce** yazdığım tahmindir.

| # | motora eklenen | üründe ne olur | `recognize` içinde makul yol mu | 5 kapı | yakalayan | sınıf |
|---|---|---|---|---|---|---|
| R01 | `sys.__stdout__.write(m)` (newline yok) | cp1254'te `UnicodeEncodeError`; pythonw'da `None.write` | evet (özgün akışa "debug" yazımı) | `XXXXX` | soğuk+sıcak (fd), AST, **mypy** (`Optional`), real_check (cp1254 çöküşü) | yakalandı |
| R02 | `os.write(2, m)` | stderr'e metin | evet | `.X.XX` | soğuk+sıcak, AST | yakalandı |
| R12 | `sys.stdout.buffer.write(bytes)` | stdout'a metin | evet | `.X.XX` | soğuk+sıcak, AST | yakalandı |
| **R16** | `getattr(sys,'stdout').write(m)` | = M25b | evet | `.XXXX` | **yalnız davranış** (soğuk+sıcak) + real_check cp1254 | yakalandı — **AST'yi atlatan M25b davranış ölçüsüne takılıyor: ölçü adı değil davranışı kancalıyor** |
| R17 | `RapidOCR` logger'ına **ERROR** ile metin | motor ERROR'a çekse de geçer → kütüphane StreamHandler'ı ile stderr'e | evet (makul geliştirici hatası) | `.X.XX` | soğuk+sıcak (doğrudan handler), tur 1 caplog testi, AST | yakalandı — seviye-bağımsız |
| R07 / R07b | alt süreç `cmd /c echo m` / `python -c` stdout | çocuk süreç miras fd 1'e yazar | zor (ama olur) | `.X.XX` | soğuk+sıcak (capfd fd'yi görür) | yakalandı |
| R09b | ayrı thread'den yaz + `join` | stdout'a metin | zor | `.X.XX` | soğuk+sıcak, AST | yakalandı |
| **R04** | kök logger handler'larının `.stream`ine doğrudan `write` | uygulama kök logger'a FileHandler kurduysa OCR metni **log dosyasına** | **hayır** — `for h in logger.handlers: h.stream.write(...)` bir debug print değil, ölçüyü atlatmak için kurulmuş yol | `.....` | — | **kaçtı** — bulgu adayı; ürüne erişilebilir ama makul yol değil |
| **R05** | `RapidOCR` handler'larının `.stream`ine doğrudan `write` | gerçek kütüphane `StreamHandler(stderr)` kurar → stderr'e metin; cp1254'te `UnicodeEncodeError`, pythonw'da `None.write` | **hayır** (aynı gerekçe) | `.....` | — | **kaçtı** — bulgu adayı; sebebi ölçüldü (aşağıda) |
| R08 | `atexit.register(print, m)` | süreç sonunda metin | hayır | `.....` | — | karakterizasyon: **zaman penceresi** |
| R09 | `threading.Timer(0.3, print, [m])` | 300 ms sonra metin | hayır | `.....` | — | karakterizasyon: zaman penceresi |
| R10 | **boş** karede `sys.stderr.write('bos kare')` | metinsiz; pythonw'da `None.write` → boş karede çöker | evet | `.X.XX` | **yalnız AST** | davranış ölçüsü boş kareyi **koşmuyor** (girdi uzayı) |
| R10b | boş karede `open(2,'w',closefd=False).write` | pythonw'da fd 2 geçersiz → `OSError` | hayır (`open(2)` kurgusal) | `.....` | — | karakterizasyon: girdi uzayı; makul biçimleri (R10, `print`, `logger.warning`) AST yakalıyor |
| R11 | yalnız `puan > 0.95` iken yaz | gerçek yolda her yüksek puanlı blok | evet | `.XXXX` | AST + real_check (cp1254 çöküşü) | davranış ölçüsü nöbetçi puanları 0.9/0.4 ile koşuyor (girdi uzayı) |
| R13 | `logger.log(5, m)` (DEBUG altı) | uygulama seviye 5 açmaz; pratikte sessiz | hayır | `.X.XX` | AST | karakterizasyon |
| R14 | `close()` içinde stdout | değişmez `recognize` süresince | — | `.X.XX` | AST | kapsam dışı, AST yakalıyor |
| R19 | tanıma **hata** yolunda `traceback.print_exc()` | tanıyıcı istisnasında stderr'e iz (OCR metni yalnız istisna taşıyorsa) | evet (makul) | `.....` | — | karakterizasyon: girdi uzayı (hata yolu); makul biçimleri (`logger.exception`, `print`) AST yakalar |
| R03 | `print(m, file=devnull)` — **kontrol** | kanal yok | — | `.X.XX` | **yalnız AST** (`print` adı) | davranış ölçüsü **geçirdi** (doğru); AST ad-kancası yanlış alarm (ikincil kapı, kabul) |
| R03b | `open(devnull).write(m)` — **kontrol** | kanal yok | — | `.....` | — | **kaçtı — doğru** (yanlış pozitif yok) |
| R06 | `simplefilter('ignore')` + `warn(m)` — kontrol | üretimde de bastırılır | — | `.X.XX` | yalnız AST (`.warn`) | davranış ölçüsü geçirdi (doğru) |

**Kit özeti:** beş kapıdan kaçan bulgu adayı **R04, R05**; davranış ölçüsünün yakaladığı kontrol **yok**; tahminden sapan üçü de "beklenenden fazla yakalandı" (R01 mypy, R16/R11 real_check'in cp1254'te çökmesi — ölçü değil, ürün etkisinin kendisi).

**R04/R05 neden kaçıyor — ölçüldü (`r2-B2-1b`, 10/10):** ölçü üç şeyi görür: fd 1/2'ye inen bayt, `caplog.records`, `warnings` kaydı. Handler'ın `.stream`ine doğrudan yazmak kayıt üretmez; test bağlamında o stream `caplog.handler`'ın `StringIO`'sudur (fd'ye inmez). Teslimdeki `_kutuphane_gibi_kur` gerçek `rapidocr/utils/log.py`'nin **`StreamHandler()`'ını eklemiyor** (yalnız INFO + `propagate=False`). Ölçtüm: (a) teslim kurulumuyla R05 sahtesi ölçüden **geçer**, ama `caplog.text` nöbetçiyi **taşır**; (b) gerçek kütüphane gibi `StreamHandler()` eklenince **aynı ölçü, aynı sahte** `stderr'e … yazildi` ile **düşer**; (c) M28b sınıfı da o kurulumda iki kanaldan görünür. R04 için `caplog.text` aynı şekilde görüyor.

**Ölçülmeyen sınır (dürüst damga, `[ÖLÇÜLMÜYOR]`):** zaman penceresi dışı yazım (R08/R09), doğrudan dosya sistemi kanalı (mutant kurmadım — K7'nin lafzı stdout/stderr/logging/warnings), hata yolu (R19), boş kare (R10b), üçüncü-çağrı-sonrası yazım. Gerçek yolda bunların stdout/stderr'e inen kısmını tek şey görür: real_check'in **alt süreç bayt ölçüsü** (tur 1 Ş2 — hâlâ yok, şefin dosyası).

## B2-2 · Pozitif kontrol gerçek mi? — evet, aynı fonksiyon, aynı yol

**AST (`r2-B2-2a`):** `_k7_kanal_olcusu` **tek** tanım (satır 751); dört çağıran: soğuk (`motor(tmp_path, f)` = `RapidOcrEngine`), sıcak (`m` = `RapidOcrEngine`), pozitif kontrol (`sahte()` — 7 `OcrEngine` altsınıfı), negatif kontrol (`FakeOcrEngine`). Gövdede `isinstance`/`type(m)`/`RapidOcrEngine`/iç durum erişimi **0**; `m` üzerinde yapılan tek şey `m.recognize`. Dört assert: stdout `== ""`, stderr `== ""`, kayıtlarda nöbetçi yok, uyarılarda nöbetçi yok.

**Çalışma zamanı (`r2-B2-2b`):** fonksiyonu toplama sonrası sarmalayıp 110 testi koştum: **10 çağrı, 1 kod nesnesi** (`test_rapid_engine.py:751`). `RapidOcrEngine` ×2 → geçti (2 blok); 7 sahte → 7'si **beklenen** kanal mesajıyla düştü (stdout ×2, stderr ×2, log kaydı ×2, warnings ×1 — `pytest.raises(AssertionError)` `match`'siz olsa da yanlış sebepten düşen yok); `FakeOcrEngine` → geçti.

**Gerçek motor sınıfıyla pozitif kontrol (`r2-B2-1b`, src'ye dokunmadan):** `RapidOcrEngine` + fabrikadan enjekte edilen, kanala yazan **tanıyıcı**: stdout → `stdout'a` ile düşer; `os.write(2)` → `stderr'e`; `RapidOCR.error(m)` → `log kaydina`; sessiz tanıyıcı → geçer. Yani "sahteler farklı yoldan geçiyor" değil: ölçü gerçek motor sınıfında da ateşliyor. Tur 1 kitinin M25b/M28b/M28c satırları da bunu **src mutasyonuyla** gösteriyor (düşen: `test_k7_soguk_*`, `test_k7_sicak_*`).

## B2-3 · `capfd` yan etkileri — bulgu yok

* **caplog bozulmuyor:** kök-logger ve `RapidOCR`-logger pozitif kontrolleri capfd altında `nobetci bir log kaydina dustu` ile düşüyor; caplog'a dayanan tur 1 testleri her sırada geçiyor.
* **Handler sızıntısı yok:** her test **sonrasında** `RapidOCR` (level, propagate, handlers) kaydedildi (`r2-B2-2b` ve 8 sıra varyantı): handler kalan test **0**; `propagate` hep geri. `RapidOCR.level` oturum başı 0 → ilk `recognize` koşan testten sonra 40 ve öyle kalıyor — bu **motorun K7 davranışı** (kurulumdan sonra ERROR), test sızıntısı değil; tur 2 fixture'ı test-öncesi değere geri alıyor.
* **Sıra:** ters, `rastgele:{1,7,42,1234,99999}`, K7-önce, K7-sona → hepsi **110 passed**.
* **`-s`:** 110 passed, pytest'in toplam çıktısı **133 bayt** (110 nokta + özet), konsola sızan nöbetçi parçası **0** — pozitif kontrollerin yazdığı nöbetçi capfd'nin tmpfile'ında kalıyor. `--capture=sys` ve `tee-sys`: 110, sızıntı 0.
* Tur 2 K7/K10 testleri **tek başına** da geçiyor (8 seçim); ardışık soğuk→sıcak→pozitif 9/9.

## B2-4 · Regresyon — dördüncü kırık yok

* Tur 1 kiti 51 mutant: **47/47 davranış mutantı yakalandı** (tur 1: 43/47), kapı başına G1 0 · G2 47 · G3 9 · G4 47 · G5 47; **4/4 kontrol kaçtı**. Tur 1'de kaçan dördü: M25b/M28b/M28c → soğuk+sıcak (+AST), M32 → `assert <_tani …> is None` (weakref).
* 38 mercek B testim (tur 1): **38 passed**. Totoloji taraması 110 testli dosyada: 65 fonksiyon; assert'siz 0, sabit 0, çok-ifadeli `raises` 0; tek bayrak tur 1'deki `pytest.skip` (dağıtım yoksa) ve adında "gerçekten" geçen weakref testi (gc + weakref ile gerçekten ölçüyor; pozitif kontrolü var: close öncesi ref canlı).
* **Tur 1 işaretleri (`r2-tur1-isaretleri-yeniden-nisan.txt`):** Ş1 **kapandı** (real_check cp1254 exit 0). Y2 kapandı (yeniden deneme politikası docstring K10/K6 b + `test_k6_fabrika_hatasindan_sonra_yeniden_denenebilir`). Y3 kapandı (`_varsayilan_fabrika` docstring `[ÖLÇÜLMÜYOR]` + damga testi). Ş2 açık (real_check stdout/stderr bayt ölçüsü yok — B2-1'in zaman-penceresi/alt-süreç sınıfını gerçek yolda görecek tek şey). Ş3/Ş4 belge kalemleri, decision.md'de. Y1 belgelendi (docstring: "üst katman kararı"). Y4 damgalı (`[ÖLÇÜLMÜYOR]: ag kesmek`). Ş5: mypy tur 1 kitinde yine 0/47 — ama r2 kitinde R01'i yakaladı (`sys.__stdout__` `Optional`).

## B2-5 · Orantı — karar

Ret eşiği: *ürünü bozan **ve** üründe erişilebilir bir sınıf beş kapıdan geçiyor*. Beş kapıdan geçenler: R04/R05 (handler `.stream`'e doğrudan yazma — ürünü bozar, ama `recognize` içinde makul bir kod yolu değil; ölçüyü atlatmak için yazılmış üç satır), R08/R09 (gecikmeli yazım — makul değil), R10b/R19 (girdi uzayı — kurgusal biçimler; makul biçimleri AST yakalıyor), R03b (kontrol, doğru). Tur 1'in ret sınıfı (`sys.stdout.write(text)` — tek satırlık makul debug kalıntısı, her dolu karede çöküş) artık **üç yoldan** yakalanıyor ve AST'yi atlatan biçimi (R16) davranış ölçüsüne takılıyor. Kalan boşluk **keskinlik**; ürünü bozmuyor çünkü kod doğru (tur 1 B4: gerçek modelle 0/0 bayt) ve makul kusur biçimleri kapıda. Hakem çağrılacak bir anlaşmazlık yok.

## Keskinleştirme önerileri — bloke etmez, hepsi ölçüldü (`r2-B2-1b`)

1. **`_kutuphane_gibi_kur` gerçek kütüphaneyi tam taklit etsin:** `lg.addHandler(logging.StreamHandler())` (utils/log.py birebir). Etki: R05 sınıfı `stderr'e` ile yakalanır; M28b/R17 iki kanaldan görünür. Bir satır.
2. **`caplog.text` de nöbetçi taşımasın** (`assert n not in caplog.text`). Etki: R04 ve R05 pytest bağlamında yakalanır. Bir satır.
3. **Üçüncü nokta: boş kare** (`SahteCikti()` döndüren tanıyıcı ile `_k7_kanal_olcusu`). Ölçtüm: gerçek motor orada temiz geçer, boş karede yazan tanıyıcı `stderr'e` ile düşer. R10 sınıfı davranışla da yakalanır. Üç satır.
4. **Pozitif kontrolde `match=`** (`ids` → beklenen mesaj: stdout/os.write → `stdout'a`, stderr/`__stderr__` → `stderr'e`, logger'lar → `log kaydina`, warnings → `warnings kaydina`). Şu an 7/7 doğru sebepten düşüyor (ölçtüm), ama ölçü değişirse yanlış sebepten geçebilir.
5. **AST sayacı (bilgi):** `_yazma_sayaci` `.log/.error/.warn` **adını** sayar — `math.log(...)` ya da bir nesnenin `.error(...)`ı yanlış alarm verir (`r2-ast-sayac-kirilganligi.txt`); `getattr(sys,'stdout')` ve `_p = print` görünmez. İkincil kapı olarak kabul; yalnız `logging`'e bağlanan bir sayaç (ya da `Name` kökü `logging`/`getLogger` olan zincir) yanlış alarmı kapatır.
6. **Şef (Ş2, tur 1'den):** real_check'e alt-süreç stdout/stderr **bayt** ölçüsü — gerçek yolda zaman-penceresi/alt-süreç/hata-yolu sınıflarını görecek tek kapı; `b4_gercek_surec_sondasi.py`'nin A/B'si taşınabilir.

## Dosyalar

`tester_B/`: `r2_mutant_kiti.py` (21 kaçış yolu; tur 1 kit altyapısını yeniden kullanır, kapıları cp1254'te koşar, `TB_DRY=1` kuru koşum), `test_mercek_B_r2.py` (10 test: gerçek motor sınıfıyla pozitif kontrol, R04/R05 kaçış sebebi + keskinleştirme ayırt etme gücü, boş kare noktası), `r2_b2_2_cagri_grafigi.py` (AST), `r2_izleme_plugin.py` (çağrı izi + logger sızıntı izi), `r2_sira_plugin.py` (ters/rastgele/K7-önce/sona). `tester_B_evidence/r2-*`: taban 1–5, B1 regresyon, B2-1a/1b, B2-2a/2b, B2-3a, B2-4a/4b, AST eşitliği, tur 1 işaretleri, AST sayacı, git status. `tester_A/`, `tester_A_evidence/` **okunmadı**.
