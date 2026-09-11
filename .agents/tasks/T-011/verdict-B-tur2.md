---
task: T-011
role: tester
round: 2
decision: onay
checks:
  - name: "taban 1 -- mypy --strict temiz (modul)"
    cmd: "python -m mypy --strict --explicit-package-bases src/translate/sozluk.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/tur2/taban-1-mypy.txt
  - name: "taban 1b -- mypy --strict temiz (implementer test dosyasi)"
    cmd: "python -m mypy --strict --explicit-package-bases tests/unit/translate/test_sozluk.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/tur2/taban-1b-mypy-test-dosyasi.txt
  - name: "taban 2 -- implementer birim testleri 453 passed"
    cmd: "python -m pytest tests/unit/translate/test_sozluk.py -q -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/tur2/taban-2-pytest.txt
  - name: "taban 3 -- real_check v4 TEMIZ 18/18 satir (#1b kazanc 4/6 [0,1,2,4]; #4a Elder sizmasi RAPOR; #8 17.3 ms)"
    cmd: "python .agents/tasks/T-011/real_check.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/tur2/taban-3-real_check.txt
  - name: "taban 4 -- kapsam %100 (433 ifade, 0 eksik)"
    cmd: "python -m pytest tests/unit/translate/test_sozluk.py -q -p no:cacheprovider --cov=src.translate.sozluk --cov-fail-under=95 --cov-report=term-missing"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/tur2/taban-4-kapsam.txt
  - name: "taban 5 -- tam takim 1897 passed"
    cmd: "python -m pytest tests -q -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/tur2/taban-5-tum-takim.txt
  - name: "tur-1 testlerim v3 kodunda (yeniden nisandan ONCE): 30 failed / 61 passed / 1 xfail -- sinif basina (a)8 (b)17 (c)4 (d)1"
    cmd: "python -m pytest .agents/tasks/T-011/tester_B/test_mercek_b.py -q -p no:cacheprovider --import-mode=importlib -rfEx --tb=line"
    exit_code: 1
    result: gecti
    evidence: tester_B_evidence/tur2/tur1-testleri-v3-kodunda-ham.txt
  - name: "mercek-B testleri (tur-1 yeniden nisanli 93 + tur-2 yeni 209 = 302 kosum, 95 fonksiyon): 301 passed + 1 xfail (paketin belgeli `검은 옷` siniri)"
    cmd: "python -m pytest .agents/tasks/T-011/tester_B -q -p no:cacheprovider --import-mode=importlib -rfEx --tb=short"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/tur2/mercek-b-testleri-tur2.txt
  - name: "mercek-B + sefin translate dizini birlikte: 1013 passed + 1 xfail (bariyer iki tarafta)"
    cmd: "python -m pytest tests/unit/translate .agents/tasks/T-011/tester_B -q -p no:cacheprovider --import-mode=importlib"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/tur2/birlikte-kosum-tur2.txt
  - name: "statik sonda 3 (modelsiz): JP 17/17 + KR 18/19 eslesiyor; `マルクス山`=1, `마르쿠스들이다`=1; 3-ek 0/6; liste disi KR 0/7; dogal KR 2/10 kacak; kanji ad+kanji ek 6/12, hiragana 5/10 kacak; betik gecisi/sembol/genislik; K2/K6 kotu kullanim; zincir `RüzgarDeğirmen`"
    cmd: "python .agents/tasks/T-011/tester_B/sonda3_statik_tur2.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/tur2/sonda3-statik-stdout.txt
  - name: "statik sonda 3 -- ham (CJK) ciktilar, UTF-8"
    cmd: "python .agents/tasks/T-011/tester_B/sonda3_statik_tur2.py  (ayni kosum, ham dosya)"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/tur2/sonda3-statik-ham.txt
  - name: "gercek model olcum M1-M7: zincir/betik gecisi ham-gomulu ciftleri; UNVAN 10 segment EN unvan ham 0/10 gomulu 1/10 (cumle ici 0/10 -> 0/10), ad 6/10 -> 10/10; KR dogal kacak 2/10 ad kaybi 0/2; JP kanji/hiragana ad + liste disi ek 3/4 ad kaybi; kapi #6 modelle; #5c and/or; #4b ham ihtiyar"
    cmd: "python .agents/tasks/T-011/tester_B/b_model_olcum_tur2.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/tur2/model-olcum-tur2-stdout.txt
  - name: "gercek model olcum -- ham ceviri metinleri (UTF-8; konsola basilmadi)"
    cmd: "python .agents/tasks/T-011/tester_B/b_model_olcum_tur2.py  (ayni kosum, ham dosya)"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/tur2/model-olcum-tur2-ham.txt
  - name: "depo dokunulmadi: src/tests/real_check/packet/fixtures git status BOS (yalniz `demo/sozluk_ornek.json` calisma kopyasinda baskasinin degisikligi, benim degil); sha256; HEAD 9c8d85f"
    cmd: "git status --short -- src tests demo .agents/tasks/T-011/real_check.py .agents/tasks/T-011/packet.md .agents/tasks/T-011/fixtures; sha256sum ..."
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/tur2/git-status-tur2.txt
  - name: "korluk: test_sozluk.py yalniz kendi testlerim (301+1) ve model olcumlerim (M1-M7) bittikten SONRA, yalniz test kalitesi icin acildi (an kaydi)"
    cmd: "date"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/tur2/test_sozluk-acilis-ani-tur2.txt
