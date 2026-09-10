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

**BULGU R5-1 (BLOKE EDICI, bkz. `feedback-A.md`):** `tail`, docstring'in
KOSULSUZ iddia ettigi gibi HER ZAMAN "grubun son HAM ogesi" DEGIL -- adim
3'un (hyphen birlesimi, `_merge_hyphenated`) urettigi COK BLOKLU bir oge de
`tail` olabiliyor ve onun BIRLESIK bbox'i, K24'un tam olarak kaldirmayi vaat
ettigi artifakti GERI GETIRIYOR. 5. bolum bunu UC ayri geometrik yolla ve bir
MAKINE denetimiyle sabitler; dordu de `xfail(strict=True)` -- kod duzelirse
XPASS testi KIRAR, yani bulgu sessizce kapatilamaz. Uc yoldan IKISI
MONOTONIK'tir (dikey uzanim okuma sirasina UYGUN, "egzotik" geometri
GEREKMEZ): hyphen-birlesik kutunun `h`/`w`'sini SISIRMESI tek basina yeter.
"""
from __future__ import annotations

import inspect
import random
from dataclasses import replace

import pytest

from src.contracts.models import OcrPreset, Rect, Segment, TextBlock
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


def _group_tur4(items: list[_Item], params: NormalizerParams, *, apply_inheritance: bool = True) -> list[_Item]:
    """TUR 4'un mekanizmasi: miras, mute edilmis `speaker`'i BIR SONRAKI
    gruplama kararina GIRDI yapar (kirmizi takimin B1 bulgusu). Bu dosyanin
    K23 karsilastiricisinin DISLERI oldugunu ispatlamak icin yeniden kuruldu
    -- `src/` altindaki koda DOKUNULMAZ."""
    if not items:
        return []
    groups: list[_Item] = []
    current = items[0]
    for nxt in items[1:]:
        reason = _group_rejection_reason(current, nxt, params)
        if reason is None:
            current = _Item(
                text=current.text + " " + nxt.text,
                bbox=_union_rect(current.bbox, nxt.bbox),
                speaker=current.speaker,
                source_blocks=tuple(sorted((*current.source_blocks, *nxt.source_blocks))),
            )
        else:
            groups.append(current)
            if (
                apply_inheritance
                and reason == "length"
                and current.speaker is not None
                and nxt.speaker is None
                and _group_rejection_reason(current, nxt, params, ignore_length=True) is None
            ):
                nxt = replace(nxt, speaker=current.speaker)
            current = nxt
    groups.append(current)
    return groups


def _group_mirassiz(items: list[_Item], params: NormalizerParams) -> list[_Item]:
    """"MIRAS MEKANIZMASI HIC VAR OLMASAYDI" -- miras kodu SIFIR."""
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
    grupleyicisi degistirilebilir."""
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
    grouped = grouper(items, params, **kw) if params.should_group else items
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
    Bulamazsa yukaridaki "0 fark" sonucu hicbir sey ispatlamaz."""
    farklar = 0
    for seed in SEEDS:
        for blocks in _corpus(seed):
            for preset in PRESETS:
                try:
                    a = _normalize_with(blocks, preset, _group_tur4, apply_inheritance=True)
                    b = _normalize_with(blocks, preset, _group_tur4, apply_inheritance=False)
                except (ValueError, TypeError):
                    continue
                if _partition(a) != _partition(b):
                    farklar += 1
    assert farklar > 0, "karsilastirici tur 4'un bilinen B1 hatasini bile yakalamiyor -- sonda kor"


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
@pytest.mark.xfail(
    reason="BULGU R5-1 (BLOKE EDICI, feedback-A.md): `tail` her zaman 'grubun son HAM "
    "ogesi' DEGIL -- adim 3'un hyphen birlesimi COK BLOKLU bir oge uretebilir ve onun "
    "BIRLESIK bbox'i, K24'un step-5 icin kaldirdigi artifakti step-3 uzerinden GERI "
    "GETIRIR; `speaker` GERCEK bir geometrik kopusun OTESINE atfediliyor (K19 tablosu: "
    "'geometrik bosluk -> None KALIR'). Uc yolun IKISI monotoniktir.",
    strict=True,
)
def test_r51_kuyruk_gercek_geometrik_kopusun_otesine_speaker_atfetmiyor(
    ad: str, blocks: list[TextBlock], ham_sebep: str, monotonik: bool
) -> None:
    """BULGU (bu test KIRMIZI -- `xfail(strict=True)`, kod duzelirse XPASS
    ile KIRILIR): K19 tablosu "geometrik bosluk -> `None` KALIR" diyor.
    Aday blok ile grubun GERCEK son metin satiri arasinda gercek bir kopus
    var (yukaridaki mekanizma testi bunu sabitliyor), ama kod mirasi
    UYGULUYOR."""
    segs = normalize(blocks, OcrPreset.DIALOGUE)
    assert [(s.source_blocks, s.speaker) for s in segs] == [((0, 1, 2), "Ada"), ((3,), None)], ad


@pytest.mark.xfail(
    reason="BULGU R5-1 (BLOKE EDICI) -- MAKINE DENETIMI: derlemde K24'un ifadesinin "
    "birebir okunusuyla (grubun okuma sirasindaki SON HAM BLOGU) kodun item-duzeyi "
    "`tail`'i binlerce sinirda ayrisiyor.",
    strict=True,
)
def test_r51_makine_denetimi_ham_son_blok_kuralinda_sifir_ayrisma() -> None:
    """R5-1'in TEK bir elle kurulmus nokta OLMADIGINI makineyle gosterir:
    tek tohumlu derlem (630 girdi) x uc gruplayan on ayar taranir; her
    uzunluk-sinirinda kodun `tail` sorgusu ile HAM son blok sorgusu
    karsilastirilir. Tek fark bile K24'un ifadesinin kodda tutmadigini
    gosterir; sayilar `verdict-A.md`/`feedback-A.md`'de raporlanir."""
    kod_evet_ham_hayir = 0
    kod_hayir_ham_evet = 0
    sinir = 0
    for blocks in _corpus(SEEDS[0]):
        for preset in (OcrPreset.DIALOGUE, OcrPreset.TOOLTIP, OcrPreset.SUBTITLE):
            params = get_params(preset)
            items = _items_of(blocks, params)
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
                        kod = _group_rejection_reason(tail, nxt, params, ignore_length=True) is None
                        ham_tail = replace(tail, bbox=_last_raw_rect(tail, blocks))
                        ham = _group_rejection_reason(ham_tail, nxt, params, ignore_length=True) is None
                        if kod and not ham:
                            kod_evet_ham_hayir += 1
                        elif ham and not kod:
                            kod_hayir_ham_evet += 1
                    current = nxt
                    tail = nxt
    assert sinir > 1000, f"denetim totoloji: incelenen uzunluk-siniri {sinir}"
    assert (kod_evet_ham_hayir, kod_hayir_ham_evet) == (0, 0), (
        f"incelenen uzunluk-siniri={sinir} · kod MIRAS VER/ham MIRAS YOK={kod_evet_ham_hayir} · "
        f"kod MIRAS YOK/ham MIRAS VER={kod_hayir_ham_evet}"
    )
