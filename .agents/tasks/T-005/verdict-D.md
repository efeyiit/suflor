---
task: T-005
role: tester
round: 3
decision: onay
checks:
  - name: "kabul #1 -- mypy --strict temiz"
    cmd: "python -m mypy --strict --explicit-package-bases src/capture/service.py src/capture/monitors.py"
    exit_code: 0
    result: gecti
    evidence: tester_D_evidence/r3-01-mypy.txt
  - name: "kabul #2 -- sahipli iki test dosyasi: 164 passed (sefin tabani birebir)"
    cmd: "python -m pytest tests/unit/capture/test_service.py tests/unit/capture/test_monitors.py -q"
    exit_code: 0
    result: gecti
    evidence: tester_D_evidence/r3-02-pytest-owned.txt
  - name: "kabul #3 -- headless_check.py TEMIZ"
    cmd: "python .agents/tasks/T-005/headless_check.py"
    exit_code: 0
    result: gecti
    evidence: tester_D_evidence/r3-03-headless.txt
  - name: "kabul #4 -- tests/unit/capture 747 passed, kapsam %98.83 (171 ifade / 2 eksik; tur 1-2-3 BIREBIR AYNI)"
    cmd: "python -m pytest tests/unit/capture -q --cov=src.capture.service --cov=src.capture.monitors --cov-fail-under=95 --cov-report=term-missing"
    exit_code: 0
    result: gecti
    evidence: tester_D_evidence/r3-04-cov.txt
  - name: "kabul #5 -- tam takim 986 passed"
    cmd: "python -m pytest tests -q"
    exit_code: 0
    result: gecti
    evidence: tester_D_evidence/r3-05-pytest-all.txt
  - name: "D3-5a -- tur 2 kitinin bayatligi: TAM IKI beklenen kirik (iki xfail(strict) bulgu isareti XPASS = iki bulgu KAPANDI), dorduncu YOK (2 failed / 113 passed)"
    cmd: "python -m pytest .agents/tasks/T-005/tester_D -q -rxXf"
    exit_code: 1
    result: gecti
    evidence: tester_D_evidence/r3-06-tester-D-kit.txt
  - name: "sefin kapi mutantlari dalga 1 (sef kostu, ben yeniden urettim): M12/M13/M37/M44 DORDU DE yakalandi [.X.XX]"
    cmd: "python .agents/tasks/T-005/tester_D/mutant_kiti.py M12 M13 M37 M44"
    exit_code: 0
    result: gecti
    evidence: tester_D_evidence/r3-07-sef-kapi-mutantlari-dalga1.txt
  - name: "sefin kapi mutantlari dalga 2 (sef kostu, ben yeniden urettim): M50/M51/M53/M56/M57 yakalandi, M53 tur 2'de KACIYORDU simdi [.X.XX]; M52 KONTROL dogru kacti; M54 yalniz §3; M58 kacti (adlandirilmis, bloke degil)"
    cmd: "python .agents/tasks/T-005/tester_D/mutant_kiti_tur2.py"
    exit_code: 0
    result: gecti
    evidence: tester_D_evidence/r3-08-sef-kapi-mutantlari-dalga2.txt
  - name: "D3-1a -- sefin YAPISAL iddiasi kendi elimle olculdu: 14 cikis yolu -> exc_type TAM 2 ayrik SINIF (None x5 yol, istisna x9 yol); GeneratorExit dahil ucuncu SINIF yok -> DOGRU. AMA exc_type'in DEGER ekseni 2 degil: None + 114 BaseException alt sinifi"
    cmd: "python -X utf8 .agents/tasks/T-005/tester_D/t3_exc_type_ekseni.py"
    exit_code: 0
    result: gecti
    evidence: tester_D_evidence/r3-09-exc-type-ekseni.txt
  - name: "D3-1b -- YENI mutant dalgasi (8), kapilar = tur 3'un BES kabul komutu birebir, TABAN bes kapida TEMIZ: M63 pozitif kontrol (yut) YAKALANDI [.X.XX]; M67 (__exit__ close() yerine baska metoda bagli) YAKALANDI [.X.XX]; M66 KONTROL (close govdesi satir ici, davranis ayni) DOGRU KACTI -> olcu mekanizmayi degil DEGISMEZI kancaliyor; M65 KONTROL yalniz mypy'ye takildi (tip kurali, davranissal kapilar dogru kacti); M60/M61/M62/M64 (exc_type DEGERINE kapili) BES KAPIDAN DA GECTI -> bloke DEGIL, adlandirilmis yukumluluk"
    cmd: "python -X utf8 .agents/tasks/T-005/tester_D/t3_mutant_kiti.py"
    exit_code: 0
    result: gecti
    evidence: tester_D_evidence/r3-10-mutant-dalga-tur3.txt
  - name: "D3-2 -- parametrizasyon ESKI KAPSAMI KAYBETMEDI: exc_type=None bacagi TEK BASINA M12/M50/M53T/M67'yi yakaliyor (tur 2 tekil testinin gucu birebir); CaptureError bacagi TEK BASINA M53/M63'u ekliyor; bacaklar TAMAMLAYICI (M53 yalniz istisna, M53T yalniz None bacaginda duser); govde ici assert pytest.raises tarafindan YUTULMUYOR (S1 sondasi iki bacakta da 1 failed); M68 kontrol her yerde kacti"
    cmd: "python -X utf8 .agents/tasks/T-005/tester_D/t3_bacak_gucu.py"
    exit_code: 0
    result: gecti
    evidence: tester_D_evidence/r3-11-bacak-gucu.txt
  - name: "D3-3a -- docstring denetimi: 8/8 olumlu iddia BAGIMSIZ olcumle tutuyor (derin INSIDE karsi ornegi 560 px; x==w uyeleri + komsu pozitif kontrolu; x!=w uyesi Rect(100,600,1124,64) uint16 CaptureError, derinlik 100 px; kenar grid'i 6480/1108/240; L duzeni uint8 ciplak OverflowError; atif dosyalari var+dolu; 'hicbirinde backend cagrilmaz' 5 kosulda grab_calls=0; kirpma birlesime karsi w=5120). capture_region'da ACIK GIRDI KUMESI uzerinde olumsuz evrensel iddia KALMADI; [OLCULMUYOR] damgasi VAR"
    cmd: "python -X utf8 .agents/tasks/T-005/tester_D/t3_docstring_denetimi.py"
    exit_code: 0
    result: gecti
    evidence: tester_D_evidence/r3-12-docstring-denetimi.txt
  - name: "D3-3b/D3-4 -- delivery.md'nin YALNIZCA YAML on bilgisi ayristirildi (anlati OKUNMADI): known_gaps 33 kalem; M54 ve M58 kalem [4]'te ADLANDIRILMIS ve [OLCULMUYOR] damgali; docstring ile CELISKI YOK; kalem [1] test docstring'iyle AYNI 'eksen TAMAMEN kapatir' iddiasini tasiyor (asagida)"
    cmd: "python -X utf8 <delivery.md on bilgisinden yalnizca known_gaps/files_written>"
    exit_code: 0
    result: gecti
    evidence: tester_D_evidence/r3-13-known-gaps-alani.txt
  - name: "D3-1c -- kacan sinifin ERISILEBILIRLIGI: uretimde (src/, demo/) `with ...Backend()` kullanimi YOK, uretec YOK; tek gercek tuketici demo/bolge_izle.py MssBackend()'i ne with'le ne close()'la kapatiyor"
    cmd: "grep -rn 'MssBackend|.close()|__exit__|with .*Backend|yield' src demo tests"
    exit_code: 0
    result: gecti
    evidence: tester_D_evidence/r3-14-uretim-kullanim-yerleri.txt
  - name: "D3-1d -- tur 3 olcumleri YASAYAN test olarak: 11 passed, 3 xfailed (uc xfail = M61/M62/M64 adlandirilmis yukumlulugu; kapanirsa XPASS verip kasitli kirilir)"
    cmd: "python -m pytest .agents/tasks/T-005/tester_D/test_d10_tur3_exc_type_ekseni.py -q -rxXf"
    exit_code: 0
    result: gecti
    evidence: tester_D_evidence/r3-15-d10-kit.txt
  - name: "D3-5b -- YENIDEN NISANLANMIS kit: 126 passed, 3 xfailed (iki tur 2 bulgu isareti yesil 'KAPANDI' testine cevrildi; uc xfail = bu turun yukumlulugu)"
    cmd: "python -m pytest .agents/tasks/T-005/tester_D -q -rxX"
    exit_code: 0
    result: gecti
    evidence: tester_D_evidence/r3-16-tester-D-kiti-tur3.txt
  - name: "kapsam/pragma degismedi (3 pragma, gizli config yok, 171/2/%98.83) + TEST docstring'inin olumsuz evrensel cumlesi olcumle karsilastirildi"
    cmd: "grep pragma + config varligi + test docstring taramasi"
    exit_code: 0
    result: gecti
    evidence: tester_D_evidence/r3-17-pragma-ve-test-docstring.txt
  - name: "src/ ve tests/ DEGISTIRILMEDI (git status --short -- src tests BOS; ayna agaci depo DISINDA; ayna service.py == depo service.py); 043cef2..HEAD arasinda sahipli dosyalar degismedi -> taban gecerli"
    cmd: "git status --short -- src tests && git diff --stat 043cef2 HEAD -- src/capture tests/unit/capture"
    exit_code: 0
    result: gecti
    evidence: tester_D_evidence/r3-18-son-durum.txt
