---
task: T-004
role: tester
round: 7
decision: onay
checks:
  - name: "mypy --strict temiz (kabul komutu 1)"
    cmd: "python -m mypy --strict src/ocr/normalizer.py src/ocr/presets.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r7-mypy.txt
  - name: "urun testleri yesil (kabul komutu 2) -- 124 -> 125"
    cmd: "python -m pytest tests/unit/ocr/test_normalizer.py -q"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r7-pytest-urun.txt
  - name: "saflik denetimi temiz (kabul komutu 3, K29 atiflari bozulmadi)"
    cmd: "python .agents/tasks/T-004/purity_check.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r7-purity.txt
  - name: "olcu kiti bes kanal temiz (kabul komutu 4) -- ayrisma/kimlik/kapsam/sira/sayi = 0"
    cmd: "python .agents/tasks/T-004/olcu_kiti.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r7-olcu-kiti.txt
  - name: "regresyon: sefin daraltilmis tabani -- 822 passed, dusen yok"
    cmd: "python -m pytest tests/unit/ocr tests/unit/contracts tests/unit/capture/test_dpi.py tests/unit/capture/test_change_detector.py -q"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r7-pytest-regresyon.txt
  - name: "tur 6 mutant sondam regresyonsuz -- M3/M4/M5/M11/M12/M13a/M13b/M15 hepsi ayakta (181 passed)"
    cmd: "python -m pytest .agents/tasks/T-004/tester_B -q"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r7-pytest-tester_B.txt
  - name: "kor takim: TEK kirik ve o da BEKLENEN (A'nin strict xfail'i XPASS'a dondu) -- 623 passed"
    cmd: "python -m pytest .agents/tasks/T-004/tester_A .agents/tasks/T-004/tester_B .agents/tasks/T-004/tester_C -q"
    exit_code: 1
    result: gecti
    evidence: tester_B_evidence/r7-kor-takim.txt
  - name: "T7-1: `### K24` bolumu SILINMEDI, devir blogu + 'NEDEN CURUDU' var; K28=8 _raw_query_pair=3 (tur basi 0/0); `## K28`'de DEVRALINDI capasi"
    cmd: "python .agents/tasks/T-004/tester_B_evidence/r7-k24-bolum.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r7-k24-bolum.txt
  - name: "T7-1: degisiklik SALT DOKUMANTASYON -- uc kademeli kanit, MODUL docstring'i disinda hicbir sey degismedi"
    cmd: "python .agents/tasks/T-004/tester_B_evidence/r7-ast-esitlik.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r7-ast-esitlik.txt
  - name: "T7-1: yeni K24 metninin testler hakkindaki iddialari DOGRU (K29 bir kademe ileri) + T7-2 sondasinin kanca hijyeni"
    cmd: "python .agents/tasks/T-004/tester_B_evidence/r7-k24-iddia-denetimi.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r7-k24-iddia-denetimi.txt
  - name: "T7-2 DISLI MI: kendi kurdugum DORT `params` mutantinin DORDU DE testte dusuyor (M15-c yalniz-dialogue'da GECIYOR -- iki yonluluk ZORUNLU)"
    cmd: "for m in TEMIZ M15-a M15-b M15-c M15-d; do python .agents/tasks/T-004/tester_B_evidence/r7-mutant-kosucu.py $m; done"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r7-mutant-params.txt
  - name: "T7-2: esik carpimlari ASSERT'te -- on ayar tablosu kayarsa test TOTOLOJIYE dusmuyor, KIRILIYOR"
    cmd: "for p in P-a P-b; do python .agents/tasks/T-004/tester_B_evidence/r7-onayar-kaymasi.py $p; done"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r7-onayar-kaymasi.txt
  - name: "T7-2: olcu kiti DEGISTIRILMEDI -- dort surumde de ayni SHA (db0361a); `sorgu_kaydi()` katmanli ve LIFO geri aliyor"
    cmd: "git rev-parse 74256d8:.agents/tasks/T-004/olcu_kiti.py 0de4546:.agents/tasks/T-004/olcu_kiti.py HEAD:.agents/tasks/T-004/olcu_kiti.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r7-kit-degismedi.txt
  - name: "known_gaps: kararin 'YAPILMAYACAKLAR' tablosundaki ALTI kalemin ALTISI DA yazilmis (1/6..6/6), her biri gerekceli"
    cmd: "grep -o \"DEVREDEN [0-9]/6\" .agents/tasks/T-004/delivery.md | sort | uniq -c"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r7-known-gaps.txt
  - name: "NOT (bloke DEGIL): kararin kabul satiri `pytest tests -q -> 822` commit'in TEMIZ checkout'unda YANLIS -- T-005'in kirmizi faz testleri src'siz commit'lenmis"
    cmd: "sh .agents/tasks/T-004/tester_B_evidence/r7-commit-tutarliligi.sh <gecici-worktree>"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r7-commit-tutarliligi.txt
