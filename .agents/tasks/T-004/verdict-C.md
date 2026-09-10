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
    evidence: tester_C_evidence/r6-01-mypy.txt
  - name: "urun testleri (tests/unit/ocr) yesil"
    cmd: "python -m pytest tests/unit/ocr/test_normalizer.py -q"
    exit_code: 0
    result: gecti
    evidence: tester_C_evidence/r6-02-pytest-urun.txt
  - name: "K29 kapisi (purity_check) exit 0"
    cmd: "python .agents/tasks/T-004/purity_check.py"
    exit_code: 0
    result: gecti
    evidence: tester_C_evidence/r6-03-purity.txt
  - name: "olcu kitinin kendi sagligi exit 0"
    cmd: "python .agents/tasks/T-004/olcu_kiti.py"
    exit_code: 0
    result: gecti
    evidence: tester_C_evidence/r6-04-olcu_kiti.txt
  - name: "Tester-C takimi (tur 5'ten 125 + tur 6'dan 143 = 268)"
    cmd: "python -m pytest .agents/tasks/T-004/tester_C -q"
    exit_code: 0
    result: gecti
    evidence: tester_C_evidence/r6-14-tester_C.txt
  - name: "tests/ tamami -- sefin tabani 821 passed"
    cmd: "python -m pytest tests -q"
    exit_code: 0
    result: gecti
    evidence: tester_C_evidence/r6-15-tests-tam.txt
  - name: "kor tester takimi -- ONUNCU (gercek) kirik var mi"
    cmd: "python -m pytest .agents/tasks/T-004/tester_A .agents/tasks/T-004/tester_B .agents/tasks/T-004/tester_C -q"
    exit_code: 0
    result: gecti
    evidence: tester_C_evidence/r6-16-kor-takim.txt
  - name: "M14 -- kitin uretmedigi BES girdi sinifinin sondasi"
    cmd: "python .agents/tasks/T-004/tester_C_evidence/r6-07-bes-girdi-sinifi-sonda.py"
    exit_code: 0
    result: gecti
    evidence: tester_C_evidence/r6-07-bes-girdi-sinifi-sonda.txt
  - name: "K32 (NFC/NFD), K31 (a)/(b), yozlasmis geometri sondasi"
    cmd: "python .agents/tasks/T-004/tester_C_evidence/r6-08-k31-k32-yozlasmis-sonda.py"
    exit_code: 0
    result: gecti
    evidence: tester_C_evidence/r6-08-k31-k32-yozlasmis-sonda.txt
  - name: "kotu kullanim yuzeyi + K16'nin K28 sag taraf regresyonu"
    cmd: "python .agents/tasks/T-004/tester_C_evidence/r6-09-kotu-kullanim-sonda.py"
    exit_code: 0
    result: gecti
    evidence: tester_C_evidence/r6-09-kotu-kullanim-sonda.txt
  - name: "K28 SOL taraf -- sefin adlandirdigi 'yalniz-etiket blogu' ek yuzeyi"
    cmd: "python .agents/tasks/T-004/tester_C_evidence/r6-10-etiket-blogu-sol-taraf-sonda.py"
    exit_code: 0
    result: gecti
    evidence: tester_C_evidence/r6-10-etiket-blogu-sol-taraf-sonda.txt
  - name: "K32'nin kapsam olcumu -- NFC olan adlar da reddediliyor mu"
    cmd: "python .agents/tasks/T-004/tester_C_evidence/r6-11-nfc-yetmez-taramasi.py"
    exit_code: 0
    result: gecti
    evidence: tester_C_evidence/r6-11-nfc-yetmez-taramasi.txt
  - name: "bes sinifin uzerinde degismez fuzz'i (1600 kosum, 0 ihlal)"
    cmd: "python .agents/tasks/T-004/tester_C_evidence/r6-12-bes-sinif-degismez-fuzz.py"
    exit_code: 0
    result: gecti
    evidence: tester_C_evidence/r6-12-bes-sinif-degismez-fuzz.txt
  - name: "mutasyon denetimi -- yeni 143 test totoloji mi (7/7 mutant kirildi)"
    cmd: "python .agents/tasks/T-004/tester_C_evidence/r6-13-mutasyon-denetimi.py"
    exit_code: 0
    result: gecti
    evidence: tester_C_evidence/r6-13-mutasyon-denetimi.txt
  - name: "olcek n=500/1000/2000 -- TEK BASINA kosuldu (sefin O3 uyarisi)"
    cmd: "python .agents/tasks/T-004/tester_C_evidence/r6-06-olcek-tek-basina.py"
    exit_code: 0
    result: gecti
    evidence: tester_C_evidence/r6-06-olcek-tek-basina.txt
