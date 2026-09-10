# -*- coding: utf-8 -*-
"""Tester-C, TUR 6 -- sefin "kit URETMIYOR" dedigi BES girdi sinifinin sondasi.

M14 (sef_karari-tur6.md, "bilinen sinirlar" tablosu): emoji/astral + ZWJ,
`monitor_index != 0`, `dpi_scale != 1.0`, >=40 bloklu girdi, ASCII-disi
konusmaci adi. Besi de olcu kitine VE 1174 kor teste gorunmez.

Kosum:  python .agents/tasks/T-004/tester_C_evidence/r6-07-bes-girdi-sinifi-sonda.py
"""
from __future__ import annotations

import random
import sys
import unicodedata
from pathlib import Path

_KOK = Path(__file__).resolve().parents[4]
if str(_KOK) not in sys.path:
    sys.path.insert(0, str(_KOK))

from src.contracts.models import OcrPreset, Rect, TextBlock
from src.ocr.normalizer import (
    _group,
    _Item,
    _group_rejection_reason,
    _normalize_impl,
    _raw_query_pair,
    _split_speaker_label,
    normalize,
)
from src.ocr.presets import get_params

PRESETS = [OcrPreset.DIALOGUE, OcrPreset.TOOLTIP, OcrPreset.SUBTITLE, OcrPreset.MENU]


def blk(text, x, y, *, w=300, h=20, conf=0.9, mon=0, dpi=1.0):
    return TextBlock(
        text=text,
        bbox=Rect(x=x, y=y, w=w, h=h, monitor_index=mon, dpi_scale=dpi),
        confidence=conf,
    )


def bol(blocks, preset):
    """Bolumleme imzasi: (source_blocks, speaker) listesi."""
    return [(s.source_blocks, s.speaker) for s in normalize(blocks, preset)]


def basliki(s):
    print()
    print("=" * 78)
    print(s)
    print("=" * 78)


# ---------------------------------------------------------------------------
basliki("1. EMOJI / ASTRAL / ZWJ")
# ---------------------------------------------------------------------------

ORNEKLER = [
    ("tek emoji U+1F44D", "\U0001F44D"),
    ("ZWJ aile (5 cp)", "\U0001F468‍\U0001F469‍\U0001F467"),
    ("bayrak TR (2 cp)", "\U0001F1F9\U0001F1F7"),
    ("varyasyon secici gunes (2 cp)", "☀️"),
    ("varyasyon secicisiz gunes (1 cp)", "☀"),
    ("astral CJK ext-B (1 cp)", "\U0002000B"),
    ("astral matematiksel bold A (1 cp)", "\U0001D400"),
    ("ten tonlu el (2 cp)", "\U0001F44B\U0001F3FB"),
    ("keycap 1 (3 cp)", "1️⃣"),
]
for ad, metin in ORNEKLER:
    cikti = normalize([blk(metin, 10, 10)], OcrPreset.MENU)
    cats = " ".join(unicodedata.category(c) for c in metin)
    print(
        f"  {ad:34s} len={len(metin)} kat=[{cats:20s}] -> "
        f"{'KORUNDU' if cikti else 'SILINDI':8s} {[s.text for s in cikti]!r}"
    )

print()
print("  -- ZWJ dizisi codepoint SAYISI max_group_chars'i sisiriyor mu? --")
AILE = "\U0001F468‍\U0001F469‍\U0001F467"  # 5 cp, 1 grapheme
# TOOLTIP max_group_chars=200. 20 aile = 100 grapheme ama 100 codepoint.
for tekrar in (20, 45):
    metin_a = AILE * tekrar          # 5*tekrar codepoint
    metin_b = "x" * tekrar           # tekrar codepoint, AYNI grapheme sayisi
    a = normalize([blk("Ada: " + metin_a, 10, 0), blk(metin_a, 10, 25)], OcrPreset.TOOLTIP)
    b = normalize([blk("Ada: " + metin_b, 10, 0), blk(metin_b, 10, 25)], OcrPreset.TOOLTIP)
    print(
        f"    tekrar={tekrar:3d}  ZWJ(cp={len(metin_a):3d}): {len(a)} segment  |  "
        f"ASCII(cp={len(metin_b):3d}, AYNI grapheme): {len(b)} segment"
    )

