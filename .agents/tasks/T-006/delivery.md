---
task: T-006
role: implementer
round: 1
status: kismi
files_written:
  - src/ocr/rapid_engine.py
  - tests/unit/ocr/test_rapid_engine.py
  - .agents/tasks/T-006/evidence/mypy.txt
  - .agents/tasks/T-006/evidence/pytest.txt
  - .agents/tasks/T-006/evidence/real_check.txt
  - .agents/tasks/T-006/evidence/cov.txt
  - .agents/tasks/T-006/evidence/pytest-tum.txt
  - .agents/tasks/T-006/evidence/tdd-kirmizi.txt
  - .agents/tasks/T-006/evidence/olcum-1-bariyer-ve-model-dizini.py
  - .agents/tasks/T-006/evidence/olcum-1-bariyer-ve-model-dizini.txt
  - .agents/tasks/T-006/evidence/olcum-2-model-adlari-ve-enum.py
  - .agents/tasks/T-006/evidence/olcum-2-model-adlari-ve-enum.txt
  - .agents/tasks/T-006/evidence/olcum-3-gercek-motor-davranisi.py
  - .agents/tasks/T-006/evidence/olcum-3-gercek-motor-davranisi.txt
  - .agents/tasks/T-006/evidence/olcum-4-korece-benzerlik-teshis.py
  - .agents/tasks/T-006/evidence/olcum-4-korece-benzerlik-teshis.txt
  - .agents/tasks/T-006/evidence/olcum-5-real-check-6a-teshis.py
  - .agents/tasks/T-006/evidence/olcum-5-real-check-6a-teshis.txt
  - .agents/tasks/T-006/evidence/mutant-kiti.py
  - .agents/tasks/T-006/evidence/mutant-ayirt-etme.txt
  - .agents/tasks/T-006/delivery.md
commands:
  - cmd: "python -m mypy --strict --explicit-package-bases src/ocr/rapid_engine.py"
    exit_code: 0
    evidence: evidence/mypy.txt
  - cmd: "python -m pytest tests/unit/ocr/test_rapid_engine.py -q"
    exit_code: 0
    evidence: evidence/pytest.txt
  - cmd: "python .agents/tasks/T-006/real_check.py"
    exit_code: 1
    evidence: evidence/real_check.txt
  - cmd: "python -m pytest tests/unit/ocr/test_rapid_engine.py -q --cov=src.ocr.rapid_engine --cov-fail-under=90 --cov-report=term-missing"
    exit_code: 0
    evidence: evidence/cov.txt
  - cmd: "python -m pytest tests -q"
    exit_code: 0
    evidence: evidence/pytest-tum.txt
