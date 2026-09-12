---
task: T-012
role: implementer
round: 1
status: tamamlandi
files_written:
  - src/ui/__init__.py
  - src/ui/__main__.py
  - src/ui/uygulama.py
  - src/ui/kabuk.py
  - src/ui/kenar_sekmesi.py
  - src/ui/geometri.py
  - tests/unit/ui/test_geometri.py
  - tests/unit/ui/test_kenar_sekmesi.py
  - tests/unit/ui/test_kabuk.py
  - tests/unit/ui/test_uygulama.py
  - .agents/tasks/T-012/delivery.md
  - .agents/tasks/T-012/evidence/tdd-kirmizi-1-modul-yok.txt
  - .agents/tasks/T-012/evidence/tdd-kirmizi-2-5c-balon.txt
  - .agents/tasks/T-012/evidence/mypy.txt
  - .agents/tasks/T-012/evidence/mypy-tur1-son.txt
  - .agents/tasks/T-012/evidence/mypy-test-dosyalari.txt
  - .agents/tasks/T-012/evidence/mypy-test-dosyalari-tur1-son.txt
  - .agents/tasks/T-012/evidence/pytest.txt
  - .agents/tasks/T-012/evidence/pytest-tur1-son.txt
  - .agents/tasks/T-012/evidence/cov.txt
  - .agents/tasks/T-012/evidence/cov-tur1-son.txt
  - .agents/tasks/T-012/evidence/pytest-cp1254.txt
  - .agents/tasks/T-012/evidence/pytest-cp1254-tur1-son.txt
  - .agents/tasks/T-012/evidence/pytest-tum.txt
  - .agents/tasks/T-012/evidence/pytest-tum-kosum1-t011-sure-titremesi.txt
  - .agents/tasks/T-012/evidence/pytest-tum-ui-haric-t011-sure-titremesi.txt
  - .agents/tasks/T-012/evidence/pytest-tum-tur1-son.txt
  - .agents/tasks/T-012/evidence/pytest-tum-tur1-son-kosum2.txt
  - .agents/tasks/T-012/evidence/real_check-dogrudan-kosum.txt
  - .agents/tasks/T-012/evidence/real_check-on-plan-sarici.py
  - .agents/tasks/T-012/evidence/real_check.txt
  - .agents/tasks/T-012/evidence/real_check-tur1-son.txt
  - .agents/tasks/T-012/evidence/olcum-5c-sag-tik-teshis.py
  - .agents/tasks/T-012/evidence/olcum-5c-sag-tik-teshis.txt
  - .agents/tasks/T-012/evidence/olcum-5c-sag-tik-teshis-onplan.txt
  - .agents/tasks/T-012/evidence/olcum-5c-sag-tik-teshis-onplan-duzeltme-sonrasi.txt
  - .agents/tasks/T-012/evidence/olcum-5c-balon.py
  - .agents/tasks/T-012/evidence/olcum-5c-balon.txt
  - .agents/tasks/T-012/evidence/olcum-paint-ve-giris-noktasi.py
  - .agents/tasks/T-012/evidence/olcum-paint-ve-giris-noktasi.txt
  - .agents/tasks/T-012/evidence/olcum-t011-sure-titremesi.py
  - .agents/tasks/T-012/evidence/olcum-t011-sure-titremesi.txt
  - .agents/tasks/T-012/evidence/mutant-kiti.py
  - .agents/tasks/T-012/evidence/mutant-ayirt-etme.txt
  - .agents/tasks/T-012/evidence/mutant-ayirt-etme-hangi-testler.txt