blocking_issues: []
---

# Tester-B — T-004, Tur 7 (kapanış turu, mercek: **B — karar uyumu**)

**Karar: ONAY.** İki kalem de kararın tarif ettiği gibi yapılmış. T7-1 gerçekten
salt dokümantasyon; T7-2 gerçekten dişli — hem de kararın kendi M15 tarifinden
**daha** dişli. Bloke eden bulgu yok.

Aşağıdaki her ölçüyü kendi elimle yeniden ürettim; şefin sayılarına
dayanmadım. Kanıt dosyaları `tester_B_evidence/r7-*` altında, üretici
betikleriyle birlikte.

---

## T7-1 — `### K24` bölümü

### Denetlenenler

| Karar ne dedi | Ölçtüm | Sonuç |
|---|---|---|
| Bölüm **silinmeyecek** (tarihçe korunur) | Bölüm yerinde, 50 → **85 satır** (büyümüş, kısalmamış) | ✔ |
| Başına **devir bloğu** | `DEVREDILDI (tur 6, K28)` bloğu var (1 geçiş) | ✔ |
| **"Neden çürüdü"** paragrafı | `NEDEN CURUDU` paragrafı var (1 geçiş) | ✔ |
| `## K28`'e **devralma çapası** | `DEVRALINDI` var; K28 bölümünde `K24` geçişi 1 → **7** | ✔ |
| Bölümde `K28` ve `_raw_query_pair` | **8** ve **3** (tur başında **0** ve **0**) | ✔ şefin sayısıyla birebir |
| `purity_check` exit 0 (K29 atıfları) | exit 0 | ✔ |

Bölüm sınırını kendi dilimleyicimle çıkardım (başlık metninden bir sonraki
`##`/`###` satırına kadar), şefin diliminden bağımsız olarak. Aynı sayıya
vardım.

### "Salt dokümantasyon mu" — şefin ölçüsünden **bir kademe dar** ölçtüm

Şef "docstring'siz AST önceki commit'le birebir aynı" diye ölçmüş. Bu doğru
ama **tek başına yetmez**: tüm docstring'leri silip karşılaştırmak, bir
**fonksiyon** docstring'inin de değiştiğini gizlerdi — oysa karar T7-1'i
*modül* docstring'iyle sınırlı tarif ediyor. Üç kademe koştum:

1. **Tüm docstring'ler çıkarılmış AST** → AYNI (şefin ölçüsü, yeniden üretildi)
2. **Yeni ağacın modül docstring'i eskisiyle değiştirilip tam AST** → AYNI
   → yani *diğer docstring'ler dahil* modül docstring'i dışında **hiçbir şey**
   değişmemiş
3. **Bayt düzeyi:** `git diff -U0`'daki tüm hunk'lar modül docstring'inin
   kaynak aralığında (1–947) mı → **evet, dışarıda hunk YOK**

Sonuç: değişiklik salt dokümantasyon ve **yalnız modül docstring'i**.

### Çelişki taraması

