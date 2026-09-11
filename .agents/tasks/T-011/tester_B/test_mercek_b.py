"""TESTER-B (T-011) -- mercek: KOTU KULLANIM + SARTNAME UYUMU.

Kor yazildi: `delivery.md`, `evidence/`, `sef_dogrulama/`, `test_sozluk.py` acilmadan.
Paket: `.agents/tasks/T-011/packet.md` surum 2 (K1-K7). Kod: `src/translate/sozluk.py`.

TUR 2 (paket v3, fixture v3, kod v3): 92 kosumun 30'u dustu; her biri yeniden nisanlandi ve `TUR-2 (x)` ile isaretlendi:
  (a) duzeltilen bulgu pin'i -> v3 beklentisi (8): b3 kaynak terminator, b6 reddedilen komsu x4, b6 NFD yer tutucu, b8 CV x2
  (b) v3 kuraliyla degisen eski davranis (17): b6 kimlik cipasi, b7 JP 17, b7 KR 21, b7 sembol x14
  (c) fixture v3 (7 terim, unvansiz) (4): b1 list/tuple, b6 NFD indeks (`mill` yok), bx repr 11->7, bk kapi yolu 10->6
  (d) `マルクス。` test verisi (1): b9 sema serbest listesi
Tur-2'nin yeni testleri `test_mercek_b_tur2.py` icinde.

Kos:
    python -m pytest .agents/tasks/T-011/tester_B -q -p no:cacheprovider --import-mode=importlib

Test adlari:
  test_b1_*  lookup -> terimleri_gom zinciri (segment_index unutma, lookup_segments denkligi, list/tuple/generator)
  test_b2_*  segment listesi kimligi (ayni nesne iki kez, bos metin, yalniz yer tutucu, speaker)
  test_b3_*  T-007 ile etkilesim (modelsiz: `cumlelere_bol`/`modele_gider`; kaynak terimde terminator; `{0}` metinken)
  test_b4_*  Y3 / yazarlik: sema kimlik gomme, hedef icinde kaynak (idempotens), kayit duzeyi anahtar
  test_b6_*  JSON kotu kullanim: kimlik gomme, idempotens, NFD yer tutucu kaymasi
  test_b7_*  sinir listesi: sembol `S*`, JP saygi eki, KR `에게/님` -- paket kapsamini OLCER (kacak sinifi)
  test_b8_*  hata siniflari: TypeError vs ContractViolation; numpy int indeks
  test_b9_*  sartname satir satir: K1..K7 paketin ornekleri + uydurulmus davranis (bas/son bosluk, ek zinciri)
  test_bx_*  belge (docstring) iddialari -- tutuyorsa gecer, ayrisirsa XFAIL(strict) ile haber verir
"""
from __future__ import annotations

import dataclasses
import json
import random
import unicodedata
from pathlib import Path

import numpy as np
import pytest

from src.contracts.errors import ContractViolation, TranslatorError
from src.contracts.models import Rect, Segment, TermHit
from src.translate.local_nmt import cumlelere_bol, modele_gider
from src.translate.sozluk import GlossaryStore, ilk_harfi_buyut, terimleri_gom

KOK = Path(__file__).resolve().parents[4]
FIXTURE = KOK / ".agents" / "tasks" / "T-011" / "fixtures" / "sozluk_ornek.json"
R = Rect(0, 0, 100, 20)


def seg(text: str, ph: tuple[str, ...] = (), speaker: str | None = None) -> Segment:
    return Segment(text=text, bbox=R, placeholders=ph, speaker=speaker)


def sozluk(tmp_path: Path, terimler: list[dict[str, object]], ad: str = "s.json", **ust: object) -> GlossaryStore:
    p = tmp_path / ad
    p.write_text(json.dumps({**ust, "terimler": terimler}, ensure_ascii=False), encoding="utf-8")
    return GlossaryStore(p)


@pytest.fixture(scope="module")
def s() -> GlossaryStore:
    return GlossaryStore(FIXTURE)


# ---------------------------------------------------------------------------
# B1 -- lookup -> terimleri_gom zinciri
# ---------------------------------------------------------------------------


def test_b1_segment_index_unutulursa_contract_violation_ve_mesaj_yol_gosterir(s: GlossaryStore) -> None:
    """Paket K7: `None` -> ContractViolation. Mesaj hangi hit ve ne beklendigini soyler (sayi/tip; metin yok)."""
    sg = seg("長老マルクスが水車小屋で待っています。")
    hits = s.lookup(sg.text)
    assert hits and all(h.segment_index is None for h in hits)
    with pytest.raises(ContractViolation, match=r"hits\[0\]\.segment_index .*NoneType.*int.*\[0, 1\)") as ei:
        terimleri_gom((sg,), hits)
    assert isinstance(ei.value, TranslatorError)
    assert "マルクス" not in str(ei.value) and "Marcus" not in str(ei.value)


def test_b1_lookup_segments_ile_elle_replace_yolu_birebir_ayni_1000_rastgele(s: GlossaryStore) -> None:
    """Iki yolun ciktisi (hits VE gomulu segmentler) 1000 rastgele segment listesinde ayni; yer tutucular farkli."""
    rnd = random.Random(2011)
    havuz = ["長老", "マルクス", "水車小屋", "アイラ", "が", "を", "は", "に", "で", "。", " ", "村", "人", "{0}", "%s",
             "장로", " ", "마르쿠스", "방앗간", "을", "에서", "아일라", "Marcus", "mill", "elder", "MARCUS", "the", ".", ",",
             "Elder", "Mill", "{PLAYER}", "[Mill]", "　", "Değirmen", "İhtiyar"]
    toplam_hit = 0
    for _ in range(1000):
        segs = tuple(
            seg("".join(rnd.choice(havuz) for _ in range(rnd.randint(1, 12))),
                tuple(rnd.sample(["{0}", "%s", "{PLAYER}", "[Mill]"], rnd.randint(0, 3))))
            for _ in range(rnd.randint(1, 3))
        )
        a = s.lookup_segments(segs)
        b = tuple(dataclasses.replace(h, segment_index=i) for i, g in enumerate(segs) for h in s.lookup(g.text, g.placeholders))
        assert a == b
        assert terimleri_gom(segs, a) == terimleri_gom(list(segs), list(b))
        toplam_hit += len(a)
    assert toplam_hit > 2000  # pozitif kontrol: kume gercekten hit uretiyor


