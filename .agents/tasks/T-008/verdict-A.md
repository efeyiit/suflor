---
task: T-008
role: tester
round: 2
lens: "A — geometri (K2/K7), betik (K3), sözleşme (K5/K6/K8); gerçek OCR ayrı süreç"
decision: onay
checks:
  - name: "taban: mypy --strict temiz"
    cmd: "python -m mypy --strict --explicit-package-bases src/ocr/satir_birlestirici.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r2-00-taban-mypy.txt
  - name: "taban: implementer birim 76 passed"
    cmd: "python -m pytest tests/unit/ocr/test_satir_birlestirici.py -q -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r2-01-taban-birim.txt
  - name: "taban: real_check TEMİZ 15/15 (#1c 11→2 blok, en büyük 6; KR [2,5,5,5]; 1-em 4→4; 3.8 ms)"
    cmd: "python .agents/tasks/T-008/real_check.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r2-02-taban-real_check.txt
  - name: "tur 1 ret dosyam tur 2 koduyla 6/6 (etiketli 3 + etiketsiz 3 pozitif kontrol)"
    cmd: "python -m pytest .agents/tasks/T-008/tester_A/test_ret_a_uzun_kutu_koprusu.py -q -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r2-03-ret-6of6.txt
  - name: "tur 1 84 testim, yeniden nişan ÖNCESİ: yalnız 2 `_SINIF` düşer, 82 geçer (dördüncü kırık yok)"
    cmd: "python -m pytest .agents/tasks/T-008/tester_A/test_mercek_a.py -q -p no:cacheprovider  (yeniden nişan öncesi)"
    exit_code: 1
    result: gecti
    evidence: tester_A_evidence/r2-04-mercek-a-tur1-hali-bayat.txt
  - name: "2 `_SINIF` testi T2-1'e yeniden nişanlandı (`*_T2_1`): 84/84"
    cmd: "python -m pytest .agents/tasks/T-008/tester_A/test_mercek_a.py -q -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r2-05-mercek-a-yeniden-nisan-84.txt
  - name: "A2-1/A2-2 gerçek OCR (ayrı süreç, 46 fixture): etiket sağda/ortada/merdiven/3 satır/iki etiket/1.2×/1.5× HEPSİ temiz; sarkan token, alt çizgi, g/j/y, noktalama, dar menü — 7 'ihlal'in kaynağı r2-11 ile ayrıştırıldı (T2-1'e ait olan: sarkma 8 px token ayrı blok)"
    cmd: "python -X utf8 .agents/tasks/T-008/tester_A/a6_tur2_gercek_ocr.py --geometri"
    exit_code: 1
    result: gecti
    evidence: tester_A_evidence/r2-10-a2-gercek-ocr.txt
  - name: "AYNI fixture'lar tur 1 koduyla (ayna, referans = ilk): 3 satırlık etiket [11,5] fermuar (T2-1 kapatıyor); tırnak/tire/ortada farkları iki kodda AYNI (K2 boşluk kuralı + tespitçi hayaleti, T2-1 dışı)"
    cmd: "TESTER_A_KOK=<ayna_tur1> python -X utf8 .agents/tasks/T-008/tester_A/a6_tur2_gercek_ocr.py"
    exit_code: 1
    result: gecti
    evidence: tester_A_evidence/r2-11-a2-gercek-ocr-AYNA-tur1-kodu.txt
  - name: "A2-2 yanlış BÖLÜNME sınıfı gerçek OCR (üst konumlu minik işaret ™ ® ° ² ' ^ * \", font 30/40): minik kutular hep kelimelerden SONRA işleniyor, bölünme için ≥ 12 px titreşim gerekir (gözlenen ≤ 5) → erişilemez; parçalanmalar K2 `0.75×min(h)` kuralı"
    cmd: "python -X utf8 .agents/tasks/T-008/tester_A/a6_tur2_gercek_ocr.py --geometri d"
    exit_code: 1
    result: gecti
    evidence: tester_A_evidence/r2-12-a2-gercek-ocr-minik-isaret.txt
  - name: "tur 2 sentetik ölçülerim 26/26: gerçek geometri 8 varyant + 2160 konfigürasyonluk tarama + sarkan kutu türetimi (1815 sahne: bozulma ⇒ aralık ≤ 0) + bölünme formülü + T2-2 + K6 fuzz 6000 + belge sınırları"
    cmd: "python -m pytest .agents/tasks/T-008/tester_A/test_mercek_a_tur2.py -q -p no:cacheprovider -v"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r2-20-mercek-a-tur2-pytest.txt
  - name: "test dosyalarım mypy --strict temiz"
    cmd: "python -m mypy --strict --explicit-package-bases .agents/tasks/T-008/tester_A/test_mercek_a.py .agents/tasks/T-008/tester_A/test_mercek_a_tur2.py .agents/tasks/T-008/tester_A/test_ret_a_uzun_kutu_koprusu.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r2-21-testerA-mypy.txt
  - name: "mutant kiti (ayna): tur 1 kodu impl 5/ret 3/a1 2/a2 12; en uzun 6/3/2/13; son eklenen 2/0/0/4; bağ `<=` 1/0/0/1; `(x,idx)` 2/0/2/2; kontroller `-idx` ve `(x,y)` 0 (davranış-eşdeğer)"
    cmd: "python -X utf8 .agents/tasks/T-008/tester_A/mutant_kiti_tur2.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r2-22-mutant-ayirt-etme.txt
  - name: "implementer'ın 4 yeniden nişanlanan testi ayırt ediyor (son→merdiven+k6 bağlı; `<=`→merdiven; `(x,idx)`→2; ilk→5) ve docstring'deki 12 test adı mevcut"
    cmd: "(ayna dizinlerinde) python -m pytest tests/unit/ocr/test_satir_birlestirici.py -q -rf"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r2-23-mutant-implementer-dusen-testler.txt
  - name: "A2-4: tur 1 A6 raporum (30 fixture) tur 2 koduyla canlı — exit 0, yanlış birleşme yok"
    cmd: "python -X utf8 .agents/tasks/T-008/tester_A/a6_gercek_ocr.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r2-30-a6-tur1-raporu-tur2-koduyla.txt
  - name: "A2-4: canlı çıktı vs tur 1 E-prototipi çıktısı — 3 fixture'da GİRDİ (kutu kümesi) farklı (T-009 KR tanıma v5), gerisi birebir"
    cmd: "diff <(tur1 E çıktısı) <(r2-30)  (CRLF normalize)"
    exit_code: 1
    result: gecti
    evidence: tester_A_evidence/r2-31-a6-diff-vs-E-prototipi.txt
  - name: "A2-4: tur 1 kanıt dosyasındaki 30 gerçek geometri tur 2 birleştiricisine yeniden beslendi — 30/30 AYNI (birleştirici E ile özdeş; farklar girdiden)"
    cmd: "python -X utf8 .agents/tasks/T-008/tester_A/a6_gecmis_geometri_regresyon.py tester_A_evidence/a6-aday-E-gercek-ocr.txt"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r2-32-a6-tur1-geometrileri-tur2-koduyla.txt
  - name: "şefin dizini + tester_A (3 dosya) birlikte 440 passed (bariyerler çakışmıyor)"
    cmd: "python -m pytest tests/unit/ocr .agents/tasks/T-008/tester_A/test_mercek_a.py .agents/tasks/T-008/tester_A/test_mercek_a_tur2.py .agents/tasks/T-008/tester_A/test_ret_a_uzun_kutu_koprusu.py -q -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r2-40-birlikte-pytest.txt
  - name: "tam takım 1444 passed"
    cmd: "python -m pytest tests -q -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r2-41-taban-pytest-tum.txt
  - name: "yalnız kendi 116 testimle kapsam %100 (100/100 ifade)"
    cmd: "python -m pytest <tester_A 3 dosya> -q --cov=src.ocr.satir_birlestirici --cov-report=term-missing"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/r2-42-testerA-cov.txt
