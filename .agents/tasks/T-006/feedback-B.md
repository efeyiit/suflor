# T-006 — Tester-B geri bildirimi (tur 1 → tur 2)

**Kime:** implementer (tur 2, taze ajan). **Elinde bundan başka bağlam yok; her şey burada.**
**Ne değişmeli:** yalnız `tests/unit/ocr/test_rapid_engine.py` (owns içinde). `src/ocr/rapid_engine.py` **doğru** — motor koduna dokunman gerekmiyor (aşağıdaki mutantlar motorun bozulmuş kopyalarıdır, teslim ettiğin motor değil).

## Ret gerekçesi (tek sınıf, üç mutant) + bir ikincil bulgu (K10)

K7 değişmezi: *"`rapid_engine.py`'de `print` yok; hiçbir `logging` çağrısına blok metni girmez"*. Ölçün paketin lafzına birebir uyuyor (AST: `print` sayısı 0 + `logging` argümanında `.text`/`txts` yok; çalışma zamanı: `caplog.at_level(DEBUG, logger="RapidOCR")` altında nöbetçi). Ama bu ölçü **mekanizma adı** ile kancalanmış (§4.6/7): `print` adı, `.text`/`txts` alt dizgisi, `RapidOCR` logger adı. Değişmezin kendisi kanal-bağımsız: *motor OCR metnini hiçbir çıkış kanalına yazmaz*. Aşağıdaki üç mutant motora blok metnini yazdırıyor ve **beş kabul kapısının beşinden de geçiyor** (`tester_B_evidence/B1-mutant-kiti.txt`):

| mutant | motor kopyasına eklenen satır | 5 kapı | üründe ne olur |
|---|---|---|---|
| **M25b** | `recognize` sonunda `sys.stdout.write(bloklar[0].text if bloklar else '')` (+ `import sys`) | `[.....]` | OCR metni stdout'a; cp1254 konsolda Japonca/Korece metin **`UnicodeEncodeError`** (paketin kendi "Windows tuzakları" maddesi); `pythonw`/pencereli pakette `sys.stdout is None` → **her `recognize` `AttributeError`** |
| **M28b** | `_bloklara_cevir` döngüsünde `logging.getLogger(_LOGGER_ADI).info("blok %s", metin)` | `[.....]` | Motor `RapidOCR` logger'ını ERROR'a çektiği için sessiz; uygulama o logger'ı açarsa (debug modu) metin **stderr'e** (logger'ın kendi StreamHandler'ı, `propagate=False`) |
| **M28c** | aynı yerde `logging.getLogger("suflor.ocr").debug("blok %s", metin)` | `[.....]` | Kök logger DEBUG'a açılınca (uygulama debug modu / dosya logu) OCR metni **log dosyasına** — PROTOKOL §6.7 ihlali |

Neden kaçıyorlar: (1) AST testi yalnız `print` adını sayıyor — `sys.stdout.write`, `sys.stderr.write`, `os.write` görünmez; (2) AST'nin `logging` denetimi `.text`/`txts` alt dizgisine bakıyor — döngü değişkeni `metin` görünmez; (3) çalışma zamanı testi `caplog.at_level(..., logger="RapidOCR")` ile **yalnız o logger'ı** açıyor ve motor kurulumdan sonra onu zaten ERROR'a çekiyor — motorun kendi logger'ı, uygulama logger'ı ve stdout/stderr hiç gözlenmiyor; `capsys` yok.

Karar eşiği (şef): *"Ret = ürünü bozan bir mutant beş kapıdan da geçiyor **ve** o sınıf üründe erişilebilir."* M25b her dolu karede tetiklenir → ret.

M25b'nin ürün etkisi **ölçüldü** (`tester_B_evidence/B1c-M25b-urun-etkisi.txt`): gerçek model + stdout dosyaya yönlendirilmiş (cp1254) → `UnicodeEncodeError` (ham, `OcrError` bile değil); `sys.stdout = None` → `AttributeError: 'NoneType' object has no attribute 'write'`.

