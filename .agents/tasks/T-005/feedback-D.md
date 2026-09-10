# T-005 · Tester-D (mercek: test kalitesi) · **tur 2** · ret

> Bu dosyayi okuyan duzeltme ajani baglami SIFIRDAN kuruyor (PROTOKOL §7).
> Asagida: ne eksik, nasil yeniden uretilir, ne beklenir, hazir kod, ve
> onerilen duzeltmenin OLCULMUS ayirt etme gucu.

## Once: tur 1'in iki bloke bulgusu KAPANDI

Eklenen dort testi mutantla sinadim; sefin adlandirdigi dordu de yakalaniyor:

```
python .agents/tasks/T-005/tester_D/mutant_kiti.py M12 M13 M37 M44
  M12 [.X.XX]  M13 [.X.XX]  M37 [.X.XX]  M44 [.X.XX]      -> hepsi YAKALANDI
```

Testler **totoloji degil**: ayni degismezleri BASKA bicimde ihlal eden
varyantlar da dusuyor (`mutant_kiti_tur2.py`):

| mutant | ne yapiyor | sonuc |
|---|---|---|
| M50 | `__exit__` tutamaci **kapatmadan** birakir (alan `None` olur) | YAKALANDI |
| M51 | `close()` alani sifirlar ama alttaki `close()`'u cagirmaz | YAKALANDI (G2 + §3) |
| M52 | **KONTROL**: `close()` sirasi ters, davranis ayni | dogru sekilde kacti |
| M56 | varsayilan uretici **devrik** `(w,h,4)` | YAKALANDI |
| M57 | varsayilan uretici `ones` dondurur | YAKALANDI |

Kapsam/pragma da temiz: tam 3 pragma, ucu de izinli metotta, gerekce yorumlu,
gizli `exclude_lines` yok. Kapsam tur 1 ile **birebir ayni** (171 ifade / 2
eksik / %98.83) -- yeni testler kapsami yukseltmedi, cunku `close()` govdesi
zaten pragma'li; olctukleri sey kapsam degil **davranis**. Dogru olan bu.

`src/` yine **degismeyecek**. Iki kalem de tek dosyada kapaniyor: biri
`tests/unit/capture/test_service.py`, digeri `src/capture/service.py`'nin
**docstring metni** (+ `delivery.md` `known_gaps`).

---

## BLOKE D-2.1 · `__exit__` -> `close()` olcusu ISTISNA yolunda BOS

**Yazili degismez (packet.md K10):** "`MssBackend` baglam yoneticisidir
(`__enter__` self, `__exit__` -> `close()`)." Kosulsuz.

**Olculen:** `__exit__`'i **yalnizca temiz cikista** kapatan bir uygulama
**bes kabul komutundan da exit 0 aliyor.**

### Yeniden uretim

`src/capture/service.py` icinde (gecici olarak):

```python
    def __exit__(self, *_: object) -> None:
        if not _ or _[0] is None:      # <-- istisna varsa KAPATMIYOR
            self.close()
```

sonra bes komutu kostur. Tek komutla:

```bash
python .agents/tasks/T-005/tester_D/mutant_kiti_tur2.py M53
```

Ham cikti: `tester_D_evidence/r2-09-mutant-dalga-tur2.txt`

```
M53 [.....] *** HICBIR KAPI YAKALAMADI ***
     __exit__ yalnizca ISTISNASIZ cikista kapatir (govde patlarsa tutamac sizar)
```

(`.` = kapi kacirdi.) Karsilastirma icin ayni dosyada `M50 [.X.XX]` ve
`M51 [.XXXX]` -- yani olcu **calisiyor**, sadece bu eksende tek noktada.

### Neden onemli: bu, urunun ISTISNAI degil NORMAL yolu

