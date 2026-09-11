---
task: T-007
role: implementer
round: 2
status: tamamlandi
files_written:
  - src/translate/local_nmt.py
  - tests/unit/translate/test_local_nmt.py
  - .agents/tasks/T-007/delivery.md
  - .agents/tasks/T-007/evidence/mypy-tur2.txt
  - .agents/tasks/T-007/evidence/pytest-tur2.txt
  - .agents/tasks/T-007/evidence/real_check-tur2.txt
  - .agents/tasks/T-007/evidence/cov-tur2.txt
  - .agents/tasks/T-007/evidence/pytest-tum-tur2.txt
  - .agents/tasks/T-007/evidence/mypy-test-dosyasi-tur2.txt
  - .agents/tasks/T-007/evidence/pytest-cp1254-tur2.txt
  - .agents/tasks/T-007/evidence/tdd-kirmizi-tur2.txt
  - .agents/tasks/T-007/evidence/mutant-kiti-tur2.py
  - .agents/tasks/T-007/evidence/mutant-ayirt-etme-tur2.txt
  - .agents/tasks/T-007/evidence/olcum-4-yer-tutucu-ve-terminator-gercek-model.py
  - .agents/tasks/T-007/evidence/olcum-4-yer-tutucu-ve-terminator-gercek-model.txt
commands:
  - cmd: "python -m mypy --strict --explicit-package-bases src/translate/local_nmt.py"
    exit_code: 0
    evidence: evidence/mypy-tur2.txt
  - cmd: "python -m pytest tests/unit/translate/test_local_nmt.py -q"
    exit_code: 0
    evidence: evidence/pytest-tur2.txt
  - cmd: "python .agents/tasks/T-007/real_check.py"
    exit_code: 0
    evidence: evidence/real_check-tur2.txt
  - cmd: "python -m pytest tests/unit/translate/test_local_nmt.py -q --cov=src.translate.local_nmt --cov-fail-under=90 --cov-report=term-missing"
    exit_code: 0
    evidence: evidence/cov-tur2.txt
  - cmd: "python -m pytest tests -q"
    exit_code: 0
    evidence: evidence/pytest-tum-tur2.txt
  - cmd: "python .agents/tasks/T-007/evidence/mutant-kiti-tur2.py  (T007_AYNA=<scratchpad>/ayna-tur2)"
    exit_code: 0
    evidence: evidence/mutant-ayirt-etme-tur2.txt
  - cmd: "python .agents/tasks/T-007/evidence/olcum-4-yer-tutucu-ve-terminator-gercek-model.py"
    exit_code: 0
    evidence: evidence/olcum-4-yer-tutucu-ve-terminator-gercek-model.txt
  - cmd: "python -m mypy --strict --explicit-package-bases tests/unit/translate/test_local_nmt.py"
    exit_code: 0
    evidence: evidence/mypy-test-dosyasi-tur2.txt
  - cmd: "python -m pytest tests/unit/translate/test_local_nmt.py -q -p no:cacheprovider  (PYTHONIOENCODING YOK, stdout cp1254)"
    exit_code: 0
    evidence: evidence/pytest-cp1254-tur2.txt
  - cmd: "python -m pytest tests/unit/translate/test_local_nmt.py -q -p no:cacheprovider --no-header -rf  (TDD KIRMIZI: testler yazildi, src henuz degismedi -- 16 failed, hepsi T2-2)"
    exit_code: 1
    evidence: evidence/tdd-kirmizi-tur2.txt
