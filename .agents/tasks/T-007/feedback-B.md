# T-007 · feedback-B (mercek B: test kalitesi) · tur 1 → tur 2 implementer'a

**Karar: RET.** Kod doğru; reddedilen şey **K3 (Y1) ölçüsü**: altı cümle-sonu işaretinden ikisi (`?` U+003F ve `！` U+FF01) hiçbir testte **ayırt edici konumda değil**. Terminatör kümesinden bu iki işaretten biri düşerse **beş kapının beşi de yeşil kalıyor** ve gerçek modelde Y1'in düzelttiği kusur (C6/C8 kaynaşması: cümle kaybı) geri geliyor. Düzeltme test dosyasına ~10 satır; ayırt etme gücü ölçüldü (aşağıda). `src/` dokunulmasına gerek yok.

Tüm komutlar depo kökünden, bu makinede koşuldu. Ham çıktılar `.agents/tasks/T-007/tester_B_evidence/`.

## 1 · Yeniden üretim (bloke eden bulgu)

```
set TESTER_B_SCRATCH=<bos bir dizin>
python .agents/tasks/T-007/tester_B/mutant_kiti.py K3-03 K3-05
```

Kit `src/tests/real_check/models` dosyalarını `%TESTER_B_SCRATCH%\t007_tester_B_mutroot` altına **kopyalar** (depoya yazmaz), `src/translate/local_nmt.py` içinde tek satırı değiştirir ve paketin **beş kabul komutunu** koşar. Ham çıktı `tester_B_evidence/B1-mutant-kiti.txt`:

```
K3-03   [.....] *** HICBIR KAPI YAKALAMADI ***   (beklenen: G2 G4 G5)
        K3 (Y1): terminator kumesinden `ASCII soru` ('?') EKSIK
K3-05   [.....] *** HICBIR KAPI YAKALAMADI ***   (beklenen: G2 G4 G5)
        K3 (Y1): terminator kumesinden `CJK unlem` ('！') EKSIK
```

Uygulanan yama (her biri ayrı mutant, `mutant_kiti.py` `_term_eksik`):

```python
_TERMINATORLER: Final = ".!?。！？"      # teslim
_TERMINATORLER: Final = ".!。！？"       # K3-03  ('?' yok)  -> mypy 0, 210 passed, real_check TEMIZ, %100, 1314 passed
_TERMINATORLER: Final = ".!?。？"       # K3-05  ('！' yok) -> aynı: beş kapı yeşil
```

**Beklenen:** en az bir kapı kırmızı. Karşılaştırma: aynı kümeden `.` (K3-01), `!` (K3-02), `。` (K3-04), `？` (K3-06) düşürülünce birim kapısı 11/3/13/2 testle **yakalıyor** — yani ölçü var, ama altı noktanın **dördünde** koşuyor (PROTOKOL 4.6/7: tek noktaya kapılı uygulama görünmez; 4.6/10: pozitif kontrol sınıf başına).

**Neden kaçıyor (AST ile bakıldı):** teslim testlerinde `?` ve `！` yalnız şu girdilerde geçiyor — `"Wait... what?!"` (`?` ardından `!`: `!` böler), `"c! e?"` (`?` **sonda**: `\Z` kuyruğu zaten parça), `"A。？！"` / `"!?.。！？"` (Y2 süzgeci harfsiz parçayı yutuyor, `test_k3c_modele_giden_her_parcada_harf_veya_rakam_var` yalnız gönderilen parçaları denetliyor). Hiçbirinde `?`/`！` sonrasında **harf içeren** ikinci bir cümle yok.

## 2 · Ürün etkisi — gerçek modelle ölçüldü (`B1c-kacan-mutant-gercek-model.txt`)

`python .agents/tasks/T-007/tester_B/b1c_kacan_mutant_gercek_model.py` — mutasyonlu/mutasyonsuz modül ayrı alt süreçte gerçek modelle tek segmentlik istekleri çevirir; motor sarmalanıp modele giden parça sayılır; yalnız sayılar basılır.

