"""T-011 olcum (implementer, tur 2): `_anahtar` VE `_trie_anahtari`, `re.IGNORECASE` denklik siniflariyla ortusuyor mu?

    python .agents/tasks/T-011/evidence/olcum-trie-anahtari-ignorecase-denkligi-tur2.py

Tur 1 olcumu yalniz `_anahtar`i (kanonik anahtar) taradi; Tester-A O-A1 trie
DUGUM anahtarinin (`_trie_anahtari`) coklu-kodpoint casefold sinifinda
(`ß`/`ẞ`, `ᾈ`/`ᾀ`) ayristigini buldu: IGNORECASE denk iki karakter ayri dala
dusuyor, ilk dal kisa terminalde durup uzun terimi kaciriyordu. v3 temsilci
`ch.lower()`; bu betik IGNORECASE'in `c ~ d` dedigi HER kodpoint cifti icin
ikisinin de esit oldugunu tum Unicode'da (0..0x10FFFF) dogrular. `re`nin
buyuk/kucuk denkligi: `_sre.unicode_tolower` + `re._casefix._EXTRA_CASES`
(3.12; surum bagimli ic tablo; yalniz olcum icin okunur, urun kodu kullanmaz).
Pozitif kontrol: tur-1 anahtari (`k if len(k) == 1 else ch`) ayni taramada
ayrisan cift URETMELI. Stdout ASCII.
"""
from __future__ import annotations

import sys
from pathlib import Path

import _sre  # type: ignore[import-not-found]
import re._casefix as _cf  # type: ignore[import-not-found]

KOK = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(KOK))

from src.translate.sozluk import _anahtar, _trie_anahtari  # noqa: E402


def _tur1_trie_anahtari(ch: str) -> str:
    k = _anahtar(ch)
    return k if len(k) == 1 else ch


def _lower_temsilci(ch: str) -> str:
    """Tasarim adayi (reddedildi): coklu kodpoint katlamada `ch.lower()` temsilcisi."""
    k = _anahtar(ch)
    return k if len(k) == 1 else ch.lower()


fixes: dict[int, tuple[int, ...]] = getattr(_cf, "_EXTRA_CASES")
tolower = _sre.unicode_tolower
sorun_anahtar: list[tuple[int, int]] = []
sorun_trie: list[tuple[int, int]] = []
sorun_tur1: list[tuple[int, int]] = []
sorun_lower: list[tuple[int, int]] = []
cift_sayisi = 0
gruplar: dict[str, list[int]] = {}
for c in range(0x110000):
    lo = tolower(c)
    esler = {lo, *fixes.get(lo, ())}
    esler.discard(c)
    for d in esler:
        cift_sayisi += 1
        if _anahtar(chr(c)) != _anahtar(chr(d)):
            sorun_anahtar.append((c, d))
        if _trie_anahtari(chr(c)) != _trie_anahtari(chr(d)):
            sorun_trie.append((c, d))
        if _tur1_trie_anahtari(chr(c)) != _tur1_trie_anahtari(chr(d)):
            sorun_tur1.append((c, d))
        if _lower_temsilci(chr(c)) != _lower_temsilci(chr(d)):
            sorun_lower.append((c, d))
    gruplar.setdefault(_trie_anahtari(chr(c)), []).append(c)
# ters yon: ayni trie anahtarina dusen iki tek-kodpoint karakter IGNORECASE'de DENK olmali
# (regex literali dalin ilk gorulen uyesidir; denk degilse literal oteki uyeyi eslemez)
ters_sorun: list[tuple[int, int]] = []
for _k, uyeler in gruplar.items():
    if len(uyeler) < 2:
        continue
    ilk = uyeler[0]
    denk_ilk = {tolower(ilk), *fixes.get(tolower(ilk), ())}
    for d in uyeler[1:]:
        if d not in denk_ilk and tolower(d) not in denk_ilk and not ({tolower(d), *fixes.get(tolower(d), ())} & denk_ilk):
            ters_sorun.append((ilk, d))
print(f"python {sys.version.split()[0]}; taranan kodpoint: 0x110000; IGNORECASE denk cift: {cift_sayisi}")
print(f"_anahtar (kanonik) FARKLI olan denk cift: {len(sorun_anahtar)}")
print(f"_trie_anahtari (v3 = kanonik anahtar) FARKLI olan denk cift: {len(sorun_trie)}")
for c, d in sorun_trie[:20]:
    print(f"  U+{c:04X} ~ U+{d:04X}")
cok_uyeli = sum(1 for u in gruplar.values() if len(u) > 1)
print(f"TERS YON -- ayni trie anahtarinda toplanan ama IGNORECASE'de denk OLMAYAN cift: {len(ters_sorun)} ({cok_uyeli} cok uyeli dal)")
for c, d in ters_sorun[:20]:
    print(f"  U+{c:04X} !~ U+{d:04X}")
print(f"POZITIF KONTROL 1 -- tur-1 trie anahtari (`k if len(k)==1 else ch`) FARKLI olan denk cift: {len(sorun_tur1)}")
for c, d in sorun_tur1[:8]:
    print(f"  U+{c:04X} ~ U+{d:04X}")
print(f"POZITIF KONTROL 2 -- reddedilen aday `ch.lower()` temsilcisi FARKLI olan denk cift: {len(sorun_lower)}")
for c, d in sorun_lower[:8]:
    print(f"  U+{c:04X} ~ U+{d:04X}")
tamam = not sorun_anahtar and not sorun_trie and not ters_sorun and bool(sorun_tur1) and bool(sorun_lower)
print("SONUC:", "v3 trie anahtari IGNORECASE denkligini iki yonde tam kapsar; tur-1 anahtari ve lower() temsilcisi ayrisiyordu (kontroller atesledi)" if tamam else "BEKLENTI TUTMADI")
raise SystemExit(0 if tamam else 1)
