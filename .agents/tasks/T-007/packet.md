---
task: T-007
title: "LocalNmtProvider: yerel NMT çeviri sağlayıcısı (NLLB-200 600M int8, CTranslate2)"
role: implementer
level: B
wave: 2
packet_version: 1
owns:
  - "src/translate/__init__.py"
  - "src/translate/local_nmt.py"
  - "tests/unit/translate/__init__.py"
  - "tests/unit/translate/test_local_nmt.py"
  - ".agents/tasks/T-007/evidence/**"
  - ".agents/tasks/T-007/delivery.md"
forbidden:
  - "src/contracts/**"
  - "src/capture/**"
  - "src/ocr/**"
  - "tests/unit/ocr/**"
  - "tests/unit/capture/**"
  - "tests/unit/translate/conftest.py"
  - "demo/**"
  - "models/**"
  - ".agents/tasks/T-007/real_check.py"
  - ".agents/tasks/T-007/fixtures/**"
  - "diğer tüm dizinler"
depends_on: ["T-001", "T-004"]
acceptance:
  - "python -m mypy --strict --explicit-package-bases src/translate/local_nmt.py"
  - "python -m pytest tests/unit/translate/test_local_nmt.py -q"
  - "python .agents/tasks/T-007/real_check.py"
  - "python -m pytest tests/unit/translate/test_local_nmt.py -q --cov=src.translate.local_nmt --cov-fail-under=90 --cov-report=term-missing"
  - "python -m pytest tests -q"
budget_ms: 200   # TEK bütçe: JAPAN, 4 cümle tek batch, gerçek model, 8 iş parçacığı — C2: 311 ms/4 = 78 ms/cümle; bütçe cümle başına değil BATCH başına 4 cümle için
---

> **Bu paket dokuz ön ölçüme dayanıyor:** `.agents/tasks/T-007/olgular.txt` (C1–C9). Her karar oradaki bir olguya bağlı. **Önce onu oku.** Ölçülmemiş hiçbir kalite iddiası yazılmadı; kalite altın seti yok (tasarım 12), o ayrı görev.

# Görev

`TranslationProvider` arayüzünün (`src/contracts/interfaces.py`) **Katman 1** uygulaması: `TranslationRequest` → `TranslationResult`. Tasarım §4.2, §4.6 (Mod 2 varsayılanı), §5.1 (bileşen 7). **Oku.** Sözleşme paketten üstündür.

## Ne yazılacak

**`src/translate/local_nmt.py`** — `LocalNmtProvider(TranslationProvider)`. Altta `ctranslate2` 4.8.2 + `sentencepiece` 0.2.2, model NLLB-200-distilled-600M CT2 int8 (C1). Tek enjeksiyon dikişi:

```python
class NmtDili(StrEnum):                   # NLLB kodları, sabit tablo (C4)
    JAPAN = "jpn_Jpan"; KOREAN = "kor_Hang"; CHINESE = "zho_Hans"; ENGLISH = "eng_Latn"; TURKISH = "tur_Latn"

class CeviriMotoru(Protocol):             # ctranslate2.Translator'ın bize gereken yüzü
    def translate_batch(self, tokens: list[list[str]], *, target_prefix: list[list[str]],
                        beam_size: int, max_decoding_length: int, **kw: object) -> Sequence[object]: ...

MotorFabrikası = Callable[[Path, dict[str, object]], tuple[CeviriMotoru, Callable[[str], list[str]], Callable[[list[str]], str]]]
# (model_dir, motor_params) -> (motor, encode, decode)

class LocalNmtProvider(TranslationProvider):
    def __init__(self, *,
        model_dir: Path,                              # ZORUNLU; yol ile değil BAYT ile açılır (C5)
        threads: int | None = None,                   # None -> min(8, cpu_count); aralık [1, cpu_count] (T-006 K3)
        beam_size: int = 4,                           # C2 ile ölçüldü
        repetition_penalty: float = 1.0,              # C7: varsayılan CEZASIZ; >1 halüsinasyon
        motor_fabrikasi: MotorFabrikası | None = None # None -> gerçek CT2 (K1)
    ) -> None: ...
    @property
    def provider_id(self) -> str: ...                 # "local-nmt-nllb200-600m-int8"
    def translate(self, request: TranslationRequest) -> TranslationResult: ...
    def close(self) -> None: ...
```