blocking_issues: []
notes:
  - "K28 dogru uygulanmis: miras sorgusunun IKI tarafi da OZGUN bloktan, OKUMA sirasiyla. Yedi mutantin yedisi de yeni testlerimce kirildi."
  - "BLOKE ETMEYEN 1 (en onemlisi): K32'nin BELGELEDIGI KAPSAM, olculen olgudan DAR. Devanagari/Tayca/harekeli Arapca/nikudlu Ibranice adlar ZATEN NFC-normaldir (NFC == NFD) ve yine de konusmaci sayilmiyor; T-006'nin NFC uretmesi bu sinifi KAPATMAZ. Onerilen cumle asagida."
  - "BLOKE ETMEYEN 2: miras, `monitor_index`/`dpi_scale` SINIRINI asiyor. AYNI iki blok metin KISA ise K10 ValueError'u veriyor, UZUN ise (yalniz-uzunluk siniri) sessizce miras veriyor. Sonuc YALNIZCA metin uzunluguna bagli."
  - "BLOKE ETMEYEN 3: `NaN` bir `dpi_scale` kendisiyle esit olmadigi icin 'degerler uyusmuyor: (0, nan) != (0, nan)' gibi kendi icinde celiskili bir tani mesaji uretiyor; K7'nin `confidence` icin yaptigi on denetim burada yok."
  - "BLOKE ETMEYEN 4: ZWJ/emoji dizileri `max_group_chars`'i grapheme basina 5 codepoint sisiriyor -- K32'nin 'codepoint sayar' mekanizmasinin NFC/NFD DISINDAKI ikinci yuzeyi."
  - "Olcek KOTULESMEDI: n=500/1000/2000 -> 2.53-2.70 / 6.62-6.95 / 20.33-20.63 ms (tur 5: 3.199/8.429/24.866). K28'in en agir yolu (her sinirda cok bloklu tail) n=4000'de 18.3 ms, dogrusal."
  - "Kor takim: 623 passed, 1 xfailed, 0 kirik -- ONUNCU bir kirik YOK, gercek regresyon bulunamadi."
---

# Tester-C · T-004 · TUR 6 · MERCEK C — sınır, kötü kullanım ve dil

**Karar: ONAY.** Bloke edici bulgu yok. Dört bloke etmeyen bulgu var; dördü de
ölçüldü, ham çıktıları `tester_C_evidence/` altında, ikisi belgeleyen testle
sabitlendi.

Bu tur `tester_C/test_tur6_sinir_dil.py` (**143 yeni test**) eklendi. Tur 5
dosyası (`test_cjk_misuse_scale.py`, 125 test) **değiştirilmedi** — regresyon
avı olarak olduğu gibi koşuyor. Toplam **268 passed**.

`src/` ve `tests/unit/ocr/` altında **hiçbir şey değiştirilmedi**.

---

## 0. Kabul komutları ve taban

```
mypy --strict                       exit 0   Success: no issues found in 2 source files
pytest tests/unit/ocr/...           exit 0   124 passed
purity_check.py                     exit 0   TEMIZ
olcu_kiti.py                        exit 0   KIT SAGLIGI: TEMIZ
pytest tests                        exit 0   821 passed          <- sefin tabani, birebir
pytest tester_A tester_B tester_C   exit 0   623 passed, 1 xfailed, 0 failed
pytest tester_C                     exit 0   268 passed
```

Şefin haber verdiği dokuz bayat kırık **kapanmış** (kör takımda 0 kırık).
**Onuncu bir kırık görmedim** — bu turda gerçek regresyon yok. Kendi
`test_olcek_tur2/tur4` testlerim bu koşumda da yeşil geçti; yine de ölçeği
şefin O3 uyarısına uyarak **tek başına** ölçtüm (aşağıda §6).

---

## 1. Asıl iş — kitin ÜRETMEDİĞİ beş girdi sınıfı (M14)

Şefin "bilinen sınırlar" tablosu bu beş sınıfı bana verdi. Beşini de kurdum;
ham çıktı `r6-07-bes-girdi-sinifi-sonda.txt`.

### 1.1 Emoji / astral karakterler / ZWJ dizileri

