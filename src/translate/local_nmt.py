"""Suflor -- yerel NMT ceviri saglayicisi (`LocalNmtProvider`), T-007.

`TranslationProvider` sozlesmesinin (`src/contracts/interfaces.py`) Katman 1
uygulamasi: `TranslationRequest` -> `TranslationResult`. Altta ctranslate2
4.8.2 + sentencepiece 0.2.2; model NLLB-200-distilled-600M CT2 int8
(olgular C1). Dil kodu ACIK verilir (algilama yok), cumleler noktalamaya
gore bolunur ve TEK batch'te cevrilir, yer tutucular kaba onarimla korunur.

Bu docstring, gorev paketindeki (T-007 packet.md surum 2) K1-K10
kararlarinin bu modulde nasil uygulandigini belgeler. Her kararin yaninda
onu olcen test adi vardir (`tests/unit/translate/test_local_nmt.py`) ya da
`[ÖLÇÜLMÜYOR]` damgasi. Tester `known_gaps`i OKUMAZ; garanti alani burasidir.

Yapi
-----
`NmtDili` (StrEnum, NLLB kodlari) · `CeviriMotoru` (Protocol: CT2
`Translator`in bize gereken yuzu) · `MotorFabrikası` (tip takma adi:
`(model_dir, params) -> (motor, encode, decode)`) · `LocalNmtProvider`
(dogrulama + tembel kurulum + bolme/birlestirme/onarim) · public yardimcilar
`cumlelere_bol`, `modele_gider`, `kaynak_dili_coz`, `hedef_dili_coz`,
`zorunlu_model_dosyalari`, `eksik_model_dosyalari`.

Kutuphane ENJEKTE edilir: `motor_fabrikasi` `(model_dir, params)` alir ve
`(motor, encode, decode)` uclusu dondurur. `None` ise gercek kutuphaneyi
kuran `_varsayilan_fabrika` kullanilir. Butun birim testleri sahte
fabrikayla kosar; gercek model yalniz `.agents/tasks/T-007/real_check.py`
ile (ayri surec) olculur.

## K1 -- import bicimi: kutuphane yalniz `_varsayilan_fabrika` govdesinde

`ctranslate2` ve `sentencepiece` yalniz `_varsayilan_fabrika` GOVDESINDE
import edilir; modul duzeyinde ve baska hicbir fonksiyonda gecmez. Sefin
`tests/unit/translate/conftest.py` bariyeri test surecinde bu import'lari
`RuntimeError` ile keser; testlerde calisan HICBIR yol kutuphaneye
dokunamaz -- model dosyasi denetimi, dil tablosu, bolme kurali dahil.
`src/__init__.py` yoktur; `src.contracts` MUTLAK import edilir. Bu modul
kardes modul (`src.ocr`, `src.capture`) import etmez. Olcu: `test_k1_*`.

## K2 -- hizalama: `ensure_aligned` + CUMLE sayisi denetimi

`translations` `request.segments` ile birebir hizalidir; `translate`
donmeden `ensure_aligned` cagrilir. Ek olarak (O3): motor, gonderilen
cumle sayisi kadar hipotez dondurmek zorundadir; sayi tutmuyorsa
`ContractViolation` -- segment sayisi tutup cumle sayisi tutmayan KAYMAYI
`ensure_aligned` goremez, cumle-duzeyi sayim gorur. Bos `segments` ->
`translations == ()`, `latency_ms >= 0`, motor ve fabrika CAGRILMAZ.
`request` bir `TranslationRequest` degilse ya da bir segmentin `text`i
`str` degilse `ContractViolation`, motor cagrilmaz. Olcu: `test_k2_*`.

## K3 -- cumle bolme NOKTALAMAYA gore, dile gore DEGIL (C6, C8, Y1, Y2)

Her segment metni `cumlelere_bol` ile parcalara ayrilir; tum segmentlerin
tum parcalari TEK `translate_batch` cagrisinda gider (C2: toplu ceviri
cumle basina 2x ucuz); cikti segment basina `" "` ile birlestirilir.

Kural (Y1): cumle sonu isareti kumesi EVRENSEL `.!?。！？` -- ALTI isaretin
HER BIRI TEK BASINA cumle sonudur (T2-1). Korece ASCII `.` kullanir, v1'in
dile gore `。！？` kurali KR'yi hic bolmuyor ve tek girdide ikinci cumle
tamamen kayboluyordu (KRT olctu, sef dogruladi). Tur 1 olcusu `?` (U+003F)
ve `！` (U+FF01) icin kordu: kumeden dusurulunce bes kapi yesil kaliyor,
gercek modelde "Are you ready? The village elder..." tek parca gidip ilk
cumle kayboluyordu (Tester-B olctu, sef uretti). Simdi her isaret ayri
olculur (`test_k3b_her_terminator_tek_basina_boler[U+XXXX]`,
`test_k3b_terminator_diger_isaretler_yokken_*`); kumenin sinirini negatif
kontrol sabitler (`,` `;` `:` `…` `、` `，` bolmez).
Bosluk sarti YOK (`A.B.` -> 2 parca). Ardisik terminatorler (`...`, `？！`)
ve terminatorden sonraki kapanis isaretleri (`」』）)"'”’»`; arada bosluk olsa
da) ayni parcada kalir (`「A。」` -> 1 parca, `A。 」` -> 1 parca). Terminatorsuz kuyruk tek parcadir.

Parca suzgeci (Y2, T2-2 ile keskinlestirildi): parca, `Segment.placeholders`
icindeki dizeler CIKARILDIKTAN SONRA hic harf/rakam icermiyorsa (`？`, `」`,
`。。。`, `...`, yalniz bosluk, `{PLAYER}!`, `{0}。`, `%s!`) modele
GONDERILMEZ, ciktiya AYNEN gecer -- model bu parcalara Turkce UYDURUR
(`？` -> "- Hayir, hayir."; KRT olctu, sef dogruladi, 5/5; `{PLAYER}!` ->
"- Hayir, hayir. {PLAYER}", `{0}。` -> `{0}♪`: Tester-A K-1, sef uretti;
bu kuralla gercek modelde `A。？`, `「A。」`, `待って！？…`, `…。「…。」`
ciktilarinda uydurma YOK, olcum-2 [E]; `{PLAYER}!` -> `{PLAYER}!` aynen,
olcum-4). Yer tutucu bilgisi YALNIZ `Segment.placeholders`tan gelir:
bildirilmemis `{PLAYER}` METINDIR ve gider. Yer tutucu yaninda metin varsa
(`{PLAYER} is here.`) parca gider. Gecis parcasindaki yer tutucu K5 sayimina
girer (ciktida zaten var, eklenmez). Hicbir parcasi modele gitmeyen segment
(bos metin, yalniz bosluk, yalniz noktalama, yalniz yer tutucu) ciktida
KAYNAK METNIN AYNISIDIR (`"" -> ""`, `"   " -> "   "`, `"{PLAYER}!" ->
"{PLAYER}!"`). Gonderilecek parca yoksa motor KURULMAZ bile (fabrika
sayaci 0).

Bilinen zayifliklar `[ÖLÇÜLMÜYOR]` (kalite; altin set yok): EN kisaltma
(`Dr. Smith` -> `Dr.` + `Smith`), ondalik (`3.5` -> `3.` + `5`, iki parca da
rakam icerdigi icin modele gider), surum numarasi (`v1.2.3`), boslukssuz
`what?No` bolunur; JP tirnak ici cumle (`「…。」`) tek parca kalir; `…`
(U+2026) ve tam genislik nokta `．` (U+FF0E) terminator DEGILDIR; simetrik
ASCII tirnakta (`A. "B."`) acilis tirnagi kapanis sayilip ONCEKI cumleye
yapisir (`A. "` + `B."`; kayipsiz, uydurma yok -- Tester-A K-2). Olcu:
`test_k3a_*` (2 segment 3+1 cumle, tek cagri, 4 giris, dogru dagitim),
`test_k3b_*` (Y1: KR/JP/karisik, uc dilde ayni; T2-1: alti terminator ayri
ayri), `test_k3c_*` (Y2: 1/1/0/0 + aynen), `test_k3d_*` (kayipsizlik: harf/
rakam dizisi), `test_k3e_*` (T2-2: yalniz yer tutucu parcasi gitmez, yaninda
metin varsa gider, bildirilmemisse gider; cumle sinirinda uc segment),
`test_k3_*`; `real_check.py` #3 (JP paragraf), #4 (KR tek segment), #4b
(`。。。` aynen); `evidence/olcum-4-*` (gercek model: `{PLAYER}!` aynen).

## K4 -- dil kodu ACIK, uc bicimli; `source_lang=None` desteklenmez

NLLB dil algilamaz. Kabul edilen kaynak kodlari (buyuk/kucuk harf duyarsiz,
bosluk kirpma YOK): NLLB (`jpn_Jpan`, `kor_Hang`, `zho_Hans`, `eng_Latn`),
ISO 639-1 (`ja`, `ko`, `zh`, `en`), T-006 `OcrLanguage` degerleri (`japan`,
`korean`, `chinese`, `english`). Hedef: `tr`, `tur`, `tur_Latn`, `turkish`.
Disi ya da `None` ya da `str` olmayan -> `ProviderUnavailable`, motor
kurulmaz; dogrulama BOS istekte de yapilir. Turkce kaynak olamaz.
Kaynak belirteci token dizisinin BASINA, `"</s>"` SONA;
`target_prefix=[["tur_Latn"]]*n` (C4; olcum-1 [3]/[4]: `hypotheses[0][0]
== "tur_Latn"`, hipotezde `</s>` yok). `detected_lang` cozumlenen NLLB
kodudur (algilama degil, kullanilan kod). Olcu: `test_k4_*` (4 dil x 3
bicim x buyuk/kucuk; 8 gecersiz kod); `real_check.py` #8.

## K5 -- yer tutucu: tam alt dize kontrolu + KABA onarim (C9, O1)

`Segment.placeholders` icindeki her dize ciktida tam alt dize olarak
aranir; eksikse SONA eklenir (listedeki sirayla, boslukla). Sayim (O1):
gereken adet `max(1, kaynak_metin.count(yt))`, mevcut adet
`cikti.count(yt)`; fark kadar eklenir -- normalizer her gecisi ayri oge
verir (`("%s","%s")`), `in` kontrolu tek gecisle tatmin olurdu. Onarim
SEGMENT duzeyindedir (yer tutucu baska cumleye kaysa da sayilir).

Kaba ve belgelidir `[ÖLÇÜLMÜYOR]`: model yer tutucuyu DUSURUR (C9: JP `{0}`)
ya da BOZAR (O1: `[Mill]` -> `[Mill'de]`, `<T0>` -> `T0'yi`; EN'de
`{PLAYER}` dusuyor). Bozulmus bicim tam alt dize olarak bulunmadigi icin
eklenir -> ciktida hem bozuk hem eklenmis kopya olabilir. Gercek cozum
Katman 0 (sozluk/yer tutucu stratejisi) ya da Katman 2 (LLM).
`glossary_hits`, `tm_examples`, `style_profile`, `image_crops` KABUL
EDILIR, OKUNMAZ, UYGULANMAZ `[ÖLÇÜLMÜYOR]` -- NMT'ye sozluk zorlanamaz (C9).
Olcu: `test_k5_*` (dusen -> sonda; korunan -> dokunulmaz; bozuk -> ekli;
`%s` x2 sayim; AST: dort alan adi modulde gecmez; dolu istek == duz istek);
`real_check.py` #5.

## K6 -- hata siniflandirmasi

(a) `model_dir`de DORT zorunlu dosyadan biri yoksa (`model.bin`,
`sentencepiece.bpe.model`, `shared_vocabulary.txt`, `config.json`; O4)
`ModelMissingError` MOTOR KURULMADAN (fabrika sayaci 0); mesajda eksik
dosya adlari; `__cause__` yok. Denetim VARLIK denetimidir (`is_file`),
boyut denetlenmez: sifir baytlik `model.bin` fabrikada CT2 `RuntimeError`
("incomplete") -> (b); bos sentencepiece protosu kurulumda sessiz,
`encode`de `RuntimeError` -> (b) (olcum-1 [7]; saglayici uzerinden
olculdu: ikisi de `ProviderUnavailable`, `__cause__` `RuntimeError`,
olcum-2 [B]/[C]). Checksum ModelManager'in
isidir (tasarim 13). `model_dir` yapimda `Path`/`str` olmali, degilse
`TypeError`; var olmasi yapimda ARANMAZ (K10).
(b) Fabrika (kurulum) istisnasi: `TranslatorError` oldugu gibi;
`FileNotFoundError` -> `ModelMissingError`; baska `Exception` ->
`ProviderUnavailable` (`__cause__` ozgun). Kurulum basarisizsa ornek
tutulmaz; sonraki `translate` kurulumu YENIDEN dener (otomatik yeniden
deneme YOK). Ceviri sirasinda motor/`encode`/`decode` istisnasi ->
`ProviderUnavailable` (`__cause__` ozgun); motor ciktisi bozuksa (dizi
degil, `.hypotheses` yok/bos, token `str` degil, `decode` `str`
dondurmuyor) -> `ProviderUnavailable`.
(c) Hizalama / cumle sayisi -> `ContractViolation` (K2).
Sarmalayan hata mesajlari yalniz TIP ADI ve SAYI tasir; kaynak/ceviri
metni asla (PROTOKOL 7) -- olcu iki nobetcili: kaynak metinde VE motor
ciktisinda / bozuk motor nesnesinin repr'inde (T2-3; `{cikti!r}`,
`{nesne!r}`, `{ilk!r}` ekleyen uygulama duser,
`test_k6_hata_mesajlari_kaynak_metni_tasimaz[*-nobetcili-*]`).
`ProviderTimeout` v1'de FIRLATILMAZ (butce yok,
`translate_batch` senkron ve iptal edilemez; ust katman zaman asimi uygular)
`[ÖLÇÜLMÜYOR]`. Olcu: `test_k6_*`; `real_check.py` #8.

## K7 -- model dosyalari BAYT ile acilir (C5)

sentencepiece ASCII-disi mutlak yolu ACAMIYOR (bu depo yolu `çeviri`
icerir; olcum-1 [1]: `model_file=<yol>` -> `RuntimeError`).
`_varsayilan_fabrika` `SentencePieceProcessor(model_proto=<bayt>)` kurar;
`model_file=` HIC kullanilmaz. CT2 yolu acabiliyor; `str(model_dir.resolve())`
(MUTLAK) verilir. Olcu: `test_k7_*` (fabrika AST'sinde `model_proto=` var,
`model_file=` yok, `read_bytes` + `.resolve()` var); `real_check.py` #7
(ASCII-disi gecici dizine kopya).

## K8 -- is parcacigi ACIK; ceza varsayilan KAPALI (T-006 K3, C7)

`threads` in `[1, os.cpu_count()]`; `None` -> `min(8, cpu_count)`; aralik
disi `ValueError`; tam sayi olmayan (`bool` dahil) `TypeError`; `np.int64`
gibi `Integral` duz `int`e duzlestirilir. Deger `intra_threads` olarak
gider; `inter_threads=1`; `device="cpu"`, `compute_type="int8"`. Fabrikaya
giden params sozlugu tam olarak bu dort anahtardir (`motor_parametreleri()`,
her cagrida taze kopya).

`repetition_penalty` varsayilan `1.0` = CEZASIZ: C7'de `>1` tekrari
HALUSINASYONLA takas etti ("Ba'at Colu"); ceza parametreleri kalite
karari, altin set olmadan secilemez `[ÖLÇÜLMÜYOR]`. Yapilandirilabilir:
`1.0` iken `translate_batch`e HIC gecilmez (CT2 varsayilani; olcum-1 [5]:
acik `1.0` ile gecilmemis ayni hipotezleri verir), `>1.0` iken `float`
olarak aynen gider (olcum-2 [D]: `1.2` gercek CT2'de hatasiz, cikti farkli). `< 1.0` (tekrari odullendirir), `nan`/`inf` ->
`ValueError`; sayi olmayan/`bool` -> `TypeError`. `beam_size` varsayilan 4
(C2/C3 kalitesi bununla olculdu; 2 ve 1 daha hizli, kalite `[ÖLÇÜLMÜYOR]`),
`>= 1` tam sayi, aynen gider. Olcu: `test_k8_*`.

## K9 -- sure ve `latency_ms`

`latency_ms` `translate`in kendi duvar saati (`perf_counter`), motor
KURULUMU HARIC (ilk cagrida fabrika suresi dusulur; gercek modelde ilk
cagri duvar 611 ms / `latency_ms` 91 ms, olcum-2 [F]). Butce (Y3): JAPAN 4
cumle tek batch, beam=4, 8 iplik -> <= 350 ms medyan (olculdu 307-316;
olcum-1 [9]: 311). `max_decoding_length=256` ACIK gecilir (O2). CT2 girdiyi
`max_input_length=1024` token'da SESSIZCE KIRPAR ve `translate_batch`
IPTAL EDILEMEZ: 843 token'lik noktalamasiz girdi 5.9 s, 500 cumlelik batch
22.6 s (KRT olctu) -- ust katman zaman asimi/parcalama uygular
`[ÖLÇÜLMÜYOR]`. Sure disaridan olculur; saglayici `last_timing` tutmaz.
Olcu: `test_k9_*`; `real_check.py` #6.

## K10 -- tembel kurulum, tek ornek, kapatma, loglama

`__init__` kutuphaneye ve dosya sistemine DOKUNMAZ (yalniz arguman
dogrulama). Ilk gonderimli `translate` dosyalari denetler, fabrikayi
cagirir; sonrakiler ayni motoru kullanir. `close()` idempotent; motor,
`encode` ve `decode` referanslari BIRAKILIR (weakref olu; gercek modelde
`close()` + `gc.collect()` sonrasi calisma kumesi 751 -> 47 MB, olcum-3);
sonrasi `translate` -> `ProviderUnavailable`
(bos istek dahil), fabrika yeniden CAGRILMAZ. Baglam yoneticisi DEGIL.
Sira: kapali mi -> istek/dil dogrulama -> bolme -> (gonderilecek varsa)
tembel kurulum -> ceviri -> sayim -> birlestirme -> onarim ->
`ensure_aligned`.

Loglama (PROTOKOL 7): bu modulde `print`, `sys.std*`, `os.write`, `logging`
ve `warnings` YOK; hicbir kanala kaynak/ceviri metni yazilmaz. Olcu
(DAVRANIS, T-006 K7 deseni): `test_k10_soguk_*` / `test_k10_sicak_*` --
iki nobetci (Latin + CJK) ile `capfd` sifir bayt, kok logger DEBUG `caplog`
+ `Logger.handle` kancasi (propagate=False, adi bilinmeyen logger dahil),
`warnings`; 7 pozitif kontrol sahte saglayici kanala ozgu mesajla
(`match=`: stdout / stderr / log kaydi / warnings kaydi -- T2-3) DUSER,
`FakeProvider` gecer; AST ikincil. CT2'nin C++ logu (stderr, varsayilan WARNING) global
seviyesine DOKUNULMAZ; gercek kosumda olculdu: kurulum + uc dilde ceviri
boyunca alt surecin stdout/stderr'i 0 bayt (olcum-2 [A]); birim testte
`[ÖLÇÜLMÜYOR]` (K1 bariyeri).
Thread-safe DEGILDIR: tek isci ipliginden kullanilir (tasarim 5.5).
"""
from __future__ import annotations

