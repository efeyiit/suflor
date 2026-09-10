---
task: T-005
role: implementer
round: 3
status: tamamlandi
files_written:
  - src/capture/service.py
  - tests/unit/capture/test_service.py
  - .agents/tasks/T-005/evidence/mypy-tur3.txt
  - .agents/tasks/T-005/evidence/pytest-tur3.txt
  - .agents/tasks/T-005/evidence/headless-tur3.txt
  - .agents/tasks/T-005/evidence/cov-tur3.txt
  - .agents/tasks/T-005/evidence/pytest-tum-tur3.txt
  - .agents/tasks/T-005/evidence/budget-tur3.txt
  - .agents/tasks/T-005/evidence/t3-1-mutant-ayirt-etme.txt
  - .agents/tasks/T-005/evidence/t3-1-mutant-kiti.py
  - .agents/tasks/T-005/evidence/t3-2-derin-inside-ayrisma.txt
  - .agents/tasks/T-005/evidence/t3-2-olcum-kiti.py
  - .agents/tasks/T-005/delivery.md
commands:
  - cmd: "python -m mypy --strict --explicit-package-bases src/capture/service.py src/capture/monitors.py"
    exit_code: 0
    evidence: evidence/mypy-tur3.txt
  - cmd: "python -m pytest tests/unit/capture/test_service.py tests/unit/capture/test_monitors.py -q"
    exit_code: 0
    evidence: evidence/pytest-tur3.txt
  - cmd: "python .agents/tasks/T-005/headless_check.py"
    exit_code: 0
    evidence: evidence/headless-tur3.txt
  - cmd: "python -m pytest tests/unit/capture -q --cov=src.capture.service --cov=src.capture.monitors --cov-fail-under=95"
    exit_code: 0
    evidence: evidence/cov-tur3.txt
  - cmd: "python -m pytest tests -q"
    exit_code: 0
    evidence: evidence/pytest-tum-tur3.txt
