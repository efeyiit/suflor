"""TESTER-B (T-007, mercek B: test kalitesi, K1 bariyeri, omur, loglama, hata taksonomisi) -- tur 1.

Kor tester: `delivery.md` bu testler yazilirken OKUNMADI. Girdi: `packet.md`
(surum 2), `olgular.txt`, `krt-1.md`, `src/translate/local_nmt.py`,
`tests/unit/translate/{test_local_nmt,conftest,test_conftest_bariyer}.py`.

Bariyer bu dizinin KENDI `conftest.py`sinden kurulur (`tb_bariyer.py`);
testler `match="K1 bariyeri"` kullanir -- sefin bariyeriyle birlikte kosunca
da tutar. Teslimin sahte motoru/fabrikasi ve K10 olcusu teslim dosyasindan
YUKLENIR (kopyalanmaz), boylece burada olculen sey teslimin kendi olcusudur.

Kosum (tek basina / sefin bariyeriyle birlikte):
    python -m pytest .agents/tasks/T-007/tester_B -q -p no:cacheprovider
    python -m pytest tests/unit/translate .agents/tasks/T-007/tester_B -q -p no:cacheprovider

Ceviri/kaynak metni hicbir yere basilmaz (PROTOKOL 7).
"""
from __future__ import annotations

import ast
import importlib
import importlib.machinery
import importlib.util
import logging
import re
import sys
import types
import warnings
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest

import tb_bariyer
from src.contracts.errors import ContractViolation, ModelMissingError, ProviderUnavailable
from src.contracts.models import Rect, Segment, TranslationRequest, TranslationResult
from src.translate import local_nmt
from src.translate.local_nmt import LocalNmtProvider

KOK = tb_bariyer._KOK
KAYNAK = KOK / "src" / "translate" / "local_nmt.py"
TESLIM_TEST = KOK / "tests" / "unit" / "translate" / "test_local_nmt.py"
SEF_CONFTEST = KOK / "tests" / "unit" / "translate" / "conftest.py"
MODEL_DOSYALARI: tuple[str, ...] = ("model.bin", "sentencepiece.bpe.model", "shared_vocabulary.txt", "config.json")
HEDEF = "tur_Latn"
CT2_TRANSLATE_BATCH_PARAMS: frozenset[str] = frozenset({  # BAGIMSIZ kanal: gercek imza, tester_B_evidence/B4-*.txt
    "source", "target_prefix", "max_batch_size", "batch_type", "asynchronous", "beam_size", "patience",
    "num_hypotheses", "length_penalty", "coverage_penalty", "repetition_penalty", "no_repeat_ngram_size",
    "disable_unk", "suppress_sequences", "end_token", "return_end_token", "prefix_bias_beta",
    "max_input_length", "max_decoding_length", "min_decoding_length", "use_vmap", "return_scores",
    "return_logits_vocab", "return_attention", "return_alternatives", "min_alternative_expansion_prob",
    "sampling_topk", "sampling_topp", "sampling_temperature", "replace_unknowns", "callback",
})


def _teslim_modulu() -> types.ModuleType:
    """Teslimin test modulunu DOSYADAN yukler (kopya degil): sahte motor + K10 olcusu oradan."""
    spec = importlib.util.spec_from_file_location("tb_teslim_test_local_nmt", TESLIM_TEST)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


T = _teslim_modulu()
SahteMotor = T.SahteMotor
SahteFabrika = T.SahteFabrika
SahteHipotez = T.SahteHipotez
istek = T.istek
NOBETCILER: tuple[str, str] = T.NOBETCILER


def model_dosyalari(dizin: Path, haric: str | None = None) -> None:
    for ad in MODEL_DOSYALARI:
        if ad != haric:
            (dizin / ad).write_bytes(b"")


def saglayici(tmp_path: Path, fabrika: Any, **ek: Any) -> LocalNmtProvider:
    model_dosyalari(tmp_path)
    return LocalNmtProvider(model_dir=tmp_path, motor_fabrikasi=fabrika, **ek)


@pytest.fixture
def handle_kancasi(monkeypatch: pytest.MonkeyPatch) -> list[logging.LogRecord]:
    """Teslimin `logger_handle_kancasi` fixture'inin AYNISI (Logger.handle sarmalanir)."""
    kayitlar: list[logging.LogRecord] = []
    ozgun = logging.Logger.handle

    def _handle(self: logging.Logger, record: logging.LogRecord) -> None:
        kayitlar.append(record)
        ozgun(self, record)

    monkeypatch.setattr(logging.Logger, "handle", _handle)
    return kayitlar


