"""Sonda 4: cok buyuk girdiler -- RecursionError esigi, 10k segment, 5000 terim, 1000x500 sure, geri izleme."""
from __future__ import annotations

import dataclasses
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from yardimci import KOK, seg, sozluk, u  # noqa: E402
from src.translate.sozluk import terimleri_gom  # noqa: E402

OUT = KOK / ".agents/tasks/T-011/tester_A_evidence/sonda-04-buyuk.txt"
satirlar: list[str] = []


def yaz(*a: object) -> None:
    satirlar.append(" ".join(str(x) for x in a))
    print(" ".join(str(x) for x in a).encode("ascii", "backslashreplace").decode("ascii"))


yaz(f"sys.getrecursionlimit() = {sys.getrecursionlimit()}")
yaz("== 1. RecursionError esigi: tek terim, uzunluk N ==")
son_ok = 0
ilk_hata = None
for n in [50, 100, 200, 400, 600, 800, 900, 950, 960, 970, 980, 990, 1000, 1100, 2000]:
    try:
        st = sozluk(("a" * n, "X"))
        h = st.lookup("b " + "a" * n + " b")
        yaz(f"  N={n:5d} -> KABUL, lookup {len(h)} hit {[(x.start, x.end) for x in h]}")
        son_ok = n
    except RecursionError as e:
        yaz(f"  N={n:5d} -> RecursionError")
        if ilk_hata is None:
            ilk_hata = n
    except Exception as e:  # noqa: BLE001
        yaz(f"  N={n:5d} -> {type(e).__name__}: {u(str(e))[:100]}")
        if ilk_hata is None:
            ilk_hata = n
# ikili arama ile tam esik
lo, hi = son_ok, ilk_hata or 2000
while hi - lo > 1:
    mid = (lo + hi) // 2
    try:
        sozluk(("a" * mid, "X"))
        lo = mid
    except RecursionError:
        hi = mid
yaz(f"  TAM ESIK: N={lo} son kabul, N={hi} ilk RecursionError (tek terim, bu surecte)")

yaz("== 1b. Esik derinlige mi (en uzun terim) bagli, terim sayisina mi ==")
try:
    st = sozluk(*[("a" * 50 + str(i), "X") for i in range(2000)])
    yaz(f"  2000 terim x 52 kodpoint -> KABUL len={len(st)}")
except RecursionError:
    yaz("  2000 terim x 52 -> RecursionError")
# gercekci: 300 kodpointlik cumle-terimi (sistem mesaji)
try:
    st = sozluk(("これは長いシステムメッセージです。" * 15, "Uzun"))
    yaz(f"  300 kodpointlik JP cumle terimi -> KABUL")
except RecursionError:
    yaz("  300 JP -> RecursionError")

yaz("== 1c. pytest gibi derin yigin altinda esik duser mi ==")
def derin(k, n):
    if k == 0:
        return sozluk(("a" * n, "X"))
    return derin(k - 1, n)
for yigin in [0, 100, 300, 500]:
    try:
        derin(yigin, 400)
        yaz(f"  yigin {yigin} + N=400 -> KABUL")
    except RecursionError:
        yaz(f"  yigin {yigin} + N=400 -> RecursionError")

yaz("== 2. 10 000 karakterlik tek segment ==")
st = sozluk(("マルクス", "Marcus"), ("長老", "İhtiyar"), ("水車小屋", "Değirmen"), ("Marcus", "Marcus"), ("mill", "Değirmen"))
buyuk = ("長老マルクスが水車小屋で待っています。" * 500)[:10000]
t0 = time.perf_counter()
h = st.lookup(buyuk)
t1 = time.perf_counter()
yaz(f"  len={len(buyuk)}; hit={len(h)}; sure={(t1-t0)*1000:.1f} ms")
hits = tuple(dataclasses.replace(x, segment_index=0) for x in h)
t0 = time.perf_counter()
o = terimleri_gom((seg(buyuk),), hits)
t1 = time.perf_counter()
yaz(f"  gom sure={(t1-t0)*1000:.1f} ms; cikti len={len(o[0].text)}; Marcus sayisi={o[0].text.count('Marcus')}")
# hit'siz 10k (terim yok) -> hizli mi
yok = "あ" * 10000
t0 = time.perf_counter(); h0 = st.lookup(yok); t1 = time.perf_counter()
yaz(f"  10k terim-siz: {len(h0)} hit, {(t1-t0)*1000:.1f} ms")
# 10k ilk-karakter tuzagi: her karakter bir terimin ilk karakteri ama terim degil
tuzak = "マ" * 10000
t0 = time.perf_counter(); h0 = st.lookup(tuzak); t1 = time.perf_counter()
yaz(f"  10k ilk-karakter tuzagi (マx10000): {len(h0)} hit, {(t1-t0)*1000:.1f} ms")
tuzak2 = "マルク" * 3333
t0 = time.perf_counter(); h0 = st.lookup(tuzak2); t1 = time.perf_counter()
yaz(f"  10k onek tuzagi (マルクx3333, son harf eksik): {len(h0)} hit, {(t1-t0)*1000:.1f} ms")

yaz("== 3. 5000 terimli sozluk: yukleme + lookup ==")
import random
random.seed(11)
hece = "가나다라마바사아자차카타파하거너더러머버서어저처커터퍼허"
terimler = set()
while len(terimler) < 5000:
    terimler.add("".join(random.choice(hece) for _ in range(random.randint(2, 6))))
