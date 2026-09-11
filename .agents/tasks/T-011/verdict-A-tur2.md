---
task: T-011
role: tester
round: 2
decision: onay
checks:
  - name: "taban 1 -- mypy --strict temiz (sozluk.py)"
    cmd: "python -m mypy --strict --explicit-package-bases src/translate/sozluk.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r2-taban-1-mypy.txt
  - name: "taban 1b -- mypy --strict temiz (implementer test dosyasi; govde acilmadi)"
    cmd: "python -m mypy --strict --explicit-package-bases tests/unit/translate/test_sozluk.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r2-taban-1b-mypy-test-dosyasi.txt
  - name: "taban 2 -- implementer birim testleri 453 passed"
    cmd: "python -m pytest tests/unit/translate/test_sozluk.py -q -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r2-taban-2-pytest.txt
  - name: "taban 3 -- real_check v4 TEMIZ 18/18 (gercek motor; #1b kazanc 4/6, #4a Elder sizmasi rapor, #5c pozitif kontrol, #6a windmills=0, #8 medyan 18.0 ms < 50)"
    cmd: "python .agents/tasks/T-011/real_check.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r2-taban-3-real_check.txt
  - name: "taban 4 -- kapsam %100 (433 ifade, 0 eksik)"
    cmd: "python -m pytest tests/unit/translate/test_sozluk.py -q -p no:cacheprovider --cov=src.translate.sozluk --cov-fail-under=95 --cov-report=term-missing"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r2-taban-4-kapsam.txt
  - name: "taban 5 -- tam takim 1897 passed"
    cmd: "python -m pytest tests -q -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r2-taban-5-tum-takim.txt
  - name: "tur-1 mercek testleri v3 kodunda HAM: 15 failed / 147 passed (dusenler siniflandirildi ve yeniden nisanlandi; asagida)"
    cmd: "python -m pytest .agents/tasks/T-011/tester_A/test_mercek_a.py -q -p no:cacheprovider --import-mode=importlib -rfE --no-header"
    exit_code: 1
    result: gecti
    evidence: tester_A_evidence/r2-tur1-testleri-v3-kodunda-ham.txt
  - name: "A tur 2 -- mercek-A 416 passed = 162 tur-1 (15'i yeniden nisanli) + 254 yeni (zincir, betik, ek, trie, K2 NFC, K6, K5, fuzz, thread)"
    cmd: "python -m pytest .agents/tasks/T-011/tester_A -p no:cacheprovider --import-mode=importlib -v -rfE --no-header"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r2-A-mercek-testleri.txt
  - name: "A -- implementer + mercek-A ayni oturumda 869 passed (etkilesim yok)"
    cmd: "python -m pytest tests/unit/translate/test_sozluk.py .agents/tasks/T-011/tester_A -q -p no:cacheprovider --import-mode=importlib -rfE --no-header"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r2-A-birlikte-kosum.txt
  - name: "sonda r2-01 -- betik sinifi tablosu KAMU API ile: 71 karakter (uzatma/kucuk kana/yarim genislik/Jamo/hanja/kanji sayisi/tam genislik Latin/rakam/birlestirici/々〆〇ヶ/astral kana/Cf) docstring ile uyumsuz 0; yarim genislik metin tam genislik terimi bulmaz (NFC != NFKC); Kelvin isareti NFC -> K"
    cmd: "python .agents/tasks/T-011/tester_A/sonda_r2_01_betik_tablosu.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r2-sonda-01-betik-tablosu.txt
  - name: "sonda r2-02 -- trie/IGNORECASE tam Unicode, bagimsiz kanal: re.I denk 1495 tek-kodpoint cift x 2 sira x 6 metin -> 0 ayrisan; ters yon (ayni dal, re.I denk degil) 0"
    cmd: "python .agents/tasks/T-011/tester_A/sonda_r2_02_trie_ignorecase.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r2-sonda-02-trie-ignorecase.txt
  - name: "sonda r2-03 -- GERCEK MOTOR (ayri surec): ek listesi disi ekler -- JP hiragana ad + くん/さま 0 hit ve hamda ad KAYIP (2 kacak, Y-B2 sinifi); KR 다/예요/한테서/에게서 0 hit ama ham zaten adi koruyor; pozitif kontrol 5/5"
    cmd: "python .agents/tasks/T-011/tester_A/sonda_r2_03_gercek_model.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r2-sonda-03-gercek-model.txt
  - name: "sonda r2-03 stdout (ASCII)"
    cmd: "python .agents/tasks/T-011/tester_A/sonda_r2_03_gercek_model.py > r2-sonda-03-gercek-model-stdout.txt"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r2-sonda-03-gercek-model-stdout.txt
  - name: "sonda r2-04 -- K5 izleyicisiz: hit 2x -> sure 1.95-2.15x (DOGRUSAL; tur 1 3.2-3.9x), 8000 hit 18.7-19.4 ms, 8000 uyeli zincir canli 23-25 / olu 21-26 ms (< 60), a*10000 onek zinciri 910 hit 53 ms (tur 1: 850 ms), 1000 seg x fixture 11 ms (yuk altinda 26; karisik 3 dil 4000 hit 18 / yukte 42 ms < 50)"
    cmd: "python .agents/tasks/T-011/tester_A/sonda_r2_04_sure.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r2-sonda-04-sure.txt
  - name: "sonda r2-05 -- zincir degismezleri, bagimsiz sinir tanimi: 40000 rastgele metin 0 ihlal (sirali/ortusmesiz, kosu dis uclari gercek sinir, sinirli aday atlanmaz, kabul edilmis komsu ucu sinir, JSON sirasi); pozitif: 2231 zincir kosusu kabul, 6920 aday red, 2781 olu zincir; yer tutuculu 4500 metin 0 ihlal, 526'sinda yt sonucu degistirdi"
    cmd: "python .agents/tasks/T-011/tester_A/sonda_r2_05_zincir_fuzz.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r2-sonda-05-zincir-fuzz.txt
  - name: "depo dokunulmadi: git status --short -- src tests real_check packet fixtures BOS; git diff HEAD -- src tests 0; sha256 (sozluk.py 8a0dd7c4..., test_sozluk.py 42172d49..., real_check eaf46b8e..., fixture 39e9bc04...); HEAD 9c8d85f"
    cmd: "git status --short -- src tests .agents/tasks/T-011/real_check.py .agents/tasks/T-011/packet.md .agents/tasks/T-011/fixtures; git diff HEAD --stat -- src tests; sha256sum ..."
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r2-A-git-status-depo-dokunulmadi.txt
  - name: "korluk kaydi: implementer test ADLARI (164 fonksiyon) yalniz kapsam boslugu icin, 416 mercek testi ve 5 sonda bittikten SONRA grep'lendi; govde acilmadi; delivery.md / evidence/ / sef_dogrulama/ okunmadi"
    cmd: "grep -n '^def test_' tests/unit/translate/test_sozluk.py | sed 's/(.*//'"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r2-A-implementer-test-adlari.txt
