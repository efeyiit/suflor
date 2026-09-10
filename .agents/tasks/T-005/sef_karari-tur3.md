# Şef Kararı — T-005, Tur 3

Tester-D tur 2'de **yine ret** verdi, iki bloke bulguyla. **İkisini de şef kendi eliyle yeniden üretti** (`sef_dogrulama/sonda_tester_D_tur2.txt`). İkisi de haklı.

Bu turun farkı: **tekil varyantı yamamıyoruz, ekseni kapatıyoruz.**

## Neden kilitlenme değil (PROTOKOL §7 notu)

§7, 3. turda tester hâlâ ret verirse Hakem'i çağırmayı söyler. Hakem'in işi **kimin haklı olduğunu** ayırt etmektir. Burada ayırt edilecek bir anlaşmazlık yok:

- **Implementer** diyor ki: uygulama doğru.
- **Tester-D** diyor ki: *"Uygulama DOĞRU — kusur kapıda. Bu bir kod düzeltmesi değil, bir ölçü düzeltmesidir."*
- **Şef** ölçtü ve ikisini de doğruladı.

Üçü de aynı şeyi söylüyor. Her tur, **aynı değişmezin ölçülmemiş başka bir yarısını** buldu — bu yakınsamama değil, derinleşme. Hakem bu turda yeni bir bilgi üretmez; üreteceği tek şey gecikmedir. **Hakem çağrılmıyor, gerekçesi bu.** Tur 3 de ret gelirse Hakem çağrılır ve o zaman sorulacak soru "kim haklı" değil, **"şefin kapı tasarımı bu görev için yeterli mi"** olur.

---

## T3-1 · `__exit__` ölçüsü ÇIKIŞ YOLU ekseninde tek noktada (BLOKE)

**BULAN:** Tester-D (D2-1). **ŞEF ÜRETTİ:** M53 — `__exit__`'i yalnız `exc_type is None` iken kapatan uygulama **beş kabul komutundan da tabanla aynı çıktıyla geçiyor** (mypy exit 0 · sahipli 163 · headless TEMİZ · capture 746 · tam takım 985).

**Gerçek zarar, gerçek ekranda ölçüldü:**

```
with MssBackend() as b:
    b.grab(rect)
    raise CaptureError(...)        # K6 sınıf b/c — ürünün NORMAL hata yolu
```
→ çıkıştan sonra `_tutamac = <mss.base.MSS object>` **açık kaldı**. Taban aynı dizide kapatıyor.

Bu istisnai bir senaryo değil: K6 sınıf (b) backend istisnası ve sınıf (c) geçersiz çıktı **tanımlı** hata sınıflarıdır. `mss`'te `__del__` yok; her hatalı yakalama bir window DC sızdırır ve 5001. kapatılmamış örnekte `GetWindowDC` **kalıcı** düşer.

### Yamamıyoruz — ekseni kapatıyoruz

Tur 1'de bu değişmez **hiç** ölçülmüyordu. Tur 2'de **bir** noktada ölçülür oldu. Üçüncü bir varyantın gelmemesi için ölçünün **ekseni** kapatması gerekir.

**ŞEFİN YAPISAL ÖLÇÜMÜ** — Python'da `with` bloğundan çıkış yolları ve `__exit__`'in gördüğü `exc_type`:

| çıkış yolu | `exc_type` |
|---|---|
| normal düşüş | `None` |
| `return` | `None` |
| `break` | `None` |
| `continue` | `None` |
| gövdede istisna | `ValueError` (vb.) |
| `generator.close()` | `GeneratorExit` |

**Eksenin ayrık sınıf sayısı = 2.** `return`/`break`/`continue` birinci sınıfa, `generator.close()` ikinciye çöküyor. **Üçüncü bir varyant yok** — ikisini de koşan bir ölçü ekseni **tamamen** kapatır.

