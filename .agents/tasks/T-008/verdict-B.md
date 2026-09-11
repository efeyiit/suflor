---
task: T-008
role: tester
round: 1
decision: ret
checks:
  - name: "taban 1 -- mypy --strict temiz"
    cmd: "python -m mypy --strict --explicit-package-bases src/ocr/satir_birlestirici.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/taban-1-mypy.txt
  - name: "taban 2 -- birim 68 passed"
    cmd: "python -m pytest tests/unit/ocr/test_satir_birlestirici.py -q -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/taban-2-pytest.txt
  - name: "taban 3 -- real_check 12:38 surumu (14 kontrol, #1c YOK): TEMIZ, cp1254 konsol (PYTHONIOENCODING yok), [6] 2.9 ms"
    cmd: "python .agents/tasks/T-008/real_check.py   (12:38'de, commit 766e860 surumu)"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/taban-3-real_check.txt
  - name: "taban 3b -- real_check SEFIN 13:11 SURUMU (commit 432a87c, #1c etiket_kopru_KR.png): mevcut teslim kodunda IHLAL [1c] 11 kutu -> 1 blok, en buyuk blok 11 parca; diger 14 kontrol ok -- KENDI ELIMLE YENIDEN URETILDI (bloke eden B-1'in gercek-OCR ayagi)"
    cmd: "python .agents/tasks/T-008/real_check.py   (13:21'de, HEAD surumu)"
    exit_code: 1
    result: kaldi
    evidence: tester_B_evidence/taban-3b-real_check-sef-13-11-surumu-1c.txt
  - name: "taban 4 -- kapsam %100 (95 ifade, 0 eksik; pragma yok, kapsam yapilandirma dosyasi yok)"
    cmd: "python -m pytest tests/unit/ocr/test_satir_birlestirici.py -q -p no:cacheprovider --cov=src.ocr.satir_birlestirici --cov-fail-under=95 --cov-report=term-missing"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/taban-4-kapsam.txt
  - name: "taban 5 -- tam takim 1427 passed"
    cmd: "python -m pytest tests -q -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/taban-5-tum-takim.txt
  - name: "B1 -- mutant kiti parti 1 (ayna agaci taban 5/5 + M01-M12), bes kapi, real_check 12:38 surumu; 12/12 yakalandi"
    cmd: "T008_TB_SCRATCH=<scratch> python .agents/tasks/T-008/tester_B/mutant_kiti.py --taban --jsonl tester_B_evidence/B1-mutant-kiti.jsonl M01 ... M12"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/B1-mutant-kiti-parti1.txt
  - name: "B1 -- mutant kiti parti 2 (M13-M20; M21 kapilari kostu ama aciklama satiri cp1254 konsolda coktu -> kit stdout errors=replace ile duzeltildi, M21 parti 3'te yeniden); 8/8 yakalandi"
    cmd: "T008_TB_SCRATCH=<scratch> python .agents/tasks/T-008/tester_B/mutant_kiti.py --jsonl ... M13 ... M24"
    exit_code: 1
    result: gecti
    evidence: tester_B_evidence/B1-mutant-kiti-parti2.txt
  - name: "B1 -- mutant kiti parti 3 (M21-M33): 12/13 yakalandi, M23 (uyumluluk ideografi) KACTI"
    cmd: "T008_TB_SCRATCH=<scratch> python .agents/tasks/T-008/tester_B/mutant_kiti.py --jsonl ... M21 ... M33"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/B1-mutant-kiti-parti3.txt
  - name: "B1 -- mutant kiti parti 4 (M34-M46): 11/13 yakalandi, M40 (bag max idx) ve M41 (satir ici (x,idx)) KACTI"
    cmd: "T008_TB_SCRATCH=<scratch> python .agents/tasks/T-008/tester_B/mutant_kiti.py --jsonl ... M34 ... M46"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/B1-mutant-kiti-parti4.txt
  - name: "B1 -- mutant kiti parti 5 (M47 + kontrol C-1..C-6): M47 yakalandi, 6/6 kontrol KACTI (yanlis pozitif yok; C-1 = (y,x,idx)->(y,x) gorevin istedigi kontrol)"
    cmd: "T008_TB_SCRATCH=<scratch> python .agents/tasks/T-008/tester_B/mutant_kiti.py --jsonl ... M47 C-6 C-1 C-2 C-3 C-4 C-5"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/B1-mutant-kiti-parti5.txt
  - name: "B1 -- ozet tablo: 47 davranis mutanti 44 yakalandi / 3 kacti; 6/6 kontrol kacti; kapi basina G1 0, G2 44, G3 9, G4 44, G5 44; yalniz real_check ile yakalanan 0; yalniz sabit-pin testiyle yakalanan 0"
    cmd: "python .agents/tasks/T-008/tester_B/b1_ozet_tablo.py tester_B_evidence/B1-mutant-kiti.jsonl"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/B1-mutant-kiti-ozet-tablo.txt
  - name: "B1b -- kacan 3 mutant davranis-esdeger DEGIL: M23 ayristi (bosluk 0 -> 1), M40 monitorler arasi bag ayristi + tek yuzey 3000 rastgelede 438, M41 [b,a,c] ayristi + 3000'de 801"
    cmd: "python .agents/tasks/T-008/tester_B/b1b_kacan_ayirt.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/B1b-kacan-mutant-ayirt.txt
  - name: "B1b -- M23 erisilebilirlik: KR v4 tanima sozlugunde 76 uyumluluk ideografi VAR, JP v4'te 0 (ayri surec, yalniz sayim)"
    cmd: "PYTHONIOENCODING=utf-8 python - < (sozluk sayim betigi; cikti dosyada)"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/B1b-M23-erisilebilirlik-ocr-sozlugu.txt
  - name: "B1c -- AYIRT ETME (ayna): kacan 3 mutant x {teslim, mercek-B}: teslim 3/3 `.` (kitle tutarli), mercek-B 3/3 `X`; taban 68 + 36 passed (yanlis pozitif yok)"
    cmd: "T008_TB_SCRATCH=<scratch> python .agents/tasks/T-008/tester_B/b1c_ayirt_etme.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/B1c-kacan-ayirt-etme.txt
  - name: "B2 -- KR_GEOMETRI (teslim fixture'i) gercek OCR ciktisiyla 17/17 birebir ayni (referans turetilmemis, gercek fixture'dan); gercek KR'de bos/bosluklu metin 0, NaN 0, ayni-x cifti 0"
    cmd: "python .agents/tasks/T-008/tester_B/b2_kr_geometri_gercek_ocr.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/B2-kr-geometri-gercek-ocr.txt
  - name: "B2-B5 -- mercek-B testleri 37 passed (totoloji taramasi, esik ikinci parametre noktasi h=20/33, saflik AST, girdi degismezligi id+==, 100 rastgele x2 + permutasyon, iki surec farkli PYTHONHASHSEED, 4 yerlesimde 1000 blok < 50 ms, 1k->10k oran < 40, 100k < 1 s, pragma yok, davranissiz test yok, bariyer 68/68 setup'ta aktif)"
    cmd: "python -m pytest .agents/tasks/T-008/tester_B/test_mercek_B.py -p no:cacheprovider -rfE -v"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/B2-B5-mercek-testleri.txt
  - name: "B3 -- olcekleme: 1k/10k/100k, dort yerlesim; 10k/1k oranlari 9.0-15.1 (n log n ~13), 100k/10k 11.8-23.7; 1000 blok 1.4-3.2 ms"
    cmd: "python .agents/tasks/T-008/tester_B/b3_olcekleme.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/B3-olcekleme.txt
  - name: "B5 -- sefin dizini + mercek-B birlikte, iki sirada 344/344 (ILK kosumda 3 kirik: benim bariyerim basa girince sefin `match=\"T-006 K1 bariyeri\"` KESIN eslesmesi dustu -> tb_bariyer sefin bariyerinin ARKASINA girecek sekilde duzeltildi; ilk kosum ayrica dosyada)"
    cmd: "python -m pytest tests/unit/ocr .agents/tasks/T-008/tester_B/test_mercek_B.py -q -p no:cacheprovider -rfE  (+ ters sira)"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/B5-birlikte-kosum-sef-ve-tester-B.txt
  - name: "RET-1 -- uzun etiket koprusu SENTETIK (OCR yok): etiket solda h=2 satir + 2x3 kelime -> 'T a d b e c f' TEK blok (iki satir kelime kelime fermuarlanmis); x-ayni varyantta satirlar tek kelimeye bolunur; etiketsiz pozitif kontrol 'a b c' / 'd e f' GECER -> 3 failed 1 passed (beklenen)"
    cmd: "python -m pytest .agents/tasks/T-008/tester_B/test_mercek_B_ret.py -p no:cacheprovider -rfE -v"
    exit_code: 1
    result: kaldi
    evidence: tester_B_evidence/RET-1-uzun-etiket-koprusu-sentetik.txt
  - name: "depo dokunulmadi: git status --short -- src tests real_check packet BOS; kaynak/test sha256 ayna ile ayni; mtime'lar oturum oncesi"
    cmd: "git status --short -- src tests .agents/tasks/T-008/real_check.py .agents/tasks/T-008/packet.md; sha256sum ..."
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/git-status-src-tests.txt
blocking_issues:
  - "B-1 (K2, uzun kutu koprusu -- KRT-1 O2 sinifi): iki satir yuksekliginde bir etiket kutusu SOLDA (x en kucuk, y en kucuk) durunca satir bolumlemesinin ve grubun ILK blogu o olur; iki satirin butun kelimeleri onunla ortusur, satir ici x siralamasi iki satiri birbirine gecirir ve TEK blok cikar -- metin iki satirin kelime kelime fermuarlanmasi ('T a d b e c f'). Sentetik, OCR'siz: `test_mercek_B_ret.py` 3/3 duser, etiketsiz pozitif kontrol gecer. Gercek OCR: sefin 13:11 `real_check` #1c 11 kutu -> 1 blok (kendi elimle yeniden urettim). Mercek-B ayagi: teslimdeki `test_k2_grup_icinde_dikey_ortusme_grubun_ilk_bloguyla` bu sinifi 'olctugunu' soyluyor ama uzun kutuyu ORTAYA (x=60) koyuyor -- grubun ilk blogu kisa `a` kalir, `c` ayri kalir, test gecer; ayni uc kutu uzun kutu sola alininca bolumleme degisir. Olcu mekanizmayi ('grubun ilk blogu') kancaliyor, degismezi ('farkli satirlardan parcalar tek blokta olmaz') degil (§4.6/4, /7). M17/M18 mutantlari bu testle 'yakalandi' -- duzeltme sonrasi bu test BAYATLAR (§4.6/5) ve M17/M18 yeniden nisanlanmali."
