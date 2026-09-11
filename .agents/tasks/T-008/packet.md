---
task: T-008
title: "SatırBirleştirici: aynı satırdaki kelime kutularını tek bloğa birleştirme (normalize öncesi)"
role: implementer
level: B
wave: 2
packet_version: 2
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
budget_ms: 1   # saf fonksiyon; ölçü: 1000 blok < 50 ms (sırala + tek geçiş = O(n log n); KRT: naif O(n²) 357 ms — bütçe algoritmayı seçiyor, bilinçli)
---

> **Paket sürümü 2.** v1 kırmızı takımdan **3 yüksek / 6 orta** ile döndü; şef Y1 ve Y3'ü kendi eliyle üretti (`sef_dogrulama/krt1_sef_kosumlari.txt`). **Y1 kapsam değiştirdi:** Korece tanıma modeli cümle sonu noktalarını düşürüyor — birleştirme tek başına KR'yi kurtarmaz; o **T-009**. Bu paket yalnız kelime→satır birleştirmeyi garanti eder.
>
> **Bu paket dokuz ön ölçüme dayanıyor:** `.agents/tasks/T-008/olgular.txt` (S1–S9). **Neden var:** `demo/canli_cevir.py` Korece ile koşulunca bulundu — KR tespit modeli **kelime** kutusu veriyor (17), normalizer yatayda birleştirmiyor (K11 "yatay örtüşme" dikey gruplama ön koşulu), 16 segment çıkıyor, çeviri kelime kelime gidiyor: "İhtiyar / Marcus. / Kasaba. / Seni. / Bekliyor. / Evet." Ne T-004 ne T-006 kapısı bunu görebilirdi. **Önce `olgular.txt`'yi oku.**

# Görev

Saf fonksiyon: `satirlari_birlestir(blocks: Sequence[TextBlock]) -> list[TextBlock]`. Aynı satırda yatay komşu kutuları tek `TextBlock`'a birleştirir. Pipeline'da `normalize`'dan **önce** çağrılır (T-004'e dokunulmaz — 125 ürün + 623 kör test dondurulmuş). Satır-düzeyi girdide **etkisiz** (JP/EN: 4 → 4).

**`src/ocr/satir_birlestirici.py`** — modül düzeyi sabitler `DIKEY_ORTUSME_ESIGI = 0.5`, `YATAY_BOSLUK_ESIGI = 0.75` (ölçü S6 + KRT Y3: KR kelime boşluğu ≤ 0.57×h, 1-em boşluk sınıfı ≥ 0.97×h). Girdi sırası **önemsiz**; çıktı okuma sırasında.

---

# Değişmezler

## K1 · Saf ve deterministik
**DEĞİŞMEZ:** I/O yok, global durum yok, aynı girdi → aynı çıktı; girdi listesi ve `TextBlock`'lar **değiştirilmez** (frozen zaten). 1000 blok < 50 ms.
**ÖLÇÜ:** T-004 `purity_check.py` desenine benzer AST denetimi (`open`/`print`/`random`/`time` yok, modül düzeyi mutable yok) — `real_check` içinde. İki ardışık çağrı eşit çıktı; girdi kopyası eşit kalır. 1000 rastgele blok (sabit tohum) süre ölçümü.

## K2 · Aynı satır ve komşuluk geometriyle — ALGORİTMA TANIMLI (S6, **Y2, Y3**)

**DEĞİŞMEZ:** Girdi `(bbox.y, bbox.x, girdi indeksi)` ile sıralanır (T-004 K28 okuma sırası; üçüncü anahtar bağları çözer — KRT: `(y,x)` bağlarında 20/20 permütasyon farklı çıktı veriyordu). **Tek geçiş:** her blok, açık satır grubunun **ilk** bloğuyla dikey örtüşmesi ≥ `0.5 × min(h)` **ve** grubun **son** bloğuna göre `x` ilerliyor **ve** boşluk ≤ `0.75 × min(h_orijinal)` ise gruba eklenir; aksi hâlde yeni grup açılır. Eşikler **orijinal** blok yükseklikleriyle hesaplanır, birleşik yükseklikle **değil** (Y2: birleşik `h` büyüyünce ikinci geçişte yeni komşuluk doğuyordu). Farklı `monitor_index` asla birleşmez; `h=0`/`w=0` hiçbir şeyle birleşmez.

