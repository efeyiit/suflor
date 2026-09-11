"""T-011 -- `GlossaryStore` / `terimleri_gom` birim testleri (gercek model YOK).

Sozluk her testte `tmp_path` altina JSON olarak yazilir ve `GlossaryStore`
ile yuklenir; `.agents/` altindaki fixture OKUNMAZ. Referanslar BAGIMSIZ
kanaldan (PROTOKOL 4.6/8): paket v2'nin K1-K7 OLCU satirlari, olgular G5/G6
ve fixture v2'nin terim listesi burada SABIT yazilidir -- modulun kendi
tablolarindan (parcacik/ek kumesi, terminator kumesi) TURETILMEZ.

Her OLCU ornegi AYRI test kimligiyle gorunur (`pytest.param(..., id=)`):
T-007'de "4/6 nokta" dersi -- tek parametrize icinde kaybolan ornek
olculmemis sayilir.

Ceviri/kaynak metni hicbir yere basilmaz (PROTOKOL 7); `print` yok. K5
kanal olcusu nobetciyi segment metnine koyar ve `capfd`/`caplog`/`warnings`
ile sifir sizinti dogrular; konsola ULASMAZ.
"""
from __future__ import annotations

import ast
import dataclasses
import json
import logging
import re
import statistics
import sys
import time
import unicodedata
import warnings
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pytest

from src.contracts.errors import ContractViolation, TranslatorError
from src.contracts.models import Rect, Segment, TermHit
from src.translate import sozluk
from src.translate.sozluk import GlossaryStore, SozlukTerimi, ilk_harfi_buyut, terimleri_gom

KAYNAK = Path(sozluk.__file__)

# --- BAGIMSIZ referanslar (paket v2, olgular G5/G6, fixture v2) ------------------

FIXTURE_V2: tuple[tuple[str, str], ...] = (
    ("マルクス", "Marcus"), ("마르쿠스", "Marcus"), ("Marcus", "Marcus"),
    ("アイラ", "Ayla"), ("아일라", "Ayla"),
    ("水車小屋", "Değirmen"), ("방앗간", "Değirmen"), ("mill", "Değirmen"),
    ("長老", "İhtiyar"), ("장로", "İhtiyar"), ("elder", "İhtiyar"),
)
"""Kapinin fixture v2 terim listesi -- yalniz motorun YANLIS cevirdigi terimler (Y3)."""

TERMINATORLER: tuple[str, ...] = (".", "!", "?", "。", "！", "？")
"""K6: hedefte yasak cumle sonu kumesi -- T-007 K3 kumesiyle ayni; paket metninden SABIT."""

JP_PARCACIKLAR: tuple[str, ...] = tuple("をがはにのでともへや")
"""K1 sinir: JP parcaciklar -- paket K1 metninden SABIT."""

KR_EKLER: tuple[str, ...] = (
    "을", "를", "이", "가", "은", "는", "에", "에서", "으로", "로", "와", "과", "도", "의", "만", "께서", "부터", "까지",
)
"""K1 sinir: KR ekler -- paket K1 metninden SABIT (G6)."""

NOBETCI = "NOBETCI-METIN-7f3a"
"""K5/PROTOKOL 7: segment metnine konan nobetci; hicbir kanala ve hata mesajina sizmamali."""

BBOX = Rect(10, 20, 300, 40, monitor_index=1, dpi_scale=1.5)


# --- yardimcilar --------------------------------------------------------------------


def _json_yaz(yol: Path, veri: object) -> Path:
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(json.dumps(veri, ensure_ascii=False), encoding="utf-8")
    return yol


def sozluk_dosyasi(tmp_path: Path, terimler: Sequence[object], ad: str = "sozluk.json") -> Path:
    """`terimler`: `(kaynak, hedef)` ciftleri ya da ham sozluk kayitlari."""
    kayitlar: list[object] = []
    for t in terimler:
        if isinstance(t, tuple):
            kayitlar.append({"kaynak": t[0], "hedef": t[1]})
        else:
            kayitlar.append(t)
    return _json_yaz(tmp_path / "çeviri" / ad, {"terimler": kayitlar})


def store(tmp_path: Path, terimler: Sequence[object], ad: str = "sozluk.json") -> GlossaryStore:
    return GlossaryStore(sozluk_dosyasi(tmp_path, terimler, ad))


def izinli(kaynak: str, hedef: str) -> dict[str, object]:
    return {"kaynak": kaynak, "hedef": hedef, "kisa_terim_izni": True}


def fixture_store(tmp_path: Path) -> GlossaryStore:
    return store(tmp_path, FIXTURE_V2)


def seg(metin: str, **ek: Any) -> Segment:
    return Segment(text=metin, bbox=BBOX, **ek)


def hit(kaynak: str, hedef: str, start: int, end: int, idx: int | None = 0, note: str | None = None) -> TermHit:
    return TermHit(source_term=kaynak, target_term=hedef, start=start, end=end, segment_index=idx, note=note)


def araliklar(hits: Sequence[TermHit]) -> list[tuple[int, int]]:
    return [(h.start, h.end) for h in hits]


def _modul_agaci() -> ast.Module:
    return ast.parse(KAYNAK.read_text(encoding="utf-8"))


def _fonksiyon(agac: ast.AST, ad: str) -> ast.FunctionDef:
    for d in ast.walk(agac):
        if isinstance(d, ast.FunctionDef) and d.name == ad:
            return d
    raise AssertionError(f"fonksiyon yok: {ad}")


def _cagri_adlari(dugum: ast.AST) -> set[str]:
    return {ast.unparse(d.func) for d in ast.walk(dugum) if isinstance(d, ast.Call)}


def _import_kokleri(dugum: ast.AST) -> set[str]:
    kokler: set[str] = set()
    for d in ast.walk(dugum):
        if isinstance(d, ast.Import):
            kokler.update(a.name.split(".")[0] for a in d.names)
        elif isinstance(d, ast.ImportFrom):
            kokler.add((d.module or "").split(".")[0])
    return kokler


# ===========================================================================
# K1 -- esleme: en uzun once, ortusmesiz, sinir kurali her betikte ayni
# ===========================================================================


@pytest.mark.parametrize(
    ("terimler", "metin"),
    [
        pytest.param([izinli("村", "Köy")], "村人", id="JP-村人-bilesik-kanji"),
        pytest.param([izinli("剣", "Kılıç")], "剣士", id="JP-剣士-bilesik-kanji"),
        pytest.param([izinli("검", "Kılıç")], "검사", id="KR-검사-bilesik-hece"),
        pytest.param([("방앗간", "Değirmen")], "방앗간집", id="KR-방앗간집-bilesik"),
        pytest.param([izinli("剣", "Kılıç")], "真剣に", id="JP-真剣に-on-bilesik"),
        pytest.param([izinli("村", "Köy")], "中村", id="JP-中村-soyadi"),
        pytest.param([("mill", "Değirmen")], "windmill", id="EN-windmill-on-bilesik"),
        pytest.param([("mill", "Değirmen")], "millstone", id="EN-millstone-son-bilesik"),
        pytest.param([("elder", "İhtiyar")], "elders", id="EN-elders-cogul"),
        pytest.param([("방앗간", "Değirmen")], "방앗간도둑", id="KR-방앗간도둑-ek-baska-kelimenin-basi"),
        pytest.param([("장로", "İhtiyar")], "의장로", id="KR-의장로-sol-hece"),
        pytest.param([("マルクス", "Marcus")], "マルクスマン", id="JP-マルクスマン-katakana-devam"),
        pytest.param([("Marcus", "Marcus")], "Marcus2", id="EN-Marcus2-rakam-devam"),
    ],
)
def test_k1_sinir_negatif_eslesmez(tmp_path: Path, terimler: list[object], metin: str) -> None:
    """G5/G6 + KRT Y1: bilesik icinde gecen terim ESLESMEZ (her iki ucta sinir sarti)."""
    assert store(tmp_path, terimler).lookup(metin) == []