contract_change_request: false
known_gaps:
  - "[TUR 2 OZETI] Sef karari tur 2: T2-1 (bloke, olcu), T2-2 (urun-gorunur, src), T2-3 (keskinlik, olcu). Tek `src` davranis degisikligi T2-2: `modele_gider(parca, yer_tutucular=())` -- karar `Segment.placeholders` dizeleri parcadan CIKARILDIKTAN SONRA verilir; `translate` icindeki tek cagri `modele_gider(parca, segment.placeholders)`. Docstring K3/K6/K10 guncellendi. Birim 210 -> 255 (+45), tam takim 1314 -> 1359 (+45), dusen YOK. Tur 1 test dosyasi (`git show HEAD:tests/unit/translate/test_local_nmt.py`, 1466 satir) yeni src'de 210/210 GECIYOR (`mutant-ayirt-etme-tur2.txt` temel satiri) -- yani TESLIM dosyasinda bayatlayan test yok; Tester-A'nin verdict'te adlandirdigi bayatlayan testler (`test_a1_bolme_tablosu[{0}. B.]`, `[{PLAYER}! Wait!]`, `test_a4_cumle_sinirinda_*`) A'nin kendi dizininde (`tester_A/`, bana YASAK) -- sef kararindaki gibi sef regresyon olarak kosar ve o kiriklari bekler. Ayni davranislar teslim dosyasinda yeni kurala gore YENIDEN NISANLANDI: `test_k3e_yer_tutucu_cikarildiktan_sonra_suzgec_tablosu[vokatif+cumle]` (`{PLAYER}! Wait!` -> yalniz `Wait!` gider), `[sinirda-nokta]` (`{0}. B.` -> yalniz `B.`), `test_k3e_yer_tutucu_cumle_sinirinda_uc_segment_kendi_segmentinde_kalir` (`{0}. B.` / `C. {1}` / `D.`: gidenler `B.`,`C.`,`D.`; yer tutucu kendi segmentinde yerinde). `git commit` ATILMADI."
  - "[T2-1 -- K3 TERMINATOR KUMESI ALTI NOKTADA AYRI OLCULUYOR] Degismez ayni (`.!?。！？` her biri tek basina cumle sonu). Yeni olcu: `TERMINATORLER` sabiti test dosyasinda paket K3 metninden BAGIMSIZ yazildi (saglayicidan turetilmez); `test_k3b_her_terminator_tek_basina_boler[U+XXXX]` (6 nokta: `A{t} B{t}` -> 2, `A{t}B{t} C{t}` -> 3), `test_k3b_terminator_diger_isaretler_yokken_harfli_kuyrugu_ayirir[U+XXXX]` (6 nokta, tek-isaretli fixture `A{t} B` -> 2, uc dilde; `{t}A` -> 2; `t` tek basina gecis parcasi), `test_k3b_bolme_*` listesine `A? B.` ve `A！B。` (feedback-B (a)), negatif kontrol `test_k3b_terminator_olmayan_isaret_bolmez_negatif_kontrol` (`,` `;` `:` `…` `、` `，` bolmez -- kumenin siniri). AYIRT ETME (kendim olctum, `mutant-kiti-tur2.py` -> `mutant-ayirt-etme-tur2.txt`, ayna agaci, iki test dosyasi): K3-01..06 (her isaret ayri cikarilmis) tur 2 dosyasi 6/6 yakaliyor (16/9/4/15/3/4 test); tur 1 dosyasi K3-03 (`?`) ve K3-05 (`！`) icin `.` (210 passed, KACIRIYOR) -- feedback-B'nin bulgusu birebir yeniden uretildi; C-3 (kume ayni, sira farkli) iki dosyada da kaciyor. GERCEK MODEL (olcum-4 [B]): `Are you ready? The village elder...` -> 2 parca gidiyor, 'hazır'+'bekliyor' VAR; JP `止まれ！村の長老...` -> 2 parca, 'dur'+'bekliyor' VAR; JP `待って！本当に行くの？` -> 2 parca (feedback-B gibi yalniz sayi; ilk kosumda uydurdugum 'bekle' anahtari tutmadi, kaldirdim -- kalite altin setsiz olculmez). `real_check.py` sefe ait; oraya `?`/`！` pozitif kontrolu sefin karari (feedback-B §3 son satir)."
  - "[T2-2 -- YALNIZ YER TUTUCU PARCASI MODELE GITMEZ] `modele_gider(parca, yer_tutucular=())`: her bildirilen dize parcadan tum gecisleriyle cikarilir (bos dize yok sayilir), kalan harf/rakam icermiyorsa parca gecis parcasidir. `{PLAYER}!` (`placeholders=(\"{PLAYER}\",)`) -> motora giden 0, motor KURULMAZ (fabrika 0), cikti `\"{PLAYER}!\"` aynen; `{PLAYER} is here.` -> gider (pozitif kontrol); `placeholders=()` iken `{PLAYER}!` -> GIDER (bildirilmemis yer tutucu METINDIR; yer tutucu bilgisi yalniz `Segment.placeholders`tan). Olcu: `test_k3e_*` (11 test + 12 satirlik tablo: `{0}!`, `{0}。`, `%s!`, `{0} {1}!`, `{0}{1}`, `{0}! {1}?` (iki gecis parcasi -> segment aynen), `<T0>!`, `[Marcus]!`, `{0}! Go {1}.` (yalniz `{1}` bildirildi -> `{0}!` gider), `{0}5!` (rakam kalir -> gider)); `test_k3e_yer_tutucu_onarimi_gecis_parcasiyla_cakismaz` (gecis parcasindaki yer tutucu K5 sayimina girer: model dusurse de eklenmez; kaynakta 2 gecis + biri dustu -> 1 eklenir); `test_k3e_modele_giden_her_parcada_yer_tutucu_disinda_harf_veya_rakam_var` (toplu degismez). Mutantlar: T2-2-M1 (suzgec yer tutuculari gormuyor = tur 1) 15 test, T2-2-M2 (yalniz ilk gecis cikariliyor) 1 test, T2-2-M3 (yalniz-yer-tutucu segment bos) 9 test -> tur 2 3/3 yakaladi, tur 1 dosyasi 3/3 kor (beklenen: o davranis tur 1'in kendisi). GERCEK MODEL (olcum-4 [A], fabrika sarmalanip giden parca sayildi): `{PLAYER}!` EN, `{0}!` EN/KR, `{0}。` JP, `%s!` -> giden 0, cikti == kaynak (aynen=True), 'hayır' kalibi YOK 5/5; `{PLAYER}! Wait!` -> giden 1, cikti `{PLAYER}! ` + 13 karakter (yalniz `Wait!` cevirisi), uydurma yok; `{PLAYER} is here.` -> giden 1; `placeholders=()` iken `{PLAYER}!` -> giden 1 ve model UYDURUYOR (hayir_kalibi=True) -- bu Tester-A K-1'in olctugu tur 1 davranisi, artik yalniz BILDIRILMEMIS yer tutucuda kalir ve tasarim geregi (normalizer/Katman 0 bildirir) [ÖLÇÜLMÜYOR] kalite. KARAR (sef sessizdi): cikarma `str.replace` ile TUM gecisler (ic ice `{{0}}`/`{0}` -> `{}` kalir, gecis parcasi olur -- belgeli, zararsiz)."
  - "[T2-3 -- KESKINLIK] (1) `test_k6_hata_mesajlari_kaynak_metni_tasimaz`: ikinci nobetci `MOTOR_NOBETCISI` motor CIKTISINDA / bozuk motor nesnesinin repr'inde / hipotez tokenlerinde / decode'un dondurdugu nesnede (5 yeni satir: `sayi-nobetcili-cikti`, `bozuk-nesne-nobetcili`, `bos-hipotez-nobetcili-nesne`, `int-token-nobetcili-hipotez`, `decode-tip-nobetcili-nesne`); iki nobetci de ne `str` ne `repr` icinde; pozitif kontrol `test_k6_motor_ciktisi_nobetcisi_gercekten_motora_ulasiyor_pozitif_kontrol` (saglam bicimde nobetci ceviriye ULASIYOR -> nobetci yolun icinde). Mutantlar K10-08 (`{cikti!r}`), K10-09 (`{nesne!r}`), K10-10 (`{tokenler!r}`), K10-11 (`{metinler!r}`) -> tur 2 4/4 yakaladi (1/2/1/1 test), tur 1 dosyasi 4/4 kor (feedback-B'nin K10-08/09 bulgusu yeniden uretildi + iki yeni yol). (2) `test_k10_pozitif_kontrol_kanal_olcusu_atesliyor` 7 satir `match=`: stdout / os.write(1) -> \"stdout'a\", stderr / sys.__stderr__ -> \"stderr'e\", iki logger -> \"log kaydina\", warnings -> \"warnings kaydina\" -- 7/7 dogru sebeple dusuyor (255 passed)."
  - "[K3 -- BOLME NOKTALAMAYA GORE, SUZGEC, TEK BATCH] Kural: `[^T]*[T]+(?:\\s*[K]+)*|[^T]+\\Z` (T=`.!?。！？`, K=`」』）)\"'”’»`), bosluk sarti YOK; kirpilmis bos olmayan parcalar. Harf/rakam icermeyen parca (yer tutucular cikarildiktan sonra, T2-2) modele gitmez, ciktida yerinde aynen; hicbir parcasi gitmeyen segment KAYNAK METNIN AYNISI (`\"\"`, `\"   \"`, `\"。。。\"`, `\"{PLAYER}!\"`); gonderilecek parca yoksa fabrika bile cagrilmaz. Tum segmentlerin parcalari TEK `translate_batch`; segment ciktisi `\" \"` ile birlesir. Olcu: `test_k3a_*`, `test_k3b_*` (14 metin x 3 dil + 6x2 terminator + 6 negatif), `test_k3c_*`, `test_k3d_*`, `test_k3e_*`, 500 cumle tek batch. Gercek model: `real_check` #3/#4/#4b; olcum-2 [E]; olcum-4 [A]/[B]. KARAR (paket sessizdi): terminator ile kapanis isareti arasinda bosluk olsa da isaret ONCEKI cumleye ait (`A。 」 B。` -> `A。 」` + `B。`); `…` (U+2026) ve tam genislik nokta `．` (U+FF0E, Tester-A K-3 -- `．` JP OCR'da gorulebilir, kume genisletilirse A'nin `A．B．` satiri bayatlar; sef karari) terminator DEGIL; `\\n` terminator degil. SIMETRIK ASCII TIRNAK (Tester-A K-2): `\"`/`'` kapanis kumesinde oldugu icin `A. \"B.\"` -> `A. \"` + `B.\"` -- acilis tirnagi ONCEKI cumleye yapisir; kayipsiz, uydurma yok, gercek modelde tirnak sayisi korunuyor ama ikinci cumlede tirnak ortaya dusuyor [ÖLÇÜLMÜYOR] kalite (cozum: `\"`/`'` yalniz bosluksuzken kapanis say -- kalite gorevine). [ÖLÇÜLMÜYOR] kalite: `Dr. Smith`, `3.5`, `v1.2.3`, `what?No` bolunur -- testte SABITLENDI."
  - "[K3 ITIRAZ DEGIL, NOT -- bosluk sarti] KRT Y1 duzeltmesi ASCII terminator icin 'ardindan bosluk/sonu' sartini oneriyordu; paket v2 K3 metni evrensel kumeyi sartsiz yazdi ve `3.5`i bilinen zayiflik olarak listeledi. Pakete uydum (sartsiz). Iki secenegin de kaybi var: sartli kural `3.5`/`v1.2`/URL'yi korur ama JP/KR OCR'in bosluksuz yarim-genislik noktasini (`はい.そうです.`) bolmez; sartsiz kural tersi. Hangisinin urunu daha az bozdugu altin set olmadan olculemez -- kalite gorevine not."
  - "[K4 -- UC BICIMLI TABLO] 4 dil x 3 bicim x buyuk/kucuk = 24 nokta (`test_k4_uc_bicim_*`): ilk token NLLB kodu, son `</s>`, `target_prefix` her satirda `[\"tur_Latn\"]`, `detected_lang` == NLLB kodu. Reddedilen kaynak: `None`, `xx`, `tr`, `tur_Latn`, `jpn`, `\"\"`, `ja-JP`, `\" ja\"` -> `ProviderUnavailable`, fabrika 0. Hedef 4 bicim + buyuk harf kabul; `tr-TR`, `tr_TR`, `en`, `eng_Latn`, `\"\"`, `turkce`, `None`, `5` -> `ProviderUnavailable`. KARAR (paket sessizdi): bosluk KIRPILMAZ (`\" ja\"` red), `str` olmayan kod `ProviderUnavailable` (`AttributeError` degil), dogrulama BOS istekte de yapilir, Turkce kaynak olamaz. Mutant M-13, M-18 yakalandi (tur 2'de de). Gercek: `real_check` #8."
  - "[K5 -- SAPMA, O1'E UYULDU: SAYIM, `in` DEGIL] Paket K5 lafzi 'tam alt dize olarak aranir; eksikse sona eklenir'; sef O1'i kabul etmis ama K5 metni `in` kaldi. Uygulama: gereken = `max(1, kaynak_metin.count(yt))`, mevcut = `cikti.count(yt)`, fark kadar sona (listedeki sirayla, boslukla; ayni dize bir kez islenir). NOT (tur 2'de gorundu): `max(1, ...)` bildirilen ama KAYNAKTA OLMAYAN yer tutucuyu da ekler (`{PLAYER}!` + `placeholders=(\"{0}\",)` -> `... {0}`) -- tur 1 davranisi, testerlar onayladi, degistirilmedi; T2-2 fixture'lari kaynakta var olan yer tutucuyla kuruldu. Gecis parcasindaki yer tutucu (T2-2) sayima girer: model dusurse de segmentte var -> eklenmez. Mutant M-05, M-06 yakalandi. Bozuk bicim (`[Mill'de]`) tam alt dize degil -> eklenir [ÖLÇÜLMÜYOR]. AST: `glossary_hits`/`tm_examples`/`style_profile`/`image_crops` modulde gecmez; dolu istek == duz istek. Gercek: `real_check` #5."
  - "[K6 -- DORT DOSYA, VARLIK DENETIMI; sifir bayt -> ProviderUnavailable] `is_file()` ile dort ad; eksik olan(lar) mesajda. Boyut denetlenmez (paketin olcusu 'bos dosyalar konunca fabrika cagrilir'); gercek modelde sifir baytlik `model.bin` -> `ProviderUnavailable` (`__cause__` RuntimeError), bos proto encode'da `ProviderUnavailable` (olcum-2 [B]/[C]). Fabrika `FileNotFoundError` -> `ModelMissingError` (paket K6(b) lafzindan SERT -- feedback-B (e): sefin karara yazmasi gereken sapma; K6-06 mutanti birim kapisinda dusuyor, olcu var); `TranslatorError` sarilmaz; baska `Exception` -> `ProviderUnavailable`. Motor ciktisi 9 bozuk bicim -> `ProviderUnavailable`; sayi uyusmazligi -> `ContractViolation`. Hata mesaji 12 yolda iki nobetciyi (kaynak + motor ciktisi, T2-3) tasimaz."
  - "[K7 -- BAYT ILE ACMA] `_varsayilan_fabrika`: `SentencePieceProcessor(model_proto=...read_bytes())`, `Translator(str(model_dir.resolve()), **params)`. AST: `model_proto=` var, `model_file=` yok. Gercek: olcum-1 [1]; `real_check` #7 (tur 2'de yine ok)."
  - "[K8 -- IPLIK, CEZA, ISIN] `params` tam olarak `{device: cpu, compute_type: int8, inter_threads: 1, intra_threads: threads}`. `threads` [1, cpu_count], `None` -> min(8, cpu). `repetition_penalty=1.0` iken `translate_batch` kwargs `{}`; `< 1.0`/`nan`/`inf` -> `ValueError`; `beam_size` 4 varsayilan, 0/-1 `ValueError`. `max_decoding_length=256` acik. Degismedi; mutant M-07/M-08/M-16 tur 2'de de yakalandi."
  - "[K9 -- LATENCY KURULUM HARIC; 311 ms] Degismedi. `real_check` #6 tur 2: medyan 311 ms (esik 350, uyari yok); [1] ilk cagri `latency_ms=333` (kurulum degil, ilk cikarimin soguk maliyeti; butce isinma sonrasi medyan). `ProviderTimeout` firlatilmaz [ÖLÇÜLMÜYOR]."
  - "[K10 -- TEMBEL, TEK ORNEK, KAPATMA, KANAL] Degismedi (M-10/M-11/M-12/M-20 tur 2'de de yakalandi). Kanal olcusu 3 nokta + 7 pozitif kontrol (T2-3: `match=` ile kanala ozgu mesaj) + 1 negatif. Gercek: olcum-2 [A] 0 bayt. cp1254 konsolda 255 passed (`pytest-cp1254-tur2.txt`; yeni test id'lerinde ASCII-disi var, pytest kacisliyor)."
  - "[K1 / K2 -- DEGISMEDI] Test dosyasi kutuphane import etmez; her `model_dir` `tmp_path`; K1 bariyeri altinda 255 passed. `ensure_aligned` `translate` govdesinde (M-04 yakalandi); cumle sayimi (M-03 yakalandi)."
  - "[AYIRT ETME TUR 2 -- `evidence/mutant-kiti-tur2.py` -> `mutant-ayirt-etme-tur2.txt`] Ayna agaci (scratchpad), IKI test dosyasi: tur 2 (255) ve tur 1 (`git show HEAD:...`, 210). Temel: ikisi de yeni src'de yesil. 13 yeni mutant (K3-01..06, T2-2-M1..M3, K10-08..11) tur 2 dosyasi 13/13 yakaladi; tur 1 dosyasi K3-03 (`?`), K3-05 (`！`), T2-2-M1..M3, K10-08..11 icin KOR (9/13 kacti -- beklenen, bu turun kapattigi bosluklar), K3-01/02/04/06 icin yakaladi (feedback-B tablosuyla birebir: 11/3/13/2). 22 tur-1 mutanti (M-01..M-22; M-02 hedef satiri T2-2 ile degistigi icin `M-02'` olarak uyarlandi) iki dosyada da 22/22 yakalandi (regresyon yok). 5 davranis-esdeger kontrol (C-1 `split/join`, C-2 liste, C-3 kume sirasi, C-4 `1e3`, C-5 close sirasi) iki dosyada da 5/5 kacti (yanlis pozitif yok). TDD kirmizi: `tdd-kirmizi-tur2.txt` (16 failed / 239 passed -- 16'sinin hepsi T2-2 `test_k3e_*`; T2-1 ve T2-3 testleri dogru kodda zaten yesil, onlarin kirmizisi mutant kitidir)."
  - "KAPSAM DISI (bloke etmeyen, tur 1 ile ayni): thread-safe degil; `unload_model()` cagrilmiyor; CT2 C++ log seviyesi degistirilmiyor; `max_input_length` gecilmiyor; kalite altin setsiz [ÖLÇÜLMÜYOR]; `git commit` ATILMADI; `pip install` YAPILMADI; sefe ait dosyalara (conftest, test_conftest_bariyer, real_check, fixtures, packet, sef_karari-*, sef_dogrulama/, tester_A/, tester_B/, *_evidence/) DOKUNULMADI ve tester dizinleri OKUNMADI (yalniz verdict-A.md, feedback-B.md)."
