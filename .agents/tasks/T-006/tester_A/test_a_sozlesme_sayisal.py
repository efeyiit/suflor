"""T-006 tester-A — mercek A: sözleşme uyumu ve sayısal doğruluk (tur 1).

Kör test: yalnız `packet.md`, sözleşme (`src/contracts/*`) ve kodun kendisi
okundu; referanslar (dil tablosu, anahtar adları, beklenen kutular) BURADA
sabit — motorun tablosundan TÜRETİLMEZ (§4.6/8).

Saldırı noktaları: A1 K4 kutu matematiği · A2 kaydırma/frame alanları ·
A3 K5 süzülmeme · A4 K6 hata taksonomisi + `__cause__` · A5 K3 aralık ve
K11 tablo. A6 (gerçek model) ayrı süreçte: `a6_gercek_model.py`.

OCR metni hiçbir yere basılmaz; `print` yok.
"""
from __future__ import annotations

import dataclasses
import enum
import json
import math
import os
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from src.contracts.errors import (
    CaptureError,
    ContractViolation,
    ModelMissingError,
    OcrError,
)
from src.contracts.models import Frame, OcrPreset, Rect, TextBlock
from src.ocr.rapid_engine import OcrLanguage, RapidOcrEngine

# --- BAĞIMSIZ referanslar (packet.md K11 tablosu + K6 dosya adları) ---------

INTRA = "EngineConfig.onnxruntime.intra_op_num_threads"
INTER = "EngineConfig.onnxruntime.inter_op_num_threads"

K11_TABLO: dict[str, tuple[str, str]] = {
    "japan": ("multi", "japan"),
    "korean": ("multi", "korean"),
    "chinese": ("ch", "ch"),
    "english": ("ch", "en"),
}
ORTAK = {"engine_type": "onnxruntime", "model_type": "mobile", "ocr_version": "PP-OCRv4"}

MODEL_ADLARI: dict[str, tuple[str, str]] = {
    "japan": ("multi_PP-OCRv3_det_mobile.onnx", "japan_PP-OCRv4_rec_mobile.onnx"),
    "korean": ("multi_PP-OCRv3_det_mobile.onnx", "korean_PP-OCRv4_rec_mobile.onnx"),
    "chinese": ("ch_PP-OCRv4_det_mobile.onnx", "ch_PP-OCRv4_rec_mobile.onnx"),
    "english": ("ch_PP-OCRv4_det_mobile.onnx", "en_PP-OCRv4_rec_mobile.onnx"),
}


# --- sahte çıktı / fabrika ---------------------------------------------------


class Cikti:
    """Kütüphane çıktısının yüzü: üç salt-okunur alan (Y4: hepsi None olabilir)."""

    def __init__(self, boxes: Any = None, txts: Any = None, scores: Any = None) -> None:
        self._b, self._t, self._s = boxes, txts, scores

    @property
    def boxes(self) -> Any:
        return self._b

    @property
    def txts(self) -> Any:
        return self._t

    @property
    def scores(self) -> Any:
        return self._s


class Fabrika:
    """`params`ı kaydeder, çağrı sayar; `tani` verilmezse sabit `sonuc` döndürür."""

    def __init__(
        self,
        sonuc: Any = None,
        tani: Callable[[Any], Any] | None = None,
        kurulum_hatasi: BaseException | None = None,
    ) -> None:
        self.sonuc = sonuc if sonuc is not None else Cikti()
        self.tani = tani
        self.kurulum_hatasi = kurulum_hatasi
        self.calls = 0
        self.params: list[dict[str, object]] = []
        self.goruntuler: list[Any] = []

    def __call__(self, params: dict[str, object]) -> Callable[[Any], Any]:
        self.calls += 1
        self.params.append(dict(params))
        if self.kurulum_hatasi is not None:
            raise self.kurulum_hatasi
        if self.tani is not None:
            return self.tani

        def _t(img: Any) -> Any:
            self.goruntuler.append(img)
            return self.sonuc

        return _t

    @property
    def son(self) -> dict[str, object]:
        return self.params[-1]


def dortgen(x0: float, y0: float, x1: float, y1: float) -> list[list[float]]:
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def cikti(*uclu: tuple[Any, str, Any], dtype: Any = np.float32) -> Cikti:
    boxes = np.asarray([u[0] for u in uclu], dtype=dtype)
    return Cikti(boxes=boxes, txts=tuple(u[1] for u in uclu), scores=tuple(u[2] for u in uclu))


def kare(image: Any = None, rect: Rect | None = None, h: int = 40, w: int = 100) -> Frame:
    if image is None:
        image = np.zeros((h, w, 3), dtype=np.uint8)
    if rect is None:
        rect = Rect(0, 0, w, h)
    return Frame(image=image, rect=rect, captured_at=0.0, seq=0)


