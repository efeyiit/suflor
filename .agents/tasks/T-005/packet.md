---
task: T-005
title: "CaptureService: ekran/bölge yakalama, monitör listeleme, backend enjeksiyonu"
role: implementer
level: B
wave: 1
packet_version: 8
owns:
  - "src/capture/service.py"
  - "src/capture/monitors.py"
  - "tests/unit/capture/test_service.py"
  - "tests/unit/capture/test_monitors.py"
  - "tests/unit/capture/conftest.py"
  - ".agents/tasks/T-005/evidence/**"
  - ".agents/tasks/T-005/delivery.md"
forbidden:
  - "src/contracts/**"
  - "src/capture/__init__.py"
  - "src/capture/dpi.py"
  - "src/capture/change_detector.py"
  - "src/ocr/**"
  - "tests/unit/contracts/**"
  - "tests/unit/capture/test_dpi.py"
  - "tests/unit/capture/test_change_detector.py"
  - "diğer tüm dizinler"
depends_on: ["T-001", "T-003"]
acceptance:
  - "python -m mypy --strict --explicit-package-bases src/capture/service.py src/capture/monitors.py"
  - "python -m pytest tests/unit/capture/test_service.py tests/unit/capture/test_monitors.py -q"
  - "python .agents/tasks/T-005/headless_check.py"
  - "python -m pytest tests/unit/capture/test_service.py tests/unit/capture/test_monitors.py -q --cov=src.capture.service --cov=src.capture.monitors --cov-fail-under=95 --cov-report=term-missing"
  - "python -m pytest tests/unit/capture -q"
budget_ms: 10   # servisin KENDI ek yuku (K11); mss.grab'in 13.5 ms'i bu butceye dahil degil
---

# Görev

Ekranın tamamını veya bir bölgesini yakalayıp `Frame` üreten servis. Mod 2 canlı döngüsünün ilk halkası; Mod 1'in donmuş ekranını da bu üretir.

Tasarım: `docs/superpowers/specs/2026-09-09-suflor-design.md` §5.1, §5.5, §5.6, §5.7, §6, §8.3-A2. **Oku.**