@pytest.mark.parametrize(
    ("terimler", "metin", "aralik"),
    [
        pytest.param([izinli("村", "Köy")], "村は", (0, 1), id="JP-村は-parcacik-は"),
        pytest.param([izinli("剣", "Kılıç")], "剣を", (0, 1), id="JP-剣を-parcacik-を"),
        pytest.param([izinli("검", "Kılıç")], "검을", (0, 1), id="KR-검을-ek-을"),
        pytest.param([("방앗간", "Değirmen")], "방앗간에서", (0, 3), id="KR-방앗간에서-ek-에서"),
        pytest.param([("방앗간", "Değirmen")], "방앗간을 지나", (0, 3), id="KR-방앗간을-지나-ek+bosluk"),
        pytest.param([("방앗간", "Değirmen")], "방앗간에서는", (0, 3), id="KR-방앗간에서는-ek-zinciri"),
        pytest.param([("방앗간", "Değirmen")], "방앗간까지는.", (0, 3), id="KR-방앗간까지는-ek-zinciri+nokta"),
        pytest.param([("Marcus", "Marcus")], "Marcusが", (0, 6), id="Latin+JP-Marcusが-parcacik"),
        pytest.param([("Marcus", "Marcus")], "Marcus가", (0, 6), id="Latin+KR-Marcus가-ek"),
        pytest.param([("Marcus", "Marcus")], "Marcus", (0, 6), id="EN-Marcus-metin-ucu"),
        pytest.param([("mill", "Değirmen")], "mill-house", (0, 4), id="EN-mill-house-tire-Pd"),
        pytest.param([("mill", "Değirmen")], "Mill's", (0, 4), id="EN-Mill's-kesme-Po"),
        pytest.param([("mill", "Değirmen")], "(mill)", (1, 5), id="EN-(mill)-parantez-Ps/Pe"),
        pytest.param([("mill", "Değirmen")], "by the mill.", (7, 11), id="EN-by-the-mill.-bosluk+nokta"),
        pytest.param([izinli("村", "Köy")], "私が村に", (2, 3), id="JP-私が村に-sol-parcacik"),
        pytest.param([("マルクス", "Marcus")], "「マルクス」", (1, 5), id="JP-「マルクス」-CJK-tirnak"),
        pytest.param([("マルクス", "Marcus")], "マルクス、", (0, 4), id="JP-マルクス、-CJK-virgul"),
        pytest.param([("マルクス", "Marcus")], "マルクス。", (0, 4), id="JP-マルクス。-CJK-nokta"),
        pytest.param([("Marcus", "Marcus")], "“Marcus”", (1, 7), id="EN-tipografik-tirnak-Pi/Pf"),
        pytest.param([("Marcus", "Marcus")], "Marcus　", (0, 6), id="EN-ideografik-bosluk-Zs"),
        pytest.param([("Marcus", "Marcus")], "Marcus\n", (0, 6), id="EN-satir-sonu"),
    ],
)
def test_k1_sinir_pozitif_eslesir(tmp_path: Path, terimler: list[object], metin: str, aralik: tuple[int, int]) -> None:
    """G6: terimden once/sonra metin ucu, bosluk, P* noktalama, JP parcacik ya da KR ek varsa ESLESIR."""
    hits = store(tmp_path, terimler).lookup(metin)
    assert araliklar(hits) == [aralik]
    assert hits[0].source_term == metin[aralik[0]:aralik[1]]


@pytest.mark.parametrize("parcacik", JP_PARCACIKLAR, ids=[f"U+{ord(p):04X}" for p in JP_PARCACIKLAR])
def test_k1_her_jp_parcacik_tek_basina_sinir(tmp_path: Path, parcacik: str) -> None:
    """Paketin JP parcacik kumesinin HER uyesi ayri olculur (T-007 '4/6 nokta' dersi)."""
    s = store(tmp_path, [("マルクス", "Marcus")])
    assert araliklar(s.lookup("マルクス" + parcacik + "行く")) == [(0, 4)]


@pytest.mark.parametrize("ek", KR_EKLER)
def test_k1_her_kr_ek_tek_basina_sinir(tmp_path: Path, ek: str) -> None:
    """Paketin KR ek kumesinin HER uyesi ayri olculur; ekten sonra metin ucu."""
    s = store(tmp_path, [("방앗간", "Değirmen")])
    assert araliklar(s.lookup("방앗간" + ek)) == [(0, 3)]


def test_k1_kr_ek_kumesi_disi_hece_sinir_degil(tmp_path: Path) -> None:
    """Pozitif kontrol: ek kumesine girmeyen bir hece (집) sinir sayilmaz -- ek olcusu gercekten ayirt ediyor."""
    s = store(tmp_path, [("방앗간", "Değirmen")])
    assert s.lookup("방앗간집") == []
    assert araliklar(s.lookup("방앗간을")) == [(0, 3)]


def test_k1_kr_ek_zinciri_iki_ekle_sinirli(tmp_path: Path) -> None:
    """Ek zinciri en fazla IKI ek: uc ek ust uste sinir sayilmaz (kural sinirini sabitler)."""
    s = store(tmp_path, [("방앗간", "Değirmen")])
    assert araliklar(s.lookup("방앗간에서는")) == [(0, 3)]
    assert s.lookup("방앗간에서는도") == []


def test_k1_검은_옷_izinsiz_sema_reddi_eslesme_yok(tmp_path: Path) -> None:
    """OLCU '검은 옷 -> eslesmez': tek heceli `검` izinsiz SEMADA reddedilir; sozluk kurulamaz, hit yok."""
    with pytest.raises(ValueError, match="검"):
        store(tmp_path, [("검", "Kılıç")])


def test_k1_검은_옷_izinle_bilinen_sinir_eslesir(tmp_path: Path) -> None:
    """Bilinen sinir (K1 metni, real_check #6c): `검`+gercek ek `은` kuraldan GECER -- ek kurali ayristiramaz."""
    s = store(tmp_path, [izinli("검", "Kılıç")])
    assert araliklar(s.lookup("검은 옷")) == [(0, 1)]


def test_k1_bitisik_iki_terim_長老マルクス_iki_hit(tmp_path: Path) -> None:
    """G6 ek kural: sozlukteki baska terimin baslangici/bitisi sinirdir -> unvan + ad ikisi de eslesir."""
    hits = fixture_store(tmp_path).lookup("長老マルクス")
    assert araliklar(hits) == [(0, 2), (2, 6)]
    assert [h.target_term for h in hits] == ["İhtiyar", "Marcus"]


def test_k1_bitisik_iki_terim_ters_sirada_マルクス長老_iki_hit(tmp_path: Path) -> None:
    """Komsu terim siniri isleme sirasindan bagimsiz: uzun terim once islenirken kisa komsu henuz kabul edilmemis olsa da sinirdir."""
    assert araliklar(fixture_store(tmp_path).lookup("マルクス長老")) == [(0, 4), (4, 6)]


def test_k1_komsu_terim_siniri_yalniz_sozluk_terimi_icin(tmp_path: Path) -> None:
    """Pozitif kontrol: bitisik parca sozlukte DEGILSE sinir olusmaz (`長老会` -> hit yok)."""
    assert fixture_store(tmp_path).lookup("長老会") == []


def test_k1_장로_마르쿠스_iki_hit_start_artan(tmp_path: Path) -> None:
    """Uzun terim once islenir (마르쿠스), donus yine `start` ARTAN siralidir."""
    hits = fixture_store(tmp_path).lookup("장로 마르쿠스")
    assert araliklar(hits) == [(0, 2), (3, 7)]
    assert [h.source_term for h in hits] == ["장로", "마르쿠스"]


@pytest.mark.parametrize("sira", ["uzun-once", "kisa-once"])
def test_k1_en_uzun_once_水車小屋_yalniz_uzun(tmp_path: Path, sira: str) -> None:
    """`水車小屋` + `水車`: yalniz uzun; JSON sirasi sonucu degistirmez."""
    terimler = [("水車小屋", "Değirmen"), ("水車", "Çark")]
    if sira == "kisa-once":
        terimler.reverse()
    hits = store(tmp_path, terimler).lookup("水車小屋を過ぎて")
    assert araliklar(hits) == [(0, 4)]
    assert hits[0].target_term == "Değirmen"


def test_k1_en_uzun_once_kisa_terim_gecerli_sinirda_da_atlanir(tmp_path: Path) -> None:
    """Kisa terim KENDI sinirlarini saglasa da (`Marcus` + bosluk) uzun terimle ortustugu icin atlanir.

    Soldan-en-uzun/kisa-once tarama burada `Marcus`i alir ve uzunu kacirir -- global uzunluk sirasini ayirt eder.
    """
    s = store(tmp_path, [("Marcus", "Marcus"), ("Marcus Aurelius", "Marcus Aurelius")])
    hits = s.lookup("Marcus Aurelius geldi")
    assert araliklar(hits) == [(0, 15)]


