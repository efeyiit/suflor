---
task: T-008
role: implementer
round: 2
status: tamamlandi
files_written:
  - src/ocr/satir_birlestirici.py
  - tests/unit/ocr/test_satir_birlestirici.py
  - .agents/tasks/T-008/delivery.md
  - .agents/tasks/T-008/evidence/mypy-tur2.txt
  - .agents/tasks/T-008/evidence/mypy-test-dosyasi-tur2.txt
  - .agents/tasks/T-008/evidence/pytest-tur2.txt
  - .agents/tasks/T-008/evidence/pytest-cp1254-tur2.txt
  - .agents/tasks/T-008/evidence/real_check-tur2.txt
  - .agents/tasks/T-008/evidence/real_check-taban-tur2-oncesi.txt
  - .agents/tasks/T-008/evidence/cov-tur2.txt
  - .agents/tasks/T-008/evidence/pytest-tum-tur2.txt
  - .agents/tasks/T-008/evidence/tdd-kirmizi-tur2.txt
  - .agents/tasks/T-008/evidence/geometri-etiket-kopru-tur2.py
  - .agents/tasks/T-008/evidence/geometri-etiket-kopru-tur2.txt
  - .agents/tasks/T-008/evidence/mutant-kiti-tur2.py
  - .agents/tasks/T-008/evidence/mutant-ayirt-etme-tur2.txt
  - .agents/tasks/T-008/evidence/mutant-ayirt-etme-tur2-hangi-testler.txt
commands:
  - cmd: "python -m mypy --strict --explicit-package-bases src/ocr/satir_birlestirici.py"
    exit_code: 0
    evidence: evidence/mypy-tur2.txt
  - cmd: "python -m pytest tests/unit/ocr/test_satir_birlestirici.py -q  (76 passed)"
    exit_code: 0
    evidence: evidence/pytest-tur2.txt
  - cmd: "python .agents/tasks/T-008/real_check.py  (TEMIZ 15/15; #1c 11 kutu -> 2 blok, en buyuk 6 parca)"
    exit_code: 0
    evidence: evidence/real_check-tur2.txt
  - cmd: "python -m pytest tests/unit/ocr/test_satir_birlestirici.py -q --cov=src.ocr.satir_birlestirici --cov-fail-under=95 --cov-report=term-missing  (100 ifade, %100)"
    exit_code: 0
    evidence: evidence/cov-tur2.txt
  - cmd: "python -m pytest tests -q  (1444 passed, dusen yok; sayi T-009 es zamanli testlerini icerir)"
    exit_code: 0
    evidence: evidence/pytest-tum-tur2.txt
  - cmd: "python -m mypy --strict --explicit-package-bases tests/unit/ocr/test_satir_birlestirici.py"
    exit_code: 0
    evidence: evidence/mypy-test-dosyasi-tur2.txt
  - cmd: "python -m pytest tests/unit/ocr/test_satir_birlestirici.py -q -p no:cacheprovider  (PYTHONIOENCODING YOK, stdout cp1254)"
    exit_code: 0
    evidence: evidence/pytest-cp1254-tur2.txt
  - cmd: "python .agents/tasks/T-008/real_check.py  (TABAN: tur 2 oncesi, tur 1 koduyla; #1c IHLAL 11 -> 1 blok / 11 parca -- olcu atesliyor)"
    exit_code: 1
    evidence: evidence/real_check-taban-tur2-oncesi.txt
  - cmd: "python -m pytest tests/unit/ocr/test_satir_birlestirici.py -q -p no:cacheprovider --no-header -rf  (TDD KIRMIZI: tur 2 testleri, tur 1 kodu; 5 failed, 71 passed)"
    exit_code: 1
    evidence: evidence/tdd-kirmizi-tur2.txt
  - cmd: "python .agents/tasks/T-008/evidence/geometri-etiket-kopru-tur2.py  (gercek OCR; fixtures/etiket_kopru_KR.png kutu geometrisi, metin yok; 11 kutu, tur 1 kodu 11 -> 1)"
    exit_code: 0
    evidence: evidence/geometri-etiket-kopru-tur2.txt
  - cmd: "python .agents/tasks/T-008/evidence/mutant-kiti-tur2.py  (T008_AYNA=<scratchpad>/t008_ayna_tur2; 23 mutant + 3 kontrol, ayna agaci; test adlari evidence/mutant-ayirt-etme-tur2-hangi-testler.txt)"
    exit_code: 0
    evidence: evidence/mutant-ayirt-etme-tur2.txt