commands:
  - cmd: "python -m mypy --strict --explicit-package-bases src/ui  (6 dosya, temiz)"
    exit_code: 0
    evidence: evidence/mypy-tur1-son.txt
  - cmd: "python -m pytest tests/unit/ui -q -p no:cacheprovider  (190 passed: 188 + 2 yeni [5c] testi; sefin 2 bariyer testi dahil)"
    exit_code: 0
    evidence: evidence/pytest-tur1-son.txt
  - cmd: "python .agents/tasks/T-012/evidence/real_check-on-plan-sarici.py  (= python .agents/tasks/T-012/real_check.py, on plan kosuluyla cocuk surec; kapi v2 + sef [8] GetMonitorInfo referansi: TEMIZ 18/18; [4a] 160 ms, [4b] 478 ms, [5c] ok, [7] 0.22/0.21 ms, [8] fark=+1 px)"
    exit_code: 0
    evidence: evidence/real_check-tur1-son.txt
  - cmd: "python -m pytest tests/unit/ui -q -p no:cacheprovider --cov=src.ui --cov-fail-under=95 --cov-report=term-missing  (487 ifade, %99.59; eksik: uygulama.py 36/40 = gercek `sys.argv` ve `app.exec()` dallari, taze surecte olculdu)"
    exit_code: 0
    evidence: evidence/cov-tur1-son.txt
  - cmd: "python -m pytest tests -q -p no:cacheprovider  (tam takim kosum 1: 2087 passed)"
    exit_code: 0
    evidence: evidence/pytest-tum-tur1-son.txt
  - cmd: "python -m pytest tests -q -p no:cacheprovider  (tam takim kosum 2: 2087 passed)"
    exit_code: 0
    evidence: evidence/pytest-tum-tur1-son-kosum2.txt
  - cmd: "python -m mypy --strict --explicit-package-bases tests/unit/ui/test_geometri.py tests/unit/ui/test_kenar_sekmesi.py tests/unit/ui/test_kabuk.py tests/unit/ui/test_uygulama.py  (4 test dosyasi, temiz)"
    exit_code: 0
    evidence: evidence/mypy-test-dosyalari-tur1-son.txt
  - cmd: "cmd /c cp1254.cmd  (chcp 1254, PYTHONIOENCODING/PYTHONUTF8 bos, sys.stdout.encoding=cp1254; python -m pytest tests/unit/ui -q: 190 passed)"
    exit_code: 0
    evidence: evidence/pytest-cp1254-tur1-son.txt
  - cmd: "python -m pytest tests/unit/ui -q -p no:cacheprovider --no-header -rf --tb=line  (TDD KIRMIZI 1: testler modul yokken, 4 toplama hatasi)"
    exit_code: 2
    evidence: evidence/tdd-kirmizi-1-modul-yok.txt
  - cmd: "python -m pytest tests/unit/ui/test_kabuk.py -q -p no:cacheprovider -k 'balonu_gostermez or surukleme_sonrasi_sag_tik'  (TDD KIRMIZI 2: [5c] kok neden testi duzeltme ONCESI kodda 1 failed; K8 sag tik yolu offscreen'de zaten yesil)"
    exit_code: 1
    evidence: evidence/tdd-kirmizi-2-5c-balon.txt
  - cmd: "python .agents/tasks/T-012/evidence/mutant-kiti.py  (ayna agaci; 30 davranis mutanti 30/30 yakalandi, 3 kontrol kacti; M26-M28 yeni)"
    exit_code: 0
    evidence: evidence/mutant-ayirt-etme.txt
  - cmd: "python .agents/tasks/T-012/evidence/olcum-5c-sag-tik-teshis.py onplansiz  ([5c] teshis, on plan ALINMADAN: V1-V5 hepsi OK -- ihlal uretilemedi)"
    exit_code: 0
    evidence: evidence/olcum-5c-sag-tik-teshis.txt
  - cmd: "python .agents/tasks/T-012/evidence/real_check-on-plan-sarici.py .agents/tasks/T-012/evidence/olcum-5c-sag-tik-teshis.py onplan  ([5c] teshis, kapinin birebir dizisi, duzeltme ONCESI: V6 IHLAL -- sag tik oncesi WindowFromPoint = Windows.UI.Core.CoreWindow (baska surec); V7 OK)"
    exit_code: 0
    evidence: evidence/olcum-5c-sag-tik-teshis-onplan.txt
  - cmd: "python .agents/tasks/T-012/evidence/olcum-5c-balon.py  ([5c] kok neden: tepsiye_al() balonu 'Yeni bildirim' rect (2164,1239)-(2560,1392), omur ~6.2 s (ms=2500 yok sayilir), sekme alt-sinir rect'ini orter; bildir kapaliyken 12 s hep sekme)"
    exit_code: 0
    evidence: evidence/olcum-5c-balon.txt
  - cmd: "python .agents/tasks/T-012/evidence/real_check-on-plan-sarici.py .agents/tasks/T-012/evidence/olcum-5c-sag-tik-teshis.py onplan  (ayni V6/V7 duzeltme SONRASI: V6 OK)"
    exit_code: 0
    evidence: evidence/olcum-5c-sag-tik-teshis-onplan-duzeltme-sonrasi.txt
  - cmd: "python .agents/tasks/T-012/evidence/olcum-t011-sure-titremesi.py  (T-011 K5 8000 uyeli zincir: bosta 26-28 ms 0/5 asim; 2 is parcacigi CPU yuku 59-106 ms 5/5 asim -- T-012 modulu degil)"
    exit_code: 0
    evidence: evidence/olcum-t011-sure-titremesi.txt
  - cmd: "python .agents/tasks/T-012/evidence/olcum-paint-ve-giris-noktasi.py  (paint 100 kare medyani offscreen kapali 0.07-0.09 / acik 0.13-0.16 ms, 5 tekrar; taze surec calistir() rc=0 quitOnLastWindowClosed=False; python -m src.ui 2 s ayakta)"
    exit_code: 0
    evidence: evidence/olcum-paint-ve-giris-noktasi.txt
  - cmd: "python .agents/tasks/T-012/real_check.py  (DOGRUDAN, arka plan kabugundan: [3] on kosul duser -- sahne on plana alinamiyor (Windows on plan kilidi); sarici bu yuzden gerekli)"
    exit_code: 1
    evidence: evidence/real_check-dogrudan-kosum.txt
  - cmd: "python .agents/tasks/T-012/evidence/real_check-on-plan-sarici.py  (tur-1 ILK kosum, duzeltme ONCESI: 3 denemede de yalniz [5c] IHLAL)"
    exit_code: 1
    evidence: evidence/real_check.txt