blocking_issues: []
---

# T-011 tur 2 -- Tester-B (mercek: kotu kullanim + sartname uyumu)

Karar: **ONAY**. Paket v3'un 20 ▲ maddesinin **hicbirinde olculmus ihlal yok**; docstring iddialari tutuyor; bes taban komutu yesil; kendi 302 kosumum yesil (1 xfail paketin belgeli siniri). Gercek zincirde (lookup -> gom -> translate) **gomme kaynakli bozulma yalniz paketin K4'te acikca gri bolge ilan ettigi sinifta** (unvan + ad, unvan sozlukte yok): 20 segmentte 2 bozulma / 11 ad kazanci -- olcum asagida, hedef tarafi duzeltme gorevinin paketine girecek. Tur-1 bulgularimin tamami (Y-B1, Y-B2, O-B1..O-B7, K-B1..K-B7) kodda ya da pakette kapandi; her biri v3 beklentisiyle yeniden nisanlandi.

Korluk: `delivery.md`, `evidence/`, `sef_dogrulama/`, `tester_A*` acilmadi. `test_sozluk.py` 21:20:17'de, kendi testlerim ve model olcumlerim bittikten sonra yalniz test kalitesi icin acildi (`tester_B_evidence/tur2/test_sozluk-acilis-ani-tur2.txt`). Tester-A eszamanli kosuyordu (model yuku: birlikte-kosumun ilk denemesinde kendi sure testim medyanla 60 ms'yi asti; testi 5 kosumun en kucugune cevirdim, O(n^2) mutant (472 ms) yine yakalanir -- gerekce test docstring'inde).

## Tur-1 testlerimin v3 koduna karsi durumu

92 kosumun **30'u dustu** (`tur1-testleri-v3-kodunda-ham.txt`). Her biri sinifladi ve `test_mercek_b.py` icinde `TUR-2 (x)` etiketiyle yeniden nisanlandi:

