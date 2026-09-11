"""T-011 Tester-A -- mercek: GARANTI ALANI + SINIR.

Docstring'in (src/translate/sozluk.py) her cumlesi bir iddia; burada kabul edilen
uc girdilerde tutuyor mu diye olculur. Kural 10: her "eslesmez" icin ayni siniftan
bir pozitif kontrol vardir. `test_bulgu_*` adli testler MEVCUT davranisi PINLER
(rapordaki bulgu); duzeltilirse kirilarak haber verir.

Kosum: python -m pytest .agents/tasks/T-011/tester_A -q -p no:cacheprovider --import-mode=importlib
"""
from __future__ import annotations

import dataclasses
import io
import logging
import re
import statistics
import sys
import time
import unicodedata
import warnings
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from yardimci import seg, sozluk, sozluk_ham  # noqa: E402
from src.contracts.errors import ContractViolation  # noqa: E402
from src.contracts.models import Segment, TermHit  # noqa: E402
from src.translate.sozluk import GlossaryStore, ilk_harfi_buyut, terimleri_gom  # noqa: E402

NFD = lambda s: unicodedata.normalize("NFD", s)  # noqa: E731
NFC = lambda s: unicodedata.normalize("NFC", s)  # noqa: E731


def araliklar(hits):
    return [(h.start, h.end) for h in hits]


def gom1(store, metin, yt=()):
    s = seg(metin, yt)
    hits = tuple(dataclasses.replace(h, segment_index=0) for h in store.lookup(metin, yt))
    return terimleri_gom((s,), hits)[0].text


# ---------------------------------------------------------------------------
# A1 -- K1 sinir kurali simetrisi: KR ek yalniz SAG, JP parcacik iki taraf
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def kr():
    return sozluk(("방앗간", "Değirmen"), ("마르쿠스", "Marcus"))


@pytest.fixture(scope="module")
def jp():
    return sozluk(("マルクス", "Marcus"), ("長老", "İhtiyar"), ("水車小屋", "Değirmen"))


@pytest.mark.parametrize(
    "metin, beklenen",
    [
        ("방앗간을", [(0, 3)]),            # terim metnin basinda + ek, ek metin sonunda
        ("을방앗간", []),                  # ek SOLDA -> sinir degil (docstring: yalniz sag)
        ("지나 방앗간", [(3, 6)]),          # terim metnin sonunda
        ("방앗간", [(0, 3)]),              # tek basina
        ("방앗간에서는", [(0, 3)]),         # ek zinciri 2
        ("방앗간에서는을", []),             # ek zinciri 3 -> docstring: hayir
        ("방앗간이가을", []),               # zinciri 3 (kisa ekler) -> hayir
        ("방앗간이가", [(0, 3)]),           # zincir 2 pozitif kontrol
        ("방앗간으로", [(0, 3)]),           # uzun ek 으로
        ("방앗간로", [(0, 3)]),             # kisa ek 로
        ("방앗간으", []),                   # 으 tek basina ek degil -> harf komsusu
        ("방앗간을.", [(0, 3)]),            # ekten sonra noktalama
        ("방앗간을마르쿠스", [(0, 3)]),      # ekten sonra baska terim: 방앗간 evet; 마르쿠스 solu 을 (harf) -> hayir
        ("방앗간마르쿠스", [(0, 3), (3, 7)]),  # bitisik iki terim -> ikisi de (komsu terim kurali)
        ("방앗간도둑", []),                 # 도 + 둑: ekten sonra sinir yok
        ("방앗간도 둑", [(0, 3)]),           # pozitif kontrol
        ("방앗간에서에서에서", []),          # ayni ek x3 -> hayir (zincir 2)
        ("방앗간에서에서", [(0, 3)]),        # ayni ek x2 -> evet
    ],
)
def test_a1_kr_ek_simetrisi_ve_zinciri(kr, metin, beklenen):
    assert araliklar(kr.lookup(metin)) == beklenen


@pytest.mark.parametrize(
    "metin, beklenen",
    [
        ("がマルクス", [(1, 5)]),           # parcacik SOLDA sinir (KR ekten farkli)
        ("マルクスが", [(0, 4)]),
        ("村マルクス", []),                 # kanji komsu solda
        ("マルクス村", []),                 # kanji komsu sagda
        ("マルクスの村", [(0, 4)]),          # の parcacik
        ("マルクス　長老", [(0, 4), (5, 7)]),  # ideografik bosluk
        ("長老マルクス", [(0, 2), (2, 6)]),
        ("マルクス長老", [(0, 4), (4, 6)]),
        ("長老マルクス水車小屋", [(0, 2), (2, 6), (6, 10)]),  # UC terim bitisik
        ("マルクスマルクス", [(0, 4), (4, 8)]),               # ayni terim iki kez bitisik
        ("マルクスマルクスマルクス", [(0, 4), (4, 8), (8, 12)]),
        ("長老マルクス村", [(0, 2)]),        # マルクス sagi 村 -> ret; 長老 sagi マルクス basi -> kabul
        ("村長老マルクス", [(3, 7)]),        # 長老 solu 村 -> ret; マルクス solu 長老 BITISI (kabul edilmemis komsu yeter -- docstring)
        ("村長老マルクス村", []),            # ikisi de dis sinirsiz
    ],
)
def test_a1_jp_parcacik_ve_komsu_terim(jp, metin, beklenen):
    assert araliklar(jp.lookup(metin)) == beklenen


def test_a1_kr_ek_solda_negatif_pozitif_kontrolu(kr):
    """Kural 10: '을방앗간' eslesmez (0) -- ayni siniftan pozitif: bosluk solda eslesir."""
    assert kr.lookup("을방앗간") == []
    assert araliklar(kr.lookup("을 방앗간")) == [(2, 5)]


# ---------------------------------------------------------------------------
# A2 -- ortusme, en uzun once, esit uzunluk, JSON sirasindan bagimsizlik
# ---------------------------------------------------------------------------


def test_a2_kismi_ortusme_sinirsiz_hic_eslesmez_ve_pozitif():
    st = sozluk(("ABCD", "Uzun"), ("CDEF", "Kisa"))
    assert st.lookup("ABCDEF") == []          # ikisi de ic siniri saglamaz
    assert araliklar(st.lookup("ABCD CDEF")) == [(0, 4), (5, 9)]   # pozitif kontrol