@pytest.fixture
def yabanci_logger_geri_al() -> Iterator[None]:
    adlar = ("tb.propagate.kapali", "tb.dogrudan.handler", "bilinmeyen.kutuphane.logger")
    eski = {ad: (logging.getLogger(ad).level, logging.getLogger(ad).propagate, list(logging.getLogger(ad).handlers)) for ad in adlar}
    yield
    for ad, (lv, pr, hs) in eski.items():
        lg = logging.getLogger(ad)
        lg.setLevel(lv)
        lg.propagate = pr
        lg.handlers[:] = hs


# ===========================================================================
# B3 -- K1 bariyeri: kendi bariyerim, kacis yollari, on-yuklu sys.modules
# ===========================================================================


@pytest.mark.parametrize("ad", ["ctranslate2", "sentencepiece", "ctranslate2.converters", "sentencepiece._sentencepiece"])
def test_b3_kendi_bariyerim_import_module_yolunu_kesiyor(ad: str) -> None:
    sys.modules.pop(ad, None)
    with pytest.raises(RuntimeError, match="K1 bariyeri"):
        importlib.import_module(ad)
    assert not any(k.split(".", 1)[0] in tb_bariyer.YASAK_KOKLER for k in sys.modules)


@pytest.mark.parametrize("ad", ["ctranslate2", "sentencepiece"])
def test_b3_dunder_import_yolu_da_kesiliyor(ad: str) -> None:
    sys.modules.pop(ad, None)
    with pytest.raises(RuntimeError, match="K1 bariyeri"):
        __import__(ad)


def test_b3_conftest_yuklenirken_yasak_kok_sys_modulesta_yoktu() -> None:
    """B3 'sys.modules onceden dolu' kacisi: bariyer kurulmadan once kutuphane yuklu olsaydi bariyer KOR olurdu -- olculdu."""
    assert tb_bariyer.ONCEDEN_YUKLU == ()


def test_b3_sys_modules_onceden_dolu_kacisi_gercekten_kor_birakir() -> None:
    """Karakterizasyon: `sys.modules`a onceden konmus bir nesne bariyeri ATLAR (import sistemi once oraya bakar)."""
    sahte = types.ModuleType("ctranslate2")
    sys.modules["ctranslate2"] = sahte
    try:
        assert importlib.import_module("ctranslate2") is sahte  # bariyer sorgulanmadi bile
    finally:
        sys.modules.pop("ctranslate2", None)
    # temizlik sonrasi bariyer yine ateslemeli
    with pytest.raises(RuntimeError, match="K1 bariyeri"):
        importlib.import_module("ctranslate2")


def test_b3_spec_from_file_location_kacisi_olculur() -> None:
    """`spec_from_file_location` meta_path'i ATLAR; paket __init__'i alt modul import edince bariyere carpar mi -- OLCULUR.

    Bulucu `PathFinder.find_spec` DOGRUDAN cagrilir (meta_path degil) ki dosya yolu bariyere carpmadan bulunsun.
    """
    spec = importlib.machinery.PathFinder.find_spec("sentencepiece")
    if spec is None or spec.origin is None:
        pytest.skip("sentencepiece kurulu degil")
    onceki = set(sys.modules)
    yeni_spec = importlib.util.spec_from_file_location(
        "sentencepiece", spec.origin, submodule_search_locations=spec.submodule_search_locations  # pakete tam sans
    )
    assert yeni_spec is not None and yeni_spec.loader is not None
    mod = importlib.util.module_from_spec(yeni_spec)
    sys.modules["sentencepiece"] = mod
    try:
        with pytest.raises(RuntimeError, match="K1 bariyeri"):
            yeni_spec.loader.exec_module(mod)  # __init__ icindeki `from . import _sentencepiece` meta_path'ten gecer
    finally:
        for k in set(sys.modules) - onceki:
            sys.modules.pop(k, None)
        sys.modules.pop("sentencepiece", None)
    assert not any(k.split(".", 1)[0] in tb_bariyer.YASAK_KOKLER for k in sys.modules)


def test_b3_uzanti_dosyasi_dogrudan_yuklenirse_bariyer_kor_karakterizasyon() -> None:
    """Sinir: `spec_from_file_location` + ExtensionFileLoader ile `.pyd` DOGRUDAN yuklenir; meta_path hic sorulmaz.
    Bariyerin gormedigi tek yol budur (ve `sys.modules` on-yukleme). Motor/testler bu API'yi kullanmiyor (AST testi)."""
    spec = importlib.machinery.PathFinder.find_spec("sentencepiece")
    if spec is None or not spec.submodule_search_locations:
        pytest.skip("sentencepiece kurulu degil")
    pyd = next(iter(Path(spec.submodule_search_locations[0]).glob("_sentencepiece*.pyd")), None)
    if pyd is None:
        pytest.skip("uzanti dosyasi bulunamadi")
    sorgu_oncesi = len(tb_bariyer.BARIYER.sorgular)
    uz_spec = importlib.util.spec_from_file_location("sentencepiece._sentencepiece", pyd)  # yasak kokle adlandirilmis, yine de yuklenir
    assert uz_spec is not None and uz_spec.loader is not None
    mod = importlib.util.module_from_spec(uz_spec)
    try:
        uz_spec.loader.exec_module(mod)  # bariyer SORGULANMAZ
        assert hasattr(mod, "SentencePieceProcessor")
    finally:
        sys.modules.pop("sentencepiece._sentencepiece", None)
    assert len(tb_bariyer.BARIYER.sorgular) == sorgu_oncesi  # kendi bariyerim hic sorgulanmadi


