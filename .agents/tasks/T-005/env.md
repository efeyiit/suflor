# Koşum Ortamı — T-005 (CaptureService)

Ortam Ajanı ürünü. **Dört tester** var; her biri farklı mercekle çalışır ve **kendi raporunu ayrı yazar**. Birleştirilmiş özet yoktur. Diğerlerinin varlığından habersizsin.

## Doğrulanmış ortam

| | |
|---|---|
| Python | 3.12.10 · pytest 9.1.1 · pytest-cov · mypy · numpy 2.4.6 · mss 10.2.0 |
| Çalışma dizini | depo kökü |
| Ekran | iki monitör: `M0 = (-2560, 0, 2560, 1440)` (birincil **değil**), `M1 = (0, 0, 2560, 1440)` (birincil) |
| Yapılandırma | depoda `pytest.ini`/`pyproject.toml` **yok**; `tests/unit/capture` bir paket değil |

**Testlerin gerçek ekrana dokunamaz** (K1): `conftest.py`'nin oturum kapsamlı engel fixture'ı `sys.modules["mss"]`'e bir engel modül koyar ve `mss.MSS()` çağrısı `AssertionError` verir. Bu bilinçlidir — CI'da ekran yok, ve gerçek `mss.MSS()` process DPI politikasını **geri alınamaz** biçimde değiştirir.

## Koşum komutları

```bash
python -m mypy --strict --explicit-package-bases src/capture/service.py src/capture/monitors.py
python -m pytest tests/unit/capture/test_service.py tests/unit/capture/test_monitors.py -q
python .agents/tasks/T-005/headless_check.py
python -m pytest tests/unit/capture/test_service.py tests/unit/capture/test_monitors.py -q --cov=src.capture.service --cov=src.capture.monitors --cov-fail-under=95 --cov-report=term-missing
python -m pytest tests/unit/capture -q
```

Kendi testlerin:
```bash
python -m pytest .agents/tasks/T-005/tester_<MERCEK>/ -q
```

## Okumaman gerekenler

- `.agents/tasks/T-005/delivery.md` — **okuma**
- `.agents/tasks/T-005/evidence/` — **okuma**
- Diğer tester dizinleri — **okuma**

Okuyabileceğin ve **okuman gereken**: `packet.md`, `src/capture/service.py`, `src/capture/monitors.py`, `tests/unit/capture/` altındaki test dosyaları, dondurulmuş `src/capture/dpi.py` ve `src/contracts/`, ve `sef_dogrulama/olgular.txt` (şefin ham ölçümleri).

---

# Neden DÖRT mercek (PROTOKOL §4.5 gerekçesi)

Varsayılan üçtür. Şef dörde çıkardı ve gerekçesi ölçümdür: T-005'in paketi implementer'a gitmeden **yedi kırmızı takım turundan** geçti ve 106'dan fazla bulgu verdi, 18'i yüksek. Bulguların dağılımı üç değil **dört** ayrı hata yüzeyi gösterdi:

| Yüzey | Ölçülen örnek |
|---|---|
| numpy sahiplik / takma ad | `np.ascontiguousarray(a[:,:,:3])` 4 kanalda kopyalıyor, **3 kanalda takma ad** veriyor |
| sayısal tip | işaretsiz numpy dondurulmuş `dpi.py`'de **taşıyor**, `classify_region` `inside` yerine `partial` veriyor |
| durum | `seq` × `refresh_monitors` × üç hata sınıfı × boş monitör kümesi; `refresh` hatasında eski küme korunmalı |
| kapı kalitesi | yedi turun **yüksek bulgularının çoğu kapıların kendisindeydi** — ölçü var görünüp hiçbir şey ölçmüyordu |

Dördüncü mercek (D) bu sonuncusu içindir ve bu görevde en pahalı sınıftır. Azaltma yok, artırma var; §4.5 artırmayı yasaklamıyor.

**Dört tester'dan biri ret verirse görev reddedilir.** Onay için dördünün de onayı gerekir.

---

# MERCEK A — Takma ad (view/copy, paylaşılan mutable durum)

*Docstring "kopya" diyor; gerçekten kopya mı, yoksa bir görünüm mü? Dışarıdan mutasyon neyi bozuyor?*

Somut saldırı noktaları:

