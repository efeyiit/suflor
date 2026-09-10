---
task: T-004
role: tester
round: 6
decision: onay
checks:
  - name: "mypy --strict temiz"
    cmd: "python -m mypy --strict src/ocr/normalizer.py src/ocr/presets.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r6-mypy.txt
  - name: "urun kabul testleri -- 124 passed (tur 5'te 98'di; K28 olcu 1-8 + K30 x2 + K31 x3 + K32 x2 eklendi)"
    cmd: "python -m pytest tests/unit/ocr/test_normalizer.py -q"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r6-pytest-urun.txt
  - name: "K29 kapisi -- saflik/determinizm + docstring'de anilan her test adi var"
    cmd: "python .agents/tasks/T-004/purity_check.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r6-purity.txt
  - name: "sefin olcu kiti kendi sagligini siniyor -- KIT SAGLIGI: TEMIZ; uc on ayarda ayrisma/kimlik/kapsam/sira/sayi = 0"
    cmd: "python .agents/tasks/T-004/olcu_kiti.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r6-olcu-kiti.txt
  - name: "TESTER-B karar-uyumu saldiri seti TUR 6 -- 181 passed (116 onceki + 55 yeni karar-uyumu + 10 mutant sondasi)"
    cmd: "python -m pytest .agents/tasks/T-004/tester_B -q"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r6-pytest-tester_B.txt
  - name: "K28 MUTANT SONDASI -- kontrol + 8 mutant (M3/M4/M5/M11/M12/M13a/M13b/M15); kitin GORMEDIGI BES SINIFIN BESI DE kendi diferansiyelimde kiriliyor"
    cmd: "python -m pytest .agents/tasks/T-004/tester_B/test_k28_mutant_sondasi_tur6.py -q -s"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r6-mutant-sondasi.txt
  - name: "K28-K32 karar uyumu -- 55 test: imzalar, AST, tarihsel karsilastirma, K29 bagimsiz tarama, K30/K31/K32 kendi girdilerimle"
    cmd: "python -m pytest .agents/tasks/T-004/tester_B/test_karar_uyumu_tur6.py -q"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r6-karar-uyumu-tur6.txt
  - name: "yeni karar-uyumu dosyasinin DISLERI -- sekiz mutant agacinda kosuldu; M4 2, M5 5, M11 1, M13b 1 test kiriyor, kontrol TEMIZ"
    cmd: "python .agents/tasks/T-004/tester_B_evidence/r6-karar-uyumu-dis-matrisi.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r6-karar-uyumu-dis-matrisi.txt
  - name: "K29 kapisinin DISLERI -- uc tur bayat atif enjekte edildi (duz ad, satir-sarmali ad, ciplak '_' on-ek); hem kendi taramam hem purity_check ucunu de gordu"
    cmd: "python .agents/tasks/T-004/tester_B_evidence/r6-k29-kapi-disleri.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r6-k29-kapi-disleri.txt
  - name: "TARIHSEL -- K28 oncesi surumle (74256d8) govde karsilastirmasi: YENI tanim yalniz _raw_query_pair; govdesi degisen yalniz _group ve _normalize_impl"
    cmd: "python .agents/tasks/T-004/tester_B_evidence/r6-degismedi-git.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r6-degismedi-git.txt
  - name: "BULGU N1/N2 olcumu -- olcu 5 fixture'inin sag tarafi IKI sinirda da TEK BLOKLU; olcu 3b fixture'i OKUMA SIRASINDA"
    cmd: "python .agents/tasks/T-004/tester_B_evidence/r6-olcu-iddialari.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r6-olcu-iddialari.txt
  - name: "regresyon -- pytest tests 821 passed; kor tester takimi IKI kosumda da 623 passed, 1 xfailed, 0 KIRIK"
    cmd: "python -m pytest tests -q  ve  python -m pytest .agents/tasks/T-004/tester_A tester_B tester_C -q --tb=no"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r6-kor-takim.txt