> **Paket sürümü 8.** v7 kırmızı takımdan **16** bulguyla döndü (2 yüksek).
> **Y7-1:** `grab` kutusunu 0'a **kırpan** bir `MssBackend` beş kapıdan da geçiyordu — §3'ün `grab_args` denetimi **tek noktada** (`Rect(10,20,64,16)`, hepsi pozitif) ölçüyordu. Bu makinenin gerçek düzeninde sol monitör `x=-2560`; kırpan bir uygulama orada **her yakalamada sessizce yanlış piksel** verirdi ve `Frame.rect` doğru geometriyi bildirirdi. §3 artık **iki noktada** ölçüyor; şef doğruladı (kırpan varyant → exit 1).
> **Y7-2 (şefin kendi hatası):** v7'de K10'a *"ÖLÇÜ: §3 casusu dönen listeyi bozar ve ikinci çağrının bozulmamış liste verdiğini doğrular"* cümlesi yazılmıştı — **`headless_check`'te böyle bir denetim yok** (şef doğruladı: `m1` yalnızca okunuyor, 0 mutasyon). Dahası değişmez gerçek `mss`'te **gözlemlenemez**: K10 zaten "her çağrıda yeni `MSS()`" dediği için bir örneğin listesini bozmak sonrakini etkilemiyor (şef ölçtü). Cümle geri çekildi; kopyalama bir **uygulama tercihi** olarak yazıldı, kapı olarak değil.
> **Y7-3:** girişte `int()` bir *gürültülü hatayı* *sessiz yanlışa* çevirmişti — `10.9` sessizce `10`, `'10'` ve `True` sessizce kabul, `inf`/`nan` K6 taksonomisi dışında `OverflowError`/`ValueError` (şef ölçtü). Düzleştirmenin **önüne kabul kapısı** kondu.
> **Y7-4/5/7:** §5'in `elif` zinciri ayrıldı (`tumuyle_sifir` artık koşulsuz ihlal), §4 `grab`'in dekoratörsüz olmasını arıyor ve **çalışma zamanında** `isinstance(FakeBackend(()), CaptureBackend)` ölçüyor, §3'ün tip denetimi K7'nin `isinstance`'ıyla hizalandı (alt sınıf → uyarı). Şef üçünü de doğruladı.
> **Y7-6:** K7'nin kuralı **girdi sayarak** yazılmıştı; sayım kaçınılmaz anahtar deliği açıyor — KRT dört ayrışan biçim ölçtü (`__array_interface__`, `__array__`, 3B'ye `cast` edilmiş `memoryview`, `__buffer__`). Kural **tip düzeyine** taşındı.
> **Y7-8:** K8 ÖLÇÜ'sünün `capture_full` bacağı **yapısal olarak boş** — o yolun `rect`'i K5'in zaten düzleştirdiği monitör kümesinden gelir, numpy skaleri oraya ulaşamaz. `[ÖLÇÜLMÜYOR]` damgalandı.
>
> **Paket sürümü 7.** v6 kırmızı takımdan 14 bulguyla döndü (2 yüksek) ve **ikisi de yine şefin kapılarıydı** — mekanizmanın **adını** kancalıyorlardı, değişmezi değil (PROTOKOL §4.6/7; kuralı şef iki tur önce kendisi yazmıştı).
> **Y6-1:** §4'ün uyum kapısı `AnnAssign`'ın **değerini** denetlemiyordu; çıplak `_uyum_fake: CaptureBackend` (değer yok) kapıyı geçiyor ve mypy hiçbir uyum doğrulamıyordu. Şef doğruladı; kapı artık değerin `FakeBackend(...)`/`MssBackend(...)` **çağrısı** olmasını ve `grab`'in `FakeBackend`'in **kendi gövdesinde** tanımlı olmasını arıyor.
> **Y6-2 (ağır):** `headless_check` §3 `grab` dönüşünü **`np.asarray` ile** ölçüyordu — yani K7'nin yasakladığı sessiz dönüşümü denetleyicinin içinde yapıyordu. Ham `ScreenShot` döndüren bir `MssBackend.grab` beş kapıdan da geçiyor, gerçek ekranla **her yakalama `CaptureError`** veriyordu. §3 artık önce `type(a1) is np.ndarray` denetliyor; şef doğruladı (ham `ScreenShot` → exit 1).
> **Y6-3/Y6-4:** şefin iki kapısı meşru biçimlerde yanlış pozitif veriyordu (tırnaklı açıklama, `ImageArray`, `if TYPE_CHECKING:` gövdesi, monkeypatch / `from sys import modules` ile kurulan engel). İkisi de genişletildi; şef doğruladı.
> **Y6-8:** §5'in konum sadakati denetimi **şefin kendi yanlış pozitifiydi** — canlı ekranda iki grab arasında masaüstü değişiyor. Uyarıya indirildi; konum sadakatinin deterministik kapısı §3'ün `grab_args` denetimidir.
> **Y6-5/6/7/9 ve D1** aşağıdaki maddelere işlendi; hepsi şef tarafından ölçüldü.
>
> **Paket sürümü 6.** v5 kırmızı takımdan 12 bulguyla döndü (1 yüksek).
> **Y5-1 (yüksek):** v5'in protokol uyum satırları (`_uyum_fake`/`_uyum_mss`) bir **mekanizmaydı** ve varlığını hiçbir kapı denetlemiyordu — satırları silen uygulama beş kabul komutundan da geçiyordu, yani paketin "protokol uyumu böylece **makineyle** doğrulanır" cümlesi yanlıştı. Bu tam olarak PROTOKOL **§4.6/7**'nin tarif ettiği hâl ve şef o kuralı bir tur önce kendisi yazmıştı. `headless_check` §4 artık AST ile hem iki satırın varlığını hem `FakeBackend.grab`'in dönüş açıklamasının tam olarak `np.ndarray` olduğunu denetliyor (şef doğruladı: satırlar yokken exit 1, varken temiz, `np.ndarray | None` yakalanıyor).
> **Y5-2:** K5'in "`Rect` alanlarına **hiçbir zaman** numpy skaleri yazılmaz" cümlesi mutlaktı ama yalnız **monitör sözlüğü** yolunda ölçülüyordu; `Frame.rect` yolu çağıranın numpy'sini aynen taşıyor (şef ölçtü: `Frame.rect` alanları `['int64','int64','int64','int64']`, PARTIAL'da karışık `['int','int64','int64','int64']`, ikisinde de `json.dumps(asdict(...))` → `TypeError`). K8'e ikinci düzleştirme değişmezi eklendi.
> **Y5-3:** `headless_check` §1(d) `conftest.py`'deki **her** `autouse` fixture'ı session olmaya zorluyordu; meşru ikinci bir fixture yanlış pozitif üretiyordu (şef yeniden üretti). Artık engel fixture'ı **gövdesinden** seçiliyor.
> **Y5-4:** K7'nin "`np.ndarray` değilse" değişmezinin **ayrışma girdisi yoktu** (§4.6/4): sayılan üç girdi (liste/`memoryview`/`None`) `np.asarray` ile sessizce dönüştürüldüğünde de `ndim != 3`'ten `CaptureError` alıyor — şef ölçtü: `ndim` sırasıyla 2/1/0. Ayrışan tek girdi `__array_interface__` taşıyan nesne (gerçek `mss.ScreenShot` böyledir): `np.asarray` onu `(20,30,4) uint8` olarak **sessizce kabul ediyor**.
> **Y5-5:** `headless_check` §5'in içerik iddiası 4 kanallı her `grab`'de alfa kanalı yüzünden neredeyse otomatik sağlanıyordu. Artık **birincil monitörün tamamında** `np.unique(BGR) >= 8` ölçülüyor (şef ölçtü: tam ekran 256 tekil değer). *(KRT'nin "64×16 blokların %68'i tek renkli" sayısını şef kendi örnekleminde yeniden **üretemedi** — 252 blokta %0; düzeltme yine de doğrudur çünkü tam monitör kesin olarak daha sağlamdır, ama o sayı "şef ölçtü" diye işaretlenmemiştir.)*
> **Y5-6:** düzleştirme ölçüsü yalnız `np.int64` kullanıyordu, kabul ölçüsü dört tipte koşuyordu (§4.6/7). Parametrelendirildi.
> **Y5-7:** `raw_override`'ın **public öznitelik** olduğu yazılmamıştı; implementer `self._raw_override` diye saklarsa tester'ın mutasyonu sessizce kaybolurdu.
>
> **Paket sürümü 5.** v4 kırmızı takımdan 13 bulguyla döndü (1 yüksek). **Y-C:** K5'in `numbers.Integral` kuralı bir *tanım* veriyordu, bir *dönüşüm* değil — şef ölçtü: `isinstance(v, numbers.Integral)` `object`'i `Integral`'a daraltır, `int`'e değil, bu yüzden kuralın **lafzî** uygulaması (`return v`) `mypy --strict`'i kırıyor; implementer'ın kaçış yolu (`cast(int, v)`) mypy'yi geçiyor ama `Rect`'e numpy skaleri sızdırıyor ve **paketin hiçbir ölçüsü bunu göremiyor** (`Rect(np.int64(10),…) == Rect(10,…)` → `True`, hash eşit, küme boyutu 1, `right`/`bottom` aritmetiği doğru) — oysa `json.dumps(asdict(rect))` → `TypeError: Object of type int64 is not JSON serializable`. v5 `int(v)` düzleştirmesini zorunlu kılıyor ve **tip kimliği** ölçüsü ekliyor (eşitlik ölçüsü yetmez).
> **O-F/O-G:** `FakeBackend`'in `None` dönüşü `CaptureBackend` protokolüyle tip düzeyinde çelişiyordu ve sözleşmesi K5/K6'nın kendi ÖLÇÜ satırlarının ihtiyaç duyduğu vakaları (bozuk sözlük, değişen küme, backend istisnası) kuramıyordu. **O-H:** v4'ün beş kararı (O-B, D-3, D-5, D-6, D-8) şefin kendi yeniden üretimi kayda geçmeden yazılmıştı — PROTOKOL §4.6/6 ihlali, ve **Y-C tam bu yüzden doğdu**: D-5 yeniden üretilseydi `Integral`'ın mypy altındaki daraltma davranışı ölçülür ve düzleştirme kuralı v4'e girerdi. Eksik beş kalem `olgular.txt`'ye ham çıktısıyla eklendi.
>
> **Paket sürümü 4.** v3 kırmızı takımdan 15 bulguyla döndü (2 yüksek): `headless_check` §3'ün casus `ScreenShot`'u `__array_interface__`'e **nesne adresi** veriyordu (bellek-güvensiz, büyük kutuda segfault) ve `grab()` dönüşünü **içerik** olarak hiç ölçmüyordu — ekranı hiç okumayan bir `grab` beş kapıdan geçiyordu; K8'in `dpi_scale` kuralı yalnız INSIDE yolunda ölçülüyordu, PARTIAL'da `dpi.intersect`'in ikinci argümandan getirdiği `1.0` çağıranın değerini sessizce eziyordu. Şef ikisini de kendi eliyle yeniden üretti (`olgular.txt` `[Y-A]`/`[Y-B]`). v4: §3 casusu gerçek `mss` gibi tampon nesnesi veriyor ve desenli baytlarla içerik doğruluyor; K8 iki yolda ayrı ölçülüyor; `owns` kanıt dizinini içeriyor; K5 tamsayı kuralı `numbers.Integral`; L düzeninde `monitor_index` tanımlı.
>
> **Paket sürümü 3.** v1 23 bulguyla (5 yüksek), v2 27 bulguyla (5 yüksek) kırmızı takımdan döndü. v2'nin özü: her değişmezin yanına "ÖLÇÜ" yazılmıştı ama **iki kabul komutu kodun kalitesinden bağımsız olarak çöküyordu** (kapsam komutu %0 ölçüyor, mypy mutlak import'ta çift-modül hatası veriyor), iki değişmez lafzen çelişiyordu (K9×K2), ve K10'un "her çağrıda yeni `MSS()`" kuralı kapatmayı söylemediği için 5001. çağrıda process'i öldürüyordu. Şef v2'nin beş yüksek bulgusunun **hepsini kendi eliyle yeniden üretti**; ham çıktılar `sef_dogrulama/olgular.txt` sonundaki `[Y1]..[O11]` satırlarında.
>
> Bu sürümde: beş kabul komutunun beşi de şef tarafından **çalıştırılıp** exit kodu doğrulanmış biçimde yazıldı; `headless_check.py` v3 dönüş değerlerini, kapatma sayaçlarını ve canlılığı ölçüyor; K8'in `dpi_scale` kuralı `mss`'in ölçek taşımadığı olgusuna göre yeniden yazıldı.

## Yazılacak

**`src/capture/monitors.py`** — saf yardımcılar: `rects_from_mss_monitors`, `list_monitors`, `union_bbox`.
**`src/capture/service.py`** — `CaptureBackend` protokolü, `MssBackend`, `FakeBackend`, `CaptureService`.
**`tests/unit/capture/conftest.py`** — `mss`'i engelleyen `autouse` fixture (K1).

Dondurulmuş sözleşmeler — **kullan, değiştirme**:

```
Rect(x, y, w, h, monitor_index=0, dpi_scale=1.0)  + right, bottom
Frame(image: ImageArray, rect: Rect, captured_at: float, seq: int)   # image compare=False; seq KARSILASTIRMAYA DAHIL
CaptureError(TranslatorError)
```

`ImageArray` = numpy ndarray, **BGR, uint8**.

Hazır parçalar (`src/capture/dpi.py`, **dokunma**): `classify_region(rect, monitors) -> RegionValidity` (**birleşime** göre sınıflandırır, monitör sırasına duyarsız), `intersect(a, b) -> Rect | None` (dönen `Rect`'in `monitor_index`/`dpi_scale`'i **ikinci argümandan** gelir — şef ölçtü). `clamp_to_monitor(rect, monitor)` gövdesi birebir `return intersect(rect, monitor)` — yani **aynı fonksiyon**; belirleyici olan ikinci argümandır (K4).

## Import biçimi — kabul komutu #1'in geçmesi için zorunlu

`src/__init__.py` **yok**. `src/capture` içindeki kardeş modüller **relatif** import edilir: `from . import dpi`, `from .monitors import ...`. Mutlak `from src.capture.monitors import ...` biçimi `mypy --strict`'i "Source file found twice under different module names" ile kırar (şef ölçtü, exit 2). `src/contracts` mutlak import edilir (`from src.contracts.models import ...`) — T-004'ün `normalizer.py`'si aynı düzeni kullanıyor. Kabul komutu #1'e `--explicit-package-bases` de eklendi; ikisi birden.

---

# Şefin kararları — her biri değişmez, her birinin ölçüsü yazılı

## K1 · Backend enjeksiyonu ve headless testler

```
class CaptureBackend(Protocol):
    def monitors(self) -> Sequence[Mapping[str, object]]: ...   # mss ham liste bicimi (K5'te tanimli)
    def grab(self, rect: Rect) -> np.ndarray: ...                # (h, w, 3|4) uint8

CaptureService(backend: CaptureBackend, clock: Callable[[], float] = time.monotonic)
```

**DEĞİŞMEZ:** T-005'in sahip olduğu test dosyaları gerçek ekrana dokunmaz ve gerçek `mss` modülüne **erişemez**.
**ÖLÇÜ:** `conftest.py` oturum kapsamlı (`scope="session"`) `autouse` fixture'ı `sys.modules["mss"]`'e bir **engel modül** koyar: `types.ModuleType("mss")` — gerçek `mss`'e devretmez, `__file__`'ı yoktur, gerçek `mss`'in `base`/`factory` alt modüllerini taşımaz; `MSS` ve `mss` öznitelikleri çağrılınca `AssertionError("gercek mss testte yasak")`. `headless_check.py` §1 alt-süreçte pytest altında (a) `mss.MSS()`/`mss.mss()` → `AssertionError`, (b) `getattr(mss, "__file__", None) is None` ve `base`/`factory` yok, (c) **oturum kapsamı**: iki ayrı testte `import mss` **aynı nesneyi** verir (fonksiyon kapsamlı fixture burada düşer) doğrular. Testler `FakeBackend` ile koşar.

`clock` enjeksiyonu: `captured_at` deterministik test edilebilsin diye.

**`FakeBackend` biçim sözleşmesi:**

```
FakeBackend(
    monitors: tuple[Rect, ...],
    image_factory: Callable[[Rect], np.ndarray | None] = <varsayilan>,
    raw_override: Sequence[Mapping[str, object]] | None = None,
)
```

- `monitors()` **ham `mss` biçiminde** liste döndürür — **`[0]` birleşim girdisi dahil** (K5), `[1:]` monitörler; `[0]`'ı unutan bir `FakeBackend` ilk monitörü sessizce yutar (`test_monitors.py::test_k5_fake_backend_bicimi` yakalar).
- **`raw_override` verilirse `monitors()` onu döndürür.** `raw_override`, **aynı adla public bir öznitelik** olarak saklanır (`self.raw_override = raw_override`) ve `monitors()` her çağrıda onu **o anki hâliyle** okur — anlık görüntü almak (yapımda dondurmak) **yasak**. Tester ile implementer arasındaki tek mutasyon arayüzü budur; `self._raw_override` gibi özel bir ad kullanılırsa tester'ın `fb.raw_override = [...]` ataması yeni bir öznitelik yaratır ve mutasyon sessizce kaybolur (KRT ölçtü). K5/K6'nın şu ÖLÇÜ satırları **yalnızca** bu yolla kurulabilir: bozuk sözlük (yapımda ve `refresh_monitors()`'ta), küme sayı/sıra değişimi, canlılık. (v4'ün iki parametreli sözleşmesi bunları kuramıyordu; implementer ve tester ayrı ayrı bir mekanizma **icat etmek** zorunda kalırdı.)
- Varsayılan `image_factory` `(rect.h, rect.w, 4)` sıfır dizi döndürür. Üretici **`None` döndürürse** backend `None` döndürmüş sayılır (K6 sınıf c). Üretici **istisna fırlatırsa** o istisna `grab`'den **olduğu gibi** yayılır — K6 sınıf (b) bu yolla kurulur.
- **Tip biçimi zorunlu (O-F):** `FakeBackend.grab` imzası `-> np.ndarray` **kalır** (protokole uyar) ve üreticinin `None` dönüşü `# type: ignore[return-value]` ile geçirilir. `service.py` modül düzeyine iki uyum satırı yazılır: `_uyum_fake: CaptureBackend = FakeBackend(())` ve `_uyum_mss: CaptureBackend = MssBackend()` — protokol uyumu böylece **makineyle** doğrulanır. `grab` imzasını `-> np.ndarray | None` yapmak **yasaktır**: `mypy --strict`'i geçer ama `FakeBackend` artık `CaptureBackend` **değildir**. **ÖLÇÜ (Y5-1):** `headless_check.py` §4 AST ile (a) `service.py` modül düzeyinde `_uyum_fake: CaptureBackend = ...` ve `_uyum_mss: CaptureBackend = ...` **ek açıklamalı atamalarının varlığını**, (b) `FakeBackend.grab`'in dönüş açıklamasının **tam olarak** `np.ndarray` olduğunu denetler — ikisi de eksikse kabul komutu #3 exit 1. Bu ölçü olmadan satırları silen bir uygulama beş kapıdan da geçer (KRT ölçtü; şef yeniden üretti). **Not:** `# type: ignore[return-value]`, `image_factory`'nin dönüş tipi `np.ndarray | None` olduğu sürece gereklidir; `| None` olmadan yazılırsa `--strict`'in `warn_unused_ignores`'u **exit 1** verir (KRT ölçtü). (Şef ölçtü: beş biçim denendi — `A` doğal biçim mypy'yi kırıyor, `C` mypy'yi geçiyor ama `D` onun protokole uymadığını kanıtlıyor, `E` = seçilen biçim.)

## K2 · Kare sıra numarası

**DEĞİŞMEZ:** Bir `CaptureService` örneğinde başarılı her yakalama `seq`'i tam **1** artırır; ilk başarılı yakalama `seq=0`. K6'nın **üç sınıfının hiçbiri** `seq` tüketmez. `refresh_monitors()` `seq`'i **sıfırlamaz**. Yeni örnek `seq=0`'dan başlar.
**ÖLÇÜ:** `test_service.py::test_k2_*` — başarı/başarısızlık(a,b,c)/refresh dizisi sonrası `seq` değerleri.

**Alan uyarısı — docstring'e ve `known_gaps`'e:** `seq` yalnızca **tek bir örnek içinde** karşılaştırılabilir. §5.5'in "küçük `seq`'i yok say" kuralı örnekler arasında **çalışmaz**: pipeline servis örneğini değiştirirse karşılaştırma tabanını sıfırlamak zorundadır, aksi hâlde yeni kareler eski sanılıp atılır ve çeviri sessizce donar. Bu bir pipeline (A6) kısıtıdır; burada belgelenir.

## K3 · Servis DPI'ye kördür — `dpi_scale` yakalanan pikselleri etkilemez

`capture_region(rect)` içindeki `rect`, **fiziksel piksel**, sanal masaüstü koordinatlarında. Servis ölçekleme yapmaz.

**DEĞİŞMEZ:** Aynı `x, y, w, h` ile, yalnızca `dpi_scale` alanı değiştirilerek (1.0 / 1.25 / 1.5 / 2.0) yapılan çağrılarda backend'e ulaşan `x, y, w, h` **birebir aynıdır**. `INSIDE` sınıfındaki her `rect` için backend'e giden `x, y, w, h`, çağıranın verdiğiyle birebir aynıdır.
**ÖLÇÜ:** `test_service.py::test_k3_*` — `FakeBackend` aldığı `rect`'i kaydeder; dört ölçekte karşılaştırılır.

## K4 · Bölge doğrulama — her zaman birleşime göre

Her `capture_region`'da `rect`, **servisin önbelleğindeki** monitör kümesine karşı (K5) `dpi.classify_region` ile sınıflandırılır:

| Sonuç | Davranış |
|---|---|
| `INSIDE` | olduğu gibi yakala |
| `PARTIAL` | `dpi.intersect(rect, union_bbox(monitors))` ile kırp; kırpılmışı yakala |
| `OUTSIDE` | `CaptureError` — backend **çağrılmaz** |

**DEĞİŞMEZ:** Kırpma **her zaman** `union_bbox(monitors)`'a karşı yapılır, **asla** tek bir monitöre karşı değil. (`intersect` ve `clamp_to_monitor` aynı gövdedir; yanlışlık fonksiyon adında değil ikinci argümanda olur. Şef ölçtü: iki monitöre yayılan 5300w bölge tek monitöre karşı 2560w, birleşime karşı 5120w verir — doğru cevap 5120w.)
**ÖLÇÜ:** `test_service.py::test_k4_kirpma_birlesime_gore` — yayılan bölgede `Frame.rect.w == 5120`.

**DEĞİŞMEZ:** `capture_region`, girdi `rect`'in `monitor_index` ve `dpi_scale` alanlarını **hiçbir kararda kullanmaz** — bölge yalnızca `x, y, w, h` ile değerlendirilir. (Bu makinede `Rect`'in varsayılanı `monitor_index=0` **birincil olmayan sol monitör**; varsayılana göre kırpma geçerli bölgeleri reddederdi.)
**ÖLÇÜ:** `test_service.py::test_k4_*` — gerçek negatif düzen (`M0=(-2560,0,2560,1440)`, `M1=(0,0,2560,1440)`) ile: dört kenardan ayrı ayrı taşan, köşeden taşan, iki monitöre yayılıp taşan, tamamen dışarıda; ve aynı geometrinin `monitor_index` 0/1/7 ile **aynı** sonucu vermesi.

