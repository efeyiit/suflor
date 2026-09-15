---
task: T-013
title: "KisayolServisi: global kısayollar (Ctrl+Alt+T anlık çeviri, Ctrl+Alt+R bölge izle) — tepsideyken/kenardayken de çalışır; çakışma açıkça bildirilir"
role: implementer
level: B
wave: 3
packet_version: 1
owns:
  - "src/ui/kisayol.py"
  - "src/ui/uygulama.py"
  - "src/ui/kabuk.py"
  - "tests/unit/ui/test_kisayol.py"
  - "tests/unit/ui/test_uygulama.py"
  - "tests/unit/ui/test_kabuk.py"
  - ".agents/tasks/T-013/evidence/**"
  - ".agents/tasks/T-013/delivery.md"
forbidden:
  - "src/ui/kenar_sekmesi.py"
  - "src/ui/geometri.py"
  - "src/contracts/**"
  - "src/capture/**"
  - "src/ocr/**"
  - "src/translate/**"
  - "tests/unit/ui/conftest.py"
  - "demo/**"
  - ".agents/tasks/T-013/real_check.py"
  - ".agents/tasks/T-013/olcum_kisayol.py"
  - "diğer tüm dizinler"
depends_on: ["T-012"]
acceptance:
  - "python -m mypy --strict --explicit-package-bases src/ui"
  - "python -m pytest tests/unit/ui -q"
  - "python .agents/tasks/T-013/real_check.py"
  - "python -m pytest tests/unit/ui -q --cov=src.ui --cov-fail-under=95 --cov-report=term-missing"
  - "python -m pytest tests -q"
budget_ms: 20   # WM_HOTKEY → sinyal gecikmesi (ölçüldü 1.9 ms)
---

> **Bu paket yedi ön ölçüme dayanıyor:** `.agents/tasks/T-013/olgular.txt` (U1–U7, gerçek Windows, sentetik `keybd_event`): `RegisterHotKey(hwnd=NULL)` + `QAbstractNativeEventFilter` **WM_HOTKEY alıyor, 1.9 ms**; aynı kombinasyonu ikinci kayıt (aynı ya da başka süreç) `False` + `GetLastError 1409`, diğer süreç ölünce serbest; **bütün pencereler gizliyken olay geliyor** (tepsi/kenar durumu); `MOD_NOREPEAT` ile basılı tutma 1 olay; filtre içinde istisna Qt tarafından yutuluyor ama **stderr'e traceback basılıyor**; `UnregisterHotKey` sonrası olay yok, yeniden kayıt çalışıyor; bu makinede `Ctrl+Alt+T/R` boş. Tasarım dokümanı bileşen 12 `HotkeyService.register(combo, handler)`, A7 "kısayol çakışması testi". T-012 açık kalemi: kısayollar tepsideyken de çalışmalı (kullanıcı isteği: "arkaplanda çalıştırma").

# Görev

