---
task: T-005
role: tester
round: 1
decision: onay
checks:
  - name: "mypy --strict temiz (kabul #1)"
    cmd: "python -m mypy --strict --explicit-package-bases src/capture/service.py src/capture/monitors.py"
    exit_code: 0
    result: gecti
    evidence: tester_C_evidence/r1-01-mypy.txt
  - name: "sahibin test dosyalari (kabul #2) -- 159 passed"
    cmd: "python -m pytest tests/unit/capture/test_service.py tests/unit/capture/test_monitors.py -q"
    exit_code: 0
    result: gecti
    evidence: tester_C_evidence/r1-02-pytest-service-monitors.txt
  - name: "headless_check.py (kabul #3) -- K1 engeli, tembel import, casus MssBackend, Qt yok"
    cmd: "python .agents/tasks/T-005/headless_check.py"
    exit_code: 0
    result: gecti
    evidence: tester_C_evidence/r1-03-headless.txt
  - name: "tests/unit/capture tumu (kabul #5) -- 742 passed, sefin tabaniyla ayni"
    cmd: "python -m pytest tests/unit/capture -q"
    exit_code: 0
    result: gecti
    evidence: tester_C_evidence/r1-04-pytest-capture.txt
  - name: "MERCEK C testleri -- 122 passed (seq matrisi, K6 dizileri, kume durumu, MssBackend omru)"
    cmd: "python -m pytest .agents/tasks/T-005/tester_C -q"
    exit_code: 0
    result: gecti
    evidence: tester_C_evidence/r1-05-pytest-tester-C.txt
  - name: "tum depo regresyonu -- 981 passed, sefin tabaniyla ayni"
    cmd: "python -m pytest tests -q"
    exit_code: 0
    result: gecti
    evidence: tester_C_evidence/r1-06-pytest-tum-depo.txt
  - name: "kendi kapilarimin mutasyon denetimi -- 18/18 mutasyon oldu"
    cmd: "python <scratch>/mutasyon.py"
    exit_code: 0
    result: gecti
    evidence: tester_C_evidence/r1-07-mutasyon.txt
  - name: "MERCEK C testleri BASKA calisma dizininden -- 122 passed"
    cmd: "cd C:/ && python -m pytest \"<depo>/.agents/tasks/T-005/tester_C\" -q"
    exit_code: 0
    result: gecti
    evidence: tester_C_evidence/r1-08-baska-cwd.txt
  - name: "MERCEK C ayrintili dokum (test adi basina sonuc)"
    cmd: "python -m pytest .agents/tasks/T-005/tester_C -v"
    exit_code: 0
    result: gecti
    evidence: tester_C_evidence/r1-09-tester-C-ayrintili.txt
  - name: "ham kesif sondalari (seq matrisi / kume gecisleri / casus omur olcumleri)"
    cmd: "python probe_c1.py; python probe_c2.py; python probe_c3.py"
    exit_code: 0
    result: gecti
    evidence: tester_C_evidence/r1-10-ham-sondalar.txt
blocking_issues: []
notes: |
  MERCEK C -- durum makinesi (cagri sirasi, sifirlama, ulasilamayan durum).
  env.md'nin yedi saldiri noktasinin yedisi de kosuldu; kirik BULUNAMADI.
  122 yeni test `.agents/tasks/T-005/tester_C/` altinda; ic karar ve gozlem
  raporun govdesinde.
---

# MERCEK C · Durum makinesi — T-005 tur 1

**Karar: onay.** Yedi saldiri noktasinin hicbirinde degismez ihlali bulamadim.
Asagidaki her sayi bu makinede kendi elimle koşturuldu; ham ciktilar
`tester_C_evidence/` altinda.

## Taban dogrulamasi

Sefin bildirdigi taban birebir ureildi: kabul komutlarinin hepsi exit 0,
`tests/unit/capture` → **742 passed**, `tests` → **981 passed**. `src/`,
`tests/` ve `headless_check.py` **degistirilmedi** (`git diff --stat` bos).

## Kosulan saldiri noktalari

### 1 · `seq` tam matrisi (K2)

