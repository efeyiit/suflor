"""TESTER-B (T-011, TUR 2) -- mercek: KOTU KULLANIM + SARTNAME UYUMU; paket v3'un ▲ maddeleri hedefte.

Kor yazildi: `delivery.md`, `evidence/`, `sef_dogrulama/`, `test_sozluk.py` acilmadan.
Paket: `.agents/tasks/T-011/packet.md` surum 3. Kod: `src/translate/sozluk.py` (v3, HEAD 9c8d85f).
Tur-1 testleri `test_mercek_b.py` icinde yeniden nisanlandi (her degisiklik `TUR-2 (a|b|c|d)` ile isaretli).

Kos:
    python -m pytest .agents/tasks/T-011/tester_B -q -p no:cacheprovider --import-mode=importlib

Test adlari:
  test_t1_*  ▲ sartname satir satir: JP/KR ek listeleri (her ek ayri kimlik), zincir, betik gecisi 6+8, trie sirasi,
             K2 NFC/CV, K4 kimlik, K5 ozyineleme, K6 terminator/Cc/100 -- "kod yapiyor mu"
  test_t2_*  paket-olcum celiskileri (`マルクス山`, `마르쿠스들이다`) + 3-ek/liste-disi ek kacagi OLCUMU (statik)
  test_t3_*  betik gecisi kotu kullanim: katakana cins isim + kanji/katakana, Latin ad + Latin ek, sembol asimetrisi, genislik
  test_t4_*  K2/K3/K6 kotu kullanim: bosluklu/terimle ayni yer tutucu, gomulu segmentin tekrar zincire girmesi, kaydirilmis
             liste, `kisa_terim_izni` x terminator/`{`, `Cf` hedef, elle kurulan hit K6'yi atlar
  test_t5_*  K5 dusmanca zincir girdileri (< 60 ms; izleyici altinda 4x)
  test_t6_*  zincir: `windmill` -> bitisik `RüzgarDeğirmen` (belgeli), `oldmillhouse`, olu yon
  test_t7_*  kapi (`real_check` v4) modelsiz denetim: `_kat`, #6 sabitleri kod dogrulamasi, kural 8
  test_t8_*  demo (sefin K-B7 duzeltmesi) statik denetim: `except TranslatorError`, kimlik suzgeci
"""
from __future__ import annotations

import dataclasses
import json
import re
import statistics
import sys
import time
import unicodedata
from pathlib import Path

import pytest

from src.contracts.errors import ContractViolation, TranslatorError
from src.contracts.models import Rect, Segment, TermHit
from src.translate.local_nmt import _yer_tutuculari_onar, cumlelere_bol, modele_gider
from src.translate.sozluk import GlossaryStore, terimleri_gom

KOK = Path(__file__).resolve().parents[4]
FIXTURE = KOK / ".agents" / "tasks" / "T-011" / "fixtures" / "sozluk_ornek.json"
SOZLUK_PY = KOK / "src" / "translate" / "sozluk.py"
DEMO_PY = KOK / "demo" / "canli_cevir.py"
R = Rect(0, 0, 100, 20)

JP_EKLER = ["さん", "様", "殿", "君", "ちゃん", "達", "たち", "って", "だ", "から", "まで", "より", "か", "よ", "ね"]
KR_EKLER_G6 = ["을", "를", "이", "가", "은", "는", "에", "에서", "으로", "로", "와", "과", "도", "의", "만", "께서", "부터", "까지"]
KR_EKLER_V3 = ["에게", "한테", "께", "님", "씨", "야", "아", "랑", "이랑", "들", "처럼", "보다", "마다", "밖에", "조차", "라고", "라면", "입니다", "이다"]


def seg(text: str, ph: tuple[str, ...] = (), speaker: str | None = None) -> Segment:
    return Segment(text=text, bbox=R, placeholders=ph, speaker=speaker)


def sozluk(tmp_path: Path, terimler: list[dict[str, object]], ad: str = "s.json") -> GlossaryStore:
    p = tmp_path / ad
    p.write_text(json.dumps({"terimler": terimler}, ensure_ascii=False), encoding="utf-8")
    return GlossaryStore(p)


def hedefler(s: GlossaryStore, metin: str, ph: tuple[str, ...] = ()) -> list[str]:
    return [h.target_term for h in s.lookup(metin, ph)]


@pytest.fixture(scope="module")
def s() -> GlossaryStore:
    return GlossaryStore(FIXTURE)


@pytest.fixture(scope="module")
def u(tmp_path_factory: pytest.TempPathFactory) -> GlossaryStore:
    """Unvanli sozluk (paketin K1 ornekleri unvan ister; fixture v3 unvansiz)."""
    return sozluk(tmp_path_factory.mktemp("u"), [
        {"kaynak": "長老", "hedef": "İhtiyar"}, {"kaynak": "장로", "hedef": "İhtiyar"}, {"kaynak": "マルクス", "hedef": "Marcus"},
        {"kaynak": "마르쿠스", "hedef": "Marcus"}, {"kaynak": "アイラ", "hedef": "Ayla"}, {"kaynak": "아일라", "hedef": "Ayla"},
        {"kaynak": "水車小屋", "hedef": "Değirmen"}, {"kaynak": "방앗간", "hedef": "Değirmen"}, {"kaynak": "ひかり", "hedef": "Hikari"},
    ])


# ---------------------------------------------------------------------------
# T1 -- ▲ sartname satir satir
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ek", JP_EKLER)
def test_t1_k1_jp_saygi_eki_her_biri_eslesir_katakana_ve_kanji_ve_hiragana_ad(u: GlossaryStore, ek: str) -> None:
    """▲ K1: listedeki HER JP ek katakana adda (betik gecisi de kapsar), kanji unvanda (Han+Han: yalniz liste) ve
    hiragana adda (Hiragana+Hiragana: yalniz liste) sag sinirdir."""
    assert hedefler(u, "マルクス" + ek) == ["Marcus"]
    assert hedefler(u, "長老" + ek + "が来た。") == ["İhtiyar"]
    assert hedefler(u, "ひかり" + ek) == ["Hikari"]