`ctranslate2` ve `sentencepiece` **yalnız fonksiyon gövdesinde** import edilir (K1).

---

# Değişmezler — her birinin yanında ölçüsü

## K1 · Testler modeli hiç yüklemez; gerçek model tek kapıdan ölçülür

**DEĞİŞMEZ:** `tests/unit/translate/test_local_nmt.py` `ctranslate2`/`sentencepiece` import etmez, `models/` okumaz. Her test `motor_fabrikasi=` ile sahte enjekte eder.
**ÖLÇÜ:** **Şefe ait** `tests/unit/translate/conftest.py` modül düzeyinde `meta_path` bariyeri (`ctranslate2*`, `sentencepiece*` → `RuntimeError`), pozitif kontrolü `tests/unit/translate/test_conftest_bariyer.py` (şefe ait). `real_check.py` ayrı süreçte gerçek model.

## K2 · Hizalama sözleşmesi — `ensure_aligned` her dönüşten önce

**DEĞİŞMEZ:** `translations` `request.segments` ile **birebir hizalı**; boş `segments` → boş `translations`, `latency_ms ≥ 0`. `translate` dönmeden `ensure_aligned` çağrılır. Sahte motor eksik/fazla hipotez döndürürse → `ContractViolation` (motor sözleşme dışı), **asla** eksik liste dönmez.
**ÖLÇÜ:** Sahte motor 3 giriş / 2 çıkış → `ContractViolation`; 3/4 → aynı; boş istek → `translations == ()`, motor **çağrılmaz**. AST: `translate` gövdesinde `ensure_aligned` çağrısı var.

## K3 · Cümle bölme ve yeniden birleştirme (C6, C8)

**DEĞİŞMEZ:** Her segment metni **cümlelere bölünür**, tüm segmentlerin tüm cümleleri **tek** `translate_batch` çağrısında gider (C2: toplu 2× ucuz), çıktı cümleleri segment başına `" "` ile birleştirilir. Bölme: JP/KR/ZH için `。！？` sonrası; EN için `[.!?]` + boşluk/sonu. Cümle içermeyen (noktalama yok) segment **tek cümle** sayılır. Bölme **kayıpsız**: bölünen parçaların birleşimi kaynağa eşit (boşluk dışında).
**ÖLÇÜ:** Sahte motor aldığı token listelerini kaydeder: 2 segment (3+1 cümle) → **tek** çağrı, 4 giriş; çıktı 2 segmente doğru dağıtılır. Bölmenin kayıpsızlığı 6 fixture'da (`。` art arda, sonda noktalama yok, `！？` karışık, EN kısaltma `Dr. Smith` — **bilinen zayıflık**, bölünür, belgelenir). `real_check` #3: JP 3-cümlelik paragraf → çıktıda üç cümlenin üçü de var (tek girdide 2. cümle eriyordu — C8 pozitif kontrol).

## K4 · Dil kodu açık; `source_lang=None` desteklenmez

**DEĞİŞMEZ:** NLLB dil algılamaz. `request.source_lang` `NmtDili`'ye eşlenemiyorsa ya da `None` ise → `ProviderUnavailable` (mesaj: "bu sağlayıcı dil algılamaz; kaynak dil zorunlu"). `target_lang` yalnız `"tr"`/`"tur_Latn"` (v1). Kaynak belirteci token dizisinin **başına**, `"</s>"` sona, `target_prefix=[["tur_Latn"]]` (C4).
**ÖLÇÜ:** `source_lang=None`, `"xx"`, `"ja"` (ISO-639-1, NLLB kodu değil — eşleme tablosu `"ja"→jpn_Jpan` **kabul eder**), `"jpn_Jpan"` (doğrudan) → ilk ikisi `ProviderUnavailable`, son ikisi geçer. Sahte motor kaydı: ilk token `"jpn_Jpan"`, son `"</s>"`, `target_prefix` her satırda `["tur_Latn"]`. **İki dilde** (JAPAN, KOREAN).