_KACIS_ADLARI = ("spec_from_file_location", "module_from_spec", "__import__", "import_module", "subprocess", "runpy", "exec", "eval")


def _kacis_kullanimi(dosya: Path) -> dict[str, int]:
    agac = ast.parse(dosya.read_text(encoding="utf-8"))
    sayac = {ad: 0 for ad in _KACIS_ADLARI}
    sayac["sys.modules-yazma"] = 0
    for d in ast.walk(agac):
        if isinstance(d, ast.Call):
            ad = ast.unparse(d.func)
            for k in _KACIS_ADLARI:
                if ad == k or ad.endswith("." + k):
                    sayac[k] += 1
        if isinstance(d, ast.Assign):
            for hedef in d.targets:
                if isinstance(hedef, ast.Subscript) and ast.unparse(hedef.value) == "sys.modules":
                    sayac["sys.modules-yazma"] += 1
        if isinstance(d, (ast.Import, ast.ImportFrom)):
            kok = (d.module or "").split(".")[0] if isinstance(d, ast.ImportFrom) else ""
            adlar = [a.name.split(".")[0] for a in d.names] if isinstance(d, ast.Import) else [kok]
            for a in adlar:
                if a in ("subprocess", "runpy"):
                    sayac[a] += 1
    return sayac


def test_b3_motor_bariyer_kacis_apisi_kullanmiyor() -> None:
    sayac = _kacis_kullanimi(KAYNAK)
    assert sayac == {k: 0 for k in sayac}, sayac


def test_b3_teslim_testleri_bariyer_kacis_apisi_kullanmiyor() -> None:
    sayac = _kacis_kullanimi(TESLIM_TEST)
    assert sayac == {k: 0 for k in sayac}, sayac


def test_b3_sefin_bariyeri_modul_duzeyinde_ve_mesaji_uyumlu() -> None:
    """Sefin conftest'i fixture'da degil modul duzeyinde kurar; mesaji `K1 bariyeri` tasir (match uyumu)."""
    kaynak = SEF_CONFTEST.read_text(encoding="utf-8")
    agac = ast.parse(kaynak)
    assert not any(isinstance(d, ast.FunctionDef) and any(ast.unparse(x).startswith("pytest.fixture") for x in d.decorator_list) for d in ast.walk(agac))
    assert "K1 bariyeri" in kaynak and "sys.meta_path.insert(0" in kaynak


def test_b3_bariyer_meta_path_basinda() -> None:
    """Hangi bariyer (sef/tester-B) olursa olsun ilk bulucu bir K1 bariyeridir -- PathFinder'dan ONCE."""
    ilk = sys.meta_path[0]
    assert type(ilk).__name__ in ("TesterBBariyer", "_T007Bariyer"), type(ilk)


# ===========================================================================
# B2 -- sahte motorun gercekligi; teslim testlerinin totoloji taramasi (betik ayri)
# ===========================================================================


def test_b2_sahte_motor_gercek_ct2_donus_bicimini_taklit_ediyor() -> None:
    """olgular C4 / KRT D2: her girdi icin `.hypotheses`, `hypotheses[0][0] == "tur_Latn"`, `</s>` yok, sayi == girdi."""
    m = SahteMotor()
    girdi = [["jpn_Jpan", "A。", "</s>"], ["jpn_Jpan", "B。", "</s>"], ["eng_Latn", "C.", "</s>"]]
    cikti = m.translate_batch(girdi, target_prefix=[[HEDEF]] * 3, beam_size=4, max_decoding_length=256)
    assert len(cikti) == 3
    for nesne in cikti:
        h = nesne.hypotheses
        assert isinstance(h, list) and len(h) >= 1 and isinstance(h[0], list)
        assert h[0][0] == HEDEF and "</s>" not in h[0]
        assert all(isinstance(t, str) for t in h[0])
    assert m.calls[0]["target_prefix"] == [[HEDEF]] * 3


