"""TESTER-B (KARAR UYUMU merceği) -- T-004 TUR 3 -- K19/K20 saldiri seti.

Bu dosya `test_karar_uyumu.py` (TUR 2'den kalma, hala gecerli -- K1-K18)
dosyasina EK olarak, `.agents/tasks/T-004/sef_karari-tur3.md`deki IKI YENI
kararin (K19 davranis degisikligi, K20 salt dokumantasyon) koda BIREBIR
uygulandigini, ozellikle K19'un en yuksek regresyon riskini tasiyan
mekanizmasini (`_should_group` <-> `_group_rejection_reason` tutarliligi,
mirasin SADECE "length" sebebinde calismasi, X/Y'ye ASLA sizmamasi)
dogrular.

Odak (env.md TUR 3 / MERCEK B):
  1. `_should_group` ile `_group_rejection_reason` HER girdide tutarli mi
     (kapsamli + fuzz, sabit tohum).
  2. Miras YALNIZ "length" sebebinde mi calisiyor -- diger bes sebebe
     (speaker, height, gap, width, overlap) sizmis mi?
  3. X/Y (iki farkli konusmaci) durumunda miras KESINLIKLE olmamali.
  4. K15 matrisinin bes satiri (K19 sonrasi da).
  5. K16 yozlasmis geometri reddi (K19 ayni fonksiyonda).
  6. K20: NFKC ile acilan alti karakterin BAGIMSIZ tam Unicode taramasi.
  7. K14 bütçe assertion'i imkansiz esikle zorlanir.
  8. K2 islem sirasi K19 sonrasi kaymamis.

Sabit tohum / deterministik girdi -- rastgelelik yok.
"""
from __future__ import annotations

import random
import unicodedata

import pytest

from src.contracts.models import OcrPreset, Rect, Segment, TextBlock
from src.ocr.normalizer import _Item, _group_rejection_reason, _should_group, normalize
from src.ocr.presets import get_params


def blk(
    text: str,
    x: int,
    y: int,
    *,
    w: int = 300,
    h: int = 20,
    confidence: float = 0.9,
    monitor_index: int = 0,
    dpi_scale: float = 1.0,
) -> TextBlock:
    return TextBlock(
        text=text,
        bbox=Rect(x=x, y=y, w=w, h=h, monitor_index=monitor_index, dpi_scale=dpi_scale),
        confidence=confidence,
    )


# ---------------------------------------------------------------------------
# 1. `_should_group` <-> `_group_rejection_reason` tutarliligi -- kapsamli
#    (kucuk parametre uzayi TAM) + fuzz (buyuk uzay, sabit tohum).
# ---------------------------------------------------------------------------


_SPEAKERS: list[str | None] = [None, "Ada", "Efe"]
_HEIGHTS = [-5, 0, 1, 20]
_WIDTHS = [-5, 0, 1, 100]
_GAPS = [-10, 0, 5, 50]
_TEXT_LENS = [1, 50, 400]


def test_r3_should_group_ve_rejection_reason_tam_kapsamli_tutarli() -> None:
    """Kucuk ama TAM (kartezyen carpim) bir parametre uzayinda, HER
    kombinasyon icin `_should_group(a,b,p) == (_group_rejection_reason(a,b,p)
    is None)`. Bu ikisi ayrisirsa K19'un mirasi YANLIS yerde tetiklenir --
    ya da K15/K16 testleri (`_should_group` uzerinden) artik gercek
    `_group` davranisini YANSITMAZ."""
    params_all = [get_params(p) for p in OcrPreset]
    count = 0
    for a_sp in _SPEAKERS:
        for b_sp in _SPEAKERS:
            for h in _HEIGHTS:
                for w in _WIDTHS:
                    for gap in _GAPS:
                        for tlen in _TEXT_LENS:
                            a = _Item(
                                text="x" * tlen,
                                bbox=Rect(x=0, y=0, w=w, h=h),
                                speaker=a_sp,
                                source_blocks=(0,),
                            )
                            b = _Item(
                                text="y" * tlen,
                                bbox=Rect(x=0, y=h + gap, w=w, h=h),
                                speaker=b_sp,
                                source_blocks=(1,),
                            )
                            for params in params_all:
                                reason = _group_rejection_reason(a, b, params)
                                sg = _should_group(a, b, params)
                                assert sg == (reason is None), (
                                    f"TUTARSIZLIK: a_sp={a_sp} b_sp={b_sp} h={h} w={w} "
                                    f"gap={gap} tlen={tlen} reason={reason!r} should_group={sg}"
                                )
                                count += 1
    assert count > 0


