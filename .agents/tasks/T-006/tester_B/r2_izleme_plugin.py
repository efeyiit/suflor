"""TESTER-B tur 2 -- pytest eklentisi: `_k7_kanal_olcusu` cagri izi + logger sizinti izi.

(a) B2-2: `_k7_kanal_olcusu` toplama bittikten sonra bir sarmalayiciyla
    degistirilir; her cagri icin motorun sinifi, kod nesnesinin kimligi ve
    sonuc (gecti / hangi AssertionError mesaji) kaydedilir. Gercek motor ve
    7 sahte AYNI kod nesnesinden gecmeli; sahtelerin her biri BEKLENEN kanal
    mesajiyla dusmeli (`pytest.raises(AssertionError)` match'siz -- yanlis
    sebepten dusme burada gorunur).

(b) B2-3: her testten SONRA `RapidOCR` logger'inin seviye/propagate/handler
    durumu ve kok logger'in handler sayisi kaydedilir; oturum sonunda
    baslangica gore fark listelenir (handler sizintisi olcusu).

Kosum:
    PYTHONPATH=.agents/tasks/T-006/tester_B TB_IZ_CIKTI=<dosya> \
      python -m pytest tests/unit/ocr/test_rapid_engine.py -q -p no:cacheprovider -p r2_izleme_plugin
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any

import pytest

OLCU = "_k7_kanal_olcusu"
LOGGER_ADI = "RapidOCR"
KAYITLAR: list[dict[str, Any]] = []
LOGGER_IZI: list[dict[str, Any]] = []
_GUNCEL: dict[str, str] = {"nodeid": "?"}
_BASLANGIC: dict[str, Any] = {}


def _logger_durumu() -> dict[str, Any]:
    lg = logging.getLogger(LOGGER_ADI)
    kok = logging.getLogger()
    return {
        "RapidOCR.level": lg.level,
        "RapidOCR.propagate": lg.propagate,
        "RapidOCR.handlers": [type(h).__name__ for h in lg.handlers],
        "kok.level": kok.level,
        "kok.handlers": [type(h).__name__ for h in kok.handlers],
    }


def _sar(orig: Any) -> Any:
    def sarmal(m: Any, capfd: Any, caplog: Any) -> Any:
        kayit: dict[str, Any] = {
            "test": _GUNCEL["nodeid"].split("::")[-1],
            "motor": f"{type(m).__module__}.{type(m).__qualname__}",
            "kod": f"{os.path.basename(orig.__code__.co_filename)}:{orig.__code__.co_firstlineno}#{id(orig.__code__):x}",
        }
        try:
            r = orig(m, capfd, caplog)
        except AssertionError as e:
            kayit["sonuc"] = "AssertionError: " + (str(e).splitlines() or ["(mesajsiz)"])[0]
            KAYITLAR.append(kayit)
            raise
        kayit["sonuc"] = f"gecti ({len(r)} blok)"
        KAYITLAR.append(kayit)
        return r

    return sarmal


def pytest_collection_finish(session: pytest.Session) -> None:
    _BASLANGIC.update(_logger_durumu())
    yamalanan = set()
    for item in session.items:
        mod = getattr(item, "module", None)
        if mod is not None and hasattr(mod, OLCU) and id(mod) not in yamalanan:
            setattr(mod, OLCU, _sar(getattr(mod, OLCU)))
            yamalanan.add(id(mod))


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item: pytest.Item) -> Any:
    _GUNCEL["nodeid"] = item.nodeid
    yield


@pytest.hookimpl(hookwrapper=True, trylast=True)
def pytest_runtest_teardown(item: pytest.Item, nextitem: pytest.Item | None) -> Any:
    yield
    d = _logger_durumu()
    d["test"] = item.nodeid.split("::")[-1]
    LOGGER_IZI.append(d)


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    hedef = os.environ.get("TB_IZ_CIKTI")
    if not hedef:
        return
    son = _logger_durumu()
    farkli = [k for k in _BASLANGIC if _BASLANGIC[k] != son[k]]
    # testler arasinda RapidOCR'da handler kalan var mi?
    handlerli = [t["test"] for t in LOGGER_IZI if t["RapidOCR.handlers"]]
    with open(hedef, "w", encoding="utf-8") as f:
        f.write("# _k7_kanal_olcusu cagri izi (motor sinifi, kod nesnesi, sonuc)\n")
        for k in KAYITLAR:
            f.write(json.dumps(k, ensure_ascii=False) + "\n")
        f.write(f"\n# farkli kod nesnesi sayisi: {len({k['kod'] for k in KAYITLAR})}  (1 olmali)\n")
        f.write(f"# cagri sayisi: {len(KAYITLAR)}\n")
        f.write("\n# logger durumu -- oturum basi\n" + json.dumps(_BASLANGIC, ensure_ascii=False) + "\n")
        f.write("# logger durumu -- oturum sonu\n" + json.dumps(son, ensure_ascii=False) + "\n")
        f.write(f"# bas/son FARKLI alanlar: {farkli if farkli else 'yok'}\n")
        f.write(f"# test sonrasi RapidOCR'da handler kalan testler: {handlerli if handlerli else 'yok'}\n")
        f.write("\n# her test SONRASI RapidOCR (level, propagate, handlers) ve kok (level, handler sayisi)\n")
        for t in LOGGER_IZI:
            f.write(f"{t['test']:70s} RapidOCR=({t['RapidOCR.level']}, {t['RapidOCR.propagate']}, {t['RapidOCR.handlers']}) kok=({t['kok.level']}, {len(t['kok.handlers'])})\n")
