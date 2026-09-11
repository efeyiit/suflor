"""T-011 Tester-A TUR 2 -- mercek: GARANTI ALANI + SINIR; paket v3 (▲) siniflari.

Hedef: K1 zincir kurali, betik gecisi, JP saygi / KR ek listeleri, trie-IGNORECASE denkligi;
K2 NFC (`placeholders`) + `ContractViolation`; K5 dogrusal maliyet / ozyineleme yok; K6 kaynak
terminatoru, hedef `Cc`, kaynak <= 100. Kural 10: her negatif icin ayni siniftan pozitif kontrol.
`test_bulgu_*` MEVCUT davranisi pinler (rapordaki bulgu); duzeltilirse kirilarak haber verir.

Kosum: python -m pytest .agents/tasks/T-011/tester_A -q -p no:cacheprovider --import-mode=importlib
"""
from __future__ import annotations

import dataclasses
import random
import re
import statistics
import sys
import time
import unicodedata
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from yardimci import KOK, seg, sozluk, sozluk_ham  # noqa: E402
from src.contracts.errors import ContractViolation  # noqa: E402
from src.contracts.models import Rect, Segment, TermHit  # noqa: E402
from src.translate.sozluk import GlossaryStore, terimleri_gom  # noqa: E402

NFD = lambda s: unicodedata.normalize("NFD", s)  # noqa: E731
NFC = lambda s: unicodedata.normalize("NFC", s)  # noqa: E731
FIXTURE = KOK / ".agents/tasks/T-011/fixtures/sozluk_ornek.json"


def araliklar(hits):
    return [(h.start, h.end) for h in hits]


def gom1(store, metin, yt=()):
    s = seg(metin, yt)
    hits = tuple(dataclasses.replace(h, segment_index=0) for h in store.lookup(metin, yt))
    return terimleri_gom((s,), hits)[0].text


@pytest.fixture(scope="module")
def jp():
    return sozluk(("マルクス", "Marcus"), ("長老", "İhtiyar"), ("水車小屋", "Değirmen"), ("アイラ", "Ayla"))


@pytest.fixture(scope="module")
def kr():
    return sozluk(("방앗간", "Değirmen"), ("마르쿠스", "Marcus"), ("아일라", "Ayla"), ("장로", "İhtiyar"))


@pytest.fixture(scope="module")
def lat():
    return sozluk(("Marcus", "Marcus"), ("wind", "Rüzgar"), ("mill", "Değirmen"), ("stone", "Tas"))


@pytest.fixture(scope="module")
def hira():
    return sozluk(("ひかり", "Hikari"), ("マルクス", "Marcus"), ("長老", "İhtiyar"))


# ===========================================================================
# Z -- K1 ZINCIR kurali (▲ v3)
# ===========================================================================


@pytest.mark.parametrize(
    "metin, beklenen",
    [
        ("長老マルクス", [(0, 2), (2, 6)]),                        # 2 uyeli
        ("長老マルクスアイラ", [(0, 2), (2, 6), (6, 9)]),           # 3 uyeli
        ("長老マルクスアイラ水車小屋", [(0, 2), (2, 6), (6, 9), (9, 13)]),
        ("マルクス" * 10, [(4 * i, 4 * i + 4) for i in range(10)]),  # 10 uyeli, tekrar eden terim
        ("マルクスマルクス", [(0, 4), (4, 8)]),
    ],
)
def test_z_zincir_uye_sayisi_jp(jp, metin, beklenen):
    assert araliklar(jp.lookup(metin)) == beklenen


def test_z_zincir_tekrar_eden_terim_latin(lat):
    """`MarcusMarcus` -> 2 (zincir); `Marcuss`/`MarcusMarcuss` -> 0 (dis uc `s` DIGER|DIGER sinir degil)."""
    assert araliklar(lat.lookup("MarcusMarcus")) == [(0, 6), (6, 12)]
    assert araliklar(lat.lookup("Marcus" * 10)) == [(6 * i, 6 * i + 6) for i in range(10)]
    assert lat.lookup("Marcuss") == [] and lat.lookup("MarcusMarcuss") == []
    assert gom1(lat, "MarcusMarcuss") == "MarcusMarcuss"


@pytest.mark.parametrize(
    "metin, yt, beklenen",
    [
        ("{0}マルクスアイラ", ("{0}",), [(3, 7), (7, 10)]),     # zincir sol ucu yer tutucu
        ("マルクスアイラ{0}", ("{0}",), [(0, 4), (4, 7)]),     # zincir sag ucu yer tutucu
        ("%swindmill", ("%s",), [(2, 6), (6, 10)]),          # Latin: yt bildirilmis -> ucu sinir
        ("windmill%s", ("%s",), [(0, 4), (4, 8)]),
        ("xwindmill%s", ("%s",), []),                        # sol dis uc `x` -> zincir olu (negatif)
        ("wind%smill", ("%s",), [(0, 4), (6, 10)]),          # yt zincirin ortasinda: iki ayri tek uye
        ("windAAmill", ("AA",), [(0, 4), (6, 10)]),          # harf yt: bildirilince korunur ve sinirdir
        ("windAAmill", (), []),                              # bildirilmezse `AA` metindir -> 0 (pozitif kontrol cifti)
    ],
)
def test_z_zincir_ucu_yer_tutucu(jp, lat, metin, yt, beklenen):
    st = jp if "マ" in metin else lat
    assert araliklar(st.lookup(metin, yt)) == beklenen


@pytest.mark.parametrize(
    "metin, beklenen",
    [
        ("마르쿠스아일라에게", [(0, 4), (4, 7)]),     # zincir sag ucu KR ek (listeden)
        ("마르쿠스아일라에게는", [(0, 4), (4, 7)]),   # ek zinciri 2
        ("마르쿠스아일라에게는을", []),              # ek zinciri 3 -> belgeli sinir (negatif)
        ("장로마르쿠스아일라가", [(0, 2), (2, 6), (6, 9)]),
        ("마르쿠스아일라가나", []),                  # ekten sonra harf -> zincirin HICBIR uyesi
        ("마르쿠스아일라", [(0, 4), (4, 7)]),        # pozitif kontrol: metin ucu
    ],
)
def test_z_zincir_ucu_kr_ek(kr, metin, beklenen):
    assert araliklar(kr.lookup(metin)) == beklenen