import math
import numbers
import os
import re
import time
from collections.abc import Callable, Sequence
from enum import StrEnum
from pathlib import Path
from typing import Final, Protocol

from src.contracts.errors import (
    ContractViolation,
    ModelMissingError,
    ProviderUnavailable,
    TranslatorError,
)
from src.contracts.interfaces import TranslationProvider, ensure_aligned
from src.contracts.models import TranslationRequest, TranslationResult

__all__ = [
    "NmtDili",
    "CeviriMotoru",
    "MotorFabrikası",
    "LocalNmtProvider",
    "cumlelere_bol",
    "modele_gider",
    "kaynak_dili_coz",
    "hedef_dili_coz",
    "zorunlu_model_dosyalari",
    "eksik_model_dosyalari",
]


class NmtDili(StrEnum):
    """NLLB dil kodlari -- sabit tablo (C4). `StrEnum`: profil JSON'una yazilir."""

    JAPAN = "jpn_Jpan"
    KOREAN = "kor_Hang"
    CHINESE = "zho_Hans"
    ENGLISH = "eng_Latn"
    TURKISH = "tur_Latn"


class CeviriMotoru(Protocol):
    """CT2 `Translator`in bize gereken yuzu.

    Gercek imzada ilk parametrenin adi `source`dur ve KONUMSAL cagrilir
    (olcum-1 [3]: `tokens=` anahtariyla cagri `TypeError`); bu modul her
    zaman konumsal gecer. Donus: her girdi icin `.hypotheses` tasiyan nesne
    (`hypotheses[0]` = `["tur_Latn", <token>...]`, `</s>` yok).
    """

    def translate_batch(
        self,
        tokens: list[list[str]],
        *,
        target_prefix: list[list[str]],
        beam_size: int,
        max_decoding_length: int,
        **kw: object,
    ) -> Sequence[object]: ...


