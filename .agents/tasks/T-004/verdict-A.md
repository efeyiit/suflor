---
task: T-004
role: tester
round: 6
decision: onay
checks:
  - name: "mypy --strict temiz (normalizer.py + presets.py)"
    cmd: "python -m mypy --strict src/ocr/normalizer.py src/ocr/presets.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r6-mypy.txt
  - name: "implementer test dosyasi yesil"
    cmd: "python -m pytest tests/unit/ocr/test_normalizer.py -q"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r6-pytest_implementer.txt
  - name: "saflik kapisi (K29 dahil) exit 0"
    cmd: "python .agents/tasks/T-004/purity_check.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r6-purity_check.txt
  - name: "olcu kitinin kendi sagligi exit 0"
    cmd: "python .agents/tasks/T-004/olcu_kiti.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r6-olcu_kiti.txt
  - name: "tur 6 taban: tests/ tamami (sefin olctugu 821)"
    cmd: "python -m pytest tests -q"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r6-pytest_tests_tamami.txt
  - name: "tester_A tur 6 oncesi taban (yeni dosya EKLENMEDEN)"
    cmd: "python -m pytest .agents/tasks/T-004/tester_A -q"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r6-pytest_tester_A-baslangic.txt
  - name: "tester_A tur 6 sonrasi (yeni garanti-alani dosyasi dahil)"
    cmd: "python -m pytest .agents/tasks/T-004/tester_A -q"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r6-pytest_tester_A.txt
  - name: "kor tester takimi -- onuncu bir kirik var mi (sefin tabani 388)"
    cmd: "python -m pytest .agents/tasks/T-004/tester_A .agents/tasks/T-004/tester_B .agents/tasks/T-004/tester_C -q"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r6-pytest_kor_takim.txt
  - name: "mercek A/2 -- `_group`/`_raw_query_pair` sinir alani ham sondasi"
    cmd: "python - (sinir alani sondasi; ham cikti dosyada)"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r6-sinir-alani-sondasi.txt
  - name: "yeni testlerin DISLERI -- dort mutant sondasi"
    cmd: "python scratchpad/dis_kontrolu.py (mutantlar monkeypatch; src/ DEGISTIRILMEDI)"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r6-dis_kontrolu-mutantlar.txt
  - name: "gozlem G2 -- M-c mutanti kitin dort kanalina gorunuyor mu"
    cmd: "python - (olcu6_kos x 3 on ayar, taban vs M-c)"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r6-gozlem-G2-kit-vs-Mc.txt
  - name: "yeni testlerin sayaclari -- alt sinirlar totoloji degil"
    cmd: "python - (derlem/segment/sinir/oge sayaclari)"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r6-sayaclar.txt
  - name: "BULGU N1 -- modul docstring '### K24' bolumu bayat (BLOKE ETMEZ)"
    cmd: "python - (AST: urunun cagri bicimi vs docstring iddiasi) + pytest -rx"
    exit_code: 0
    result: kaldi
    evidence: tester_A_evidence/r6-bulgu-N1-K24-bayat-docstring.txt
blocking_issues: []
notes:
  - "N1 (bloke etmez, dokumantasyon): `normalizer.py` modul docstring'inin `### K24` bolumu (satir 827-836) K28 ONCESI cagri bicimini SIMDIKI ZAMANDA ve KOSULSUZ anlatiyor; bolumde K28'e/`_raw_query_pair`'e ileri referans YOK. Davranis DOGRU. `.agents/tasks/T-004/tester_A/test_r6_garanti_alani.py::test_modul_docstringinin_K24_bolumu_bugunku_cagri_bicimini_anlatiyor` `xfail(strict=True)` olarak duruyor -- duzeltilince XPASS ile kendini duyurur."
  - "G1 (gozlem): `_group(..., blocks=())` uzunluk-tek sinirda `apply_inheritance=False` ILE DE `IndexError` yukseltiyor (olculdu). Dogru davranis -- K23'un 'bayrak bolumleme gecisinde HIC OKUNMAZ' degismezinin dogrudan sonucu -- ama `_group` docstring'inin `blocks=()` cumlesi bayragi anmiyor."
  - "G2 (gozlem): K28'in KARAR METNI sol tarafi 'kapanan GRUBUN kaynak bloklari' diye tanimliyor, UYGULAMA ise `tail` OGESININ kaynak bloklarindan seciyor. 4063 sinirda 0 ayrisma olctum, ama denklik adim 1-4'un BELGELENMEMIS bir yapisal ozelligine dayaniyor (ogeler okuma sirasinda BITISIK kosulara boluyor). O ozelligi bozan mutant kitin DORT kanalina da gorunmuyor (uc on ayarda `temiz=True`, hepsi 0)."
  - "Tur 6'da tester_A'ya dusen yeniden nisanlama isinin tamami kapandi: uc `strict=True` xfail yesil teste cevrildi, dorduncu xfail'in yerine `normalize` uzerinden gecen SIRASIZ girdili + >=3 bloklu kuyruklu makine denetimi kondu, `:401`'in kor sondasi urunun yeni sorgu bicimine esitlenip AST kapisiyla korundu."
  - "Yeni dosya: `.agents/tasks/T-004/tester_A/test_r6_garanti_alani.py` (27 gecen + 1 strict xfail). `src/` ve `tests/unit/ocr/` DEGISTIRILMEDI; olcu kiti ice aktarildi, DEGISTIRILMEDI."