contract_change_request: false
known_gaps:
  - "[TUR 3 -- T3-1] `__exit__` olcusu artik CIKIS YOLU ekseninde parametreli. `test_k10_exit_uzun_omurlu_tutamaci_kapatir` `exc_type` uzerinde iki parametre kosuyor: `exc_type=None` (normal dusus / `return` / `break` / `continue`) ve `exc_type=CaptureError` (govdede istisna; `generator.close()` -> `GeneratorExit` ayni sinifa coker). Eksenin ayrik sinif sayisi 2'dir, ucuncu varyant yoktur -- bu yuzden iki parametre ekseni KAPATIR (PROTOKOL 4.6/7). Testin istisna bacagi `pytest.raises(..., match=...)` ile ayrica `__exit__`'in istisnayi YUTMADIGINI olcer. AYIRT ETME GUCU AYNA AGACINDA OLCULDU (ham cikti evidence/t3-1-mutant-ayirt-etme.txt; kit evidence/t3-1-mutant-kiti.py; depodaki src/ ve tests/ HIC degistirilmedi): TABAN tur2 123 passed -> tur3 124 passed; MT-53 (`__exit__` yalniz istisnasiz cikista kapatir) tur2 123 passed KACTI -> tur3 1 failed YAKALANDI; MT-12 (`__exit__` -> `return None`) tur2 1 failed -> tur3 2 failed; MT-YUT (`__exit__` kapatir ama `return True` ile istisnayi YUTAR) tur2 123 passed KACTI -> tur3 1 failed YAKALANDI; MT-KONTROL (davranis-esdeger) IKISINDE DE kacti -- yani olcu yanlis pozitif URETMIYOR. Uygulamaya DOKUNULMADI: `MssBackend.__exit__` tur 1'den beri kosulsuz `self.close()` cagiriyor; kusur kodda degil OLCUDEYDI (Tester-D'nin kendi ifadesi)."
  - "[TUR 3 -- T3-2 -- OLCUM SEFIN KARAKTERIZASYONUNU GENISLETTI, OKUNMASI GEREKEN KALEM] `capture_region` docstring'inden tur 2'de yazilan su cumle SILINDI: 'Kenardan uzak (derin INSIDE) bolgelerde ise dort tipte de ayrisma sifirdir -- tasma yalnizca monitor sinirlarina yaklasan bolgelerde gozlemlenebilir hale gelir.' Cumle OLCUMLE YANLIS ve PROTOKOL 4.6/10'un yasakladigi siniftandi (olumsuz evrensel iddia, olcunun ateslenebildigi gosterilmeden). Sefin karsi ornegi BAGIMSIZ YENIDEN URETILDI (ham cikti evidence/t3-2-derin-inside-ayrisma.txt, A bolumu): `Rect(1000,600,1000,200)` M1=(0,0,2560,1440)'in tamamen icinde, her kenardan >= 560 px uzak; duz `int` -> ok (1000,600,1000,200), ham `uint16`/`uint32`/`uint64` -> `CaptureError` (uint8 bu degerleri TEMSIL EDEMEZ, bu yuzden o tipte vaka yok). ANCAK sefin 'ayrisan aile x == w' karakterizasyonu EKSIK cikti: hedefli sonda (C2 bolumu) `x != w` olan 52 ayrisan uye buldu, ornegin `uint16` + `Rect(100,600,1124,64)` -- ayni derinlikte, `CaptureError`. Sefin kararindaki tablo (x==w ailesi) DOGRU ama KAPSAYICI DEGIL; kararin lafzi yazilmadi, OLCULEN yazildi (tur 2'de de tam olarak bu yasandi). Docstring artik kumeyi [OLCULMUYOR] damgaliyor ve yalnizca OLCULMUS UYELERI sayiyor: (1) kenardan tasan bolgeler (1108 sessiz farkli geometri / 240 sessizce kabul edilen gecersiz bolge, tur 2 olcumu), (2) derin INSIDE uyeler -- `x == w` ailesi VE `x != w` uyeleri, (3) L duzeninde `uint8` ciplak `OverflowError` (tur 3'te yeniden uretildi: `Rect(0,0,201,201)`, duzen A=(0,0,100,100) B=(100,100,100,100) -> 'Python integer 10000 out of bounds for uint8')."
  - "[TUR 3 -- POZITIF KONTROL] Yeni docstring hicbir olumsuz evrensel iddia TASIMIYOR; tasidigi tek nokta-negatifi ('x=1000 w=1001 ve x=999 w=1000 komsulari ayrismiyor') POZITIF KONTROLLE birlikte yazildi: ayni tablonun ayni satirlarinda ayni olcu, `x=1000 w=1000` icin ATESLIYOR (evidence/t3-2-derin-inside-ayrisma.txt, B ve D bolumleri). D bolumu bu kontrolu ayrica acikca yaziyor: derin INSIDE x==w -> ATESLEDI, kenardan tasan PARTIAL -> ATESLEDI, derin INSIDE x!=w -> ateslemedi. C bolumundeki 'TEK MONITOR duzeninde 0 ayrisma' sayimi da bu yuzden anlam tasiyor: AYNI olcu, AYNI grid, iki monitorlu duzende 54 ayrisma veriyor."
  - "[TUR 3 -- ADLANDIRILMIS TESTER YUKUMLULUGU, KAPSAM DISI BIRAKILDI] Tur 2 geri bildiriminde bloke ETMEYEN iki sinif kayda gecmisti ve tur 3 karari ikisini de bu turun kapsamina ALMADI; gizlenmesin diye burada adlandiriliyor. (1) M54 sinifi -- `grab()` tutamaci `_tutamac`'tan BASKA bir alana yazarsa yeni testler yine gecer (kendi enjekte ettikleri alani kapatirlar), yakalayan tek kapi `headless_check` 3'un kurulum/kapatma sayacidir; bagi VAR ama tek noktadan geciyor. (2) M58 sinifi -- `test_k3_backend_kutusu_duz_int_tasir` dort TIP noktasinda kosuyor ama yalniz INSIDE bacaginda; backend kutusuna numpy skalerini SADECE PARTIAL yolunda sizdiran bir uygulama bes kapidan da gecer. Ikisi de bu teslimde [OLCULMUYOR]. Bu ajan ikisini de KENDILIGINDEN kapatmadi: tur 3 karari kapsami acikca iki kaleme baglamis ve ertelemenin gerekcesini yazmistir; kapsam genisletme sefin yetkisindedir."
  - "[TUR 2 -- SEFE ITIRAZ, OKUNMASI GEREKEN KALEM] (TUR 3'TE DE GECERLI, uzerine T3-2 eklendi) T2-2'nin kendi olcusu KOR cikti; docstring sefin dikte ettigi cumleyle DEGIL, olculen gerceklerle yazildi. Sefin karari 'sessiz ayrisma SIFIR, tasmanin tek gorunur kipi CaptureError (gurultulu red)' diyor ve docstring'e bunun yazilmasini istiyor. Bu ajan iddiayi bagimsiz yeniden uretmeye calisti (ham cikti evidence/t2-2-tasma-olcumu.txt): sefin grid'i (x,y 0..260, w,h 1..260) bu makinenin GERCEK duzeninde (M0=(-2560,0,2560,1440), M1=(0,0,2560,1440)) yeniden kosuldugunda GERCEKTEN sifir ayrisma veriyor (B bolumu: dort tipte de 28561/33124 kombinasyonun tamami AYNI) -- ama sebebi tasmanin zararsizligi DEGIL, o grid'in her bolgesinin 2560x1440'lik monitorun derin icinde kalmasi: PARTIAL/OUTSIDE bir bolge grid'de HIC DOGMUYOR, yani sessiz sinifin olculdugu nokta yok. Grid kenarlardan gecirilince (C bolumu: x 0..2600, y 0..1400, w/h in {1,50,200,500}) sessiz sinif DOLUYOR: uint32/uint64 icin 6480 kombinasyonun 1108'i SESSIZCE FARKLI GEOMETRI, 240'i SESSIZCE KABUL EDILEN GECERSIZ bolge. Kanonik ornek (D bolumu): Rect(uint32(2500), uint32(100), uint32(200), uint32(100)) gercekte PARTIAL'dir (dogru cevap w=60), duzlestirme olmasa classify_region onu 'inside' sayiyor ve backend'e de Frame.rect'e de w=200 gidiyor -- istisna yok, uyari disinda gorunur iz yok. Ucuncu bir kip de var (E bolumu): kucuk monitor duzeninde uint8 ile K6 taksonomisi DISINDA ciplak OverflowError. Sonuc: 'sessizce yanlis' cumlesi CURUMEDI, YERI DEGISTI -- tur 1 docstring'i onu yanlis mekanizmaya (monitor_index) bagliyordu, dogrusu KIRPMANIN ATLANMASI. Sefin bildirdigi 2136/1152 sayilari bu ajan tarafindan YENIDEN URETILEMEDI (hangi monitor duzeninde olculdukleri karara yazilmamis), bu yuzden docstring'e YAZILMADI. TUR 3 EKI: bu grid'in bir kor noktasi daha vardi -- adim 20 yuzunden `x == w` noktasini yapisal olarak uretemiyordu, bu yuzden 'derin INSIDE'da ayrisma yok' genellemesi dogdu ve YANLISTI; bkz. yukaridaki [TUR 3 -- T3-2] kalemi. PROTOKOL 4.6/7 ve /10 tam olarak bu sinif: olcu, degismezin ihlal EDILEBILECEGI noktada kosmali."
  - "[K8 ZORUNLU -- TUR 2'DE DUZELTILDI, TUR 3'TE GENISLETILDI] Isaretsiz numpy tamsayilarinda dondurulmus dpi.py TASAR ve tasma DORT TIPIN DORDUNDE DE vardir: np.uint8, np.uint16, np.uint32, np.uint64 (her birinde RuntimeWarning: overflow encountered -- olculdu, evidence/t2-2-tasma-olcumu.txt A bolumu). Tur 1 docstring'i yalniz uint16/uint32 sayiyordu ve zarari 'monitor_index sessizce yanlis' diye tarif ediyordu; ikisi de duzeltildi. Olculen zarar kipleri: (1) GURULTULU RED -- gecerli bir bolge CaptureError alir (Rect(uint16(100),uint16(100),uint16(100),uint16(100)) INSIDE olmasina ragmen classify_region 'outside' verir; ayni kip DERIN INSIDE'da da olculdu, bkz. [TUR 3 -- T3-2]); (2) SESSIZ YANLIS -- kirpma atlanir ve backend'e de Frame.rect'e de KIRPILMAMIS dikdortgen gider (Rect(uint32(2500),uint32(100),uint32(200),uint32(100)) icin dogru cevap w=60, olculen w=200); (3) K6 TAKSONOMISI DISI ciplak OverflowError (uint8, kucuk L duzeni). KURAL DEGISMEDI: duzlestirme yine capture_region'in GIRISINDEDIR ve yine KOSULSUZ GEREKLIDIR; degisen yalnizca gerekce cumlesidir. Ayni metin capture_region docstring'inde."
  - "[TUR 2 -- T2-1] tests/unit/capture/test_service.py'ye K10'un iki bos olcusunu kapatan iki test eklendi: test_k10_exit_uzun_omurlu_tutamaci_kapatir ve test_k10_close_tutamaci_sifirlar_ve_idempotenttir. Sahte tutamac (_SahteTutamac) dogrudan MssBackend._tutamac'a enjekte edilir; gercek ekrana ve gercek mss'e SIFIR temas, K1 engeli altinda kosar. TUR 3'te birincisi `exc_type` ekseninde PARAMETRELENDI (bkz. [TUR 3 -- T3-1]); ikisi de silinmedi ve zayiflatilmadi."
  - "[TUR 2 -- T2-3] Iki kor olcu kapatildi, uygulamaya DOKUNULMADI. (1) test_k1_fake_backend_varsayilan_ureticisi_bgra_sifir_dizi -- K1'in 'varsayilan image_factory (rect.h, rect.w, 4) sifir dizi dondurur' sozlesmesini olcer; h != w (Rect(0,0,4,3) -> (3,4,4)) secildi ki devrik bir uretici de dussun. (2) test_k3_backend_kutusu_duz_int_tasir -- backend'e giden kutuda numpy sizintisini TIP KIMLIGIYLE olcer (type(x) is int), dort numpy tipinde birden kosar. Ayirt etme gucu olculdu (evidence/t2-mutant-ayirt-etme.txt): MK-B (varsayilan uretici (h,w,3) dondurur, M44 sinifi) ve MK-A (backend kutusuna HAM rect gider, M37 sinifi) tur 1 testleriyle 159 passed / KACIRDI, tur 2 testleriyle 1 failed / YAKALANDI. (2)'nin PARTIAL bacagi hala olculmuyor -- bkz. [TUR 3 -- ADLANDIRILMIS TESTER YUKUMLULUGU], M58 sinifi."
  - "[K2 ZORUNLU] `seq` yalnizca TEK BIR CaptureService ornegi icinde karsilastirilabilir. Her yeni ornek 0'dan baslar; 5.5'in 'kucuk seq'i yok say' kurali ornekler ARASINDA calismaz. Pipeline servis ornegini degistirirse (bolge degisimi, monitor yeniden kesfi, yeniden baslatma) karsilastirma tabanini SIFIRLAMAK ZORUNDADIR; aksi halde yeni kareler eski sanilip atilir ve ceviri sessizce donar. Bu bir pipeline (A6) kisitidir, T-005 kapsaminda cozulemez -- `Rect`/`Frame` sozlesmesi ornek kimligi tasimiyor. Ayni cumle `service.py` modul docstring'inde ('seq yalnizca TEK ORNEK icinde karsilastirilabilir') yazilidir."
  - "[K5 ZORUNLU] Monitor kimligi KONUMSAL ve KARARSIZDIR. `monitor_index` yalnizca `mss`'in dondurdugu siradir. `mss` ham sozlukte `is_primary` ve `unique_id` veriyor ama dondurulmus `Rect` sozlesmesi bu alanlari TASIYAMIYOR, bu yuzden atiliyorlar. Monitor takilip cikarildiginda ya da duzen degistiginde eski `Rect`'ler sessizce BASKA bir monitore isaret edebilir ve bunu tespit etmenin bir yolu yok. Tasarim 5.6'nin 'Monitor cikarildi -> seridi birincil monitore tasi' satiri, `Rect`'e bir kimlik alani (`is_primary` / `unique_id`) eklenmeden UYGULANAMAZ; sef bunu v1 kapsami disina aldi, A7 icin sozlesme degisikligi adayi. Ayni not `monitors.py` modul docstring'inde."
  - "[K8 ZORUNLU] Servis DPI olcegini URETEMEZ; `Frame.rect.dpi_scale` cagiranin BEYANIDIR, `capture_full` icin `1.0`'dir. Gerekce (sef olctu): `mss` monitor sozlukleri olcek anahtari tasimaz (`left/top/width/height/is_primary/name/unique_id`), bu yuzden servisin monitor kumesindeki her `Rect`'in olcegi daima 1.0'dir. Olcek bilgisi A7'de (Qt `devicePixelRatio`) uretilir ve `Rect`'e cagiran tarafindan yazilir. `dpi.intersect` ciktisinin metadata'si KULLANILMAZ -- `intersect` donen `Rect`'in `monitor_index`/`dpi_scale`'ini IKINCI ARGUMANDAN alir, yani PARTIAL kirpmasinda cagiranin 1.5'i birlesimin 1.0'ina ezilirdi. Servis geometriyi `intersect`'ten, metadata'yi K8 kurallarindan kurar. Ayni not `CaptureService` sinif docstring'inde."
  - "[K10 ZORUNLU] Process icindeki ILK `mss.MSS()` kurulumu -- yani `MssBackend`'in ilk `monitors()` veya `grab()` cagrisi -- process DPI politikasini KALICI olarak `PER_MONITOR_DPI_AWARE` yapar (0 -> 2, geri alinamaz; sef olctu) ve Qt'nin olceklemesini etkiler. `MssBackend` metotlari `QApplication` kurulmadan ONCE cagrilmamalidir. (`MssBackend()` YAPIMI zararsizdir: tembeldir, `mss`'e hic dokunmaz -- modul duzeyindeki `_uyum_mss` ornegi de bu yuzden guvenlidir ve hicbir DC sizdirmaz.) Bu A6/A7 icin bir ENTEGRASYON KISITIDIR. Ayni not `service.py` modul docstring'inde ('mss yan etkileri -- ENTEGRASYON KISITI')."
  - "[K11 ZORUNLU] 5.7'nin 'Capture <= 10 ms' butcesi `mss` ile SIMDIDEN ASILIYOR: sefin olcumune gore gercek `mss.grab` medyani 13.5 ms'dir ve 600x200 ile 100x50 icin AYNIDIR -- yani bolge boyutundan bagimsiz SABIT maliyet. Servisin KENDI ek yuku butce icindedir ve cok altindadir (tur 3'te yeniden olculdu, 200 cagri, 600x200 bolge, `FakeBackend` (200,600,4): medyan 0.5199 ms, p95 0.6140 ms, min 0.4953, maks 0.8900 -- ham cikti `evidence/budget-tur3.txt`). Butce asimi T-005'in kapsami disindadir (backend degisikligi gerektirir) ve sef DXGI Desktop Duplication icin ayri gorev acmistir. Ayni not `service.py` modul docstring'inde ('Performans -- butce SIMDIDEN ASILIYOR')."
  - "[K12] `CaptureService` THREAD-SAFE DEGILDIR: `seq` sayaci ve monitor onbellegi kilitsizdir. 5.5 geregi tek bir worker thread'den kullanilir. Paket bunu [OLCULMUYOR] isaretlemis; test yazilmadi, docstring'e yazildi. Eszamanlilik testi A6'nin kapsamindadir."
  - "[K4] Kabul edilen sinir: L seklinde bir duzende birlesim sinirlayici dikdortgeni hicbir monitore dusmeyen 'olu' alan icerebilir ve `mss` orayi siyah doldurur. v1 bunu tespit ETMEZ, belgeler. `capture_region` ve `union_bbox` docstring'lerinde yazili; `test_k4_l_duzeninde_olu_alana_degen_bolge` davranisi sabitler."
  - "KARAR (dokuman sessizdi): `monitors.py` icinde `MonitorKaynagi` adli kucuk bir `Protocol` tanimlandi (`monitors() -> Sequence[Mapping[str, object]]`) ve `list_monitors`'in parametre tipi bu oldu. Gerekce: `list_monitors(backend)` imzasi `CaptureBackend`'i gerektirir ama o tip `service.py`'dedir ve `service.py` zaten `monitors.py`'yi import eder -- dairesel import olurdu. `CaptureBackend` bu protokole YAPISAL olarak uyar, ek bir yukumluluk dogurmaz ve `monitors.py` saf kalir (headless 2 `mss` import'u aramaz)."
  - "KARAR (dokuman sessizdi): `FakeBackend`'in gozlem oznitelikleri `monitors_calls` (monitors() sayaci), `grab_calls` (grab() sayaci -- URETICI PATLASA DA artar, K6'nin cagri sayisi hucreleri bunu gerektirir), `grab_rects` (grab()'e ulasan Rect listesi, sirali) ve `monitor_rects` (yapimda verilen demet) olarak adlandirildi. `monitor_rects` adi ZORUNLUYDU: `monitors` bu sinifta bir METOTTUR, ayni adli bir oznitelik onu golgeler ve protokol uyumu calisma zamaninda cokerdi. Dordu de PUBLIC ve `FakeBackend` docstring'inde tek tek belgelendi (tester `known_gaps` okumaz)."
  - "KARAR (dokuman sessizdi): `FakeBackend.monitors()`'in urettigi ham sozlukler YALNIZCA `left/top/width/height` anahtarlarini tasir (fazladan `is_primary`/`name`/`unique_id` konmadi); `[0]` birlesim girdisi `union_bbox(monitor_rects)` geometrisidir, monitor kumesi BOSSA `{'left':0,'top':0,'width':0,'height':0}`'dir (boylece `FakeBackend(())` -> `rects_from_mss_monitors` -> `()` ve servis bos kumeyle kurulabilir; `_uyum_fake` satiri tam olarak bunu kullanir). K5'in 'fazladan anahtarlar yok sayilir' kurali gercek ham liste uzerinden `test_k5_fazladan_anahtarlar_yok_sayilir` ve `test_k5_gercek_duzen` ile olculuyor. TUR 2: varsayilan `image_factory`'nin `(rect.h, rect.w, 4)` sifir dizi dondurdugu artik AYRICA olculuyor (tur 1'de hic olculmuyordu)."
  - "KARAR (dokuman sessizdi): `refresh_monitors()` yeni monitor demetini DONDURUR (`None` degil) -- cagiranin ikinci bir okuma yapmasini gereksiz kilar. Monitor kumesi ayrica salt-okunur `CaptureService.monitors` PROPERTY'siyle okunur."
  - "KARAR (dokuman sessizdi): `captured_at`, backend cagrisi BASARILI olduktan ve bicim dogrulandiktan SONRA, `Frame` kurulmadan hemen once okunur (yeniden denemelerde birden fazla okuma yapilmaz). K9'un 'enjekte sabit saatle captured_at birebir ayni' iddiasi bu secimden bagimsizdir."
  - "KARAR (dokuman sessizdi): `capture_full(i)` govdesi indeksi dogruladiktan sonra `capture_region(self._monitors[i])`'ye DEVREDER. Bu, K9'un 'ayni backend cagrisi' degismezini yapisal olarak garanti eder (iki yol ayri yazilsaydi sapabilirlerdi) ve K8'in `capture_full` bacaginin neden [OLCULMUYOR] oldugunu aciklar: o yolun rect'i K5'in zaten duzlestirdigi monitor kumesinden gelir. Negatif indeks ACIKCA reddedilir (`0 <= i < len`), cunku Python'un negatif indekslemesi `capture_full(-1)`'i sessizce 'son monitor' yapardi."
  - "KARAR (dokuman sessizdi): K6 (b) sinifinda yakalanan istisna tipi `Exception`'dir (`BaseException` DEGIL): `KeyboardInterrupt`/`SystemExit` yeniden denenmez, oldugu gibi yayilir. Deneme sayisi modul duzeyinde `_DENEME_SAYISI = 3` sabitidir. (c) sinifinda `raise` bir `except` blogunun ICINDE degildir, bu yuzden hem `__cause__` hem `__context__` `None` kalir -- karisik (b)->(c) dizisinde de oyle."
  - "KARAR (dokuman sessizdi): kopya `np.array(ham[:, :, :3], dtype=np.uint8, copy=True, order='C')` ile alinir. `np.ascontiguousarray(a[:, :, :3])` KULLANILMADI: 4 kanalda kopyaliyor ama 3 kanalda TAKMA AD donduruyor (sef dogruladi). Secilen bicim ayrica salt-okunur bir kaynaktan (`np.frombuffer(shot.bgra, ...)`) yazilabilir bir dizi uretir -- `test_k7_sahiplik_salt_okunur_kaynak` bunu ayri olcer."
  - "KARAR (dokuman sessizdi, paket iki secenek sunmustu): `MssBackend`'in uzun omurlu tutamacinin tipi `mss.MSS | None` secildi (`object | None` degil). Gerekce: `mss` 10.2.0 bir `py.typed` isaretcisi tasiyor, bu yuzden gercek tip `mypy --strict` tarafindan cozulebiliyor ve `cast`/`Any` kacisi gerekmiyor. Tip yalnizca `if TYPE_CHECKING: import mss` ile gelir; calisma zamani `import mss` yalnizca `monitors()`/`grab()` GOVDELERINDEDIR."
  - "KARAR (dokuman sessizdi): `CaptureBackend.grab` / `FakeBackend.grab` / `MssBackend.grab` donus aciklamasi `ImageArray` (= `npt.NDArray[np.uint8]`, dondurulmus sozlesme takma adi) secildi; `headless_check` 4 bu bicimi acikca kabul ediyor. Gerekce: sozlesmenin 'BGR, uint8' anlamini tipe tasir. NOT (tur 1'de OLCTUM): ciplak `np.ndarray` de bu ortamda `--strict`'i geciyor (mypy 2.3.1 + numpy 2.4.6, `ndarray` PEP 696 tip-parametresi varsayilanlarina sahip) -- yani bu bir ZORUNLULUK degil, bir TERCIHTI. `image_factory`'nin tipi `Callable[[Rect], ImageArray | None]` oldugu icin `FakeBackend.grab`'in `return` satirinda `# type: ignore[return-value]` GEREKLIDIR (`| None` olmadan `warn_unused_ignores` exit 1 verirdi)."
  - "KARAR (dokuman sessizdi): K8'in kabul kapisi yalnizca `x/y/w/h` icin zorunlu tutulmustu; `dpi_scale` icin de bir kapi konuldu (`bool` ve sayi olmayan degerler -> `CaptureError`), sonra `float()` uygulanir. Gerekce ayni Y7-3 mantigi: kapisiz `float('1.5')` SESSIZCE calisir ve K5'in ayni degerleri monitor sozlugunde acikca reddetmesiyle celisirdi. `np.float32(1.5)` KABUL edilir ve duz `float`'a duzlestirilir (`np.float32` JSON'a serilesmez -- sef olctu). Olculer: `test_k8_giris_dpi_scale_sayi_olmayan_reddedilir`, `test_k8_giris_dpi_scale_float32_duz_float_a_duzlesir`."
  - "KARAR (dokuman sessizdi): bozuk monitor sozlugu hata mesaji HEM monitor indeksini HEM ham liste indeksini bildirir ('monitor 0 (ham indeks 1): left anahtari yok'), cunku paket 'hangi indeks' derken ikisi arasinda ayrim yapmiyordu ve `[0]`'in atilmasi yuzunden ikisi birbirinden 1 kayiktir."
  - "KARAR (dokuman sessizdi): K13'un izin verdigi uc `# pragma: no cover` isareti, ilgili metotlarin `def` SATIRINA konuldu (`MssBackend.monitors`, `.grab`, `.close`), her birinin yaninda zorunlu `# K1: gercek ekran, headless_check 3 ile denetleniyor` yorumuyla. Gerekce: coverage pragma'yi yalnizca uzerinde bulundugu SATIRA/CLAUSE'a uygular; govde icindeki tek basina bir yorum satiri HICBIR SEYI dislamaz (once oyle yazildi, olculdu, duzeltildi). `def` satirindaki pragma tum govdeyi dislar -- paketin kastettigi budur. BASKA hicbir yerde `no cover` YOK (tur 2 ve tur 3'te degismedi). Yapisal olarak erisilemez iki savunma satiri (`union_bbox is None`, `intersect is None`) pragma ALMADI ve kapsanmadan da esik tutuyor: monitors.py %100, service.py %99, TOPLAM %98.83 -- bu sayi tur 1, tur 2 ve tur 3'te BIREBIR AYNIDIR (171 ifade / 2 eksik). Yeni parametre kapsami YUKSELTMEZ cunku `close()` govdesi zaten pragma'lidir; olctugu sey kapsam degil DAVRANISTIR."
  - "KARAR (dokuman sessizdi): `tests/unit/capture/conftest.py` engel fixture'ina EK OLARAK depo kokunu `sys.path`'e ekler (modul duzeyinde). Gerekce: `headless_check` 1 sondasi pytest'i `cwd=tests/unit/capture` ile kosuyor; depo koku olmadan `src.*` import'lari cozulmezdi. `tests/unit/contracts/conftest.py` ayni onlemi aliyor. Engel modulun geri alinmasi `finally` dalinda yapilir (oturum sonunda `sys.modules` eski haline doner)."
  - "KARAR (dokuman sessizdi): K7 dogrulama SIRASI: `isinstance(np.ndarray)` -> `ndim != 3` -> kanal 3/4 -> `dtype != uint8` -> boyut uyusmazligi. Tip denetimi ilk siradadir ki hicbir asamada sessiz donusum ihtimali dogmasin."
  - "OLCUM (tur 1'de dogrulandi): K7'nin dort ayrisan girdisi GERCEKTEN ayristirici -- `__array_interface__` tasiyan nesne, `__array__` metotlu nesne, 3B'ye cast edilmis `memoryview` ve PEP 688 `__buffer__` tasiyan nesne; DORDU de `np.asarray` ile `(4,5,4) uint8` veriyor (isinstance hepsinde False)."
  - "KAPSAM DISI (bloke etmeyen): `headless_check.py --real` (5, gercek `mss` dumani) KOSULMADI -- paket onu 'yalnizca sef kosar' diye isaretliyor ve bes kabul komutundan hicbiri `--real` icermiyor. Gercek ekran davranisi bu teslimde yalnizca 3'un casus modulu ve tur 2/tur 3'un sahte-tutamac testleri uzerinden dogrulanmistir."
  - "TUR 3 KAPSAMI: iki dosya degisti -- `tests/unit/capture/test_service.py` (bir test `exc_type` ekseninde PARAMETRELENDI; hicbir test silinmedi, hicbir assertion zayiflatilmadi, eski davranis `exc_type=None` parametresinde BIREBIR korunuyor) ve `src/capture/service.py`'nin `capture_region` DOCSTRING METNI. Kod mantigina, imzalara, davranisa DOKUNULMADI -- `git diff --stat`: iki dosya, +85/-15, hepsi bu iki kalem. `git commit` ATILMADI (sef atar)."