def modeller(dizin: Path, dil: str) -> tuple[Path, Path]:
    det, rec = MODEL_ADLARI[dil]
    (dizin / det).write_bytes(b"")
    (dizin / rec).write_bytes(b"")
    return dizin / det, dizin / rec


def motor(tmp_path: Path, f: Fabrika, dil: str = "japan", **ek: Any) -> RapidOcrEngine:
    modeller(tmp_path, dil)
    ek.setdefault("allow_download", False)
    ek.setdefault("model_dir", tmp_path)
    return RapidOcrEngine(language=OcrLanguage(dil), recognizer_factory=f, **ek)


def tek(tmp_path: Path, c: Cikti, rect: Rect | None = None) -> list[TextBlock]:
    return motor(tmp_path, Fabrika(c)).recognize(kare(rect=rect), OcrPreset.DIALOGUE)


def duz_int(r: Rect) -> bool:
    return all(type(getattr(r, a)) is int for a in ("x", "y", "w", "h", "monitor_index"))


# ===========================================================================
# A0 — bariyer pozitif kontrolü (bu dizin tek başına koşulduğunda da)
# ===========================================================================


def test_a0_bariyer_atesliyor() -> None:
    with pytest.raises(RuntimeError):
        import rapidocr  # noqa: F401
    with pytest.raises(RuntimeError):
        import onnxruntime  # noqa: F401
    assert not any(k.split(".")[0] in ("rapidocr", "onnxruntime") for k in sys.modules)


def test_a0_motor_kosumu_kutuphane_yuklemez(tmp_path: Path) -> None:
    tek(tmp_path, cikti((dortgen(0, 0, 4, 4), "x", 0.5)))
    assert not any(k.split(".")[0] in ("rapidocr", "onnxruntime") for k in sys.modules)


# ===========================================================================
# A1 — K4 kutu matematiği
# ===========================================================================


def test_a1_tam_sayi_koseler_fazla_piksel_yok(tmp_path: Path) -> None:
    [b] = tek(tmp_path, cikti((dortgen(10, 20, 50, 40), "a", 0.9)))
    assert (b.bbox.x, b.bbox.y, b.bbox.w, b.bbox.h) == (10, 20, 40, 20)
    assert duz_int(b.bbox)


def test_a1_yarim_piksel_koseler_floor_ceil(tmp_path: Path) -> None:
    # min 10.5/20.5 -> floor 10/20; max 50.5/40.5 -> ceil 51/41; w=41, h=21
    [b] = tek(tmp_path, cikti((dortgen(10.5, 20.5, 50.5, 40.5), "a", 0.9)))
    assert (b.bbox.x, b.bbox.y, b.bbox.w, b.bbox.h) == (10, 20, 41, 21)
    assert duz_int(b.bbox)


def test_a1_negatif_koseler_floor_negatife_dogru(tmp_path: Path) -> None:
    # min -5.5/-3.5 -> floor -6/-4 (int() -5/-3 OLMAZ); max 10.5/4.5 -> ceil 11/5
    [b] = tek(tmp_path, cikti((dortgen(-5.5, -3.5, 10.5, 4.5), "a", 0.9)))
    assert (b.bbox.x, b.bbox.y, b.bbox.w, b.bbox.h) == (-6, -4, 17, 9)
    assert duz_int(b.bbox)


def test_a1_eksi_yarim_ile_sifir_sinirinda(tmp_path: Path) -> None:
    # min_x=-0.5 -> floor -1; max_x=0.5 -> ceil 1; w=2. min_y=-0.0 -> 0.
    [b] = tek(tmp_path, cikti(([[-0.5, -0.0], [0.5, -0.0], [0.5, 0.25], [-0.5, 0.25]], "a", 0.9)))
    assert (b.bbox.x, b.bbox.y, b.bbox.w, b.bbox.h) == (-1, 0, 2, 1)
    assert duz_int(b.bbox)


def test_a1_tek_noktali_cokgen_tam_sayi_w0_h0(tmp_path: Path) -> None:
    [b] = tek(tmp_path, cikti(([[7, 3]], "a", 0.9)))
    assert (b.bbox.x, b.bbox.y, b.bbox.w, b.bbox.h) == (7, 3, 0, 0)
    assert duz_int(b.bbox)


def test_a1_tek_noktali_cokgen_kesirli_w1_h1(tmp_path: Path) -> None:
    [b] = tek(tmp_path, cikti(([[7.2, 3.9]], "a", 0.9)))
    assert (b.bbox.x, b.bbox.y, b.bbox.w, b.bbox.h) == (7, 3, 1, 1)


def test_a1_dejenere_yatay_cizgi_h0(tmp_path: Path) -> None:
    [b] = tek(tmp_path, cikti(([[10, 20], [50, 20], [50, 20], [10, 20]], "a", 0.9)))
    assert (b.bbox.w, b.bbox.h) == (40, 0) and duz_int(b.bbox)