@pytest.mark.parametrize(
    "metin, beklenen",
    [
        ("長老マルクス村", [(0, 2), (2, 6)]),      # zincir sag ucu betik gecisi (Katakana|Han)
        ("村長老マルクス", [(3, 7)]),              # 長老 solu Han|Han -> olu; マルクス solu Han|Katakana -> tek
        ("村長老マルクス村", [(3, 7)]),
        ("2長老マルクス", [(1, 3), (3, 7)]),        # sol dis uc rakam (DIGER|Han)
        ("長老マルクスx", [(0, 2), (2, 6)]),        # sag dis uc Latin (Katakana|DIGER)
    ],
)
def test_z_zincir_ucu_betik_gecisi(jp, metin, beklenen):
    assert araliklar(jp.lookup(metin)) == beklenen


@pytest.mark.parametrize("sira", [0, 1])
def test_z_zincir_ortusen_daha_uzun_aday_olu_kisa_zincir_kazanir(sira):
    """{水車小屋, 水車, 小屋町} + `水車小屋町`: en uzun `水車小屋` sag ucu `町` (Han|Han) olu -> atlanir;
    `水車`+`小屋町` zinciri iki dis ucu sinirli -> kabul. JSON sirasi sonucu degistirmez."""
    ciftler = [("水車小屋", "Değirmen"), ("水車", "SuArabasi"), ("小屋町", "KulubeKasabasi")]
    if sira:
        ciftler.reverse()
    st = sozluk(*ciftler)
    h = st.lookup("水車小屋町")
    assert [(x.start, x.end, x.target_term) for x in h] == [(0, 2, "SuArabasi"), (2, 5, "KulubeKasabasi")]
    assert [(x.start, x.end, x.target_term) for x in st.lookup("水車小屋 x")] == [(0, 4, "Değirmen")]  # uzun canliyken kazanir


@pytest.mark.parametrize("sira", [0, 1])
def test_z_zincir_windmill_uzun_terim_varken(sira):
    ciftler = [("wind", "Rüzgar"), ("mill", "Değirmen"), ("windmill", "YelDegirmeni")]
    if sira:
        ciftler.reverse()
    st = sozluk(*ciftler)
    assert st.lookup("windmills") == []
    assert [(x.start, x.end, x.target_term) for x in st.lookup("windmill")] == [(0, 8, "YelDegirmeni")]
    assert [(x.start, x.end, x.target_term) for x in st.lookup("wind mill")] == [(0, 4, "Rüzgar"), (5, 9, "Değirmen")]


@pytest.mark.parametrize("metin", ["windmills", "millstones", "windmillstones", "xwindmillstone", "windmillstonex", "MarcusMarcuss"])
def test_z_zincir_hicbir_uye_eslesmez_ortadaki_dahil(lat, metin):
    """Docstring: dis uc sinir degilse zincirin HICBIR uyesi eslesmez -- ortadaki `mill` dahil; metin dokunulmaz."""
    assert lat.lookup(metin) == []
    assert gom1(lat, metin) == metin


def test_z_zincir_pozitif_kontrol(lat):
    assert araliklar(lat.lookup("windmillstone")) == [(0, 4), (4, 8), (8, 13)]
    assert gom1(lat, "windmillstone") == "RüzgarDeğirmenTas"
    assert araliklar(lat.lookup("wind mill stone")) == [(0, 4), (5, 9), (10, 15)]
    assert araliklar(lat.lookup("Marcuswindmill")) == [(0, 6), (6, 10), (10, 14)]


@pytest.mark.parametrize(
    "metin",
    ["長老マルクスアイラ村", "水車小屋マルクス長老アイラ", "windmillstone wind mills", "마르쿠스아일라장로에게", "MarcusMarcuswindmill x"],
)
def test_z_iki_sozluk_sirasi_ayni_sonuc(metin):
    ciftler = [("マルクス", "Marcus"), ("長老", "İhtiyar"), ("水車小屋", "Değirmen"), ("アイラ", "Ayla"),
               ("Marcus", "Marcus"), ("wind", "Rüzgar"), ("mill", "Değirmen"), ("stone", "Tas"),
               ("마르쿠스", "Marcus"), ("아일라", "Ayla"), ("장로", "İhtiyar")]
    a = sozluk(*ciftler).lookup(metin)
    b = sozluk(*reversed(ciftler)).lookup(metin)
    assert [(x.start, x.end, x.target_term) for x in a] == [(x.start, x.end, x.target_term) for x in b]
    assert a  # pozitif: bos degil


# ---------------------------------------------------------------------------
# Z-fuzz -- zincir degismezleri, bagimsiz sinir tanimiyla (kural 8: referans uygulamadan turemez)
# ---------------------------------------------------------------------------

_HARF = "abc村人あい"
_SINIF = {"a": 0, "b": 0, "c": 0, "村": 1, "人": 1, "あ": 2, "い": 2, "を": 9, " ": 9, ".": 9, "x": 0}
_AYIRAC = {"を", " ", "."}
_ALFABE = _HARF + "を ."


def _sol(t, p):
    return p == 0 or t[p - 1] in _AYIRAC or _SINIF[t[p - 1]] != _SINIF[t[p]]


def _sag(t, e):
    return e == len(t) or t[e] in _AYIRAC or _SINIF[t[e - 1]] != _SINIF[t[e]]


def _korunan(t, yt):
    out = []
    for y in yt:
        i = t.find(y)
        while i != -1:
            out.append((i, i + len(y)))
            i = t.find(y, i + len(y))
    return out


def _adaylar(t, terimler):
    out = []
    for term in terimler:
        i = t.find(term)
        while i != -1:
            out.append((i, i + len(term), term))
            i = t.find(term, i + 1)
    return out