```
  tek emoji U+1F44D                  len=1 kat=[So                  ] -> SILINDI
  ZWJ aile (5 cp)                    len=5 kat=[So Cf So Cf So      ] -> KORUNDU
  bayrak TR (2 cp)                   len=2 kat=[So So               ] -> KORUNDU
  varyasyon secici gunes (2 cp)      len=2 kat=[So Mn               ] -> KORUNDU
  varyasyon secicisiz gunes (1 cp)   len=1 kat=[So                  ] -> SILINDI
  astral CJK ext-B (1 cp)            len=1 kat=[Lo                  ] -> KORUNDU
  astral matematiksel bold A (1 cp)  len=1 kat=[Lu                  ] -> KORUNDU
  ten tonlu el (2 cp)                len=2 kat=[So Sk               ] -> KORUNDU
  keycap 1 (3 cp)                    len=3 kat=[Nd Mn Me            ] -> KORUNDU
```

**Doğru.** K4'ün tek-karakter kuralı `len(stripped) != 1` ile korunuyor; çok
kod noktalı dizilerin hiçbiri kurala girmiyor, astral **harfler** (`Lo`/`Lu`)
tek kod noktalı olsalar da `L*` dalından geçiyor. Karar **sınıf tabanlı**,
beyaz liste yok — K4'ün lafzı.

Konuşmacı adı yüzeyinde de aynı sınıf kuralı:

```
    '👨: merhaba'      -> speaker=None      (So, isalpha() False)
    '𝐀𝐁: merhaba'      -> speaker='𝐀𝐁'      (astral Lu)
    '𠀋: merhaba'      -> speaker='𠀋'       (astral Lo)
    'Ada👍: merhaba'    -> speaker=None      (ad icinde emoji -> tum etiket duser)
```

Yalnız vekil (lone surrogate — UTF-16 tabanlı bir motorun sızdırabileceği)
girdide **çökme yok**.

Mirasta `speaker` kod noktası düzeyinde korunuyor (`['0x52c7','0x8005']` iki
segmentte de aynı) — `_raw_query_pair`'in `replace(...)` ikamesi gerçekten
yalnız `bbox`'a dokunuyor.

**Bloke etmeyen bulgu 4** aşağıda §7.4: ZWJ dizileri `max_group_chars`'ı
grapheme başına 5 kod noktası şişiriyor.

### 1.2 `monitor_index ≠ 0`

Dört ön ayar × `monitor_index ∈ {0, 1, 7, -3}`: **bölümleme ve `speaker`
dizisi birebir aynı** — alan gerçekten atıl, geometriye karışmıyor.
Birleşmiş segment `monitor_index`'i **taşıyor** (varsayılan `0`'a düşmüyor).
Karışık monitör + birleşme → `ValueError` (K10 regresyonu ayakta).

**Bloke etmeyen bulgu 2** aşağıda §7.2.

### 1.3 `dpi_scale ≠ 1.0`

Dört ön ayar × `dpi_scale ∈ {1.0, 1.25, 1.5, 2.0, 0.5}`: **ayrışma yok**.
Ayrıca DPI'nin *gerçek* yüzeyini de ölçtüm — tüm koordinatları `k ∈ {2,3,4}`
ile ölçekleyince bölümleme **değişmiyor**, çünkü bütün eşikler çarpma ile ve
oran olarak yazılmış (`gap < oran * min(h)`). Bölmeye ya da mutlak piksel
eşiğine kayan bir uygulama burada ayrışırdı.

**Bloke etmeyen bulgu 3** aşağıda §7.3 (`NaN` `dpi_scale`).

### 1.4 ≥40 bloklu girdi

`n ∈ {40, 63, 120, 250}` × dört ön ayar: K8 (artan/tekrarsız/**ayrık**/aralık
içinde), K3 (çıktı sırası) ve K23 (miras açık/kapalı bölümleme birebir) hepsi
**TEMİZ**. 60 bloklu zincirde miras **sonuna kadar** taşınıyor:

```
    segment sayisi=60  farkli speaker degerleri=['Ada']
    None sayisi=0  'Ada' sayisi=60
```

Sırasız + CJK + yozlaşmış geometrili 40–70 bloklu 200 girdide K23 ihlali
**0/600**.

### 1.5 ASCII-dışı konuşmacı adı

On bir yazı sisteminde etiket doğru ayıklanıyor (kanji, hiragana, hangul,
Çince, Kiril, Yunanca, harekesiz Arapça, nikudsuz İbranice, halfwidth
katakana, Vietnamca NFC, fullwidth ayraç). `speaker` kod noktası düzeyinde
birebir; `ｶﾞﾝ` halfwidth katakana **NFKC ile açılmıyor** (ad süzgeci
normalizasyon yapmıyor — doğru).

