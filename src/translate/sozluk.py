"""Suflor -- terim sozlugu (`GlossaryStore`) ve kaynaga gomme (`terimleri_gom`), T-011 (tur 2).

Katman 0 on-islemcisi. Tasarim 4.1 "sozluk motora zorunlu kisit olarak
enjekte edilir" der; yerel NMT motoru (T-007) kisit ALAMAZ ve
`TranslationRequest.glossary_hits`i okumaz (dondurulmus). Olculen tek
calisan yol (olgular G1/G4: 21/21 korundu, Ingilizce'ye kayma 0/21): terimi
KAYNAK metinde hedef bicimiyle degistirmek ve aralik disindaki her karakteri
(KR ekler `을/를/가/는`, JP parcaciklar `を/が/は`) DOKUNMADAN birakmak; motor
gomulu terimi aynen tasir ve kalan eki dogru cekimler (`방앗간을` ->
`Değirmen을` -> "Değirmen'den gecin").

Zincir (pipeline kurar, bu modul cevirmez):
    hits = store.lookup_segments(segments)          # segment_index dolu
    gomulu = terimleri_gom(segments, hits)          # saf, kopya dondurur
    provider.translate(TranslationRequest(segments=gomulu, ...))
`lookup(text, placeholders)` tek metin uzerinde calisir ve `segment_index`i
dolduramaz (sozlesme); `lookup_segments` iliskilendirmeyi yapar.
GOMULU SEGMENT TEKRAR SOZLUKTEN GECIRILMEZ (Tester-B O-B3): sema `hedef ⊇
kaynak` girdisini (`mill -> Değirmen mill`) reddetmez, ikinci geciste terim
buyur (idempotens YOK). Pipeline/TM ham metni saklar, gomuluyu degil.

Bu docstring, gorev paketindeki (T-011 packet.md surum 3) K1-K7
degismezlerinin bu modulde nasil uygulandigini belgeler. Her kararin
yaninda onu olcen test adi vardir (`tests/unit/translate/test_sozluk.py`)
ya da `[ÖLÇÜLMÜYOR]` damgasi. Tester `known_gaps`i OKUMAZ; garanti alani
burasidir.

YAZARLIK KURALI (K4, Y3 + Y-B1 -- gercek motorla IKI YONLU olculdu): sozluge
OZEL ADLAR (karakter, yer) ve motorun YANLIS ya da TUTARSIZ cevirdigi
bilesikler girer (`水車小屋`/`방앗간` -> "su arabasi"/"cukur" yerine
`Değirmen`; `マルクス` -> "Marks/Markos" yerine `Marcus`). UNVAN VE CINS
ISIMLER TEHLIKELIDIR: bileşik icinde dogru ceviriyi bozarlar (`마을 장로가
마르쿠스를 불렀습니다.` ham "Koy ihtiyari Marcus'u cagirdi" -> `장로->İhtiyar`
gomulu "İhtiyar kasabasi Marcus'a seslendi"; `The village elder came.` ->
"İhtiyar koyu geldi"), ama unvan+ad segmentinde unvan sozlukte YOKSA cikti
Ingilizce'ye kayabilir ("Elder Marcus"). Bu bir GRI BOLGEDIR: kod karar
veremez; yazar `not` alanina niyeti yazar, terimi eklemeden once ham ceviriyi
gorur; hedef tarafi duzeltme (ceviri sonrasi "Elder" -> "İhtiyar") ayri gorev
adayidir. Ceviri KALITESI bu modulde `[ÖLÇÜLMÜYOR]` (altin set yok; gomulu
terimin korunumu `real_check.py` #1/#2/#5 ile, unvan gri bolgesi #4 ile
gercek motorla olculur).

## K1 -- esleme: en uzun once, ortusmesiz, sinir kurali HER BETIKTE AYNI (v3)

`lookup(text, placeholders=())`:
  1. `text` ve `placeholders` NFC'lenir (K6). Bos sozluk/metin -> `[]`.
  2. TEK GECIS: sozlugun butun terimleri tek bir ileri-bakisli TRIE
     deseninde (`re.IGNORECASE`, ORIJINAL/NFC metin uzerinde; metin
     kucultulmez -- casefold `İ`/`ﬁ`yi genisletip indeksi kaydirir, KRT O2)
     taranir; her konumda o konumdan baslayan EN UZUN terim bulunur (eslesen
     dilim kanonik anahtarla terime baglanir), ayni konumda baslayan daha kisa
     terimler yukleme zamaninda hesaplanan onek tablosundan eklenir. Aday
     kumesi TAMDIR (her `(konum, terim)` cifti); maliyet terim sayisindan
     bagimsiz (K5). Trie dugum anahtari IGNORECASE denklik sinifinin KANONIK
     anahtaridir (`_trie_anahtari` = `_anahtar`; `ß/ẞ`, `ᾈ/ᾀ`, `ΐ/ΐ`, `ﬅ/ﬆ`
     tek dal), regex literali dalin ilk gorulen uyesi -- `{Maßen, Maẞer, Maße}`
     sozlugunde harfiyen gecen `Maẞer` HER JSON sirasinda bulunur (Tester-A
     O-A1; `test_k1_trie_anahtari_*`; tum Unicode olcumu `evidence/`).
  3. Adaylar `(uzunluk azalan, start artan, sozluk sirasi)` ile islenir:
     kabul edilmis ya da korunan (K3) bir aralikla ortusen aday ATLANIR
     (konum bitmap'i, K5). Aday ancak iki ucunda da SINIR varsa kabul edilir;
     sinir ya GERCEK sinirdir ya da ZINCIR kuraliyla komsu adaydan gelir
     (asagida). Esit uzunlukta ortusen iki aday: kucuk `start` kazanir (JSON
     sirasi sonucu degistirmez; `test_k1_esit_uzunlukta_*`).
  4. Donus `start` ARTAN sirali `list[TermHit]`; `source_term` METINDEKI
     DILIM (buyuk/kucuk harf metinden, `MARCUS` -> `"MARCUS"`; K2 tam
     esitlik denetimi bunu ister), `target_term` sozlugun ilk harfi
     buyutulmus hedefi (K4), `segment_index=None`, `note` = JSON `not`.
     Indeksler KODPOINT indeksidir (Python `str`), NFC metne gore.

GERCEK SINIR (terimin betigine bakilmaz; kelime siniri meta-karakteri
KULLANILMAZ -- CJK'da Latin terim + parcacik `Marcusが` hic eslesmezdi):
  - metin ucu · bosluk (`str.isspace`, ideografik bosluk dahil) ·
    Unicode noktalama (kategori `P*`: `.,!?、。「」()[]{}“”'-_…・` ...);
  - JP parcacik `をがはにのでともへや` (iki tarafta: `村は`, `が村に`);
  - BETIK GECISI (▲ v3): terimin uc karakteri ile komsusu FARKLI betik
    sinifindaysa sinirdir. Siniflar: Han (kanji/hanja, `々〆〇`, radikaller,
    uyumluluk ideograflari, uzanti bloklari) · Hiragana (birlestirici ses
    isaretleri dahil) · Katakana (`ー`, fonetik uzanti, yarim genislik dahil)
    · Hangul (heceler + Jamo + uyumluluk/yarim genislik Jamo) · DIGER (Latin,
    rakam, oteki harfler, semboller TEK sinif; kodpoint araliklari
    `_BETIK_ARALIKLARI`). `長老マルクス` -> `マルクス` eslesir (Han|Katakana,
    unvan sozlukte yokken de); `マルクス様`/`マルクスさん`/`マルクスたち`
    (Katakana|Han, Katakana|Hiragana); `長老Marcus`, `Marcus様`, `마르쿠스Marcus`
    (kimlik cipasi GEREKMEZ). Sinif ici komsu sinir DEGIL: `マルクスタウン`,
    `アイラー`, `村人`/`剣士`/`中村`, `검사`/`방앗간집`, `Marcus2`/`Marcuss`/
    `windmills`. Sagdaki komsu birlestirici isaretse (`M*`) sinir DEGIL
    (terimin son karakterine aittir). Sembol (`S*`) DIGER sinifindadir:
    `マルクス♪` betik gecisiyle sinir, `Marcus♪`/`Marcus$` degil (asimetri
    belgeli; `test_k1_betik_gecisi_sembol_*`). PAKET ILE OLCUM CELISKISI:
    paket `マルクス山`i saygi listesinin negatif kontrolu olarak "eslesmez"
    yazar; Katakana|Han bu kurala gore sinirdir (`マルクス様` ile ayni cift)
    ve `Marcus山` ("Marcus Dagi": ad + kanji siniflandirici, `ゴブリン王`
    sinifi) istenen davranistir -- kural izlendi, ornek pinlendi
    (`test_k1_betik_gecisi_マルクス山_*`). Betik kestirimleri: Kana Ek/Kucuk
    Kana Ek bloklari (astral) DIGER sayilir `[ÖLÇÜLMÜYOR]`.
  - JP SAYGI/KOPULA EKI (▲ v3, Y-B2; yalniz SAGDA, en uzun once, ekten sonra
    da GERCEK sinir, zincir en fazla iki ek -- KR ek kuraliyla AYNI
    mekanizma): `さん 様 殿 君 ちゃん 達 たち って だ から まで より か よ ね`.
    Katakana/Han terim icin hiragana ekleri betik gecisi zaten kapsar; liste
    AYNI betikli ciftlerde yuk tasir: `長老様`/`長老達が` (Han+Han),
    `ひかりさん`/`ひかりだから` (Hiragana+Hiragana). Negatif: `長老山`,
    `長老様子`, `ひかりこ`, `ひかりさんご`, `ひかりかわ` eslesmez (`ひかりやま`
    eslesir: `や` parcaciktir); `ひかりだからね`
    (uc ek) eslesmez (belgeli sinir). `test_k1_her_jp_saygi_eki_*`,
    `test_k1_jp_saygi_*`.
  - KR EK (yalniz SAG tarafta, en uzun once, EKTEN SONRA DA GERCEK sinir,
    zincir en fazla IKI ek): `을 를 이 가 은 는 에 에서 으로 로 와 과 도 의 만 께서
    부터 까지` (G6) **+ ▲ v3** `에게 한테 께 님 씨 야 아 랑 이랑 들 처럼 보다 마다
    밖에 조차 라고 라면 입니다 이다` (Y-B2). `방앗간을 지나` evet, `방앗간도둑`
    hayir (`도`+`둑`); `장로님이`, `마르쿠스들이다` (`들`+`이다` = iki ek) evet;
    `마르쿠스아침`/`방앗간들판`/`마르쿠스씨앗` hayir (tek heceli ek kelime basi
    da olabilir, ekten sonra sinir yok). PAKET ILE OLCUM CELISKISI: paket
    `마르쿠스들이다`yi "3 ek" sayar; `이다` listede tek ektir, zincir 2 ->
    eslesir (pinlendi). BILINEN SINIR: uc ek (`마르쿠스님에게는` = `님`+`에게`+
    `는`, `들에게는`) eslesmez -- paket K1 "zincir <= 2" degismedi; derinlik 3
    sef karari (`test_k1_kr_ek_zinciri_uc_ek_*`).
  - korunan araligin (yer tutucu, K3) ucu: `%sMarcus` + `("%s",)` -> hit;
    bildirilmemisken `s`|`M` ayni sinif, hit yok.
  Sinir OLMAYANLAR: ayni betik sinifindan harf/rakam/kana/kanji/hece komsusu;
  KR ek SOLDA (onceki kelimenin ekidir: `의장로` eslesmez); bicim
  karakterleri (`Cf`: ZWSP, SHY) `[ÖLÇÜLMÜYOR]`; ekten sonraki komsu aday
  (`마르쿠스가아일라를` bosluksuz) `[ÖLÇÜLMÜYOR]`.
  Bilinen sinir (belgelenir, duzeltilemez): `검은 옷` (siyah giysi) = `검` +
  GERCEK ek `은` -> kural GECER; tek heceli/tek kodpointlik kaynak terim bu
  yuzden semada reddedilir, `kisa_terim_izni: true` ile acik opt-in (K6;
  `real_check` #7c yalniz raporlar).

ZINCIR KURALI (▲ v3; Tester-A O-A3 + Tester-B O-B5): sozlukteki baska bir
terimin bitisik olmasi TEK BASINA sinir degildir. Bitisik adaylar bir ZINCIR
olusturur; zincir ancak IKI DIS UCU da gercek sinirsa butunuyle eslesir, aksi
halde hicbir uyesi eslesmez. Reddedilen bir aday hicbir komsuya sinir
veremez. `windmills` = `wind`+`mill`+`s` -> 0 hit (tur 1: `Rüzgarmills`,
gercek motorda degirmen kayboldu); `millstones` -> 0; `windmill` -> 2 (yazar
ikisini de istedi); `長老マルクスアイラ` -> 3; `マルクスアイラ` -> 2 (Katakana|
Katakana ic ucu zincirden gelir). Uygulama: aday islenirken sol ve sag
zincirleri ES ZAMANLI, adim adim, yigin tabanli (ozyineleme YOK) DFS ile
aranir (`_ZincirDfs`); bir yon olu cikar cikmaz arama durur; olu konumlar
kalici hafizaya alinir (doluluk yalniz artar, oluluk kararlidir); bulunan
zincirin tum uyeleri birlikte kabul edilir. Zincir icinde de en uzun aday
oncelikli (`oldmillhouse` -> `old`+`millhouse`). Korunan aralikla ortusen
aday zincire giremez; korunan araligin ucu gercek sinirdir. Kabul edilmis
komsunun ucu da sinirdir (zincirin sonradan gorulen parcasi). Maliyet
amortize dogrusal: her aday kenari en fazla bir kez olu isaretlenir ya da
kabul edilir; canli yon olu yonun adim sayisiyla sinirlanir. 8000 uyeli
zincir (gecerli/olu) < 60 ms (`test_k5_sure_8000_uyeli_zincir_*`,
`test_k1_zincir_*`).

## K2 -- gomme: aralik disi karakter dokunulmaz; gecersiz hit -> `ContractViolation`

`terimleri_gom(segments, hits) -> tuple[Segment, ...]`: her hit
`segment_index`ine gore gruplanir; grup `start` AZALAN sirayla uygulanir
(indeksler kaymasin -- hedef uzunlugu kaynaktan farkli, `test_k2_iki_hit_
basta_ve_sonda_*` start-artan uygulamayi ayirt eder). Cikti `Segment`
`dataclasses.replace(seg, text=..., placeholders=...)`: `bbox/speaker/
source_blocks` AYNEN. ▲ v3: hit'i olan segmentte `text` VE `placeholders`
BIRLIKTE NFC'lenir (Tester-A O-A4 + Tester-B O-B2: metin NFC, yer tutucu NFD
kalinca T-007 K5 sayimi yer tutucuyu goremiyor ve kopya ekliyordu) -- "aralik
disi dokunulmaz" KODPOINT-DUZEYI NFC DISINDA gecerlidir; yer tutucu
tuple'inin uzunlugu/sirasi/bos ogeleri korunur, her yer tutucu ciktida
`text`in alt dizesi kalir. Hit'i olmayan segment ve `hits` bos -> AYNI nesne
(`is`), normalize edilmez. Girdi degistirilmez.
Denetim (hepsi `ContractViolation`, sessiz kayma/yutma yok): oge `Segment`
degil · `text` `str` degil · ▲ `placeholders` duz `str` / dizi degil / `str`
olmayan oge (Tester-B O-B4: `TypeError` `TranslatorError` degildir, tasarim
5.6 `except TranslatorError` yakalayamaz; `lookup_segments` de ayni) · oge
`TermHit` degil · `segment_index` `None`/`bool`/`int` degil/aralik disi (K7)
· `start`/`end` `int` degil · `0 <= start < end <= len(metin)` degil
(`start == end` dahil) · `metin[start:end] != source_term` (TAM esitlik; iki
taraf da NFC) · iki hit ortusur (`a.end > b.start`; bitisik `==` serbest) ·
hit segmentin `placeholders`indan biriyle ortusur (K3) · `target_term` bos/
`str` degil. Hata mesajlari yalniz sayi ve tip adi tasir; kaynak metin, terim
ve dilim ASLA (PROTOKOL 7; `test_k2_hata_mesajlari_metin_tasimaz[*]`).
Olcu: `test_k2_*`, `test_k7_*`.

## K3 -- terim yer tutucu ile cakismaz (KRT Y2)

`placeholders` icindeki her dizenin metindeki TUM gecisleri (tam alt dize,
buyuk/kucuk duyarli, ortusmesiz tarama) korunan araliktir; onlarla (kismen
de olsa) ortusen aday eslesmez ve zincire giremez: `{PLAYER}は村にいます` +
`("{PLAYER}",)` -> hit yok; `placeholders=()` iken `{`/`}` `P*` sinirdir ve
`PLAYER` eslesir (pozitif kontrol). `{0}マルクス` -> `マルクス` eslesir, `{0}`
dokunulmaz. `terimleri_gom` `segment.placeholders`i AYNI kurala gore
denetler: ortusen hit -> `ContractViolation` (dusurme degil). Bos dize yok
sayilir. Dogrudan `lookup(text, placeholders)` cagrisinda duz `str` ya da
`str` olmayan oge -> `TypeError` (programci hatasi); `Segment`ten gelen ayni
bicim hatasi `ContractViolation` (K2). Yer tutucu bilgisi YALNIZ cagirandan
gelir (T-007 K3 ile ayni ilke): bildirilmemis `{PLAYER}` metindir.
Olcu: `test_k3_*`, `test_k1_yer_tutucu_ucu_sinirdir`, `test_k1_zincir_yer_
tutucu_*`; `real_check` #3a-c.

## K4 -- hedef her zaman ilk harfi BUYUK gomulur; kimlik girdisi = SINIR CIPASI

JP kaynakta kucuk harfli cins isim (`değirmen`) motorda KAYBOLUYOR (G7);
buyuk harf 21/21 korundu. `ilk_harfi_buyut`: ilk kodpoint `upper()`, Turkce
`i` -> `İ` (hedef dili Turkce; `ihtiyar` -> `İhtiyar`, `ışık` -> `Işık`);
gerisi aynen, zaten buyukse aynen, harf degilse aynen. Iki yerde: yukleme
(`SozlukTerimi.hedef` ve `TermHit.target_term` buyuk) VE `terimleri_gom`
(elle kurulan hit de buyuk gomulur). Motorun ozel-ad kesme isareti
(`Değirmen'de`) kozmetik, `[ÖLÇÜLMÜYOR]`. `ozel_ad` bayragi YOK; serbest `not`
alani `TermHit.note`ya gider. Sinir `[ÖLÇÜLMÜYOR]`: kucuk `i` ile baslamasi
gereken hedef (marka adi gibi) da `İ` ile buyutulur -- paket her hedefi
buyutmeyi zorunlu kilar (G7); `upper()` genislemesi (`ß` -> `SS`, `ﬁ` ->
`FI`) belgeli.
▲ KIMLIK GIRDISI (`Marcus -> Marcus`) gecerlidir: hit uretir, `terimleri_gom`
ciktisi metin-esittir. Islevi SINIR CIPASIdir: adin Latin yazimini sozluge
kaydeder (`MARCUS`/`marcus` da tek bicime iner) ve tur 1'de betik gecisi
kurali yokken `長老Marcus` gibi bitisik dizilimlerde komsuya sinir veriyordu;
v3'te betik gecisi bunu cipa olmadan da saglar. Cagiran "gomulen terim"
sayacini `source_term != target_term` ile suzer (demo duzeltildi).
Olcu: `test_k4_*`.

## K5 -- saf, deterministik, hizli

`lookup`, `lookup_segments`, `terimleri_gom`, `ilk_harfi_buyut` I/O yapmaz,
import etmez, modul duzeyinde degisken durum yok (yalniz `Final` sabitler);
dosya YALNIZ `GlossaryStore.__init__`te okunur (yeniden yukleme yok: yeni
profil = yeni `GlossaryStore`; dosya sonradan silinse lookup calisir).
Ayni girdi -> esit cikti (yeni liste). Butce: 1000 segment x 50 terim,
`lookup_segments` + `terimleri_gom` medyan < 50 ms; terim sayisindan
bagimsiz (11 / 50 / 500 terim ayni). ▲ v3: segment basina maliyet hit
sayisinda amortize DOGRUSAL (Tester-A D-A1: tur 1 kabul listesini dogrusal
tariyordu, 8000 hit 472 ms): ortusme denetimi konum BITMAP'i (`bytearray`,
`find`), zincir aramasi olu-konum hafizasi; 8000 hit'lik tek segment < 60 ms
(`test_k5_sure_8000_*`). ▲ Sozluk yuklemesi terim uzunluguna bagli
ozyineleme yapmaz: kaynak <= 100 kodpoint semada zorunlu (K6; trie govdesi
en fazla 101 derinlik). Kapsam izleyicisi (C tracer) aktifken Python
satirlari ~4x yavaslar; sure testleri o kosumda butceyi 4x alir, gercek
butce izleyicisiz kosumda ve `real_check` #8'de olculur. Hicbir kanala
(stdout/stderr/logging/warnings) metin yazilmaz; `repr` terim basmaz
(yalniz sayi + dosya adi). Olcu: `test_k5_*`; `real_check` #8.

## K6 -- yukleme, sema ve hata

`GlossaryStore(json_path)`: `Path` ya da `str` (baskasi `TypeError`); dosya
BAYT ile okunur ve `json.loads(bayt)` ile cozulur (UTF-8 BOM cozulur, KRT
D4; ASCII-disi yol calisir). Dosya yoksa `FileNotFoundError` SARILMAZ
(model dosyasi degil, `ModelMissingError` yanlis sinif olurdu); diger
`OSError`ler de aynen gecer. Bozuk JSON -> `ValueError` (dosya adi mesajda).
Sema `{"terimler": [{"kaynak": str, "hedef": str, "not": str|null?,
"kisa_terim_izni": bool?}]}`; ust duzeyde ek anahtar (profil meta verisi)
SERBEST, kayit duzeyinde bilinmeyen anahtar RED (`ozel_ad` v1 bayragi ve
yazim hatalari sessizce yutulmaz). `kaynak`/`hedef` NFC'lenir. Red
(`ValueError`, mesajda terim ya da alan adi; ILK hatali kayit bildirilir):
  - `kaynak`/`hedef` eksik, `str` degil, bos/yalniz bosluk, bas/son bosluklu;
  - `kaynak` NFC sonrasi TEK KODPOINT (tek hangul hecesi, tek kanji, tek
    kana, tek Latin harf -- sinir kurali ayristiramaz, `검은`) ve
    `kisa_terim_izni` `true` degil;
  - ▲ `kaynak` 100 kodpointten UZUN (Tester-A O-A2: tur 1'de >= 996 kodpoint
    `RecursionError`; 100 kabul, 101 red, 2000 `ValueError`);
  - ▲ `kaynak`ta cumle sonu isareti `.!?。！？` -- herhangi bir yerde
    (Tester-B O-B1: `マルクス。 -> Marcus` gomme cumle sinirini yuttu, gercek
    motorda ikinci cumle kayboldu; OCR'dan kopyalanan terime nokta yapismasi
    kolay; `Mr. Marcus` da red);
  - tekrar eden `kaynak` (esleme semantigiyle: `Marcus`/`MARCUS`,
    `istanbul`/`İstanbul`, NFC/NFD ayni terim; D-A2: casefold `ß`->`ss`
    tekrar reddi eslemeden genis -- `straße`/`strasse` ikisi birden
    eklenemez `[ÖLÇÜLMÜYOR]` urun dillerinde);
  - `hedef`te cumle sonu isareti `.!?。！？` (T-007 K3 kumesi; `St. Marcus`
    cumleyi boler, motor uydurur -- KRT O5), `{`/`}` (yer tutucu bicimi) ya
    da ▲ KONTROL KARAKTERI (kategori `Cc`: `\\n \\t \\r`, NUL, DEL, NEL --
    Tester-A D-A4: `\\n` T-007 satir bolmesine gider); `%s`/`[Mill]` gibi
    yer tutucu BENZERI hedefler serbesttir (cagiran `placeholders` ile
    bildirir) `[ÖLÇÜLMÜYOR]`;
  - `not` `str`/`null` degil; `kisa_terim_izni` `bool` degil (`1` de red).
`terimler` ozelligi uzunluk-azalan sirali `tuple[SozlukTerimi, ...]`
(`hedef` buyutulmus, `kaynak` NFC), `len(store)` terim sayisi, `yol`.
Olcu: `test_k6_*` (her red sinifi ayri kimlikle; alti terminator kaynak ve
hedef icin ayri; alti kontrol karakteri ayri).

## K7 -- `segment_index` denetimi

`terimleri_gom`a gelen hit'in `segment_index`i `None`, `bool`, `int` degil
ya da `[0, len(segments))` disi -> `ContractViolation`; bir hit gecersizse
cagri BUTUNUYLE duser, kismi cikti yok. Olcu: `test_k7_*`.

Loglama (PROTOKOL 7): bu modulde stdout/stderr/logging/warnings YOK.
Thread-safe: `GlossaryStore` yuklemeden sonra degismezdir, paylasilabilir;
arama durumu (`_SinirBaglami`) cagri yerelidir.
"""
from __future__ import annotations

