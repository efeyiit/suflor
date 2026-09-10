r"""TESTER-A · TUR 5 · MERCEK: GARANTI ALANI.

Bu dosya tur 5'in dort saldiri noktasini kapsar (env.md "TUR 5 mercekleri /
A · Garanti alani"):

  1. **K23 bolumleme kararliligi** -- implementer'in 2500 girdilik denetimine
     GUVENMEDEN, KENDI ureticimle (bes ayri geometri dagilimi, dort tohum,
     dort on ayar) `_normalize_impl(..., apply_inheritance=True)` ile
     `False`'in BOLUMLEMESINI karsilastirir. Sondanin DISLERI oldugu ayrica
     ISPATLANIR: tur 4'un mekanizmasi bu dosyada yeniden kurulur ve AYNI
     karsilastirici onda fark BULUR (aksi halde "0 fark" totoloji olurdu).
  2. **`apply_inheritance=False`'in ALANI** -- bayrak "son adimi atlamak" mi,
     yoksa gercekten "miras mekanizmasi HIC VAR OLMASAYDI uretilecek cikti"
     mi? Miras kodu SIFIR olan BAGIMSIZ bir referans boru hatti kurulur ve
     `speaker` DAHIL tam segment esitligi aranir.
  3. **`_normalize_impl` sizintisi** -- `__all__`, star-import, `normalize`
     imzasi, paket duzeyi.
  4. **K24 `tail`** -- her durumda tanimli mi (tek ogeli grup, ilk grup, grup
     kapanip yeniden baslarken, yozlasmis tek-ogeli grup) ve `tail` ile
     `current` HANGI geometrilerde ayrisiyor -- IKI yonde de kendi
     geometrilerimle.

Regresyon (K5/K6/K7/K15/K16/K17/K18) ayni dizindeki `test_warranty_domain.py`
(tur 2) dosyasinda durur ve tur 5'te de kosar.

**BULGU R5-1 (tur 5'te BLOKE EDICI) -- TUR 6'DA KAPANDI.** `tail`, tur 5'te
docstring'in KOSULSUZ iddia ettigi gibi HER ZAMAN "grubun son HAM ogesi"
DEGILDI -- adim 3'un (hyphen birlesimi, `_merge_hyphenated`) urettigi COK
BLOKLU bir oge de `tail` olabiliyordu ve onun BIRLESIK bbox'i, K24'un tam
olarak kaldirmayi vaat ettigi artifakti GERI GETIRIYORDU. Sef K28'i (tur 6)
verdi: sorgunun IKI tarafi da OZGUN blok listesinden turetiliyor
(`_raw_query_pair`).

TUR 6'DA BU DOSYADA YAPILANLAR (sef_karari-tur6.md, mercek A/1):
  * 5. bolumun UC parametreli `xfail(strict=True)` testi XPASS verdi ve
    DUZELTILMIS davranisi dogrulayan YESIL testlere cevrildi; yanlarina
    (a) duzeltmenin MEKANIZMASINI (sorgu cifti) dogrulayan ve (b) ayni
    fixture'in TUR 5 biciminde HALA yanlis sonuc verdigini gosteren birer
    test eklendi.
  * DORDUNCU xfail (`test_r51_makine_denetimi_*`) `_group`'u/`normalize`'i
    HIC cagirmiyordu (gruplama dongusunu test icinde kuruyordu), bu yuzden
    hicbir duzeltme onu XPASS yapamazdi. KALDIRILDI; yerine 6. bolumdeki
    yeni makine denetimi geldi: `normalize` uzerinden, SIRASIZ girdiyle ve
    >=3 BLOKLU kuyruklarla, sef kitinin `sorgu_kaydi()` kancasiyla.
  * `:401`'in kor sondasi KIRILMIYORDU ama SESSIZCE BAYATLAMISTI (kendi
    yerel `_group_tur4` kopyasini olcuyordu, urunun yeni sorgu bicimini
    hic gormuyordu). Yerel kopya urunun TUR 6 yapisiyla esitlendi
    (`_group_tur4_yeni_sorgu_bicimiyle`) ve bir daha sessizce bayatlamasin
    diye AST kapisi eklendi.
Uc geometrik yolun IKISI MONOTONIK'tir (dikey uzanim okuma sirasina UYGUN,
"egzotik" geometri GEREKMEZ): hyphen-birlesik kutunun `h`/`w`'sini SISIRMESI
tek basina yetiyordu.
"""
from __future__ import annotations

import ast
import inspect
import random
import sys
import textwrap
from collections.abc import Sequence
from dataclasses import replace

import pytest

from olcu_kiti import okuma_sirasi, sorgu_kaydi
from src.contracts.models import OcrPreset, Rect, Segment, TextBlock
from src.ocr import normalizer as normalizer_modulu
from src.ocr.normalizer import (
    _PLACEHOLDER_PATTERN,
    _collapse_intraline,
    _extract_speakers,
    _group,
    _group_rejection_reason,
    _is_noise,
    _Item,
    _merge_hyphenated,
    _normalize_impl,
    _raw_query_pair,
    _union_rect,
    _validate_confidences,
    normalize,
)
from src.ocr.presets import NormalizerParams, get_params

PRESETS = (OcrPreset.DIALOGUE, OcrPreset.MENU, OcrPreset.TOOLTIP, OcrPreset.SUBTITLE)

# Implementer'in denetimi 2500 girdi/tek tohum kullaniyor (docstring). Bu
# uretici KASITLI olarak farklidir: ALTI ayri geometri dagilimi, dort tohum,
# 3+ konusmaci zincirleri, ic ice uzunluk+geometri bolunmeleri, ayni y'de
# yan yana bloklar, cok kucuk/sifir/negatif h, VE (tur 5, bu ajan) adim 3'un
# hyphen birlesimini YOGUN tetikleyen bir dagilim (bkz. `_gen_hyphen_dense`).
# 6 uretici x 105 x 4 tohum = 2520 AYRI girdi (sefin >=2000 tabani asilir).
SEEDS = (777, 1234567, 20260910, 42)
PER_GEN = 105

_NAMES = ("Ada", "Bob", "Cem", "勇者", "魔王", "村人", "Deniz")
_WORDS = (
    "merhaba", "dunya", "bu", "uzun", "bir", "cumledir", "kelime", "tra-",
    "dition", "well-known", "{0}", "%s", "<b>", "[X]", "こんにちは", "力",
)


def _txt(rng: random.Random, n: int) -> str:
    return " ".join(rng.choice(_WORDS) for _ in range(n))


def _gen_speaker_chain(rng: random.Random) -> list[TextBlock]:
    """3+ konusmaci zinciri -- her birkac blokta yeni bir etiket."""
    blocks: list[TextBlock] = []
    y = rng.randint(0, 40)
    for _ in range(rng.randint(3, 12)):
        h = rng.choice((18, 20, 22))
        mode = rng.random()
        if mode < 0.35:
            text = f"{rng.choice(_NAMES)}{rng.choice((':', '：'))} {_txt(rng, rng.randint(3, 30))}"
        elif mode < 0.50:
            text = f"{rng.choice(_NAMES)}{rng.choice((':', '：'))}"
        else:
            text = _txt(rng, rng.randint(3, 40))
        blocks.append(
            TextBlock(
                text=text,
                bbox=Rect(x=rng.randint(0, 6), y=y, w=rng.randint(150, 400), h=h),
                confidence=rng.uniform(0.66, 1.0),
            )
        )
        y += h + rng.choice((0, 1, 2, 3, 5, 12, 60, 400))
    return blocks


def _gen_nested_split(rng: random.Random) -> list[TextBlock]:
    """Ic ice uzunluk + geometri bolunmesi; arada KENDI etiketiyle gelen
    replikler (tur 5 kirmizi takiminin B1 senaryosu)."""
    blocks = [TextBlock(text=f"{rng.choice(_NAMES)}:", bbox=Rect(x=0, y=0, w=90, h=20), confidence=1.0)]
    y = 20
    for _ in range(rng.randint(4, 14)):
        h = rng.choice((16, 20, 24))
        blocks.append(
            TextBlock(
                text=_txt(rng, rng.randint(20, 60)),
                bbox=Rect(x=rng.randint(0, 4), y=y, w=rng.randint(200, 420), h=h),
                confidence=rng.uniform(0.7, 1.0),
            )
        )
        y += h + rng.choice((0, 1, 2, 3, 4, 30, 200))
        if rng.random() < 0.25:
            blocks.append(
                TextBlock(
                    text=f"{rng.choice(_NAMES)}: {_txt(rng, rng.randint(3, 25))}",
                    bbox=Rect(x=rng.randint(0, 4), y=y, w=rng.randint(200, 420), h=20),
                    confidence=1.0,
                )
            )
            y += 20 + rng.choice((0, 1, 2))
    return blocks