contract_change_request: false
known_gaps:
  - "[KAPI] real_check v2 (sef [8] GetMonitorInfo referansi) bu turda TEMIZ 18/18 (`real_check-tur1-son.txt`). Kapi itirazi YOK. [8] RAPOR: ikinci monitor dpr=1.25, sekme fiziksel sag=1, monitor calisma alani sag=0, fark=+1 px (KRT G4 prototipte de +1; Qt mantiksal (-538,525,26,52) -> fiziksel x=-2560+round(2022*1.25)=-32, w=round(32.5)=33 -> sag=1; +-1 kabul). Kapi ARKA PLAN kabugundan dogrudan kosulunca [3] on kosulu duser (`real_check-dogrudan-kosum.txt`: sahne `activateWindow()` Windows on plan kilidine takilir); `evidence/real_check-on-plan-sarici.py` fare 6 s bosta kalinca kendi penceresine gercek tik yapip on plani alir, `AllowSetForegroundWindow(ASFW_ANY)` sonrasi kapiyi cocuk surec olarak kosar (kapiya dokunulmaz). Sef etkilesimli terminalden kosarsa sarici gerekmez."
  - "[5c KOK NEDENI -- OLCULDU, DUZELTILDI] Tur-1 ilk kapi kosumunda [5c] 3/3 IHLAL (`real_check.txt`). Teshis (`olcum-5c-sag-tik-teshis*.txt`): on plan alinmadan V1-V5 (surukleme / acma-kapama / gercek tiklar / tam dizi) hepsi OK; kapinin BIREBIR dizisi V6 (tepsi turu + sahne on planda) IHLAL -- sag tik oncesi `WindowFromPoint` sekme degil `Windows.UI.Core.CoreWindow` (BASKA surec), Qt olay gunlugu bos, `WM_ACTIVATEAPP` (on plan baska surece gecti); V7 (yalniz on plan + surukleme) OK. Kok neden (`olcum-5c-balon.txt`): [1a] `tepsiye_al()` -> `bildir()` -> Windows bildirim balonu 'Yeni bildirim' rect (2164,1239)-(2560,1392) = sag altta 396x153 px, omur ~6.2 s (istenen `ms=2500` yok sayilir); [5a] sekmeyi alt sinira (y=1340, rect (2534,1340)-(2560,1392)) surukler, [5c] ~5.5 s sonra oraya sag tiklar -> tik balona gider. `bildir` kapaliyken 12 s boyunca nokta hep sekme (negatif kontrol). Sefin uc hipotezi olculdu ve elendi: imlec konumu dogru (GetCursorPos = hedef), `mousePressEvent` sag dugme yolu calisiyor (V1-V5, V7), `surukleniyor` birakinca False, sag tik press'te (M27/M28 mutantlari bu siniflari test kitinin yakaladigini gosterir). DUZELTME: `AnaPencere.tepsiye_al()` balon gostermez (prototip `demo/kabuk.py` gosteriyordu -- PROTOTIPTEN SAPMA, gerekce: kabugun kendi bildirimi kendi sekmesini 6 s ortmemeli, sure kontrol edilemiyor, balon bildirim merkezinde birikiyor; dugme tooltip'i 'tepsi ikonuna tik geri getirir' ipucunu tasiyor). `Tepsi.bildir` API'si paket arayuzunde kaldi. Testler: `test_k5_tepsiye_al_bildirim_balonu_gostermez` (`showMessage` casusu, pozitif kontrollu; duzeltme oncesi KIRMIZI, `tdd-kirmizi-2-5c-balon.txt`) ve `test_k8_surukleme_sonrasi_sag_tik_pencereyi_getirir` (sefin istedigi offscreen `qtbot.mouseClick(RightButton)` yolu; bu yol hic bozuk degildi, duzeltme oncesi de yesil). Kapi duzeltme sonrasi [5c] ok; V6 tekrar OK (`...-duzeltme-sonrasi.txt`)."
  - "[ÖLÇÜLMÜYOR -- shell ust bandi] Baska uygulamalarin bildirim balonlari, Baslat, bildirim merkezi, gorev cubugu acilir pencereleri sekmenin USTUNDEDIR (`WindowStaysOnTopHint` shell bandinin ustune cikamaz): sag alt banda (y >= alt sinir - ~100) suruklenmis sekme bir balon suresince (~6 s) gorunmez ve tik/hover almaz. Yalniz kabugun kendi balonu olculdu (yukarida); genel sinif olculmedi, bilinen sinir."
  - "[ÖLÇÜLMÜYOR -- topmost/exclusive oyun] Borderless-topmost ya da exclusive tam ekran oyun sekmeden SONRA gosterilince ustte kalir (KRT k5 Z2); sekme gorunmez. `_ac()` icinde `raise_()` ucuz iyilestirme (yoklamada degil, K6 blok yok). Tasarim 5.6 'borderless'a gec' uyarisi; olcusu yok."
  - "[ÖLÇÜLMÜYOR -- yatay / monitorler arasi tasima] Paket v2: yalniz dikey `y`; yatay ve baska monitore surukleme v2 (farkli dpr'li monitorler arasinda 512 px mantiksal bosluk, T-003 gerekir; K7 `src.capture` importunu yasaklar). `mouseMoveEvent` x'i yok sayar."
  - "[ÖLÇÜLMÜYOR -- global kisayollar] `Ctrl+Alt+T/R` (istek: tepsideyken calismaya devam eder) bu paketin disinda; HotkeyService ayri gorev. Kabuk kisayol bilmez."
  - "[ÖLÇÜLMÜYOR -- monitor cikarma] `screenRemoved` bagli degil: yapiciya verilen `QScreen` silinirse Qt nesnesi olur, sonraki `availableGeometry()`/sinyal erisimi `RuntimeError`. Birincile tasima sonraki surum. `availableGeometryChanged` BAGLI (gorev cubugu tasininca yeniden konumlanir; sahte sinyalle olculdu)."
  - "[ÖLÇÜLMÜYOR -- gorev cubugu sagda/solda] KARAR: `ekran = availableGeometry()` (cubukla cakismaz). Cubuk sagda iken `sag` sekme fiziksel kenara bitisik DEGIL (cubugun solunda yuzer; KRT G3: x [2486,2511], fiziksel kenar 2559); cubuk solda iken `sol` icin ayni. Cubuk altta/ustte sorun yok (bu makine: altta, 48 px; olculen kapali rect (2534,670,26,52) U2 birebir)."
  - "[ÖLÇÜLMÜYOR -- bildirim kapali] `Tepsi.bildir` bildirimler/odak yardimi kapaliyken sessizce yok olur (offscreen hata yok, KRT o12); sistem ayari degistirilmedi. Urun akisinda artik yalniz cagiranlar kullanir (kabuk cagirmiyor)."
  - "[ÖLÇÜLMÜYOR birim -- DPI fiziksel yuvarlama] Geometri mantiksal pikselde dogru (3 ekran x 2 kenar x 5 y, U2 birebir); dpr != 1.0 monitorde fiziksel kenar yuvarlamasi birim testte olculemez; `real_check` [8] ikinci monitorde +1 px olctu (yukarida). Kabul: +-1. Sekme `setScreen` cagirmaz; Qt geometriden ekrani secer -- [8] bunun dogru monitore dustugunu (`MonitorFromWindow` = sol monitor) gosterir."
  - "[ÖLÇÜLMÜYOR -- activeWindow offscreen] K3 odak degismezi offscreen'de olculemez (platform bayraklari uygulamaz, KRT k2b): `test_k3_bayraklar_ve_oznitelikler` yapisaldir; gercek davranis yalniz `real_check` [3a]/[3b] gercek OS tiki (on plan sahne kaldi, clicked=1). Sef pozitif kontrolu (bayraksiz pencere on plani alir, KRT k5b T2) `sef_dogrulama/`ya bir kez yazar."
  - "[ÖLÇÜLMÜYOR -- ornekleme fazi] 50/50 ms iceri-disari titremesinde yoklama fazina bagli tek tuk acilma olabilir (<= 1 yoklama; KRT k1 P2 1/10). Belgeli; olcusu yok."
  - "[ÖLÇÜLMÜYOR -- bosta CPU] Yoklayici yalniz gorunurken calisir (`test_k4_yoklayici_yalniz_gorunurken`, enjekte callable cagri sayar); %0.3 tek cekirdek KRT k4b olcumudur, bu turda yeniden olculmedi."
  - "[T-011 SURE TITREMESI -- T-012 modulu DEGIL] Tam takim tur-1 ilk kosumlarinda `tests/unit/translate/test_sozluk.py::test_k5_sure_8000_uyeli_zincir_60ms_alti` iki kez dustu (`pytest-tum-kosum1-t011-sure-titremesi.txt` gecerli 62.3 ms; `pytest-tum.txt` 68.5 ms; sinir 60; UI haric kosumda da dustu: `pytest-tum-ui-haric-t011-sure-titremesi.txt` -> UI testleriyle ilgisiz). Duzeltme sonrasi iki tam takim kosumu temiz (2087/2087 x2). Olcum (`olcum-t011-sure-titremesi.txt`, testin kendi yardimcilariyla): bosta 26-28 ms (0/5 asim, 2x pay); 2 is parcacigi CPU yuku altinda 59-106 ms (5/5 asim). KOSUL: makinede es zamanli yuk (o sirada gercek ekran kapi/teshis betikleri kosuyordu). Sinir yukte asilir; T-011 sahibinin kalemi."
  - "[PAKETIN BIR ADIM OTESI] (a) `KenarSekmesi` parametre dogrulama: `yaricap >= 1`, `acilma_ms/kapanma_ms >= 0`, `yoklama_ms >= 1`, aksi `ValueError` (paket sessiz). (b) `kapandi`, `yokluyor`, `ekran_dikdortgeni` salt-okunur ozellikleri (test/kapi gozlemi icin). (c) `kapat()` sonrasi `goster()/tepsiye_al()/kenara_al()` DIRILTMEZ (paket yalniz sinyal sayisini soyler). (d) `kenar` durumunda `tepsiye_al()` kenari korur (paket: `kenar -> tepsi yok`). (e) `hideEvent` paneli kapatir ve surukleme bayragini temizler: yeniden gosterilince kapali gelir. (f) `Tepsi.bildir` tepsi yokken sessiz. (g) `uygulama.calistir(..., calistirici=None)` enjekte edilebilir kosucu (birim testte `exec()` cagirmadan kurulum sinanir; gercek `exec()` + 0 ms `kapat()` ayrica olculur)."
  - "[PAKET ARAYUZU -- `y` ozelligi `QWidget.y()`yi golgeler] Paket `y: int` okunur-yazilir ozellik ister ve kapi `s.y` okur; bu, tabanin `QWidget.y()` YONTEMINI golgeler (`sekme.y()` -> `TypeError`; `# type: ignore[override]`). Pencerenin gercek konumu `frameGeometry()`/`pos()`; `s.y` her zaman KAPALI sekmenin ust kenaridir (panel acikken pencere y'si panelin ustudur, `s.y` degismez). Docstring'de belgeli."
  - "[K5 ISTISNASI] Tepsi yokken `tepsiye_al()` -> `kenar` uclusu (F,T,F); K1 tablosuna `kenar (tepsi yok)` satiri olarak eklendi (paket v2 ▲). Offscreen'de `isSystemTrayAvailable()` False; `AnaPencere(tepsi_kullanilabilir=True)` ile iki dal da olculur."
  - "[K6 PAINT] 100 kare medyani: offscreen kapali 0.07-0.09 / acik 0.13-0.16 ms (5 tekrar; `paintEvent` cagri sayisi 500+500 = repaint gercekten ciziyor); gercek ekran (`real_check` [7]) kapali 0.22 / acik 0.21 ms. Acik halde `paintEvent` hicbir sey cizmez (panel `QFrame` kendi stilini cizer), bu yuzden acik <= kapali."
  - "[EVIDENCE] Tur-1 ilk kosum delilleri (`-tur1-son` eki olmayanlar: `mypy.txt`, `pytest.txt`, `cov.txt`, `pytest-cp1254.txt`, `pytest-tum*.txt`, `real_check.txt`) duzeltme ONCESI koddur (188 test); `-tur1-son` ekli olanlar duzeltme sonrasi (190 test). `git add`/`commit` ATILMADI. Delillerde mutlak yol yok (`<depo>`, `<gecici dizin>`, `<yol>`)."
