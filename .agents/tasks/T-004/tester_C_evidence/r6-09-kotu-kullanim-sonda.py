# -*- coding: utf-8 -*-
"""Tester-C, TUR 6 -- KOTU KULLANIM yuzeyi + K16'nin K28 SAG TARAF regresyonu.

Kosum:  python .agents/tasks/T-004/tester_C_evidence/r6-09-kotu-kullanim-sonda.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_KOK = Path(__file__).resolve().parents[4]
if str(_KOK) not in sys.path:
    sys.path.insert(0, str(_KOK))

from src.contracts.models import OcrPreset, Rect, TextBlock
from src.ocr.normalizer import _group, _Item, _normalize_impl, normalize
from src.ocr.presets import get_params


def blk(text, x, y, *, w=300, h=20, conf=0.9, mon=0, dpi=1.0):
    return TextBlock(
        text=text,
        bbox=Rect(x=x, y=y, w=w, h=h, monitor_index=mon, dpi_scale=dpi),
        confidence=conf,
    )


def basliki(s):
    print()
    print("=" * 78)
    print(s)
    print("=" * 78)


# ---------------------------------------------------------------------------
basliki("A. K28 SAG TARAF -- birlesik aday, HAM ilk satir h=0 (K16 sinifi)")
# ---------------------------------------------------------------------------
# Uzunluk sinirini ZORLA: 270 + 1 + 12 > 280 -> reason 'length'
UZ = "a" * 270
bl = [
    blk("Ada: " + UZ, 10, 0, w=300, h=20),   # idx0
    blk("keli-", 10, 25, w=300, h=0),        # idx1  HAM ilk satir h=0
    blk("me devam", 10, 30, w=300, h=20),    # idx2
]
segs = normalize(bl, OcrPreset.DIALOGUE)
print(f"  segment sayisi={len(segs)}")
for s in segs:
    print(f"    speaker={s.speaker!r:8s} text={s.text[:24]!r} source_blocks={s.source_blocks} bbox.h={s.bbox.h}")
print("  BEKLENTI (K16): birlesik aday bbox'i h=0'i GIZLEMEMELI -> ikinci speaker None")

print()
print("  -- kontrol: ayni sekil ama HAM ilk satir h=20 -> miras UYGULANMALI --")
bl2 = [
    blk("Ada: " + UZ, 10, 0, w=300, h=20),
    blk("keli-", 10, 25, w=300, h=20),
    blk("me devam", 10, 30, w=300, h=20),
]
segs2 = normalize(bl2, OcrPreset.DIALOGUE)
print(f"    speakers={[s.speaker for s in segs2]!r} source_blocks={[s.source_blocks for s in segs2]!r}")

print()
print("  -- kontrol: birlesik kutu ile bakilsaydi ne olurdu? --")
print("     birlesik aday bbox: y=25, h=min(0..)=?  -> union(y25 h0, y30 h20) = y25 h25")
print("     gap = 25 - 20 = 5 ; 0.8*min(20,25)=16 -> 5<16 -> MIRAS (YANLIS)")
print("     ham ilk satir h=0 -> ref_height=0 -> 'height' -> MIRAS YOK (DOGRU)")


# ---------------------------------------------------------------------------
basliki("B. `blocks=` GECIRILMEZSE: sessiz yanlis mi, gurultulu kirilma mi?")
# ---------------------------------------------------------------------------
params = get_params(OcrPreset.DIALOGUE)
it0 = _Item(text="a" * 270, bbox=Rect(x=10, y=0, w=300, h=20), speaker="Ada", source_blocks=(0,))
it1 = _Item(text="b" * 20, bbox=Rect(x=10, y=25, w=300, h=20), speaker=None, source_blocks=(1,))
print("  1) UZUNLUK siniri DOGAN dogrudan cagri, blocks= VERILMEDEN:")
try:
    _group([it0, it1], params)
    print("     ISTISNA YOK (!) -- sessiz yanlis")
except IndexError as exc:
    print(f"     IndexError: {exc}   (BILINCLI: gurultulu kirilir)")

print("  2) UZUNLUK siniri DOGMAYAN dogrudan cagri, blocks= VERILMEDEN:")
it2 = _Item(text="kisa", bbox=Rect(x=10, y=0, w=300, h=20), speaker="Ada", source_blocks=(0,))
it3 = _Item(text="metin", bbox=Rect(x=10, y=500, w=300, h=20), speaker=None, source_blocks=(1,))
try:
    cikti = _group([it2, it3], params)
    print(f"     calisti: {[(i.text, i.speaker) for i in cikti]!r}")
except IndexError as exc:
    print(f"     IndexError: {exc}")

print("  3) SUZULMUS blocks (indeks kaymasi) -- bir sonraki ajanin klasik hatasi:")
tam = [blk("x", 10, 0, h=20), blk("Ada: " + "a" * 270, 10, 25, h=20), blk("b" * 20, 10, 50, h=20)]
suzulmus = tam[1:]  # indeks 0 dusuruldu
items = [
    _Item(text="a" * 270, bbox=tam[1].bbox, speaker="Ada", source_blocks=(1,)),
    _Item(text="b" * 20, bbox=tam[2].bbox, speaker=None, source_blocks=(2,)),
]
try:
    dogru = _group(list(items), params, blocks=tam)
    print(f"     DOGRU (blocks=tam)      -> speakers={[i.speaker for i in dogru]!r}")
except Exception as exc:
    print(f"     DOGRU (blocks=tam)      -> {type(exc).__name__}: {exc}")
try:
    yanlis = _group(list(items), params, blocks=suzulmus)
    print(f"     YANLIS (blocks=suzulmus)-> speakers={[i.speaker for i in yanlis]!r}")
except Exception as exc:
    print(f"     YANLIS (blocks=suzulmus)-> {type(exc).__name__}: {exc}")


# ---------------------------------------------------------------------------
basliki("C. `_normalize_impl` / `apply_inheritance=False` KOTU KULLANIM yuzeyi")
# ---------------------------------------------------------------------------
import src.ocr.normalizer as N

print(f"  __all__ = {N.__all__!r}")
print(f"  'normalize' imzasi genel API'de mi degisti: "
      f"{__import__('inspect').signature(N.normalize)}")
print(f"  _normalize_impl imzasi: {__import__('inspect').signature(N._normalize_impl)}")
print(f"  _group imzasi:          {__import__('inspect').signature(N._group)}")
d = N._normalize_impl.__doc__ or ""
for anahtar in ("SADECE K23", "MAKINE DENETIMI", "DISARIYA", "SIZMAZ"):
    print(f"    docstring '{anahtar}' iceriyor mu: {anahtar in d}")

print()
print("  -- apply_inheritance=False URUNDE kullanilirsa ne kaybedilir? --")
bl = [blk("Ada: " + "a" * 270, 10, 0, h=20), blk("b" * 20, 10, 25, h=20)]
acik = _normalize_impl(bl, OcrPreset.DIALOGUE, apply_inheritance=True)
kapali = _normalize_impl(bl, OcrPreset.DIALOGUE, apply_inheritance=False)
print(f"    True : speakers={[s.speaker for s in acik]!r} source_blocks={[s.source_blocks for s in acik]!r}")
print(f"    False: speakers={[s.speaker for s in kapali]!r} source_blocks={[s.source_blocks for s in kapali]!r}")
print(f"    bolumleme BIREBIR ayni mi: "
      f"{[s.source_blocks for s in acik] == [s.source_blocks for s in kapali]}")


# ---------------------------------------------------------------------------
basliki("D. YALNIZ-ETIKET blogu OKUMA SIRASINDA SON olan sol taraf")
# ---------------------------------------------------------------------------
# `_extract_speakers` yalniz-etiket blogunun indeksini bir SONRAKI ogeye tasir.
# Sirasiz girdide o etiket blogu, tasiyan ogenin source_blocks'unda OKUMA
# SIRASINDA SON olabilir -> `_raw_query_pair`'in SOL tarafi ETIKET kutusunu alir.
UZ2 = "a" * 270
bl = [
    blk("勇者：", 10, 100, w=300, h=200),   # idx0: yalniz etiket, y=100, h=200 (ALTA uzaniyor)
    blk(UZ2, 10, 0, w=300, h=20),           # idx1: govde, y=0  (etiketin USTUNDE -- sirasiz)
    blk("b" * 20, 10, 305, w=300, h=20),    # idx2: devam
]
for preset in (OcrPreset.DIALOGUE, OcrPreset.TOOLTIP):
    segs = normalize(bl, preset)
    print(f"  {preset.value:9s} {[(s.speaker, s.source_blocks, s.text[:12]) for s in segs]!r}")
print("  (idx0 etiket kutusu bottom=300; govde idx1 bottom=20. SOL taraf hangisi?)")
print("  okuma sirasi (y,x,i): idx1(y=0) < idx0(y=100) -> SON = idx0 = ETIKET kutusu")
print("  etiket kutusuyla: gap = 305-300 = 5  < 0.8*20=16 -> MIRAS")
print("  govde kutusuyla : gap = 305-20  = 285 > 16       -> MIRAS YOK")


# ---------------------------------------------------------------------------
basliki("E. monitor_index / dpi_scale SINIRINI ASAN MIRAS")
# ---------------------------------------------------------------------------
UZ3 = "a" * 270
for ad, k1, k2 in (
    ("monitor 0 -> 1", dict(mon=0), dict(mon=1)),
    ("dpi 1.0 -> 2.0", dict(dpi=1.0), dict(dpi=2.0)),
):
    bl = [blk("Ada: " + UZ3, 10, 0, h=20, **k1), blk("b" * 20, 10, 25, h=20, **k2)]
    try:
        segs = normalize(bl, OcrPreset.DIALOGUE)
        print(f"  {ad:16s} UZUN metin (uzunluk siniri): speakers={[s.speaker for s in segs]!r} "
              f"bbox={[(s.bbox.monitor_index, s.bbox.dpi_scale) for s in segs]!r}")
    except ValueError as exc:
        print(f"  {ad:16s} UZUN metin: ValueError: {exc}")
    bl = [blk("Ada: kisa", 10, 0, h=20, **k1), blk("metin", 10, 25, h=20, **k2)]
    try:
        segs = normalize(bl, OcrPreset.DIALOGUE)
        print(f"  {ad:16s} KISA metin (birlesme denenir): speakers={[s.speaker for s in segs]!r}")
    except ValueError as exc:
        print(f"  {ad:16s} KISA metin: ValueError -> {str(exc)[:60]}...")

print()
print("SONDA BITTI.")