---

# Tester-A · Tur 6 · Mercek: Garanti alanı

**Karar: ONAY.** Bloke edici bulgu yok. Bir dokümantasyon bulgusu (N1) ve iki
gözlem (G1, G2) bloke etmeyen olarak aşağıda; N1 için kalıcı bir `strict=True`
xfail işareti bıraktım.

Merceğin sorusu: *"Docstring/tip ne söz veriyor ve bu söz, fonksiyonun kabul
ettiği **her** girdi için tutuyor mu?"* — K28 ile açılan yeni yüzeyde
(`_raw_query_pair`, `_group(..., blocks=)`) bu soruyu sınır alanı taramasıyla
sordum.

## 0 · Taban — şefin ölçtüğü sayıların yeniden üretimi

| Komut | Şefin ölçtüğü | Benim ölçtüğüm |
|---|---|---|
| `mypy --strict` | exit 0 | exit 0 |
| `pytest tests/unit/ocr/test_normalizer.py` | 124 passed | **124 passed** |
| `purity_check.py` | exit 0 | exit 0, `TEMIZ` |
| `olcu_kiti.py` | exit 0, ayrışma 0/0/0 | exit 0, `KIT SAGLIGI: TEMIZ`, üç ön ayarda `ayrisma=0 kimlik=0 kapsam_ihlali=0 sira=0 sayi=0 patlama=0` |
| `pytest tests` | 821 passed | **821 passed** |
| kör takım (A+B+C), tur 6 başlangıcı | 388 passed, 0 kırık | **388 passed, 0 kırık** |
| kör takım, benim yeni dosyamla | — | **425 passed, 1 xfailed, 0 kırık** |

**Onuncu bir kırık yok.** Dördüncü xfail dahil, şefin §4.6/5 listesindeki
dokuz bayatlama tur 6 tabanında zaten kapanmış durumda.

## 1 · Bu turda tester_A'ya düşen yeniden nişanlama (tamamlandı)

`test_r5_partition_invariant.py`:

* Üç `strict=True` xfail → düzeltilmiş davranışı doğrulayan yeşil testler;
  yanlarında (a) mekanizmayı (sorgu çifti) doğrulayan, (b) aynı fixture'ın
  tur 5 biçiminde **hâlâ** yanlış sonuç verdiğini gösteren birer test.
* Dördüncü xfail (`test_r51_makine_denetimi_*`) `_group`/`normalize`
  çağırmadığı için **kaldırıldı**; yerine `normalize` üzerinden geçen,
  **sırasız girdi** (her girdinin karıştırılmış bir kopyası) ve **≥3 bloklu
  kuyruk** içeren yeni makine denetimi geldi. Alt sınırları makineyle
  sabitlendi: `sinir > 1000`, `coklu_sol > 200`, `uclu_sol > 50`,
  `coklu_sag > 50`, **`ayirt_edici > 20`** (indeks sırası ile okuma
  sırasının ayrıştığı sınır — `max(sb)` yazan bir uygulama ancak orada
  görünür). İki ayrı sonda kontrolü dişlerini kanıtlıyor (indeks-sırası
  mutantı ve tur 5 biçimi ikisi de ayrışma buluyor).