blocking_issues: []
---

# T-008 · Tester-A (mercek A) · tur 2 · **ONAY**

Tur 1 ret'imin (B1, uzun kutu köprüsü) düzeltmesi benim E prototipim temel alınarak yapıldı; bu tur sorum **"E sınıfı mı kapattı, fixture'ı mı?"** ve **"en kısa referans hangi yeni sınıfı açar?"** idi. İkisini de gerçek OCR (46 yeni fixture, ayrı süreç) + sentetik tarama + tur 1 kodunun aynası ile ölçtüm. `tester_B/` okunmadı; `delivery.md` yalnız şefin işaret ettiği `known_gaps` kalemleri için (4 yeniden nişan + M04) ve **ölçümlerimden sonra** okundu. Tur 1 verdict'im git tarihinde (`ef397e3`).

## 1 · Taban şefinkiyle birebir

mypy 0 · 76 · `real_check` TEMİZ 15/15 (#1c 11→2 `[6,5]`) · tam takım 1444 · ret dosyam 6/6. Yeniden nişan öncesi 84 testimden **yalnız** 2 `_SINIF` düştü (82 geçti, dördüncü kırık yok); ikisi `*_T2_1` olarak yeniden nişanlandı (`T a`,`c` / `T a1 a2`,`c1 c2`) → 84/84.

## 2 · A2-1 — E sınıfı kapattı (fixture'ı değil)

Gerçek OCR (r2-10, referans kanal = çizim parametreleri, etiket kutusu satır üyeliğinden muaf):

| varyant | tur 2 | tur 1 kodu (ayna, r2-11) |
|---|---|---|
| etiket **sağda** | 11→2 `[6,5]` | aynı |
| etiket **ortada**, iki tarafta kelime | satır 0 `[2]+[3]`, satır 1 `[2]+[3]` (K7 boşluk, beklenen) | aynı |
| **merdiven** (satır 0 solda / satır 1 sağda) | 5→2 `[3,2]` | aynı |
| etiket **3 satırı** kaplıyor | 16→3 `[6,5,5]` | **[11,5] — satır 0+1 fermuar** |
| **iki etiket** sol+sağ | 12→2 `[7,5]` | aynı |
| 1.2× üst / orta · 1.5× üst / orta | `[6,5]` / `[5,1,5]` / `[6,5]` / `[5,1,5]` | aynı |

Hepsinde etiketsiz kontrol `[5,5]`(`[5,5,5]`). Sentetik tarama (`test_r2_*`): etiket h ∈ {1.2…3.0}×h × dy 9 nokta × pitch {1.05…1.5}×h × 2/3 satır × sol/sağ/orta × ±3 px titreşim = **2160 konfigürasyon**, satır bütünlüğü hepsinde; köprü geometrisi 142/720'de gerçekten kuruluyor (pozitif). Tur 1 kodu bu taramanın üç konumunda da düşüyor (r2-22). Sınıf kapalı, yalnız düzeltme fixture'ında değil.

`etiket ortada`'daki fazladan kutu (254,75,25,23) boş bölgede tespitçi hayaleti (görsel kontrol yapıldı); birleştirici onu yalıtıyor, iki kodda aynı.

## 3 · A2-2 — "referans = en kısa" ne zaman yanlış? (ölçüldü)

**(a) Sarkan kısa kutu → yanlış birleşme.** Türetim: p `[t0,t1]` satır 0'a katılmak için `a1−t0 ≥ 0.5h_p`, satır 1'in p ile örtüşmesi için `t1−b0 ≥ 0.5h_p`; toplamı `g ≤ 0`. Yani iki satır ancak kutuları **fiziksel iç içeyken** karışır. Tarama h_p 4–24 × sarkma 0–20 × aralık −6…8 (**1815 sahne**): bütünlük bozulan her sahnede aralık ≤ 0, pozitif kontrol var (`test_r3_sarkan_*_ic_iceyken`). Gerçek OCR pitch 1.05×h'de satır kutuları arası aralık **2 px** (>0) → sınıf gerçek düzende kapalı; alt çizgili metin, Latin g/j/y, "...", dar menü: temiz.

**(b) T2-1'in gerçek OCR'da ölçülen tek yan etkisi:** küçük fontlu (16 px) token satır altından **8 px** sarkınca tur 2 onu **ayrı blok** bırakıyor (en kısa kelime kutusuyla örtüşme 7 < 8.5), tur 1 satıra yapıştırıyordu (ilk kutuyla 9 ≥ 8.5); sarkma 0/4'te ikisi de yapıştırır, 12'de ikisi de ayırır (r2-10 [B1] p36/p40; sentetik `test_r3_*_penceresi_*`). Cümle bütün; ürün etkisi: 2 karakterlik ek işaret ayrı çevrilir. **Ürünü bozmaz.**

**(c) Üst konumlu minik kutu → yanlış BÖLÜNME (tur 2'ye özgü, sentetik).** Minik kutu (h_t) satıra katılıp referans olursa, ondan sonra işlenen aynı-satır kelimesi `titreşim > 0.5·h_t` ise satır ikiye bölünür (`test_r3_yanlis_bolunme_*`, formül 4 h_t'de doğrulandı; tur 1 kodu bölmez). Gerçek OCR (r2-12, ™ ® ° ² ' ^ * " font 30/40): minik kutular kelime üstünden 1–9 px **aşağıda** ve h ≥ 13 → hep kelimelerden **sonra** işleniyor; bölünme için ≥ 12 px titreşim gerekir, gözlenen ≤ 5. Erişilemedi → `[ÖLÇÜLMÜYOR]`-gerçek olarak belgeye girmeli (yükümlülük 1).

**(d) T2-1 dışı ama ölçüldü:** boşlukla ayrılmış tek işaret (™, `*`, `"`) kendi minik kutusunu alıyor ve K2'nin `0.75×min(h)` boşluk eşiği (≈10 px) kelime boşluğunun (11–12 px) altına düşüp satırı parçalıyor (™ f30: 5 blok). Paket kuralı, tur 1 ile **aynı** (r2-11/r2-12), bu turun değişikliği değil — yükümlülük 3.

## 4 · A2-3 — T2-2 ve K6

`p(0,0) q(0,10) r(55,10)` 6 permütasyon `["p","q r"]`; aynı x'te 3 kutu + sağ komşu 24 permütasyon aynı; `(x,idx)` mutantı 6 testle düşüyor (impl 2, benim 4). K6 daraltılmış cümle: 6000 rastgele girdi (h 4–60 karışık, T2-1 mantığını zorlar) — permütasyon farkı **yalnız** çıktı `(y,x)` bağında, küme aynı. Tutuyor.

## 5 · A2-4 — regresyon

116 kendi testim + 6 ret geçiyor; birlikte 440; tam takım 1444; kapsam yalnız benim testlerimle %100. Tur 1 A6 raporum tur 2 koduyla **exit 0**; E-prototipi çıktısıyla fark 3 fixture'da ve hepsi **girdi** farkı (T-009 KR tanıma v5 → boş metinli kutu elemesi değişti: `kr_dar_1p1` 15→16 kutu, `kr_dar_1p0` 16→17, `menu_KR` bir `/` kutusu yer değiştirdi); tur 1 kanıt dosyasındaki 30 geometri tur 2 koduna yeniden beslendiğinde **30/30 aynı** (r2-32). Birleştirici E ile özdeş.

`known_gaps` kalemleri (ölçümlerden sonra okundu): 4 yeniden nişanlanan test ayırt ediyor (r2-23: son→merdiven+k6 bağlı, `<=`→merdiven, `(x,idx)`→2, ilk→5); M04 `-idx` benim kitimde de 0 düşürüyor — davranış-eşdeğer (bağlı çiftin işleme sırası ne üyeliği ne referansı değiştirir), **kontrol sınıflaması doğru**. Ek: `(x, y)` (idx'siz satır içi sıra) de 0 — kararlı sıralama + `(y,x,idx)` ön sıralı girdi nedeniyle eşdeğer; docstring'in `(x, y, idx)` ifadesinde idx etkisiz (not).

## 6 · A2-5 — orantı ve karar

Ret eşiği "ürünü bozan **ve** erişilebilir sınıf". Ölçülenler: köprü sınıfı gerçek OCR'da 7 varyant + 2160 sentetik konfigürasyonda kapalı; en kısa referansın yanlış birleşme sınıfı matematiksel olarak iç içe satır gerektiriyor ve 1.05×h'de bile yok; yanlış bölünme sınıfı sentetik-yalnız (gerçek marj ≥ 8 px); gerçek yan etki (8 px sarkan küçük token ayrı blok) cümleyi bozmuyor. **Onay.**

## 7 · Yükümlülükler (karara yazılmalı; ret dışı)

1. **Docstring "SINIR" paragrafı** (`[ÖLÇÜLMÜYOR] gerçek OCR'da … satır aralığı ≥ 10 px … fixture üretilemedi`) artık ölçüldü ve iki cümlesi dar/yanlış: (i) yanlış birleşme koşulu **aralık ≤ 0** (türetim + 1815 sahne), 1.05×h'de aralık 2 px ölçüldü ve temiz — "≥ 10 px" yerine "> 0"; (ii) "tespitçi noktalamayı kelime kutusuna dahil ediyor" bitişik noktalama için doğru, **boşlukla ayrılmış** işaret/küçük-font token ayrı kutu alıyor (r2-10 [B], r2-12 [D]); (iii) gerçek yan etki (8 px sarkan token ayrı blok, r2-10 [B1]) ve (iv) yanlış bölünme sınıfı (formül `titreşim > 0.5·h_minik`, gerçek marj ≥ 8 px, `[ÖLÇÜLMÜYOR]`-gerçek) yazılmalı. Ölçüler: `tester_A/test_mercek_a_tur2.py::test_r3_*`, fixture'lar `tester_A/fixtures/r2/`.
2. **K6 cümlesi** "bağ yalnız çıktı SIRASINI etkiler, satır üyeliğini DEĞİL": aynı `(x,y)` farklı `w` çift tespitte **grup bölümlemesi** (küme) de girdi sırasına bağlı (`test_r5_ayni_x_y_farkli_w_*`: `['p','P r']` / `['P','p r']`). Satır üyeliği gerçekten aynı; cümle "grup bölümlemesi de" diye genişletilmeli. Sentetik-yalnız (gerçek tespitçi çift kutu vermiyor, A6 tur 1).
3. **K2 `0.75×min(h)` boşluk kuralı minik işaret kutusunda satırı parçalıyor** (™/`*`/`"` h 13–19: eşik ≈ 10 px < 11–12 px kelime boşluğu; r2-12 ™ f30 → 5 blok). Paket kararı, tur 1 ile aynı, T2-1 dışı; ürün erişimi boşlukla ayrılmış tek işaretle sınırlı (nadir). Şef kararı/ileri görev için kayıt (ör. eşikte satır medyan h'si).
4. Gri bölge `[0.6, 0.95]×h` (tur 1 yük. 2) bu turda da ölçülmedi — hizalanmış metin.

`git status --short -- src tests` boş; `git commit` yok; ayna ağaçları scratchpad'de; metin basılmadı (yalnız geometri).