@pytest.mark.parametrize("ek", KR_EKLER_G6 + KR_EKLER_V3)
def test_t1_k1_kr_ek_her_biri_eslesir_ve_ekten_sonra_sinir_gerekir(u: GlossaryStore, ek: str) -> None:
    """▲ K1: listedeki HER KR ek sag sinirdir; ekten sonra gercek sinir gerekir (`ek` + `침` eslesmez)."""
    assert hedefler(u, "마르쿠스" + ek) == ["Marcus"]
    assert hedefler(u, "마르쿠스" + ek + " 왔다.") == ["Marcus"]
    assert hedefler(u, "마르쿠스" + ek + "침") == []  # ekten sonra Hangul harfi: sinir yok


def test_t1_k1_paketin_pozitif_ornekleri_v3(u: GlossaryStore) -> None:
    """▲ K1 OLCU satiri: `장로 마르쿠스` 2, `長老マルクス` 2 (zincir), `長老マルクスアイラ` 3, `マルクスさんが` 1, `장로님이` 1, `에게` listeden."""
    assert hedefler(u, "장로 마르쿠스") == ["İhtiyar", "Marcus"]
    assert hedefler(u, "長老マルクス") == ["İhtiyar", "Marcus"]
    assert hedefler(u, "長老マルクスアイラ") == ["İhtiyar", "Marcus", "Ayla"]
    assert hedefler(u, "マルクスさんが") == ["Marcus"]
    assert hedefler(u, "장로님이") == ["İhtiyar"]
    assert hedefler(u, "마르쿠스에게") == ["Marcus"]
    assert hedefler(u, "Marcusが") == []  # `Marcus` bu sozlukte yok -> pozitif kontrol icin fixture'a bak (asagida)


def test_t1_k1_paketin_negatif_ornekleri_v3(u: GlossaryStore, tmp_path: Path) -> None:
    """▲ K1: `村人`/`剣士`/`검사`/`방앗간집`/`真剣に`/`中村`/`windmills`/`millstones` eslesmez."""
    st = sozluk(tmp_path, [{"kaynak": "村", "hedef": "Köy", "kisa_terim_izni": True}, {"kaynak": "剣", "hedef": "Kılıç", "kisa_terim_izni": True},
                           {"kaynak": "검", "hedef": "Kılıç", "kisa_terim_izni": True}, {"kaynak": "방앗간", "hedef": "Değirmen"},
                           {"kaynak": "wind", "hedef": "Rüzgar"}, {"kaynak": "mill", "hedef": "Değirmen"}, {"kaynak": "stone", "hedef": "Taş"}])
    for m in ("村人", "剣士", "검사", "방앗간집", "真剣に", "中村", "windmills", "millstones", "The windmills turn.", "millstones."):
        assert st.lookup(m) == [], m
    assert [h.target_term for h in st.lookup("windmill")] == ["Rüzgar", "Değirmen"]  # yazar ikisini de istedi (belgeli)
    assert [h.target_term for h in st.lookup("millstone")] == ["Değirmen", "Taş"]


@pytest.mark.parametrize("metin,n", [
    ("長老マルクス", 1), ("マルクス様", 1), ("マルクスさん", 1), ("マルクスたち", 1), ("長老Marcus", 1), ("Marcus様", 1), ("마르쿠스Marcus", 2),
])
def test_t1_k1_betik_gecisi_pozitif_kimlik_cipasi_gerekmez(s: GlossaryStore, metin: str, n: int) -> None:
    """▲ K1 betik gecisi 6 pozitif (fixture v3, unvan YOK): `長老マルクス` -> `マルクス`; `長老Marcus` kimlik cipasi olmadan da
    (`Marcus` fixture'da kimlik olarak var; pozitif kontrol asagida ayrica cipasiz sozlukle)."""
    assert len(s.lookup(metin)) == n


def test_t1_k1_betik_gecisi_kimlik_cipasi_olmadan_da_sinir(tmp_path: Path) -> None:
    """▲ K4/K1: `長老Marcus` -> `長老` yalniz `Marcus` sozlukteyken DEGIL, betik gecisiyle her zaman eslesir (v3)."""
    st = sozluk(tmp_path, [{"kaynak": "長老", "hedef": "İhtiyar"}])
    assert hedefler(st, "長老Marcus") == ["İhtiyar"]
    assert hedefler(st, "長老Marcusa") == ["İhtiyar"]
    assert hedefler(st, "Marcus長老") == ["İhtiyar"]


@pytest.mark.parametrize("metin", ["マルクスタウン", "村人", "剣士", "中村", "검사", "방앗간집", "Marcus2", "Marcuss", "windmills", "アイラー", "마르쿠스아침"])
def test_t1_k1_betik_gecisi_negatif_sinif_ici_komsu_sinir_degil(tmp_path: Path, metin: str) -> None:
    """▲ K1 betik gecisi 8 negatif (+3): ayni sinif komsu sinir DEGIL."""
    st = sozluk(tmp_path, [{"kaynak": "マルクス", "hedef": "Marcus"}, {"kaynak": "村", "hedef": "Köy", "kisa_terim_izni": True},
                           {"kaynak": "剣", "hedef": "Kılıç", "kisa_terim_izni": True}, {"kaynak": "검", "hedef": "Kılıç", "kisa_terim_izni": True},
                           {"kaynak": "방앗간", "hedef": "Değirmen"}, {"kaynak": "Marcus", "hedef": "Marcus"}, {"kaynak": "wind", "hedef": "Rüzgar"},
                           {"kaynak": "mill", "hedef": "Değirmen"}, {"kaynak": "アイラ", "hedef": "Ayla"}, {"kaynak": "마르쿠스", "hedef": "Marcus"}])
    assert st.lookup(metin) == []


def test_t1_k1_trie_anahtari_ignorecase_denk_iki_sirada(tmp_path: Path) -> None:
    """▲ K1 (O-A1): `{Maßen, Maẞer, Maße}` her JSON sirasinda `Maẞer` bulunur."""
    siralar: tuple[list[dict[str, object]], ...] = ([{"kaynak": "Maßen", "hedef": "A"}, {"kaynak": "Maẞer", "hedef": "B"}, {"kaynak": "Maße", "hedef": "C"}],
                 [{"kaynak": "Maße", "hedef": "C"}, {"kaynak": "Maẞer", "hedef": "B"}, {"kaynak": "Maßen", "hedef": "A"}],
                 [{"kaynak": "Maẞer", "hedef": "B"}, {"kaynak": "Maße", "hedef": "C"}, {"kaynak": "Maßen", "hedef": "A"}])
    for sira in siralar:
        st = sozluk(tmp_path, sira)
        assert [(h.source_term, h.target_term) for h in st.lookup("Die Maẞer sind da")] == [("Maẞer", "B")]
        assert [(h.source_term, h.target_term) for h in st.lookup("die maßer sind da")] == [("maßer", "B")]


