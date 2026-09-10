---
task: T-005
role: implementer
round: 1
status: tamamlandi
files_written:
  - src/capture/service.py
  - src/capture/monitors.py
  - tests/unit/capture/conftest.py
  - tests/unit/capture/test_service.py
  - tests/unit/capture/test_monitors.py
  - .agents/tasks/T-005/evidence/pytest-red.txt
  - .agents/tasks/T-005/evidence/mypy.txt
  - .agents/tasks/T-005/evidence/pytest.txt
  - .agents/tasks/T-005/evidence/headless.txt
  - .agents/tasks/T-005/evidence/cov.txt
  - .agents/tasks/T-005/evidence/pytest-capture-all.txt
  - .agents/tasks/T-005/evidence/budget.txt
  - .agents/tasks/T-005/delivery.md
commands:
  - cmd: "python -m mypy --strict --explicit-package-bases src/capture/service.py src/capture/monitors.py"
    exit_code: 0
    evidence: evidence/mypy.txt
  - cmd: "python -m pytest tests/unit/capture/test_service.py tests/unit/capture/test_monitors.py -q"
    exit_code: 0
    evidence: evidence/pytest.txt
  - cmd: "python .agents/tasks/T-005/headless_check.py"
    exit_code: 0
    evidence: evidence/headless.txt
  - cmd: "python -m pytest tests/unit/capture/test_service.py tests/unit/capture/test_monitors.py -q --cov=src.capture.service --cov=src.capture.monitors --cov-fail-under=95 --cov-report=term-missing"
    exit_code: 0
    evidence: evidence/cov.txt
  - cmd: "python -m pytest tests/unit/capture -q"
    exit_code: 0
    evidence: evidence/pytest-capture-all.txt