blocking_issues: []
notes:
  - "N1 (orta, KARARDA -- urunde degil): 'M5 -> olcu 2, 5 ve 6 kirilmali' cumlesinin 'olcu 5' yarisi TUTMUYOR. olcu5_fixture() IKI sinir uretiyor ve IKISINDE DE aday (sag taraf) TEK BLOKLU -- (3,) ve (6,). Tek bloklu adayda replace(nxt, bbox=blocks[ilk].bbox) ile nxt'in KENDISI ayni bbox'i tasir, yani olcu 5 sag taraf ikamesini YAPI GEREGI olcemez. Olctum: M5 olcu 2'nin uc varyantini ve olcu 6'nin uc on ayarini kiriyor, olcu 5'i KIRMIYOR. Kitin derleminde coklu_sag >= 500 alt siniri VAR; olcu 5'in fixture'inda karsiligi SIFIR (kitin selftest'i de yalniz coklu_sol yazdiriyor). Bu, sefin bes turdur tekrar eden S4.6/4 sinifinin SAG TARAFTAKI kopyasidir. Onerim: olcu5_fixture'a en az bir sinirda COK BLOKLU aday (zincirleme hyphen ile gelen nxt) eklenmesi -- kit dosyasi sefe ait, ben degistirmedim."
  - "N2 (dusuk, ENV.MD'DE -- kararda degil): env.md TUR 6 / MERCEK B/1 'M4 ... -> olcu 3/3b ve kit geo kirilmali' diyor. olcu3b_fixture()in bloklari OKUMA SIRASINDA dizili (y = 0, 20, 40, 60, 90), yani max(source_blocks) ile okuma_sirasi(...)[-1] AYNI blogu verir ve M4 orada AYRISMAZ. Olctum: M4 olcu 3'un IKI on ayarini, olcu 5'i ve olcu 6'nin uc on ayarini kiriyor; olcu 3b'yi KIRMIYOR. Kararin KENDI metni ('olcu 3 ve 6 kirilmali') DOGRU -- sapan env.md'nin ozeti. olcu 3b'nin isi zaten off-by-one (uclu kuyruk), M4 degil."
  - "N3 (orta, KAPI KAPSAMI): M15 (miras sorgusunu YANLIS params ile soran mutant) DORT kabul komutunun DORDUNU de, 124 urun testinin HEPSINI ve kitin bes kanalinin HEPSINI TEMIZ geciyor. Kendi diferansiyelim 1844 ayrisma buluyor (DIALOGUE 270 / TOOLTIP 543 / SUBTITLE 1031; bolumleme degismiyor, yalniz miras karari kayiyor) -- sefin 'kor takimda ek kirik 0' olcumunu yeniden urettim. Tur 6'dan sonra bu sinifi tutan TEK sey tester_B'nin sondasi olur ve o bir kabul komutu DEGILDIR. Onerim: tests/ altina TEK bir davranissal test -- dialogue'da h=18, uzunluk-TEK-engelli bir sinirda gap=12 (MENU esigi 0.5*18=9 -> 'gap', DIALOGUE esigi 0.8*18=14.4 -> None); dogru uygulamada kuyruk 'Ada' miras alir, MENU tablosuyla soran uygulamada None kalir."
  - "N4 (dusuk, KAPI KAPSAMI): M12 sinifinda (adim 1-4 yardimcisini degistiren mutant) kitin adim1_4'u DENETLENEN modulun kendi _merge_hyphenated'ini cagirdigi icin kimlik kanali mutantla BIRLIKTE kayiyor -- sefin ilan ettigi sinir dogrulandi (13.088 ayrisma, kit UC on ayarda TEMIZ). Bu ORNEK urun testi test_k5_buyuk_harfle_baslayan_sonraki_satir_birlesmez tarafindan yakalaniyor, yani sinif tamamen acik degil; ama kapi o TEK kosula bagli -- ayni yardimcinin bbox/source_blocks tarafini degistiren bir mutant icin ayni guvence yok."
  - "KAPSAM BEYANI: kararin K28-kok / K30 / K31 / K32 maddeleri hem docstring'e HEM known_gaps'e yazilmayi sart kosuyor. known_gaps delivery.md'de ve o dosya benim mercegime KAPALI (env.md 'Okumaman gerekenler') -- bu maddelerin DOCSTRING + TEST yarilarini dogruladim, known_gaps yarisini DOGRULAMADIM. Sefin elle denetlemesi gerekir."
  - "Gorev tanimi 'BES YENI MUTANT' diyor ama alti kalem sayiyor (M4, M5, M11, M12, M13, M15); M13'un kendisi iki ayri nokta (MENU on ayari / apply_inheritance=False yolu). Yedi mutasyon noktasinin yedisini de kurdum, arti sefin 'esdeger' dedigi M3'u olcum icin geri getirdim (kaldirmadim -- ayri dosyada, tur 5 sondasindan cikmis halde kaliyor)."
  - "M3 hakkinda: sefin 'davranissal olarak ESDEGER' nitelemesi DOGRU (3000 girdi x 4 on ayar x 2 kip = 24.000 kosumda 0 ayrisma); 'yeniden nisanlanirsa OLU mutant olur' nitelemesi EKSIK -- kitin KIMLIK kanali (2387/1350/826) ve 10 urun olcusu onu yine de kiriyor. Bu, K28'in 'source_blocks AYNEN korunur' onkosulunun (V2) gercekten disli oldugunun kanitidir."
  - "Tabanin degistigi: sefin verdigi kor-takim tabani 388 passed idi; tur SIRASINDA tester_A ve tester_C kendi tur-6 dosyalarini ekledi, toplam 623 passed + 1 xfailed oldu. IKI ayri kosumda da KIRIK 0 -- regresyon yok. tester_C'nin yuk altinda kararsiz oldugu bilinen olcek testleri bu iki kosumda da gecti."
