---
task: T-012
role: tester
round: 1
decision: onay
checks:
  - name: "taban 1 -- mypy --strict temiz (6 dosya)"
    cmd: "python -m mypy --strict --explicit-package-bases src/ui"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/taban-1-mypy.txt
  - name: "taban 2 -- implementer birim testleri 190 passed"
    cmd: "python -m pytest tests/unit/ui -q -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/taban-2-pytest-ui.txt
  - name: "taban 3 -- real_check v2 sarici ile: OTURUM KILITLI (on plan LockApp.exe), gercek girdi olculemedi; ilk kosum gecersiz (dosya adi soyluyor); sefin/implementer'in 18/18 TEMIZ kosumlari (`sef_dogrulama/real_check-tur1-sef.txt`, `evidence/real_check-tur1-son.txt`) okundu, kilitten bagimsiz kalemler ([1],[2],[6],[7]) kendi sondamda birebir"
    cmd: "python .agents/tasks/T-012/evidence/real_check-on-plan-sarici.py .agents/tasks/T-012/tester_B/sonda_1_gercek_ekran.py"
    exit_code: 0
    result: kaldi
    evidence: tester_B_evidence/sonda1-ILK-KOSUM-oturum-kilitli-gecersiz.txt
  - name: "taban 4 -- kapsam %99.59 (487 ifade, 2 eksik: uygulama.py 36/40 gercek argv/exec)"
    cmd: "python -m pytest tests/unit/ui -q -p no:cacheprovider --cov=src.ui --cov-fail-under=95 --cov-report=term-missing"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/taban-4-kapsam.txt
  - name: "taban 5 -- tam takim 2087 passed"
    cmd: "python -m pytest tests -q -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/taban-5-tum-takim.txt
  - name: "mercek-B testleri: 97 passed + 2 xfail(strict) = 99 kosum, 85 + 14 fonksiyon (A istek satir satir · B K1 · C/C2 kotu kullanim · D v2 ▲ · E kapi yapisal · F demo gercek cagiran · G taze surec)"
    cmd: "python -m pytest .agents/tasks/T-012/tester_B -q -p no:cacheprovider --import-mode=importlib -rfEx --tb=short"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/mercek-b-testleri.txt
  - name: "mercek-B + implementer birlikte: 287 passed + 2 xfail (ortam kirliligi yok)"
    cmd: "python -m pytest tests/unit/ui .agents/tasks/T-012/tester_B -q -p no:cacheprovider --import-mode=importlib"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/birlikte-kosum.txt
  - name: "sonda 1a (gercek ekran, kilitten bagimsiz, fare yok): Alt-Tab adayi 0 (tepsi/kenar), Shell_NotifyIconGetRect bagimsiz kanal 5 noktada dogru, WM_CLOSE 3 durumda cikis 1 + (F,F,F) + Shell'de ikon yok, z-sirasi (_ac raise_ topmost oyunun VE secim katmaninin ustune cikar), DPI %125 birincil: sag kenar +1 fiziksel px, panel +0, sol +0"
    cmd: "python .agents/tasks/T-012/tester_B/sonda_1a_kilitten_bagimsiz.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/sonda1a-kilitten-bagimsiz.txt
  - name: "sonda 1b (gercek fare girdisi: tepsi ikonuna tik + on plan, sag tik on plan, balon suresi, tasma) -- oturum kilitli, 90 dk bekleyici (`bekle_ve_kos.py`) kilit acilirsa kosar; bu belge yazildiginda KOSULMADI"
    cmd: "python .agents/tasks/T-012/tester_B/bekle_ve_kos.py 90"
    exit_code: 3
    result: kaldi
    evidence: tester_B_evidence/bekle-ve-kos-durum.txt
  - name: "depo dokunulmadi: src/tests/demo/real_check/packet git status BOS, sha256, HEAD 7c430eb"
    cmd: "git status --short -- src tests demo .agents/tasks/T-012/real_check.py .agents/tasks/T-012/packet.md; sha256sum src/ui/*.py ..."
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/git-durumu.txt
  - name: "korluk: tests/unit/ui/test_*.py, evidence/mutant-kiti.py, delivery.md, sef_dogrulama/ yalniz kendi testlerim + sonda_1a bittikten SONRA (22:54:43) test kalitesi / kapi denetimi icin acildi; tester_A* hic acilmadi"
    cmd: "date"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/korluk-kaldirma-ani.txt