def test_t1_k2_nfd_segment_ve_yer_tutucu_birlikte_nfc_ve_t007_sayimi_bir(s: GlossaryStore) -> None:
    """▲ K2 (O-B2 duzeltmesi): hit'i olan segmentte `text` VE `placeholders` NFC; her yer tutucu ciktida alt dize;
    T-007 `modele_gider` sayimi 1 ve `_yer_tutuculari_onar` kopya EKLEMEZ. Hit'siz NFD segment aynen (`is`)."""
    nfd = unicodedata.normalize("NFD", "{Değirmen}")
    nfc = unicodedata.normalize("NFC", nfd)
    sg = seg(nfd + "はマルクスの家です。", (nfd,))
    g = terimleri_gom((sg,), s.lookup_segments((sg,)))[0]
    assert unicodedata.is_normalized("NFC", g.text) and g.placeholders == (nfc,)
    assert g.placeholders[0] in g.text
    assert g.text.count(g.placeholders[0]) == 1
    parcalar = cumlelere_bol(g.text)
    assert len(parcalar) == 1 and modele_gider(parcalar[0], g.placeholders) is True
    assert _yer_tutuculari_onar(nfc + " Marcus evi", g.text, g.placeholders) == nfc + " Marcus evi"  # kopya yok
    sg3 = seg(unicodedata.normalize("NFD", "Değirmen yok."))
    assert terimleri_gom((sg3,), s.lookup_segments((sg3,)))[0] is sg3


def test_t1_k2_yer_tutucu_tuple_uzunluk_sira_bos_oge_korunur(s: GlossaryStore) -> None:
    """▲ K2: NFC'leme tuple'in uzunlugunu/sirasini/bos ogelerini korur (docstring iddiasi)."""
    nfd = unicodedata.normalize("NFD", "{Değirmen}")
    sg = seg("マルクス" + nfd, ("", nfd, "{0}", ""))
    g = terimleri_gom((sg,), s.lookup_segments((sg,)))[0]
    assert g.placeholders == ("", unicodedata.normalize("NFC", nfd), "{0}", "")
    assert g.text == "Marcus" + unicodedata.normalize("NFC", nfd)


@pytest.mark.parametrize("ph", ["{0}", b"{0}", 5, [1], ["{0}", None], {"{0}": 1}])
def test_t1_k2_segment_kaynakli_bicim_hatasi_contract_violation_iki_girisde(s: GlossaryStore, ph: object) -> None:
    """▲ K2 (O-B4 duzeltmesi): `Segment.placeholders` duz str/bytes/int/str-olmayan oge -> `lookup_segments` VE
    `terimleri_gom` `ContractViolation` (TranslatorError). Dogrudan `lookup` `TypeError` (belgeli)."""
    bozuk = Segment(text="マルクスが来た。", bbox=R, placeholders=ph)  # type: ignore[arg-type]
    with pytest.raises(ContractViolation, match=r"segments\[0\]\.placeholders") as e1:
        s.lookup_segments((bozuk,))
    assert isinstance(e1.value, TranslatorError)
    with pytest.raises(ContractViolation, match=r"segments\[0\]\.placeholders") as e2:
        terimleri_gom((bozuk,), (TermHit("マルクス", "Marcus", 0, 4, 0),))
    assert isinstance(e2.value, TranslatorError)
    assert "マルクス" not in str(e1.value) and "マルクス" not in str(e2.value)
    with pytest.raises(TypeError):
        s.lookup("マルクスが来た。", ph)  # type: ignore[arg-type]


def test_t1_k2_text_str_degil_contract_violation(s: GlossaryStore) -> None:
    bozuk = Segment(text=b"x", bbox=R)  # type: ignore[arg-type]
    with pytest.raises(ContractViolation, match="text str degil"):
        s.lookup_segments((bozuk,))
    with pytest.raises(ContractViolation, match="text str degil"):
        terimleri_gom((bozuk,), (TermHit("x", "Y", 0, 1, 0),))
    with pytest.raises(ContractViolation, match="Segment degil"):
        s.lookup_segments(("マルクス",))  # type: ignore[arg-type]


def test_t1_k4_kimlik_girdisi_hit_uretir_metin_esit_ve_docstring_adlandirir(s: GlossaryStore) -> None:
    """▲ K4: `Marcus -> Marcus` hit uretir, gom ciktisi metin-esit; docstring 'SINIR CIPASI' der ve 'v3'te cipa gerekmez' der."""
    sg = seg("Marcusが待っています。")
    hits = s.lookup_segments((sg,))
    assert [(h.source_term, h.target_term) for h in hits] == [("Marcus", "Marcus")]
    assert terimleri_gom((sg,), hits)[0].text == sg.text
    doc = SOZLUK_PY.read_text(encoding="utf-8")
    assert "SINIR CIPASI" in doc and "cipa olmadan da" in doc
    assert "source_term != target_term" in doc  # cagirana suzme talimati


def test_t1_k4_docstring_yazarlik_kurali_ve_gri_bolge_ve_idempotens_notu() -> None:
    """▲ K4/K6 docstring maddeleri: yazarlik kurali (unvan/cins isim uyarisi), gri bolge, 'tekrar sozlukten gecirilmez'."""
    doc = SOZLUK_PY.read_text(encoding="utf-8").split('"""', 2)[1]
    for parca in ("YAZARLIK KURALI", "UNVAN VE CINS", "GRI BOLGE", "GOMULU SEGMENT TEKRAR SOZLUKTEN GECIRILMEZ", "idempotens YOK",
                  "hedef tarafi duzeltme", "ZINCIR KURALI", "BETIK GECISI", "[ÖLÇÜLMÜYOR]"):
        assert parca in doc, parca


def test_t1_k5_2000_kodpoint_kaynak_valueerror_recursionerror_degil(tmp_path: Path) -> None:
    """▲ K5/K6 (O-A2): 2000 kodpoint kaynak -> `ValueError` (asla `RecursionError`); 100 kabul, 101 red."""
    with pytest.raises(ValueError, match="en fazla 100"):
        sozluk(tmp_path, [{"kaynak": "マ" * 2000, "hedef": "X"}])
    with pytest.raises(ValueError, match="101 kodpoint"):
        sozluk(tmp_path, [{"kaynak": "a" * 101, "hedef": "X"}])
    st = sozluk(tmp_path, [{"kaynak": "a" * 100, "hedef": "X"}])
    assert len(st) == 1 and hedefler(st, "a" * 100) == ["X"] and hedefler(st, "a" * 101) == []