---

# T-005 teslim -- tur 3

Tur 2'de Tester-D yine **ret** verdi; iki bulgusunu da sef kendi eliyle
yeniden uretti ve ikisini de dogruladi. Ikisi de **kod** kusuru degil: biri bir
**olcunun ekseni**, digeri bir **belge cumlesi**. `src/capture` mantigina bu
turda da **hic dokunulmadi**.

## Ne degisti

| Kalem | Dosya | Ne |
|---|---|---|
| **T3-1** (bloke) | `tests/unit/capture/test_service.py` | `test_k10_exit_uzun_omurlu_tutamaci_kapatir` **`exc_type` ekseninde parametrelendi** (2 parametre) + `__exit__` istisnayi **yutmuyor** iddiasi |
| **T3-2** (bloke) | `src/capture/service.py` | `capture_region` docstring'indeki **olumsuz evrensel iddia silindi**, yerine olculmus uyeler + `[OLCULMUYOR]` damgasi -- **yalnizca metin** |

Sahipli test sayisi 163 -> **164**; tam takim 985 -> **986**. **Var olan hicbir
test silinmedi ya da zayiflatilmadi**: eski davranis `exc_type=None`
parametresinde birebir korunuyor.

## Bes kabul komutu -- besi de kosuldu, besi de exit 0

