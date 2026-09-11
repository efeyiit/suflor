---
task: T-007
role: tester
round: 2
decision: onay
checks:
  - name: "taban 1 -- mypy --strict temiz"
    cmd: "python -m mypy --strict --explicit-package-bases src/translate/local_nmt.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-taban-1-mypy.txt
  - name: "taban 2 -- birim 255 passed (210 -> 255)"
    cmd: "python -m pytest tests/unit/translate/test_local_nmt.py -q -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-taban-2-pytest.txt
  - name: "taban 3 -- real_check 13/13 TEMIZ, cp1254 konsol (PYTHONIOENCODING yok), [6] medyan 331 ms; NOT: sef kararindaki '#4c {PLAYER}!' real_check'te YOK (13 kontrol) -- B2 ile kapatildi"
    cmd: "python .agents/tasks/T-007/real_check.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-taban-3-real_check-cp1254.txt
  - name: "taban 4 -- kapsam %100 (243 ifade, 1 pragma)"
    cmd: "python -m pytest tests/unit/translate/test_local_nmt.py -q -p no:cacheprovider --cov=src.translate.local_nmt --cov-fail-under=90 --cov-report=term-missing"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-taban-4-kapsam.txt
  - name: "taban 5 -- tam takim 1359 passed (1314 -> 1359, dusen yok)"
    cmd: "python -m pytest tests -q -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-taban-5-tum-takim.txt
  - name: "B1 -- yeni R2 mutantlarinin SEMANTIK on-dogrulamasi (ayna, ayri surec): 33 davranis mutanti amaclanan farki uretiyor, 4 kontrol (R2-C07/YT-09/10/11) sondada ESDEGER -- kit hatasi yok (tur 1 K3-07 dersi)"
    cmd: "TESTER_B_SCRATCH=<scratch> python .agents/tasks/T-007/tester_B/r2_mutant_semantik.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-B1-mutant-semantik.txt
  - name: "B1/B2-4 -- mutant kiti (tur 1 53+6 REGRESYON + tur 2 R2 33+4) x 5 kapi, ayna agaci (models/ dahil, cp1254): tur 1 53/53 YAKALANDI (K3-03, K3-05, K10-08, K10-09 ✗->✓), 6/6 kontrol kacti; R2 21/33 yakalandi, 4/4 kontrol kacti, 12 kacan (asagida siniflandi: bloke eden YOK)"
    cmd: "TESTER_B_SCRATCH=<scratch> python .agents/tasks/T-007/tester_B/mutant_kiti.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-B1-mutant-kiti.txt
  - name: "B1 -- R2-YT-12 (segment izolasyonu; kit koşumu basladiktan sonra eklendi) ayri kosum: [.....] kacti -> keskinlik"
    cmd: "TESTER_B_SCRATCH=<scratch> python .agents/tasks/T-007/tester_B/mutant_kiti.py R2-YT-12"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-B1-mutant-kiti-YT-12.txt
  - name: "B1 -- kapi basina ozet tablo (tur 1: G2 53/53, G3 10/53; R2: G2 21/33, G3 3/33)"
    cmd: "python .agents/tasks/T-007/tester_B/r2_ozet_tablo.py tester_B_evidence/r2-B1-mutant-kiti.txt"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-B1-mutant-kiti-ozet-tablo.txt
  - name: "B1b -- AYIRT ETME: 13 kacan R2 mutanti x {teslim testleri, mercek-B r2 testleri} ayri aynada: teslim 13/13 `.` (kitle tutarli), mercek-B r2 13/13 `X`; mutasyonsuz taban 255 + 107 passed (yanlis pozitif yok) -> her kacan sinif icin hazir olcu var"
    cmd: "TESTER_B_SCRATCH=<scratch> python .agents/tasks/T-007/tester_B/r2_ayirt_etme.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-B1b-ayirt-etme.txt
  - name: "B2 -- T2-2 GERCEK MODELDE (depo kodu, ayri surec, motor sarmalanip parca sayildi, metin basilmadi): `{PLAYER}!`/`{0}!`/`{0}。`/`{0} {1}!`/`<T0>?!` -> giden 0, FABRIKA 0 (motor kurulmadi), cikti == kaynak; pozitif kontroller (bildirilmemis `{PLAYER}!`, `{PLAYER} is here.`, `{0}! Wait!`) -> giden 1; stderr 0 bayt"
    cmd: "python .agents/tasks/T-007/tester_B/r2_gercek_model_t22.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-B2-gercek-model-t22.txt
  - name: "B2-4 -- tur 1 mercek-B testleri (55) yeni teslimde: 54 passed, 1 failed (`test_b2_gercek_adli_testler_listesi`: ad listesi karakterizasyonu, yeni `test_k6_..._gercekten_..._pozitif_kontrol` eklendi -- BENIM testimin kirilganligi, teslim regresyonu DEGIL; yeniden nisanlandi)"
    cmd: "python -m pytest .agents/tasks/T-007/tester_B -q -p no:cacheprovider -rfE  (yeniden nisan ONCESI)"
    exit_code: 1
    result: kaldi
    evidence: tester_B_evidence/r2-B4-mercek-testleri-regresyon-ilk.txt
  - name: "mercek-B testleri TUMU: 55 (tur 1, yeniden nisanli) + 98 (tur 2: test_mercek_B_r2.py) = 153 passed"
    cmd: "python -m pytest .agents/tasks/T-007/tester_B -q -p no:cacheprovider -rfE"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-B4-mercek-testleri-tumu.txt
  - name: "B2-4 -- bariyer kosum bicimleri: `pytest tests` / `tests/unit/translate` / dosya -> toplama sonunda meta_path[0] _T007Bariyer, translate testleri 259/259 setup aninda basta, yasak kok sys.modules 0; `tests/unit/translate` DIZININDEN `pytest .` hala `src` import edemiyor (sef 'tur sonrasi ekler' demisti -- henuz eklenmemis, bilgi)"
    cmd: "PYTHONPATH=.agents/tasks/T-007/tester_B TB_GOZLEM=<dosya> python -m pytest tests -q -p no:cacheprovider -p tb_gozlem_plugin  (+2 bicim + dizinden)"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-B4-bariyer-kosum-bicimleri.txt
  - name: "B2-4 -- sefin bariyeriyle BIRLIKTE iki sirada 412 passed (259 + 153)"
    cmd: "python -m pytest tests/unit/translate .agents/tasks/T-007/tester_B -q -p no:cacheprovider  (ve ters sira)"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-B4-birlikte-kosum.txt
  - name: "B2-4 -- totoloji taramasi 109 fonksiyon: assert'siz 0, sabit 0, cok-ifadeli raises 0, turetilmis referans 0; damga 4 + hasattr 1 (tur 1 ile ayni); raises match= 1/37 (yalniz T2-3 pozitif kontrol -- istenen buydu)"
    cmd: "python .agents/tasks/T-007/tester_B/b2_totoloji_tarama.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-B4-totoloji-tarama.txt
  - name: "sahiplik: git status --short -- src tests real_check.py packet.md conftest.py sef_karari-tur2.md sef_dogrulama/ BOS (ayna agaclari depo disi)"
    cmd: "git status --short -- src tests .agents/tasks/T-007/real_check.py .agents/tasks/T-007/packet.md tests/unit/translate/conftest.py .agents/tasks/T-007/sef_karari-tur2.md .agents/tasks/T-007/sef_dogrulama"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-git-status-src-tests.txt
  - name: "GOZLEM (sefe): tester_B/ altinda bu oturumun YAZMADIGI iki degisiklik belirdi (b2_totoloji_tarama.py etiket satiri 10:42:50 + r2-B4-totoloji-tarama.txt yeniden yazildi; r2-B1-mutant-kiti-ek-YT12.txt 10:55:42) -- ayni gorevle ikinci bir Tester-B sureci calisiyor olabilir; bu verdict 10:57 sonrasi yazildi"
    cmd: "ls -la --time-style=full-iso .agents/tasks/T-007/tester_B .agents/tasks/T-007/tester_B_evidence; git diff -- .agents/tasks/T-007/tester_B/b2_totoloji_tarama.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-eszamanli-yazim-gozlemi.txt
