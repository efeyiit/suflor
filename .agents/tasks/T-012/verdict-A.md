---
task: T-012
role: tester
round: 1
decision: ret
checks:
  - name: "taban 1 -- mypy --strict temiz (6 dosya); onceki oturum, src/ui degismedi (sha256 A-git-status ile ayni)"
    cmd: "python -m mypy --strict --explicit-package-bases src/ui"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/taban-1-mypy.txt
  - name: "taban 2 -- implementer birim testleri 190 passed (onceki oturum, gecerli)"
    cmd: "python -m pytest tests/unit/ui -q -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/taban-2-pytest-ui.txt
  - name: "taban 3 -- real_check v2 TEMIZ 18/18, on-plan sarici ile gercek ekran (onceki oturum, gecerli)"
    cmd: "python .agents/tasks/T-012/evidence/real_check-on-plan-sarici.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/taban-3-real_check.txt
  - name: "taban 4 -- kapsam %99.59 (487 ifade, 2 eksik: uygulama.py 36, 40)"
    cmd: "python -m pytest tests/unit/ui -q -p no:cacheprovider --cov=src.ui --cov-fail-under=95 --cov-report=term-missing"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/taban-4-kapsam.txt
  - name: "taban 5 -- tam takim 2086 passed / 1 failed: tests/unit/translate/test_sozluk.py::test_k5_sure_8000_uyeli_zincir_60ms_alti (61.5 ms > 60; T-011 sure testi, T-012 disi; tek basina 4/4 gecer)"
    cmd: "python -m pytest tests -q -p no:cacheprovider"
    exit_code: 1
    result: kaldi
    evidence: tester_A_evidence/taban-5-tum-takim.txt
  - name: "taban 5b -- tam takim tekrar: ayni tek test 65.4 ms > 60, 2086 passed (yuk altinda sure payi; src/ui ile ilgisi yok)"
    cmd: "python -m pytest tests -q -p no:cacheprovider"
    exit_code: 1
    result: kaldi
    evidence: tester_A_evidence/taban-5b-tum-takim-tekrar.txt
  - name: "taban 5c -- ayni translate sure testi tek basina 3/3 passed (0.47-0.67 s): tam takim yuku kaynakli titreme, T-011 yukumlulugu"
    cmd: "python -m pytest tests/unit/translate/test_sozluk.py::test_k5_sure_8000_uyeli_zincir_60ms_alti -q -p no:cacheprovider (x3)"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/taban-5c-translate-sure-testi-tek-basina.txt
  - name: "A mercek testleri -- 239 test: 236 passed / 3 FAILED (ucu de Y-A1 DOCSTRING olcumu: sekme silinmiyor); ayrintili -v cikti"
    cmd: "python -m pytest .agents/tasks/T-012/tester_A -p no:cacheprovider --import-mode=importlib -v -rfE --no-header -s"
    exit_code: 1
    result: kaldi
    evidence: tester_A_evidence/A-mercek-testleri.txt
  - name: "A kararlilik -- ayni takim 2 tekrar daha: ikisinde de ayni 3 failed / 236 passed (zaman testleri titremedi)"
    cmd: "python -m pytest .agents/tasks/T-012/tester_A -q -p no:cacheprovider --import-mode=importlib -rfE --no-header (x2)"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/A-mercek-kararlilik-2-3.txt
  - name: "A birlikte kosum -- implementer 190 + mercek-A 239 ayni oturumda: 426 passed / 3 failed (yalniz Y-A1; etkilesim yok)"
    cmd: "python -m pytest tests/unit/ui .agents/tasks/T-012/tester_A -q -p no:cacheprovider --import-mode=importlib -rfE --no-header"
    exit_code: 1
    result: kaldi
    evidence: tester_A_evidence/A-birlikte-kosum.txt
  - name: "sonda A-01 -- Y-A1 yeniden uretim (ayri surec, offscreen): [1] referans dusurme -> sekme gorunur+yokluyor+sag tik alicisiz; [2] deleteLater ayni; [3] tek basina KenarSekmesi toplanmaz; [4] kapat()+dusurme gizli sizinti; [5] pozitif kontrol: lambda baglantili QWidget toplanmaz, bagli yontemli toplanir -> 3 IHLAL"
    cmd: "python .agents/tasks/T-012/tester_A/sonda_a_01_omur_zombi.py"
    exit_code: 1
    result: kaldi
    evidence: tester_A_evidence/A-sonda-01-omur-zombi.txt
  - name: "depo dokunulmadi: git status --short -- src tests demo real_check packet evidence BOS; git diff HEAD --stat 0; sha256 src/ui (kabuk 100c4fcb..., kenar_sekmesi 7b42ba8b..., geometri d9afa598...), real_check 900925f7..., conftest d8bc361b...; HEAD 7c430eb"
    cmd: "git status --short -- src tests demo ...; git diff HEAD --stat -- src tests demo; sha256sum src/ui/*.py ..."
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/A-git-status-depo-dokunulmadi.txt
  - name: "korluk kaydi: implementer test ADLARI (109) yalniz kapsam boslugu icin, 239 mercek testi ve sonda-01 bittikten SONRA grep'lendi; govde acilmadi; delivery.md / evidence/ (sarici haric) / sef_dogrulama/ / tester_B* okunmadi"
    cmd: "grep -n '^def test_' tests/unit/ui/test_*.py | sed 's/(.*//'"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/A-implementer-test-adlari.txt