import bisect
import dataclasses
import json
import re
import unicodedata
from collections.abc import Sequence
from pathlib import Path
from typing import Final, TypeAlias

from src.contracts.errors import ContractViolation
from src.contracts.models import Segment, TermHit

__all__ = ["GlossaryStore", "SozlukTerimi", "terimleri_gom", "ilk_harfi_buyut"]


_NFC: Final = "NFC"
_JP_PARCACIKLAR: Final = frozenset("をがはにのでともへや")
"""K1 (G6): JP parcaciklar -- terimin iki yaninda da sinir."""
_KR_EKLER_G6: Final[tuple[str, ...]] = (
    "을", "를", "이", "가", "은", "는", "에", "에서", "으로", "로", "와", "과", "도", "의", "만", "께서", "부터", "까지",
)
"""K1 (G6): KR ekler, tur 1 listesi."""
_KR_EKLER_V3: Final[tuple[str, ...]] = (
    "에게", "한테", "께", "님", "씨", "야", "아", "랑", "이랑", "들", "처럼", "보다", "마다", "밖에", "조차", "라고", "라면", "입니다", "이다",
)
"""K1 v3 (Y-B2): KR ek listesine eklenen yonelme/saygi/cogul/kopula ekleri."""
_JP_SAYGI_EKLERI: Final[tuple[str, ...]] = (
    "さん", "様", "殿", "君", "ちゃん", "達", "たち", "って", "だ", "から", "まで", "より", "か", "よ", "ね",
)
"""K1 v3 (Y-B2): JP saygi/kopula ekleri -- yalniz sagda, KR ekleriyle ayni mekanizma."""
_EKLER: Final[tuple[str, ...]] = tuple(sorted({*_KR_EKLER_G6, *_KR_EKLER_V3, *_JP_SAYGI_EKLERI}, key=lambda e: (-len(e), e)))
"""K1: sag ekler (KR + JP), en uzun once; ekten sonra da gercek sinir gerekir."""
_EK_ILK_KARAKTER: Final[dict[str, tuple[str, ...]]] = {
    ch: tuple(e for e in _EKLER if e[0] == ch) for ch in {e[0] for e in _EKLER}
}
"""K1/K5: ilk karaktere gore ek alt listesi (sicak yolda 52 `startswith` yerine O(1) secim); yuklemeden sonra degismez."""
_EK_ZINCIRI: Final = 2
"""K1: art arda en fazla bu kadar ek (`에서는`, `님이`, `들이다`, `さんたち`)."""
_CUMLE_SONU: Final = ".!?。！？"
"""K6: kaynak ve hedefte yasak -- T-007 K3'un evrensel cumle sonu kumesiyle AYNI (bolmeyi tetikler)."""
_YER_TUTUCU_AYRACLARI: Final = "{}"
"""K6: hedefte yasak -- yer tutucu bicimi (T-007 K5 onarimiyla cakisir)."""
_KAYNAK_AZAMI: Final = 100
"""K6 v3: kaynak terim en fazla bu kadar kodpoint (trie govdesi derinligi sinirli kalir, RecursionError yok)."""
_ANAHTAR_TERIMLER: Final = "terimler"
_ANAHTAR_KAYNAK: Final = "kaynak"
_ANAHTAR_HEDEF: Final = "hedef"
_ANAHTAR_NOT: Final = "not"
_ANAHTAR_IZIN: Final = "kisa_terim_izni"
_KAYIT_ANAHTARLARI: Final = frozenset({_ANAHTAR_KAYNAK, _ANAHTAR_HEDEF, _ANAHTAR_NOT, _ANAHTAR_IZIN})