---

# T-007 teslim -- tur 2

## Ne degisti

* `src/translate/local_nmt.py` -- **tek davranis degisikligi (T2-2):** `modele_gider(parca, yer_tutucular=())`
  karari `Segment.placeholders` dizeleri cikarildiktan sonra verir; `translate` icindeki cagri
  `modele_gider(parca, segment.placeholders)`. Docstring K3 (T2-1 alti nokta, T2-2 kural, A'nin K-2/K-3
  kayitlari), K6 (iki nobetci), K10 (`match=`) ve `translate` sira satiri guncellendi. Baska satir degismedi.
* `tests/unit/translate/test_local_nmt.py` -- 210 -> **255 test** (+45):
  * **T2-1:** `TERMINATORLER` bagimsiz sabit; `test_k3b_her_terminator_tek_basina_boler[U+XXXX]` (6),
    `test_k3b_terminator_diger_isaretler_yokken_harfli_kuyrugu_ayirir[U+XXXX]` (6), `test_k3b_bolme_*`
    listesine `A? B.` / `A！B。` (2), negatif kontrol 6 isaret (6).
  * **T2-2:** `test_k3e_*` 11 test (+ 12 satirlik tablo): yalniz-yer-tutucu parcasi gitmez / yaninda metin
    varsa gider / bildirilmemisse gider / uc segment cumle sinirinda / onarimla cakismaz / yardimci / toplu.
  * **T2-3:** `test_k6_hata_mesajlari_kaynak_metni_tasimaz` +5 motor-ciktisi-nobetcili satir + 1 pozitif
    kontrol; `test_k10_pozitif_kontrol_kanal_olcusu_atesliyor` 7 satir `match=`.
  * Var olan hicbir test silinmedi ya da zayiflatilmadi.