blocking_issues:
  - "Y-A1: kabuk.py docstring K1 'Sekme EBEVEYNSIZ Tool penceredir (Python sahipligi: AnaPencere silinince silinir, KRT o6)' OLCULEN IHLAL -- KenarSekmesi hic toplanmiyor (kenar_sekmesi.py 222-224: clicked.connect(lambda: self._mod_tiki(...)) kapanislari Qt baglantisinda self'i tutar); kenar durumundaki AnaPencere dusurulunce (del+gc ya da deleteLater) sekme GORUNUR + yokluyor + sag tik alicisiz = zombi ust-duzey pencere, geri donus yolu yok. Pozitif kontrol: bagli yontem baglantili QWidget toplanir. Yeniden uretim: sonda_a_01_omur_zombi.py (3 IHLAL) + 3 DOCSTRING testi. Duzeltme: uc lambda -> bagli yontem; docstring cumlesine olcen test adi. feedback-A.md"
---

# T-012 tur 1 -- Tester-A (mercek: durum makinesi + sinir + takma ad/omur)

Karar: **RET** -- tek bloklayici bulgu: **Y-A1**, docstring K1'in acik ve "olculdu" (KRT o6) diye yazilmis sahiplik iddiasinin olculen ihlali, sonucu zombi ust-duzey pencere. Urun yolu (`calistir` -> `app.quit` -> surec biter) etkilenmez; belgelenen modele guvenen her tuketici etkilenir; duzeltme uc satir (`feedback-A.md`). Bunun disinda **durum makinesi, sinirlar ve sinyaller olctugum her noktada docstring/paket v2 ile tutuyor**: 239 mercek testinin 236'si gecti; dusen 3'u yalniz Y-A1. Taban: mypy 0, 190 passed, real_check 18/18 TEMIZ (gercek ekran, sarici), kapsam %99.59; tam takimda tek dusen test T-011 sure testi (61.5/65.4 ms > 60, tek basina 4/4 gecer -- T-012 disi, yuk altinda pay).

Korluk: `delivery.md`, `evidence/**` (sarici haric), `sef_dogrulama/**`, `tester_B*` **okunmadi**; implementer testleri yalniz **ad** duzeyinde, isim bittikten sonra (`A-implementer-test-adlari.txt`). Ad duzeyinde gorunmeyen siniflar: omur/gc/weakref/deleteLater, iki ornek, rastgele yuruyus, `showMinimized`, taban sinif `hide()/show()`, `PANEL_BOYUTU` mutasyonu, yaricap > 66 salinimi, ust sinir tasmasi, `availableGeometryChanged` + `y` sinir disi / panel acikken, kenar degisimi acikken, mod tiki sonrasi yeniden acilma, `yoklama_ms=1` sayac cozunurlugu, surukleme + `hide()`, surukleme SIRASINDA sag tik.

Dosyalar: `tester_A/test_mercek_a.py` (239 test, 8 bolum), `tester_A/sonda_a_01_omur_zombi.py`, `tester_A/conftest.py`.

## YUKSEK