@pytest.mark.parametrize("kayit,parca", [
    ({"kaynak": "マルクス。", "hedef": "Marcus"}, "kaynak cumle sonu"),
    ({"kaynak": "Marcus.", "hedef": "Marcus"}, "kaynak cumle sonu"),
    ({"kaynak": "Mr. Marcus", "hedef": "Marcus"}, "kaynak cumle sonu"),
    ({"kaynak": "マルクス！", "hedef": "Marcus"}, "kaynak cumle sonu"),
    ({"kaynak": "？", "hedef": "Soru", "kisa_terim_izni": True}, "kaynak cumle sonu"),
    ({"kaynak": "マルクス", "hedef": "Mar\ncus"}, "kontrol karakteri"),
    ({"kaynak": "マルクス", "hedef": "Mar\tcus"}, "kontrol karakteri"),
    ({"kaynak": "マルクス", "hedef": "Mar\x85cus"}, "kontrol karakteri"),
    ({"kaynak": "マルクス", "hedef": "Mar\x00cus"}, "kontrol karakteri"),
    ({"kaynak": "マルクス", "hedef": "Marcus", "kisa_terim_izni": 1}, "bool olmali"),
    ({"kaynak": "マルクス", "hedef": "Marcus", "not": 5}, "'not' str"),
])
def test_t1_k6_yeni_red_siniflari(tmp_path: Path, kayit: dict[str, object], parca: str) -> None:
    """▲ K6: kaynakta terminator (her yerde; `kisa_terim_izni` kurtarmaz), hedefte Cc, tip hatalari -> ValueError, mesajda sinif."""
    with pytest.raises(ValueError, match=parca):
        sozluk(tmp_path, [kayit])


def test_t1_k6_kaynak_terminator_reddi_zinciri_korur_pozitif_kontrol(tmp_path: Path) -> None:
    """(O-B1 kapanisi) Terminatorsuz kaynakla ayni cumle: hit var ve T-007 parca sayisi 2 -> 2 (cumle siniri korunur)."""
    st = sozluk(tmp_path, [{"kaynak": "マルクス", "hedef": "Marcus"}])
    sg = seg("彼はマルクス。 行こう。")
    g = terimleri_gom((sg,), st.lookup_segments((sg,)))[0]
    assert g.text == "彼はMarcus。 行こう。" and len(cumlelere_bol(sg.text)) == len(cumlelere_bol(g.text)) == 2


# ---------------------------------------------------------------------------
# T2 -- paket-olcum celiskileri + kacak olcumu
# ---------------------------------------------------------------------------


def test_t2_paket_celiskisi_マルクス山_betik_gecisiyle_1_hit_implementer_hakli(s: GlossaryStore) -> None:
    """Paket K1: `マルクス山` 'eslesmez' (saygi listesi negatif kontrolu); ama ayni paketin betik gecisi kurali Katakana|Han'i
    sinir yapar (`マルクス様` ile AYNI cift). Implementer kurali izledi, olcum 1 hit. Tester-B de olctu: 1. Paketin ic celiskisi;
    implementer hakli (`Marcus山` -> ad + siniflandirici, `ゴブリン王` sinifi)."""
    assert [(h.source_term, h.end) for h in s.lookup("マルクス山")] == [("マルクス", 4)]
    assert len(s.lookup("マルクス様")) == 1  # ayni betik cifti


def test_t2_paket_celiskisi_마르쿠스들이다_iki_ek_implementer_hakli(s: GlossaryStore) -> None:
    """Paket K1: `마르쿠스들이다` '3 ek, eslesmez'; ama `이다` paketin kendi listesinde TEK ektir -> `들`+`이다` = 2 -> eslesir.
    Implementer olctu 1; Tester-B de olctu 1. Paketin ic celiskisi; implementer hakli."""
    assert len(s.lookup("마르쿠스들이다")) == 1
    assert len(s.lookup("마르쿠스들이")) == 1 and len(s.lookup("마르쿠스이다")) == 1


@pytest.mark.parametrize("metin", ["마르쿠스님에게는", "마르쿠스님께서는", "마르쿠스님한테도", "마르쿠스들에게는", "마르쿠스님으로부터", "마르쿠스님들은", "마르쿠스님께서도"])
def test_t2_uc_ek_yigini_eslesmez_belgeli_sinir_olcum(s: GlossaryStore, metin: str) -> None:
    """BELGELI SINIR (K1 zincir <= 2): 3 ek yigini 0 hit. Dogal NPC metninde yayginligi `test_t2_kr_dogal_10_cumle_*` ve
    gercek modelle `model-olcum-tur2` M4 ile olculdu (2/10; hamda ad KAYIP 0/2). Bu test siniri PINLER, davranisi onaylamaz."""
    assert s.lookup(metin) == []


@pytest.mark.parametrize("metin", ["마르쿠스에게서", "마르쿠스한테서", "마르쿠스예요", "마르쿠스이에요", "마르쿠스요", "마르쿠스가요", "마르쿠스는데", "마르쿠스인가"])
def test_t2_liste_disi_kr_ek_eslesmez_olcum(s: GlossaryStore, metin: str) -> None:
    """OLCUM (paket K1 KR listesi disi): `에게서/한테서` (-den), `예요/이에요` (kopula), `요` (nezaket), `는데`, `인가` -> 0 hit.
    `에게서` = `에게` + `서` (`서` listede yok); `예요` listede yok. Oyun diyalogunda `-예요`/`-에게서` yaygin (orta, paket)."""
    assert s.lookup(metin) == []


