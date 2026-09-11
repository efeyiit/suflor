---
task: T-011
title: "GlossaryStore + terim gömme: oyuna özel terimler kaynağa hedef biçimiyle gömülür (Katman 0)"
role: implementer
level: B
wave: 2
packet_version: 1
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
budget_ms: 1   # saf metin işlemi; 1000 segment × 50 terim < 50 ms
---

> **Bu paket dört ön ölçüme dayanıyor:** `.agents/tasks/T-011/olgular.txt` (G1–G4). Tasarım 4.1 "motora zorunlu kısıt olarak enjekte edilir" der; NMT kısıt **alamaz** ve yer tutucu JP'de **kaybolur** (T-007 C9). Ölçülen tek çalışan yol: **terimi kaynağa hedef biçimiyle gömmek** — 21/21 korunuyor, İngilizce'ye kayma 0, üstelik çeviriyi **düzeltiyor** (bilinmeyen kelime yerine hedef terim geçince "su arabası" → "Değirmen", KR tekrar dejenerasyonu kayboluyor).

# Görev

İki parça, tek modül `src/translate/sozluk.py`:

1. **`GlossaryStore`** — tasarım bileşen 5, `lookup(text) -> list[TermHit]` (sözleşme `src/contracts/models.py:TermHit`). Sözlük oyun profili başına JSON'dan yüklenir (`{"terimler": [{"kaynak": "マルクス", "hedef": "Marcus", "not": "..."}]}`); v1'de profil dosyası yolu yapıcıya verilir, `ProfileStore` yok.
2. **`terimleri_gom(segments, hits) -> tuple[Segment, ...]`** — saf ön-işlemci, `LocalNmtProvider.translate`'ten **önce** çağrılır (T-007 **dondurulmuş**, `glossary_hits`'i okumaz ve okumayacak). Her `TermHit` aralığı `target_term` ile değiştirilir; **aralık dışı her karakter aynen kalır** (KR ekler `을/를/가/는`, JP parçacıklar `を/が/は` terime bitişik — G1: `방앗간을` → `Değirmen을`, model doğru çekim üretti).

---

# Değişmezler

## K1 · Eşleme: en uzun önce, örtüşmesiz, betik-uygun sınır
**DEĞİŞMEZ:** `lookup` sözlükteki terimleri **uzunluk azalan** sırayla arar; bir aralık eşleşince **örtüşen** daha kısa terim atlanır. JP/ZH/KR için alt dize eşleme (ekler bitişik); Latin kaynak (EN) için **kelime sınırı** (`\bmill\b` — `windmill` eşleşmez). Aynı terim birden çok geçerse her geçiş ayrı `TermHit`. `start/end` **kodpoint** indeksi (Python `str`); `segment_index` `lookup`'ta `None` (sözleşme), `terimleri_gom` doldurur.
**ÖLÇÜ:** `"水車小屋"` ve `"水車"` ikisi de sözlükte → yalnız uzun eşleşir (**iki nokta:** uzun önce/kısa önce sıralı sözlük aynı sonuç). `"mill"`/`"windmill"` EN → `windmill` içinde `mill` eşleşmez; boşluklu/noktalı sınır eşleşir. Terim 2× → 2 hit, `start` artan. Boş sözlük → `[]`. Boş metin → `[]`. Büyük/küçük: Latin kaynakta **duyarsız** (`Marcus`/`MARCUS`), CJK/KR'de anlamsız (aynen).

## K2 · Gömme: aralık dışı karakter dokunulmaz, hits geçersizse `ContractViolation`
**DEĞİŞMEZ:** `terimleri_gom`, her segment için o segmentin hit'lerini (`segment_index` eşleşen) `start` **azalan** sırayla uygular (indeksler kaymasın). Çıktı `Segment`: `text` gömülü, `bbox/speaker/placeholders/source_blocks` **aynen**. Hit aralığı segment metniyle **tutarsızsa** (`text[start:end] != source_term`, aralık dışı, örtüşen iki hit) → `ContractViolation` (sessiz kayma yok). `hits` boş → **aynı** segment nesneleri (`is`).
**ÖLÇÜ:** `"방앗간을 지나"` + hit(방앗간→Değirmen) → `"Değirmen을 지나"` (ek korundu). İki hit aynı segmentte, biri metnin başında biri sonunda → ikisi de doğru yerde (start-azalan uygulama). `text[start:end] != source_term` → `ContractViolation`; örtüşen hitler → `ContractViolation`. `placeholders=("{0}",)` taşınıyor. `speaker` dokunulmamış. Boş hits → `is`.