Alfabe `{S = basari, a = K6(a), b = K6(b), c = K6(c), R = refresh_monitors()}`
uzerinde uzunluk **1, 2, 3 ve 4**'un **butun** permutasyonlari — 5+25+125+625 =
**780 dizi** — kosuldu. Her dizide gorulen `seq` listesi
`range(dizideki basari sayisi)`'na birebir esitlendi. **780/780 gecti**:
uc hata sinifinin hicbiri `seq` tuketmiyor, `refresh` sifirlamiyor, kayma yok.
(`test_c1_seq_tam_permutasyon_matrisi`, `test_c1_seq_permutasyon_uzunluk_4`)

Ustune 500 olayluk **deterministik rastgele yuruyus** (tohum `20260910`) —
kume kucultme/buyutme, bos kumeye dusup geri donme, bozuk sozlukle basarisiz
`refresh`, `capture_full` aralik disi cagrilari dahil — sayac bir kez bile
atlamadi (`test_c1_uzun_rastgele_yuruyus`). Ayrica: 100 ardisik `refresh`
sayaca dokunmuyor; ayni backend'le kurulan ikinci servis `0`'dan basliyor ve
**ilk ornegi etkilemiyor**; `capture_full` ile `capture_region` **tek** sayaci
paylasiyor; 1000 ardisik yakalamada `0..999` kesintisiz.

**Paketin adini koymadigi bir (a) kapisi:** K8'in giris kabul kapisi
(`'10'` / `True` / `10.9` / `nan` / `inf`) da `seq` tuketmiyor ve backend'i
cagirmiyor — depodaki `test_k8_giris_*` yalnizca `CaptureError` firlatildigini
olcuyor, sayaca ve `grab_calls`'a bakmiyor (`test_c1_giris_kabul_kapisi_seq_tuketmez`).

### 2 · K6'nin 3×3 matrisi + karisik diziler

Dokuz hucrenin dokuzu de dolu; ustune sekiz dizi:

| dizi | grab cagrisi | sonuc | `seq` | `__cause__` | `__context__` |
|---|---|---|---|---|---|
| `a` (OUTSIDE) | 0 | CaptureError | tuketmez | `None` | `None` |
| `c` | 1 | CaptureError | tuketmez | `None` | `None` |
| `b→b→b` | 3 | CaptureError | tuketmez | `RuntimeError("istisna-3")` | `None` |
| `b→b→basari` | 3 | Frame | 0 | — | — |
| `b→basari` | 2 | Frame | 0 | — | — |
| `b→c` | 2 | CaptureError | tuketmez | `None` | `None` |
| `b→b→c` | 3 | CaptureError | tuketmez | `None` | `None` |
| `c→b` | 1 | CaptureError | tuketmez | `None` | `None` |

Uc ayirt edici olcu ekledim:

* **`__cause__` SON istisnadir, ilk degil.** Depodaki `test_k6_b_cause` hep ayni
  mesajla firlatan bir uretici kullaniyor, yani ilk ile son istisnayi ayirt
  **edemiyor**. Uretici her denemede farkli mesaj verince `"istisna-3"` cikti —
  dogru. (Bu olcu `M6_ilk_istisna_baglanir` mutasyonunu oldurdu; depodaki olcu
  oldurmezdi.)
* **`__context__` de olculdu.** `__cause__ is None` tek basina zayiftir: bicim
  dogrulamasi bir `except` govdesinin **icinde** yapilsaydi `__cause__` yine
  `None` kalir, `__context__` `RuntimeError` olurdu ve traceback iki hatayi
  birlikte gosterirdi. Olculdu: `b→c` ve `b→b→c` dizilerinde ikisi de `None`.
* **Mesajdaki `3` totoloji degil.** Depodaki olcu `Rect(11,22,33,44)` kullaniyor
  ve `"3" in mesaj` iddiasi zaten `33`'ten saglaniyor. `Rect(11,22,44,55)` ile
  koştum; `3` yalnizca deneme sayisindan geliyor.

`c` sinifinin **terminalligi** yapisal olarak dolu bir hucredir: ikinci
denemede duzelen bir uretici bile **cagrilmiyor** (`grab_calls == 1`).
Deneme sayaci **cagri basina** sifirlaniyor: tukenen bir (b)'den sonraki cagri
yine tam 3 deneme aliyor. Dorduncu denemede duzelen backend'e sira gelmiyor.

**Kayda gecen:** `except Exception` kullanildigi icin `KeyboardInterrupt`
yeniden **denenmiyor** ve `CaptureError`'a sarmalanmiyor — kullanicinin Ctrl+C'si
uc kez yeniden denenip donmus bir uygulama uretmiyor. Paket bunu yazmiyor;
dogru davranis, olcusu eklendi.

