---
task: T-008
role: tester
round: 2
decision: onay
checks:
  - name: "taban 1 -- mypy --strict temiz (modul + test dosyasi)"
    cmd: "python -m mypy --strict --explicit-package-bases src/ocr/satir_birlestirici.py; ... tests/unit/ocr/test_satir_birlestirici.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-taban-1-mypy.txt
  - name: "taban 2 -- birim 76 passed"
    cmd: "python -m pytest tests/unit/ocr/test_satir_birlestirici.py -q -p no:cacheprovider -rfE"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-taban-2-pytest.txt
  - name: "taban 3 -- real_check TEMIZ 15/15 (#1c 11 kutu -> 2 blok, en buyuk 6 parca); PYTHONIOENCODING yok"
    cmd: "python .agents/tasks/T-008/real_check.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-taban-3-real_check.txt
  - name: "taban 4 -- kapsam %100 (100 ifade, 0 eksik)"
    cmd: "python -m pytest tests/unit/ocr/test_satir_birlestirici.py -q -p no:cacheprovider --cov=src.ocr.satir_birlestirici --cov-fail-under=95 --cov-report=term-missing"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-taban-4-kapsam.txt
  - name: "taban 5 -- tam takim 1444 passed"
    cmd: "python -m pytest tests -q -p no:cacheprovider -rfE"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-taban-5-tum-takim.txt
  - name: "B2-1 -- kit kuru kosum: 61 yama hedefi (53 davranis + 8 kontrol) tur 2 kaynaginda tekil ve derlenir (M16 yeniden nisanlandi; M48-M53, C-7/C-8 yeni)"
    cmd: "T008_TB_DRY=1 T008_TB_SCRATCH=<scratch> python .agents/tasks/T-008/tester_B/mutant_kiti.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-B2-1-kit-kuru-kosum-yama-hedefleri.txt
  - name: "B2-1 -- parti 1 (ayna taban 5/5 + tur 2 odakli 11 mutant): M48 E-geri 5 test + #1c, M49 en uzun 6 + #1c, M50 bag <= 1, M51 tur 1 lafzi 5 + #1c + mypy, M52 yanlis boyut (w) 3 (yalniz sentetik), M53 bir onceki 2, M16/M17/M18 yeniden nisan 2/2/1, M41 (x,idx) 2; M37 (-idx) KACTI (tahmin edilmisti)"
    cmd: "T008_TB_SCRATCH=<scratch> python .agents/tasks/T-008/tester_B/mutant_kiti.py --taban --jsonl tester_B_evidence/r2-B1-mutant-kiti.jsonl M48 M49 M50 M51 M52 M53 M37 M41 M16 M17 M18"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-B1-mutant-kiti-parti1.txt
  - name: "B2-1 -- parti 2 (M01-M15): 15/15 yakalandi"
    cmd: "T008_TB_SCRATCH=<scratch> python .agents/tasks/T-008/tester_B/mutant_kiti.py --jsonl ... M01 ... M15"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-B1-mutant-kiti-parti2.txt
  - name: "B2-1 -- parti 3 (M19-M36): 17/18 yakalandi, M23 (uyumluluk ideografi) KACTI (tur 1 ile ayni)"
    cmd: "T008_TB_SCRATCH=<scratch> python .agents/tasks/T-008/tester_B/mutant_kiti.py --jsonl ... M19 ... M36"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-B1-mutant-kiti-parti3.txt
  - name: "B2-1 -- parti 4 (M38-M47 + 8 kontrol): 8/9 yakalandi, M40 (bag max idx) KACTI (tur 1 ile ayni); 8/8 kontrol kacti (yanlis pozitif yok)"
    cmd: "T008_TB_SCRATCH=<scratch> python .agents/tasks/T-008/tester_B/mutant_kiti.py --jsonl ... M38 M39 M40 M42 ... M47 C-1 ... C-8"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-B1-mutant-kiti-parti4.txt
  - name: "B2-1 -- ozet tablo: 53 davranis mutanti 50 yakalandi / 3 kacti (M23, M37, M40); 8/8 kontrol kacti; kapi basina G1 1, G2 50, G3 12, G4 50, G5 50; yalniz real_check ile yakalanan 0; yalniz sabit-pin testiyle yakalanan 0"
    cmd: "python .agents/tasks/T-008/tester_B/b1_ozet_tablo.py tester_B_evidence/r2-B1-mutant-kiti.jsonl"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-B1-mutant-kiti-ozet-tablo.txt
  - name: "B2-1b -- implementer C-3 (`-idx`, eski M04) DAVRANIS-ESDEGER DEGIL: ayni (y,x) farkli h cift + komsu satir: [R,s,a,D] orijinal ['R s','D','a'] / -idx ['R','D','s','a']; sinif-ici 3000 rastgelede 264 ayrisma. Ayni ornekte docstring K6 'bag ... satir uyeligini DEGIL' cumlesi de yanlis (orijinal kod: [R,s,a,D] != [R,a,s,D])"
    cmd: "python .agents/tasks/T-008/tester_B/b2_1b_idx_esdeger_mi.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-B2-1b-idx-mutanti-esdeger-degil.txt
  - name: "B2-1c -- AYIRT ETME (ayna): kacan 3 mutant x {teslim, mercek-B}: teslim 3/3 `.` (kitle tutarli), mercek-B 3/3 `X` (M37 icin yeni pin testi); taban 76 + 41 passed 1 xfailed"
    cmd: "T008_TB_SCRATCH=<scratch> python .agents/tasks/T-008/tester_B/b1c_ayirt_etme.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-B1c-kacan-ayirt-etme.txt
  - name: "B2-2 -- ETIKET_KOPRU_GEOMETRI gercek motorla BAGIMSIZ betikle yeniden uretildi: 11/11 birebir ayni (tespitci sirasinda); satir kumeleri {1..5},{6..10} ve [6,5]/[5,5] uygulamasiz y-kumelemeyle turetildi, teslimle ayni; etiket iki satirla da ortusuyor (35, 18 >= 0.5*min h), satirlar arasi 10 px, ayni-x cifti 0"
    cmd: "python .agents/tasks/T-008/tester_B/b2_etiket_geometri_gercek_ocr.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-B2-2-etiket-geometri-gercek-ocr.txt
  - name: "B2-2/B2-3/B2-4 -- mercek-B 42 passed + 1 strict xfail (bulgu): totoloji taramasi 76 testte (assert var, sabit/kendine-esit yok, yalniz-kendine-bagli listesi degismedi: 3), esik ikinci parametre noktalari, saflik AST, id+==, 100 rastgele x2 + permutasyon, iki surec PYTHONHASHSEED, 1000 blok 4 yerlesim, 1k->10k oran, 100k, pragma yok, bariyer her testte; yeniden nisan: en az 68 + tur 1'in 45 korunan adi + 3 eski ad yok + 9 yeni ad var"
    cmd: "python -m pytest .agents/tasks/T-008/tester_B/test_mercek_B.py .agents/tasks/T-008/tester_B/test_mercek_B_ret.py -p no:cacheprovider -rfEx -v"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-B2-B5-mercek-testleri.txt
  - name: "B2-3 -- olcekleme (tur 2 kodu): 1000 blok 1.3-3.0 ms; 10k/1k 12.1-13.4 (n log n ~13); 100k/10k 11.1-20.3 (karesel ~100 degil); 100k rastgele 654 ms"
    cmd: "python .agents/tasks/T-008/tester_B/b3_olcekleme.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-B3-olcekleme.txt
  - name: "B2-4 -- sefin bariyeri teslim dosyasi kosarken 76/76 setup'ta meta_path[0], import 76/76 kesildi, yasak kok sys.modules 0 (gozlem eklentisi, ayri surec)"
    cmd: "TB_GOZLEM=<json> PYTHONPATH=.agents/tasks/T-008/tester_B python -m pytest tests/unit/ocr/test_satir_birlestirici.py -q -p no:cacheprovider -p tb_gozlem_plugin"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-B4-bariyer-76-76-gozlem.txt
  - name: "B2-4 -- sefin dizini + mercek-B birlikte iki sirada: 366 passed + 1 xfailed / 366 + 1"
    cmd: "python -m pytest tests/unit/ocr .agents/tasks/T-008/tester_B -q -p no:cacheprovider -rfEx  (+ ters sira)"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-B5-birlikte-kosum-sef-ve-tester-B.txt
  - name: "B2-5 -- T2-1 etki alani, tur 1 (fe01641) vs tur 2 diferansiyel: ETIKETSIZ 3000 KR-sinifi yerlesimde ayrisma 0 (regresyon yok); ETIKETLI 3000'de 1852 ayrisma (pozitif kontrol); DEGISMEZ taramasi etiketli 3000: tur 2'de iki satir karisan blok 0 / parcalanan satir 0, tur 1'de 251 / 3210 (1815 ihlalli yerlesim); KR 17 -> [2,5,5,5] iki surumde ayni"
    cmd: "python .agents/tasks/T-008/tester_B/b2_5_tur1_vs_tur2_diferansiyel.py  (tur 1 kaynagi git show fe01641 ile)"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-B2-5-tur1-vs-tur2-diferansiyel.txt
  - name: "RET-1 (tur 1 olcusu) tur 2 koduyla: 4/4 GECIYOR (3 kayma + etiketsiz pozitif kontrol)"
    cmd: "python -m pytest .agents/tasks/T-008/tester_B/test_mercek_B_ret.py -p no:cacheprovider -rfE -v"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-B2-B5-mercek-testleri.txt
  - name: "depo dokunulmadi: git status --short -- src tests real_check packet BOS; git diff HEAD -- src tests 0 satir; kaynak/test sha256 ayna ile ayni (HEAD 019b9ae; satir_birlestirici son degisim ef397e3)"
    cmd: "git status --short -- src tests .agents/tasks/T-008/real_check.py .agents/tasks/T-008/packet.md; sha256sum ..."
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/r2-git-status-src-tests.txt
blocking_issues: []
---

