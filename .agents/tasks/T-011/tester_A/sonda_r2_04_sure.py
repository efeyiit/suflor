"""Sonda r2-04: K5 v3 -- hit sayisinda dogrusallik, 8000 uyeli zincir (canli/olu), lookup_segments 1000 x fixture v3,
onek zinciri a*10000 (tur 1: 850 ms). Izleyicisiz, medyan / 7 tekrar; iki kez kosulur (baska surec yuk bindirebilir)."""
from __future__ import annotations

import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from yardimci import KOK, sozluk  # noqa: E402
from src.contracts.models import Rect, Segment  # noqa: E402
from src.translate.sozluk import GlossaryStore, terimleri_gom  # noqa: E402

OUT = KOK / ".agents/tasks/T-011/tester_A_evidence/r2-sonda-04-sure.txt"
satirlar: list[str] = []


def yaz(s: str) -> None:
    satirlar.append(s)
    print(s.encode("ascii", "backslashreplace").decode("ascii"))


def medyan_ms(f, n=7) -> float:
    t = []
    for _ in range(n):
        t0 = time.perf_counter()
        f()
        t.append((time.perf_counter() - t0) * 1000)
    return statistics.median(t)


assert sys.gettrace() is None and "coverage" not in sys.modules
st = sozluk(("マルクス", "Marcus"), ("長老", "İhtiyar"))
for tur in (1, 2):
    yaz(f"== kosum {tur}")
    yaz("-- hit sayisi (bosluklu, zincirsiz): k hit -> ms   [2x hit -> ~2x sure beklenir]")
    onceki = None
    for k in (500, 1000, 2000, 4000, 8000):
        m = "長老マルクス " * (k // 2)
        n = len(st.lookup(m))
        ms = medyan_ms(lambda: st.lookup(m))
        oran = f" oran {ms / onceki:.2f}" if onceki else ""
        yaz(f"   {k:5d} hit: {ms:7.2f} ms ({n} hit){oran}")
        onceki = ms
    yaz("-- zincir (bitisik, canli): k uye -> ms")
    onceki = None
    for k in (1000, 2000, 4000, 8000):
        m = "マルクス" * k
        n = len(st.lookup(m))
        ms = medyan_ms(lambda: st.lookup(m))
        oran = f" oran {ms / onceki:.2f}" if onceki else ""
        yaz(f"   {k:5d} uye: {ms:7.2f} ms ({n} hit){oran}")
        onceki = ms
    yaz("-- zincir OLU (sag dis uc `ー` Katakana|Katakana): k uye -> ms, 0 hit")
    onceki = None
    for k in (1000, 2000, 4000, 8000):
        m = "マルクス" * k + "ー"
        n = len(st.lookup(m))
        ms = medyan_ms(lambda: st.lookup(m))
        oran = f" oran {ms / onceki:.2f}" if onceki else ""
        yaz(f"   {k:5d} uye: {ms:7.2f} ms ({n} hit){oran}")
        onceki = ms
    yaz("-- zincir OLU (sol dis uc): 8000 uye")
    m = "ー" + "マルクス" * 8000
    yaz(f"   8000 uye: {medyan_ms(lambda: st.lookup(m)):7.2f} ms ({len(st.lookup(m))} hit)")
    yaz("-- onek zinciri a2..a11 + a*10000 (tur 1: 909 hit, 850 ms)")
    st2 = sozluk(*[("a" * k, "A" + str(k)) for k in range(2, 12)])
    m = "a" * 10000
    h = st2.lookup(m)
    yaz(f"   {len(h)} hit, son iki: {[(x.start, x.end) for x in h[-2:]]}, kaplama {sum(x.end - x.start for x in h)}/10000: {medyan_ms(lambda: st2.lookup(m), 3):7.2f} ms")
    yaz("-- lookup_segments + terimleri_gom, 1000 segment x fixture v3 (7 terim) (real_check #8 yolu, modelsiz)")
    fx = GlossaryStore(KOK / ".agents/tasks/T-011/fixtures/sozluk_ornek.json")
    segs = tuple(Segment(text="長老マルクスが水車小屋で待っています。", bbox=Rect(0, i, 1, 1)) for i in range(1000))
    yaz(f"   {len(fx)} terim, {len(fx.lookup_segments(segs))} hit: {medyan_ms(lambda: terimleri_gom(segs, fx.lookup_segments(segs))):7.2f} ms (< 50)")
    segs2 = tuple(Segment(text="長老マルクスが水車小屋で待っています。 방앗간을 지나 Marcus by the mill.", bbox=Rect(0, i, 1, 1)) for i in range(1000))
    yaz(f"   karisik 3 dil, {len(fx.lookup_segments(segs2))} hit: {medyan_ms(lambda: terimleri_gom(segs2, fx.lookup_segments(segs2))):7.2f} ms")

OUT.write_text("\n".join(satirlar) + "\n", encoding="utf-8")
print(f"yazildi -> {OUT.name}")
