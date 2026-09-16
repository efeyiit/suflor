---
task: T-015
role: sef
round: 1
decision: kabul
---

# T-015 — Hedef tarafı düzeltme (`HedefDuzeltici`): KABUL

T-011'in açık kalemi: sözlük kaynak tarafında çalışır; unvanlar gri bölgedir (gömmek bileşiği bozar, gömmemek yalnız-unvan+ad segmentinde İngilizce sızdırır — Tester-B O-B10: 1/10 "Elder Marcus"; ad varyantları "Marks/Eira"). Çözüm çıktı tarafında: kelime sınırlı, büyük/küçük duyarsız (Türkçe I/İ ayrı) tek geçişli ikame tablosu; kesme öncesi Türkçe ek korunur (`Marks'ın` → `Marcus'ın`). Kurallar sözlük JSON'unun isteğe bağlı `hedef_duzeltmeler` listesinden; anahtar yoksa kimlik.

`src/translate/hedef_duzeltici.py` (K1–K5), 27 test; `cevir_yap`/`AnlikAkisi(duzeltici=)`, `demo/kabuk.py`, `demo/canli_cevir.py` bağlandı; `demo/sozluk_ornek.json` 6 kural (Elder→İhtiyar, Marks/Markos/Markus→Marcus, Eira/Aira→Ayla).

**Gerçek NMT kapısı (5/5):** 10 unvan+ad segmentinde sızıntı 1/10 → **0/10**; düzeltme dışında kelime farkı 0; bileşik cümlede kimlik; 1000 çeviri 1.9 ms.

Sınır: tablo yalnız bilinen sızıntıları düzeltir ("Şerif Ayla" gibi yanlış Türkçe unvan yakalanmaz — `[ÖLÇÜLMÜYOR]`); kullanıcı kuralları sözlük dosyasına elle yazar (ayarlar UI'si sonraki görev).