---

# Tester-B · Karar uyumu · T-004 Tur 6 — **ONAY**

**Karar: onay.** `sef_karari-tur6.md` (sürüm 8) K28–K32'nin kodda ve testlerde
bulabildiğim her satırı **birebir var**; uydurulmuş davranış bulamadım.
Bloke edici bulgu yok. Dört not var ve **ikisi ürünle ilgili değil** — şefin
kendi ölçü metnindeki iki iddia tutmuyor (N1, N2), ikisi de kapı kapsamı
uyarısı (N3, N4).

---

## 1. Bu turda ne yaptım

Turun ilk yarısı (bayat kapı aletlerinin yeniden nişanlanması) daha önce
bitirilip commit edilmişti: `test_karar_uyumu_tur5.py:556`'nın AST beklentisi
`_group_rejection_reason(*_raw_query_pair(tail, nxt, blocks), params,
ignore_length=True)` biçimine, `test_k23_mutant_sondasi_tur5.py`'nin M1/M2
desenleri yeni satıra nişanlandı, M3 o dosyadan çıkarıldı. Bu turda o işe
dokunmadım; üstüne **iki yeni dosya** yazdım:

| Dosya | Ne | Test |
|---|---|---|
| `tester_B/test_k28_mutant_sondasi_tur6.py` | sekiz mutant × üç bağımsız ölçüm | 10 |
| `tester_B/test_karar_uyumu_tur6.py` | K28–K32'nin madde madde denetimi | 55 |

`tester_B` toplamı 116 → **181 passed**.

### Sondanın yöntemi

`src/` altına hiçbir şey yazılmadı. Her mutant için `tmp_path` altında ayrı
bir ağaç kuruldu (`src/`, `tests/`, şefin `olcu_kiti.py` + iki `conftest.py`),
kopyadaki `normalizer.py`'ye **tek bir cerrahi mutasyon** uygulandı ve **üç
bağımsız ölçüm** yapıldı:

1. **Davranışsal diferansiyel** — kendi üreticim (sabit tohum; kitin
   derleminden ve tur 5 sondasından farklı), **3000 girdi × 4 ön ayar × 2 kip**
   (`normalize` ve `_normalize_impl(..., apply_inheritance=False)`) = **24.000
   koşum**. Referans, aynı harness'ta koşan mutasyonsuz kontrol kopyası.
   `MENU` ön ayarı ve miras-kapalı kip **bilerek** dahil — kit ikisini de
   koşmuyor.
2. **Şefin kiti** — mutant ağacında `olcu6_kos` üç ön ayarda; beş kanalın
   (geo / kimlik / kapsam / sıra / sayı) hangisinin kırıldığı kaydedildi.
   "Kit bunu görmez" iddiasını **kör kabul etmedim, ölçtüm**.
3. **Ürün ölçüleri** — mutant ağacında `pytest tests/unit/ocr/
   test_normalizer.py`; kırılan test adları toplandı.

Üreticim şu sınıfları bilerek üretir: ard arda uzunluk-tek-engelli sınırlar
(zincirleme miras → M11), tire ile biten satır + **büyük harfle** başlayan
devam satırı (→ M12), `gap = dy − h` 0–22 aralığında dağıtılmış boşluklar
(TOOLTIP 5,4 · MENU 9,0 · DIALOGUE 14,4 · SUBTITLE 18,0 eşiklerinin **dördü
de** straddle edilir → M15), yalnız-etiket blokları, ikinci konuşmacı,
eşik-altı bloklar, yozlaşmış (`w<=0`/`h<=0`) geometri, negatif koordinat ve
girdilerin ~yarısında `shuffle` (→ M4).

