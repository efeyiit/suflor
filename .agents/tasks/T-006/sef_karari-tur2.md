# Şef Kararı — T-006, Tur 2

Tester turu 1: **A onay · B ret.** İkisinin her iddiası şef tarafından yeniden üretildi (`sef_dogrulama/sonda_tester_{A,B}.txt`).

B'nin ret'i **haklı ve kabul edildi.** Kusur ürün kodunda değil, **paketin K7 ölçüsünde** — implementer lafza birebir uymuş, lafız yanlışmış. Kod doğru: hiçbir kanala OCR metni yazmıyor (B gerçek modelle ayrı süreçte ölçtü: stdout 0 / stderr 0 bayt). Ama bunu **ölçen** yok.

## Şefin bu turda kabul ettiği iki kendi hatası

**[16] K7 ölçüsü mekanizmayı kancalıyordu (§4.6/7).** Paket "AST: `print` yok; `logging` argümanında `.text`/`txts` yok; `caplog` `RapidOCR` logger'ında" dedi. Üçü de **ad** kancası: `sys.stdout.write` `print` değil; döngü değişkeni `metin` `.text` değil; uygulama logger'ı `RapidOCR` değil. B'nin M25b/M28b/M28c mutantları beş kapıdan geçti; şef M25b'yi üretti (95 birim testi **geçiyor**). M25b üründe her dolu karede tetiklenir: cp1254 konsolda `UnicodeEncodeError`, pencereli pakette (`sys.stdout is None`) `AttributeError`. Kuralı iki görev önce ben yazdım; üçüncü kez aynı sınıfta hata.

**[17] `real_check` çıktısında `≈` (U+2248).** Paketin "Windows tuzakları" bölümü cp1254'ü **özellikle** uyarıyordu; şef `[6a]`'yı düzeltirken o karakteri **kendisi** ekledi. `PYTHONIOENCODING` yokken kapı exit 1 veriyordu — ve B'nin kiti bu yüzden 51 mutantın 51'ini "yakalandı" gösterebilirdi. Düzeltildi: stdout'a giden her özel işaret ASCII'ye çekildi, cp1254 altında koşuldu, TEMİZ.

---

## T2-1 · K7 ölçüsü davranışa kancalanır (BLOKE)

**DEĞİŞMEZ (K7'nin doğru okunuşu, kanal-bağımsız):** `recognize` çağrısı süresince OCR metni **hiçbir çıkış kanalına** yazılmaz — stdout, stderr, herhangi bir `logging` logger'ı (hangi ad, hangi seviye olursa olsun).

**ÖLÇÜ (Tester-B tarif etti, `feedback-B.md`; şef ayırt etme gücünü tur sonunda kendi ölçecek):** `tests/unit/ocr/test_rapid_engine.py`'ye:

1. **`capsys`:** nöbetçi metinli (`"NÖBETÇİ-7f3a"` ve ASCII-dışı bir nöbetçi daha, ör. `"長老-9c1e"`) sahte tanıyıcıyla `recognize` → `capsys.readouterr()` **out ve err boş** (`== ""`, "nöbetçi içermez" yetmez — sıfır bayt).
2. **`caplog` kök logger, DEBUG, propagate:** `caplog.set_level(logging.DEBUG)` (logger belirtmeden = kök) **ve** motorun kurabileceği her logger'ın `propagate`'i açık olacak şekilde; `recognize` sonrası `caplog.records`'un **hiçbirinin** `getMessage()`'ı iki nöbetçiyi de içermez. `RapidOCR` logger'ının `propagate=False` olması bu ölçüyü kör bırakır — test o logger'a bir `caplog.handler` **doğrudan** takar.
3. **AST kalır ama ikincil:** `print`, `sys.stdout.write`, `sys.stderr.write`, `os.write` — dördü de 0. (Davranış ölçüsü asıl kapı; AST erken uyarı.)

**Pozitif kontrol (§4.6/10):** aynı iki test, `recognizer_factory` yerine **test içinde** stdout'a nöbetçi yazan bir sahte motorla (engine'in kendisi değil, `OcrEngine`'i uygulayan 5 satırlık sınıf) koşulunca **düşmeli** — ölçünün ateşlediği gösterilir.

**Beklenen ayırt etme (B ölçtü; şef doğrulayacak):** M25b, M28b, M28c → yakalanır; 4 kontrol mutantı → kaçar.

## T2-2 · `close()` tanıyıcıyı bırakır (K10, ikincil — aynı turda)

**DEĞİŞMEZ:** `close()` sonrası motor tanıyıcıya referans tutmaz (gerçek yolda det+rec ONNX oturumları; dil değişiminde eski motor bellekte kalmasın).
**ÖLÇÜ:** Fabrikanın döndürdüğü tanıyıcıya `weakref.ref`; `close()` + `gc.collect()` sonrası `ref() is None`. Bu **bir satırlık** `src` değişikliği ister (`self._taniyici = None`); paket K10'un "kapatma" lafzı buna zaten izin veriyor, davranış değişmiyor (kapalı motorda `recognize` zaten `OcrError`).

## Kapsam — bu turda yapılmayacaklar

| Kalem | Neden |
|---|---|
| K1 paket metni conftest'le uyuşmuyor (nöbetçi+sayaç vs meta_path bulucu) | Belge; conftest doğru olan. Paket v3'e not, davranış değişmez. |
| Bariyer pozitif kontrolü yalnız `import_module` yolunu sınıyor | B dört yolu ölçtü, hepsi tutuyor; ek test şefin, ayrı. |
| `_varsayilan_fabrika` içindeki `isinstance` dalı ölçülmüyor | `[ÖLÇÜLMÜYOR]` damgası eklenir (docstring), davranış değişmez. |
| Uygulama `RapidOCR` logger'ını açarsa boş karede kütüphane WARNING'i düşer | Üst katman kararı (logging yapılandırması), motor değil. |
| A'nın bulguları: `lang_type` yalnız `allow_download=True` yolunda ölçülür; K9 "süre kutu sayısına bağlı" eksik; `dpi_scale` numpy asimetrisi | Hepsi decision.md açık kalemi; ürün doğru. |

## Neden karar kırmızı takımına gitmiyor

Yeni değişmez yok (K7 ve K10 zaten yazılı; değişen **ölçünün kancası**). Ölçüyü B kurdu ve ayırt etme gücünü ölçtü; şef üretti. `src` değişikliği tek satır ve davranış-nötr. §4.6/9.

## Kabul komutları (tur 2)

Beş komut aynı (`packet.md`). Beklenen: birim **95 + yeni testler**, tam takım **1085 + aynı sayı**, düşen yok. **Şefin ayrıca koşacağı:** `python .agents/tasks/T-006/tester_B/mutant_kiti.py` — M25b/M28b/M28c/M32 yakalanmalı, 4 kontrol kaçmalı.

## Tur 2 sonrası

Tester-B yeniden nişan alır. A yeniden koşmaz; şef A'nın takımını regresyon olarak koşar.
