---
task: T-004
role: implementer
round: 6
status: tamamlandi
files_written:
  - src/ocr/normalizer.py
  - tests/unit/ocr/test_normalizer.py
commands:
  - cmd: "python -m mypy --strict src/ocr/normalizer.py src/ocr/presets.py"
    exit_code: 0
    evidence: evidence/mypy-r6.txt
  - cmd: "python -m pytest tests/unit/ocr/test_normalizer.py -q"
    exit_code: 0
    evidence: evidence/pytest-r6.txt
  - cmd: "python .agents/tasks/T-004/purity_check.py"
    exit_code: 0
    evidence: evidence/purity-r6.txt
  - cmd: "python .agents/tasks/T-004/olcu_kiti.py"
    exit_code: 0
    evidence: evidence/kit-r6.txt
  - cmd: "python -m pytest tests -q"
    exit_code: 0
    evidence: evidence/pytest-regresyon-r6.txt
  - cmd: "python -m pytest tests/unit/ocr/test_normalizer.py -q  (KIRMIZI FAZ -- K28 uygulanmadan once)"
    exit_code: 1
    evidence: evidence/pytest-red-r6.txt
  - cmd: "python .agents/tasks/T-004/evidence/k28_once_sonra.py  (K28 oncesi/sonrasi ayrisma olcumu)"
    exit_code: 0
    evidence: evidence/k28-ayrisma-once-sonra-r6.txt
  - cmd: "python -m pytest tests/unit/ocr/test_normalizer.py -q -k k14_normalizasyon_butcesi  (K14 butcesi, PROTOKOL S6/5)"
    exit_code: 0
    evidence: evidence/budget-r6.txt
