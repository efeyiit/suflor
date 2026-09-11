---
task: T-008
role: implementer
round: 1
status: tamamlandi
files_written:
  - src/ocr/satir_birlestirici.py
  - tests/unit/ocr/test_satir_birlestirici.py
  - .agents/tasks/T-008/delivery.md
  - .agents/tasks/T-008/evidence/mypy.txt
  - .agents/tasks/T-008/evidence/mypy-test-dosyasi.txt
  - .agents/tasks/T-008/evidence/pytest.txt
  - .agents/tasks/T-008/evidence/pytest-cp1254.txt
  - .agents/tasks/T-008/evidence/real_check.txt
  - .agents/tasks/T-008/evidence/cov.txt
  - .agents/tasks/T-008/evidence/pytest-tum.txt
  - .agents/tasks/T-008/evidence/tdd-kirmizi-1-modul-yok.txt
  - .agents/tasks/T-008/evidence/mutant-kiti.py
  - .agents/tasks/T-008/evidence/mutant-ayirt-etme.txt
  - .agents/tasks/T-008/evidence/olcum-1-k2-lafzi-vs-uygulama-gercek-ocr.py
  - .agents/tasks/T-008/evidence/olcum-1-k2-lafzi-vs-uygulama-gercek-ocr.txt
  - .agents/tasks/T-008/evidence/olcum-2-1em-pozitif-kontrol-gercek-ocr.py
  - .agents/tasks/T-008/evidence/olcum-2-1em-pozitif-kontrol-gercek-ocr.txt
  - .agents/tasks/T-008/evidence/fixtures-1em/jp_secim_ideospace.png
  - .agents/tasks/T-008/evidence/fixtures-1em/jp_secim_gap1h.png
  - .agents/tasks/T-008/evidence/fixtures-1em/kr_menu_2sutun_1h.png
  - .agents/tasks/T-008/evidence/fixtures-1em/kr_menu_2sutun_2h.png
commands:
  - cmd: "python -m mypy --strict --explicit-package-bases src/ocr/satir_birlestirici.py"
    exit_code: 0
    evidence: evidence/mypy.txt
  - cmd: "python -m pytest tests/unit/ocr/test_satir_birlestirici.py -q"
    exit_code: 0
    evidence: evidence/pytest.txt
  - cmd: "python .agents/tasks/T-008/real_check.py"
    exit_code: 0
    evidence: evidence/real_check.txt
  - cmd: "python -m pytest tests/unit/ocr/test_satir_birlestirici.py -q --cov=src.ocr.satir_birlestirici --cov-fail-under=95 --cov-report=term-missing"
    exit_code: 0
    evidence: evidence/cov.txt
  - cmd: "python -m pytest tests -q"
    exit_code: 0
    evidence: evidence/pytest-tum.txt
  - cmd: "python -m mypy --strict --explicit-package-bases tests/unit/ocr/test_satir_birlestirici.py"
    exit_code: 0
    evidence: evidence/mypy-test-dosyasi.txt
  - cmd: "python -m pytest tests/unit/ocr/test_satir_birlestirici.py -q -p no:cacheprovider  (PYTHONIOENCODING YOK, stdout cp1254)"
    exit_code: 0
    evidence: evidence/pytest-cp1254.txt
  - cmd: "python -m pytest tests/unit/ocr/test_satir_birlestirici.py -q -p no:cacheprovider --no-header  (TDD KIRMIZI: testler yazildi, modul henuz yok -- ImportError)"
    exit_code: 2
    evidence: evidence/tdd-kirmizi-1-modul-yok.txt
  - cmd: "python .agents/tasks/T-008/evidence/mutant-kiti.py  (T008_AYNA=<scratchpad>/t008_ayna; 20 mutant + 2 kontrol, ayna agaci)"
    exit_code: 0
    evidence: evidence/mutant-ayirt-etme.txt
  - cmd: "python .agents/tasks/T-008/evidence/olcum-1-k2-lafzi-vs-uygulama-gercek-ocr.py  (gercek OCR; paket K2 lafzi vs uygulama; esik taramasi dlg_KR + menu)"
    exit_code: 0
    evidence: evidence/olcum-1-k2-lafzi-vs-uygulama-gercek-ocr.txt
  - cmd: "python .agents/tasks/T-008/evidence/olcum-2-1em-pozitif-kontrol-gercek-ocr.py  (gercek OCR; 1-em bosluk sinifi dort fixture, esik taramasi)"
    exit_code: 0
    evidence: evidence/olcum-2-1em-pozitif-kontrol-gercek-ocr.txt
