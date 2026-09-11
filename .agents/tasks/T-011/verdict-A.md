---
task: T-011
role: tester
round: 1
decision: onay
checks:
  - name: "taban 1 -- mypy --strict temiz"
    cmd: "python -m mypy --strict --explicit-package-bases src/translate/sozluk.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/taban-1-mypy.txt
  - name: "taban 2 -- implementer birim testleri 256 passed"
    cmd: "python -m pytest tests/unit/translate/test_sozluk.py -q -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/taban-2-pytest.txt
  - name: "taban 3 -- real_check TEMIZ 12/12 (#7 medyan 36.0 ms < 50; #6c bilinen sinir 1 hit raporlandi)"
    cmd: "python .agents/tasks/T-011/real_check.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/taban-3-real_check.txt
  - name: "taban 4 -- kapsam %100 (301 ifade, 0 eksik)"
    cmd: "python -m pytest tests/unit/translate/test_sozluk.py -q -p no:cacheprovider --cov=src.translate.sozluk --cov-fail-under=95 --cov-report=term-missing"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/taban-4-kapsam.txt
  - name: "taban 5 -- tam takim 1700 passed"
    cmd: "python -m pytest tests -q -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/taban-5-tum-takim.txt
  - name: "A -- mercek-A 162 passed (145 dogrulama + 17 `test_bulgu_*` pin); her negatif icin ayni siniftan pozitif kontrol"
    cmd: "python -m pytest .agents/tasks/T-011/tester_A -p no:cacheprovider --import-mode=importlib -v -rfE"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/A-mercek-testleri.txt
  - name: "A -- implementer + mercek-A ayni oturumda 418 passed (etkilesim yok)"
    cmd: "python -m pytest tests/unit/translate/test_sozluk.py .agents/tasks/T-011/tester_A -q -p no:cacheprovider --import-mode=importlib -rfE"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/A-birlikte-kosum.txt
  - name: "sonda 1 -- sinir simetrisi: KR ek yalniz sag / zincir 2 / 3 ret, JP parcacik iki taraf, uc terim bitisik, Latin bitisik terimler (millelder -> 2 hit), Cf karakterleri hit kesiyor"
    cmd: "python .agents/tasks/T-011/tester_A/sonda_01_sinir.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/sonda-01-sinir.txt
  - name: "sonda 2 -- IGNORECASE (Kelvin, uzun s, Turkce I sinifi, sigma, Kiril), eszett/ligature eslesmez ama tekrar sayilir, NFD metin indeksleri NFC'ye gore, gom NFD segment -> NFC cikti (aralik disi kodpoint degisir), astral kodpoint indeksi"
    cmd: "python .agents/tasks/T-011/tester_A/sonda_02_ignorecase_nfc.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/sonda-02-ignorecase-nfc.txt
  - name: "sonda 3 -- yer tutucu sinirlari (ic ice/ortusen/bos/uzun/terim icinden/yt==terim), NFD segment placeholders-text iliskisi kopuyor, 52 sema sinir girdisi (10000 kodpoint kaynak -> RecursionError), 14 gecersiz hit -> ContractViolation sizintisiz, 0 bayt stdout/stderr/log/warnings"
    cmd: "python .agents/tasks/T-011/tester_A/sonda_03_yertutucu_sema.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/sonda-03-yertutucu-sema.txt
  - name: "sonda 4 -- RecursionError esigi N=995/996 (tek terim; 2000 terim x 52 gecer; 300 kodpoint JP cumle gecer), 9500 kodpoint segment 1500 hit 25 ms, 5000 terim yukleme 75 ms / lookup 0.26 ms, 1000 seg x {11,50,500,5000} terim 30-36 ms (oran 0.95-1.14), onek zinciri a*10000 -> 850 ms"
    cmd: "python .agents/tasks/T-011/tester_A/sonda_04_buyuk.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/sonda-04-buyuk.txt
  - name: "sonda 5 -- hit sayisinda KARESEL (2x hit -> 3.2-3.9x; 8000 hit 472 ms; hit sabitken uzunluk etkisiz), real_check #7 yolu modelsiz 16 ms, windmill/windmills/elderly Latin bilesik bolunmesi, bagimsiz IGNORECASE taramasi 2912 cift 0 ayrisma"
    cmd: "python .agents/tasks/T-011/tester_A/sonda_05_olcek.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/sonda-05-olcek.txt
  - name: "sonda 6 -- GERCEK MOTOR (ayri surec): 'The windmills turn slowly.' ham dogru, gomulu 'Rüzgarmills' -> ciktida degirmen KAYIP, melez kelime sizdi; 2 pozitif kontrol dogru"
    cmd: "python .agents/tasks/T-011/tester_A/sonda_06_gercek_model.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/sonda-06-gercek-model.txt
  - name: "sonda 7 -- trie dal ayrismasi: {Maßen, Maẞer, Maße} sozlugunde harfiyen gecen 'Maẞer' eslesmez, JSON sirasi tersken eslesir; Yunan iota-subscript ayni; regex-ozel ilk karakterler 8/8 temiz"
    cmd: "python .agents/tasks/T-011/tester_A/sonda_07_trie_dal.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/sonda-07-trie-dal.txt
  - name: "depo dokunulmadi: git status --short -- src tests real_check packet fixtures BOS; git diff HEAD -- src tests 0; kaynak/test/real_check sha256; HEAD 1ff6a8a (kosum boyunca sozluk.py degismedi)"
    cmd: "git status --short -- src tests .agents/tasks/T-011/real_check.py .agents/tasks/T-011/packet.md .agents/tasks/T-011/fixtures; git diff HEAD --stat -- src tests; sha256sum ..."
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/A-git-status-depo-dokunulmadi.txt
  - name: "korluk kaydi: implementer test ADLARI (113) yalniz 'hangi sinif hic test edilmemis' icin, tum mercek testleri ve sondalar bittikten sonra grep'lendi; govde acilmadi"
    cmd: "grep -n '^def test_' tests/unit/translate/test_sozluk.py | sed 's/(.*//'"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/A-implementer-test-adlari.txt