# T-008 tur 2 -- Tester-B (mercek B: test kalitesi, saflik, mutant)

Karar: **ONAY**. Tur 1'in bloke eden bulgusu B-1 (sol uzun etiket koprusu) kapandi: kendi ret olcum 4/4 geciyor, `real_check` #1c kendi elimle TEMIZ (11 -> 2 `[6,5]`), gercek geometri gomulu testi bagimsiz kanaldan dogrulandi. Mutant kriteri (urunu bozan VE erisilebilir mutant bes kapidan geciyor mu) **karsilaniyor**: 53 davranis mutantinin 50'si yakalandi; kacan 3'u (M23, M37, M40) keskinlik sinifi, hicbiri gercek fixture'larda erisilebilir degil (ayni-(y,x) cifti gercek KR 17'de ve etiket 11'de 0). Tur 1'e gore: M41 (ayni-x cifti) artik yakalaniyor (T2-2 fixture'i, 2 test); **M37 (`-idx`) tur 1'de yakalanirken simdi kaciyor** -- ve implementer'in onu "davranis-esdeger kontrol" diye yeniden siniflamasi YANLIS (asagida, bloke etmez). `tester_A/` okunmadi; `delivery.md` ve `sef_karari-tur2.md` gorev metninin talimatiyla okundu.