def test_b2_sahte_motor_konumsal_source_ile_cagrilabiliyor_ve_anahtarla_degil() -> None:
    """Gercek imza `source` KONUMSAL (KRT D2); saglayici konumsal gecer; sahte de konumsal kabul eder."""
    m = SahteMotor()
    m.translate_batch([["jpn_Jpan", "A。", "</s>"]], target_prefix=[[HEDEF]], beam_size=1, max_decoding_length=8)
    assert m.call_count == 1
    agac = ast.parse(KAYNAK.read_text(encoding="utf-8"))
    cagri = next(d for d in ast.walk(agac) if isinstance(d, ast.Call) and ast.unparse(d.func).endswith("translate_batch"))
    assert len(cagri.args) == 1 and ast.unparse(cagri.args[0]) == "tokenler"  # konumsal, `tokens=`/`source=` DEGIL
    anahtarlar = {kw.arg for kw in cagri.keywords if kw.arg}
    assert anahtarlar <= CT2_TRANSLATE_BATCH_PARAMS, anahtarlar - CT2_TRANSLATE_BATCH_PARAMS
    assert {"target_prefix", "beam_size", "max_decoding_length"} <= anahtarlar
    assert any(kw.arg is None for kw in cagri.keywords)  # **ek (repetition_penalty yalniz != 1.0)


def test_b2_saglayici_token_duzeyinde_islem_yapmiyor_sahte_encode_tek_token_yeterli() -> None:
    """Sahte `encode` parcayi TEK token yapar (`▁` onekli gercek sentencepiece degil). Bu ancak saglayici
    encode ciktisini AYNEN gecirirse (indeksleme/dilimleme yok) yeterlidir -- AST ile dogrulanir.
    Gercek `▁`/bosluk davranisi B4 alt surecinde olculur (tester_B_evidence/B4-*.txt)."""
    agac = ast.parse(KAYNAK.read_text(encoding="utf-8"))
    cevir = next(d for d in ast.walk(agac) if isinstance(d, ast.FunctionDef) and d.name == "_cevir")
    encode_cagrilari = [d for d in ast.walk(cevir) if isinstance(d, ast.Call) and ast.unparse(d.func) == "encode"]
    assert len(encode_cagrilari) == 1
    # tek kullanim: `[kaynak.value, *encode(p), _SON_BELIRTECI]` -- yildizli yayma, baska islem yok
    starred = [d for d in ast.walk(cevir) if isinstance(d, ast.Starred) and ast.unparse(d.value) == "encode(p)"]
    assert len(starred) == 1
    decode_cagrilari = [d for d in ast.walk(cevir) if isinstance(d, ast.Call) and ast.unparse(d.func) == "decode"]
    assert len(decode_cagrilari) == 1 and ast.unparse(decode_cagrilari[0].args[0]) == "h"


def test_b2_sahte_encode_decode_gercek_gibi_roundtrip() -> None:
    """Sahtenin kendi tutarliligi: decode(encode(x)) == x (gercek sentencepiece de bunu saglar, B4)."""
    f = SahteFabrika()
    for x in ("A。", "村の長老があなたを待っています。", "Take the eastern road.", "3.5 km"):
        assert f.decode(f.encode(x)) == x


def test_b2_gercek_adli_testler_listesi() -> None:
    """Adinda 'gercek/gerçek' gecen teslim testleri: hangisi gercege dokunuyor? (weakref+gc: olcuyor; 'gercek fabrika': AST -- K1 geregi kosamaz)."""
    agac = ast.parse(TESLIM_TEST.read_text(encoding="utf-8"))
    adlar = sorted(d.name for d in ast.walk(agac) if isinstance(d, ast.FunctionDef) and d.name.startswith("test_") and re.search(r"gercek|gerçek", d.name))
    assert adlar == [
        "test_k10_close_motoru_ve_encode_decode_yu_gercekten_birakir_weakref",
        "test_k7_gercek_fabrika_model_proto_var_model_file_yok",
    ], adlar
    weak = next(d for d in ast.walk(agac) if isinstance(d, ast.FunctionDef) and d.name == adlar[0])
    src = ast.unparse(weak)
    assert "weakref.ref" in src and "gc.collect()" in src and "is not None for z in zayif" in src  # pozitif kontrol var
    fab = next(d for d in ast.walk(agac) if isinstance(d, ast.FunctionDef) and d.name == adlar[1])
    assert "_varsayilan_fabrika" in ast.unparse(fab) and "ast." in ast.unparse(fab)  # AST: mekanizma olcusu, kosmaz


# ===========================================================================
# B4 -- K10 kanal olcusu: Logger.handle kancasi ne ekliyor, kor noktalari, gercek sinifta atesliyor mu
# ===========================================================================


def test_b4_logger_handle_kancasi_propagate_false_loggeri_gorur_caplog_gormez(
    handle_kancasi: list[logging.LogRecord], caplog: pytest.LogCaptureFixture, yabanci_logger_geri_al: None
) -> None:
    caplog.set_level(logging.DEBUG)
    lg = logging.getLogger("tb.propagate.kapali")
    lg.propagate = False
    lg.setLevel(logging.INFO)
    lg.info("x %s", NOBETCILER[1])
    assert not [r for r in caplog.records if NOBETCILER[1] in r.getMessage()]  # kok caplog KOR
    assert [r for r in handle_kancasi if NOBETCILER[1] in r.getMessage()]  # kanca GORUR -> T-006'nin ust kumesi