### 3 · Bos monitor kumesi

Servis **kuruluyor**. Bes ayri bolge (INSIDE/PARTIAL/OUTSIDE/1×1/birlesim) ve
bes `capture_full` indeksi (`-99, -1, 0, 1, 99`) icin: hepsi `CaptureError`,
**backend cagrisi 0**. 50 tur `capture_region` + `capture_full` sonrasi
`monitors_calls` hala **1** — bos kumede bile sicak yol backend'e donmuyor.
Dolu → bos → dolu gecisinde `seq` ne sifirlaniyor ne atliyor. Bos kumeyle
**kurulan** servis `refresh_monitors()` ile calisir hale geliyor.
`raw_override = []` (girdi hic yok) da `()` veriyor, hata degil.

### 4 · `refresh_monitors()` hata yolu

**Yedi ayri bozuk sozluk** (anahtar eksik · `None` · `str` · `bool` · `float` ·
`np.bool_` · ikinci monitorde bozukluk) icin ayni sey olculdu: `CaptureError`
firliyor, `monitors_calls` **artiyor** (backend gercekten cagrildi), eski kume
**birebir korunuyor** ve **sonraki `capture_region` eski kumeyle dogru
calisiyor** — PARTIAL kirpmasi `(-2560, 0, 60, 100)`, `monitor_index == 0`,
`seq` tuketilmemis. Ardisik bes basarisiz `refresh` de kumeyi bozmuyor;
`capture_full` da etkilenmiyor.

Bu, "once ata sonra dogrula" hatasinin tek ayirt edici olcusudur:
`M2_refresh_once_atar_sonra_dogrular` mutasyonu tam burada oldu.

Ayrica: `backend.monitors()`'in **kendi** istisnasi (surucu/DC hatasi)
`CaptureError`'a **sarmalanmiyor**, oldugu gibi yayiliyor — hem `refresh`'te
hem yapimda (K5) — ve o durumda da eski kume korunuyor.

### 5 · Kume degisimi

**Sira degisimi** bes bolge tipinde ayri ayri olculdu (PARTIAL sol, PARTIAL ust,
INSIDE sag, INSIDE sol, INSIDE iki monitore yayilan): kirpma geometrisi
**degismiyor**, backend'e giden kutu **birebir ayni**, `dpi_scale` korunuyor;
degisen tek sey `Frame.rect.monitor_index` (`0↔1`, yayilanda `-1` sabit).

**Sayi degisimi**: 2→1'de sol monitordeki bolge OUTSIDE oluyor (backend
cagrilmiyor), yayilan bolge PARTIAL'a dusup `(0,0,50,100)`'e kirpiliyor, sag
bolge etkilenmiyor. 1→3'te indeksler yeniden numaralaniyor ve `capture_full(2)`
dogru monitoru veriyor. Kume 2→1 olunca `capture_full(1)` **aralik disi**
oluyor. Butun bu gecisler `seq`'e dokunmuyor.

### 6 · `MssBackend` omru

K1 geregi test paketi gercek `mss`'e dokunamaz; `headless_check.py` §3'un
yontemiyle **alt surecte sayacli bir casus modul** kurdum (casus gercek `mss`
gibi: `monitors` ornek uzerinde memoize, `close()` idempotent,
`ScreenShot.__array_interface__` ham tampon tasiyor). `headless_check` §3'un
**olcmedigi** gecisleri olctum:

* **Sefin olctugu olum noktasinda:** `monitors()` **5001** kez cagrildi →
  `MSS()` kurulumu **5001**, kapatma **5001**, sizinti **0** ve — asil olcu —
  **ayni anda acik ornek sayisinin zirvesi 1'i asmadi**. Toplam sayacin
  esitlenmesi yetmezdi: en sonda toplu kapatan bir uygulama da esitlerdi ama
  arada 5001 DC'yi acik tutardi. 5001 `monitors()` sonrasi `close()` kapatacak
  bir sey bulmuyor (`monitors` uzun omurlu tutamaci kurmuyor).
* **`close()` sonrasi `grab()`:** kapali tutamac **yeniden kullanilmiyor**
  (gercek `mss` "kapatilan MSS tekrar kullanilamaz" der — `mss/base.py`);
  uygulama yeni bir tutamac kuruyor ve o da kapaniyor, sizinti 0. Paket bu
  gecisi tanimlamiyor; davranis dogru ve olcusu eklendi.