def test_a1_kose_sirasi_ters_ayni_kutu(tmp_path: Path) -> None:
    saat = [[10.6, 20.6], [51.2, 18.9], [51.2, 40.1], [11.1, 42.3]]
    ters = list(reversed(saat))
    karisik = [saat[2], saat[0], saat[3], saat[1]]
    b0, b1, b2 = (tek(tmp_path, cikti((p, "a", 0.9)))[0] for p in (saat, ters, karisik))
    assert b0.bbox == b1.bbox == b2.bbox == Rect(10, 18, 42, 25)


def test_a1_float32_hassasiyeti_tam_sayiya_yuvarlanan_deger(tmp_path: Path) -> None:
    """float32(2600.0000001) == 2600.0 tam; ceil/floor fazla piksel VERMEMELİ."""
    v = np.float32(2600.0000001)
    assert float(v) == 2600.0  # ön koşul: float32 bunu 2600.0'a yuvarlar
    [b] = tek(tmp_path, cikti(([[v, v], [v + 10, v], [v + 10, v + 5], [v, v + 5]], "a", 0.9)))
    assert (b.bbox.x, b.bbox.y, b.bbox.w, b.bbox.h) == (2600, 2600, 10, 5)
    assert duz_int(b.bbox)


def test_a1_float32_hassasiyeti_kesirli_deger_ceil(tmp_path: Path) -> None:
    """float32(1199.9999) = 1199.99987... -> ceil 1200; float32(100.1) -> floor 100."""
    lo, hi = np.float32(100.1), np.float32(1199.9999)
    [b] = tek(tmp_path, cikti(([[lo, lo], [hi, lo], [hi, hi], [lo, hi]], "a", 0.9)))
    assert (b.bbox.x, b.bbox.y, b.bbox.w, b.bbox.h) == (100, 100, 1100, 1100)


@pytest.mark.parametrize("dtype", [np.float32, np.float64, np.int64, np.int32, np.float16])
def test_a1_farkli_dtype_cokgen_hep_duz_int(tmp_path: Path, dtype: Any) -> None:
    [b] = tek(tmp_path, cikti((dortgen(10, 20, 50, 40), "a", 0.9), dtype=dtype))
    assert (b.bbox.x, b.bbox.y, b.bbox.w, b.bbox.h) == (10, 20, 40, 20)
    assert duz_int(b.bbox)
    json.dumps(dataclasses.asdict(b.bbox))  # np.int64 sızıntısı burada da görünürdü


def test_a1_liste_bicimli_boxes_de_kabul(tmp_path: Path) -> None:
    c = Cikti(boxes=[dortgen(1.5, 2.5, 3.5, 4.5)], txts=("a",), scores=(0.5,))
    [b] = tek(tmp_path, c)
    assert (b.bbox.x, b.bbox.y, b.bbox.w, b.bbox.h) == (1, 2, 3, 3) and duz_int(b.bbox)


def test_a1_buyuk_koordinat_json(tmp_path: Path) -> None:
    [b] = tek(tmp_path, cikti((dortgen(2559.7, 1439.2, 2560.0, 1440.0), "a", 0.9)),
              rect=Rect(-2560, 0, 2560, 1440, monitor_index=0))
    assert (b.bbox.x, b.bbox.y, b.bbox.w, b.bbox.h) == (2559 - 2560, 1439, 1, 1)
    assert duz_int(b.bbox)
    json.dumps(dataclasses.asdict(b.bbox))


# ===========================================================================
# A2 — kaydırma ve frame alanları
# ===========================================================================


@pytest.mark.parametrize(
    "rect",
    [
        Rect(-2600, -50, 100, 40, monitor_index=0),
        Rect(-1, -1, 100, 40, monitor_index=-1, dpi_scale=1.25),
        Rect(2560, 0, 100, 40, monitor_index=1, dpi_scale=2.0),
        Rect(0, 0, 100, 40, monitor_index=-1, dpi_scale=1.0),
    ],
)
def test_a2_kaydirma_ve_alanlar_aynen(tmp_path: Path, rect: Rect) -> None:
    [b] = tek(tmp_path, cikti((dortgen(10.6, 18.9, 51.2, 42.3), "a", 0.9)), rect=rect)
    assert (b.bbox.x, b.bbox.y, b.bbox.w, b.bbox.h) == (10 + rect.x, 18 + rect.y, 42, 25)  # 42.3->43, 18.9->18
    assert b.bbox.monitor_index == rect.monitor_index and type(b.bbox.monitor_index) is int
    assert b.bbox.dpi_scale == rect.dpi_scale and type(b.bbox.dpi_scale) is float
    assert duz_int(b.bbox)
    json.dumps(dataclasses.asdict(b.bbox))


def test_a2_monitor_index_eksi_bir_birlesim_aynen(tmp_path: Path) -> None:
    """`CaptureService._monitor_indeksi` -1 üretebilir (birleşim); motor sıfıra çekmemeli."""
    [b] = tek(tmp_path, cikti((dortgen(0, 0, 4, 4), "a", 0.9)), rect=Rect(5, 5, 100, 40, monitor_index=-1))
    assert b.bbox.monitor_index == -1 and type(b.bbox.monitor_index) is int


