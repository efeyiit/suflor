---
task: T-012
role: tester
round: 2
decision: onay
checks:
  - name: "taban 1 -- mypy --strict src/ui temiz (8 dosya, conftest + bariyer dahil)"
    cmd: "python -m mypy --strict --explicit-package-bases src/ui tests/unit/ui/conftest.py tests/unit/ui/test_conftest_bariyer.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/tur2-taban-1-mypy.txt
  - name: "taban 1b -- mypy --strict src/ui + tests/unit/ui temiz (13 dosya; testler bittikten sonra kosuldu, korluk)"
    cmd: "python -m mypy --strict --explicit-package-bases src/ui tests/unit/ui"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/tur2-taban-1b-mypy-src-ui-ve-testler.txt
  - name: "taban 2 -- implementer birim testleri 216 passed"
    cmd: "python -m pytest tests/unit/ui -q -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/tur2-taban-2-pytest-ui.txt
  - name: "taban 3 -- real_check v3 KOSULMADI: oturum kilitli (LogonUI pid 13444/66928); sef kilit acilinca kosar"
    cmd: "Get-Process LogonUI  (python .agents/tasks/T-012/real_check.py kilit yuzunden kosulmadi)"
    exit_code: -1
    result: kosulmadi
    evidence: tester_A_evidence/tur2-taban-3-real_check-kilitli.txt
  - name: "taban 4 -- kapsam %99.61 (517 ifade, 2 eksik: uygulama.py 36, 40 = gercek argv/exec dallari)"
    cmd: "python -m pytest tests/unit/ui -q -p no:cacheprovider --cov=src.ui --cov-fail-under=95 --cov-report=term-missing"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/tur2-taban-4-kapsam.txt
  - name: "taban 5 -- tam takim 2113 passed (tur 1'de dusen T-011 sure testi bu kosumda gecti)"
    cmd: "python -m pytest tests -q -p no:cacheprovider -rfE --no-header"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/tur2-taban-5-tum-takim.txt
  - name: "A1 -- tur-1 testleri DEGISTIRILMEDEN v3'e karsi: 233 passed / 6 failed; 3 Y-A1 DOCSTRING testi yesile dondu; dusen 6 = 5 duzeltilen bulgu (Y-A1 gizli sizinti, O-A1, D-A1, D-A3, D-A4) + 1 yeni ust sinir (yaricap=ekran yuksekligi -> ValueError); beklenen sinif, kod hatasi degil"
    cmd: "python -m pytest .agents/tasks/T-012/tester_A -q -p no:cacheprovider --import-mode=importlib -rfE --no-header  (test_mercek_a.py tur-1 hali)"
    exit_code: 1
    result: kaldi
    evidence: tester_A_evidence/tur2-A1-tur1-testleri-v3-karsi-degistirilmemis.txt
  - name: "A2 -- 6 pin `_v3` olarak ters cevrildi + yeni tur-2 dosyasi (139 test): tester_A dizini 378 passed (-v)"
    cmd: "python -m pytest .agents/tasks/T-012/tester_A -p no:cacheprovider --import-mode=importlib -v -rfE --no-header"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/tur2-A-mercek-testleri-v.txt
  - name: "A3 -- kararlilik: ayni 378 test x3, ucunde de 378 passed (zaman/omur testleri titremedi)"
    cmd: "python -m pytest .agents/tasks/T-012/tester_A -q -p no:cacheprovider --import-mode=importlib -rfE --no-header (x3)"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/tur2-A-mercek-kararlilik-x3.txt
  - name: "A4 -- implementer 216 + mercek-A 378 ayni oturumda: 594 passed (balon sinif sayaci dahil etkilesim yok)"
    cmd: "python -m pytest tests/unit/ui .agents/tasks/T-012/tester_A -q -p no:cacheprovider --import-mode=importlib -rfE --no-header"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/tur2-A-birlikte-kosum.txt
  - name: "sonda A-01 (tur 1, Y-A1) v3'e karsi: TEMIZ -- del+gc, deleteLater, tek basina sekme, kapat()+dusurme hepsi toplaniyor; pozitif kontrol ayrisiyor"
    cmd: "python .agents/tasks/T-012/tester_A/sonda_a_01_omur_zombi.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/tur2-A-sonda-01-omur-zombi-v3.txt
  - name: "sonda A-02 (O-A2, offscreen): panel ACIKKEN sekme.close()/closeAllWindows() -> kapali sekme yeniden gosterilince 200x132; saydam alanda hover panel acar -> 3 IHLAL; hide() ve dogrudan QCloseEvent yollari 26x52 (pozitif kontrol)"
    cmd: "python .agents/tasks/T-012/tester_A/sonda_a_02_close_geometri_bayat.py"
    exit_code: 1
    result: kaldi
    evidence: tester_A_evidence/tur2-A-sonda-02-close-geometri-bayat-offscreen.txt
  - name: "sonda A-02 GERCEK windows platformunda (kilitliyken yalniz geometri, girdi yok): birebir ayni 3 IHLAL (x=2022, 2048 px ekran) -> offscreen'e ozgu degil, Qt6 QWindow::close akisi"
    cmd: "python .agents/tasks/T-012/tester_A/sonda_a_02_close_geometri_bayat.py windows"
    exit_code: 1
    result: kaldi
    evidence: tester_A_evidence/tur2-A-sonda-02-close-geometri-bayat-windows-platform-kilitli.txt
  - name: "sonda A-02b -- duzeltme onerisi alt sinifla dogrulandi (src/ui degismedi): showEvent -> _konumlan() iki platformda 26x52; hide sonrasi 0 ms ertelemeli yeniden uygulama ISE YARAMAZ"
    cmd: "python .agents/tasks/T-012/tester_A/sonda_a_02b_duzeltme_onerisi.py [offscreen|windows]"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/tur2-A-sonda-02b-duzeltme-onerisi-dogrulama.txt
  - name: "depo dokunulmadi: git diff HEAD --stat -- src tests demo real_check packet evidence BOS; HEAD f94e012; sha256 src/ui (kabuk 5c0e30cb..., kenar_sekmesi 7fda6b4a..., geometri c7af01a7...), real_check 335e3501..., conftest d8bc361b...; tester_B/** baska oturumda degisiyor, OKUNMADI"
    cmd: "git status --short; git diff HEAD --stat -- src tests demo ...; sha256sum src/ui/*.py ..."
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/tur2-A-git-status-depo-dokunulmadi.txt
  - name: "korluk kaydi: implementer test ADLARI (127) mercek testleri bittikten SONRA yalniz kapsam boslugu icin grep'lendi; govde acilmadi; delivery.md / evidence/ / sef_dogrulama/ / tester_B* okunmadi"
    cmd: "grep -n '^def test_' tests/unit/ui/test_*.py | sed 's/(.*//'"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/tur2-A-implementer-test-adlari.txt