_BETIK_DIGER: Final = 0
_BETIK_HAN: Final = 1
_BETIK_HIRAGANA: Final = 2
_BETIK_KATAKANA: Final = 3
_BETIK_HANGUL: Final = 4
_BETIK_ARALIKLARI: Final[tuple[tuple[int, int, int], ...]] = (
    (0x1100, 0x11FF, _BETIK_HANGUL),  # Hangul Jamo
    (0x2E80, 0x2FDF, _BETIK_HAN),  # CJK radikal ek + Kangxi radikalleri
    (0x3005, 0x3007, _BETIK_HAN),  # 々 〆 〇
    (0x3041, 0x309F, _BETIK_HIRAGANA),  # Hiragana (birlestirici/ayrik ses isaretleri, tekrar isaretleri dahil)
    (0x30A0, 0x30FF, _BETIK_KATAKANA),  # Katakana (ー dahil; ・ noktalama olarak once yakalanir)
    (0x3130, 0x318F, _BETIK_HANGUL),  # Hangul uyumluluk Jamo
    (0x31F0, 0x31FF, _BETIK_KATAKANA),  # Katakana fonetik uzanti
    (0x3400, 0x4DBF, _BETIK_HAN),  # CJK uzanti A
    (0x4E00, 0x9FFF, _BETIK_HAN),  # CJK birlesik ideograflar
    (0xA960, 0xA97F, _BETIK_HANGUL),  # Hangul Jamo uzanti A
    (0xAC00, 0xD7FF, _BETIK_HANGUL),  # Hangul heceleri + Jamo uzanti B
    (0xF900, 0xFAFF, _BETIK_HAN),  # CJK uyumluluk ideograflari
    (0xFF66, 0xFF9F, _BETIK_KATAKANA),  # yarim genislik Katakana
    (0xFFA0, 0xFFDC, _BETIK_HANGUL),  # yarim genislik Hangul
    (0x20000, 0x323AF, _BETIK_HAN),  # CJK uzanti B..H + uyumluluk ek
)
"""K1 v3: betik siniflari (kodpoint araliklari, artan; `_betik`). Kapsam disi her sey DIGER."""
_BETIK_BASLARI: Final[tuple[int, ...]] = tuple(a for a, _, _ in _BETIK_ARALIKLARI)


