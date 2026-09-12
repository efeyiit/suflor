---
task: T-012
role: implementer
round: 2
status: tamamlandi
files_written:
  - src/ui/kabuk.py
  - src/ui/kenar_sekmesi.py
  - src/ui/geometri.py
  - tests/unit/ui/test_kabuk.py
  - tests/unit/ui/test_kenar_sekmesi.py
  - tests/unit/ui/test_geometri.py
  - .agents/tasks/T-012/delivery.md
  - .agents/tasks/T-012/evidence/tdd-kirmizi-3-tur2-yeni-testler-eski-kodda.txt
  - .agents/tasks/T-012/evidence/mypy-tur2.txt
  - .agents/tasks/T-012/evidence/mypy-test-dosyalari-tur2.txt
  - .agents/tasks/T-012/evidence/pytest-tur2.txt
  - .agents/tasks/T-012/evidence/cov-tur2.txt
  - .agents/tasks/T-012/evidence/pytest-tum-tur2.txt
  - .agents/tasks/T-012/evidence/pytest-tum-tur2-kosum2.txt
  - .agents/tasks/T-012/evidence/pytest-tum-tur2-kosum3.txt
  - .agents/tasks/T-012/evidence/pytest-t011-sure-testi-tek-basina-tur2.txt
  - .agents/tasks/T-012/evidence/pytest-cp1254-tur2.txt
  - .agents/tasks/T-012/evidence/real_check-tur2-KILIT.txt
  - .agents/tasks/T-012/evidence/mutant-kiti.py
  - .agents/tasks/T-012/evidence/mutant-ayirt-etme-tur2.txt
  - .agents/tasks/T-012/evidence/mutant-ayirt-etme-hangi-testler.txt
  - .agents/tasks/T-012/evidence/olcum-tur2-omur-gercek-platform.py
  - .agents/tasks/T-012/evidence/olcum-tur2-omur-gercek-platform.txt
  - .agents/tasks/T-012/evidence/tester-A-sonda-01-duzeltme-sonrasi.txt
