---
task: T-008
title: "SatırBirleştirici: aynı satırdaki kelime kutularını tek bloğa birleştirme (normalize öncesi)"
role: implementer
level: B
wave: 2
packet_version: 1
owns:
  - "src/ocr/satir_birlestirici.py"
  - "tests/unit/ocr/test_satir_birlestirici.py"
  - ".agents/tasks/T-008/evidence/**"
  - ".agents/tasks/T-008/delivery.md"
forbidden:
  - "src/contracts/**"
  - "src/ocr/normalizer.py"
  - "src/ocr/presets.py"
  - "src/ocr/rapid_engine.py"
  - "src/ocr/__init__.py"
  - "src/capture/**"
  - "src/translate/**"
  - "tests/unit/ocr/conftest.py"
  - "tests/unit/ocr/test_normalizer.py"
  - "tests/unit/ocr/test_rapid_engine.py"
  - "demo/**"
  - ".agents/tasks/T-008/real_check.py"
  - "diğer tüm dizinler"
depends_on: ["T-001", "T-004", "T-006"]
acceptance:
  - "python -m mypy --strict --explicit-package-bases src/ocr/satir_birlestirici.py"
  - "python -m pytest tests/unit/ocr/test_satir_birlestirici.py -q"
  - "python .agents/tasks/T-008/real_check.py"
  - "python -m pytest tests/unit/ocr/test_satir_birlestirici.py -q --cov=src.ocr.satir_birlestirici --cov-fail-under=95 --cov-report=term-missing"
  - "python -m pytest tests -q"
budget_ms: 1   # saf fonksiyon, 17 blok; ölçü: 1000 blok < 50 ms (K1)
---

> **Bu paket dokuz ön ölçüme dayanıyor:** `.agents/tasks/T-008/olgular.txt` (S1–S9). **Neden var:** `demo/canli_cevir.py` Korece ile koşulunca bulundu — KR tespit modeli **kelime** kutusu veriyor (17), normalizer yatayda birleştirmiyor (K11 "yatay örtüşme" dikey gruplama ön koşulu), 16 segment çıkıyor, çeviri kelime kelime gidiyor: "İhtiyar / Marcus. / Kasaba. / Seni. / Bekliyor. / Evet." Ne T-004 ne T-006 kapısı bunu görebilirdi. **Önce `olgular.txt`'yi oku.**

# Görev

Saf fonksiyon: `satirlari_birlestir(blocks: Sequence[TextBlock]) -> list[TextBlock]`. Aynı satırda yatay komşu kutuları tek `TextBlock`'a birleştirir. Pipeline'da `normalize`'dan **önce** çağrılır (T-004'e dokunulmaz — 125 ürün + 623 kör test dondurulmuş). Satır-düzeyi girdide **etkisiz** (JP/EN: 4 → 4).

**`src/ocr/satir_birlestirici.py`** — modül düzeyi sabitler `DIKEY_ORTUSME_ESIGI = 0.5`, `YATAY_BOSLUK_ESIGI = 1.0` (ölçü S6: örtüşme 1.0, boşluk ≤ 0.57×h; satır geçişi negatif → yanlış birleştirme yapısal olarak imkânsız). Girdi sırası **önemsiz**; çıktı okuma sırasında.

---

# Değişmezler

## K1 · Saf ve deterministik
**DEĞİŞMEZ:** I/O yok, global durum yok, aynı girdi → aynı çıktı; girdi listesi ve `TextBlock`'lar **değiştirilmez** (frozen zaten). 1000 blok < 50 ms.
**ÖLÇÜ:** T-004 `purity_check.py` desenine benzer AST denetimi (`open`/`print`/`random`/`time` yok, modül düzeyi mutable yok) — `real_check` içinde. İki ardışık çağrı eşit çıktı; girdi kopyası eşit kalır. 1000 rastgele blok (sabit tohum) süre ölçümü.

## K2 · Aynı satır ve komşuluk geometriyle (S6)
**DEĞİŞMEZ:** İki blok **aynı satırda** ⇔ dikey örtüşme ≥ `0.5 × min(h)`. Aynı satırda **komşu** ⇔ sağdaki `x > soldakinin x`'i **ve** boşluk (`sağ.x − (sol.x+sol.w)`) ≤ `1.0 × min(h)`. Boşluk negatif (çakışma) da komşudur (OCR kutuları taşabilir). Farklı `monitor_index` **asla** birleşmez. `h=0` ya da `w=0` blok **hiçbir şeyle** birleşmez (dejenere; aynen geçer).
**ÖLÇÜ:** Sentetik fixture'lar, **eşik sınırında iki nokta**: örtüşme `0.49×h` → ayrı, `0.51×h` → aynı; boşluk `0.99×h` → komşu, `1.01×h` → ayrı. Çakışan kutular (boşluk −5) → komşu. `monitor_index` 0/1 → ayrı. `h=0` → geçer. **Y1 pozitif kontrolü:** `real_check` KR 17 → **4**; JP 4 → 4; EN 4 → 4.