def test_b4_kanca_kor_noktasi_handler_a_dogrudan_kayit(
    handle_kancasi: list[logging.LogRecord], caplog: pytest.LogCaptureFixture, yabanci_logger_geri_al: None
) -> None:
    """Karakterizasyon (T-006 R04/R05 sinifi): `Handler.handle(record)` DOGRUDAN -> Logger.handle atlanir; kanca ve caplog.records KOR."""
    caplog.set_level(logging.DEBUG)
    lg = logging.getLogger("tb.dogrudan.handler")
    lg.addHandler(caplog.handler)
    kayit = logging.LogRecord("tb.dogrudan.handler", logging.INFO, __file__, 1, "y %s", (NOBETCILER[0],), None)
    caplog.handler.handle(kayit)  # Logger.handle atlanir
    assert not [r for r in handle_kancasi if NOBETCILER[0] in r.getMessage()]
    assert [r for r in caplog.records if NOBETCILER[0] in r.getMessage()]  # caplog.handler'a dogrudan gittigi icin caplog gorur
    # ama bir YABANCI handler'a dogrudan yazim hicbir kanalda gorunmez:
    yabanci: list[logging.LogRecord] = []
    h = logging.Handler()
    h.emit = yabanci.append  # type: ignore[method-assign]
    h.handle(kayit)
    assert yabanci and not [r for r in handle_kancasi if r is kayit]


def test_b4_kanca_seviye_altindaki_kaydi_gormez_ama_o_kayit_hicbir_yere_gitmez(
    handle_kancasi: list[logging.LogRecord], caplog: pytest.LogCaptureFixture, yabanci_logger_geri_al: None
) -> None:
    caplog.set_level(logging.DEBUG)
    lg = logging.getLogger("tb.propagate.kapali")
    lg.setLevel(logging.WARNING)
    lg.info("z %s", NOBETCILER[0])  # isEnabledFor(INFO) False -> handle cagrilmaz -> sizinti da yok
    assert not handle_kancasi and not caplog.records


def _kanala_yazan_fabrika(yaz: Callable[[str], None]) -> Any:
    """`decode` sonucu bir kanala YAZAN sahte fabrika: gercek `LocalNmtProvider` sinifi uzerinden olcu ateslemeli."""
    def decode(t: list[str]) -> str:
        s = "".join(t)
        yaz(s)
        return s
    return SahteFabrika(decode=decode)


@pytest.mark.parametrize(
    ("yaz", "beklenen"),
    [
        (lambda s: sys.stdout.write(s), "stdout'a"),
        (lambda s: sys.stderr.write(s), "stderr'e"),
        (lambda s: logging.getLogger("suflor.translate").debug("%s", s), "log kaydina"),
        (lambda s: (lambda lg: (setattr(lg, "propagate", False), lg.setLevel(logging.INFO), lg.info("%s", s)))(logging.getLogger("bilinmeyen.kutuphane.logger")), "log kaydina"),
        (lambda s: warnings.warn(s, stacklevel=2), "warnings kaydina"),
    ],
    ids=["stdout", "stderr", "kok-logger-debug", "propagate-kapali-logger", "warnings"],
)
def test_b4_teslim_olcusu_gercek_saglayici_sinifinda_atesliyor(
    tmp_path: Path, yaz: Callable[[str], None], beklenen: str,
    capfd: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture,
    handle_kancasi: list[logging.LogRecord], yabanci_logger_geri_al: None,
) -> None:
    """Teslimin `_k10_kanal_olcusu`su, sahte SAGLAYICI degil GERCEK `LocalNmtProvider` + kanala yazan enjekte `decode` ile DUSER (dogru sebeple)."""
    p = saglayici(tmp_path, _kanala_yazan_fabrika(yaz))
    with pytest.raises(AssertionError, match=beklenen):
        T._k10_kanal_olcusu(p, capfd, caplog, handle_kancasi)
    capfd.readouterr()
    caplog.clear()


