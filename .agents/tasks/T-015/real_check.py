"""T-015 kabul kapisi -- hedef tarafi duzeltme, GERCEK NMT.

    python .agents/tasks/T-015/real_check.py

Sefe aittir. Stdout ASCII.
  1. Adlar-yalniz sozluk (T-011 fixture v3) + demo hedef_duzeltmeler: 10 unvan+ad segmenti (JP/KR) gomulu ceviride
     Ingilizce unvan ("elder") ve ad varyanti ("marks/markos/eira/aira") sayisi -> duzeltme SONRASI 0
     (pozitif kontrol: duzeltme ONCESI en az 1 -- Tester-B: 'Elder Marcus' 1/10)
  2. Duzeltme metnin geri kalanini degistirmez: duzeltilen ciktida duzeltme kelimeleri disinda fark yok (kelime bazli)
  3. Bilesik cumle (Y-B1): ham dogru kalan cumlede duzeltici hicbir sey degistirmez (kimlik)
  4. 1000 ceviri x demo kurallari < 20 ms
"""
from __future__ import annotations

import re
import sys
import time
from pathlib import Path

KOK = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(KOK))

from src.contracts.models import Rect, Segment, TranslationRequest  # noqa: E402

ihlaller: list[str] = []


def ihlal(m: str) -> None:
    ihlaller.append(m); print(f"  IHLAL  {m}")


def tamam(m: str) -> None:
    print(f"  ok     {m}")


SIZINTI = re.compile(r"\b(elder|marks|markos|markus|eira|aira)\b", re.IGNORECASE)


def main() -> int:
    print("T-015 real_check -- hedef tarafi duzeltme, gercek NMT")
    from src.pipeline.anlik import cevir_yap
    from src.translate.hedef_duzeltici import HedefDuzeltici
    from src.translate.local_nmt import LocalNmtProvider
    from src.translate.sozluk import GlossaryStore
    from src.contracts.models import OcrPreset, TextBlock

    nmt = LocalNmtProvider(model_dir=KOK / "models/nllb-200-distilled-600M-ct2-int8", threads=8)
    sozluk = GlossaryStore(KOK / ".agents/tasks/T-011/fixtures/sozluk_ornek.json")   # adlar-yalniz
    duzeltici = HedefDuzeltici.dosyadan(KOK / "demo/sozluk_ornek.json")
    segmentler = [("jpn_Jpan", "長老マルクス"), ("jpn_Jpan", "隊長アイラ"), ("jpn_Jpan", "村長マルクス"), ("jpn_Jpan", "騎士アイラ"), ("jpn_Jpan", "王女アイラ"),
                  ("kor_Hang", "장로 마르쿠스"), ("kor_Hang", "대장 아일라"), ("kor_Hang", "촌장 마르쿠스"), ("kor_Hang", "기사 아일라"), ("kor_Hang", "공주 아일라")]
    once = 0; sonra = 0; kelime_farki_kotu = 0
    for dil, m in segmentler:
        blok = [TextBlock(text=m, bbox=Rect(0, 0, 400, 40), confidence=0.9)]
        _, ham_c = cevir_yap(nmt, sozluk, blok, dil, OcrPreset.DIALOGUE)
        _, duz_c = cevir_yap(nmt, sozluk, blok, dil, OcrPreset.DIALOGUE, duzeltici=duzeltici)
        once += sum(1 for c in ham_c if SIZINTI.search(c)); sonra += sum(1 for c in duz_c if SIZINTI.search(c))
        # 2: kelime bazli fark yalniz duzeltme kelimelerinde
        for h, d in zip(ham_c, duz_c):
            hw, dw = h.split(), d.split()
            if len(hw) != len(dw) or any(a != b and not SIZINTI.search(a) for a, b in zip(hw, dw)):
                kelime_farki_kotu += 1
    (tamam if once >= 1 else ihlal)(f"[1a] pozitif kontrol: duzeltme ONCESI sizinti {once}/10 segment (>= 1)")
    (tamam if sonra == 0 else ihlal)(f"[1b] duzeltme SONRASI sizinti {sonra}/10 (0)")
    (tamam if kelime_farki_kotu == 0 else ihlal)(f"[2] duzeltme disinda kelime farki olan cikti: {kelime_farki_kotu} (0)")

    # 3 bilesik cumle: ham dogru; duzeltici kimlik
    b = "마을 장로가 마르쿠스를 불렀습니다."
    r = nmt.translate(TranslationRequest(segments=(Segment(text=b, bbox=Rect(0, 0, 1, 1)),), source_lang="kor_Hang", target_lang="tr")).translations[0]
    (tamam if duzeltici.duzelt(r) == r or SIZINTI.search(r) else ihlal)(f"[3] bilesik cumlede duzeltici degisiklik yapmadi={duzeltici.duzelt(r) == r} (sizinti varsa duzeltir: {bool(SIZINTI.search(r))})")

    # 4 butce
    metinler = [f"Elder Marks ve Eira, {i}. kez koye geldi." for i in range(1000)]
    t = []
    for _ in range(5):
        t0 = time.perf_counter(); duzeltici.hepsini_duzelt(metinler); t.append((time.perf_counter() - t0) * 1000)
    (tamam if min(t) < 20 else ihlal)(f"[4] 1000 ceviri x {len(duzeltici)} kural: en kucuk {min(t):.1f} ms (< 20)")
    nmt.close()
    print()
    if ihlaller: print(f"REAL_CHECK: {len(ihlaller)} IHLAL"); return 1
    print("REAL_CHECK: TEMIZ"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
