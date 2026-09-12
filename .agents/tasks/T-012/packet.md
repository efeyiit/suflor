---
task: T-012
title: "UI kabuğu: ana pencere üç düğme (Kapat · Tepsiye al · Kenara al), sistem tepsisi, kenar sekmesi (yarım daire → Anlık çeviri / Bölge izle)"
role: implementer
level: B
wave: 3
packet_version: 2
owns:
  - "src/ui/__init__.py"
  - "src/ui/__main__.py"
  - "src/ui/uygulama.py"
  - "src/ui/kabuk.py"
  - "src/ui/kenar_sekmesi.py"
  - "src/ui/geometri.py"
  - "tests/unit/ui/test_kabuk.py"
  - "tests/unit/ui/test_kenar_sekmesi.py"
  - "tests/unit/ui/test_geometri.py"
  - "tests/unit/ui/test_uygulama.py"
  - ".agents/tasks/T-012/evidence/**"
  - ".agents/tasks/T-012/delivery.md"
forbidden:
  - "src/contracts/**"
  - "src/capture/**"
  - "src/ocr/**"
  - "src/translate/**"
  - "tests/unit/ui/conftest.py"
  - "tests/unit/ui/test_conftest_bariyer.py"
  - "demo/**"
  - ".agents/tasks/T-012/real_check.py"
  - ".agents/tasks/T-012/olcum_kabuk.py"
  - ".agents/tasks/T-012/krt_kosumlari/**"
  - "diğer tüm dizinler"
depends_on: ["T-001"]
acceptance:
  - "python -m mypy --strict --explicit-package-bases src/ui"
  - "python -m pytest tests/unit/ui -q"
  - "python .agents/tasks/T-012/real_check.py"
  - "python -m pytest tests/unit/ui -q --cov=src.ui --cov-fail-under=95 --cov-report=term-missing"
  - "python -m pytest tests -q"
budget_ms: 16   # kenar sekmesi paintEvent (açık ve kapalı) tek kare; boşta CPU ≤ %1 tek çekirdek (60 ms yoklama ölçüldü %0.3)
---

> **Paket sürümü 2.** v1 kırmızı takımdan **3 yüksek / 9 orta / 7 düşük** ile döndü (`krt-1.md`, ham ölçümler `krt_kosumlari/`); şef Y1 ve Y3'ü kendi eliyle üretti, Y2'yi kod okumasıyla doğruladı (`sef_dogrulama/krt1_sef_kosumlari.txt`). Değişiklikler **▲** ile işaretli. Üç yüksek: (Y1) `close()`/Alt+F4 durum makinesinde yoktu → **zombi süreç** (pencere, tepsi, sekme üçü gizli, ulaşılabilir yol yok); (Y2) sürükleme sırasında panel **açılıyor** ve kırpılmış görsel çöp bırakıyor — v1 ölçüsü bu sınıfa hiç uğramıyordu; (Y3) odak ölçüsü offscreen'de doğru kodda bile düşüyor, gerçek ekranda odak-çalan kodda bile geçiyor (Windows her `Tool` pencereyi `SHOWNOACTIVATE` gösterir) — ayrışan tek ölçü **gerçek OS tıkı**.
>
> **Kullanıcı isteği (11 Eylül 2026, `istek.md`):** sağ üstte üç düğme — kapat · arka planda çalıştır (tepsi) · kenara al (masaüstünde pencere yok, ekran kenarında küçük **yarım daire**; imleç gelince **iki** çeviri seçeneği). Şef `demo/kabuk.py` ile prototipledi, gerçek ekranda ölçtü (`olgular.txt` U0–U6; KRT iki kez tekrarladı, birebir): tepsi var; sekme sağ kenara bitişik, dikey ortada; **sekme gösterilince aktif pencere değişmiyor**; açılma **129–153 ms** (ayar 120 + 60 ms yoklama), kapanma **476–478 ms** (ayar 450) — ▲ v1'deki 193/469 ham dosyada yoktu, düzeltildi; sürükleme sınıra kilitleniyor; sağ tık pencereyi getiriyor ve ön plana alıyor; boşta 60 ms yoklama %0.3 tek çekirdek; sekmenin saydam köşesine tık oyuna geçiyor. Bu paket prototipi ürün bileşenine çevirir: saf geometri + test edilebilir durum makinesi + enjekte edilebilir imleç.