contract_change_request: false
known_gaps:
  - "[TUR 1 OZETI] `src/ocr/satir_birlestirici.py` (95 ifade, kapsam %100) + `tests/unit/ocr/test_satir_birlestirici.py` (68 test, sentetik `TextBlock`, OCR yok, mypy --strict temiz). Bes kabul komutu exit 0; tam takim 1359 -> 1427 (+68), dusen YOK. `real_check` TEMIZ: KR 17 -> 4 `[2,5,5,5]`, JP/EN no-op, normalize 2 segment, NMT tek-kelimelik ceviri 0, menu KR 13 -> 9 (her satir >= 2), EN 8 -> 8, saflik temiz, 1000 blok medyan 2.6 ms. Mutant kiti (ayna agaci): 20 davranis mutanti 20/20 YAKALANDI (1-9 test), 2 kontrol 2/2 KACTI. `git commit` ATILMADI. Entegrasyon (pipeline'da `normalize` oncesi cagri) bu paketin kapsami disinda -- `src/ocr/__init__.py` ve `demo/**` yasak; KRT O6 hala acik."
  - "[K2 -- ITIRAZ 1: PAKETIN TEK-GECIS LAFZI GERCEK KR'DE 17 -> 9 VERIR, 4 DEGIL] Paket v2 K2: `(y,x,idx)` sirala, TEK GECIS, acik grubun ILK bloguyla dikey ortusme, SON bloguna gore x ilerleme + bosluk. Bunu birebir kodlayip gercek OCR ciktisina uyguladim (`olcum-1`, [A]): 17 -> 9 grup, parca sayilari [2,5,1,2,1,1,2,1,2]; `real_check` #1 bu lafizla DUSER. Kok: ayni satirdaki kelime kutularinin `y`'si 1-4 px titrer (satir 3: y=212/209/209/208/210); `(y,x)` sirasi satir 3'u x=386,225,305,467,82 dizer; `x ilerliyor` kosulu satiri parcalar. Paketin dayandigi '`(y,x)` sirasi = satir ici x sirasi' varsayimi gercek OCR'da tutmaz (KRT'nin 'birikimli' varyanti da 'x-sirali tarama' diyordu, yani satir ici x siralamasi vardi -- paket bunu tek siralama diye yazdi). UYGULAMA (ayni degismezler, `O(n log n)`): (1) `(y,x,idx)` sirala; (2) yozlasmis kutulari ayir, kalanlari `(monitor_index, dpi_scale)` yuzeylerine bol; (3) satir bolumleme: satirin ILK bloguyla dikey ortusme >= 0.5*min(h) (tek gecis); (4) satir icinde `(x,y,idx)` sirala, tek gecis: grubun ILK bloguyla dikey ortusme VE son bloga gore x KESIN ilerliyor VE bosluk <= 0.75*min(h_son,h_aday) -- hep OZGUN yukseklikler; (5) cikti `(y,x,en kucuk girdi indeksi)`. Satir uyeligi satirin ILK bloguyla (merdiven tek satir degil, `test_k2_satir_bolumleme_*`, mutant M17), grup ici dikey referans GRUBUN ilk blogu (uzun kutu koprusu: c ayri, `test_k2_grup_icinde_*`, M18). Birim izi: `test_itiraz_paket_lafzi_kr_geometrisinde_dokuz_grup_verir` (lafiz 9, uygulama 4) ve `test_k2_y_titresimli_satir_x_sirasinda_birlesir_itiraz`. Paketin K2 metni 'sirala + tek gecis' yerine 'sirala + satir bolumleme + satir ici x siralama + tek gecis' diye duzeltilmeli; degismezler degismedi."
  - "[K2/K7 -- ITIRAZ 2: `real_check` #4b 10.0 MUTANTINI DUSURMUYOR; PAKETIN CUMLESI OLCULMEMIS] Paket: 'Esigi 2.0/10.0 yapan mutant dlg_KR'de yine 4 verir -- bu yuzden menu fixture'i zorunlu: orada 10.0 birlestirir ve duser.' Olctum (`olcum-1` [B]/[C], modul sabiti gecici degistirilerek): menu fixture'inda etiket|deger boslugu 13.1-16.3 x min(h) (KR 14.85/13.62/15.59/14.11, EN 13.37/14.18/16.27/13.10); 10.0 < 13.1 oldugu icin 10.0 ile de HICBIR etiket|deger birlesmez, #4b 'ok' verir (KR 13 -> 8, EN 8 -> 8, her satir >= 2). Paketin kendi sayisi (13-16 x h) bunu zaten soyluyordu. Kapinin gercek ayirt penceresi: 0.57 -> dlg_KR 5 blok (#1 IHLAL); 0.75/1.0/2.0/10.0 -> #1 ve #4b 'ok'. Yani kapi esigi yalniz (0.57, 13.1) araligina daraltiyor; 0.75'in sebebi olan 1-em sinifi (0.97-1.06) kapida HIC yok (§4.6/10: sinif hic ugramiyor). Telafi olcumu (`olcum-2`, KRT'nin sentetik goruntuleri `evidence/fixtures-1em/`, gercek motor): JP ideografik bosluk 1.03, JP 1-em 1.14, KR etiket|deger 1.06 ve 0.78 -> esik 0.75 dort fixture'da kutu sayisini korur (3/2/4/4); 1.0 (v1) KR 0.78'i birlestirir (4 -> 3); 2.0 ve 10.0 hepsini birlestirir. Birim testi de 0.76 ve 3 x h'yi ayirir; mutant M01 (10.0) 9 testle yakalanir. ONERI (sef dosyasi, ben yazamam): `real_check` #4b'ye `fixtures-1em`'den bir goruntu (orn. `kr_menu_2sutun_1h.png`: 0.75 -> 4, 1.0 -> 3, 2.0 -> 2) eklenirse kapi 0.75'i 1.0/2.0/10.0'dan ayirir; packet'teki '10.0 burada duser' cumlesi duzeltilmeli."
  - "[K2 -- GRI BOLGE KAYDI] Gri bolge [0.6, 0.95] x h sinif olarak [ÖLÇÜLMÜYOR]; olculen iki ornek: menu fixture'inda `/`-`150` boslugu 1.04 -> AYRILIR (sefin olcumuyle ayni), KR 1-em `kr_menu_2sutun_1h` 2. satir 0.78 -> AYRILIR ama esige 0.03 x h (~1 px, h=31) mesafede -- font/olcek degisince donebilir. Uzun kutu koprusu (cok satiri tek kutuda veren tespit) ayni SATIRA toplayabilir; grup ici referans ilk blok oldugu icin gruplar geometriye bagli, gercek OCR'da fixture yok [ÖLÇÜLMÜYOR]."
  - "[K2 -- KARARLAR, PAKET SESSIZDI] (a) Farkli `dpi_scale` BIRLESMEZ (yuzey anahtari `(monitor_index, dpi_scale)`): normalizer K10 `_union_rect` farkli `dpi_scale`'i `ValueError` ile reddeder; burada sessiz kopyalama olmasin diye; K5 'ilk parcadan' cumlesi boylece her zaman dogru. Olcu `test_k2_farkli_dpi_scale_birlesmez`, mutant M09. (b) `x ilerliyor` = KESIN buyuk (`aday.x > son.x`): ayni x'teki cift tespit yeni grup acar (metin cogalmaz), `x` ilerleyen ic ice kutu BIRLESIR ve metin cogalir (S6 geri cekildi; `test_k2_ic_ice_*` ile SABITLENDI; cakisma siniri yok -- KRT O2'nin `-0.5*min(w)` onerisi pakete girmedi, uygulamadim). (c) Yozlasmis kutu (`h<=0` ya da `w<=0`) bolumlemeye hic girmez; araya girdigi iki komsuyu AYIRMAZ (A, Z(w=0), B -> 'A B' + Z; `test_k2_yozlasmis_*`, M16). Paketin tek-gecis lafzinda yozlasmis kutu grubu bolerdi."
  - "[K3 -- BETIK] `unicodedata.name` icinde HIRAGANA / KATAKANA / CJK UNIFIED IDEOGRAPH / CJK COMPATIBILITY IDEOGRAPH gecen ILK HARF (`str.isalpha`) -> CJK; degilse LATIN. KARAR: paket 'Hiragana/Katakana/CJK Unified' der; yarim genislik katakana (`HALFWIDTH KATAKANA LETTER`), `ー` (`KATAKANA-HIRAGANA PROLONGED SOUND MARK`) ve uyumluluk ideograflari da CJK sayildi (ayni degismezin alt kumesi; tabloda olculdu). Harfsiz parca (`。`, `！？`, salt rakam) LATIN -> bosluk: `待って 。`, `42 点` (paket boyle yaziyor; KRT D1'in 'komsunun betigini al' onerisi pakete girmedi) -- testte SABITLENDI. `々`/`〆`/Bopomofo LATIN [ÖLÇÜLMÜYOR] (nadir). Her parca strip; strip sonrasi BOS parca `text`e katilmaz (ayirici da eklenmez) ama kutu/guven hesabina girer (KARAR; gercek motor bos metin vermez, T-006 K5); hepsi bos -> `\"\"`. Mutantlar M05 (CJK bosluklu) 6 test, M14 (strip yok) 4, M20 (bos parca) 1."
  - "[K4 -- TEK UYGULAMA] Docstring'de yasak sozcuk gecmiyor (`grep` bos; `test_k4_docstring_*` AST ile 'idempoten' yok + 'bir kez' uyarisi VAR pozitif kontrol). `f(f(x)) != f(x)` Y2 fixture'inda 2 -> 1 olarak SABITLENDI (`test_k4_ikinci_uygulama_*`, degismez degil, belge). Pipeline'da tek cagri garantisi bu modulun disinda -- cagri noktasi sahipsiz (KRT O6)."
  - "[K5/K6/K8] K5: bbox birlesim int (ek donusum yok; girdi float ise float -- tip denetimi yok, paket bilincli), `confidence` NaN-suzgecli min (NaN ilk/son/orta -> ayni; hepsi NaN -> NaN), `line_boxes` parcalarin bbox'lari x sirasinda (kendi `line_boxes`'lari degil), tek parca `is` ayni nesne ve `line_boxes` dokunulmaz. K6: cikti `(y, x, en kucuk girdi indeksi)`; bagsiz girdide 5 karisik KR sirasi ve 4 kutunun 24 permutasyonu ayni; bagli `(y,x)` cift -> girdi sirasi (SABITLENDI: ters girdi ters cikti; monitorler arasi bagda da girdi indeksi, isleme sirasi degil -- M04 `-idx` mutanti 1 testle yakalanir). K6 SINIRI: bagli iki kutudan girdide once gelen satirin REFERANS blogu olur; yukseklikleri farkliysa sonraki kutularin satir uyeligi buna baglidir (`test_k6_bagli_durumda_satir_referansi_*` [a,b,c] -> a,b,c / [b,a,c] -> b,a,c). Ayni satirdaki iki grup da `(y,x)` sirasinda (sagdaki grubun min y kucukse once gelir -- normalizer zaten yeniden siralar). K8: bos -> [], tek -> ayni nesne, negatif koordinat normal, `h<0`/`w<0` = `h=0`; `confidence` araligi denetlenmez (normalizer K7'nin isi); numpy denetimi yok."
  - "[MUTANT KITI -- KONTROL NOTU] C-1 'ilk siralama anahtarindan `idx` cikarildi' KACIYOR ve kacmasi DOGRU: `sorted` kararli, girdi `enumerate` sirasinda verildigi icin `(y,x)` anahtari da baglari girdi sirasiyla cozer -- davranis esdeger. 'Ucuncu anahtar yok' sinifinin davranis degistiren hali `(y,x,-idx)` (M04) ve bu YAKALANIYOR. Gorevin istedigi 8 mutantin karsiliklari: 0.75->10.0 = M01 (9 test), 0.5->0.0 = M02 (3), birlesik yukseklik = M03 (2), ucuncu anahtar = M04 (1) + C-1 (esdeger, kontrol), CJK bosluklu = M05 (6), min->max = M06 (3), line_boxes bos = M07 (6), monitor_index yok = M08 (1). Ek 12 mutant: dpi, `>`/`>=`, `<=`/`<`, `>=`/`>`, NaN suzgeci, strip, son siralama, yozlasmis, satir referansi, grup referansi, max(h), bos parca -- hepsi yakalandi."
  - "[SEF ICIN OLCUM NOTLARI] (1) `real_check` 7 s surdu (~30 s degil; model onbellekte). (2) Menu KR 13 -> 9: deger ici bosluklar 0.17-0.26 x h birlesti (sefin 'birlesmeli' olcumuyle uyumlu); KR satir 4 (round(y/50)=4) OCR'da hic kutu vermedi, satir anahtarlari 1,2,3,5. (3) `evidence/fixtures-1em/` KRT'nin scratchpad'deki sentetik goruntuleri (sistem fontu, 1200x400); sefin `fixtures/` dizinine ben yazamam."