def test_r3_should_group_ve_rejection_reason_fuzz_tutarli_sabit_tohum() -> None:
    """Genis, RASTGELE (SABIT tohum -- deterministik, tekrar edilebilir)
    bir ornekleme -- kapsamli testin gormedigi kombinasyonlari (negatif
    genis araliklar, buyuk metinler, karisik x/y konumlari) tarar."""
    rng = random.Random(20260910)  # sabit tohum
    params_all = [get_params(p) for p in OcrPreset]
    speakers: list[str | None] = [None, "Ada", "Efe", "Zzz"]
    n_mismatch = 0
    for _ in range(4000):
        a = _Item(
            text="x" * rng.randint(0, 500),
            bbox=Rect(
                x=rng.randint(-200, 200),
                y=rng.randint(-200, 200),
                w=rng.randint(-50, 300),
                h=rng.randint(-50, 300),
            ),
            speaker=rng.choice(speakers),
            source_blocks=(0,),
        )
        b = _Item(
            text="y" * rng.randint(0, 500),
            bbox=Rect(
                x=rng.randint(-200, 200),
                y=rng.randint(-200, 200),
                w=rng.randint(-50, 300),
                h=rng.randint(-50, 300),
            ),
            speaker=rng.choice(speakers),
            source_blocks=(1,),
        )
        params = rng.choice(params_all)
        reason = _group_rejection_reason(a, b, params)
        sg = _should_group(a, b, params)
        if sg != (reason is None):
            n_mismatch += 1
    assert n_mismatch == 0, f"{n_mismatch} tutarsiz cift bulundu (4000 fuzz denemesi)"


# ---------------------------------------------------------------------------
# 2 + 3. K19 mirasi YALNIZ "length" sebebinde; diger bes sebepte (speaker,
#    height, gap, width, overlap) KESINLIKLE sizmiyor -- ozellikle X/Y.
# ---------------------------------------------------------------------------


def _reason_for(a: _Item, b: _Item, preset: OcrPreset = OcrPreset.DIALOGUE) -> str | None:
    return _group_rejection_reason(a, b, get_params(preset))


def test_r3_reason_kodlarinin_hepsi_uretilebilir_oncul_kontrol() -> None:
    """Asagidaki testlerin gecerliligi icin ONCE her reason kodunun
    GERCEKTEN uretilebildigini dogrula -- aksi halde "miras sizmiyor"
    iddiasi bos bir dogrulama olur (o reason hic tetiklenmemis olabilir)."""
    dialogue = get_params(OcrPreset.DIALOGUE)

    # speaker
    a = _Item("a", Rect(0, 0, 100, 20), "Ada", (0,))
    b = _Item("b", Rect(0, 20, 100, 20), "Efe", (1,))
    assert _reason_for(a, b) == "speaker"

    # length
    a = _Item("x" * 200, Rect(0, 0, 100, 20), "Ada", (0,))
    b = _Item("y" * 200, Rect(0, 20, 100, 20), None, (1,))
    assert _reason_for(a, b) == "length"

    # height (ref_height <= 0)
    a = _Item("a", Rect(0, 0, 100, 0), "Ada", (0,))
    b = _Item("b", Rect(0, 0, 100, 20), None, (1,))
    assert _reason_for(a, b) == "height"

    # gap (dikey bosluk esigi asildi)
    a = _Item("a", Rect(0, 0, 100, 20), "Ada", (0,))
    big_gap_y = 20 + int(dialogue.max_vertical_gap_ratio * 20) + 100
    b = _Item("b", Rect(0, big_gap_y, 100, 20), None, (1,))
    assert _reason_for(a, b) == "gap"

    # width (ref_width <= 0) -- gap kosulunu GECMESI icin dikey yakin tutulur
    a = _Item("a", Rect(0, 0, 0, 20), "Ada", (0,))
    b = _Item("b", Rect(0, 2, 0, 20), None, (1,))
    assert _reason_for(a, b) == "width"

    # overlap (yatay ortusme yetersiz) -- dikey yakin, genislik pozitif
    a = _Item("a", Rect(0, 0, 10, 20), "Ada", (0,))
    b = _Item("b", Rect(1000, 2, 10, 20), None, (1,))
    assert _reason_for(a, b) == "overlap"


