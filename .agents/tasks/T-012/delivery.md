---
task: T-012
role: implementer
round: 3
status: tamamlandi
files_written:
  - src/ui/kabuk.py
  - src/ui/kenar_sekmesi.py
  - tests/unit/ui/test_kabuk.py
  - tests/unit/ui/test_kenar_sekmesi.py
  - .agents/tasks/T-012/delivery.md
  - .agents/tasks/T-012/evidence/tdd-kirmizi-4-tur3-yeni-testler-eski-kodda.txt
  - .agents/tasks/T-012/evidence/mypy-tur3.txt
  - .agents/tasks/T-012/evidence/mypy-test-dosyalari-tur3.txt
  - .agents/tasks/T-012/evidence/pytest-tur3.txt
  - .agents/tasks/T-012/evidence/cov-tur3.txt
  - .agents/tasks/T-012/evidence/pytest-tum-tur3.txt
  - .agents/tasks/T-012/evidence/pytest-tum-tur3-kosum2.txt
  - .agents/tasks/T-012/evidence/pytest-cp1254-tur3.txt
  - .agents/tasks/T-012/evidence/real_check-tur3-KILIT.txt
  - .agents/tasks/T-012/evidence/mutant-kiti.py
  - .agents/tasks/T-012/evidence/mutant-ayirt-etme-tur3.txt
  - .agents/tasks/T-012/evidence/mutant-ayirt-etme-hangi-testler.txt
  - .agents/tasks/T-012/evidence/olcum-tur3-omur-ve-geometri-gercek-platform.py
  - .agents/tasks/T-012/evidence/olcum-tur3-omur-ve-geometri-gercek-platform.txt
  - .agents/tasks/T-012/evidence/tester-A-sonda-02-duzeltme-sonrasi-tur3.txt
  - .agents/tasks/T-012/evidence/tester-A-sonda-02b-duzeltme-sonrasi-tur3.txt
  - .agents/tasks/T-012/evidence/tester-A-sonda-01-regresyon-tur3.txt
  - .agents/tasks/T-012/evidence/tester-B-sonda-ob5-duzeltme-sonrasi-tur3.txt
