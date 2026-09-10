---
task: T-005
role: tester
round: 2
decision: ret
checks:
  - name: "kabul #1 -- mypy --strict temiz"
    cmd: "python -m mypy --strict --explicit-package-bases src/capture/service.py src/capture/monitors.py"
    exit_code: 0
    result: gecti
    evidence: tester_D_evidence/r2-01-mypy.txt
  - name: "kabul #2 -- sahipli iki test dosyasi: 163 passed (sefin tabani birebir)"
    cmd: "python -m pytest tests/unit/capture/test_service.py tests/unit/capture/test_monitors.py -q"
    exit_code: 0
    result: gecti
    evidence: tester_D_evidence/r2-02-pytest-owned.txt
  - name: "kabul #3 -- headless_check.py TEMIZ"
    cmd: "python .agents/tasks/T-005/headless_check.py"
    exit_code: 0
    result: gecti
    evidence: tester_D_evidence/r2-03-headless.txt
  - name: "kabul #4 -- tests/unit/capture 746 passed, kapsam %98.83 (171 ifade / 2 eksik)"
    cmd: "python -m pytest tests/unit/capture -q --cov=src.capture.service --cov=src.capture.monitors --cov-fail-under=95 --cov-report=term-missing"
    exit_code: 0
    result: gecti
    evidence: tester_D_evidence/r2-04-cov.txt
  - name: "kabul #5 -- tam takim 985 passed"
    cmd: "python -m pytest tests -q"
    exit_code: 0
    result: gecti
    evidence: tester_D_evidence/r2-05-pytest-all.txt
  - name: "D2-1a -- sefin dort mutanti: M12/M13/M37/M44 DORDU DE yakalandi ([.X.XX])"
    cmd: "python .agents/tasks/T-005/tester_D/mutant_kiti.py M12 M13 M37 M44"
    exit_code: 0
    result: gecti
    evidence: tester_D_evidence/r2-08-sef-kapi-mutantlari.txt
  - name: "D2-1b BLOKE -- YENI mutant dalgasi (8): M50/M51/M56/M57 yakalandi, M52 kontrol dogru kacti, M54 yalniz §3'e takildi, M53 ve M58 BES KAPIDAN DA GECTI"
    cmd: "python .agents/tasks/T-005/tester_D/mutant_kiti_tur2.py"
    exit_code: 0
    result: kaldi
    evidence: tester_D_evidence/r2-09-mutant-dalga-tur2.txt
  - name: "D2-1c -- onerilen duzeltmenin AYIRT ETME GUCU: taban 164 passed, M53 1 failed, M12/M50 2 failed"
    cmd: "python .agents/tasks/T-005/tester_D/t2_onerilen_duzeltme_gucu.py"
    exit_code: 0
    result: gecti
    evidence: tester_D_evidence/r2-16-onerilen-duzeltme-gucu.txt
  - name: "D2-2 -- totoloji sondasi: enjekte edilen `_tutamac` uretimin yazdigi alan mi (M54) + `(h,w,4)` ve `type(x) is int` iddialarinin uretim yolu"
    cmd: "python -m pytest .agents/tasks/T-005/tester_D/test_d5_bos_olcum_noktalari.py .agents/tasks/T-005/tester_D/test_d6_totoloji.py -q"
    exit_code: 0
    result: gecti
    evidence: tester_D_evidence/r2-15-tester-D-kiti-tur2.txt
  - name: "D2-3a -- docstring'in UC zarar kipi ve IKI sayisi BAGIMSIZ olculdu: gurultulu red, sessiz yanlis (w=60 vs w=200), K6 disi ciplak OverflowError; uint32/uint64 icin 6480'in 1108'i SESSIZ + 240'i gecersiz-kabul (birebir tutuyor)"
    cmd: "python .agents/tasks/T-005/tester_D/t2_docstring_olcumu.py"
    exit_code: 0
    result: gecti
    evidence: tester_D_evidence/r2-10-docstring-tasma-olcumu.txt
  - name: "D2-3b BLOKE -- docstring'in OLUMSUZ iddiasi ('kenardan uzak / derin INSIDE bolgelerde dort tipte de ayrisma SIFIRDIR') OLCUMLE YANLIS: 64/1408 ayrisma, aile `x == w`, kenara uzaklikla ilgisiz"
    cmd: "python .agents/tasks/T-005/tester_D/t2_docstring_olcumu2.py"
    exit_code: 0
    result: kaldi
    evidence: tester_D_evidence/r2-11-docstring-sifir-iddiasi.txt
  - name: "D2-3c -- en guclu karsi ornek: Rect(1000,600,1000,200) her kenardan >=560 px uzak, INSIDE, ham uint16/32/64'te CaptureError; TEK monitorlu duzende ayrisma 0 (kaynak M0'in -2560'i)"
    cmd: "python -X utf8 <derin-inside karakterizasyonu>"
    exit_code: 0
    result: kaldi
    evidence: tester_D_evidence/r2-13-en-guclu-karsi-ornek.txt
  - name: "D2-3d -- ayrisan (x,w) ailesinin karakterizasyonu ve tek-monitor kontrolu"
    cmd: "python -X utf8 <derin-inside grid taramasi>"
    exit_code: 0
    result: kaldi
    evidence: tester_D_evidence/r2-12-derin-inside-ayrisma-karakterizasyonu.txt
  - name: "D2-4 -- kapsam ve pragma: tam 3 pragma (ucu de izinli metotta, ucu de gerekce yorumlu), gizli exclude_lines yok, kapsam tur 1 ile BIREBIR AYNI (171/2/%98.83); '%99' yuvarlanmis gosterim"
    cmd: "grep -rn pragma src/capture/ + kapsam karsilastirmasi"
    exit_code: 0
    result: gecti
    evidence: tester_D_evidence/r2-07-kapsam-pragma.txt
  - name: "D2-5 -- `known_gaps` x docstring: celiski YOK; ama olculmemis 'sifir' cumlesi YALNIZ docstring'de (known_gaps o genellemeyi yapmiyor)"
    cmd: "python -X utf8 <delivery.md'nin YALNIZCA known_gaps alani ayristirildi>"
    exit_code: 0
    result: kaldi
    evidence: tester_D_evidence/r2-14-known-gaps-vs-docstring.txt
  - name: "mercek D kiti -- tur 1 bayatligi: BEKLENEN UC kirik, dorduncu YOK (3 failed / 94 passed)"
    cmd: "python -m pytest .agents/tasks/T-005/tester_D -q"
    exit_code: 0
    result: gecti
    evidence: tester_D_evidence/r2-06-tester-D-bayat.txt
  - name: "mercek D kiti -- YENIDEN NISANLANMIS hali: 113 passed, 2 xfailed (= iki tur 2 bulgusu)"
    cmd: "python -m pytest .agents/tasks/T-005/tester_D -q -rxX"
    exit_code: 0
    result: gecti
    evidence: tester_D_evidence/r2-15-tester-D-kiti-tur2.txt
  - name: "src/ ve tests/ DEGISTIRILMEDI (mutantlar depo DISINDAKI ayna agacinda kosuldu)"
    cmd: "git status --short -- src tests"
    exit_code: 0
    result: gecti
    evidence: tester_D_evidence/r2-17-son-durum.txt
