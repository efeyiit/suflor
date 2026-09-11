"""Sonda 7: trie dal ayrismasi (coklu-kodpoint casefold: ß/ẞ, Yunan iota-subscript) -> en uzun terim kacar mi;
regex-ozel ilk karakterli terimler; yer tutucu ortusmesiz tarama."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from yardimci import KOK, hit_ozet, sozluk, u  # noqa: E402

OUT = KOK / ".agents/tasks/T-011/tester_A_evidence/sonda-07-trie-dal.txt"
satirlar: list[str] = []


def yaz(s: str) -> None:
    satirlar.append(s)
    print(s.encode("ascii", "backslashreplace").decode("ascii"))


yaz("== 1. ß/ẞ: uc terim, ilk dal kisa terminalde durur, uzun terim ikinci dalda ==")
# Sirali (uzunluk azalan, JSON sirasi): Maßen(5) -> dal 'ß'; Maẞer(5) -> dal 'ẞ'; Maße(4) -> dal 'ß' terminal.
st = sozluk(("Maßen", "Massen"), ("Maẞer", "Masser"), ("Maße", "Masse"))
yaz(f"  desen: {u(st._desen.pattern)}")
for metin in ["Maßen geht", "Maẞer geht", "Maßer geht", "Maße geht", "MASSER", "Maẞen geht"]:
    yaz(f"  {u(metin)!s:14s} -> {hit_ozet(st.lookup(metin))}")
yaz("  beklenen (docstring 'aday kumesi TAM'): 'Maßer geht' -> Maẞer [0,5) (re.I ß~ẞ); 'Maẞen geht' -> Maßen [0,5)")

yaz("== 1b. JSON sirasi ters: Maẞer once ==")
st2 = sozluk(("Maẞer", "Masser"), ("Maßen", "Massen"), ("Maße", "Masse"))
for metin in ["Maßer geht", "Maẞen geht", "Maẞe geht"]:
    yaz(f"  {u(metin)!s:14s} -> {hit_ozet(st2.lookup(metin))}")

yaz("== 1c. tek kodpoint casefold (ayni dal) kontrolu: Marcus/marcus aurelius ==")
st3 = sozluk(("Marcus", "M"), ("marcus aurelius", "MA"))
yaz(f"  'MARCUS AURELIUS x' -> {hit_ozet(st3.lookup('MARCUS AURELIUS x'))}")
yaz(f"  'Marcus x' -> {hit_ozet(st3.lookup('Marcus x'))}")

yaz("== 1d. Yunan iota-subscript: ᾈ (U+1F88) ~ ᾀ (U+1F80) re.I; casefold 2 kodpoint ==")
import re
yaz(f"  re.I esler mi: {bool(re.fullmatch('ᾈ', 'ᾀ', re.I))}; casefold: {u('ᾈ'.casefold())!r} len {len('ᾈ'.casefold())}")
st4 = sozluk(("ᾈβγ", "A"), ("ᾀβδ", "B"), ("ᾈβ", "C"))
for metin in ["ᾈβδ x", "ᾀβγ x", "ᾀβδ x"]:
    yaz(f"  {u(metin)!s:20s} -> {hit_ozet(st4.lookup(metin))}")

yaz("== 2. regex-ozel ilk karakterli terimler ==")
st5 = sozluk(("]x", "A"), ("^x", "B"), ("-x", "C"), ("\\x", "D"), ("[x", "E"), (".x", "F"), ("|x", "G"), ("(x", "H"))
yaz(f"  desen ilk 60: {u(st5._desen.pattern[:60])}")
for metin in ["]x", "^x", "-x", "\\x", "[x", ".x", "|x", "(x", "ax", "yx"]:
    yaz(f"  {u(metin)!s:6s} -> {hit_ozet(st5.lookup(metin))}")

yaz("== 3. yer tutucu ortusmesiz tarama: 'aa' x 'aaa' ==")
st6 = sozluk(("aab", "X"))
yaz(f"  'aaab' yt=('aa',): {hit_ozet(st6.lookup('aaab', ('aa',)))}  (korunan [0,2); aab [1,4) ortusur -> yok)")
yaz(f"  'aaab' yt=():      {hit_ozet(st6.lookup('aaab'))} (aab solu 'a' harf -> yok; pozitif: ' aab')")
yaz(f"  ' aab' yt=():      {hit_ozet(st6.lookup(' aab'))}")

yaz("== 4. hedef == kaynak (ozdes) her gecis hit ==")
st7 = sozluk(("Marcus", "Marcus"))
yaz(f"  'Marcus Marcus' -> {hit_ozet(st7.lookup('Marcus Marcus'))}")

yaz("== 5. lookup('') ve yalniz bosluk / yalniz noktalama / yalniz yt ==")
yaz(f"  '' -> {st7.lookup('')}; '   ' -> {st7.lookup('   ')}; '...' -> {st7.lookup('...')}; '{{0}}' yt -> {st7.lookup('{0}', ('{0}',))}")

OUT.write_text("\n".join(satirlar) + "\n", encoding="utf-8")
print(f"yazildi -> {OUT.name}")