def test_k1_en_uzun_once_harf_durumu_farkli_onek_terimleri(tmp_path: Path) -> None:
    """`Marcus` + `marcus aurelius` (ilk harf durumu farkli): IGNORECASE metinde UZUN olan bulunur.

    Terimleri harf durumuna gore ayri dallara koyan tarama ilk dalda `Marcus`ta durur ve uzun terimi kacirir.
    """
    s = store(tmp_path, [("Marcus", "Marcus"), ("marcus aurelius", "Marcus Aurelius")])
    assert araliklar(s.lookup("MARCUS AURELIUS geldi")) == [(0, 15)]
    assert araliklar(s.lookup("marcus Aurelius geldi")) == [(0, 15)]
    assert araliklar(s.lookup("Marcus geldi")) == [(0, 6)]
    s2 = store(tmp_path, [("mill", "Değirmen"), ("Mill House", "Değirmen Evi")], "b.json")
    assert araliklar(s2.lookup("the MILL HOUSE")) == [(4, 14)]
    # uc terim, iki harf durumu: en uzun (`M...`) dali once denenir, geri sarinca ayni daldaki kisa `Marcus`ta
    # DURAN tarama `m...` dalindaki orta uzunluktaki terimi kacirir.
    s3 = store(tmp_path, [("Marcus", "A"), ("marcus aurelius", "B"), ("MARCUS AURELIUS ANTONINUS", "C")], "c.json")
    hits = s3.lookup("marcus aurelius geldi")
    assert araliklar(hits) == [(0, 15)] and hits[0].target_term == "B"


def test_k1_en_uzun_once_soldan_tarama_degil_old_mill_house(tmp_path: Path) -> None:
    """Global uzunluk-azalan: `mill house` (10) `old mill` (8)'den once; soldan tarama `old mill`i alirdi."""
    s = store(tmp_path, [("old mill", "Eski Değirmen"), ("mill house", "Değirmen Evi")])
    hits = s.lookup("old mill house")
    assert araliklar(hits) == [(4, 14)]
    assert hits[0].target_term == "Değirmen Evi"


def test_k1_en_uzun_once_uzun_reddedilince_ayni_konumdaki_kisa_denenir(tmp_path: Path) -> None:
    """Ayni baslangicta uzun terim SINIRDAN duserse (`Marcus Aureliusa`: sag `a`), kisa (`Marcus`) yine bulunur.

    Konum basina yalniz en uzun adayi tutan uygulama burada hit uretmez.
    """
    s = store(tmp_path, [("Marcus", "Marcus"), ("Marcus Aurelius", "Marcus Aurelius")])
    assert araliklar(s.lookup("Marcus Aureliusa geldi")) == [(0, 6)]
    assert araliklar(s.lookup("Marcus Aurelio geldi")) == [(0, 6)]


def test_k1_esit_uzunlukta_ortusme_soldaki_kazanir_json_sirasindan_bagimsiz(tmp_path: Path) -> None:
    """Esit uzunlukta, sinirlari gecerli, ortusen iki aday: kucuk `start` kazanir; JSON sirasi degistirmez (KRT O6)."""
    a = store(tmp_path, [("old mill", "A"), ("mill run", "B")], "a.json").lookup("old mill run")
    b = store(tmp_path, [("mill run", "B"), ("old mill", "A")], "b.json").lookup("old mill run")
    assert araliklar(a) == araliklar(b) == [(0, 8)]
    assert a[0].target_term == b[0].target_term == "A"


def test_k1_cjk_kismi_ortusme_sinirsiz_ikisi_de_duser(tmp_path: Path) -> None:
    """`水車小`: `水車`@0 sag=`小` sinir degil, `車小`@1 sol=`水` sinir degil -> ikisi de duser (komsu terim siniri BASLANGIC/BITIS ister, ortusme degil)."""
    s = store(tmp_path, [("水車", "A"), ("車小", "B")])
    assert s.lookup("水車小 ") == []
    assert araliklar(s.lookup("水車 小")) == [(0, 2)]


@pytest.mark.parametrize("metin", ["MARCUS", "marcus", "Marcus", "mArCuS"])
def test_k1_latin_buyuk_kucuk_duyarsiz(tmp_path: Path, metin: str) -> None:
    hits = fixture_store(tmp_path).lookup(metin)
    assert araliklar(hits) == [(0, 6)]
    assert hits[0].source_term == metin  # metindeki dilim, sozluk anahtari degil
    assert hits[0].target_term == "Marcus"


def test_k1_casefold_tuzagi_İstanbul_indeksler_orijinal_metne_gore(tmp_path: Path) -> None:
    """KRT O2: `İ`/`ﬁ` casefold'da genisler (22 -> 24 kodpoint); indeksler ORIJINAL metne ait olmali."""
    metin = "The ﬁne İstanbul mill."
    assert len(metin.casefold()) != len(metin)  # tuzak gercekten kurulu
    hits = fixture_store(tmp_path).lookup(metin)
    assert araliklar(hits) == [(17, 21)]
    assert metin[17:21] == "mill"


def test_k1_turkce_noktali_I_sinifi_karsilikli_eslesir(tmp_path: Path) -> None:
    """`i`/`I`/`İ`/`ı` tek sinif (KRT O2 olcumu): sozluk `istanbul`, metin `İstanbul` -> eslesir, indeks 0..8."""
    s = store(tmp_path, [("istanbul", "İstanbul")])
    assert araliklar(s.lookup("İstanbul burada")) == [(0, 8)]
    assert araliklar(s.lookup("ISTANBUL")) == [(0, 8)]


def test_k1_ayni_terim_n_gecis_n_hit_start_artan_segment_index_none(tmp_path: Path) -> None:
    metin = "Marcus, Marcus and MARCUS"
    hits = fixture_store(tmp_path).lookup(metin)
    assert araliklar(hits) == [(0, 6), (8, 14), (19, 25)]
    assert all(h.segment_index is None for h in hits)
    assert all(h.target_term == "Marcus" for h in hits)


def test_k1_indeks_kodpoint_astral_karakter(tmp_path: Path) -> None:
    """Indeks kodpoint sayar: astral (BMP disi) karakter 1 kodpoint."""
    metin = "\U0001F600 Marcus"
    hits = fixture_store(tmp_path).lookup(metin)
    assert araliklar(hits) == [(2, 8)]
    assert metin[2:8] == "Marcus"


def test_k1_bos_sozluk_bos_liste(tmp_path: Path) -> None:
    s = store(tmp_path, [])
    assert s.lookup("長老マルクスが待っています。") == []
    assert len(s) == 0


def test_k1_bos_metin_bos_liste(tmp_path: Path) -> None:
    assert fixture_store(tmp_path).lookup("") == []


def test_k1_terim_icermeyen_metin_bos_liste(tmp_path: Path) -> None:
    assert fixture_store(tmp_path).lookup("日が暮れたら道を外れないように。") == []


def test_k1_yer_tutucu_ucu_sinirdir(tmp_path: Path) -> None:
    """Korunan aralik (yer tutucu) ucu sinir sayilir: `%sマルクス` -> hit; bildirilmemisken `s` harf -> hit YOK."""
    s = fixture_store(tmp_path)
    assert araliklar(s.lookup("%sマルクス", ("%s",))) == [(2, 6)]
    assert s.lookup("%sマルクス") == []


def test_k1_kaynakta_kelime_siniri_metakarakteri_yok() -> None:
    """K1: `\\b` kullanilmaz (CJK'da Latin+parcacik eslesmez) -- kaynak dosyada gecmez."""
    assert "\\b" not in KAYNAK.read_text(encoding="utf-8")


@pytest.mark.parametrize("kotu", [None, 5, b"Marcus", ["Marcus"]])
def test_k1_lookup_text_str_degil_typeerror(tmp_path: Path, kotu: object) -> None:
    with pytest.raises(TypeError):
        fixture_store(tmp_path).lookup(kotu)  # type: ignore[arg-type]


@pytest.mark.parametrize("kotu", ["{0}", (1,), [None]])
def test_k1_lookup_placeholders_bicimi_typeerror(tmp_path: Path, kotu: object) -> None:
    """`placeholders` str dizisi olmali; duz `str` (karakterlere bolunur) ve str olmayan oge reddedilir."""
    with pytest.raises(TypeError):
        fixture_store(tmp_path).lookup("Marcus", kotu)  # type: ignore[arg-type]


def test_k1_lookup_segments_segment_index_doldurur(tmp_path: Path) -> None:
    """`lookup_segments`: her segmentin `placeholders`i ile arar, `segment_index` doldurur, start artan."""
    s = fixture_store(tmp_path)
    segs = (seg("長老マルクス"), seg("{PLAYER}は村にいます", placeholders=("{PLAYER}",)), seg("장로 마르쿠스"))
    s2 = store(tmp_path, [*FIXTURE_V2, ("PLAYER", "Oyuncu")], "yt.json")
    hits = s2.lookup_segments(segs)
    assert [(h.segment_index, h.start, h.end) for h in hits] == [(0, 0, 2), (0, 2, 6), (2, 0, 2), (2, 3, 7)]
    assert s.lookup_segments(()) == ()
    assert terimleri_gom(segs, hits)[1] is segs[1]


# ===========================================================================
# K2 -- gomme: aralik disi karakter dokunulmaz; hits gecersizse ContractViolation
# ===========================================================================