commands:
  - cmd: "python -m mypy --strict --explicit-package-bases src/ui  (6 dosya, temiz)"
    exit_code: 0
    evidence: evidence/mypy-tur3.txt
  - cmd: "python -m pytest tests/unit/ui -q -p no:cacheprovider  (220 passed = 216 + 4 yeni; omur testinin deleteLater varyanti referans tutacak sekilde ayristirildi; sefin 2 bariyer testi dahil)"
    exit_code: 0
    evidence: evidence/pytest-tur3.txt
  - cmd: "python .agents/tasks/T-012/real_check.py  (KOSULMADI: oturum kilitli -- on plan LockApp.exe, LogonUI calisiyor; kapi [3]/[5] gercek fare + on plan ister; tur-3 degisiklikleri kapinin olctugu kalemleri degistirmez; kilitten bagimsiz gercek-platform olcumu ayri betikle yapildi)"
    exit_code: null
    evidence: evidence/real_check-tur3-KILIT.txt
  - cmd: "python -m pytest tests/unit/ui -q -p no:cacheprovider --cov=src.ui --cov-fail-under=95 --cov-report=term-missing  (521 ifade, %99.62; eksik 2: uygulama.py 36/40 gercek sys.argv/exec dallari, tur 1-2 ile ayni)"
    exit_code: 0
    evidence: evidence/cov-tur3.txt
  - cmd: "python -m pytest tests -q -p no:cacheprovider  (tam takim kosum 1: 2117 passed = 2113 + 4)"
    exit_code: 0
    evidence: evidence/pytest-tum-tur3.txt
  - cmd: "python -m pytest tests -q -p no:cacheprovider  (tam takim kosum 2: 2117 passed)"
    exit_code: 0
    evidence: evidence/pytest-tum-tur3-kosum2.txt
  - cmd: "python -m mypy --strict --explicit-package-bases tests/unit/ui/test_geometri.py tests/unit/ui/test_kenar_sekmesi.py tests/unit/ui/test_kabuk.py tests/unit/ui/test_uygulama.py ; python -m mypy --strict --explicit-package-bases src/ui tests/unit/ui  (4 test dosyasi temiz; 13 dosya birlikte temiz; `shiboken6.isValid` importu dahil)"
    exit_code: 0
    evidence: evidence/mypy-test-dosyalari-tur3.txt
  - cmd: "cmd /c cp1254.cmd  (chcp 1254, PYTHONIOENCODING/PYTHONUTF8 bos, sys.stdout.encoding=cp1254; python -m pytest tests/unit/ui -q: 220 passed)"
    exit_code: 0
    evidence: evidence/pytest-cp1254-tur3.txt
  - cmd: "python -m pytest tests/unit/ui -q -p no:cacheprovider -rfE --tb=line -k '<tur-3 testler>'  (TDD KIRMIZI 4: tur-3 testleri TUR-2 KODUNDA: 5 failed / 1 passed -- dusenler: omur[deleteLater_referans_tutulur] (zombi), O-A2 sekme close|closeAllWindows + kabuk yolu (200x132), balona tik; gecen: omur[del_gc] (beklenen, degismedi))"
    exit_code: 1
    evidence: evidence/tdd-kirmizi-4-tur3-yeni-testler-eski-kodda.txt
  - cmd: "python .agents/tasks/T-012/evidence/mutant-kiti.py  (ayna agaci; 44 davranis mutanti + 5 kontrol; tur 3: M34 destroyed->sekme.deleteLater yok, M34b Tepsi.destroyed->menu.deleteLater yok, M35 showEvent _konumlan yok, M36 messageClicked bagli degil)"
    exit_code: 0
    evidence: evidence/mutant-ayirt-etme-tur3.txt
  - cmd: "python .agents/tasks/T-012/tester_A/sonda_a_02_close_geometri_bayat.py ; python .agents/tasks/T-012/tester_A/sonda_a_02b_duzeltme_onerisi.py  (Tester-A O-A2 sondalari, dokunulmadan, QT_QPA_PLATFORM=offscreen, DUZELTME SONRASI: SONDA TEMIZ; 02b'de taban KenarSekmesi de 'ok')"
    exit_code: 0
    evidence: evidence/tester-A-sonda-02-duzeltme-sonrasi-tur3.txt
  - cmd: "python .agents/tasks/T-012/tester_B/olcum_ob5_zombi_ve_duzeltme.py ; python .agents/tasks/T-012/tester_B/olcum_ob5_duzeltme_uc_yol.py  (Tester-B O-B5 sondalari, dokunulmadan, offscreen, DUZELTME SONRASI: duzeltme=False satiri da temiz (urun baglantisi); uc yolda cokme yok -- sondanin kendi ek baglantisiyla cift deleteLater da guvenli)"
    exit_code: 0
    evidence: evidence/tester-B-sonda-ob5-duzeltme-sonrasi-tur3.txt
  - cmd: "python .agents/tasks/T-012/tester_A/sonda_a_01_omur_zombi.py  (Tester-A tur-1 omur sondasi, regresyon: SONDA TEMIZ)"
    exit_code: 0
    evidence: evidence/tester-A-sonda-01-regresyon-tur3.txt
  - cmd: "python .agents/tasks/T-012/evidence/olcum-tur3-omur-ve-geometri-gercek-platform.py  (GERCEK windows platformu, kilitten/fareden bagimsiz: deleteLater+referans -> sekme hwnd IsWindow=False, C++ sekme/menu gecersiz, gorunur 0, yoklayici durdu; panel acikken close -> kenara_al GetWindowRect 33x65 == ilk kapali sekme (dpr 1.25), Qt 26x52, saydam kosede hover acmaz; closeAllWindows ayni; pozitif kontrol baglantisiz kalip hwnd yasar: TEMIZ 6/6)"
    exit_code: 0
    evidence: evidence/olcum-tur3-omur-ve-geometri-gercek-platform.txt
