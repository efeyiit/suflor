"""TESTER-B -- T-006 mercek B (test kalitesi, K1 bariyeri, omur, loglama), tur 1.

Kor yazildi: yalniz packet.md (surum 2), motor kaynagi ve sefin conftest'i
okundu. Butun testler SAHTE fabrikayla kosar; bariyer bu dizinin kendi
`conftest.py`'sinde bagimsiz kurulur. Gercek modelle olcumler ayri surecte
`b4_gercek_surec_sondasi.py` ile yapilir (pytest'in disinda).

Referanslar BAGIMSIZ: sahte fabrika ve beklenen degerler burada yeniden
yazildi, implementer'in test dosyasindan ICE AKTARILMADI.

Kosum:
    python -m pytest .agents/tasks/T-006/tester_B -q -p no:cacheprovider
"""
from __future__ import annotations

import ast
import gc
import importlib
import importlib.metadata
import importlib.util
import logging
import subprocess
import sys
import types
import weakref
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import numpy as np
import pytest

import tb_bariyer as tb_conftest  # bu dizinin bariyer modulu (conftest ayni nesneyi import eder)
from src.contracts.errors import ContractViolation, ModelMissingError, OcrError
from src.contracts.models import Frame, OcrPreset, Rect
from src.ocr import rapid_engine
from src.ocr.rapid_engine import OcrLanguage, RapidOcrEngine

DEPO = tb_conftest._KOK
MOTOR_KAYNAK = DEPO / "src" / "ocr" / "rapid_engine.py"
TEST_KAYNAK = DEPO / "tests" / "unit" / "ocr" / "test_rapid_engine.py"
SEF_CONFTEST = DEPO / "tests" / "unit" / "ocr" / "conftest.py"
SEF_BARIYER_TESTI = DEPO / "tests" / "unit" / "ocr" / "test_conftest_bariyer.py"
LOGGER_ADI = "RapidOCR"

# Bagimsiz referans: paket K6 dosya adlari (olcum-2 degil, paketin K11 tablosu + O4 dosya adlari)
DOSYALAR: dict[OcrLanguage, tuple[str, str]] = {
    OcrLanguage.JAPAN: ("multi_PP-OCRv3_det_mobile.onnx", "japan_PP-OCRv4_rec_mobile.onnx"),
    OcrLanguage.KOREAN: ("multi_PP-OCRv3_det_mobile.onnx", "korean_PP-OCRv4_rec_mobile.onnx"),
    OcrLanguage.CHINESE: ("ch_PP-OCRv4_det_mobile.onnx", "ch_PP-OCRv4_rec_mobile.onnx"),
    OcrLanguage.ENGLISH: ("ch_PP-OCRv4_det_mobile.onnx", "en_PP-OCRv4_rec_mobile.onnx"),
}


# ---------------------------------------------------------------------------
# sahte kutuphane (gercek bicim: float32 (N,4,2), tuple[str], tuple[float]; bos -> None'lar)
# ---------------------------------------------------------------------------


class Cikti:
    def __init__(self, boxes: Any = None, txts: Any = None, scores: Any = None) -> None:
        self.boxes, self.txts, self.scores = boxes, txts, scores


def dolu(*metinler: str, puan: float = 0.9) -> Cikti:
    kutular = [[[5.0, 5.0 + 20 * i], [60.0, 5.0 + 20 * i], [60.0, 20.0 + 20 * i], [5.0, 20.0 + 20 * i]] for i in range(len(metinler))]
    return Cikti(np.asarray(kutular, dtype=np.float32), tuple(metinler), tuple(float(puan) for _ in metinler))


class Fabrika:
    """Sayar, params kaydeder; her cagri TAZE bir tanıyıcı kapanisi uretir (weakref icin)."""

    def __init__(
        self,
        cikti: Cikti | None = None,
        tanima: Callable[[Any], Any] | None = None,
        kurulumda: Callable[[], None] | None = None,
        hata: BaseException | None = None,
    ) -> None:
        self.cikti = cikti if cikti is not None else Cikti()
        self.tanima = tanima
        self.kurulumda = kurulumda
        self.hata = hata
        self.calls = 0
        self.params: list[dict[str, object]] = []
        self.uretilenler: list[weakref.ReferenceType[Any]] = []

    def __call__(self, params: dict[str, object]) -> Callable[[Any], Any]:
        self.calls += 1
        self.params.append(dict(params))
        if self.kurulumda is not None:
            self.kurulumda()
        if self.hata is not None:
            raise self.hata
        cikti, tanima = self.cikti, self.tanima

        def _t(img: Any) -> Any:
            return tanima(img) if tanima is not None else cikti

        self.uretilenler.append(weakref.ref(_t))
        return _t