**İkincil (K10, aynı turda kapat):** **M32** — `close()` `_kapali = True` yapıyor ama `self._taniyici = None` yapmıyor → beş kapı da geçiyor `[.....]`. Dışarıdan `recognize` → `OcrError` göründüğü için 95 test ayırt edemiyor; ama K10'un lafzı "tanıyıcıyı bırakır" ve gerçek yolda bırakılmayan şey det+rec+cls ONNX oturumlarıdır (dil değişiminde eski motor referansta kalırsa bellek). Ölçüsü ucuz: fabrikanın döndürdüğü tanıyıcıya `weakref`, `close()` + `gc.collect()` sonrası ölmeli (`test_mercek_B.py::test_b5_close_taniyiciyi_gercekten_birakir`, M32'yi yakalıyor — `B1b-mercekB-ayirt-etme.txt`). Ürünü bozmadığı için tek başına ret sebebi değil; ret zaten açıkken bu turda kapatılmalı.

## Ne yazılacak (öneri; eşdeğer başka ölçü de kabul)

**1 · Tek çalışma-zamanı testi**, kanaldan bağımsız — `tests/unit/ocr/test_rapid_engine.py`'ye:

```python
@pytest.mark.parametrize("seviye", [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR])
def test_k7_hicbir_kanala_metin_yazilmaz(tmp_path, caplog, capsys, seviye):
    nobetci = "NOBETCI-7f3a"
    lg = logging.getLogger(LOGGER_ADI)
    def _kutuphane_gibi():            # rapidocr utils/log.py: INFO, propagate=False, kendi stderr handler'i
        lg.setLevel(logging.INFO); lg.propagate = False
        if not lg.handlers: lg.addHandler(logging.StreamHandler())
    f = SahteFabrika(cikti((kutu(0, 0, 5, 5), nobetci, 0.9)), kurulumda=_kutuphane_gibi)
    m = motor(tmp_path, f)
    m.recognize(kare(), OcrPreset.DIALOGUE)          # kurulum: motor RapidOCR'u ERROR'a ceker
    caplog.clear(); caplog.set_level(seviye)         # KOK logger (uygulama debug modu)
    for ad in (LOGGER_ADI, "src.ocr.rapid_engine", "suflor", "suflor.ocr", "rapidocr"):
        logging.getLogger(ad).setLevel(seviye)       # kurulumdan SONRA acilir; ikinci recognize fabrikayi cagirmaz
    try:
        [b] = m.recognize(kare(), OcrPreset.DIALOGUE)
    finally:
        for ad in ("src.ocr.rapid_engine", "suflor", "suflor.ocr", "rapidocr"):
            logging.getLogger(ad).setLevel(logging.NOTSET)
        for h in list(lg.handlers): lg.removeHandler(h)
        lg.propagate = True; lg.setLevel(logging.NOTSET)
    assert b.text == nobetci
    assert all(nobetci not in r.getMessage() for r in caplog.records)
    out, err = capsys.readouterr()
    assert out == "" and err == ""
```

**2 · K10 bırakma testi** — sahte fabrika döndürdüğü tanıyıcıyı `self`'te TUTMASIN (aksi hâlde weakref hep canlı kalır; `SahteFabrika._tani` kapanışı zaten taze üretiliyor, yalnız `weakref.ref(_tani)` kaydet):

```python
def test_k10_close_taniyiciyi_birakir(tmp_path):
    f = SahteFabrika(); m = motor(tmp_path, f)
    m.recognize(kare(), OcrPreset.DIALOGUE)
    ref = weakref.ref(m._taniyici)          # ya da fabrikanin kaydettigi weakref
    m.close(); gc.collect()
    assert ref() is None
```

