r"""TextNormalizer -- OCR bloklarindan cevrilmeye hazir `Segment` uretimi.

Tasarim dokumani S5.2: "Ceviri kalitesinin yarisi burada belirlenir." Bu
modul TAMAMEN SAF'tir: I/O yok, global mutable durum yok, rastgelelik yok,
zaman bagimliligi yok (`purity_check.py` bunu statik VE surecler-arasi
(farkli `PYTHONHASHSEED`) olarak denetler). Bu yuzden kod hicbir yerde
`set` kullanmaz -- CPython'da `set` iterasyon sirasi `PYTHONHASHSEED`'e
bagli olabilir (str hash randomizasyonu); bu modulde sira onemli oldugu
her yerde `list`/`tuple` + `sorted(...)` kullanilir, bu deger turunden
(int) bagimsiz olarak da her zaman deterministiktir.

Bu docstring, gorev paketindeki (T-004 packet.md) ON DORT SEF KARARININ
(K1-K14) HER BIRININ bu modulde nasil uygulandigini belgeler -- tester bu
dosyayi okur, `known_gaps`'i OKUMAZ; garanti alani burasidir.

TUR 2 (duzeltme turu -- `.agents/tasks/T-004/sef_karari-tur2.md`): uc kor
tester'in ikisi (A, C) tur 1'i reddetti, sef dort bulguyu kendi eliyle
yeniden uretti ve DORT YENI KARAR verdi -- K15 (gruplamada `None` "farkli
konusmaci" DEGIL "devam" demektir), K16 (yozlasmis yukseklik/genislikte
gruplama KOSULSUZ yok), K17 (fullwidth `：` konusmaci ayraci), K18 (`?`/`!`
istisnasi NFKC denkligiyle tanimlanir). Dordu de asagida, ilgili K-bolumu
icinde "(tur 2)" etiketiyle belgelenir.

TUR 3 (duzeltme turu -- `.agents/tasks/T-004/sef_karari-tur3.md`): tur
2'de UCU DE onay verdi, ama sef Tester-C'nin "bloke etmeyen" saydigi IKI
notu inceledi ve BIRINI yeniden siniflandirdi. IKI YENI KARAR: K19
(DAVRANIS degisikligi -- `max_group_chars` YUZUNDEN bolunen bir grubun
KUYRUK segmenti artik konusmaciyi MIRAS alir; geometrik bosluk/farkli
konusmaci/yozlasmis bbox yuzunden bolunen kuyruk HALA `None` kalir) ve
K20 (SALT DOKUMANTASYON -- K4 bolumundeki NFKC istisna iddiasindaki bir
OLGUSAL hata duzeltildi, davranis DEGISMEDI). Ikisi de asagida ilgili
K-bolumu icinde "(tur 3)" etiketiyle belgelenir.

TUR 4 (duzeltme turu -- `.agents/tasks/T-004/sef_karari-tur4.md`): tur
3'te B onay, C RET verdi -- sef bulguyu kendi eliyle yeniden uretti ve
DOGRULADI. Bulgu, K19'un MEKANIZMASINDAKI (kararin KENDISI degil) bir
ACIGA dayaniyor: `_group_rejection_reason` bir ciftin BIRDEN FAZLA
kontrolden AYNI ANDA reddedilebilecegini gozden kacirmisti (sirali
kontroller birbirini DISLIYOR sanilmisti -- DISLAMIYORLAR). IKI YENI
KARAR: K21 (DAVRANIS degisikligi -- miras SADECE `max_group_chars` TEK
BASINA engelse uygulanir; ayni ciftte BASKA bir kontrol de (geometri,
konusmaci, yozlasmis bbox) basarisizsa miras YOK, `speaker=None` kalir)
ve K22 (SALT DOKUMANTASYON -- K20'nin "ASCII/fullwidth DISINDA" ifadesi
kendi listesiyle CELISIYORDU, "ASCII DISINDA" olarak duzeltildi, davranis
DEGISMEDI). Ikisi de asagida ilgili K-bolumu icinde "(tur 4)" etiketiyle
belgelenir.

TUR 5 (duzeltme turu -- `.agents/tasks/T-004/sef_karari-tur5.md`): tur
4'te implementer K21/K22'yi DOGRU uyguladi ve sef DOGRULADI -- ama bu
turde ILK KEZ devreye alinan KARAR KIRMIZI TAKIMI (sefin KARARLARINI,
implementer'in kodunu DEGIL, denetleyen ayri bir kapı) sefin kendi
kararlarinda 12 bulgu cikardi, UCU yuksek siddetli; sef ucunu de kendi
eliyle yeniden uretti ve DOGRULADI. Kok teshis: sefin onceki kararlari
(K9, K19, K21, K22) hep MEKANIZMA olarak yazilmisti ("su kosulda sunu
yap") ve ETKILESIMLERI hic denetlenmemisti. BES YENI KARAR: K23 (bir
DEGISMEZ, mekanizma DEGIL -- herhangi bir girdi icin `normalize`
ciktisinin BOLUMLEMESI, yani `Segment.source_blocks` demetlerinin
dizisi, miras mekanizmasi ACIKKEN ve KAPALIYKEN BIREBIR ayni olmalidir;
miras YALNIZCA `Segment.speaker` degerini degistirebilir), K24 (K21'in
"denk iki ifade"sindeki ESDEGERLIK YANLISTI -- kirmizi takim OLCTU, ~%2
ayrisiyor; GECERLI TEK ifade: ayni `(a, b)` cifti SADECE uzunluk
kontrolu CIKARILARAK yeniden degerlendirilir, VE bu degerlendirmede SOL
TARAF kapanan grubun okuma sirasindaki SON KAYNAK OGESIDIR -- birikmis
grubun BIRLESIK bbox'i DEGIL, cunku birlesik kutu grubun en alta uzanan
ogesinin `bottom`'unu tasiyip GERCEK satir-arasi boslugu OLCMEZ/negatif
`gap` artifakti uretir), K25 (tur 4'un SECENEK 1'i -- `ignore_length`
parametresi -- ZORUNLU kalir, SECENEK 2 donus tipini degistirip
hâlihazirda yesil tester assertion'larini kirardi), K26 (K22'nin OLGUSAL
hatasi -- "ikisi fullwidth, dordu uyumluluk formu" YANLIS; ALTISI DA
Unicode uyumluluk formudur, fark YALNIZCA ayristirma ETIKETIDIR: ikisi
`<wide>`, ikisi `<small>`, ikisi `<vertical>`) ve K27 (`menu`'de
`should_group=False` oldugu icin `_group` HIC cagirilmaz -- K19/K21/K23/
K24 SADECE `should_group=True` olan on ayarlarda TANIMLIDIR; `menu`
bilincli VE belgelenmis bir KAPSAM DISIDIR). Besi de asagida ilgili
K-bolumu icinde "(tur 5)" etiketiyle belgelenir; K23/K24 icin miras
mekanizmasinin KENDISI (`_group`) tur 5'te YENIDEN YAZILDI -- bkz. "##
K23/K24" bolumu.

TUR 6 (duzeltme turu -- `.agents/tasks/T-004/sef_karari-tur6.md`): tur
5'te A RET, B ve C ONAY verdi. K23 degismezi SAGLANDI; kalan bulgu
R5-1 idi ve sefin karari YEDI kirmizi takim gecisinden gecti. BES YENI
KARAR: K28 (DAVRANIS -- miras-uygunluk sorgusunun IKI tarafi da OZGUN
`TextBlock` listesinden gelir; bkz. asagida "## K28"), K29 (SALT
DOKUMANTASYON -- bu dosyanin docstring'lerinde ANILAN her `test_*` adi
test dosyasinda GERCEKTEN var olmali; iki bayat ad duzeltildi), K30
(SALT DOKUMANTASYON -- K2 x K19/K21 etkilesimi KOSULLU cumleyle
yazildi; bkz. `_group`), K31 (SALT DOKUMANTASYON -- bitisik iki
replikte IKI alt durum; bkz. `_group`) ve K32 (SALT DOKUMANTASYON --
girdi NFC varsayimi MODUL duzeyindedir; bkz. asagida "## K32"). Yalniz
K28 KOD degisikligidir; K29-K32 davranisi DEGISTIRMEZ.

## K28 (tur 6) -- miras-uygunluk sorgusunun IKI tarafi da OZGUN bloktan

DEGISMEZ: bir grup kapanirken miras-uygunluk sorgusuna (`_group_
rejection_reason(..., ignore_length=True)` cagrisi) verilen IKI geometri
de `normalize`'a verilen OZGUN `TextBlock` listesinden gelir --

  - SOL taraf `bbox` = kapanan grubun kaynak bloklari arasinda OKUMA
    SIRASINDA SON gelen blogun `bbox`'i;
  - SAG taraf `bbox` = adayin (`nxt`) kaynak bloklari arasinda OKUMA
    SIRASINDA ILK gelen blogun `bbox`'i.

OKUMA SIRASI = `(bbox.y, bbox.x, girdi indeksi)` ARTAN -- adim 1'in
kararli `sorted(enumerate(blocks), key=(y, x))` cagrisiyla AYNI. HICBIR
birlesik `_Item` `bbox`'i (adim 3'ten ya da adim 5'ten) bu sorguya
GIRMEZ. Sorgunun `speaker`/`text` alanlari sirasiyla `tail` ve `nxt`'ten
alinir; YALNIZCA `bbox` IKAME EDILIR (`dataclasses.replace`; `speaker`,
`text` VE `source_blocks` AYNEN korunur).

`source_blocks[-1]` / `[0]` KULLANILMAZ: `source_blocks` K8 geregi artan
INDEKS sirasindadir, K3 geregi girdi listesi okuma sirasinda OLMAK
ZORUNDA DEGILDIR; en buyuk indeks ile okuma sirasindaki son blok AYNI
SEY DEGILDIR.

KAPSAM (K24'ten devralinir): bu degismez YALNIZCA miras-uygunluk
sorgusu icindir. `_group`'un ANA birlestirme karari (bolumleme gecisi)
K10/K11 uyarinca `current`'in BIRLESIK `bbox`'ini kullanmaya DEVAM
EDER; K23'un iki-gecis yapisi DEGISMEZ.

Uygulama: modul duzeyinde `_raw_query_pair(tail, nxt, blocks)` (tam
gerekce ve olcumler orada) + `_group(items, params, *, blocks=(),
apply_inheritance=True)`. `_Item` DEGISMEDI (yeni alan yok, adim 3/adim
5 yayilimi yok) -- geometri SORGU ANINDA turetilir, saklanan ve
bayatlayabilecek bir kopya YOKTUR.

KOK, ACIK BIRAKILDI: R5-1'in KOKU adim 3'un (`_merge_hyphenated`, K5)
GEOMETRIK KONTROL YAPMAMASIDIR; K28 SEMPTOMU kapatir, koku DEGIL --
adim 3 SALT TIPOGRAFIKTIR ve OYLE KALIR (bkz. `_merge_hyphenated`).

## K32 (tur 6) -- girdi NFC varsayimi, MODUL duzeyinde

`normalize` girdinin **NFC** oldugunu VARSAYAR. Ad suzgeci codepoint
bazli `isalpha()`'dir; NFD adlar (birlesik aksan) konusmaci SAYILMAZ,
etiket METINDE kalir (K31/b). Bu varsayim SUZGECLE SINIRLI DEGILDIR:
`max_group_chars` (K11) ve `_MAX_SPEAKER_NAME_LEN` (K9) CODEPOINT
SAYAR; ayni GORUNEN metin NFD gelirse BOLUMLEME DE DEGISIR. Olcum (sef,
kirmizi takim yeniden uretti): 3 bloklu aksanli bir govde NFC'de 1
segment, NFD'de 3 segment (blok basina ~85-92 codepoint); YALNIZ etiket
aksanliysa segment SAYISI degismez (1/1) ama `speaker` `'María'` ->
`None`'a duser ve etiket metinde kalir. Ayrac kumesi (`:` / `：`, K17)
ETKILENMEZ. Davranis tur 6'da DEGISTIRILMEDI (K9/K11'in sozluksel
kurallarina dokunmak yeni bir kapi turudur); NFC normalizasyonu T-006
CIKIS SOZLESMESINE adaydir. Testler:
`test_k32_nfd_govde_bolumlemeyi_degistirir` ve `test_k32_nfd_yalniz_
etiket_segment_sayisini_degistirmez_ama_speakeri_dusurur`.

## Isleme sirasi (K2 -- degistirilemez)

    1. guven esigi filtresi + gecerlilik denetimi (K7)
    2. gurultu eleme: bos/yalniz-bosluk metin + tek-karakter kurali (K4)
    3. satir birlestirme + hyphen cozme (K1, K5)
    4. konusmaci ayiklama (K9)
    5. gruplama -- on ayara gore (K11)
    6. yer tutucu toplama (K6)

Sira SONUCU DEGISTIRIR: bolunmus bir cumlenin ORTASINDAKI esik-alti blok
adim 1'de düşer, bu yuzden adim 3+ o blok hic var olmamis gibi calisir --
kalan iki parca birbirine (hyphen kosulu tutuyorsa) birlesebilir. Bu,
"once filtrele sonra birlestir" sirasinin DOGAL sonucudur, kusur degildir
(bkz. `tests/unit/ocr/test_normalizer.py::test_k2_esik_alti_orta_blok_
komsulari_birlestirir`).

K30 (sef_karari-tur6.md, TUR 6) -- BU CUMLE KOSULLUDUR: adim 1'de dusen
blok, adim 5'te geride GERCEK bir GEOMETRIK BOSLUK birakir. "O blok hic
var olmamis gibi calisir" ifadesi METIN/HYPHEN icin dogrudur, GEOMETRI
icin DEGIL -- artik bosluk esigi ASARSA sinir yalniz-uzunluk siniri
olmaktan cikar ve miras UYGULANMAZ, ASMAZSA miras KORUNUR. Tam ifade ve
iki test icin bkz. `_group` docstring'inin K30 bolumu.

## K1 -- "satir" tanimi

Bu bilesende satir = bir `TextBlock`. Birlestirme BLOKLAR ARASI yapilir.
`TextBlock.line_boxes` bu modulde HIC OKUNMAZ (yalnizca `text`/`bbox`/
`confidence` kullanilir) -- bu yuzden `line_boxes == ()` (sozlesme
varsayilani) her zaman gecerlidir ve sonucu degistirmez; dolu bir
`line_boxes` da sonucu degistirmez (okunmadigi icin).

`TextBlock.text` icinde `\n` geciyorsa: satirlara bolunur, bos satirlar
atilir, kalanlar AYNI blok-arasi birlestirme kuraliyla (hyphen kosulu,
K5) tek metne indirilir -- bu TEK blogun ic-satir birlesimidir, ayri bir
Segment uretmez (`_collapse_intraline`).

BILINEN SINIR (Tester-A, tur 1 feedback-A.md Bulgu 3; davranis
DEGISTIRILMEDI, yalniz BELGELENIYOR -- sef_karari-tur2.md "bloke etmeyen,
belgelenecek"): `_collapse_intraline`, `\n` ICERSIN ICERMESIN HER blok
metnine KOSULSUZ uygulanir (`text.split("\n")` tek-elemanli bir liste
dondurse BILE o TEK eleman yine `strip()` edilir). Bu yuzden `\n`
ICERMEYEN tek-satirlik bir blogun BAS/SON bosluklari da SESSIZCE
kirpilir (ör. `"   Merhaba dunya   "` -> `"Merhaba dunya"`). K6 yalniz
placeholder'larin BIREBIRLIGINI garanti eder (yer tutucunun kendisi
degistirilmez); bas/son genel metin bosluk kirpma bunun disinda, makul
ama paket.md'de AYRICA belirtilmemis bir davranistir.

## K2 -- yukarida.

## K3 -- cikti sirasi

Donen liste `(bbox.y, bbox.x)` artan sirada (`normalize`'in son satiri).
Her `Segment.source_blocks` de artan sirada ve tekrarsizdir (her
birlesim noktasinda `tuple(sorted(...))` ile saglanir).

## K4 -- tek karakter kurali (SINIF tabanli, liste degil) + K18 (tur 2) +
## K20 (olgusal duzeltme, tur 3)

Tek karakterlik (strip sonrasi uzunluk == 1) bir blok/satir:
  - Unicode kategorisi `L*` (harf) veya `N*` (rakam) ise HER ZAMAN KORUNUR
    (tek-kanji `力`/`火`, tek-hangul, tek-kiril harfi, tek rakam dahil).
  - Aksi halde (kategori `M*`, `P*`, `S*`, `Z*`, `C*`) atilir -- TEK
    ISTISNA: karakterin Unicode NFKC NORMALIZASYONU
    (`unicodedata.normalize("NFKC", ch)`) TAM OLARAK `?` veya `!` ise
    korunur (K18, sef_karari-tur2.md, TUR 2). TUR 1'de bu istisna
    literal ASCII `ch in ("?", "!")` ile yaziliydi -- tam-genislik
    (fullwidth) esdegerleri `？` U+FF1F / `！` U+FF01 bu kontrolden
    GECMIYOR, S*/P* dalina dusup SESSIZCE siliniyordu (Bulgu 4,
    Tester-C). NFKC uyumluluk ayristirmasi `？`->`?` ve `！`->`!`
    esler (Unicode'un KENDI tanimi), bu yuzden fullwidth varyantlar
    OTOMATIK kapsanir.

    K20 (sef_karari-tur3.md, TUR 3) -- OLGUSAL DUZELTME, DAVRANIS
    DEGISMEDI: bu docstring ONCEDEN (tur 2) burada KOSULSUZ bir iddiada
    bulunuyordu -- *"ayrica baska hicbir karakter NFKC ile `?`/`!`ye
    ACILMADIGI icin istisna GENISLEMEZ, DARALMAZ"*. Bu iddia YANLISTI.
    Sefin TAM Unicode taramasi (TUM codepoint araligi, 0x0-0x10FFFF)
    NFKC ile `?` veya `!`ye acilan, ASCII DISINDA ALTI karakter daha
    buldu -- ALTISI DA Unicode UYUMLULUK (compatibility) formudur (Tester-C
    bulgu, sef bagimsiz dogruladi; K26, sef_karari-tur5.md -- asagida bu
    cumlenin KENDISI bir kez daha duzeltildi, bkz. o bolum):

        U+FE15  PRESENTATION FORM FOR VERTICAL EXCLAMATION MARK  -> '!'
        U+FE16  PRESENTATION FORM FOR VERTICAL QUESTION MARK     -> '?'
        U+FE56  SMALL QUESTION MARK                              -> '?'
        U+FE57  SMALL EXCLAMATION MARK                           -> '!'
        U+FF01  FULLWIDTH EXCLAMATION MARK                       -> '!'
        U+FF1F  FULLWIDTH QUESTION MARK                          -> '?'

    Davranis DOGRUYDU (altisi de zararsiz `Po` (noktalama) kategorisinde,
    korunmalari isabetli -- bkz. `test_k20_nfkc_ile_acilan_alti_
    karakterin_hepsi_korunur`); YANLIS olan YALNIZCA docstring'in
    "GENISLEMEZ, DARALMAZ" olgusal iddiasiydi. Bu ALTI karakterlik liste
    BILGI AMACLIDIR / bir Unicode TARAMASINDAN TURETILMISTIR -- sabit
    kodlanmis bir BEYAZ LISTE DEGILDIR ve kod bu listeye BAKARAK karar
    VERMEZ: karar hala VE YALNIZCA NFKC denkligiyle alinir
    (`unicodedata.normalize("NFKC", ch) in ("?", "!")`, asagida
    `_is_single_char_noise`). Python'un Unicode surumune gore
    degisebilir (yeni bir surum yeni bir uyumluluk karakteri
    ekleyebilir/kaldirabilir); LISTE BILGI AMACLIDIR, KOD NFKC ILE
    KARAR VERIR.

    K22 (sef_karari-tur4.md, TUR 4) -- SALT DOKUMANTASYON, TESTER-C
    (bloke etmeyen not), DAVRANIS DEGISMEDI: yukaridaki paragraf ONCEDEN
    (tur 3) *"ASCII/fullwidth DISINDA ALTI karakter"* diyordu -- kendi
    listesiyle CELISEN bir ifade, cunku liste fullwidth `！`/`？`'yi
    ZATEN ICERIYOR ("disinda" degil "icinde"). Duzeltme: ifade artik
    *"ASCII DISINDA ALTI karakter"* diyor -- alti karakterin TAMAMI
    ASCII-DISI. Kod HICBIR SATIR degismedi.

    K26 (sef_karari-tur5.md, TUR 5) -- OLGUSAL DUZELTME, K22'NIN KENDI
    OLGUSAL HATASI, DAVRANIS DEGISMEDI: K22 (yukaridaki paragraf) BURADA
    *"ikisi fullwidth, dordu DIGER uyumluluk formlari"* diyordu -- "diger"
    sozcugu, fullwidth ikilinin (U+FF01/U+FF1F) uyumluluk formu
    OLMADIGINI ima ediyordu. YANLIS -- kirmizi takim `unicodedata.
    decomposition` ile OLCTU: ALTI karakterin TAMAMI (fullwidth ikisi
    DAHIL) Unicode UYUMLULUK (compatibility) formudur; fark YALNIZCA
    ayristirma ETIKETIDIR:

        U+FE15  <vertical>  ->  '!'      U+FE56  <small>     ->  '?'
        U+FE16  <vertical>  ->  '?'      U+FE57  <small>     ->  '!'
        U+FF01  <wide>      ->  '!'      U+FF1F  <wide>      ->  '?'

    Dogru ifade: alti karakterin TAMAMI ASCII-DISIDIR VE ALTISI DA
    Unicode uyumluluk formudur; ayristirma ETIKETLERI farklidir -- ikisi
    `<wide>` (fullwidth `！`/`？`), ikisi `<small>`, ikisi `<vertical>`.
    Sayi Python'un Unicode surumune baglidir (bu olcum: Unicode 15.0.0,
    `unicodedata.unidata_version`). "Fullwidth" bu yuzden AYRI bir
    istisna KATEGORISI degil -- ALTI uyumluluk formunun `<wide>` ETIKETLI
    IKI UYESI. Kod HICBIR SATIR degismedi -- bu duzeltme SADECE bu
    docstring'in OLGUSAL ifadesini duzeltir (K20/K22 ile AYNI ilke: kod
    HER ZAMAN dogruydu, yalniz docstring'in OLGUSAL iddiasi hatali
    kurulmustu). Zorunlu test: `test_k26_alti_karakterin_hepsi_uyumluluk_
    formu_ve_etiket_dogru` (tests/unit/ocr/test_normalizer.py)
    -- `unicodedata.decomposition` ile ALTISININ da uyumluluk formu
    OLDUGUNU VE etiket dagilimini (2x `<wide>`, 2x `<small>`, 2x
    `<vertical>`) SABITLER.
  - Beyaz liste YOK: hem asil karar (`unicodedata.category(ch)[0]`)
    hem `?`/`!` istisnasi SINIF/DENKLIK ile alinir, sabit bir karakter
    kumesiyle DEGIL -- K18'in secimi (NFKC denkligi) bilerek bir beyaz
    liste ("belirli fullwidth karakterleri sabit kodla ekle") DEGILDIR;
    yukaridaki K20 listesi de (yeniden) bir beyaz liste DEGILDIR, yalniz
    var olan NFKC kuralinin hangi karakterleri KAPSADIGINI GOSTEREN bir
    dokumantasyon notudur.

## K5 -- hyphen kurali (dil-bagimsiz, geometrik/tipografik)

Kural SADECE ASCII kisa cizgi `-` (U+002D) icin tanimlidir (Unicode `‐`
U+2010, en-dash `–` gibi varyantlar KAPSAM DISI -- bu bilincli bir
daraltmadir, delivery.md `known_gaps`'te de belirtilir). (Onceki, birlesik
yani) satirin STRIP EDILMIS metni `-` ile bitiyor VE bir sonraki
satirin strip edilmis metni KUCUK HARFLE (`str.islower()`) basliyorsa:
iki metin `-` DUSURULEREK, ARA BOSLUKSUZ birlestirilir
(`"tra-" + "dition"` -> `"tradition"`). Aksi halde iki satir bir BOSLUK
ile birlestirilir (K1'in gerektirdigi genel "satir birlestirme").
Kelime ortasindaki tire (`well-known`, satirin SONUNDA degil) hic
etkilenmez -- kural yalnizca satir/blok SONUNDAKI tireye bakar.

`normalize` dil parametresi ALMAZ (sozlesme dondurulmus); dil-kosullu bir
kural gerekmedi, bu yuzden `contract_change_request` acilmadi.

## K6 -- yer tutucular

`Segment.text` ORIJINAL yer tutucuyu BIREBIR korur -- hicbir isaretleme,
sarma veya degistirme YAPILMAZ. `placeholders` alani, NIHAI (gruplama
sonrasi) segment metninde asagidaki dort desenden herhangi birine uyan
TUM eslesmeleri, METINDEKI GECIS SIRASIYLA ve TEKRARLARI KORUYARAK
(tekillestirme YOK) listeler:

  - `{...}`      -- `\{[^{}]*\}`      (ic ice `{}` desteklenmez)
  - `%` + harf   -- `%[a-zA-Z]`       (`%s`, `%d`, `%f`, ... -- SADECE
                    hemen ardindan bir HARF gelen `%`; `"50%"` gibi bir
                    sayinin sonundaki `%` bu deseni EŞLEŞTİRMEZ, cunku
                    ardindan harf yok -- K6 "sayilar placeholders'a
                    girmez" kosulu boylece saglanir)
  - `<...>`      -- `<[^<>]*>`        (bicim/renk etiketi, `<color=..>`)
  - `[...]`      -- `\[[^\[\]]*\]`    (bicim/renk etiketi, `[PlayerName]`)

Sayilarin KENDISI (yalnizca rakam) hicbir desene uymadigi icin asla
`placeholders`'a girmez.

BILINEN SINIR (Tester-A, tur 1 feedback-A.md Bulgu 2; davranis
DEGISTIRILMEDI, yalniz BELGELENIYOR -- sef_karari-tur2.md "bloke
etmeyen, belgelenecek"): bir placeholder token'i TAM OLARAK bir
blok/satir SINIRINA BOLUNMUSSE (ör. bir blokta `"{0"`, BIR SONRAKI
blokta `"} birimdir"`), gruplama bu ikisini ARAYA TEK BOSLUK sokarak
birlestirir (K1/K11 geregi genel satir birlestirme kurali) ve nihai
metin `"... {0 } birimdir"` olur -- `placeholders` alanina GERCEK bir
`{0}` DEGIL, ARADA BOSLUKLU BOZUK bir token (`"{0 }"`) girer. Bu,
placeholder deseninin SADECE nihai/gruplanmis METIN uzerinde calismasinin
(blok sinirlarindan HABERSIZ oldugunun) dogal bir sonucudur; packet.md bu
senaryoyu ele almiyor, K6'nin dort deseni ihlal edilmiyor (tanimlanan
regex birebir uygulaniyor) -- bu yuzden davranis DEGISTIRILMEDI.

## K7 -- guven esigi

Once GECERLILIK: `confidence` `NaN` ise VEYA `[0.0, 1.0]` araligi
DISINDAYSA -- girdideki ORIJINAL sira ile ilk boyle blok bulundugunda --
`ValueError` FIRLATILIR (kurtarma/atlama YOK; T-003'un kirildigi delikle
ayni sinif hata). Gecerlilik NaN kontrolunu `math.isnan` ile ACIKCA yapar
(`if not (c >= th)` gibi bir NaN-yutan karsilastirma KULLANILMAZ --
boyle bir ifade NaN icin sessizce "esik alti" sonucu uretirdi, K7'nin
yasakladigi tam olarak budur). Gecerlilik sonrasi: `confidence < esik` ->
DUSER; `confidence == esik` -> KALIR (`>=` karsilastirmasi).

## K8 -- `source_blocks`

Her zaman ORIJINAL `blocks` dizisinin (fonksiyona GECEN sekliyle,
FILTRELEME ONCESI) 0-tabanli indeksleridir. Bir blok esik/gurultu
filtresinde elenirse VEYA bir konusmaci etiketi olarak sonraki ogeye
tasinmadan (bir baska etiketle GECERSIZ kilinarak ya da liste sonunda
kullanilmadan) duserse indeksi HICBIR Segment'te GORUNMEZ; aksi halde
katildigi (ya da konusmacisini verdigi) TEK segmentin `source_blocks`'unda
gorunur (bkz. K9 -- etiket-blok, kullanildigi durumda, konusmaciyi
devraldigi segmentin `source_blocks`'una DAHIL edilir). Iki farkli
segmentin `source_blocks` kumeleri bu yuzden HER ZAMAN AYRIKTIR (bir
blok en fazla bir segmente katkida bulunur -- birden fazla segmente
bolunen blok senaryosu bu turda YOK, delivery.md `known_gaps`'te belirtilir).

## K9 -- konusmacı + K17 (ayirac genisletme, tur 2)

Blok metni (strip edilmis) `Isim<ayirac>` desenine uyuyorsa (`Isim`:
1-40 karakter, ILK karakter Unicode harf, kalan karakterler yalniz
harf/bosluk/kesme/tire -- HICBIR RAKAM YOK -- boylece `"12:30"` gibi bir
saat metni yanlislikla konusmaci sayilmaz; `<ayirac>`: metindeki EN
SOLDAKI `presets.SPEAKER_LABEL_SEPARATORS` uyesi -- K17, sef_karari-
tur2.md, TUR 2: `:` U+003A VE `：` U+FF1A [tam-genislik, JP/KR
oyunlarinda STANDART]. TUR 1'de yalniz ASCII `:` taniniyordu,
`'勇者：こんにちは'` gibi fullwidth-etiketli bir blok konusmacisiz
kaliyordu -- Bulgu 3, Tester-C. Ayirac kumesi `presets.py`de
adlandirilmis sabit, sabit kodlama YOK -- bkz. `_find_speaker_separator`):
  - `<ayirac>` sonrasi metin BOSSA (strip sonrasi): bu blok HICBIR SEGMENT
    URETMEZ; `Isim` VE bu blogun ORIJINAL indeksi bir sonraki (okuma
    sirasindaki) ogeye TASINIR -- o oge nihayetinde bir segment
    uretirse (KENDI etiketi yoksa), etiket-blogun indeksi o segmentin
    `source_blocks`'una DAHIL EDILIR (K8: bu blok o segmentin
    URETILMESINE katkida bulunmustur). Sonraki oge yoksa (liste biter)
    `Isim` ve indeksi KULLANILMADAN DUSER -- hicbir segmentte gorunmez.
  - `<ayirac>` sonrasi metin DOLUYSA: bu ogenin KENDI konusmacisi `Isim`
    olur, metni etiketten SONRAKI kisimla degistirilir; ONCEKI bir
    bloktan TASINAN bekleyen konusmaci (varsa) bu ogenin KENDI etiketi
    tarafindan GECERSIZ KILINIR -- bekleyen konusmaci VE onun blok
    indeksi KULLANILMADAN duser (o onceki etiket-blok hicbir segmente
    katkida bulunmamis sayilir, ciktiya hicbir etkisi olmadigi icin).
  - Desen uymuyorsa: oge, varsa bekleyen konusmaciyi VE bekleyen
    etiket-blogun indeksini devralir (`source_blocks`'a eklenir; yoksa
    `speaker=None`, ek indeks yok); bekleyen deger her durumda tuketilir
    (bir sonraki ogeye tekrar tasınmaz).

NOT: yukaridaki mekanizma geregi, bir etiket YALNIZ kendisinden SONRAKI
ILK ogeye tasinir -- 3+ bloklu bir govdede (`Isim<ayirac>` + 2 icerik
blogu) 2. oge `speaker=Isim` alir ama 3. oge `speaker=None` KALIR (etiket
2. ogede "tuketildi"). Bu KENDI BASINA bir hata degildir (K9'un tarif
ettigi TAM OLARAK budur); hatanin kaynagi ASAGIDAKI K15 -- eskiden
gruplama bu `None`'u "farkli konusmaci" saniyordu.

### K15 (tur 2) -- gruplama konusmaci matrisi: `None` "farkli konusmaci"
DEGIL, "devam" demektir

TUR 1'DE `_should_group` konusmaci sinirini KATI Python esitligiyle
(`a.speaker != b.speaker`) kontrol ediyordu. Bu, yukaridaki "etiket
SADECE ilk takip-ogesine tasinir" gercegiyle CARPISIYORDU: 3+ bloklu bir
konusmaci govdesinde 2. oge `speaker=Isim`, 3. oge `speaker=None` olunca
eski kod ikisini "farkli konusmaci" sanip ARALARINDAKI gruplamayi
REDDEDIYORDU -- cumle VE konusmaci bilgisi ikiye bolunuyordu
(`['Ada:', 'Bu uzun bir', 'cumledir.']` -> 2 segment, ikincisi
`speaker=None`; Japonca'da BIREBIR ayni -- Bulgu 1/KRITIK, Tester-C,
tasarim dokumani S5.2'nin modulun VAR OLMA SEBEBI olarak verdigi ornegin
ta kendisi). K15 (sef_karari-tur2.md) bunu su matrisle duzeltir --
`_should_group` icinde TAM OLARAK bu tabloya gore uygulanir:

    a.speaker | b.speaker  | gruplama                        | grubun speaker'i
    ----------|------------|----------------------------------|------------------
    X         | X          | EVET                             | X
    X         | None       | EVET (devam satiri)              | X (miras alinir)
    None      | None       | EVET                             | None
    None      | Y          | HAYIR (yeni konusmaci basliyor)  | --
    X         | Y (X != Y) | HAYIR (konusmaci siniri)         | --

Kosul (kod): `a.speaker != b.speaker and not (a.speaker is not None and
b.speaker is None)` -> `True` ise gruplama REDDEDILIR. K9'un ASIL niyeti
(iki FARKLI, adlandirilmis konusmaci ASLA birlesmez) TAMAMEN korunur --
degisen TEK sey, etiketsiz bir DEVAM satirinin (`b.speaker=None` iken
`a.speaker=X`) ARTIK "farkli konusmaci" SAYILMAMASIDIR. Birlesen grubun
`speaker` degeri HER ZAMAN "a" tarafinin (mevcut grubun/soldaki ogenin)
`speaker`'idir (`_group`: `current.speaker`) -- X/None satirinda bu X'i
DOGAL olarak MIRAS aldirir (`current` zaten X'i tasiyor, degismiyor);
digger satirlarda zaten esit veya `None`'dir.

Gruplama (adim 5) hala FARKLI (ikisi de None-degil VE birbirinden farkli)
konusmacili komsu ogeleri ASLA birlestirmez -- yukaridaki tablonun son
satiri.

`normalize` HICBIR KOSULDA metni bos/yalniz-bosluk olan bir `Segment`
dondurmez -- son adimda `if g.text.strip()` filtresiyle guvenceye alinir
(tasarim geregi zaten bu asamaya kadar bos metin uretilmez; bu satir
savunma amaclidir).

## K10 -- `bbox` birlesimi + K16 (yozlasmis geometride gruplama yok, tur 2)

Iki oge birlestiginde (hyphen birlesimi VEYA gruplama) yeni bbox, iki
kaynagin KAPSAYICI dikdortgenidir (`x=min`, `y=min`, sag/alt kenar =
`max(right)`/`max(bottom)`). `monitor_index` veya `dpi_scale` FARKLIYSA
`ValueError` (sessiz kopyalama YOK) -- `_union_rect`. TEK bloktan olusan
bir segment icin bu kontrol hic calismaz (birlesim yok).

Butun geometrik karsilastirmalar (`_should_group`) CARPMA ile yapilir
(`gap < oran * yukseklik`), BOLME ile DEGIL -- boylece `bbox.h == 0` veya
`bbox.w == 0` durumunda (yozlasmis girdi) bolme hatasi OLUSMAZ.

TUR 1'DE bu docstring "ilgili kosul basitce 'gruplama yok' tarafina
duser" diye KOSULSUZ bir iddiada bulunuyordu; bu SADECE `bbox.w == 0`
icin dogruydu (sifir-genislikli bir kutu HICBIR kutuyla pozitif yatay
ortusmeye giremez -- `right = x + w = x`, bu her zaman `min(a.right,
b.right) - max(a.x, b.x) <= 0` sonucunu geometrik olarak ZORUNLU kilar,
yani `overlap` DAIMA `<=0` cikar). `bbox.h == 0` (veya NEGATIF `h`) icin
bu YANLISTI: eski kod yalniz `gap > 0` ise reddediyordu; kutular dikeyde
DEGIYORSA veya CAKISIYORSA (`gap <= 0`) yatay ortusme yeterliyse
GRUPLUYORDU (Bulgu 2, Tester-A, sef_karari-tur2.md -- ilk sef sondasi da
hatali kuruldugu icin bunu once dogrulayamadi, PROTOKOL S3 kapi 6 ikinci
kez sefin UZERINDE calisti).

K16 (tur 2) bunu duzeltir: `_should_group` icinde `ref_height =
min(a.bbox.h, b.bbox.h)` VEYA `ref_width = min(a.bbox.w, b.bbox.w)`
`<= 0` (yani YOZLASMIS -- sifir veya NEGATIF) ise gruplama KOSULSUZ
REDDEDILIR, `gap`/`overlap` degerine BAKILMAKSIZIN (iki ayri erken-cikis
`return False`, birbirinden BAGIMSIZ). `ref_width <= 0` dali davranis
OLARAK degismedi (zaten matematiksel olarak her zaman reddediyordu, bkz.
yukarida) -- yalniz KOSULSUZ hale getirilerek `ref_height` dali ile
SIMETRIK ve okunakli kilindi. Boylece bu paragrafin ilk cumlesindeki
iddia artik HEM `w==0` HEM `h==0` (VE HER IKISININ negatif hallerinde)
icin DOGRUDUR: yozlasmis geometride bir gruplama karari VERILEMEZ, cunku
karar icin gereken olcu YOK -- gurultulu bir OCR kutusunun komsusunu
SESSIZCE yutmasi kabul edilmez (sef_karari-tur2.md, K16 gerekcesi;
alternatif -- "sadece iddiayi daralt" -- ACIKCA REDDEDILDI).

## K11 -- gruplama

`dialogue`/`tooltip`/`subtitle` -> gruplar; `menu` -> gruplamaz (her oge
kendi Segment'i olur). Preset'ler arasindaki SAYISAL farklar SADECE
`presets.py`deki `NormalizerParams` alanlaridir (guven esigi, dikey
bosluk orani, maksimum grup karakter sayisi). Yatay ortusme esigi
(`_MIN_HORIZONTAL_OVERLAP_RATIO`) TUM presetler icin SABIT ve PAYLASILAN
bir degerdir (preset basina degismez) -- packet.md'nin "diger fark
SADECE ... (guven esigi, dikey bosluk orani, maksimum grup uzunlugu)"
cumlesiyle tutarli: yatay ortusme bu ucluye dahil degil, bu yuzden
preset parametresi yapilmadi (delivery.md `known_gaps`'te de belirtilir).

### K27 (tur 5) -- `menu` K19/K21/K23/K24'un KAPSAMI DISINDADIR, BILINCLI

`menu` icin `params.should_group` `False`'tur (yukarida); bu yuzden
`normalize` adim 5'te `_group`'u HIC CAGIRMAZ (`grouped = items`
dogrudan). K19/K21/K23/K24'un TAMAMI `_group`'un ICINDE yasar --
`_group` cagirilmadigi icin bu dort kararin HICBIRI `menu` icin
TANIMSIZDIR: "uzunluk yuzunden bolunme" kavraminin KENDISI `menu`'de
YOKTUR (hicbir sey gruplanmadigi icin bolunecek bir grup da yoktur).
`_extract_speakers` (K9) HALA `menu` icin de calisir (adim 4, gruplama
ONCESI) -- yani bir etiket-blok (`Isim<ayirac>`) `menu`'de de kendisinden
SONRAKI ILK ogeye konusmaciyi tasir; ama o ogeden SONRAKI (etiketsiz,
"devam" olabilecek) bir ucuncu oge `menu`'de speaker=None KALIR --
`dialogue`/`tooltip`/`subtitle`'da K15/K19/K21/K23 bu ogeyi ONCEKI
grubun devami sayip (kosullar tutuyorsa) MIRAS aldirirdi, `menu`'de bu
HIC OLMAZ, cunku miras mekanizmasi `_group`'un ICINDEDIR ve `_group` hic
calismamistir. Bu, K11'in ASIL karari geregi BILINCLI VE belgelenmis bir
KAPSAM DISIDIR (sef_karari-tur5.md, K27) -- implementer'in kendi UYDUR-
DUGU bir daraltma DEGILDIR, sef'in ACIKCA yazdigi bir sinirdir.

**Zorunlu test** (dort on ayarin HER biri icin bir test,
`tests/unit/ocr/test_normalizer.py`, `# --- TUR 5 ---` basligi altinda):
AYNI "etiket + govde1 (SIKI gruplanir) + govde2 (etiketsiz, DEVAM
olabilecek)" fixture'u DORT on ayarla da calistirilir --
`dialogue`/`tooltip`/`subtitle`'da govde2 `speaker`'i MIRAS ALIR
(gruplama + K15/K19/K21/K23 devrede); `menu`'de govde2 AYRI bir segment
olarak KALIR VE `speaker=None`'DUR (gruplama YOK, K27'nin tarif ettigi
kapsam disi BIREBIR gozlemlenir).

## K19 (tur 3) -- uzunluk bolunmesinde konusmaci mirasi

TUR 2'YE KADAR (K15 dahil) `_group` bir cifti REDDETTIGINDE -- REDDIN
SEBEBI NE OLURSA OLSUN -- yeni grup dogrudan `nxt` ile basliyordu;
`nxt.speaker` HER ZAMAN NE ISE O KALIYORDU (cogunlukla `None`, cunku K9
bir etiketi YALNIZ ILK takip-ogesine tasir -- bkz. yukaridaki K9
bolumundeki NOT). Bu, SADECE UZUNLUK siniri (`params.max_group_chars`)
yuzunden bolunen govdelerde SESSIZ bilgi kaybina yol aciyordu (Tester-C,
tur 2'de "bloke etmeyen" bulundu; sef tur 3'te YENIDEN SINIFLANDIRDI --
bloke edici):

    girdi : "Ada:" + 5 uzun govde blogu (toplam uzunluk max_group_chars'i asiyor)
    cikti : speaker='Ada'  src=(0,1,2,3)  len=275
            speaker=None   src=(4,5)      len=183   <- Ada'nin DEVAMI, bilgi kayboluyor

Asagi akis (ceviri katmani) `speaker=None` gordugunde "konusmacisi yok"
ile "bir oncekinin DEVAMI" ayirt edemez -- Japonca gibi dillerde zamir/
hitap/nezaket seviyesi secimi konusmaci KIMLIGINE baglidir (tasarim
dokumani S5.2, sef_karari-tur3.md).

K19 karari, BOLUNME SEBEBINE gore ikiye ayirir:

    bolunme sebebi                            | kuyruk segmentin speaker'i
    -------------------------------------------|---------------------------
    `max_group_chars` asildi (SADECE uzunluk)  | MIRAS ALIR -- ayni
                                                | konusmacinin devami, KESIN
    geometrik bosluk / farkli `speaker` /      | `None` KALIR -- yeni baglam
    yozlasmis bbox (K16)                       | OLABILIR, atfetmek spekulasyon

Gerekce (sef_karari-tur3.md): `max_group_chars` BIZIM koydugumuz YAPAY
bir sinir -- metnin KENDISINDE bir kopus YOK, kesinlikle ayni
konusmacinin devami. Geometrik bosluk (K15'in `None/Y`, `X/Y` satirlari;
K16'nin yozlasmis-bbox reddi) ise METNIN KENDISINDEN gelen bir sinyal --
oraya konusmaci atfetmek UYDURMA olur.

Mekanizma (`_group_rejection_reason`, `_group`) -- K21 (tur 4) ile
DUZELTILMIS HALI, tam gerekce ve bulgu icin asagidaki "## K21" bolumune
bkz.: `_should_group`'un kullandigi HER reddetme kosulu ayri bir REASON
KODU olarak dondurulur -- `"speaker"`, `"length"`, `"height"`, `"gap"`,
`"width"`, `"overlap"` (`_group_rejection_reason`; `_should_group` bunun
`is None` KISALTMASIDIR -- IMZASI/DAVRANISI DEGISMEDI, K15 matris
testleri HALA DOGRUDAN `_should_group`'u cagirir ve bool bekler, bkz.
`tests/unit/ocr/test_normalizer.py::test_k15_matris_*`). `_group`, reddin
REASON'I `"length"` ISE VE mevcut grubun `speaker`'i `None`-DEGILSE VE
`nxt.speaker` `None` ISE VE (K21) `max_group_chars` SONSUZ olsaydı bu
cift YINE DE gruplanacak MIYDI (yani `length` kontrolu ATLANDIGINDA
`_group_rejection_reason` `None` DONUYOR MU) -- YALNIZ O ZAMAN `nxt`'i
(yeni grubun ilk ogesi olarak) mevcut grubun `speaker`'iyla
`dataclasses.replace` eder (MIRAS). Diger TUM reddetme sebeplerinde
(`"speaker"`, `"height"`, `"gap"`, `"width"`, `"overlap"`) VE `"length"`
ile AYNI ANDA BASKA bir kontrol de basarisiz olan bilesik durumlarda (K21)
bu miras UYGULANMAZ -- `nxt` KENDI speaker'iyla (cogunlukla `None`, veya
kendi etiketiyle geldiyse o etiket) yeni grubun basi olur; K15'in matrisi
(ozellikle `None/Y` ve `X/Y` ASLA birlesmez satirlari) K19/K21 SONRASI da
BIREBIR ayni sekilde gecerlidir -- K19/K21 SADECE `_should_group` `False`
DONDUKTEN SONRAKI, `_group`'un yeni grubu NASIL basladigi adimina
dokunur, `_should_group`'un KENDI kararina (kimin gruplanip kimin
gruplanmayacagina) DOKUNMAZ.

`Segment.speaker`'daki `None` degerinin ARTIK IKI ayri anlami var VE
bunlar ALAN DUZEYINDE (deger olarak) AYIRT EDILEMEZ -- bu BILINEN bir
sinirdir, K19 bunu GIDERMEZ, YALNIZCA uzunluk-kaynakli kaybi giderir:
  - "ETIKET YOK" -- bu icerik icin hicbir zaman bir `Isim<ayirac>` bloku
    GORULMEDI (K9'un normal, etiketsiz durumu; ya da K9'un "liste burada
    biter" / "bir sonraki etiketle GECERSIZ kilinir" dallari).
  - "BILINMIYOR/ATFEDILEMEZ" -- bu segment ETIKETLI bir grubun ARDINDAN
    geliyor ama aralarinda GEOMETRIK bir kopus var (K15 `None/Y`/`X/Y`
    siniri ya da K16 yozlasmis-bbox reddi); segment BELKI ayni
    konusmacinin devami BELKI yeni bir baglam -- karar VERILEMEDIGI icin
    `None` KALIR (spekulasyon YAPMAMAK tercih edilir).

**Sozlesme degisikligi YOK.** `Segment` (`src/contracts/models.py`)
DONDURULMUS; `continues_previous` gibi yeni bir alan EKLENMEDI -- miras
alma cozumu MEVCUT `speaker: str | None` alani icinde yeterlidir
(sef_karari-tur3.md, "Sozlesme degisikligi yok" karari).

## K21 (tur 4) -- bilesik sinirda miras duzeltmesi

TUR 3'TE (K19 dahil) `_group`, reddin REASON'I TAM OLARAK `"length"`
STRING'INE ESIT MI diye bakiyordu -- ve `_group_rejection_reason` sabit
bir SIRAYLA (`speaker -> length -> height -> gap -> width -> overlap`)
calisip YALNIZ ILK basarisiz kontrolun kodunu dondurdugu icin, bir cift
AYNI ANDA HEM uzunluk sinirini asiyor HEM geometrik olarak kopuksa (ör.
aralarinda buyuk bir dikey bosluk VAR, ama zaten birlikte
`max_group_chars`'i da asiyorlar) `length` GEOMETRI kontrolunden ONCE
kontrol edildigi icin kod hep `"length"` donduruyordu -- geometrik kontrol
HIC CALISMIYORDU. K19 bu yuzden YANLISLIKLA miras uyguluyordu: bolunmenin
GERCEK sebebi (geometrik kopus) gizleniyor, kuyruk segment konusmaciyi
MIRAS ALIYORDU (Tester-C, tur 3'te "bloke edici" bulundu; sef kendi
eliyle yeniden uretti ve dogruladi -- bkz. `.agents/tasks/T-004/
sef_karari-tur4.md`, `.agents/tasks/T-004/feedback-C.md`):

    _group_rejection_reason ciktilari (TUR 3, DUZELTME ONCESI):
      sadece uzunluk (yakin bloklar)     -> "length"
      uzunluk + BUYUK dikey bosluk       -> "length"   <- gecersiz miras
      uzunluk + h=0 (yozlasmis bbox)     -> "length"   <- gecersiz miras

Bu, K19'un KENDI gerekcesini de gecersiz kilan bir durumdu: K19'un
mirasi haklı cikaran gerekce *"`max_group_chars` BIZIM koydugumuz YAPAY
bir sinir, metinde bir kopus YOK"* idi -- ama bilesik durumda metnin/
geometrinin KENDISINDE GERCEK bir kopus VARDI, sadece `length` sirada
ONCE kontrol edildigi icin gorunmuyordu.

**Kok sebep şefin K19 kararinda:** K19 red sebeplerinin BIRBIRINI
DISLADIGINI varsaymisti (bir ciftin AYNI ANDA yalniz TEK bir kontrolden
reddedilebilecegi). Dislamiyorlar -- bir cift AYNI ANDA birden fazla
kontrolden basarisiz olabilir; `_group_rejection_reason` SIRALI oldugu
icin bunlardan yalniz ILKINI raporlar, ama K19'un miras kosulu SIRADAKI
ILK sebebi degil GERCEK (TEK) sebebi bilmesi GEREKIRDI.

**Yeni kural** (denk iki ifade):

  - Kuyruk segment konusmaciyi YALNIZ `max_group_chars` TEK BASINA
    gruplamayi engelliyorsa MIRAS alir. Baska HERHANGI bir kontrol de
    (geometri, konusmaci, yozlasmis bbox) basarisizsa MIRAS YOK.
  - Esdeger: `max_group_chars` SONSUZ olsaydi bu cift gruplanir miydi?
    EVET ise tek engel uzunluktur -> MIRAS al. HAYIR ise gercek bir
    kopus var -> `speaker=None` KALIR.

**Uygulama** (SECENEK 1 -- `sef_karari-tur4.md`'nin sundugu iki
secenekten biri, burada secilen): `_group_rejection_reason`'a
KEYWORD-ONLY, VARSAYILANI `False` olan bir `ignore_length: bool`
parametresi eklendi -- `True` ise fonksiyon UZUNLUK kontrolunu (`"length"`
donme yolunu) ATLAR, dogrudan geometri kontrollerine GECER (konusmaci
kontrolu HALA EN ONCE calisir, degismedi). `_group`, bir cift
`"length"` REASON'IYLA reddedildiginde (VE mevcut grubun `speaker`'i
`None`-degilse VE `nxt.speaker` `None`'sa) `_group_rejection_reason`'i
`ignore_length=True` ile IKINCI KEZ cagirir: sonuc `None` ise (yani
uzunluk kontrolu DISINDA HICBIR kontrol reddetmiyor -- `max_group_chars`
sonsuz olsaydi cift gruplanirdi) MIRAS uygulanir; sonuc `None`-DEGILSE
(geometri/konusmaci/yozlasmis-bbox kontrollerinden EN AZ biri de HALA
basarisiz) MIRAS UYGULANMAZ.

Bu secim, `_should_group`'un DIS IMZASINI (`(_Item, _Item,
NormalizerParams) -> bool`) VE tur 3'te AST ile ispatlanan
`_should_group` <-> `_group_rejection_reason` YAPISAL AYRISMAZLIGINI
(tek satirlik devretme deseni: `return _group_rejection_reason(a, b,
params) is None`) HICBIR SEKILDE BOZMAZ -- `_should_group`'un GOVDESI
TEK BIR KARAKTER bile degismedi (`ignore_length` VARSAYILAN `False`
oldugu icin `_should_group`'un mevcut cagrisi ETKILENMEZ); yalniz
`_group_rejection_reason`'in (PRIVATE, `_should_group`'un DISINDA
DOGRUDAN test edilmeyen bir yardimci) imzasina keyword-only bir
parametre eklendi VE `_group`'un miras KARARI, `_group_rejection_
reason`'i tekrar cagiran bu ikinci (ayri) kontrole baglandi.
`speaker` kontrolunun `length`'ten ONCE gelmesi de DEGISMEDI -- bu
sira sayesinde X/Y (farkli konusmaci) ve None/Y ciftleri HER ZAMAN
`"speaker"` reason'ini alir, `length`'in golgesine hic DUSMEZ (K15
matrisinin son iki satiri buna bagli).

**Regresyon testleri** (`tests/unit/ocr/test_normalizer.py`, `# --- TUR
4 ---` basligi altinda): uzunluk TEK engel -> miras VAR (ASCII ve
Japonca) · uzunluk + BUYUK dikey bosluk -> miras YOK · uzunluk + `h=0`
-> miras YOK · uzunluk + `w=0` -> miras YOK · uzunluk + yetersiz yatay
ortusme -> miras YOK · uzunluk + farkli konusmaci -> miras YOK (reason
zaten `"speaker"`, `length` yoluna hic girilmiyor) · uc VE daha fazla
parcaya bolunen bir zincirde HER bolunme noktasi KENDI sebebine gore
degerlendiriliyor (bazilari miras aliyor bazilari almiyor, AYNI
zincirde).

**TUR 5'TE BULUNAN BULGU (K23/K24, asagida): bu mekanizmanin (yukarida
tarif edilen "IKINCI cagri" yontemi) KENDISI, farkli bir hataya
yol aciyordu -- yeni bulgunun VE yeni (K23/K24) kararin tam metni,
mekanizmanin tur 5'te NASIL yeniden yazildigi asagidaki "## K23/K24"
bolumundedir. K19/K21'in KURALI (SONUC -- hangi kosulda miras uygulanir)
DEGISMEDI; DEGISEN yalniz `_group`'un bu karari NASIL uyguladigi
(uygulama YONTEMI).**

## K23/K24 (tur 5) -- bolumleme DEGISMEZI ve K21'in TEK gecerli ifadesi

**Kaynak:** `.agents/tasks/T-004/sef_karari-tur5.md`. Tur 4'te
implementer K21/K22'yi DOGRU uyguladi ve sef DOGRULADI -- ama bu turde
ILK KEZ devreye alinan KARAR KIRMIZI TAKIMI, sefin KARARLARINDA (kodun
KENDISINDE degil) 12 bulgu cikardi, UCU yuksek siddetli. Sef ucunu de
kendi eliyle yeniden uretti ve DOGRULADI.

### Bulgu B1 (yuksek) -- miras BOLUMLEMEYI degistiriyordu

Tur 4'un mekanizmasi (yukarida): `_group` bir grubu `"length"`
sebebiyle kapatirken `nxt`'i (yeni grubun BASI) `dataclasses.replace`
ILE mevcut grubun `speaker`'ini TASIYACAK sekilde MUTE EDIYORDU, ve bu
MUTE EDILMIS `nxt` doğrudan `current`'e ATANIYORDU (`current = nxt`).
Sonraki dongu adiminda bu (ARTIK MUTE EDILMIS) `current`, BIR SONRAKI
ciftin `_group_rejection_reason` cagrisina `a` olarak GIRIYORDU --
yani miras, kendi UYDURDUGU `speaker` degerini bir sonraki GRUPLAMA
KARARINA girdi yapiyordu:

    VARYANT A (onceki sinir uzunluk-tek -> miras VAR):
       speaker='Ada'  src=(0, 1)
       speaker='Ada'  src=(2, 3)      <- b2 ve b3 BIRLESTI

    VARYANT B (onceki sinir bilesik -> miras YOK):
       speaker='Ada'  src=(0, 1)
       speaker=None   src=(2,)        <- ayri kaldi
       speaker='Ada'  src=(3,)

b2<->b3 GEOMETRISI ve METNI iki varyantta da AYNI -- TEK fark ONCEKI
sinirdaki miras kararidir. Mekanizma: K15 matrisinde `None/Y -> hayir`
satiri, sol taraf `None`'dan (b2'nin OZGUN, OCR'dan gelen speaker'i)
`Ada`'ya (mute edilmis, MIRAS alinmis deger) CEVRILDIGI icin `Ada/Ada ->
evet` satirina DONUSUYOR -- b3 KENDI `Ada:` etiketiyle gelen YENI bir
replik oldugu halde, b2'nin (miras yoluyla TASIDIGI, kendi degeri
OLMAYAN) `speaker`'iyla ESLESIP onun KUYRUGUNA YAPISIYOR. Iki AYRI
sozce TEK `Segment` oluyor -- JP/KR oyunlarinda her replik satiri
konusmaci adiyla YENIDEN etiketlendigi icin bu BIRINCIL hedef kitlede
STANDART bir senaryo.

### K23 -- DEGISMEZ (mekanizma DEGIL)

Sefin onceki kararlari (K9, K19, K21) hep MEKANIZMA olarak yazildi ("su
kosulda sunu yap") ve ETKILESIMLERI GORUNMEDI. K23 bu yuzden bir
DEGISMEZ olarak yazilir:

> **DEGISMEZ:** Herhangi bir girdi icin, `normalize` ciktisinin
> **BOLUMLEMESI** -- `Segment.source_blocks` demetlerinin dizisi --
> miras mekanizmasi ACIKKEN ve KAPALIYKEN **BIREBIR AYNI** olmalidir.
> Miras **YALNIZCA** `Segment.speaker` degerini degistirebilir. `text`,
> `bbox`, `source_blocks`, `placeholders` ve segment **SAYISI** miras
> kararindan ETKILENEMEZ.

### Uygulama -- iki-gecisli (`_group`, tur 5'te YENIDEN YAZILDI)

Dogrudan yol secildi (sef_karari-tur5.md'nin onerdigi): gruplama
KARARLARI ogenin OCR'dan gelen OZGUN `speaker` degerini KULLANIR; miras
YALNIZCA kapanan grubun `Segment`'i URETILIRKEN uygulanir. `_group`
ARTIK IKI ayri gecisten olusur:

  1. **Bolumleme gecisi** (`apply_inheritance` parametresinden TAMAMEN
     BAGIMSIZ): okuma-sirali komsu ogeler `_group_rejection_reason`
     kosuluna gore birlestirilir -- TIPKI oncesi gibi -- ama `current`/
     `nxt`'in `speaker` alani bu gecis BOYUNCA **HICBIR ZAMAN** mute
     EDILMEZ (K19/K21'in eski "ikinci cagriya bagli `replace`" satiri
     dongudEN COKARILDI). Her kapanan grup icin (grubun `current`'i
     `groups`'a eklenirken) `reason == "length"` VE `nxt.speaker is
     None` VE (K24, asagida) grubun KUYRUK ogesiyle `nxt` arasinda
     `ignore_length=True` cagrisi `None` DONUYORSA -- bu sinirin "SADECE
     uzunluk sinirli" OLDUGU bir bayrak (`pure_length_boundary`)
     KAYDEDILIR (uygulanmaz, sadece KAYDEDILIR). Bu gecisin URETTIGI
     `groups` listesi (her `_Item`'in `text`/`bbox`/`source_blocks`/
     ORIJINAL `speaker`'i) **BOLUMLEMENIN KENDISIDIR** ve `apply_
     inheritance`'tan ETKILENMEZ -- K23'un DEGISMEZI bu YUZDEN
     YAPI GEREGI (mekanizma HATASI degil, TASARIM) saglanir.
  2. **Goruntu gecisi** (`apply_inheritance` `True` ISE, yani `normalize`
     her zaman): bolumleme TAMAMEN BITTIKTEN SONRA, `groups` uzerinde
     SOLDAN SAGA TEK bir ek gecis yapilir -- `pure_length_boundary[i]`
     isaretliyse VE `groups[i-1].speaker is not None` ise
     `groups[i] = dataclasses.replace(groups[i], speaker=groups[i-1].
     speaker)`. Bu gecis `groups`'un `text`/`bbox`/`source_blocks`
     alanlarina HICBIR SEKILDE DOKUNMAZ -- SADECE `speaker` alanini
     GUNCELLER, VE bu guncelleme HICBIR gruplama KARARINA GERI
     BESLENMEZ (bolumleme ZATEN bitmistir). SOLDAN SAGA islendigi icin
     zincirleme miras (bir grubun KENDISI de miras almissa, SONRAKI
     `None`-basli grup ONDAN da miras alabilir) DOGAL olarak ORTAYA
     CIKAR -- bu, K19'un "kesinlikle ayni konusmacinin devami" gerekce-
     sinin UZUN (birden fazla uzunluk-sinirina CARPAN) bir monologda da
     TUTARLI kalmasini saglar; hicbir MEVCUT test bunun TERSINI
     BEKLEMIYOR (`test_k21_zincirde_her_bolunme_noktasi_kendi_sebebine_
     gore_degerlendirilir` zincirdeki IKINCI sinirin BILESIK oldugunu,
     yani zincirlemenin bu testte HIC devreye GIRMEDIGINI, dogrular).

`apply_inheritance` -- `_group`'a eklenen KEYWORD-ONLY, VARSAYILANI
`True` olan parametre -- SADECE bu IKI gecisin GORUNUM (2.) gecisini
ACIP KAPATIR; bolumleme (1.) gecisi HER ZAMAN calisir ve HER IKI degerde
de BIREBIR AYNI `groups`'u uretir (K23'un makineyle DENETLENDIGI TAM
BUDUR). `normalize`'in KENDISI bu parametreyi HICBIR SEKILDE DISARI
ACMAZ (GENEL API'YE SIZMAZ) -- `normalize(blocks, preset)` imzasi
DEGISMEDI. Test kancasi: `_normalize_impl(blocks, preset, *,
apply_inheritance: bool = True)` -- `normalize`'in GERCEK govdesi,
`normalize` bunu SABIT `True` ile cagirir; `tests/unit/ocr/
test_normalizer.py` bu IC fonksiyonu DOGRUDAN import EDER (K23
denetimi icin `apply_inheritance=False` ile CAGIRIR).

**Zorunlu makine denetimi (K23):** `test_k23_miras_acik_kapali_
bolumleme_degismezi_fuzz` -- sabit tohum, **2500 rastgele girdi**
(>=2000), DORT on ayarin HEPSI, yozlasmis geometri (sifir/negatif `w`/
`h`) DAHIL, `_normalize_impl(..., apply_inheritance=True)` ile `...
apply_inheritance=False)`'nin `[s.source_blocks for s in cikti]`
dizilerini (VE `text`/`bbox`/`placeholders`/segment SAYISINI) KARSILAS-
TIRIR. **TEK BIR fark bile testi KIRAR.** Ayrica B1'in BIREBIR AYNI
senaryosu (etiketli govde + kendi etiketiyle gelen UCUNCU blok) tek bir
regresyon testiyle SABITLENDI --
`test_k23_kendi_etiketiyle_gelen_kuyruk_mirastan_dolayi_yanlislikla_
birlesmiyor` -- b2/b3 AYRI segment KALIR (VARYANT B), ARTIK Varyant A'ya
DUSMEZ.

### K24 -- K21'in TEK gecerli ifadesi (esdegerlik IPTAL)

Tur 4'teki "denk ve daha kolay uygulanabilir ifade" cumlesi **IPTAL**.
Kirmizi takim OLCTU: iki ifade denk DEGIL, 4000 rastgele girdi/11.656
ardisik segment ciftinde ~%2 AYRISIYOR. Sebep: "bu cift" TANIMSIZDI --
birikmis grubun BIRLESIK `bbox`'i mi, grubun SON blogu mu belirsizdi, ve
kirmizi takim IKISININ ZIT sonuc UREDEBILDIGINI gosterdi (birlesik kutu
grubun EN ALTA uzanan ogesinin `bottom`'unu tasiyip GERCEK satir-arasi
boslugu OLCMEZ -- NEGATIF `gap` ARTIFAKTI uretip "kopus YOK" diyebilir,
oysa grubun GERCEK KUYRUGU ile aday arasinda BUYUK bir bosluk olabilir).

**Gecerli TEK ifade:**

> Ayni `(a, b)` cifti, `_should_group`'un kontrollerinden **YALNIZCA
> uzunluk kontrolu CIKARILARAK** yeniden degerlendirilir. Baska hicbir
> kontrol REDDETMIYORSA uzunluk TEK engeldir.
>
> Bu degerlendirmede **SOL TARAF, kapanan grubun okuma sirasindaki SON
> KAYNAK OGESIDIR** -- birikmis grubun birlesik `bbox`'i **DEGIL**.

**Uygulama:** `_group` artik `current` (birikmis/birlesik `_Item`) ile
PARALEL bir `tail: _Item` degiskeni TUTAR -- her BASARILI birlesimde
(`current` GUNCELLENDIGINDE) `tail = nxt` (birlesime KATILAN, HAM,
BIREYSEL oge) ATANIR; her YENI grup basladiginda `tail = nxt` (yeni
grubun TEK ogesi) ile SIFIRLANIR. K21'in `ignore_length=True` IKINCI
cagrisi ARTIK `_group_rejection_reason(current, nxt, ...)` DEGIL,
`_group_rejection_reason(tail, nxt, ...)` KULLANIR -- yani SOL TARAF
DAIMA grubun okuma-sirasindaki EN SON (birlesime en son KATILAN) HAM
ogesidir, `current`'in (birden fazla oge ICEREBILEN) BIRLESIK `bbox`'i
DEGIL.

**Kapsam:** bu degisiklik SADECE K19/K21/K23'un miras UYGUNLUK kontrolu
icindir -- `_group`'un ANA (`current` ile `nxt` arasindaki) BIRLESTIRME
KARARI HALA `current` (birikmis/birlesik) kullanir, K10/K11'in "birlesik
bbox kaynak bloklarin KAPSAYICI dikdortgenidir" tanimi VE mevcut
gruplama SEMANTIGI (ör. `test_k10_bbox_birlesimi_kapsayici`) DEGISMEDI
-- YALNIZ K21'in IKINCI (miras-uygunluk) sorgusu icin SOL TARAFIN HANGI
oge OLDUGU degisti.

**Zorunlu test:** `test_k24_kuyruk_ile_birlesik_bbox_farkli_sonuc_verir`
-- en az BIR ogesi SONRAKILERDEN daha AŞAĞI uzanan (yani grubun
BIRLESIK `bbox`'inin `bottom`'unu TASIYAN oge grubun BASINDA, KUYRUKTA
DEGIL) COK bloklu bir grubun KUYRUGUNDA bu ayrimi SABITLER: `current`
(birlesik) ile yapilan `ignore_length=True` sorgusu YANLISLIKLA `None`
(gap KUCUK gorunur, MIRAS UYGULANIRDI) donerken, `tail` ile yapilan AYNI
sorgu DOGRU sekilde `"gap"` DONER (GERCEK kopus GORULUR, MIRAS
UYGULANMAZ) -- VE `normalize()` UZERINDEN uctan-uca `test_k24_
normalize_uzerinden_kuyruk_temelli_kontrol_yanlis_mirasi_onler` bunun
GERCEK pipeline'da da dogru DAVRANDIGINI dogrular.

## K12 -- bos sonuclar

Bos girdi -> `[]`. Tum bloklar esik alti -> `[]` (kurtarma YOK). Gurultu
elendikten sonra hicbir sey kalmadi -> `[]`. Ucu de ozel-durum kodu
GEREKTIRMEZ: bos listeler pipeline boyunca dogal olarak akar.

## K13 -- determinizm

Yukarida aciklandigi gibi: `set` KULLANILMAZ. Butun coklu-indeks
birlesimleri `tuple(sorted((*a, *b)))` ile yapilir (int `sorted`,
PYTHONHASHSEED'den etkilenmez; zaten `set` de kullanilmadigi icin bu
soru bu modulde hic gundeme gelmez).

## K14 -- performans butcesi

Bu modul kendi icinde butce OLCMEZ (saf fonksiyon, zaman bagimliligi
YASAK). Olcum VE `assert` `tests/unit/ocr/test_normalizer.py` icindedir
(K14, budget_ms=5, medyan uzerinden, 30 blok/~40 karakter, dialogue,
50 tekrar).

## Yozlasmis girdiler -- hicbiri cokmez

  - `bbox.w == 0` / `bbox.h == 0` / negatif `w`/`h`: cokmez -- gruplama
    kosullari carpma ile kurulmus, bolme yok; `Rect.right`/`Rect.bottom`
    yine `x+w`/`y+h` hesaplanir (Rect'in kendi property'si), min/max
    aritmetigi bunlarla da cokmez. K16 (tur 2): boyle bir blok BASKA bir
    ogeyle KOMSU (gruplama adayi) oldugunda, `_should_group` bu ciftin
    `ref_height`/`ref_width`'inin `<= 0` oldugunu tespit edip gruplamayi
    KOSULSUZ REDDEDER (bkz. K10 bolumu) -- blok TEK BASINA (gruplama
    disi) normal islenir, kendi ic-degeri degismez; sonuc dikdortgeni
    (birlesim DISINDA) gorsel olarak anlamsiz olabilir ama hicbir islem
    exception firlatmaz.
  - Bos/yalniz-bosluk `text`: adim 2'de gurultu olarak elenir (segment
    uretmez, cokmez).
  - `line_boxes == ()`: zaten okunmaz (K1).
  - `confidence` NaN/alan disi: K7 -- ACIKCA `ValueError` (bu, "cokme"
    degil, sozlesmenin GEREKTIRDIGI gurultulu hata).
  - Tek blok / bos liste / 30'dan cok blok: genel dongulerde ozel durum
    KODU yok, hepsi ayni yoldan gecer.
  - Farkli `monitor_index`/`dpi_scale`: K10 -- ACIKCA `ValueError`.
"""
from __future__ import annotations

