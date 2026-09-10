r"""TESTER-A · TUR 6 · MERCEK: GARANTI ALANI -- K28'in SINIR ALANI.

`test_r5_partition_invariant.py` tur 6'da K23/K24/K28'in **davranisini** ve
xfail'den donusen uc varyanti kapsar; bu dosya merceğin KALAN uc sorusunu
tasir (sef_karari-tur6.md, "MERCEK A" maddeleri 2-4 ve mercegin ASIL
sorusu):

  2. **`source_blocks` HER durumda tanimli mi** -- tek bloklu grup, bos
     grup, `_group([], params)`, tek ogeli liste; ve `_raw_query_pair`'in
     sinir durumlari: `blocks=()`, tek elemanli `source_blocks`, indeks
     aralik disi.
  3. **Zincirleme miras** `tests/unit/ocr/` altinda PINLI mi -- ve zincir
     gercekten UC segmentle SINIRLI DEGIL mi.
  4. **Docstring/tip ne soz veriyor, KABUL EDILEN HER girdi icin tutuyor
     mu** -- merceğin asil sorusu; T-003'un kirildigi hata sinifi
     (KOSULSUZ iddia, DAR gecerlilik).

Ayrica tur 6'ya OZGU, baska hicbir yerde olculmeyen bir denklik:
**K28'in KARAR METNI** sol tarafi "kapanan GRUBUN kaynak bloklari
arasinda okuma sirasinda son gelen blok" diye tanimlar; **UYGULAMA** ise
`tail` OGESININ kaynak bloklarindan secer. Ikisi ancak adim 1-4'un
ogeleri okuma sirasinda BITISIK kosulara bolmesi sayesinde ayni seydir --
bu dosya once denkligi olcer, sonra denkligi mumkun kilan YAPISAL
ozelligi ayrica sabitler.

Kit (`olcu_kiti.py`) YALNIZCA kanca (`sorgu_kaydi`) ve okuma-sirasi
tanimi icin ice aktarilir; DEGISTIRILMEZ. Referanslar bu dosyanin KENDI
uygulamasindan turetilir (PROTOKOL S4.6/8).
"""
from __future__ import annotations

import ast
import random
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path

import pytest

from olcu_kiti import okuma_sirasi, sorgu_kaydi
from src.contracts.models import OcrPreset, Rect, TextBlock
from src.ocr import normalizer as normalizer_modulu
from src.ocr.normalizer import (
    _collapse_intraline,
    _extract_speakers,
    _group,
    _is_noise,
    _Item,
    _merge_hyphenated,
    _raw_query_pair,
    _split_speaker_label,
    normalize,
)
from src.ocr.presets import NormalizerParams, get_params

PRESETS = (OcrPreset.DIALOGUE, OcrPreset.MENU, OcrPreset.TOOLTIP, OcrPreset.SUBTITLE)
GRUPLAYAN = (OcrPreset.DIALOGUE, OcrPreset.TOOLTIP, OcrPreset.SUBTITLE)

_URUN = Path(__file__).resolve().parents[4] / "src" / "ocr" / "normalizer.py"
_IMPLEMENTER_TESTI = (
    Path(__file__).resolve().parents[4] / "tests" / "unit" / "ocr" / "test_normalizer.py"
)


def _blk(text: str, x: int, y: int, w: int = 240, h: int = 18, c: float = 1.0) -> TextBlock:
    return TextBlock(text=text, bbox=Rect(x=x, y=y, w=w, h=h), confidence=c)


def _item(
    text: str, sb: tuple[int, ...], *, x: int = 0, y: int = 0, w: int = 240, h: int = 18,
    speaker: str | None = None,
) -> _Item:
    return _Item(text=text, bbox=Rect(x=x, y=y, w=w, h=h), speaker=speaker, source_blocks=sb)


# ===========================================================================
# DUSMAN DERLEM -- kitin derleminden ve `test_r5_partition_invariant.py`nin
# ureticilerinden KASITLI olarak farkli: yalniz-etiket bloklari, tam esit
# `(y, x)` ciftleri, yozlasmis geometri ve KARISTIRILMIS girdi sirasi.
# ===========================================================================

_AD = ("Ada", "Bora", "勇者", "魔王")
_GOVDE = ("merhaba dunya", "bu uzun bir cumledir", "こんにちは", "tra-", "dition", "X" * 90)


def _gen_etiket_zinciri(rng: random.Random) -> list[TextBlock]:
    """Yalniz-etiket bloklari + govde: K9'un `pending_blocks` yolu."""
    bl: list[TextBlock] = []
    y = 0
    for _ in range(rng.randint(2, 5)):
        bl.append(_blk(f"{rng.choice(_AD)}:", 0, y, w=60))
        y += 20
        for _ in range(rng.randint(1, 3)):
            bl.append(_blk(rng.choice(_GOVDE), 0, y, h=rng.choice([18, 18, 1])))
            y += rng.choice([19, 20, 24, 60])
    return bl


def _gen_hyphen_etiket(rng: random.Random) -> list[TextBlock]:
    """Adim 3'un cok bloklu `_Item`'lari + etiket tasima birlikte."""
    bl = [_blk(f"{rng.choice(_AD)}:", 0, 0, w=60)]
    y = 20
    for _ in range(rng.randint(3, 6)):
        bl.append(_blk("keli-", 0, y, w=rng.choice([240, 8])))
        y += 20
        bl.append(_blk("me " + rng.choice(_GOVDE), 0, y))
        y += rng.choice([20, 22, 90])
    return bl