blocking_issues: []
tester_obligations:
  - "D-3.Y1 · `exc_type` DEGER ekseni [OLCULMUYOR]. Sefin 'eksen tam 2 ayrik sinif alir, ucuncu varyant yok' iddiasi CIKIS YOLU icin DOGRU (kendi elimle: 14 yol -> 2 sinif, r3-09 A). Ama `__exit__` `exc_type`'i bir DEGER olarak alir ve deger uzayi None + BaseException'in tum alt siniflaridir (bu process'te 114). `exc_type`'in DEGERINE gore ayrisan bir `__exit__` iki parametreyi de gecer: M60 (yalniz GeneratorExit'te kapatmaz), M61 (YALNIZ None/CaptureError'da kapatir -- olcunun iki noktasina birebir kapili), M62 (BaseException'da kapatmaz; 'except Exception' aliskanliginin dogal hatasi), M64 (CaptureError disini sessizce YUTAR) -> dordu de BES kapidan geciyor (r3-10). Neden BLOKE DEGIL: uygulama DOGRU (kosulsuz `self.close()`), tur 3 olcusu her MAKUL ihlal bicimini yakaliyor (kapatmama, yalniz temiz/yalniz istisnali cikista kapatma, alttaki close'u atlama, yutma, baska metoda baglama) ve kacan sinif urunun HICBIR cagri yerinde erisilebilir degil (r3-14: src/ ve demo/'da `with ...Backend()` yok, uretec yok). Bu urunu bozan bir sinif degil, olcunun keskinlik siniri. Yasayan isaret: test_d10 xfail(strict) x3. Kapatmak istenirse en ucuz sertlestirme: parametre listesine BaseException-ama-Exception-olmayan bir uye (`KeyboardInterrupt` ya da `GeneratorExit`) eklemek -- M60/M62'yi kapatir; M61/M64 (tam nokta kapili) ancak parametre kumesi disindan bir tiple kapanir."
  - "D-3.Y2 · Test docstring'inde OLCULMEMIS bir 'TAMAMEN' iddiasi. `test_k10_exit_uzun_omurlu_tutamaci_kapatir` docstring'i (tests/unit/capture/test_service.py:943-971) sunu yaziyor: 'exc_type tam **iki ayrik sinif** alir ... Ucuncu bir varyant yoktur ... Bu yuzden iki parametre ekseni TAMAMEN kapatir'. Ilk iki cumle CIKIS YOLU icin dogru; SONUC cumlesi olcumle YANLIS (D-3.Y1: dort varyant iki parametreyi de geciyor) ve pozitif kontrolsuz (deger ekseninden hicbir mutant kosulmamis). Bu, D-2.2'de bloke ettigim sinifin (olgu dogru, GENELLEME yanlis) bir kat yukarida -- olcunun kendi aciklamasinda -- tekrari; ayni cumle known_gaps kalem [1]'de de var. Neden BLOKE DEGIL: cumle `src/` docstring'inde degil TEST docstring'inde, urun davranisini degil olcunun kendi kapsamini anlatiyor, ve §4.6/9 ucuncu turdan sonra kalan bulgulari tester yukumlulugune yazmayi soyluyor. Onerilen duzeltme (bir cumle): 'Bu yuzden iki parametre CIKIS YOLU eksenini kapatir; exc_type'in DEGERINE kapili bir uygulama [OLCULMUYOR] (bkz. tester_D/test_d10).'"
  - "D-3.Y3 · M54 (tutamacin baska alana yazilmasi) ve M58 (K3 kutu olcusunun PARTIAL bacagi) -- known_gaps kalem [4]'te ADLANDIRILMIS, [OLCULMUYOR] damgali, kapsam disi birakilma gerekcesi yazili. Sessiz bosluk YOK. Bu turda yeniden olctum: M54 yine yalniz §3 c1_close'a takiliyor [..X..], M58 yine bes kapidan geciyor (r3-08). Ikisi de tur 2'deki durumuyla ayni; yeni bir sey acilmadi."
