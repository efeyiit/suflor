# T-019 paket — ürün Bölge İzleme modu

## Amaç

Ana uygulamadaki Bölge İzleme düğmesini canlı görüntü gösteriminden gerçek, oyun içinde kullanılabilir
OCR ve Türkçe çeviri akışına geçirmek.

## Kabul ölçütleri

1. Kullanıcı dikdörtgen seçince ilk kare otomatik okunur ve çevrilir.
2. Alan yalnız kararlı bir değişimde yeniden işlenir; iş sürerken kuyruk büyümez, yalnız son kare tutulur.
3. OCR ve çeviri UI thread'ini bloklamaz; mevcut `AnlikAkisi` kullanılır.
4. Üstte kalan şerit çeviriyi gösterir; kaynak metin isteğe bağlıdır.
5. Duraklat, devam et, alanı değiştir ve kapat doğrudan erişilebilir; modal pencere yoktur.
6. Otomatik dil seçimi, sözlük ve hedef düzeltici Snapshot ile aynı biçimde çalışır.
7. Pencere kapanınca akış thread'i durur; Snapshot ve Bölge İzleme aynı OCR motorunu eşzamanlı kullanmaz.
8. Tam test takımı ve katı tip denetimi temizdir.

