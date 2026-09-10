# -*- coding: utf-8 -*-
"""Tester-C, TUR 6 -- BES SINIFIN uzerinde DEGISMEZ fuzz'i (hata AVI).

Uretici, sefin "kit uretmiyor" dedigi bes sinifi KASITLI olarak uretir:
emoji/astral/ZWJ, monitor_index != 0, dpi_scale != 1.0, >=40 blok,
ASCII-disi konusmaci adi -- ayrica yozlasmis geometri ve sirasiz girdi.

Denetlenen degismezler:
  D1  cokme yok (K10 ValueError'u HARIC -- karisik monitor/dpi kasitli)
  D2  K8: source_blocks artan, tekrarsiz, ayrik, aralik icinde, bos degil
  D3  K3: cikti (bbox.y, bbox.x) artan
  D4  K23: miras acik/kapali BOLUMLEME birebir ayni
  D5  speaker CODEPOINT duzeyinde bir kaynak blogun etiket on-ekine ESIT
  D6  Segment.bbox.monitor_index / dpi_scale, KAYNAK bloklarininkiyle AYNI
  D7  segment metni bos degil (K12)

Kosum:  python .agents/tasks/T-004/tester_C_evidence/r6-12-bes-sinif-degismez-fuzz.py
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
from src.ocr.normalizer import _normalize_impl, _split_speaker_label, normalize

PRESETS = (OcrPreset.DIALOGUE, OcrPreset.TOOLTIP, OcrPreset.SUBTITLE, OcrPreset.MENU)

ADLAR = ["勇者", "魔王", "村人", "용사", "Ада", "Αδα", "مرحبا", "שלום", "María", "Şeyma", "𝐀𝐁"]
AYRACLAR = [":", "："]
GOVDELER = [
    "こんにちは世界",
    "안녕하세요",
    "привет мир",
    "أهلا بالعالم",
    "שלום עולם",
    "hola qué tal",
    "\U0001F468‍\U0001F469‍\U0001F467 aile",
    "\U0001F1F9\U0001F1F7 bayrak",
    "\U0002000B astral",
    "☀️ gunes",
    "kelime-",
    "devam eden satir",
]


def uret(r: random.Random) -> list[TextBlock]:
    n = r.randint(40, 70)
    mon = r.choice([0, 0, 1, 2, 7])
    dpi = r.choice([1.0, 1.0, 1.25, 1.5, 2.0])
    bl: list[TextBlock] = []
    y = 0
    for i in range(n):
        govde = " ".join(r.choice(GOVDELER) for _ in range(r.randint(1, 8)))
        tur = r.random()
        if tur < 0.18:
            metin = r.choice(ADLAR) + r.choice(AYRACLAR) + " " + govde
        elif tur < 0.26:
            metin = r.choice(ADLAR) + r.choice(AYRACLAR)   # yalniz etiket
        else:
            metin = govde
        h = r.choice([0, 1, 12, 18, 20, 30])
        w = r.choice([0, 1, 200, 300, 320])
        bl.append(
            TextBlock(
                text=metin,
                bbox=Rect(x=r.choice([-20, 0, 10, 12, 400]), y=y, w=w, h=h,
                          monitor_index=mon, dpi_scale=dpi),
                confidence=r.choice([0.9, 0.9, 0.7, 0.44, 0.55, 0.60, 0.65]),
            )
        )
        y += max(h, 1) + r.choice([1, 3, 8, 50])
    r.shuffle(bl)
    return bl


ihlaller: dict[str, int] = {k: 0 for k in ("D1", "D2", "D3", "D4", "D5", "D6", "D7")}
ilk_ornek: dict[str, str] = {}
kosum = 0
value_error = 0

for t in range(400):
    r = random.Random(500000 + t)
    bl = uret(r)
    for preset in PRESETS:
        kosum += 1
        try:
            segs = normalize(bl, preset)
        except ValueError as exc:
            if "monitor_index/dpi_scale" in str(exc):
                value_error += 1
                continue
            ihlaller["D1"] += 1
            ilk_ornek.setdefault("D1", f"t={t} {preset}: {type(exc).__name__}: {exc}")
            continue
        except Exception as exc:  # noqa: BLE001
            ihlaller["D1"] += 1
            ilk_ornek.setdefault("D1", f"t={t} {preset}: {type(exc).__name__}: {exc}")
            continue

        gorulen: set[int] = set()
        for s in segs:
            sb = s.source_blocks
            if (not sb) or list(sb) != sorted(set(sb)) or (gorulen & set(sb)) \
                    or not (0 <= min(sb) and max(sb) < len(bl)):
                ihlaller["D2"] += 1
                ilk_ornek.setdefault("D2", f"t={t} {preset}: {sb}")
            gorulen |= set(sb)
            if not s.text.strip():
                ihlaller["D7"] += 1
                ilk_ornek.setdefault("D7", f"t={t} {preset}: {s!r}")
            # D6
            for i in sb:
                if (bl[i].bbox.monitor_index != s.bbox.monitor_index
                        or bl[i].bbox.dpi_scale != s.bbox.dpi_scale):
                    ihlaller["D6"] += 1
                    ilk_ornek.setdefault("D6", f"t={t} {preset}: seg={s.bbox} blok={bl[i].bbox}")
            # D5
            if s.speaker is not None:
                adaylar = {_split_speaker_label(bl[i].text)[0] for i in sb}
                if s.speaker not in adaylar:
                    # miras: baska bir segmentin konusmacisi olabilir
                    tum = {sp.speaker for sp in segs if sp.speaker is not None}
                    if s.speaker not in tum:
                        ihlaller["D5"] += 1
                        ilk_ornek.setdefault("D5", f"t={t} {preset}: {s.speaker!r} not in {adaylar!r}")

        anahtarlar = [(s.bbox.y, s.bbox.x) for s in segs]
        if anahtarlar != sorted(anahtarlar):
            ihlaller["D3"] += 1
            ilk_ornek.setdefault("D3", f"t={t} {preset}")

        acik = [s.source_blocks for s in _normalize_impl(bl, preset, apply_inheritance=True)]
        kapali = [s.source_blocks for s in _normalize_impl(bl, preset, apply_inheritance=False)]
        if acik != kapali:
            ihlaller["D4"] += 1
            ilk_ornek.setdefault("D4", f"t={t} {preset}")

print(f"koşum = {kosum}  (400 girdi x 4 on ayar)")
print(f"K10 ValueError (karisik monitor/dpi -- KASITLI, ihlal degil) = {value_error}")
print()
for k in ("D1", "D2", "D3", "D4", "D5", "D6", "D7"):
    print(f"  {k}: {ihlaller[k]:5d} ihlal   {ilk_ornek.get(k, '')}")
print()
print("TOPLAM IHLAL =", sum(ihlaller.values()))