@pytest.mark.parametrize("sira", [0, 1])
def test_a2_esit_uzunluk_ortusme_kucuk_start_kazanir_json_sirasindan_bagimsiz(sira):
    """Docstring K1/3: esit uzunlukta ortusen iki aday -> kucuk start kazanir; JSON sirasi sonucu degistirmez.
    Noktalama iceren kaynaklar iki adayin da sinirli olmasini saglar: 'a-b' [0,3) ve 'b-c' [2,5) 'a-b-c'te ortusur."""
    ciftler = [("a-b", "Bir"), ("b-c", "Iki")]
    if sira:
        ciftler.reverse()
    st = sozluk(*ciftler)
    h = st.lookup("a-b-c")
    assert araliklar(h) == [(0, 3)]
    assert h[0].target_term == "Bir"
    # pozitif kontrol: ikinci terim tek basina eslesir
    assert araliklar(st.lookup("x b-c")) == [(2, 5)]


def test_a2_onek_terim_uzun_terimin_icinde_yutulur_tek_basina_eslesir():
    st = sozluk(("ABC", "Uzun"), ("BC", "Kisa"))
    h = st.lookup("ABC")
    assert araliklar(h) == [(0, 3)] and h[0].target_term == "Uzun"
    assert araliklar(st.lookup("BC")) == [(0, 2)]
    assert st.lookup("xABC") == []            # her ikisi de sol sinirsiz


@pytest.mark.parametrize("sira", [0, 1])
def test_a2_iki_sirali_sozluk_ayni_sonuc(sira):
    ciftler = [("水車小屋", "Değirmen"), ("水車", "SuArabasi"), ("小屋", "Kulube")]
    if sira:
        ciftler.reverse()
    st = sozluk(*ciftler)
    h = st.lookup("水車小屋を過ぎて 小屋は 水車が")
    assert [(x.start, x.end, x.target_term) for x in h] == [(0, 4, "Değirmen"), (9, 11, "Kulube"), (13, 15, "SuArabasi")]


def test_a2_ayni_terim_n_gecis_start_artan_kodpoint():
    st = sozluk(("Marcus", "Marcus"))
    h = st.lookup("Marcus, MARCUS ve marcus.")
    assert araliklar(h) == [(0, 6), (8, 14), (18, 24)]
    assert [x.source_term for x in h] == ["Marcus", "MARCUS", "marcus"]
    assert all(x.segment_index is None for x in h)


# ---------------------------------------------------------------------------
# A3 -- IGNORECASE + kanonik anahtar
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def latin():
    return sozluk(("Marcus", "Marcus"), ("İstanbul", "İstanbul"), ("straße", "Sokak"), ("fine", "Ince"),
                  ("ΣΟΦΙΑ", "Sofya"), ("Кремль", "Kremlin"), ("kelvin", "Kelvin"), ("dış", "Dis"))


@pytest.mark.parametrize("metin", ["MARCUS", "marcus", "mArCuS", "Marcuſ"])
def test_a3_buyuk_kucuk_source_term_metindeki_dilim(latin, metin):
    h = latin.lookup(metin)
    assert araliklar(h) == [(0, 6)]
    assert h[0].source_term == metin          # docstring: METINDEKI DILIM
    assert h[0].target_term == "Marcus"
    assert gom1(latin, metin) == "Marcus"


@pytest.mark.parametrize("metin", ["istanbul", "ISTANBUL", "ıstanbul", "İSTANBUL", "İstanbul"])
def test_a3_turkce_i_sinifi_dort_harf_denk(latin, metin):
    h = latin.lookup(metin)
    assert araliklar(h) == [(0, 8)] and h[0].source_term == metin


def test_a3_kelvin_isareti_ve_uzun_s(latin):
    assert araliklar(latin.lookup("Kelvin")) == [(0, 6)]   # U+212A KELVIN SIGN ~ k
    assert araliklar(latin.lookup("KELVIN")) == [(0, 6)]


def test_a3_yunan_sigma_ve_kiril(latin):
    assert araliklar(latin.lookup("σοφια")) == [(0, 5)]
    assert araliklar(latin.lookup("Σοφια")) == [(0, 5)]
    assert latin.lookup("σοφιας") == []       # final sigma harf komsusu (ek)
    assert araliklar(latin.lookup("кремль")) == [(0, 6)]
    assert araliklar(latin.lookup("КРЕМЛЬ")) == [(0, 6)]


def test_bulgu_a3_eszett_ss_eslesmez_ama_tekrar_sayilir(latin):
    """DUSUK: `_anahtar` casefold (ß -> ss) ile TEKRAR reddi yapar; eslestirici re.I (ß != ss).
    Sonuc: 'straße' sozlukteyken 'STRASSE'/'strasse' eslesmez, ama 'straße'+'strasse' cifti
    'tekrar eden kaynak' diye reddedilir -- docstring 'esleme semantigiyle' der, iki semantik ayrisiyor."""
    assert latin.lookup("STRASSE") == []
    assert latin.lookup("strasse") == []
    assert araliklar(latin.lookup("STRAẞE")) == [(0, 6)]      # buyuk eszett U+1E9E re.I ile eslesir (pozitif)
    with pytest.raises(ValueError, match="tekrar eden kaynak"):
        sozluk(("straße", "A"), ("strasse", "B"))


def test_bulgu_a3_fi_ligature_eslesmez_ama_tekrar_sayilir(latin):
    assert latin.lookup("ﬁne") == []
    assert araliklar(latin.lookup("FINE")) == [(0, 4)]
    with pytest.raises(ValueError, match="tekrar eden kaynak"):
        sozluk(("fine", "A"), ("ﬁne", "B"))


def test_bulgu_a3_turkce_dis_dis_ayni_anahtar():
    """DUSUK/bilgi: Turkce 'dış' (disari) ve 'diş' (dis) IGNORECASE I-sinifiyla AYNI terim sayilir;
    kaynak dili Turkce olmadigi icin urun etkisi yok, belgelenir."""
    st = sozluk(("dış", "Dis"))
    assert araliklar(st.lookup("diş")) == [(0, 3)]
    with pytest.raises(ValueError, match="tekrar eden kaynak"):
        sozluk(("dış", "A"), ("diş", "B"))