import math
import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass, replace

from src.contracts.models import OcrPreset, Rect, Segment, TextBlock

from .presets import SPEAKER_LABEL_SEPARATORS, NormalizerParams, get_params

__all__ = ("normalize",)
"""Tuple -- liste degil: `purity_check.py` modul duzeyinde MUTABLE global
(list/dict/set) arar; `__all__` de -- Python acisindan gecerli olan --
tuple bicimiyle yazilir."""


_PLACEHOLDER_PATTERN = re.compile(r"\{[^{}]*\}|%[a-zA-Z]|<[^<>]*>|\[[^\[\]]*\]")
"""K6 -- dort placeholder deseni, tek gecişte METIN SIRASIYLA toplanir."""

_MIN_HORIZONTAL_OVERLAP_RATIO: float = 0.30
"""K11 -- gruplama icin yatay ortusme esigi, TUM presetlerde SABIT
(preset parametresi degil -- bkz. modul docstring'i K11 bolumu). Iki oge
arasindaki yatay ortusme genisligi, DAR olan ogenin genisliginin bu
orandan BUYUK olmalidir (`overlap > oran * min(w1, w2)`, carpma ile,
bolme degil)."""

_MAX_SPEAKER_NAME_LEN: int = 40
"""K9 -- `Isim:` deseninde `Isim` icin en fazla karakter sayisi. Cok
uzun bir on-ek (ör. sıradan bir cumlenin ortasindaki bir ':' oncesi
metin) yanlislikla konusmaci sayilmasin diye sinirlandirilmistir."""