@pytest.mark.parametrize(
    ("sahte_adi", "beklenen"),
    [
        ("_StdoutaYazan", "stdout'a"), ("_StderreYazan", "stderr'e"), ("_FdYeYazan", "stdout'a"),
        ("_OzgunStderreYazan", "stderr'e"), ("_KokLoggeraYazan", "log kaydina"),
        ("_PropagateKapaliLoggeraYazan", "log kaydina"), ("_UyariVeren", "warnings kaydina"),
    ],
)
def test_b4_teslimin_yedi_pozitif_kontrolu_dogru_sebeple_dusuyor(
    sahte_adi: str, beklenen: str, capfd: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture,
    handle_kancasi: list[logging.LogRecord], yabanci_logger_geri_al: None,
) -> None:
    """Teslim `pytest.raises(AssertionError)` yazar, `match=` yok (T-006 tur 2 keskinlestirme #4). Burada sebep dogrulanir."""
    sahte = getattr(T, sahte_adi)
    with pytest.raises(AssertionError, match=beklenen):
        T._k10_kanal_olcusu(sahte(), capfd, caplog, handle_kancasi)
    capfd.readouterr()
    caplog.clear()


def test_b4_teslim_olcusu_sessiz_gercek_saglayicida_gecer(
    tmp_path: Path, capfd: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture, handle_kancasi: list[logging.LogRecord]
) -> None:
    r = T._k10_kanal_olcusu(saglayici(tmp_path, SahteFabrika()), capfd, caplog, handle_kancasi)
    assert r.translations == (NOBETCILER[0] + "。", NOBETCILER[1] + "。")


def test_b4_hata_mesaji_motor_ciktisini_da_tasimaz_nobetci_ciktida(tmp_path: Path) -> None:
    """Keskinlik: teslimin nobetci testi sayi/bozuk-cikti yollarinda nobetcisiz sahte ('x') kullanir.
    Burada motor CIKTISI nobetci tasir: sayi uyusmazligi ve bozuk-cikti mesajlari onu tasimamali."""
    nob = NOBETCILER[0]
    f = SahteFabrika(SahteMotor(cikti=lambda tokens: [SahteHipotez([[HEDEF, nob]]) for _ in range(len(tokens) + 1)]))
    with pytest.raises(ContractViolation) as e1:
        saglayici(tmp_path, f).translate(istek(["A。"]))
    assert nob not in str(e1.value) and nob not in repr(e1.value)
    f2 = SahteFabrika(SahteMotor(cikti=lambda tokens: [SahteHipotez([[HEDEF, nob, 5]]) for _ in tokens]))
    with pytest.raises(ProviderUnavailable) as e2:
        saglayici(tmp_path, f2).translate(istek(["A。"]))
    assert nob not in str(e2.value) and nob not in repr(e2.value)
    f3 = SahteFabrika(SahteMotor(cikti=lambda tokens: [types.SimpleNamespace(hypotheses=None, metin=nob) for _ in tokens]))
    with pytest.raises(ProviderUnavailable) as e3:
        saglayici(tmp_path, f3).translate(istek(["A。"]))
    assert nob not in str(e3.value) and nob not in repr(e3.value)


# ===========================================================================
# B5 -- omur ve hata taksonomisi
# ===========================================================================


def test_b5_close_iki_kez_sonra_translate_provider_unavailable_fabrika_yeniden_cagrilmaz(tmp_path: Path) -> None:
    f = SahteFabrika()
    p = saglayici(tmp_path, f)
    p.translate(istek(["A。"]))
    assert f.calls == 1
    p.close()
    p.close()
    for req in (istek(["A。"]), istek([]), istek(["。。。"]), istek(["A。"], kaynak="xx")):
        with pytest.raises(ProviderUnavailable):
            p.translate(req)
    assert f.calls == 1 and f.motor.call_count == 1
    assert p.provider_id == "local-nmt-nllb200-600m-int8" and p.motor_parametreleri()["inter_threads"] == 1  # gozlem hala calisir


def test_b5_close_hic_kurulmamis_saglayicida_fabrika_hic_cagrilmaz(tmp_path: Path) -> None:
    f = SahteFabrika()
    p = saglayici(tmp_path, f)
    p.close()
    with pytest.raises(ProviderUnavailable):
        p.translate(istek(["A。"]))
    assert f.calls == 0


def test_b5_fabrika_ilk_cagrida_firlatirsa_ikinci_translate_yeniden_dener_belgeli(tmp_path: Path) -> None:
    """Paket sessiz; teslim docstring'i 'sonraki translate kurulumu YENIDEN dener' der -- olculdu ve docstring'de ariyor."""
    f = SahteFabrika(hata=RuntimeError("ilk"))
    p = saglayici(tmp_path, f)
    with pytest.raises(ProviderUnavailable) as e1:
        p.translate(istek(["A。"]))
    assert isinstance(e1.value.__cause__, RuntimeError)
    with pytest.raises(ProviderUnavailable):
        p.translate(istek(["A。"]))
    assert f.calls == 2  # ornek tutulmadi, yeniden denendi
    f.hata = None
    assert p.translate(istek(["A。"])).translations == ("A。",) and f.calls == 3
    doc = local_nmt.__doc__ or ""
    assert re.search(r"YENIDEN dener|yeniden dener", doc), "yeniden deneme politikasi docstring'de belgeli olmali"