1. **`src/ui/kisayol.py`** — `KisayolServisi(QObject)`: `kaydet(ad: str, kombinasyon: str) -> KayitSonucu`, `kaldir(ad) -> None`, `hepsini_kaldir() -> None`, `kayitli() -> Mapping[str, str]`; sinyal `tetiklendi(str)` (ad); `KayitSonucu(StrEnum)`: `OK`, `CAKISMA` (1409), `GECERSIZ` (ayrıştırılamayan kombinasyon), `HATA` (diğer Win32 hata; kod özellikte). Kombinasyon dilbilgisi: `"Ctrl+Alt+T"` — değiştiriciler `Ctrl Alt Shift Win` (sıra serbest, büyük/küçük duyarsız), tuş: tek harf/rakam, `F1`–`F24`, `Space`, `Esc`… (küçük tablo); en az bir değiştirici **zorunlu** (`"T"` → `GECERSIZ`; oyun tuşlarını çalmamak için). Her kayıt `MOD_NOREPEAT` ile. Win32 çağrıları **enjekte edilebilir** (`kayit_fn`, `kaldir_fn`, `hata_kodu_fn`) — offscreen/CI testleri gerçek `RegisterHotKey` çağırmaz; gerçek Win32 yalnız `real_check`.
2. **`uygulama.calistir`** — servisi kurar: `Ctrl+Alt+T → pencere.anlik_cevir_istendi`, `Ctrl+Alt+R → pencere.bolge_izle_istendi`; `cikis_istendi` → `hepsini_kaldir()`; çakışma → `pencere.durum_goster("Ctrl+Alt+T başka bir uygulama tarafından kullanılıyor — ayarlardan değiştirin")` (yeni küçük `AnaPencere.durum_goster(metin: str)` API'si: durum satırı; **modal yok**). `calistir(..., kisayollar: Mapping[str, str] | None = None)` — varsayılan `{"anlik_cevir": "Ctrl+Alt+T", "bolge_izle": "Ctrl+Alt+R"}`; ayar dosyası **yok** (v2).

## Arayüz (bağlayıcı)
- `KisayolServisi(ebeveyn: QObject | None = None, *, kayit_fn=None, kaldir_fn=None, hata_kodu_fn=None)`; `kaydet`, `kaldir`, `hepsini_kaldir`, `kayitli`, `son_hata_kodu: int`; sinyal `tetiklendi(str)`; sınıf yöntemi `kombinasyonu_coz(metin) -> tuple[int, int]` (mod, vk) — saf, `ValueError`.
- `AnaPencere.durum_goster(metin: str) -> None` (durum satırı; boş dize temizler) ve `AnaPencere.durum_metni() -> str` (kapı okur).
- `calistir(argv=None, *, kenar=Kenar.SAG, calistirici=None, kisayollar=None)`.

---

# Değişmezler

## K1 · Kayıt/kaldırma durum makinesi
**DEĞİŞMEZ:** Aynı `ad` ikinci kez `kaydet` → önce eski kayıt kaldırılır (yeniden bağlama); aynı **kombinasyon** başka `ad` ile → `CAKISMA` (Win32 1409 ya da servis içi tekrar — ikisi de). `kaldir(bilinmeyen ad)` sessiz. `hepsini_kaldir()` idempotent; nesne silinirken (`destroyed`) kalan kayıtlar kaldırılır (süreç kapanınca Windows zaten temizler ama uygulama içi yeniden kurulum için gerekli). Win32 kimlikleri (`id`) 1'den artan, ad→id tablosu.
**ÖLÇÜ (sahte Win32):** kaydet/kaldir çağrı dizileri; 1409 → `CAKISMA` ve `kayitli()`de yok; aynı ad yeniden → önce kaldır sonra kaydet (çağrı sırası); `hepsini_kaldir` ×2; `destroyed` sonrası kaldırma çağrıları.

## K2 · Olay yolu: WM_HOTKEY → `tetiklendi(ad)` yalnız bizim id'ler için
**DEĞİŞMEZ:** Native filtre `WM_HOTKEY` mesajını `wParam` (id) ile eşler; bilinmeyen id → dokunmaz (`False` döner, başka bileşen alabilir); bilinen id → `tetiklendi(ad)` yayar, `True` döner. Filtre **istisna sızdırmaz**: sinyal dinleyicisi istisna atarsa Qt yutar (bu kabul); filtrenin kendi gövdesi istisna üretmez (ölçü: mesaj yapısı bozuksa `False`). Filtre yalnız bir kez kurulur (`QCoreApplication.installNativeEventFilter`), servis silinince kaldırılır. Gecikme WM_HOTKEY → sinyal < 20 ms (ölçüldü 1.9).
**ÖLÇÜ (offscreen, sahte MSG):** `nativeEventFilter` doğrudan çağrılır — bilinen id → sinyal 1 + `True`; bilinmeyen id → sinyal 0 + `False`; WM_HOTKEY dışı mesaj → `False`; servis silindikten sonra filtre kaldırılmış (`QCoreApplication` filtre listesi yoklanamaz → `kaldirildi` bayrağı + sahte uygulama nesnesi). Gerçek WM_HOTKEY yalnız `real_check`.

## K3 · Kombinasyon dilbilgisi saf ve katı
**DEĞİŞMEZ:** `kombinasyonu_coz`: değiştirici seti {Ctrl, Alt, Shift, Win} (`Control`/`Ctrl`, `Alt`, `Shift`, `Win`/`Meta` eşanlamlı), en az biri zorunlu; tuş: `A`–`Z`, `0`–`9`, `F1`–`F24`, `Space`, `Esc`/`Escape`, `Tab`, `Enter`/`Return`, `Backspace`, `Delete`, `Insert`, `Home`, `End`, `PageUp`, `PageDown`, ok tuşları; boşluklar kırpılır; tekrar eden değiştirici → `ValueError`; iki tuş → `ValueError`. Dönüş `(mod | MOD_NOREPEAT, vk)`.
**ÖLÇÜ:** tablo testi (≥ 30 örnek: geçerli/geçersiz); `"ctrl + alt + t"` ≡ `"Alt+Ctrl+T"`; `"T"`, `"Ctrl"`, `"Ctrl+Ctrl+T"`, `"Ctrl+T+R"`, `""` → `ValueError`; `kaydet` bunları `GECERSIZ` olarak döndürür (Win32 çağrılmaz — sahte fn sayacı 0).

## K4 · Tepside/kenardayken çalışır; kabuk durumundan bağımsız
**DEĞİŞMEZ:** Kayıt `hwnd=NULL` (thread kuyruğu) — pencere görünürlüğüne bağlı değil (U3). `calistir` kısayolları **kabuk durumundan bağımsız** bağlar: tetiklenince ilgili sinyal yayılır; kabuk `tepsi`/`kenar`daysa pencere **açılmaz** (sinyal alıcısı — pipeline — karar verir; T-012 K7).
**ÖLÇÜ:** `real_check`: üç durumda (görünür/tepsi/kenar) sentetik `Ctrl+Alt+T` → `anlik_cevir_istendi` 1, durum değişmedi. Offscreen: `calistir(calistirici=…)` ile servis bağlantısı: `tetiklendi("anlik_cevir")` → `anlik_cevir_istendi` 1.

## K5 · Çakışma açıkça bildirilir, modal yok, uygulama çalışmaya devam eder
**DEĞİŞMEZ:** `CAKISMA`/`HATA` → `durum_goster(...)` + tepsi ipucu (`Tepsi.ikon().setToolTip`) — `QMessageBox` **yok**; diğer kısayol çalışmaya devam eder; `calistir` çıkış kodunu değiştirmez. `GECERSIZ` (yapılandırma hatası) da aynı yolla bildirilir.
**ÖLÇÜ:** sahte `kayit_fn` biri için `False`+1409 → `durum_goster` metni "Ctrl+Alt+T" içerir, diğeri `OK`; AST: `src/ui/kisayol.py` ve `uygulama.py`'de `QMessageBox`/`exec` yok; `real_check`: başka bir süreç `Ctrl+Alt+T`'yi tutarken `calistir` → durum satırı dolu, `Ctrl+Alt+R` çalışıyor.

## K6 · Metin yok, blok yok, thread
**DEĞİŞMEZ:** `print`/`logging`/`warnings` yok; `time.sleep` yok; `RegisterHotKey` **yalnız ana thread**'den (`QThread.currentThread() is app.thread()` değilse `RuntimeError`). Kombinasyon metinleri UI metnidir (log değil), serbest.
**ÖLÇÜ:** AST; başka thread'den `kaydet` → `RuntimeError` (sahte Win32 çağrılmaz).

---

# Kabul kapısı — `real_check.py` (şefe ait; koş, yazma)
Gerçek Windows, sentetik `keybd_event` (offscreen değil; ekran kilitli olmamalı): (1) `calistir(calistirici=…)` ile kurulum; `Ctrl+Alt+T` → `anlik_cevir_istendi` 1, gecikme < 20 ms; `Ctrl+Alt+R` → `bolge_izle_istendi` 1; (2) tepsi ve kenar durumlarında aynı, durum değişmedi; (3) başka süreç `Ctrl+Alt+T` tutarken → `CAKISMA`, durum satırı dolu, `Ctrl+Alt+R` çalışıyor; (4) `kapat()` → kısayollar kaldırıldı: tuş → sinyal 0; ikinci süreç aynı kombinasyonu artık alabiliyor; (5) 700 ms basılı → 1 sinyal; (6) 20 hızlı basış → 20 sinyal (kayıp yok); (7) `Ctrl+Alt+T` basılıyken `Alt` menü/odak yan etkisi: aktif pencere değişmedi.

# Teslim
`delivery.md`; K1–K6 docstring + `known_gaps` (ayar dosyası v2; donanım tekrar `[ÖLÇÜLMÜYOR]` sentetik; exclusive fullscreen oyunda RegisterHotKey `[ÖLÇÜLMÜYOR]`; UAC yükseltilmiş pencere odaktayken kısayol gelmez — Windows kısıtı, belge). **Ölçümün paketle çelişirse ölçümüne uy, yaz.** Model/sağlayıcı/araç adı yazma; delillerde mutlak yol yok.
