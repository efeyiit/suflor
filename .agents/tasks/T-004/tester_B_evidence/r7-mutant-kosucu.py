"""T7-2 DIS DENETIMI: `params` mutantlarini KENDIM kurup testin dustugunu olcerim.

Mutant `src/`'ye YAZILMAZ: normalizer'in KAYNAK METNI okunur, miras-sorgusu
cagri noktasi metinsel olarak degistirilir, sonuc BELLEKTE bir modul olarak
derlenip `sys.modules["src.ocr.normalizer"]`e KONUR. Calisma agaci TEMIZ kalir
(kosum sonunda `git status` ile dogrulanir).

Kullanim:  python r7-mutant-kosucu.py <mutant-adi>
"""
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

KOK = Path(__file__).resolve()
while not (KOK / ".agents").is_dir():
    KOK = KOK.parent
KIT = KOK / ".agents" / "tasks" / "T-004"
for _y in (str(KOK), str(KIT)):
    if _y not in sys.path:
        sys.path.insert(0, _y)

NORM = KOK / "src" / "ocr" / "normalizer.py"

# Miras-uygunluk sorgusunun cagri noktasi (tek gecis, birebir).
ORIJ = "*_raw_query_pair(tail, nxt, blocks), params, ignore_length=True"

MUTANTLAR: dict[str, tuple[str, str]] = {
    "TEMIZ": (ORIJ, "(mutasyon YOK -- kontrol kosumu)"),
    "M15-a": (
        "*_raw_query_pair(tail, nxt, blocks), get_params(OcrPreset.TOOLTIP), ignore_length=True",
        "sorgu SABIT tooltip params ile soruluyor",
    ),
    "M15-b": (
        "*_raw_query_pair(tail, nxt, blocks), replace(params, max_vertical_gap_ratio=0.3), "
        "ignore_length=True",
        "sorgu ICINDE esik IKAMESI (deger DEGISIR)",
    ),
    "M15-c": (
        "*_raw_query_pair(tail, nxt, blocks), get_params(OcrPreset.DIALOGUE), ignore_length=True",
        "sorgu SABIT dialogue params ile soruluyor (KARARIN M15 TARIFI birebir)",
    ),
    "M15-d": (
        "*_raw_query_pair(tail, nxt, blocks), "
        "replace(params, max_vertical_gap_ratio=params.max_vertical_gap_ratio), "
        "ignore_length=True",
        "sorgu ICINDE `replace` -- DEGERLER AYNI, NESNE BASKA (salt-kimlik mutanti)",
    ),
}


def mutant_modul_kur(ad: str) -> str:
    kaynak = NORM.read_text(encoding="utf-8")
    yeni, aciklama = MUTANTLAR[ad]
    if yeni != ORIJ:
        if kaynak.count(ORIJ) != 1:
            raise SystemExit(f"cagri noktasi {kaynak.count(ORIJ)} kez bulundu -- 1 bekleniyordu")
        kaynak = kaynak.replace(ORIJ, yeni)
    import src.ocr  # paket; alt modulu BIZ koyacagiz
    mod = types.ModuleType("src.ocr.normalizer")
    mod.__file__ = str(NORM)
    mod.__package__ = "src.ocr"
    sys.modules["src.ocr.normalizer"] = mod
    exec(compile(kaynak, str(NORM), "exec"), mod.__dict__)
    src.ocr.normalizer = mod  # type: ignore[attr-defined]
    return aciklama


def test_modulu_yukle() -> types.ModuleType:
    yol = KOK / "tests" / "unit" / "ocr" / "test_normalizer.py"
    spec = importlib.util.spec_from_file_location("t7_test_normalizer", yol)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    ad = sys.argv[1]
    aciklama = mutant_modul_kur(ad)
    tm = test_modulu_yukle()

    # --- 1) SEFIN/IMPLEMENTER'IN testi (iki yonlu) --------------------------
    try:
        tm.test_k28_miras_sorgusu_ayni_params_ile_sorulur()
        gercek = "GECTI"
        detay = ""
    except AssertionError as e:
        gercek = "DUSTU"
        detay = str(e).strip().splitlines()[0][:150]

    # --- 2) ABLASYON: YALNIZ-`dialogue` bir test bunu yakalar miydi? --------
    #     (implementer'in "sefin olcusunde boşluk var" iddiasinin olcusu)
    ablasyon = yalniz_dialogue_ablasyonu(tm)

    print(f"{ad:8s} | test={gercek:6s} | yalniz-dialogue ablasyonu={ablasyon:6s} | {aciklama}")
    if detay:
        print(f"         `-> {detay}")
    return 0


def yalniz_dialogue_ablasyonu(tm: types.ModuleType) -> str:
    """Testin YALNIZCA `dialogue` yonu yazilsaydi mutant yakalanir miydi?

    Testin uc assert ailesini birebir tekrarlar, ama TEK on ayarla."""
    from src.contracts.models import OcrPreset
    from src.ocr.presets import get_params
    params = get_params(OcrPreset.DIALOGUE)
    blocks = [
        tm.blk("Ada: " + "X" * 150, 0, 0, w=240, h=18),
        tm.blk("Y" * 150, 0, 30, w=240, h=18),
    ]
    try:
        out, miras, gorulen = tm._t72_params_sondasi(blocks, OcrPreset.DIALOGUE)
        assert [s.source_blocks for s in out] == [(0,), (1,)]
        assert [s.speaker for s in out] == ["Ada", "Ada"]          # aile 1
        assert len(miras) == 1                                      # aile 2
        assert (miras[0].sol_bbox, miras[0].sag_bbox) == (blocks[0].bbox, blocks[1].bbox)
        assert gorulen and all(p is params for p in gorulen)        # aile 3
        return "GECTI"
    except AssertionError:
        return "DUSTU"


if __name__ == "__main__":
    raise SystemExit(main())
