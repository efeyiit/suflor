"""T-009 kor tester -- K11 tablosu dort dilde (sahte fabrika, gercek model YOK).

Referanslar BAGIMSIZ kanaldan (PROTOKOL 4.6/8): T-009 packet K1 + olgular K4/K5
(KOREAN rec v5, dosya `korean_PP-OCRv5_rec_mobile.onnx`), T-006 packet K11
(lang_type tablosu), T-006 tester_A/B'nin kutuphane cozucusunden aldigi dosya
adlari (JP/ZH/EN v4). Motorun kendi `_DIL_TABLOSU`/`_MODEL_DOSYALARI`ndan
TURETILMEZ; ozel adlara yalniz yapisal denetimde (uzunluk/eslik) bakilir.

OCR metni basilmaz; `print` yok.
"""
from __future__ import annotations

import dataclasses
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np
import pytest

import conftest as tb_conftest
from src.contracts.errors import ModelMissingError
from src.contracts.models import Frame, OcrPreset, Rect
from src.ocr import rapid_engine
from src.ocr.rapid_engine import OcrLanguage, RapidOcrEngine, beklenen_model_dosyalari

# --- bagimsiz referanslar ----------------------------------------------------

DET_SURUMU = "PP-OCRv4"  # T-009 K1: Det her dilde v4 (det degismedi)
REC_SURUMU: dict[str, str] = {  # T-009 K1 / olgular K4-K5
    "japan": "PP-OCRv4",  # v5 YOK (ValueError)
    "korean": "PP-OCRv5",  # v4 nokta vermiyor
    "chinese": "PP-OCRv4",
    "english": "PP-OCRv4",  # v5 mumkun, kapsam disi
}
LANG_TYPE: dict[str, tuple[str, str]] = {  # T-006 packet K11 (Det.lang_type, Rec.lang_type)
    "japan": ("multi", "japan"),
    "korean": ("multi", "korean"),
    "chinese": ("ch", "ch"),
    "english": ("ch", "en"),
}
DOSYALAR: dict[str, tuple[str, str]] = {  # (det, rec)
    "japan": ("multi_PP-OCRv3_det_mobile.onnx", "japan_PP-OCRv4_rec_mobile.onnx"),
    "korean": ("multi_PP-OCRv3_det_mobile.onnx", "korean_PP-OCRv5_rec_mobile.onnx"),  # T-009
    "chinese": ("ch_PP-OCRv4_det_mobile.onnx", "ch_PP-OCRv4_rec_mobile.onnx"),
    "english": ("ch_PP-OCRv4_det_mobile.onnx", "en_PP-OCRv4_rec_mobile.onnx"),
}
KOREAN_V4_REC = "korean_PP-OCRv4_rec_mobile.onnx"  # T-009 oncesi; artik ARANMAMALI
DILLER = ["japan", "korean", "chinese", "english"]


# --- sahte kutuphane ---------------------------------------------------------


@dataclasses.dataclass
class Cikti:
    boxes: Any = None
    txts: Any = None
    scores: Any = None


def dolu(*metin: str) -> Cikti:
    n = len(metin)
    kutular = np.asarray(
        [[[10 * i, 0], [10 * i + 8, 0], [10 * i + 8, 5], [10 * i, 5]] for i in range(n)],
        dtype=np.float32,
    )
    return Cikti(boxes=kutular, txts=tuple(metin), scores=tuple(0.9 for _ in metin))


class Fabrika:
    def __init__(self, sonuc: Cikti | None = None) -> None:
        self.sonuc = sonuc if sonuc is not None else Cikti()
        self.params: list[dict[str, object]] = []
        self.calls = 0

    def __call__(self, params: dict[str, object]) -> Any:
        self.calls += 1
        self.params.append(dict(params))
        return lambda img: self.sonuc

    @property
    def son(self) -> dict[str, object]:
        return self.params[-1]


def kare() -> Frame:
    return Frame(image=np.zeros((20, 60, 3), np.uint8), rect=Rect(0, 0, 60, 20), captured_at=0.0, seq=0)


def dosyalari_koy(dizin: Path, dil: str) -> tuple[Path, Path]:
    det, rec = DOSYALAR[dil]
    (dizin / det).write_bytes(b"")
    (dizin / rec).write_bytes(b"")
    return dizin / det, dizin / rec


def motor(dizin: Path, f: Fabrika, dil: str, **ek: Any) -> RapidOcrEngine:
    dosyalari_koy(dizin, dil)
    ek.setdefault("allow_download", False)
    ek.setdefault("model_dir", dizin)
    return RapidOcrEngine(language=OcrLanguage(dil), recognizer_factory=f, **ek)