def test_k2_ek_korunur_방앗간을_지나(tmp_path: Path) -> None:
    s = fixture_store(tmp_path)
    segs = (seg("방앗간을 지나", speaker="장로", placeholders=("{0}",), source_blocks=(3, 4)),)
    hits = tuple(dataclasses.replace(h, segment_index=0) for h in s.lookup(segs[0].text, segs[0].placeholders))
    out = terimleri_gom(segs, hits)
    assert out[0].text == "Değirmen을 지나"
    assert (out[0].bbox, out[0].speaker, out[0].placeholders, out[0].source_blocks) == (BBOX, "장로", ("{0}",), (3, 4))


@pytest.mark.parametrize(
    ("metin", "beklenen"),
    [
        pytest.param("長老マルクス", "İhtiyarMarcus", id="JP-長老マルクス"),
        pytest.param("マルクスがあなたを待っています。", "Marcusがあなたを待っています。", id="JP-マルクスが"),
        pytest.param("水車小屋を過ぎて東の道を行きなさい。", "Değirmenを過ぎて東の道を行きなさい。", id="JP-水車小屋を"),
        pytest.param("장로 마르쿠스", "İhtiyar Marcus", id="KR-장로-마르쿠스"),
        pytest.param("방앗간을 지나 동쪽 길로 가십시오.", "Değirmen을 지나 동쪽 길로 가십시오.", id="KR-방앗간을"),
        pytest.param("The elder Marcus waits by the mill.", "The İhtiyar Marcus waits by the Değirmen.", id="EN-elder-Marcus-mill"),
    ],
)
def test_k2_g1_cumleleri_lookup_gom_zinciri(tmp_path: Path, metin: str, beklenen: str) -> None:
    """G1'in alti cumlesi: lookup -> gom; aralik disi her karakter aynen (real_check #1'in gomme yarisi)."""
    s = fixture_store(tmp_path)
    segs = (seg(metin),)
    hits = tuple(dataclasses.replace(h, segment_index=0) for h in s.lookup(metin))
    assert terimleri_gom(segs, hits)[0].text == beklenen


def test_k2_iki_hit_basta_ve_sonda_start_azalan_uygulama(tmp_path: Path) -> None:
    """Hedef uzunlugu kaynaktan farkli (mill 4 -> Değirmen 8): start-ARTAN uygulama ikinci hiti kaydirir."""
    segs = (seg("mill road ends at the elder"),)
    hits = (hit("mill", "Değirmen", 0, 4), hit("elder", "İhtiyar", 22, 27))
    assert terimleri_gom(segs, hits)[0].text == "Değirmen road ends at the İhtiyar"


def test_k2_ayni_segmentte_uc_hit_farkli_uzunluklar(tmp_path: Path) -> None:
    segs = (seg("マルクスは水車小屋で長老を待つ"),)
    hits = (hit("マルクス", "Marcus", 0, 4), hit("水車小屋", "Değirmen", 5, 9), hit("長老", "İhtiyar", 10, 12))
    assert terimleri_gom(segs, hits)[0].text == "MarcusはDeğirmenでİhtiyarを待つ"


def test_k2_hitler_verilis_sirasindan_bagimsiz(tmp_path: Path) -> None:
    segs = (seg("mill road ends at the elder"),)
    a = terimleri_gom(segs, (hit("mill", "Değirmen", 0, 4), hit("elder", "İhtiyar", 22, 27)))
    b = terimleri_gom(segs, (hit("elder", "İhtiyar", 22, 27), hit("mill", "Değirmen", 0, 4)))
    assert a == b


def test_k2_coklu_segment_hitler_dogru_segmente(tmp_path: Path) -> None:
    segs = (seg("Marcus here"), seg("no term"), seg("by the mill"))
    hits = (hit("mill", "Değirmen", 7, 11, idx=2), hit("Marcus", "Marcus", 0, 6, idx=0))
    out = terimleri_gom(segs, hits)
    assert [o.text for o in out] == ["Marcus here", "no term", "by the Değirmen"]
    assert out[1] is segs[1]
    assert len(out) == 3


def test_k2_tutarsiz_source_term_contract_violation(tmp_path: Path) -> None:
    """`text[start:end] != source_term` -> ContractViolation (sessiz kayma yok)."""
    segs = (seg("by the mill"),)
    with pytest.raises(ContractViolation):
        terimleri_gom(segs, (hit("mill", "Değirmen", 6, 10),))  # bir kaymis


def test_k2_source_term_buyuk_kucuk_farki_da_tutarsizliktir(tmp_path: Path) -> None:
    """Denetim TAM esitliktir: `source_term` metindeki dilim olmali (lookup oyle uretir)."""
    segs = (seg("by the MILL"),)
    with pytest.raises(ContractViolation):
        terimleri_gom(segs, (hit("mill", "Değirmen", 7, 11),))
    assert terimleri_gom(segs, (hit("MILL", "Değirmen", 7, 11),))[0].text == "by the Değirmen"


@pytest.mark.parametrize(
    ("start", "end"),
    [
        pytest.param(-1, 4, id="start-negatif"),
        pytest.param(7, 12, id="end-metin-disi"),
        pytest.param(7, 7, id="start==end-bos-aralik"),
        pytest.param(11, 7, id="start>end"),
    ],
)
def test_k2_aralik_disi_contract_violation(tmp_path: Path, start: int, end: int) -> None:
    segs = (seg("by the mill"),)
    with pytest.raises(ContractViolation):
        terimleri_gom(segs, (hit(segs[0].text[max(start, 0):max(end, 0)], "Değirmen", start, end),))


def test_k2_ortusen_hitler_contract_violation(tmp_path: Path) -> None:
    segs = (seg("水車小屋を"),)
    hits = (hit("水車小屋", "Değirmen", 0, 4), hit("水車", "Çark", 0, 2))
    with pytest.raises(ContractViolation):
        terimleri_gom(segs, hits)


def test_k2_kismen_ortusen_hitler_contract_violation(tmp_path: Path) -> None:
    segs = (seg("水車小屋を"),)
    hits = (hit("水車小", "A", 0, 3), hit("小屋", "B", 2, 4))
    with pytest.raises(ContractViolation):
        terimleri_gom(segs, hits)


def test_k2_bitisik_hitler_ortusme_degil(tmp_path: Path) -> None:
    """`a.end == b.start` ortusme DEGILDIR (長老|マルクス)."""
    segs = (seg("長老マルクス"),)
    hits = (hit("長老", "İhtiyar", 0, 2), hit("マルクス", "Marcus", 2, 6))
    assert terimleri_gom(segs, hits)[0].text == "İhtiyarMarcus"


def test_k2_bos_hits_ayni_segment_nesneleri_is(tmp_path: Path) -> None:
    segs = [seg("Marcus"), seg("mill")]
    out = terimleri_gom(segs, ())
    assert isinstance(out, tuple) and len(out) == 2
    assert out[0] is segs[0] and out[1] is segs[1]


def test_k2_bos_segments_bos_hits_bos_tuple(tmp_path: Path) -> None:
    assert terimleri_gom((), ()) == ()


def test_k2_bos_segments_dolu_hits_contract_violation(tmp_path: Path) -> None:
    with pytest.raises(ContractViolation):
        terimleri_gom((), (hit("Marcus", "Marcus", 0, 6),))


def test_k2_bos_target_term_contract_violation(tmp_path: Path) -> None:
    """Bos hedef terim gommek terimi SILER -- sessiz kayip yerine ihlal."""
    with pytest.raises(ContractViolation):
        terimleri_gom((seg("Marcus"),), (hit("Marcus", "", 0, 6),))


@pytest.mark.parametrize("kotu", ["metin", None, 3])
def test_k2_segment_olmayan_oge_contract_violation(tmp_path: Path, kotu: object) -> None:
    with pytest.raises(ContractViolation):
        terimleri_gom((kotu,), (hit("Marcus", "Marcus", 0, 6),))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("start", "end"),
    [pytest.param("0", 6, id="start-str"), pytest.param(0, 6.0, id="end-float"), pytest.param(False, 6, id="start-bool")],
)
def test_k2_start_end_int_degil_contract_violation(tmp_path: Path, start: object, end: object) -> None:
    h = TermHit(source_term="Marcus", target_term="Marcus", start=start, end=end, segment_index=0)  # type: ignore[arg-type]
    with pytest.raises(ContractViolation):
        terimleri_gom((seg("Marcus"),), (h,))


def test_k2_lookup_segments_segment_olmayan_oge_contract_violation(tmp_path: Path) -> None:
    with pytest.raises(ContractViolation):
        fixture_store(tmp_path).lookup_segments(("Marcus",))  # type: ignore[arg-type]


