---
task: T-011
title: "GlossaryStore + terim gömme: oyuna özel terimler kaynağa hedef biçimiyle gömülür (Katman 0)"
role: implementer
level: B
wave: 2
packet_version: 2
owns:
  - "src/translate/sozluk.py"
  - "tests/unit/translate/test_sozluk.py"
  - ".agents/tasks/T-011/evidence/**"
  - ".agents/tasks/T-011/delivery.md"
forbidden:
  - "src/contracts/**"
  - "src/translate/local_nmt.py"
  - "src/ocr/**"
  - "src/capture/**"
  - "tests/unit/translate/conftest.py"
  - "tests/unit/translate/test_local_nmt.py"
  - "demo/**"
  - ".agents/tasks/T-011/real_check.py"
  - ".agents/tasks/T-011/fixtures/**"
  - "diğer tüm dizinler"
depends_on: ["T-001", "T-007"]
acceptance:
  - "python -m mypy --strict --explicit-package-bases src/translate/sozluk.py"
  - "python -m pytest tests/unit/translate/test_sozluk.py -q"
  - "python .agents/tasks/T-011/real_check.py"
  - "python -m pytest tests/unit/translate/test_sozluk.py -q --cov=src.translate.sozluk --cov-fail-under=95 --cov-report=term-missing"
  - "python -m pytest tests -q"
budget_ms: 50   # TEK bütçe: 1000 segment × fixture terimleri, lookup+gom medyan (real_check #7)
---

> **Paket sürümü 2.** v1 kırmızı takımdan **3 yüksek / 8 orta** ile döndü; şef Y1 ve Y3'ü kendi eliyle üretti (`sef_dogrulama/krt1_sef_kosumlari.txt`). **En önemli değişiklik:** sözlük, modelin **yanlış** çevirdiği terimler için; bildiği kelimeyi gömmek **zarar** verir (Y3: `검을 건넸습니다` → "Kılıç'i inşa ediyoruz"). Alt dize eşleme bileşiklerde anlam bozar (Y1: `검사` → "Kılıç geldi."); tek heceli/tek kanji terimler şemada reddedilir.
>
> **Bu paket yedi ön ölçüme dayanıyor:** `.agents/tasks/T-011/olgular.txt` (G1–G7). Tasarım 4.1 "motora zorunlu kısıt olarak enjekte edilir" der; NMT kısıt **alamaz** ve yer tutucu JP'de **kaybolur** (T-007 C9). Ölçülen tek çalışan yol: **terimi kaynağa hedef biçimiyle gömmek** — 21/21 korunuyor, İngilizce'ye kayma 0, üstelik çeviriyi **düzeltiyor** (bilinmeyen kelime yerine hedef terim geçince "su arabası" → "Değirmen", KR tekrar dejenerasyonu kayboluyor).

# Görev

İki parça, tek modül `src/translate/sozluk.py`:

1. **`GlossaryStore`** — tasarım bileşen 5, `lookup(text) -> list[TermHit]` (sözleşme `src/contracts/models.py:TermHit`). Sözlük oyun profili başına JSON'dan yüklenir (`{"terimler": [{"kaynak": "マルクス", "hedef": "Marcus", "not": "..."}]}`); v1'de profil dosyası yolu yapıcıya verilir, `ProfileStore` yok.
2. **`terimleri_gom(segments, hits) -> tuple[Segment, ...]`** — saf ön-işlemci, `LocalNmtProvider.translate`'ten **önce** çağrılır (T-007 **dondurulmuş**, `glossary_hits`'i okumaz ve okumayacak). Her `TermHit` aralığı `target_term` ile değiştirilir; **aralık dışı her karakter aynen kalır** (KR ekler `을/를/가/는`, JP parçacıklar `を/が/は` terime bitişik — G1: `방앗간을` → `Değirmen을`, model doğru çekim üretti).

---

# Değişmezler

## K1 · Eşleme: en uzun önce, örtüşmesiz, **sınır kuralı her betikte aynı** (G5, G6, Y1)

