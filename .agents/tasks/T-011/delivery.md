---
task: T-011
role: implementer
round: 2
status: tamamlandi
files_written:
  - src/translate/sozluk.py
  - tests/unit/translate/test_sozluk.py
  - .agents/tasks/T-011/delivery.md
  - .agents/tasks/T-011/evidence/tdd-kirmizi-tur2.txt
  - .agents/tasks/T-011/evidence/mypy-tur2.txt
  - .agents/tasks/T-011/evidence/mypy-test-dosyasi-tur2.txt
  - .agents/tasks/T-011/evidence/pytest-tur2.txt
  - .agents/tasks/T-011/evidence/pytest-cp1254-tur2.txt
  - .agents/tasks/T-011/evidence/cov-tur2.txt
  - .agents/tasks/T-011/evidence/pytest-tum-tur2.txt
  - .agents/tasks/T-011/evidence/real_check-tur2.txt
  - .agents/tasks/T-011/evidence/mutant-kiti-tur2.py
  - .agents/tasks/T-011/evidence/mutant-ayirt-etme-tur2.txt
  - .agents/tasks/T-011/evidence/mutant-ayirt-etme-hangi-testler-tur2.txt
  - .agents/tasks/T-011/evidence/sure-olcumu-tur2.py
  - .agents/tasks/T-011/evidence/sure-olcumu-tur2.txt
  - .agents/tasks/T-011/evidence/olcum-trie-anahtari-ignorecase-denkligi-tur2.py
  - .agents/tasks/T-011/evidence/olcum-trie-anahtari-ignorecase-denkligi-tur2.txt
  - .agents/tasks/T-011/evidence/tester-testleri-tur2-kodu-uzerinde.txt
commands:
  - cmd: "python -m mypy --strict --explicit-package-bases src/translate/sozluk.py"
    exit_code: 0
    evidence: evidence/mypy-tur2.txt
  - cmd: "python -m pytest tests/unit/translate/test_sozluk.py -q -p no:cacheprovider  (453 passed; tur 1: 256)"
    exit_code: 0
    evidence: evidence/pytest-tur2.txt
  - cmd: "python .agents/tasks/T-011/real_check.py  (kapi v4, 16 kontrol: TEMIZ 16/16; #1b kazanc 4/6; #8 medyan 14 ms; tur-1 kodunda 3 IHLAL vardi)"
    exit_code: 0
    evidence: evidence/real_check-tur2.txt
  - cmd: "python -m pytest tests/unit/translate/test_sozluk.py -q -p no:cacheprovider --cov=src.translate.sozluk --cov-fail-under=95 --cov-report=term-missing  (433 ifade, %100)"
    exit_code: 0
    evidence: evidence/cov-tur2.txt
  - cmd: "python -m pytest tests -q -p no:cacheprovider  (tam takim 1897 passed, dusen yok)"
    exit_code: 0
    evidence: evidence/pytest-tum-tur2.txt
  - cmd: "python -m mypy --strict --explicit-package-bases tests/unit/translate/test_sozluk.py"
    exit_code: 0
    evidence: evidence/mypy-test-dosyasi-tur2.txt
  - cmd: "python -m pytest tests/unit/translate/test_sozluk.py -q -p no:cacheprovider  (chcp 1254, PYTHONIOENCODING YOK, sys.stdout.encoding=cp1254; 453 passed)"
    exit_code: 0
    evidence: evidence/pytest-cp1254-tur2.txt
  - cmd: "python -m pytest tests/unit/translate/test_sozluk.py -q -p no:cacheprovider --no-header -rf --tb=line  (TDD KIRMIZI: tur-2 testleri TUR-1 KODU uzerinde: 136 failed / 310 passed)"
    exit_code: 1
    evidence: evidence/tdd-kirmizi-tur2.txt
  - cmd: "python .agents/tasks/T-011/evidence/mutant-kiti-tur2.py  (ayna agaci; 47 davranis mutanti 47/47 yakalandi; 5 kontrol + M45 dogrusal-liste bilgi mutanti kacti (beklenen); M45 sure testleriyle 2 testte yakalandi)"
    exit_code: 0
    evidence: evidence/mutant-ayirt-etme-tur2.txt
  - cmd: "python .agents/tasks/T-011/evidence/sure-olcumu-tur2.py  (K5: 1000 seg x 7/50/500 terim 7-12 ms; hit yogunlugu 2x -> 2.0-2.25x (dogrusal); 8000 uyeli zincir 20-24 ms; onek zinciri a*10000 60 ms)"
    exit_code: 0
    evidence: evidence/sure-olcumu-tur2.txt
  - cmd: "python .agents/tasks/T-011/evidence/olcum-trie-anahtari-ignorecase-denkligi-tur2.py  (tum Unicode: 1514 denk ciftin 0'inda trie anahtari farkli, ters yonde 0; pozitif kontroller: tur-1 anahtari 34, lower() temsilcisi 6 cift ayristi)"
    exit_code: 0
    evidence: evidence/olcum-trie-anahtari-ignorecase-denkligi-tur2.txt
  - cmd: "python -m pytest .agents/tasks/T-011/tester_A .agents/tasks/T-011/tester_B -q -p no:cacheprovider --import-mode=importlib -rfEx --tb=line  (tester testleri tur-2 kodunda: 45 failed / 208 passed / 1 xfail; siniflandirma asagida)"
    exit_code: 1
    evidence: evidence/tester-testleri-tur2-kodu-uzerinde.txt
