---
task: T-006
role: implementer
round: 2
status: tamamlandi
files_written:
  - src/ocr/rapid_engine.py
  - tests/unit/ocr/test_rapid_engine.py
  - .agents/tasks/T-006/evidence/mypy-tur2.txt
  - .agents/tasks/T-006/evidence/pytest-tur2.txt
  - .agents/tasks/T-006/evidence/real_check-tur2.txt
  - .agents/tasks/T-006/evidence/cov-tur2.txt
  - .agents/tasks/T-006/evidence/pytest-tum-tur2.txt
  - .agents/tasks/T-006/evidence/mutant-kiti-tur2.py
  - .agents/tasks/T-006/evidence/mutant-ayirt-etme-tur2.txt
  - .agents/tasks/T-006/evidence/tdd-kirmizi-tur2.txt
  - .agents/tasks/T-006/evidence/olcum-6-close-satiri-head.txt
  - .agents/tasks/T-006/evidence/pytest-cp1254-tur2.txt
  - .agents/tasks/T-006/delivery.md
commands:
  - cmd: "python -m mypy --strict --explicit-package-bases src/ocr/rapid_engine.py"
    exit_code: 0
    evidence: evidence/mypy-tur2.txt
  - cmd: "python -m pytest tests/unit/ocr/test_rapid_engine.py -q"
    exit_code: 0
    evidence: evidence/pytest-tur2.txt
  - cmd: "python .agents/tasks/T-006/real_check.py"
    exit_code: 0
    evidence: evidence/real_check-tur2.txt
  - cmd: "python -m pytest tests/unit/ocr/test_rapid_engine.py -q --cov=src.ocr.rapid_engine --cov-fail-under=90 --cov-report=term-missing"
    exit_code: 0
    evidence: evidence/cov-tur2.txt
  - cmd: "python -m pytest tests -q"
    exit_code: 0
    evidence: evidence/pytest-tum-tur2.txt
  - cmd: "python .agents/tasks/T-006/evidence/mutant-kiti-tur2.py"
    exit_code: 0
    evidence: evidence/mutant-ayirt-etme-tur2.txt