| # | Komut | Cikis | Sonuc | Kanit |
|---|---|---|---|---|
| 1 | `mypy --strict --explicit-package-bases` | **0** | Success: no issues found in 2 source files | `evidence/mypy-tur3.txt` |
| 2 | `pytest test_service.py test_monitors.py -q` | **0** | **164 passed** | `evidence/pytest-tur3.txt` |
| 3 | `python .agents/tasks/T-005/headless_check.py` | **0** | TEMIZ | `evidence/headless-tur3.txt` |
| 4 | `pytest tests/unit/capture -q --cov ... --cov-fail-under=95` | **0** | **747 passed**, TOPLAM **%98.83** | `evidence/cov-tur3.txt` |
| 5 | `pytest tests -q` | **0** | **986 passed** | `evidence/pytest-tum-tur3.txt` |

**Dusen test yok.** Kapsam tur 1/2/3'te **birebir ayni** (171 ifade / 2 eksik /
%98.83) -- yeni parametre kapsami yukseltmez, cunku `close()` govdesi zaten
pragma'lidir; olctugu sey kapsam degil **davranis**. Butce (K11) yeniden
olculdu: medyan **0.5199 ms**, p95 **0.6140 ms** (butce 10 ms) --
`evidence/budget-tur3.txt`.

## Hangi iddiayi nasil olctum

