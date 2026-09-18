# T-020 paket — yerel çeviri hafızası

## Amaç

Aynı oyun metninin farklı zamanlarda farklı çevrilmesini önlemek ve benzer önceki çevirileri
sağlayıcılara bağlam örneği olarak vermek. Oyun başına zorunlu profil olmadan çalışmalıdır.

## Kabul ölçütleri

1. Veriler kullanıcı dizinindeki SQLite dosyasında, WAL modunda tutulur.
2. NFC, büyük/küçük harf ve boşluk farkları kesin eşleşmeyi bozmaz; dil çiftleri ayrıdır.
3. Kesin eşleşmede model çağrılmaz ve önceki Türkçe doğrudan kullanılır.
4. Yeni çeviri hedef düzeltmesinden sonra hafızaya eklenir.
5. Benzer kayıtlar trigram puanıyla sıralanır ve `TranslationRequest.tm_examples` alanına eklenir.
6. 50.000 kayıtta benzer arama medyanı 20 ms'yi aşmaz.
7. UI ve işçi thread'lerinden güvenli kullanım; idempotent kapanış.
8. Veritabanı açılamazsa uygulama çökmeden hafızasız devam eder.

