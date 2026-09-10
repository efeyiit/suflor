---
task: T-005
role: tester
round: 1
lens: "B -- Sayisal (tip, tasma, duzlestirme)"
decision: onay
checks:
  - name: "mypy --strict temiz"
    cmd: "python -m mypy --strict --explicit-package-bases src/capture/service.py src/capture/monitors.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r1-mypy.txt
  - name: "sahip olunan iki test dosyasi"
    cmd: "python -m pytest tests/unit/capture/test_service.py tests/unit/capture/test_monitors.py -q"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r1-pytest-owned.txt
  - name: "headless_check.py"
    cmd: "python .agents/tasks/T-005/headless_check.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r1-headless.txt
  - name: "kapsam esigi (>=95)"
    cmd: "python -m pytest tests/unit/capture/test_service.py tests/unit/capture/test_monitors.py -q --cov=src.capture.service --cov=src.capture.monitors --cov-fail-under=95 --cov-report=term-missing"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r1-cov.txt
  - name: "tests/unit/capture tamami (regresyon)"
    cmd: "python -m pytest tests/unit/capture -q"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r1-pytest-capture-all.txt
  - name: "tests tamami (regresyon)"
    cmd: "python -m pytest tests -q"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r1-pytest-all.txt
  - name: "MERCEK B testleri (136 gecti, 1 atlandi)"
    cmd: "python -m pytest .agents/tasks/T-005/tester_B -q"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r1-tester-B.txt
  - name: "MERCEK B + capture, RuntimeWarning HATA olarak"
    cmd: "python -W error::RuntimeWarning -m pytest .agents/tasks/T-005/tester_B tests/unit/capture -q"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r1-tester-B-runtimewarning.txt
  - name: "sefin iki olgusunun ve yan olgularin yeniden uretimi"
    cmd: "python -W error::RuntimeWarning probe1.py; python probe2.py; python probe3.py; python probe4.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r1-olgu-yeniden-uretim.txt
  - name: "kapilarin ayirt etme gucu: 8 mutasyon, 8'i de yakalandi"
    cmd: "python mutasyon.py; python mutasyon2.py  (gecici kopyada; depodaki src DEGISTIRILMEDI)"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r1-mutasyon.txt
blocking_issues: []
notes:
  - "Taban birebir yeniden uretildi: bes kabul komutu exit 0; tests/unit/capture 742 passed; tests 981 passed; kapsam %98.83."
  - "MERCEK B'nin alti saldiri noktasinin altisi da temiz. Kirik yok."
  - "Iki gozlem (bloke edici DEGIL, asagida): union_bbox'in dogrudan cagrida tip tasimasi; dpi_scale=nan/inf'in kabul edilmesi."
---

# MERCEK B — Sayısal (tip, taşma, düzleştirme) · Tur 1 · **ONAY**

*Sayılar hangi tipte akıyor; nerede sessizce başka bir şeye dönüşüyor?*

Testlerim: `.agents/tasks/T-005/tester_B/` (136 geçti, 1 atlandı).
Ham çıktılar: `.agents/tasks/T-005/tester_B_evidence/r1-*.txt`.
`src/`, `tests/` ve `headless_check.py` **değiştirilmedi** (`git diff --stat` boş).

## 0 · Önce ölçüyü kurdum: eşitlik bu sızıntıya kördür

Her düzleştirme iddiasını `type(...) is int` **tip kimliğiyle** ölçtüm, `==` ile
değil. Gerekçeyi kendim yeniden ürettim
(`test_olgu_esitlik_sizintiyi_goremez`, `r1-olgu-yeniden-uretim.txt`):

```
a == b        : True
hash esit     : True
kume boyutu   : 1
a.right       : 40 int64
type(a.x)     : int64   type(b.x): int
json a        : TypeError: Object of type int64 is not JSON serializable
json b        : {"x": 10, "y": 20, "w": 30, "h": 40, "monitor_index": 0, "dpi_scale": 1.0}
```

Yani `==`, `hash`, `set` ve `right`/`bottom` aritmetiğinin **hiçbiri** sızıntıyı
göremez; gören yalnız tip kimliği ve zararın kendisi (`json.dumps(asdict(...))`).
Bu, aşağıdaki her ölçünün neden `type()` + `json` çifti kullandığının nedenidir.