print()
print("  -- emoji/astral KONUSMACI ADI olarak --")
for ad_metni in (
    "\U0001F468: merhaba",
    "\U0001D400\U0001D401: merhaba",  # astral matematiksel bold AB
    "\U0002000B: merhaba",            # astral kanji
    "Ada\U0001F44D: merhaba",
):
    isim, kalan = _split_speaker_label(ad_metni)
    print(f"    {ad_metni!r:34s} -> speaker={isim!r} kalan={kalan!r}")

print()
print("  -- yalniz vekil (lone surrogate) -- UTF-16 tabanli motorun uretebilecegi --")
try:
    yalniz_vekil = "\ud83d"
    cikti = normalize([blk(yalniz_vekil, 10, 10), blk(yalniz_vekil + "abc", 10, 40)], OcrPreset.MENU)
    print(f"    cokme YOK; cikti={[s.text for s in cikti]!r}")
except Exception as exc:  # pragma: no cover
    print(f"    ISTISNA: {type(exc).__name__}: {exc}")

print()
print("  -- emoji ile MIRAS: speaker codepoint duzeyinde korunuyor mu? --")
UZUN = "あ" * 150
cikti = normalize(
    [blk("勇者：" + UZUN, 10, 0, h=20), blk(UZUN, 10, 25, h=20)],
    OcrPreset.DIALOGUE,
)
print(f"    segment sayisi={len(cikti)} speaker'lar={[s.speaker for s in cikti]!r}")
print(
    "    codepoint'ler:",
    [[hex(ord(c)) for c in (s.speaker or "")] for s in cikti],
)


# ---------------------------------------------------------------------------
basliki("2. monitor_index != 0")
# ---------------------------------------------------------------------------

rng = random.Random(20250910)


def derlem(n, *, mon=0, dpi=1.0, tohum=1):
    r = random.Random(tohum)
    bl = []
    y = 0
    for i in range(n):
        metin = ("Ada: " if i % 5 == 0 else "") + "kelime" * r.randint(1, 12)
        h = r.choice([12, 18, 20, 30])
        bl.append(blk(metin, r.choice([10, 12, 15]), y, w=r.choice([200, 300, 320]), h=h, mon=mon, dpi=dpi))
        y += h + r.choice([2, 5, 9, 40])
    r.shuffle(bl)
    return bl


print("  -- monitor_index BLOK BASINA SABIT: bolumleme monitor 0 ile AYNI mi? --")
for mon in (0, 1, 7, -3):
    for preset in PRESETS:
        a = bol(derlem(30, mon=0, tohum=5), preset)
        b = bol(derlem(30, mon=mon, tohum=5), preset)
        if a != b:
            print(f"    AYRISMA mon={mon} preset={preset}")
            break
    else:
        continue
    break
else:
    print("    dort on ayar x mon in (0,1,7,-3): AYRISMA YOK (monitor_index atil)")

print()
print("  -- Segment.bbox monitor_index'i TASIYOR mu (birlesmis segmentte)? --")
cikti = normalize([blk("Ada: bir", 10, 0, mon=4), blk("iki", 10, 25, mon=4)], OcrPreset.DIALOGUE)
for s in cikti:
    print(f"    text={s.text!r} bbox.monitor_index={s.bbox.monitor_index} dpi={s.bbox.dpi_scale}")

print()
print("  -- KARISIK monitor: BIRLESEN cift -> ValueError bekleniyor (K10) --")
try:
    normalize([blk("Ada: bir", 10, 0, mon=0), blk("iki", 10, 25, mon=1)], OcrPreset.DIALOGUE)
    print("    ValueError YOK (!)")
