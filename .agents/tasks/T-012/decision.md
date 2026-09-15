---
task: T-012
role: sef
round: 3
decision: kabul
---

# T-012 — UI kabuğu (üç düğme · tepsi · kenar sekmesi): KABUL

Üç tur. Görev kapandı. **Projenin ilk ürün arayüzü**; kullanıcının 11 Eylül isteği ("sağ üstte üç düğme: kapat, arka planda çalıştır, kenara al — yarım daire, imleçle iki çeviri seçeneği") birebir.

## Ne teslim edildi

`src/ui/` — `geometri.py` (saf: kapalı/açık dikdörtgen, `y_sinirla`, disk içi testi, `Kenar` sağ/sol), `kenar_sekmesi.py` (`KenarSekmesi`: yarım daire + panel; yoklama tabanlı, imleç enjekte; sürüklemede açılmaz; mod tıkı önce paneli kapatır, imleç diskten çıkana kadar yeniden açılmaz; yalnız görünürken yoklar; `kapandi`), `kabuk.py` (`AnaPencere`: üç durumlu makine `gorunur (T,F,F) · tepsi (F,F,T) · kenar (F,T,T)`, `closeEvent == kapat`, `kapat` idempotent + `cikis_istendi` tam bir kez, tepsi yoksa kenara düşer, süreç başına bir kez balon, ömür: `destroyed → sekme/menü deleteLater`; `Tepsi`), `uygulama.py` + `__main__.py` (`python -m src.ui`, `setQuitOnLastWindowClosed(False)` sahibi). **220 test**, kapsam %99.6, mypy --strict modül+test, cp1254, mutant 44/44. Kör tester A (durum makinesi + sınır + ömür) **378** + B (kötü kullanım + istek uyumu + test kalitesi) **142 koşum**. `demo/kabuk.py` ürün kabuğunu kullanır; Bölge izle gerçek T-005 seçim katmanına bağlı.

**Gerçek ekran (`real_check` v3, şef koşumu 18/18):** sabitler ürün değerleri · üçlü tablo · sekme sağ kenara bitişik `(2534,670,26,52)`, dikey orta · bayraklar · **gerçek OS tıkı:** sekmeye ve panel düğmesine tık → ön plan sahnede kalıyor (pozitif kontrol: bayraksız pencere ön planı alıyor — `k5b_pozitif_kontrol_sef.txt`) · açılma 176 ms, kapanma 487 ms · yukarı sürükleme üst sınıra kilitleniyor, panel açılmıyor · sağ tık → pencere · WM_CLOSE → `cikis_istendi` 1, üçlü (F,F,F) · paint 0.19/0.19 ms · 2. monitör dpr 1.25 fiziksel +1 px (rapor).

## Tur kaydı

| Tur | Ne oldu |
|---|---|
| ölçüm | U0–U6 prototip (`demo/kabuk.py`): tepsi var, bitişik/orta, odak çalınmıyor, 129–153 / 476–478 ms |
| paket | v1 → **tek** KRT: 3 yüksek (Alt+F4 → zombi süreç; sürüklerken panel açılıyor; odak ölçüsü iki tarafta yanlış — ayrışan tek ölçü gerçek OS tıkı) + 9 orta → v2 |
| 1 | Implementer: 190 test, kapı 18/18 (tek ihlalin sebebi Windows bildirim balonu — ölçtü). **A ret** (sekme lambda bağlantılarıyla hiç toplanmıyor → zombi yarım daire) · **B onay** (yüksek bulgusu şefin demosunda: Esc uygulamayı kapatıyordu) → v3 |
| 2 | Ömür (bağlı yöntem), `kapandi`, mod tıkı mandalı, bir kez balon, üst sınırlar. **A onay · B onay**; iki orta: `deleteLater`+tutulan referans zombisi, panel açıkken `close` sonrası bayat geometri |
| 3 (dar) | `destroyed → deleteLater`, `showEvent → konumlan`, balona tık → göster. Şef tester sondalarını koştu: temiz. Kapı 18/18 (kilit açılınca) |

## Kalite kanıtı