def test_b1_list_tuple_generator_girdi_ayni_cikti(s: GlossaryStore) -> None:
    sg = seg("長老マルクスが水車小屋で待っています。")
    beklenen = terimleri_gom((sg,), s.lookup_segments((sg,)))
    assert terimleri_gom([sg], s.lookup_segments([sg])) == beklenen
    assert terimleri_gom((x for x in [sg]), s.lookup_segments((x for x in [sg]))) == beklenen
    assert isinstance(terimleri_gom([sg], ()), tuple)
    assert beklenen[0].text == "長老MarcusがDeğirmenで待っています。"  # TUR-2 (c): fixture v3 unvansiz


def test_b1_girdi_listesi_degistirilmez(s: GlossaryStore) -> None:
    sg = seg("マルクスが来た。")
    liste = [sg]
    hits = list(s.lookup_segments(liste))
    kopya_l, kopya_h = list(liste), list(hits)
    terimleri_gom(liste, hits)
    assert liste == kopya_l and hits == kopya_h and liste[0] is sg


# ---------------------------------------------------------------------------
# B2 -- segment listesi kimligi
# ---------------------------------------------------------------------------


def test_b2_ayni_segment_nesnesi_iki_kez_ikisi_de_gomulur_hitsiz_olan_is_kalir(s: GlossaryStore) -> None:
    a = seg("マルクスが来た。")
    b = seg("こんにちは。")
    hits = s.lookup_segments((a, b, a))
    assert [h.segment_index for h in hits] == [0, 2]
    out = terimleri_gom((a, b, a), hits)
    assert out[0].text == out[2].text == "Marcusが来た。"
    assert out[1] is b  # hit'siz olan AYNI nesne (K2)
    assert out[0] is not a and out[2] is not a


@pytest.mark.parametrize("text,ph", [("", ()), ("{0}", ("{0}",)), ("{0}", ()), ("   ", ()), ("。", ()), ("{PLAYER}!", ("{PLAYER}",))])
def test_b2_bos_veya_yalniz_yer_tutucu_segment_hit_yok_ve_is(s: GlossaryStore, text: str, ph: tuple[str, ...]) -> None:
    sg = seg(text, ph)
    hits = s.lookup_segments((sg,))
    assert hits == ()
    assert terimleri_gom((sg,), hits)[0] is sg


def test_b2_speaker_icindeki_terim_gomulmez_ve_speaker_aynen(s: GlossaryStore) -> None:
    """Paket K2: `speaker` dokunulmaz; lookup_segments yalniz `text`i tarar."""
    sg = seg("はい。", speaker="マルクス")
    assert s.lookup_segments((sg,)) == ()
    sg2 = seg("マルクスが来た。", speaker="長老")
    out = terimleri_gom((sg2,), s.lookup_segments((sg2,)))
    assert out[0].speaker == "長老" and out[0].text == "Marcusが来た。"


# ---------------------------------------------------------------------------
# B3 -- T-007 etkilesimi (modelsiz)
# ---------------------------------------------------------------------------


def test_b3_gomme_modele_gider_kararini_degistirmez_fixture_cumleleri(s: GlossaryStore) -> None:
    """Gomulu terim Latin harf icerir ama kaynak parca zaten harf iceriyordu -> T-007 bypass'i degismez."""
    cumleler = ["長老マルクス", "マルクスがあなたを待っています。", "水車小屋を過ぎて東の道を行きなさい。", "장로 마르쿠스",
                "방앗간을 지나 동쪽 길로 가십시오.", "The elder Marcus waits by the mill.", "{0}マルクスは村にいます。", "マルクス。"]
    for c in cumleler:
        sg = seg(c, ("{0}",) if "{0}" in c else ())
        g = terimleri_gom((sg,), s.lookup_segments((sg,)))[0]
        once = [modele_gider(p, sg.placeholders) for p in cumlelere_bol(sg.text)]
        sonra = [modele_gider(p, g.placeholders) for p in cumlelere_bol(g.text)]
        assert once == sonra, c
        assert len(cumlelere_bol(sg.text)) == len(cumlelere_bol(g.text)), c


def test_b3_fixture_hedefleri_terminator_icermez_parca_sayisi_korunur(s: GlossaryStore) -> None:
    for t in s.terimler:
        assert not any(ch in ".!?。！？" for ch in t.hedef)
        assert len(cumlelere_bol(f"A {t.hedef} B。")) == 1


def test_b3_kaynak_terimde_terminator_sema_kabul_eder_ve_gomme_cumle_sinirini_yutar(tmp_path: Path) -> None:
    """TUR-2 (a)+(d): O-B1 duzeltildi -- kaynak `マルクス。` artik SEMADA reddedilir (K6 v3, mesajda terim ve sinif); tur 1'de
    kabul edilip gomme cumle sinirini yutuyordu (gercek modelde ikinci cumle kayip). Pozitif kontrol: terminatorsuz kaynakla
    ayni cumle 2 parca -> 2 parca kalir."""
    with pytest.raises(ValueError, match="kaynak cumle sonu") as ei:
        sozluk(tmp_path, [{"kaynak": "マルクス。", "hedef": "Marcus"}])
    assert "マルクス。" in str(ei.value)
    s2 = sozluk(tmp_path, [{"kaynak": "マルクス", "hedef": "Marcus"}])
    sg = seg("彼はマルクス。 行こう。")
    g = terimleri_gom((sg,), s2.lookup_segments((sg,)))[0]
    assert g.text == "彼はMarcus。 行こう。" and len(cumlelere_bol(sg.text)) == len(cumlelere_bol(g.text)) == 2