contract_change_request: false
known_gaps:
  - "[TUR 2 OZETI] Sef karari tur 2 uygulandi. T2-1: `_satirlara_bol` referansi satirin ILK blogu degil EN KISA blogu (bag: `(y,x,idx)` sirasinda ilk; satira katilan blok daha kisaysa referans o olur) -- A'nin E diff'i temel alindi. T2-2: ayni-x/farkli-y cifti fixture'i (`(x, y, idx)`'nin `y` bileseni, 6 permutasyon). T2-3: docstring adim 3 metni, `[ÖLÇÜLMÜYOR] (fixture yok)` damgasi KALDIRILDI (sinif olculuyor), K6 cumlesi daraltildi. Birim 68 -> 76 (+8: 3 param sentetik kopru, gercek geometri kopru, kisa alt kutu siniri, satir ici merdiven, T2-2, cikti-anahtari bagi); kapsam %100 (100 ifade); mypy --strict modul + test temiz; real_check TEMIZ 15/15 (#1c 11 -> 2 `[6,5]`); tam takim 1444, dusen yok. Mutant kiti (ayna): 23/23 yakalandi, 3/3 kontrol kacti. `git commit` ATILMADI. `src/ocr/rapid_engine.py` ve `test_rapid_engine.py` calisma kopyasinda DEGISIK (T-009 implementer'i, bana ait degil; dokunmadim)."
  - "[T2-1 -- OLCU] Gercek fixture geometrisi (`fixtures/etiket_kopru_KR.png`, 11 kutu; etiket (57,55,125,72) = A'nin `kr_etiket_ortali_60_45_10`) bagimsiz kanaldan alindi (`evidence/geometri-etiket-kopru-tur2.py`, gercek motor, metin basilmaz) ve `ETIKET_KOPRU_GEOMETRI` olarak test dosyasina gomuldu (A'nin dizinine yaslanilmadi; `tester_A/` OKUNMADI). `test_k2_uzun_kutu_koprusu_gercek_geometri_11_kutu_iki_blok_6_5`: her cizilen satirin 5 kutusu TAM OLARAK BIR blokta, iki satir ayni blokta DEGIL, `[6,5]` (etiket satir 0'a yapisik), x sirali, ters girdi ayni; etiketsiz pozitif kontrol 10 -> `[5,5]`. Sentetik (Tester-B geometrisi, `feedback-B.md`): T(0,0,40,60) + a/b/c (y=5) + d/e/f (y=40, kaydirma 5/0/12) -> `[\"T a b c\", \"d e f\"]`; etiketsiz `[\"a b c\", \"d e f\"]`. TDD kirmizi: tur 1 koduyla bu 5 test duser (`tdd-kirmizi-tur2.txt`); real_check #1c tur 1 koduyla IHLAL (`real_check-taban-tur2-oncesi.txt`: 11 -> 1 blok / 11 parca) -- olcu ateşliyor (§4.6/10)."
  - "[T2-1 -- AYIRT ETME, ayna agaci] M21 E geri alinmis (referans = satirin ilk blogu, tur 1 kodu): 5 test duser (3 sentetik kopru + gercek geometri + kisa alt kutu siniri). M22 referans = EN UZUN blok (`<` -> `>`): 6 test (ustteki 5 + `test_k6_bagli_durumda_satir_referansi_en_kisa_girdi_sirasindan_bagimsiz`). M17 (yeniden hedeflendi) referans = SON EKLENEN blok: 2 test (merdiven + k6 bagli durum). M24 bag `<=` (esit yukseklikte SON kisa blok referans olur): 1 test (merdiven; a/b/c hepsi h=20, bag -> a; `<=` ile b referans olur, c b ile ortusur ve `c b` birlesir) -- 'bag: ilk' olculuyor. Kit: `evidence/mutant-kiti-tur2.py`, ham: `mutant-ayirt-etme-tur2.txt`, test adlari: `mutant-ayirt-etme-tur2-hangi-testler.txt`."
  - "[T2-2 -- OLCU] `test_k6_ayni_x_farkli_y_satir_ici_sira_y_ile_permutasyonlar_ayni`: p(0,0,50,20) q(0,10,50,20) r(55,10,50,20) -- p/q ayni x (ikincisi yeni grup acar, K2 `x KESIN ilerliyor`), r acik (SON) gruba katilir; `y` anahtarda oldugu icin acik grup her girdi sirasinda q -> `[\"p\", \"q r\"]`, 6 permutasyon ayni (K6). Mutant M23 `(x, idx)` (y'siz): [q,p,r] girdisinde acik grup p olur, r p'ye katilir -> `[\"p r\", \"q\"]` -- 2 testle yakalanir (bu test + `test_k6_cikti_anahtarinda_bag_girdi_sirasina_bagli_sinir`). Tur 1'de hicbir fixture ayni x'li iki kutu icermiyordu (Tester-B M41 kaciyordu)."
  - "[T2-3 -- BELGE] Docstring: adim 3 metni (referans = en kisa, bag: ilk; tur 1'de ilk blok), yeni paragraf 'Satir referansi ve uzun kutu koprusu (T2-1, OLCULDU)' (fixture, olcu adlari, real_check #1c, 'ilk'/'en uzun' olsaydi duser), 'Grup icinde dikey referans' paragrafi yeniden yazildi (adim 4 DEGISMEDI: grubun ilk blogu; satir ici merdiven + uzun kutu solda ornekleri). `[ÖLÇÜLMÜYOR] gercek OCR'da (fixture yok)` cumlesi KALDIRILDI. K6: '`(y,x)` bagi olmayan girdide her permutasyon ayni' -> 'iki CIKTI blogunun `(y,x)`'i esit olmadikca'; bag girdide ayni `(y,x)` olmadan da dogabilir (A'nin ornegi C/A/B: `[C, A B]` / `[A B, C]`, `test_k6_cikti_anahtarinda_bag_girdi_sirasina_bagli_sinir` ile SABITLENDI; urun etkisi yok, normalizer yeniden siralar). 'Bagli iki kutudan girdide once gelen satirin referans blogu olur' cumlesi KALDIRILDI (artik yanlis: referans en kisa, bag sirasi uyeligi etkilemez). Docstring'de anilan 12 test adinin hepsi test dosyasinda var (dogrulandi)."
  - "[SECILEN KURALIN SINIRI -- kisa alt kutu] Satirin ALTINA sarkan kisa kutu (orn. h=12 noktalama) referans olursa, bir sonraki satir onunla `>= 0.5*h_kisa` ortusecek kadar yakinken (yani satirlar birbirine girmisken) ayni satira girer ve x sirasi satirlari karistirir. Sentetik SABITLENDI (`test_k2_satir_referansi_en_kisa_blok_kisa_alt_kutu_siniri_sabitlendi`: w1 w2 (h=30) + p(110,20,8,12) + n1 n2; aralik 27 -> `[\"w1 w2 p\", \"n1 n2\"]` butun, aralik 26 (ortusme 6 = 0.5*12) -> parcalanir). Tur 1 kurali (ilk blok) bu geometride bozulmuyordu; secilen kural burada daha zayif -- bilincli takas (KRT O2 sinifi gercek, bu sinif sentetik). Gercek OCR'da `[ÖLÇÜLMÜYOR]`: tespitci noktalamayi kelime kutusuna dahil ediyor (dlg_KR 17 kutu, ayri noktalama kutusu yok; KR nokta tanimi zaten T-009) ve gercek satir araligi >= 10 px (satirlar birbirine girmiyor). Bu sinifta fixture uretilemedi; A'nin onerdigi 'en kisa, ama `h >= 0.5*medyan`' siniri sefin kararinda YOK, uygulanmadi (mekanizma degisikligi = sef karari)."
  - "[BAYATLAYAN TESLIM TESTLERI -- yeniden nisanlandi (§4.6/5)] (1) `test_k2_satir_bolumleme_satirin_ilk_bloguna_gore` -> `test_k2_satir_bolumleme_satirin_referansiyla_bir_oncekiyle_degil`: assert ayni (merdiven a/b/c -> uc ayri), docstring 'ilk blok' -> 'referans (en kisa, bag: ilk); hepsi h=20 -> a'; M17 (son eklenen) + M24 (`<=`) burada duser. (2) `test_k2_grup_icinde_dikey_ortusme_grubun_ilk_bloguyla` (T ORTADA) -> T2-1 sonrasi c ayri SATIRA dustugu icin M18'i (grup referansi ilk -> son) AYIRT EDEMIYORDU (gecer ama olcusuz); ikiye bolundu: `..._uzun_kutu_solda` (T(0,0,40,60) a b c, c b ile 9 < 10 ortusur ama grubun ilk blogu T ile 20 -> tek blok; son-referans mutanti c'yi ayirir) ve `..._satir_ici_merdiven` (A(0,0,50,20) S(55,11,40,18) B(100,20,50,20) -> `A S`, `B`; son-referans `A S B`). M18 2 testle yakalanir. (3) `test_k6_bagli_durumda_satir_referansi_ilk_girdi_blogu` -> `..._en_kisa_girdi_sirasindan_bagimsiz`: assert ayni ([a,b,c] -> a,b,c; [b,a,c] -> b,a,c), docstring yanlis olmustu ('once gelen referans olur'; artik en kisa) -- M17/M22 burada duser; E geri alinmis (M21) bu geometride AYNI ciktiyi verir (c satira girer ama a'nin grubu araya girer), bunu docstring acikca soyler. (4) Eski M04 (`-idx`, ilk siralamada bag ters) tur 1'de yalniz (3) ile yakalaniyordu; T2-1 sonrasi DAVRANIS-ESDEGER: bagli ciftin isleme sirasi ne satir uyeligini ne referansi degistirir (ikisi de satira girer, en kisa referans olur), satir ici `(x,y,idx)` ve cikti `(y,x,min idx)` yeniden siralar -> kitte C-3 KONTROL olarak yeniden siniflandi ve olculdu: 0 test duser (kacmasi dogru; C-1 ile ayni sinif). Tur 1 `[K5/K6/K8]` notundaki 'M04 `-idx` mutanti 1 testle yakalanir' cumlesi bu turla GECERSIZ."
  - "[K2 -- GRI BOLGE KAYDI, tur 1'den; uzun kutu cumlesi GUNCELLENDI] Gri bolge [0.6, 0.95] x h sinif olarak `[ÖLÇÜLMÜYOR]`; olculen iki ornek: menu fixture'inda `/`-`150` boslugu 1.04 -> AYRILIR, KR 1-em `kr_menu_2sutun_1h` 2. satir 0.78 -> AYRILIR ama esige 0.03 x h (~1 px) mesafede. Uzun kutu koprusu (cok satiri tek kutuda veren tespit) tur 1'de `[ÖLÇÜLMÜYOR]` idi -- tur 2'de OLCULDU ve duzeltildi (yukarida T2-1)."
  - "[TUR 1 KAYITLARI -- gecerliligini koruyanlar, ozet] ITIRAZ 1 (paketin tek-gecis K2 lafzi gercek KR'de 17 -> 9; uygulama satir bolumleme + satir ici x siralama; `test_itiraz_paket_lafzi_*`), ITIRAZ 2 (`real_check` #4b 10.0 mutantini dusurmuyor; 1-em sinifi `olcum-2`, sef #4c'yi ekledi), K2 kararlar (farkli `dpi_scale` birlesmez; `x` KESIN ilerliyor; ic ice birlesir SABITLENDI; yozlasmis kutu komsulugu bozmaz), K3 betik (uyumluluk ideografi/yarim genislik CJK; harfsiz parca LATIN; bos parca kutuya girer metne girmez), K4 (tek uygulama, `f(f(x)) != f(x)` Y2'de), K5/K8 (bbox int, NaN suzgecli min, tek parca `is`). Ayrintilar tur 1 teslimindeki `evidence/olcum-*` ve `mutant-ayirt-etme.txt`'de; degismedi."