## K5 · Yer tutucu korunumu — kontrol + kaba onarım (C9)

**DEĞİŞMEZ:** `Segment.placeholders` içindeki her dize çıktıda aranır; **eksikse sona eklenir** (sırayla, boşlukla). Bu kaba ve belgelenir: NLLB Japonca'da yer tutucuyu **düşürüyor** (C9: `{0}があなたを{1}で` → "Seni bekliyor."), İngilizce'de koruyor. Gerçek çözüm Katman 0/2; v1 yıkıcı olmayan onarım yapar. `glossary_hits`, `tm_examples`, `style_profile`, `image_crops` **kabul edilir, uygulanmaz** — NMT kısıt almaz; docstring `[ÖLÇÜLMÜYOR]`.
**ÖLÇÜ:** Sahte motor yer tutucuyu düşüren çıktı verir → sonuçta yer tutucu **sonda** var; koruyan çıktı → **dokunulmaz** (iki nokta). `real_check` #5: JP `{0}` fixture'ı → çıktıda `{0}` var (onarım); EN → var (model korudu). AST: `glossary_hits` **okunmuyor** (v1'de kullanılmadığı gerçek; sessiz "uyguluyor" yanılsaması olmasın).

## K6 · Hata sınıflandırması

**DEĞİŞMEZ:** (a) `model_dir`'de `model.bin` ya da `sentencepiece.bpe.model` yok → `ModelMissingError` **motor kurulmadan**. (b) Motor kurulumu/çevirisi istisna → `ProviderUnavailable` (`__cause__` özgün). (c) Hizalama → `ContractViolation` (K2). Yeniden deneme **yok**. `ProviderTimeout` v1'de **fırlatılmaz** (bütçe yok) — `[ÖLÇÜLMÜYOR]`.
**ÖLÇÜ:** Boş `tmp_path` → `ModelMissingError`, fabrika sayacı 0; boş dosyalar konunca fabrika çağrılır. Sahte fabrika `RuntimeError` → `ProviderUnavailable`, `__cause__` o.

## K7 · Model dosyaları BAYT ile açılır (C5)

**DEĞİŞMEZ:** `sentencepiece` ASCII-dışı yolu açamıyor (bu depo yolu `çeviri`). `SentencePieceProcessor(model_proto=bytes)`; CT2 yolu açabiliyor ama `str(model_dir)` **mutlak** verilir.
**ÖLÇÜ:** Gerçek fabrika AST'sinde `model_file=` **yok**, `model_proto=` **var**. `real_check` #7: `model_dir` ASCII-dışı bir geçici dizine **kopyalanır** (`tmp/çeviri-ölçüm/`), sağlayıcı oradan kurulur ve çevirir.

## K8 · İş parçacığı açık; ceza varsayılan kapalı (T-006 K3, C7)

**DEĞİŞMEZ:** `threads` aralık denetimli (`[1, cpu_count]`, `-1` yasak), `intra_threads` olarak CT2'ye; `inter_threads=1`. `repetition_penalty` **1.0** varsayılan (C7: >1 "Ba'at Çölü" halüsinasyonu); yapılandırılabilir, `[ÖLÇÜLMÜYOR]` kalite.
**ÖLÇÜ:** Sahte fabrika `params` kaydeder: `threads=4`/`8` iki nokta; `cpu_count` yaması ile `9` → `ValueError`. `repetition_penalty` çağrıya **aynen** gider; `1.0` iken `translate_batch`'e **hiç geçilmez** (CT2 varsayılanı).