contract_change_request: false
known_gaps:
  - "[K2 ZORUNLU] `seq` yalnizca TEK BIR CaptureService ornegi icinde karsilastirilabilir. Her yeni ornek 0'dan baslar; §5.5'in 'kucuk seq'i yok say' kurali ornekler ARASINDA calismaz. Pipeline servis ornegini degistirirse (bolge degisimi, monitor yeniden kesfi, yeniden baslatma) karsilastirma tabanini SIFIRLAMAK ZORUNDADIR; aksi halde yeni kareler eski sanilip atilir ve ceviri sessizce donar. Bu bir pipeline (A6) kisitidir, T-005 kapsaminda cozulemez -- `Rect`/`Frame` sozlesmesi ornek kimligi tasimiyor. Ayni cumle `service.py` modul docstring'inde ('seq yalnizca TEK ORNEK icinde karsilastirilabilir') yazilidir."
  - "[K5 ZORUNLU] Monitor kimligi KONUMSAL ve KARARSIZDIR. `monitor_index` yalnizca `mss`'in dondurdugu siradir. `mss` ham sozlukte `is_primary` ve `unique_id` veriyor ama dondurulmus `Rect` sozlesmesi bu alanlari TASIYAMIYOR, bu yuzden atiliyorlar. Monitor takilip cikarildiginda ya da duzen degistiginde eski `Rect`'ler sessizce BASKA bir monitore isaret edebilir ve bunu tespit etmenin bir yolu yok. Tasarim §5.6'nin 'Monitor cikarildi -> seridi birincil monitore tasi' satiri, `Rect`'e bir kimlik alani (`is_primary` / `unique_id`) eklenmeden UYGULANAMAZ; sef bunu v1 kapsami disina aldi, A7 icin sozlesme degisikligi adayi. Ayni not `monitors.py` modul docstring'inde."
  - "[K8 ZORUNLU] Servis DPI olcegini URETEMEZ; `Frame.rect.dpi_scale` cagiranin BEYANIDIR, `capture_full` icin `1.0`'dir. Gerekce (sef olctu): `mss` monitor sozlukleri olcek anahtari tasimaz (`left/top/width/height/is_primary/name/unique_id`), bu yuzden servisin monitor kumesindeki her `Rect`'in olcegi daima 1.0'dir. Olcek bilgisi A7'de (Qt `devicePixelRatio`) uretilir ve `Rect`'e cagiran tarafindan yazilir. `dpi.intersect` ciktisinin metadata'si KULLANILMAZ -- `intersect` donen `Rect`'in `monitor_index`/`dpi_scale`'ini IKINCI ARGUMANDAN alir, yani PARTIAL kirpmasinda cagiranin 1.5'i birlesimin 1.0'ina ezilirdi. Servis geometriyi `intersect`'ten, metadata'yi K8 kurallarindan kurar. Ayni not `CaptureService` sinif docstring'inde."
  - "[K10 ZORUNLU] Process icindeki ILK `mss.MSS()` kurulumu -- yani `MssBackend`'in ilk `monitors()` veya `grab()` cagrisi -- process DPI politikasini KALICI olarak `PER_MONITOR_DPI_AWARE` yapar (0 -> 2, geri alinamaz; sef olctu) ve Qt'nin olceklemesini etkiler. `MssBackend` metotlari `QApplication` kurulmadan ONCE cagrilmamalidir. (`MssBackend()` YAPIMI zararsizdir: tembeldir, `mss`'e hic dokunmaz -- modul duzeyindeki `_uyum_mss` ornegi de bu yuzden guvenlidir ve hicbir DC sizdirmaz.) Bu A6/A7 icin bir ENTEGRASYON KISITIDIR. Ayni not `service.py` modul docstring'inde ('mss yan etkileri -- ENTEGRASYON KISITI')."
  - "[K11 ZORUNLU] §5.7'nin 'Capture <= 10 ms' butcesi `mss` ile SIMDIDEN ASILIYOR: sefin olcumune gore gercek `mss.grab` medyani 13.5 ms'dir ve 600x200 ile 100x50 icin AYNIDIR -- yani bolge boyutundan bagimsiz SABIT maliyet. Servisin KENDI ek yuku butce icindedir ve cok altindadir (bu turda olculdu, 200 cagri, 600x200 bolge, `FakeBackend` (200,600,4): medyan 0.4289 ms, p95 0.5078 ms, min 0.3620, maks 0.7411 -- ham cikti `evidence/budget.txt`). Butce asimi T-005'in kapsami disindadir (backend degisikligi gerektirir) ve sef DXGI Desktop Duplication icin ayri gorev acmistir. Ayni not `service.py` modul docstring'inde ('Performans -- butce SIMDIDEN ASILIYOR')."
  - "[K12] `CaptureService` THREAD-SAFE DEGILDIR: `seq` sayaci ve monitor onbellegi kilitsizdir. §5.5 geregi tek bir worker thread'den kullanilir. Paket bunu [OLCULMUYOR] isaretlemis; test yazilmadi, docstring'e yazildi. Eszamanlilik testi A6'nin kapsamindadir."
  - "[K4] Kabul edilen sinir: L seklinde bir duzende birlesim sinirlayici dikdortgeni hicbir monitore dusmeyen 'olu' alan icerebilir ve `mss` orayi siyah doldurur. v1 bunu tespit ETMEZ, belgeler. `capture_region` ve `union_bbox` docstring'lerinde yazili; `test_k4_l_duzeninde_olu_alana_degen_bolge` davranisi sabitler."
  - "KARAR (dokuman sessizdi): `monitors.py` icinde `MonitorKaynagi` adli kucuk bir `Protocol` tanimlandi (`monitors() -> Sequence[Mapping[str, object]]`) ve `list_monitors`'in parametre tipi bu oldu. Gerekce: `list_monitors(backend)` imzasi `CaptureBackend`'i gerektirir ama o tip `service.py`'dedir ve `service.py` zaten `monitors.py`'yi import eder -- dairesel import olurdu. `CaptureBackend` bu protokole YAPISAL olarak uyar, ek bir yukumluluk dogurmaz ve `monitors.py` saf kalir (headless §2 `mss` import'u aramaz)."
  - "KARAR (dokuman sessizdi): `FakeBackend`'in gozlem oznitelikleri `monitors_calls` (monitors() sayaci), `grab_calls` (grab() sayaci -- URETICI PATLASA DA artar, K6'nin cagri sayisi hucreleri bunu gerektirir), `grab_rects` (grab()'e ulasan Rect listesi, sirali) ve `monitor_rects` (yapimda verilen demet) olarak adlandirildi. `monitor_rects` adi ZORUNLUYDU: `monitors` bu sinifta bir METOTTUR, ayni adli bir oznitelik onu golgeler ve protokol uyumu calisma zamaninda cokerdi. Dordu de PUBLIC ve `FakeBackend` docstring'inde tek tek belgelendi (tester `known_gaps` okumaz)."
  - "KARAR (dokuman sessizdi): `FakeBackend.monitors()`'in urettigi ham sozlukler YALNIZCA `left/top/width/height` anahtarlarini tasir (fazladan `is_primary`/`name`/`unique_id` konmadi); `[0]` birlesim girdisi `union_bbox(monitor_rects)` geometrisidir, monitor kumesi BOSSA `{'left':0,'top':0,'width':0,'height':0}`'dir (boylece `FakeBackend(())` -> `rects_from_mss_monitors` -> `()` ve servis bos kumeyle kurulabilir; `_uyum_fake` satiri tam olarak bunu kullanir). K5'in 'fazladan anahtarlar yok sayilir' kurali gercek ham liste uzerinden `test_k5_fazladan_anahtarlar_yok_sayilir` ve `test_k5_gercek_duzen` ile olculuyor."
  - "KARAR (dokuman sessizdi): `refresh_monitors()` yeni monitor demetini DONDURUR (`None` degil) -- cagiranin ikinci bir okuma yapmasini gereksiz kilar. Monitor kumesi ayrica salt-okunur `CaptureService.monitors` PROPERTY'siyle okunur."
  - "KARAR (dokuman sessizdi): `captured_at`, backend cagrisi BASARILI olduktan ve bicim dogrulandiktan SONRA, `Frame` kurulmadan hemen once okunur (yeniden denemelerde birden fazla okuma yapilmaz). K9'un 'enjekte sabit saatle captured_at birebir ayni' iddiasi bu secimden bagimsizdir."
  - "KARAR (dokuman sessizdi): `capture_full(i)` govdesi indeksi dogruladiktan sonra `capture_region(self._monitors[i])`'ye DEVREDER. Bu, K9'un 'ayni backend cagrisi' degismezini yapisal olarak garanti eder (iki yol ayri yazilsaydi sapabilirlerdi) ve K8'in `capture_full` bacaginin neden [OLCULMUYOR] oldugunu aciklar: o yolun rect'i K5'in zaten duzlestirdigi monitor kumesinden gelir. Negatif indeks ACIKCA reddedilir (`0 <= i < len`), cunku Python'un negatif indekslemesi `capture_full(-1)`'i sessizce 'son monitor' yapardi."
  - "KARAR (dokuman sessizdi): K6 (b) sinifinda yakalanan istisna tipi `Exception`'dir (`BaseException` DEGIL): `KeyboardInterrupt`/`SystemExit` yeniden denenmez, oldugu gibi yayilir. Deneme sayisi modul duzeyinde `_DENEME_SAYISI = 3` sabitidir. (c) sinifinda `raise` bir `except` blogunun ICINDE degildir, bu yuzden hem `__cause__` hem `__context__` `None` kalir -- karisik (b)->(c) dizisinde de oyle."
  - "KARAR (dokuman sessizdi): kopya `np.array(ham[:, :, :3], dtype=np.uint8, copy=True, order='C')` ile alinir. `np.ascontiguousarray(a[:, :, :3])` KULLANILMADI: 4 kanalda kopyaliyor ama 3 kanalda TAKMA AD donduruyor (sef dogruladi). Secilen bicim ayrica salt-okunur bir kaynaktan (`np.frombuffer(shot.bgra, ...)`) yazilabilir bir dizi uretir -- `test_k7_sahiplik_salt_okunur_kaynak` bunu ayri olcer."
  - "KARAR (dokuman sessizdi, paket iki secenek sunmustu): `MssBackend`'in uzun omurlu tutamacinin tipi `mss.MSS | None` secildi (`object | None` degil). Gerekce: `mss` 10.2.0 bir `py.typed` isaretcisi tasiyor, bu yuzden gercek tip `mypy --strict` tarafindan cozulebiliyor ve `cast`/`Any` kacisi gerekmiyor. Tip yalnizca `if TYPE_CHECKING: import mss` ile gelir; calisma zamani `import mss` yalnizca `monitors()`/`grab()` GOVDELERINDEDIR."
  - "KARAR (dokuman sessizdi): `CaptureBackend.grab` / `FakeBackend.grab` / `MssBackend.grab` donus aciklamasi `ImageArray` (= `npt.NDArray[np.uint8]`, dondurulmus sozlesme takma adi) secildi; `headless_check` §4 bu bicimi acikca kabul ediyor. Gerekce: sozlesmenin 'BGR, uint8' anlamini tipe tasir. NOT (bu turda OLCTUM): ciplak `np.ndarray` de bu ortamda `--strict`'i geciyor (mypy 2.3.1 + numpy 2.4.6, `ndarray` PEP 696 tip-parametresi varsayilanlarina sahip) -- yani bu bir ZORUNLULUK degil, bir TERCIHTI. `image_factory`'nin tipi `Callable[[Rect], ImageArray | None]` oldugu icin `FakeBackend.grab`'in `return` satirinda `# type: ignore[return-value]` GEREKLIDIR (`| None` olmadan `warn_unused_ignores` exit 1 verirdi)."
  - "KARAR (dokuman sessizdi): K8'in kabul kapisi yalnizca `x/y/w/h` icin zorunlu tutulmustu; `dpi_scale` icin de bir kapi konuldu (`bool` ve sayi olmayan degerler -> `CaptureError`), sonra `float()` uygulanir. Gerekce ayni Y7-3 mantigi: kapisiz `float('1.5')` SESSIZCE calisir ve K5'in ayni degerleri monitor sozlugunde acikca reddetmesiyle celisirdi. `np.float32(1.5)` KABUL edilir ve duz `float`'a duzlestirilir (`np.float32` JSON'a serilesmez -- sef olctu). Olculer: `test_k8_giris_dpi_scale_sayi_olmayan_reddedilir`, `test_k8_giris_dpi_scale_float32_duz_float_a_duzlesir`."
  - "KARAR (dokuman sessizdi): bozuk monitor sozlugu hata mesaji HEM monitor indeksini HEM ham liste indeksini bildirir ('monitor 0 (ham indeks 1): left anahtari yok'), cunku paket 'hangi indeks' derken ikisi arasinda ayrim yapmiyordu ve `[0]`'in atilmasi yuzunden ikisi birbirinden 1 kayiktir."
  - "KARAR (dokuman sessizdi): K13'un izin verdigi uc `# pragma: no cover` isareti, ilgili metotlarin `def` SATIRINA konuldu (`MssBackend.monitors`, `.grab`, `.close`), her birinin yaninda zorunlu `# K1: gercek ekran, headless_check §3 ile denetleniyor` yorumuyla. Gerekce: coverage pragma'yi yalnizca uzerinde bulundugu SATIRA/CLAUSE'a uygular; govde icindeki tek basina bir yorum satiri HICBIR SEYI dislamaz (once oyle yazildi, olculdu, duzeltildi). `def` satirindaki pragma tum govdeyi dislar -- paketin kastettigi budur. BASKA hicbir yerde `no cover` YOK. Yapisal olarak erisilemez iki savunma satiri (`union_bbox is None`, `intersect is None`, service.py:478 ve 481) pragma ALMADI ve kapsanmadan da esik tutuyor: monitors.py %100, service.py %99, TOPLAM %98.83."
  - "KARAR (dokuman sessizdi): `tests/unit/capture/conftest.py` engel fixture'ina EK OLARAK depo kokunu `sys.path`'e ekler (modul duzeyinde). Gerekce: `headless_check` §1 sondasi pytest'i `cwd=tests/unit/capture` ile kosuyor; depo koku olmadan `src.*` import'lari cozulmezdi. `tests/unit/contracts/conftest.py` ayni onlemi aliyor. Engel modulun geri alinmasi `finally` dalinda yapilir (oturum sonunda `sys.modules` eski haline doner)."
  - "KARAR (dokuman sessizdi): K7 dogrulama SIRASI: `isinstance(np.ndarray)` -> `ndim != 3` -> kanal 3/4 -> `dtype != uint8` -> boyut uyusmazligi. Tip denetimi ilk siradadir ki hicbir asamada sessiz donusum ihtimali dogmasin."
  - "OLCUM (bu turda dogrulandim, paketin iddiasini yeniden urettim): K7'nin dort ayrisan girdisi GERCEKTEN ayristirici -- `__array_interface__` tasiyan nesne, `__array__` metotlu nesne, 3B'ye cast edilmis `memoryview` ve PEP 688 `__buffer__` tasiyan nesne; DORDU de `np.asarray` ile `(4,5,4) uint8` veriyor (isinstance hepsinde False). K8'in isaretsiz numpy tuzagi da yeniden uretildi: dondurulmus `dpi.py`'de `uint16`/`uint32` ile `classify_region` `inside` yerine `partial` veriyor, 4 `RuntimeWarning: overflow` doguyor ve kesisen monitor sayisi 1 yerine 2 cikiyor -- yani duzlestirme olmasa `monitor_index` 1 yerine -1 olurdu."
  - "KAPSAM DISI (bloke etmeyen): `headless_check.py --real` (§5, gercek `mss` dumani) KOSULMADI -- paket onu 'yalnizca sef kosar' diye isaretliyor ve bes kabul komutundan hicbiri `--real` icermiyor. Gercek ekran davranisi bu teslimde yalnizca §3'un casus modulu uzerinden dogrulanmistir."
  - "GOZLEM (T-005 disi, bilgi amacli): calisma sirasinda depoda es zamanli git etkinligi vardi -- `tests/unit/capture/conftest.py`, `test_monitors.py`, `test_service.py` ve `evidence/pytest-red.txt` baska bir surec tarafindan commit edildi (f75d4d4 ve oncesi, T-004 turlariyla birlikte). Bu ajan hicbir git komutu CALISTIRMADI; diskteki dosyalar dogru ve beste kabul komutu bu dosyalar uzerinde kosuldu."