* `:401`'in kör sondası ürünün tur 6 yapısına eşitlendi
  (`_group_tur4_yeni_sorgu_bicimiyle`) ve bir daha **sessizce**
  bayatlamasın diye AST kapısı eklendi: ürünün miras sorgusu biçimi
  `*_raw_query_pair(tail, nxt, blocks), params` olarak pinli, yerel kopya
  onunla eşit olmak zorunda. Ayrıca sondanın gerçekten o yoldan geçtiği
  `_raw_query_pair` çağrı sayısıyla (>1000) ölçülüyor.

## 2 · Sınır alanı taraması — `source_blocks` her durumda tanımlı mı

Ham çıktı: `tester_A_evidence/r6-sinir-alani-sondasi.txt`.

```
_group([], params)                     [tester_C bicimi]   -> []
_group([], params, blocks=())                              -> []
_group([], params, apply_inheritance=False)                -> []
_group([tek_oge], params)              [blocks YOK]        -> [(0,)]
_raw_query_pair(source_blocks=())                          -> IndexError
_raw_query_pair(blocks=())                                 -> IndexError
_raw_query_pair(source_blocks=(5,), len(blocks)=1)         -> IndexError
_raw_query_pair tek elemanli sb -> ikame yapiliyor mu      -> Rect(x=0,y=0,w=10,h=10,...)  [HAM blogun kutusu]
_group(uzunluk-tek sinir, blocks=())  [apply_inh=True]     -> IndexError
_group(uzunluk-tek sinir, blocks=())  [apply_inh=False]    -> IndexError
_group('gap' siniri, blocks=())        [kisa devre]        -> [(0,), (1,)]
```

Dördü de docstring'in söz verdiği gibi: **sessiz yanlış değil, gürültülü
`IndexError`**. Patlamanın gecikmeli olduğu (`reason == "length" and
nxt.speaker is None` sınırı dışında doğmadığı) ayrıca sabitlendi — `"gap"`
sınırında `and` kısa devre yapıyor ve `blocks=()` sorun çıkarmıyor.

Segment düzeyinde K8'in koşulsuz iddiaları, **1800 girdilik düşman derlem ×
dört ön ayar** üzerinde (yalnız-etiket blokları, tam eşit `(y,x)` çiftleri,
yozlaşmış kutular, karıştırılmış girdi sırası):

```
segment = 25384   bos=0  artan/tekrarsiz=0  aralik=0  ayriklik=0
```

Ayrıca **`normalize` belgelenmemiş istisna atmıyor**: 7200 koşumda
`ValueError` dışında hiçbir istisna yok. Bu, K28'in koda açtığı `IndexError`
yolunun genel API'den erişilemediğinin ölçüsü — ve dişi var: `blocks`'u
kaydıran bir mutantta test `{'IndexError': 1188}` ile kırılıyor.

## 3 · K28'in KARAR METNİ ile UYGULAMASI aynı bloğu mu seçiyor

Bu, başka hiçbir yerde ölçülmüyor. Karar metni sol tarafı *"kapanan
**grubun** kaynak blokları arasında okuma sırasında son gelen blok"* diye
tanımlıyor; uygulama ise `tail` **öğesinin** kaynak bloklarından seçiyor.
Kitin kancası (`sorgu_kaydi`) hem bölümleme (`ignore_length=False`, sol
taraf = `current` = **kapanan grup**) hem miras (`ignore_length=True`, sol
taraf = `tail`) sorgularını kaydettiği için ikisi karşılaştırılabiliyor:

```
4063 miras siniri, 199 tanesinde `tail` grubun TAMAMINDAN kucuk (cok ogeli grup)
grup-son  !=  tail-son   ->   0
```