### T3-1 -- eksenin ayirt etme gucu (`evidence/t3-1-mutant-ayirt-etme.txt`)

Ayna agacinda (depodaki `src/` ve `tests/` **hic degistirilmedi**) bes varyant
kosuldu; her biri **iki** test dosyasiyla: tur 2'de teslim edilen
`test_service.py` ve bu turdaki hali. Kit: `evidence/t3-1-mutant-kiti.py`.

| Varyant | Ne yapiyor | TUR 2 testleri | TUR 3 testleri |
|---|---|---|---|
| **TABAN** | mutasyon yok | `123 passed` | `124 passed` |
| **MT-53** | `__exit__` **yalniz istisnasiz** cikista kapatir | `123 passed` **KACTI** | `1 failed` **YAKALANDI** |
| **MT-12** | `__exit__` hicbir sey yapmaz | `1 failed` | `2 failed` |
| **MT-YUT** | `__exit__` kapatir ama istisnayi **YUTAR** (`return True`) | `123 passed` **KACTI** | `1 failed` **YAKALANDI** |
| **MT-KONTROL** | davranis-esdeger (kontrol) | `123 passed` kacti | `124 passed` kacti |

Hedef mutant yakalaniyor, ikinci bir bicim (istisnayi yutan varyant) da
yakalaniyor, tabanda gecen **kontrol mutanti yanlis pozitif uretmiyor**. Sefin
bildirdigi tabloyla ayni yon (`TABAN 164`, `M53 1 failed`, `M12 2 failed`);
sayilar burada `test_service.py` **tek basina** kosuldugu icin 123/124'tur
(+40 `test_monitors.py` = 163/164).

