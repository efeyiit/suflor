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
    evidence: tester_B_evidence/taban-1-mypy.txt
  - name: "taban 2 -- implementer birim testleri 256 passed"
    cmd: "python -m pytest tests/unit/translate/test_sozluk.py -q -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/taban-2-pytest.txt
  - name: "taban 3 -- real_check TEMIZ 12/12 (#7 yuk altinda 35.0 ms; yalitilmis yeniden olcum 17.6 ms, model-olcum2 [L])"
    cmd: "python .agents/tasks/T-011/real_check.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/taban-3-real_check.txt
  - name: "taban 4 -- kapsam %100 (301 ifade, 0 eksik)"
    cmd: "python -m pytest tests/unit/translate/test_sozluk.py -q -p no:cacheprovider --cov=src.translate.sozluk --cov-fail-under=95 --cov-report=term-missing"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/taban-4-kapsam.txt
  - name: "taban 5 -- tam takim 1700 passed"
    cmd: "python -m pytest tests -q -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/taban-5-tum-takim.txt
  - name: "mercek-B testleri: 48 fonksiyon / 92 kosum -- 91 passed + 1 xfail (paketin belgeli `검은 옷` siniri)"
    cmd: "python -m pytest .agents/tasks/T-011/tester_B -q -p no:cacheprovider --import-mode=importlib -rfEx"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/mercek-b-testleri.txt
  - name: "mercek-B + sefin translate dizini birlikte: 606 passed + 1 xfail (bariyer iki tarafta)"
    cmd: "python -m pytest tests/unit/translate .agents/tasks/T-011/tester_B -q -p no:cacheprovider --import-mode=importlib"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/birlikte-kosum.txt
  - name: "gercek model olcum 1 (A-I, G): G1 6/6 -> gercek gomme katkisi 4/6, deterministik 6/6; kendi 6 cumlem bozulma 0; Y3 7/11 terim hamda zaten var; unvan bilesik 3/8 ham dogru -> gomulu YANLIS; sinir kacagi 4/6 ad kayip; kaynak `。` ikinci cumle KAYIP; sure 11/50/500 terim ayni"
    cmd: "python .agents/tasks/T-011/tester_B/b_model_olcum.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/model-olcum-stdout.txt
  - name: "gercek model olcum 1 -- ham ceviri metinleri (UTF-8; konsola basilmadi)"
    cmd: "python .agents/tasks/T-011/tester_B/b_model_olcum.py  (ayni kosum, ham dosya)"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/model-olcum-ham.txt
  - name: "gercek model olcum 2: kismi gomme (`İhtiyarマルクス様`) bozmuyor, ad ham kaliyor 3/3; real_check #7 yalitilmis medyan 17.6 ms"
    cmd: "python .agents/tasks/T-011/tester_B/b_model_olcum2.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/model-olcum2-ham.txt
  - name: "gercek model olcum 3: real_check #4 pozitif kontrolu -- yalniz ad gomulu `장로 Marcus` -> 'Elder Marcus' (olcu ateslenebilir; kapi kosmuyor)"
    cmd: "python .agents/tasks/T-011/tester_B/b_model_olcum3.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/model-olcum3-ham.txt
  - name: "statik sonda 1: segment_index unutma mesaji, ayni nesne x2, speaker, kimlik gomme, idempotens (fixture / hedef⊇kaynak), sembol kategorileri, TypeError siniflari, generator/list, kaynak `。`"
    cmd: "python .agents/tasks/T-011/tester_B/sonda1_statik.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/sonda1-statik.txt
  - name: "statik sonda 2: JP saygi eki 17/17 + KR ek disi 21/21 kacak, sembol 7->5/2, NFD yer tutucu kaymasi, kaynak terminator bolme 2->1, IGNORECASE Turkce I, 1000 rastgele lookup==lookup_segments (4466 hit), KR ek zinciri, buyutme kenarlari"
    cmd: "python .agents/tasks/T-011/tester_B/sonda2_statik.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/sonda2-statik.txt
  - name: "depo dokunulmadi: src/tests/demo/real_check/packet/fixtures git status BOS; olculen dosyalarin sha256; HEAD 1ff6a8a"
    cmd: "git status --short -- src tests demo .agents/tasks/T-011/real_check.py .agents/tasks/T-011/packet.md .agents/tasks/T-011/fixtures; sha256sum ..."
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/git-status.txt
  - name: "korluk: test_sozluk.py yalniz kendi testlerim bittikten SONRA, yalniz test kalitesi icin acildi (an kaydi)"
    cmd: "date"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/test_sozluk-acilis-ani.txt
