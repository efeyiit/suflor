# Şef Kararı — T-005, Tur 2

Tester turu 1 bitti: **A, B, C onay · D ret.** Dördünün de her iddiası şef tarafından kendi eliyle yeniden üretildi (`sef_dogrulama/sonda_tester_{A,B,C,D}.txt`).

D'nin ret'i **haklı ve kabul edildi.** Bulduğu iki kusur ürünün kodunda değil, **şefin kapısında**: iki değişmezin ölçüsü yapısal olarak boş. Ama sonuçlarından biri (M13) **ürünü gerçekten kırıyor** ve beş kapının hiçbiri görmüyor — bu yüzden bloke.

## Şefin beş kapıyı kendi koşumu

|  | TABAN | M12 (`__exit__` boş) | M13 (`close()` sıfırlamaz) |
|---|---|---|---|
| mypy --strict | exit 0 | exit 0 | exit 0 |
| sahipli iki dosya | 159 passed | 159 passed | 159 passed |
| headless_check | TEMİZ | TEMİZ | TEMİZ |
| tests/unit/capture | 742 passed | 742 passed | 742 passed |
| tests (tam takım) | 981 passed | 981 passed | 981 passed |

**Gerçek ekranda zarar (şef ölçtü):**

- **M12** — `with MssBackend() as b: b.grab(...)` bloğundan çıkışta `_tutamac` **açık kaldı** (taban: `None`). Her `with` bir window DC sızdırır; K10'un kendi ölçtüğü arıza 5001. örnekte `GetWindowDC`'yi kalıcı düşürüyor.
- **M13** — `grab → close() → grab` dizisi: **`ScreenShotError: BitBlt`**. Taban aynı dizide `(16,32,4)` döndürüp yeni `MSS` kuruyor.

M13 ürünü kırıyor ve hiçbir kapı görmüyor. Kapı kör.

---

## T2-1 · K10'un iki ölçüsü boş — iki test eklenecek (BLOKE)

