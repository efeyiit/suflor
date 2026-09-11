---
task: T-007
role: tester
round: 1
decision: ret
checks:
  - name: "taban 1 -- mypy --strict temiz"
    cmd: "python -m mypy --strict --explicit-package-bases src/translate/local_nmt.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/taban-1-mypy.txt
  - name: "taban 2 -- birim 210 passed"
    cmd: "python -m pytest tests/unit/translate/test_local_nmt.py -q -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/taban-2-pytest.txt
  - name: "taban 3 -- real_check 13/13 TEMIZ, cp1254 konsol (PYTHONIOENCODING yok), medyan 315 ms"
    cmd: "python .agents/tasks/T-007/real_check.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/taban-3-real_check-cp1254.txt
  - name: "taban 4 -- kapsam %100 (239 ifade, 1 pragma: _varsayilan_fabrika, K1 gerekceli)"
    cmd: "python -m pytest tests/unit/translate/test_local_nmt.py -q -p no:cacheprovider --cov=src.translate.local_nmt --cov-fail-under=90 --cov-report=term-missing"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/taban-4-kapsam.txt
  - name: "taban 5 -- tam takim 1314 passed"
    cmd: "python -m pytest tests -q -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/taban-5-tum-takim.txt
  - name: "B1 -- mutant kiti: 53 davranis mutanti x 5 kapi ayna agacinda (models/ dahil, cp1254): 49 YAKALANDI, 4 KACTI (K3-03 '?', K3-05 U+FF01 -> BLOKE; K10-08/09 -> keskinlik); 6/6 kontrol kacti (yanlis pozitif yok)"
    cmd: "TESTER_B_SCRATCH=<scratch> python .agents/tasks/T-007/tester_B/mutant_kiti.py"
    exit_code: 0
    result: kaldi
    evidence: tester_B_evidence/B1-mutant-kiti.txt
  - name: "B1 -- K3-07 duzeltilmis kosum (ilk surum regex'i bozan gecersiz mutantti, kit hatasi): `」` kapanis kumesinden eksik -> [.X.XX] yakalandi"
    cmd: "TESTER_B_SCRATCH=<scratch> python .agents/tasks/T-007/tester_B/mutant_kiti.py K3-07"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/B1-mutant-kiti-K3-07-duzeltilmis.txt
  - name: "B1 -- kapi basina ozet tablo (G1 2/53, G2 49/53, G3 10/53, G4 49/53, G5 49/53)"
    cmd: "python - (betik kanit dosyasinin basinda; iki kit ciktisini birlestirir)"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/B1-mutant-kiti-ozet-tablo.txt
  - name: "B1b -- kacan K3-03/K3-05'in bolme etkisi (teslimin regex'i, kume eksik): KR 3->2, EN 2->1, JP 2->1 parca"
    cmd: "python - (betik kanit dosyasinin basinda)"
    exit_code: 0
    result: kaldi
    evidence: tester_B_evidence/B1b-kacan-mutant-urun-etkisi.txt
  - name: "B1b -- AYIRT ETME: onerilen test ekleri (a)(b)(c) mutasyonsuz src'de 220 passed (yanlis pozitif yok); K3-03/K3-05/K10-08/K10-09 dordu de yakalanir"
    cmd: "TESTER_B_SCRATCH=<scratch> python .agents/tasks/T-007/tester_B/mercekB_ayirt_etme.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/B1b-mercekB-ayirt-etme.txt
  - name: "B1c -- kacan mutantlar GERCEK MODELDE: '?' eksik -> EN 2 cumle tek parca, 'hazir' KAYIP; U+FF01 eksik -> JP 2 cumle tek parca, 'dur' KAYIP (Y1 kusuru geri geliyor)"
    cmd: "TESTER_B_SCRATCH=<scratch> python .agents/tasks/T-007/tester_B/b1c_kacan_mutant_gercek_model.py"
    exit_code: 0
    result: kaldi
    evidence: tester_B_evidence/B1c-kacan-mutant-gercek-model.txt
  - name: "B2 -- totoloji taramasi (97 fonksiyon / 210 ornek): assert'siz 0, sabit 0, cok-ifadeli raises 0, turetilmis referans 0; damga (yalniz __doc__) 4, yalniz hasattr 1"
    cmd: "python .agents/tasks/T-007/tester_B/b2_totoloji_tarama.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/B2-totoloji-tarama.txt
  - name: "B3 -- bariyer kosum bicimleri: `pytest tests` / `tests/unit` / `tests/unit/translate` / dosya -> bariyer toplama sonunda meta_path[0], 214/214 translate testinde basta, yasak kok sys.modules'ta 0; translate dizininden kosum src import edemiyor (bilgi)"
    cmd: "PYTHONPATH=.agents/tasks/T-007/tester_B TB_GOZLEM=<dosya> python -m pytest tests -q -p no:cacheprovider -p tb_gozlem_plugin  (+3 bicim)"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/B3-bariyer-kosum-bicimleri.txt
  - name: "B3 -- sefin bariyeriyle BIRLIKTE her iki sirada 269 passed; hangi bariyer meta_path[0] olursa olsun match='K1 bariyeri' tutuyor"
    cmd: "python -m pytest tests/unit/translate .agents/tasks/T-007/tester_B -q -p no:cacheprovider  (ve ters sira)"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/B3-birlikte-kosum.txt
  - name: "B4 -- gercek model ayri surecte: kurulum + 7 istek + close x2 -> stdout 0 / stderr 0 bayt; pozitif kontrol os.write(2) 1 bayt; CT2 DEBUG'da 2053 bayt (kanal gorunur, saglayici seviyeye dokunmuyor); sentencepiece roundtrip/`▁` olgulari; translate_batch 31 parametre"
    cmd: "python .agents/tasks/T-007/tester_B/b4_gercek_surec_sondasi.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/B4-gercek-surec-sondasi.txt
  - name: "mercek B testleri (55): B2 sahte gerceklik, B3 kacis yollari, B4 kanca/kor nokta + teslim olcusu gercek sinifta 5 kanal + 7 pozitif kontrol dogru sebeple, B5 omur/hata (22), B6 kapsam durustlugu"
    cmd: "python -m pytest .agents/tasks/T-007/tester_B -v -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/B-mercek-testleri-tek-basina.txt
  - name: "sahiplik: git status --short -- src tests real_check.py packet.md conftest.py BOS (ayna agaci kullanildi)"
    cmd: "git status --short -- src tests .agents/tasks/T-007/real_check.py .agents/tasks/T-007/packet.md tests/unit/translate/conftest.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/git-status-src-tests.txt