def kare(h: int = 40, w: int = 100, image: Any = None, rect: Rect | None = None) -> Frame:
    if image is None:
        image = np.zeros((h, w, 3), dtype=np.uint8)
    return Frame(image=image, rect=rect or Rect(0, 0, w, h), captured_at=0.0, seq=0)


def motor(tmp_path: Path, f: Fabrika, dil: OcrLanguage = OcrLanguage.JAPAN, **ek: Any) -> RapidOcrEngine:
    for ad in DOSYALAR[dil]:
        (tmp_path / ad).write_bytes(b"")
    return RapidOcrEngine(language=dil, model_dir=tmp_path, allow_download=False, recognizer_factory=f, **ek)


def _yasak_modulleri_temizle() -> None:
    for k in [k for k in sys.modules if k.split(".", 1)[0] in tb_conftest.YASAK_KOKLER]:
        del sys.modules[k]


@pytest.fixture
def rapid_logger() -> Iterator[logging.Logger]:
    """`RapidOCR` logger'ini test oncesi/sonrasi temiz tutar."""
    lg = logging.getLogger(LOGGER_ADI)
    eski = (lg.level, lg.propagate, list(lg.handlers))
    lg.setLevel(logging.NOTSET)
    lg.propagate = True
    for h in list(lg.handlers):
        lg.removeHandler(h)
    try:
        yield lg
    finally:
        for h in list(lg.handlers):
            lg.removeHandler(h)
        lg.setLevel(eski[0])
        lg.propagate = eski[1]
        for h in eski[2]:
            lg.addHandler(h)


def kutuphane_gibi_kur(lg: logging.Logger) -> None:
    """rapidocr `utils/log.py`'nin yaptigi: INFO, propagate=False, kendi stderr handler'i."""
    lg.setLevel(logging.INFO)
    lg.propagate = False
    if not lg.handlers:
        h = logging.StreamHandler()  # sys.stderr'i SIMDI baglar (capsys altinda yakalanir)
        h.setLevel(logging.INFO)
        lg.addHandler(h)


# ===========================================================================
# B3 -- K1 bariyeri gercekten tutuyor mu? (kacis yollari OLCULUR)
# ===========================================================================


def test_b3_conftest_yuklenirken_yasak_kok_sys_modules_ta_yoktu() -> None:
    """'sys.modules onceden dolu' kacisi: bariyer kurulmadan once yuklu olsaydi bulucu hic sorulmazdi."""
    assert tb_conftest.ONCEDEN_YUKLU == ()
    assert not any(k.split(".", 1)[0] in tb_conftest.YASAK_KOKLER for k in sys.modules)


@pytest.mark.parametrize("ad", ["rapidocr", "rapidocr.main", "rapidocr.inference_engine.base", "onnxruntime"])
def test_b3_import_module_kesilir(ad: str) -> None:
    _yasak_modulleri_temizle()
    with pytest.raises(RuntimeError, match=tb_conftest.BARIYER_MESAJI):
        importlib.import_module(ad)
    assert ad not in sys.modules


def test_b3_dunder_import_kesilir() -> None:
    with pytest.raises(RuntimeError, match=tb_conftest.BARIYER_MESAJI):
        __import__("rapidocr")
    with pytest.raises(RuntimeError, match=tb_conftest.BARIYER_MESAJI):
        __import__("onnxruntime.capi")


def test_b3_find_spec_kesilir() -> None:
    with pytest.raises(RuntimeError, match=tb_conftest.BARIYER_MESAJI):
        importlib.util.find_spec("rapidocr")


def _dagitim_kok(ad: str) -> Path | None:
    try:
        d = importlib.metadata.distribution(ad)
    except importlib.metadata.PackageNotFoundError:
        return None
    return Path(str(d.locate_file(ad)))