except ValueError as exc:
    print(f"    ValueError: {exc}")

print()
print("  -- KARISIK monitor: BIRLESMEYEN ama UZUNLUK sinirinda kalan cift --")
UZ = "a" * 200
mixed = [blk("Ada: " + UZ, 10, 0, h=20, mon=0), blk(UZ, 10, 25, h=20, mon=1)]
try:
    cikti = normalize(mixed, OcrPreset.DIALOGUE)
    print(f"    ValueError YOK; segment sayisi={len(cikti)}")
    for s in cikti:
        print(
            f"      speaker={s.speaker!r} monitor={s.bbox.monitor_index} "
            f"source_blocks={s.source_blocks}"
        )
except ValueError as exc:
    print(f"    ValueError: {exc}")

print("    (AYNI cift, metin KISA -> birlesme denenir):")
try:
    cikti = normalize([blk("Ada: bir", 10, 0, mon=0), blk("iki", 10, 25, mon=1)], OcrPreset.DIALOGUE)
    print(f"      ValueError YOK; {[(s.text, s.speaker) for s in cikti]}")
except ValueError as exc:
    print(f"      ValueError: {exc}")


# ---------------------------------------------------------------------------
basliki("3. dpi_scale != 1.0")
# ---------------------------------------------------------------------------

print("  -- dpi_scale BLOK BASINA SABIT: bolumleme dpi=1.0 ile AYNI mi? --")
ayrisan = []
for dpi in (1.0, 1.25, 1.5, 2.0, 0.5):
    for preset in PRESETS:
        a = bol(derlem(30, dpi=1.0, tohum=7), preset)
        b = bol(derlem(30, dpi=dpi, tohum=7), preset)
        if a != b:
            ayrisan.append((dpi, preset))
print(f"    ayrisan (dpi, preset) ciftleri: {ayrisan if ayrisan else 'YOK (dpi_scale atil)'}")

print()
print("  -- GEOMETRI dpi ile OLCEKLENIRSE bolumleme degisiyor mu? (oran tabanli olmali) --")


def olcekle(blocks, k):
    return [
        TextBlock(
            text=b.text,
            bbox=Rect(
                x=b.bbox.x * k,
                y=b.bbox.y * k,
                w=b.bbox.w * k,
                h=b.bbox.h * k,
                monitor_index=b.bbox.monitor_index,
                dpi_scale=float(k),
            ),
            confidence=b.confidence,
        )
        for b in blocks
    ]


taban = derlem(30, tohum=11)
for k in (2, 3, 4):
    farkli = [p for p in PRESETS if bol(taban, p) != bol(olcekle(taban, k), p)]
    print(f"    k={k}: bolumleme farkli olan on ayarlar -> {farkli if farkli else 'YOK'}")

print()
print("  -- NaN dpi_scale: IKI blok da AYNI NaN tasiyor --")
nan = float("nan")
try:
    cikti = normalize([blk("Ada: bir", 10, 0, dpi=nan), blk("iki", 10, 25, dpi=nan)], OcrPreset.DIALOGUE)
    print(f"    ValueError YOK; {[(s.text, s.speaker) for s in cikti]}")
except ValueError as exc:
    print(f"    ValueError: {exc}")
print("    (K7'nin confidence NaN mesaji ile karsilastir:)")
try:
    normalize([blk("x", 10, 0, conf=nan)], OcrPreset.DIALOGUE)
except ValueError as exc:
    print(f"      {exc}")

print()
print("  -- dpi_scale int 1 vs float 1.0 / -0.0 vs 0.0 --")
for a_dpi, b_dpi in ((1, 1.0), (-0.0, 0.0)):
    try:
        normalize([blk("Ada: bir", 10, 0, dpi=a_dpi), blk("iki", 10, 25, dpi=b_dpi)], OcrPreset.DIALOGUE)
        print(f"    dpi {a_dpi!r} vs {b_dpi!r}: birlesti (esit sayildi)")
    except ValueError:
        print(f"    dpi {a_dpi!r} vs {b_dpi!r}: ValueError")