def test_a2_iki_nokta_farki_w_h_degismez(tmp_path: Path) -> None:
    f = Fabrika(cikti((dortgen(10.6, 18.9, 51.2, 42.3), "a", 0.9)))
    m = motor(tmp_path, f)
    [b0] = m.recognize(kare(rect=Rect(0, 0, 100, 40)), OcrPreset.DIALOGUE)
    [b1] = m.recognize(kare(rect=Rect(-2600, -50, 100, 40)), OcrPreset.DIALOGUE)
    [b2] = m.recognize(kare(rect=Rect(2560, 1400, 100, 40)), OcrPreset.DIALOGUE)
    assert (b1.bbox.x - b0.bbox.x, b1.bbox.y - b0.bbox.y) == (-2600, -50)
    assert (b2.bbox.x - b0.bbox.x, b2.bbox.y - b0.bbox.y) == (2560, 1400)
    assert (b0.bbox.w, b0.bbox.h) == (b1.bbox.w, b1.bbox.h) == (b2.bbox.w, b2.bbox.h)


@pytest.mark.parametrize(
    "rect",
    [
        Rect(np.int64(0), 0, 100, 40),  # type: ignore[arg-type]
        Rect(0, np.int64(0), 100, 40),  # type: ignore[arg-type]
        Rect(0, 0, 100, 40, monitor_index=np.int64(0)),  # type: ignore[arg-type]
        Rect(np.uint16(5), np.uint16(5), 100, 40),  # type: ignore[arg-type]
        Rect(True, 0, 100, 40),  # type: ignore[arg-type]
    ],
)
def test_a2_rect_numpy_veya_bool_alan_contractviolation_motor_cagrilmaz(tmp_path: Path, rect: Rect) -> None:
    f = Fabrika(cikti((dortgen(0, 0, 4, 4), "a", 0.9)))
    m = motor(tmp_path, f)
    with pytest.raises(ContractViolation) as ei:
        m.recognize(kare(rect=rect), OcrPreset.DIALOGUE)
    assert f.calls == 0 and ei.value.__cause__ is None


def test_a2_rect_w_h_numpy_denetlenmez_bbox_yine_duz(tmp_path: Path) -> None:
    """`rect.w/h` bbox'a girmez; numpy olsalar da sonuç düz int (gözlem, sözleşme değil)."""
    rect = Rect(0, 0, np.int64(100), np.int64(40))  # type: ignore[arg-type]
    [b] = tek(tmp_path, cikti((dortgen(1, 2, 3, 4), "a", 0.9)), rect=rect)
    assert duz_int(b.bbox)
    json.dumps(dataclasses.asdict(b.bbox))


def test_a2_rect_dpi_scale_np_float32_sizar_json_duser(tmp_path: Path) -> None:
    """GÖZLEM (bulgu D-A2): `rect.x/y/monitor_index` numpy ise ContractViolation ama
    `dpi_scale` denetlenmiyor -> np.float32 bbox'a AYNEN sızar, `json.dumps` düşer.
    CaptureService dpi_scale'i `float()` ile düzleştirdiği için üretimde erişilemez;
    bilinen boşluk olarak kayda geçer. Bu test MEVCUT davranışı sabitler."""
    rect = Rect(0, 0, 100, 40, dpi_scale=np.float32(1.5))  # type: ignore[arg-type]
    [b] = tek(tmp_path, cikti((dortgen(1, 2, 3, 4), "a", 0.9)), rect=rect)
    assert type(b.bbox.dpi_scale) is np.float32
    with pytest.raises(TypeError):
        json.dumps(dataclasses.asdict(b.bbox))


# ===========================================================================
# A3 — K5 süzülmeme: hiçbir blok kaybolmaz, hiçbir yolda float dışı tip yok
# ===========================================================================

PUANLAR: list[Any] = [
    0.0, float("nan"), -0.1, 1.5, 0.5, 1.0, 0.123456789,
    np.float32(0.3), np.float64(0.7), np.int64(1), 0, 1, np.float16(0.25),
]


def test_a3_puanlar_suzulmez_hepsi_float(tmp_path: Path) -> None:
    uclu = [(dortgen(0, i * 10, 5, i * 10 + 5), f"m{i}", p) for i, p in enumerate(PUANLAR)]
    bl = tek(tmp_path, cikti(*uclu))
    assert len(bl) == len(PUANLAR)
    assert [b.text for b in bl] == [f"m{i}" for i in range(len(PUANLAR))]
    for b, p in zip(bl, PUANLAR, strict=True):
        assert type(b.confidence) is float
        if isinstance(p, float) and math.isnan(p):
            assert math.isnan(b.confidence)
        else:
            assert b.confidence == float(p)  # yuvarlama YOK (0.123456789 aynen)


