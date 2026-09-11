# T-008 · feedback-A (tur 1 → tur 2) · Tester-A, mercek A

Tek bloke edici sınıf. Düzeltme ajanının elinde bu dosyadan başka bağlam yok; her şey burada.

## B1 · Uzun kutu köprüsü gerçek OCR'da satırları bozuyor

**Ne oluyor.** Solda iki satırı dikey kaplayan büyük bir etiket (2× font, dikey ortalı) ve sağında iki KR satırı. Gerçek tespitçi 11 kutu verir: etiket + 5 + 5. Etiket kutusunun `y`'si en küçük olduğu için `(y,x)` sırasında **satırın ilk bloğu** olur; adım 3 (`_satirlara_bol`: "satırın İLK bloğuyla dikey örtüşme ≥ 0.5×min(h)") iki satırın 10 kelimesini de bu etiketle örtüştüğü için **tek satıra** toplar; adım 4 `(x,y)` sıralaması iki satırın kelimelerini x'e göre karıştırır. Sonuç fixture'a göre:

| Fixture (`tester_A/fixtures/`) | Etiket kutusu | Sonuç (şu an) | Etiketsiz aynı görüntü |
|---|---|---|---|
| `kr_etiket_ortali_60_45_10.png` | (57,55,125,72) | **11 → 1 blok**, 11 parça; parçaların satırları `[0,1,0,0,1,0,1,0,1,1,0]` — iki cümlenin kelimeleri karışık tek metin | 10 → 2 `[5,5]` |
| `kr_etiket_ortali_72_48_14.png` | (57,56,149,81) | **11 → 9 blok** `[2,1,1,1,1,2,1,1,1]` — satırlar parçalandı (kelime-kelime çeviri, S3) | 10 → 2 `[5,5]` |
| `kr_etiket_ortali_60_40_8.png` | (59,62,121,67) | **11 → 10 blok** | 10 → 2 `[5,5]` |

Ham çıktı: `tester_A_evidence/a6-gercek-ocr.txt` bölüm `[4b]` (gerçek motor, ayrı süreç). Üst hizalı etiket (bölüm `[4]`, 4 varyant) 3/4'te kurtuluyor çünkü büyük fontun iç boşluğu etiket kutusunun üstünü satır 0'ın üstünden 2–6 px aşağı itiyor → etiket ilk blok olmuyor. Dikey ortalı etikette bu **hiç** olmuyor.

### Yeniden üretim (OCR gerekmez, gerçek geometri gömülü)

```
python -m pytest .agents/tasks/T-008/tester_A/test_ret_a_uzun_kutu_koprusu.py -q -p no:cacheprovider
```

Ham hata (`tester_A_evidence/testerA-ret-uzun-kutu-pytest.txt`):

```
FAILED ...::test_ret_buyuk_etiket_solda_satirlar_bozulmamali[kr_etiket_ortali_60_45_10]
  AssertionError: kr_etiket_ortali_60_45_10: iki satır aynı blokta {0: [0], 1: [0]}; blok parça sayıları [11]
FAILED ...::test_ret_buyuk_etiket_solda_satirlar_bozulmamali[kr_etiket_ortali_72_48_14]
  AssertionError: kr_etiket_ortali_72_48_14: satır -> bloklar {0: [0, 1, 2, 3, 4], 1: [5, 6, 7, 8]}; toplam 9 blok ... (satırlar parçalandı)
FAILED ...::test_ret_buyuk_etiket_solda_satirlar_bozulmamali[kr_etiket_ortali_60_40_8]
  AssertionError: kr_etiket_ortali_60_40_8: satır -> bloklar {0: [1, 2, 3, 4, 5], 1: [6, 7, 8, 9]}; toplam 10 blok ...
3 failed, 3 passed
```

Geçen 3 test etiketsiz varyantlardır (pozitif kontrol: ölçü ateşliyor, geometri doğru).

Gerçek motorla tekrar (isteğe bağlı, ~60 s):

```
python -X utf8 .agents/tasks/T-008/tester_A/a6_gercek_ocr.py
```

### Ne bekleniyor — ayırt etme ölçüsü

Düzeltme şu **dördünü birlikte** sağlamalı (dördü de mevcut dosyalarla ölçülür):