@dataclass(frozen=True)
class _Item:
    """Boru hattinin ic (yari-mamul) birimi -- ne `TextBlock` ne `Segment`.

    Frozen: her donusum YENI bir `_Item` uretir (mutasyon yok), boylece
    ara adimlarda kazara paylasilan durum olusmaz.
    """

    text: str
    bbox: Rect
    speaker: str | None
    source_blocks: tuple[int, ...]


def normalize(blocks: Sequence[TextBlock], preset: OcrPreset) -> list[Segment]:
    """OCR bloklarini cevrilmeye hazir `Segment` listesine indirger.

    Tam davranis sozlesmesi bu modulun UST docstring'indedir (K1-K14,
    K15-K18 [tur 2], K19-K22 [tur 3/4], K23-K27 [tur 5], K28-K32 [tur
    6], yozlasmis girdiler). GIRDININ NFC OLDUGU VARSAYILIR (K32 --
    NFD girdi hem konusmaci tanimayi hem BOLUMLEMEYI degistirir).
    Ozet: 6 sabit adim (K2) -- esik filtresi, gurultu eleme,
    satir birlestirme+hyphen, konusmaci ayiklama, on-ayara-gore
    gruplama, yer tutucu toplama. Cikti okuma sirasindadir (K3). Saf
    fonksiyon: I/O yok, global mutasyon yok, rastgelelik yok.

    Bu fonksiyon `_normalize_impl`'in (asagida) SABIT `apply_
    inheritance=True` ile cagrilmasidir -- GENEL IMZA (`(blocks, preset)
    -> list[Segment]`) TUR 5'te DEGISMEDI VE DEGISMEYECEK; K23'un
    miras-acik/miras-kapali DENETIM kancasi `_normalize_impl`'in KENDISI
    (bkz. o fonksiyonun docstring'i) -- buraya SIZMAZ.

    Raises:
        ValueError: bir `TextBlock.confidence` `NaN` ya da `[0,1]`
            disindaysa (K7); VEYA birlesecek iki `TextBlock`/oge farkli
            `bbox.monitor_index` ya da `bbox.dpi_scale` tasiyorsa (K10).
    """
    return _normalize_impl(blocks, preset)