def test_t2_kr_dogal_10_cumle_kacak_2_10(s: GlossaryStore) -> None:
    """OLCUM: 10 dogal NPC cumlesi (ad + ek); ad hit'i olmayan 2/10 (`님께서는` 3 ek, `한테서` liste disi).
    Yigin agirlikli 10 cumlede 6/10. Gercek model (M4): kacak 2'de ad hamda zaten dogru -> kayip 0/2."""
    dogal = ["마르쿠스님, 어서 오세요.", "마르쿠스님께서 부르십니다.", "아일라는 방앗간에 있어요.", "마르쿠스님께서는 오늘 안 계십니다.",
             "이건 아일라의 검이에요.", "마르쿠스에게 이 편지를 전해 주세요.", "아일라한테서 들었어요.", "마르쿠스님도 함께 가실 거예요.",
             "아일라야, 조심해!", "마르쿠스님은 마을 장로입니다."]
    kacak = [c for c in dogal if not any(h.target_term in ("Marcus", "Ayla") for h in s.lookup(c))]
    assert kacak == ["마르쿠스님께서는 오늘 안 계십니다.", "아일라한테서 들었어요."]
    yigin = ["마르쿠스님께서는 지금 안 계십니다.", "마르쿠스님에게는 비밀이 있습니다.", "아일라님한테도 말했어요.", "마르쿠스님께 전해 주세요.",
             "아일라님이 오셨습니다.", "마르쿠스에게서 편지가 왔습니다.", "마르쿠스님의 검입니다.", "아일라님은 방앗간에 계십니다.",
             "마르쿠스님들은 어디 계세요?", "마르쿠스님께서도 동의하셨습니다."]
    assert sum(not any(h.target_term in ("Marcus", "Ayla") for h in s.lookup(c)) for c in yigin) == 6


@pytest.mark.parametrize("metin,n", [
    ("太郎先生", 0), ("太郎先輩", 0), ("太郎氏", 0), ("太郎公", 0), ("太郎王", 0), ("太郎隊長", 0),
    ("太郎様", 1), ("太郎君", 1), ("太郎達", 1), ("太郎殿", 1), ("太郎が", 1), ("太郎さん", 1),
    ("ひかりくん", 0), ("ひかりさま", 0), ("ひかりせんぱい", 0), ("ひかりせんせい", 0), ("ひかりたん", 0),
    ("ひかりちゃん", 1), ("ひかりさん", 1), ("ひかりは", 1), ("ひかりです", 1), ("ひかり姫", 1),
])
def test_t2_jp_ayni_betik_ad_ek_liste_disi_kacak_olcum(tmp_path: Path, metin: str, n: int) -> None:
    """OLCUM (paket K1 JP listesi disi; Y-B2 devami): KANJI ad + kanji unvan eki (`先生 先輩 氏 公 王 隊長`) ve HIRAGANA ad +
    hiragana eki (`くん さま せんぱい せんせい たん`) betik gecisi vermez, listede de yok -> 0 hit. Katakana adlar etkilenmez.
    Gercek model (M5): `太郎先輩`/`ひかりくん`/`ひかりさま` hamda ad KAYIP ('Tamir Bey', 'Bir ışık'); `太郎様`/`ひかりちゃん` gomulu dogru."""
    st = sozluk(tmp_path, [{"kaynak": "太郎", "hedef": "Taro"}, {"kaynak": "ひかり", "hedef": "Hikari"}])
    assert len(st.lookup(metin)) == n


# ---------------------------------------------------------------------------
# T3 -- betik gecisi kotu kullanim
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def c(tmp_path_factory: pytest.TempPathFactory) -> GlossaryStore:
    """Cins isim sozlugu (K4 uyarisina ragmen yazarin girebilecegi)."""
    return sozluk(tmp_path_factory.mktemp("c"), [
        {"kaynak": "ゴブリン", "hedef": "Goblin"}, {"kaynak": "ポーション", "hedef": "İksir"}, {"kaynak": "エルフ", "hedef": "Elf"},
        {"kaynak": "マルクス", "hedef": "Marcus"}, {"kaynak": "마르쿠스", "hedef": "Marcus"}, {"kaynak": "Marcus", "hedef": "Marcus"},
    ])


@pytest.mark.parametrize("metin,beklenen", [
    ("ゴブリンキング", []), ("ゴブリン・キング", ["Goblin"]), ("ゴブリンの王", ["Goblin"]),
    ("ゴブリン王", ["Goblin"]), ("ゴブリン王が現れた。", ["Goblin"]), ("ポーション瓶", ["İksir"]), ("エルフ族の村", ["Elf"]),
    ("마르쿠스王", ["Marcus"]), ("マルクス家", ["Marcus"]),
])
def test_t3_katakana_terim_kanji_komsu_sinir_katakana_komsu_degil(c: GlossaryStore, metin: str, beklenen: list[str]) -> None:
    """Betik gecisi: `ゴブリンキング` (Katakana|Katakana) 0; `ゴブリン王` (Katakana|Han) 1 -> `Goblin王` gomulur.
    Gercek model (M2): `Goblin王` -> 'Goblin Kralı' (ham 'Kral Goblin'), `İksir瓶` -> 'İksir şişesi' (ham 'Potasyon şişesi'),
    `Elf族` -> 'Elf köyü' (ham 'Elfler köyü'): 0/5 bozulma, 2/5 duzelme. Istenen davranis; K4 cins-isim uyarisi belgeli."""
    assert hedefler(c, metin) == beklenen


@pytest.mark.parametrize("metin,n", [
    ("Marcus's", 1), ("Marcus'", 1), ("Marcus’s", 1), ("Marcus'ın", 1), ("MARCUS'UN", 1), ("Marcus-san", 1), ("Marcus_2", 1),
    ("Marcusさん", 1), ("Marcus様", 1), ("長老Marcus", 1), ("Marcus2", 0), ("Marcuss", 0), ("Marcusa", 0), ("xMarcus", 0),
])
def test_t3_latin_ad_latin_ek_apostrof_ve_tire_sinir_harf_ve_rakam_degil(c: GlossaryStore, metin: str, n: int) -> None:
    """Latin ad + Latin ek: `'`/`’`/`-`/`_` P* -> sinir (`Marcus'ın` Turkce ek iyi); harf/rakam bitisik -> degil (`Marcus2` 0)."""
    assert len(c.lookup(metin)) == n


@pytest.mark.parametrize("sym", ["♪", "～", "♥", "☆", "→", "＋", "♡", "★", "♫", "©", "™", "°", "＄", "￥"])
def test_t3_sembol_asimetrisi_cjk_terimde_sinir_latin_terimde_degil(c: GlossaryStore, sym: str) -> None:
    """Sembol (`S*`) DIGER sinifinda (docstring belgeli asimetri): `マルクス♪` betik gecisiyle 1, `Marcus♪` 0.
    `マルクス→アイラ` 2 hit ama `Marcus→Ayla` 0 (tur-1 D-B1 CJK tarafinda kapandi, Latin tarafinda kaldi; dusuk)."""
    assert unicodedata.category(sym).startswith("S")
    assert len(c.lookup("マルクス" + sym)) == 1 and len(c.lookup(sym + "マルクス")) == 1
    assert len(c.lookup("Marcus" + sym)) == 0 and len(c.lookup(sym + "Marcus")) == 0