---

# T-005 teslim -- tur 1

## Ne yazildi

| Dosya | Icerik |
|---|---|
| `src/capture/monitors.py` | `MonitorKaynagi` (Protocol), `rects_from_mss_monitors`, `list_monitors`, `union_bbox` -- **saf**, `mss` import'u yok |
| `src/capture/service.py` | `CaptureBackend` (Protocol), `MssBackend`, `FakeBackend`, `CaptureService` + iki uyum satiri |
| `tests/unit/capture/conftest.py` | Oturum kapsamli `autouse` **engel modul** fixture'i (K1) + depo koku `sys.path` |
| `tests/unit/capture/test_monitors.py` | K5'in saf tarafi -- 40 test |
| `tests/unit/capture/test_service.py` | K1-K11 -- 119 test |

TDD: once kirmizi faz (`evidence/pytest-red.txt`, iki toplama hatasi:
`ModuleNotFoundError: No module named 'src.capture.service' / .monitors`,
exit 2), sonra uygulama.

## Bes kabul komutu -- hepsi gercekten kosuldu

| # | Komut | Cikis | Kanit |
|---|---|---|---|
| 1 | `mypy --strict --explicit-package-bases` | **0** | `evidence/mypy.txt` (Success: no issues found in 2 source files) |
| 2 | `pytest test_service.py test_monitors.py -q` | **0** | `evidence/pytest.txt` (**159 passed**) |
| 3 | `python .agents/tasks/T-005/headless_check.py` | **0** | `evidence/headless.txt` (TEMIZ) |
| 4 | `pytest ... --cov-fail-under=95` | **0** | `evidence/cov.txt` (monitors %100, service %99, **TOPLAM %98.83**) |
| 5 | `pytest tests/unit/capture -q` | **0** | `evidence/pytest-capture-all.txt` (**742 passed**) |