contract_change_request: false
known_gaps:
  - "K28-KOK (ZORUNLU, sef_karari-tur6.md): R5-1'in KOKU adim 3'tur (`_merge_hyphenated`, K5) ve K28 yalnizca SEMPTOMU kapatir. Adim 3 SALT TIPOGRAFIKTIR: tire satirin son karakteriyse ve sonraki satir kucuk harfle basliyorsa iki oge, ARALARINDAKI GEOMETRIK MESAFEYE BAKILMAKSIZIN birlesir -- hicbir geometrik kontrol yapilmaz. Bu yuzden adim 3 COK BLOKLU `_Item`'lar uretir ve o `_Item`'in bbox'i BIRLESIK kutudur. Kok BILINCLI olarak ACIK BIRAKILMISTIR (sefin karari): adim 3 salt tipografiktir ve OYLE KALIR. Birlesik oge geometrisi adim 5'in MIRAS kararina artik HIC girmez (sorgu aninda `_raw_query_pair` onun yerine ozgun bloklari koyar), BOLUMLEME kararina ise birlesik bbox ile GIRER (K10/K11). Docstring'de: `_merge_hyphenated` (K28-KOK bolumu) ve modul ust docstring'i '## K28' -> 'KOK, ACIK BIRAKILDI'."
  - "K30 (ZORUNLU, K2 x K19/K21 KOSULLU ETKILESIMI): adim 1'de dusen esik-alti bir blok, adim 5'te geride GERCEK bir GEOMETRIK BOSLUK birakir. Modul docstring'inin K2 bolumundeki 'o blok hic var olmamis gibi calisir' ifadesi METIN/HYPHEN icin dogrudur, GEOMETRI icin DEGIL. Bu ARTIK bosluk `max_vertical_gap_ratio * min(h)` esigini ASARSA sinir artik yalniz-uzunluk siniri degildir ve K21 uyarinca miras UYGULANMAZ; ASMAZSA miras KORUNUR. Ikisi de K2 sirasinin BILINCLI sonucudur ve sonuc ARTIK BOSLUGUN BUYUKLUGUNE baglidir. Docstring'de: `_group` (K30 bolumu) + modul ust docstring'inin K2 bolumune eklenen kosullu cumle. Testler: `test_k30_artik_bosluk_esigi_asmazsa_miras_korunur` (ikinci yol -- karar bunu implementer'a verdi) ve `test_k30_artik_bosluk_esigi_asarsa_miras_yok` (ilk yol -- Tester-B'nin `test_r3_k2_*`'siyle ayni sinif; kendi dosyamda da sabitledim, bkz. 'Belgenin sessiz kaldigi yerler' 8)."
  - "K31 (ZORUNLU, BITISIK IKI REPLIK -- IKI ALT DURUM): K15 uyarinca geometrik olarak bitisik iki replik, IKINCI BLOGUN KONUSMACISI BIRINCIYLE AYNI ya da `None` ISE tek segmentte birlesir; ikinci blogun ETIKET TASIMASI utterance siniri SAYILMAZ (K15'in bilincli siniri). Iki FARKLI TANINAN ad BIRLESMEZ (`['Ada: merhaba','Bora: nasilsin']` -> iki ayri segment). (a) Ikinci etiket K9'a gore TANINIYORSA ve ad AYNIYSA etiket metinden DUSER, segment tek `speaker` tasir: `['Ada: merhaba','Ada: nasilsin']` -> `'merhaba nasilsin'`, `speaker='Ada'`. (b) Ikinci etiket K9'un AD SUZGECINDEN gecemiyorsa (rakam iceren ad, K32'deki NFD adlar) o blok `speaker=None` kalir, K15'in `X/None` satiriyla bloklar YINE birlesir, ETIKET METNIN ICINDE KALIR ve segment ILK konusmaciya atfedilir: `['Ada: merhaba','Ada2: nasilsin']` -> `'merhaba Ada2: nasilsin'`, `speaker='Ada'`. (b) urun etkisi olarak (a)'dan KOTUDUR; IKISI DE BILINCLI SINIRDIR, sef tur 6'da davranisi degistirmiyor. Docstring'de: `_group` (K31 bolumu). Testler: `test_k31a_ikinci_etiket_taniniyorsa_duser_tek_segment_kalir`, `test_k31b_taninmayan_ikinci_etiket_metinde_kalir`, `test_k31_iki_farkli_taninan_ad_birlesmez`."
  - "K32 (ZORUNLU, GIRDI NFC VARSAYIMI -- MODUL DUZEYINDE): `normalize` girdinin NFC oldugunu VARSAYAR. Ad suzgeci codepoint bazli `isalpha()`'dir; NFD adlar (birlesik aksan) konusmaci SAYILMAZ, etiket metinde kalir (K31/b yolu). Varsayim SUZGECLE SINIRLI DEGILDIR: `max_group_chars` (K11) ve `_MAX_SPEAKER_NAME_LEN` (K9) CODEPOINT SAYAR, dolayisiyla ayni GORUNEN metin NFD gelirse BOLUMLEME DE DEGISIR -- olctum: blok basina 90 codepoint'lik aksanli govde, uc blok, NFC'de 1 segment / NFD'de 3 segment (NFD'de blok basina 180 codepoint). Yalniz etiket aksanliysa segment sayisi degismez (1/1) ama `speaker` 'Maria' (aksanli) -> `None`'a duser ve etiket metinde kalir. Ayrac kumesi (`:` / fullwidth, K17) etkilenmez. Davranis tur 6'da DEGISTIRILMEDI (K9/K11'in sozluksel kurallarina dokunmak yeni bir kapi turudur); NFC normalizasyonu T-006 CIKIS SOZLESMESINE adaydir. Docstring'de UC yerde (karardaki 'aynı kapsamla' sarti): modul UST docstring'i '## K32', `_split_speaker_label` (K32 bolumu) ve `normalize`'in docstring'indeki ozet. Testler: `test_k32_nfd_govde_bolumlemeyi_degistirir`, `test_k32_nfd_yalniz_etiket_segment_sayisini_degistirmez_ama_speakeri_dusurur`."
  - "`_group`'un `blocks=()` VARSAYILANI GECIKMELI PATLAMA uretir (BILINCLI, karara yazili): `blocks` gecirilmeden yapilan DOGRUDAN `_group(...)` cagrilarinda, `reason == 'length' and nxt.speaker is None` sinirina varilirsa `_raw_query_pair` `IndexError` yukseltir. Varsayilan YALNIZCA `items` bosken (`_group([], params)` -- Tester-C'nin dogrudan cagrisi, olctum: calisiyor) ya da uzunluk-tek sinir DOGMAYAN cagrilar icin gecerlidir. Sessiz yanlis uretmez ama patlama GECIKMELIDIR. `_normalize_impl` her zaman `blocks=blocks` gecirir; urun yolunda bu durum DOGMAZ."
  - "Kabul edilmis eski sinirlar (tur 1-5'ten degismedi): (i) K5 hyphen kurali YALNIZCA ASCII `-` (U+002D) icin tanimlidir; `‐` U+2010 / en-dash / em-dash KAPSAM DISIDIR (bilincli daraltma, docstring'de). (ii) `_collapse_intraline` `\\n` ICERMEYEN metinlerin de bas/son bosluklarini kirpar (docstring'de belgelendi). (iii) S8.3 A3'un 'altin goruntu seti' kriteri bu gorevin KAPSAMI DISINDADIR (altin set A9'un dizinine bagli, OCR motoru yok); fixture'lar test dosyasinda elle kurulur. (iv) `presets.py` bu turda YALNIZ normalizasyon parametreleri icerir; S3.2'nin olcekleme faktoru / kontrast on islemesi alanlari sonraki goreve birakildi (yapi on ayar basina tek dataclass ile bu genislemeyi kaldirir)."
  - "K28 KAPI ALETLERINI BAYATLATTI (karar S4.6/5 listesi -- benim duzeltmem DEGIL, A/B yeniden nisanliyor): `tester_B/test_karar_uyumu_tur5.py:567` (`args[0] == 'tail'` AST beklentisi), ayni dosyadaki `test_r5_k23_normalize_impl_bayragi_yalniz_group_cagrisina_iletir` (`_group` cagrisi artik `blocks=` de tasiyor), `tester_B/test_k23_mutant_sondasi_tur5.py`'deki M1/M2/M3 mutasyon desenleri ve `test_r5_mutant_m2_k21_ayrimini_da_bozuyor`; ayrica `blocks=` gecirmeyen DOGRUDAN `_group` cagrilari (sefin olcumu: kor takimda 96 kirik, 90'i `IndexError`). `tester_A/test_r5_partition_invariant.py:401` kirilmaz ama SESSIZCE bayatlar (kendi yerel `_group_tur4` kopyasini olcuyor). Bunlarin hicbirine DOKUNMADIM -- benim sahipligimde degiller."
  - "Kitin BILINEN SINIRLARI degismedi ve benim tarafimdan KAPATILMADI (karardaki tablo, M11-M15): `adim1_4` bagimsiz degil (denetlenen modulun kendi yardimcilarini cagirir), `n23` sinifi (gorunum gecisi ters yon) kit tarafindan OLCULMUYOR, MENU on ayari ve `apply_inheritance=False` yolu kitte kosulmuyor, bes girdi sinifi (emoji/astral, `monitor_index != 0`, `dpi_scale != 1.0`, >=40 bloklu girdi, ASCII-disi konusmaci adi) kite gorunmez, sorgudaki `params` kimligi kaydedilmiyor. Bunlar Tester-B/C yukumlulugudur."