blocking_issues: []
---

# T-012 tur 2 -- Tester-A (mercek: durum makinesi + sinir + omur)

Karar: **ONAY**. Tur-1 ret nedeni **Y-A1 kapandi**: sekme artik her yoldan (del+gc, deleteLater, close()+dusurme, kapat()+dusurme; 5 durum x 4 yol = 20 hucre) toplaniyor, tepsi + menu + ikon + panel + dugmeler dahil; 10 kurulum/dusurme dongusu sonra `topLevelWidgets` tur listesi ve `allWidgets` sayisi taban degere donuyor; yoklayici duruyor (enjekte sayac artmiyor); tur-1 sondasi TEMIZ. O-A1 (mandal), D-A1 (showNormal), D-A3/D-A4 (ust sinirlar) de olculerek kapandi. Yeni ▲▲ eklerinin ucu de (omur, `kapandi`, balon) docstring'le tutuyor. **Bir yeni orta bulgu (O-A2)**: `kapandi` yolunun panel ACIKKEN kosulmasi kapali sekmeyi 200x132 birakiyor -- tek satirlik duzeltme onerisi alt sinifla iki platformda dogrulandi; bloklamiyor (gecici, kendini toparlar, urun yolu oturum kapanisinda zaten cikiyor) ama implementer'a gitmeli. Kapi (gercek ekran) kilit yuzunden kosulmadi; sonda-02 gercek `windows` platformunda yalniz geometriyle kosuldu, ayni sonuc.

