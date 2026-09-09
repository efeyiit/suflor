---
task: T-001
role: implementer
round: 1
status: tamamlandi
files_written:
  - src/contracts/models.py
  - src/contracts/interfaces.py
  - src/contracts/errors.py
  - src/contracts/__init__.py
  - tests/unit/contracts/conftest.py
  - tests/unit/contracts/test_models.py
  - tests/unit/contracts/test_errors.py
  - tests/unit/contracts/test_interfaces.py
commands:
  - cmd: "python -m mypy --strict src/contracts"
    exit_code: 0
    evidence: evidence/mypy.txt
  - cmd: "python -m pytest tests/unit/contracts -q"
    exit_code: 0
    evidence: evidence/pytest.txt
  - cmd: "python .agents/tasks/T-001/purity_check.py"
    exit_code: 0
    evidence: evidence/purity.txt
contract_change_request: false
known_gaps:
  - "TermHit ve Pair, tasarim dokumani 5.3'te yalnizca adiyla geciyor; alan duzeyinde tanimli degil. Alanlarini bu gorevde ben belirledim (gerekce asagida). Sefin onayina acik."
  - "OcrPreset enum'u 5.3'te yok; 3.1'deki `ocr_preset = dialogue | menu | tooltip | subtitle` degerlerinden turetildi. OcrEngine.recognize(frame, preset) imzasi (5.1) bir preset tipi gerektirdigi icin eklendi."
  - "Frame.image ve TranslationRequest.image_crops esitlik/hash disinda tutuldu (field(compare=False)); ndarray'in `==` operatoru skaler degil dizi dondurdugu icin dataclass'in uretilmis __eq__/__hash__ metodlari aksi halde calisma zamaninda patliyordu."
---

# T-001 teslim

## Ne yapildi

`src/contracts/` altina dort dosya, `tests/unit/contracts/` altina dort dosya yazildi.
Tasarim dokumani 5.3'teki sekiz model, iki soyut arayuz, iki deterministik sahte
implementasyon ve yedi sinifik hata taksonomisi tamamlandi. **114 test** kosuyor,
uc kabul komutunun ucu de cikis kodu 0 veriyor.

## TDD kaniti (kirmizi -> yesil)

Once uc test modulu yazildi, implementasyon yokken kosuldu ve **basarisiz oldu**:

```
ERROR tests/unit/contracts/test_errors.py
ERROR tests/unit/contracts/test_interfaces.py
ERROR tests/unit/contracts/test_models.py
E   ModuleNotFoundError: No module named 'src'
!!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!
3 errors in 0.27s
```

Ham cikti: `evidence/pytest-red.txt` (cikis kodu 2). Yesil kosum: `evidence/pytest.txt`.

## Tasarim kararlari

**1 - Doc'ta olmayan iki model: `TermHit` ve `Pair`.**
5.3 bunlari `TranslationRequest` alanlarinda kullaniyor ama alanlarini tanimlamiyor.
5.1'deki `GlossaryStore.lookup(text) -> list[TermHit]` ve
`TranslationMemory.find_similar(text, k)` / `add(pair)` imzalarina gore turettim:

- `TermHit(source_term, target_term, start, end, segment_index=None, note=None)`.
  `lookup(text)` tek bir metin uzerinde calistigi icin hangi segmentte gectigini
  bilemez; bu yuzden `segment_index` opsiyoneldir ve iliskilendirmeyi pipeline yapar.
- `Pair(source, target, score=1.0)`. `score` fuzzy benzerlik (0..1); `find_similar`
  doldurur, `add` ile eklenen kesin kayitlarda 1.0 kalir.

Bunlar tahmindir, dokumandan alinti degildir. A5 (store) ve A4 (translate) ajanlari
farkli bir sekil isterse **simdi** soylemeli; donduktan sonra kirici degisiklik olur.

**2 - `OcrPreset` bir `StrEnum`.**
5.1 `recognize(frame, preset)` diyor, 3.1 degerleri sayiyor. `StrEnum` sectim cunku
uyeler ayni zamanda `str`: profil JSON'una dogrudan yazilabiliyor, `OcrPreset("menu")`
ile geri okunabiliyor, ama tip denetimi yine de yazim hatasini yakaliyor.

**3 - ndarray tasiyan alanlar esitlik/hash disinda.**
`Frame(...) == Frame(...)` veya `hash(frame)` cagrisi, ndarray alani karsilastirmaya
girseydi `ValueError: truth value of an array is ambiguous` ile patlardi. Bir karenin
kimligi zaten `seq`; `image` ve `image_crops` `compare=False, repr=False` ile isaretlendi.
Sonuc: butun modeller hashlenebilir (cache/kuyruk anahtari olarak kullanilabilir) ve
`repr()` piksel yigini dokmez (PROTOKOL 6.7 loglama disiplini).