## Bes komut (tur 2)

| # | komut | exit | sonuc | kanit |
|---|---|---|---|---|
| 1 | mypy --strict | 0 | temiz | `evidence/mypy-tur2.txt` |
| 2 | pytest birim | 0 | **255 passed** | `evidence/pytest-tur2.txt` |
| 3 | real_check.py | 0 | 13/13 ok, TEMIZ, 0 uyari; #6 medyan 311 ms | `evidence/real_check-tur2.txt` |
| 4 | coverage >= 90 | 0 | %100 (243 ifade, 0 eksik) | `evidence/cov-tur2.txt` |
| 5 | pytest tum takim | 0 | **1359 passed** (1314 + 45), dusen yok | `evidence/pytest-tum-tur2.txt` |

Ek: mutant kiti tur 2 (35/35 yakalandi, 5/5 kontrol kacti), gercek model olcum-4 TEMIZ,
test dosyasi mypy temiz, cp1254 255 passed, TDD kirmizi 16 failed (hepsi T2-2).

## Ayirt etme tablosu (ayna agaci, `mutant-ayirt-etme-tur2.txt`)

| mutant | tur 2 dosyasi (255) | tur 1 dosyasi (210, HEAD) |
|---|---|---|
| K3-01 `.` eksik | X (16) | X (11) |
| K3-02 `!` eksik | X (9) | X (3) |
| **K3-03 `?` eksik** | **X (4)** | **. (kacti)** |
| K3-04 `。` eksik | X (15) | X (13) |
| **K3-05 `！` eksik** | **X (3)** | **. (kacti)** |
| K3-06 `？` eksik | X (4) | X (2) |
| T2-2-M1 suzgec yer tutucuyu gormuyor (tur 1) | X (15) | . |
| T2-2-M2 yalniz ilk gecis cikariliyor | X (1) | . |
| T2-2-M3 yalniz-yer-tutucu segment bos | X (9) | . |
| K10-08 `{cikti!r}` mesajda | X (1) | . |
| K10-09 `{nesne!r}` mesajda | X (2) | . |
| K10-10 `{tokenler!r}` mesajda | X (1) | . |
| K10-11 `{metinler!r}` mesajda | X (1) | . |
| M-01..M-22 (tur 1 kiti, regresyon) | 22/22 X | 22/22 X |
| C-1..C-5 (davranis-esdeger) | 5/5 . | 5/5 . |

