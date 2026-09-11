"""T-007 -- `LocalNmtProvider` birim testleri (K1: gercek model YOK).

Her test `motor_fabrikasi=` ile SAHTE bir fabrika enjekte eder; gercek
kutuphane bu surecte hic yuklenmez (sefin `conftest.py` bariyeri
`ctranslate2*`/`sentencepiece*` import'unu `RuntimeError` ile keser). Model
dizini her zaman `tmp_path` (bos dosyalar); `models/` OKUNMAZ. Gercek davranis
yalniz `.agents/tasks/T-007/real_check.py` ile (ayri surec) olculur.

Referanslar BAGIMSIZ kanaldan (PROTOKOL 4.6/8): NLLB dil kodlari, zorunlu
model dosya adlari, motor parametre adlari ve `translate_batch` anahtar
kelimeleri burada SABIT yazilidir -- saglayicinin kendi tablosundan
TURETILMEZ. Kaynak: `olgular.txt` C4/C5, `evidence/olcum-1-ct2-api-olgulari.txt`.

Ceviri/kaynak metni hicbir yere basilmaz (PROTOKOL 7); `print` yok. K10
pozitif kontrolleri nobetciyi bir kanala YAZAR ama o kanal `capfd`/`caplog`/
`catch_warnings` ile yutulur; konsola ULASMAZ.

Sahte motor bicimi gercek CT2 ciktisini taklit eder (olcum-1 [4]):
`translate_batch(source, target_prefix=..., beam_size=..., ...)` -> her girdi
icin `.hypotheses[0] == ["tur_Latn", <token>...]` (hedef belirteci basta,
`</s>` yok). Sahte `encode` parcayi TEK token yapar (`[parca]`), `decode`
tokenleri `"".join` eder; boylece motorun kaydettigi `tokens[i][1]` tam olarak
modele giden PARCA metnidir ve ozdes cevirici (echo) parcayi aynen dondurur.
"""
from __future__ import annotations

import ast
import dataclasses
import gc
import inspect
import logging
import os
import sys
import time
import warnings
import weakref
from collections.abc import Callable, Iterator, Sequence
from pathlib import Path
from typing import Any

import pytest

from src.contracts.errors import ContractViolation, ModelMissingError, ProviderUnavailable
from src.contracts.interfaces import FakeProvider, TranslationProvider
from src.contracts.models import Pair, Rect, Segment, TermHit, TranslationRequest, TranslationResult
from src.translate import local_nmt
from src.translate.local_nmt import (
    CeviriMotoru,
    LocalNmtProvider,
    NmtDili,
    cumlelere_bol,
    hedef_dili_coz,
    kaynak_dili_coz,
    modele_gider,
    zorunlu_model_dosyalari,
)

KAYNAK = Path(local_nmt.__file__)

# --- BAGIMSIZ referanslar (olgular C4/C5, olcum-1) ----------------------------

SAGLAYICI_KIMLIGI = "local-nmt-nllb200-600m-int8"
HEDEF = "tur_Latn"
SON = "</s>"
NLLB: dict[str, str] = {"JAPAN": "jpn_Jpan", "KOREAN": "kor_Hang", "CHINESE": "zho_Hans", "ENGLISH": "eng_Latn"}
MODEL_DOSYALARI: tuple[str, ...] = ("model.bin", "sentencepiece.bpe.model", "shared_vocabulary.txt", "config.json")
MAKS_COZUM = 256
KAYNAK_BICIMLERI: dict[str, tuple[str, str, str]] = {  # NLLB, ISO 639-1, OcrLanguage degeri
    "jpn_Jpan": ("jpn_Jpan", "ja", "japan"),
    "kor_Hang": ("kor_Hang", "ko", "korean"),
    "zho_Hans": ("zho_Hans", "zh", "chinese"),
    "eng_Latn": ("eng_Latn", "en", "english"),
}
HEDEF_BICIMLERI: tuple[str, ...] = ("tr", "tur", "tur_Latn", "turkish")

JP_CUMLELER = ("長老マルクス", "村の長老があなたを待っています。", "水車小屋を過ぎて東の道を行きなさい。", "日が暮れたら道を外れないように。")
JP_PARAGRAF = "村の長老があなたを待っています。水車小屋を過ぎて東の道を行きなさい。日が暮れたら道を外れないように。"
KR_CUMLELER = ("마을 장로가 당신을 기다리고 있습니다.", "방앗간을 지나 동쪽 길로 가십시오.")


# --- sahte motor / fabrika -----------------------------------------------------


@dataclasses.dataclass
class SahteHipotez:
    """CT2 `TranslationResult`'un bize gereken yuzu: `.hypotheses`."""

    hypotheses: Any


def _tek_token(metin: str) -> list[str]:
    return [metin]


def _birlestir(tokenler: list[str]) -> str:
    return "".join(tokenler)


class SahteMotor:
    """`translate_batch` cagrilarini KAYDEDER; `cevir` ile parca -> ceviri uretir.

    `cevir` verilmezse echo (ozdes). `cikti` verilirse ham donus o olur (K2
    sayi/bicim mutantlari icin). `gecikme_s` motoru uyutur (K9).
    """

    def __init__(
        self,
        cevir: Callable[[str], str] | None = None,
        cikti: Callable[[list[list[str]]], Any] | None = None,
        hata: BaseException | None = None,
        gecikme_s: float = 0.0,
    ) -> None:
        self.cevir = cevir
        self.cikti = cikti
        self.hata = hata
        self.gecikme_s = gecikme_s
        self.calls: list[dict[str, Any]] = []

    def translate_batch(
        self,
        tokens: list[list[str]],
        *,
        target_prefix: list[list[str]],
        beam_size: int,
        max_decoding_length: int,
        **kw: object,
    ) -> Sequence[object]:
        self.calls.append(
            {
                "tokens": [list(t) for t in tokens],
                "target_prefix": [list(p) for p in target_prefix],
                "beam_size": beam_size,
                "max_decoding_length": max_decoding_length,
                "kw": dict(kw),
            }
        )
        if self.gecikme_s:
            time.sleep(self.gecikme_s)
        if self.hata is not None:
            raise self.hata
        if self.cikti is not None:
            return self.cikti(tokens)  # type: ignore[no-any-return]
        return [SahteHipotez([[HEDEF, self._cevir("".join(t[1:-1]))]]) for t in tokens]

    def _cevir(self, parca: str) -> str:
        return parca if self.cevir is None else self.cevir(parca)

    @property
    def call_count(self) -> int:
        return len(self.calls)

    @property
    def son(self) -> dict[str, Any]:
        return self.calls[-1]

    def gonderilen_parcalar(self, cagri: int = -1) -> list[str]:
        """`tokens[i][1]` -- sahte encode tek token yaptigi icin bu, modele giden parca metnidir."""
        return [t[1] for t in self.calls[cagri]["tokens"]]

    def tum_gonderilen_parcalar(self) -> list[str]:
        return [t[1] for c in self.calls for t in c["tokens"]]


class SahteFabrika:
    """`(model_dir, params)` cagrilarini KAYDEDER, sayar, `(motor, encode, decode)` dondurur."""

    def __init__(
        self,
        motor: SahteMotor | None = None,
        hata: BaseException | None = None,
        gecikme_s: float = 0.0,
        encode: Callable[[str], list[str]] | None = None,
        decode: Callable[[list[str]], str] | None = None,
    ) -> None:
        self.motor = motor if motor is not None else SahteMotor()
        self.hata = hata
        self.gecikme_s = gecikme_s
        self.encode = encode if encode is not None else _tek_token
        self.decode = decode if decode is not None else _birlestir
        self.calls = 0
        self.model_dirs: list[Path] = []
        self.params: list[dict[str, object]] = []

    def __call__(
        self, model_dir: Path, params: dict[str, object]
    ) -> tuple[CeviriMotoru, Callable[[str], list[str]], Callable[[list[str]], str]]:
        self.calls += 1
        self.model_dirs.append(model_dir)
        self.params.append(dict(params))
        if self.gecikme_s:
            time.sleep(self.gecikme_s)
        if self.hata is not None:
            raise self.hata
        return self.motor, self.encode, self.decode

    @property
    def son(self) -> dict[str, object]:
        return self.params[-1]


def model_dosyalari(dizin: Path, haric: str | None = None) -> None:
    """`dizin`e dort zorunlu adla BOS dosyalar koyar (K6 olcusu); `haric` verilirse o dosya konmaz."""
    for ad in MODEL_DOSYALARI:
        if ad != haric:
            (dizin / ad).write_bytes(b"")


def saglayici(tmp_path: Path, fabrika: SahteFabrika, **ek: Any) -> LocalNmtProvider:
    """Sahte fabrikali saglayici; dort model dosyasi `tmp_path`te hazir."""
    model_dosyalari(tmp_path)
    return LocalNmtProvider(model_dir=tmp_path, motor_fabrikasi=fabrika, **ek)


def istek(
    metinler: Sequence[str],
    kaynak: str | None = "jpn_Jpan",
    hedef: Any = "tr",
    yer_tutucular: tuple[str, ...] = (),
    **ek: Any,
) -> TranslationRequest:
    """Her segmente ayni `yer_tutucular` demeti verilir."""
    segs = tuple(
        Segment(text=m, bbox=Rect(0, i * 40, 800, 36), placeholders=tuple(yer_tutucular))
        for i, m in enumerate(metinler)
    )
    return TranslationRequest(segments=segs, source_lang=kaynak, target_lang=hedef, **ek)


def _modul_agaci() -> ast.Module:
    return ast.parse(KAYNAK.read_text(encoding="utf-8"))