def _gen_esit_yx(rng: random.Random) -> list[TextBlock]:
    """TAM ESIT `(y, x)` cifti tasiyan bloklar -- okuma sirasinin ucuncu
    (girdi indeksi) bileseni ancak burada belirleyici olur."""
    bl: list[TextBlock] = []
    for k in range(rng.randint(3, 7)):
        y = 20 * (k // 2)
        bl.append(_blk(rng.choice(_GOVDE), 0, y, w=rng.choice([240, 120]), h=rng.choice([18, 9])))
    return bl


def _gen_yozlasmis(rng: random.Random) -> list[TextBlock]:
    bl: list[TextBlock] = []
    y = 0
    for _ in range(rng.randint(2, 6)):
        bl.append(
            _blk(
                rng.choice(_GOVDE),
                rng.choice([-40, 0, 300]),
                y,
                w=rng.choice([-5, 0, 1, 240]),
                h=rng.choice([-5, 0, 1, 18]),
                c=rng.choice([0.44, 0.9, 1.0]),
            )
        )
        y += rng.choice([0, 19, 25])
    return bl


def _gen_uzun_zincir(rng: random.Random) -> list[TextBlock]:
    """UZUNLUK-tek sinirlarin ard arda dogdugu, 4+ segmentlik monolog."""
    bl = [_blk(f"{rng.choice(_AD)}: " + "A" * 150, 0, 0)]
    for k in range(1, rng.randint(3, 6)):
        bl.append(_blk(chr(66 + k) * 150, 0, 20 * k, h=18))
    return bl


_URETICILER = (
    _gen_etiket_zinciri,
    _gen_hyphen_etiket,
    _gen_esit_yx,
    _gen_yozlasmis,
    _gen_uzun_zincir,
)
_TOHUMLAR = (31337, 987654, 20260911)


def _dusman_derlem() -> list[list[TextBlock]]:
    """Her girdinin KARISTIRILMIS bir kopyasi da eklenir (K3: girdi listesi
    okuma sirasinda OLMAK ZORUNDA DEGIL)."""
    out: list[list[TextBlock]] = []
    for tohum in _TOHUMLAR:
        rng = random.Random(tohum)
        kar = random.Random(tohum ^ 0x5EED)
        for _ in range(60):
            for gen in _URETICILER:
                bl = gen(rng)
                out.append(bl)
                kopya = list(bl)
                kar.shuffle(kopya)
                out.append(kopya)
    return out


_DERLEM = _dusman_derlem()


def test_dusman_derlem_gercekten_dusman() -> None:
    """Derlemin KENDISI de bir iddiadir: yalniz-etiket blogu, esit `(y,x)`
    cifti, yozlasmis kutu ve karistirilmis sira GERCEKTEN uretiliyor mu?"""
    etiket = esit = yoz = 0
    for bl in _DERLEM:
        for b in bl:
            ad, kalan = _split_speaker_label(b.text)
            if ad is not None and not kalan.strip():
                etiket += 1
            if b.bbox.w <= 0 or b.bbox.h <= 0:
                yoz += 1
        anahtarlar = [(b.bbox.y, b.bbox.x) for b in bl]
        esit += len(anahtarlar) - len(set(anahtarlar))
    assert len(_DERLEM) >= 1500, len(_DERLEM)
    assert etiket > 500, f"yalniz-etiket blogu uretilmemis ({etiket})"
    assert esit > 500, f"esit (y,x) cifti uretilmemis ({esit})"
    assert yoz > 200, f"yozlasmis kutu uretilmemis ({yoz})"


# ===========================================================================
# 1 · `_group` ve `_raw_query_pair`'in SINIR ALANI (mercek A/2)
# ===========================================================================


@pytest.mark.parametrize("preset", PRESETS)
def test_group_bos_liste_dort_on_ayarda_da_bos_doner(preset: OcrPreset) -> None:
    """`_group([], params)` -- `tester_C`'nin dogrudan cagri BICIMI dahil
    (iki KONUMSAL argüman, `blocks` HIC verilmeden). Dort varyantin
    dordu de `[]` dondurmeli, hicbiri `IndexError` YUKSELTMEMELI."""
    params = get_params(preset)
    assert _group([], params) == []
    assert _group([], params, blocks=()) == []
    assert _group([], params, apply_inheritance=False) == []
    assert _group([], params, blocks=[_blk("a", 0, 0)], apply_inheritance=False) == []


@pytest.mark.parametrize("preset", GRUPLAYAN)
def test_group_tek_ogeli_liste_blocks_ISTEMEZ(preset: OcrPreset) -> None:
    """TEK ogeli grup: dongu HIC donmez, sinir DOGMAZ, dolayisiyla
    `blocks` varsayilani (`()`) YETERLIDIR -- ve donen ogenin
    `source_blocks`'u AYNEN korunur (`_group` tek ogeye DOKUNMAZ)."""
    params = get_params(preset)
    it = _item("tek satir", (7,), speaker="Ada")
    for bayrak in (True, False):
        (cikan,) = _group([it], params, apply_inheritance=bayrak)
        assert cikan is it
        assert cikan.source_blocks == (7,)


@pytest.mark.parametrize("bayrak", (True, False))
def test_group_uzunluk_tek_sinirda_blocks_yoksa_GURULTULU_kirilir(bayrak: bool) -> None:
    """`_group` docstring'i: "varsayilan YALNIZCA `items` bosken ya da
    UZUNLUK-TEK sinir DOGMAYAN dogrudan cagrilar icindir. Aksi halde
    `IndexError` yukselir -- BILINCLIDIR: sessiz yanlis yerine gurultulu
    hata." Iddia OLCULUR.

    IKINCI (belgelenmemis) yon de burada sabitlenir: `apply_inheritance=
    False` bu patlamayi ENGELLEMEZ -- miras sorgusu BOLUMLEME dongusunun
    icinde (`pure_length_boundaries.append(...)`) kosar ve bayrak yalniz
    GORUNUM gecisini kapatir. Bu, K23'un "bayrak bolumleme gecisinde HIC
    OKUNMAZ" degismezinin DOGRUDAN sonucudur."""
    params = get_params(OcrPreset.DIALOGUE)
    a = _item("X" * 150, (0,), y=0, speaker="Ada")
    b = _item("Y" * 150, (1,), y=20)
    with pytest.raises(IndexError):
        _group([a, b], params, apply_inheritance=bayrak)


def test_group_uzunluk_DISI_sinirda_blocks_gerekmez() -> None:
    """Ayni cagri, sinirin sebebi `"length"` DEGILSE (burada `"gap"`)
    patlamaz: `and` kisa devre yapar, `_raw_query_pair` HIC cagrilmaz.
    Bu, ustteki testin "her sinirda patlar" diye YANLIS okunmasini
    engeller -- patlama GECIKMELIDIR ve YALNIZ `reason == "length" and
    nxt.speaker is None` sinirinda dogar."""
    params = get_params(OcrPreset.DIALOGUE)
    a = _item("kisa", (0,), y=0, speaker="Ada")
    b = _item("kisa", (1,), y=500)  # devasa dikey bosluk -> "gap"
    cikan = _group([a, b], params)
    assert [it.source_blocks for it in cikan] == [(0,), (1,)]
    assert [it.speaker for it in cikan] == ["Ada", None]


def test_raw_query_pair_bos_source_blocks_IndexError() -> None:
    """`source_blocks == ()` -- urun boru hattinda DOGMAZ (her `_Item` en
    az bir indeksle kurulur, birlesimler indeks KAYBETMEZ) ama fonksiyon
    imzasi bunu KABUL EDER. Kabul edilen bu girdide de sessiz yanlis
    degil, `IndexError` beklenir."""
    b = [_blk("a", 0, 0)]
    bos = _item("x", ())
    with pytest.raises(IndexError):
        _raw_query_pair(bos, bos, b)


def test_raw_query_pair_blocks_bos_IndexError() -> None:
    b: Sequence[TextBlock] = ()
    it = _item("x", (0,))
    with pytest.raises(IndexError):
        _raw_query_pair(it, it, b)


def test_raw_query_pair_indeks_ARALIK_DISI_IndexError() -> None:
    """Suzulmus/sikistirilmis bir `blocks` gecirmenin (M9 sinifi) EN IYI
    halde gorunen yuzu: indeks aralik disina duserse gurultulu kirilir.
    (EN KOTU hali -- liste yeterince UZUN ama YANLIS -- sessizdir; onu
    olcu 5'in AST yarisi ve olcu 6 yakalar, bu test DEGIL.)"""
    b = [_blk("a", 0, 0), _blk("b", 0, 20)]
    it = _item("x", (5,))
    with pytest.raises(IndexError):
        _raw_query_pair(it, it, b)


def test_raw_query_pair_TEK_elemanli_source_blocks_ikameyi_GERCEKTEN_yapar() -> None:
    """Tek elemanli `source_blocks` "ikame gereksiz" DEMEK DEGILDIR: oge
    adim 3'ten gecmemis olsa bile `_Item.bbox` ile ozgun blogun `bbox`'i
    AYRISABILIR (adim 3 birlesmeyen ogeyi de yeniden kurar). Fonksiyon
    tek elemanda da HAM blogun kutusunu koymali."""
    blocks = [_blk("ham", 10, 100, w=30, h=7)]
    tail = _item("t", (0,), x=0, y=0, w=999, h=999, speaker="Ada")
    nxt = _item("n", (0,), x=5, y=5, w=888, h=888)
    sol, sag = _raw_query_pair(tail, nxt, blocks)
    assert sol.bbox == blocks[0].bbox
    assert sag.bbox == blocks[0].bbox
    assert sol.bbox != tail.bbox and sag.bbox != nxt.bbox


def test_raw_query_pair_YALNIZ_bbox_degistirir_uc_alan_AYNEN_korunur() -> None:
    """K28'in olcu ONKOSULU (sef_karari-tur6.md, V2): ikame
    `dataclasses.replace` ile yapilir; `speaker`, `text` VE
    `source_blocks` AYNEN korunur. Dusman derlemin URETTIGI her sorgu
    cifti uzerinde ve ayrica sentetik uc durumlarda olculur."""
    kontrol = 0
    for blocks in _DERLEM[:400]:
        for preset in GRUPLAYAN:
            params = get_params(preset)
            try:
                items = _adim1_4(blocks, params)
            except ValueError:
                continue
            for i in range(len(items) - 1):
                tail, nxt = items[i], items[i + 1]
                sol, sag = _raw_query_pair(tail, nxt, blocks)
                kontrol += 1
                assert (sol.text, sol.speaker, sol.source_blocks) == (
                    tail.text,
                    tail.speaker,
                    tail.source_blocks,
                )
                assert (sag.text, sag.speaker, sag.source_blocks) == (
                    nxt.text,
                    nxt.speaker,
                    nxt.source_blocks,
                )
    assert kontrol > 500, f"olcum totoloji: {kontrol} cift"


def test_raw_query_pair_UCUNCU_anahtar_source_blocks_SIRASINDAN_bagimsiz_kilar() -> None:
    """Docstring: ucuncu bilesen (girdi indeksi) "bugunku kodda
    davranissal bir NO-OP'tur (`source_blocks` K8 geregi ARTAN ve
    `sorted` KARARLIDIR)" -- yani iddia KOSULLUDUR ve kosulu K8'dir.
    Bu test kosulun DISINDA olcer: ayni `(y, x)` tasiyan iki blok ve
    TERS SIRALI bir `source_blocks` ile.

      * ucuncu anahtarLA  -> sonuc tuple SIRASINDAN bagimsiz;
      * ucuncu anahtarSIZ (kararli ikili anahtar, tuple sirasina duser)
        -> ayni girdide FARKLI blok secilir.

    Yani ucuncu bilesen K8 ALTINDA no-op, K8 DISINDA belirleyicidir --
    docstring'in kosullu ifadesi DOGRUDUR ve bu, fonksiyonu dogrudan
    cagiran bir sonraki ajan icin ONEMLIDIR."""
    blocks = [_blk("a", 0, 0, w=10, h=10), _blk("b", 0, 0, w=500, h=500)]
    ters = _item("t", (1, 0), speaker="Ada")
    duz = _item("t", (0, 1), speaker="Ada")
    assert _raw_query_pair(ters, ters, blocks)[0].bbox == blocks[1].bbox
    assert _raw_query_pair(duz, duz, blocks)[0].bbox == blocks[1].bbox

    def ikili_anahtar(sb: tuple[int, ...]) -> int:
        return sorted(sb, key=lambda i: (blocks[i].bbox.y, blocks[i].bbox.x))[-1]

    assert ikili_anahtar((1, 0)) == 0 and ikili_anahtar((0, 1)) == 1, (
        "sonda dissiz: ikili anahtar bu fixture'da da ayni sonucu veriyor"
    )


# ===========================================================================
# 2 · OKUMA SIRASI -- docstring "adim 1'in siralamasiyla AYNI" diyor
# ===========================================================================


def _adim1_4(blocks: Sequence[TextBlock], params: NormalizerParams) -> list[_Item]:
    """`_normalize_impl`'in adim 1-4'u -- BU DOSYANIN kendi turetimi
    (kitin `adim1_4`'u KULLANILMAZ; PROTOKOL S4.6/8). Yardimcilar MODUL
    ICE AKTARIMIYLA baglanir, yani bu turetim urunun `_group` oncesi
    listesinden BAGIMSIZ kalir -- BAGIMSIZLIGIN bedeli SESSIZ
    BAYATLAMADIR (`:401`'in tur 5'te dustugu tuzak), bu yuzden
    `test_yerel_turetim_urunun_group_girdisiyle_ESIT` iki tarafi
    makineyle esitler."""
    ordered = sorted(enumerate(blocks), key=lambda p: (p[1].bbox.y, p[1].bbox.x))
    items = [
        _Item(text=b.text, bbox=b.bbox, speaker=None, source_blocks=(i,))
        for i, b in ordered
        if b.confidence >= params.confidence_threshold
    ]
    items = [it for it in items if not _is_noise(it.text)]
    items = [replace(it, text=_collapse_intraline(it.text)) for it in items]
    return _extract_speakers(_merge_hyphenated(items))


def _urun_group_girdisi(blocks: Sequence[TextBlock], preset: OcrPreset) -> list[_Item]:
    """`normalize` kosarken `_group`'a GERCEKTEN giren oge listesi.

    Adim 1-4'un URUNDEKI ciktisidir -- yeniden uygulanmis degil, urunun
    kendisinden alinmistir. (`menu` icin `_group` HIC cagrilmaz, K27:
    bu yardimci yalniz gruplayan uc on ayar icin anlamlidir.)"""
    yakalanan: list[list[_Item]] = []
    orij = normalizer_modulu._group

    def kanca(
        items: list[_Item],
        params: NormalizerParams,
        *,
        blocks: Sequence[TextBlock] = (),
        apply_inheritance: bool = True,
    ) -> list[_Item]:
        yakalanan.append(list(items))
        return orij(items, params, blocks=blocks, apply_inheritance=apply_inheritance)

    normalizer_modulu._group = kanca  # type: ignore[assignment]
    try:
        normalize(blocks, preset)
    finally:
        normalizer_modulu._group = orij  # type: ignore[assignment]
    return yakalanan[0] if yakalanan else []


def test_yerel_turetim_urunun_group_girdisiyle_ESIT() -> None:
    """BAYATLAMA KAPISI: bu dosyanin bagimsiz `_adim1_4` turetimi ile
    urunun `_group`'a GERCEKTEN gecirdigi oge listesi BIREBIR ayni
    olmali. Ayrismalari, asagidaki yapisal testlerin urunle iliskisini
    SESSIZCE koparirdi (tur 5'te `:401` tam olarak boyle bayatladi)."""
    kontrol = ayrisma = 0
    ilk = ""
    for blocks in _DERLEM[:500]:
        for preset in GRUPLAYAN:
            params = get_params(preset)
            try:
                yerel = _adim1_4(blocks, params)
                urun = _urun_group_girdisi(blocks, preset)
            except ValueError:
                continue
            kontrol += 1
            if yerel != urun:
                ayrisma += 1
                if not ilk:
                    ilk = f"yerel={[it.source_blocks for it in yerel]} urun={[it.source_blocks for it in urun]}"
    assert kontrol > 1000, f"olcum totoloji: {kontrol} karsilastirma"
    assert ayrisma == 0, f"{kontrol} karsilastirmanin {ayrisma} tanesi ayrisiyor: {ilk}"


def test_okuma_sirasi_adim1_siralamasinin_ALTKUMESINE_esit() -> None:
    """`_raw_query_pair` docstring'i: "OKUMA SIRASI = `(bbox.y, bbox.x,
    girdi indeksi)` ARTAN -- adim 1'de kullanilan KARARLI
    `sorted(enumerate(blocks), key=(y, x))` cagrisiyla AYNI siradir."

    Iddia iki sorted cagrisi ARASINDA bir denklik ONERIR ve KOSULSUZ
    yazilmistir. Burada dusman derlemin HER girdisinde, rastgele
    ALTKUMELER uzerinde olculur. Sondanin disleri: adim 1 sirasinin
    INDEKS sirasindan ayristigi altkumeler AYRICA sayilir -- sifirsa
    denklik totolojidir."""
    ihlal = kontrol = ayirt_edici = 0
    rng = random.Random(4242)
    for blocks in _DERLEM:
        if not blocks:
            continue
        adim1 = [i for i, _ in sorted(enumerate(blocks), key=lambda p: (p[1].bbox.y, p[1].bbox.x))]
        yer = {b: k for k, b in enumerate(adim1)}
        for _ in range(3):
            k = rng.randint(1, min(6, len(blocks)))
            alt = tuple(sorted(rng.sample(range(len(blocks)), k)))
            kontrol += 1
            if list(alt) != sorted(alt, key=lambda i: yer[i]):
                ayirt_edici += 1
            if okuma_sirasi(blocks, alt) != sorted(alt, key=lambda i: yer[i]):
                ihlal += 1
    assert kontrol > 3000, kontrol
    assert ayirt_edici > 300, (
        f"indeks sirasi ile adim 1 sirasi HIC ayrismiyor ({ayirt_edici}) -- denklik totoloji"
    )
    assert ihlal == 0, f"{kontrol} altkumenin {ihlal} tanesinde adim 1 sirasindan ayrisiyor"


# ===========================================================================
# 3 · `source_blocks` GARANTI ALANI -- segment duzeyi (K8, mercek A/2)
# ===========================================================================


def test_k8_source_blocks_dusman_derlemde_HER_durumda_tanimli() -> None:
    """K8'in modul docstring'indeki KOSULSUZ iddialari, dusman derlemin
    tamaminda ve DORT on ayarda birden:

      * BOS DEGIL,
      * KESIN ARTAN (dolayisiyla tekrarsiz),
      * hepsi ozgun `blocks` dizisinin GECERLI indeksleri,
      * iki farkli segmentin kumeleri AYRIK ("HER ZAMAN AYRIKTIR").
    """
    seg = bos = artan = aralik = ayrik = 0
    for blocks in _DERLEM:
        for preset in PRESETS:
            try:
                out = normalize(blocks, preset)
            except ValueError:
                continue
            gorulen: set[int] = set()
            for s in out:
                seg += 1
                sb = s.source_blocks
                if not sb:
                    bos += 1
                if list(sb) != sorted(set(sb)):
                    artan += 1
                if any(not 0 <= i < len(blocks) for i in sb):
                    aralik += 1
                if gorulen & set(sb):
                    ayrik += 1
                gorulen |= set(sb)
    assert seg > 5000, f"olcum totoloji: {seg} segment"
    assert (bos, artan, aralik, ayrik) == (0, 0, 0, 0), (
        f"K8 ihlali -- bos={bos} artan={artan} aralik={aralik} ayriklik={ayrik}"
    )


def test_normalize_BELGELENEN_disinda_istisna_atmiyor() -> None:
    """`normalize` docstring'inin `Raises:` bolumu YALNIZ `ValueError`
    (K7 + K10) sayar; modul docstring'i de yozlasmis girdiler icin
    "hicbiri cokmez" der. K28 kodun icine bir `IndexError` YOLU acti
    (`blocks` yetersizse) -- bu yol GENEL API'den ERISILEBILIR MI?

    Dusman derlemin tamami x dort on ayar: `ValueError` DISINDA hicbir
    istisna gorulmemeli. Ozellikle `IndexError` gorulurse `normalize`'in
    `Raises:` sozlesmesi K28 ile SESSIZCE genislemis demektir."""
    beklenmeyen: dict[str, int] = {}
    kosum = 0
    for blocks in _DERLEM:
        for preset in PRESETS:
            kosum += 1
            try:
                normalize(blocks, preset)
            except ValueError:
                continue
            except Exception as exc:  # noqa: BLE001 -- olculen sey tam olarak bu
                beklenmeyen[type(exc).__name__] = beklenmeyen.get(type(exc).__name__, 0) + 1
    assert kosum > 6000, kosum
    assert beklenmeyen == {}, f"`normalize` belgelenmemis istisna atiyor: {beklenmeyen}"


# ===========================================================================
# 4 · K28'in KARAR METNI ("kapanan GRUP") ile UYGULAMASI (`tail` OGESI)
#     ayni blogu mu seciyor? -- baska hicbir yerde olculmuyor
# ===========================================================================


def test_k28_karar_metni_GRUP_ile_uygulama_TAIL_ayni_ham_blogu_seciyor() -> None:
    """K28 (karar metni): *"sol taraf `bbox` = kapanan grubun kaynak
    bloklari arasinda okuma sirasinda SON gelen blogun `bbox`'i"*.
    Uygulama ise `tail` OGESININ kaynak bloklarindan secer -- KAPANAN
    GRUBUN (`current`, birden cok oge icerebilir) degil.

    Ikisi ancak adim 1-4'un ogeleri okuma sirasinda BITISIK kosulara
    bolmesi sayesinde ayni seydir. Olculur: kitin kancasi
    (`sorgu_kaydi`) hem BOLUMLEME (`ignore_length=False`, sol taraf =
    `current` = KAPANAN GRUP) hem MIRAS (`ignore_length=True`, sol taraf
    = `tail`) sorgularini kaydeder; bir miras sorgusunun HEMEN ONCESINDE
    gelen bolumleme sorgusu, ayni sinirin GRUP tarafidir.

    Sondanin disleri: `tail`in grubun TAMAMINDAN KUCUK oldugu (cok ogeli
    grup) sinirlar ayrica sayilir -- sifirsa denklik totolojidir."""
    sinir = coklu_grup = ayrisma = 0
    ilk_fark = ""
    for blocks in _DERLEM:
        for preset in GRUPLAYAN:
            with sorgu_kaydi() as kayit:
                try:
                    normalize(blocks, preset)
                except ValueError:
                    continue
            for i, sg in enumerate(kayit):
                if not sg.miras:
                    continue
                assert i > 0 and not kayit[i - 1].miras, (
                    "kanca beklenen sirayi gormedi -- miras sorgusundan HEMEN ONCE "
                    "ayni sinirin bolumleme sorgusu gelmeli"
                )
                grup_sb = kayit[i - 1].sol_sb  # kapanan GRUP (`current`)
                tail_sb = sg.sol_sb  # `tail` OGESI
                sinir += 1
                if len(grup_sb) > len(tail_sb):
                    coklu_grup += 1
                grup_son = okuma_sirasi(blocks, grup_sb)[-1]
                tail_son = okuma_sirasi(blocks, tail_sb)[-1]
                if grup_son != tail_son:
                    ayrisma += 1
                    if not ilk_fark:
                        ilk_fark = f"grup_sb={grup_sb} -> {grup_son} | tail_sb={tail_sb} -> {tail_son}"
    assert sinir > 300, f"olcum totoloji: {sinir} miras sorgusu"
    assert coklu_grup > 50, (
        f"cok ogeli grup uretilmemis ({coklu_grup}) -- `tail` ile GRUP ayni sey oldugu "
        "surece denklik totolojidir"
    )
    assert ayrisma == 0, (
        f"K28'in KARAR METNI ile UYGULAMASI {sinir} sinirin {ayrisma} tanesinde farkli "
        f"blok seciyor: {ilk_fark}"
    )


def test_ogeler_okuma_sirasinda_BITISIK_kosulara_boluyor() -> None:
    """Ustteki denkligi MUMKUN KILAN yapisal ozellik, ayri ve dogrudan:
    adim 1-4'un urettigi oge listesi, hayatta kalan bloklari okuma
    sirasinda BITISIK ve ARTAN kosulara boler.

      * BITISIKLIK: bir ogenin `source_blocks`'u, hayatta kalan
        bloklarin okuma sirasinda ARDISIK bir dilimdir (adim 3'un
        hyphen zinciri ve adim 4'un etiket TASIMASI bu ozelligi
        BOZMAZ);
      * SIRA: kosular birbirini takip eder, ic ice GECMEZ.

    Bu ozellik bozulursa `tail`in son ham blogu grubun son ham blogu
    OLMAYABILIR -- yani K28 SESSIZCE karar metninden ayrisir. Ustteki
    davranissal test bunu derlem BAGIMLI olarak yakalar; bu test
    YAPIYI dogrudan sabitler.

    Olculen sey URUNUN kendi oge listesidir (`_urun_group_girdisi`),
    bu dosyanin yeniden uygulamasi DEGIL -- aksi halde adim 1-4'u bozan
    bir degisiklik bu testi hic gormezdi."""
    oge = cok_bloklu = bitisiklik = sira = 0
    for blocks in _DERLEM:
        for preset in GRUPLAYAN:
            try:
                items = _urun_group_girdisi(blocks, preset)
            except ValueError:
                continue
            if not items:
                continue
            kalan = okuma_sirasi(blocks, sorted({i for it in items for i in it.source_blocks}))
            yer = {b: k for k, b in enumerate(kalan)}
            onceki_son = -1
            for it in items:
                oge += 1
                if len(it.source_blocks) > 1:
                    cok_bloklu += 1
                konum = sorted(yer[b] for b in it.source_blocks)
                if konum != list(range(konum[0], konum[0] + len(konum))):
                    bitisiklik += 1
                if konum[0] <= onceki_son:
                    sira += 1
                onceki_son = konum[-1]
    assert oge > 5000, f"olcum totoloji: {oge} oge"
    assert cok_bloklu > 500, f"cok bloklu oge uretilmemis ({cok_bloklu})"
    assert (bitisiklik, sira) == (0, 0), (
        f"oge kosulari bitisik/artan degil -- bitisiklik ihlali={bitisiklik} sira ihlali={sira}"
    )


def test_miras_sorgusunun_SOL_blogu_asla_yalniz_etiket_blogu_degil() -> None:
    """Sefin K28 gerekcesinde adlandirdigi EK YUZEY: *"sirasiz girdide
    `[-1]` segment uretmeyen bir ETIKET blogunu bile gosterebilir."*

    K9'un `pending_blocks` yolu, yalniz-etiket bir blogun indeksini bir
    SONRAKI ogenin `source_blocks`'una tasir. O oge miras sorgusunun SOL
    tarafi olursa, secilen ham blok ETIKET blogu OLABILIR mi? (Olursa
    sorgu gercek satir-arasi boslugu degil, ETIKETE olan boslugu olcer.)

    Olculur: dusman derlem 500'den fazla yalniz-etiket blogu uretiyor
    (bkz. `test_dusman_derlem_gercekten_dusman`) ve HICBIR miras
    sorgusunun sol/sag blogu yalniz-etiket CIKMIYOR.

    Iki asamali olculur ki sonda urunun GERCEKTEN kullandigi kutuyu
    gorsun: (1) K28'in tanimladigi blok yalniz-etiket OLMAMALI,
    (2) urunun sorguya SOKTUGU `bbox` o blogun kutusu OLMALI -- ikinci
    assert olmasaydi sol tarafi okuma-sirasi ILK bloga ceviren bir
    mutant bu testten gecerdi."""
    sinir = etiketli = kutu_ayristi = 0
    for blocks in _DERLEM:
        for preset in GRUPLAYAN:
            with sorgu_kaydi() as kayit:
                try:
                    normalize(blocks, preset)
                except ValueError:
                    continue
            for sg in kayit:
                if not sg.miras:
                    continue
                sinir += 1
                for sb, uc, olculen in (
                    (sg.sol_sb, -1, sg.sol_bbox),
                    (sg.sag_sb, 0, sg.sag_bbox),
                ):
                    ham = blocks[okuma_sirasi(blocks, sb)[uc]]
                    ad, kalan = _split_speaker_label(ham.text)
                    if ad is not None and not kalan.strip():
                        etiketli += 1
                    if olculen != ham.bbox:
                        kutu_ayristi += 1
    assert sinir > 300, f"olcum totoloji: {sinir} miras sorgusu"
    assert etiketli == 0, (
        f"{sinir} miras sorgusunun {etiketli} tanesinde K28'in tanimladigi ham blok "
        "YALNIZ-ETIKET blogu -- sorgu gercek satir-arasi boslugu olcmuyor"
    )
    assert kutu_ayristi == 0, (
        f"{sinir} miras sorgusunun {kutu_ayristi} tanesinde urunun kullandigi `bbox` "
        "K28'in tanimladigi ham blogun kutusu DEGIL"
    )


# ===========================================================================
# 5 · ZINCIRLEME MIRAS -- `tests/` altinda PINLI mi (mercek A/3)
# ===========================================================================


def test_zincirleme_miras_implementer_testinde_PINLI() -> None:
    """Sefin tur 6 listesinde: *"Zincirleme miras `tests/` altinda
    pinlenir -- A gozlem 2"*. Sadece davranisin dogru olmasi YETMEZ,
    URUN test dosyasinda bir PIN olmalidir (yoksa bir sonraki tur onu
    sessizce kaybedebilir).

    AST ile aranir: `tests/unit/ocr/test_normalizer.py` icinde,
    `normalize` cagirip `speaker` listesini UC KEZ ayni ada esitleyen
    bir test fonksiyonu."""
    kaynak = _IMPLEMENTER_TESTI.read_text(encoding="utf-8")
    agac = ast.parse(kaynak)
    bulunan: list[str] = []
    for dugum in ast.walk(agac):
        if not isinstance(dugum, ast.FunctionDef) or not dugum.name.startswith("test_"):
            continue
        govde = ast.unparse(dugum)
        if "normalize(" not in govde:
            continue
        for ad in ("'Ada', 'Ada', 'Ada'", '"Ada", "Ada", "Ada"'):
            if ad in govde and ".speaker" in govde:
                bulunan.append(dugum.name)
                break
    assert bulunan, (
        "zincirleme miras `tests/unit/ocr/test_normalizer.py` altinda PINLI DEGIL -- "
        "`normalize` uzerinden `['Ada','Ada','Ada']` bekleyen bir test bulunamadi"
    )


def test_zincirleme_miras_UC_segmentle_sinirli_degil() -> None:
    """Pinin KAPSAMI: implementer'in testi UC segment olcuyor. Zincirin
    UZUNLUGA bagli bir tavani var mi? Kendi geometrimle BES segment:
    goruntu gecisi SOLDAN SAGA islendigi icin her segment bir oncekinden
    devralmali."""
    blocks = [_blk("Ada: " + "A" * 150, 0, 0)]
    blocks += [_blk(ch * 150, 0, 20 * k) for k, ch in enumerate("BCDE", start=1)]
    out = normalize(blocks, OcrPreset.DIALOGUE)
    assert [s.source_blocks for s in out] == [(0,), (1,), (2,), (3,), (4,)]
    assert [s.speaker for s in out] == ["Ada"] * 5


def test_zincirleme_miras_GERCEK_kopusta_kesilir_ve_bir_daha_baslamaz() -> None:
    """Ustteki testin disleri: zincir "her segmente Ada yaz" DEGILDIR.
    Ucuncu blogun onune GERCEK bir geometrik bosluk konur -- miras orada
    KESILIR ve sonraki segmentler `None` KALIR (K19/K21: sinir yalniz-
    uzunluk sinirI DEGILSE miras uygulanmaz)."""
    blocks = [
        _blk("Ada: " + "A" * 150, 0, 0),
        _blk("B" * 150, 0, 20),
        _blk("C" * 150, 0, 400),  # gercek kopus
        _blk("D" * 150, 0, 420),
    ]
    out = normalize(blocks, OcrPreset.DIALOGUE)
    assert [s.source_blocks for s in out] == [(0,), (1,), (2,), (3,)]
    assert [s.speaker for s in out] == ["Ada", "Ada", None, None]


# ===========================================================================
# 6 · DOCSTRING GARANTI ALANI -- mercegin ASIL sorusu (mercek A/4)
# ===========================================================================


def _miras_sorgusu_bicimi(kaynak: str) -> list[str]:
    """`_group`'un GERCEK miras-sorgusu cagri bicimi (AST)."""
    agac = ast.parse(kaynak)
    (fn,) = [
        d for d in ast.walk(agac) if isinstance(d, ast.FunctionDef) and d.name == "_group"
    ]
    return [
        ", ".join(ast.unparse(a) for a in d.args)
        for d in ast.walk(fn)
        if isinstance(d, ast.Call)
        and isinstance(d.func, ast.Name)
        and d.func.id == "_group_rejection_reason"
        and any(k.arg == "ignore_length" for k in d.keywords)
    ]


@pytest.mark.xfail(
    strict=True,
    reason=(
        "BAYAT DOKUMANTASYON (tester_A, tur 6): modul docstring'inin '### K24' "
        "bolumu (normalizer.py:832-836) K28 ONCESI cagri bicimini KOSULSUZ ve "
        "SIMDIKI ZAMANDA anlatiyor; K28'e ileri referans YOK. Davranis DOGRU, "
        "iddia BAYAT -- bkz. verdict-A.md (tur 6) notlar."
    ),
)
def test_modul_docstringinin_K24_bolumu_bugunku_cagri_bicimini_anlatiyor() -> None:
    """MERCEGIN ASIL SORUSU, DOKUMANTASYONA UYGULANMIS: "docstring ne soz
    veriyor ve bu soz TUTUYOR mu?"

    `normalizer.py` modul docstring'i, "### K24 -- K21'in TEK gecerli
    ifadesi" bolumunde (satir 832-836) su iddiayi tasir:

        K21'in `ignore_length=True` IKINCI cagrisi ARTIK
        `_group_rejection_reason(current, nxt, ...)` DEGIL,
        `_group_rejection_reason(tail, nxt, ...)` KULLANIR -- yani SOL
        TARAF DAIMA grubun okuma-sirasindaki EN SON ... HAM ogesidir

    Kod ARTIK bunu yapmiyor (K28, tur 6): cagri
    `_group_rejection_reason(*_raw_query_pair(tail, nxt, blocks), params,
    ignore_length=True)`. Ustelik "`tail` HAM ogedir" cumlesi, bulgu
    R5-1'in tam olarak CURUTTUGU cumledir (`tail` adim 3'ten BIRLESIK
    gelebilir). Bolum, K28'e hicbir ileri referans TASIMIYOR ve
    SIMDIKI ZAMAN kullaniyor -- modulun baska yerlerinde (ör. "## K10"
    ve "## K16") bayatlayan iddialar "TUR 1'DE ... diyordu; ... duzeltir"
    kalibiyla ACIKCA isaretlenmis.

    Bu test, satirlar duzeltildiginde XPASS ile KENDINI DUYURUR."""
    kaynak = _URUN.read_text(encoding="utf-8")
    kod_bicimi = _miras_sorgusu_bicimi(kaynak)
    assert kod_bicimi == ["*_raw_query_pair(tail, nxt, blocks), params"], kod_bicimi
    docstring = ast.get_docstring(ast.parse(kaynak)) or ""
    k24 = docstring.split("### K24")[1].split("## K12")[0]
    tek_satir = " ".join(k24.split())
    assert "_group_rejection_reason(tail, nxt, ...)` KULLANIR" not in tek_satir, (
        "modul docstring'i '### K24' bolumu K28 ONCESI cagri bicimini hala "
        "KOSULSUZ anlatiyor (normalizer.py:832-836)"
    )