`with MssBackend() as b:` govdesinin istisnayla bitmesi beklenmedik bir olay
degil: K6 sinif (b) backend istisnasi ve sinif (c) gecersiz cikti **tanimli**
hata siniflaridir ve `capture_region` bunlari `CaptureError` olarak cagirana
yayar. Yani "govde patladi -> `__exit__` calisti" senaryosu, urunun her hatali
yakalamasinda gerceklesir.

Bedeli tur 1'de bloke edilen M12'ninkiyle **ayni**: `mss`'te `__del__` yok;
kapatilmayan her ornek bir window DC + memory DC sizdirir ve sefin olcumune
gore **5001. kapatilmamis ornekte `GetWindowDC` kalici olarak duser**.

### Uygulama DOGRU -- kusur kapida (pozitif kontrol)

Teslim edilen kod istisna yolunda da kapatiyor; bunu casus `mss` modulu ile
gercek ekrana dokunmadan olctum:

```
tester_D/test_d5_bos_olcum_noktalari.py::test_d5_TUR2_uygulama_ISTISNA_yolunda_da_kapatiyor
  -> MSS kurulum 1, kapatma 1, `_tutamac is None`   (GECTI)
```

Yani bu bir **kod** duzeltmesi degil, bir **olcu** duzeltmesidir.

### DUZELTME -- hazir kod

`tests/unit/capture/test_service.py`'nin **sonuna** ekle (mevcut
`_SahteTutamac` sinifi ve `pytest` import'u zaten orada):

```python
def test_k10_exit_ISTISNA_yolunda_da_kapatir() -> None:
    """K10: `__exit__` -> `close()` KOSULSUZDUR -- istisna yolunda da.

    `with MssBackend() as b:` govdesinin `CaptureError` ile bitmesi urunun
    NORMAL hata yoludur (K6 sinif b/c: backend istisnasi ve gecersiz cikti).
    Yalnizca temiz cikista kapatan bir uygulama HER hatada bir window DC
    sizdirir -- K10'un kendi olctugu ariza 5001. kapatilmamis ornekte
    `GetWindowDC`'yi kalici olarak dusuruyor. Ustteki test istisnasiz yolu
    olcer; bu test ikinci noktadir (PROTOKOL §4.6/7).
    """
    b = MssBackend()
    t = _SahteTutamac()
    b._tutamac = t  # type: ignore[assignment]
    with pytest.raises(RuntimeError):
        with b:
            raise RuntimeError("govde patladi")
    assert t.kapatma == 1, (
        "istisna ile cikilan `with` blogunda __exit__ close() cagirmadi -> "
        "her hatali yakalama bir window DC sizdirir"
    )
    assert b._tutamac is None
```

### Bu duzeltmenin AYIRT ETME GUCU olculdu

Ayna agacinda kosuldu (ham cikti:
`tester_D_evidence/r2-16-onerilen-duzeltme-gucu.txt`):

| durum | oneri EKLENMEDEN | oneri EKLENEREK |
|---|---|---|
| TABAN (teslim edilen kod) | 163 passed | **164 passed** |
| M53 (`__exit__` yalniz temiz cikista kapatir) | 163 passed (**kacti**) | **1 failed** |
| M12 (`__exit__` -> `return None`) | 1 failed | **2 failed** |
| M50 (`__exit__` kapatmadan birakir) | 1 failed | **2 failed** |

Yani test tabanda gecer, hedef mutantta kirilir ve diger iki bicimi de
bagimsiz olarak yakalar -- totoloji degil.

---

## BLOKE D-2.2 · Docstring, olculmemis bir "SIFIR" iddiasi tasiyor

`src/capture/service.py` -> `CaptureService.capture_region` docstring'inin son
paragrafi soyle bitiyor:

> "Kenardan uzak (derin INSIDE) bolgelerde ise dort tipte de ayrisma
> **sifirdir** -- tasma yalnizca monitor sinirlarina yaklasan bolgelerde
> gozlemlenebilir hale gelir."

**Bu cumle olcumle YANLIS.**

