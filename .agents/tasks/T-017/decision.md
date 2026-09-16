---
task: T-017
role: sef
round: 1
decision: kabul
---

# T-017 — Seçim = bütün metin · Enter'sız çeviri: KABUL

Kullanıcının ilk gerçek oyun testi geri bildirimi: *"bir metni bütünsel algılayamıyor satır satır algılıyor … bütünlüğü bozuluyor; bir de Enter yerine daha pratik bir şey lazım."*

**Ölçüm önce** (`olcum_secim.py`, gerçek RapidOCR, oyun benzeri panel, satır adımı 2.0/2.4/2.8 × punto): eski yol `normalize` (DIALOGUE eşiği: boşluk < 0.8 × min h) Korece'de adım 2.4'ten itibaren 4 satırı **4 parçaya**, Japonca'da (OCR satırı yan yana 2-3 parçaya bölüyor, satır birleştirici yakalamıyor) **6-7 parçaya** bölüyor — şikâyet yeniden üretildi. İlk `secimi_birlestir` sürümüm (eşik 1.6 × medyan h) Korece'yi tuttu ama Japonca adım ≥ 2.4'te bölündü (kana kutuları kısa: boşluk/h = 2.2) ve yan yana parçaları `(y, x)` sırasıyla dizmek metin sırasını bozabiliyordu → **satırlara kümeleme** (dikey örtüşme > 0.5 × min h → aynı satır, x sıralı) + eşik **2.5** × medyan satır yüksekliği. Sonuç: 6 konfigürasyonun 6'sında 1 segment; birleşik metin ~ beklenen gövde benzerliği KR 1.000, JP 0.98 (sıra doğru).

- `src/pipeline/secim.py` — `secimi_birlestir(bloklar) -> list[Segment]`: satırlara kümele → büyük dikey boşlukta grupla → grup = tek segment (`satir_birlestir`: CJK-CJK boşluksuz, Hangul boşluklu, `-`+küçük harf tire düşer) → kısa/noktalamasız/dar ilk satır ya da `Ad:` konuşmacı olarak ayrı. 10 test.
- `src/pipeline/anlik.py` — `cevir_yap` artık `normalize` yerine `secimi_birlestir`; **`cevir()` her çağrıda yeni `seq`** (seçim değişince eski çeviri geç gelse bile düşer). +2 test (çok satırlı seçim modele TEK segment gider; ikinci `cevir` ilkinin sonucunu düşürür).
- `src/ui/anlik_pencere.py` — Enter yerine: her seçim değişikliğinden **350 ms sonra kendiliğinden** `cevir_istendi` (art arda tıklar tek istek); **sağ tık** ve Enter beklemeden; seçim `sonuc`/`cevriliyor`'da da düzenlenebilir (sonuçlar silinir, yeniden çevrilir); seçim boşalırsa istek yok; `ceviriyi_goster` sayaç çalışıyorsa eski sonucu basmaz; kapanış sayacı durdurur. Pencere testleri 25 (8 yeni).

**Gerçek kapı** `real_check.py` (gerçek OCR + NLLB, gerçek ekranda tam ekran pencere, adım 2.4 fixture): KR ve JP **10/10 temiz** — sürükleme sonrası Enter'sız 374/367 ms'de çevriliyor; **1 sonuç**, kaynak tüm satırları içeriyor, çeviride satır kırığı yok (KR 2012 ms, JP 2708 ms); **mutant**: aynı seçimi eski yol 4 / 7 parçaya bölerdi; konuşmacı satırı eklenince eski sonuç silinip 2 sonuç (Marcus sözlükten); sağ tık 0.2 ms'de çeviriyor, sayaç iptal; Esc sonrası istek yok. Görüntü: `sef_dogrulama/anlik_butun_KR.png`, `anlik_butun_JP.png`.

Tam takım **2397** (×2), mypy --strict temiz. Sınır: birbirinden < 2.5 satır yüksekliği uzaktaki iki ayrı panel tek seçimde tek metin olur (kullanıcı seçimle ayırır); `normalize` bölge-izle (T-005/T-008) yolunda duruyor, Snapshot dışı davranış değişmedi.