def test_b5_fabrika_modelmissing_firlatirsa_oldugu_gibi_ve_yeniden_denenir(tmp_path: Path) -> None:
    ozel = ModelMissingError("indirilmedi")
    f = SahteFabrika(hata=ozel)
    p = saglayici(tmp_path, f)
    with pytest.raises(ModelMissingError) as e:
        p.translate(istek(["A。"]))
    assert e.value is ozel and e.value.__cause__ is None
    f.hata = None
    assert p.translate(istek(["A。"])).translations == ("A。",) and f.calls == 2


def test_b5_fabrika_baseexception_sarilmaz_ve_ornek_tutulmaz(tmp_path: Path) -> None:
    """`except Exception`: KeyboardInterrupt ProviderUnavailable'a sarilmaz (dogru); saglayici kapanmaz, yeniden denenebilir."""
    f = SahteFabrika(hata=KeyboardInterrupt())
    p = saglayici(tmp_path, f)
    with pytest.raises(KeyboardInterrupt):
        p.translate(istek(["A。"]))
    f.hata = None
    assert p.translate(istek(["A。"])).translations == ("A。",) and f.calls == 2


def test_b5_fabrika_bozuk_demet_dondururse_provider_unavailable_cause_valueerror(tmp_path: Path) -> None:
    def iki(model_dir: Path, params: dict[str, object]) -> Any:
        return (SahteMotor(), lambda s: [s])  # 3 degil 2 oge

    model_dosyalari(tmp_path)
    with pytest.raises(ProviderUnavailable) as e:
        LocalNmtProvider(model_dir=tmp_path, motor_fabrikasi=iki).translate(istek(["A。"]))
    assert isinstance(e.value.__cause__, ValueError)


def test_b5_iki_saglayici_ayni_fabrikayi_paylasir_biri_kapaninca_digeri_calisir(tmp_path: Path) -> None:
    f = SahteFabrika()
    model_dosyalari(tmp_path)
    p1 = LocalNmtProvider(model_dir=tmp_path, motor_fabrikasi=f)
    p2 = LocalNmtProvider(model_dir=tmp_path, motor_fabrikasi=f)
    assert p1.translate(istek(["A。"])).translations == ("A。",)
    assert p2.translate(istek(["B。"])).translations == ("B。",)
    assert f.calls == 2 and f.motor.call_count == 2  # her saglayici KENDI kurulumunu yapar (paylasim yok)
    p1.close()
    with pytest.raises(ProviderUnavailable):
        p1.translate(istek(["A。"]))
    assert p2.translate(istek(["C。"])).translations == ("C。",) and f.calls == 2 and f.motor.call_count == 3


@pytest.mark.parametrize("eksik", MODEL_DOSYALARI)
def test_b5_dort_dosyanin_her_biri_icin_modelmissing_fabrika_sayaci_sifir(tmp_path: Path, eksik: str) -> None:
    model_dosyalari(tmp_path, haric=eksik)
    f = SahteFabrika()
    p = LocalNmtProvider(model_dir=tmp_path, motor_fabrikasi=f)
    with pytest.raises(ModelMissingError) as e:
        p.translate(istek(["A。"]))
    assert f.calls == 0 and f.motor.call_count == 0
    assert eksik in str(e.value) and e.value.__cause__ is None
    assert not any(n in str(e.value) for n in NOBETCILER)
    # dosya konunca AYNI ornek kurulur (kapanmadi, kilitlenmedi)
    (tmp_path / eksik).write_bytes(b"")
    assert p.translate(istek(["A。"])).translations == ("A。",) and f.calls == 1


def test_b5_model_dir_yoksa_veya_dosyaysa_modelmissing_fabrika_sifir(tmp_path: Path) -> None:
    f = SahteFabrika()
    with pytest.raises(ModelMissingError):
        LocalNmtProvider(model_dir=tmp_path / "yok", motor_fabrikasi=f).translate(istek(["A。"]))
    dosya = tmp_path / "model.bin"
    dosya.write_bytes(b"")
    with pytest.raises(ModelMissingError):
        LocalNmtProvider(model_dir=dosya, motor_fabrikasi=f).translate(istek(["A。"]))
    assert f.calls == 0


def test_b5_sifir_baytlik_dosyalar_varlik_denetimini_gecer_belgeli(tmp_path: Path) -> None:
    """K6 (a) VARLIK denetimidir (docstring: 'boyut denetlenmez'); sifir bayt fabrikaya gider -> gercek yolda CT2 'incomplete' -> (b)."""
    f = SahteFabrika()
    saglayici(tmp_path, f).translate(istek(["A。"]))
    assert f.calls == 1
    assert "boyut denetlenmez" in (local_nmt.__doc__ or "")


