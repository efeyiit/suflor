"""Sonda r2-05: zincir kurali degismezleri -- rastgele sozluk x metin, BAGIMSIZ sinir tanimi (kural 8), sayaclarla.

Degismezler (docstring K1 v3): (1) hit'ler sirali/ortusmesiz, dilim = terim; (2) her bitisik kosunun dis uclari gercek
sinir; (3) iki ucu gercek sinirli ve kabul edilenle ortusmeyen aday atlanmaz; (4) kabul edilmis komsu ucu da sinirdir;
(5) JSON sirasi sonucu degistirmez. Pozitif kontrol (kural 10): kac metinde 2+ uyeli zincir kabul edildi, kac aday
zincir/ortusme yuzunden reddedildi, kac metinde hic hit yokken aday vardi (zincir olu).
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from yardimci import KOK, sozluk  # noqa: E402

OUT = KOK / ".agents/tasks/T-011/tester_A_evidence/r2-sonda-05-zincir-fuzz.txt"
satirlar: list[str] = []


def yaz(s: str) -> None:
    satirlar.append(s)
    print(s.encode("ascii", "backslashreplace").decode("ascii"))


HARF = "abc村人あい"
SINIF = {"a": 0, "b": 0, "c": 0, "村": 1, "人": 1, "あ": 2, "い": 2, "を": 9, " ": 9, ".": 9}
AYIRAC = {"を", " ", "."}
ALFABE = HARF + "を ."


def sol(t, p):
    return p == 0 or t[p - 1] in AYIRAC or SINIF[t[p - 1]] != SINIF[t[p]]


def sag(t, e):
    return e == len(t) or t[e] in AYIRAC or SINIF[t[e - 1]] != SINIF[t[e]]


def adaylar(t, terimler):
    out = []
    for term in terimler:
        i = t.find(term)
        while i != -1:
            out.append((i, i + len(term), term))
            i = t.find(term, i + 1)
    return out


def kontrol(t, terimler, hits):
    hs = [(h.start, h.end) for h in hits]
    assert hs == sorted(hs), ("sira", hs)
    for (s, e), h in zip(hs, hits):
        assert t[s:e] in terimler and h.source_term == t[s:e], ("dilim", s, e)
    for (s1, e1), (s2, e2) in zip(hs, hs[1:]):
        assert e1 <= s2, ("ortusme", hs)
    uzun = 0
    i = 0
    while i < len(hs):
        j = i
        while j + 1 < len(hs) and hs[j][1] == hs[j + 1][0]:
            j += 1
        assert sol(t, hs[i][0]) and sag(t, hs[j][1]), ("kosu dis uc", hs[i][0], hs[j][1], hs)
        uzun += j > i
        i = j + 1
    dolu = [False] * len(t)
    for s, e in hs:
        for k in range(s, e):
            dolu[k] = True
    kabul_bas = {s for s, _ in hs}
    kabul_bit = {e for _, e in hs}
    red = 0
    ad = adaylar(t, terimler)
    for s, e, term in ad:
        if any(dolu[s:e]):
            red += (s, e) not in hs
            continue
        red += 1
        assert not (sol(t, s) and sag(t, e)), ("atlanan gercek-sinirli aday", s, e, term, hs)
        assert not ((sol(t, s) or s in kabul_bit) and (sag(t, e) or e in kabul_bas)), ("atlanan komsu-sinirli aday", s, e, term, hs)
    return uzun, red, bool(ad) and not hs


toplam = uzun_t = red_t = olu_t = 0
ihlal = 0
for tohum in (1, 2, 3, 4, 5):
    rnd = random.Random(tohum)
    for _ in range(400):
        terimler = set()
        while len(terimler) < rnd.randint(2, 7):
            terimler.add("".join(rnd.choice(HARF) for _ in range(rnd.choice([1, 2, 2, 3, 3]))))
        terimler = sorted(terimler)
        kayitlar = [{"kaynak": x, "hedef": "T" + str(i), "kisa_terim_izni": True} for i, x in enumerate(terimler)]
        st, st2 = sozluk(*kayitlar), sozluk(*reversed(kayitlar))
        for _ in range(20):
            t = "".join(rnd.choice(ALFABE) for _ in range(rnd.randint(1, 14)))
            h1, h2 = st.lookup(t), st2.lookup(t)
            toplam += 1
            if [(x.start, x.end) for x in h1] != [(x.start, x.end) for x in h2]:
                ihlal += 1
                yaz(f"IHLAL json sirasi: {t!r} {terimler}")
                continue
            try:
                uzun, red, olu = kontrol(t, terimler, h1)
            except AssertionError as e:
                ihlal += 1
                yaz(f"IHLAL {e.args[0]!r} metin={t!r} terimler={terimler}")
                continue
            uzun_t += uzun
            red_t += red
            olu_t += olu
yaz(f"metin: {toplam} (5 tohum x 400 sozluk x 20), ihlal: {ihlal}")
yaz(f"pozitif kontrol: 2+ uyeli kabul edilen zincir kosusu {uzun_t}; zincir/ortusme yuzunden reddedilen aday {red_t}; aday var ama 0 hit (olu zincir) metin {olu_t}")

# yer tutuculu varyant
fark = kor = toplam2 = ihlal2 = 0
rnd = random.Random(7)
for _ in range(300):
    terimler = sorted({"".join(rnd.choice(HARF) for _ in range(rnd.choice([1, 2, 3]))) for _ in range(rnd.randint(2, 6))})
    st = sozluk(*[{"kaynak": x, "hedef": "T", "kisa_terim_izni": True} for x in terimler])
    for _ in range(15):
        p = ["".join(rnd.choice(ALFABE) for _ in range(rnd.randint(0, 5))) for _ in range(3)]
        t = p[0] + "xx" + p[1] + ("xx" if rnd.random() < 0.5 else "") + p[2]
        h = st.lookup(t, ("xx",))
        toplam2 += 1
        # korunan araliklar (ortusmesiz tarama), hic hit ortusmez; uclari sinir
        kor_ar = []
        i = t.find("xx")
        while i != -1:
            kor_ar.append((i, i + 2))
            i = t.find("xx", i + 2)
        kor += bool(kor_ar)
        for x in h:
            for a, b in kor_ar:
                if not (x.end <= a or b <= x.start):
                    ihlal2 += 1
                    yaz(f"IHLAL yt ortusmesi: {t!r} {(x.start, x.end)}")
        fark += [(x.start, x.end) for x in h] != [(x.start, x.end) for x in st.lookup(t)]
yaz(f"yer tutuculu metin: {toplam2}, korunan aralikli: {kor}, ihlal: {ihlal2}; yt bildirilince sonucu degisen metin (pozitif): {fark}")
OUT.write_text("\n".join(satirlar) + "\n", encoding="utf-8")
print(f"yazildi -> {OUT.name}")