def _normalize_impl(
    blocks: Sequence[TextBlock], preset: OcrPreset, *, apply_inheritance: bool = True
) -> list[Segment]:
    """`normalize`'in GERCEK govdesi (K1-K14, K15-K18, K19-K22, K23-K27).

    `apply_inheritance` (KEYWORD-ONLY, VARSAYILANI `True`) SADECE K23'un
    MAKINE DENETIMI icin vardir -- `normalize` bunu HER ZAMAN `True` ile
    cagirir ve DISARIYA hicbir sekilde ACMAZ, yani GENEL API'YE (`normalize`
    'in KENDI imzasi) SIZMAZ (sef_karari-tur5.md, K23: "test kancasi
    ... genel API'ye sizmayacak"). `tests/unit/ocr/test_normalizer.py`
    bu IC fonksiyonu DOGRUDAN import EDER ve K23 denetimi icin `apply_
    inheritance=False` ile cagirir.

    `False` ISE adim 5'teki `_group` cagrisi K19/K21/K23'un GORUNUM
    (ikinci) gecisini ATLAR -- BOLUMLEME (`source_blocks` dizisi, VE
    `text`/`bbox`/`placeholders`/segment SAYISI) `True` ile BIREBIR
    AYNIDIR, YALNIZ bazi segmentlerin `speaker` alani `None` KALIR
    (miras UYGULANMAMIS olur). Bu, K23 DEGISMEZININ (bkz. modul
    docstring'i "## K23/K24") tanimi/ispatidir -- `_group`'un ARTIK IKI
    ayri gecisten olusmasi sayesinde (bkz. `_group` docstring'i)
    bolumleme gecisi bu bayraktan YAPI GEREGI ETKILENMEZ.

    K28 (TUR 6): adim 5'teki `_group` cagrisi `blocks=blocks` ile
    yapilir -- `blocks`, bu fonksiyona verilen OZGUN dizidir (adim 1'de
    esik-alti diye ELENEN bloklar DAHIL; `source_blocks` indeksleri o
    dizinin indeksleridir, K8). Suzulmus/sikistirilmis bir liste
    gecirmek miras-uygunluk sorgusunda INDEKS KAYMASINA yol acar.
    """
    _validate_confidences(blocks)
    params = get_params(preset)

    ordered = sorted(enumerate(blocks), key=lambda pair: (pair[1].bbox.y, pair[1].bbox.x))

    # 1. guven esigi filtresi
    items: list[_Item] = [
        _Item(text=block.text, bbox=block.bbox, speaker=None, source_blocks=(idx,))
        for idx, block in ordered
        if block.confidence >= params.confidence_threshold
    ]

    # 2. gurultu eleme (bos/yalniz-bosluk + tek-karakter kurali, K4)
    items = [it for it in items if not _is_noise(it.text)]

    # 3. satir birlestirme (blok-ici \n collapse, K1) + hyphen cozme (K5)
    items = [replace(it, text=_collapse_intraline(it.text)) for it in items]
    items = _merge_hyphenated(items)

    # 4. konusmaci ayiklama (K9)
    items = _extract_speakers(items)

    # 5. gruplama -- on ayara gore (K11); menu icin _group HIC cagirilmaz (K27)
    # K28 (TUR 6): `blocks=blocks` -- OZGUN (adim 1'de elenenler DAHIL) liste
    # gecirilmek ZORUNDADIR; suzulmus bir liste indeks kaymasi uretir.
    grouped = (
        _group(items, params, blocks=blocks, apply_inheritance=apply_inheritance)
        if params.should_group
        else items
    )

    # 6. yer tutucu toplama (K6) + Segment insasi
    segments = [
        Segment(
            text=g.text,
            bbox=g.bbox,
            speaker=g.speaker,
            placeholders=tuple(m.group(0) for m in _PLACEHOLDER_PATTERN.finditer(g.text)),
            source_blocks=tuple(sorted(g.source_blocks)),
        )
        for g in grouped
        if g.text.strip()
    ]

    return sorted(segments, key=lambda s: (s.bbox.y, s.bbox.x))