### Yeniden uretim (tek nokta, 6 satir)

```python
import numpy as np
from src.capture.service import CaptureService, FakeBackend
from src.contracts.models import Rect
s = CaptureService(FakeBackend((Rect(-2560,0,2560,1440), Rect(0,0,2560,1440))))
s._hedef_dikdortgen(Rect(1000, 600, 1000, 200))                    # -> ok (1000,600,1000,200)
s._hedef_dikdortgen(Rect(np.uint32(1000), np.uint32(600),
                         np.uint32(1000), np.uint32(200)))         # -> CaptureError
```

`Rect(1000, 600, 1000, 200)` bolgesi `M1 = (0,0,2560,1440)`'in **tamamen
icindedir**; en yakin monitor kenarina uzakliklari: sag **560 px**, ust
**600 px**, alt **640 px**, M0/M1 dikisine **1000 px**. "Kenardan uzak"
tanimina her olcude uyar -- ve duzlestirme olmasaydi bu **gecerli** bolge
`CaptureError` alirdi.

Kit halinde:

```bash
python .agents/tasks/T-005/tester_D/t2_docstring_olcumu2.py
python -m pytest .agents/tasks/T-005/tester_D/test_d9_tur2_docstring_iddialari.py -q
```

Ham ciktilar: `tester_D_evidence/r2-11`, `r2-12`, `r2-13`.

### Olculen tablo -- derin INSIDE grid (x 100..1100, y 100..800, w/h in {1,50,200,500})

| tip | temsil edilebilir kombinasyon | **ayrisma** | kip |
|---|---|---|---|
| uint8 | 36 | **6** | gurultulu red |
| uint16 | 1408 | **64** | gurultulu red |
| uint32 | 1408 | **64** | gurultulu red |
| uint64 | 1408 | **64** | gurultulu red |

Ayrisan aile **`x == w`**'dir (x=100,200,300,500,700,1000,1200 -- hepsi
ayrisiyor; `x != w` komsulari ayrismiyor) ve **kenara uzaklikla ilgisi
yoktur**. Kaynak M0'in negatif x'idir: ayni grid TEK monitorlu (`M1`) duzende
kosuldugunda ayrisma **0/1408**.

### Neden bu, tam olarak PROTOKOL §4.6/10'un yasakladigi sinif

Kural bu turda **tam bu cumlenin atasi** yuzunden eklendi: "'Sifir ihlal' bir
olcum degildir -- olcunun ateşleyebildigi gosterilmeden yazilamaz."

Iddianin dayandigi grid (`x,y` 0..260 **adim 20**, `w,h` 1..260 **adim 20**)
`x == w` noktasini **yapisal olarak uretemez**: `x` cift/20'nin kati, `w` ise
`1, 21, 41, ...`. Yani "sifir", uygulamanin dogrulugunu degil **grid'in o
aileye hic ugramadigini** olcuyor -- bir kat asagida ayni kor nokta.

Teslimin kendi kanit dosyasinda da karsi ornek var: `t2-2-tasma-olcumu.txt`
D bolumu, `-- INSIDE (100,100,100,100)` satiri dort tipte de
`<== GURULTULU: gecerli bolge REDDEDILDI` diyor. `x=100, w=100` -> `x == w`.

### DUZELTME -- hazir metin

Docstring'deki o cumleyi **sil** ve yerine olculeni yaz:

```
Ayrisma monitor kenarina YAKINLIKLA belirlenmez: derin INSIDE bir bolge de
ayrisabiliyor (olculdu -- `Rect(1000, 600, 1000, 200)` M1'in tamamen icinde,
her kenardan >= 560 px uzak, ve ham `uint16/32/64` yolunda `CaptureError`
aliyor; ayrisan aile `x == w`). Belirleyen sey, isaretsiz aritmetigin
NEGATIF x'li monitorle (M0 = -2560) karsilasmasidir: tek monitorlu bir
duzende ayni grid'de ayrisma yoktur. Bu yuzden duzlestirme bolgeye gore
degil KOSULSUZ uygulanir.
```