1. **`Frame.image` sahipliği dört yönde.** 3 kanal × 4 kanal, yazılabilir kaynak × **salt-okunur** kaynak (`np.frombuffer(bytes(...))` → `writeable=False`; gerçek `mss` yolunda `np.frombuffer(shot.bgra, …)` bunu üretir). Her birinde: `np.shares_memory(frame.image, backend_dizisi) is False`, `frame.image.flags.writeable is True`, `frame.image`'ı yerinde bozup backend dizisinin **değişmediği**, backend dizisini bozup önceki `Frame`'in **değişmediği**. **Şefin ölçtüğü tuzak:** `np.ascontiguousarray(arr[:, :, :3])` 4 kanalda kopyalar, **3 kanalda takma ad döndürür** — yalnız 4 kanallı vakayla yazılmış bir sahiplik testi yeşil kalır.
2. **`monitors()` dönüşü.** Dönen listeyi çağıran bozarsa sonraki çağrı etkileniyor mu? *(K10 bunu bir kapı olarak değil uygulama tercihi olarak yazıyor — gerçek `mss`'te her çağrıda yeni `MSS()` kurulduğu için gözlemlenemez. Yine de `FakeBackend` üzerinden ölç ve gördüğünü yaz.)*
3. **`raw_override` canlılığı.** `fb.raw_override = [...]` ataması `monitors()`'un sonraki çağrısında görünüyor mu? Yapımda anlık görüntü alan bir uygulama burada düşer.
4. **Servisin monitör önbelleği.** `service._monitors` benzeri bir alan dışarıdan bozulursa `capture_region` etkileniyor mu; `refresh_monitors()` hata verdiğinde **eski küme korunuyor** mu (K5 durum değişmezi).
5. **`Rect` ve `Frame` dondurulmuş mu gerçekten** — `dataclasses.replace` dışında bir yol var mı; `Frame.image` `compare=False` olduğu için eşitlik neyi kaçırıyor.

---

# MERCEK B — Sayısal (tip, taşma, düzleştirme)

*Sayılar hangi tipte akıyor; nerede sessizce başka bir şeye dönüşüyor?*

Somut saldırı noktaları:

1. **numpy skaler sızıntısı — eşitlik onu GÖREMEZ.** `Rect(np.int64(10), …) == Rect(10, …)` → **`True`**, hash'ler eşit, `right`/`bottom` aritmetiği doğru. Sızıntıyı yalnız **tip kimliği** görür: `type(r.x) is int`. Ölç: `monitors.py` yolunda ve `Frame.rect` yolunda ayrı ayrı, **`np.int64`/`np.int32`/`np.uint8`/`int` dört tipinde**. Zarar `json.dumps(asdict(rect))` → `TypeError`.
2. **İşaretsiz taşma — dondurulmuş `dpi.py`'de.** Şef ölçtü: `np.uint16`/`np.uint32` ile `Rect(10,10,100,50)` `classify_region`'da `inside` yerine **`partial`** veriyor ve üç `RuntimeWarning: overflow encountered` doğuyor; `monitor_index` sessizce yanlış çıkıyor. `-W error::RuntimeWarning` ile koş.
3. **`dpi_scale` float tipi.** `np.float64` `float` alt sınıfı olduğu için serileşir; **`np.float32` serileşmez**. `type(f.rect.dpi_scale) is float` mi?
4. **Girişteki kabul kapısı.** `'10'`, `True`, `10.9`, `float('nan')`, `float('inf')`, `np.float32(10.5)` → her biri **`CaptureError`** mi, yoksa sessizce kabul mü ediliyor? `10.0` ve `np.float64(10.0)` **kabul** edilmeli. Çıplak `int()` `10.9`'u sessizce `10` yapar ve `inf`/`nan` için K6 taksonomisi dışında `OverflowError`/`ValueError` fırlatır.
5. **`numbers.Integral` daraltması.** `isinstance(v, numbers.Integral)` `int`'e **daraltmaz**; `cast(int, v)` yazan bir uygulama `mypy`'yi geçer ve numpy'yi `Rect`'e sızdırır. Kodda `cast` var mı?
6. **Kırpma aritmetiği.** İki monitöre yayılan `5300w` bölge: tek monitöre kırpma `2560`, **birleşime kırpma `5120`** (doğru). L düzeninde ölü alan.

---

# MERCEK C — Durum makinesi (sıra, sıfırlama, ulaşılamayan durum)

*Çağrı sırası neyi bozuyor; hangi durum hiç test edilmemiş?*

Somut saldırı noktaları:

1. **`seq` tam matrisi.** Başarı / K6 sınıf (a) / (b) / (c) / `refresh_monitors()` dizilerinin **her permütasyonunda** `seq` değeri. K2: üç hata sınıfının **hiçbiri** `seq` tüketmez, `refresh` **sıfırlamaz**, yeni örnek `0`'dan başlar.
2. **K6'nın 3×3 matrisi + karışık diziler.** `{a,b,c} × {çağrı sayısı, seq, __cause__}` — **hiçbir hücre boş kalmasın**. Artı: `b→c` (2 çağrı, `__cause__ is None`), `b→başarı` (2 çağrı, `seq` tüketilir), `b→b→b` (3 çağrı, sonra `CaptureError`).
3. **Boş monitör kümesi.** Servis **kurulur**; her `capture_region`/`capture_full` `CaptureError` ve backend çağrısı **0**. `refresh_monitors()` ile boşa düşüp geri dolma.
4. **`refresh_monitors()` hata yolu.** Bozuk sözlükte fırlatır **ve eski küme korunur** — sonraki `capture_region` eski kümeyle çalışmalı.
5. **Küme değişimi.** Sayı değişimi (eski bölge artık PARTIAL/OUTSIDE olur mu), **sıra değişimi** (kırpma geometrisi **değişmez**, yalnız `Frame.rect.monitor_index` değişir — K5 sıra değişmezi).
6. **`MssBackend` ömrü.** `close()` idempotent mi; `close()` sonrası `grab()` ne yapıyor; `__enter__`/`__exit__` iç içe kullanımda; `monitors()` çağrı başına **tam bir** kurulum + **tam bir** kapatma (kapatmayan uygulama 5001. çağrıda `GetWindowDC` ile kalıcı ölür — şef ölçtü).
7. **`capture_full` indeks aralığı.** Negatif indeks, `len(monitors)`, boş kümede.

---

# MERCEK D — Test kalitesi (kapı gerçekten bir şey ölçüyor mu)

*Bu görevde en pahalı sınıf. Yedi kırmızı takım turunun yüksek bulgularının çoğu **kapıların kendisindeydi**: ölçü var görünüyor, hiçbir şey ölçmüyordu.*

Somut saldırı noktaları — her biri **ölçülmüş** bir kaçış:

1. **Ölçü, denetlediği koddan referans türetiyor mu?** (PROTOKOL §4.6/8) `headless_check` §3 bir zamanlar `grab` dönüşünü **`np.asarray` ile** ölçüyordu — yani K7'nin yasakladığı sessiz dönüşümü denetleyicinin içinde yapıyordu; ham `ScreenShot` döndüren bir `MssBackend.grab` beş kapıdan da geçiyordu. Başka böyle bir yer var mı?
2. **Ölçü mekanizmanın adını mı kancalıyor?** (§4.6/7) Uyum satırları (`_uyum_fake`/`_uyum_mss`) bir mekanizmadır; varlıkları denetlenmezse silen uygulama beş kapıdan geçer. Şimdi `AnnAssign.value`'nun bir **çağrı** olması aranıyor — atlatılabiliyor mu? `grab` dekoratörle sarmalanırsa mypy imzayı `Any`'ye düşürür.
3. **Ölçü parametre uzayının kaç noktasında koşuyor?** §3'ün `grab_args` denetimi bir zamanlar **tek noktada** (hepsi pozitif) ölçüyordu; kutuyu `max(0, …)` ile kırpan bir uygulama bu makinenin **gerçek negatif düzeninde** her yakalamada yanlış piksel verirken beş kapıdan geçiyordu.
4. **Girdi SAYARAK yazılmış kural var mı?** Sayım anahtar deliği açar: K7'nin "`np.ndarray` değilse" değişmezi için en az **dört** ayrışan biçim var (`__array_interface__`, `__array__`, 3B'ye `cast` edilmiş `memoryview`, `__buffer__`); üçünü reddedip birini çeviren uygulama geçer.
5. **Ölçüm noktası ihlal edilebilir mi?** K8'in `capture_full` bacağı yapısal olarak **boştu** — o yolun `rect`'i zaten düzleştirilmiş monitör kümesinden gelir, numpy oraya ulaşamaz. Paket bunu `[ÖLÇÜLMÜYOR]` damgaladı; **başka boş ölçüm noktası** var mı?
6. **Testler totoloji mi?** Her `assert`'i tek tek boz ve testin gerçekten kırıldığını gör. Özellikle: `writeable` iddiasının **bağımsız** gücü var mı (yoksa `shares_memory` onu zaten kapsıyor); K3'ün `==` ölçüsü numpy sızıntısını göremez.
7. **Kapsam yalanı.** `--cov-fail-under=95` fazladan `# pragma: no cover`'ı **görmez** (kapsamı düşürür ama eşiği kırmaz). `MssBackend`'in I/O gövdeleri dışında pragma var mı?
8. **Makinenin görmediği kapılar.** `validate.py` `known_gaps` **içeriğini**, `commands` **sayısını** ve "başka `no cover` yasak" kuralını denetlemiyor. Paket bunları "şef elle denetler" diye işaretliyor — teslimde gerçekten var mı?

---

## Ortak zorunluluklar

- **`FakeBackend` sözleşmesi** `packet.md` K1'de tanımlı: `(monitors, image_factory, raw_override)`. `raw_override` **public öznitelik** ve `monitors()` her çağrıda o anki hâlini okur; `image_factory` `None` döndürürse backend `None` döndürmüş sayılır, istisna fırlatırsa istisna `grab`'den olduğu gibi yayılır.
- **Gerçek ekran yasak.** `MssBackend`'in gövdesini testle koşmaya çalışma; onun kapısı `headless_check.py` §3'ün casus modülüdür.
- **Kanıt zorunlu.** Her komutun ham çıktısı `.agents/tasks/T-005/tester_<MERCEK>_evidence/` altına. Ret veriyorsan `feedback-<MERCEK>.md` **zorunlu** ve `blocking_issues` boş olamaz (`validate.py` denetliyor).
- **Bulduğun her şeyi kendin yeniden üret.** "Şuna benziyor" yetmez; koştuğun kodun ham çıktısını yapıştır.
