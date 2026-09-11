"""T-011 K5 sure olcumu (implementer).

    python .agents/tasks/T-011/evidence/sure-olcumu.py

1000 segment; sozluk: (a) kapinin fixture v2'si (11 terim), (b) 50 terim,
(c) 500 terim. Iki yol: `lookup_segments` + `terimleri_gom` (onerilen) ve
kapinin #7 yolu (`lookup` + `dataclasses.replace` + `terimleri_gom`). 7 kosum,
medyan ms. Iki metin: JP (3 hit/segment) ve EN (3 hit/segment). Stdout ASCII;
metin basilmaz.
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
    print(f"T-011 K5 sure olcumu -- python {sys.version.split()[0]}, 1000 segment, 7 kosum medyani (ms)")
    fixture_terimler = json.loads(FIXTURE.read_bytes())["terimler"]
    with tempfile.TemporaryDirectory() as td:
        sozlukler: list[tuple[str, GlossaryStore]] = []
        for etiket, ekstra in (("fixture v2", 0), ("50 terim", 50 - len(fixture_terimler)), ("500 terim", 500 - len(fixture_terimler))):
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