blocking_issues: []
---

# T-011 tur 1 -- Tester-B (mercek: kotu kullanim + sartname uyumu)

Karar: **ONAY**. Paket K1-K7 ve docstring iddialarinin **olculmus ihlali yok**; bes taban komutu yesil; kendi 92 kosumum yesil (1 xfail paketin kendi belgeli siniri). Gercek zincirde (lookup -> gom -> translate) kendi 6 cumlemde ve G1'in 6'sinda **gomme yuzunden bozulma 0**. Ret esigine en cok yaklasan bulgu Y-B1'dir (asagida): fixture'in kendi unvan terimleri bilesik icinde dogru cevriyi bozuyor (3/8) -- ama bu sinif docstring K4'te acikca `[ÖLÇÜLMÜYOR]` damgali ve Y3 olarak belgeli, kodun degil paketin/fixture'in karari; implementer'in duzeltebilecegi bir sey degil. Ret degil, sefe yuksek oncelikli oneri + kapi bulgusu.

Korluk: `delivery.md`, `evidence/`, `sef_dogrulama/`, `tester_A*` acilmadi. `test_sozluk.py` 19:30:06'da, kendi testlerim (91+1) ve model olcumlerim bittikten sonra, yalniz test kalitesi icin acildi (`tester_B_evidence/test_sozluk-acilis-ani.txt`). `demo/canli_cevir.py` ve `demo/sozluk_ornek.json` calisma sirasinda sef tarafindan commit edildi (1ff6a8a); implementer sahiplik ihlali degil -- ama zincirin gercek cagirani artik var ve bulgular ona gore yazildi.

## Yontem

Onceden okunan: PROTOKOL, packet v2, olgular G1-G7, krt-1, real_check.py, fixture, `sozluk.py`, `local_nmt.py`, contracts, demo, tasarim 4.1/5.x. Statik sondalar (`sonda1/2_statik.py`) -> 48 test fonksiyonu (`test_mercek_b.py`, 92 kosum) -> gercek model ayri surecte 3 betik (`b_model_olcum{,2,3}.py`; stdout ASCII, ham metin UTF-8 dosyada). Model olcumlerinde karsilastirma anahtari `casefold` + Turkce `İ/ı` katlama (`"İ".lower()` 2 kodpoint uretir; ilk kosumda bu tuzaga ben de dustum, `_k` ile duzeltip yeniden kostum -- bkz. K-B4).

## Sartname uyumu (K1-K7 satir satir)

| K | Paketin istedigi | Kod | Olcu |
|---|---|---|---|
| K1 | en uzun once, ortusmesiz, `\b` yok, sinir listesi, IGNORECASE orijinal metinde, n gecis n hit | uyuyor; trie tek gecis | `test_b9_k1_*` (paketin 7 negatif / 7 pozitif ornegi, iki sirali sozluk, `İstanbul`/`ﬁne`, n gecis) |
| K2 | start-azalan uygulama, alanlar aynen, tutarsiz/ortusen -> CV, bos hits -> `is` | uyuyor | `test_b9_k2_*`, `test_b2_*`, `test_b1_girdi_listesi_degistirilmez` |
| K3 | placeholders korunan aralik, gom da denetler (CV) | uyuyor | `test_b9_k3_*`, `test_b3_yer_tutucu_bildirilmemisse_*` |
| K4 | ilk harf buyuk, `ozel_ad` yok, `not` -> note | uyuyor | `test_b9_k4_*` |
| K5 | saf, deterministik, 1000x50 < 50 ms | uyuyor; **terim sayisindan bagimsiz dogrulandi** (11/50/500 terim: `lookup_segments`+gom 30.4/31.3/31.2 ms, kapi yolu 39.6/40.1/39.7 ms -- eszamanli model yuku altinda; kapi yolu yalitilmis 17.6 ms) | `test_bx_docstring_k5_*`, model-olcum [G], model-olcum2 [L] |
| K6 | sema (bos, tekrar, tek hece/kanji, hedefte terminator, `{}`), NFC, FileNotFoundError sarilmaz, bayt | uyuyor | `test_b9_k6_*`, `test_b8_dosya_yok_*`, `test_bx_docstring_bom_*` |
| K7 | None/aralik disi -> CV | uyuyor | `test_b9_k7_*`, `test_b1_segment_index_unutulursa_*` |

