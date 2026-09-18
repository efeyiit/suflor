# T-019 karar — ürün Bölge İzleme modu

**KABUL — 18 Eylül 2026.** `src/ui/bolge_pencere.py` seçili ekran alanını 10 Hz yakalar,
`ChangeDetector` ile kararlı değişimleri süzer ve mevcut `AnlikAkisi` üzerinden OCR ile Türkçe çeviriyi
arka planda çalıştırır. İş sürerken yalnız en son değişen kare bekletilir.

Ana ürün kabuğundaki Bölge İzleme düğmesi bu pencereye bağlandı. Şeritte duraklat/devam et,
kaynak metni göster/gizle, alanı değiştir ve kapat kontrolleri bulunur. Snapshot ve Bölge İzleme,
aynı OCR motorunun iki thread'den kullanılmasını önlemek için aynı anda açılmaz.

Doğrulama:

- Yeni Bölge İzleme UI testleri: 4 geçti.
- T-018 + pipeline + yeni UI hedef takımı: 48 geçti.
- Tam takım: 2432 geçti (43,61 s).
- `mypy --strict --explicit-package-bases src/ui/bolge_pencere.py`: temiz.
- Ürün kabuğu ve yeni pencere başsız ortamda içe aktarma kontrolü: temiz.

Sınırlar: Gerçek oyun üstünde gecikme ve yerleşim henüz Blue Prince ile ölçülmedi. Şerit bölgeye otomatik
kenetlenmiyor; standart üstte kalan pencere olarak kullanıcı tarafından taşınabiliyor. Bu iki madde bir
sonraki gerçek oyun doğrulamasında ölçülecek.

