---
task: T-013
role: implementer
round: 1
status: tamamlandi
files_written:
  - src/ui/kisayol.py
  - src/ui/uygulama.py
  - src/ui/kabuk.py
  - tests/unit/ui/test_kisayol.py
  - tests/unit/ui/test_uygulama.py
  - tests/unit/ui/test_kabuk.py
  - .agents/tasks/T-013/delivery.md
  - .agents/tasks/T-013/evidence/olcum-on-pyside-davranislari.py
  - .agents/tasks/T-013/evidence/olcum-on-pyside-davranislari.txt
  - .agents/tasks/T-013/evidence/tdd-kirmizi-1-kisayol-modul-yok.txt
  - .agents/tasks/T-013/evidence/tdd-kirmizi-2-uygulama-kabuk-eski-kodda.txt
  - .agents/tasks/T-013/evidence/tdd-kirmizi-2b-kabuk-yeni-testler-eski-kodda.txt
  - .agents/tasks/T-013/evidence/mypy.txt
  - .agents/tasks/T-013/evidence/mypy-test-dosyalari.txt
  - .agents/tasks/T-013/evidence/pytest.txt
  - .agents/tasks/T-013/evidence/cov.txt
  - .agents/tasks/T-013/evidence/real_check.txt
  - .agents/tasks/T-013/evidence/pytest-tum-kosum1-t011-sure-titremesi.txt
  - .agents/tasks/T-013/evidence/pytest-tum-kosum2.txt
  - .agents/tasks/T-013/evidence/pytest-tum-kosum3.txt
  - .agents/tasks/T-013/evidence/pytest-tum-kosum4.txt
  - .agents/tasks/T-013/evidence/pytest-t011-sure-testleri-tek-basina.txt
  - .agents/tasks/T-013/evidence/pytest-translate-tek-basina-t011-sure.txt
  - .agents/tasks/T-013/evidence/pytest-tum-ui-haric.txt
  - .agents/tasks/T-013/evidence/pytest-cp1254.txt
  - .agents/tasks/T-013/evidence/mutant-kiti.py
  - .agents/tasks/T-013/evidence/mutant-ayirt-etme.txt
  - .agents/tasks/T-013/evidence/mutant-ayirt-etme-hangi-testler.txt
  - .agents/tasks/T-013/evidence/olcum-filtre-gecikme-offscreen.py
  - .agents/tasks/T-013/evidence/olcum-filtre-gecikme-offscreen.txt
  - .agents/tasks/T-013/evidence/demo-ekran-goruntusu.py
  - .agents/tasks/T-013/evidence/demo-ekran-goruntusu.txt
  - .agents/tasks/T-013/evidence/kabuk_kisayollar.png
  - .agents/tasks/T-013/evidence/kabuk_kisayol_cakisma.png