@pytest.mark.parametrize("a, b", [("Marcus", "MARCUS"), ("istanbul", "İstanbul"), ("K", "K"), ("s", "ſ")])
def test_a3_tekrar_reddi_ignorecase_denk_ciftler(a, b):
    with pytest.raises(ValueError) as ei:
        sozluk({"kaynak": a, "hedef": "X", "kisa_terim_izni": True}, {"kaynak": b, "hedef": "Y", "kisa_terim_izni": True})
    assert "tekrar eden kaynak" in str(ei.value)


# ---------------------------------------------------------------------------
# A4 -- NFC: indeksler, gom ciktisi, aralik disi karakter
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def nfc_st():
    return sozluk(("Değirmen", "Değirmen"), ("방앗간", "Değirmen"), ("café", "Kahve"), ("noir", "Kara"))


def test_a4_nfd_metin_indeksler_nfc_metne_gore(nfc_st):
    metin = NFD("le café noir")            # 13 kodpoint; NFC 12
    assert len(metin) == 13
    h = nfc_st.lookup(metin)
    assert [(x.start, x.end, x.source_term) for x in h] == [(3, 7, "café"), (8, 12, "noir")]
    assert NFC(metin)[3:7] == "café"       # indeks NFC metne gore
    assert metin[3:7] != "café"            # NFD metinde dilim FARKLI -- cagiran NFC'lemeli


def test_a4_nfd_hangul_jamo_eslesir(nfc_st):
    metin = NFD("방앗간을 지나")            # 17 kodpoint
    assert len(metin) == 17
    assert araliklar(nfc_st.lookup(metin)) == [(0, 3)]
    assert araliklar(nfc_st.lookup(NFD("Değirmen eski"))) == [(0, 8)]


def test_a4_gom_nfd_segment_kabul_cikti_nfc(nfc_st):
    metin = NFD("le café noir")
    assert gom1(nfc_st, metin) == "le Kahve Kara"    # NFD dilim tutarsizligi ContractViolation DEGIL: gom da NFC'ler


def test_bulgu_a4_gom_nfd_segment_aralik_disi_kodpointler_degisir(nfc_st):
    """ORTA: K2 'aralik disi her karakter aynen' vs K6 'gom segment metnini NFC'ler'.
    Hit'li NFD segmentte aralik DISI 'café'/'été' kodpoint duzeyinde degisir (NFD -> NFC, 16 -> 13);
    hit'siz NFD segment ise aynen (NFD) kalir -> ayni cagrida iki segment farkli normalizasyonda."""
    st = sozluk(("noir", "Kara"))           # yalniz 'noir' terim; 'café'/'été' aralik DISI
    metin = NFD("café noir été")
    assert len(metin) == 16
    s1, s2 = seg(metin), seg(NFD("café été"))
    hits = tuple(dataclasses.replace(h, segment_index=0) for h in st.lookup(metin))
    assert araliklar(hits) == [(5, 9)]
    out = terimleri_gom((s1, s2), hits)
    assert out[0].text == "café Kara été" and out[0].text == NFC(out[0].text)
    assert out[0].text[:4] != metin[:4]             # aralik disi kodpointler degisti
    assert out[1] is s2 and out[1].text != NFC(out[1].text)   # hit'siz komsu segment NFD kaldi


def test_bulgu_a4_gom_nfd_segment_placeholders_text_iliskisi_bozulur(nfc_st):
    """ORTA: Segment.placeholders AYNEN (NFD) kopyalanir, text NFC'lenir -> girdide `yt in text` True,
    ciktida False. T-007 K5 onarimi `kaynak.count(yt)` ile calisir; cikti segmenti kendi icinde tutarsiz."""
    yt = NFD("{Ünlü}")
    s = seg(yt + " noir", (yt,))
    assert s.placeholders[0] in s.text
    hits = tuple(dataclasses.replace(h, segment_index=0) for h in nfc_st.lookup(s.text, s.placeholders))
    assert araliklar(hits) == [(7, 11)]
    out = terimleri_gom((s,), hits)[0]
    assert out.placeholders == s.placeholders
    assert out.placeholders[0] not in out.text      # iliski koptu
    assert NFC(out.placeholders[0]) in out.text     # NFC'lenmis hali var (pozitif kontrol)


def test_a4_gom_hit_nfd_source_term_ve_target_term_kabul(nfc_st):
    s = seg("le café noir")
    h = nfc_st.lookup(s.text)[0]
    out = terimleri_gom((s,), (dataclasses.replace(h, source_term=NFD(h.source_term), segment_index=0),))
    assert out[0].text == "le Kahve noir"
    out2 = terimleri_gom((s,), (dataclasses.replace(h, target_term=NFD("kahvé"), segment_index=0),))
    assert out2[0].text == "le Kahvé noir" and out2[0].text == NFC(out2[0].text)   # hedef NFC + buyuk


# ---------------------------------------------------------------------------
# A5 -- kodpoint indeksi; astral; birlestirici; Cf
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def kp():
    return sozluk(("マルクス", "Marcus"), ("Marcus", "Marcus"), ("か゚き", "Kaki"))


def test_a5_astral_karakter_once_indeks_kodpoint(kp):
    metin = "\U0002000B マルクス"            # astral 1 kodpoint (UTF-16'da 2)
    h = kp.lookup(metin)
    assert araliklar(h) == [(2, 6)] and metin[2:6] == "マルクス"
    assert gom1(kp, metin) == "\U0002000B Marcus"


def test_a5_birlestirici_isaret_terimin_icinde_eslesir(kp):
    """か゚ (ka + U+309A birlestirici handakuten, NFC'de bilesigi yok) terimin parcasi -> 3 kodpoint eslesir."""
    assert araliklar(kp.lookup("か゚きが")) == [(0, 3)]
    assert kp.lookup("かき゚が") == []          # pozitif kontrol: isaret baska yerde -> farkli dizi


def test_a5_birlestirici_isaret_terimin_ucunda_harf_gibi(kp):
    assert kp.lookup("Marcuś") == []     # NFC: s + U+0301 -> ś, terim degisir
    assert kp.lookup("́Marcus") == []
    assert kp.lookup("マルクズ") == []     # ス + dakuten -> ズ
    assert araliklar(kp.lookup("マルクス")) == [(0, 4)]