* **Ic ice `with`:** `MssBackend` yeniden girisli (reentrant) **degil** — ic
  cikis tutamaci kapatiyor, dis bloktaki sonraki `grab()` sessizce yeni tutamac
  kuruyor, dis cikis onu kapatiyor. Cokme yok, **sizinti yok**, yalnizca bir
  kurulum maliyeti. Paket ic ice kullanimi tanimlamiyor.
* **`with` govdesinde istisna:** `__exit__` `None` donduruyor → istisna
  **yutulmuyor** ve tutamac kapaniyor.
* **Tembellik:** `grab` yapilmadan `close()`/`with` → `MSS` kurulumu 0.
* **Bagimsizlik:** araya giren `monitors()` cagrisi uzun omurlu `grab`
  tutamacini ne kapatiyor ne de sonraki `grab`'i yeni kuruluma zorluyor.
* **Canlilik:** casusun listesi 3→2→3 degistiginde her cagri yenisini goruyor;
  donen listeyi bozmak sonraki cagriyi kirletmiyor.

### 7 · `capture_full` indeks araligi

Sekiz aralik disi deger (`-100, -3, -2, -1, 2, 3, 99, 1000`): hepsi
`CaptureError`, **backend cagrisi 0**, `__cause__ is None`, mesajda hem indeks
hem kume boyutu, `seq` korunuyor. Negatif indeksleme **bilerek devre disi**:
`capture_full(-1)` son monitoru vermiyor. `n = 1, 2, 3, 5` monitorlu kumelerde
`0..n-1` gecerli / `-1, n, n+1` gecersiz sinirlari ayri ayri kosuldu.
`width=0` tasiyan ham sozlukle kurulan monitor kumeye giriyor ama
`capture_full(0)` "bolgenin alani yok" ile duşuyor ve backend cagrilmiyor.
100 tur `capture_full` sonrasi `monitors_calls` hala 1.

## Kendi kapilarimi denetledim (PROTOKOL §4.6/7-8)

Testlerimin totoloji olmadigini **olctum**: `src/` ve `tester_C/` gecici bir
koke kopyalandi (depo dokunulmadi), kopyada teker teker **18 mutasyon**
uygulandi ve yalnizca `tester_C` kosuldu. **18/18 mutasyon oldu** —
`seq`'i hatada da tuketen, `refresh`'te once atayan, `refresh`'te `seq`'i
sifirlayan, (c)'yi yeniden deneyen, deneme sayisini 5 yapan, ILK istisnayi
baglayan, negatif indekslemeye izin veren, `len`'i kabul eden, `monitor_index`'i
cagirandan alan, tek monitore kirpan, `mss` oturumunu kapatmayan, her `grab`'de
yeni `MSS` kuran, `close`'u idempotanttan cikaran, `monitors`'i onbellekleyen,
`__exit__`'te istisnayi yutan, yapim hatasini bos kumeye ceviren, giris kapisini
kaldiran ve bos kume denetimini silen varyantlarin **hepsi** en az bir kapida
duştu (`tester_C_evidence/r1-07-mutasyon.txt`).

18. mutasyon ilk turda **hayatta kalmisti** ve bu bir bulgudur: bos kume
denetimi (`if not self._monitors`) **davranissal olarak gereksizdir** —
silindiginde `classify_region(rect, ())` zaten OUTSIDE veriyor, `CaptureError`
yine firliyor ve backend yine cagrilmiyor; olculdu, iki durum `Rect(0,0,10,10)`
icin **birebir ayni mesaji** veriyor. Yani o savunma satirini koruyan tek sey
tanisal mesajdir. Kapiyi ayirt edici hale getirmek icin "bos kume mesaji
OUTSIDE mesajindan farkli olmali" olcusunu ekledim (icerigi degil, yalnizca
farkli olmasi aranir). **Bu, paketin lafzinin bir adim otesidir ve bilincli
bir tester karari olarak bildirilir** (PROTOKOL §6); ret gerekcesi degildir,
uygulama zaten sagliyor.

Testlerim ayrica **baska bir calisma dizininden** de kosuyor (`cd C:/`);
kendi `conftest.py`'m depo kokunu `parents[4]` ile buluyor ve K1 engelini
yeniden kuruyor — bu dizin `tests/` altinda olmadigi icin depodaki engel
buraya ulasmiyor.

## Ret gerekcesi olmayan, kayda gecen gozlemler

