---
task: T-011
role: implementer
round: 1
status: tamamlandi
files_written:
  - src/translate/sozluk.py
  - tests/unit/translate/test_sozluk.py
  - .agents/tasks/T-011/delivery.md
  - .agents/tasks/T-011/evidence/mypy.txt
  - .agents/tasks/T-011/evidence/mypy-test-dosyasi.txt
  - .agents/tasks/T-011/evidence/pytest.txt
  - .agents/tasks/T-011/evidence/pytest-cp1254.txt
  - .agents/tasks/T-011/evidence/cov.txt
  - .agents/tasks/T-011/evidence/pytest-tum.txt
  - .agents/tasks/T-011/evidence/real_check.txt
  - .agents/tasks/T-011/evidence/real_check-duzeltilmis-kopya.py
  - .agents/tasks/T-011/evidence/real_check-duzeltilmis-kopya.diff
  - .agents/tasks/T-011/evidence/real_check-duzeltilmis-kopya.txt
  - .agents/tasks/T-011/evidence/kapi-itirazi-3c-6a.py
  - .agents/tasks/T-011/evidence/kapi-itirazi-3c-6a.txt
  - .agents/tasks/T-011/evidence/tdd-kirmizi-1-modul-yok.txt
  - .agents/tasks/T-011/evidence/mutant-kiti.py
  - .agents/tasks/T-011/evidence/mutant-ayirt-etme.txt
  - .agents/tasks/T-011/evidence/mutant-ayirt-etme-hangi-testler.txt
  - .agents/tasks/T-011/evidence/sure-olcumu.py
  - .agents/tasks/T-011/evidence/sure-olcumu.txt
  - .agents/tasks/T-011/evidence/olcum-anahtar-ignorecase-denkligi.py
  - .agents/tasks/T-011/evidence/olcum-anahtar-ignorecase-denkligi.txt
commands:
  - cmd: "python -m mypy --strict --explicit-package-bases src/translate/sozluk.py"
    exit_code: 0
    evidence: evidence/mypy.txt
  - cmd: "python -m pytest tests/unit/translate/test_sozluk.py -q  (256 passed)"
    exit_code: 0
    evidence: evidence/pytest.txt
  - cmd: "python .agents/tasks/T-011/real_check.py  (10/12 ok; 2 IHLAL = KAPI HATASI: #3c segmente placeholders verilmiyor, #6a chr(44608)=U+AE40 aranirken terim U+AC80 -- bkz. Kapi itirazi; modul degil)"
    exit_code: 1
    evidence: evidence/real_check.txt
  - cmd: "python .agents/tasks/T-011/evidence/real_check-duzeltilmis-kopya.py  (sefin kapisinin iki satiri duzeltilmis KOPYASI, evidence/ altinda; TEMIZ 12/12; #7 medyan 35.1 ms)"
    exit_code: 0
    evidence: evidence/real_check-duzeltilmis-kopya.txt
  - cmd: "python .agents/tasks/T-011/evidence/kapi-itirazi-3c-6a.py  (gercek model; #6a kod noktasi olcumu; #3c uc kol: ham / gomulu yer tutucusuz / gomulu placeholders=('{0}',))"
    exit_code: 0
    evidence: evidence/kapi-itirazi-3c-6a.txt
  - cmd: "python -m pytest tests/unit/translate/test_sozluk.py -q --cov=src.translate.sozluk --cov-fail-under=95 --cov-report=term-missing  (301 ifade, %100)"
    exit_code: 0
    evidence: evidence/cov.txt
  - cmd: "python -m pytest tests -q  (1700 passed, dusen yok)"
    exit_code: 0
    evidence: evidence/pytest-tum.txt
  - cmd: "python -m mypy --strict --explicit-package-bases tests/unit/translate/test_sozluk.py"
    exit_code: 0
    evidence: evidence/mypy-test-dosyasi.txt
  - cmd: "python -m pytest tests/unit/translate/test_sozluk.py -q -p no:cacheprovider  (chcp 1254, PYTHONIOENCODING YOK, sys.stdout.encoding=cp1254)"
    exit_code: 0
    evidence: evidence/pytest-cp1254.txt
  - cmd: "python -m pytest tests/unit/translate/test_sozluk.py -q -p no:cacheprovider --no-header  (TDD KIRMIZI: testler yazildi, modul yok -> toplama hatasi ImportError)"
    exit_code: 2
    evidence: evidence/tdd-kirmizi-1-modul-yok.txt
  - cmd: "python .agents/tasks/T-011/evidence/mutant-kiti.py  (ayna: %TEMP%/t011_ayna, depoya dokunmaz; 32 mutant + 3 kontrol; 32/32 yakalandi, 3/3 kacti; test adlari evidence/mutant-ayirt-etme-hangi-testler.txt)"
    exit_code: 0
    evidence: evidence/mutant-ayirt-etme.txt
  - cmd: "python .agents/tasks/T-011/evidence/sure-olcumu.py  (K5: 1000 segment x 11/50/500 terim, JP+EN, lookup_segments+gom 15-16 ms, kapi yolu 18-22 ms; butce 50)"
    exit_code: 0
    evidence: evidence/sure-olcumu.txt
  - cmd: "python .agents/tasks/T-011/evidence/olcum-anahtar-ignorecase-denkligi.py  (tum Unicode; IGNORECASE denk 1514 ciftin 0'inda kanonik anahtar farkli)"
    exit_code: 0
    evidence: evidence/olcum-anahtar-ignorecase-denkligi.txt