def test_k2_termhit_olmayan_oge_contract_violation(tmp_path: Path) -> None:
    with pytest.raises(ContractViolation):
        terimleri_gom((seg("Marcus"),), (("Marcus", "Marcus", 0, 6, 0),))  # type: ignore[arg-type]


def test_k2_girdi_segmentleri_degismez(tmp_path: Path) -> None:
    segs = (seg("by the mill"),)
    kopya = segs[0]
    terimleri_gom(segs, (hit("mill", "Değirmen", 7, 11),))
    assert segs[0] == kopya and segs[0].text == "by the mill"


def test_k2_contract_violation_translatorerror_altsinifi() -> None:
    assert issubclass(ContractViolation, TranslatorError)


@pytest.mark.parametrize(
    "hits",
    [
        pytest.param((hit(NOBETCI, "X", 0, 4),), id="tutarsiz-source"),
        pytest.param((hit(NOBETCI, "X", 0, len(NOBETCI)), hit(NOBETCI[:5], "Y", 0, 5)), id="ortusme"),
        pytest.param((hit(NOBETCI, "X", 0, len(NOBETCI), idx=None),), id="segment_index-None"),
        pytest.param((hit(NOBETCI, "X", 0, len(NOBETCI), idx=4),), id="segment_index-disi"),
        pytest.param((hit(NOBETCI, "X", 0, 200),), id="aralik-disi"),
    ],
)
def test_k2_hata_mesajlari_metin_tasimaz(tmp_path: Path, hits: tuple[TermHit, ...]) -> None:
    """PROTOKOL 7: ContractViolation mesaji kaynak metni de terimi de tasimaz (yalniz sayilar/tipler)."""
    with pytest.raises(ContractViolation) as bilgi:
        terimleri_gom((seg(NOBETCI),), hits)
    assert NOBETCI not in str(bilgi.value)
    assert NOBETCI[:5] not in str(bilgi.value)


# ===========================================================================
# K3 -- terim yer tutucu ile cakismaz
# ===========================================================================


def test_k3_yer_tutucu_icinde_terim_eslesmez_pozitif_kontrol(tmp_path: Path) -> None:
    s = store(tmp_path, [("PLAYER", "Oyuncu"), *FIXTURE_V2])
    metin = "{PLAYER}は村にいます"
    assert s.lookup(metin, ("{PLAYER}",)) == []
    assert araliklar(s.lookup(metin, ())) == [(1, 7)]  # pozitif kontrol: yer tutucu bildirilmemisse `{`/`}` P* sinir


def test_k3_yer_tutucu_bitisik_terim_eslesir(tmp_path: Path) -> None:
    hits = fixture_store(tmp_path).lookup("{0}マルクス", ("{0}",))
    assert araliklar(hits) == [(3, 7)]
    assert hits[0].target_term == "Marcus"


def test_k3_yer_tutucunun_tum_gecisleri_korunur(tmp_path: Path) -> None:
    s = store(tmp_path, [("PLAYER", "Oyuncu"), ("Marcus", "Marcus")])
    metin = "{PLAYER} met Marcus; {PLAYER} left"
    hits = s.lookup(metin, ("{PLAYER}",))
    assert araliklar(hits) == [(13, 19)]


def test_k3_yer_tutucu_ile_kismen_ortusen_aday_eslesmez(tmp_path: Path) -> None:
    """Aday araligi korunan aralikla KISMEN ortusuyorsa da atlanir (pozitif kontrol: yer tutucusuz hit var)."""
    s = store(tmp_path, [("mill road", "Değirmen Yolu")])
    assert araliklar(s.lookup("the mill road")) == [(4, 13)]
    assert s.lookup("the mill road", ("mill r",)) == []
    assert s.lookup("the mill road", ("l ro",)) == []
    assert s.lookup("the mill road", ("road",)) == []


def test_k3_yer_tutucu_ayni_dizeyi_birden_fazla_kez_bildirmek_zararsiz(tmp_path: Path) -> None:
    s = store(tmp_path, [("PLAYER", "Oyuncu")])
    assert s.lookup("{PLAYER}", ("{PLAYER}", "{PLAYER}")) == []


def test_k3_bos_yer_tutucu_dizesi_yok_sayilir(tmp_path: Path) -> None:
    assert araliklar(fixture_store(tmp_path).lookup("Marcus", ("",))) == [(0, 6)]


def test_k3_gom_yer_tutucuyla_ortusen_hit_contract_violation(tmp_path: Path) -> None:
    segs = (seg("{PLAYER}は村にいます", placeholders=("{PLAYER}",)),)
    with pytest.raises(ContractViolation):
        terimleri_gom(segs, (hit("PLAYER", "Oyuncu", 1, 7),))


def test_k3_gom_yer_tutucuya_bitisik_hit_gecer(tmp_path: Path) -> None:
    segs = (seg("{0}マルクス", placeholders=("{0}",)),)
    assert terimleri_gom(segs, (hit("マルクス", "Marcus", 3, 7),))[0].text == "{0}Marcus"


def test_k3_gom_yer_tutucu_denetimi_segmentin_kendi_placeholders_ile(tmp_path: Path) -> None:
    """Denetim segment bazli: yer tutucu bildirmeyen segmentte ayni hit gecer (pozitif kontrol)."""
    segs = (seg("{PLAYER}は村にいます"),)
    assert terimleri_gom(segs, (hit("PLAYER", "Oyuncu", 1, 7),))[0].text == "{Oyuncu}は村にいます"


# ===========================================================================
# K4 -- hedef her zaman ilk harfi buyuk gomulur
# ===========================================================================


@pytest.mark.parametrize(
    ("girdi", "beklenen"),
    [
        pytest.param("değirmen", "Değirmen", id="değirmen"),
        pytest.param("marcus", "Marcus", id="marcus"),
        pytest.param("Değirmen", "Değirmen", id="zaten-buyuk"),
        pytest.param("İhtiyar", "İhtiyar", id="zaten-buyuk-İ"),
        pytest.param("ihtiyar", "İhtiyar", id="turkce-i->İ"),
        pytest.param("ışık", "Işık", id="turkce-ı->I"),
        pytest.param("çark", "Çark", id="ç"),
        pytest.param("eski değirmen", "Eski değirmen", id="yalniz-ilk-kelime"),
        pytest.param("3d", "3d", id="rakam-aynen"),
        pytest.param("", "", id="bos"),
    ],
)
def test_k4_ilk_harfi_buyut(girdi: str, beklenen: str) -> None:
    assert ilk_harfi_buyut(girdi) == beklenen


def test_k4_lookup_target_term_buyuk(tmp_path: Path) -> None:
    hits = store(tmp_path, [("水車小屋", "değirmen"), ("Marcus", "marcus")]).lookup("Marcusが水車小屋で")
    assert [h.target_term for h in hits] == ["Marcus", "Değirmen"]


def test_k4_gom_elle_kurulan_kucuk_hedef_buyuk_gomulur(tmp_path: Path) -> None:
    out = terimleri_gom((seg("水車小屋を過ぎて"),), (hit("水車小屋", "değirmen", 0, 4),))
    assert out[0].text == "Değirmenを過ぎて"


def test_k4_gom_zaten_buyuk_aynen(tmp_path: Path) -> None:
    out = terimleri_gom((seg("長老マルクス"),), (hit("長老", "İhtiyar", 0, 2), hit("マルクス", "MARCUS", 2, 6)))
    assert out[0].text == "İhtiyarMARCUS"


def test_k4_terimler_ozelliginde_hedef_buyuk(tmp_path: Path) -> None:
    s = store(tmp_path, [("水車小屋", "değirmen")])
    assert s.terimler == (SozlukTerimi(kaynak="水車小屋", hedef="Değirmen", note=None, kisa_terim_izni=False),)


# ===========================================================================
# K5 -- saf, deterministik, hizli
# ===========================================================================

IO_CAGRILARI = {"open", "print", "input"}
IO_OZNITELIKLERI = {"read_bytes", "read_text", "write_text", "write_bytes", "loads", "load", "dumps", "dump", "exists", "is_file", "stat"}


def _io_iceriyor(dugum: ast.AST) -> set[str]:
    adlar = _cagri_adlari(dugum)
    return {a for a in adlar if a in IO_CAGRILARI or a.split(".")[-1] in IO_OZNITELIKLERI or a.startswith(("json.", "Path", "os.", "sys.", "logging.", "warnings."))}


@pytest.mark.parametrize("ad", ["lookup", "lookup_segments", "terimleri_gom", "ilk_harfi_buyut"])
def test_k5_lookup_ve_gom_io_yapmaz_ast(ad: str) -> None:
    fonk = _fonksiyon(_modul_agaci(), ad)
    assert _io_iceriyor(fonk) == set(), ad
    assert _import_kokleri(fonk) == set(), ad  # govdede import yok