@pytest.mark.parametrize(
    "reason_kurulumu",
    ["speaker_x_y", "height", "gap", "width", "overlap"],
)
def test_r3_diger_bes_sebepte_miras_YOK(reason_kurulumu: str) -> None:
    """`_group` icinde miras SADECE `reason == "length"` iken tetiklenir.
    Asagida, mumkun olan HER diger sebep (speaker/height/gap/width/overlap)
    icin, current.speaker="Ada" (miras ONCULU saglanmis) olacak sekilde bir
    TAM PIPELINE senaryosu kurulur -- kuyruk segmentin speaker'i `None`
    KALMALI (miras YOK). ("speaker_x_y" ozel: X/Y iki farkli etiketli
    konusmaci -- K9'un ASIL yasagi, bloke edici olurdu.)"""
    dialogue = get_params(OcrPreset.DIALOGUE)

    if reason_kurulumu == "speaker_x_y":
        # Ada'nin govdesi ardindan HEMEN Efe'nin KENDI etiketi -- reason "speaker".
        blocks = [
            blk("Ada:", 10, 0),
            blk("Merhaba dunya", 10, 22),
            blk("Efe:", 10, 44),
            blk("Selam sana", 10, 66),
        ]
        out = normalize(blocks, OcrPreset.DIALOGUE)
        assert len(out) == 2
        assert out[0].speaker == "Ada"
        assert out[1].speaker == "Efe"  # KENDI etiketi -- Ada'dan miras ALMADI
        return

    if reason_kurulumu == "height":
        # Ada'nin govdesinden sonra h<=0 olan bir sonraki blok.
        blocks = [blk("Ada:", 10, 0), blk("ilk parca", 10, 22, h=20), blk("ikinci parca", 10, 42, h=0)]
        out = normalize(blocks, OcrPreset.DIALOGUE)
        assert len(out) == 2
        assert out[0].speaker == "Ada"
        assert out[1].speaker is None  # K19: height sebebi -- miras YOK
        return

    if reason_kurulumu == "gap":
        big_gap_y = 22 + 20 + int(dialogue.max_vertical_gap_ratio * 20) + 80
        blocks = [blk("Ada:", 10, 0), blk("ilk parca", 10, 22, h=20), blk("ikinci parca", 10, big_gap_y, h=20)]
        out = normalize(blocks, OcrPreset.DIALOGUE)
        assert len(out) == 2
        assert out[0].speaker == "Ada"
        assert out[1].speaker is None  # K19: gap sebebi -- miras YOK
        return

    if reason_kurulumu == "width":
        blocks = [blk("Ada:", 10, 0, w=0), blk("ilk parca", 10, 22, w=0), blk("ikinci parca", 10, 24, w=0)]
        out = normalize(blocks, OcrPreset.DIALOGUE)
        assert len(out) == 2
        assert out[0].speaker == "Ada"
        assert out[1].speaker is None  # K19: width sebebi -- miras YOK
        return

    if reason_kurulumu == "overlap":
        blocks = [blk("Ada:", 10, 0, w=10), blk("ilk parca", 10, 22, w=10), blk("ikinci parca", 5000, 24, w=10)]
        out = normalize(blocks, OcrPreset.DIALOGUE)
        assert len(out) == 2
        assert out[0].speaker == "Ada"
        assert out[1].speaker is None  # K19: overlap sebebi -- miras YOK
        return

    raise AssertionError(f"bilinmeyen kurulum: {reason_kurulumu}")


