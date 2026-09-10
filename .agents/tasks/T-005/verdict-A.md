---
task: T-005
role: tester
round: 1
lens: "A -- takma ad (view/copy, paylasilan mutable durum, disaridan mutasyon)"
decision: onay
checks:
  - name: "kabul-1 mypy --strict"
    cmd: "python -m mypy --strict --explicit-package-bases src/capture/service.py src/capture/monitors.py"
    exit_code: 0
    result: "Success: no issues found in 2 source files"
    evidence: "tester_A_evidence/r1-01-mypy.txt"
  - name: "kabul-2 sahip olunan test dosyalari"
    cmd: "python -m pytest tests/unit/capture/test_service.py tests/unit/capture/test_monitors.py -q"
    exit_code: 0
    result: "159 passed"
    evidence: "tester_A_evidence/r1-02-pytest-owned.txt"
  - name: "kabul-3 headless_check"
    cmd: "python .agents/tasks/T-005/headless_check.py"
    exit_code: 0
    result: "TEMIZ (K1 engeli, mss import girisimi yok, grab icerigi, monitors kur+kapat+canli, close idempotent, Qt yok)"
    evidence: "tester_A_evidence/r1-03-headless.txt"
  - name: "kabul-4 kapsam esigi"
    cmd: "python -m pytest tests/unit/capture/test_service.py tests/unit/capture/test_monitors.py -q --cov=src.capture.service --cov=src.capture.monitors --cov-fail-under=95 --cov-report=term-missing"
    exit_code: 0
    result: "159 passed; TOTAL 171 satir, 2 eksik, %98.83 (sefin tabaniyla birebir ayni)"
    evidence: "tester_A_evidence/r1-08-cov.txt"
  - name: "kabul-5 tests/unit/capture tamami"
    cmd: "python -m pytest tests/unit/capture -q"
    exit_code: 0
    result: "742 passed (sefin tabani: 742) -- gerileme yok"
    evidence: "tester_A_evidence/r1-04-pytest-capture-all.txt"
  - name: "tum depo test paketi"
    cmd: "python -m pytest tests -q"
    exit_code: 0
    result: "981 passed (sefin tabani: 981) -- gerileme yok"
    evidence: "tester_A_evidence/r1-05-pytest-tests-all.txt"
  - name: "MERCEK A test paketi (A1-A5 + K1 oz-denetimi)"
    cmd: "python -m pytest .agents/tasks/T-005/tester_A -q"
    exit_code: 0
    result: "74 passed -- bes saldiri noktasinin hicbirinde kirik yok"
    evidence: "tester_A_evidence/r1-06-pytest-tester-A.txt"
  - name: "mutasyon denetimi -- kapilarin ayirt etme gucu"
    cmd: "PYTHONPATH=<scratch> python -m pytest .agents/tasks/T-005/tester_A -q -p mutant{1,2,3,4}"
    exit_code: 1
    result: "dort mutantin dordu de yakalandi: mutant1 (sefin tuzagi) 14 kirik ve HEPSI 3 kanal parametrelerinde; mutant2 (raw_override anlik goruntusu) 7; mutant3 (refresh once bozuyor) 2; mutant4 (kume mutable liste olarak sizdiriliyor) 5. src/ DEGISTIRILMEDI -- mutantlar calisma zamaninda -p eklentisiyle enjekte edildi."
    evidence: "tester_A_evidence/r1-07-mutasyon.txt"
  - name: "ham olcumler -- tuzak, dort yon, dondurulmusluk, modul duzeyi durum"
    cmd: "python probe_a.py; python probe_b.py; python probe_c.py"
    exit_code: 0
    result: "ascontiguousarray kanal=3 shares_memory=True / kanal=4 False (sefin tuzagi yeniden uretildi); dort yonde de shares=False, writeable=True, base=None; refresh hatasinda kume nesnesi AYNI; Rect/Frame __slots__ tasimiyor"
    evidence: "tester_A_evidence/r1-09-ham-olcumler.txt"