blocking_issues: []
---

# T-012 tur 1 -- Tester-B (mercek: kotu kullanim + istek/sartname uyumu + test kalitesi)

Karar: **ONAY** (implementer teslimi). Paket v2'nin ▲ maddelerinde **olculmus ihlal yok**; docstring iddialari tutuyor (biri kismen: asagida O-B1); bes taban komutu yesil (taban 3 gercek-girdi kalemleri bu oturumda kilit yuzunden olculemedi -- kilitten bagimsiz kalemler kendi sondamda birebir, gercek-girdi kalemleri sefin ve implementer'in 18/18 kosumlarinda). Kendi 99 kosumum yesil (2 xfail = O-B1). **Yuksek bulgum implementer'in modulunde degil, sefin entegrasyonunda** (`demo/kabuk.py` -> `SecimKatmani` Esc = `QApplication.quit()`): kabuk kapatilmadan surec biter. Implementer'a feedback yok; sefe iki kalem var.

Korluk: `delivery.md`, `evidence/`, `sef_dogrulama/`, `tests/unit/ui/test_*.py` 22:54:43'te (kendi testlerim + sonda_1a bittikten sonra) yalniz test kalitesi/kapi denetimi icin acildi; `tester_A*` hic acilmadi. Onceki oturum kota yuzunden kesilmisti; `test_mercek_b.py` (85 fonksiyon) o oturumdan, ilk kosumda 2 test kendi varsayim hatamdi (x1: (F,F,T) tepsi satiriyla cakisiyordu, asil bulgu `durum`≠uclu; d11: 100 px ekranda panel sigmaz ama sekme sigar) -- duzeltildi, urun bulgusu degil.

**Ortam notu (olcum gecerliligi):** bu oturumda makine **kilitli** (on plan `LockApp.exe`) ve ekran duzeni **degismis**: tek monitor 2560x1440 @ %125 (mantiksal 2048x1104 avail, dpr 1.25); olgular U0 / KRT / sef kosumlari 2560x1392 dpr 1.0 + sol dpr 1.25 monitorde yapilmisti. Gercek fare girdisi (`mouse_event`) kilit ekranina gider -> S3/S4/S8/S9 olculemedi; `bekle_ve_kos.py` 90 dk kilit acilmasini bekliyor (acilirsa `sonda1b-gercek-girdi.txt` + `taban-3-real_check-sarici.txt` yazilir). Kilitten bagimsiz olan her sey olculdu ve **dpr 1.25 BIRINCIL** bugune kadar kimsenin olcmedigi bir konfigurasyon: geometri dogru, +1 px sinifi ayni.

## Istek (kullanicinin sozleri) <-> urun, satir satir

