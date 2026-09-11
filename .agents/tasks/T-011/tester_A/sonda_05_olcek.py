"""Sonda 5: hit sayisinda olcekleme (karesel mi), real_check #7 yolu modelsiz, Latin bilesik (windmill) kontrolu."""
from __future__ import annotations

import dataclasses
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from yardimci import KOK, hit_ozet, seg, sozluk, u  # noqa: E402
from src.contracts.models import Rect, Segment  # noqa: E402
from src.translate.sozluk import GlossaryStore, terimleri_gom  # noqa: E402

OUT = KOK / ".agents/tasks/T-011/tester_A_evidence/sonda-05-olcek.txt"
satirlar: list[str] = []


def yaz(*a: object) -> None:
    s = " ".join(str(x) for x in a)
    satirlar.append(s)
    print(s.encode("ascii", "backslashreplace").decode("ascii"))


yaz("== 1. tek segment, yogun hit: uzunluk 2x -> sure kac x? ==")
st = sozluk(("マルクス", "Marcus"), ("長老", "İhtiyar"))
birim = "長老マルクス "  # 7 kodpoint, 2 hit
onceki = None
for k in [250, 500, 1000, 2000, 4000]:
    metin = birim * k
    t = []
    for _ in range(3):
        t0 = time.perf_counter(); h = st.lookup(metin); t.append((time.perf_counter() - t0) * 1000)
    m = statistics.median(t)
    oran = f"{m/onceki:.2f}x" if onceki else "-"
    yaz(f"  len={len(metin):6d} hit={len(h):5d} medyan {m:8.1f} ms  (onceki x2 uzunluga oran: {oran})")
    onceki = m

yaz("== 1b. ayni hit yogunlugu, seyrek metin (hit sayisi sabit, uzunluk artar) ==")
onceki = None
for dolgu in [10, 40, 160]:
    metin = ("長老マルクス " + "あ" * dolgu) * 500
    t = []
    for _ in range(3):
        t0 = time.perf_counter(); h = st.lookup(metin); t.append((time.perf_counter() - t0) * 1000)
    m = statistics.median(t)
    yaz(f"  len={len(metin):6d} hit={len(h):5d} medyan {m:8.1f} ms")

yaz("== 2. real_check #7 yolu MODELSIZ (ayni cumle, ayni fixture) ==")
s = GlossaryStore(KOK / ".agents/tasks/T-011/fixtures/sozluk_ornek.json")
segs = tuple(Segment(text="長老マルクスが水車小屋で待っています。", bbox=Rect(0, i, 1, 1)) for i in range(1000))
for tur in range(3):
    t = []
    for _ in range(5):
        t0 = time.perf_counter()
        hits = tuple(dataclasses.replace(h, segment_index=i) for i, sg in enumerate(segs) for h in s.lookup(sg.text, sg.placeholders))
        terimleri_gom(segs, hits); t.append((time.perf_counter() - t0) * 1000)
    yaz(f"  tur {tur}: kapi yolu medyan {statistics.median(t):.1f} ms (min {min(t):.1f}, max {max(t):.1f}); hit={len(hits)}")
t = []
for _ in range(5):
    t0 = time.perf_counter()
    hits = s.lookup_segments(segs)
    terimleri_gom(segs, hits); t.append((time.perf_counter() - t0) * 1000)
yaz(f"  lookup_segments yolu medyan {statistics.median(t):.1f} ms")

yaz("== 3. Latin bilesik: docstring 'windmill eslesmez' -- 'wind' de sozlukteyken ==")
l1 = sozluk(("mill", "Değirmen"))
l2 = sozluk(("mill", "Değirmen"), ("wind", "Rüzgar"))
for metin in ["windmill", "the windmill.", "Windmill", "windmills", "wind mill"]:
    yaz(f"  {metin!r:18s} yalniz mill: {hit_ozet(l1.lookup(metin))}  |  mill+wind: {hit_ozet(l2.lookup(metin))}")