**Eşik 0.75 (Y3):** KR kelime boşluğu en çok `0.57×h` (S6); gerçek 1-em boşluk sınıfı `0.97–1.06×h` (KRT gerçek OCR: JP ideografik-boşluklu seçim satırı 1.03, KR etiket|değer 1.06). v1'in `1.0`'ı bu sınıfın **içindeydi**. Gri bölge `[0.6, 0.95]` **`[ÖLÇÜLMÜYOR]`** (docstring): "120 / 150" içindeki `/`–`150` boşluğu 1.04 → ayrılır, belgelenir.

**S6'nın "yanlış birleştirme yapısal olarak imkânsız" cümlesi GERİ ÇEKİLDİ** (KRT: uzun kutu köprüsü, iç içe kutu ile 14 → 24 karakter). Satır geçişi çoğunlukla negatif ama **her zaman** değil.

**ÖLÇÜ:** Sentetik, **eşik sınırında iki nokta:** örtüşme `0.49/0.51×h`; boşluk `0.74/0.76×h`; çakışma (−5) → komşu; `monitor_index` 0/1 → ayrı; `h=0` → geçer. Zincir: A–B komşu, B–C komşu, A–C değil → **tek** blok (grup son bloğa göre ilerler — tanım gereği geçişli). **Gerçek OCR iki yönlü pozitif kontrol** (`real_check`): `dlg_KR` 17 → **4** (kelimeler birleşir); `fixtures/menu_KR_EN.png` etiket|değer satırları (boşluk 13–16×h) **hiç birleşmez** — KR 13 kutuda her satır ≥ 2 blok kalır, EN 8 → 8. Eşiği `2.0`/`10.0` yapan mutant `dlg_KR`'de yine 4 verir (KRT ölçtü) — bu yüzden **menü fixture'ı zorunlu**: orada `10.0` birleştirir ve düşer.

## K3 · Birleştirme karakteri betikle, dille değil (S7)
**DEĞİŞMEZ:** İki komşu metin arasına: ikisi de CJK (Hiragana/Katakana/CJK Unified) ise **hiç**; aksi hâlde (Hangul, Latin, karışık) **tek boşluk**. Betik = metindeki **ilk harfin** `unicodedata.name`'i (harf yoksa LATIN sayılır). Dil parametresi **yok** — JP satırında Latin kelime (`HP`) olabilir.
**ÖLÇÜ:** `("村の","長老")` → `"村の長老"`; `("장로","마르쿠스")` → `"장로 마르쿠스"`; `("elder","is")` → `"elder is"`; `("HP","が")` → `"HP が"`; `("42","点")` → `"42 点"` (rakam LATIN sayılır — belgelenir). Kaynak metinlerdeki baştaki/sondaki boşluk **korunmaz** (strip edilip tek boşlukla birleşir; JP'de strip sonrası boşsuz).

## K4 · Tek uygulama — idempotens DEĞİŞMEZ DEĞİL (Y2)

**DEĞİŞMEZ:** Fonksiyon pipeline'da **bir kez** çağrılır (`normalize`'dan hemen önce). İkinci uygulama tanımsızdır: birleşik blokların yüksekliği büyüdüğü için `f(f(x)) == f(x)` **genel olarak tutmaz** (KRT: 4000 rastgele girdide 115 ihlal; şef kabul etti). v1 bunu **yalan söyleyerek** değişmez yazmıştı. Docstring `[ÖLÇÜLMÜYOR]` + "bir kez çağır" uyarısı.
**ÖLÇÜ:** Yok (kaldırıldı). Yalnız belge: docstring'de "idempotent" **sözcüğü geçmez** (AST).

## K5 · Birleşik bloğun alanları (S9)
**DEĞİŞMEZ:** `bbox` = parçaların eksen hizalı birleşimi, dört alan `type is int`, `monitor_index`/`dpi_scale` ilk parçadan; `confidence = min(parçalar)`; `line_boxes` = parçaların `bbox`'ları **x sırasında** (tek parçalı blokta `line_boxes` girdideki gibi, **dokunulmaz**); `text` K3'e göre.
**ÖLÇÜ:** 3 parçalı fixture: bbox = min x/y, max sağ/alt; `confidence` 0.9/0.5/0.7 → 0.5; `line_boxes` uzunluk 3, x artan; tek parça → nesne **aynı** (`is`) ya da eşit ve `line_boxes` korunmuş. `json.dumps(asdict(bbox))` geçer.