def _gen_side_by_side(rng: random.Random) -> list[TextBlock]:
    """Ayni `y`'de YAN YANA bloklar (sutunlar)."""
    blocks: list[TextBlock] = []
    y = 0
    for _ in range(rng.randint(2, 6)):
        h = rng.choice((14, 20))
        x = 0
        for _ in range(rng.randint(2, 4)):
            w = rng.randint(40, 160)
            text = (
                f"{rng.choice(_NAMES)}: {_txt(rng, rng.randint(1, 12))}"
                if rng.random() < 0.4
                else _txt(rng, rng.randint(1, 20))
            )
            blocks.append(TextBlock(text=text, bbox=Rect(x=x, y=y, w=w, h=h), confidence=rng.uniform(0.66, 1.0)))
            x += w + rng.choice((0, 1, 5, 40))
        y += h + rng.choice((0, 1, 2, 4))
    return blocks


def _gen_tiny_h(rng: random.Random) -> list[TextBlock]:
    """Cok kucuk / sifir / negatif `h` ve `w`; monotonik OLMAYAN dikey uzanim."""
    blocks: list[TextBlock] = []
    y = 0
    for _ in range(rng.randint(2, 10)):
        text = (
            f"{rng.choice(_NAMES)}: {_txt(rng, rng.randint(1, 30))}"
            if rng.random() < 0.35
            else _txt(rng, rng.randint(1, 40))
        )
        blocks.append(
            TextBlock(
                text=text,
                bbox=Rect(
                    x=rng.randint(-5, 10),
                    y=y,
                    w=rng.choice((0, 1, 3, -4, 120, 300)),
                    h=rng.choice((0, 1, 1, 2, 3, -5, -1, 20, 400)),
                ),
                confidence=rng.uniform(0.6, 1.0),
            )
        )
        y += rng.choice((-3, 0, 1, 2, 20, 100))
    return blocks


_HYPHEN_TAILS = ("son-", "uzun-", "goz-", "tra-", "kelime-")
_HYPHEN_HEADS = ("raki", "ca", "lem", "dition", "nin")


def _gen_hyphen_dense(rng: random.Random) -> list[TextBlock]:
    """TUR 5 (bu ajan): adim 3'un (`_merge_hyphenated`) COK BLOKLU oge
    uretmesini YOGUN tetikleyen dagilim -- her blogun ~%35'i tire ile biter,
    devam satirlari KISA (`h` 3-8) veya YATAY olarak KAYDIRILMIS olabilir.
    Amac: `_group`'a giren bir ogenin KENDISININ birlesik bir bbox tasidigi
    (yani `tail`'in "HAM oge" OLMADIGI) durumlari uretmek -- bkz. bolum 5,
    BULGU R5-1. Bu dagilim onceki uretici setinde YOKTU."""
    blocks: list[TextBlock] = []
    y = rng.randint(-10, 30)
    for _ in range(rng.randint(3, 16)):
        h = rng.choice((3, 5, 8, 16, 18, 20, 24, 40))
        n = rng.randint(2, 45)
        parts = [rng.choice(_WORDS) for _ in range(n)]
        if rng.random() < 0.35:
            parts[-1] = rng.choice(_HYPHEN_TAILS)
        elif rng.random() < 0.35:
            parts[0] = rng.choice(_HYPHEN_HEADS)
        text = " ".join(parts)
        if rng.random() < 0.25:
            text = f"{rng.choice(_NAMES)}{rng.choice((':', '：'))} {text}"
        blocks.append(
            TextBlock(
                text=text,
                bbox=Rect(
                    x=rng.randint(-10, 60),
                    y=y,
                    w=rng.choice((8, 30, 120, 200, 240, 300)),
                    h=h,
                ),
                confidence=rng.uniform(0.66, 1.0),
            )
        )
        y += h + rng.choice((-4, 0, 1, 2, 3, 5, 8, 14, 30))
    return blocks


def _gen_mixed(rng: random.Random) -> list[TextBlock]:
    out: list[TextBlock] = []
    for _ in range(rng.randint(1, 3)):
        out.extend(
            rng.choice(
                (_gen_speaker_chain, _gen_nested_split, _gen_side_by_side, _gen_tiny_h, _gen_hyphen_dense)
            )(rng)
        )
    rng.shuffle(out)  # K3: girdi sirasiz gelebilir
    return out


GENERATORS = (
    _gen_speaker_chain,
    _gen_nested_split,
    _gen_side_by_side,
    _gen_tiny_h,
    _gen_hyphen_dense,
    _gen_mixed,
)


def _corpus(seed: int) -> list[list[TextBlock]]:
    rng = random.Random(seed)
    return [gen(rng) for gen in GENERATORS for _ in range(PER_GEN)]


def _partition(segments: list[Segment]) -> list[tuple]:
    """K23'un korudugu HER SEY -- `speaker` HARIC."""
    return [(s.source_blocks, s.text, s.bbox, s.placeholders) for s in segments]


def test_derlem_sefin_2000_girdi_tabanini_asiyor() -> None:
    """Denetimin BUYUKLUGU de bir iddiadir -- makineyle sabitlenir
    (sef_karari-tur5.md: ">=2000 girdi"). Ayrica derlemin BOS/dejenere
    olmadigi (blok sayisi) dogrulanir."""
    toplam = sum(len(_corpus(seed)) for seed in SEEDS)
    assert toplam >= 2500, toplam
    bloklar = sum(len(b) for seed in SEEDS for b in _corpus(seed))
    assert bloklar > 20000, bloklar


# ===========================================================================
# 1 · K23 -- BOLUMLEME DEGISMEZI, KENDI URETICIMLE
# ===========================================================================


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("preset", PRESETS)
def test_k23_bolumleme_miras_acik_kapali_birebir_ayni(seed: int, preset: OcrPreset) -> None:
    """K23 DEGISMEZI: bolumleme (`source_blocks` dizisi + `text`/`bbox`/
    `placeholders`/segment SAYISI) miras acikken ve kapaliyken BIREBIR ayni.
    TEK fark bile bloke edicidir."""
    for blocks in _corpus(seed):
        try:
            on = _normalize_impl(blocks, preset, apply_inheritance=True)
        except (ValueError, TypeError) as exc_on:
            with pytest.raises(type(exc_on)):
                _normalize_impl(blocks, preset, apply_inheritance=False)
            continue
        off = _normalize_impl(blocks, preset, apply_inheritance=False)
        assert _partition(on) == _partition(off), f"bolumleme ayristi: preset={preset} blocks={blocks!r}"
        assert len(on) == len(off)


@pytest.mark.parametrize("seed", SEEDS)
def test_k23_denetim_totoloji_degil_miras_gercekten_speaker_degistiriyor(seed: int) -> None:
    """Yukaridaki testin BOS olmadigini kanitlar: ayni derlemde miras
    GERCEKTEN cok sayida segmentin `speaker`'ini degistiriyor. Eger miras hic
    tetiklenmiyorsa "0 bolumleme farki" hicbir sey soylemez."""
    etkilenen = 0
    for blocks in _corpus(seed):
        for preset in PRESETS:
            try:
                on = _normalize_impl(blocks, preset, apply_inheritance=True)
                off = _normalize_impl(blocks, preset, apply_inheritance=False)
            except (ValueError, TypeError):
                continue
            etkilenen += sum(1 for a, b in zip(on, off) if a.speaker != b.speaker)
    assert etkilenen > 100, f"miras derlemde neredeyse hic tetiklenmemis ({etkilenen}) -- denetim totoloji"