---

# T-008 tur 1 -- teslim ozeti

Ayrintilar YAML `known_gaps` alaninda; garanti alani `src/ocr/satir_birlestirici.py` modul docstring'inde (K1-K8, her biri test adiyla ya da `[ÖLÇÜLMÜYOR]` damgasiyla).

## Iki itiraz (ikisi de olculdu, ham cikti `evidence/`)

1. **Paketin K2 tek-gecis lafzi gercek KR'de 17 -> 9 verir.** `olcum-1` [A]: `(y,x,idx)` sirasi satir ici x sirasi degil (y titresimi 1-4 px). Uygulama satir bolumleme + satir ici x siralama + tek gecis; degismezler ayni; `real_check` #1 4 veriyor.
2. **`real_check` #4b `10.0` mutantini dusurmuyor.** `olcum-1` [B]/[C]: etiket|deger boslugu 13.1-16.3 x h > 10. Kapi 0.75'i 1.0/2.0/10.0'dan ayiramiyor; 1-em sinifi icin gercek pozitif kontrol `olcum-2` (0.75 korur, 1.0 KR 0.78'i birlestirir). Oneri: `fixtures-1em/kr_menu_2sutun_1h.png` #4b'ye eklensin (sef dosyasi).

## Sayilar

| olcu | sonuc |
|---|---|
| birim | 68 passed, kapsam %100, mypy --strict (modul + test) temiz |
| tam takim | 1427 passed (1359 + 68), dusen yok |
| real_check | TEMIZ (13/13 ok), 1000 blok 2.6 ms |
| mutant | 20/20 yakalandi, 2/2 kontrol kacti |
