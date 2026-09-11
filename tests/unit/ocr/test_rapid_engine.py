"""T-006 -- `RapidOcrEngine` birim testleri (K1: gercek model YOK).

Her test `recognizer_factory=` ile SAHTE bir fabrika enjekte eder; gercek
kutuphane bu surecte hic yuklenmez (sefin `conftest.py` bariyeri bunu
`RuntimeError` ile keser). Gercek davranis yalniz
`.agents/tasks/T-006/real_check.py` ile (ayri surec) olculur.

Referanslar BAGIMSIZ kanaldan (PROTOKOL 4.6/8): beklenen model dosya adlari,
dil tablosu degerleri ve anahtar adlari burada SABIT yazilidir -- motorun
kendi tablosundan TURETILMEZ. Kaynak: `.agents/tasks/T-006/evidence/
olcum-2-model-adlari-ve-enum.txt` (rapidocr'un kendi cozucusunun ciktisi).

OCR metni hicbir yere basilmaz (PROTOKOL 7); `print` yok. Tur 2'nin K7
pozitif kontrolleri nobetciyi bir kanala YAZAR ama o kanal `capfd`/`caplog`/
`catch_warnings` ile yutulur; konsola ULASMAZ (asagida "K7 -- tur 2").
"""
from __future__ import annotations

import ast
import dataclasses
import gc
import importlib.metadata
import inspect
import json
import logging
import math
import os
import sys
import warnings
import weakref
from collections.abc import Callable, Iterator, Sequence
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from src.contracts.errors import ContractViolation, ModelMissingError, OcrError
from src.contracts.interfaces import OcrEngine
from src.contracts.models import Frame, OcrPreset, Rect, TextBlock
from src.ocr import rapid_engine
from src.ocr.rapid_engine import (
    OcrLanguage,
    RapidOcrEngine,
    beklenen_model_dosyalari,
    varsayilan_model_dizini,
)

KAYNAK = Path(rapid_engine.__file__)
LOGGER_ADI = "RapidOCR"

# --- BAGIMSIZ referanslar (paket K11 tablosu + olcum-2 dosya adlari) -------

DIL_TABLOSU: dict[OcrLanguage, tuple[str, str]] = {
    OcrLanguage.JAPAN: ("multi", "japan"),
    OcrLanguage.KOREAN: ("multi", "korean"),
    OcrLanguage.CHINESE: ("ch", "ch"),
    OcrLanguage.ENGLISH: ("ch", "en"),
}
MODEL_ADLARI: dict[OcrLanguage, tuple[str, str]] = {
    OcrLanguage.JAPAN: ("multi_PP-OCRv3_det_mobile.onnx", "japan_PP-OCRv4_rec_mobile.onnx"),
    OcrLanguage.KOREAN: ("multi_PP-OCRv3_det_mobile.onnx", "korean_PP-OCRv4_rec_mobile.onnx"),
    OcrLanguage.CHINESE: ("ch_PP-OCRv4_det_mobile.onnx", "ch_PP-OCRv4_rec_mobile.onnx"),
    OcrLanguage.ENGLISH: ("ch_PP-OCRv4_det_mobile.onnx", "en_PP-OCRv4_rec_mobile.onnx"),
}


# --- sahte ciktilar / fabrika ----------------------------------------------


@dataclasses.dataclass
class SahteCikti:
    """rapidocr `RapidOCROutput`'unun bize gereken yuzu (Y4: `None` alanlar)."""

    boxes: Any = None
    txts: Any = None
    scores: Any = None


def kutu(x0: float, y0: float, x1: float, y1: float) -> list[list[float]]:
    """Eksen hizali dortgen cokgeni (rapidocr sirasi: sol-ust, sag-ust, sag-alt, sol-alt)."""
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def cikti(*uclu: tuple[Sequence[Sequence[float]], str, float]) -> SahteCikti:
    """`(kutu, metin, puan)` uclulerinden gercek bicimde cikti: float32 (N,4,2) + tuple'lar."""
    if not uclu:
        return SahteCikti()
    boxes = np.asarray([u[0] for u in uclu], dtype=np.float32)
    return SahteCikti(boxes=boxes, txts=tuple(u[1] for u in uclu), scores=tuple(u[2] for u in uclu))


class SahteFabrika:
    """`params` sozlugunu KAYDEDER, cagri sayar, sabit/ozel tanıyıcı dondurur.

    `taniyici` verilmezse her cagri `sonuc`u dondurur. `kurulumda` verilirse
    fabrika cagrilirken calistirilir (K7: rapidocr'un logger seviyesini
    sifirlamasini taklit etmek icin).
    """

    def __init__(
        self,
        sonuc: SahteCikti | None = None,
        taniyici: Callable[[Any], Any] | None = None,
        kurulumda: Callable[[], None] | None = None,
        hata: BaseException | None = None,
    ) -> None:
        self.sonuc = sonuc if sonuc is not None else SahteCikti()
        self.taniyici = taniyici
        self.kurulumda = kurulumda
        self.hata = hata
        self.params: list[dict[str, object]] = []
        self.calls = 0
        self.goruntuler: list[Any] = []

    def __call__(self, params: dict[str, object]) -> Callable[[Any], Any]:
        self.calls += 1
        self.params.append(dict(params))
        if self.kurulumda is not None:
            self.kurulumda()
        if self.hata is not None:
            raise self.hata
        if self.taniyici is not None:
            return self.taniyici

        def _tani(img: Any) -> Any:
            self.goruntuler.append(img)
            return self.sonuc

        return _tani

    @property
    def son(self) -> dict[str, object]:
        return self.params[-1]


def kare(
    h: int = 40, w: int = 100, rect: Rect | None = None, image: Any = None
) -> Frame:
    if image is None:
        image = np.zeros((h, w, 3), dtype=np.uint8)
    if rect is None:
        rect = Rect(0, 0, w, h)
    return Frame(image=image, rect=rect, captured_at=0.0, seq=0)


def model_dosyalari(dizin: Path, dil: OcrLanguage) -> tuple[Path, Path]:
    """`dizin`e beklenen adlarla BOS dosyalar koyar (K6 olcusu)."""
    det, rec = MODEL_ADLARI[dil]
    (dizin / det).write_bytes(b"")
    (dizin / rec).write_bytes(b"")
    return dizin / det, dizin / rec


def motor(
    tmp_path: Path,
    fabrika: SahteFabrika,
    dil: OcrLanguage = OcrLanguage.JAPAN,
    **ek: Any,
) -> RapidOcrEngine:
    """Sahte fabrikali motor; model dosyalari `tmp_path`te hazir (acik yol dali)."""
    model_dosyalari(tmp_path, dil)
    ek.setdefault("allow_download", False)
    ek.setdefault("model_dir", tmp_path)
    return RapidOcrEngine(language=dil, recognizer_factory=fabrika, **ek)


# ===========================================================================
# K1 -- testler gercek modeli yuklemez; modul duzeyinde rapidocr yok
# ===========================================================================


def _modul_agaci() -> ast.Module:
    return ast.parse(KAYNAK.read_text(encoding="utf-8"))