contract_change_request: false
known_gaps:
  - "[KAPI] real_check v4 bu turda TEMIZ 16/16; kapi itirazi YOK. Tur-1 itirazlari (#3c placeholders, #6a kod noktasi) v4'te kapanmis (kapi `yer_tutucular` parametresi ve `TEK_HECE` sabiti ile)."
  - "[PAKET ILE OLCUM CELISKISI 1 -- K1 v3 `マルクス山 -> eslesmez`] Paketin betik gecisi kurali Katakana|Han'i sinir sayar (`マルクス様` ornegi ayni cifttir); ayni paragraf `マルクス山`i saygi listesinin negatif kontrolu olarak 'eslesmez' yazar. Iki kural birlikte tutamaz. Kapi #6b'nin arkasindaki betik kurali izlendi: `マルクス山` -> 1 hit (`Marcus山`, 'Marcus Dagi' = ad + kanji siniflandirici; `ゴブリン王`/`エルフ族` sinifi, istenen davranis). Saygi listesinin gercek negatif kontrolu AYNI betikli orneklerle yazildi: `長老山`, `長老様子` (Han+Han), `ひかりこ`, `ひかりさんご`, `ひかりかわ` (Hiragana+Hiragana) -> 0; `ひかりやま` negatif OLAMAZ (`や` parcaciktir). Test: `test_k1_betik_gecisi_マルクス山_eslesir_paket_celiskisi`, `test_k1_jp_saygi_listesi_negatif_kontrol`."
  - "[PAKET ILE OLCUM CELISKISI 2 -- K1 v3 `마르쿠스들이다 (3 ek) -> eslesmez`] `이다` (kopula) listede TEK ektir; `들`+`이다` = 2 ek <= zincir siniri -> eslesir (dilbilgisel: 'onlar Marcus'lardir'). Paket 3 saymis. Zincir <= 2 kurali (v3'te degismedi) korundu; gercek uc-ek negatifleri `마르쿠스들에게는`, `마르쿠스님에게는`, `마르쿠스들한테도` -> 0 (`test_k1_kr_ek_zinciri_uc_ek_eslesmez_bilinen_sinir`). BILINEN SINIR (sef karari): saygi + yonelme + konu (`장로님에게는`) gercek Korece'de yaygindir ve zincir 2 ile KACAR; derinlik 3 onerilir, paket disi oldugu icin uygulanmadi."
  - "[PAKETIN BIR ADIM OTESI -- K1 v3 JP saygi ekleri] Paket JP saygi ekleri icin yalniz 'sagda' der; KR ek disiplini (en uzun once, EKTEN SONRA da gercek sinir, zincir <= 2) JP eklerine de uygulandi (tek mekanizma `_ek_sonrasi`, `_EKLER` birlesik liste). Sonuc: `長老様子` (様+子), `ひかりさんご`, `ひかりかわ` eslesmez; `ひかりさんたち`, `ひかりだから` eslesir; `ひかりだからね` (3 ek) eslesmez (belgeli). Katakana/Han terimler icin hiragana ekleri betik gecisi zaten kapsar; liste yalniz ayni betikli ciftlerde yuk tasir -- her ek icin bu ciftte de ayri test var (`test_k1_her_jp_saygi_eki_ayni_betikte_listeden_gelir`), mutant M35 (liste bos) 16 testle yakalandi."
  - "[K1 v3 -- BETIK SINIFLANDIRMASI, kenarlar] Siniflar kodpoint aralik tablosuyla (`_BETIK_ARALIKLARI`, bisect). Kararlar: `ー` (uzatma), fonetik uzanti ve yarim genislik Katakana; `々〆〇`, radikaller, uyumluluk ve uzanti bloklari Han; Jamo/uyumluluk/yarim genislik Hangul; Hiragana blogundaki birlestirici ses isaretleri Hiragana. SAGDAKI komsu birlestirici isaretse (`M*`) sinir DEGIL (terimin son karakterine aittir; `マルクス`+U+0335, +U+309A -> 0). Sembol (`S*`) DIGER sinifindadir: `マルクス♪` betik gecisiyle sinir (1 hit), `Marcus♪`/`Marcus$` degil (0) -- asimetri belgeli ve pinli (`test_k1_betik_gecisi_sembol_komsusu_asimetrik_belgeli`); Tester-B D-B1 CJK tarafinda kapandi, Latin tarafinda `[ÖLÇÜLMÜYOR]`. Kana Supplement / Small Kana Extension (astral) DIGER sayilir `[ÖLÇÜLMÜYOR]`."
  - "[K1 v3 -- ZINCIR, uygulama siniri] Ek (KR/JP) sonrasinda gelen komsu ADAY sinir sayilmaz: `방앗간을마르쿠스` (bosluksuz) -> 0 hit (tur 1: `방앗간`). Gercek KR/JP metinde ek ile sonraki kelime arasinda bosluk/noktalama vardir; `[ÖLÇÜLMÜYOR]`, belgeli. Tester-A `test_a1_kr_ek_simetrisi_ve_zinciri[방앗간을마르쿠스]` bu tur-1 davranisini pinliyor (asagida sinif e)."
  - "[K1 v3 -- ZINCIR, maliyet] Zincir aramasi iki yon ES ZAMANLI adim adim (yigin, ozyineleme yok), olu konumlar kalici hafizada (doluluk yalniz artar, oluluk kararli -- gerekce docstring). Olculdu: 8000 uyeli gecerli/olu zincir 20-24 ms; ilk surumde tek yonlu arama `Marcus*8000+x` icin karesel cikmisti (300 ms @1000 uye), es zamanli adimlama ile dogrusal. Onek zinciri `a2..a11` + `a*10000` (Tester-A sonda 4): 910 hit 60 ms (tur 1: 850 ms), `+b` (0 hit) 150 ms -- maliyet 100k adayin uretimi/siralanmasi. Kapsam izleyicisi altinda zincir yolu ~5x yavaslar (115 ms / 240 ms butce, `_izleyici_payi` 4x korundu); tek koşumda tracer altinda bir kez esik asimi gozlendi ve DFS geri sarmasi tek adimda toplanarak pay artirildi."
  - "[K2 v3 -- NFC] Hit'li segmentte `text` VE `placeholders` NFC; tuple uzunlugu/sirasi/bos ogeleri korunur (`test_k2_placeholders_tuple_ve_eleman_sayisi_korunur`). Hit'siz NFD segment aynen (`is`). Segment kaynakli bicim hatalari (`placeholders` duz str / dizi degil / str olmayan oge) `lookup_segments` ve `terimleri_gom`da `ContractViolation`; dogrudan `lookup(text, '{0}')` `TypeError` (programci hatasi). `hits` bosken segmentler denetlenmez (D-A7, tur 1 ile ayni, belgeli)."
  - "[K6 v3 -- SEMA] Kaynakta `.!?。！？` HERHANGI bir yerde red (`Mr. Marcus` dahil; OCR'dan yapisik nokta sinifi). Hedefte `Cc` red (LF/TAB/CR/NUL/DEL/NEL ayri test); `Cf` (ZWJ) ve `Zs` kabul (pozitif kontrol). Kaynak > 100 kodpoint red (100 kabul + eslesir, 101 red, 2000 `ValueError`; `RecursionError` yolu kapandi, trie govdesi ozyinelemesi <= 101). Hedefte `%s`/`[Mill]` gibi yer tutucu BENZERI dizeler serbest `[ÖLÇÜLMÜYOR]` (cagiran `placeholders` ile bildirir). D-A2 (`straße`/`strasse` tekrar reddi eslemeden genis) `[ÖLÇÜLMÜYOR]` urun dillerinde. Kaynakta kontrol karakteri denetlenmez (paket istemedi) `[ÖLÇÜLMÜYOR]`."
  - "[K1 v3 -- TRIE ANAHTARI, olcumle secildi] Ilk aday `ch.lower()` temsilcisi (Tester-A onerisi) tum Unicode taramasinda 3 IGNORECASE ciftini kacirdi (`U+0390~U+1FD3`, `U+03B0~U+1FE3`, `U+FB05~U+FB06`: ikisi de kucuk harf, `_EXTRA_CASES` ile denk). Secilen: dugum anahtari = kanonik `_anahtar` (casefold + Turkce I sinifi; coklu kodpoint olabilir), regex literali = dalin ILK gorulen uyesi. Iki yonde 0 ayrisma (1514 denk cift; 1427 cok uyeli dal); pozitif kontroller tur-1 anahtari 34, lower() 6 cift. Yunan ciftlerini K6 NFC zaten tekillestirir; yuk tasiyan birim testi `ﬅ/ﬆ` (mutant M24c 1 testle yakalandi)."
  - "[K4 v3 -- KIMLIK CIPASI] `Marcus -> Marcus` gecerli, hit uretir, gom ciktisi metin-esit; docstring 'sinir cipasi' adiyla belgeler ve v3'te betik gecisi cipayi gereksiz kilar (`長老Marcus` -> `長老` yalniz `長老` sozlukteyken de eslesir; `test_k4_kimlik_cipasi_gerekmez_betik_gecisi_yeter`). Cagiran sayaci `source_term != target_term` ile suzer. Unvan gri bolgesi (Y-B1) docstring YAZARLIK KURALI'nda iki yonlu olcumle ozetlendi; idempotens yokluguna (`hedef ⊇ kaynak`) docstring basinda uyari."
  - "[TESTER TESTLERI -- tur-2 kodunda 45 dusen, 5 sinif; duzeltme onlarin isi] (a) tur-1 bulgusunu pinleyen, bulgu duzeltilince kirilan testler: 18 (A: bulgu_a4, bulgu_a7 x2, bulgu_a8, bulgu_b1_windmills, bulgu_c1 x2, c4; B: b3_kaynak_terminator, b6_reddedilen_komsu x4, b6_nfd_yer_tutucu, b7_jp_saygi, b7_kr_ek, b8_typeerror x2). (b) v3 BETIK GECISI sonucu eski davranisi pinleyen testler: 20 (A: a1_jp_parcacik_ve_komsu_terim x4 -- `村マルクス`/`マルクス村` artik Han|Katakana sinir; bulgu_a5 emoji/sembol -- CJK|DIGER sinir; B: b6_kimlik_terim_sinir_cipasi -- cipa gerekmez; b7_sembol x14 -- fixture cumlelerinde CJK terim + sembol artik sinir, hit dusmez). (c) fixture v3 (unvan ve `mill` cikti) sonucu: 4 (B: b1_list_tuple_generator `İhtiyarMarcus` bekler, b6_hit_indeksleri `mill` bekler, bx_repr `terim_sayisi=11`, bk_real_check_kapi_yolu 10 hit). (d) K6 v3 kaynak terminatoru test verisini reddeder: 2 (A: c2_regex_ozel `.x` terimi; B: b9_hedef_kaynagi_iceren `マルクス。` kaydi). (e) tur-1 mekanizma pin'i, v3 zincir kurali sonucu: 1 (A: a1_kr_ek_simetrisi `방앗간을마르쿠스` -> ek sonrasi komsu aday sinir degil). B'nin `검은 옷` xfail'i degismedi (bilinen sinir, xfail kaliyor)."
  - "[MUTANT M45 -- bisect/bitmap yerine dogrusal] Tur-1 `_ortusur` mekanizmasi (kabul listesi dogrusal tarama) davranisi degistirmez: sure testleri HARIC kosumda 0 test dustu (beklenen, bilgi). Sure testleri DAHIL kosumda 2 test yakaladi (`test_k5_sure_8000_hit_tek_segment_60ms_alti`, `test_k5_sure_8000_uyeli_zincir_60ms_alti`); `gom` sure testi yakalamadi (gom bitmap'i ayri). Yani K5 hit-yogunlugu degismezi yalniz sure testiyle olculuyor; sure testleri kapida (duz pytest) kosar."
  - "[CALISMA KOPYASI] `git add`/`commit` ATILMADI. Tur-1 delil dosyalari (`evidence/*` `-tur2` eki olmayanlar) yerinde birakildi; tur-2 delilleri `*-tur2.*` ekiyle. Mutlak yol yok (delillerde `<yol>`/`<gecici dizin>`)."