**4 - Opsiyonel alanlara varsayilan deger verildi.**
Alan adlari, siralari ve tipleri 5.3 ile birebir; ek olarak `monitor_index=0`,
`dpi_scale=1.0`, `line_boxes=()`, `speaker=None`, `placeholders=()`, `source_blocks=()`,
`glossary_hits=()`, `tm_examples=()`, `style_profile=None`, `image_crops=None`,
`from_cache=False`, `detected_lang=None`, `partial=False` varsayilanlari eklendi.
Alan kumesini degistirmez, test yazmayi ciddi olarak kolaylastirir.

**5 - `ensure_aligned()` sozlesme denetleyicisi.**
Hizalama kurali (`len(translations) == len(segments)`) tek bir yerde, `interfaces.py`
icinde uygulanir ve `ContractViolation` firlatir. Her saglayici donmeden once bunu
cagirmali. `FakeProvider` kendi cikitisini bununla denetliyor.

**6 - `mypy --strict` icin `ImageArray` takma adi.**
`--strict`, `disallow_any_generics` acar; ciplak `np.ndarray` gecmez. `models.py`
`ImageArray: TypeAlias = npt.NDArray[np.uint8]` tanimlar (5.3'teki "BGR, uint8"
yorumunun tipe cevrilmis hali). Butun goruntu alanlari bunu kullanir.

## Sonraki ajanlarin bilmesi gerekenler

**Import yolu.** Depo kokunde `pyproject.toml` yok, `src/__init__.py` yok. `src` ortuk
ad alani paketi olarak cozuluyor; **depo kokunden** `python -m ...` ile kosuldugunda
calisma dizini `sys.path`'e girdigi icin `from src.contracts import ...` sorunsuz
calisiyor (kanit: `evidence/selfcheck.txt` ilk satir). Baska bir dizinden kosarsaniz
`PYTHONPATH=.` on eki gerekir. `tests/unit/contracts/conftest.py` bu bootstrap'i
zaten yapiyor.

**Sahtelerle test yazma.**

```python
from src.contracts import FakeOcrEngine, FakeProvider, OcrPreset, ensure_aligned

engine = FakeOcrEngine([[blok_a], [blok_b, blok_c]])   # cagri basina bir adim
engine.recognize(frame, OcrPreset.DIALOGUE)            # betik bitince son adim tekrarlanir
engine.calls        # [(Frame, OcrPreset), ...]  -- neyin gectigini dogrulayin

p = FakeProvider(translations={"Attack": "Saldiri"}, provider_id="fake-nmt")
p.translate(req)    # eslesmeyen segmentler "[tr] <metin>" olur; sayilar hep hizali
p.requests          # gelen istekler -- sozluk/TM aktarimini burada dogrulayin
p = FakeProvider(error=ProviderUnavailable("OOM"))   # hata yolunu deterministik sina
```

Ikisi de tamamen deterministik: rastgelelik yok, saat okuma yok, I/O yok.
`FakeProvider.latency_ms` varsayilan 0.0 (yapilandirilabilir ama sabit), yani
performans testlerinde gurultu uretmez.

**Sozlesme dondu.** `src/contracts/` artik yalnizca A1 ve sefin alani. Eksik alan
gorurseniz kendiniz eklemeyin; `contract_change_request: true` ile talep acin.
Ozellikle A4 (translate) ve A5 (store), yukaridaki `TermHit` / `Pair` sekline
**erken** itiraz etmeli.

**Saflik.** `src/contracts/` yalnizca `abc`, `dataclasses`, `enum`, `typing`,
`collections.abc` ve `numpy` import ediyor. Modul ici baglanti goreli import
(`from .models import ...`) ile yapiliyor; mutlak `src.contracts...` importu
`purity_check.py`'yi kirar (`src` izinli ust modul degil). Dinamik import yok
(`evidence/selfcheck.txt` kontrol 5).

## Kanit dosyalari

| Dosya | Ne | Cikis kodu |
|---|---|---|
| `evidence/mypy.txt` | `python -m mypy --strict src/contracts` | 0 (4 dosya, sorun yok) |
| `evidence/pytest.txt` | `python -m pytest tests/unit/contracts -q` | 0 (114 gecti) |
| `evidence/purity.txt` | `python .agents/tasks/T-001/purity_check.py` | 0 (TEMIZ) |
| `evidence/pytest-red.txt` | TDD kirmizi fazi, implementasyon oncesi | 2 (3 collection error) |
| `evidence/selfcheck.txt` | `env.md`'deki 5 bagimsiz kontrolun kosumu | 0 (14/14 gecti) |

`selfcheck.txt`, `env.md`'nin "Neye bakilacak" listesini bagimsiz olarak kosar:
sekiz modelin frozen davranisi, `FakeProvider`'in 1/3/0 segmentle hizalamasi,
`image_crops`'un varligi ve None kabul etmesi, alti hata sinifinin `issubclass`
denetimi, ve dinamik import taramasi. Kabul komutlarinin disinda oldugu icin
`commands` listesine konmadi; tester kendi kosumunu kendi yapacak.