**Uydurulmus davranis (kod yapiyor, paket istemiyor) -- hepsi docstring'de belgeli, hicbiri ihlal degil:** bas/son bosluklu kaynak/hedef reddi; kayit duzeyinde bilinmeyen anahtar reddi (`ozel_ad`, `kategori` -> butun sozluk yuklenmez); KR ek zinciri 2 derinlik (`방앗간에서는` evet, `방앗간은가` da evet, 3 ek hayir); tek kodpoint reddi Latin/kana/rakama genisletildi; `TypeError` sinifi (O-B4); `lookup_segments` (KRT O4 onerisi). Sonraki cagirana etkisi asagida tek tek.

**Eksik davranis (paket istiyor, kod yapmiyor):** bulunmadi.

## Bulgular

### YUKSEK (oneri/yukumluluk -- ret degil, gerekce her maddede)

**Y-B1 · Fixture'in kendi unvan terimleri bilesik icinde DOGRU cevriyi bozuyor; paket "fixture yalniz yanlis cevrilen terimleri icerir" der, olcum bunu 7/11'de yalanliyor; kapi bu sinifi olcmuyor.** Gercek model, fixture sozlugu, `model-olcum-ham.txt` [H]/[C]:
- `마을 장로가 마르쿠스를 불렀습니다.` ham **"Köy ihtiyarı Marcus'u çağırdı."** (dogru) -> gomulu `마을 İhtiyar가 Marcus를…` -> **"İhtiyar kasabası Marcus'a seslendi."** (anlam kaydi: ozne "İhtiyar kasabasi")
- `마을 장로가 왔습니다.` ham "Köyde bir ihtiyar geldi." -> gomulu **"İhtiyar kasabasından geldi."**
- `The village elder came.` ham **"Köy ihtiyarı geldi."** -> gomulu `The village İhtiyar came.` -> **"İhtiyar köyü geldi."**
- 8 bilesik cumlenin 3'unde ham dogru -> gomulu yanlis ([H0], [H1], [H6]); 4'unde gomulu duzeltti ([H3], [H4], [H5], [H7]); 1'i notr ([H2]).
- [C]: 11 fixture teriminin **7'sinde** tek cumlelik ham ceviri hedefi zaten iceriyor (`마르쿠스`, `Marcus`, `アイラ`, `아일라`, `長老`, `장로`, `elder`). Savunulabilir gerekce "tutarsizlik" (ayni ad Marks/Markos/Mark/Markus, Aira/Ayla; `長老` ihtiyarlar/İhtiyar) -- ama paketin ve docstring'in kurali "yanlis cevirdigi" diyor, "guvenilmez cevirdigi" degil.
- Mekanizma: Latin, buyuk harfli `İhtiyar` bir isim-isim bilesiginde (koy + ihtiyar) ozel ad okunuyor; model "X'in kasabasi" kuruyor. Bu tam KRT Y3'un sinifi -- unvanlar da cins isimdir.
- **Neden ret degil:** docstring K4 bu sinifi acikca belgeliyor ("motorun ZATEN BILDIGI bir kelimeyi gommek ceviriyi BOZAR … Ceviri KALITESI `[ÖLÇÜLMÜYOR]`"); K1-K7'nin hicbiri ihlal edilmiyor; kod fixture'in icerigine karar veremez. Bu, paketin **fixture ve yazarlik kurali** karari.
- **Oneri (sef):** (1) fixture'dan `장로/長老/elder` cikarilir ya da `not` alanina "unvan: bilesikte ('koy ihtiyari') gomme anlam kaydirir" yazilir ve real_check'e **negatif olcu** girer: ham dogru olan bir bilesik cumle kumesinde gomulu cevirinin ozne/nesne yapisi korunmali (en az `마을 장로가 마르쿠스를 불렀습니다.` -> ciktida "Marcus'u/Marcus'a" nesne, "kasaba" yok); (2) docstring yazarlik kurali "yanlis" -> "yanlis ya da TUTARSIZ" + acik uyari: **unvan ve cins isim sozluge girerse bilesik icinde ('koy ihtiyari', 'ihtiyar meclisi') anlam kayabilir; adlar guvenli**; (3) UI sozluk editoru (ileriki gorev) icin tasarim yukumlulugu: terim eklenmeden once **ham ceviri onizlemesi** (kod bunu denetleyemez -- `not` alanini zorunlu kilmak yeterli degil, yalniz niyet kaydeder; onizleme olcer).

