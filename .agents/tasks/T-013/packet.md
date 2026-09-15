---
task: T-013
title: "KisayolServisi: global kısayollar (Ctrl+Alt+D anlık çeviri, Ctrl+Alt+R bölge izle) — tepsideyken/kenardayken de çalışır; çakışma açıkça bildirilir"
role: implementer
level: B
wave: 3
packet_version: 2
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
  - ".agents/tasks/T-013/krt_kosumlari/**"
  - "diğer tüm dizinler"
depends_on: ["T-012"]
acceptance:
  - "python -m mypy --strict --explicit-package-bases src/ui"
  - "python -m pytest tests/unit/ui -q"
  - "python .agents/tasks/T-013/real_check.py"
  - "python -m pytest tests/unit/ui -q --cov=src.ui --cov-fail-under=95 --cov-report=term-missing"
  - "python -m pytest tests -q"
budget_ms: 20   # WM_HOTKEY → sinyal gecikmesi, BOŞTA (ölçüldü 1.9 ms); yük altında [ÖLÇÜLMÜYOR] (KRT: Python thread'leriyle 200+ ms — GIL)
---

> **Paket sürümü 2.** v1 kırmızı takımdan **3 yüksek / 8 orta / 7 düşük** ile döndü (`krt-1.md`, ham ölçümler `krt_kosumlari/`). ▲ = düzeltme. Üç yüksek: (Y1) offscreen'de de Win32 dağıtıcı çalışıyor → enjeksiyonsuz `calistir` testleri **gerçek** kısayol kaydediyor, paralel pytest 1409; (Y2) **Türkçe Q klavyede `Ctrl+Alt` = AltGr**: `Ctrl+Alt+T` kayıtlıyken ₺ hiçbir uygulamada yazılamıyor (AltGr'de dolu: A E I Q S T + 9 rakam) → varsayılan **`Ctrl+Alt+D`** (dondur) + `Ctrl+Alt+R`, ve AltGr çakışması kayıtta **tespit edilir**; (Y3) `self.destroyed.connect(self.yontem)` PySide6 6.11'de çalışmıyor (4/4) → alıcı `self`'siz serbest fonksiyon/partial.
>
> **Ön ölçümler** (`olgular.txt` U1–U7 + KRT k1–k9, gerçek Windows): `RegisterHotKey(hwnd=NULL)` + `QAbstractNativeEventFilter` **1.9 ms**; aynı kombinasyon ikinci kayıt `False`+1409 (aynı/başka süreç), diğer süreç ölünce serbest; bütün pencereler gizliyken olay geliyor; `MOD_NOREPEAT`: 5 DOWN (UP'sız) → 1 olay, NOREPEAT'siz 5; filtre içi istisna stderr'e basılır (Qt yutar); `UnregisterHotKey` sonrası olay yok; borderless tam ekran topmost başka süreçte kısayol geliyor; Alt menü modu yan etkisi yok; demo uçtan uca (tepsideyken `Ctrl+Alt+R` seçim katmanını açtı). Tasarım bileşen 12 `HotkeyService`; tasarımın `Ctrl+Alt+S`/`T` örnekleri TR-Q'da AltGr çakışır (karara yazılır).

# Görev

1. **`src/ui/kisayol.py`** — `KisayolServisi(QObject)`: `kaydet(ad, kombinasyon) -> KayitSonucu`, `kaldir(ad)`, `hepsini_kaldir()`, `kayitli() -> Mapping[str, str]`; sinyal `tetiklendi(str)`; `KayitSonucu(StrEnum)`: `OK`, `CAKISMA` (1409), `ALTGR_CAKISMA` ▲, `GECERSIZ`, `HATA` (`son_hata_kodu`). Her kayıt `MOD_NOREPEAT`. Win32 çağrıları enjekte edilebilir (`kayit_fn`, `kaldir_fn`, `hata_kodu_fn`, ▲ `altgr_karakteri_fn`); ▲ **gerçek Win32 yalnız açıkça istenince**: yapıcı `gercek_win32: bool = False` — `True` değilse ve fn'ler verilmemişse `RuntimeError` (Y1: offscreen'de de gerçek kayıt olur; birim test asla gerçek kaydetmez). `real_check` ve `calistir` `gercek_win32=True` kullanır.
2. **`uygulama.calistir(argv=None, *, kenar=Kenar.SAG, calistirici=None, kisayollar=None, kisayol_servisi=None)`** — ▲ `kisayol_servisi` verilmezse gerçek servis kurulur (`gercek_win32=True`); testler sahte servis enjekte eder. Varsayılan `{"anlik_cevir": "Ctrl+Alt+D", "bolge_izle": "Ctrl+Alt+R"}` ▲. `tetiklendi("anlik_cevir") → pencere.anlik_cevir_istendi`, `"bolge_izle" → bolge_izle_istendi`; `cikis_istendi → hepsini_kaldir()`. Sonuç `OK` değilse `pencere.durum_goster(...)` + tepsi ipucu; ▲ kombinasyonlar pencerede **görünür**: `AnaPencere.kisayol_etiketleri({"anlik_cevir": "Ctrl+Alt+D", ...})` mod düğmelerinin kısayol metnini günceller (bugün sabit "Ctrl+Alt+T/R" yazıyor — yalan olur), tepsi ipucu da.