Sayilar: tur-1 dosyasi v3'e karsi 233/6 (6'si beklenen sinif) -> 6 pin `_v3` ters cevrildi; yeni tur-2 dosyasi **139 test**; toplam **378 passed**, x3 kararli, implementer'la birlikte 594 passed. Taban: mypy 0 (src/ui + tests/unit/ui), 216 passed, kapsam %99.61, tam takim **2113 passed**.

Korluk: `delivery.md`, `evidence/**` (sarici haric), `sef_dogrulama/**`, `tester_B*` okunmadi; implementer testleri yalniz ad duzeyinde ve testlerim bittikten sonra. Ad duzeyinde gorunmeyen siniflar: close/closeAllWindows panel acikken (O-A2), closeAllWindows durum tablosu, deleteLater + tutulan sarmalayici, `kapandi` dinleyici yeniden girisi, mandal + surukleme / kenar degisimi, N dongu sizinti sayimi, ekran sinyali dusurme sonrasi, `imlec_konumu` closure dongusu, `partial` pozitif kontrolu, balon casusunda uclu/ikon gorunurlugu, iki ornekli rastgele yuruyus, ayri surec crash senaryolari.

Dosyalar: `tester_A/test_mercek_a.py` (tur 1, 239; 6'si `_v3`), `tester_A/test_mercek_a_tur2.py` (139, 7 bolum A-G), `tester_A/sonda_a_01_omur_zombi.py` (v3'te TEMIZ), `tester_A/sonda_a_02_close_geometri_bayat.py` (O-A2, `[offscreen|windows]`), `tester_A/sonda_a_02b_duzeltme_onerisi.py`.

## Tur-1 bulgularinin kapanisi (yeniden nisanlanan testler)

| Tur 1 | v3 olcumu | Test |
|---|---|---|
| Y-A1 zombi sekme | del+gc / deleteLater / close+del / kapat+del x 5 durum: sekme, tepsi, menu, ikon, panel, dugme weakref'leri None; gorunur ust-duzey doner; yoklayici durur | `test_a_omur_ana_pencere_dusunce_sekme_tepsi_menu_silinir` (20), `test_d_omur_*_DOCSTRING` (3, degismeden yesil), `..._kapat_sonrasi_dusurulen_ana_pencere_sekme_silinir_v3`, sonda-01 TEMIZ |
| O-A1 yeniden acilma | uc dugme x hizli/urun sayaclar: diskte kalinca kapali, cikip girince acilir; disk disinda tik hemen sifirlanir; tek yoklama disari yeter (saydam kose de) | `test_d_mandal_*` (13), `..._panel_yeniden_acilmaz_v3` |
| D-A1 kucultulmus | tepsi ve kenar uzerinden `goster()` -> `isMinimized` False | `..._goster_normale_doner_v3` |
| D-A3 yaricap > 66 | 67 -> ValueError; 66 disk kosesinde 0 salinim; 66'da panel her y'de sekmeyi kapsar (3 ekran x 2 kenar), 67'de kapsamaz | `..._ust_sinir_salinim_yok_v3`, `test_f_ust_sinir_66_panel_her_y_de_sekmeyi_kapsar` |
| D-A4 OverflowError | 19 sinir noktasi (66/67, 2**31-1 / 2**31, 0/-1, 10**12): tam sinir kabul, otesi ValueError, hicbir Qt nesnesi yaratilmadan (`topLevelWidgets` + `allWidgets` sabit); ayri surecte ekran sinyali sonrasi stderr bos | `test_f_ust_sinir_tam_sinir_kabul_otesi_valueerror_qt_nesnesi_yok` (19), `..._valueerror_ayri_surec_v3` |
| D-A5 PANEL_BOYUTU | AST bekci (set*/scale/aug/yeniden atama yok, pozitif kontrollu) + akis sonrasi (200,132); mutable kaldi (docstring 'tanimsiz' der, kabul) | `test_f_panel_boyutu_*` |