blocking_issues:
  - "D-2.1 · K10'un `__exit__` -> `close()` degismezi ISTISNA YOLUNDA hala olculmuyor. Tur 2'de eklenen `test_k10_exit_uzun_omurlu_tutamaci_kapatir` yalnizca TEMIZ cikisi kosuyor. `__exit__`'i `if not _ or _[0] is None: self.close()` yapan mutant (M53) BES kabul komutundan da exit 0 aliyor (r2-09: `M53 [.....]`). Bu tam olarak tur 1'de bloke edilen M12'nin zarar sinifidir -- her sizan `with` blogu bir window DC + memory DC birakir ve K10'un kendi olcumune gore 5001. kapatilmamis ornekte `GetWindowDC` KALICI olarak duser -- ama simdi yalnizca hata yolunda. Ve `with MssBackend() as b:` govdesinin istisnayla bitmesi urunun ISTISNAI degil NORMAL yoludur: K6 sinif (b) ve (c) `CaptureError` uretir, `capture_region` onu cagirana yayar. PROTOKOL §4.6/7 (davranissal olcu uzayin en az IKI noktasinda kosar) ihlali; `[OLCULMUYOR]` damgasi da yok (§4.6/2). Sefin tur 2 karari 'T2-1 sinifi tests/ katmaninda kapaniyor' diyor -- olcum bunu curutuyor: sinifin istisna yarisi acik. Uygulama DOGRU (pozitif kontrol: `test_d5_TUR2_uygulama_ISTISNA_yolunda_da_kapatiyor` -- casus mss ile istisnali `with` blogunda kapatma sayaci 1, `_tutamac is None`); kusur KAPIDA. Duzeltme tek test, +25 satir, yalniz `tests/unit/capture/test_service.py`; ayirt etme gucu OLCULDU (r2-16): taban 164 passed, M53 1 failed, M12 ve M50 2 failed. Hazir kod feedback-D.md'de. Yeniden uretim: `python .agents/tasks/T-005/tester_D/mutant_kiti_tur2.py M53`."
  - "D-2.2 · `capture_region` docstring'i (tur 2'de degisen TEK `src/` kalemi) OLCULMEMIS ve OLCUMLE YANLIS bir OLUMSUZ iddia tasiyor: 'Kenardan uzak (derin INSIDE) bolgelerde ise dort tipte de ayrisma **sifirdir** -- tasma yalnizca monitor sinirlarina yaklasan bolgelerde gozlemlenebilir hale gelir.' Olctum (r2-11, r2-12, r2-13): derin INSIDE grid'de (x 100..1100, y 100..800, w/h in {1,50,200,500}; hepsi M1'in tamamen icinde) uint16/uint32/uint64 icin 1408 kombinasyonun **64'u** ayrisiyor, uint8 icin 36'nin **6'si**. En guclu karsi ornek: `Rect(1000, 600, 1000, 200)` -- M1'in icinde, en yakin monitor kenarina 560 px (sag), 600 px (ust), 640 px (alt), M0/M1 dikisine 1000 px; duzlestirilmis yol `ok (1000,600,1000,200)` verirken ham `uint16/32/64` yolu `CaptureError` veriyor (GECERLI bolge reddedilir). Ayrisan aile `x == w`'dir ve kenara uzaklikla ILGISI YOKTUR; kaynak M0'in negatif x'idir (tek monitorlu kontrol duzeninde ayni grid'de ayrisma 0). Bu, PROTOKOL §4.6/10'un yasakladigi sinifin ta kendisidir ve kural bu turda TAM BU cumlenin atasi yuzunden eklendi: bir 'sifir' ancak olcunun ATESLEYEBILDIGI gosterilerek yazilir. Iddianin dayanagi olan grid (`x,y` 0..260 adim 20, `w,h` 1..260 adim 20) `x == w` noktasini YAPISAL OLARAK uretemez -- ayni kor nokta bir kat asagida tekrar etti. Teslimin kendi kanit dosyasi da karsi ornek tasiyor: `INSIDE (100,100,100,100)` dort tipte de 'GURULTULU: gecerli bolge REDDEDILDI' diye kayitli (x=100, w=100 -> `x == w`). Duzeltme: cumleyi kaldir ya da olculenle degistir (feedback-D.md'de hazir metin); ayni duzeltme `known_gaps`'e de girer (paketin 'IKI YERE yaz' kurali)."
