---
task: T-016
role: sef
round: 1
decision: kabul
---

# T-016 — Ayarlar (dil · kısayollar · sözlük dosyası · kenar · açılış durumu): KABUL

Kullanıcı artık komut satırı argümanı yerine ⚙ düğmesiyle ayar değiştiriyor; ayarlar `%APPDATA%\Suflor\ayarlar.json`'da (insan okunur JSON, atomik yazma). Modal dialog yok (tasarım A7): panel `Tool` penceresi, dosya seçici non-modal `open()`.

- `src/ayarlar/model.py` — `Ayarlar` (dondurulmuş dataclass, `dogrula()` alan adıyla sorun listesi: dil, kısayol dilbilgisi + iki kısayol farklı, kenar, açılış, sözlük yolu), `AyarlarDeposu.yukle()` **asla istisna atmaz** (dosya yok → varsayılan; bozuk JSON → varsayılan + "json"; bilinmeyen alan yok sayılır; hatalı bilinen alan varsayılana + sorun), `kaydet()` doğrular + geçici dosya + `os.replace`. 21 test.
- `src/ui/ayarlar_paneli.py` — canlı doğrulama (Kaydet yalnız geçerliyken; ilk sorun durum satırında; `Ctrl+Alt+<tuş>` için **AltGr uyarısı** — TR-Q'da `Ctrl+Alt+T` = ₺), Enter kaydet / Esc vazgeç, `kaydedildi(Ayarlar)` tam bir kez. 8 test (AST: exec/QMessageBox/QDialog yok).
- `uygulama.calistir(ayarlar_deposu=…)` — yükleme sorunları durum satırında; kenar/kısayollar/açılış durumu ayarlardan; ⚙ → panel; kaydedince **canlı**: kısayollar yeniden kaydedilir (eskiler kaldırılır), sekme kenarı değişir, etiketler güncellenir, `pencere.ayarlar_degisti` yayılır. `demo/kabuk.py`: dil/sözlük değişince motorlar arka planda yeniden yüklenir. 4 test.

**Ölçülen tuzak (kayıt):** `_AyarKontrolu(QObject)` pencereye ebeveynli çocuk iken pencereye **güçlü Python referansı** tutuyordu → çocuk→ebeveyn Python referansı + ebeveyn→çocuk C++ sahipliği çapraz döngüsü; GC pencereyi toplarken çocuğun öznitelikleri boşaltılırken **yığın bozulması** (`0xC0000374`, yalnız pipeline+ui testleri birlikte, nondeterministik). Çözüm: `parent()` üzerinden erişim. T-012 Y-A1 / T-013 Y3 ile aynı aile: PySide'da ebeveyn-çocuk arasında Python referansı tutma.

Tam takım **2380** (×2), mypy --strict temiz. Sınır: kısayol alanı serbest metin (tuş yakalama editörü v2); sözlük dosyası doğrulaması yükleme anında (`GlossaryStore` şema hatası durum satırında).