def _degismezler(t, terimler, hits, yt=()):
    """(1) sirali/ortusmesiz/dilim=terim, (2) her bitisik kosunun dis uclari gercek sinir (yt ucu dahil),
    (3) iki ucu sinirli ve kabul edilenlerle/korunanla ortusmeyen aday atlanmaz, (4) kabul edilmis komsu ucu da sinir,
    (5) hic bir hit korunan aralikla ortusmez. Doner: (kosu_sayisi >= 2 olan kosu sayisi, reddedilen aday sayisi)."""
    korunan = _korunan(t, yt)
    yt_bas = {a for a, _ in korunan}
    yt_bit = {b for _, b in korunan}
    hs = araliklar(hits)
    assert hs == sorted(hs)
    for (s, e), h in zip(hs, hits):
        assert t[s:e] in terimler and h.source_term == t[s:e]
    for (s1, e1), (s2, e2) in zip(hs, hs[1:]):
        assert e1 <= s2
    for s, e in hs:
        for a, b in korunan:
            assert e <= a or b <= s, ("yer tutucu ortusmesi", s, e, a, b)
    sol = lambda p: _sol(t, p) or p in yt_bit  # noqa: E731
    sag = lambda e: _sag(t, e) or e in yt_bas  # noqa: E731
    uzun_kosu = 0
    i = 0
    while i < len(hs):
        j = i
        while j + 1 < len(hs) and hs[j][1] == hs[j + 1][0]:
            j += 1
        assert sol(hs[i][0]) and sag(hs[j][1]), ("kosu dis uc", hs[i][0], hs[j][1])
        uzun_kosu += j > i
        i = j + 1
    dolu = [False] * len(t)
    for s, e in hs + korunan:
        for k in range(s, e):
            dolu[k] = True
    kabul_bas = {s for s, _ in hs}
    kabul_bit = {e for _, e in hs}
    red = 0
    for s, e, term in _adaylar(t, terimler):
        if any(dolu[s:e]):
            red += (s, e) not in hs
            continue
        red += 1
        assert not (sol(s) and sag(e)), ("atlanan gercek-sinirli aday", s, e, term)
        assert not ((sol(s) or s in kabul_bit) and (sag(e) or e in kabul_bas)), ("atlanan komsu-sinirli aday", s, e, term)
    return uzun_kosu, red


@pytest.mark.parametrize("tohum", [1, 2, 3])
def test_z_fuzz_zincir_degismezleri_ve_json_sirasi(tohum):
    """300 rastgele sozluk x 20 metin: bes degismez + JSON sirasindan bagimsizlik. Pozitif kontrol (kural 10):
    en az 100 metinde 2+ uyeli zincir kabul edildi, en az 300 aday zincir/ortusme yuzunden reddedildi."""
    rnd = random.Random(tohum)
    uzun_toplam = red_toplam = 0
    for _ in range(300):
        terimler = set()
        while len(terimler) < rnd.randint(2, 7):
            terimler.add("".join(rnd.choice(_HARF) for _ in range(rnd.choice([1, 2, 2, 3, 3]))))
        terimler = sorted(terimler)
        kayitlar = [{"kaynak": x, "hedef": "T" + str(i), "kisa_terim_izni": True} for i, x in enumerate(terimler)]
        st, st2 = sozluk(*kayitlar), sozluk(*reversed(kayitlar))
        for _ in range(20):
            t = "".join(rnd.choice(_ALFABE) for _ in range(rnd.randint(1, 14)))
            h1, h2 = st.lookup(t), st2.lookup(t)
            assert araliklar(h1) == araliklar(h2), t
            uzun, red = _degismezler(t, terimler, h1)
            uzun_toplam += uzun
            red_toplam += red
    assert uzun_toplam >= 100 and red_toplam >= 300, (uzun_toplam, red_toplam)


def test_z_fuzz_yer_tutucu_ile_zincir_degismezleri():
    """Yer tutucu `xx` (harf; bildirilmezse metin): korunan aralik hic hit almaz, uclari sinirdir; pozitif kontrol:
    ayni metinlerde yt bildirilmeyince `xx` civarinda hit sayisi farklidir (en az bir metinde)."""
    rnd = random.Random(7)
    fark = 0
    korunan_var = 0
    for _ in range(200):
        terimler = sorted({"".join(rnd.choice(_HARF) for _ in range(rnd.choice([1, 2, 3]))) for _ in range(rnd.randint(2, 6))})
        st = sozluk(*[{"kaynak": x, "hedef": "T", "kisa_terim_izni": True} for x in terimler])
        for _ in range(15):
            parcalar = ["".join(rnd.choice(_ALFABE) for _ in range(rnd.randint(0, 5))) for _ in range(3)]
            t = parcalar[0] + "xx" + parcalar[1] + ("xx" if rnd.random() < 0.5 else "") + parcalar[2]
            h = st.lookup(t, ("xx",))
            korunan_var += len(_korunan(t, ("xx",))) > 0
            _degismezler(t, terimler, h, ("xx",))
            fark += araliklar(h) != araliklar(st.lookup(t))
    assert korunan_var > 0 and fark > 0


# ===========================================================================
# B -- BETIK GECISI (▲ v3): sinif tablosu ve sinir olcumu (docstring ile karsilastirma)
# ===========================================================================

# (karakter, docstring sinifi) -- sinif, kamu API'siyla olculur: ayni betikli terim + karakter -> hit YOK;
# farkli betikli terim + karakter -> hit VAR. Terimler: Katakana マルクス, Han 長老, Hiragana ひかり, Hangul 마르쿠스, DIGER Marcus.
BETIK_TABLOSU = [
    ("ー", "Katakana"),   # ー uzatma isareti
    ("ｰ", "Katakana"),   # ｰ yarim genislik uzatma
    ("ﾏ", "Katakana"),   # ﾏ yarim genislik
    ("ㇰ", "Katakana"),   # ㇰ fonetik uzanti (kucuk ku)
    ("ヶ", "Katakana"),   # ヶ kucuk ke
    ("ヽ", "Katakana"),   # ヽ katakana tekrar isareti
    ("々", "Han"),        # 々 kanji tekrar isareti
    ("〆", "Han"),        # 〆
    ("〇", "Han"),        # 〇
    ("三", "Han"),        # 三 kanji sayisi
    ("漢", "Han"),        # 漢 hanja
    ("⼀", "Han"),        # ⼀ Kangxi radikali (So)
    ("\U00020000", "Han"),    # CJK uzanti B
    ("あ", "Hiragana"),   # あ (か/よ/ね ek, を/が parcacik: tabloya alinmaz)
    ("ゝ", "Hiragana"),   # ゝ hiragana tekrar isareti
    ("ᄀ", "Hangul"),     # Hangul Jamo (U+1100 blogu)
    ("ㄱ", "Hangul"),     # uyumluluk Jamo
    ("ﾡ", "Hangul"),     # yarim genislik Hangul
    ("나", "Hangul"),     # hece (가/이/은... ek: tabloya alinmaz)
    ("Ｍ", "DIGER"),      # Ｍ tam genislik Latin
    ("ａ", "DIGER"),      # ａ
    ("2", "DIGER"),
    ("①", "DIGER"),      # ①
    ("♪", "DIGER"),      # ♪ (So)
    ("\U0001f600", "DIGER"),  # emoji
    ("α", "DIGER"),      # Yunan alfa
    ("\U0001b100", "DIGER"),  # hentaigana (Kana Ek) -- docstring [ÖLÇÜLMÜYOR]: DIGER sayilir
    ("㈱", "DIGER"),      # ㈱ cevrelenmis CJK (So) -- tabloda yok -> DIGER
]
_BETIK_TERIMLERI = {"Katakana": "マルクス", "Han": "長老", "Hiragana": "ひかり", "Hangul": "마르쿠스", "DIGER": "Marcus"}