def test_b5_contractviolation_sonrasi_saglayici_kullanilabilir_kalir(tmp_path: Path) -> None:
    durum = {"bozuk": True}

    def cikti(tokens: list[list[str]]) -> list[Any]:
        n = len(tokens) + (1 if durum["bozuk"] else 0)
        return [SahteHipotez([[HEDEF, "".join(t[1:-1])]]) for t in tokens] + [SahteHipotez([[HEDEF, "x"]])] * (n - len(tokens))

    f = SahteFabrika(SahteMotor(cikti=cikti))
    p = saglayici(tmp_path, f)
    with pytest.raises(ContractViolation):
        p.translate(istek(["A。"]))
    durum["bozuk"] = False
    assert p.translate(istek(["A。"])).translations == ("A。",)
    assert f.calls == 1 and f.motor.call_count == 2


def test_b5_motor_istisnasi_sonrasi_motor_yeniden_kurulmaz(tmp_path: Path) -> None:
    f = SahteFabrika(SahteMotor(hata=RuntimeError("gecici")))
    p = saglayici(tmp_path, f)
    with pytest.raises(ProviderUnavailable):
        p.translate(istek(["A。"]))
    f.motor.hata = None
    assert p.translate(istek(["A。"])).translations == ("A。",)
    assert f.calls == 1 and f.motor.call_count == 2


def test_b5_hata_siniflari_kardes_ve_duz(tmp_path: Path) -> None:
    """Taksonomi: ContractViolation / ProviderUnavailable / ModelMissingError birbirinden turemez -> `except` dallari birbirini yutmaz."""
    for a in (ContractViolation, ProviderUnavailable, ModelMissingError):
        for b in (ContractViolation, ProviderUnavailable, ModelMissingError):
            assert (a is b) == issubclass(a, b)
    f = SahteFabrika(SahteMotor(cikti=lambda tokens: [SahteHipotez([[HEDEF, "x"]])] * (len(tokens) + 1)))
    with pytest.raises(ContractViolation) as e:
        saglayici(tmp_path, f).translate(istek(["A。"]))
    assert not isinstance(e.value, ProviderUnavailable)


def test_b5_kapali_saglayici_tip_hatali_istegi_de_provider_unavailable_ile_reddeder(tmp_path: Path) -> None:
    """Sira: kapali mi -> tip dogrulama. Kapali saglayici ContractViolation degil ProviderUnavailable verir."""
    p = saglayici(tmp_path, SahteFabrika())
    p.close()
    with pytest.raises(ProviderUnavailable):
        p.translate(["A。"])  # type: ignore[arg-type]


# ===========================================================================
# B6 -- kapsam durustlugu
# ===========================================================================


def test_b6_tek_pragma_ve_yalniz_gercek_fabrikada_k1_gerekceli() -> None:
    kaynak = KAYNAK.read_text(encoding="utf-8")
    satirlar = [ln for ln in kaynak.splitlines() if "pragma" in ln]
    assert len(satirlar) == 1 and satirlar[0].startswith("def _varsayilan_fabrika(") and "no cover" in satirlar[0]
    agac = ast.parse(kaynak)
    fab = next(d for d in ast.walk(agac) if isinstance(d, ast.FunctionDef) and d.name == "_varsayilan_fabrika")
    kokler = {a.name.split(".")[0] for d in ast.walk(fab) if isinstance(d, ast.Import) for a in d.names}
    assert kokler == {"ctranslate2", "sentencepiece"}  # pragma yalniz K1 geregi kosamayan govdeyi disliyor
    for d in ast.walk(agac):  # baska hicbir fonksiyon bu kutuphaneleri import etmiyor
        if isinstance(d, ast.FunctionDef) and d.name != "_varsayilan_fabrika":
            assert not any(a.name.split(".")[0] in ("ctranslate2", "sentencepiece") for x in ast.walk(d) if isinstance(x, ast.Import) for a in x.names)


def test_b6_docstring_damga_testleri_sayisi_ve_adlari() -> None:
    """Yalniz `__doc__` iceren (davranissiz) teslim testleri: paket 'hem docstring' istedigi icin var; sayilari sabitlenir."""
    agac = ast.parse(TESLIM_TEST.read_text(encoding="utf-8"))
    damga: list[str] = []
    for d in ast.walk(agac):
        if isinstance(d, ast.FunctionDef) and d.name.startswith("test_"):
            src = ast.unparse(d)
            if "__doc__" in src and "translate(" not in src and "LocalNmtProvider(" not in src and "ast.walk" not in src:
                damga.append(d.name)
    assert sorted(damga) == [
        "test_k10_olculmuyor_damgalari_docstringlerde",
        "test_k3_olculmuyor_damgasi_bilinen_zayifliklar_docstringde",
        "test_k5_olculmuyor_damgasi_docstringde",
        "test_k8_olculmuyor_damgasi_ceza_kalitesi_docstringde",
    ], damga