blocking_issues: []
notes:
  - "Sefin tuzagi kendi elimle yeniden uretildi: np.ascontiguousarray(a[:, :, :3]) 4 kanalda shares_memory=False (kopya), 3 kanalda True (TAKMA AD). Teslim bu tuzaga DUSMUYOR: _kopyala tek satirdir ve np.array(ham[:, :, :3], dtype=np.uint8, copy=True, order='C') ile kopyayi KOSULSUZ yapar."
  - "A1 -- Frame.image sahipligi dort yonde de temiz (3ch/4ch x yazilabilir/salt-okunur): shares_memory=False, may_share_memory=False, flags.writeable=True, base=None, owndata=True, C-bitisik, adimlar (30,3,1), tip tam olarak np.ndarray. Frame.image'i yerinde bozmak backend dizisini bozmuyor; backend dizisini bozmak onceki Frame'i bozmuyor."
  - "A1 ek -- dort yonun otesinde yedi egzotik kaynak da denendi ve hepsi kopyalaniyor: buyuk arenanin BITISIK gorunumu (tuzagin en sert bicimi), altinda canli/yazilabilir bellek olan salt-okunur gorunum, 0-adimli broadcast, ndarray alt sinifi, [:, :, :3] dilimlemesini yutan alt sinif, np.ma.MaskedArray, Fortran duzenli dizi. PARTIAL (kirpma) dali ve capture_full dali ayri ayri olculdu; iki Frame birbiriyle de bellek paylasmiyor."
  - "A2 -- FakeBackend.monitors() monitor_rects yolunda her cagrida YENI bir liste ve YENI sozlukler uretiyor: donen listeyi clear() etmek ya da donen sozlugu bozmak sonraki cagriyi etkilemiyor. K10 bunu kapi degil uygulama tercihi sayiyor; teslim tercihi dogru yonde kullanmis. MssBackend.monitors() de kaynakta [dict(ham) for ham in oturum.monitors] ile sigkopya aliyor -- K1 geregi kosulamadi, yalnizca okundu."
  - "A2 belgelenen asimetri (kusur DEGIL): raw_override yolunda monitors() nesnenin KENDISINI donduruyor (donen is raw_override). Bu K1'in mutasyon arayuzunun zorunlu sonucudur -- monitors() raw_override'i 'o anki haliyle' okumak zorunda. Iki yolun farkli davrandigi kayda gecirilir."
  - "A3 -- raw_override canliligi tam: public oznitelik (vars(fb) icinde), yapimda verilen nesne KOPYALANMIYOR (fb.raw_override is ov), gizli bir _raw_override yok, yapimdan sonraki atama ve YERINDE mutasyon (append/del/sozluk yazma) sonraki monitors() cagrisinda goruluyor, None'a donunce monitor_rects yoluna dusuyor (icerikle ayirt edildi, uzunlukla degil), refresh_monitors() canli degeri goruyor. Anlik goruntu alan bir uygulama (mutant2) 7 testte dusuyor."
  - "A4 -- servisin monitor onbellegi: public yol (monitors property, refresh_monitors donusu) DEGISMEZ bir demet veriyor, elemanlari dondurulmus Rect; disaridan bozulacak mutable bir yapi sizmiyor. Cagiranin elinde tuttugu demet basarili bir refresh'ten sonra da degismiyor (kararli anlik goruntu). refresh_monitors() hem bozuk sozlukte (CaptureError) hem backend'in kendi istisnasinda (RuntimeError) eski kumeyi koruyor ve kume NESNESI ayni kaliyor (is); hata sonrasi capture_region eski kumeyle dogru calisiyor. Yakalama yolu backend.monitors()'i hic cagirmiyor (25 capture_region + 1 capture_full sonrasi sayac hala 1)."
  - "A4 -- servis._monitors OZEL bir alandir; disaridan yeniden baglanirsa capture_region onu izler. Public yol degismez bir demet verdigi icin bu bir sizinti degil; mercek A'nin dorduncu maddesi sordugu icin olculdu ve kaydedildi."
  - "A5 -- Rect ve Frame'in butun alanlari (6 + 4) atamada ve silmede FrozenInstanceError veriyor; dataclasses.replace calisiyor. replace DISINDA iki yol var: ikisi de __slots__ tasimadigi icin object.__setattr__(r, 'x', 9) ve r.__dict__['y'] = 42 gecerli. Bu src/contracts/ sozlesmesinin ozelligidir (T-005'in degil, dondurulmus dosya) ve T-005'i baglamaz -- bilgi olarak kaydedilir."
  - "A5 -- Frame.image compare=False oldugu icin esitlik goruntuyu HIC gormuyor: siyah bir kare ile beyaz bir kare, ayni rect/captured_at/seq ile ESIT ve HASH'leri ayni. Yani bir sahiplik gerilemesi '==' ile OLCULEMEZ. Bu yuzden mercek A'nin butun iddialari shares_memory / may_share_memory / flags / array_equal uzerine kuruldu, hicbiri '==' uzerine degil."
  - "A5 -- frozen=True Frame.image'in ICERIGINI korumuyor (K7 zaten writeable=True istiyor): dondurulmus bir Frame'in goruntusu yerinde degistirilebiliyor ve '==' bunu gormuyor. Servis her kareye kendi kopyasini verdigi icin bu T-005'in disindadir; asagi akista (A6 pipeline) iki asama ayni Frame'i tutarsa gecerli bir tehlikedir. Kaydedilir."
  - "A5 -- backend'e giden Rect ile Frame.rect AYNI nesne (fb.grab_rects[-1] is kare.rect). Rect dondurulmus oldugu icin zararsiz: paylasim var, mutable degil. Cagiranin verdigi Rect ise tasinmiyor (kare.rect is not giris) -- giristeki duzlestirme yeni bir nesne kuruyor."
  - "Modul duzeyinde paylasilan mutable durum: _uyum_fake process genelinde tek bir FakeBackend ornegidir (grab_rects listesi ve sayaclari modul omru boyunca yasar) ve _uyum_mss tek bir MssBackend ornegidir. Ikisi de K1/O-F geregi ZORUNLU ve K10 'MssBackend() yapimi zararsizdir' diyor; olcum dogruluyor: _uyum_mss._tutamac is None, _uyum_fake sayaclari 0. Kullanilmadiklari surece zararsiz; kaydedilir."
  - "Kendi test paketim K1'e uyuyor: tester_A/conftest.py bagimsiz bir engel modul kuruyor (uygulamanin conftest'inden referans turetmiyor) ve paket kendi engelini test ediyor -- import mss -> __file__ yok, base yok, MSS()/mss() AssertionError."
  - "Kirilganlik uyarisi (kapi degil): teslimin sahiplik ölcusu tek bir satira (_kopyala) baglidir ve o satirda np.array(..., copy=True) yerine ascontiguousarray yazan bir gelecek duzenleme, uygulamanin KENDI test paketinde yalnizca 3 kanalli vakalarda duser. Uygulamanin test_k7_sahiplik_3kanal testi bu vakayi kapsiyor, yani tuzak bugun aciktir; ancak salt-okunur vaka yalnizca 4 KANALLA yazilmis (test_k7_sahiplik_salt_okunur_kaynak). Dort yonun 3ch-salt-okunur kosesi uygulamanin paketinde YOK; benim paketimde var. Bu bir ret gerekcesi degildir (degismez bugun saglaniyor ve 3 kanal ayri olculuyor), ilerisi icin kayittir."
  - "src/, tests/ ve .agents/tasks/T-005/headless_check.py DEGISTIRILMEDI -- git status: izlenen hicbir dosyada degisiklik yok, yalnizca tester_A/ ve tester_A_evidence/ yeni."