**DEĞİŞMEZ:** `lookup(text, placeholders=())` terimleri **uzunluk azalan** sırayla arar; eşleşen aralıkla örtüşen kısa terim atlanır. **`\b` kullanılmaz** (CJK'da `Marcusが` eşleşmez — KRT). Bir aday aralık ancak **her iki ucunda sınır** varsa eşleşir; sınır = metin ucu · boşluk · Unicode noktalama (`P*`) · JP parçacık (`をがはにのでともへや`) · KR ek (`을 를 이 가 은 는 에 에서 으로 로 와 과 도 의 만 께서 부터 까지`, en uzun önce, **ekten sonra da sınır**) · **sözlükteki başka bir terimin başlangıcı** (`長老マルクス` → ikisi de). Bilinen sınır: `검은` (`검`+ek `은`) kuraldan geçer → **tek hangul heceli / tek kanji terimler şemada reddedilir** (K6). Latin kaynakta büyük/küçük duyarsız: `re.IGNORECASE` **orijinal** metinde (casefold indeks kaydırır — KRT). Aynı terim n geçiş → n hit, `start` artan, **kodpoint** indeksi; `segment_index=None` (sözleşme).
**ÖLÇÜ (G6'nın 17'si + KRT'nin 8'i, hepsi test):** `村人`/`剣士`/`검사`/`방앗간집`/`검은 옷`/`真剣に`/`中村` → **eşleşmez**; `村は`/`剣を`/`검을`/`방앗간에서`/`Marcusが`/`장로 마르쿠스`/`長老マルクス` (iki hit) → eşleşir. `"水車小屋"`+`"水車"` → yalnız uzun (iki sıralı sözlük). `MARCUS`/`marcus` eşleşir, indeksler orijinal metne göre doğru (`İstanbul` casefold tuzağı testi). Boş sözlük/metin → `[]`.

## K2 · Gömme: aralık dışı karakter dokunulmaz, hits geçersizse `ContractViolation`
**DEĞİŞMEZ:** `terimleri_gom`, her segment için o segmentin hit'lerini (`segment_index` eşleşen) `start` **azalan** sırayla uygular (indeksler kaymasın). Çıktı `Segment`: `text` gömülü, `bbox/speaker/placeholders/source_blocks` **aynen**. Hit aralığı segment metniyle **tutarsızsa** (`text[start:end] != source_term`, aralık dışı, örtüşen iki hit) → `ContractViolation` (sessiz kayma yok). `hits` boş → **aynı** segment nesneleri (`is`).
**ÖLÇÜ:** `"방앗간을 지나"` + hit(방앗간→Değirmen) → `"Değirmen을 지나"` (ek korundu). İki hit aynı segmentte, biri metnin başında biri sonunda → ikisi de doğru yerde (start-azalan uygulama). `text[start:end] != source_term` → `ContractViolation`; örtüşen hitler → `ContractViolation`. `placeholders=("{0}",)` taşınıyor. `speaker` dokunulmamış. Boş hits → `is`.

## K3 · Terim yer tutucu ile çakışmaz (Y2)
**DEĞİŞMEZ:** `lookup(text, placeholders)` — `placeholders` içindeki her dizenin **tüm** geçişleri korunan aralıktır; onlarla örtüşen aday eşleşmez. `terimleri_gom` de `segment.placeholders`'ı **aynı** kurala göre denetler (hit yer tutucuyla örtüşüyorsa `ContractViolation`).
**ÖLÇÜ:** `"{PLAYER}は村にいます"` + `PLAYER→Oyuncu` + `placeholders=("{PLAYER}",)` → hit **yok**; `placeholders=()` → hit **var** (pozitif kontrol). `{0}マルクス` bitişik → `マルクス` eşleşir, `{0}` dokunulmaz. `real_check` #3 segmentlere `placeholders` verir.

## K4 · Hedef her zaman ilk harfi büyük gömülür; sözlük yalnız modelin yanlış çevirdiği terimler için (G7, **Y3**)
**DEĞİŞMEZ:** Gömülen `target_term`'ün ilk harfi **büyük** yapılır (JP'de küçük `değirmen` **kayboluyor** — G7; büyük 21/21 korundu). Kesme işareti (`Değirmen'de`) kozmetik, belgelenir. **Yazarlık kuralı (docstring + JSON şeması açıklaması):** sözlüğe yalnız modelin **yanlış** çevirdiği terimler girer — bildiği bir kelimeyi gömmek çeviriyi **bozar** (Y3: `검을 건넸습니다` ham "Kılıcını çeker", gömülü "Kılıç'i inşa ediyoruz"). `ozel_ad` bayrağı kalkar; yerine `not` alanı (serbest metin, `TermHit.note`).
**ÖLÇÜ:** `değirmen` girdisi → gömülen `Değirmen`; `marcus` → `Marcus`; zaten büyük → aynen. `real_check` #1 fixture'ı yalnız yanlış-çevrilen terimleri içerir (bkz. kapı).