## Gercek model (olcum-4, ayri surec, yalniz sayi/boolean)

* [A] `{PLAYER}!`, `{0}!` (EN/KR), `{0}。` (JP), `%s!` -> giden **0**, cikti == kaynak, 'hayır' kalibi yok (5/5);
  `{PLAYER}! Wait!` -> giden 1, `{PLAYER}! ` + 13 karakter; `{PLAYER} is here.` -> giden 1;
  `placeholders=()` iken `{PLAYER}!` -> giden 1 ve model uyduruyor (bildirilmemis yer tutucu = metin; belgeli).
* [B] `Are you ready? The village elder...` -> 2 parca, hazır+bekliyor var; JP `止まれ！...` -> 2 parca, dur+bekliyor var;
  JP `待って！本当に行くの？` -> 2 parca.

## Yeniden nisanlanan testler

Teslim dosyasinda bayatlayan test **yok** (tur 1 dosyasi yeni src'de 210/210). Tester-A'nin adlandirdigi
`test_a1_bolme_tablosu[{0}. B.]`, `[{PLAYER}! Wait!]`, `test_a4_cumle_sinirinda_*` A'nin kendi dizininde
(bana yasak) -- sef regresyonda bekliyor. Ayni davranislar teslim dosyasinda yeni kurala gore olculuyor:
`test_k3e_yer_tutucu_cikarildiktan_sonra_suzgec_tablosu[vokatif+cumle]`, `[sinirda-nokta]`,
`test_k3e_yer_tutucu_cumle_sinirinda_uc_segment_kendi_segmentinde_kalir`.

## Itiraz / sapma

Sefin kararlariyla olcumum celismedi. Iki kayit: (1) K5 `max(1, ...)` bildirilen-ama-kaynakta-olmayan yer
tutucuyu ekler (tur 1 davranisi; T2-2 fixture'larini buna gore kurdum, degistirmedim). (2) olcum-4 [B]
ucuncu satirda uydurdugum 'bekle' anahtari tutmadi; feedback-B gibi yalniz parca sayisi olculdu.

Yeni bagimlilik yok, `git commit` yok, sefe/tester'lara ait dosyalara dokunulmadi.