def _group_tur4_yeni_sorgu_bicimiyle(
    items: list[_Item],
    params: NormalizerParams,
    *,
    blocks: Sequence[TextBlock] = (),
    apply_inheritance: bool = True,
) -> list[_Item]:
    """TUR 4'un HATASI, TUR 6'nin SORGU BICIMIYLE (bu ajan, tur 6 --
    `:401`'in yeniden NISANLANMASI).

    ESKI HALI BAYATTI (sef_karari-tur6.md, "A `:401`'i yeni sorgu bicimine
    nisanlar"): bu yardimci tur 4'un TEK GECISLI govdesini tasiyordu ve
    miras-uygunluk sorgusunu `_group_rejection_reason(current, nxt, ...)`
    ile -- yani K28 ONCESI bicimle -- soruyordu. Sonda KIRILMIYORDU ama
    urun kodunun ARTIK KOSTUGU sorgu yolundan (`_raw_query_pair(tail,
    nxt, blocks)`) hic gecmiyordu: "karsilastiricinin disleri var"
    iddiasi K28 sonrasi hicbir sey ispatlamiyordu.

    YENI HALI: govde, urun `_group`'unun TUR 6 yapisinin birebir
    kopyasidir -- IKI GECIS, `blocks` keyword-only parametresi ve
    `_raw_query_pair(tail, nxt, blocks)` ile ham sorgu cifti. Tek fark
    TUR 4'un HATASIDIR: miras edilen `speaker` bolumleme dongusune GERI
    BESLENIR (`current = replace(nxt, speaker=...)`), yani bir sonraki
    gruplama karari mute edilmis `speaker` ile verilir. `src/` altindaki
    koda DOKUNULMAZ; yapinin urunle ESLESTIGI ayrica
    `test_r6_401_sondasi_urun_sorgu_bicimiyle_esitlenmis_ast` ile
    makineyle sabitlenir."""
    if not items:
        return []
    groups: list[_Item] = []
    pure_length_boundaries: list[bool] = []
    current = items[0]
    tail = items[0]
    for nxt in items[1:]:
        reason = _group_rejection_reason(current, nxt, params)
        if reason is None:
            current = _Item(
                text=current.text + " " + nxt.text,
                bbox=_union_rect(current.bbox, nxt.bbox),
                speaker=current.speaker,
                source_blocks=tuple(sorted((*current.source_blocks, *nxt.source_blocks))),
            )
            tail = nxt
        else:
            groups.append(current)
            miras_uygun = (
                reason == "length"
                and nxt.speaker is None
                and _group_rejection_reason(
                    *_raw_query_pair(tail, nxt, blocks), params, ignore_length=True
                )
                is None
            )
            pure_length_boundaries.append(miras_uygun)
            # TUR 4'UN HATASI: miras BOLUMLEMEYE geri beslenir.
            if apply_inheritance and miras_uygun and current.speaker is not None:
                nxt = replace(nxt, speaker=current.speaker)
            current = nxt
            tail = nxt
    groups.append(current)
    return groups


def _group_mirassiz(
    items: list[_Item], params: NormalizerParams, *, blocks: Sequence[TextBlock] = ()
) -> list[_Item]:
    """"MIRAS MEKANIZMASI HIC VAR OLMASAYDI" -- miras kodu SIFIR.
    (`blocks` yalnizca cagri BICIMI urunle ayni kalsin diye kabul edilir;
    miras sorgusu HIC yapilmadigi icin OKUNMAZ.)"""
    if not items:
        return []
    groups: list[_Item] = []
    current = items[0]
    for nxt in items[1:]:
        if _group_rejection_reason(current, nxt, params) is None:
            current = _Item(
                text=current.text + " " + nxt.text,
                bbox=_union_rect(current.bbox, nxt.bbox),
                speaker=current.speaker,
                source_blocks=tuple(sorted((*current.source_blocks, *nxt.source_blocks))),
            )
        else:
            groups.append(current)
            current = nxt
    groups.append(current)
    return groups


def _normalize_with(blocks, preset, grouper, **kw) -> list[Segment]:
    """`_normalize_impl`'in adimlarini AYNEN kullanir; YALNIZ adim 5'in
    grupleyicisi degistirilebilir. TUR 6: urun gibi `blocks=blocks`
    GECIRIR -- K28'in ham sorgu cifti bu yoldan da kosulur."""
    _validate_confidences(blocks)
    params = get_params(preset)
    ordered = sorted(enumerate(blocks), key=lambda p: (p[1].bbox.y, p[1].bbox.x))
    items = [
        _Item(text=b.text, bbox=b.bbox, speaker=None, source_blocks=(i,))
        for i, b in ordered
        if b.confidence >= params.confidence_threshold
    ]
    items = [it for it in items if not _is_noise(it.text)]
    items = [replace(it, text=_collapse_intraline(it.text)) for it in items]
    items = _merge_hyphenated(items)
    items = _extract_speakers(items)
    grouped = grouper(items, params, blocks=blocks, **kw) if params.should_group else items
    segments = [
        Segment(
            text=g.text,
            bbox=g.bbox,
            speaker=g.speaker,
            placeholders=tuple(m.group(0) for m in _PLACEHOLDER_PATTERN.finditer(g.text)),
            source_blocks=tuple(sorted(g.source_blocks)),
        )
        for g in grouped
        if g.text.strip()
    ]
    return sorted(segments, key=lambda s: (s.bbox.y, s.bbox.x))


def test_k23_karsilastiricinin_disleri_var_tur4_mekanizmasi_yakalaniyor() -> None:
    """SONDA KONTROLU (PROTOKOL S3 kapi 6): ayni derlem + ayni
    karsilastirici, TUR 4'un mekanizmasinda BOLUMLEME FARKI bulmali.
    Bulamazsa yukaridaki "0 fark" sonucu hicbir sey ispatlamaz.

    TUR 6 (`:401`'in yeniden nisanlanmasi): sonda artik URUNUN sorgu
    bicimini (`_raw_query_pair(tail, nxt, blocks)`) kosan bir mutant
    kullanir -- bkz. `_group_tur4_yeni_sorgu_bicimiyle`. Sondanin
    GERCEKTEN o yoldan gectigi (yani `_raw_query_pair` cagrildigi)
    ayrica SAYILARAK sabitlenir; sifirsa sonda yine korlesmis demektir."""
    farklar = 0
    ham_sorgu_sayisi = 0
    bu_modul = sys.modules[__name__]
    orij = _raw_query_pair

    def sayan(tail: _Item, nxt: _Item, blocks: Sequence[TextBlock]):  # type: ignore[no-untyped-def]
        nonlocal ham_sorgu_sayisi
        ham_sorgu_sayisi += 1
        return orij(tail, nxt, blocks)

    # Yerel mutant `_raw_query_pair`'i BU MODULUN globalinden cozer; sayaci
    # buraya takmak, sondanin GERCEKTEN ham sorgu yolundan gectigini olcer
    # (urun modulu DEGISTIRILMEZ).
    bu_modul._raw_query_pair = sayan  # type: ignore[attr-defined]
    try:
        for seed in SEEDS:
            for blocks in _corpus(seed):
                for preset in PRESETS:
                    try:
                        a = _normalize_with(
                            blocks, preset, _group_tur4_yeni_sorgu_bicimiyle, apply_inheritance=True
                        )
                        b = _normalize_with(
                            blocks, preset, _group_tur4_yeni_sorgu_bicimiyle, apply_inheritance=False
                        )
                    except (ValueError, TypeError):
                        continue
                    if _partition(a) != _partition(b):
                        farklar += 1
    finally:
        bu_modul._raw_query_pair = orij  # type: ignore[attr-defined]
    assert ham_sorgu_sayisi > 1000, (
        f"sonda urunun ham sorgu yolundan gecmiyor ({ham_sorgu_sayisi} cagri) -- "
        "`:401` yine bayat"
    )
    assert farklar > 0, "karsilastirici tur 4'un bilinen B1 hatasini bile yakalamiyor -- sonda kor"