def test_bulgu_a5_emoji_ve_sembol_komsusu_sinir_degil(kp):
    """DUSUK (docstring `S*` [OLCULMUYOR] damgali): emoji (So) / $ (Sc) / + (Sm) komsusu sinir sayilmaz -> hit YOK."""
    assert kp.lookup("\U0001F600マルクス") == []
    assert kp.lookup("Marcus$") == []
    assert kp.lookup("Marcus+Marcus") == []
    assert araliklar(kp.lookup("\U0001F600 マルクス")) == [(2, 6)]   # pozitif kontrol


def test_bulgu_a5_bicim_karakterleri_cf_sinir_degil(kp):
    """DUSUK (docstring'de anilmiyor): soft hyphen U+00AD, ZWSP U+200B, WJ U+2060, ZWJ U+200D (Cf) komsusu -> hit YOK."""
    for cf in ("­", "​", "⁠", "‍"):
        assert kp.lookup(f"{cf}Marcus") == [], hex(ord(cf))
        assert kp.lookup(f"Marcus{cf} x") == [], hex(ord(cf))
    assert araliklar(kp.lookup(" Marcus　")) == [(1, 7)]   # NBSP/ideografik bosluk isspace -> pozitif


# ---------------------------------------------------------------------------
# A6 -- K3 yer tutucu sinirlari
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def yt_st():
    return sozluk(("Marcus", "Marcus"), ("マルクス", "Marcus"), ("PLAYER", "Oyuncu"), ("{0}{1}", "Cift"))


@pytest.mark.parametrize(
    "metin, yt, beklenen",
    [
        ("{0}{1}Marcus", ("{0}", "{0}{1}"), [(6, 12)]),      # birbirini iceren yt
        ("{0}{1}Marcus", ("{0}{1}", "{0}"), [(6, 12)]),
        ("{0}{1}Marcus", ("0}{1",), [(6, 12)]),              # kismi ortusen yt
        ("{0}{1}Marcus", (), [(0, 6), (6, 12)]),             # yt yok -> {0}{1} TERIM
        ("Marcus", ("", "Marcus"), []),                      # bos dize yok sayilir; yt == terim
        ("Marcus Marcus", ("Marcus",), []),                  # yt == terim, tum gecisler korunur
        ("Mar{0}cus", ("{0}",), []),                         # yt terimin icinden
        ("Marcus", ("x" * 10000,), [(0, 6)]),                # cok uzun yt (metinde yok)
        ("Marcus", ("M",), []),                              # tek harf yt, terimin ilk harfi
        ("Marcus", ("s",), []),
        ("Marcus", ("arc",), []),
        ("Marcusマルクス", ("マルクス",), [(0, 6)]),             # yt basi sinir
        ("マルクスMarcus", ("マルクス",), [(4, 10)]),            # yt sonu sinir
        ("MARCUS", ("Marcus",), [(0, 6)]),                   # yt buyuk/kucuk DUYARLI -> MARCUS terim
        ("{Ünlü}Marcus", (NFD("{Ünlü}"),), [(6, 12)]),        # NFD yt NFC'lenir
        (NFD("{Ünlü}") + "Marcus", ("{Ünlü}",), [(6, 12)]),   # NFD metin, NFC yt
    ],
)
def test_a6_yer_tutucu_sinirlari(yt_st, metin, yt, beklenen):
    assert araliklar(yt_st.lookup(metin, yt)) == beklenen


def test_a6_yer_tutucu_liste_kabul_duz_str_ret(yt_st):
    assert yt_st.lookup("Marcus", ["Marcus"]) == []
    with pytest.raises(TypeError):
        yt_st.lookup("Marcus", "Marcus")
    with pytest.raises(TypeError):
        yt_st.lookup("Marcus", (1,))
    with pytest.raises(TypeError):
        yt_st.lookup("Marcus", None)


@pytest.mark.parametrize(
    "metin, yt, hit",
    [
        ("{PLAYER}は村にいます", ("{PLAYER}",), TermHit("PLAYER", "Oyuncu", 1, 7, 0)),
        ("Marcus", ("Marcus",), TermHit("Marcus", "Marcus", 0, 6, 0)),
        ("Mar{0}cus", ("{0}",), TermHit("Mar{0}cus", "Marcus", 0, 9, 0)),
    ],
)
def test_a6_gom_yer_tutucuyla_ortusen_elle_hit_contract_violation(metin, yt, hit):
    with pytest.raises(ContractViolation, match="yer tutucu"):
        terimleri_gom((seg(metin, yt),), (hit,))
    # pozitif kontrol: yt bildirilmemisken ayni hit kabul
    assert terimleri_gom((seg(metin),), (hit,))[0].text.startswith(("Oyuncu", "Marcus", "{"))


# ---------------------------------------------------------------------------
# A7 -- cok buyuk girdiler, sure, geri izleme
# ---------------------------------------------------------------------------


def test_bulgu_a7_uzun_kaynak_terim_recursion_error():
    """ORTA: `_trie_govdesi` kaynak uzunlugu kadar ozyineler; ~996+ kodpointlik kaynak terim yuklemede
    RecursionError (ValueError degil, TranslatorError degil). Sema uzunluk siniri koymaz; docstring'in
    red listesinde yok -> belgesiz cokme sinifi. 300 kodpoint kabul (gercekci cumle-terim gecer)."""
    assert len(sozluk(("a" * 300, "X"))) == 1
    with pytest.raises(RecursionError):
        sozluk(("a" * 2000, "X"))


def test_a7_on_bin_karakterlik_segment_dogru_ve_hizli():
    st = sozluk(("マルクス", "Marcus"), ("長老", "İhtiyar"), ("水車小屋", "Değirmen"))
    metin = "長老マルクスが水車小屋で待っています。" * 500      # 9500 kodpoint, 1500 terim
    t0 = time.perf_counter()
    h = st.lookup(metin)
    sure = (time.perf_counter() - t0) * 1000
    assert len(h) == 1500 and araliklar(h)[:3] == [(0, 2), (2, 6), (7, 11)]
    out = gom1(st, metin)
    assert out.count("Marcus") == 500 and out.count("İhtiyar") == 500 and out.count("Değirmen") == 500
    assert sure < 2000, sure