@dataclasses.dataclass(frozen=True)
class SozlukTerimi:
    """Yuklenmis bir sozluk kaydi: `kaynak` NFC, `hedef` NFC + ilk harfi buyuk (K4)."""

    kaynak: str
    hedef: str
    note: str | None = None
    """JSON `not` alani -- `TermHit.note`ya gider (cevirmene serbest talimat)."""
    kisa_terim_izni: bool = False
    """K6: tek kodpointlik kaynak icin acik opt-in."""


# ---------------------------------------------------------------------------
# yardimcilar: buyutme / NFC / betik / sinir karakteri / yer tutucu
# ---------------------------------------------------------------------------


def ilk_harfi_buyut(metin: str) -> str:
    """K4: ilk kodpoint buyuk (Turkce `i` -> `İ`), gerisi aynen; bos/harf-disi aynen."""
    if not metin:
        return metin
    ilk = metin[0]
    if ilk == "i":
        return "İ" + metin[1:]
    return ilk.upper() + metin[1:]


def _nfc(metin: str) -> str:
    return unicodedata.normalize(_NFC, metin)


def _betik(ch: str) -> int:
    """K1 v3: karakterin betik sinifi (Han / Hiragana / Katakana / Hangul / DIGER), aralik tablosuyla."""
    o = ord(ch)
    if o < 0x1100:
        return _BETIK_DIGER
    i = bisect.bisect_right(_BETIK_BASLARI, o) - 1
    _, hi, sinif = _BETIK_ARALIKLARI[i]
    return sinif if o <= hi else _BETIK_DIGER