@pytest.mark.parametrize("ad", ["rapidocr", "onnxruntime"])
def test_b3_spec_from_file_location_kacisi_olculur(ad: str) -> None:
    """Dosyadan yukleme bulucuyu ATLAR; ama paketin `__init__`i alt modul import eder ve o import
    yine `sys.meta_path`ten gecer -> bariyer orada ateslemeli. Varsayilmaz, olculur."""
    kok = _dagitim_kok(ad)
    if kok is None or not (kok / "__init__.py").is_file():
        pytest.skip(f"{ad} dagitimi yok")
    _yasak_modulleri_temizle()
    spec = importlib.util.spec_from_file_location(ad, kok / "__init__.py", submodule_search_locations=[str(kok)])
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[ad] = mod
    try:
        with pytest.raises(RuntimeError, match=tb_conftest.BARIYER_MESAJI):
            spec.loader.exec_module(mod)
    finally:
        _yasak_modulleri_temizle()
    assert not any(k.split(".", 1)[0] in tb_conftest.YASAK_KOKLER for k in sys.modules)


def test_b3_sys_modules_onceden_dolu_kacisi_olculur() -> None:
    """`sys.modules['rapidocr']` elle doldurulursa `import rapidocr` bulucuya sormaz -> KACAR.
    Ama ALT MODUL (`rapidocr.main`) yine bulucudan gecer -> kesilir. Iki yon de olculur."""
    sahte = types.ModuleType("rapidocr")
    sahte.__path__ = []  # type: ignore[attr-defined]
    sys.modules["rapidocr"] = sahte
    try:
        import rapidocr as r  # noqa: F401  -- bulucu sorulmaz

        assert r is sahte  # kacis var: sys.modules onceligi
        with pytest.raises(RuntimeError, match=tb_conftest.BARIYER_MESAJI):
            importlib.import_module("rapidocr.main")
    finally:
        _yasak_modulleri_temizle()


def test_b3_alt_surec_kacisi_var_ama_motor_ve_testler_kullanmiyor() -> None:
    """Bariyer surec-yerel: alt surecte import serbest (real_check bunu bilerek kullanir).
    Motor ve birim testleri `subprocess`/`spec_from_file_location`/`__import__`/`sys.modules[..] =`
    kacislarindan hicbirini KULLANMAMALI -- AST ile olculur."""
    r = subprocess.run([sys.executable, "-c", "import importlib.util; print(importlib.util.find_spec('rapidocr') is not None)"],
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0 and r.stdout.strip() == "True"  # alt surecte bariyer YOK (beklenen)

    kacislar = ("spec_from_file_location", "subprocess", "__import__", "import_module", "runpy", "exec_module")
    for dosya in (MOTOR_KAYNAK, TEST_KAYNAK):
        agac = ast.parse(dosya.read_text(encoding="utf-8"))
        kullanilan: list[str] = []
        for n in ast.walk(agac):
            if isinstance(n, ast.Import):
                kullanilan += [a.name for a in n.names if a.name.split(".")[0] in ("subprocess", "runpy")]
            if isinstance(n, ast.ImportFrom) and (n.module or "").split(".")[0] in ("subprocess", "runpy"):
                kullanilan.append(n.module or "")
            if isinstance(n, ast.Call):
                src = ast.unparse(n.func)
                if any(k in src for k in kacislar):
                    kullanilan.append(src)
            if isinstance(n, ast.Assign):
                for t in n.targets:
                    if isinstance(t, ast.Subscript) and ast.unparse(t.value) == "sys.modules":
                        kullanilan.append("sys.modules[...] =")
        assert kullanilan == [], f"{dosya.name}: kacis yolu kullaniyor: {kullanilan}"


def test_b3_sefin_pozitif_kontrolu_yalniz_import_module_yolunu_goruyor() -> None:
    """Belgeleme olcusu: sefin `test_conftest_bariyer.py` hangi kacis yollarini sinar?"""
    agac = ast.parse(SEF_BARIYER_TESTI.read_text(encoding="utf-8"))
    cagrilar = {ast.unparse(n.func) for n in ast.walk(agac) if isinstance(n, ast.Call)}
    assert "importlib.import_module" in cagrilar
    gormedigi = [k for k in ("importlib.util.spec_from_file_location", "__import__", "subprocess.run", "importlib.util.find_spec") if k not in cagrilar]
    # Bulgu (verdict'e): pozitif kontrol yalniz import_module yolunu sinar; asagidakiler sinanmiyor.
    assert gormedigi == ["importlib.util.spec_from_file_location", "__import__", "subprocess.run", "importlib.util.find_spec"]


def test_b3_sefin_bariyeri_meta_path_basinda_ve_sys_modules_e_nobetci_koymuyor() -> None:
    """Paket K1: 'sys.modules[\"rapidocr\"]a nobetci koyar + meta_path sayaci'. Sefin conftest'i
    gercekte ne yapiyor? Kaynak okunur: nobetci YOK, sayac YOK, yalniz meta_path bulucu."""
    kaynak = SEF_CONFTEST.read_text(encoding="utf-8")
    assert "sys.meta_path.insert(0" in kaynak
    assert 'sys.modules["rapidocr"]' not in kaynak and "sys.modules['rapidocr']" not in kaynak
    assert "onnxruntime" in kaynak


def test_b3_sahte_fabrikayla_tam_kosum_yasak_kok_yuklemez(tmp_path: Path) -> None:
    f = Fabrika(dolu("a", "b"))
    m = motor(tmp_path, f)
    for dil in OcrLanguage:
        motor(tmp_path, Fabrika(), dil).recognize(kare(), OcrPreset.DIALOGUE)
    assert len(m.recognize(kare(), OcrPreset.DIALOGUE)) == 2
    assert not any(k.split(".", 1)[0] in tb_conftest.YASAK_KOKLER for k in sys.modules)
    # bariyer HIC sorgulanmadi: motor bariyer altinda kutuphane adini aramadi bile
    assert tb_conftest.BARIYER.sorgular == [] or all(
        s.split(".", 1)[0] in tb_conftest.YASAK_KOKLER for s in tb_conftest.BARIYER.sorgular
    )


def test_b3_varsayilan_model_dizini_bariyer_altinda_bulucuya_sormaz() -> None:
    if _dagitim_kok("rapidocr") is None:
        pytest.skip("rapidocr dagitimi yok")
    once = len(tb_conftest.BARIYER.sorgular)
    d = rapid_engine.varsayilan_model_dizini()
    assert d.name == "models"
    assert len(tb_conftest.BARIYER.sorgular) == once  # find_spec sorgusu YOK
    assert "rapidocr" not in sys.modules


# ===========================================================================
# B4 -- K7 loglama: her seviyede, gercek logger yapilandirmasiyla, stdout/stderr dahil
# ===========================================================================

SEVIYELER = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR]
DIGER_LOGGERLAR = ("rapidocr", "RapidOCR.det", "RapidOCR.rec", "src.ocr.rapid_engine", "suflor", "suflor.ocr", "onnxruntime")