`## K28` ile `### K24`'ü satır satır karşılaştırdım. Sert çelişki **yok**:
K24'ün ayakta kalan yönü (sorulan öğe grubun **kuyruğu**dur, birikmiş
`current`'in birleşik kutusu değil) ile K28 aynı şeyi söylüyor; çürüyen kısım
(`tail`in **ham** olduğu varsayımı ve tur-5 çağrı biçimi) artık geçmiş zamanda
ve `CURUYEN kisim su:` altında etiketli. Eski cümlenin **koşulsuz ve şimdiki
zamanlı** biçimi kalmamış — A'nın xfail'inin şikâyeti buydu ve XPASS'a dönmesi
bunu bağımsız olarak doğruluyor.

Ayrıca bölümün testler hakkındaki **ölçülebilir iddialarını** denetledim
(K29'un bir üst katmanı: atıf var olan teste ama iddia edilen *mekanizma*
doğru mu?):

- "birincisi `_group_rejection_reason`'i doğrudan çağırır, `_raw_query_pair`
  yoluna hiç girmez" → o testin koşumunda `_raw_query_pair` çağrı sayısı
  **0**. **Doğru.**
- "ikincisinde kuyruk tek bloklu (`source_blocks=(2,)`), ham ikame özdeşliktir"
  → miras sorgusu 1 adet, `sol_sb=(2,)`. **Doğru.**
- Her iki test de var ve yeşil. **K29 tamam.**

Bir de K28'e eklenen "BAŞLIK DİSİPLİNİ" notunun kendi iddiasını ölçtüm: K24
başlık metni docstring'de **tam olarak 1 kez** geçiyor. Doğru.

---

## T7-2 — `test_k28_miras_sorgusu_ayni_params_ile_sorulur`

### İki yönlü mü, eşikler assert'te mi

Evet. Eşik çarpımları yorumda değil, **assert'te**:

```
assert dialogue.max_vertical_gap_ratio * 18 == pytest.approx(14.4)
assert tooltip.max_vertical_gap_ratio  * 18 == pytest.approx(5.4)
assert tooltip.max_vertical_gap_ratio * 18 < 12 < dialogue.max_vertical_gap_ratio * 18
```

Bu korumanın **dişi var mı** diye ön ayar tablosunu bellekte kaydırdım
(`src/` yazmadan):

| Kayma | Sonuç |
|---|---|
| `dialogue` 0.8 → 0.5 | test **düştü**, kırılma yeri satır 1934 — eşik assert'i |
| `tooltip` 0.3 → 0.8 (iki ön ayar aynılaşır, ayırt gücü biterdi) | test **düştü**, satır 1935 |

Yani tablo kayarsa test totolojiye düşmüyor, **kırılıyor**. Docstring'in
iddiası doğru.

### Dişli mi — dört mutant kurdum, dördü de düşüyor

Mutantları `src/`'ye **yazmadan** kurdum: `normalizer.py`'nin kaynak metni
okunuyor, miras-sorgusu çağrı noktası metinsel değiştiriliyor, sonuç bellekte
derlenip `sys.modules`'a konuyor. Koşum sonunda `git status src/ocr/` boş —
çalışma ağacına sızma yok.

| Mutant | Ne yapıyor | Şefin/İmpl.'in testi | **Yalnız-`dialogue`** ablasyonu |
|---|---|---|---|
| TEMİZ | (kontrol) | geçti | geçti |
| **M15-a** | sorgu sabit `tooltip` params ile | **DÜŞTÜ** (`DIALOGUE`) | düştü |
| **M15-b** | sorgu içi `replace(params, ratio=0.3)` | **DÜŞTÜ** (`DIALOGUE`) | düştü |
| **M15-c** | sorgu sabit `dialogue` params ile | **DÜŞTÜ** (`TOOLTIP`) | **GEÇTİ** |
| **M15-d** | sorgu içi `replace(...)`, **değerler aynı** | **DÜŞTÜ** (`DIALOGUE`) | düştü |

Üçü istenmişti; dördüncüyü (M15-d) kendim ekledim.

### İmplementer'ın bulduğu boşluk gerçek — kökünü ölçtüm

M15-c satırı, implementer'ın "şefin ölçüsünde boşluk var" iddiasını
**doğruluyor**: kararın M15 tarifiyle birebir örtüşen mutant (sabit
`get_params(DIALOGUE)`) yalnız-`dialogue` bir testte **ayırt edilemiyor**.