## ORTA

**O-A2 · Panel ACIKKEN `sekme.close()` / `QApplication.closeAllWindows()` -> kapali sekme 200x132 kalir (K2/K3/K4 ihlali, gecici).** Qt6'da `QWidget::close()` ust-duzeyde `QWindow::close()` akisindan gecer; bu akis icinde kabugun `goster()` -> `sekme.hide()` -> `hideEvent` -> `_kapat()` -> `setGeometry(26x52)` cagrisi widget `crect`'ini gunceller ama pencere geometrisi 200x132'de kalir (konum kapali sekmeninki, boyut panelinki: `(2022,526,200,132)`); `kenara_al()` ile yeniden gosterilen KAPALI sekme 200x132 penceredir: `sekme_icinde` boyuta bakip 'panel' sanir ve duz `contains` yapar -> saydam alanda hover panel acar (urun sayaclariyla olculdu), o alandaki tik oyuna gitmez (gercek ekranda sag kenarda 26x132'lik serit; kalan kisim ekran disi). Bir acilip kapanma ya da `y`/`kenar` atamasi kendini toparlar. Pozitif kontrol: `hide()` yolu (kabugun kendi yolu) ve panel kapaliyken `close()` 26x52; dogrudan `QCloseEvent` `sendEvent` de 26x52 (Qt close akisina girmez). **Offscreen ve gercek `windows` platformunda birebir** (sonda-02). Docstring K1 DIS KAPATMA "panel kapanir" der -- `acik` False olur ama geometri uygulanmaz; K2 "kapali dikdortgen r x 2r", K3 olcusu "kapali/acik frameGeometry (yaricap, 2*yaricap)" ihlal. Tetikleyici: dis `close()`/oturum kapanisi TAM imlec sekmedeyken; urun yolunda (`closeAllWindows` -> `cikis_istendi` -> quit) etkisi yok, `sekme.close()` cagiran sonraki ajan (demo secim katmani vb.) icin var. **Duzeltme (dogrulandi, sonda-02b):** `KenarSekmesi.showEvent` icinde `super().showEvent(e)` oncesi/sonrasi `self._konumlan()` -- her iki platformda 26x52. `hideEvent` sonrasi 0 ms ertelemeli yeniden uygulama ISE YARAMAZ (crect zaten 26x52 gorundugu icin `setGeometry` erken doner, pencere 200x132 kalir). Pin: `test_b_kapandi_panel_acikken_close_sonrasi_kapali_sekme_200x132_kalir_PIN[close|close_all_windows]`.

## DUSUK

**D-A9 · `deleteLater` + Python sarmalayicisi TUTULURKEN sekme gorunur kalir; `kapat()`/`goster()` RuntimeError.** C++ `AnaPencere` silinir (tepsi/ikon/menu ile), `p._sekme` sarmalayicida yasar: sekme GORUNUR + yokluyor; sag tik `pencereyi_goster` yayar, kabugun yuvasi C++ aliciyla birlikte dusmustur (alici yok, istisna yok, donus yolu yok); `p.goster()` RuntimeError, `p.kapat()` `_kapandi=True` + sekmeyi gizledikten sonra `_tepsi.gizle()`de RuntimeError (yarim kapanis). Sarmalayici birakilinca toplanir (docstring cumlesi o kosulda dogru). Oneri: yapicida `self.destroyed.connect(self._sekme.hide)` (bagli yontem, sekme QObject) ya da docstring'e "sarmalayici birakilmali" notu. Pin: `test_a_omur_delete_later_sarmalayici_tutulurken_sekme_gorunur_kalir_ve_kapat_runtime_error_PIN`.