def _sinir_karakteri(ch: str) -> bool:
    """K1: bosluk, Unicode noktalama (`P*`) ya da JP parcacik -- iki tarafta da gercek sinir."""
    return ch.isspace() or unicodedata.category(ch).startswith("P") or ch in _JP_PARCACIKLAR


def _korunan_araliklar(metin: str, yer_tutucular: Sequence[str]) -> list[tuple[int, int]]:
    """K3: her (bos olmayan) yer tutucunun metindeki TUM gecisleri (tam alt dize, ortusmesiz tarama)."""
    sonuc: list[tuple[int, int]] = []
    for yt in yer_tutucular:
        if not yt:
            continue
        i = metin.find(yt)
        while i != -1:
            sonuc.append((i, i + len(yt)))
            i = metin.find(yt, i + len(yt))
    return sonuc


def _yer_tutuculari_dogrula(yer_tutucular: object) -> tuple[str, ...]:
    """K3: `str` dizisi (duz `str` DEGIL); her oge NFC; uzunluk ve sira korunur (bos oge kalir)."""
    if isinstance(yer_tutucular, (str, bytes)) or not isinstance(yer_tutucular, Sequence):
        raise TypeError(f"placeholders bir str dizisi olmali, gelen: {type(yer_tutucular).__name__}")
    sonuc: list[str] = []
    for yt in yer_tutucular:
        if not isinstance(yt, str):
            raise TypeError(f"placeholders ogesi str olmali, gelen: {type(yt).__name__}")
        sonuc.append(_nfc(yt))
    return tuple(sonuc)


def _segment_yer_tutuculari(seg: Segment, i: int) -> tuple[str, ...]:
    """K2 v3: `Segment.placeholders` bicim hatasi -> `ContractViolation` (TranslatorError; pipeline yakalar)."""
    try:
        return _yer_tutuculari_dogrula(seg.placeholders)
    except TypeError as e:
        raise ContractViolation(f"segments[{i}].placeholders bicimi gecersiz: {e}") from e


def _dolu_bitmap(n: int, araliklar: Sequence[tuple[int, int]]) -> bytearray:
    """K5: konum bitmap'i -- `[a, b)` araliklari 1; ortusme denetimi `find(1, s, e)` ile O(e - s)."""
    dolu = bytearray(n)
    for a, b in araliklar:
        dolu[a:b] = b"\x01" * (b - a)
    return dolu


# ---------------------------------------------------------------------------
# K1: sinir baglami ve zincir aramasi
# ---------------------------------------------------------------------------

_Aday: TypeAlias = tuple[int, int, int]
"""`(start, end, terim indeksi)` -- zincir uyesi."""

_SURUYOR: Final = 0
_BASARI: Final = 1
_OLU: Final = 2


class _SinirBaglami:
    """K1 sinir denetimi ve zincir aramasi icin bir metnin cagri-yerel durumu (sicak yol: `__slots__`).

    `bitenler[p]` / `baslayanlar[p]`: `p`de biten / baslayan adaylar, en uzun once
    (`(diger uc, terim indeksi)`). `dolu`: korunan (yer tutucu) + kabul edilmis
    konumlar. `kabul_bas`/`kabul_bit`: kabul edilmis adaylarin uclari (zincir
    komsusu olarak sinir verir). `olumsuz_sol`/`olumsuz_sag`: o yonde gercek
    sinira ulasamayan konumlar (kalici: doluluk yalniz artar, oluluk kararli).
    """

    __slots__ = (
        "metin", "n", "yt_baslari", "yt_bitisleri", "dolu", "bitenler", "baslayanlar",
        "kabul_bas", "kabul_bit", "olumsuz_sol", "olumsuz_sag",
    )

    def __init__(self, metin: str, korunan: Sequence[tuple[int, int]], adaylar: Sequence[tuple[int, int, int]]) -> None:
        self.metin = metin
        self.n = len(metin)
        self.yt_baslari = {a for a, _ in korunan}
        self.yt_bitisleri = {b for _, b in korunan}
        self.dolu = _dolu_bitmap(self.n, korunan)
        self.bitenler: dict[int, list[tuple[int, int]]] = {}
        self.baslayanlar: dict[int, list[tuple[int, int]]] = {}
        for eksi_n, start, j in adaylar:  # uzunluk azalan sirada gelir -> her liste en uzun once
            end = start - eksi_n
            self.bitenler.setdefault(end, []).append((start, j))
            self.baslayanlar.setdefault(start, []).append((end, j))
        self.kabul_bas: set[int] = set()
        self.kabul_bit: set[int] = set()
        self.olumsuz_sol: set[int] = set()
        self.olumsuz_sag: set[int] = set()

    # -- gercek sinirlar ---------------------------------------------------------

    def gercek_sol(self, start: int) -> bool:
        """Terimden ONCE gercek sinir: metin basi, yer tutucu ucu, sinir karakteri, betik gecisi."""
        if start == 0 or start in self.yt_bitisleri:
            return True
        onceki = self.metin[start - 1]
        return _sinir_karakteri(onceki) or _betik(onceki) != _betik(self.metin[start])

    def _sag_temel(self, end: int) -> bool:
        """`end`den SONRA gercek sinir (ek zinciri haric); `metin[end - 1]` terimin ya da ekin son karakteri."""
        if end == self.n or end in self.yt_baslari:
            return True
        sonraki = self.metin[end]
        if unicodedata.category(sonraki).startswith("M"):
            return False  # birlestirici isaret onceki karaktere aittir
        return _sinir_karakteri(sonraki) or _betik(self.metin[end - 1]) != _betik(sonraki)

    def _ek_sonrasi(self, konum: int, derinlik: int) -> bool:
        """K1 (G6 + v3): ek (en uzun once) + EKTEN SONRA gercek sinir; en fazla `derinlik` ek zinciri."""
        if derinlik <= 0 or konum >= self.n:
            return False
        for ek in _EK_ILK_KARAKTER.get(self.metin[konum], ()):
            if self.metin.startswith(ek, konum):
                sonrasi = konum + len(ek)
                if self._sag_temel(sonrasi) or self._ek_sonrasi(sonrasi, derinlik - 1):
                    return True
        return False

    def gercek_sag(self, end: int) -> bool:
        """Terimden SONRA gercek sinir (KR/JP ek zinciri dahil)."""
        return self._sag_temel(end) or self._ek_sonrasi(end, _EK_ZINCIRI)

    def sinir_sol(self, konum: int) -> bool:
        """`konum` sol sinir mi: kabul edilmis komsunun bitisi ya da gercek sol sinir."""
        return konum in self.kabul_bit or self.gercek_sol(konum)

    def sinir_sag(self, konum: int) -> bool:
        """`konum` sag sinir mi: kabul edilmis komsunun baslangici ya da gercek sag sinir."""
        return konum in self.kabul_bas or self.gercek_sag(konum)

    # -- doluluk / kabul -----------------------------------------------------------

    def dolu_mu(self, start: int, end: int) -> bool:
        return self.dolu.find(1, start, end) != -1

    def kabul(self, start: int, end: int) -> None:
        self.dolu[start:end] = b"\x01" * (end - start)
        self.kabul_bas.add(start)
        self.kabul_bit.add(end)

    # -- zincir ------------------------------------------------------------------

    def zincir(self, start: int, end: int, sol_ok: bool, sag_ok: bool) -> tuple[list[_Aday], list[_Aday]] | None:
        """`[start, end)` adayinin sol ve sag zincir yollari; bir yon gercek sinira ulasamazsa `None`.

        `sol_ok`/`sag_ok`: cagiranin hesapladigi `sinir_sol(start)` / `sinir_sag(end)`.

        Iki yon ES ZAMANLI, adim adim aranir: bir yon olu cikar cikmaz durulur --
        boylece canli yonun (uzun olabilir) maliyeti olu yonun adim sayisiyla
        sinirlanir ve olu konumlar hafizaya alindigi icin toplam maliyet amortize
        dogrusaldir (yapay `Marcus` x 8000 + `x` zinciri).
        """
        if (not sol_ok and start in self.olumsuz_sol) or (not sag_ok and end in self.olumsuz_sag):
            return None
        sol = _ZincirDfs(self, start, -1, sol_ok)
        sag = _ZincirDfs(self, end, 1, sag_ok)
        while True:
            if sol.durum == _OLU or sag.durum == _OLU:
                return None
            if sol.durum == _BASARI and sag.durum == _BASARI:
                return sol.yol, sag.yol
            if sol.durum == _SURUYOR:
                sol.adim()
            if sag.durum == _SURUYOR and sol.durum != _OLU:
                sag.adim()


