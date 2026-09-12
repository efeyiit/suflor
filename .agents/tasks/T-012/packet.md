---
task: T-012
title: "UI kabuğu: ana pencere üç düğme (Kapat · Tepsiye al · Kenara al), sistem tepsisi, kenar sekmesi (yarım daire → Anlık çeviri / Bölge izle)"
role: implementer
level: B
wave: 3
packet_version: 1
owns:
  - "src/ui/__init__.py"
  - "src/ui/kabuk.py"
  - "src/ui/kenar_sekmesi.py"
  - "src/ui/geometri.py"
  - "tests/unit/ui/test_kabuk.py"
  - "tests/unit/ui/test_kenar_sekmesi.py"
  - "tests/unit/ui/test_geometri.py"
  - ".agents/tasks/T-012/evidence/**"
  - ".agents/tasks/T-012/delivery.md"
forbidden:
  - "src/contracts/**"
  - "src/capture/**"
  - "src/ocr/**"
  - "src/translate/**"
  - "tests/unit/ui/conftest.py"
  - "demo/**"
  - ".agents/tasks/T-012/real_check.py"
  - ".agents/tasks/T-012/olcum_kabuk.py"
  - "diğer tüm dizinler"
depends_on: ["T-001", "T-003"]
acceptance:
  - "python -m mypy --strict --explicit-package-bases src/ui"
  - "python -m pytest tests/unit/ui -q"
  - "python .agents/tasks/T-012/real_check.py"
  - "python -m pytest tests/unit/ui -q --cov=src.ui --cov-fail-under=95 --cov-report=term-missing"
  - "python -m pytest tests -q"
budget_ms: 16   # kenar sekmesi paintEvent + geometri hesabı (tek kare)
---

> **Kullanıcı isteği (11 Eylül 2026, `istek.md`):** sağ üstte üç düğme — kapat · arka planda çalıştır (tepsi) · kenara al (masaüstünde pencere yok, ekran kenarında küçük **yarım daire**; imleç gelince **iki** çeviri seçeneği: Anlık çeviri / Bölge izle). Şef `demo/kabuk.py` ile prototipledi ve gerçek ekranda ölçtü (`olgular.txt` U0–U6): tepsi var; sekme sağ kenara bitişik, dikey ortada; bayraklar Tool+Frameless+StaysOnTop+NoFocus+translucent; **sekme gösterilince aktif pencere None** (odak çalınmıyor); açılma 193 ms (ayar 120 + 60 ms yoklama), kapanma 469 ms (ayar 450); sürükleme kenar sınırına kilitleniyor; sağ tık pencereyi getiriyor. Bu paket o prototipi **ürün bileşenine** çevirir: saf geometri + test edilebilir durum makinesi + enjekte edilebilir imleç/zaman.

# Görev

`src/ui/` altında üç modül:

1. **`geometri.py`** — saf fonksiyonlar (Qt tipine bağımlı olabilir ama **ekran/pencere yaratmaz**): `sekme_kapali_dikdortgeni(ekran: QRect, y: int, yaricap: int, kenar: Kenar) -> QRect`, `sekme_acik_dikdortgeni(ekran, y, yaricap, panel: QSize, kenar) -> QRect`, `y_sinirla(ekran, y, yaricap) -> int`. `Kenar` = `StrEnum("sag", "sol")` (v1: sağ ve sol; üst/alt yok).
2. **`kenar_sekmesi.py`** — `KenarSekmesi(QWidget)`: yarım daire + açılır panel; sinyaller `anlik_cevir`, `bolge_izle`, `pencereyi_goster`; yapıcı `KenarSekmesi(ekran: QScreen, *, kenar=Kenar.SAG, yaricap=26, acilma_ms=120, kapanma_ms=450, yoklama_ms=60, imlec_konumu: Callable[[], QPoint] = QCursor.pos)`; `y` özelliği (sürükleme/geri yükleme için).
3. **`kabuk.py`** — `AnaPencere(QWidget)`: çerçevesiz, sağ üstte üç düğme (`dugme_kapat`, `dugme_tepsi`, `dugme_kenar` — test için erişilebilir adlar), gövdede iki mod düğmesi; `Tepsi` (QSystemTrayIcon sarmalayıcı); **durum makinesi** `KabukDurumu = StrEnum("gorunur", "tepsi", "kenar")`, `durum` özelliği; sinyaller `anlik_cevir_istendi`, `bolge_izle_istendi`, `cikis_istendi`. Kabuk **model/yakalama/OCR/çeviri bilmez** (K7): yalnız sinyal üretir; bağlama `demo/kabuk.py`'de (şef).

## Arayüz — kapının (`real_check.py`) ve tester'ların kullandığı adlar (bağlayıcı)

