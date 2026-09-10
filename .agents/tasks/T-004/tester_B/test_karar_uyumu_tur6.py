"""TESTER-B (KARAR UYUMU merceği) -- T-004 TUR 6 -- K28-K32 saldiri seti.

`test_karar_uyumu.py` (K1-K18), `test_karar_uyumu_tur3.py` (K19/K20) ve
`test_karar_uyumu_tur5.py` (K23-K27) dosyalarina EK. Bu dosya
`sef_karari-tur6.md` (surum 8) kararinin BES maddesini (K28 tek kod
degisikligi, K29-K32 belgeleme) koda ve testlere karsi TEK TEK dogrular.

Mercegin asil sorusu (env.md TUR 6 / MERCEK B/2-3 + gorev tanimi):
**"Kararin HER SATIRI kodda ve testlerde gercekten var mi -- uydurulmus
ya da eksik davranis var mi?"** Bu yuzden burada uc tur denetim var:

  YAPISAL  -- AST: imzalar, `_raw_query_pair`in bicimi, `_group`in tek
              `replace`i, `blocks=blocks` iletimi, `source_blocks[-1]`
              yasagi.
  TARIHSEL -- `git show` ile K28 ONCESI surumle karsilastirma: kararin
              "DEGISMEZ/DEGISMEDI" dedigi HER parca (`_Item`, `normalize`,
              `_should_group`, `_group_rejection_reason` ve adim 1-4'un
              dort yardimcisi) gercekten degismemis mi. Bu, "docstring
              degisti ama govde de degisti" sinifini yakalar.
  DAVRANIS -- K30'un IKI yolu, K31'in (a)/(b)/iki-farkli-ad durumu,
              K32'nin NFC/NFD ayrimi KENDI girdilerimle yeniden uretilir
              (urun testinin fixture'i kopyalanmaz).

Ayrica bu turun IKI OLCUM BULGUSU testle sabitlenir (bkz. `verdict-B.md`):
kararin "M4 -> olcu 3b kirilmali" ve "M5 -> olcu 5 kirilmali" cumleleri
FIXTURE'lar yuzunden TUTMUYOR; testler fixture'larin o ozelligini pinler,
boylece fixture guclendirilirse haber verilir.

Sabit tohum / deterministik girdi -- rastgelelik yok.
"""
from __future__ import annotations

import ast
import inspect
import random
import re
import subprocess
import textwrap
import unicodedata
from dataclasses import fields, replace
from typing import Any

import pytest

import src.ocr.normalizer as normalizer_mod
from olcu_kiti import okuma_sirasi, olcu3b_fixture, olcu5_fixture, sorgu_kaydi
from src.contracts.models import OcrPreset, Rect, TextBlock
from src.ocr.normalizer import (
    _group,
    _group_rejection_reason,
    _Item,
    _normalize_impl,
    _raw_query_pair,
    _should_group,
    _split_speaker_label,
    normalize,
)
from src.ocr.presets import get_params

REPO_KOK = __import__("pathlib").Path(normalizer_mod.__file__).resolve().parents[2]
URUN_TESTI = REPO_KOK / "tests" / "unit" / "ocr" / "test_normalizer.py"
K28_ONCESI = "74256d8"  # "T-004: olcu kiti surum 3; K28 implementer'a gidiyor"

ALL_PRESETS = (OcrPreset.DIALOGUE, OcrPreset.MENU, OcrPreset.TOOLTIP, OcrPreset.SUBTITLE)


def blk(text: str, x: int, y: int, *, w: int = 240, h: int = 18, confidence: float = 0.9) -> TextBlock:
    return TextBlock(text=text, bbox=Rect(x=x, y=y, w=w, h=h), confidence=confidence)


def _func_ast(func: Any) -> ast.FunctionDef:
    node = ast.parse(textwrap.dedent(inspect.getsource(func))).body[0]
    assert isinstance(node, ast.FunctionDef)
    return node


def _duz(metin: str) -> str:
    """Docstring'i tek satira indirger -- satir sarmasi eslesmeyi bozmasin."""
    return re.sub(r"\s+", " ", metin).strip()


# ===========================================================================
# 1. K28 -- DEGISMEZIN HER CUMLESI
# ===========================================================================


def test_r6_k28_raw_query_pair_modul_duzeyinde_ve_imzasi_kararda_yazildigi_gibi() -> None:
    """Karar: "Modul duzeyinde yardimci: `_raw_query_pair(tail: _Item, nxt:
    _Item, blocks: Sequence[TextBlock]) -> tuple[_Item, _Item]`". Ic ice
    tanimlanmis (`_group` icinde) bir yardimci karari KARSILAMAZ: kit ve
    tester onu ayri ayri cagirabilmelidir."""
    assert _raw_query_pair.__module__ == "src.ocr.normalizer"
    assert getattr(normalizer_mod, "_raw_query_pair", None) is _raw_query_pair
    imza = inspect.signature(_raw_query_pair)
    assert list(imza.parameters) == ["tail", "nxt", "blocks"], imza
    assert all(
        p.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD for p in imza.parameters.values()
    ), imza
    assert [p.annotation for p in imza.parameters.values()] == [
        "_Item",
        "_Item",
        "Sequence[TextBlock]",
    ], imza
    assert imza.return_annotation == "tuple[_Item, _Item]", imza
    # modul duzeyinde tanimli (ic ice DEGIL)
    agac = ast.parse(REPO_KOK.joinpath("src/ocr/normalizer.py").read_text(encoding="utf-8"))
    ust_duzey = [n.name for n in agac.body if isinstance(n, ast.FunctionDef)]
    assert "_raw_query_pair" in ust_duzey, ust_duzey


