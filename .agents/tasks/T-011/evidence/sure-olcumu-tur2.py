"""T-011 K5 sure olcumu (implementer, tur 2).

    python .agents/tasks/T-011/evidence/sure-olcumu-tur2.py

1. 1000 segment; sozluk: kapinin fixture v3'u (7 terim), 50 terim, 500 terim;
   iki yol (`lookup_segments`+gom ve kapinin #8 yolu), JP + EN metin; 7 kosum
   medyani (butce 50 ms).
2. Hit yogunlugu (Tester-A D-A1): tek segmentte 500..8000 hit, 2x hit -> sure
   orani (tur 1: 3.2-3.9x = karesel; hedef ~2x = dogrusal).
3. Zincir aramasi: 8000 uyeli gecerli zincir, sag/sol/iki uc olu zincir,
   ortadan noktalamayla bolunen zincir; onek zinciri `a2..a11` + `a`*10000
   (Tester-A sonda 4 §5: tur 1'de 850 ms).
Stdout ASCII; metin basilmaz.
"""
from __future__ import annotations

import dataclasses
import json
import statistics
import sys
import tempfile
import time
from collections.abc import Callable
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(KOK))

from src.contracts.models import Rect, Segment  # noqa: E402
from src.translate.sozluk import GlossaryStore, terimleri_gom  # noqa: E402

FIXTURE = KOK / ".agents" / "tasks" / "T-011" / "fixtures" / "sozluk_ornek.json"
JP = "長老マルクスが水車小屋で待っています。"
EN = "The elder Marcus waits by the mill and the terms tell tales."


def medyan_ms(f: Callable[[], object], n: int = 7) -> float:
    r: list[float] = []
    for _ in range(n):
        t0 = time.perf_counter()
        f()
        r.append((time.perf_counter() - t0) * 1000)
    return statistics.median(r)


def main() -> int:
    print(f"T-011 K5 sure olcumu (tur 2) -- python {sys.version.split()[0]}, 7 kosum medyani (ms)")
    fixture_terimler = json.loads(FIXTURE.read_bytes())["terimler"]
    with tempfile.TemporaryDirectory() as td:
        print("== 1. 1000 segment x terim sayisi ==")
        sozlukler: list[tuple[str, GlossaryStore]] = []
        for etiket, ekstra in (("fixture v3", 0), ("50 terim", 50 - len(fixture_terimler)), ("500 terim", 500 - len(fixture_terimler))):
            yol = Path(td) / f"{ekstra}.json"
            terimler = fixture_terimler + [{"kaynak": f"terim{i:03d}", "hedef": f"Hedef{i:03d}"} for i in range(ekstra)]
            yol.write_text(json.dumps({"terimler": terimler}, ensure_ascii=False), encoding="utf-8")
            t0 = time.perf_counter()
            s = GlossaryStore(yol)
            print(f"  yukleme {etiket:>10} ({len(s):3d} terim): {(time.perf_counter() - t0) * 1000:6.1f} ms")
            sozlukler.append((etiket, s))
        for metin_adi, metin in (("JP", JP), ("EN", EN)):
            segs = tuple(Segment(text=metin, bbox=Rect(0, i, 1, 1)) for i in range(1000))
            for etiket, s in sozlukler:
                hits = s.lookup_segments(segs)
                onerilen = medyan_ms(lambda: terimleri_gom(segs, s.lookup_segments(segs)))
                kapi = medyan_ms(
                    lambda: terimleri_gom(
                        segs,
                        tuple(dataclasses.replace(h, segment_index=i) for i, sg in enumerate(segs) for h in s.lookup(sg.text, sg.placeholders)),
                    )
                )
                print(f"  {metin_adi} x {etiket:>10}: lookup_segments+gom {onerilen:6.1f} ms | kapi yolu (lookup+replace+gom) {kapi:6.1f} ms | hit {len(hits)} | butce 50")

        s = sozlukler[0][1]
        print("== 2. hit yogunlugu: tek segment, 2x hit -> sure orani (dogrusal ~2x; tur 1 karesel 3.2-3.9x) ==")
        onceki = 0.0
        for n in (500, 1000, 2000, 4000, 8000):
            metin = "Marcus " * n
            hit = len(s.lookup(metin))
            m = medyan_ms(lambda: s.lookup(metin), 5)
            oran = f"{m / onceki:.2f}x" if onceki else "-"
            print(f"  hit={hit:5d} len={len(metin):6d} medyan {m:7.1f} ms  (onceki 2x hit'e oran: {oran})")
            onceki = m
        segs1 = (Segment(text="Marcus " * 8000, bbox=Rect(0, 0, 1, 1), placeholders=("{0}",)),)
        hits1 = s.lookup_segments(segs1)
        print(f"  gom 8000 hit tek segment: medyan {medyan_ms(lambda: terimleri_gom(segs1, hits1), 5):.1f} ms")

        print("== 3. zincir aramasi (8000 uye) ==")
        for etiket, metin in (
            ("gecerli zincir", "Marcus" * 8000),
            ("sag ucu olu (+x)", "Marcus" * 8000 + "x"),
            ("sol ucu olu (x+)", "x" + "Marcus" * 8000),
            ("iki ucu olu", "x" + "Marcus" * 8000 + "x"),
            ("ortadan noktalama, sag yarisi olu", "Marcus" * 4000 + "-" + "Marcus" * 4000 + "x"),
        ):
            hit = len(s.lookup(metin))
            print(f"  {etiket:34s} hit={hit:5d} medyan {medyan_ms(lambda: s.lookup(metin), 5):7.1f} ms")
        yol = Path(td) / "onek.json"
        yol.write_text(json.dumps({"terimler": [{"kaynak": "a" * k, "hedef": "A" * k} for k in range(2, 12)]}), encoding="utf-8")
        s2 = GlossaryStore(yol)
        for etiket, metin in (("onek zinciri a2..a11 + a*10000", "a" * 10000), ("ayni, sag ucu olu (+b)", "a" * 10000 + "b")):
            hit = len(s2.lookup(metin))
            print(f"  {etiket:34s} hit={hit:5d} medyan {medyan_ms(lambda: s2.lookup(metin), 3):7.1f} ms (tur 1: 909 hit 850 ms)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