@pytest.mark.parametrize("seviye", SEVIYELER, ids=logging.getLevelName)
def test_b4_her_seviyede_nobetci_hicbir_loga_ve_stdout_stderr_e_dusmez(
    tmp_path: Path, caplog: pytest.LogCaptureFixture, capsys: pytest.CaptureFixture[str],
    rapid_logger: logging.Logger, seviye: int,
) -> None:
    """Kurulumdan SONRA butun ilgili logger'lar `seviye`ye acilir (uygulama DEBUG acmis gibi) ve
    ikinci `recognize` kosulur: motor metni hicbir logger'a, stdout'a, stderr'e YAZMAMALI."""
    nobetci = "NÖBETÇİ-7f3a-B"
    f = Fabrika(dolu(nobetci, f"ikinci {nobetci}"), kurulumda=lambda: kutuphane_gibi_kur(rapid_logger))
    m = motor(tmp_path, f)
    m.recognize(kare(), OcrPreset.DIALOGUE)  # kurulum (motor RapidOCR'u ERROR'a ceker)
    caplog.clear()
    caplog.set_level(seviye)  # kok logger
    for ad in (LOGGER_ADI, *DIGER_LOGGERLAR):
        logging.getLogger(ad).setLevel(seviye)
    try:
        bl = m.recognize(kare(), OcrPreset.DIALOGUE)
        bl2 = m.recognize(kare(rect=Rect(-2600, -50, 100, 40)), OcrPreset.DIALOGUE)
    finally:
        for ad in DIGER_LOGGERLAR:
            logging.getLogger(ad).setLevel(logging.NOTSET)
    assert [b.text for b in bl] == [nobetci, f"ikinci {nobetci}"] and len(bl2) == 2
    assert all(nobetci not in r.getMessage() for r in caplog.records), [r.getMessage() for r in caplog.records]
    assert all("7f3a" not in (r.args and str(r.args) or "") for r in caplog.records)
    out, err = capsys.readouterr()
    assert out == "" and err == "", (out, err)


