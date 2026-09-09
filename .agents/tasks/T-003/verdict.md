---
task: T-003
role: tester
round: 2
decision: onay
checks:
  - name: "mypy --strict temiz (kabul komutu)"
    cmd: "python -m mypy --strict src/capture/dpi.py"
    exit_code: 0
    result: gecti
    evidence: tester_evidence/r2-mypy.txt
  - name: "implementer test paketi geciyor (kabul komutu)"
    cmd: "python -m pytest tests/unit/capture/test_dpi.py -q"
    exit_code: 0
    result: gecti
    evidence: tester_evidence/r2-pytest_acceptance.txt
  - name: "tester'in bagimsiz test paketi (tur-1'den guncellenmis + tur-2 ek testleri, tester_tests/)"
    cmd: "python -m pytest .agents/tasks/T-003/tester_tests -q"
    exit_code: 0
    result: gecti
    evidence: tester_evidence/r2-pytest_tester_tests.txt
  - name: "bagimsiz testlerin -vv (tam) cikisi"
    cmd: "python -m pytest .agents/tasks/T-003/tester_tests -q -vv"
    exit_code: 0
    result: gecti
    evidence: tester_evidence/r2-pytest_tester_tests_verbose.txt
  - name: "bagimsiz regresyon taramasi (yeni tohum 424242, tur-1'den farkli ornekleme -- (0,1) sessiz-kabul kontrolu, s>=1.0 icin 300k round-trip, sinir (1.0/0.999999/1.0000001), hata mesaji kalitesi, negatif-koordinatli monitor, karisik DPI, classify_region matrisi, determinizm, sozlesme degismezligi)"
    cmd: "python .agents/tasks/T-003/tester_evidence/r2_independent_regression_sweep.py"
    exit_code: 0
    result: gecti
    evidence: tester_evidence/r2-independent_regression_sweep_output.txt
blocking_issues: []
---

# Verdict — T-003 (round 2)

## Yontem

Kor calisildi: `delivery.md` ve `evidence/` **okunmadi** (kural geregi). Okunanlar:
`feedback.md`, `verdict.md` (tur 1, tester A yazdi), `packet.md`, `env.md`,
`.agents/PROTOKOL.md` §4, `src/contracts/models.py`, tasarim dokumani §5.1/§5.3/
§5.6/§8.3, **kodun kendisi** (`src/capture/dpi.py`, `tests/unit/capture/test_dpi.py`).

Sef'in uyguladigi karar (feedback.md'deki iki secenegin IKISI BIRDEN) `dpi.py`'de
dogrulandi:

1. `logical_to_physical` ve `physical_to_logical`, `rect.dpi_scale < 1.0` icin
   `ValueError` firlatiyor (yalnizca `<= 0` degil).
2. Modul docstring'indeki round-trip iddiasi artik "modulun kabul ettigi HER
   girdi icin (yani `dpi_scale >= 1.0`)" diye acikca daraltilmis; ispat
   taslagi ile validasyonun kabul alani birebir ortusuyor.

## 1 · Kusur gercekten gitti mi -- EVET

Tur 1'in tam tekrar-uretim ornegi (`Rect(x=3,y=3,w=3,h=3,dpi_scale=0.5)`) artik
`ValueError: dpi_scale >= 1.0 olmali (...)` ile reddediliyor -- ne
`logical_to_physical` ne `physical_to_logical` sessizce yanlis sonuc
uretebiliyor.

Bagimsiz, yeni tohumla (424242, tur-1'in 908171'inden farkli) `(0,1)`
araliginda **40.000 rastgele (scale, x, y, w, h) kombinasyonu** tarandi
(hem `logical_to_physical` hem `physical_to_logical` icin ayri ayri):
**0 sessiz kabul**. Ayrica implementer'in kendi `test_dpi.py`'si de
`[0.0, -1.0, -0.5, 0.5, 0.75, 0.99, 0.999999]` icin ayni davranisi 149
testte dogruluyor.

## 2 · Regresyon var mi -- HAYIR

