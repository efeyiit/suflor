---
task: T-007
title: "LocalNmtProvider: yerel NMT çeviri sağlayıcısı (NLLB-200 600M int8, CTranslate2)"
role: implementer
level: B
wave: 2
packet_version: 2
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
budget_ms: 350   # TEK bütçe: JAPAN 4 cümle tek batch, beam=4, 8 iplik — ÖLÇÜLDÜ 307-316 ms (C2, KRT Y3, şef). 79 ms/cümle = tasarım 4.2'nin 50-150 aralığında. v1'in 200'ü uydurmaydı (Y3).
---

> **Paket sürümü 2.** v1 kırmızı takımdan **3 yüksek / 6 orta** ile döndü; şef üçünü (Y1, Y2, Y3) kendi eliyle yeniden üretti (`sef_dogrulama/krt1_sef_kosumlari.txt`). Değişenler `Y*`/`O*` etiketli.
>
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

**DEĞİŞMEZ (O3 ile güçlendirildi):** `translations` `request.segments` ile **birebir hizalı**; ayrıca motor **gönderilen cümle sayısı kadar** hipotez döndürmeli — segment sayısı tutup cümle sayısı tutmuyorsa (kayma) `ensure_aligned` **görmez**, bu yüzden cümle-düzeyi sayı denetimi ayrıca yapılır → `ContractViolation`. boş `segments` → boş `translations`, `latency_ms ≥ 0`. `translate` dönmeden `ensure_aligned` çağrılır. Sahte motor eksik/fazla hipotez döndürürse → `ContractViolation` (motor sözleşme dışı), **asla** eksik liste dönmez.
**ÖLÇÜ:** Sahte motor 3 giriş / 2 çıkış → `ContractViolation`; 3/4 → aynı; boş istek → `translations == ()`, motor **çağrılmaz**. AST: `translate` gövdesinde `ensure_aligned` çağrısı var.

## K3 · Cümle bölme ve yeniden birleştirme (C6, C8, **Y1, Y2**)

