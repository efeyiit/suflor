# T-012 — UI kabuğu: pencere düğmeleri ve kenar sekmesi (kullanıcı isteği, 11 Eylül 2026)

**Kullanıcının sözleriyle:** "3 pencere düğmesi olsun sağ üste: biri uygulama kapatma, biri arkaplanda
çalıştırma, biri de gene arkaplana atacak yani masaüstünde gözükmeyecek ama ekranın bir kenarında küçük
bir yarım daire olacak; imleçle oraya gidince çevirme seçeneği çıkacak, iki tane."

## Yorum (şef) — tasarım dokümanı A7 (UI ve Overlay) kapsamına girer

Ana pencerenin sağ üstünde **üç düğme**, standart Windows kapat/küçült yerine:

| # | Düğme | Davranış |
|---|---|---|
| 1 | **Kapat** | Uygulama tamamen kapanır (model süreçleri dahil; tepside kalıntı yok). |
| 2 | **Arka plana al (tepsi)** | Pencere gizlenir, uygulama **sistem tepsisinde** çalışır; kısayollar (`Ctrl+Alt+T` / `Ctrl+Alt+R`) çalışmaya devam eder; tepsi ikonuna tıklayınca pencere geri gelir. |
| 3 | **Kenar sekmesi** | Pencere gizlenir, masaüstünde **hiçbir pencere görünmez**; ekranın bir kenarında (varsayılan: sağ kenar, dikey orta; sürüklenebilir) **küçük yarım daire** durur. İmleç üstüne gelince sekme açılır ve **iki seçenek** çıkar: **Anlık çeviri** (Snapshot modu) ve **Bölge izle** (Region-watch). İmleç uzaklaşınca kapanır. Yarım daire oyunun üstünde kalır (`WindowStaysOnTopHint`), tıklamayı yalnız kendi alanında yutar. |

Notlar:
- Yarım daire boyutu ~24–28 px yarıçap, yarı saydam; oyuna fare girdisi geçişi A7 kabul kriteri ("overlay tıklamayı yutmamalı") yalnız sekme dışı alan için.
- Sekmeden ana pencereye dönüş: sekmede üçüncü küçük bir "pencereyi göster" simgesi ya da sağ tık menüsü (kullanıcıya sorulacak; varsayılan sağ tık).
- Çoklu monitör: sekme ana (birincil) monitörün kenarında başlar; sürüklenerek başka monitöre taşınabilir (T-003 DPI dönüşümleri).
- Ölçüler paket yazılırken: hover açılma gecikmesi (ms), kapanma gecikmesi, DPI %100/%150/%200 konumlandırma, iki monitör.

**Durum:** istek alındı; UI kabuğu görevi (T-012) paketlenirken K maddelerine dönüştürülecek. Öncelik: T-011 kapanışından sonra ilk UI görevi.