## K5 · Saf, deterministik, hızlı
**DEĞİŞMEZ:** `lookup` ve `terimleri_gom` I/O yapmaz (yükleme yalnız `GlossaryStore.__init__`/`yukle`), global durum yok. 1000 segment × 50 terim < 50 ms.
**ÖLÇÜ:** AST (T-008 deseniyle); iki çağrı eşit; süre.

## K6 · Yükleme, şema ve hata (Y1, Y3, KRT-orta)
**DEĞİŞMEZ:** JSON `{"terimler": [{"kaynak": str, "hedef": str, "not": str?}]}`. Şema reddi (`ValueError`, mesajda terim): kaynak/hedef boş · tekrar eden kaynak · **kaynak tek hangul hecesi ya da tek kanji** (sınır kuralı ayrıştıramaz — `kisa_terim_izni: true` ile opt-in) · **hedefte cümle sonu işareti** (`.!?。！？` — T-007 bölmesini tetikler; "St. Marcus" yasak) · hedefte yer tutucu biçimi (`{`/`}`). Kaynak ve metin **NFC** normalize edilir; indeksler NFC metne göre; `terimleri_gom` segment metnini **aynı** NFC ile normalize eder (KRT: NFD KR 3→9 kodpoint). Dosya yoksa `FileNotFoundError` sarılmaz (model değil). Dosya **bayt** ile açılır.
**ÖLÇÜ:** Her red sınıfı birer test (`검`, `村`, `St. Marcus`, `{0}`); `kisa_terim_izni` ile `검` kabul; NFD girdi NFC sözlükle eşleşir ve gömme doğru yerde; `tmp_path/"çeviri"` altında JSON.

## K7 · `segment_index` denetimi
**DEĞİŞMEZ:** `terimleri_gom`'a gelen hit'in `segment_index`'i `None` ya da aralık dışı → `ContractViolation` (sessiz yutma yok — KRT).
**ÖLÇÜ:** `None`, `-1`, `len(segments)` → üçü de `ContractViolation`.

---

# Kabul kapısı — `real_check.py` (şefe ait; koş, yazma)
Gerçek NMT, `fixtures/sozluk_ornek.json` **v2** (yalnız modelin yanlış çevirdiği terimler: `マルクス/마르쿠스→Marcus`, `アイラ/아일라→Ayla`, `水車小屋/방앗간/mill→Değirmen`, `長老/장로/elder→İhtiyar`; `剣/검/村/마을` **çıkarıldı** — model biliyor, Y3):
1. G1'in 6 cümlesi: lookup → gom → translate → hedef terim var (6/6).
2. **Pozitif kontrol:** gömmeden → en az 2/6'da hedef yok (deterministik 4/6 — KRT).
3. Yer tutucu: `{PLAYER}は村にいます` + `placeholders` → hit yok; `{0}マルクス` → `Marcus` var, `{0}` var.
4. KR `방앗간을 지나…` gömülü → "Değirmen" var, tekrar yok.
5. Unvan: `장로 마르쿠스` → "Elder" yok, "İhtiyar"+"Marcus" var.
6. **Y1 negatif:** ayrı geçici sözlükte `검` → şema `ValueError` mesajında `검`; `kisa_terim_izni` ile kabul edilirse `검사가 왔습니다.` üzerinde lookup **boş** (sınır kuralı) ama `검은 옷` üzerinde **dolu** (bilinen sınır — belgelenir, düşürmez).
7. 1000 segment × fixture: lookup+gom medyan < 50 ms.

# Teslim
`delivery.md`; K1/K2/K3/K6 docstring + `known_gaps`. **Ölçümün paketle çelişirse ölçümüne uy, yaz.** Metin basma; model/sağlayıcı/araç adı yazma.