commands:
  - cmd: "python -m mypy --strict --explicit-package-bases src/ui  (6 dosya, temiz)"
    exit_code: 0
    evidence: evidence/mypy-tur2.txt
  - cmd: "python -m pytest tests/unit/ui -q -p no:cacheprovider  (216 passed = 190 + 26 yeni; sefin 2 bariyer testi dahil)"
    exit_code: 0
    evidence: evidence/pytest-tur2.txt
  - cmd: "python .agents/tasks/T-012/real_check.py  (KOSULMADI: oturum kilitli -- on plan LockApp.exe, LogonUI calisiyor; kapi [3]/[5] gercek fare + on plan ister; sef kilit acilinca evidence/real_check-on-plan-sarici.py ile kosar)"
    exit_code: null
    evidence: evidence/real_check-tur2-KILIT.txt
  - cmd: "python -m pytest tests/unit/ui -q -p no:cacheprovider --cov=src.ui --cov-fail-under=95 --cov-report=term-missing  (517 ifade, %99.61; eksik 2: uygulama.py 36/40 gercek sys.argv/exec dallari, tur 1 ile ayni)"
    exit_code: 0
    evidence: evidence/cov-tur2.txt
  - cmd: "python -m pytest tests -q -p no:cacheprovider  (tam takim kosum 1: 2113 passed)"
    exit_code: 0
    evidence: evidence/pytest-tum-tur2.txt
  - cmd: "python -m pytest tests -q -p no:cacheprovider  (tam takim kosum 2: 2112 passed / 1 failed: T-011 tests/unit/translate/test_sozluk.py::test_k5_sure_8000_hit_gom_60ms_alti 60.8 ms > 60 -- yuk-hassas sure testi, T-012 disi, sef karari tur 1 T-011 kalemi)"
    exit_code: 1
    evidence: evidence/pytest-tum-tur2-kosum2.txt
  - cmd: "python -m pytest tests -q -p no:cacheprovider  (tam takim kosum 3: 2113 passed)"
    exit_code: 0
    evidence: evidence/pytest-tum-tur2-kosum3.txt
  - cmd: "python -m pytest tests/unit/translate/test_sozluk.py::test_k5_sure_8000_hit_gom_60ms_alti -q -p no:cacheprovider  (x3 tek basina: 3/3 passed, 0.54 s)"
    exit_code: 0
    evidence: evidence/pytest-t011-sure-testi-tek-basina-tur2.txt
  - cmd: "python -m mypy --strict --explicit-package-bases tests/unit/ui/test_geometri.py tests/unit/ui/test_kenar_sekmesi.py tests/unit/ui/test_kabuk.py tests/unit/ui/test_uygulama.py  (4 test dosyasi, temiz)"
    exit_code: 0
    evidence: evidence/mypy-test-dosyalari-tur2.txt
  - cmd: "cmd /c cp1254.cmd  (chcp 1254, PYTHONIOENCODING/PYTHONUTF8 bos, sys.stdout.encoding=cp1254; python -m pytest tests/unit/ui -q: 216 passed)"
    exit_code: 0
    evidence: evidence/pytest-cp1254-tur2.txt
  - cmd: "python -m pytest tests/unit/ui -q -p no:cacheprovider -rfE --tb=line -k '<tur-2 yeni testler>'  (TDD KIRMIZI 3: 26 yeni test TUR-1 KODUNDA: 19 failed + 1 teardown error (D-A4 yarim kurulu nesne) / 12 passed -- gecenler pozitif kontroller, Tepsi omru (zaten toplaniyordu), panel-AST disiplin bekcisi, eski parametre dallari)"
    exit_code: 1
    evidence: evidence/tdd-kirmizi-3-tur2-yeni-testler-eski-kodda.txt
  - cmd: "python .agents/tasks/T-012/evidence/mutant-kiti.py  (ayna agaci; 40 davranis mutanti 40/40 yakalandi, 5 kontrol kacti; tur 2: M26/M26b/M26c balon, M29/M29b lambda+partial, M30/M30b kapandi, M31/M31b mandal, M32 showNormal, M33 ust sinir; C-4/C-5 yeni kontrol)"
    exit_code: 0
    evidence: evidence/mutant-ayirt-etme-tur2.txt
  - cmd: "python .agents/tasks/T-012/evidence/olcum-tur2-omur-gercek-platform.py  (GERCEK windows platformu, kilitten/fareden bagimsiz: del+gc / deleteLater / tek basina -> weakref None, Win32 IsWindow(hwnd)=False, gorunur ust-duzey 0; pozitif kontrol lambda hwnd yasar: TEMIZ 4/4)"
    exit_code: 0
    evidence: evidence/olcum-tur2-omur-gercek-platform.txt
  - cmd: "python .agents/tasks/T-012/tester_A/sonda_a_01_omur_zombi.py  (Tester-A'nin kendi sondasi, dokunulmadan kosuldu: SONDA TEMIZ; [4] gizli sizinti da yok)"
    exit_code: 0
    evidence: evidence/tester-A-sonda-01-duzeltme-sonrasi.txt