---

# MERCEK A -- karar: ONAY

## Ozet

Mercek A'nin bes saldiri noktasinin **hicbirinde kirik bulunamadi**. Sefin
tabani birebir yeniden uretildi (`tests/unit/capture` -> 742 passed,
`tests` -> 981 passed, kapsam %98.83, bes kabul komutu exit 0) ve mercege
ozel 74 test yazildi; hepsi gecti.

Sahiplik degismezi (K7) tek bir satirda toplaniyor:

```python
return np.array(ham[:, :, :3], dtype=np.uint8, copy=True, order="C")
```

`copy=True` kopyayi **kosulsuz** yapar; sefin olctugu tuzak
(`np.ascontiguousarray(arr[:, :, :3])`) bu satirda yok. Tuzagi kendi elimle
yeniden urettim (`r1-09-ham-olcumler.txt`):

```
ascontiguousarray kanal=3: shares_memory=True  owndata=False
ascontiguousarray kanal=4: shares_memory=False owndata=True
arena-view ascontiguousarray: True
```

## Kapilarimin ayirt etme gucu -- mutasyon denetimi

Kendi kapilarimin bir sey olctugunu kanitlamak icin dort mutanti **calisma
zamaninda** (`-p` eklentisi; `src/` diskte degistirilmedi) enjekte ettim:

| Mutant | Ne bozuldu | Yakalanan test |
|---|---|---|
| 1 | `_kopyala` -> sefin tuzagi | **14** -- ve hepsi **3 kanal** parametrelerinde |
| 2 | `raw_override` yapimda dondurulur | 7 |
| 3 | `refresh_monitors` kumeyi donusumden once bozar | 2 |
| 4 | monitor kumesi mutable `list` olarak sizdirilir | 5 |

Mutant 1'in kirik listesi merceğin cekirdek iddiasini dogruluyor: **yalniz
4 kanalli bir sahiplik testi yesil kalirdi** (`[4ch-yazilabilir]` ve
`[4ch-salt-okunur]` parametreleri mutant altinda bile geciyor).

## Bulunan kirik

Yok. `blocking_issues` bos, `feedback-A.md` yazilmadi.

## Kayda gecen gozlemler

Kirik olmayan ama merceğin sorusunun dogru cevabini olusturan gozlemler
yukaridaki `notes` alanindadir. Ozetle:

1. **Kopya gercekten kopya** -- dort yonde ve yedi egzotik kaynakta.
2. **`monitors()` donusu** `monitor_rects` yolunda her cagrida yeni;
   `raw_override` yolunda **canli nesnenin kendisi** (K1 boyle istiyor).
3. **`raw_override` canli**, public, yapimda dondurulmuyor.
4. **Onbellek** public yoldan bozulamiyor; `refresh` hatasinda **ayni nesne**
   kaliyor.
5. **`Rect`/`Frame` dondurulmus** ama `__slots__` yok -- `object.__setattr__`
   ve `__dict__` acik kapi (sozlesme dosyasinin ozelligi, T-005'in degil);
   ve `compare=False` yuzunden **esitlik goruntuyu hic gormuyor**, bu yuzden
   sahiplik `==` ile olculemez.
