"""TESTER-B tur 2 -- kit ciktisindan (r2-B1-mutant-kiti.txt) kapi basina ozet tablo.

    python .agents/tasks/T-007/tester_B/r2_ozet_tablo.py <kit_cikti_dosyasi>
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

KAPILAR = ["G1-mypy", "G2-birim", "G3-real", "G4-kapsam", "G5-tum"]
SATIR = re.compile(r"^([A-Za-z0-9-]+)\s+\[([.X]{5})\]\s+(.*?)\s+\(beklenen: (.*)\)\s*$")


def main() -> None:
    metin = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
    satirlar: list[tuple[str, str, str, str]] = []
    for ln in metin.splitlines():
        m = SATIR.match(ln)
        if m:
            satirlar.append((m.group(1), m.group(2), m.group(3), m.group(4)))
    tur1 = [s for s in satirlar if not s[0].startswith("R2-")]
    tur2 = [s for s in satirlar if s[0].startswith("R2-")]
    for ad, grup in (("TUR 1 KITI (53 davranis + 6 kontrol) -- regresyon", tur1), ("TUR 2 EKLERI (R2-*)", tur2)):
        dav = [s for s in grup if "kontrol" not in s[2].lower()]
        kon = [s for s in grup if "kontrol" in s[2].lower()]
        kacan = [s[0] for s in dav if "X" not in s[1]]
        yp = [s[0] for s in kon if "X" in s[1]]
        print(f"=== {ad} ===")
        print(f"davranis mutanti: {len(dav)}  yakalanan: {len(dav) - len(kacan)}  kacan: {kacan}")
        print(f"kontrol mutanti: {len(kon)}  kacan (dogru): {len(kon) - len(yp)}  yakalanan (yanlis pozitif): {yp}")
        print("kapi basina yakalama (davranis mutantlari):")
        for i, k in enumerate(KAPILAR):
            print(f"  {k:10s} {sum(1 for s in dav if s[1][i] == 'X'):3d} / {len(dav)}")
        print()
    print("| mutant | G1 | G2 | G3 | G4 | G5 | sonuc | beklenen |")
    print("|---|---|---|---|---|---|---|---|")
    for mid, durum, etiket, bek in satirlar:
        print(f"| {mid} | " + " | ".join(durum) + f" | {etiket.split('   ')[0]} | {bek} |")


if __name__ == "__main__":
    main()