def test_t3_genislik_katlanmaz_yarim_katakana_tam_latin_eslesmez(c: GlossaryStore) -> None:
    """NFC genislik katlamaz (NFKC degil): `ﾏﾙｸｽ` (yarim genislik) ve `Ｍａｒｃｕｓ` (tam genislik) 0 hit. T-004 girdiyi NFKC'lemez;
    JP oyunlarinda tam genislik Latin yaygin -> yazar kaynagi OCR'daki genislikle yazmali. `[ÖLÇÜLMÜYOR]` adayi (dusuk)."""
    assert c.lookup("ﾏﾙｸｽが来た。") == [] and c.lookup("Ｍａｒｃｕｓが来た。") == []
    assert len(c.lookup(unicodedata.normalize("NFKC", "ﾏﾙｸｽが来た。"))) == 1  # pozitif kontrol: NFKC'lenirse eslesir


# ---------------------------------------------------------------------------
# T4 -- K2/K3/K6 kotu kullanim
# ---------------------------------------------------------------------------


def test_t4_bosluk_yer_tutucu_hit_engellemez_gomme_dogru(s: GlossaryStore) -> None:
    """`placeholders=(" ",)`: her bosluk korunan aralik (zaten sinir); hit'ler etkilenmez, gom dogru, yer tutucu tasinir."""
    sg = seg("マルクスが アイラを 待つ", (" ",))
    hits = s.lookup_segments((sg,))
    assert [h.target_term for h in hits] == ["Marcus", "Ayla"]
    g = terimleri_gom((sg,), hits)[0]
    assert g.text == "Marcusが Aylaを 待つ" and g.placeholders == (" ",)


def test_t4_terimle_ayni_yer_tutucu_hit_yok_elle_hit_contract_violation(s: GlossaryStore) -> None:
    """`placeholders=("マルクス",)`: terim korunan aralik -> 0 hit; elle kurulan hit -> CV (dusurme degil)."""
    sg = seg("マルクスが来た。", ("マルクス",))
    assert s.lookup_segments((sg,)) == ()
    with pytest.raises(ContractViolation, match="yer tutucu"):
        terimleri_gom((sg,), (TermHit("マルクス", "Marcus", 0, 4, 0),))


def test_t4_yer_tutucu_terimin_parcasi_hit_yok_komsu_terim_etkilenmez(s: GlossaryStore) -> None:
    sg = seg("マルクスとアイラ", ("ル",))
    assert [h.target_term for h in s.lookup_segments((sg,))] == ["Ayla"]


def test_t4_gomulu_segment_tekrar_zincire_fixture_ile_sessiz_sabit(s: GlossaryStore) -> None:
    """Docstring 'gomulu segment tekrar sozlukten gecirilmez' -- ama gecirilirse: fixture ile CV YOK, metin sabit; kimlik hit
    (`Marcus`) uretilir (sayac icin suzulmeli). Sessiz, zararsiz."""
    for m in ("長老マルクスが水車小屋で待っています。", "마르쿠스는 방앗간에서 아일라를 만났습니다.", "The elder Marcus waits by the mill."):
        g1 = terimleri_gom((seg(m),), s.lookup_segments((seg(m),)))
        h2 = s.lookup_segments(g1)
        assert all(h.source_term == h.target_term == "Marcus" for h in h2) and len(h2) == 1
        assert terimleri_gom(g1, h2)[0].text == g1[0].text


def test_t4_gomulu_segment_tekrar_zincire_hedef_baska_terimin_kaynagi_sessiz_kayma(tmp_path: Path) -> None:
    """KOTU KULLANIM (belgeli sinirin ikinci yuzu): `マルクス->Marcus` + `Marcus->Marküs` semadan gecer; ikinci geciste
    `Marcus` -> `Marküs` SESSIZCE kayar (CV yok). Docstring yalniz `hedef ⊇ kaynak` buyumesini anar; bu sinif da ayni kural."""
    st = sozluk(tmp_path, [{"kaynak": "マルクス", "hedef": "Marcus"}, {"kaynak": "Marcus", "hedef": "Marküs"}])
    g1 = terimleri_gom((seg("マルクスが来た。"),), st.lookup_segments((seg("マルクスが来た。"),)))
    g2 = terimleri_gom(g1, st.lookup_segments(g1))
    assert g1[0].text == "Marcusが来た。" and g2[0].text == "Marküsが来た。"


def test_t4_kaydirilmis_segment_listesi_ayni_terim_ayni_konum_sessiz(s: GlossaryStore) -> None:
    """KOTU KULLANIM (cagiran hatasi, sozlesme goremez): `hits(A)` + `gom(B)` (B = A'nin permutasyonu) -- terim ayni konumda
    oldugu icin K2 tam-esitlik denetimi gecer, CV yok. Farkli konumda CV (pozitif kontrol)."""
    a = (seg("マルクスが来た。"), seg("マルクスは村にいます。"))
    hits = s.lookup_segments(a)
    b = (a[1], a[0])
    assert [x.text for x in terimleri_gom(b, hits)] == ["Marcusは村にいます。", "Marcusが来た。"]
    c2 = (a[1], seg("今日マルクスが来た。"))
    with pytest.raises(ContractViolation, match="source_term"):
        terimleri_gom(c2, hits)