def _validate_confidences(blocks: Sequence[TextBlock]) -> None:
    """K7: `NaN` veya `[0,1]` disi ilk `confidence`'ta `ValueError`.

    Orijinal (girdi) sirada tarar -- hata mesaji deterministik olsun diye.
    `math.isnan` ACIKCA kullanilir: `c < esik` veya `not (c >= esik)`
    turu bir ifade NaN'i SESSIZCE yutar (NaN ile her karsilastirma
    `False` doner) -- K7'nin yasakladigi tam olarak budur.
    """
    for idx, block in enumerate(blocks):
        c = block.confidence
        if math.isnan(c) or not (0.0 <= c <= 1.0):
            raise ValueError(
                f"TextBlock[{idx}].confidence gecersiz: {c!r} "
                "(NaN olamaz, [0.0, 1.0] araliginda olmali)"
            )


def _is_noise(text: str) -> bool:
    """K4 + K12: bos/yalniz-bosluk VEYA tek-karakter-gurultu ise `True`.

    Tek karakter kurali SINIF tabanlidir (bkz. modul docstring K4) --
    sabit bir karakter listesi YOKTUR.
    """
    stripped = text.strip()
    if not stripped:
        return True
    if len(stripped) != 1:
        return False
    return _is_single_char_noise(stripped)


