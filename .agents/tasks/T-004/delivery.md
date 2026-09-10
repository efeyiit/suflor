---
task: T-004
role: implementer
round: 5
status: tamamlandi
files_written:
  - src/ocr/normalizer.py
  - src/ocr/presets.py
  - tests/unit/ocr/test_normalizer.py
commands:
  - cmd: "python -m pytest tests/unit/ocr/test_normalizer.py -k 'k23 or k24' -v  (KIRMIZI FAZ -- TUR 4'un HATALI, mute-eden `_group` mekanizmasi GECICI olarak geri alinip TUR 5 testlerine karsi calistirildi)"
    exit_code: 1
    evidence: evidence/pytest-red-r5.txt
  - cmd: "python -m mypy --strict src/ocr/normalizer.py src/ocr/presets.py"
    exit_code: 0
    evidence: evidence/mypy-r5.txt
  - cmd: "python -m pytest tests/unit/ocr/test_normalizer.py -q"
    exit_code: 0
    evidence: evidence/pytest-r5.txt
  - cmd: "python .agents/tasks/T-004/purity_check.py"
    exit_code: 0
    evidence: evidence/purity-r5.txt
  - cmd: "standalone script -- K23 DEGISMEZ denetimi: 2500 rastgele girdi (sabit tohum 20260910), dort on ayar, %50 genel/%50 hedefli B1-yapili uretici, apply_inheritance=True/False karsilastirmasi"
    exit_code: 0
    evidence: evidence/invariant-r5.txt
  - cmd: "standalone script -- K14 sartnamesiyle birebir (30 blok/~40 karakter/dialogue/50 tekrar) + n=500/1000/2000 olcek dogrulamasi (Tester-C senaryosu)"
    exit_code: 0
    evidence: evidence/budget-r5.txt
