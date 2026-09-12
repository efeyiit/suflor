---
task: T-012
role: tester
round: 2
decision: onay
checks:
  - name: "taban 1 -- mypy --strict temiz (6 dosya)"
    cmd: "python -m mypy --strict --explicit-package-bases src/ui"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/tur2/taban-1-mypy.txt
  - name: "taban 2 -- implementer birim testleri 216 passed"
    cmd: "python -m pytest tests/unit/ui -q -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/tur2/taban-2-pytest-ui.txt
  - name: "taban 3 -- real_check v3: OTURUM KILITLI (LogonUI x2, on plan LockApp) -- gercek fare/on plan kalemleri ([3],[5],[5c]) bu oturumda da olculemedi; kilitten bagimsiz kalemler sonda_1a (v3'e karsi yeniden) + sonda_2a ile olculdu"
    cmd: "powershell Get-Process LogonUI  (calisiyor -> kapi kosulmadi)"
    exit_code: 1
    result: kaldi
    evidence: tester_B_evidence/tur2/kilit-durumu-son.txt
  - name: "taban 4 -- kapsam %99.61 (517 ifade, 2 eksik: uygulama.py 36/40)"
    cmd: "python -m pytest tests/unit/ui -q -p no:cacheprovider --cov=src.ui --cov-fail-under=95 --cov-report=term-missing"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/tur2/taban-4-kapsam.txt
  - name: "taban 5 -- tam takim 2113 passed"
    cmd: "python -m pytest tests -q -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/tur2/taban-5-tum-takim.txt
  - name: "tur-1 mercek-B testleri v3 koduna karsi HAM: 8 failed / 91 passed -- hepsi sinifli (2 XPASS O-B1 duzeltildi; 3 `ac()` yardimcim mandal-farkinda degildi; c7 D-B6 duzeltildi; c2x10 O-B1 yan etkisi; f1 Y-B1/O-B2 duzeltildi); urun hatasi YOK"
    cmd: "python -m pytest .agents/tasks/T-012/tester_B -q -p no:cacheprovider --import-mode=importlib -rfEx --tb=short  (dosyalar guncellenmeden once)"
    exit_code: 1
    result: gecti
    evidence: tester_B_evidence/tur2/tur1-testleri-v3-koduna-karsi-HAM.txt
  - name: "mercek-B tur 1 (ters cevrilmis) + tur 2 (43 yeni): 138 passed + 2 skipped + 2 xfail(strict)=BULGU (O-B5 zombi, D-B10 demo Esc) = 142 kosum"
    cmd: "python -m pytest .agents/tasks/T-012/tester_B -q -p no:cacheprovider --import-mode=importlib -rfEsx --tb=short"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/tur2/mercek-b-tur1+tur2-testleri.txt
  - name: "mercek-B + implementer birlikte, iki sirada: 354 passed + 2 skipped + 2 xfailed (balon sinif sayaci dahil ortam kirliligi yok)"
    cmd: "python -m pytest tests/unit/ui .agents/tasks/T-012/tester_B -q -p no:cacheprovider --import-mode=importlib  ;  ters sira"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/tur2/birlikte-kosum.txt
  - name: "sonda 2a (gercek ekran, kilitten bagimsiz): S8 sekme hwnd'sine gercek WM_CLOSE -> kapandi 1, (T,F,F), Shell ikon yok, yeni hwnd (tepsili/tepsisiz); S9 Win32 capture SW_HIDE'da birakiliyor (D-B10 gercek OS'te ulasilmaz); S10 deleteLater+ref ZOMBI (O-B5) ve tek satir duzeltme calisiyor; S11 balon bayragi + kapat sonrasi Shell'de ikon yok"
    cmd: "python .agents/tasks/T-012/tester_B/sonda_2a_tur2_kilitten_bagimsiz.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/tur2/sonda2a-tur2-kilitten-bagimsiz.txt
  - name: "sonda 1a v3'e karsi yeniden (Alt-Tab, Shell ikon kanali, WM_CLOSE uc durum, z-sirasi, DPI %125 birincil): tur 1 ile birebir; tek bulgu D-B1 (+1 px, bilinen)"
    cmd: "python .agents/tasks/T-012/tester_B/sonda_1a_kilitten_bagimsiz.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/tur2/sonda1a-v3-yeniden.txt
  - name: "O-B5 olcumu (offscreen): deleteLater + Python referansi -> C++ AnaPencere olu, sekme gorunur+yokluyor, hover panel acar, sag tik alicisiz; `destroyed.connect(sekme.deleteLater)` ile gider; del+gc / deleteLater+del / kapat+del yollarinda cokme yok"
    cmd: "python .agents/tasks/T-012/tester_B/olcum_ob5_zombi_ve_duzeltme.py ; python .agents/tasks/T-012/tester_B/olcum_ob5_duzeltme_uc_yol.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/tur2/olcum-ob5-zombi-ve-duzeltme.txt
  - name: "K5 balon sonrasi kapat(): gercek tepside Shell ikon 0.3 s icinde silinir, 10 s izlendi (balonlu/balonsuz) -- 'tepside kalinti yok' tutuyor"
    cmd: "python .agents/tasks/T-012/tester_B/olcum_k5_balon_sonrasi_ikon_kalintisi.py"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/tur2/olcum-k5-balon-sonrasi-ikon-kalintisi.txt
  - name: "mandal geometrisi: disk ici piksel anlik 392/5518 (sag 15 sutun), bolge 11/5518 (sag-ust kose 5x3), goster 0 -> mandal sinifi pratikte yalniz 'Anlık çeviri' sag ucundan; kapandi yikimda dis dinleyiciye 0; Esc sonrasi release QTest yolunda secildi 1"
    cmd: "python -m pytest .agents/tasks/T-012/tester_B/test_mercek_b_tur2.py -q -s -k 'test_h3_ or test_i3 or test_j1'"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/tur2/mandal-disk-ici-noktalar-ve-bilgi-satirlari.txt
  - name: "depo dokunulmadi: src/tests/demo/real_check/packet git status BOS, sha256, HEAD f94e012"
    cmd: "git status --short -- src tests demo .agents/tasks/T-012/real_check.py .agents/tasks/T-012/packet.md; sha256sum ..."
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/tur2/git-durumu.txt
  - name: "korluk: tests/unit/ui/test_*.py, evidence/**, delivery.md, sef_dogrulama/** yalniz kendi testlerim + sonda_1a/2a bittikten SONRA (00:43:15) test kalitesi / kapi denetimi icin acildi; tester_A* acilmadi"
    cmd: "date"
    exit_code: 0
    result: gecti
    evidence: tester_B_evidence/tur2/korluk-kaldirma-ani.txt
