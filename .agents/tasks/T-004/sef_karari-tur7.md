# Şef Kararı — T-004, Tur 7 (kapanış turu: iki kalem)

Tur 6'da **üç tester de onay verdi** (A: 13 kontrol, B: 12, C: 15 — üçü de `validate.py`'den geçti, şef hepsini kendi eliyle yeniden üretti). K28 kodda, R5-1 kapandı, ölçü kiti ayrışması `3677/6119/7249 → 0/0/0`, `pytest tests` 821 passed, kör tester takımı **623 passed, 1 xfailed, 0 kırık**.

Görev §4.5 gereği **kabul edilebilir durumda**. Bu tur, üç tester'ın bulduğu ve şefin doğruladığı **iki somut boşluğu** kapatıyor — yeni değişmez yok, davranış değişikliği yok.

---

## Neden karar kırmızı takımına gitmiyor (§4.5 tarzı gerekçeli azaltma)

Karar kırmızı takımı, şefin **değişmez ve ölçü** kurgusundaki hataları yakalamak için var. Bu turda:
- **yeni değişmez yok** — K28 ve K29–K32 aynen duruyor,
- **yeni ölçü kurgusu yok** — eklenecek testin içeriğini Tester-B ölçüp verdi (aşağıda birebir yazılı),
- **davranış değişikliği yok** — biri docstring düzeltmesi, biri var olan doğru davranışı pinleyen tek test.

Kırmızı takımın bu turda yakalayacağı bir hata sınıfı açılmıyor. Aynı gerekçeyle **tek tester** koşacak (Tester-B, karar uyumu merceği): iki kalem de B'nin ve A'nın karar-uyumu bulgularından doğdu, dil/sınır ve garanti alanı yüzeyi açılmıyor.

---

## T7-1 · `### K24` docstring bölümü bayat — düzeltilecek

**Bulan:** Tester-A (N1) · **Şef doğrulaması:** `src/ocr/normalizer.py:807` bölümü, `K28`/`_raw_query_pair` geçen satır sayısı **0**.

`normalizer.py`'nin modül docstring'indeki `### K24` bölümü, K28 **öncesi** çağrı biçimini **şimdiki zamanda ve koşulsuz** anlatıyor:

> *"K21'in `ignore_length=True` IKINCI cagrisi ARTIK `_group_rejection_reason(current, nxt, ...)` DEGIL, `_group_rejection_reason(tail, nxt, ...)` KULLANIR — yani SOL TARAF DAIMA grubun okuma-sirasindaki EN SON (birlesime en son KATILAN) HAM ogesidir…"*

İki ayrı sorun:
1. **Çağrı biçimi yanlış.** Gerçek çağrı `_group_rejection_reason(*_raw_query_pair(tail, nxt, blocks), params, ignore_length=True)`.
2. **"`tail` … HAM öğesidir" cümlesi R5-1'in çürüttüğü cümledir.** Kuyruk, adım 3'te hyphen'le birleşmiş **çok bloklu** bir öğe olabilir; bbox'ı o zaman birleşik kutudur, ham bir bloğun kutusu değil. K28 tam olarak bu yüzden yazıldı.

**Neden bloke değil ama düzeltilmeli:** davranış doğru ve `## K28` bölümü (satır 92–120) eksiksiz. Ama `### K24`'ü okuyan bir sonraki ajan **yanlış** bilgilenir ve iki bölüm birbiriyle çelişir. K29'un bir üst katmanı: K29 var olmayan teste atfı yasaklıyor, bu ise **var olmayan mekanizmayı** anlatıyor.

**Yapılacak:** `### K24` bölümü, K28 tarafından **devralındığını** söyleyecek biçimde düzeltilir. Bölüm silinmez (tarihçe değerli); başına K28'e devrettiğini belirten bir cümle ve çürütülen cümlenin **neden** çürüdüğü yazılır. `## K28` bölümüne de `### K24`'ün buraya devrettiği bir çapa satırı eklenir.

