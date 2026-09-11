"""Tester-A tur 2 / A2-4 -- tur 1 A6 kanit dosyasindaki GERCEK OCR kutu listelerini (E prototipi
kosumu, `a6-aday-E-gercek-ocr.txt`, 33 fixture) bugunku `satirlari_birlestir`e yeniden besler
ve 'N kutu -> M blok; parca sayilari [...]' satirini tur 1 ciktisiyla karsilastirir.
Girdi degisimi (T-009 tanima modeli, kutu kumesi) ile birlestirici degisimini AYIRIR.

    python .agents/tasks/T-008/tester_A/a6_gecmis_geometri_regresyon.py <kanit.txt>
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(KOK))
from src.contracts.models import Rect, TextBlock  # noqa: E402
from src.ocr.satir_birlestirici import satirlari_birlestir  # noqa: E402

BASLIK = re.compile(r"^\s+\[(?P<ad>[^\]]+)\] (?P<n>\d+) kutu -> (?P<m>\d+) blok; parca sayilari (?P<lb>\[.*\])$")
KUTU = re.compile(r"^\s+kutular \(x,y,w,h\): (?P<k>\[.*\])$")


def main() -> int:
    yol = Path(sys.argv[1])
    satirlar = yol.read_text(encoding="utf-8", errors="replace").splitlines()
    fark = 0
    toplam = 0
    i = 0
    while i < len(satirlar):
        m = BASLIK.match(satirlar[i])
        if m and i + 1 < len(satirlar):
            k = KUTU.match(satirlar[i + 1])
            if k:
                kutular = ast.literal_eval(k.group("k"))
                bl = [TextBlock(text=f"w{j}", bbox=Rect(*kk), confidence=0.9) for j, kk in enumerate(kutular)]
                c = satirlari_birlestir(bl)
                lb = [len(x.line_boxes) or 1 for x in c]
                eski = (int(m.group("n")), int(m.group("m")), ast.literal_eval(m.group("lb")))
                yeni = (len(bl), len(c), lb)
                toplam += 1
                durum = "AYNI " if eski == yeni else "FARK "
                if eski != yeni:
                    fark += 1
                print(f"  {durum} [{m.group('ad')}] tur1: {eski[0]} -> {eski[1]} {eski[2]}  |  simdi: {yeni[0]} -> {yeni[1]} {yeni[2]}")
                i += 2
                continue
        i += 1
    print()
    print(f"{toplam} fixture geometrisi yeniden beslendi; birlestirici ciktisi farkli: {fark}")
    return 1 if fark else 0


if __name__ == "__main__":
    raise SystemExit(main())
