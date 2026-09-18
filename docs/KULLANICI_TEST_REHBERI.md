# Suflör kullanıcı test rehberi

Bu rehber, geliştirilen özellikleri oyun oynayan bir kullanıcı gibi sınamak içindir. Test sırasında
oyunu **pencereli** veya **kenarlıksız tam ekran** çalıştır. Windows'un exclusive fullscreen modunda
üstte kalan çeviri pencereleri görünmeyebilir.

## 1. Uygulamayı aç

1. `Suflor` klasöründeki `Suflor.bat` dosyasına çift tıkla.
2. Ana pencerenin açılmasını bekle.
3. İlk çalıştırmada OCR modellerinin indirilmesi ve çeviri modelinin yüklenmesi biraz sürebilir.
4. Durum satırında model hatası görünürse `models/nllb-200-distilled-600M-ct2-int8` klasörünün
   bulunduğunu kontrol et.

## 2. Otomatik dil seçimini test et

1. Dişli düğmesinden Ayarlar'ı aç.
2. Dil alanını **Otomatik (oyundan algıla)** olarak bırak ve kaydet.
3. Blue Prince veya İngilizce metin gösteren başka bir oyun aç.
4. `Ctrl+Alt+D` tuşlarına bas.
5. Ekrandaki İngilizce metni seç.

Beklenen sonuç:

- Dil rozeti **İngilizce** göstermeli.
- Seçilen metin Türkçeye çevrilmeli.
- Uygulama veya oyun donmamalı.
- Yeni bir oturumda İngilizce ilk denendiği için diğer dillere göre ek arama beklenmemeli.
- Dil kesin belirlenemezse rozetin yanında `?` görünmeli; uygulama kapanmamalı.

## 3. Anlık Çeviri modunu test et

1. Oyunda çevirmek istediğin ekranı aç.
2. `Ctrl+Alt+D` tuşlarına bas veya ana pencereden **Anlık çeviri** seçeneğine tıkla.
3. Ekran donunca bir metin bloğuna tıkla ya da birden çok satırın üzerinden sürükle.
4. Yaklaşık kısa bir beklemeden sonra çevirinin otomatik gelmesini bekle.
5. `Ctrl+C` ile sonucu kopyalamayı ve `Esc` ile pencereyi kapatmayı dene.

Beklenen sonuç:

- Donmuş oyun görüntüsünde Suflör ana penceresi, kenar sekmesi veya ayarlar penceresi görünmemeli.
- Birden çok satır tek bir bütün metin olarak çevrilmeli.
- Enter'a basmak zorunlu olmamalı.
- Kaynak metin ile çeviri anlam bakımından aynı olmalı; özel adlar gereksiz yere değişmemeli.

## 4. Bölge İzleme modunu test et

1. `Ctrl+Alt+R` tuşlarına bas veya ana pencereden **Bölge izle** seçeneğini aç.
2. Oyundaki diyalog veya altyazı alanının çevresine fareyle bir dikdörtgen çiz.
3. Metnin değişmesini bekle.

Beklenen sonuç:

- İlk görüntü ve sonraki kararlı metin değişiklikleri otomatik çevrilmeli.
- Türkçe çeviri seçtiğin alanın hemen üstündeki ince şeritte görünmeli. Üstte yer yoksa şerit alanın altında açılmalı.
- Normal durumda yalnızca çeviri görünmeli; fareyi şeridin üzerine getirince kontroller açılmalı.
- Suflör şeridi izlenen oyun alanının ekran görüntüsüne girmemeli.
- **Kaynağı göster** düğmesi özgün metni açıp kapatmalı.
- **Duraklat** seçiliyken yeni metin işlenmemeli; **Devam et** sonrasında izleme sürmeli.
- **Alanı değiştir** yeni bir dikdörtgen seçtirmeli.
- **Kapat** bütün Bölge İzleme işini durdurmalı.
- Aynı yazı ekranda kalırken yeniden yükleniyor veya çevriliyor göstergesi çıkmamalı.

Hızlı değişen animasyon sırasında yarım yazının çevrilmemesi beklenir; uygulama görüntünün kararlı hale
gelmesini bekler.

Ekran yakalama korumasının Windows tarafından kullanılamadığı bir sistemde Suflör pencereleri yakalama
anında çok kısa süreliğine gizlenip geri gelebilir. Sonuç görüntüsünde yine görünmemeleri gerekir.

## 5. Çeviri hafızasını test et

1. Anlık Çeviri veya Bölge İzleme ile kısa ve belirgin bir cümleyi çevir.
2. Türkçe sonucu not et.
3. Aynı kaynak cümleyi yeniden göster ve tekrar çevir.
4. Uygulamayı kapatıp açtıktan sonra aynı denemeyi bir kez daha yap.

Beklenen sonuç:

- Aynı kaynak cümle aynı Türkçe karşılığı vermeli.
- İkinci ve sonraki çeviriler önceki kayıt sayesinde daha hızlı gelebilir.
- Hafıza yalnızca bilgisayarındaki `%APPDATA%\Suflor\db.sqlite` dosyasında tutulmalı.

## Sorun bildirirken

Şu dört bilgiyi birlikte yaz:

1. Hangi adımda sorun oluştu?
2. Kaynak dil ve ekrandaki metin neydi?
3. Beklediğin sonuç ve gördüğün sonuç neydi?
4. Oyun pencereli, kenarlıksız tam ekran veya exclusive fullscreen mıydı?

Metin veya ekran görüntüsü özel bilgi taşıyorsa paylaşma; aynı sorunu örnek bir metinle yeniden üretmek yeterlidir.