| Istek | Urun | Olcu | Uyum |
|---|---|---|---|
| "3 pencere dugmesi olsun sag uste" | ust seritte (y<44) sagda, sirali kenar·tepsi·kapat, kapat en sagda, mod dugmelerinin ustunde | `test_a1` | evet |
| "biri uygulama kapatma" (tepside kalinti yok) | `kapat()`: uclu (F,F,F), yoklayici durur, `cikis_istendi` 1; **Shell_NotifyIconGetRect = E_FAIL** (Qt'den bagimsiz kanal: ikon Shell'den silinmis); `calistir` bagliysa surec biter | `test_a2`, `test_g1`, sonda_1a S2e/S5 | evet |
| "biri arkaplanda calistirma" (tepsi) | pencere gizli, ikon Shell'de kayitli, olay dongusu donuyor, mod sinyali tepsideyken de calisir; WM_CLOSE tepsideyken de temiz cikar | `test_a3`, `test_g1`, sonda_1a S2b/S5 | evet (kisayollar haric, asagida) |
| "kisayollar (`Ctrl+Alt+T/R`) calismaya devam eder" (sef yorumu) | kabuk kisayol bilmez | -- | **eksik, paket karari** (`known_gaps`, HotkeyService ayri gorev) |
| "tepsi ikonuna tiklayinca pencere geri gelir" | `activated(Trigger/DoubleClick)` -> `goster()`; gercek tik + on plan | `test_b1`, `test_c15`; **gercek tik sonda_1b (kilit)** | offscreen evet; gercek `[OLCULEMEDI bu oturum]` |
| "masaustunde gozukmeyecek" | kenar/tepsi durumunda **Alt-Tab/gorev cubugu adayi 0** (gorunur+sahipsiz+!WS_EX_TOOLWINDOW), sekme `WS_EX_TOOLWINDOW|TOPMOST|NOACTIVATE` | `test_a6`, sonda_1a S1b/S1c | evet |
| "ekranin bir kenarinda kucuk bir yarim daire" | 26x52 (istek 24-28 px), sag kenara bitisik, dikey orta; ic koseler alfa 0, kenar tarafi opak; sol kenarda aynali | `test_a4`, `test_d2`, sonda_1a S7 | evet |
| "imlecle oraya gidince cevirme secenegi cikacak, iki tane" | panelde **2 buyuk mod dugmesi + 1 kucuk (22x20) `dugme_goster`** | `test_a5` | **fazla: 3. dugme** -- paket v2 K8 karari (KRT O3d); istek notu "kullaniciya sorulacak" diyordu, sorulmadi (sef kalemi) |
| "imlec uzaklasinca kapanir" | 450 ms sonra; icerideyken sayac durur | `test_d6`, `test_a5` | evet |
| "surukleneblir" | yalniz dikey, sinira kilitlenir; yatay/monitor `known_gaps` | `test_d4c` | kismi, belgeli |
| "yarim daire oyunun ustunde kalir" | normal oyun: evet; **sekmeden SONRA gosterilen topmost oyun ustte** (belgeli sinir); ilk acilistan sonra `raise_` ile sekme ustte kalir | sonda_1a S6a/S6b' | belgeli sinir, dogrulandi |
| "tiklamayi yalniz kendi alaninda yutar" | pencere yalniz sekme kadar (yapisal); saydam kose diskin disinda | `test_c17`, `test_d11`; KRT k1b P8 | evet |
| "sag tik -> ana pencere" (varsayilan) | sag tik + `dugme_goster` + tooltip | `test_b1`, `test_d9` | evet |
| "birincil monitorun kenarinda baslar" | `ekran=None` -> `primaryScreen()` | implementer `test_k2_ekran_none_birincil` | evet |
| "DPI %100/%150/%200 … iki monitor" (istek notu) | %100 (sef, KRT), %125 ikincil (kapi [8]), **%125 birincil (ben)**; %150/%200 olculmedi | sonda_1a S7 | kismi |

**Eksik davranis (paket istiyor, kod yapmiyor): bulunmadi.** Fazla davranislar (parametre dogrulama, `kapandi`/`yokluyor`, dirilme yok, hideEvent temizligi, `calistirici`) docstring'de belgeli.

## Sartname v2 ▲ maddeleri <-> kod