---

# T-012 tur 1 -- teslim ozeti

`src/ui/`: `geometri.py` (saf: `Kenar`, `PANEL_BOYUTU`, `y_sinirla`, `sekme_kapali_dikdortgeni`, `sekme_acik_dikdortgeni`, `sekme_icinde` disk testi), `kenar_sekmesi.py` (`KenarSekmesi`: yarim daire + panel, yoklama tabanli zamanlama, enjekte imlec, surukleme, mod tiki once kapanir, sag tik / `dugme_goster`), `kabuk.py` (`AnaPencere` uc dugme + iki mod dugmesi, `Tepsi`, `KabukDurumu`, `closeEvent == kapat()`, idempotent `kapat()`), `uygulama.py` + `__main__.py` (`calistir`: `QApplication`, `setQuitOnLastWindowClosed(False)`, `cikis_istendi -> app.quit`). Paket v2'nin ▲ maddelerinin tamami uygulandi. **190 birim testi**, kapsam %99.59, mypy --strict modul + testler temiz, tam takim 2087 x2, **kapi TEMIZ 18/18**, mutant 30/30.

Oturum yarida kesilmisti; bu teslim devralan oturumun teslimidir. Kalan is: kapidaki tek ihlal ([5c]) olculdu ve duzeltildi, tam takim yeniden kosuldu, `known_gaps` ve bu belge yazildi.

