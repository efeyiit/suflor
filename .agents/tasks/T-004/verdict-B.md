---
task: T-004
role: tester
round: 5
decision: onay
checks:
  - name: "mypy --strict temiz"
    cmd: "python -m mypy --strict src/ocr/normalizer.py src/ocr/presets.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r5-mypy.txt
  - name: "kabul testleri (98 test -- tur 5'te K23 fuzz + K24 + K26 + K27 eklendi)"
    cmd: "python -m pytest tests/unit/ocr/test_normalizer.py -q"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r5-pytest_existing.txt
  - name: "saflik/determinizm denetimi (surecler-arasi PYTHONHASHSEED)"
    cmd: "python .agents/tasks/T-004/purity_check.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r5-purity_check.txt
  - name: "TESTER-B karar-uyumu saldiri seti TUR 5 (117 test: 34 tur2 + 24 tur3 + 54 tur5 + 5 mutant sondasi) -- TAMAMEN YESIL"
    cmd: "python -m pytest .agents/tasks/T-004/tester_B -q"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r5-pytest_tester_B.txt
  - name: "KIRIK TESTIN TESHISI -- tur3 assertion'i K21 (tur 4) ile bayatlamis, KOD dogru: sinir hem 'length' hem GERCEK 'gap'"
    cmd: "python .agents/tasks/T-004/tester_B (teshis betigi) -- reason zinciri + tail/current sorgulari + kontrol senaryosu"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r5-kirik_test_teshisi.txt
  - name: "K23 MUTANT SONDASI -- mirasi bolumlemeye sizdiran mutant K23 denetimimi GERCEKTEN kiriyor (7/1600 ihlal + B1 VARYANT A geri geliyor); M2/M3 K24'u kirip K23'u kirmiyor"
    cmd: "python -m pytest .agents/tasks/T-004/tester_B/test_k23_mutant_sondasi_tur5.py -q"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r5-mutant_sondasi.txt
  - name: "K23 -- iki-gecisli yapinin AST ispati + kendi ureticilerimle bolumleme degismezi (3600 + 2400 + 1600 kosum, uc farkli tohum)"
    cmd: "python -m pytest .agents/tasks/T-004/tester_B -k k23 -v"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r5-k23_yapisal_ve_degismez.txt
  - name: "K24 -- miras-uygunluk sorgusu `tail` ile cagriliyor (AST satiri) + tail/current zit sonuc + uctan uca"
    cmd: "python -m pytest .agents/tasks/T-004/tester_B -k k24 -v"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r5-k24_tail.txt
  - name: "Ayrismazlik: `_should_group` hala tek satirlik devretme + 20.000 cift fuzz (yeni tohum) + `speaker` hala `length`ten once + reason kodlari tur 3-4 ile birebir"
    cmd: "python -m pytest .agents/tasks/T-004/tester_B -k 'should_group or reason_kodlari or lengthten_once' -v"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r5-ayrismazlik_ve_reason_kodlari.txt
  - name: "K25 (secenek 1 + donus tipi `str | None`) / K26 (bagimsiz tam Unicode taramasi + 2-2-2 etiket dagilimi) / K27 (dort on ayar)"
    cmd: "python -m pytest .agents/tasks/T-004/tester_B -k 'k25 or k26 or k27' -v"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r5-k25_k26_k27.txt
  - name: "K14 -- gercek test dosyasindaki butce assertion'i IMKANSIZ esikle (0.0 ms) zorlandi, GERCEKTEN kiriliyor"
    cmd: "python -m pytest .agents/tasks/T-004/tester_B -k k14 -v"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r5-pytest_k14_forced_break.txt
  - name: "K14 -- gercek butce testi tek basina (medyan << 5 ms)"
    cmd: "python -m pytest tests/unit/ocr/test_normalizer.py -k test_k14_normalizasyon_butcesi_5ms_medyan -v"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r5-k14_real_test.txt
  - name: "Docstring OFSET testleri (tur 3 yontemi) docstring BUYUDUKTEN sonra da yesil"
    cmd: "python -m pytest .agents/tasks/T-004/tester_B -k 'docstring or ofset' -v"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r5-docstring_ofset.txt
  - name: "K1-K27 uyum tablosu -- her kararin hangi dosyada kac testle sabitlendigi (182 test fonksiyonu tarandi)"
    cmd: "python (kmap betigi) -- 5 test dosyasinin AST'sinden K-etiketi cikarimi"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r5-k1_k27_uyum_tablosu.txt
  - name: "BULGU (bloke etmeyen): docstring'de ANILAN iki test adi GERCEK test dosyasinda YOK"
    cmd: "python (atif tarayici) -- modul+fonksiyon docstring'lerindeki test adlari vs. gercek test fonksiyonlari"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r5-bayat_docstring_atiflari.txt
