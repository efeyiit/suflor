---
task: T-011
title: "GlossaryStore + terim gömme: oyuna özel terimler kaynağa hedef biçimiyle gömülür (Katman 0)"
role: implementer
level: B
wave: 2
packet_version: 3
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

> **Paket sürümü 3 (tur 2).** İki kör tester tur 1'de **onay** verdi ama aynı sınıfı bağımsız buldu (reddedilen komşu aday sınır veriyor → `millstones` → `Değirmenstones`) ve Tester-B oyun metninin en yaygın sınıfını gösterdi (JP saygı ekleri, KR `에게/님/들` **hiç** eşleşmiyor → modelde "Bay Marks", "Markos'a"). İkisi de **paket hatası**; şef hepsini yeniden üretti (`sef_dogrulama/tur1_tester_bulgulari_statik.txt`, `sef_karari-tur1.md`). v3 farkları **▲** ile işaretli.
>
> **Paket sürümü 2.** v1 kırmızı takımdan **3 yüksek / 8 orta** ile döndü; şef Y1 ve Y3'ü kendi eliyle üretti (`sef_dogrulama/krt1_sef_kosumlari.txt`). **En önemli değişiklik:** sözlük, modelin **yanlış** çevirdiği terimler için; bildiği kelimeyi gömmek **zarar** verir (Y3: `검을 건넸습니다` → "Kılıç'i inşa ediyoruz"). Alt dize eşleme bileşiklerde anlam bozar (Y1: `검사` → "Kılıç geldi."); tek heceli/tek kanji terimler şemada reddedilir.
>
> **Bu paket yedi ön ölçüme dayanıyor:** `.agents/tasks/T-011/olgular.txt` (G1–G7). Tasarım 4.1 "motora zorunlu kısıt olarak enjekte edilir" der; NMT kısıt **alamaz** ve yer tutucu JP'de **kaybolur** (T-007 C9). Ölçülen tek çalışan yol: **terimi kaynağa hedef biçimiyle gömmek** — 21/21 korunuyor, İngilizce'ye kayma 0, üstelik çeviriyi **düzeltiyor** (bilinmeyen kelime yerine hedef terim geçince "su arabası" → "Değirmen", KR tekrar dejenerasyonu kayboluyor).

# Görev

İki parça, tek modül `src/translate/sozluk.py`:

1. **`GlossaryStore`** — tasarım bileşen 5, `lookup(text) -> list[TermHit]` (sözleşme `src/contracts/models.py:TermHit`). Sözlük oyun profili başına JSON'dan yüklenir (`{"terimler": [{"kaynak": "マルクス", "hedef": "Marcus", "not": "..."}]}`); v1'de profil dosyası yolu yapıcıya verilir, `ProfileStore` yok.
2. **`terimleri_gom(segments, hits) -> tuple[Segment, ...]`** — saf ön-işlemci, `LocalNmtProvider.translate`'ten **önce** çağrılır (T-007 **dondurulmuş**, `glossary_hits`'i okumaz ve okumayacak). Her `TermHit` aralığı `target_term` ile değiştirilir; **aralık dışı her karakter aynen kalır** (KR ekler `을/를/가/는`, JP parçacıklar `を/が/は` terime bitişik — G1: `방앗간을` → `Değirmen을`, model doğru çekim üretti).

---

# Değişmezler

## K1 · Eşleme: en uzun önce, örtüşmesiz, **sınır kuralı her betikte aynı** (G5, G6, Y1; ▲ tur 2)