def test_r6_k28_okuma_sirasi_uclu_anahtar_GERCEKTEN_yazili() -> None:
    """Karar: "OKUMA SIRASI = `(bbox.y, bbox.x, girdi indeksi)` ARTAN".

    Ucuncu bilesen bugun DAVRANISSAL bir no-op'tur (`source_blocks` K8
    geregi artan, `sorted` kararli) -- yani "yazilmis mi" sorusu ancak
    K8'e BAGIMLI OLMAYAN bir girdiyle sorulabilir: `source_blocks`'u
    AZALAN veren bir `_Item` ile dogrudan cagirilir. Ikili anahtar
    kullanan bir uygulama girdi sirasini korur ve BASKA bir blok secer.

    (Kararin kendisi bu no-op'lugu K3/Z3 olcumuyle kabul ediyor; bu test
    "tanimi K8'e bagimli olmaktan cikarmak icin ACIKCA yazilir" cumlesinin
    gercekten uygulandiginin kanitidir.)

    KAPSAM SINIRI (kendi olcumum): bu test INDEKS SIRASI kullanan bir
    uygulamayi (M4) AYIRT EDEMEZ -- tum `(y, x)` esitken okuma sirasi
    ZATEN indeks sirasidir. M4'u `..._sol_okuma_sirasi_SON_..._fuzz` ve
    `..._source_blocks_indeksi_KULLANILMIYOR_ast` yakalar (olculdu: mutant
    agacinda ikisi de kiriliyor)."""
    # UCU DE ayni (y, x) -- ama `w` FARKLI, yoksa `bbox` esitligi TOTOLOJIK olurdu
    blocks = [blk("a", 0, 0, w=10), blk("b", 0, 0, w=20), blk("c", 0, 0, w=30)]
    assert len({(b.bbox.x, b.bbox.y, b.bbox.w, b.bbox.h) for b in blocks}) == 3
    tail = _Item(text="t", bbox=Rect(9, 9, 9, 9), speaker="Ada", source_blocks=(2, 0, 1))
    nxt = _Item(text="n", bbox=Rect(8, 8, 8, 8), speaker=None, source_blocks=(2, 0, 1))
    sol, sag = _raw_query_pair(tail, nxt, blocks)
    assert sol.bbox is blocks[2].bbox or sol.bbox == blocks[2].bbox, (
        "esitlikte GIRDI INDEKSI anahtari kullanilmiyor -- ikili anahtarla kararli "
        "sort girdi sirasini korur ve `blocks[1]` secilirdi"
    )
    assert sag.bbox == blocks[0].bbox
    # AST: anahtar uc bilesenli
    fn = _func_ast(normalizer_mod._raw_query_pair)
    lambdalar = [n for n in ast.walk(fn) if isinstance(n, ast.Lambda)]
    assert len(lambdalar) == 1, [ast.unparse(n) for n in lambdalar]
    assert ast.unparse(lambdalar[0].body) == "(blocks[i].bbox.y, blocks[i].bbox.x, i)", ast.unparse(
        lambdalar[0]
    )


def test_r6_k28_sol_okuma_sirasi_SON_sag_okuma_sirasi_ILK_fuzz() -> None:
    """DEGISMEZ, davranissal: sol = `tail.source_blocks` icinde okuma
    sirasinda SON, sag = `nxt.source_blocks` icinde okuma sirasinda ILK.

    Referans KENDI hesabimla kurulur (kitin `okuma_sirasi`'yla ayrica
    capraz kontrol edilir -- ikisi ayrismamali). 4000 rastgele cift,
    esit `(y, x)` cesitleri dahil."""
    rng = random.Random(606_28_001)
    esit_yx = 0
    for _ in range(4000):
        n = rng.randint(2, 9)
        # `w`ye `i` eklenir: her blogun `bbox`'i TEKIL olsun, yoksa esit `(y, x)`
        # ciftlerinde `bbox` karsilastirmasi TOTOLOJIK olur ve ucuncu anahtari
        # olcmez.
        blocks = [
            blk(
                f"b{i}",
                rng.choice([0, 0, 100, -50]),
                rng.choice([0, 10, 10, 20, 40]),
                w=rng.choice([8, 240]) + i,
                h=rng.choice([0, 5, 18]),
            )
            for i in range(n)
        ]
        assert len({(b.bbox.x, b.bbox.y, b.bbox.w, b.bbox.h) for b in blocks}) == n
        idxs = sorted(rng.sample(range(n), rng.randint(1, n)))
        jdxs = sorted(rng.sample(range(n), rng.randint(1, n)))
        koordlar = [(b.bbox.y, b.bbox.x) for b in blocks]
        if len(set(koordlar)) < len(koordlar):
            esit_yx += 1
        tail = _Item("t", Rect(7, 7, 7, 7), "Ada", tuple(idxs))
        nxt = _Item("n", Rect(6, 6, 6, 6), None, tuple(jdxs))

        benim = sorted(idxs, key=lambda i: (blocks[i].bbox.y, blocks[i].bbox.x, i))
        benim_sag = sorted(jdxs, key=lambda i: (blocks[i].bbox.y, blocks[i].bbox.x, i))
        assert benim == okuma_sirasi(blocks, idxs)  # kitle capraz kontrol

        sol, sag = _raw_query_pair(tail, nxt, blocks)
        assert sol.bbox == blocks[benim[-1]].bbox, (idxs, koordlar)
        assert sag.bbox == blocks[benim_sag[0]].bbox, (jdxs, koordlar)
    assert esit_yx > 200, f"derlemimde esit (y, x) cifti yeterince yok: {esit_yx}"


def test_r6_k28_source_blocks_indeksi_KULLANILMIYOR_ast() -> None:
    """Karar: "`source_blocks[-1]` / `[0]` KULLANILMAZ". Yapisal: fonksiyonun
    hicbir yerinde `<sey>.source_blocks` uzerinde SABIT indeksleme
    (`[-1]`, `[0]`) ve `max(...)`/`min(...)` kisayolu yok."""
    fn = _func_ast(normalizer_mod._raw_query_pair)
    for node in ast.walk(fn):
        if isinstance(node, ast.Subscript):
            hedef = ast.unparse(node.value)
            if hedef.endswith(".source_blocks"):
                raise AssertionError(f"`source_blocks` dogrudan indeksleniyor: {ast.unparse(node)}")
    for node in ast.walk(fn):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("max", "min"):
            arg = ast.unparse(node.args[0]) if node.args else ""
            assert not arg.endswith("source_blocks"), (
                f"okuma sirasi yerine INDEKS sirasi kisayolu: {ast.unparse(node)}"
            )
    # `reading_order(...)` uzerinde `[-1]` / `[0]` ise BEKLENENDIR
    kaynak = _duz(inspect.getsource(normalizer_mod._raw_query_pair))
    assert "reading_order(tail.source_blocks)[-1]" in kaynak
    assert "reading_order(nxt.source_blocks)[0]" in kaynak