contract_change_request: false
known_gaps:
  - "[KAPI KOSULMADI -- OTURUM KILITLI] `real_check.py` v3 bu turda implementer tarafindan KOSULMADI: oturum boyunca on plan `LockApp.exe` (`Windows.UI.Core.CoreWindow`), `LogonUI.exe` calisiyor (`real_check-tur2-KILIT.txt`, iki kontrol). Kapi [3] (gercek OS tiki + `GetForegroundWindow`) ve [5] (gercek surukleme) kilit ekraninda gecersiz olur (Tester-B tur-1 ilk kosumu). Kilit acilinca sef `evidence/real_check-on-plan-sarici.py` ile kosar. Kapi v3'un yeni kalemi (sürükleme YUKARI, `s.y == g.top()`) offscreen'de `test_k4_surukleme_y_tasir_ve_sinira_kilitlenir` (ust sinir `g.top()`) ve `test_k8_surukleme_sonrasi_sag_tik_pencereyi_getirir` ile karsilanir; [1a] artik balon gosterir (K5 ▲▲) -- balon sag altta, sekme ust sinirda; kesisme yok. Kilitten bagimsiz olan tek gercek-ekran olcumu (omur, Win32 `IsWindow`) `olcum-tur2-omur-gercek-platform.txt` ile yapildi."
  - "[Y-A1 -- OLCULDU, DUZELTILDI] Kok: `kenar_sekmesi.py` uc `clicked.connect(lambda: self._mod_tiki(...))` (eski 222-224). Duzeltme: bagli yontemler `_anlik_tiki/_bolge_tiki/_goster_tiki`; `availableGeometryChanged.connect` yapicinin son satiri (D-A4 ikincil). Olcu (uc kanal): offscreen `weakref`+gc+olay dongusu (`test_k1_omur_kenar_durumunda_ana_pencere_dusunce_sekme_silinir[del_gc|deleteLater]`, `test_k1_omur_son_referans_dusunce_silinir_gorunur_kalmaz[del_gc|deleteLater]`, `test_k1_omur_tepsi_son_referans_dusunce_silinir`), pozitif kontrol (`test_k1_omur_pozitif_kontrol_lambda_baglantisi_sarmalayiciyi_tutar`: lambda'li widget canli+gorunur kalir, bagli yontemli toplanir), yapisal AST bekci (`test_k1_sinyal_baglantilarinda_lambda_yok_ast`); gercek platform Win32 `IsWindow` (`olcum-tur2-omur-gercek-platform.txt`); Tester-A sondasi TEMIZ. On olcum: `.emit` baglantilari ve uzun omurlu `QScreen` gondericisine bagli yontem sarmalayiciyi TUTMAZ (Tepsi zaten toplaniyordu -- test eklendi, kod degismedi). Mutant: M29 lambda geri (4 test), M29b `functools.partial` (3 test; AST bekcisi gormez, omur testleri yakalar). Docstring K1 cumlesi (tur 1'de olculmeden yazilmis ve YANLIS) olcen test adlariyla yeniden yazildi. Not: tek basina `KenarSekmesi` icin `deleteLater` yolu lambda'li kodda da toplaniyordu (C++ silinince baglanti kopar) -- o varyant zayif olcudur; `del`+gc ve `AnaPencere.deleteLater` yollari ayristirir (kirmizi delilde gorulur)."
  - "[O-B1 -- DUZELTILDI] `KenarSekmesi.closeEvent` -> `kapandi` sinyali (yeni, paket v3 arayuzu); `AnaPencere` kenar durumunda `kapandi` -> `goster()` ((T,F,F), tepsisiz konfigurasyonda da). Sekme gizliyken `close()` durum makinesine dokunmaz (gorunur/tepsi korunur). `hide()` `kapandi` YAYMAZ (ayirt edici test). Sira: `closeEvent` icinde `goster()` sekmeyi `hide()` eder (hideEvent: yoklayici durur), ardindan Qt `close()` zaten gizli oldugu icin tekrar gizlemez; olculdu (uclu (T,F,F), `yokluyor False`, `acik False`). Mutant M30 (bagli degil, 2 test), M30b (yayilmiyor, 3 test). `QApplication.quit()` -> `closeAllWindows` yolunda sekme kenar durumundaysa `goster()` cagrilir ve ana pencere gorunur olur; urun `calistir` yalniz `cikis_istendi -> quit` ile cikar (sekme onceden `hide()`), bu yol urunde olusmaz -- `[ÖLÇÜLMÜYOR]`, belge."
  - "[O-A1 -- DUZELTILDI] Tek atimlik mandal `_cikis_bekleniyor`: `_mod_tiki` sonrasi imlec KAPALI diskin icindeyken acilma sayaci baslamaz; diskten bir kez cikinca normal. `hideEvent` mandali sifirlar (yeniden gosterilince taze). Test noktasi dugme ∩ kapali disk kesisiminden (diske en derin nokta) secilir ve on kosul (kesisim bos degil) assert'lenir; iki dugme; `qtbot.wait(acilma_ms + 3*yoklama_ms)` x2 -> `acik False`; disari -> iceri -> acilir (pozitif kontrol). Mutant M31 (2 test), M31b (1 test). Sag tik `_mod_tiki`den gecmez (mandal yok; kabuk sekmeyi gizler). `real_check` [9] dugme MERKEZINDEN tiklar (disk disinda) -> mandal bir sonraki yoklamada silinir, kapi etkilenmez."
  - "[O-B3 / K5 ▲▲ -- UYGULANDI] Ilk `tepsiye_al()` surec basina bir kez `bildir(\"Suflör arka planda\", \"Tepsi ikonuna tıklayınca pencere geri gelir.\", 2500)`; sayac `AnaPencere._balon_gosterildi` (ClassVar; testler `monkeypatch` ile sifirlar -- olcu `showMessage` casusudur, sifirlama kurulumdur). Ornek basina degil (ikinci `AnaPencere` gostermez: `test_k5_balon_surec_basina_bir_kez_ikinci_ornek_de_gostermez`, M26c ayristirir); tepsisiz `tepsiye_al()` sayaci tuketmez. Tur-1 [5c] sinifi kapida cozuldu (surukleme yukari); kalan sinif `tepsi -> kenar` gecisi balon omru (~6 s) icinde + sekme alt-sag bantta -- `[ÖLÇÜLMÜYOR]`, docstring. Balonun gercek ekranda gosterildigi bu turda olculemedi (kilit); tur-1 `olcum-5c-balon.txt` ayni cagriyla balonu olcmustu."
  - "[TESTER-A DUSUK -- UCUZ OLANLAR YAPILDI] D-A1: `goster()` `isMinimized()` ise `showNormal()` (olculdu offscreen `showMinimized` calisiyor; tepsi ve kenar yollari; M32). D-A3+D-A4: `1 <= yaricap <= 66` (`PANEL_BOYUTU.height()//2`, panel sekmeyi kapsar), `acilma/kapanma/yoklama_ms <= 2**31-1`; hepsi `ValueError`, Qt nesnesi yaratilmadan (on olcum: 67 kabul ediliyordu, 2**30 `OverflowError`, ms 2**31 `OverflowError`); 66 tam deger kabul testi; M33. D-A4 ikincil (`connect` en sona): davranissal olcusu YOK -- kontrol mutanti C-4 kacar, belgeli. D-A5 `PANEL_BOYUTU`: `Final` yalniz tip duzeyinde, `QSize` dondurulamaz; KARAR `Final` + docstring + yapisal AST bekci (`src/ui` yerinde degistirmez, pozitif kontrollu) -- dis degistirme tanimsiz, belgeli; 'kopya dondur' (modul `__getattr__`) paket arayuzunu (`Final[QSize]` adi) bulandirdigi icin secilmedi. YAPILMAYANLAR: D-A2 taban sinif `hide()/show()` atlamasi (programatik; `goster()` toparlar; docstring), D-A6/D-A7/D-A8 bilgi. Tester-B D-B2/D-B3/D-B4 belge; test kalitesi notu (`dugme_goster` panel kapaliyken) -> `test_k1_panel_acikken_dugme_goster_pencereyi_getirir` eklendi."
  - "[T-011 SURE TITREMESI -- T-012 DISI] Tam takim kosum 2'de `test_k5_sure_8000_hit_gom_60ms_alti` 60.8 ms > 60 (`_izleyici_payi()` = 1.0); kosum 1 ve 3 temiz (2113/2113), tek basina 3/3 0.54 s. Tur 1'de ayni sinif (`..._zincir_60ms_alti`, 61.5-68.5 ms) sef karari tur 1'de T-011 bakim kalemi olarak yazildi; bu turda ikinci bir test ayni sinifta dustu."
  - "[TDD KIRMIZI 3] 26 yeni testin 19'u + 1 teardown error tur-1 kodunda dusuyor (`tdd-kirmizi-3-...txt`); gecen 12: pozitif kontroller (lambda widget canli; tepsi omru -- kod degismedi), `test_k2_panel_boyutu_kaynakta_degistirilmez_ast` (disiplin bekcisi, TDD kirmizisi DEGIL -- pozitif kontrolle ateslenebilirligi gosterilir), `test_k1_sekme_dis_close_gorunur_ve_tepsi_durumunda_durum_degismez` (eski kodda da dokunmuyordu), `test_k4_yaricap_ust_sinir_tam_degeri_kabul` (66 eskiden de kabul), `test_k4_mod_tiki_mandali_gizlenip_gosterilince_sifirlanir` (mandalin olmadigi kodda da acilir -- M31b ayristirir), 5 eski parametre dali. `[dugme_bolge]` varyantinin kirmizisi ilk nokta secim yardimcisiyla alindi (assert on kosulu dusuyordu); son yardimci (kesisimden secim) ile ayrisma mutant M31 ile gosterildi (2 test)."
  - "[ÖLÇÜLMÜYOR -- shell ust bandi] Baska uygulamalarin bildirim balonlari, Baslat, bildirim merkezi sekmenin USTUNDEDIR; kabugun kendi balonu artik surec basina bir kez (yukarida). Genel sinif olculmedi."
  - "[ÖLÇÜLMÜYOR -- topmost/exclusive oyun] Sekmeden SONRA gosterilen topmost oyun ustte kalir (KRT k5 Z2); `_ac()` `raise_()`; olcusu yok."
  - "[ÖLÇÜLMÜYOR -- yatay / monitorler arasi tasima] Yalniz dikey `y`; v2 (T-003 gerekir)."
  - "[ÖLÇÜLMÜYOR -- global kisayollar] `Ctrl+Alt+T/R` paket disi; HotkeyService ayri gorev."
  - "[ÖLÇÜLMÜYOR -- monitor cikarma] `screenRemoved` bagli degil; verilen `QScreen` silinirse `RuntimeError`. `availableGeometryChanged` bagli (sahte sinyalle olculdu)."
  - "[ÖLÇÜLMÜYOR -- gorev cubugu sagda/solda] `ekran = availableGeometry()`; cubuk sagda iken sekme fiziksel kenara bitisik degil (KRT G3)."
  - "[ÖLÇÜLMÜYOR -- bildirim kapali] `Tepsi.bildir` bildirimler kapaliyken sessizce yok olur; K5 balonu da."
  - "[ÖLÇÜLMÜYOR birim -- DPI fiziksel yuvarlama] Mantiksal pikselde dogru; `real_check` [8] tur 1'de +1 px (kabul +-1); bu turda kapi kosulmadi."
  - "[ÖLÇÜLMÜYOR -- activeWindow offscreen] K3 yapisal test; gercek davranis `real_check` [3] (bu turda kilit)."
  - "[ÖLÇÜLMÜYOR -- ornekleme fazi / bosta CPU] Tur 1 ile ayni (<= 1 yoklama; %0.3 KRT k4b)."
  - "[PAKETIN BIR ADIM OTESI] Tur 1 kalemleri (parametre dogrulama, `kapandi`/`yokluyor`/`ekran_dikdortgeni`, dirilme yok, kenar korunur, hideEvent temizligi, `calistirici`) + tur 2: ust sinirlar, `KenarSekmesi.kapandi` sekme gizliyken de yayilir ama kabuk yalniz kenar durumunda tepki verir, mandal `hideEvent`te sifirlanir, `showNormal` yalniz `isMinimized()` ise (maksimize/normal pencerede `show()`)."
  - "[PAKET ARAYUZU -- `y` ozelligi `QWidget.y()`yi golgeler] Tur 1 ile ayni; belgeli."
  - "[EVIDENCE] `-tur2` ekli dosyalar bu turun; `mutant-kiti.py` ve `mutant-ayirt-etme-hangi-testler.txt` guncellendi (tur-1 `mutant-ayirt-etme.txt` eski kodun kaydi olarak duruyor). Edit araci uc kaynak + uc test dosyasini CRLF'e cevirmisti; LF'e dondurulduler (`git ls-files --eol` crlf yok). `git add`/`commit` ATILMADI. Delillerde mutlak yol yok (`<depo>`, `<gecici dizin>`, `<python>`, `<kullanici>`); model/arac adi yok (tarandi)."