blocking_issues: []
---

# T-007 · Tester-B · mercek B (test kalitesi) · tur 2

**Karar: ONAY.** Tur 1'in bloke edicisi (K3-03/K3-05 beş kapıdan geçiyordu) **kapandı**: tur 1 kitinin 53 davranış mutantının **53'ü** yakalanıyor (K3-03 `?` 4 testle, K3-05 `！` 3 testle, K10-08/09 1–2 testle), 6/6 kontrol kaçıyor. Tur 2'nin üç kalemi değişmez düzeyinde yeniden ölçüldü (33 yeni davranış mutantı + 4 yeni kontrol + 98 yeni mercek testi + gerçek model). **13 yeni mutant beş kapıdan kaçıyor; hiçbiri ret eşiğini (ürünü bozan **ve** erişilebilir) geçmiyor** — hepsi keskinlik/bilgi sınıfı, her biri için ayırt eden hazır ölçü `tester_B/test_mercek_B_r2.py`'de (13/13 ✗→✓, mutasyonsuz 107 passed). §7: Hakem gerekmiyor.

Kör çalıştım: `tester_A/` okunmadı. `delivery.md` (round 2, `known_gaps`) şefin bu turdaki talimatıyla, kit ve mercek testleri **tasarlanıp koşulduktan sonra** okundu (kaçanların hangisini bildiğine bakmak için — aşağıda). Tüm sayılar bu makinede koşuldu; ham çıktılar `tester_B_evidence/r2-*`; mutasyonlar iki ayna ağacında, depoya yazılmadı.