notes: |
  TUR 3 OZETI. Tur 2'nin iki bloke bulgusu (D-2.1 istisna yolu, D-2.2 docstring
  'sifir' iddiasi) KAPANDI; bunu hem sefin kapi mutantlariyla (M53 artik
  [.X.XX]) hem kendi kitimin iki xfail(strict) isaretinin XPASS'a donmesiyle
  olctum. Uygulamaya DOKUNULMADI; `src/` degisikligi yalniz docstring, `tests/`
  degisikligi yalniz bir testin parametrelenmesi (git show 043cef2).

  KOSUM TABANI sefin bildirdigiyle birebir: mypy exit 0, sahipli 164, headless
  TEMIZ, tests/unit/capture 747 passed / %98.83, tam takim 986. Sefin dokuz
  mutanti dokuzu da yakalandi, M52 kontrol dogru kacti -- KENDI ELIMLE
  yeniden urettim (r3-07, r3-08).

  D3-1 · EKSEN GERCEKTEN KAPANDI MI? Sefin iddiasini iki yariya ayirdim ve
  ikisini de OLCTUM:
    * CIKIS YOLU ekseni: 14 yol kurdum (normal, return, break, continue,
      Exception, CaptureError, KeyboardInterrupt, SystemExit,
      generator.close(), uretec cop toplama, generator.throw(),
      StopIteration, except icinde yeniden yukseltme, dis finally-return).
      `__exit__` HER yolda tam bir kez cagriliyor ve `exc_type` tam iki
      sinifa dusuyor. Sef HAKLI: ucuncu bir SINIF yok (r3-09 A).
    * DEGER ekseni: `exc_type` bir degerdir, uzayi None + 114 alt sinif.
      'Iki parametre ekseni TAMAMEN kapatir' sonucu yapidan CIKMAZ; mutantla
      olctum: M60/M61/M62/M64 iki parametreyi de geciyor (r3-10).
    Yeni dalganin KONTROLLERI olcunun saglikli oldugunu gosteriyor: M63
    (kapat ama yut) yeni ucuncu assert'e TAKILDI -> assert ateşleyebiliyor;
    M66 (close govdesi satir ici, davranis ayni) KACTI -> olcu `close()`
    CAGRISINI degil tutamacin KAPANMASINI kancaliyor (§4.6/7'nin istedigi
    tam bu); M67 (`__exit__` close yerine sadece birakan metoda bagli)
    TAKILDI. M65 (`return False`) yalniz mypy'ye takildi -- bu bir tip
    kurali ('bool is invalid as return type for __exit__ that always returns
    False'), davranissal kapilar dogru sekilde kacirdi; yanlis pozitif yok.

  D3-2 · PARAMETRIZASYON KAYBI YOK. Her bacagi TEK BASINA node id ile
  kostum (r3-11). `exc_type=None` bacagi tur 2'nin tekil testinin yakaladigi
  M12 ve M50'yi ve aynasi M53T'yi tek basina yakaliyor -- eski guc birebir.
  `exc_type=CaptureError` bacagi M53 ve M63'u EKLIYOR. Iki bacak
  tamamlayici: M53 yalniz istisna bacaginda, M53T yalniz None bacaginda
  duser; yani hicbiri digerinin golgesinde degil. Parametrizasyonun klasik
  tuzagi -- `pytest.raises`'in govde ici AssertionError'i yutmasi -- S1
  sondasiyla olculdu: `__enter__` onceden kapatinca IKI bacak da 1 failed.
  Kontrol mutanti M68 her yerde kacti.

  D3-3 · DOCSTRING GATELENEBILIR. capture_region'in yeniden yazilan
  paragrafinda ACIK GIRDI KUMESI uzerinde olumsuz evrensel iddia KALMADI;
  `[OLCULMUYOR]` damgasi var; 'aile x==w ile sinirli degildir' bir varlik
  iddiasi ve karsi ornegi adli. Kalan 8 olumlu iddianin 8'i bagimsiz
  olcumumle tutuyor (r3-12) -- implementer'in sefe karsi buldugu `x != w`
  uyesi dahil: `Rect(100,600,1124,64)` uint16'da CaptureError, derinlik
  100 px, INSIDE. Kenar grid'inde ilk kosumum 1792/306/128 verdi; sebep
  BENIM gridimdi (adim 200), docstring'in gridi adim 100 = 6480; duzeltince
  1108/240 birebir. Dosyadaki 93 belirtecli cumlenin capture_region'daki
  'her zaman / asla / hicbirinde' uclusu KAPALI kume uzerindedir (kendi kod
  akisi, bes numarali hata kosulu) ve ikisini kostum: bes K6-a kosulunda
  grab_calls=0; 5300w bolge birlesime karsi 5120w. Bunlar §4.6/10'un
  yasakladigi sinif degil: sonlu, sayilabilir, olculmus.

  TEK KALAN KUSUR OLCUNUN KENDI ACIKLAMASINDA: test docstring'i 'iki
  parametre ekseni TAMAMEN kapatir' diyor ve bu olcumle yanlis (D-3.Y2).
  Bloke etmiyorum: urun davranisi degil, `src/` degil, ve §4.6/9 tam bu
  durumu tester yukumlulugune yaziyor.

  D3-4 · M54/M58 ADLANDIRILMIS. known_gaps kalem [4] ikisini de acikca,
  [OLCULMUYOR] damgasiyla ve erteleme gerekcesiyle yaziyor. Sessiz bosluk
  yok. Bu turda yeniden olctum, durum tur 2 ile ayni.

  D3-5 · DORDUNCU KIRIK YOK. Tur 2 kitim tam iki kirik verdi ve ikisi de
  beklenen bayatlama: iki xfail(strict) bulgu isareti XPASS'a dondu =
  bulgular kapandi. Ikisini yesil 'KAPANDI' testine cevirdim
  (`test_d5_TUR3_exit_ISTISNA_yolu_artik_KAPIYA_TAKILIYOR`,
  `test_d9_TUR3_docstring_sifir_iddiasi_SILINDI_ve_damga_var`). Kit simdi
  126 passed, 3 xfailed; uc xfail bu turun D-3.Y1 yukumlulugudur.

  KENDI KITIMDE DUZELTTIGIM IKI HATA (kayda gecsin): (1) ilk t3 mutant
  kosumunda G5 tam takim kapisi SEKIZ mutantin sekizine de takildi --
  kontroller dahil. Sebep mutant degil, EKSIK AYNAYDI: `tests/unit/ocr/
  conftest.py` `.agents/tasks/T-004/olcu_kiti.py`'ye bagimli ve ayna onu
  kopyalamiyordu. Aynayi tamamladim, TABAN kontrolu ekledim (bes kapi
  mutasyonsuz aynada TEMIZ), sonra kostum. Sonuc r3-10. (2) bacak secimi
  once `-k "exc_type=None"` ile yazildi; `-k` `=` kabul etmiyor (rc=4) ve
  her bacak 'yakaladi' gorunuyordu. Node id ile duzeltildi; r3-11 son hali.
  Ikisi de §4.6/10'un dedigi sey: 'yakaladi' da 'kacirdi' da ancak tabanin
  temiz oldugu gosterilince anlam tasir.

  ORANTI. Uc turda da bulgum hakliydi ve uc turda da sinif kuculdu: tur 1
  'olcu YOK', tur 2 'olcu TEK noktada + yanlis genelleme', tur 3 'olcu
  eksenin iki sinifinda da var, kalan bosluk deger ekseninde ve urunde
  erisilebilir degil + genelleme bu kez olcunun kendi metninde'. Bu bir
  urun kusuru sinifi degil, olcunun keskinlik siniri. §7 esigi -- 'urunu
  bozan, olculmus bir sinif' -- karsilanmiyor. ONAY; uc adlandirilmis
  yukumluluk yukarida.

  KAPSAM DISI BIRAKTIKLARIM. Mercegim D. `delivery.md`'nin yalnizca YAML on
  bilgisi (known_gaps/files_written) ayristirildi, anlati OKUNMADI (r3-13
  bunu sayiyla belgeliyor: 22804 karakter on bilgi, 5996 karakter anlati
  okunmadi). `evidence/` altindan hicbir dosya OKUNMADI; docstring'in atif
  verdigi iki dosyanin yalnizca VARLIGI ve BOYUTU olculdu (r3-12 B6). Diger
  tester dizinleri OKUNMADI. `src/`, `tests/`, `headless_check.py`,
  `packet.md`, `sef_karari-*.md`, `sef_dogrulama/`, `PROTOKOL.md`,
  `validate.py` YAZILMADI; `git commit` ATILMADI. Butun mutasyonlar depo
  DISINDAKI ayna agacinda kosuldu; `git status --short -- src tests` BOS
  (r3-18). Gozlem (bulgu degil, sahipli degil): tek gercek tuketici
  `demo/bolge_izle.py` `MssBackend()`'i hic kapatmiyor -- process sonunda
  bir DC kalir, K10'un olctugu 5001 esigine uzaktir; ama K10 API'sinin
  `with`/`close()` disiplinini ilk tuketicinin kullanmadigini sef bilsin.
---

# Mercek D -- tur 3: eksen kapandi mi?

**Onay.** Tur 2'nin iki bloke bulgusu kapandi ve bunu kendi elimle olctum:
sefin dokuz mutanti dokuzu da yakalaniyor, M53 (tur 2'de bes kapidan gecen)
simdi `[.X.XX]`, M52 kontrol dogru kaciyor, kitimin iki `xfail(strict)`
bulgu isareti XPASS'a dondu.

Sefin yapisal iddiasini ikiye boldum ve ikisini de olctum:

1. **Cikis yolu ekseni tam 2 sinif** -- 14 yol kurdum, `__exit__` her
   birinde tam bir kez cagriliyor, `exc_type` iki sinifa dusuyor,
   `GeneratorExit` dahil ucuncu sinif yok. **Sef hakli.**
2. **"Iki parametre ekseni TAMAMEN kapatir"** -- yanlis. `exc_type` bir
   degerdir; degerine kapili dort varyant (M60/M61/M62/M64) iki parametreyi
   de geciyor. Ama uygulama dogru, olcu her makul ihlali yakaliyor (M63/M67
   takildi, M66 kontrol kacti: olcu mekanizmayi degil degismezi kancaliyor)
   ve kacan sinif urunun hicbir cagri yerinde erisilebilir degil. **Urunu
   bozan sinif degil, olcunun keskinlik siniri** -> adlandirilmis
   yukumluluk, bloke degil.

Parametrizasyon eski kapsami **kaybetmedi**: `exc_type=None` bacagi tek
basina tur 2'nin yakaladigi her mutanti yakaliyor, istisna bacagi ustune
ekliyor, ikisi tamamlayici, govde ici assert canli.

Docstring **gatelenebilir**: acik girdi kumesi uzerinde olumsuz evrensel
iddia kalmadi, damga var, kalan sekiz olumlu iddianin sekizi bagimsiz
olcumle tutuyor -- implementer'in sefe karsi buldugu `x != w` uyesi dahil.
Kalan tek kusur olcunun **kendi** docstring'inde ("TAMAMEN kapatir");
`src/` degil, urun davranisi degil, §4.6/9 geregi yukumluluge yazildi.

M54/M58 `known_gaps`'te adlandirilmis; sessiz bosluk yok. Dorduncu kirik yok.
