---
task: T-004
role: tester
round: 5
decision: ret
checks:
  - name: "mypy --strict temiz (kabul komutu)"
    cmd: "python -m mypy --strict src/ocr/normalizer.py src/ocr/presets.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r5-mypy.txt
  - name: "implementer pytest paketi (kabul komutu, 98 test)"
    cmd: "python -m pytest tests/unit/ocr/test_normalizer.py -q"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r5-pytest_implementer.txt
  - name: "purity_check.py (kabul komutu)"
    cmd: "python .agents/tasks/T-004/purity_check.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r5-purity_check.txt
  - name: "tester_A bagimsiz saldiri paketi -- garanti alani (134 gecti, 4 xfail(strict) = BULGU R5-1)"
    cmd: "python -m pytest .agents/tasks/T-004/tester_A -q -rxX"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r5-pytest_tester_A.txt
  - name: "K23 bolumleme degismezi -- KENDI hyphen-yogun ureticimle, 3200 girdi x 4 on ayar, 0 fark"
    cmd: "python .agents/tasks/T-004/tester_A/sonda_r5_bulgu.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r5-bulgu-R5-1-sonda.txt
  - name: "BULGU R5-1: hyphen-birlesik `tail` K24 artifaktini geri getiriyor (uc geometrik yol + makine denetimi)"
    cmd: "python .agents/tasks/T-004/tester_A/sonda_r5_bulgu.py"
    exit_code: 0
    result: kaldi
    evidence: tester_A_evidence/r5-bulgu-R5-1-sonda.txt
  - name: "BULGU R5-1 ham assertion cikitisi (xfail maskesi kapali)"
    cmd: "python -m pytest .agents/tasks/T-004/tester_A -q --runxfail -k 'makine_denetimi or kuyruk_gercek'"
    exit_code: 1
    result: kaldi
    evidence: tester_A_evidence/r5-bulgu-R5-1-runxfail.txt
