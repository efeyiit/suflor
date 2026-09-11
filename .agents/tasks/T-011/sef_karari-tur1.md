---
task: T-011
role: sef
round: 1
decision: tur-2
---

# T-011 tur 1 → tur 2 kararı

İki kör tester **onay** verdi (A: 0Y/4O/7D, 162 test · B: 2Y/7O/6D, 92 koşum). Kod K1–K7'ye uyuyor; **bulguların tamamı paketin kendisinde** (K1 sınır listeleri dar, komşu-terim kuralı yanlış, şema iki sınıfı kaçırıyor). Kural 9: paket hatası implementer'a bir düzeltme turu olarak gider; tester'lar tur 2'de kendi testleriyle yeniden doğrular.

## Şefin yeniden üretimleri (`sef_dogrulama/`)

| Bulgu | Kim | Şef üretti | Sonuç |
|---|---|---|---|
| Reddedilen komşu aday sınır veriyor → kısmi gömme (`windmills`→`Rüzgarmills`, `millstones`→`Değirmenstones`, `長老マルクス様`→yalnız unvan) | A O-A3 + B O-B5 **bağımsız** | `tur1_tester_bulgulari_statik.txt`, `real_check v4 #6a` (tur-1 kodunda windmills=1) | **Paket K1 hatası** → zincir kuralı |
| JP saygı ekleri (`さん 様 たち って か`) ve KR `에게 한테 님 들 씨` **0 hit**; modelde "Bay Marks", "Markos'a" | B Y-B2 | statik 0/0 (5+5); `real_check v4 #5a` tur-1 kodunda 0/0 | **Paket K1 eksiği** → listeler genişledi + **betik geçişi** kuralı |
| Unvan sözlükten çıkınca `長老マルクス` **0 hit** → "İhtiyar Marks" | şef (kapı v4 #1a 5/6) | `real_check-v4-tur1-kodu-uzerinde.txt` | Kimlik çıpası yetmiyor → **betik geçişi sınırdır** (Han\|Katakana, Katakana\|Hiragana, Latin\|CJK…) |
| Unvan terimi bileşikte doğru çeviriyi bozuyor (`마을 장로가…` ham "Köy ihtiyarı" → gömülü "İhtiyar kasabası", 3/8) ama unvan sözlükte yokken `장로 Marcus` → "Elder Marcus" | B Y-B1, K-B3; şef `y3_unvan_jangro.txt` (8 cümle: 3 düzelme / 1 bozulma) | evet | **Gri bölge, iki yönlü ölçüldü.** Fixture v3 unvanları çıkarır (adlar + bilinmeyen bileşikler); K4 yazarlık kuralı netleşti; kapı #4a rapor + #4b negatif ölçü; **hedef tarafı düzeltme** ("Elder"→"İhtiyar" çeviri sonrası eşleme) ayrı görev adayı |
| `ß/ẞ` casefold sınıfı trie'de ayrı dal → JSON sırasına bağlı | A O-A1 | `[]` vs `[Maẞer]` | K1 ▲ trie anahtarı IGNORECASE ile denk |
| ≥996 kodpoint kaynak → `RecursionError` | A O-A2 | 1000 → RecursionError | K6 ▲ kaynak ≤ 100 kodpoint (ya da yinelemeli trie) |
| NFD segment: metin NFC, `placeholders` NFD → T-007 sayımı göremez | A O-A4 + B O-B2 | kod okuma | K2 ▲ `placeholders` da NFC |
| Kaynakta `。` şemadan geçiyor → ikinci cümle kayboldu | B O-B1 | şema kabul etti, 1 hit | K6 ▲ kaynakta terminatör reddi |
| Hedefte `\n`, `%s`, `[Mill]` kabul | A D-A4 | — | K6 ▲ kontrol karakteri reddi; `%s`/`[...]` belge |
| `TypeError` `TranslatorError` değil | B O-B4 | — | K2 ▲ Segment kaynaklı biçim hataları `ContractViolation` |
| `hedef ⊇ kaynak` idempotens kırıyor | B O-B3 | şema kabul | Belge: gömülü segment tekrar sözlükten geçmez |
| Kimlik hit (`Marcus→Marcus`) demo'da "gömülen" sayılıyor; demo `TranslatorError` yakalamıyor (pencere donar) | B O-B6, K-B7 | — | **Demo düzeltildi** (şef): kimlik süzülür, `TranslatorError` yakalanır |
| Hit sayısında O(n²) | A D-A1 | — | K5 ▲ bisect/bitmap |
| Kapı: #1 6/6'nın 4'ü gömmeden; #3/#4 pozitif kontrolsüz; `lower()` `İ` tuzağı | B K-B1..K-B4 | evet (`İhtiyar`.lower() 8 kodpoint) | **real_check v4**: kazanç ölçüsü, tekrar/Elder pozitif kontrolleri, `_kat` katlama, #4b negatif, #5 Y-B2, #6 zincir+betik |

## Şefin ölçülmüş hataları (tur 1)

| # | Hata | Yakalayan |
|---|---|---|
| 1 | K1 "komşu terimin başlangıcı sınırdır" — aday yeter dedi, kabul şartı yok → kısmi gömme | Tester-A, Tester-B |
| 2 | K1 JP/KR ek listeleri oyun metninin en yaygın sınıfını kapsamıyor (saygı ekleri, yönelme) | Tester-B |
| 3 | K6 terminatör yasağı yalnız hedefte | Tester-B |
| 4 | K4 "yalnız yanlış çevrilen terimler" — fixture'ın 7/11'i hamda zaten doğruydu; unvan sınıfı iki yönlü ölçülmemişti | Tester-B |
| 5 | real_check #1 katkıyı ölçmüyordu (gömmeden gelen 4/6 "kazanç" sayılıyordu), #3/#4 pozitif kontrolsüz (kural 10), `lower()` Türkçe tuzağı | Tester-B |
| 6 | real_check #6a `chr(44608)` yanlış kodpoint; #3c placeholders verilmiyor; #3a pozitif kontrolsüz | Implementer |
| 7 | Kimlik çıpası fikri (`Marcus→Marcus`) gerçek ihtiyacı (betik geçişi) örtüyordu — unvan çıkınca `長老マルクス` düştü | şef (kapı v4) |
| 8 | Demo entegrasyonu `TranslatorError` yakalamıyordu; kimlik hit'i "gömülen terim" sayıyordu | Tester-B |

## Tur 2 kapsamı (implementer)

Paket **v3** (▲ maddeleri): K1 zincir kuralı + betik geçişi + ek listeleri + trie/casefold denkliği · K2 `placeholders` NFC + `ContractViolation` sınıfı · K5 bisect + özyineleme yok · K6 kaynak terminatör, hedef `Cc`, kaynak ≤ 100 · docstring notları (idempotens, kimlik çıpası, unvan gri bölgesi). Kapı `real_check.py` **v4** (16 kontrol; tur-1 kodunda 3 İHLAL: #1a 5/6, #5a 0/0, #6a windmills=1 — pozitif kontrol).

Tur 2 sonrası: Tester-A ve Tester-B kendi testlerini yeniden koşar + ▲ sınıflarını hedefler (`verdict-*-tur2.md`).

## Açık kalemler (karara taşınacak)

- **Hedef tarafı düzeltme tablosu** ("Elder"→"İhtiyar", "Marks"→"Marcus" çeviri sonrası) — sözlüğün kaynak tarafı çözemediği unvan sınıfı için; ayrı görev.
- UI sözlük editörü: terim eklerken **ham çeviri önizlemesi** (Y3/Y-B1 kod ile denetlenemez; önizleme ölçer) — T-012+ tasarım yükümlülüğü.
- TextNormalizer (T-004) çıktısına NFC garantisi (O-B7) — T-004 sahibine kayıt.
- D-A2 casefold `ß→ss` tekrar reddi eşlemeden geniş; D-A3 `Cf` karakterleri sınır değil; D-A5 `_` sınır — `[ÖLÇÜLMÜYOR]`, belge.