**Eksenin kapali oldugunun gerekcesi sayim degil YAPIDIR:** `with`'ten cikista
`__exit__`'in gordugu `exc_type` tam **iki** ayrik sinif alir -- `None` (normal
dusus, `return`, `break`, `continue`) ve bir istisna sinifi (govdede yukselen
istisna; `generator.close()` -> `GeneratorExit` ikinciye coker). Ucuncu varyant
yok; iki parametre ekseni tuketir.

### T3-2 -- silinen cumlenin curutulmesi (`evidence/t3-2-derin-inside-ayrisma.txt`)

Sefin karsi ornegini **bagimsiz yeniden urettim** (kit:
`evidence/t3-2-olcum-kiti.py`; olcum noktasi `_hedef_dikdortgen`, referans ayni
geometrinin duz `int` hali -- **denetlenen uygulamadan turemeyen** bagimsiz
kanal, PROTOKOL 4.6/8):

* **A -- kanonik karsi ornek.** `Rect(1000,600,1000,200)`, `M1`'in tamamen
  icinde, her kenardan >= 560 px uzak: duz `int` -> `ok (1000,600,1000,200)`;
  `uint16`/`uint32`/`uint64` -> `CaptureError: bolge hicbir monitorle
  kesismiyor`. (`uint8` bu degerleri temsil edemez.) Urunun **kendi** yolu dort
  tipte de dogru: `(1000,600,1000,200)`, dort alan duz `int`.
