"""tester_B tur 6 -- BULGU N1/N2'nin olcumu.

Soru: kararin/env.md'nin iki olcu iddiasi FIXTURE tabaninda tutuyor mu?
  N1  "M5 (sag tarafi `nxt` birakan) -> olcu 2, 5 ve 6 kirilmali"
  N2  "M4 (indeks sirasi) -> olcu 3/3b ve kit geo kirilmali"

Yontem: sefin kitinin fixture'lari `sorgu_kaydi()` ile kosulur; her miras
sinirinda (a) sol tarafin OKUMA-sirasi-son ile INDEKS-sirasi-son blogu ayni mi
(ayni ise M4 orada GORUNMEZ), (b) sag taraf cok bloklu mu (tek bloklu ise M5
orada GORUNMEZ) yazdirilir.

Basari kosulu (betigin kendi karari): olcu 3b'de M4 gorunmez VE olcu 5'in her
iki sinirinda M5 gorunmez -- yani iki bulgu da HALA gecerli. Fixture'lar
guclendirilirse betik BASARISIZ verir ve bulgular kapanmis demektir.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
for yol in (str(REPO), str(REPO / ".agents" / "tasks" / "T-004")):
    if yol not in sys.path:
        sys.path.insert(0, yol)

from olcu_kiti import (  # noqa: E402
    OLCU6_ALT_SINIRLAR,
    okuma_sirasi,
    olcu3_fixture,
    olcu3b_fixture,
    olcu5_fixture,
    sorgu_kaydi,
)
from src.contracts.models import OcrPreset  # noqa: E402
from src.ocr import normalizer as N  # noqa: E402

print("KARARIN OLCU IDDIALARININ FIXTURE TABANI (tester_B, tur 6)")
print("soru: 'M4 -> olcu 3b kirilmali' ve 'M5 -> olcu 5 kirilmali' cumleleri tutuyor mu?\n")

m4_gorunur: dict[str, list[bool]] = {}
m5_gorunur: dict[str, list[bool]] = {}
for ad, f, pr in (
    ("olcu3 ", olcu3_fixture, OcrPreset.DIALOGUE),
    ("olcu3 ", olcu3_fixture, OcrPreset.TOOLTIP),
    ("olcu3b", olcu3b_fixture, OcrPreset.DIALOGUE),
    ("olcu5 ", olcu5_fixture, OcrPreset.DIALOGUE),
):
    blocks = f()
    with sorgu_kaydi() as kayit:
        N.normalize(blocks, pr)
    miras = [s for s in kayit if s.miras]
    anahtar = f"{ad.strip()}/{pr.name}"
    m4_gorunur[anahtar] = []
    m5_gorunur[anahtar] = []
    print(f"{ad} {pr.name:9s} miras_sinir={len(miras)}")
    for s in miras:
        sol_okuma = okuma_sirasi(blocks, s.sol_sb)[-1]
        sol_indeks = max(s.sol_sb)
        sag_okuma = okuma_sirasi(blocks, s.sag_sb)[0]
        sag_indeks = min(s.sag_sb)
        m4 = sol_okuma != sol_indeks
        m5 = len(s.sag_sb) > 1
        m4_gorunur[anahtar].append(m4)
        m5_gorunur[anahtar].append(m5)
        print(f"    sol_sb={s.sol_sb} okuma_son={sol_okuma} indeks_son={sol_indeks}"
              f"  {'AYRISIR (M4 gorunur)' if m4 else 'AYNI  (M4 GORUNMEZ)'}")
        print(f"    sag_sb={s.sag_sb} okuma_ilk={sag_okuma} indeks_ilk={sag_indeks}"
              f"  {'COK BLOKLU (M5 gorunur)' if m5 else 'TEK BLOKLU (M5 GORUNMEZ)'}")
    print()

b3b = olcu3b_fixture()
print("olcu3b bloklarinin okuma sirasi:",
      sorted(range(len(b3b)), key=lambda i: (b3b[i].bbox.y, b3b[i].bbox.x, i)))
print("kitin derlem alt sinirlari arasinda coklu_sag VAR:", OLCU6_ALT_SINIRLAR["coklu_sag"])
print("olcu5 fixture'inda coklu_sag:", sum(m5_gorunur["olcu5/DIALOGUE"]),
      " -> olcu 5'in SAG TARAF yarisi ayirt edici DEGIL")

hata = []
if any(m4_gorunur["olcu3b/DIALOGUE"]):
    hata.append("olcu3b artik SIRASIZ -- N2 bulgusu kapanmis, verdict guncellensin")
if any(m5_gorunur["olcu5/DIALOGUE"]):
    hata.append("olcu5 artik COK BLOKLU aday uretiyor -- N1 bulgusu kapanmis, verdict guncellensin")
if not any(m4_gorunur["olcu3/DIALOGUE"]):
    hata.append("olcu3 DIALOGUE'da M4 gorunmuyor -- olcu 3'un M4 iddiasi da bos olurdu")
print()
print("=== SONUC ===")
print("BASARILI: N1 ve N2 bulgulari HALA gecerli (fixture'lar degismemis)"
      if not hata else "BASARISIZ: " + "; ".join(hata))
sys.exit(1 if hata else 0)
