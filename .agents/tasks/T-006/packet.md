---
task: T-006
title: "RapidOcrEngine: yerel ONNX OCR motoru (JP/KR/EN/ZH), dil açık, iş parçacığı açık"
role: implementer
level: B
wave: 1
packet_version: 2
owns:
  - "src/ocr/rapid_engine.py"
  - "tests/unit/ocr/test_rapid_engine.py"
  - ".agents/tasks/T-006/evidence/**"
  - ".agents/tasks/T-006/delivery.md"
forbidden:
  - "src/contracts/**"
  - "src/capture/**"
  - "src/ocr/normalizer.py"
  - "src/ocr/presets.py"
  - "src/ocr/__init__.py"
  - "tests/unit/ocr/conftest.py"
  - "tests/unit/ocr/test_normalizer.py"
  - "tests/unit/capture/**"
  - "demo/**"
  - ".agents/tasks/T-006/real_check.py"
  - ".agents/tasks/T-006/fixtures/**"
  - "diğer tüm dizinler"
depends_on: ["T-001", "T-004", "T-005"]
acceptance:
  - "python -m mypy --strict --explicit-package-bases src/ocr/rapid_engine.py"
  - "python -m pytest tests/unit/ocr/test_rapid_engine.py -q"
  - "python .agents/tasks/T-006/real_check.py"
  - "python -m pytest tests/unit/ocr/test_rapid_engine.py -q --cov=src.ocr.rapid_engine --cov-fail-under=90 --cov-report=term-missing"
  - "python -m pytest tests -q"
budget_ms: 300   # TEK bütçe: JAPAN, 1200x400 4 satırlık fixture, gerçek v4-mobile model, 8 iş parçacığı (O4: 191-206 ms). Diğer diller RAPORLANIR.
---

> **Paket sürümü 2.** v1 kırmızı takımdan **7 yüksek** bulguyla döndü; şef üçünü (Y1, Y2, Y5) kendi eliyle yeniden üretti, ikisi (Y4, Y6) şefin kendi ölçümüyle çakıştı. Değişenler `Y*` etiketiyle işaretli. **Ham çıktılar:** `olgular.txt` (O1–O6) ve `krt-1.md`.

# Görev

`OcrEngine` arayüzünün (`src/contracts/interfaces.py`) v1 uygulaması: `Frame` → `list[TextBlock]`. Tasarım §5.1 (bileşen 3), §3.2, §5.7, §6. **Oku.** Sonra `olgular.txt` ve `krt-1.md`'yi oku — her karar oradaki bir ölçüme bağlı.

## Ne yazılacak

**`src/ocr/rapid_engine.py`** — `RapidOcrEngine(OcrEngine)`. Altta `rapidocr` 3.9.2, `EngineType.ONNXRUNTIME`. Motor **tembel** kurulur, tek **enjeksiyon dikişi** vardır (Y-orta: örnek/fabrika çelişkisi kaldırıldı):

```python
class OcrLanguage(StrEnum):
    JAPAN = "japan"; KOREAN = "korean"; CHINESE = "chinese"; ENGLISH = "english"

class TanımaÇıktısı(Protocol):        # rapidocr'un RapidOCROutput'unun bize gereken yüzü
    boxes: object | None               # ndarray float32 (N,4,2) ya da None
    txts: Sequence[str] | None
    scores: Sequence[float] | None

Tanıyıcı = Callable[[ImageArray], TanımaÇıktısı]
TanıyıcıFabrikası = Callable[[dict[str, object]], Tanıyıcı]   # params sözlüğünü alır

class RapidOcrEngine(OcrEngine):
    def __init__(
        self, *,
        language: OcrLanguage,                          # ZORUNLU, varsayılan YOK (K2)
        threads: int | None = None,                     # None -> min(8, os.cpu_count()); -1 YASAK (K3)
        allow_download: bool = False,                   # K6
        model_dir: Path | None = None,                  # None -> rapidocr'un kendi models/ dizini (K6)
        recognizer_factory: TanıyıcıFabrikası | None = None,   # None -> gerçek rapidocr (K1)
    ) -> None: ...
    def recognize(self, frame: Frame, preset: OcrPreset) -> list[TextBlock]: ...
    def close(self) -> None: ...
```