Kökü şu — ve bu, benim (N3) tur 6'da verdiğim ölçünün gerçek kusuru:
`get_params` modül düzeyinde **tekil (singleton)** nesneler döndürüyor
(`get_params(DIALOGUE) is get_params(DIALOGUE)` → `True`, ölçtüm). Bu yüzden
sabit `get_params(DIALOGUE)` yazan mutant, `dialogue` koşumunda **hem davranış
hem de `is` kimlik assert'ini** geçiyor: kaçırdığı nesne zaten aynı tekil.
Ayıran tek şey `tooltip` koşumu. **Ölçüyü ben verdim ve eksik verdim;
implementer haklı, düzeltme yerinde.**

M15-d ise testin `is` kullanma gerekçesini doğruluyor: değerleri **birebir
aynı** (`(0.8, 280)`) ama nesnesi başka olan bir `replace`, yalnızca kimlik
assert'iyle yakalanıyor — değer karşılaştırması bunu kaçırırdı. Docstring'in
"`is` ile yazılır çünkü..." gerekçesi ölçüyle doğrulandı.

### Kit ve `sorgu_kaydi()`

- **Kit değiştirilmemiş:** `olcu_kiti.py` SHA'sı `74256d8`, `0de4546`, `HEAD`
  ve çalışma ağacında **aynı** (`db0361a…`). Şefe ait `tests/unit/ocr/conftest.py`
  de değişmemiş.
- **`sorgu_kaydi()` doğru kullanılmış:** sonda kendi `params` kancasını kitin
  **altına** katmanlıyor (önce kendisi, sonra kit), böylece kitin `orij`i sondanın
  kancası oluyor ve çıkışta LIFO sırayla geri alınıyor. Ölçtüm: sonda öncesi ve
  sonrası `_group_rejection_reason` **aynı nesne**, üstelik gerçek fonksiyon;
  kit kaydı 1 miras sorgusu, kendi kancası 2 çağrı (1 bölümleme + 1 miras)
  görüyor. Sızıntı yok, kit mutasyonu yok.
- Testin `all(p is params ...)` assert'i bölümleme çağrılarını da kapsıyor —
  değişmezin **üst kümesi**, altı değil. Sorun değil, fazlası.
- `assert gorulen_params` ve `assert len(miras) == 1` sayesinde sonda hiç çağrı
  görmezse test **totolojik geçmiyor**, düşüyor.

---

## Regresyon

- **Tur 6 mutant sondam** (M3/M4/M5/M11/M12/M13a/M13b/M15): `tester_B` takımı
  **181 passed**, exit 0. Regresyon yok.
- **Şefin daraltılmış tabanı: 822 passed**, düşen yok — şefin ölçtüğü sayıyla
  birebir.
- **Kör takım: 623 passed, 1 failed.** Tek kırık, brifingde önceden haber
  verilen A'nın `strict=True` xfail'i (`test_modul_docstringinin_K24_bolumu_
  bugunku_cagri_bicimini_anlatiyor`), T7-1 düzeltilince XPASS'a döndüğü için.
  **Beklenen ve doğru yönde:** A'nın kapısı düzeltmenin gerçekten yapıldığını
  bağımsız olarak doğruluyor. Başka kırık yok.

## `known_gaps`

Kararın "bu turda YAPILMAYACAKLAR" tablosundaki **altı** kalemin **altısı da**
yazılmış (`DEVREDEN 1/6` … `6/6`, her biri tam bir kez), her biri erteleme
gerekçesiyle ve doğru bulgu sahibiyle (B/N1, B/N4, C/1, C/4, C/2, C/3).
Tabloyla birebir eşleşiyor.

> **Kapsam beyanı.** `delivery.md` merceğime kapalı. Şef bu turda `known_gaps`
> denetimini açıkça bana verdi; bu yüzden dosyadan **yalnız `known_gaps`
> alanının `DEVREDEN n/6` işaretçilerini** çektim, geri kalanını okumadım.
> Tur 6'da bu yarıyı "doğrulanmadı" diye bırakmıştım; artık doğrulandı.

---

## Notlar (bloke değil)