---

# T-004 · Tur 6 teslimi — K28 (kod) + K29/K30/K31/K32 (belgeleme + test)

Karar: `.agents/tasks/T-004/sef_karari-tur6.md` (sürüm 8). Kararın "Tur 6 —
implementer'a giden liste" tablosundaki beş kalem de uygulandı. **Kararı
yeniden yorumlamadım**; uygulama biçimi kararda sabitlenmişti ve birebir o
biçimde yazıldı.

## Ne değişti

### K28 — **kod** (tek davranış değişikliği)

`src/ocr/normalizer.py`:

1. **Yeni modül düzeyi yardımcı** `_raw_query_pair(tail, nxt, blocks) ->
   tuple[_Item, _Item]`. Her iki tarafın kaynak indekslerini **okuma sırası
   anahtarıyla** (`(bbox.y, bbox.x, girdi indeksi)` artan) sıralar ve
   `replace(tail, bbox=blocks[son].bbox)`, `replace(nxt, bbox=blocks[ilk].bbox)`
   döndürür. İkame **yalnız `bbox`**'a dokunur; `speaker`, `text` **ve
   `source_blocks`** aynen korunur (ölçünün önkoşulu — kanca yalnız
   `(a, b, params)` görür).
2. **`_group` imzası** `_group(items, params, *, blocks: Sequence[TextBlock] = (),
   apply_inheritance: bool = True)`. `blocks` **keyword-only ve varsayılanlı** —
   `tester_C`'nin `_group([], params)` doğrudan çağrısı kırılmaz (ölçtüm: `[]`
   dönüyor).