MotorFabrikası = Callable[
    [Path, dict[str, object]],
    tuple[CeviriMotoru, Callable[[str], list[str]], Callable[[list[str]], str]],
]
"""`(model_dir, motor_params) -> (motor, encode, decode)`. Tek enjeksiyon dikisi (K1)."""


_SAGLAYICI_KIMLIGI: Final = "local-nmt-nllb200-600m-int8"
_SON_BELIRTECI: Final = "</s>"
_MAKS_COZUM_UZUNLUGU: Final = 256
"""K9/O2: `max_decoding_length` ACIK gecilir (CT2 varsayilani da 256)."""
_VARSAYILAN_PARCACIK: Final = 8
"""K8: `threads=None` -> `min(8, cpu_count)` (C2: 8 iplik ile olculdu)."""

_ZORUNLU_DOSYALAR: Final[tuple[str, ...]] = (
    "model.bin",
    "sentencepiece.bpe.model",
    "shared_vocabulary.txt",
    "config.json",
)
"""K6 (a): dordu de yoksa `ModelMissingError` motor kurulmadan (O4)."""

_KAYNAK_KODLARI: Final[dict[str, NmtDili]] = {
    "jpn_jpan": NmtDili.JAPAN, "ja": NmtDili.JAPAN, "japan": NmtDili.JAPAN,
    "kor_hang": NmtDili.KOREAN, "ko": NmtDili.KOREAN, "korean": NmtDili.KOREAN,
    "zho_hans": NmtDili.CHINESE, "zh": NmtDili.CHINESE, "chinese": NmtDili.CHINESE,
    "eng_latn": NmtDili.ENGLISH, "en": NmtDili.ENGLISH, "english": NmtDili.ENGLISH,
}
"""K4: kucuk harfe indirilmis kabul kumesi -- NLLB + ISO 639-1 + `OcrLanguage` degeri."""