def test_a7_bes_bin_terim_yukleme_ve_lookup():
    import random
    random.seed(11)
    hece = "가나다라마바사아자차카타파하거너더러머버서어저처커터퍼허"
    terimler: set[str] = set()
    while len(terimler) < 5000:
        terimler.add("".join(random.choice(hece) for _ in range(random.randint(2, 6))))
    sirali = sorted(terimler)
    st = sozluk(*[(t, "H" + str(i)) for i, t in enumerate(sirali)])
    assert len(st) == 5000
    metin = " ".join(sirali[i] + "을" for i in range(0, 5000, 125))     # 40 kelime
    h = st.lookup(metin)
    assert len(h) == 40


def test_a7_maliyet_terim_sayisindan_bagimsiz():
    """Docstring K5: 11 / 500 / 5000 terim ayni. Olcu: 1000 segment, oran < 2.5 (gevsek; olculdu 0.95-1.14)."""
    taban = [("マルクス", "Marcus"), ("水車小屋", "Değirmen"), ("방앗간", "Değirmen"), ("Marcus", "Marcus"), ("mill", "Değirmen")]
    dolgu = [("ダミー" + format(i, "x") + "語", "D" + str(i)) for i in range(2000)]
    segs = tuple(seg("長老マルクスが水車小屋で待っています。 방앗간을 지나 Marcus by the mill.") for _ in range(1000))

    def olc(st):
        t = []
        for _ in range(5):
            t0 = time.perf_counter()
            terimleri_gom(segs, st.lookup_segments(segs))
            t.append(time.perf_counter() - t0)
        return statistics.median(t)

    kucuk, buyuk = olc(sozluk(*taban)), olc(sozluk(*taban, *dolgu))
    assert buyuk / kucuk < 2.5, (kucuk, buyuk)


def test_bulgu_a7_maliyet_hit_sayisinda_karesel():
    """DUSUK: `_ortusur(start, end, kabul)` kabul listesini dogrusal tarar -> segment basina hit sayisinda
    O(n^2). Hit 4x -> sure > 6x (dogrusal 4x olurdu; olculdu ~11x). Gercekci segmentte (<= 10 hit) etkisiz;
    docstring 'metinle olcekli' der, hit yogunluguna bagli."""
    st = sozluk(("マルクス", "Marcus"), ("長老", "İhtiyar"))
    def olc(k):
        metin = "長老マルクス " * k
        t = []
        for _ in range(3):
            t0 = time.perf_counter(); st.lookup(metin); t.append(time.perf_counter() - t0)
        return statistics.median(t)
    a, b = olc(500), olc(2000)
    assert b / a > 6, (a, b)


def test_a7_regex_geri_izleme_yok_dallanan_trie():
    dal = sozluk(*[("ab" * k + "c", "X" + str(k)) for k in range(1, 30)], *[("ab" * k + "d", "Y" + str(k)) for k in range(1, 30)])
    t0 = time.perf_counter()
    assert dal.lookup("ab" * 5000) == []            # asla bitmeyen onek: geri izleme patlamamali
    assert (time.perf_counter() - t0) < 1.0
    assert araliklar(dal.lookup("ababc x abd")) == [(0, 5), (8, 11)]   # pozitif kontrol


# ---------------------------------------------------------------------------
# A8 -- K6 sema sinirlari ve hata mesajlari
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "veri, parca",
    [
        ({"terimler": {}}, "liste olmali"),
        ({"terimler": None}, "liste olmali"),
        ([], "ust duzey"),
        ({}, "ust duzey"),
        ({"terimler": [{"kaynak": "ab", "hedef": "  "}]}, "'hedef' bos"),
        ({"terimler": [{"kaynak": "  ", "hedef": "X"}]}, "'kaynak' bos"),
        ({"terimler": [{"kaynak": "ab", "hedef": "X", "not": 5}]}, "'not'"),
        ({"terimler": [{"kaynak": "ab", "hedef": "X。"}]}, "cumle sonu"),
        ({"terimler": [{"kaynak": "ab", "hedef": "X？"}]}, "cumle sonu"),
        ({"terimler": [{"kaynak": "ab", "hedef": "X", "ozel_ad": True}]}, "bilinmeyen anahtar"),
        ({"terimler": [{"kaynak": "ab", "hedef": "X", "kisa_terim_izni": 1}]}, "bool olmali"),
        ({"terimler": [{"kaynak": "ab", "hedef": "X", "kisa_terim_izni": None}]}, "bool olmali"),
        ({"terimler": [{"kaynak": "ab", "hedef": "X"}, "str"]}, "#1"),
        ({"terimler": [{"kaynak": "ab", "hedef": "X"}, None]}, "#1"),
        ({"terimler": [{"kaynak": "ab", "hedef": "X"}, {"kaynak": "cd"}]}, "'cd'"),      # ilk hatali kayit, terim adiyla
        ({"terimler": [{"kaynak": 5, "hedef": "X"}]}, "str olmali"),
        ({"terimler": [{"kaynak": "Değirmen", "hedef": "X"}, {"kaynak": NFD("Değirmen"), "hedef": "Y"}]}, "tekrar eden kaynak"),
        ({"terimler": [{"kaynak": "\U0001F600", "hedef": "X"}]}, "tek kodpoint"),
    ],
)
def test_a8_sema_reddi(veri, parca):
    with pytest.raises(ValueError) as ei:
        sozluk_ham(veri)
    assert parca in str(ei.value), str(ei.value)


@pytest.mark.parametrize(
    "veri",
    [
        {"terimler": []},                                                            # bos sozluk gecerli
        {"terimler": [{"kaynak": "ab", "hedef": "X", "kisa_terim_izni": True}]},      # izin + 2 kodpoint
        {"terimler": [{"kaynak": "ab", "hedef": "X", "not": ""}]},
        {"terimler": [{"kaynak": "ab", "hedef": "X", "not": None}]},
        {"terimler": [{"kaynak": "a b", "hedef": "X Y"}]},                           # ic bosluk
        {"terimler": [{"kaynak": "ab", "hedef": "X…"}]},                             # elipsis yasak degil
        {"terimler": [{"kaynak": "ab", "hedef": "X;"}]},
        {"terimler": [{"kaynak": "{0}", "hedef": "X"}]},                             # kaynakta yer tutucu bicimi serbest
        {"terimler": [{"kaynak": "İ", "hedef": "X", "kisa_terim_izni": True}]},
        {"terimler": [{"kaynak": "\U0001F600\U0001F600", "hedef": "X"}]},
        {"terimler": [{"kaynak": "ab", "hedef": "X"}], "oyun": "Test", "surum": 2},   # ust duzey ek anahtar
        {"terimler": [{"kaynak": "ab", "hedef": "X" * 10000}]},
    ],
)
def test_a8_sema_kabul(veri):
    st = sozluk_ham(veri)
    assert len(st) == len(veri["terimler"])
    if st.terimler:
        assert st.lookup(veri["terimler"][0]["kaynak"]) or veri["terimler"][0]["kaynak"] == "İ"