terimler = sorted(terimler)
t0 = time.perf_counter()
st5 = sozluk(*[(t, "H" + str(i)) for i, t in enumerate(terimler)])
t1 = time.perf_counter()
yaz(f"  5000 terim yukleme: {(t1-t0)*1000:.0f} ms; desen uzunlugu: {len(st5._desen.pattern)}")
metin = " ".join(random.choice(terimler) + random.choice(["을", "를", "이", "가", "", "에서"]) for _ in range(40))
t = []
for _ in range(20):
    t0 = time.perf_counter(); h = st5.lookup(metin); t.append((time.perf_counter() - t0) * 1000)
yaz(f"  40 kelimelik KR metin, 5000 terim: {len(h)} hit, medyan {statistics.median(t):.2f} ms")

yaz("== 4. 1000 segment x {11, 50, 500, 5000} terim: lookup_segments + gom medyan ==")
segs = tuple(seg("長老マルクスが水車小屋で待っています。 방앗간을 지나 Marcus by the mill.") for _ in range(1000))
def olc(store, etiket):
    t = []
    for _ in range(7):
        t0 = time.perf_counter()
        hs = store.lookup_segments(segs)
        terimleri_gom(segs, hs)
        t.append((time.perf_counter() - t0) * 1000)
    yaz(f"  {etiket:14s}: hit/segment={len(hs)//1000}, medyan {statistics.median(t):.1f} ms, min {min(t):.1f}, max {max(t):.1f}")
    return statistics.median(t)
taban = [("マルクス", "Marcus"), ("마르쿠스", "Marcus"), ("Marcus", "Marcus"), ("アイラ", "Ayla"), ("아일라", "Ayla"),
         ("水車小屋", "Değirmen"), ("방앗간", "Değirmen"), ("mill", "Değirmen"), ("長老", "İhtiyar"), ("장로", "İhtiyar"), ("elder", "İhtiyar")]
m11 = olc(sozluk(*taban), "11 terim")
dolgu = lambda n: [("ダミー" + format(i, "x") + "語", "D" + str(i)) for i in range(n)]
m50 = olc(sozluk(*taban, *dolgu(39)), "50 terim")
m500 = olc(sozluk(*taban, *dolgu(489)), "500 terim")
m5000 = olc(sozluk(*taban, *dolgu(4989)), "5000 terim")
# ilk karakter cesitliligi yuksek dolgu (bekci kumesi buyur)
import itertools
cesit = [(chr(0x4E00 + i) + chr(0x4E00 + i + 1), "C" + str(i)) for i in range(0, 4000, 2)]
m_cesit = olc(sozluk(*taban, *cesit), "11+2000 cesitli")
yaz(f"  oran 500/11 = {m500/m11:.2f}; 5000/11 = {m5000/m11:.2f}; cesitli/11 = {m_cesit/m11:.2f}")
# kapinin yolu (real_check #7 gibi): lookup + replace
t = []
s11 = sozluk(*taban)
for _ in range(7):
    t0 = time.perf_counter()
    hs = tuple(dataclasses.replace(h, segment_index=i) for i, sg in enumerate(segs) for h in s11.lookup(sg.text, sg.placeholders))
    terimleri_gom(segs, hs)
    t.append((time.perf_counter() - t0) * 1000)
yaz(f"  kapi yolu (lookup+replace) 11 terim: medyan {statistics.median(t):.1f} ms")

yaz("== 5. regex geri izleme: onek zinciri sozluk + en kotu metin ==")
# (?:a|ab|abc|...) benzeri: a, aa, aaa, ... aaaaaaaaaa (10 onek) + metin a*10000 (hicbiri sinirli degil)
onek = sozluk(*[("a" * n, "X" + str(n)) for n in range(2, 12)])
kotu = "a" * 10000
t0 = time.perf_counter(); h = onek.lookup(kotu); t1 = time.perf_counter()
yaz(f"  onek zinciri (a2..a11) x a*10000: {len(h)} hit, {(t1-t0)*1000:.1f} ms")
kotu2 = ("a" * 11 + "b") * 800
t0 = time.perf_counter(); h = onek.lookup(kotu2); t1 = time.perf_counter()
yaz(f"  (a*11 b) x 800: {len(h)} hit, {(t1-t0)*1000:.1f} ms")
kotu3 = " ".join("a" * 11 for _ in range(800))
t0 = time.perf_counter(); h = onek.lookup(kotu3); t1 = time.perf_counter()
yaz(f"  'a*11 ' x 800 (hepsi sinirli, 800 hit + 8000 onek adayi): {len(h)} hit, {(t1-t0)*1000:.1f} ms")
# 2-yollu dallanma trie: ab, ac, abd, abe, ... derin
dal = sozluk(*[("ab" * k + "c", "X" + str(k)) for k in range(1, 30)], *[("ab" * k + "d", "Y" + str(k)) for k in range(1, 30)])
kotu4 = "ab" * 5000
t0 = time.perf_counter(); h = dal.lookup(kotu4); t1 = time.perf_counter()
yaz(f"  dallanan trie (ab)^k c/d, metin (ab)^5000 (asla bitmez): {len(h)} hit, {(t1-t0)*1000:.1f} ms")

OUT.write_text("\n".join(satirlar) + "\n", encoding="utf-8")
print(f"yazildi -> {OUT.name}")
