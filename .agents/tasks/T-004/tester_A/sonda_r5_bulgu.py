# -*- coding: utf-8 -*-
"""TESTER-A · TUR 5 · yeniden uretilebilir sonda (pytest DISI, elle kosulur).

    python .agents/tasks/T-004/tester_A/sonda_r5_bulgu.py

Uc bolum:
  1. BULGU R5-1 -- uc geometrik yolun uctan-uca yeniden uretimi (`normalize`).
  2. K23 DEGISMEZI -- bu ajanin KENDI (hyphen-yogun) ureticisiyle bolumleme
     karsilastirmasi: 3200 girdi x 4 on ayar.
  3. K24'un ifadesinin HAM BLOK duzeyindeki makine denetimi + uctan-uca
     `speaker` etkisi (referans boru hatti: `tail` yerine grubun okuma
     sirasindaki SON HAM BLOGU).

`src/` ve `tests/` altina HICBIR SEY yazmaz; yalniz okur.
"""
from __future__ import annotations

import random
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from src.contracts.models import OcrPreset, Rect, Segment, TextBlock  # noqa: E402
from src.ocr.normalizer import (  # noqa: E402
    _PLACEHOLDER_PATTERN,
    _collapse_intraline,
    _extract_speakers,
    _group_rejection_reason,
    _is_noise,
    _Item,
    _merge_hyphenated,
    _normalize_impl,
    _union_rect,
    normalize,
)
from src.ocr.presets import NormalizerParams, get_params  # noqa: E402

GRUPLAYAN = (OcrPreset.DIALOGUE, OcrPreset.TOOLTIP, OcrPreset.SUBTITLE)
HEPSI = (OcrPreset.DIALOGUE, OcrPreset.MENU, OcrPreset.TOOLTIP, OcrPreset.SUBTITLE)


def items_of(blocks: list[TextBlock], params: NormalizerParams) -> list[_Item]:
    ordered = sorted(enumerate(blocks), key=lambda p: (p[1].bbox.y, p[1].bbox.x))
    items = [
        _Item(text=b.text, bbox=b.bbox, speaker=None, source_blocks=(i,))
        for i, b in ordered
        if b.confidence >= params.confidence_threshold
    ]
    items = [x for x in items if not _is_noise(x.text)]
    items = [replace(x, text=_collapse_intraline(x.text)) for x in items]
    return _extract_speakers(_merge_hyphenated(items))


def last_raw_rect(item: _Item, blocks: list[TextBlock]) -> Rect:
    idxs = sorted(item.source_blocks, key=lambda i: (blocks[i].bbox.y, blocks[i].bbox.x))
    return blocks[idxs[-1]].bbox


# ---------------------------------------------------------------- 1. BULGU R5-1
YOLLAR = {
    "A non-monotonik (bottom artifakti)": [
        TextBlock(text="Ada: " + "X" * 130, bbox=Rect(0, 0, 240, 18), confidence=0.9),
        TextBlock(text="Y" * 90 + " son-", bbox=Rect(0, 20, 240, 50), confidence=0.9),
        TextBlock(text="raki", bbox=Rect(0, 26, 240, 18), confidence=0.9),
        TextBlock(text="Z" * 140, bbox=Rect(0, 60, 240, 18), confidence=0.9),
    ],
    "B MONOTONIK (min(h) sismesi)": [
        TextBlock(text="Ada: " + "X" * 130, bbox=Rect(0, -20, 240, 18), confidence=0.9),
        TextBlock(text="Y" * 90 + " son-", bbox=Rect(0, 0, 240, 18), confidence=0.9),
        TextBlock(text="raki", bbox=Rect(0, 30, 240, 5), confidence=0.9),
        TextBlock(text="Z" * 140, bbox=Rect(0, 40, 240, 18), confidence=0.9),
    ],
    "C MONOTONIK (overlap+min(w) sismesi)": [
        TextBlock(text="Ada: " + "X" * 130, bbox=Rect(0, -20, 240, 18), confidence=0.9),
        TextBlock(text="Y" * 90 + " son-", bbox=Rect(0, 0, 240, 18), confidence=0.9),
        TextBlock(text="raki", bbox=Rect(300, 20, 8, 18), confidence=0.9),
        TextBlock(text="Z" * 140, bbox=Rect(0, 40, 240, 18), confidence=0.9),
    ],
}