class _ZincirDfs:
    """Tek yonlu, yigin tabanli (ozyinelemesiz), adim adim zincir aramasi.

    `yon < 0`: `konum`da BITEN adaylar uzerinden sola; `yon > 0`: `konum`da
    BASLAYAN adaylar uzerinden saga. Her `adim()` bir kenar dener ya da tukenen
    bir dugumu olu isaretleyip geri sarar. `durum` `_BASARI` olunca `yol`
    kok konumdan gercek sinira uzanan uyeleri tasir.
    """

    __slots__ = ("bag", "yon", "komsular", "olumsuz", "sinir", "yigin", "yol", "durum")

    def __init__(self, bag: _SinirBaglami, konum: int, yon: int, sinir: bool) -> None:
        """`sinir`: kok konum zaten sinirsa (`sinir_sol`/`sinir_sag`) arama bos yolla biter."""
        self.bag = bag
        self.yon = yon
        self.komsular = bag.bitenler if yon < 0 else bag.baslayanlar
        self.olumsuz = bag.olumsuz_sol if yon < 0 else bag.olumsuz_sag
        self.sinir = bag.sinir_sol if yon < 0 else bag.sinir_sag
        self.yol: list[_Aday] = []
        self.yigin: list[tuple[int, int]] = []  # (konum, sonraki aday indeksi)
        if sinir:
            self.durum = _BASARI
        else:  # kok konumun oluluk denetimi `zincir()`de (nesne kurulmadan once)
            self.durum = _SURUYOR
            self.yigin.append((konum, 0))

    def adim(self) -> None:
        p, i = self.yigin[-1]
        liste = self.komsular.get(p, ())
        while i < len(liste):
            q, j = liste[i]
            i += 1
            start, end = (q, p) if self.yon < 0 else (p, q)
            if q in self.olumsuz or self.bag.dolu_mu(start, end):
                continue
            self.yigin[-1] = (p, i)
            self.yol.append((start, end, j))
            if self.sinir(q):
                self.durum = _BASARI
            else:
                self.yigin.append((q, 0))
            return
        # tum kenarlar denendi: bu konumdan bu yonde gercek sinir yok (kalici); tukenmis atalari da tek seferde sar
        while True:
            self.olumsuz.add(p)
            self.yigin.pop()
            if self.yol:
                self.yol.pop()
            if not self.yigin:
                self.durum = _OLU
                return
            p, i = self.yigin[-1]
            if i < len(self.komsular.get(p, ())):
                return


# ---------------------------------------------------------------------------
# yukleme ve sema (K6)
# ---------------------------------------------------------------------------


def _metin_alani(kayit: dict[str, object], anahtar: str, etiket: str) -> str:
    """K6: zorunlu `str` alan -- eksik, `str` degil, bos, bas/son bosluklu -> `ValueError`."""
    if anahtar not in kayit:
        raise ValueError(f"sozluk semasi: {etiket}: '{anahtar}' alani eksik")
    deger = kayit[anahtar]
    if not isinstance(deger, str):
        raise ValueError(f"sozluk semasi: {etiket}: '{anahtar}' str olmali, gelen: {type(deger).__name__}")
    if not deger.strip():
        raise ValueError(f"sozluk semasi: {etiket}: '{anahtar}' bos")
    if deger != deger.strip():
        raise ValueError(f"sozluk semasi: {etiket}: '{anahtar}' bas/son bosluk tasiyor: {deger!r}")
    return _nfc(deger)


def _kaydi_dogrula(indeks: int, ham: object) -> SozlukTerimi:
    """K6: tek kayit -> `SozlukTerimi`; her red sinifi terim adiyla `ValueError`."""
    if not isinstance(ham, dict):
        raise ValueError(f"sozluk semasi: terim kaydi #{indeks} bir JSON nesnesi degil: {type(ham).__name__}")
    kayit: dict[str, object] = {str(k): v for k, v in ham.items()}
    kaynak = _metin_alani(kayit, _ANAHTAR_KAYNAK, f"terim kaydi #{indeks}")
    etiket = f"terim {kaynak!r}"
    fazla = sorted(set(kayit) - _KAYIT_ANAHTARLARI)
    if fazla:
        raise ValueError(f"sozluk semasi: {etiket}: bilinmeyen anahtar(lar) {fazla}; izinli: {sorted(_KAYIT_ANAHTARLARI)}")
    if len(kaynak) > _KAYNAK_AZAMI:
        raise ValueError(f"sozluk semasi: {etiket}: kaynak {len(kaynak)} kodpoint, en fazla {_KAYNAK_AZAMI} olabilir")
    for ch in kaynak:
        if ch in _CUMLE_SONU:
            raise ValueError(f"sozluk semasi: {etiket}: kaynak cumle sonu isareti iceremez ({_CUMLE_SONU}); gomme cumle sinirini yutar")
    hedef = _metin_alani(kayit, _ANAHTAR_HEDEF, etiket)
    for ch in hedef:
        if ch in _CUMLE_SONU:
            raise ValueError(f"sozluk semasi: {etiket}: hedef cumle sonu isareti iceremez ({_CUMLE_SONU}); bolmeyi tetikler")
        if ch in _YER_TUTUCU_AYRACLARI:
            raise ValueError(f"sozluk semasi: {etiket}: hedef yer tutucu ayraci iceremez ({_YER_TUTUCU_AYRACLARI})")
        if unicodedata.category(ch) == "Cc":
            raise ValueError(f"sozluk semasi: {etiket}: hedef kontrol karakteri iceremez (U+{ord(ch):04X}); satir bolmesine gider")
    not_ = kayit.get(_ANAHTAR_NOT)
    if not_ is not None and not isinstance(not_, str):
        raise ValueError(f"sozluk semasi: {etiket}: 'not' str ya da null olmali, gelen: {type(not_).__name__}")
    izin = kayit.get(_ANAHTAR_IZIN, False)
    if not isinstance(izin, bool):
        raise ValueError(f"sozluk semasi: {etiket}: '{_ANAHTAR_IZIN}' bool olmali, gelen: {type(izin).__name__}")
    if len(kaynak) == 1 and not izin:
        raise ValueError(
            f"sozluk semasi: {etiket}: tek kodpointlik kaynak terim (tek hangul hecesi / tek kanji / tek harf) "
            f"sinir kuraliyla bilesiklerden ayristirilamaz; bilincli kabul icin '{_ANAHTAR_IZIN}': true"
        )
    return SozlukTerimi(kaynak=kaynak, hedef=ilk_harfi_buyut(hedef), note=not_, kisa_terim_izni=izin)