def _is_single_char_noise(ch: str) -> bool:
    """Tek bir karakter icin K4 karari. `ch` tam olarak uzunluk-1 olmali.

    K18 (sef_karari-tur2.md, TUR 2): `?`/`!` istisnasi literal ASCII
    karsilastirma DEGIL, Unicode NFKC normalizasyon DENKLIGI ile
    tanimlanir -- `？` U+FF1F / `！` U+FF01 gibi tam-genislik
    (fullwidth) varyantlar NFKC ile `?`/`!`ye acilir, boylece istisna
    OTOMATIK olarak onlari da kapsar (TUR 1'de yalniz ASCII kapsaniyordu,
    fullwidth tek-karakterli bloklar SESSIZCE siliniyordu).

    K20 (sef_karari-tur3.md, TUR 3, SALT DOKUMANTASYON -- bu fonksiyonun
    DAVRANISI degismedi): karar hala VE YALNIZCA NFKC denkligiyle
    alinir, sabit bir karakter listesine BAKILMAZ. Modul-ust docstring'in
    K4 bolumunde, sefin tam Unicode taramasinin bulduğu NFKC ile `?`/`!`ye
    acilan ALTI karakterin (ASCII disinda, ALTISI DA Unicode uyumluluk
    formu -- K26, sef_karari-tur5.md: ayristirma ETIKETLERI farklidir,
    ikisi `<wide>`/fullwidth, ikisi `<small>`, ikisi `<vertical>`)
    BILGI AMACLI tam listesi VE bu listedeki onceki (tur 2 VE tur 4)
    OLGUSAL hatalarin duzeltilmesi belgelenir (K22/K26, sef_karari-
    tur4.md/sef_karari-tur5.md -- K20'nin KENDI ifadesindeki "ASCII/
    fullwidth disinda" sozunun listenin fullwidth `！`/`？` icermesiyle
    CELISTIGI (K22) VE ardindan K22'nin KENDI "dordu DIGER uyumluluk
    formu" ifadesinin fullwidth ikilinin uyumluluk formu OLMADIGINI ima
    ETTIGI (K26) duzeltildi; kod bu iki duzeltmeden de ETKILENMEDI)."""
    category = unicodedata.category(ch)
    if category[0] in ("L", "N"):
        return False
    if unicodedata.normalize("NFKC", ch) in ("?", "!"):
        return False
    return True


def _join_line(prev: str, nxt: str) -> str:
    """K5: `prev` `-` ile bitiyor VE `nxt` kucuk harfle basliyorsa
    tireyi dusurup ARA BOSLUKSUZ birlestir; aksi halde TEK BOSLUKLA
    birlestir. `prev`/`nxt` bos-olmayan (strip edilmis) kabul edilir --
    cagiranlar bunu garanti eder."""
    if prev.endswith("-") and nxt[:1].islower():
        return prev[:-1] + nxt
    return prev + " " + nxt


def _collapse_intraline(text: str) -> str:
    """K1: blok metnindeki `\\n`'leri, AYNI (K5) birlestirme kuraliyla
    tek satira indirger. Bos ara satirlar atilir. Girdi zaten
    `_is_noise` filtresinden gectigi icin sonuc her zaman bos-olmayandir."""
    lines = [ln.strip() for ln in text.split("\n")]
    non_empty = [ln for ln in lines if ln]
    if not non_empty:
        return ""
    result = non_empty[0]
    for nxt in non_empty[1:]:
        result = _join_line(result, nxt)
    return result


def _union_rect(a: Rect, b: Rect) -> Rect:
    """K10: kapsayici dikdortgen. `monitor_index`/`dpi_scale` FARKLIYSA
    `ValueError` (sessiz kopyalama yok)."""
    if a.monitor_index != b.monitor_index or a.dpi_scale != b.dpi_scale:
        raise ValueError(
            "birlesecek bloklarin monitor_index/dpi_scale degerleri uyusmuyor: "
            f"({a.monitor_index}, {a.dpi_scale}) != ({b.monitor_index}, {b.dpi_scale})"
        )
    x = min(a.x, b.x)
    y = min(a.y, b.y)
    right = max(a.right, b.right)
    bottom = max(a.bottom, b.bottom)
    return Rect(x=x, y=y, w=right - x, h=bottom - y, monitor_index=a.monitor_index, dpi_scale=a.dpi_scale)


def _merge_hyphenated(items: list[_Item]) -> list[_Item]:
    """K1 + K5: okuma sirasindaki komsu ogeleri, hyphen kosulu tutuyorsa
    birlestirir (bloklar-arasi satir birlestirme).

    K28-KOK (sef_karari-tur6.md, TUR 6 -- BILINCLI ve ACIK BIRAKILMIS
    SINIR): ADIM 3 SALT TIPOGRAFIKTIR (K5) ve HICBIR GEOMETRIK KONTROL
    YAPMAZ -- tire satirin son karakteriyse ve sonraki satir kucuk harfle
    basliyorsa iki oge, ARALARINDAKI GEOMETRIK MESAFEYE BAKILMAKSIZIN
    birlesir. Bulgu R5-1'in KOKU BUDUR: adim 3 COK BLOKLU `_Item`'lar
    uretir ve o `_Item`'in `bbox`'i BIRLESIK kutudur. Sef bu koku tur
    6'da BILINCLI olarak ACIK BIRAKTI -- adim 3 salt tipografiktir ve
    OYLE KALIR; K28 SEMPTOMU kapatir, koku DEGIL.

    Birlesik oge geometrisi ADIM 5'in MIRAS kararina HIC GIRMEZ: sorgu
    aninda `_raw_query_pair` onun yerine OZGUN bloklari koyar (K28).
    BOLUMLEME kararina ise birlesik `bbox` ile GIRER (K10/K11) -- bu
    ayrim K28'in KAPSAM cumlesidir ve olcu kitinin KAPSAM kanaliyla
    denetlenir."""
    if not items:
        return []
    result: list[_Item] = []
    buffer = items[0]
    for nxt in items[1:]:
        if buffer.text.endswith("-") and nxt.text[:1].islower():
            merged_text = buffer.text[:-1] + nxt.text
            merged_bbox = _union_rect(buffer.bbox, nxt.bbox)
            merged_blocks = tuple(sorted((*buffer.source_blocks, *nxt.source_blocks)))
            buffer = _Item(text=merged_text, bbox=merged_bbox, speaker=None, source_blocks=merged_blocks)
        else:
            result.append(buffer)
            buffer = nxt
    result.append(buffer)
    return result


def _find_speaker_separator(text: str) -> int:
    """K17 (sef_karari-tur2.md, TUR 2): `text` icinde
    `presets.SPEAKER_LABEL_SEPARATORS` kumesindeki HERHANGI bir ayiracin
    EN SOLDAKI (en kucuk indeksli) gorulme noktasini dondurur; hicbiri
    yoksa `-1`. Kumedeki HER ayirac TEK codepoint (uzunluk 1) kabul
    edilir -- cagiran (`_split_speaker_label`) donen indeksi `idx + 1`
    ile diler, bu varsayima dayanir."""
    best = -1
    for sep in SPEAKER_LABEL_SEPARATORS:
        pos = text.find(sep)
        if pos != -1 and (best == -1 or pos < best):
            best = pos
    return best


def _split_speaker_label(text: str) -> tuple[str | None, str]:
    """K9 + K17 (tur 2): `text` `Isim<ayirac>` ile basliyorsa
    `(Isim, kalan)`, aksi halde `(None, text)`. `<ayirac>`:
    `_find_speaker_separator` -- `presets.SPEAKER_LABEL_SEPARATORS`
    kumesindeki EN SOLDAKI eslesme (K17: ASCII `:` + fullwidth `：`).
    `Isim`: ilk karakter Unicode harf, geri kalani yalniz harf/bosluk/
    kesme/tire, uzunluk `_MAX_SPEAKER_NAME_LEN` altinda -- rakam icermez
    (`"12:30"` gibi bir metin konusmaci sayilmaz).

    K32 (sef_karari-tur6.md, TUR 6) -- GIRDI NFC VARSAYIMI: `normalize`
    girdinin **NFC** oldugunu VARSAYAR. Buradaki ad suzgeci CODEPOINT
    BAZLI `isalpha()`'dir; NFD adlar (birlesik aksan -- `'Mari' + U+0301
    + 'a'`) konusmaci SAYILMAZ (birlesen aksan `Mn` kategorisindedir,
    `isalpha()` `False` doner), etiket METINDE kalir (K31/b yolu). Sef
    olctu: `'María: hola'` NFC -> `speaker='María'`; NFD -> `speaker=
    None`, `text` etiketi TASIR. Varsayim BU SUZGECLE SINIRLI DEGILDIR
    -- MODUL DUZEYINDEDIR; tam kapsam ve bolumleme etkisi icin bkz. modul
    ust docstring'inin "## K32" bolumu."""
    idx = _find_speaker_separator(text)
    if idx <= 0:
        return None, text
    name = text[:idx].strip()
    rest = text[idx + 1 :].strip()
    if not name or len(name) > _MAX_SPEAKER_NAME_LEN:
        return None, text
    if not name[0].isalpha():
        return None, text
    if not all(ch.isalpha() or ch in " '-" for ch in name):
        return None, text
    return name, rest


