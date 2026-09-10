---
task: T-004
role: tester
round: 5
decision: onay
checks:
  - name: "mypy --strict temiz (resmi kabul komutu)"
    cmd: "python -m mypy --strict src/ocr/normalizer.py src/ocr/presets.py"
    exit_code: 0
    result: gecti
    evidence: tester_C_evidence/r5-mypy.txt
  - name: "pytest resmi kabul suiti (98 test -- tur 4'te 72'ydi, TUR 5'te K23-K27 testleriyle buyudu)"
    cmd: "python -m pytest tests/unit/ocr/test_normalizer.py -q"
    exit_code: 0
    result: gecti
    evidence: tester_C_evidence/r5-pytest.txt
  - name: "purity_check.py (saflik + surecler-arasi determinizm) -- DIKKAT: harness TUR 5 ORTASINDA degisti, YENI K29 kontrolu (sef_karari-tur6.md) 1 IHLAL bildiriyor; ayrinti verdict govdesi S5.3"
    cmd: "python .agents/tasks/T-004/purity_check.py"
    exit_code: 1
    result: kaldi
    evidence: tester_C_evidence/r5-purity_check.txt
  - name: "K29 ihlalinin BAGIMSIZ dogrulamasi (iddia DOGRU: normalizer.py:92 bayat test atfi) + harness degisiklik zamani"
    cmd: "grep -n test_k2_esik_alti src/ocr/normalizer.py tests/unit/ocr/test_normalizer.py"
    exit_code: 0
    result: gecti
    evidence: tester_C_evidence/r5-purity_check-K29-dogrulama.txt
  - name: "Tester-C kendi saldiri suiti TUR 5 (125 test: 82 korunan/guncellenen tur 1-4 testi + 43 yeni TUR 5 testi) -- TAMAMEN YESIL"
    cmd: "python -m pytest .agents/tasks/T-004/tester_C -q"
    exit_code: 0
    result: gecti
    evidence: tester_C_evidence/r5-tester_c_pytest.txt
  - name: "Ayni suit -v (hangi testin gectigi tek tek gorulebilsin)"
    cmd: "python -m pytest .agents/tasks/T-004/tester_C -v"
    exit_code: 0
    result: gecti
    evidence: tester_C_evidence/r5-tester_c_pytest_verbose.txt
  - name: "B1'in JAPONCA yuzeyi -- kendi 勇者： etiketli YENI replik AYRI kaliyor mu (cap GERCEKTEN asiliyor) + uc konusmaculu zincir + menu"
    cmd: "python .agents/tasks/T-004/tester_C_evidence/r5-b1-japonca-repro.py"
    exit_code: 0
    result: gecti
    evidence: tester_C_evidence/r5-b1-japonca-repro-output.txt
  - name: "Gorunum gecisinin CJK yuzeyi -- speaker Unicode BIREBIRLIGI (halfwidth katakana/fullwidth latin dahil), bosluk artigi, karisik script, _normalize_impl sizinti taramasi"
    cmd: "python .agents/tasks/T-004/tester_C_evidence/r5-cjk-speaker-unicode.py"
    exit_code: 0
    result: gecti
    evidence: tester_C_evidence/r5-cjk-speaker-unicode-output.txt
  - name: "K24 tail-vs-birlesik-bbox ayrismasi (CJK) + K26 decomposition etiket dagilimi + K23 fuzz (Tester-C tohumu 20250910, 2600 girdi, 0 ihlal)"
    cmd: "python .agents/tasks/T-004/tester_C_evidence/r5-k24-k26-fuzz.py"
    exit_code: 0
    result: gecti
    evidence: tester_C_evidence/r5-k24-k26-fuzz-output.txt
  - name: "MUTASYON DENETIMI -- TUR 5 testlerim TUR 4'un HATALI _group'unda GERCEKTEN kiriliyor mu (src/ degistirilmeden, monkeypatch)"
    cmd: "python .agents/tasks/T-004/tester_C_evidence/r5-mutation-check.py"
    exit_code: 0
    result: gecti
    evidence: tester_C_evidence/r5-mutation-check.txt
  - name: "Olcek n=500/1000/2000 -- TUR 2/3/4 ile AYNI yontem, TUR 4 tabaniyla (2.744/7.032/20.138 ms) karsilastirma + CJK gruplama yolu"
    cmd: "gomulu olcum scripti -- bkz. tester_C_evidence/r5-scale_timing.txt"
    exit_code: 0
    result: gecti
    evidence: tester_C_evidence/r5-scale_timing.txt
  - name: "Olcum GURULTUSU -- ayni olcum 6 kez (TUR 4 tabaniyla farkin makine gurultusu oldugunun ayirt edilmesi)"
    cmd: "gomulu olcum scripti -- bkz. tester_C_evidence/r5-scale_noise.txt"
    exit_code: 0
    result: gecti
    evidence: tester_C_evidence/r5-scale_noise.txt