**Y-A1 · `KenarSekmesi` hic toplanmiyor -> kenar durumunda `AnaPencere` dusurulunce ZOMBI sekme (docstring K1 ihlali).** Iddia: "Sekme EBEVEYNSIZ `Tool` penceredir (Python sahipligi: `AnaPencere` silinince silinir, KRT o6)". Olcum (`A-sonda-01`): `AnaPencere` sarmalayicisi toplaniyor ve C++ nesnesi siliniyor (hem `del`+`gc.collect()`, hem `deleteLater`), sekme silinMIYOR: `weakref` canli, `isVisible()` True, `yokluyor` True, sag tik `pencereyi_goster` yayiyor ama alici yok -> ekranda `StaysOnTop` yarim daire kalir, geri donus yolu yok. `kapat()` cagrilmissa gizli sizinti (her ornek sizar; implementer takimi 190+ sekme sizdirir, gorunmez). Kok: `kenar_sekmesi.py` 222-224 `clicked.connect(lambda: self._mod_tiki(...))` -- lambda `self`i kapatir, Qt baglantisi callable'i C++ tarafinda tutar, gc dongusu gormez. **Pozitif kontrol:** ayni kalipta minimal `QWidget` -- lambda baglantili toplanmaz/gorunur kalir, `clicked.connect(self._tik)` toplanir (`test_d_omur_mekanizma_pozitif_kontrol_lambda_baglantisi_sarmalayiciyi_tutar`). KRT D6 olcumu prototipteydi (lambda yoktu); urun kodu mekanizmayi degistirip cumleyi olcmeden tasidi (4.6/3). Ikincil: yapici `availableGeometryChanged.connect` SONRASINDA tasarsa (`yaricap >= 2**30`) yarim kurulu nesne sinyale kalici bagli kalir ve her ekran degisiminde yuvasi istisna atar (D-A4, ayri surecte olculdu). Pinler: `test_d_omur_ana_pencere_referansi_dusunce_sekme_silinir_DOCSTRING`, `test_d_omur_delete_later_referans_birakilinca_sekme_silinir_DOCSTRING`, `test_d_omur_kenar_sekmesi_tek_basina_referans_dusunce_silinir_DOCSTRING` (3 failed); `..._kapat_sonrasi_dusurulen_ana_pencere_sekmeyi_sizdirir_PIN`, `..._delete_later_python_referansi_tutulurken_sekme_zombi_PIN` (gecen pinler).

## ORTA

**O-A1 · Mod tikinda imlec kapali sekmenin DISKI icinde kaliyorsa panel `acilma_ms` sonra YENIDEN acilir.** Dugmelerin sag ~26 px'i (`dugme_anlik` sag ucu, kenara <= 26 px) kapali diskin icindedir: tik -> `_kapat()` -> sinyal (bu anda `acik` False, boyut 26x52 -- docstring iddiasi TUTUYOR, `test_g_k4_sirasi_*` 4 dugme/2 duzey) -> bir sonraki yoklamada imlec disk icinde -> 120 ms sonra panel tekrar acik. Ertelenmis Snapshot karesine (>= 120+60 ms) panel metni girer. Pozitif kontrol: dugme ortasi (kenara 100 px) -> acik kalmaz; `real_check` [9] ortadan tikladigi icin gormez. Pin: `test_g_k4_mod_tiki_sonrasi_imlec_disk_icindeyse_panel_yeniden_acilir_PIN`. Oneri: mod tiki sonrasi imlec diskten bir kez cikana kadar acilma sayacini kilitle (tek atimlik mandal). Ihlal degil.

## DUSUK

**D-A1 · `goster()` kucultulmus pencereyi geri getirmez.** `showMinimized()` (Win+D sinifi) -> `tepsiye_al()` -> `goster()`: uclu (T,F,F) ama `isMinimized()` True kalir; docstring "pencere one gelir". Bu pakette kullanici yolu yok (dugmeler kucultulmusken tiklanamaz), kisayol servisi gelince (Ctrl+Alt+T) gorunur olur. `showNormal()`/`setWindowState(~Minimized)`. Pin: `test_b_k1_show_minimized_sonra_tepsi_sonra_goster_kucultulmus_kalir_PIN`.