Besinci komutun tabani sefin saydigi **583** dondurulmus testti; 583 + 159 =
**742**. Dondurulmus `test_dpi.py` / `test_change_detector.py`'de **dusen
yok** -- yeni `conftest.py` onlari etkilemiyor (`mss` kullanmiyorlar).

Butce: `evidence/budget.txt` -- 200 cagri, `Rect(0,0,600,200)`, backend
`(200,600,4)`: **medyan 0.4289 ms**, **p95 0.5078 ms** (butce 10 ms).

## K1-K13 nasil karsilandi (ozet)

- **K1** -- `conftest.py` oturum kapsamli `autouse` fixture'i `sys.modules["mss"]`'e
  bos bir `types.ModuleType("mss")` koyar; `__file__` yok, `base`/`factory` yok,
  `MSS`/`mss` cagrilinca `AssertionError`. Protokol uyumu modul sonundaki
  `_uyum_fake: CaptureBackend = FakeBackend(())` / `_uyum_mss: CaptureBackend =
  MssBackend()` satirlariyla mypy'ye dogrulatilir; `FakeBackend.grab` kendi
  govdesinde, dekoratorsuz, donusu `ImageArray`.
- **K2** -- `_seq = -1` baslar, yalnizca **basarili** yakalamada artar; uc hata
  sinifinin hicbiri tuketmez; `refresh_monitors()` sifirlamaz.