1. `test_ret_a_uzun_kutu_koprusu.py` **6/6 geçer**: her çizilen satırın 5 kelime kutusu TAM OLARAK BİR çıktı bloğunda **ve** hiçbir çıktı bloğu iki satırdan kelime kutusu içermez. Etiketin kendi bloğu serbest (ayrı ya da satır 0'a yapışık — ikisi de kabul).
2. `tests/unit/ocr/test_satir_birlestirici.py` **68/68** (özellikle `test_k2_satir_bolumleme_satirin_ilk_bloguna_gore` merdiven ve `test_k2_grup_icinde_dikey_ortusme_grubun_ilk_bloguyla` `a T | c` bozulmasın).
3. `python .agents/tasks/T-008/real_check.py` **TEMİZ** (KR 17→4 `[2,5,5,5]`, 1-em 4→4, menü, JP/EN no-op).
4. `python -X utf8 .agents/tasks/T-008/tester_A/a6_gercek_ocr.py` **exit 0** (`TESTER_A_KOK` vermeden; depo `src/` ile).

`tester_A/test_mercek_a.py` içindeki `test_a1_uzun_kutu_koprusu_T_solda_iki_satiri_tek_bloga_alir_SINIF` ve `test_a1_uzun_kutu_solda_iki_kelimelik_satirlari_parcalar_SINIF` **mevcut bozuk davranışı** sabitler; düzeltmeyle düşmeleri **beklenir** (§4.6/5 — ben tur 2'de yeniden yazarım). Onları geçirmeye çalışma.

### Ölçülmüş aday yönler (mekanizma senin; bunlar bağlayıcı değil)

Ayna ağacında (depo `src/` dokunulmadı) iki prototip: `tester_A_evidence/aday-duzeltme-prototipleri.txt` (diff'ler + sonuçlar).

- **E — satır referansı = satırın EN KISA bloğu (bağ: ilk).** `_satirlara_bol` içinde referans, satıra katılan her blokla `h` küçükse güncellenir. Sonuç: implementer 68/68 · ret dosyası 6/6 · gerçek OCR `a6` **exit 0** (`tester_A_evidence/a6-aday-E-gercek-ocr.txt`: etiketli 60_45_10 → 2 blok `[6,5]`, 72_48_14 → 2 `[6,5]`, 60_40_8 → 3 `[1,5,5]`; dlg_KR `[2,5,5,5]`, 1-em 4→4, diğer 17 fixture taban). Neden işliyor: satır 0'ın ilk kelimesi etikete katılır katılmaz referans olur; satır 1 onunla örtüşmez. Dikkat edilecek: kısa noktalama kutusu (h≈12) satırın **altında** dursa ve satır aralığı çok darsa referans olur — bu turda ölçmedim; docstring'e sınır olarak yazılır ya da referans "en kısa" yerine "en kısa, ama `h ≥ 0.5×medyan`" gibi sınırlanır.
- **D — `h > 1.5×yüzey medyanı` olan kutu yalnız geçer.** Ret dosyası 6/6 ama implementer'ın `a T | c` fixture'ı (T yalnız kalır) ve `min(h)` küçük-kutu sınırı (2 kutulu yüzeyde medyan anlamsız) bozulur. Tek başına önermiyorum.
- **Çakışma sınırı (KRT O2, `bosluk ≥ −0.5×min(w)`) tek başına YETMEZ:** 60_45_10'da satır 1'in kelimesi satır 0'ın kelimesine −147 px boşlukla katılıyor; sınır konsa katılmaz ama satır 1'in kelimeleri ayrı ayrı yeni grup açar (grup-ilk bloğu satır 0'dan olduğu için) → parçalanma (72_48_14 sınıfı). Kök satır bölümlemesinde, gruplamada değil.

### Docstring

K2 "Grup içinde dikey referans" paragrafındaki `[ÖLÇÜLMÜYOR] gerçek OCR'da (fixture yok)` cümlesi kalkar; yerine ölçülen sınıf ve seçilen kural yazılır (fixture: `tester_A/fixtures/kr_etiket_ortali_*.png`, ölçü: `test_ret_a_uzun_kutu_koprusu.py`). Seçilen kuralın kendi sınırı (E için kısa alt kutu; D için medyan) `[ÖLÇÜLMÜYOR]` damgasıyla ve gerekçesiyle yazılır.

## Ret dışı (karara yükümlülük; bu turda dokunmak zorunlu değil)

- K6 docstring: "`(y,x)` bağı olmayan girdide her permütasyon aynı" → bağ **çıktı** anahtarında da doğabilir (`C(0,0,10,30) A(0,10,10,20) B(20,0,10,20)`: `[C, A B]` / `[A B, C]`); cümle "iki çıktı bloğunun `(y,x)`'i eşitse girdi sırasına bağlı" olmalı. Ölçü: `test_mercek_a.py::test_a5_*POZITIF_KONTROL`. Ürün etkisi yok.