* **B -- komsu tablosu.** `x=1000 w=1000` ayrisiyor; `x=1000 w=1001` ve
  `x=999 w=1000` **ayni tabloda** ayrismiyor -- yani olcu o noktalarda
  ateslenebilir durumda. `500/500`, `300/300`, `100/100`, `1200/1200`
  ayrisiyor.
* **C -- derin INSIDE grid, `x == w` uretebilen adimlarla.** Iki monitorlu
  duzende `uint16`/`uint32`/`uint64` icin 486 kombinasyonun **54'u** ayrisiyor;
  `uint8` icin 12'nin **6'si**. Ayni grid **tek monitorlu** duzende **0**
  ayrisma veriyor -- bu sayi ancak yukaridaki pozitif kontrolle birlikte anlam
  tasir.
* **C2 -- SEFIN KARAKTERIZASYONU EKSIK CIKTI.** Sefin karari ayrisan aileyi
  `x == w` diye tanimliyor. Hedefli sonda `x != w` olan **52** ayrisan uye
  buldu; en kisa ornek `uint16` + `Rect(100,600,1124,64)` -- ayni derinlikte,
  `CaptureError`. Bu yuzden docstring'e `x == w` bir **uye kumesi** olarak
  yazildi, kumenin **tanimi** olarak degil; kume `[OLCULMUYOR]` damgali.