contract_change_request: false
known_gaps:
  - "[T2-1 -- K7 OLCUSU DAVRANISA KANCALANDI] Yeni testler (`test_k7_soguk_motor_hicbir_kanala_metin_yazmaz`, `test_k7_sicak_motor_kutuphane_logger_i_acikken_metin_yazmaz`): iki nobetci (`NÖBETÇİ-7f3a` Latin, `長老-9c1e` CJK) tasiyan sahte taniyiciyla TEK `recognize`; (1) `capfd.readouterr()` out == '' VE err == '' (sifir bayt); (2) `caplog.set_level(DEBUG)` (kok, logger belirtmeden) + `RapidOCR` logger'ina `caplog.handler` DOGRUDAN takili (propagate=False kor birakmasin) -> hicbir `record.getMessage()` nobetci icermez; (3) `warnings` kanali temiz. Iki nokta (4.6/7): SOGUK (kurulum + tanima ayni cagrida) ve SICAK (kurulum bitmis; `RapidOCR` logger'i uygulama debug modu gibi SONRADAN DEBUG'a acilmis -- motor seviyeyi yalniz kurulumda ceker). Iki nokta ZORUNLU: `RapidOCR` logger'ina `.info` yazan mutant (M-D = tester M28b) yalniz sicak noktada gorunur, cunku soguk cagrida motor kurulumdan sonra seviyeyi ERROR'a ceker (K7'nin istedigi davranis). Pozitif kontrol (4.6/10): `OcrEngine`i uygulayan 7 test-ici sahte motor (stdout / stderr / os.write(1) / sys.__stderr__ tamponlu / kok logger debug / RapidOCR logger info+propagate=False / warnings.warn) AYNI olcu fonksiyonundan gecirilince 7/7 `AssertionError` (`test_k7_pozitif_kontrol_kanal_olcusu_atesliyor`); negatif kontrol: sozlesmenin `FakeOcrEngine`i olcuden gecer (yanlis pozitif yok). Yazilan nobetci `capfd`/`caplog`/`catch_warnings` tarafindan yutulur, konsola ULASMAZ; `evidence/pytest-cp1254-tur2.txt` PYTHONIOENCODING YOKKEN (stdout cp1254) 110 passed gosterir. AST ikincil (`test_k7_ast_yazma_cagrisi_ve_log_yayimi_sifir`): `print`, `sys.stdout.write`, `sys.stderr.write`, `os.write` dordu de 0; ayrica `sys.std*`/`sys.__std*__` erisimi 0 ve `.debug/.info/.warning/.warn/.error/.critical/.exception/.log` yayimi 0 -- K7'nin lafzindan SERT: modulde hicbir log yayimi yok (docstring 'logging cagrisi yok, yalniz setLevel' zaten boyle diyordu); sayacin kor olmadigi parca-kodla gosterildi (`test_k7_ast_pozitif_kontrol_sayac_hepsini_gorur`)."
  - "[T2-1 ITIRAZ/SAPMA -- `capsys` yerine `capfd`; OLCUME UYULDU] Sef karari `capsys` diyor. `capsys` yalniz `sys.stdout/sys.stderr` NESNELERINI degistirir; `os.write(1, ...)` ve `sys.__stderr__.write(...)` ondan gecmez. `capfd` dosya tanimlayicisini (fd 1/2) yakalar ve `sys.std*`i de tamponsuz kopyayla degistirir -- `capsys`in ust kumesi. Olculdu: M-F (`os.write(1, blok.text)`) ve M-K (`sys.__stderr__.write(blok.text)`) `capfd` ile davranis testinde yakalaniyor (`mutant-ayirt-etme-tur2.txt`). Ek ders: `sys.__stderr__` satir tamponludur; newline'siz yazim fd'ye inmeden olcum penceresi kapaniyordu (ilk kosumda M-K'yi yalniz AST yakaladi). Cozum: olcum penceresinin iki ucunda `sys.__stdout__/__stderr__.flush()` (`_ozgun_akislari_bosalt`) -- olcu tampona degil davranisa bagli. Ayni sinif `warnings` kanalinda: `recwarn` fixture'i `simplefilter('default')` kurar, ayni konumdan ikinci uyariyi `__warningregistry__` bastirir, sicak nokta kor kaliyordu; olcu kendi `catch_warnings(record=True)` + `simplefilter('always')` blogunu kullanir. Her ikisi de mutant kitiyle yeniden uretildi (M-G iki noktada da yakalaniyor)."
  - "[T2-2 -- close() TANIYICIYI BIRAKIR; src DAVRANIS DEGISIKLIGI GEREKMEDI] `evidence/olcum-6-close-satiri-head.txt`: HEAD (`19222f9`, tur 1 teslimi) `close()` icinde `self._taniyici = None` ZATEN var (satir 666). Sef karari 'bir satirlik src degisikligi ister' diyor; olculdu, satir yerinde -- tester-B'nin M32'si bu satiri SILEN mutanttir ve tur 1 testleri onu ayirt edemiyordu. Tur 2'de eklenen sey OLCU: `test_k10_close_taniyiciyi_gercekten_birakir_weakref` -- fabrikanin dondurdugu taniyiciya `weakref.ref`; pozitif kontrol `close()` ONCESI `gc.collect()` sonrasi ref CANLI (motor tutuyor; aksi halde olcu bos donerdi), `close()` + `gc.collect()` sonrasi `ref() is None`; sonra `recognize` -> `OcrError`, fabrika sayaci hala 1; ikinci `close()` sessiz. M-E (satir silindi) yakalaniyor, C-1 (close icinde sira degisimi) kaciyor. `src`te yalniz docstring degisti (`close()` ve modul K10 bolumu)."
  - "[K6 (b) -- FABRIKA HATASINDA YENIDEN DENEME VAR; ACIKCA YAZILDI] Kurulum (fabrika) istisna verirse motor ornegi TUTMAZ (`self._taniyici` None kalir) ve `_kapali` DEGISMEZ; bir sonraki `recognize` cagrisi `parametreler()` + fabrikayi YENIDEN cagirir. Yani: otomatik (motor ici) yeniden deneme YOK, cagiran-tetiklemeli yeniden deneme VAR. Olcu: `test_k6_fabrika_hatasindan_sonra_yeniden_denenebilir` (ilk cagri `OcrError`, hata kaldirilinca ikinci cagri basarili, fabrika sayaci 2). Tester-B B5 bunu olctu, paket sessizdi; simdi modul docstring'i K10 bolumunde ve burada acikca yazili. Bu davranisin sonucu: `ModelMissingError`/`OcrError` alan cagiran ayni motor ornegini atmak zorunda degil; dosya yerine konunca ayni ornek calisir."
  - "[ÖLÇÜLMÜYOR -- `_varsayilan_fabrika` `isinstance(cikti, RapidOCROutput)` dali] Damga docstring'e eklendi (`test_k6_varsayilan_fabrika_isinstance_dali_olculmuyor_damgali` damgayi olcer). Neden olculmuyor: birim testte kutuphane yuklenmez (K1 bariyeri); `real_check.py`nin uc fixture'i uc dilde de `RapidOCROutput` donduruyor, `TextDetOutput` gibi baska bir tipin gercek tetikleyicisi bilinmiyor. Motorun genel 'taniyici sozlesme hatasi oldugu gibi gecer' yolu sahte taniyiciyla olculuyor (`test_k6_taniyici_sozlesme_hatasi_oldugu_gibi_gecer`)."
  - "[AYIRT ETME OLCUMU -- tur 2 kiti, `evidence/mutant-kiti-tur2.py` -> `mutant-ayirt-etme-tur2.txt`] Ayna agacinda 11 mutant + 3 davranis-esdeger kontrol, HER BIRI iki test dosyasiyla ayri kosuldu: TUR1 = `git show HEAD:tests/unit/ocr/test_rapid_engine.py` (95 test), TUR2 = calisma kopyasi (110 test). Sonuc: M-A `sys.stdout.write(blok.text)` [M25b] · M-B `sys.stderr.write` · M-C kok logger `suflor.ocr` debug [M28c] · M-D `RapidOCR` logger info [M28b] · M-E close birakmaz [M32] · M-F `os.write(1)` · M-G `warnings.warn` · M-I `getLogger(__name__).log()` · M-J kurulumda `sys.stdout.write(str(params))` (OCR metni degil, sifir-bayt ihlali) · M-K `sys.__stderr__.write` -> 10'u TUR1'den KACTI, TUR2'de YAKALANDI; M-H `print` iki turda da yakalandi (tur 1 AST'si de goruyor, beklenen). C-1 close sira degisimi · C-2 `setLevel(logging.ERROR)` -> `setLevel(40)` · C-3 recognize sonucu yerel degiskenden donuyor -> ikisinden de KACTI (yanlis pozitif yok). Kit TEMIZ, exit 0. TDD kirmizi: `evidence/tdd-kirmizi-tur2.txt` (M-A + M-E uygulanmis motorda 4 yeni test DUSER)."
  - "[TEST HIJYENI] `RapidOCR` logger'i global durumdur; sahte fabrikanin `kurulumda` kancasi kutuphane gibi INFO + propagate=False kurar. `kutuphane_logger_geri_al` fixture'i seviye/propagate/handler'lari test sonunda geri alir; `_k7_kanal_olcusu` taktigi `caplog.handler`i `finally`de kaldirir. Var olan 95 test silinmedi, zayiflatilmadi (tur 1 K7 testleri duruyor; yeni testler EK). Yeni `# pragma: no cover` eklenmedi; kapsam %98.94 (188 ifade / 2 eksik, tur 1 ile ayni satirlar 359 ve 368: yapisal olarak erisilemez `ValueError`lar)."
  - "[TUR 1 ITIRAZLARININ DURUMU] ITIRAZ-1 (real_check [3] KOREAN kova bolunmesi) ve ITIRAZ-2 ([6a] `y<0` saglanamaz): sef kapiyi duzeltmis; tur 2'de `real_check.py` exit 0, 16/16 ok ([3] 0.971 >= 0.95; [6a] `x<0` olcuyor). Bu ajan `real_check.py`ye dokunmadi. ITIRAZ-3 (K6/K11 canli cozucu vs K1 bariyeri -> sabit ad tablosu + string params + fabrikada enum donusumu) ve ITIRAZ-4 (cls modeli silinmisse `allow_download=False` altinda kutuphane indirir, [ÖLÇÜLMÜYOR]) tur 1'deki gibi gecerli; davranis degismedi."
  - "[TUR 1 KAYITLARI -- HALA GECERLI, ozet] K2 `language` zorunlu/keyword-only/varsayilan yok · K3 `threads` [1, cpu_count], None -> min(8, cpu), bool/float/str `TypeError`, np.int64 duz int · K4 bbox floor/ceil + rect kaydirma, `type is int`, dejenere/tasan cokgen oldugu gibi · K5 `Global.text_score=0.0`, metin degistirilmez, `boxes=None` -> `[]`, kutusuz metin -> `OcrError` · K6 acik `model_path` / `allow_download=True`'da `Global.model_root_dir`=model_dir (KARAR), bozuk cikti 18 vaka `OcrError`, hata metni blok metni tasimaz · K8 preset params'a girmez, damga docstring'de · K9 sure tutulmaz, real_check #5 raporlar (JAPAN 183 ms / ENGLISH 232 ms / KOREAN 678 ms 17 kutu) · K10 tembel, tek ornek, close idempotent, baglam yoneticisi degil · K11 dil tablosu string, fabrikada enum. Ayrintili gerekceler HEAD'deki tur 1 `delivery.md`de (`git show 19222f9:.agents/tasks/T-006/delivery.md`)."
  - "KAPSAM DISI (bloke etmeyen): thread-safe degil (tasarim 5.5); `frame.image` C-contiguous ve `image.shape`/`rect.w/h` tutarliligi denetlenmez; gercek `DownloadFileException` yolu [ÖLÇÜLMÜYOR]; `git commit` ATILMADI."