def test_r6_k28_ikame_yalniz_bbox_a_dokunuyor_ast_ve_davranis() -> None:
    """Karar: "IKAME YALNIZ `bbox`'a dokunur: `dataclasses.replace` ile
    `speaker`, `text` VE `source_blocks` AYNEN KORUNUR." `source_blocks`
    korumasi urun icin OLU ama OLCUNUN ONKOSULU (V2) -- kit `tail`/`nxt`
    kimligini baska hicbir kanaldan geri kazanamaz."""
    fn = _func_ast(normalizer_mod._raw_query_pair)
    replaces = [
        n for n in ast.walk(fn)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "replace"
    ]
    assert len(replaces) == 2, [ast.unparse(n) for n in replaces]
    for r in replaces:
        assert {k.arg for k in r.keywords} == {"bbox"}, ast.unparse(r)

    blocks = [blk("a", 0, 0), blk("b", 0, 20), blk("c", 0, 40)]
    tail = _Item("metin-sol", Rect(1, 2, 3, 4), "Ada", (0, 1))
    nxt = _Item("metin-sag", Rect(5, 6, 7, 8), None, (2,))
    sol, sag = _raw_query_pair(tail, nxt, blocks)
    for once, sonra in ((tail, sol), (nxt, sag)):
        assert sonra.text == once.text
        assert sonra.speaker == once.speaker
        assert sonra.source_blocks == once.source_blocks, "V2 ONKOSULU: `source_blocks` yeniden yazilmis"
        assert type(sonra) is _Item
    assert sol.bbox == blocks[1].bbox and sag.bbox == blocks[2].bbox


def test_r6_k28_sorguya_giren_bbox_daima_bir_HAM_blogun_kutusu() -> None:
    """DEGISMEZ (davranissal, uctan uca): "HICBIR birlesik `_Item` `bbox`'i
    (adim 3'ten ya da adim 5'ten) bu sorguya GIRMEZ." Kendi derlemimde
    gozlenen HER miras sorgusunun IKI bbox'i da OZGUN listedeki bir blogun
    kutusuna BIREBIR esit olmali."""
    rng = random.Random(606_28_002)
    gozlenen = 0
    coklu_sag = 0
    for _ in range(600):
        blocks = _zincirli_girdi(rng)
        for preset in (OcrPreset.DIALOGUE, OcrPreset.TOOLTIP, OcrPreset.SUBTITLE):
            kutular = [b.bbox for b in blocks]
            with sorgu_kaydi() as kayit:
                normalize(blocks, preset)
            for sg in kayit:
                if not sg.miras:
                    continue
                gozlenen += 1
                if len(sg.sag_sb) > 1:
                    coklu_sag += 1
                assert sg.sol_bbox in kutular, (sg.sol_sb, sg.sol_bbox)
                assert sg.sag_bbox in kutular, (sg.sag_sb, sg.sag_bbox)
    assert gozlenen > 500, f"derlemim miras sorgusu uretmiyor: {gozlenen}"
    assert coklu_sag > 50, (
        f"derlemimde COK BLOKLU ADAY (sag taraf) yok ({coklu_sag}) -- sag taraf "
        "cumlesini olcemiyorum (bkz. olcu 5 fixture'inin ayni kusuru)"
    )


def test_r6_k28_kapsam_bolumleme_sorgusu_hala_BIRLESIK_kutu_kullaniyor() -> None:
    """Karar, KAPSAM cumlesi: "ANA birlestirme karari (bolumleme gecisi)
    K10/K11 uyarinca `current`'in BIRLESIK `bbox`'ini KULLANMAYA DEVAM
    EDER". Ham ikame o yola SIZMAMALI.

    Bagimsiz olcum (kitin `ham_ikame_sizmis`'i kullanilmadan): bolumleme
    sorgusunun sol `bbox`'i, o tarafin GEOMETRIYE KATKI VEREN tum
    bloklarini KAPSAMALI (yalniz-etiket bloklari K9'un `pending_blocks`
    yoluyla `source_blocks`'a girer ama bbox'a girmez -- muaf)."""
    rng = random.Random(606_28_003)
    denetlenen = 0
    for _ in range(400):
        blocks = _zincirli_girdi(rng)
        for preset in (OcrPreset.DIALOGUE, OcrPreset.SUBTITLE):
            with sorgu_kaydi() as kayit:
                normalize(blocks, preset)
            for sg in kayit:
                if sg.miras:
                    continue
                for sb, bbox in ((sg.sol_sb, sg.sol_bbox), (sg.sag_sb, sg.sag_bbox)):
                    katki = [
                        blocks[i].bbox
                        for i in sb
                        if not _yalniz_etiket(blocks[i].text)
                    ]
                    if len(katki) < 2:
                        continue
                    denetlenen += 1
                    assert bbox.x <= min(r.x for r in katki), (sb, bbox)
                    assert bbox.y <= min(r.y for r in katki), (sb, bbox)
                    assert bbox.right >= max(r.right for r in katki), (sb, bbox)
                    assert bbox.bottom >= max(r.bottom for r in katki), (sb, bbox)
    assert denetlenen > 200, f"cok bloklu bolumleme sorgusu gozlemedim: {denetlenen}"


