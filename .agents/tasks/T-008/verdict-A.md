---
task: T-008
role: tester
round: 1
lens: "A — geometri (K2/K7), betik (K3), sözleşme (K5/K6/K8); gerçek OCR ayrı süreç"
decision: ret
checks:
  - name: "taban: mypy --strict temiz"
    cmd: "python -m mypy --strict --explicit-package-bases src/ocr/satir_birlestirici.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/00-taban-mypy.txt
  - name: "taban: implementer birim testleri 68 passed"
    cmd: "python -m pytest tests/unit/ocr/test_satir_birlestirici.py -q -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/01-taban-birim.txt
  - name: "taban: real_check TEMİZ (KR 17→4 [2,5,5,5]; JP/EN no-op; normalize 2 segment; tek-kelime 0; menü KR 13→9 EN 8→8; 1-em 4→4; saflık; 5.1 ms)"
    cmd: "python .agents/tasks/T-008/real_check.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/02-taban-real_check.txt
  - name: "taban: tam takım 1427 passed"
    cmd: "python -m pytest tests -q -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/03-taban-pytest-tum.txt
  - name: "tester-A: 84 kör test (A0 bariyer pozitif kontrolü, A1–A5), kendi bariyeri altında tek başına"
    cmd: "python -m pytest .agents/tasks/T-008/tester_A/test_mercek_a.py -q -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/testerA-mercek-a-pytest.txt
  - name: "tester-A: şefin dizini + tester_A birlikte 391 passed (iki bariyer çakışmıyor)"
    cmd: "python -m pytest tests/unit/ocr .agents/tasks/T-008/tester_A/test_mercek_a.py -q -p no:cacheprovider"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/testerA-birlikte-pytest.txt
  - name: "tester-A: yalnız kendi testlerinin kapsamı %100 (95/95 ifade)"
    cmd: "python -m pytest .agents/tasks/T-008/tester_A/test_mercek_a.py -q -p no:cacheprovider --cov=src.ocr.satir_birlestirici --cov-report=term-missing"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/testerA-cov.txt
  - name: "tester-A: test dosyaları mypy --strict temiz"
    cmd: "python -m mypy --strict --explicit-package-bases .agents/tasks/T-008/tester_A/test_mercek_a.py .agents/tasks/T-008/tester_A/test_ret_a_uzun_kutu_koprusu.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/testerA-mypy.txt
  - name: "A6 gerçek OCR (ayrı süreç): T-006/T-008 fixture'ları + 20 kendi fixture'ım — 3 YANLIŞ BİRLEŞME/AYRILMA (solda iki satırı kaplayan büyük etiket, KR)"
    cmd: "python -X utf8 .agents/tasks/T-008/tester_A/a6_gercek_ocr.py"
    exit_code: 1
    result: kaldi
    evidence: tester_A_evidence/a6-gercek-ocr.txt
  - name: "RET kanıtı (sentetik, gerçek OCR geometrisi): etiketsiz 3/3 geçer (pozitif kontrol), etiketli 3/3 düşer"
    cmd: "python -m pytest .agents/tasks/T-008/tester_A/test_ret_a_uzun_kutu_koprusu.py -q -p no:cacheprovider"
    exit_code: 1
    result: kaldi
    evidence: tester_A_evidence/testerA-ret-uzun-kutu-pytest.txt
  - name: "aday düzeltme prototipleri (ayna, depo src/ dokunulmadı): E → 68/68 + ret 6/6 geçer + gerçek OCR exit 0; D → implementer fixture'ını bozar"
    cmd: "TESTER_A_KOK=<ayna_E> python -X utf8 .agents/tasks/T-008/tester_A/a6_gercek_ocr.py"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/a6-aday-E-gercek-ocr.txt
  - name: "aday prototipleri birim sonuçları + diff'ler"
    cmd: "(ayna_E / ayna_D içinde) python -m pytest tests/unit/ocr/test_satir_birlestirici.py -q; TESTER_A_KOK=<ayna> pytest tester_A"
    exit_code: 0
    result: gecti
    evidence: tester_A_evidence/aday-duzeltme-prototipleri.txt