def test_r6_401_sondasi_urun_sorgu_bicimiyle_esitlenmis_ast() -> None:
    """`:401`'in SESSIZ BAYATLAMASINA karsi YAPISAL kapi (tur 6).

    Sondanin yerel kopyasi kirilmadan bayatlayabilir -- tur 5'te tam
    olarak bu oldu. Bu test iki tarafi da AST ile okuyup ayni SORGU
    BICIMINI aradigini sabitler: hem urunun `_group`'u hem yerel
    mutant, miras sorgusunu `_group_rejection_reason(*_raw_query_pair(
    tail, nxt, blocks), ..., ignore_length=True)` seklinde yapmali.
    Urun bicimini degistirirse bu test KIRILIR -- sonda sessizce
    bayatlayamaz."""

    def miras_sorgusu_bicimi(fn) -> list[str]:  # type: ignore[no-untyped-def]
        agac = ast.parse(textwrap.dedent(inspect.getsource(fn)))
        bulunan: list[str] = []
        for dugum in ast.walk(agac):
            if not isinstance(dugum, ast.Call):
                continue
            if not (isinstance(dugum.func, ast.Name) and dugum.func.id == "_group_rejection_reason"):
                continue
            if not any(k.arg == "ignore_length" for k in dugum.keywords):
                continue
            bulunan.append(", ".join(ast.unparse(a) for a in dugum.args))
        return bulunan

    urun = miras_sorgusu_bicimi(_group)
    yerel = miras_sorgusu_bicimi(_group_tur4_yeni_sorgu_bicimiyle)
    assert urun == ["*_raw_query_pair(tail, nxt, blocks), params"], (
        f"urunun miras sorgusunun BICIMI degismis: {urun} -- `:401` sondasi ve bu "
        "dosyadaki yerel kopya yeniden nisanlanmali"
    )
    assert yerel == urun, f"yerel sonda urunle ayni sorgu bicimini kosmuyor: {yerel} != {urun}"


def test_k23_b1_senaryosu_kendi_etiketiyle_gelen_replik_kuyruga_yapismaz() -> None:
    """Kirmizi takimin B1 senaryosu, kendi geometrimle: uzunluk-tek sinirda
    miras VAR; hemen ardindan KENDI `Ada:` etiketiyle gelen blok AYRI segment
    kalmali (VARYANT B). Tur 4'te bu `(2, 3)` olarak BIRLESIYORDU."""
    blocks = [
        TextBlock(text="Ada: " + "A" * 150, bbox=Rect(0, 0, 200, 20), confidence=1.0),
        TextBlock(text="B" * 120, bbox=Rect(0, 22, 200, 20), confidence=1.0),
        TextBlock(text="C" * 120, bbox=Rect(0, 44, 200, 20), confidence=1.0),
        TextBlock(text="Ada: " + "D" * 60, bbox=Rect(0, 66, 200, 20), confidence=1.0),
    ]
    on = normalize(blocks, OcrPreset.DIALOGUE)
    off = _normalize_impl(blocks, OcrPreset.DIALOGUE, apply_inheritance=False)
    assert [s.source_blocks for s in on] == [s.source_blocks for s in off]
    assert (2,) in [s.source_blocks for s in on] and (3,) in [s.source_blocks for s in on]


# ===========================================================================
# 2 · `apply_inheritance=False`'IN ALANI
# ===========================================================================


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("preset", PRESETS)
def test_apply_inheritance_false_miras_hic_olmasaydi_ciktisiyla_birebir(seed: int, preset: OcrPreset) -> None:
    """Bayrak "yalnizca son adimi atlayan bir yaklasim" DEGIL: miras kodu
    SIFIR olan BAGIMSIZ bir boru hatti ile `speaker` DAHIL tam segment
    esitligi. Ikisi ayrisirsa K23 denetiminin KENDISI eksik olurdu."""
    for blocks in _corpus(seed):
        try:
            ref = _normalize_with(blocks, preset, _group_mirassiz)
            off = _normalize_impl(blocks, preset, apply_inheritance=False)
        except (ValueError, TypeError):
            continue
        assert ref == off, f"apply_inheritance=False, mirassiz referanstan ayristi: {blocks!r}"


@pytest.mark.parametrize("seed", SEEDS)
def test_miras_yalnizca_none_speakeri_doldurur_asla_degistirmez_veya_silmez(seed: int) -> None:
    """`_normalize_impl` docstring'i: `False` iken "YALNIZ bazi segmentlerin
    `speaker` alani `None` KALIR". Iki yon de sinanir: (a) kapali iken
    None-DISI bir speaker acik haldekinden FARKLI olamaz, (b) acik iken
    `None` olan bir segment kapali iken DOLU olamaz."""
    for blocks in _corpus(seed):
        for preset in PRESETS:
            try:
                on = _normalize_impl(blocks, preset, apply_inheritance=True)
                off = _normalize_impl(blocks, preset, apply_inheritance=False)
            except (ValueError, TypeError):
                continue
            for a, b in zip(on, off):
                if b.speaker is not None:
                    assert a.speaker == b.speaker
                if a.speaker is None:
                    assert b.speaker is None


def test_bayragin_alani_k15_ici_grup_yayilimini_KAPATMAZ() -> None:
    """Bayragin ALANININ UST sinirini sabitler. `apply_inheritance=False`
    "HER TURLU miras kapali" DEMEZ: K15'in GRUP ICI `speaker` yayilimi
    (`X` etiketli oge, etiketsiz bir DEVAM ogesiyle AYNI gruba girdiginde
    grubun `speaker`'i `X` olur -- `_group`'ta `speaker=current.speaker`)
    bayraktan ETKILENMEZ ve ETKILENMEMELIDIR: o yayilim, K15 matrisinin
    `X/None -> evet` satirinin KENDISIDIR, yani BOLUMLEME kuralinin bir
    parcasidir -- kapatilirsa K23'un korumasi gereken bolumlemenin KENDISI
    degisirdi. Bayragin alani TAM OLARAK K19/K21/K23'un GRUP SINIRLARI
    ARASI (goruntu gecisi) mirasidir.

    Kurulum: b0 etiketli + b1 etiketsiz AYNI gruba girer (uzunluk sinirini
    asmaz) -- iki bayrak degerinde de segmentin `speaker`'i `Ada`."""
    blocks = [
        TextBlock(text="Ada: kisa bir", bbox=Rect(0, 0, 200, 20), confidence=1.0),
        TextBlock(text="cumledir.", bbox=Rect(0, 22, 200, 20), confidence=1.0),
    ]
    on = _normalize_impl(blocks, OcrPreset.DIALOGUE, apply_inheritance=True)
    off = _normalize_impl(blocks, OcrPreset.DIALOGUE, apply_inheritance=False)
    assert [(s.source_blocks, s.speaker) for s in on] == [((0, 1), "Ada")]
    assert on == off, "K15 ici-grup yayilimi bayrakla kapanmis -- bolumleme kuralinin parcasi, kapanmamali"


def test_menu_icin_bayrak_hicbir_etkiye_sahip_degil_k27() -> None:
    """K27: `menu`'de `_group` HIC cagirilmadigi icin bayrak `speaker`
    dahil HICBIR seyi degistirmemeli."""
    blocks = [TextBlock(text="Ada: " + "A" * 150, bbox=Rect(0, 0, 200, 20), confidence=1.0)]
    y = 22
    for ch in "BCD":
        blocks.append(TextBlock(text=ch * 150, bbox=Rect(0, y, 200, 20), confidence=1.0))
        y += 22
    on = _normalize_impl(blocks, OcrPreset.MENU, apply_inheritance=True)
    off = _normalize_impl(blocks, OcrPreset.MENU, apply_inheritance=False)
    assert on == off
    assert [s.speaker for s in on] == ["Ada", None, None, None]


# ===========================================================================
# 3 · `_normalize_impl` SIZINTISI
# ===========================================================================


def test_normalize_impl_genel_apiye_sizmiyor() -> None:
    import src.ocr as ocr_pkg
    import src.ocr.normalizer as mod

    assert mod.__all__ == ("normalize",)
    ns: dict[str, object] = {}
    exec("from src.ocr.normalizer import *", ns)  # noqa: S102
    assert sorted(k for k in ns if not k.startswith("__")) == ["normalize"]
    assert not hasattr(ocr_pkg, "_normalize_impl")


def test_normalize_imzasi_degismedi_ve_apply_inheritance_kabul_etmiyor() -> None:
    params = list(inspect.signature(normalize).parameters)
    assert params == ["blocks", "preset"]
    with pytest.raises(TypeError):
        normalize([], OcrPreset.DIALOGUE, apply_inheritance=False)  # type: ignore[call-arg]


def test_test_kancasi_keyword_only_ve_varsayilani_true() -> None:
    for fn in (_normalize_impl, _group):
        p = inspect.signature(fn).parameters["apply_inheritance"]
        assert p.kind is inspect.Parameter.KEYWORD_ONLY
        assert p.default is True


# ===========================================================================
# 4 · K24 -- `tail` ALANI VE `current` ILE AYRISMA
# ===========================================================================

_P = get_params(OcrPreset.DIALOGUE)


