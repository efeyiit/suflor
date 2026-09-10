---
task: T-004
role: implementer
round: 7
status: tamamlandi
files_written:
  - src/ocr/normalizer.py
  - tests/unit/ocr/test_normalizer.py
commands:
  - cmd: "python -m mypy --strict src/ocr/normalizer.py src/ocr/presets.py"
    exit_code: 0
    evidence: evidence/mypy-r7.txt
  - cmd: "python -m pytest tests/unit/ocr/test_normalizer.py -q"
    exit_code: 0
    evidence: evidence/pytest-r7.txt
  - cmd: "python .agents/tasks/T-004/purity_check.py"
    exit_code: 0
    evidence: evidence/purity-r7.txt
  - cmd: "python .agents/tasks/T-004/olcu_kiti.py"
    exit_code: 0
    evidence: evidence/kit-r7.txt
  - cmd: "python -m pytest tests -q   (REGRESYON -- 822 passed = 821 + T7-2)"
    exit_code: 0
    evidence: evidence/pytest-regresyon-r7.txt
  - cmd: "python .agents/tasks/T-004/evidence/kirmizi_r7.py   (KIRMIZI FAZ -- T7-2 uc M15 mutantinda da KIRILIYOR)"
    exit_code: 0
    evidence: evidence/pytest-red-r7.txt
  - cmd: "python .agents/tasks/T-004/evidence/mutasyon_r7.py   (DIS OLCUMU -- uc mutant x bes kapi tablosu)"
    exit_code: 0
    evidence: evidence/mutant-r7.txt
  - cmd: "python .agents/tasks/T-004/evidence/ast_esitlik_r7.py   (T7-1 SALT DOKUMANTASYON: docstring'siz AST HEAD ile ozdes)"
    exit_code: 0
    evidence: evidence/ast-esitlik-r7.txt
  - cmd: "python -m pytest tests/unit/ocr/test_normalizer.py -q -k k14   (K14 butcesi, PROTOKOL S6/5)"
    exit_code: 0
    evidence: evidence/budget-r7.txt
  - cmd: "python -m pytest .agents/tasks/T-004/tester_A tester_B tester_C -q   (KOR TAKIM -- sahipligimde DEGIL, yalniz gozlem: 623 passed + BEKLENEN tek XPASS kirigi)"
    exit_code: 1
    evidence: evidence/kor-takim-r7.txt