## [5c] -- kok neden (olculdu) ve duzeltme

| adim | olcum | dosya |
|---|---|---|
| Ilk kapi kosumu | 3/3 denemede yalniz `[5c] sag tik: uclu=(F,T,T) durum=kenar` | `real_check.txt` |
| Teshis, on plan alinmadan | V1 surukleme / V2 acma-kapama / V3 gercek tiklar / V4 tam dizi / V5 panel acikken: **5/5 OK** -- ihlal uretilemedi | `olcum-5c-sag-tik-teshis.txt` |
| Teshis, kapinin birebir dizisi (sarici ile) | **V6 IHLAL**: sag tik oncesi `WindowFromPoint(2555,1365)` = `Windows.UI.Core.CoreWindow` (BASKA surec); Qt olay gunlugu `[]`; `WM_ACTIVATEAPP`. V7 (yalniz on plan + surukleme) OK -> fark [1a] tepsi turu | `olcum-5c-sag-tik-teshis-onplan.txt` |
| Kok neden | `tepsiye_al()` -> `bildir()` -> balon "Yeni bildirim" rect (2164,1239)-(2560,1392), 396x153 px, **omur ~6.2 s** (`ms=2500` yok sayilir), kapali sekmenin alt-sinir rect'i (2534,1340)-(2560,1392) ile **kesisir**; `bildir` kapaliyken 12 s nokta hep sekme; tekrar (C) ayni | `olcum-5c-balon.txt` |
| Sefin hipotezleri | imlec konumu dogru; `mousePressEvent` sag dugme yolu calisiyor; `surukleniyor` birakinca False; sag tik press'te -- hepsi elendi (V1-V5/V7 gunlukleri: `MouseButtonPress:RightButton`, `GetCapture=0`, `surukleniyor=False`) | `olcum-5c-sag-tik-teshis*.txt` |
| Duzeltme | `AnaPencere.tepsiye_al()` balon gostermez; `Tepsi.bildir` API'si kalir; docstring K5 gerekcesi | `src/ui/kabuk.py` |
| Test (TDD) | `test_k5_tepsiye_al_bildirim_balonu_gostermez` duzeltme oncesi KIRMIZI (1 failed); `test_k8_surukleme_sonrasi_sag_tik_pencereyi_getirir` (offscreen `qtbot.mouseClick(RightButton)`, sefin istegi) yesil | `tdd-kirmizi-2-5c-balon.txt` |
| Dogrulama | kapi TEMIZ 18/18 ([5c] ok); V6 tekrar OK; mutant M26 (balon geri eklendi) tam 1 testle yakalandi | `real_check-tur1-son.txt`, `...-duzeltme-sonrasi.txt`, `mutant-ayirt-etme.txt` |