def test_r3_uzunluk_asimi_ile_ayni_anda_farkli_konusmaci_speaker_kazanir_length_degil() -> None:
    """`_group_rejection_reason` kontrolleri SIRAYLA calisir (speaker ONCE).
    Iki FARKLI etiketli konusmacinin govdeleri, BIRLESTIRILSE
    `max_group_chars`'i da asacak kadar UZUN olsa BILE, reddin sebebi HER
    ZAMAN "speaker" olmali -- ASLA "length" (aksi halde speaker kontrolu
    length'in ARKASINA dusmus olurdu, K9'un asil yasagi length kontrolunun
    GOLGESINDE ihlal EDILEBILIRDI)."""
    dialogue = get_params(OcrPreset.DIALOGUE)
    long_text = "x" * (dialogue.max_group_chars + 50)  # TEK BASINA bile capi asiyor
    a = _Item(long_text, Rect(0, 0, 100, 20), "Ada", (0,))
    b = _Item(long_text, Rect(0, 20, 100, 20), "Efe", (1,))
    assert _reason_for(a, b) == "speaker"  # "length" DEGIL


def test_r3_k19_mixed_zincir_length_split_sonra_gap_split_miras_dogru_sifirlanir() -> None:
    """KARISIK zincir: Ada'nin govdesi ONCE uzunluk yuzunden bolunur (ilk
    kuyruk MIRAS alir -- K19), SONRA aradaki bir blok BUYUK bir dikey
    bosluk yuzunden ayrilir (bu ikinci bolunme MIRAS ALMAMALI, cunku sebep
    "length" degil "gap"). Onceki bir "length" mirasinin, ZINCIRIN
    ILERISINDEKI bir "gap" bolunmesini de yanlislikla MIRAS ALDIRIP
    ALDIRMADIGINI sinar (K19'un `reason=="length"` sartinin HER bolunme
    NOKTASINDA ayri ayri degerlendirildigini kanitlar)."""
    dialogue = get_params(OcrPreset.DIALOGUE)
    cap = dialogue.max_group_chars
    body = "x" * 60
    # Ada: + yeterince govde bloğu -- en az bir UZUNLUK bolunmesi olusturur.
    n_before_gap = (cap // 60) + 2
    blocks = [blk("Ada:", 10, 0)]
    y = 22
    for i in range(n_before_gap):
        blocks.append(blk(body, 10, y))
        y += 22
    # Simdi BUYUK bir dikey bosluk birak -- bir sonraki blok GAP yuzunden ayrilsin.
    y += int(dialogue.max_vertical_gap_ratio * 20) + 200
    blocks.append(blk("son parca", 10, y))

    out = normalize(blocks, OcrPreset.DIALOGUE)
    assert len(out) >= 3, "en az bir length-bolunmesi + bir gap-bolunmesi bekleniyor"
    # length-kaynakli TUM ara kuyruklar Ada'yi miras almali.
    for s in out[:-1]:
        assert s.speaker == "Ada", f"length-kaynakli kuyruk miras almadi: {s!r}"
    # SON segment (gap yuzunden ayrilan) MIRAS ALMAMALI.
    assert out[-1].text == "son parca"
    assert out[-1].speaker is None, "gap-kaynakli kuyruk YANLISLIKLA miras aldi (K19 ihlali)"


def test_r3_menu_preset_gruplama_kapali_miras_mekanizmasi_hic_calismaz() -> None:
    """K11: `menu` hic gruplamaz (`params.should_group=False`) -- `_group`
    (ve dolayisiyla K19 mirasi) bu preset icin HIC CAGRILMAZ. Uzun bir
    Ada govdesi MENU altinda calistirilinca HER blok kendi ayri
    Segment'i olur, hicbiri (etiket-blogun DOGRUDAN takipcisi disinda)
    Ada'yi miras ALMAMALIDIR."""
    body = "x" * 60
    blocks = [blk("Ada:", 10, 0)] + [blk(body, 10, 22 * (i + 1)) for i in range(5)]
    out = normalize(blocks, OcrPreset.MENU)
    assert len(out) == 5  # gruplama YOK -- her govde ayri segment
    assert out[0].speaker == "Ada"  # K9: etiket ilk takipciye tasindi
    assert all(s.speaker is None for s in out[1:]), "MENU'de K19 mirasi calismamali (gruplama kapali)"


# ---------------------------------------------------------------------------
# 4. K15 matrisinin bes satiri -- K19 SONRASI, hem `_should_group` hem
#    `_group_rejection_reason` seviyesinde.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "a_sp,b_sp,expected",
    [
        ("Ada", "Ada", True),
        ("Ada", None, True),
        (None, None, True),
        (None, "Efe", False),
        ("Ada", "Efe", False),
    ],
)
def test_r3_k15_matris_should_group_ve_reason_ikisi_de_dogru(
    a_sp: str | None, b_sp: str | None, expected: bool
) -> None:
    a = _Item("a", Rect(0, 0, 100, 20), a_sp, (0,))
    b = _Item("b", Rect(0, 20, 100, 20), b_sp, (1,))
    params = get_params(OcrPreset.DIALOGUE)
    assert _should_group(a, b, params) is expected
    reason = _group_rejection_reason(a, b, params)
    assert (reason is None) is expected
    if not expected:
        assert reason == "speaker"