Bu turun en kritik kismi. Bagimsiz, implementer'inkinden ve tur-1
tester'ininkinden farkli rastgele ornekleme (`tester_evidence/
r2_independent_regression_sweep.py`, tohum 424242) ile `dpi_scale >= 1.0`
icin tur 1'de dogrulanmis HER iddia yeniden sinandi:

- **Round-trip** (`logical -> physical -> logical`): `[1.0, 10.0)` araliginda,
  genis rastgele (x,y,w,h) ile **300.000 deneme, 0 basarisizlik**.
- **Yuvarlama simetrisi**: `-1.000.000..1.000.000` araliginda **100.000
  rastgele deger, 0 asimetri** (`_round_half_away_from_zero` degismedi,
  beklendigi gibi).
- **Negatif koordinatli monitor** (sol, ust VE sol-ust kose, tur-1'den farkli
  bir monitor duzeniyle): 3 monitor x 2000 rastgele nokta = **6.000 iki yonlu
  round-trip, 0 basarisizlik**.
- **Karisik DPI** (1.0 / 1.75 / 2.25): uc monitorun fiziksel boyutlari
  birbirinden farkli ve dogru; `clamp_to_monitor` metadata'yi (dpi_scale,
  monitor_index) rect'in kendi (yanlis/eski) degerinden degil, monitorden
  aliyor -- degismedi.
- **`classify_region` sinir matrisi**: tur-1'den TAMAMEN farkli bir duzenle
  (dikey bitisik + araya bosluk birakilmis ucuncu monitor) INSIDE/PARTIAL/
  OUTSIDE siniflandirmasi **6/6 dogru**.
- **Determinizm ve saflik**: 7 fonksiyon, ayni girdiyle iki cagirimda ayni
  sonucu veriyor; `tester_tests/test_dpi_adversarial.py`'deki AST tabanli
  import/sinif denetimi (import allowlist, tek sinif = `RegionValidity`)
  hala geciyor -- duzeltme yalniz iki fonksiyonun giris denetimini ve
  docstring'i degistirmis, saflik/yapi bozulmamis.
- **Sozlesme degismezligi**: `Rect` hala frozen (dogrudan mutasyon istisna
  firlatiyor), donusler hala YENI nesne (`is not`), girdi hala degismiyor.

Sonuc: `dpi_scale >= 1.0` alaninda tur 1'de "tutuyor" diye isaretlenen
**hicbir seyin bozulmadigi** bagimsiz olarak dogrulandi.

## 3 · Bayat testler guncellendi -- EVET, `tester_tests/` tamamen yesil

Tur 1'in iki testi -- iddia edilen kusurun VAR OLDUGUNU dogrulayan
`test_round_trip_claim_as_documented_is_scale_ge_1_only_KNOWN_GAP` ve
`test_round_trip_fails_broadly_for_scale_below_one_quantified` -- artik
kod duzeldigi icin (ilki beklenmeyen `ValueError` ile, ikincisi de ayni
sekilde) kirmiziydi. Ikisi de **duzeltilmis davranisi dogrulayacak
sekilde guncellendi** (`_FIXED` soneki, eski bulgu tarihiyle birlikte
docstring'de belgelendi, testin KENDI ASSERTION'I artik `ValueError`
bekliyor):

- `test_round_trip_claim_as_documented_is_scale_ge_1_only_FIXED`
- `test_scale_below_one_systematically_rejected_across_range_FIXED`

Ayrica sefin talep ettigi ek sinamalar icin 4 yeni test eklendi
(`tester_tests/test_dpi_adversarial.py`, `_TUR2` sonekli):

- `test_scale_exactly_one_is_accepted_not_off_by_one_TUR2` -- `dpi_scale
  == 1.0` KABUL ediliyor (yanlislikla `<=` yazilmamis).
- `test_scale_just_below_one_is_rejected_TUR2` -- `0.999999` /
  `1.0 - 1e-9` REDDEDILIYOR.
- `test_scale_just_above_one_is_accepted_TUR2` -- `1.0000001` KABUL
  ediliyor.
- `test_value_error_message_explains_why_not_just_invalid_TUR2` -- hata
  mesaji sadece "invalid" degil; esik degeri (1.0) ve gelen gecersiz
  degeri metinde tasiyor, 20 karakterden uzun.

`python -m pytest .agents/tasks/T-003/tester_tests -q` -> **54 passed**
(48 tur-1 testi + 2 guncellenmis + 4 yeni), 0 basarisiz, 0 atlanmis.

## Ek sinama sonuclari (gorev metninde ozellikle istenen)

- **Hata mesaji "neden" acikliyor mu?** EVET. Mesaj: `"dpi_scale >= 1.0
  olmali (Windows olcekleri %100'un altina inmez ve s < 1 icin round-trip
  garantisi tutmaz), gelen: 0.5"` -- hem esik hem gerekce (ikili: Windows
  gercekciligi + matematiksel zorunluluk) hem gelen deger aciyor. Bu,
  §5.6'daki "bolge gecersiz" bandina donusecek bir mesaj icin yeterince
  bilgilendirici.
- **Sinir: `dpi_scale == 1.0` kabul, `0.999999` red?** EVET, dogrulandi
  (yukaridaki TUR2 testleri + bagimsiz sweep script'i, bolum 0b).
- **Docstring'in yeni iddiasi kodun davranisiyla birebir mi?** EVET.
  Docstring "modulun kabul ettigi HER `r` icin (`dpi_scale >= 1.0`)"
  diyor; kod da TAM bu alani kabul ediyor (`< 1.0` red, `>= 1.0` kabul).
  Kapsanmayan girdi kalmadi: `(0,1)` araligi artik kod tarafindan da
  reddediliyor, docstring de o araliktan hic bahsetmiyor (yalniz "s<1
  reddedilir" diyor) -- tutarli.

## env.md'deki 8 saldiri noktasi — tur 2 sonucu

1. **Round-trip iddiasi** — ARTIK KOSULSUZ DOGRU (kabul edilen tum girdi
   alaninda). Tur-1 bulgusu kapatildi.
2–8. **Degismedi, hala TUTUYOR** — tur 1'de dogrulanan yuvarlama simetrisi,
   negatif koordinatli monitor, karisik DPI, sinir durumlari (negatif w/h
   dahil, dokumantasyona da eklenmis), saflik, sozlesmeye saygi, tasarim
   dokumani uyumu (§5.6) bu turda bagimsiz yeniden sinandi ve hicbirinde
   regresyon bulunmadi (bkz. bolum 2).

## Sonuc

Tur 1'in tek blocking bulgusu gercekten ve dogru sekilde kapatildi;
bagimsiz genis rastgele/sinir-degeri sinamada regresyon bulunmadi;
`tester_tests/` tamamen yesil. **ONAY.**
