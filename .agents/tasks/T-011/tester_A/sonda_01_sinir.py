"""Sonda 1: sinir kurali simetrisi + ortusme/determinizm kesfi. Ham cikti dosyaya (UTF-8)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from yardimci import KOK, hit_ozet, sozluk, u  # noqa: E402

OUT = KOK / ".agents/tasks/T-011/tester_A_evidence/sonda-01-sinir.txt"
satirlar: list[str] = []


def yaz(*a: object) -> None:
    satirlar.append(" ".join(str(x) for x in a))


def dene(store, metin: str, yt=(), etiket: str = "") -> list:
    h = store.lookup(metin, yt)
    yaz(f"{etiket:40s} metin={u(metin)!s:45s} yt={u(str(yt))} -> {hit_ozet(h)}")
    return h


# --- 1. KR ek: yalniz SAG. Terim metnin basinda/sonunda + ek ---
s = sozluk(("방앗간", "Değirmen"), ("마르쿠스", "Marcus"))
yaz("== 1. KR ek simetrisi ==")
dene(s, "방앗간을", etiket="basta terim + ek (metin sonu)")
dene(s, "을방앗간", etiket="ek SOLDA (sinir olmamali)")
dene(s, "지나 방앗간", etiket="sonda terim, bosluk solda")
dene(s, "방앗간에서는", etiket="ek zinciri 2 (에서+는)")
dene(s, "방앗간에서는을", etiket="ek zinciri 3 (에서+는+을) -> hayir?")
dene(s, "방앗간으로", etiket="으로 (uzun ek)")
dene(s, "방앗간로", etiket="로 (kisa ek)")
dene(s, "방앗간으", etiket="으 tek (ek degil) -> hayir")
dene(s, "방앗간을.", etiket="ek + noktalama")
dene(s, "방앗간을마르쿠스", etiket="ek + baska terim (terim basi sinir)")
dene(s, "방앗간마르쿠스", etiket="bitisik iki terim (KR)")
dene(s, "방앗간도둑", etiket="도+둑 -> hayir")
dene(s, "방앗간도 둑", etiket="도 + bosluk -> evet")
dene(s, "방앗간이가", etiket="이+가 zincir 2 -> evet")
dene(s, "방앗간이가을", etiket="zincir 3 -> hayir")
dene(s, "방앗간에서에서", etiket="에서+에서 zincir 2")
dene(s, "방앗간에서에서에서", etiket="에서x3 -> hayir")

# --- 2. JP parcacik iki taraf ---
j = sozluk(("マルクス", "Marcus"), ("長老", "İhtiyar"), ("水車小屋", "Değirmen"))
yaz("== 2. JP parcacik ==")
dene(j, "がマルクス", etiket="parcacik solda")
dene(j, "マルクスが", etiket="parcacik sagda")
dene(j, "長老マルクス", etiket="iki terim bitisik")
dene(j, "マルクス長老", etiket="ters sira bitisik")
dene(j, "長老マルクス水車小屋", etiket="uc terim bitisik")
dene(j, "マルクスマルクス", etiket="ayni terim iki kez bitisik")
dene(j, "マルクスマルクスマルクス", etiket="ayni terim uc kez bitisik")
dene(j, "長老長老", etiket="長老 x2 bitisik")
dene(j, "村マルクス", etiket="kanji komsu solda -> hayir")
dene(j, "マルクス村", etiket="kanji komsu sagda -> hayir")
dene(j, "マルクスの村", etiket="の parcacik ortada")
dene(j, "マルクス　長老", etiket="ideografik bosluk")

# --- 3. Kismi ortusme, determinizm, JSON sirasi ---
yaz("== 3. ortusme / determinizm ==")
a = sozluk(("水車", "SuArabasi"), ("車小屋", "ArabaKulube"))
b = sozluk(("車小屋", "ArabaKulube"), ("水車", "SuArabasi"))
dene(a, "水車小屋", etiket="A: 水車,車小屋 sirasi")
dene(b, "水車小屋", etiket="B: 車小屋,水車 sirasi")
dene(a, "水車小屋を", etiket="A + parcacik")
dene(b, "水車小屋を", etiket="B + parcacik")
# esit uzunluk, farkli konumda ortusme
c = sozluk(("水車", "SuArabasi"), ("車小", "ArabaKucuk"))
d = sozluk(("車小", "ArabaKucuk"), ("水車", "SuArabasi"))
dene(c, "水車小", etiket="C: esit uzunluk ortusme (水車 once)")
dene(d, "水車小", etiket="D: esit uzunluk ortusme (車小 once)")
dene(c, "水車小屋", etiket="C: 水車小屋 icinde")
dene(d, "水車小屋", etiket="D: 水車小屋 icinde")
# kisa terim uzun terimin icinde baslayip disinda bitiyor
e = sozluk(("ABCD", "Uzun"), ("CDEF", "Kisa"))
dene(e, "ABCDEF", etiket="ABCD + CDEF kismi ortusme")
dene(e, "abcdef", etiket="kucuk harf")
dene(e, "ABCDEF CDEF", etiket="ikinci gecis bagimsiz")
# uc terim: en uzun ortadaki iki kisayi keser mi
f = sozluk(("AB", "x"), ("BCD", "y"), ("DE", "z"))
dene(f, "ABCDE", etiket="AB|BCD|DE: BCD (3) once, AB ve DE ortusur")
dene(f, "AB BCD DE", etiket="ayri ayri pozitif kontrol")

# --- 4. Sozlukteki baska terimin basi/sonu sinir: kabul edilmeyen komsu ---
yaz("== 4. komsu terim sinir ==")
g = sozluk(("マルクス", "Marcus"), ("長老", "İhtiyar"))
dene(g, "長老マルクス村", etiket="長老 sagi マルクス basi; マルクス sagi 村 -> マルクス reddedilir; 長老?")
dene(g, "村長老マルクス", etiket="長老 solu 村 -> ret; マルクス solu 長老 biti (kabul edilmemis!)")
dene(g, "村長老マルクス村", etiket="ikisi de komsu-terim sinirli ama ikisi de dis sinirsiz")

# --- 5. Latin kaynakta sinir ---
yaz("== 5. Latin ==")
l = sozluk(("mill", "Değirmen"), ("elder", "İhtiyar"), ("Marcus", "Marcus"))
dene(l, "windmill", etiket="windmill -> hayir")
dene(l, "mill-house", etiket="tire noktalama -> evet")
dene(l, "Mill's", etiket="kesme")
dene(l, "mill2", etiket="rakam -> hayir")
dene(l, "mill_house", etiket="alt cizgi (Pc noktalama!) -> evet?")
dene(l, "mill$", etiket="sembol S* -> ?")
dene(l, "mill+elder", etiket="+ (Sm) -> ?")
dene(l, "mill€", etiket="para (Sc) -> ?")
dene(l, "millelder", etiket="bitisik iki Latin terim -> ikisi de? (komsu terim kurali)")
dene(l, "Marcusmill", etiket="bitisik Latin: Marcus+mill")
dene(l, "Marcusが", etiket="Latin + JP parcacik")
dene(l, "Marcus가", etiket="Latin + KR ek")
dene(l, "Marcus은", etiket="Latin + KR ek 은")
dene(l, "Marcus­mill", etiket="soft hyphen (Cf) arada -> ?")
dene(l, "Marcus​mill", etiket="ZWSP (Cf) arada")
dene(l, "Marcus　mill", etiket="ideografik bosluk")
dene(l, "Marcus mill", etiket="NBSP")
dene(l, "⁠Marcus", etiket="WJ (Cf) once")

OUT.write_text("\n".join(satirlar) + "\n", encoding="utf-8")
print(f"yazildi: {len(satirlar)} satir -> {OUT.name}")