contract_change_request: false
known_gaps:
  - "[KAPI ITIRAZI 1 -- real_check #6a, OLCULDU] Kapi `chr(44608) in str(e)` ariyor; 44608 = U+AE40. Gecici sozluge yazilan terim U+AC80'dir (real_check.py satir 95 literali; `kapi-itirazi-3c-6a.txt`: 'ikisi ayni mi: False'). Modulun ValueError mesaji GERCEK terimi (U+AC80) tasir (`var: True`), U+AE40'i tasimaz (`False`). Duzeltme onerisi: literali degiskene al ve ayni degiskeni ara (duzeltilmis kopyada `TEK_HECE`). Modulde degisiklik gerekmez."
  - "[KAPI ITIRAZI 2 -- real_check #3c, OLCULDU] Kapinin `cevir()`i segmentleri `Segment(text=t, bbox=...)` ile kurar: `placeholders=()`. `{0}` bu yuzden hem sozluk icin hem T-007 K5 onarimi icin DUZ METINDIR; model JP'de yer tutucuyu dusurur (T-007 C9). Uc kol gercek modelle (`kapi-itirazi-3c-6a.txt`): (a) HAM, gommesiz, placeholders=() -> {0}=False (dusus gommeden BAGIMSIZ, modelin); (b) gomulu, placeholders=() (kapinin yolu) -> {0}=False; (c) gomulu, `placeholders=('{0}',)` (paket K3: 'real_check #3 segmentlere placeholders verir') -> {0}=True, Marcus=True. Gomulu KAYNAK metinde {0} sayisi 1 (modul yer tutucuya dokunmadi). Not: bu cumlede ham ceviri de 'Marcus' uretiyor; #3c'nin 'Marcus var' kolu bu cumlede ayirt edici degil. Duzeltme onerisi: `cevir(..., yer_tutucular=())` parametresi, #3c `('{0}',)` ile. Duzeltilmis kopya (`evidence/real_check-duzeltilmis-kopya.py`, fark `*.diff`: iki degisiklik + yol sabitleri) TEMIZ 12/12."
  - "[PAKET ILE OLCUM CELISKISI -- K1 OLCU '검은 옷 -> eslesmez'] Ayni satirdaki `검사` (izinli tek hece, sinir kurali reddeder) ile ayni sinifta degil: `검은 옷` = `검` + GERCEK ek `은` + bosluk, kural GECER (K1 metni 'Bilinen sinir', real_check #6c '1 hit (rapor)'). 'Eslesmez' yalniz SEMA etkisiyle dogrudur: `검` izinsiz reddedilir, sozluk kurulamaz, hit olusamaz. Iki test ayri yazildi: `test_k1_검은_옷_izinsiz_sema_reddi_eslesme_yok` (ValueError, mesajda terim) ve `test_k1_검은_옷_izinle_bilinen_sinir_eslesir` ([(0,1)], bilinen sinir sabitlendi). Paketin OLCU satiri bu ayrimi yapmiyor; DEGISMEZ metni ve kapi #6c ile uyumlu olan olcum izlendi."
  - "[PAKETIN BIR ADIM OTESI -- belgelenmis genisletmeler] (1) KR ek zinciri: 'ekten sonra da sinir' ozyineli okundu, en fazla 2 ek (`에서는`, `까지는.` eslesir; 3 ek eslesmez -- `test_k1_kr_ek_zinciri_iki_ekle_sinirli`, mutant M22). (2) Yer tutucu (korunan aralik) UCU sinirdir: `%s`+JP ad `placeholders=('%s',)` ile eslesir, bildirilmemisken `s` harftir -> hit yok (`test_k1_yer_tutucu_ucu_sinirdir`, M23). (3) Tek kodpoint reddi paketin 'tek hangul/tek kanji'sinden TUM tek kodpointlere genisletildi (tek kana, tek Latin harf; gerekce ayni: sinir kurali ayristiramaz; opt-in ayni bayrak). (4) Kayit duzeyinde bilinmeyen anahtar RED (`ozel_ad` v1 bayragi, `kisa_terim_izin` yazim hatasi sessiz yutulmaz); ust duzey ek anahtar SERBEST (profil meta verisi). (5) Bas/son bosluklu kaynak/hedef RED (sessiz kirpma yok). (6) Turkce buyutme: `i` -> `İ` (`ihtiyar` -> `İhtiyar`; `.upper()` `Ihtiyar` verirdi). (7) `GlossaryStore.lookup_segments(segments)`: `segment_index` dolu, kopyasiz (KRT O4 el yordami; kapi `dataclasses.replace` ile kendi yapar, ikisi de calisir). (8) `terimleri_gom` ek denetimleri: `start == end`, `target_term` bos, oge `Segment`/`TermHit` degil, `start/end` int degil -> ContractViolation. (9) `lookup` duz `str` placeholders -> TypeError (karakterlere bolunme tuzagi)."
  - "[K1 -- KOMSU TERIM SINIRI, sinif kaydi] 'Sozlukteki baska terimin baslangici/bitisi sinirdir' kurali (G6 EK KURAL) komsu terimin KABUL edilmesini istemez, aday olmasi yeter (`マルクス長老`: uzun terim once islenirken kisa komsu henuz kabul edilmemistir; kabul sarti aransa ikisi de duserdi -- `test_k1_bitisik_iki_terim_ters_sirada_*`). Sonucu: iki sozluk terimi bitisik bir bilesik olusturuyorsa ikisi de gomulur (`millstone` = `mill`+`stone` ikisi de sozlukteyse `DeğirmenTaş`) -- yazar ikisini de istedigi icin kabul edilebilir; D1 fuzyon sinifi `[ÖLÇÜLMÜYOR]` (motor 5/5 ayirdi, KRT). Ayni terimin bitisik iki gecisi (`MarcusMarcus`) iki hit verir."
  - "[K1 -- SINIRDA OLMAYAN KARAKTERLER] Sembol kategorileri (`S*`: `~ + $ ♪ →`) sinir DEGIL `[ÖLÇÜLMÜYOR]` -- paket yalniz `P*` sayar; `Marcus♪` eslesmez. KR ekler yalniz SAG sinirdir (solda ek = onceki kelimenin eki; `의장로` eslesmez, bilincli). Ek kumesi paketin 18 ekidir; `에게`, `한테`, `님` gibi ekler kumede YOK -> `마르쿠스에게` eslesmez `[ÖLÇÜLMÜYOR]` (kume sefin kararidir; genisletme ayri karar)."
  - "[K4 -- SINIR] Kucuk `i` ile baslamasi gereken hedef (marka adi) da `İ` ile buyutulur; paket her hedefi buyutmeyi zorunlu kilar (G7). Kesme isareti (`Değirmen'de`) kozmetik `[ÖLÇÜLMÜYOR]` (real_check #5 raporlar: bu kosumda kesme=False)."
  - "[K5 -- KAPSAM IZLEYICISI] `--cov` (C tracer) altinda Python satirlari ~4x yavaslar: 1000 segment x 50 terim 12-16 ms -> 55 ms. Sure testleri `sys.gettrace()` aktifken butceyi 4x alir ve olculen degeri assert mesajina yazar; gercek butce izleyicisiz kosumda (`pytest.txt`, `sure-olcumu.txt`: 15-22 ms) ve `real_check` #7'de (model yuklu surecte 35-36 ms, onceki kosumda 22.7 ms; < 50) olculur. Performans: TRIE yapili tek ileri-bakisli desen + ilk-karakter bekcisi + kanonik anahtar tablosu; duz alternation 50 terimde 28 ms, 500 terimde 300+ ms tarama veriyordu (asamalar `evidence/sure-olcumu.txt`, ara olcumler bu teslimde yalniz metin olarak: 51 ms -> 17 ms -> 12 ms)."
  - "[K6 -- KANONIK ANAHTAR] Eslesen dilim terime `casefold` + Turkce I sinifi anahtariyla baglanir; IGNORECASE'in denk saydigi 1514 kodpoint ciftinin (tum Unicode, `_sre.unicode_tolower` + `re._casefix._EXTRA_CASES`, 3.12) hepsinde anahtar ayni (`olcum-anahtar-ignorecase-denkligi.txt`); yedek dogrusal tarama bu olcumle KALDIRILDI. Tekrar tespiti ayni anahtarla (`Marcus`/`MARCUS`, `istanbul`/`İstanbul`, NFC/NFD). Python surumu degisirse denklik tablosu degisebilir `[ÖLÇÜLMÜYOR]` (olcum betigi yeniden kosulur)."
  - "[TDD] Kirmizi faz: test dosyasi modul yokken yazildi, toplama `ImportError` (`tdd-kirmizi-1-modul-yok.txt`, exit 2). Ilk yesil kosumda 168/169 gecti; tek dusen K5 sure testiydi (51.5 ms > 50) ve performans calismasini tetikledi (yukarida). Davranis ayirt etme mutant kitiyle: 32/32 yakalandi (ayrintili tablo asagida), 3/3 esdeger kontrol kacti."
  - "[CALISMA KOPYASI] `demo/sozluk_ornek.json` takipsiz dosya bana ait degil, dokunmadim. `git add`/`commit` ATILMADI."