@pytest.fixture(scope="module")
def bes_betik():
    return sozluk(*[(t, "T" + s) for s, t in _BETIK_TERIMLERI.items()])


@pytest.mark.parametrize("ch, sinif", BETIK_TABLOSU, ids=[f"U+{ord(c):04X}-{s}" for c, s in BETIK_TABLOSU])
def test_b_betik_sinifi_kamu_apiyle_olculur(bes_betik, ch, sinif):
    """Sagda: yalniz ayni siniftaki terimle hit YOK (sinif ici komsu sinir degil), digerlerinde hit VAR."""
    assert unicodedata.category(ch)[0] not in "MPZ", "tablo yalniz harf/sembol/rakam icin"
    olculen = {s for s, t in _BETIK_TERIMLERI.items() if not bes_betik.lookup(t + ch)}
    assert olculen == {sinif}, (hex(ord(ch)), olculen)
    solda = {s for s, t in _BETIK_TERIMLERI.items() if not bes_betik.lookup(ch + t)}
    assert solda == {sinif}, (hex(ord(ch)), solda)   # simetrik


def test_b_betik_gecisi_docstring_ornekleri_pozitif(jp, kr, lat):
    for st, m, beklenen in [
        (jp, "長老マルクス", 2), (jp, "マルクス様", 1), (jp, "マルクスさん", 1), (jp, "マルクスたち", 1), (jp, "長老Marcus", 1),
        (lat, "Marcus様", 1), (kr, "마르쿠스Marcus", 1), (jp, "マルクス三", 1), (jp, "2マルクス", 1), (jp, "マルクス2", 1),
        (kr, "마르쿠스漢", 1), (kr, "漢마르쿠스", 1), (jp, "マルクス♪", 1), (jp, "\U0001f600マルクス", 1), (jp, "マルクス山", 1),
    ]:
        assert len(st.lookup(m)) == beklenen, m


def test_b_betik_gecisi_docstring_ornekleri_negatif(jp, kr, lat):
    for st, m in [
        (jp, "マルクスタウン"), (jp, "アイラー"), (jp, "マルクスー"), (jp, "ーマルクス"), (jp, "マルクスヶ"), (jp, "マルクスㇰ"),
        (kr, "검사"), (kr, "방앗간집"), (kr, "마르쿠스ᄀ"), (kr, "ᄀ마르쿠스"), (kr, "마르쿠스ㄱ"),
        (lat, "Marcus2"), (lat, "Marcuss"), (lat, "windmills"), (lat, "Marcus♪"), (lat, "Marcus\U0001f600"), (lat, "Ｍarcus"), (lat, "Marcusａ"),
    ]:
        assert st.lookup(m) == [], m


def test_b_birlestirici_isaret_sagda_sinir_degil_solda_betik_gecisi(jp, lat):
    """Sagdaki `M*` terimin son karakterine aittir (sinir degil); NFC birlesik uretse de terim degisir."""
    assert jp.lookup("マルクズ") == []                       # ス+゛ -> NFC ズ
    assert jp.lookup("マルクス゚") == []                       # birlesik yok, M* sagda -> sinir degil
    assert lat.lookup("Marcuś") == []                       # s+´ -> ś
    assert lat.lookup("Marcus̸") == []                       # birlesik yok; M* sagda
    assert araliklar(jp.lookup("マルクスか゚")) == [(0, 4)]     # pozitif: か゚ Hiragana|Katakana gecisi
    assert araliklar(jp.lookup("か゚マルクス")) == [(2, 6)]     # solda M* Hiragana sinifinda -> betik gecisi


def test_b_yarim_genislik_katakana_tam_genislik_terimi_bulmaz_nfc_nfkc_degil(jp):
    """BILGI: metin NFC'lenir, NFKC degil -> `ﾏﾙｸｽ` (yarim genislik) `マルクス` terimini bulmaz; sozlukte yarim
    genislik yazim ayri terim olarak calisir (pozitif kontrol)."""
    assert jp.lookup("ﾏﾙｸｽが来た") == []
    st = sozluk(("ﾏﾙｸｽ", "Marcus"))
    assert araliklar(st.lookup("ﾏﾙｸｽが来た")) == [(0, 4)]
    assert st.lookup("マルクスが来た") == []


def test_b_ideografik_bosluk_ve_orta_nokta_gercek_sinir(jp):
    assert araliklar(jp.lookup("マルクス・アイラ")) == [(0, 4), (5, 8)]     # ・ Po (Katakana blogunda ama noktalama)
    assert araliklar(jp.lookup("マルクス　アイラ")) == [(0, 4), (5, 8)]


# ===========================================================================
# E -- EK LISTELERI (▲ v3): JP saygi/kopula, KR yonelme/saygi/cogul/kopula
# ===========================================================================

JP_EKLER = ["さん", "様", "殿", "君", "ちゃん", "達", "たち", "って", "だ", "から", "まで", "より", "か", "よ", "ね"]
KR_EKLER_G6 = ["을", "를", "이", "가", "은", "는", "에", "에서", "으로", "로", "와", "과", "도", "의", "만", "께서", "부터", "까지"]
KR_EKLER_V3 = ["에게", "한테", "께", "님", "씨", "야", "아", "랑", "이랑", "들", "처럼", "보다", "마다", "밖에", "조차", "라고", "라면", "입니다", "이다"]


@pytest.mark.parametrize("ek", JP_EKLER)
def test_e_jp_her_ek_ayni_betikli_terimle_yuk_tasir(hira, ek):
    """Hiragana terim + hiragana ek / Han terim + kanji ek: betik gecisi yok, ek listesi tek dayanak."""
    terim = "長老" if unicodedata.category(ek[0]) == "Lo" and ord(ek[0]) >= 0x4E00 else "ひかり"
    assert araliklar(hira.lookup(terim + ek)) == [(0, len(terim))], ek
    assert araliklar(hira.lookup(terim + ek + "が")) == [(0, len(terim))], ek        # ek + parcacik
    assert araliklar(hira.lookup(terim + ek + "。")) == [(0, len(terim))], ek