contract_change_request: false
known_gaps:
  - "[STATUS NEDEN kismi -- OKUNMASI GEREKEN KALEM] Bes kabul komutunun dordu exit 0; `real_check.py` exit 1 (2 IHLAL, 0 uyari). Iki ihlal de MOTORDA DEGIL KAPIDA olculdu ve her ikisi de ham ciktiyla yeniden uretildi (asagida [ITIRAZ-1] ve [ITIRAZ-2]). `real_check.py` sefe ait, bu ajan YAZMADI. 16 kontrolun 14'u `ok`: JAPAN 4/4, CHINESE-on-JP 0/4 (K2 pozitif kontrolu ATESLIYOR), ENGLISH 4/4, bbox iki nokta farki tam (-2600,-50), monitor_index her iki frame'de dogru, tum bbox alanlari `type is int`, JAPAN medyan 176 ms (butce 300), ENGLISH 240 ms (350), KOREAN 673 ms / 17 kutu = 40 ms/kutu (150), KR+JAPAN 17 blok / 8'i confidence<0.5 (K5 suzgec KAPALI kaniti), confidence tipi float, model yok -> ModelMissingError (__cause__ NoneType). Motor kodu her iki ihlalde de DOGRU davranisi veriyor; `status: tamamlandi` yazmadim cunku listelenen bir komut exit 1 -- sef kapiyi duzeltir ya da karar verir."
  - "[ITIRAZ-1 -- real_check [3] KOREAN benzerlik 0.932 < 0.95: KAPININ OKUMA SIRASI KOVASI BIR SATIRI BOLUYOR] Ham cikti `evidence/olcum-4-korece-benzerlik-teshis.txt` (METINSIZ teshis: yalniz geometri/puan/uzunluk/opcode). 17 kelime kutusunun dorduncu satirindaki bloklarin `bbox.y` degerleri 212, 213, 214, 215, 215; `okuma_sirasi` `round(y/25)` ile kovaliyor: 212/25=8.48 -> kova 8, 213/25=8.52 -> kova 9. Yani satirin bir kelimesi (idx 13) satirin ONUNE sirala niyor ve birlesik metin bozuluyor -> 0.932. AYNI 17 blok, kova `y//60` ile birlestirilince benzerlik 0.971 -- sefin olgular O5'te yazdigi sayinin TA KENDISI ('benzerlik 0.971, tek fark cumle sonu noktalari dusuyor'). Satir bazli teshis: kova 2 -> 1.000, kova 4 -> 0.970, kova 6 -> 0.966, kova 8 (tek blok, bolunen) -> 0.235, kova 9 -> 0.889. Motorun `bbox.y` hesabi K4'un lafzidir (`floor(min_y)`); baska bir y secimi de kova sinirina denk gelebilirdi -- kusur olcude: kelime kutulari icin 25 px'lik yuvarlama kovasi sinirda kararsiz (O6'nin dersi: 'cikti bicimi degistiginde karsilastirma bicimi de degismeli'). Onerim (sefin yetkisinde): `okuma_sirasi` satir kovasini satir yuksekligi olceginde (`y // 60` ya da merkez-y ile satir gruplama) kursun; ya da #3'u kelime-sira-bagimsiz olcsun (bosluksuz karakter cok-kumesi). Bu ajan `real_check.py`ye DOKUNMADI."
  - "[ITIRAZ-2 -- real_check [6a] 'ilk blok bbox.y < 0 olmali': FIXTURE ILE SAGLANAMAZ] Ham cikti `evidence/olcum-5-real-check-6a-teshis.txt`. JP fixture'inda ilk satirin cokgeni goruntu-yerel y=93'te basliyor (olcum-3 #6: `[[82,95],[229,93],[229,115],[82,116]]`, min_y=93). `Frame.rect=(-2600,-50)` ile y = 93 - 50 = 43 >= 0; bu kosul bu fixture'la HICBIR dogru uygulamada tutmaz. Pozitif kontrol (olcunun ateslenebildigi gosterildi, 4.6/10): ayni motor `rect.y=-93` -> y=0, `rect.y=-94` -> y=-1, `rect.y=-100` -> y=-7 -- motor y'yi sifira SABITLEMIYOR, kaydirma tam `rect.y` kadar. Ayni kosumda [6c] 'iki nokta farki == (-2600,-50)' `ok` -- K4'un asil degismezi bu ve saglaniyor. `x < 0` yarisi (-2518) da saglaniyor. Onerim: [6a] `y < 0` yerine `y == 93 + rect.y` (ya da yalniz `x < 0`) olcsun, ya da fixture ust kenara yakin bir satir tasisin."
  - "[ITIRAZ-3 -- K6/K11 ile K1 CELISIYOR; OLCUME UYULDU] Paket K6 'beklenen dosya adini rapidocr'un kendi cozucusuyle (`InferSession.get_model_url`) bulur' ve K11 'sahte fabrika params'i enum uyeleriyle karsilastirir' diyor; K1 ise testlerin `rapidocr` import etmemesini ve sefin bariyerinin her `rapidocr*` import'unu `RuntimeError` ile kesmesini istiyor. OLCULDU (`evidence/olcum-1-bariyer-ve-model-dizini.txt`): bariyer altinda `import rapidocr`, `import rapidocr.inference_engine.base` VE `importlib.util.find_spec('rapidocr')` UCU DE `RuntimeError`. Yani birim testlerde kosan HICBIR motor yolu cozucuyu cagiramaz ve params'a kutuphane enum uyesi koyamaz; K6'nin kendi olcusu ('model_dir'e beklenen adlarla bos dosyalar konunca fabrika cagrildi, params[...model_path] o dosyalar') canli cozucuyle YAZILAMAZ. Uygulanan cozum: (a) dosya adlari motorda SABIT tablo (`beklenen_model_dosyalari`); tablo kutuphanenin cozucusuyle dort dil x det/rec icin BIREBIR eslendi (`evidence/olcum-2-model-adlari-ve-enum.txt` (a)); yanlis ad `real_check` #1-#4'te `ModelMissingError` olarak patlar (kapali dongu). (b) params STRING deger tasir ('multi', 'japan', 'onnxruntime', 'mobile', 'PP-OCRv4'); `_varsayilan_fabrika` bunlari kutuphane enum uyelerine cevirir (`LangDet('multi') is LangDet.MULTI` vb. -- olcum-2 (c)); donusum ZORUNLU cunku kutuphane `engine_type/model_type/ocr_version` icin string verilirse `TypeError` atiyor (olcum-2 (b)). Birim testi K11'i string degerlerle olcer (4 dil x 6 anahtar, `test_k11_*`), gercek yol `real_check` #1-#4 ile olculur. (c) varsayilan model dizini `importlib.metadata.distribution('rapidocr').locate_file(...)` ile bulunur: bariyeri tetiklemiyor (meta_path bulucularina 'rapidocr' adi icin sormuyor), `Path(rapidocr.__file__).parent/'models'` ile AYNI yolu veriyor ve `sys.modules`a rapidocr YUKLEMIYOR (olcum-1 C). Sef paketi 'canli cozucu' lafziyla degil bu tabloyla okumali."
  - "[ITIRAZ-4 -- K6 'Cls modeli paketle geliyor' DOGRULANDI ama bir bosluk var] wheel RECORD'unda `ch_ppocr_mobile_v2.0_cls_mobile.onnx` VAR (olcum-2 (d)); paketin cumlesi dogru, cls YONETILMEZ. Bosluk: `use_cls=False` iken de kutuphane cls oturumunu KURUYOR ve `Cls.model_path` verilmedigi icin `Global.model_root_dir/<ad>` uzerinden `DownloadFile.run` calisiyor -- dosya varsa sha256 dogrulayip geciyor, YOKSA INDIRIYOR. OLCULDU (olcum-3 #8): `Global.model_root_dir`=bos tmp + det/rec acik yol -> kurulum BASARILI ve cls tmp'ye indirildi (ag erisimi). Bu yuzden motor `allow_download=False` yolunda `Global.model_root_dir`i ASLA gecmez (cls kutuphanenin kendi dizininden, wheel'den gelir); o dosya elle silinmisse kutuphane 0.6 MB indirir -- `allow_download=False`'un 'hic ag yok' garantisinin tek deligi, [ÖLÇÜLMÜYOR], belgelendi (docstring K6). Kapatmak `Cls.model_path`i de sabitlemeyi gerektirir; paket 'yonetilmez' dedigi ve bu, birim testleri kurulu kutuphaneye bagimli kilacagi icin YAPMADIM -- sef isterse tur 2."
  - "[K2 ZORUNLU] `language` keyword-only, varsayilani YOK; `OcrLanguage(language)` ile dogrulanir (uye ya da 'japan' gibi degeri kabul, baska sey `ValueError` yapimda). Motor dili tahmin etmez; guven puani dil hatasini goremez (O2). Olcu: `test_k2_*` (imza AST, `RapidOcrEngine()` -> TypeError) + `real_check` #1/#2 (JAPAN 4/4, CHINESE 0/4 -- pozitif kontrol K11 tablosuyla ATESLEDI). Docstring '## K2'."
  - "[K3 ZORUNLU] `threads` in [1, os.cpu_count()]; None -> min(8, cpu_count or 1); aralik disi ValueError YAPIMDA; deger iki anahtara (`EngineConfig.onnxruntime.intra_op_num_threads`, `inter_op_num_threads`) AYNEN duz `int` olarak; `Global.use_cls=False`. KARAR (paket sessizdi): tam sayi olmayan (`bool`, `float`, `str`) -> `TypeError` (`True == 1` sessizce gecmesin); `numbers.Integral` (np.int64) kabul edilip duz int'e duzlestirilir; `cpu_count()` None -> 1. Olcu: `test_k3_*` -- 4 ve 8 iki noktada, `cpu_count=6` yamasiyla 8 -> ValueError / None -> 6 / 4 -> gecer, 0/-1/-8 -> ValueError, True/2.0/'8'/4.5 -> TypeError. Gercek oturum secenekleri birim testte [ÖLÇÜLMÜYOR]; olcum-3 #4 det ve rec oturumlarinda intra/inter = 8/8 gosterdi. Docstring '## K3'."
  - "[K5 ZORUNLU] `Global.text_score = 0.0` gecilir; her (kutu, metin, puan) bire bir TextBlock, rapidocr sirasiyla, `confidence = float(puan)` (NaN aynen, np.float32 duz float), `text` DEGISTIRILMEZ (strip yok; bos string ve bosluklu metin aynen). Bos sonuc `boxes=None` nesnesi -> `[]`. YENIDEN URETILDI (olcum-3 #9): KR fixture + JAPAN modeli `text_score=0.5` -> 9 kutu, `0.0` -> 17 kutu, 8'i 0.5 altinda (min 0.113). `real_check` #8 `ok` (17 blok, 8 tanesi <0.5). KRT D3 belgelendi: kutuphane `strip()` sonrasi bos metinleri bizden ONCE eler, bu guven suzgeci degildir ve kapatilamaz. KARAR: `boxes=None` ama `txts` bos-olmayan dizi -> `OcrError` ('kutusuz metin'; gercek motor uretmez, sahte icin gurultulu); `txts=()`/`scores=()` ile `boxes=None` -> `[]`. Olcu: `test_k5_*`. Docstring '## K5'."
  - "[K6 ZORUNLU] (a) `allow_download=False`: `Det.model_path`/`Rec.model_path` = `model_dir / <ad>` (Path nesnesi, paketin lafzi); dosya yoksa fabrika CAGRILMADAN `ModelMissingError`, mesajda eksik adlar, `__cause__` None. `allow_download=True`: `*.model_path` YOK; KARAR (paket sessizdi): `model_dir` verilmisse `Global.model_root_dir = model_dir` gecilir ki indirme cagiranin dizinine insin (verilmezse kutuphane site-packages icine yazar; `Global.model_root_dir` Path kabul ediyor -- olculdu). Cevrimdisi `DownloadFileException` -> `ModelMissingError` (`__cause__` ozgun) [ÖLÇÜLMÜYOR] -- ag kesilmedi. (b) tanıyıcı istisnasi -> `OcrError` (`__cause__` ozgun); fabrika istisnasi: `TranslatorError` oldugu gibi, `FileNotFoundError` -> `ModelMissingError`, diger `Exception` -> `OcrError` (Y2 `ValueError` dahil). KARAR: kurulum basarisizsa ornek tutulmaz, sonraki `recognize` kurulumu yeniden dener (otomatik yeniden deneme YOK). (c) `frame` `Frame` degilse / `image` ndarray-(h,w,3)-uint8-pozitif boyut degilse / `rect.x,y,monitor_index` duz int degilse -> `ContractViolation`, fabrika sayaci 0. 0x0 ve h=0 gercek motorda `ZeroDivisionError` (olcum-3 #7) -> bu yuzden reddedilir; 1x1 tanıyıcıya gider. Bozuk cikti sinifi (16 vaka, `test_k6_bozuk_cikti_ocrerror`) -> `OcrError`, hata metni blok metnini TASIMAZ (`test_k6_hata_mesaji_ocr_metni_tasimaz`). `real_check` #7 `ok`. Docstring '## K6'."
  - "[K7] Modulde `print` yok, `logging` cagrisi yok (yalniz `setLevel`; AST testi). Kutuphane kurulumda logger seviyesini SIFIRLIYOR -- yeniden uretildi (olcum-3 #2: kurulum oncesi ERROR -> sonrasi INFO); motor seviyeyi fabrika DONDUKTEN SONRA ERROR'a ceker VE params'a `Global.log_level='error'` koyar (olcum-3 #3: kurulum sirasindaki 6 INFO satiri da susuyor). Olcu: `test_k7_*` (fabrika seviyeyi INFO'ya sifirlar -> recognize sonrasi ERROR; nobetci metin caplog'a dusmez; seviye dusurulmezse WARNING'in gectigi pozitif kontrol). Mutant kiti MT-03/03b/04 ucu de yakalandi."
  - "[K8 ZORUNLU] `preset` kabul edilir, hicbir params anahtarina girmez, dort preset ayni ciktiyi verir (`test_k8_dort_preset_ayni_cikti`: fabrika tek kez, params dort cagrida ayni). On ayar bazli olcekleme/kontrast on islemesi [ÖLÇÜLMÜYOR] -- ayri gorev; damga modul docstring'inde VE `recognize` docstring'inde (AST testi `test_k8_olculmuyor_damgasi_docstringde`)."
  - "[K9] Motor sure tutmaz (`last_timing` yok -- `test_uyum_ocrengine_altsinifi` hasattr ile olcer). Sureler `real_check` #5'te RAPORLANDI: JAPAN medyan 176 ms / 4 kutu (butce 300 -- ALTINDA), ENGLISH 240 ms / 4 kutu (350), KOREAN 673 ms / 17 kutu = 40 ms/kutu (150). Ilk kurulum 356-412 ms (olcum-3 #2/#3)."
  - "[K10] `__init__` kutuphaneye ve dosya sistemine dokunmaz (yalniz arguman dogrulama; `test_k10_init_model_kontrolu_yapmaz`: model yokken yapim basarili, hata ilk recognize'da). Uc recognize -> fabrika 1; `close()` x2 sessiz; sonra recognize -> `OcrError`, sayac hala 1; kurulmamis motorda close sonrasi recognize -> OcrError, sayac 0. Baglam yoneticisi DEGIL (`__enter__`/`__exit__` yok). Docstring '## K10'."
  - "[K11 ZORUNLU] Dil basina sabit tablo: JAPAN (multi, japan), KOREAN (multi, korean), CHINESE (ch, ch), ENGLISH (ch, en); ortak engine_type='onnxruntime', model_type='mobile', ocr_version='PP-OCRv4'; params STRING tasir, gercek fabrika enum'a cevirir (bkz. [ITIRAZ-3]). Olcu: `test_k11_dil_tablosu_alti_anahtar` (4 dil), `test_k11_params_anahtar_kumesi_sabit` (tam anahtar kumesi, KRT D4 'yanlis ic ice anahtar' sinifina karsi), `test_k11_params_her_cagri_taze_kopya`. `real_check` #1-#4 bu tabloyla gecti; #2 pozitif kontrolu ATESLEDI (CHINESE 0/4). Cls anahtari HIC gecilmez. Docstring '## K11'."
  - "[MUTANT KAPISI -- kendi olcumum] `evidence/mutant-kiti.py` ayna agacinda 24 mutant + 1 davranis-esdeger kontrol kostu (`evidence/mutant-ayirt-etme.txt`): 24/24 YAKALANDI, MT-KONTROL (sozluk anahtar sirasi) KACTI = yanlis pozitif yok. Ilk kosumda MT-05 (floor -> round) KACMISTI: K4 fixture'imin `min_x=10.4` ve `-5.5` degerleri round/floor'u ayirmiyordu (`round(-5.5) == -6`, tesadufen floor ile ayni). Fixture ayrisan noktalara tasindi (min 10.6/18.9, max 51.2/42.3; tasan kutu -5.4) ve MT-05/05c/05d/05b dordu de yakalaniyor. 4.6/4'un dersi: olcu, ifadenin degismezden AYRISTIGI girdide kosmali."
  - "KARAR (dokuman sessizdi): `TanımaÇıktısı` Protocol'unun uc alani salt-okunur `@property` olarak tanimlandi (paketin taslagi duz oznitelikti). Gerekce: mypy Protocol'de duz (mutable) oznitelikleri DEGISMEZ tipli ister; kutuphanenin `Optional[np.ndarray]` / `Optional[Tuple[str]]` alanlari `object | None` / `Sequence[str] | None`e ancak salt-okunur ozellikle yapisal olarak uyar (mypy sondasiyla dogrulandi; `--strict` temiz). `_varsayilan_fabrika`nin tanıyıcısi kutuphane ciktisini `isinstance(..., RapidOCROutput)` ile daraltir; baska tip (`TextDetOutput` gibi, kutuphane rec bos donerse bunu dondurebiliyor) -> `OcrError`."
  - "KARAR (dokuman sessizdi): iki gozlem ozelligi ve bir gozlem metodu PUBLIC: `language`, `threads` (duzlestirilmis), `parametreler()` (fabrikaya gidecek sozlugun TAZE kopyasi; `allow_download=False` ise model dosya denetimini de yapar). Tester ve `real_check` fabrikasiz da gozlemleyebilsin diye. `beklenen_model_dosyalari(language)` ve `varsayilan_model_dizini()` de public (K6 olcusu icin gerekli)."
  - "KARAR (dokuman sessizdi): `recognize` sirasi kapali-mi -> kare dogrulama -> tembel kurulum -> tanıma -> donusum. Kapali motorda bozuk kare de `OcrError` alir (ContractViolation degil); docstring'de yazili. `allow_download` `bool` degilse `TypeError`; `model_dir` `str` ise `Path`e cevrilir."
  - "KARAR (dokuman sessizdi): `# pragma: no cover` YALNIZ `_varsayilan_fabrika`nin `def` satirinda (`-- K1: gercek model, real_check.py ile denetleniyor`). Kapsam %98.94 (188 ifade / 2 eksik: iki 'yapisal olarak erisilemez' `ValueError` satiri, pragma almadi). Esik 90."
  - "KAPSAM DISI (bloke etmeyen): `frame.image` C-contiguous mu ve `image.shape` ile `rect.w/h` tutarli mi DENETLENMEZ (`CaptureService` K7 garanti eder); goruntu kopyalanmaz (kutuphane girdiyi degistirmiyor -- olcum-3 #6 yeniden uretti). Thread-safe degil (tasarim 5.5). Gorev paketindeki kabul komutu #3'un iki ihlali icin `real_check.py`ye DOKUNULMADI; `git commit` ATILMADI."