def _fonksiyon(agac: ast.AST, ad: str) -> ast.FunctionDef:
    for d in ast.walk(agac):
        if isinstance(d, ast.FunctionDef) and d.name == ad:
            return d
    raise AssertionError(f"fonksiyon yok: {ad}")


def _import_kokleri(dugum: ast.AST) -> set[str]:
    kokler: set[str] = set()
    for d in ast.walk(dugum):
        if isinstance(d, ast.Import):
            kokler.update(a.name.split(".")[0] for a in d.names)
        elif isinstance(d, ast.ImportFrom):
            kokler.add((d.module or "").split(".")[0])
    return kokler


def _docstring_disi_dize_sabitleri(agac: ast.Module) -> list[str]:
    """Modul/sinif/fonksiyon docstring'i OLMAYAN her `str` sabiti (getattr(..., "alan") kacagi icin)."""
    docstringler: set[int] = set()
    for d in ast.walk(agac):
        if isinstance(d, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and d.body:
            ilk = d.body[0]
            if isinstance(ilk, ast.Expr) and isinstance(ilk.value, ast.Constant) and isinstance(ilk.value.value, str):
                docstringler.add(id(ilk.value))
    return [
        d.value
        for d in ast.walk(agac)
        if isinstance(d, ast.Constant) and isinstance(d.value, str) and id(d) not in docstringler
    ]


# ===========================================================================
# K1 -- testler gercek modeli yuklemez; modul duzeyinde ctranslate2/sentencepiece yok
# ===========================================================================


def test_k1_modul_duzeyinde_kutuphane_import_yok() -> None:
    for dugum in _modul_agaci().body:  # yalniz MODUL duzeyi
        if isinstance(dugum, ast.Import):
            assert all(a.name.split(".")[0] not in ("ctranslate2", "sentencepiece") for a in dugum.names)
        if isinstance(dugum, ast.ImportFrom):
            assert (dugum.module or "").split(".")[0] not in ("ctranslate2", "sentencepiece")


def test_k1_kutuphane_importu_yalniz_varsayilan_fabrika_govdesinde() -> None:
    agac = _modul_agaci()
    assert {"ctranslate2", "sentencepiece"} <= _import_kokleri(_fonksiyon(agac, "_varsayilan_fabrika"))
    for d in ast.walk(agac):  # baska hicbir fonksiyonda kutuphane importu yok
        if isinstance(d, ast.FunctionDef) and d.name != "_varsayilan_fabrika":
            assert not ({"ctranslate2", "sentencepiece"} & _import_kokleri(d)), d.name


def test_k1_sahte_fabrikayla_kosum_kutuphane_yuklemez(tmp_path: Path) -> None:
    f = SahteFabrika()
    saglayici(tmp_path, f).translate(istek(["A。"]))
    assert not any(k.split(".")[0] in ("ctranslate2", "sentencepiece") for k in sys.modules)
    assert f.calls == 1


def test_uyum_translationprovider_altsinifi() -> None:
    assert issubclass(LocalNmtProvider, TranslationProvider)
    assert not hasattr(LocalNmtProvider, "__enter__") and not hasattr(LocalNmtProvider, "__exit__")  # K10: baglam yoneticisi degil
    p = LocalNmtProvider(model_dir=Path("yok"))
    assert p.provider_id == SAGLAYICI_KIMLIGI
    assert isinstance(LocalNmtProvider.provider_id, property)


def test_uyum_nmtdili_degerleri() -> None:
    assert {m.name: m.value for m in NmtDili} == {**NLLB, "TURKISH": HEDEF}
    assert all(isinstance(m, str) for m in NmtDili)


def test_uyum_imza_paketle_birebir() -> None:
    imza = inspect.signature(LocalNmtProvider.__init__)
    adlar = [n for n in imza.parameters if n != "self"]
    assert adlar == ["model_dir", "threads", "beam_size", "repetition_penalty", "motor_fabrikasi"]
    assert all(imza.parameters[n].kind is inspect.Parameter.KEYWORD_ONLY for n in adlar)
    assert imza.parameters["model_dir"].default is inspect.Parameter.empty
    assert imza.parameters["threads"].default is None
    assert imza.parameters["beam_size"].default == 4
    assert imza.parameters["repetition_penalty"].default == 1.0
    assert imza.parameters["motor_fabrikasi"].default is None
    with pytest.raises(TypeError):
        LocalNmtProvider()  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        LocalNmtProvider(Path("x"))  # type: ignore[call-arg]


def test_uyum_gozlem_ozellikleri(tmp_path: Path) -> None:
    p = LocalNmtProvider(model_dir=tmp_path, threads=2, beam_size=3, repetition_penalty=1.25)
    assert p.model_dir == tmp_path and p.threads == 2 and p.beam_size == 3 and p.repetition_penalty == 1.25


def test_uyum_model_dir_str_kabul_baska_tip_typeerror(tmp_path: Path) -> None:
    f = SahteFabrika()
    model_dosyalari(tmp_path)
    p = LocalNmtProvider(model_dir=str(tmp_path), motor_fabrikasi=f)  # type: ignore[arg-type]
    p.translate(istek(["A。"]))
    assert f.model_dirs[0] == tmp_path and isinstance(f.model_dirs[0], Path)
    with pytest.raises(TypeError):
        LocalNmtProvider(model_dir=None)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        LocalNmtProvider(model_dir=5)  # type: ignore[arg-type]


# ===========================================================================
# K2 -- hizalama: ensure_aligned + cumle sayisi denetimi
# ===========================================================================


def _n_hipotez(n: int) -> Callable[[list[list[str]]], list[SahteHipotez]]:
    return lambda tokens: [SahteHipotez([[HEDEF, "x"]]) for _ in range(n)]


@pytest.mark.parametrize("donen", [2, 4, 0])
def test_k2_uc_giris_farkli_sayida_cikis_contractviolation(tmp_path: Path, donen: int) -> None:
    f = SahteFabrika(SahteMotor(cikti=_n_hipotez(donen)))
    with pytest.raises(ContractViolation):
        saglayici(tmp_path, f).translate(istek(["A。", "B。", "C。"]))
    assert f.motor.call_count == 1


def test_k2_segment_sayisi_tutup_cumle_sayisi_tutmayan_kayma_contractviolation(tmp_path: Path) -> None:
    """O3: 2 segment (3+1 cumle) icin motor 3 hipotez donerse `ensure_aligned` GORMEZ; cumle sayimi yakalar."""
    f = SahteFabrika(SahteMotor(cikti=_n_hipotez(3)))
    with pytest.raises(ContractViolation):
        saglayici(tmp_path, f).translate(istek(["A。B。C。", "D。"]))
    f2 = SahteFabrika(SahteMotor(cikti=_n_hipotez(2)))  # segment sayisiyla ayni: 2 -- yine ihlal
    with pytest.raises(ContractViolation):
        saglayici(tmp_path, f2).translate(istek(["A。B。C。", "D。"]))


def test_k2_bos_istek_bos_demet_motor_ve_fabrika_cagrilmaz(tmp_path: Path) -> None:
    f = SahteFabrika()
    r = saglayici(tmp_path, f).translate(istek([]))
    assert r.translations == () and isinstance(r.translations, tuple)
    assert r.latency_ms >= 0 and isinstance(r.latency_ms, float)
    assert r.provider_id == SAGLAYICI_KIMLIGI and r.from_cache is False and r.partial is False
    assert f.calls == 0 and f.motor.call_count == 0


def test_k2_ast_translate_govdesinde_ensure_aligned_cagrisi_var() -> None:
    agac = _modul_agaci()
    sinif = next(d for d in agac.body if isinstance(d, ast.ClassDef) and d.name == "LocalNmtProvider")
    translate = next(d for d in sinif.body if isinstance(d, ast.FunctionDef) and d.name == "translate")
    cagrilar = [ast.unparse(d.func) for d in ast.walk(translate) if isinstance(d, ast.Call)]
    assert "ensure_aligned" in cagrilar


def test_k2_sonuc_alanlari_ve_hizali_cikti(tmp_path: Path) -> None:
    f = SahteFabrika(SahteMotor(cevir=lambda p: "T(" + p + ")"))
    r = saglayici(tmp_path, f).translate(istek(["A。", "B。", "C。"]))
    assert isinstance(r, TranslationResult)
    assert r.translations == ("T(A。)", "T(B。)", "T(C。)")
    assert r.provider_id == SAGLAYICI_KIMLIGI and r.from_cache is False and r.partial is False
    assert r.detected_lang == NLLB["JAPAN"]


def test_k2_istek_tipi_ve_segment_metni_contractviolation(tmp_path: Path) -> None:
    f = SahteFabrika()
    p = saglayici(tmp_path, f)
    with pytest.raises(ContractViolation):
        p.translate(["A。"])  # type: ignore[arg-type]
    with pytest.raises(ContractViolation):
        p.translate(None)  # type: ignore[arg-type]
    kotu = TranslationRequest(segments=(Segment(text=None, bbox=Rect(0, 0, 1, 1)),), source_lang="ja", target_lang="tr")  # type: ignore[arg-type]
    with pytest.raises(ContractViolation):
        p.translate(kotu)
    kotu_yt = TranslationRequest(segments=(Segment(text="A。", bbox=Rect(0, 0, 1, 1), placeholders=(5,)),), source_lang="ja", target_lang="tr")  # type: ignore[arg-type]
    with pytest.raises(ContractViolation):
        p.translate(kotu_yt)
    assert f.calls == 0 and f.motor.call_count == 0


# ===========================================================================
# K3 -- cumle bolme (noktalamaya gore) + parca suzgeci + tek batch + birlestirme
# ===========================================================================


def test_k3a_iki_segment_uc_arti_bir_cumle_tek_cagri_dort_giris_dogru_dagitim(tmp_path: Path) -> None:
    f = SahteFabrika(SahteMotor(cevir=lambda p: "T(" + p + ")"))
    r = saglayici(tmp_path, f).translate(istek(["A。B。C。", "D。"]))
    assert f.motor.call_count == 1
    assert f.motor.gonderilen_parcalar() == ["A。", "B。", "C。", "D。"]
    assert r.translations == ("T(A。) T(B。) T(C。)", "T(D。)")


@pytest.mark.parametrize(
    ("metin", "parcalar"),
    [
        ("A. B.", ["A.", "B."]),  # Y1: KR ASCII nokta
        ("A。B。", ["A。", "B。"]),  # JP
        ("A! B？ C.", ["A!", "B？", "C."]),  # karisik
        (" ".join(KR_CUMLELER), list(KR_CUMLELER)),  # KR fixture'inin kendisi (v1 kurali 1 parca veriyordu)
        (JP_PARAGRAF, list(JP_CUMLELER[1:])),  # C8 paragrafi -> 3
        ("A.B.", ["A.", "B."]),  # bosluk sarti YOK (paket v2: evrensel kume)
        ("Wait... what?!", ["Wait...", "what?!"]),  # terminator dizisi tek parcada
        ("A.」B.", ["A.」", "B."]),  # kapanis isareti cumleye dahil
        ("A. 」 B.", ["A. 」", "B."]),  # arada bosluk olsa da
        ("「A。」「B。」", ["「A。」", "「B。」"]),
        ("A。\nB。", ["A。", "B。"]),
        ("A", ["A"]),  # terminator yok -> tek parca
        ("A。B", ["A。", "B"]),  # sonda terminatorsuz kuyruk
    ],
)
def test_k3b_bolme_noktalamaya_gore_dile_gore_degil(tmp_path: Path, metin: str, parcalar: list[str]) -> None:
    f = SahteFabrika()
    for kaynak in ("jpn_Jpan", "kor_Hang", "eng_Latn"):  # ayni metin uc dilde AYNI bolunur
        saglayici(tmp_path, f).translate(istek([metin], kaynak=kaynak))
        assert f.motor.gonderilen_parcalar() == parcalar, (kaynak, metin)


@pytest.mark.parametrize(
    ("metin", "gonderilen", "cikti"),
    [
        ("A。？", ["A。？"], "A。？"),  # ardisik terminator ayni parcada (Y2)
        ("「A。」", ["「A。」"], "「A。」"),
        ("。。。", [], "。。。"),  # harf/rakam yok -> modele GITMEZ, aynen
        ("...", [], "..."),
        ("？", [], "？"),
        ("」", [], "」"),
        ("   ", [], "   "),  # yalniz bosluk aynen
        ("", [], ""),  # bos metin aynen
        ("A。 。。。", ["A。"], "A。 。。。"),  # gecis parcasi cikti sirasinda yerinde
        ("。。。 A。", ["A。"], "。。。 A。"),
        ("A。 」 B。", ["A。 」", "B。"], "A。 」 B。"),  # bosluklu kapanis isareti onceki cumleye ait
        ("3.5", ["3.", "5"], "3. 5"),  # bilinen zayiflik: ondalik bolunur (rakam iceren parca modele gider)
        ("Dr. Smith", ["Dr.", "Smith"], "Dr. Smith"),  # bilinen zayiflik: kisaltma bolunur
    ],
)
def test_k3c_parca_suzgeci_harf_rakam_olmayan_modele_gitmez_aynen_gecer(
    tmp_path: Path, metin: str, gonderilen: list[str], cikti: str
) -> None:
    f = SahteFabrika()  # echo: modele giden parca aynen doner -> cikti = birlestirme kurali
    r = saglayici(tmp_path, f).translate(istek([metin]))
    assert f.motor.tum_gonderilen_parcalar() == gonderilen
    assert r.translations == (cikti,)
    if not gonderilen:
        assert f.motor.call_count == 0 and f.calls == 0  # gonderecek parca yoksa motor KURULMAZ bile


def test_k3c_gecis_parcasi_ceviriden_ayirt_edilir(tmp_path: Path) -> None:
    """Echo degil: ceviri parcalari degisir, gecis parcalari DEGISMEZ -- ikisi ayni cikti dizisinde."""
    f = SahteFabrika(SahteMotor(cevir=lambda p: "T"))
    r = saglayici(tmp_path, f).translate(istek(["A。 。。。 B。", "。。。", "C. ..."]))
    assert r.translations == ("T 。。。 T", "。。。", "T ...")
    assert f.motor.call_count == 1 and f.motor.gonderilen_parcalar() == ["A。", "B。", "C."]


def test_k3c_modele_giden_her_parcada_harf_veya_rakam_var(tmp_path: Path) -> None:
    f = SahteFabrika()
    metinler = ["A。？！", "。。。x。。。", "1.", "!?.。！？", "「」『』", "a", "  b  。 ", "。a。b。"]
    saglayici(tmp_path, f).translate(istek(metinler))
    parcalar = f.motor.tum_gonderilen_parcalar()
    assert parcalar and all(any(ch.isalnum() for ch in p) for p in parcalar)
    assert all(p == p.strip() and p for p in parcalar)


def test_k3d_kayipsizlik_harf_rakam_dizisi_korunur(tmp_path: Path) -> None:
    f = SahteFabrika()
    metinler = [*JP_CUMLELER, JP_PARAGRAF, *KR_CUMLELER, "A! B？ C.", "Wait... what?! 」", "3.5 km. OK", "x.y.z", "。。。"]
    r = saglayici(tmp_path, f).translate(istek(metinler))
    def harf(s: str) -> str:
        return "".join(ch for ch in s if ch.isalnum())

    for kaynak, cikti in zip(metinler, r.translations, strict=True):
        assert harf(cikti) == harf(kaynak)
    # modele giden parcalarin birlesimi de kaynak dizisine esit (segment sirasi korunur)
    tum = "".join(ch for p in f.motor.tum_gonderilen_parcalar() for ch in p if ch.isalnum())
    assert tum == "".join(ch for m in metinler for ch in m if ch.isalnum())


def test_k3_cumlelere_bol_yardimcisi_ve_modele_gider() -> None:
    """Ikincil (mekanizma): public yardimci -- tester dogrudan olcebilsin."""
    assert cumlelere_bol("A. B.") == ["A.", "B."]
    assert cumlelere_bol("") == [] and cumlelere_bol("   ") == []
    assert cumlelere_bol("。。。") == ["。。。"] and not modele_gider("。。。")
    assert modele_gider("A。") and modele_gider("5") and modele_gider("３") and not modele_gider("？」 ")
    # ham parcalarin birlesimi kaynakla ayni (bosluk dahil kayip yok) -- rastgele karisim
    metin = "「はい。」 Wait...what?! 3.5 km. x」』）)\"' ！？。 sonu"
    assert "".join(cumlelere_bol(metin, ham=True)) == metin


def test_k3_bes_yuz_cumlelik_segment_tek_batch(tmp_path: Path) -> None:
    f = SahteFabrika()
    metin = "".join(f"c{i}。" for i in range(500))
    r = saglayici(tmp_path, f).translate(istek([metin]))
    assert f.motor.call_count == 1 and len(f.motor.son["tokens"]) == 500
    assert r.translations[0].split(" ") == [f"c{i}。" for i in range(500)]


def test_k3_birden_cok_segment_tek_cagri_sira_korunur(tmp_path: Path) -> None:
    f = SahteFabrika(SahteMotor(cevir=lambda p: p.upper()))
    r = saglayici(tmp_path, f).translate(istek(["b. a.", "d", "c! e?"]))
    assert f.motor.call_count == 1
    assert f.motor.gonderilen_parcalar() == ["b.", "a.", "d", "c!", "e?"]
    assert r.translations == ("B. A.", "D", "C! E?")


def test_k3_olculmuyor_damgasi_bilinen_zayifliklar_docstringde() -> None:
    doc = local_nmt.__doc__ or ""
    assert "[ÖLÇÜLMÜYOR]" in doc and "Dr. Smith" in doc and "3.5" in doc


# ===========================================================================
# K4 -- dil kodu acik, uc bicimli; None desteklenmez
# ===========================================================================


@pytest.mark.parametrize("kaynak", [None, "xx", "tr", "tur_Latn", "jpn", "", "ja-JP", " ja"])
def test_k4_kaynak_kodu_tablo_disi_provider_unavailable_motor_kurulmaz(tmp_path: Path, kaynak: Any) -> None:
    f = SahteFabrika()
    with pytest.raises(ProviderUnavailable):
        saglayici(tmp_path, f).translate(istek(["A。"], kaynak=kaynak))
    assert f.calls == 0 and f.motor.call_count == 0


@pytest.mark.parametrize("nllb", list(KAYNAK_BICIMLERI))
@pytest.mark.parametrize("bicim", [0, 1, 2])
@pytest.mark.parametrize("buyuk", [False, True])
def test_k4_uc_bicim_dort_dil_kaynak_belirteci_basta_son_sonda(tmp_path: Path, nllb: str, bicim: int, buyuk: bool) -> None:
    kod = KAYNAK_BICIMLERI[nllb][bicim]
    kod = kod.upper() if buyuk else kod
    f = SahteFabrika()
    r = saglayici(tmp_path, f).translate(istek(["A。", "B。"], kaynak=kod))
    for t in f.motor.son["tokens"]:
        assert t[0] == nllb and t[-1] == SON and len(t) == 3
    assert f.motor.son["target_prefix"] == [[HEDEF], [HEDEF]]
    assert r.detected_lang == nllb
    assert kaynak_dili_coz(kod).value == nllb


@pytest.mark.parametrize("hedef", HEDEF_BICIMLERI + tuple(h.upper() for h in HEDEF_BICIMLERI))
def test_k4_hedef_dort_bicim_kabul(tmp_path: Path, hedef: str) -> None:
    f = SahteFabrika()
    saglayici(tmp_path, f).translate(istek(["A。"], hedef=hedef))
    assert f.motor.son["target_prefix"] == [[HEDEF]]
    assert hedef_dili_coz(hedef) is NmtDili.TURKISH


@pytest.mark.parametrize("hedef", ["tr-TR", "tr_TR", "en", "eng_Latn", "", "turkce", None, 5])
def test_k4_hedef_tablo_disi_provider_unavailable(tmp_path: Path, hedef: Any) -> None:
    f = SahteFabrika()
    with pytest.raises(ProviderUnavailable):
        saglayici(tmp_path, f).translate(istek(["A。"], hedef=hedef))
    assert f.calls == 0
    with pytest.raises(ProviderUnavailable):
        hedef_dili_coz(hedef)


def test_k4_kaynak_dili_coz_none_ve_enum_uyesi() -> None:
    with pytest.raises(ProviderUnavailable):
        kaynak_dili_coz(None)
    assert kaynak_dili_coz(NmtDili.KOREAN) is NmtDili.KOREAN
    with pytest.raises(ProviderUnavailable):
        kaynak_dili_coz(NmtDili.TURKISH)  # hedef dili kaynak olamaz
    with pytest.raises(ProviderUnavailable):
        kaynak_dili_coz(7)


def test_k4_kaynak_dogrulamasi_bos_istekte_de_calisir(tmp_path: Path) -> None:
    """Bos istek bile gecersiz dil koduyla kabul edilmez -- dogrulama segment sayisindan bagimsiz."""
    with pytest.raises(ProviderUnavailable):
        saglayici(tmp_path, SahteFabrika()).translate(istek([], kaynak=None))


# ===========================================================================
# K5 -- yer tutucu: tam alt dize kontrolu + kaba onarim; sozluk/TM/stil okunmaz
# ===========================================================================


def test_k5_dusen_yer_tutucu_sona_eklenir_sirayla_boslukla(tmp_path: Path) -> None:
    f = SahteFabrika(SahteMotor(cevir=lambda p: "Seni bekliyor."))  # C9: model {0}/{1} dusurdu
    r = saglayici(tmp_path, f).translate(istek(["{0}があなたを{1}で待っています。"], yer_tutucular=("{0}", "{1}")))
    assert r.translations == ("Seni bekliyor. {0} {1}",)


def test_k5_korunan_yer_tutucuya_dokunulmaz(tmp_path: Path) -> None:
    f = SahteFabrika(SahteMotor(cevir=lambda p: "{0} {1}'de seni bekliyor."))
    r = saglayici(tmp_path, f).translate(istek(["{0} is waiting for you at the {1}."], kaynak="en", yer_tutucular=("{0}", "{1}")))
    assert r.translations == ("{0} {1}'de seni bekliyor.",)
    f2 = SahteFabrika(SahteMotor(cevir=lambda p: "<T0> sizi <T1>'de bekliyor."))  # ikinci nokta: farkli bicim
    r2 = saglayici(tmp_path, f2).translate(istek(["<T0> waits at <T1>."], kaynak="en", yer_tutucular=("<T0>", "<T1>")))
    assert r2.translations == ("<T0> sizi <T1>'de bekliyor.",)


def test_k5_yalniz_eksik_olan_eklenir(tmp_path: Path) -> None:
    f = SahteFabrika(SahteMotor(cevir=lambda p: "{1} bekliyor"))
    r = saglayici(tmp_path, f).translate(istek(["{0} x {1}。"], yer_tutucular=("{0}", "{1}")))
    assert r.translations == ("{1} bekliyor {0}",)


def test_k5_bozuk_bicim_tam_alt_dize_degil_eklenir(tmp_path: Path) -> None:
    """O1: `[Mill]` -> `[Mill'de]`, `<T0>` -> `T0'yi`: tam alt dize bulunmaz, eklenir (cikti hem bozuk hem ekli -- belgeli)."""
    f = SahteFabrika(SahteMotor(cevir=lambda p: "[Marcus] sizi [Mill'de] bekliyor."))
    r = saglayici(tmp_path, f).translate(istek(["[Marcus] waits at the [Mill]."], kaynak="en", yer_tutucular=("[Marcus]", "[Mill]")))
    assert r.translations == ("[Marcus] sizi [Mill'de] bekliyor. [Mill]",)


def test_k5_ayni_yer_tutucu_birden_cok_gecis_sayim_ile(tmp_path: Path) -> None:
    """O1: normalizer her gecisi ayri oge verir (`("%s","%s")`); `in` tek gecisle tatmin olurdu -- sayim yapilir."""
    f = SahteFabrika(SahteMotor(cevir=lambda p: "%s ve"))  # ikinciyi dusurdu
    r = saglayici(tmp_path, f).translate(istek(["%s and %s."], kaynak="en", yer_tutucular=("%s", "%s")))
    assert r.translations == ("%s ve %s",)
    f2 = SahteFabrika(SahteMotor(cevir=lambda p: "%s ve %s"))  # ikisi de korundu -> dokunulmaz
    r2 = saglayici(tmp_path, f2).translate(istek(["%s and %s."], kaynak="en", yer_tutucular=("%s", "%s")))
    assert r2.translations == ("%s ve %s",)
    f3 = SahteFabrika(SahteMotor(cevir=lambda p: "yok"))  # ikisi de dustu, kaynakta 2 gecis, listede 1
    r3 = saglayici(tmp_path, f3).translate(istek(["%s and %s."], kaynak="en", yer_tutucular=("%s",)))
    assert r3.translations == ("yok %s %s",)


def test_k5_yer_tutucu_cok_cumleli_segmentte_segment_duzeyinde(tmp_path: Path) -> None:
    """Yer tutucu baska cumleye kaysa bile segment ciktisinda VAR -> eklenmez."""
    f = SahteFabrika(SahteMotor(cevir=lambda p: "{0} T" if p.startswith("B") else "T"))
    r = saglayici(tmp_path, f).translate(istek(["{0} A。B。"], yer_tutucular=("{0}",)))
    assert r.translations == ("T {0} T",)


def test_k5_gecis_parcali_segmentte_yer_tutucu_kaynakta_zaten_var(tmp_path: Path) -> None:
    r = saglayici(tmp_path, SahteFabrika()).translate(istek(["{0}"], yer_tutucular=("{0}",)))
    assert r.translations == ("{0}",)  # harf/rakum yok -> gecis; onarim eklemez (zaten var)


def test_k5_bos_placeholders_cikti_dokunulmaz(tmp_path: Path) -> None:
    f = SahteFabrika(SahteMotor(cevir=lambda p: "T"))
    r = saglayici(tmp_path, f).translate(istek(["{0} x。"]))
    assert r.translations == ("T",)


def test_k5_sozluk_tm_stil_gorsel_alanlari_okunmaz_ast() -> None:
    agac = _modul_agaci()
    erisimler = {d.attr for d in ast.walk(agac) if isinstance(d, ast.Attribute)}
    for alan in ("glossary_hits", "tm_examples", "style_profile", "image_crops"):
        assert alan not in erisimler, alan
    # dize olarak da gecmez (getattr(..., "glossary_hits") kacagi)
    for dize in _docstring_disi_dize_sabitleri(agac):
        assert dize not in ("glossary_hits", "tm_examples", "style_profile", "image_crops")


def test_k5_sozluk_tm_stil_dolu_istek_cikti_ve_motor_cagrisi_ayni(tmp_path: Path) -> None:
    f1, f2 = SahteFabrika(), SahteFabrika()
    duz = istek(["A。B。"])
    dolu = istek(
        ["A。B。"],
        glossary_hits=(TermHit("A", "X", 0, 1, segment_index=0),),
        tm_examples=(Pair("A。", "Y。"),),
        style_profile="resmi",
    )
    r1 = saglayici(tmp_path, f1).translate(duz)
    r2 = saglayici(tmp_path, f2).translate(dolu)
    assert r1.translations == r2.translations
    assert f1.motor.calls == f2.motor.calls


def test_k5_olculmuyor_damgasi_docstringde() -> None:
    doc = local_nmt.__doc__ or ""
    assert "glossary_hits" in doc and "[ÖLÇÜLMÜYOR]" in doc


# ===========================================================================
# K6 -- hata siniflandirmasi
# ===========================================================================


def test_k6_bos_dizin_modelmissing_fabrika_sifir_mesajda_dort_ad(tmp_path: Path) -> None:
    f = SahteFabrika()
    p = LocalNmtProvider(model_dir=tmp_path, motor_fabrikasi=f)
    with pytest.raises(ModelMissingError) as ei:
        p.translate(istek(["A。"]))
    assert f.calls == 0 and ei.value.__cause__ is None
    assert all(ad in str(ei.value) for ad in MODEL_DOSYALARI)
    assert zorunlu_model_dosyalari() == MODEL_DOSYALARI


@pytest.mark.parametrize("eksik", MODEL_DOSYALARI)
def test_k6_dort_dosyadan_biri_yoksa_modelmissing_adi_mesajda(tmp_path: Path, eksik: str) -> None:
    model_dosyalari(tmp_path, haric=eksik)
    f = SahteFabrika()
    with pytest.raises(ModelMissingError) as ei:
        LocalNmtProvider(model_dir=tmp_path, motor_fabrikasi=f).translate(istek(["A。"]))
    assert f.calls == 0
    assert eksik in str(ei.value)
    assert all(ad not in str(ei.value) for ad in MODEL_DOSYALARI if ad != eksik)


def test_k6_dort_bos_dosya_varsa_fabrika_cagrilir(tmp_path: Path) -> None:
    f = SahteFabrika()
    saglayici(tmp_path, f).translate(istek(["A。"]))
    assert f.calls == 1 and f.model_dirs == [tmp_path]


def test_k6_model_dir_dosya_ise_modelmissing(tmp_path: Path) -> None:
    dosya = tmp_path / "model.bin"
    dosya.write_bytes(b"")
    with pytest.raises(ModelMissingError):
        LocalNmtProvider(model_dir=dosya, motor_fabrikasi=SahteFabrika()).translate(istek(["A。"]))


def test_k6_dizin_yerine_ayni_adli_alt_dizin_dosya_sayilmaz(tmp_path: Path) -> None:
    model_dosyalari(tmp_path, haric="config.json")
    (tmp_path / "config.json").mkdir()
    f = SahteFabrika()
    with pytest.raises(ModelMissingError) as ei:
        LocalNmtProvider(model_dir=tmp_path, motor_fabrikasi=f).translate(istek(["A。"]))
    assert "config.json" in str(ei.value) and f.calls == 0


def test_k6_fabrika_istisnasi_siniflandirilir(tmp_path: Path) -> None:
    with pytest.raises(ProviderUnavailable) as e1:
        saglayici(tmp_path, SahteFabrika(hata=RuntimeError("kurulum"))).translate(istek(["A。"]))
    assert isinstance(e1.value.__cause__, RuntimeError)
    with pytest.raises(ProviderUnavailable) as e2:  # CT2 "File model.bin is incomplete" sinifi (olcum-1 [7])
        saglayici(tmp_path, SahteFabrika(hata=ValueError("bozuk"))).translate(istek(["A。"]))
    assert isinstance(e2.value.__cause__, ValueError)
    with pytest.raises(ModelMissingError) as e3:
        saglayici(tmp_path, SahteFabrika(hata=FileNotFoundError("model.bin"))).translate(istek(["A。"]))
    assert isinstance(e3.value.__cause__, FileNotFoundError)
    ozel = ModelMissingError("indirilemedi")
    with pytest.raises(ModelMissingError) as e4:  # sozlesme hatasi OLDUGU GIBI gecer
        saglayici(tmp_path, SahteFabrika(hata=ozel)).translate(istek(["A。"]))
    assert e4.value is ozel


def test_k6_fabrika_hatasindan_sonra_yeniden_denenebilir(tmp_path: Path) -> None:
    f = SahteFabrika(hata=RuntimeError("ilk"))
    p = saglayici(tmp_path, f)
    with pytest.raises(ProviderUnavailable):
        p.translate(istek(["A。"]))
    f.hata = None
    assert p.translate(istek(["A。"])).translations == ("A。",) and f.calls == 2


def test_k6_motor_istisnasi_provider_unavailable_cause_korunur(tmp_path: Path) -> None:
    ozgun = RuntimeError("motor patladi")
    with pytest.raises(ProviderUnavailable) as ei:
        saglayici(tmp_path, SahteFabrika(SahteMotor(hata=ozgun))).translate(istek(["A。"]))
    assert ei.value.__cause__ is ozgun
    ozel = ContractViolation("motorun kendi sozlesme hatasi")
    with pytest.raises(ContractViolation) as e2:  # TranslatorError sarilmaz
        saglayici(tmp_path, SahteFabrika(SahteMotor(hata=ozel))).translate(istek(["A。"]))
    assert e2.value is ozel


def test_k6_encode_decode_istisnasi_provider_unavailable(tmp_path: Path) -> None:
    def _enc(_m: str) -> list[str]:
        raise RuntimeError("INTERNAL")  # bos sentencepiece protosu encode'da patlar (olcum-1 [7])

    with pytest.raises(ProviderUnavailable) as e1:
        saglayici(tmp_path, SahteFabrika(encode=_enc)).translate(istek(["A。"]))
    assert isinstance(e1.value.__cause__, RuntimeError)

    def _dec(_t: list[str]) -> str:
        raise ValueError("decode")

    with pytest.raises(ProviderUnavailable) as e2:
        saglayici(tmp_path, SahteFabrika(decode=_dec)).translate(istek(["A。"]))
    assert isinstance(e2.value.__cause__, ValueError)


def test_k6_encode_decode_sozlesme_hatasi_oldugu_gibi_gecer(tmp_path: Path) -> None:
    """`TranslatorError` sarilmaz: encode/decode'dan gelen `ModelMissingError` aynen yuzeye cikar."""
    ozel = ModelMissingError("proto bozuk")

    def _enc(_m: str) -> list[str]:
        raise ozel

    with pytest.raises(ModelMissingError) as e1:
        saglayici(tmp_path, SahteFabrika(encode=_enc)).translate(istek(["A。"]))
    assert e1.value is ozel

    def _dec(_t: list[str]) -> str:
        raise ozel

    with pytest.raises(ModelMissingError) as e2:
        saglayici(tmp_path, SahteFabrika(decode=_dec)).translate(istek(["A。"]))
    assert e2.value is ozel


@pytest.mark.parametrize(
    "cikti",
    [
        lambda tokens: [object() for _ in tokens],  # .hypotheses yok
        lambda tokens: [SahteHipotez([]) for _ in tokens],  # bos hipotez listesi
        lambda tokens: [SahteHipotez(None) for _ in tokens],
        lambda tokens: [SahteHipotez([None]) for _ in tokens],
        lambda tokens: [SahteHipotez([[HEDEF, 5]]) for _ in tokens],  # token str degil
        lambda tokens: [SahteHipotez([[HEDEF, b"x"]]) for _ in tokens],
        lambda tokens: [SahteHipotez(["tur_Latn x"]) for _ in tokens],  # hipotez liste degil duz str
        lambda tokens: None,  # donus dizi degil
        lambda tokens: 7,
    ],
    ids=["attr-yok", "bos-hipotez", "None-hipotez", "None-eleman", "int-token", "bytes-token", "str-hipotez", "None-donus", "int-donus"],
)
def test_k6_bozuk_motor_ciktisi_provider_unavailable(tmp_path: Path, cikti: Callable[[list[list[str]]], Any]) -> None:
    with pytest.raises(ProviderUnavailable):
        saglayici(tmp_path, SahteFabrika(SahteMotor(cikti=cikti))).translate(istek(["A。"]))


def test_k6_decode_str_dondurmezse_provider_unavailable(tmp_path: Path) -> None:
    with pytest.raises(ProviderUnavailable):
        saglayici(tmp_path, SahteFabrika(decode=lambda t: 5)).translate(istek(["A。"]))  # type: ignore[arg-type,return-value]


def _patlayan_encode(_m: str) -> list[str]:
    raise RuntimeError("enc")


def _patlayan_decode(_t: list[str]) -> str:
    raise RuntimeError("dec")


def _sayi_donduren_decode(_t: list[str]) -> str:
    return 5  # type: ignore[return-value]


@pytest.mark.parametrize(
    ("fabrika", "hata"),
    [
        (lambda: SahteFabrika(SahteMotor(cikti=_n_hipotez(3))), ContractViolation),  # sayi uyusmazligi (2 cumle / 3 hipotez)
        (lambda: SahteFabrika(SahteMotor(cikti=lambda t: [SahteHipotez([[HEDEF, 5]]) for _ in t])), ProviderUnavailable),  # bozuk cikti
        (lambda: SahteFabrika(SahteMotor(hata=RuntimeError("motor"))), ProviderUnavailable),  # motor istisnasi
        (lambda: SahteFabrika(hata=RuntimeError("kurulum")), ProviderUnavailable),  # fabrika istisnasi
        (lambda: SahteFabrika(encode=_patlayan_encode), ProviderUnavailable),  # encode istisnasi
        (lambda: SahteFabrika(decode=_patlayan_decode), ProviderUnavailable),  # decode istisnasi
        (lambda: SahteFabrika(decode=_sayi_donduren_decode), ProviderUnavailable),  # decode str degil
    ],
    ids=["sayi", "bozuk-cikti", "motor", "fabrika", "encode", "decode", "decode-tip"],
)
def test_k6_hata_mesajlari_kaynak_metni_tasimaz(tmp_path: Path, fabrika: Callable[[], SahteFabrika], hata: type[Exception]) -> None:
    """PROTOKOL 7: hangi yoldan gelirse gelsin, istisna metni KAYNAK metni (nobetci) icermez."""
    nobetci = "NOBETCI-9c1e"
    with pytest.raises(hata) as ei:
        saglayici(tmp_path, fabrika()).translate(istek([nobetci + "。", "x " + nobetci + "."]))
    assert nobetci not in str(ei.value)
    assert nobetci not in repr(ei.value)


def test_k6_hata_mesaji_motor_hatasinin_metnini_tasimaz(tmp_path: Path) -> None:
    """Sarmalayan mesaj yalniz TIP ADI tasir; kutuphane hatasinin metni `__cause__`ta kalir."""
    nobetci = "NOBETCI-9c1e"
    with pytest.raises(ProviderUnavailable) as ei:
        saglayici(tmp_path, SahteFabrika(SahteMotor(hata=RuntimeError(nobetci)))).translate(istek(["A。"]))
    assert nobetci not in str(ei.value) and nobetci in str(ei.value.__cause__)


def test_k6_provider_timeout_firlatilmaz_olculmuyor_damgali() -> None:
    agac = _modul_agaci()
    assert "ProviderTimeout" not in {d.id for d in ast.walk(agac) if isinstance(d, ast.Name)}
    assert "ProviderTimeout" not in {a.name for d in ast.walk(agac) if isinstance(d, ast.ImportFrom) for a in d.names}
    doc = local_nmt.__doc__ or ""
    assert "ProviderTimeout" in doc and "[ÖLÇÜLMÜYOR]" in doc


def test_k6_hedef_belirteci_ilk_token_olarak_atilir_degilse_korunur(tmp_path: Path) -> None:
    """C4: `hypotheses[0][0] == "tur_Latn"` atilir; sahte motor belirtecsiz donerse token korunur."""
    f = SahteFabrika(SahteMotor(cikti=lambda tokens: [SahteHipotez([[HEDEF, "a", "b"]]), SahteHipotez([["a", "b"]])]))
    r = saglayici(tmp_path, f).translate(istek(["x。", "y。"]))
    assert r.translations == ("ab", "ab")


# ===========================================================================
# K7 -- model dosyalari BAYT ile acilir (sentencepiece ASCII-disi yol acamiyor)
# ===========================================================================


def _anahtar_argumanlar(fonk: ast.FunctionDef) -> set[str]:
    return {kw.arg for d in ast.walk(fonk) if isinstance(d, ast.Call) for kw in d.keywords if kw.arg}


def test_k7_gercek_fabrika_model_proto_var_model_file_yok() -> None:
    fabrika = _fonksiyon(_modul_agaci(), "_varsayilan_fabrika")
    anahtarlar = _anahtar_argumanlar(fabrika)
    assert "model_proto" in anahtarlar and "model_file" not in anahtarlar
    kaynak = ast.unparse(fabrika)
    assert "read_bytes" in kaynak and "sentencepiece.bpe.model" in kaynak
    assert ".resolve()" in kaynak  # CT2'ye mutlak yol


def test_k7_ast_tarayici_pozitif_kontrol() -> None:
    parca = ast.parse("def f(p):\n    x = S(model_file=str(p))\n    y = S(model_proto=p.read_bytes())\n")
    assert _anahtar_argumanlar(_fonksiyon(parca, "f")) == {"model_file", "model_proto"}


def test_k7_model_file_dizesi_modulde_hic_gecmez() -> None:
    assert all("model_file" not in dize for dize in _docstring_disi_dize_sabitleri(_modul_agaci()))


def test_k7_fabrikaya_verilen_model_dir_path_ve_params_ayri_kopya(tmp_path: Path) -> None:
    f = SahteFabrika()
    p = saglayici(tmp_path, f)
    p.translate(istek(["A。"]))
    assert isinstance(f.model_dirs[0], Path) and f.model_dirs[0] == tmp_path
    ps = p.motor_parametreleri()
    ps["intra_threads"] = 99
    assert p.motor_parametreleri()["intra_threads"] != 99  # her cagrida taze kopya


# ===========================================================================
# K8 -- is parcacigi acik; beam/ceza yapilandirilabilir; ceza 1.0 iken gecilmez
# ===========================================================================


@pytest.mark.parametrize("n", [4, 8])
def test_k8_threads_intra_aynen_inter_bir_cpu_int8(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, n: int) -> None:
    monkeypatch.setattr(os, "cpu_count", lambda: 32)
    f = SahteFabrika()
    saglayici(tmp_path, f, threads=n).translate(istek(["A。"]))
    assert f.son["intra_threads"] == n and type(f.son["intra_threads"]) is int
    assert f.son["inter_threads"] == 1
    assert f.son["device"] == "cpu" and f.son["compute_type"] == "int8"
    assert set(f.son) == {"device", "compute_type", "inter_threads", "intra_threads"}


def test_k8_threads_none_min8_cpu(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "cpu_count", lambda: 32)
    f = SahteFabrika()
    saglayici(tmp_path, f).translate(istek(["A。"]))
    assert f.son["intra_threads"] == 8
    monkeypatch.setattr(os, "cpu_count", lambda: 6)
    f2 = SahteFabrika()
    saglayici(tmp_path, f2, threads=None).translate(istek(["A。"]))
    assert f2.son["intra_threads"] == 6
    assert LocalNmtProvider(model_dir=tmp_path).threads == 6


def test_k8_threads_cpu_ustu_valueerror(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(os, "cpu_count", lambda: 8)
    with pytest.raises(ValueError):
        LocalNmtProvider(model_dir=tmp_path, threads=9)
    LocalNmtProvider(model_dir=tmp_path, threads=8)  # tam sinir gecer
    LocalNmtProvider(model_dir=tmp_path, threads=1)


@pytest.mark.parametrize("n", [0, -1, -8])
def test_k8_threads_sifir_ve_negatif_valueerror(tmp_path: Path, n: int) -> None:
    with pytest.raises(ValueError):
        LocalNmtProvider(model_dir=tmp_path, threads=n)


@pytest.mark.parametrize("n", [True, 2.0, "8", 4.5])
def test_k8_threads_tamsayi_olmayan_typeerror(tmp_path: Path, n: Any) -> None:
    with pytest.raises(TypeError):
        LocalNmtProvider(model_dir=tmp_path, threads=n)


def test_k8_cpu_count_none_ise_bir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(os, "cpu_count", lambda: None)
    assert LocalNmtProvider(model_dir=tmp_path).threads == 1
    with pytest.raises(ValueError):
        LocalNmtProvider(model_dir=tmp_path, threads=2)


def test_k8_repetition_penalty_varsayilan_1_hic_gecilmez(tmp_path: Path) -> None:
    f = SahteFabrika()
    saglayici(tmp_path, f).translate(istek(["A。"]))
    assert "repetition_penalty" not in f.motor.son["kw"]
    assert f.motor.son["kw"] == {}  # baska hicbir ek anahtar yok
    f2 = SahteFabrika()
    saglayici(tmp_path, f2, repetition_penalty=1.0).translate(istek(["A。"]))
    assert f2.motor.son["kw"] == {}


@pytest.mark.parametrize("rp", [1.2, 1.5, 2])
def test_k8_repetition_penalty_birden_buyukse_aynen_gider(tmp_path: Path, rp: float) -> None:
    f = SahteFabrika()
    saglayici(tmp_path, f, repetition_penalty=rp).translate(istek(["A。"]))
    assert f.motor.son["kw"] == {"repetition_penalty": float(rp)}
    assert type(f.motor.son["kw"]["repetition_penalty"]) is float


@pytest.mark.parametrize("rp", [0.0, 0.5, 0.999, -1.0, float("nan"), float("inf")])
def test_k8_repetition_penalty_birden_kucuk_veya_sonsuz_valueerror(tmp_path: Path, rp: float) -> None:
    with pytest.raises(ValueError):
        LocalNmtProvider(model_dir=tmp_path, repetition_penalty=rp)


@pytest.mark.parametrize("rp", [True, "1.2", None])
def test_k8_repetition_penalty_sayi_degilse_typeerror(tmp_path: Path, rp: Any) -> None:
    with pytest.raises(TypeError):
        LocalNmtProvider(model_dir=tmp_path, repetition_penalty=rp)


@pytest.mark.parametrize("beam", [4, 2, 1])
def test_k8_beam_size_aynen_max_decoding_length_256(tmp_path: Path, beam: int) -> None:
    f = SahteFabrika()
    saglayici(tmp_path, f, beam_size=beam).translate(istek(["A。"]))
    assert f.motor.son["beam_size"] == beam and type(f.motor.son["beam_size"]) is int
    assert f.motor.son["max_decoding_length"] == MAKS_COZUM


def test_k8_beam_size_varsayilan_4(tmp_path: Path) -> None:
    f = SahteFabrika()
    saglayici(tmp_path, f).translate(istek(["A。"]))
    assert f.motor.son["beam_size"] == 4


@pytest.mark.parametrize("beam", [0, -1])
def test_k8_beam_size_sifir_negatif_valueerror(tmp_path: Path, beam: int) -> None:
    with pytest.raises(ValueError):
        LocalNmtProvider(model_dir=tmp_path, beam_size=beam)


@pytest.mark.parametrize("beam", [True, 2.0, "4"])
def test_k8_beam_size_tamsayi_olmayan_typeerror(tmp_path: Path, beam: Any) -> None:
    with pytest.raises(TypeError):
        LocalNmtProvider(model_dir=tmp_path, beam_size=beam)


def test_k8_olculmuyor_damgasi_ceza_kalitesi_docstringde() -> None:
    doc = local_nmt.__doc__ or ""
    assert "repetition_penalty" in doc and "[ÖLÇÜLMÜYOR]" in doc


# ===========================================================================
# K9 -- latency_ms: translate'in duvar saati, kurulum HARIC
# ===========================================================================


def test_k9_latency_motor_suresini_kapsar(tmp_path: Path) -> None:
    f = SahteFabrika(SahteMotor(gecikme_s=0.03))
    r = saglayici(tmp_path, f).translate(istek(["A。"]))
    assert 30 <= r.latency_ms < 200 and type(r.latency_ms) is float


def test_k9_ilk_cagri_latency_fabrika_suresini_icermez(tmp_path: Path) -> None:
    f = SahteFabrika(gecikme_s=0.1)
    r = saglayici(tmp_path, f).translate(istek(["A。"]))
    assert f.calls == 1 and r.latency_ms < 100


def test_k9_bos_ve_gecis_istekte_latency_sifir_veya_pozitif(tmp_path: Path) -> None:
    p = saglayici(tmp_path, SahteFabrika())
    assert p.translate(istek([])).latency_ms >= 0
    assert p.translate(istek(["。。。"])).latency_ms >= 0


def test_k9_sure_tutulmaz_last_timing_yok(tmp_path: Path) -> None:
    assert not hasattr(LocalNmtProvider(model_dir=tmp_path), "last_timing")


# ===========================================================================
# K10 -- tembel kurulum, tek ornek, kapatma, loglama
# ===========================================================================


def test_k10_tembel_tek_ornek_close_idempotent(tmp_path: Path) -> None:
    f = SahteFabrika()
    p = saglayici(tmp_path, f)
    assert f.calls == 0  # __init__ fabrikaya dokunmaz
    for _ in range(3):
        p.translate(istek(["A。"]))
    assert f.calls == 1 and f.motor.call_count == 3
    p.close()
    p.close()
    with pytest.raises(ProviderUnavailable):
        p.translate(istek(["A。"]))
    with pytest.raises(ProviderUnavailable):
        p.translate(istek([]))  # kapali saglayici bos istegi de reddeder
    assert f.calls == 1 and f.motor.call_count == 3


def test_k10_init_model_kontrolu_yapmaz(tmp_path: Path) -> None:
    """Tembellik: model yoksa bile YAPIM basarili, hata ilk `translate`te."""
    p = LocalNmtProvider(model_dir=tmp_path / "yok", motor_fabrikasi=SahteFabrika())
    with pytest.raises(ModelMissingError):
        p.translate(istek(["A。"]))


def test_k10_close_kurulmamis_saglayicida_da_sessiz(tmp_path: Path) -> None:
    f = SahteFabrika()
    p = saglayici(tmp_path, f)
    p.close()
    with pytest.raises(ProviderUnavailable):
        p.translate(istek(["A。"]))
    assert f.calls == 0


def test_k10_close_motoru_ve_encode_decode_yu_gercekten_birakir_weakref(tmp_path: Path) -> None:
    """`close()` sonrasi saglayici motora/encode/decode'a referans TUTMAZ (gercek yolda CT2 + sp bellegi).

    Pozitif kontrol: `close()` ONCESI `gc.collect()` sonrasi uc weakref de CANLI.
    """
    zayif: list[weakref.ref[Any]] = []
    sayac = {"n": 0}

    def fabrika(model_dir: Path, params: dict[str, object]) -> tuple[CeviriMotoru, Callable[[str], list[str]], Callable[[list[str]], str]]:
        sayac["n"] += 1
        m = SahteMotor()  # taze nesneler; fabrika onlari TUTMAZ

        def enc(s: str) -> list[str]:
            return [s]

        def dec(t: list[str]) -> str:
            return "".join(t)

        zayif.extend([weakref.ref(m), weakref.ref(enc), weakref.ref(dec)])
        return m, enc, dec

    model_dosyalari(tmp_path)
    p = LocalNmtProvider(model_dir=tmp_path, motor_fabrikasi=fabrika)
    p.translate(istek(["A。"]))
    gc.collect()
    assert len(zayif) == 3 and all(z() is not None for z in zayif)  # pozitif kontrol
    p.close()
    gc.collect()
    assert all(z() is None for z in zayif)
    with pytest.raises(ProviderUnavailable):
        p.translate(istek(["A。"]))
    assert sayac["n"] == 1
    p.close()
    gc.collect()
    assert all(z() is None for z in zayif) and sayac["n"] == 1


def test_k10_kapali_saglayici_gecersiz_dilde_de_provider_unavailable(tmp_path: Path) -> None:
    """Sira: kapali mi -> dogrulama. Kapali saglayici her istegi ayni hatayla reddeder."""
    p = saglayici(tmp_path, SahteFabrika())
    p.close()
    with pytest.raises(ProviderUnavailable):
        p.translate(istek(["A。"], kaynak=None))


# -- K10 kanal olcusu: T-006 K7 deseniyle birebir (capfd + kok caplog + warnings) -----
#
# Degismez: `translate` suresince kaynak/ceviri metni HICBIR cikis kanalina
# yazilmaz -- stdout, stderr, herhangi bir `logging` logger'i (ad, seviye ve
# `propagate` ne olursa olsun), `warnings`. Olcu davranisi kancalar:
#
#   * `capfd`  -- fd duzeyinde stdout/stderr: `sys.stdout.write`, `os.write(1)`,
#                 `sys.__stderr__` hepsi gorunur. Beklenen: out == "" VE err == "" (sifir bayt).
#   * `caplog` -- KOK logger DEBUG; ek olarak `logging.Logger.handle` yamasi
#                 (`Logger.handle` kanali): `propagate=False` ve ADI BILINMEYEN bir
#                 logger'a yazilan kayit da yakalanir (T-006'da kutuphane logger'i adi
#                 biliniyordu; burada bilinmiyor -> ust kume).
#   * `warnings.catch_warnings(record=True)` + `simplefilter("always")`.
#
# Iki nokta (4.6/7): SOGUK (ilk translate = kurulum + ceviri) ve SICAK (kurulum
# bitmis, kok logger DEBUG'da). Pozitif kontroller: `TranslationProvider`i uygulayan,
# nobetciyi bir kanala yazan test ici sahte saglayicilar AYNI olcuden gecirilir ve
# DUSER (4.6/10). Negatif kontrol: sozlesmenin `FakeProvider`i gecer.

NOBETCILER: tuple[str, str] = ("NÖBETÇİ-7f3a", "長老-9c1e")
"""Iki nobetci: Turkce harfli Latin + ASCII-disi CJK (cp1254 tuzagi -- Windows)."""


def _nobetci_istegi() -> TranslationRequest:
    return istek([NOBETCILER[0] + "。", NOBETCILER[1] + "。"])


def _ozgun_akislari_bosalt() -> None:
    """`sys.__stdout__`/`sys.__stderr__` tamponunu fd'ye indirir (capfd ancak fd'de gorur)."""
    for akis in (sys.__stdout__, sys.__stderr__):
        if akis is not None:
            akis.flush()


@pytest.fixture
def logger_handle_kancasi(monkeypatch: pytest.MonkeyPatch) -> list[logging.LogRecord]:
    """`logging.Logger.handle`'i sarar: HER logger'in gercekten yayimladigi kayit (propagate/handler bagimsiz)."""
    kayitlar: list[logging.LogRecord] = []
    ozgun = logging.Logger.handle

    def _handle(self: logging.Logger, record: logging.LogRecord) -> None:
        kayitlar.append(record)
        ozgun(self, record)

    monkeypatch.setattr(logging.Logger, "handle", _handle)
    return kayitlar


def _k10_kanal_olcusu(
    p: TranslationProvider,
    capfd: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
    handle_kayitlari: list[logging.LogRecord],
) -> TranslationResult:
    """K10'un kanal-bagimsiz olcusu: TEK `translate`, uc kanal, sifir sizinti."""
    caplog.set_level(logging.DEBUG)  # KOK logger + caplog.handler: DEBUG
    caplog.clear()
    handle_kayitlari.clear()
    _ozgun_akislari_bosalt()
    capfd.readouterr()  # olcum oncesi artiklari at
    with warnings.catch_warnings(record=True) as uyari_kayitlari:
        warnings.simplefilter("always")
        sonuc = p.translate(_nobetci_istegi())
    _ozgun_akislari_bosalt()
    out, err = capfd.readouterr()
    assert out == "", f"stdout'a {len(out)} karakter yazildi (sifir olmali)"
    assert err == "", f"stderr'e {len(err)} karakter yazildi (sifir olmali)"
    mesajlar = [r.getMessage() for r in caplog.records] + [r.getMessage() for r in handle_kayitlari]
    uyarilar = [str(w.message) for w in uyari_kayitlari]
    for n in NOBETCILER:
        assert not [m for m in mesajlar if n in m], "nobetci bir log kaydina dustu"
        assert not [u for u in uyarilar if n in u], "nobetci bir warnings kaydina dustu"
    return sonuc


def test_k10_soguk_saglayici_hicbir_kanala_metin_yazmaz(
    tmp_path: Path,
    capfd: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
    logger_handle_kancasi: list[logging.LogRecord],
) -> None:
    """Nokta 1: ilk `translate` (kurulum + ceviri)."""
    f = SahteFabrika()
    r = _k10_kanal_olcusu(saglayici(tmp_path, f), capfd, caplog, logger_handle_kancasi)
    assert r.translations == (NOBETCILER[0] + "。", NOBETCILER[1] + "。")  # metin motordan AYNEN cikti
    assert f.calls == 1


def test_k10_sicak_saglayici_kok_logger_debugdayken_metin_yazmaz(
    tmp_path: Path,
    capfd: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
    logger_handle_kancasi: list[logging.LogRecord],
) -> None:
    """Nokta 2: kurulum bitti; kok logger DEBUG (uygulama debug modu) altinda ikinci `translate`."""
    f = SahteFabrika()
    p = saglayici(tmp_path, f)
    p.translate(_nobetci_istegi())
    r = _k10_kanal_olcusu(p, capfd, caplog, logger_handle_kancasi)
    assert r.translations == (NOBETCILER[0] + "。", NOBETCILER[1] + "。")
    assert f.calls == 1 and f.motor.call_count == 2


def test_k10_hata_yolunda_da_kanal_temiz(
    tmp_path: Path,
    capfd: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
    logger_handle_kancasi: list[logging.LogRecord],
) -> None:
    """Uc nokta: sayi uyusmazligi (ContractViolation) yolunda da hicbir kanala yazilmaz."""
    p = saglayici(tmp_path, SahteFabrika(SahteMotor(cikti=_n_hipotez(1))))
    caplog.set_level(logging.DEBUG)
    _ozgun_akislari_bosalt()
    capfd.readouterr()
    with warnings.catch_warnings(record=True) as uyarilar:
        warnings.simplefilter("always")
        with pytest.raises(ContractViolation):
            p.translate(_nobetci_istegi())
    _ozgun_akislari_bosalt()
    out, err = capfd.readouterr()
    assert out == "" and err == ""
    mesajlar = [r.getMessage() for r in caplog.records] + [r.getMessage() for r in logger_handle_kancasi]
    assert not [m for m in mesajlar if any(n in m for n in NOBETCILER)]
    assert not [w for w in uyarilar if any(n in str(w.message) for n in NOBETCILER)]


# -- pozitif kontroller (4.6/10): olcu ATESLIYOR mu? ----------------------------


def _sonuc(metin: str) -> TranslationResult:
    return TranslationResult(translations=(metin, metin), provider_id="sahte", latency_ms=0.0)


class _StdoutaYazan(TranslationProvider):
    @property
    def provider_id(self) -> str:
        return "sahte"

    def translate(self, request: TranslationRequest) -> TranslationResult:
        sys.stdout.write(NOBETCILER[0])
        return _sonuc(NOBETCILER[0])


class _StderreYazan(_StdoutaYazan):
    def translate(self, request: TranslationRequest) -> TranslationResult:
        sys.stderr.write(NOBETCILER[1])
        return _sonuc(NOBETCILER[1])


class _FdYeYazan(_StdoutaYazan):
    def translate(self, request: TranslationRequest) -> TranslationResult:
        os.write(1, NOBETCILER[1].encode("utf-8"))  # sys.stdout'u atlar; capsys GOREMEZ, capfd gorur
        return _sonuc(NOBETCILER[1])


class _OzgunStderreYazan(_StdoutaYazan):
    def translate(self, request: TranslationRequest) -> TranslationResult:
        assert sys.__stderr__ is not None
        sys.__stderr__.write(NOBETCILER[0])  # newline YOK: satir tamponunda kalir; bosaltma olmasa gorunmezdi
        return _sonuc(NOBETCILER[0])


class _KokLoggeraYazan(_StdoutaYazan):
    def translate(self, request: TranslationRequest) -> TranslationResult:
        logging.getLogger("suflor.translate").debug("segment %s", NOBETCILER[0])
        return _sonuc(NOBETCILER[0])


class _PropagateKapaliLoggeraYazan(_StdoutaYazan):
    def translate(self, request: TranslationRequest) -> TranslationResult:
        lg = logging.getLogger("bilinmeyen.kutuphane.logger")
        lg.propagate = False  # koke ULASMAZ; yalniz Logger.handle kancasi gorur
        lg.setLevel(logging.INFO)
        lg.info("segment %s", NOBETCILER[1])
        return _sonuc(NOBETCILER[1])


class _UyariVeren(_StdoutaYazan):
    def translate(self, request: TranslationRequest) -> TranslationResult:
        warnings.warn(NOBETCILER[0], stacklevel=2)
        return _sonuc(NOBETCILER[0])


@pytest.fixture
def yabanci_logger_geri_al() -> Iterator[None]:
    lg = logging.getLogger("bilinmeyen.kutuphane.logger")
    eski = (lg.level, lg.propagate, list(lg.handlers))
    yield
    lg.setLevel(eski[0])
    lg.propagate = eski[1]
    lg.handlers[:] = eski[2]


@pytest.mark.parametrize(
    "sahte",
    [_StdoutaYazan, _StderreYazan, _FdYeYazan, _OzgunStderreYazan, _KokLoggeraYazan, _PropagateKapaliLoggeraYazan, _UyariVeren],
    ids=["stdout", "stderr", "os.write(1)", "sys.__stderr__-tamponlu", "kok-logger-debug", "adi-bilinmeyen-logger-propagate-kapali", "warnings"],
)
def test_k10_pozitif_kontrol_kanal_olcusu_atesliyor(
    sahte: type[TranslationProvider],
    yabanci_logger_geri_al: None,
    capfd: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
    logger_handle_kancasi: list[logging.LogRecord],
) -> None:
    """Ayni olcu, nobetciyi o kanala yazan sahte saglayiciyla DUSMELI (4.6/10)."""
    with pytest.raises(AssertionError):
        _k10_kanal_olcusu(sahte(), capfd, caplog, logger_handle_kancasi)
    capfd.readouterr()
    caplog.clear()


def test_k10_negatif_kontrol_sessiz_fakeprovider_olcuden_gecer(
    capfd: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
    logger_handle_kancasi: list[logging.LogRecord],
) -> None:
    """Yanlis pozitif yok: hicbir kanala yazmayan sozlesme sahtesi olcuden gecer."""
    r = _k10_kanal_olcusu(FakeProvider(), capfd, caplog, logger_handle_kancasi)
    assert len(r.translations) == 2


# -- AST (ikincil, erken uyari): yazma cagrisi + log yayimi 0 -------------------

_YAZMA_CAGRILARI: tuple[str, ...] = ("print", "sys.stdout.write", "sys.stderr.write", "os.write")
_AKIS_ADLARI: tuple[str, ...] = ("sys.stdout", "sys.stderr", "sys.__stdout__", "sys.__stderr__")
_LOG_YAYIM_METOTLARI: frozenset[str] = frozenset({"debug", "info", "warning", "warn", "error", "critical", "exception", "log"})


def _yazma_sayaci(agac: ast.AST) -> dict[str, int]:
    sayac: dict[str, int] = {ad: 0 for ad in (*_YAZMA_CAGRILARI, *_AKIS_ADLARI, "log-yayimi", "logging-import")}
    for d in ast.walk(agac):
        if isinstance(d, ast.Call):
            ad = ast.unparse(d.func)
            if ad in _YAZMA_CAGRILARI:
                sayac[ad] += 1
            if isinstance(d.func, ast.Attribute) and d.func.attr in _LOG_YAYIM_METOTLARI:
                sayac["log-yayimi"] += 1
        if isinstance(d, ast.Attribute) and ast.unparse(d) in _AKIS_ADLARI:
            sayac[ast.unparse(d)] += 1
        if isinstance(d, ast.Import) and any(a.name.split(".")[0] == "logging" for a in d.names):
            sayac["logging-import"] += 1
        if isinstance(d, ast.ImportFrom) and (d.module or "").split(".")[0] == "logging":
            sayac["logging-import"] += 1
    return sayac


def test_k10_ast_yazma_cagrisi_log_yayimi_ve_logging_importu_sifir() -> None:
    sayac = _yazma_sayaci(_modul_agaci())
    assert sayac == {ad: 0 for ad in sayac}, sayac


def test_k10_ast_pozitif_kontrol_sayac_hepsini_gorur() -> None:
    parca = (
        "import sys, os, logging\n"
        "def f(m):\n"
        "    print(m)\n"
        "    sys.stdout.write(m)\n"
        "    sys.stderr.write(m)\n"
        "    os.write(1, m.encode())\n"
        "    sys.__stdout__.write(m)\n"
        "    sys.__stderr__.flush()\n"
        "    logging.getLogger('x').debug('%s', m)\n"
        "    logging.getLogger('y').log(10, m)\n"
    )
    assert _yazma_sayaci(ast.parse(parca)) == {
        "print": 1, "sys.stdout.write": 1, "sys.stderr.write": 1, "os.write": 1,
        "sys.stdout": 1, "sys.stderr": 1, "sys.__stdout__": 1, "sys.__stderr__": 1,
        "log-yayimi": 2, "logging-import": 1,
    }


def test_k10_olculmuyor_damgalari_docstringlerde() -> None:
    assert "[ÖLÇÜLMÜYOR]" in (local_nmt.__doc__ or "")
    assert "[ÖLÇÜLMÜYOR]" in (LocalNmtProvider.translate.__doc__ or "")
    assert "[ÖLÇÜLMÜYOR]" in (local_nmt._varsayilan_fabrika.__doc__ or "")


# ===========================================================================
# Yozlasmis girdiler (paket "Yozlasmis girdiler -- sahte motorla")
# ===========================================================================


def test_yozlasmis_bos_segment_ciktisi_bos_motora_gitmez(tmp_path: Path) -> None:
    f = SahteFabrika()
    r = saglayici(tmp_path, f).translate(istek(["", "A。", ""]))
    assert r.translations == ("", "A。", "")
    assert f.motor.call_count == 1 and f.motor.gonderilen_parcalar() == ["A。"]


def test_yozlasmis_tum_segmentler_gecis_ise_motor_kurulmaz(tmp_path: Path) -> None:
    f = SahteFabrika()
    r = saglayici(tmp_path, f).translate(istek(["", "   ", "。。。", "!?"]))
    assert r.translations == ("", "   ", "。。。", "!?")
    assert f.calls == 0 and f.motor.call_count == 0


def test_yozlasmis_cok_uzun_noktalamasiz_tek_parca_oldugu_gibi_gider(tmp_path: Path) -> None:
    f = SahteFabrika()
    metin = "あ" * 3000  # terminator yok -> tek parca; CT2 1024 token'da sessizce kirpar (belgeli)
    saglayici(tmp_path, f).translate(istek([metin]))
    assert f.motor.gonderilen_parcalar() == [metin]


def test_yozlasmis_encode_bos_liste_dondururse_yine_gider(tmp_path: Path) -> None:
    """Sahte encode `[]` dondurse de kaynak belirteci + `</s>` gider; cikti decode'a bagli."""
    f = SahteFabrika(encode=lambda s: [], motor=SahteMotor(cikti=lambda tokens: [SahteHipotez([[HEDEF]]) for _ in tokens]))
    r = saglayici(tmp_path, f).translate(istek(["A。"]))
    assert f.motor.son["tokens"] == [[NLLB["JAPAN"], SON]]
    assert r.translations == ("",)