def test_a3_yuksek_hassasiyetli_puan_aynen(tmp_path: Path) -> None:
    [b] = tek(tmp_path, cikti((dortgen(0, 0, 5, 5), "a", 0.987654321012345)))
    assert b.confidence == 0.987654321012345


def test_a3_metin_degismez_bos_ve_bosluk(tmp_path: Path) -> None:
    metinler = ["", " ", "\t\n", "  iki  ", "a b", "ａｂ　"]
    uclu = [(dortgen(0, i * 10, 5, i * 10 + 5), t, 0.5) for i, t in enumerate(metinler)]
    bl = tek(tmp_path, cikti(*uclu))
    assert [b.text for b in bl] == metinler
    assert all(type(b.text) is str for b in bl)


def test_a3_elli_blok_sifir_puanlarla_hepsi_gecer(tmp_path: Path) -> None:
    puan = [0.0 if i % 3 == 0 else i / 50 for i in range(50)]
    uclu = [(dortgen(0, i, 5, i + 1), "x", p) for i, p in enumerate(puan)]
    bl = tek(tmp_path, cikti(*uclu))
    assert [b.confidence for b in bl] == puan and len(bl) == 50


def test_a3_scores_ndarray_float32_duz_float(tmp_path: Path) -> None:
    c = Cikti(
        boxes=np.asarray([dortgen(0, 0, 5, 5), dortgen(0, 10, 5, 15)], np.float32),
        txts=("a", "b"),
        scores=np.asarray([0.25, 0.0], np.float32),
    )
    bl = tek(tmp_path, c)
    assert [type(b.confidence) for b in bl] == [float, float]
    assert bl[0].confidence == 0.25 and bl[1].confidence == 0.0


def test_a3_txts_ndarray_str_gozlem(tmp_path: Path) -> None:
    """GÖZLEM: `txts` numpy `<U` dizisi ise `text` `np.str_` (str alt sınıfı) olur.
    Gerçek kütüphane `tuple[str]` verir (olcum-3 #6); kayda geçer, sözleşme ihlali değil."""
    c = Cikti(boxes=np.asarray([dortgen(0, 0, 5, 5)], np.float32), txts=np.asarray(["a"]), scores=(0.5,))
    [b] = tek(tmp_path, c)
    assert isinstance(b.text, str)
    assert type(b.text) is np.str_  # mevcut davranış sabitlenir


@pytest.mark.parametrize(
    "c",
    [
        Cikti(boxes=np.zeros((3, 4, 2), np.float32), txts=("a", "b"), scores=(0.5, 0.5, 0.5)),
        Cikti(boxes=np.zeros((2, 4, 2), np.float32), txts=("a", "b"), scores=(0.5,)),
        Cikti(boxes=np.zeros((2, 4, 2), np.float32), txts=("a", "b", "c"), scores=(0.5, 0.5)),
        Cikti(boxes=np.zeros((2, 4, 2), np.float32), txts=None, scores=(0.5, 0.5)),
        Cikti(boxes=np.zeros((2, 4, 2), np.float32), txts=("a", "b"), scores=None),
        Cikti(boxes=np.zeros((2, 4, 2), np.float32), txts=None, scores=None),
        Cikti(boxes=None, txts=("a",), scores=(0.5,)),
        Cikti(boxes=None, txts=("a",), scores=None),
    ],
)
def test_a3_uzunluk_veya_none_uyusmazligi_ocrerror_kismi_sonuc_yok(tmp_path: Path, c: Cikti) -> None:
    with pytest.raises(OcrError):
        tek(tmp_path, c)


def test_a3_bos_sonuc_bicimleri_bos_liste(tmp_path: Path) -> None:
    assert tek(tmp_path, Cikti(None, None, None)) == []
    assert tek(tmp_path, Cikti(None, (), ())) == []
    assert tek(tmp_path, Cikti(np.zeros((0, 4, 2), np.float32), (), ())) == []
    assert tek(tmp_path, Cikti([], [], [])) == []


def test_a3_puan_tipi_bozuksa_ocrerror_metin_mesajda_yok(tmp_path: Path) -> None:
    nobetci = "NOBETCI-A3"
    for kotu in ("0.5", None, [0.5], complex(0.5, 0), np.bool_(True), True):
        c = Cikti(boxes=np.zeros((1, 4, 2), np.float32), txts=(nobetci,), scores=(kotu,))
        with pytest.raises(OcrError) as ei:
            tek(tmp_path, c)
        assert nobetci not in str(ei.value)


# ===========================================================================
# A4 — K6 hata taksonomisi ve `__cause__` zinciri
# ===========================================================================


_YOK = object()  # `image=None`i yardımcıdan geçirmeden Frame'e koymak için nöbetçi