blocking_issues: []
---

# T-012 tur 2 -- Tester-B (mercek: kotu kullanim + istek/sartname uyumu + test kalitesi)

Karar: **ONAY**. Paket v3'un dort ▲▲ maddesi (K1 omur, K1 `kapandi`, K4 mandal, K5 balon) ve ust sinirlar kodda var, docstring iddialari olculdu ve tutuyor; sefin demo duzeltmeleri (Y-B1 Esc, O-B2 secimde sekme gizli) gercek cagiranla dogrulandi. Tur-1 bulgularimin tamami (O-B1, O-B3, D-B6, Y-B1, O-B2) ters cevrilmis testlerle KAPANDI. Bes taban komutu yesil; kapi yine **kilit** yuzunden kosulamadi (bu oturumda da LogonUI), kilitten bagimsiz her sey olculdu. Yeni bulgu: **1 orta** (O-B5: `deleteLater` + referans tutulunca zombi -- Y-A1 sinifinin ikinci yolu, 1 satir, dogrulandi), **6 dusuk**. Ret sebebi yok: urun yolu (`calistir`) O-B5'e ugramaz; sef isterse implementer'in bir sonraki dokunusuna eklenir.

Korluk: `delivery.md`, `evidence/`, `sef_dogrulama/`, `tests/unit/ui/test_*.py` 00:43:15'te (kendi testlerim + sondalar bittikten sonra) yalniz test kalitesi / kapi denetimi icin acildi; `tester_A*` hic acilmadi.

**Ortam:** tek monitor 2560x1440 @ %125 (mantiksal 2048x1104), oturum **kilitli** (on plan `LockApp.exe`); gercek fare girdisi olculemez. Kilitten bagimsiz olculer: gercek hwnd'ye `PostMessage`, `EnumWindows`, `Shell_NotifyIconGetRect`, `GetCapture`, `IsWindowVisible`.

