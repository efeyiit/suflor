---
task: T-011
role: sef
round: 2
decision: kabul
---

# T-011 — GlossaryStore + terimleri_gom (Katman 0): KABUL

İki tur. Görev kapandı. **Projede ilk "kalite düzeltme" katmanı:** kullanıcının oyun sözlüğü, model yanlış çevirmeden önce kaynağa gömülüyor.

## Ne teslim edildi

`src/translate/sozluk.py` (975 satır) — `GlossaryStore(json_path)`: `lookup(text, placeholders=())`, `lookup_segments(segments)`, `terimler`, `len`; `terimleri_gom(segments, hits) -> tuple[Segment, ...]`; `ilk_harfi_buyut`. Trie yapılı tek geçiş eşleme (`re.IGNORECASE` orijinal NFC metinde, kanonik anahtar tüm-Unicode denk); **sınır kuralı her betikte aynı**: metin ucu · boşluk · `P*` · JP parçacık+saygı ekleri · KR 37 ek (sağda, zincir ≤2) · **betik geçişi** (Han/Hiragana/Katakana/Hangul/diğer) · yer tutucu ucu · **bitişik terim zinciri** (iki dış uç gerçek sınırsa hepsi, değilse hiçbiri); en uzun önce, örtüşmesiz; gömme start-azalan, `placeholders` ile birlikte NFC, hit'siz segment `is`; 30+ şema reddi (`ValueError`, mesajda terim), Segment kaynaklı biçim hataları `ContractViolation`. **453 test**, kapsam %100 (433 ifade), mypy --strict modül + test, cp1254. Kör tester A (garanti alanı+sınır) **416** + B (kötü kullanım+şartname) **302 koşum**.

**Gerçek NMT (`real_check` v4b, 19/19):** G1'in 6 cümlesi gömülü 6/6, **kazanç 4/6** (hamda yok → gömülüde var) · KR "Doğu'ya doğru Doğu'ya doğru" tekrarı gömmeyle kayboluyor (hamda var: pozitif kontrol) · yer tutucu korunuyor · **JP `マルクスさん` / KR `마르쿠스에게` ad korunuyor** (hamda "Bay Marks", "Markos'a") · zincir: `windmills` 0 hit → ham çeviri korunur (tur 1: `Rüzgarmills`) · `長老マルクス` unvan sözlükte olmadan da eşleşir (betik geçişi) · tek kodpoint şema reddi · 1000 segment 16–32 ms. Demo `canli_cevir.py` uçtan uca: KR/JP ekran görüntüleri (`sozluk_uctan_uca_{KR,JP}.png`).

**Yazarlık kuralı (ölçülmüş):** sözlük **özel adlar ve modelin bilmediği bileşikler** içindir. Modelin bildiği kelimeyi gömmek zarar verir (`검을 건넸습니다` → "Kılıç'i inşa ediyoruz"). **Unvanlar gri bölge, iki yönlü ölçüldü** (Tester-B, 20 segment): unvan sözlükte → bileşikte 3/8 bozulma ("İhtiyar kasabası"); sözlükte değil → yalnız-unvan+ad segmentinde 1/10 İngilizce sızma ("Elder Marcus") + 1/10 yanlış Türkçe unvan ("Şerif Ayla"); ad kazancı 11/20. Çözüm kaynak tarafında değil → **hedef tarafı düzeltme** görevi.

## Tur kaydı

| Tur | Ne oldu |
|---|---|
| ölçüm | G1–G7: gömme 21/21 korunuyor, İngilizce'ye kayma 0, alt dize eşleme bileşikte anlam bozuyor (`검사`→"Kılıç"), küçük harf JP'de kayboluyor |
| paket | v1 → **tek** KRT: 3 yüksek (Y1 bileşik, Y2 yer tutucu, Y3 bilinen kelime gömme zarar) → v2 |
| 1 | Implementer: 256 test, %100, mutant 32/32; kapıda 2 şef hatası ölçtü (`chr(44608)`, placeholders). **A onay · B onay** — ama aynı sınıf bağımsız: reddedilen komşu aday sınır veriyor (`millstones`→`Değirmenstones`); B: JP saygı ekleri / KR `에게` hiç eşleşmiyor ("Bay Marks"); B: unvan gömme bileşikte bozuyor. Hepsi paket hatası → v3 |
| 2 | Zincir kuralı + betik geçişi + ek listeleri + ß trie + K2/K6 şema: 453 test, mutant 47/47, kapı v4 16/16. **A onay · B onay** (0 yüksek; orta: liste hâlâ hiragana/kanji saygı eklerini ve KR `에게서/예요` + 3-ek yığınlarını kapsamıyor — bakım kalemi) |

## Kalite kanıtı