print("=" * 78)
print("1. BULGU R5-1 -- hyphen-birlesik `tail`, GERCEK geometrik kopusu gizliyor")
print("=" * 78)
P = get_params(OcrPreset.DIALOGUE)
for ad, blocks in YOLLAR.items():
    items = items_of(blocks, P)
    tail, aday = items[1], items[2]
    ham = replace(tail, bbox=last_raw_rect(tail, blocks))
    current = _Item(
        text=items[0].text + " " + tail.text,
        bbox=_union_rect(items[0].bbox, tail.bbox),
        speaker=items[0].speaker,
        source_blocks=tuple(sorted((*items[0].source_blocks, *tail.source_blocks))),
    )
    segs = normalize(blocks, OcrPreset.DIALOGUE)
    off = _normalize_impl(blocks, OcrPreset.DIALOGUE, apply_inheritance=False)
    print(f"\n{ad}")
    print(f"  tail (adim 3'te birlesmis oge)   : src={tail.source_blocks} bbox={tail.bbox}")
    print(f"  grubun HAM son metin satiri      : bbox={ham.bbox}")
    print(f"  monotonik mi (bottom AYNI mi)    : {ham.bbox.bottom == tail.bbox.bottom}")
    print(f"  sinir sebebi (current, nxt)      : {_group_rejection_reason(current, aday, P)!r}")
    print(f"  KODUN sorgusu   (tail, nxt, ignore_length=True) : "
          f"{_group_rejection_reason(tail, aday, P, ignore_length=True)!r}   <- 'kopus YOK' (artifakt)")
    print(f"  K24 IFADESI (HAM son satir, nxt, ignore_length) : "
          f"{_group_rejection_reason(ham, aday, P, ignore_length=True)!r}  <- GERCEK kopus")
    print(f"  normalize()  src/speaker         : {[(s.source_blocks, s.speaker) for s in segs]}")
    print(f"  apply_inheritance=False          : {[(s.source_blocks, s.speaker) for s in off]}")
    print("  K19 tablosu 'geometrik bosluk -> None KALIR' ihlal edildi mi: "
          f"{segs[-1].speaker is not None}")

# ------------------------------------------------------------------- uretici
NAMES = ("Ada", "Bob", "勇者", "魔王", "村人", "Cem")
WORDS = ("bir", "cumle", "devam", "ediyor", "son-", "raki", "uzun-", "ca", "kelime",
         "こんにちは", "{0}", "%s", "well-known", "goz-", "lem")


def gen(rng: random.Random) -> list[TextBlock]:
    """Hyphen-YOGUN dagilim: adim 3'un COK BLOKLU oge uretmesini tetikler."""
    blocks = []
    y = rng.randint(-5, 20)
    for _ in range(rng.randint(3, 16)):
        h = rng.choice((3, 5, 8, 16, 18, 20, 24, 40))
        parts = [rng.choice(WORDS) for _ in range(rng.randint(2, 45))]
        if rng.random() < 0.30:
            parts[-1] = rng.choice(("son-", "uzun-", "goz-"))
        text = " ".join(parts)
        if rng.random() < 0.25:
            text = f"{rng.choice(NAMES)}{rng.choice((':', '：'))} {text}"
        blocks.append(TextBlock(
            text=text,
            bbox=Rect(x=rng.randint(-10, 60), y=y, w=rng.choice((8, 30, 120, 200, 240, 300)), h=h),
            confidence=rng.uniform(0.66, 1.0)))
        y += h + rng.choice((-4, 0, 1, 2, 3, 5, 8, 14, 30))
    return blocks


SEEDS = (11, 2027, 999983, 5150)
PER_SEED = 800


def derlem():
    for seed in SEEDS:
        rng = random.Random(seed)
        for _ in range(PER_SEED):
            yield gen(rng)


# ------------------------------------------------------------ 2. K23 DEGISMEZI
print()
print("=" * 78)
print("2. K23 DEGISMEZI -- KENDI (hyphen-yogun) ureticimle, 3200 girdi x 4 on ayar")
print("=" * 78)
girdi = kosum = fark = spk = 0
for blocks in derlem():
    girdi += 1
    for p in HEPSI:
        try:
            on = _normalize_impl(blocks, p, apply_inheritance=True)
            off = _normalize_impl(blocks, p, apply_inheritance=False)
        except (ValueError, TypeError):
            continue
        kosum += 1
        key = lambda ss: [(s.source_blocks, s.text, s.bbox, s.placeholders) for s in ss]  # noqa: E731
        if key(on) != key(off):
            fark += 1
        spk += sum(1 for a, b in zip(on, off) if a.speaker != b.speaker)
print(f"  girdi={girdi}  kosum={kosum}")
print(f"  BOLUMLEME FARKI (source_blocks/text/bbox/placeholders/sayi) = {fark}   <- 0 olmali")
print(f"  miras GERCEKTEN tetiklendi mi (speaker'i degisen segment)   = {spk}   <- totoloji degil")