**DEĞİŞMEZ:** Backend'e hiçbir zaman `OUTSIDE` sınıfında veya sıfır/negatif alanlı (`w<=0` ya da `h<=0`) bir `rect` gitmez; ikisi de `CaptureError`, backend çağrısı **0**.
**ÖLÇÜ:** `test_service.py::test_k4_backend_cagrisi_yok_*` — `FakeBackend.grab` çağrı sayacı.

**Kabul edilen sınır — docstring'e:** L şeklinde düzende birleşim sınırlayıcı dikdörtgeni hiçbir monitöre düşmeyen alan içerebilir; `mss` o alanı siyah doldurur. v1 bunu tespit etmez, belgeler.

## K5 · Monitör anlık görüntüsü

`monitors.py`:

- `rects_from_mss_monitors(dicts) -> tuple[Rect, ...]` — **saf**. `mss` ham listesini alır, `[0]`'ı (sanal masaüstü birleşimi) **atar**, `[1:]`'i `monitor_index=0..n-1`, `dpi_scale=1.0` ile `Rect`'e çevirir. Sözlükteki fazladan anahtarlar (`is_primary`, `name`, `unique_id`, …) **yok sayılır**.
- `list_monitors(backend) -> tuple[Rect, ...]` — `backend.monitors()`'ı `rects_from_mss_monitors`'a verir. `backend.monitors()`'ın fırlattığı istisna **olduğu gibi** yayılır (sarmalanmaz, docstring'de).
- `union_bbox(monitors) -> Rect | None` — birleşim sınırlayıcı dikdörtgeni; boş küme → `None`.

