# T-005 · Tester-D (mercek: test kalitesi) · tur 1 · **ret**

> Bu dosyayi okuyan duzeltme ajani baglami SIFIRDAN kuruyor (PROTOKOL §7).
> Asagida: ne bozuk, nasil yeniden uretilir, ne beklenir, hazir duzeltme kodu.

## Once iyi haber -- `src/` DEGISMEYECEK

Uygulamanin kendisinde bulgu YOK. 49 mutantla saldirdim; teslim edilen
`service.py` ve `monitors.py` her yazili degismezi dogru gerceklestiriyor.
Taban birebir yeniden uretildi:

```
python -m mypy --strict --explicit-package-bases src/capture/service.py src/capture/monitors.py   -> exit 0
python -m pytest tests/unit/capture/test_service.py tests/unit/capture/test_monitors.py -q        -> 159 passed
python .agents/tasks/T-005/headless_check.py                                                      -> TEMIZ, exit 0
python -m pytest tests/unit/capture -q --cov=src.capture.service --cov=src.capture.monitors       -> 742 passed, %98.83
python -m pytest tests -q                                                                          -> 981 passed
```

Eksik olan **iki olcu**. Ikisi de senin sahip oldugun tek bir dosyada
kapaniyor: `tests/unit/capture/test_service.py`. `src/` ve `conftest.py`
degismeyecek.

---

## BLOKE D-1 · `MssBackend.__exit__` -> `close()` degismezinin olcusu BOS

**Yazili degismez (packet.md K10):** "`MssBackend` baglam yoneticisidir
(`__enter__` self, `__exit__` -> `close()`)."

**Olculen:** `__exit__`'in govdesini `return None` yapan bir uygulama **bes
kabul komutundan da exit 0 aliyor.**

### Yeniden uretim

`src/capture/service.py` icinde (gecici olarak):

```python
    def __exit__(self, *_: object) -> None:
        return None                      # <-- self.close() yerine
```

sonra bes komutu kostur. Ham cikti:
`.agents/tasks/T-005/tester_D_evidence/r1-18-mutant-birlesik.txt`, `M12` satiri:

```
| M12 | __exit__ close() CAGIRMAZ (baglam yoneticisi tutamaci sizdirir) | K10 `__exit__` -> close() | . | . | . | . | . |
```

(`.` = kapi kacirdi.) Kitin kendisi:
`python .agents/tasks/T-005/tester_D/mutant_kiti.py M12`

### Neden hicbir kapi gormuyor

* `headless_check.py` §3 `MssBackend`'i **hic `with` ile kullanmiyor** --
  yalnizca `b.close()`'u iki kez cagiriyor (`grep -n "with b" headless_check.py`
  bos doner).
* Tek birim testi `test_service.py::test_k1_mss_backend_yapimi_mss_e_dokunmaz`
  satiri **kapsiyor** ama iddiasi sadece:

  ```python
  b = MssBackend()
  with b as ic:
      assert ic is b          # <-- yalnizca __enter__'i olcuyor
  b.close()                   # <-- iddiasiz
  ```

  Orada `_tutamac` zaten `None` oldugu icin `close()` etkisizdir; iddia
  `self.close()` ile `return None` arasini **ayirt edemez**. Kapsam yesil,
  olcu bos.
* K13 bu uc metodu (`__init__`/`__enter__`/`__exit__`) bilerek pragma DISI
  birakiyor ("testte kapsanir") -- yani olcu senin dosyanda beklenecek.

### Ihlalin bedeli (K10'un kendi olctugu ariza)

`mss`'te `__del__` yok. `__exit__` kapatmazsa **her `with MssBackend() as b:`
blogu bir window DC + memory DC sizdirir**; sefin olcumune gore **5001.
kapatilmamis ornekte `GetWindowDC` kalici olarak basarisiz olur** ve process
bir daha yakalama yapamaz.

---

## BLOKE D-2 · `close()` idempotens olcusu (§3 `c2_close`) DUSEMEZ

**Yazili degismez (packet.md K10):** "`MssBackend.close()` bu tutamaci
kapatir, **idempotent**tir (ikinci cagri sessiz)."

**Olculen:** `close()`'dan `self._tutamac = None` satirini silen bir uygulama
**bes kapidan da exit 0 aliyor.**

### Yeniden uretim

```python
    def close(self) -> None:  # pragma: no cover -- ...
        if self._tutamac is not None:
            self._tutamac.close()
            # self._tutamac = None       <-- silindi
```

Ham cikti: `r1-18-mutant-birlesik.txt`, `M13` satiri -> `| . | . | . | . | . |`
(`python .agents/tasks/T-005/tester_D/mutant_kiti.py M13`).