blocking_issues:
  - "K3 (Y1) olcusu alti terminatorun DORDUNDE kosuyor: `?` (U+003F) ve `！` (U+FF01) hicbir testte ayirt edici konumda degil. Kumeden biri dusurulunce (K3-03, K3-05) mypy/birim/real_check/kapsam/tam takim BESI DE YESIL (B1-mutant-kiti.txt). Gercek modelde urun etkisi olculdu (B1c): EN `Are you ready? The village elder…` tek parca -> tek cumle, 'hazir' KAYIP; JP `止まれ！村の長老が…` tek parca -> 'dur' KAYIP -- KRT Y1'in duzelttigi cumle-kaybi kusuru. Erisilebilir (tek karakterlik sabit), urunu bozan, bes kapidan gecen -> ret esigi. Duzeltme ~10 satir test (feedback-B.md §3), ayirt etme olculdu: yamali testlerle 4/4 yakalanir, mutasyonsuz src 220 passed."
---

# T-007 · Tester-B · mercek B (test kalitesi, K1 bariyeri, ömür, loglama, hata taksonomisi) · tur 1

**Karar: RET — kod doğru, ölçü eksik.** Ret eşiği "ürünü bozan **ve** erişilebilir mutant beş kapıdan geçiyor": iki mutant geçiyor (K3-03, K3-05), ikisinin de ürün etkisi gerçek modelle ölçüldü (bir cümle çeviride kayboluyor — Y1'in düzelttiği sınıf). Düzeltme yalnız test dosyasında, ayırt etme gücü ölçüldü (`feedback-B.md`). Onun dışında teslim sağlam: 53 davranış mutantının 49'u yakalandı, kontrol mutantlarının hiçbiri yakalanmadı, K1 bariyeri dört koşum biçiminde de yerinde, gerçek modelle ayrı süreçte sıfır bayt, ömür/hata sınıfları 22 ek testle doğrulandı.

Kör çalıştım: `tester_A*` okunmadı. `delivery.md` ölçümler ve karar **bittikten sonra**, şefin bu turdaki açık talimatıyla ("Teslim: … delivery.md") yalnız `known_gaps`'in bulgularımı kapsayıp kapsamadığına bakmak için okundu (kapsamıyor: K3 ölçüsü "12 metin × 3 dil" diye yazılmış, işaret başına iddia yok; K6/K10 nöbetçi testi yalnız *kaynak* metin). Tüm sayılar bu makinede koşuldu; ham çıktılar `tester_B_evidence/`; mutasyonlar iki ayrı ayna ağacında (`t007_tester_B_mutroot`, `t007_tester_B_ayirt`), depoya yazılmadı (`git-status-src-tests.txt`).

## 0 · Şefin tabanı — birebir (cp1254, PYTHONIOENCODING yok)

| kapı | şef | ben |
|---|---|---|
| mypy | 0 | 0 |
| birim | 210 | 210 |
| real_check | 13/13 | 13/13 TEMİZ, `[6]` medyan 315 ms |
| kapsam | %100 | %100 (239 ifade, 1 pragma) |
| tam takım | 1314 | 1314 |

## B1 · Mutant kiti — 53 davranış + 6 kontrol × 5 kapı (`B1-mutant-kiti.txt`, özet `B1-mutant-kiti-ozet-tablo.txt`)

Kit (`tester_B/mutant_kiti.py`) depoyu `src/tests/real_check/fixtures/models(4 dosya)` ile ayna ağacına kopyalar, tek satır değiştirir, paketin beş kabul komutunu koşar (pytest'e yalnız `-p no:cacheprovider -rfE`; `PYTHONIOENCODING` **silinerek** — cp1254). Taban 5/5 yeşil. `beklenen` sütunu koşumdan **önce** yazıldı.

| # | sınıf | mutant | üründe ne olur | 5 kapı | yakalayan |
|---|---|---|---|---|---|
| K3-01 | K3 | `.` eksik | KR/EN paragraf bölünmez (Y1 aynen) | `.XXXX` | `test_k3b` ×11, real_check `[4]` |
| K3-02 | K3 | `!` eksik | `A! B.` tek parça | `.X.XX` | `test_k3b` ×3 |
| **K3-03** | **K3** | **`?` eksik** | **EN/KR `A? B.` tek parça → cümle kaybı** | **`.....`** | **—** |
| K3-04 | K3 | `。` eksik | JP paragraf bölünmez (C8) | `.XXXX` | 13 test, real_check `[3]` |
| **K3-05** | **K3** | **`！` (U+FF01) eksik** | **JP `A！B。` tek parça → cümle kaybı** | **`.....`** | **—** |
| K3-06 | K3 | `？` eksik | `A？B。` tek parça | `.X.XX` | `test_k3b` ×2 |
| K3-07 | K3 | `」` kapanış kümesinden eksik | `」` sonraki cümleye yapışır | `.X.XX` | `test_k3b[A.」B.]` ×5 (düzeltilmiş koşum; ilk sürüm regex'i bozuyordu — kit hatam) |
| K3-08 | K3 | `isalnum`→`isalpha` | `42`, `5`, `3.` modele gitmez | `.X.XX` | `test_k3c[3.5]`, `modele_gider("5")` |
| K3-09/10/11 | K3 | kırpma yok / `""` birleştirme / geçiş segmenti boş | boşluklu parça / bitişik cümle / `。。。` silinir | `.X.XX` / `.X.XX` / `.XXXX` | k3b / k3a / k3c + real_check `[4b]` |
| K2-01 | K2 | cümle sayısı denetimi yok | kayma sessiz / ham IndexError | `.X.XX` | `test_k2_*` |
| K2-02 | K2 | `ensure_aligned` atlanmış | davranış aynı — **yalnız AST** yakalar | `.X.XX` | `test_k2_ast_…` (1 test) |
| K2-03 | K2 | `detected_lang=None` | | `.X.XX` | `test_k2_sonuc_alanlari` |
| K4-01..04 | K4 | JA `ja`→zho / KO `kor_hang`→jpn / ZH `chinese`→kor / EN `en_Latn` | yanlış belirteç, CT2 hata vermez | `.X.XX` ×3, `.XXXX` | 24 noktalı `test_k4_uc_bicim` (biçim başına); **K4-02'yi real_check görmedi** — KR metin JP belirteciyle de "bekliyor+doğu" verdi (içerik kontrolü zayıf, paket bunu kabul ediyor) |
| K4-05 | K4 | hedef `eng_Latn` | çeviri İngilizce | `.XXXX` | `target_prefix` testleri, real_check `[2]` |
| K4-06 | K4 | `.lower()` yok | `jpn_Jpan` reddedilir | `.XXXX` | |
| K4-07 | K4 | kaynak belirteci yok | kalite düşer | `.XXXX` | 57 test, real_check `[2]` "değirmen YOK" |
| K5-01..04 | K5 | `in` / başa ekle / dedup yok / onarım yok | ikinci `%s` kaybı / konum / fazla kopya / `{0}` kaybı | `.X.XX` ×3, `.XXXX` | `test_k5_*`; K5-04 real_check `[5]` |
| K6-01..04 | K6 | dört dosyadan biri denetlenmiyor (**her biri ayrı**) | `ProviderUnavailable` yerine | `.X.XX` ×4 | `test_k6_dort_dosyadan_biri…[<ad>]` + `zorunlu_model_dosyalari` |
| K6-05 | K6 | `ModelMissingError`→`ProviderUnavailable` | indirme dalı tetiklenmez | `.XXXX` | real_check `[8]` de |
| K6-06 | K6 | FNF eşlemesi kaldırılmış (**paket lafzı**) | paket lafzıyla uyumlu | `.X.XX` | `test_k6_fabrika_istisnasi…` e3 — **testler paketin ötesini kilitliyor** (bilgi, aşağıda) |
| K6-07/08 | K6 | `from None` / `TranslatorError` sarılır | | `.X.XX` | |
| K7-01 | K7 | `model_file=` | ASCII-dışı dizinde kurulamaz | `.XXXX` | AST + real_check `[7]` |
| K7-02 | K7 | `.resolve()` yok | real_check mutlak yol verir → ayrışmaz; **yalnız AST** | `.X.XX` | |
| K8-01..06 | K8 | inter=threads / rp 1.0 geçiliyor / mdl 1024 / mdl geçilmiyor / üst sınır yok / None→cpu | | `.X.XX` ×5, K8-04 `XX.XX` | K8-04'ü **mypy** de yakaladı (`**dict[str, object]` vs varsayılanlı Protocol) |
| K9-01/02 | K9 | kurulum dahil / sabit 0 | | `.X.XX` | `test_k9_ilk_cagri…` (fabrika 100 ms) / `test_k9_latency_motor…` |
| K10-01/02/03 | K10 | kapalı translate çalışır / motor bırakılmaz / tek örnek yok | model yeniden yüklenir / 700 MB kalır / her karede 470 ms | `.X.XX` | close / weakref / sayaç testleri |
| K10-04 | K10 | `sys.stdout.write(çeviri)` | konsola metin | `.X.XX` | soğuk+sıcak (capfd) + AST |
| K10-05 | K10 | adlı logger INFO | log dosyasına metin | `.X.XX` | caplog |
| K10-06 | K10 | `propagate=False` bilinmeyen logger INFO | | `.X.XX` | **yalnız `Logger.handle` kancası** ("nobetci bir log kaydina dustu") — kanca gerçekten ekliyor |
| K10-07 | K10 | hata mesajına **kaynak** metin | | `.X.XX` | `test_k6_hata_mesajlari…` |
| **K10-08** | K10 | sayı uyuşmazlığı mesajına **motor çıktısı** (`{cikti!r}`) | çeviri metni istisna→log | **`.....`** | — (nöbetçi testi bu yolda `"x"` hipotezi) |
| **K10-09** | K10 | bozuk-çıktı mesajına `{nesne!r}` | | **`.....`** | — |
| K1-01 | K1 | modül düzeyi `import ctranslate2` | | `XX.XX` | mypy (`import-untyped`) + bariyer |
| C01–C06 | kontrol | `tokenler and`→`len>0`; `extend`→döngü; tip ek açıklaması; dict satır sırası; join→`+`; parantez | eşdeğer | `.....` ×6 | **hiçbiri yakalanmadı** — yanlış pozitif yok |

Kapı başına: mypy 2/53 · birim 49/53 · real_check 10/53 · kapsam 49/53 · tam takım 49/53. Yalnız AST'nin yakaladığı iki mekanizma mutantı (K2-02, K7-02) paketin kendi istediği AST ölçüleri; davranışsal olarak ayrışmıyorlar (K2-02: hizalama yapısal; K7-02: real_check mutlak yol verir) — kabul, bilgi.

**Tahminden sapanlar (6):** K3-03/K3-05 beklenenden **az** (bulgu); K3-07 ilk sürüm kit hatası (düzeltildi, `B1-mutant-kiti-K3-07-duzeltilmis.txt`); K4-02 real_check'i **kör** buldu; K4-07 ve K8-04 beklenenden **fazla** yakalandı (real_check `[2]`, mypy).

### Bloke eden: K3-03 / K3-05 — neden kaçıyor, üründe ne yapıyor

AST ile bakıldı: teslimde `?` yalnız `"Wait... what?!"` (ardından `!` böler) ve `"c! e?"` (**sonda**, `\Z` kuyruğu) girdilerinde; `！` yalnız `"A。？！"`/`"!?.。！？"` gibi harfsiz parçalarda (Y2 süzgeci yutar). Hiçbirinde işaretten sonra **harf içeren ikinci cümle** yok → işaret düşse de bölünme aynı. real_check `[3]` yalnız `。`, `[4]` yalnız `.` içerir. PROTOKOL 4.6/7 (ölçü, parametre uzayının noktalarında koşmalı) ve 4.6/10 (sınıf başına pozitif kontrol): altı işaretin **ikisi** ölçülmüyor.

Ürün etkisi — teslimin regex'i, kümesi eksik (`B1b-kacan-mutant-urun-etkisi.txt`): KR (KRT Y1'in örneği) 3→2 parça, EN 2→1, JP `！,。` 2→1, JP `！？。` 3→2. **Gerçek modelle** (`B1c-…`, ayrı süreç, motor sarmalanarak parça sayıldı, metin basılmadı): `?` eksik → EN "Are you ready? The village elder is waiting for you." **1 parça → 1 cümle, "hazır" yok** (teslim: 2 → 3 cümle, üç anahtar var); `！` eksik → JP "止まれ！村の長老が…" **1 parça → 1 cümle, "dur" yok**; JP "待って！本当に行くの？" 2→1. Bu, KRT Y1'in "ikinci cümle tamamen kayboluyordu" bulgusunun aynısı. Tek karakterlik sabitte bir eksik = erişilebilir; cümle kaybı = ürünü bozan; beş kapı yeşil = ret eşiği.

**Ayırt etme (`B1b-mercekB-ayirt-etme.txt`):** `test_k3b` parametrize'ına iki satır + "her terminatör tek başına böler" testi (6 nokta) + nöbetçi testine iki motor-çıktısı satırı → mutasyonsuz src **220 passed** (yanlış pozitif yok); K3-03 ✗→**✓(2)**, K3-05 ✗→**✓(2)**, K10-08 ✗→✓(1), K10-09 ✗→✓(1); K3-01/02/04/06 birer test daha. Tam yama `feedback-B.md` §3–§4.

## B2 · Totoloji ve sahte-gerçeklik — bulgu yok, iki not

* **Tarama** (`B2-totoloji-tarama.txt`, 97 fonksiyon/210 örnek): assert'siz 0, sabit 0, çok-ifadeli `raises` 0, beklenen değeri denetlenen modülden türeten assert 0 (referanslar sabit: NLLB kodları, dosya adları, `MAKS_COZUM`, biçim tabloları — 4.6/8 tutuyor). Damga testleri (yalnız `__doc__`) **4** + yalnız `hasattr` **1** (`last_timing`) — davranışsız ama paket "hem docstring" istediği için var; kapsamı taşımıyorlar (%100 onlarsız da tutar: hepsi docstring okur). `pytest.raises` 37/37 `match`'siz — tip yeter, mesaj sözleşme değil, kabul.
* **Sahte motor gerçek CT2 biçiminde** (`test_b2_sahte_motor_…`): her girdi için `.hypotheses`, `hypotheses[0][0]=="tur_Latn"`, `</s>` yok, sayı == girdi, `source` **konumsal** (AST: `translate_batch(tokenler, target_prefix=…, beam_size=…, max_decoding_length=…, **ek)`; anahtarlar gerçek imzanın 31 parametresinin alt kümesi — imza B4 [D]'de ayrı süreçte gerçek kütüphaneden okundu, testteki sabitle eşit).
* **Sahte `encode`/`decode` düşük sadakatli ama yeterli:** tek token / `"".join`. Gerçek sentencepiece (B4 [D]): ilk parça `▁` ile başlıyor, `decode(encode(x)) == x` 6/6, `encode("")==[]`, `decode([])==""`. Sağlayıcı encode çıktısını **yalnız yıldızla yayıyor**, decode'a hipotezi **aynen** veriyor (AST testi `test_b2_saglayici_token_duzeyinde_islem_yapmiyor…`) — token düzeyinde mantık olmadığı için `▁`/boşluk davranışı sağlayıcıyı ayırmaz. Real_check ve olcum-2 gerçek yolu kapatıyor.
* "Gerçek" adlı iki test: weakref testi gerçekten ölçüyor (gc + pozitif kontrol); `test_k7_gercek_fabrika_…` **AST** (K1 gereği koşamaz) — ad yanıltıcı değil, gövde belli. Kabul.

## B3 · Bariyer — dört koşum biçiminde yerinde; kaçış yolları ölçüldü

* **Ölçüldü** (`B3-bariyer-kosum-bicimleri.txt`, gözlem eklentisi bariyeri **kurmaz**, yalnız bakar): `pytest tests`, `tests/unit`, `tests/unit/translate`, dosya adı — dördünde de toplama sonunda `meta_path[0] = _T007Bariyer` (tam takımda `[1] _T006Bariyer`), translate testlerinin **214/214**'ünde setup anında başta, yasak kök `sys.modules`'ta **0** (oturum başı/sonu). Bilgi: `tests/unit/translate` **dizininden** `pytest .` → `ModuleNotFoundError: src` (translate conftest'i depo kökünü `sys.path`e eklemiyor; contracts/ocr ekliyor). Kabul komutları kökten koşuyor, kapıyı etkilemez.
* **Kendi bariyerim** (`tb_bariyer.py`, mesaj "tester-B T-007 K1 bariyeri") şefinkiyle **birlikte** her iki sırada 269 passed; `meta_path[0]` sıraya göre `TesterBBariyer` ya da `_T007Bariyer`, `match="K1 bariyeri"` ikisinde de tutuyor (`B3-birlikte-kosum.txt`).
* **Kaçış yolları** (`test_b3_*`): `importlib.import_module` ✗, `__import__` ✗, `spec_from_file_location(paket __init__)` → `__init__` içindeki alt-modül importu meta_path'ten geçer → ✗ (`submodule_search_locations` verilerek pakete tam şans tanındı); **`sys.modules` ön-yükleme** bariyeri atlar (karakterizasyon; bu süreçte ön-yüklü kök **0**, `ONCEDEN_YUKLU==()`); **`.pyd`'yi `ExtensionFileLoader` ile doğrudan yükleme** meta_path'i hiç sormaz (yasak kökle adlandırılsa da yüklenir; bariyer sorgu sayacı değişmez) — bariyerin tek gerçek kör noktası; motor ve teslim testleri bu API'lerin hiçbirini kullanmıyor (AST sayacı 0/0). Şefin pozitif kontrolü yalnız `import_module` yolunu sınıyor (3 ad); `__import__`/statement aynı mekanizma, yeter.

## B4 · K10 kanal ölçüsü — T-006 tur 2 deseninin üst kümesi; gerçek süreçte 0 bayt

* **Desen farkı:** T-006 bilinen kütüphane logger'ına `caplog.handler` takıyordu; T-007'de ad bilinmiyor → `logging.Logger.handle` monkeypatch. Ölçüldü (`test_b4_logger_handle_kancasi_…`): `propagate=False` + INFO logger'a yazılan kayıt **kök caplog'da yok, kancada var** → gerçekten ekliyor (K10-06 mutantı da yalnız bununla düştü). **Kör noktaları** (karakterizasyon): `Handler.handle(record)` **doğrudan** (T-006 R04/R05 sınıfı) kancayı ve `caplog.records`'u atlar; seviye altı kayıt (`WARNING` logger'da `.info`) görünmez ama hiçbir yere de gitmez. Ölçü üç noktada (soğuk/sıcak/hata yolu) — 4.6/7 tutuyor.
* **Teslim ölçüsü gerçek sınıfta ateşliyor:** `LocalNmtProvider` + kanala yazan enjekte `decode` ile aynı `_k10_kanal_olcusu` 5 kanalda **doğru mesajla** düşüyor (`match=`: stdout'a / stderr'e / log kaydina ×2 / warnings kaydina), sessiz gerçek sınıf geçiyor; teslimin 7 pozitif kontrolü de doğru sebeple düşüyor (`match=` ile yeniden koşuldu) — teslimde `match=` yok (keskinlik, feedback §4-d).
* **Gerçek modelle ayrı süreç** (`B4-gercek-surec-sondasi.txt`, `capture_output` fd düzeyi): kurulum + JP 4 / KR tek segment / EN 2 / JP yer tutucu / boş / geçiş / rakam + `close()` ×2 → **stdout 0 bayt, stderr 0 bayt**, exit 0. Pozitif kontrol: `os.write(2, b"x")` → 1 bayt (yakalama çalışıyor); **CT2 seviyesi DEBUG'a çekilince aynı akış 2053 bayt** stderr → C++ log kanalı bu ölçüyle **görünüyor**, A'daki sıfır anlamlı: sağlayıcı seviyeye dokunmuyor, CT2 varsayılanı 30 (WARNING). Ek gözlem: ilk `translate` duvar 916 ms / `latency_ms` 358 (kurulum düşülmüş, K9); `"42"`/`"3.5"` gerçek modelde 2/4 karakter (ondalık bölünmesi belgeli zayıflık, aynen).
* Hata mesajı sınıfı: kaynak metin 7 yolda taşınmıyor (teslim testi + K10-07 yakalandı); **motor çıktısı** iki yolda ölçülmüyor (K10-08/09, `test_b4_hata_mesaji_motor_ciktisini_da_tasimaz…` bugünkü kodda geçiyor) — gerçek CT2 bu yolları üretmez (D2), keskinlik.

## B5 · Ömür ve hata taksonomisi — 22 test, bulgu yok

`close()` ×2 sessiz; sonrası dört istek biçimi (dolu/boş/geçiş/geçersiz dil) → `ProviderUnavailable`, fabrika ve motor sayacı **değişmez**, gözlem özellikleri çalışır; hiç kurulmamışta `close()` → fabrika 0. Fabrika ilk çağrıda `RuntimeError` → `ProviderUnavailable(__cause__)`, ikinci `translate` **yeniden dener** (sayaç 2, sonra 3 ile başarır) — paket sessiz, **docstring belgeliyor** ("sonraki translate kurulumu YENIDEN dener", `test_b5_…_belgeli` docstring'de arıyor). `ModelMissingError` fabrikadan olduğu gibi + yeniden denenir; `KeyboardInterrupt` sarılmaz, örnek tutulmaz, sonra çalışır; 2'li demet → `ProviderUnavailable(ValueError)`. İki sağlayıcı aynı fabrika: **her biri kendi kurulumunu yapar** (paylaşım yok, sayaç 2), biri kapanınca diğeri çalışır. Dört dosyanın **her biri** için `ModelMissingError` sayaç 0, mesajda yalnız eksik ad, `__cause__` yok, dosya konunca **aynı örnek** kurulur; dizin yok / dizin dosya → aynı; sıfır bayt varlık denetimini geçer (docstring "boyut denetlenmez"). `ContractViolation` ve motor istisnası sonrası sağlayıcı kullanılabilir kalır (motor önbellekte, fabrika 1). Kardeş sınıflar düz (birbirinden türemez). Kapalı sağlayıcı tip-hatalı isteği de `ProviderUnavailable` ile reddeder (sıra: kapalı → doğrulama).

**Şefe bilgi (K6-06):** teslim `FileNotFoundError` → `ModelMissingError` eşlemesi yapıyor ve testi var; paket K6(b) "kurulum istisnası → `ProviderUnavailable`" der. Paket lafzına uyan uygulama birim kapısında düşer. Docstring belgeliyor; karara yazılacak sapma, implementer'a iş değil.

## B6 · Kapsam dürüstlüğü — %100 gerçek

Tek pragma (`_varsayilan_fabrika` `def` satırı, `no cover`), gerekçesi K1: gövde `ctranslate2`/`sentencepiece` import ediyor, bariyer altında koşamaz, `real_check` #1–#8 kapatıyor; başka hiçbir fonksiyon bu kökleri import etmiyor (AST). Kapsam için yazılmış davranışsız test: 4 damga + 1 `hasattr` (yukarıda) — hepsi docstring/öznitelik okuyor, kapsama katkıları yok. `_uyum_fabrika` satırı modül yüklemesiyle kapsanıyor (Protocol uyumunu mypy denetliyor).

## Ölçülmeyen sınır (dürüst damga)

Zaman penceresi dışı yazım (atexit/Timer), dosya sistemi kanalı, `Handler.handle` doğrudan, `.pyd` doğrudan yükleme — mutant kurulmadı ya da karakterizasyon; T-006 tur 2'de de aynı sınırlar. Kalite (altın set yok) paketin kendi `[ÖLÇÜLMÜYOR]`'u.

## Dosyalar

`tester_B/`: `mutant_kiti.py` (53+6, `TB_DRY=1` kuru koşum), `mercekB_ayirt_etme.py`, `b1c_kacan_mutant_gercek_model.py`, `b2_totoloji_tarama.py`, `b4_gercek_surec_sondasi.py`, `tb_gozlem_plugin.py`, `tb_bariyer.py` + `conftest.py` (kendi bariyerim), `test_mercek_B.py` (55). `tester_B_evidence/`: taban 1–5, B1 (+K3-07 düzeltilmiş, özet tablo), B1b ×2, B1c, B2, B3 ×2, B4, mercek testleri, git status. `feedback-B.md`: yeniden üretim + yama + ayırt etme.