contract_change_request: false
known_gaps:
  - "[KAPI KOSULMADI -- OTURUM KILITLI] `real_check.py` v3 bu turda da KOSULMADI: on plan `LockApp.exe` (`Windows.UI.Core.CoreWindow`), `LogonUI.exe` calisiyor (`real_check-tur3-KILIT.txt`). Kapi [3]/[5] gercek fare + on plan ister. Tur-3 degisiklikleri kapinin olctugu kalemleri DEGISTIRMEZ: [2] kapali sekme geometrisi (`showEvent -> _konumlan()` ayni degeri uygular), [6] WM_CLOSE (kabuk `closeEvent` degismedi), [7] paint (`paintEvent` degismedi), [9] mod tiki (mandal degismedi). Kilitten bagimsiz gercek-platform olcumu (Win32 `IsWindow`/`GetWindowRect`) `olcum-tur3-omur-ve-geometri-gercek-platform.txt` ile yapildi (TEMIZ). Kilit acilinca sef sariciyla kosar; Tester-A'nin onerdigi [5d] (panel acikken WM_CLOSE -> yeniden kenara al -> `GetWindowRect` r x 2r) kapi kalemi sefe."
  - "[O-B5 / D-A9 -- OLCULDU, DUZELTILDI] `AnaPencere.deleteLater()` + tutulan Python referansi -> C++ `AnaPencere` (tepsi+ikon ile) oluyor, `_sekme` sarmalayicisi `__dict__`te yasiyordu: ZOMBI yarim daire (gorunur, yokluyor, hover panel acar, sag tik alicisiz, tepsi ikonu yok) + ebeveynsiz `QMenu` ust-duzeyde. Duzeltme: `AnaPencere.__init__` sonunda `self.destroyed.connect(self._sekme.deleteLater)`; `Tepsi.__init__`te `self.destroyed.connect(self._menu.deleteLater)` (alici sekme/menu: bagli yontem, `self` yakalanmaz; AST lambda bekcisi yesil). OLCU DUZELTMESI (paket lafzi 'weakref None' derdi): referans tutulurken sarmalayici `__dict__`te durdugu icin `weakref(sekme)()` None OLMAZ; ayrisan olcu `shiboken6.isValid(sekme) is False` + gorunur ust-duzey 0 + `QMenu` ust-duzeyde yok + yoklayici sayaci artmaz; referans birakilinca weakref'ler None (on olcum; test yardimcisi `_cpp_olu`). Tur-2 `[deleteLater]` varyanti `del p` de yaptigi icin ayrismiyordu -> `[deleteLater_referans_tutulur]` olarak AYRISTIRILDI (kirmizi delilde duser, `del_gc` gecer). Mutant M34 (1 test: bu varyant -- tur-2 halinde HICBIR test yakalamazdi), M34b (1 test). Uc yol (`del`+gc / `deleteLater`+`del` / `kapat()`+`del`) cift silme/cokme yok (Tester-B sondasi + kit). Tutulan sarmalayicida `goster()/kapat()` C++ oldukten sonra `RuntimeError` (silinmis QObject; PySide standardi) -- kotu kullanim, docstring, `[ÖLÇÜLMÜYOR]`."
  - "[O-A2 -- OLCULDU, DUZELTILDI] Panel ACIKKEN `sekme.close()` / `closeAllWindows()` -> yeniden gosterilen kapali sekme 200x132 kaliyordu. ON OLCUM (mekanizma, Tester-A'nin okumasindan farkli): `hideEvent -> _kapat() -> setGeometry(26x52)` UYGULANIYOR (close hemen sonrasi 26x52) ama close SONRASI olay dongusunde islenen gecikmis geometri olayi widget'i 200x132'ye geri yaziyor (`processEvents`/`dongu(0)`/`dongu(50)` uc bekleme de bayatlatir; beklemesiz `close(); show()` bayatlatmaz). Urunde kullanicinin sonraki eylemi her zaman en az bir tur sonradir -> testler `close` ile `show` arasina `qtbot.wait(20)` koyar (ilk kirmizi denemede beklemesiz testler eski kodda GECMISTI; delil dosyasi son halidir). Duzeltme: `KenarSekmesi.showEvent` basinda `self._konumlan()` (Tester-A 02b ile dogrulanan tek satir). Olcu: `test_k2_panel_acikken_close_sonrasi_yeniden_gosterilince_kapali_geometri[close|closeAllWindows]` (frameGeometry == ilk kapali dikdortgen; saydam kosede `acilma+3*yoklama` sonra `acik False`; pozitif kontrol diskte acilir), `test_k1_sekme_dis_close_panel_acikken_kenara_al_kapali_geometri_taze` (kabuk yolu, urun sayaclari); gercek platform Win32 `GetWindowRect` 33x65 == ilk kapali (dpr 1.25). Mutant M35 (3 test). Tester-A sondasi 02 TEMIZ, 02b'de taban sinif 'ok'."
  - "[D-B12 -- YAPILDI] `Tepsi`: `QSystemTrayIcon.messageClicked -> goster_istendi.emit` (1 satir): 'Tepsi ikonuna tıklayınca pencere geri gelir.' balonuna tik da pencereyi getirir. `test_k5_balona_tik_pencereyi_getirir` (tepsi durumundan `messageClicked.emit()` -> `goster_istendi` 1, (T,F,F)); balon baska surecin penceresi, gercek tik `[ÖLÇÜLMÜYOR]`. Mutant M36 (1 test). Dar tura eklendi cunku K5 ▲▲ balonunun yarim kalan parcasi ve durum makinesine dokunmuyor."
  - "[TESTER DUSUKLERI -- KARARLAR] D-A9: O-B5 ile kapandi (yukarida). D-A10 (`kapandi` dinleyicisi ayni cagri icinde `kenara_al()` -> (F,F,T) + durum kenar): YAPILMADI -- yeniden giris; Qt close akisi closeEvent SONRASI gizler, dinleyici sekmeyi bir sonraki olay dongusu turunda gostermeli; `goster()` toparlar; docstring K1 DIS KAPATMA'ya yazildi, `[ÖLÇÜLMÜYOR]`. D-A11 (dis `sekme.deleteLater()` kabugu kirar): YAPILMADI -- paketin yolu `close()`; `_sekme.destroyed` dinleyip toparlamak her `_sekme` erisimini korumayi gerektirir (ucuz degil, kabuk arayuzu bulanir); docstring + `known_gaps`, `[ÖLÇÜLMÜYOR]`. D-B10/D-B11: sefin demo dosyalari (sahiplik disi), dokunulmadi. D-B13 (`PANEL_BOYUTU` AST bekcisi `import as` takma adini gormez): disiplin bekcisi, urun etkisi yok, YAPILMADI. D-B14 (`close()` platform penceresini yikar, hwnd degisir): docstring K1 DIS KAPATMA'ya yazildi. D-B15 (`app.quit()` kenar durumunda temiz kapanis): tur 2'de belgelenmisti, degismedi. D-B1/D-B8: tur 1, degismedi."
  - "[T-011 SURE TITREMESI -- T-012 DISI] Tam takim iki kosumda da 2117/2117 (T-011 sure testleri bu turda titremedi; tur 1-2 kaydi ve sef karari T-011 bakim kalemi olarak durur). Not: kosum 1 mutant kiti ile es zamanli kosuldu (32 cekirdek), yine temiz."
  - "[TDD KIRMIZI 4] 5 tur-3 testi tur-2 kodunda dusuyor: `omur[deleteLater_referans_tutulur]` (sekme C++ yasiyor), O-A2 x3 (bayat 200x132), `balona_tik` (sinyal yok); `omur[del_gc]` geciyor (degismedi, beklenen). Ilk deneme: O-A2 testleri `close(); show()` beklemesiz yazilinca eski kodda GECTI (bulguyu uretemedi) -> on olcumle mekanizma bulundu (gecikmis olay), testlere bir olay dongusu turu eklendi; delil dosyasi ikinci (son) kosumdur."
  - "[ÖLÇÜLMÜYOR -- shell ust bandi] Tur 2 ile ayni: baska uygulamalarin balonlari, Baslat, bildirim merkezi sekmenin USTUNDEDIR; kabugun kendi balonu surec basina bir kez."
  - "[ÖLÇÜLMÜYOR -- topmost/exclusive oyun] Sekmeden SONRA gosterilen topmost oyun ustte kalir (KRT k5 Z2); `_ac()` `raise_()`; olcusu yok."
  - "[ÖLÇÜLMÜYOR -- yatay / monitorler arasi tasima] Yalniz dikey `y`; v2 (T-003 gerekir)."
  - "[ÖLÇÜLMÜYOR -- global kisayollar] `Ctrl+Alt+T/R` paket disi; HotkeyService ayri gorev."
  - "[ÖLÇÜLMÜYOR -- monitor cikarma] `screenRemoved` bagli degil; verilen `QScreen` silinirse `RuntimeError`. `availableGeometryChanged` bagli (sahte sinyalle olculdu)."
  - "[ÖLÇÜLMÜYOR -- gorev cubugu sagda/solda] `ekran = availableGeometry()`; cubuk sagda iken sekme fiziksel kenara bitisik degil (KRT G3)."
  - "[ÖLÇÜLMÜYOR -- bildirim kapali] `Tepsi.bildir` bildirimler kapaliyken sessizce yok olur; K5 balonu da; `messageClicked` de gelmez."
  - "[ÖLÇÜLMÜYOR birim -- DPI fiziksel yuvarlama] Mantiksal pikselde dogru; gercek platform olcumu dpr 1.25'te 26x52 -> 33x65 (yuvarlama ust), `real_check` [8] tur 1'de +1 px (kabul +-1); bu turda kapi kosulmadi."
  - "[ÖLÇÜLMÜYOR -- activeWindow offscreen] K3 yapisal test; gercek davranis `real_check` [3] (bu turda kilit)."
  - "[ÖLÇÜLMÜYOR -- ornekleme fazi / bosta CPU] Tur 1 ile ayni (<= 1 yoklama; %0.3 KRT k4b)."
  - "[PAKETIN BIR ADIM OTESI] Tur 1-2 kalemleri + tur 3: `showEvent` her gosterimde geometriyi durumdan uygular (yalniz close sonrasi degil: `y`/`kenar` gizliyken degistirilse de tutarli), `Tepsi.destroyed -> menu.deleteLater`, `messageClicked -> goster_istendi`."
  - "[PAKET ARAYUZU -- `y` ozelligi `QWidget.y()`yi golgeler] Tur 1 ile ayni; belgeli."
  - "[EVIDENCE] `-tur3` ekli dosyalar bu turun; `mutant-kiti.py` ve `mutant-ayirt-etme-hangi-testler.txt` guncellendi (tur-1/2 `mutant-ayirt-etme*.txt` eski kodun kaydi olarak duruyor). LF korundu (`git ls-files --eol` crlf yok). `git add`/`commit` ATILMADI. Delillerde mutlak yol yok (`<depo>`, `<gecici dizin>`, `<python>`); model/arac adi yok (tarandi). Tester dizinlerine, `conftest.py`ye, `real_check.py`ye, `demo/`ya dokunulmadi (sondalar yalniz KOSULDU)."