# gomulu hali
h = tuple(dataclasses.replace(x, segment_index=0) for x in l2.lookup("The windmill is old."))
yaz(f"  gom: {u(terimleri_gom((seg('The windmill is old.'),), h)[0].text)!r}")
# KR/JP esdegeri (bu kural oradan geliyor): 방앗간 + 집(ev) sozlukte -> 방앗간집 iki hit
k2 = sozluk(("방앗간", "Değirmen"), ("집주인", "EvSahibi"))
yaz(f"  KR 방앗간집주인 (mill house-owner): {hit_ozet(k2.lookup('방앗간집주인'))}")
k1 = sozluk(("방앗간", "Değirmen"))
yaz(f"  KR 방앗간집주인 yalniz 방앗간: {hit_ozet(k1.lookup('방앗간집주인'))} (G5 negatifi korunuyor)")
# Latin: elder + s? 's' tek kodpoint reddedilir; 'ly' / 'er' gibi 2-harfli ekler
l3 = sozluk(("elder", "İhtiyar"), ("ly", "Ly"))
yaz(f"  'elderly' elder+ly sozlukte: {hit_ozet(l3.lookup('elderly'))}")
l4 = sozluk(("Marcus", "Marcus"), ("es", "Es"))
yaz(f"  'Marcuses' Marcus+es: {hit_ozet(l4.lookup('Marcuses'))}")

yaz("== 4. IGNORECASE denklik taramasi (bagimsiz): re.I esleyen her (c, d) ciftinde _anahtar ayni mi ==")
import re
from src.translate.sozluk import _anahtar
import unicodedata
farkli: list[tuple[str, str]] = []
kontrol = 0
cift_sayisi = 0
for cp in range(0x110000):
    c = chr(cp)
    if unicodedata.category(c).startswith(("Cs", "Cn", "Co")):
        continue
    adaylar = {c.lower(), c.upper(), c.casefold(), c.swapcase(), c.title()}
    # Python sre'nin ozel denklik tablosu (re._compiler._equivalences) uzerinden ek adaylar
    adaylar.discard(c)
    adaylar = {d for d in adaylar if len(d) == 1}
    if not adaylar:
        continue
    desen = re.compile(re.escape(c), re.IGNORECASE)
    for d in adaylar:
        if desen.fullmatch(d):
            cift_sayisi += 1
            if _anahtar(c) != _anahtar(d):
                farkli.append((c, d))
        else:
            kontrol += 1
# sre ozel tablo
try:
    from re._compiler import _equivalences  # type: ignore[attr-defined]
    for grup in _equivalences:
        for a in grup:
            for b in grup:
                if a != b:
                    ca, cb = chr(a), chr(b)
                    if re.fullmatch(re.escape(ca), cb, re.IGNORECASE):
                        cift_sayisi += 1
                        if _anahtar(ca) != _anahtar(cb):
                            farkli.append((ca, cb))
    yaz(f"  sre ozel denklik gruplari: {len(_equivalences)}")
except Exception as e:  # noqa: BLE001
    yaz(f"  sre tablo okunamadi: {type(e).__name__}")
yaz(f"  re.I ile eslesen (c,d) cifti: {cift_sayisi}; _anahtar farkli olan: {len(farkli)}; case-varyanti olup re.I eslesmeyen (pozitif kontrol): {kontrol}")
for c, d in farkli[:30]:
    yaz(f"    U+{ord(c):04X} vs U+{ord(d):04X}: anahtar {u(_anahtar(c))!r} vs {u(_anahtar(d))!r}")

yaz("== 4b. ters yon: _anahtar AYNI ama re.I eslesmeyen ciftler (tekrar reddi > eslesme; ss/eszett gibi) ==")
from collections import defaultdict
gruplar: dict[str, list[str]] = defaultdict(list)
for cp in range(0x110000):
    c = chr(cp)
    if unicodedata.category(c).startswith(("Cs", "Cn", "Co")):
        continue
    k = _anahtar(c)
    gruplar[k].append(c)
ters = 0
ornek = []
for k, uyeler in gruplar.items():
    if len(uyeler) < 2:
        continue
    for i in range(len(uyeler)):
        for j in range(i + 1, len(uyeler)):
            if not re.fullmatch(re.escape(uyeler[i]), uyeler[j], re.IGNORECASE):
                ters += 1
                if len(ornek) < 25:
                    ornek.append((uyeler[i], uyeler[j], k))
yaz(f"  _anahtar ayni ama re.I eslesmeyen tek-kodpoint cifti: {ters}")
for a, b, k in ornek:
    yaz(f"    U+{ord(a):04X} ~ U+{ord(b):04X} (anahtar {u(k)!r})")

OUT.write_text("\n".join(satirlar) + "\n", encoding="utf-8")
print(f"yazildi -> {OUT.name}")