- `AnaPencere(ekran: QScreen | None = None, *, tepsi_kullanilabilir: bool | None = None, imlec_konumu: Callable[[], QPoint] | None = None)`; özellikler `durum: KabukDurumu`, `sekme: KenarSekmesi`, `tepsi: Tepsi`, `dugme_kapat`, `dugme_tepsi`, `dugme_kenar`, `dugme_anlik`, `dugme_bolge` (QPushButton); yöntemler `goster()`, `tepsiye_al()`, `kenara_al()`, `kapat()`; sinyaller `anlik_cevir_istendi`, `bolge_izle_istendi`, `cikis_istendi`.
- `KabukDurumu(StrEnum)`: `GORUNUR="gorunur"`, `TEPSI="tepsi"`, `KENAR="kenar"`.
- `KenarSekmesi(ekran, *, kenar=Kenar.SAG, yaricap=26, acilma_ms=120, kapanma_ms=450, yoklama_ms=60, imlec_konumu=None)`; salt-okunur özellikler `yaricap`, `acilma_ms`, `kapanma_ms`, `yoklama_ms`, `acik: bool`, `kenar`; okunur-yazılır `y: int` (sınırlanır); sinyaller `anlik_cevir`, `bolge_izle`, `pencereyi_goster`.
- `Tepsi(ikon: QIcon, ebeveyn: QObject | None, *, kullanilabilir: bool | None = None)`: `goster()`, `gizle()`, `gorunur() -> bool`, `bildir(baslik, metin, ms)`; sinyaller `goster_istendi`, `kenara_al_istendi`, `cikis_istendi`.
- `geometri.py`: `Kenar(StrEnum)`, `sekme_kapali_dikdortgeni`, `sekme_acik_dikdortgeni`, `y_sinirla`, `PANEL_BOYUTU: Final[QSize] = QSize(200, 132)`.

---

# Değişmezler

## K1 · Durum makinesi: üç durum, her geçiş tanımlı, ulaşılamayan durum yok
**DEĞİŞMEZ:** `gorunur ⇄ tepsi`, `gorunur ⇄ kenar`, `tepsi → kenar` (tepsi menüsü), `kenar → tepsi` yok (sekmede tepsi düğmesi yok; kenardan yalnız `pencereyi_goster` → `gorunur`). Her durumda kullanıcıya **en az bir geri dönüş yolu** vardır: `tepsi` → tepsi ikonuna tık ya da menü "Göster"; `kenar` → sağ tık ya da tepsi ikonu (kenar durumunda tepsi ikonu **da** görünür). `kapat()` her durumdan: pencere + sekme + tepsi ikonu kapanır, `cikis_istendi` yayılır; kabuk `QApplication.quit()` **çağırmaz** (uygulama karar verir).
**ÖLÇÜ (pytest-qt, offscreen):** her geçiş bir test; geçiş sonrası `durum`, `isVisible()` üçlüsü (pencere/sekme/tepsi) tablo ile; `kapat()` sonrası görünür üst-düzey widget **0**, `tepsi.gorunur() is False`, `cikis_istendi` **tam bir kez**. Aynı geçişi iki kez çağırmak idempotent (tepsiye al ×2).