blocking_issues: []
---

# TESTER-B verdict — T-004 — TUR 5 — Merceğim: KARAR UYUMU

**Karar: onay.** K1–K27, yirmi yedi kararın **27'si uygulanmış**, **0'ı sapmış**,
**0'ı doğrulanamadı**. Bloke edici bulgu yok. Üç bloke **etmeyen** not aşağıda.

## Körlük ve dürüstlük beyanı

Okuduklarım: `env.md` (TUR 5 + MERCEK B), `sef_karari-tur5.md`, `sef_karari-tur4.md`,
`sef_karari-tur3.md`, `sef_karari-tur2.md`, `packet.md`, `.agents/PROTOKOL.md` §4/§4.5/§4.6,
`src/ocr/normalizer.py`, `src/ocr/presets.py`, `src/contracts/models.py`,
`tests/unit/ocr/test_normalizer.py`, kendi `tester_B/` dosyalarım.

`delivery.md`, `evidence/`, `iptal-tur0/`, `tester_A*`, `tester_C*` **okunmadı** —
**bir istisna dışında:** K25'in referans verdiği satırı doğrulamak isterken tek bir
komutta yanlışlıkla `tester_C/test_cjk_misuse_scale.py`'nin **1138. satırını** (tek satır:
bir `set(...)` kurulumu) gördüm. İçeriği hiçbir bulgu/sonuç bilgisi taşımıyor ve bu
raporun hiçbir cümlesini etkilemedi; yine de kural ihlali olduğu için bildiriyorum.

## Devam görevi — bıraktığım yerden

Önceki ajan `tester_B/test_karar_uyumu_tur5.py`'yi yazdı (K23 AST ispatı, kendi
üreticileriyle değişmez denetimi, K24/K25/K26/K27, regresyon) ve son sözü *"mutant
sondası kuracağım"* idi. Bu turda: (1) kırık testi teşhis ettim, (2) mutant sondasını
kurdum, (3) K23 denetim zincirinin eksik halkasını kapattım, (4) docstring atıflarını
taradım. Set 34 → **117 test**, tamamı yeşil.

---

## 1. Kırık testin teşhisi — **bayat assertion, kod sapması DEĞİL**

Kırık test: `tester_B/test_karar_uyumu_tur3.py::test_r3_k2_esik_alti_orta_blok_uzunluk_mirasiyla_birlikte_dogru_calisir`
(eski assertion: `assert all(s.speaker == "Ada" for s in out)`).

Ham kanıt: `tester_B_evidence/r5-kirik_test_teshisi.txt`. Tek sınır var ve zinciri şu:

```
SINIR: kapanan grup src=(0,1,2,3,4)  ->  nxt src=(6,)
  reason (ANA karar, current ile)        = 'length'
  TUR 3 (K19) mekanizmasi                -> miras VAR      <- eski assertion buna dayaniyordu
  TUR 4/5 (K21+K24) sorgusu tail ile     = 'gap'  (gap=24, esik=0.8*20=16)
  (karsilastirma) ayni sorgu current ile = 'gap'  (gap=24)
  -> K21/K24 mirasi: YOK
```

Sebep zinciri: eşik-altı blok (`conf=0.05`, y=110) adım 1'de **düşüyor** — ama düştüğü
yer **2 satırlık dikey boşluk** olarak kalıyor (b4 `bottom=108`, b6 `y=132`). Yani sınır
**aynı anda** hem `length` hem **gerçek** bir geometrik kopuş. K21 (tur 4) tam olarak
bunu düzeltti: *uzunluk tek engel değilse miras yok.* Dolayısıyla:

- **Kod K19/K21/K24'e birebir uyuyor**; kuyruk segmentin `speaker=None` kalması doğru.
- Eski assertion **K21-öncesi (tur 3)** davranışı kodluyordu. Tester-B **tur 4'te
  koşmadığı** için (kanıt dizinimde `r4-` yok, `verdict-B.md` tur 3'te kalmış) bu
  bayatlama tur 4'te fark edilmedi, tur 5'te ortaya çıktı.
- **Kontrol:** aynı senaryoda gürültü bloğu komşusuyla **aynı `y`'de** olursa (düşünce
  geometrik iz bırakmaz) sınır uzunluk-tek olur ve miras **gerçekten çalışır**
  (`['Ada','Ada']`). Yani `None`, mekanizmanın bozukluğundan değil, K21'in doğru
  ayrımından geliyor.
- Bu senaryoda K23 değişmezi de sağlam: bölümleme miras açık/kapalı **birebir aynı**.

**Yaptığım:** testi düzelttim (yerinde, K25'in koruduğu 356/361/366 satırlarına
dokunmadan — onlar hâlâ aynı satırlarda ve yeşil). Yeni hâli K2'nin **asıl** iddiasını
daha sıkı sabitliyor: (a) gürültü indeksi hiçbir `source_blocks`'ta yok, (b) blok
girdiden **tamamen çıkarılmış** gibi davranıyor (metin/speaker/segment sayısı birebir),
(c) K21 gereği kuyruk `None`, (d) boşluk açmayan varyantta miras **çalışıyor**.
Docstring'inde bayatlamanın hikâyesi yazılı.

---

## 2. K1–K27 — tek tek

| Karar | Durum | Nerede sabitlendi (dosya(test sayısı)) |
|---|---|---|
| K1 satır tanımı | uygulanmış | B/tur2(2), B/tur5(1), GERÇEK(2) |
| K2 işlem sırası | uygulanmış | B/tur2(3), B/tur3(2 — biri bu turda düzeltildi), GERÇEK(1) |
| K3 çıktı sırası | uygulanmış | B/tur2(1), B/tur5(1), GERÇEK(2) |
| K4 tek karakter (sınıf tabanlı) | uygulanmış | B/tur2(1), GERÇEK(6) |
| K5 hyphen | uygulanmış | B/tur2(1), GERÇEK(3) |
| K6 yer tutucu | uygulanmış | B/tur2(1), GERÇEK(3) |
| K7 confidence | uygulanmış | B/tur2(2), GERÇEK(4) |
| K8 `source_blocks` indeks uzayı | uygulanmış | B/tur2(2), B/tur5(1), GERÇEK(2) |
| K9 konuşmacı sınırı | uygulanmış | B/tur2(5), B/tur5(1), GERÇEK(4) |
| K10 `bbox` birleşimi / `ValueError` | uygulanmış | B/tur2(1), B/tur5(1), GERÇEK(3) |
| K11 ön ayar davranışı | uygulanmış | B/tur2(1), B/tur5(1), GERÇEK(6) |
| K12 boş sonuçlar | uygulanmış | B/tur2(1), B/tur5(1), GERÇEK(3) |
| K13 determinizm | uygulanmış | B/tur2(1), B/tur5(1) + `purity_check` |
| K14 bütçe assertion'ı | uygulanmış | B/tur2(2), B/tur3(2), B/tur5(2), GERÇEK(1) — **imkânsız eşikle zorlandı, kırıldı** |
| K15 konuşmacı matrisi (5 satır) | uygulanmış | B/tur2(2), B/tur3(1), B/tur5(1), GERÇEK(7) |
| K16 yozlaşmış geometri | uygulanmış | B/tur2(1), B/tur3(1), GERÇEK(2) |
| K17 ayraç kümesi | uygulanmış | B/tur2(4), GERÇEK(2) |
| K18 NFKC istisnası | uygulanmış | B/tur2(3), GERÇEK(1) |
| K19 uzunluk mirası | uygulanmış | B/tur3(2), GERÇEK(5) |
| K20 NFKC olgu düzeltmesi | uygulanmış | B/tur3(3), GERÇEK(1) |
| K21 bileşik sınırda miras yok | uygulanmış | GERÇEK(10), B/mutant(1) — mutant M2 ile dişi kanıtlandı |
| K22 (SALT DOK.) | uygulanmış — **K26 ile ikame** | Hatalı ifade docstring'de yalnızca *"YANLIS"* damgasıyla anılıyor; doğru ifade K26 bölümünde |
| K23 bölümleme DEĞİŞMEZİ | uygulanmış | B/tur5(15), B/mutant(2), GERÇEK(3) |
| K24 `tail` kuralı | uygulanmış | B/tur5(4), B/mutant(1), GERÇEK(2) |
| K25 seçenek 1 zorunlu | uygulanmış | B/tur5(2) + tur3'ün üç string assertion'ı hâlâ yeşil |
| K26 altısı da uyumluluk formu | uygulanmış | B/tur5(5), GERÇEK(2) |
| K27 `menu` kapsam dışı | uygulanmış | B/tur5(4), GERÇEK(4) |