## 0 · Şefin tabanı — birebir (cp1254)

mypy 0 · birim **255** · real_check **13/13** TEMİZ ([6] medyan 331 ms) · kapsam **%100** (243 ifade, 1 pragma) · tam takım **1359**. Not: `sef_karari-tur2.md` T2-2 ölçüsü olarak `real_check #4c` yazıyor; `real_check.py`'de #4c **yok** (13 kontrol, şefe ait). B2'de kendi gerçek-model ölçümümle kapattım.

## B2-1 · T2-1 gerçekten kapandı mı? — Evet; ölçü değişmezi kancalıyor, biçimi değil

**Yeniden koşum (`r2-B1-mutant-kiti.txt`):** K3-01..06 altısı da `[.X.XX]`/`[.XXXX]`; K3-03 → `test_k3b_bolme…[A? B.]`, `test_k3b_her_terminator_tek_basina_boler[U+003F]`, `…_diger_isaretler_yokken…[U+003F]` (+1); K3-05 aynı desen `[U+FF01]`. `TERMINATORLER` sabiti test dosyasında paket metninden bağımsız yazılı (4.6/8).

**Yeni varyantlar — küme sınırı, kapanış kümesi, regex yapısı (semantik ön-doğrulama `r2-B1-mutant-semantik.txt`: her mutant amaçlanan farkı üretiyor, kontroller eşdeğer):**

| # | mutant | 5 kapı | yakalayan / sınıf |
|---|---|---|---|
| R2-K3-12 | `,` fazladan (virgülde böler) | `.XXXX` | negatif kontrol `[virgul]` **+ real_check [2]** ("değirmen YOK") — **bulgu değil, ölçü var** |
| R2-K3-13/14/15 | `;` / `…` / `，` fazladan | `.X.XX` | negatif kontrol |
| **R2-K3-16** | `．` (U+FF0E) fazladan | **`.....`** | belgeli sınır ("`．` terminatör DEĞİL") teslim dosyasında ölçülmüyor; `delivery.md` A'nın `A．B．` satırının bunu kilitlediğini ve şefin A'yı regresyon olarak koştuğunu yazıyor. Ürün: `．` bölünse kayıp yok. **Bilgi.** |
| **R2-K3-17** | `\n` fazladan | **`.....`** | **Erişilemez:** `src/ocr/normalizer.py` `_collapse_intraline` blok içi `\n`'leri Segment üretiminden önce tek satıra indiriyor. **Bilgi.** |
| R2-K3-18a..h | kapanış kümesinden `』` `）` `)` `"` `'` `”` `’` `»` **her biri ayrı** eksik | **`.....` ×8** | Kapanış değişmezi ("terminatörden sonraki kapanış işareti cümleye dahil") **9 noktanın 1'inde** (`」`, K3-07) ölçülüyor — T2-1 ile aynı 4.6/7 deseni. Ürün etkisi: `A.” B.` → `A.` + `” B.`; kayıp **yok**, uydurma **yok** (tek başına kapanış Y2 süzgeciyle aynen geçer), işaret sonraki cümleyle modele gider → noktalama yerleşimi (kalite). **Keskinlik**, ret değil. Hazır ölçü: `test_r2_k3_her_kapanis_isareti_tek_basina_onceki_cumleye_dahil[9]` → 8/8 ✗→✓. |
| R2-K3-19 | `\Z` kuyruk dalı yok (noktalamasız metin hiç parça üretmez → çevrilmez) | `.XXXX` | 21 test + real_check [8] |
| R2-K3-20 | terminatör–kapanış arası `\s*` yok | `.X.XX` | `[A. 」 B.]` |
| R2-K3-21 | `[T]+` → `[T]` (`...` üçe bölünür) | `.X.XX` | `[Wait... what?!]` |
| R2-C07 | `\Z` → `$` (kontrol) | `.....` | doğru: eşdeğer |