**D-A2 · Taban sinif `hide()`/`show()` durum makinesini atlar (programatik).** `gorunur` + `hide()` -> (F,F,F), `kapandi` False, `durum` gorunur (docstring'in "ulasilamaz" dedigi uclu, kullanici yolu yok); `tepsi` + `show()` -> (T,F,T) tablo disi; `kapat()` + `show()` -> pencere gorunur, `kapandi` True (docstring yalniz `goster/tepsiye_al/kenara_al` icin "diriltmez" der; ikinci `close()` sinyal uretmez). `goster()` hepsini toparlar. `calistir` yalniz baslangicta `show()` kullanir (tutarli). Pinler `test_b_k1_dis_*`.

**D-A3 · `yaricap > 66` (= `PANEL_BOYUTU.height()//2`) kabul edilir -> panel sekmeyi kapsamaz -> salinim.** Docstring kosulu ("panel.h >= 2r oldugu surece") yazili ama dogrulama yalniz `>= 1`. Olcum: yaricap 80, disk icinde-panel disinda nokta, 20/20/10 ms -> 400 ms'de >= 4 acik/kapali gecisi; yaricap 26 ayni gorece noktada 0. Urun degeri 26 etkilenmez. Oneri: `2*yaricap <= PANEL_BOYUTU.height()` dogrulamasi. Pin: `test_e_sinir_yaricap_panel_yuksekliginin_yarisindan_buyukse_salinim_PIN`.

**D-A4 · Ust sinir dogrulanmaz.** `yaricap/acilma_ms/kapanma_ms/yoklama_ms >= 2**31` ve `yaricap >= 2**30` -> `OverflowError` (docstring `ValueError` sinifi disi); `yaricap` tasmasi `availableGeometryChanged.connect` SONRASINDA (Y-A1 sizintisiyla kalici, sonraki ekran degisimlerinde yuva istisnasi -- test kirliligi, bu yuzden ayri surecte olculdu); `yaricap = 2**30-1` kabul, Qt geometriyi 16777215'e kirpar, cokmez. Pin: `test_e_geometri_ust_sinir_overflow_ayri_surec_PIN`.

**D-A5 · `PANEL_BOYUTU: Final[QSize]` mutable (takma ad).** `PANEL_BOYUTU.setWidth(300)` -> acik panel 300x132. `Final` yalniz tip duzeyinde. Pin: `test_d_takma_ad_panel_boyutu_final_ama_mutable_PIN`.

**D-A6 · `yoklama_ms=1` Windows kaba sayaciyla ~16 ms.** 400 ms'de 25 cagri (60 ms: 6), CPU ~0. Docstring iddiasi yok; bilgi. `test_f_zaman_yoklama_0_valueerror_ve_1_calisir`.

**D-A7 · `imlec_konumu` istisna atarsa** her yoklamada istisna Qt yuvasindan sizar (pytest-qt yakalar, `>= 2` RuntimeError/60 ms), yoklayici durmaz, `acik` False kalir; kotu kullanim, bilgi. Pin `test_d_omur_imlec_konumu_istisna_atarsa_*`.

**D-A8 · Panel ekrandan buyukse** (100x100) `sag` -> sag kenara bitisik, ust = top, sola tasar; "ekran icine sikistirilmis" bu sinifta karsilanamaz; bilgi. `test_e_geometri_panel_ekrandan_buyuk_kenara_bitisik_ust_kenar`.

## Dogrulanan K1-K8 iddialari (secki; hepsi `A-mercek-testleri.txt`)

- **K1 tablo (110 hucre):** 5 baslangic satiri (`gorunur`, `tepsi`, `kenar`, `kenar (tepsi yok)`, `gorunur (tepsi yok)`) x 22 eylem (`goster/tepsiye_al/kenara_al/kapat/close()/closeEvent`, 3 ust dugme, tepsi `activated` Trigger/DoubleClick/Context/Middle/Unknown, 3 menu eylemi, sekme sag tik (gercek tik gorunurken), `dugme_goster`, 2x2 mod dugmesi) -> `durum` + uclu + `cikis_istendi` sayisi + `kapandi` + `yoklayici == sekme gorunur` + panel kapali, hepsi beklenenle ayni; kapat sinifinda ikinci `kapat()`+`close()` 1 kalir. `kenar -> tepsi` yolu yok; K5 istisna satiri (F,T,F). `kapat()` sonrasi 11 eylemin hicbiri diriltmez, sinyal 1, `durum` son durumu korur; gorunur ust-duzey 0 (5 satir).
- **Rastgele yuruyus:** 8 tohum x 40 kamu eylemi: her adimda uclu tabloda / (F,F,F), `cikis_istendi <= 1` ve `kapandi` ile tutarli, tepsi yokken `tepsi` durumu hic; pozitif kontrol (taban sinif `hide()`) olcuyu atesler.
- **Sinyaller:** `cikis_istendi` 5 yol x 4 durum tam bir kez + ardindan 5 yol daha 1; mod sinyalleri dinleyicisiz hatasiz, pencere/sekme dugmeleri ayni sinyal; K4 sirasi 3 dugme (`acik` False, 26x52, dugme gorunmez) + `AnaPencere` duzeyi ((F,T,T) korunur); yeniden giris: mod dinleyicisi `goster/kapat/kenara_al` cagirir, `cikis` dinleyicisi `kapat/close/goster/kenara_al` cagirir -> tutarli, sinyal 1.
- **Omur:** `deleteLater` ile tepsi ikonu gecersiz (C++ ebeveynlik, zombi ikon yok); iki `AnaPencere` bagimsiz (ayri sekme/tepsi/menu; biri kapaninca digeri etkilenmez); `KenarSekmesi` tek basina calisir; `ekran=None` -> birincil; `primaryScreen()` None -> `RuntimeError`, sizdirilmis pencere yok; gecersiz `kenar` -> `ValueError`, pencere sizmaz; `calistir` gercek `exec()` ile `cikis_istendi -> quit`, donus 0, `kapandi`, gorunur ust-duzey 0; `ekran_dikdortgeni` kopya; `kenar`/`y` gecersiz atamada durum degismez (atomik), `kenar="sol"` str kabul.
- **Sinir geometri:** yaricap 1: 5 ekran x 2 kenar x 5 `y` -> 1x2 dikdortgen, iki piksel de disk icinde, panel kapsar, `KenarSekmesi(yaricap=1)` acilir; yaricap 0/-1/-26 saf fonksiyonlarda cokmez, yapicida `ValueError`; yaricap = ekran yuksekligi -> `y = top`, alt tasma kabul (docstring); bos/negatif `QRect` cokmez; `y_sinirla` monoton + idempotent + tam sinirda (`alt`, `alt+1`, `top-1`), tam sinirda sekme alt kenari = ekran alt kenari; disk: ic koseler disarida, kenar tarafi koseleri iceride, ic kenar ortasi iceride, dikdortgen disi disk noktasi disarida, sayilan piksel ~ pi r^2/2 (+-%6, bagimsiz referans); `y` float kirpilir, "13" kabul, bool 1, -inf/None/list/"abc" reddedilir ve durum degismez, `s.y()` TypeError (docstring); `availableGeometryChanged` kucultme -> `y` sikistirilir + yeni x, buyutme -> `y` sabit, 30x30 -> `y = 0`, panel acikken -> yeniden bitisik ve acik kalir; `kenar` degisimi acikken -> sol kenara bitisik 200x132, imlec disarida kalinca kapanir.
- **Sinir zaman:** `acilma_ms=0`/`kapanma_ms=0` calisir; `kapanma < yoklama` (5/50) <= 205 ms; `2**31-1` hic acilmaz, yoklayici calisir; `yoklama_ms=0`/negatif sureler `ValueError`; `hide()` -> `yokluyor` False ve enjekte sayac artmaz, `show()`/`setVisible` -> artar (urun 60 ms); `hide()` calisan acilma sayacini sifirlar (150+100+100 > 200 ama kapali); surukleme + `hide()` -> `surukleniyor` False, `show()` sonrasi yoklama calisir; surukleme SIRASINDA sag tik -> sinyal 1, surukleme surer (tek basina) / `AnaPencere` ile `goster()` -> sekme gizlenir, surukleme temizlenir; surukleme alt/ust sinira kilitlenir (100000 px), `acik` degismez, birakinca acilir -- hizli ve urun sayaclariyla (kural 7); acik panel cercevesinde sol tik surukleme baslatmaz.
- **K6/K7:** 6 dosya AST (yasak ad + import; `uygulama.py` yalniz `exec`/`quit`), pozitif kontrol; taze surecte `src.capture/ocr/translate` yuklenmez (+ pozitif kontrol); enum uyeleri ve urun sabitleri; salt-okunur ozellikler.

## Tester yukumlulugu / oneri (sef icin, sirali)

1. **Y-A1** uc lambda -> bagli yontem; docstring cumlesine olcen test (`weakref` + `gc.collect` + gorunur ust-duzey); `availableGeometryChanged.connect`i `_kapat()` sonrasina al. Ret nedeni yalniz bu.
2. **O-A1** mod tiki sonrasi tek atimlik "diskten cik" mandali; `real_check` [9]'a dugmenin sag ucundan tik varyanti.
3. **D-A1** `goster()` icinde `showNormal()` (kisayol servisi oncesi ucuz).
4. **D-A3** `2*yaricap <= PANEL_BOYUTU.height()` dogrulamasi (docstring kosulunu koda tasir).
5. Tam takim: T-011 `test_k5_sure_8000_uyeli_zincir_60ms_alti` tam takim yukunde 61.5/65.4 ms > 60 (tek basina 0.5-0.7 s'de gecer) -- T-011 D-A13 sinifi, `_izleyici_payi` tam takimda da uygulanmali; T-012 disi.
6. `tester_A/` sefin dizinine tasinabilir: gecis tablosu (110), rastgele yuruyus, omur/weakref testleri implementer adlarinda yok.