def test_b3_yer_tutucu_bildirilmemisse_icindeki_rakam_terim_olur(tmp_path: Path) -> None:
    """K3 ilkesi (belgeli): `placeholders=()` iken `{0}` metindir; `0`->`Sıfır` (izinli kisa terim) `{0}`in icini gomer.
    Bildirilirse korunur (pozitif kontrol). Cagiran yer tutucuyu bildirmek ZORUNDA."""
    s0 = sozluk(tmp_path, [{"kaynak": "0", "hedef": "Sıfır", "kisa_terim_izni": True}, {"kaynak": "マルクス", "hedef": "Marcus"}])
    sg = seg("{0}マルクスは村にいます。", ())
    g = terimleri_gom((sg,), s0.lookup_segments((sg,)))[0]
    assert g.text == "{Sıfır}Marcusは村にいます。"
    sg2 = seg("{0}マルクスは村にいます。", ("{0}",))
    g2 = terimleri_gom((sg2,), s0.lookup_segments((sg2,)))[0]
    assert g2.text == "{0}Marcusは村にいます。"


# ---------------------------------------------------------------------------
# B4 / B6 -- JSON kotu kullanim: kimlik gomme, idempotens, NFD yer tutucu
# ---------------------------------------------------------------------------


def test_b6_kimlik_gomme_hit_uretir_metin_ayni_nesne_yeni(s: GlossaryStore) -> None:
    """Fixture `Marcus -> Marcus`: JP metinde Latin `Marcus` hit uretir, gom metni degistirmez ama KOPYA doner.
    Sayac/istatistik icin: `len(hits)` 'gomme sayisi' DEGIL. ContractViolation yok, kayma yok."""
    sg = seg("Marcusが待っています。")
    hits = s.lookup_segments((sg,))
    assert len(hits) == 1 and hits[0].source_term == hits[0].target_term == "Marcus"
    out = terimleri_gom((sg,), hits)
    assert out[0].text == sg.text and out[0] == sg and out[0] is not sg


def test_b6_kimlik_terim_komsu_sinir_cipasi_olarak_ise_yarar(tmp_path: Path) -> None:
    """TUR-2 (b)+(c): v3'te betik gecisi (Han|Latin) sinirdir -- kimlik cipasi `Marcus->Marcus` GEREKMEZ (tur 1'de gerekiyordu).
    Fixture v3 unvansiz; yerel sozlukle: cipasiz `長老Marcus` -> `長老` eslesir; cipali -> ikisi de."""
    st = sozluk(tmp_path, [{"kaynak": "長老", "hedef": "İhtiyar"}])
    assert [h.target_term for h in st.lookup("長老Marcus")] == ["İhtiyar"]
    st2 = sozluk(tmp_path, [{"kaynak": "長老", "hedef": "İhtiyar"}, {"kaynak": "Marcus", "hedef": "Marcus"}], ad="s2.json")
    assert [h.target_term for h in st2.lookup("長老Marcus")] == ["İhtiyar", "Marcus"]


@pytest.mark.parametrize("metin,beklenen", [
    ("長老Marcusa", ["İhtiyar"]),                  # `Marcus` adayi olu (sag `a`); `長老` BETIK GECISIYLE (Han|Latin) eslesir
    ("長老マルクス様", ["İhtiyar", "Marcus"]),      # tur 1: yalniz unvan (kismi gomme); v3: `様` Katakana|Han sinir -> ikisi
    ("장로마르쿠스님", ["İhtiyar", "Marcus"]),      # Hangul|Hangul: ZINCIR, dis uclar (bas, `님` eki) sinir -> ikisi
    ("水車小屋マルクス様", ["Değirmen", "Marcus"]),
    ("장로마르쿠스니", []),                          # dis uc sinir degil -> zincirin HICBIR uyesi (reddedilen aday sinir vermez)
])
def test_b6_reddedilen_komsu_aday_da_sinirdir_kismi_gomme(tmp_path: Path, metin: str, beklenen: list[str]) -> None:
    """TUR-2 (a): O-B5 duzeltildi -- v3 ZINCIR kurali: reddedilen aday komsuya sinir VERMEZ; zincir ancak iki dis ucu gercek
    sinirsa butunuyle eslesir. Tur 1'in kismi gommesi (`İhtiyarマルクス様`) kayboldu. Fixture v3 unvansiz -> yerel sozluk."""
    st = sozluk(tmp_path, [{"kaynak": "長老", "hedef": "İhtiyar"}, {"kaynak": "장로", "hedef": "İhtiyar"}, {"kaynak": "マルクス", "hedef": "Marcus"},
                           {"kaynak": "마르쿠스", "hedef": "Marcus"}, {"kaynak": "水車小屋", "hedef": "Değirmen"}, {"kaynak": "Marcus", "hedef": "Marcus"}])
    assert [h.target_term for h in st.lookup(metin)] == beklenen