| ▲ madde | Kod | Olcum |
|---|---|---|
| K1 uclu tablosu + `goster()` ikonu gizler | evet; her yoldan (7 yol) (T,F,F) | `test_b1` x7, `test_b2` |
| K1 `closeEvent` == `kapat()`, ignore yok, zombi ulasilamaz | evet, uc durumda; **gercek WM_CLOSE uc durumda** cikis 1 + (F,F,F) + Shell'de ikon yok + yoklayici durdu | `test_b4` x3, sonda_1a S5 |
| K1 `kapat()` idempotent, tam bir kez | evet; `kapat();kapat();close()` -> 1; dinleyici icinden yeniden `kapat()` -> 1 | `test_b3` x4, `test_c2x6` |
| K1 kabuk `quit()` cagirmaz; `calistir` baglar | evet; taze surecte `dugme_kapat` -> exec doner 0; `close()` de | `test_g1`, `test_d8` |
| K2 `sekme_icinde` disk; sol kenar aynali; `availableGeometryChanged` | evet; panel ACIKKEN de yeni dikdortgene sikisir | `test_d1`, `test_d2`, `test_c2x4` |
| K3 bayraklar (yapisal) + `_ac()` `raise_()` | evet; **gercek z-sirasi**: `_ac()` sekmeyi topmost oyunun ustune alir | `test_d3`, sonda_1a S6b |
| K4 surukleme: sayac baslamaz/durur, birakinca sifirdan; acikken sol tik surukleme degil | evet | `test_d4`, `test_d4b` |
| K4 mod sinyali oncesi panel kapanir (uc dugme) | evet, sinyal aninda (F, 26x52) | `test_d5` |
| K4 yoklayici yalniz gorunurken; imlec yalniz callable | evet; `QCursor.setPos` etkisiz | `test_d4d` |
| K5 tepsi yok -> kenar (F,T,F); menu; `gorunur()` daima False | evet | `test_b6`, `test_c15`, `test_d7` |
| K6/K7 AST + taze surec import | evet (pozitif kontrollu) | `test_d8*` |
| K8 tooltip "Sağ tık: pencereyi göster", `dugme_goster` | evet | `test_d9` |
| Sabitler urun degerleri | 26/120/450/60, 200x132 | `test_a4`, `test_e1` |

## Bulgular

### YUKSEK -- implementer'da yok; SEFE (entegrasyon, `demo/kabuk.py`)

**Y-B1 (sef) · Bolge secimini Esc ile iptal etmek UYGULAMAYI KAPATIR; kabuk `kapat()` cagrilmadan surec biter.** `demo/kabuk.py` `_bagla` -> `bolge_izle_istendi` -> `demo/bolge_izle.py::SecimKatmani`; `keyPressEvent(Esc)` -> `QApplication.quit()` (bagimsiz demonun "Esc = çık"i). Olcum (`test_f1`, taze surec, offscreen): kenar durumunda sekmeden "Bolge izle" -> katman -> Esc -> `exec()` **0 ile doner**, `kapandi=False`, `cikis_istendi=0`, `durum=kenar`. Kullanici icin: "yanlis yere tikladim, iptal" = uygulama gitti. Ayrica Qt 6.11 `quit()` once GORUNUR ust-duzey pencereleri `close()` eder: sekme kapanir, **gizli ana pencere closeEvent almaz** -> `kapat()` yolu atlanir (`test_c2x10`). Duzeltme sefte: `SecimKatmani` Esc -> `close()` (iptal sinyali), `quit` yok; `demo/kabuk.py` katmani kapatinca sekmeyi/pencereyi eski durumuna dondurur.

### ORTA

**O-B1 · `KenarSekmesi` dis `close()`/WM_CLOSE'u ele almiyor -> `durum` ile uclu ayrisir; tepsisiz konfigurasyonda ZOMBI (Y1 sinifi, dis yol).** `sekme.close()` (Qt `quit()`nin closeAllWindows'u, `taskkill` WM_CLOSE, sonraki ajanin `pencere.sekme.close()` cagrisi) sekmeyi gizler; kabuk KENAR sanir: uclu (F,F,T) = TEPSI satiri (`test_x1` xfail); `tepsi_kullanilabilir=False` iken (F,F,F) + `kapandi=False` + cikis 0 (`test_x2` xfail) -- paketin "ulasilamaz" dedigi durum dis yoldan ulasilir. Urun konfigurasyonunda (Windows, tepsi var) geri yol tepsi ikonu; ret degil. Oneri (implementer, 5 satir): `KenarSekmesi.closeEvent` -> `event.ignore()` + `pencereyi_goster.emit()` ya da yeni `kapatildi` sinyali -> `AnaPencere.goster()`/`kapat()`.