## K1-K8 -- uygulama ve olcu

| K | uygulama (docstring'de ayrintili) | olcu (test / kapi) |
|---|---|---|
| K1 durum makinesi | Uclu tablosu `gorunur` (T,F,F) · `tepsi` (F,F,T) · `kenar` (F,T,T) · `kenar (tepsi yok)` (F,T,F); `goster()` tepsi ikonunu da gizler; `kenar -> tepsi` yok; `closeEvent` her durumda `kapat()` (ignore yok); `kapat()` idempotent (`kapandi` bayragi, `hide()`), `cikis_istendi` tam bir kez; dirilme yok; kabuk `quit()` cagirmaz | 23 `test_k1_*` (25 kosum): her gecis + uclu; `kapat();kapat()` -> 1; `close()` -> (F,F,F) + 1; `tepsiye_al()` x2; fixture teardown `kapat()`; `real_check` [1a][1b][6a][6b][6c] |
| K2 geometri | Saf modul; `availableGeometry` + `availableGeometryChanged`; `sag` x = right-r+1, `sol` x = left; panel bitisik, dikey merkeze hizali, ekrana sikistirilmis; `y_sinirla` monoton; `sekme_icinde` disk (kapali) / dikdortgen (acik); `sol` cizim aynali | 84 `test_geometri` (3 ekran x 2 kenar x 5 y izgara, U2 birebir, disk kose/merkez) + 13 `test_k2_*` (sekme/kabuk: bitisik, sinirlar, sol kenar, sahte `availableGeometryChanged`, `grab()` alfa); `real_check` [2a][4a][8] |
| K3 odak | `Frameless|Tool|StaysOnTop|DoesNotAcceptFocus`, `WA_TranslucentBackground`, `WA_ShowWithoutActivating`, `NoFocus` (dugmeler de); pencere yalniz sekme/panel kadar; `_ac()` icinde `raise_()` | `test_k3_bayraklar_ve_oznitelikler` (yapisal), `test_k3_kapali_ve_acik_boyutlar`; `activeWindow` offscreen `[ÖLÇÜLMÜYOR]`; `real_check` [2b][3a][3b] gercek OS tiki |
| K4 zamanlama | Yoklayici (`yoklama_ms`) yalniz gorunurken; `sekme_icinde` -> acilma/kapanma tek atim sayaclari; titreme sifirlar; surukleme: press acilmayi durdurur, yoklama sayac baslatmaz, `acik` degismez, birakinca sifirdan; mod tiki once `_kapat()` sonra sinyal; imlec yalniz enjekte callable | 25 `test_k4_*`: deterministik alt sinir + gevsek ust sinir, titreme, kose, enjekte callable sayaci, surukleme x4, mod tiki x3; `real_check` [4a] 160 ms [4b] 478 ms [5a][5b][9] |
| K5 tepsi | `kullanilabilir=None` -> platform; yoksa `goster()` yok, `gorunur()` daima False, `bildir` sessiz; menu 3 eylem; `Trigger`/`DoubleClick` -> goster; `tepsiye_al()` tepsi yoksa `kenara_al()`; **`tepsiye_al()` balon gostermez** | 14 `test_k5_*` (iki dal, menu adlari, sinyaller, activated sebepleri, balon casusu pozitif kontrollu); `real_check` [1a] |
| K6 modal/metin/blok yok | AST: yasak ad/import yok (pozitif kontrollu); `paintEvent` kapali yarim daire + "S", acik hicbir sey | `test_k6_k7_*` (AST + pozitif kontrol), `test_k6_paint_100_kare_medyani_kapali_ve_acik`; `real_check` [7] 0.22/0.21 ms |
| K7 bagimsiz | `src.capture/ocr/translate` import yok (AST + taze surec `sys.modules`); pencere ve sekme dugmeleri ayni sinyal; dinleyicisiz calisir; mod sinyali durumu degistirmez | `test_k7_*` x3 |
| K8 surukleme/erisilebilirlik | Ust 44 px seritten sol surukleme tasir, dugmede/govdede baslamaz; `accessibleName` {Kapat, Tepsiye al, Kenara al}; sekme `toolTip` sag tik ipucu; panelde `dugme_goster`; sag tik (kapali/acik) `pencereyi_goster` | 10 `test_k8_*` (surukleme x3, tooltip/accessible, sag tik press, acikken sag tik, `dugme_goster`, surukleme sonrasi `mouseClick(RightButton)`); `real_check` [5c] |

## Mutant ayirt etme (`evidence/mutant-ayirt-etme.txt`; test adlari `-hangi-testler.txt`)

30 davranis mutanti **30/30 yakalandi**; 3 kontrol (C-1 kenara_al sirasi, C-2 disk esitsizligi `**`, C-3 `_konumlan` gecici degisken) kacti (beklenen). M01-M25 onceki oturum; **M26** tepsiye_al balon gosterir (1 test: yeni K5), **M27** sag tik release'te (2 test), **M28** surukleme bayragi takili (4 test) -- sefin [5c] hipotez siniflari kitte olculur. En dar ayirt etme 1 testle: M05b, M12, M14, M17b, M19, M20, M21, M22, M23, M24, M26.

## Sayilar

| olcu | sonuc |
|---|---|
| birim | 190 passed (188 + 2); kapsam %99.59 (487 ifade; eksik 2: `uygulama.py` gercek `sys.argv`/`exec()` dallari, taze surecte olculdu); mypy --strict modul 6 dosya + 4 test dosyasi temiz |
| TDD kirmizi | (1) modul yokken 4 toplama hatasi; (2) [5c] balon testi duzeltme oncesi 1 failed |
| kapi (real_check v2, sef [8] referansi) | TEMIZ 18/18; [4a] 160 ms, [4b] 478 ms, [7] 0.22/0.21 ms, [8] +1 px; duzeltme oncesi 1 IHLAL ([5c]) |
| tam takim | 2087 passed x2 (ilk kosumlarda T-011 sure testi 2 kez dustu: 62.3 / 68.5 ms; yuk altinda, `known_gaps`) |
| mutant | 30/30 yakalandi; 3 kontrol kacti |
| cp1254 | 190 passed, `PYTHONIOENCODING` yok |
| paint | offscreen 0.07-0.09 / 0.13-0.16 ms; gercek 0.22 / 0.21 ms |