@pytest.mark.parametrize("metin", ["マルクスさんが", "マルクス様には", "マルクスさんたちが", "ひかりさんが", "ひかりさんたちには", "長老様には", "長老達が"])
def test_e_jp_ek_parcacik_zinciri(hira, metin):
    terim = metin[:4] if metin.startswith("マ") else metin[:3] if metin.startswith("ひ") else metin[:2]
    assert araliklar(hira.lookup(metin)) == [(0, len(terim))]


def test_e_jp_ek_zinciri_en_fazla_iki_ayni_betikte(hira):
    """Docstring: `ひかりだからね` (uc ek) eslesmez; iki ek eslesir. Katakana terimde betik gecisi ek sayisini anlamsiz kilar."""
    assert hira.lookup("ひかりだからね") == []
    assert hira.lookup("ひかりさんたちよ") == []
    assert araliklar(hira.lookup("ひかりだから")) == [(0, 3)]
    assert araliklar(hira.lookup("ひかりさんたち")) == [(0, 3)]
    assert araliklar(hira.lookup("マルクスさんたちよね")) == [(0, 4)]      # Katakana|Hiragana gecisi: ek sayisi onemsiz
    assert araliklar(hira.lookup("マルクスだからね")) == [(0, 4)]


def test_e_jp_ek_listesi_bilesik_uretmez_negatif(hira):
    assert hira.lookup("ひかりさんご") == []      # さん + go
    assert hira.lookup("ひかりこ") == []
    assert hira.lookup("長老様子") == []          # 様 + 子
    assert hira.lookup("ひかりかわ") == []        # か + わ
    assert araliklar(hira.lookup("ひかりやま")) == [(0, 3)]   # や parcacik (docstring)


def test_bulgu_e_jp_hiragana_saygi_ekleri_kun_sama_listede_yok(hira):
    """ORTA (paket eksigi, gercek motorla olculdu -- `r2-sonda-03`): hiragana yazimli ad + hiragana `くん`/`さま`
    (listede yalniz kanji `君`/`様`) -> 0 hit; ham ceviride ad "isik" oldu, gomme yapilamadi (Y-B2 sinifi).
    Katakana adda betik gecisi kurtarir (pozitif). Pin: duzeltilirse kirilir."""
    assert hira.lookup("ひかりくんが来た。") == []
    assert hira.lookup("ひかりさまが来た。") == []
    assert araliklar(hira.lookup("ひかりさんが来た。")) == [(0, 3)]       # pozitif: listedeki ek
    assert araliklar(hira.lookup("マルクスくんが来た。")) == [(0, 4)]      # pozitif: betik gecisi


@pytest.mark.parametrize("ek", KR_EKLER_G6 + KR_EKLER_V3)
def test_e_kr_her_ek(kr, ek):
    assert araliklar(kr.lookup("마르쿠스" + ek)) == [(0, 4)], ek
    assert araliklar(kr.lookup("마르쿠스" + ek + " 왔다.")) == [(0, 4)], ek
    assert araliklar(kr.lookup("마르쿠스" + ek + "는")) == [(0, 4)] or ek in ("는", "은"), ek   # 2 ek (ayni ek x2 de zincir)


def test_e_kr_uc_ek_kacar_belgeli(kr):
    """Docstring BILINEN SINIR: `님`+`에게`+`는` (uc ek) eslesmez; iki ek eslesir (pozitif)."""
    assert kr.lookup("장로님에게는") == []
    assert kr.lookup("마르쿠스님에게는") == []
    assert kr.lookup("마르쿠스들에게는") == []
    assert araliklar(kr.lookup("장로님에게")) == [(0, 2)]
    assert araliklar(kr.lookup("마르쿠스들에게")) == [(0, 4)]
    assert araliklar(kr.lookup("마르쿠스들이다")) == [(0, 4)]      # docstring: `들`+`이다` = iki ek (paketle celiski pinlendi)


def test_e_kr_ek_ile_baslayan_kelime_bilesik_negatif(kr):
    assert kr.lookup("마르쿠스님프") == []        # 님 + 프 (nymph)
    assert kr.lookup("마르쿠스씨앗") == []        # 씨 + 앗
    assert kr.lookup("마르쿠스아침") == []        # 아 + 침
    assert kr.lookup("방앗간도둑") == []          # 도 + 둑
    assert kr.lookup("마르쿠스이다음") == []      # 이다 + 음
    assert araliklar(kr.lookup("마르쿠스님 프")) == [(0, 4)]   # pozitif


def test_e_kr_irang_rang_en_uzun_once(kr):
    assert araliklar(kr.lookup("마르쿠스이랑")) == [(0, 4)]
    assert araliklar(kr.lookup("마르쿠스랑")) == [(0, 4)]
    assert araliklar(kr.lookup("마르쿠스이랑은")) == [(0, 4)]      # 이랑 + 은 (2 ek); 이+랑+은 olsaydi 3
    assert araliklar(kr.lookup("마르쿠스랑은")) == [(0, 4)]
    assert kr.lookup("마르쿠스이랑은요") == []                    # 이랑+은+요 -> 3 (요 listede yok zaten)


def test_bulgu_e_kr_kopula_da_yeyo_ve_cikma_hanteseo_listede_yok(kr):
    """DUSUK (paket eksigi; gercek motor -- `r2-sonda-03`: bu cumlelerde ham ceviri adi zaten koruyor):
    unlu sonrasi kopula `다` (`마르쿠스다`; `이다` listede ama `다` yok), kibar kopula `예요`/`이에요`, cikma
    `한테서`/`에게서` -> 0 hit. Pozitif: `입니다`, `이다`, `한테`, `에게`."""
    assert kr.lookup("마르쿠스다") == []
    assert kr.lookup("마르쿠스예요") == []
    assert kr.lookup("마르쿠스한테서") == []
    assert kr.lookup("마르쿠스에게서") == []
    assert araliklar(kr.lookup("마르쿠스입니다")) == [(0, 4)]
    assert araliklar(kr.lookup("마르쿠스이다")) == [(0, 4)]
    assert araliklar(kr.lookup("마르쿠스한테")) == [(0, 4)]


def test_e_kr_ek_solda_sinir_degil_v3_listesi_dahil(kr):
    for ek in ("에게", "님", "들", "입니다"):
        assert kr.lookup(ek + "마르쿠스") == [], ek
    assert araliklar(kr.lookup("님 마르쿠스")) == [(2, 6)]


# ===========================================================================
# T -- TRIE / IGNORECASE denkligi (▲ v3)
# ===========================================================================