**O-B2 (sef, demo) · Bolge secimi sirasinda imlec sekme diskine girerse panel SECIM KATMANININ USTUNE cikar.** `_ac()` `raise_()` (K3 ucuz iyilestirme) katman gibi Tool+topmost pencerelerin de ustune cikar; gercek ekranda olculdu: katman z=7 sekme z=8 -> `_ac()` sonrasi sekme 7 katman 8 (sonda_1a S6c). Kullanici ekran kenarina dogru dikdortgen cizerken 200x132 panel secimin ustune acilir. Duzeltme sefte (`demo/kabuk.py`): secim sirasinda `pencere.sekme.hide()` / secim bitince `show()` (yoklayici zaten durur). Kabuk tarafinda alternatif: `bolge_izle` sinyali sonrasi kabuk sekmeyi kendisi gizlemez (K7 "baglayan taraf karar verir") -- karar sefin.

**O-B3 · `tepsiye_al()` sonrasi kullanici HICBIR SEY gormuyor (ilk kullanim).** Balon kaldirildi ([5c] kok nedeni, dogru karar); Windows 11'de yeni tepsi ikonu varsayilan olarak TASMA menusunde gizlidir (bu makinede `HKCU\Control Panel\NotifyIconSettings\<id>` python.exe girdisinde `IsPromoted` YOK = gizli). Sonuc: pencere kaybolur, balon yok, gorunur ikon yok. Ipucu yalniz dugmenin tooltip'inde. Oneri (implementer/sef, paket K5 kalemi): ilk `tepsiye_al()`da tek seferlik `bildir(...)` (balon sekmeyi ortemez: tepsi durumunda sekme YOK; [5c] sinifi yalniz tepsi->kenar<6 s dizisinde dogar -- o gecis tepsi menusunden, kullanici zaten ikonu bulmus) ya da gizlemeden once durum satirinda 1 s "Tepsiye aliniyor" metni. Docstring'in "balon ~6.2 s, `ms` yok sayilir" iddiasi sonda_1b S8 ile olculecekti (kilit).