def _goruntu_varyantlari() -> list[tuple[str, Any]]:
    taban = np.zeros((40, 100, 3), np.uint8)
    salt = taban.copy()
    salt.flags.writeable = False
    return [
        ("int32", np.zeros((40, 100, 3), np.int32)),
        ("uint16", np.zeros((40, 100, 3), np.uint16)),
        ("bool", np.zeros((40, 100, 3), bool)),
        ("float64", np.zeros((40, 100, 3), np.float64)),
        ("2kanal", np.zeros((40, 100, 2), np.uint8)),
        ("4kanal", np.zeros((40, 100, 4), np.uint8)),
        ("0x0", np.zeros((0, 0, 3), np.uint8)),
        ("0xw", np.zeros((0, 100, 3), np.uint8)),
        ("hx0", np.zeros((40, 0, 3), np.uint8)),
        ("4B", np.zeros((1, 40, 100, 3), np.uint8)),
        ("liste", taban.tolist()),
        ("bytes", taban.tobytes()),
        ("None", _YOK),
    ]


@pytest.mark.parametrize("ad,image", _goruntu_varyantlari(), ids=[a for a, _ in _goruntu_varyantlari()])
def test_a4_bicim_disi_goruntu_contractviolation_motor_cagrilmaz(tmp_path: Path, ad: str, image: Any) -> None:
    f = Fabrika(cikti((dortgen(0, 0, 4, 4), "a", 0.9)))
    m = motor(tmp_path, f)
    fr = Frame(image=None, rect=Rect(0, 0, 100, 40), captured_at=0.0, seq=0) if image is _YOK else kare(image=image)  # type: ignore[arg-type]
    with pytest.raises(ContractViolation) as ei:
        m.recognize(fr, OcrPreset.DIALOGUE)
    assert f.calls == 0
    assert ei.value.__cause__ is None
    assert not isinstance(ei.value, (OcrError, ModelMissingError))


def _bitisik_olmayan_varyantlar() -> list[tuple[str, Any]]:
    kaynak = np.arange(40 * 100 * 3, dtype=np.uint8).reshape(40, 100, 3)
    salt = kaynak.copy()
    salt.flags.writeable = False
    return [
        ("transpoze_gorunum", np.arange(100 * 40 * 3, dtype=np.uint8).reshape(100, 40, 3).transpose(1, 0, 2)),
        ("yatay_ters_gorunum", kaynak[:, ::-1]),
        ("fortran", np.asfortranarray(kaynak)),
        ("dilim_gorunum", np.zeros((80, 200, 3), np.uint8)[10:50, 20:120]),
        ("salt_okunur", salt),
        ("bgra_dilimi", np.zeros((40, 100, 4), np.uint8)[:, :, :3]),
    ]


@pytest.mark.parametrize("ad,image", _bitisik_olmayan_varyantlar(), ids=[a for a, _ in _bitisik_olmayan_varyantlar()])
def test_a4_bitisik_olmayan_veya_salt_okunur_uint8_motora_gider(tmp_path: Path, ad: str, image: Any) -> None:
    """GÖZLEM: (h,w,3) uint8 ama C-bitişik olmayan / salt-okunur dizi ContractViolation
    ALMAZ, tanıyıcıya AYNEN (kopyasız) gider. Gerçek kütüphanede ne olduğu A6'da ayrı
    süreçte ölçüldü (`a6_gercek_model.txt`)."""
    assert image.shape == (40, 100, 3) and image.dtype == np.uint8
    f = Fabrika(cikti((dortgen(0, 0, 4, 4), "a", 0.9)))
    m = motor(tmp_path, f)
    [b] = m.recognize(kare(image=image), OcrPreset.DIALOGUE)
    assert f.calls == 1 and f.goruntuler[0] is image
    assert b.text == "a"


def test_a4_contractviolation_modelmissing_onunde(tmp_path: Path) -> None:
    """Model dosyası YOK + bozuk kare -> ContractViolation (dosya denetimi hiç koşmaz)."""
    f = Fabrika()
    m = RapidOcrEngine(language=OcrLanguage.JAPAN, allow_download=False, model_dir=tmp_path, recognizer_factory=f)
    with pytest.raises(ContractViolation):
        m.recognize(kare(image=np.zeros((40, 100, 3), np.int32)), OcrPreset.DIALOGUE)
    assert f.calls == 0
    with pytest.raises(ModelMissingError) as ei:  # aynı motor, doğru kare -> sıra: dosya denetimi
        m.recognize(kare(), OcrPreset.DIALOGUE)
    assert ei.value.__cause__ is None and f.calls == 0
    assert MODEL_ADLARI["japan"][0] in str(ei.value) and MODEL_ADLARI["japan"][1] in str(ei.value)


def test_a4_cause_zinciri_taniyici_istisnalari(tmp_path: Path) -> None:
    for ozgun in (RuntimeError("x"), ZeroDivisionError("y"), MemoryError(), OSError("z"), TypeError("t")):
        def _pat(_img: Any, _e: BaseException = ozgun) -> Any:
            raise _e

        with pytest.raises(OcrError) as ei:
            motor(tmp_path, Fabrika(tani=_pat)).recognize(kare(), OcrPreset.DIALOGUE)
        assert ei.value.__cause__ is ozgun
        assert type(ei.value) is OcrError