## K3 · Birleştirme karakteri betikle, dille değil (S7)
**DEĞİŞMEZ:** İki komşu metin arasına: ikisi de CJK (Hiragana/Katakana/CJK Unified) ise **hiç**; aksi hâlde (Hangul, Latin, karışık) **tek boşluk**. Betik = metindeki **ilk harfin** `unicodedata.name`'i (harf yoksa LATIN sayılır). Dil parametresi **yok** — JP satırında Latin kelime (`HP`) olabilir.
**ÖLÇÜ:** `("村の","長老")` → `"村の長老"`; `("장로","마르쿠스")` → `"장로 마르쿠스"`; `("elder","is")` → `"elder is"`; `("HP","が")` → `"HP が"`; `("42","点")` → `"42 点"` (rakam LATIN sayılır — belgelenir). Kaynak metinlerdeki baştaki/sondaki boşluk **korunmaz** (strip edilip tek boşlukla birleşir; JP'de strip sonrası boşsuz).

## K4 · İdempotent (S8)
**DEĞİŞMEZ:** `f(f(x)) == f(x)`.
**ÖLÇÜ:** KR gerçek çıktısı (`real_check`) ve 20 sentetik fixture'da iki uygulama eşit. Birleşik bloğun `line_boxes`'ı ikinci geçişte **değişmez** (yeniden sarılmaz).

## K5 · Birleşik bloğun alanları (S9)
**DEĞİŞMEZ:** `bbox` = parçaların eksen hizalı birleşimi, dört alan `type is int`, `monitor_index`/`dpi_scale` ilk parçadan; `confidence = min(parçalar)`; `line_boxes` = parçaların `bbox`'ları **x sırasında** (tek parçalı blokta `line_boxes` girdideki gibi, **dokunulmaz**); `text` K3'e göre.
**ÖLÇÜ:** 3 parçalı fixture: bbox = min x/y, max sağ/alt; `confidence` 0.9/0.5/0.7 → 0.5; `line_boxes` uzunluk 3, x artan; tek parça → nesne **aynı** (`is`) ya da eşit ve `line_boxes` korunmuş. `json.dumps(asdict(bbox))` geçer.

## K6 · Okuma sırası (T-004 K28 ile aynı tanım)
**DEĞİŞMEZ:** Çıktı `(bbox.y, bbox.x)` artan sırada. Girdi karıştırılmış olsa da aynı çıktı.
**ÖLÇÜ:** KR fixture'ı 5 farklı permütasyonda → aynı liste. Sentetik: 3 satır × 3 kutu karıştırılmış → 3 blok, y sırasında, her biri x sırasında birleşmiş.

## K7 · İki sütunlu düzen `[ÖLÇÜLMÜYOR]`
**DEĞİŞMEZ:** Aynı satırda `> 1.0×h` boşluk → ayrı blok (menü sütunları). Fixture yok; docstring damgalı, `real_check`'te yok.
**ÖLÇÜ:** Yalnız sentetik: iki kutu, boşluk `3×h` → 2 blok.

## K8 · Hata ve yozlaşmış girdi
**DEĞİŞMEZ:** Boş girdi → `[]`. Tek blok → `[aynı]`. `confidence` NaN → aynen (min NaN ile karşılaştırma **tanımsız**; NaN'lı parça `min`'de **atlanır**, hepsi NaN ise NaN). Negatif koordinat (ekran koordinatı, T-006 K4) → normal. Numpy skaler alanlı `Rect` → `ContractViolation` (T-005/T-006 dersi: `type is int` girişte denetlenir).
**ÖLÇÜ:** Her biri birer test; NaN iki nokta (bir NaN / hepsi NaN); `np.int64` alanlı blok → `ContractViolation`.

---

# Kabul kapısı — `real_check.py` (şefe ait; koş, yazma)
Gerçek OCR (T-006 fixture'ları, gerçek model, ayrı süreç):
1. KR 17 blok → **4** blok; her satırın `text`'i boşlukla birleşmiş; `line_boxes` uzunlukları `[2,5,5,5]`.
2. JP 4 → 4, `text` **birebir aynı**, EN 4 → 4 aynı (no-op).
3. **Uçtan uca (Y1 asıl kanıtı):** KR 17 blok → birleştir → `normalize(DIALOGUE)` → segment sayısı **≤ 4** (16 değil) → `LocalNmtProvider` → çıktıda "bekliyor" ve ("doğu"|"dogu") var; kelime-başına çeviri **yok** (hiçbir segment çevirisi tek kelimelik `"Evet."`/`"Seni."` değil).
4. İdempotens KR gerçek çıktısında.
5. Saflık AST denetimi.
6. 1000 blok süre.

# Teslim
`delivery.md` — `validate.py`; K2/K3/K7/K8 hem docstring hem `known_gaps`. **Paketle ölçümün çelişirse ölçümüne uy, itirazını yaz** — önceki üç görevde implementer bunu yedi kez yaptı, yedisinde de haklıydı.