---

# T-006 teslim -- tur 2

## Ne degisti

* `tests/unit/ocr/test_rapid_engine.py` -- 95 -> **110 test** (+15):
  * K7 davranis olcusu: `_k7_kanal_olcusu` (capfd sifir bayt + kok logger
    DEBUG/`RapidOCR` dogrudan handler + warnings), **soguk** ve **sicak** nokta.
  * 7 pozitif kontrol (nobetciyi bir kanala yazan sahte motorlar -> olcu
    DUSER) + 1 negatif kontrol (`FakeOcrEngine` gecer).
  * AST ikincil: `print`/`sys.stdout.write`/`sys.stderr.write`/`os.write` 0,
    `sys.std*` erisimi 0, log yayimi 0 + sayac pozitif kontrolu.
  * K10 weakref: `close()` sonrasi taniyici olu; kapali motor + bozuk kare
    sirasi.
  * K6 damga testi (`_varsayilan_fabrika` `[ÖLÇÜLMÜYOR]`).
* `src/ocr/rapid_engine.py` -- **yalniz docstring**: K7 bolumu (kanal-bagimsiz
  degismez + yeni olcu), K10 bolumu (birakma + kurulum hatasinda yeniden deneme),
  `close()` docstring'i, `_varsayilan_fabrika` `isinstance` dali `[ÖLÇÜLMÜYOR]`.
  `close()` icindeki `self._taniyici = None` HEAD'de zaten vardi
  (`evidence/olcum-6-close-satiri-head.txt`); davranis degismedi.