**ÖLÇÜ:** Tester-A'nın `strict=True` xfail'i (`tester_A/test_r6_garanti_alani.py:771`) düzeltme sonrası **XPASS ile kırılır** — A onu yeşile çevirir. Ayrıca `purity_check.py` exit 0 kalmalı (K29 atıfları bozulmasın).

---

## T7-2 · M15 sınıfının `tests/` altında kapısı yok — bir test eklenecek

**Bulan:** Tester-B (N3) · **Şef doğrulaması:** M15, dört kabul komutunu, 124 ürün testini **ve** ölçü kitinin beş kanalını temiz geçiyor; B'nin kendi diferansiyelinde 1844 ayrışma veriyor.

**M15 nedir:** miras-uygunluk sorgusunu **yanlış `params`** ile soran uygulama — ör. `get_params(OcrPreset.DIALOGUE)` yerine çağrının aldığı `params`'tan başkasını geçiren. Kit `params` kimliğini **kaydetmiyor**, bu yüzden dört kanalın hiçbiri görmüyor.

**DEĞİŞMEZ:** Miras-uygunluk sorgusu, `_group`'a verilen **aynı** `params` nesnesiyle sorulur; ön ayar eşiği sorgu içinde değiştirilemez.

**ÖLÇÜ (Tester-B'nin ölçüp verdiği test — birebir):** `tests/unit/ocr/test_normalizer.py::test_k28_miras_sorgusu_ayni_params_ile_sorulur` — `dialogue` ön ayarı, `h=18`, sınırda `gap=12`. Bu geometri `dialogue` eşiğinde (`0.8 × 18 = 14.4`) mirası **uygular**, `tooltip` eşiğinde (`0.3 × 18 = 5.4`) **uygulamaz**; yanlış `params` geçiren uygulama bu tek testte düşer. Test hem `normalize` çıktısındaki `speaker`'ı hem — `olcu_kiti.sorgu_kaydi()` ile — sorgunun gerçekten tek bir `params` gördüğünü assert eder.

---

## Kapsam — bu turda YAPILMAYACAKLAR (bilinçli, kayda geçer)

| Kalem | Neden bu turda değil |
|---|---|
| `olcu5_fixture`'a çok bloklu aday (B/N1) | Kitin fixture'ını değiştirmek ölçü kurgusuna dokunur; kırmızı takım gerektirir. Ayrı tur. |
| M12 sınıfının yalnız `test_k5_*`'ye yaslanması (B/N4) | Aynı sınıf; kitin `adim1_4` bağımsızlığı sorunu (karar sürüm 8 "bilinen sınırlar"da yazılı). |
| `Mn`/`Mc` ad süzgeci genişletmesi (C/1) | **K9'un sözlüksel kuralını değiştirir** — davranış değişikliği, ayrı tur. Bu turda yalnız `known_gaps` cümlesi düzeltildi (karar sürüm 8'de yapıldı). |
| ZWJ/emoji grapheme şişmesi (C/4) | Aynı sınıf: `max_group_chars`'ın codepoint sayması K11'in kuralı. Ayrı tur. |
| Miras `monitor_index`/`dpi_scale` sınırını aşıyor (C/2) | Yeni değişmez gerektirir. Ayrı tur. |
| `NaN` `dpi_scale` tanı mesajı (C/3) | Kozmetik; K7'nin `confidence` ön denetiminin `dpi_scale` karşılığı yok. Ayrı tur. |

Altısı da `known_gaps`'e yazılır ve **T-004 kapanışında açık kalem olarak** kayda geçer.

---

## Kabul komutları

Tur 6 ile aynı dördü, hepsi exit 0 olmalı:

```
python -m mypy --strict src/ocr/normalizer.py src/ocr/presets.py
python -m pytest tests/unit/ocr/test_normalizer.py -q
python .agents/tasks/T-004/purity_check.py
python .agents/tasks/T-004/olcu_kiti.py
```

Artı regresyon: `python -m pytest tests -q` → **822 passed** (821 + T7-2'nin tek testi), düşen yok.