## K3 · Terim yer tutucu ile çakışmaz
**DEĞİŞMEZ:** `Segment.placeholders` içindeki bir dize ile örtüşen aralık eşleşmez (yer tutucu `{0}` içinde terim aranmaz; terim yer tutucuyu içeremez).
**ÖLÇÜ:** `"{PLAYER}は村にいます"` + sözlükte `"PLAYER"→"Oyuncu"` → hit **yok**. Sözlükte `"村"→"köy"` → hit var, yer tutucu bozulmadı.

## K4 · Büyük/küçük harf bayrağı (G4)
**DEĞİŞMEZ:** Sözlük girdisi `"ozel_ad": true|false` taşır (varsayılan `true`). `target_term` **aynen** gömülür — bu bayrak v1'de yalnız **belgeleme** ve `TermHit.note`'a yazılır (`"ozel ad"`/`"cins isim"`); model kesme işaretini ("Değirmen'de") ad için doğru üretiyor, cins isim için ne ürettiği `[ÖLÇÜLMÜYOR]` (real_check raporlar, düşürmez).
**ÖLÇÜ:** JSON'da bayrak yok → `note` `"ozel ad"`; `false` → `"cins isim"`.

## K5 · Saf, deterministik, hızlı
**DEĞİŞMEZ:** `lookup` ve `terimleri_gom` I/O yapmaz (yükleme yalnız `GlossaryStore.__init__`/`yukle`), global durum yok. 1000 segment × 50 terim < 50 ms.
**ÖLÇÜ:** AST (T-008 deseniyle); iki çağrı eşit; süre.

## K6 · Yükleme ve hata
**DEĞİŞMEZ:** JSON yoksa → `ModelMissingError` **değil** (model değil) — `FileNotFoundError` **sarılmadan** (sözleşme sessiz; belgelenir). Bozuk JSON / şema dışı (kaynak boş, hedef boş, tekrar eden kaynak) → `ValueError` **mesajda satır/terim**. Kaynak terimler NFC normalize edilir (T-004 dersi: **NFC yeterli değil** — `Mn/Mc` hâlâ sorun; burada yalnız eşitlik için NFC, belgelenir). Dosya **bayt** ile açılır (ASCII-dışı yol, T-007 C5).
**ÖLÇÜ:** Her hata sınıfı birer test; NFC/NFD aynı terim eşleşir; `tmp_path / "çeviri"` altındaki JSON açılır.

---

# Kabul kapısı — `real_check.py` (şefe ait; koş, yazma)
Gerçek NMT ile, `fixtures/sozluk_ornek.json` (Marcus, Ayla, Kılıç, Değirmen, Han, 장로→İhtiyar, 長老→İhtiyar):
1. G1'in 6 cümlesi: lookup → gom → translate → hedef terim çıktıda **var** (6/6).
2. **Pozitif kontrol:** aynı cümleler **gömmeden** → en az 2'sinde hedef terim **yok** ("Marks", "su arabası").
3. KR `방앗간을 지나 동쪽 길로 가십시오.` gömülü → çıktıda "Değirmen" var **ve** "Doğu'ya doğru Doğu'ya doğru" tekrarı **yok** (G1: dejenerasyon kalkıyor).
4. Unvan: `장로 마르쿠스` iki hit (장로→İhtiyar, 마르쿠스→Marcus) → çıktıda "Elder" **yok**, "İhtiyar" ve "Marcus" var (G4 sızması kapanır).
5. Cins isim raporu: `"değirmen"` küçük harf gömülü → çıktı **raporlanır** (kesme işareti var mı), düşürmez.
6. 1000 segment süre.

# Teslim
`delivery.md`; K1/K2/K3/K6 docstring + `known_gaps`. **Ölçümün paketle çelişirse ölçümüne uy, yaz.** Metin basma; model/sağlayıcı/araç adı yazma.