**Y-B2 · Sinir listesi oyun metninin en yaygin sinifini kaciriyor: JP saygi ekleri 17/17, KR ek listesi disi 21/21 eslesmez; gercek modelde 4/6 cumlede ad kayboluyor. Kod pakete UYUYOR -- paket eksikligi.** `sonda2-statik.txt`, `test_b7_jp_*`/`test_b7_kr_*`, `model-olcum-ham.txt` [E]:
- JP: `マルクスさん/様/殿/君/ちゃん/達/たち/って/だ/じゃない/なら/から/まで/より/か/よ/ね` -> **0 hit** (kana/kanji komsusu sinir degil -- docstring bunu genel kuralla belgeler, saygi ekini adlandirmaz). Modelde: `マルクスさんが来た。` -> "Bay **Marks** geldi."; `マルクスたちは東へ行った。` -> "**Markslar** doğuya gitti."
- KR: `마르쿠스에게/한테/께/님/씨/야/아/랑/처럼/보다/마다/밖에/조차/들/라고/라면/인가`, `장로님`, `장로에게`, `방앗간이다/입니다` -> **0 hit**. `에게` (yonelme, cok yaygin): `에` ek + `게` sinir degil -> zincir kurtarmiyor. Modelde: `마르쿠스에게 말했습니다.` -> "**Markos'a** söyledim."; `아일라가 장로에게 편지를…` [B5] -> "ihtiyarlara" (cogul, yanlis).
- **Oneri (paket K1, sef):** JP sinir kumesine saygi/kopula ekleri (`さん 様 殿 君 ちゃん 達 たち って だ から まで より か よ ね`), KR ek listesine `에게 한테 께 님 씨 야 아 랑 이랑 들 처럼 보다 마다 밖에 조차 라고 라면 입니다 이다` -- ayni sag-sinir mekanizmasi, yeni mekanizma gerekmez. Yeni ek her seferinde G6 gibi bilesik negatif kontrolle olculur (`님` -> `장로님` evet ama `님` ile baslayan kelime yok; `들` -> `마르쿠스들` evet).

### ORTA

**O-B1 · Kaynak terimde cumle sonu isareti kabul ediliyor; gomme cumle sinirini yutuyor, gercek modelde ikinci cumle KAYBOLDU.** `test_b3_kaynak_terimde_terminator_*`, `model-olcum-ham.txt` [I]: sozluk `マルクス。 -> Marcus` semadan gecer (K6 terminatoru yalniz **hedefte** yasaklar); `彼はマルクス。 行こう。` -> `彼はMarcus 行こう。` -> T-007 2 parca -> 1 parca; ham **"Bu adam Marks. Hadi gidelim."** -> gomulu **"O da Marcus."** ("Hadi gidelim" yok). OCR metninden kopyalanan terime nokta yapismasi kolay. K2 "aralik disi aynen" tutar (nokta aralik ICINDE), yani iddia ihlali degil; sessiz kayip. **Oneri:** K6 semasi kaynak icin de `.!?。！？` reddi (en azindan son karakter), mesajda terim.