contract_change_request: false
known_gaps:
  - "TUR 6'DAN DEVREDEN 1/6 (karar tur 7, 'bu turda YAPILMAYACAKLAR' tablosu) -- `olcu5_fixture`'a COK BLOKLU aday (B/N1): kitin `olcu5_fixture`'inda adayin (`nxt`) COK BLOKLU oldugu bir sinir YOK, dolayisiyla olcu 5 SAG taraftaki ham ikameyi tam olarak yoklamiyor. Kitin fixture'ini degistirmek OLCU KURGUSUNA dokunur ve karar kirmizi takimi gerektirir; sef AYRI BIR TURA birakti. Kit SEFE AITTIR, ben DOKUNMADIM."
  - "TUR 6'DAN DEVREDEN 2/6 -- M12 sinifi yalniz `test_k5_*`'ye yaslaniyor (B/N4): kitin `adim1_4` referansi DENETLENEN modulun kendi yardimcilarini (`_merge_hyphenated`, `_extract_speakers`, ...) cagirarak uretilir, yani PROTOKOL 4.6/8 anlaminda BAGIMSIZ DEGILDIR -- o yardimcilari bozan bir mutantta kitin oge listesi mutantla BIRLIKTE kayar ve kimlik/sira kanallari sessizce bosalir. Bugun bu sinifin tek dayanagi urun dosyasindaki `test_k5_*` testleridir. Karar sürüm 8'in 'bilinen sinirlar'inda yazili; ayri tur."
  - "TUR 6'DAN DEVREDEN 3/6 -- `Mn`/`Mc` ad suzgeci genisletmesi (C/1): K9'un ad suzgeci codepoint bazli `isalpha()`'dir; birlesik aksan isaretleri (`Mn`/`Mc` kategorileri) HARF SAYILMAZ, bu yuzden NFD adlar konusmaci sayilmaz (K32). Suzgeci `Mn`/`Mc`'yi kabul edecek sekilde genisletmek K9'UN SOZLUKSEL KURALINI DEGISTIRIR -- DAVRANIS degisikligidir, ayri tur. Tur 6'da yalniz `known_gaps` cumlesi duzeltilmisti."
  - "TUR 6'DAN DEVREDEN 4/6 -- ZWJ/emoji grapheme sismesi (C/4): `max_group_chars` (K11) ve `_MAX_SPEAKER_NAME_LEN` (K9) CODEPOINT sayar, GRAPHEME degil. ZWJ ile birlestirilmis emoji dizileri (aile emojisi vb.) tek bir GORSEL karakter olmasina ragmen 5-7 codepoint tuketir ve bolumlemeyi ERKEN keser. K32'nin NFC/NFD sinifiyla AYNI sinif; K11'in kuralini degistirir, ayri tur."
  - "TUR 6'DAN DEVREDEN 5/6 -- miras `monitor_index`/`dpi_scale` sinirini asiyor (C/2): K10 farkli `monitor_index`/`dpi_scale` tasiyan bloklarin BIRLESIMINI `ValueError` ile yasaklar, ama K19/K21'in MIRAS gecisi bir bolumleme degil bir GORUNUM gecisidir ve bu sinira TABI DEGILDIR -- iki AYRI monitorde duran iki segment arasinda `speaker` mirasi bugun MUMKUNDUR. Kapatmak YENI BIR DEGISMEZ gerektirir; ayri tur."
  - "TUR 6'DAN DEVREDEN 6/6 -- `NaN` `dpi_scale` tani mesaji (C/3): K7 `confidence` icin `NaN`/alan disi degerde ACIK ve tanimlayici bir `ValueError` uretir; `dpi_scale` icin BOYLE BIR ON DENETIM YOKTUR -- `NaN` bir `dpi_scale` sessizce akar ya da baska bir yerde anlamsiz bir mesajla patlar. KOZMETIK (tani kalitesi); ayri tur."
  - "TUR 7'DE OLCTUM -- KARARIN OLCUSU TEK YONLUYDU (raporlanir, sef okusun): karar T7-2'yi YALNIZ `dialogue` on ayarinda tarif ediyordu. Olctum (`evidence/mutant-r7.txt`): sorguyu SABIT `get_params(OcrPreset.DIALOGUE)` ile soran mutant (M15-c -- kararin M15 tarifiyle BIREBIR ortusen, dort kabul komutunu ve 124 urun testini TEMIZ gecen mutant) yalniz-`dialogue` bir testte AYIRT EDILEMEZ, cunku o kosumda mutant ile dogru uygulama AYNI sonucu verir. Testi AYNI ADLA ve TEK TEST olarak biraktim (822 sayisi korunur) ama govdesini IKI YONLU yaptim: AYNI bloklar `dialogue` VE `tooltip` on ayarlarinda kosulur. Uc mutant da (M15-a sabit `tooltip`, M15-b sorgu ici `replace` esik ikamesi, M15-c sabit `dialogue`) simdi YAKALANIYOR."
  - "TUR 7'DE OLCTUM -- KITIN `params` SINIRI KAPANMADI, KATMANLANDI: `olcu_kiti.sorgu_kaydi()` kancasi `(a, b, params)` uclusunu gorur ama `params` KIMLIGINI kaydetmez (karar tur 6'nin M15 satiri). Kit SEFE AITTIR ve DEGISTIRILMEDI: T7-2 kiti ICE AKTARIR (geometri/sayi kanali icin) ve UZERINE kendi `params` kancasini KATMANLAR (once benimki, sonra kitinki; cikista LIFO). Kitin kendi kanallarinda `params` kimligi HALA olculmuyor -- kit surum 4 yazilirsa oraya tasinmalidir."
  - "TUR 7'DE OLCTUM -- BASLIK METNI BOLUM SINIRIDIR (tuzak, kayda geciyor): garanti alani denetimleri modul docstring'ini `docstring.split('### K24')` gibi BASLIK METNIYLE dilimler. K28 bolumune yazdigim capa cumlesi ilk halinde baslik metnini AYNEN tekrarliyordu ve tester_A'nin dilimini SESSIZCE kaydiriyordu (olctum: dilim 4492 -> 334 karaktere dustu). Capa metnini baslik metnini TEKRARLAMAYACAK bicimde yazdim ve bu disiplini `## K28` bolumune NOT olarak ekledim. Baska bolum basliklarinda AYNI risk duruyor -- denetimlerin dilimleme mekanizmasi kirilgandir, gelecekte satir-numarasi/regex yerine ACIK bir isaretleyici (or. `<!-- K24:son -->`) daha saglam olurdu; bu turda ONERI olarak birakiliyor, uygulanmadi."
  - "TUR 6'DAN DEVREDEN (degismedi) -- K28-KOK: R5-1'in KOKU adim 3'tur (`_merge_hyphenated`, K5) ve K28 yalnizca SEMPTOMU kapatir. Adim 3 SALT TIPOGRAFIKTIR (tire + kucuk harf; GEOMETRIK kontrol YOK) ve sefin karariyla OYLE KALIR. Birlesik oge geometrisi adim 5'in MIRAS kararina artik hic girmez, BOLUMLEME kararina ise birlesik bbox ile GIRER (K10/K11)."
  - "TUR 6'DAN DEVREDEN (degismedi) -- `_group`'un `blocks=()` VARSAYILANI GECIKMELI PATLAMA uretir: `blocks` gecirilmeden yapilan DOGRUDAN `_group(...)` cagrilarinda `reason == 'length' and nxt.speaker is None` sinirina varilirsa `_raw_query_pair` `IndexError` yukseltir. BILINCLIDIR (sessiz yanlis yerine gurultulu hata); `_normalize_impl` her zaman `blocks=blocks` gecirir, urun yolunda bu durum DOGMAZ."
  - "TUR 6'DAN DEVREDEN (degismedi) -- K30/K31/K32'nin BILINCLI sinirlari: (K30) adim 1'de dusen blogun biraktigi ARTIK bosluk esigi ASARSA miras kesilir, ASMAZSA korunur -- sonuc BOSLUGUN BUYUKLUGUNE baglidir; (K31/b) K9'un ad suzgecinden GECEMEYEN ikinci etiket METINDE kalir ve segment ILK konusmaciya atfedilir, urun etkisi olarak (a)'dan KOTUDUR; (K32) girdi NFC VARSAYILIR, NFD govde BOLUMLEMEYI de degistirir -- NFC normalizasyonu T-006 cikis sozlesmesine adaydir."
  - "TUR 6'DAN DEVREDEN (degismedi) -- kabul edilmis eski sinirlar: (i) K5 hyphen kurali YALNIZCA ASCII `-` (U+002D); `‐`/en-dash/em-dash kapsam disi. (ii) `_collapse_intraline` `\\n` icermeyen metinlerin de bas/son bosluklarini kirpar. (iii) S8.3 A3'un 'altin goruntu seti' kriteri bu gorevin KAPSAMI DISINDA. (iv) `presets.py` yalniz normalizasyon parametreleri icerir; S3.2'nin olcekleme faktoru / kontrast on islemesi alanlari sonraki goreve birakildi. (v) K17 ayrac kumesi `:` + `：` ile sinirli; `﹕` (U+FE55) gibi varyantlar kapsam disi."
  - "TUR 6'DAN DEVREDEN (benim duzeltmem DEGIL) -- K28'in BAYATLATTIGI KAPI ALETLERI: `tester_B/test_karar_uyumu_tur5.py:567` (`args[0] == 'tail'` AST beklentisi), ayni dosyadaki `test_r5_k23_normalize_impl_bayragi_yalniz_group_cagrisina_iletir`, `tester_B/test_k23_mutant_sondasi_tur5.py`'deki M1/M2/M3 desenleri, ve `blocks=` gecirmeyen DOGRUDAN `_group` cagrilari. Bunlarin hicbirine DOKUNMADIM -- sahipligimde degiller. TUR 7'de bunlara BIR YENI kalem eklendi: `tester_A/test_r6_garanti_alani.py:771`'deki `strict=True` xfail T7-1 duzeltilince XPASS ile KIRILDI (BEKLENEN; kararda yazili, A yesile cevirecek). Kor takim kosumu: 623 passed + O TEK kirik, baska duşen YOK (`evidence/kor-takim-r7.txt`)."