---

# T-008 tur 1 -- Tester-B (mercek B: test kalitesi, saflik, mutant)

Karar: **RET** -- tek bloke eden bulgu B-1. Mutant kriteri (urunu bozan ve erisilebilir mutant bes kapidan geciyor mu) **karsilanmadi**: 47 davranis mutantinin 44'u yakalandi, kacan 3'u (M23/M40/M41) ürünü bozmuyor (keskinlik sinifi, asagida). Ret'in sebebi mutant degil, **teslim edilmis kodun** bir kabul kapisinda dusmesi ve o kapinin birim-test ayaginin fixture seçimiyle bos kalmasi: B-1. Not: `delivery.md`'yi sefin talimatiyla okudum (gorev metni "Teslim" altinda listeliyor); `tester_A/` okunmadi; A'nin ret verdigi yalniz `git log` basligindan goruldu, icerigine bakilmadi -- B-1'i kendi olcumumle (sentetik + #1c yeniden uretim) kurdum.

## B1 -- Mutant kiti: 47 davranis + 6 kontrol x 5 kapi (ayna agaci; `tester_B/mutant_kiti.py`)

Tahminler kosumdan once yazildi (`beklenen`); sapan 2: M07 ve M26 (ikisi de yakalandi, yalniz G3 tahmini yanlisti). Tam tablo: `B1-mutant-kiti-ozet-tablo.txt`.

| sinif | mutantlar | sonuc | G2'de dusen (sabit-pin haric) |
|---|---|---|---|
| K2 dikey esik 0.5 -> 0.0 / 0.9 | M01, M02 | .X.XX | 2 / 4 (0.49-0.51 sinir testleri) |
| K2 yatay esik 0.75 -> 0.6 / 0.9 / 1.0 / 10.0 | M03-M06 | 0.6: .X.XX; 0.9/1.0/10.0: .XXXX (#4c) | 4 / 2 / 2 / 8 |
| K2 min(h) -> max(h) (bosluk / dikey) | M07, M08 | .XXXX / .X.XX | 3 / 1 |
| K2 birlesik yukseklik (Y2), x `>`->`>=`, monitor, dpi | M09-M12 | .X.XX | 2 / 4 / 1 / 1 |
| K2 satir ici siralama YOK (ITIRAZ 1 tersi) | M13 | .XXXX (#1: 17 -> 9) | 8 |
| K2 `>=`/`<=` sinir, satir/grup referansi, dikey denetimsiz grup | M14-M18 | .X.XX | 2 / 3 / 2 / 1 / 2 |
| K3 CJK bosluklu, Hangul bossuz, ilk karakter, strip yok, kume eksik, karisik | M19-M22, M24-M26 | .X.XX (M20 .XXXX) | 6 / 1 / 1 / 4 / 3 / 2 / 5 |
| K3 uyumluluk ideografi CJK degil | **M23** | **.....** | 0 |
| K5 confidence max/ilk/ortalama, NaN suzgeci yok, hepsi-NaN -> 0.0 | M27-M31 | .X.XX | 3 / 3 / 3 / 1 / 1 |
| K5 line_boxes bos/ters, bbox ilk / h ilk, tek parca kopya | M32-M36 | .X.XX (M32 .XXXX) | 6 / 5 / 4 / 1 / 2 |
| K6 -idx, ters sira, siralama yok | M37-M39 | .X.XX (M38 .XXXX) | 1 / 14 / 3 |
| K6 bag max idx; satir ici (x,idx) | **M40, M41** | **.....** | 0 / 0 |
| K8 bos -> istisna; h=0/w=0 birlesir; `and`; `== 0` | M42-M45 | .X.XX | 1 / 4 / 5 / 2 |
| K1 modul mutable; `import os` | M46, M47 | .X.XX / .XXXX | 1 / 1 |
| KONTROL (esdeger): (y,x,idx)->(y,x); min->sorted()[0] x2; x=parcalar[0].x; monitor son parcadan; etkisiz ek siralama | C-1..C-6 | ..... x6 | -- |

Kapi basina: G1 mypy 0/47 (tip koruyan mutantlar; beklenen), G2 birim 44/47, G3 real_check 9/47, G4 44/47, G5 44/47. **Yalniz real_check ile yakalanan mutant yok**; birim testler tasiyici. `test_k1_sabitler_paketteki_degerlerde` sabiti pinler ama hicbir esik mutanti yalniz onunla yakalanmiyor (0.74/0.75/0.76, 0.49/0.50/0.51 sinir testleri ayrica dusuruyor). G3 sutunu real_check'in **12:38 surumu** iledir (parti 1-5 12:51-13:09; #1c 13:11'de eklendi); 13:11 surumuyle taban zaten dustugu icin G3 sutunu yeniden uretilmedi.

**Kacan 3 mutant -- davranis-esdeger degil (B1b), hicbiri urunu bozmuyor:**
- **M23** uyumluluk ideografi (U+F900..) CJK sayilmiyor: docstring "CJK'dir" der, K3 tablosunda ornek yok. Erisilebilirlik: KR tanima sozlugunde 76 uyumluluk ideografi var, JP'de 0 -> yalniz KR'de iki Hanja kutusu yan yana gelirse araya fazladan bosluk. Belge iddiasi olculmuyor; hazir test `test_b1_ek_k3_uyumluluk_ideografi_cjk`.
- **M40** bag EN KUCUK degil EN BUYUK girdi indeksiyle: ayni (y,x)'te birlesik grup ile tekil blok (monitorler arasi ya da cift tespit). 3000 rastgelede 438 ayrisma ama yalniz cikti SIRASI (normalizer yeniden siralar). Keskinlik.
- **M41** satir ici siralama (x,idx), y yok: ayni x farkli y iki kutu + sag komsu -> hangisinin komsuyu aldigi girdi sirasina bagli: `[a,b,c]` ve `[b,a,c]` farkli cikti. Bu, **K6'nin "bagsiz girdide her permutasyon ayni" olcusunde delik**: teslimin permutasyon fixture'larinda (KR 17, 4 kutu) ayni-x cifti yok; gercek KR'de de 0. Cift tespit sinifi; hazir test `test_b1_ek_k6_ayni_x_farkli_y_permutasyon_bagimsiz`.

Ayirt etme (B1c, ayna): ucu de teslimde `.`, mercek-B'de `X`; mutasyonsuz tabanda 68 + 36 gecer.

## B2 -- Totoloji

- 68 testin hepsinde assert var; sabit/`X == X` assert yok. **Yalniz kendi ciktisina bagli** 3 test (determinizm/permutasyon: `test_k1_ayni_girdi_ayni_cikti`, `test_k6_kr_geometrisi_permutasyonlarda_ayni_cikti`, `test_k6_bagsiz_kucuk_girdi_tum_permutasyonlar_ayni`) -- tek baslarina `return []` ile gecerler; KR fixture'i `[2,5,5,5]` ile ayrica cipali, dort kutuluk `temel_g` fixture'inin bagimsiz cipasi YOK (mercek-B'de eklendi: "a b", "c", "d"). Bloke etmez.
- Esik fixture'lari **sinirda**: 0.49/0.50/0.51 ve 0.74/0.75/0.76, ama yalniz h=100 (tek parametre noktasi). h=20 ve TEK h=33 (0.75*33 = 24.75; 0.5*33 = 16.5) eklendi: 6/6 gecer -- carpma semantigi tek sayida da dogru.
- **KR_GEOMETRI referans turetilmemis**: gercek OCR'la 17/17 birebir ayni (ayri surec). `[2,5,5,5]` geometriden bagimsiz turetilebilir (y kumeleri).
- **real_check kirilganligi**: `len(kr) == 17`, `[2,5,5,5]`, `len(mb) == 4` OCR modeline PINLI; model surumu degisirse dogru uygulama da duser. Birim testler model-bagimsiz (KR_GEOMETRI). Ayrica #3 NMT modeline bagli (yoksa IHLAL). Bilgi; docstring'e "model pinli" notu onerilir.

## B3 -- Saflik

- Bagimsiz AST: yalniz `__future__/math/unicodedata/collections/typing/src` import; yasak cagri yok; `global/nonlocal` yok; mutable varsayilan yok; modul duzeyi yalniz `Final` demet/sayi; `sys./os.` nitelik yok.
- Girdi degismezligi: 61 blok (NaN, iki monitor, iki dpi, yozlasmis dahil): `id` listesi, `==` (deepcopy), `line_boxes` kimlikleri ayni; birlesik cikti bloklari yeni nesne, tek parcalilar `is`.
- Determinizm: 100 rastgele bagsiz girdi x 2 esit; karistirilmis kopya esit; **iki ayri surec** PYTHONHASHSEED=1/2 ile 50 girdi birebir ayni (dict/set sira bagimliligi yok).
- Sure: 1000 blok 1.4-3.2 ms (4 yerlesim: rastgele, tek satir zincir, hepsi bagli, sutun). Olcekleme 1k -> 10k oran 9.0-15.1 (n log n ~13; n^2 ~100); 10k -> 100k 11.8-23.7 (rastgele yerlesimde 23.7: satir basina ~2900 parcali gruplar, dogrusal-ustu ama karesel degil); 100k rastgele 673 ms. Butce (1000 < 50 ms) 15x payla tutuyor.

## B4 -- Kapsam durustlugu

%100 (95 ifade), `pragma`/`no cover` yok, `.coveragerc`/`pyproject`/`setup.cfg`/`tox.ini`/`pytest.ini` yok. Her test ya `satirlari_birlestir`/`_paket_lafzi` cagiriyor ya kaynagi (AST) okuyor -- kapsam icin yazilmis davranissiz test yok. `test_k1_sabitler_*` sabit-pin (davranis degil) ama tek basina hicbir mutanti tasimiyor.

## B5 -- Bariyer

Teslim dosyasi kosarken (ayri surec, gozlem eklentisi): 68/68 setup'ta `meta_path[0]` sefin bariyeri, `import` girisimi 68/68 kesiliyor (mesaj "T-006 K1 bariyeri"), yasak kok `sys.modules`ta 0. Modulun kendisi yasak kok import etmiyor (reload sonrasi da 0). Kendi conftest'im `match="K1 bariyeri"` ile 3/3 atesliyor. **Bilgi (sefe):** `tests/unit/ocr/test_conftest_bariyer.py` `match="T-006 K1 bariyeri"` ile KESIN eslesiyor; baska bir bariyer once yuklenirse (birlikte kosum, ilk denemem) 3 test duser -- T-006'daki "9 kirik" sinifi. Kendi bariyerimi sefinkinin arkasina girecek sekilde duzelttim; iki sirada 344/344.

## Sefe bulgular (bloke etmeyen)

1. K6 permutasyon olcusu ayni-x ciftlerine ugramiyor (M41); hazir test var.
2. K3 uyumluluk ideografi belge iddiasi olculmuyor (M23); KR sozlugunde erisilebilir; hazir test var.
3. Esik testleri tek parametre noktasinda (h=100); h=20/33 noktalari eklenmeli (§4.6/7).
4. real_check gercek-OCR sayilarina pinli (17 / [2,5,5,5] / 4); "model pinli" damgasi.
5. `test_conftest_bariyer.py` kesin `match` -- birlikte kosumda kirilgan.
6. Tur 2 icin kit yukumlulugu: B-1 duzeltmesi `test_k2_grup_icinde_*`'yi bayatlatir; M16/M17/M18 (satir/grup referansi) yeniden nisanlanmali; kit `tester_B/mutant_kiti.py` yeni kaynakta yama hedeflerini `T008_TB_DRY=1` ile dogrular.
