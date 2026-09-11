---
task: T-007
role: tester
round: 1
lens: "A — sözleşme uyumu, cümle bölme, dil/yer tutucu doğruluğu"
decision: onay
checks:
  - name: "taban: mypy --strict temiz"
    cmd: "python -m mypy --strict --explicit-package-bases src/translate/local_nmt.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/00-taban-mypy.txt
  - name: "taban: implementer birim testleri 210 passed"
    cmd: "python -m pytest tests/unit/translate/test_local_nmt.py -q -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/01-taban-birim.txt
  - name: "taban: real_check gerçek model TEMİZ 13/13 (JP 4 cümle medyan 314 ms, uyarı 0)"
    cmd: "python .agents/tasks/T-007/real_check.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/02-taban-real_check.txt
  - name: "taban: tam takım 1314 passed"
    cmd: "python -m pytest tests -q -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/03-taban-pytest-tum.txt
  - name: "tester-A: 265 kör test, kendi bariyeri altında tek başına (A0 pozitif kontrol dahil, cp1254 konsolda)"
    cmd: "python -m pytest .agents/tasks/T-007/tester_A -q -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/testerA-pytest.txt
  - name: "tester-A: şefin dizini + tester_A birlikte 479 passed (210 + 4 bariyer + 265; iki bariyer çakışmıyor)"
    cmd: "python -m pytest tests/unit/translate .agents/tasks/T-007/tester_A -q -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/testerA-birlikte-pytest.txt
  - name: "tester-A: yalnız kendi testlerinin kapsamı %87 (eksikler K6/K10 hata yolları — mercek dışı)"
    cmd: "python -m pytest .agents/tasks/T-007/tester_A -q -p no:cacheprovider --cov=src.translate.local_nmt --cov-report=term-missing"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/testerA-cov.txt
  - name: "tester-A mutant kiti: 30/30 yakalandı (MA-00 kopya yükleme kanıtı dahil), davranış-eşdeğer kontrol MA-99 kaçtı"
    cmd: "python .agents/tasks/T-007/tester_A/mutant_kiti_A.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/mutant-A.txt
  - name: "A5 gerçek model (ayrı süreç): 4 dil × 2 cümle sonuç alanları, 6 kod biçimi aynı çıktı, beam 1/4, 50 segment tek batch, 13 keskinlik sondası"
    cmd: "python .agents/tasks/T-007/tester_A/a5_gercek_model.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/a5-gercek-model.txt
  - name: "A5b gerçek model: yalnız-yer-tutucu cümlesi sınıfı, 8 kalıp × (yer tutuculu / gerçek adlı) — keskinlik ölçümü"
    cmd: "python .agents/tasks/T-007/tester_A/a5b_yer_tutucu_cumlesi.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/a5b-yer-tutucu-cumlesi.txt
blocking_issues: []
---

# T-007 · Tester-A (mercek A: sözleşme uyumu, cümle bölme, dil/yer tutucu doğruluğu) · tur 1 · **ONAY**

Şefin tabanı birebir yeniden üretildi (mypy 0 · 210 passed · real_check TEMİZ 13/13 · tam takım 1314). Üstüne **265 kör test**, **30 + 1 mutant** ve **iki gerçek-model sondası** (ayrı süreç, bariyer dışı) koştu. **Sözleşmeyi ihlal eden ya da ürünü bozan ölçülmüş bir sınıf bulunmadı.** Bir keskinlik (K-1) ölçülüp sayıyla raporlandı; `known_gaps`'ta yok, yükümlülük olarak yazıldı. Depoya yazılmadı: `git status --short -- src tests` boş. `delivery.md` gövdesi okunmadı; yalnız ön bilgideki `known_gaps` listesi, testler bitip kanıtlar yazıldıktan SONRA §4 karşılaştırması için açıldı.

Kendi `conftest.py`'m bariyeri kendi başına kurar (`match="K1 bariyeri"`, `test_a0_bariyer_atesliyor` 4 nokta); şefin dizini ile birlikte koşunca da geçer (479). `TESTER_A_KOK` ortam değişkeni mutant kitine ayna kökü verir; MA-00 (kimlik sabiti) kopyanın gerçekten yüklendiğini kanıtlar.

## 1. Saldırı noktaları — ölçülen sonuç