---

# T-004 · Tur 7 teslimi — kapanış turu: T7-1 (docstring) + T7-2 (tek test)

Karar: `.agents/tasks/T-004/sef_karari-tur7.md`. İki kalem de uygulandı.
**Yeni değişmez yok, davranış değişikliği yok** — makineyle kanıtlandı:
`evidence/ast-esitlik-r7.txt`, `normalizer.py`'nin docstring'siz AST'si
HEAD ile **birebir aynı** (`docstring'siz AST BIREBIR AYNI MI: True`).

## T7-1 — `### K24` bölümü K28'e devretti

`src/ocr/normalizer.py` modül docstring'i. Bölüm **silinmedi** (tarihçe
değerli); dört ekleme yapıldı:

| Yer | Ne eklendi |
|---|---|
| `### K24` başlığının hemen altı | **DEVREDILDI (tur 6, K28)** alıntı bloğu: bölümün tur 5'in kaydı olduğu, bugünkü tanımın `## K28`'de durduğu, **ayakta kalan** yönün (sol taraf = grubun kuyruğu, `current`'in birleşik kutusu değil) ve **çürüyen** kısmın (`tail`in HAM olduğu varsayımı + çağrı biçimi) ayrı ayrı adı. Bugünkü çağrı birebir yazılı: `_group_rejection_reason(*_raw_query_pair(tail, nxt, blocks), params, ignore_length=True)` |
| "Geçerli TEK ifade" bloğunun altı | K28 okuma notu: "SON KAYNAK ÖGESİ" bugün "kaynak **blokları** arasında okuma sırasında son gelen **özgün blok**" olarak okunur; sağ taraf için simetriği geçerli |
| "Uygulama" paragrafı | Başlığı **`(TUR 5, K28 ONCESI -- TARIHCE)`** oldu; şimdiki zaman geçmiş zamana çevrildi. `tail` değişkeninin **bugün de durduğu** ayrıca söylenir (o iki cümle bayat değil) |
| Yeni **NEDEN ÇÜRÜDÜ** paragrafı | Çürüyen cümlenin **niçin** çürüdüğü: `tail` grubun kuyruğudur ama **ham olmak zorunda değildir** — adım 3 (`_merge_hyphenated`, K5) hyphen'li satırları tek `_Item`'a birleştirir ve bbox'ı birleşik kutudur; kuyruk çok bloklu olduğunda K24'ün kaldırdığı artefakt **adım 3 üzerinden geri gelir**. Aynı şey aday (`nxt`) tarafı için de geçerli. Ölçüm (A'nın derlemi, kararda yazılı): 30.174 sınırın %5,2'si; sağ tarafta 2065 sınırın 242'si |

`## K28` bölümüne de bir **devralma çapası** eklendi: K24'ün miras-uygunluk
sorgusu hakkındaki kısmını devraldığı, K24'ün ne dediği, K28'in bir adım
daha ileri gittiği ve **çağrı biçimi için burasının geçerli olduğu**.

**Ölçü (kararın istediği):** `### K24` bölümünde `K28` **8**, `_raw_query_pair`
**3** kez geçiyor (turun başında **0/0** idi). `purity_check.py` exit 0 —
K29 atıfları bozulmadı, bölümde anılan iki `test_k24_*` adı hâlâ gerçek.

Tester-A'nın `strict=True` xfail'i **beklendiği gibi XPASS ile kırıldı**
(`evidence/kor-takim-r7.txt`: `623 passed, 1 failed`, kırık **yalnızca**
o). O dosyaya **dokunmadım**.

## T7-2 — M15 kapısı: `test_k28_miras_sorgusu_ayni_params_ile_sorulur`

`tests/unit/ocr/test_normalizer.py`, `# --- TUR 7 ---` başlığı altında
**tek test** (+ toplanmayan `_t72_params_sondasi` yardımcısı). Toplam
`tests` sayısı **821 → 822**; ürün dosyası 124 → 125.

**Geometri kararda yazıldığı gibi:** `h=18`, sınırda `gap=12`; sınır iki ön
ayarda da yalnız-uzunluk sınırı (`150 + 1 + 150 = 301`; dialogue cap 280,
tooltip cap 200). Eşik çarpımları **yorumda değil assert'te** —
`0.8 × 18 = 14.4 > 12 > 5.4 = 0.3 × 18` — ön ayar tablosu kayarsa test
totolojiye düşmek yerine kırılır (kitin `_esik_alti_conf` ilkesi).

Her ön ayarda üç assert ailesi:

1. **Davranış:** `normalize` çıktısında miras `dialogue`'da taşınıyor
   (`["Ada", "Ada"]`), `tooltip`'te taşınmıyor (`["Ada", None]`).
2. **Kit kanalı (`olcu_kiti.sorgu_kaydi()`):** miras sorgusu **tek**, sol/sağ
   `source_blocks` `(0,)`/`(1,)` ve bbox'lar **ham blokların** (K28).
3. **Değişmez:** gözlenen **her** çağrı **tek ve aynı** `params` nesnesini
   gördü — `p is get_params(<ön ayar>)`. `is` bilinçlidir: değişmez "aynı
   `params` nesnesi" der, bir eşik ikamesi (`replace(params, ...)`) değeri
   tesadüfen aynı kalsa bile ihlaldir.

**Kit değiştirilmedi.** `sorgu_kaydi()` `params` kimliğini kaydetmiyor
(kitin bilinen sınırı), bu yüzden kendi kancam kitin **altına katmanlandı**
(önce benimki, sonra kitinki; çıkışta LIFO). Kit yalnızca içe aktarıldı.

### Testin dişleri — üç mutant, geçici kopyada

**Depo dosyaları hiçbir aşamada değiştirilmedi.** Her mutant, betiğin kendi
açtığı geçici bir depo kopyasında kuruluyor ve koşum bitince kopya siliniyor
(`evidence/_mutant_kopya_r7.py`). İki betik de **depo kökünden aynen
koşulabilir** — `delivery.md`'deki `cmd` satırları birebir yeniden
üretilebilir komutlardır (PROTOKOL §3/1):
`python .agents/tasks/T-004/evidence/mutasyon_r7.py` (tablo) ve
`python .agents/tasks/T-004/evidence/kirmizi_r7.py` (ham kırmızı çıktı).

| Mutant (miras sorgusunun `params`'ı) | mypy | ürün testleri (T7-2 hariç) | purity | ölçü kiti | **T7-2** |
|---|---|---|---|---|---|
| — (mutasyonsuz kontrol) | 0 | 0 | 0 | 0 | **0 (yeşil)** |
| M15-a sabit `tooltip` | 0 | **1** | 0 | 0 | **1 (kırmızı)** |
| M15-b `replace(params, ratio=0.3)` | 0 | **1** | 0 | 0 | **1 (kırmızı)** |
| M15-c sabit `dialogue` — *kararın M15'i* | 0 | **0** | 0 | 0 | **1 (kırmızı)** |

Üçü de T7-2'nin **davranış** assert'inde düşüyor (kimlik assert'i teknik bir
yedek, tek dayanak değil) — ham çıktı `evidence/pytest-red-r7.txt`.

## Belgenin sessiz kaldığı yerler — verdiğim kararlar

1. **Kararın ölçüsü tek yönlüydü; testi iki yönlü yaptım.** Karar T7-2'yi
   yalnız `dialogue` ön ayarında tarif ediyor. Ölçtüm: kararın M15 tarifiyle
   birebir örtüşen mutant (M15-c — sorguyu sabit `get_params(DIALOGUE)` ile
   soran, dört kabul komutunu **ve** 124 ürün testini temiz geçen mutant)
   yalnız-`dialogue` bir testte **ayırt edilemez**; o koşumda mutant ile
   doğru uygulama aynı sonucu verir. Testi kararın verdiği **adla** ve **tek
   test** olarak bıraktım (822 sayısı korunur), gövdesini iki ön ayarda
   koşacak biçimde yazdım. Yeni değişmez eklemedim — ölçülen değişmez
   kararın yazdığı değişmezin ta kendisi.
2. **`params` kimliği `is` ile ölçüldü.** Karar "aynı `params` nesnesi"
   diyor; eşitlik (`==`) `replace(params, ...)` ile üretilmiş bir kopyayı
   kabul ederdi. `is` tercih edildi ve gerekçesi test docstring'ine yazıldı.
3. **Kit yerine katman.** Kararın istediği ölçü kanalı (`params` kimliği)
   kitte yok. Kiti değiştirmek yasak olduğu için kanca **katmanlandı**; kitin
   kendi kanalları olduğu gibi kullanıldı (geometri + sayı).
4. **`### K24` bölümü silinmedi, geçmiş zamana çevrildi.** Kararın "silme,
   devrettiğini söyle" talimatı harfiyen uygulandı; ek olarak "Uygulama"
   paragrafındaki **hâlâ doğru** olan iki cümle (`tail` değişkeninin bugün de
   tutulduğu) açıkça ayrıldı — yoksa doğru bilgi de tarihçeye gömülürdü.
5. **Başlık metni bölüm sınırıdır.** Çapa cümlesinin ilk hâli `### K24`
   başlığını aynen tekrarlıyordu ve tester_A'nın `docstring.split('### K24')`
   dilimini sessizce kaydırıyordu (ölçtüm: 4492 → 334 karakter). Çapa metni
   başlığı tekrarlamayacak biçimde yazıldı ve bu disiplin `## K28` bölümüne
   **NOT** olarak eklendi. Denetimlerin dilimleme mekanizması kırılgan;
   açık bir işaretleyici daha sağlam olurdu — **öneri olarak** bırakıldı,
   uygulanmadı (ölçü kurgusuna dokunur, ayrı tur).
6. **`### K24`'ün "Zorunlu test" paragrafına kısa bir K28 notu** eklendi:
   iki test de bugün yeşil — birincisi `_group_rejection_reason`'ı doğrudan
   çağırır (`_raw_query_pair` yoluna hiç girmez), ikincisinde kuyruk tek
   bloklu (`source_blocks=(2,)`) olduğu için ham ikame özdeşliktir. İkisini
   de kendim ölçtüm, iddia etmedim.

## Dokunmadıklarım

`olcu_kiti.py`, `purity_check.py`, iki `conftest.py`, `tester_A/`,
`tester_B/`, `tester_C/`, `src/contracts/`, `src/capture/`, `presets.py`.
`git diff --stat`: yalnız `src/ocr/normalizer.py` (docstring) ve
`tests/unit/ocr/test_normalizer.py`. `.agents/PROTOKOL.md`'deki değişiklik
bu oturumdan **önce** vardı, benim değil.