def test_k5_yukleme_io_su_yalniz_yukleyicide_ast() -> None:
    """Pozitif kontrol: dosya okuma/JSON cozme kodu modulde VAR (olcu bos kumeyi degil yeri olcer)."""
    agac = _modul_agaci()
    hepsi = _io_iceriyor(agac)
    assert any(a.endswith("read_bytes") for a in hepsi)
    assert any(a.startswith("json.") for a in hepsi)


def test_k5_modul_importlari_stdlib_ve_sozlesme() -> None:
    izinli_kokler = {"__future__", "dataclasses", "json", "re", "unicodedata", "collections", "pathlib", "typing", "src"}
    assert _import_kokleri(_modul_agaci()) <= izinli_kokler
    for d in _modul_agaci().body:
        if isinstance(d, ast.ImportFrom) and (d.module or "").startswith("src."):
            assert d.module in {"src.contracts.errors", "src.contracts.models"}, d.module


def test_k5_modulde_kanal_yok_ast() -> None:
    """`print`/`logging`/`warnings`/`sys` modulde hic gecmez (PROTOKOL 7)."""
    agac = _modul_agaci()
    adlar = {d.id for d in ast.walk(agac) if isinstance(d, ast.Name)} | {ast.unparse(d) for d in ast.walk(agac) if isinstance(d, ast.Attribute)}
    assert not ({"print", "logging", "warnings", "sys", "os"} & {a.split(".")[0] for a in adlar})


def test_k5_modul_duzeyinde_degisken_durum_yok_ast() -> None:
    """Modul duzeyi: import, `__all__`, `Final` sabit / `TypeAlias`, sinif, fonksiyon, docstring -- baska sey yok."""
    for d in _modul_agaci().body:
        if isinstance(d, (ast.Import, ast.ImportFrom, ast.ClassDef, ast.FunctionDef)):
            continue
        if isinstance(d, ast.Expr) and isinstance(d.value, ast.Constant) and isinstance(d.value.value, str):
            continue
        if isinstance(d, ast.Assign) and [ast.unparse(t) for t in d.targets] == ["__all__"]:
            continue
        assert isinstance(d, ast.AnnAssign) and ast.unparse(d.annotation) in {"Final", "TypeAlias"} or (
            isinstance(d, ast.AnnAssign) and ast.unparse(d.annotation).startswith("Final[")
        ), ast.unparse(d)[:60]


def test_k5_deterministik_iki_cagri_esit(tmp_path: Path) -> None:
    s = fixture_store(tmp_path)
    metin = "長老マルクスが水車小屋で待っています。"
    a = s.lookup(metin)
    b = s.lookup(metin)
    assert a == b and a is not b
    segs = (seg(metin),)
    hits = tuple(dataclasses.replace(h, segment_index=0) for h in a)
    assert terimleri_gom(segs, hits) == terimleri_gom(segs, hits)


def test_k5_iki_store_bagimsiz(tmp_path: Path) -> None:
    a = store(tmp_path, [("Marcus", "Marcus")], "a.json")
    b = store(tmp_path, [("mill", "Değirmen")], "b.json")
    assert araliklar(a.lookup("Marcus by the mill")) == [(0, 6)]
    assert araliklar(b.lookup("Marcus by the mill")) == [(14, 18)]


def test_k5_lookup_dosyayi_yeniden_okumaz(tmp_path: Path) -> None:
    """Yukleme yalniz `__init__`: dosya silinse de lookup calisir."""
    yol = sozluk_dosyasi(tmp_path, FIXTURE_V2)
    s = GlossaryStore(yol)
    yol.unlink()
    assert araliklar(s.lookup("Marcus")) == [(0, 6)]


def test_k5_donus_tipleri(tmp_path: Path) -> None:
    hits = fixture_store(tmp_path).lookup("Marcus")
    assert isinstance(hits, list) and all(isinstance(h, TermHit) for h in hits)
    assert isinstance(terimleri_gom((seg("Marcus"),), ()), tuple)


def _elli_terim() -> list[tuple[str, str]]:
    ekstra = [(f"term{i:02d}", f"Hedef{i:02d}") for i in range(50 - len(FIXTURE_V2))]
    return [*FIXTURE_V2, *ekstra]


def _izleyici_payi() -> float:
    """Kapsam/izleme (sys.settrace, C tracer) aktifken Python satirlari ~4-5x yavaslar; butce o kosumda 4x.

    Gercek butce izleyicisiz `pytest` kosumunda (evidence/pytest.txt) ve `real_check` #7'de olculur.
    """
    return 4.0 if sys.gettrace() is not None else 1.0


def test_k5_sure_1000_segment_50_terim_medyan_50ms_alti(tmp_path: Path) -> None:
    """K5 butcesi: 1000 segment x 50 terim, lookup_segments + gom, 5 kosum medyani < 50 ms (K5 metni)."""
    s = store(tmp_path, _elli_terim())
    assert len(s) == 50
    segs = tuple(seg("長老マルクスが水車小屋で待っています。") for _ in range(1000))
    sureler: list[float] = []
    for _ in range(5):
        t0 = time.perf_counter()
        hits = s.lookup_segments(segs)
        out = terimleri_gom(segs, hits)
        sureler.append((time.perf_counter() - t0) * 1000)
    assert len(hits) == 3000 and out[999].text == "İhtiyarMarcusがDeğirmenで待っています。"
    medyan = statistics.median(sureler)
    assert medyan < 50 * _izleyici_payi(), f"medyan {medyan:.1f} ms (izleyici payi x{_izleyici_payi():.0f}); {sureler}"


def test_k5_sure_kapi_yolu_lookup_ve_replace_ile_50ms_alti(tmp_path: Path) -> None:
    """`real_check` #7'nin yolu: segment basina `lookup` + `dataclasses.replace` + `terimleri_gom`, fixture terimleri."""
    s = fixture_store(tmp_path)
    segs = tuple(seg("長老マルクスが水車小屋で待っています。") for _ in range(1000))
    sureler: list[float] = []
    for _ in range(5):
        t0 = time.perf_counter()
        hits = tuple(dataclasses.replace(h, segment_index=i) for i, sg in enumerate(segs) for h in s.lookup(sg.text, sg.placeholders))
        terimleri_gom(segs, hits)
        sureler.append((time.perf_counter() - t0) * 1000)
    assert len(hits) == 3000
    medyan = statistics.median(sureler)
    assert medyan < 50 * _izleyici_payi(), f"medyan {medyan:.1f} ms (izleyici payi x{_izleyici_payi():.0f}); {sureler}"


def test_k5_terim_sayisiyla_dogrusal_degil_tek_gecis(tmp_path: Path) -> None:
    """500 terimli sozlukte de 1000 segment ayni butcede: terim-basi tarama degil tek gecis (trie)."""
    s = store(tmp_path, [*FIXTURE_V2, *((f"terim{i:03d}", f"Hedef{i:03d}") for i in range(489))])
    assert len(s) == 500
    segs = tuple(seg("長老マルクスが水車小屋で待っています。") for _ in range(1000))
    sureler: list[float] = []
    for _ in range(5):
        t0 = time.perf_counter()
        hits = s.lookup_segments(segs)
        terimleri_gom(segs, hits)
        sureler.append((time.perf_counter() - t0) * 1000)
    assert len(hits) == 3000
    medyan = statistics.median(sureler)
    assert medyan < 50 * _izleyici_payi(), f"medyan {medyan:.1f} ms (izleyici payi x{_izleyici_payi():.0f}); {sureler}"


@pytest.fixture
def logger_handle_kancasi(monkeypatch: pytest.MonkeyPatch) -> list[logging.LogRecord]:
    kayitlar: list[logging.LogRecord] = []
    ozgun = logging.Logger.handle

    def _handle(self: logging.Logger, record: logging.LogRecord) -> None:
        kayitlar.append(record)
        ozgun(self, record)

    monkeypatch.setattr(logging.Logger, "handle", _handle)
    return kayitlar


def test_k5_hicbir_kanala_metin_yazilmaz_davranis(
    tmp_path: Path,
    capfd: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
    logger_handle_kancasi: list[logging.LogRecord],
) -> None:
    """Yukleme + lookup + gom + iki hata yolu: stdout/stderr sifir bayt, log ve warnings kaydinda nobetci yok."""
    caplog.set_level(logging.DEBUG)
    capfd.readouterr()
    with warnings.catch_warnings(record=True) as uyarilar:
        warnings.simplefilter("always")
        s = store(tmp_path, [(NOBETCI, "Hedef"), *FIXTURE_V2])
        segs = (seg(f"{NOBETCI} met Marcus"),)
        hits = s.lookup_segments(segs)
        out = terimleri_gom(segs, hits)
        with pytest.raises(ContractViolation):
            terimleri_gom(segs, (hit(NOBETCI, "Hedef", 1, len(NOBETCI) + 1),))
        with pytest.raises(ValueError):
            store(tmp_path, [(NOBETCI, "Hedef"), (NOBETCI, "Baska")], "kotu.json")
    o, e = capfd.readouterr()
    assert (o, e) == ("", "")
    assert out[0].text == "Hedef met Marcus"
    mesajlar = [r.getMessage() for r in caplog.records] + [r.getMessage() for r in logger_handle_kancasi]
    assert not [m for m in mesajlar if NOBETCI in m or "Marcus" in m]
    assert not [w for w in uyarilar if NOBETCI in str(w.message)]


