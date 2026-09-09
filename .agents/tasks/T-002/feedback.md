# T-002 Geri Bildirim (Tur 1 -- RET)

Bağımsız doğrulama sonucu: kritik davranışların (debounce, livelock direnci, eşiğin iki tarafı, bölge sıfırlama, bütçe) hepsi sağlam bulundu -- bu kısımlara dokunmana gerek yok. Tek blokaj, küçük bölge boyutlarında bir çökme.

## Blokaj 1 (zorunlu düzeltme): küçük bölgelerde `IndexError` çöküşü

`src/capture/change_detector.py::_block_mean_resize`, `np.add.reduceat(gray, row_edges[:-1], axis=0)` çağrısında girdi çok küçükse patlıyor.

**Tekrar üretim** (`tester_evidence/crash_repro_1x1_3x3.txt`):

```
python -c "
import numpy as np
from src.capture.change_detector import ChangeDetector
from src.contracts.models import Frame, Rect
img = np.full((1,1,3), 128, dtype=np.uint8)
det = ChangeDetector()
det.has_changed(Frame(image=img, rect=Rect(x=0,y=0,w=1,h=1), captured_at=1.0, seq=1))
"
```

Ham çıktı:

```
Traceback (most recent call last):
  ...
  File "src\capture\change_detector.py", line 91, in _block_mean_resize
    row_sums: npt.NDArray[np.float32] = np.add.reduceat(
IndexError: index 1 out-of-bounds in add.reduceat [0, 1)
```

Aynı senaryo 3x3 için de çöküyor (`index 3 out-of-bounds`). Bağımsız test dosyamda `test_1x1_region_does_not_crash` ve `test_3x3_region_does_not_crash` bunu birebir gösteriyor (`tester_evidence/tester_pytest_verbose.txt`).

**Kapsam haritası** (kendim ölçtüm, varsayılan `hash_size=8` ile, `w`/`h` 1..9 aralığında tarama):

```
    w=1  2  3  4  5  6  7  8  9
h=1  X  X  X  X  X  X  X  X  X
h=2  X  X  X  X  X  X  X  X  X
h=3  X  X  X  X  X  X  X  X  X
h=4  X  X  X  X  X  X  X  X  X
h=5  X  X  X  X  N  N  N  N  N
h=6  X  X  X  X  N  N  N  N  N
h=7  X  X  X  X  N  N  N  N  N
h=8  X  X  X  X  N  N  N  N  .
h=9  X  X  X  X  N  N  N  N  .
```
`X` = `IndexError` (çöküş), `N` = çökmüyor ama `RuntimeWarning: divide by zero encountered in divide` + `NaN` üretiyor (bkz. Blokaj 2), `.` = temiz. Yani `h<5` VEYA `w<5` olan HERHANGİ bir bölgede çöküyor -- yalnızca 1x1/3x3'e özgü değil.

**Kök neden:** `row_edges = np.linspace(0, h, out_h + 1).round().astype(np.int64)` ile üretilen kova sınırları, `h < out_h` (örn. `h=1`, `out_h=8`) olduğunda tekrarlı/artmayan değerler üretiyor; `np.add.reduceat` monoton artmayan indeks dizisiyle çalışamıyor ve `IndexError` fırlatıyor.

**Neden bloke edici:** Bu bileşenin sözleşmesi "yalnızca verilen `Frame` üzerinde çalış, saf ol" (packet, Kritik kısıtlar) ve girdi boyutu için hiçbir alt sınır belgelenmemiş/denetlenmemiş. Tasarım dokümanı §2.2 adım 2, kullanıcının capture bölgesini "kenarlarından yeniden boyutlandırabileceğini" söylüyor -- küçük bir bölge (yanlışlıkla veya bilinçli) çizilirse Mod 2'nin canlı döngüsü yakalanmamış bir istisnayla çöker. `env.md` madde 6 bu tam senaryoyu ("çok küçük bölge (1×1, 3×3)") açıkça saldırı noktası olarak sayıyor.

**Önerilen çözüm yönü** (zorunlu değil, implementer'ın kararı): `_block_mean_resize` girişine `h >= out_h` ve `w >= out_w` (ya da eşdeğer bir asgari boyut) doğrulaması ekle -- ya `has_changed`/`_dhash` başında `ValueError` fırlat (böylece hata sessiz değil, çağıran taraf -- capture döngüsü -- yakalayıp durum çubuğuna yazabilir; packet §8 "Modal dialog yok, hata durum çubuğuna yazılır" ile uyumlu), ya da çok küçük bölgeler için `hash_size`'ı otomatik küçülten bir yol izle. Hangisini seçersen seç, davranışı docstring'de belgele ve testle.

## Blokaj 2 (aynı kök neden, düşük şiddetli ama gerçek): sınır bandında sessiz `NaN`

Yukarıdaki haritada `N` işaretli bölgelerde (örn. 6x6) çökme yok ama `block_sums / counts` sıfıra bölünüyor, `RuntimeWarning` ve `NaN` üretiyor; `NaN` karşılaştırmaları her zaman `False` döndüğü için ilgili hash bitleri sessizce (denetlenemez şekilde) sabitleniyor. Bağımsız testim: `test_small_region_below_hash_grid_does_not_silently_corrupt` (`tester_evidence/tester_pytest_verbose.txt`). Blokaj 1 için uyguladığın çözüm muhtemelen bunu da kapatır (aynı kök neden) -- ayrı bir yama gerekmeyebilir, ama lütfen doğrula.

## Bloke etmeyen notlar (düzeltme zorunlu değil, kayda geçsin)

1. **Düz renk (siyah/beyaz) tam ekran geçişi görünmez.** Sadece yatay-komşu dHash, düz renkli görüntülerde her zaman `hash=0` üretiyor -- tam siyahtan tam beyaza geçiş bile Hamming mesafesi 0. Bu, seçilen algoritmanın (paket dHash/aHash'e izin veriyor) bilinen matematiksel özelliği, implementasyon hatası saymadım. Yine de docstring'de "yalnızca göreli/yerel kontrast farklarını yakalar, düz renk geçişlerini kaçırabilir" şeklinde bir not eklemen gelecekteki entegrasyon hatalarını önler.
2. Periyodik-döşemeli (senin `_pattern` yardımcın gibi 16px periyotlu) içerik, blok-ortalamalı küçültmeyle birleşince kaydırmaya karşı neredeyse kör olabiliyor -- gerçek oyun metni bu kadar periyodik olmadığı için bloke edici değil, ama kendi test yardımcı fonksiyonunun bu özelliği taşıdığının farkında ol (bkz. bağımsız testim `test_periodic_tiled_content_is_a_documented_blind_spot_not_bug`, salt dokümantasyon amaçlı, assertion yok).

## Dokunmaman istenenler

Debounce mantığı, eşik karşılaştırması (`<=` kapsayıcı), bölge sıfırlama, tabana-dönüşte aday iptali, bütçe -- hepsi bağımsız testlerimde geçti. Bunları yeniden tasarlama; yalnızca küçük-bölge doğrulamasını ekle.