## Arayüz (bağlayıcı)
- `KisayolServisi(ebeveyn=None, *, gercek_win32=False, kayit_fn=None, kaldir_fn=None, hata_kodu_fn=None, altgr_karakteri_fn=None)`; `kaydet`, `kaldir`, `hepsini_kaldir`, `kayitli`, `son_hata_kodu: int`; sinyal `tetiklendi(str)`; sınıf yöntemi `kombinasyonu_coz(metin) -> tuple[int, int]` (mod, vk) — saf, `ValueError`; ▲ modül fonksiyonu `altgr_karakteri(vk: int) -> str` (gerçek `ToUnicodeEx`, etkin düzen; `""` = karakter yok).
- `AnaPencere.durum_goster(metin)`, `AnaPencere.durum_metni() -> str`, ▲ `AnaPencere.kisayol_etiketleri(etiketler: Mapping[str, str]) -> None`.
- `calistir(argv=None, *, kenar=Kenar.SAG, calistirici=None, kisayollar=None, kisayol_servisi=None)`.

---

# Değişmezler

## K1 · Kayıt/kaldırma durum makinesi (▲ O4, Y3)
**DEĞİŞMEZ:** Aynı `ad` yeniden `kaydet` → önce eski kayıt kaldırılır; aynı kombinasyon başka `ad` → `CAKISMA` (servis içi tekrar da). `kaldir(bilinmeyen)` sessiz; `hepsini_kaldir()` idempotent. ▲ Win32 `id` **süreç genelinde benzersiz** (modül düzeyi sayaç, 1..0xBFFF; KRT: aynı id iki kayıt alıyor ve `UnregisterHotKey` ikisini birden siliyor). ▲ Nesne silinirken temizlik: `destroyed` alıcısı **`self`'i yakalamayan** serbest fonksiyon/`partial` (paylaşılan kayıt tablosu + `kaldir_fn` + filtre + `removeNativeEventFilter` argüman olarak) — bağlı yöntem PySide6 6.11'de çalışmaz (KRT 4/4). `kaldir` yalnız kendi id'lerini çağırır.
**ÖLÇÜ (sahte Win32):** çağrı dizileri; 1409 → `CAKISMA`, `kayitli()`de yok; aynı ad yeniden → kaldır sonra kaydet; `hepsini_kaldir` ×2; ▲ aynı süreçte iki servis → id kümeleri ayrık; ▲ `del`+gc ve `deleteLater`+`qtbot.wait` yollarında sahte `kaldir_fn` her id için çağrıldı ve filtre kaldırıldı (`removeNativeEventFilter` sahte uygulama nesnesinde sayıldı) — pozitif kontrol: bağlı yöntemle bağlanmış bir kopya bu ölçüde **düşer**.

