---
task: T-002
role: implementer
round: 2
status: tamamlandi
files_written:
  - src/capture/change_detector.py
  - tests/unit/capture/test_change_detector.py
commands:
  - cmd: "python -m mypy --strict src/capture/change_detector.py"
    exit_code: 0
    evidence: evidence/mypy-r2.txt
  - cmd: "python -m pytest tests/unit/capture/test_change_detector.py -q"
    exit_code: 0
    evidence: evidence/pytest-r2.txt
contract_change_request: false
known_gaps:
  - "Secilen strateji: izgarayi bolgeye gore KUCULT. `_block_mean_resize`, hedef hucre sayisini (out_h, out_w) girdinin kendi boyutuyla (h, w) sinirlar: eff_out_h=min(out_h,h), eff_out_w=min(out_w,w). Bu, h>=out_h ve w>=out_w oldugu (gercekci/buyuk bolgeler -- her zaman) durumda davranissiz (no-op) kalir; kucuk bolgelerde ise kova basina en az 1 piksel garanti eder (linspace+round icin out<=n oldugunda hicbir zaman cakisan/geriye-gitmeyen sinir uretilmedigi out in 1..24, n in out..999 araliginda ampirik olarak dogrulandi), boylece hem IndexError hem 0/0->NaN yapisal olarak imkansiz hale gelir. Reddedilen alternatifler: (a) bolgeyi izgara boyutuna doldurma/tekrarlama -- yatay dHash icin bilgi kazandirmiyor (tekrarlanan sutunlarin farki hep 0), yanlis bir guven verirdi; (b) kucuk bolgede pixel-pixel karsilastirmaya dusme -- packet madde 1'in acikca yasakladigi yontemi baska bir kod yolunda gizlice geri getirirdi, iki ayri karsilastirma semantigi (hash-tabanli + pixel-tabanli) debounce/esik mantigini karmasiklastirirdi."
  - "Yan etki: kucuk bolgelerde hash bit uzunlugu kuculuyor (hash_size*hash_size yerine eff_out_h*(eff_out_w-1) bit); ayni threshold=4 varsayilani daha az bit uzerinde daha 'toleransli' hale gelebilir -- kucuk bolgelerde algilama hassasiyeti dogal olarak dusebilir (asla cokme/NaN degil, her zaman gecerli bool). Ozel uc durum: w==1 (tek piksel genislikte bolge) icin izgara genisligi de 1'e kirpilir, dHash yalnizca yatay komsu hucre farkina baktigi icin (bkz. modul docstring 'Algoritma' bolumu) karsilastirilacak 2. sutun yok -> 0 bit -> o bolge icin has_changed ilk kareden sonra hep False doner. Bu implementasyon hatasi degil, geometrik bir sinir (1 px genislikte yatay turev tanimsiz); regresyon testinde (w=1,h=50 dahil) 'cokme yok/uyari yok/bool doner' kriterleriyle sinandi, algilama hassasiyeti iddia edilmedi."
  - "Tester'in bloke etmeyen iki notu docstring'e eklendi (duzeltme gerekmiyordu, yalnizca belgeleme istendi): (1) duz renk (tek renkli) tam ekran gecisi dHash icin gorunmez kalir -- yatay-komsu farkina dayanan algoritmanin matematiksel ozelligi. (2) periyodik-dosemeli icerik blok-ortalamali kucultmeyle kaydirmaya karsi algilamayi korlestirebilir -- gercek oyun metni bu kadar periyodik olmadigi icin pratikte bloke edici degil."
  - "Debounce, esik (<=, kapsayici), bolge sifirlama, aday iptali, butce davranislari DEGISTIRILMEDI -- yalnizca _block_mean_resize/_dhash duzeltildi. Buyuk bolge (600x200) regresyon testiyle (test_large_region_16x16_and_above_is_unaffected_by_small_region_clamp) ve mevcut tur 1 testlerinin tumunun (25/25) degismeden gecmesiyle dogrulandi."
  - "Teknik engel yok; sef onayi gerektiren yeni bagimlilik eklenmedi."