commands:
  - cmd: "python -m mypy --strict --explicit-package-bases src/ui  (7 dosya: T-012'nin 6'si + kisayol.py; temiz)"
    exit_code: 0
    evidence: evidence/mypy.txt
  - cmd: "python -m pytest tests/unit/ui -q -p no:cacheprovider  (379 passed: T-012 tabani + 157 yeni T-013 testi -- 128 kisayol, 18 uygulama, 11 kabuk; sefin 3 bariyer testi dahil)"
    exit_code: 0
    evidence: evidence/pytest.txt
  - cmd: "python .agents/tasks/T-013/real_check.py  (GERCEK Windows, ekran kilitsiz, arka plan kabugundan, sentetik keybd_event: 12/12 TEMIZ -- [1a] 1.6 ms, [5] NOREPEAT 1 / NOREPEAT'siz 5, [6] 20/20, [8] T='₺' D='' ALTGR_CAKISMA, [9] del+gc, [3] cakisma metni + '(kısayol yok)')"
    exit_code: 0
    evidence: evidence/real_check.txt
  - cmd: "python -m pytest tests/unit/ui -q -p no:cacheprovider --cov=src.ui --cov-fail-under=95 --cov-report=term-missing  (767 ifade, %99.74; kisayol.py %100 -- ince Win32 sarmalayicilari pragma: no cover; eksik 2: uygulama.py 80/84 gercek sys.argv/exec dallari, T-012 ile ayni)"
    exit_code: 0
    evidence: evidence/cov.txt
  - cmd: "python -m pytest tests -q -p no:cacheprovider  (tam takim kosum 1: 2 failed / 2272 passed -- ikisi de T-011 tests/unit/translate/test_sozluk.py SURE testleri (51.2 ms / 69.0 ms, butce 50 / 60), T-013 sahiplik disi; asagida)"
    exit_code: 1
    evidence: evidence/pytest-tum-kosum1-t011-sure-titremesi.txt
  - cmd: "python -m pytest tests -q -p no:cacheprovider  (tam takim kosum 2: 1 failed / 2273 passed -- test_k5_sure_8000_uyeli_zincir_60ms_alti 69.7 ms)"
    exit_code: 1
    evidence: evidence/pytest-tum-kosum2.txt
  - cmd: "python -m pytest tests -q -p no:cacheprovider  (tam takim kosum 3: 1 failed / 2273 passed -- ayni test 65.3 ms)"
    exit_code: 1
    evidence: evidence/pytest-tum-kosum3.txt
  - cmd: "python -m pytest tests -q -p no:cacheprovider  (tam takim kosum 4, mutant kiti bittikten sonra: 2 failed / 2274 passed -- yine yalniz T-011 sure testleri (8000 uyeli zincir 73.2 ms, 8000 hit gom); T-013 testlerinin hepsi gecti)"
    exit_code: 1
    evidence: evidence/pytest-tum-kosum4.txt
  - cmd: "python -m pytest tests/unit/translate -q -p no:cacheprovider  (YALNIZ translate dizini, hicbir UI testi kosmadan: ayni 2 T-011 sure testi dusuyor -> T-013'ten BAGIMSIZ)"
    exit_code: 1
    evidence: evidence/pytest-translate-tek-basina-t011-sure.txt
  - cmd: "python -m pytest tests -q -p no:cacheprovider --ignore=tests/unit/ui  (tam takim tests/unit/ui HARIC: 5 failed / 1892 passed -- hepsi T-011 test_sozluk.py sure testleri (medyan 59.0 / 70.0 / 68.2 ms, butce 50); T-013 testleri hic kosmadan da dusuyor)"
    exit_code: 1
    evidence: evidence/pytest-tum-ui-haric.txt
  - cmd: "python -m pytest tests/unit/translate/test_sozluk.py -q -p no:cacheprovider -k sure  (T-011 sure testleri TEK BASINA: 4 passed x3 kosum; tam takim yuku + makinede arka plan surecleri (CPU %23) ile titriyor; T-013 src/ui disina dokunmaz)"
    exit_code: 0
    evidence: evidence/pytest-t011-sure-testleri-tek-basina.txt
  - cmd: "python -m mypy --strict --explicit-package-bases src/ui tests/unit/ui/test_kisayol.py tests/unit/ui/test_uygulama.py tests/unit/ui/test_kabuk.py  (uc test dosyasi + modul birlikte temiz)"
    exit_code: 0
    evidence: evidence/mypy-test-dosyalari.txt
  - cmd: "cmd /c cp1254.cmd  (chcp 1254, PYTHONIOENCODING/PYTHONUTF8 bos, sys.stdout.encoding=cp1254; python -m pytest tests/unit/ui -q: 379 passed)"
    exit_code: 0
    evidence: evidence/pytest-cp1254.txt
  - cmd: "python -m pytest tests/unit/ui/test_kisayol.py -q --tb=line  (TDD KIRMIZI 1: src/ui/kisayol.py yokken toplama hatasi)"
    exit_code: 2
    evidence: evidence/tdd-kirmizi-1-kisayol-modul-yok.txt
  - cmd: "python -m pytest tests/unit/ui/test_uygulama.py tests/unit/ui/test_kabuk.py -q --tb=line -rfE  (TDD KIRMIZI 2: kisayol.py var, uygulama.py/kabuk.py T-013 API'siz: test_uygulama toplama hatasi (VARSAYILAN_KISAYOLLAR yok))"
    exit_code: 2
    evidence: evidence/tdd-kirmizi-2-uygulama-kabuk-eski-kodda.txt
  - cmd: "python -m pytest tests/unit/ui/test_kabuk.py -q --tb=line -rfE  (TDD KIRMIZI 2b: eski kabuk.py'de 11 yeni T-013 testi duser (durum_goster/kisayol_etiketleri/kisayol_tetiklendi yok), 73 T-012 testi gecer)"
    exit_code: 1
    evidence: evidence/tdd-kirmizi-2b-kabuk-yeni-testler-eski-kodda.txt
  - cmd: "python .agents/tasks/T-013/evidence/mutant-kiti.py  (ayna agaci, kemer aynada da acik; 34 davranis mutanti YAKALANDI + 4 kontrol KACTI; ilk kosumda M28 kacti -> dilbilgisi tablosuna sinif ayrimi (bozuk metin DUZ ValueError) + 2 ornek eklendi, ikinci kosum 34/34)"
    exit_code: 0
    evidence: evidence/mutant-ayirt-etme.txt
  - cmd: "python .agents/tasks/T-013/evidence/olcum-on-pyside-davranislari.py  (tasarimdan ONCE, offscreen + gercek ToUnicodeEx, kayit yok: partial 0 ek argumanla cagrilir; QByteArray==bytes; installNativeEventFilter sarmalayiciyi TUTMAZ; filtre weakref(servis) ile del+gc toplanir ve destroyed partial kosar; Ctrl+Alt ile yalniz harf/rakam karakter uretir (Space/Tab/Enter/Esc/ok/F bos); thread kimligi)"
    exit_code: 0
    evidence: evidence/olcum-on-pyside-davranislari.txt
  - cmd: "python .agents/tasks/T-013/evidence/olcum-filtre-gecikme-offscreen.py  (offscreen, sahte Win32, gercek MSG yapisi + addressof: bilinen kimlik -> tetiklendi medyan 1.1 us / max 13.8 us (n=1000); bilinmeyen/yanlis eventType/eski servis False 0.3-0.5 us; kayit_fn cagrisi 2, gercek RegisterHotKey yok)"
    exit_code: 0
    evidence: evidence/olcum-filtre-gecikme-offscreen.txt
  - cmd: "python .agents/tasks/T-013/evidence/demo-ekran-goruntusu.py  (GERCEK windows platformu, gercek servis, calistir varsayilan yolu: kabuk_kisayollar.png dugmelerde Ctrl+Alt+D / Ctrl+Alt+R; kabuk_kisayol_cakisma.png baska surec D tutarken '(kısayol yok)' + durum satiri; cocuk surec try/finally)"
    exit_code: 0
    evidence: evidence/demo-ekran-goruntusu.txt