---

# T-006 teslim -- tur 1

## Ne yazildi

* `src/ocr/rapid_engine.py` -- `OcrLanguage`, `TanımaÇıktısı`, `Tanıyıcı`,
  `TanıyıcıFabrikası`, `RapidOcrEngine`, `beklenen_model_dosyalari`,
  `varsayilan_model_dizini`. Paketin imzasi AYNEN. `rapidocr` yalniz
  `_varsayilan_fabrika` govdesinde import edilir. Modul docstring'i K1-K11'i
  olcusuyle belgeler.
* `tests/unit/ocr/test_rapid_engine.py` -- 95 test, hepsi sahte fabrikayla,
  bariyer altinda. TDD: `evidence/tdd-kirmizi.txt` (modul yokken
  toplama hatasi) -> yesil.

## Bes komut

| # | komut | exit | kanit |
|---|---|---|---|
| 1 | mypy --strict | 0 | `evidence/mypy.txt` |
| 2 | pytest birim | 0 (95 passed) | `evidence/pytest.txt` |
| 3 | real_check.py | **1** (2 IHLAL, 14 ok) | `evidence/real_check.txt` |
| 4 | coverage >= 90 | 0 (%98.94) | `evidence/cov.txt` |
| 5 | pytest tum takim | 0 (1085 passed = 990 + 95) | `evidence/pytest-tum.txt` |