# ===========================================================================
# T0 -- bariyer pozitif kontrolu (4.6/10)
# ===========================================================================


def test_t0_bariyer_atesliyor() -> None:
    once = tb_conftest.BARIYER.ates
    with pytest.raises(RuntimeError, match="K1 bariyeri"):
        import rapidocr  # noqa: F401
    with pytest.raises(RuntimeError, match="K1 bariyeri"):
        import onnxruntime  # type: ignore[import-untyped]  # noqa: F401
    assert tb_conftest.BARIYER.ates >= once  # sefin bariyeri once ateslerse sayac artmayabilir
    assert not any(k.split(".", 1)[0] in tb_conftest.YASAK_KOKLER for k in sys.modules)


# ===========================================================================
# T1 -- surumler: Det hep v4; Rec yalniz KOREAN v5 (dort dil, acik yol)
# ===========================================================================


@pytest.mark.parametrize("dil", DILLER)
def test_t1_det_v4_rec_dile_ozel_acik_yol(tmp_path: Path, dil: str) -> None:
    f = Fabrika()
    motor(tmp_path, f, dil).recognize(kare(), OcrPreset.DIALOGUE)
    p = f.son
    assert p["Det.ocr_version"] == DET_SURUMU, dil
    assert p["Rec.ocr_version"] == REC_SURUMU[dil], dil
    assert isinstance(p["Det.ocr_version"], str) and isinstance(p["Rec.ocr_version"], str)
    det, rec = LANG_TYPE[dil]
    assert p["Det.lang_type"] == det and p["Rec.lang_type"] == rec
    for bolum in ("Det", "Rec"):
        assert p[f"{bolum}.engine_type"] == "onnxruntime"
        assert p[f"{bolum}.model_type"] == "mobile"


@pytest.mark.parametrize("dil", DILLER)
def test_t1_det_v4_rec_dile_ozel_indirme_yolu(tmp_path: Path, dil: str) -> None:
    """`allow_download=True`: `Rec.ocr_version` dosyayi SECEN yol -- KOREAN v5 burada da tasinmali."""
    f = Fabrika()
    m = RapidOcrEngine(language=OcrLanguage(dil), allow_download=True, model_dir=tmp_path, recognizer_factory=f)
    m.recognize(kare(), OcrPreset.DIALOGUE)
    p = f.son
    assert p["Det.ocr_version"] == DET_SURUMU
    assert p["Rec.ocr_version"] == REC_SURUMU[dil]
    assert "Det.model_path" not in p and "Rec.model_path" not in p
    assert p["Global.model_root_dir"] == tmp_path


def test_t1_v5_kumesi_tam_olarak_korean(tmp_path: Path) -> None:
    v5_rec = {d for d in DILLER if motor_params(tmp_path, d)["Rec.ocr_version"] == "PP-OCRv5"}
    v5_det = {d for d in DILLER if motor_params(tmp_path, d)["Det.ocr_version"] == "PP-OCRv5"}
    assert v5_rec == {"korean"}
    assert v5_det == set()


def motor_params(tmp_path: Path, dil: str) -> dict[str, object]:
    d = tmp_path / dil
    d.mkdir(exist_ok=True)
    f = Fabrika()
    motor(d, f, dil).recognize(kare(), OcrPreset.DIALOGUE)
    assert f.calls == 1
    return f.son


def test_t1_iki_nokta_korean_japan_ayrisir(tmp_path: Path) -> None:
    """4.6/7: ayni sahte fabrika, iki dil -- yalniz `Rec.ocr_version` ve dosya adi farkli."""
    kr = motor_params(tmp_path, "korean")
    jp = motor_params(tmp_path, "japan")
    assert kr["Rec.ocr_version"] != jp["Rec.ocr_version"]
    assert kr["Det.ocr_version"] == jp["Det.ocr_version"] == DET_SURUMU
    assert kr["Det.lang_type"] == jp["Det.lang_type"] == "multi"
    assert Path(str(kr["Det.model_path"])).name == Path(str(jp["Det.model_path"])).name
    assert Path(str(kr["Rec.model_path"])).name != Path(str(jp["Rec.model_path"])).name


# ===========================================================================
# T2 -- dosya adlari dort dilde (`beklenen_model_dosyalari` + `*.model_path`)
# ===========================================================================


@pytest.mark.parametrize("dil", DILLER)
def test_t2_beklenen_dosya_adlari(dil: str) -> None:
    assert beklenen_model_dosyalari(OcrLanguage(dil)) == DOSYALAR[dil]
    assert beklenen_model_dosyalari(dil) == DOSYALAR[dil]  # type: ignore[arg-type]  # deger de kabul


