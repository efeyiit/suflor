---
task: T-007
role: implementer
round: 1
status: tamamlandi
files_written:
  - src/translate/__init__.py
  - src/translate/local_nmt.py
  - tests/unit/translate/test_local_nmt.py
  - .agents/tasks/T-007/delivery.md
  - .agents/tasks/T-007/evidence/mypy.txt
  - .agents/tasks/T-007/evidence/pytest.txt
  - .agents/tasks/T-007/evidence/real_check.txt
  - .agents/tasks/T-007/evidence/cov.txt
  - .agents/tasks/T-007/evidence/pytest-tum.txt
  - .agents/tasks/T-007/evidence/mypy-test-dosyasi.txt
  - .agents/tasks/T-007/evidence/pytest-cp1254.txt
  - .agents/tasks/T-007/evidence/tdd-kirmizi-1-modul-yok.txt
  - .agents/tasks/T-007/evidence/olcum-1-ct2-api-olgulari.py
  - .agents/tasks/T-007/evidence/olcum-1-ct2-api-olgulari.txt
  - .agents/tasks/T-007/evidence/olcum-2-gercek-saglayici-davranisi.py
  - .agents/tasks/T-007/evidence/olcum-2-gercek-saglayici-davranisi.txt
  - .agents/tasks/T-007/evidence/olcum-3-close-bellek.py
  - .agents/tasks/T-007/evidence/olcum-3-close-bellek.txt
  - .agents/tasks/T-007/evidence/mutant-kiti.py
  - .agents/tasks/T-007/evidence/mutant-ayirt-etme.txt
commands:
  - cmd: "python -m mypy --strict --explicit-package-bases src/translate/local_nmt.py"
    exit_code: 0
    evidence: evidence/mypy.txt
  - cmd: "python -m pytest tests/unit/translate/test_local_nmt.py -q"
    exit_code: 0
    evidence: evidence/pytest.txt
  - cmd: "python .agents/tasks/T-007/real_check.py"
    exit_code: 0
    evidence: evidence/real_check.txt
  - cmd: "python -m pytest tests/unit/translate/test_local_nmt.py -q --cov=src.translate.local_nmt --cov-fail-under=90 --cov-report=term-missing"
    exit_code: 0
    evidence: evidence/cov.txt
  - cmd: "python -m pytest tests -q"
    exit_code: 0
    evidence: evidence/pytest-tum.txt
  - cmd: "python .agents/tasks/T-007/evidence/mutant-kiti.py"
    exit_code: 0
    evidence: evidence/mutant-ayirt-etme.txt
  - cmd: "python .agents/tasks/T-007/evidence/olcum-1-ct2-api-olgulari.py"
    exit_code: 0
    evidence: evidence/olcum-1-ct2-api-olgulari.txt
  - cmd: "python .agents/tasks/T-007/evidence/olcum-2-gercek-saglayici-davranisi.py"
    exit_code: 0
    evidence: evidence/olcum-2-gercek-saglayici-davranisi.txt
  - cmd: "python .agents/tasks/T-007/evidence/olcum-3-close-bellek.py"
    exit_code: 0
    evidence: evidence/olcum-3-close-bellek.txt
  - cmd: "python -m mypy --strict --explicit-package-bases tests/unit/translate/test_local_nmt.py"
    exit_code: 0
    evidence: evidence/mypy-test-dosyasi.txt
  - cmd: "python -m pytest tests/unit/translate/test_local_nmt.py -q  (PYTHONIOENCODING YOK, stdout cp1254)"
    exit_code: 0
    evidence: evidence/pytest-cp1254.txt