blocking_issues:
  - "B1 · Uzun kutu köprüsü GERÇEK OCR'da ürünü bozuyor: solda iki satırı kaplayan büyük etiket (2× font, dikey ortalı) + sağda iki KR satırı → tespitçi 11 kutu (etiket + 5 + 5) verir; birleştirici 3/3 fixture'da satır bütünlüğünü bozar — `kr_etiket_ortali_60_45_10`: 11 → 1 blok, iki satırın kelimeleri x sırasında İÇ İÇE (parça satırları [0,1,0,0,1,0,1,0,1,1,0]); `kr_etiket_ortali_72_48_14`: 11 → 9 blok; `kr_etiket_ortali_60_40_8`: 11 → 10 blok (kelime-kelime çeviri, S3 sınıfı). Aynı görüntü etiket karartılınca 10 → 2 blok DOĞRU. Sebep: etiket kutusu `(y,x)`-ilk blok olunca satır bölümlemesi (adım 3, 'satırın ilk bloğuyla örtüşme') iki satırı tek satıra toplar; satır içi `(x,y)` sıralaması iki satırın kelimelerini karıştırır. Docstring bu bölgeyi `[ÖLÇÜLMÜYOR] gerçek OCR'da (fixture yok)` bırakmıştı — fixture artık var (`tester_A/fixtures/kr_etiket_ortali_*.png`), sınıf ölçüldü. Yeniden üretim + ayırt etme ölçüsü + iki aday yön: `feedback-A.md`."
---

# T-008 · Tester-A (mercek A) · tur 1 · **RET**

Kör çalıştım: `packet.md` v2, `olgular.txt`, `krt-1.md`, modül docstring'i (garanti alanı), kod, `real_check.py`, `conftest.py`. Şefin talimatı gereği `delivery.md` `known_gaps`'i **bütün ölçümlerim bittikten sonra** okudum (aşağıda §7); kararımı değiştirmedi. `tester_B/` okunmadı.

## 1 · Taban şefinkiyle birebir (kendi elimle)

mypy 0 · 68 passed · `real_check` TEMİZ (KR 17→4 `[2,5,5,5]`, JP/EN no-op, 2 segment, tek-kelime 0, menü KR 13→9 / EN 8→8, 1-em 4→4, saflık, 1000 blok 5.1 ms) · tam takım 1427. Teslim bu oturumda değişmedi (`fe01641`, md5 `ff3ddf2d…`).

## 2 · A1 — K2 geometri, eşik sınırları (84 testin 30'u)

