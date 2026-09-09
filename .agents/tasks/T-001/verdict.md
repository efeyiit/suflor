---
task: T-001
role: tester
round: 1
decision: onay
checks:
  - name: "mypy --strict temiz"
    cmd: "python -m mypy --strict src/contracts"
    exit_code: 0
    result: gecti
    evidence: tester_evidence/mypy.txt
  - name: "implementer test paketi (bagimsiz calistirildi, okunmadan)"
    cmd: "python -m pytest tests/unit/contracts -q"
    exit_code: 0
    result: gecti
    evidence: tester_evidence/pytest.txt
  - name: "saflik denetimi (purity_check.py)"
    cmd: "python .agents/tasks/T-001/purity_check.py"
    exit_code: 0
    result: gecti
    evidence: tester_evidence/purity_check.txt
  - name: "tester'in kendi bagimsiz test paketi (140 test, 5 dosya)"
    cmd: "python -m pytest .agents/tasks/T-001/tester_tests -q"
    exit_code: 0
    result: gecti
    evidence: tester_evidence/tester_pytest.txt
blocking_issues: []
---

# Gerekce

## Yontem

`delivery.md` ve `evidence/` **okunmadi** (korluk kurali). Yalnizca
`packet.md`, `env.md`, `.agents/PROTOKOL.md` §4, tasarim dokumani §5.3 ve
`src/contracts/` + `tests/unit/contracts/` altindaki kodun kendisi okundu.

Uc kabul komutu bagimsiz olarak yeniden calistirildi (implementer'in
`evidence/`sine guvenilmedi). Ardindan `.agents/tasks/T-001/tester_tests/`
altina implementer'in test dosyalari OKUNMADAN, dogrudan packet.md + env.md +
tasarim dokumani §5.3'ten transkribe edilerek 5 bagimsiz test dosyasi
yazildi (140 test): `test_tester_frozen.py`, `test_tester_alignment.py`,
`test_tester_errors.py`, `test_tester_conformance.py`,
`test_tester_hash_safety.py`.

## Dusmanca dogrulama sonuclari (bozmaya calisildi, bozulamadi)

1. **Frozen davranissal olarak dogrulandi** -- implementer'in testinin
   aksine yalnizca ilk alan degil, 8 modelin **her alani** icin ayri ayri
   `setattr`/`delattr` denendi (41 parametrize test). Hepsi
   `dataclasses.FrozenInstanceError` firlatti. `dataclasses.replace()`
   ile dogru kacis yolunun calistigi da ayrica dogrulandi.

2. **FakeProvider hizalamasi** -- 0, 1, 2, 3, 10, 17 segmentle test edildi;
   `len(translations) == len(segments)` her seferinde tutuyor. Ayrica
   `ensure_aligned` FakeProvider'dan bagimsiz, elle kurulmus uyumsuz
   `(segments, translations)` ciftleriyle (0/1, 1/0, 3/2, 3/4, 1/100, 5/1)
   dogrudan sinandi -- her durumda `ContractViolation` firlatti. Siralama
   korunuyor, tekrarlanan metinli segmentler de dogru hizalaniyor.

3. **`image_crops` alani** -- `TranslationRequest` uzerinde var, tipi
   `tuple[ImageArray, ...] | None`, varsayilani `None`, hem `None` hem dolu
   demetle calisiyor.

4. **Hata hiyerarsisi** -- `TranslatorError.__subclasses__()` ile TAM
   OLARAK 6 dogrudan alt sinif dogrulandi (fazla/eksik yok):
   `CaptureError, ModelMissingError, OcrError, ProviderUnavailable,
   ProviderTimeout, ContractViolation`. Hiyerarsi duz (kardesler birbirinden
   turemiyor), hepsi tek bir `except TranslatorError` ile yakalanabiliyor,
   hepsi argumansiz olusturulabiliyor.

5. **Saflik -- iki bagimsiz yontemle** dogrulandi: (a) ham metin uzerinde
   regex taramasi (`importlib`, `__import__`, `eval(`, `exec(`, `compile(`),
   (b) AST duzeyinde `ast.Call` dugumlerinde `__import__`/`eval`/`exec`/
   `compile`/`importlib.import_module`/`importlib.reload` cagrisi arandi.
   Ikisi de temiz. Tum `import` satirlari gozle tarandi: yalnizca
   `abc`, `dataclasses`, `enum`, `typing`, `collections.abc`, `numpy`,
   `numpy.typing` ve goreli (`.errors`, `.models`, `.interfaces`) importlar
   var -- `purity_check.py`'nin izin verdigi kumeyle birebir uyumlu.

6. **ndarray tasiyan modellerin esitlik/hash guvenligi FIILEN calistirilarak**
   dogrulandi (yalnizca kod okunarak degil): `Frame` ve `TranslationRequest`
   farkli piksel icerigiyle karsilastirildiginda `==` skaler `bool` donduruyor
   ve `hash()` patlamadan calisiyor, `set`/`dict` anahtari olarak
   kullanilabiliyor. Bu, `compare=False` yanlis uygulansaydi runtime'da
   `ValueError`/`TypeError` ile patlayacak bir hata sinifidir.

7. **Tasarim dokumani §5.3 ile alan-alan karsilastirma** -- `Rect, Frame,
   TextBlock, Segment, TranslationRequest, TranslationResult` icin alan
   adlari VE sirasi tasarim dokumanindan tester tarafindan bagimsiz
   transkribe edilip `dataclasses.fields()` ciktisiyla karsilastirildi:
   tam eslesme, ne eksik ne fazladan uydurulmus alan var.

## Kapsam sinirlamasi (dogru raporlaniyor, gizlenmiyor)

Tasarim dokumani §5.3'teki kod blogu `TermHit` ve `Pair` icin **tam alan
semasi vermiyor** (yalnizca 5.1 tablosunda `GlossaryStore.lookup(text) ->
list[TermHit]` ve 4.1'de TM "kaynak/hedef cifti" olarak bahsediliyor). Bu
yuzden bu iki tip icin katı bir "alan-alan" spec-uyum testi yazilamadi;
yalnizca var olduklari, frozen olduklari ve kullanim baglamlarina (kaynak/
hedef terim, TM ornegi) semantik olarak uygun olduklari dogrulandi. Bu bir
implementer hatasi degil, spec'in bu iki tip icin kod seviyesinde sessiz
kalmasinin dogal sonucu.

## Kucuk gozlem (BLOKE EDICI DEGIL)

Tasarim dokumanindaki pseudocode bazi alanlarda varsayilan deger
gostermiyor (orn. `Rect.monitor_index`, `Rect.dpi_scale`,
`TextBlock.line_boxes`, `Segment.speaker/placeholders/source_blocks`,
`TranslationRequest.glossary_hits/tm_examples/style_profile`,
`TranslationResult.from_cache/detected_lang`) ama implementasyon bunlara
varsayilan deger eklemis (spec yalnizca `TranslationResult.partial`icin
acikca varsayilan gosteriyor). Bu; alan adini, tipini veya sirasini
DEGISTIRMIYOR, yalnizca constructor'i daha esnek hale getiriyor -- geriye
donuk uyumlu ve hicbir tuketiciyi kiramayacak bir gevseme. `mypy --strict`
zaten deger verildiginde tip dogrulugunu koruyor. Bloke edici bulunmadi,
ancak kayda gecsin diye burada belirtiliyor.

## Sonuc

140 bagimsiz dusmanca test + 3 kabul komutunun bagimsiz yeniden calistirilmasi
+ tasarim dokumani ile satir satir karsilastirma sonucunda **hicbir kirici
kusur bulunamadi**. Onay veriliyor.