@pytest.mark.parametrize("kayit,kabul", [
    ({"kaynak": ".", "hedef": "Nokta", "kisa_terim_izni": True}, False),
    ({"kaynak": "。", "hedef": "Nokta", "kisa_terim_izni": True}, False),
    ({"kaynak": "{", "hedef": "Küme", "kisa_terim_izni": True}, True),
    ({"kaynak": "{0}", "hedef": "Sıfır"}, True),
    ({"kaynak": "%s", "hedef": "Yüzde"}, True),
    ({"kaynak": "マルクス", "hedef": "Mar​cus"}, True),
    ({"kaynak": "マルクス", "hedef": "Marcus", "not": None}, True),
    ({"kaynak": "マ" * 100, "hedef": "X", "kisa_terim_izni": True}, True),
])
def test_t4_k6_kisa_izin_ve_yer_tutucu_bicimli_kaynak_ve_cf_hedef(tmp_path: Path, kayit: dict[str, object], kabul: bool) -> None:
    """K6 kenarlari: `kisa_terim_izni` terminatoru KURTARMAZ (red once); yer tutucu bicimli KAYNAK (`{0}`, `%s`) serbest (K3:
    cagiran bildirir); hedefte `Cf` (ZWSP) KABUL (D-A3 sinifi; `Cc` degil) -> model ZWSP'li terim gorur (dusuk, belge)."""
    if kabul:
        assert len(sozluk(tmp_path, [kayit])) == 1
    else:
        with pytest.raises(ValueError, match="cumle sonu"):
            sozluk(tmp_path, [kayit])


def test_t4_yer_tutucu_bicimli_kaynak_bildirilmemisse_gomulur_bildirilirse_korunur(tmp_path: Path) -> None:
    st = sozluk(tmp_path, [{"kaynak": "{0}", "hedef": "Sıfır"}, {"kaynak": "マルクス", "hedef": "Marcus"}])
    sg = seg("{0}マルクスは村にいます。")
    assert terimleri_gom((sg,), st.lookup_segments((sg,)))[0].text == "SıfırMarcusは村にいます。"
    sg2 = seg("{0}マルクスは村にいます。", ("{0}",))
    assert terimleri_gom((sg2,), st.lookup_segments((sg2,)))[0].text == "{0}Marcusは村にいます。"


def test_t4_elle_kurulan_hit_k6_semasini_atlar_terminatorlu_hedef_gomulur(s: GlossaryStore) -> None:
    """KOTU KULLANIM: `terimleri_gom` elle kurulan hit'in `target_term`ini K6 ile denetlemez (paket K2 yalniz bos/str-degil der):
    `Marcus.` gomulur -> T-007 parca sayisi 1 -> 2. Store uzerinden imkansiz (K6); pin + belge (dusuk)."""
    sg = seg("マルクスが来た。")
    g = terimleri_gom((sg,), (TermHit("マルクス", "Marcus.", 0, 4, 0),))[0]
    assert g.text == "Marcus.が来た。" and len(cumlelere_bol(g.text)) == 2 and len(cumlelere_bol(sg.text)) == 1
    with pytest.raises(ContractViolation, match="target_term"):
        terimleri_gom((sg,), (TermHit("マルクス", "", 0, 4, 0),))


def test_t4_ayni_hit_iki_kez_verilirse_contract_violation(s: GlossaryStore) -> None:
    sg = seg("マルクスが来た。")
    h = s.lookup_segments((sg,))
    with pytest.raises(ContractViolation, match="ortusuyor"):
        terimleri_gom((sg,), h + h)


# ---------------------------------------------------------------------------
# T5 -- K5 dusmanca zincir girdileri
# ---------------------------------------------------------------------------


DUSMANCA: dict[str, tuple[str, int]] = {
    "8000 gecerli": ("Marcus " * 8000, 8000),
    "8000 zincir sag olu": ("Marcus" * 8000 + "x", 0),
    "8000 zincir sol olu": ("x" + "Marcus" * 8000, 0),
    "4000x2 terim zincir olu": ("MarcusAyla" * 4000 + "x", 0),
    "windmill x4000 + s": ("windmill" * 4000 + "s", 0),
    "windmill x4000 bosluklu": ("windmill " * 4000, 8000),
    "yarim canli yarim olu": ("Marcus" * 4000 + " " + "Marcus" * 4000 + "x", 4000),
    "xMarcus x8000": ("xMarcus" * 8000, 0),
}


@pytest.mark.parametrize("ad", list(DUSMANCA))
def test_t5_k5_dusmanca_zincir_60ms(tmp_path: Path, ad: str) -> None:
    """▲ K5: 8000 uyeli gecerli/olu zincir < 60 ms (5 kosumun EN KUCUGU; izleyici aktifse 4x); olu yon hafizasi amortize dogrusal.
    Yalitilmis olcum ~19-23 ms (sonda; `tester_B_evidence/tur2/sonda3-*`)."""
    st = sozluk(tmp_path, [{"kaynak": "Marcus", "hedef": "Marcus"}, {"kaynak": "Ayla", "hedef": "Ayla"},
                           {"kaynak": "wind", "hedef": "Rüzgar"}, {"kaynak": "mill", "hedef": "Değirmen"}])
    metin, n = DUSMANCA[ad]
    pay = 4.0 if sys.gettrace() is not None else 1.0
    sureler: list[float] = []
    for _ in range(5):
        t0 = time.perf_counter()
        hits = st.lookup(metin)
        sureler.append((time.perf_counter() - t0) * 1000)
    assert len(hits) == n, ad
    # min: eszamanli model yuku (Tester-A) medyani 60 ms ustune itti (birlikte-kosum-tur2 ilk deneme); O(n^2) mutant (472 ms) yine yakalanir
    assert min(sureler) < 60 * pay, (ad, sureler)


# ---------------------------------------------------------------------------
# T6 -- zincir davranisi
# ---------------------------------------------------------------------------


def test_t6_zincir_windmill_bitisik_latin_gomme_belgeli(tmp_path: Path) -> None:
    """`windmill` -> `wind`+`mill` -> `RüzgarDeğirmen` (bitisik). Paket: 'yazar ikisini de istedi, belgelenir'. Gercek model (M6-1):
    'Rüzgar Değirmen dönüyor.' (ham 'Rüzgar değirmeni dönüyor.') -- ayiriyor, iyelik eki kayboluyor (kucuk bozulma; K4 cins isim).
    `windmills` 0 hit -> ham 'Rüzgar değirmenleri dönüyor.' DOGRU (zincir kurali dogru sinifi koruyor); tur-1 `Rüzgarmills` -> bozuk."""
    st = sozluk(tmp_path, [{"kaynak": "wind", "hedef": "Rüzgar"}, {"kaynak": "mill", "hedef": "Değirmen"}, {"kaynak": "old", "hedef": "Eski"},
                           {"kaynak": "millhouse", "hedef": "Değirmen Evi"}, {"kaynak": "house", "hedef": "Ev"}])
    def g(m: str) -> str:
        return terimleri_gom((seg(m),), st.lookup_segments((seg(m),)))[0].text
    assert g("The windmill turns.") == "The RüzgarDeğirmen turns."
    assert g("The windmills turn.") == "The windmills turn."
    assert g("oldmillhouse") == "EskiDeğirmen Evi"  # zincir icinde en uzun aday (`millhouse` > `mill`+`house`)
    assert g("windmillhouse") == "RüzgarDeğirmen Evi"
    assert g("windmillhouses") == "windmillhouses" and g("xwindmill") == "xwindmill"


