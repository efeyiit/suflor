# Feedback — T-003, tur 1 (tester -> implementer)

## Ozet

Kabul komutlarinin ikisi de geciyor (`mypy --strict`, `pytest
tests/unit/capture/test_dpi.py -q` -- 133/133). Modulun buyuk cogunlugu
saglam: yuvarlama simetrisi, negatif koordinatli monitor round-trip'i,
karisik DPI izolasyonu, saflik, sozlesmeye saygi ve `classify_region`
siniflandirmasi -- hepsini kendi bagimsiz, genis rastgele orneklemimle
(sabit tohum `908171`, tekrar uretilebilir) sinadim ve hepsi tuttu.

Tek ama gercek bir sorun var: **round-trip iddiasinin docstring'deki
kosulsuz ifadesi, kodun kendi kabul ettigi girdi kumesinin tamami icin
dogru degil.**

## Sorun

`src/capture/dpi.py` modul docstring'i, "Round-trip kararliligi" basligi
altinda soyle diyor:

> `physical_to_logical(logical_to_physical(r)) == r` -- HER ZAMAN dogru.

Bu ifade **hicbir `dpi_scale` kisitiyla nitelenmemis** -- yani okuyucuya
"kod hangi `dpi_scale`'i kabul ediyorsa, hepsi icin gecerli" izlenimini
veriyor. Fakat hemen altindaki ispat taslagi acikca "s >= 1 olcek olsun"
diye baslıyor -- yani ispat, iddiayi TUM kabul edilen girdiler icin degil,
yalnizca `s >= 1` alt kumesi icin kapsıyor.

Kodun kendisi (`logical_to_physical` ve `physical_to_logical`,
`src/capture/dpi.py`) ise SADECE sunu kontrol ediyor:

```python
if rect.dpi_scale <= 0:
    raise ValueError(...)
```

Yani `0 < dpi_scale < 1` araligi **hicbir hata firlatmadan gecerli kabul
ediliyor** -- ama bu aralik icin round-trip iddiasi **sistematik olarak
yanlis**.

## Tekrar uretim (minimal, pytest'siz)

```bash
cd "C:\Users\pc\Desktop\efe\çeviri uygulaması"
PYTHONPATH=. python -c "
from src.capture.dpi import logical_to_physical, physical_to_logical
from src.contracts.models import Rect

original = Rect(x=3, y=3, w=3, h=3, dpi_scale=0.5)
physical = logical_to_physical(original)
recovered = physical_to_logical(physical)
print('orijinal:', original)
print('fiziksel:', physical)
print('geri-don:', recovered)
print('esit mi :', recovered == original)
"
```

Gercek cikti (ayrica `tester_evidence/repro_scale_below_one_output.txt`
dosyasinda duruyor):

```
orijinal: Rect(x=3, y=3, w=3, h=3, monitor_index=0, dpi_scale=0.5)
fiziksel: Rect(x=2, y=2, w=2, h=2, monitor_index=0, dpi_scale=0.5)
geri-don: Rect(x=4, y=4, w=4, h=4, monitor_index=0, dpi_scale=0.5)
esit mi : False
```

`logical_to_physical` **hata firlatmadi** (`dpi_scale=0.5 > 0` oldugu
icin gecerli sayildi) ama sonuc orijinalden farkli: `3 -> 2 -> 4`.

## Bunun izole bir kaza olmadiginin kaniti (sistematik olcum)

Ayni betikte, `(0, 1)` araligini taradim (`0.05` adimlarla, `L` degerleri
`-50..50`):

```
(0,1) araliginda sistematik basarisizlik: 960/1919 (%50.0)
```

Yani bu araliktaki gecerli (hata firlatmayan) girdilerin **yaklasik
yarisinda** round-trip bozuluyor. Tam betik: `tester_evidence/repro_scale_below_one.py`,
cikti: `tester_evidence/repro_scale_below_one_output.txt`.

Ayni bulgu, bagimsiz pytest test dosyamda da (kopya degil, sifirdan
yazilan) kirmizi olarak duruyor:

```
python -m pytest .agents/tasks/T-003/tester_tests -q -vv
```

`test_round_trip_claim_as_documented_is_scale_ge_1_only_KNOWN_GAP`
testinin tam cikisi `tester_evidence/pytest_tester_tests_verbose.txt`
dosyasinda.

## Neden bu blokeleyici (env.md, saldiri noktasi #1)

env.md acikca soyle diyor: "İddia tutmuyorsa bu bloke edicidir." Iddia
(docstring'deki kosulsuz "HER ZAMAN dogru" ifadesi), kodun kendi
validasyonunun kabul ettigi bir girdi kumesi icin tutmuyor. Bu, "gercekci
olmayan/asiri uc bir girdi" degil -- kod bu girdiyi ACIKCA gecerli
sayiyor (hata firlatmiyor), sadece dokumante edilen garantiyi saglamiyor.

## Onerilen duzeltme (ikisinden biri yeterli)

**Secenek A -- validasyonu sikilastir (tercih edilen, cunku iddia gercekten
"HER ZAMAN" kalir):**

```python
if rect.dpi_scale < 1.0:  # veya <= 0, hangisi once kontrol edilecekse
    raise ValueError(f"dpi_scale >= 1.0 olmali, gelen: {rect.dpi_scale!r}")
```

Hem `logical_to_physical` hem `physical_to_logical` icin (ikisi de zaten
ayni desende `<= 0` kontrolu yapiyor, oraya ekleme dogal olur). Bu secim
zaten gercekci: Windows DPI olcekleri hicbir zaman %100'un altina inmez.

**Secenek B -- docstring'i durustlestir (validasyonu degistirmeden):**

Module docstring'deki "HER ZAMAN dogru" cumlesini "s >= 1 icin HER ZAMAN
dogru" olarak degistir; `dpi_scale < 1` icin round-trip'in GARANTI
EDILMEDIGINI acikca yaz (fiziksel->mantiksal->fiziksel yonu icin zaten
yapilan uyariya benzer bicimde).

Hangi secenek uygulanirsa uygulansin, `tests/unit/capture/test_dpi.py`
icindeki `SCALES = (1.0, 1.25, 1.5, 1.75, 2.0)` sabitine en az bir
`< 1.0` deger (ornegin `0.5` veya `0.75`) eklenmesini, ve secilen
davranisin (ValueError mi, belgelenmis sinirlama mi) o degerle acikca
test edilmesini oneririm -- mevcut kabul testleri bu araligi hic
kapsamiyor, bulgu tam da bu bosluktan gecti.

## Bloke etmeyen ek not (isterseniz bu turda da duzeltebilirsiniz)

Negatif genislik/yukseklik (`w < 0` veya `h < 0`) hicbir fonksiyonda
cokmeye yol acmiyor ve `intersect`/`clamp_to_monitor`/`classify_region`
bunu tutarli sekilde "alani yok" (None/OUTSIDE) sayiyor -- guvenli bir
secim. Ama bu, modulun docstring'inde hicbir yerde ACIKCA yazilmiyor
(dpi_scale<=0 icin oldugu gibi bir aciklama yok). Bloke etmiyorum ama
bir cumleyle belgelenmesini oneririm.