## 1 · numpy skaler sızıntısı — iki yol, dört tip · **TEMİZ**

| Yol | Ölçü | Sonuç |
|---|---|---|
| `rects_from_mss_monitors` | 4 tip × 4 alan ayrı ayrı | `type is int`, json temiz |
| servis önbelleği (yapım + `refresh_monitors`) | 4 tip | `type is int` |
| `Frame.rect` — **INSIDE** | 4 tip | `type is int`, json temiz |
| `Frame.rect` — **PARTIAL** | 4 tip | `type is int`, json temiz |
| `Frame.rect` — negatif PARTIAL (`-2600` → `-2560,0,60,100`) | 3 tip | `type is int` |
| `capture_full` | 4 tip | `type is int` |
| `union_bbox(list_monitors(...))` | 4 tip | `type is int` |

PARTIAL yolu ayrıştırıcıdır: şefin ölçtüğü gibi `dpi.intersect` orada **karışık**
üretiyor (`['int','int64','int64','int64']` — `x` düzleşiyor çünkü `max()` Python
`int`'ini seçiyor). Yalnız INSIDE'ı düzleşten bir uygulama orada düşer.
Uygulama düzleştirmeyi `capture_region`'ın **girişinde** yaptığı için iki yol da
temiz. `typing.cast` kaçışı kodda **yok** (AST ile ölçüldü).

`test_b1_monitors_yolu_dort_alan_ayri_ayri` her alanı tek tek numpy yapıyor:
yalnız `left`'i düzleşten bir uygulama burada düşer.

## 2 · İşaretsiz taşma — dondurulmuş `dpi.py` · **TEMİZ**

Önce tehlikeyi kendim yeniden ürettim (dondurulmuş modülü **doğrudan** çağırarak,
servis araya girmeden). Şefin `np.uint16`/`np.uint32` ölçümünü doğruladım ve
şefin listelemediği bir üçüncüsünü de buldum: **`np.uint8` de taşıyor.**

```
uint16   classify=partial  kesisen=[0, 1]  uyari=4  overflow encountered in scalar subtract/multiply/add
uint32   classify=partial  kesisen=[0, 1]  uyari=4  overflow encountered in scalar subtract/multiply/add
uint8    classify=inside   kesisen=[0, 1]  uyari=5  overflow encountered in scalar multiply/subtract
int64    classify=inside   kesisen=[1]     uyari=0
int      classify=inside   kesisen=[1]     uyari=0
```

`np.uint8` özellikle önemli: sınıflandırma tesadüfen `inside` çıkıyor ama **iki**
monitörle kesişiyor görünüyor, yani K8 kuralı `1` yerine `-1` üretirdi — ve
`np.uint8` K5/K8'in parametrelendirdiği **dört tipten biri**.

Servis tarafı: `capture_region` girişinde düzleştirdiği için
`uint8`/`uint16`/`uint32`/`uint64`'ün dördünde de INSIDE, PARTIAL, L düzeni ve
işaretsiz **monitör sözlüğü** yollarında taşma yok, `monitor_index` doğru.
Bütün B2 testleri `-W error::RuntimeWarning` altında koşuyor
(`filterwarnings("error::RuntimeWarning")` + ayrı bir tam koşum:
`r1-tester-B-runtimewarning.txt`, 878 passed).

Bu ölçünün ayırt etme gücü mutasyonla kanıtlandı — düzleştirmeyi girişten
`Frame.rect` kurulumuna taşıyan **M7** mutasyonunda tam olarak dondurulmuş
`dpi.py`'nin `w = x2 - x1` satırı patlıyor:

```
src\capture\service.py:468: in _hedef_dikdortgen
    sinif = dpi.classify_region(duz, self._monitors)
src\capture\dpi.py:321: in intersect
    w = x2 - x1
E   RuntimeWarning: overflow encountered in scalar subtract
```

## 3 · `dpi_scale` float tipi · **TEMİZ**

Olguyu yeniden ürettim: `np.float64` `float` **alt sınıfıdır** (serileşir),
`np.float32` değildir (`TypeError: Object of type float32 is not JSON
serializable`). Dolayısıyla `isinstance(v, float)` yeterli bir kapı değil ve
`float()` koşulsuz uygulanmalı — uygulama koşulsuz uyguluyor.

`float` / `float32` / `float64` / `int` / `int64` / `uint8` altısında da
`type(f.rect.dpi_scale) is float` ve json temiz. `capture_full` → `1.0` ve `float`.
PARTIAL yolunda çağıranın `1.5`'i `union_bbox`'ın `1.0`'ına **ezilmiyor**
(Y-B); `dpi.intersect`'in metadata'yı ikinci argümandan aldığını da ayrıca
ölçtüm — yani ölçü bir farka dayanıyor, tek bir sayıya değil.

## 4 · Girişteki kabul kapısı · **TEMİZ**

**24 hücre** ölçüldü: altı red değeri × dört alan (`x`, `y`, `w`, `h`).
`'10'` · `True` · `10.9` · `nan` · `inf` · `np.float32(10.5)` → her biri
`CaptureError`, mesajda **alan adı ve ham değer**, `grab_calls == 0`,
`__cause__ is None` (K6 sınıf a), `seq` tüketilmiyor.
`10.0` ve `np.float64(10.0)` → **kabul**, sonuç düz `int`; bu da dört alanda ayrı
ölçüldü. Tek alanda (`x`) ölçen bir kapı, `w`'yi çıplak `int()` ile çeviren bir
uygulamayı kaçırırdı.

Kapının gerekçesini de ölçtüm (`test_b4_ciplak_int_in_yapacagi_sessiz_yanlis`):
`int(10.9) == 10`, `int("10") == 10`, `int(True) == 1`, `int(inf)` →
`OverflowError`, `int(nan)` → `ValueError`. Yani kapı kaldırılsa gürültülü bir
hata sessiz bir yanlışa dönüşürdü.

Paketin saymadığı girdileri de ekledim: `None`, `np.bool_(True/False)`, `bytes`,
`complex` → hepsi `CaptureError`. `np.bool_` özellikle önemli:
`isinstance(np.bool_(True), bool)` **`False`**'tur, yani yalnız `bool`
kontrolüne güvenen bir uygulama onu kaçırırdı; `numbers.Integral` kapısı eliyor
(şefin ölçtüğü gibi `np.bool_` `Integral` değil — ben de doğruladım).

Sıra da ölçüldü: kapı **alan denetiminden önce** koşuyor, yoksa `w='10'`
karşılaştırması K6 taksonomisi dışında `TypeError` doğururdu.

## 5 · `numbers.Integral` daraltması ve `cast` kaçışı · **TEMİZ**

Y-C'yi mypy ile kendim yeniden ürettim (`test_b5_integral_daraltmasi_mypy_altinda`,
her koşumda gerçekten `mypy --strict` çağırıyor):