Ayni duzeltme `delivery.md` `known_gaps`'ine de girer (paketin "IKI YERE yaz"
kurali). **Not:** `known_gaps`'teki mevcut metin **dogru** -- orada iddia
sefin grid'ine baglanmis durumda ("...sebebi tasmanin zararsizligi DEGIL, o
grid'in her bolgesinin ... derin icinde kalmasi"). Hata **kopyalamada degil,
docstring'de yapilan GENELLEMEDE**. Genellemeyi kaldirmak yeterli.

**Davranis degismez, yeni test gerekmez** -- ama isterseniz olcu hazir:
`tester_D/test_d9_tur2_docstring_iddialari.py::test_d9_derin_INSIDE_bolgede_de_AYRISMA_VAR`
(uc tipte parametreli, tabanda gecer).

---

## Docstring'in DIGER iddialari: ucu de dogru cikti (degistirme)

Bagimsiz olctum (`t2_docstring_olcumu.py`, `r2-10`); hepsi birebir tutuyor:

| iddia | olculen |
|---|---|
| dort isaretsiz tipin **dordu de** tasar, her birinde `RuntimeWarning` | uint8 x5, uint16/32/64 x3 uyari -- DOGRU |
| gurultulu red: `Rect(uint16(100)x4)` INSIDE ama `outside` cikar | DOGRU |
| sessiz yanlis: `Rect(uint32(2500),100,200,100)` -> dogru `w=60`, ham `w=200`, istisna yok | DOGRU (2 RuntimeWarning disinda iz yok) |
| 6480 kombinasyonun **1108**'i sessiz farkli geometri (uint32/uint64) | **1108** -- DOGRU |
| **240**'i sessizce kabul edilen gecersiz bolge | **240** -- DOGRU |
| uint8 kucuk duzende K6 disi ciplak `OverflowError` | DOGRU (L duzeninde 25 vaka, "integer 10000 out of bounds for uint8") |
| urunun kendi yolu: `Frame.rect = (2500,100,60,100)`, dort alan duz `int` | DOGRU |

Sefin tur 1'de bildirdigi **2136/1152** sayilarini ben de yeniden uretemedim;
teslimin onlari docstring'e yazmamis olmasi **dogru karar**.

---

## Bloke ETMEYEN, kayda gecen notlar

1. **Enjeksiyonun uretime bagi TEK kapiya yasliyor.** Yeni iki test
   `_tutamac`'a dogrudan yaziyor. `grab()` tutamaci **baska** bir alana
   (`_tutamac2`) yazsin, `close()`/`__exit__` yine `_tutamac`'a baksin (M54):
   iki test de **gecer** (kendi enjekte ettikleri alani kapatiyorlar), uretimde
   ise her tutamac sizar. Bu mutanti yakalayan tek sey `headless_check` §3'un
   `c1_close` sayacidir (`M54 [..X..]`). Bagi VAR, ama tek noktadan geciyor;
   §3 degisirse iki test sessizce totolojiye doner. Ucuz sertlestirme: yeni
   testlerden birine `assert "_tutamac" in vars(MssBackend())` yerine, casus
   `mss` ile `grab()` sonrasi `b._tutamac is not None` iddiasi eklemek.
2. **`test_k3_backend_kutusu_duz_int_tasir` tek YOL noktasinda kosuyor.** Dort
   TIP noktasi var (iyi), ama yalniz INSIDE bacagi. Backend kutusuna numpy
   skalerini **yalniz PARTIAL yolunda** sizdiran bir mutant (M58) bes kapidan
   da geciyor (`r2-09`). Bloke DEGIL: K3'un yazili degismezi INSIDE kapsamli
   ve `Frame.rect` iki yolda da duz kaliyor. Sertlestirme: ayni testin
   parametrelerinden birini PARTIAL bolge yap (or. `Rect(tip(2500), tip(100),
   tip(200), tip(100))` -> kirpik `w=60`, kutu yine duz `int` olmali).