---

# T-011 tur 1 -- teslim ozeti

Iki parca tek modulde: `GlossaryStore(json_path)` (`lookup(text, placeholders=())`, `lookup_segments(segments)`, `terimler`, `len`) ve `terimleri_gom(segments, hits)`; yardimci `ilk_harfi_buyut`, kayit tipi `SozlukTerimi`. Garanti alani modul docstring'i (K1-K7, her karar yaninda test adi ya da `[ÖLÇÜLMÜYOR]`).

## K1-K7 nasil karsilandi

| K | uygulama | olcu |
|---|---|---|
| K1 esleme | NFC metin uzerinde TEK ileri-bakisli TRIE deseni (`re.IGNORECASE`, metin kucultulmez); konum basina en uzun terim + onek tablosundan kisa adaylar -> aday kumesi tam; `(uzunluk azalan, start artan)` isleme, ortusen/korunan aday atlanir; iki ucta sinir sarti: metin ucu, `isspace`, `P*`, JP parcacik (iki tarafta), KR ek (sagda, ekten sonra da sinir, en fazla 2 ek), komsu sozluk terimi, yer tutucu ucu; kelime siniri meta-karakteri yok; `source_term` = metindeki dilim; donus `start` artan, `segment_index=None` | 13 negatif + 21 pozitif sinir ornegi ayri kimlikle; 10 JP parcacik ve 18 KR ek her biri ayri; `長老マルクス`/`マルクス長老` iki hit; `水車小屋`/`水車` iki JSON sirasi; `Marcus`/`Marcus Aurelius` (kisa terim gecerli sinirda da atlanir; uzun sinirdan duserse kisa bulunur); `old mill house` (soldan tarama degil global uzunluk); harf durumu farkli onek terimleri (3 terim, 2 dal); `İstanbul`/`ﬁ` casefold tuzagi (indeks 17..21); `i/I/İ/ı` sinifi; n gecis n hit; astral kodpoint; bos sozluk/metin; kaynakta `\b` yok |
| K2 gomme | `segment_index` gruplama, `start` AZALAN uygulama, `dataclasses.replace(seg, text=...)`; hit'siz segment ve bos hits `is`; tam esitlik / aralik / ortusme / yer tutucu / tip denetimleri `ContractViolation`; mesajlar yalniz sayi+tip | G1'in 6 cumlesi lookup->gom; iki hit basta+sonda (start-artan ayrisir); uc hit; verilis sirasi bagimsiz; coklu segment; her denetim ayri test; 5 nobetcili mesaj testi |
| K3 yer tutucu | `placeholders` tum gecisleri korunan aralik; kismi ortusme de atlanir; uclari sinir; gom `segment.placeholders` ile ayni kural -> `ContractViolation` | `{PLAYER}は村にいます` (+/- placeholders pozitif kontrol), `{0}マルクス`, iki gecis, kismi ortusme, bos dize, gom ortusme/bitisik/segment-bazli |
| K4 buyuk harf | `ilk_harfi_buyut`: ilk kodpoint `upper`, `i`->`İ`; yuklemede VE gomde | 10 buyutme ornegi; lookup target_term; elle kurulan hit; zaten buyuk aynen; `terimler` ozelligi |
| K5 saf/hizli | I/O yalniz `__init__`; AST: lookup/gom/lookup_segments/ilk_harfi_buyut govdesinde I/O ve import yok, modulde print/logging/warnings/sys/os yok, modul duzeyi yalniz Final/TypeAlias; deterministik; 1000x50 < 50 ms | AST testleri (pozitif kontrol: yukleyicide `read_bytes` + `json.` VAR), iki cagri esit, iki store bagimsiz, dosya silinse lookup calisir, capfd+caplog+handle kancasi+warnings sifir sizinti (yukleme+lookup+gom+2 hata yolu), repr terim basmaz, 3 sure testi (50 terim / kapi yolu / 500 terim) |
| K6 yukleme/sema | `read_bytes` + `json.loads(bayt)` (BOM), `FileNotFoundError` sarilmaz, bozuk JSON ValueError; kayit semasi: eksik/tip/bos/bas-son bosluk, tek kodpoint (opt-in `kisa_terim_izni`), tekrar (kanonik anahtar), hedefte `.!?。！？` ve `{}`, `not` str/null, izin bool, bilinmeyen anahtar; NFC iki tarafta; `terimler` uzunluk-azalan, degismez | 27 red sinifi ayri kimlikle (mesajda terim/alan); 6 terminator ayri + 7 terminator-olmayan isaret kabul; 4 tekrar cifti; izin ile kabul/uzun terimde zararsiz/`false` acikca red; `not` -> `note`; ust duzey 4 red + ek anahtar serbest; NFD sozluk / NFD metin / NFD segment gom / NFD hedef / NFD source_term; ASCII-disi dizin (`çeviri/sözlük/オヤ.json`); BOM; `read_bytes` AST; dosya yok; bozuk JSON; `str` yol / `None`/`bytes` TypeError; ilk hatali kayit bildirilir |
| K7 segment_index | `None`/`bool`/`int` degil/aralik disi -> `ContractViolation`; bir hit gecersizse butun cagri duser | `None`, `-1`, `len`, `len+1`, `True`, `0.0`; diger hitler dogruyken de ihlal; son gecerli indeks kabul |