_HEDEF_KODLARI: Final[dict[str, NmtDili]] = {
    "tr": NmtDili.TURKISH, "tur": NmtDili.TURKISH, "tur_latn": NmtDili.TURKISH, "turkish": NmtDili.TURKISH,
}

_TERMINATORLER: Final = ".!?。！？"
"""K3 (Y1): cumle sonu isaretleri -- EVRENSEL, dile gore degil."""
_KAPANIS_ISARETLERI: Final = "」』）)\"'”’»"
"""K3: terminatorden sonra gelirse cumleye DAHIL edilen kapanis isaretleri."""
_CUMLE_DESENI: Final = re.compile(
    f"[^{re.escape(_TERMINATORLER)}]*[{re.escape(_TERMINATORLER)}]+(?:\\s*[{re.escape(_KAPANIS_ISARETLERI)}]+)*"
    f"|[^{re.escape(_TERMINATORLER)}]+\\Z"
)
"""Bir cumle: terminatorsuz govde + terminator dizisi + (bosluklu da olsa) kapanis isaretleri; ya da terminatorsuz kuyruk."""


# ---------------------------------------------------------------------------
# yardimcilar: dil / bolme / model dosyalari / parametre dogrulama
# ---------------------------------------------------------------------------


def kaynak_dili_coz(kod: object) -> NmtDili:
    """K4: `source_lang` -> NLLB kodu. Tablo disi, `None` ya da `str` olmayan -> `ProviderUnavailable`."""
    if not isinstance(kod, str):
        raise ProviderUnavailable(
            "kaynak dili verilmedi ya da str degil: bu saglayici dil ALGILAMAZ "
            f"(source_lang={type(kod).__name__}); kabul: {sorted(_KAYNAK_KODLARI)}"
        )
    dil = _KAYNAK_KODLARI.get(kod.lower())
    if dil is None:
        raise ProviderUnavailable(f"desteklenmeyen kaynak dili kodu: {kod!r}; kabul: {sorted(_KAYNAK_KODLARI)}")
    return dil