contract_change_request: false
known_gaps:
  - "[TAM TAKIM EXIT 1 -- T-011 SURE TESTLERI, T-013'TEN BAGIMSIZ] `pytest tests -q` dort kosumda da yalniz T-011'in `tests/unit/translate/test_sozluk.py` SURE testleri dustu (kosum 1: 1000 segment medyan 51.2 ms > 50, 8000 uyeli zincir 69.0 ms > 60; kosum 2: 69.7; kosum 3: 65.3; kosum 4: 73.2 + 8000 hit gom). T-013 testlerinin hepsi dort kosumda da gecti. BAGIMSIZLIK OLCULDU: (a) yalniz `tests/unit/translate` (UI testi hic kosmadan) -> ayni 2 test dusuyor; (b) tam takim `--ignore=tests/unit/ui` -> 5 T-011 sure testi dusuyor (59.0/70.0/68.2 ms); (c) `-k sure` alt kumesi tek basina 4/4 x3 gecer. Butceler izleyicisiz mutlak ms; makinede surekli arka plan yuku var (GPU surucu servisi, canli duvar kagidi, bir sohbet masaustu uygulamasi, oyun motoru editoru; CPU %23-24 bosta). T-013 `src/ui` ve `tests/unit/ui` disina dokunmaz (`git status`); T-012 teslimi de ayni sinifi 'T-011 bakim kalemi' olarak kaydetmisti. Bu delil kabul komutunun cikis kodunu 0 yapmaz; sef karari."
  - "[PAKETIN LAFZINDAN SAPMALAR -- OLCULDU, BELGELI] (a) K3 >= 2 degistirici kurali paket 'harf/rakam/Space' der; Tab/Enter/Esc/Backspace/Delete/Insert/Home/End/PageUp/PageDown/ok tuslari da yazma-gezinme tuslari oldugundan AYNI kural (Alt+Enter, Ctrl+Tab, Shift+Delete tek degistiriciyle GECERSIZ) -- bir adim otesi; F1-F11 >= 1 paket gibi. (b) K6 thread kurali paket yalniz `kaydet` der; `kaldir`/`hepsini_kaldir` de ana thread'e bagli (`UnregisterHotKey` baska thread'den 1419) -- `test_k6_baska_threadden_kaldir_ve_hepsini_kaldir_runtimeerror`. (c) `kaydet` bozuk metinde (bos, tekrar eden degistirici, iki tus) istisna YAYMAZ, `GECERSIZ` doner (paket K3 `ValueError`i dilbilgisi fonksiyonu icin yazar; `kaydet` icin sessiz) -- K5 'istisna kabuga ulasmaz'; `kombinasyonu_coz` iki sinifi ayirir: bozuk metin DUZ `ValueError`, yasak kombinasyon `GecersizKombinasyon(ValueError)`. (d) K1 'ayni ad yeniden kaydet -> once eski kaldirilir': dilbilgisi + AltGr denetimi ESKI KAYDI KALDIRMADAN once yapilir; gecersiz yeni kombinasyon eski kaydi bozmaz (`test_k1_ayni_ad_gecersiz_yeni_kombinasyon_eski_kayit_korunur`); Win32 cagri sirasi paketin dedigi gibi kaldir -> kaydet. Win32 1409 SONRASI eski kayit geri GELMEZ -- `[ÖLÇÜLMÜYOR]` (v2 geri alma). (e) K1 OLCU '`removeNativeEventFilter` sahte uygulama nesnesinde sayildi': arayuze parametre eklemeden `kisayol._uygulama()` modul yardimcisi monkeypatch'lenir (sahte uygulama install/remove sayar, gercek uygulamaya iletir, `thread()` iletir). (f) `kayitli()` `dict` KOPYASI doner (`Mapping` arayuzu saglanir; takma ad testi)."
  - "[Y3 -- OLCULDU] `destroyed` alicisi `functools.partial(_yikimda_temizle, kimlikler, kaldir_fn, filtre, app.removeNativeEventFilter)`; `self` argumanlarda YOK (yapisal AST bekcisi + M03/M03b). On olcum o1: PySide partial'i 0 ek argumanla cagirir (`*_` toleransli). Filtre servise `weakref` ile ulasir; `installNativeEventFilter` Python sarmalayicisini canli TUTMAZ (o3: del+gc sonrasi weakref None) -> servis `_filtre` guclu referansini kendi tutar (KRT p3 'olaylar gelmeye devam' C++ tarafinda; Python override'i sarmalayicisiz cagrilamaz -- gozlem, urun yolunda sarmalayici tutulur). Cikista (`QApplication` yikimi widget'lari, cocuk servisi silerken) temizleyici kosar, cikis kodu 0 (on olcum, ayri alt surec). `deleteLater` yolu kapida `[ÖLÇÜLMÜYOR]` (paket: `bekle()` DeferredDelete islemez), birim testte olculur; `del`+gc yolu kapi [9] TEMIZ."
  - "[Y1 -- OLCULDU] Enjeksiyonsuz `calistir` gercek servis kurar (`KisayolServisi(pencere, gercek_win32=True)`); testte kemer `RuntimeError` (`test_k4_kisayol_servisi_verilmezse_gercek_servis_kurulur_kemer_ateslenir` + casus sinifla yapici argumanlari `(pencere, gercek_win32=True)`). Birim testlerin HICBIRI gercek `RegisterHotKey` cagirmaz: mutant kiti aynada da kemer acik. Kemerin pozitif kontrolu: degisken silinince `KisayolServisi(gercek_win32=True)` KURULUR, `kaydet` cagrilmaz (filtre kurulur/sokulur, Win32 yok)."
  - "[Y2 -- OLCULDU] Varsayilan `Ctrl+Alt+D` / `Ctrl+Alt+R` (`VARSAYILAN_KISAYOLLAR` salt okunur `MappingProxyType`); gercek `altgr_karakteri`: TR-Q'da T='₺', D='' (kapi [8]); `Ctrl+Alt+T` `ALTGR_CAKISMA`, Win32 cagrilmaz. On olcum o5: Ctrl+Alt durumunda yalniz harf/rakam karakter uretir, Space/Tab/Enter/Esc/Backspace/Delete/Insert/Home/End/PageUp/PageDown/ok/F1/F11 bos -> AltGr sorgusu her tusa sorulur, yalniz harf/rakamda dolu cikar. Olu tus (`ToUnicodeEx < 0`) bos durumla `Space` sorgusuyla temizlenir, olu tus karakteri doner (AltGr o tusu kullaniyor -> cakisma) -- TR-Q'da AltGr olu tusu YOK, `[ÖLÇÜLMÜYOR]`. Duzen sorgusu `GetKeyboardLayout(0)` = bu thread'in KAYIT ANINDAKI duzeni; calisirken duzen degisimi ve TR-F/diger duzenler `[ÖLÇÜLMÜYOR]` (duzen yuklemek kullanici ayarini degistirir)."
  - "[ÖLÇÜLMÜYOR -- ayar dosyasi] Kisayol degistirme yolu yok (v2); durum satiri 'ayarlardan degistirin' YAZMAZ (`test_k5_cakisma_durum_satiri_ve_etiketler`: 'ayar' gecmez)."
  - "[ÖLÇÜLMÜYOR -- donanim autorepeat] Fiziksel typematic sentetik girdiyle uretilemez; ayirt edici sinif (tekrar bayragi: 5 DOWN UP'siz) kapi [5] ile OLCULDU: NOREPEAT'li 1, NOREPEAT'siz gecici kayit 5."
  - "[ÖLÇÜLMÜYOR -- exclusive fullscreen ve UAC yukseltilmis on plan] Sentetik girdi yukseltilmis pencereye UIPI'den gecmez (KRT f2); borderless topmost baska surecte kisayol geliyor (KRT f1). Donanim tusuyla el olcumu gerekir."
  - "[ÖLÇÜLMÜYOR -- yuk altinda gecikme] Bosta kapi [1a] 1.6 ms (< 20); offscreen filtre dagitimi 1.1 us medyan; GIL'i tutan surec ici thread'ler altinda KRT 200+ ms -- pipeline entegrasyon gorevinin yukumlulugu."
  - "[ÖLÇÜLMÜYOR -- bozuk MSG adresi] Filtre `message` adresini yalniz Qt'den alir; sifir/bozuk adres `MSG.from_address` ile sureci oldurur (KRT k9); olcusu YOK. Yanlis `eventType` mesaja DOKUNMADAN `False` (gecerli MSG + yanlis tip ile olculur, sifir adresle DEGIL)."
  - "[ÖLÇÜLMÜYOR -- kimlik tukenmesi] 1..0xBFFF hepsi canliysa `RuntimeError` (pragma: no cover; 49151 canli kayit gercekci degil); sarma ve canli atlama olculdu (`test_k1_kimlik_*`)."
  - "[KOTU KULLANIM -- belgeli] C++ oldukten sonra tutulan servis sarmalayicisinda `kaydet` PySide `RuntimeError` verir (standart). `kisayol_servisi` enjekte edilince `calistir` onu YENIDEN EBEVEYNLEMEZ (test sahibi yasatir); baglanti bagli yontem oldugundan pencere toplanabilir (`test_k4_calistir_sonrasi_pencere_toplanabilir_baglanti_pencereyi_tutmaz`)."
  - "[EVIDENCE] LF korundu; delillerde mutlak yol yok (`<depo>`, `<gecici dizin>`, `pytest-of-<kullanici>`); model/saglayici/arac adi yok (tarandi). `git add`/`commit` ATILMADI. `conftest.py`, `real_check.py`, `olcum_kisayol.py`, `krt_kosumlari/`, `kenar_sekmesi.py`, `geometri.py`, `demo/` dokunulmadi (`git status`: yalniz owns dosyalari)."
