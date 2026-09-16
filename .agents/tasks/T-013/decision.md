---
task: T-013
role: sef
round: 1
decision: kabul
---

# T-013 — KisayolServisi (global kısayollar): KABUL

Tek tur. **Süreç notu:** kullanıcı 16 Eylül 2026'da çok-ajanlı sistemi bıraktı ("bu sistemi bırakıyoruz, sen halletmeye devam et"); bu görevin tester turu yarıda kesildi (oturum kapandı). Karar şefin kendi koşumları + tester'ların yarım kalan ama **koşulmuş** ölçümleriyle veriliyor. Bundan sonraki görevler tek elden (şef uygular, ölçer, test eder) yürür; ölçüm-önce disiplini ve kapılar kalır, ajan turları kalkar.

## Ne teslim edildi

`src/ui/kisayol.py` — `KisayolServisi(QObject)`: `RegisterHotKey(hwnd=NULL)` + `QAbstractNativeEventFilter`; `kaydet/kaldir/hepsini_kaldir/kayitli`, `tetiklendi(str)`; `KayitSonucu` `OK/CAKISMA/ALTGR_CAKISMA/GECERSIZ/HATA`; **`gercek_win32` kemeri** (offscreen'de de gerçek kayıt olurdu — KRT), `SUFLOR_GERCEK_KISAYOL_YASAK` ortamında gerçek kurulum reddi; süreç genelinde benzersiz id; `self`'siz `destroyed` temizliği; katı dilbilgisi (≥2 değiştirici, `Win`/`F12`/kara liste `GECERSIZ`); **AltGr tespiti** (`ToUnicodeEx`: TR-Q'da `Ctrl+Alt+T` = ₺ → `ALTGR_CAKISMA`); `MOD_NOREPEAT`; ana thread şartı. `uygulama.calistir(kisayollar=…, kisayol_servisi=…)`: varsayılan **`Ctrl+Alt+D`** (anlık) / **`Ctrl+Alt+R`** (bölge); çakışma → durum satırı + "(kısayol yok)" etiketi, modal yok; `AnaPencere.durum_goster/durum_metni/kisayol_etiketleri`. **379 UI testi** (+157), kapsam %99.7, mypy --strict, mutant 34/34, cp1254.

**Gerçek Windows (`real_check` v2, şef 12/12):** tetikleme 0.9 ms · tepsi/kenar durumunda çalışır, durum değişmez · başka süreç D tutarken çakışma metni + R çalışır · `kapat()` sonrası kayıt serbest · 5 DOWN → NOREPEAT 1 / NOREPEAT'siz 5 (pozitif kontrol) · 20 hızlı basış 20/20 · ön plan/menü modu değişmedi · TR-Q `T→₺`, `D→""` · `del`+gc sonrası yeniden alınabilir.

**Tester-B (yarım, koşulmuş kısımlar):** gerçek Windows sondası `sonda1` **TEMİZ** (AltGr tablosu `VkKeyScanW` ile çapraz 62/62 uyumlu; `deleteLater` gerçek `exec` ile temizlik; dinleyici istisnası süreci öldürmüyor; iki `calistir` çakışma metni); mutant kiti B **0 beklenti dışı**; demo sondası 4 bulgu → aşağıda. **Tester-A:** yalnız taban koşumları (5/5 yeşil); test dosyası yarım (süreci düşürüyor — kullanılmadı).

## Tur kaydı

| Tur | Ne oldu |
|---|---|
| ölçüm | U1–U7: WM_HOTKEY 1.9 ms, 1409, gizli pencerede çalışır, NOREPEAT, unregister |
| paket | v1 → **tek** KRT: 3 yüksek (offscreen'de gerçek kayıt; **TR-Q AltGr = Ctrl+Alt**; `destroyed` bağlı yöntem çalışmıyor) + 8 orta → v2 |
| 1 | Implementer: 379 test, kapı 12/12, mutant 34/34; itiraz yok. Tester turu yarıda kesildi (kullanıcı sistemi bıraktı) |

## Şefin ölçülmüş hataları

| # | Hata | Yakalayan |
|---|---|---|
| 1 | Varsayılan `Ctrl+Alt+T` — Türkçe Q klavyede AltGr+T (₺); tasarım dokümanının `Ctrl+Alt+S/T` örnekleri de çakışır | KRT |
| 2 | "Birim testler gerçek Win32 çağırmaz" yapısal olarak sağlanmıyordu (offscreen'de dağıtıcı çalışır) | KRT |
| 3 | K1 `destroyed` mekanizması PySide6'da çalışmıyor (T-012 tur 3'te de aynı sınıf) | KRT |
| 4 | Kapı [5] tek DOWN ile tekrar üretemiyordu, [7] `or True` yapısaldı, bozuk-MSG ölçüsü süreci öldürüyordu | KRT |
| 5 | Demo: kısayolla seçim katmanı açıkken tekrar basılınca ikinci katman açılıyordu | Tester-B (sonda A2) — **düzeltildi** |

## Açık kalemler

| Kalem | Not | Sahip |
|---|---|---|
| **Anlık çeviri (Snapshot) modu** | kısayol + kabuk sinyali hazır; alıcı yok (demo yer tutucu pencereyi gösteriyor) | sıradaki iş |
| Kısayoldan sonra ana pencere ön plana gelmiyor (bazen; tepsi taşma alanı ön planda kalıyor) | Tester-B B3/A3; `goster()` `SetForegroundWindow` denemesi | UI bakım |
| Kısayol ayarı (kullanıcı değiştirebilsin) | ayar dosyası v2 | ayarlar görevi |
| Tasarım dokümanı 2.3 kısayol örnekleri (`Ctrl+Alt+S/T`) TR-Q'da çakışır | belge güncellenmeli | doküman |
| Donanım autorepeat, exclusive fullscreen, UAC yükseltilmiş pencere | `[ÖLÇÜLMÜYOR]` (sentetik girdi UIPI'ye takılır) | belge |
| Yük altında gecikme (GIL, Python thread'leri) 200+ ms | `[ÖLÇÜLMÜYOR]`; pipeline thread'leri gelince ölçülür | pipeline |

## Karar

**T-013 KABUL.** Beş kabul komutu exit 0 (şef), gerçek Windows kapısı 12/12, tam takım **2276**, Tester-B gerçek Windows sondası temiz, demo düzeltildi. `python demo/kabuk.py` açıkken `Ctrl+Alt+R` seçim katmanını açıyor, `Ctrl+Alt+D` pencereyi getiriyor (Snapshot gelince ekranı donduracak).