blocking_issues: []
---

# Tester-C değerlendirmesi — T-004, TUR 5 (Mercek: sınır, kötü kullanım ve dil)

**Karar: ONAY.** K23–K27'nin beşi de bağımsız doğrulamamda kodda var ve
merceğimin baktığı yerlerde doğru çalışıyor. En önemlisi: **B1'in Japonca
yüzeyi gerçekten düzelmiş** — `勇者：` etiketli, uzunluk sınırını aşan bir
repliğin ardından kendi `勇者：` etiketiyle gelen yeni replik **ayrı bir
`Segment` olarak kalıyor**, ve bölümleme miras açık/kapalı **birebir aynı**.

Kendi suitim **125 test, tamamen yeşil** — tur 1–4'ten korunan 82 test +
tur 5'e özgü 43 yeni test.

**Kabul komutları:** `mypy --strict` temiz, resmî suit 98/98, kendi suitim
125/125. **`purity_check.py` çıkış 1 veriyor** — ama koşumumun *ortasında*
başka bir ajan harness'ı değiştirdi ve **K29** diye yeni bir kontrol ekledi
(kaynak `sef_karari-tur6.md`, yani benim tur 5 görevimden *sonraki* bir tur).
İhlali kendim doğruladım — **gerçek**, ama bir docstring *atıf* hatası, davranış
değil. Ayrıntı ve gerekçe **§5.3**; bloke edici saymıyorum.

**Üç bloke etmeyen gözlem** kayda geçiyor (§5) — üçü de şefin kendi
kararlarının *lafzına* uygun, ama biri şefin B1 için yazdığı **ürün etkisi
cümlesinin** K23'ten sonra da başka bir yoldan üretilebildiğini gösteriyor.