def _item(text: str, x: int, y: int, w: int, h: int, speaker: str | None = None) -> _Item:
    return _Item(text=text, bbox=Rect(x=x, y=y, w=w, h=h), speaker=speaker, source_blocks=(0,))


def test_k24_ayrisma_yonu_1_birlesik_kutu_kopusu_gizler_tail_gorur() -> None:
    """KENDI geometrim: grup basi ASIRI YUKSEK (0..1000), grubun GERCEK
    kuyrugu 10..30. Aday 100..120 -> birlesik kutuyla `gap` NEGATIF
    (`None`, "kopus yok" ARTIFAKTI), `tail` ile `"gap"` (GERCEK 70px kopus).
    Kod `tail`'i kullandigi icin miras UYGULANMAMALI."""
    a1 = _item("A" * 150, 0, 0, 200, 1000, "Ada")
    a2 = _item("B" * 120, 0, 10, 200, 20)
    nxt = _item("C" * 100, 0, 100, 200, 20)
    current = _Item(
        text=a1.text + " " + a2.text,
        bbox=_union_rect(a1.bbox, a2.bbox),
        speaker="Ada",
        source_blocks=(0, 1),
    )
    assert _group_rejection_reason(a1, a2, _P) is None
    assert _group_rejection_reason(current, nxt, _P) == "length"
    assert _group_rejection_reason(current, nxt, _P, ignore_length=True) is None  # artifakt
    assert _group_rejection_reason(a2, nxt, _P, ignore_length=True) == "gap"  # gercek

    blocks = [
        TextBlock(text="Ada: " + a1.text, bbox=a1.bbox, confidence=1.0),
        TextBlock(text=a2.text, bbox=a2.bbox, confidence=1.0),
        TextBlock(text=nxt.text, bbox=nxt.bbox, confidence=1.0),
    ]
    segs = normalize(blocks, OcrPreset.DIALOGUE)
    assert [(s.source_blocks, s.speaker) for s in segs] == [((0, 1), "Ada"), ((2,), None)]


def test_k24_ayrisma_yonu_2_birlesik_kutu_reddeder_tail_izin_verir() -> None:
    """Ters yon (K24'un zorunlu testinde YOK): birlesik kutu `"overlap"`
    reddi verirken `tail` `None` diyor -- kod `tail`'i kullandigi icin miras
    UYGULANMALI. Bu, kodun gercekten `tail`'e baglandigini IKI YONDEN
    kanitlar; yalniz birinci yon sinanirsa `current` kullanan bir kod da
    testi gecebilirdi."""
    b1 = _item("A" * 150, -100, 0, 110, 20, "Ada")
    b2 = _item("B" * 120, 0, 15, 10, 20)
    nxt = _item("C" * 100, 0, 40, 100, 20)
    current = _Item(
        text=b1.text + " " + b2.text,
        bbox=_union_rect(b1.bbox, b2.bbox),
        speaker="Ada",
        source_blocks=(0, 1),
    )
    assert _group_rejection_reason(b1, b2, _P) is None
    assert _group_rejection_reason(current, nxt, _P) == "length"
    assert _group_rejection_reason(current, nxt, _P, ignore_length=True) == "overlap"
    assert _group_rejection_reason(b2, nxt, _P, ignore_length=True) is None

    blocks = [
        TextBlock(text="Ada: " + b1.text, bbox=b1.bbox, confidence=1.0),
        TextBlock(text=b2.text, bbox=b2.bbox, confidence=1.0),
        TextBlock(text=nxt.text, bbox=nxt.bbox, confidence=1.0),
    ]
    segs = normalize(blocks, OcrPreset.DIALOGUE)
    assert [(s.source_blocks, s.speaker) for s in segs] == [((0, 1), "Ada"), ((2,), "Ada")]
    off = _normalize_impl(blocks, OcrPreset.DIALOGUE, apply_inheritance=False)
    assert [s.source_blocks for s in segs] == [s.source_blocks for s in off]


def test_k24_tail_tek_ogeli_grupta_tanimli_ve_current_ile_ayni() -> None:
    """`tail` her durumda tanimli: TEK ogeli bir grupta `tail is current`
    oldugu icin ayrisma YOK, miras normal calisir."""
    blocks = [
        TextBlock(text="Ada: " + "A" * 200, bbox=Rect(0, 0, 200, 20), confidence=1.0),
        TextBlock(text="B" * 200, bbox=Rect(0, 22, 200, 20), confidence=1.0),
    ]
    segs = normalize(blocks, OcrPreset.DIALOGUE)
    assert [(s.source_blocks, s.speaker) for s in segs] == [((0,), "Ada"), ((1,), "Ada")]


def test_k24_tail_ilk_grupta_ve_ard_arda_kapanan_gruplarda_tanimli() -> None:
    """ILK grup + arka arkaya kapanan TEK ogeli gruplar: `tail` her adimda
    yeniden atanir, `IndexError`/`UnboundLocalError` yok, zincirleme miras
    dogal olarak ortaya cikar."""
    blocks = [TextBlock(text="Ada: " + "A" * 150, bbox=Rect(0, 0, 200, 20), confidence=1.0)]
    y = 22
    for ch in "BCD":
        blocks.append(TextBlock(text=ch * 150, bbox=Rect(0, y, 200, 20), confidence=1.0))
        y += 22
    segs = normalize(blocks, OcrPreset.DIALOGUE)
    assert [(s.source_blocks, s.speaker) for s in segs] == [
        ((0,), "Ada"), ((1,), "Ada"), ((2,), "Ada"), ((3,), "Ada")
    ]
    off = _normalize_impl(blocks, OcrPreset.DIALOGUE, apply_inheritance=False)
    assert [s.speaker for s in off] == ["Ada", None, None, None]
    assert [s.source_blocks for s in segs] == [s.source_blocks for s in off]


def test_k24_tail_yozlasmis_tek_ogeli_grupta_da_tanimli_miras_yok() -> None:
    """`tail` YOZLASMIS olabilir -- ama yalnizca TEK ogeli bir grupta
    (asagidaki test bunun NEDENINI sabitler). O durumda `tail` sorgusu
    `"height"` dondugu icin miras UYGULANMAZ (K16 + K19 tablosu)."""
    blocks = [
        TextBlock(text="Ada: " + "A" * 200, bbox=Rect(0, 0, 200, 20), confidence=1.0),
        TextBlock(text="B" * 200, bbox=Rect(0, 22, 200, 0), confidence=1.0),
        TextBlock(text="C" * 200, bbox=Rect(0, 24, 200, 20), confidence=1.0),
    ]
    segs = normalize(blocks, OcrPreset.DIALOGUE)
    assert [(s.source_blocks, s.speaker) for s in segs] == [((0,), "Ada"), ((1,), None), ((2,), None)]


def test_k24_cok_ogeli_grubun_taili_asla_yozlasmis_olamaz() -> None:
    """YAPISAL olgu: K16 birlesmeye ancak `min(a.h, b.h) > 0` VE
    `min(a.w, b.w) > 0` iken izin verdigi icin, bir gruba SONRADAN katilan
    her oge (= yeni `tail`) POZITIF `w`/`h` tasir. Yani `tail`'in yozlasmis
    olmasi YALNIZCA tek-ogeli gruplarda mumkundur ve orada `tail is current`
    oldugu icin `current`/`tail` ayrimi hicbir sey degistirmez."""
    rng = random.Random(7)
    izinli = yozlasmis = 0
    for _ in range(40000):
        a = _item("x", rng.randint(-5, 20), rng.randint(-5, 20), rng.choice((0, 1, 5, -3, 50)), rng.choice((0, 1, 5, -3, 50)))
        b = _item("y", rng.randint(-5, 20), rng.randint(-5, 20), rng.choice((0, 1, 5, -3, 50)), rng.choice((0, 1, 5, -3, 50)))
        if _group_rejection_reason(a, b, _P) is None:
            izinli += 1
            if b.bbox.w <= 0 or b.bbox.h <= 0:
                yozlasmis += 1
    assert izinli > 500, "izgara birlesme izni veren cift uretmemis -- test totoloji"
    assert yozlasmis == 0


