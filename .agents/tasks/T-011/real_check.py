"""T-011 kabul kapisi -- gercek NMT ile sozluk gomme.

    python .agents/tasks/T-011/real_check.py

Sefe aittir. Stdout yalniz ASCII; metin basilmaz (yalniz sayilar/boolean).
  1. G1'in 6 cumlesi: lookup -> gom -> translate -> hedef terim var (6/6)
  2. POZITIF KONTROL: gommeden -> en az 2'sinde hedef terim YOK
  3. KR degirmen cumlesi: "Degirmen" var, "Dogu'ya dogru Dogu'ya dogru" tekrari YOK
  4. Unvan: 장로 마르쿠스 -> "Elder" YOK, "Ihtiyar" ve "Marcus" var
  5. Cins isim raporu (dusurmez)
  6. 1000 segment x 15 terim < 50 ms
"""
from __future__ import annotations

import statistics
import sys
import time
from pathlib import Path

KOK = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(KOK))

from src.contracts.models import Rect, Segment, TranslationRequest  # noqa: E402

MODEL = KOK / "models" / "nllb-200-distilled-600M-ct2-int8"
SOZLUK = Path(__file__).resolve().parent / "fixtures" / "sozluk_ornek.json"
ihlaller: list[str] = []


def ihlal(m: str) -> None:
    ihlaller.append(m); print(f"  IHLAL  {m}")


def tamam(m: str) -> None:
    print(f"  ok     {m}")


def main() -> int:
    print("T-011 real_check -- sozluk gomme, gercek NMT")
    try:
        from src.translate.sozluk import GlossaryStore, terimleri_gom
    except Exception as e:  # noqa: BLE001
        ihlal(f"src.translate.sozluk import edilemedi: {type(e).__name__}: {e}"); return 1
    from src.translate.local_nmt import LocalNmtProvider
    p = LocalNmtProvider(model_dir=MODEL, threads=8)
    s = GlossaryStore(SOZLUK)

    def cevir(metinler: list[str], dil: str, gom: bool) -> list[str]:
        segs = tuple(Segment(text=t, bbox=Rect(0, i * 40, 800, 36)) for i, t in enumerate(metinler))
        if gom:
            hits = []
            for i, seg in enumerate(segs):
                for h in s.lookup(seg.text):
                    hits.append(type(h)(source_term=h.source_term, target_term=h.target_term, start=h.start, end=h.end, segment_index=i, note=h.note))
            segs = terimleri_gom(segs, tuple(hits))
        return list(p.translate(TranslationRequest(segments=segs, source_lang=dil, target_lang="tr")).translations)

    # 1 + 2
    ornek = [("jpn_Jpan", "長老マルクス", "Marcus"), ("jpn_Jpan", "マルクスがあなたを待っています。", "Marcus"),
             ("jpn_Jpan", "水車小屋を過ぎて東の道を行きなさい。", "Değirmen"), ("kor_Hang", "장로 마르쿠스", "Marcus"),
             ("kor_Hang", "방앗간을 지나 동쪽 길로 가십시오.", "Değirmen"), ("eng_Latn", "The elder Marcus waits by the mill.", "Değirmen")]
    var_gom = 0; yok_ham = 0
    for dil, m, hedef in ornek:
        g = cevir([m], dil, True)[0]; h = cevir([m], dil, False)[0]
        var_gom += hedef.lower() in g.lower(); yok_ham += hedef.lower() not in h.lower()
    (tamam if var_gom == 6 else ihlal)(f"[1] gomulu: hedef terim {var_gom}/6 ciktida")
    (tamam if yok_ham >= 2 else ihlal)(f"[2] pozitif kontrol: gommeden {yok_ham}/6'da hedef YOK (>= 2)")

    # 3
    c = cevir(["방앗간을 지나 동쪽 길로 가십시오."], "kor_Hang", True)[0].lower().replace("ğ", "g")
    tekrar = "dogu'ya dogru dogu'ya dogru" in c
    (tamam if "degirmen" in c and not tekrar else ihlal)(f"[3] KR: degirmen={'degirmen' in c} tekrar={tekrar}")

    # 4
    u = cevir(["장로 마르쿠스"], "kor_Hang", True)[0]
    (tamam if "Elder" not in u and "İhtiyar" in u and "Marcus" in u else ihlal)(
        f"[4] unvan: Elder={'Elder' in u} Ihtiyar={'İhtiyar' in u} Marcus={'Marcus' in u}")

    # 5 rapor
    r = cevir(["村は東にある。"], "jpn_Jpan", True)[0]
    tamam(f"[5] cins isim (koy) raporu: kesme isareti var={chr(39) in r}  ({len(r)} kar.)")

    # 6 sure
    segs = tuple(Segment(text="長老マルクスが水車小屋で待っています。", bbox=Rect(0, i, 1, 1)) for i in range(1000))
    t = []
    for _ in range(5):
        t0 = time.perf_counter()
        hits = tuple(type(h)(source_term=h.source_term, target_term=h.target_term, start=h.start, end=h.end, segment_index=i, note=h.note)
                     for i, sg in enumerate(segs) for h in s.lookup(sg.text))
        terimleri_gom(segs, hits); t.append((time.perf_counter() - t0) * 1000)
    (tamam if statistics.median(t) < 50 else ihlal)(f"[6] 1000 segment lookup+gom medyan {statistics.median(t):.1f} ms (< 50)")
    p.close()
    print()
    if ihlaller: print(f"REAL_CHECK: {len(ihlaller)} IHLAL"); return 1
    print("REAL_CHECK: TEMIZ"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