**`rapidocr` yalnız fonksiyon gövdesi içinde import edilir** (T-005 K10 "tembel import" ile aynı; Y7: modül düzeyi import bariyeri patlatır). Modül düzeyinde `LangRec`/`LangDet` **adı geçmez**; dil eşlemesi bir fonksiyonun içinde kurulur.

---

# Değişmezler — her birinin yanında ölçüsü

## K1 · Testler gerçek modeli hiç yüklemez; gerçek model tek kapıdan ölçülür

**DEĞİŞMEZ:** `tests/unit/ocr/test_rapid_engine.py` hiçbir testte `rapidocr`'u import etmez, `onnxruntime` oturumu açmaz, ağa çıkmaz. Her birim testi `recognizer_factory=` ile **sahte** enjekte eder.
**ÖLÇÜ (Y7 düzeltildi):** Bariyer **şefe ait** `tests/unit/ocr/conftest.py`'de, **modül düzeyinde** (fixture'da değil — fixture toplama sonrası kurulur ve modül düzeyi import'u görmez; KRT pytest sandığında ölçtü). Bariyer `sys.modules["rapidocr"]`'a import edilince `RuntimeError` fırlatan bir nöbetçi koyar ve `sys.meta_path`'e `onnxruntime` import girişimlerini sayan bulucu ekler. **Pozitif kontrol:** conftest'in kendi self-testi `import rapidocr` deneyip `RuntimeError` aldığını doğrular — bariyerin ateşlediği gösterilir (§4.6/10). `real_check.py` gerçek modeli ayrı süreçte koşar. **Implementer bu conftest'e dokunmaz** (T-004'ün `olcu_kiti` yolu da orada; üzerine yazılırsa 125 normalizer testi + 623 kör test kırılır).

## K2 · Dil açık seçilir; güven puanı dil hatasını göremez