---

# T-012 tur 3 (dar) -- teslim ozeti

**Tur 1 ozeti:** `src/ui/` kabugu (saf geometri, `KenarSekmesi`, `AnaPencere`/`Tepsi`/`KabukDurumu`, `calistir`), 190 test, kapi v2 18/18 TEMIZ, mutant 30/30. Tester-A **RET** (Y-A1: lambda baglantilari yuzunden sekme hic silinmiyor -> zombi), Tester-B **ONAY** (O-B1 dis `close()`, O-B3 balon). Sef paketi v3'e cekti.

**Tur 2 ozeti:** paket v3 ▲▲ maddeleri (omur, `kapandi`, mandal, balon) + Tester-A dusukleri (D-A1/A3/A4/A5): 216 test, kapsam %99.61, mutant 40/40, tam takim 2113, gercek-platform omur olcumu TEMIZ; kapi kilit yuzunden kosulmadi. Iki tester **ONAY**, iki orta bulgu (sef ikisini de uretti): **O-B5/D-A9** (`deleteLater` + tutulan referans -> zombi sekme) ve **O-A2** (panel acikken dis `close()` -> kapali sekme 200x132).

**Tur 3 (dar):** iki orta bulgu + D-B12 duzeltildi; her biri icin ayristiran test (TDD kirmizi delili: eski kodda 5 failed / 1 passed) ve mutant (M34/M34b/M35/M36). **220 test** (+4; omur testinin `deleteLater` varyanti referans tutacak sekilde AYRISTIRILDI), kapsam %99.62, mypy modul + testler temiz, cp1254 220, **mutant 44/44** (+4, 5 kontrol kacti), tester sondalari (A-01, A-02, A-02b, B-ob5 x2) dokunulmadan **TEMIZ**, gercek windows platformu Win32 olcumu **TEMIZ 6/6**. **Kapi KOSULMADI: oturum kilitli** (`real_check-tur3-KILIT.txt`).

