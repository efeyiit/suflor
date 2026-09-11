"""Sonda r2-02: trie anahtari -- IGNORECASE denkligi, tam Unicode, BAGIMSIZ kanal (kural 8).

(i) re.I'nin denk saydigi her tek-kodpoint cift (casefold/lower/upper/swapcase kapanisi + re.I dogrulamasi + Python'un
    belgeli ozel harfleri I/i/İ/ı, K/k/Kelvin, s/ſ) ayni trie dalina duser mu -- olcu: {a+"xy", b+"xz", a+"x"} sozlugu
    (uzun terim ikinci dalda kalirsa kacar) ile 3 metin x 2 sira = 6 esleme; kanonik anahtar `_anahtar` KULLANILMAZ.
(ii) Ters yon: ayni dala dusen ama re.I denk OLMAYAN cift var mi (ikinci terim erisilemez olurdu) -- olcu:
    {a+"x", b+"y"} sozlugunde b+"y" bulunmali.
Tarama maliyeti: (i) casefold kumeleri (yaklasik 1500 cift), (ii) tum kodpointlerin ikili kapanisi (casefold ile
gruplanir; ayni gruptaki her cift denenir).
"""
from __future__ import annotations

import itertools
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from yardimci import KOK, sozluk  # noqa: E402

OUT = KOK / ".agents/tasks/T-011/tester_A_evidence/r2-sonda-02-trie-ignorecase.txt"
satirlar: list[str] = []


def yaz(s: str) -> None:
    satirlar.append(s)
    print(s.encode("ascii", "backslashreplace").decode("ascii"))


def reI(a: str, b: str) -> bool:
    return bool(re.fullmatch(re.escape(a), b, re.I)) and bool(re.fullmatch(re.escape(b), a, re.I))


def yasak(ch: str) -> bool:
    """Sema/eslemeyle ilgisiz kodpointler: bosluk, noktalama, kontrol, terminator, yer tutucu ayraci, atanmamis."""
    kat = unicodedata.category(ch)
    return kat[0] in "CZP" or ch in ".!?。！？{}"


gruplar: dict[str, set[str]] = defaultdict(set)
for cp in range(0x110000):
    ch = chr(cp)
    if yasak(ch):
        continue
    for k in (ch.casefold(), ch.lower(), ch.upper()):
        gruplar[k].add(ch)
for a, b in [("I", "i"), ("I", "İ"), ("I", "ı"), ("i", "İ"), ("i", "ı"), ("İ", "ı"), ("K", "K"), ("k", "K"), ("s", "ſ"), ("S", "ſ")]:
    gruplar["__ozel_" + a].update({a, b})

ciftler: set[tuple[str, str]] = set()
for kume in gruplar.values():
    if len(kume) < 2:
        continue
    for a, b in itertools.combinations(sorted(kume), 2):
        if reI(a, b):
            ciftler.add((a, b))
yaz(f"(i) re.I denk tek-kodpoint cift sayisi (bagimsiz kapanis): {len(ciftler)}")

ayrisan: list[tuple[str, str, str]] = []
for a, b in sorted(ciftler):
    for sira in (0, 1):
        kayit = [(a + "xy", "A"), (b + "xz", "B"), (a + "x", "C")]
        if sira:
            kayit[0], kayit[1] = kayit[1], kayit[0]
        try:
            st = sozluk(*kayit)
        except ValueError as e:  # tekrar reddi vb. -- kaydet
            ayrisan.append((a, b, f"sira {sira}: yukleme {e.__class__.__name__}"))
            break
        for metin, hedef in [(b + "xz q", "B"), (a + "xy q", "A"), (b + "xy q", "A"), (a + "xz q", "B"), (a + "x q", "C"), (b + "x q", "C")]:
            h = st.lookup(metin)
            if [(x.start, x.end, x.target_term) for x in h] != [(0, len(metin) - 2, hedef)]:
                ayrisan.append((a, b, f"sira {sira} metin {metin!r}: {[(x.start, x.end, x.target_term) for x in h]}"))
                break
yaz(f"(i) ayrisan (harfiyen gecen terim kacan / capraz yazim bulunmayan) cift: {len(ayrisan)}")
for a, b, m in ayrisan[:30]:
    yaz(f"   U+{ord(a):04X} ~ U+{ord(b):04X}: {m}")

# (ii) ters yon: re.I denk OLMAYAN ama ayni gruba dusen (casefold/lower/upper esit) ciftler
ters_aday: set[tuple[str, str]] = set()
for kume in gruplar.values():
    if len(kume) < 2:
        continue
    for a, b in itertools.combinations(sorted(kume), 2):
        if not reI(a, b):
            ters_aday.add((a, b))
yaz(f"(ii) casefold/lower/upper esit ama re.I denk OLMAYAN cift: {len(ters_aday)}")
erisilemez: list[tuple[str, str, str]] = []
tekrar_reddi = 0
for a, b in sorted(ters_aday):
    try:
        st = sozluk((a + "x", "A"), (b + "y", "B"))
    except ValueError:
        tekrar_reddi += 1  # ayni kanonik anahtar (tek harf ayni) -> ikisi ayni terim degil; farkli son harf var, red beklenmez
        erisilemez.append((a, b, "yukleme ValueError"))
        continue
    hb = st.lookup(b + "y q")
    ha = st.lookup(a + "x q")
    if [(x.start, x.end, x.target_term) for x in hb] != [(0, 2, "B")] or [(x.start, x.end, x.target_term) for x in ha] != [(0, 2, "A")]:
        erisilemez.append((a, b, f"a+x -> {[(x.target_term) for x in ha]}, b+y -> {[(x.target_term) for x in hb]}"))
yaz(f"(ii) ayni dala dusup erisilemez kalan (ya da yuklenemeyen) cift: {len(erisilemez)}")
for a, b, m in erisilemez[:30]:
    yaz(f"   U+{ord(a):04X} ({unicodedata.name(a, '?')}) ~ U+{ord(b):04X} ({unicodedata.name(b, '?')}): {m}")

OUT.write_text("\n".join(satirlar) + "\n", encoding="utf-8")
print(f"yazildi -> {OUT.name}")