**O-B2 · NFD yer tutucu + hit: cikti Segment'te `placeholders` artik metnin alt dizesi degil; T-007 K5 kopya ekler; hit'siz segment NFD kalir (karisik normalizasyon).** `test_b6_nfd_yer_tutucu_*`, `sonda2-statik.txt`: K6 metni NFC'ler, K2 `placeholders`i aynen tasir -- ikisi de paketin lafzi, bilesimi tutarsiz Segment uretir: `modele_gider` NFD `{Değirmen}`i cikaramaz (metin sayar), `_yer_tutuculari_onar` `count` 0 gorup sona NFD kopya ekler. Girdi NFD olma olasiligi dusuk (OCR onbirlesik uretir) -> orta. **Oneri:** cikti Segment'te `placeholders` da NFC'lenir (`dataclasses.replace(seg, text=…, placeholders=nfc)`) ya da metin NFC'lenmez, yalniz arama NFC uzerinden yapilir (indeksler o zaman orijinal metne aittir -- O-B7 ile birlikte cozulur).

**O-B3 · `hedef ⊇ kaynak` semada serbest -> gomme idempotent degil; pipeline ayni segmenti iki kez islerse terim buyur.** `test_b6_hedef_kaynagi_iceriyorsa_*`: `mill -> Değirmen mill` kabul; `by the mill.` -> `by the Değirmen mill.` -> `by the Değirmen Değirmen mill.` -> … Fixture ile idempotent (`test_b6_fixture_ile_gomme_idempotent`). **Oneri:** sema: hedef, kaynagi (IGNORECASE, sinirli) icermesin -> `ValueError`; ya da docstring'e "gom ciktisi tekrar lookup'a verilmez" (TM/cache gomulu metni saklarsa tuzak).

**O-B4 · `TypeError` sinifi `TranslatorError` degil; paket bu sinifi saymiyor; T-007 ayni bozuk Segment'i sessizce kabul ediyor.** `test_b8_typeerror_*`, `test_b8_t007_ayni_bozuk_segmenti_*`: `Segment(placeholders="{0}")` (duz str) -> `lookup_segments`/`terimleri_gom` `TypeError`; T-007 `translate` icin `all(isinstance(yt, str) for yt in "{0}")` True -> gecer. Sozluk zincirin onunde oldugu icin pipeline artik burada patlar ve `except TranslatorError` (tasarim 5.6, demo) yakalamaz. Docstring K3/K6 `TypeError`i belgeler -> ihlal degil. **Oneri:** Segment'ten turetilen bicim hatalari (`lookup_segments`, `terimleri_gom`) `ContractViolation`; `lookup(text, placeholders)` dogrudan cagrisinda `TypeError` kalabilir. `numpy` tamsayi indeks de CV (`test_b8_numpy_*`; T-007 `numbers.Integral` kabul ediyor -- tutarsiz, dusuk).

**O-B5 · Reddedilen komsu aday da sinir verir -> KISMI gomme.** `test_b6_reddedilen_komsu_aday_*`, `model-olcum2-ham.txt` [J]: `長老マルクス様` -> yalniz `İhtiyar` (ad `様` yuzunden reddedilir ama VARLIGI `長老`ya sag sinir verir) -> `İhtiyarマルクス様が来た。` -> "İhtiyar **Marks** geldi." Docstring K1 bunu "aday olmasi yeter" diye belgeler; modelde bozulma yok (3/3 unvan dogru, ad ham). Paketin lafzi ("baska bir terimin baslangici") izin verir. Y-B2 cozulurse buyuk olcude kaybolur. **Oneri:** docstring'e kismi gomme ornegi; istenirse "komsu aday KABUL edilmis olmali" (iki gecisli) -- mekanizma degisikligi, sef karari.

**O-B6 · Kimlik gomme (`Marcus -> Marcus`) hit uretir, gom kopya doner; gercek cagiran (demo) bunu "gomulen terim" sayiyor.** `test_b6_kimlik_gomme_*`: `Marcusが待っています。` -> 1 hit, metin ayni, `is` degil. `demo/canli_cevir.py:71` `terimler = [h.target_term for h in hits]` -> seritte "sözlük N terim" ve Turkce panoda vurgu, gomme olmadan. Fixture'daki `Marcus->Marcus` girdisinin gercek islevi **sinir cipasi** (`長老Marcus` -> `長老` ancak `Marcus` sozlukteyse eslesir; `test_b6_kimlik_terim_komsu_sinir_cipasi_*`) -- docstring/fixture bunu soylemiyor. **Oneri:** docstring'e "kimlik girdisi = sinir cipasi, hit uretir, metni degistirmez"; cagiran sayaci `source_term != target_term` ile suzsun (ya da `TermHit`e ek alan -- sozlesme degisikligi, sef).