# Görev

`src/ui/` altında:

1. **`geometri.py`** — saf fonksiyonlar (Qt tipine bağımlı olabilir, **ekran/pencere yaratmaz**): `sekme_kapali_dikdortgeni(ekran: QRect, y: int, yaricap: int, kenar: Kenar) -> QRect`, `sekme_acik_dikdortgeni(ekran, y, yaricap, panel: QSize, kenar) -> QRect`, `y_sinirla(ekran, y, yaricap) -> int`, ▲ `sekme_icinde(dikdortgen: QRect, nokta: QPoint, yaricap: int, kenar: Kenar) -> bool` (**disk** testi: yarım dairenin merkezine uzaklık ≤ yaricap — saydam köşe "içeride" sayılmaz, KRT D1). `Kenar = StrEnum("sag", "sol")`.
2. **`kenar_sekmesi.py`** — `KenarSekmesi(QWidget)`: yarım daire + açılır panel; sinyaller `anlik_cevir`, `bolge_izle`, `pencereyi_goster`.
3. **`kabuk.py`** — `AnaPencere(QWidget)`: çerçevesiz, sağ üstte üç düğme, gövdede iki mod düğmesi; `Tepsi`; durum makinesi `KabukDurumu`; sinyaller `anlik_cevir_istendi`, `bolge_izle_istendi`, `cikis_istendi`. Kabuk **model/yakalama/OCR/çeviri bilmez** (K7).
4. ▲ **`uygulama.py` + `__main__.py`** — giriş noktası (KRT Y1: "uygulama karar verir" ama uygulama kimse değildi): `calistir(argv: Sequence[str] | None = None, *, kenar: Kenar = Kenar.SAG) -> int` — `QApplication`, **`setQuitOnLastWindowClosed(False)`**, `AnaPencere`, `cikis_istendi → app.quit`, `app.exec()`. `python -m src.ui` ile açılır; pipeline bağlamaz (o iş `demo/kabuk.py`'de şefindir ve bu modülü kullanır).

## Arayüz — kapının (`real_check.py`) ve tester'ların kullandığı adlar (bağlayıcı)

- `AnaPencere(ekran: QScreen | None = None, *, kenar: Kenar = Kenar.SAG, tepsi_kullanilabilir: bool | None = None, imlec_konumu: Callable[[], QPoint] | None = None)` (▲ `kenar` eklendi; `None` → `QGuiApplication.primaryScreen()` / `QCursor.pos`); özellikler `durum: KabukDurumu`, `sekme: KenarSekmesi`, `tepsi: Tepsi`, `dugme_kapat`, `dugme_tepsi`, `dugme_kenar`, `dugme_anlik`, `dugme_bolge` (QPushButton); yöntemler `goster()`, `tepsiye_al()`, `kenara_al()`, `kapat()`; sinyaller `anlik_cevir_istendi`, `bolge_izle_istendi`, `cikis_istendi`.
- `KabukDurumu(StrEnum)`: `GORUNUR="gorunur"`, `TEPSI="tepsi"`, `KENAR="kenar"`.
- `KenarSekmesi(ekran: QScreen, *, kenar=Kenar.SAG, yaricap=26, acilma_ms=120, kapanma_ms=450, yoklama_ms=60, imlec_konumu=None)`; salt-okunur `yaricap`, `acilma_ms`, `kapanma_ms`, `yoklama_ms`, `acik: bool`, `surukleniyor: bool`; okunur-yazılır `y: int` (sınırlanır), ▲ `kenar: Kenar` (değişince yeniden konumlanır); ▲ `dugme_anlik`, `dugme_bolge`, `dugme_goster` (paneldeki üç düğme); sinyaller `anlik_cevir`, `bolge_izle`, `pencereyi_goster`.
- `Tepsi(ikon: QIcon, ebeveyn: QObject | None, *, kullanilabilir: bool | None = None)`: `goster()`, `gizle()`, `gorunur() -> bool`, `bildir(baslik, metin, ms)`; sinyaller `goster_istendi`, `kenara_al_istendi`, `cikis_istendi`.
- `geometri.py`: `Kenar`, `sekme_kapali_dikdortgeni`, `sekme_acik_dikdortgeni`, `y_sinirla`, `sekme_icinde`, `PANEL_BOYUTU: Final[QSize] = QSize(200, 132)`.
- ▲ Varsayılan sabitler **ürün değerleridir** ve kapı bunları **ön koşul** olarak sorar (KRT O1, §4.6/8): `yaricap=26`, `acilma_ms=120`, `kapanma_ms=450`, `yoklama_ms=60`, `PANEL_BOYUTU=(200,132)`. Değiştirmek isteyen paket sürümünü değiştirir.

---

# Değişmezler

## K1 · Durum makinesi: üç durum, her geçiş tanımlı, ulaşılamayan durum yok (▲ Y1, O6)
**DEĞİŞMEZ:** Durum üçlüsü (pencere görünür, sekme görünür, tepsi ikonu görünür): ▲ **`gorunur` (T,F,F) · `tepsi` (F,F,T) · `kenar` (F,T,T)** — başka üçlü **yok**; `goster()` tepsi ikonunu da gizler. Geçişler: `gorunur ⇄ tepsi`, `gorunur ⇄ kenar`, `tepsi → kenar` (tepsi menüsü); `kenar → tepsi` yok. Her durumda geri dönüş yolu: `tepsi` → ikona tık / menü "Pencereyi göster"; `kenar` → sağ tık / paneldeki `dugme_goster` / tepsi ikonu. ▲ **`closeEvent` (Alt+F4, WM_CLOSE) `gorunur` durumunda `kapat()` ile eşdeğerdir** — `ignore()` edilmez; "pencere gizli + ikon gizli + sekme gizli" durumu **ulaşılamaz**. ▲ **`kapat()` idempotent:** her durumdan pencere + sekme + tepsi ikonu kapanır, yoklayıcı durur, `cikis_istendi` **tam bir kez** (ikinci çağrı / `close()` sonrası `closeEvent` zinciri ikinci sinyal üretmez). Kabuk `QApplication.quit()` **çağırmaz**; `uygulama.calistir` bağlar.
**ÖLÇÜ (pytest-qt, offscreen):** her geçiş bir test; geçiş sonrası `durum` + üçlü tablo ile (▲ `gorunur`a hangi yoldan gelinirse gelinsin (T,F,F)); `kapat()` sonrası görünür üst-düzey **0**, `tepsi.gorunur() is False`, `cikis_istendi` == 1; ▲ `kapat(); kapat()` → 1; ▲ `p.close()` → üçlü (F,F,F) + `cikis_istendi` == 1; `tepsiye_al()` ×2 idempotent. ▲ Test fixture'ı teardown'da `kapat()` çağırır (sekme ebeveynsiz `Tool` pencere; sıraya bağlı "görünür üst-düzey" kirliliği — KRT O6).

## K2 · Geometri saf ve ekran-bağımsız; kenara bitişik, sınırlar içinde (▲ O5, O7, D1, D5)
**DEĞİŞMEZ:** Kapalı dikdörtgen: `kenar=sag` → `x = ekran.right() - yaricap + 1`, `w = yaricap`, `h = 2*yaricap`; `sol` → `x = ekran.left()`. Açık dikdörtgen: panel kenara bitişik, `y` sekmenin dikey merkezine hizalı, `ekran` içine sıkıştırılmış. `y_sinirla`: `[ekran.top(), ekran.bottom() - 2*yaricap + 1]`. `ekran` = **`QScreen.availableGeometry()`** (▲ karar: görev çubuğuyla çakışmaz; çubuk sağda/solda ise sekme fiziksel kenara bitişik **değildir** — `known_gaps`, KRT O7). Mantıksal piksel; negatif koordinatlı monitör destek. ▲ `sekme_icinde`: kapalı hâlde **disk** (merkez kenar üzerinde, yarıçap `yaricap`); açık hâlde panel dikdörtgeni. ▲ `sol` kenarda yarım daire **aynalı** çizilir (opak yarı ekranın iç tarafında). ▲ `QScreen.availableGeometryChanged` bağlanır: görev çubuğu taşınınca sekme yeniden konumlanır. Monitör çıkarılması (`screenRemoved`) **`[ÖLÇÜLMÜYOR]`** — bilinen sınır: verilen `QScreen` silinirse `RuntimeError`; `known_gaps` + birincile taşıma sonraki sürüm. DPI ≠ 1.0: geometri mantıksal pikselde doğrudur; fiziksel kenar yuvarlaması (KRT G4: 1 px taşma) **`[ÖLÇÜLMÜYOR birim]`**, `real_check` ikinci monitörde ±1 px ile ölçer.
**ÖLÇÜ (saf, ekran yok):** 3 ekran dikdörtgeni (`0,0,2560,1392` · `-2560,0,2560,1440` · `-2560,0,2048,1152` dpr 1.25 mantıksal) × 2 kenar × 5 `y` → kapalı/açık `ekran.contains()` her zaman; kapalı `right()==ekran.right()` (sağ) / `left()==ekran.left()` (sol); açık panel kenara bitişik ve **sekme dikdörtgenini kapsar**; `y_sinirla` monoton; U2 birebir `(2534,670,26,52)`. ▲ `sekme_icinde`: merkez → True, köşe `(0,0)` → **False**, panel açıkken köşe → True. ▲ `sol` kenar `grab()`: sol yarı opak, sağ yarı saydam; `sag` tersi. ▲ `availableGeometryChanged` sahte sinyalle → yeni `x`.

## K3 · Odak ve girdi: sekme odak almaz, oyunun girdisini yutmaz (▲ Y3, O4)
**DEĞİŞMEZ:** `KenarSekmesi` bayrakları `FramelessWindowHint | Tool | WindowStaysOnTopHint | WindowDoesNotAcceptFocus`, `WA_TranslucentBackground`, `WA_ShowWithoutActivating`. Pencere yalnız sekme/panel kadar (tam ekran katman yok): dışındaki her tık oyuna gider — yapısal. ▲ `_ac()` içinde `raise_()` (yoklamada değil). ▲ **`[ÖLÇÜLMÜYOR]`: topmost (borderless-topmost) ve exclusive fullscreen oyun üstünde sekme görünmez** (KRT k5 Z2: `StaysOnTop` oyun sekmeden sonra gösterilince üstte kalır); tasarım dokümanı 5.6 "borderless'a geç" uyarısı — `known_gaps`.
**ÖLÇÜ:** bayrak/öznitelik testi (**yapısal**, davranış değil); ▲ `activeWindow()` offscreen'de **`[ÖLÇÜLMÜYOR]`** (platform bayrakları uygulamaz — KRT k2b: doğru kodda bile sekme aktif görünür; v1 "None kalır" cümlesi yanlıştı); gerçek davranış yalnız `real_check` **gerçek OS tıkı** ile (sahne ön plandayken sekmeye ve panel düğmesine `mouse_event` sol tık → `GetForegroundWindow` değişmez, düğme sinyali 1; pozitif kontrol: bayraksız pencere ön planı alır — şef `sef_dogrulama/`'ya bir kez yazar). Kapalı/açık `frameGeometry` boyutları `(yaricap, 2*yaricap)` / `PANEL_BOYUTU`.