Ek değişmez ölçüsü (`test_r2_k3_fuzz_degismezi_1000_rastgele_metin`, seed 7): 1000 rastgele karışımda (harf + 6 terminatör + 9 kapanış + küme dışı 13 işaret) ham birleşim = kaynak, her parçada ilk terminatörden sonra yalnız terminatör/kapanış/boşluk, son parça dışında her parça terminatörle biter, terminatör+harf ardışıklığı hep iki parçada → geçiyor; 42 nokta × 7 konum (`A{t} B`, bitişik, başta, ardışık, kapanışlı, boşluklu kapanış, üçlü) geçiyor.

## B2-2 · T2-2 değişmezi kancalanıyor — 8/8 davranış mutantı yakalandı, 3/3 kontrol kaçtı

| # | mutant | 5 kapı | yakalayan |
|---|---|---|---|
| R2-YT-01 | çağrı yerinde yer tutucular geçilmiyor (tur 1 davranışı) | `.X.XX` | `test_k3e_*` |
| R2-YT-02 | gövdede çıkarım yok | `.X.XX` | `test_k3e_*` |
| R2-YT-03 | yalnız **ilk** yer tutucu çıkarılıyor | `.X.XX` | `[iki-yt]`, `[iki-yt-bitisik]` +3 |
| R2-YT-04 | her yer tutucunun yalnız **ilk geçişi** çıkarılıyor | `.X.XX` | **yalnız** `test_k3e_modele_gider_yardimcisi_…` (`{0}{0}!`) — sağlayıcı düzeyinde fixture yok; helper public API olduğu için kabul (bilgi) |
| R2-YT-05 | çıkarım **regex** `\{…\}`, liste yok sayılıyor | `.X.XX` | `bildirilmemisse_metindir`, `[yuzde-s]`, `[acili]`, `[koseli]` +3 |
| R2-YT-06 | çıkarım yerine tam eşitlik (`parca in yer_tutucular`) | `.X.XX` | `[unlem]`, `[JP-nokta]` … |
| R2-YT-07 | ölçüt `isalnum` → "boş değil" | `.XXXX` | + real_check [4b] |
| R2-YT-08 | karar parça yerine **segment** metniyle | `.X.XX` | `[vokatif+cumle]`, `[sinirda-nokta]` |
| **R2-YT-12** | karar **tüm segmentlerin** yer tutucu birleşimiyle (izolasyon yok) | **`.....`** | segment A `{0}` bildirir, B'de bildirilmemiş `{0}!` metin olmalı → mutantta çevrilmez. Nadir (normalizer segment başına bildirir). **Keskinlik**; hazır ölçü `test_r2_t22_segment_izolasyonu…` ✗→✓ |
| R2-YT-09/10/11 | `yt in kalan` ön koşulu / boşlukla değiştirme / `if yt` yok (kontrol) | `.....` | doğru: eşdeğer |
| K3-08 | `isalnum`→`isalpha` (hedef `kalan`'a güncellendi) | `.X.XX` | `[rakam-kalir]`, `test_k3c[3.5]` |

Uç durumlar (`test_r2_t22_modele_gider_yardimcisi_uc_durumlar`, 21 nokta): çıkarım **tam alt dize** (`{0}}!` → `}!` gitmez; `{{0}!` gitmez; `{0}}` bildirilmişse de gitmez); `{0} a {1}` → gider; Unicode `{0} ç` / `{0}村` / `{0} ３` → gider; liste boş ya da `("",)` iken `{0}!` → gider; `PLAYER!`+`("PLAYER",)` → gitmez, `PLAYERS!` → gider; büyük/küçük harf duyarlı; örtüşen yer tutucularda çıkarım sırası sonucu değiştirmiyor. Sağlayıcı düzeyinde: 9 yalnız-noktalama kalıntısı → fabrika 0, çıktı aynen; aynı parça yalnız `placeholders` farkıyla iki kola ayrılıyor (pozitif/negatif çift).

**Gerçek model (`r2-B2-gercek-model-t22.txt`):** `{PLAYER}!`, `{0}!`, `{0}。`, `{0} {1}!`, `<T0>?!` → modele giden **0**, **fabrika 0** (motor hiç kurulmadı), çıktı == kaynak, yer tutucu çıktıda; bildirilmemiş `{PLAYER}!` / `{PLAYER} is here.` / `{0}! Wait!` → giden 1. stderr 0 bayt.

**Bilgi (K5, tur 1 kabul, docstring `max(1, sayım)`):** bildirilen ama **metinde geçmeyen** yer tutucu çıktıya eklenir (`{0} ç` + `("{0}","{1}")` → `… {1}`; `test_r2_t22_bilgi_…`). Normalizer yer tutucuyu metinden çıkardığı için erişilemez; `delivery.md` de aynı notu düşmüş. T2-2 bulgusu değil.

## B2-3 · T2-3

**Nöbetçi motor çıktısını görüyor mu:** K10-08 (`{cikti!r}`) → `[sayi-nobetcili-cikti]`; K10-09 (`{nesne!r}`) → `[bozuk-nesne-nobetcili]`, `[bos-hipotez-nobetcili-nesne]`; R2-K10-12 (`{tokenler!r}`) → `[int-token-nobetcili-hipotez]`; R2-K10-13 (`{metinler!r}`) → `[decode-tip-nobetcili-nesne]`; R2-K10-14 (decode istisnasına hipotez tokenleri) → `[decode]` (echo motor: kaynak nöbetçisi); R2-K10-15 (encode istisnasına parçalar) → `[encode]`. Beş nöbetçili fabrikanın **iddia ettiği raise satırına düştüğü** ayrıca ölçüldü (`test_r2_t23_nobetci_testinin_bes_motor_yolu_…`: mesaj alt dizeleri `kadar hipotez dondurmedi` / `hipotez listesi yok ya da bos` / `hipotez tokenleri str degil` / `decode str dondurmedi`).

**Kaçan iki yol (keskinlik, gerçek CT2'de erişilemez):** **R2-K10-10** `motor dizi yerine X dondurdu` mesajına `{cikti!r}` (motor düz `str` döndürürse çeviri metni mesaja) ve **R2-K10-11** `hipotez token dizisi degil` mesajına `{ilk!r}` (hipotez düz `str` ise) → `[.....]`; teslimin nöbetçi testi bu yolları nöbetçisiz (`None`/`7`/`"tur_Latn x"`) sınıyor. Gerçek CT2 hep liste/liste-of-str döndürür (olcum-1) → erişilebilirlik düşük; T2-3 (1)'in "2 parametre satırı" lafzını implementer 5 satıra genişletmiş, 6. ve 7. yol kalmış. Hazır ölçü: `test_r2_t23_nobetcisiz_kalan_yollar_da_motor_ciktisini_tasimaz[5]` (2+2 ✗→✓).

**`match=` doğru sebebi sabitliyor mu — evet (test-of-test, TEST dosyası mutantı):** R2-M-01 `_StdoutaYazan` stderr'e yazınca `[stdout]` **düşüyor** (`.X.XX`, "Regex pattern did not match"); R2-M-02 `_UyariVeren` logger'a yazınca `[warnings]` düşüyor. Mercek testi 7 sahtenin **her biri** için kanalı değiştirip teslimin `match=` değerini parametrize tablosundan **okuyarak** (kopyalamadan) düşmeyi doğruluyor (`test_r2_t23_match_kanal_degisince_duser…[7]`); değişmemiş 7 sahte teslimin kendi `match=`iyle geçiyor (pozitif kontrol).

## B2-4 · Regresyon

* **Tur 1 kiti:** 53/53 yakalandı, 6/6 kontrol kaçtı (tur 1: 49/53). Tahminden sapan 6 kalem tur 1'dekilerle aynı (K4-02 real_check kör, K4-07/K8-04/R2-K3-12/R2-K3-19 beklenenden fazla, K10-08 artık yakalanıyor). K3-08 hedef satırı T2-2 ile değiştiği için kitte güncellendi (`kalan`).
* **Tur 1 mercek testleri (55):** 54 geçti, 1 kırık — `test_b2_gercek_adli_testler_listesi` (ad listesi karakterizasyonu; yeni `test_k6_motor_ciktisi_nobetcisi_gercekten_motora_ulasiyor_pozitif_kontrol` eklendi). **Benim testimin kırılganlığı**, teslim regresyonu değil; yeniden nişanlandı (yeni testin gövdesi gerçek pozitif kontrol: nöbetçi `r.translations`'a ulaşıyor). Şefin beklediği "üç kırık" A'nın dizinindeydi; dördüncü kırık **yok**.
* **Bariyer:** `pytest tests` → toplama sonunda `meta_path[0] _T007Bariyer` (`[1] _T006Bariyer`), translate testleri 259/259 setup anında başta, yasak kök 0; üç koşum biçiminde aynı. `tests/unit/translate` **dizininden** `pytest .` hâlâ `ModuleNotFoundError: src` — şef "tur sonrası ekler" demişti, henüz eklenmemiş (bilgi, kapıyı etkilemez). Kendi bariyerimle birlikte iki sırada 412 passed.
* **Totoloji:** 109 fonksiyon; assert'siz 0, sabit 0, çok-ifadeli `raises` 0, türetilmiş referans 0; damga 4 + `hasattr` 1 (tur 1 ile aynı); `raises` `match=` 1/37 (yalnız T2-3 pozitif kontrol — istenen buydu).

## B2-5 · Orantı — ret eşiği geçilmiyor

13 kaçan mutantın hiçbiri **ürünü bozan ∧ erişilebilir** değil: R2-K3-17 ve R2-YT-12 erişilemez/nadir; R2-K3-16 belgeli ve (delivery'ye göre) A'nın dizininde ölçülü; R2-K3-18a..h erişilebilir ama kayıpsız/uydurmasız (kalite); R2-K10-10/11 gerçek motorla erişilemez. Tur 1'in ret gerekçesi (cümle kaybı, tek karakterlik sabit) bu turda 53/53 ile kapandı. §7 gereği Hakem'e gitmiyor.

**Şefe kayıt (bloke etmeyen, karara/env.md'ye yazılabilir):** (1) kapanış kümesi 9 noktanın 1'inde ölçülüyor — hazır 9-noktalı test `tester_B/test_mercek_B_r2.py::test_r2_k3_her_kapanis_isareti_tek_basina_onceki_cumleye_dahil`; (2) motor çıktısı nöbetçisi 7 yolun 5'inde — `dizi yerine` ve `ilk` str yolları için 5 satır hazır; (3) segment izolasyonu — 1 test hazır; (4) `．`/`\n` küme sınırı negatif kontrolde yok — 13 işaretli negatif kontrol hazır; (5) real_check #4c yok; (6) K5 `max(1,…)` bildirilen-ama-yok yer tutucuyu ekler (erişilemez, belgeli); (7) translate dizininden koşum hâlâ kırık (şef).

**Gözlem (şefe):** koşum sırasında `tester_B/` altında bu oturumun yazmadığı iki değişiklik belirdi (`r2-eszamanli-yazim-gozlemi.txt`): aynı görevle ikinci bir Tester-B süreci çalışıyor olabilir; bu verdict onun ardından yazıldı, üstüne yazılırsa zaman damgasından ayırt edilebilir.

## Dosyalar

`tester_B/`: `mutant_kiti.py` (53+6 tur 1 + **34+4 R2**, `dosya` alanı ile TEST dosyası mutantları), `r2_mutant_semantik.py`, `r2_ayirt_etme.py`, `r2_gercek_model_t22.py`, `r2_ozet_tablo.py`, `test_mercek_B_r2.py` (98), `test_mercek_B.py` (55, 1 yeniden nişan). `tester_B_evidence/r2-*`: taban 1–5, B1 (kit, YT-12, semantik, özet), B1b ayırt etme, B2 gerçek model, B4 (mercek ilk/tümü, bariyer, birlikte, totoloji), git status, eşzamanlı yazım gözlemi.