**DEĞİŞMEZ:** `language` zorunlu, varsayılanı yok, motor dili **tahmin etmez** (O2: `ch` modeli Japonca'da 0.90 güvenle yanlış).
**ÖLÇÜ:** AST — `__init__`'te `language` parametresinin varsayılanı **yok**. `RapidOcrEngine()` → `TypeError`. `real_check.py` #1/#2: JAPAN 4/4, aynı görüntü CHINESE **<4** (pozitif kontrol; Y2 ile birlikte okuyun — bu kontrol **yalnız v4-mobile model tablosuyla** ateşler, v6 varsayılanında CH/EN/JAPAN aynı dosyaya çözülür ve kontrol **düşer**).

## K3 · İş parçacığı sayısı açık; "otomatik" hiçbir yoldan girmez

**DEĞİŞMEZ (Y5 düzeltildi):** `threads` ∈ `[1, os.cpu_count()]`; `None` → `min(8, os.cpu_count() or 1)`. Aralık dışı (`0`, `-1`, `cpu_count+1`) → `ValueError` **yapımda**. Değer `EngineConfig.onnxruntime.intra_op_num_threads` **ve** `inter_op_num_threads`'e aynen gider. **Neden üst sınır:** KRT ölçtü, şef doğruladı — `threads > cpu_count` verilirse onnxruntime **sessizce (0,0) = otomatik**'e döner; O3'te "otomatik" 6 kat yavaş. `Global.use_cls = False` (O3: oyun metni dönük değil).
**ÖLÇÜ:** Sahte fabrika `params` sözlüğünü kaydeder; `threads=4` ve `threads=8` **iki noktada** iki anahtar da o değer, `Global.use_cls is False`. `monkeypatch.setattr(os, "cpu_count", lambda: 6)` ile `threads=8` → `ValueError` (sessiz otomatik **değil**); aynı yamayla `threads=None` → `6`; `threads=4` → geçer (pozitif kontrol). `threads=0`, `-1` → `ValueError`.

## K4 · `bbox` ekran koordinatında, düz `int`, eksen hizalı

**DEĞİŞMEZ:** rapidocr `(N,4,2)` float32 çokgen döndürür, görüntü-yerel. `TextBlock.bbox` = çokgenin eksen hizalı sınır kutusu, `frame.rect.x/y` kadar **kaydırılmış**, alanları **`type(v) is int`**: `x=floor(min_x)`, `y=floor(min_y)`, `w=ceil(max_x)−x`, `h=ceil(max_y)−y`. `monitor_index`/`dpi_scale` `frame.rect`'ten aynen. `w=0`/`h=0` **mümkündür** (dejenere çokgen) ve **olduğu gibi** geçer — kırpma/eleme normalizer'ın işi (KRT düşük bulgusu: belgelenir).
**ÖLÇÜ:** Sahte fabrika `np.float32` çokgen verir; **iki frame**: `rect=(0,0,…)` ve `rect=(-2600,-50,…, monitor_index=0)`. Her alan `type(v) is int` (`==` yetmez), kaydırma tam `rect.x/y`, `json.dumps(asdict(bbox))` geçer. Eğik çokgen fixture'ı zorunlu (min/max). Tam sayı köşeli çokgen (`[[10,20],[50,20],[50,40],[10,40]]`) → `w=40,h=20` (fazla piksel **yok** — KRT ölçtü).

## K5 · Güven süzülmez; kütüphanenin kendi süzgeci KAPATILIR (Y1)

**DEĞİŞMEZ:** Arayüz: motor **eşik uygulamaz**. rapidocr'un `Global.text_score` varsayılanı **0.5**'tir ve puanı altında kalan blokları **sessizce düşürür** (KRT ölçtü, şef doğruladı: KR fixture + JAPAN modeli → varsayılanla 9 kutu, `text_score=0.0` ile 17 kutu; 8 blok kayıp). Motor `Global.text_score = 0.0` **geçer**. Her `(kutu, metin, puan)` üçlüsü bire bir `TextBlock`, rapidocr sırasıyla; `confidence` = `float(puan)`, `text` **değiştirilmez**. Boş sonuç: rapidocr `None` **döndürmez**, `boxes/txts/scores` alanları `None` olan `RapidOCROutput` döndürür (Y4; şef ölçtü) → `[]`, istisna **yok**.
**ÖLÇÜ:** Sahte fabrika `params["Global.text_score"] == 0.0` assert eder. Sahte tanıyıcı puanlar `0.05/0.99/0.60`, biri boşluklu metin, biri boş string → **3 blok** aynen. `boxes=None` nesnesi → `[]`. `real_check.py` #8 (pozitif kontrol): KR fixture `language=JAPAN` ile → **en az 1 blok `confidence < 0.5`** dönmeli; dönmüyorsa süzgeç açık demektir.

## K6 · Hata sınıflandırması ve indirme denetimi (Y6)

**DEĞİŞMEZ:** rapidocr'un `model_dir` parametresi **yok sayılıyor** (şef ölçtü); tek işleyen `Det.model_path`/`Rec.model_path`. Bu yüzden `allow_download` motorun kendi işidir:
- Motor beklenen dosya adını rapidocr'un kendi çözücüsüyle bulur: `rapidocr.inference_engine.base.InferSession.get_model_url(FileInfo(...))` → URL → `Path(url).name`. `model_dir` `None` ise `Path(rapidocr.__file__).parent / "models"`.
- `allow_download=False`: det ve rec için **açık** `model_path` = `model_dir / ad` geçilir; dosya yoksa rapidocr **çağrılmadan** `ModelMissingError` (mesajda eksik dosya adı, `__cause__` yok — dosya sistemi kontrolü bizim). Cls modeli paketle geliyor ve `use_cls=False`; yönetilmez.
- `allow_download=True`: `model_path` geçilmez; rapidocr ilk kurulumda indirir (O4: modelscope.cn, 2.3+9.3 MB). Çevrimdışıysa rapidocr `DownloadFileException` fırlatır → `ModelMissingError` (`__cause__` özgün).
- (b) Motor kuruldu, `recognize` içinde istisna → `OcrError` (`__cause__` özgün). Kurulumda rapidocr `ValueError` (desteklenmeyen dil/sürüm kombinasyonu, Y2) → `OcrError`.
- (c) `frame.image` `(h,w,3)` `uint8` değilse → `ContractViolation`, motor **çağrılmaz** (`CaptureService` 3 kanal BGR veriyor — KRT doğruladı). **Yeniden deneme yok.**
**ÖLÇÜ:** Sahte fabrika `FileNotFoundError` **fırlatmaz** — çünkü kontrol fabrikadan önce. Test: `allow_download=False`, `model_dir=tmp_path` (boş) → ilk `recognize` `ModelMissingError`, fabrika **çağrılmadı** (sayaç 0). `model_dir`'e beklenen adlarla boş dosyalar konunca → fabrika çağrıldı, `params["Det.model_path"]` ve `["Rec.model_path"]` o dosyalar. `allow_download=True` → `params`'ta `model_path` **yok**. Sahte tanıyıcı `RuntimeError` → `OcrError`. `(h,w,4)`, `(h,w)`, `float32` → `ContractViolation`, sayaç 0. Gerçek `DownloadFileException` yolu **`[ÖLÇÜLMÜYOR]`** — ağ kesmek kapının işi değil; belgelenir.

## K7 · Motor OCR metnini loglamaz; rapidocr'un logu susturulur (kurulumdan SONRA)

**DEĞİŞMEZ:** `rapid_engine.py`'de `print` yok; hiçbir `logging` çağrısına blok metni girmez. rapidocr `"RapidOCR"` logger'ını **kurulumda kendisi seviyelendirir** (KRT orta) — bu yüzden motor seviyeyi `ERROR`'a **rapidocr örneğini kurduktan sonra** çeker (`WARNING` yetmez: boş sonuçta `WARNING` basıyor, şef ölçtü).
**ÖLÇÜ:** AST — `print` çağrısı 0; `logging` argümanlarında `.text`/`txts` yok. Çalışma zamanı — `caplog.at_level(logging.WARNING, logger="RapidOCR")` altında nöbetçi metinli (`"NÖBETÇİ-7f3a"`) bir `recognize` → kayıtların hiçbiri nöbetçiyi içermez. Sıralama testi: sahte fabrika çağrıldığında logger seviyesini `INFO`'ya **sıfırlar** (rapidocr'u taklit); `recognize` sonrası seviye yine `ERROR` olmalı.