**DEĞİŞMEZ:** Her segment metni **cümlelere bölünür**, tüm segmentlerin tüm cümleleri **tek** `translate_batch` çağrısında gider (C2), çıktı segment başına `" "` ile birleştirilir. **Bölme kuralı DİLE göre DEĞİL, NOKTALAMAYA göre (Y1):** cümle sonu işareti kümesi **evrensel** — `.!?。！？` — ve ardından gelen kapanış işaretleri (`」』"』）)`) cümleye **dahil** edilir. Neden: Korece ASCII `.` kullanır (KR fixture'ının kendisi dahil); v1'in `。！？` kuralı KR'yi hiç bölmüyordu ve tek-girdi çeviride **ikinci cümle tamamen kayboluyordu** (KRT ölçtü, şef doğruladı: "Şehrin ihtiyarı seni bekliyor." — tek cümle). JP'de OCR yarım-genişlik `.` de verebilir.

**Parça süzgeci (Y2):** içinde **hiç harf/rakam olmayan** parça (`？`, `」`, `。。。`, `...`, yalnız boşluk) modele **gönderilmez**, çıktıya **aynen** geçer. Neden: model bu parçalara Türkçe **uydurur** — `？` → "- Hayır, hayır.", `」` → "\"Böyle bir şey.", boşluk → "Hayır, hayır." (KRT ölçtü, şef doğruladı, 5/5). v1'in "kayıpsızlık" ölçüsü (birleşim == kaynak) bunu **geçiriyordu** — ölçü, uydurmayı görmez.

Bilinen zayıflık (belgelenir, `[ÖLÇÜLMÜYOR]`): EN kısaltma (`Dr. Smith`) ve ondalık (`3.5`) bölünür; JP tırnak içi cümle (`「…。」`) kapanış işareti dahil edilerek tek parça kalır.

**ÖLÇÜ:** Sahte motor aldığı token listelerini kaydeder. (a) 2 segment (3+1 cümle) → **tek** çağrı, 4 giriş, çıktı 2 segmente doğru dağıtılır. (b) **Y1 pozitif kontrolü:** KR `"A. B."` → 2 parça; JP `"A。B。"` → 2; karışık `"A! B？ C."` → 3. (c) **Y2 pozitif kontrolü:** `"A。？"`, `"「A。」"`, `"。。。"`, `"   "` → modele giden parça sayısı sırasıyla 1, 1, **0**, **0**; çıktıda `？`/`」`/`。。。` aynen. (d) Kayıpsızlık: harf/rakam içeren parçaların birleşimi kaynağın harf/rakam dizisine eşit. `real_check` #3 (JP paragraf) ve **#4 yeniden yazıldı**: KR 2 cümle **tek segment** → çıktı ≥ 2 cümle ve "bekliyor" + ("doğu" | "dogu") ikisi de var (v1'de KR önceden bölünmüş gidiyordu, kapı kördü).

## K4 · Dil kodu açık; `source_lang=None` desteklenmez

**DEĞİŞMEZ:** NLLB dil algılamaz. Kabul edilen kaynak kodu kümesi **sabit ve üç biçimli (O6):** NLLB (`jpn_Jpan`, `kor_Hang`, `zho_Hans`, `eng_Latn`), ISO 639-1 (`ja`, `ko`, `zh`, `en`), T-006 `OcrLanguage` değerleri (`japan`, `korean`, `chinese`, `english`). Büyük/küçük harf duyarsız. Bunların dışı ya da `None` → `ProviderUnavailable`. `target_lang`: `tr`, `tur`, `tur_Latn`, `turkish` (aynı üç biçim); dışı → `ProviderUnavailable`. Kaynak belirteci token dizisinin **başına**, `"</s>"` sona, `target_prefix=[["tur_Latn"]]` (C4; KRT doğruladı: `hypotheses[0][0]=="tur_Latn"`, `[1:]` doğru).
**ÖLÇÜ:** `source_lang=None`, `"xx"`, `"ja"` (ISO-639-1, NLLB kodu değil — eşleme tablosu `"ja"→jpn_Jpan` **kabul eder**), `"jpn_Jpan"` (doğrudan) → ilk ikisi `ProviderUnavailable`, son ikisi geçer. Sahte motor kaydı: ilk token `"jpn_Jpan"`, son `"</s>"`, `target_prefix` her satırda `["tur_Latn"]`. **İki dilde** (JAPAN, KOREAN).

## K5 · Yer tutucu korunumu — kontrol + kaba onarım (C9)

**DEĞİŞMEZ:** `Segment.placeholders` içindeki her dize çıktıda **tam alt dize** olarak aranır; **eksikse sona eklenir** (sırayla, boşlukla). Bu kaba ve belgelenir: model yer tutucuyu **düşürür** (C9: JP `{0}`) ya da **bozar** (O1: `[Mill]`→`[Mill'de]`, `<T0>`→`T0'yi`; EN'de `{PLAYER}` düşüyor). Bozulmuş biçim tam alt dize olarak bulunmadığı için eklenir → çıktıda **hem bozuk hem eklenmiş** kopya olabilir — `[ÖLÇÜLMÜYOR]`, docstring'e yazılır; gerçek çözüm Katman 0/2. `glossary_hits`, `tm_examples`, `style_profile`, `image_crops` **kabul edilir, uygulanmaz** — `[ÖLÇÜLMÜYOR]`.
**ÖLÇÜ:** Sahte motor yer tutucuyu düşüren çıktı verir → sonuçta yer tutucu **sonda** var; koruyan çıktı → **dokunulmaz** (iki nokta). `real_check` #5: JP `{0}` fixture'ı → çıktıda `{0}` var (onarım); EN → var (model korudu). AST: `glossary_hits` **okunmuyor** (v1'de kullanılmadığı gerçek; sessiz "uyguluyor" yanılsaması olmasın).

## K6 · Hata sınıflandırması

**DEĞİŞMEZ:** (a) `model_dir`'de **dört** zorunlu dosyadan biri yok → `ModelMissingError` **motor kurulmadan** (O4): `model.bin`, `sentencepiece.bpe.model`, `shared_vocabulary.txt`, `config.json` — v1 ilk ikisini sayıyordu; son ikisi yoksa CT2 `ProviderUnavailable` üretiyordu (KRT ölçtü). Mesajda eksik dosya adı. (b) Motor kurulumu/çevirisi istisna → `ProviderUnavailable` (`__cause__` özgün). (c) Hizalama → `ContractViolation` (K2). Yeniden deneme **yok**. `ProviderTimeout` v1'de **fırlatılmaz** (bütçe yok) — `[ÖLÇÜLMÜYOR]`.
**ÖLÇÜ:** Boş `tmp_path` → `ModelMissingError`, fabrika sayacı 0; boş dosyalar konunca fabrika çağrılır. Sahte fabrika `RuntimeError` → `ProviderUnavailable`, `__cause__` o.

## K7 · Model dosyaları BAYT ile açılır (C5)

**DEĞİŞMEZ:** `sentencepiece` ASCII-dışı yolu açamıyor (bu depo yolu `çeviri`). `SentencePieceProcessor(model_proto=bytes)`; CT2 yolu açabiliyor ama `str(model_dir)` **mutlak** verilir.
**ÖLÇÜ:** Gerçek fabrika AST'sinde `model_file=` **yok**, `model_proto=` **var**. `real_check` #7: `model_dir` ASCII-dışı bir geçici dizine **kopyalanır** (`tmp/çeviri-ölçüm/`), sağlayıcı oradan kurulur ve çevirir.

## K8 · İş parçacığı açık; ceza varsayılan kapalı (T-006 K3, C7)

**DEĞİŞMEZ:** `threads` aralık denetimli (`[1, cpu_count]`, `-1` yasak), `intra_threads` olarak CT2'ye; `inter_threads=1`. `repetition_penalty` **1.0** varsayılan (C7: >1 "Ba'at Çölü" halüsinasyonu); yapılandırılabilir, `[ÖLÇÜLMÜYOR]` kalite.
**ÖLÇÜ:** Sahte fabrika `params` kaydeder: `threads=4`/`8` iki nokta; `cpu_count` yaması ile `9` → `ValueError`. `repetition_penalty` çağrıya **aynen** gider; `1.0` iken `translate_batch`'e **hiç geçilmez** (CT2 varsayılanı).

## K9 · Süre ve `latency_ms`

**DEĞİŞMEZ:** `latency_ms` `translate`'in kendi duvar saati (`perf_counter`), motor kurulumu **hariç**. **Bütçe (Y3 düzeltildi):** JAPAN 4 cümle tek batch, beam=4 → ≤ **350 ms** medyan (ölçüldü 307-316; 79 ms/cümle = tasarım 4.2 aralığında). v1'in 200 ms'i **ölçülmeden yazılmıştı** ve her koşumda uyarı verip hiçbir uygulamayı ayırmıyordu. `beam_size=4` varsayılan kalır (C3 kalitesi bununla ölçüldü; beam=2 234 ms, greedy 183 ms — kalite altın set olmadan seçilemez, yapılandırılabilir). **`max_decoding_length=256`** açık geçilir (O2: CT2 varsayılanı da 256 ama pakette yazılı olmalı; 843 token'lık noktalamasız girdi 5.9 s dejenere, 500 cümlelik batch 22.6 s — v1 iptal edemez, `ProviderTimeout` `[ÖLÇÜLMÜYOR]`, docstring'e yazılır). CT2 girdiyi 1024 token'da **sessizce kırpar** — belgelenir.
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
