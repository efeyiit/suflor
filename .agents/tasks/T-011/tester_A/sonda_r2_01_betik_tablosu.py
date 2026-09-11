"""Sonda r2-01: betik sinifi tablosu -- KAMU API ile olculur (ayni betikli terim + karakter -> hit yok), docstring ile karsilastirilir.

Her karakter icin: bes betikli terimin (Katakana マルクス, Han 長老, Hiragana ひかり, Hangul 마르쿠스, DIGER Marcus) sagina ve
soluna konur; hit VERMEYEN terim(ler)in sinifi karakterin sinifidir. Noktalama/bosluk/birlestirici isaretler ayri
(gercek sinir ya da M* kurali). Ham cikti UTF-8 dosyaya; konsol ASCII.
"""
from __future__ import annotations

import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from yardimci import KOK, sozluk, u  # noqa: E402

OUT = KOK / ".agents/tasks/T-011/tester_A_evidence/r2-sonda-01-betik-tablosu.txt"
satirlar: list[str] = []


def yaz(s: str) -> None:
    satirlar.append(s)
    print(u(s))


TERIMLER = {"Katakana": "マルクス", "Han": "長老", "Hiragana": "ひかり", "Hangul": "마르쿠스", "DIGER": "Marcus"}
st = sozluk(*[(t, "T" + s) for s, t in TERIMLER.items()])

# (karakter, docstring'e gore beklenen sinif ya da 'SINIR' (noktalama/bosluk) ya da 'M*')
TABLO = [
    ("ー", "Katakana"), ("ｰ", "Katakana"), ("ﾏ", "Katakana"), ("ｽ", "Katakana"), ("ㇰ", "Katakana"), ("ヶ", "Katakana"), ("ヽ", "Katakana"), ("ヾ", "Katakana"),
    ("・", "SINIR"),  # Katakana blogunda ama Po -> gercek sinir
    ("々", "Han"), ("〆", "Han"), ("〇", "Han"), ("三", "Han"), ("漢", "Han"), ("⼀", "Han"), ("⺀", "Han"), ("㐀", "Han"), ("豈", "Han"), ("\U00020000", "Han"), ("\U0002F800", "Han"),
    ("あ", "Hiragana"), ("ゝ", "Hiragana"), ("ゞ", "Hiragana"), ("ぁ", "Hiragana"), ("ゟ", "Hiragana"),
    ("゛", "Hiragana"), ("゜", "Hiragana"),  # ayrik ses isaretleri (Sk) Hiragana blogunda
    ("゙", "M*"), ("゚", "M*"),      # birlestirici ses isaretleri: sagda sinir degil (M*), solda Hiragana sinifi
    ("ᄀ", "Hangul"), ("ᅡ", "Hangul"), ("ᆨ", "Hangul"), ("ㄱ", "Hangul"), ("ﾡ", "Hangul"), ("나", "Hangul"), ("힣", "Hangul"), ("ꥠ", "Hangul"), ("ힰ", "Hangul"),
    ("Ｍ", "DIGER"), ("ａ", "DIGER"), ("2", "DIGER"), ("２", "DIGER"), ("①", "DIGER"), ("Ⅲ", "DIGER"), ("♪", "DIGER"), ("\U0001f600", "DIGER"),
    ("α", "DIGER"), ("Я", "DIGER"), ("ش", "DIGER"), ("अ", "DIGER"), ("ก", "DIGER"),
    ("\U0001b000", "DIGER"), ("\U0001b100", "DIGER"),   # Kana Ek / Kana Uzanti-A (astral) -- docstring: DIGER [ÖLÇÜLMÜYOR]
    ("㈱", "DIGER"), ("㊙", "DIGER"), ("㍿", "DIGER"), ("㆒", "DIGER"), ("〶", "DIGER"),    # cevrelenmis/kanbun CJK isaretleri: tabloda yok -> DIGER
    ("ㄅ", "DIGER"),   # Bopomofo: tabloda yok -> DIGER
    ("㄰", "Hangul"),  # atanmamis (Cn) ama uyumluluk Jamo blogunda
    ("　", "SINIR"), (" ", "SINIR"), ("。", "SINIR"), ("「", "SINIR"), ("〜", "SINIR"), ("－", "SINIR"), ("_", "SINIR"),
    ("を", "SINIR"), ("が", "SINIR"),  # JP parcacik -> gercek sinir (iki tarafta)
    ("​", "DIGER"), ("­", "DIGER"),  # Cf: DIGER sinifi (docstring [ÖLÇÜLMÜYOR])
]

yaz("== betik sinifi tablosu (kamu API): karakter | kategori | sag: hit vermeyen terim siniflari | sol: ... | docstring | uyum")
uyumsuz = 0
for ch, beklenen in TABLO:
    kat = unicodedata.category(ch)
    ad = unicodedata.name(ch, "?")
    sag = {s for s, t in TERIMLER.items() if not st.lookup(t + ch)}
    sol = {s for s, t in TERIMLER.items() if not st.lookup(ch + t)}
    if beklenen == "SINIR":
        olcum = "SINIR" if not sag and not sol else f"sag={sorted(sag)} sol={sorted(sol)}"
        uyum = not sag and not sol
    elif beklenen == "M*":
        # sagda: HICBIR terim eslesmez (M* sinir degil; NFC birlesik uretebilir); solda: karakterin blok sinifi
        olcum = f"sag={sorted(sag)} sol={sorted(sol)}"
        uyum = sag == set(TERIMLER) and len(sol) <= 1
    else:
        olcum = f"sag={sorted(sag)} sol={sorted(sol)}"
        uyum = sag == {beklenen} and sol == {beklenen}
    uyumsuz += not uyum
    yaz(f"U+{ord(ch):05X} {ad[:38]:38s} {kat} | {olcum:52s} | {beklenen:9s} | {'ok' if uyum else 'UYUMSUZ'}")
yaz(f"toplam {len(TABLO)} karakter, docstring ile uyumsuz: {uyumsuz}")

yaz("")
yaz("== yarim genislik katakana: NFC != NFKC (tam genislik terimi bulmaz; ayri terim olarak calisir)")
yaz(f"  マルクス terimi, metin ﾏﾙｸｽが: {len(st.lookup('ﾏﾙｸｽが'))} hit")
st2 = sozluk(("ﾏﾙｸｽ", "Marcus"))
yaz(f"  ﾏﾙｸｽ terimi, metin ﾏﾙｸｽが: {len(st2.lookup('ﾏﾙｸｽが'))} hit; metin マルクスが: {len(st2.lookup('マルクスが'))} hit")
yaz(f"  NFKC('ﾏﾙｸｽ') == 'マルクス': {unicodedata.normalize('NFKC', 'ﾏﾙｸｽ') == 'マルクス'}; NFC esit mi: {unicodedata.normalize('NFC', 'ﾏﾙｸｽ') == 'マルクス'}")

yaz("")
yaz("== Kelvin isareti U+212A: NFC -> K; source_term NFC dilim")
st3 = sozluk(("Kelvin", "K"))
h = st3.lookup("Kelvin")
yaz(f"  hit: {[(x.start, x.end, x.source_term) for x in h]}; source_term ASCII K mi: {h[0].source_term == 'Kelvin'}")

OUT.write_text("\n".join(satirlar) + "\n", encoding="utf-8")
print(f"yazildi -> {OUT.name}")