---

# T-008 tur 2 -- teslim ozeti

Sef karari tur 2 (`sef_karari-tur2.md`) uc kalemiyle uygulandi; garanti alani `src/ocr/satir_birlestirici.py` modul docstring'i (adim 3, "Satir referansi ve uzun kutu koprusu", K6).

## T2-1 (bloke) -- satir referansi = satirin EN KISA blogu

`_satirlara_bol`: referans satira katilan her blokla `h` kucukse guncellenir (bag: ilk). Etiket koprusu gercek OCR'da 11 -> **2** blok `[6, 5]` (`real_check` #1c ok; tur 1 koduyla IHLAL, taban kanitta). Gercek geometri (`fixtures/etiket_kopru_KR.png`, bagimsiz kanaldan alindi, `tester_A/` okunmadi) + Tester-B'nin sentetik geometrisi (3 kaydirma) test dosyasina gomuldu; etiketsiz pozitif kontroller `[5,5]` / `["a b c","d e f"]`.

## T2-2 -- ayni-x cifti

p(0,0) q(0,10) r(55,10): `(x, y, idx)` ile 6 permutasyon ayni `["p", "q r"]`; `(x, idx)` mutanti 2 testle duser.

## T2-3 -- belge

Adim 3 metni; `[ÖLÇÜLMÜYOR] (fixture yok)` kaldirildi; K6 "iki CIKTI blogunun `(y,x)`'i esitse" diye daraltildi ve A'nin C/A/B ornegi testle sabitlendi. Secilen kuralin kendi siniri (kisa alt kutu + birbirine girmis satirlar) sentetik sabitlendi, gercek OCR'da `[ÖLÇÜLMÜYOR]` gerekceli.

## Yeniden nisanlanan testler (4)

`..._satirin_ilk_bloguna_gore` -> `..._satirin_referansiyla_bir_oncekiyle_degil`; `..._grubun_ilk_bloguyla` (T ortada, M18'i artik ayirt edemiyordu) -> `..._uzun_kutu_solda` + `..._satir_ici_merdiven`; `..._satir_referansi_ilk_girdi_blogu` -> `..._en_kisa_girdi_sirasindan_bagimsiz`; eski M04 (`-idx`) T2-1 sonrasi davranis-esdeger -> kontrol C-3 (olculdu, kacar).

## Sayilar

| olcu | sonuc |
|---|---|
| birim | 76 passed (68 + 8), kapsam %100, mypy --strict modul + test temiz |
| tam takim | 1444 passed, dusen yok (T-009 es zamanli testleri dahil) |
| real_check | TEMIZ 15/15; #1c 11 -> 2 blok, en buyuk 6 parca; 1000 blok 3.1 ms |
| mutant (ayna) | 23/23 yakalandi (M21 E-geri 5, M22 en uzun 6, M23 `(x,idx)` 2, M24 bag `<=` 1), 3/3 kontrol kacti |