## Kapi itirazi (real_check.py -- sefe ait, koşuldu, yazilmadi)

Sefin kapisi **10/12 ok, 2 IHLAL**; ikisi de kapinin kendi hatasi, ikisi de gercek modelle olculdu (`evidence/kapi-itirazi-3c-6a.txt`):

1. **#6a** -- `chr(44608)` = **U+AE40**; gecici sozluge yazilan terim **U+AC80** (farkli hece). Modulun mesaji gercek terimi tasir (`True`), U+AE40'i tasimaz (`False`). Kapi yanlis kod noktasini ariyor.
2. **#3c** -- `cevir()` segmentlere `placeholders` vermiyor. Ham ceviride de `{0}` yok (dusus modelin, gommeden bagimsiz); gomulu+yer tutucusuz (kapinin yolu) `{0}` yok; gomulu + `placeholders=('{0}',)` -> `{0}` var, `Marcus` var. Paket K3 "real_check #3 segmentlere placeholders verir" der; kod vermiyor.

Iki satiri duzeltilmis **kopya** (`evidence/real_check-duzeltilmis-kopya.py`, fark `.diff`) **TEMIZ 12/12**, #7 medyan 35.1 ms. Sefin dosyasina dokunulmadi.

## Paket ile olcum celiskisi

K1 OLCU satirindaki `검은 옷 -> eslesmez`, `검사` ile ayni sinifta degil: gercek ek `은` kuraldan gecer (K1 DEGISMEZ metninin "bilinen sinir"i, kapi #6c "1 hit (rapor)"). "Eslesmez" yalniz sema etkisiyle (izinsiz `검` reddedilir) dogru. Iki ayri test yazildi; DEGISMEZ metni ve kapi izlendi (ayrinti `known_gaps`).

## Mutant ayirt etme (ayna agaci, `evidence/mutant-ayirt-etme.txt`, test adlari `-hangi-testler.txt`)

| mutant | ne | dusen |
|---|---|---|
| M01 | sinir kurali kaldirildi (alt dize) | 20 |
| M02 | en-uzun-once ters | 3 |
| M03 | JP parcacik kumesi sinir degil | 23 |
| M04 | KR ek kurali kaldirildi | 32 |
| M05 | metin casefold'lanip aranir (indeks kayar) | 19 |
| M06 | NFC kaldirildi | 7 |
| M07 | start-ARTAN uygulama | 8 |
| M08 / M09 | buyuk harf kapali (gom / yukleme) | 1 / 3 |
| M10 | lookup placeholders yoksayildi | 6 |
| M11 | segment_index None sessizce yutuldu | 3 |
| M12 | tek kodpoint sema kontrolu kaldirildi | 9 |
| M13 / M14 / M15 | hedefte terminator / `{}` / tekrar kontrolu kaldirildi | 8 / 3 / 5 |
| M16 / M17 / M18 | gom: ortusme / tam esitlik / yer tutucu denetimi kaldirildi | 3 / 4 / 1 |
| M19 | bos hits -> kopya (is bozulur) | 1 |
| M20 | komsu terim siniri kaldirildi (sol+sag) | 5 |
| M21 | donus start-artan siralanmaz | 3 |
| M22 | KR ek zinciri derinligi 1 | 3 |
| M23 | yer tutucu ucu sinir degil | 1 |
| M24 | trie anahtari harf durumunu katlamaz | 1 |
| M25 | onek tablosu kullanilmaz (konum basina yalniz en uzun) | 1 |
| M26 | ekten sonra sinir sarti kaldirildi | 2 |
| M27 / M28 | SOL / SAG sinir kaldirildi | 6 / 15 |
| M29 | `start == end` kabul | 1 |
| M30 | Turkce `i` -> `İ` kaldirildi | 1 |
| M31 | lookup_segments segment_index doldurmaz | 4 |
| M32 | ortusme `<` -> `<=` (bitisik = ortusme) | 8 |
| C-1 / C-2 / C-3 | KONTROL: sort anahtari acik / `_ortusur` yanlari / KR ek dongusu kisa once (ozyineli tarama sirayi anlamsiz kilar) | 0 / 0 / 0 (kacti, dogru) |

Hicbir mutant sifir testle kacmadi; en dar ayirt etme 1 testle (M08, M18, M19, M23, M24, M25, M29, M30) -- her biri o mutant icin yazilmis adlandirilmis test.

## Sayilar

| olcu | sonuc |
|---|---|
| birim | 256 passed; kapsam %100 (301 ifade); mypy --strict modul + test temiz |
| tam takim | 1700 passed, dusen yok |
| real_check (sef) | 10/12 ok; 2 IHLAL = kapi hatasi (#3c placeholders, #6a kod noktasi) |
| real_check (duzeltilmis kopya) | TEMIZ 12/12; #7 35.1 ms |
| sure (izleyicisiz) | 1000 seg x 11/50/500 terim: lookup_segments+gom 15-16 ms, kapi yolu 18-22 ms |
| mutant | 32/32 yakalandi, 3/3 kontrol kacti |
| cp1254 | 256 passed, `PYTHONIOENCODING` yok |