## B2-1 -- Kit yeniden kosum (ayna agaci, bes kapi; `tester_B/mutant_kiti.py` 61 mutant)

Tur 2 kaynaginda tur 1'in `SATIR_UYELIK` hedefi yok (T2-1); M16 yeniden nisanlandi (referans = SON EKLENEN), M48-M53 ve C-7/C-8 eklendi; tahminler kosumdan once yazildi. Tam tablo `r2-B1-mutant-kiti-ozet-tablo.txt`.

| mutant | ne | sonuc | G2'de dusen |
|---|---|---|---|
| M48 | E geri: referans satirin ILK blogu (guncelleme yok, tur 1 kodu) | .XXXX (#1c IHLAL 11 -> 1) | 5 (3 sentetik kayma + gercek geometri + kisa alt kutu) |
| M51 | tur 1 lafzi birebir (`satirlar[-1][0]`, referans guncellenir ama kullanilmaz) | XXXXX (mypy `union-attr` de) | 5 (M48 ile ayni -- capraz dogrulama) |
| M49 | referans EN UZUN (`<` -> `>`) | .XXXX (#1c IHLAL) | 6 (ustteki 5 + `k6_bagli_..._en_kisa`) |
| M50 | bag `<=` (esit yukseklikte son kisa blok) | .X.XX | 1 (`k2_satir_bolumleme_..._referansiyla`) -- "bag: ilk" olculuyor |
| M52 | referans yanlis boyutla (en DAR `w`, `h` degil) | .X.XX | 3 -- **yalniz sentetik**; gercek geometri testi ve #1c GECER (etiket w=125 > ilk kelime w=59: referans zaten ilk kelimeye kayar) |
| M53 | uyelik bir ONCEKIYLE (referans kullanilmaz) | .X.XX | 2 (M16 ile ayni) |
| M16/M17/M18 | son eklenen / grup referansi son / grup ici dikey denetim yok (yeniden nisan) | .X.XX | 2 / 2 / 1 |
| M41 | T2-2 `(x, idx)` y'siz | .X.XX | 2 (`k6_ayni_x_farkli_y` + `k6_cikti_anahtarinda_bag`) -- tur 1'de kaciyordu |
| **M37** | `-idx` (ilk siralamada bag ters; implementer C-3) | **.....** | 0 -- tur 1'de 1 testle yakalaniyordu (o test yeniden nisanlandi) |
| M23 / M40 | uyumluluk ideografi / bag max idx | ..... | 0 (tur 1 ile ayni) |
| M01-M15, M19-M22, M24-M36, M38-M39, M42-M47 | tur 1 kiti | hepsi yakalandi | -- |
| C-1..C-8 | 8 kontrol (C-7 = implementer C-2 min arguman takasi; C-8 uyelik ortusme argumanlari simetrik) | ..... x8 | yanlis pozitif yok |

Kapi basina: G1 1/53 (yalniz M51), G2 50/53, G3 12/53, G4 50/53, G5 50/53; yalniz real_check ile yakalanan yok; yalniz sabit-pin testiyle yakalanan yok. Tahminden sapan: M51 (mypy de yakaladi), M07/M26 (tur 1'deki ayni G3 sapmasi).

**B2-1b -- implementer'in 3 kontrolu:** C-1 (`(y,x,idx)` -> `(y,x)`, kararli sort) ESDEGER (benim C-1, kacti); C-2 (min arguman takasi) ESDEGER (benim C-7, kacti); **C-3 (`-idx`, eski M04) ESDEGER DEGIL.** Teslim "bagli ciftin isleme sirasi ne satir uyeligini ne referansi degistirir (ikisi de satira girer)" diyor; "ikisi de satira girer" varsayimi bagli ciftin yukseklikleri farkliyken tutmuyor: R(0,0,95,20) satir 0, D(160,0,50,20) sagda, s(100,15,50,8) kisa ve a(100,15,50,20) uzun AYNI (y,x). Kisa s once islenirse R'nin referansiyla 5 >= 0.5*8 ortusur, satira girer ve referans olur; a onunla 8 >= 4 ortusup ayni satira girer -> `"R s","D","a"`. a once islenirse R ile 5 < 10 -> yeni satir; s ona katilir -> `"R","D","a","s"`. `-idx` isleme sirasini tersler: 3000 sinif-ici rastgelede 264 ayrisma. "0 test duser" burada esdegerligi degil, fixture kumesinin bu dala ugramadigini olcuyor (§4.6/10). Ayni ornek **docstring K6'nin T2-3'te yeni yazilan cumlesini** de bosa cikariyor: "Bag yalniz cikti SIRASINI etkiler, satir uyeligini DEGIL" -- orijinal kodda `[R,s,a,D]` ve `[R,a,s,D]` farkli satir bolumlemesi veriyor. Erisilebilirlik: ayni (x,y) baslangicli farkli yukseklikte iki kutu = cift tespit; gercek KR 17 ve etiket 11'de ayni-(y,x) cifti 0, satir araligi >= 10 px. **Urunu bozmuyor -> bloke etmez**; ama teslimdeki iki cumle (esdegerlik + docstring) yanlis ve sefin sondasi ("Kabul") bunu kendi eliyle uretmeden almis (§4.6/6). Hazir olculer `tester_B/test_mercek_B.py`: `test_b1_ek_k6_ayni_yx_farkli_h_cift_ters_idx_mutanti_sinir_pini` (mevcut davranisi girdi sirasiyla pinler, M37'yi yakalar) ve `test_b2_docstring_k6_bag_sirasi_satir_uyeligini_degistirmez_iddiasi` (docstring iddiasi; **strict xfail** -- mekanizma degisirse XPASS ile haber verir).

## B2-2 -- Totoloji, 8 yeni test ve gomulu geometri

- `ETIKET_KOPRU_GEOMETRI`: **bagimsiz betikle** (`b2_etiket_geometri_gercek_ocr.py`, implementer'in betigi kullanilmadi) gercek motordan yeniden uretildi: 11/11 birebir ayni, tespitci sirasinda. Referans uygulamanin ciktisindan turetilmemis (§4.6/8).
- `[6,5]` ve `ETIKET_KOPRU_SATIRLAR` ({1..5}, {6..10}): uygulama cagrilmadan y-orta kumelemeyle turetildi, teslimle ayni. Geometrik olgular: etiket (57,55,125,72) her iki satirla da `>= 0.5*min h` ortusuyor (35 ve 18) -> "ilk"/"en uzun" referans kopruler (M48/M49/M51 #1c ile dogruladi); satirlar arasi bosluk 10 px (kisa alt kutu siniri erisilmez); etiket solda ve y en kucuk.
- 8 yeni/yeniden nisanlanan testin hepsi bagimsiz literal beklentiye ya da geometriden turetilen degismeze (`_satir_dagilimi`: `line_boxes` -> cizilen satir indeksi) bagli; yalniz-kendine-bagli liste degismedi (tur 1'deki 3). `..._gercek_geometri_11_kutu` icindeki `reversed == cikti` kendine bagli ama ayni testte `[6,5]` ve dagilim cipasi var.
- `test_k2_satir_referansi_en_kisa_blok_kisa_alt_kutu_siniri_sabitlendi` bilinen ZAYIF davranisi sabitliyor (aralik 26 -> parcalanir) -- belge olcusu, degismez degil; docstring'de `[ÖLÇÜLMÜYOR]` gerekceli. Kabul.
- Bilgi: gercek geometri testi + #1c, "en kisa h" mekanizmasini "en dar w"den (M52) AYIRAMIYOR; sentetik 3 kayma ayiriyor. Iki olcu birlikte yeterli; tek basina gercek geometriye yaslanilmamali.

## B2-3 -- Saflik / determinizm / olcek (tur 2 kodu)

AST bagimsiz denetim temiz; girdi degismezligi `id` + `==` (61 blok, NaN/iki monitor/iki dpi/yozlasmis); 100 rastgele x2 + karistirilmis kopya esit; iki surec PYTHONHASHSEED=1/2 birebir; 1000 blok 1.3-3.0 ms (4 yerlesim); 10k/1k 12.1-13.4 (n log n); 100k/10k 11.1-20.3 (hepsi-bagli 20.3: dogrusal-ustu, karesel degil); 100k rastgele 654 ms. Referans guncellemesi O(1)/blok, karmasiklik degismedi.

## B2-4 -- Bariyer

76/76 setup'ta `meta_path[0]` sefin bariyeri, import 76/76 kesildi, yasak kok 0. Iki bariyer iki sirada 366 + 1 xfail / 366 + 1 xfail.

## B2-5 -- Oranti ve T2-1'in etki alani

Esik "urunu bozan VE erisilebilir mutant bes kapidan geciyor": **karsilanmiyor** (kacan 3'u de keskinlik sinifi; gercek fixture'larda erisilebilir degil). Ret icin sebep yok; tur 3'e gitmez. T2-1'in etkisi dar ve olculdu: tur 1 (fe01641) vs tur 2 diferansiyel, KR-sinifi (h 26-41 titresimli, satir araligi >= 10) 3000 etiketsiz yerlesimde **0 ayrisma** (regresyon yok), 3000 sol-etiketli yerlesimde 1852 ayrisma (pozitif kontrol); degismez taramasi ("hicbir blok iki satirdan kelime tasimaz" ve "her satir tek blokta") tur 2'de **0/0**, tur 1'de 251/3210 (1815 ihlalli yerlesim). KR 17 -> `[2,5,5,5]` iki surumde ayni.

## Yeniden nisanlananlar (§4.6/5, kendi dosyalarim)

`test_b2_teslim_68_test_topluyor` -> `test_b2_teslim_en_az_68_test_topluyor_dusen_yok_yeniden_nisan_adlari` (en az 68; tur 1'in 45 korunan fonksiyon adi gomulu, hicbiri sessizce dusmedi; 3 eski ad yok, 4 yeni + 5 tur 2 adi var). `test_b5_..._68_68_aktif` -> `..._her_testte_aktif` (setup >= 68, dort sayac setup'a esit). `b1c_ayirt_etme.py` kacan listesi M23/M37/M40. Kit: M16 yeniden nisan, M48-M53, C-7/C-8, M37 aciklamasi.

## Sefe bulgular (bloke etmeyen)

1. **Implementer C-3 (`-idx`) esdeger degil; docstring K6 "satir uyeligini DEGIL" cumlesi yanlis** (B2-1b, kanit `r2-B2-1b-*`). Oneri: teslimdeki kit tablosu "23/23 + 3 kontrol" degil "23 yakalandi / 1 kacti (keskinlik) + 2 kontrol" olarak duzeltilsin; docstring cumlesi daraltilsin ("bagli ciftin yukseklikleri farkliysa ve kisa olan komsu satirin referansiyla ortusuyorsa uyelik girdi sirasina baglidir -- cift tespit sinifi, gercek OCR'da `[ÖLÇÜLMÜYOR]`"). Mekanizma degisikligi (orn. bagda `h` ile siralama) sef karari; gerekli DEGIL. Belge-yalniz duzeltme, kod yolu degismez.
2. M23 (uyumluluk ideografi) ve M40 (bag max idx) tur 1'deki gibi kaciyor; hazir olculer `test_b1_ek_*`'de. Keskinlik.
3. Gercek geometri olcusu "en kisa h"yi "en dar w"den ayiramiyor (M52); sentetik olcu tasiyor. Bilgi.
4. `real_check` gercek-OCR sayilarina pinli (17 / [2,5,5,5] / 11 / 4) -- tur 1 bulgusu, degismedi.
5. Olcek: 100k/10k hepsi-bagli yerlesimde 20.3 (tur 1 rastgele 23.7) -- karesel degil, butce 15x payla tutuyor.