def test_a4_cause_zinciri_fabrika_istisnalari(tmp_path: Path) -> None:
    fnf = FileNotFoundError("model.onnx")
    with pytest.raises(ModelMissingError) as e1:
        motor(tmp_path, Fabrika(kurulum_hatasi=fnf)).recognize(kare(), OcrPreset.DIALOGUE)
    assert e1.value.__cause__ is fnf
    ve = ValueError("Unsupported rec.lang_type")
    with pytest.raises(OcrError) as e2:
        motor(tmp_path, Fabrika(kurulum_hatasi=ve)).recognize(kare(), OcrPreset.DIALOGUE)
    assert e2.value.__cause__ is ve
    pe = PermissionError("kilitli")
    with pytest.raises(OcrError) as e3:
        motor(tmp_path, Fabrika(kurulum_hatasi=pe)).recognize(kare(), OcrPreset.DIALOGUE)
    assert e3.value.__cause__ is pe
    mm = ModelMissingError("indirilemedi")
    with pytest.raises(ModelMissingError) as e4:
        motor(tmp_path, Fabrika(kurulum_hatasi=mm)).recognize(kare(), OcrPreset.DIALOGUE)
    assert e4.value is mm and e4.value.__cause__ is None


def test_a4_baseexception_sarilmaz(tmp_path: Path) -> None:
    def _kes(_img: Any) -> Any:
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        motor(tmp_path, Fabrika(tani=_kes)).recognize(kare(), OcrPreset.DIALOGUE)


def test_a4_taniyici_translatorerror_kardesi_oldugu_gibi_gecer_gozlem(tmp_path: Path) -> None:
    """GÖZLEM: tanıyıcı `CaptureError` fırlatırsa `recognize` onu AYNEN geçirir
    (OcrEngine Raises listesinde yok). Gerçek tanıyıcı yalnız OcrError üretir; kayda geçer."""
    ce = CaptureError("yabanci")

    def _pat(_img: Any) -> Any:
        raise ce

    with pytest.raises(CaptureError) as ei:
        motor(tmp_path, Fabrika(tani=_pat)).recognize(kare(), OcrPreset.DIALOGUE)
    assert ei.value is ce


def test_a4_kapali_motor_ocrerror_cause_yok(tmp_path: Path) -> None:
    f = Fabrika()
    m = motor(tmp_path, f)
    m.close()
    with pytest.raises(OcrError) as ei:
        m.recognize(kare(), OcrPreset.DIALOGUE)
    assert ei.value.__cause__ is None and f.calls == 0
    with pytest.raises(OcrError):  # kapalı + bozuk kare: OcrError (K10 sırası, belgeli)
        m.recognize(kare(image=np.zeros((40, 100, 3), np.int32)), OcrPreset.DIALOGUE)
    assert f.calls == 0


def test_a4_kurulum_hatasi_sonrasi_yeniden_deneme_yeni_fabrika_cagrisi(tmp_path: Path) -> None:
    f = Fabrika(kurulum_hatasi=RuntimeError("ilk"))
    m = motor(tmp_path, f)
    with pytest.raises(OcrError):
        m.recognize(kare(), OcrPreset.DIALOGUE)
    f.kurulum_hatasi = None
    assert m.recognize(kare(), OcrPreset.DIALOGUE) == [] and f.calls == 2


# ===========================================================================
# A5 — K3 aralık ve K11 tablo
# ===========================================================================


class _Sayi(enum.IntEnum):
    SEKIZ = 8


@pytest.mark.parametrize(
    "deger,beklenen",
    [
        (np.int64(8), 8),
        (np.int32(4), 4),
        (np.uint8(2), 2),
        (_Sayi.SEKIZ, 8),
        (8, 8),
        (None, 8),
    ],
)
def test_a5_threads_tam_sayi_turevleri_duz_int(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, deger: Any, beklenen: int) -> None:
    monkeypatch.setattr(os, "cpu_count", lambda: 32)
    f = Fabrika()
    m = motor(tmp_path, f, threads=deger)
    m.recognize(kare(), OcrPreset.DIALOGUE)
    assert f.son[INTRA] == beklenen and f.son[INTER] == beklenen
    assert type(f.son[INTRA]) is int and type(f.son[INTER]) is int
    assert type(m.threads) is int and m.threads == beklenen


@pytest.mark.parametrize("deger", [True, False, 8.0, np.float64(8.0), "8", b"8", 4.5, complex(8), [8], np.array(8)])
def test_a5_threads_tam_sayi_olmayan_typeerror(deger: Any) -> None:
    with pytest.raises(TypeError):
        RapidOcrEngine(language=OcrLanguage.JAPAN, threads=deger)