def test_b4_pozitif_kontrol_olcu_atesliyor(
    tmp_path: Path, caplog: pytest.LogCaptureFixture, capsys: pytest.CaptureFixture[str], rapid_logger: logging.Logger
) -> None:
    """Ayni duzenek, metni loglayan SAHTE bir tanıyıcı ile: (a) kok logger yoluyla caplog,
    (b) propagate=False RapidOCR logger yoluyla stderr -- ikisi de nobetciyi GORMELI."""
    nobetci = "NÖBETÇİ-pk-B"

    def _tani(_img: Any) -> Any:
        logging.getLogger("suflor.ocr").debug("blok %s", nobetci)
        rapid_logger.info("blok %s", nobetci)
        return dolu(nobetci)

    f = Fabrika(tanima=_tani, kurulumda=lambda: kutuphane_gibi_kur(rapid_logger))
    m = motor(tmp_path, f)
    m.recognize(kare(), OcrPreset.DIALOGUE)
    caplog.clear()
    caplog.set_level(logging.DEBUG)
    rapid_logger.setLevel(logging.DEBUG)
    m.recognize(kare(), OcrPreset.DIALOGUE)
    assert any(nobetci in r.getMessage() and r.name == "suflor.ocr" for r in caplog.records)
    _, err = capsys.readouterr()
    assert nobetci in err  # propagate=False + StreamHandler yolu capsys'e dusuyor


def test_b4_rapidocr_logger_kurulumdan_sonra_error(tmp_path: Path, rapid_logger: logging.Logger) -> None:
    """Fabrika (kutuphaneyi taklit) seviyeyi INFO'ya sifirlar + propagate=False + handler kurar;
    recognize sonrasi logger seviyesi ERROR olmali. DEBUG'a sifirlayan daha sert taklit de olculur."""
    f = Fabrika(kurulumda=lambda: kutuphane_gibi_kur(rapid_logger))
    motor(tmp_path, f).recognize(kare(), OcrPreset.DIALOGUE)
    assert rapid_logger.level == logging.ERROR
    assert f.params[-1]["Global.log_level"] == "error"

    def _debug() -> None:
        kutuphane_gibi_kur(rapid_logger)
        rapid_logger.setLevel(logging.DEBUG)

    f2 = Fabrika(kurulumda=_debug)
    motor(tmp_path, f2).recognize(kare(), OcrPreset.DIALOGUE)
    assert rapid_logger.level == logging.ERROR


def test_b4_bos_karede_kutuphane_warningi_stderr_e_dusmez(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], rapid_logger: logging.Logger
) -> None:
    """Gercek kutuphane metinsiz karede `logger.warning('The text detection result is empty')` basar
    (main.py:132) ve logger'in kendi stderr handler'i var. Motor ERROR'a cektigi icin stderr BOS kalmali.
    Pozitif kontrol: seviye WARNING'e geri alinirsa ayni uyari stderr'de GORUNUR."""
    def _tani(_img: Any) -> Any:
        rapid_logger.warning("The text detection result is empty")
        return Cikti()

    f = Fabrika(tanima=_tani, kurulumda=lambda: kutuphane_gibi_kur(rapid_logger))
    m = motor(tmp_path, f)
    assert m.recognize(kare(), OcrPreset.DIALOGUE) == []
    assert m.recognize(kare(), OcrPreset.DIALOGUE) == []
    out, err = capsys.readouterr()
    assert out == "" and err == ""
    rapid_logger.setLevel(logging.WARNING)  # pozitif kontrol
    m.recognize(kare(), OcrPreset.DIALOGUE)
    _, err = capsys.readouterr()
    assert "detection result is empty" in err


def test_b4_motor_yalniz_rapidocr_logger_ina_dokunur_baska_logger_i_susturmaz(tmp_path: Path, rapid_logger: logging.Logger) -> None:
    """Olcu degil BELGE: motor `rapidocr` (kucuk harf) ya da `RapidOCR.det` gibi logger'lari susturmaz.
    Gercek kutuphanede bunlarin VAR OLMADIGI ayri surecte olculur (b4_gercek_surec_sondasi.py)."""
    for ad in ("rapidocr", "RapidOCR.det"):
        logging.getLogger(ad).setLevel(logging.INFO)
    try:
        motor(tmp_path, Fabrika()).recognize(kare(), OcrPreset.DIALOGUE)
        assert logging.getLogger("rapidocr").level == logging.INFO
        assert logging.getLogger("RapidOCR.det").level == logging.INFO  # acik seviye korunur (motor dokunmaz)
        assert rapid_logger.level == logging.ERROR
    finally:
        for ad in ("rapidocr", "RapidOCR.det"):
            logging.getLogger(ad).setLevel(logging.NOTSET)