contract_change_request: false
known_gaps:
  - >
    K23 (YENI, tur 5, sef_karari-tur5.md) -- DEGISMEZ, SAGLANDI. Bulgu
    B1 (yuksek siddetli, kirmizi takim + sef kendi eliyle yeniden
    uretti): tur 4'un mekanizmasi (K19/K21) bir grubu "length" sebebiyle
    kapatirken `nxt`'i (yeni grubun basi) `dataclasses.replace` ILE
    HEMEN mute EDIP bu mute EDILMIS `_Item`'i DOGRUDAN `current`'e
    atiyordu -- SONRAKI dongu adiminda bu mute EDILMIS `current.speaker`
    BIR SONRAKI ciftin `_group_rejection_reason` cagrisina `a` OLARAK
    GIRIYORDU, yani miras kendi UYDURDUGU degeri bir sonraki GRUPLAMA
    KARARINA girdi yapiyordu: K15 matrisinde `None/Y -> hayir` satiri,
    sol taraf `None`'dan `Ada`'ya (miras) CEVRILDIGI icin `Ada/Ada ->
    evet`e DONUSUYORDU -- kendi `Ada:` etiketiyle gelen YENI bir replik
    (kendisinden ONCEKI, miras yoluyla "Ada" GORUNEN segmentle SADECE
    AYNI ADA sahip oldugu icin) YANLISLIKLA o segmentin kuyruguna
    YAPISIYORDU. BOLUMLEME (segment SAYISI/`source_blocks`) miras
    acik/kapali FARKLILASIYORDU -- K23'un yasakladigi TAM OLARAK bu.

    DEGISMEZ: "herhangi bir girdi icin `normalize` ciktisinin
    BOLUMLEMESI (`Segment.source_blocks` demetlerinin dizisi) miras
    mekanizmasi ACIKKEN/KAPALIYKEN BIREBIR AYNI olmalidir; miras
    YALNIZCA `Segment.speaker`'i degistirebilir" -- SAGLANDI. Uygulama:
    `_group` TAMAMEN YENIDEN YAZILDI, ARTIK IKI ayri gecisten olusuyor:
    (1) BOLUMLEME gecisi -- ana dongu, `current`/`nxt`.speaker HICBIR
    ZAMAN mute EDILMEZ, her karsilastirma HER ZAMAN ogelerin OZGUN
    (OCR'dan gelen) speaker'ini kullanir; kapanan HER grup icin bu
    sinirin "SADECE uzunluk sinirli" olup olmadigi (`pure_length`)
    HESAPLANIR ve KAYDEDILIR (UYGULANMAZ). Bu gecisin urettigi `groups`
    -- text/bbox/source_blocks/OZGUN speaker -- `apply_inheritance`
    bayragindan YAPI GEREGI ETKILENMEZ (bayrak bu gecisin ICINDE HIC
    OKUNMAZ). (2) GORUNUM gecisi -- `apply_inheritance=True` ISE (yani
    `normalize` HER ZAMAN), dongu SONRASI SOLDAN SAGA TEK bir ek pas:
    `pure_length_boundaries[i-1]` isaretli VE `groups[i-1].speaker is
    not None` ise `groups[i]`'nin SADECE `speaker` alani `dataclasses.
    replace` ile guncellenir -- text/bbox/source_blocks'a DOKUNULMAZ,
    VE bu guncelleme HICBIR gruplama kararina GERI BESLENMEZ (bolumleme
    zaten TAMAMLANMISTIR).

    Test kancasi (GENEL API'YE SIZMADAN): `normalize`'in govdesi
    `_normalize_impl(blocks, preset, *, apply_inheritance: bool = True)`
    adli bir IC fonksiyona tasindi; `normalize` bunu SABIT `True` ile
    cagirir (`normalize(blocks, preset)` imzasi DEGISMEDI/DEGISMEYECEK).
    `tests/unit/ocr/test_normalizer.py` bu ic fonksiyonu DOGRUDAN import
    eder.

    ZORUNLU makine denetimi -- UC test: (a)
    `test_k23_miras_acik_kapali_bolumleme_degismezi_fuzz`: sabit tohum
    (20260910), **2500** rastgele girdi (>=2000), DORT on ayarin HEPSI,
    yozlasmis geometri (sifir/negatif w/h) DAHIL, %50 GENEL rastgele +
    %50 B1'in YAPISINI tasiyan HEDEFLI uretici karisimi (genel uretici
    TEK BASINA bu hata SINIFINI YAKALAMA olasiligi COK dusuk oldugu icin
    -- ONCE denendi, 2500 genel girdide 0 fark bulundu BUGGY KODA
    KARSI BILE; hedefli uretici EKLENINCE ayni buggy koda karsi 422/2500
    fark bulundu, bkz. evidence/pytest-red-r5.txt) -- `apply_inheritance
    =True/False` ciktilarinin segment SAYISINI VE HER segmentin
    text/bbox/placeholders/source_blocks'unu (speaker HARIC) karsilastirir,
    TEK BIR fark bile testi KIRAR (evidence/invariant-r5.txt: **2500
    girdi denendi, 0 fark bulundu**, DUZELTILMIS kod). (b)
    `test_k23_kendi_etiketiyle_gelen_kuyruk_mirastan_dolayi_yanlislikla_
    birlesmiyor`: B1'in BIREBIR AYNI senaryosu, uctan uca `normalize()`
    uzerinden -- 3 AYRI segment (VARYANT B, DOGRU), 2 DEGIL (VARYANT A,
    tur 4'un HATASI). (c)
    `test_k23_invariant_b1_senaryosunda_bolumleme_ayni_speaker_farkli`:
    AYNI senaryo, `_normalize_impl` ile DOGRUDAN apply_inheritance=True/
    False karsilastirmasi -- BOLUMLEME BIREBIR ayni, SADECE bir
    segmentin speaker'i degisir.

    KIRMIZI FAZ (evidence/pytest-red-r5.txt): `_group` GECICI olarak
    tur 4'un HATALI (mute-eden, tek-gecisli) mekanizmasina geri alinip
    (yeni `apply_inheritance` parametresi KORUNARAK -- `False` ISE HIC
    mutasyon yapmaz, `True` ISE HER ZAMAN mutasyon yapar, tur 4'teki GIBI)
    `-k "k23 or k24"` calistirildi: **4 FAILED, 1 passed** -- basarisiz
    olan DORT test tam olarak B1/K23/K24'un YAKALADIGI senaryolar (fuzz
    testi 422/2500 fark BULDU; ilk fark iterasyon 16'da segment SAYISI
    2!=3); basarili kalan `test_k24_kuyruk_ile_birlesik_bbox_farkli_
    sonuc_verir` `_group`'un ICINE HIC GIRMEDIGI (dogrudan `_group_
    rejection_reason`'u sinayan) DUSUK-seviye bir test oldugu icin
    ETKILENMEDI (beklenen). Ardindan GERCEK (duzeltilmis, iki-gecisli)
    kod geri getirildi; TAM suit **98/98 GECTI** (evidence/pytest-r5.txt,
    82 round-4 testi HICBIRI degistirilmeden/silinmeden GECTI + 16 yeni
    TUR 5 testi).
  - >
    K24 (YENI, tur 5, sef_karari-tur5.md) -- UYGULANDI, SAGLANDI. Tur
    4'teki "denk ve daha kolay uygulanabilir ifade" cumlesi IPTAL edildi
    (kirmizi takim OLCTU: iki ifade denk DEGIL, ~%2 ayrisiyor). GECERLI
    TEK ifade: "(a,b) cifti SADECE uzunluk kontrolu CIKARILARAK yeniden
    degerlendirilir; bu degerlendirmede SOL TARAF kapanan grubun okuma
    sirasindaki SON KAYNAK OGESIDIR -- birikmis grubun birlesik bbox'i
    DEGIL (birlesik kutu grubun EN ALTA uzanan ogesinin bottom'unu
    tasiyip GERCEK boslugu YANLIS/negatif OLCEBILIR)".

    UYGULAMA: `_group` ARTIK `current` (birikmis/birlesik) ile PARALEL
    bir `tail: _Item` DEGISKENI tutuyor -- her BASARILI birlesimde
    `tail = nxt` (birlesime KATILAN HAM oge), her YENI grup basladiginda
    `tail = nxt` ile SIFIRLANIR. K19/K21/K23'un miras-uygunluk sorgusu
    (`ignore_length=True` ikinci cagri) ARTIK `_group_rejection_reason
    (tail, nxt, ...)` KULLANIR, `_group_rejection_reason(current, nxt,
    ...)` DEGIL. KAPSAM: bu degisiklik SADECE bu IKINCI (miras-uygunluk)
    sorgu icindir -- `_group`'un ANA (`current` ile `nxt` arasindaki)
    BIRLESTIRME KARARI HALA `current` kullanir, K10/K11'in "birlesik
    bbox kaynak bloklarin KAPSAYICI dikdortgenidir" tanimi DEGISMEDI.

    ZORUNLU testler: (a) `test_k24_kuyruk_ile_birlesik_bbox_farkli_
    sonuc_verir` (DUSUK seviye) -- en az bir ogesi SONRAKILERDEN daha
    ASAGI uzanan (grubun BIRLESIK bbox'inin bottom'unu TASIYAN oge
    grubun BASINDA, KUYRUKTA DEGIL) coklu-bloklu bir grubun kuyrugunda:
    `current` (birlesik) ile `ignore_length=True` sorgusu YANLISLIKLA
    `None` doner (gap KUCUK gorunur -- 5px, esik 16px altinda), `tail`
    ile AYNI sorgu DOGRU sekilde `"gap"` doner (GERCEK kopus -- 475px --
    GORULUR). (b) `test_k24_normalize_uzerinden_kuyruk_temelli_kontrol_
    yanlis_mirasi_onler` -- AYNI senaryo uctan uca `normalize()`
    uzerinden -- 2 segment, ikincisi speaker=None (K24 sonrasi miras
    UYGULANMAZ; K24 ONCESI -- KIRMIZI FAZDA -- speaker='Ada' YANLISLIKLA
    UYGULANIYORDU, bkz. evidence/pytest-red-r5.txt).
  - >
    K25 (tur 4'un SECENEK 1'i, sef_karari-tur5.md geregi ZORUNLU) --
    ZATEN SAGLANMISTI, tur 5'te DEGISTIRILMEDI/KORUNDU. `_group_
    rejection_reason`'a tur 4'te eklenen KEYWORD-ONLY, VARSAYILANI
    `False` olan `ignore_length: bool` parametresi (SECENEK 1) tur
    5'te de AYNI kaldi -- fonksiyonun DONUS TIPI (`str | None`) HICBIR
    SEKILDE degismedi, SECENEK 2'nin (tum sebepleri donduren bir kume/
    liste turu) getirecegi kirilma RISKI hic OLUSMADI. Ayrica bu turde
    `_should_group`'un DIS IMZASI (`(_Item, _Item, NormalizerParams) ->
    bool`) VE `_should_group` <-> `_group_rejection_reason` YAPISAL
    AYRISMAZLIGI (`return _group_rejection_reason(a, b, params) is
    None`) da HICBIR SEKILDE degismedi -- K15 matris testleri
    (`test_k15_matris_*`) VE tum K19/K21 dusuk-seviye testleri
    (`_group_rejection_reason`/`_should_group`'u DOGRUDAN sinayan)
    DEGISTIRILMEDEN GECIYOR (82 round-4 testinin TAMAMI, evidence/
    pytest-r5.txt). AYRICA ZORUNLU test EKLENMEDI (K25 icin ayri bir
    yeni test istenmiyordu -- "regresyon tabani korunacak" gerekcesi
    MEVCUT testlerin degismeden gecmesiyle SAGLANIYOR).
  - >
    K26 (YENI, tur 5, sef_karari-tur5.md) -- UYGULANDI (SALT
    DOKUMANTASYON, davranis DEGISMEDI). K22'nin (tur 4) "ikisi fullwidth,
    dordu uyumluluk formu" ifadesi OLGUSAL olarak YANLISTI -- "diger"
    sozcugu fullwidth ikilinin (U+FF01/U+FF1F) uyumluluk formu
    OLMADIGINI ima ediyordu. Olcum (`unicodedata.decomposition`,
    Unicode 15.0.0): ALTISI DA uyumluluk formudur, fark YALNIZCA
    ayristirma ETIKETIDIR -- U+FE15/U+FE16 `<vertical>`, U+FE56/U+FE57
    `<small>`, U+FF01/U+FF1F `<wide>` (2/2/2 dagilim). Duzeltme UC yerde
    yapildi: (1) modul docstring K4 bolumu, ilk gecis ("buldu -- ikisi
    fullwidth, dordu uyumluluk formu" -> "ALTISI DA Unicode UYUMLULUK
    formudur"), (2) modul docstring K22 (tur 4) bolumu -- YANLIS
    "ikisi fullwidth ... dordu DIGER uyumluluk formlari" ifadesi TAMAMEN
    cikarilip DOGRU ifade + etiket dagilimi tablosuyla degistirildi VE
    yeni bir "K26" alt-paragrafi eklendi, (3) `_is_single_char_noise`
    fonksiyon docstring'i (AYNI hatali ifadeyi TEKRARLIYORDU) -- ayni
    sekilde duzeltildi. Kod HICBIR SATIR degismedi (`_is_single_char_
    noise` ayni `unicodedata.normalize("NFKC", ch) in ("?", "!")`
    kontrolunu kullanmaya devam ediyor) -- K20/K22 ile AYNI ilke: kod
    HER ZAMAN dogruydu, docstring'in OLGUSAL iddiasi hataliydi.

    ZORUNLU testler (YENI, `unicodedata.decomposition` ile): (a)
    `test_k26_alti_karakterin_hepsi_uyumluluk_formu_ve_etiket_dogru`
    (parametrize, 6 karakter) -- HER karakterin decomposition'inin
    BEKLENEN etiketle (`<wide>`/`<small>`/`<vertical>`) BASLADIGINI
    sabitler. (b) `test_k26_alti_karakterin_etiket_dagilimi_iki_iki_iki`
    -- etiket DAGILIMININ TAMAMININ 2x`<wide>`/2x`<small>`/2x`<vertical>`
    OLDUGUNU (K22'nin "dordu uyumluluk formu" -- yani 2/4 -- iddiasinin
    de YANLIS oldugunu) sabitler, VE hicbirinin BOS decomposition
    (yani ALTISININ da GERCEKTEN uyumluluk formu OLDUGUNU) tasimadigini
    dogrular.
  - >
    K27 (YENI, tur 5, sef_karari-tur5.md) -- UYGULANDI (SALT
    DOKUMANTASYON + acikca belgelenmis kapsam sinirini SABITLEYEN
    testler; davranis DEGISMEDI -- zaten `menu` icin `should_group=
    False` oldugu, `_group`'un HIC cagirilmadigi tur 2'den BERI DOGRUYDU,
    bu turde YALNIZCA acikca yazildi). K11 bolumune "### K27" alt-basligi
    eklendi: `menu`'de `params.should_group=False` -> `normalize` adim
    5'te `_group`'u HIC CAGIRMAZ -> K19/K21/K23/K24'un TAMAMI (hepsi
    `_group`'un ICINDE yasar) `menu` icin TANIMSIZDIR -- "uzunluk
    yuzunden bolunme" kavraminin KENDISI `menu`'de YOKTUR. `_extract_
    speakers` (K9) HALA `menu` icin de calisir (gruplamadan BAGIMSIZ,
    adim 4) -- yani bir etiket-blok KENDISINDEN SONRAKI ILK ogeye
    konusmaciyi HALA tasir, ama O OGEDEN SONRAKI (etiketsiz) bir ucuncu
    oge `menu`'de speaker=None KALIR (diger UC on ayarda K15/K19/K21/K23
    bunu ONCEKI grubun devami sayip miras ALDIRIRDI). Bu, implementer'in
    UYDURDUGU bir daraltma DEGIL, K11'in ASIL karari geregi BILINCLI ve
    ARTIK acikca BELGELENMIS bir kapsam disidir.

    ZORUNLU testler -- DORT on ayarin HER biri icin BIR test: `test_
    k27_dialogue_uzunluk_bolunmesinde_miras_calisir`, `..._tooltip_...`,
    `..._subtitle_...` (ucu de AYNI "etiket + govde1 (SIKI) + govde2
    (etiketsiz, uzunluk KENDI cap'ini asar)" kalibiyla, HER USUNUN
    KENDI `max_group_chars`'iyla -- govde2 MIRAS alir, gruplama+K19/K21/
    K23 DEVREDE) VE `test_k27_menu_gruplama_yok_miras_kavrami_yok` (AYNI
    kalip `menu` ile -- govde1/govde2 AYRI segment KALIR, govde2
    speaker=None KALIR, K9'un etiket-tasima DAVRANISI ise -- gruplamadan
    BAGIMSIZ oldugu icin -- HALA calisir, govde1 Ada'yi ALIR).
  - >
    Regresyon YASAGI -- sef_karari-tur5.md'nin "Bozmadan koru" listesinin
    TAMAMI DOGRULANDI (82 round-4 testinin HICBIRI degistirilmedi/
    silinmedi, TAMAMI degismeden GECIYOR, evidence/pytest-r5.txt):
    K21'in DOGRU calisan kismi (bilesik sinirda miras YOK -- artik IKI-
    gecisli mekanizmanin bir SONUCU, testler AYNI kaldi) · `_should_
    group` govdesinin TEK SATIRLIK devretme deseni (HICBIR SEKILDE
    degismedi -- `_group`'un YENIDEN YAZILMASI `_should_group`'a
    DOKUNMADI) · `speaker` kontrolunun `length`'ten ONCE gelmesi
    (`_group_rejection_reason` icinde DEGISMEDI) · K15 matrisinin BES
    satiri · K16 · K17 · K18/K20 · K7 · K6 · K5 · K8 · K4 · K10 · K14
    butce assertion'i · K13 determinizm · asil is · olcek (yeniden
    OLCULDU, evidence/budget-r5.txt: K14 medyan 0.1556 ms; n=500/1000/
    2000 -> 2.737/6.723/21.071 ms -- onceki turlerin (tur2: 3.443/9.271/
    27.069; tur3: 3.673/9.234/26.461; tur4: 2.744/7.032/20.138) ile AYNI
    BUYUKLUK MERTEBESINDE, buyume SINIFI -- O(n)'den kotu, bilinen VE
    kabul edilmis sinir -- DEGISMEDI).
  - >
    Round-1/2/3/4'ten DEVAM EDEN, TUR 5'te DEGISMEYEN, ACIK known_gap'ler
    (tam gerekce onceki turlerin delivery.md'lerinde durur, burada
    SADECE tekrar dogrulandigi kayda gecer): `SPEAKER_LABEL_SEPARATORS`
    sef'in "en az" istedigi iki karakterle SINIRLI · ust uste binen
    bloklarda `_group`'un olcegi O(n)'den KOTU (bu turde de OLCULDU,
    yukarida) · K5 hyphen kurali SADECE ASCII `-` icin tanimli · K8'de
    "bir blok birden fazla segmente bolunur" senaryosu YOK · K6'nin
    blok-sinirina bolunmus placeholder VE K1'in tek-satirlik blok
    bas/son bosluk kirpma davranislari DEGISMEDI.
---

# T-004 -- TextNormalizer duzeltme teslimi (round 5)

## Ozet

Tur 4'te implementer K21/K22'yi DOGRU uyguladi ve sef DOGRULADI. Ama bu
turde **ILK KEZ devreye alinan KARAR KIRMIZI TAKIMI** -- sefin
kararlarini denetleyen, implementer'in kodunu DEGIL -- sefin
kararlarinda **12 bulgu** cikardi, **ucu yuksek siddetli**. Sef ucunu de
kendi eliyle yeniden uretti ve dogruladi.

Kok teshis (sef_karari-tur5.md): sefin onceki kararlari (K9, K19, K21,
K22) hep **mekanizma** olarak yazildi ("su kosulda sunu yap") ve
**etkilesimleri** hic denetlenmedi. **Hatalar implementer'in DEGIL, sefin
kararlarindaydi** -- K21'in mekanizmasi DOGRU uygulanmisti, ama
etkilesimi (miras degerinin bir SONRAKI karara sizmasi) GORUNMUYORDU.

**BES YENI KARAR, HEPSI bu turde UYGULANDI, HICBIRI reddedilmedi/bloke
olmadi:** K23 (DEGISMEZ -- miras BOLUMLEMEYI degistiremez), K24 (K21'in
TEK gecerli ifadesi -- "bu cift" grubun KUYRUGUDUR), K25 (secenek 1
zorunlu -- ZATEN saglanmisti, korundu), K26 (K22'nin olgusal hatasi --
ALTISI DA uyumluluk formu), K27 (`menu` acikca kapsam disi).

## K23 -- en kritik: bir DEGISMEZ, mekanizma degil

`_group` **TAMAMEN YENIDEN YAZILDI** -- artik IKI ayri gecisten olusuyor:

1. **Bolumleme gecisi** -- ana dongu, `speaker` HICBIR ZAMAN mute
   EDILMEZ, her karsilastirma HER ZAMAN ogelerin OZGUN speaker'ini
   kullanir. Bu gecis `apply_inheritance` bayragindan YAPI GEREGI
   ETKILENMEZ.
2. **Goruntu gecisi** -- bolumleme TAMAMEN bittikten SONRA, SOLDAN SAGA
   TEK bir ek pas SADECE `speaker` alanini gunceller; hicbir gruplama
   kararina GERI BESLENMEZ.

Bu ayrim K23'u **YAPI GEREGI** (mekanizma hatasi degil, tasarim)
saglar -- makineyle denetlenmis: `_normalize_impl(..., apply_
inheritance=True/False)` **2500 rastgele girdide 0 fark** buldu
(evidence/invariant-r5.txt).

**KIRMIZI FAZ** (evidence/pytest-red-r5.txt): tur 4'un HATALI (mute-eden)
mekanizmasi GECICI olarak geri getirilip yeni testlere karsi calistirildi
-- **4 FAILED** (B1'in tam senaryosu VE K23 fuzz testi -- 422/2500
fark), sadece `_group`'un ICINE HIC GIRMEYEN bir K24 dusuk-seviye testi
etkilenmedi (beklenen). Duzeltilmis kod geri getirilince **98/98 GECTI**.

## K24 -- "bu cift"in tek gecerli ifadesi: SOL TARAF kuyruktur

Tur 4'un "denk ifade" iddiasi **IPTAL** (kirmizi takim: ~%2 ayrisiyor).
`_group` artik `current` (birikmis) ile paralel bir `tail` (grubun
okuma-sirasindaki SON HAM ogesi) tutuyor; miras-uygunluk sorgusu ARTIK
`tail` ile yapiliyor -- birlesik bbox'in `bottom`'u grubun EN ALTA uzanan
ogesinden geldigi icin (grup ICINDE monotonik olmayan bir dikey uzanim
varsa) GERCEK boslugu YANLIS (kucuk/negatif) OLCEBILIYORDU.

## Ana K sorulari (son cevapta tekrarlanacak)

Uc kabul komutu GERCEK exit code'lari, K23 denetiminin girdi/fark
sayisi, medyan butce -- asagidaki tablo VE `evidence/` altindaki ham
ciktilar.

| Komut | exit_code | Kanit |
|---|---|---|
| `python -m mypy --strict src/ocr/normalizer.py src/ocr/presets.py` | **0** | evidence/mypy-r5.txt |
| `python -m pytest tests/unit/ocr/test_normalizer.py -q` | **0** (98 passed) | evidence/pytest-r5.txt |
| `python .agents/tasks/T-004/purity_check.py` | **0** | evidence/purity-r5.txt |

`evidence/invariant-r5.txt`: sabit tohum 20260910, **2500 girdi
denendi, 0 fark bulundu** (duzeltilmis kod); ayni denetim, tur 4'un
buggy koduna karsi calistirilinca **422/2500 fark** buldu (evidence/
pytest-red-r5.txt).

`evidence/budget-r5.txt`: K14 medyan **0.1556 ms** (butce 5 ms, cok
altinda); n=500/1000/2000 -> 2.737/6.723/21.071 ms (onceki turlerle AYNI
buyukluk mertebesinde, buyume sinifi degismedi).

## Sahiplik

Yalniz `owns` icindeki uc dosyaya yazildi: `src/ocr/normalizer.py`,
`src/ocr/presets.py` (bu turde presets.py HICBIR SATIR degismedi -- K23-
K27 `NormalizerParams`'a dokunmuyor, listede tamlik icin yer aliyor),
`tests/unit/ocr/test_normalizer.py`. `sef_karari-tur5/4/3/2.md`,
`packet.md`, `purity_check.py`, `tester_*` dizinleri, `src/ocr/
__init__.py`, `src/contracts/**`, `src/capture/**` -- HICBIRINE
dokunulmadi (bu delivery.md + `evidence/` haricinde).

## Dogruluk beyani (PROTOKOL S6 madde 9)

K23, K24, K26, K27'nin HEPSI uygulandi ve YENI regresyon/denetim
testleriyle DOGRULANDI. K25 ZATEN saglanmisti (tur 4'te secilen SECENEK
1), bu turde DEGISTIRILMEDEN korundu -- mevcut testlerin (82/82)
degismeden gecmesi bunun kaniti. Hicbir karar "uygulanamadi" olarak
bildirilmiyor, hicbir KISIT ile celismedi. K23 DEGISMEZININ SAGLANDIGI
hem YAPISAL ispatla (iki-gecisli tasarim, bolumleme gecisi `apply_
inheritance`'i hic okumuyor) hem MAKINEYLE (2500 girdi, 0 fark) hem
KIRMIZI FAZLA (eski koda karsi 422/2500 fark, testlerin TOTOLOJI
OLMADIGININ kaniti) gosterildi. Round-1/2/3/4'ten devam eden acik
known_gap'ler (SPEAKER_LABEL_SEPARATORS kapsami, O(n)'den kotu olcek,
K6/K1/K5/K8 bilinen sinirlari) bu turde de degismedi, tekrar
dogrulandi/olculdu, ayrintili gerekceleri onceki turlerin
delivery.md'lerinde durur.