def test_r6_k28_group_imzasi_kararda_yazildigi_gibi() -> None:
    """Karar: "`_group(items, params, *, blocks: Sequence[TextBlock] = (),
    apply_inheritance: bool = True)` -- `blocks` KEYWORD-ONLY ve
    VARSAYILANLI". Konumsal ya da varsayilansiz yazilirsa `tester_C`'nin
    `_group([], params)` dogrudan cagrisi kirilirdi (sef olctu: surum
    2'nin secenegi kor takimda 70 kirik)."""
    imza = inspect.signature(_group)
    assert list(imza.parameters) == ["items", "params", "blocks", "apply_inheritance"], imza
    p = imza.parameters
    assert p["items"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert p["params"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert p["blocks"].kind is inspect.Parameter.KEYWORD_ONLY
    assert p["apply_inheritance"].kind is inspect.Parameter.KEYWORD_ONLY
    assert p["blocks"].default == ()
    assert p["apply_inheritance"].default is True
    assert p["blocks"].annotation == "Sequence[TextBlock]"
    assert p["apply_inheritance"].annotation == "bool"
    assert imza.return_annotation == "list[_Item]"
    assert _group([], get_params(OcrPreset.DIALOGUE)) == []  # tester_C'nin cagrisi


def test_r6_k28_normalize_impl_OZGUN_listeyi_geciriyor_indeks_kaymasi_yok() -> None:
    """Karar: "`_normalize_impl` `_group`'u cagirirken `blocks=blocks`
    gecmek ZORUNDADIR ... suzulmus/sikistirilmis bir liste gecirmek INDEKS
    KAYMASINA yol acar."

    AST yarisi urun olcu 5'te var; buradaki yari DAVRANISSAL: girdinin
    BASINA esik-alti bir blok konur (K8 indeks uzayini kaydirmaz).
    Suzulmus liste geciren bir uygulama ya `IndexError` verir ya da
    YANLIS blogun geometrisiyle sorar; ikisi de burada gorunur."""
    govde = "Ada: " + "X" * 150
    temiz = [blk(govde, 0, 0), blk("Y" * 150, 0, 20), blk("Z" * 150, 0, 40)]
    kayik = [blk("gurultu", 0, -40, confidence=0.10), *temiz]

    a = normalize(temiz, OcrPreset.DIALOGUE)
    b = normalize(kayik, OcrPreset.DIALOGUE)
    assert [s.source_blocks for s in a] == [(0,), (1,), (2,)]
    assert [s.source_blocks for s in b] == [(1,), (2,), (3,)], "K8 indeks uzayi kaydi"
    assert [s.speaker for s in a] == ["Ada", "Ada", "Ada"]
    assert [s.speaker for s in b] == ["Ada", "Ada", "Ada"], (
        "esik-alti blok eklenince miras kayboldu -- `_group`'a SUZULMUS liste geciyor olabilir"
    )

    with sorgu_kaydi() as kayit:
        normalize(kayik, OcrPreset.DIALOGUE)
    miras = [s for s in kayit if s.miras]
    assert len(miras) == 2, miras
    assert miras[0].sol_bbox == kayik[1].bbox and miras[0].sag_bbox == kayik[2].bbox
    assert miras[1].sol_bbox == kayik[2].bbox and miras[1].sag_bbox == kayik[3].bbox


def test_r6_k28_blocks_varsayilani_bilincli_ve_GECIKMELI_patliyor() -> None:
    """Karar: "`blocks=()` varsayilani YALNIZCA `items` bosken ya da
    UZUNLUK-TEK sinir DOGMAYAN dogrudan cagrilar icindir. Aksi halde
    `IndexError` yukselir -- BILINCLIDIR: sessiz yanlis yerine GURULTULU
    hata (patlama GECIKMELIDIR, yalniz `reason == "length" and
    nxt.speaker is None` sinirinda dogar)."

    Uc sik da ayri ayri sinanir; ozellikle "sessiz yanlis URETMIYOR"."""
    params = get_params(OcrPreset.DIALOGUE)
    assert _group([], params) == []

    # (a) uzunluk-TEK sinir DOGMAYAN dogrudan cagri -> patlamaz
    a = _Item("kisa", Rect(0, 0, 240, 18), "Ada", (0,))
    b = _Item("metin", Rect(0, 500, 240, 18), None, (1,))  # gap -> "gap" sebebi
    assert _group_rejection_reason(a, b, params) == "gap"
    ciktı = _group([a, b], params)
    assert [it.source_blocks for it in ciktı] == [(0,), (1,)]
    assert [it.speaker for it in ciktı] == ["Ada", None]

    # (b) UZUNLUK-TEK sinir + `nxt.speaker is None` -> GURULTULU IndexError
    c = _Item("A" * 200, Rect(0, 0, 240, 18), "Ada", (0,))
    d = _Item("B" * 200, Rect(0, 20, 240, 18), None, (1,))
    assert _group_rejection_reason(c, d, params) == "length"
    with pytest.raises(IndexError):
        _group([c, d], params)

    # (c) ayni cift, `blocks` VERILDIGINDE calisir ve miras uygular
    blocks = [blk("A" * 200, 0, 0), blk("B" * 200, 0, 20)]
    sonuc = _group([c, d], params, blocks=blocks)
    assert [it.speaker for it in sonuc] == ["Ada", "Ada"]


def test_r6_k28_group_icinde_TEK_replace_var_ve_goruntu_gecisinde() -> None:
    """Karar: "Bolumleme dongusunun ICINDE hicbir `replace(...)` YAZILMAZ
    -- ikame TAMAMEN `_raw_query_pair`'in icindedir." Yani `_group`in
    TAMAMINDA tek bir `replace` cagrisi olmali ve o da goruntu gecisinde."""
    fn = _func_ast(normalizer_mod._group)
    replaces = [
        n for n in ast.walk(fn)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "replace"
    ]
    assert len(replaces) == 1, [ast.unparse(n) for n in replaces]
    assert {k.arg for k in replaces[0].keywords} == {"speaker"}, ast.unparse(replaces[0])
    flag_ifs = [
        s for s in fn.body
        if isinstance(s, ast.If) and isinstance(s.test, ast.Name) and s.test.id == "apply_inheritance"
    ]
    assert len(flag_ifs) == 1
    assert replaces[0] in list(ast.walk(flag_ifs[0])), "tek `replace` goruntu gecisinde DEGIL"


# ===========================================================================
# 2. TARIHSEL -- kararin "DEGISMEZ/DEGISMEDI" dedigi her parca
# ===========================================================================


def _git_kaynak(rev: str) -> str:
    proc = subprocess.run(
        ["git", "show", f"{rev}:src/ocr/normalizer.py"],
        cwd=str(REPO_KOK), capture_output=True, text=True, encoding="utf-8",
    )
    if proc.returncode != 0:
        pytest.skip(f"git erisilemedi ({rev}): {proc.stderr[:200]}")
    return proc.stdout


def _govde_metni(src: str, ad: str) -> str:
    """Bir tanimın DOCSTRING'SIZ, normalize edilmis govde metni."""
    for n in ast.parse(src).body:
        if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name == ad:
            kopya = ast.parse(ast.unparse(n)).body[0]
            govde = kopya.body  # type: ignore[attr-defined]
            if (
                govde
                and isinstance(govde[0], ast.Expr)
                and isinstance(govde[0].value, ast.Constant)
                and isinstance(govde[0].value.value, str)
            ):
                kopya.body = govde[1:]  # type: ignore[attr-defined]
            return ast.unparse(kopya)
    raise AssertionError(f"{ad} bulunamadi")


@pytest.mark.parametrize(
    "ad",
    [
        "_Item",
        "normalize",
        "_should_group",
        "_group_rejection_reason",
        "_merge_hyphenated",
        "_extract_speakers",
        "_is_noise",
        "_collapse_intraline",
        "_union_rect",
        "_split_speaker_label",
        "_validate_confidences",
    ],
)
def test_r6_kararin_DEGISMEDI_dedigi_parca_gercekten_degismemis(ad: str) -> None:
    """Karar tur 6 icin TEK kod degisikligi ilan ediyor (K28): `_group`
    imzasi + `_raw_query_pair` + `_normalize_impl`'in `blocks=blocks`
    satiri. "`_Item`, `normalize` govdesi, `_should_group` DEGISMEDI"
    ACIKCA yaziyor; adim 1-4'un yardimcilari da K28'in kapsaminda degil.

    Bu test iddiayi K28 ONCESI surumle (`74256d8`) karsilastirarak
    dogrular -- "docstring buyudu" ile "govde de degisti" karistirilamaz.
    Kararin belgeleme maddeleri (K29-K32) docstring'leri BUYUTUR; govde
    KARSILASTIRMASI docstring'siz yapilir."""
    onceki = _govde_metni(_git_kaynak(K28_ONCESI), ad)
    simdi = _govde_metni(REPO_KOK.joinpath("src/ocr/normalizer.py").read_text(encoding="utf-8"), ad)
    assert onceki == simdi, f"{ad} GOVDESI K28 turunda degismis -- karar bunu ilan etmiyor"


def test_r6_k28_turunun_kod_degisikligi_gercekten_UC_noktayla_sinirli() -> None:
    """Tersten kapi: K28 oncesi surume gore GOVDESI degisen ust duzey
    tanimlar TAM OLARAK `_group`, `_normalize_impl` ve YENI `_raw_query_
    pair` olmali. Dorduncu bir degisiklik varsa karar onu ilan etmiyordur."""
    onceki_src = _git_kaynak(K28_ONCESI)
    simdi_src = REPO_KOK.joinpath("src/ocr/normalizer.py").read_text(encoding="utf-8")

    def adlar(src: str) -> set[str]:
        return {
            n.name for n in ast.parse(src).body if isinstance(n, (ast.FunctionDef, ast.ClassDef))
        }

    eski, yeni = adlar(onceki_src), adlar(simdi_src)
    assert yeni - eski == {"_raw_query_pair"}, yeni - eski
    assert eski - yeni == set(), eski - yeni
    degisen = {
        ad for ad in eski if _govde_metni(onceki_src, ad) != _govde_metni(simdi_src, ad)
    }
    assert degisen == {"_group", "_normalize_impl"}, degisen


def test_r6_item_alanlari_degismedi_ve_normalize_govdesi_tek_delegasyon() -> None:
    """Karar: "`_Item` DEGISMEZ. Yeni alan yok" + "`normalize`'in govdesi
    degismez" (K30 bolumunde geri cekilen madde). `normalize` govdesi TEK
    bir `return _normalize_impl(blocks, preset)` -- `apply_inheritance`
    ACIKCA GECILMEZ (tur 5'te sef bunu zorunlu kilmis, tur 6'da GERI
    CEKMISTI; testim o geri cekmenin uygulandiginin kanitidir)."""
    assert [f.name for f in fields(_Item)] == ["text", "bbox", "speaker", "source_blocks"]
    assert [f.type for f in fields(_Item)] == ["str", "Rect", "str | None", "tuple[int, ...]"]

    fn = _func_ast(normalize)
    govde = [s for s in fn.body if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))]
    assert len(govde) == 1 and isinstance(govde[0], ast.Return), [ast.unparse(s) for s in govde]
    assert ast.unparse(govde[0]) == "return _normalize_impl(blocks, preset)"
    assert list(inspect.signature(normalize).parameters) == ["blocks", "preset"]
    assert normalizer_mod.__all__ == ("normalize",)