def test_b4_hata_yollari_da_metin_tasimaz(tmp_path: Path, caplog: pytest.LogCaptureFixture, capsys: pytest.CaptureFixture[str]) -> None:
    """Bozuk cikti (puan str) -> OcrError; istisna metni, __cause__ metni, loglar ve stdout/stderr nobetciyi tasimaz."""
    nobetci = "NÖBETÇİ-hata-B"
    c = Cikti(np.zeros((1, 4, 2), np.float32), (nobetci,), ("x",))
    f = Fabrika(tanima=lambda _img: c)
    caplog.set_level(logging.DEBUG)
    with pytest.raises(OcrError) as ei:
        motor(tmp_path, f).recognize(kare(), OcrPreset.DIALOGUE)
    zincir = []
    e: BaseException | None = ei.value
    while e is not None:
        zincir.append(str(e))
        e = e.__cause__ or e.__context__
    assert all(nobetci not in s for s in zincir)
    assert all(nobetci not in r.getMessage() for r in caplog.records)
    out, err = capsys.readouterr()
    assert out == "" and err == ""


# ===========================================================================
# B5 -- K10 omur
# ===========================================================================


def test_b5_close_x2_sonra_recognize_ocrerror_ve_fabrika_yeniden_cagrilmaz(tmp_path: Path) -> None:
    f = Fabrika(dolu("a"))
    m = motor(tmp_path, f)
    assert f.calls == 0
    for _ in range(3):
        m.recognize(kare(), OcrPreset.DIALOGUE)
    assert f.calls == 1
    m.close()
    m.close()
    for _ in range(3):
        with pytest.raises(OcrError):
            m.recognize(kare(), OcrPreset.DIALOGUE)
    assert f.calls == 1
    m.close()  # kapali motorda tekrar close: sessiz
    assert f.calls == 1


def test_b5_close_taniyiciyi_gercekten_birakir(tmp_path: Path) -> None:
    """K10 'close() tanıyıcıyı birakir': fabrikanin urettigi kapanisa weakref tutulur;
    close() + gc sonrasi olmeli. (`_taniyici=None` yapmayan bir close bunu gecemez.)"""
    f = Fabrika(dolu("a"))
    m = motor(tmp_path, f)
    m.recognize(kare(), OcrPreset.DIALOGUE)
    [ref] = f.uretilenler
    assert ref() is not None  # motor tutuyor
    m.close()
    gc.collect()
    assert ref() is None, "close() tanıyıcıyı birakmadi (oturumlar canli kalir)"


def test_b5_fabrika_ilk_cagrida_firlatirsa_ikinci_recognize_yeniden_dener_ve_ornek_tutulmaz(tmp_path: Path) -> None:
    """Paket bu durumda SESSIZ (K6 'yeniden deneme yok' cumlesi (c) kare dogrulamasina ait).
    Motor docstring'i: kurulum basarisizsa ornek tutulmaz, sonraki recognize yeniden dener. Olculur."""
    f = Fabrika(dolu("a"), hata=RuntimeError("ilk kurulum"))
    m = motor(tmp_path, f)
    with pytest.raises(OcrError) as e1:
        m.recognize(kare(), OcrPreset.DIALOGUE)
    assert isinstance(e1.value.__cause__, RuntimeError) and f.calls == 1
    with pytest.raises(OcrError):
        m.recognize(kare(), OcrPreset.DIALOGUE)  # otomatik yeniden deneme YOK: her cagri yeniden dener, hata surer
    assert f.calls == 2
    f.hata = None
    assert [b.text for b in m.recognize(kare(), OcrPreset.DIALOGUE)] == ["a"]
    assert f.calls == 3
    m.recognize(kare(), OcrPreset.DIALOGUE)
    assert f.calls == 3  # basarili kurulumdan sonra tek ornek