**O-B7 · `TermHit.start/end` NFC metne gore; `Segment.text` NFD ise UI vurgusu kayar.** `test_b6_hit_indeksleri_nfc_metne_gore_*`: docstring K1 belgeli; kaynak paneli vurgulayan sonraki ajan once NFC'lemek zorunda (demo gomulu metni gosteriyor, orijinali degil -> bugun etkilenmiyor). **Oneri:** TextNormalizer (T-004) ciktisi NFC garantisi verirse sinif kapanir; verilmiyorsa `lookup_segments` docstring'inde UI notu.

### DUSUK

- **D-B1** Sembol kategorileri (`S*`) sinir degil (docstring `[ÖLÇÜLMÜYOR]`, olctum): fixture'in 5 cumlesine sonek `♪ ～ ♥ ☆ → ＋ ♡ ★ ♫ © ™ ° ＄ ￥` -> 7 hit -> **5**; onek -> **2**. `～` (U+FF5E, Sm) ile `〜` (U+301C, Pd) ayni gorunur, farkli davranir (`マルクス～` 0, `マルクス〜` 1). `test_b7_sembol_*`. Oneri: `S*` de sinir (sembol kelime kurmaz; bilesik riski yok).
- **D-B2** `ilk_harfi_buyut` `upper()` genislemesi: `ﬁne -> FIne`, `ß -> SS`, `ǅ -> Ǆ`; `iPhone -> İPhone` belgeli. `test_b9_k4_*`. Oneri: `str.title()`-benzeri tek kodpoint (`capitalize` degil) ya da belge.
- **D-B3** Belgeli uydurulmus davranislarin UI etkisi: kayit duzeyi ek alan (`kategori`, `aktif`) ve bas/son bosluk -> **butun sozluk yuklenmez** (`ValueError`), UI editoru meta veri koyamaz/kirpmak zorunda. `test_b9_uydurulmus_*`. Oneri: bilinmeyen anahtar icin `ValueError` yerine belgeli yoksayma ya da `ek: {...}` serbest alan; bosluk kirpma. Sef karari.
- **D-B4** Yalniz-terim segment gomulunce modele gidiyor: `マルクス` -> `Marcus` -> **"- Marcus."** (tire + nokta uydurma; ham "Marx."); `水車小屋`/`장로`/`mill`/`アイラ` aynen. `model-olcum-ham.txt` [D]. T-007 sinifi; oneri (pipeline): tamami hedef terim (+bosluk/noktalama) olan gomulu segment modele gonderilmeden aynen gecer.
- **D-B5** Sure: kapi yolu yalitilmis 17.6 ms ([L]); eszamanli model yuku altinda `lookup_segments`+gom 30-31 ms, kapi yolu 39.6-40.1 ms ([G]; 11/50/500 terim ayni -- terim sayisindan bagimsiz); real_check #7 benim taban kosumumda 35.0 ms. Butce tutuyor, pay yuk altinda 1.25x. Bilgi.
- **D-B6** KR ek zinciri anlamsiz dizileri de kabul ediyor (`방앗간은가`, `방앗간로가` -> 1 hit); gercek metinde erisilmez, zararsiz. `test_b9_uydurulmus_kr_ek_zinciri_*`.

### Test kalitesi (implementer testleri; `test_sozluk.py` 19:30:06'da acildi)