| girdi (tek segment) | teslim: parça → çıktı cümle, anahtarlar | K3-03 `?` eksik | K3-05 `！` eksik |
|---|---|---|---|
| EN `Are you ready? The village elder is waiting for you.` | 2 → 3, hazır ✓ bekliyor ✓ ihtiyar ✓ | **1 → 1, "hazır" YOK** | 2 → 3 |
| KR `기다려! 정말 가는 거야? 마을 장로가 … 있습니다.` (KRT Y1'in örneği) | 3 → 3, üçü ✓ | 2 → 3 (model bu kez idare etti) | 3 → 3 |
| JP `止まれ！村の長老があなたを待っています。` | 2 → 2, dur ✓ bekliyor ✓ ihtiyar ✓ | 2 → 2 | **1 → 1, "dur" YOK** |
| JP `待って！本当に行くの？` (KRT Y2'nin örneği) | 2 → 2 | 2 → 2 | **1 → 1** |

Yani ilk cümle çeviride **kayboluyor** — KRT Y1'in "ikinci cümle tamamen kayboluyordu" bulgusunun aynısı, yalnız işaret farklı. Oyun diyaloğunda `?` (EN/KR) ve `！` (JP) en sık ikinci/üçüncü işaretler; erişilebilir.

## 3 · Düzeltme — test dosyasına ekler (ayırt etme gücü ölçüldü)

`tests/unit/translate/test_local_nmt.py`:

**(a)** `test_k3b_bolme_noktalamaya_gore_dile_gore_degil` parametrize listesine, `("A! B？ C.", ...)` satırından sonra:

```python
        ("A? B.", ["A?", "B."]),  # ASCII soru isareti tek basina ayirt edici
        ("A！B。", ["A！", "B。"]),  # CJK unlem tek basina ayirt edici
```

**(b)** Değişmezin kendisi — altı işaretin her biri **tek başına** böler (yeni test; `test_k3_cumlelere_bol_yardimcisi_ve_modele_gider`'in önüne):

```python
@pytest.mark.parametrize("t", list(".!?。！？"))
def test_k3b_her_terminator_tek_basina_boler(tmp_path: Path, t: str) -> None:
    """K3 degismezi ALTI isaretin her birinde ayri olculur (4.6/7: tek noktaya kapili uygulama gorunsun)."""
    f = SahteFabrika()
    saglayici(tmp_path, f).translate(istek([f"A{t}B{t} C{t}"]))
    assert f.motor.gonderilen_parcalar() == [f"A{t}", f"B{t}", f"C{t}"]
```

**Ayırt etme ölçümü** (`mercekB_ayirt_etme.py` → `B1b-mercekB-ayirt-etme.txt`; ayrı ayna ağacı, yalnız G2):

| | teslim testleri (210) | (a)+(b)+(c) yamalı testler (220) |
|---|---|---|
| mutasyonsuz src | 210 passed | **220 passed** (yanlış pozitif yok) |
| K3-01 `.` | X (11) | X (12) |
| K3-02 `!` | X (3) | X (4) |
| **K3-03 `?`** | **. 210 passed** | **X (2): `test_k3b…[A? B.]`, `test_k3b_her_terminator…[?]`** |
| K3-04 `。` | X (13) | X (14) |
| **K3-05 `！`** | **. 210 passed** | **X (2): `test_k3b…[A！B。]`, `test_k3b_her_terminator…[！]`** |
| K3-06 `？` | X (2) | X (3) |

Ekleri koyduktan sonra doğrulama: `python .agents/tasks/T-007/tester_B/mutant_kiti.py K3-01 K3-02 K3-03 K3-04 K3-05 K3-06` → altısı da `[.X.XX]` (ya da `.XXXX`) olmalı; kontroller C01–C06 `[.....]` kalmalı.

`real_check.py` şefe ait; oraya `?`/`！` pozitif kontrolü (ör. `FX["EN"]`'e `?` cümlesi) **şefin** kararı — feedback'in kapsamı test dosyası.

## 4 · Bloke etmeyen keskinleştirme — aynı turda ucuz (ölçüldü)

**(c) Hata mesajına MOTOR ÇIKTISI (çeviri metni) sızması ölçülmüyor** — K10-08 / K10-09 beş kapıdan kaçtı (`[.....]`). `test_k6_hata_mesajlari_kaynak_metni_tasimaz` nöbetçiyi **kaynak** metne koyuyor; `sayi` ve `bozuk-cikti` yollarında sahte motor `"x"`/`5` döndürdüğü için mesaja `{cikti!r}` / `{nesne!r}` ekleyen bir uygulama geçiyor. Gerçek CT2 bu iki yolu üretmez (D2: sayı hep eşit, biçim sabit) → erişilebilirlik düşük, **ret sebebi değil**; ama K10'un lafzı "hiçbir kanala çeviri/kaynak metni". İki parametre satırı yeter (aynı teste, `sayi`'dan sonra; `import types` gerekir):

```python
        (lambda: SahteFabrika(SahteMotor(cikti=lambda t: [SahteHipotez([[HEDEF, "NOBETCI-9c1e"]])] * (len(t) + 1))), ContractViolation),  # MOTOR CIKTISI nobetci tasir
        (lambda: SahteFabrika(SahteMotor(cikti=lambda t: [types.SimpleNamespace(hypotheses=None, metin="NOBETCI-9c1e") for _ in t])), ProviderUnavailable),  # nesne repr nobetci tasir
```
ve `ids` listesine `"sayi-nobetcili-cikti", "bozuk-nesne-nobetcili"` (sırayla, `sayi`'dan hemen sonra). Ölçüldü: K10-08 → `X (1): …[sayi-nobetcili-cikti]`, K10-09 → `X (1): …[bozuk-nesne-nobetcili]`; mutasyonsuz src 220 passed.

**(d) 7 pozitif kontrolde `match=` yok** (`test_k10_pozitif_kontrol_kanal_olcusu_atesliyor`: `pytest.raises(AssertionError)`): ölçü değişirse yanlış sebeple düşüp yeşil kalabilir. Bugün 7/7 doğru sebeple düşüyor (ölçtüm: `test_b4_teslimin_yedi_pozitif_kontrolu_dogru_sebeple_dusuyor`, `B-mercek-testleri-tek-basina.txt`). `ids` → beklenen mesaj: stdout/`os.write(1)` → `"stdout'a"`, stderr/`__stderr__` → `"stderr'e"`, iki logger → `"log kaydina"`, warnings → `"warnings kaydina"`. T-006 tur 2 keskinleştirme #4'ün aynısı.

**(e) Bilgi, değişiklik istemiyor:** `test_k6_fabrika_istisnasi_siniflandirilir` e3 (`FileNotFoundError` → `ModelMissingError`) paketin K6(b) lafzından ("kurulum istisnası → `ProviderUnavailable`") **daha sert**; K6-06 mutantı (paket lafzına uyan uygulama) birim kapısında düşüyor. Docstring bunu belgeliyor; şefin karara yazması gereken bir sapma — implementer'a iş değil.

## 5 · Değişmeyen / onaylanan (tur 2'de yeniden koşulacak)

53 davranış mutantının 49'u yakalandı, 6/6 kontrol kaçtı (yanlış pozitif yok); sahte motor gerçek CT2 biçimiyle uyumlu; K1 bariyeri dört koşum biçiminde de `meta_path[0]`; ömür/hata sınıfları 22 mercek-B testiyle doğrulandı; gerçek modelle ayrı süreçte stdout/stderr **0/0 bayt** (CT2 DEBUG'a çekilince 2053 bayt — kanal görünür, sağlayıcı seviyeye dokunmuyor). Ayrıntı `verdict-B.md`.