def test_bulgu_a8_hedefte_yeni_satir_ve_yer_tutucu_benzeri_kabul():
    """DUSUK: hedefte `\\n`/`\\t` ve `%s`/`<T0>`/`[Mill]` reddedilmez (yalniz .!?。！？{}). Gomulen `\\n` T-007
    bolmesine, `%s`/`[Mill]` segment placeholders ile cakismaya acik; docstring yalniz `{}`yi yasaklar."""
    for hedef in ("X\nY", "X\tY", "%s", "<T0>", "[Mill]"):
        st = sozluk(("ab", hedef))
        assert gom1(st, "ab") == ilk_harfi_buyut(hedef)


def test_a8_bos_sozluk_lookup_bos_ve_gom_aynen():
    st = sozluk_ham({"terimler": []})
    assert st.lookup("Marcus マルクス") == []
    assert st.lookup("") == []
    s = seg("x")
    assert terimleri_gom((s,), ())[0] is s


def test_a8_hata_mesajlari_terim_ve_dosya_adi_tasir_icerik_tasimaz(tmp_path):
    with pytest.raises(ValueError) as ei:
        sozluk_ham({"terimler": [{"kaynak": "GIZLI_TERIM_XYZ", "hedef": "St. Marcus"}]})
    assert "GIZLI_TERIM_XYZ" in str(ei.value)                 # sema hatasi TERIMI tasir (istenen)
    kotu = tmp_path / "çeviri" / "kotu.json"
    kotu.parent.mkdir()
    kotu.write_bytes(b"{GIZLI_ICERIK_ABC")
    with pytest.raises(ValueError) as ei2:
        GlossaryStore(kotu)
    assert "kotu.json" in str(ei2.value) and "GIZLI_ICERIK_ABC" not in str(ei2.value)
    with pytest.raises(FileNotFoundError):
        GlossaryStore(tmp_path / "yok.json")
    with pytest.raises(TypeError):
        GlossaryStore(123)  # type: ignore[arg-type]
    d = tmp_path / "dizin.json"
    d.mkdir()
    with pytest.raises(OSError) as ei3:
        GlossaryStore(d)
    assert not isinstance(ei3.value, ValueError)


def test_a8_bom_utf16_ascii_disi_yol(tmp_path):
    govde = '{"terimler": [{"kaynak": "ab", "hedef": "X"}]}'
    yol = tmp_path / "çeviri"
    yol.mkdir()
    (yol / "bom.json").write_bytes(b"\xef\xbb\xbf" + govde.encode("utf-8"))
    (yol / "u16.json").write_bytes(govde.encode("utf-16"))
    assert len(GlossaryStore(yol / "bom.json")) == 1
    assert len(GlossaryStore(str(yol / "u16.json"))) == 1
    (yol / "bozuk.json").write_bytes(b'{"terimler": [{"kaynak": "\xff\xfe", "hedef": "X"}]}')
    with pytest.raises(ValueError):
        GlossaryStore(yol / "bozuk.json")


# ---------------------------------------------------------------------------
# A9 -- K2/K7 ContractViolation: her sinif, mesaj sizintisi yok
# ---------------------------------------------------------------------------

GIZLI = seg("GIZLIMETIN kelimesi burada")
KOTU_HITLER = [
    pytest.param(TermHit("GIZLITERIM", "GIZLIHEDEF", 0, 999, 0), "aralik gecersiz", id="aralik-disi"),
    pytest.param(TermHit("GIZLITERIM", "GIZLIHEDEF", 0, 10, 0), "dilimiyle ayni degil", id="dilim-farkli"),
    pytest.param(TermHit("", "GIZLIHEDEF", 3, 3, 0), "aralik gecersiz", id="start-eq-end"),
    pytest.param(TermHit("GIZLITERIM", "GIZLIHEDEF", -1, 5, 0), "aralik gecersiz", id="negatif-start"),
    pytest.param(TermHit("GIZLIMETIN", "GIZLIHEDEF", 0, 10, None), "segment_index gecersiz", id="seg-None"),
    pytest.param(TermHit("GIZLIMETIN", "GIZLIHEDEF", 0, 10, -1), "aralik disi", id="seg--1"),
    pytest.param(TermHit("GIZLIMETIN", "GIZLIHEDEF", 0, 10, 1), "aralik disi", id="seg-len"),
    pytest.param(TermHit("GIZLIMETIN", "GIZLIHEDEF", 0, 10, True), "segment_index gecersiz", id="seg-bool"),  # type: ignore[arg-type]
    pytest.param(TermHit("GIZLIMETIN", "GIZLIHEDEF", 0, 10, 0.0), "segment_index gecersiz", id="seg-float"),  # type: ignore[arg-type]
    pytest.param(TermHit("GIZLIMETIN", "", 0, 10, 0), "target_term bos", id="bos-target"),
    pytest.param(TermHit("GIZLIMETIN", "GIZLIHEDEF", False, 10, 0), "int olmali", id="start-bool"),  # type: ignore[arg-type]
    pytest.param(TermHit("GIZLIMETIN", "GIZLIHEDEF", 0.0, 10, 0), "int olmali", id="start-float"),  # type: ignore[arg-type]
    pytest.param(TermHit(None, "GIZLIHEDEF", 0, 10, 0), "dilimiyle ayni degil", id="source-None"),  # type: ignore[arg-type]
    pytest.param(TermHit("GIZLIMETIN", None, 0, 10, 0), "target_term bos", id="target-None"),  # type: ignore[arg-type]
]


@pytest.mark.parametrize("hit, parca", KOTU_HITLER)
def test_a9_gecersiz_hit_contract_violation_mesaj_sizdirmaz(hit, parca):
    with pytest.raises(ContractViolation) as ei:
        terimleri_gom((GIZLI,), (hit,))
    m = str(ei.value)
    assert parca in m
    assert "GIZLI" not in m                          # metin/terim/hedef mesajda YOK


