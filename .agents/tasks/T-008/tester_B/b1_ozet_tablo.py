"""B1 -- mutant kiti ozet tablosu (jsonl kaydindan): mutant x kapi; G2'de dusen test sayisi
(`test_k1_sabitler_paketteki_degerlerde` HARIC de sayilir -- sabit-pin testi tek basina
davranis olcusu degildir); kapi basina yakalama sayisi; kacan/kontrol ozeti.
Kosum: python .agents/tasks/T-008/tester_B/b1_ozet_tablo.py <jsonl>
"""
from __future__ import annotations
import json, sys
from collections import Counter
from pathlib import Path
kayit = [json.loads(l) for l in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines() if l.strip()]
# ayni mid birden fazla kez kosulduysa (M21 ilk kosumda cikti cokmesi) SON kayit gecerli
son: dict[str, dict] = {}
for k in kayit:
    son[k["mid"]] = k
kayit = list(son.values())
kapilar = ["G1-mypy", "G2-birim", "G3-real", "G4-kapsam", "G5-tum"]
print(f"{'mid':5s} {'G1G2G3G4G5':11s} {'G2 dusen':>8s} {'sabit haric':>11s} {'sonuc':22s} sinif / aciklama")
kacan, kontrol_yakalanan, davranis, kontrol = [], [], 0, 0
kapi_sayac: Counter[str] = Counter()
for k in kayit:
    d = k["durum"]
    dusen = k["dusenler"].get("G2-birim", [])
    haric = [t for t in dusen if "test_k1_sabitler_paketteki_degerlerde" not in t]
    if k["kontrol"]:
        kontrol += 1
        sonuc = "kontrol KACTI" if "X" not in d else "KONTROL YAKALANDI!"
        if "X" in d: kontrol_yakalanan.append(k["mid"])
    else:
        davranis += 1
        sonuc = "YAKALANDI" if "X" in d else "*** KACTI ***"
        if "X" not in d: kacan.append(k["mid"])
        for i, c in enumerate(d):
            if c == "X": kapi_sayac[kapilar[i]] += 1
    print(f"{k['mid']:5s} [{d}]     {len(dusen):8d} {len(haric):11d} {sonuc:22s} {k['sinif']} -- {k['aciklama'][:90]}")
print()
print(f"davranis mutanti {davranis}: yakalanan {davranis - len(kacan)}, kacan {len(kacan)} {kacan}")
print(f"kontrol {kontrol}: kacan {kontrol - len(kontrol_yakalanan)}, yakalanan (yanlis pozitif) {kontrol_yakalanan}")
print("kapi basina yakalama: " + ", ".join(f"{g} {kapi_sayac[g]}/{davranis}" for g in kapilar))
yalniz_g3 = [k["mid"] for k in kayit if not k["kontrol"] and k["durum"] == "..X.."]
yalniz_sabit = [k["mid"] for k in kayit if not k["kontrol"] and k["durum"] != "....." and
                k["dusenler"].get("G2-birim") and all("test_k1_sabitler" in t for t in k["dusenler"]["G2-birim"])]
print(f"yalniz real_check ile yakalanan: {yalniz_g3}; G2'de YALNIZ sabit-pin testiyle yakalanan: {yalniz_sabit}")