- **K3** -- `dpi_scale` hicbir kararda kullanilmaz; dort olcekte backend'e giden
  kutu birebir ayni.
- **K4** -- kirpma **her zaman** `union_bbox(monitors)`'a karsi; `monitor_index`
  girdisi karari degistirmez; `OUTSIDE` ve sifir/negatif alanda backend cagrisi **0**.
- **K5** -- `[0]` atilir, `[1:]` sirayla; `numbers.Integral` (bool haric) kabul,
  `int(v)` ile duzlestirme; bozuk sozlukte `CaptureError`, `refresh` hatasinda
  **eski kume korunur**; `monitors()` sicak yolda **hic** cagrilmaz (sayac 1 / 2).
- **K6** -- (a) 0 cagri, (b) en fazla 3 + `__cause__`, (c) 1 cagri + `__cause__ is
  None`, yeniden deneme yok; karisik (b)->(c) 2 cagri.
- **K7** -- kural **tip duzeyinde** (`isinstance(np.ndarray)`), hicbir
  `np.asarray`/`hasattr` donusumu yok; kopya **kosulsuz**, 3 ve 4 kanalda ayri
  ayri + salt-okunur kaynak vakasi.
- **K8** -- duzlestirme `capture_region`'in **girisinde**, onunde kabul kapisi;
  `dpi_scale` cagiranin, `monitor_index` hesaplanan (tam 1 kesisim -> indeks,
  degilse `-1`); `intersect` metadata'si kullanilmaz.
- **K9** -- `capture_full(i)` = `capture_region(monitors[i])` (devir), aralik disi
  (negatif dahil) -> `CaptureError`, backend cagrisi 0.
- **K10** -- `monitors()` her cagrida yeni `with mss.MSS()`; `grab()` icin **tembel**,
  tek, uzun omurlu tutamac; `close()` idempotent; `mss.mss()` **hic** cagrilmaz;
  calisma zamani `import mss` yalnizca metot govdelerinde.
- **K11** -- `test_k11_butce` medyan **ve** p95 olcup assert eder.
- **K12** -- [OLCULMUYOR], docstring'de.
- **K13** -- kapsam **%98.83**; `no cover` yalnizca uc `MssBackend` metodunda.

## Kanit

Butun ham ciktilar `.agents/tasks/T-005/evidence/` altinda ve her dosyanin
sonunda gercek `exit_code` satiri var.
