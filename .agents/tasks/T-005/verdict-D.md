---
task: T-005
role: tester
round: 1
decision: ret
checks:
  - name: "kabul #1 -- mypy --strict temiz"
    cmd: "python -m mypy --strict --explicit-package-bases src/capture/service.py src/capture/monitors.py"
    exit_code: 0
    result: gecti
    evidence: tester_D_evidence/r1-01-mypy.txt
  - name: "kabul #2 -- sahipli iki test dosyasi (159 passed)"
    cmd: "python -m pytest tests/unit/capture/test_service.py tests/unit/capture/test_monitors.py -q"
    exit_code: 0
    result: gecti
    evidence: tester_D_evidence/r1-02-pytest-owned.txt
  - name: "kabul #3 -- headless_check.py TEMIZ"
    cmd: "python .agents/tasks/T-005/headless_check.py"
    exit_code: 0
    result: gecti
    evidence: tester_D_evidence/r1-03-headless.txt
  - name: "kabul #4/#5 -- 742 passed, kapsam %98.83 (sefin tabani birebir)"
    cmd: "python -m pytest tests/unit/capture -q --cov=src.capture.service --cov=src.capture.monitors --cov-report=term-missing"
    exit_code: 0
    result: gecti
    evidence: tester_D_evidence/r1-04-cov.txt
  - name: "tam takim regresyonu -- 981 passed (sefin tabani birebir)"
    cmd: "python -m pytest tests -q"
    exit_code: 0
    result: gecti
    evidence: tester_D_evidence/r1-05-pytest-all.txt
  - name: "mercek D kiti -- 95 passed, 2 xfailed (iki xfail = iki BOS olcum noktasi)"
    cmd: "python -m pytest .agents/tasks/T-005/tester_D -q"
    exit_code: 0
    result: gecti
    evidence: tester_D_evidence/r1-06-tester-D.txt
  - name: "D-1/D-2 BLOKE -- 49 mutant x 5 kapi: iki DEGISMEZ mutanti bes kapidan da GECIYOR (M12, M13)"
    cmd: "python .agents/tasks/T-005/tester_D/mutant_kiti.py"
    exit_code: 0
    result: kaldi
    evidence: tester_D_evidence/r1-18-mutant-birlesik.txt
  - name: "D-1/D-2 tek komutla yeniden uretim -- M12 ve M13 ikisi de [.....]"
    cmd: "python .agents/tasks/T-005/tester_D/mutant_kiti.py M12 M13"
    exit_code: 0
    result: kaldi
    evidence: tester_D_evidence/r1-21-bloke-mutantlar.txt
  - name: "onerilen duzeltme AYIRT EDIYOR -- iki test tabanda gecer, M12'de 1, M13'te 2 kirilir"
    cmd: "bkz. r1-17 (ayna agacinda taban / M12 / M13)"
    exit_code: 0
    result: gecti
    evidence: tester_D_evidence/r1-17-onerilen-duzeltme.txt
  - name: "D-1 referans bagimsizligi -- §3 tip denetimini donusumden ONCE yapiyor; ham ScreenShot ve ekrani okumayan grab §3'te DUSUYOR (Y6-2 gerilemesi yok)"
    cmd: "python -m pytest .agents/tasks/T-005/tester_D/test_d1_referans_bagimsizligi.py -q"
    exit_code: 0
    result: gecti
    evidence: tester_D_evidence/r1-06-tester-D.txt
  - name: "D-3 parametre uzayi -- §3 grab kutusunu IKI ayri noktada (biri negatif) olcuyor; kirpan grab yalniz ikinci noktada dusuyor (Y7-1 gerilemesi yok)"
    cmd: "python -m pytest .agents/tasks/T-005/tester_D/test_d3_parametre_uzayi.py -q"
    exit_code: 0
    result: gecti
    evidence: tester_D_evidence/r1-06-tester-D.txt
  - name: "D-4 girdi sayan kural -- dort ayrisan bicimin dordu de reddediliyor; K5/K8 duzlestirmesi BES numpy tipinde tutuyor; hasattr ile sayan uygulama kabul #2'de dusuyor"
    cmd: "python -m pytest .agents/tasks/T-005/tester_D/test_d4_girdi_sayan_kural.py -q"
    exit_code: 0
    result: gecti
    evidence: tester_D_evidence/r1-06-tester-D.txt
  - name: "D-6 totoloji taramasi -- iddiasiz/sabit-dogru/bos-raises test YOK; `writeable` iddiasinin BAGIMSIZ ayirt etme gucu var"
    cmd: "python -m pytest .agents/tasks/T-005/tester_D/test_d6_totoloji.py -q"
    exit_code: 0
    result: gecti
    evidence: tester_D_evidence/r1-06-tester-D.txt
  - name: "D-7 kapsam yalani -- 4 fazladan pragma: 171->149 ifade, %98.83->%98.66, esik yine exit 0 (makine GORMEZ); teslimde K13 disi pragma YOK (3 pragma, ucu de izinli)"
    cmd: "python -m pytest ... --cov-fail-under=95 (fazladan pragma ile, ayna agacinda)"
    exit_code: 0
    result: gecti
    evidence: tester_D_evidence/r1-13-kapsam-yalani.txt
  - name: "D-8 makine gormeyen kapilar -- validate.py `known_gaps: []`'i, alanin YOKLUGUNU ve TEK komutu KABUL ediyor"
    cmd: "python .agents/validate.py <sentetik teslim>"
    exit_code: 0
    result: kaldi
    evidence: tester_D_evidence/r1-14-validate-korlugu.txt
  - name: "D-8b 'IKI YERE yaz' docstring yarisi -- K2/K5/K8/K10/K11/K12 zorunlu maddelerinin 11'i de docstring'de VAR"
    cmd: "python -m pytest .agents/tasks/T-005/tester_D/test_d8_makine_gormeyen_kapilar.py -q"
    exit_code: 0
    result: gecti
    evidence: tester_D_evidence/r1-15-docstring-known-gaps.txt
  - name: "src/ ve tests/ DEGISTIRILMEDI (mutantlar ayna agacinda kosuldu)"
    cmd: "git status --short -- src tests"
    exit_code: 0
    result: gecti
    evidence: tester_D_evidence/r1-19-son-durum.txt
