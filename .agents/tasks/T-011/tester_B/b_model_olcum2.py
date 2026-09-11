"""TESTER-B (T-011) -- gercek NMT ile ikinci olcum: KISMI gomme (reddedilen komsu aday sinir verir).

    python .agents/tasks/T-011/tester_B/b_model_olcum2.py

Stdout yalniz ASCII. Ham metinler: tester_B_evidence/model-olcum2-ham.txt
  J. `長老マルクス様が来た。` -> `İhtiyarマルクス様が来た。` (unvan gomulu, ad ham): ham vs gomulu; ad ciktida?
  K. Ayni cumle saygi eki OLMADAN (pozitif kontrol: tam gomme) ve KR esdegeri.
  L. real_check #7 yeniden (yalitilmis surecte, 7 tekrar).
"""
from __future__ import annotations

import dataclasses
import statistics
import sys
import time
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(KOK))

from src.contracts.models import Rect, Segment, TranslationRequest  # noqa: E402
from src.translate.local_nmt import LocalNmtProvider  # noqa: E402
from src.translate.sozluk import GlossaryStore, terimleri_gom  # noqa: E402

MODEL = KOK / "models" / "nllb-200-distilled-600M-ct2-int8"
SOZLUK = KOK / ".agents" / "tasks" / "T-011" / "fixtures" / "sozluk_ornek.json"
HAM = KOK / ".agents" / "tasks" / "T-011" / "tester_B_evidence" / "model-olcum2-ham.txt"
R = Rect(0, 0, 800, 36)


def main() -> int:
    out = open(HAM, "w", encoding="utf-8")
    p = LocalNmtProvider(model_dir=MODEL, threads=8)
    s = GlossaryStore(SOZLUK)

    def cevir(m: str, dil: str, gom: bool) -> tuple[str, str]:
        sg = (Segment(text=m, bbox=R),)
        if gom:
            sg = terimleri_gom(sg, s.lookup_segments(sg))
        return sg[0].text, p.translate(TranslationRequest(segments=sg, source_lang=dil, target_lang="tr")).translations[0]

    print("== J/K. kismi gomme ==")
    ornek = [("J0", "jpn_Jpan", "長老マルクス様が来た。", ["İhtiyar", "Marcus"]),
             ("J1", "kor_Hang", "장로 마르쿠스님이 오셨습니다.", ["İhtiyar", "Marcus"]),
             ("J2", "jpn_Jpan", "水車小屋のマルクス様", ["Değirmen", "Marcus"]),
             ("K0", "jpn_Jpan", "長老マルクスが来た。", ["İhtiyar", "Marcus"]),
             ("K1", "kor_Hang", "장로 마르쿠스가 오셨습니다.", ["İhtiyar", "Marcus"])]
    for ad, dil, m, hedefler in ornek:
        _, ham = cevir(m, dil, False)
        gk, gom = cevir(m, dil, True)
        hits = len(s.lookup(m))
        ham_v = [t for t in hedefler if t.lower() in ham.lower()]
        gom_v = [t for t in hedefler if t.lower() in gom.lower()]
        print(f"[{ad}] {dil} kaynak={m!r} hits={hits} gomulu={gk!r}\n     ham={ham!r}\n     gom={gom!r}\n     hamda={ham_v} gomuluda={gom_v}", file=out)
        print(f"  {ad} {dil}: hit={hits} hedef hamda {len(ham_v)}/{len(hedefler)} gomuluda {len(gom_v)}/{len(hedefler)}")
    p.close()

    print("== L. real_check #7 yeniden (yalitilmis) ==")
    segs = tuple(Segment(text="長老マルクスが水車小屋で待っています。", bbox=Rect(0, i, 1, 1)) for i in range(1000))
    t: list[float] = []
    for _ in range(7):
        t0 = time.perf_counter()
        hits = tuple(dataclasses.replace(h, segment_index=i) for i, sg in enumerate(segs) for h in s.lookup(sg.text, sg.placeholders))
        terimleri_gom(segs, hits)
        t.append((time.perf_counter() - t0) * 1000)
    print(f"  [L] kapi yolu medyan {statistics.median(t):.1f} ms, min {min(t):.1f}, max {max(t):.1f} (< 50)")
    out.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