def test_b5_modelmissing_kurulumda_ornek_tutulmaz_dosya_gelince_kurulur(tmp_path: Path) -> None:
    """Gercek senaryo: allow_download=False, model sonradan diske konur -> ayni motor kendini kurar."""
    f = Fabrika(dolu("a"))
    m = RapidOcrEngine(language=OcrLanguage.KOREAN, model_dir=tmp_path, allow_download=False, recognizer_factory=f)
    with pytest.raises(ModelMissingError):
        m.recognize(kare(), OcrPreset.DIALOGUE)
    assert f.calls == 0
    for ad in DOSYALAR[OcrLanguage.KOREAN]:
        (tmp_path / ad).write_bytes(b"")
    assert len(m.recognize(kare(), OcrPreset.DIALOGUE)) == 1 and f.calls == 1


def test_b5_kurulum_hatasindan_sonra_close_ve_kapali_davranisi(tmp_path: Path) -> None:
    f = Fabrika(hata=RuntimeError("kurulum"))
    m = motor(tmp_path, f)
    with pytest.raises(OcrError):
        m.recognize(kare(), OcrPreset.DIALOGUE)
    m.close()
    f.hata = None
    with pytest.raises(OcrError, match="kapatildi"):
        m.recognize(kare(), OcrPreset.DIALOGUE)
    assert f.calls == 1  # kapali motor fabrikayi yeniden CAGIRMAZ


def test_b5_iki_motor_ayni_fabrikayi_paylasirsa_durum_karismaz(tmp_path: Path) -> None:
    f = Fabrika(dolu("x"))
    a = motor(tmp_path, f, OcrLanguage.JAPAN, threads=2)
    b = motor(tmp_path, f, OcrLanguage.KOREAN, threads=3)
    assert a.recognize(kare(), OcrPreset.DIALOGUE)[0].text == "x"
    assert b.recognize(kare(), OcrPreset.DIALOGUE)[0].text == "x"
    assert f.calls == 2
    assert f.params[0]["Rec.lang_type"] == "japan" and f.params[1]["Rec.lang_type"] == "korean"
    assert f.params[0]["EngineConfig.onnxruntime.intra_op_num_threads"] == 2
    assert f.params[1]["EngineConfig.onnxruntime.intra_op_num_threads"] == 3
    a.close()
    assert b.recognize(kare(), OcrPreset.DIALOGUE)[0].text == "x"  # b etkilenmez
    with pytest.raises(OcrError):
        a.recognize(kare(), OcrPreset.DIALOGUE)
    assert f.calls == 2
    # a'nin tanıyıcısı birakildi, b'ninki duruyor
    gc.collect()
    assert f.uretilenler[0]() is None and f.uretilenler[1]() is not None


def test_b5_kapali_motorda_bozuk_kare_de_ocrerror_ve_fabrika_sayaci_sabit(tmp_path: Path) -> None:
    f = Fabrika()
    m = motor(tmp_path, f)
    m.close()
    with pytest.raises(OcrError):
        m.recognize(kare(image=np.zeros((4, 4, 4), np.uint8)), OcrPreset.DIALOGUE)
    assert f.calls == 0


def test_b5_parametreler_close_sonrasi_da_calisir_ama_fabrikaya_gitmez(tmp_path: Path) -> None:
    """Gozlem metodu kapalilikla ilgisiz (paket sessiz); belge amacli olcum."""
    f = Fabrika()
    m = motor(tmp_path, f)
    m.close()
    p = m.parametreler()
    assert p["Global.text_score"] == 0.0 and f.calls == 0


def test_b5_taniyici_istisnasi_ornegi_dusurmez(tmp_path: Path) -> None:
    """Tanıma sirasinda kutuphane hatasi -> OcrError; motor AYNI tanıyıcıyı tutmaya devam eder (K6 b: yeniden deneme yok, ama ornek de atilmaz)."""
    sayac = {"n": 0}

    def _tani(_img: Any) -> Any:
        sayac["n"] += 1
        if sayac["n"] == 1:
            raise RuntimeError("gecici")
        return dolu("ok")

    f = Fabrika(tanima=_tani)
    m = motor(tmp_path, f)
    with pytest.raises(OcrError):
        m.recognize(kare(), OcrPreset.DIALOGUE)
    assert m.recognize(kare(), OcrPreset.DIALOGUE)[0].text == "ok"
    assert f.calls == 1 and sayac["n"] == 2


# ===========================================================================
# B6 -- kapsam durustlugu
# ===========================================================================