def test_k1_modul_duzeyinde_rapidocr_import_yok() -> None:
    agac = _modul_agaci()
    for dugum in agac.body:  # yalniz MODUL duzeyi
        if isinstance(dugum, ast.Import):
            assert all(not a.name.split(".")[0] in ("rapidocr", "onnxruntime") for a in dugum.names)
        if isinstance(dugum, ast.ImportFrom):
            assert (dugum.module or "").split(".")[0] not in ("rapidocr", "onnxruntime")


def test_k1_langrec_langdet_adi_modul_duzeyinde_gecmez() -> None:
    """Dil eslemesi bir FONKSIYONUN icinde kurulur; modul govdesinde `LangRec`/`LangDet` adi yok."""
    agac = _modul_agaci()
    for dugum in agac.body:
        if isinstance(dugum, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
            continue
        for alt in ast.walk(dugum):
            if isinstance(alt, ast.Name):
                assert alt.id not in ("LangRec", "LangDet")


def test_k1_sahte_fabrikayla_kosum_rapidocr_yuklemez(tmp_path: Path) -> None:
    f = SahteFabrika(cikti((kutu(1, 1, 5, 5), "x", 0.9)))
    m = motor(tmp_path, f)
    m.recognize(kare(), OcrPreset.DIALOGUE)
    assert not any(k.split(".")[0] in ("rapidocr", "onnxruntime") for k in sys.modules)


def test_varsayilan_model_dizini_rapidocr_yuklemeden_bulunur() -> None:
    """Bariyer altinda `import rapidocr` PATLAR (olcum-1); dizin metadata ile bulunur."""
    try:
        importlib.metadata.distribution("rapidocr")
    except importlib.metadata.PackageNotFoundError:
        pytest.skip("rapidocr dagitimi kurulu degil; dizin cozumlemesi olculemez")
    d = varsayilan_model_dizini()
    assert isinstance(d, Path) and d.name == "models" and d.parent.name == "rapidocr"
    assert "rapidocr" not in sys.modules


def test_varsayilan_model_dizini_paket_yoksa_modelmissing(monkeypatch: pytest.MonkeyPatch) -> None:
    def _yok(_ad: str) -> Any:
        raise importlib.metadata.PackageNotFoundError("rapidocr")

    monkeypatch.setattr(importlib.metadata, "distribution", _yok)
    with pytest.raises(ModelMissingError):
        varsayilan_model_dizini()


def test_uyum_ocrengine_altsinifi() -> None:
    assert issubclass(RapidOcrEngine, OcrEngine)
    assert not hasattr(RapidOcrEngine, "__enter__") and not hasattr(RapidOcrEngine, "__exit__")  # K10
    assert not hasattr(RapidOcrEngine(language=OcrLanguage.JAPAN), "last_timing")  # K9: sure tutmaz


# ===========================================================================
# K2 -- dil acik secilir
# ===========================================================================


def test_k2_language_parametresinin_varsayilani_yok() -> None:
    imza = inspect.signature(RapidOcrEngine.__init__)
    p = imza.parameters["language"]
    assert p.kind is inspect.Parameter.KEYWORD_ONLY
    assert p.default is inspect.Parameter.empty
    with pytest.raises(TypeError):
        RapidOcrEngine()  # type: ignore[call-arg]


def test_k2_dil_dogrulanir() -> None:
    with pytest.raises(ValueError):
        RapidOcrEngine(language="klingon")  # type: ignore[arg-type]
    m = RapidOcrEngine(language="japan")  # type: ignore[arg-type]  # StrEnum degeri kabul
    assert m.language is OcrLanguage.JAPAN
    assert RapidOcrEngine(language=OcrLanguage.KOREAN).language is OcrLanguage.KOREAN


def test_k2_ocrlanguage_degerleri() -> None:
    assert [m.value for m in OcrLanguage] == ["japan", "korean", "chinese", "english"]


# ===========================================================================
# K3 -- is parcacigi acik; "otomatik" hicbir yoldan girmez
# ===========================================================================

INTRA = "EngineConfig.onnxruntime.intra_op_num_threads"
INTER = "EngineConfig.onnxruntime.inter_op_num_threads"


@pytest.mark.parametrize("n", [4, 8])
def test_k3_threads_iki_anahtara_aynen_gider(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, n: int) -> None:
    monkeypatch.setattr(os, "cpu_count", lambda: 32)
    f = SahteFabrika()
    motor(tmp_path, f, threads=n).recognize(kare(), OcrPreset.DIALOGUE)
    assert f.son[INTRA] == n and f.son[INTER] == n
    assert type(f.son[INTRA]) is int and type(f.son[INTER]) is int
    assert f.son["Global.use_cls"] is False


def test_k3_threads_none_min8_cpu(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "cpu_count", lambda: 32)
    f = SahteFabrika()
    motor(tmp_path, f).recognize(kare(), OcrPreset.DIALOGUE)
    assert f.son[INTRA] == 8 and f.son[INTER] == 8
    monkeypatch.setattr(os, "cpu_count", lambda: 6)
    f2 = SahteFabrika()
    motor(tmp_path, f2, threads=None).recognize(kare(), OcrPreset.DIALOGUE)
    assert f2.son[INTRA] == 6 and f2.son[INTER] == 6


def test_k3_threads_cpu_ustu_valueerror_sessiz_otomatik_degil(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "cpu_count", lambda: 6)
    with pytest.raises(ValueError):
        RapidOcrEngine(language=OcrLanguage.JAPAN, threads=8)
    with pytest.raises(ValueError):
        RapidOcrEngine(language=OcrLanguage.JAPAN, threads=7)
    RapidOcrEngine(language=OcrLanguage.JAPAN, threads=6)  # tam sinir: gecer
    RapidOcrEngine(language=OcrLanguage.JAPAN, threads=4)  # pozitif kontrol


@pytest.mark.parametrize("n", [0, -1, -8])
def test_k3_threads_sifir_ve_negatif_valueerror(n: int) -> None:
    with pytest.raises(ValueError):
        RapidOcrEngine(language=OcrLanguage.JAPAN, threads=n)


@pytest.mark.parametrize("n", [True, 2.0, "8", 4.5])
def test_k3_threads_tamsayi_olmayan_typeerror(n: Any) -> None:
    with pytest.raises(TypeError):
        RapidOcrEngine(language=OcrLanguage.JAPAN, threads=n)


def test_k3_threads_numpy_tamsayi_duz_int_olur(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "cpu_count", lambda: 32)
    f = SahteFabrika()
    motor(tmp_path, f, threads=np.int64(4)).recognize(kare(), OcrPreset.DIALOGUE)  # type: ignore[arg-type]
    assert f.son[INTRA] == 4 and type(f.son[INTRA]) is int


def test_k3_cpu_count_none_ise_bir_sayilir(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "cpu_count", lambda: None)
    assert RapidOcrEngine(language=OcrLanguage.JAPAN).threads == 1
    with pytest.raises(ValueError):
        RapidOcrEngine(language=OcrLanguage.JAPAN, threads=2)


# ===========================================================================
# K4 -- bbox ekran koordinatinda, duz int, eksen hizali
# ===========================================================================

EGIK = [[10.6, 20.6], [51.2, 18.9], [51.2, 40.1], [11.1, 42.3]]
"""Egik cokgen: min_x=10.6 (floor 10 / round 11), min_y=18.9 (floor 18 / round 19),
max_x=51.2 (ceil 52 / round 51), max_y=42.3 (ceil 43 / round 42) -- her kenar round/int'ten AYRISIR."""


def _bbox_duz_int(b: TextBlock) -> bool:
    return all(type(getattr(b.bbox, a)) is int for a in ("x", "y", "w", "h", "monitor_index"))


@pytest.mark.parametrize(
    "rect",
    [Rect(0, 0, 100, 40), Rect(-2600, -50, 100, 40, monitor_index=0), Rect(300, 700, 100, 40, monitor_index=1, dpi_scale=1.5)],
)
def test_k4_bbox_kaydirma_tam_rect_kadar_ve_duz_int(tmp_path: Path, rect: Rect) -> None:
    f = SahteFabrika(cikti((EGIK, "a", 0.9)))
    [b] = motor(tmp_path, f).recognize(kare(rect=rect), OcrPreset.DIALOGUE)
    assert (b.bbox.x, b.bbox.y, b.bbox.w, b.bbox.h) == (10 + rect.x, 18 + rect.y, 42, 25)
    assert _bbox_duz_int(b)
    assert b.bbox.monitor_index == rect.monitor_index and b.bbox.dpi_scale == rect.dpi_scale
    json.dumps(dataclasses.asdict(b.bbox))


def test_k4_iki_nokta_farki_tam_kaydirma(tmp_path: Path) -> None:
    f = SahteFabrika(cikti((EGIK, "a", 0.9)))
    m = motor(tmp_path, f)
    [b0] = m.recognize(kare(rect=Rect(0, 0, 100, 40)), OcrPreset.DIALOGUE)
    [b1] = m.recognize(kare(rect=Rect(-2600, -50, 100, 40)), OcrPreset.DIALOGUE)
    assert (b1.bbox.x - b0.bbox.x, b1.bbox.y - b0.bbox.y) == (-2600, -50)
    assert (b1.bbox.w, b1.bbox.h) == (b0.bbox.w, b0.bbox.h)


def test_k4_tam_sayi_koseli_cokgen_fazla_piksel_yok(tmp_path: Path) -> None:
    f = SahteFabrika(cikti(([[10, 20], [50, 20], [50, 40], [10, 40]], "a", 0.9)))
    [b] = motor(tmp_path, f).recognize(kare(), OcrPreset.DIALOGUE)
    assert (b.bbox.x, b.bbox.y, b.bbox.w, b.bbox.h) == (10, 20, 40, 20)


def test_k4_goruntu_disina_tasan_cokgen_kirpilmaz(tmp_path: Path) -> None:
    f = SahteFabrika(cikti((kutu(-5.4, -3.2, 130.1, 45.9), "a", 0.9)))  # -5.4: floor -6, round/int -5
    [b] = motor(tmp_path, f).recognize(kare(h=40, w=100, rect=Rect(10, 10, 100, 40)), OcrPreset.DIALOGUE)
    assert (b.bbox.x, b.bbox.y, b.bbox.w, b.bbox.h) == (10 - 6, 10 - 4, 137, 50)


def test_k4_dejenere_cokgen_w0_oldugu_gibi_gecer(tmp_path: Path) -> None:
    f = SahteFabrika(cikti(([[10, 20], [10, 20], [10, 40], [10, 40]], "a", 0.9)))
    [b] = motor(tmp_path, f).recognize(kare(), OcrPreset.DIALOGUE)
    assert (b.bbox.w, b.bbox.h) == (0, 20) and _bbox_duz_int(b)


def test_k4_line_boxes_bos_ve_sira_korunur(tmp_path: Path) -> None:
    f = SahteFabrika(cikti((kutu(0, 30, 5, 35), "ikinci", 0.5), (kutu(0, 0, 5, 5), "birinci", 0.7)))
    bl = motor(tmp_path, f).recognize(kare(), OcrPreset.DIALOGUE)
    assert [b.text for b in bl] == ["ikinci", "birinci"]  # rapidocr sirasi, yeniden siralama YOK
    assert all(b.line_boxes == () for b in bl)


# ===========================================================================
# K5 -- guven suzulmez; kutuphane suzgeci kapatilir
# ===========================================================================


def test_k5_text_score_sifir_params(tmp_path: Path) -> None:
    f = SahteFabrika()
    motor(tmp_path, f).recognize(kare(), OcrPreset.DIALOGUE)
    assert f.son["Global.text_score"] == 0.0 and type(f.son["Global.text_score"]) is float


def test_k5_uc_blok_aynen_metin_degismez(tmp_path: Path) -> None:
    f = SahteFabrika(cikti((kutu(0, 0, 5, 5), " bosluklu ", 0.05), (kutu(0, 10, 5, 15), "", 0.99), (kutu(0, 20, 5, 25), "u", 0.60)))
    bl = motor(tmp_path, f).recognize(kare(), OcrPreset.DIALOGUE)
    assert [b.text for b in bl] == [" bosluklu ", "", "u"]
    assert [b.confidence for b in bl] == [0.05, 0.99, 0.60]
    assert all(type(b.confidence) is float for b in bl)


def test_k5_bos_sonuc_boxes_none_bos_liste(tmp_path: Path) -> None:
    f = SahteFabrika(SahteCikti(boxes=None, txts=None, scores=None))
    assert motor(tmp_path, f).recognize(kare(), OcrPreset.DIALOGUE) == []
    f2 = SahteFabrika(SahteCikti(boxes=None, txts=(), scores=()))
    assert motor(tmp_path, f2).recognize(kare(), OcrPreset.DIALOGUE) == []
    f3 = SahteFabrika(SahteCikti(boxes=np.zeros((0, 4, 2), np.float32), txts=(), scores=()))
    assert motor(tmp_path, f3).recognize(kare(), OcrPreset.DIALOGUE) == []


def test_k5_nan_puan_aynen_float(tmp_path: Path) -> None:
    f = SahteFabrika(cikti((kutu(0, 0, 5, 5), "a", float("nan"))))
    [b] = motor(tmp_path, f).recognize(kare(), OcrPreset.DIALOGUE)
    assert math.isnan(b.confidence) and type(b.confidence) is float


def test_k5_numpy_puan_duz_float(tmp_path: Path) -> None:
    f = SahteFabrika(SahteCikti(boxes=np.asarray([kutu(0, 0, 5, 5)], np.float32), txts=("a",), scores=(np.float32(0.25),)))
    [b] = motor(tmp_path, f).recognize(kare(), OcrPreset.DIALOGUE)
    assert b.confidence == pytest.approx(0.25) and type(b.confidence) is float


# ===========================================================================
# K6 -- hata siniflandirmasi ve indirme denetimi
# ===========================================================================


def test_k6_model_yok_fabrika_cagrilmadan_modelmissing(tmp_path: Path) -> None:
    f = SahteFabrika()
    m = RapidOcrEngine(language=OcrLanguage.JAPAN, allow_download=False, model_dir=tmp_path, recognizer_factory=f)
    with pytest.raises(ModelMissingError) as ei:
        m.recognize(kare(), OcrPreset.DIALOGUE)
    assert f.calls == 0
    assert ei.value.__cause__ is None
    det, rec = MODEL_ADLARI[OcrLanguage.JAPAN]
    assert det in str(ei.value) and rec in str(ei.value)


def test_k6_yalniz_rec_eksikse_adi_mesajda(tmp_path: Path) -> None:
    det, rec = MODEL_ADLARI[OcrLanguage.ENGLISH]
    (tmp_path / det).write_bytes(b"")
    f = SahteFabrika()
    m = RapidOcrEngine(language=OcrLanguage.ENGLISH, model_dir=tmp_path, recognizer_factory=f)
    with pytest.raises(ModelMissingError) as ei:
        m.recognize(kare(), OcrPreset.DIALOGUE)
    assert rec in str(ei.value) and det not in str(ei.value) and f.calls == 0


@pytest.mark.parametrize("dil", list(OcrLanguage))
def test_k6_model_var_acik_yol_gecilir(tmp_path: Path, dil: OcrLanguage) -> None:
    f = SahteFabrika()
    det_yol, rec_yol = model_dosyalari(tmp_path, dil)
    RapidOcrEngine(language=dil, allow_download=False, model_dir=tmp_path, recognizer_factory=f).recognize(kare(), OcrPreset.DIALOGUE)
    assert f.calls == 1
    assert f.son["Det.model_path"] == det_yol and f.son["Rec.model_path"] == rec_yol
    assert "Global.model_root_dir" not in f.son
    assert beklenen_model_dosyalari(dil) == MODEL_ADLARI[dil]


def test_k6_model_dir_str_kabul(tmp_path: Path) -> None:
    f = SahteFabrika()
    det_yol, _ = model_dosyalari(tmp_path, OcrLanguage.JAPAN)
    RapidOcrEngine(language=OcrLanguage.JAPAN, model_dir=str(tmp_path), recognizer_factory=f).recognize(kare(), OcrPreset.DIALOGUE)  # type: ignore[arg-type]
    assert f.son["Det.model_path"] == det_yol


def test_k6_allow_download_true_model_path_yok(tmp_path: Path) -> None:
    f = SahteFabrika()
    RapidOcrEngine(language=OcrLanguage.JAPAN, allow_download=True, recognizer_factory=f).recognize(kare(), OcrPreset.DIALOGUE)
    assert not any(k.endswith("model_path") for k in f.son)
    assert "Global.model_root_dir" not in f.son
    f2 = SahteFabrika()
    RapidOcrEngine(language=OcrLanguage.JAPAN, allow_download=True, model_dir=tmp_path, recognizer_factory=f2).recognize(kare(), OcrPreset.DIALOGUE)
    assert not any(k.endswith("model_path") for k in f2.son)
    assert f2.son["Global.model_root_dir"] == tmp_path  # KARAR: indirme hedefi cagiranin dizini


def test_k6_allow_download_bool_olmali() -> None:
    with pytest.raises(TypeError):
        RapidOcrEngine(language=OcrLanguage.JAPAN, allow_download=1)  # type: ignore[arg-type]


def test_k6_taniyici_istisnasi_ocrerror_cause_korunur(tmp_path: Path) -> None:
    ozgun = RuntimeError("motor patladi")

    def _pat(_img: Any) -> Any:
        raise ozgun

    f = SahteFabrika(taniyici=_pat)
    with pytest.raises(OcrError) as ei:
        motor(tmp_path, f).recognize(kare(), OcrPreset.DIALOGUE)
    assert ei.value.__cause__ is ozgun


def test_k6_taniyici_sozlesme_hatasi_oldugu_gibi_gecer(tmp_path: Path) -> None:
    """Gercek fabrikanin tanıyıcısı beklenmeyen cikti tipinde `OcrError` firlatir; sarilmaz."""
    ozel = OcrError("beklenmeyen cikti tipi")

    def _pat(_img: Any) -> Any:
        raise ozel

    f = SahteFabrika(taniyici=_pat)
    with pytest.raises(OcrError) as ei:
        motor(tmp_path, f).recognize(kare(), OcrPreset.DIALOGUE)
    assert ei.value is ozel and ei.value.__cause__ is None


def test_k6_fabrika_istisnasi_siniflandirilir(tmp_path: Path) -> None:
    with pytest.raises(OcrError) as e1:
        motor(tmp_path, SahteFabrika(hata=RuntimeError("kurulum"))).recognize(kare(), OcrPreset.DIALOGUE)
    assert isinstance(e1.value.__cause__, RuntimeError)
    with pytest.raises(OcrError) as e2:  # Y2: desteklenmeyen kombinasyon -> ValueError -> OcrError
        motor(tmp_path, SahteFabrika(hata=ValueError("Unsupported"))).recognize(kare(), OcrPreset.DIALOGUE)
    assert isinstance(e2.value.__cause__, ValueError)
    with pytest.raises(ModelMissingError) as e3:
        motor(tmp_path, SahteFabrika(hata=FileNotFoundError("x.onnx"))).recognize(kare(), OcrPreset.DIALOGUE)
    assert isinstance(e3.value.__cause__, FileNotFoundError)
    ozel = ModelMissingError("indirilemedi")
    with pytest.raises(ModelMissingError) as e4:  # sozlesme hatasi OLDUGU GIBI gecer
        motor(tmp_path, SahteFabrika(hata=ozel)).recognize(kare(), OcrPreset.DIALOGUE)
    assert e4.value is ozel


def test_k6_fabrika_hatasindan_sonra_yeniden_denenebilir(tmp_path: Path) -> None:
    f = SahteFabrika(hata=RuntimeError("ilk"))
    m = motor(tmp_path, f)
    with pytest.raises(OcrError):
        m.recognize(kare(), OcrPreset.DIALOGUE)
    f.hata = None
    assert m.recognize(kare(), OcrPreset.DIALOGUE) == [] and f.calls == 2


@pytest.mark.parametrize(
    "image",
    [
        np.zeros((40, 100, 4), np.uint8),
        np.zeros((40, 100), np.uint8),
        np.zeros((40, 100, 3), np.float32),
        np.zeros((40, 100, 1), np.uint8),
        np.zeros((0, 0, 3), np.uint8),  # 0x0: rapidocr'da ZeroDivisionError (olcum-3)
        np.zeros((0, 100, 3), np.uint8),
        np.zeros((40, 0, 3), np.uint8),
        np.zeros((40, 100, 3), np.uint8).tolist(),  # ndarray degil
        np.zeros((2, 40, 100, 3), np.uint8),
    ],
)
def test_k6_kare_bicimi_contractviolation_motor_cagrilmaz(tmp_path: Path, image: Any) -> None:
    f = SahteFabrika()
    m = motor(tmp_path, f)
    with pytest.raises(ContractViolation):
        m.recognize(kare(image=image), OcrPreset.DIALOGUE)
    assert f.calls == 0


def test_k6_frame_olmayan_girdi_contractviolation(tmp_path: Path) -> None:
    f = SahteFabrika()
    m = motor(tmp_path, f)
    with pytest.raises(ContractViolation):
        m.recognize(np.zeros((40, 100, 3), np.uint8), OcrPreset.DIALOGUE)  # type: ignore[arg-type]
    with pytest.raises(ContractViolation):
        m.recognize(None, OcrPreset.DIALOGUE)  # type: ignore[arg-type]
    assert f.calls == 0


def test_k6_1x1_kare_taniyiciya_gider(tmp_path: Path) -> None:
    f = SahteFabrika()
    assert motor(tmp_path, f).recognize(kare(h=1, w=1, rect=Rect(0, 0, 1, 1)), OcrPreset.DIALOGUE) == []
    assert f.calls == 1 and f.goruntuler[0].shape == (1, 1, 3)


def test_k6_goruntu_aynen_kopyasiz_gecer(tmp_path: Path) -> None:
    img = np.zeros((40, 100, 3), np.uint8)
    f = SahteFabrika()
    motor(tmp_path, f).recognize(kare(image=img), OcrPreset.DIALOGUE)
    assert f.goruntuler[0] is img


def test_k6_rect_duz_int_degilse_contractviolation(tmp_path: Path) -> None:
    f = SahteFabrika()
    m = motor(tmp_path, f)
    with pytest.raises(ContractViolation):
        m.recognize(kare(rect=Rect(np.int64(0), 0, 100, 40)), OcrPreset.DIALOGUE)  # type: ignore[arg-type]
    with pytest.raises(ContractViolation):
        m.recognize(kare(rect=Rect(0, 0, 100, 40, monitor_index=np.int32(1))), OcrPreset.DIALOGUE)  # type: ignore[arg-type]
    assert f.calls == 0


@pytest.mark.parametrize(
    "c",
    [
        SahteCikti(boxes=np.zeros((2, 4, 2), np.float32), txts=("a",), scores=(0.5, 0.5)),  # uzunluk farki
        SahteCikti(boxes=np.zeros((1, 4, 2), np.float32), txts=("a",), scores=(0.5, 0.5)),
        SahteCikti(boxes=np.zeros((1, 4, 2), np.float32), txts=None, scores=(0.5,)),  # boxes var txts None
        SahteCikti(boxes=np.zeros((1, 4, 2), np.float32), txts=("a",), scores=None),
        SahteCikti(boxes=np.zeros((1, 4, 2), np.float32), txts=(None,), scores=(0.5,)),  # txts icinde None
        SahteCikti(boxes=np.zeros((1, 4, 2), np.float32), txts=(b"a",), scores=(0.5,)),
        SahteCikti(boxes=None, txts=("a",), scores=(0.5,)),  # kutusuz metin
        SahteCikti(boxes=np.zeros((1, 4, 3), np.float32), txts=("a",), scores=(0.5,)),  # cokgen bicimi
        SahteCikti(boxes=np.zeros((1, 0, 2), np.float32), txts=("a",), scores=(0.5,)),
        SahteCikti(boxes=np.asarray([[[float("nan"), 0], [1, 0], [1, 1], [0, 1]]], np.float32), txts=("a",), scores=(0.5,)),
        SahteCikti(boxes=np.asarray([[[float("inf"), 0], [1, 0], [1, 1], [0, 1]]], np.float32), txts=("a",), scores=(0.5,)),
        SahteCikti(boxes=np.zeros((1, 4, 2), np.float32), txts=("a",), scores=("0.5",)),  # puan sayi degil
        SahteCikti(boxes=np.zeros((1, 4, 2), np.float32), txts=("a",), scores=(True,)),
        SahteCikti(boxes=5, txts=("a",), scores=(0.5,)),  # uzunlugu yok
        SahteCikti(boxes=None, txts=7, scores=None),  # boxes None, txts skaler
        SahteCikti(boxes=np.zeros((1, 4, 2), np.float32), txts="a", scores=(0.5,)),  # txts dizi degil, duz str
        SahteCikti(boxes=[[["a", 0], [1, 0], [1, 1], [0, 1]]], txts=("a",), scores=(0.5,)),
        object(),  # alanlari yok
    ],
)
def test_k6_bozuk_cikti_ocrerror(tmp_path: Path, c: Any) -> None:
    f = SahteFabrika(taniyici=lambda _img: c)
    with pytest.raises(OcrError):
        motor(tmp_path, f).recognize(kare(), OcrPreset.DIALOGUE)


def test_k6_varsayilan_fabrika_isinstance_dali_olculmuyor_damgali() -> None:
    """Tur 2: gercek fabrikanin `isinstance(cikti, RapidOCROutput)` dali olculmuyor -- damga docstring'de (4.6/2)."""
    doc = rapid_engine._varsayilan_fabrika.__doc__ or ""
    assert "[ÖLÇÜLMÜYOR]" in doc and "isinstance" in doc


def test_k6_hata_mesaji_ocr_metni_tasimaz(tmp_path: Path) -> None:
    """PROTOKOL 7: bozuk ciktida bile istisna metni blok metnini icermez."""
    nobetci = "NOBETCI-9c1e"
    c = SahteCikti(boxes=np.zeros((1, 4, 2), np.float32), txts=(nobetci,), scores=("x",))
    f = SahteFabrika(taniyici=lambda _img: c)
    with pytest.raises(OcrError) as ei:
        motor(tmp_path, f).recognize(kare(), OcrPreset.DIALOGUE)
    assert nobetci not in str(ei.value)


# ===========================================================================
# K7 -- loglama disiplini; rapidocr logu kurulumdan SONRA susturulur
# ===========================================================================


def test_k7_ast_print_yok_logging_metin_yok() -> None:
    agac = _modul_agaci()
    for dugum in ast.walk(agac):
        if isinstance(dugum, ast.Call):
            if isinstance(dugum.func, ast.Name):
                assert dugum.func.id != "print"
            kaynak = ast.unparse(dugum)
            if "logging." in kaynak or "logger." in kaynak or "getLogger" in kaynak:
                assert ".text" not in kaynak and "txts" not in kaynak


def test_k7_logger_seviyesi_fabrikadan_sonra_error(tmp_path: Path) -> None:
    lg = logging.getLogger(LOGGER_ADI)
    lg.setLevel(logging.ERROR)
    f = SahteFabrika(kurulumda=lambda: lg.setLevel(logging.INFO))  # rapidocr'u taklit: kurulum sifirlar
    motor(tmp_path, f).recognize(kare(), OcrPreset.DIALOGUE)
    assert lg.level == logging.ERROR
    assert f.son["Global.log_level"] == "error"


def test_k7_nobetci_metin_loga_dusmez(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    nobetci = "NOBETCI-7f3a"
    lg = logging.getLogger(LOGGER_ADI)

    def _tani(_img: Any) -> Any:
        lg.warning("kutuphane uyarisi %s", nobetci)  # gercek kutuphane WARNING basar (bos kare)
        return cikti((kutu(0, 0, 5, 5), nobetci, 0.9))

    f = SahteFabrika(taniyici=_tani, kurulumda=lambda: lg.setLevel(logging.INFO))
    with caplog.at_level(logging.DEBUG, logger=LOGGER_ADI):
        [b] = motor(tmp_path, f).recognize(kare(), OcrPreset.DIALOGUE)
    assert b.text == nobetci
    assert all(nobetci not in r.getMessage() for r in caplog.records)
    assert not [r for r in caplog.records if r.name == LOGGER_ADI]


def test_k7_pozitif_kontrol_seviye_dusurulmezse_uyari_gecer(caplog: pytest.LogCaptureFixture) -> None:
    """Olcunun ateslendigi gosterilir: ERROR'a cekilmemis logger WARNING'i GECIRIR."""
    lg = logging.getLogger(LOGGER_ADI)
    with caplog.at_level(logging.WARNING, logger=LOGGER_ADI):
        lg.warning("pozitif-kontrol")
    assert any("pozitif-kontrol" in r.getMessage() for r in caplog.records)


# ===========================================================================
# K7 -- tur 2: olcu DAVRANISA kancali (PROTOKOL 4.6/7), kanal-bagimsiz
# ===========================================================================
#
# Degismez (sef karari T2-1): `recognize` suresince OCR metni HICBIR cikis
# kanalina yazilmaz -- stdout, stderr, herhangi bir `logging` logger'i (ad ve
# seviye ne olursa olsun), `warnings`. Tur 1'in olcusu `print` ADINI sayiyor ve
# yalniz `RapidOCR` logger'ini dinliyordu; `sys.stdout.write(blok.text)` ekleyen
# mutant 95 testten geciyordu. Asagidaki olcu davranisi olcer:
#
#   * `capfd`  -- dosya tanimlayici duzeyinde stdout/stderr: `sys.stdout.write`i
#                 de, `os.write(1, ...)`i de, `sys.__stderr__`i de gorur
#                 (`capsys` yalniz `sys.stdout` nesnesini gorur; `capfd` ust kume).
#                 Beklenen: out == "" VE err == "" -- sifir bayt, "nobetci
#                 icermez" YETMEZ.
#   * `caplog` -- KOK logger DEBUG (logger belirtmeden); `RapidOCR` logger'ina
#                 `caplog.handler` DOGRUDAN takilir ki kutuphanenin
#                 `propagate=False` ayari olcuyu kor birakmasin. Beklenen: hicbir
#                 `record.getMessage()` iki nobetciyi de icermez.
#   * `warnings.catch_warnings(record=True)` + `simplefilter("always")` --
#                 `warnings.warn` kanali (uretimde stderr'e gider; pytest ayri
#                 yakalar, bu yuzden `capfd` goremez). "always" sart: "default"
#                 suzgec ayni konumdan ikinci uyariyi bastirir, sicak nokta kor
#                 kalirdi. Beklenen: hicbir uyari metni nobetci icermez.
#
# Iki nokta (4.6/7): SOGUK motor (ilk recognize = kurulum + tanima) ve SICAK
# motor (kurulum bitmis, kutuphane logger'i uygulama debug modu gibi SONRADAN
# acilmis -- motor seviyeyi yalniz kurulumda ceker, sonra dokunmaz). Pozitif
# kontroller: `OcrEngine`i uygulayan, nobetciyi bir kanala yazan test ici sahte
# motorlar AYNI olcu fonksiyonundan gecirilir ve DUSER (4.6/10).

NOBETCILER: tuple[str, str] = ("NÖBETÇİ-7f3a", "長老-9c1e")
"""Iki nobetci: Turkce harfli Latin + ASCII-disi CJK (cp1254 tuzagi -- Windows)."""


def _kutuphane_gibi_kur() -> None:
    """Gercek kutuphanenin kurulumda yaptigi: `RapidOCR` logger'i INFO + propagate KAPALI."""
    lg = logging.getLogger(LOGGER_ADI)
    lg.setLevel(logging.INFO)
    lg.propagate = False


@pytest.fixture
def kutuphane_logger_geri_al() -> Iterator[None]:
    """`RapidOCR` logger'inin seviye/propagate/handler'larini test sonunda geri alir (global durum sizmasin)."""
    lg = logging.getLogger(LOGGER_ADI)
    eski_seviye, eski_propagate, eski_handlerlar = lg.level, lg.propagate, list(lg.handlers)
    yield
    lg.setLevel(eski_seviye)
    lg.propagate = eski_propagate
    lg.handlers[:] = eski_handlerlar


def _nobetci_ciktisi() -> SahteCikti:
    return cikti((kutu(0, 0, 5, 5), NOBETCILER[0], 0.9), (kutu(0, 10, 5, 15), NOBETCILER[1], 0.4))


def _ozgun_akislari_bosalt() -> None:
    """`sys.__stdout__`/`sys.__stderr__` tamponunu fd'ye indirir (capfd ancak fd'de gorur).

    `capfd` `sys.stdout/stderr`i tamponsuz kopyayla degistirir ama OZGUN nesneler
    (`sys.__std*__`) kendi satir tamponunu korur: newline'siz bir `write` fd'ye
    inmeden olcum penceresi kapanabilirdi. Pencerenin iki ucunda bosaltilir ki
    olcum tampona degil DAVRANISA bagli olsun. Pencereli pakette (`pythonw`)
    bu nesneler `None`dur -- atlanir.
    """
    for akis in (sys.__stdout__, sys.__stderr__):
        if akis is not None:
            akis.flush()


def _k7_kanal_olcusu(
    m: OcrEngine,
    capfd: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> list[TextBlock]:
    """K7'nin kanal-bagimsiz olcusu: TEK `recognize` cagrisi, uc kanal, sifir sizinti.

    Kutuphane logger'i `propagate=False` olsa bile gorulsun diye `caplog.handler`
    ona DOGRUDAN takilir (sonunda kaldirilir; `propagate` eski degerine doner).
    Sahte motorlar da ayni fonksiyondan gecer -- olcu motora degil DAVRANISA bagli.
    """
    lg = logging.getLogger(LOGGER_ADI)
    eski_propagate = lg.propagate
    caplog.set_level(logging.DEBUG)  # KOK logger + caplog.handler: DEBUG
    caplog.set_level(logging.DEBUG, logger=LOGGER_ADI)  # uygulama debug modu: kutuphane logger'i ACIK
    lg.addHandler(caplog.handler)  # propagate=False kor birakmasin
    caplog.clear()
    _ozgun_akislari_bosalt()
    capfd.readouterr()  # olcum oncesi artiklari at
    try:
        with warnings.catch_warnings(record=True) as uyari_kayitlari:
            warnings.simplefilter("always")  # "default" olsaydi ayni konumdan 2. uyari BASTIRILIRDI (sicak nokta kor kalirdi)
            bloklar = m.recognize(kare(), OcrPreset.DIALOGUE)
    finally:
        lg.removeHandler(caplog.handler)
        lg.propagate = eski_propagate
    _ozgun_akislari_bosalt()  # `sys.__stderr__.write` satir tamponunda kalmasin; fd'ye insin
    out, err = capfd.readouterr()
    assert out == "", f"stdout'a {len(out)} karakter yazildi (sifir olmali)"
    assert err == "", f"stderr'e {len(err)} karakter yazildi (sifir olmali)"
    mesajlar = [r.getMessage() for r in caplog.records]
    uyarilar = [str(w.message) for w in uyari_kayitlari]
    for n in NOBETCILER:
        assert not [msg for msg in mesajlar if n in msg], "nobetci bir log kaydina dustu"
        assert not [u for u in uyarilar if n in u], "nobetci bir warnings kaydina dustu"
    return bloklar


def test_k7_soguk_motor_hicbir_kanala_metin_yazmaz(
    tmp_path: Path,
    kutuphane_logger_geri_al: None,
    capfd: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Nokta 1: ilk `recognize` (kurulum + tanima) -- stdout/stderr sifir bayt, log/uyari temiz."""
    f = SahteFabrika(_nobetci_ciktisi(), kurulumda=_kutuphane_gibi_kur)
    bloklar = _k7_kanal_olcusu(motor(tmp_path, f), capfd, caplog)
    assert [b.text for b in bloklar] == list(NOBETCILER)  # metin motordan AYNEN cikti
    assert f.calls == 1


def test_k7_sicak_motor_kutuphane_logger_i_acikken_metin_yazmaz(
    tmp_path: Path,
    kutuphane_logger_geri_al: None,
    capfd: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Nokta 2: kurulum bitti, sonra `RapidOCR` logger'i DEBUG'a acildi (uygulama debug modu).

    Motor seviyeyi yalniz kurulumda ERROR'a ceker; ikinci `recognize` fabrikayi
    cagirmaz, dolayisiyla acik logger acik kalir -- kutuphane logger'ina `.info`
    ile metin yazan bir uygulama burada gorunur.
    """
    f = SahteFabrika(_nobetci_ciktisi(), kurulumda=_kutuphane_gibi_kur)
    m = motor(tmp_path, f)
    m.recognize(kare(), OcrPreset.DIALOGUE)  # kurulum; motor RapidOCR'u ERROR'a cekti
    assert logging.getLogger(LOGGER_ADI).level == logging.ERROR
    bloklar = _k7_kanal_olcusu(m, capfd, caplog)
    assert [b.text for b in bloklar] == list(NOBETCILER)
    assert f.calls == 1


# -- pozitif kontroller (4.6/10): olcu ATESLIYOR mu? ----------------------------
#
# `OcrEngine`i uygulayan 5 satirlik sahte motorlar; her biri nobetciyi TEK bir
# kanala yazar. Yazilan sey `capfd`/`caplog`/`catch_warnings` tarafindan yutulur,
# konsola/dosyaya ULASMAZ. Olcu her birinde AssertionError vermeli.


def _blok(metin: str) -> TextBlock:
    return TextBlock(text=metin, bbox=Rect(0, 0, 5, 5), confidence=0.9)


class _StdoutaYazan(OcrEngine):
    def recognize(self, frame: Frame, preset: OcrPreset) -> list[TextBlock]:
        sys.stdout.write(NOBETCILER[0])  # M25b sinifi
        return [_blok(NOBETCILER[0])]


class _StderreYazan(OcrEngine):
    def recognize(self, frame: Frame, preset: OcrPreset) -> list[TextBlock]:
        sys.stderr.write(NOBETCILER[1])
        return [_blok(NOBETCILER[1])]


class _FdYeYazan(OcrEngine):
    def recognize(self, frame: Frame, preset: OcrPreset) -> list[TextBlock]:
        os.write(1, NOBETCILER[1].encode("utf-8"))  # sys.stdout'u atlar; capsys GOREMEZ, capfd gorur
        return [_blok(NOBETCILER[1])]


class _OzgunStderreYazan(OcrEngine):
    def recognize(self, frame: Frame, preset: OcrPreset) -> list[TextBlock]:
        assert sys.__stderr__ is not None
        sys.__stderr__.write(NOBETCILER[0])  # newline YOK: satir tamponunda kalir; bosaltma olmasa gorunmezdi
        return [_blok(NOBETCILER[0])]


class _KokLoggeraYazan(OcrEngine):
    def recognize(self, frame: Frame, preset: OcrPreset) -> list[TextBlock]:
        logging.getLogger("suflor.ocr").debug("blok %s", NOBETCILER[0])  # M28c sinifi
        return [_blok(NOBETCILER[0])]


class _KutuphaneLoggerinaYazan(OcrEngine):
    def recognize(self, frame: Frame, preset: OcrPreset) -> list[TextBlock]:
        lg = logging.getLogger(LOGGER_ADI)
        lg.propagate = False  # kutuphane gibi: koke ULASMAZ; yalniz dogrudan takili handler gorur
        lg.info("blok %s", NOBETCILER[1])  # M28b sinifi
        return [_blok(NOBETCILER[1])]


class _UyariVeren(OcrEngine):
    def recognize(self, frame: Frame, preset: OcrPreset) -> list[TextBlock]:
        warnings.warn(NOBETCILER[0], stacklevel=2)
        return [_blok(NOBETCILER[0])]


@pytest.mark.parametrize(
    "sahte",
    [_StdoutaYazan, _StderreYazan, _FdYeYazan, _OzgunStderreYazan, _KokLoggeraYazan, _KutuphaneLoggerinaYazan, _UyariVeren],
    ids=["stdout", "stderr", "os.write(1)", "sys.__stderr__-tamponlu", "kok-logger-debug", "RapidOCR-logger-info-propagate-kapali", "warnings"],
)
def test_k7_pozitif_kontrol_kanal_olcusu_atesliyor(
    sahte: type[OcrEngine],
    kutuphane_logger_geri_al: None,
    capfd: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Ayni olcu, nobetciyi o kanala yazan sahte motorla DUSMELI (4.6/10)."""
    with pytest.raises(AssertionError):
        _k7_kanal_olcusu(sahte(), capfd, caplog)
    capfd.readouterr()
    caplog.clear()


def test_k7_negatif_kontrol_sessiz_sahte_motor_olcuden_gecer(
    kutuphane_logger_geri_al: None,
    capfd: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Yanlis pozitif yok: hicbir kanala yazmayan sozlesme sahtesi olcuden gecer."""
    from src.contracts.interfaces import FakeOcrEngine

    bloklar = _k7_kanal_olcusu(FakeOcrEngine([[_blok(NOBETCILER[0])]]), capfd, caplog)
    assert [b.text for b in bloklar] == [NOBETCILER[0]]


# -- AST (ikincil, erken uyari): dort yazma cagrisi + log yayimi 0 ------------

_YAZMA_CAGRILARI: tuple[str, ...] = ("print", "sys.stdout.write", "sys.stderr.write", "os.write")
_AKIS_ADLARI: tuple[str, ...] = ("sys.stdout", "sys.stderr", "sys.__stdout__", "sys.__stderr__")
_LOG_YAYIM_METOTLARI: frozenset[str] = frozenset(
    {"debug", "info", "warning", "warn", "error", "critical", "exception", "log"}
)


def _yazma_sayaci(agac: ast.AST) -> dict[str, int]:
    """Kaynakta `print`/`sys.stdout.write`/`sys.stderr.write`/`os.write` cagrisi,
    `sys.std*` akis erisimi ve `<nesne>.debug/info/.../log(...)` yayimi sayisi."""
    sayac: dict[str, int] = {ad: 0 for ad in (*_YAZMA_CAGRILARI, *_AKIS_ADLARI, "log-yayimi")}
    for d in ast.walk(agac):
        if isinstance(d, ast.Call):
            ad = ast.unparse(d.func)
            if ad in _YAZMA_CAGRILARI:
                sayac[ad] += 1
            if isinstance(d.func, ast.Attribute) and d.func.attr in _LOG_YAYIM_METOTLARI:
                sayac["log-yayimi"] += 1
        if isinstance(d, ast.Attribute) and ast.unparse(d) in _AKIS_ADLARI:
            sayac[ast.unparse(d)] += 1
    return sayac


def test_k7_ast_yazma_cagrisi_ve_log_yayimi_sifir() -> None:
    """`print`, `sys.stdout.write`, `sys.stderr.write`, `os.write` -> dordu de 0;
    `sys.std*` akisina erisim 0; hicbir `.debug/.info/.warning/...` yayimi yok
    (modulde `logging` yalniz `getLogger(...).setLevel` icin)."""
    sayac = _yazma_sayaci(_modul_agaci())
    assert sayac == {ad: 0 for ad in sayac}, sayac


def test_k7_ast_pozitif_kontrol_sayac_hepsini_gorur() -> None:
    """Sayacin kor olmadigi gosterilir: dort cagri + akis + yayim iceren parca -> hepsi > 0."""
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
    sayac = _yazma_sayaci(ast.parse(parca))
    assert sayac == {
        "print": 1, "sys.stdout.write": 1, "sys.stderr.write": 1, "os.write": 1,
        "sys.stdout": 1, "sys.stderr": 1, "sys.__stdout__": 1, "sys.__stderr__": 1,
        "log-yayimi": 2,
    }


# ===========================================================================
# K8 -- preset kabul edilir, v1'de motoru degistirmez
# ===========================================================================


def test_k8_dort_preset_ayni_cikti(tmp_path: Path) -> None:
    f = SahteFabrika(cikti((EGIK, "a", 0.4), (kutu(0, 0, 3, 3), "b", 0.9)))
    m = motor(tmp_path, f)
    sonuclar = [m.recognize(kare(), p) for p in OcrPreset]
    assert all(s == sonuclar[0] for s in sonuclar)
    assert all(p == f.params[0] for p in f.params)  # fabrika tek kez, preset params'a girmez
    assert f.calls == 1


def test_k8_olculmuyor_damgasi_docstringde() -> None:
    assert "[ÖLÇÜLMÜYOR]" in (rapid_engine.__doc__ or "")
    assert "[ÖLÇÜLMÜYOR]" in (RapidOcrEngine.recognize.__doc__ or "")


# ===========================================================================
# K10 -- tembel kurulum, tek ornek, kapatma
# ===========================================================================


def test_k10_tembel_tek_ornek_close_idempotent(tmp_path: Path) -> None:
    f = SahteFabrika()
    m = motor(tmp_path, f)
    assert f.calls == 0  # __init__ fabrikaya dokunmaz
    for _ in range(3):
        m.recognize(kare(), OcrPreset.DIALOGUE)
    assert f.calls == 1
    m.close()
    m.close()
    with pytest.raises(OcrError):
        m.recognize(kare(), OcrPreset.DIALOGUE)
    assert f.calls == 1


def test_k10_init_model_kontrolu_yapmaz(tmp_path: Path) -> None:
    """Tembellik: model yoksa bile YAPIM basarili, hata ilk `recognize`te."""
    m = RapidOcrEngine(language=OcrLanguage.JAPAN, model_dir=tmp_path, recognizer_factory=SahteFabrika())
    with pytest.raises(ModelMissingError):
        m.recognize(kare(), OcrPreset.DIALOGUE)


def test_k10_close_kurulmamis_motorda_da_sessiz(tmp_path: Path) -> None:
    f = SahteFabrika()
    m = motor(tmp_path, f)
    m.close()
    with pytest.raises(OcrError):
        m.recognize(kare(), OcrPreset.DIALOGUE)
    assert f.calls == 0


def test_k10_close_taniyiciyi_gercekten_birakir_weakref(tmp_path: Path) -> None:
    """Tur 2 (T2-2): `close()` sonrasi motor tanıyıcıya referans TUTMAZ.

    Gercek yolda tanıyıcı det+rec ONNX oturumlarini tasir; dil degisiminde eski
    motor bellekte kalmamali. Olcu: fabrikanin dondurdugu tanıyıcıya `weakref`;
    `close()` + `gc.collect()` sonrasi olu. Pozitif kontrol: `close()` ONCESI
    ayni weakref CANLI (motor tutuyor) -- yoksa olcu bos donerdi (4.6/10).
    """
    f = SahteFabrika(_nobetci_ciktisi())
    zayif: list[weakref.ref[Any]] = []

    def fabrika(params: dict[str, object]) -> Callable[[Any], Any]:
        t = f(params)  # taze kapanis; `f` onu TUTMAZ, yalniz motor tutar
        zayif.append(weakref.ref(t))
        return t

    model_dosyalari(tmp_path, OcrLanguage.JAPAN)
    m = RapidOcrEngine(language=OcrLanguage.JAPAN, model_dir=tmp_path, recognizer_factory=fabrika)
    m.recognize(kare(), OcrPreset.DIALOGUE)
    [ref] = zayif
    gc.collect()
    assert ref() is not None  # pozitif kontrol: kapatmadan once motor referansi tutuyor
    m.close()
    gc.collect()
    assert ref() is None  # birakildi
    with pytest.raises(OcrError):
        m.recognize(kare(), OcrPreset.DIALOGUE)
    assert f.calls == 1  # kapali motor fabrikayi YENIDEN cagirmaz
    m.close()
    gc.collect()
    assert ref() is None and f.calls == 1  # idempotent


def test_k10_kapali_motor_close_sonrasi_bozuk_karede_de_ocrerror(tmp_path: Path) -> None:
    """Sira (K10 -> K6 c): kapali motorda bozuk kare bile `OcrError` alir, fabrika 0."""
    f = SahteFabrika()
    m = motor(tmp_path, f)
    m.close()
    with pytest.raises(OcrError):
        m.recognize(kare(image=np.zeros((40, 100, 4), np.uint8)), OcrPreset.DIALOGUE)
    assert f.calls == 0


# ===========================================================================
# K11 -- model tablosu dil basina SABIT
# ===========================================================================


@pytest.mark.parametrize("dil", list(OcrLanguage))
def test_k11_dil_tablosu_alti_anahtar(tmp_path: Path, dil: OcrLanguage) -> None:
    f = SahteFabrika()
    motor(tmp_path, f, dil=dil).recognize(kare(), OcrPreset.DIALOGUE)
    det, rec = DIL_TABLOSU[dil]
    p = f.son
    assert p["Det.lang_type"] == det and p["Rec.lang_type"] == rec
    for bolum in ("Det", "Rec"):
        assert p[f"{bolum}.engine_type"] == "onnxruntime"
        assert p[f"{bolum}.model_type"] == "mobile"
        assert p[f"{bolum}.ocr_version"] == "PP-OCRv4"
    assert not any(k.startswith("Cls.") for k in p)  # cls yonetilmez (paketle geliyor)


def test_k11_params_anahtar_kumesi_sabit(tmp_path: Path) -> None:
    """Anahtar kumesi tam olarak bu; yanlis ic ice anahtar (KRT D4) sessizce kabul edilirdi."""
    f = SahteFabrika()
    motor(tmp_path, f).recognize(kare(), OcrPreset.DIALOGUE)
    assert set(f.son) == {
        "Global.text_score", "Global.use_cls", "Global.log_level",
        INTRA, INTER,
        "Det.engine_type", "Det.ocr_version", "Det.model_type", "Det.lang_type", "Det.model_path",
        "Rec.engine_type", "Rec.ocr_version", "Rec.model_type", "Rec.lang_type", "Rec.model_path",
    }


def test_k11_params_her_cagri_taze_kopya(tmp_path: Path) -> None:
    """Fabrikaya giden sozluk motorun ic durumu DEGIL; fabrika onu bozsa da ikinci motor temiz gorur."""
    f = SahteFabrika()
    m = motor(tmp_path, f)
    m.recognize(kare(), OcrPreset.DIALOGUE)
    p = m.parametreler()
    p["Global.text_score"] = 0.9
    assert m.parametreler()["Global.text_score"] == 0.0