## K2 · Olay yolu: WM_HOTKEY → `tetiklendi(ad)` yalnız bizim id'ler için (▲ O7, Y1)
**DEĞİŞMEZ:** Filtre `eventType == b"windows_generic_MSG"` değilse `False`; `WM_HOTKEY` ve bilinen `wParam` → `tetiklendi(ad)`, `True`; bilinmeyen id → `False` (filtreler son kurulan önce çağrılır; eski servis yeni servisin olayını yutmaz). Filtre bir kez kurulur, silinince kaldırılır. ▲ "Bozuk mesaj" ölçüsü **yok**: sıfır/bozuk adres `MSG.from_address` ile süreci öldürür (KRT); filtre `message` adresini yalnız Qt'den alır. Gecikme boşta < 20 ms; yük altında `[ÖLÇÜLMÜYOR]` (GIL).
**ÖLÇÜ (offscreen, sahte MSG — gerçek `ctypes.wintypes.MSG` yapısı, adresi `ctypes.addressof`):** bilinen id → sinyal 1 + `True`; bilinmeyen → 0 + `False`; WM_HOTKEY dışı → `False`; yanlış `eventType` → `False`; ▲ `gercek_win32=False` iken `kayit_fn` verilmemişse `RuntimeError` (pozitif kontrol: verilince `OK`). Gerçek WM_HOTKEY yalnız `real_check`.