### 1. Kapanış commit'i kendi içinde tutarlı değil — şefin işlem yapması gerek

Kararın kabul satırı: *"Artı regresyon: `python -m pytest tests -q` → 822
passed, düşen yok."* Bu, **commit'in temiz bir checkout'unda doğru değil.**

`f75d4d4` commit'i T-005'in TDD kırmızı faz testlerini (`tests/unit/capture/
test_service.py`, `test_monitors.py`, `conftest.py`) **içeriyor**, ama
import ettikleri `src/capture/service.py` ve `src/capture/monitors.py`
commit'te **yok** (hâlâ takipsiz). Geçici bir worktree'de ölçtüm:

```
### TEMIZ checkout'ta: python -m pytest tests -q
E   ModuleNotFoundError: No module named 'src.capture.service'
ERROR tests/unit/capture/test_monitors.py
ERROR tests/unit/capture/test_service.py
!!! Interrupted: 2 errors during collection !!!
```

Yerelde görünmüyor çünkü o iki `src/` dosyası çalışma ağacında **takipsiz
olarak var**. Aynı temiz checkout'ta T-004'ün kendi kapsamı **822 passed** ve
dört kabul komutu da temiz — yani **kusur T-004'ün iki kaleminde değil**,
başka bir görevin yarım işinin kapanış commit'ine süpürülmüş olmasında.

**Neden bloke etmiyorum:** brifingde şef T-005'in kırmızı fazını ve oradaki
toplama hatasını zaten kapsam dışı ilan etmişti; iki kalem kusursuz; T-004'ün
kapsamında düşen tek test yok. **Ama şefin bilmesi gereken şey şu:** kapsam
dışı sayılan durum artık yalnız kirli çalışma ağacında değil, **commit'in
kendisinde**. `f75d4d4`'ü checkout eden hiç kimse tam takımı koşamaz ve
kararın kabul satırı o commit için yanlıştır. T-004 kapandı denmeden önce ya
T-005 kendi `src/` dosyalarını indirmeli, ya bu dosyalar commit'ten
ayrılmalı.

### 2. `### K24`'ün "Kapsam" paragrafı tarihçe olarak etiketsiz

"Uygulama" paragrafı `(TUR 5, K28 ONCESI -- TARIHCE)` diye açıkça
etiketlenmiş; hemen ardından gelen **"Kapsam"** paragrafı etiketsiz ve
"…YALNIZ K21'in IKINCI sorgusu icin **SOL TARAFIN** HANGI oge OLDUGU degisti"
diyor. Bu, K24'ün *kendi* deltası için doğru; ama K28 **iki tarafı da**
değiştirdi, dolayısıyla paragraf bugünkü durumu tek başına okuyan için eksik.

Sert çelişki saymıyorum: üstteki devir bloğu, blockquote sonrası parantez
("SAG taraf icin de simetrigi gecerlidir") ve "NEDEN CURUDU" paragrafı
("AYNI sey ADAY (`nxt`) tarafi icin de gecerlidir") okuru üç ayrı yerde doğru
yöne çeviriyor; `## K28` de "KAPSAM (K24'ten devralinir)" diyerek bu paragrafı
açıkça devralıyor. Bir sonraki dokümantasyon turunda "Kapsam" paragrafına da
"Uygulama"daki gibi bir tarihçe etiketi eklenirse bölüm tamamen tekdüze olur.
Bu tur için gereksiz — yeni değişmez açmıyor.

### 3. Kararın M15 tarifi düzeltilmeli (kayda geçsin)

Karar M15'i *"ör. `get_params(OcrPreset.DIALOGUE)` yerine çağrının aldığı
`params`'tan başkasını geçiren"* diye tarif ediyor. `get_params` tekil
döndürdüğü için bu tarif, **`dialogue` koşumunda kendi kendini ayırt
edilemez kılıyor**. Ölçüldü (M15-c). Gelecekte bu sınıfa kapı yazacak
herkesin bilmesi için: **`params` kimliği en az iki farklı ön ayarla
sınanmalıdır**; tek ön ayarla sınanan kimlik değişmezi, o ön ayarı sabitleyen
mutanta karşı kördür.