def hedef_dili_coz(kod: object) -> NmtDili:
    """K4: `target_lang` -> `NmtDili.TURKISH`. Tablo disi -> `ProviderUnavailable`."""
    if not isinstance(kod, str):
        raise ProviderUnavailable(f"hedef dili str degil: {type(kod).__name__}; kabul: {sorted(_HEDEF_KODLARI)}")
    dil = _HEDEF_KODLARI.get(kod.lower())
    if dil is None:
        raise ProviderUnavailable(f"desteklenmeyen hedef dili kodu: {kod!r}; kabul: {sorted(_HEDEF_KODLARI)}")
    return dil


def cumlelere_bol(metin: str, *, ham: bool = False) -> list[str]:
    """K3: metni noktalamaya gore cumle parcalarina ayirir.

    `ham=False` (varsayilan): kirpilmis, bos olmayan parcalar -- modele
    giden/gecen birimler. `ham=True`: kirpilmamis eslesmeler; birlesimleri
    kaynagin AYNISIDIR (kayipsizlik olcusu icin).
    """
    parcalar: list[str] = [str(p) for p in _CUMLE_DESENI.findall(metin)]
    if ham:
        return parcalar
    return [p.strip() for p in parcalar if p.strip()]


def modele_gider(parca: str, yer_tutucular: Sequence[str] = ()) -> bool:
    """K3 (Y2, T2-2): parca, `yer_tutucular` CIKARILDIKTAN SONRA en az bir harf/rakam iceriyorsa modele gider.

    `{PLAYER}!` (`yer_tutucular=("{PLAYER}",)`) -> False (aynen gecer);
    `{PLAYER} is here.` -> True; `{PLAYER}!` yer tutucu bildirilmemisken -> True
    (bildirilmemis yer tutucu METINDIR). Her gecis cikarilir; bos dize yok sayilir.
    """
    kalan = parca
    for yt in yer_tutucular:
        if yt:
            kalan = kalan.replace(yt, "")
    return any(ch.isalnum() for ch in kalan)


def zorunlu_model_dosyalari() -> tuple[str, ...]:
    """K6 (a): `model_dir`de aranan dort dosya adi."""
    return _ZORUNLU_DOSYALAR


def eksik_model_dosyalari(model_dir: Path) -> list[str]:
    """K6 (a): `model_dir`de dosya olarak BULUNMAYAN zorunlu adlar (varlik denetimi, boyut degil)."""
    return [ad for ad in _ZORUNLU_DOSYALAR if not (model_dir / ad).is_file()]