# ===========================================================================
# 5 · BULGU R5-1 -- `tail` "HAM oge" DEGIL: hyphen-birlesik kuyruk K24'un
#     kaldirmayi VAAT ETTIGI artifakti GERI GETIRIYOR
# ===========================================================================
#
# K24 (sef_karari-tur5.md): "SOL TARAF, kapanan grubun okuma sirasindaki SON
# KAYNAK OGESIDIR -- birikmis grubun birlesik `bbox`'i DEGIL. Birlesik kutu
# grubun en alta uzanan ogesinin `bottom`'unu tasidigi icin GERCEK satir-arasi
# boslugu OLCMEZ."  `_group` docstring'i: "`tail`, ... grubun okuma-sirasindaki
# SON (birlesime en son katilan) HAM ogesidir".
#
# `tail` GERCEKTE `_group`'a GIREN son OGEDIR -- ve o oge, adim 3'te
# (`_merge_hyphenated`) IKI YA DA DAHA COK ham blogun BIRLESIMI olabilir.
# `_merge_hyphenated` HICBIR geometrik kontrol YAPMAZ (K5 salt tipografik:
# "tire ile bitiyor + sonraki kucuk harfle basliyor"), yani birlesik kutu
# ISTEDIGI KADAR buyuyebilir. Boyle bir `tail` ile yapilan miras-uygunluk
# sorgusu, K24'un step-5 icin kaldirdigi artifaktin AYNISINI step-3
# uzerinden geri getirir: kod, GERCEK bir geometrik kopusun OTESINE
# `speaker` ATFEDER (K19 tablosu: "geometrik bosluk -> `None` KALIR").
#
# Uc bagimsiz geometrik yol; UCUNU de KENDIM kurdum. Yol A `bottom`
# artifaktini (non-monotonik uzanim), yol B ve C ise MONOTONIK -- yani
# okuma sirasina TAMAMEN uygun -- geometrilerde `min(h)` / `overlap`+
# `min(w)` SISMESINI kullanir. B ve C, "bu bulgu ancak egzotik geometride
# olur" savunmasini KAPATIR.


def _last_raw_rect(item: _Item, blocks: list[TextBlock]) -> Rect:
    """Ogenin okuma sirasindaki SON HAM blogunun `bbox`'i -- K24'un
    "grubun okuma sirasindaki SON KAYNAK OGESI" ifadesinin birebir
    okunusu. (Okuma sirasi `(y, x)`; etiket-blok indeksleri K9 geregi
    daima ONCE geldigi icin son eleman DAIMA gercek son metin satiridir.)"""
    idxs = sorted(item.source_blocks, key=lambda i: (blocks[i].bbox.y, blocks[i].bbox.x))
    return blocks[idxs[-1]].bbox


def _items_of(blocks: list[TextBlock], params: NormalizerParams) -> list[_Item]:
    """`_normalize_impl`'in 1-4. adimlari (src'deki AYNI yardimcilarla)."""
    ordered = sorted(enumerate(blocks), key=lambda p: (p[1].bbox.y, p[1].bbox.x))
    items = [
        _Item(text=b.text, bbox=b.bbox, speaker=None, source_blocks=(i,))
        for i, b in ordered
        if b.confidence >= params.confidence_threshold
    ]
    items = [it for it in items if not _is_noise(it.text)]
    items = [replace(it, text=_collapse_intraline(it.text)) for it in items]
    return _extract_speakers(_merge_hyphenated(items))


# R5-1'in uc yolu: (ad, blocks, kodun `tail` sorgusu, HAM son satir sorgusu)
_R51_YOL_A = [
    TextBlock(text="Ada: " + "X" * 130, bbox=Rect(0, 0, 240, 18), confidence=0.9),
    TextBlock(text="Y" * 90 + " son-", bbox=Rect(0, 20, 240, 50), confidence=0.9),
    TextBlock(text="raki", bbox=Rect(0, 26, 240, 18), confidence=0.9),
    TextBlock(text="Z" * 140, bbox=Rect(0, 60, 240, 18), confidence=0.9),
]
_R51_YOL_B = [
    TextBlock(text="Ada: " + "X" * 130, bbox=Rect(0, -20, 240, 18), confidence=0.9),
    TextBlock(text="Y" * 90 + " son-", bbox=Rect(0, 0, 240, 18), confidence=0.9),
    TextBlock(text="raki", bbox=Rect(0, 30, 240, 5), confidence=0.9),
    TextBlock(text="Z" * 140, bbox=Rect(0, 40, 240, 18), confidence=0.9),
]
_R51_YOL_C = [
    TextBlock(text="Ada: " + "X" * 130, bbox=Rect(0, -20, 240, 18), confidence=0.9),
    TextBlock(text="Y" * 90 + " son-", bbox=Rect(0, 0, 240, 18), confidence=0.9),
    TextBlock(text="raki", bbox=Rect(300, 20, 8, 18), confidence=0.9),
    TextBlock(text="Z" * 140, bbox=Rect(0, 40, 240, 18), confidence=0.9),
]
_R51_YOLLAR = (
    ("A/non-monotonik: bottom artifakti", _R51_YOL_A, "gap", False),
    ("B/MONOTONIK: min(h) sismesi", _R51_YOL_B, "gap", True),
    ("C/MONOTONIK: overlap+min(w) sismesi", _R51_YOL_C, "overlap", True),
)


@pytest.mark.parametrize(("ad", "blocks", "ham_sebep", "monotonik"), _R51_YOLLAR)
def test_r51_mekanizma_hyphen_birlesik_tail_ham_son_satirdan_ayrisiyor(
    ad: str, blocks: list[TextBlock], ham_sebep: str, monotonik: bool
) -> None:
    """MEKANIZMA (bu test YESIL -- bulgunun KENDISI degil, SEBEBI):
    grubun `tail`'i adim 3'te birlesmis COK BLOKLU bir ogedir; onun
    BIRLESIK bbox'iyla yapilan miras-uygunluk sorgusu `None` ("kopus yok")
    derken, K24'un ifadesinin birebir okunusu (grubun okuma sirasindaki SON
    HAM blogu) GERCEK bir red sebebi dondurur. `monotonik=True` yollarda
    birlesik kutunun `bottom`'u ham son satirla AYNIDIR -- yani bulgunun
    non-monotonik/egzotik geometriye IHTIYACI YOKTUR."""
    items = _items_of(blocks, _P)
    assert len(items) == 3, f"{ad}: kurulum hatali, adim 3 sonrasi {len(items)} oge"
    tail = items[1]  # grubun kuyrugu: adim 3'te HYPHEN ile birlesmis COK BLOKLU oge
    aday = items[2]
    assert len(tail.source_blocks) > 1, f"{ad}: kurulum hatali, tail cok bloklu degil"

    # grubun birikmis `current`'i (kod bunu ANA birlestirme karari icin kullanir)
    assert _group_rejection_reason(items[0], tail, _P) is None, f"{ad}: ilk cift birlesmiyor"
    current = _Item(
        text=items[0].text + " " + tail.text,
        bbox=_union_rect(items[0].bbox, tail.bbox),
        speaker=items[0].speaker,
        source_blocks=tuple(sorted((*items[0].source_blocks, *tail.source_blocks))),
    )
    assert _group_rejection_reason(current, aday, _P) == "length", f"{ad}: sinir uzunluk sinirinda kapanmiyor"

    ham = replace(tail, bbox=_last_raw_rect(tail, blocks))
    assert (ham.bbox.bottom == tail.bbox.bottom) is monotonik, ad
    assert _group_rejection_reason(tail, aday, _P, ignore_length=True) is None, f"{ad}: artifakt yok"
    assert _group_rejection_reason(ham, aday, _P, ignore_length=True) == ham_sebep, ad


@pytest.mark.parametrize(("ad", "blocks", "ham_sebep", "monotonik"), _R51_YOLLAR)
def test_r51_kuyruk_gercek_geometrik_kopusun_otesine_speaker_atfetmiyor(
    ad: str, blocks: list[TextBlock], ham_sebep: str, monotonik: bool
) -> None:
    """TUR 6 -- BULGU R5-1 KAPANDI, test YESILE CEVRILDI.

    Tur 5'te bu test `xfail(strict=True)` idi; K28 uygulandiktan sonra
    UCU DE XPASS verdi (tur 6 taban koşumu: 3 failed = 3 XPASS(strict)).
    Artik DUZELTILMIS davranisi DOGRULAR: K19 tablosu "geometrik bosluk
    -> `None` KALIR" diyor; aday blok ile grubun GERCEK son metin satiri
    arasinda gercek bir kopus var (ustteki mekanizma testi bunu hala
    sabitliyor) ve kod ARTIK mirasi UYGULAMIYOR."""
    segs = normalize(blocks, OcrPreset.DIALOGUE)
    assert [(s.source_blocks, s.speaker) for s in segs] == [((0, 1, 2), "Ada"), ((3,), None)], ad