# ---------------------------------------------------------------------------
# 5. K16 -- yozlasmis geometri reddi K19 SONRASI da kosulsuz (reason
#    "height"/"width", gap/overlap degerine BAKILMAKSIZIN).
# ---------------------------------------------------------------------------


def test_r3_k16_yozlasmis_yukseklik_genislik_reason_dogru_ve_kosulsuz() -> None:
    params = get_params(OcrPreset.DIALOGUE)
    # h=0, ayni y (gap=0 -- "uygun" olurdu, geometri BAKILMAKSIZIN reddedilmeli)
    a = _Item("a", Rect(0, 0, 100, 0), None, (0,))
    b = _Item("b", Rect(0, 0, 100, 0), None, (1,))
    assert _group_rejection_reason(a, b, params) == "height"

    # negatif h, cakisan kutular (gap negatif -- "uygun" olurdu)
    a = _Item("a", Rect(0, -15, 100, 20), None, (0,))
    b = _Item("b", Rect(0, 0, 100, -10), None, (1,))
    assert _group_rejection_reason(a, b, params) == "height"

    # w=0, tam dikey komsuluk (gap=0)
    a = _Item("a", Rect(0, 0, 0, 20), None, (0,))
    b = _Item("b", Rect(0, 20, 0, 20), None, (1,))
    assert _group_rejection_reason(a, b, params) == "width"


# ---------------------------------------------------------------------------
# 6. K20 -- BAGIMSIZ tam Unicode taramasi (0x0-0x10FFFF), docstring'in
#    alti karakterlik listesiyle BIREBIR karsilastirma.
# ---------------------------------------------------------------------------


_EXPECTED_K20_CODEPOINTS = {0xFE15, 0xFE16, 0xFE56, 0xFE57, 0xFF01, 0xFF1F}