| Varyant | mypy | sızdırır mı |
|---|---|---|
| `return v` (kuralın lafzı) | **exit ≠ 0** | — |
| `return cast(int, v)` | exit 0 | **evet** |
| `return int(v)` | exit 0 | hayır |

Yani tehlike gerçek: kuralın lafzî uygulaması mypy'yi kırdığı için implementer'ın
önünde bir kaçış duruyordu. Uygulama üçüncüyü seçmiş. AST ile doğruladım:
`service.py` ve `monitors.py`'de `cast(...)` çağrısı, `*.cast(...)` ve
`from typing import cast` **yok**. `# type: ignore` sayısı: paketin izin verdiği
tek bir tane (`FakeBackend.grab`'in `[return-value]`'su).

*(Bu kapının ilk yazımı bir metin aramasıydı ve docstring'deki
`# type: ignore[return-value]` **açıklamasını** bir susturma sanıp yanlış pozitif
verdi. `tokenize` ile gerçek yorum belirteçlerine geçirdim; olay testin
docstring'inde kayıtlı.)*

## 6 · Kırpma aritmetiği · **TEMİZ**

`Rect(-2560,0,5300,100)` gerçek negatif düzende:

```
tek monitore kirpma (clamp_to_monitor(r, M0))     -> w = 2560   YANLIS
birlesime kirpma    (intersect(r, union_bbox))    -> w = 5120   DOGRU
servis                                            -> Frame.rect.w = 5120, backend kutusu 5120, monitor_index = -1
```

İkisini de ölçtüm ki "5120 doğru mu" sorusu bir sayıya değil bir **farka**
dayansın (`intersect` ve `clamp_to_monitor` birebir aynı gövdedir; yanlışlık
ikinci argümandadır). Ayrıca dört kenar + köşe (beş nokta), sıra değişiminde
geometrinin değişmemesi, numpy girdide aynı sonuç, ve L düzeninde ölü alan:
birleşime dahil (`(50,50,300,300)` → `(50,50,150,150)`, `monitor_index=-1`),
ölü alanın kendisi `OUTSIDE`, yalnız A ile kesişen bölge → `0`.

Aşırı büyük koordinatlar (`1e30`, `2**70`, `np.uint64(2**64-1)`) K6 taksonomisi
**içinde** kalıyor: `CaptureError`, `OverflowError` değil, backend çağrısı 0.

## 7 · Kapılarımın kendisi: 8 mutasyon, 8'i de yakalandı

Kapılarımın totoloji olmadığını mutasyonla kanıtladım. `src/` ve testlerim
**geçici bir kopyaya** alındı, mutasyon orada uygulandı — depodaki `src/`
değiştirilmedi (`git diff --stat -- src tests` boş).

| Mutasyon | Yakalayan **hedef** kapı |
|---|---|
| M1 giriş düzleştirmesi yok | B1 (`frame_rect_duz_int`) |
| M2 monitör düzleştirmesi yok | B1 (`monitors_yolu_duz_int`) |
| M3 çıplak `int()` (kapı yok) | B4 (24 hücrenin 20'si) |
| M4 `dpi_scale` düzleştirmesi yok | B3 |
| M5 tek monitöre kırpma | **B6'nın beş kapısı** |
| M6 `cast(int, v)` kaçışı | B1 + **B5 AST kapısı** |
| M7 düzleştirme girişte değil, geç | **B2 taşma kapıları** (yukarıdaki traceback) |
| M8 yalnız `np.int64` düzleştiriliyor | B1 (`int32` parametresi) |

Her mutasyon **hedeflediği** kapıyı düşürüyor, sadece tesadüfi bir komşuyu değil.

## Bloke etmeyen iki gözlem

**(1) `union_bbox` doğrudan çağrıda girdinin tipini taşır.** `union_bbox` saf
aritmetiktir ve `int()` uygulamaz; numpy taşıyan `Rect` verilirse çıktısı da
numpy taşır (ölçtüm: `Rect(x=np.int64(0), …)`). **Servisin hiçbir yolu bunu
kuramaz**: iki çağıran yeri de (`CaptureService._hedef_dikdortgen` ve
`FakeBackend.monitors`) ona ya `list_monitors` çıktısını ya da ham sözlüğe
çevrilecek bir `Rect` verir; ikisi de düzleşir. Ölçüm noktası servis dışındadır,
yani ihlal edilemez — Y7-8'in `[ÖLÇÜLMÜYOR]` damgasıyla aynı sınıf. Kırık
saymıyorum; `test_b1_union_bbox_dogrudan_cagrida_sizdirir` bunu belgeliyor.

**(2) `dpi_scale = nan` / `inf` kabul ediliyor.** Paket `dpi_scale` için yalnız
"düz `float` olmalı" diyor, **sonlu** olma koşulu yazmıyor; K3/K8 gereği servis
bu değeri hiçbir kararda kullanmıyor (ölçtüm: `nan` ölçekle piksel kararı
etkilenmiyor) ve `json.dumps` varsayılan ayarla `NaN` üretiyor, istisna değil.
Sözleşmenin sessiz kaldığı bir nokta; A7'ye (Qt `devicePixelRatio`'yu yazan
taraf) taşınacak bir soru olarak kaydediyorum.

**(3) Belgelenen asimetri, kırık değil.** `10.0` monitör sözlüğünde **RET**
(K5), giriş `Rect`'inde **KABUL** (K8). İkisi de paketin yazdığı gibi; gerekçe
farklı kaynaklar (`mss` daima `int` verir; çağıran Qt'den `float` taşıyabilir).
`test_b4_k5_ve_k8_kapilari_bilerek_FARKLI` bunu bir karar olarak kaydediyor.

## Karar

**onay.** Mercek B'nin altı saldırı noktasının altısı da temiz; şefin ölçtüğü
iki kritik olguyu da kendim yeniden ürettim ve uygulamanın ikisine karşı da
koruduğunu ölçtüm. Taban birebir tuttu (742 / 981 / %98.83, beş komut exit 0).
Bloke edici bulgu yok.