3. **Miras sorgusu** artık
   `_group_rejection_reason(*_raw_query_pair(tail, nxt, blocks), params, ignore_length=True)`.
   Bölümleme döngüsünde **hiçbir `replace(...)` yazılmadı** (AST ile doğruladım:
   döngü içinde 0 çağrı; `_group`'taki tek `replace` görünüm geçişinde, tur
   5'ten beri orada duran satır).
4. **`_normalize_impl`** `_group`'u `blocks=blocks` ile çağırıyor (özgün liste,
   adım 1'de elenen bloklar dahil).

**Değişmeyenler** (doğruladım): `_Item` alanları, `normalize` imzası **ve
gövdesi** (`return _normalize_impl(blocks, preset)` — `apply_inheritance=True`
maddesi geri çekilmişti), `_should_group` imzası ve tek satırlık devretme
deseni, `_group_rejection_reason` imzası ve gövdesi, `__all__`.

### K29 — iki bayat test adı düzeltildi

| Yer | Eski (hayalî) | Yeni (gerçek) |
|---|---|---|
| modül docstring K2 bölümü | `test_k2_esik_alti_blok_ortada` | `test_k2_esik_alti_orta_blok_komsulari_birlestirir` |
| modül docstring K26 bölümü | `test_k26_alti_karakterin_hepsi_uyumluluk_formu_ve_etiket_dagilimi_dogru` | `test_k26_alti_karakterin_hepsi_uyumluluk_formu_ve_etiket_dogru` |

`purity_check.py` turun başında bu ikisini raporluyordu (exit 1); şimdi **exit
0**. Çıplak `_` sonlu önek atfı yok. Yeni yazdığım docstring'lerde anılan
**bütün** `test_*` adları test dosyasında gerçekten tanımlı (kapı doğruluyor).

### K30 / K31 / K32 — belgeleme + test

Kararın istediği cümleler **iki yere** yazıldı: ilgili docstring'e (tester
yalnız burayı görür) **ve** yukarıdaki `known_gaps`'e.

| Karar | Docstring yeri | Test |
|---|---|---|
| K28-kök | `_merge_hyphenated` + modül `## K28` | — (ölçü 1/2 dolaylı) |
| K30 | `_group` (K30 bölümü) + modül K2 bölümü | 2 test |
| K31 (a)/(b) | `_group` (K31 bölümü) | 3 test |
| K32 | modül `## K32` + `_split_speaker_label` + `normalize` özeti | 2 test |

## Sekiz zorunlu ölçü

Hepsi `tests/unit/ocr/test_normalizer.py` içinde, `# --- TUR 6 ---` başlığı
altında. Ölçüler **şefe ait `olcu_kiti.py`'den içe aktarıldı, yeniden
yazılmadı** (`olcu3_fixture`, `OLCU3_BEKLENEN`, `olcu3b_fixture`,
`OLCU3B_BEKLENEN`, `olcu5_fixture`, `olcu6_kos`, `sorgu_kaydi`, `derlem`,
`ON_AYARLAR`).

| # | Test | Ne ölçüyor |
|---|---|---|
| 1 | `test_k28_olcu1_sol_taraf_birlesik_kuyruk_gercek_kopusu_gizlemez` (3 varyant) | sol taraf ham son blok; A non-monotonik, B/C monotonik |
| 2 | `test_k28_olcu2_sag_taraf_birlesik_aday_gercek_kopusu_gizlemez` (3 varyant) | sağ taraf ham ilk blok; A2 = **K16 regresyonu** (`h == 0` gizleniyordu) |
| 3 | `test_k28_olcu3_sirasiz_girdi_cift_bloklu_kuyruk` (dialogue + tooltip) | sırasız girdi, çift bloklu kuyruk; iki ön ayar |
| 3b | `test_k28_olcu3b_zincirleme_hyphen_uc_bloklu_kuyruk_sorgu_cifti` | üç bloklu kuyruk; **çıktıyı değil sorgu çiftini** assert eder |
| 4 | `test_k28_olcu4_ham_geometri_mirasi_acar_birlesik_kutu_kapatir` | ters yön: ham geometri mirası **açar** |
| 5 | `test_k28_olcu5_yapisal_sorguyu_ham_bloklar_belirler` + `..._ast_normalize_impl_group_cagrisina_blocks_adini_gecirir` | üç mutasyon koşumu + AST yarısı |
| 6 | `test_k28_olcu6_makine_denetimi` (3 ön ayar) | `olcu6_kos(preset).temiz` |
| 7 | `test_k28_olcu7_k23_bolumleme_degismezi_kit_derleminde` (3 ön ayar) | K23 korunuyor |
| 8 | `test_k28_olcu8_zincirleme_miras_uc_segmentte_korunur` | `['Ada','Ada','Ada']` |