def test_r3_k20_bagimsiz_tam_unicode_taramasi_docstringle_birebir_eslesir() -> None:
    """Sefin iddiasini (`sef_karari-tur3.md`, docstring K4/K20 bolumu)
    KENDI taramamizla dogrula: NFKC ile TAM OLARAK `?` veya `!`ye acilan,
    ASCII `?`/`!` HARIC her Unicode codepoint (0x0-0x10FFFF) -- sonuc
    docstring'in alti karakterlik listesiyle BIREBIR ayni olmali (ne
    eksik ne fazla)."""
    found: set[int] = set()
    for cp in range(0x110000):
        ch = chr(cp)
        if ch in ("?", "!"):
            continue
        if unicodedata.normalize("NFKC", ch) in ("?", "!"):
            found.add(cp)
    assert found == _EXPECTED_K20_CODEPOINTS, (
        f"BAGIMSIZ tarama docstring listesinden FARKLI: "
        f"eksik={_EXPECTED_K20_CODEPOINTS - found} fazla={found - _EXPECTED_K20_CODEPOINTS}"
    )
    # hepsi zararsiz Po (noktalama) kategorisinde mi -- docstring'in "zararsiz" iddiasi
    for cp in found:
        assert unicodedata.category(chr(cp)) == "Po"


def test_r3_k20_docstring_listesi_koddan_ayri_bir_beyaz_liste_DEGIL() -> None:
    """K20'nin listesi (docstring) BILGI AMACLIDIR -- kod bu listeye
    BAKARAK karar VERMEZ. `_is_single_char_noise`'in YURUTULEBILIR
    GOVDESI (docstring HARIC -- docstring'in aciklama amaciyla ornek
    karakterlerden BAHSETMESI beyaz liste degildir, kod SATIRLARINDA bu
    alti codepoint'in HICBIRINE literal referans OLMAMALI -- karar
    SADECE NFKC denkligiyle alinmali)."""
    import ast
    import inspect

    from src.ocr import normalizer as normalizer_mod

    src = inspect.getsource(normalizer_mod._is_single_char_noise)
    tree = ast.parse(src)
    func_node = tree.body[0]
    assert isinstance(func_node, ast.FunctionDef)
    body_without_docstring = func_node.body[1:]  # ilk eleman docstring (Expr/Constant)
    code_only_src = "\n".join(ast.unparse(node) for node in body_without_docstring)

    for cp in _EXPECTED_K20_CODEPOINTS:
        ch = chr(cp)
        assert ch not in code_only_src, (
            f"U+{cp:04X} YURUTULEBILIR KOD GOVDESINDE sabit kodlanmis (beyaz liste supheli): "
            f"{code_only_src!r}"
        )
    assert "in ('?', '!')" in code_only_src or "in ('!', '?')" in code_only_src, (
        f"NFKC denklik kontrolu koddan kayboldu: {code_only_src!r}"
    )


def test_r3_k20_docstring_beyaz_liste_degil_ibaresini_tasir() -> None:
    """Docstring'in K20 bolumu, listenin BILGI AMACLI oldugunu VE beyaz
    liste OLMADIGINI acikca belirtmeli (env.md: "Liste 'bilgi amaçlı,
    kod NFKC ile karar verir' diye işaretlenmiş mi -- yoksa beyaz liste
    gibi mi okunuyor?")."""
    from src.ocr import normalizer as normalizer_mod

    doc = normalizer_mod.__doc__ or ""
    # ozet paragrafta degil, K4 icindeki DETAYLI K20 aciklamasinda ara --
    # bu yuzden sef_karari referansini tasiyan, daha OZGUL anchor kullanilir.
    k20_start = doc.find("K20 (sef_karari-tur3.md")
    assert k20_start != -1, "K20 detay bolumu (sef_karari-tur3.md referansli) docstring'den kayboldu"
    k20_section = doc[k20_start : k20_start + 3000]
    assert "BILGI AMACLIDIR" in k20_section
    assert "BEYAZ LISTE DEGILDIR" in k20_section
    assert "NFKC" in k20_section


# ---------------------------------------------------------------------------
# 7. K14 -- bütçe assertion'i gercek test dosyasinda imkansiz esikle
#    (kendi olcumumuzle) ZORLANIR -- dekoratif degil.
# ---------------------------------------------------------------------------