## Bes komut

| # | komut | exit | sonuc | kanit |
|---|---|---|---|---|
| 1 | mypy --strict | 0 | temiz | `evidence/mypy-tur2.txt` |
| 2 | pytest birim | 0 | 110 passed | `evidence/pytest-tur2.txt` |
| 3 | real_check.py | 0 | 16/16 ok, TEMIZ | `evidence/real_check-tur2.txt` |
| 4 | coverage >= 90 | 0 | %98.94 | `evidence/cov-tur2.txt` |
| 5 | pytest tum takim | 0 | 1100 passed (1085 + 15) | `evidence/pytest-tum-tur2.txt` |

Ek: mutant kiti tur 2 exit 0 (`evidence/mutant-ayirt-etme-tur2.txt`), TDD
kirmizi (`evidence/tdd-kirmizi-tur2.txt`), cp1254 kosumu 110 passed
(`evidence/pytest-cp1254-tur2.txt`).

## Ayirt etme tablosu (TUR1 = HEAD test dosyasi, TUR2 = bu teslim)

| mutant | ne | TUR1 | TUR2 |
|---|---|---|---|
| M-A | `sys.stdout.write(blok.text)` [M25b] | KACTI | **YAKALANDI** (soguk, sicak, AST) |
| M-B | `sys.stderr.write(blok.text)` | KACTI | **YAKALANDI** (soguk, sicak, AST) |
| M-C | `getLogger("suflor.ocr").debug(metin)` [M28c] | KACTI | **YAKALANDI** (soguk, sicak, AST) |
| M-D | `getLogger("RapidOCR").info(metin)` [M28b] | KACTI | **YAKALANDI** (sicak, AST) |
| M-E | `close()` `_taniyici` birakmaz [M32] | KACTI | **YAKALANDI** (weakref) |
| M-F | `os.write(1, ...)` | KACTI | **YAKALANDI** (soguk, sicak, AST) |
| M-G | `warnings.warn(metin)` | KACTI | **YAKALANDI** (soguk, sicak, AST) |
| M-H | `print(blok.text)` | YAKALANDI | YAKALANDI |
| M-I | `getLogger(__name__).log(DEBUG, metin)` | KACTI | **YAKALANDI** (soguk, sicak, AST) |
| M-J | kurulumda `sys.stdout.write(str(params))` | KACTI | **YAKALANDI** (soguk, AST) |
| M-K | `sys.__stderr__.write(blok.text)` | KACTI | **YAKALANDI** (soguk, sicak, AST) |
| C-1 | `close()` sira degisimi (esdeger) | KACTI | KACTI |
| C-2 | `setLevel(logging.ERROR)` -> `setLevel(40)` (esdeger) | KACTI | KACTI |
| C-3 | sonuc yerel degiskenden donuyor (esdeger) | KACTI | KACTI |

## Sefe notlar

1. `capsys` yerine `capfd` (ust kume; `os.write`/`sys.__stderr__` de gorunur) --
   gerekce ve olcum `known_gaps` T2-1 ITIRAZ/SAPMA kaleminde.
2. T2-2'nin "bir satirlik src degisikligi" HEAD'de zaten vardi; eklenen sey olcu.
3. AST testi K7'nin lafzindan sert: modulde HICBIR log yayimi yok (yalniz
   `setLevel`). Ileride motor icine kasitli bir log (metinsiz) eklenirse bu test
   bilerek duser; o zaman test, yayimi 'metin tasimayan' olarak daraltilmali.