def test_r6_should_group_deseni_K28_sonrasi_da_tek_satirlik_devretme() -> None:
    """Karar: "`_should_group` imzasi ve TEK SATIRLIK devretme deseni
    DEGISMEZ" + docstring'i "K28 (TUR 6) de bu fonksiyona DOKUNMADI"
    diyor. Yapisal + davranissal (ayrismazlik fuzz'i yeni tohumla)."""
    fn = _func_ast(_should_group)
    govde = [s for s in fn.body if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))]
    assert len(govde) == 1 and isinstance(govde[0], ast.Return)
    assert ast.unparse(govde[0]) == "return _group_rejection_reason(a, b, params) is None"
    assert list(inspect.signature(_should_group).parameters) == ["a", "b", "params"]

    rng = random.Random(606_28_004)
    gorulen: set[str | None] = set()
    for _ in range(3000):
        for preset in ALL_PRESETS:
            params = get_params(preset)
            a = _Item(
                "a" * rng.randint(1, 200),
                Rect(rng.randint(-40, 300), rng.randint(-40, 300), rng.choice([-2, 0, 8, 240]), rng.choice([-2, 0, 5, 18])),
                rng.choice([None, "Ada", "Efe"]),
                (0,),
            )
            b = _Item(
                "b" * rng.randint(1, 200),
                Rect(rng.randint(-40, 300), rng.randint(-40, 300), rng.choice([-2, 0, 8, 240]), rng.choice([-2, 0, 5, 18])),
                rng.choice([None, "Ada", "Efe"]),
                (1,),
            )
            r = _group_rejection_reason(a, b, params)
            gorulen.add(r)
            assert _should_group(a, b, params) is (r is None)
    assert gorulen == {None, "speaker", "length", "height", "gap", "width", "overlap"}, gorulen


# ===========================================================================
# 3. K29 -- docstring'de anilan her test adi VAR (BAGIMSIZ tarama)
# ===========================================================================