## K8 · `preset` kabul edilir ama v1'de motoru değiştirmez `[ÖLÇÜLMÜYOR → belgelenir]`

**DEĞİŞMEZ:** Dört `OcrPreset` de aynı sonucu verir. Tasarım §3.2'nin ön ayar bazlı ölçekleme/kontrast önerisi **ölçülmeden yazılmaz**; docstring'e `[ÖLÇÜLMÜYOR]` damgasıyla "ön ayar bazlı ön işleme: ayrı görev".
**ÖLÇÜ:** Aynı sahte, dört preset → dört **eşit** çıktı. Damga docstring'de var (AST).

## K9 · Süre kutu sayısına bağlıdır; ölçü dışarıdan, tek bütçe

**DEĞİŞMEZ:** Bütçe **bir** yerde, **bir** sayıdır: `budget_ms: 300` = JAPAN fixture, 4 satır, v4-mobile, 8 parçacık (O4). Diğer diller `real_check`'te **raporlanır**, düşürmez (O5: Korece tespit kelime ayırır, 17 kutu → süre kutu sayısıyla ölçeklenir). Motor **süre tutmaz** (`last_timing` kaldırıldı — KRT: ölçüsüz alan yazılmaz).
**ÖLÇÜ:** `real_check.py` #5.

## K10 · Tembel kurulum, tek örnek, kapatma