@pytest.mark.parametrize("deger", [0, -1, -8, np.int64(0), np.int64(-1), 2**63])
def test_a5_threads_aralik_disi_valueerror(deger: Any) -> None:
    with pytest.raises(ValueError):
        RapidOcrEngine(language=OcrLanguage.JAPAN, threads=deger)


def test_a5_threads_cpu_siniri_numpy_ile_de(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "cpu_count", lambda: 6)
    with pytest.raises(ValueError):
        RapidOcrEngine(language=OcrLanguage.JAPAN, threads=np.int64(8))
    assert RapidOcrEngine(language=OcrLanguage.JAPAN, threads=np.int64(6)).threads == 6
    assert RapidOcrEngine(language=OcrLanguage.JAPAN).threads == 6
    monkeypatch.setattr(os, "cpu_count", lambda: 2)
    assert RapidOcrEngine(language=OcrLanguage.JAPAN).threads == 2
    with pytest.raises(ValueError):
        RapidOcrEngine(language=OcrLanguage.JAPAN, threads=3)


def test_a5_threads_yapimda_dondurulur_sonraki_cpu_degisimi_etkilemez(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "cpu_count", lambda: 32)
    f = Fabrika()
    m = motor(tmp_path, f, threads=8)
    monkeypatch.setattr(os, "cpu_count", lambda: 4)
    m.recognize(kare(), OcrPreset.DIALOGUE)
    assert f.son[INTRA] == 8  # yapımdaki değer; K3 aralığı yapımda ölçülür


@pytest.mark.parametrize("dil", ["japan", "korean", "chinese", "english"])
def test_a5_k11_dort_dil_alti_anahtar_birebir(tmp_path: Path, dil: str) -> None:
    f = Fabrika()
    motor(tmp_path, f, dil=dil).recognize(kare(), OcrPreset.DIALOGUE)
    p = f.son
    det, rec = K11_TABLO[dil]
    assert p["Det.lang_type"] == det and p["Rec.lang_type"] == rec
    for bolum in ("Det", "Rec"):
        for alan, deger in ORTAK.items():
            assert p[f"{bolum}.{alan}"] == deger, (dil, bolum, alan)
    assert p["Global.use_cls"] is False and p["Global.text_score"] == 0.0
    assert p["Det.model_path"] == tmp_path / MODEL_ADLARI[dil][0]
    assert p["Rec.model_path"] == tmp_path / MODEL_ADLARI[dil][1]
    assert not any(k.startswith("Cls.") for k in p)


def test_a5_k11_diller_arasi_det_ve_rec_ayrimi() -> None:
    """Tablonun ayırt edici noktaları: JAPAN/KOREAN det=multi, CHINESE/ENGLISH det=ch;
    dört rec değeri birbirinden farklı. Tek dili yanlış eşleyen mutant burada da düşer."""
    p = {d: RapidOcrEngine(language=OcrLanguage(d), allow_download=True).parametreler() for d in K11_TABLO}
    assert p["japan"]["Det.lang_type"] == p["korean"]["Det.lang_type"] == "multi"
    assert p["chinese"]["Det.lang_type"] == p["english"]["Det.lang_type"] == "ch"
    assert len({p[d]["Rec.lang_type"] for d in K11_TABLO}) == 4
    assert {p[d]["Rec.lang_type"] for d in K11_TABLO} == {"japan", "korean", "ch", "en"}


def test_a5_k2_dil_degeri_buyuk_harf_reddedilir() -> None:
    with pytest.raises(ValueError):
        RapidOcrEngine(language="JAPAN")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        RapidOcrEngine(language="jp")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        RapidOcrEngine()  # type: ignore[call-arg]


def test_a5_preset_params_ve_ciktiyi_degistirmez(tmp_path: Path) -> None:
    f = Fabrika(cikti((dortgen(1.5, 2.5, 9.5, 8.5), "a", 0.31)))
    m = motor(tmp_path, f)
    sonuc = [m.recognize(kare(), p) for p in OcrPreset]
    assert all(s == sonuc[0] for s in sonuc) and f.calls == 1


def test_a4_rect_rect_degilse_gozlem(tmp_path: Path) -> None:
    """GÖZLEM (düşük): `Frame.rect` bir `Rect` değilse (`tuple`) motor `AttributeError`
    fırlatır — K6 taksonomisi DIŞINDA çıplak istisna; fabrika yine çağrılmaz.
    `Frame` dataclass'ı alan tipini doğrulamaz; CaptureService her zaman `Rect` verir."""
    f = Fabrika()
    m = motor(tmp_path, f)
    fr = Frame(image=np.zeros((40, 100, 3), np.uint8), rect=(0, 0, 100, 40), captured_at=0.0, seq=0)  # type: ignore[arg-type]
    with pytest.raises(AttributeError):
        m.recognize(fr, OcrPreset.DIALOGUE)
    assert f.calls == 0