---

## 2. Mutant sonuçları — ham tablo

`tester_B_evidence/r6-mutant-sondasi.txt`

```
mutant                        davranis   kit (geo/kim/kap/sir/say)      urun olculeri
KONTROL                              0   TEMIZ x3                       0 kirik
M3  tail -> current                  0   kimlik 2387/1350/826           10 kirik
M4  indeks sirasi                  342   geo 1668/2672/3163              6 kirik (olcu3 x2, olcu5, olcu6 x3)
M5  sag taraf nxt kalir            259   geo 2208/3957/4721              6 kirik (olcu2 x3, olcu6 x3)
M11 goruntu gecisi ters yon       1204   TEMIZ x3                        1 kirik (olcu8)
M12 adim3 yardimcisi (isalpha)   13088   TEMIZ x3                        1 kirik (test_k5_*)
M13a yalniz MENU                  6000   TEMIZ x3                        1 kirik (test_k27_*)
M13b yalniz miras-kapali          2988   TEMIZ x3                        1 kirik (test_k23_invariant_b1_*)
M15 yanlis params                 1844   TEMIZ x3                        0 kirik
```

**Şefin dört "kit görmez" iddiasının dördü de doğrulandı** (M11, M12, M13,
M15 — kit üç ön ayarda `TEMİZ`), ve **beşinin beşi de** benim davranışsal
diferansiyelimde kırılıyor. Ölçtüğüm sayılar şefin sayılarıyla aynı
büyüklükte (şef: M11 1322 · M12 3672 · M13 2422 ve 12 · M15 398/516; ben:
1204 · 13.088 · 6000 ve 2988 · 1844 — üreticiler farklı, yön aynı).

Mutant izolasyonu da ayrıca pinlendi ve tutuyor:

- M11 yalnız `acik` kipte ve `MENU` dışında ayrışıyor (görünüm geçişi başka
  yerde koşmuyor);
- M13a yalnız `MENU`'de, üç gruplayan ön ayarda **0**;
- M13b yalnız `kapali` kipte, `acik` kipte **0** — yani K23'ün makine
  denetimini yalancı yapan sınıf;
- M15 yalnız `acik` kipte; `kapali` (bölümleme) kipinde **0** — bölümlemeye
  sızmıyor, K23 ihlali değil.

---

## 3. K28'in her cümlesi — tek tek

`tester_B_evidence/r6-karar-uyumu-tur6.txt`, `r6-karar-uyumu-dis-matrisi.txt`

| Kararın cümlesi | Nasıl doğruladım | Sonuç |
|---|---|---|
| "Modül düzeyinde `_raw_query_pair(tail, nxt, blocks)`" | `__module__`, `inspect.signature`, üst düzey AST tanımı | **var** |
| "sol = okuma sırasında SON, sağ = okuma sırasında İLK" | 4000 rastgele çift, kendi referansımla + kitle çapraz | **tutuyor** |
| "OKUMA SIRASI = `(bbox.y, bbox.x, girdi indeksi)`" | `source_blocks=(2,0,1)` + üçünde de eşit `(y,x)` ama **farklı `w`** ile doğrudan çağrı → ikili anahtar `blocks[1]` verirdi, kod `blocks[2]` veriyor; ayrıca lambda AST'si | **üçlü anahtar gerçekten yazılı** |
| "`source_blocks[-1]` / `[0]` KULLANILMAZ" | AST: `.source_blocks` üzerinde sabit indeksleme ve `max/min` kısayolu yok | **yok** |
| "İKAME YALNIZ `bbox`'a dokunur; `speaker`, `text` **ve `source_blocks`** aynen korunur" | AST (iki `replace`, ikisinde de tek kwarg `bbox`) + davranışsal alan alan | **tutuyor** |
| "Hiçbir birleşik `_Item` bbox'ı bu sorguya girmez" | uçtan uca: 500+ miras sorgusunun **iki** bbox'ı da özgün listedeki bir bloğa birebir eşit (çok bloklu aday >50) | **tutuyor** |
| KAPSAM: "ana birleştirme kararı `current`'ın BİRLEŞİK bbox'ını kullanmaya devam eder" | kitin `ham_ikame_sizmis`'ini kullanmadan, kendi **kapsama** denetimimle 200+ çok bloklu bölümleme sorgusu | **tutuyor** |
| "`_group(items, params, *, blocks=(), apply_inheritance=True)`" | `inspect.signature`: parametre sırası, `KEYWORD_ONLY` türü, varsayılanlar, anotasyonlar; `_group([], params)` çalışıyor | **birebir** |
| "`_normalize_impl` `blocks=blocks` geçmek ZORUNDADIR (özgün liste)" | davranışsal indeks-kayması testi: başa eşik-altı blok → `source_blocks` `(1,),(2,),(3,)`, miras korunuyor, sorgu bbox'ları doğru bloklara düşüyor | **tutuyor** |
| "`blocks=()` varsayılanı … aksi hâlde `IndexError` — bilinçli, patlama gecikmeli" | üç şık ayrı ayrı: boş liste, uzunluk-tek olmayan sınır (patlamıyor, sessiz yanlış da üretmiyor), uzunluk-tek sınır (`IndexError`), `blocks` verilince miras uygulanıyor | **tutuyor** |
| "Bölümleme döngüsünün içinde hiçbir `replace(...)` yazılmaz" | AST: `_group`'un **tamamında** tek `replace`, o da görünüm geçişinde, tek kwarg `speaker` | **tutuyor** |