**DEĞİŞMEZ (biçim):** `rects_from_mss_monitors`, bu makinede ölçülmüş ham listeyi doğru çevirir:
```
[{'left':-2560,'top':0,'width':5120,'height':1440},
 {'left':-2560,'top':0,'width':2560,'height':1440,'is_primary':False,'name':...,'unique_id':...},
 {'left':0,'top':0,'width':2560,'height':1440,'is_primary':True,...}]
-> (Rect(-2560,0,2560,1440,monitor_index=0,dpi_scale=1.0), Rect(0,0,2560,1440,monitor_index=1,dpi_scale=1.0))
```
**ÖLÇÜ:** `test_monitors.py::test_k5_gercek_duzen` — ham liste test dosyasına gömülü. Ayrıca: tek monitör, üç monitör, boş `[1:]` → `()`, boş liste `[]` → `()`.

**DEĞİŞMEZ (yozlaşmış sözlük):** `[1:]` içinde `left/top/width/height` anahtarlarından biri **eksik** ya da değeri **tamsayı değil** → `CaptureError` (mesajda hangi indeks, hangi anahtar). Tamsayı **testi**: `isinstance(v, numbers.Integral) and not isinstance(v, bool)` — `int` ve `numpy.int64/int32/uint8` **kabul**, `bool`/`np.bool_`/`None`/`str`/`float` **ret**. (Gerçek `mss` düz `int` verir — şef ölçtü; `numpy` tamsayıları DXGI görevi ve numpy tabanlı sahte backend'ler için kabul edilir. `np.bool_` `Integral` **değildir**, ayrıca elemeye gerek yok — şef ölçtü.)

**DEĞİŞMEZ (düzleştirme — Y-C):** Kabul edilen değer `Rect`'e yazılmadan **`int(v)` ile düzleştirilir**; `Rect` alanlarına **hiçbir zaman** numpy skaleri yazılmaz. `typing.cast(int, v)` ile `mypy`'yi susturmak **yasaktır**. Gerekçe (şef ölçtü): `isinstance(v, numbers.Integral)` `object`'i `Integral`'a daraltır, `int`'e değil — `return v` `mypy --strict`'i kırar (kabul #1), `cast(int, v)` ise mypy'yi geçer ama numpy skalerini `Rect`'e sızdırır ve **eşitlikle görülemez**: `Rect(np.int64(10),…) == Rect(10,…)` → `True`, hash eşit, `right`/`bottom` aritmetiği doğru. Zarar `Rect` serileşince çıkar: `json.dumps(asdict(rect))` → `TypeError: Object of type int64 is not JSON serializable`. (Ayrıca `np.uint64 - np.int64 → float64`; karışık işaretli aritmetikte `w` float olur.) **Durum değişmezi:** `refresh_monitors()` bozuk sözlükte fırlattığında servisin **eski** monitör kümesi **değişmeden kalır** (atama yalnızca başarılı dönüşümden sonra). Bu, `list_monitors` üzerinden **yapımda** (`CaptureService.__init__`) ve `refresh_monitors()`'ta da fırlar — K6 taksonomisi yalnızca yakalama çağrılarını kapsar; yapım hatası ayrı ve burada tanımlı.
**ÖLÇÜ:** `test_monitors.py::test_k5_bozuk_sozluk_*` — her vaka (`None`/`str`/`float`/`bool`/`np.bool_`/eksik anahtar ret; `np.int64`/`np.int32`/`np.uint8` kabul); **`test_monitors.py::test_k5_numpy_tamsayi_duz_int_e_duzlestirilir` — `type(r.x) is int and type(r.y) is int and type(r.w) is int and type(r.h) is int`**, **`np.int64`/`np.int32`/`np.uint8`/`int` üzerinden parametrelenir** (§4.6/7 ve Y5-6: kabul ölçüsü dört tipte koşuyorsa düzleştirme ölçüsü de koşmalı — yalnız `int64`'ü düzleştiren bir uygulama tek tipli ölçüyü geçer ve `int32`/`uint8`'i sızdırır). Eşitlik ölçüsü **yetmez**, yukarıdaki gerekçe; `test_service.py::test_k5_yapimda_bozuk_sozluk`; `test_service.py::test_k5_refresh_hatasi_eski_kumeyi_korur`.

**DEĞİŞMEZ (`union_bbox`):** dönen `Rect`, kümedeki her monitörü **kapsar** ve bundan **daha büyük değildir** (`x=min(x)`, `y=min(y)`, `right=max(right)`, `bottom=max(bottom)`); `monitor_index=-1`, `dpi_scale=1.0` ("birleşim, tek monitör değil" işareti — K8'in `-1`'iyle aynı anlam). Sıraya duyarsız.
**ÖLÇÜ:** `test_monitors.py::test_k5_union_bbox_*` — negatif x'li iki monitör (→ `Rect(-2560,0,5120,1440,-1,1.0)`), üç monitör, L düzeni, tek monitör (→ aynı geometri, `monitor_index=-1`), ters sıra aynı sonuç, boş → `None`.

**DEĞİŞMEZ (okuma zamanı):** `CaptureService` monitör kümesini **yalnızca** `list_monitors(self._backend)` ile, **yalnızca** yapımda ve `refresh_monitors()` içinde okur. `capture_region`/`capture_full` `backend.monitors()`'ı **hiç** çağırmaz.
**ÖLÇÜ:** `test_service.py::test_k5_monitors_cagri_sayaci` — 100 `capture_region` sonrası `FakeBackend.monitors` sayacı **1**; `refresh_monitors()` sonrası **2**.

**DEĞİŞMEZ (sıra değişimi):** `refresh_monitors()` sonrası monitör **sırası** değişirse, aynı PARTIAL `rect`'in kırpılmış geometrisi **değişmez** (kırpma birleşime göredir, sıraya duyarsız — şef ölçtü); değişen yalnızca `Frame.rect.monitor_index`'tir. Bu, K5'in konumsal-kimlik eksikliğinin görünür yüzüdür.
**ÖLÇÜ:** `test_service.py::test_k5_sira_degisimi_kirpmayi_degistirmez_metadatayi_degistirir`.

Boş monitör kümesi → servis **kurulur**, her `capture_region`/`capture_full` `CaptureError`, backend çağrısı 0.

**Kabul edilen eksiklik — `known_gaps`'e ve docstring'e:** monitör kimliği **konumsal ve kararsız**. `mss` `is_primary`/`unique_id` veriyor; `Rect` taşıyamıyor. Düzen değişiminde eski `Rect`'ler sessizce başka monitöre işaret edebilir. §5.6'nın "şeridi birincil monitöre taşı" satırı, `Rect`'e kimlik alanı eklenmeden uygulanamaz — şef bunu v1 kapsamı dışına aldı; A7 için sözleşme değişikliği adayı.

## K6 · Yeniden deneme — üç sınıf, üçü de sayılı

| Sınıf | Backend çağrısı | Yeniden deneme | `seq` | `__cause__` |
|---|---|---|---|---|
| (a) K4 doğrulama hatası | **0** | yok | tüketmez | `None` |
| (b) backend **istisna** fırlattı | en fazla **3** | evet, 3'e kadar | tüketmez | son backend istisnası |
| (c) backend döndü ama çıktı **geçersiz** (K7) | **doğrulama başına 1** | **yok** | tüketmez | `None` |

**DEĞİŞMEZ:** (b)'de üçüncü başarısızlıktan sonra `CaptureError`; mesajı `rect` değerlerini ve deneme sayısını içerir. İlk denemede başarılıysa **tam 1** çağrı. **Karışık dizi:** 1. deneme istisna (b), 2. deneme geçersiz çıktı (c) → toplam **2** çağrı, `CaptureError`, `__cause__ is None` (son olay (c)); geçersiz çıktıdan sonra **yeniden denenmez**.
**ÖLÇÜ:** `test_service.py::test_k6_*` — 3×3 matris: {a, b, c} × {çağrı sayısı, `seq`, `__cause__`} + `test_k6_karisik_b_sonra_c` + `test_k6_b_sonra_basari` (1. istisna, 2. başarı → 2 çağrı, `seq` tüketilir). Hiçbir hücre boş kalmayacak.

## K7 · Görüntü biçimi ve sahiplik

**Şefin ölçümü (mss 10.2.0, `sef_dogrulama/olgular.txt`):** `grab()` her çağrıda **yeni** `bytearray` ayırır — ardışık grab'ler bellek **paylaşmaz**. Ama `np.asarray(ScreenShot)` o `bytearray`'i **takma adlar** ve dizi `writeable`'dır: kopyalanmazsa `Frame.image` üzerinde yerinde bir değişiklik backend nesnesini bozar. Kopya **koşulsuz** — 3 kanalda da, 4 kanalda da. (`np.ascontiguousarray(arr[:, :, :3])` 4 kanalda kopyalar ama **3 kanalda takma ad döndürür** — şef doğruladı; bu yüzden iki kanal sayısı ayrı ölçülür.)

**DEĞİŞMEZ:** `Frame.image.shape == (frame.rect.h, frame.rect.w, 3)`, `dtype == uint8`, **BGR**. Backend BGRA verirse alfa atılır. Backend'in döndürdüğü şey `np.ndarray` **değilse**, dizisi bu boyutla uyuşmuyorsa, `ndim != 3` ise, kanal 3/4 değilse, ya da `dtype != uint8` ise → `CaptureError` (sınıf c: sessiz dönüşüm yok, yeniden deneme yok).
**ÖLÇÜ:** `test_service.py::test_k7_bicim_*` — her bozuk biçim için ayrı vaka. **`np.ndarray` değil** değişmezinin ayrışma girdisi (Y5-4, §4.6/4): sayılan üç doğal girdi (liste / `memoryview` / `None`) bu değişmezi **ölçmez** — `np.asarray` onları sessizce dönüştürse bile `ndim` sırasıyla 2/1/0 çıkar ve aynı `CaptureError` doğar (şef ölçtü). Ayırt eden tek girdi **`__array_interface__` taşıyan bir nesne**: `np.asarray` onu `(h,w,4) uint8` olarak **sessizce kabul eder** (şef ölçtü) — ve gerçek `mss.ScreenShot` tam olarak böyle bir nesnedir. **Kural TİP DÜZEYİNDEDİR, girdi sayarak yazılmaz (Y7-6):** `isinstance(arr, np.ndarray)` **değilse** `CaptureError`; hiçbir `np.asarray` / `np.array` / `hasattr` dönüşümü yapılmaz. Girdi **sayan** bir kural kaçınılmaz olarak **anahtar deliği** açar — KRT en az **dört** ayrışan biçim ölçtü: `__array_interface__` taşıyan nesne, `__array__` metotlu nesne, 3 boyuta `cast` edilmiş `memoryview`, `__buffer__` (PEP 688) taşıyan nesne; dördü de `np.asarray` ile `(h,w,4) uint8` verir, ve v7'nin zorunlu kıldığı **iki** girdiyi `hasattr` ile reddedip gerisini çeviren bir uygulama beş kapıdan da geçiyor. (Şef ölçtü: `__array_interface__` ve `__array__` sessizce kabul ediliyor; sayılan liste/`memoryview`/`None` üçlüsü ise `ndim != 3`'ten zaten düşüyor, yani ayırt etmiyor.) **ÖLÇÜ:** `test_k7_bicim_donusum_yok` bu **dört** girdiyi birlikte parametreler; üçünü reddedip birini çeviren uygulama dördüncüde düşer.

**DEĞİŞMEZ:** `Frame.image`, backend'in döndürdüğü diziyle bellek **paylaşmaz** ve `writeable`'dır (kopya).
**ÖLÇÜ:** `test_service.py::test_k7_sahiplik_3kanal`, `test_k7_sahiplik_4kanal` **ve `test_k7_sahiplik_salt_okunur_kaynak`** (`np.frombuffer(bytes(...))` → `writeable=False` üretici; gerçek `mss` yolunda `np.frombuffer(shot.bgra, …)` bunu üretir) — üçünde ayrı ayrı: `np.shares_memory(frame.image, backend_dizisi) is False`, `frame.image.flags.writeable is True`; `frame.image`'ı yerinde bozup backend dizisinin değişmediği; backend dizisini bozup önceki `Frame`'in değişmediği. (Salt-okunur vaka olmadan `writeable` iddiasının bağımsız ayırt etme gücü yoktur — onu kıran her uygulama `shares_memory` iddiasını da kırar.)

## K8 · `Frame.rect` metadata'sı

**Şefin ölçümü:** `mss` monitör sözlükleri **DPI ölçeği taşımaz** (anahtarlar: `left/top/width/height/is_primary/name/unique_id`). Servisin monitör kümesindeki her `Rect`'in `dpi_scale`'i bu yüzden **daima 1.0**'dır (K5). Servis ölçeği **bilemez**; tek olası kaynak çağırandır (A7'nin Qt'den aldığı `devicePixelRatio`). **İkinci ölçüm (`[Y-B]`):** `dpi.intersect(rect, union_bbox)` dönen `Rect`'in `dpi_scale`'i ve `monitor_index`'i **ikinci argümandan** gelir — PARTIAL kırpmasında çağıranın 1.5'i `union_bbox`'ın 1.0'ına ezilir. Bu yüzden `Frame.rect` **hiçbir zaman** `intersect` çıktısının metadata'sıyla kurulmaz; geometri `intersect`'ten, metadata aşağıdaki kurallardan.

**DEĞİŞMEZ (geometri):** `Frame.rect.x, y, w, h` = backend'in **gerçekten yakaladığı** dikdörtgen (kırpma olduysa kırpılmış).

**DEĞİŞMEZ (`dpi_scale`):** `Frame.rect.dpi_scale`, `capture_region`'da çağıranın verdiği `rect.dpi_scale`'dir — **INSIDE ve PARTIAL yollarında aynı**; servis bu değeri **okur ve olduğu gibi taşır**, hiçbir karar için kullanmaz (K3/K4). `capture_full(i)` → `monitors[i].dpi_scale`, yani `1.0`.
**ÖLÇÜ:** `test_service.py::test_k8_dpi_scale_korunur_inside` **ve** `test_k8_dpi_scale_korunur_partial` — ikisi ayrı ayrı, `dpi_scale=1.5` ile; PARTIAL vakası gerçek negatif düzende sol taşma (`Rect(-2600,0,100,100,dpi_scale=1.5)` → `Frame.rect == Rect(-2560,0,60,100,monitor_index=0,dpi_scale=1.5)`); `test_k8_capture_full_dpi_scale_1_0`.

**DEĞİŞMEZ (`monitor_index`):** çağıranın verdiği değer **yok sayılır**. Yakalanan (kırpılmışsa kırpılmış) dikdörtgenle **pozitif alanlı kesişimi olan** monitör sayısı **tam 1** ise o monitörün indeksi — bölge o monitörün tamamen içinde olmasa da (L düzeninde ölü alan içerebilir, K4); **0 ya da 1'den fazla** ise `-1` ("tek monitöre atfedilemez" işareti, `union_bbox`'ın `-1`'iyle aynı anlam).
**ÖLÇÜ:** `test_service.py::test_k8_monitor_index_*` — INSIDE yolunda çağıranın 7'sine rağmen gerçek monitör; PARTIAL kırpması sonrası tek monitöre düşen bölge (üst taşma `Rect(100,-50,100,100)` → kırpık `(100,0,100,50)` → `1`); iki monitöre yayılan → `-1`; **L düzeni** (`A=(0,0,100,100)`, `B=(100,100,100,100)`, bölge `Rect(90,50,20,20)` → yalnız A ile kesişir → `0`); `capture_full(i)` → `i` (**monitörler örtüşmez** varsayımı altında — `dpi.classify_region`'ın belgelediği varsayım; klon/iç içe düzende kural gereği `-1` döner, Windows klon modu tek monitör bildirdiği için üretimde erişilemez).