# ---------------------------------------------------------------------------
basliki("4. >=40 BLOKLU GIRDI")
# ---------------------------------------------------------------------------

for n in (40, 63, 120, 250):
    for preset in PRESETS:
        bl = derlem(n, tohum=n)
        segs = normalize(bl, preset)
        # K8: source_blocks artan, tekrarsiz, bos degil, ayrik
        gorulen = set()
        hata = []
        for s in segs:
            sb = s.source_blocks
            if not sb:
                hata.append("bos source_blocks")
            if list(sb) != sorted(set(sb)):
                hata.append(f"artan/tekrarsiz degil: {sb}")
            if gorulen & set(sb):
                hata.append(f"AYRIK DEGIL: {sb}")
            gorulen |= set(sb)
            if not (0 <= min(sb) and max(sb) < len(bl)):
                hata.append(f"indeks araligi disi: {sb}")
        # K3: cikti sirasi
        anahtarlar = [(s.bbox.y, s.bbox.x) for s in segs]
        if anahtarlar != sorted(anahtarlar):
            hata.append("K3 sira bozuk")
        # K23: miras acik/kapali bolumleme BIREBIR ayni
        acik = [s.source_blocks for s in _normalize_impl(bl, preset, apply_inheritance=True)]
        kapali = [s.source_blocks for s in _normalize_impl(bl, preset, apply_inheritance=False)]
        if acik != kapali:
            hata.append("K23 IHLALI")
        print(f"  n={n:3d} {preset.value:9s} segment={len(segs):3d}  {'TEMIZ' if not hata else hata}")

print()
print("  -- >=40 blokta ZINCIRLEME miras (tek etiket + 60 devam blogu) --")
UZUN2 = "kelime" * 45  # ~270 cp; dialogue cap 280 -> her sinir yalniz-uzunluk
zincir = [blk("Ada: " + UZUN2, 10, 0, h=20)]
y = 25
for i in range(59):
    zincir.append(blk(UZUN2, 10, y, h=20))
    y += 25
segs = normalize(zincir, OcrPreset.DIALOGUE)
speakers = [s.speaker for s in segs]
print(f"    segment sayisi={len(segs)}  farkli speaker degerleri={sorted(set(map(str, speakers)))}")
print(f"    None sayisi={speakers.count(None)}  'Ada' sayisi={speakers.count('Ada')}")

print()
print("  -- >=40 blok + SIRASIZ girdi + K23 fuzz (200 koşum) --")
ihlal = 0
for t in range(200):
    r = random.Random(90000 + t)
    n = r.randint(40, 70)
    bl = []
    y = 0
    for i in range(n):
        metin = ("Ada: " if i % 7 == 0 else "") + "あ" * r.randint(3, 60)
        h = r.choice([0, 5, 12, 18, 20, 30])
        bl.append(blk(metin, r.choice([0, 10, 200]), y, w=r.choice([0, 50, 300]), h=h,
                      conf=r.choice([0.9, 0.5, 0.62])))
        y += max(h, 1) + r.choice([1, 3, 8, 50])
    r.shuffle(bl)
    for preset in (OcrPreset.DIALOGUE, OcrPreset.TOOLTIP, OcrPreset.SUBTITLE):
        a = [s.source_blocks for s in _normalize_impl(bl, preset, apply_inheritance=True)]
        b = [s.source_blocks for s in _normalize_impl(bl, preset, apply_inheritance=False)]
        if a != b:
            ihlal += 1
print(f"    K23 ihlali: {ihlal} / 600")


# ---------------------------------------------------------------------------
basliki("5. ASCII-DISI KONUSMACI ADI")
# ---------------------------------------------------------------------------