### Neden §3 goremiyor

§3'un casusu `close()`'u kendi icinde koruyor:

```python
        def close(self):
            if not self._closed:
                state['close'] += 1        # <-- ikinci cagri sayaci ARTIRMAZ
                self._closed = True
```

Bu, gercek `mss.MSS.close()`'un sadik bir modeli (`mss` 10.2.0 belgesi:
"It is safe to call this multiple times; multiple calls have no effect").
Dolayisiyla `c2_close == 3` beklentisi **her uygulamada** saglanir --
idempotent olan da olmayan da gecer. Olcu sessizdir.

### Ihlalin bedeli

Sayacta degil, **kapatilmis tutamacla grab**'de. `_tutamac` sifirlanmazsa
`close()` sonrasi ilk `grab()` `self._tutamac is None` denetimini gecer ve
**kapatilmis** bir `MSS` uzerinden yakalama dener. `mss` belgesi: "Once the
MSS object is closed, it may not be used again." Dogru uygulamada (senin
teslim ettigin) `close()` tutamaci sifirladigi icin sonraki `grab()`
**yeni** bir `MSS` kurar; bunu kendi sondamla dogruladim (r1-06,
`test_d5_uygulama_close_tutamaci_sifirliyor`: `close()` sonrasi grab -> MSS
sayaci 2).

---

## Paketin seni yanilttigi nokta (sefe de bildirildi)

`packet.md` K10'un ÖLÇÜ satiri soyle bitiyor:

> "(Test paketi bunu olcemez, K1 geregi.)"

**Bu parantez olgusal olarak yanlis** ve muhtemelen olcuyu yazmaktan seni
alikoydu. K1 **gercek ekrani** ve **gercek `mss` modulunu** yasakliyor;
`__enter__`/`__exit__`/`close()` govdeleri ise sahte bir tutamacla gercek
ekrana **hic dokunmadan** olculebiliyor. Kendi kitimda iki ayri yoldan
yaptim ve ikisi de gecti:

* sahte tutamac enjeksiyonu (asagidaki duzeltme),
* `sys.modules['mss']`'e sayacli casus modul koyup `with MssBackend() as b:`
  kosturmak (`tester_D/test_d5_bos_olcum_noktalari.py::
  test_d5_uygulama_exit_close_cagiriyor`).

---

## DUZELTME -- hazir kod

`tests/unit/capture/test_service.py` **sonuna** ekle. `src/` ve `conftest.py`
degismeyecek. Gercek ekrana / gercek `mss`'e sifir temas.

```python
# ==========================================================================
# K10 -- MssBackend omru (baglam yoneticisi + close idempotensi)
# ==========================================================================


class _SahteTutamac:
    """`mss.MSS` gibi davranan sahte tutamac -- gercek ekrana dokunmaz.

    Gercek `mss.MSS.close()` KENDI ICINDE idempotenttir ("It is safe to call
    this multiple times"); sahte de oyle davranir ki olcu `MssBackend`'in
    KENDI idempotensini olcsun, alttaki nesneninkini degil. Ayirt eden
    gozlem sayac degil, `_tutamac`'in sifirlanmasidir.
    """

    def __init__(self) -> None:
        self.kapatma = 0
        self._kapali = False

    def close(self) -> None:
        if not self._kapali:
            self.kapatma += 1
            self._kapali = True


def test_k10_exit_uzun_omurlu_tutamaci_kapatir() -> None:
    b = MssBackend()
    t = _SahteTutamac()
    b._tutamac = t  # type: ignore[assignment]
    with b as ic:
        assert ic is b
        assert t.kapatma == 0
    assert t.kapatma == 1, (
        "__exit__ close() cagirmadi -> her `with` blogu bir window DC sizdirir "
        "(K10: 5001. kapatilmamis ornekte GetWindowDC kalici olarak duser)"
    )
    assert b._tutamac is None


def test_k10_close_tutamaci_sifirlar_ve_idempotenttir() -> None:
    b = MssBackend()
    t = _SahteTutamac()
    b._tutamac = t  # type: ignore[assignment]
    b.close()
    assert t.kapatma == 1
    assert b._tutamac is None, (
        "close() tutamaci sifirlamadi -> sonraki grab KAPATILMIS MSS'i kullanir "
        "(mss: 'Once the MSS object is closed, it may not be used again')"
    )
    b.close()
    assert t.kapatma == 1, "ikinci close() sessiz olmali (idempotent)"
```

### Bu duzeltmenin AYIRT ETME GUCU olculdu