**O-B4 (kapi) · `real_check` [3] pozitif kontrolu sefin elinde YOK.** Paket K3: "pozitif kontrol: bayraksiz pencere on plani alir -- sef `sef_dogrulama/`'ya bir kez yazar". `sef_dogrulama/` icinde yalniz KRT k5b T2'ye atif var (`krt1_sef_kosumlari.txt` Y3 satiri offscreen); bayraksiz varyantin gercek tikla on plani aldigi **sef olctu** kaydi yok -> [3a]/[3b] "sifir ihlal" kural 10'a gore KRT olcumune dayaniyor (kural 6 etiketi: "KRT olctu"). Kapiya 5 satirlik pozitif kontrol adimi ([3c]: `Tool` olmayan sade QWidget'a gercek tik -> on plan degisir) eklenmeli.

### DUSUK

- **D-B1** DPI %125 **birincil** monitorde kapali sekme fiziksel `(2528,658,2561,723)`: sag kenar **+1 px** monitorun otesinde (2022*1.25=2527.5->2528, 26*1.25=32.5->33); panel +0, sol kenar +0 (sonda_1a S7). Kapi [8] ile ayni sinif (orada sol monitor -> birincilin x=0 sutunu sekmeye ait). Tek monitorde zararsiz; komsu monitorde 1 px sutunun tiki sekmeye gider. `known_gaps` +-1 kabulu tutarli. Oneri: kapi [8] yalniz `screens()[1]` degil, `dpr != 1` olan HER ekrani (birincil dahil) olcmeli -- bugunku konfigurasyonda [8] "atlandi" der ve DPI hic olculmez.
- **D-B2** `kapat()` sonrasi `pencere.show()` (QWidget API) pencereyi getirir ama uc dugme oludur (`kapandi`), `cikis_istendi` bir daha yayilmaz (`test_c2x5`). Sonraki ajan kapat sonrasi kabugu yeniden kullanamaz; docstring "dirilme yok" bunu ima ediyor, `show()` icin acik degil.
- **D-B3** `calistir()` mevcut `QApplication`'a `setQuitOnLastWindowClosed(False)` YAN ETKISI birakir ve iki kez cagri iki kabuk kurar (tekil degil) (`test_c3`). Belge yeter.
- **D-B4** `imlec_konumu` `(x, y)` tuple donerse her 60 ms `TypeError` (sessiz degil, hic acilmaz) (`test_c2x7`); `KenarSekmesi.y = "abc"` `ValueError`, `None` `TypeError`, `3.7 -> 3` (`test_c5`). Belge.
- **D-B5** `durum` `kapat()` sonrasi son durumu gosterir ((F,F,F) ile KENAR); ayirt edici `kapandi` (`test_b7`) -- docstring belgeli.
- **D-B6** Mod tiki noktasi kapali diskin icindeyse (dugmenin kenar ucu) panel 120 ms sonra YENIDEN acilir; Snapshot yakalamasi sinyalden >~180 ms sonra yapilirsa panel metni kareye girer (`test_c7`). Dugme merkezi diskin disinda -> dogal tikta olmaz. Baglayan tarafa not.
- **D-B7** Slot istisnasi: pytest-qt disinda (gercek `exec()`) PySide6 6.11 istisnayi basar, surec dusmez, sonraki tik islenir (`test_c1b`); uzun dinleyici (300 ms) boyunca yoklama durur, panel zaten kapali (`test_c2`). Tasarim 5.5 sorumlulugu baglayan tarafta.
- **D-B8** Paket K5 metni "ikona tik sonrasi on plana gelme ... `real_check`" der ama kapi tepsi ikonuna hic tiklamaz (yalniz `goster()`); docstring dogru (`[OLCULMUYOR]`). Paket cumlesi bayat.
- **D-B9** `mypy --strict` temiz; `y` ozelliginin `QWidget.y()`yi golgelemesi `# type: ignore[override]` ile -- paket arayuzu bagliyor, belgeli tuzak (`test_c5`: `sekme.y()` `TypeError`).

## Kotu kullanim (sonraki cagiran = demo/pipeline) -- olculdu, bozulma yok

`anlik_cevir_istendi -> kapat()` yeniden giris (`_mod_tiki` -> `hideEvent` -> `_kapat`) hata yok, tek sinyal (`test_c2x1`) · pencere mod dugmesi -> `kenara_al()` (`test_c2x2`) · surukleme sirasinda sag tik -> goster, bayrak temiz (`test_c2x3`) · `cikis_istendi` dinleyicisi `kapat()+bildir()+goster()` (`test_c2x6`) · tepsi menusu sinyali gorunurken (`test_c2x8`) · `kenar=SOL` + panel (`test_c2x9`) · `kenar` gecersiz dize `ValueError`, durum bozulmaz (`test_c4b`, `test_c12`) · `acilma_ms=0`, `yoklama_ms=1` calisir (`test_c11`) · `bildir` 20x + bos + negatif (`test_c6`) · `ekran_dikdortgeni` kopya (`test_c14`) · demo `anlik_cevir` -> `goster()` kenar->gorunur tutarli, ardindan kapat -> exec 0 (`test_f2`, `test_c16`).

## Kapi (`real_check.py` v2) denetimi (kural 8/10)

- [0] sabitler literal `(26,120,450,60,200,132)`, [4] sinirlar literal `120+2*60+150` / `450+2*60+150` -- referans uygulamadan turemiyor (`test_e1`). ok.
- [3] pozitif kontrol: **O-B4**.
- [8] `+1 px`: **D-B1**; yalniz ikinci monitor -- dpr != 1 birincil olculmuyor.
- [5c] sag tik: uclu olculuyor, **on plan olculmuyor** (docstring "pencere one gelir"); KRT k1b P4 olctu, kapi/sef olcmedi; benim sonda_1b S4c kilit yuzunden bekliyor.
- [6] gizli ana pencereye `PostMessage(WM_CLOSE)`: kapi yalniz GORUNUR durumdan gonderiyor; tepsi/kenar durumlarinda gercek WM_CLOSE'u ben olctum (S5) -- temiz. Kapiya [6d] tepsi/kenar satiri onerilir.
- [9] yalniz [3b] panel acilirsa olculur; acilmazsa `[3b] panel acilmadi` ihlali -> sessiz atlanmaz. ok.
- Sarici: kilitli oturumda `on planda=False` deyip yine de kosuyor ve sonuc "TEMIZ" olabilir ([3] on kosulu ihlal verir, digerleri gecer) -- `oturum.py` gibi bir kilit kontrolu sariciya eklenmeli (KRT k1'in hatali kilit tespiti sinifi; benim ilk kosumum bu yuzden gecersizdi).

## Test kalitesi (implementer; 190 test, mutant 30/30, kapsam %99.59)

- Beklentiler literal; ozel mekanizma (`_yokla`, `_ac`) kancalanmiyor (kural 7). Totoloji yok; `test_k2_kapali_sag_kenara_bitisik_dikey_orta` referansi urunun saf fonksiyonundan alir ama `right()==g.right()` ve merkezle bagimsiz da dogrular. Izgara testleri ozellik (contains/bitisik/kapsar) olcuyor.
- Sabit `qtbot.wait`: `100 ms` titreme (paketin sayisi), `acilma_ms//2` alt sinir (deterministik), `_ust_sinir` gevsek ust sinir -- CI titremesine karsi dogru desen.
- Offscreen'de anlamsiz: `test_k6_paint_100_kare_medyani` (0.07 ms, 16 ms esigi yalniz 100x regresyonu gorur; gercek olcu kapi [7], pozitif kontrol KRT); `test_k1_kabuk_qapplication_quit_cagirmaz`in davranissal yarisi (`qtbot.wait(20)`) bos, AST yarisi gercek olcu; `test_k5_tepsi_varken_goster_gizle` offscreen quirk'e (isVisible True) dayanir -- hepsi etiketli.
- `test_k1_gorunur_yollari_hepsi_ayni_uclu`: `dugme_goster.click()` panel KAPALIYKEN (gizli dugme) -- gercekci degil; benim `test_b1[panel_dugme_goster]` once acar.
- Mutant kitinde olmayan siniflar (benim testlerim kapatir): dis `sekme.close()` (O-B1), `app.quit()` semantigi (`test_c2x10`), demo Esc (`test_f1`), yeniden giris (`test_c2x1`), `availableGeometryChanged` panel acikken, `hideEvent` `_surukleme` temizligi (M28 yalniz release'i), kapat sonrasi `show()`, tuple donen callable, `calistir` x2, gercek WM_CLOSE tepsi/kenar (S5), Shell ikon kaydi bagimsiz kanal (S2), Alt-Tab yapisal (S1), z-sirasi (S6), dpr 1.25 birincil (S7).

## Ozet

Modul paket v2'yi uyguluyor; istek satirlarinin tamami ya karsilaniyor ya paket kararıyla belgeli (kisayol, yatay tasima, 3. kucuk dugme). Kalan risk kabugun disinda ve olculmus: **(1)** sefin demo entegrasyonunda Esc uygulamayi kapatiyor (Y-B1) ve secim sirasinda panel katmanin ustune cikiyor (O-B2) -- ikisi de `demo/kabuk.py`de 3-5 satir; **(2)** dis `close()` yolu (O-B1) ve ilk-kullanim gorunurlugu (O-B3) implementer'a bir sonraki turda 5'er satirlik oneri, ret sebebi degil; **(3)** gercek fare girdisi kalemleri (tepsi tiki + on plan, sag tik on plan, balon suresi) bu oturumda **oturum kilidi** yuzunden olculemedi -- sef/implementer/KRT kosumlarina dayaniyor, `bekle_ve_kos.py` kilit acilirsa kendiliginden olcup `tester_B_evidence/` altina yazar.