## Tur 3 bulgu -> degisiklik -> olcu

| bulgu | degisiklik | olcu (test / mutant / delil) |
|---|---|---|
| **O-B5 / D-A9** `deleteLater()` + tutulan referans -> C++ `AnaPencere` olu, `_sekme` sarmalayicisi yasiyor: zombi yarim daire; ebeveynsiz `QMenu` ust-duzeyde | `kabuk.py`: `AnaPencere.__init__` sonu `self.destroyed.connect(self._sekme.deleteLater)`; `Tepsi.__init__` `self.destroyed.connect(self._menu.deleteLater)` (bagli yontemler; AST lambda bekcisi yesil) | `test_k1_omur_kenar_durumunda_ana_pencere_dusunce_sekme_silinir[deleteLater_referans_tutulur]` (`del p` YOK; `isValid` False, gorunur 0, `QMenu` yok, yoklayici durdu; sonra `del` -> weakref None); M34 (1), M34b (1); Tester-B sondalari TEMIZ (uc yol cokme yok); gercek platform Win32 `IsWindow`=False |
| **O-A2** panel acikken `close()`/`closeAllWindows()` -> yeniden gosterilen kapali sekme 200x132 (saydam alanda hover panel acar) | `kenar_sekmesi.py`: `showEvent` basinda `self._konumlan()` | `test_k2_panel_acikken_close_sonrasi_yeniden_gosterilince_kapali_geometri[close|closeAllWindows]`, `test_k1_sekme_dis_close_panel_acikken_kenara_al_kapali_geometri_taze` (kabuk yolu; frameGeometry == ilk kapali; saydam kosede acmaz; pozitif kontrol diskte acilir); M35 (3); Tester-A sonda 02 TEMIZ, 02b taban 'ok'; gercek platform `GetWindowRect` 33x65 == ilk kapali |
| **D-B12** balona tik hicbir seye bagli degil | `Tepsi`: `messageClicked -> goster_istendi.emit` | `test_k5_balona_tik_pencereyi_getirir`; M36 (1) |