Tablo kanıtı: `tester_B_evidence/r5-k1_k27_uyum_tablosu.txt` (5 test dosyası, 182 test
fonksiyonu AST ile tarandı).

---

## 3. K23 — iki geçiş **gerçekten** kodda mı? (yapısal ispat)

Taklit değil, yapı. `_group`'un AST'si üzerinden altı bağımsız kilit:

1. **Gövde şekli:** gövdede **tek** üst düzey `for` (bölümleme) ve **tek**
   `if apply_inheritance:` (görünüm) var; `if` bloğu `for`'dan **sonra**, ve ondan sonra
   yalnızca `return groups` kalıyor (başka hiçbir işlem yok).
2. **Bölümleme geçişinde hiç `speaker` mutasyonu yok:** döngü içinde `replace(...)`
   çağrısı **yok** (tur 4'ün mutasyon satırı döngüden çıkarılmış); `speaker=` anahtar
   kelimesi döngüde **tam bir kez** ve yalnızca `_Item(...)` inşasında geçiyor, değeri
   **`current.speaker`** — yani grubun kendi özgün değeri; `<şey>.speaker = ...` biçiminde
   hiçbir atama yok.
3. **Bayrak bölümlemeyi göremez:** `apply_inheritance` `_group` içinde **tam olarak bir
   kez** okunuyor ve o okuma görünüm passinin `if` koşulunun **kendisi** (`reads[0] is
   flag_if.test`). Döngü içinde bayrak adı **hiç** geçmiyor.
4. **Görünüm geçişi yalnızca `speaker` güncelliyor:** blok içinde tek `replace(...)`
   çağrısı var ve anahtar kelime kümesi **tam olarak `{"speaker"}`**;
   `text`/`bbox`/`source_blocks`/`placeholders` **geçmiyor**.
5. **Geri besleme yolu yok:** görünüm passinin içinde `_group_rejection_reason`,
   `_should_group`, `_union_rect`, `_Item`, `_group` **çağrısı yok**;
   `append/insert/pop/extend/remove` **yok** (yalnızca `groups[i] = ...` yerinde
   güncelleme); `current`/`tail`/`pure_length_boundaries`/`groups` değişkenlerine
   **atama yok**. (3)+(1) ile birlikte: üretilen `speaker`'ın tekrar bir gruplama
   kararına girebileceği **yol yok**.
6. **`_normalize_impl` bayrağı yalnızca `_group`'a iletiyor:** fonksiyon içinde
   `apply_inheritance` tam bir kez okunuyor ve tek `_group(...)` çağrısının anahtar
   kelime sözlüğü **tam olarak** `{"apply_inheritance": "apply_inheritance"}`. Boru
   hattının diğer beş adımı bayrağı görmüyor. `__all__ == ("normalize",)`,
   `normalize`'ın imzası `(blocks, preset)` — kanca genel API'ye **sızmıyor**.

**Bu turda kapattığım eksik halka:** yukarıdaki tüm K23 kanıtları `_normalize_impl`
üzerinden ölçülüyordu, ama ürünün çağırdığı fonksiyon `normalize`. Hiçbir test
`normalize` ≡ `_normalize_impl(..., True)` bağını **pinlemiyordu**; `_normalize_impl`'in
varsayılanı `False`'a dönse `normalize` mirası **sessizce** kaybederdi ve K23 denetimi
yine yeşil kalırdı. Yeni test (`test_r5_k23_normalize_gercekten_miras_ACIK_yola_delege_ediyor`):
`normalize` gövdesi **tek satır** `return _normalize_impl(blocks, preset)`, varsayılan
`True`, dört ön ayarda çıktı eşitliği, ve eşitliğin **boş olmadığı** (miras kapalıyla
`speaker`'da gerçekten ayrıştığı) kanıtlanıyor.

**Davranış tarafı (kendi üreticilerim, implementer'ın 2500'lük denetimine güvenmeden):**
karışık üretici 900×4 = **3600 koşum** (tohum 987654321), monolog üretici 600×4 =
**2400 koşum** (tohum 1337), mutant harness'ının üreticisi 400×4 = **1600 koşum**
(tohum 20240510). Toplam **7600 koşum, üç ayrı tohum, üç ayrı geometri dağılımı**,
tek ihlal yok. Denetimin **boş olmadığı** ayrıca ölçülü: monolog üreticisinde miras
2400 koşumun 200'den fazlasında **gerçekten** gözleniyor, 20'den fazlasında **iki veya
daha çok** noktada (zincirleme). Farkın yönü de kilitli: her fark **yalnızca**
`None → değer` yönünde; miras hiçbir `speaker`'ı silmiyor veya değiştirmiyor.

---

## 4. Mutant sondası — denetimin dişleri var mı?

`tester_B/test_k23_mutant_sondasi_tur5.py`. Yöntem: repo'nun `src/` ağacı `tmp_path`
altına **kopyalanır**, kopyaya tek cerrahi mutasyon uygulanır, ölçüm **ayrı bir
süreçte** (kopyanın dizini `sys.path[0]`) koşar. **`src/` altına hiçbir şey yazılmaz.**
Ham çıktı: `tester_B_evidence/r5-mutant_sondasi.txt`.

| Koşum | K23 ihlali (1600 koşum) | B1 bölümlemesi | K24 kuyruk `speaker` | K2/K21 fixture |
|---|---|---|---|---|
| **KONTROL** (mutasyon yok) | **0** | `[(0,1),(2,),(3,)]` | `None` ✓ | `['Ada', None]` ✓ |
| **M1** miras bölümlemeye sızıyor | **7** ✗ | `[(0,1),(2,3)]` ✗ **VARYANT A** | `None` | `['Ada', None]` |
| **M2** K21/K24 ikinci sorgusu kaldırıldı | 0 | `[(0,1),(2,),(3,)]` | `'Ada'` ✗ | `['Ada','Ada']` ✗ |
| **M3** `tail` → `current` | 0 | `[(0,1),(2,),(3,)]` | `'Ada'` ✗ | `['Ada', None]` |

Okunuşu:

- **M1** (tur 4'ün gerçek hatası: `nxt = replace(nxt, speaker=current.speaker)` bölümleme
  geçişinde) K23 denetimimi **gerçekten kırıyor** — hem kendi üreticimde 1600 koşumun
  7'sinde bölümleme farkı, hem şefin **B1** senaryosunda `(2,3)` birleşmesi (VARYANT A)
  birebir geri geliyor. İlk ihlalin ham hâli: `subtitle` ön ayarında miras açıkken
  `[7,8]` birleşiyor, kapalıyken `[7],[8]` ayrı kalıyor. **Denetim boş değil, dişli.**
  (M1 ayrıca AST kilidi 2'yi de kırar — döngüye `replace(` sokuyor.)
- **M2/M3** K23'ü **kırmıyor** (bölümleme değişmiyor, çünkü sızıntı yok) ama K24
  ölçümünü bozuyor. Yani K23 ve K24 denetimlerim **birbirinden bağımsız** olarak dişli;
  K23 değişmezi tek başına K24 hatasını yakalamaz — bu iş bölümü artık makineyle sabit.
- **M2** ek olarak K21'in kendisini kaldırdığı için, §1'de düzelttiğim testin **eski**
  assertion'ı (`['Ada','Ada']`) tam olarak bu mutantla yeşil kalıyor. Teşhisimin
  makineyle doğrulanmış hâli budur.
- **KONTROL** koşumu temiz — sonda yanlış pozitif üretmiyor.
- Sonda **bayatlamaya karşı korunmuş**: her mutasyon deseni kaynakta **tam bir kez**
  bulunmalı, yoksa test açık bir mesajla kırılıyor (`_group` yeniden yazılırsa sonda
  sessizce etkisiz kalmaz).

---

## 5. Ayrışmazlık, sıra, reason kodları

- **`_should_group` hâlâ tek satırlık devretme:** gövde = docstring + **tek** `return`,
  ve `ast.unparse` çıktısı **tam olarak** `return _group_rejection_reason(a, b, params) is None`.
  İmza `(a, b, params) -> bool`, `ignore_length` **geçirilmiyor** (varsayılan kullanılıyor).
  Davranış ispatı: **20.000 çift** (yeni tohum 555000111, tur 3'ten farklı) —
  `_should_group(a,b,p) is (_group_rejection_reason(a,b,p) is None)` her çiftte;
  ve ispat boş değil: `None` + **altı reason kodunun hepsi** örneklemde görülüyor.
- **`speaker` hâlâ `length`'ten önce:** hem yapısal (`return` satır numaraları
  `speaker < length < height < gap < width < overlap`) hem davranışsal (X/Y çifti tek
  başına kapasiteyi aşacak kadar uzun olsa bile reason `"speaker"`; `ignore_length=True`
  bunu değiştirmiyor).
- **Reason kodları tur 3–4 ile birebir aynı:** kendi bağımsız örneklemimde altı kodun
  altısı da beklenen değeri veriyor; `_group_rejection_reason`'ın döndürdüğü sabit
  kümesi **tam olarak** `{speaker, length, height, gap, width, overlap, None}`.
  Tur 3'ün üç string-karşılaştırmalı assertion'ı (`tester_B/test_karar_uyumu_tur3.py`
  satır **356/361/366** — K25'in koruduğu regresyon tabanı) **aynı satırlarda ve yeşil**.

## 6. K24 / K25 / K26 / K27 / K14 / docstring ofset

- **K24 — miras sorgusu `tail` ile mi?** Evet, satır **`src/ocr/normalizer.py:1363`**:
  `and _group_rejection_reason(tail, nxt, params, ignore_length=True) is None`.
  `_group` içinde `_group_rejection_reason` tam **iki** kez çağrılıyor; ana karar
  `(current, nxt, params)`, miras sorgusu `(tail, nxt, params, ignore_length=True)`.
  `tail` tanımı yapısal olarak da doğru: döngü öncesi `items[0]`, döngü içinde **yalnızca**
  `nxt` (ham öge) atanıyor — `_Item(...)`/`current` **asla**; toplam üç atama
  (kurulum + başarılı birleşim + yeni grup). Ayrım gerçek: kendi geometrimde aynı çift
  için `current` ile sorgu yanlışlıkla `None`, `tail` ile `"gap"` dönüyor; uçtan uca
  `normalize` üzerinden kuyruk `speaker=None` kalıyor.
- **K25 — dönüş tipi `str | None`:** imzada ve AST'de `str | None`; `ignore_length`
  KEYWORD-ONLY, varsayılan `False`, anotasyon `bool`; çalışma zamanında dönen değer
  `str`/`None` (küme/liste değil). Seçenek 2 kırardı denilen üç assertion sağ.
- **K26 — decomposition etiketleri:** bağımsız tam Unicode taraması (0x0–0x10FFFF) ASCII
  dışı kümeyi **tam olarak** altı codepoint veriyor; altısının da `decomposition`'ı
  `<` ile başlıyor (uyumluluk formu), etiket dağılımı **2×`<wide>` + 2×`<small>` +
  2×`<vertical>`**, hedefler `?`/`!`, kategori hepsinde `Po`. Docstring'in olgusal
  ifadesi ölçümle örtüşüyor ve *"Unicode 15.0.0"* iddiası ortamla (unidata_version
  15.0.0) uyumlu — bayatlama sondası yeşil. Kod hâlâ NFKC ile karar veriyor; altı
  codepoint'in hiçbiri yürütülebilir kodda sabit kodlanmış değil (beyaz liste yok).
- **K27 — dört ön ayar testi:** gerçek test dosyasında **tam dört** `test_k27_*` var ve
  her biri **kendi** `OcrPreset` üyesini kullanıyor. Aynı fixture dört ön ayarda:
  dialogue/tooltip/subtitle → gövde2 `"Ada"` miras alıyor, menu → ayrı segment ve
  `None`. `menu`'de `_group`'un **hiç** çağrılmadığı, patlayan bir yedekle kanıtlı
  (menu sorunsuz geçiyor, dialogue patlıyor), ve çağrının `params.should_group`
  koşuluna bağlı bir `IfExp` içinde olduğu yapısal olarak sabit.
- **K14 — assertion gerçek mi?** Gerçek testin kaynak kodu alınıp eşik `5.0 → 0.0`
  (imkânsız) yapıldığında **`AssertionError` fırlatıyor**; orijinal gövde (5 ms) hâlâ
  geçiyor. `assert median_ms <= 5.0` metni yerinde, `skip`/`xfail`/`skipif` işareti yok.
- **Docstring ofset testlerim yeşil:** docstring tur 5'te büyüdü (821 satır); tur 3'te
  kurduğum anchor+pencere yöntemi hâlâ doğru bölümleri buluyor — "## Isleme sirasi" →
  "## K1" penceresi altı adımı **aynı sırayla** taşıyor, K20 penceresi
  *"BILGI AMACLIDIR"*/*"BEYAZ LISTE DEGILDIR"*/NFKC ibarelerini kapsıyor, K23 penceresi
  *"BOLUMLEMESI"*/*"BIREBIR AYNI"*/`source_blocks` içeriyor.

---

## 7. Bloke ETMEYEN notlar (şefin takdirine)

**N1 · Docstring'de anılan iki test adı gerçekte yok.** (`r5-bayat_docstring_atiflari.txt`)

| Yer | Anılan ad | Gerçek ad |
|---|---|---|
| `normalizer.py:92` (K2) | `test_k2_esik_alti_blok_ortada` | `test_k2_esik_alti_orta_blok_komsulari_birlestirir` |
| `normalizer.py:203–204` (K26 "Zorunlu test") | `test_k26_alti_karakterin_hepsi_uyumluluk_formu_ve_etiket_dagilimi_dogru` | `test_k26_alti_karakterin_hepsi_uyumluluk_formu_ve_etiket_dogru` + `test_k26_alti_karakterin_etiket_dagilimi_iki_iki_iki` |

Ölçümün **kendisi** var ve yeşil — bulgu yalnızca atıf düzeyinde, bu yüzden bloke
etmiyor. Yine de PROTOKOL §4.6/2 (*"her değişmezin yanında onu ölçen ... test adı
yazılır"*) açısından okuyucu ölçümü **adıyla bulamıyor**; ve ikincisi, tam olarak
*sessizce bayatlamayı önlemek için* yazılmış **K26 bölümünün içinde**. Şef tur 3'te
benzer bir "bloke etmeyen" notu yeniden sınıflandırmıştı; kararı şefe bırakıyorum.
Yeni bir bayat atıf eklenirse testim kırılacak, bu ikisi düzeltilince geçmeye devam
edecek (alt küme kontrolü) — yani not makineyle takipli.

**N2 · K2 × K19/K21 etkileşimi belgelenmemiş (ürün görünür).** Uzun bir monoloğun
**ortasında** tek bir eşik-altı OCR satırı düşerse, geride kalan boşluk gerçek bir
geometrik kopuş üretebilir; o sınır artık "uzunluk-tek" olmadığı için K19 mirası
**sessizce kaybolur** ve kuyruk repliği `speaker=None` kalır. Davranış K19/K21'in
lafzına **uygun** (geometrik boşlukta atıf spekülasyondur), ama hiçbir K bu etkileşimi
yazmıyor; docstring'in K2 bölümü *"o blok hiç var olmamış gibi çalışır"* diyor — bu
**metin/hyphen** için doğru, **geometri** için değil (blok düşse de boşluğu kalıyor).
Bir cümlelik docstring notu yeterdi. §1'deki düzeltilmiş testim iki yönü de sabitliyor.

**N3 · `normalize` "sabit `True` ile delege eder" — kodda `True` yazılı değil.** Şef
kararı (env.md K23 satırı) *"`normalize` buna sabit `True` ile delege eder"* diyor;
kod `return _normalize_impl(blocks, preset)` ile **varsayılana** güveniyor. Bugün
davranış aynı, ama varsayılan bir gün `False`'a dönerse `normalize` mirası **sessizce**
kaybeder ve K23 denetimi yeşil kalmaya devam ederdi. Artık test bunu pinliyor (§3).
Açık `apply_inheritance=True` yazmak kararın lafzına da daha uygun olurdu.

---

## 8. Yazdıklarım

- `tester_B/test_karar_uyumu_tur5.py` — üç yeni test eklendi (delegasyon halkası +
  docstring atıf taraması + K26 zorunlu ölçümünün gerçek adlarıyla doğrulanması).
- `tester_B/test_k23_mutant_sondasi_tur5.py` — **yeni**, mutant sondası (5 test).
- `tester_B/test_karar_uyumu_tur3.py` — bayat assertion düzeltildi (satır 518+; K25'in
  koruduğu 356/361/366 satırları **değişmedi**).
- `tester_B_evidence/r5-*.txt` — 15 kanıt dosyası, UTF-8.
- `verdict-B.md` — bu dosya (`round: 5`).

`src/` ve `tests/` altına **hiçbir şey yazılmadı**.