Denkliği mümkün kılan yapısal özelliği ayrıca ve doğrudan sabitledim: **adım
1–4, hayatta kalan blokları okuma sırasında bitişik ve artan koşulara
bölüyor** (adım 3'ün hyphen zinciri ve adım 4'ün etiket taşıması bu özelliği
bozmuyor) — 23859 öğede (8874'ü çok bloklu) `bitisiklik ihlali=0`, `sira ihlali=0`.

Şefin K28 gerekçesinde adlandırdığı **ek yüzey** (*"sırasız girdide `[-1]`
segment üretmeyen bir ETİKET bloğunu bile gösterebilir"*) de kapalı: 4063
miras sorgusunun hiçbirinde sorguya giren ham blok yalnız-etiket değil, ve
ürünün sorguya soktuğu `bbox` her seferinde K28'in tanımladığı bloğun
kutusu.

## 4 · Zincirleme miras — `tests/` altında pinli mi

**Pinli.** `tests/unit/ocr/test_normalizer.py::test_k28_olcu8_zincirleme_miras_uc_segmentte_korunur`
(AST ile bulundu, ad sabit kodlanmadı — `normalize` çağırıp `speaker`
listesini üç kez `Ada`'ya eşitleyen test aranıyor).

Pinin **kapsamını** kendi geometrimle genişlettim:

```
bes bloklu monolog  -> [((0,),'Ada'), ((1,),'Ada'), ((2,),'Ada'), ((3,),'Ada'), ((4,),'Ada')]
ortada gercek kopus -> [((0,),'Ada'), ((1,),'Ada'), ((2,),None),  ((3,),None)]
```

Zincirin uzunluğa bağlı bir tavanı yok; ve zincir "her segmente Ada yaz"
değil — gerçek geometrik kopuşta kesiliyor ve **bir daha başlamıyor**.

## 5 · Yeni testlerin dişleri — dört mutant sondası

`src/` değiştirilmeden, ürün modülünün öznitelikleri geçici olarak
yamalandı. Ham çıktı: `tester_A_evidence/r6-dis_kontrolu-mutantlar.txt`.

| Mutant | Ne yapıyor | Hangi yeni test kırılıyor |
|---|---|---|
| **M-a** | iki segment aynı bloğu paylaşıyor (K8 ayrıklık) | k8 alan taraması, bitişik koşular, yerel==ürün, etiket bloğu, zincir ×2 |
| **M-b** | `blocks` süzülmüş/kaydırılmış (M9 sınıfı) | **istisna sözleşmesi** (`{'IndexError': 1188}`) + hepsi |
| **M-c** | bitişik **olmayan** öğeler birleştiriliyor | **grup-vs-tail (88/3047)**, bitişik koşular, yerel==ürün, zincir ×2 |
| **M-d** | sol taraf okuma-sırası **ilk** blok | **etiket bloğu (98/4063)** |

Taban koşumda dördü de `GECTI` — yani sondalar totoloji değil.

**Bir bayatlama tuzağını kendi dosyamda kapattım.** İlk sürümde yapısal test
kendi yeniden uygulamamı ölçüyordu ve M-c'yi **göremiyordu** (`:401`'in tur
5'te düştüğü tuzağın aynısı). Düzeltildi: yapısal test artık ürünün
`_group`'a gerçekten geçirdiği öğe listesini ölçüyor, ve ayrıca
`test_yerel_turetim_urunun_group_girdisiyle_ESIT` iki tarafı makineyle
eşitleyerek bir daha sessizce ayrışmalarını engelliyor.

## 6 · Bulgu N1 — bloke etmez · modül docstring'inin `### K24` bölümü bayat

**Yeniden üretim:** `tester_A_evidence/r6-bulgu-N1-K24-bayat-docstring.txt`.

Ürünün gerçek çağrı biçimi (AST):

```
_group_rejection_reason(*_raw_query_pair(tail, nxt, blocks), params, ignore_length=True)
```

`normalizer.py:832-836` (modül docstring, `### K24` bölümü):

```
K21'in `ignore_length=True` IKINCI cagrisi ARTIK `_group_rejection_reason(current,
nxt, ...)` DEGIL, `_group_rejection_reason(tail, nxt, ...)` KULLANIR -- yani SOL
TARAF DAIMA grubun okuma-sirasindaki EN SON (birlesime en son KATILAN) HAM
ogesidir, `current`'in (birden fazla oge ICEREBILEN) BIRLESIK `bbox`'i DEGIL.
```

İki ayrı sorun:

1. **Çağrı biçimi artık bu değil.** İddia şimdiki zamanda ve koşulsuz;
   bölümde `K28` de `raw_query_pair` de **hiç geçmiyor** (ölçüldü: bölüm
   2720 karakter, ikisinin de sayısı 0).
2. *"`tail` … HAM öğesidir"* cümlesi, **bulgu R5-1'in tam olarak çürüttüğü
   cümledir** — `tail` adım 3'ten birleşik gelebilir. Bugün doğru olmasının
   sebebi `tail` değil, `_raw_query_pair`'in ham blok ikamesi.

**Neden bloke etmiyor:** (a) hiçbir girdi için davranışsal bir garanti
ihlal edilmiyor — merceğimin bloke etme ölçütü bu; (b) modül docstring'inin
**daha yeni ve daha önce gelen** `## K28` bölümü (satır 92–120) kuralı
eksiksiz ve doğru veriyor; (c) bir sonraki ajanın okuyacağı iki fonksiyonun
(`_group`, `_raw_query_pair`) docstring'leri K28'e açıkça referans veriyor
ve doğru.

**Neden yine de bir bulgu:** modül başka yerlerde bayatlayan iddiaları açık
kalıpla işaretliyor (`## K10`, satır 457: *"TUR 1'DE bu docstring … diyordu;
… düzeltir"*); `### K24` bölümü bu kalıbı kullanmıyor. Şef bunu bloke edici
saymak isterse gerekçesi hazır — ölçüm ve satır numaraları yukarıda.

## 7 · Gözlem G1 — `apply_inheritance=False` `blocks=()` patlamasını engellemiyor

Ölçüldü (bkz. sınır alanı sondası): uzunluk-tek sınırda `blocks=()` ile
`IndexError`, **iki bayrak değerinde de**. Bu **doğru** davranış ve K23'ün
"bayrak bölümleme geçişinde hiç okunmaz" değişmezinin doğrudan sonucu
(`pure_length_boundaries` bölümleme döngüsünde hesaplanıyor). Ancak
`_group` docstring'inin `blocks=()` cümlesi (*"varsayılan YALNIZCA `items`
boşken ya da uzunluk-tek sınır doğmayan doğrudan çağrılar içindir"*)
bayrağı anmıyor; doğrudan çağıran bir sonraki ajan
`apply_inheritance=False`'ın kalkan olduğunu sanabilir. Bir cümle yeterdi.
Testle sabitledim (`test_group_uzunluk_tek_sinirda_blocks_yoksa_GURULTULU_kirilir`,
iki bayrakla parametrize).

## 8 · Gözlem G2 — K28'in karar-metni uyumu belgelenmemiş bir yapıya dayanıyor

§3'teki denklik (grup-son == tail-son) adım 1–4'ün **bitişik koşu**
özelliğine dayanıyor ve bu özellik hiçbir yerde yazılı değil. Kırılırsa
K28 sessizce karar metninden ayrışır. Ölçtüm — o özelliği bozan M-c mutantı
**kitin dört kanalına da görünmüyor**:

```
taban  DIALOGUE/TOOLTIP/SUBTITLE  temiz=True  (hepsi 0)
M-c    DIALOGUE/TOOLTIP/SUBTITLE  temiz=True  ayrisma=0 kimlik=0 kapsam=0 sira=0 sayi=0 patlama=0
```

(Kararın "bilinen sınırlar" tablosundaki **M12** sınıfı: kitin `adim1_4`'ü
mutantla birlikte kayıyor.) Benim iki yeni testim onu 88/3047 ve
4743 ihlalle yakalıyor — yani bu sınıfın bir dilimi artık ölçülüyor.

**Öneri (bloke etmez):** bitişik-koşu özelliği `_raw_query_pair` ya da
`_group` docstring'ine bir cümleyle yazılsın, veya `known_gaps`'e girsin.

## 9 · Yazdığım dosyalar

* `.agents/tasks/T-004/tester_A/test_r6_garanti_alani.py` — **yeni**
  (27 geçen + 1 `strict=True` xfail).
* `.agents/tasks/T-004/tester_A_evidence/r6-*.txt` — ham çıktılar.

`src/`, `tests/unit/ocr/`, `olcu_kiti.py`, `conftest.py` ve diğer tester
dizinleri **değiştirilmedi**. Ölçü kiti yalnızca `sorgu_kaydi` /
`okuma_sirasi` için içe aktarıldı; referanslar bu dosyanın kendi
türetiminden geliyor (PROTOKOL §4.6/8).
