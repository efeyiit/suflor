---
task: T-003
role: implementer
round: 2
status: tamamlandi
files_written:
  - src/capture/dpi.py
  - tests/unit/capture/test_dpi.py
commands:
  - cmd: "python -m mypy --strict src/capture/dpi.py"
    exit_code: 0
    evidence: evidence/mypy-r2.txt
  - cmd: "python -m pytest tests/unit/capture/test_dpi.py -q"
    exit_code: 0
    evidence: evidence/pytest-r2.txt
contract_change_request: false
known_gaps:
  - "Sef karari birebir uygulandi: (1) validasyon sikilastirildi -- logical_to_physical VE physical_to_logical artik 'dpi_scale < 1.0' olan HER girdiyi ValueError ile reddediyor (once yalnizca '<= 0' reddediliyordu, 0 < dpi_scale < 1 sessizce kabul ediliyordu). (2) docstring daraltildi/durustlestirildi -- 'HER ZAMAN dogru' ifadesi artik acikca 'modulun kabul ettigi HER girdi icin (r.dpi_scale >= 1.0)' diye nitelendi ve validasyonun kabul alani ile ispatin varsaydigi alanin (s >= 1) birebir ortustugu acikca yazildi. Ikisi birlikte: iddia ile davranis arasinda artik hicbir bosluk yok."
  - "ValueError mesaji artik NEDEN gecersiz oldugunu aciklyor: 'dpi_scale >= 1.0 olmali (Windows olcekleri %100'un altina inmez ve s < 1 icin round-trip garantisi tutmaz), gelen: <deger>' -- eskiden yalnizca 'dpi_scale pozitif olmali' diyordu, 0 < dpi_scale < 1 durumunda bu mesaj hicbir zaman tetiklenmiyordu."
  - "Regresyon testi eklendi: test_scale_below_one_is_rejected_not_silently_broken_REGRESSION, tester'in tur 1'de bulup raporladigi TAM ornegi (Rect(x=3,y=3,w=3,h=3,dpi_scale=0.5)) kullanarak artik ValueError firlatildigini dogrudan dogruluyor. Ayrica test_scale_below_one_systematically_rejected_across_range_REGRESSION, (0,1) araliginda 7 farkli deger icin (0.05, 0.1, 0.5, 0.6, 0.75, 0.9, 0.9999) her ikisinin de (logical_to_physical VE physical_to_logical) reddettigini dogruluyor -- tester'in sistematik olcumune (araligin ~yarisinda sessiz bozulma) karsilik gelen kapsam."
  - "Mevcut test_logical_to_physical_rejects_non_positive_scale / test_physical_to_logical_rejects_non_positive_scale testleri, tur 1'deki bosluga tam denk dusen degerlerle (0.5, 0.75, 0.99, 0.999999) genisletilip test_..._rejects_scale_below_one olarak yeniden adlandirildi; artik hata mesajinin icerigini de (match='dpi_scale >= 1\\.0') dogruluyorlar."
  - "Kapsam DISINDA birakilan (bloke edici olmayan not, tester'in kendisi de zorunlu tutmadi): negatif genislik/yukseklik (w<0 / h<0) davranisi artik dpi.py modul docstring'inde acikca belgelendi ('Negatif genislik/yukseklik -- guvenli ele alinir, cokme yok' basligi) ama bu davranisi hedefleyen YENI bir test eklenmedi -- mevcut classify_region/clamp_to_monitor testleri zaten negatif olmayan girdilerle bu yollari dolayli kapsiyor, ve gorev bu notu 'zorunlu degil' olarak isaretlemisti. Sef isterse ayri bir tur/istekle eklenebilir."
  - "Teknik engel YOK: sef karari (secenek A + secenek B birlesimi) hicbir degisiklik/uyarlama olmadan dogrudan uygulanabildi. SCALES sabiti (1.0, 1.25, 1.5, 1.75, 2.0) zaten tamami >= 1.0 oldugu icin degismedi; mevcut 149 testin TAMAMI (133 + 16 yeni) yesil."
---

# T-003 teslim -- tur 2 (duzeltme turu)

## Ne degisti (tester'in tek bulgusuna karsilik)

Tester'in bulgusu: modul docstring'i round-trip'i kosulsuz "HER ZAMAN dogru"
diye iddia ediyordu ama kodun tek validasyonu (`dpi_scale <= 0`) `0 < dpi_scale
< 1` araligini sessizce kabul ediyordu -- bu aralikta iddia sistematik olarak
yanlisti (somut ornek: `Rect(3,3,3,3,dpi_scale=0.5)` icin `3 -> 2 -> 4`).

Sefin karari (ikisi birden) birebir uygulandi:

1. **Validasyon sikilastirildi.** `logical_to_physical` ve `physical_to_logical`
   artik `if rect.dpi_scale < 1.0: raise ValueError(...)` kontrolu yapiyor
   (eskiden `<= 0`). Bu, `<= 0` durumunu da kapsiyor (0 ve negatifler zaten
   `< 1.0`), ayri bir kontrole gerek kalmadi. Hata mesaji artik nedeni
   aciklyor: *"dpi_scale >= 1.0 olmali (Windows olcekleri %100'un altina
   inmez ve s < 1 icin round-trip garantisi tutmaz), gelen: <deger>"*.
2. **Docstring daraltildi.** Modul docstring'ine yeni bir bolum eklendi
   ("Kabul edilen deger alani -- dpi_scale >= 1.0 ZORUNLUDUR") ve "Round-trip
   kararliligi" bolumundeki "HER ZAMAN dogru" cumlesi artik acikca "modulun
   kabul ettigi HER `r` icin (yani `r.dpi_scale >= 1.0`)" diye nitelendi.
   Ispat taslagindaki "s >= 1 olcek olsun" varsayiminin artik validasyon
   tarafindan ZORLANDIGI, yani ispatin varsaydigi alan ile kodun kabul
   ettigi alanin birebir ortustugu acikca yazildi. Iki fonksiyonun
   docstring'lerindeki `Raises:` bolumleri de ayni gerekceyle guncellendi.

Ilke ("bir garanti, kabul edilen girdi kumesinin TAMAMINDA tutmali") artik
saglaniyor: alan daraltildi (validasyon) VE iddia bu daraltilmis alana gore
ifade edildi (docstring) -- sessiz kabul bitti, belge durust.

## Regresyon testi (zorunlu, eklendi)

`tests/unit/capture/test_dpi.py` icine:

- `test_scale_below_one_is_rejected_not_silently_broken_REGRESSION` --
  tester'in TAM raporladigi ornegi (`Rect(x=3,y=3,w=3,h=3,dpi_scale=0.5)`)
  kullanarak hem `logical_to_physical` hem `physical_to_logical`'in artik
  `ValueError` firlattigini dogrudan dogrular. Bu test o kusurun bir daha
  sessizce geri gelmedigini garanti eder.
- `test_scale_below_one_systematically_rejected_across_range_REGRESSION` --
  tester'in sistematik olcumune (`(0,1)` araliginda ~%50/%68.6 sessiz
  bozulma) karsilik, 7 farkli `(0,1)` degeriyle parametrize, hepsinin
  reddedildigini dogrular.
- Mevcut `test_..._rejects_non_positive_scale` testleri
  `test_..._rejects_scale_below_one` olarak yeniden adlandirilip
  `[0.0, -1.0, -0.5, 0.5, 0.75, 0.99, 0.999999]` ile genisletildi ve hata
  mesajinin icerigi de (`match=r"dpi_scale >= 1\.0"`) dogrulaniyor.

Toplam test sayisi 133 -> **149** (16 yeni test: 2 regresyon + genisletilen
2 parametrize testin ek degerleri).

## Ek not (bloke etmeyen, tester'in onerisi)

Negatif genislik/yukseklik davranisi artik modul docstring'inde acikca
belgeli ("Negatif genislik/yukseklik -- guvenli ele alinir, cokme yok"): hicbir
fonksiyon cokmuyor, `intersect`/`clamp_to_monitor` -> `None`, `classify_region`
-> `OUTSIDE`. Ayri bir test eklenmedi (tester bunu zorunlu tutmadi, mevcut
testler bu yollari dolayli kapsiyor); `known_gaps`'te seffaf sekilde belirtildi.

## Kanit

- `.agents/tasks/T-003/evidence/mypy-r2.txt` -- `mypy --strict`, cikis 0.
- `.agents/tasks/T-003/evidence/pytest-r2.txt` -- `pytest -q`, **149 passed**,
  cikis 0.
- `.agents/tasks/T-003/evidence/repro-r2.txt` -- tester'in tam raporladigi
  ornek (`Rect(3,3,3,3,dpi_scale=0.5)`) artik her iki fonksiyonda da
  `ValueError` firlatiyor (ham cikti dosyada); karsilastirma icin ayni
  ornegin gecerli bir olcekle (`dpi_scale=1.5`) round-trip'inin hala kararli
  oldugu da gosteriliyor.

## Yazma yetkisi

Yalnizca izin verilen dosyalar degistirildi: `src/capture/dpi.py`,
`tests/unit/capture/test_dpi.py`, `.agents/tasks/T-003/delivery.md`,
`.agents/tasks/T-003/evidence/*`. `src/capture/__init__.py`,
`src/capture/change_detector.py`, `src/contracts/**`,
`.agents/tasks/T-003/tester_tests/**`, `tester_evidence/**` -- DOKUNULMADI.

## Kendi dogrulamam

`python .agents/validate.py .agents/tasks/T-003/delivery.md` -> asagida.