Ayna agacinda kosuldu (ham cikti:
`.agents/tasks/T-005/tester_D_evidence/r1-17-onerilen-duzeltme.txt`):

| durum | sonuc |
|---|---|
| TABAN (teslim edilen kod) | `2 passed` |
| M12 (`__exit__` -> `return None`) | `test_k10_exit_uzun_omurlu_tutamaci_kapatir` **FAILED** |
| M13 (`close()` `_tutamac`'i sifirlamiyor) | **iki test de FAILED** |

Yani iki test de gercekten kiriliyor; totoloji degiller.

### Kabul kosulu (tur 2)

```bash
python -m mypy --strict --explicit-package-bases src/capture/service.py src/capture/monitors.py
python -m pytest tests/unit/capture/test_service.py tests/unit/capture/test_monitors.py -q   # 161 passed
python .agents/tasks/T-005/headless_check.py
python -m pytest tests/unit/capture -q --cov=src.capture.service --cov=src.capture.monitors --cov-fail-under=95
python -m pytest tests -q                                                                    # 983 passed
python .agents/tasks/T-005/tester_D/mutant_kiti.py M12 M13                                   # ikisi de YAKALANDI
```

Son satir bu duzeltmenin **kapiyi gercekten kapattigini** dogrular: `M12` ve
`M13` artik `[.X.XX]` vermeli, `[.....]` degil.

---

## Bloke ETMEYEN, kayda gecen notlar

1. **`FakeBackend` varsayilan `image_factory`'si olculmuyor.** K1 "varsayilan
   `(rect.h, rect.w, 4)` sifir dizi dondurur" diyor; onu `(h, w, 3)` yapan
   mutant (M44) bes kapidan da geciyor. Yalnizca test altyapisi, uretime
   etkisi yok. Tek satir kapatir:
   `assert FakeBackend((Rect(0,0,4,3),)).grab(Rect(0,0,4,3)).shape == (3, 4, 4)`.
2. **K3 olcusu `==` ile yazilmis, tip kimligiyle degil.** `Rect(np.int64(100),
   ...) == Rect(100, ...)` -> `True`, hash esit, demet ve kume karsilastirmasi
   da esit; bu yuzden backend'e giden kutuda bir numpy sizintisini `test_k3_*`
   **goremez** (M37 bes kapidan geciyor). Senin uygulaman DOGRU -- kutuya dort
   numpy tipinde de duz `int` gidiyor, olctum. Isteğe bagli sertlestirme:
   `test_k3_*`'in birine `assert type(giden.x) is int` eklemek.
3. **Fazladan `# pragma: no cover` yok.** `src/capture` altinda tam 3 pragma
   var, ucu de `MssBackend.monitors/grab/close` uzerinde ve ucu de K13'un
   istedigi gerekce yorumunu tasiyor. Gizli `exclude_lines` yapilandirmasi da
   yok. (Bu kural makineyle denetlenmiyor -- elle dogruladim, temiz.)
4. **Zorunlu kararlarin docstring yarisi TAM.** K2/K5/K8/K10/K11/K12'nin 11
   zorunlu maddesinin 11'i de kaynak docstring'lerinde var. `known_gaps`
   yarisini tester korlugu geregi okuyamiyorum; o sefin elle denetleyecegi
   kalemdir.

## Kanit dosyalari

| dosya | ne |
|---|---|
| `tester_D_evidence/r1-01..05` | bes kabul komutunun ham ciktisi (taban) |
| `tester_D_evidence/r1-06-tester-D.txt` | mercek D kiti: 95 passed, 2 xfailed (= iki bulgu) |
| `tester_D_evidence/r1-18-mutant-birlesik.txt` | 49 mutant x 5 kapi birlesik tablo |
| `tester_D_evidence/r1-21-bloke-mutantlar.txt` | iki bloke mutantin TEK KOMUTLA yeniden uretimi |
| `tester_D_evidence/r1-17-onerilen-duzeltme.txt` | duzeltmenin ayirt etme gucu (taban/M12/M13) |
| `tester_D_evidence/r1-13-kapsam-yalani.txt` | fazladan pragma esigi kirmiyor (mekanizma) |
| `tester_D_evidence/r1-14-validate-korlugu.txt` | `validate.py` sentetik bos teslimi kabul ediyor |
| `tester_D_evidence/r1-15-docstring-known-gaps.txt` | zorunlu kararlarin docstring yarisi |
| `tester_D_evidence/r1-19-son-durum.txt` | `src/` ve `tests/` degismedi (git) |
| `tester_D/mutant_kiti.py` | mutant kitinin kendisi (ayna agaci, `src/` yazilmaz) |