def test_a9_ortusen_hitler_cv_bitisik_serbest():
    with pytest.raises(ContractViolation) as ei:
        terimleri_gom((GIZLI,), (TermHit("GIZLIMETIN", "A", 0, 10, 0), TermHit("METIN kel", "B", 5, 14, 0)))
    assert "ortusuyor" in str(ei.value) and "GIZLI" not in str(ei.value)
    out = terimleri_gom((GIZLI,), (TermHit("GIZLI", "a", 0, 5, 0), TermHit("METIN", "b", 5, 10, 0)))
    assert out[0].text == "AB kelimesi burada"      # bitisik + ilk harf buyuk


def test_a9_hit_ve_segment_tipi_cv_sizdirmaz():
    with pytest.raises(ContractViolation) as ei:
        terimleri_gom((GIZLI,), ("GIZLITERIM",))  # type: ignore[arg-type]
    assert "GIZLI" not in str(ei.value)
    with pytest.raises(ContractViolation) as ei2:
        terimleri_gom(("GIZLIMETIN",), (TermHit("GIZLIMETIN", "X", 0, 10, 0),))  # type: ignore[arg-type]
    assert "GIZLI" not in str(ei2.value)
    st = sozluk(("ab", "X"))
    with pytest.raises(ContractViolation) as ei3:
        st.lookup_segments(("GIZLIMETIN",))  # type: ignore[arg-type]
    assert "GIZLI" not in str(ei3.value)


def test_bulgu_a9_segments_bozuk_hits_bos_denetimsiz_aynen():
    """BILGI: `hits` bosken segments hic denetlenmez (docstring: bos hits -> ayni nesne); str/int oge aynen doner."""
    out = terimleri_gom(("GIZLIMETIN", 5), ())  # type: ignore[arg-type]
    assert out == ("GIZLIMETIN", 5)


def test_a9_bir_hit_gecersizse_butun_cagri_duser():
    s0, s1 = seg("Marcus geldi"), seg("x")
    iyi = TermHit("Marcus", "Marcus", 0, 6, 0)
    kotu = TermHit("x", "Y", 0, 1, 5)
    with pytest.raises(ContractViolation):
        terimleri_gom((s0, s1), (iyi, kotu))
    assert terimleri_gom((s0, s1), (iyi,))[0].text == "Marcus geldi"   # pozitif kontrol


# ---------------------------------------------------------------------------
# A10 -- K5 saflik / kanal / determinizm
# ---------------------------------------------------------------------------


def test_a10_hic_bir_kanala_yazmaz(capfd, caplog):
    caplog.set_level(logging.DEBUG)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        st = sozluk(("マルクス", "Marcus"), ("Marcus", "Marcus"))
        for _ in range(3):
            st.lookup("長老マルクスが Marcus 방앗간을", ("{0}",))
            terimleri_gom((seg("長老マルクスが Marcus"),), tuple(dataclasses.replace(h, segment_index=0) for h in st.lookup("長老マルクスが Marcus")))
        repr(st); str(st); len(st); st.terimler; st.yol
        for hit, _ in [(p.values[0], p.values[1]) for p in KOTU_HITLER[:5]]:
            with pytest.raises(ContractViolation):
                terimleri_gom((GIZLI,), (hit,))
        with pytest.raises(ValueError):
            sozluk_ham({"terimler": [{"kaynak": "x", "hedef": "Y"}]})
        with pytest.raises(FileNotFoundError):
            GlossaryStore(Path("yok.json"))
    out, err = capfd.readouterr()
    assert out == "" and err == ""
    assert caplog.records == []
    assert w == []
    assert "src.translate.sozluk" not in logging.Logger.manager.loggerDict


def test_a10_repr_terim_basmaz_dosya_silinince_lookup_calisir():
    st = sozluk(("GIZLITERIM", "GIZLIHEDEF"))
    assert "GIZLI" not in repr(st) and "terim_sayisi=1" in repr(st)
    Path(st.yol).unlink()
    assert not Path(st.yol).exists()
    assert araliklar(st.lookup("GIZLITERIM geldi")) == [(0, 10)]


def test_a10_determinizm_yeni_liste_girdi_degismez():
    st = sozluk(("Marcus", "Marcus"), ("PLAYER", "Oyuncu"))
    a, b = st.lookup("Marcus PLAYER"), st.lookup("Marcus PLAYER")
    assert a == b and a is not b
    segs = (seg("Marcus PLAYER", ("{0}",), speaker="NPC"),)
    hits = st.lookup_segments(segs)
    out = terimleri_gom(segs, hits)
    assert segs[0].text == "Marcus PLAYER" and out[0].text == "Marcus Oyuncu"
    assert out[0].speaker == "NPC" and out[0].placeholders == ("{0}",) and out[0].source_blocks == (0,)


# ---------------------------------------------------------------------------
# B -- komsu-terim kurali Latin'de: docstring 'windmill eslesmez' KOSULLU
# ---------------------------------------------------------------------------


def test_b1_windmill_yalniz_mill_sozlukteyken_eslesmez():
    st = sozluk(("mill", "Değirmen"))
    assert st.lookup("windmill") == [] and st.lookup("windmills") == []
    assert araliklar(st.lookup("wind mill")) == [(5, 9)]


def test_bulgu_b1_windmill_wind_de_sozlukteyken_iki_hit_bilesik_bolunur():
    """ORTA: 'sozlukteki baska terimin baslangici/bitisi sinirdir' kurali Latin'de de aktif ->
    `windmill` -> `RüzgarDeğirmen`, `elderly` (elder+ly) -> `İhtiyarLy`. Docstring `windmill`i
    kosulsuz 'sinir olmayan' ornegi verir; iddia sozluk icerigine bagli."""
    st = sozluk(("mill", "Değirmen"), ("wind", "Rüzgar"))
    assert araliklar(st.lookup("windmill")) == [(0, 4), (4, 8)]
    assert gom1(st, "The windmill is old.") == "The RüzgarDeğirmen is old."
    st2 = sozluk(("elder", "İhtiyar"), ("ly", "Ly"))
    assert gom1(st2, "elderly") == "İhtiyarLy"


