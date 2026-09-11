---
task: T-008
role: sef
round: 2
decision: kabul
---

# T-008 — SatırBirleştirici: KABUL

İki tur. Görev kapandı.

## Ne teslim edildi

`src/ocr/satir_birlestirici.py` — `satirlari_birlestir(blocks) -> list[TextBlock]`, saf fonksiyon, `normalize`'dan önce. `(y,x,idx)` sırala → satır bölümleme (referans: satırın **en kısa** bloğu) → satır içi `(x,y,idx)` → tek geçiş; eşikler `0.5×min(h)` dikey / `0.75×min(h_orijinal)` yatay; birleştirme karakteri betikle (CJK boşsuz, diğerleri boşluk); `confidence=min`, `line_boxes` parçalar. **76 test**, %100. Kör tester A+B — 158 test.

**Neden var:** `demo/canli_cevir.py` Korece ile koşulunca bulundu — KR tespit kelime kutusu veriyor, normalizer yatayda birleştirmiyor, çeviri kelime kelime gidiyordu. Ne T-004 ne T-006 kapısı görebilirdi.

**Gerçek OCR (`real_check` 15/15):** KR 17 → 4 `[2,5,5,5]` · JP/EN no-op · normalize 16 → 2 segment · NMT'de tek kelimelik çeviri 0 · menü 13–16×h ayrı · **1-em menü 0.78–1.06×h ayrı** (0.75 eşiği; 1.0/10.0 mutantları düşer) · **etiket köprüsü 11 → 2 `[6,5]`** (tur 1: 1 blok) · saflık AST · 1000 blok ~2 ms. T-009 ile birlikte Korece uçtan uca 3 cümle.

## Tur kaydı

| Tur | Ne oldu |
|---|---|
| ölçüm | S1–S9: geometri (örtüşme 1.0, boşluk ≤0.57h, satır geçişi negatif), betik, idempotens |
| paket | v1 → **tek** KRT: 3 yüksek (Y1: KR tanıma noktayı düşürüyor → **T-009**; Y2: idempotens birleşik h ile tutmaz; Y3: 1.0 eşiği 1-em sınıfının içinde) → v2 |
| 1 | Implementer: 68 test; iki ölçülü itiraz (tek-geçiş lafzı y titreşiminde 17→9; şefin menü fixture'ı 10.0'ı ayıramıyor) — ikisi de haklı. **A ret · B ret** — aynı sınıf bağımsız: 2× etiket iki satırı fermuarlıyor (gerçek OCR 11→1) |
| 2 | Referans = en kısa blok (A'nın E prototipi); aynı-x çifti; köprü fixture'ı kapıya. **A onay · B onay** |

## Kalite kanıtı

**İmplementer'a giden kod hatası: bir** (satır referansı ilk blok — paketin K2 adım 3 lafzı buydu; paket hatası). Implementer iki, tester'lar üç ölçülü düzeltme getirdi; hepsi haklı.

Şefin ölçülmüş hataları:

| # | Hata | Yakalayan |
|---|---|---|
| 1 | `real_check #3` "doğu" beklentisi ölçülmeden yazıldı; doğru uygulama da geçemezdi (KR tanıma noktasız) | KRT-1 |
| 2 | Eşik 1.0 gerçek 1-em boşluk sınıfının içindeydi | KRT-1 |
| 3 | İdempotens "değişmez" diye yazıldı; birleşik h ile tutmaz | KRT-1 |
| 4 | S6 "yanlış birleştirme yapısal olarak imkânsız" — uzun kutu köprüsü | KRT-1 |
| 5 | K2 tek-geçiş metni gerçek veriyle koşulmadan yazıldı (17→9) | Implementer |
| 6 | Menü fixture'ı eşiğin ayrıştığı noktada değil çok uzağında (13–16×h); 10.0 mutantı kapıdan geçti | Implementer |
| 7 | KRT'nin adlandırdığı köprü sınıfı `[ÖLÇÜLMÜYOR] (fixture yok)` bırakıldı; fixture 10 dakikaydı | Tester-A, Tester-B |
| 8 | `real_check`'te idempotens kontrolü paket kaldırdıktan sonra kaldı | şef |

## Açık kalemler

| Kalem | Not | Sahip |
|---|---|---|
| **`ch` det + KR v5 rec satır kutusu veriyor** — KR'de birleştirmeye gerek kalmayabilir | T-009 tester ölçtü, tek fixture; menüyle ölçülmeli | yeni ölçüm |
| `-idx` (M04) davranış-eşdeğer **değil**: aynı `(y,x)` farklı `h` + komşu satır → üyelik girdi sırasına bağlı (B: 264/3000) | Gerçek OCR'da aynı-`(y,x)` çifti yok; docstring K6 cümlesi daraltılmalı — implementer §4.6/10 sınıfı | belge |
| Gri bölge `[0.6, 0.95]×h` (`"120 / 150"` 1.04 ayrılır) | `[ÖLÇÜLMÜYOR]` | kayıt |
| Sarkan 8 px minik token ayrı blok kalır (cümle bütün); minik işaretler (™ `*`) satırı parçalayabilir | K2 `0.75×min(h)` kuralı | kayıt |
| M23 uyumluluk ideografı, M37, M40 keskinlik | B'de hazır ölçü | Tester-B |
| A'nın 2 `_SINIF`, B'nin sayı pinleri yeniden nişanlandı | Tamam | — |

## Karar

**T-008 KABUL.** İki tester onayı (tur 2), beş kabul komutu exit 0, gerçek OCR 15/15, 1444 test yeşil, Korece demo uçtan uca.