def test_r3_k14_assertion_imkansiz_esikle_gercekten_kiriliyor() -> None:
    import statistics
    import time

    blocks = [
        blk(f"Bu diyalog metni numara {i:02d} icin ornek satirdir.", 10, i * 22, confidence=0.9)
        for i in range(30)
    ]
    durations_ms: list[float] = []
    for _ in range(50):
        start = time.perf_counter()
        normalize(blocks, OcrPreset.DIALOGUE)
        durations_ms.append((time.perf_counter() - start) * 1000.0)
    median_ms = statistics.median(durations_ms)

    with pytest.raises(AssertionError):
        assert median_ms <= 0.0, f"medyan {median_ms:.6f} ms > 0.0 ms (imkansiz butce, kasitli)"


def test_r3_k14_gercek_test_dosyasinda_hala_gercek_assert() -> None:
    import inspect

    from tests.unit.ocr import test_normalizer as real_test_mod

    src = inspect.getsource(real_test_mod.test_k14_normalizasyon_butcesi_5ms_medyan)
    assert "assert" in src
    assert "median_ms <= 5.0" in src
    marks = getattr(real_test_mod.test_k14_normalizasyon_butcesi_5ms_medyan, "pytestmark", [])
    mark_names = {m.name for m in marks}
    assert "skip" not in mark_names
    assert "xfail" not in mark_names


# ---------------------------------------------------------------------------
# 8. K2 -- islem sirasi K19 SONRASI kaymadi (esik -> gurultu -> birlestirme
#    -> konusmaci -> gruplama -> yer tutucu).
# ---------------------------------------------------------------------------


def test_r3_k2_docstring_sirasi_k19_sonrasi_hala_dogru() -> None:
    """K19, `_group` (adim 5) iCINDEKI bir mekanizmadir -- adim SIRASININ
    KENDISINI degistirmemeli. Docstring'in "## Isleme sirasi" bolumu HALA
    ayni alti adimi, AYNI sirayla listeliyor mu?"""
    import src.ocr.normalizer as normalizer_mod

    doc = normalizer_mod.__doc__ or ""
    section_start = doc.find("## Isleme sirasi")
    assert section_start != -1
    section_end = doc.find("## K1", section_start)
    assert section_end != -1
    order_section = doc[section_start:section_end]

    idx_threshold = order_section.find("guven esigi filtresi")
    idx_noise = order_section.find("gurultu eleme")
    idx_merge = order_section.find("satir birlestirme")
    idx_speaker = order_section.find("konusmaci ayiklama")
    idx_group = order_section.find("gruplama")
    idx_placeholder = order_section.find("yer tutucu toplama")
    assert -1 not in (idx_threshold, idx_noise, idx_merge, idx_speaker, idx_group, idx_placeholder)
    assert idx_threshold < idx_noise < idx_merge < idx_speaker < idx_group < idx_placeholder