def _docstringler(yol: Any) -> list[str]:
    """Modul, sinif, fonksiyon VE attribute docstring'lerinin hepsi."""
    agac = ast.parse(yol.read_text(encoding="utf-8"))
    out: list[str] = []
    for n in ast.walk(agac):
        govde = getattr(n, "body", None)
        if not isinstance(govde, list):
            continue
        for st in govde:
            if isinstance(st, ast.Expr) and isinstance(st.value, ast.Constant) and isinstance(st.value.value, str):
                out.append(st.value.value)
    return out


def test_r6_k29_docstring_test_atiflari_BAGIMSIZ_taramada_da_temiz() -> None:
    """K29 DEGISMEZ: "`normalizer.py`/`presets.py` docstring'lerinde `test_`
    ile baslayan her tanimlayici `tests/unit/ocr/test_normalizer.py`
    icinde `def <ad>(` olarak VAR; on-ek atfi YALNIZCA `test_x_*`
    biciminde."

    Olcusu `purity_check.py` (kabul komutu). Bu test o kapiyi KOR KABUL
    ETMEZ, taramayi KENDIM yapar: satir sarmasi (`_` ile bolunmus ad)
    birlestirilir, `.py` dosya adlari dislanir, CIPLAK `_` sonlu on-ek
    IHLALDIR (yalniz acik `*` kabul edilir)."""
    tanimli = set(re.findall(r"def\s+(test_[A-Za-z0-9_]+)\s*\(", URUN_TESTI.read_text(encoding="utf-8")))
    assert len(tanimli) > 90, len(tanimli)
    atif = 0
    ihlal: list[str] = []
    for yol in (REPO_KOK / "src/ocr/normalizer.py", REPO_KOK / "src/ocr/presets.py"):
        for d in _docstringler(yol):
            birlesik = re.sub(r"_\s*\n\s*", "_", d)  # satir-sonu `_` sarmasi
            for m in re.finditer(r"test_[A-Za-z0-9_]*\*?", birlesik):
                ad = m.group(0)
                if birlesik[m.end() : m.end() + 3] == ".py" or ad == "test_":
                    continue
                atif += 1
                if ad.endswith("*"):
                    if not any(t.startswith(ad[:-1]) for t in tanimli):
                        ihlal.append(f"{yol.name}: on-ek `{ad}` hicbir testle eslesmiyor")
                elif ad not in tanimli:
                    ihlal.append(f"{yol.name}: `{ad}` urun test dosyasinda YOK")
    assert atif >= 15, f"tarama hicbir sey bulmadi ({atif}) -- kapim BOS"
    assert ihlal == [], ihlal


# ===========================================================================
# 4. K30 / K31 / K32 -- KENDI girdilerimle davranissal yeniden uretim
# ===========================================================================


def test_r6_k30_artik_bosluk_KUCUKSE_miras_korunur_kendi_geometrim() -> None:
    """K30 (kararin KOSULLU cumlesi, birinci yol): adim 1'de dusen bir blok
    geride GERCEK bir geometrik bosluk birakir; bosluk
    `max_vertical_gap_ratio * min(h)` esigini ASMAZSA miras KORUNUR.
    `dialogue`: 0.8 * 18 = 14.4; artik bosluk 4px."""
    blocks = [
        blk("Ada: " + "X" * 150, 0, 0),       # bottom 18
        blk("GURULTU", 0, 18, confidence=0.10),  # adim 1'de DUSER
        blk("Y" * 150, 0, 22),                # gap = 22 - 18 = 4 < 14.4
    ]
    out = normalize(blocks, OcrPreset.DIALOGUE)
    assert [s.source_blocks for s in out] == [(0,), (2,)], [s.source_blocks for s in out]
    assert [s.speaker for s in out] == ["Ada", "Ada"]


def test_r6_k30_artik_bosluk_BUYUKSE_miras_yok_kendi_geometrim() -> None:
    """K30, IKINCI yol: ayni fixture, artik bosluk 22px > 14.4 -> sinir
    artik YALNIZ-UZUNLUK siniri DEGILDIR, K21 uyarinca miras UYGULANMAZ.
    Sefin sürüm-1 cumlesi KOSULSUZDU ve YANLISTI; bu test kosulun IKI
    yonunu de sabitler."""
    blocks = [
        blk("Ada: " + "X" * 150, 0, 0),
        blk("GURULTU", 0, 18, confidence=0.10),
        blk("Y" * 150, 0, 40),                # gap = 40 - 18 = 22 > 14.4
    ]
    out = normalize(blocks, OcrPreset.DIALOGUE)
    assert [s.source_blocks for s in out] == [(0,), (2,)]
    assert [s.speaker for s in out] == ["Ada", None]


def test_r6_k31_a_ikinci_etiket_taniniyorsa_duser_kendi_girdim() -> None:
    """K31 (a): ikinci etiket K9'a gore TANINIYOR ve ad AYNI -> etiket
    METINDEN DUSER, tek segment, tek `speaker`."""
    out = normalize([blk("Ada: merhaba", 0, 0), blk("Ada: nasilsin", 0, 20)], OcrPreset.DIALOGUE)
    assert len(out) == 1, [s.text for s in out]
    assert out[0].text == "merhaba nasilsin"
    assert out[0].speaker == "Ada"
    assert out[0].source_blocks == (0, 1)


def test_r6_k31_b_taninmayan_ikinci_etiket_metinde_kalir_kendi_girdim() -> None:
    """K31 (b): ikinci etiket K9'un AD SUZGECINDEN gecemiyorsa (rakamli
    ad) o blok `speaker=None` kalir, K15'in `X/None` satiriyla bloklar
    YINE birlesir, ETIKET METNIN ICINDE KALIR, segment ILK konusmaciya
    atfedilir. Karar bunu "(a)'dan KOTU ama BILINCLI sinir" diye
    isaretliyor -- test davranisi BELGELER, DUZELTMEZ."""
    out = normalize([blk("Ada: merhaba", 0, 0), blk("Ada2: nasilsin", 0, 20)], OcrPreset.DIALOGUE)
    assert len(out) == 1, [s.text for s in out]
    assert out[0].text == "merhaba Ada2: nasilsin"
    assert out[0].speaker == "Ada"