---

# T-013 tur 1 -- teslim ozeti

`src/ui/kisayol.py` (`KisayolServisi`, `KayitSonucu`, `kombinasyonu_coz`/`kombinasyonu_yaz`, `altgr_karakteri`),
`calistir`e kisayol kurulumu (`kisayollar`, `kisayol_servisi`), kabuga `durum_goster`/`durum_metni`/
`kisayol_etiketleri`/`kisayol_tetiklendi`. **379 birim testi** (157 yeni), kapsam **%99.74** (kisayol %100),
mypy modul + 3 test dosyasi temiz, **kapi v2 12/12 TEMIZ** (gercek Windows, kilitsiz), **mutant 34/34 + 4 kontrol**,
cp1254 379, tam takim: **exit 1 -- yalniz T-011 sure testleri**, T-013'ten bagimsizligi olculdu (asagida).

## Paket itirazlari

Paketle celisen olcum yok; lafzindan sapmalar `known_gaps` [PAKETIN LAFZINDAN SAPMALAR] (a)-(f): >= 2 degistirici
kurali tum yazma/gezinme tuslarina; thread kurali `kaldir`/`hepsini_kaldir`a da; `kaydet` bozuk metinde `GECERSIZ`
(istisna degil); dilbilgisi/AltGr denetimi eski kaydi kaldirmadan once; `removeNativeEventFilter` sayimi
`_uygulama()` monkeypatch'iyle; `kayitli()` kopya. Hicbiri bir kapi kalemini degistirmez.