@pytest.mark.parametrize(("ad", "blocks", "ham_sebep", "monotonik"), _R51_YOLLAR)
def test_r6_duzeltmenin_MEKANIZMASI_sorgu_ham_blok_ciftiyle_yapiliyor(
    ad: str, blocks: list[TextBlock], ham_sebep: str, monotonik: bool
) -> None:
    """Ustteki test yalnizca SONUCU (segment listesi) dogrular; bu test
    duzeltmenin MEKANIZMASINI dogrular -- dogru sonucu YANLIS sebeple
    ureten bir uygulama buradan gecemez.

    `sorgu_kaydi()` (sef kiti) miras sorgusunu yakalar; sorgunun IKI
    tarafinin da OZGUN bloklardan geldigi (sol = kuyrugun okuma
    sirasindaki SON ham blogu, sag = adayin okuma sirasindaki ILK ham
    blogu) VE sorgunun ARTIK bir red sebebi dondurdugu sabitlenir."""
    with sorgu_kaydi() as kayit:
        normalize(blocks, OcrPreset.DIALOGUE)
    miras = [sg for sg in kayit if sg.miras]
    assert len(miras) == 1, f"{ad}: beklenen tek miras sorgusu, gozlenen {len(miras)}"
    sg = miras[0]
    assert sg.sol_sb == (1, 2) and sg.sag_sb == (3,), ad
    assert sg.sol_bbox == blocks[okuma_sirasi(blocks, sg.sol_sb)[-1]].bbox, (
        f"{ad}: sol taraf ham blogun bbox'i degil -- olculen {sg.sol_bbox}"
    )
    assert sg.sag_bbox == blocks[okuma_sirasi(blocks, sg.sag_sb)[0]].bbox, (
        f"{ad}: sag taraf ham blogun bbox'i degil -- olculen {sg.sag_bbox}"
    )
    # ... ve bu ciftle sorulan sorgu GERCEK sebebi doner (miras UYGULANMAZ).
    sol = _Item(text="", bbox=sg.sol_bbox, speaker="Ada", source_blocks=sg.sol_sb)
    sag = _Item(text="", bbox=sg.sag_bbox, speaker=None, source_blocks=sg.sag_sb)
    assert _group_rejection_reason(sol, sag, _P, ignore_length=True) == ham_sebep, ad


@pytest.mark.parametrize(("ad", "blocks", "ham_sebep", "monotonik"), _R51_YOLLAR)
def test_r6_ayni_fixture_tur5_sorgu_bicimiyle_HALA_yanlis_sonuc_verir(
    ad: str, blocks: list[TextBlock], ham_sebep: str, monotonik: bool
) -> None:
    """DISLERIN KANITI: ustteki iki test, K28 KALDIRILIRSA gercekten
    kiriliyor mu? Ayni fixture, TUR 5'in sorgu bicimiyle (ham ikame YOK,
    sorgu dogrudan `tail`/`nxt` ile) kosulur ve `speaker`'in gercek
    kopusun OTESINE atfedildigi -- yani bulgunun geri geldigi --
    gosterilir. Ayni girdi iki bicimde ZIT sonuc veriyorsa fixture
    ayirt edicidir."""

    def _group_tur5(
        items: list[_Item],
        params: NormalizerParams,
        *,
        blocks: Sequence[TextBlock] = (),
        apply_inheritance: bool = True,
    ) -> list[_Item]:
        if not items:
            return []
        groups: list[_Item] = []
        sinirlar: list[bool] = []
        current = items[0]
        tail = items[0]
        for nxt in items[1:]:
            reason = _group_rejection_reason(current, nxt, params)
            if reason is None:
                current = _Item(
                    text=current.text + " " + nxt.text,
                    bbox=_union_rect(current.bbox, nxt.bbox),
                    speaker=current.speaker,
                    source_blocks=tuple(sorted((*current.source_blocks, *nxt.source_blocks))),
                )
                tail = nxt
            else:
                groups.append(current)
                sinirlar.append(
                    reason == "length"
                    and nxt.speaker is None
                    # TUR 5: HAM IKAME YOK -- sorgu dogrudan `tail`/`nxt` ile.
                    and _group_rejection_reason(tail, nxt, params, ignore_length=True) is None
                )
                current = nxt
                tail = nxt
        groups.append(current)
        if apply_inheritance:
            for i, tek_uzunluk in enumerate(sinirlar, start=1):
                if tek_uzunluk and groups[i - 1].speaker is not None:
                    groups[i] = replace(groups[i], speaker=groups[i - 1].speaker)
        return groups

    eski = _normalize_with(blocks, OcrPreset.DIALOGUE, _group_tur5)
    assert [(s.source_blocks, s.speaker) for s in eski] == [((0, 1, 2), "Ada"), ((3,), "Ada")], (
        f"{ad}: tur 5 bicimi bu fixture'da BULGUYU URETMIYOR -- fixture ayirt edici degil"
    )
    yeni = normalize(blocks, OcrPreset.DIALOGUE)
    assert [(s.source_blocks, s.speaker) for s in yeni] != [
        (s.source_blocks, s.speaker) for s in eski
    ], ad


# ===========================================================================
# 6 · TUR 6 -- YENI MAKINE DENETIMI (eski `test_r51_makine_denetimi_*`
#     YERINE; sef_karari-tur6.md, mercek A/1)
# ===========================================================================
#
# ESKI DENETIM NEDEN DEGISTIRILDI: `test_r51_makine_denetimi_ham_son_blok_
# kuralinda_sifir_ayrisma` `_group`'u ve `normalize`'i HIC CAGIRMIYORDU --
# `_group_rejection_reason`'i dogrudan cagirip gruplama dongusunu TEST
# ICINDE kuruyordu. Bu yuzden `_group`'taki HICBIR duzeltme onu XPASS
# yapamazdi ve tur 6 tabaninda hala `xfailed` gorunuyordu (sef de bunu
# dogruladi). Yerine gecen denetim:
#   * URUNUN KENDI yolundan gecer -- `normalize` cagrilir, sorgular sef
#     kitinin `sorgu_kaydi()` kancasiyla yakalanir (kanca DEGISMEZI
#     kancalar: ikame nerede yapilirsa yapilsin cagri oradan gecer);
#   * SIRASIZ girdi icerir (K3: girdi listesi okuma sirasinda OLMAK
#     ZORUNDA DEGIL) ve indeks sirasi ile okuma sirasinin AYRISTIGI
#     sinirlari AYRICA sayar -- `okuma_sirasi(...)[-1]` yerine
#     `max(...)` yazan bir uygulama ancak orada gorunur;
#   * >=3 BLOKLU KUYRUK icerir (iki elemanli bir kumede `sirali[-1]` ile
#     `sirali[1]` AYNI seydir -- off-by-one gorunmez);
#   * referansi KITTEN DEGIL, bu dosyanin KENDI okuma-sirasi
#     uygulamasindan turetir (kit yalnizca kanca icin kullanilir).


def _kendi_okuma_sirasi(blocks: list[TextBlock], idxs: tuple[int, ...]) -> list[int]:
    """K28'in okuma sirasi -- BU DOSYANIN BAGIMSIZ uygulamasi.

    Kitin `okuma_sirasi`'si ile ayni sonucu vermeli; referansi kitten
    almamak icin ayri yazildi (kit hatali olsaydi denetim onunla birlikte
    kayardi -- PROTOKOL S4.6/8)."""
    return sorted(idxs, key=lambda i: (blocks[i].bbox.y, blocks[i].bbox.x, i))


def _sirasiz_derlem() -> list[list[TextBlock]]:
    """Tur 6 denetiminin derlemi: mevcut alti ureticinin dort tohumlu
    ciktisi + HER girdinin ayrica KARISTIRILMIS bir kopyasi (K3).

    Karistirma ayri bir `Random` ile yapilir; girdi indeksleri boylece
    okuma sirasindan sistematik olarak AYRISIR."""
    karistirici = random.Random(20260910)
    out: list[list[TextBlock]] = []
    for seed in SEEDS:
        for blocks in _corpus(seed):
            out.append(blocks)
            kopya = list(blocks)
            karistirici.shuffle(kopya)
            out.append(kopya)
    return out