def test_b6_hedef_kaynagi_iceriyorsa_gomme_idempotent_degil_ve_sema_kabul_eder(tmp_path: Path) -> None:
    """KOTU KULLANIM (orta): `mill -> Değirmen mill` semada kabul; gom ciktisi tekrar lookup+gom'a verilirse her turda
    bir `Değirmen` daha eklenir (pipeline degisim tespitiyle ayni segmenti iki kez isleyebilir)."""
    s4 = sozluk(tmp_path, [{"kaynak": "mill", "hedef": "Değirmen mill"}])
    sg = seg("by the mill.")
    for i in range(1, 4):
        sg = terimleri_gom((sg,), s4.lookup_segments((sg,)))[0]
        assert sg.text == "by the " + "Değirmen " * i + "mill."


def test_b6_fixture_ile_gomme_idempotent(s: GlossaryStore) -> None:
    """Fixture sozlugunde (hedef kaynagi icermez) ikinci tur lookup+gom metni degistirmez."""
    for c in ["長老マルクスが水車小屋で待っています。", "The elder Marcus waits by the mill.", "장로 마르쿠스가 방앗간에서 아일라를 만났습니다."]:
        g1 = terimleri_gom((seg(c),), s.lookup_segments((seg(c),)))
        g2 = terimleri_gom(g1, s.lookup_segments(g1))
        assert g2[0].text == g1[0].text


def test_b6_nfd_yer_tutucu_gom_sonrasi_metnin_alt_dizesi_degil_t007_onarimi_kopya_ekler(s: GlossaryStore) -> None:
    """TUR-2 (a): O-B2 duzeltildi -- K2 v3 hit'i olan segmentte `placeholders` da NFC; yer tutucu ciktida alt dize KALIR,
    T-007 K5 onarimi kopya EKLEMEZ. Hit'siz NFD segment aynen (`is`, normalize edilmez) -- bu kisim degismedi."""
    nfd = unicodedata.normalize("NFD", "{Değirmen}")
    nfc = unicodedata.normalize("NFC", nfd)
    sg = seg(nfd + "はマルクスの家です。", (nfd,))
    assert sg.placeholders[0] in sg.text  # girdi tutarli
    g = terimleri_gom((sg,), s.lookup_segments((sg,)))[0]
    assert unicodedata.is_normalized("NFC", g.text)
    assert g.placeholders == (nfc,)
    assert g.placeholders[0] in g.text  # tutarlilik korundu
    assert modele_gider(cumlelere_bol(g.text)[0], g.placeholders) is True
    from src.translate.local_nmt import _yer_tutuculari_onar

    cikti = nfc + " Marcus evi"
    assert _yer_tutuculari_onar(cikti, g.text, g.placeholders) == cikti  # kopya YOK
    # pozitif kontrol: NFC yer tutucu ile tutarlilik korunur
    nfc = unicodedata.normalize("NFC", nfd)
    sg2 = seg(nfc + "はマルクスの家です。", (nfc,))
    g2 = terimleri_gom((sg2,), s.lookup_segments((sg2,)))[0]
    assert g2.placeholders[0] in g2.text
    # hit'siz NFD segment NFD kalir
    sg3 = seg(unicodedata.normalize("NFD", "Değirmen yok."))
    assert terimleri_gom((sg3,), s.lookup_segments((sg3,)))[0] is sg3


def test_b6_hit_indeksleri_nfc_metne_gore_nfd_segment_text_ile_kayar(s: GlossaryStore) -> None:
    """UI tuzagi: `Segment.text` NFD ise `TermHit.start/end` orijinal metne uymaz (K1 belgeli: indeks NFC metne gore).
    Kaynak paneli vurgulayan sonraki ajan once NFC'lemek zorunda."""
    nfd = unicodedata.normalize("NFD", "Değirmen ") + "Marcus."  # TUR-2 (c): fixture v3'te `mill` yok, `Marcus` kimlik
    sg = seg(nfd)
    hits = s.lookup_segments((sg,))
    assert len(hits) == 1
    h = hits[0]
    assert sg.text[h.start:h.end] != h.source_term  # NFD orijinalde kayik
    assert unicodedata.normalize("NFC", sg.text)[h.start:h.end] == h.source_term


# ---------------------------------------------------------------------------
# B7 -- sinir listesi kapsami (paket vs oyun metni) -- OLCUM, kacak sinifi
# ---------------------------------------------------------------------------

JP_SAYGI_EKI = ["マルクスさん", "マルクス様", "マルクス殿", "マルクス君", "マルクスちゃん", "マルクス達", "マルクスたち",
                "マルクスって", "マルクスだ", "マルクスじゃない", "マルクスなら", "マルクスから", "マルクスまで", "マルクスより",
                "マルクスか", "マルクスよ", "マルクスね"]
KR_EK_DISI = ["마르쿠스님", "마르쿠스씨", "마르쿠스야", "마르쿠스아", "마르쿠스에게", "마르쿠스한테", "마르쿠스께", "마르쿠스랑",
              "마르쿠스처럼", "마르쿠스보다", "마르쿠스마다", "마르쿠스밖에", "마르쿠스조차", "마르쿠스들", "마르쿠스라고",
              "마르쿠스라면", "마르쿠스인가", "장로님", "장로에게", "방앗간이다", "방앗간입니다"]


def test_b7_jp_saygi_eki_ve_kopula_sinir_degil_17_17_kacak(s: GlossaryStore) -> None:
    """TUR-2 (b): Y-B2 kapandi -- 17/17 ESLESIYOR: 15'i K1 v3 saygi/kopula listesinden, `じゃない`/`なら` (listede yok) BETIK
    GECISIYLE (Katakana|Hiragana). Tur 1: 17/17 kacak. Gercek model (real_check #5b): 'Marcus' korunuyor."""
    kacak = [t for t in JP_SAYGI_EKI if not s.lookup(t)]
    assert kacak == [] and len(JP_SAYGI_EKI) == 17
    # pozitif kontrol: paketin parcaciklari eslesir
    assert all(s.lookup("マルクス" + p) for p in "をがはにのでともへや")