def _extract_speakers(items: list[_Item]) -> list[_Item]:
    """K9: konusmaci etiketlerini ayiklar. Yalniz-etiket ogeler
    (`Isim:` sonrasi bos) segment uretmez; etiket VE o ogenin orijinal
    `source_blocks`'u bir sonraki ogeye tasinir -- o oge KENDI etiketi
    olmadan bir segment uretirse, tasinan indeksler o segmentin
    `source_blocks`'una eklenir (K8). Bir sonraki oge KENDI etiketini
    tasiyorsa VEYA liste burada biterse, bekleyen etiket VE indeksi
    KULLANILMADAN duser."""
    result: list[_Item] = []
    pending_speaker: str | None = None
    pending_blocks: tuple[int, ...] = ()
    for it in items:
        name, rest = _split_speaker_label(it.text)
        if name is not None and not rest:
            pending_speaker = name
            pending_blocks = tuple(sorted((*pending_blocks, *it.source_blocks)))
            continue
        if name is not None:
            result.append(replace(it, text=rest, speaker=name))
            pending_speaker = None
            pending_blocks = ()
            continue
        merged_blocks = tuple(sorted((*pending_blocks, *it.source_blocks)))
        result.append(replace(it, speaker=pending_speaker, source_blocks=merged_blocks))
        pending_speaker = None
        pending_blocks = ()
    return result


def _group_rejection_reason(
    a: _Item, b: _Item, params: NormalizerParams, *, ignore_length: bool = False
) -> str | None:
    """K11 karari + K19/K21 (tur 3/tur 4) mekanizmasi: `a` (mevcut
    grubun son ogesi) ile `b` (aday sonraki oge) GRUPLANMALI MI -- ve
    GRUPLANMIYORSA NEDEN? `_should_group`'un uyguladigi HER kontrolu
    AYNI SIRAYLA calistirir, ama `False` yerine hangi kontrolun
    REDDETTIGINI gosteren bir REASON KODU dondurur (gruplanmaliysa
    `None`):

        `"speaker"`  -- konusmaci sinirini asiyor (K9 + K15)
        `"length"`   -- `params.max_group_chars` asiliyor (K11)
        `"height"`   -- `ref_height <= 0`, yozlasmis (K10 + K16)
        `"gap"`      -- dikey bosluk esigi asiliyor (K11)
        `"width"`    -- `ref_width <= 0`, yozlasmis (K10 + K16)
        `"overlap"`  -- yatay ortusme esigi altinda (K11)

    Bu ayrim SADECE `_group`'un K19 (sef_karari-tur3.md) mirasini --
    "`max_group_chars` YUZUNDEN bolunen bir grubun kuyrugu konusmaciyi
    MIRAS alir, diger butun sebeplerde `None` kalir" -- uygulayabilmesi
    icin vardir (bkz. modul docstring K19 bolumu). `_should_group` bu
    fonksiyonun `is None` KISALTMASIDIR; DIS IMZA/DAVRANIS (bool) hic
    degismedi.

    `ignore_length` (K21, sef_karari-tur4.md, TUR 4, KEYWORD-ONLY,
    VARSAYILAN `False` -- BU parametre EKLENMEDEN once bu fonksiyonun
    davranisi/imzasi neyse `ignore_length` VERILMEDIGINDE/`False`
    OLDUGUNDA HALA AYNIDIR): `True` ISE uzunluk kontrolu (`"length"`
    donme yolu) TAMAMEN ATLANIR -- konusmaci kontrolu HALA EN ONCE
    calisir (degismedi), ama uzunluk asilsa BILE fonksiyon GEOMETRI
    kontrollerine GECER. Bu, `_group`'un "`max_group_chars` SONSUZ
    olsaydi bu cift gruplanir miydi?" sorusunu SORABILMESI icindir (K21
    -- bkz. modul docstring "## K21" bolumu): REDDIN TEK sebebi uzunluksa
    `ignore_length=True` ile cagrildiginda sonuc `None` olur (miras
    UYGULANIR); REDDIN BASKA bir sebebi de VARSA (geometri/konusmaci/
    yozlasmis-bbox) `ignore_length=True` ile cagrildiginda da BASKA bir
    reason KODU doner (miras UYGULANMAZ). BULGU (Tester-C, tur 3, sef
    dogruladi): `ignore_length` EKLENMEDEN once `_group`, REDDIN
    `"length"` OLUP OLMADIGINA (SIRADAKI ILK basarisiz kontrol) BAKIYORDU
    -- bir cift AYNI ANDA hem uzunluk SINIRINI hem GERCEK bir geometrik
    kopusu asiyorsa `"length"` speaker/height/gap/width/overlap
    kontrollerinden ONCE geldigi icin GEOMETRIK kopus HIC GORULMUYOR,
    kod YANLISLIKLA miras uyguluyordu. `ignore_length` bu ayrimi (TEK
    engel uzunluk MU, yoksa uzunlukla BIRLIKTE BASKA bir engel de VAR MI)
    ACIKCA sorulabilir kilar.

    Konusmaci (K9 + K15, sef_karari-tur2.md TUR 2): asagidaki kosul
    `True` ise `"speaker"` REDDIYLE SONUCLANIR --
    `a.speaker != b.speaker and not (a.speaker is not None and
    b.speaker is None)`. Yani: iki FARKLI, ikisi de None-DEGIL
    konusmaci VEYA `b` YENI bir konusmaci basliyorsa (`a.speaker is
    None`, `b.speaker` degil) REDDEDILIR; ama `a` etiketli (X) iken `b`
    etiketsizse (None -- K9'un "etiket sadece ilk takip ogesine
    tasinir" davranisinin DOGAL sonucu, bir DEVAM satiri) bu ARTIK
    "farkli konusmaci" SAYILMAZ (bkz. modul docstring K15 tablosu, 5
    satirin TAMAMI). Bu kontrol `ignore_length`'ten ETKILENMEZ VE HER
    ZAMAN uzunluk kontrolunden ONCE calisir -- X/Y ve None/Y ciftleri
    boylece `length`'in golgesine HICBIR ZAMAN dusmez.

    Maksimum grup karakteri (K11, `params.max_group_chars`) -- SADECE
    `ignore_length` `False` (varsayilan) ISE kontrol edilir; asilirsa
    REDDEDILIR (`"length"`).

    Geometri (K10 + K16, tur 2): `ref_height = min(a.bbox.h, b.bbox.h)`
    VEYA `ref_width = min(a.bbox.w, b.bbox.w)` `<= 0` (yozlasmis --
    sifir/negatif) ise gruplama KOSULSUZ REDDEDILIR, `gap`/`overlap`
    degerine BAKILMAKSIZIN. Aksi halde dikey bosluk/yatay ortusme
    esikleri CARPMA ile (`gap < oran * yukseklik`, `overlap > oran *
    genislik`), BOLME ile DEGIL denenir.

    K24 (sef_karari-tur5.md, TUR 5) -- ÇAGIRAN SORUMLULUGU, bu fonksiyon
    DEGISMEDI: `_group`, K19/K21/K23'un miras-uygunluk sorgusu icin
    `ignore_length=True` ile bu fonksiyonu cagirdiginda, `a` parametresi
    olarak kapanan grubun BIRIKMIS/BIRLESIK `_Item`'ini (`current`)
    DEGIL, grubun okuma-sirasindaki SON (birlesime en son katilan) HAM
    ogesini (`tail`) GECIRIR -- cunku birlesik `bbox` grubun EN ALTA
    uzanan ogesinin `bottom`'unu tasiyabilir (grup ICINDE monotonik
    OLMAYAN bir dikey uzanim varsa) ve bu GERCEK satir-arasi boslugu
    (`gap`) YANLIS (ozellikle YANLISLIKLA kucuk/negatif) OLCEBILIR --
    bkz. modul docstring "## K23/K24" bolumu VE `_group`'un docstring'i.
    Bu fonksiyonun KENDISI `a`'nin "tail" mi "current" mi oldugunu
    BILMEZ/AYIRT ETMEZ -- sadece iki `_Item` alir; ayrim TAMAMEN
    CAGIRANIN (`_group`) SORUMLULUGUDUR."""
    if a.speaker != b.speaker and not (a.speaker is not None and b.speaker is None):
        return "speaker"
    if not ignore_length and len(a.text) + 1 + len(b.text) > params.max_group_chars:
        return "length"

    gap = b.bbox.y - a.bbox.bottom
    ref_height = min(a.bbox.h, b.bbox.h)
    if ref_height <= 0:
        return "height"
    if not (gap < params.max_vertical_gap_ratio * ref_height):
        return "gap"

    overlap = max(0, min(a.bbox.right, b.bbox.right) - max(a.bbox.x, b.bbox.x))
    ref_width = min(a.bbox.w, b.bbox.w)
    if ref_width <= 0:
        return "width"
    if not (overlap > _MIN_HORIZONTAL_OVERLAP_RATIO * ref_width):
        return "overlap"

    return None


def _should_group(a: _Item, b: _Item, params: NormalizerParams) -> bool:
    """K11: `a` (mevcut grubun son ogesi) ile `b` (aday sonraki oge)
    gruplanmali mi? `_group_rejection_reason(a, b, params) is None`
    KISALTMASIDIR -- tam kural gerekcesi VE K19/K21 (tur 3/tur 4)
    reason-kodu mekanizmasi icin bkz. `_group_rejection_reason`. Bu
    fonksiyonun DIS IMZASI (iki `_Item` + `NormalizerParams` -> `bool`)
    K19 ILE DE K21 ILE DE DEGISMEDI -- `tests/unit/ocr/
    test_normalizer.py::test_k15_matris_*` HALA dogrudan bunu cagirir.
    K21 (sef_karari-tur4.md, TUR 4) `_group_rejection_reason`'a
    KEYWORD-ONLY, VARSAYILANI `False` olan bir `ignore_length` parametresi
    ekledi -- bu satir o parametreyi HIC GECMEDIGI icin (varsayilan
    kullanilir) K21'den ETKILENMEDI, GOVDESI TEK KARAKTER DEGISMEDI. K28
    (TUR 6) de bu fonksiyona DOKUNMADI: ham-blok ikamesi YALNIZCA miras-
    uygunluk sorgusunun (`ignore_length=True`) cagri noktasindadir."""
    return _group_rejection_reason(a, b, params) is None


def _raw_query_pair(
    tail: _Item, nxt: _Item, blocks: Sequence[TextBlock]
) -> tuple[_Item, _Item]:
    """K28 (sef_karari-tur6.md, TUR 6): miras-uygunluk sorgusunun IKI
    tarafinin da geometrisini OZGUN `TextBlock` listesinden turetir.

    Doner: `(sol, sag)` --
      - `sol` = `tail`in KOPYASI, `bbox` yerine `tail.source_blocks` icinde
        OKUMA SIRASINDA SON gelen ozgun blogun `bbox`'i;
      - `sag` = `nxt`in KOPYASI, `bbox` yerine `nxt.source_blocks` icinde
        OKUMA SIRASINDA ILK gelen ozgun blogun `bbox`'i.

    OKUMA SIRASI = `(bbox.y, bbox.x, girdi indeksi)` ARTAN -- `_normalize_
    impl`'in ADIM 1'de kullandigi kararli `sorted(enumerate(blocks),
    key=(y, x))` cagrisiyla AYNI siradir. Ucuncu bilesen (girdi indeksi)
    bugunku kodda davranissal bir NO-OP'tur (`source_blocks` K8 geregi
    artan ve `sorted` kararlidir, yani esitlikte ikili anahtar zaten girdi
    indeksine duser -- sef olctu: 200.000 ornekte 0 ayrisma); tanimi K8'e
    BAGIMLI olmaktan cikarmak icin ACIKCA yazilir.

    NEDEN (bulgu R5-1, Tester-A sol taraf + kirmizi takim sag taraf, sef
    ikisini de kendi eliyle yeniden uretti): K2'nin sirasinda ADIM 3
    (`_merge_hyphenated`, K5) ADIM 5'ten (`_group`) ONCE calisir ve
    hyphen'li satirlari TEK bir `_Item`'a birlestirir -- o `_Item`'in
    `bbox`'i BIRLESIK kutudur. `_group` onu `tail` (ya da `nxt`) olarak
    kullanirsa K24'un kaldirdigi artifakt adim 3 uzerinden GERI gelir:
    birlesik kutu gercek satir-arasi kopusu GIZLER (`gap` yanlislikla
    kucuk/negatif, `ref_height`/`ref_width` yanlislikla buyuk, `overlap`
    UYDURULMUS) ve `speaker` gercek kopusun OTESINE atfedilir. Sag tarafta
    ayni artifakt bir K16 ihlalini de gizler: adayin ham ILK satirinin
    `h == 0` olmasi birlesik kutuda gorunmez. Olcum (A'nin derlemi):
    30.174 sinirin %5,2'si; sag tarafta birlesik aday iceren 2065 sinirin
    242'si, 239'u tehlikeli yonde.

    `source_blocks[-1]` / `[0]` KULLANILMAZ: `source_blocks` K8 geregi
    artan INDEKS sirasindadir, K3 geregi girdi listesi OKUMA sirasinda
    OLMAK ZORUNDA DEGILDIR; en buyuk indeks ile okuma sirasindaki son blok
    AYNI SEY DEGILDIR (sef olctu: 25.460 sinirin %3,2'sinde, sirasiz
    girdilerde %8,5'inde ayrisiyorlar; sirasiz girdide `[-1]` segment
    uretmeyen bir ETIKET blogunu bile gosterebilir).

    IKAME YALNIZ `bbox`'a dokunur: `dataclasses.replace` ile `speaker`,
    `text` VE `source_blocks` AYNEN KORUNUR. `speaker`/`text` bu cagri
    noktasinda OLU alanlardir (cagri `nxt.speaker is None` ile kisa devre
    olur ve `ignore_length=True` uzunluk kontrolunu atlar) -- ikisini de
    ham bloktan alan bir uygulama DAVRANISSAL olarak esdegerdir (sef
    olctu: dort on ayar x 4000 girdi, 0 ayrisma); kural OKUNABILIRLIK ve
    `ignore_length` bir gun kaldirilirsa DOGRULUK icindir.
    `source_blocks`'un korunmasi da urun davranisi icin OLU bir alandir
    ama OLCUNUN ONKOSULUDUR: olcu kitinin kancasi yalnizca `(a, b,
    params)` gorur, `tail`/`nxt` KIMLIGI baska hicbir kanaldan geri
    kazanilamaz.

    SOZLESME -- `blocks` OZGUN listedir: `normalize`'a verilen `blocks`
    dizisinin KENDISI (adim 1'de esik-alti diye ELENEN bloklar DAHIL;
    indeksler OZGUN indekslerdir). Suzulmus/sikistirilmis bir liste
    gecirmek INDEKS KAYMASINA yol acar -- bunu olcu 5'in AST yarisi
    (`_normalize_impl` icindeki `_group(...)` cagrisi `blocks=blocks`
    yaziyor mu) ve, derlem esik-alti blok icerdiginde, olcu 6 yakalar.

    `blocks` YETERSIZSE `IndexError` yukselir (bkz. `_group`'un `blocks=()`
    varsayilani) -- bu BILINCLIDIR: sessiz yanlis uretmek yerine gurultulu
    kirilir."""

    def reading_order(idxs: tuple[int, ...]) -> list[int]:
        return sorted(idxs, key=lambda i: (blocks[i].bbox.y, blocks[i].bbox.x, i))

    left_idx = reading_order(tail.source_blocks)[-1]
    right_idx = reading_order(nxt.source_blocks)[0]
    return (replace(tail, bbox=blocks[left_idx].bbox), replace(nxt, bbox=blocks[right_idx].bbox))