def _terimleri_yukle(yol: Path) -> tuple[SozlukTerimi, ...]:
    """K6: dosya BAYT ile okunur, `json.loads(bayt)` (BOM cozulur); `FileNotFoundError` sarilmaz."""
    ham = yol.read_bytes()
    try:
        veri: object = json.loads(ham)
    except ValueError as e:
        raise ValueError(f"sozluk JSON ayristirilamadi ({yol.name}): {e}") from e
    if not isinstance(veri, dict) or _ANAHTAR_TERIMLER not in veri:
        raise ValueError(f"sozluk semasi ({yol.name}): ust duzey '{_ANAHTAR_TERIMLER}' listesi tasiyan bir JSON nesnesi olmali")
    kayitlar = veri[_ANAHTAR_TERIMLER]
    if not isinstance(kayitlar, list):
        raise ValueError(f"sozluk semasi ({yol.name}): '{_ANAHTAR_TERIMLER}' bir liste olmali, gelen: {type(kayitlar).__name__}")
    return tuple(_kaydi_dogrula(i, k) for i, k in enumerate(kayitlar))


def _anahtar(metin: str) -> str:
    """IGNORECASE denkligiyle ortusen kanonik anahtar: casefold + Turkce I sinifi (`i/I/İ/ı`) tek harf (olculdu, K1)."""
    return metin.casefold().replace("i̇", "i").replace("ı", "i")


_TrieDugumu: TypeAlias = dict[str, tuple[str, "_TrieDugumu"]]
"""Trie dugumu: `anahtar -> (regex literali, cocuk)`; anahtar `_trie_anahtari`, literal sinifin ILK gorulen uyesi."""
_TERMINAL: Final = ""


def _trie_anahtari(ch: str) -> str:
    """Trie dugum anahtari = IGNORECASE denklik sinifinin KANONIK anahtari (`_anahtar`, coklu kodpoint olabilir).

    IGNORECASE'in denk saydigi karakterler (`M`/`m`, `İ`/`I`/`ı`/`i`, `ß`/`ẞ`,
    `ᾈ`/`ᾀ`, `ΐ`/`ΐ`, `ﬅ`/`ﬆ`) AYNI dala duser; regex literali olarak dalin ilk
    gorulen uyesi yazilir (denklik sinifi oldugu icin her uyeyi esler). Tur 1
    coklu-kodpoint katlamada karakterin kendisini anahtar yapiyordu (`ß`/`ẞ`
    ayri dal, 34 ayrisan cift), `ch.lower()` temsilcisi de 3 cifti kaciriyordu
    (ikisi de kucuk harf olan `_EXTRA_CASES` ciftleri) -- tum Unicode olcumu
    `evidence/olcum-trie-anahtari-ignorecase-denkligi-tur2.txt` (Tester-A O-A1).
    """
    return _anahtar(ch)


def _trie_govdesi(dugum: _TrieDugumu) -> str:
    """Trie -> regex govdesi. Terminal dugumde cocuklar `(?:...)?` ile ONCE denenir -> konumdaki EN UZUN terim.

    Ozyineleme derinligi en uzun terimin uzunlugu + 1; K6 kaynak <= 100 kodpoint bunu sinirlar.
    """
    dallar = [re.escape(literal) + _trie_govdesi(alt) for k, (literal, alt) in dugum.items() if k != _TERMINAL]
    if not dallar:
        return ""
    if _TERMINAL in dugum:
        return "(?:" + "|".join(dallar) + ")?"
    return dallar[0] if len(dallar) == 1 else "(?:" + "|".join(dallar) + ")"


def _tarama_deseni(terimler: Sequence[SozlukTerimi]) -> re.Pattern[str]:
    """K1/K5: ileri-bakisli TRIE deseni; `group(1)` = konumdan baslayan en uzun terimin metindeki dilimi.

    Duz alternation her konumda her terimi dener (50 terim: 28 ms, 500 terim:
    300+ ms / 1000 segment). Trie'de bir konumda yalniz ilk karakteri tutan
    dal yurur; onde ilk-karakter kumesi bekcisi (IGNORECASE kumeye de
    uygulanir). Maliyet terim sayisindan bagimsiz (500 terimde de ~13 ms).
    Dugum anahtarlari denklik sinifi temsilcisidir (`_trie_anahtari`);
    IGNORECASE literal karsilastirmayi ustlenir.
    """
    kok: _TrieDugumu = {}
    for t in terimler:
        dugum = kok
        for ch in t.kaynak:
            dugum = dugum.setdefault(_trie_anahtari(ch), (ch, {}))[1]
        dugum[_TERMINAL] = ("", {})
    ilk_karakterler = "".join(sorted(literal for k, (literal, _) in kok.items() if k != _TERMINAL))
    return re.compile(f"(?=[{re.escape(ilk_karakterler)}])(?=({_trie_govdesi(kok)}))", re.IGNORECASE)


