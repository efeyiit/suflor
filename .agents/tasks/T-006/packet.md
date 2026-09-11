---
task: T-006
title: "RapidOcrEngine: yerel ONNX OCR motoru (JP/KR/EN/ZH), dil açık, iş parçacığı açık"
role: implementer
level: B
wave: 1
packet_version: 1
owns:
  - "src/ocr/rapid_engine.py"
  - "tests/unit/ocr/test_rapid_engine.py"
  - "tests/unit/ocr/conftest.py"
  - ".agents/tasks/T-006/evidence/**"
  - ".agents/tasks/T-006/delivery.md"
forbidden:
  - "src/contracts/**"
  - "src/capture/**"
  - "src/ocr/normalizer.py"
  - "src/ocr/presets.py"
  - "src/ocr/__init__.py"
  - "tests/unit/ocr/test_normalizer.py"
  - "tests/unit/capture/**"
  - "demo/**"
  - ".agents/tasks/T-006/real_check.py"
  - "diğer tüm dizinler"
depends_on: ["T-001", "T-004", "T-005"]
acceptance:
  - "python -m mypy --strict --explicit-package-bases src/ocr/rapid_engine.py"
  - "python -m pytest tests/unit/ocr/test_rapid_engine.py -q"
  - "python .agents/tasks/T-006/real_check.py"
  - "python -m pytest tests/unit/ocr/test_rapid_engine.py -q --cov=src.ocr.rapid_engine --cov-fail-under=90 --cov-report=term-missing"
  - "python -m pytest tests -q"
budget_ms: 300   # 1200x400, 4 satırlık diyalog kutusu, gerçek model, 8 iş parçacığı (O4: 191-206 ms ölçüldü)
---

# Görev

`OcrEngine` arayüzünün (`src/contracts/interfaces.py`) v1 uygulaması: `Frame` → `list[TextBlock]`. Tasarım §5.1 (bileşen 3), §3.2, §5.7, §6. **Oku.**

**Bu paket ölçüme dayanıyor.** `.agents/tasks/T-006/olgular.txt` — şefin altı ön ölçümü (O1–O6). Her karar oradaki bir olguya bağlı. **Önce onu oku.**

## Ne yazılacak