> **Bir önceki turumun devamıyım.** Devraldığım dosyada `tester_C/`
> docstring'i "yeni bölüm 16" ve "**YENİ BLOKE EDİCİ BULGU (C1)**" vaat
> ediyordu ama **bölüm 16 dosyada yoktu** (dosya bölüm 15'te bitiyordu) ve
> C1 için ne test ne kanıt vardı. Bölüm 16'yı yazdım, C1 iddiasını kendim
> yeniden ürettim ve **bloke edici saymadım** — gerekçe §5.1'de. Docstring'in
> yanlış vaadini düzelttim.

## 1. B1 Japonca'da düzeldi mi? — **Evet, kesin olarak**

Merceğimin birinci sorusu: *`勇者：` etiketli, uzunluk sınırını aşan replik +
hemen ardından **yeni** `勇者：` etiketli replik → iki ayrı sözce mi?*

`dialogue` için `max_group_chars=280`. Japonca'da karakter başına anlam
yoğunluğu yüksek olduğu için ilk denememde (5×31 karakter) **cap hiç
aşılmıyordu** — senaryo kurulmamış oluyordu. 10 bloklu gövdeyle (~310
karakter) cap'i gerçekten aştırdım:

```
b0  '勇者：'                              (yalnız etiket)
b1..b10  31 karakterlik JP gövde blokları  (sıkı aralıklı, y adımı 22)
b11 '勇者：これは全く新しい台詞です。'      (KENDİ etiketiyle YENİ replik)

miras ACIK   -> speaker='勇者' src=(0..8) | speaker='勇者' src=(9,10) | speaker='勇者' src=(11,)
miras KAPALI -> speaker='勇者' src=(0..8) | speaker=None   src=(9,10) | speaker='勇者' src=(11,)
                                                                        ^^^^^^^^^^^^^^^^^^^^^^
K23 bölümleme (src+text+bbox+placeholders+sayı) BİREBİR AYNI: True
```

b11 **ayrı kaldı** (`src=(11,)`). Mekanizma doğru: b10'un *özgün* speaker'ı
`None`, b11'in kendi etiketi `勇者` → K15 satırı `None/Y → hayır`. Tur 4'te
b10 mirasla `勇者`'ya **mutasyona uğruyor** ve satır `X/X → evet`e dönüşüyordu.

**Bunu mutasyon denetimiyle kanıtladım** (`r5-mutation-check.txt`): `src/`'ye
hiç dokunmadan, tur 4'ün hatalı `_group`'unu monkeypatch ile kurdum ve
**kendi testlerimi** o kodun üzerinde çalıştırdım:

| | mevcut kod (tur 5) | mutant (tur 4 mekanizması) |
|---|---|---|
| B1/JP: son segment `src` | `(11,)` ✔ | `(9,10,11)` ✘ **yapıştı** |
| K23 bölümleme birebir mi | `True` | `False` |
| B1 testim | GEÇTİ | **KIRILDI** |
| K23 fuzz testim | GEÇTİ | **KIRILDI (48/2600 ihlal)** |

Yani testlerim **totoloji değil**: bilinen hatayı gerçekten yakalıyorlar.

**Ek senaryolar (hepsi doğru):**
- Son blok **etiketsiz** → kuyruk `勇者`'yı **miras alır**, bölümleme yine birebir aynı.
- Son blok **`魔王：`** → miras yok, `src=(11,)`, metinler karışmıyor.
- **Üç konuşmacılı zincir** (`勇者`/`魔王`/`村人`), her biri çok satırlı **ve
  her birinin gövdesi cap'i aşıyor** → 6 segment: `勇者,勇者,魔王,魔王,村人,村人`.
  Her konuşmacının içinde miras zincirleniyor, konuşmacılar arası sınır
  **hiç** geçilmiyor, atfedilemez (`None`) segment kalmıyor. Miras kapalıyken
  aynı 6 segment ama üç kuyruk `None` — bölümleme birebir aynı.
- Kısa repliklerle aynı zincir → 3 segment, `src=(0,1,2)/(3,4,5)/(6,7,8)`,
  metin sızıntısı yok.

## 2. `speaker` Unicode **birebir** mi? — **Evet, codepoint düzeyinde**

Merceğimin ikinci sorusu: görünüm geçişi `speaker` alanına özgün string'i mi
kopyalıyor, normalize edilmiş bir kopyasını mı? Bu modülde **NFKC gerçekten
kullanılıyor** (K18'in tek-karakter istisnası) — yani sızma riski teorik değil.

On isim/ayraç kombinasyonunu codepoint düzeyinde sınadım. Kritik iki vaka,
NFKC formu **kendisinden farklı** olanlar:

| girdi | `speaker` | codepoint | NFKC olsaydı |
|---|---|---|---|
| `ｱｲｳ:` (halfwidth katakana) | `ｱｲｳ` | `ff71 ff72 ff73` ✔ | `アイウ` |
| `ＡＢＣ:` (fullwidth latin) | `ＡＢＣ` | `ff21 ff22 ff23` ✔ | `ABC` |

İkisi de **birebir korunuyor** → görünüm geçişi ve `_split_speaker_label`
NFKC uygulamıyor. Kanji (`勇者`), hiragana (`あい`), hangul (`김철수`,
`이영희`), Kiril (`Пётр`), Türkçe (`Ayşe`), precomposed aksanlı Latin
(`María`) — hepsi birebir. **Miras yoluyla** gelen değer de birebir
(`test_k23_MIRAS_ALINAN_speaker_de_UNICODE_BIREBIR`).

**Boşluk artığı / karakter kaybı yok.** Fullwidth `：` ile ayrılmış etikette
altı biçim sınandım — `勇者：`, `勇者 ：`, ` 勇者： `, `勇者　：`, `勇者：　`
(U+3000 IDEOGRAPHIC SPACE, CJK metinlerinde sık) — hepsinde `speaker='勇者'`,
artık boşluk yok, ayraç karakteri `speaker`'a sızmıyor. `勇 者：` → `勇 者`:
**iç** boşluk korunuyor (K9 bunu açıkça izinli sayıyor, doğru).

**Karışık script zinciri** (4 kombinasyon: JP etiket + Latin gövde; KR etiket
+ JP gövde; Latin etiket + fullwidth ayraç + karışık gövde; JP etiket +
Kiril/JP gövde) — hepsinde tek segment, doğru konuşmacı, gövde metni birebir,
bölümleme K23'e uygun. Karışık script + uzunluk bölünmesi birlikte de
çalışıyor (JP etiket, Latin gövde, cap aşılıyor → kuyruk `勇者`'yı miras alıyor).

## 3. Kötü kullanım — API sızdırmıyor, güvenli yönde bozuluyor

| Soru | Bulgu |
|---|---|
| `_normalize_impl` `__all__`'da mı? | **Hayır.** `__all__ == ("normalize",)`, tuple |
| PEP8 private mı? | Evet, `_` ile başlıyor → `import *` almaz |
| `normalize` imzası değişti mi? | **Hayır.** `(blocks, preset)`, keyword-only parametre yok; `normalize(..., apply_inheritance=False)` **`TypeError`** |
| Bayrak yanlışlıkla konumsal geçilebilir mi? | **Hayır** — keyword-only, varsayılan `True`; `_normalize_impl([], p, False)` → `TypeError` |
| "Yalnızca test/denetim için" işaretli mi? | **Evet** — docstring'de *"SADECE K23'un MAKINE DENETIMI icin vardir"*, *"DISARIYA hicbir sekilde ACMAZ"*, *"GENEL API'YE SIZMAZ"*, ve **meşru çağıran adıyla yazılı**: `tests/unit/ocr/test_normalizer.py` |
| `normalize`'ın kendi docstring'i uyarıyor mu? | Evet — bir sonraki ajanın okuyacağı yer, kancanın nerede olduğunu ve buraya sızmadığını söylüyor |
| `_group`'un iki geçişi belgeli mi? | Evet — "Bölümleme geçişi" / "Görüntü geçişi" ayrı ayrı |

**Kötü kullanımın sonucu güvenli.** Bir sonraki ajan yanlışlıkla
`apply_inheritance=False` ile çağırsa ne olur? Kayıp **yalnızca `speaker`
alanında**: bazı segmentler `None` kalır; `text`/`bbox`/`source_blocks`/
`placeholders`/segment sayısı **değişmez**. Yani sessizce **yanlış** değil,
**daha az bilgi taşıyan ama doğru** bir sonuç — API bu yönde bozuluyor.

**K24 `tail` alanı** (CJK gövdede, `_group_rejection_reason` düzeyinde):

```
grubun BAŞINDAKİ öge çok aşağı uzanıyor (h=400) -> birleşik bottom=400
kuyruk (birleşime en son katılan HAM öge) bottom=30, aday y=200

reason(birleşik, aday)                     -> 'length'
reason(birleşik, aday, ignore_length=True) -> None    <- YANLIŞ (tur 4): kopuş GÖRÜNMEZ
reason(kuyruk,   aday, ignore_length=True) -> 'gap'   <- DOĞRU (K24): kopuş GÖRÜLÜR
```

İki sorgu **zıt** sonuç veriyor; kod `tail` kullanıyor. `tail` **her zaman
tanımlı**: boş liste → `[]`, tek ögeli grup → dönüş `items[0]`'ın kendisi,
her yeni grupta sıfırlanıyor (üç durumu da iki bayrak değeriyle sınadım).

## 4. Ölçek — kötüleşmedi

TUR 2/3/4 ile **aynı yöntem** (üst üste binen bloklar, `kelime{i}-`,
DIALOGUE, medyan-of-7):

| n | TUR 2 | TUR 3 | TUR 4 | **TUR 5** |
|---|---|---|---|---|
| 500 | 3.443 | 3.673 | 2.744 | **3.199** |
| 1000 | 9.271 | 9.234 | 7.032 | **8.429** |
| 2000 | 27.069 | 26.461 | 20.138 | **24.866** |

TUR 4 tabanına göre +17…+24%. **Bunu iki-geçişli `_group`'a atfetmiyorum**,
iki nedenle:

1. Bu veri şeklinde hyphen kuralı (K5, adım 3) **2000 bloğun hepsini tek
   ögeye indiriyor** — `normalize` 1 segment döndürüyor, yani `_group` tek
   ögeyle çağrılıyor ve iki-geçişli yapının katkısı **yapı gereği ~0**.
2. Aynı ölçümü 6 kez tekrarladım: 24.054–25.577 ms, yayılım %6.3
   (`r5-scale_noise.txt`). TUR 5 değerleri **TUR 3 tabanının altında**,
   TUR 4 tabanının üstünde — TUR 4 bu makinedeki dağılımın alt ucundan bir
   koşu.

`_group`'u **gerçekten yükleyen** ikinci bir ölçüm ekledim (CJK, hyphen'siz,
her 4. blok etiketli → miras sorgusu tetiklenir): n=500→3.330, n=1000→6.420,
n=2000→13.418 ms; 4× blok için **4.03×** süre. Kuadratik davranış yok.

## 5. Bloke etmeyen üç gözlem

### 5.1 B1'in ürün etkisi, miras hiç devreye girmeden de üretilebiliyor

Şef B1'i şu ürün etkisiyle tarif etti: *"kendi `Ada:` etiketi olan yeni bir
replik, önceki repliğin kuyruğuna yapışıyor. İki ayrı sözce tek `Segment`
oluyor."* K23 bu etkinin **miras yoluyla** oluşan biçimini kesin olarak
kapatıyor (§1). Ama **aynı ürün etkisi**, miras hiç devreye girmeden de
oluşabiliyor:

```
b0 '勇者：こんにちは、村人さん。'   (kendi etiketi -> speaker='勇者')
b1 '勇者：今日はいい天気ですね。'   (kendi etiketi -> speaker='勇者')

-> 1 segment, src=(0,1), speaker='勇者',
   text='こんにちは、村人さん。 今日はいい天気ですね。'
```

Çift `X/X` olduğu için **K15 matrisinin birinci satırı** (`X/X → EVET`)
ikisini birleştiriyor. b1'in **kendi etiketi taşıması** — yani yeni bir sözce
başlangıcının kanıtı — bu kararda hiç kullanılmıyor; utterance sınırı
yalnızca isim *farklı* olduğunda korunuyor.

**Bloke etmiyorum, üç gerekçeyle:**

1. **K23 ihlali değil.** Bölümleme miras açık/kapalı birebir aynı; miras bu
   yolda hiç çalışmıyor (birleşmeyi K15 yapıyor). Mutasyon denetiminde bu
   test mutant kodda da geçiyor — yani gerçekten mirastan bağımsız.
2. **Karar–kod sapması değil.** K15 satır 1 şefin kendi kararı, tur 2'den
   beri değişmemiş, kod onu birebir uyguluyor. Tur 2/3/4'te üç tester ve
   şefin kendi sondası bu satırı onayladı.
3. **Geçerlilik alanı dar ve çoğunlukla istenen davranış.** Kontrol
   assertion'ım: gerçek bir dikey boşluk (ayrı diyalog kutuları) varsa iki
   replik **ayrı kalıyor** (`src=(0,) / (1,)`). Yani birleşme yalnız iki
   repliğin geometrik olarak komşu olduğu durumda görülür — ki şefin kendi
   gerekçesi (*"JP/KR oyunlarında her replik **satırı** konuşmacı adıyla
   yeniden etiketlenir"*) o durumda birleşmenin **doğru** olduğunu söylüyor:
   §5.2'nin modülün varlık sebebi olarak verdiği çok satırlı replik senaryosu
   tam olarak bu.

**Kayda geçirmemin sebebi:** K23'ün değişmezi bu yolu **kapsamıyor**. Yani
B1'in ürün semptomu K23'ten sonra tamamen ortadan kalkmıyor — sadece
uydurma bir değerle oluşan biçimi kalkıyor. Şef B1'i mekanizmayla değil ürün
etkisiyle tarif ettiği için bu ayrımı açıkça yazıyorum. Karar şefin: K15
satır 1'in "b'nin kendi etiketi varsa yine de yeni sözce" diye daraltılıp
daraltılmayacağı bir **karar** sorusu, uygulama hatası değil. Davranış
`test_GOZLEM_iki_AYRI_kendi_etiketli_replik_K15_satir1_ile_BIRLESIR` ile
pin edildi (kırık kırmızı test bırakmıyorum).

### 5.2 NFD (kombine aksanlı) isimler konuşmacı olarak tanınmıyor

`_split_speaker_label` isim karakterleri için `ch.isalpha() or ch in " '-"`
şartı koyuyor. Unicode **kombine** aksan (U+0301, kategori `Mn`)
`isalpha()`'yı geçmiyor:

```
'María:'  (NFC, U+00ED)          -> speaker='María', text='body line one.'
'María:'  (NFD, 'i'+U+0301)      -> speaker=None,   text='María: body line one.'
```

Aynı isim, aynı görüntü, iki farklı sonuç. OCR motorlarının hangi
normalizasyon biçimini ürettiği **motora bağlıdır**.

**Bloke etmiyorum:** K9'un lafzı ("kalan karakterler yalnız
harf/boşluk/kesme/tire") birebir uygulanmış, sapma yok; kayıp güvenli yönde
(sessiz **uydurma** değil, sessiz **kayıp** — ve etiket metinde kaldığı için
bilgi tamamen yok olmuyor).

**Önerim (şefe):** bu daraltma `normalizer.py` K9 bölümünde **belgelensin** —
K5'te Unicode tire varyantları için açıkça yapıldığı gibi bir "kapsam dışı"
notu. Alternatif olarak isim karakteri testi `unicodedata.category(ch)[0] in
("L","M")` ile genişletilebilir; bu bir **karar** olduğu için şefe bırakıyorum.
Davranış `test_GOZLEM_k9_KOMBINE_AKSANLI_isim_konusmaci_SAYILMAZ` ile pin edildi.

### 5.3 `purity_check.py` koşumumun ortasında değişti — yeni K29 gate'i 1 ihlal buluyor

**Kronoloji (dosya zaman damgalarıyla):** dört kabul komutunu **05:27**'de
koştum, dördü de temizdi (`purity_check` dâhil, çıkış 0). **05:29:30**'da
`purity_check.py` başka bir ajan tarafından değiştirildi ve **K29** diye yeni
bir kontrol eklendi — *"docstring'lerde anılan her `test_*` adı test dosyasında
gerçekten var olmalı"*. Kaynağı `sef_karari-tur6.md`, yani **benim tur 5
görevimden sonraki** bir tur. Komutu yeniden koştuğumda:

```
IHLAL (1):
  normalizer.py:1  docstring HAYALI test aniyor (AD) -> test_k2_esik_alti_blok_ortada
                   [K29: test_normalizer.py'de yok]
exit=1
```

**İddiayı kendim doğruladım — gerçek** (`r5-purity_check-K29-dogrulama.txt`):

```
normalizer.py:92  (bkz. `...::test_k2_esik_alti_blok_ortada`)   <- anılan ad
test_normalizer.py:93  def test_k2_esik_alti_orta_blok_komsulari_birlestirir()   <- gerçek ad
```

Atıf bayat: o **adla** bir test yok. Davranış etkisi yok.

**Bloke edici saymıyorum, üç gerekçeyle:**

1. **Gate, denetlediğim teslimden sonra yaratıldı.** K29 benim görev
   listemdeki kararlar (K23–K27) arasında değil. Tur 5 teslimini tur 6'nın
   gate'iyle yargılamak, `env.md`'nin *"Şefin notu — tur 1 harness hatası"*
   bölümünde zaten kayda geçmiş durumun aynısı: harness'taki değişiklik
   implementer'ın kodunun kusuru değildir.
2. **Sınıfı dokümantasyon.** Bu, K20/K22/K26 ile **aynı** sınıf bir olgusal
   atıf hatası — şef üç kez bu sınıfı "salt dokümantasyon, davranış değişmedi"
   diye ele aldı. Tek satırlık bir ad düzeltmesiyle giderilir.
3. **Merceğimin dışında.** Sınır/kötü kullanım/dil merceği docstring atıf
   tutarlılığına bakmaz; bayat docstring atıfları karar-uyumu merceğinin işi.

**Kaydı dürüst tutuyorum:** eski harness sürümü git'te yok (dizin untracked),
bu yüzden **05:27'deki temiz koşumun kanıt dosyası kurtarılamıyor** —
`r5-purity_check.txt` şu an **başarısız** ham çıktıyı tutuyor, ve verdict ön
bilgisinde o kontrol `exit_code: 1 / result: kaldi` olarak duruyor. Ajanın
sözü delil değildir; temiz koşumu iddia etmiyorum, yalnızca şu an
ölçülebileni raporluyorum.

## 6. Regresyon — bulunmadı

Tur 1–4'ten **82 test değiştirilmeden yeniden koşuldu**, hepsi yeşil:

- **K4 sınıf tabanlı tek karakter** — 11 yazı sistemi (kanji `力`/`火`/`東`,
  hangul, hiragana, Kiril, Devanagari, Arapça, İbranice, Yunanca, Tayca,
  Gürcüce, Ermenice), fullwidth rakam, `menu`'de tek kanjilik blok
- **Karışık script / RTL / emoji-ZWJ / kombine aksan** — çökme yok, metin korunuyor
- **K10** — farklı `monitor_index`/`dpi_scale` → `ValueError` (CJK metinde,
  hyphen birleşiminde, üç bloklu zincirde üçüncüde)
- **K16** — `h==0` / negatif `h` / `w==0` koşulsuz red; `_should_group` doğrudan
- **K15 matrisinin beş satırı** — hem `_should_group` düzeyinde hem uçtan uca
- **K17** — ayraç kümesi, metin ortasındaki ayraç, diğer CJK ayraç
  varyantlarının kapsam dışı kalması, fullwidth rakamlı saat metni
- **K18/K20** — NFKC istisnası, tam Unicode taraması (0x0–0x10FFFF), altı
  karakterin listesi **tam olarak** eşleşiyor (ne eksik ne fazla)
- **K19/K21** — üç+ parçaya bölünen gövdede her kuyruk, zincir kopması,
  Japonca'da bölünmenin **her zaman blok sınırında** olması, bileşik sınırda
  (uzunluk + geometri **aynı anda**) mirasın **olmaması**
- **`presets.py` genişletilebilirliği** — dört ön ayar aynı dataclass türünü
  kullanıyor, yeni alan eklemek mevcut örnekleri bozmuyor, bilinmeyen preset
  `ValueError`
- **Takma ad / determinizm** — girdi listesi yan etkiyle değişmiyor, aynı
  girdiyle iki çağrı bit-bit aynı, önbellek yok

**K26 bağımsız doğrulama:** `unicodedata.decomposition` ile altı karakterin
**altısı da** uyumluluk formu; etiket dağılımı **2×`<wide>`, 2×`<small>`,
2×`<vertical>`** — K26'nın tablosuyla birebir. `unidata_version == 15.0.0`
testte sabitlendi, sürüm değişirse test kırılıp listeyi yeniden doğrulatacak.

**K27 dört ön ayar:** aynı JP fixture (etiket + sıkı gövde1 + etiketsiz
gövde2) dört ön ayarla koşuldu — `dialogue`/`tooltip`/`subtitle` tek segment
(`src=(0,1,2)`, `speaker='勇者'`); `menu` iki segment, ikincisi
`src=(2,)`/`speaker=None`. K27'nin tarif ettiği kapsam dışı birebir gözlendi
ve K23 değişmezi dördünde de tutuyor.

**K23 kendi fuzz'ım:** tohum 20250910 (implementer'ınkinden farklı), CJK/KR
ağırlıklı metin, dört yazı sisteminden isim, yozlaşmış geometri (sıfır/negatif
`w`/`h`), y adımları 1–900 arası sıçramalarla, dört ön ayar, **2600 girdi →
0 ihlal**. Üreticinin duyarlılığı ölçüldü: ilk hali mutant kodda **sıfır**
ihlal buluyordu (yanlış güvence!) — B1 desenini kasıtlı kuran "sahne" modu
eklenerek **48/2600**'e çıkarıldı.

## Özet

| Soru | Cevap |
|---|---|
| B1 Japonca'da düzeldi mi? | **Evet** — kendi `勇者：` etiketli yeni replik `src=(11,)` olarak ayrı kalıyor; mutant kodda `(9,10,11)` oluyordu |
| Üç konuşmacılı zincir (cap aşan, çok satırlı)? | **Doğru** — 6 segment, miras her konuşmacı içinde zincirleniyor, konuşmacı sınırı hiç geçilmiyor |
| `speaker` Unicode birebir mi? | **Evet, codepoint düzeyinde** — halfwidth katakana ve fullwidth latin dahil NFKC uygulanmıyor; U+3000 dahil boşluk artığı yok |
| K23 değişmezi tutuyor mu? | **Evet** — kendi fuzz'ımda 2600 girdi / 0 ihlal; mutant kodda 48 ihlal (test totoloji değil) |
| K24 `tail` gerçekten kullanılıyor mu? | **Evet** — CJK gövdede iki sorgu zıt sonuç veriyor, kod `tail` alıyor; `tail` her zaman tanımlı |
| `_normalize_impl` sızmış mı? | **Hayır** — `__all__` temiz, `normalize` imzası değişmemiş, bayrak keyword-only, "yalnızca denetim için" işaretli |
| Ölçek kötüleşti mi? | **Hayır** — TUR 3'ün altında; TUR 4 farkı ölçüm gürültüsü (yayılım %6.3) ve o veri şeklinde `_group` zaten tek ögeyle çağrılıyor |
| Regresyon var mı? | **Hayır** — 82 tur 1–4 testi + 98 testlik resmî suit temiz |
| Kabul komutları | `mypy` ✔ · resmî suit 98/98 ✔ · kendi suitim 125/125 ✔ · `purity_check` **çıkış 1** (tur 6'nın K29 gate'i, koşumumun ortasında eklendi — §5.3) |
| Bloke edici bulgu? | **Yok.** Üç bloke etmeyen gözlem (§5.1 K15 satır-1 utterance sınırı, §5.2 NFD isimler, §5.3 K29 bayat docstring atfı) |

`feedback-C.md` **tur 3 tarihlidir ve güncellenmemiştir** — tur 5 kararı
onaydır, PROTOKOL §4 gereği feedback yalnızca ret hâlinde yazılır. §5'teki iki
gözlem şefin kararına bırakılmıştır.
