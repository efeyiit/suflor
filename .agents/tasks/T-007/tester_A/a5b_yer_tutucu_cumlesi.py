"""Tester-A · A5b — "yalnız yer tutucudan oluşan cümle" sınıfı, gerçek modelle (ayrı süreç).

    python .agents/tasks/T-007/tester_A/a5b_yer_tutucu_cumlesi.py

K3 Y2 süzgeci harf/rakam arar; `{PLAYER}!`, `{0}!`, `{0}。` gibi parçalar yer
tutucunun İÇİNDEKİ harf/rakam yüzünden modele gider. Ölçü: aynı kalıplar
(a) yer tutucuyla, (b) yer tutucu yerine gerçek adla ("Marcus"). Her çıktı
için yalnız: uzunluk, uydurma işareti ("hayır" alt dizesi — KRT Y2'nin
ölçtüğü uydurma kalıbı), yer tutucu var mı. Metin basılmaz.
"""
from __future__ import annotations

import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(KOK))

from src.contracts.models import Rect, Segment, TranslationRequest  # noqa: E402
from src.translate.local_nmt import LocalNmtProvider  # noqa: E402

MODEL = KOK / "models" / "nllb-200-distilled-600M-ct2-int8"

# (kaynak dili, yer tutuculu metin, yer tutucu, gerçek adlı eş)
KALIPLAR: list[tuple[str, str, str, str]] = [
    ("eng_Latn", "{PLAYER}! Wait for me!", "{PLAYER}", "Marcus! Wait for me!"),
    ("eng_Latn", "{0}! The elder is waiting.", "{0}", "Marcus! The elder is waiting."),
    ("eng_Latn", "{NAME}. Come here.", "{NAME}", "Marcus. Come here."),
    ("eng_Latn", "{0}? Is that you?", "{0}", "Marcus? Is that you?"),
    ("eng_Latn", "Well done, {0}. Take the road.", "{0}", "Well done, Marcus. Take the road."),  # yer tutucu cümle İÇİNDE: kontrol
    ("jpn_Jpan", "{0}！待って！", "{0}", "マルクス！待って！"),
    ("jpn_Jpan", "{0}。東へ行きなさい。", "{0}", "マルクス。東へ行きなさい。"),
    ("kor_Hang", "{0}! 기다려!", "{0}", "마르쿠스! 기다려!"),
]


def istek(metin: str, kaynak: str, ph: tuple[str, ...]) -> TranslationRequest:
    return TranslationRequest(
        segments=(Segment(text=metin, bbox=Rect(0, 0, 800, 36), placeholders=ph),),
        source_lang=kaynak, target_lang="tr",
    )


def main() -> int:
    print("Tester-A A5b -- yalniz yer tutucu cumlesi sinifi, gercek model")
    p = LocalNmtProvider(model_dir=MODEL, threads=8)
    uyduran = 0
    ad_uyduran = 0
    for i, (dil, metin, ph, adli) in enumerate(KALIPLAR, 1):
        c = p.translate(istek(metin, dil, (ph,))).translations[0]
        ca = p.translate(istek(adli, dil, ())).translations[0]
        u = "hayır" in c.lower() or "hayir" in c.lower()
        ua = "hayır" in ca.lower() or "hayir" in ca.lower()
        uyduran += u
        ad_uyduran += ua
        print(f"  [{i}] {dil} yer tutuculu: uzunluk={len(c):3d} uydurma={u!s:5} yt_var={ph in c!s:5} | gercek adli: uzunluk={len(ca):3d} uydurma={ua!s:5}")
    p.close()
    print()
    print(f"A5b: {len(KALIPLAR)} kalip -> yer tutuculu {uyduran} uydurma, gercek adli {ad_uyduran} uydurma (bulgu: keskinlik, known_gaps)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