**`src/ocr/rapid_engine.py`** — `RapidOcrEngine(OcrEngine)`. Altta `rapidocr` 3.9.2 (`EngineType.ONNXRUNTIME`). Motor **tembel** kurulur (ilk `recognize`'da), **enjekte edilebilir** (testler gerçek modeli hiç yüklemez).

```python
class Tanıyıcı(Protocol):
    """rapidocr'un çağrı biçimi: BGR uint8 dizi -> (kutular, metinler, puanlar) | None"""
    def __call__(self, image: ImageArray) -> TanımaSonucu | None: ...

class RapidOcrEngine(OcrEngine):
    def __init__(
        self, *,
        language: OcrLanguage,                 # StrEnum: JAPAN | KOREAN | CHINESE | ENGLISH — ZORUNLU, varsayılan YOK
        threads: int = 8,                      # -1 ("otomatik") YASAK — K3
        allow_download: bool = False,          # model yoksa: True -> rapidocr indirir, False -> ModelMissingError
        recognizer: Tanıyıcı | None = None,    # test enjeksiyonu; None -> rapidocr tembel kurulur
    ) -> None: ...
    def recognize(self, frame: Frame, preset: OcrPreset) -> list[TextBlock]: ...
```

`OcrLanguage` bu modülde tanımlanır (`src/contracts/` dondurulmuş). Dört üye yeter; `rapidocr.LangRec`'e eşlemeyi modül içinde tek bir sözlük yapar.

---

# Değişmezler — her birinin yanında ölçüsü

## K1 · Testler gerçek modeli hiç yüklemez; gerçek model tek kapıdan ölçülür

**DEĞİŞMEZ:** `tests/unit/ocr/test_rapid_engine.py` hiçbir testte `rapidocr`'u import etmez, `onnxruntime` oturumu açmaz, disk'ten `.onnx` okumaz, ağa çıkmaz. Bütün birim testleri `recognizer=` ile **sahte tanıyıcı** enjekte eder.
**ÖLÇÜ:** `tests/unit/ocr/conftest.py` — oturum kapsamlı fixture `sys.modules["rapidocr"]`'a **patlayan** bir bariyer koyar (import edilirse `RuntimeError`); ayrıca `sys.meta_path`'e bulucu ekleyip `onnxruntime` için import girişimi sayar → **0** olmalı. `real_check.py` (şefe ait) gerçek modeli **`--real`** ile ayrı süreçte koşar.
**Neden:** T-005 K1 ile aynı gerekçe — model yükleme 1-2 s, testleri yavaşlatır ve her geliştirici makinesinde model bulunmasını şart koşar. Gerçek davranış yine ölçülür, ama tek yerden.

## K2 · Dil açık seçilir; güven puanı dil hatasını göremez

**DEĞİŞMEZ:** `language` zorunlu, varsayılanı yok. Motor dili **tahmin etmez**. Yanlış dilde tanıma yüksek güvenle yanlış metin üretir (O2: `ch` modeli Japonca diyalogda 0.90 güvenle `村の長老待。`); bu yüzden dil bir **yapılandırma** kararıdır, motor kararı değil.
**ÖLÇÜ:** `RapidOcrEngine()` (dilsiz) → `TypeError` (Python'un keyword-only zorunluluğu; AST ile `language` parametresinin varsayılanı olmadığı denetlenir). `real_check.py`: Japonca diyalog kutusu `language=JAPAN` ile **4/4 satır birebir**, aynı görüntü `language=CHINESE` ile 4/4 **değil** — ölçünün ateşlediği gösterilir (§4.6/10 pozitif kontrol).

## K3 · İş parçacığı sayısı açık; "otomatik" yasak

**DEĞİŞMEZ:** `threads` motora **aynen** geçer (`EngineConfig.onnxruntime.intra_op_num_threads` ve `inter_op_num_threads`). `threads < 1` → `ValueError` yapımda. `-1` **hiçbir yoldan** motora ulaşmaz.
**ÖLÇÜ:** Sahte `rapidocr.RapidOCR` sınıfı (test içinde, `sys.modules` üzerinden değil — `recognizer` fabrikası enjekte edilerek) kendisine verilen `params` sözlüğünü kaydeder; test `threads=4` ve `threads=8` ile **iki noktada** iki anahtarın da o değeri taşıdığını, `Global.use_cls`'nin `False` olduğunu assert eder. `threads=0` ve `threads=-1` → `ValueError`. **Neden:** O3 — 32 çekirdekte "otomatik" 1450 ms, 8 parçacık 195 ms; **6 kat**. Bütçe 250 ms.

## K4 · `bbox` ekran koordinatında, düz `int`, eksen hizalı

**DEĞİŞMEZ:** rapidocr dört köşeli float çokgen döndürür (`[[x1,y1],[x2,y2],[x3,y3],[x4,y4]]`, görüntü-yerel). `TextBlock.bbox`, çokgenin **eksen hizalı sınır kutusu**dur, `frame.rect.x/y` kadar **kaydırılmış** (ekran fiziksel koordinatı), dört alanı **`type(v) is int`** (`x`,`y` = floor; `w`,`h` = ceil(sağ)−floor(sol) ile **kapsayıcı**). `monitor_index` ve `dpi_scale` `frame.rect`'ten **aynen** taşınır.
**ÖLÇÜ:** Sahte tanıyıcı `np.float32` köşeli çokgen döndürür; test **iki frame'de** koşar: `Frame.rect=(0,0,…)` ve `Frame.rect=(-2600,-50,…, monitor_index=0)` (negatif sanal-masaüstü; bu makinede gerçek). Her `bbox` alanı için `type(v) is int` (`==` yetmez — T-004/T-005'te ölçüldü, `np.int64(10) == 10` `True`); kaydırma doğru; `json.dumps(asdict(bbox))` `TypeError` vermez. Çokgen döndürülmüş (eğik) olduğunda kutu köşelerin **min/max**'ını alır — bir eğik çokgen fixture'ı zorunlu.

## K5 · Güven süzülmez, sıra korunur, boş sonuç geçerli

**DEĞİŞMEZ:** Arayüz sözleşmesi: motor **eşik uygulamaz** (`TextNormalizer`'ın işi). rapidocr'un her `(kutu, metin, puan)` üçlüsü **bire bir** bir `TextBlock` olur, **rapidocr'un sırasıyla**; `confidence` puanın `float`'ı (`type is float`), `text` **değiştirilmez** (strip yok, normalize yok — o da normalizer'ın işi). rapidocr `None` ya da boş liste döndürürse `[]` döner, istisna **yok**.
**ÖLÇÜ:** Sahte tanıyıcı üç blok verir: puanlar `0.05`, `0.99`, `0.60`; metinlerden biri başında/sonunda boşluklu, biri boş string. Çıktı **3 blok**, aynı sırada, metinler **aynen**, güvenler aynen. `None` ve `([],[],[])` → `[]`. Bu ölçü K7'nin "eleme yok" kuralını da kapsar.

## K6 · Hata sınıflandırması

**DEĞİŞMEZ:** (a) Motor kurulurken model dosyası yok **ve** `allow_download=False` → `ModelMissingError` (`__cause__` rapidocr'un özgün istisnası). (b) Motor kuruldu ama `recognize` içinde istisna → `OcrError` (`__cause__` özgün). (c) `frame.image` 3 kanallı `uint8` değilse → `ContractViolation`, motor **çağrılmaz**. **Yeniden deneme yok** (OCR deterministik; T-005 K6'nın aksine).
**ÖLÇÜ:** Enjekte edilen sahte fabrika `FileNotFoundError` fırlatır → `ModelMissingError`, `__cause__` o. Sahte tanıyıcı `RuntimeError` fırlatır → `OcrError`. `(h,w,4)` ve `(h,w)` ve `float32` görüntü → `ContractViolation`, tanıyıcı çağrı sayısı **0**. `allow_download=True`'nun **gerçek** davranışı yalnız `real_check.py`'de (K1).

## K7 · Motor hiçbir OCR metnini loglamaz; rapidocr'un logu susturulur

**DEĞİŞMEZ:** PROTOKOL §7 loglama disiplini. `rapid_engine.py` içinde `print` **yok**; `logging` çağrılarının hiçbirine `TextBlock.text` ya da rapidocr metni girmez. rapidocr'un kendi logger'ı (`"RapidOCR"`) motor kurulurken `WARNING`'e çekilir (O4'te görüldü: renk kodlu `INFO` satırları stdout'a yazıyor).
**ÖLÇÜ:** AST — modülde `print` çağrısı 0; `logging.*` çağrılarının argümanlarında `.text`/`txts`/`metin` adlı isim **yok**. Çalışma zamanı — `caplog` ile bir `recognize` koşumu: kayıtların hiçbiri sahte tanıyıcının döndürdüğü **nöbetçi** metni (`"NÖBETÇİ-7f3a"`) içermez.

## K8 · `preset` kabul edilir ama v1'de motoru değiştirmez `[ÖLÇÜLMÜYOR → belgelenir]`

**DEĞİŞMEZ:** `recognize(frame, preset)` dört `OcrPreset` üyesini de kabul eder ve **aynı** sonucu verir. Tasarım §3.2 ön ayarın "ölçekleme faktörü ve kontrast ön işlemesi"ni değiştirmesini öngörüyor; bu **ölçülmeden** yazılmaz (küçük yazı için 2× büyütmenin yardımcı olup olmadığı bilinmiyor). v1: parametre alınır, docstring'e `[ÖLÇÜLMÜYOR]` damgasıyla "ön ayar bazlı ön işleme T-0xx" yazılır.
**ÖLÇÜ:** Aynı sahte tanıyıcı, dört preset → dört **eşit** çıktı. Damga docstring'de **var** (AST ile `[ÖLÇÜLMÜYOR]` metni aranır).

## K9 · Süre kutu sayısına bağlıdır; ölçü kutu başına

**DEĞİŞMEZ:** Bütçe tek sayı değil (O5: Korece 17 kutu → 2070 ms, Japonca 4 kutu → 200 ms). `recognize` ölçülen süreyi **döndürmez** (arayüz sabit) ama motor son çağrının `(toplam_ms, kutu_sayısı)`'nı `last_timing` özelliğinde tutar.
**ÖLÇÜ:** `real_check.py`: Japonca 4 satırlık diyalog ≤ **300 ms** (medyan, 5 koşum, ısınma sonrası); İngilizce ≤ 350 ms; Korece kutu başına ≤ **150 ms** raporlanır (toplam **bütçe değil**, tespit kelime ayırdığı için). Bu ölçüler `[ÖLÇÜLMÜYOR]` değil ama **makineye bağlı**; `real_check` sayıyı yazar, eşik aşımında **uyarı** verir, düşürmez — bütçe kararı şefin.

## K10 · Tembel kurulum, tek örnek, kapatma

**DEĞİŞMEZ:** `__init__` rapidocr'a dokunmaz (K1 altında kapsanabilir). İlk `recognize` motoru kurar; sonrakiler **aynı** örneği kullanır (kurulum 1-2 s, her karede yapılamaz). `close()` idempotent; kapatıldıktan sonra `recognize` → `OcrError`.
**ÖLÇÜ:** Enjekte fabrika çağrı sayacı: yapım → 0; üç `recognize` → **1**. `close()` iki kez → sessiz; sonra `recognize` → `OcrError`. **Değer ekseni dersi (T-005 D-3.Y1):** kapatma bayrağı hangi yoldan geçilirse geçilsin okunur — `with` bloğu **yok** (motor bağlam yöneticisi değil, gereksiz yüzey açmaz).

---

# Kabul kapısı — `real_check.py` (şefe ait, implementer koşar ama yazmaz)

Şefin üç PNG'si (`.agents/tasks/T-006/fixtures/dlg_{EN,JP,KR}.png`, 1200×400, O4/O5'te üretildi) üzerinde **gerçek** modelle:

1. `JAPAN` → 4/4 satır birebir (`長老マルクス` / `村の長老があなたを待っています。` / …).
2. Aynı görüntü `CHINESE` → 4/4 **değil** (K2'nin pozitif kontrolü).
3. `KOREAN` → okuma sırasına dizilip birleştirilince benzerlik ≥ 0.95 (O5: 0.971 ölçüldü; noktalar düşüyor, bu **bilinen** kayıp).
4. `ENGLISH` → 4/4.
5. Süreler K9'a göre raporlanır.
6. `bbox`'lar `frame.rect`'e göre kaydırılmış: PNG `Frame.rect=(-2600,-50,1200,400)` ile sarılır, ilk satırın `bbox.x < 0` olmalı.
7. `allow_download=False` + model yok → `ModelMissingError` (ayrı süreçte, model dizini geçici olarak boş bir yere yönlendirilerek; rapidocr'un model yolu parametresi kullanılır).

Model dosyaları `real_check` koşulmadan önce diskte olmalı (`rapidocr` ilk kullanımda modelscope.cn'den indirir — O4). Şef indirdi; implementer'ın makinesinde de var.

---

# Yozlaşmış girdiler — hepsi test edilecek (sahte tanıyıcıyla)

`0×0` görüntü (→ `ContractViolation`, tanıyıcı çağrılmaz) · `1×1` görüntü (tanıyıcıya gider, `[]` dönerse `[]`) · çokgen köşeleri görüntü dışına taşan (kutu **kırpılmaz**, olduğu gibi kaydırılır — kırpma normalizer'ın işi değil, ama **belgelenir**) · `NaN` puan (aynen geçer, `float`) · metin `None` (→ `OcrError`, rapidocr sözleşme dışı) · tanıyıcı `txts` ile `boxes` uzunluğu farklı (→ `OcrError`).

# Teslim

`delivery.md` — `validate.py` şemasına uy; her kabul komutunun ham çıktısı `evidence/` altında **dolu**. K2/K3/K4/K6/K8'in "docstring'e yaz" maddeleri **hem** docstring'de **hem** `known_gaps`'te. Bu paket **bir** kırmızı takım geçişi görecek (§4.6/9); paketin kendisine güvenmeyin — sözleşme `src/contracts/interfaces.py`'dedir, çelişirse **sözleşme** kazanır ve `known_gaps`'e yazılır.