Hicbiri degismez ihlali degildir; degisirlerse gorunsun diye olcu altina alindi.

1. **Saat istisnasi `seq` tuketir (taksonomi disi).** `capture_region`
   `self._seq += 1` satirini `Frame(...)` kurulumundan **once** calistirir;
   `captured_at=self._clock()` ise arguman olarak sonra degerlendirilir. Enjekte
   edilen saat firlatirsa sayac tuketilir ama `Frame` dogmaz. K6'nin uc sinifinin
   **disindaki** tek `seq` sizinti yolu budur ve paket bu yolu tanimlamaz
   (`clock` cagirandan gelir, varsayilan `time.monotonic` firlatmaz). Olculdu:
   0 → RuntimeError → **2** (1 atlandi).
   `test_c1_saat_istisnasi_seq_TUKETIR_taksonomi_disi`
2. **`close()` alttaki tutamac firlatirsa idempotan degil.** `self._tutamac =
   None` atamasi yalnizca basarili kapatmadan **sonra** yapiliyor, bu yuzden
   ikinci `close()` de firlatiyor. **Gercek `mss` bu durumu uretmez** —
   `mss/base.py`'nin `close()`'u kendi icinde idempotenttir ve "safe to call
   this multiple times" der — ve yeniden deneme imkani vermek savunulabilir bir
   tercihtir. `test_c6_tutamacin_close_u_firlarsa_idempotans_KAYBOLUR`
3. **`MssBackend` yeniden girisli degil.** Ic ice `with`'te ic cikis tutamaci
   kapatir; dis bloktaki sonraki `grab()` yeni tutamac kurar. Sizintisiz ve
   cokmesiz, ama bir kurulum maliyeti odetir. Paket ic ice kullanimi tanimlamaz.
   `test_c6_ic_ice_with_ic_cikista_tutamaci_KAPATIR`
4. **Sira degisimi `capture_full`'un fiziksel hedefini kaydirir.** `refresh`
   sonrasi `capture_full(0)` `x=-2560` yerine `x=0` veriyor. Bu, K5'in
   `known_gaps`'e yazdigi "monitor kimligi konumsal ve kararsiz" eksikliginin
   **gozlemlenebilir yuzudur**; belgelenmis bir sinirin olcusudur.
   `test_c5_sira_degisimi_capture_full_un_HEDEFINI_degistirir`
5. **`capture_full(True) == capture_full(1)`.** `bool` `int` alt sinifi ve
   `0 <= i < n` karsilastirmasi onu `1` olarak kabul ediyor. K5/K8 girislerinde
   `bool` acikca reddediliyor; `capture_full`'un indeksi icin paket kural
   yazmiyor. Zararsiz (indeks disaridan gelen kullanici degeri degil).
   `test_c7_capture_full_bool_indeksi`
6. **Bos kume denetimi davranissal olarak gereksiz** (yukarida, mutasyon M18).

## Kapsam disi biraktiklarim

`Frame.image` sahipligi/takma ad, sayisal tip sizintisi ve kirpma aritmetiginin
sayisal dogrulugu bu merceğin disindadir; yalnizca durum gecislerini etkiledigi
noktalarda (kirpma geometrisinin sira degisiminde sabit kalmasi gibi) olculdu.
K12 (thread guvenligi) paket geregi `[OLCULMUYOR]`; tek worker thread
varsayimini bu mercek de sinamadi.

## Dosyalar

* `.agents/tasks/T-005/tester_C/conftest.py` — K1 engeli + `sys.path`
* `.agents/tasks/T-005/tester_C/_ortak.py` — ortak kurulum (gercek duzen, `Yonlendirici`, `sirali_uretici`)
* `.agents/tasks/T-005/tester_C/test_c_seq_matrisi.py` — 14 test (saldiri noktasi 1)
* `.agents/tasks/T-005/tester_C/test_c_k6_matrisi.py` — 29 test (saldiri noktasi 2)
* `.agents/tasks/T-005/tester_C/test_c_kume_durumu.py` — 62 test (saldiri noktalari 3, 4, 5, 7)
* `.agents/tasks/T-005/tester_C/test_c_mss_omru.py` — 17 test (saldiri noktasi 6)
* `.agents/tasks/T-005/tester_C_evidence/` — 10 kanit dosyasi + mutasyon ve sonda kaynaklari

`src/`, `tests/` ve `headless_check.py` **degistirilmedi**.