---

# T-012 tur 2 -- teslim ozeti

**Tur 1 ozeti:** `src/ui/` kabugu (saf geometri, `KenarSekmesi`, `AnaPencere`/`Tepsi`/`KabukDurumu`, `calistir`), 190 test, kapi v2 18/18 TEMIZ, mutant 30/30; [5c] kok nedeni (balon sekmeyi ortuyor) olculup balon kaldirilmisti. Tester-A **RET** (Y-A1: lambda baglantilari yuzunden sekme hic silinmiyor -> zombi), Tester-B **ONAY** (O-B1 dis `close()`, O-B3 balon kaldirilinca kullanici hicbir sey gormuyor). Sef paketi v3'e cekti; kapi v3 surukleme yukari.

**Tur 2:** paket v3 ▲▲ maddelerinin tamami uygulandi ve olculdu; Tester-A dusuk bulgularindan ucuz olanlar (D-A1, D-A3, D-A4, D-A5) yapildi. **216 test** (+26), kapsam %99.61, mypy modul + testler temiz, tam takim 2113 x2 temiz (bir kosumda T-011 sure testi), cp1254 216, **mutant 40/40** (+10 tur-2 mutanti, +2 kontrol), Tester-A sondasi TEMIZ, gercek platform omur olcumu TEMIZ. **Kapi KOSULMADI: oturum kilitli** (`real_check-tur2-KILIT.txt`) -- sef kilit acilinca sarici ile kosar.