@pytest.mark.parametrize("sira", [0, 1])
@pytest.mark.parametrize("a, b", [("ß", "ẞ"), ("ΐ", "ΐ"), ("ΰ", "ΰ"), ("ﬅ", "ﬆ"), ("ᾈ", "ᾀ"), ("ǅ", "Ǆ"), ("µ", "μ")],
                         ids=lambda x: f"U+{ord(x):04X}")
def test_t_ignorecase_denk_cift_tek_dal_her_sirada(a, b, sira):
    """`a`~`b` re.I denk (bagimsiz kontrol). {a+xy, b+xz, a+x} sozlugunde harfiyen gecen her terim her sirada bulunur;
    capraz yazim (b+xy) da eslesir (denklik)."""
    assert re.fullmatch(re.escape(a), b, re.I) and re.fullmatch(re.escape(b), a, re.I)
    ciftler = [(a + "xy", "A"), (b + "xz", "B"), (a + "x", "C")]
    if sira:
        ciftler[0], ciftler[1] = ciftler[1], ciftler[0]
    st = sozluk(*ciftler)
    for metin, hedef in [(b + "xz q", "B"), (a + "xy q", "A"), (b + "xy q", "A"), (a + "xz q", "B"), (a + "x q", "C"), (b + "x q", "C")]:
        h = st.lookup(metin)
        assert [(x.start, x.end, x.target_term, x.source_term) for x in h] == [(0, len(metin) - 2, hedef, metin[: len(metin) - 2])], metin


@pytest.mark.parametrize("terim", ["İstanbul", "istanbul", "ISTANBUL", "ıstanbul"])
@pytest.mark.parametrize("metin", ["İstanbul", "istanbul", "ISTANBUL", "ıstanbul", "İSTANBUL"])
def test_t_turkce_i_sinifi_matrisi_indeksler_orijinal_metne_gore(terim, metin):
    st = sozluk((terim, "Istanbul"))
    h = st.lookup("x " + metin + " y")
    assert [(x.start, x.end, x.source_term) for x in h] == [(2, 10, metin)]
    assert gom1(st, "x " + metin + " y") == "x Istanbul y"


def test_t_i_nokta_birlesik_ignorecase_disi_eslesmez_ama_tekrar_sayilir():
    """BILGI (D-A2 sinifi): `i`+U+0307 (2 kodpoint, NFC birlesmez) `İ` ile re.I denk DEGIL -> eslesmez; ama
    kanonik anahtar ayni -> tekrar reddi."""
    st = sozluk(("İstanbul", "Istanbul"))
    assert st.lookup("i̇stanbul") == []
    with pytest.raises(ValueError, match="tekrar eden kaynak"):
        sozluk(("İstanbul", "A"), ("i̇stanbul", "B"))


def test_t_kelvin_uzun_s_ve_karisik_yazim_source_term_metinden():
    st = sozluk(("Kelvin", "K"), ("Straße", "S"))
    for m in ["Kelvin", "KELVIN", "kelvin"]:          # ilki U+212A KELVIN SIGN: NFC -> `K`, source_term NFC dilim
        h = st.lookup(m)
        assert araliklar(h) == [(0, 6)] and h[0].source_term == NFC(m)
    assert NFC("Kelvin") == "Kelvin" and "Kelvin" != "Kelvin"
    for m in ["STRAẞE", "straße", "Straße"]:
        h = st.lookup(m)
        assert araliklar(h) == [(0, 6)] and h[0].source_term == m
    assert st.lookup("strasse") == []      # ss != ß (re.I)


# ===========================================================================
# N -- K2 NFC (▲ v3): text + placeholders birlikte; hit'siz aynen; speaker/source_blocks aynen
# ===========================================================================


@pytest.fixture(scope="module")
def noir():
    return sozluk(("noir", "Kara"), ("café", "Kahve"))


def test_n_hitli_nfd_segment_text_ve_placeholders_nfc_her_yer_tutucu_alt_dize(noir):
    yt = NFD("{Ünlü}")
    s = Segment(text=yt + " noir " + yt + NFD(" été"), bbox=Rect(1, 2, 3, 4), speaker=NFD("Ünlü"), placeholders=(yt, NFD("é"), "", "zzz"),
                source_blocks=(3, 1))
    hits = noir.lookup_segments((s,))
    assert araliklar(hits) == [(7, 11)] and hits[0].segment_index == 0
    out = terimleri_gom((s,), hits)[0]
    assert out.text == NFC(out.text) == "{Ünlü} Kara {Ünlü} été"
    assert out.placeholders == ("{Ünlü}", "é", "", "zzz")           # NFC, uzunluk/sira/bos oge korunur
    assert all(p == NFC(p) for p in out.placeholders)
    assert all(p in out.text for p in out.placeholders if p and p != "zzz")
    assert out.speaker == s.speaker and out.speaker != NFC(out.speaker)   # speaker DOKUNULMAMIS (NFD kaldi)
    assert out.source_blocks == (3, 1) and out.bbox == Rect(1, 2, 3, 4)
    assert s.text != NFC(s.text) and s.placeholders[0] != NFC(s.placeholders[0])   # girdi degismedi


def test_n_hitsiz_nfd_segment_ayni_nesne(noir):
    s0 = seg(NFD("café noir"), (NFD("ü"),))
    s1 = seg(NFD("été"), (NFD("é"),), speaker=NFD("Ü"))
    hits = noir.lookup_segments((s0, s1))
    assert [h.segment_index for h in hits] == [0, 0]
    out = terimleri_gom((s0, s1), hits)
    assert out[1] is s1 and out[1].text != NFC(out[1].text) and out[1].placeholders[0] != NFC(out[1].placeholders[0])
    assert out[0] is not s0 and out[0].text == "Kahve Kara" and out[0].placeholders == ("ü",)
    assert terimleri_gom((s0, s1), ())[0] is s0


@pytest.mark.parametrize("yt", ["{0}", b"{0}", None, 5, ("{0}", 5), ("{0}", None), [("{0}",)]], ids=repr)
def test_n_segment_placeholders_bicimi_contract_violation_iki_yolda(noir, yt):
    s = Segment(text="noir", bbox=Rect(0, 0, 1, 1), placeholders=yt)  # type: ignore[arg-type]
    with pytest.raises(ContractViolation) as e1:
        noir.lookup_segments((s,))
    with pytest.raises(ContractViolation) as e2:
        terimleri_gom((s,), (TermHit("noir", "Kara", 0, 4, 0),))
    assert "placeholders" in str(e1.value) and "placeholders" in str(e2.value)
    assert isinstance(e1.value, ContractViolation) and not isinstance(e1.value, TypeError)


