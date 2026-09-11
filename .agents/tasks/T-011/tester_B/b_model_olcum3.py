"""TESTER-B (T-011) -- real_check #4 icin POZITIF KONTROL (kural 10): 'Elder' sizmasi olcu ATESLEYEBILIYOR mu.

    python .agents/tasks/T-011/tester_B/b_model_olcum3.py

Yalniz `마르쿠스 -> Marcus` iceren sozlukle (`장로` yok) `장로 마르쿠스` -> `장로 Marcus` -> ciktida 'Elder' var mi
(G2 boyle dedi). Varsa #4'un 'Elder yok' olcusu bu sinifta ateslenebilir; yoksa #4 bos kontrol.
Ham metin: tester_B_evidence/model-olcum3-ham.txt. Stdout ASCII.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(KOK))

from src.contracts.models import Rect, Segment, TranslationRequest  # noqa: E402
from src.translate.local_nmt import LocalNmtProvider  # noqa: E402
from src.translate.sozluk import GlossaryStore, terimleri_gom  # noqa: E402

MODEL = KOK / "models" / "nllb-200-distilled-600M-ct2-int8"
HAM = KOK / ".agents" / "tasks" / "T-011" / "tester_B_evidence" / "model-olcum3-ham.txt"
R = Rect(0, 0, 800, 36)


def main() -> int:
    out = open(HAM, "w", encoding="utf-8")
    p = LocalNmtProvider(model_dir=MODEL, threads=8)
    with tempfile.TemporaryDirectory() as td:
        pj = Path(td) / "ad.json"
        pj.write_text(json.dumps({"terimler": [{"kaynak": "마르쿠스", "hedef": "Marcus"}, {"kaynak": "マルクス", "hedef": "Marcus"}]}, ensure_ascii=False), encoding="utf-8")
        s = GlossaryStore(pj)
        for ad, dil, m in [("M0", "kor_Hang", "장로 마르쿠스"), ("M1", "kor_Hang", "장로 마르쿠스가 오셨습니다."), ("M2", "jpn_Jpan", "長老マルクス")]:
            sg = (Segment(text=m, bbox=R),)
            gs = terimleri_gom(sg, s.lookup_segments(sg))
            gom = p.translate(TranslationRequest(segments=gs, source_lang=dil, target_lang="tr")).translations[0]
            print(f"[{ad}] {dil} kaynak={m!r} gomulu={gs[0].text!r}\n     gom={gom!r}\n     Elder={'Elder' in gom} Ihtiyar={'İhtiyar' in gom}", file=out)
            print(f"  {ad} {dil}: yalniz ad gomulu -> Elder={'Elder' in gom} Ihtiyar={'İhtiyar' in gom}")
    p.close()
    out.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