**DEĞİŞMEZ (yeni değil, K10'da zaten yazılı):** `MssBackend.__exit__` `close()`'u çağırır; `close()` tutamacı kapatır, **`_tutamac`'ı `None`'a çeker** ve idempotenttir.

**NEDEN ÖLÇÜ BOŞTU:**

- `__exit__` tarafı: tek birim testi (`test_k1_mss_backend_yapimi_mss_e_dokunmaz`) satırı **kapsıyor** ama yalnız `ic is b` iddia ediyor; orada `_tutamac` zaten `None` olduğu için `close()` etkisiz ve iddia iki davranışı ayırt edemiyor. `headless_check.py` §3 `MssBackend`'i **hiç `with` ile kullanmıyor**.
- `close()` tarafı: §3 casusunun `_FakeMSS.close()`'u kendi içinde `self._closed` ile korunuyor (gerçek `mss.MSS.close()` gibi). Sayaç bu yüzden **hiçbir uygulamada** artmaz — ölçü yapısal olarak düşemez. Ayırt eden gözlem sayaç değil, **`_tutamac`'ın sıfırlanması**.

**ÖLÇÜ (Tester-D yazdı, şef ayırt etme gücünü kendi ölçtü):** `tests/unit/capture/test_service.py`'ye iki test — `feedback-D.md`'deki kod birebir. Sahte tutamaç `_tutamac`'a enjekte edilir; **gerçek ekrana sıfır temas**, K1 engeli altında koşar.

| durum | sonuç (şef koştu) |
|---|---|
| TABAN | `2 passed` |
| M12 | `1 failed, 1 passed` |
| M13 | `2 failed` |

Ekli haliyle taban: sahipli **161 passed**, tam takım **983 passed**, mypy exit 0.

---

## T2-2 · `capture_region` docstring'i ölçülmemiş bir gerekçe yazıyor (şefin kendi hatası)

**BULAN:** şef, Tester-B'nin `np.uint8` olgusunu doğrularken.

`src/capture/service.py` `capture_region` docstring'i şunu diyor:

> *"…dondurulmus `dpi.py` isaretsiz numpy tamsayilarinda **tasar** (`np.uint16`/`np.uint32` ile `classify_region` `inside` yerine `partial` verir…), yani `monitor_index` **sessizce yanlis cikardi**."*

İki ayrı sorun, ikisi de ölçüldü:

**(a) Tip listesi eksik.** Dört işaretsiz tipin **dördü de** taşıyor:

| tip | `classify_region` | RuntimeWarning |
|---|---|---|
| `uint8` | `inside` (tesadüfen doğru) | **var** |
| `uint16` | `partial` | var |
| `uint32` | `partial` | var |
| `uint64` | `partial` | **var** |

Docstring yalnız `uint16`/`uint32` sayıyor. `uint8` ve `uint64` de taşıyor.

**(b) "Sessizce yanlış" cümlesi ÇÜRÜDÜ.** Şefin ölçümü — 1.136.328 kombinasyon (`x,y` 0..260, `w,h` 1..260, dört tip), düzleştirilmiş ile ham numpy `_hedef_dikdortgen` çıktıları karşılaştırıldı:

| tip | aynı | ok→HATA | HATA→ok | **SESSİZ** |
|---|---|---|---|---|
| uint8 | 264264 | **2136** | 0 | **0** |
| uint16 | 290688 | 1152 | 0 | **0** |
| uint32 | 290688 | 1152 | 0 | **0** |
| uint64 | 290688 | 1152 | 0 | **0** |

**Sessiz ayrışma sıfır.** Taşmanın tek görünür kipi `CaptureError` — yani **gürültülü red**, sessiz yanlış değil.

**Düzleştirme yine de GEREKLİ ve kural değişmiyor:** onsuz 2136 (uint8) / 1152 (diğerleri) **geçerli** bölge reddedilirdi. Değişen yalnız **gerekçe cümlesi**.

**YAPILACAK:** docstring'in ilgili cümlesi ölçüme uygun biçimde düzeltilir — dört tip de sayılır, "sessizce yanlış çıkardı" yerine ölçülen kip yazılır (geçerli bölgeler `CaptureError` ile reddedilirdi; sayılar yukarıda). Aynı düzeltme `delivery.md` `known_gaps`'ine de girer (paketin "İKİ YERE yaz" kuralı).

**ÖLÇÜ:** davranış değişikliği yok → yeni test yok. Kapı: beş kabul komutu düşmemeli. Bu bir **belge** kalemi; sınıfı T-004'ün T7-1'i ile aynı.

---

## T2-3 · Tester-D'nin ölçtüğü iki kör ölçü — birer satırla kapanıyor (ikincil)

İkisinde de **uygulama doğru**; kör olan ölçü.

1. **M44 — `FakeBackend` varsayılan `image_factory`.** K1 "varsayılan `(rect.h, rect.w, 4)` sıfır dizi döndürür" diyor; şekli `(h,w,3)` yapan mutant beş kapıdan da geçiyor. Tek satır kapatır.
2. **M37 — K3 ölçüsü `==` ile yazılmış.** `Rect(np.int64(100),…) == Rect(100,…)` `True`, hash eşit; bu yüzden backend'e giden kutuda numpy sızıntısını `test_k3_*` **göremez**. Sızıntıyı gören tek şey `type(x) is int` (şef T-004'te ölçtü, B tur 1'de yeniden üretti).

**ÖLÇÜ:** implementer bu iki testi ekledikten sonra, **şef** mutant kitini koşar: `M44` ve `M37` artık `[.....]` vermemeli. Kiti implementer koşmaz (tester dizini; kör yapı korunur).

---

## Kapsam — bu turda YAPILMAYACAKLAR (bilinçli, kayda geçer)

| Kalem | Neden bu turda değil |
|---|---|
| `headless_check.py` §3'e `with` bacağı eklemek | T2-1 sınıfı `tests/` katmanında kapanıyor; §3'e ikinci bir savunma yazmak **şefin ölçü kurgusuna** dokunur ve kırmızı takım ister. Kapanışta açık kalem. |
| §4'ün dekoratör denetiminin yalnız `FakeBackend.grab`'e bakması | Aynı sınıf, aynı gerekçe. |
| `validate.py`'nin `known_gaps` içeriğine kör olması | Paket bunu zaten "şefin elle denetlediği kapı" diye yazıyor; D denetledi, temiz. Ajan altyapısı kalemi. |
| Saat fırlatırsa `seq` tüketilir (Tester-C) | Üretimde erişilemez (`time.monotonic` fırlatmaz). Kayda geçti. |
| `dpi_scale = nan/inf` kabul ediliyor (Tester-B) | Sözleşme sorusu, `src/contracts/` dondurulmuş. Ayrı görev. |
| `Frame.image` `compare=False` → `==` sahiplik regresyonunu göremez (Tester-A) | Dondurulmuş `src/contracts/`; T-005'in suçu değil. Ayrı görev. |
| Boş monitör guard'ı davranışsal olarak gereksiz (Tester-C) | Guard'ın değeri **tanı mesajı**; silinirse mesaj yanıltıcı olur ama davranış aynı. Kayda geçti, dokunulmuyor. |

---

## Neden karar kırmızı takımına gitmiyor (§4.5 tarzı gerekçeli azaltma)

Karar kırmızı takımı şefin **değişmez ve ölçü kurgusundaki** hatalarını yakalamak için var. Bu turda:

- **Yeni değişmez yok.** T2-1 K10'un, T2-3 K1 ve K3'ün **zaten yazılı** değişmezleri.
- **Şef yeni ölçü kurgulamıyor.** T2-1'in ölçüsünü **Tester-D yazdı ve ayırt etme gücünü ölçtü; şef üçünü de kendi koştu** (taban 2 passed / M12 1 kırık / M13 2 kırık). T2-2 bir cümlenin **çıkarılması** (ekleme değil). T2-3 iki tek satırlık assert, hedef mutantları adlandırılmış.
- **Davranış değişikliği yok.** `src/capture` mantığına dokunulmuyor; yalnız docstring metni + testler.
- **Kapı şefin elinde.** Kabul mutant kitiyle ölçülüyor ve kiti şef koşuyor.

Kırmızı takımın bu turda açacağı bir hata sınıfı yok. §4.6/9 da aynı yöne işaret ediyor: paket sekiz kırmızı takım turu gördü, iş artık implementer'da.

---

## Kabul komutları (tur 2)

```
python -m mypy --strict --explicit-package-bases src/capture/service.py src/capture/monitors.py
python -m pytest tests/unit/capture/test_service.py tests/unit/capture/test_monitors.py -q
python .agents/tasks/T-005/headless_check.py
python -m pytest tests/unit/capture -q --cov=src.capture.service --cov=src.capture.monitors --cov-fail-under=95
python -m pytest tests -q
```

**Şefin ayrıca koşacağı kapı (implementer koşmaz):**

```
python .agents/tasks/T-005/tester_D/mutant_kiti.py M12 M13 M37 M44
```

Beklenen: **163 sahipli / 985 tam takım** — T2-1 iki test (161/983 şef tarafından ölçüldü) + T2-3 iki test. Sayı değil **yön** bağlayıcıdır: düşen test olmayacak, dört mutantın dördü de yakalanacak.

## Tur 2 sonrası

Tester-D **yeniden nişan alır** (ret veren tester re-test eder). A, B, C yeniden koşmaz; şef onların takımlarını regresyon olarak koşar — `src/capture` mantığı değişmediği için düşen beklenmiyor.
