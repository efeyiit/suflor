# T-008 tur 1 -- Tester-B geri bildirimi (mercek B: test kalitesi / mutant)

Tek bloke eden bulgu: **B-1 uzun etiket koprusu**. Mutant kiti (47 davranis + 6 kontrol x 5 kapi) baska bloke eden sinif bulmadi; kacan 3 mutant (M23/M40/M41) keskinlik sinifi, `verdict-B.md`'de.

## B-1 -- Iki satir yuksekliginde SOLDAKI etiket, iki satiri tek bloga fermuarliyor

**Yeniden uretim 1 (sentetik, OCR yok, 0.3 s):**

```
python -m pytest .agents/tasks/T-008/tester_B/test_mercek_B_ret.py -p no:cacheprovider -rfE -v
```

Ham cikti (`tester_B_evidence/RET-1-uzun-etiket-koprusu-sentetik.txt`):

```
test_ret_uzun_etiket_solda_iki_satiri_tek_bloga_almamali[satir2-x+5-fermuar] FAILED
    assert karisik == [], f"farkli satirlar tek blokta: {karisik}; cikti {metinler}"
E   assert ['T a d b e c f'] == []
test_ret_uzun_etiket_solda_iki_satiri_tek_bloga_almamali[satir2-x-ayni] FAILED
E   assert ('a b c' in 'T a | b | c | d | e | f')
test_ret_uzun_etiket_solda_iki_satiri_tek_bloga_almamali[satir2-x+12] FAILED
E   assert ['T a d b e c f'] == []
test_ret_pozitif_kontrol_etiketsiz_iki_satir_dogru PASSED
3 failed, 1 passed
```

Fixture (hepsi `monitor_index=0`, `dpi_scale=1.0`, `confidence=0.9`):

```
T = Rect(0, 0, 40, 60)                      # etiket: iki satiri kapsar, x ve y en kucuk
satir 1: a(50,5,50,20) b(110,5,50,20) c(170,5,50,20)
satir 2: d(50+k,40,50,20) e(110+k,40,50,20) f(170+k,40,50,20)   k = 5 / 0 / 12
```

Mevcut cikti: `k=5` ve `k=12` -> TEK blok `"T a d b e c f"` (7 parca; iki satirin kelimeleri
x sirasinda birbirine gecmis). `k=0` -> `"T a" | "b" | "c" | "d" | "e" | "f"` (satirlar tek
kelimeye bolunmus: kelime-kelime ceviri, S3 sinifi). Etiket olmadan ayni geometri
`"a b c" | "d e f"` (pozitif kontrol gecer) -- sebep etikettir.

**Yeniden uretim 2 (gercek OCR, sefin 13:11 `real_check`, commit 432a87c):**

```
python .agents/tasks/T-008/real_check.py
  IHLAL  [1c] etiket koprusu: 11 kutu -> 1 blok, en buyuk blok 11 parca (>= 2 blok, <= 6 parca; v1: 1 blok/11 parca)
REAL_CHECK: 1 IHLAL
```

(`tester_B_evidence/taban-3b-real_check-sef-13-11-surumu-1c.txt`; diger 14 kontrol ok.)

**Kok neden (kod):** `_satirlara_bol` satir uyeligini satirin ILK bloguyla, `_gruplara_bol`
dikey ortusmeyi grubun ILK bloguyla olcuyor. Etiket `(y,x)` sirasinda ilk oldugu icin
iki satirin her kutusu onunla ortusur; satir ici `(x,y,idx)` siralamasi iki satiri
birbirine gecirir; `_yatay_komsu` yalniz `son` bloga gore x ilerleme + bosluk soruyor
(bosluk negatif -> gecer). Sonuc: farkli satirlardan parcalar tek blokta.

**Beklenen (degismez, mekanizmasiz):** Bir cikti blogunun `line_boxes` parcalari **ikili
olarak** dikey ortusmeli (`>= DIKEY_ORTUSME_ESIGI * min(h)`); farkli satirlardan parcalar
tek blokta OLMAZ. Iki satirin kelimeleri kendi icinde birlesik kalir (`"a b c"`, `"d e f"`).
Etiketin nereye gidecegi (ayri blok mu, ust satira mi) bu bulgunun konusu degil; sefin
`sef_karari-tur2.md`'si mekanizmayi secer. `real_check` #1c: `>= 2 blok`, en buyuk blok
`<= 6 parca`.

**Test dosyasinda bayatlayacak olan (§4.6/5):** `test_k2_grup_icinde_dikey_ortusme_grubun_ilk_bloguyla`
uzun kutuyu ORTAYA (x=60) koyar; grubun ilk blogu kisa `a` kalir, `c` ayri kalir ve test
gecer -- erisilebilir geometri (etiket solda) olculmuyor. Duzeltmeyle bu testin beklentisi
(`["a T", "c"]`) buyuk olasilikla degisir; yeniden yazilirken fixture'a **etiket solda**
varyanti eklenmeli (yukaridaki 7 kutu) ve assert degismez uzerinden yazilmali (parcalar
ikili dikey ortusmeli), `"grubun ilk blogu"` uzerinden degil. Mutant kitinde M16/M17/M18
(satir/grup referansi) bu testle yakalaniyordu; tur 2'de yeniden nisanlanir.

## Tur 2 icin mutant yukumlulugu (kit hazir)

```
T008_TB_DRY=1 T008_TB_SCRATCH=<scratch> python .agents/tasks/T-008/tester_B/mutant_kiti.py      # yama hedefleri yeni kaynakta hala tekil mi
T008_TB_SCRATCH=<scratch> python .agents/tasks/T-008/tester_B/mutant_kiti.py --taban --jsonl <dosya>   # 47 + 6, bes kapi
```

Kacan 3 sinif icin hazir olculer (`tester_B/test_mercek_B.py`, `test_b1_ek_*`): ayni-x
farkli-y permutasyon (M41), birlesik grup vs tekil bag (M40), uyumluluk ideografi (M23).
Sef isterse teslim dosyasina tasinir.