notes: |
  TUR 2 OZETI. Sefin adlandirdigi dort mutant (M12/M13/M37/M44) artik DORDU DE
  yakalaniyor; tur 1'in iki bloke bulgusu KAPANDI. Ret, tur 2'nin kendi iki
  kalemindedir: eklenen olcunun kosmadigi ikinci nokta (istisna yolu) ve tur
  2'de yeniden yazilan docstring'in yeni bir olculmemis 'sifir' iddiasi.

  KOSUM TABANI birebir sefin bildirdigi gibi: mypy exit 0, sahipli 163 passed,
  headless TEMIZ, tests/unit/capture 746 passed, tam takim 985 passed. Kirik
  regresyon YOK.

  D2-1 · DUZELTME DEGISMEZI MI, YAZILDIGI BICIMI MI OLCUYOR? Sekiz yeni mutant
  kurdum (r2-09):
    * M50 `__exit__` tutamaci KAPATMADAN birakir (alan None olur) -> YAKALANDI
      (`test_k10_exit_...`). Olcu mutantin adini degil davranisi kancaliyor.
    * M51 `close()` alani sifirlar ama alttaki `close()`'u cagirmaz ->
      YAKALANDI, hem G2 hem G3 (§3'un `c1_close` sayaci).
    * M52 KONTROL (close() sirasi ters, davranis ayni) -> DOGRU sekilde kacti.
      Kapilar yanlis pozitif uretmiyor.
    * M56 devrik `(w,h,4)` ve M57 `ones` -> ikisi de YAKALANDI; yeni testin
      "h != w sectim ki devrik uretici de dussun" gerekcesi DOGRU cikti.
    * M53 (istisna yolu) -> BES KAPIDAN DA GECTI. BLOKE (yukarida).
    * M58 -> BES KAPIDAN DA GECTI, bloke DEGIL (asagida).
    * M54 (totoloji sondasi) -> yalniz §3'e takildi (asagida).

  D2-2 · EKLENEN DORT TEST TOTOLOJI MI? Hayir, ama biri TEK bir kapiya
  yasliyor:
    * `_tutamac`'a dogrudan yazmak, uretimin kurdugu durumu olcuyor mu? Sonda
      M54: `grab()` tutamaci `_tutamac2`'ye yazsin, `close()`/`__exit__` yine
      `_tutamac`'a baksin -> iki enjeksiyon testi de GECIYOR (kendi enjekte
      ettikleri alani kapatiyorlar), uretimde ise HER tutamac sizar. Bu mutanti
      yakalayan TEK sey `headless_check` §3'un `c1_close` sayacidir. Yani
      enjeksiyonun uretime bagi VAR ama tek noktadan geciyor; §3 degisirse iki
      test sessizce totolojiye doner. Kayda gecirilir, bloke DEGIL.
      (r2-15, `test_d5_TUR2_enjekte_edilen_alan_URETIMIN_yazdigi_alan_mi`.)
    * `(h,w,4)` iddiasi: K1'in yazili sozlesmesi; uc ihlal bicimi (M44 kanal,
      M56 devrik, M57 icerik) de yakalaniyor -> totoloji degil.
    * `type(x) is int` iddiasi: gercek `capture_region` yolunu dort numpy
      tipiyle suruyor, M37 yakalaniyor -> totoloji degil. Ama YALNIZ INSIDE
      bacaginda kosuyor (asagida M58).

  D2-3 · DOCSTRING. Uc zarar kipinin UCU DE ve iki sayinin IKISI DE bagimsiz
  olcumumle BIREBIR tuttu (r2-10):
    * gurultulu red: `Rect(uint16(100)x4)` INSIDE'dir, ham yolda `outside`.
    * sessiz yanlis: `Rect(uint32(2500),100,200,100)` -> dogru `w=60`, ham yol
      `w=200`, ISTISNA YOK (yalniz 2 RuntimeWarning). Urunun kendi ciktisi
      dogru: `Frame.rect = (2500,100,60,100)`, dort alan da duz `int`.
    * K6 disi ciplak `OverflowError`: L duzeninde uint8 ile 25 vaka,
      "Python integer 10000 out of bounds for uint8".
    * sayilar: uint32/uint64 icin 6480 kombinasyonun **1108**'i sessiz farkli
      geometri, **240**'i sessizce kabul edilen gecersiz bolge. Docstring'le
      birebir. (uint16 icin 750/240 -- docstring uint16'yi bu cumlede saymiyor,
      dogru.)
    * dort isaretsiz tipte de RuntimeWarning: uint8 x5, uint16/32/64 x3.
    Tutmayan TEK cumle, sondaki OLUMSUZ iddiadir -> BLOKE D-2.2.

  D2-4 · KAPSAM VE PRAGMA. `src/capture` altinda tam **3** `# pragma: no
  cover`; ucu de `MssBackend.monitors/grab/close`'un `def` satirinda ve ucu de
  K13'un istedigi `# K1: gercek ekran, headless_check §3` gerekcesini tasiyor.
  Tur 2 fazladan pragma GETIRMEDI. Gizli `exclude_lines` yok (`.coveragerc`,
  `pyproject.toml`, `setup.cfg`, `tox.ini`, `pytest.ini` -- besi de YOK).
  Kapsam **artmadi**: tur 1 ve tur 2 birebir ayni -- 171 ifade, 2 eksik,
  **%98.83**; degisen yalnizca eksik satirlarin NUMARASI (479/482 -> 501/504),
  cunku docstring 22 satir uzadi. "%99" `term` tablosunun yuvarlanmis
  gosterimidir ve tur 1'de de %99 yaziyordu (r1-04). Payda oyunu YOK, gercek
  artis da YOK. Kapsanmayan iki satir yine K13'un "pragma ALMAZ" dedigi
  yapisal olarak erisilemez savunma satirlari (`union_bbox is None`,
  `intersect is None`). Eklenen dort testin ikisi `close()` govdesini suruyor
  ama o govde pragma'lidir -- yani yeni testler kapsami YUKSELTMEZ; olctukleri
  sey kapsam degil DAVRANIS. (r2-07)

  D2-5 · `known_gaps` x DOCSTRING. Korluk notu: PROTOKOL kapi 2 ve env.md
  `delivery.md` okumayi yasakliyor, sefin tur 2 yonergesi ise D2-5'i acikca
  gorevlendirdi. Uzlasma olarak `delivery.md`'nin YALNIZCA `known_gaps` alanini
  ayristirdim (anlati, `commands`, kanit iddialari OKUNMADI) ve bunu kendi
  olcumlerim BITTIKTEN SONRA yaptim (r2-14).
    * CELISKI YOK: iki metin de dort isaretsiz tipi, iki (+bir) zarar kipini,
      1108/240 sayilarini ve "kural degismedi, degisen gerekce cumlesidir"i
      ayni sekilde soyluyor.
    * AMA: bloke edilen 'sifir' genellemesi YALNIZ docstring'de. `known_gaps`
      dar ve DOGRU olani soyluyor ("sefin grid'i ... GERCEKTEN sifir ayrisma
      veriyor ... sebebi o grid'in her bolgesinin monitorun derin icinde
      kalmasi"); docstring bunu "kenardan uzak bolgelerde dort tipte de ayrisma
      sifirdir" diye GENELLEDI. Yani hata kopyalamada degil, genellemede.
    * K2/K5/K8/K10/K11/K12'nin 11 zorunlu maddesinin 11'i de docstring'lerde
      duruyor (test_d8, r2-15).

  UC BEKLENEN KIRIK -- YENIDEN NISANLANDI, DORDUNCU YOK. Tur 1 kitim uc kirik
  verdi (r2-06: 3 failed / 94 passed) ve ucu de sefin bildirdigi kacinilmaz
  bayatlamaydi: iki `xfail(strict)` XPASS'a dondu, bir "not" testi kendi
  mesajinin dedigi gibi guncellenmesi gerektigini soyledi. Ucu de dogrulanmis
  yesil teste cevrildi:
    `test_d5_TUR2_exit_close_cagirmayan_uygulama_kapiya_TAKILIYOR`,
    `test_d5_TUR2_idempotent_olmayan_close_kapiya_TAKILIYOR`,
    `test_d6_TUR2_backend_e_giden_kutunun_TIPI_artik_olculuyor`
  (sonuncusu ayrica §4.6/7'yi arar: olcu tip uzayinin >=2 noktasinda kosmali --
  kosuyor, dort tip). DORDUNCU bir kirik YOK; 113 passed, 2 xfailed ve iki
  xfail bu turun iki bulgusudur.

  BLOKE ETMEYEN, KAYDA GECEN:
    a) M58 -- backend'e giden kutuya numpy skaleri YALNIZ PARTIAL yolunda
       sizdiran bir uygulama bes kapidan da geciyor (r2-09). Yeni
       `test_k3_backend_kutusu_duz_int_tasir` dort TIP noktasinda kosuyor ama
       tek YOL noktasinda (INSIDE). Bloke DEGIL: K3'un yazili degismezi
       INSIDE kapsamlidir, `Frame.rect` ve karar yolu iki yolda da duz kalir
       (K8 olcusu INSIDE+PARTIAL kosuyor). Sertlestirme: ayni testin bir
       parametresi PARTIAL bolge olsun.
    b) M54 -- yukarida; enjeksiyonun uretime bagi tek kapiya (§3 `c1_close`)
       yasliyor.
    c) `headless_check` §3 hala `MssBackend`'i `with` ile hic kullanmiyor ve
       §4'un dekorator denetimi hala yalniz `FakeBackend.grab`'e bakiyor. Sef
       ikisini de "kapanista acik kalem" diye bilincli erteledi; D-2.1 bunun
       bedelini gosteriyor -- `tests/` katmanindaki olcu istisna yolunu
       kapsamayinca o sinifin yarisi acik kaldi.

  KAPSAM DISI BIRAKTIKLARIM. Merceğim D. Takma ad / sayisal / durum makinesi
  yuzeylerine yalnizca mutant sondasinin gerektirdigi kadar dokundum ve
  onlarda bulgu BILDIRMIYORUM. `delivery.md`'nin yalnizca `known_gaps` alani
  okundu (yukarida gerekce); `evidence/` altindan yalnizca sefin bu tur icin
  acikca isaret ettigi `t2-2-tasma-olcumu.txt` okundu ve KENDI olcumumden
  SONRA -- dogrulamak icin, turetmek icin degil. Diger tester dizinleri
  OKUNMADI. `headless_check.py` okundu ve denetlendi, DEGISTIRILMEDI. `src/`
  ve `tests/` HIC yazilmadi (`git status --short -- src tests` bos, r2-17);
  butun mutasyonlar depo DISINDAKI ayna agacinda kosuldu.