contract_change_request: false
known_gaps:
  - "[K3 -- BOLME NOKTALAMAYA GORE, SUZGEC, TEK BATCH] Kural: `[^T]*[T]+(?:\\s*[K]+)*|[^T]+\\Z` (T=`.!?。！？`, K=`」』）)\"'”’»`), bosluk sarti YOK; kirpilmis bos olmayan parcalar. Harf/rakam icermeyen parca (`str.isalnum` hicbir karakterde True degil) modele gitmez, ciktida yerinde aynen; hicbir parcasi gitmeyen segment KAYNAK METNIN AYNISI (`\"\"`, `\"   \"`, `\"。。。\"`); gonderilecek parca yoksa fabrika bile cagrilmaz. Tum segmentlerin parcalari TEK `translate_batch`; segment ciktisi `\" \"` ile birlesir. Olcu: `test_k3a_*` (2 segment 3+1 -> tek cagri 4 giris, dogru dagitim), `test_k3b_*` (12 metin x 3 dil AYNI bolunme: KR `A. B.` 2, JP `A。B。` 2, `A! B？ C.` 3, KR fixture 2, JP paragraf 3), `test_k3c_*` (`A。？` 1, `「A。」` 1, `。。。` 0, `   ` 0, `\"\"` 0; gecis parcasi cikti sirasinda yerinde), `test_k3d_*` (kayipsizlik: harf/rakam dizisi segment ve batch duzeyinde esit), 500 cumle tek batch. Gercek model: `real_check` #3 (JP paragraf 3 cumle, uc anahtar), #4 (KR tek segment 2 cumle, bekliyor+dogu), #4b (`。。。` aynen); ek olcum-2 [E]: `A。？`, `「A。」`, `待って！？本当に行くの？` (2 parca), `長老は言った。「東へ行きなさい。」` (2 parca) ciktilarinda `Hayır`/`Böyle` uydurmasi YOK. Mutant: M-01 (dile gore bolme, v1 hatasi), M-02 (suzgec yok), M-15 (bosluksuz birlestirme), M-17 (gecis segmenti bos), M-21 (segment basina ayri batch) -> 5/5 yakalandi. KARAR (paket sessizdi): terminator ile kapanis isareti arasinda bosluk olsa da isaret ONCEKI cumleye ait (`A。 」 B。` -> `A。 」` + `B。`); `…` (U+2026) terminator degil; `\\n` terminator degil (parca icinde kalir, kenarda kirpilir). [ÖLÇÜLMÜYOR] kalite: `Dr. Smith`, `3.5` (iki parca da rakam icerir, ikisi de modele gider), `v1.2.3`, `what?No` bolunur -- davranis testte SABITLENDI (`test_k3c` `3.5` -> `[\"3.\", \"5\"]`, `Dr. Smith` -> 2) ki degisirse gorunsun; dogru/yanlis oldugu altin setsiz olculemez."
  - "[K3 ITIRAZ DEGIL, NOT -- bosluk sarti] KRT Y1 duzeltmesi ASCII terminator icin 'ardindan bosluk/sonu' sartini oneriyordu; paket v2 K3 metni evrensel kumeyi sartsiz yazdi ve `3.5`i bilinen zayiflik olarak listeledi. Pakete uydum (sartsiz). Iki secenegin de kaybi var: sartli kural `3.5`/`v1.2`/URL'yi korur ama JP/KR OCR'in bosluksuz yarim-genislik noktasini (`はい.そうです.`) bolmez; sartsiz kural tersi. Hangisinin urunu daha az bozdugu altin set olmadan olculemez -- kalite gorevine not."
  - "[K4 -- UC BICIMLI TABLO] 4 dil x 3 bicim x buyuk/kucuk = 24 nokta (`test_k4_uc_bicim_*`): ilk token NLLB kodu, son `</s>`, `target_prefix` her satirda `[\"tur_Latn\"]`, `detected_lang` == NLLB kodu. Reddedilen kaynak: `None`, `xx`, `tr`, `tur_Latn`, `jpn`, `\"\"`, `ja-JP`, `\" ja\"` -> `ProviderUnavailable`, fabrika 0. Hedef 4 bicim + buyuk harf kabul; `tr-TR`, `tr_TR`, `en`, `eng_Latn`, `\"\"`, `turkce`, `None`, `5` -> `ProviderUnavailable`. KARAR (paket sessizdi): bosluk KIRPILMAZ (`\" ja\"` red), `str` olmayan kod `ProviderUnavailable` (`AttributeError` degil), dogrulama BOS istekte de yapilir (`test_k4_kaynak_dogrulamasi_bos_istekte_de_calisir`), Turkce kaynak olamaz. Mutant M-13 (None -> JAPAN), M-18 (belirtec sonda) yakalandi. Gercek: `real_check` #8."
  - "[K5 -- SAPMA, O1'E UYULDU: SAYIM, `in` DEGIL] Paket K5 lafzi 'tam alt dize olarak aranir; eksikse sona eklenir'; sef O1'i kabul etmis ama K5 metni `in` kaldi. Uygulama: gereken = `max(1, kaynak_metin.count(yt))`, mevcut = `cikti.count(yt)`, fark kadar sona (listedeki sirayla, boslukla; ayni dize bir kez islenir). Tek gecisli her girdide paketin lafziyla BIREBIR ayni cikti; yalniz cok gecisli girdide ayrisiyor (`%s and %s.` -> model `%s ve` -> `in` kontrolu 'var' der, ikinci `%s` sessizce kaybolur; sayim `%s ve %s` verir). Mutant M-05 (`in` kontrolu) `test_k5_ayni_yer_tutucu_birden_cok_gecis_sayim_ile` ile yakalandi; M-06 (onarim yok) yakalandi. Iki nokta: dusen -> sonda (`test_k5_dusen_*`), korunan -> dokunulmaz (`{0}`/`{1}` ve `<T0>`/`<T1>` iki bicim). Bozuk bicim (`[Mill'de]`) tam alt dize degil -> eklenir, cikti hem bozuk hem ekli [ÖLÇÜLMÜYOR] (`test_k5_bozuk_bicim_*` davranisi sabitler). Onarim SEGMENT duzeyinde (baska cumleye kayan yer tutucu sayilir). AST: `glossary_hits`/`tm_examples`/`style_profile`/`image_crops` ne oznitelik ne docstring-disi dize olarak modulde gecmez; davranis: dolu istek == duz istek, motor cagrisi ayni. Gercek: `real_check` #5 (JP `{0}`/`{1}` onarildi, EN korundu)."
  - "[K6 -- DORT DOSYA, VARLIK DENETIMI; sifir bayt -> ProviderUnavailable] `is_file()` ile dort ad; eksik olan(lar) mesajda, digerleri degil (`test_k6_dort_dosyadan_biri_*` 4 nokta + bos dizin + dizin-adli-dosya + `model_dir` dosya). Paketin olcusu 'bos dosyalar konunca fabrika cagrilir' boyut denetimini DISLIYOR; KRT O4'un 'sifir bayt -> ModelMissingError' onerisi bu yuzden uygulanmadi. Gercek modelde olculdu (olcum-2 [B]/[C]): sifir baytlik `model.bin` -> fabrikada CT2 `RuntimeError` -> `ProviderUnavailable` (`__cause__` RuntimeError); bos sentencepiece protosu kurulumda SESSIZ, `encode`de `RuntimeError` -> `ProviderUnavailable` ('kaynak metin tokenlestirilemedi'). Yani bozuk/yarim indirme `ModelMissingError` DEGIL `ProviderUnavailable` olarak yuzeye cikar (tasarim 5.6'da motor dususu tetikler, indirme degil) -- checksum ModelManager'in isi (tasarim 13), burada [ÖLÇÜLMÜYOR]. Fabrika `FileNotFoundError` -> `ModelMissingError`; `TranslatorError` sarilmaz; baska `Exception` -> `ProviderUnavailable` (mutant M-19 yakalandi). Kurulum hatasinda ornek tutulmaz, sonraki cagri yeniden dener. Motor ciktisi 9 bozuk bicim -> `ProviderUnavailable`; sayi uyusmazligi (3/2, 3/4, 3/0, 2 segment 3+1 -> 3 ya da 2 hipotez) -> `ContractViolation` (M-03 yakalandi). Hata mesaji 7 yolda nobetciyi tasimaz (M-22 ILK KOSUMDA KACTI: testin nobetcisi motor HATASINDAYDI, kaynak metinde degil; test duzeltildi, mutant simdi yakalaniyor -- `mutant-ayirt-etme.txt` son kosum)."
  - "[K7 -- BAYT ILE ACMA] `_varsayilan_fabrika`: `SentencePieceProcessor(model_proto=(model_dir / \"sentencepiece.bpe.model\").read_bytes())`, `Translator(str(model_dir.resolve()), **params)`. AST olcusu: fabrikada `model_proto=` var, `model_file=` yok, `read_bytes` + `.resolve()` var; `model_file` dizesi docstring disinda modulde hic gecmez; tarayicinin kor olmadigi parca-kodla gosterildi. Gercek: olcum-1 [1] `model_file=<ASCII-disi mutlak yol>` -> `RuntimeError` (C5 yeniden uretildi), `model_proto=bytes` acildi; `real_check` #7 ASCII-disi kopya dizinden ceviri calisti. Fabrikaya giden `model_dir` yapimda verilen `Path` (cozumlenmemis; `resolve` fabrikanin icinde, yapim dosya sistemine dokunmasin diye)."
  - "[K8 -- IPLIK, CEZA, ISIN] `params` tam olarak `{device: cpu, compute_type: int8, inter_threads: 1, intra_threads: threads}` (`test_k8_threads_intra_aynen_*` anahtar kumesi esit). `threads` [1, cpu_count], `None` -> min(8, cpu), 0/-1/-8 `ValueError`, `bool`/float/str `TypeError`, `cpu_count=None` -> 1 (T-006 K3 mantigi aynen). `repetition_penalty=1.0` (varsayilan VE acik 1.0) iken `translate_batch` kwargs `{}` (M-07 yakalandi); 1.2/1.5/2 -> `float` olarak aynen; KARAR (paket sessizdi): `< 1.0` (tekrari odullendirir), `nan`, `inf` -> `ValueError`; `bool`/str/None -> `TypeError`. `beam_size` 4 varsayilan, 2/1 aynen, 0/-1 `ValueError`, `bool`/float/str `TypeError` (paket sessizdi). `max_decoding_length=256` acik (M-16 160'a cekince yakalandi). Gercek: olcum-1 [5] `rp=1.0` acik == gecilmemis (ayni hipotezler, KRT D1 dogru); olcum-2 [D] `rp=1.2` gercek CT2'de hatasiz ve cikti farkli. Kalite [ÖLÇÜLMÜYOR]."
  - "[K9 -- LATENCY KURULUM HARIC; 315 ms] `t0` translate basinda; fabrika suresi ayrica olculup dusulur. Sahte: motor 30 ms uyur -> `latency_ms in [30, 200)`; fabrika 100 ms uyur -> ilk cagri `latency_ms < 100` (M-09 yakalandi). Gercek (olcum-2 [F]): ilk cagri duvar 611 ms, `latency_ms` 91 ms. `real_check` #6: JP 4 cumle beam=4 8 iplik medyan 315 ms (esik 350, uyari yok); olcum-1 [9] sef sarmalayicisiz ham CT2 311 ms (min 305). NOT: `real_check` [1]'in ilk cagrisi `latency_ms=354` -- bu KURULUM degil, yuklemeden sonraki ILK cikarimin soguk maliyeti (sonraki cagrilar 305-330); butce isinma sonrasi medyan uzerinden tanimli, tutuyor. `ProviderTimeout` firlatilmaz, ad modulde hic gecmez (AST), [ÖLÇÜLMÜYOR] damgasi docstring'de. CT2 `max_input_length=1024` sessiz kirpma belgelendi, `translate_batch`e gecilmedi (paket yalniz `max_decoding_length` istiyor; kwargs kumesi olcusu bozulmasin)."
  - "[K10 -- TEMBEL, TEK ORNEK, KAPATMA] Yapim fabrika 0; uc `translate` -> fabrika 1, motor 3. `close()` idempotent; sonrasi `translate` -> `ProviderUnavailable` (bos istek dahil, M-20 yakalandi), fabrika yeniden cagrilmaz. Weakref: fabrikanin dondurdugu motor + encode + decode ucune `weakref`; `close()` ONCESI `gc.collect()` sonrasi uclu CANLI (pozitif kontrol), SONRASI uclu OLU (M-10 yakalandi). Gercek (olcum-3): yapim +0 MB, ilk translate +722 MB, `close()` + `gc.collect()` -> 751 -> 47 MB (-704 MB), weakref [False, False, False], sonrasi `ProviderUnavailable`. `Translator.unload_model()` CAGRILMAZ (Protocol'de yok; referans birakma yetiyor, olculdu). KARAR (KRT D7): gonderilecek parcasi olmayan istek (bos, yalniz noktalama/bosluk) fabrikayi CAGIRMAZ -- yani bos istekle model varligi sinanamaz; `ModelMissingError` ilk gercek gonderimde dogar (`real_check` #8 'x' ile gecti)."
  - "[K10 KANAL OLCUSU -- T-006 K7 deseni + `Logger.handle` kancasi] `_k10_kanal_olcusu`: `capfd` out == '' VE err == '' (sifir bayt; `_ozgun_akislari_bosalt` iki ucta), kok logger DEBUG `caplog`, `warnings.catch_warnings(record=True)` + `simplefilter('always')`, iki nobetci (`NÖBETÇİ-7f3a`, `長老-9c1e`). EK (T-006'dan sapma, ust kume): `logging.Logger.handle` monkeypatch ile HER logger'in gercekten yayimladigi kayit toplanir -- T-006'da kutuphane logger'inin adi biliniyordu (`RapidOCR`) ve dogrudan handler takiliyordu; burada CT2'nin Python logger'i yok, adi bilinmeyen `propagate=False` bir logger'a yazan mutant ancak boyle gorulur (M-12 yakalandi; pozitif kontrol `adi-bilinmeyen-logger-propagate-kapali`). Uc nokta: soguk (kurulum + ceviri), sicak (kurulum bitmis, kok DEBUG), hata yolu (`ContractViolation`). 7 pozitif kontrol sahte saglayici (stdout / stderr / `os.write(1)` / `sys.__stderr__` tamponlu / kok logger debug / bilinmeyen logger info+propagate=False / warnings) 7/7 DUSER; negatif kontrol `FakeProvider` gecer. AST ikincil: `print`/`sys.std*.write`/`os.write`/`sys.std*` erisimi/log yayimi/`logging` importu hepsi 0 + sayac pozitif kontrolu. Gercek (olcum-2 [A]): alt surecte kurulum + JP/KR/EN ceviri boyunca stdout 0 bayt, stderr 0 bayt -- CT2 C++ logu (varsayilan WARNING) bir sey basmadi; global seviyesine dokunulmadi. cp1254 konsolda (PYTHONIOENCODING yok) 210 passed (`pytest-cp1254.txt`)."
  - "[K2 -- HIZALAMA] `ensure_aligned` `translate` govdesinde (AST; M-04 kaldirilinca yakalandi). Cumle sayisi denetimi `_hipotez_tokenleri`de, `ensure_aligned`dan once. `request` `TranslationRequest` degilse, segment `text` `str` degilse, `placeholders` icinde `str` olmayan varsa `ContractViolation` ve motor/fabrika 0. Hedef belirteci yalniz `hypotheses[0][0] == \"tur_Latn\"` ise atilir; belirtecsiz hipotez (sahte) aynen korunur (`test_k6_hedef_belirteci_*`)."
  - "[K1 -- BARIYER ALTINDA] Test dosyasi `ctranslate2`/`sentencepiece` import etmez; her `model_dir` `tmp_path` (dort bos dosya); `models/` okunmaz. Modul duzeyi ve `_varsayilan_fabrika` disindaki her fonksiyon kutuphane importundan arindirilmis (AST). Sahte kosum sonrasi `sys.modules`de kutuphane yok. `CeviriMotoru.translate_batch` ilk parametresi paketteki gibi `tokens` ADLI ama her zaman KONUMSAL cagrilir -- gercek imza `source` (olcum-1 [2]/[3]: `tokens=` -> `TypeError`, konumsal OK, KRT D2 dogru)."
  - "[AYIRT ETME -- `evidence/mutant-kiti.py` -> `mutant-ayirt-etme.txt`] Ayna agacinda (scratchpad) 22 mutant + 3 davranis-esdeger kontrol, her biri test dosyasiyla `-x` kosuldu: M-01..M-22 22/22 YAKALANDI; C-1 (close satir sirasi), C-2 (`1000.0` -> `1e3`), C-3 (`any(gen)` -> `any(list)`) 3/3 KACTI (yanlis pozitif yok). Ilk kosumda M-22 kacti; test guclendirildi (yukarida K6). TDD kirmizi: `tdd-kirmizi-1-modul-yok.txt` (modul yokken toplama hatasi); anlamli kirmizi kiti mutant kitidir."
  - "[OLCUM BETIKLERI -- sef yeniden uretebilsin] `olcum-1-ct2-api-olgulari.py` (C4/C5/D1/D2/O4 yeniden uretimi: `model_file` ASCII-disi -> RuntimeError; `tokens=` -> TypeError; `hyp[0][0]=='tur_Latn'`, `</s>` yok; rp=1.0 acik==yok; bos batch `[]`; sifir bayt model.bin -> RuntimeError, `contains_model` True; bos proto kurulumda sessiz encode'da RuntimeError; weakref/unload_model var; 311 ms), `olcum-2-gercek-saglayici-davranisi.py` (kanal 0 bayt, K6 siniflari, rp=1.2, Y2 gercek pozitif kontrol, latency), `olcum-3-close-bellek.py` (Windows `GetProcessMemoryInfo`; ilk kosumda restype eksikligiyle 0 MB okudu, duzeltildi -- betik dosyasi duzeltilmis hali). Ucu de ASCII basar, metin basmaz. BULGU (bilgi): olcum-1 [6] `target_prefix` 3 / source 2 -> CT2 HATA VERMIYOR (KRT D2 ters yon icin RuntimeError demisti); bu modul her zaman esit sayi gecer, etkisi yok."
  - "KAPSAM DISI (bloke etmeyen): thread-safe degil (tasarim 5.5); `Translator.unload_model()` cagrilmiyor (referans birakma olculdu, yetiyor); CT2 C++ log seviyesi degistirilmiyor; `max_input_length` gecilmiyor (belgeli); kalite (beam, ceza, bolme zayifliklari) altin setsiz [ÖLÇÜLMÜYOR]; `git commit` ATILMADI; `pip install` YAPILMADI; sefe ait dosyalara (conftest, real_check, fixtures, packet) DOKUNULMADI."