blocking_issues: []
---

# T-011 tur 2 -- Tester-A (mercek: garanti alani + sinir)

Karar: **ONAY**. Bes taban komutu + implementer test dosyasi mypy bu makinede temiz (mypy 0/0, 453 passed, real_check v4 TEMIZ 18/18 ve #8 18.0 ms, kapsam %100 / 433 ifade, tam takim 1897). Docstring v3'un K1-K7 iddialari kabul edilen girdilerin **olctugum tamaminda** tutuyor: 416 mercek testi (162 tur-1 + 254 yeni) + 5 sonda + 40.000 metinlik bagimsiz zincir fuzz'i (0 ihlal) + tam Unicode trie taramasi (1495 cift, 0 ayrisan) + 71 karakterlik betik tablosu (0 uyumsuz). **Paket/docstring v3 iddiasinin olculmus ihlali yok** -> ret kosulu olusmadi.

Tur-1 bulgularimin altisi da v3'te **kapandi** ve pinleri tersine cevrildi: O-A1 (trie dali: `Maẞer` iki sirada da bulunur; 1495 re.I cifti 0 ayrisan), O-A2 (100 kabul / 101 red / 2000 `ValueError`; ozyineleme limiti 300'de 100 kodpointlik terim yuklenir), O-A3 (`windmills`/`millstones`/`水車小屋町` 0 hit, metin dokunulmaz; gercek motorda kapi #6a), O-A4 (`placeholders` NFC, `yt in text` korunur), D-A1 (hit 2x -> sure 1.95-2.15x; 8000 hit 18.7 ms, tur 1 472 ms), D-A4 (`\n \t \r` NUL DEL NEL red). D-A2/D-A3/D-A5/D-A7 belgeli `[ÖLÇÜLMÜYOR]`/bilgi olarak kaldi.

**Bir ORTA bulgu var** (paket ek listesi eksigi, gercek motorla olculdu, docstring ihlali degil): hiragana yazimli ad + hiragana saygi eki `くん`/`さま` (liste yalniz kanji `君`/`様`) -> 0 hit, ham ceviride ad kayboluyor. Asagida.

Korluk: `delivery.md`, `evidence/**`, `sef_dogrulama/**` **okunmadi**. `test_sozluk.py` yalniz **test adlari** duzeyinde, 416 testim ve 5 sondam bittikten sonra grep'lendi (`r2-A-implementer-test-adlari.txt`; ad duzeyinde gorunmeyen siniflar: fuzz/diferansiyel, thread, yarim genislik kana, hentaigana, `くん`/`さま`, KR kopula `다`, U+2028). Yardimci: `tester_A/yardimci.py` (degismedi), `conftest.py`.

## Tur-1 testlerinin v3'te yeniden nisanlanmasi (`test_mercek_a.py`, 162 test; ham kosum 15 failed / 147 passed)

| Sinif | Adet | Testler (eski davranis yorum satirinda; `_v3` eki) |
|---|---|---|
| (a) duzeltilen bulgu pini -> v3 beklentisi | **8** | `test_bulgu_a4_gom_nfd_segment_placeholders_text_iliskisi_bozulur_v3` (O-A4), `test_bulgu_a7_uzun_kaynak_terim_recursion_error_v3` (O-A2), `test_bulgu_a7_maliyet_hit_sayisinda_karesel_v3` (D-A1: oran > 6 -> < 6), `test_bulgu_a8_hedefte_yeni_satir_ve_yer_tutucu_benzeri_kabul_v3` (D-A4: `\n`/`\t` red, `%s`/`<T0>`/`[Mill]` serbest), `test_bulgu_b1_windmills_..._v3` (O-A3: `Rüzgarmills` -> 0 hit), `test_bulgu_c1_eszett_..._v3[0]` (O-A1), `test_bulgu_c1_yunan_iota_subscript_ayni_sinif_v3` (O-A1), `test_c4_jp_komsu_terim_..._v3` (O-A3 JP: `SuArabasi小屋町` -> 0 hit) |
| (b) v3 kuraliyla degisen eski davranis pini | **6** | betik gecisi 5: `村マルクス`/`マルクス村` (0 -> hit), `長老マルクス村` ([(0,2)] -> iki hit), `村長老マルクス` (ayni sonuc farkli gerekce), `村長老マルクス村` ([] -> `マルクス`); `test_bulgu_a5_emoji_ve_sembol_komsusu_sinir_degil_v3` (`😀マルクス` DIGER\|Katakana hit; `Marcus$` 0 kaldi). Ek+bitisik terim 1: `방앗간을마르쿠스` ([(0,3)] -> [], docstring "ekten sonraki komsu aday `[ÖLÇÜLMÜYOR]`") |
| (c) fixture v3 | **0** | dosya fixture kullanmiyor |
| (d) K6 kaynak terminatoru verisi | **1** | `test_c2_regex_ozel_ilk_karakterli_terimler_kacmaz`: `.x` -> `*x` |

## YUKSEK -- yok

## ORTA

**O-A5 (tur 2) · K1 v3 JP saygi listesi hiragana yazimli ekleri kapsamiyor (`くん`, `さま`) -- ayni betikli (Hiragana+Hiragana) adda ek listesi tek dayanak, betik gecisi kurtarmiyor; gercek motorda ad kayip.** Liste `君`/`様` kanji; oyun metninde `くん`/`さま` hiragana yazimi yaygin, hiragana adlar (`ひかり`, `ゆうき`) da. `r2-sonda-03` (ayri surec, gercici sozluk `ひかり->Hikari`): `ひかりくんが来た。` ve `ひかりさまが来た。` -> **0 hit**, ham ceviri "Bir ışık geldi." (ad cevrildi), gomulu ayni. Pozitif kontroller: `ひかりさんが来た。` -> 1 hit, gomulu "Hikari geldi."; `マルクスくんが来た。` -> betik gecisiyle 1 hit, ham "Marks geldi." -> gomulu "Marcus geldi." (5/5). Y-B2 ile ayni sinif (Tester-B'nin tur-1 bulgusu `さん`/`様`); v3 listesi kanji-agirlikli kaldi. Docstring listeyi aynen yaziyor -> **ihlal degil, paket eksigi**. Oneri (tek satir, sef karari): `_JP_SAYGI_EKLERI`ne `くん さま` (+ `せんぱい せんせい どの` degerlendirilsin); K1 ▲ olcusune `ひかりくん`/`ひかりさま` pozitif. Pin: `test_bulgu_e_jp_hiragana_saygi_ekleri_kun_sama_listede_yok`.

## DUSUK

**D-A8 · KR ek listesi: unlu sonrasi kopula `다` (`마르쿠스다` -- `이다`nin dogal bicimi), kibar kopula `예요`/`이에요`, cikma `한테서`/`에게서` yok -> 0 hit.** `r2-sonda-03`: dort cumlede de ham ceviri adi zaten koruyor ("O Marcus.", "Ben Marcus.", "Marcus'tan bir mektup aldım.") -> bu cumlelerde urun etkisi yok; pozitif: `입니다`/`이다`/`에게` 1 hit (`에게` hamda "Markos'a" -> gomulu "Marcus'a"). Pin: `test_bulgu_e_kr_kopula_da_yeyo_ve_cikma_hanteseo_listede_yok`. Uc-ek siniri (`장로님에게는`, `마르쿠스들에게는`) docstring'de belgeli, olculdu ve pinlendi (`test_e_kr_uc_ek_kacar_belgeli`).

**D-A9 · K6 hedef yasak kumesi `Cc` ile sinirli: U+2028/U+2029 (Zl/Zp; `str.splitlines` satir sonu sayar) ve Cf (ZWSP, SHY, BOM) hedefte kabul.** Pozitif kontrol: U+0085 NEL (Cc) red. Docstring "kontrol karakteri (kategori Cc)" der, tutarli; satir ayiricilarin T-007/normalizer yoluna etkisi `[ÖLÇÜLMÜYOR]`. Pin: `test_bulgu_s_hedefte_satir_ayirici_zl_zp_ve_cf_kabul`.

**D-A10 · Kaynakta kontrol karakteri (`\n`, `\t`, NUL) kabul; esleme harfiyen.** Docstring iddia etmiyor; OCR metninde satir ici `\n` gecmesi beklenmez. Bilgi. Pin: `test_bulgu_s_kaynakta_kontrol_karakteri_kabul`.

**D-A11 · Yarim genislik katakana metni (`ﾏﾙｸｽ`) tam genislik terimi (`マルクス`) bulmaz -- NFC, NFKC degil.** Docstring "yarim genislik Katakana" yalniz betik sinifi icin der; eslemede ayri yazimdir (yarim genislik terim ayri kayit olarak calisir, pozitif). Bilgi. Pin: `test_b_yarim_genislik_katakana_tam_genislik_terimi_bulmaz_nfc_nfkc_degil`.

**D-A12 · `terimleri_gom` hit'i olmayan segmentin bozuk `placeholders` bicimini denetlemez (aynen doner).** Docstring "hit'i olmayan segment ayni nesne" der, tutarli; pipeline'da `lookup_segments` ayni segmenti `ContractViolation` ile yakalar (pozitif). Bilgi. Pin: `test_bulgu_n_hitsiz_segmentin_bozuk_placeholders_gomde_denetlenmez`.

**D-A13 · Butce payi yuk altinda (D-A6 devami).** `r2-sonda-04` kosum 2 (baska surec model yuklerken): 1000 seg x fixture 11 -> 26 ms, karisik 3 dil / 4000 hit 18 -> 42 ms (< 50, pay 1.2x); real_check #8 bu makinede 18.0 ms. `test_p_*` sure testleri izleyicili kosumda atlanir (`skipif`), butce izleyicisiz olculur. Bilgi.

**D-A14 · Cf karakterleri DIGER sinifinda -> `マルクス​` betik gecisiyle sinir (hit), `Marcus​` degil.** Tur-1 D-A3 ("Cf komsusu sinir degil") artik yalniz DIGER|DIGER cifti icin gecerli; docstring Cf'yi `[ÖLÇÜLMÜYOR]` damgaliyor, tutarli. `r2-sonda-01` tablosu. Bilgi.

## Dogrulanan v3 iddialari (secki; hepsi `r2-A-mercek-testleri.txt`, 254 yeni test)

- **Zincir (K1 ▲):** 2/3/4/10 uyeli (`長老マルクスアイラ水車小屋` 4 hit, `マルクス`x10, `Marcus`x10); zincir ucu yer tutucu (`{0}マルクスアイラ`, `windmill%s`, `wind%smill` iki tek uye; harf yt `AA` bildirilince 2 hit, bildirilmezse 0); zincir ucu KR ek (`마르쿠스아일라에게(는)` 2 hit, 3 ek 0, `가나` 0); zincir ucu betik gecisi (`長老マルクス村` 2, `村長老マルクス` 1); ortusen daha uzun aday olu iken kisa zincir kazanir (`{水車小屋,水車,小屋町}` + `水車小屋町` -> `水車`+`小屋町`, iki JSON sirasinda; uzun canliyken kazanir); `{wind,mill,windmill}`: `windmills` 0 / `windmill` 1; **"hicbir uye eslesmez" ortadaki uye icin de tutuyor** (`windmillstones`, `xwindmillstone`, `windmillstonex` 0, metin dokunulmaz; pozitif `windmillstone` 3 -> `RüzgarDeğirmenTas`); 5 karisik metin x iki sozluk sirasi ayni; DFS geri sarma: `a2..a11` + `a`x10000 -> 908xa11 + a10 + a2 = 910 uye, 10000/10000 kaplama (tur 1: 909 hit, son harf kayip). Fuzz: 3 tohum x 300 sozluk x 20 metin + yt varyanti, bes degismez.
- **Betik gecisi (K1 ▲):** 28 karakterlik tablo kamu API ile (sag ve sol simetrik): `ー ｰ ﾏ ㇰ ヶ ヽ` Katakana; `々 〆 〇 三 漢 ⼀ U+20000` Han; `あ ゝ` Hiragana; Jamo `ᄀ`, uyumluluk `ㄱ`, yarim genislik `ﾡ`, hece Hangul; `Ｍ ａ 2 ① ♪ 😀 α` + hentaigana `U+1B100` + `㈱` DIGER. Docstring pozitif 15 / negatif 18 ornek; birlestirici isaret sagda sinir degil (`マルクス゚`, `Marcus̸` 0), solda betik gecisi (`か゚マルクス` hit); `・`/ideografik bosluk gercek sinir. Sonda tablosu 71 karakter 0 uyumsuz.
- **Ek listeleri (K1 ▲):** 15 JP eki ayni betikli terimle (`長老`+kanji ek, `ひかり`+hiragana ek), ek+parcacik ve ek+`。`; ek+parcacik zinciri 7 ornek; `ひかりだからね`/`ひかりさんたちよ` (3 ek) 0, iki ek hit; Katakana adda ek sayisi onemsiz (`マルクスさんたちよね` hit); bilesik negatifleri (`ひかりさんご`, `長老様子`, `ひかりかわ`; `ひかりやま` hit). 37 KR eki x 3 baglam (tek, `. ` ile, ikinci ek `는`); 3 ek 0 / 2 ek hit; `님프`/`씨앗`/`아침`/`도둑`/`이다음` 0; `이랑`/`랑`/`이랑은`/`랑은` hit, `이랑은요` 0; v3 ekleri solda sinir degil.
- **Trie/IGNORECASE (K1 ▲):** 7 cift (`ß/ẞ ΐ/ΐ ΰ/ΰ ﬅ/ﬆ ᾈ/ᾀ ǅ/Ǆ µ/μ`) x 2 sira x 6 metin (harfiyen + capraz yazim), `source_term` metinden; Turkce 4 terim x 5 metin matrisi, indeksler orijinal metne gore (`x İstanbul y` -> (2,10)), gomme `Istanbul`; `i`+U+0307 re.I disi (eslesmez, tekrar sayilir -- D-A2 sinifi); Kelvin isareti NFC -> `K` (source_term NFC dilim); `strasse` != `straße`. Sonda: 1495 cift 0 ayrisan, ters yon 0.
- **K2 NFC ▲:** hit'li NFD segment -> `text` ve `placeholders` NFC, her yer tutucu alt dize, tuple uzunluk/sira/bos oge korunur, `speaker` NFD **dokunulmamis**, `source_blocks`/`bbox` aynen, girdi degismedi; hit'siz NFD segment `is` (yer tutucusu da NFD); `placeholders` duz `str`/`bytes`/`None`/`int`/`str` olmayan oge/ic ice tuple -> `lookup_segments` ve `terimleri_gom` `ContractViolation` (mesajda "placeholders", `TypeError` degil); dogrudan `lookup` `TypeError` kalir; `text` int -> CV; NFD `source_term`/`target_term` + NFC segment uyumlu.
- **K6 ▲:** 6 terminator x 3 konum (bas/orta/son) kaynakta red (mesajda terim), hedefte red; terminator olmayan 10 noktalama kabul ve eslesir (`St Marcus`, `a'b`, `ab…`); 9 kontrol karakteri (U+0000/0009/000A/000B/000C/000D/001F/007F/0085) red (mesajda kodpoint); kaynak 1 red / 2, 99, 100 kabul / 101, 2000, 10000 `ValueError` (asla `RecursionError`); uzunluk NFC sonrasi (NFD 200 -> 100 kabul, 202 -> 101 red); 1000 terim x 100 kodpoint yuklenir ve eslesir.
- **K5 ▲:** 8000 hit < 60 ms ve 2x hit -> < 3x sure; 8000 uyeli zincir canli/olu-sag/olu-sol < 60 ms; `lookup_segments` 1000 seg x fixture v3 (7 terim, 4000 hit) + gom < 50 ms; a*10000 < 200 ms; 8 is parcacigi paylasilan store ayni sonuc (thread-safe iddiasi).

## Tester yukumlulugu / oneri (sef icin, sirali)

1. **O-A5:** `くん`/`さま` (hiragana saygi ekleri) listeye; gercek motor olcusu elde (`r2-sonda-03-gercek-model.txt`). Tek satir; K1 ▲ olcusune iki pozitif.
2. **D-A8:** KR `다`/`예요`/`이에요`/`한테서`/`에게서` -- olculen cumlelerde urun etkisi yok; listeye almak ucuz, karar sefin.
3. Docstring'e (bilgi): yarim genislik kana eslemede ayri yazimdir (NFKC yok); Cf karakterleri DIGER sinifi (betik gecisi verir).
4. `tester_A/` sefin dizinine tasinabilir: fuzz/diferansiyel (`test_z_fuzz_*`), betik tablosu (`test_b_betik_sinifi_kamu_apiyle_olculur`), thread testi implementer adlarinda gorunmuyor.