def test_b6_tek_pragma_ve_yalniz_varsayilan_fabrikada() -> None:
    satirlar = MOTOR_KAYNAK.read_text(encoding="utf-8").splitlines()
    pragmalar = [(i + 1, s) for i, s in enumerate(satirlar) if "pragma: no cover" in s]
    assert len(pragmalar) == 1
    assert pragmalar[0][1].lstrip().startswith("def _varsayilan_fabrika(")


def test_b6_eksik_iki_satir_yapisal_olarak_erisilemez() -> None:
    """Kapsam raporunda eksik gorunen iki `raise ValueError` satiri: her enum uyesi tabloda,
    uye olmayan deger tabloya varmadan `OcrLanguage(...)`da patlar."""
    for dil in OcrLanguage:
        assert rapid_engine._dil_satiri(dil) is not None
        assert rapid_engine.beklenen_model_dosyalari(dil) == DOSYALAR[dil]
    with pytest.raises(ValueError) as ei:
        rapid_engine.beklenen_model_dosyalari("klingon")  # type: ignore[arg-type]
    assert "tabloda olmayan" not in str(ei.value)  # OcrLanguage(...) firlatti, tablo satiri degil
    # kaynakta iki satir da 'yapisal olarak erisilemez' etiketli ve pragma ALMAMIS (durust)
    kaynak = MOTOR_KAYNAK.read_text(encoding="utf-8")
    assert kaynak.count('raise ValueError(f"tabloda olmayan dil: ') == 2
    assert kaynak.count("yapisal olarak erisilemez") == 2


def test_b6_varsayilan_fabrika_pragma_kapsami_real_check_ile_olculuyor() -> None:
    """Pragma'li fonksiyonun icindeki iki dal (DownloadFileException, beklenmeyen cikti tipi)
    hicbir kapida kosmaz -- [ÖLÇÜLMÜYOR] damgasi docstring'de var mi?"""
    doc = rapid_engine.__doc__ or ""
    assert "[ÖLÇÜLMÜYOR]" in doc and "ag kesmek kapinin isi degil" in doc


# ===========================================================================
# B2 -- sahte bicim: gercek kutuphanenin IKINCI bicimi (bosluk suzgeci sonrasi LISTE)
# ===========================================================================


def test_b2_bosluk_suzgeci_sonrasi_liste_bicimi_de_kabul(tmp_path: Path) -> None:
    """rapidocr `main.py:181-189`: metni bos olan satirlari `filter_by_indices` ile eler; o yoldan
    donen `txts`/`scores` TUPLE degil LISTE, `boxes` fancy-index'li ndarray'dir. Implementer'in
    sahtesi hep tuple verir; motorun listeyi de kabul ettigi burada olculur (dolu ve tamamen suzulmus)."""
    boxes = np.asarray([[[1, 1], [9, 1], [9, 5], [1, 5]], [[1, 8], [9, 8], [9, 12], [1, 12]]], np.float32)[[1]]
    c = Cikti(boxes, ["kalan"], [0.7])
    [b] = motor(tmp_path, Fabrika(c)).recognize(kare(), OcrPreset.DIALOGUE)
    assert (b.text, b.confidence, b.bbox.x, b.bbox.y, b.bbox.w, b.bbox.h) == ("kalan", 0.7, 1, 8, 8, 4)
    hepsi_suzulmus = Cikti(np.zeros((2, 4, 2), np.float32)[[]], [], [])
    assert motor(tmp_path, Fabrika(hepsi_suzulmus)).recognize(kare(), OcrPreset.DIALOGUE) == []


def test_b2_gercek_cikti_nesnesinde_fazla_alanlar_sorun_degil(tmp_path: Path) -> None:
    """Gercek `RapidOCROutput` `img/word_results/elapse/viser` de tasir; Protocol uc alan ister."""

    class GercekGibi:
        img = np.zeros((4, 4, 3), np.uint8)
        word_results = (("", 1.0, None),)
        elapse = 0.01
        viser = None
        boxes = np.asarray([[[0, 0], [4, 0], [4, 4], [0, 4]]], np.float32)
        txts = ("a",)
        scores = (0.5,)

        def __len__(self) -> int:
            return 1

    [b] = motor(tmp_path, Fabrika(GercekGibi())).recognize(kare(), OcrPreset.DIALOGUE)  # type: ignore[arg-type]
    assert b.text == "a" and b.confidence == 0.5