**DEĞİŞMEZ:** `__init__` rapidocr'a dokunmaz. İlk `recognize` kurar; sonrakiler aynı örnek. `close()` idempotent; sonrası `recognize` → `OcrError`. Bağlam yöneticisi **değil** (T-005 D-3.Y1 dersi: `with` yüzeyi açılmaz).
**ÖLÇÜ:** Fabrika sayacı: yapım → 0; üç `recognize` → 1. `close()` ×2 sessiz; sonra `recognize` → `OcrError`, fabrika sayacı hâlâ 1.

## K11 · Model tablosu dil başına SABİT (Y2, Y3)

**DEĞİŞMEZ:** Kütüphane varsayılanı PP-OCRv6-small'dır ve **kullanılmaz**: KOREAN'da `ValueError`, JAPAN'da 425 ms (şef) / 1.6 s (KRT), CH/EN/JAPAN aynı dosyaya çözülüp K2 pozitif kontrolünü düşürür. Motor her dil için **şu tabloyu** geçer:

| `OcrLanguage` | `Det.lang_type` | `Rec.lang_type` | ortak |
|---|---|---|---|
| JAPAN | `MULTI` | `JAPAN` | `Det/Rec.engine_type=ONNXRUNTIME`, `Det/Rec.model_type=MOBILE`, `Det/Rec.ocr_version=PPOCRV4` |
| KOREAN | `MULTI` | `KOREAN` | aynı |
| CHINESE | `CH` | `CH` | aynı |
| ENGLISH | `CH` | `EN` | aynı |

**Neden det iki farklı:** Y3 — `multi` det İngilizce'yi 22 kelime kutusuna böler (4/4 satır düşer); `ch` det İngilizce'de 4/4 verir ama Korece boşluklarını yitirir. Tablo her dile uyanı seçer.
**ÖLÇÜ:** Sahte fabrika `params`'ı kaydeder; **dört dilin dördü** için altı anahtar tablodaki değer (enum üyeleriyle karşılaştırılır, string'le değil). `real_check.py` #1–#4 bu tabloyla geçer; #2 pozitif kontrolü **yalnız** bu tabloyla ateşler.

---

# Windows tuzakları (KRT orta) — yapıyla kapanır, belgelenir

- **cv2.imread ASCII-dışı yolda `None` döner** (bu depo yolu `çeviri` içeriyor). Motor rapidocr'a **yalnız numpy dizi** verir, asla yol; `real_check` de öyle. Docstring'e yazılır.
- **cp1254 konsolda Japonca metin `UnicodeEncodeError`.** Motor ve kapı OCR metnini **stdout'a yazmaz** (K7 zaten); testler de metin basmaz.

# Yozlaşmış girdiler — hepsi sahte tanıyıcıyla test edilir

`0×0` (→ `ContractViolation`) · `1×1` (tanıyıcıya gider) · çokgen görüntü dışına taşan (kırpılmaz, kaydırılır) · `NaN` puan (aynen, `float`) · `txts` ile `boxes` uzunluğu farklı (→ `OcrError`) · `txts` içinde `None` (→ `OcrError`) · `boxes` var `txts` `None` (→ `OcrError`) · dejenere çokgen (`w=0`).

# Kabul kapısı — `real_check.py` (şefe ait; koş, yazma)

Şefin üç fixture'ı, gerçek model, 8 kontrol: JAPAN 4/4 · CHINESE-on-JP <4 · KOREAN ≥0.95 · ENGLISH 4/4 · süreler · bbox iki noktada · model yok → `ModelMissingError` · **#8 (Y1): KR+JAPAN → ≥1 blok `confidence<0.5`**. Modeller diskte (şef indirdi).

# Teslim

`delivery.md` — `validate.py` şemasına uy; her komutun ham çıktısı `evidence/` altında **dolu**. K2/K3/K5/K6/K8/K11 docstring'de **ve** `known_gaps`'te. Sözleşme `src/contracts/interfaces.py`; paketle çelişirse **sözleşme** kazanır ve `known_gaps`'e yazılır. **Şefin kararıyla ölçümün çelişirse ölçümüne uy ve itirazını yaz** — T-005'te implementer bunu iki kez yaptı ve iki kez haklı çıktı.