## K9 · Süre ve `latency_ms`

**DEĞİŞMEZ:** `latency_ms` `translate`'in kendi duvar saati (`perf_counter`), motor kurulumu **hariç** (tembel kurulum ilk çağrıda; o çağrının `latency_ms`'i kurulumu **içermez** — kurulum ayrı ölçülür). Bütçe: `real_check` JAPAN 4 cümle tek batch ≤ **200 ms** medyan (C2: 311 ms/4 = 78 ms/cümle → 4 cümle ~311; **bütçe 200 ms/4 cümle iddialı**, eşik aşımı **uyarı**, düşürmez — sayı şefin).
**ÖLÇÜ:** Sahte motor 30 ms uyur → `latency_ms ∈ [30, 200)`; ilk çağrı `latency_ms` fabrika süresini içermez (fabrika 100 ms uyur, `latency_ms < 100`).

## K10 · Tembel kurulum, tek örnek, kapatma, loglama

**DEĞİŞMEZ:** `__init__` CT2'ye dokunmaz; ilk `translate` kurar; `close()` idempotent, sonrası `ProviderUnavailable`; `close()` motoru bırakır (weakref). **Hiçbir kanala çeviri/kaynak metni yazılmaz** (PROTOKOL §7) — T-006 K7'nin **davranış** ölçüsü aynen: `capfd` sıfır bayt, kök logger DEBUG `caplog`, `warnings`; iki nöbetçi (biri ASCII-dışı); 3+ pozitif kontrol sahte sağlayıcı.
**ÖLÇÜ:** T-006 tur 2 `_k7_kanal_olcusu` deseniyle birebir. Fabrika sayacı yapım 0 / üç çağrı 1.

---

# Kabul kapısı — `real_check.py` (şefe ait; koş, yazma)

Gerçek model, `models/nllb-200-distilled-600M-ct2-int8/`:
1. JP 4 fixture cümlesi (`.agents/tasks/T-007/fixtures/cumleler.json`) → 4 çeviri, hepsi boş değil, `provider_id` doğru, hizalı.
2. EN 2 cümle → çıktıda "bekliyor" **ve** "değirmen" geçer (C3'te EN doğruydu; bu **zayıf** içerik kontrolü, altın set değil).
3. **C8 pozitif kontrol:** JP 3-cümlelik tek segment → çıktı ≥ 3 cümle (`.`/`!`/`?` sayısı ≥ 3) **ve** "ihtiyar" + "doğu" + ("güneş" | "gün") üçü de var.
4. KR 2 cümle → hizalı, boş değil (kalite **ölçülmez**, C7 bilinen zayıflık).
5. Yer tutucu: JP `{0}`/`{1}` → çıktıda ikisi de var; EN → var.
6. Süre: JAPAN 4 cümle tek batch medyan (5 koşum, ısınma sonrası) ≤ 200 ms → uyarı eşiği.
7. ASCII-dışı `model_dir` kopyası → çalışır.
8. `source_lang=None` → `ProviderUnavailable`; `model_dir` boş → `ModelMissingError` (ayrı süreç).

# Yozlaşmış girdiler — sahte motorla

Boş segment metni (`""` → çıktı `""`, motora **gitmez**) · yalnız boşluk · yalnız noktalama (`"。。。"`) · 500 cümlelik segment (tek batch; `max_decoding_length` sınırı belgelenir) · segment metni `None` olamaz (`Segment` frozen, `str`) · `tm_examples`/`glossary_hits` dolu → yok sayılır, çıktı aynı.

# Teslim

`delivery.md` — `validate.py`; her komutun ham çıktısı `evidence/` altında **dolu**. K3/K4/K5/K7/K8 hem docstring hem `known_gaps`. **Şefin kararıyla ölçümün çelişirse ölçümüne uy, itirazını yaz** — T-005/T-006'da implementer bunu beş kez yaptı, beşinde de haklı çıktı.