## Ölçüm — K28 öncesi/sonrası (`evidence/k28-ayrisma-once-sonra-r6.txt`)

```
=== ONCE  (K28 uygulanmamis: _raw_query_pair -> (tail, nxt) kimligi) ===
  DIALOGUE  ayrisma= 3677 ... temiz=False
  TOOLTIP   ayrisma= 6119 ... temiz=False
  SUBTITLE  ayrisma= 7249 ... temiz=False
=== SONRA (K28 uygulanmis, teslim edilen kod) ===
  DIALOGUE  ayrisma=    0 kimlik=0 kapsam_ihlali=0 sira=0 sayi=0 patlama=0 temiz=True
  TOOLTIP   ayrisma=    0 kimlik=0 kapsam_ihlali=0 sira=0 sayi=0 patlama=0 temiz=True
  SUBTITLE  ayrisma=    0 kimlik=0 kapsam_ihlali=0 sira=0 sayi=0 patlama=0 temiz=True
```

"ÖNCE" ölçümü kaynak dosyayı değiştirmez: `_raw_query_pair` çalışma anında
kimlik fonksiyonuna indirgenir, ki bu K28 öncesi çağrının (`_group_rejection_
reason(tail, nxt, params, ignore_length=True)`) **birebir** aynısıdır. Betik
`evidence/k28_once_sonra.py` altında, yeniden koşulabilir. Sayılar kararın
bildirdiği 3677/6119/7249 ile birebir aynı.

## TDD — kırmızı faz

`evidence/pytest-red-r6.txt` (exit 1): yeni testler yazıldı, `normalizer.py`'ye
dokunulmadan koşuldu → **15 failed, 109 passed**. Düşenler: ölçü 1 (×3), ölçü 2
(×3), ölçü 3 (×2), ölçü 3b, ölçü 4, ölçü 5 (×2), ölçü 6 (×3). Ölçü 7, ölçü 8 ve
K30/K31/K32 testleri kırmızı fazda da **yeşildi** — beklenen: K23 zaten
sağlanıyordu ve K30/K31/K32 davranışı **değiştirmeyen**, mevcut davranışı
**belgeleyen** kararlardır (kararın kendi ifadesi: "salt dokümantasyon").

## Regresyon

`python -m pytest tests -q` → **821 passed** (taban 795 + 26 yeni test), düşen
yok. `evidence/pytest-regresyon-r6.txt`.

## Belgenin sessiz kaldığı yerler — verdiğim kararlar

1. **Ölçü 1/2/4'ün fixture geometrileri.** Karar varyantları tarif ediyordu
   (`tail h=50 birleşik / ham son satır h=18` vb.) ama somut blok listesi
   vermiyordu. Fixture'ları kendim kurdum ve **her varyantta hem çıktıyı hem
   sorgu çiftini hem de reddin sebep kodunu** (`gap`/`overlap`/`height`)
   assert ettim — böylece "yanlışlıkla doğru sonuç" ihtimali kapanıyor.
   Ölçü 2'nin bölümlemesi kararda pinlenen `[((0,1),'Ada'), ((2,3),None)]`
   biçiminde çıktı.
2. **Ölçü 5'in üçüncü koşumu.** "Birleşik `bbox` bozulduğunda değişmemeli"
   maddesini şöyle uyguladım: `olcu5_fixture`'ın kuyruğu `(0, 2)`; okuma
   sırası `[2, 0]`, yani **okuma-sırası-son = idx0**. idx2'yi bozmak birleşik
   kutuyu değiştirir ama ham-son bloğu değiştirmez → sorgu çifti **değişmemeli**.
   Ayırt edici yarı budur; K28 öncesi bu koşum da değişiyordu (kırmızı fazda
   düştü).
3. **Ölçü 5'in (ii) koşumu zayıf kalıyor:** `olcu5_fixture`'ın **sağ tarafları
   tek bloklu** (boundary 1 → `(3,)`, boundary 2 → `(6,)`), dolayısıyla idx3
   mutasyonu "ham ilk blok mu, birleşik kutu mu" ayrımını **yapmaz** (ikisi
   aynı şey). Sağ tarafın ayırt edici ölçüsü **ölçü 2**'dedir (çok bloklu
   aday). Kararın istediği "değişmeli" şartı sağlanıyor; sınırı burada
   bildiriyorum.