| Nokta | Ölçü | Sonuç |
|---|---|---|
| **A1 · Bölme (K3)** | 30 satırlık tablo (`BOLME_TABLOSU`): `A. B.`, `A.B.`, `3.5 km.`, `Dr. Smith.`, `「A。」B。`, `A！？B`, `A.\n\nB.`, `...`, `？`, yalnız boşluk, boş, `A。」」』`, `A. )`, KR fixture (ASCII nokta), C8 JP paragrafı, yarım-genişlik JP `.`, ZWJ emoji, `A. . B`, `(A.) B.`, `A.」.B`, ideografik boşluk, U+FF0E, U+2026, `A. "B."`, `{0}. B.`, `{PLAYER}! Wait!`, `%s!`, `①.` — her satırda parça listesi, modele giden sayı, **kayıpsızlık** (`ham=True` birleşimi == kaynak), sağlayıcı üzerinden `T(...)` işaretli çıktı bileşimi (`" "` birleştirme, geçiş parçası yerinde, giden parça sayısı == `T(` sayısı); 4 dilde aynı bölme; 6 segmentli karışık istek tek çağrı + sıra; 300 rastgele karışımda kayıpsızlık; 5 patolojik girdide (200–300k karakter) regex < 2 s (ölçüldü 0.2–15 ms, doğrusal). | Hepsi paket K3 lafzıyla birebir. **Y1/Y2 pozitif kontrolleri gerçekten ateşliyor:** MA-01 (ASCII nokta yok) / MA-02 (v1 CJK kuralı) → `['A. B.']` satırında düşer; MA-03 (süzgeç yok) → `['...']`; MA-04 (rakam sayılmaz) → `['3.5 km.']`; MA-07 (kapanış dahil değil) → `「A。」B。`; MA-08 (boşluksuz birleştirme), MA-09 (geçiş segmenti boş), MA-10 (strip yok), MA-29 hepsi yakalandı. Test içi monkeypatch kontrolleri (AM1/AM2/AM8) aynı sonucu verir. |
| **A2 · Hizalama (K2)** | Sahte motor 9 sayı-uyuşmazlığı noktası: **2 segment 3+1 cümle → 3 VE 2 hipotez** (`ensure_aligned`'ın göremediği iki kayma), geçiş parçalı 3 segment (gönderilen 2 → 3 ve 1 döner), tek segment 2 cümle → 1/3, 0 hipotez, 3 segment → 2; bozuk biçim 7 nokta (`hypotheses=[]`, `None`, `str`, `.hypotheses` yok, token `int`, çıktı `str`/`None`); `hypotheses[0]==["tur_Latn"]`; hedef belirteci yoksa ilk token korunur; `ensure_aligned` **davranışsal** kayıt (dolu ve boş istekte, `request`/`result` kimlikleri `is`); `segments` liste gelince de hizalı. | Uyuşmazlık 9/9 `ContractViolation` (motor çağrıldı, sayım orada); bozuk biçim 7/7 `ProviderUnavailable`; boş istek `()` + `type is tuple` + fabrika 0. MA-05 (`ensure_aligned` yok) davranışsal ölçüyle, MA-06 (cümle sayımı yok) 3 hipotez/2 cümle noktasıyla, MA-21 (belirteç koşulsuz atılır), MA-27 (boş istekte liste) yakalandı. Kayıt: `["tur_Latn"]` hipotezi → o cümle `""`; 2 cümlelik segmentte çıktı `" "` (hizalı, ihlal değil; gerçek modelde 8 kısa girdide boş çıktı 0 — a5 [5m]). |
| **A3 · Dil kodları (K4)** | 4 dil × 3 biçim × **5 harf hâli** (aynen/upper/lower/title/swapcase) = 60 kod, her biri 5 cümlelik karışık istekte: **her satırda** ilk token NLLB kodu, son `</s>`, uzunluk 3, `target_prefix` 5×`["tur_Latn"]`, `detected_lang` == NLLB (str). Reddedilen 30 kaynak: `None`, `""`, `" ja "`, `"ja "`, `" ja"`, `"JA "`, `jpn`, `jp`, `zh-CN`, `zh_CN`, `ja-JP`, `tr`, `tur`, `tur_Latn`, `turkish`, `TR`, `auto`, `xx`, `japanese`, `kor`, `eng`, `en-US`, `jpn-Jpan`, `jpn_jpan_`, `b"ja"`, `5`, `0`, tuple/list/set. Hedef 20 kabul (4 × 5 hâl), 14 ret (`en`, `eng_Latn`, `ja`, `" tr"`, `"tr "`, `tr-TR`, `tr_TR`, `""`, `None`, `5`, `b"tr"`, `türkçe`, `turkce`). Sıra: dil hatası dosya denetiminden ÖNCE (boş dizin + `xx` → PU, + `ja` → MME); kapalı sağlayıcı; boş istekte `None`. 12 kod × aynı istek → token/çıktı/`detected_lang` özdeş. | Hepsi paketle birebir: tablo dışı ve `None` → `ProviderUnavailable`, fabrika 0; hedef `"en"` → `ProviderUnavailable`; `"tr"` kaynak olamaz; boşluk kırpılmaz (`" ja "` ret). MA-11 (harf duyarlı), MA-12 (ISO kodu yok), MA-13 (belirteç sonda), MA-14 (`target_prefix` tek satır), MA-15 (`detected_lang` None), MA-16 (`en` hedef kabul), MA-28 (`None` → JAPAN) 7/7 yakalandı; MA-99 (mesaj metni) kaçtı = ölçüler davranışa bağlı. **Gerçek model:** 4 dil × 6 kod → çıktı **aynı** (a5 [2], deterministik ön kontrol geçti). |
| **A4 · Yer tutucu (K5)** | Kaynakta 2×`{0}` / çıktıda 1× → **1 eklenir** (çıktıda 2); çıktıda 3× → **ekleme yok**; 13 satırlık sayım tablosu (`%s`×2 liste/tek liste, `<color=red>`/`</color>` düşen ve korunan, `{PLAYER}` düşen ve **büyük/küçük bozuk** (`{player}` → eklenir), `{{0}}`/`{0}` iç içe 3 sıra, `[Mill'de]` bozuk biçim, listede tekrar, kaynakta hiç yok, boş yer tutucu); `placeholders=()` → dokunulmaz; **cümle sınırında** `{0}. B.` / `C. {1}` / `D.` üç segment → `{0}.` kendi parçası olarak modele gider, onarım **kendi segmentine** eklenir, komşuya sızmaz; segment başına farklı liste; başka cümleye kayan yer tutucu segment düzeyinde sayılır; geçiş segmentinde (`<>`, `...`) motor kurulmadan onarım; `glossary_hits`+`tm_examples`+`style_profile`+`image_crops` DOLU istek → çıktı, motor çağrısı ve fabrika params **aynı** (AST: dört ad ne öznitelik ne dize sabiti). | Hepsi K5 (O1 sayım) lafzıyla birebir. MA-17 (`gereken=1`, yani `in`), MA-18 (koşulsuz ekleme), MA-19 (onarım yok), MA-20 (boş yer tutucu) 4/4 yakalandı. Kayıt: iç içe `{{0}}`+`{0}` ikisi de eksikken sayım ÖZGÜN çıktıya karşı yapılır → `{{0}}` eklenince `{0}` sağlanmış olsa da ayrıca eklenir (`t {{0}} {0}`) — zararsız, belgelenmemiş. |
| **A5 · Gerçek model** (ayrı süreç) | a5: 4 dil × 2 cümle (ZH dahil) `TranslationResult` 10 alan koşulu; 6 kod biçimi aynı çıktı; beam=1 vs 4; 50 segment tek batch × 3; ilk çağrı; 13 keskinlik sondası. a5b: 8 kalıp yalnız-yer-tutucu cümlesi. | **Sözleşme:** `translations` tuple/str/boş değil/hizalı, `provider_id` beklenen sabitle eşit, `latency_ms` `type is float` ≥ 0, `from_cache`/`partial` `False`, `detected_lang` NLLB kodu — 4/4 dil. **beam=1 vs 4:** 8 cümlenin **6'sı farklı**; tek cümle latency medyan 147 vs 190 ms (rapor). **50 segment tek batch:** hizalı, latency medyan 2.85–2.88 s (≈57 ms/cümle), **duvar saati − `latency_ms` ≤ 0.02 ms** (tutarlı); ilk çağrı duvar 865 ms / `latency_ms` 295 ms (kurulum hariç, K9). Keskinlik ölçümleri §2. |
| **A6 · Sayısal/tip** | `latency_ms` 4 istek tipinde `type is float`; `threads` ∈ {`np.int64(8)`, `np.int32(4)`, `np.uint8(2)`, 1, 8} → `type(p.threads) is int`, `intra_threads` `int`, `inter_threads` 1; `True/False/8.0/np.float64/np.float32/np.bool_/"8"/4.5/[8]/np.array(8)` → `TypeError`; `0/-1/np.int64(0)/np.int64(9999)/2**63/-(2**63)` → `ValueError`; `beam_size` `0/-1/np.int64(0)/np.int32(-5)` → `ValueError`, `True/4.0/np.float64/"4"/None` → `TypeError`, `np.int32(2)/np.int64(4)/1/7` → motora düz `int`, `max_decoding_length` 256; `repetition_penalty` `nan/inf/-inf/0.99/0.0/-1.0/np.float64(nan)/np.float32(0.5)` → `ValueError`, `True/False/"1.2"/None/[1.2]/complex` → `TypeError`, `1/1.0/np.float64(1.0)/np.int64(1)` → **hiç geçilmez**, `1.2/2/np.float32(1.5)/np.float64(1.1)` → `float` olarak gider; yapım hatası fabrikaya/dosya sistemine dokunmaz. | Hepsi geçti. MA-22 (`np.int64` düzleştirilmez), MA-23 (`beam_size=0`), MA-24 (`nan`), MA-25 (1.0 iken de geçilir), MA-26 (latency `int`) 5/5 yakalandı. Kayıt: `np.float32(1.2)` → `1.2000000476837158` geçer (float32 → float dönüşümü; zararsız). |

## 2. Keskinlikler — ölçüldü, ret eşiğini geçmiyor, `known_gaps` yükümlülüğü

**K-1 · Yalnız yer tutucudan oluşan cümle modele gider ve model uydurur (Y2'nin kalıntısı).** Y2 süzgeci `str.isalnum` arar; `{PLAYER}!`, `{0}!`, `{0}。` parçaları yer tutucunun İÇİNDEKİ harf/rakam yüzünden modele gider. Gerçek model, a5 [5b]: `{PLAYER}! Wait!` → çıktı 38 karakter = `{PLAYER}!` tek başına **24 karakter uydurma** (KRT Y2'nin ölçtüğü "hayır" kalıbı içeriyor) + `Wait!` tek başına 13; `{0}!` → 19 karakter uydurma; `{0}。` (JP) → 19; `{0}. Take the road.` (5a), terminatörsüz `{0}` (5b5) ve `%s!` (5b6) uydurmuyor. a5b, 8 kalıp (EN 5, JP 2, KR 1; vokatif + terminatör): yer tutuculu **5/8 uydurma**, aynı kalıplar gerçek adla (`Marcus!`) **2/8** (ikisi JP: tek-kelimelik ad cümlesi de uyduruyor — bu kısım modelin kendisi, sağlayıcıda çözümü yok). Yer tutucu onarımla her seferinde çıktıda var (`yt_var=True` 8/8) — K5 tutuyor; sorun uydurulan cümlenin de çıktıda olması. **Paketle uyumlu** (Y2 lafzı harf/rakam), sözleşme ihlali değil; ama vokatif yer tutucu (`{0}! …`) oyun diyaloğunda yaygın ve Y2 ile aynı hata sınıfı. `known_gaps`'ta **yok** (`Dr. Smith`/`3.5`/`v1.2.3`/`what?No` var). **Yükümlülük:** docstring + `known_gaps`'a yazılmalı. **Öneri (şef kararı, tur 2'ye taşınabilir):** süzgeç, parçadan `segment.placeholders` dizeleri çıkarıldıktan sonra uygulanır (`modele_gider(parca_yer_tutucusuz)`) → `{PLAYER}!` aynen geçer, çıktı `{PLAYER}! <çeviri>`; tek satır, `test_a1_bolme_tablosu` `{0}. B.`/`{PLAYER}! Wait!` satırları ve `test_a4_cumle_sinirinda_*` **bayatlar** (§4.6/5), a5b 5/8 → beklenen 0/8 ölçüsü hazır. Gerçek adlı 2/8 Katman 0/2'nin işi.

**K-2 · ASCII tırnak simetrik: `A. "B."` → açılış tırnağı ÖNCEKİ cümleye yapışır.** `_KAPANIS_ISARETLERI` `"` ve `'` içeriyor ve "arada boşluk olsa da" kuralı var → `['A. "', 'B."']`. Gerçek model a5 [5l]: `A. "` → çıktı 1 tırnak, **sonda**; `B."` → 1 tırnak, ne başta ne sonda (**cümle ortasına** düşüyor); doğru `"B."` → 2 tırnak, başta. Tırnak sayısı korunuyor (a5 [5d] 2/2), uydurma yok, uzunluk 32 vs doğru bölünmüş 30. Kayıpsızlık tutuyor. `known_gaps` "boşluklu kapanış önceki cümleye ait" kararını yazıyor ama simetrik ASCII tırnağın sonucunu (açılış tırnağı yanlış cümlede) anmıyor. **Yükümlülük:** belgelenmeli; çözüm (`"`/`'` yalnız boşluksuz ise kapanış say) K-1 ile birlikte kalite görevine.

**K-3 · Tam genişlik nokta U+FF0E (`．`) terminatör değil.** Paket kümesi `.!?。！？`; JP OCR/oyun metni `．` de verebilir. a5 [5i]/[5k]: 2 JP cümle `．` ile tek parça; **bu örnekte** model yine 2 cümle + iki anahtar üretti (kaynaşma görülmedi), yani ölçülmüş zarar yok. `known_gaps` U+2026'yı anıyor, U+FF0E'yi anmıyor. Kayıt; küme genişletilirse `test_a1_bolme_tablosu['A．B．']` bayatlar.

**K-4 · Kayıtlar (yükümlülük değil):** (a) `hypotheses[0]==["tur_Latn"]` → `""`/`" "` çıktı (hizalı; gerçek modelde görülmedi). (b) `{{0}}`/`{0}` sayımı özgün çıktıya karşı (fazladan bir `{0}` ekler). (c) `np.float32(1.2)` → `1.2000000476837158`. (d) `A. . B` → yalnız `.` parçası geçer (`A. . B` aynen). (e) `"%s!"` modele gider (`s` harf) — gerçek model aynen geri verdi (3 karakter).

## 3. Sözleşme uyumu — satır satır

- `TranslationProvider` alt sınıfı; `provider_id` kararlı str; `translate(request) -> TranslationResult`; `ensure_aligned` **her** dönüşten önce davranışsal olarak çağrılıyor (dolu/boş istek), `translations` her yolda `tuple[str, ...]` ve `len == len(segments)`.
- Hata taksonomisi düz: `ProviderUnavailable` (dil/kapalı/motor/biçim), `ContractViolation` (sayı/tip), `ModelMissingError` (dosya). `ProviderTimeout` fırlatılmıyor — paket `[ÖLÇÜLMÜYOR]`.
- `latency_ms` float, kurulum hariç (gerçek: 865 → 295 ms); `from_cache`/`partial` False; `detected_lang` kullanılan NLLB kodu.
- `glossary_hits`/`tm_examples`/`style_profile`/`image_crops` kabul edilir, okunmaz (davranış + AST).

## 4. `known_gaps` karşılaştırması (testler bitince açıldı)

Ön bilgideki K3/K4/K5/K8/K10 kararları (boşluklu kapanış, `…`/`\n`, boşluk kırpılmaz, `str` olmayan kod → PU, boş istekte doğrulama, sayım vs `in`, `< 1.0`/`nan` → `ValueError`, boş istekte fabrika çağrılmaz) ölçtüklerimle **birebir örtüşüyor**. Eksik: **K-1** (yalnız-yer-tutucu cümlesi) ve **K-2** (simetrik ASCII tırnak) — ikisi de yukarıda yükümlülük.

## 5. Dosyalar

- `.agents/tasks/T-007/tester_A/conftest.py` — kendi K1 bariyeri (`K1 bariyeri` deseni), `sys.path`, `TESTER_A_KOK`.
- `.agents/tasks/T-007/tester_A/test_mercek_a.py` — 265 test (A0 6 · A1 65 · A2 23 · A3 81 · A4 22 · A6 58 · AM 10 monkeypatch pozitif kontrolü).
- `.agents/tasks/T-007/tester_A/mutant_kiti_A.py` — 30 mutant + 1 kontrol, ayna kökte.
- `.agents/tasks/T-007/tester_A/a5_gercek_model.py`, `a5b_yer_tutucu_cumlesi.py` — gerçek model, ayrı süreç, stdout yalnız ASCII sayı/boolean; çeviri metni basılmaz.
- `.agents/tasks/T-007/tester_A_evidence/` — 10 kanıt dosyası, hepsi dolu.
- Yazılmayanlar: `src/`, `tests/`, `conftest.py` (şefin), `real_check.py`, `packet.md`, `fixtures/`. `git commit` yok.