**İmplementer'a giden kod hatası: 2 sınıf, ikisi de ömür** (Y-A1 lambda; O-B5 deleteLater) — ikisi de ölçülmemiş "Python sahipliği" varsayımından; geri kalan bulguların tamamı paket/kapı/demo kaynaklı. Implementer üç turda üç ölçülü teşhis getirdi (balon 6 s; `close` sonrası gecikmiş geometri olayı; `weakref` sarmalayıcı `__dict__`) — hepsi haklı.

Şefin ölçülmüş hataları (12):

| # | Hata | Yakalayan |
|---|---|---|
| 1 | K1'de `close()`/Alt+F4 yoktu → zombi süreç; giriş noktası sahipsizdi | KRT |
| 2 | K4 ölçüsü sürükleme jestine hiç uğramıyordu (panel açılıyordu) | KRT |
| 3 | Odak ölçüsü offscreen'de doğru kodda düşüyor, gerçek ekranda yanlış kodda geçiyordu | KRT |
| 4 | Kapı referansları uygulamadan türetiliyordu (sabitler); K4 üst sınırı CI yükünde titriyordu | KRT |
| 5 | İstek maddeleri sessizce düşmüştü (monitörler arası taşıma, kısayollar, kenar seçimi, sağ tık keşfedilebilirliği) | KRT |
| 6 | Paketteki 193/469 ms ham dosyada yoktu | KRT |
| 7 | Ömür cümlesi ölçülmeden yazıldı; kapı/ölçü bu sınıfa uğramıyordu | Tester-A |
| 8 | Demo `SecimKatmani` Esc → `quit()` ürün kabuğunu kapatıyordu | Tester-B |
| 9 | Tur-1 [5c] düzeltmesi (balonu kaldır) kullanıcı ipucunu yok etti; doğru olan kapının balon alanından uzak ölçmesiydi | Tester-B |
| 10 | [3] pozitif kontrolü KRT'ye bırakıldı, şef geç koştu | Tester-B |
| 11 | Kapı [8] ikinci monitör referansı yanlış formüldü (Qt'den) → Win32 `GetMonitorInfo` | şef |
| 12 | Seçim sırasında sekme paneli seçim katmanının üstüne çıkıyordu (demo) | Tester-B |

## Açık kalemler

| Kalem | Not | Sahip |
|---|---|---|
| **Global kısayollar** (`Ctrl+Alt+T/R`, tepside de çalışır) | paket dışı; `RegisterHotKey` + çakışma | yeni görev (HotkeyService) |
| **Anlık çeviri (Snapshot) modu** | kabuk sinyali hazır, alıcı yok | yeni görev |
| Yatay / monitörler arası sekme taşıma | farklı dpr monitörler arasında 512 px mantıksal boşluk ölçüldü — T-003 gerekir | v2 |
| Topmost / exclusive fullscreen oyun üstünde sekme görünmez | `[ÖLÇÜLMÜYOR]`; tasarım 5.6 "borderless'a geç" uyarısı | belge |
| Görev çubuğu sağda/solda → sekme fiziksel kenara bitişik değil (`availableGeometry` kararı) | `[ÖLÇÜLMÜYOR]` | belge |
| Monitör çıkarılması (`QScreen` silinir) | `[ÖLÇÜLMÜYOR]`; birincile taşıma | v2 |
| dpr ≠ 1 monitörde fiziksel +1 px taşma | rapor; tık birincile gitmiyor mu — ölçülmedi | kayıt |
| T-011 K5 süre testi yük altında titriyor (`test_k5_sure_8000_*` 60–65 ms > 60) | üç ajan gördü; eşik koşula bağlansın | T-011 bakım |
| Demo: Esc `_basla` sıfırlamıyor (D-B10), `IzlemePenceresi.close()` zamanlayıcı sürüyor (D-B11) | şef | demo |
| `yoklama_ms` küçükken CPU; balon bildirimler kapalıyken sessiz | `[ÖLÇÜLMÜYOR]` | belge |

## Karar

**T-012 KABUL.** İki tester onayı (tur 2) + tur 3 düzeltmeleri şef tarafından tester sondalarıyla doğrulandı, altı kabul komutu exit 0, gerçek ekran kapısı 18/18 (gerçek OS girdisi), tam takım **2117** test yeşil, `python demo/kabuk.py` ve `python -m src.ui` çalışıyor.