def test_r6_k31_iki_farkli_TANINAN_ad_birlesmez_kendi_girdim() -> None:
    """K31'in parantez ici cumlesi: "iki FARKLI TANINAN ad BIRLESMEZ".
    K9/K15'in asil yasagi budur; K31 (a)/(b) onu gevsetmemis olmali."""
    out = normalize([blk("Ada: merhaba", 0, 0), blk("Bora: nasilsin", 0, 20)], OcrPreset.DIALOGUE)
    assert [(s.text, s.speaker) for s in out] == [("merhaba", "Ada"), ("nasilsin", "Bora")]


def test_r6_k32_nfd_govde_bolumlemeyi_degistiriyor_kendi_girdim() -> None:
    """K32: `normalize` girdinin NFC oldugunu VARSAYAR; varsayim SUZGECLE
    SINIRLI DEGILDIR -- `max_group_chars` CODEPOINT sayar, bu yuzden ayni
    GORUNEN metin NFD gelirse BOLUMLEME de degisir.

    Kendi govdem: blok basina 88 codepoint'lik aksanli metin. NFC'de
    88*3 + 2 = 266 <= 280 (tek segment); NFD'de her `a` iki codepoint
    olur -> 176*3 + 2 = 530 > 280 (bolunur)."""
    govde = "á" * 88  # 'á' -- NFC'de TEK codepoint
    nfc = [blk(unicodedata.normalize("NFC", govde), 0, i * 20) for i in range(3)]
    nfd = [blk(unicodedata.normalize("NFD", govde), 0, i * 20) for i in range(3)]
    assert len(nfc[0].text) == 88 and len(nfd[0].text) == 176
    assert unicodedata.normalize("NFC", nfd[0].text) == nfc[0].text  # AYNI GORUNEN metin

    a = normalize(nfc, OcrPreset.DIALOGUE)
    b = normalize(nfd, OcrPreset.DIALOGUE)
    assert len(a) == 1, [s.source_blocks for s in a]
    assert len(b) > len(a), (
        "NFD govde bolumlemeyi DEGISTIRMIYOR -- K32'nin 'varsayim suzgecle sinirli "
        f"degildir' cumlesi kodda karsiligi olmayan bir iddia olurdu: {len(a)} vs {len(b)}"
    )


def test_r6_k32_yalniz_etiket_aksanliysa_speaker_dusuyor_kendi_girdim() -> None:
    """K32'nin ikinci yarisi: YALNIZ etiket aksanliysa segment SAYISI ayni
    kalir ama `speaker` `'María'` -> `None`'a duser ve etiket METINDE
    kalir (K31/b yolu). "Yalniz-sayi assert'i ayrimi kacirir" cumlesinin
    kendi girdimle kaniti."""
    nfc = unicodedata.normalize("NFC", "María: hola")
    nfd = unicodedata.normalize("NFD", "María: hola")
    a = normalize([blk(nfc, 0, 0)], OcrPreset.DIALOGUE)
    b = normalize([blk(nfd, 0, 0)], OcrPreset.DIALOGUE)
    assert len(a) == len(b) == 1
    assert a[0].speaker == unicodedata.normalize("NFC", "María")
    assert a[0].text == "hola"
    assert b[0].speaker is None, "NFD ad konusmaci sayildi -- K32'nin cumlesi yanlis olurdu"
    assert ":" in b[0].text and b[0].text.startswith(unicodedata.normalize("NFD", "María"))
    # ayrac kumesi ETKILENMEZ (K17)
    assert _split_speaker_label(nfc)[0] is not None
    assert _split_speaker_label(nfd)[0] is None


# ===========================================================================
# 5. KARARIN ZORUNLU KILDIGI DOCSTRING CUMLELERI GERCEKTEN VAR MI
# ===========================================================================


def _hedef_docstring(ad: str) -> str:
    if ad == "MODUL":
        return _duz(normalizer_mod.__doc__ or "")
    return _duz(getattr(normalizer_mod, ad).__doc__ or "")


@pytest.mark.parametrize(
    ("hedef", "cumle"),
    [
        # --- K28 DEGISMEZ ---
        ("MODUL", "OKUMA SIRASINDA SON gelen blogun `bbox`'i"),
        ("MODUL", "OKUMA SIRASINDA ILK gelen blogun `bbox`'i"),
        ("MODUL", "OKUMA SIRASI = `(bbox.y, bbox.x, girdi indeksi)` ARTAN"),
        ("MODUL", "`source_blocks[-1]` / `[0]` KULLANILMAZ"),
        ("MODUL", "KAPSAM (K24'ten devralinir)"),
        # --- K28-KOK: adim 3 salt tipografik, bilincli acik sinir ---
        ("_merge_hyphenated", "ADIM 3 SALT TIPOGRAFIKTIR (K5) ve HICBIR GEOMETRIK KONTROL YAPMAZ"),
        ("MODUL", "KOK, ACIK BIRAKILDI"),
        # --- `_raw_query_pair` sozlesmesi ---
        ("_raw_query_pair", "`blocks` OZGUN listedir"),
        ("_raw_query_pair", "`blocks` YETERSIZSE `IndexError` yukselir"),
        ("_raw_query_pair", "IKAME YALNIZ `bbox`'a dokunur"),
        # --- K30 KOSULLU cumle ---
        ("_group", "esigini ASARSA sinir artik yalniz-uzunluk siniri DEGILDIR"),
        ("_group", "ASMAZSA miras KORUNUR"),
        # --- K31 (a)/(b) ---
        ("_group", "(a) Ikinci etiket K9'a gore TANINIYORSA"),
        ("_group", "(b) Ikinci etiket K9'un AD SUZGECINDEN gecemiyorsa"),
        ("_group", "iki FARKLI TANINAN ad BIRLESMEZ"),
        # --- K28 kapsam / iki gecis ---
        ("_group", "Bolumleme dongusunun ICINDE hicbir `replace(...)` YAZILMAZ"),
        # --- K32 modul duzeyinde VE ad suzgecinde ---
        ("MODUL", "`normalize` girdinin **NFC** oldugunu VARSAYAR"),
        ("MODUL", "BOLUMLEME DE DEGISIR"),
        ("_split_speaker_label", "GIRDI NFC VARSAYIMI"),
        ("_split_speaker_label", "Varsayim BU SUZGECLE SINIRLI DEGILDIR"),
    ],
)
def test_r6_kararin_zorunlu_kildigi_docstring_cumlesi_var(hedef: str, cumle: str) -> None:
    """PROTOKOL S4.6/2: karar bir cumleyi "docstring'e ZORUNLU" diye
    yazdiysa o cumlenin karsiligi kodda ARANABILIR olmali. Bu kapi,
    "belgelendi" denip belgelenmemis maddeleri yakalar."""
    assert _duz(cumle) in _hedef_docstring(hedef), f"{hedef} docstring'inde YOK: {cumle}"