ADAYLAR = [
    ("japonca kanji + fullwidth ayrac", "勇者：こんにちは"),
    ("japonca kanji + ASCII ayrac", "魔王: こんにちは"),
    ("japonca hiragana", "むらびと：やあ"),
    ("korece hangul", "용사: 안녕"),
    ("cince", "王小明：你好"),
    ("kiril", "Ада: привет"),
    ("yunanca", "Αδα: γεια"),
    ("arapca (harekesiz)", "مرحبا: أهلا"),
    ("arapca + hareke (fatha)", "مَرحبا: أهلا"),
    ("ibranice", "שלום: היי"),
    ("ibranice + nikud", "שָלוֹם: היי"),
    ("devanagari (namaste)", "नमस्ते: नमस्ते"),
    ("devanagari (sadece basit harf)", "राम: नमस्ते"),
    ("tayca", "สวัสดี: สวัสดี"),
    ("turkce aksanli (NFC)", "Şeyma: merhaba"),
    ("turkce aksanli (NFD)", unicodedata.normalize("NFD", "Şeyma") + ": merhaba"),
    ("RTL isaretli (U+200F)", "مرحبا‏: أهلا"),
    ("vietnamca (NFC)", "Đức: xin chào"),
    ("vietnamca (NFD)", unicodedata.normalize("NFD", "Đức") + ": xin chào"),
    ("halfwidth katakana", "ｶﾞﾝ: やあ"),
]
print(f"  {'ornek':34s} {'speaker':16s} kalan")
for ad, metin in ADAYLAR:
    isim, kalan = _split_speaker_label(metin)
    isaret = "  " if isim is not None else "!!"
    print(f"{isaret}{ad:34s} {str(isim):16s} {kalan!r}")

print()
print("  -- KOMBINE ISARETLERIN kategorileri (neden reddediliyorlar) --")
for ad, ornek in (
    ("devanagari virama U+094D", "्"),
    ("devanagari e-matra U+0947", "े"),
    ("tayca sara-i U+0e34", "ิ"),
    ("arapca fatha U+064E", "َ"),
    ("ibranice kamats U+05B8", "ָ"),
    ("birlesen akut U+0301", "́"),
    ("RTL isareti U+200F", "‏"),
):
    print(f"    {ad:28s} kategori={unicodedata.category(ornek)} isalpha={ornek.isalpha()}")

print()
print("  -- ASCII-DISI ad ile MIRAS ZINCIRI (uzunluk bolunmesi) --")
GOVDE = "あ" * 150
for etiket, ayrac in (("勇者", "："), ("魔王", ":"), ("Ада", ":")):
    bl = [blk(etiket + ayrac + GOVDE, 10, 0, h=20), blk(GOVDE, 10, 25, h=20), blk(GOVDE, 10, 50, h=20)]
    segs = normalize(bl, OcrPreset.DIALOGUE)
    print(f"    {etiket!r:10s}: {len(segs)} segment speakers={[s.speaker for s in segs]!r}")

print()
print("  -- YALNIZ-ETIKET blok (ASCII-disi) bir sonrakine tasiniyor mu? --")
bl = [blk("勇者：", 10, 0, h=20), blk("こんにちは", 10, 200, h=20)]
segs = normalize(bl, OcrPreset.DIALOGUE)
print(f"    {[(s.text, s.speaker, s.source_blocks) for s in segs]!r}")

print()
print("  -- ASCII-disi ad + SIRASIZ girdi: yalniz-etiket blok ASAGIDA --")
bl = [
    blk("こんにちは" * 30, 10, 0, h=20),   # idx0, y=0
    blk("勇者：", 10, 300, h=100),                  # idx1, y=300 (yalniz etiket)
    blk("やあ" * 40, 10, 420, h=20),                    # idx2
]
for preset in (OcrPreset.DIALOGUE, OcrPreset.TOOLTIP):
    segs = normalize(bl, preset)
    print(f"    {preset.value:9s} {[(s.speaker, s.source_blocks) for s in segs]!r}")

print()
print("SONDA BITTI.")