### Tarihsel denetim — "değişmedi" gerçekten değişmedi mi

`tester_B_evidence/r6-degismedi-git.txt`

K28 **öncesi** sürümle (`74256d8`) docstring'siz gövde karşılaştırması:

- **Yeni tanım:** yalnız `_raw_query_pair`. Silinen tanım: yok.
- **Gövdesi değişen:** tam olarak `_group` ve `_normalize_impl`. Başka hiçbir
  şey.
- `_Item`, `normalize`, `_should_group`, `_group_rejection_reason`,
  `_merge_hyphenated`, `_extract_speakers`, `_is_noise`,
  `_collapse_intraline`, `_union_rect`, `_split_speaker_label`,
  `_validate_confidences` — **gövdeler birebir aynı**; büyüyen yalnız
  docstring'ler (K29–K32'nin belgeleme maddeleri).

Bu, "docstring değişti ama gövde de değişti" sınıfını kapatıyor ve şefin "tur
6'nın TEK kod değişikliği K28'dir" ilanını doğruluyor.

Ayrıca: `normalize`'ın gövdesi **tek** `return _normalize_impl(blocks, preset)`
— sürüm 3'te zorunlu kılınıp tur 6'da **geri çekilen** "`apply_inheritance=
True`'yu açıkça yaz" maddesi gerçekten uygulanmamış (Z1 doğru çözülmüş).
`_Item` alanları `(text, bbox, speaker, source_blocks)`, tipleriyle birlikte
aynı. `_should_group` hâlâ tek satırlık devretme (`_group_rejection_reason(a,
b, params) is None`) ve 12.000 çiftlik yeni tohumlu fuzz'da yedi reason
kodunun yedisi de görülüyor, ayrışma yok.

### Denetimimin dişleri

`tester_B_evidence/r6-karar-uyumu-dis-matrisi.txt` — yeni karar-uyumu
dosyasını **sekiz mutant ağacında** koşturdum:

```
KONTROL   43 passed, 12 skipped        (12 skip = git tabanli tarihsel testler; kopya agac depo degil)
M4        2 failed   (fuzz + source_blocks AST)
M5        5 failed   (ikame kwarg sayisi, uclu anahtar, fuzz, ham-blok kapisi, source_blocks AST)
M11       1 failed   (zincirleme miras)
M13b      1 failed   (ikinci `replace` gorunum gecisinin disinda)
M3/M12/M13a/M15  0 failed  -- beklenen: bunlari mutant sondasi yakaliyor
```

---

## 4. K29 / K30 / K31 / K32

**K29** — Şefin kapısını (`purity_check.py`) kör kabul etmedim; taramayı
kendim yaptım (AST ile modül/sınıf/fonksiyon **ve attribute** docstring'leri,
satır sarması `_` birleştirme, `.py` dosya adlarını dışlama, çıplak `_` sonlu
ön-ek = ihlal). **20 atıf, hepsi var.** Kapının dişlerini de ölçtüm: docstring'e
üç tür bayat atıf enjekte ettim (düz ad, satır-sarmalı ad, çıplak `_` ön-ek) —
**hem benim bağımsız taramam hem `purity_check.py` üçünü de gördü**
(`r6-k29-kapi-disleri.txt`). K29'un iki bayat adı (`:92`, `:203`) düzelmiş.

**K30** — Koşullu cümlenin **iki yolunu da kendi geometrimle** yeniden
ürettim (`dialogue`, `h=18`, eşik `0.8 × 18 = 14,4`): artık boşluk 4px →
`['Ada','Ada']`; 22px → `['Ada', None]`. İki yolda da bölümleme aynı
(`(0,), (2,)`). Docstring'de "ASARSA … DEGILDIR" ve "ASMAZSA miras KORUNUR"
cümleleri var.

**K31** — (a) `['Ada: merhaba', 'Ada: nasilsin']` → tek segment
`'merhaba nasilsin'`, `speaker='Ada'`. (b) `['Ada: merhaba', 'Ada2: nasilsin']`
→ `'merhaba Ada2: nasilsin'`, `speaker='Ada'` (etiket metinde kalıyor).
Parantez içi cümle de tutuyor: `['Ada: merhaba', 'Bora: nasilsin']` → **iki**
ayrı segment. Üçü de kendi girdilerimle.

**K32** — Kendi gövdemle: blok başına 88 codepoint aksanlı metin, üç blok →
NFC'de **1** segment, NFD'de **daha fazla** (`max_group_chars` codepoint
sayıyor). Yalnız etiket aksanlıysa: `'María: hola'` NFC → `speaker='María'`,
`text='hola'`; NFD → `speaker is None`, etiket metinde. Ayraç kümesi (K17)
etkilenmiyor. `_split_speaker_label` docstring'inde "GIRDI NFC VARSAYIMI" ve
"Varsayim BU SUZGECLE SINIRLI DEGILDIR" var; modül docstring'inde "BOLUMLEME
DE DEGISIR" var.

**Zorunlu docstring cümleleri** — kararın "docstring'e zorunlu" dediği **20
çapa** parametrize bir testle arandı (boşluk normalize edilerek, satır sarması
eşleşmeyi bozmasın diye). Yirmisi de yerinde.

---

## 5. Bulgular

### N1 · "M5 → ölçü 5 kırılmalı" tutmuyor — ölçü 5'in **sağ taraf** yarısı ayırt edici değil (orta)

`tester_B_evidence/r6-olcu-iddialari.txt`

Karar (MERCEK B/(d)): *"M5 ekler — sağ tarafı `nxt` olarak bırakan mutant →
**ölçü 2, 5 ve 6** kırılmalı."*

Ölçtüm: `olcu5_fixture()` iki sınır üretiyor ve **ikisinde de aday tek bloklu**
— `(3,)` ve `(6,)`. Tek bloklu bir adayda `replace(nxt, bbox=blocks[ilk].bbox)`
ile `nxt`'in kendisi **aynı** bbox'ı taşır, yani M5 orada **yapı gereği**
ayrışamaz. Uçtan uca doğrulama: M5 ölçü 2'nin üç varyantını ve ölçü 6'nın üç
ön ayarını kırıyor, **ölçü 5'i kırmıyor**.

Bu, şefin beş turdur tekrarlayan §4.6/4 sınıfının sağ taraftaki kopyası:
fixture, mekanizmanın değişmezden ayrıştığı girdiyi içermiyor. Kitin kendi
derleminde `coklu_sag >= 500` alt sınırı **var**; ölçü 5'in fixture'ında
karşılığı **sıfır** — kitin selftest çıktısı da yalnız `coklu_sol` yazdırıyor,
yani eksiklik görünmüyor.

Önerim: `olcu5_fixture`'a en az bir sınırda **çok bloklu aday** (zincirleme
hyphen ile gelen `nxt`) eklensin ve ölçü 5'in (ii) şıkkı o sınırda ölçülsün.
Kit şefe ait; değiştirmedim. Fixture güçlendirilirse haber veren bir test
bıraktım: `test_r6_BULGU_olcu5_fixture_sag_tarafi_daima_tek_bloklu_M5_orada_
ayrismaz`.

### N2 · env.md'nin "M4 → ölçü 3/3b" özeti yanlış (düşük)

`olcu3b_fixture()`'ın blokları okuma sırasında dizili (`y = 0, 20, 40, 60, 90`),
bu yüzden `max(source_blocks)` ile `okuma_sirasi(...)[-1]` **aynı** bloğu verir
ve M4 orada ayrışmaz. Ölçtüm: M4 ölçü 3'ün iki ön ayarını, ölçü 5'i ve ölçü
6'nın üç ön ayarını kırıyor; **ölçü 3b'yi kırmıyor**. Kararın kendi metni
("ölçü 3 ve 6 kırılmalı") **doğru** — sapan `env.md`'nin özeti. Ölçü 3b'nin
işi zaten off-by-one (üçlü kuyruk), M4 değil. Bu da bir testle pinli.

### N3 · M15 sınıfının `tests/` altında **hiçbir** kapısı yok (orta, kapı kapsamı)

M15 dört kabul komutunu, 124 ürün testini ve kitin beş kanalını **temiz**
geçiyor; benim diferansiyelim 1844 ayrışma buluyor. Şefin "kör takımda ek
kırık 0" ölçümünü yeniden ürettim. Şef bunu "bilinen sınır" olarak dürüstçe
ilan etti ve bana devretti — ama tur 6'dan sonra bu sınıfı tutan tek şey
`tester_B`'nin sondası olur ve **o bir kabul komutu değildir**.

Somut öneri (tek test, `tests/unit/ocr/test_normalizer.py`): `dialogue`,
`h = 18`, uzunluk-**tek**-engelli bir sınırda `gap = 12`. MENU tablosuyla
sorulursa `0,5 × 18 = 9 ≤ 12` → `"gap"` → miras yok; doğru `params` ile
`0,8 × 18 = 14,4 > 12` → `None` → miras var. Tek assert, sıfır fixture
karmaşıklığı.

### N4 · M12 sınıfı yalnız tek bir ürün testine yaslanıyor (düşük, kapı kapsamı)

Kitin `adim1_4`'ü denetlenen modülün kendi `_merge_hyphenated`'ini çağırdığı
için mutantla birlikte kayıyor — şefin ilan ettiği sınır **doğrulandı**
(13.088 ayrışma, kit üç ön ayarda `TEMİZ`). Benim örneğim
(`islower` → `isalpha`) `test_k5_buyuk_harfle_baslayan_sonraki_satir_birlesmez`
tarafından yakalanıyor, yani sınıf tamamen açık değil; ama kapı **o tek
koşula** bağlı — aynı yardımcının `bbox`/`source_blocks` tarafını değiştiren
bir mutant için aynı güvence yok.

---

## 6. Kapsam beyanı ve regresyon

**Doğrulamadığım yarı:** kararın K28-kök / K30 / K31 / K32 maddeleri hem
docstring'e **hem `known_gaps`'e** yazılmayı şart koşuyor. `known_gaps`
`delivery.md`'de ve o dosya benim merceğime kapalı (`env.md`, "Okumaman
gerekenler"). Bu maddelerin **docstring + test** yarılarını doğruladım;
`known_gaps` yarısını **doğrulamadım** — şefin elle denetlemesi gerekir.

**Regresyon:** `pytest tests` → **821 passed** (şefin tabanıyla aynı). Kör
tester takımı iki ayrı koşumda da **623 passed, 1 xfailed, 0 kırık**. Şefin
verdiği taban 388'di; tur **sırasında** `tester_A` ve `tester_C` kendi tur-6
dosyalarını ekledi (`git status`: `tester_A/test_r6_garanti_alani.py`,
`tester_C/test_tur6_sinir_dil.py`), toplam bu yüzden yükseldi. Onuncu bir
kırık — yani gerçek regresyon — **yok**. `tester_C`'nin yük altında kararsız
olduğu bilinen ölçek testleri iki koşumda da geçti.

**Kendi dosyalarımda düzelttiğim bir yanlış:** `test_k23_mutant_sondasi_tur5.py`
içindeki M3 notu, henüz koşmamış bir ölçüme ("21.000 koşum") atıf yapıyordu.
Ölçümü bu turda gerçekten yaptım ve notu gerçek sayılarla değiştirdim
(24.000 koşum, 0 ayrışma, kimlik 2387/1350/826, 10 ürün ölçüsü, ham çıktı
`r6-mutant-sondasi.txt`).

`src/` ve `tests/unit/ocr/` altına **hiçbir şey yazmadım**; şefin
`olcu_kiti.py` / `conftest.py` / `purity_check.py` dosyalarına dokunmadım
(mutant ağaçlarına yalnız **kopyaları** alındı).