* **D -- pozitif kontrol.** Ayni olcu, ayni kod yolu: derin INSIDE `x==w` ->
  ATESLEDI, kenardan tasan PARTIAL -> ATESLEDI, derin INSIDE `x!=w` ->
  ateslemedi.
* **E -- ucuncu kip.** Kucuk L duzeninde `uint8`: `Rect(0,0,201,201)` ->
  `OverflowError: Python integer 10000 out of bounds for uint8` (K6 taksonomisi
  **disinda**). Tur 2 olcumu yeniden uretildi.

**Docstring'e hicbir yeni olumsuz evrensel iddia yazilmadi.** Tasidigi tek
nokta-negatifi (iki komsunun ayrismamasi) pozitif kontrolu ile **yan yana**
duruyor.

## Kanit

Butun ham ciktilar `.agents/tasks/T-005/evidence/` altinda; tur 3 dosyalari
`-tur3` ekiyle, tur 1 ve tur 2'ninkiler **korunarak**. Her kabul komutu dosyasi
calistirilan komutla baslar ve gercek `exit_code=` satiriyla biter. Iki olcum
kiti (`t3-1-mutant-kiti.py`, `t3-2-olcum-kiti.py`) da kanit dizininde -- sef
her iddiayi kendi eliyle yeniden uretebilsin diye.