---

# T-002 Teslim Raporu -- TUR 2 (duzeltme)

## Kusur ve kok neden

Tur 1'de `_block_mean_resize`, hedef izgara (varsayilan `hash_size=8` ->
8x9 hucre) girdi bolgesinden BUYUK oldugunda (`h<8` veya `w<9`)
`np.add.reduceat` icin cakisan/geriye-gitmeyen kova sinirlari uretiyordu:
`h<5` veya `w<5` bandinda `IndexError` (cokme), `5<=h/w<hash_size(+1)`
bandinda sessiz `0/0 -> NaN` (`RuntimeWarning: divide by zero`). Sef'in
bagimsiz olcumu (`round.json`) ve tester'in `feedback.md`'si bunu birebir
dogruladi.

## Uygulanan duzeltme

`_block_mean_resize`, hedef hucre sayisini girdinin kendi boyutuna kirpar:
`eff_out_h = min(out_h, h)`, `eff_out_w = min(out_w, w)`. Bu tek satirlik
degisiklik:

- **Buyuk bolgelerde (gercekci durum, >=8x9) devreye girmez** -- `min(...)`
  her zaman `out_h`/`out_w`'yi secer, davranis BIREBIR ayni (regresyon yok).
- **Kucuk bolgelerde** kova basina en az 1 piksel garanti eder --
  `out<=n` oldugu surece `np.linspace(0,n,out+1).round()` hicbir zaman
  cakisan sinir uretmiyor (out=1..24, n=out..999 araliginda ampirik
  dogrulandi, bkz. asagida "Dogrulama" ve modul docstring'i). Yani hem
  `IndexError` hem `NaN` yapisal olarak imkansiz.

`_dhash` ve modul dokstring'i, kucuk bolgelerde hash uzunlugunun
kuculebilecegini (ve `w==1` uc durumunda 0 bit -> o bolge icin sabit "hic
degismedi" sonucunu) acikca belgeliyor -- bkz. `known_gaps`.

## Dogrulama

- `python -m mypy --strict src/capture/change_detector.py` -> `evidence/mypy-r2.txt` (exit 0)
- `python -m pytest tests/unit/capture/test_change_detector.py -q` -> `evidence/pytest-r2.txt` (exit 0, **434 passed**)
- Boyut taramasi 1x1..20x20 (400 kombinasyon) + 1x50/50x1/3x80/80x3 + hedefli
  regresyon testleri (1x1, 3x3, 5x5-8x8 bandi, 16x16/600x200 buyuk-bolge
  regresyonu, saf `_dhash` yardimcisi uzerinden 400 kombinasyon) ->
  `evidence/size-sweep-r2.txt` (409 passed, tumu `warnings.catch_warnings()`
  + `simplefilter("error")` altinda -- herhangi bir `RuntimeWarning`
  testi kirar).
- Butce yeniden olculdu: `evidence/budget-r2.txt` -- 600x200 gercekci
  bolgede `max=0.8301ms`, butce `5ms`'nin cok altinda (tur 1'de
  `max=0.6231ms`'ye kiyasla hafif sistem gurultusu farki, yapisal bir
  yavaslamayla ilgisi yok -- buyuk bolge yolunda eklenen tek islem bir
  `min()` karsilastirmasi).

## Dokunulmayanlar

`src/capture/__init__.py`, `src/capture/dpi.py`, `src/contracts/**`,
`.agents/tasks/T-002/tester_tests/`, `.agents/tasks/T-002/tester_evidence/`
-- hicbirine dokunulmadi (bkz. `git status` -- yalnizca `src/capture/`
(change_detector.py) ve `tests/unit/capture/` (test_change_detector.py)
altindaki sahip oldugum dosyalar degisti).