# ------------------------------------------- 3. K24 makine denetimi + e2e etki
def group_ref(items, params, blocks):
    """K24'un ifadesinin HAM BLOK duzeyinde faithful uygulanisi."""
    if not items:
        return []
    groups, pure = [], []
    current = tail = items[0]
    for nxt in items[1:]:
        reason = _group_rejection_reason(current, nxt, params)
        if reason is None:
            current = _Item(text=current.text + " " + nxt.text,
                            bbox=_union_rect(current.bbox, nxt.bbox),
                            speaker=current.speaker,
                            source_blocks=tuple(sorted((*current.source_blocks, *nxt.source_blocks))))
            tail = nxt
        else:
            groups.append(current)
            ref_tail = replace(tail, bbox=last_raw_rect(tail, blocks))
            pure.append(reason == "length" and nxt.speaker is None
                        and _group_rejection_reason(ref_tail, nxt, params, ignore_length=True) is None)
            current = tail = nxt
    groups.append(current)
    for i, pl in enumerate(pure, start=1):
        if pl and groups[i - 1].speaker is not None:
            groups[i] = replace(groups[i], speaker=groups[i - 1].speaker)
    return groups


def norm_ref(blocks, preset):
    params = get_params(preset)
    items = items_of(blocks, params)
    grouped = group_ref(items, params, blocks) if params.should_group else items
    segs = [Segment(text=g.text, bbox=g.bbox, speaker=g.speaker,
                    placeholders=tuple(m.group(0) for m in _PLACEHOLDER_PATTERN.finditer(g.text)),
                    source_blocks=tuple(sorted(g.source_blocks))) for g in grouped if g.text.strip()]
    return sorted(segs, key=lambda s: (s.bbox.y, s.bbox.x))


print()
print("=" * 78)
print("3. K24'un ifadesi HAM BLOK duzeyinde tutuyor mu (makine denetimi + e2e)")
print("=" * 78)
sinir = ayr = mono = 0
ters = 0
e2e_seg = 0
e2e_girdi = 0
bol_farki = 0
girdi = 0
for blocks in derlem():
    girdi += 1
    kirli = False
    for p in GRUPLAYAN:
        params = get_params(p)
        items = items_of(blocks, params)
        if items:
            current = tail = items[0]
            for nxt in items[1:]:
                reason = _group_rejection_reason(current, nxt, params)
                if reason is None:
                    current = _Item(text=current.text + " " + nxt.text,
                                    bbox=_union_rect(current.bbox, nxt.bbox),
                                    speaker=current.speaker,
                                    source_blocks=tuple(sorted((*current.source_blocks, *nxt.source_blocks))))
                    tail = nxt
                else:
                    if reason == "length" and nxt.speaker is None:
                        sinir += 1
                        kod = _group_rejection_reason(tail, nxt, params, ignore_length=True) is None
                        lr = last_raw_rect(tail, blocks)
                        ham = _group_rejection_reason(replace(tail, bbox=lr), nxt, params,
                                                      ignore_length=True) is None
                        if kod and not ham:
                            ayr += 1
                            if lr.bottom >= tail.bbox.bottom:
                                mono += 1
                        elif ham and not kod:
                            ters += 1
                    current = tail = nxt
        kod_segs = normalize(blocks, p)
        ref_segs = norm_ref(blocks, p)
        if [s.source_blocks for s in kod_segs] != [s.source_blocks for s in ref_segs]:
            bol_farki += 1
        d = sum(1 for a, b in zip(kod_segs, ref_segs) if a.speaker != b.speaker)
        if d:
            kirli = True
            e2e_seg += d
    if kirli:
        e2e_girdi += 1
print(f"  girdi={girdi}  incelenen uzunluk-siniri={sinir}")
print(f"  kod MIRAS VER / HAM son satir MIRAS YOK = {ayr}  ({100.0 * ayr / sinir:.1f}%)   <- K19 tablosu ihlali")
print(f"    bunlardan MONOTONIK (bottom artifakti YOK, egzotik geometri GEREKMEZ) = {mono}")
print(f"  kod MIRAS YOK / HAM son satir MIRAS VER = {ters}")
print(f"  UCTAN UCA: speaker'i FARKLI cikan segment = {e2e_seg}, etkilenen girdi = {e2e_girdi}/{girdi}")
print(f"  UCTAN UCA: bolumleme farki = {bol_farki}   <- 0: bulgu K23'u IHLAL ETMIYOR, yalniz `speaker`i bozuyor")