4. **Ölçü 7'nin derlemi.** Karar "üç ön ayarda ayrı ayrı" diyordu ama derlem
   belirtmiyordu. Kitin `derlem()`'ini (2500 girdi) kullandım — zincirleme
   hyphen, eşik-altı bloklar, shuffle, ASCII-dışı, yozlaşmış/negatif geometri,
   büyük girdi, iki konuşmacı hepsi içinde. `len(girdiler) >= 2000` ayrıca
   assert ediliyor (totolojik koşum olamaz).
5. **`_raw_query_pair`'in içindeki `reading_order` iç fonksiyonu.** Karar
   "modül düzeyinde yardımcı: `_raw_query_pair`" diyor ve "`_group` imzası
   dışında imza değişikliği yok". Okuma sırası anahtarını **ikinci bir modül
   düzeyi ada** çıkarmadım; `_raw_query_pair` içinde iç fonksiyon olarak
   duruyor, böylece yeni bir genel ad açılmıyor.
6. **`sorted(...)[-1]` / `[0]` biçimi.** `max`/`min` ile davranışsal olarak
   eşdeğer (anahtarın üçüncü bileşeni benzersiz), ama kararın ve kitin
   `okuma_sirasi(...)` ifadesine **birebir** karşılık gelsin diye `sorted`
   yazdım — Tester-B'nin M26 off-by-one mutantı (`[-1]` → `[min(1, len-1)]`)
   bu biçimde nişanlanabilir.
7. **Test dosyasına dört yeni import** eklendi: `ast`, `inspect`, `textwrap`
   (ölçü 5'in AST yarısı) ve `collections.abc.Callable` (parametrize edilen
   fixture üreticilerinin tipi). `purity_check.py` yalnız `src/ocr/*.py`'yi
   tarar; test dosyası etkilenmez.
8. **K30'un birinci yolunu da kendi dosyama yazdım.** Karar ilk yolu
   Tester-B'nin `test_r3_k2_*`'sine, ikinciyi bana veriyordu; ikisini birlikte
   yazmak "iki yol da birer testle sabitlenir" şartını benim dosyamda da
   karşılıyor ve cümlenin **koşulluluğunu** tek yerde görünür kılıyor.
   Tester-B'nin testine dokunmadım.
9. **K31'e üçüncü bir test** (`test_k31_iki_farkli_taninan_ad_birlesmez`)
   ekledim: karar metni "iki farklı tanınan ad birleşmez — şef doğruladı"
   diyor ama testini istemiyordu. Cümle docstring'de garanti olarak durduğu
   için ölçüsünü de koydum.
10. **Modül docstring'inin K2 bölümüne K30 cümlesi eklendi.** Karar cümlenin
    `_group` docstring'ine gitmesini istiyor; ama düzeltilen olgusal hata K2
    bölümündeki "o blok hiç var olmamış gibi çalışır" ifadesindeydi, bu yüzden
    oraya da koşullu bir uyarı + `_group`'a çapraz gönderme yazdım.
11. **`normalize`'ın docstring'i** K28-K32'ye ve NFC varsayımına atıf yapacak
    şekilde genişletildi; **gövdesi değişmedi**.
12. **Koşum süresi.** Ölçü 6 + ölçü 7 birlikte `tests/unit/ocr` koşumunu
    0,25 s'den ~2,6 s'ye çıkarıyor (tam takım 3,2 s). K14 bütçe testi
    (medyan ≤ 5 ms) etkilenmiyor: **medyan 0,170 ms** (min 0,166 / max 0,263),
    `evidence/budget-r6.txt`. `_raw_query_pair` sınır başına iki kısa `sorted`
    çağrısı ekliyor; ölçülebilir bir maliyeti yok.

## Kapsam dışı bıraktıklarım

- `olcu_kiti.py`, `purity_check.py`, `conftest.py` dosyalarına **dokunmadım**
  (şefe ait). `tester_A/`, `tester_B/`, `tester_C/` dizinlerini **okumadım**.
- `src/ocr/presets.py` **değişmedi** (kabul komutunda yer aldığı için
  `files_written`'a yazılmadı).
- Kararın §4.6/5 listesindeki bayat tester testleri A ve B tarafından yeniden
  nişanlanacak; benim sahipliğimde değiller.