## Tur-1 testlerim v3 koduna karsi (HAM: 8 dusen / 91 gecen -- hepsi sinifli, urun hatasi yok)

| test | sinif | ne yapildi |
|---|---|---|
| `x1`, `x2` (xfail strict) | **XPASS**: O-B1 duzeltildi | ters cevrildi: `sekme.close()` kenar -> (T,F,F) gorunur, tepsisizde de |
| `a5`, `c16`, `d5` | `ac()` yardimcim mandal-farkinda degildi (imlec ayni noktada kaliyordu) | yardimci: once disari (1 yoklama), sonra diske -- K4 ▲▲ kuralinin kendisi |
| `c7` | D-B6 duzeltildi (mandal) | ters: imlec diskte kalsa da `acilma+3*yoklama` sonra kapali |
| `c2x10` | O-B1 yan etkisi: `app.quit()` kenar durumunda artik kabugu **temiz** kapatiyor (cikis 1, (F,F,F)) | ters (D-B15, olumlu) |
| `f1` | Y-B1 + O-B2 duzeltildi | ters: Esc -> surec yasar, katman kapali, sekme geri, durum kenar |

## Sef duzeltmeleri denetimi (`demo/kabuk.py`, `demo/bolge_izle.py`)

- Esc uygulamayi kapatmiyor: `iptal` -> `close()`; gercek cagiranda (`calistir` + `_bagla`) exec donmuyor, `kapandi False`, `cikis 0` (`test_h5`, `test_f1`).
- Sekme secim boyunca gizli, yoklayici durmus (`KATMAN 1 UCLU False False YOKLUYOR False`); secim bitince (`secildi` de `iptal` de) geri geliyor ve yokluyor (`test_h5`, `test_j2`).
- Kenar degilken `sekme.show()` cagrilmiyor: gorunur durumdan `dugme_bolge` -> secim -> sekme gizli kaliyor, durum gorunur, yoklayici kapali (`test_j3`).
- `cikis_istendi` -> demo lambda katman/izleme pencerelerini kapatiyor; secim acikken tepsi "Cikis" -> katman kapanir, `iptal` yayilmaz, `bitti()` cagrilmaz, gorunur ust-duzey 0 (`test_j4`, `test_j2`).
- `bitti()` iki kez -> `sekme.show()` x2 idempotent, tek yoklayici (`test_j6`).
- `sekme.hide()` `kapandi` yaymaz -> demo akisinda surpriz yok (`test_j5`, `test_h2`).

## ▲▲ satir satir <-> kod (paket v3)