ASCII-dışı adla üç segmentlik miras zinciri `勇者`/`魔王`/`Ада`/`مرحبا` için
çalışıyor. Yalnız-etiketli CJK blok (`勇者：`) 180px uzaktaki bloğa bile
taşınıyor (K9).

**Bloke etmeyen bulgu 1** aşağıda §7.1 — bu maddenin asıl bulgusu.

---

## 2. K32 — NFC / NFD

Ham çıktı: `r6-08-k31-k32-yozlasmis-sonda.txt`.

**Gövde de aksanlıysa segment sayısı değişiyor** (kendi bağımsız gövdemle —
doğal İspanyolca cümle, 80 cp NFC / 92 cp NFD):

```
  [govde+etiket aksanli] NFC: 1 segment  speakers=['María']  source_blocks=[(0, 1, 2)]
  [govde+etiket aksanli] NFD: 2 segment  speakers=[None, None]  source_blocks=[(0, 1), (2,)]
```

Şefin ölçümü 1/3 idi; benimki 1/2. **Çelişki değil** — fark gövdenin kod
noktası uzunluğuna bağlı ve şef gövdesini kararda açıkça pinlemiş. Olgu
(bölümlemenin NFD'de değiştiği) bağımsız bir gövdeyle **yeniden üretildi**.

**Yalnız etiket aksanlıysa segment sayısı aynı, `speaker` `None`'a düşüyor**:

```
    NFC: 1 segment  speaker='María'  text='hola hola hola ...'
    NFD: 1 segment  speaker=None     text='María: hola hola ...'   <- etiket metinde
```

Çok bloklu gövdeyle de aynı (`1/1`, `speaker` `'María'` → `None`). Şefin
cümlesi birebir doğru.

Ayraç kümesi NFD'den **etkilenmiyor** (`:` ve `：` NFD altında değişmiyor);
düşen şey adın kendisi, ayraç değil.

`_MAX_SPEAKER_NAME_LEN` de kod noktası sayıyor: 40 cp tam sınırda kabul edilen
bir ad NFD'de 41 cp olup **reddediliyor**.

Bunların hepsi `test_k32_*` (dört test) ile sabitlendi.

---

## 3. K31 (a) / (b)

```
  (a) ayni ad, IKISI de etiketli
      speaker='Ada'  text='merhaba nasilsin'          source_blocks=(0, 1)
  (b) ikinci etiket RAKAMLI
      speaker='Ada'  text='merhaba Ada2: nasilsin'    source_blocks=(0, 1)
  (kontrol) IKI FARKLI taninan ad
      speaker='Ada'  text='merhaba'   / speaker='Bora' text='nasilsin'
  (b') ikinci etiket NFD ad
      speaker='Ada'  text='merhaba Ádá: nasilsin'
```

Üçü de kararın yazdığı gibi. **CJK yüzeyinde de aynı** (kararın örnekleri
ASCII):

```
  (a-CJK)  勇者：/勇者：  -> tek segment 'こんにちは げんきですか', speaker='勇者'
  (b-CJK)  勇者：/勇者2： -> tek segment 'こんにちは 勇者2：げんきですか', speaker='勇者'
  (kontrol) 勇者：/魔王： -> IKI ayri segment
```

`test_k31a_*`, `test_k31b_*`, `test_k31_iki_farkli_TANINAN_ad_birlesmez_cjk_dahil`,
`test_k31_a_ve_b_cjk_yuzeyinde_de_ayni_davraniyor`, `test_k31b_nfd_ad_*`.

---

## 4. Yozlaşmış geometri

`w<=0`, `h<=0`, aynı `(y,x)` çiftli bloklar, tek karakterli bloklar:

- Beş yozlaşmış varyantın beşinde de gruplama **yok** ama blok **yok
  edilmiyor** — kendi segmentini üretiyor, `speaker` `None` kalıyor (K16).
- **K28'in sağ tarafı K16'yı gizlemiyor** — bunu şefin `tests/` altındaki
  testinden bağımsız olarak, kendi kurduğum uzunluk sınırıyla yeniden ürettim:

```
  aday adim 3'te hyphen ile birlesmis; BIRLESIK kutu h=25 -> gap=5 < 16 -> MIRAS (yanlis)
  HAM ilk satir h=0                   -> ref_height=0     -> 'height' -> MIRAS YOK (dogru)
  gozlenen: speakers=['Ada', None]                         <- DOGRU
  kontrol (ham ilk satir h=20): speakers=['Ada', 'Ada']    <- test totoloji degil
```

- Aynı `(y,x)` çiftli bloklarda okuma sırası **kararlı**: adım 1'in kararlı
  `(y,x)` sıralaması ile `_raw_query_pair`'in `(y,x,indeks)` sıralaması 500
  eşit-anahtarlı girdide **0 uyuşmazlık**.
- Tek karakterli bloklarda karar `w=0,h=0` ile de salt sözlüksel kalıyor
  (`力`/`a`/`1`/`?`/`？` korunur; `。`/`-` atılır).
- `_group([], params)` ve `_group([tek], params)` doğrudan çağrıları
  **kırılmıyor** (K28'in keyword-only + varsayılanlı imza seçimi tuttu).
- `_raw_query_pair`: `blocks=()` ve boş `source_blocks` → `IndexError`
  (bilinçli, gürültülü); `speaker`/`text`/`source_blocks` **aynen korunuyor**.

40–60 bloklu, negatif koordinatlı, yozlaşmış kutulu, eşik-altı bloklu 150
girdide dört ön ayarda **0 çökme, 0 K23 ihlali**.

---

## 5. Kötü kullanım yüzeyi + K28'in SOL tarafı

Ham çıktı: `r6-09-kotu-kullanim-sonda.txt`, `r6-10-etiket-blogu-sol-taraf-sonda.txt`.

- `blocks=` **geçirilmezse**: uzunluk sınırı doğduğunda `IndexError`, doğmadığında
  çalışıyor. Süzülmüş `blocks` (bir sonraki ajanın klasik hatası) da
  `IndexError` — **sessiz yanlış üretmiyor**. Kararın "gecikmeli ama gürültülü"
  takası birebir bu.
- Genel API **sızmamış**: `__all__ == ('normalize',)`, `normalize` imzası iki
  parametreli, iki yeni parametre de `_` önekli fonksiyonlarda ve
  **keyword-only + varsayılanlı**.
- `apply_inheritance=False` docstring'de "SADECE K23 … MAKINE DENETIMI …
  DISARIYA … SIZMAZ" ile işaretli ve davranışsal olarak da yalnız `speaker`'ı
  değiştiriyor (`source_blocks`/`text`/`bbox` birebir aynı).
- **Şefin adlandırdığı "ek yüzey" kapandı.** Şef, `source_blocks[-1]`'in
  sırasız girdide **yalnız-etiket bloğunu** gösterebileceğini yazmıştı.
  Ölçtüm — 2985 miras sorgusunda:

```
  SOL taraf yalniz-etiket blogu    : 0
  SAG taraf yalniz-etiket blogu    : 0
  SOL: okuma-sirasi-son != max(idx): 199   <- derlem `[-1]` uygulamasini AYIRT EDIYOR
```

  199 sayısı totolojiyi dışlıyor: derlem gerçekten `[-1]` ile okuma sırasını
  ayrıştırıyor ve okuma sırası kuralı her seferinde etiket kutusundan
  kaçınıyor. Ayrıca kurulu bir vaka (ASCII-dışı etiket + sırasız girdi +
  uzunluk sınırı) `[-1]` uygulamasının **yanlış** karar vereceğini gösteriyor:

```
  idx0 = govde (y=25, bottom=45) · idx1 = devam (y=50) · idx2 = ETIKET 勇者： (y=0)
  `[-1]` indeks-son = idx2 -> gap = 50-20 = 30 > 16 -> MIRAS YOK   (yanlis)
  okuma-sirasi-son  = idx0 -> gap = 50-45 =  5 < 16 -> MIRAS       (dogru)
  gozlenen: ['勇者', '勇者']
```

---

## 6. Ölçek — TEK BAŞINA koşuldu

Şefin O3 uyarısına uydum: ölçüm tam takım yükü altında değil, **tek başına**
yapıldı. Yeni test dosyasına **zamanlama testi eklemedim** — kararsız bir
ölçüyü çoğaltmak kapıyı gürültülendirmekten başka bir şey yapmaz.

```
A) tur 2-5 ile AYNI veri sekli   (TUR5: 3.199 / 8.429 / 24.866 ms)
   kosum 1: 2.697 / 6.951 / 20.627 ms
   kosum 2: 2.581 / 6.707 / 20.329 ms
   kosum 3: 2.533 / 6.617 / 20.477 ms

B) `_group`'u gercekten yukleyen yol (CJK)   (TUR5: 3.330 / 6.420 / 13.418 ms)
   kosum 1: 2.783 / 5.672 / 11.691 ms
   kosum 2: 2.818 / 5.703 / 11.339 ms
   kosum 3: 2.739 / 5.651 / 11.516 ms

C) K28'in EN AGIR yolu (her sinirda cok bloklu tail):
   n=500 2.190 · n=1000 4.487 · n=2000 8.936 · n=4000 18.281 ms
```

**Kötüleşme yok** — üç boyda da tur 5'in altında. C sütunu `n` iki katına
çıktığında süre de ~iki katına çıkıyor: `_raw_query_pair` sınır başına
`O(k log k)` sıralama yapmasına rağmen **kuadratik davranış yok**.

*Dürüstlük notu:* C yolunu bu turda iki kez ölçtüm (mola öncesi
1.828/3.761/7.694, şimdi 2.190/4.487/8.936). Fark makine gürültüsü; ikisi de
doğrusal ve ikisi de kanıt dosyasında. Mutlak sayı değil **oran** okunmalı.

---

## 7. Bloke etmeyen bulgular

### 7.1 K32'nin belgelediği kapsam, ölçülen olgudan DAR

**Bu turun en önemli bulgusu.** K32 şöyle diyor: *"NFD adlar (birleşik aksan)
konuşmacı SAYILMAZ"* ve *"NFC normalizasyonu T-006 ÇIKIŞ SÖZLEŞMESİNE
adaydır."* Bu ikisi birlikte okununca çıkarım şu oluyor: **motor NFC üretirse
konuşmacı ayıklama çalışır.** Ölçtüm — bu çıkarım bir yazı sistemi ailesi için
**yanlış** (`r6-11-nfc-yetmez-taramasi.txt`):

```
ad                           NFC-normal?  NFC==NFD?  NFC ile taniniyor?
devanagari राम               True         True       False
devanagari नमस्ते            True         True       False
tayca สวัสดี                 True         True       False
arapca+hareke مَرحبا         True         True       False
ibranice+nikud שָלוֹם        True         True       False
korece 용사                    True         False      True
japonca 勇者                   True         True       True
vietnamca Đức                True         False      True
```

Devanagari matra/virama, Tayca vokal işareti, Arapça hareke ve İbranice nikud
**NFC ile taşıyıcı harfe birleşmez** — bu adlar zaten NFC-normaldir
(`is_normalized("NFC") is True`, NFC == NFD) ve `isalpha()` bu `Mn`/`Mc`
işaretlerini reddettiği için etiket ayıklanmıyor, metinde kalıyor (K31/b
yolu). Aynı sınıf görünmez yön işaretleri (`U+200F`/`U+200E`, `Cf`) için de
geçerli — RTL metinde bunlar sık.

**Neden bloke etmiyor:** kod K9'un lafzına **uygun**; metin kaybolmuyor,
çökme yok, bölümleme bozulmuyor — yalnız `speaker` `None` kalıyor ve bu
davranış K31/b ile aynı **belgeli** yol. Eksik olan tek şey K32'nin **kapsam
cümlesi**. Ama şef T-006 paketine "çıktı NFC" maddesi eklemeyi planlıyor ve o
madde bu sınıfı **kapatmayacak** — kararın buna dayanmaması için yazıyorum.

**Önerilen ek (K32'ye ve `known_gaps`'e):** *"Kapsam NFD ile sınırlı değildir:
Devanagari matra/virama, Tayca vokal işaretleri, Arapça hareke, İbranice nikud
ve yön işaretleri (`U+200E`/`U+200F`) NFC altında da ayrı kod noktası olarak
kalır (`Mn`/`Mc`/`Cf`) ve `isalpha()` süzgecinden geçmez; bu adlar **NFC girdide
de** konuşmacı sayılmaz. T-006'nın NFC üretmesi bu sınıfı kapatmaz — kapatmak
K9'un ad süzgecini `Mn`/`Mc` kabul edecek şekilde genişletmeyi gerektirir ve o
ayrı bir kapı turudur."*

Davranış `test_BULGU_BLOKE_ETMEYEN_nfc_olan_indic_tayca_ve_harekeli_adlar_taninmiyor`
(5 parametre) ve `test_BULGU_BLOKE_ETMEYEN_yonelim_isaretleri_adi_dusuruyor`
(2 parametre) ile sabitlendi — **belgeleyen** testler, düzelten değil.

### 7.2 Miras `monitor_index` / `dpi_scale` sınırını aşıyor

```
  monitor 0 -> 1   UZUN metin (uzunluk siniri): speakers=['Ada', 'Ada'] bbox=[(0,1.0),(1,1.0)]
  monitor 0 -> 1   KISA metin (birlesme denenir): ValueError
  dpi 1.0 -> 2.0   UZUN metin: speakers=['Ada', 'Ada'] bbox=[(0,1.0),(0,2.0)]
  dpi 1.0 -> 2.0   KISA metin: ValueError
```

**Aynı iki blok**, metin kısaysa `ValueError` veriyor, uzunsa (reason
`"length"`) sessizce geçiyor **ve** ikinci segment birincinin `speaker`'ını
miras alıyor. Miras-uygunluk sorgusu iki farklı ekrandaki kutular arasında
`gap`/`overlap` hesaplıyor; o geometri kıyaslanabilir değil.

**Neden bloke etmiyor:** K10'un lafzı **birleşim** içindir ("iki öğe
BIRLESTIGINDE … `ValueError`") ve burada birleşim yok — segmentler kendi
`bbox`'larıyla ayrı kalıyor, sessiz bir kutu kopyalaması olmuyor. Gerçekçi
boru hattında da tek `Frame` tek monitördendir.

**Önerilen `known_gaps` maddesi:** *"Miras-uygunluk sorgusu `monitor_index`/
`dpi_scale` eşitliğini denetlemez; farklı ekrandaki iki blok arasında
yalnız-uzunluk sınırı doğarsa `speaker` ekran sınırını aşabilir. K10'un
birleşim yasağı bu yola girmez — sonuç yalnızca metin uzunluğuna bağlıdır."*

Sabitleyen test: `test_BULGU_BLOKE_ETMEYEN_miras_monitor_sinirini_asiyor`.

### 7.3 `NaN` `dpi_scale` kendi kendine eşit değil — yanıltıcı tanı

```
    ValueError: birlesecek bloklarin monitor_index/dpi_scale degerleri uyusmuyor: (0, nan) != (0, nan)
    (K7'nin confidence NaN mesaji ile karsilastir:)
      TextBlock[0].confidence gecersiz: nan (NaN olamaz, [0.0, 1.0] araliginda olmali)
```

`Rect.dpi_scale`, K7'nin `confidence` için yaptığı gibi bir ön denetimden
geçmiyor. **Aynı** `NaN` değerini taşıyan iki blok birleşemiyor ve mesaj iki
tarafı da `nan` yazarak kendi içinde çelişkili görünüyor.

**Neden bloke etmiyor:** sonuç sessiz değil (patlıyor) ve K10'un lafzını
ihlal etmiyor; yalnızca tanı kalitesi düşük. `math.isnan` ile bir ön denetim
(K7'nin deseni) bunu düzeltirdi. Sabitleyen test:
`test_BULGU_BLOKE_ETMEYEN_nan_dpi_scale_kendi_kendine_esit_degil`.

*Not:* `1` vs `1.0` ve `-0.0` vs `0.0` doğru şekilde **eşit** sayılıyor
(`!=` kullanılmış, `is`/`repr` değil) — ayrı bir testle pinlendi.

### 7.4 ZWJ / emoji kod noktası şişmesi — K32'nin ikinci yüzeyi

```
    tekrar= 20  ZWJ(cp=100): 2 segment  |  ASCII(cp= 20, AYNI grapheme): 1 segment
    tekrar= 45  ZWJ(cp=225): 2 segment  |  ASCII(cp= 45, AYNI grapheme): 1 segment
```

`max_group_chars` `len()` ile ölçülüyor ve `len()` **kod noktası** sayıyor,
grapheme değil. Aynı sayıda görünür karakter içeren iki gövde, biri ZWJ
dizilerinden kurulunca farklı bölümleniyor. K32 mekanizmayı doğru anlatıyor
("codepoint sayar") ama örnekleri yalnız NFC/NFD; emoji yüzeyi anılmıyor.

**Önerilen ek (K32'ye, tek cümle):** *"Aynı mekanizma NFD dışında da işler:
ZWJ/bayrak/varyasyon dizileri grapheme başına 2–5 kod noktası taşır ve
`max_group_chars`'ı aynı oranda şişirir."*

Sabitleyen test: `test_m14_zwj_dizisi_codepoint_sayisi_max_group_chars_i_sisiriyor`.

---

## 8. Testlerimin dişli olduğunun kanıtı

Yeni 143 testin totoloji olmadığını `src/` hiç değiştirmeden, modül
globallerini monkeypatch ile mutasyona uğratarak ölçtüm
(`r6-13-mutasyon-denetimi.txt`):

```
TABAN (mutasyonsuz):                        exit=0  143 passed

  MC1 indeks sirasi (M4 sinifi)             exit=1  KIRILDI   2 failed
  MC2 ham ikame YOK (K28 oncesi)            exit=1  KIRILDI   3 failed
  MC3 sag taraf `nxt` kalir (M5)            exit=1  KIRILDI   1 failed
  MC4 ikame monitor_index==0'a kapili       exit=1  KIRILDI   6 failed
  MC5 ikame dpi_scale==1.0'a kapili         exit=1  KIRILDI   8 failed
  MC6 gorunum gecisi TERS yon (M11)         exit=1  KIRILDI   5 failed
  MC7 ad suzgeci ASCII'ye kapili            exit=1  KIRILDI  12 failed
```

**Kendi hatam, kayda geçer:** MC4 ve MC5 ilk sürümde **geçiyordu** (dişsiz).
Sebep: derlemim hyphen zinciri üretmiyordu, dolayısıyla her öğenin
`source_blocks`'u tek elemanlıydı ve `_raw_query_pair`'in ham ikamesi **no-op**
oluyordu — ikameyi bir koşula kapılayan mutant hiçbir şeyi değiştirmiyordu.
Derleme 2–4 bloklu, yükseklikleri kasıtlı farklı hyphen zincirleri ekleyip
kalibre ettim (ayırt ediciliği ayrıca ölçtüm), sonra ikisi de kırıldı. Bu, tam
olarak şefin §4.6/4'te tarif ettiği hata sınıfı: **ölçü, mekanizmanın
değişmezden ayrıştığı girdiyi içermiyordu.**

Ayrıca `test_k28_miras_sorgusunun_hicbir_tarafi_yalniz_etiket_blogu_olmuyor`
kendi totolojik olmadığını **test içinde** assert ediyor (`ayrisma > 0`).

---

## 9. Bes sınıfın kesişimindeki değişmez fuzz'ı

1600 koşum (400 girdi × 4 ön ayar), her girdide beş sınıf birlikte
(emoji/ZWJ/astral + `monitor_index ≠ 0` + `dpi_scale ≠ 1.0` + ≥40 blok +
ASCII-dışı etiket + yalnız-etiket + sırasız + eşik-altı + yozlaşmış kutu):

```
  D1 cokme                  0 ihlal
  D2 K8 (artan/ayrik/aralik) 0 ihlal
  D3 K3 (cikti sirasi)       0 ihlal
  D4 K23 (miras acik/kapali) 0 ihlal
  D5 speaker kaynak-tutarli  0 ihlal
  D6 bbox monitor/dpi        0 ihlal
  D7 bos metinli segment yok 0 ihlal
  TOPLAM IHLAL = 0
```

Aynı fuzz test dosyasında da (60 girdi × 4 ön ayar) koşuyor.

---

## 10. Karar

**ONAY.**

- K28 doğru uygulanmış: sorgunun iki tarafı da özgün bloktan, **okuma
  sırasıyla**; `source_blocks[-1]` kullanılmıyor ve bu benim derlemimde
  199 sınırda **ölçülebilir** fark yaratıyor.
- K16 K28'in sağ tarafında gizlenmiyor; K23 beş sınıfın kesişiminde de tutuyor.
- K30/K31/K32 belgelenen davranışlar birebir yeniden üretildi (K31 CJK
  yüzeyinde de).
- Kötü kullanım yüzeyi kapalı: genel API sızmamış, `blocks=` hatası gürültülü.
- Ölçek kötüleşmedi.
- Kör takımda **onuncu bir kırık yok** — gerçek regresyon bulamadım.

Dört bloke etmeyen bulgunun tamamı belgeleme/kapsam kalemidir; hiçbiri kodun
K1–K32'den sapması değildir. **7.1 numaralı bulgu bir sonraki tur kararına
girmeli** — çünkü şefin T-006 için planladığı "çıktı NFC" maddesi, o bulgu
düzeltilmezse kapatmadığı bir sınıfı kapattığı varsayılarak yazılacak.