Kritik noktalar (test 1): (a) logger'lar **kurulumdan sonra** açılır (motor `_taniyici_al`'da seviyeyi bir kez çeker; ikinci `recognize` fabrikayı çağırmaz, dolayısıyla seviye açık kalır — M28b böyle görünür); (b) `RapidOCR` logger'ı gerçek kütüphane gibi kurulur (`propagate=False` + StreamHandler) ki metin caplog'a değil **stderr'e** gitsin ve `capsys` yakalasın; (c) kök logger `caplog.set_level(seviye)` ile açılır (M28c); (d) `capsys` stdout/stderr'i ölçer (M25b). İsteğe bağlı: AST testine `sys.stdout`/`sys.stderr`/`os.write` adlarını da yasakla — ama asıl ölçü çalışma zamanı olanıdır.

## Düzeltmenin ayırt etme gücü — ölçüldü

Yukarıdakiyle aynı düzenek `.agents/tasks/T-006/tester_B/test_mercek_B.py::test_b4_her_seviyede_nobetci_hicbir_loga_ve_stdout_stderr_e_dusmez` olarak yazıldı ve ayna ağacında mutantlara karşı koşuldu (`tester_B_evidence/B1b-mercekB-ayirt-etme.txt`):

| mutant | 5 kapı | mercek B testi |
|---|---|---|
| M25 (`print`) | `[.X.XX]` | X (4/4 seviye) |
| **M25b** (`sys.stdout.write`) | `[.....]` | **X** (4/4 seviye) |
| M28a (modül logger WARNING) | `[.X.XX]` | X |
| **M28b** (RapidOCR logger INFO) | `[.....]` | **X** (DEBUG, INFO) |
| **M28c** (uygulama logger DEBUG) | `[.....]` | **X** (DEBUG) |
| **M32** (close bırakmaz) | `[.....]` | **X** (`test_b5_close_taniyiciyi_gercekten_birakir`) |
| M29/M30/M31 (K10 diğer) | `[.X.XX]` | X |
| C01–C04 (davranış-eşdeğer kontrol) | `[.....]` | . (kaçtı — yanlış pozitif yok) |

## Yeniden üretim (kendin koş)

```
python .agents/tasks/T-006/tester_B/mutant_kiti.py M25b M28b M28c M32              # bes kapi, ayna agacinda (~2 dk)
python .agents/tasks/T-006/tester_B/mercekB_mutant_ayirt_etme.py M25b M28b M28c M32 C01   # mercek B testleri
python .agents/tasks/T-006/tester_B/mutant_kiti.py                                   # tam kit, 51 mutant (~23 dk)
```

Ham çıktı: `tester_B_evidence/B1-mutant-kiti.txt` (M25b/M28b/M28c/M32 satırları `[.....]`), `tester_B_evidence/B1b-mercekB-ayirt-etme.txt`, `tester_B_evidence/B1c-M25b-urun-etkisi.txt`.

Tur 2 kabulü için benim koşacağım: tam kit yeniden (M25b/M28b/M28c/M32 → en az `G2-birim` X), C01–C04 hâlâ `[.....]`, 95+N passed, kapsam ≥ 90, tam takım yeşil.

**Not (kit):** `real_check.py` cp1254 stdout'ta `≈` (U+2248) yüzünden çöker; kit ve bu ölçümler `PYTHONIOENCODING=utf-8` ile koşuldu (`tester_B_evidence/taban-3-real_check.txt` çökmeyi, `taban-3b-real_check-utf8.txt` 16/16 TEMİZ'i gösterir). Sen de kabul komutu #3'ü o değişkenle koş; bu şefin dosyası, dokunma.

## Tur 2'de yapılmayacaklar

* Motor kodunu değiştirme — 47 davranış mutantının 43'ü yakalanıyor (kaçan 4'ün hepsi ölçü kusuru, motor doğru), 4 kontrol mutantı kaçıyor (yanlış pozitif yok); K1/K2/K3/K4/K5/K6/K11 ölçüleri keskin.
* `real_check.py`, `conftest.py` — şefe ait.
* Yeni `# pragma: no cover` ekleme.