**DEĞİŞMEZ:** `lookup(text, placeholders=())` terimleri **uzunluk azalan** sırayla arar; eşleşen aralıkla örtüşen kısa terim atlanır. **`\b` kullanılmaz** (CJK'da `Marcusが` eşleşmez — KRT). Bir aday aralık ancak **her iki ucunda sınır** varsa eşleşir; sınır:
- metin ucu · boşluk · Unicode noktalama (`P*`);
- JP parçacık/ek (**iki tarafta**): `を が は に の で と も へ や` **▲ + saygı/kopula ekleri (sağda):** `さん 様 殿 君 ちゃん 達 たち って だ から まで より か よ ね`;
- KR ek (**sağda**, en uzun önce, **ekten sonra da sınır**, zincir ≤ 2): `을 를 이 가 은 는 에 에서 으로 로 와 과 도 의 만 께서 부터 까지` **▲ +** `에게 한테 께 님 씨 야 아 랑 이랑 들 처럼 보다 마다 밖에 조차 라고 라면 입니다 이다`;
- **▲ bitişik sözlük terimi — ZİNCİR kuralı (Tester-A O-A3 + Tester-B O-B5, bağımsız):** sözlükteki başka bir terimin bitişik olması **tek başına sınır değildir**. Bitişik adaylar bir **zincir** oluşturur (`長老マルクス`, `マルクス長老`, `長老マルクスアイラ`); zincir ancak **iki dış ucu da yukarıdaki gerçek sınırlardan biriyse** bütünüyle eşleşir, aksi hâlde zincirin **hiçbir** üyesi eşleşmez. `windmills` = `wind`+`mill`+`s` → dış uç `s` sınır değil → **0 hit** (tur 1: `Rüzgarmills`, gerçek motorda değirmen kayboldu); `millstones` → 0; `windmill` → 2 (yazar ikisini de istedi, belgelenir). Reddedilen bir aday hiçbir komşuya sınır veremez.
- **▲ betik geçişi (kapı v4 #1a: unvan sözlükten çıkınca `長老マルクス` 0 hit → "İhtiyar Marks"):** terimin uç karakteri ile komşusu **farklı betik sınıfındaysa** sınırdır. Sınıflar: Han (kanji/hanja) · Hiragana · Katakana · Hangul · diğer (Latin, rakam, öteki harfler tek sınıf). `長老マルクス` → `マルクス` eşleşir (Han|Katakana); `マルクス様`/`マルクスさん`/`マルクスたち` → eşleşir (Katakana|Han, Katakana|Hiragana); `長老Marcus`, `Marcus様`, `마르쿠스Marcus` → eşleşir (kimlik çıpası **gerekmez**). Sınıf içi komşu sınır **değil**: `マルクスタウン` (Katakana|Katakana) 0, `村人`/`剣士`/`中村` (Han|Han) 0, `검사`/`방앗간집` (Hangul|Hangul) 0, `Marcus2`/`Marcuss`/`windmills` (diğer|diğer) 0. Ek listeleri (parçacık/saygı/KR ek) sınıf içi komşular için kalır (`장로님`, `村は`).
- yer tutucu (korunan aralık) ucu (K3).
Bilinen sınır: `검은` (`검`+ek `은`) kuraldan geçer → tek kodpointlik terimler şemada reddedilir (K6). Latin kaynakta büyük/küçük duyarsız: `re.IGNORECASE` **orijinal** metinde (casefold indeks kaydırır). **▲ Trie anahtarı IGNORECASE ile birebir denk olmalı:** `ß/ẞ` ve çok-kodpointli casefold sınıfı için `{Maßen, Maẞer, Maße}` sözlüğünde metinde harfiyen geçen `Maẞer` **her JSON sırasında** eşleşir (Tester-A O-A1: tur 1'de sıraya bağlıydı). Aynı terim n geçiş → n hit, `start` artan, **kodpoint** indeksi; `segment_index=None` (sözleşme).
**ÖLÇÜ (hepsi test, her ek ayrı kimlik):** `村人`/`剣士`/`검사`/`방앗간집`/`真剣に`/`中村`/`windmills`/`millstones` → **eşleşmez**; `村は`/`剣を`/`검을`/`방앗간에서`/`Marcusが`/`장로 마르쿠스`/`長老マルクス` (iki hit)/`長老マルクスアイラ` (üç hit)/`windmill` (iki hit) → eşleşir. **▲** JP: `マルクスさん`, `マルクス様`, `マルクスたち`, `マルクスって`, `マルクスか` ve listedeki **her** ek birer test → eşleşir; **negatif kontrol:** `さん` ile başlayan kelime yoksa ek listesi bileşik üretmez — `マルクスさんが` (ek+parçacık zinciri) eşleşir, `マルクス山` (dağ) eşleşmez. KR: `마르쿠스에게/한테/님/들/씨` ve listedeki **her** ek → eşleşir; `에게` zincirle değil listeden gelir (`에`+`게` zinciri kurtarmaz — Tester-B); negatif: `장로님이` eşleşir (ek zinciri 2), `마르쿠스들이다` (3 ek) eşleşmez. `MARCUS`/`marcus` eşleşir, indeksler orijinal metne göre (`İstanbul` casefold tuzağı). `Maẞer` iki sıralı sözlükte de eşleşir. **▲** Betik geçişi: yukarıdaki 6 pozitif + 8 negatif birer test. Boş sözlük/metin → `[]`.

## K2 · Gömme: aralık dışı karakter dokunulmaz, hits geçersizse `ContractViolation` (▲ NFC notu)
**DEĞİŞMEZ:** `terimleri_gom`, her segment için o segmentin hit'lerini (`segment_index` eşleşen) `start` **azalan** sırayla uygular (indeksler kaymasın). Çıktı `Segment`: `text` gömülü, `bbox/speaker/source_blocks` **aynen**. **▲** Hit'i olan segmentte `text` **ve `placeholders`** birlikte NFC'lenir (Tester-A O-A4 + Tester-B O-B2: metin NFC, yer tutucu NFD kalınca T-007 K5 sayımı yer tutucuyu göremiyor ve kopya ekliyordu); "aralık dışı dokunulmaz" **kodpoint-düzeyi NFC dışında** geçerlidir ve docstring bunu açıkça yazar. Hit'i olmayan segment ve boş `hits` → **aynı** nesne (`is`), normalize edilmez. Hit aralığı segment metniyle **tutarsızsa** (`text[start:end] != source_term`, aralık dışı, örtüşen iki hit) → `ContractViolation` (sessiz kayma yok). **▲** `Segment`'ten türeyen biçim hataları (`placeholders` düz `str`/`str` olmayan öge, `text` `str` değil, öge `Segment`/`TermHit` değil) `lookup_segments` ve `terimleri_gom`'da **`ContractViolation`**, `TypeError` değil (Tester-B O-B4: `TypeError` `TranslatorError` alt sınıfı değil, tasarım 5.6 `except TranslatorError` yakalayamaz; T-007 aynı bozuk Segment'i kabul ediyor). Doğrudan `lookup(text, placeholders)` çağrısında `TypeError` kalabilir.
**ÖLÇÜ:** `"방앗간을 지나"` + hit → `"Değirmen을 지나"`. İki hit başta+sonda → ikisi doğru yerde. Tutarsız/örtüşen → `ContractViolation`. `placeholders=("{0}",)` taşınıyor; **▲** NFD segment + NFD yer tutucu + hit → çıktıda `text` ve `placeholders` NFC ve her yer tutucu `text`'in alt dizesi (T-007 `modele_gider` sayımı 1); hit'siz NFD segment aynen (`is`). `speaker` dokunulmamış. **▲** `Segment(placeholders="{0}")` → `lookup_segments` ve `terimleri_gom` `ContractViolation`.

## K3 · Terim yer tutucu ile çakışmaz (Y2)
**DEĞİŞMEZ:** `lookup(text, placeholders)` — `placeholders` içindeki her dizenin **tüm** geçişleri korunan aralıktır; onlarla örtüşen aday eşleşmez. `terimleri_gom` de `segment.placeholders`'ı **aynı** kurala göre denetler (hit yer tutucuyla örtüşüyorsa `ContractViolation`).
**ÖLÇÜ:** `"{PLAYER}は村にいます"` + `PLAYER→Oyuncu` + `placeholders=("{PLAYER}",)` → hit **yok**; `placeholders=()` → hit **var** (pozitif kontrol). `{0}マルクス` bitişik → `マルクス` eşleşir, `{0}` dokunulmaz. `real_check` #3 segmentlere `placeholders` verir.

## K4 · Hedef her zaman ilk harfi büyük gömülür; sözlük **adlar ve modelin bilmediği bileşikler** için (G7, Y3, ▲ Y-B1)
**DEĞİŞMEZ:** Gömülen `target_term`'ün ilk harfi **büyük** yapılır (Türkçe `i→İ`). **Yazarlık kuralı (docstring + şema açıklaması), ▲ tur 2 netleşti:** sözlüğe **özel adlar** (karakter, yer) ve modelin **yanlış ya da tutarsız** çevirdiği bileşikler girer. **Unvan ve cins isimler tehlikelidir:** Tester-B gerçek motorla ölçtü — `장로→İhtiyar` unvanı bileşik içinde doğru çeviriyi bozuyor (`마을 장로가 마르쿠스를 불렀습니다.` ham "Köy ihtiyarı Marcus'u çağırdı" → gömülü "İhtiyar kasabası Marcus'a seslendi"; `The village elder came.` → "İhtiyar köyü geldi"), ama tek başına unvan+ad segmentinde (`장로 Marcus`) unvan sözlükte **yoksa** İngilizce'ye kayıyor ("Elder Marcus"). İki yönlü ölçülmüş bir **gri bölge**: kod karar veremez; docstring ve şema açıklaması yazarı uyarır, `not` alanı niyeti kaydeder; **hedef tarafı düzeltme** (çeviri sonrası "Elder"→"İhtiyar" eşlemesi) ayrı görev adayı (karara yazılır). **▲ Kimlik girdisi** (`Marcus→Marcus`) geçerlidir, hit üretir, metni değiştirmez; işlevi **sınır çıpası**dır (`長老Marcus` → `長老` yalnız `Marcus` sözlükteyse eşleşir) — docstring bunu adlandırır; çağıran "gömülen terim" sayacını `source_term != target_term` ile süzer (demo düzeltildi).
**ÖLÇÜ:** `değirmen` → `Değirmen`; `ihtiyar` → `İhtiyar`; zaten büyük → aynen. `Marcus→Marcus` hit üretir ve `terimleri_gom` çıktısı metin-eşit. `real_check` fixture v3 yalnız adlar + bilinmeyen bileşikler (`장로/長老/elder/mill` **çıkarıldı**; unvan sınıfı kapıda **rapor**).

## K5 · Saf, deterministik, hızlı (▲ hit yoğunluğu)
**DEĞİŞMEZ:** `lookup` ve `terimleri_gom` I/O yapmaz (yükleme yalnız `GlossaryStore.__init__`), global durum yok. 1000 segment × 50 terim < 50 ms. **▲** Segment başına maliyet hit sayısında **doğrusal-log** (Tester-A D-A1: `_ortusur` kabul listesini doğrusal tarıyor → 4000 hit 121 ms, 8000 hit 472 ms; `bisect` ya da konum bitmap'i). **▲** Sözlük yüklemesi terim uzunluğuna bağlı **özyineleme yapmaz** (Tester-A O-A2: ≥996 kodpoint `RecursionError`) — ya trie gövdesi yinelemeli kurulur ya şema kaynak uzunluğunu sınırlar (K6).
**ÖLÇÜ:** AST (T-008 deseniyle); iki çağrı eşit; süre; **▲** 8000 hit'lik tek segment < 60 ms; 2000 kodpointlik kaynak terim ya yüklenir ya `ValueError` (asla `RecursionError`).

## K6 · Yükleme, şema ve hata (Y1, Y3, KRT-orta, ▲ tur 2)
**DEĞİŞMEZ:** JSON `{"terimler": [{"kaynak": str, "hedef": str, "not": str?, "kisa_terim_izni": bool?}]}`. Şema reddi (`ValueError`, mesajda terim): kaynak/hedef boş · tekrar eden kaynak · **kaynak tek kodpoint** (`kisa_terim_izni: true` ile opt-in) · **hedefte cümle sonu işareti** (`.!?。！？`) · hedefte `{`/`}` · **▲ kaynakta cümle sonu işareti** (Tester-B O-B1: `マルクス。→Marcus` şemadan geçti, gömme cümle sınırını yuttu, gerçek motorda ikinci cümle kayboldu; OCR'dan kopyalanan terime nokta yapışması kolay) · **▲ hedefte kontrol karakteri** (`\n \t \r`, kategori `Cc` — Tester-A D-A4: `\n` T-007 bölmesine gider) · **▲ kaynak > 100 kodpoint** (RecursionError yerine şema). Kaynak ve metin **NFC**; dosya **bayt** ile; `FileNotFoundError` sarılmaz. **▲ Docstring'e:** gömülü segment **tekrar sözlükten geçirilmez** (Tester-B O-B3: `hedef ⊇ kaynak` girdisinde idempotens yok — `mill→Değirmen mill` iki geçişte büyür; pipeline/TM ham metni saklar, gömülüyü değil). D-A2 (casefold `ß→ss` tekrar reddi eşlemeden geniş) belgelenir, `[ÖLÇÜLMÜYOR]` ürün dillerinde.
**ÖLÇÜ:** Her red sınıfı birer test (`검`, `村`, `St. Marcus`, `{0}`, **▲** `マルクス。`, `Marcus.`, hedefte `\n`, 101 kodpoint kaynak); `kisa_terim_izni` ile `검` kabul; 100 kodpoint kaynak kabul; NFD girdi NFC sözlükle eşleşir; `tmp_path/"çeviri"` altında JSON.

## K7 · `segment_index` denetimi
**DEĞİŞMEZ:** `terimleri_gom`'a gelen hit'in `segment_index`'i `None` ya da aralık dışı → `ContractViolation` (sessiz yutma yok — KRT).
**ÖLÇÜ:** `None`, `-1`, `len(segments)` → üçü de `ContractViolation`.

---

# Kabul kapısı — `real_check.py` v4 (şefe ait; koş, yazma)
Gerçek NMT, `fixtures/sozluk_ornek.json` **v3** (7 terim: `マルクス/마르쿠스/Marcus→Marcus`, `アイラ/아일라→Ayla`, `水車小屋/방앗간→Değirmen`; unvan ve `mill` çıkarıldı — Y-B1/K-B1):
1. G1'in 6 cümlesi: gömülü çıktıda hedef **6/6**; **kazanç** (hamda yok, gömülüde var) cümle cümle raporlanır, ≥ 2 (pozitif kontrol; `İ` tuzağı için `casefold` + `İ→i`).
2. KR `방앗간을 지나…` gömülü → "Değirmen" var, tekrar yok; **pozitif kontrol:** hamda tekrar **var** (K-B2).
3. Yer tutucu: `{PLAYER}` korunan aralık (geçici sözlük, pozitif kontrol); `{0}マルクス` → `Marcus` ve `{0}` çıktıda.
4. **Unvan raporu (gri bölge, düşürmez):** `장로 마르쿠스` adlar-yalnız sözlükle → "Elder" var mı (K-B3 pozitif kontrol: Tester-B "Elder Marcus"); `마을 장로가 마르쿠스를 불렀습니다.` → **negatif ölçü (düşürür):** çıktıda "Marcus" var, "kasaba" yok, "ihtiyar" var (ham doğru → gömülü doğru kalmalı; Y-B1 sınıfı).
5. **▲ Y-B2:** `マルクスさんが来た。` ve `마르쿠스에게 말했습니다.` gömülü → "Marcus" var; pozitif kontrol: hamda "Marcus" yok (Tester-B: "Bay Marks", "Markos'a").
6. **▲ Zincir + betik geçişi (statik):** geçici `{wind→Rüzgar, mill→Değirmen}` + `The windmills turn.` → **0 hit**; `windmill` → 2; fixture `マルクスアイラ` → 2; `長老マルクス` → 1 (`マルクス`); `マルクスタウン` → 0.
7. Y1 negatif: `검` şema reddi (mesajda terim); izinle `검사가` boş, `검은 옷` dolu (rapor).
8. 1000 segment × fixture: lookup+gom medyan < 50 ms (yük altında 35 ms ölçüldü; eşik kalır, K-B5 bilgi).

# Teslim
`delivery.md`; K1/K2/K3/K6 docstring + `known_gaps`. **Ölçümün paketle çelişirse ölçümüne uy, yaz.** Metin basma; model/sağlayıcı/araç adı yazma.