## Hangi iddia nasil olculdu

* **olcum-1** -- bariyer altinda `import rapidocr` / `find_spec` patlar,
  `importlib.metadata` ayni dizini yuklemeden verir -> K6/K11 ile K1
  celiskisinin cozumu (ITIRAZ-3).
* **olcum-2** -- K11 tablosu -> kutuphane cozucusunun dosya adlari (sabit
  tablo buradan); string -> enum zorunlulugu (`TypeError`); cls wheel'de.
* **olcum-3** -- gercek motor: logger sifirlama (K7), oturum 8/8 (K3), bos
  kare `boxes=None` (K5/Y4), 0x0 `ZeroDivisionError` (K6 c), girdi mutasyonu
  yok, `Det.model_dir` yok sayilip INDIRME yapiliyor (K6), `text_score`
  0.5 -> 9 kutu / 0.0 -> 17 kutu (K5).
* **olcum-4** -- real_check #3 teshisi (metinsiz): kova `round(y/25)`
  212 -> 8, 213 -> 9; ayni bloklar `y//60` ile 0.971 = O5.
* **olcum-5** -- real_check #6a teshisi: ilk satir y=93, -50 ile 43;
  `rect.y<=-94` ile negatif (pozitif kontrol).
* **mutant kiti** -- 24 mutant yakalandi, davranis-esdeger kontrol kacti.

## Pakete itirazlar (ozet; ayrintisi `known_gaps`)

1. real_check [3] -- okuma sirasi kovasi satiri boluyor (kapi kusuru).
2. real_check [6a] -- `y<0` bu fixture'la saglanamaz (kapi kusuru).
3. K6/K11 "canli cozucu / enum uyesi" K1 bariyeriyle celisiyor -- olcume
   uyuldu: sabit ad tablosu + string params + fabrikada enum donusumu.
4. K6 cls "paketle geliyor" dogru; ama silinmisse `allow_download=False`
   altinda kutuphane indirir -- belgelendi, kapatilmadi.