## Tur 2 bulgu -> degisiklik -> olcu

| bulgu | degisiklik | olcu (test / mutant / delil) |
|---|---|---|
| **Y-A1** sekme hic silinmiyor (lambda `self`i tutar) | `kenar_sekmesi.py`: uc lambda -> bagli yontem (`_anlik_tiki/_bolge_tiki/_goster_tiki`); `availableGeometryChanged.connect` en sona (D-A4 ikincil); docstring K1 omur cumlesi olcen test adlariyla | `test_k1_omur_*` x6 (del+gc, deleteLater, tek basina, tepsi; `weakref` None + gorunur ust-duzey 0 + yoklayici durur), pozitif kontrol (lambda widget canli kalir), AST bekci; M29 (4 test), M29b partial (3 test); gercek windows platformu Win32 `IsWindow`=False (`olcum-tur2-omur-gercek-platform.txt`); Tester-A sondasi TEMIZ |
| **O-B1** dis `sekme.close()` -> durum ayrisir, tepsisizde zombi | `KenarSekmesi.kapandi` sinyali (`closeEvent`); `AnaPencere._sekme_kapandi` kenar durumunda `goster()` | `test_k1_sekme_dis_close_kenar_durumunda_gorunure_doner[tepsi_var|tepsi_yok]`, `..._gorunur_ve_tepsi_durumunda_durum_degismez`, `test_k1_kapandi_sinyali_close_ile_yayilir_hide_ile_yayilmaz`; M30, M30b |
| **O-A1** mod tiki sonrasi imlec diskteyse 120 ms sonra yeniden acilir | tek atimlik mandal `_cikis_bekleniyor` (`_mod_tiki` kurar, `_yokla` diskten cikinca siler, `hideEvent` sifirlar) | `test_k4_mod_tiki_sonrasi_imlec_diskte_kalsa_da_yeniden_acilmaz_ciktiktan_sonra_acilir[anlik|bolge]` (dugme ∩ disk kesisiminden nokta, on kosul assert; pozitif kontrol: cikis sonrasi acilir), `..._mandali_gizlenip_gosterilince_sifirlanir`; M31, M31b |
| **O-B3 / K5 ▲▲** balon yok -> ilk kullanimda hicbir sey gorunmuyor | `tepsiye_al()` surec basina bir kez `bildir("Suflör arka planda", ..., 2500)`; `_balon_gosterildi: ClassVar` | `test_k5_ilk_tepsiye_al_surec_basina_bir_kez_balon` (x3 -> 1, basi/metin/ms), `..._ikinci_ornek_de_gostermez` (ornek basina degil), `..._tepsi_yokken_..._tuketmez`; M26/M26b/M26c |
| D-A1 `goster()` kucultulmusu getirmez | `isMinimized()` ise `showNormal()` | `test_k1_goster_kucultulmus_pencereyi_geri_getirir`; M32 |
| D-A3/D-A4 `yaricap > 66` salinim; `>= 2**30` OverflowError | `1 <= yaricap <= 66`, ms `<= 2**31-1` -> `ValueError` on dogrulama | `test_k4_gecersiz_parametre_valueerror` (+6 dal), `test_k4_yaricap_ust_sinir_tam_degeri_kabul`; M33; kirmizi delildeki teardown error (yarim kurulu nesne) kayboldu |
| D-A5 `PANEL_BOYUTU` mutable | `Final` + docstring (Qt deger nesnesi dondurulamaz) + yapisal bekci | `test_k2_panel_boyutu_kaynakta_degistirilmez_ast` (pozitif kontrollu; eski kodda da yesil -- disiplin bekcisi) |
| Tester-B test kalitesi: `dugme_goster` panel kapaliyken | gercekci yol testi | `test_k1_panel_acikken_dugme_goster_pencereyi_getirir` |

