# T-020 karar — yerel çeviri hafızası

**KABUL — 18 Eylül 2026.** `TranslationMemory`, `%APPDATA%/Suflor/db.sqlite` içinde WAL modunda
kesin ve benzer çeviri eşleşmeleri tutar. Metin anahtarı NFC + casefold + tek boşluktur; kaynak/hedef
dil çiftleri ayrıdır. Trigramlar ayrı indekslenir ve yazma sırasında tutulan gram sayacı, aramada en
seyrek iki gramla aday kümesini daraltır.

Snapshot ve Bölge İzleme ortak hafızayı kullanır. Kesin eşleşmeler modeli atlar; eksik segmentler
çevrilir, hedef düzeltmesinden sonra kaydedilir. Benzer kayıtlar `tm_examples` olarak aktarılır.
Veritabanı açılamazsa ürün hafızasız çalışmaya devam eder.

Doğrulama:

- Hafıza + pipeline hedef takımı: 38 geçti.
- Tam takım: 2441 geçti (43,59 s).
- `mypy --strict --explicit-package-bases` (hafıza, pipeline, Bölge UI): temiz.
- 50.000 sentetik kayıtta 10 benzer arama: min 13,48 ms; medyan 16,00 ms; maks 17,22 ms.
  İlk sonuç puanı 0,872; kayıt sayısı 50.000.

Sınırlar: Yerel NMT sağlayıcısı bugün `tm_examples` alanını kabul eder fakat model girdisinde kullanmaz;
kesin eşleşme kazancı aktiftir, benzer örneklerin kalite kazancı LLM/bulut sağlayıcılarıyla etkinleşir.
Kullanıcının hafızayı görüntüleme, düzeltme ve temizleme arayüzü sonraki görevdir.