@pytest.mark.parametrize("dil", DILLER)
def test_t2_model_path_tam_yol(tmp_path: Path, dil: str) -> None:
    f = Fabrika()
    det_yol, rec_yol = dosyalari_koy(tmp_path, dil)
    RapidOcrEngine(language=OcrLanguage(dil), allow_download=False, model_dir=tmp_path, recognizer_factory=f).recognize(
        kare(), OcrPreset.DIALOGUE
    )
    assert f.son["Det.model_path"] == det_yol and f.son["Rec.model_path"] == rec_yol
    assert isinstance(f.son["Det.model_path"], Path) and isinstance(f.son["Rec.model_path"], Path)


def test_t2_rec_dosya_adi_surum_etiketiyle_tutarli() -> None:
    """Dosya adindaki surum ile `Rec.ocr_version` etiketi dort dilde AYNI (iki tablo tutarli)."""
    for dil in DILLER:
        _det, rec = beklenen_model_dosyalari(OcrLanguage(dil))
        etiket = REC_SURUMU[dil]  # "PP-OCRv4" / "PP-OCRv5"
        assert f"_{etiket}_rec_" in rec, (dil, rec, etiket)
        assert rec.startswith(LANG_TYPE[dil][1] + "_"), (dil, rec)


def test_t2_korean_v4_adi_hicbir_yerde_aranmaz() -> None:
    for dil in DILLER:
        assert KOREAN_V4_REC not in beklenen_model_dosyalari(OcrLanguage(dil))


def test_t2_tablolar_yapisal_olarak_tam() -> None:
    """Her dil iki tabloda TAM BIR kez; `_DIL_TABLOSU` satirlari 4'lu, `_MODEL_DOSYALARI` 3'lu."""
    dt = rapid_engine._DIL_TABLOSU
    md = rapid_engine._MODEL_DOSYALARI
    assert [s[0] for s in dt] == list(OcrLanguage) and [s[0] for s in md] == list(OcrLanguage)
    assert all(len(s) == 4 for s in dt) and all(len(s) == 3 for s in md)
    assert all(isinstance(x, str) for s in dt for x in s[1:])
    assert all(isinstance(x, str) and x.endswith(".onnx") for s in md for x in s[1:])


# ===========================================================================
# T3 -- allow_download=False + bos dizin: dort dilde DOGRU dosya adi mesajda
# ===========================================================================


@pytest.mark.parametrize("dil", DILLER)
def test_t3_bos_dizin_modelmissing_dogru_adlar(tmp_path: Path, dil: str) -> None:
    f = Fabrika()
    m = RapidOcrEngine(language=OcrLanguage(dil), allow_download=False, model_dir=tmp_path, recognizer_factory=f)
    with pytest.raises(ModelMissingError) as ei:
        m.recognize(kare(), OcrPreset.DIALOGUE)
    mesaj = str(ei.value)
    det, rec = DOSYALAR[dil]
    assert det in mesaj and rec in mesaj, (dil, mesaj)
    assert KOREAN_V4_REC not in mesaj
    assert str(tmp_path) in mesaj
    assert f.calls == 0
    assert ei.value.__cause__ is None
    # baska dilin rec adi mesaja sizmaz
    for d2 in DILLER:
        if d2 != dil:
            assert DOSYALAR[d2][1] not in mesaj, (dil, d2)


@pytest.mark.parametrize("dil", DILLER)
def test_t3_yalniz_rec_eksik_mesajda_yalniz_rec(tmp_path: Path, dil: str) -> None:
    det, rec = DOSYALAR[dil]
    (tmp_path / det).write_bytes(b"")
    f = Fabrika()
    m = RapidOcrEngine(language=OcrLanguage(dil), allow_download=False, model_dir=tmp_path, recognizer_factory=f)
    with pytest.raises(ModelMissingError) as ei:
        m.recognize(kare(), OcrPreset.DIALOGUE)
    assert rec in str(ei.value) and det not in str(ei.value)
    assert f.calls == 0


@pytest.mark.parametrize("dil", DILLER)
def test_t3_yalniz_det_eksik_mesajda_yalniz_det(tmp_path: Path, dil: str) -> None:
    det, rec = DOSYALAR[dil]
    (tmp_path / rec).write_bytes(b"")
    f = Fabrika()
    m = RapidOcrEngine(language=OcrLanguage(dil), allow_download=False, model_dir=tmp_path, recognizer_factory=f)
    with pytest.raises(ModelMissingError) as ei:
        m.recognize(kare(), OcrPreset.DIALOGUE)
    assert det in str(ei.value) and rec not in str(ei.value)