def _k2_esik_alti_orta_blok_fixture(*, bosluk_acar: bool) -> tuple[list[TextBlock], list[int]]:
    """K2 fixture'i: uzunluk-kaynakli bolunecek bir govdenin ORTASINA
    esik-alti bir blok. `bosluk_acar=True` ise gurultu blogu KENDI dikey
    seridini isgal eder (dustukten sonra 2 satirlik BOSLUK kalir);
    `False` ise komsusuyla AYNI `y`'de durur (dustukten sonra hicbir
    geometrik iz BIRAKMAZ)."""
    cap = get_params(OcrPreset.DIALOGUE).max_group_chars
    body = "x" * 60
    n = (cap // 60) + 3
    blocks = [blk("Ada:", 10, 0)]
    noise: list[int] = []
    y = 22
    for i in range(n):
        blocks.append(blk(body, 10, y, confidence=0.9))
        if not bosluk_acar and i == n // 2:
            # AYNI y -- esik-alti (dialogue esigi 0.60), dustugunde bosluk BIRAKMAZ
            noise.append(len(blocks))
            blocks.append(blk("GURULTU", 10, y, confidence=0.05))
        y += 22
        if bosluk_acar and i == n // 2:
            noise.append(len(blocks))
            blocks.append(blk("GURULTU", 10, y, confidence=0.05))
            y += 22
    return blocks, noise


def test_r3_k2_esik_alti_orta_blok_uzunluk_mirasiyla_birlikte_dogru_calisir() -> None:
    """K2 + K19/K21 etkilesimi: bolunmus (uzunluk-kaynakli) bir govdenin
    ORTASINA esik-alti bir blok koy -- adim 1 (esik) adim 5'ten (gruplama,
    K19'un calistigi yer) ONCE calismali, yani esik-alti blok gruplama VE
    miras mantigina hic girmeden dusmeli.

    TUR 5 DUZELTMESI (bu testin assertion'i TUR 3'te yazildi ve TUR 4'te
    BAYATLADI; Tester-B tur 4'te KOSMADIGI icin fark tur 5'te goruldu --
    bkz. `verdict-B.md` tur 5, "kirik testin teshisi"). Eski assertion
    `all(s.speaker == "Ada")` idi. O beklenti K19'un TUR 3 mekanizmasina
    dayaniyordu: "SIRADAKI ILK basarisiz kontrol `length` ise miras al".
    Bu fixture'da esik-alti blok DUSUNCE geride 2 satirlik BOSLUK kaliyor
    (gap=24 > 0.8*20=16), yani sinir AYNI ANDA hem `length` hem GERCEK bir
    geometrik kopus -- K21 (tur 4) TAM OLARAK bunu duzeltti: uzunluk TEK
    engel DEGILSE miras YOK. Yani KOD dogru, ESKI ASSERTION K21-oncesi
    davranisi kodluyordu. Duzeltilmis test artik K2'nin ASIL iddiasini
    (sira: esik ONCE) VE K19/K21'in ayrimini AYRI AYRI sabitliyor."""
    blocks, noise_indices = _k2_esik_alti_orta_blok_fixture(bosluk_acar=True)
    assert noise_indices
    out = normalize(blocks, OcrPreset.DIALOGUE)
    assert len(out) >= 2

    # (a) K2'nin ASIL iddiasi -- esik filtresi adim 1'de calisir: esik-alti
    #     blok gruplamaya HIC girmez, indeksi HICBIR segmentte gorunmez.
    all_src = sorted(i for s in out for i in s.source_blocks)
    for ni in noise_indices:
        assert ni not in all_src

    # (b) ve o blok, GIRDIDEN TAMAMEN cikarilmis gibi davranir: metin,
    #     speaker ve segment SAYISI birebir ayni (indeks uzayi kayar --
    #     K8, cunku girdi listesi kisalir; ama BOLUMLEME SEKLI ayni).
    temiz = [b for i, b in enumerate(blocks) if i not in noise_indices]
    out_temiz = normalize(temiz, OcrPreset.DIALOGUE)
    assert [s.text for s in out] == [s.text for s in out_temiz]
    assert [s.speaker for s in out] == [s.speaker for s in out_temiz]

    # (c) K21 (tur 4): bu fixture'da sinir uzunluk-TEK DEGIL (dusen blogun
    #     yerinde kalan 2 satirlik bosluk GERCEK bir geometrik kopus), o
    #     yuzden kuyruk segment miras ALMAZ.
    assert out[0].speaker == "Ada"
    assert out[-1].speaker is None, [s.speaker for s in out]

    # (d) KONTROL -- ayni senaryo, ama esik-alti blok komsusuyla AYNI y'de
    #     (dustugunde geometrik iz BIRAKMAZ): sinir artik uzunluk-TEK,
    #     miras GERCEKTEN calisir. Yani (c)'deki `None`, mirasin bozuk
    #     olmasindan DEGIL, K21'in dogru ayriminden geliyor.
    blocks2, noise2 = _k2_esik_alti_orta_blok_fixture(bosluk_acar=False)
    out2 = normalize(blocks2, OcrPreset.DIALOGUE)
    assert len(out2) >= 2
    all_src2 = sorted(i for s in out2 for i in s.source_blocks)
    for ni in noise2:
        assert ni not in all_src2
    assert all(s.speaker == "Ada" for s in out2), [s.speaker for s in out2]