**DEĞİŞMEZ (düzleştirme, ikinci yol — Y5-2):** `Frame.rect`'in `x, y, w, h` alanları da **düz `int`**'tir. Servis, çağıranın `rect`'ini `Frame.rect`'e geçirirken (INSIDE yolu) ve `dpi.intersect` çıktısını kullanırken (PARTIAL yolu) `int()` uygular. Gerekçe (şef ölçtü): çağıran `Rect(np.int64(10), …)` verirse `Frame.rect` alanları `['int64','int64','int64','int64']` olur; PARTIAL yolunda `dpi.intersect` **karışık** üretir (`['int','int64','int64','int64']` — `x` düzleşir çünkü `max()` Python `int`'ini seçer); ikisinde de `json.dumps(asdict(frame.rect))` → `TypeError`. Ayrıca `np.uint64` ile `np.int64` karışımında `w` **`float64`** olur.
**Düzleştirme `capture_region`'ın GİRİŞİNDE yapılır (Y6-6), `Frame.rect` kurulumunda değil:** servis, çağıranın `rect`'ini doğrulamadan **önce** `Rect(int(rect.x), int(rect.y), int(rect.w), int(rect.h), rect.monitor_index, float(rect.dpi_scale))` biçiminde yeniden kurar; `dpi.classify_region`, `dpi.intersect` ve `monitor_index` hesabı **yalnız düzleştirilmiş** `Rect` görür. Gerekçe (şef ölçtü): işaretsiz numpy tamsayılarında **dondurulmuş `dpi.py`** taşıyor — `np.uint16`/`np.uint32` ile `Rect(10,10,100,50)` `classify_region`'da `inside` yerine **`partial`** çıkıyor ve üç `RuntimeWarning: overflow encountered` doğuyor; yani `monitor_index` sessizce yanlış oluyor. `dpi_scale` de `float()` ile düzleştirilir: `np.float64` `float` alt sınıfı olduğu için serileşir ama **`np.float32` serileşmez** (şef ölçtü).
**Düzleştirme bir DÖNÜŞÜMDÜR, doğrulama değil (Y7-3) — önüne kabul kapısı konur:** `capture_region`, `x, y, w, h`'nin her biri için `isinstance(v, numbers.Integral) and not isinstance(v, bool)` **ya da** (`float`/`np.floating` **ve** `float(v).is_integer()`) koşulunu arar; sağlanmıyorsa `CaptureError` (mesajda alan adı ve ham değer). Gerekçe (şef ölçtü): çıplak `int()` `10.9`'u sessizce `10` yapıyor (v6'da bu `CaptureError: boyut uyusmuyor` ile **gürültülü** düşerdi), `'10'` ve `True`'yu sessizce kabul ediyor — oysa K5 aynı değerleri monitör sözlüğünde **açıkça reddediyor** — ve `inf`/`nan` için K6 taksonomisi dışında `OverflowError`/`ValueError` fırlatıyor. **ÖLÇÜ:** `test_k8_giris_tamsayi_olmayan_reddedilir` — `'10'` / `True` / `10.9` / `float('nan')` / `float('inf')` / `np.float32(10.5)` her biri **`CaptureError`**; `10.0` ve `np.float64(10.0)` **kabul** (tam sayı değerli float).

**ÖLÇÜ:** `test_service.py::test_k8_frame_rect_alanlari_duz_int` — **`np.int64`/`np.int32`/`np.uint8`/`int` üzerinden parametreli** (Y6-5, §4.6/7: K5'in düzleştirme ölçüsü dört tipte koşuyorsa K8'inki de koşmalı), her tipte **INSIDE + PARTIAL** yolları — bu iki nokta ayrıştırıcıdır; `type(f.rect.x) is int and … is int`, `type(f.rect.dpi_scale) is float`, ve `json.dumps(asdict(f.rect))` istisnasız. **`capture_full` bacağı bu ölçüde `[ÖLÇÜLMÜYOR]` (Y7-8):** o yolun `rect`'i K5'in zaten düzleştirdiği monitör kümesinden gelir, numpy skaleri oraya **ulaşamaz**; ölçüm noktası ihlal edilemediği için ayırt etme gücü sıfırdır (KRT ölçtü: düzleştirmeyi yalnız `capture_full`'da atlayan uygulama beş kapıdan da geçiyor). `capture_full`'un kendi ölçüsü `test_k8_monitor_index_capture_full[i]`'dir. Ayrıca `test_k8_monitor_index_isaretsiz_numpy` — `np.uint16`/`np.uint32` ile INSIDE bölgede `monitor_index` doğru monitörü verir (taşma yok).

**`known_gaps`'e ve docstring'e zorunlu:** "Servis DPI ölçeğini üretemez; `Frame.rect.dpi_scale` çağıranın beyanıdır, `capture_full` için `1.0`'dır. Ölçek bilgisi A7'de (Qt `devicePixelRatio`) üretilir ve `Rect`'e çağıran tarafından yazılır. `dpi.intersect` çıktısının metadata'sı **kullanılmaz** (ikinci argümandan gelir)."

## K9 · `capture_full` ve sanal masaüstü

**DEĞİŞMEZ:** `capture_full(i)`, `capture_region(monitors[i])` ile **aynı backend çağrısını** üretir (backend'e giden `x,y,w,h` birebir aynı) ve dönen `Frame`'in `rect`'i, görüntü içeriği (`np.array_equal`) ve — enjekte sabit saatle — `captured_at`'i birebir aynıdır. `seq` K2 gereği **artar**; `Frame` **eşitliği beklenmez** (`seq` karşılaştırmaya dahil). `i` aralık dışı (negatif dahil) → `CaptureError`, backend çağrısı 0.
**ÖLÇÜ:** `test_service.py::test_k9_capture_full_ayni_rect_ve_ayni_grab_cagrisi`, `test_k9_aralik_disi`.

Sanal masaüstünün tamamı `capture_region(union_bbox(monitors))` ile yakalanır (`INSIDE`); `capture_full` yalnızca tek monitörü hedefler. Docstring'de.

## K10 · `mss` API'si, ömrü ve yan etkileri

**Şefin ölçümü:** `mss.mss()` **kullanımdan kalkmış** (`DeprecationWarning`, mss 10.2.0); doğru giriş `mss.MSS()`. `mss.MSS.monitors` **örnek üzerinde memoize** (`_monitors`) — aynı örnekten tekrar okumak bayat liste verir. `mss.MSS()` kurulumu **process genelinde** DPI awareness'ı `0 → 2` (`PER_MONITOR_DPI_AWARE`) yapar ve geri alınamaz. **`mss`'te `__del__` yok**: kapatılmayan her `MSS()` örneği bir window DC + memory DC sızdırır; **5001. kapatılmamış örnekte `GetWindowDC` kalıcı olarak başarısız olur** (şef ölçtü; `with` ile 12.000 örnek sorunsuz).

**DEĞİŞMEZ (canlılık + kapatma):** `MssBackend.monitors()` her çağrıda **canlı** kümeyi döndürür: her çağrıda yeni bir `mss.MSS()` kurar, ham `monitors` listesini **olduğu gibi** (`[0]` birleşim girdisi dahil) döndürür. **Kopyalama ayrı bir değişmez DEĞİLDİR (Y7-2):** gerçek `mss` `monitors`'ı örnek üzerinde memoize eder ve K10 her çağrıda **yeni** `MSS()` kurulmasını şart koştuğu için, dönen listeyi bozmanın sonraki çağrıya etkisi **yoktur** — şef ölçtü: bir örneğin listesini bozmak başka bir örneği etkilemiyor. `dict(m)` kopyası önerilir ama **kapı değildir**; ölçülen değişmez **canlılıktır** (§3 `m2_len`). *(v7 buraya "ÖLÇÜ: §3 casusu dönen listeyi bozar…" cümlesi yazmıştı; `headless_check`'te böyle bir denetim **yoktu** — şef doğruladı, `m1` yalnızca okunuyor. §4.6/2 ve /3 ihlaliydi, geri çekildi.)* ve **dönmeden önce kapatır** (`with mss.MSS() as s:`). Çağrı başına **tam 1** kurulum, **tam 1** kapatma.
**DEĞİŞMEZ (uzun ömürlü tutamaç):** `grab` için ayrı bir `mss.MSS()` **tembel** kurulur — **ilk `grab()` çağrısında**, `__init__`'te değil. `__init__` `mss`'e dokunmaz (bu yüzden K1 engeli altında kapsanabilir; K13). `MssBackend.close()` bu tutamacı kapatır, **idempotent**tir (ikinci çağrı sessiz); `MssBackend` bağlam yöneticisidir (`__enter__` self, `__exit__` → `close()`).
**DEĞİŞMEZ:** `MssBackend` `mss.mss()`'i **hiç** çağırmaz, `mss.MSS()`'i çağırır.
**ÖLÇÜ:** `headless_check.py` §3 — alt-süreçte `sys.modules["mss"]`'e **casus modül** koyar; casus `ScreenShot` gerçek `mss` gibi `__array_interface__['data']`'ya **tampon nesnesinin kendisini** (`bytearray`) verir ve `raw`/`bgra` alanlarını **desenli** (`01 02 03 FF` tekrarı) doldurur. Ölçülenler: (0) `grab()` dönüşünün **her pikseli** casusun verdiği baytların kendisidir — 4 kanalda `[1,2,3,255]`, 3 kanalda `[1,2,3]` (ekranı okumayan ya da kanal sırasını çeviren `grab` burada düşer); (1) `MssBackend()` yapımı → `MSS` sayacı **0**; (2) `monitors()` iki kez → sayaç her çağrıda **+1**, `close`/`__exit__` sayacı her çağrıda **+1**, `mss.mss` sayacı **0**; (3) dönen liste casusun ham listesine **eşit** (`len==3`, `[0]` dahil); (4) iki çağrı arasında casusun listesi değiştirilir, ikinci çağrı **yeni** listeyi görür (canlılık); (5) `grab` casus `MSS.grab`'i `{'left','top','width','height'}` sözlüğüyle çağırır ve gönderilen sözlük **çağıranın `Rect`'inin birebir kendisidir** — bu **en az iki noktada** ölçülür: `Rect(10,20,64,16)` **ve `Rect(-2600,-50,64,16)`** (negatif sanal-masaüstü koordinatı; bu makinenin gerçek düzeninde sol monitör `x=-2560`'ta). Kırpan/kaydıran bir dönüşüm yalnız ikinci noktada düşer (Y7-1, şef doğruladı), ilk `grab`'de tam 1 kurulum, ikinci `grab`'de **0** yeni kurulum (uzun ömürlü); (6) `close()` iki kez → kapatma sayacı +1, ikinci çağrı sessiz. (Test paketi bunu ölçemez, K1 gereği.)

**DEĞİŞMEZ (tembel import):** `service.py` ve `monitors.py` modül yüklenirken `mss`'i import etmeye **hiç kalkışmaz** (try/except içinde bile); çalışma zamanı `import mss` yalnızca `MssBackend`'in metot gövdesi içinde. `if TYPE_CHECKING: import mss` (ya da `TYPE_CHECKING` takma adıyla) **serbesttir** — yalnızca `if` gövdesinde, `else` dalında değil; tutamaç tipi `mss.base.MSSBase | None` ya da `object | None` — implementer seçer, docstring'e yazar.
**ÖLÇÜ:** `headless_check.py` §2 — AST: `TYPE_CHECKING` gövdesi dışındaki her `import mss` bir `FunctionDef` gövdesi **içinde**; alt-süreçte `sys.meta_path`'e kayıt tutan bir bulucu konur ve iki modül import edilirken `mss` için **hiçbir import girişimi** kaydedilmez (try/except ve `importlib` kaçışlarını da yakalar).

**`known_gaps`'e ve docstring'e zorunlu:** "Process içindeki **ilk** `mss.MSS()` kurulumu — `MssBackend`'in ilk `monitors()` veya `grab()` çağrısı — process DPI politikasını kalıcı olarak `PER_MONITOR_DPI_AWARE` yapar ve Qt'nin ölçeklemesini etkiler. `MssBackend` metotları `QApplication` kurulmadan **önce** çağrılmamalıdır. (`MssBackend()` yapımı zararsızdır.)" Bu A6/A7 için entegrasyon kısıtıdır.

## K11 · Performans bütçesi — alanı belirtilmiş, aşım bilgisi zorunlu

**DEĞİŞMEZ:** `FakeBackend` (`Rect(0,0,600,200)`, backend `(200,600,4)` döndürür) ile 200 çağrının **medyanı ≤ 10 ms ve p95'i ≤ 10 ms** — servisin **kendi ek yükü** (doğrulama + kırpma + kopya + `Frame` kurma). Test `assert` eder. Şefin beklentisi ~0.4 ms; bu test duman testidir, asıl sıcak-yol koruması K5'in çağrı sayacıdır.
**ÖLÇÜ:** `test_service.py::test_k11_butce`; ham sayılar `evidence/budget.txt`.

**Şefin ölçümü (`olgular.txt`):** gerçek `mss.grab` medyanı **13.5 ms**, 600×200 ve 100×50 için aynı — **bölge boyutundan bağımsız sabit maliyet**. §5.7'nin "Capture ≤ 10 ms" bütçesi `mss` ile **şimdiden aşılıyor**. Bu T-005'in kapsamı dışıdır ve **`known_gaps`'e zorunlu** yazılır; şef DXGI Desktop Duplication için ayrı görev açar. T-005 bu yüzden reddedilmez.

## K12 · Thread güvenliği **[ÖLÇÜLMÜYOR]**

`CaptureService` thread-safe değildir; tek worker thread'den kullanılır (§5.5). Docstring'de. Test yok — eşzamanlılık testi A6'nın (pipeline) kapsamı.

## K13 · Kapsam

**ÖLÇÜ:** dördüncü kabul komutu — `service.py` + `monitors.py` satır kapsamı ≥ %95 (`--cov=src.capture.service --cov=src.capture.monitors`; şef doğruladı: noktalı modül adı ölçer, dosya yolu %0 ölçer). `# pragma: no cover` yalnızca `MssBackend.monitors`, `MssBackend.grab` ve `MssBackend.close` **gövdelerinde**; her işaretin yanına `# K1: gercek ekran, headless_check §3 ile denetleniyor` yorumu. `MssBackend.__init__`/`__enter__`/`__exit__` pragma **almaz** (K10: tembel, `mss`'e dokunmaz, testte kapsanır). Başka `no cover` **yasak** — bu **şefin elle denetlediği** bir kuraldır, kapsam eşiği onu göremez (KRT ölçtü: fazladan pragma ile kapsam %97'ye çıkıyor ve komut yine exit 0). Yapısal olarak erişilemez savunma satırları (PARTIAL dalında `union_bbox is None` / `intersect is None`, K8'in "0 monitörle kesişir" dalı) pragma **almaz**; kapsanmadan da eşik tutar. **Sayı değil yön yazılır** (test kümesi büyüdükçe her mutlak sayı bayatlar): fazladan pragma kapsamı **yükseltmez, düşürür** (KRT ölçtü: %98.59 → %98.52) — mekanizma yine de geçerli, eşik onu görmez.

**Beşinci kabul komutu (yeni):** `tests/unit/capture` dizininin tamamı — `conftest.py` aynı dizindeki dondurulmuş `test_dpi.py` + `test_change_detector.py`'yi (**583 test** — şef saydı) de etkiler; regresyon burada görünür.

---

# Yozlaşmış girdiler — hepsi test edilecek

`w=0` · `h=0` · negatif `w`/`h` · tamamen dışarıda · boş monitör kümesi · `capture_full` aralık dışı (negatif, `len`) · backend `None` döndürür · yanlış `ndim`/kanal/`dtype` · boyut uyuşmazlığı · **bozuk monitör sözlüğü** (`left` eksik / `left=None` / `width='2560'` / `height=True`) yapımda ve `refresh_monitors()`'ta · `refresh_monitors()` sonrası küme değişti (sayı değişimi: eski bölge artık PARTIAL/OUTSIDE; sıra değişimi: K5 sıra değişmezi) · `refresh_monitors()` bozuk sözlükte fırlatır, eski küme korunur · L düzeninde ölü alana değen bölge (`monitor_index` kuralı K8).

---

# Kanıt etiketleri (PROTOKOL §4.6/6)

Bu pakette **"şef ölçtü"** ibaresi yalnızca şefin kendi eliyle koştuğu kalemlerde kullanılır; kırmızı takımın kanıtına dayanılarak kabul edilenler **"KRT ölçtü"** diye işaretlidir. Ham çıktılar `sef_dogrulama/olgular.txt` altında. Şefin **kendi koşmadığı** ve KRT'ye dayanan kalemler: `raw_override`'ın public öznitelik olması, `# type: ignore` × `warn_unused_ignores` bağı, `K13` fazladan pragma ölçümü, `validate.py`'nin `commands` sayısını denetlememesi. KRT'nin "%68 tek renkli blok" sayısı şefin örnekleminde **yeniden üretilemedi** ve hiçbir yerde "şef ölçtü" diye geçmez.

**Elle denetlenen kapılar (makine görmez — şef denetler):** `known_gaps` içeriği, "başka `no cover` yasak", `commands` altında beş komut bulunması. `validate.py` üçünü de denetlemez (KRT ölçtü: `known_gaps: []` ve tek komutlu bir `delivery.md` exit 0 alıyor).

# Kararlarını İKİ YERE yaz

Tester `known_gaps`'i okumaz. Her karar hem **docstring'e** hem `delivery.md` **`known_gaps`** alanına. K2/K5/K8/K10/K11'in "zorunlu `known_gaps`" maddeleri **eksikse teslim reddedilir** — bu **şefin elle denetlediği** bir kapıdır: `validate.py` `known_gaps` **içeriğini** denetlemez (KRT ölçtü: `known_gaps: []` içeren tam bir `delivery.md` exit 0 alıyor). Kabul komutlarının ham çıktıları `.agents/tasks/T-005/evidence/` altına yazılır ve `files_written`'da **beyan edilir** — dizin `owns` kapsamındadır.

# Diğer kısıtlar

- `src/capture/__init__.py` şefe ait — dokunma. (Docstring'i "alt modüller doğrudan import edilir" der; bu **paketin dışından** import biçimidir. Paket **içinde** kardeşler relatif import edilir — yukarıdaki "Import biçimi".)
- **Qt yok** `owns` kapsamındaki **beş** dosyada da (`headless_check` §4 beşini tarar).
- `mss` dışında yeni bağımlılık yok. `pytest-cov` Ortam Ajanı tarafından kuruldu.
- Dondurulmuş: `src/contracts/`, `src/capture/dpi.py`. Eksik → `contract_change_request: true`.
- `headless_check.py` §1 çalışırken `tests/unit/capture/` altına `_hc_probe_k1_a.py`, `_hc_probe_k1_b.py` ve `_hc_probe_store.py` geçici dosyalarını yazıp siler (`__pycache__` altında `.pyc` artıkları kalabilir — zararsız); bu adlar **owns dışıdır**, implementer böyle dosyalar yazmaz.

# Yöntem ve teslim

TDD; kırmızı faz `evidence/pytest-red.txt`. **Beş** kabul komutunu gerçekten çalıştır, ham çıktı `.agents/tasks/T-005/evidence/` (`mypy.txt`, `pytest.txt`, `headless.txt`, `cov.txt`, `pytest-capture-all.txt`). Bütçe `evidence/budget.txt`.

`.agents/tasks/T-005/delivery.md`, `task: T-005`, `round: 1`, PROTOKOL §4 şeması; `commands` altında beş komut.

PROTOKOL §6 geçerli. Dokümanın sessiz kaldığı yerde verdiğin her kararı bildir.
