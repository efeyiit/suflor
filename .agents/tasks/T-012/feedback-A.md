# T-012 tur 1 -- Tester-A geri bildirimi (mercek: durum makinesi + sinir + takma ad/omur)

Karar: **RET** -- tek bloklayici bulgu (Y-A1). Geri kalan her sey onay duzeyinde (verdict-A.md).

## Y-A1 · `KenarSekmesi` HIC toplanmiyor; kenar durumundaki `AnaPencere` dusurulunce ZOMBI sekme (docstring K1 ihlali)

**Iddia (garanti alani, `src/ui/kabuk.py` docstring K1):**
> Sekme EBEVEYNSIZ `Tool` penceredir (Python sahipligi: `AnaPencere` silinince silinir, KRT o6); `kapat()` onu acikca gizler.

**Olcum (offscreen; Python/PySide nesne omru, platformdan bagimsiz):** `tester_A_evidence/A-sonda-01-omur-zombi.txt`

```
  ok     [1] AnaPencere sarmalayicisi toplandi=True
  IHLAL  [1] sekme silindi=False; gorunur ust-duzey=['KenarSekmesi']
         [1] zombi: gorunur=True yokluyor=True sag tik sinyal=1 (alici pencere yok) -> geri donus yolu yok
  IHLAL  [2] deleteLater: AnaPencere toplandi=True sekme silindi=False gorunur=['KenarSekmesi']
  IHLAL  [3] tek basina KenarSekmesi son referans dusunce silindi=False gorunur=['KenarSekmesi']
  bilgi  [4] kapat()+dusurme: sekme yasiyor=True gorunur=False (gizli sizinti, zombi degil)
  ok     [5] pozitif kontrol: lambda baglantili canli kaldi=True, bagli yontemli canli kaldi=False
```

`AnaPencere` gercekten siliniyor (sarmalayici toplandi, C++ nesnesi Python sahipligiyle gitti; `deleteLater` yolunda da ayni), sekme silinmiyor: `weakref` canli, `isVisible()` True, `yokluyor` True, sag tik `pencereyi_goster` yayiyor ama alici pencere yok -> ekranda `StaysOnTop` bir yarim daire kalir, geri donus yolu yoktur (surec sonuna kadar). `kapat()` cagrilmissa sekme gizlidir ama nesne yine yasar (her ornek sizar; implementer takiminin 190 testi 190+ sekme sizdirir, gorunmez).

**Mekanizma (kod okumasiyla, pozitif kontrolle ayristirildi):** `src/ui/kenar_sekmesi.py` yapicisi, satir 222-224:

```python
self._dugme_anlik.clicked.connect(lambda: self._mod_tiki(self.anlik_cevir))
self._dugme_bolge.clicked.connect(lambda: self._mod_tiki(self.bolge_izle))
self._dugme_goster.clicked.connect(lambda: self._mod_tiki(self.pencereyi_goster))
```

Uc lambda `self`i kapatir; Qt baglantisi callable'i C++ tarafinda tutar (Python gc dongusu goremez) -> sekme sarmalayicisinin sayaci hic sifira inmez -> C++ `KenarSekmesi` hic silinmez. Pozitif kontrol [5]: ayni kalipta minimal `QWidget` -- `clicked.connect(lambda: self._tik())` olan toplanmaz ve gorunur kalir, `clicked.connect(self._tik)` olan toplanir (PySide bagli yontemi zayif tutar). Yani olcu ayrisir ve duzeltme uc satirdir.

Ikincil sonuc (D-A4): yapici `availableGeometryChanged.connect(self._ekran_degisti)` (satir 238) SONRASINDA `_kapat()` icinde tasarsa (`yaricap >= 2**30` -> `OverflowError`) yarim kurulu nesne ekran sinyaline kalici bagli kalir (ayni sizinti yuzunden) ve sonraki her ekran degisiminde yuvasi istisna atar -- olculdu, ayri surecte (`test_e_geometri_ust_sinir_overflow_ayri_surec_PIN`).

**Neden ret:** docstring'in acik ve olculmus-diye-yazilmis ("KRT o6") bir iddiasinin olculen ihlali; sonucu zombi ust-duzey pencere. KRT D6'nin olcumu prototip/minimal kopya uzerindeydi (lambda yoktu); urun kodu mekanizmayi degistirip olcumu yeniden yapmadan ayni cumleyi tasidi (PROTOKOL 4.6/3 sinifi). Urun yolu (`calistir` -> `app.quit` -> surec biter) ETKILENMEZ; belgelenen sahiplik modeline guvenen her tuketici etkilenir.

**Yeniden uretim:**
```
python .agents/tasks/T-012/tester_A/sonda_a_01_omur_zombi.py                        # rc=1, 3 IHLAL
python -m pytest .agents/tasks/T-012/tester_A -q -p no:cacheprovider --import-mode=importlib -k "DOCSTRING"   # 3 failed
```
Dusen testler: `test_d_omur_ana_pencere_referansi_dusunce_sekme_silinir_DOCSTRING`, `test_d_omur_delete_later_referans_birakilinca_sekme_silinir_DOCSTRING`, `test_d_omur_kenar_sekmesi_tek_basina_referans_dusunce_silinir_DOCSTRING`. Gecen pozitif kontrol: `test_d_omur_mekanizma_pozitif_kontrol_lambda_baglantisi_sarmalayiciyi_tutar`.

**Beklenen (duzeltme sonrasi):** ucu de yesil: son referans dusunce (`del` + `gc.collect()`, `deleteLater` + dongu) `weakref` None, gorunur ust-duzey listesine yeni eleman kalmaz; sonda `TEMIZ`. Onerilen duzeltme: uc lambdayi bagli yonteme cevir (`def _anlik_tiki(self): self._mod_tiki(self.anlik_cevir)` vb.; `functools.partial(self._mod_tiki, ...)` da bagli yontemi guclu tutar, KULLANMA) ve docstring cumlesini olcen testin adini yaz (`weakref` + `gc.collect` + gorunur ust-duzey). `hideEvent`/`kapat()` degismez. Isteğe bagli: yapicida `availableGeometryChanged.connect`i `_kapat()`tan SONRAYA al (D-A4 yarim kurulu nesne).

## Bloklamayan bulgular (ret gerekcesi DEGIL; verdict-A.md'de ayrintili)

- **O-A1** mod tikinda imlec kapali diskin icinde kaliyorsa (dugmenin sag ~26 px'i) panel `acilma_ms` sonra YENIDEN acilir -- ertelenmis Snapshot karesine girer; "once kapanir sonra sinyal" iddiasi sinyal aninda tutuyor. Oneri: tik sonrasi imlec diskten bir kez cikana kadar acilma sayacini kilitle.
- **D-A1** `goster()` kucultulmus (Win+D sinifi) pencereyi geri getirmez (`isMinimized` True kalir); `showNormal()` gerekir.
- **D-A3** `yaricap > 66` kabul -> panel sekmeyi kapsamaz -> salinim; dogrulamaya `2*yaricap <= PANEL_BOYUTU.height()`.
- **D-A2/D-A4/D-A5/D-A6/D-A7/D-A8** bilgi/pin (taban sinif `hide()/show()`, ust sinir OverflowError, `PANEL_BOYUTU` mutable, `yoklama_ms=1` kaba sayac, `imlec_konumu` istisnasi, panel > ekran).