blocking_issues:
  - id: R5-1
    severity: yuksek
    karar: "K24 (+ K19 tablosu)"
    ozet: >-
      `tail` her zaman "grubun okuma sirasindaki SON HAM ogesi" DEGIL: adim 3
      (`_merge_hyphenated`, K5) COK BLOKLU bir `_Item` uretebilir ve o oge
      grubun `tail`'i olabilir. Onun BIRLESIK bbox'i, K24'un step-5 icin
      kaldirdigi artifakti step-3 uzerinden GERI GETIRIYOR -- `speaker`
      GERCEK bir geometrik kopusun otesine atfediliyor (K19 tablosu:
      "geometrik bosluk -> `None` KALIR"). Uc bagimsiz geometrik yol; IKISI
      MONOTONIK (egzotik/non-monotonik geometri GEREKMEZ). Olcum: 3200 girdi,
      30.174 uzunluk-siniri, 1561 ihlal (%5,2; 1473'u monotonik); uctan uca
      1004 segmentin `speaker`'i yanlis, 383/3200 girdi etkileniyor.
      K23 bolumleme degismezi IHLAL EDILMIYOR (bolumleme farki 0).
    repro: "python .agents/tasks/T-004/tester_A/sonda_r5_bulgu.py"
    testler: >-
      tester_A/test_r5_partition_invariant.py::test_r51_mekanizma_hyphen_birlesik_tail_ham_son_satirdan_ayrisiyor
      (YESIL, mekanizmayi sabitler) ·
      test_r51_kuyruk_gercek_geometrik_kopusun_otesine_speaker_atfetmiyor[A/B/C]
      ve test_r51_makine_denetimi_ham_son_blok_kuralinda_sifir_ayrisma
      (xfail strict=True -- kod duzelirse XPASS ile KIRILIR)
    evidence: tester_A_evidence/r5-bulgu-R5-1-sonda.txt
---

# T-004 — Tester A raporu (Mercek: **Garanti alanı**) — TUR 5

## Karar

**RET.** Bir bloke edici bulgu: **R5-1**.

Tur 5'in **ana** merceği olan **K23 bölümleme değişmezi kusursuz** — kendi
üreticimle 3200 girdi × 4 ön ayar (12.800 koşum) ve önceki ajanın 2520
girdilik derlemiyle **tek bir bölümleme farkı yok**, ve miras gerçekten
tetikleniyor (8117 segmentin `speaker`'ı değişiyor), yani denetim totoloji
değil. İki-geçişli yapı değişmezi **yapı gereği** sağlıyor.

Ret, K23'ten değil **K24'ten** geliyor: K24'ün *"sol taraf grubun okuma
sırasındaki son kaynak öğesidir — birleşik bbox değil"* kuralı **step-5 için**
uygulandı, ama **step-3'ün** ürettiği birleşik bbox için uygulanmadı. Aynı
artifakt, aynı sonuç, farklı kapıdan.

## Yöntem

Kör çalıştım. Okuduklarım: `env.md` (TUR 5 + MERCEK A), `sef_karari-tur5.md`
(K23–K27), `sef_karari-tur4.md`, `sef_karari-tur3.md`, `sef_karari-tur2.md`,
`packet.md` (K1–K14), `PROTOKOL.md` §1–§4.5, `src/ocr/normalizer.py`,
`src/ocr/presets.py`, `src/contracts/models.py`,
`tests/unit/ocr/test_normalizer.py`, ve bu rolde bir önceki ajanın bıraktığı
`tester_A/test_r5_partition_invariant.py` + `tester_A/test_warranty_domain.py`
+ kendi tur 2 raporum (`verdict-A.md`), `feedback-A.md`.
**Okumadım:** `delivery.md`, `evidence/`, `iptal-tur0/`, `tester_B*`,
`tester_C*`.

Devraldığım dosyayı **kabul ettim ve genişlettim** (silmedim):

| Ne | Nasıl |
|---|---|
| Üretici seti | 5 → **6**; kendi dağılımımı (`_gen_hyphen_dense`) ekledim: blokların ~%35'i tire ile biter, devam satırları `h∈{3,5,8}` veya yatay kaydırılmış. Bu dağıtım önceki sette **yoktu** ve bulguyu ortaya çıkaran dağılımdır |
| Derlem boyutu | 1200 → **2520** ayrı girdi (şefin ≥2000 tabanı artık makineyle sabitli: `test_derlem_sefin_2000_girdi_tabanini_asiyor`) |
| Önceki `xfail` | `strict=False` → **`strict=True`**, ve tek elle kurulmuş noktadan **üç geometrik yol + bir makine denetimine** çıkarıldı |
| Bayrağın alanı | K15'in **grup içi** yayılımının bayrakla kapanmadığını sabitleyen yeni test |

Ayrıca `pytest` dışı, elle koşulabilir bir sonda yazdım:
`tester_A/sonda_r5_bulgu.py` — şefin kendi eliyle yeniden üretmesi için.
`src/` ve `tests/` altına hiçbir şey yazmadım.

---

## 1 · K23 bölümleme değişmezi — **geçti**

Implementer'ın 2500 girdilik denetimine güvenmedim; **kendi** üreticimle
sınadım (farklı tohum **ve** farklı dağılım).

| | |
|---|---|
| Kendi üreticim (hyphen-yoğun, `sonda_r5_bulgu.py`) | 3200 girdi × 4 ön ayar = **12.800 koşum** |
| Devraldığım altı üreticili derlem (`test_k23_bolumleme_miras_acik_kapali_birebir_ayni`) | **2520** girdi × 4 ön ayar = **10.080 koşum** |
| **Bölümleme farkı (`source_blocks` dizisi + `text` + `bbox` + `placeholders` + segment sayısı)** | **0** |
| Miras gerçekten tetiklendi mi | **8117** segmentin `speaker`'ı `True`/`False` arasında değişiyor |

Kapsanan dağılımlar: 3+ konuşmacı zinciri (ASCII **ve** `勇者`/`魔王`/`村人`,
`:` ve `：` karışık), iç içe uzunluk+geometri bölünmeleri, aynı `y`'de yan
yana bloklar (sütunlar), `h ∈ {0, ±1, 2, 3, 5, 8, −5, 400}`, `w ∈ {0, 8,
−3, −4, 300}`, karışık/karıştırılmış giriş sırası, `_merge_hyphenated`'ı
yoğun tetikleyen tire dağılımı.

**Sondanın dişleri var (PROTOKOL §3 kapı 6).** "0 fark" totoloji olmasın diye
tur 4'ün mekanizmasını test dosyasında yeniden kurdum (`_group_tur4`) ve
**aynı** karşılaştırıcıyı ona uyguladım: bölümleme farkı **buluyor**
(`test_k23_karsilastiricinin_disleri_var_tur4_mekanizmasi_yakalaniyor`).
Yanlış kurulmuş bir sonda hatanın yokluğunu kanıtlamaz — bu sonda kurulmuş.

Kod tarafında değişmez **yapı gereği** sağlanıyor: `apply_inheritance`
bayrağı bölümleme geçişinin **içinde hiç okunmuyor**; görünüm geçişi yalnızca
`replace(..., speaker=...)` yapıyor ve döngü bittikten sonra çalışıyor.

## 2 · `apply_inheritance=False`'ın alanı — **geçti**, ama alanı **tam olarak** şu

Soru: "son adımı mı atlıyor, yoksa miras hiç olmasaydı üretilecek çıktıyı mı
veriyor?" Cevap: **ikisi de doğru, çünkü bu iki şey burada aynı şey** — ama
yalnızca K19/K21/K23 mirası için.

- Miras kodu **sıfır** olan bağımsız bir referans boru hattı (`_group_mirassiz`)
  ile `speaker` **dâhil** tam `Segment` eşitliği: 2520 girdi × 4 ön ayar, fark
  yok (`test_apply_inheritance_false_miras_hic_olmasaydi_ciktisiyla_birebir`).
- Tek yönlü daralma sabitlendi: kapalıyken `None` olmayan bir `speaker` açık
  haldekinden farklı **olamaz**, açıkken `None` olan bir segment kapalıyken
  dolu **olamaz**.
- **Bayrağın kapatmadığı şey:** K15'in **grup içi** `speaker` yayılımı
  (`_group`'ta `speaker=current.speaker`). Bu **doğru** — o yayılım K15
  matrisinin `X/None → evet` satırının kendisidir, yani **bölümleme
  kuralının parçası**; kapatılsa K23'ün koruması gereken bölümlemenin
  kendisi değişirdi. Yeni test:
  `test_bayragin_alani_k15_ici_grup_yayilimini_KAPATMAZ`.
- `menu`'de bayrak **hiçbir** şeyi değiştirmiyor (K27 kapsam dışı doğrulandı).

**Sızıntı yok:** `__all__ == ("normalize",)`, `from ... import *` yalnız
`normalize` getiriyor, `src.ocr` paketinde `_normalize_impl` yok,
`normalize`'ın imzası `(blocks, preset)` ve `apply_inheritance` **reddediyor**
(`TypeError`); `_normalize_impl`/`_group`'ta parametre keyword-only ve
varsayılanı `True`.

## 3 · K24 `tail` — **tanımlılık geçti, alan iddiası KALDI (BULGU R5-1)**

**Tanımlılık:** `tail` her durumda tanımlı. `items[0]` ile başlatılıyor, her
başarılı birleşimde ve her yeni grupta yeniden atanıyor; boş liste erken
dönüyor. Tek öğeli grupta `tail is current` (ayrışma yok); ilk grupta,
gruplar arka arkaya kapanırken ve yozlaşmış tek öğeli grupta `IndexError`/
`UnboundLocalError` yok. **Yapısal olgu** (40.000 çiftlik ızgarayla
sabitledim): K16 birleşmeye ancak `min(h) > 0` **ve** `min(w) > 0` iken izin
verdiği için gruba **sonradan** katılan her öğe pozitif `w`/`h` taşır —
yozlaşmış `tail` yalnızca **tek öğeli** grupta mümkündür, orada da
`tail is current`.

**`tail` ile `current` hangi geometrilerde ayrışıyor:** `speaker` kontrolü
**hiç** ayrışmaz — miras sorgusu zaten `nxt.speaker is None` koşuluna bağlı
ve o durumda `speaker` dalı her iki tarafta da reddetmez. Ayrışma **tamamen
geometrik**, ve `current` **sistematik olarak daha gevşek**: birleşik kutu
`bottom = max(bottom)` taşır (→ `gap` küçük/negatif), `h`/`w` her iki bileşenden
büyüktür (→ `min(h)`/`min(w)` eşikleri şişer), `x`/`right` daha geniştir (→
`overlap` şişer). İki yönü de sabitledim: (1) birleşik kutu kopuşu gizler,
`tail` görür → **miras yok** (K24'ün zorunlu testinin yönü); (2) birleşik kutu
`"overlap"` reddederken `tail` izin verir → **miras var**. İkinci yön K24'ün
zorunlu testinde **yoktu**; onsuz `current` kullanan bir kod da testi geçerdi.

**Ama:** `tail` docstring'in koşulsuz iddia ettiği gibi *"grubun okuma
sırasındaki SON **HAM** öğesi"* **değil.** Ayrıntı ve ölçüm için
`feedback-A.md`; özet:

```
tail (adim 3'te birlesmis oge) : src=(1, 2)  bbox=(y=0, h=35)   <- BIRLESIK
grubun HAM son metin satiri    :             bbox=(y=30, h=5)
KODUN sorgusu (tail, nxt)      : None        <- "kopus YOK" (artifakt)
K24 IFADESI   (ham son satir)  : 'gap'       <- GERCEK kopus
normalize()                    : [((0,1,2),'Ada'), ((3,),'Ada')]   <- K19 tablosu ihlali
beklenen                       : [((0,1,2),'Ada'), ((3,),None)]
```

Üç bağımsız geometrik yol var, **ikisi monotonik** (dikey uzanım okuma
sırasına tamamen uygun — "egzotik geometri" savunması kapalı):

| Yol | Mekanizma | Monotonik? |
|---|---|---|
| A | birleşik kutunun `bottom`'u (non-monotonik uzanım) | hayır |
| B | `min(h)` şişmesi — devam satırı kısa (`h=5`) | **evet** |
| C | `overlap` + `min(w)` şişmesi — devam satırı kaydırılmış/dar | **evet** |

Makine denetimi (3200 girdi, üç gruplayan ön ayar): **30.174** uzunluk
sınırının **1561'inde** (%5,2) kod miras veriyor ama K24'ün ifadesinin
birebir okunuşu (grubun okuma sırasındaki **son ham bloğu**) vermiyor;
bunların **1473'ü monotonik**. Ters yön 27. Uçtan uca **1004 segmentin**
`speaker`'ı yanlış, **383/3200 girdi** etkileniyor.

**K23 ihlal edilmiyor** — bölümleme farkı 0. Bulgu yalnızca `speaker`'ı
bozuyor; ama bozduğu şey tam olarak K19'un *"geometrik boşluğa konuşmacı
atfetmek uydurmadır"* yasağıdır ve aynı semptom tur 3→4'te şef tarafından
**bloke edici** sayılmıştı.

## 4 · Regresyon — **hepsi geçti**

`tester_A/test_warranty_domain.py` (tur 2'de kurduğum paket) tur 5'te de
koşuyor, **tamamı yeşil**:

- **K7** — tam eşik dört ön ayarda korunuyor, eşiğin hemen altı düşüyor,
  `NaN`/`inf`/alan dışı → `ValueError`, `NaN` sessizce hayatta kalmıyor, ilk
  bozuk `confidence` **orijinal** sırada raporlanıyor
- **K6** — `"%s ve %s"` tekrar/sıra, `"50%"` vs `"50%s"`, bitişik yer
  tutucular, sayılar `placeholders`'a girmiyor, blok sınırına bölünmüş yer
  tutucunun belgelenmiş bozuk davranışı
- **K5** — `well-known` korunuyor, blok-arası `keli-`/`me` birleşiyor,
  sonraki satır **büyük** harfle başlarsa tire **düşmüyor**, Unicode tire
  varyantları ASCII kuralından dışlanıyor
- **K16** — `h==0`/negatif `h`/`w==0` ızgaraları (`ref_height <= 0` ve
  `ref_width <= 0` için tam ızgara) + tohumlu yozlaşmış fuzz: **hiçbirinde**
  gruplama yok, çökme yok
- **K17/K18** — ayraç kümesi (`:`, `：`), metin ortasında ayraç, birden çok
  ayraçta en sol kazanır, ayraçla başlayan blok etiket değil, rakam/uzunluk
  koruması fullwidth'e de uzanıyor; NFKC istisnası `？`/`！`/`﹖`/`﹗`/dikey
  formlarda tutuyor, `？？`/`⁉`/`：`/`。`/`．`/`¿`/`❓` **genişletmiyor**
- **Saflık** — art arda çağrılar değer-eşit, dönen listeyi mutasyona uğratmak
  sonraki çağrıyı kirletmiyor, modül düzeyi önbellek yok

Ayrıca üç kabul komutu da temiz: `mypy --strict` **Success**, implementer
paketi **98 geçti**, `purity_check.py` **TEMIZ**.

## 5 · `tester_A/` durumu

`134 passed, 4 xfailed` — **tamamen yeşil.** Dört `xfail`'in **hepsi**
`strict=True` ve **hepsi** BULGU R5-1'dir: gerekçe bu raporun 3. bölümünde ve
`feedback-A.md`'de. `strict=True` seçtim ki kod düzeltildiğinde bu testler
**XPASS ile kırılsın** — bulgu sessizce kapatılamaz, işaretin kaldırılması
zorunlu olur. Bulgunun **mekanizması** ayrıca `xfail` olmayan yeşil bir
testle sabitlendi (`test_r51_mekanizma_...`), yani xfail'ler boşa düşse bile
sebep kayda geçmiş olur.

## 6 · Bloke etmeyen gözlemler

1. **K24'ün zorunlu testi tek yönlü.** `test_k24_kuyruk_ile_birlesik_bbox_
   farkli_sonuc_verir` yalnızca "birleşik kutu izin verir / `tail` reddeder"
   yönünü sınıyor. Ters yön (`tail` izin verir / birleşik kutu reddeder)
   sınanmadığı için `current` kullanan bir kod bile o testi geçebilirdi.
   Kendi paketimde ikinci yönü ekledim; kalıcı olması iyi olur.
2. **Zincirleme miras hiçbir testle bağlı değil.** `_group` docstring'i
   soldan sağa geçişin zincirleme mirası **kasıtlı** olarak mümkün kıldığını
   söylüyor ve "hiçbir mevcut test bunun tersini beklemiyor" diyor — ama
   **lehine** de bir test yok. Kendi paketimde dört öğeli monologda
   sabitledim (`test_k24_tail_ilk_grupta_...`); `tests/` altında da bir test
   hak ediyor, aksi halde ileride sessizce kaybolabilir.
3. **`_merge_hyphenated` hiçbir geometrik kontrol yapmıyor** (K5 salt
   tipografik). Bu belgeli ve bu turda karar konusu değil, ama R5-1'in
   **kökü** burada: birbirinden 400 px uzaktaki iki blok da, biri tire ile
   bitip diğeri küçük harfle başlıyorsa tek öğe oluyor ve o öğenin birleşik
   kutusu grup kararlarına giriyor.

---

## Doğrulama

```
python .agents/validate.py .agents/tasks/T-004/verdict-A.md
```