---

# T-007 teslim -- tur 1

## Ne yazildi

* `src/translate/__init__.py` -- docstring, bos (paket importu kutuphaneye dokunmaz).
* `src/translate/local_nmt.py` (728 satir) -- `NmtDili`, `CeviriMotoru`, `MotorFabrikası`,
  `LocalNmtProvider`; public yardimcilar `cumlelere_bol`, `modele_gider`,
  `kaynak_dili_coz`, `hedef_dili_coz`, `zorunlu_model_dosyalari`, `eksik_model_dosyalari`.
  K1-K10 bolumlu modul docstring'i; her karar yaninda test adi ya da `[ÖLÇÜLMÜYOR]`.
  `ctranslate2`/`sentencepiece` yalniz `_varsayilan_fabrika` govdesinde
  (`# type: ignore[import-untyped]` yalniz orada, baska yerde yok).
* `tests/unit/translate/test_local_nmt.py` (1471 satir, **210 test**) -- sahte motor/fabrika,
  K1-K10 + yozlasmis girdiler, K10 kanal olcusu (3 nokta + 7 pozitif + 1 negatif kontrol),
  AST ikincil olculer + tarayici pozitif kontrolleri. Referanslar sabit (NLLB kodlari, dosya
  adlari, parametre adlari) -- saglayicidan turetilmiyor. mypy --strict temiz.