def _parcacik_sayisi(threads: object) -> int:
    """K8: kabul kapisi + duzlestirme + aralik denetimi `[1, cpu_count]` (T-006 K3 ile ayni)."""
    cekirdek = os.cpu_count() or 1
    if threads is None:
        return min(_VARSAYILAN_PARCACIK, cekirdek)
    if isinstance(threads, bool) or not isinstance(threads, numbers.Integral):
        raise TypeError(f"threads tam sayi olmali, gelen: {threads!r}")
    n = int(threads)
    if not 1 <= n <= cekirdek:
        raise ValueError(f"threads aralik disi: {n} (izinli [1, {cekirdek}]; -1/'otomatik' YASAK)")
    return n


def _isin_genisligi(beam_size: object) -> int:
    """K8: `beam_size` `>= 1` tam sayi (`bool` degil)."""
    if isinstance(beam_size, bool) or not isinstance(beam_size, numbers.Integral):
        raise TypeError(f"beam_size tam sayi olmali, gelen: {beam_size!r}")
    n = int(beam_size)
    if n < 1:
        raise ValueError(f"beam_size >= 1 olmali, gelen: {n}")
    return n


def _tekrar_cezasi(repetition_penalty: object) -> float:
    """K8: `repetition_penalty` sonlu `float`, `>= 1.0` (1.0 = kapali); `< 1` tekrari odullendirir."""
    if isinstance(repetition_penalty, bool) or not isinstance(repetition_penalty, numbers.Real):
        raise TypeError(f"repetition_penalty sayi olmali, gelen: {repetition_penalty!r}")
    x = float(repetition_penalty)
    if not math.isfinite(x) or x < 1.0:
        raise ValueError(f"repetition_penalty sonlu ve >= 1.0 olmali, gelen: {x!r}")
    return x


# ---------------------------------------------------------------------------
# gercek kutuphane fabrikasi (K1: import yalniz burada)
# ---------------------------------------------------------------------------


def _varsayilan_fabrika(  # pragma: no cover -- K1: gercek model, real_check.py ile denetleniyor
    model_dir: Path, params: dict[str, object]
) -> tuple[CeviriMotoru, Callable[[str], list[str]], Callable[[list[str]], str]]:
    """Gercek kutuphaneyi kurar: sentencepiece BAYT ile (K7), CT2 MUTLAK yolla.

    `params` `Translator` yapicisina aynen acilir (`device`, `compute_type`,
    `inter_threads`, `intra_threads`). Istisnalar saglayiciya yayilir ve
    orada siniflandirilir (K6 b).

    `[ÖLÇÜLMÜYOR]` birim testte (K1 bariyeri): bu govde yalniz
    `real_check.py` ile kosulur (#1-#8). Kutuphanenin bozuk model dosyasinda
    verdigi hata metinleri (`"incomplete"`, `INTERNAL`) burada yakalanmaz;
    saglayici tip adiyla `ProviderUnavailable` uretir.
    """
    import ctranslate2  # type: ignore[import-untyped]
    import sentencepiece

    sp = sentencepiece.SentencePieceProcessor(model_proto=(model_dir / "sentencepiece.bpe.model").read_bytes())
    motor = ctranslate2.Translator(str(model_dir.resolve()), **params)

    def encode(metin: str) -> list[str]:
        return [str(t) for t in sp.encode(metin, out_type=str)]

    def decode(tokenler: list[str]) -> str:
        return str(sp.decode(tokenler))

    return motor, encode, decode


# ---------------------------------------------------------------------------
# motor ciktisi dogrulama + yer tutucu onarimi
# ---------------------------------------------------------------------------


def _hipotez_tokenleri(cikti: object, beklenen: int, hedef_kodu: str) -> list[list[str]]:
    """K2/K6: motor ciktisi -> her cumle icin token listesi (hedef belirteci atilmis).

    Sayi uyusmazligi -> `ContractViolation`; bicim bozuklugu ->
    `ProviderUnavailable`. Mesajlar yalniz sayi/tip tasir (PROTOKOL 7).
    """
    if not isinstance(cikti, Sequence) or isinstance(cikti, (str, bytes)):
        raise ProviderUnavailable(f"motor dizi yerine {type(cikti).__name__} dondurdu")
    if len(cikti) != beklenen:
        raise ContractViolation(
            f"motor gonderilen cumle sayisi kadar hipotez dondurmedi: cumle={beklenen}, "
            f"hipotez={len(cikti)} (provider={_SAGLAYICI_KIMLIGI!r})"
        )
    sonuc: list[list[str]] = []
    for nesne in cikti:
        hipotezler = getattr(nesne, "hypotheses", None)
        if not isinstance(hipotezler, Sequence) or isinstance(hipotezler, (str, bytes)) or len(hipotezler) == 0:
            raise ProviderUnavailable(f"motor ciktisinda hipotez listesi yok ya da bos: {type(nesne).__name__}")
        ilk = hipotezler[0]
        if not isinstance(ilk, Sequence) or isinstance(ilk, (str, bytes)):
            raise ProviderUnavailable(f"hipotez token dizisi degil: {type(ilk).__name__}")
        tokenler = list(ilk)
        if not all(isinstance(t, str) for t in tokenler):
            raise ProviderUnavailable("hipotez tokenleri str degil")
        if tokenler and tokenler[0] == hedef_kodu:
            tokenler = tokenler[1:]  # C4: ilk token hedef dil belirteci, ATILIR
        sonuc.append(tokenler)
    return sonuc