def test_t6_zincir_reddedilen_aday_komsuya_sinir_vermez_betik_gecisi_verir(u: GlossaryStore) -> None:
    """Tur-1 O-B5 kapanisi: `長老Marcusa` -> `Marcus` yok (bu sozlukte), `長老` betik gecisiyle (Han|Latin) eslesir -- reddedilen
    aday degil gecis sinir verdi. `장로마르쿠스님` (Hangul|Hangul) zincir: ikisi de (dis uclar sinir)."""
    assert hedefler(u, "長老Marcusa") == ["İhtiyar"]
    assert hedefler(u, "장로마르쿠스님") == ["İhtiyar", "Marcus"]
    assert hedefler(u, "장로마르쿠스님이") == ["İhtiyar", "Marcus"]
    assert hedefler(u, "장로마르쿠스니") == []  # dis uc sinir degil -> zincirin HICBIR uyesi
    assert hedefler(u, "x장로마르쿠스") == ["İhtiyar", "Marcus"]  # sol dis uc betik gecisi


# ---------------------------------------------------------------------------
# T7 -- kapi (real_check v4) modelsiz denetim
# ---------------------------------------------------------------------------


def test_t7_kapi_kat_turkce_katlama_dogru() -> None:
    """Kapi `_kat` (K-B4 duzeltmesi): `İ`->`i`, `I`->`ı`, casefold. `İhtiyar` kucuk 'ihtiyar' ile esler; 'ı' 'i' ile KARISMAZ."""
    def _kat(t: str) -> str:
        return t.replace("İ", "i").replace("I", "ı").casefold()
    assert _kat("İhtiyar") == "ihtiyar" and _kat("ihtiyar") in _kat("bir İhtiyar geldi")
    assert _kat("Işık") == "ışık" and _kat("ışık") == "ışık"
    assert _kat("DEĞİRMEN") == "değirmen"


def test_t7_kapi_6_statik_sabitleri_kod_ile_ayni_ve_referans_bagimsiz(s: GlossaryStore, tmp_path: Path) -> None:
    """Kural 8: kapinin #6 beklentileri (0/2/2/1/0) sabit literal, uygulamadan turetilmiyor; kod ayni degerleri veriyor."""
    g6 = sozluk(tmp_path, [{"kaynak": "wind", "hedef": "Rüzgar"}, {"kaynak": "mill", "hedef": "Değirmen"}])
    assert (len(g6.lookup("The windmills turn.")), len(g6.lookup("The windmill turns.")), len(s.lookup("マルクスアイラ")),
            len(s.lookup("長老マルクス")), len(s.lookup("マルクスタウン"))) == (0, 2, 2, 1, 0)
    kaynak = (KOK / ".agents" / "tasks" / "T-011" / "real_check.py").read_text(encoding="utf-8")
    assert "n_wms == 0 and n_wm == 2 and n_adad == 2" in kaynak and "n_kanji_ad == 1 and n_kata_kata == 0" in kaynak


def test_t7_kapi_5c_or_gevsek_iki_dil_ayri_ayri_pozitif_kontrol_olmali() -> None:
    """KAPI BULGUSU: #5c `"Marcus" not in h_jp or "Marcus" not in h_kr` -- iki dilden BIRI hamda adsizsa gecer; #5b ikisini de
    ister. Pozitif kontrol dil basina olmali (`and`). Bugun ikisi de True (M6-5c) -> `and` de gecer; gevseklik gelecege donuk."""
    kaynak = (KOK / ".agents" / "tasks" / "T-011" / "real_check.py").read_text(encoding="utf-8")
    assert '"Marcus" not in h_jp or "Marcus" not in h_kr' in kaynak


def test_t7_kapi_4b_ihtiyar_sarti_hama_gore_degil_mutlak() -> None:
    """KAPI BULGUSU: #4b `"ihtiyar" in _kat(bg)` MUTLAK sart; model unvani 'yaşlı' cevirirse ham da gomulu de 'ihtiyar'siz
    olur ve kapi yanlis IHLAL verir (M3-0: JP tarafinda ayni cumle sinifi 'İhtiyar' -> 'Yaşlı' oynadi). Sart hama GORELI olmali."""
    kaynak = (KOK / ".agents" / "tasks" / "T-011" / "real_check.py").read_text(encoding="utf-8")
    assert 'and "ihtiyar" in _kat(bg)' in kaynak and "'ihtiyar' in _kat(bh)" in kaynak  # ham olculuyor ama sarta girmiyor


# ---------------------------------------------------------------------------
# T8 -- demo (sef K-B7 duzeltmesi) statik denetim
# ---------------------------------------------------------------------------


def test_t8_demo_translatorerror_yakalar_ve_kimlik_hiti_suzer() -> None:
    """K-B7 kapanisi: `except TranslatorError` cevir cagrisini sarar; sayac `h.target_term != h.source_term` ile suzer;
    `GlossaryStore` sema hatasi (`ValueError`) baslangicta acik (belgeli yorum). PySide6 import edilmez (metin okunur)."""
    kaynak = DEMO_PY.read_text(encoding="utf-8")
    assert "except TranslatorError" in kaynak
    assert "h.target_term != h.source_term" in kaynak
    m = re.search(r"try:\s*\n\s*gomulu, ceviriler, terimler = self\._cevirici\.cevir\(.*?\n\s*except TranslatorError", kaynak, re.S)
    assert m is not None
    assert "ValueError, açık" in kaynak or "ValueError" in kaynak


def test_t8_demo_ceviri_hatasinda_isliyor_bayragi_sifirlanir() -> None:
    """Pencere donmasi (K-B7): hata yolunda da `bitti.emit` cagrilir -> `_bitti` `_isliyor = False` yapar."""
    kaynak = DEMO_PY.read_text(encoding="utf-8")
    hata_blok = kaynak.split("except TranslatorError", 1)[1].split("return", 1)[0]
    assert "self.bitti.emit(" in hata_blok
    assert "self._isliyor = False" in kaynak.split("def _bitti", 1)[1]