blocking_issues: []
---

# T-011 tur 1 -- Tester-A (mercek: garanti alani + sinir)

Karar: **ONAY**. Bes taban komutu bu makinede temiz (mypy 0, 256 passed, real_check TEMIZ 12/12, kapsam %100, tam takim 1700). Docstring'in K1-K7 iddialari **kabul edilen gercekci girdilerin tamaminda** tutuyor: 162 mercek testi + 7 sonda; sinir kurali simetrisi (KR ek yalniz sag, zincir <= 2, JP parcacik iki taraf), en-uzun-once/ortusmesiz/JSON-sirasindan-bagimsiz esit uzunluk, IGNORECASE `source_term` metinden + kodpoint indeks, NFD girdi NFC indeks, yer tutucu korumasi (ic ice/ortusen/terim icinden/yt==terim), 14 gecersiz hit sinifi `ContractViolation` ve **hicbir mesaj metin/terim/hedef tasimiyor**, 0 bayt kanal, dosya silinince lookup, 5000 terimde maliyet degismiyor (oran 1.01). Bagimsiz tam-Unicode taramasi: re.I'nin esledigi 2912 kodpoint ciftinin hepsinde `_anahtar` ayni (docstring'in 1514 iddiasini kendi kanalimdan dogruladim).

**Ret vermeyen ama olculmus 4 orta bulgu var** (asagida). Dordu de ya paketin lafzinin dogrudan sonucu (O-A3, O-A4: implementer pakete uymus, kusur pakette) ya da urun dillerinde (JP/KR/EN) erisilemeyen bir girdi sinifinda (O-A1: `ß/ẞ`, Yunan; O-A2: >= 996 kodpointlik terim). T-008 verdict-B emsali ("urunu bozmuyor -> bloke etmez") uygulandi; her biri `test_bulgu_*` ile pinlendi, duzeltilirse kirilir. Sef aksi kanaatteyse O-A1 ve O-A3 ret gerekcesine donusturulebilir -- her ikisinin komutu ve ham ciktisi asagida.

Korluk: `delivery.md`, `evidence/**`, `sef_dogrulama/**` **okunmadi**. `test_sozluk.py` yalniz **test adlari** duzeyinde, 162 testim ve 7 sondam tamamlandiktan sonra grep'lendi (`A-implementer-test-adlari.txt`); govde acilmadi. Yardimci: `tester_A/yardimci.py` (gecici JSON sozluk kurucu), `conftest.py` (depo koku `sys.path`).

## YUKSEK -- yok

## ORTA

**O-A1 · K1/2 "aday kumesi TAMDIR" ve K1/3 "JSON sirasi sonucu degistirmez" -- coklu-kodpoint casefold sinifinda ikisi de kiriliyor (olculdu, dar sinif).** `_trie_anahtari`, casefold'u >1 kodpoint ureten karakteri (`ß`->`ss`, `ẞ`->`ss`, `ᾈ`->`ἀι`) oldugu gibi birakir; `ß` ve `ẞ` re.I'de **denk** oldugu halde trie'de **ayri dala** duser. Alternation ilk dalda kisa terminalde durur ve ikinci daldaki uzun terim hic aday olmaz. Olcu (`sonda_07` §1): sozluk `{Maßen, Maẞer, Maße}` (bu sirayla) -> `lookup("Maẞer geht")` = **`[]`** (terim metinde harfiyen var); `lookup("Maßer geht")` = `[]`; ayni sozluk `Maẞer` ilk yazilinca (§1b) -> `[(0,5) Masser]`. Yunan iota-subscript (`ᾈ`~`ᾀ`) ayni: `{ᾈβγ, ᾀβδ, ᾈβ}` -> `lookup("ᾀβδ x")` = `[]`. Docstring'in kendi ornegi (`Marcus`/`marcus aurelius`, tek-kodpoint katlama) dogru calisir (§1c). Erisilebilirlik: JP/KR/EN kaynakta `ẞ` (U+1E9E) ve politonik Yunan yok -> **urunu bozmaz**. Oneri (tek satir, sef/implementer karari): `_trie_anahtari` `return k if len(k) == 1 else ch.lower()` -- `"ẞ".lower() == "ß"`, `"ᾈ".lower() == "ᾀ"`; boylece re.I denklik sinifi tek dala iner. Pin: `test_bulgu_c1_eszett_dal_ayrismasi_*[0]`, `test_bulgu_c1_yunan_iota_subscript_ayni_sinif`.

**O-A2 · K6 -- semaya uygun ama >= 996 kodpointlik `kaynak` yuklemede `RecursionError` (ValueError degil, `TranslatorError` degil).** `_trie_govdesi` en uzun terimin uzunlugu kadar ozyineler. Olcu (`sonda_04` §1): tek terim N=995 kabul, **N=996 RecursionError** (ikili arama; `sys.getrecursionlimit()==1000`); 2000 terim x 52 kodpoint kabul (derinlik, sayi degil); 300 kodpointlik JP cumle-terim kabul; 500 derinlikli yigin altinda N=400 kabul. Docstring K6 red listesi kapali bicimde yazilmis ve uzunluk siniri yok -> belgesiz cokme sinifi; gercekci sozluk teriminde (2-50 kodpoint) erisilemez. Oneri: sema `len(kaynak) <= 256` -> `ValueError` (terim adiyla) **ya da** `_trie_govdesi` yigin/iteratif; docstring'e sinir. Pin: `test_bulgu_a7_uzun_kaynak_terim_recursion_error`.

**O-A3 · K1 "sozlukteki baska terimin baslangici/bitisi sinirdir" + "komsu terimin kabul edilmesi gerekmez" -- Latin'de kelime PARCASI gomulur; docstring'in kosulsuz `windmill` negatifi sozluk icerigine bagli (paket lafzi; gercek motorla urun bozulmasi olculdu).** `sonda_05` §3: `{mill, wind}` -> `windmill` -> 2 hit (`RüzgarDeğirmen`); **`windmills` -> yalniz `wind`** (`mill` adayi sagindaki `s` yuzunden REDDEDILIR ama baslangici `wind`e sag sinir verir) -> `Rüzgarmills`; `elderly` (`elder`+`ly`) -> `İhtiyarLy`. JP karsiligi `test_c4`: `{水車, 小屋}` + `水車小屋町` -> `SuArabasi小屋町`. Gercek motor (`sonda_06`, ayri surec): `The windmills turn slowly.` **ham** "Rüzgar değirmenleri yavaş dönüyor." (dogru) -> gomulu kaynak `The Rüzgarmills turn slowly.` -> **"Rüzgarmills yavaş dönüyor."** (degirmen kayip, melez kelime sizdi; kelime 4 -> 3). Pozitif kontroller dogru (`by the mill` -> "Değirmen'in yanında", `The wind` -> "Rüzgar"). Bu Y1/G5 sinifidir (bilesik icinde parca degistirme anlam bozar) -- Latin icin. Neden ret degil: (a) paket K1 bu kurali **zorunlu kilar**, implementer uymus; (b) `wind` motorun bildigi bir kelime, K4 yazarlik kurali onu sozluge almayi zaten yasaklar; iki OZEL ADIN bir kelime icinde bitisik gelmesi gerekir. Oneri (paket duzeyi, sef karari): komsu-terim siniri yalniz **KABUL EDILEN** komsu icin (iki geciste: once dis-sinirli adaylar, sonra komsu-sinirlilar) **ya da** yalniz harf-disi betikler icin; docstring `windmill` ornegine "`wind` sozlukte degilken" kosulu. Pin: `test_bulgu_b1_windmill_*`, `test_bulgu_b1_windmills_*`.

**O-A4 · K2 "aralik disi karakter dokunulmaz" vs K6 "gom segment metnini NFC'ler" -- NFD segmentte cikti Segment kendi icinde tutarsiz (paket lafzi).** `sonda_02` §2b / `sonda_03` §1b: NFD `café noir été` (16 kodpoint) + `noir` hit -> cikti `café Kara été` **NFC (13)**: aralik DISI `café`/`été` kodpoint duzeyinde degisti; ayni cagrida hit'siz NFD komsu segment **aynen NFD** kaldi (iki segment iki normalizasyon). Daha onemlisi: `placeholders` sozlesme gereği **aynen** (NFD) kopyalanir, `text` NFC -> girdide `yt in text` **True**, ciktida **False**; NFC'lenmis hali var. T-007 K5 onarimi `kaynak.count(yt)` / K3 `parca.replace(yt, "")` bu yer tutucuyu artik **goremez**. Erisilebilirlik: OCR ciktisi pratikte NFC (KRT O3 bunu "NFD metin eslesmez [OLCULMUYOR]" diye teklif etmisti; paket v2 NFC'lemeyi zorunlu kildi). Oneri: normalizer katinda Segment (text + placeholders) tek yerde NFC; ya da gom `placeholders`i de NFC'ler ve docstring K2 "aynen" -> "NFC'lenmis" (sozlesme degisimi degil, alan degeri). Pin: `test_bulgu_a4_gom_nfd_segment_aralik_disi_kodpointler_degisir`, `test_bulgu_a4_gom_nfd_segment_placeholders_text_iliskisi_bozulur`.

## DUSUK

**D-A1 · K5 "metinle olcekli" -- segment basina hit sayisinda O(n^2).** `_ortusur(start, end, kabul)` kabul listesini her aday icin dogrusal tarar. `sonda_05` §1: hit 2x -> sure 3.2-3.9x (500 hit 2.9 ms, 2000 hit 32 ms, 4000 hit 121 ms, 8000 hit 472 ms); hit sabit (501) metin 8.5k -> 83.5k: 7.0 -> 7.6 ms (uzunluk degil, hit yogunlugu). `sonda_04` §5: onek zinciri `a2..a11` + `a*10000` -> 909 hit, 850 ms. Gercekci segment (<= 10 hit) etkisiz; 1000 segment kapisi 30-36 ms. Oneri: `kabul` sirali + `bisect`, ya da konum bitmap'i. Pin: `test_bulgu_a7_maliyet_hit_sayisinda_karesel`.

**D-A2 · K6 "tekrar eden kaynak (esleme semantigiyle)" -- red, eslemeden GENIS.** `_anahtar` casefold (ß->ss, ﬁ->fi) ile `straße`/`strasse` ve `fine`/`ﬁne` ciftlerini "tekrar" diye reddeder; eslestirici re.I bunlari **denk saymaz** (`straße` sozlukteyken `STRASSE`/`strasse` -> `[]`; `STRAẞE` -> hit). Kullanici iki yazimi da ekleyemez. Ayrica Turkce I-sinifi: `dış` ve `diş` ayni anahtar (kaynak dili Turkce olmadigi icin urun etkisi yok). `sonda_02` §1/1c; `test_bulgu_a3_*`.

**D-A3 · K1 sinir listesi -- bicim karakterleri (Cf) sessiz.** Soft hyphen U+00AD, ZWSP U+200B, WJ U+2060, ZWJ U+200D komsusu sinir DEGIL -> bitisik terim hic eslesmez (`Marcus­mill` -> `[]`, `⁠Marcus` -> `[]`). Emoji/`S*` icin docstring `[OLCULMUYOR]` der (olctum: `😀マルクス`, `Marcus$`, `Marcus+Marcus` -> `[]`); Cf icin hicbir sey demiyor. Yanlis eslesme degil, kacirma; OCR bu karakterleri nadiren uretir. `sonda_01` §5, `sonda_02` §3; `test_bulgu_a5_*`.

**D-A4 · K6 hedef yasak kumesi dar.** Hedefte `\n`/`\t`, `%s`, `<T0>`, `[Mill]` kabul (yalniz `.!?。！？{}` yasak). Gomulen `\n` T-007 bolmesine, `%s`/`[Mill]` bicimleri segment `placeholders` ile cakismaya (K5 sayimi artar) acik. `sonda_03` §2; `test_bulgu_a8_hedefte_yeni_satir_ve_yer_tutucu_benzeri_kabul`.

**D-A5 · `_` (Pc) noktalama -> sinir.** `mill_house` -> `Değirmen_house`; `millhouse` -> `[]`. Docstring `P*` der, tutarli; tanimlayici gorunumlu metinde gomme yapar (bilgi). `test_bulgu_b1_alt_cizgi_pc_noktalama_sinirdir`.

**D-A6 · Butce payi kapida 1.4x.** real_check #7 bu makinede **36.0 ms** (model yuklu, 8 is parcacigi); ayni yol modelsiz **16 ms** (`sonda_05` §2, docstring'in 15-21 ms'iyle uyumlu). Kapinin kendi kosullarinda pay dar; butce tutuyor. Bilgi.

**D-A7 · `hits` bosken `segments` denetlenmez** (`("GIZLI", 5)` aynen doner). Docstring "bos hits -> ayni nesne" der; tutarli. Bilgi. `test_bulgu_a9_segments_bozuk_hits_bos_denetimsiz_aynen`.

## Dogrulanan iddialar (secki; hepsi `A-mercek-testleri.txt`)

- K1 sinir: 18 KR + 14 JP parametreli ornek (ek solda -> yok, zincir 3 -> yok, `으로`/`로`, ekten sonra noktalama/baska terim, uc terim bitisik, ayni terim x3 bitisik, ideografik bosluk); `test_a1_*`.
- K1 siralama: esit uzunlukta ortusme (`a-b`/`b-c` in `a-b-c`) iki JSON sirasinda da kucuk start kazanir; uc terimli sozluk iki sirada ayni; `test_a2_*`.
- K1 IGNORECASE: `MARCUS/marcus/mArCuS/Marcuſ` -> `source_term` metindeki dilim, gom `Marcus`; Turkce I-sinifi 5 bicim; Kelvin isareti; sigma/Kiril; `test_a3_*`. Bagimsiz tam-Unicode tarama 2912 cift / 0 ayrisma (`sonda_05` §4).
- K6 NFC: NFD Latin/hangul jamo eslesir, indeksler NFC metne gore (NFD metinde dilim farkli -- cagiran NFC'lemeli); gom NFD `source_term`/`target_term` kabul, cikti NFC + buyuk; `test_a4_*`.
- Kodpoint: astral + bosluk -> `(2,6)`; birlestirici isaret terimin icinde (`か゚き`) eslesir, ucunda harf gibi; `test_a5_*`.
- K3: 16 yer tutucu sinir durumu; 3 elle-hit x yer tutucu -> `ContractViolation` ("yer tutucu"), bildirilmemisken kabul; `TypeError` (duz str/int/None); `test_a6_*`.
- K2/K7: 14 gecersiz hit sinifi -> `ContractViolation`, mesajlarda `GIZLI*` YOK; ortusen -> CV, bitisik serbest; bir hit gecersizse butun cagri duser; `test_a9_*`.
- K5: `capfd`+kok `caplog` DEBUG+`warnings` -> 0/0/0/0; `repr` terim basmaz; dosya silinince lookup; determinizm; girdi degismez; `bbox/speaker/placeholders/source_blocks` aynen; `test_a10_*`.
- K6 sema: 18 red sinifi (mesajda terim/alan adi, ilk hatali kayit), 12 kabul sinifi (bos sozluk, ust duzey ek anahtar, 10000 kodpoint hedef, iki emoji), BOM/UTF-16/ASCII-disi yol, bozuk JSON icerik sizdirmaz, `FileNotFoundError`/`PermissionError` sarilmaz; `test_a8_*`.
- Buyuk: 9500 kodpoint / 1500 hit 25 ms; 5000 terim 75 ms yukleme, 0.26 ms lookup; 1000 seg x 5000 terim / 11 terim = 1.01; dallanan trie (ab)^5000 6.5 ms (geri izleme yok); regex-ozel ilk karakter 8/8; `test_a7_*`, `test_c2`.

## Tester yukumlulugu / oneri (sef icin, sirali)

1. **O-A3 paket karari:** komsu-terim siniri "kabul edilen komsu" ile sinirlansin mi (iki gecis) -- ya da docstring `windmill` negatifi kosullansin ve `[OLCULMUYOR: iki sozluk terimi bir kelimede bitisik]` damgalansin. Gercek motor olcusu elde (`sonda-06-gercek-model.txt`).
2. **O-A4 paket karari:** Segment NFC'si tek yerde (normalizer) mi, gom'da `placeholders` da mi NFC'lenir. Su an cikti Segment `yt in text` degismezini bozuyor.
3. O-A1/O-A2 tek satirlik duzeltmeler; ikisi de `test_bulgu_c1_*`/`test_bulgu_a7_uzun_*` pinleriyle olculur (duzeltme pinleri kirar -> pin ters cevrilir).
4. Implementer test adlarinda gorunmeyen siniflar (ad duzeyi, 113 test): coklu-kodpoint casefold dal ayrismasi, >= 996 kodpoint terim, `wind`+`windmill`, Cf/emoji komsusu, hit-karesel olcek, 5000 terim. Mercek-A bunlari kapatiyor; `tester_A/` sefin dizinine tasinabilir.
5. D-A6: `real_check` #7 payi kapida 1.4x; bir sonraki makinede dusebilir -- butce ya 75 ms'ye ya da modelsiz olcume cekilsin (karar sefin).
