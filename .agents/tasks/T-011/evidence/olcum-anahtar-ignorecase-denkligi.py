"""T-011 olcum (implementer): `_anahtar` kanonik anahtari, `re.IGNORECASE` denklik siniflariyla ortusuyor mu?

    python .agents/tasks/T-011/evidence/olcum-anahtar-ignorecase-denkligi.py

Neden: `lookup` eslesen dilimi terime kanonik anahtarla (`casefold` + Turkce I
sinifi) baglar. IGNORECASE'in `c ~ d` dedigi HER kodpoint cifti icin
`_anahtar(c) == _anahtar(d)` olmali; aksi halde dilim terime baglanamaz ve
eslesme sessizce kacar. `re`nin buyuk/kucuk denkligi: `_sre.unicode_tolower`
+ `re._casefix._EXTRA_CASES` (3.12; surum bagimli ic tablo; yalniz olcum icin
okunur, urun kodu kullanmaz). Tum Unicode (0..0x10FFFF) taranir. Stdout ASCII.
"""
from __future__ import annotations

import sys
from pathlib import Path

import _sre  # type: ignore[import-not-found]
import re._casefix as _cf  # type: ignore[import-not-found]

KOK = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(KOK))

from src.translate.sozluk import _anahtar  # noqa: E402

fixes: dict[int, tuple[int, ...]] = getattr(_cf, "_EXTRA_CASES")
tolower = _sre.unicode_tolower
sorunlar: list[tuple[int, int]] = []
cift_sayisi = 0
for c in range(0x110000):
    lo = tolower(c)
    esler = {lo, *fixes.get(lo, ())}
    esler.discard(c)
    for d in esler:
        cift_sayisi += 1
        if _anahtar(chr(c)) != _anahtar(chr(d)):
            sorunlar.append((c, d))
print(f"python {sys.version.split()[0]}; taranan kodpoint: 0x110000; IGNORECASE denk cift: {cift_sayisi}")
print(f"anahtari FARKLI olan denk cift: {len(sorunlar)}")
for c, d in sorunlar[:20]:
    print(f"  U+{c:04X} ~ U+{d:04X}")
print("SONUC:", "kanonik anahtar IGNORECASE denkligini tam kapsar; yedek tarama gereksiz" if not sorunlar else "yedek tarama GEREKLI")
raise SystemExit(1 if sorunlar else 0)
