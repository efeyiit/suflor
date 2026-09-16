---
task: T-014
role: sef
round: 1
decision: kabul
---

# T-014 — Anlık çeviri (Snapshot) modu: KABUL

Tek elden (16 Eylül süreç kararı): ölçüm → kod + testler → gerçek OCR/NMT kapısı → karar. Ürünün **ana modu** artık uçtan uca çalışıyor: kısayol/düğme → imlecin monitörü donar → OCR blokları çerçeveler → tıkla/sürükle seç → Enter → Türkçe blokların yanında.

## Ölçüm (`olgular.txt`, gerçek motorlar, sentetik 2560×1440 kare)
- `capture_full` 35 ms · tam kare OCR **360–550 ms** (KR/JP, 3 boyda 12/12 satır; 0.4× = ~16 px metin de okunuyor) · 1280×720'ye küçültme küçük metni **kaybediyor** (43 → 13 blok) ve JP'de yavaşlıyor → küçültme yok, tam kare OCR · seçim → çeviri 441 ms sıcak · 2560×1440 BGR → QPixmap 8 ms (UI thread'de kabul edilebilir).
- Kapı sırasında bulunan gerçek: tam kare tespiti kutuları **gevşek** veriyor (dedektör 2560 px'i küçültüyor; h 29 → 38) → normalizer konuşmacı satırını paragrafa yapıştırıyordu ("İhtiyar Marcus kasabası İhtiyar sizi bekliyor"). Çözüm **ikinci geçiş**: seçimin kırpığı yeniden okunur (bölge yakalamayla aynı sıkı kutular) → 2 segment, konuşmacı ayrı. Kapı [4] 1 → 2 sonuç.

## Ne teslim edildi
- `src/pipeline/anlik.py` — `AnlikAkisi(QObject)`: `oku(kare)` → `bloklar_hazir`; `cevir(bloklar)` → ikinci geçiş → normalize → sözlük (yalnız modele) → translate → `ceviri_hazir(segmentler, çeviriler)`; `hata(sınıf_adı)`; **UI thread bloklanmaz** (kendi QThread'i, QueuedConnection); **seq sıra koruması** (eski/iptal edilen sonuç düşürülür); `kapat()` idempotent, `destroyed` → thread durur (self'siz alıcı — T-012/T-013 dersi). Saf zincir fonksiyonları `oku_yap`, `cevir_yap`, `ikinci_gecis`. 25 test; kapsam %89 (kalan: Qt işçi thread'i içindeki slot gövdeleri — kapsam izleyicisi Qt thread'lerini görmez; mantık saf fonksiyonlarla ölçülü).
- `src/pipeline/motorlar.py` — `MotorDeposu`: OCR + NMT + sözlük açılışta arka planda kurulur (`hazir`/`hata`), hazır değilken erişim `RuntimeError`. 3 test.
- `src/ui/anlik_pencere.py` — `AnlikPencere`: tam ekran donmuş kare, blok çerçeveleri, tık/sürükle/Ctrl+A seçimi, Enter → `cevir_istendi`, sonuç kutuları (sağ → alt → üst → sol; seçilen bloklarla ve önceki sonuçlarla kesişmez), Ctrl+C kopyala, Esc → `iptal` bir kez; durum makinesi okunuyor → seçim → çevriliyor → sonuç; hata durum satırı. 18 test, kapsam %99.
- `demo/kabuk.py` — kısayol/düğme/sekme → `anlik_cevir` (fiziksel imleç → monitör → `capture_full` → pencere + akış); tek örnek; seçim sırasında kenar sekmesi gizli; çıkışta akış/depo kapanır. `python demo/kabuk.py [korean|japan|english] [sag|sol]`.

**Gerçek kapı (`real_check.py`, KR ve JP TEMİZ 10/10):** okuma 306–347 ms, UI bu sırada 15–16 kare çizdi (donmadı) · pencere == ekran, bloklar çizili · sürükleme 4 satır seçti · çeviri 0.9–1.3 s, 2 sonuç, boş/eşit yok · sözlük ("Marcus") sonuçta · paint 2.4–2.7 ms · Esc → iptal 1, thread durdu · iptal edilen okuma gelmez, pozitif kontrol gelir.

## Bilinen sınırlar / açık kalemler
| Kalem | Not |
|---|---|
| Unvan gri bölgesi ("İhtiyar kasabası") | T-011 açık kalemi (hedef tarafı düzeltme) |
| DPR ≠ 1 monitörde kare ekrana ölçeklenir; keskinlik `[ÖLÇÜLMÜYOR]`; sürükleme koordinatları mantıksal→fiziksel `_pencereye` ile | kayıt |
| Exclusive fullscreen oyun: tam ekran pencere üstte kalmaz (T-012 sınırı) | belge |
| Tam takım 2276 → **2319**; T-011 süre testleri en-küçük-değer (bakım) | tamam |
| Kısayoldan sonra pencere odak alıyor mu (WM_HOTKEY sonrası `activateWindow`) — demo A3/B3 sınıfı | gerçek oyunla ölçülmeli |
| Sonuç panosu yalnız Türkçe; kaynak metin gösterimi (TM/düzenleme) | v2 |

## Karar
**T-014 KABUL.** mypy --strict temiz (src/pipeline, src/ui, testler), 46 yeni test, gerçek OCR+NMT kapısı KR/JP temiz, tam takım yeşil, `python demo/kabuk.py` ile uçtan uca çalışıyor (ekran görüntüleri `sef_dogrulama/anlik_sonuc_{KR,JP}.png`).