## On olcumler (karardan once, `olcum_omur_on` -- scratch, ozeti burada)

`.emit` baglantilari (`timeout.connect(self.a.emit)`, `a.connect(self.b.emit)`), bagli yontem, uzun omurlu `QScreen` gondericisine bagli yontem: uc sinif da sarmalayiciyi TUTMAZ (toplandi=True); `Tepsi` + `QMenu` zaten toplaniyor; eski `KenarSekmesi` toplanmiyor (lambda). `showMinimized` offscreen'de `isMinimized=True`; eski `goster()` sonrasi True kaliyor (D-A1 uretildi), `showNormal` False. `yaricap=67` kabul, `2**30-1` kabul (Qt 16777215'e kirpar), `2**30` OverflowError, ms `2**31` OverflowError.

## Sayilar

| olcu | tur 1 | tur 2 |
|---|---|---|
| birim | 190 | **216** (+26); kapsam %99.61 (517 ifade; eksik 2 ayni) |
| mypy | modul 6 + test 4 temiz | ayni |
| kapi | v2 18/18 TEMIZ | **kosulmadi (kilit)**; kilitten bagimsiz gercek-platform omur olcumu TEMIZ 4/4 |
| tam takim | 2087 x2 | 2113 (kosum 1, 3); kosum 2: T-011 sure testi 60.8 ms |
| mutant | 30/30, 3 kontrol | **40/40, 5 kontrol** |
| cp1254 | 190 | 216 |
| TDD kirmizi | 2 | +1 (19 failed + 1 error / 12 passed, eski kodda) |