## On olcumler (karardan once)

- **O-B5 olcu duzeltmesi:** referans tutulurken `weakref(sekme)()` None OLMAZ (sarmalayici `p.__dict__`te), `shiboken6.isValid` False olur; referans birakilinca None. Duzeltmesiz kodda ust-duzey listesi `['QMenu', 'KenarSekmesi']`, gorunur `['KenarSekmesi']`, yoklayici okuyor; duzeltmeyle ikisi de bos, okumuyor. `p.goster()/p.kapat()` C++ oldukten sonra her iki durumda `RuntimeError` (kotu kullanim, belge).
- **O-A2 mekanizma:** `close()` hemen sonrasi widget 26x52 (hideEvent'in `setGeometry`si uygulandi); bir olay dongusu turu sonra 200x132 (gecikmis geometri olayi geri yaziyor); beklemesiz `close(); show()` 26x52 kalir. Testlere `qtbot.wait(20)` eklendi (ilk kirmizi denemesi bu yuzden eski kodda gecmisti).

## Sayilar

| olcu | tur 1 | tur 2 | tur 3 |
|---|---|---|---|
| birim | 190 | 216 | **220** (+4; 1 varyant ayristirildi); kapsam %99.62 (521 ifade; eksik 2 ayni) |
| mypy | modul 6 + test 4 temiz | ayni | ayni (+ 13 dosya birlikte) |
| kapi | v2 18/18 TEMIZ | kosulmadi (kilit) | **kosulmadi (kilit)**; gercek platform Win32 olcumu TEMIZ 6/6 |
| tam takim | 2087 x2 | 2113 (x2; bir kosumda T-011 sure) | **2117 x2** (temiz; T-011 sure testleri bu kez titremedi) |
| mutant | 30/30, 3 kontrol | 40/40, 5 kontrol | **44/44, 5 kontrol** |
| cp1254 | 190 | 216 | 220 |
| TDD kirmizi | 2 | +1 | +1 (5 failed / 1 passed eski kodda) |
| tester sondalari | -- | A-01 TEMIZ | A-01, A-02, A-02b, B-ob5 x2 **TEMIZ** |
