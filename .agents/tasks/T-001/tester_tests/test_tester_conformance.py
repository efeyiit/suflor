"""TESTER -- tasarim dokumani 5.3 ile birebir alan uyumu + saflik taramasi.

Bu dosyadaki beklenen alan adi/sirasi/tip listeleri, implementer'in test
dosyasi (tests/unit/contracts/test_models.py) OKUNMADAN, dogrudan
docs/superpowers/specs/2026-09-09-suflor-design.md #5.3'teki kod bloklarindan
tester tarafindan bagimsiz olarak transkribe edilmistir.

`TermHit` ve `Pair` icin: tasarim dokumani #5.3 kod blogu bu iki tipin tam
alan semasini VERMEZ (yalnizca adlarini ve kullanim baglamlarini verir --
5.1 tablosunda `GlossaryStore.lookup(text) -> list[TermHit]`, 4.1'de "TM
kaynak/hedef cifti"). Bu yuzden bu iki tip icin katı alan-listesi denetimi
YAPILMAZ; yalnizca var olduklari, frozen olduklari ve semantik olarak
kullanilabilir olduklari dogrulanir. Bu sinirlama verdict.md'de belirtilir.
"""
from __future__ import annotations

import ast
import dataclasses
from pathlib import Path
from typing import get_type_hints

import numpy as np
import pytest