def test_b7_kr_ek_listesi_disi_ekler_sinir_degil_21_21_kacak(s: GlossaryStore, tmp_path: Path) -> None:
    """TUR-2 (b)+(c): Y-B2 kapandi -- 21 girdinin 20'si ESLESIYOR (K1 v3 KR listesi); tek kacak `마르쿠스인가` (`인가` listede
    yok, belgeli). `장로님`/`장로에게` fixture v3'te unvan olmadigi icin yerel sozlukle olculur (c)."""
    kacak = [t for t in KR_EK_DISI if not s.lookup(t) and "장로" not in t]
    assert kacak == ["마르쿠스인가"]
    st = sozluk(tmp_path, [{"kaynak": "장로", "hedef": "İhtiyar"}])
    assert st.lookup("장로님") and st.lookup("장로에게")
    assert all(s.lookup("마르쿠스" + ek) for ek in ("을", "를", "이", "가", "은", "는", "에", "에서", "으로", "로", "와", "과", "도", "의", "만", "께서", "부터", "까지"))


@pytest.mark.parametrize("sym", ["♪", "～", "♥", "☆", "→", "＋", "♡", "★", "♫", "©", "™", "°", "＄", "￥"])
def test_b7_sembol_kategorisi_sinir_degil_hit_duser(s: GlossaryStore, sym: str) -> None:
    """TUR-2 (b): D-B1 CJK tarafinda kapandi -- sembol (`S*`) DIGER sinifinda, CJK terime bitisik sembol BETIK GECISIYLE sinir:
    fixture v3'un 5 cumlesi (5 hit; unvansiz) sonek/onek sembolle 5/5 kalir; `マルクス～` 1. Latin terimde (`Marcus♪`) hala 0
    (belgeli asimetri; `test_t3_sembol_asimetrisi_*`)."""
    assert unicodedata.category(sym).startswith("S")
    base = ["長老マルクス", "マルクスがあなたを待っています。", "水車小屋を過ぎて東の道を行きなさい。", "장로 마르쿠스", "방앗간을 지나 동쪽 길로 가십시오."]
    assert sum(len(s.lookup(t)) for t in base) == 5
    assert sum(len(s.lookup(t.rstrip("。") + sym)) for t in base) == 5
    assert sum(len(s.lookup(sym + t)) for t in base) == 5
    assert len(s.lookup("マルクス" + sym)) == 1 and len(s.lookup("マルクス〜")) == 1 and len(s.lookup("Marcus" + sym)) == 0


# ---------------------------------------------------------------------------
# B8 -- hata siniflari
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("cagri,ad", [
    (lambda s: s.lookup("マルクス", "{0}"), "lookup duz str placeholders"),
    (lambda s: s.lookup("マルクス", [1]), "lookup int oge"),
    (lambda s: s.lookup(5), "lookup int text"),
    (lambda s: GlossaryStore(None), "GlossaryStore(None)"),  # type: ignore[arg-type]
])
def test_b8_typeerror_siniflari_translatorerror_degil_pipeline_yakalamaz(s: GlossaryStore, cagri: object, ad: str) -> None:
    """TUR-2 (a): O-B4 duzeltildi -- DOGRUDAN `lookup(text, placeholders)` / `GlossaryStore(None)` programci hatasi olarak
    `TypeError` KALIR (paket v3 K2 izin verir); Segment'ten turetilen bicim hatalari artik `ContractViolation` (asagida)."""
    with pytest.raises(TypeError) as ei:
        cagri(s)  # type: ignore[operator]
    assert not isinstance(ei.value, TranslatorError), ad


@pytest.mark.parametrize("cagri,ad", [
    (lambda s: s.lookup_segments((Segment(text="マルクス", bbox=R, placeholders="{0}"),)), "lookup_segments Segment.placeholders str"),  # type: ignore[arg-type]
    (lambda s: terimleri_gom((Segment(text="マルクス", bbox=R, placeholders="{0}"),), (TermHit("マルクス", "Marcus", 0, 4, 0),)), "gom Segment.placeholders str"),  # type: ignore[arg-type]
])
def test_b8_segment_kaynakli_bicim_hatasi_contract_violation_pipeline_yakalar(s: GlossaryStore, cagri: object, ad: str) -> None:
    """TUR-2 (a): O-B4 duzeltmesi -- `Segment(placeholders="{0}")` `lookup_segments` ve `terimleri_gom`da `ContractViolation`
    (`TranslatorError`; tasarim 5.6 `except TranslatorError` ve demo yakalar)."""
    with pytest.raises(ContractViolation) as ei:
        cagri(s)  # type: ignore[operator]
    assert isinstance(ei.value, TranslatorError), ad


def test_b8_t007_ayni_bozuk_segmenti_kabul_eder_sozluk_reddeder() -> None:
    """Karsilastirma: T-007 `translate`in placeholders denetimi `all(isinstance(yt, str) for yt in "{0}")` -> True."""
    bozuk = Segment(text="マルクス", bbox=R, placeholders="{0}")  # type: ignore[arg-type]
    assert all(isinstance(yt, str) for yt in bozuk.placeholders)  # T-007'nin denetimi gecer
    assert modele_gider("マルクス", bozuk.placeholders) is True


@pytest.mark.parametrize("deger", [np.int64(0), np.int32(0)])
def test_b8_numpy_tamsayi_segment_index_reddedilir_contract_violation(s: GlossaryStore, deger: object) -> None:
    """K7 `isinstance(i, int)`: numpy tamsayi (OCR tarafi numpy uretir) `int` degil -> ContractViolation (sessiz degil,
    ama T-007 `threads` icin `numbers.Integral` kabul eder; tutarsizlik, dusuk)."""
    sg = seg("マルクスが来た。")
    h = dataclasses.replace(s.lookup(sg.text)[0], segment_index=deger)  # type: ignore[arg-type]
    with pytest.raises(ContractViolation, match="segment_index gecersiz"):
        terimleri_gom((sg,), (h,))