## K6 · Okuma sırası (T-004 K28 ile aynı tanım)
**DEĞİŞMEZ:** Çıktı `(bbox.y, bbox.x)` artan sırada; bağlar **girdi indeksiyle** çözülür (K2'nin sıralaması). Girdi karıştırılmışsa çıktı **bağsız** durumda aynıdır; bağlı durumda girdi sırasına bağlıdır — belgelenir.
**ÖLÇÜ:** KR fixture'ı (bağsız — KRT ölçtü) 5 permütasyonda → aynı liste. Bağlı sentetik (`y` eşit, `x` eşit iki kutu) → girdi sırası korunur, **ölçülür** (bu K6'nın sınırıdır). Sentetik: 3 satır × 3 kutu karıştırılmış → 3 blok, y sırasında, her biri x sırasında birleşmiş.

## K7 · İki sütunlu düzen — gerçek fixture ile ölçülür (v1'de `[ÖLÇÜLMÜYOR]` idi)
**DEĞİŞMEZ:** Aynı satırda `> 0.75×h` boşluk → ayrı blok (menü sütunları). `fixtures/menu_KR_EN.png` (şef üretti, gerçek OCR: etiket|değer boşluğu 13–16×h).
**ÖLÇÜ:** Sentetik iki kutu `3×h` → 2 blok; gerçek: `real_check` #4.

## K8 · Yozlaşmış girdi
**DEĞİŞMEZ:** Boş → `[]`. Tek blok → `[aynı nesne]` (`is`). `confidence` NaN: `min` **NaN olmayanlar** üzerinden; hepsi NaN → NaN (Python `min` NaN'da sıraya bağlıdır — KRT ölçtü; bu yüzden **açık** süzme). Negatif koordinat → normal. `h<0`/`w<0` → `h=0` gibi (birleşmez, geçer). Numpy denetimi **yok** (KRT: hiçbir üretici numpy vermiyor; T-006 `int` garantili — gereksiz yüzey).
**ÖLÇÜ:** Her biri birer test; NaN iki nokta (biri NaN / hepsi NaN) ve **sıra bağımsızlığı** (NaN başta / sonda → aynı sonuç).

---

# Kabul kapısı — `real_check.py` (şefe ait; koş, yazma)
Gerçek OCR (T-006 fixture'ları + `T-008/fixtures/menu_KR_EN.png`), ayrı süreç:
1. `dlg_KR` 17 → **4** blok; `line_boxes` uzunlukları `[2,5,5,5]`; her satır boşlukla birleşmiş.
2. `dlg_JP` 4 → 4, `dlg_EN` 4 → 4 **birebir** (no-op).
3. **Uçtan uca — yeniden kapsamlandı (Y1):** KR → birleştir → `normalize(DIALOGUE)` → segment sayısı **≤ 4** → NMT → **hiçbir** segment çevirisi tek kelimelik değil (`"Evet."`, `"Seni."` sınıfı — kelime-kelime çeviri **yok**). "doğu" beklentisi **kaldırıldı**: KR tanıma noktayı düşürüyor, cümle kaybı T-009'un konusu; v1 kapısı bunu ölçmeden yazmıştı (şef hatası, §4.6/10).
4. **Menü fixture'ı (Y3 pozitif kontrol):** KR 13 kutuda her satır ≥ 2 blok kalır (etiket|değer birleşmez); EN 8 → 8. `YATAY_BOSLUK_ESIGI=10.0` mutantı burada **düşer**.
5. Saflık AST. 6. 1000 blok < 50 ms.

# Teslim
`delivery.md` — `validate.py`; K2/K3/K7/K8 hem docstring hem `known_gaps`. **Paketle ölçümün çelişirse ölçümüne uy, itirazını yaz** — önceki üç görevde implementer bunu yedi kez yaptı, yedisinde de haklıydı.