blocking_issues:
  - "D-1 · K10'un `MssBackend.__exit__` -> `close()` DEGISMEZININ olcusu YAPISAL OLARAK BOS. `__exit__`'i `return None` yapan mutant (M12) BES kabul komutundan da exit 0 aliyor. Tek birim testi (`test_service.py::test_k1_mss_backend_yapimi_mss_e_dokunmaz`) satiri KAPSIYOR ama yalnizca `ic is b` iddia ediyor; orada `_tutamac` zaten `None` oldugu icin `close()` etkisiz ve iddia iki davranisi AYIRT EDEMEZ. `headless_check.py` §3 hic `with b:` kullanmiyor. Ihlalin sonucu K10'un kendi olctugu ariza: her `with` blogu bir window DC sizdirir, 5001. kapatilmamis ornekte `GetWindowDC` KALICI olarak duser. `[OLCULMUYOR]` damgasi da yok (PROTOKOL §4.6/2). Kanit: tester_D_evidence/r1-18-mutant-birlesik.txt (M12 satiri) ve r1-06-tester-D.txt (XFAIL test_d5_BULGU_exit_...)."
  - "D-2 · K10'un `close()` IDEMPOTENT degismezinin olcusu (§3 `c2_close`) YAPISAL OLARAK DUSEMEZ. `close()`'dan `self._tutamac = None` satirini silen mutant (M13) BES kapidan da exit 0 aliyor, cunku §3 casusunun `_FakeMSS.close()`'u kendi icinde `self._closed` ile korunuyor -- gercek `mss.MSS.close()` gibi ('It is safe to call this multiple times'). Sayac bu yuzden hicbir uygulamada artmaz. Gercek zarar sayacta degil: tutamac sifirlanmayinca `close()` sonrasi `grab()` KAPATILMIS bir `MSS` kullanir (mss: 'Once the MSS object is closed, it may not be used again') ve bunu hicbir kapi olcmez. Kanit: tester_D_evidence/r1-18-mutant-birlesik.txt (M13 satiri) ve r1-06-tester-D.txt (XFAIL test_d5_BULGU_idempotent_...)."