def _group(
    items: list[_Item],
    params: NormalizerParams,
    *,
    blocks: Sequence[TextBlock] = (),
    apply_inheritance: bool = True,
) -> list[_Item]:
    """K11: `params.should_group` `True` iken okuma-sirali komsu ogeleri
    `_group_rejection_reason` kosuluna gore birlestirir. Metinler TEK
    BOSLUKLA birlestirilir (hyphen kurali burada uygulanmaz -- o adim
    3'te bitmistir; adim 5 tamamen geometrik/konusmaci tabanlidir).

    K15 (tur 2): birlesen grubun `speaker`'i HER ZAMAN `current.speaker`
    (soldaki/mevcut grubun konusmacisi) olur -- X/None gruplandiginda bu
    X'i DOGAL olarak MIRAS aldirir (current zaten X tasiyor, degismez);
    digger izinli kombinasyonlarda (X/X, None/None) zaten esittir. Bu
    davranis K19/K21/K23'ten TAMAMEN BAGIMSIZDIR -- asagidaki IKI
    gecisin HICBIRI bu satiri (`speaker=current.speaker`) DEGISTIRMEZ.

    TUR 5 (K23/K24, sef_karari-tur5.md) -- BU FONKSIYON YENIDEN YAZILDI.
    Tur 4'un mekanizmasi (K19/K21) `nxt`'i (yeni grubun basi) miras
    alacaksa `dataclasses.replace` ILE HEMEN mute EDIYOR ve bu mute
    EDILMIS `_Item`'i DOGRUDAN `current`'e atiyordu -- SONRAKI dongu
    adiminda bu mute EDILMIS `current.speaker`, BIR SONRAKI ciftin
    `_group_rejection_reason` cagrisina `a` olarak GIRIYOR, yani MIRAS
    kendi UYDURDUGU degeri bir sonraki GRUPLAMA KARARINA girdi yapiyordu
    -- Tur 5 kirmizi takiminin B1 bulgusu (bkz. modul docstring "##
    K23/K24"): kendi ETIKETIYLE gelen bir SONRAKI oge, mirasla ayni ada
    sahip OLDUGU icin YANLISLIKLA onun kuyruguna YAPISIYORDU (`X/X ->
    evet` satirina yanlislikla DUSEREK), BOLUMLEME (segment SAYISI/
    `source_blocks`) miras acik/kapali FARKLILASIYORDU -- K23'un
    yasakladigi TAM OLARAK budur.

    **K23 duzeltmesi -- IKI ayri gecis:**

    1. **Bolumleme gecisi** (asagidaki `for` dongusu): `current`/`nxt`
       `.speaker` alanlari bu gecis BOYUNCA HICBIR ZAMAN mute EDILMEZ --
       her karsilastirma DAIMA ogelerin OCR'dan gelen OZGUN `speaker`
       degerini kullanir. Bir grup kapandiginda (`reason is not None`),
       bu sinirin K19/K21'in kuralina gore "SADECE uzunluk sinirli" olup
       olmadigi (`pure_length`) HESAPLANIR VE `pure_length_boundaries`
       listesine KAYDEDILIR -- ama HENUZ UYGULANMAZ. Bu gecisin urettigi
       `groups` (her `_Item`'in `text`/`bbox`/`source_blocks`/OZGUN
       `speaker`'i) K23'un `apply_inheritance` bayragindan YAPI GEREGI
       ETKILENMEZ -- cunku bayrak bu gecisin ICINDE HIC OKUNMAZ.
    2. **Goruntu gecisi** (`apply_inheritance` `True` ise, dongu SONRASI,
       SOLDAN SAGA TEK ek pas): `pure_length_boundaries[i-1]` isaretli
       VE `groups[i-1].speaker is not None` ise `groups[i]`'nin
       `speaker`'i `groups[i-1].speaker`'a `dataclasses.replace` ile
       GUNCELLENIR. `text`/`bbox`/`source_blocks` HICBIR SEKILDE
       DOKUNULMAZ -- SADECE goruntu (`speaker`) degisir, VE bu degisim
       hicbir GRUPLAMA kararina GERI BESLENMEZ (bolumleme bu ASAMADA
       ZATEN tamamlanmistir). SOLDAN SAGA islendigi icin `groups[i-1]`
       KENDISI de bu AYNI passta miras almis olabilir -- zincirleme
       DOGAL olarak ORTAYA CIKAR (K19'un "kesinlikle ayni konusmacinin
       devami" gerekcesi UZUN/coklu-uzunluk-sinirli monologlarda da
       TUTARLI kalir; bkz. `test_k19_uzunluk_bolunmesinde_kuyruk_
       speaker_miras_alir_ascii` -- ZATEN 2 gruba bolunen bu senaryoda
       zincirleme HENUZ gozlenmiyor, ama YAPI zincirlemeye IZIN VERIR).

    `pure_length` (K19+K21+K24+K28 -- bir sinirin "SADECE uzunluk sinirli"
    olup OLMADIGI): `reason == "length"` (kapanan grup ile `nxt` arasinda
    -- birikmis/birlesik `current` ile HESAPLANIR, K10/K11'in mevcut ANA
    birlestirme SEMANTIGI DEGISMEDI) VE `nxt.speaker is None` (miras
    ALACAK ogenin KENDI etiketi OLMAMALI -- bu HAM/OZGUN deger, HICBIR
    ZAMAN mute EDILMEDIGI icin BURADA GUVENLE OKUNUR) VE (K24, sef_karari
    -tur5.md; K28, sef_karari-tur6.md) `_group_rejection_reason(*_raw_
    query_pair(tail, nxt, blocks), params, ignore_length=True) is None`
    -- burada `tail`, `current`'in BIRLESIK `bbox`'i
    DEGIL, grubun okuma-sirasindaki SON (birlesime en son katilan) HAM
    ogesidir (asagida ayrica TUTULUR, her birlesimde `tail = nxt`
    guncellenir). K24 gerekcesi: birlesik `bbox`, grubun EN ALTA uzanan
    ogesinin `bottom`'unu tasiyabilir (grup ICINDE dikey uzanim
    monotonik OLMAYABILIR); bu durumda birlesik kutuyla yapilan bir
    `gap` HESABI YANLISLIKLA kucuk/negatif cikip GERCEK bir kopusu
    GIZLEYEBILIR -- `tail` KULLANMAK bunu ONLER (bkz. modul docstring
    "## K23/K24", `test_k24_kuyruk_ile_birlesik_bbox_farkli_sonuc_verir`).
    `current.speaker is not None` kontrolu BU GECISTE YOKTUR (tur 4'te
    vardi) -- "gercekten miras alinacak bir sey VAR MI" sorusu artik
    SADECE goruntu gecisinde (`groups[i-1].speaker is not None`)
    sorulur; bu, zincirlemeyi DOGAL olarak MUMKUN kilan degisikliktir VE
    hicbir MEVCUT testle CELISMEZ (K21'in dusuk-seviye 6 testi HALA
    `_group_rejection_reason`'i DOGRUDAN cagirir, bu fonksiyonun ICINE
    HIC GIRMEZ).

    TUR 6 (K28, sef_karari-tur6.md) -- `blocks` PARAMETRESI: K24 `tail`i
    getirmisti, ama `tail`in KENDISI de ADIM 3'ten (`_merge_hyphenated`,
    K5) BIRLESIK gelebilir; AYNI sey ADAY (`nxt`) icin de gecerlidir.
    K28 sorgunun IKI tarafinin da geometrisini OZGUN `TextBlock`
    listesinden okur: `_raw_query_pair(tail, nxt, blocks)` SOL tarafa
    `tail.source_blocks`'un OKUMA SIRASINDA SON, SAG tarafa
    `nxt.source_blocks`'un OKUMA SIRASINDA ILK ozgun blogunun `bbox`'ini
    koyar (tam gerekce, olcumler ve okuma sirasi tanimi o fonksiyonun
    docstring'indedir).

      - `blocks` KEYWORD-ONLY ve VARSAYILANI `()`; varsayilan YALNIZCA
        `items` bosken ya da UZUNLUK-TEK sinir DOGMAYAN DOGRUDAN cagrilar
        icindir. Aksi halde `IndexError` yukselir -- BILINCLIDIR: sessiz
        yanlis yerine GURULTULU hata (patlama GECIKMELIDIR, yalniz
        `reason == "length" and nxt.speaker is None` sinirinda dogar).
      - `_normalize_impl` bu parametreyi `blocks=blocks` ile gecirmek
        ZORUNDADIR (OZGUN liste -- adim 1'de ELENEN bloklar DAHIL,
        indeksler OZGUN indekslerdir).
      - KAPSAM (K24'ten devralinir): ham ikame YALNIZCA miras-uygunluk
        sorgusu icindir. ANA birlestirme karari (asagidaki bolumleme
        dongusunun `_group_rejection_reason(current, nxt, params)`
        cagrisi) K10/K11 uyarinca `current`'in BIRLESIK `bbox`'ini
        KULLANMAYA DEVAM EDER; K23'un iki-gecis yapisi DEGISMEZ.
      - Bolumleme dongusunun ICINDE hicbir `replace(...)` YAZILMAZ --
        ikame TAMAMEN `_raw_query_pair`'in icindedir.

    K30 (sef_karari-tur6.md, TUR 6) -- K2 x K19/K21 ETKILESIMI, KOSULLU:
    ADIM 1'de dusen bir blok, ADIM 5'te geride GERCEK bir GEOMETRIK
    BOSLUK birakir -- modul docstring'inin K2 bolumundeki "o blok hic var
    olmamis gibi calisir" ifadesi METIN/HYPHEN icin dogrudur, GEOMETRI
    icin DEGIL. Bu ARTIK bosluk `max_vertical_gap_ratio * min(h)` esigini
    ASARSA sinir artik yalniz-uzunluk siniri DEGILDIR ve K21 uyarinca
    miras UYGULANMAZ; ASMAZSA miras KORUNUR. IKISI DE K2 sirasinin
    BILINCLI sonucudur -- sonuc ARTIK BOSLUGUN BUYUKLUGUNE baglidir (sef
    olctu: 22px > 14.4 esik -> miras kesilir; 4px < 14.4 -> miras
    korunur). Iki yol da birer testle sabitlenmistir:
    `test_k30_artik_bosluk_esigi_asmazsa_miras_korunur` ve
    `test_k30_artik_bosluk_esigi_asarsa_miras_yok`.

    K31 (sef_karari-tur6.md, TUR 6) -- BITISIK IKI REPLIK, IKI ALT DURUM:
    K15 uyarinca geometrik olarak bitisik iki replik, IKINCI BLOGUN
    KONUSMACISI BIRINCIYLE AYNI ya da `None` ISE tek segmentte birlesir
    (iki FARKLI TANINAN ad BIRLESMEZ -- sef dogruladi: `['Ada: merhaba',
    'Bora: nasilsin']` -> IKI ayri segment); ikinci blogun ETIKET
    TASIMASI utterance siniri SAYILMAZ (K15'in BILINCLI siniri).

      (a) Ikinci etiket K9'a gore TANINIYORSA ve ad AYNIYSA etiket
          METINDEN DUSER, segment TEK `speaker` tasir:
          `['Ada: merhaba', 'Ada: nasilsin']` -> `'merhaba nasilsin'`,
          `speaker='Ada'` (bkz. `test_k31a_ikinci_etiket_taniniyorsa_
          duser_tek_segment_kalir`).
      (b) Ikinci etiket K9'un AD SUZGECINDEN gecemiyorsa (rakam iceren
          ad, K32'deki NFD adlar) o blok `speaker=None` KALIR, K15'in
          `X/None` satiriyla bloklar YINE birlesir, ETIKET METNIN ICINDE
          KALIR ve segment ILK konusmaciya atfedilir:
          `['Ada: merhaba', 'Ada2: nasilsin']` -> `'merhaba Ada2:
          nasilsin'`, `speaker='Ada'` (bkz. `test_k31b_taninmayan_ikinci_
          etiket_metinde_kalir`).

    (b) urun etkisi olarak (a)'dan KOTUDUR; IKISI DE BILINCLI SINIRDIR --
    sef tur 6'da davranisi DEGISTIRMIYOR."""
    if not items:
        return []
    groups: list[_Item] = []
    pure_length_boundaries: list[bool] = []
    current = items[0]
    tail = items[0]
    for nxt in items[1:]:
        reason = _group_rejection_reason(current, nxt, params)
        if reason is None:
            merged_text = current.text + " " + nxt.text
            merged_bbox = _union_rect(current.bbox, nxt.bbox)
            merged_blocks = tuple(sorted((*current.source_blocks, *nxt.source_blocks)))
            current = _Item(text=merged_text, bbox=merged_bbox, speaker=current.speaker, source_blocks=merged_blocks)
            tail = nxt  # K24: grubun YENI kuyrugu -- birlesime en son katilan HAM oge
        else:
            groups.append(current)
            pure_length_boundaries.append(
                reason == "length"
                and nxt.speaker is None
                # K28 (TUR 6): sorgunun IKI tarafi da OZGUN bloklardan --
                # ikame `_raw_query_pair`'in ICINDEDIR, bu dongude DEGIL
                # (bolumleme gecisi hicbir `replace(...)` yazmaz).
                and _group_rejection_reason(
                    *_raw_query_pair(tail, nxt, blocks), params, ignore_length=True
                )
                is None
            )
            current = nxt
            tail = nxt
    groups.append(current)

    if apply_inheritance:
        # K19/K21/K23: goruntu gecisi -- bolumleme (yukarida) TAMAMEN
        # bitmistir, bu pas SADECE `speaker` alanini gunceller ve
        # hicbir gruplama kararina GERI BESLENMEZ.
        for i, pure_length in enumerate(pure_length_boundaries, start=1):
            if pure_length and groups[i - 1].speaker is not None:
                groups[i] = replace(groups[i], speaker=groups[i - 1].speaker)

    return groups