def test_bulgu_b1_windmills_komsu_reddedilse_de_sinir_verir_kismi_kelime_gomulur():
    """ORTA (Y1/G5 sinifi, Latin): `windmills`te `mill` adayi (sagi `s`) REDDEDILIR ama baslangici
    `wind`e sag sinir verir -> yalniz `wind` gomulur: `Rüzgarmills`. Docstring 'komsu terimin kabul
    edilmesi gerekmez' der (マルクス長老 icin dogru), Latin'de kelime parcasi degisir."""
    st = sozluk(("mill", "Değirmen"), ("wind", "Rüzgar"))
    h = st.lookup("windmills")
    assert araliklar(h) == [(0, 4)] and h[0].source_term == "wind"
    assert gom1(st, "The windmills turn.") == "The Rüzgarmills turn."


def test_bulgu_b1_alt_cizgi_pc_noktalama_sinirdir():
    """DUSUK/bilgi: `_` kategori Pc -> docstring `P*` sinir; `mill_house` -> `Değirmen_house` (tanimlayici gorunumlu metin)."""
    st = sozluk(("mill", "Değirmen"))
    assert araliklar(st.lookup("mill_house")) == [(0, 4)]
    assert st.lookup("millhouse") == []


def test_b1_kr_bilesik_negatifi_korunur_ikinci_parca_sozlukteyse_ikiye_bolunur():
    st1 = sozluk(("방앗간", "Değirmen"))
    assert st1.lookup("방앗간집주인") == []                 # G5 negatifi
    st2 = sozluk(("방앗간", "Değirmen"), ("집주인", "EvSahibi"))
    assert araliklar(st2.lookup("방앗간집주인")) == [(0, 3), (3, 6)]   # G6 EK KURAL (tasarim niyeti)


# ---------------------------------------------------------------------------
# C -- trie dal ayrismasi: coklu-kodpoint casefold (ß/ẞ, Yunan iota-subscript)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("sira", [0, 1])
def test_bulgu_c1_eszett_dal_ayrismasi_aday_kumesi_tam_degil_json_sirasina_bagli(sira):
    """ORTA (dar sinif, olculdu): `_trie_anahtari` casefold'u coklu kodpoint uretince karakteri oldugu gibi
    birakir -> `ß` ve `ẞ` (re.I DENK) ayri dallara duser. Alternation ILK dalda kisa terminalde durur, uzun
    terim ikinci dalda kacar: {Maßen, Maẞer, Maße} sozlugunde metinde HARFIYEN gecen 'Maẞer' eslesmez;
    JSON sirasi tersken eslesir. Docstring K1/2 'aday kumesi TAMDIR' ve K1/3 'JSON sirasi sonucu
    degistirmez' iddialari bu sinifta kirilir. Urun dilleri (JP/KR/EN) icin erisilemez."""
    ciftler = [("Maßen", "Massen"), ("Maẞer", "Masser"), ("Maße", "Masse")]
    if sira:
        ciftler[0], ciftler[1] = ciftler[1], ciftler[0]
    st = sozluk(*ciftler)
    h = st.lookup("Maẞer geht")
    if sira == 0:
        assert h == []                                  # BULGU: harfiyen gecen terim kacti
    else:
        assert [(x.start, x.end, x.target_term) for x in h] == [(0, 5, "Masser")]
    # pozitif kontroller (iki sirada da): ilk daldaki terimler eslesir
    assert araliklar(st.lookup("Maßen geht")) == [(0, 5)]
    assert araliklar(st.lookup("Maße geht")) == [(0, 4)]


def test_c1_tek_kodpoint_casefold_ayni_dal_marcus_aurelius():
    """Docstring'in kendi ornegi: `Marcus` / `marcus aurelius` ayni dalda, uzun terim kacmaz."""
    st = sozluk(("Marcus", "M"), ("marcus aurelius", "MA"))
    h = st.lookup("MARCUS AURELIUS x")
    assert [(x.start, x.end, x.target_term) for x in h] == [(0, 15, "MA")]


def test_bulgu_c1_yunan_iota_subscript_ayni_sinif():
    """Ayni mekanizma: ᾈ (U+1F88) ~ ᾀ (U+1F80) re.I denk, casefold 2 kodpoint -> ayri dal; 'ᾀβδ' harfiyen gecerken kacar."""
    assert re.fullmatch("ᾈ", "ᾀ", re.I)
    st = sozluk(("ᾈβγ", "A"), ("ᾀβδ", "B"), ("ᾈβ", "C"))
    assert st.lookup("ᾀβδ x") == []                    # BULGU
    assert araliklar(st.lookup("ᾀβγ x")) == [(0, 3)]   # pozitif kontrol


def test_c2_regex_ozel_ilk_karakterli_terimler_kacmaz():
    st = sozluk(("]x", "A"), ("^x", "B"), ("-x", "C"), ("\\x", "D"), ("[x", "E"), (".x", "F"), ("|x", "G"), ("(x", "H"))
    for metin, hedef in [("]x", "A"), ("^x", "B"), ("-x", "C"), ("\\x", "D"), ("[x", "E"), (".x", "F"), ("|x", "G"), ("(x", "H")]:
        h = st.lookup(metin)
        assert araliklar(h) == [(0, 2)] and h[0].target_term == hedef, metin
    assert st.lookup("ax") == [] and st.lookup("yx") == []


def test_c3_yer_tutucu_ortusmesiz_tarama_ve_bos_metin():
    st = sozluk(("aab", "X"))
    assert st.lookup("aaab", ("aa",)) == []           # korunan [0,2) ile [1,4) ortusur
    assert araliklar(st.lookup(" aab")) == [(1, 4)]
    assert st.lookup("") == [] and st.lookup("   ") == [] and st.lookup("...") == []
    assert st.lookup("{0}", ("{0}",)) == []


def test_c4_jp_komsu_terim_reddedilse_de_sinir_verir_bilesik_parcalanir():
    """B1'in JP karsiligi (docstring 'her betikte ayni'): {水車, 小屋} sozlugunde `水車小屋町` -> `水車` gomulur
    (`小屋` adayi `町` yuzunden reddedilir ama baslangici sinir verir)."""
    st = sozluk(("水車", "SuArabasi"), ("小屋", "Kulube"))
    h = st.lookup("水車小屋町")
    assert araliklar(h) == [(0, 2)]
    assert gom1(st, "水車小屋町") == "SuArabasi小屋町"
    assert araliklar(st.lookup("水車小屋")) == [(0, 2), (2, 4)]     # pozitif: tam bilesik iki hit
