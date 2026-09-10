# -*- coding: utf-8 -*-
"""Tester-C, TUR 6 -- K32 (NFC/NFD), K31 (a)/(b) ve YOZLASMIS GEOMETRI sondasi.

Kosum:  python .agents/tasks/T-004/tester_C_evidence/r6-08-k31-k32-yozlasmis-sonda.py
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
basliki("K32 -- NFC / NFD")
# ---------------------------------------------------------------------------

# Sefin olcumu: 3 bloklu aksanli govde, blok basina ~85-92 codepoint ->
# NFC'de 1 segment, NFD'de 3 segment (DIALOGUE cap 280).
GOVDE_NFC = "María dijo qué así canción " * 3  # aksan YOGUN
GOVDE_NFC = GOVDE_NFC[:88].strip()
GOVDE_NFD = unicodedata.normalize("NFD", GOVDE_NFC)
print(f"  govde NFC cp={len(GOVDE_NFC)}  NFD cp={len(GOVDE_NFD)}  gorunum ayni mi="
      f"{unicodedata.normalize('NFC', GOVDE_NFD) == GOVDE_NFC}")
print(f"  govde: {GOVDE_NFC!r}")


def uc_bloklu(govde, etiket):
    return [
        blk(etiket + ": " + govde, 10, 0, h=20),
        blk(govde, 10, 25, h=20),
        blk(govde, 10, 50, h=20),
    ]


for ad, etiket_nfc in (("govde+etiket aksanli", "María"),):
    for bicim, govde, etiket in (
        ("NFC", GOVDE_NFC, etiket_nfc),
        ("NFD", GOVDE_NFD, unicodedata.normalize("NFD", etiket_nfc)),
    ):
        segs = normalize(uc_bloklu(govde, etiket), OcrPreset.DIALOGUE)
        print(
            f"  [{ad}] {bicim}: {len(segs)} segment  speakers={[s.speaker for s in segs]!r}  "
            f"source_blocks={[s.source_blocks for s in segs]!r}"
        )

print()
print("  -- YALNIZ ETIKET aksanli, govde ASCII (segment sayisi AYNI kalmali) --")
GOVDE_ASCII = "hola " * 10
for bicim, etiket in (("NFC", "María"), ("NFD", unicodedata.normalize("NFD", "María"))):
    bl = [blk(etiket + ": " + GOVDE_ASCII, 10, 0, h=20)]
    segs = normalize(bl, OcrPreset.DIALOGUE)
    print(f"    {bicim}: {len(segs)} segment  speaker={segs[0].speaker!r}  text={segs[0].text[:40]!r}...")

print()
print("  -- YALNIZ ETIKET aksanli, COK BLOKLU govde (sefin '1/1' iddiasi) --")
for bicim, etiket in (("NFC", "María"), ("NFD", unicodedata.normalize("NFD", "María"))):
    bl = [blk(etiket + ": " + "hola " * 8, 10, 0, h=20), blk("adios " * 8, 10, 25, h=20)]
    segs = normalize(bl, OcrPreset.DIALOGUE)
    print(f"    {bicim}: {len(segs)} segment  speakers={[s.speaker for s in segs]!r}")

print()
print("  -- ayrac kumesi NFD'den ETKILENIYOR mu (K17)? --")
for ad, s in (("ASCII :", ":"), ("fullwidth ：", "：")):
    print(f"    {ad}: NFC={unicodedata.normalize('NFC', s)!r} NFD={unicodedata.normalize('NFD', s)!r} "
          f"esit={unicodedata.normalize('NFD', s) == s}")

print()
print("  -- _MAX_SPEAKER_NAME_LEN (40 cp) NFD ile asiliyor mu? --")
uzun_ad_nfc = "á" * 30          # 30 cp
uzun_ad_nfd = unicodedata.normalize("NFD", uzun_ad_nfc)  # 60 cp
for bicim, ad in (("NFC(30cp)", uzun_ad_nfc), ("NFD(60cp)", uzun_ad_nfd)):
    isim, kalan = _split_speaker_label(ad + ": merhaba")
    print(f"    {bicim}: len={len(ad)} -> speaker={'None' if isim is None else 'VAR'}")
# Sadece ILK karakteri aksanli, kalani ASCII -> NFD'de de isalpha zinciri kirilir
karma_nfc = "á" + "b" * 39      # 40 cp, tam sinirda
karma_nfd = unicodedata.normalize("NFD", karma_nfc)  # 41 cp
for bicim, ad in (("NFC(40cp, tam sinir)", karma_nfc), ("NFD(41cp)", karma_nfd)):
    isim, kalan = _split_speaker_label(ad + ": merhaba")
    print(f"    {bicim}: len={len(ad)} -> speaker={'None' if isim is None else repr(isim)[:20]}")


# ---------------------------------------------------------------------------
basliki("K31 (a) / (b)")
# ---------------------------------------------------------------------------

SENARYOLAR = [
    ("(a) ayni ad, IKISI de etiketli", ["Ada: merhaba", "Ada: nasilsin"]),
    ("(b) ikinci etiket RAKAMLI", ["Ada: merhaba", "Ada2: nasilsin"]),
    ("(kontrol) IKI FARKLI taninan ad", ["Ada: merhaba", "Bora: nasilsin"]),
    ("(b') ikinci etiket NFD ad", ["Ada: merhaba", unicodedata.normalize("NFD", "Ádá") + ": nasilsin"]),
    ("(a-CJK) ayni CJK ad, ikisi de etiketli", ["勇者：こんにちは", "勇者：げんきですか"]),
    ("(b-CJK) ikinci CJK etiket rakamli", ["勇者：こんにちは", "勇者2：げんきですか"]),
    ("(kontrol-CJK) iki FARKLI CJK ad", ["勇者：こんにちは", "魔王：ふふふ"]),
]
for ad, metinler in SENARYOLAR:
    bl = [blk(t, 10, i * 25, h=20) for i, t in enumerate(metinler)]
    segs = normalize(bl, OcrPreset.DIALOGUE)
    print(f"  {ad}")
    for s in segs:
        print(f"      speaker={s.speaker!r:10s} text={s.text!r} source_blocks={s.source_blocks}")

print()
print("  -- (b) ETIKET METINDE KALIYOR mu: tam metin dogrulamasi --")
segs = normalize([blk("Ada: merhaba", 10, 0, h=20), blk("Ada2: nasilsin", 10, 25, h=20)], OcrPreset.DIALOGUE)
print(f"    {[(s.text, s.speaker) for s in segs]!r}")
print(f"    'Ada2:' metinde mi -> {'Ada2:' in segs[0].text}")


# ---------------------------------------------------------------------------
basliki("YOZLASMIS GEOMETRI")
# ---------------------------------------------------------------------------

print("  -- w<=0 / h<=0 blok GRUPLANMIYOR (K16) ama SEGMENT URETIYOR --")
for ad, w, h in (("h=0", 300, 0), ("h=-5", 300, -5), ("w=0", 0, 20), ("w=-7", -7, 20), ("w=0,h=0", 0, 0)):
    bl = [blk("Ada: bir", 10, 0, w=300, h=20), blk("iki", 10, 25, w=w, h=h)]
    segs = normalize(bl, OcrPreset.DIALOGUE)
    print(f"    {ad:9s}: {len(segs)} segment  {[(s.text, s.speaker, s.source_blocks) for s in segs]!r}")

print()
print("  -- yozlasmis blok MIRASA engel mi (K21: yalniz-uzunluk degil)? --")
UZ = "a" * 200
for ad, h2 in (("aday h=0", 0), ("aday h=20 (kontrol)", 20)):
    bl = [blk("Ada: " + UZ, 10, 0, h=20), blk(UZ, 10, 25, h=h2)]
    segs = normalize(bl, OcrPreset.DIALOGUE)
    print(f"    {ad:22s}: speakers={[s.speaker for s in segs]!r}")

print()
print("  -- K28 sag taraf: BIRLESIK aday h=0'i gizliyor mu? (hyphen zinciri) --")
# Aday, adim 3'te hyphen ile birlesmis olsun; HAM ilk satirin h'si 0.
bl = [
    blk("Ada: " + "a" * 200, 10, 0, w=300, h=20),   # idx0
    blk("keli-", 10, 25, w=300, h=0),               # idx1  HAM ilk satir h=0
    blk("me devam", 10, 30, w=300, h=20),           # idx2
]
segs = normalize(bl, OcrPreset.DIALOGUE)
print(f"    {[(s.text[:20], s.speaker, s.source_blocks) for s in segs]!r}")
print("    (K16 geregi h=0 aday MIRAS ALMAMALI -> ikinci speaker None olmali)")

print()
print("  -- AYNI (y,x) cifti tasiyan bloklar: okuma sirasi kararli mi? --")
bl = [
    blk("ucuncu", 10, 100, h=20),   # idx0
    blk("Ada: bir", 10, 100, h=20), # idx1  AYNI (y,x)
    blk("ikinci", 10, 100, h=20),   # idx2  AYNI (y,x)
]
for preset in (OcrPreset.DIALOGUE, OcrPreset.TOOLTIP, OcrPreset.MENU):
    segs = normalize(bl, preset)
    print(f"    {preset.value:9s} {[(s.text, s.speaker, s.source_blocks) for s in segs]!r}")

print()
print("  -- AYNI (y,x): _raw_query_pair okuma sirasi ile adim-1 sirasi UYUSUYOR mu? --")
r = random.Random(4242)
uyusmazlik = 0
for t in range(500):
    n = r.randint(3, 9)
    bloklar = []
    for i in range(n):
        y = r.choice([0, 0, 10, 10, 25])
        x = r.choice([0, 0, 10])
        bloklar.append(blk("m" * r.randint(1, 5), x, y, h=r.choice([0, 10, 20])))
    adim1 = [i for i, _ in sorted(enumerate(bloklar), key=lambda p: (p[1].bbox.y, p[1].bbox.x))]
    kit = sorted(range(n), key=lambda i: (bloklar[i].bbox.y, bloklar[i].bbox.x, i))
    if adim1 != kit:
        uyusmazlik += 1
print(f"    500 sirasiz/esit-anahtarli girdi: uyusmazlik={uyusmazlik}")

print()
print("  -- TEK KARAKTERLI bloklar (K4) yozlasmis geometriyle birlikte --")
for ch in ("力", "a", "1", "?", "？", "。", "-"):
    bl = [blk(ch, 10, 0, w=0, h=0)]
    segs = normalize(bl, OcrPreset.MENU)
    print(f"    {ch!r:5s} kat={unicodedata.category(ch)} w=0,h=0 -> {[s.text for s in segs]!r}")

print()
print("  -- _group([], params) DOGRUDAN cagri (blocks= verilmeden) --")
print(f"    _group([], get_params(DIALOGUE)) -> {_group([], get_params(OcrPreset.DIALOGUE))!r}")
tek = _Item(text="tek", bbox=Rect(x=0, y=0, w=10, h=10), speaker=None, source_blocks=(0,))
print(f"    _group([tek], params)          -> {[i.text for i in _group([tek], get_params(OcrPreset.DIALOGUE))]!r}")

print()
print("  -- _raw_query_pair sinir durumlari --")
a = _Item(text="a", bbox=Rect(x=0, y=0, w=10, h=10), speaker="Ada", source_blocks=(0,))
b = _Item(text="b", bbox=Rect(x=0, y=20, w=10, h=10), speaker=None, source_blocks=(1,))
bloklar = [blk("a", 0, 0, w=10, h=10), blk("b", 0, 20, w=10, h=10)]
sol, sag = _raw_query_pair(a, b, bloklar)
print(f"    normal: sol.bbox={sol.bbox} sag.bbox={sag.bbox} speaker korundu={sol.speaker!r}/{sag.speaker!r}")
print(f"            source_blocks korundu={sol.source_blocks}/{sag.source_blocks}")
try:
    _raw_query_pair(a, b, ())
    print("    blocks=() -> ISTISNA YOK (!)")
except IndexError as exc:
    print(f"    blocks=() -> IndexError: {exc}")
try:
    _raw_query_pair(_Item("a", Rect(0, 0, 1, 1), None, ()), b, bloklar)
    print("    BOS source_blocks -> ISTISNA YOK (!)")
except IndexError as exc:
    print(f"    BOS source_blocks -> IndexError: {exc}")

print()
print("  -- YOZLASMIS GEOMETRI + >=40 blok + dort on ayar: cokme/K23 fuzz --")
ihlal = cokme = 0
for t in range(150):
    r = random.Random(70000 + t)
    n = r.randint(40, 60)
    bl = []
    for i in range(n):
        bl.append(
            blk(
                ("Ada: " if i % 6 == 0 else "") + "x" * r.randint(1, 90),
                r.choice([-20, 0, 10, 500]),
                r.randint(0, 400),
                w=r.choice([-5, 0, 1, 300]),
                h=r.choice([-3, 0, 1, 20]),
                conf=r.choice([0.9, 0.44, 0.6]),
            )
        )
    r.shuffle(bl)
    for preset in (OcrPreset.DIALOGUE, OcrPreset.TOOLTIP, OcrPreset.SUBTITLE, OcrPreset.MENU):
        try:
            acik = [s.source_blocks for s in _normalize_impl(bl, preset, apply_inheritance=True)]
            kapali = [s.source_blocks for s in _normalize_impl(bl, preset, apply_inheritance=False)]
            if acik != kapali:
                ihlal += 1
        except Exception as exc:
            cokme += 1
            print(f"      COKME t={t} {preset}: {type(exc).__name__}: {exc}")
print(f"    150 x 4 on ayar: K23 ihlali={ihlal} cokme={cokme}")

print()
print("SONDA BITTI.")