def test_k5_repr_terim_basmaz(tmp_path: Path) -> None:
    s = store(tmp_path, [(NOBETCI, "Hedef")])
    assert NOBETCI not in repr(s) and "Hedef" not in repr(s)
    assert "1" in repr(s)


# ===========================================================================
# K6 -- yukleme, sema ve hata
# ===========================================================================


@pytest.mark.parametrize(
    ("kayit", "mesajda"),
    [
        pytest.param({"kaynak": "", "hedef": "Marcus"}, "kaynak", id="kaynak-bos"),
        pytest.param({"kaynak": "   ", "hedef": "Marcus"}, "kaynak", id="kaynak-yalniz-bosluk"),
        pytest.param({"kaynak": "Marcus", "hedef": ""}, "Marcus", id="hedef-bos"),
        pytest.param({"kaynak": "Marcus", "hedef": " "}, "Marcus", id="hedef-yalniz-bosluk"),
        pytest.param({"kaynak": " Marcus", "hedef": "Marcus"}, "Marcus", id="kaynak-bas-bosluk"),
        pytest.param({"kaynak": "Marcus", "hedef": "Marcus "}, "Marcus", id="hedef-son-bosluk"),
        pytest.param({"kaynak": "검", "hedef": "Kılıç"}, "검", id="tek-hangul-hecesi-검"),
        pytest.param({"kaynak": "村", "hedef": "Köy"}, "村", id="tek-kanji-村"),
        pytest.param({"kaynak": "剣", "hedef": "Kılıç"}, "剣", id="tek-kanji-剣"),
        pytest.param({"kaynak": unicodedata.normalize("NFD", "한"), "hedef": "Han"}, "한", id="tek-hece-NFD-jamo-NFC-sonrasi-tek"),
        pytest.param({"kaynak": "ア", "hedef": "A"}, "ア", id="tek-katakana"),
        pytest.param({"kaynak": "x", "hedef": "İks"}, "x", id="tek-latin-harf"),
        pytest.param({"kaynak": "Marcus", "hedef": "St. Marcus"}, "Marcus", id="hedef-nokta-St.-Marcus"),
        pytest.param({"kaynak": "Marcus", "hedef": "Marcus!"}, "Marcus", id="hedef-unlem"),
        pytest.param({"kaynak": "Marcus", "hedef": "{0}"}, "Marcus", id="hedef-yer-tutucu-{0}"),
        pytest.param({"kaynak": "Marcus", "hedef": "Oyuncu}"}, "Marcus", id="hedef-kapanan-suslu"),
        pytest.param({"kaynak": "Marcus", "hedef": "{Oyuncu"}, "Marcus", id="hedef-acilan-suslu"),
        pytest.param({"kaynak": "Marcus", "hedef": "Marcus", "ozel_ad": True}, "ozel_ad", id="bilinmeyen-anahtar-ozel_ad-v1"),
        pytest.param({"kaynak": "Marcus", "hedef": "Marcus", "kisa_terim_izin": True}, "kisa_terim_izin", id="bilinmeyen-anahtar-yazim-hatasi"),
        pytest.param({"kaynak": 5, "hedef": "Marcus"}, "kaynak", id="kaynak-str-degil"),
        pytest.param({"kaynak": "Marcus", "hedef": ["Marcus"]}, "Marcus", id="hedef-str-degil"),
        pytest.param({"kaynak": "Marcus", "hedef": "Marcus", "not": 3}, "Marcus", id="not-str-degil"),
        pytest.param({"kaynak": "Marcus", "hedef": "Marcus", "kisa_terim_izni": "true"}, "Marcus", id="izin-bool-degil"),
        pytest.param({"kaynak": "Marcus", "hedef": "Marcus", "kisa_terim_izni": 1}, "Marcus", id="izin-int-bool-degil"),
        pytest.param({"hedef": "Marcus"}, "kaynak", id="kaynak-eksik"),
        pytest.param({"kaynak": "Marcus"}, "Marcus", id="hedef-eksik"),
        pytest.param("Marcus", "terim", id="kayit-sozluk-degil"),
    ],
)
def test_k6_sema_reddi_valueerror_mesajda_terim(tmp_path: Path, kayit: object, mesajda: str) -> None:
    with pytest.raises(ValueError, match=re.escape(mesajda)):
        store(tmp_path, [kayit])


@pytest.mark.parametrize("terminator", TERMINATORLER, ids=[f"U+{ord(t):04X}" for t in TERMINATORLER])
def test_k6_hedefte_her_terminator_tek_basina_red(tmp_path: Path, terminator: str) -> None:
    """Alti terminatorun HER BIRI ayri olculur (T-007 K3 kumesi; bolmeyi tetikler); mesajda KAYNAK terim."""
    with pytest.raises(ValueError, match="マルクス"):
        store(tmp_path, [("マルクス", "Mar" + terminator + "cus")])


@pytest.mark.parametrize("isaret", [",", ";", ":", "…", "、", "'", "-"])
def test_k6_hedefte_terminator_olmayan_noktalama_kabul(tmp_path: Path, isaret: str) -> None:
    """Kumenin siniri (pozitif kontrol): T-007'nin bolmedigi isaretler hedefte serbest."""
    s = store(tmp_path, [("マルクス", "Mar" + isaret + "cus")])
    assert s.terimler[0].hedef == "Mar" + isaret + "cus"


@pytest.mark.parametrize(
    ("a", "b"),
    [
        pytest.param("Marcus", "Marcus", id="birebir"),
        pytest.param("Marcus", "MARCUS", id="buyuk-kucuk"),
        pytest.param("istanbul", "İstanbul", id="turkce-İ-sinifi"),
        pytest.param("방앗간", unicodedata.normalize("NFD", "방앗간"), id="NFC-NFD-ayni-terim"),
    ],
)
def test_k6_tekrar_eden_kaynak_red(tmp_path: Path, a: str, b: str) -> None:
    with pytest.raises(ValueError, match=re.escape(a)):
        store(tmp_path, [(a, "X"), (b, "Y")])


def test_k6_kisa_terim_izni_ile_tek_hece_kabul(tmp_path: Path) -> None:
    s = store(tmp_path, [izinli("검", "Kılıç"), izinli("村", "Köy")])
    assert len(s) == 2
    assert s.lookup("검사가 왔습니다.") == []
    assert araliklar(s.lookup("村は")) == [(0, 1)]
    assert s.terimler[0].kisa_terim_izni is True


def test_k6_kisa_terim_izni_uzun_terimde_zararsiz(tmp_path: Path) -> None:
    s = store(tmp_path, [izinli("マルクス", "Marcus")])
    assert araliklar(s.lookup("マルクスが")) == [(0, 4)]


def test_k6_kisa_terim_izni_false_acikca_red(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="검"):
        store(tmp_path, [{"kaynak": "검", "hedef": "Kılıç", "kisa_terim_izni": False}])


def test_k6_not_alani_termhit_note(tmp_path: Path) -> None:
    s = store(tmp_path, [{"kaynak": "マルクス", "hedef": "Marcus", "not": "baş karakter, ad"}, ("mill", "Değirmen")])
    hits = s.lookup("マルクス mill")
    assert [h.note for h in hits] == ["baş karakter, ad", None]
    assert s.terimler[0].note == "baş karakter, ad"


def test_k6_not_null_kabul(tmp_path: Path) -> None:
    s = store(tmp_path, [{"kaynak": "マルクス", "hedef": "Marcus", "not": None}])
    assert s.terimler[0].note is None


@pytest.mark.parametrize(
    "veri",
    [
        pytest.param([], id="ust-duzey-liste"),
        pytest.param({"terimler": {"kaynak": "a"}}, id="terimler-liste-degil"),
        pytest.param({"terms": []}, id="terimler-anahtari-yok"),
        pytest.param("metin", id="ust-duzey-str"),
    ],
)
def test_k6_ust_duzey_sema_reddi(tmp_path: Path, veri: object) -> None:
    with pytest.raises(ValueError, match="terimler"):
        GlossaryStore(_json_yaz(tmp_path / "çeviri" / "kotu.json", veri))