## K4 · Açılma/kapanma zamanlaması deterministik ve enjekte edilebilir (▲ Y2, O2, O9, D3, D4)
**DEĞİŞMEZ:** İmleç `sekme_icinde` iken `acilma_ms` sonra açılır; dışındayken `kapanma_ms` sonra kapanır; içeri-dışarı titremesi sayaçları sıfırlar (içerideyken kapanma sayacı durur). ▲ **Sürükleme (sol düğme basılı) sırasında açılma sayacı başlamaz ve çalışıyorsa durur; `acik` sürükleme boyunca değişmez** (KRT Y2: prototipte panel açılıp kırpılıyordu); bırakıldığında imleç içerideyse sayaç **sıfırdan** başlar. ▲ **Mod sinyali (`anlik_cevir`/`bolge_izle`) yayılmadan önce panel kapanır** (kapalı geometri uygulanır) — Snapshot karesine panel metni girmesin (KRT O9). İmleç konumu **yalnız** yapıcıya verilen `imlec_konumu()` ile okunur (enter/leave'e güvenilmez). ▲ **Yoklayıcı yalnız sekme görünürken çalışır** (`hide()` → durur; boşta CPU ≤ %1). Örnekleme fazı belirsizliği ≤ 1 yoklama (hızlı 50/50 ms titremede tek tük açılma olabilir — belge).
**ÖLÇÜ (pytest-qt, sahte imleç — çağrı sayan callable):** içeri → `qtbot.waitUntil(lambda: s.acik, timeout=acilma_ms + 2*yoklama_ms + 300)` (▲ gevşek üst sınır: CI yükünde 11/30 titredi) **ve** deterministik alt sınır: `qtbot.wait(acilma_ms // 2)` sonra `acik is False`; dışarı → kapanır (`kapanma_ms + 2*yoklama_ms + 300`) ve `qtbot.wait(kapanma_ms // 2)` sonra hâlâ açık; içeri-dışarı-içeri (100 ms) → açık kalır; ▲ `qtbot.mousePress` + imleç içeride + `qtbot.wait(acilma_ms + 3*yoklama_ms)` → `acik is False`, `surukleniyor is True`; `mouseRelease` → `waitUntil(acik)`; ▲ `dugme_anlik.click()` → `waitSignal(anlik_cevir)` sonrası `acik is False` ve boyut `(yaricap, 2*yaricap)`; ▲ enjekte callable `show()` sonrası çağrı sayısı artar, `hide()` sonrası **artmaz**. Sıkı sayılar yalnız `real_check`'te.

## K5 · Tepsi: yoksa kullanıcı kilitlenmez
**DEĞİŞMEZ:** `isSystemTrayAvailable()` yanlışsa (ya da `kullanilabilir=False`) `tepsiye_al()` **kenara al**'a düşer, `durum == "kenar"`. Menü: "Pencereyi göster", "Kenara al", ayırıcı, "Çıkış". İkona tek/çift tık → `goster()`. Tepsi yoksa `gorunur()` daima `False` (offscreen'de `QSystemTrayIcon.show()` `isVisible()=True` döner — ölçü ateşleyebilir, KRT). `bildir` bildirimler kapalıyken sessiz **`[ÖLÇÜLMÜYOR]`**; ikona tık sonrası ön plana gelme gerçek ekranda `real_check` (KRT: sağ tıkta foreground kilidine takılmadı).
**ÖLÇÜ:** iki dal (`kullanilabilir=True/False`); menü eylem adları; `activated(Trigger)` → `gorunur`; tepsi yokken `tepsiye_al()` → `kenar` üçlüsü (F,T,F) — ▲ dikkat: bu üçlü K1 tablosunun **istisnasıdır**, K1 tablosuna satır olarak eklenir (`kenar (tepsi yok)` = (F,T,F)).