- 113 test fonksiyonu / 256 kosum; her K icin ayri kimlikli sinif testleri var; totoloji (sabit==sabit, uygulamadan turetilmis beklenti) bulmadim -- beklentiler literal.
- `pytest.raises(TypeError)` **match'siz 4 yer** (`test_k1_lookup_text_str_degil_typeerror`, `test_k1_lookup_placeholders_bicimi_typeerror`, `test_k6_yol_str_kabul_baska_tip_typeerror`): kasitli `isinstance` denetimi kaldirilsa `_nfc(None)`/`Path(None)` yine `TypeError` -> test ayiramaz. `ContractViolation` raises'lar match'siz ama girdiler tek nedeni tetikliyor (ortusen hit testlerinde dilimler dogru) -- kabul.
- Sure testleri 4x gevsetme yalniz `sys.gettrace()` doluyken (kapsam kosumu); **duz `pytest` kabul listesinde** ve orada pay 1x -> 50 ms'yi asan yavas mutant duz kosumda yakalanir, kapsam kosumunda 200 ms'ye kadar kacar. Duz kosum kapida oldugu icin kabul; yuk altinda (D-B5) duz kosum flake riski var (39.7 ms olctum).
- **Hic test edilmeyen siniflar** (benim testlerim kapatir): kaynak terminator (O-B1), NFD yer tutucu kaymasi (O-B2), hedef⊇kaynak idempotens (O-B3), kismi gomme (O-B5), kimlik hit semantigi (O-B6), numpy indeks, saygi eki/`에게` kacagi (Y-B2, belgeli genel kuralla), sembol (belgeli `[ÖLÇÜLMÜYOR]`).

## Kapi bulgulari (`real_check.py`; ret sebebi degil)

- **K-B1** #1 "6/6" sayisinin **4'u gommeden** geliyor: A3 (`장로 마르쿠스` ham "İhtiyar Marcus") ve A5 (`…by the mill.` ham "değirmenin yanında") hamda zaten hedefi tasiyor. #2 (≥2/6, olculen 4/6) pozitif kontrol olarak tutuyor ama #1 cumle basina katki olcmuyor. **Ham dogru -> gomulu yanlis sinifi kapida hic yok** (kural 10) -- Y-B1 tam bu sinifta 3/8. Oneri: #1 yalniz hamda hedef olmayan cumleleri saysin; yeni #8 negatif olcu (Y-B1).
- **K-B2** #3 "tekrar yok" olcusunun pozitif kontrolu yok: hamda tekrar var (ben olctum, [F] True) ama kapi bunu iddia etmiyor; model degisse bos gecer.
- **K-B3** #4 "Elder yok": fixture cumlesinin hami zaten "İhtiyar Marcus" (Elder yok) -> olcu bu girdide ateslenemez. Ateslenebildigini yalniz `장로` sozlukte YOKKEN gosterdim: `장로 Marcus` -> **"Elder Marcus"** (`model-olcum3-ham.txt` [M0]); cumle icinde ([M1]) sizma yok. Oneri: #4'e bu pozitif kontrol.
- **K-B4** `hedef.lower() in g.lower()` Turkce `İ` tuzagi: `"İhtiyar".lower()` = `i̇htiyar` (8 kodpoint) -> `İ`li hedef ciktida kucuk harfle gecse `in` sessizce False. Bugunku #1 hedefleri `Marcus`/`Değirmen` -> etkilenmiyor; `İ`li hedef eklenince #1 yanlis IHLAL verir. `test_bk_real_check_1_olcusu_lower_*`. Oneri: `casefold()` + `İ/ı` katlama.
- **K-B5** #7 yuk altinda 35.0 ms, yalitilmis 17.6 ms ([L]); esik 50. Kapi eszamanli testerlarla 2x oynuyor; bilgi.
- **K-B6** Kural 8: hedef dizeleri sabit, uygulamadan turetilmiyor -- temiz. Kapi yolu (`lookup`+`replace`) ile `lookup_segments` 1000 rastgele + G1 6 cumlede birebir ayni (`test_b1_lookup_segments_ile_*`, `test_bk_real_check_kapi_yolu_*`).
- **K-B7** Zincirin gercek cagirani (1ff6a8a `demo/canli_cevir.py`): `ContractViolation`/`TypeError` yakalanmiyor (Qt slot icinde istisna -> `_isliyor` True kalir, pencere "okunuyor ve çevriliyor…"da donar); `terimler = [h.target_term for h in hits]` kimlik hitlerini gomulen sayiyor (O-B6). Sef dosyasi; entegrasyon yukumlulugu (KRT O8 sinifi).

## Ozet

Kod paketi uyguluyor; ihlal yok. Asil risk kodun disinda: **paketin sinir listesi** (Y-B2) ve **fixture/yazarlik kurali** (Y-B1). Ikisi de sefe donen kalemler; implementer'a feedback yok.