**DEĞİŞMEZ (K10'un koşulsuz okunuşu, yeni değil):** `MssBackend.__exit__`, `with` bloğundan **hangi yolla çıkılırsa çıkılsın** `close()` çağırır. `__exit__` istisnayı **yutmaz** (`return` değeri yanlış/`True` olmamalı).

**ÖLÇÜ:** `tests/unit/capture/test_service.py` — mevcut `test_k10_exit_uzun_omurlu_tutamaci_kapatir` testi **`exc_type` ekseni üzerinde parametrize edilir**; iki parametre: *temiz çıkış* ve *istisnalı çıkış*. Tester-D'nin `feedback-D.md`'deki hazır kodu istisna bacağını veriyor; iki bacağı tek parametrik testte birleştirmek de serbesttir — **bağlayıcı olan iki sınıfın da koşulmasıdır**, testin biçimi değil.

Ek olarak `__exit__`'in **istisnayı yutmadığı** assert edilir (bir `with` bloğunda yükseltilen `CaptureError` çağırana ulaşmalı) — bu, "istisnayı yutup sessizce kapat" varyantını kapatır.

**Tester-D'nin ölçtüğü ayırt etme gücü (şef tur 3 sonunda kendi doğrulayacak):** taban `164 passed`, M53 `1 failed`, M12/M50 `2 failed`.

---

## T3-2 · Docstring'in olumsuz iddiası YANLIŞ (BLOKE)

**BULAN:** Tester-D (D2-3). **ŞEF ÜRETTİ.**

`capture_region` docstring'i tur 2'de şunu kazandı:

> *"Kenardan uzak (derin INSIDE) bölgelerde ise dört tipte de ayrışma **sıfırdır** — taşma yalnızca monitör sınırlarına yaklaşan bölgelerde gözlemlenebilir hale gelir."*

**KARŞI ÖRNEK (şef ölçtü):** `Rect(1000, 600, 1000, 200)`, `M1=(0,0,2560,1440)` içinde — kenarlara uzaklık sol 1000, üst 600, sağ 560, alt 640. **Derin INSIDE.**

| | sonuç |
|---|---|
| düz `int` | `OK (1000, 600, 1000, 200)` |
| `uint16` / `uint32` / `uint64` | **`CaptureError: bölge hiçbir monitörle kesişmiyor`** |

**Ayrışan aile `x == w`; kenar uzaklığıyla ilgisi yok:**

| x | w | `x == w` | ayrışma |
|---|---|---|---|
| 1000 | 1000 | ✓ | **evet** |
| 1000 | 1001 | ✗ | hayır |
| 999 | 1000 | ✗ | hayır |
| 500 | 500 | ✓ | **evet** |
| 300 | 300 | ✓ | **evet** |
| 1200 | 1200 | ✓ | **evet** |

**SINIF:** Bu, PROTOKOL §4.6/**10**'un yasakladığı sınıfın **bir kat aşağıda tekrarı**. Kuralı şef bu görevde yazdı; ihlal bu kez docstring'de. İddianın dayandığı grid (adım 20) `x == w` noktasını **yapısal olarak üretemiyor** — pozitif kontrol yok.

**DEĞİŞMEZ (belge kuralı):** Docstring **olumsuz evrensel iddia yazmaz** ("hiç", "sıfır", "yalnızca … durumunda"). Ölçülen üyeler sayılır; kümenin tamamı karakterize edilmediyse `[ÖLÇÜLMÜYOR]` damgası taşır (§4.6/2).

**YAPILACAK:** O cümle **silinir.** Yerine ölçülmüş olan yazılır: ayrışma kümesi **tam karakterize edilmemiştir** `[ÖLÇÜLMÜYOR]`; ölçülmüş üyeler — (1) kenardan taşan bölgeler, (2) `x == w` ailesi (derin INSIDE'da bile), (3) L düzeninde `uint8` çıplak `OverflowError`. `delivery.md` `known_gaps` alanı da aynı biçimde düzeltilir.

Docstring'in **işlevi değişmiyor**: düzleştirmenin neden gerekli olduğunu üç zarar kipiyle zaten anlatıyor; silinen cümle o gerekçeye hiçbir şey katmıyordu, yalnız gatelenemeyen bir genelleme ekliyordu.

---

## Şefin bu turda düzelttiği kendi hatası

`sef_karari-tur2.md`'nin "YAPILMAYACAKLAR" tablosu şöyle diyordu:

> *"`headless_check.py` §3'e `with` bacağı eklemek — **T2-1 sınıfı `tests/` katmanında kapanıyor**; ayrı tur."*

**Bu ölçülmemiş bir iddiaydı ve yanlıştı**: sınıfın istisna yarısı açık kaldı. **Ertelemenin gerekçesi de bir iddiadır ve ölçülmelidir.** Kayda geçti.

`headless_check.py` §3'e `with` bacağı bu turda da eklenmiyor — ama artık **gerekçesi ölçülü**: T3-1 ekseni `tests/` katmanında **iki sınıfın ikisiyle de** kapanıyor ve eksenin sınıf sayısı (2) yukarıda ölçüldü. §3'e ikinci savunma yazmak fazlalık olur.

## Kabul edilen, bloke olmayan üç düzeltme

1. **Kapsam artmadı.** Şef tur 2'de "%98.83 → %99" yazmıştı; D ölçtü: **tur 1 ve tur 2 birebir aynı** (171 ifade / 2 eksik / %98.83). "%99" yalnızca yuvarlanmış gösterim, tur 1'de de öyleydi. **D haklı; şefin ifadesi düzeltildi.**
2. **M54 bağımlılığı** (`grab` tutamacı başka alana yazarsa yalnız `headless_check` §3 `c1_close` yakalıyor) — kayda geçti, ayrı tur.
3. **`known_gaps` ile docstring çelişmiyor**; hata kopyalamada değil **genellemede**. D haklı.

---

## Kabul komutları (tur 3)

```
python -m mypy --strict --explicit-package-bases src/capture/service.py src/capture/monitors.py
python -m pytest tests/unit/capture/test_service.py tests/unit/capture/test_monitors.py -q
python .agents/tasks/T-005/headless_check.py
python -m pytest tests/unit/capture -q --cov=src.capture.service --cov=src.capture.monitors --cov-fail-under=95
python -m pytest tests -q
```

**Şefin ayrıca koşacağı kapılar (implementer koşmaz):**

```
python .agents/tasks/T-005/tester_D/mutant_kiti.py M12 M13 M37 M44
python .agents/tasks/T-005/tester_D/mutant_kiti_tur2.py M50 M51 M52 M53 M56 M57
```

`M52` bir **kontrol mutantıdır** (davranış-eşdeğer) ve **kaçmalıdır**; kapıya takılırsa ölçü yanlış pozitif veriyordur. Diğerlerinin hepsi yakalanmalı.

**Yön bağlayıcı, sayı değil:** düşen test olmayacak; `exc_type` ekseninin **iki sınıfı da** koşulacak.