class GlossaryStore:
    """Oyun profili basina terim sozlugu; JSON'dan yuklenir, sonra DEGISMEZ (K5/K6).

    `lookup(text, placeholders)` -> `list[TermHit]` (K1/K3), `lookup_segments`
    `segment_index` doldurur, `terimler`/`len` yuklenmis kayitlar.
    """

    def __init__(self, json_path: Path | str) -> None:
        if isinstance(json_path, str):
            json_path = Path(json_path)
        if not isinstance(json_path, Path):
            raise TypeError(f"json_path Path ya da str olmali, gelen: {type(json_path).__name__}")
        self._yol: Path = json_path
        ham = _terimleri_yukle(json_path)
        # K1: uzunluk azalan, esitlikte JSON sirasi (kararli sort).
        self._terimler: tuple[SozlukTerimi, ...] = tuple(sorted(ham, key=lambda t: -len(t.kaynak)))
        self._anahtarlar: dict[str, int] = self._anahtarlari_kur()
        self._desen: re.Pattern[str] | None = _tarama_deseni(self._terimler) if self._terimler else None
        self._onekler: tuple[tuple[int, ...], ...] = self._onekleri_hesapla()

    # -- yukleme sonrasi kurulum -------------------------------------------------

    def _anahtarlari_kur(self) -> dict[str, int]:
        """K6: kanonik anahtar -> terim indeksi; ayni anahtara ikinci kaynak (`Marcus`/`MARCUS`, `istanbul`/`İstanbul`) -> `ValueError`."""
        anahtarlar: dict[str, int] = {}
        for i, t in enumerate(self._terimler):
            k = _anahtar(t.kaynak)
            if k in anahtarlar:
                raise ValueError(
                    f"sozluk semasi: terim {t.kaynak!r}: tekrar eden kaynak ({self._terimler[anahtarlar[k]].kaynak!r} ile ayni)"
                )
            anahtarlar[k] = i
        return anahtarlar

    def _indeks(self, dilim: str) -> int | None:
        """Metindeki dilim (ya da bir terimin oneki) -> terim indeksi, kanonik anahtarla.

        `_anahtar`, IGNORECASE'in denk saydigi her kodpoint ciftinde ayni
        anahtari verir (tum Unicode tarandi: `evidence/olcum-*-ignorecase-
        denkligi*.txt`); yedek tarama gerekmez.
        """
        j = self._anahtarlar.get(_anahtar(dilim))
        if j is not None and len(self._terimler[j].kaynak) == len(dilim):
            return j
        return None

    def _onekleri_hesapla(self) -> tuple[tuple[int, ...], ...]:
        """K1: her terim icin, ayni konumda baslayabilen DAHA KISA terimlerin indeksleri (onekleri)."""
        uzunluklar = sorted({len(t.kaynak) for t in self._terimler})
        sonuc: list[tuple[int, ...]] = []
        for t in self._terimler:
            onekler: list[int] = []
            for n in uzunluklar:
                if n >= len(t.kaynak):
                    break
                j = self._indeks(t.kaynak[:n])
                if j is not None:
                    onekler.append(j)
            sonuc.append(tuple(onekler))
        return tuple(sonuc)

    # -- ozellikler --------------------------------------------------------------

    @property
    def yol(self) -> Path:
        return self._yol

    @property
    def terimler(self) -> tuple[SozlukTerimi, ...]:
        """Uzunluk-azalan sirali kayitlar (`kaynak` NFC, `hedef` ilk harfi buyuk)."""
        return self._terimler

    def __len__(self) -> int:
        return len(self._terimler)

    def __repr__(self) -> str:
        return f"GlossaryStore(terim_sayisi={len(self._terimler)}, dosya={self._yol.name!r})"

    # -- esleme (K1/K3) ------------------------------------------------------------

    def lookup(self, text: str, placeholders: Sequence[str] = ()) -> list[TermHit]:
        """K1/K3: metindeki terim eslemeleri, `start` artan; `segment_index=None`.

        `text` NFC'lenir; indeksler NFC metne gore kodpoint. `placeholders`
        gecisleri korunur ve uclari sinir sayilir. Saf: I/O yok, durum yok.
        """
        if not isinstance(text, str):
            raise TypeError(f"text str olmali, gelen: {type(text).__name__}")
        return self._ara(text, _yer_tutuculari_dogrula(placeholders), None)

    def _adaylar(self, metin: str) -> list[tuple[int, int, int]]:
        """K1: TAM aday kumesi `(-uzunluk, start, terim indeksi)`, `(uzunluk azalan, start artan, sozluk sirasi)` sirali."""
        assert self._desen is not None
        adaylar: list[tuple[int, int, int]] = []
        for m in self._desen.finditer(metin):
            start = m.start()
            en_uzun = self._indeks(m.group(1))
            if en_uzun is None:  # pragma: no cover -- trie yalniz sozluk terimlerini uretir
                continue
            for j in (en_uzun, *self._onekler[en_uzun]):
                adaylar.append((-len(self._terimler[j].kaynak), start, j))
        adaylar.sort()
        return adaylar

    def _ara(self, text: str, yer_tutucular: tuple[str, ...], segment_index: int | None) -> list[TermHit]:
        """`lookup`un govdesi; `segment_index` dogrudan yazilir (`lookup_segments` kopyasiz)."""
        if self._desen is None or not text:
            return []
        metin = _nfc(text)
        adaylar = self._adaylar(metin)
        if not adaylar:
            return []
        baglam = _SinirBaglami(metin, _korunan_araliklar(metin, yer_tutucular), adaylar)

        hits: list[TermHit] = []
        for eksi_uzunluk, start, j in adaylar:
            end = start - eksi_uzunluk
            if baglam.dolu_mu(start, end):
                continue
            sol_ok = baglam.sinir_sol(start)
            sag_ok = baglam.sinir_sag(end)
            if sol_ok and sag_ok:
                uyeler: list[_Aday] = [(start, end, j)]  # sicak yol: iki uc sinir, zincir aramasi gereksiz
            else:
                yollar = baglam.zincir(start, end, sol_ok, sag_ok)
                if yollar is None:
                    continue
                uyeler = [*yollar[0], (start, end, j), *yollar[1]]
            for s, e, jj in uyeler:
                baglam.kabul(s, e)
                t = self._terimler[jj]
                hits.append(
                    TermHit(
                        source_term=metin[s:e],
                        target_term=t.hedef,
                        start=s,
                        end=e,
                        segment_index=segment_index,
                        note=t.note,
                    )
                )
        hits.sort(key=lambda h: h.start)
        return hits

    def lookup_segments(self, segments: Sequence[Segment]) -> tuple[TermHit, ...]:
        """Her segmentin `text`/`placeholders`i ile `lookup`; `segment_index` dolu; segment sirasi, sonra `start`.

        Segment kaynakli bicim hatasi (`text` `str` degil, `placeholders` duz `str`/`str` olmayan oge) -> `ContractViolation`.
        """
        hits: list[TermHit] = []
        for i, seg in enumerate(segments):
            if not isinstance(seg, Segment) or not isinstance(seg.text, str):
                raise ContractViolation(f"segments[{i}] Segment degil ya da text str degil: {type(seg).__name__}")
            hits.extend(self._ara(seg.text, _segment_yer_tutuculari(seg, i), i))
        return tuple(hits)


# ---------------------------------------------------------------------------
# gomme (K2/K3/K4/K7)
# ---------------------------------------------------------------------------


def _segment_indeksi(hit: TermHit, sira: int, n: int) -> int:
    """K7: `None`/`bool`/`int` degil/aralik disi -> `ContractViolation`."""
    i = hit.segment_index
    if i is None or isinstance(i, bool) or not isinstance(i, int):
        raise ContractViolation(f"hits[{sira}].segment_index gecersiz: {type(i).__name__} (int, [0, {n}) bekleniyor)")
    if not 0 <= i < n:
        raise ContractViolation(f"hits[{sira}].segment_index aralik disi: {i} (segment sayisi {n})")
    return i


def _hitleri_dogrula(metin: str, grup: Sequence[tuple[int, TermHit]], korunan: Sequence[tuple[int, int]]) -> list[TermHit]:
    """K2/K3: tek segmentin hit'leri -- aralik, tam esitlik, ortusme, yer tutucu; `start` ARTAN sirali doner."""
    n = len(metin)
    korunan_bit = _dolu_bitmap(n, korunan)
    for sira, h in grup:
        if not isinstance(h.start, int) or not isinstance(h.end, int) or isinstance(h.start, bool) or isinstance(h.end, bool):
            raise ContractViolation(f"hits[{sira}]: start/end int olmali")
        if not 0 <= h.start < h.end <= n:
            raise ContractViolation(f"hits[{sira}]: aralik gecersiz [{h.start}, {h.end}) (metin uzunlugu {n})")
        if not isinstance(h.source_term, str) or metin[h.start : h.end] != _nfc(h.source_term):
            raise ContractViolation(f"hits[{sira}]: source_term metnin [{h.start}, {h.end}) dilimiyle ayni degil")
        if not isinstance(h.target_term, str) or not h.target_term:
            raise ContractViolation(f"hits[{sira}]: target_term bos ya da str degil")
        if korunan_bit.find(1, h.start, h.end) != -1:
            raise ContractViolation(f"hits[{sira}]: aralik [{h.start}, {h.end}) bir yer tutucuyla ortusuyor")
    sirali = sorted(grup, key=lambda c: c[1].start)
    for (sira_a, a), (sira_b, b) in zip(sirali, sirali[1:]):
        if a.end > b.start:
            raise ContractViolation(f"hits[{sira_a}] ve hits[{sira_b}] ortusuyor: [{a.start}, {a.end}) / [{b.start}, {b.end})")
    return [h for _, h in sirali]


def terimleri_gom(segments: Sequence[Segment], hits: Sequence[TermHit]) -> tuple[Segment, ...]:
    """K2: her hit araligini ilk harfi buyuk `target_term` ile degistirir; aralik disi karakter aynen (NFC disinda).

    Hit'i olan segmentte `text` ve `placeholders` NFC (K2 v3). Hit'i olmayan
    segment ve bos `hits` -> ayni nesne (`is`). Gecersiz hit ya da segment
    bicimi (K2/K3/K7) -> `ContractViolation`, cagri butunuyle duser.
    """
    segs = tuple(segments)
    if not hits:
        return segs
    n = len(segs)
    gruplar: dict[int, list[tuple[int, TermHit]]] = {}
    for sira, h in enumerate(hits):
        if not isinstance(h, TermHit):
            raise ContractViolation(f"hits[{sira}] TermHit degil: {type(h).__name__}")
        gruplar.setdefault(_segment_indeksi(h, sira, n), []).append((sira, h))

    cikti = list(segs)
    for i, grup in gruplar.items():
        seg = segs[i]
        if not isinstance(seg, Segment) or not isinstance(seg.text, str):
            raise ContractViolation(f"segments[{i}] Segment degil ya da text str degil: {type(seg).__name__}")
        yer_tutucular = _segment_yer_tutuculari(seg, i)
        metin = _nfc(seg.text)
        korunan = _korunan_araliklar(metin, yer_tutucular)
        for h in reversed(_hitleri_dogrula(metin, grup, korunan)):  # start AZALAN: indeksler kaymaz
            metin = metin[: h.start] + ilk_harfi_buyut(_nfc(h.target_term)) + metin[h.end :]
        cikti[i] = dataclasses.replace(seg, text=metin, placeholders=yer_tutucular)
    return tuple(cikti)