Ölçüldü, docstring'le **uyumlu**:
- Dikey `0.49/0.50/0.51×h` → 2/1/1 blok (`>=`); yatay `74/75/76` (h=100) → 1/1/2 (`<=`); `min(h)` küçük kutuyla (`0.75×10=7.5`: 7 birleşir, 8 ayrılır); Y2 fixture'ı orijinal yükseklikle (`A b`, `C`).
- Eşit `x` → yeni grup (iki yönde); çakışma −1/−h/−2h → komşu, bbox birleşimi doğru; iç içe kutu x ilerliyorsa birleşir (belgeli sınır), aynı x'te ayrı.
- Yozlaşmış `(w,h) ∈ {(50,0),(0,20),(50,−5),(−5,20),(0,0),(−1,−1)}` → aynen geçer (`is`), araya girince `A B`'yi ayırmaz.
- `monitor_index` / `dpi_scale` farkı → ayrı; aynı yüzey → birleşir; iki monitörde aynı koordinat → girdi indeksi sırası.
- Zincir A–B, B–C komşu, A–C değil → tek blok. Dar satır aralığı: örtüşme 0.45h → iki satır korunur; 0.55h → çapraz birleşme (belgeli; gerçek düzende A6: 1.0×font pitch'te bile satırlar korundu, dolayısıyla ürün sınıfı değil).
- **Uzun kutu köprüsü, T en solda ve en üstte:** `T(0,0,40,60) a(50,5) c(110,40)` → **`T a c` tek blok** (a ve c farklı satır); iki satır × iki kelime + T → `T a1 | a2 | c1 | c2` (T'siz `a1 a2 | c1 c2`). Implementer'ın fixture'ı T'yi **ortaya** koyuyordu (`a T`, `c` — doğru); T ilk blok olunca sınıf açılıyor. Sentetik kayıt `test_a1_uzun_kutu_*_SINIF`; gerçek OCR karşılığı §6 → **B1**.

## 3 · A2 — satır bölümleme vs satır içi sıralama

- KR satır 3 (y 212/209/209/208/210) 120 permütasyonda tek blok, `line_boxes` x sırasında `[82,225,305,386,467]`; 17 kutu 20 karışık sırada `[2,5,5,5]`, y ve x sıralı. İtiraz 1'in gerekçesi (paket lafzı 17→9) kendi ölçümümle **tutuyor**.
- Titreşim tam 0.5h → tek blok; > 0.5h → satırlar ayrılır (gerçek titreşim 1–4 px / 33–41 px, sınıf değil).
- Satırın ilk bloğu kısa (h=12 tırnak) → `0.5×12=6` ile ölçülür, satır bütün; sonraki satırı çekmez.

## 4 · A3 — K3 betik (21 satırlık tablo + boş parça)

`unicodedata.name`: yarım genişlik katakana `ｶﾀｶﾅ`+`ｶﾅ` boşsuz; tam genişlik `ＨＰ`+`が` boşluk; Hangul Jamo / uyumluluk Jamo boşluk; uyumluluk ideografı `豈` CJK; emoji ve ZWJ dizisi harfsiz → LATIN → boşluk; `「マルクス」`+`と` boşsuz (ilk HARF マ); `第３章`+`開始` boşsuz; `村の`+`HP` → `村の HP`; `HPが`+`減った` → boşluk (K3 tanımı, belgeli); `ー` CJK, `々` LATIN (docstring `[ÖLÇÜLMÜYOR]`); harfsiz `。` iki yönde boşluk (belgeli sınır); ZWSP strip edilmez; iç `\n` korunur; baş/son boşluk strip. Boş/yalnız-boşluk/ideografik-boşluk parça metne katılmaz, kutu/`line_boxes` sayımına katılır, betik bağlamını taşımaz (`村`+``+`HP` → `村 HP`; `村`+``+`の` → `村の`). **Sapma yok.**

## 5 · A4 / A5 — K5 alanlar, K6 okuma sırası

- `confidence`: NaN başta/ortada/sonda → NaN-dışı min, hepsi NaN → NaN; `inf` → diğerinin min'i; `−inf`/negatif → aynen (aralık denetimi yok, belgeli); `[nan, inf] → inf`. bbox dört alan `type is int`, `json.dumps(asdict())` geçer; negatif koordinat + monitör 1 normal; tek parça `is` ve `line_boxes` dokunulmaz; **önceden birleşik girdi** (ikinci uygulama) → `line_boxes` parçaların bbox'ları, iç yapı kaybolur (K4/K5 belgeli). Girdi değişmez, çıktı deterministik, demet girdi kabul.
- K6: 3×3 karışık 50 permütasyon aynı; bağlı `(y,x)` → girdi sırası; aynı satırda sağ grup `min y` küçükse önce (belgeli).
- **K6 docstring cümlesi fazla geniş (yükümlülük, ret değil):** "`(y,x)` bağı olmayan girdide her permütasyon AYNI listeyi verir" — karşı örnek `C(0,0,10,30) A(0,10,10,20) B(20,0,10,20)`: girdide bağ yok, ama `A+B` birleşik bbox'ı `(0,0)` olur ve C ile **çıktı anahtarında** bağ doğar → `[C, A B]` vs `[A B, C]` (3000 rastgele girdide 1 kez, yalnız bu sınıftan; `test_a5_*POZITIF_KONTROL` ve fuzz testi sabitledi). Ürün etkisi yok (normalizer `(y,x)` ile yeniden sıralar); cümle "iki **çıktı** bloğunun `(y,x)`'i eşitse girdi sırasına bağlı" diye yazılmalı.

## 6 · A6 — gerçek OCR, ayrı süreç (`a6_gercek_ocr.py`, 20 fixture)

Referans kanal bağımsız (§4.6/8): çizilen satır merkezleri (çizim parametresi), uygulama çıktısından değil. Ölçü: hiçbir çıktı bloğu iki çizilen satırdan **kelime** kutusu içermez; tek sütunlu KR fixture'larda her satırın kelimeleri tek blokta.

| Fixture | Kutu → blok | Sonuç |
|---|---|---|
| dlg_KR / JP / EN, menü KR/EN, 1-em | 17→4 `[2,5,5,5]` / 4→4 / 4→4 / 13→9 / 8→8 / 4→4 | taban; **iç içe/çakışan kutu çifti yok** (tespitçi vermiyor) |
| KR dar satır aralığı 1.1×font | 15→3 `[5,5,5]` | doğru |
| JP dar 1.1×font | 3→3 | no-op |
| KR 1.0×font (aşırı dar; tespitçi tek uzun kutu + çakışan parça verdi) | 16→3 | doğru (şans: uzun kutu ilk blok değildi) |
| EN iki sütun menü, boşluk 30/40 px (~1.0–1.4×h) | 8→8 | etiket|değer birleşmez |
| KR tek uzun satır 2000 px (15 kelime) | 15→1 (w=1801) | doğru |
| EN tek uzun satır | 1→1 | no-op |
| KR büyük etiket solda, **üst hizalı** (4 varyant) | 3/3/3/2 blok | 3'ünde satırlar bütün + etiket ayrı; 72_48'de etiket satır 0'a yapıştı (kabul edilebilir) |
| **KR büyük etiket solda, dikey ORTALI (3 varyant)** | **11→1 (iç içe) / 11→9 / 11→10** | **B1 — etiketsiz aynı görüntü 10→2 doğru** |
| JP büyük etiket ortalı | 5→3 | etiket 3 kutuya bölündü ve kendi içinde birleşti; satırlar bütün (geometri: örtüşme 9 < 16 kurtardı) |
| KR standart (üstte konuşmacı, pitch 1.6×) | 12→3 `[2,5,5]` | doğru |

Fail koşulu ölçüldü: etiket kutusunun üstü satır 0'ın kutu üstünden **yukarıda** (etiket `(y,x)`-ilk blok olur) **ve** altı satır 1'in kutusuna `≥ 0.5×min(h)` sarkıyor. Dikey ortalı 2× etiket bu koşulu **her zaman** sağlar (üst hizalı etikette büyük fontun iç boşluğu üstü 2–6 px aşağı ittiği için 3/4 kurtuldu). Ürün düzeni: durum ekranı/başarım/liste satırı gibi "solda büyük etiket/sayı, sağda iki satır" — diyalog kutusu (ürünün ana yolu) etkilenmez, ama S3'ün (kelime-kelime çeviri) aynısı bu düzende geri geliyor; 60_45_10'da daha kötüsü: iki cümlenin kelimeleri karışık tek metin.

**Aday yönler (ayna, `src/` dokunulmadı; mekanizma seçimi implementer'ın):** **E** — satır bölümlemesinde referans = satırın **en kısa** bloğu (bağ: ilk): implementer 68/68, benim ret dosyam 6/6, gerçek OCR **exit 0** (dlg_KR `[2,5,5,5]`, 1-em 4→4, etiketli 2–3 blok satırlar bütün). **D** — `h > 1.5×medyan` kutu yalnız geçer: ret dosyası geçer ama implementer'ın `a T | c` fixture'ını ve `min(h)` küçük-kutu sınırını bozar. Diff'ler ve sonuçlar `aday-duzeltme-prototipleri.txt`.

## 7 · `delivery.md` `known_gaps` ile tutarlılık (ölçümlerden SONRA okundu)

İtiraz 1 (paket lafzı 17→9) ve İtiraz 2 (13–16×h menü 10.0'ı ayıramaz; 1-em fixture'ı gerekli) kendi ölçümlerimle **tutarlı**; `real_check` #4c bunu kapatmış. `[K2 — GRİ BÖLGE KAYDI]` uzun kutu köprüsünü "gerçek OCR'da fixture yok `[ÖLÇÜLMÜYOR]`" diye bırakıyor — **fixture artık var, sınıf ölçüldü** (§4.6/10: damga ölçüm değildir). KRT O2'nin çakışma sınırı önerisi pakete girmemişti; benim ölçümüm çakışma sınırının **yetmeyeceğini** de gösteriyor (x-ilerleyen ama satır 1'e ait kutu −147 px boşlukla birleşiyor; sınır konsa satırlar bu kez parçalanır — sorun grup değil **satır** bölümlemesinde).

## 8 · Yükümlülükler (ret dışı, karara yazılmalı)

1. K6 docstring cümlesi çıktı anahtarı üzerinden (§5).
2. Gri bölge `[0.6, 0.95]×h` paketten geliyor `[ÖLÇÜLMÜYOR]` — hizalanmış (justified) metinde kelime boşluğu bu bölgeye girebilir; bu turda ölçülmedi.
3. Düzeltme sonrası benim `test_a1_uzun_kutu_*_SINIF` iki testim (mevcut bozuk davranışı sabitliyor) **bayatlar** — düzeltme turunda `test_ret_a_uzun_kutu_koprusu.py` tek ölçü olur, o ikisini ben yeniden yazarım (§4.6/5).

`git status --short -- src tests` boş; `git commit` yok; ayna ağacı scratchpad'de.