## Kapi itirazi

Yok: `real_check.py` v2 12/12 TEMIZ ilk kosumda (`evidence/real_check.txt`). [7] RAPOR: on plan degismedi, menu modu
False/False. [3] cocuk surec `try/finally`.

## Tasarim (K1-K6, modul docstring'leri ayrintili)

| karar | mekanizma | olcu |
|---|---|---|
| Y1 kemer | `gercek_win32=False` iken 4 fn zorunlu (`RuntimeError`); `True` + `SUFLOR_GERCEK_KISAYOL_YASAK` -> `RuntimeError`; `calistir` verilmezse `KisayolServisi(pencere, gercek_win32=True)` | `test_k2_gercek_win32_*` (4 param + 3), `test_k4_kisayol_servisi_verilmezse_*`; M14/M14b |
| K1 kimlik | modul sayaci 1..0xBFFF, sarar, canli kimlik atlanir; servis basina ayrik | `test_k1_kimlik_*` x3; M02/M29 |
| Y3 yikim | `destroyed -> partial(_yikimda_temizle, kimlikler, kaldir_fn, filtre, app.removeNativeEventFilter)`; filtre `weakref(servis)` | `test_k1_yikim_*` x4 (del+gc, deleteLater, ebeveyn, cift kaldirma yok) + pozitif kontrol (bagli yontem kosmaz) + AST; M03/M03b/M15/M30 |
| K2 filtre | eventType -> `MSG.from_address` -> `WM_HOTKEY` -> tablo; bilinmeyen `False` | `test_k2_*` x8 (gercek MSG + addressof; filtre sirasi iki servis); M04/M05 |
| K3 dilbilgisi | saf, ASCII, `+`; Win/F12/tek degistirici/kara liste `GecersizKombinasyon`; bozuk `ValueError` | tablo 80 ornek (33 gecerli, 25 gecersiz, 22 bozuk) + kanonik yazim tersine; M07/M08/M09/M22/M23/M28 |
| Y2 AltGr | `Ctrl+Alt+<tus>` Shift'siz -> `altgr_karakteri_fn(vk)` dolu -> `ALTGR_CAKISMA`, Win32 yok | `test_k3_altgr_*`; kapi [8] gercek T='₺'; M06/M06b/M20 |
| K4 baglanti | `tetiklendi -> pencere.kisayol_tetiklendi` (bagli yontem), `cikis_istendi -> hepsini_kaldir` | `test_k4_*` (uc durum, bilinmeyen ad, omur); kapi [1][2][4]; M18/M19/M21 |
| K5 gorunurluk | durum satiri `"<k> kaydedilemedi: <sebep>; ...; . Pencere düğmeleri ve tepsi menüsü çalışmaya devam eder."`; dugme/ipucu/tepsi `kisayol_etiketleri(servis.kayitli())`, kaydedilemeyen "(kısayol yok)" | `test_k5_*` x7, `test_t013_k5_*` x7; kapi [3]; ekran goruntusu; M10/M11/M12/M12b/M26 |
| K6 | AST (yasak adlar, lambda yok, pragma), thread `RuntimeError` | `test_k6_*` x3; M13/M27 |

## Sayilar

| olcu | deger |
|---|---|
| birim | 379 (128 kisayol + 18 uygulama + 11 kabuk yeni); kapsam %99.74 (767 ifade; eksik 2 = T-012 ile ayni) |
| mypy | modul 7 dosya + 3 test dosyasi temiz |
| kapi | v2 **12/12 TEMIZ**; [1a] 1.6 ms |
| tam takim | 4 kosum, hepsinde yalniz T-011 sure testleri (2/1/1/2); UI haric kosumda da 5 T-011 sure testi dusuyor -> bagimsiz |
| mutant | **34/34** yakalandi, 4 kontrol kacti (ilk kosum M28 kacti -> test guclendirildi) |
| cp1254 | 379 |
| TDD kirmizi | 3 delil (modul yok / uygulama toplama hatasi / kabuk 11 failed - 73 passed) |
| on olcum | PySide davranislari o1-o6; offscreen filtre 1.1 us |