def _yer_tutuculari_onar(cikti: str, kaynak: str, yer_tutucular: Sequence[str]) -> str:
    """K5: eksik yer tutucularini (sayimla) sona ekler; tam ise dokunmaz."""
    islenen: set[str] = set()
    ekler: list[str] = []
    for yt in yer_tutucular:
        if not yt or yt in islenen:
            continue
        islenen.add(yt)
        gereken = max(1, kaynak.count(yt))
        ekler.extend([yt] * (gereken - cikti.count(yt)))
    if not ekler:
        return cikti
    return " ".join([cikti, *ekler]) if cikti else " ".join(ekler)


# ---------------------------------------------------------------------------
# saglayici
# ---------------------------------------------------------------------------


class LocalNmtProvider(TranslationProvider):
    """Yerel NMT ceviri saglayicisi -- `TranslationProvider`in Katman 1 uygulamasi.

    Args:
        model_dir: ZORUNLU model dizini (`Path` ya da `str`); dort zorunlu
            dosya ilk `translate`te aranir (K6). Dosyalar BAYT ile acilir (K7).
        threads: CT2 `intra_threads` (K8). `None` -> `min(8, cpu_count)`;
            `[1, cpu_count]` disi `ValueError`; tam sayi olmayan `TypeError`.
        beam_size: isin genisligi, varsayilan 4 (C2 ile olculdu); `>= 1`.
        repetition_penalty: varsayilan `1.0` = CEZASIZ (C7); `1.0` iken
            motora HIC gecilmez; `>= 1.0` sonlu sayi.
        motor_fabrikasi: enjeksiyon dikisi (K1). `None` -> gercek kutuphane.

    Yapim kutuphaneye ve dosya sistemine DOKUNMAZ (K10). Thread-safe
    DEGILDIR: tek isci ipliginden kullanilir (tasarim 5.5).
    """

    def __init__(
        self,
        *,
        model_dir: Path,
        threads: int | None = None,
        beam_size: int = 4,
        repetition_penalty: float = 1.0,
        motor_fabrikasi: MotorFabrikası | None = None,
    ) -> None:
        if isinstance(model_dir, str):
            model_dir = Path(model_dir)
        if not isinstance(model_dir, Path):
            raise TypeError(f"model_dir Path ya da str olmali, gelen: {type(model_dir).__name__}")
        self._model_dir: Path = model_dir
        self._threads = _parcacik_sayisi(threads)
        self._beam_size = _isin_genisligi(beam_size)
        self._repetition_penalty = _tekrar_cezasi(repetition_penalty)
        self._fabrika: MotorFabrikası = motor_fabrikasi if motor_fabrikasi is not None else _varsayilan_fabrika
        self._motor: CeviriMotoru | None = None
        self._encode: Callable[[str], list[str]] | None = None
        self._decode: Callable[[list[str]], str] | None = None
        self._kapali = False

    # -- gozlem -------------------------------------------------------------

    @property
    def provider_id(self) -> str:
        return _SAGLAYICI_KIMLIGI

    @property
    def model_dir(self) -> Path:
        return self._model_dir

    @property
    def threads(self) -> int:
        """Duzlestirilmis, aralik icinde is parcacigi sayisi (K8)."""
        return self._threads

    @property
    def beam_size(self) -> int:
        return self._beam_size

    @property
    def repetition_penalty(self) -> float:
        return self._repetition_penalty

    def motor_parametreleri(self) -> dict[str, object]:
        """Fabrikaya gidecek `params` sozlugu -- her cagrida TAZE kopya (K8).

        Tam olarak dort anahtar: `device`, `compute_type`, `inter_threads`,
        `intra_threads`. PUBLIC: testler ve `real_check` fabrikasiz gozlemleyebilsin.
        """
        return {
            "device": "cpu",
            "compute_type": "int8",
            "inter_threads": 1,
            "intra_threads": self._threads,
        }

    # -- sozlesme -----------------------------------------------------------

    def translate(self, request: TranslationRequest) -> TranslationResult:
        """`request.segments`i cevirir; `translations` segmentlerle birebir hizali.

        Sira: kapali mi (K10) -> istek/dil dogrulama (K2, K4; motor cagrilmaz)
        -> cumle bolme + parca suzgeci (K3; suzgec `segment.placeholders`
        cikarildiktan sonra karar verir, T2-2) -> gonderilecek parca varsa
        tembel kurulum (K6 a, K10) -> TEK `translate_batch` (K3) -> cumle
        sayimi (K2) -> birlestirme (K3) -> yer tutucu onarimi (K5) ->
        `ensure_aligned`.

        `glossary_hits`, `tm_examples`, `style_profile`, `image_crops` kabul
        edilir, OKUNMAZ `[ÖLÇÜLMÜYOR]` (K5). `ProviderTimeout` firlatilmaz;
        `translate_batch` iptal edilemez `[ÖLÇÜLMÜYOR]` (K9).

        Raises:
            ProviderUnavailable: saglayici kapatilmissa; dil kodu tablo disi ya
                da `None` ise; kurulum/ceviri kutuphane hatasi verdiyse; motor
                ciktisi bozuksa.
            ModelMissingError: zorunlu model dosyasi yoksa (fabrika cagrilmaz).
            ContractViolation: `request` `TranslationRequest` degilse; segment
                metni `str` degilse; motor cumle sayisi kadar hipotez
                dondurmediyse; hizalama bozuksa.
        """
        t0 = time.perf_counter()
        if self._kapali:
            raise ProviderUnavailable("saglayici kapatildi; close() sonrasi translate cagrilamaz")
        if not isinstance(request, TranslationRequest):
            raise ContractViolation(f"translate TranslationRequest bekler, gelen: {type(request).__name__}")
        kaynak = kaynak_dili_coz(request.source_lang)
        hedef = hedef_dili_coz(request.target_lang)

        # K3: segment -> parcalar; (parca, gonderim indeksi | -1)
        planlar: list[list[tuple[str, int]]] = []
        gonderilecek: list[str] = []
        for i, segment in enumerate(request.segments):
            if not isinstance(segment.text, str):
                raise ContractViolation(f"segment {i} metni str degil: {type(segment.text).__name__}")
            if not all(isinstance(yt, str) for yt in segment.placeholders):
                raise ContractViolation(f"segment {i} placeholders icinde str olmayan oge var")
            plan: list[tuple[str, int]] = []
            for parca in cumlelere_bol(segment.text):
                if modele_gider(parca, segment.placeholders):  # T2-2: yer tutucular cikarildiktan sonra karar
                    plan.append((parca, len(gonderilecek)))
                    gonderilecek.append(parca)
                else:
                    plan.append((parca, -1))
            planlar.append(plan)

        kurulum_s = 0.0
        ceviriler: list[str] = []
        if gonderilecek:
            tk0 = time.perf_counter()
            motor, encode, decode = self._motor_al()
            kurulum_s = time.perf_counter() - tk0  # K9: kurulum latency'ye girmez
            ceviriler = self._cevir(motor, encode, decode, gonderilecek, kaynak, hedef)

        sonuclar: list[str] = []
        for segment, plan in zip(request.segments, planlar, strict=True):
            if not any(idx >= 0 for _, idx in plan):
                cikti = segment.text  # K3 (Y2): hicbir parcasi modele gitmeyen segment AYNEN
            else:
                cikti = " ".join(ceviriler[idx] if idx >= 0 else parca for parca, idx in plan)
            sonuclar.append(_yer_tutuculari_onar(cikti, segment.text, segment.placeholders))

        sonuc = TranslationResult(
            translations=tuple(sonuclar),
            provider_id=_SAGLAYICI_KIMLIGI,
            latency_ms=(time.perf_counter() - t0 - kurulum_s) * 1000.0,
            from_cache=False,
            detected_lang=kaynak.value,
            partial=False,
        )
        ensure_aligned(request, sonuc)
        return sonuc

    def close(self) -> None:
        """Motoru, `encode`/`decode`yu BIRAKIR (weakref olu); idempotent.

        Sonrasi `translate` -> `ProviderUnavailable`, fabrika yeniden cagrilmaz (K10).
        """
        self._motor = None
        self._encode = None
        self._decode = None
        self._kapali = True

    # -- ic yardimcilar ----------------------------------------------------

    def _motor_al(self) -> tuple[CeviriMotoru, Callable[[str], list[str]], Callable[[list[str]], str]]:
        """Tembel kurulum (K10) + dosya denetimi (K6 a) + kurulum hatasi siniflandirmasi (K6 b)."""
        if self._motor is not None and self._encode is not None and self._decode is not None:
            return self._motor, self._encode, self._decode
        eksik = eksik_model_dosyalari(self._model_dir)
        if eksik:
            raise ModelMissingError(f"model dosyasi yok: {', '.join(eksik)} (dizin: {self._model_dir})")
        try:
            motor, encode, decode = self._fabrika(self._model_dir, self.motor_parametreleri())
        except TranslatorError:
            raise
        except FileNotFoundError as e:
            raise ModelMissingError("model dosyasi kurulum sirasinda bulunamadi") from e
        except Exception as e:
            raise ProviderUnavailable(f"ceviri motoru kurulamadi: {type(e).__name__}") from e
        self._motor, self._encode, self._decode = motor, encode, decode
        return motor, encode, decode

    def _cevir(
        self,
        motor: CeviriMotoru,
        encode: Callable[[str], list[str]],
        decode: Callable[[list[str]], str],
        parcalar: list[str],
        kaynak: NmtDili,
        hedef: NmtDili,
    ) -> list[str]:
        """K3/K4/K8: parcalari tokenlestirir, TEK batch cevirir, cozumler; hatalari siniflandirir (K6 b)."""
        try:
            tokenler = [[kaynak.value, *encode(p), _SON_BELIRTECI] for p in parcalar]
        except TranslatorError:
            raise
        except Exception as e:
            raise ProviderUnavailable(f"kaynak metin tokenlestirilemedi: {type(e).__name__}") from e

        ek: dict[str, object] = {}
        if self._repetition_penalty != 1.0:
            ek["repetition_penalty"] = self._repetition_penalty  # K8: 1.0 iken HIC gecilmez
        try:
            cikti = motor.translate_batch(
                tokenler,
                target_prefix=[[hedef.value]] * len(tokenler),
                beam_size=self._beam_size,
                max_decoding_length=_MAKS_COZUM_UZUNLUGU,
                **ek,
            )
        except TranslatorError:
            raise
        except Exception as e:
            raise ProviderUnavailable(f"ceviri basarisiz: {type(e).__name__}") from e

        hipotezler = _hipotez_tokenleri(cikti, len(tokenler), hedef.value)
        try:
            metinler = [decode(h) for h in hipotezler]
        except TranslatorError:
            raise
        except Exception as e:
            raise ProviderUnavailable(f"ceviri cozumlenemedi: {type(e).__name__}") from e
        if not all(isinstance(m, str) for m in metinler):
            raise ProviderUnavailable("decode str dondurmedi")
        return metinler


# ---------------------------------------------------------------------------
# protokol uyum satiri -- mypy --strict bunu DOGRULAR
# ---------------------------------------------------------------------------

_uyum_fabrika: MotorFabrikası = _varsayilan_fabrika
