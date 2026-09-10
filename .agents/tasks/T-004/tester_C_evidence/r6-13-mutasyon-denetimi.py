# -*- coding: utf-8 -*-
"""Tester-C, TUR 6 -- MUTASYON DENETIMI: yeni testler TOTOLOJI mi?

`src/` HIC DEGISTIRILMEDEN, `src.ocr.normalizer` modul globalleri
monkeypatch ile mutasyona ugratilir ve `tester_C/test_tur6_sinir_dil.py`
her mutanta karsi kosulur. Bir mutant HICBIR testi kirmiyorsa o mutantin
kapsadigi sinif icin sondam DISSIZDIR.

Kosum:  python .agents/tasks/T-004/tester_C_evidence/r6-13-mutasyon-denetimi.py
"""
from __future__ import annotations

import io
import sys
from contextlib import redirect_stdout
from dataclasses import replace
from pathlib import Path

_KOK = Path(__file__).resolve().parents[4]
if str(_KOK) not in sys.path:
    sys.path.insert(0, str(_KOK))

import pytest

import src.ocr.normalizer as N

HEDEF = str(_KOK / ".agents" / "tasks" / "T-004" / "tester_C" / "test_tur6_sinir_dil.py")

_ORIJINAL_RQP = N._raw_query_pair
_ORIJINAL_GROUP = N._group


# --- MC1: okuma sirasi yerine INDEKS sirasi (kararin M4 sinifi) ------------
def mc1(tail, nxt, blocks):
    return (
        replace(tail, bbox=blocks[max(tail.source_blocks)].bbox),
        replace(nxt, bbox=blocks[min(nxt.source_blocks)].bbox),
    )


# --- MC2: K28 ONCESI davranis -- ham ikame YOK (birlesik _Item kalir) -----
def mc2(tail, nxt, blocks):
    return (tail, nxt)


# --- MC3: SAG tarafi `nxt` birakan (kararin M5 sinifi) --------------------
def mc3(tail, nxt, blocks):
    sol, _ = _ORIJINAL_RQP(tail, nxt, blocks)
    return (sol, nxt)


# --- MC4: ham ikameyi `monitor_index == 0`a KAPILAYAN ---------------------
def mc4(tail, nxt, blocks):
    if blocks and blocks[0].bbox.monitor_index != 0:
        return (tail, nxt)
    return _ORIJINAL_RQP(tail, nxt, blocks)


# --- MC5: ham ikameyi `dpi_scale == 1.0`a KAPILAYAN -----------------------
def mc5(tail, nxt, blocks):
    if blocks and blocks[0].bbox.dpi_scale != 1.0:
        return (tail, nxt)
    return _ORIJINAL_RQP(tail, nxt, blocks)


# --- MC6: gorunum gecisini TERS yonde isleyen (kararin M11 sinifi) --------
def mc6_group(items, params, *, blocks=(), apply_inheritance=True):
    if not items:
        return []
    groups = []
    saf_uzunluk = []
    current = items[0]
    tail = items[0]
    for nxt in items[1:]:
        reason = N._group_rejection_reason(current, nxt, params)
        if reason is None:
            current = N._Item(
                text=current.text + " " + nxt.text,
                bbox=N._union_rect(current.bbox, nxt.bbox),
                speaker=current.speaker,
                source_blocks=tuple(sorted((*current.source_blocks, *nxt.source_blocks))),
            )
            tail = nxt
        else:
            groups.append(current)
            saf_uzunluk.append(
                reason == "length"
                and nxt.speaker is None
                and N._group_rejection_reason(
                    *N._raw_query_pair(tail, nxt, blocks), params, ignore_length=True
                )
                is None
            )
            current = nxt
            tail = nxt
    groups.append(current)
    if apply_inheritance:
        # MUTASYON: dongu TERS yonde -> zincirleme miras kirilir
        for i in reversed(range(1, len(saf_uzunluk) + 1)):
            if saf_uzunluk[i - 1] and groups[i - 1].speaker is not None:
                groups[i] = replace(groups[i], speaker=groups[i - 1].speaker)
    return groups


# --- MC7: ad suzgecini ASCII'ye KAPILAYAN (dil yuzeyi) --------------------
_ORIJINAL_SPLIT = N._split_speaker_label


def mc7_split(text):
    isim, kalan = _ORIJINAL_SPLIT(text)
    if isim is not None and not isim.isascii():
        return None, text
    return isim, kalan


MUTANTLAR = [
    ("MC1 indeks sirasi (M4 sinifi)", "_raw_query_pair", mc1),
    ("MC2 ham ikame YOK (K28 oncesi)", "_raw_query_pair", mc2),
    ("MC3 sag taraf `nxt` kalir (M5)", "_raw_query_pair", mc3),
    ("MC4 ikame monitor_index==0'a kapili", "_raw_query_pair", mc4),
    ("MC5 ikame dpi_scale==1.0'a kapili", "_raw_query_pair", mc5),
    ("MC6 gorunum gecisi TERS yon (M11)", "_group", mc6_group),
    ("MC7 ad suzgeci ASCII'ye kapili", "_split_speaker_label", mc7_split),
]


def kos() -> tuple[int, int]:
    tampon = io.StringIO()
    with redirect_stdout(tampon):
        kod = pytest.main([HEDEF, "-q", "--no-header", "-p", "no:cacheprovider"])
    cikti = tampon.getvalue()
    son = [s for s in cikti.splitlines() if "passed" in s or "failed" in s or "error" in s]
    return kod, son[-1] if son else "(ozet yok)"


print("TABAN (mutasyonsuz):")
kod, ozet = kos()
print(f"  exit={kod}  {ozet}")
print()

for ad, nitelik, yeni in MUTANTLAR:
    orijinal = getattr(N, nitelik)
    setattr(N, nitelik, yeni)
    try:
        kod, ozet = kos()
    finally:
        setattr(N, nitelik, orijinal)
    durum = "KIRILDI (iyi)" if kod != 0 else "GECTI  (DISSIZ!)"
    print(f"  {ad:38s} exit={kod}  {durum}   {ozet}")

print()
print("MUTASYON DENETIMI BITTI.")