## Bes komut

| # | komut | exit | sonuc | kanit |
|---|---|---|---|---|
| 1 | mypy --strict | 0 | temiz | `evidence/mypy.txt` |
| 2 | pytest birim | 0 | 210 passed | `evidence/pytest.txt` |
| 3 | real_check.py | 0 | 13/13 ok, TEMIZ, 0 uyari; #6 medyan 315 ms | `evidence/real_check.txt` |
| 4 | coverage >= 90 | 0 | %100 (239 ifade, 0 eksik; `_varsayilan_fabrika` pragma) | `evidence/cov.txt` |
| 5 | pytest tum takim | 0 | **1314 passed** (1104 + 210), dusen yok | `evidence/pytest-tum.txt` |

Ek: mutant kiti 22/22 + 3/3 (`mutant-ayirt-etme.txt`), uc gercek-model olcumu
(`olcum-1/2/3-*.txt`), cp1254 kosumu 210 passed, test dosyasi mypy temiz.

## Hangi iddia nasil olculdu (ozet)

| iddia | sahte (birim) | gercek model |
|---|---|---|
| K3 noktalamaya gore bolme, KR ASCII nokta | `test_k3b` 12 metin x 3 dil | real_check #3/#4 |
| K3 suzgec: noktalama parcasi modele gitmez | `test_k3c` 13 vaka | real_check #4b; olcum-2 [E] 4 girdi, uydurma yok |
| K2 cumle sayimi (segment tutup cumle tutmayan kayma) | `test_k2_segment_sayisi_tutup_*` | -- |
| K4 uc bicim, None red | 24 + 8 + 12 nokta | real_check #8 |
| K5 dusen sona, korunan dokunulmaz, sayim | `test_k5_*` 10 test | real_check #5 |
| K6 dort dosya, siniflar | `test_k6_*` 30+ vaka | olcum-2 [B]/[C]; real_check #8 |
| K7 bayt ile acma | AST + tarayici pozitif kontrolu | olcum-1 [1]; real_check #7 |
| K8 rp 1.0 gecilmez, iplik, beam, 256 | `test_k8_*` | olcum-1 [5]; olcum-2 [D] |
| K9 latency kurulum haric | 30 ms / 100 ms iki nokta | olcum-2 [F]: 611 duvar / 91 latency |
| K10 close birakir | weakref uclu | olcum-3: 751 -> 47 MB |
| K10 hicbir kanala metin yok | capfd + caplog + handle kancasi + warnings, 3 nokta, 7+1 kontrol | olcum-2 [A]: 0 bayt |

## Itiraz / sapma (hepsi `known_gaps`te gerekceli)

1. **K5 sayim** (paket lafzi `in`; O1 kabul edilmisti) -- tek gecisli girdide birebir ayni,
   cok gecisli girdide `in` yer tutucu kaybediyor; mutant M-05 ile gosterildi.
2. **K6 boyut denetimi YOK** -- paketin kendi olcusu (bos dosyalarla fabrika cagrilir) bunu
   disliyor; sifir bayt gercek modelde `ProviderUnavailable` (olcum-2 [B]).
3. **K10 `Logger.handle` kancasi** -- T-006 deseninin ust kumesi; adi bilinmeyen logger icin.
4. Paket sessiz kaldigi yerlerde KARAR'lar (bosluklu kapanis isareti, `rp < 1` red, `beam` red,
   bosluk kirpma yok, bos istekte fabrika yok) docstring + `known_gaps`te.

Yeni bagimlilik yok, `git commit` yok, sefe ait dosyalara dokunulmadi.