def _r6_denetim(derlem: list[list[TextBlock]] | None = None) -> dict[str, object]:
    """TUR 6 makine denetiminin GOVDESI -- hem urun uzerinde hem de
    (mutant sondasinda) yamalanmis bir `_raw_query_pair` uzerinde ayni
    kodla kosulur ki "0 ayrisma" ile "mutantta >0 ayrisma" AYNI olcuden
    gelsin."""
    sinir = coklu_sol = uclu_sol = coklu_sag = ayirt_edici = 0
    ayrisma = 0
    ilk_fark = ""
    for blocks in derlem if derlem is not None else _sirasiz_derlem():
        for preset in PRESETS:
            with sorgu_kaydi() as kayit:
                try:
                    normalize(blocks, preset)
                except (ValueError, IndexError) as exc:  # K7/K10 -- girdi kaynakli
                    assert isinstance(exc, ValueError), f"beklenmeyen IndexError: {exc}"
                    continue
            for sg in kayit:
                if not sg.miras:
                    continue
                sinir += 1
                if len(sg.sol_sb) > 1:
                    coklu_sol += 1
                if len(sg.sol_sb) >= 3:
                    uclu_sol += 1
                if len(sg.sag_sb) > 1:
                    coklu_sag += 1
                sol_i = _kendi_okuma_sirasi(blocks, sg.sol_sb)[-1]
                sag_i = _kendi_okuma_sirasi(blocks, sg.sag_sb)[0]
                if sol_i != max(sg.sol_sb) or sag_i != min(sg.sag_sb):
                    ayirt_edici += 1
                if sg.sol_bbox != blocks[sol_i].bbox or sg.sag_bbox != blocks[sag_i].bbox:
                    ayrisma += 1
                    if not ilk_fark:
                        ilk_fark = (
                            f"sol_sb={sg.sol_sb} beklenen={blocks[sol_i].bbox} "
                            f"olculen={sg.sol_bbox} | sag_sb={sg.sag_sb} "
                            f"beklenen={blocks[sag_i].bbox} olculen={sg.sag_bbox}"
                        )
    return {
        "sinir": sinir,
        "coklu_sol": coklu_sol,
        "uclu_sol": uclu_sol,
        "coklu_sag": coklu_sag,
        "ayirt_edici": ayirt_edici,
        "ayrisma": ayrisma,
        "ilk_fark": ilk_fark,
    }


def test_r6_makine_denetimi_normalize_uzerinden_ham_sorgu_cifti() -> None:
    """TUR 6 MAKINE DENETIMI (eski dorduncu xfail'in yerine).

    `normalize` uzerinden gecen HER miras-uygunluk sorgusunun IKI
    tarafinin da OZGUN `TextBlock` listesinden geldigi dogrulanir:
    sol = kuyrugun okuma sirasindaki SON ham blogu, sag = adayin okuma
    sirasindaki ILK ham blogu (K28). Referans bu dosyanin KENDI
    uygulamasiyla hesaplanir.

    Denetimin TOTOLOJI OLMADIGI alt sinirlarla sabitlenir: gozlenen
    sinir sayisi, >=3 bloklu kuyruk, cok bloklu SAG taraf ve -- en
    onemlisi -- indeks sirasinin okuma sirasindan AYRISTIGI sinirlar."""
    r = _r6_denetim()
    sinir = int(r["sinir"])  # type: ignore[arg-type]
    coklu_sol = int(r["coklu_sol"])  # type: ignore[arg-type]
    uclu_sol = int(r["uclu_sol"])  # type: ignore[arg-type]
    coklu_sag = int(r["coklu_sag"])  # type: ignore[arg-type]
    ayirt_edici = int(r["ayirt_edici"])  # type: ignore[arg-type]
    ayrisma = int(r["ayrisma"])  # type: ignore[arg-type]
    ilk_fark = r["ilk_fark"]
    assert sinir > 1000, f"denetim totoloji: gozlenen miras sorgusu {sinir}"
    assert coklu_sol > 200, f"cok bloklu kuyruk uretilmemis ({coklu_sol})"
    assert uclu_sol > 50, f">=3 bloklu kuyruk uretilmemis ({uclu_sol}) -- off-by-one gorunmez"
    assert coklu_sag > 50, f"cok bloklu SAG taraf uretilmemis ({coklu_sag})"
    assert ayirt_edici > 20, (
        f"indeks sirasi ile okuma sirasinin ayristigi sinir uretilmemis ({ayirt_edici}) -- "
        "`max(sb)` yazan bir uygulama bu denetimden gecerdi"
    )
    assert ayrisma == 0, f"gozlenen sinir={sinir} ayrisma={ayrisma} | ilk fark: {ilk_fark}"


def test_r6_makine_denetiminin_disleri_var_indeks_sirasi_mutanti_yakalaniyor() -> None:
    """SONDA KONTROLU 1 -- AYNI DENETIM govdesi, `_raw_query_pair`
    OKUMA SIRASI yerine INDEKS SIRASI kullanacak sekilde yamalanmis
    urun uzerinde. Denetim burada ayrisma BULMAK ZORUNDA; bulmazsa
    ustteki "0 ayrisma" hicbir sey ispatlamaz.

    (Yama YALNIZCA test suresince urun MODULUNUN oznitelgindedir; `src/`
    altindaki DOSYA degistirilmez -- PROTOKOL: tester urun kodunu
    duzenlemez.)"""

    def indeks_sirasi_mutanti(
        tail: _Item, nxt: _Item, blocks: Sequence[TextBlock]
    ) -> tuple[_Item, _Item]:
        return (
            replace(tail, bbox=blocks[max(tail.source_blocks)].bbox),
            replace(nxt, bbox=blocks[min(nxt.source_blocks)].bbox),
        )

    orij = normalizer_modulu._raw_query_pair
    normalizer_modulu._raw_query_pair = indeks_sirasi_mutanti  # type: ignore[assignment]
    try:
        r = _r6_denetim(_sirasiz_derlem()[:600])
    finally:
        normalizer_modulu._raw_query_pair = orij  # type: ignore[assignment]
    assert int(r["sinir"]) > 100, f"sonda totoloji: sinir={r['sinir']}"  # type: ignore[arg-type]
    assert int(r["ayrisma"]) > 0, (  # type: ignore[arg-type]
        f"denetim INDEKS SIRASI mutantini yakalamiyor (sinir={r['sinir']}) -- dissiz"
    )


def test_r6_makine_denetiminin_disleri_var_tur5_bicimi_ayrisiyor() -> None:
    """SONDA KONTROLU: ustteki denetim "0 ayrisma" diyor -- ayni derlem ve
    ayni referans, TUR 5'in sorgu bicimi (ham ikame YOK) uzerinde
    AYRISMA BULMALI. Bulamazsa "0 ayrisma" hicbir sey ispatlamaz."""
    ayrisma = 0
    sinir = 0
    for blocks in _sirasiz_derlem()[:400]:
        for preset in PRESETS:
            params = get_params(preset)
            try:
                items = _items_of(blocks, params)
            except ValueError:
                continue
            if not items:
                continue
            current = items[0]
            tail = items[0]
            for nxt in items[1:]:
                reason = _group_rejection_reason(current, nxt, params)
                if reason is None:
                    current = _Item(
                        text=current.text + " " + nxt.text,
                        bbox=_union_rect(current.bbox, nxt.bbox),
                        speaker=current.speaker,
                        source_blocks=tuple(sorted((*current.source_blocks, *nxt.source_blocks))),
                    )
                    tail = nxt
                else:
                    if reason == "length" and nxt.speaker is None:
                        sinir += 1
                        sol_i = _kendi_okuma_sirasi(blocks, tail.source_blocks)[-1]
                        sag_i = _kendi_okuma_sirasi(blocks, nxt.source_blocks)[0]
                        # TUR 5: sorgu `tail`/`nxt`in KENDI (birlesik olabilen)
                        # bbox'lariyla yapiliyordu.
                        if tail.bbox != blocks[sol_i].bbox or nxt.bbox != blocks[sag_i].bbox:
                            ayrisma += 1
                    current = nxt
                    tail = nxt
    assert sinir > 100, f"sonda kontrolu totoloji: incelenen sinir {sinir}"
    assert ayrisma > 0, (
        f"tur 5 bicimi bu derlemde HIC ayrismiyor ({sinir} sinir) -- denetim dissiz"
    )
