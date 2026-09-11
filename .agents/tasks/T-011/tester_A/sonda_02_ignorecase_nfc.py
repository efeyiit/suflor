"""Sonda 2: IGNORECASE + kanonik anahtar sinirlari; NFC girdi/cikti; kodpoint indeksleri."""
from __future__ import annotations

import dataclasses
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from yardimci import KOK, hit_ozet, seg, sozluk, u  # noqa: E402
from src.contracts.errors import ContractViolation  # noqa: E402
from src.translate.sozluk import terimleri_gom  # noqa: E402

OUT = KOK / ".agents/tasks/T-011/tester_A_evidence/sonda-02-ignorecase-nfc.txt"
satirlar: list[str] = []


def yaz(*a: object) -> None:
    satirlar.append(" ".join(str(x) for x in a))


def dene(store, metin: str, yt=(), etiket: str = "") -> list:
    try:
        h = store.lookup(metin, yt)
    except Exception as e:  # noqa: BLE001
        yaz(f"{etiket:44s} metin={u(metin)!s:40s} -> HATA {type(e).__name__}: {u(str(e))}")
        return []
    yaz(f"{etiket:44s} metin={u(metin)!s:40s} -> {hit_ozet(h)}")
    return h


yaz("== 1. IGNORECASE: Latin/Turkce/ozel katlamalar ==")
m = sozluk(("Marcus", "Marcus"), ("İstanbul", "İstanbul"), ("straße", "Sokak"), ("fine", "Ince"), ("ΣΟΦΙΑ", "Sofya"), ("Кремль", "Kremlin"))
dene(m, "MARCUS", etiket="tam buyuk")
dene(m, "marcus", etiket="tam kucuk")
dene(m, "mArCuS", etiket="karisik")
dene(m, "Marcuſ", etiket="uzun s (U+017F) -- IGNORECASE s~long-s")
dene(m, "MARCUS bekliyor", etiket="MARCUS + bosluk")
dene(m, "istanbul", etiket="istanbul (kucuk i)")
dene(m, "ISTANBUL", etiket="ISTANBUL (buyuk I)")
dene(m, "ıstanbul", etiket="noktasiz i ile")
dene(m, "İSTANBUL", etiket="buyuk noktali I ile")
dene(m, "STRASSE", etiket="STRASSE vs strasse-eszett -- casefold ss")
dene(m, "STRAßE", etiket="STRA + buyuk eszett? (U+00DF kucuk)")
dene(m, "strasse", etiket="strasse")
dene(m, "Straße", etiket="Strasse eszett")
dene(m, "STRAẞE", etiket="buyuk eszett U+1E9E")
dene(m, "ﬁne", etiket="fi ligature (U+FB01) vs fine")
dene(m, "FINE", etiket="FINE")
dene(m, "σοφια", etiket="sigma kucuk")
dene(m, "σοφιας", etiket="final sigma sonek -> harf komsusu")
dene(m, "Σοφια", etiket="Sigma bas buyuk")
dene(m, "кремль", etiket="Kiril kucuk")
dene(m, "КРЕМЛЬ", etiket="Kiril buyuk")

yaz("== 1b. sozlukte kucuk, metinde ozel buyuk ==")
m2 = sozluk(("kelvin", "Kelvin"), ("fiş", "Fis"), ("dış", "Dis"))
dene(m2, "Kelvin", etiket="U+212A Kelvin isareti + elvin")
dene(m2, "KELVIN", etiket="KELVIN")
dene(m2, "ﬁş", etiket="fi ligature + s-cedilla (uzunluk 2 vs 3)")
dene(m2, "FİŞ", etiket="FIS noktali buyuk I")
dene(m2, "FIŞ", etiket="FIS noktasiz buyuk I")
dene(m2, "DIŞ", etiket="DIS")
dene(m2, "diş", etiket="dis (noktali i) -- dis-noktasiz ile ayni anahtar mi?")

yaz("== 1c. tekrar reddi: IGNORECASE denk ciftler ==")
for a, b in [("Marcus", "MARCUS"), ("istanbul", "İstanbul"), ("dış", "diş"), ("straße", "strasse"), ("fine", "ﬁne"), ("K", "K"), ("s", "ſ")]:
    try:
        st = sozluk({"kaynak": a, "hedef": "X", "kisa_terim_izni": True}, {"kaynak": b, "hedef": "Y", "kisa_terim_izni": True})
        yaz(f"  {u(a)!s:12s} + {u(b)!s:12s} -> KABUL ({len(st)} terim)")
    except ValueError as e:
        yaz(f"  {u(a)!s:12s} + {u(b)!s:12s} -> ValueError: {u(str(e))[:90]}")

yaz("== 1d. tekrar reddi ATLANMIS ciftte lookup davranisi (iki terim ayni IGNORECASE sinifinda) ==")
for a, b, metin in [("straße", "strasse", "STRASSE"), ("fine", "ﬁne", "FINE"), ("K", "K", "K"), ("s", "ſ", "S")]:
    try:
        st = sozluk({"kaynak": a, "hedef": "Xa", "kisa_terim_izni": True}, {"kaynak": b, "hedef": "Yb", "kisa_terim_izni": True})
    except ValueError as e:
        yaz(f"  {u(a)} + {u(b)}: yuklenemedi: {u(str(e))[:60]}")
        continue
    dene(st, metin, etiket=f"  {u(a)}+{u(b)} sozluk, metin")
    dene(st, a, etiket=f"  ... metin = {u(a)}")
    dene(st, b, etiket=f"  ... metin = {u(b)}")