def test_k6_ust_duzey_ek_anahtar_serbest(tmp_path: Path) -> None:
    """Profil meta verisi (`oyun`, `surum`...) ust duzeyde serbest; KAYIT duzeyinde bilinmeyen anahtar red."""
    yol = _json_yaz(tmp_path / "çeviri" / "meta.json", {"oyun": "X", "surum": 2, "terimler": [{"kaynak": "マルクス", "hedef": "Marcus"}]})
    assert len(GlossaryStore(yol)) == 1


def test_k6_bos_terimler_listesi_kabul(tmp_path: Path) -> None:
    assert len(store(tmp_path, [])) == 0


def test_k6_nfd_sozluk_nfc_metin_eslesir(tmp_path: Path) -> None:
    """KRT O3: sozluk NFD (`방앗간` 9 kodpoint) -> NFC'lenir; NFC metinde 3 kodpointlik aralik."""
    nfd = unicodedata.normalize("NFD", "방앗간")
    assert len(nfd) == 9
    s = store(tmp_path, [(nfd, "Değirmen")])
    assert araliklar(s.lookup("방앗간을 지나")) == [(0, 3)]
    assert s.terimler[0].kaynak == "방앗간"


def test_k6_nfd_metin_nfc_sozlukle_eslesir_indeks_nfc_metne_gore(tmp_path: Path) -> None:
    """Metin de NFC'lenir: NFD KR metinde (9 kodpoint) terim bulunur, indeksler NFC metne (3) gore."""
    nfd_metin = unicodedata.normalize("NFD", "방앗간을 지나")
    assert len(nfd_metin) == 17 and len("방앗간을 지나") == 7
    hits = fixture_store(tmp_path).lookup(nfd_metin)
    assert araliklar(hits) == [(0, 3)]
    assert hits[0].source_term == "방앗간"


def test_k6_nfd_segment_gomme_dogru_yerde(tmp_path: Path) -> None:
    """`terimleri_gom` segment metnini AYNI NFC ile normalize eder; NFD segmentte gomme dogru yerde, cikti NFC."""
    s = fixture_store(tmp_path)
    nfd_metin = unicodedata.normalize("NFD", "방앗간을 지나")
    segs = (seg(nfd_metin),)
    hits = s.lookup_segments(segs)
    out = terimleri_gom(segs, hits)
    assert out[0].text == "Değirmen을 지나"
    assert unicodedata.is_normalized("NFC", out[0].text)


def test_k6_nfd_source_term_tasiyan_hit_gomde_kabul(tmp_path: Path) -> None:
    """Elle kurulan hit'in `source_term`i NFD olsa da denetim AYNI NFC ile yapilir."""
    nfd = unicodedata.normalize("NFD", "방앗간")
    out = terimleri_gom((seg("방앗간을 지나"),), (hit(nfd, "Değirmen", 0, 3),))
    assert out[0].text == "Değirmen을 지나"


def test_k6_nfd_hedef_nfc_gomulur(tmp_path: Path) -> None:
    nfd_hedef = unicodedata.normalize("NFD", "değirmen")
    s = store(tmp_path, [("水車小屋", nfd_hedef)])
    assert s.terimler[0].hedef == "Değirmen"
    assert s.lookup("水車小屋を")[0].target_term == "Değirmen"


def test_k6_ascii_disi_dizin_altinda_json(tmp_path: Path) -> None:
    yol = _json_yaz(tmp_path / "çeviri" / "sözlük" / "オヤ.json", {"terimler": [{"kaynak": "マルクス", "hedef": "Marcus"}]})
    s = GlossaryStore(yol)
    assert araliklar(s.lookup("マルクス")) == [(0, 4)]
    assert s.yol == yol


def test_k6_dosya_bayt_ile_acilir_bom_kabul(tmp_path: Path) -> None:
    """KRT D4: UTF-8 BOM'lu dosya `json.loads(bayt)` ile cozulur; `decode('utf-8')` sonra `loads` patlardi."""
    yol = tmp_path / "çeviri" / "bom.json"
    yol.parent.mkdir(parents=True)
    yol.write_bytes(b"\xef\xbb\xbf" + json.dumps({"terimler": [{"kaynak": "マルクス", "hedef": "Marcus"}]}, ensure_ascii=False).encode("utf-8"))
    assert len(GlossaryStore(yol)) == 1


def test_k6_read_bytes_kullanilir_ast() -> None:
    """K6: dosya BAYT ile acilir -- `read_text`/`open(` yok, `read_bytes` var."""
    kaynak = KAYNAK.read_text(encoding="utf-8")
    assert "read_bytes" in kaynak and "read_text" not in kaynak and "open(" not in kaynak


def test_k6_dosya_yoksa_filenotfounderror_sarilmaz(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        GlossaryStore(tmp_path / "çeviri" / "yok.json")


def test_k6_bozuk_json_valueerror(tmp_path: Path) -> None:
    yol = tmp_path / "çeviri" / "bozuk.json"
    yol.parent.mkdir(parents=True)
    yol.write_bytes(b'{"terimler": [')
    with pytest.raises(ValueError, match="bozuk.json"):
        GlossaryStore(yol)


def test_k6_yol_str_kabul_baska_tip_typeerror(tmp_path: Path) -> None:
    yol = sozluk_dosyasi(tmp_path, FIXTURE_V2)
    assert len(GlossaryStore(str(yol))) == len(FIXTURE_V2)
    with pytest.raises(TypeError):
        GlossaryStore(None)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        GlossaryStore(yol.read_bytes())  # type: ignore[arg-type]


def test_k6_terimler_uzunluk_azalan_sirali_ve_degistirilemez(tmp_path: Path) -> None:
    s = fixture_store(tmp_path)
    uzunluklar = [len(t.kaynak) for t in s.terimler]
    assert uzunluklar == sorted(uzunluklar, reverse=True)
    assert isinstance(s.terimler, tuple) and len(s) == len(FIXTURE_V2)
    with pytest.raises(dataclasses.FrozenInstanceError):
        s.terimler[0].hedef = "X"  # type: ignore[misc]


def test_k6_ilk_hata_terimi_bildirilir_sira_korunur(tmp_path: Path) -> None:
    """Birden fazla hatali kayitta ilk hatali kaydin terimi mesajda (yazara isaret)."""
    with pytest.raises(ValueError, match="검") as bilgi:
        store(tmp_path, [("マルクス", "Marcus"), ("검", "K"), ("村", "Köy")])
    assert "村" not in str(bilgi.value)


# ===========================================================================
# K7 -- segment_index denetimi
# ===========================================================================


@pytest.mark.parametrize(
    "idx",
    [
        pytest.param(None, id="None"),
        pytest.param(-1, id="-1"),
        pytest.param(1, id="len(segments)"),
        pytest.param(2, id="len(segments)+1"),
        pytest.param(True, id="bool-True"),
        pytest.param(0.0, id="float-0.0"),
    ],
)
def test_k7_segment_index_gecersiz_contract_violation(tmp_path: Path, idx: object) -> None:
    segs = (seg("Marcus"),)
    h = TermHit(source_term="Marcus", target_term="Marcus", start=0, end=6, segment_index=idx)  # type: ignore[arg-type]
    with pytest.raises(ContractViolation):
        terimleri_gom(segs, (h,))


def test_k7_gecersiz_indeks_diger_hitler_dogruyken_de_ihlal(tmp_path: Path) -> None:
    """Sessiz yutma yok: bir hit gecersizse cagri BUTUNUYLE duser, kismi cikti uretilmez."""
    segs = (seg("Marcus"), seg("mill"))
    hits = (hit("Marcus", "Marcus", 0, 6, idx=0), hit("mill", "Değirmen", 0, 4, idx=None))
    with pytest.raises(ContractViolation):
        terimleri_gom(segs, hits)


def test_k7_son_gecerli_indeks_kabul(tmp_path: Path) -> None:
    segs = (seg("x"), seg("Marcus"))
    out = terimleri_gom(segs, (hit("Marcus", "Marcus", 0, 6, idx=1),))
    assert out[1].text == "Marcus" and out[0] is segs[0]


# ===========================================================================
# sozlesme uyumu
# ===========================================================================


def test_uyum_termhit_alanlari_sozlesmeyle_ayni(tmp_path: Path) -> None:
    h = fixture_store(tmp_path).lookup("Marcus")[0]
    assert {f.name for f in dataclasses.fields(h)} == {"source_term", "target_term", "start", "end", "segment_index", "note"}
    assert h == TermHit(source_term="Marcus", target_term="Marcus", start=0, end=6, segment_index=None, note=None)


def test_uyum_public_api() -> None:
    assert set(sozluk.__all__) == {"GlossaryStore", "SozlukTerimi", "terimleri_gom", "ilk_harfi_buyut"}