| ▲▲ madde | kod | olcum | uyum |
|---|---|---|---|
| K1 omur: `del`+gc -> sekme/tepsi/menu silinir, gorunur 0, yoklayici durur; lambda yok | bagli yontemler; `.emit` baglantilari; `connect` son satir | `test_i1` (weakref None x3, imlec sayaci artmaz), `test_i1b` pozitif kontrol (lambda widget canli kalir), `test_i6` AST (lambda + `functools` importu yok), `test_i7` AST (son ifade `availableGeometryChanged.connect`) | evet |
| K1 omur: `deleteLater` yolu | `p.deleteLater(); del p` -> silinir (`test_i2`) | **`deleteLater()` + referans tutulunca ZOMBI** (`test_i2b` xfail, sonda_2a S10 gercek ekran) | **O-B5** |
| K1 `kapandi`: dis `close()` yayar, `hide()` yaymaz; kenar -> `goster()` | `closeEvent` -> emit; `_sekme_kapandi` | `test_h1` (tepsili/tepsisiz, `cikis 0`, yeniden kenara al calisir), `test_h2`, gercek WM_CLOSE sekme hwnd'sine (S8: kapandi 1, ana hwnd gorunur, Shell ikon yok) | evet |
| K4 mandal: mod tiki sonrasi imlec diskten cikana kadar acilmaz | `_cikis_bekleniyor` | `test_h3[dugme_anlik]` (+`dugme_bolge` 11 px kose), `test_h3b` (surukleme kaldirmaz, hide/show sifirlar, sag tik koymaz), `test_c7` ters | evet |
| K5 balon: surec basina bir kez, literal argumanlar; ikinci ornek gostermez; tepsisiz tuketmez | `_balon_gosterildi: ClassVar` | `test_i5` (x3 -> 1; ikinci ornek 0), `test_i5b`, `test_i5c` (`showMessage` casusu; tepsisiz sessiz); S11 gercek tepsi; balon sonrasi `kapat()` -> Shell ikon 0.3 s'de silinir (10 s izlendi) | evet |
| ust sinirlar `ValueError` | 66/67, 2**31-1/2**31, yoklama 1/0 | `test_i4` (11 dal: sinir degeri kabul, otesi hata, Qt nesnesi yaratilmadan, mesajda sinir + "panel"), `test_i4b` (66'da panel kapali sekmeyi kapsar -> sinir keyfi degil) | evet |
| `PANEL_BOYUTU` yerinde degistirilmez (AST) | `Final` + bekci | `test_i6` (tek adim takma ad dahil) + pozitif kontrol | evet (bekci boslugu D-B13) |

**K5 "surec basina" tartismasi (istek uyumu):** olculdu -- ayni surecte ikinci `AnaPencere`, ayni ornekte ikinci `tepsiye_al()` balon gostermez. Istekle uyumlu: TEPSI durumundan geri donusun her yolu (ikona tik / cift tik / menu "Pencereyi göster") ikonu bulmayi gerektirir; kullanici ikinci kez tepsiye aldiginda ikonu zaten bulmustur, ipucu gereksizdir. Uretimde surec = tek `AnaPencere` (`calistir`), yani surec basina == oturum basina (Windows "tepsiye kucultuldu" adeti). Bosluk: gelecekteki global kisayol (HotkeyService) tepsi durumundan ikonu hic gormeden `goster()` cagirirsa ikinci kez ipucu yok -- ilk balon (~6 s) gorulmus sayilir, kabul. **Balona tik hicbir seye bagli degil** (D-B12): "Tepsi ikonuna tıklayınca pencere geri gelir" balonuna tiklayan kullanici pencereyi geri alamaz.

**Ust sinir tuzagi:** `yaricap=67` `ValueError("1 <= yaricap <= 66 olmali (panel sekmeyi kapsamali): 67")` -- gerekce mesajda ve modul docstring'inde; 66 = `PANEL_BOYUTU.height()//2` ve 66'da acik panel kapali sekmeyi tam kapsar (olculdu). Istek 24-28 px; cagiran icin tuzak degil. `_YARICAP_AZAMI` import aninda hesaplanir: `PANEL_BOYUTU` disaridan degistirilirse bayat -- zaten "tanimsiz", belge.

## Bulgular

### YUKSEK -- yok

### ORTA

**O-B5 (implementer) · `AnaPencere.deleteLater()` cagrilip Python referansi tutulunca (Qt'de yaygin desen: `self.pencere.deleteLater()`) C++ `AnaPencere` silinir ama `__dict__`teki `_sekme` yasar -> ZOMBI yarim daire: gorunur, yokluyor, hover panel acar, dugmeler alicisiz, sag tik alicisiz, tepsi ikonu YOK (Tepsi C++ cocugu gitti) -> geri yol yok.** Y-A1 sinifinin ikinci yolu. Paket K1 ▲▲ lafzi "`del`+gc **ya da `deleteLater`**" der; implementer'in `deleteLater` olcusu `p.deleteLater(); del p` yapiyor -> `del` yolundan AYRISMIYOR (kural 4/7: iki parametre ayni mekanizmayi olcuyor), sinif gorunmez. Olcum: offscreen `test_i2b` (xfail strict), `olcum_ob5_zombi_ve_duzeltme.py`; gercek ekran sonda_2a S10 (`EnumWindows`'ta sekme hwnd gorunur, C++ AnaPencere olu). **Duzeltme (1 satir, `AnaPencere.__init__` sonuna): `self.destroyed.connect(self._sekme.deleteLater)`** -- alici sekme (bagli yontem, `self` yakalanmaz); olculdu: deleteLater+ref yolunda sekme gider (offscreen + gercek ekran S10 duzeltme=True), `del`+gc / `deleteLater`+`del` / `kapat`+`del` yollarinda cokme yok (`olcum_ob5_duzeltme_uc_yol.py`). Test: `p.deleteLater()` **`del` OLMADAN** + `qtbot.wait(300)` -> `weakref(sekme)() is None`. Urun yolu (`calistir`, demo) bu yola ugramaz -> ret degil; sonraki cagiran (HotkeyService/ayarlar) icin tuzak.

### DUSUK

- **D-B10 (sef, demo)** `SecimKatmani.keyPressEvent(Esc)` `_basla`yi sifirlamiyor; Esc'ten SONRA gelen release `secildi` yayar -> iptal edilen secim izleme penceresi acar (`test_j1` xfail: QTest yolu ve dogrudan olay ikisi de 1). Gercek OS'te **ulasilmaz**: Qt basista `SetCapture` alir, `hide()` sonrasi `GetCapture()=0` (S9) -> release gizli katmana gitmez. Yine de 1 satir: Esc'te `self._basla = self._bitir = None`.
- **D-B11 (sef, demo, T-005 mirasi)** `IzlemePenceresi.close()` (X dugmesi) pencereyi gizler ama 100 ms yakalama zamanlayicisi calismaya devam eder (olculdu: `zamanlayici aktif=True`); `WA_DeleteOnClose` ya da `closeEvent`te `stop()`.
- **D-B12 (implementer, oneri)** `QSystemTrayIcon.messageClicked` bagli degil; `Tepsi._ikon.messageClicked -> goster_istendi` balonu isleve cevirir (`test_i5c` belge).
- **D-B13 (test kalitesi)** `_panel_boyutu_degistirmeleri` bekcisi takma adi gormez: `P = PANEL_BOYUTU; P.setWidth(1)` -> `[]`, `from ... import PANEL_BOYUTU as PB; PB.setWidth(1)` -> `[]` (olculdu). Benim `test_i6` tek adim takma adi yakalar, `import as`i o da yakalamaz. Disiplin bekcisi; urun etkisi yok.
- **D-B14 (belge)** `sekme.close()` Qt platform penceresini YIKAR (`QWindow::event(Close) -> destroy()`); yeniden `show()` yeni hwnd yaratir (S8 `hwnd degisti=True`). hwnd onbellekleyen cagiran (gelecek overlay/HotkeyService) icin not.
- **D-B15 (belge, olumlu)** `app.quit()` kenar durumunda: closeAllWindows -> sekme.close() -> `kapandi` -> `goster()` (ana pencere bir an gorunur+aktif) -> closeAllWindows onu da kapatir -> `kapat()` -> cikis 1, (F,F,F). Tur 1'de gizli ana pencere closeEvent almiyordu. Urun yolu degil; delivery de belgelemis.
- **D-B1, D-B8 (tur 1, degismedi)** dpr 1.25 birincil sag kenar +1 px (sonda_1a S7); kapi tepsi ikonuna tiklamiyor.
- **Bilgi** mandal sinifinin cografyasi: kapali disk ici piksel `dugme_anlik` 392/5518 (sagdaki 15 sutun, tum satirlar), `dugme_bolge` 11/5518 (sag-ust kose 5x3), `dugme_goster` 0. Sinif pratikte yalniz "Anlık çeviri" dugmesinin sag ucundan dogar; implementer'in `[dugme_bolge]` varyanti 11 px'lik koseden geciyor (gecerli ama marjinal). `kapandi` yikimda dis dinleyiciye ulasmaz (Qt `in_destructor` -> olay yok; `test_i3`: 0).

## Kapi (`real_check.py` v3) denetimi -- ayri baslik (kural 8/10)

- **[3] pozitif kontrol hala betikte yok** (tur-1 O-B4): sef kilit acilinca `k5b` deseniyle `sef_dogrulama/`'ya yazacak -- acik kalem.
- **[5c] sag tik**: uclu olculuyor, on plan olculmuyor (tur-1 notu, acik; benim sonda_1b S4c kilit bekliyor).
- **[6] WM_CLOSE yalniz gorunur durumdan**; tepsi/kenar gercek WM_CLOSE'u ben olctum (sonda_1a S5, v3'te temiz) -- [6d] onerisi acik.
- **[8] yalniz ikinci monitor**; dpr != 1 birincil olculmuyor (S7: +1 px) -- acik.
- **▲▲ kalemlerinin HICBIRI kapida degil:** `kapandi` (oneri **[6e]**: sekme hwnd'sine `PostMessage(WM_CLOSE)` -> (T,F,F), durum gorunur; S8 temiz), omur (kapi disi; implementer gercek-platform betigi var ama `deleteLater`-yalniz yolu yok -> O-B5), balon ([1a] balonu tetikler ama varligini/suresini olcmez; tur-1 [5c] `CoreWindow` olcumu vardi -- **[1c]** olarak geri alinabilir), mandal ([9] dugme MERKEZINDEN tiklar = disk disi -> mandal hic uyarilmaz; oneri **[9b]**: `dugme_anlik` sag ucuna (`x = right-3`) gercek tik + imleci orada tut -> `120+3*60` ms sonra `acik False`).
- **[5] surukleme yukari**: `max(0, ...)` `g.top()>0` iken de ust sinira kilitler (y_sinirla); ok. [0]/[4] literal; ok.
- **Sarici** kilit kontrolu hala yok (tur-1 notu); implementer kilidi elle tespit etmis (`real_check-tur2-KILIT.txt`).
- **Kilit acilinca sefe kalan gercek fare kalemleri (degismedi):** tepsi ikonuna gercek tik -> on plan; menu "Göster" -> on plan; balon gorunurlugu/suresi (~6 s) ve sekmeyle kesismemesi; [3]/[5]; `bekle_ve_kos.py` tur-1'den hazir.

## Test kalitesi (implementer 216 test, mutant 40/40 + 5 kontrol)

- **Omur testleri:** `[del_gc|deleteLater]` parametreleri ikisi de `del p` yapiyor -> `deleteLater` varyanti `del`den ayrismiyor (O-B5 gorunmez). Pozitif kontrol (lambda widget canli kalir) dogru ve benim `test_i1b` ile ayni sonucu veriyor. Gercek-platform omur betigi ayni desende (`del p` var).
- **Balon / sinif sayaci sifirlama duzeni:** `monkeypatch.setattr(AnaPencere, "_balon_gosterildi", False)` test basinda; test ici `tepsiye_al()` sinif ozniteligini yazar, monkeypatch teardown'da onceki degeri geri yukler -> testler arasi sizinti yok (birlikte kosum iki sirada temiz). Casus `showMessage` = Qt siniri (kural 7 uygun), pozitif kontrollu (kural 10). Duzen dogru.
- **Mandal:** `_disk_icinde_dugme_noktasi` dugme ∩ disk kesisiminden en derin nokta, on kosul assert'li; `dugme_bolge` icin 11 px kose (yukarida). `qtbot.wait(acilma+3*yoklama)` x2 + pozitif kontrol. Iyi.
- **Mutant C-4 (`availableGeometryChanged.connect` `_kapat()` oncesine):** `_kapat()` yukseltemez, arada baska ifade yok -> davranis-esdeger; kontrol olarak kacmasi **kabul edilebilir**. Yapisal bekci istenirse `test_i7` (AST: `__init__` son ifadesi bu `connect`). C-5 (`not self._kapandi` kaldirilmasi) de esdeger: `goster()` zaten bakar.
- **Totoloji:** bulunmadi. `test_k4_yaricap_ust_sinir_tam_degeri_kabul` referansi urun fonksiyonundan (`sekme_acik_dikdortgeni`) turetiyor (kural 8) ama `frameGeometry().size()==(66,132)` literali de var; kabul.
- **Bekci boslugu:** D-B13.
- **Kacan siniflar (benim testlerim kapatir):** `deleteLater`-yalniz (O-B5), gercek WM_CLOSE sekme hwnd'sine (S8), `app.quit()` kenar semantigi (`c2x10` ters), demo Esc/secim/cikis akislari (H5, J2-J4), Esc-sonrasi release (`j1`), `kapandi` yikimda (`i3`), hwnd yenilenmesi (S8), `GetCapture` (S9), balon sonrasi Shell kalintisi (10 s).

## Ozet

▲▲ maddeleri kodda ve olculmus; tur-1 bulgularimin tamami kapandi; sef demo duzeltmeleri gercek cagiranla dogru. Tek orta bulgu O-B5 (`deleteLater` + referans -> zombi; 1 satir, dogrulanmis), urun yoluna ugramiyor -> **ONAY**. Kapi kilit yuzunden yine kosulmadi; ▲▲ kalemlerinin kapiya eklenmesi ([6e], [9b], [1c]) ve [3] pozitif kontrolu sefe.