def test_n_dogrudan_lookup_placeholders_type_error_kalir(noir):
    with pytest.raises(TypeError):
        noir.lookup("noir", "{0}")
    with pytest.raises(TypeError):
        noir.lookup("noir", ("{0}", 5))


def test_n_segment_text_str_degil_contract_violation(noir):
    s = Segment(text=5, bbox=Rect(0, 0, 1, 1))  # type: ignore[arg-type]
    with pytest.raises(ContractViolation):
        noir.lookup_segments((s,))
    with pytest.raises(ContractViolation):
        terimleri_gom((s,), (TermHit("5", "X", 0, 1, 0),))


def test_bulgu_n_hitsiz_segmentin_bozuk_placeholders_gomde_denetlenmez(noir):
    """BILGI (docstring K2 'hit'i olmayan segment ayni nesne'): `terimleri_gom` hit'i olmayan segmentin `placeholders`
    bicimini denetlemez (aynen doner); pipeline'da `lookup_segments` ayni segmenti CV ile yakalar (pozitif)."""
    bozuk = Segment(text="x", bbox=Rect(0, 0, 1, 1), placeholders="{0}")  # type: ignore[arg-type]
    iyi = seg("noir")
    out = terimleri_gom((bozuk, iyi), (TermHit("noir", "Kara", 0, 4, 1),))
    assert out[0] is bozuk and out[1].text == "Kara"
    with pytest.raises(ContractViolation):
        noir.lookup_segments((bozuk, iyi))


def test_n_nfd_hit_nfc_segment_uyumu(noir):
    """NFD `source_term` + NFC segment: K2 tam esitlik iki tarafi NFC'leyerek karsilastirir."""
    s = seg("le café noir")
    h = TermHit(NFD("café"), NFD("kahvé"), 3, 7, 0)
    out = terimleri_gom((s,), (h,))[0]
    assert out.text == "le Kahvé noir" and out.text == NFC(out.text)
    assert out is not s


# ===========================================================================
# S -- K6 (▲ v3): kaynak terminatoru, hedef Cc, kaynak <= 100, ozyineleme yok
# ===========================================================================

TERMINATORLER = list(".!?。！？")


@pytest.mark.parametrize("t", TERMINATORLER, ids=lambda c: f"U+{ord(c):04X}")
@pytest.mark.parametrize("konum", ["son", "bas", "orta"])
def test_s_kaynakta_her_terminator_her_konumda_red(t, konum):
    kaynak = {"son": "ab" + t, "bas": t + "ab", "orta": "a" + t + "b"}[konum]
    with pytest.raises(ValueError) as ei:
        sozluk((kaynak, "X"))
    assert "cumle sonu" in str(ei.value) and repr(kaynak) in str(ei.value)


@pytest.mark.parametrize("t", TERMINATORLER, ids=lambda c: f"U+{ord(c):04X}")
def test_s_hedefte_her_terminator_red(t):
    with pytest.raises(ValueError, match="cumle sonu"):
        sozluk(("ab", "X" + t))


@pytest.mark.parametrize("kaynak", ["ab…", "ab;", "ab,", "ab、", "ab:", "a-b", "a'b", "ab~", "St Marcus", "Mr Marcus"])
def test_s_kaynakta_terminator_olmayan_noktalama_kabul_pozitif(kaynak):
    st = sozluk((kaynak, "X"))
    assert araliklar(st.lookup(kaynak + " geldi")) == [(0, len(kaynak))]


@pytest.mark.parametrize("cc", ["\n", "\t", "\r", "\x00", "\x1f", "\x7f", "\x85", "\x0b", "\x0c"], ids=lambda c: f"U+{ord(c):04X}")
def test_s_hedefte_her_kontrol_karakteri_red(cc):
    with pytest.raises(ValueError) as ei:
        sozluk(("ab", "X" + cc + "Y"))
    assert "kontrol karakteri" in str(ei.value) and f"U+{ord(cc):04X}" in str(ei.value)


def test_bulgu_s_hedefte_satir_ayirici_zl_zp_ve_cf_kabul():
    """BILGI: docstring yalniz `Cc` yasaklar; U+2028 (Zl) / U+2029 (Zp) `str.splitlines` tarafindan satir sonu sayilir,
    U+200B/U+00AD/U+FEFF (Cf) gorunmezdir -- hepsi hedefte KABUL. Pozitif kontrol: U+0085 (Cc, NEL) red."""
    for ch in (" ", " ", "​", "­", "﻿"):
        st = sozluk(("ab", "X" + ch + "Y"))
        assert gom1(st, "ab") == "X" + ch + "Y"
        assert len(("X" + ch + "Y").splitlines()) == (2 if ch in "  " else 1)
    with pytest.raises(ValueError, match="kontrol karakteri"):
        sozluk(("ab", "X\x85Y"))


def test_bulgu_s_kaynakta_kontrol_karakteri_kabul():
    """BILGI: kaynakta `\\n`/`\\t`/NUL reddedilmez (yalniz bas/son bosluk ve terminator); eslesme harfiyen."""
    st = sozluk(("a\nb", "X"), ("c\x00d", "Y"))
    assert araliklar(st.lookup("a\nb c\x00d")) == [(0, 3), (4, 7)]


@pytest.mark.parametrize("n, kabul", [(1, False), (2, True), (99, True), (100, True), (101, False), (2000, False), (10000, False)])
def test_s_kaynak_uzunluk_siniri_tam_100_asla_recursion_error(n, kabul):
    kaynak = "a" * n
    if kabul:
        st = sozluk((kaynak, "X"))
        assert araliklar(st.lookup("x " + kaynak + " y")) == [(2, 2 + n)]
    else:
        with pytest.raises(ValueError) as ei:
            sozluk((kaynak, "X"))
        assert ("en fazla 100" in str(ei.value)) == (n > 100)
        assert not isinstance(ei.value, RecursionError)


def test_s_kaynak_uzunluk_nfc_sonrasi_olculur():
    assert len(sozluk((NFD("é") * 100, "X")).terimler[0].kaynak) == 100     # NFD 200 kodpoint -> NFC 100 kabul
    with pytest.raises(ValueError, match="101 kodpoint"):
        sozluk((NFD("é") * 101, "X"))