## K2 · Geometri saf ve ekran-bağımsız; kenara bitişik, sınırlar içinde
**DEĞİŞMEZ:** Kapalı dikdörtgen: `kenar=sag` için `x = ekran.right() - yaricap + 1`, `w = yaricap`, `h = 2*yaricap`; `sol` için `x = ekran.left()`. Açık dikdörtgen: panel kenara bitişik, `y` sekmenin dikey merkezine hizalı, **`ekran` içine sıkıştırılmış** (üst/alt taşmaz). `y_sinirla`: `[ekran.top(), ekran.bottom() - 2*yaricap + 1]`. Bütün hesap **mantıksal piksel** (`QScreen.availableGeometry`); DPI'ı Qt taşır. Çok monitör: fonksiyonlar verilen `ekran` dikdörtgenine göre çalışır; negatif koordinatlı monitör (`x=-2560`) destek.
**ÖLÇÜ (saf, ekran yok):** 3 ekran dikdörtgeni (`0,0,2560,1392` · `-2560,0,2560,1440` · `0,0,1280,720` %150'yi temsilen) × 2 kenar × 5 `y` (üst sınır, orta, alt sınır, -1000, +9999) → kapalı/açık dikdörtgen `ekran.contains()` **her zaman** doğru; kapalı `right()==ekran.right()` (sağ) / `left()==ekran.left()` (sol); açık panel kenara bitişik; `y_sinirla` monoton. Prototip ölçümü (U2) ile birebir: `(2534,670,26,52)` @ `2560×1392`, `yaricap=26`.

## K3 · Odak ve girdi: sekme odak almaz, oyunun girdisini yutmaz
**DEĞİŞMEZ:** `KenarSekmesi` bayrakları `FramelessWindowHint | Tool | WindowStaysOnTopHint | WindowDoesNotAcceptFocus`, `WA_TranslucentBackground`, `WA_ShowWithoutActivating`. Pencere **yalnız sekme kadar** büyük (tam ekran şeffaf katman yok): sekme dışındaki her tık oyuna gider — yapısal. Açık panel de yalnız panel kadar.
**ÖLÇÜ:** bayrak/öznitelik testi; `show()` sonrası `QApplication.activeWindow()` değişmez (offscreen'de `None` kalır; gerçek ekranda U5 = None ölçüldü, `real_check`); kapalı/açık `frameGeometry` boyutları `(yaricap, 2*yaricap)` ve `panel` ile sınırlı.

## K4 · Açılma/kapanma zamanlaması deterministik ve enjekte edilebilir
**DEĞİŞMEZ:** İmleç sekme dikdörtgeninin içindeyken `acilma_ms` sonra açılır; dışındayken `kapanma_ms` sonra kapanır; içeri-dışarı titremesi zamanlayıcıları sıfırlar (içerideyken kapanma sayacı **durur**). Sürükleme sırasında kapanmaz. İmleç konumu **yapıcıya verilen** `imlec_konumu()` ile okunur (varsayılan `QCursor.pos`) — enter/leave olaylarına **güvenilmez** (üst-katman pencerelerde düzensiz, U3). Yoklama `yoklama_ms`.
**ÖLÇÜ (pytest-qt, sahte imleç):** imleç içeri → `qtbot.waitUntil(acik)` ≤ `acilma_ms + 2*yoklama_ms`; dışarı → kapanır ≤ `kapanma_ms + 2*yoklama_ms`; içeri-dışarı-içeri (100 ms) → **açık kalır**; sürükleme sırasında dışarı → açılmaz/kapanmaz; `hide()` sonrası yoklama sinyal üretmez.

## K5 · Tepsi: yoksa kullanıcı kilitlenmez
**DEĞİŞMEZ:** `QSystemTrayIcon.isSystemTrayAvailable()` yanlışsa `tepsiye_al()` **kenara al**'a düşer ve `durum == "kenar"` olur (pencere asla ulaşılamaz olmaz). Tepsi menüsü: "Pencereyi göster", "Kenara al", ayırıcı, "Çıkış". İkona tek/çift tık → `goster()`. Tepsi yoksa `Tepsi.gorunur()` daima `False`.
**ÖLÇÜ:** `tepsi_var` enjekte edilebilir (`Tepsi(..., kullanilabilir: bool | None = None)`); iki dal test; menü eylem adları; `activated(Trigger)` → `gorunur`.

## K6 · Modal yok, metin yok, blok yok
**DEĞİŞMEZ:** `src/ui` **hiçbir yerde** `QMessageBox`, `QDialog.exec`, `QInputDialog`, `QFileDialog` kullanmaz (tasarım A7); `print`/`logging`/`warnings` yok; `time.sleep`/`processEvents` yok (UI thread bloklanmaz). Sekmenin `paintEvent`'i + geometri hesabı tek karede **≤ 16 ms** (bütçe; offscreen'de ölçülür, gerçek ekranda `real_check`).
**ÖLÇÜ:** AST testi (T-008 deseni; pozitif kontrol: `QSystemTrayIcon.showMessage` **serbest** — modal değil); 100 `paintEvent` medyanı.

## K7 · Kabuk bağımsız: pipeline bilmez
**DEĞİŞMEZ:** `src/ui` `src.capture`, `src.ocr`, `src.translate`'i **import etmez**; iki mod düğmesi ve sekme düğmeleri **aynı** sinyalleri yayar (`anlik_cevir_istendi`, `bolge_izle_istendi`); kabuk sinyal dinleyicisi olmadan da çalışır.
**ÖLÇÜ:** AST import testi; `qtbot.waitSignal` ile pencere düğmesi ve sekme düğmesi aynı sinyali yayar; dinleyicisiz tıklama hata vermez.

## K8 · Çerçevesiz pencere sürüklenebilir, düğmeler erişilebilir
**DEĞİŞMEZ:** Başlık şeridinden (üst 44 px) sürükleme pencereyi taşır; düğme alanında sürükleme başlamaz. Düğmelerin `toolTip`'i ve `accessibleName`'i dolu (ekran okuyucu + test).
**ÖLÇÜ:** `qtbot.mousePress/Move/Release` ile taşıma; düğme üzerinde basınca taşınmaz; üç düğmenin `accessibleName` ∈ {"Kapat","Tepsiye al","Kenara al"}.

---

# Kabul kapısı — `real_check.py` (şefe ait; koş, yazma)
Gerçek ekran (`olcum_kabuk.py`'nin ürünleşmiş hâli): U1 tepsi var · U2 kapalı sekme `(right==ekran.right, dikey orta)` · U3 açılma ≤ `acilma_ms + 2*yoklama_ms + 50`, kapanma ≤ `kapanma_ms + 2*yoklama_ms + 50` · U5 aktif pencere None · U6 sürükleme sınırı · U4 sağ tık → görünür · tepsiye al → pencere gizli, ikon var · kapat → görünür üst-düzey 0, ikon yok · `paintEvent` 100 kare medyan < 16 ms · ekran görüntüleri temsili arka planda.

# Teslim
`delivery.md`; K1–K8 docstring + `known_gaps`. **Ölçümün paketle çelişirse ölçümüne uy, yaz.** Model/sağlayıcı/araç adı yazma; delillerde mutlak yol yok. `tests/unit/ui/conftest.py` şefe ait (`QT_QPA_PLATFORM=offscreen` ayarı) — dokunma.