---

# T-011 tur 2 -- teslim ozeti

Paket v3'un ▲ maddeleri uygulandi: K1 zincir kurali + betik gecisi + JP saygi / KR ek listeleri + trie-IGNORECASE denkligi; K2 `placeholders` NFC + Segment kaynakli `ContractViolation`; K5 bitmap + es zamanli zincir aramasi (ozyineleme yok); K6 kaynak terminatoru + hedef `Cc` + kaynak <= 100. Kapi v4 (tur-1 kodunda 3 IHLAL) tur-2 kodunda **TEMIZ 16/16**. 453 birim testi (tur 1: 256), kapsam %100, tam takim 1897, mutant 47/47.

## Tur 1 (ozet)

`GlossaryStore(json_path)` (`lookup`, `lookup_segments`, `terimler`, `len`) ve `terimleri_gom(segments, hits)`; ileri-bakisli TRIE deseni (IGNORECASE, orijinal/NFC metin), onek tablosu, `(uzunluk azalan, start artan)` isleme, sinir kurali (metin ucu / bosluk / `P*` / JP parcacik / KR ek zinciri <= 2 / komsu terim / yer tutucu ucu), K2 start-azalan gomme + `ContractViolation` denetimleri, K4 `ilk_harfi_buyut` (`i` -> `İ`), K6 sema (27 red sinifi), K7. 256 test, kapsam %100, tam takim 1700, 32/32 mutant, kapi v3 10/12 (2 kapi hatasi itirazi: #3c placeholders, #6a kod noktasi -- v4'te kapandi). Iki tester onay verdi; bulgularin tamami paket hatasi cikti (komsu aday sinir veriyor -> `Rüzgarmills`; JP saygi / KR yonelme ekleri 0 hit; kaynak terminatoru; NFD yer tutucu; `TypeError` sinifi; `ß/ẞ` dal ayrismasi; >= 996 kodpoint `RecursionError`; hit sayisinda O(n²)). Tur-1 delilleri `evidence/` altinda (`-tur2` eki olmayanlar).

## Tur 2 -- ▲ maddeleri nasil karsilandi

| ▲ | uygulama | olcu |
|---|---|---|
| K1 zincir kurali | Aday isleme sirasinda (uzunluk azalan) iki ucu gercek sinir olan aday dogrudan kabul; degilse sol ve sag zincir ES ZAMANLI adim adim aranir (`_ZincirDfs`, yigin, ozyineleme yok): bitisik unoccupied adaylar uzerinden gercek sinira (ya da kabul edilmis komsunun ucuna) ulasan yol; bir yon olu cikar cikmaz durur; olu konumlar kalici; bulunan zincirin tum uyeleri birlikte kabul (konum bitmap'i). Reddedilen aday hicbir komsuya sinir vermez. Zincir icinde de en uzun aday oncelikli | `windmills` 0 / `millstones` 0 / `windmill` 2 / `長老マルクスアイラ` 3 / `マルクスアイラ` 2; `水車小屋町` 0; `oldmillhouse` -> old+millhouse; isleme sirasindan bagimsiz (2 sira); yer tutucu uyesi olamaz, orta uye kirilir; geri izleme (`abcabcz`); kok esit uzunlukta en uzun once (`xxxxabcd`); kabul edilmis komsu ucu (`ひかりはな`, `(mill)stonesx`); 3000/8000 uyeli gecerli + olu zincirler, `RecursionError` yok |
| K1 betik gecisi | `_betik` (bisect, 15 aralik: Han / Hiragana / Katakana / Hangul / DIGER); terim ucu ile komsusu farkli sinifta -> gercek sinir; sagdaki `M*` komsu sinir degil; `S*` DIGER | paketin 7 pozitif + 9 negatif ornegi ayri kimlikle; 5x5 sinif matrisi x 2 taraf (50 test); kenar karakterleri (`ー`, yarim genislik, jamo, `々`, `・`, U+0335, U+309A); sembol asimetrisi; `マルクス山` (paket celiskisi, pinli) |
| K1 JP saygi / KR ek | `_JP_SAYGI_EKLERI` (15) + `_KR_EKLER_G6` (18) + `_KR_EKLER_V3` (19) -> `_EKLER` (en uzun once) + ilk-karakter tablosu (`_EK_ILK_KARAKTER`); sagda, ekten sonra gercek sinir, zincir <= 2 | JP: her ek `マルクス`+ek (betik) VE ayni betikli cift (`長老様`, `ひかりさん`; liste yuk tasir) ayri kimlikle; negatif kontrol 5; `マルクスさんが`; ek zinciri 2/3. KR: her yeni ek ayri; `에게` listeden; `장로님이`, `장로님께서`; `마르쿠스들이다` (2 ek, paket celiskisi); uc ek negatif x3; bilesik negatif x5 (`아침`, `들판`, `씨앗`, `야채`, `님프`) |
| K1 trie-IGNORECASE | dugum anahtari = `_anahtar` (kanonik), literal = ilk gorulen uye; `lower()` adayi olcumle reddedildi | `{Maßen, Maẞer, Maße}` iki JSON sirasi; Yunan iota subscript; ikisi de kucuk harf `_EXTRA_CASES` ciftleri x3; tum Unicode iki yonlu tarama (delil) |
| K2 NFC + CV | `dataclasses.replace(seg, text=nfc, placeholders=nfc_tuple)`; `_segment_yer_tutuculari` `TypeError` -> `ContractViolation` (`lookup_segments` + `terimleri_gom`) | NFD segment + NFD yer tutucu -> cikti NFC, alt dize, sayim 1; hit'siz NFD `is`; tuple/bos oge korunur; 4 bicim hatasi x 2 cagri CV; dogrudan `lookup` TypeError kalir |
| K4 kimlik cipasi | docstring adlandirdi; betik gecisiyle cipa gereksiz | `Marcus->Marcus` hit + metin-esit cikti + suzme; `長老Marcus` `Marcus` sozlukte yokken |
| K5 hit yogunlugu | bitmap (`bytearray.find`) kabul/korunan; olu-konum hafizasi; DFS sicak yolu (iki uc gercek sinirsa arama yok); ek listesi ilk-karakter tablosu | 8000 hit tek segment (bosluklu) < 60 ms; 8000 uyeli gecerli + olu zincir < 60 ms; 8000 hit gom < 60 ms; sure olcumu: 2x hit -> 2.0-2.25x |
| K6 sema | kaynak terminator (her yer), hedef `Cc`, kaynak <= 100 | 6 terminator x (JP + Latin kaynak), `Mr. Marcus`; 6 `Cc` ayri; `Cf`/`Zs` kabul; 100 kabul + eslesir, 101 red, 2000 `ValueError` |
| Docstring | paket v3; yazarlik kurali (Y-B1 iki yonlu), kimlik cipasi, idempotens yok, betik/zincir/ek kurallari, bilinen sinirlar ve `[ÖLÇÜLMÜYOR]` damgalari | `test_k1_kaynakta_kelime_siniri_metakarakteri_yok`, `test_k6_read_bytes_kullanilir_ast` docstring dahil kaynagi tarar |

## Paket ile olcum celiskileri (ozet; ayrinti `known_gaps`)

1. `マルクス山`: betik gecisi kurali (Katakana|Han sinir) ile 'eslesmez' negatif kontrolu birlikte tutamaz; kural izlendi (1 hit), saygi listesinin negatif kontrolu ayni betikli orneklere tasindi.
2. `마르쿠스들이다`: `들`+`이다` 2 ektir, 3 degil; zincir <= 2 ile eslesir; gercek 3-ek negatifleri yazildi; `님에게는` sinifi bilinen sinir (derinlik 3 sef karari).

## Tester testleri (tur-2 kodunda, `evidence/tester-testleri-tur2-kodu-uzerinde.txt`)

45 dusen / 208 gecen / 1 xfail. Sinif dagilimi: (a) duzeltilen bulgu pin'i **18** · (b) v3 betik gecisi sonucu eski davranis pin'i **20** (A a1_jp x4, bulgu_a5; B b6_kimlik_cipasi, b7_sembol x14) · (c) fixture v3 **4** · (d) K6 kaynak terminatoru test verisi **2** (`.x`, `マルクス。`) · (e) tur-1 mekanizma pin'i, zincir kurali sonucu **1** (`방앗간을마르쿠스`). Hicbiri K1-K7 v3 ihlali degil; duzeltme tester'larin.

## Mutant ayirt etme (`evidence/mutant-ayirt-etme-tur2.txt`, test adlari `-hangi-testler-tur2.txt`)

Tur-1 32 mutant (ikame noktalari v3 koduna tasindi, M32 bitmap surumu) + tur-2 15 (M24b/M24c trie anahtari, M33 zincir kaldirildi, M34 betik gecisi kaldirildi, M35 JP listesi bos, M36 KR yeni ekler bos, M37 placeholders NFC yok, M38 kaynak terminator, M39 hedef Cc, M40 kaynak <= 100, M41 CV sarmasi yok, M42 Mn sinir sayilir, M43 kabul komsusu sinir degil, M44 zincirde kisa once, M45s dogrusal liste + sure testleri): **47/47 yakalandi**; 5 kontrol (C-1..C-5) + M45 (dogrusal, sure testleri haric) kacti (beklenen). En dar ayirt etme 1 testle: M08, M18, M19, M24c, M29, M30, M37, M44 -- her biri o mutant icin adlandirilmis test.

## Sayilar

| olcu | sonuc |
|---|---|
| birim | 453 passed (tur 1: 256); kapsam %100 (433 ifade); mypy --strict modul + test temiz |
| TDD kirmizi | tur-2 testleri tur-1 kodunda 136 failed / 310 passed |
| tam takim | 1897 passed, dusen yok |
| real_check v4 (sef) | TEMIZ 16/16; #1a 6/6, #1b kazanc 4/6, #5a 1/1, #6a 0/2/2, #6b 1/0, #8 medyan 13.7 ms |
| sure (izleyicisiz) | 1000 seg x 7/50/500 terim: lookup_segments+gom 7-12 ms, kapi yolu 9-15 ms; 8000 hit 21 ms; 8000 uyeli zincir 20-24 ms |
| mutant | 47/47 yakalandi; 5 kontrol + 1 bilgi kacti |
| tester testleri | 45 dusen (18 duzeltilen pin, 20 betik gecisi, 4 fixture v3, 2 K6 test verisi, 1 zincir pin'i) |
| cp1254 | 453 passed, `PYTHONIOENCODING` yok |