**D-A10 · `kapandi` dinleyicisi `kenara_al()` cagirirsa (F,F,T) + `durum` kenar (tablo disi).** Qt close akisi closeEvent'ten SONRA gizler: kabugun yuvasi once kosar (`goster()`), dis dinleyici sekmeyi yeniden gosterir, Qt hemen gizler -> tepsi uclusu, durum kenar, yoklayici durmus. Yeniden giris; `goster()` toparlar. Bilgi/pin: `test_b_kapandi_dinleyicisi_kenara_al_cagirirsa_tablo_disi_uclu_PIN`.

**D-A11 · Dis `sekme.deleteLater()` kabugu kirar (kotu kullanim).** `kapandi` yayilmaz (closeEvent yok), `durum` kenar, sekme yok, sonraki `goster()`/`kapat()` RuntimeError; `destroyed` dinlenmiyor. Paketin yolu `close()`dur (pozitif kontrol: ayni yerde `close()` -> (T,F,F)). Bilgi/pin: `test_b_sekme_dis_delete_later_kabugu_kirar_PIN`.

## Bilgi (olculdu, ihlal degil)

- **`closeAllWindows()` `[ÖLÇÜLMÜYOR]` -> OLCULDU** (5 durum + iki ornek + gercek `exec`): `gorunur`/`gorunur(tepsi yok)` -> `closeEvent` -> `kapat()` -> cikis 1, (F,F,F); `tepsi` -> gorunur pencere yok, HICBIR SEY olmaz ((F,F,T), cikis 0, `goster()` hala calisir); `kenar`/`kenar(tepsi yok)` -> sekme `kapandi` 1 -> `goster()` -> pencere gorunur olur -> Qt listeyi yeniler ve pencereyi de kapatir -> cikis **tam 1**, (F,F,F), `durum` GORUNUR; ikinci cagri sinyal uretmez; iki `AnaPencere` her biri 1; `calistir` + gercek `app.exec()` + kenar + `closeAllWindows` -> quit, 0 doner (oturum kapanisi `commitData` varsayilani bu yoldan gecer; tetikleyicinin kendisi `[ÖLÇÜLMÜYOR]`). K1 tablosuna 3 v3 eylemi (`sekme_close`, `sekme_close_event`, `close_all_windows`) x 5 satir eklendi; iki ornekli rastgele yuruyus (8 tohum x 40 eylem, v3 eylemleri dahil) tablo disi uclu yok, balon <= 1, sonunda ikisi de toplaniyor.
- **`kapandi` sirasi:** tek basina sekmede sinyal aninda sekme HALA gorunur ve yokluyor (Qt: closeEvent once, hide sonra); `AnaPencere`de kabugun yuvasi once koser -> dis dinleyici (T,F,F) gorur. Kabuk yollari (`goster/tepsiye_al/kenara_al/kapat`, dugmeler, menu, `hide/show/setVisible`) `kapandi` yaymaz; `close()` her durumda yayar (gizliyken de), `kapat()` sonrasi `close()` diriltmez; `close()` silmez (`kenara_al()` yeniden calisir, `kapandi` sayimi 2).
- **Mandal + surukleme (PIN):** mod tiki -> imlec diskte -> sol basili surukle -> birak: mandal SURER, panel acilmaz (K4 "birakilinca sayac sifirdan baslar" cumlesi mandala yenilir; mandalsiz ayni surukleme birakinca acar). Mandal `kenar` degisiminde imlec yeni disk disinda kaldigi icin duser; sag tik mandal koymaz; `acilma_ms=0`da da tutar; `AnaPencere` duzeyinde `dugme_goster` -> `goster()` gizler -> `kenara_al()` taze.
- **Balon (K5 ▲▲):** `showMessage` casusu: `tepsiye_al()` x3 -> 1 (`"Suflör arka planda"`, `NoIcon`, 2500); ikinci ornek gostermez, ilk ornek dusurulup yenisi kurulsa da 1 (SUREC basina, `_balon_gosterildi` sinif duzeyi); tepsisiz `tepsiye_al()` (kenara duser) sayaci tuketmez, sonraki tepsili ornek gosterir; kenar durumunda ve `kapat()` sonrasi `tepsiye_al()` gostermez ve tuketmez; menu "Kenara al" / tekrar tepsi ikinci balon uretmez; balon `hide()` + `durum=TEPSI` SONRASINDA, ikon GORUNURKEN cagrilir (casus icinde uclu (F,F,T)); `Tepsi.bildir` tepsisiz sessiz (pozitif kontrol).
- **Omur ek olculer:** `Tepsi` tek basina (ebeveynsiz) + ebeveynsiz `QMenu`'su + ikon toplanir; sekme dusurulunce `availableGeometryChanged` yayimi istisna uretmez (canliyken yeniden konumlar); `imlec_konumu` closure'u `AnaPencere`'yi yakalasa da (dongu) gc toplar; panel acikken / suruklerken / mandaldayken dusurme temiz; iki ornekte biri dusunce digeri saglam; `calistir` sonrasi dusurme temiz; pozitif kontrol 4 kalip: lambda ve `functools.partial` tutar (docstring cumlesi dogru), bagli yontem ve `sig.emit` tutmaz; yapisal bekci `.connect(lambda|partial)` 6 dosyada yok (pozitif kontrollu). Ayri surecte: `cikis_istendi` / `anlik_cevir_istendi` / `kapandi` dinleyicisi son referansi sinyal ICINDE dusurur -> cokme yok, sekme toplanir, gorunur ust-duzey 0 (gonderen yayim sirasinda silinir; Qt6 ref sayimli baglanti listesi).
- **Tip sozlesmesi disi (PIN):** `yaricap=True` (1x2) ve `yaricap=26.5` (26x53) yapicidan gecer -- mypy yakalar, belgeli sinir degil. `_YARICAP_AZAMI` import aninda turetilir, `PANEL_BOYUTU` sonradan degistirilirse izlemez (docstring 'tanimsiz').
- Tam takimda T-011 `test_k5_sure_8000_uyeli_zincir_60ms_alti` bu kez gecti (2113 passed); tur-1 D notu (yuk altinda 61-65 ms) T-011 bakim kalemi olarak durur.