yaz("== 2. NFC: NFD metin, indeksler, gom ciktisi ==")
n = sozluk(("Değirmen", "Değirmen"), ("방앗간", "Değirmen"), ("café", "Kahve"))
nfd_tr = unicodedata.normalize("NFD", "Değirmen")
nfd_kr = unicodedata.normalize("NFD", "방앗간을 지나")
nfd_cafe = unicodedata.normalize("NFD", "le café noir")
yaz(f"  NFD uzunluklar: Degirmen {len(nfd_tr)} (NFC 8), KR {len(nfd_kr)} (NFC {len(unicodedata.normalize('NFC', nfd_kr))}), cafe {len(nfd_cafe)} (NFC 12)")
h1 = dene(n, nfd_tr + " eski", etiket="NFD Degirmen + ' eski'")
h2 = dene(n, nfd_kr, etiket="NFD KR")
h3 = dene(n, nfd_cafe, etiket="NFD cafe")
if h3:
    h = h3[0]
    yaz(f"  cafe: NFD metin[{h.start}:{h.end}] = {u(nfd_cafe[h.start:h.end])!r}; NFC metin dilimi = {u(unicodedata.normalize('NFC', nfd_cafe)[h.start:h.end])!r}")

yaz("== 2b. terimleri_gom'a NFD segment ==")
s_nfd = seg(nfd_cafe)
hits = tuple(dataclasses.replace(h, segment_index=0) for h in n.lookup(s_nfd.text))
try:
    out = terimleri_gom((s_nfd,), hits)
    yaz(f"  gom OK; girdi len={len(s_nfd.text)}; cikti text = {u(out[0].text)!r}; cikti NFC?={out[0].text == unicodedata.normalize('NFC', out[0].text)}")
except ContractViolation as e:
    yaz(f"  gom ContractViolation: {u(str(e))}")

n2 = sozluk(("noir", "Kara"))
metin_nfd = unicodedata.normalize("NFD", "café noir été")
s2 = seg(metin_nfd)
hits2 = tuple(dataclasses.replace(h, segment_index=0) for h in n2.lookup(s2.text))
out2 = terimleri_gom((s2,), hits2)
yaz(f"  NFD girdi (len {len(metin_nfd)}) -> cikti (len {len(out2[0].text)}); ARALIK DISI 'cafe' ve 'ete' degisti mi? girdi[:5]={u(metin_nfd[:5])!r} cikti[:5]={u(out2[0].text[:5])!r}")
yaz(f"  aralik disi karakterler aynen mi: girdi[:5]==cikti[:5] -> {metin_nfd[:5] == out2[0].text[:5]}")
yaz(f"  hit yok + NFD segment -> ayni nesne mi: {terimleri_gom((s2,), ())[0] is s2}")
s3 = seg("noir")
out3 = terimleri_gom((s2, s3), (dataclasses.replace(n2.lookup('noir')[0], segment_index=1),))
yaz(f"  hit'siz NFD segment baska segment hit'liyken: ayni nesne={out3[0] is s2}, text NFD kaldi={out3[0].text == metin_nfd}")

yaz("== 2c. hit NFD source_term / target_term, segment NFC ==")
s4 = seg("le café noir")
h4 = n.lookup(s4.text)[0]
h4_nfd = dataclasses.replace(h4, source_term=unicodedata.normalize("NFD", h4.source_term), segment_index=0)
try:
    o = terimleri_gom((s4,), (h4_nfd,))
    yaz(f"  NFD source_term kabul: {u(o[0].text)!r}")
except ContractViolation as e:
    yaz(f"  ContractViolation: {u(str(e))}")
h5 = dataclasses.replace(h4, target_term=unicodedata.normalize("NFD", "Kahvé"), segment_index=0)
o5 = terimleri_gom((s4,), (h5,))
yaz(f"  NFD target_term -> cikti NFC? {o5[0].text == unicodedata.normalize('NFC', o5[0].text)}, text={u(o5[0].text)!r}")

yaz("== 3. kodpoint indeksleri: astral + birlestirici ==")
k = sozluk(("マルクス", "Marcus"), ("Marcus", "Marcus"), ("か゚き", "Kaki"))
t1 = "\U0001F600マルクス"
h = dene(k, t1, etiket="emoji (astral) once")
if h:
    yaz(f"  metin[{h[0].start}:{h[0].end}] = {u(t1[h[0].start:h[0].end])!r} (kodpoint dogru mu)")
dene(k, "\U0002000B マルクス", etiket="CJK Ext-B astral + bosluk once")
dene(k, "\U0002000Bマルクス", etiket="CJK Ext-B astral BITISIK (harf komsusu -> hayir)")
dene(k, "Marcuś", etiket="Marcus + birlestirici aksan (Mn) sagda")
dene(k, "́Marcus", etiket="birlestirici aksan solda")
dene(k, "Marcus‍", etiket="Marcus + ZWJ (Cf)")
dene(k, "か゚きが", etiket="ka+handakuten(U+309A) ki terim + ga")
dene(k, "かき゚が", etiket="kontrol: farkli yerde handakuten -> hayir")
dene(k, "マルクズ", etiket="marukusu + birlestirici dakuten (Mn) -> ?")
dene(k, "マルクズ", etiket="kontrol: marukuzu (NFC bilesik) -> hayir")

yaz("== 4. lookup sonucu gom'a: source_term buyuk/kucuk metinden mi ==")
h = k.lookup("MARCUS bekliyor")
yaz(f"  source_term={h[0].source_term!r} target={h[0].target_term!r} start={h[0].start} end={h[0].end}")
o = terimleri_gom((seg("MARCUS bekliyor"),), (dataclasses.replace(h[0], segment_index=0),))
yaz(f"  gom -> {o[0].text!r}")

OUT.write_text("\n".join(satirlar) + "\n", encoding="utf-8")
print(f"yazildi: {len(satirlar)} satir -> {OUT.name}")