| Sinif | Sayi | Testler | Yeni beklenti |
|---|---|---|---|
| (a) duzeltilen bulgu pin'i | **8** | b3 kaynak terminator (O-B1) · b6 reddedilen komsu x4 (O-B5) · b6 NFD yer tutucu (O-B2) · b8 CV x2 (O-B4) | `ValueError` "kaynak cumle sonu" + parca 2->2 · zincir: `長老マルクス様` 2 hit, `장로마르쿠스니` 0 · `placeholders` NFC, onarim kopya eklemez · `ContractViolation` (TranslatorError) |
| (b) v3 kuraliyla degisen eski davranis | **17** | b6 kimlik cipasi · b7 JP 17 · b7 KR 21 · b7 sembol x14 | cipasiz `長老Marcus` -> `長老` eslesir · JP 17/17 (15 liste + `じゃない`/`なら` betik gecisi) · KR 20/21 (`인가` listede yok) · CJK terim + sembol betik gecisiyle sinir (5/5), Latin terim + sembol 0 |
| (c) fixture v3 (7 terim, unvansiz) | **4** | b1 list/tuple · b6 NFD indeks · bx repr · bk kapi yolu | `長老Marcus...` · `Marcus` ile · `terim_sayisi=7` · 6 hit |
| (d) `マルクス。` test verisi | **1** | b9 sema serbest listesi | `マルクス。` RED, `hedef ⊇ kaynak` ve kimlik serbest kaldi |

Yeniden nisan sonrasi: 93 kosum (b6 bir parametre ekledi), 92 passed + 1 xfail. Tur-2 yeni testleri `test_mercek_b_tur2.py`: 46 fonksiyon / 209 kosum. Toplam **95 fonksiyon / 302 kosum**.

## Sartname v3 satir satir (▲ maddeleri) <-> kod

| ▲ madde | Kod yapiyor mu | Fazlasi | Olcu |
|---|---|---|---|
| K1 JP saygi/kopula ekleri (15) | evet, `_JP_SAYGI_EKLERI` birebir; katakana/kanji/hiragana adda her ek ayri kimlik | ek listesi her betige uygulaniyor (betik gecisi zaten kapsar, zararsiz); zincir <= 2 JP'ye de (`さんたち`) | `test_t1_k1_jp_saygi_eki_her_biri_*` (15x3) |
| K1 KR ek listesi (+19) | evet, `_KR_EKLER_V3` birebir; ekten sonra sinir (`ek+침` 0) | -- | `test_t1_k1_kr_ek_her_biri_*` (37) |
| K1 zincir kurali | evet, `_ZincirDfs`; `windmills`/`millstones` 0, `windmill` 2, `長老マルクス` 2, `長老マルクスアイラ` 3, reddedilen aday sinir vermez | zincir icinde en uzun aday (`oldmillhouse` -> `old`+`millhouse`) -- belgeli | `test_t1_k1_paketin_*`, `test_t6_*` |
| K1 betik gecisi 6+8 | evet (fixture v3 ile 6 pozitif, 11 negatif); kimlik cipasi gerekmez (cipasiz sozlukle olculdu) | `M*` sag komsu sinir degil; sembol `S*` DIGER sinifinda (asimetri belgeli); Kana Ek bloklari `[ÖLÇÜLMÜYOR]` | `test_t1_k1_betik_gecisi_*`, `test_t3_*` |
| K1 trie IGNORECASE denk | evet, 3 sirada `Maẞer` | -- | `test_t1_k1_trie_anahtari_*` |
| K1 `マルクス山` "eslesmez" / `마르쿠스들이다` "3 ek" | **kod 1 hit / 1 hit -- implementer'in olcumu DOGRU**, ben de olctum. Paketin ic celiskisi: betik gecisi Katakana\|Han'i sinir yapar (`様` ile ayni cift); `이다` paketin kendi listesinde tek ektir (`들`+`이다` = 2). "Olcumun paketle celisirse olcumune uy, yaz" uygulanmis | -- | `test_t2_paket_celiskisi_*` |
| K2 `text`+`placeholders` NFC; tuple uzunluk/sira/bos oge korunur | evet; T-007 `modele_gider` 1, `_yer_tutuculari_onar` kopya eklemez; hit'siz NFD `is` | -- | `test_t1_k2_nfd_*`, `test_t1_k2_yer_tutucu_tuple_*` |
| K2 Segment kaynakli bicim hatasi `ContractViolation` | evet, `lookup_segments` ve `terimleri_gom` (str/bytes/int/None oge/dict); dogrudan `lookup` `TypeError` | -- | `test_t1_k2_segment_kaynakli_*` (6x), `test_t1_k2_text_str_degil_*` |
| K4 kimlik girdisi; docstring "sinir cipasi", "v3'te gerekmez", cagiran suzer | evet; docstring parcalar var; demo `source_term != target_term` suzuyor | -- | `test_t1_k4_*`, `test_t8_*` |
| K4 yazarlik kurali / gri bolge / K6 idempotens notu | docstring'de | -- | `test_t1_k4_docstring_*` |
| K5 hit yogunlugu (bitmap + olu hafiza), 8000 < 60 ms | evet: 8 dusmanca oruntu 18.6-22.8 ms (yalitilmis) | -- | `test_t5_*` (8) |
| K5 ozyineleme yok / kaynak <= 100 | trie govdesi ozyinelemeli ama K6 <= 100 sinirlar (paket "ya/ya" der); 2000 -> `ValueError` | -- | `test_t1_k5_2000_*` |
| K6 kaynak terminator (her yerde), hedef `Cc`, > 100, tip hatalari | evet; `kisa_terim_izni` terminatoru kurtarmaz (red once); `Mr. Marcus` de red | hedefte `Cf` (ZWSP) KABUL (D-A3 sinifi, belgeli degil -- D-B9) | `test_t1_k6_*` (11), `test_t4_k6_*` |
| Kapi v4 #5/#6 | kosuldu, 16/16 | -- | taban 3 |