# ===========================================================================
# 6. BU TURUN IKI OLCUM BULGUSU -- kararin iddiasi FIXTURE yuzunden tutmuyor
# ===========================================================================


def test_r6_BULGU_olcu3b_fixture_okuma_sirasinda_M4_orada_ayrismaz() -> None:
    """BULGU (env.md TUR 6 / MERCEK B/1): "M4 ... -> olcu 3/3b ... kirilmali".

    OLCTUM: `olcu3b_fixture()`in bloklari INDEKS sirasi = OKUMA sirasi
    olacak sekilde dizili (y = 0, 20, 40, 60, 90), dolayisiyla
    `max(source_blocks)` ile `okuma_sirasi(...)[-1]` AYNI blogu verir ve
    M4 orada AYRISMAZ. Mutant sondasi bunu uctan uca dogruluyor
    (`test_k28_mutant_sondasi_tur6.py`): M4 olcu 3 (iki on ayar), olcu 5
    ve olcu 6'yi kiriyor, olcu 3b'yi KIRMIYOR.

    Kararin KENDI metni ("olcu 3 ve 6 kirilmali") DOGRU; sapan, env.md'nin
    ozetidir. Test fixture'in o ozelligini PINLER -- fixture guclendirilip
    sirasiz hale getirilirse bu test kirilir ve bulgu kapanmis olur."""
    blocks = olcu3b_fixture()
    sirali = sorted(range(len(blocks)), key=lambda i: (blocks[i].bbox.y, blocks[i].bbox.x, i))
    assert sirali == list(range(len(blocks))), (
        "olcu3b fixture'i artik SIRASIZ -- bulgu kapanmis olabilir, verdict guncellensin"
    )
    with sorgu_kaydi() as kayit:
        normalize(blocks, OcrPreset.DIALOGUE)
    miras = [s for s in kayit if s.miras]
    assert len(miras) == 1
    sb = miras[0].sol_sb
    assert len(sb) >= 3, sb  # 3b'nin asil isi: UC bloklu kuyruk (off-by-one)
    assert max(sb) == okuma_sirasi(blocks, sb)[-1], (
        "indeks sirasi ile okuma sirasi AYRISIYOR -- M4 burada da kirilirdi"
    )


def test_r6_BULGU_olcu5_fixture_sag_tarafi_daima_tek_bloklu_M5_orada_ayrismaz() -> None:
    """BULGU (sef_karari-tur6.md, MERCEK B/(d)): "M5 ekler -- sag tarafi
    `nxt` olarak birakan mutant -> olcu 2, 5 ve 6 kirilmali".

    OLCTUM: `olcu5_fixture()` IKI sinir uretiyor ve IKISINDE DE ADAY
    (sag taraf) TEK BLOKLU -- `(3,)` ve `(6,)`. Tek bloklu bir adayda
    `replace(nxt, bbox=blocks[ilk].bbox)` ile `nxt`in KENDISI ayni
    `bbox`'i tasir, yani M5 orada YAPI GEREGI ayrismaz. Mutant sondasi
    uctan uca dogruluyor: M5 olcu 2'nin uc varyantini ve olcu 6'yi
    kiriyor, olcu 5'i KIRMIYOR.

    Kitin `olcu6_kos`'unda `coklu_sag >= 500` alt siniri VAR; olcu 5'in
    fixture'inda karsiligi YOK (kitin kendi selftest'i de yalniz
    `coklu_sol`u yazdiriyor). Bu, olcu 5'in SAG TARAF yarisini SIFIR
    ayirt edicilikle biraktigi anlamina gelir."""
    blocks = olcu5_fixture()
    with sorgu_kaydi() as kayit:
        normalize(blocks, OcrPreset.DIALOGUE)
    miras = [s for s in kayit if s.miras]
    assert len(miras) >= 2, miras
    assert all(len(s.sol_sb) > 1 for s in miras), [s.sol_sb for s in miras]
    assert all(len(s.sag_sb) == 1 for s in miras), (
        "olcu 5 fixture'i artik COK BLOKLU aday uretiyor -- bulgu kapanmis olabilir, "
        f"verdict guncellensin: {[s.sag_sb for s in miras]}"
    )
    # ve tek bloklu adayda ham ikame ile `nxt` BIREBIR ayni bbox'i tasir
    for s in miras:
        assert s.sag_bbox == blocks[s.sag_sb[0]].bbox


# ===========================================================================
# yardimcilar
# ===========================================================================


def _yalniz_etiket(text: str) -> bool:
    ad, kalan = _split_speaker_label(text)
    return ad is not None and not kalan.strip()


def _zincirli_girdi(rng: random.Random) -> list[TextBlock]:
    """Zincirleme hyphen (cok bloklu kuyruk VE cok bloklu ADAY) + uzunluk
    sinirlari + sirasiz girdi ureten kendi derlemim."""
    bs: list[TextBlock] = []
    y = 0
    bs.append(blk("Ada: " + "X" * rng.randint(80, 160), 0, y))
    y += rng.choice([20, 22, 26])
    for _ in range(rng.randint(2, 5)):
        for j in range(rng.randint(2, 4)):
            on = "Y" if j == 0 else rng.choice("yzw")
            bs.append(
                blk(
                    on * rng.randint(20, 60) + " son-",
                    rng.choice([0, 0, 100]),
                    y,
                    w=rng.choice([240, 240, 8, 308]),
                    h=rng.choice([18, 18, 5, 50]),
                )
            )
            y += rng.choice([0, 2, 20])
        bs.append(
            blk(
                "raki" + "k" * rng.randint(0, 40),
                rng.choice([0, 100, 300]),
                y,
                w=rng.choice([240, 8, 308]),
                h=rng.choice([18, 5, 50]),
            )
        )
        y += rng.choice([2, 20, 45])
    bs.append(blk("Z" * rng.randint(60, 160), 0, y))
    if rng.random() < 0.6:
        rng.shuffle(bs)
    return bs