---

# Mercek D -- tur 2: kapi neyi olcuyor?

**Tur 1'in iki bloke bulgusu kapandi.** Sefin adlandirdigi dort mutantin
dordu de yakalaniyor, eklenen dort test totoloji degil, kontrol mutanti dogru
sekilde kaciyor ve kapsam/pragma temiz. Uygulamaya dokunulmamis; docstring
disinda `src/` degismemis.

**Ret, tur 2'nin kendi iki kalemi icin:**

1. **D-2.1** -- eklenen olcu `__exit__`'i yalnizca **temiz cikista** kosuyor.
   Istisna yolunda kapatmayan bir uygulama (M53) bes kapidan da geciyor; oysa
   `with MssBackend() as b:` govdesinin `CaptureError` ile bitmesi urunun
   **normal** hata yoludur. Tur 1'de bloke edilen M12'nin zarar sinifi, yarisi
   acik halde duruyor. Duzeltme: **tek test, +25 satir**; ayirt etme gucu
   olculdu (taban 164 passed, M53 1 failed).

2. **D-2.2** -- tur 2'de yeniden yazilan docstring, kaldirdigi olculmemis
   "sifir" iddiasinin yerine **yeni bir olculmemis "sifir" iddiasi** koydu:
   "kenardan uzak (derin INSIDE) bolgelerde dort tipte de ayrisma sifirdir".
   Olctum: `Rect(1000, 600, 1000, 200)` her kenardan >=560 px uzak, INSIDE, ve
   ham `uint32` yolunda `CaptureError` aliyor. Ayrisan aile `x == w`; iddianin
   dayandigi grid o noktayi **yapisal olarak uretemiyor**. PROTOKOL §4.6/10 bu
   turda tam bu cumlenin atasi yuzunden eklendi.

Ikisi de `owns` icinde, ikisi de birer kalemle kapanir. Hazir kod ve olculmus
ayirt etme gucu: `feedback-D.md`.