**İmplementer'a giden kod hatası: sıfır** (her iki turda da tester bulgularının tamamı paket/ölçü kaynaklı). Implementer iki turda dört ölçülü itiraz getirdi (kapı #6a/#3c/#3a; `検은 옷` sınıfı; `マルクス山` betik geçişiyle 1; `마르쿠스들이다` 2 ek) — dördü de haklı. Tester'lar iki turda toplam 25 bulgu; hepsi ölçülü, hepsi şef tarafından yeniden üretildi.

Şefin ölçülmüş hataları (12):

| # | Hata | Yakalayan |
|---|---|---|
| 1 | K1 "komşu terimin başlangıcı sınırdır" — aday yeter dedi → kısmi gömme | Tester-A, Tester-B (bağımsız) |
| 2 | K1 JP/KR ek listeleri oyun metninin en yaygın sınıfını kapsamıyordu (saygı ekleri, yönelme) | Tester-B |
| 3 | K1 v3 listesi hâlâ hiragana `くん/さま`, kanji `先生/先輩` ve KR `에게서/예요`yu kapsamıyor | Tester-A, Tester-B |
| 4 | K6 terminatör yasağı yalnız hedefte | Tester-B |
| 5 | K4 "yalnız yanlış çevrilen terimler" — fixture'ın 7/11'i hamda doğruydu; unvan iki yönlü ölçülmemişti | Tester-B |
| 6 | Kimlik çıpası (`Marcus→Marcus`) gerçek ihtiyacı (betik geçişi) örtüyordu; unvan çıkınca `長老マルクス` 0 hit | şef (kapı v4 #1a) |
| 7 | real_check #1 katkı ölçmüyordu, #3/#4 pozitif kontrolsüz (kural 10), `lower()` Türkçe `İ` tuzağı | Tester-B |
| 8 | real_check #6a yanlış kodpoint, #3c placeholders verilmiyor, #3a pozitif kontrolsüz | Implementer |
| 9 | K1 ÖLÇÜ `マルクス山→0` paketin kendi betik geçişi kuralıyla çelişiyordu; `마르쿠스들이다` 3 ek değil 2 | Implementer, Tester-B |
| 10 | real_check #4b "ihtiyar" mutlak şartı model sürümüne bağlı (kırılgan); #5c `or` gevşek; zincir sınıfı gerçek modelle ölçülmüyordu | Tester-B |
| 11 | K2 "aralık dışı dokunulmaz" ile K6 NFC çelişkisi (placeholders NFD kalıyordu) | Tester-A, Tester-B |
| 12 | Demo entegrasyonu `TranslatorError` yakalamıyor, kimlik hit'i "gömülen" sayıyordu | Tester-B |

## Açık kalemler

| Kalem | Not | Sahip |
|---|---|---|
| **Hedef tarafı düzeltme** (çeviri sonrası "Elder"→"İhtiyar" + **unvan kelimesi değişti** uyarısı) | Tester-B ölçtü: 20 segmentte 2 bozulma sınıfı; tablo tek başına yetmez, ham↔gömülü unvan farkı izlenmeli | yeni görev (T-013 adayı) |
| **Bakım kalemi (sozluk.py):** JP listesine `先生 先輩 氏 公 くん さま せんぱい せんせい`; KR listesine `에게서 한테서 예요 이에요 요 는데`; zincir derinliği 3 (`님께서는`, doğal metinde 1/10) | Tester-A O-A5, Tester-B O-B8/O-B9; aynı mekanizma, her ek negatif kontrolle | sozluk.py'ye dokunan ilk görev |
| UI sözlük editörü: terim eklerken **ham çeviri önizlemesi** (Y3/Y-B1 kod ile denetlenemez) | tasarım yükümlülüğü | T-012+ |
| TextNormalizer (T-004) çıktısına NFC garantisi | O-B7: hit indeksleri NFC metne göre | T-004 sahibi |
| Sembol `S*` sınır değil (`Marcus♪` 0; `マルクス♪` betik geçişiyle 1 — asimetri) · `Cf` karakterleri · `_` sınır · hedefte U+2028/Cf kabul · kaynakta `\n` kabul | `[ÖLÇÜLMÜYOR]`, belgeli | kayıt |
| Kabul aralığı bitmap'i yalnız süre testiyle ölçülüyor (mutant M45) | kabul: davranış eşdeğer, K5 süre ölçüsü | kayıt |
| `real_check` #4a yalnız KR; JP satırı eklenebilir | Tester-B K-B11 | kapı |

## Karar

**T-011 KABUL.** İki tester onayı (tur 2), altı kabul komutu exit 0, gerçek NMT 19/19, tam takım **1897** test yeşil, KR/JP demo uçtan uca. Paket sürümü 3, kapı sürümü 4b.