3. **Kontrol mutantlari yanlis pozitif uretmiyor.** `close()`'un sirasini
   degistiren davranis-esdeger varyant (M52) bes kapidan da geciyor -- olmasi
   gerektigi gibi.
4. **`headless_check` §3 hala `with` kullanmiyor**, §4'un dekorator denetimi
   hala yalniz `FakeBackend.grab`'e bakiyor. Sef ikisini de bilincli erteledi;
   D-2.1 bu ertelemenin bedelini gosteriyor. Bu dosya `headless_check`'e
   dokunmadan kapanabilir (yukaridaki tek test yeter).

## Kabul kosulu (tur 3)

```bash
python -m mypy --strict --explicit-package-bases src/capture/service.py src/capture/monitors.py
python -m pytest tests/unit/capture/test_service.py tests/unit/capture/test_monitors.py -q   # 164 passed
python .agents/tasks/T-005/headless_check.py
python -m pytest tests/unit/capture -q --cov=src.capture.service --cov=src.capture.monitors --cov-fail-under=95
python -m pytest tests -q                                                                    # 986 passed
python .agents/tasks/T-005/tester_D/mutant_kiti_tur2.py M53      # [.X.XX] -- artik YAKALANDI
python -m pytest .agents/tasks/T-005/tester_D -q                 # iki xfail XPASS'a donmeli
```

Son iki satir duzeltmenin kapiyi gercekten kapattigini dogrular. Sayi degil
**yon** baglayicidir: dusen test olmayacak, `M53` yakalanacak, docstring'in
"sifir" cumlesi kalkacak.

## Kanit dosyalari

| dosya | ne |
|---|---|
| `tester_D_evidence/r2-01..05` | bes kabul komutunun ham ciktisi (taban: 163 / TEMIZ / 746 / 985) |
| `tester_D_evidence/r2-06-tester-D-bayat.txt` | tur 1 kitinin beklenen UC kirigi (dorduncu yok) |
| `tester_D_evidence/r2-07-kapsam-pragma.txt` | 3 pragma, gizli config yok, kapsam tur 1 ile birebir ayni |
| `tester_D_evidence/r2-08-sef-kapi-mutantlari.txt` | M12/M13/M37/M44 -> dordu de yakalandi |
| `tester_D_evidence/r2-09-mutant-dalga-tur2.txt` | **8 yeni mutant**; M53 ve M58 bes kapidan geciyor |
| `tester_D_evidence/r2-10-docstring-tasma-olcumu.txt` | docstring'in uc kipi + iki sayisi (1108/240) bagimsiz olculdu |
| `tester_D_evidence/r2-11..13` | "sifir" iddiasinin curutulmesi + en guclu karsi ornek |
| `tester_D_evidence/r2-14-known-gaps-vs-docstring.txt` | `known_gaps` (yalniz o alan) x docstring |
| `tester_D_evidence/r2-15-tester-D-kiti-tur2.txt` | yeniden nisanlanmis kit: 113 passed, 2 xfailed |
| `tester_D_evidence/r2-16-onerilen-duzeltme-gucu.txt` | **onerilen testin ayirt etme gucu** (taban/M53/M12/M50) |
| `tester_D_evidence/r2-17-son-durum.txt` | `src/` ve `tests/` degismedi (git) |
| `tester_D/mutant_kiti_tur2.py` | yeni mutant dalgasi (ayna agaci, `src/` yazilmaz) |
| `tester_D/t2_docstring_olcumu.py`, `t2_docstring_olcumu2.py` | docstring olcum kitleri |
| `tester_D/t2_onerilen_duzeltme_gucu.py` | onerilen duzeltmenin gucunu olcen kit |