def test_t3_korean_yalniz_v4_dosyasi_dusulmez(tmp_path: Path) -> None:
    """det + eski v4 rec var, v5 yok -> ModelMissingError; v4'e sessizce dusulmez; fabrika cagrilmaz."""
    det, rec_v5 = DOSYALAR["korean"]
    (tmp_path / det).write_bytes(b"")
    (tmp_path / KOREAN_V4_REC).write_bytes(b"")
    f = Fabrika()
    m = RapidOcrEngine(language=OcrLanguage.KOREAN, allow_download=False, model_dir=tmp_path, recognizer_factory=f)
    with pytest.raises(ModelMissingError) as ei:
        m.recognize(kare(), OcrPreset.DIALOGUE)
    assert rec_v5 in str(ei.value) and det not in str(ei.value)
    assert f.calls == 0
    # dosya sonradan gelirse AYNI motor kurulur (K6 b / K10)
    (tmp_path / rec_v5).write_bytes(b"")
    m.recognize(kare(), OcrPreset.DIALOGUE)
    assert f.calls == 1 and f.son["Rec.model_path"] == tmp_path / rec_v5
    assert f.son["Rec.ocr_version"] == "PP-OCRv5"


def test_t3_korean_v4_ve_v5_ikisi_de_varsa_v5_secilir(tmp_path: Path) -> None:
    """Gercek makine durumu: dizinde v4 VE v5 dosyasi birlikte -> `Rec.model_path` v5."""
    det, rec_v5 = dosyalari_koy(tmp_path, "korean")
    (tmp_path / KOREAN_V4_REC).write_bytes(b"")
    f = Fabrika()
    RapidOcrEngine(language=OcrLanguage.KOREAN, allow_download=False, model_dir=tmp_path, recognizer_factory=f).recognize(
        kare(), OcrPreset.DIALOGUE
    )
    assert f.son["Rec.model_path"] == rec_v5
    assert Path(str(f.son["Rec.model_path"])).name != KOREAN_V4_REC


def test_t3_parametreler_fabrikasiz_ayni_bilgiyi_verir(tmp_path: Path) -> None:
    """`parametreler()` public: bos dizinde dort dil icin ModelMissingError, adlar dogru."""
    for dil in DILLER:
        m = RapidOcrEngine(language=OcrLanguage(dil), allow_download=False, model_dir=tmp_path)
        with pytest.raises(ModelMissingError) as ei:
            m.parametreler()
        assert DOSYALAR[dil][1] in str(ei.value)


def test_t3_init_dosya_sistemine_dokunmaz(tmp_path: Path) -> None:
    """K10: bos dizin + KOREAN -- yapim hata vermez; hata ilk recognize'da."""
    m = RapidOcrEngine(language=OcrLanguage.KOREAN, allow_download=False, model_dir=tmp_path)
    assert m.language is OcrLanguage.KOREAN
    with pytest.raises(ModelMissingError):
        m.recognize(kare(), OcrPreset.DIALOGUE)


# ===========================================================================
# T4 -- belge: docstring K11 tablosu kodla ayni seyi soyluyor (4.6/2)
# ===========================================================================


def test_t4_docstring_k11_tablosu_kodla_uyumlu() -> None:
    doc = rapid_engine.__doc__ or ""
    k11 = doc[doc.index("## K11") :]
    k11 = k11[: k11.index("Windows tuzaklari")] if "Windows tuzaklari" in k11 else k11
    for dil in DILLER:
        det, rec = LANG_TYPE[dil]
        satir = next(
            s for s in k11.splitlines() if s.strip().startswith(dil.upper() + " ") and "Det.lang_type" in s
        )
        assert f'Det.lang_type="{det}"' in satir and f'Rec.lang_type="{rec}"' in satir
        assert f'Rec.ocr_version="{REC_SURUMU[dil]}"' in satir, satir
    assert DOSYALAR["korean"][1] in k11
    assert KOREAN_V4_REC not in k11


def test_t4_kaynakta_v4_korean_adi_yok() -> None:
    kaynak = Path(rapid_engine.__file__).read_text(encoding="utf-8")
    assert KOREAN_V4_REC not in kaynak


# ===========================================================================
# T5 -- sahte fabrikayla tam kosum kutuphaneye dokunmaz (dort dil, iki yol)
# ===========================================================================


def test_t5_dort_dil_iki_yol_kutuphane_yuklenmez(tmp_path: Path) -> None:
    for dil in DILLER:
        d = tmp_path / dil
        d.mkdir()
        motor(d, Fabrika(dolu("a")), dil).recognize(kare(), OcrPreset.DIALOGUE)
        RapidOcrEngine(language=OcrLanguage(dil), allow_download=True, recognizer_factory=Fabrika()).recognize(
            kare(), OcrPreset.DIALOGUE
        )
    assert not any(k.split(".", 1)[0] in tb_conftest.YASAK_KOKLER for k in sys.modules)