def test_s_yuz_kodpointlik_terim_dusuk_ozyineleme_limitinde_yuklenir():
    """Trie govdesi derinligi <= 101: 100 kodpointlik terim, ozyineleme limiti 300'ken de yuklenir (2000 kodpointlik
    metinde 20 gecis bulunur; arama yigin tabanli)."""
    eski = sys.getrecursionlimit()
    sys.setrecursionlimit(300)
    try:
        st = sozluk(("マ" * 100, "X"), ("マ" * 50 + "ル", "Y"))
        h = st.lookup((" " + "マ" * 100) * 20)
        assert len(h) == 20 and all(x.target_term == "X" for x in h)
    finally:
        sys.setrecursionlimit(eski)


def test_s_bin_terimli_sozluk_hepsi_100_kodpoint():
    terimler = [(chr(0x30A1 + i % 80) + chr(0x30A1 + i // 80) + "".join(chr(0x30A1 + (i * 7 + k) % 80) for k in range(98)), "T" + str(i))
                for i in range(1000)]
    st = sozluk(*terimler)
    assert len(st) == 1000
    assert araliklar(st.lookup(terimler[500][0] + " " + terimler[999][0])) == [(0, 100), (101, 201)]


# ===========================================================================
# P -- K5 (▲ v3): hit sayisinda dogrusal, zincir 8000, lookup_segments 1000 x fixture
# ===========================================================================


def _medyan_ms(f, n=5):
    t = []
    for _ in range(n):
        t0 = time.perf_counter()
        f()
        t.append((time.perf_counter() - t0) * 1000)
    return statistics.median(t)


def _izleyici_var():
    return sys.gettrace() is not None or "coverage" in sys.modules


@pytest.mark.skipif(_izleyici_var(), reason="sure olcusu izleyicisiz kosumda (docstring: izleyici 4x)")
def test_p_8000_hit_tek_segment_60ms_ve_dogrusal():
    st = sozluk(("マルクス", "Marcus"), ("長老", "İhtiyar"))
    m4, m8 = "長老マルクス " * 2000, "長老マルクス " * 4000
    assert len(st.lookup(m8)) == 8000
    t4, t8 = _medyan_ms(lambda: st.lookup(m4)), _medyan_ms(lambda: st.lookup(m8))
    assert t8 < 60, t8
    assert t8 / t4 < 3.0, (t4, t8)          # 2x hit -> ~2x sure (docstring: amortize dogrusal)


@pytest.mark.skipif(_izleyici_var(), reason="sure olcusu izleyicisiz kosumda")
def test_p_zincir_8000_uyeli_canli_ve_olu_60ms():
    st = sozluk(("マルクス", "Marcus"), ("長老", "İhtiyar"))
    canli = "マルクス" * 8000
    olu_sag = "マルクス" * 8000 + "ー"       # sag dis uc Katakana|Katakana -> tum zincir olu
    olu_sol = "ー" + "マルクス" * 8000
    assert len(st.lookup(canli)) == 8000 and st.lookup(olu_sag) == [] and st.lookup(olu_sol) == []
    for m in (canli, olu_sag, olu_sol):
        assert _medyan_ms(lambda: st.lookup(m)) < 60
    t4, t8 = _medyan_ms(lambda: st.lookup("マルクス" * 4000 + "ー")), _medyan_ms(lambda: st.lookup(olu_sag))
    assert t8 / t4 < 3.0, (t4, t8)


@pytest.mark.skipif(_izleyici_var(), reason="sure olcusu izleyicisiz kosumda")
def test_p_lookup_segments_1000_segment_fixture_v3_50ms():
    st = GlossaryStore(FIXTURE)
    assert len(st) == 7
    segs = tuple(Segment(text="長老マルクスが水車小屋で待っています。 방앗간을 지나 Marcus by the mill.", bbox=Rect(0, i, 1, 1)) for i in range(1000))
    hits = st.lookup_segments(segs)
    assert len(hits) == 4000 and {h.segment_index for h in hits} == set(range(1000))
    assert _medyan_ms(lambda: terimleri_gom(segs, st.lookup_segments(segs))) < 50


def test_p_onek_zinciri_a10000_dogrusal_ve_geri_izleme():
    """Tur 1 D-A1 ornegi: `a2..a11` onekleri + `a`*10000. Tur 1: 909 hit (son `a` reddedilip kalanlar kabul), 850 ms.
    v3 zincir kurali: 909 x a11 + kalan 1 `a` sinirsiz -> DFS geri sarar: 908 x a11 + a10 + a2 = 910 uye, metin
    tamamen kaplanir (zincirin dis ucu metin sonu). < 200 ms."""
    st = sozluk(*[("a" * k, "A" + str(k)) for k in range(2, 12)])
    m = "a" * 10000
    h = st.lookup(m)
    assert len(h) == 910 and araliklar(h)[:2] == [(0, 11), (11, 22)] and araliklar(h)[-2:] == [(9988, 9998), (9998, 10000)]
    assert sum(x.end - x.start for x in h) == 10000
    if not _izleyici_var():
        assert _medyan_ms(lambda: st.lookup(m), 3) < 200


def test_p_thread_safe_paylasilan_store_ayni_sonuc():
    """Docstring: `GlossaryStore` yuklemeden sonra degismez, arama durumu cagri-yerel -> 8 is parcacigi ayni
    sonucu verir (zincir + ek + yt karisik girdiler)."""
    import threading

    st = sozluk(("マルクス", "Marcus"), ("長老", "İhtiyar"), ("アイラ", "Ayla"), ("wind", "Rüzgar"), ("mill", "Değirmen"))
    girdiler = [("長老マルクスアイラ村 windmills windmill {0}マルクス", ("{0}",)), ("マルクス" * 300 + "ー", ()), ("wind mill " * 100, ()),
                ("村長老マルクス", ()), ("マルクスさんたちが", ())]
    beklenen = [araliklar(st.lookup(m, yt)) for m, yt in girdiler]
    hatalar: list[str] = []

    def isci(k: int) -> None:
        rnd = random.Random(k)
        for _ in range(150):
            i = rnd.randrange(len(girdiler))
            m, yt = girdiler[i]
            if araliklar(st.lookup(m, yt)) != beklenen[i]:
                hatalar.append(f"isci {k} girdi {i}")

    ipler = [threading.Thread(target=isci, args=(k,)) for k in range(8)]
    for t in ipler:
        t.start()
    for t in ipler:
        t.join()
    assert hatalar == [] and beklenen[0] == [(0, 2), (2, 6), (6, 9), (21, 25), (25, 29), (33, 37)]