notes: |
  KOSUM TABANI birebir yeniden uretildi: kabul komutlarinin besi de exit 0;
  `pytest tests/unit/capture` 742 passed; `pytest tests` 981 passed; kapsam
  %98.83 (171 ifade, 2 eksik: 479/482 -- yapisal olarak erisilemez savunma
  satirlari, K13 geregi pragma ALMAMISLAR ve esik onlarsiz da tutuyor).
  Kirik regresyon YOK.

  YONTEM. `src/` ve `tests/` hic yazilmadi (`git status --short -- src tests`
  bos). Depo, sistem gecici dizini altindaki `t005_tester_D_mutroot/` agacina
  aynalandi (kit onu kendisi kurar; `TESTER_D_SCRATCH` ile tasinabilir);
  49 mutant orada kuruldu ve her mutant icin BES kabul komutu ayri ayri
  kosuldu. Kit ve tablo:
  `.agents/tasks/T-005/tester_D/mutant_kiti.py`,
  `tester_D_evidence/r1-18-mutant-birlesik.txt`.

  OLCULEN AYIRT ETME GUCU. 49 mutantin 40'i en az bir kapiya takildi. Kacan
  9'un dagilimi:
    * M12, M13 -> BLOKE (yukarida).
    * M31, M32 -> fazladan `# pragma: no cover`. Paketin K13 iddiasi DOGRU
      cikti: 4 fazladan pragma ifade sayisini 171'den 149'a dusuruyor, kapsami
      %98.83'ten %98.66'ya indiriyor ve komut yine exit 0 veriyor. Teslimde
      fazladan pragma YOK: `src/capture` altinda tam 3 pragma var, ucu de
      `MssBackend.monitors/grab/close` uzerinde ve ucu de `# K1: gercek ekran,
      headless_check §3` gerekcesini tasiyor. `.coveragerc`/`pyproject.toml`
      gibi gizli `exclude_lines` de yok. (r1-13)
    * M33 -> K8'in `capture_full` bacagi. Paketin `[OLCULMUYOR]` damgasi
      DURUST: bacagi ihlal eden mutant bes kapidan da geciyor, ama gercek kod
      yolunda oraya numpy ULASAMAZ cunku `_monitors` K5 tarafindan zaten
      duzlestiriliyor (M14/M15 yakalaniyor). Damga yerinde.
    * M42, M43 -> kontrol mutantlari (davranisi degistirmeyen ekleme /
      demetin kopyasi). Kacmalari DOGRU; kapilar yanlis pozitif uretmiyor.
    * M37 -> `capture_region` backend'e DUZLESTIRILMEMIS geometri gonderirken
      `Frame.rect`'i duz birakiyor; bes kapi da temiz. Sebep env.md'nin
      isaret ettigi kor nokta: K3 olcusu `==` ile yazilmis ve
      `Rect(np.int64(100),...) == Rect(100,...)` -> True, hash esit, demet ve
      kume karsilastirmasi da esit (r1-06, test_d6_esitlik_olcusu_...).
      BLOKE DEGIL: M37 hicbir yazili degismezi ihlal etmiyor (K3 "cagiranin
      verdigiyle birebir" diyor, M37 tam olarak cagiranin degerini gonderiyor;
      K8 duzlestirmesi `Frame.rect`'i ve karar yolunu kapsiyor, ikisi de duz
      kaliyor). Teslim edilen uygulama zaten DOGRU: backend'e giden kutuda
      dort numpy tipinde de `type(...) is int` (test_d6_backend_e_giden_kutu_duz_int).
      Sefe oneri: K3'e "backend'e giden kutu duz `int`'tir" cumlesi eklenirse
      olcu tip kimligiyle yazilmali, `==` ile degil.
    * M44 -> `FakeBackend` varsayilan `image_factory`'sinin `(h, w, 4)` olmasi
      K1'de YAZILI ama hicbir yerde olculmuyor. Dusuk siddet (yalnizca test
      altyapisi, uretime etkisi yok); tek satirlik bir iddia kapatir.

  MERCEK D'NIN ILK YEDI MADDESI -- SONUC.
    1) Referans bagimsizligi: §3'te `isinstance` olcusu `np.asarray`'den ONCE
       geliyor ve icerik referansi casusun kendi `01 02 03 FF` deseninden
       turetiliyor. Ham `ScreenShot` donduren grab (M06) ve ekrani hic okumayan
       grab §3'te DUSUYOR. Y6-2 gerilemesi yok. Uygulama tarafinda
       `_bicimi_dogrula` govdesinde hicbir `asarray`/`np.array` yok.
    2) Mekanizma adi: uyum satirlarinin silinmesi (M09), ciplak ek aciklamaya
       donmesi (M10) ve `FakeBackend.grab`'in dekoratorlenmesi (M11) UCU DE
       yakalaniyor. Y5-1/Y6-1/Y7-5 gerilemesi yok.
    3) Parametre uzayi: §3'un `grab_args` beklentisi iki tekil nokta tasiyor ve
       biri negatif (`left=-2600`); `max(0, ...)` ile kirpan grab (M05) YALNIZ
       o noktada dusuyor ve ihlal mesaji `-2600`'u bildiriyor. Y7-1 gerilemesi
       yok. Ek olarak K3'u 4 olcek x 4 geometri, K7 sahipligini 2 kanal x 2
       yazilabilirlik uzayinda kosturdum: hepsi tutuyor.
    4) Girdi sayan kural: dort ayrisan bicimin (`__array_interface__`,
       `__array__`, 3B `memoryview`, PEP 688 `__buffer__`) dordu de
       reddediliyor; ikisini `hasattr` ile eleyip gerisini ceviren uygulama
       (M03) kabul #2'de `test_k7_bicim_donusum_yok`'ta dusuyor. K5/K8
       duzlestirmesini paketin dort tipinin OTESINDE bes tipte (int16/uint32
       eklendi) kosturdum: tip duzeyinde, sayim yok.
    5) Bos olcum noktalari: iki tane bulundu -> D-1, D-2 (BLOKE). Paketin
       kendi `[OLCULMUYOR]` damgasi ise durust cikti.
    6) Totoloji: sahipli iki test dosyasinda iddiasiz test, `assert True`
       turu sabit-dogru iddia ve bos `pytest.raises` govdesi YOK. `writeable`
       iddiasinin `shares_memory`'den BAGIMSIZ gucu VAR: bellek paylasmayan
       ama salt-okunur bir "kopya" (`np.frombuffer(...tobytes())`, M02)
       kurulabiliyor ve onu yalniz `writeable` iddiasi yakaliyor.
    7) Kapsam yalani: mekanizma dogrulandi, teslimde ihlal YOK (yukarida).

  8. MADDE -- MAKINENIN GORMEDIGI KAPILAR. `validate.py`'nin korlugunu
  SENTETIK bir teslim dosyasiyla yeniden urettim (gercek `delivery.md`
  OKUNMADI, PROTOKOL kapi 2): `known_gaps: []` ve TEK komut tasiyan bir
  teslim exit 0 aliyor; `known_gaps` alani TAMAMEN silinse de exit 0 aliyor
  (alan `REQUIRED` listesinde bile degil); `no cover`/`pragma`/`known_gaps`
  kelimeleri `validate.py`'de hic gecmiyor (r1-14). Tester korlugu geregi
  `known_gaps` ICERIGINI ve `commands` SAYISINI olcemem -- ikisi de sefin
  elle denetleyecegi kalemdir. Olcebildigim yarim, paketin "Kararlarini IKI
  YERE yaz" kuralinin DOCSTRING yarisidir ve TAMDIR: K2 (seq yalniz tek
  ornek icinde), K5 (monitor kimligi konumsal/kararsiz), K8 (servis DPI
  olcegi uretemez + `intersect` metadata'si kullanilmaz + `capture_full` icin
  1.0), K10 (PER_MONITOR_DPI_AWARE, QApplication'dan once cagirma, 5001.
  kapatilmamis ornek), K11 (gercek `mss.grab` medyani 13.5 ms, 5.7 butcesi
  zaten asiliyor), K12 (thread-safe degil) -- 11 zorunlu maddenin 11'i de
  kaynak docstring'lerinde var (r1-15).

  SEFE -- BU TURDA DUZELTILEMEYECEK KAPI KUSURLARI (implementer'in yetkisi
  disinda, `headless_check.py` sefindir):
    a) §3 (6) `close()` olcusu casusun kendi idempotensi yuzunden hicbir
       uygulamada dusemiyor (D-2'nin kaynagi). Casusun `close()`'u sayaci
       KOSULSUZ artirir ve ayrica "kapali nesneye ikinci close" olayini ayri
       kaydederse olcu ayirt eder hale gelir.
    b) §3 `MssBackend`'i hic `with` ile kullanmiyor; `__enter__`/`__exit__`
       bacagi §3'te yok (D-1'in kaynagi).
    c) Paketin K10 ÖLÇÜ satirindaki "(Test paketi bunu olcemez, K1 geregi.)"
       parantezi OLGUSAL OLARAK YANLIS. Sahte bir tutamac enjekte ederek ya da
       `sys.modules['mss']`'e sayacli bir casus koyarak `__exit__`/`close()`
       davranisi gercek ekrana HIC dokunmadan olculuyor -- kendi kitimda iki
       ayri yoldan yaptim (test_d5_uygulama_exit_close_cagiriyor ve
       test_d5_uygulama_close_tutamaci_sifirliyor, ikisi de gecti). Bu yanlis
       parantez implementer'i mesru bir olcuden alikoydu; feedback-D.md
       duzeltmeyi hazir test koduyla veriyor.
    d) §4'un dekorator denetimi yalniz `FakeBackend.grab`'e bakiyor;
       `MssBackend.grab` ve `FakeBackend.monitors` denetim disi. Bu turda
       somut bir kacisa yol acmadi, kayda gecirilir.

  KAPSAM DISI BIRAKTIKLARIM. Merceğim D; takma ad (A), sayisal (B) ve durum
  makinesi (C) yuzeylerini yalnizca mutant sondasinin gerektirdigi kadar
  dokundum ve onlarda bulgu BILDIRMIYORUM. `delivery.md`, `evidence/` ve
  diger tester dizinleri OKUNMADI. `headless_check.py` OKUNDU ve DENETLENDI,
  DEGISTIRILMEDI.
---

# Mercek D -- kapi gercekten bir sey olcuyor mu?

Ozet: **uygulama dogru, iki kapi bos.** 49 mutantin 40'i takildi; kacan 9'un
7'si ya kontrol mutanti ya da paketin kendi durust `[OLCULMUYOR]` /
"makine gormez" damgasini tasiyan yerler. Kalan 2'si (`M12`, `M13`) K10'un iki
yazili DEGISMEZINI ihlal ediyor ve **bes kabul komutundan da temiz geciyor**.

Duzeltme `src/` degil, **yalnizca `tests/unit/capture/test_service.py`**:
iki test, ~35 satir, gercek ekrana sifir temas. Ayna agacinda dogrulandi --
tabanda gecer, `M12`'de biri, `M13`'te ikisi kirilir
(`tester_D_evidence/r1-17-onerilen-duzeltme.txt`). Hazir kod
`feedback-D.md`'dedir.