def test_b8_dosya_yok_filenotfounderror_sarilmaz(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        GlossaryStore(tmp_path / "yok.json")


def test_b8_bozuk_json_valueerror_dosya_adi_mesajda(tmp_path: Path) -> None:
    p = tmp_path / "bozuk.json"
    p.write_bytes(b"{")
    with pytest.raises(ValueError, match="bozuk.json"):
        GlossaryStore(p)


# ---------------------------------------------------------------------------
# B9 -- sartname satir satir (paketin kendi ornekleri) + uydurulmus davranis
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("metin", ["村人", "剣士", "검사", "방앗간집", "검은 옷", "真剣に", "中村"])
def test_b9_k1_paket_negatifleri_eslesmez(tmp_path: Path, metin: str) -> None:
    st = sozluk(tmp_path, [{"kaynak": "村", "hedef": "Köy", "kisa_terim_izni": True}, {"kaynak": "剣", "hedef": "Kılıç", "kisa_terim_izni": True},
                           {"kaynak": "검", "hedef": "Kılıç", "kisa_terim_izni": True}, {"kaynak": "방앗간", "hedef": "Değirmen"},
                           {"kaynak": "マルクス", "hedef": "Marcus"}, {"kaynak": "장로", "hedef": "İhtiyar"}, {"kaynak": "長老", "hedef": "İhtiyar"}])
    if metin == "검은 옷":
        pytest.xfail("paketin belgeli bilinen siniri: `검`+ek `은` kuraldan gecer (K1)")
    assert st.lookup(metin) == []


@pytest.mark.parametrize("metin,n", [("村は", 1), ("剣を", 1), ("검을", 1), ("방앗간에서", 1), ("Marcusが", 1), ("장로 마르쿠스", 2), ("長老マルクス", 2)])
def test_b9_k1_paket_pozitifleri_eslesir(tmp_path: Path, metin: str, n: int) -> None:
    st = sozluk(tmp_path, [{"kaynak": "村", "hedef": "Köy", "kisa_terim_izni": True}, {"kaynak": "剣", "hedef": "Kılıç", "kisa_terim_izni": True},
                           {"kaynak": "검", "hedef": "Kılıç", "kisa_terim_izni": True}, {"kaynak": "방앗간", "hedef": "Değirmen"},
                           {"kaynak": "マルクス", "hedef": "Marcus"}, {"kaynak": "마르쿠스", "hedef": "Marcus"}, {"kaynak": "Marcus", "hedef": "Marcus"},
                           {"kaynak": "장로", "hedef": "İhtiyar"}, {"kaynak": "長老", "hedef": "İhtiyar"}])
    assert len(st.lookup(metin)) == n


def test_b9_k1_en_uzun_once_iki_sirali_sozluk(tmp_path: Path) -> None:
    for sira in ([{"kaynak": "水車小屋", "hedef": "Değirmen"}, {"kaynak": "水車", "hedef": "Çark"}],
                 [{"kaynak": "水車", "hedef": "Çark"}, {"kaynak": "水車小屋", "hedef": "Değirmen"}]):
        st = sozluk(tmp_path, sira)
        hits = st.lookup("水車小屋を過ぎて")
        assert [(h.source_term, h.start, h.end) for h in hits] == [("水車小屋", 0, 4)]


def test_b9_k1_buyuk_kucuk_duyarsiz_indeks_orijinal_metne_gore(s: GlossaryStore) -> None:
    metin = "The ﬁne İstanbul MARCUS and marcus."
    hits = s.lookup(metin)
    assert [(h.source_term, h.target_term) for h in hits] == [("MARCUS", "Marcus"), ("marcus", "Marcus")]
    for h in hits:
        assert metin[h.start:h.end] == h.source_term


def test_b9_k1_ayni_terim_n_gecis_start_artan(s: GlossaryStore) -> None:
    hits = s.lookup("マルクスとマルクスとマルクス")
    assert [h.start for h in hits] == [0, 5, 10] and len(hits) == 3


def test_b9_k2_paket_ornekleri(s: GlossaryStore) -> None:
    sg = seg("방앗간을 지나")
    assert terimleri_gom((sg,), s.lookup_segments((sg,)))[0].text == "Değirmen을 지나"
    sg2 = seg("マルクスは水車小屋", ("{0}",), speaker="A")
    out = terimleri_gom((sg2,), s.lookup_segments((sg2,)))[0]
    assert out.text == "Marcusは Değirmen".replace(" ", "") and out.placeholders == ("{0}",) and out.speaker == "A" and out.bbox == R
    with pytest.raises(ContractViolation):
        terimleri_gom((sg,), (TermHit("방앗간", "Değirmen", 1, 4, 0),))  # dilim tutarsiz
    with pytest.raises(ContractViolation):
        terimleri_gom((sg,), (TermHit("방앗간", "Değirmen", 0, 3, 0), TermHit("앗간", "X", 1, 3, 0)))  # ortusen
    assert terimleri_gom((sg,), ())[0] is sg


def test_b9_k3_paket_ornekleri(tmp_path: Path, s: GlossaryStore) -> None:
    st = sozluk(tmp_path, [{"kaynak": "PLAYER", "hedef": "Oyuncu"}])
    assert st.lookup("{PLAYER}は村にいます", ("{PLAYER}",)) == []
    assert len(st.lookup("{PLAYER}は村にいます", ())) == 1
    hits = s.lookup("{0}マルクス", ("{0}",))
    assert [(h.source_term, h.start) for h in hits] == [("マルクス", 3)]
    # gom: hit yer tutucuyla ortusuyorsa ContractViolation (dusurme degil)
    sg = seg("{PLAYER}は村にいます", ("{PLAYER}",))
    with pytest.raises(ContractViolation, match="yer tutucu"):
        terimleri_gom((sg,), (TermHit("PLAYER", "Oyuncu", 1, 7, 0),))


def test_b9_k4_ilk_harf_buyuk_ve_kenar_durumlar(tmp_path: Path) -> None:
    st = sozluk(tmp_path, [{"kaynak": "a1", "hedef": "değirmen"}, {"kaynak": "a2", "hedef": "marcus"}, {"kaynak": "a3", "hedef": "Marcus"},
                           {"kaynak": "a4", "hedef": "ihtiyar"}, {"kaynak": "a5", "hedef": "iPhone"}])
    hedefler = {t.kaynak: t.hedef for t in st.terimler}
    assert hedefler == {"a1": "Değirmen", "a2": "Marcus", "a3": "Marcus", "a4": "İhtiyar", "a5": "İPhone"}
    # elle kurulan hit de buyutulur
    sg = seg("a1 x")
    assert terimleri_gom((sg,), (TermHit("a1", "değirmen", 0, 2, 0),))[0].text == "Değirmen x"
    # ligatur/eszett: `upper()` genisler -- belgelenmemis kenar (dusuk)
    assert ilk_harfi_buyut("ﬁne") == "FIne" and ilk_harfi_buyut("ß") == "SS"


@pytest.mark.parametrize("kayit,parca", [
    ({"kaynak": "검", "hedef": "Kılıç"}, "검"),
    ({"kaynak": "村", "hedef": "Köy"}, "村"),
    ({"kaynak": "マルクス", "hedef": "St. Marcus"}, "cumle sonu"),
    ({"kaynak": "マルクス", "hedef": "{0}"}, "yer tutucu"),
    ({"kaynak": "", "hedef": "X"}, "bos"),
    ({"kaynak": "マルクス", "hedef": ""}, "bos"),
])
def test_b9_k6_sema_red_siniflari(tmp_path: Path, kayit: dict[str, object], parca: str) -> None:
    with pytest.raises(ValueError, match=parca):
        sozluk(tmp_path, [kayit])


def test_b9_k6_tekrar_kaynak_ve_kisa_izin_ve_nfd(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="tekrar"):
        sozluk(tmp_path, [{"kaynak": "Marcus", "hedef": "A"}, {"kaynak": "MARCUS", "hedef": "B"}])
    st = sozluk(tmp_path, [{"kaynak": "검", "hedef": "Kılıç", "kisa_terim_izni": True}])
    assert st.lookup("검을") and not st.lookup("검사가 왔습니다.")
    st2 = sozluk(tmp_path, [{"kaynak": unicodedata.normalize("NFD", "방앗간"), "hedef": "Değirmen"}], ad="çeviri.json")
    nfd_metin = unicodedata.normalize("NFD", "방앗간을 지나")
    g = terimleri_gom((seg(nfd_metin),), st2.lookup_segments((seg(nfd_metin),)))[0]
    assert g.text == "Değirmen을 지나"


def test_b9_k7_segment_index_araligi(s: GlossaryStore) -> None:
    sg = seg("マルクスが来た。")
    h = s.lookup(sg.text)[0]
    for i in (None, -1, 1, True):
        with pytest.raises(ContractViolation):
            terimleri_gom((sg,), (dataclasses.replace(h, segment_index=i),))  # type: ignore[arg-type]


def test_b9_uydurulmus_bas_son_bosluk_reddi_paket_yalniz_bos_der(tmp_path: Path) -> None:
    """UYDURULMUS (belgeli, dusuk): `" Marcus"` -> ValueError. Paket yalniz 'bos' der. UI editorunden gelen bosluk
    butun sozlugu yuklenmez kilar; kirpmak da bir secenekti."""
    with pytest.raises(ValueError, match="bas/son bosluk"):
        sozluk(tmp_path, [{"kaynak": "Marcus ", "hedef": "Marcus"}])
    with pytest.raises(ValueError, match="bas/son bosluk"):
        sozluk(tmp_path, [{"kaynak": "Marcus", "hedef": "Marcus\n"}])


def test_b9_uydurulmus_kayit_duzeyi_bilinmeyen_anahtar_reddi(tmp_path: Path) -> None:
    """UYDURULMUS (belgeli, dusuk-orta): kayit duzeyinde ek alan (`kategori`, `aktif`, `ozel_ad`) -> butun sozluk
    ValueError. UI sozluk editoru meta veri ekleyemez; ust duzeyde serbest."""
    with pytest.raises(ValueError, match="bilinmeyen anahtar"):
        sozluk(tmp_path, [{"kaynak": "マルクス", "hedef": "Marcus", "kategori": "ad"}])
    assert len(sozluk(tmp_path, [{"kaynak": "マルクス", "hedef": "Marcus"}], oyun="X", surum=2)) == 1


def test_b9_uydurulmus_kr_ek_zinciri_iki_derinlik(s: GlossaryStore) -> None:
    """UYDURULMUS (belgeli): paket 'ekten sonra da sinir' der; kod bunu ozyineli okur (2 ek). `방앗간에서는` eslesir (yararli);
    `방앗간은가`/`방앗간로가` gibi anlamsiz zincirler de eslesir (zararsiz). 3 ek eslesmez."""
    assert len(s.lookup("방앗간에서는")) == 1 and len(s.lookup("방앗간까지는.")) == 1
    assert len(s.lookup("방앗간은가")) == 1 and len(s.lookup("방앗간로가")) == 1
    assert s.lookup("방앗간에서는요") == [] and s.lookup("방앗간도둑") == []


def test_b9_uydurulmus_tek_kodpoint_reddi_latin_ve_kana_da(tmp_path: Path) -> None:
    """UYDURULMUS (belgeli): paket 'tek hangul/tek kanji' der; kod tum tek kodpointleri reddeder (`x`, `ア`)."""
    for k in ("x", "ア", "1"):
        with pytest.raises(ValueError, match="tek kodpoint"):
            sozluk(tmp_path, [{"kaynak": k, "hedef": "X"}])


def test_b9_hedef_kaynagi_iceren_veya_kaynak_hedefi_iceren_kayit_semada_serbest(tmp_path: Path) -> None:
    """TUR-2 (d): `hedef ⊇ kaynak` (idempotens; docstring 'tekrar gecirilmez' ile belgelendi) ve kimlik (K4 v3 gecerli) serbest
    KALDI; `マルクス。` artik K6 v3 ile RED (O-B1)."""
    assert len(sozluk(tmp_path, [{"kaynak": "mill", "hedef": "Değirmen mill"}])) == 1
    assert len(sozluk(tmp_path, [{"kaynak": "Marcus", "hedef": "Marcus"}])) == 1
    with pytest.raises(ValueError, match="kaynak cumle sonu"):
        sozluk(tmp_path, [{"kaynak": "マルクス。", "hedef": "Marcus"}])


# ---------------------------------------------------------------------------
# BX -- docstring iddialari (garanti alani; ayrisirsa strict xfail haber verir)
# ---------------------------------------------------------------------------


def test_bx_docstring_k5_lookup_ve_gom_io_yapmaz_dosya_silinse_calisir(tmp_path: Path) -> None:
    p = tmp_path / "gecici.json"
    p.write_text(json.dumps({"terimler": [{"kaynak": "マルクス", "hedef": "Marcus"}]}, ensure_ascii=False), encoding="utf-8")
    st = GlossaryStore(p)
    p.unlink()
    sg = seg("マルクスが来た。")
    assert terimleri_gom((sg,), st.lookup_segments((sg,)))[0].text == "Marcusが来た。"


def test_bx_docstring_repr_terim_basmaz(s: GlossaryStore) -> None:
    r = repr(s)
    assert "terim_sayisi=7" in r and "マルクス" not in r and "Marcus" not in r  # TUR-2 (c): fixture v3 7 terim


def test_bx_docstring_k2_hata_mesajlari_metin_tasimaz(s: GlossaryStore) -> None:
    sg = seg("GIZLI-NOBETCI マルクス")
    h = s.lookup(sg.text)[0]
    for kotu in (dataclasses.replace(h, segment_index=0, start=0, end=5), dataclasses.replace(h, segment_index=None),
                 dataclasses.replace(h, segment_index=0, target_term="")):
        with pytest.raises(ContractViolation) as ei:
            terimleri_gom((sg,), (kotu,))
        assert "GIZLI" not in str(ei.value) and "マルクス" not in str(ei.value) and "Marcus" not in str(ei.value)


def test_bx_docstring_bom_cozulur(tmp_path: Path) -> None:
    p = tmp_path / "bom.json"
    p.write_bytes(b"\xef\xbb\xbf" + json.dumps({"terimler": [{"kaynak": "マルクス", "hedef": "Marcus"}]}, ensure_ascii=False).encode("utf-8"))
    assert len(GlossaryStore(p)) == 1


# ---------------------------------------------------------------------------
# BK -- kapi (real_check) olcu denetimi: modelsiz ayristirilabilen kisim
# ---------------------------------------------------------------------------


def test_bk_real_check_1_olcusu_lower_turkce_I_tuzagi() -> None:
    """KAPI (kural 8/10 disi, olcu dogrulugu): `hedef.lower() in g.lower()` -- `"İ".lower()` 2 kodpoint (`i` + U+0307)
    -> `İ` ile baslayan hedef (`İhtiyar`) ciktida KUCUK harfle ('ihtiyar') gecse bile `in` SESSIZCE False. #1'in bugunku
    hedefleri `Marcus`/`Değirmen` oldugu icin etkilenmiyor; fixture'a `İ`li hedef girince #1 yanlis IHLAL verir."""
    assert "İhtiyar".lower() == "i\u0307htiyar" and len("İhtiyar".lower()) == 8
    assert "İhtiyar".lower() not in "bir ihtiyar geldi."          # tuzak
    assert "ihtiyar" in "bir ihtiyar geldi."                      # niyet edilen olcu
    assert "değirmen" == "Değirmen".lower()                        # bugunku hedefler etkilenmez


def test_bk_real_check_kapi_yolu_ile_lookup_segments_ayni_hit_kumesi(s: GlossaryStore) -> None:
    """Kapi `lookup` + `dataclasses.replace` kullaniyor; modulun onerdigi yol `lookup_segments`. Ikisi ayni (kural 8:
    kapi referansi uygulamadan turetmiyor, hedef dizeleri sabit; bu test yalniz iki yolun denkligini pinler)."""
    segs = tuple(seg(t) for t in ["長老マルクス", "マルクスがあなたを待っています。", "水車小屋を過ぎて東の道を行きなさい。",
                                  "장로 마르쿠스", "방앗간을 지나 동쪽 길로 가십시오.", "The elder Marcus waits by the mill."])
    kapi = tuple(dataclasses.replace(h, segment_index=i) for i, g in enumerate(segs) for h in s.lookup(g.text, g.placeholders))
    assert kapi == s.lookup_segments(segs) and len(kapi) == 6  # TUR-2 (c): fixture v3 unvansiz/millsiz: 1+1+1+1+1+1