## K3 · Kombinasyon dilbilgisi saf ve katı (▲ O3, Y2)
**DEĞİŞMEZ:** Değiştiriciler `Ctrl`/`Control`, `Alt`, `Shift` (`Win`/`Meta` → `GECERSIZ`: Windows rezerve, 34/36 1409); tuş tablosu: `A`–`Z`, `0`–`9`, `F1`–`F11` (`F12` `GECERSIZ`: hata ayıklayıcı), `Space`, `Esc`, `Tab`, `Enter`, `Backspace`, `Delete`, `Insert`, `Home`, `End`, `PageUp`, `PageDown`, ok tuşları. ▲ Harf/rakam/`Space` için değiştirici kümesi ⊇ {Ctrl,Alt} ya da ⊇ {Ctrl,Shift} ya da ⊇ {Alt,Shift} (tek değiştirici, `Shift`-tek → `GECERSIZ`: `Shift+T` büyük T'yi yutuyor); `F1`–`F11` için ≥ 1. ▲ Kara liste `GECERSIZ`: `Alt+Tab`, `Alt+F4`, `Alt+Esc`, `Alt+Space`, `Ctrl+Esc`, `Ctrl+Alt+Delete`, `Ctrl+Shift+Esc`. Boşluk/harf durumu serbest; tekrar eden değiştirici, iki tuş, boş → `ValueError`. ▲ **AltGr:** kombinasyon `Ctrl+Alt+<tuş>` (Shift'siz) ise ve `altgr_karakteri(vk)` boş değilse `kaydet` → `ALTGR_CAKISMA` (Win32 çağrılmaz): TR-Q'da A E I Q S T 0-5 7-9. Düzen çalışırken değişirse `[ÖLÇÜLMÜYOR]` (kayıt anındaki düzen).
**ÖLÇÜ:** tablo ≥ 40 örnek; `"ctrl + alt + d"` ≡ `"Alt+Ctrl+D"`; ▲ sahte `altgr_karakteri_fn` `T→"₺"` ile `Ctrl+Alt+T` → `ALTGR_CAKISMA`, `Ctrl+Alt+R` → `OK`, `Ctrl+Shift+T` → `OK` (AltGr yolu Shift'lide sorulmaz); `real_check` gerçek `ToUnicodeEx` ile TR-Q'da `T → "₺"`, `D → ""`.

## K4 · Tepside/kenardayken çalışır; kabuk durumundan bağımsız
**DEĞİŞMEZ:** `hwnd=NULL`; kabuk `tepsi`/`kenar`daysa pencere açılmaz, yalnız sinyal (alıcı karar verir). ▲ `calistir` içindeki bağlantı `tetiklendi(ad)` → ad tablosuyla sinyal; bilinmeyen ad yok sayılır.
**ÖLÇÜ:** offscreen: sahte servis ile `calistir(calistirici=…, kisayol_servisi=sahte)` → sahte `tetiklendi.emit("anlik_cevir")` → `anlik_cevir_istendi` 1, üç durumda durum değişmez. Gerçek: `real_check`.

## K5 · Çakışma açıkça bildirilir, kısayollar görünür, modal yok (▲ O8)
**DEĞİŞMEZ:** `OK` dışı sonuç → `durum_goster("<kombinasyon> kaydedilemedi: <sebep>. Pencere düğmeleri ve tepsi menüsü çalışmaya devam eder.")` (sebep: "başka bir uygulama kullanıyor" / "bu klavye düzeninde AltGr ile çakışıyor" / "geçersiz kombinasyon") — "ayarlardan değiştirin" **yazılmaz** (ayar yok, v2); tepsi ipucu güncellenir. ▲ `kisayol_etiketleri` mod düğmelerinde ve tepsi ipucunda **kayıtlı** kombinasyonları gösterir; kaydedilemeyen için "(kısayol yok)". Diğer kısayol çalışmaya devam eder; `calistir` çıkış kodu değişmez. `QMessageBox` yok.
**ÖLÇÜ:** sahte `kayit_fn` biri `False`+1409 → durum metni kombinasyonu ve "başka bir uygulama" içerir, diğeri `OK`; `ALTGR_CAKISMA` metni "AltGr"; düğme metinleri; AST (`QMessageBox`/`QDialog.exec` yok; `uygulama.py` `app.exec()` serbest).

## K6 · Metin yok, blok yok, thread
**DEĞİŞMEZ:** `print`/`logging`/`warnings`/`time.sleep` yok; `kaydet` yalnız ana thread (`QThread.currentThread() is app.thread()` değilse `RuntimeError`, Win32 çağrılmaz). Gerçek Win32 ince sarmalayıcıları `# pragma: no cover` (offscreen'de koşulmaz — D4).
**ÖLÇÜ:** AST; başka thread'den `kaydet` → `RuntimeError`, sahte sayaç 0.

---

# Kabul kapısı — `real_check.py` v2 (şefe ait; koş, yazma)
Gerçek Windows, sentetik `keybd_event`, ekran kilitsiz: (1) `calistir(calistirici=…)` (gerçek servis) → `Ctrl+Alt+D` → `anlik_cevir_istendi` 1, gecikme < 20 ms; `Ctrl+Alt+R` → `bolge_izle_istendi` 1; (2) tepsi ve kenar durumlarında aynı, durum değişmedi; (3) başka süreç `Ctrl+Alt+D` tutarken → durum satırı "Ctrl+Alt+D" + "başka bir uygulama", `Ctrl+Alt+R` çalışıyor, düğme etiketi "(kısayol yok)"; çocuk süreç `try/finally` ile öldürülür; (4) `kapat()` → sinyal 0, aynı kombinasyon yeniden alınabiliyor; (5) ▲ pozitif kontrollü tekrar: 5 DOWN (UP'sız) → **1** sinyal, NOREPEAT'siz kayıtla **5** (ayrı geçici kayıt); (6) 20 hızlı basış → 20; (7) ▲ RAPOR: `Ctrl+Alt+D` öncesi/sonrası ön plan hwnd ve menü modu (`GetGUIThreadInfo` `GUI_INMENUMODE`) — değişmemeli; (8) ▲ gerçek `altgr_karakteri`: `T → "₺"` (TR-Q'da), `D → ""`; `kaydet("x", "Ctrl+Alt+T")` → `ALTGR_CAKISMA`; (9) ▲ `del`+gc yolu: servis düşürülünce `Ctrl+Alt+D` yeniden alınabiliyor (`deleteLater` yolu kapıda `[ÖLÇÜLMÜYOR]` — `processEvents` döngüsü işlemez; birim testte).

# Teslim
`delivery.md`; K1–K6 docstring + `known_gaps` (ayar dosyası v2; donanım autorepeat sentetikle `[ÖLÇÜLMÜYOR]`; exclusive fullscreen ve UAC yükseltilmiş pencere `[ÖLÇÜLMÜYOR]` — sentetik girdi UIPI'ye takılır; düzen değişimi; yük altında gecikme). **Ölçümün paketle çelişirse ölçümüne uy, yaz.** Model/sağlayıcı/araç adı yazma; delillerde mutlak yol yok. `tests/unit/ui/conftest.py` şefe ait: `SUFLOR_GERCEK_KISAYOL_YASAK=1` ortam değişkeni koyar — servis bu değişken varken `gercek_win32=True` ile kurulursa `RuntimeError` (Y1 emniyet kemeri; `real_check` ayrı süreç, değişken yok).