from src.contracts.models import (
    Frame,
    ImageArray,
    OcrPreset,
    Pair,
    Rect,
    Segment,
    TermHit,
    TextBlock,
    TranslationRequest,
    TranslationResult,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
CONTRACTS_DIR = REPO_ROOT / "src" / "contracts"


# --------------------------------------------------------------------------
# 5.3'ten BAGIMSIZ transkribe edilmis beklenen alan adlari + sirasi
# --------------------------------------------------------------------------

EXPECTED_ORDER: dict[type, tuple[str, ...]] = {
    Rect: ("x", "y", "w", "h", "monitor_index", "dpi_scale"),
    Frame: ("image", "rect", "captured_at", "seq"),
    TextBlock: ("text", "bbox", "confidence", "line_boxes"),
    Segment: ("text", "bbox", "speaker", "placeholders", "source_blocks"),
    TranslationRequest: (
        "segments", "source_lang", "target_lang", "glossary_hits",
        "tm_examples", "style_profile", "image_crops",
    ),
    TranslationResult: (
        "translations", "provider_id", "latency_ms", "from_cache",
        "detected_lang", "partial",
    ),
}


@pytest.mark.parametrize(("model", "expected"), list(EXPECTED_ORDER.items()),
                         ids=[m.__name__ for m in EXPECTED_ORDER])
def test_field_names_and_order_match_design_doc_exactly(
    model: type, expected: tuple[str, ...]
) -> None:
    actual = tuple(f.name for f in dataclasses.fields(model))
    missing = set(expected) - set(actual)
    extra = set(actual) - set(expected)
    assert not missing, f"{model.__name__}: eksik alan(lar): {missing}"
    assert not extra, f"{model.__name__}: fazladan uydurulmus alan(lar): {extra}"
    assert actual == expected, (
        f"{model.__name__}: sira farkli -- beklenen {expected}, "
        f"bulunan {actual}"
    )


def test_all_eight_packet_models_exist() -> None:
    """packet.md: Rect, Frame, TextBlock, Segment, TermHit, Pair,
    TranslationRequest, TranslationResult -- hepsi models.py'de var mi?"""
    from src.contracts import models as models_module
    for name in ("Rect", "Frame", "TextBlock", "Segment", "TermHit", "Pair",
                 "TranslationRequest", "TranslationResult"):
        assert hasattr(models_module, name), f"eksik model: {name}"
        cls = getattr(models_module, name)
        assert dataclasses.is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True  # type: ignore[attr-defined]


# --------------------------------------------------------------------------
# TermHit / Pair: sema tasarim dokumaninda sabitlenmemis -- yalnizca varlik +
# frozen + kullanilabilirlik (5.1 / 4.1 baglamina uygunluk) dogrulanir.
# --------------------------------------------------------------------------

def test_term_hit_is_frozen_and_usable_as_glossary_lookup_result() -> None:
    """5.1: `GlossaryStore.lookup(text) -> list[TermHit]` -- bir liste
    icinde tasinabilecek, kaynak/hedef terim eslemesi tasiyan bir tip olmali."""
    assert dataclasses.is_dataclass(TermHit)
    assert TermHit.__dataclass_params__.frozen is True  # type: ignore[attr-defined]
    field_names = {f.name for f in dataclasses.fields(TermHit)}
    # Bir "terim eslemesi" en azindan kaynak ve hedef terimi tasimali.
    assert any("source" in n or "term" in n for n in field_names), (
        f"TermHit alanlarinda kaynak terime dair bir alan bulunamadi: "
        f"{field_names}"
    )
    assert any("target" in n for n in field_names), (
        f"TermHit alanlarinda hedef terime dair bir alan bulunamadi: "
        f"{field_names}"
    )


def test_pair_is_frozen_and_usable_as_tm_example() -> None:
    """4.1: TM ciftleri "kaynak/hedef" olarak taniml ve few-shot ornek olarak
    motora verilir; `tm_examples: tuple[Pair, ...]` alaninda kullanilir."""
    assert dataclasses.is_dataclass(Pair)
    assert Pair.__dataclass_params__.frozen is True  # type: ignore[attr-defined]
    field_names = {f.name for f in dataclasses.fields(Pair)}
    assert "source" in field_names, f"Pair'de 'source' alani yok: {field_names}"
    assert "target" in field_names, f"Pair'de 'target' alani yok: {field_names}"
    # TranslationRequest.tm_examples icinde fiilen kullanilabiliyor mu?
    pair = Pair(source="hello", target="merhaba")
    req = TranslationRequest(segments=(), source_lang="en", target_lang="tr",
                             tm_examples=(pair,))
    assert req.tm_examples == (pair,)


# --------------------------------------------------------------------------
# image_crops: paket kritik kisit #4 -- bugun eklenmeli, None olabilmeli
# --------------------------------------------------------------------------

def test_image_crops_field_exists_on_translation_request() -> None:
    names = {f.name for f in dataclasses.fields(TranslationRequest)}
    assert "image_crops" in names


def test_image_crops_defaults_to_none() -> None:
    req = TranslationRequest(segments=(), source_lang=None, target_lang="tr")
    assert req.image_crops is None


def test_image_crops_type_hint_is_optional_tuple_of_arrays() -> None:
    hints = get_type_hints(TranslationRequest)
    assert hints["image_crops"] == (tuple[ImageArray, ...] | None)


def test_image_crops_accepts_none_explicitly() -> None:
    req = TranslationRequest(segments=(), source_lang=None, target_lang="tr",
                             image_crops=None)
    assert req.image_crops is None


def test_image_crops_accepts_populated_tuple() -> None:
    crops = (np.zeros((4, 4, 3), dtype=np.uint8),
              np.ones((4, 4, 3), dtype=np.uint8))
    req = TranslationRequest(segments=(), source_lang=None, target_lang="tr",
                             image_crops=crops)
    assert req.image_crops is not None
    assert len(req.image_crops) == 2


# --------------------------------------------------------------------------
# OcrPreset: 3.2'deki dort deger (implementer'in kendi testinden BAGIMSIZ
# olarak tasarim dokumanindan tekrar transkribe edilmistir)
# --------------------------------------------------------------------------

def test_ocr_preset_has_exactly_the_four_documented_values() -> None:
    expected = {"dialogue", "menu", "tooltip", "subtitle"}
    actual = {p.value for p in OcrPreset}
    assert actual == expected


def test_ocr_preset_rejects_undocumented_value() -> None:
    with pytest.raises(ValueError):
        OcrPreset("boyle_bir_sey_yok")


# --------------------------------------------------------------------------
# SAFLIK: env.md #5 -- purity_check.py'nin AST import taramasini atlatan
# dinamik import / eval / exec kaliplarini GOZLE + REGEX ile tara. Bu,
# purity_check.py'nin kendisinden BAGIMSIZ, ikinci bir yontemdir.
# --------------------------------------------------------------------------

DYNAMIC_BYPASS_MARKERS = (
    "importlib", "__import__", "eval(", "exec(", "compile(",
)


def _contracts_source_files() -> list[Path]:
    files = sorted(CONTRACTS_DIR.glob("*.py"))
    assert files, f"{CONTRACTS_DIR} altinda .py bulunamadi"
    return files


@pytest.mark.parametrize("py_file", _contracts_source_files(),
                         ids=lambda p: p.name)
def test_no_dynamic_import_bypass_markers_in_source_text(py_file: Path) -> None:
    """purity_check.py yalnizca `ast.Import`/`ast.ImportFrom` dugumlerine
    bakar. `__import__("torch")` gibi bir cagri BUNLARDAN biri DEGILDIR ve
    AST taramasini sessizce atlatabilir. Burada ham metin uzerinde ikinci
    bir (regex tabanli) tarama yapiyoruz."""
    text = py_file.read_text(encoding="utf-8")
    found = [m for m in DYNAMIC_BYPASS_MARKERS if m in text]
    assert not found, (
        f"{py_file.name} icinde dinamik import/eval/exec izi bulundu: {found}"
    )


@pytest.mark.parametrize("py_file", _contracts_source_files(),
                         ids=lambda p: p.name)
def test_ast_has_no_call_nodes_to_import_builtins(py_file: Path) -> None:
    """AST duzeyinde: `__import__(...)`, `eval(...)`, `exec(...)` fonksiyon
    CAGRISI (import statement'i degil) var mi -- bu purity_check.py'nin
    hicbir sekilde bakmadigi bir dugum turudur."""
    tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
    banned_call_names = {"__import__", "eval", "exec", "compile"}
    offending: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in banned_call_names:
                offending.append(f"{func.id}() @ line {node.lineno}")
            if isinstance(func, ast.Attribute) and func.attr in {
                "import_module", "reload",
            }:
                offending.append(f"importlib.{func.attr}() @ line {node.lineno}")
    assert not offending, f"{py_file.name}: {offending}"


def test_purity_check_script_itself_reports_zero_violations() -> None:
    """Kabul komutu #3'un cikis kodunu (0=temiz) tekrar, bagimsiz olarak
    dogrudan modul import ederek degil, alt-surec olarak calistirip
    dogrula (delivery.md / evidence/ okunmadan -- yalnizca komutun
    kendisi calistirilir)."""
    import subprocess
    import sys as _sys

    result = subprocess.run(
        [_sys.executable, str(REPO_ROOT / ".agents" / "tasks" / "T-001" /
                              "purity_check.py")],
        cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, (
        f"purity_check.py basarisiz -- stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
    assert "TEMIZ" in result.stdout