## K6 · Modal yok, metin yok, blok yok
**DEĞİŞMEZ:** `src/ui` `QMessageBox`, `QDialog.exec`, `QInputDialog`, `QFileDialog` kullanmaz; `print`/`logging`/`warnings` yok; `time.sleep`/`processEvents` yok (`uygulama.calistir` hariç: `app.exec()`). `paintEvent` **kapalı ve açık** hâlde ≤ 16 ms (ölçüldü 0.24 / 0.83 ms gerçek ekran).
**ÖLÇÜ:** AST testi (pozitif kontrol: `QSystemTrayIcon.showMessage` serbest); 100 kare medyanı iki hâlde.

## K7 · Kabuk bağımsız: pipeline bilmez (▲ O3)
**DEĞİŞMEZ:** `src/ui` `src.capture`, `src.ocr`, `src.translate`'i import etmez; pencere düğmeleri ve sekme düğmeleri aynı sinyalleri yayar; dinleyicisiz çalışır. ▲ `depends_on`'dan T-003 çıkarıldı: yatay/monitörler arası taşıma **v2** (`known_gaps`; farklı dpr'li monitörler arasında 512 px mantıksal boşluk ölçüldü — T-003 gerekir). ▲ Global kısayollar (`Ctrl+Alt+T/R`) bu paketin **dışında** — HotkeyService ayrı görev (`known_gaps`).
**ÖLÇÜ:** AST import testi; `waitSignal` ile pencere düğmesi ve sekme düğmesi aynı sinyal; dinleyicisiz tıklama hata vermez.

## K8 · Çerçevesiz pencere sürüklenebilir, düğmeler erişilebilir (▲ O3d)
**DEĞİŞMEZ:** Başlık şeridinden (üst 44 px) sürükleme taşır; düğme alanında başlamaz. Üç düğmenin `toolTip` ve `accessibleName` dolu. ▲ Sekmenin `toolTip`'i "Sağ tık: pencereyi göster" içerir; panelde `dugme_goster` (küçük, başlık satırında) `pencereyi_goster` yayar — sağ tık keşfedilebilir olmalı.
**ÖLÇÜ:** `qtbot.mousePress/Move/Release` ile taşıma; düğme üzerinde basınca taşınmaz; `accessibleName` ∈ {"Kapat","Tepsiye al","Kenara al"}; ▲ `sekme.toolTip() != ""`, `dugme_goster.click()` → `pencereyi_goster`.

---

# Kabul kapısı — `real_check.py` v2 (şefe ait; koş, yazma)
Gerçek ekran. ▲ **Ön koşul:** sabitler ürün değerleri (26/120/450/60, panel 200×132) — değilse kapı durur. (1) tepsiye al → (F,F,T), göster → (T,F,F); (2) kenara al → (F,T,T), kapalı sekme sağ kenara bitişik, dikey orta, bayraklar; (3) ▲ **gerçek OS tıkı**: sahne ön plandayken sekmeye tık → ön plan sahne, panel düğmesine tık → `clicked` 1 ve ön plan sahne; (4) açılma ≤ 120+2·60+150, kapanma ≤ 450+2·60+150; (5) sürükleme sınıra kilitlenir ▲ ve sürükleme sonrası (imleç sekmede bırakılarak) `acik is False`; sağ tık → görünür; (6) ▲ `PostMessage(WM_CLOSE)` → `cikis_istendi` == 1, üçlü (F,F,F); `kapat()` ikinci çağrı sinyal üretmez; (7) paint 100 kare medyan < 16 ms **açık ve kapalı**; (8) ▲ ikinci monitör varsa `AnaPencere(ekran=screens()[1])` → `GetWindowRect` fiziksel sağ kenar == o monitörün fiziksel sağ kenarı ±1 px; (9) ▲ mod düğmesi tıkı → panel kapalı. Ekran görüntüleri temsili arka planda.

# Teslim
`delivery.md`; K1–K8 docstring + `known_gaps` (▲ v2 kalemleri: yatay taşıma, kısayollar, topmost oyun, monitör çıkarma, görev çubuğu sağda/solda, bildirim kapalı). **Ölçümün paketle çelişirse ölçümüne uy, yaz.** Model/sağlayıcı/araç adı yazma; delillerde mutlak yol yok. `tests/unit/ui/conftest.py` şefe ait — dokunma.