## Tester yukumlulugu / oneri (sef icin, sirali)

1. **O-A2** `KenarSekmesi.showEvent` -> `self._konumlan()` (tek satir; sonda-02b iki platformda dogruladi); docstring K1 DIS KAPATMA cumlesine "gosterilirken geometri durumdan yeniden uygulanir" + olcen test adi; `real_check`e [5d] "panel acikken WM_CLOSE -> yeniden kenara al -> `GetWindowRect` 26x52" kalemi (gercek OS yolu, kilit acilinca).
2. **D-A9** `destroyed -> _sekme.hide` ya da docstring notu; **D-A11** `_sekme.destroyed` dinlenip `durum` toparlanabilir (ucuz) ya da `known_gaps`.
3. **D-A10** bilgi; istenirse `_sekme_kapandi` icinde `goster()` 0 ms ertelenerek dis dinleyicilerin yeniden gostermesi de gizlenmez -- gerekli degil.
4. Kapi kilit acilinca: `real_check` v3 + Tester-B gercek fare kalemleri + sonda-02 `windows` kosumu kilit acikken tekrar (girdiyle degismez ama kayit icin).
5. `tester_A/` sefin dizinine tasinabilir: closeAllWindows tablosu, N dongu sizinti sayimi, ayri surec crash senaryolari, balon casusu (uclu/ikon gorunurlugu) implementer adlarinda yok.