**Eksik davranis (paket istiyor, kod yapmiyor): bulunmadi.** Uydurulmus davranislarin hepsi docstring'de belgeli.

## Bulgular

### YUKSEK -- yok

### ORTA (hepsi PAKET K1 listesi / K4 gri bolge; implementer'a feedback gerektirmez)

**O-B8 · JP ayni-betik ad + liste disi unvan eki -> 0 hit; gercek modelde 3/4 ad KAYIP (Y-B2'nin kalan yarisi).** Betik gecisi katakana adlari kurtardi; KANJI ad (JP oyunlarinin en yaygin ad bicimi) + kanji eki ve HIRAGANA ad + hiragana eki yalniz listeden gecebilir ve liste dar: `太郎先生/先輩/氏/公/王/隊長` 6/12, `ひかりくん/さま/せんぱい/せんせい/たん` 5/10 eslesmez (`sonda3` S4, `test_t2_jp_ayni_betik_*` 22 kimlik). Gercek model (M5, `model-olcum-tur2-ham.txt`): `太郎先輩が来た。` ham **"Tamir Bey geldi."**, `ひかりくんが来た。` / `ひかりさまが来た。` ham **"Bir ışık geldi."** (ad kayip, `ひかり` = isik); listedeki `太郎様` -> "Taro geldi.", `ひかりちゃん` -> "Hikari geldi." (dogru). **Oneri (paket K1, sef):** JP listesine `先生 先輩 氏 公 くん さま せんぱい せんせい` -- ayni mekanizma, her ek G6 tarzi negatif kontrolle (`先生` ile baslayan kelime: `先生方`? -> ekten sonra sinir kurali zaten korur).

**O-B9 · KR liste disi ekler (`에게서 한테서 예요 이에요 요 는데`) ve 3-ek yiginlari (`님께서는 님에게는 님한테도 님께서도 들에게는 님으로부터`) -> 0 hit; dogal NPC metninde 2/10, yigin agirlikli 6/10.** `sonda3` S2/S3, `test_t2_uc_ek_*` (7), `test_t2_liste_disi_kr_*` (8), `test_t2_kr_dogal_10_*`. 10 dogal cumlemde (`마르쿠스님, 어서 오세요.` ... `마르쿠스님은 마을 장로입니다.`) kacak: `마르쿠스님께서는 오늘 안 계십니다.` (3 ek) ve `아일라한테서 들었어요.` (`한테서`). Gercek model (M4): iki kacakta da ham ad **zaten dogru** (kayip 0/2); hit olan 8'de gomme kazanci 2/8 ("Markos" -> "Marcus" x2). `에게서` = `에게`+`서` (`서` listede yok); `예요` listede yok. **Oneri (paket K1, sef):** listeye `에게서 한테서 예요 이에요 요 는데`; `님께서는` (saygili ozne+konu, NPC konusmasinda yaygin) icin zincir derinligi 3 sef karari -- olcumum: dogal metinde 1/10.

**O-B10 · UNVAN OLCUMU (Y-B1 gri bolgesi; hedef tarafi duzeltme paketi icin ham sayilar).** 10 unvan+ad segmenti (JP `長老/隊長/村長/騎士/王女` + KR `장로/대장/촌장/기사/공주`), adlar-yalniz fixture v3, gercek model (M3, `model-olcum-tur2-ham.txt`):
- **Ingilizce unvan: HAM 0/10, GOMULU 1/10** (`장로 Marcus` -> "Elder Marcus"; ham "İhtiyar Marcus" -- kapi #4a'nin raporladigi tek sinif).
- **Turkce unvan: ham 6/10 -> gomulu 4/10.** Kayiplar: (1) M3-5 "Elder" (yukaridaki), (2) **M3-8 `기사 아일라` ham "Şövalye Ayla." -> gomulu `기사 Ayla` "Şerif Ayla."** -- YANLIS Turkce unvan, "Elder->İhtiyar" tablosu bunu YAKALAMAZ; (3) M3-0 `長老Marcus` "İhtiyar" -> "Yaşlı" (esanlamli, kayip degil).
- **Ad dogru: ham 6/10 -> gomulu 10/10.**
- Cumle ici 10 varyant (M3b): Ingilizce unvan ham 0/10 -> gomulu **0/10**; ad 3/10 -> 10/10; unvan cevirisi oynak ama yon tutarsiz (M3b-4 "Kraliçe" -> "Prenses" DUZELDI, M3b-6 "Büyük Ayla kasabasında" -> "Başkan Ayla bir köyde" ikisi de yanlis).
- **Sonuc:** 20 segmentte gomme kaynakli unvan bozulmasi **2/20** (1 Ingilizce sizma + 1 yanlis Turkce unvan), ad kazanci **11/20**. Bozulma sinifi cumle ici degil yalniz-unvan+ad segmentlerinde (menu/isim etiketi bicimi). Hedef tarafi gorevine: yalniz "Elder" degil, **unvan kelimesinin degismesi** izlenmeli (ham ile gomulu unvan farkli -> uyari); tablo tek basina yetmez.
- Neden ret degil: paket K4 bu sinifi acikca gri bolge ilan ediyor, kapi #4a rapor, cozum ayri gorevde; implementer'in modulde duzeltebilecegi bir sey yok.

### DUSUK

- **D-B7** Sembol asimetrisi Latin tarafinda kaldi: `マルクス→アイラ` 2 hit, `Marcus→Ayla` 0/0; `Marcus♪`/`Marcus$` 0 (docstring belgeli). `test_t3_sembol_asimetrisi_*` (14). Oneri: `S*` de sinir (tur-1 D-B1).
- **D-B8** Genislik katlanmaz: `ﾏﾙｸｽ` (yarim genislik) ve `Ｍａｒｃｕｓ` (tam genislik; JP oyunlarinda yaygin) `マルクス`/`Marcus` ile eslesmez; T-004 girdiyi NFKC'lemez. Yazar kaynagi OCR'daki genislikle yazmali. `[ÖLÇÜLMÜYOR]` adayi (docstring'e). `test_t3_genislik_*`.
- **D-B9** Hedefte `Cf` (ZWSP U+200B) semadan gecer (`Cc` degil) -> model ZWSP'li terim gorur; web'den kopyalanan terime yapisabilir. `test_t4_k6_*`. Oneri: `Cf` de red ya da belge.
- **D-B10** Elle kurulan `TermHit.target_term` K6'yi atlar: `Marcus.` gomulur, T-007 parca 1 -> 2 (paket K2 yalniz bos/str-degil der). Store uzerinden imkansiz; belge. `test_t4_elle_kurulan_hit_*`.
- **D-B11** Gomulu segment tekrar zincire: fixture ile sessiz sabit (kimlik hit 1, CV yok, ceviri ayni -- M7 2/2); `hedef = BASKA terimin kaynagi` (`マルクス->Marcus` + `Marcus->Marküs`) ikinci geciste **sessiz kayma** -- docstring yalniz `hedef ⊇ kaynak` buyumesini aniyor; ayni kuralin ikinci yuzu. `test_t4_gomulu_segment_tekrar_*`.
- **D-B12** `windmill` -> `RüzgarDeğirmen` (paket: yazar ikisini de istedi): model ayiriyor ("Rüzgar Değirmen dönüyor.") ama iyelik eki kayboluyor (ham "Rüzgar değirmeni dönüyor."); cins isim sozlugu K4 uyarisi. `windmills` 0 hit -> ham "Rüzgar değirmenleri dönüyor." DOGRU; tur-1 sinifi `Rüzgarmills` -> "Rüzgarmills dönüyor." (bozuk) -- zincir kurali dogru sinifi koruyor (M6). `test_t6_zincir_windmill_*`.
- **D-B13** Kaydirilmis segment listesi (`hits(A)` + `gom(B)`, B permutasyon): ayni terim ayni konumdaysa K2 tam-esitlik gecer, sessiz (cagiran hatasi, sozlesme goremez); farkli konumda CV. `test_t4_kaydirilmis_*`.
- **D-B14** `Marcus_2` 1 hit (`_` Pc -> P*; D-A5 belgeli): `PLAYER_NAME` bildirilmemisken `Oyuncu_NAME`. K3 cagiran bildirir. `sonda3` S6.
- **D-B15** `장로마르쿠스` (bosluksuz KR, gercek metinde olmaz) fixture v3 ile 0 hit -> ham "Elçi Markos." (M1-6); unvanli sozlukle zincir 2 hit. Bilgi.

### Betik gecisi kotu kullanim (K4 cins-isim uyarisina ragmen) -- bozulma YOK

`ゴブリン->Goblin`, `ポーション->İksir`, `エルフ->Elf` (M2): `ゴブリンキング` 0 hit (Katakana|Katakana) -> ham "Goblin King geldi." (Ingilizce, gomme yardim edemez); `ゴブリン王` 1 hit -> `Goblin王` -> **"Goblin Kralı geldi."** (ham "Kral Goblin geldi."); `ポーション瓶` -> `İksir瓶` -> **"İksir şişesini aldım."** (ham "Potasyon şişesini aldım." YANLIS); `ポーションを` -> "İksir'i aldım." (ham "Oturumları topladım." COP); `エルフ族の村` -> "Elf köyüne gittim." (ham "Elfler köyüne gittim."); `マルクス家` -> "Marcus'un evi." (ham "Bu da Marks ailesinin evleri."). 0/5 bozulma, 2/5 net duzelme -> `Goblin王` gomulmesi **istenen davranis**; paketin `マルクス山` celiskisinde implementer'in yorumu dogru. `test_t3_katakana_terim_kanji_komsu_*` (9).

### Zincir + gercek model (M1)

`長老マルクス` -> `長老Marcus`: ham **"İhtiyar Marks."** -> gomulu **"Yaşlı Marcus."**; cumle ici "İhtiyar Marks geldi." -> "İhtiyar Marcus geldi." `マルクスアイラ` -> `MarcusAyla` (bitisik Latin): ham "- Hayır, hayır." (cop) -> **"Marcus Ayla."** -- model bitisik Latin adlari 4/4 ayirdi (`MarcusAylaが来た` "Marcus Ayla geldi.", `長老MarcusAyla` "Yaşlı Marcus Ayla.", KR `MarcusAyla가` "Marcus Ayla geldi."); ham hepsinde "Marks Island"/"Markus Island". Kontrol `マルクスとアイラ` -> "Marcus ve Ayla geldi." (ham "Marks ve Ayala"). Ingilizce sizma 0/8.

### K2/K6 kotu kullanim (sonda3 S6/S7, `test_t4_*`)

`placeholders=(" ",)` -> hit'ler etkilenmez, gom dogru · `placeholders=(terim,)` -> 0 hit, elle hit CV · `placeholders=("ル",)` -> `マルクス` dusur, `アイラ` kalir · `kisa_terim_izni` + `.`/`。`/`？` -> RED (terminator once) · `kisa_terim_izni` + `{` -> KABUL (yalniz `{}` gibi P* komsuda eslesir) · `{0}`/`%s` KAYNAK olarak KABUL (bildirilmemis `{0}マルクス` -> `SıfırMarcus`, bildirilmis korunur) · 100 kodpoint + izin KABUL · `not: null` KABUL, `kisa_terim_izni: 1` RED · ayni hit iki kez -> CV "ortusuyor".

## Kapi bulgulari (`real_check.py` v4; ret sebebi degil)

- **K-B8 · #4b `"ihtiyar" in _kat(bg)` MUTLAK sart, kirilgan.** Model ayni unvani `İhtiyar`/`Yaşlı` arasinda oynatiyor (M3-0 JP `長老` "İhtiyar" -> "Yaşlı"; KR tarafinda bugun ham=gomulu="ihtiyar" -- M6-4b). Model/ayar degisince ham da gomulu de "yaşlı" olur, kapi yanlis IHLAL verir. Oneri: `"ihtiyar" in gomulu` yerine "hamdaki unvan kelimesi gomuluda korunur" (goreli) ya da `{ihtiyar, yaşlı}` kumesi. `test_t7_kapi_4b_*`.
- **K-B9 · #5c `or` gevsek:** `"Marcus" not in h_jp or "Marcus" not in h_kr` -- iki dilden biri hamda adsizsa gecer, #5b ikisini de ister; dil basina pozitif kontrol (`and`) olmali. Bugun JP="Bay Marks geldi." KR="Markos'a söyledim." ikisi de adsiz -> `and` de gecer (M6-5c). `test_t7_kapi_5c_*`.
- **K-B10 · #6a/#6b statik; zincir sinifinin GERCEK zincirdeki amaci (kismi gomme bozar, 0 hit hami korur) kapida olculmuyor.** Olctum (M6): `windmills` 0 hit -> ham "Rüzgar değirmenleri dönüyor." DOGRU; tur-1 kismi `Rüzgarmills` -> "Rüzgarmills dönüyor." BOZUK; `windmill` 2 hit -> "Rüzgar Değirmen dönüyor." (iyelik kaybi). Oneri: #6c gercek modelle `windmills` ham ciktisinda "değirmen" var (kural 10 pozitif kontrolu: `Rüzgarmills` girdisinde yok).
- **K-B11 · #4a yalniz KR;** JP `長老マルクス` (#1 cumle 0) icin Ingilizce sizma raporu yok. Olctum: JP tarafinda 0/10 (M3), yalniz `長老Marcus` "İhtiyar"->"Yaşlı". Bilgi; #4a JP satiri eklenebilir.
- **K-B12 · #1b kazanc 4/6 = [0,1,2,4]** (`長老マルクス`, `マルクスが…`, `水車小屋…`, `방앗간을…`); 3 (`장로 마르쿠스`) ve 5 (Ingilizce) hamda zaten "Marcus" -- benim M3/M3b olcumumle tutarli. Kural 10 (pozitif kontrol >= 2) saglaniyor; kural 8: hedef dizeleri sabit literal, `_kat` Turkce katlamasi dogru (`test_t7_kapi_kat_*`).
- **K-B13 · #8 17.3 ms** (tur-1 yuk altinda 35.0); butce 50. Kendi dusmanca 8 orunt 18.6-22.8 ms.
- **K-B14 · Calisma kopyasinda `demo/sozluk_ornek.json` degismis (M, commit edilmemis)** -- benim degil; icerik: `Marcus` kimlik girdisine v3 notu, biçim genisletme. Sef dosyasi; teslim kapsamina giriyorsa commit'e dikkat (PROTOKOL commit disiplini).

## Demo (K-B7 kapanisi, statik denetim)

`demo/canli_cevir.py`: `cevir` cagrisi `except TranslatorError` ile sarili, hata yolunda `bitti.emit` -> `_isliyor = False` (pencere donmaz); sayac `h.target_term != h.source_term` ile kimlik hitini suzuyor; `GlossaryStore` sema hatasi baslangicta acik `ValueError` (yorum belgeli, kabul). `test_t8_*` (2). PySide6 import edilmedi.

## Test kalitesi (implementer; `test_sozluk.py` 21:20:17'de acildi)

- 164 fonksiyon / 453 kosum, 100% kapsam. Beklentiler literal; ozel mekanizma (`_betik`, `_anahtar`, `_ZincirDfs`) import edilmiyor (kural 7'ye uygun: davranis kancalaniyor). Totoloji bulmadim.
- `pytest.raises` **match'siz 26 yer**: 5 `TypeError` (`lookup("…", "{0}")`, `GlossaryStore(None)`, ...) -- `isinstance` bekcisi kaldirilsa `_nfc(None)`/`Path(None)` yine `TypeError` -> test ayiramaz (tur-1 notu gecerli); ~21 `ContractViolation` -- girdiler tek nedeni tetikliyor (aralik/dilim/ortusme/tip), yalniz `start-negatif` (-1, 4) iki nedeni birden (aralik + dilim) -- kabul, `match` keskinlestirir.
- Sure testleri: `_izleyici_payi` 4x yalniz `sys.gettrace()` doluyken (kapsam kosumu); duz kosumda 1x. **Mutant M45 (bitmap yerine dogrusal kabul listesi)** yalniz `test_k5_sure_8000_*` ile yakalaniyor: tur-1 olcumu 472 ms, esik 60 (duz) / 240 (kapsam) -> **iki kosumda da yakalanir**, pay 8x/2x. Kabul edilebilir; yapisal kanca (kural 7) daha kirilgan olurdu. Risk: `_medyan_ms` 5 kosumun medyani, eszamanli model yuku altinda yanlis-negatif (dogru kodda dusme) verebilir -- ben bunu kendi testimde yasadim (birlikte-kosum ilk deneme) ve `min`e cevirdim; implementer'a oneri (feedback degil): `min` ya da n=9.
- Hic test edilmeyen siniflar (benim testlerim kapatir): JP ayni-betik liste disi ek (O-B8), KR liste disi/3-ek olcumu (O-B9), sembol asimetrisinin Latin yuzu (D-B7), genislik (D-B8), `Cf` hedef (D-B9), elle hit K6 atlamasi (D-B10), `hedef = baska kaynak` kaymasi (D-B11), kaydirilmis liste (D-B13), dusmanca 8 zincir orunt (T5; implementer 2 orunt).

## Ozet

Kod paket v3'u uyguluyor; ▲ maddelerinde ihlal yok; tur-1 bulgularimin tamami kapandi. Kalan risk kodun disinda ve olculmus: **(1)** K1 listeleri ayni-betik JP/KR adlar icin hala dar (O-B8/O-B9; dogal KR 2/10, JP kanji+`先輩`/hiragana+`くん` modelde ad kayip) -- paket kalemi, mekanizma hazir; **(2)** unvan gri bolgesi 20 segmentte 2 bozulma / 11 kazanc, bozulma "Elder" sizmasindan genis ("Şövalye" -> "Şerif") -- hedef tarafi gorevinin paketine olcum olarak. Implementer'a feedback yok.
