"""TESTER-B (KARAR UYUMU merceği) -- T-004 TUR 5 -- K23-K27 saldiri seti.

`test_karar_uyumu.py` (TUR 2 -- K1-K18) ve `test_karar_uyumu_tur3.py`
(TUR 3 -- K19/K20 + reason kodlari + K14) dosyalarina EK. Bu dosya
`.agents/tasks/T-004/sef_karari-tur5.md`deki BES yeni kararin (K23 bir
DEGISMEZ, K24 K21'in tek gecerli ifadesi, K25 secenek 1 zorunlu, K26
K22'nin olgusal hatasi, K27 `menu` kapsam disi) koda BIREBIR uygulandigini
dogrular.

Odak (env.md TUR 5 / MERCEK B):
  1. K23'un IKI-GECISLI yapisi GERCEKTEN kodda mi -- yoksa tek gecişte
     "mutasyon yapmadan" TAKLIT mi ediliyor? AST ile YAPISAL ispat:
     bolumleme gecisinde HICBIR `speaker` mutasyonu YOK, goruntu gecisinin
     cikti si bolumleme kararlarina GERI BESLENMIYOR.
  2. K23 DEGISMEZI, implementer'in 2500 girdilik denetimine GUVENMEDEN,
     KENDI ureticimle (farkli tohum, farkli geometri dagilimi, monolog
     agirlikli ikinci uretici) -- bolumleme miras acik/kapali BIREBIR ayni.
  3. `_should_group` <-> `_group_rejection_reason` YAPISAL AYRISMAZLIGI
     hala tek satirlik devretme mi; `speaker` kontrolu hala `length`ten
     ONCE mi; reason kodlari tur 3-4 ile BIREBIR ayni mi.
  4. K24: miras-uygunluk sorgusu GERCEKTEN `tail` ile mi cagriliyor.
  5. K25: secenek 1 korunmus mu (`ignore_length` parametresi, donus tipi
     `str | None`), tur 3'un string-karsilastirmali assertion'lari sağ mi.
  6. K26: alti karakterin `unicodedata.decomposition` etiketleri
     docstring'le ortusuyor mu.
  7. K27: dort on ayarin HER biri icin test var mi; `menu`'de gruplama
     GERCEKTEN atlaniyor mu.
  8. K14 butce assertion'i imkansiz esikle ZORLANIR (gercek test dosyasinin
     KENDI govdesi uzerinde).

Sabit tohum / deterministik girdi -- rastgelelik yok.
"""
from __future__ import annotations

import ast
import inspect
import random
import re
import statistics
import time
import unicodedata
from typing import Any

import pytest

import src.ocr.normalizer as normalizer_mod
from src.contracts.models import OcrPreset, Rect, Segment, TextBlock
from src.ocr.normalizer import (
    _group,
    _group_rejection_reason,
    _Item,
    _normalize_impl,
    _should_group,
    normalize,
)
from src.ocr.presets import get_params

ALL_PRESETS = (OcrPreset.DIALOGUE, OcrPreset.MENU, OcrPreset.TOOLTIP, OcrPreset.SUBTITLE)


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


def _func_ast(func: Any) -> ast.FunctionDef:
    """Bir fonksiyonun AST'sini (docstring dahil) dondurur."""
    node = ast.parse(inspect.getsource(func)).body[0]
    assert isinstance(node, ast.FunctionDef)
    return node


def _seg_key(segments: list[Segment]) -> list[tuple[Any, ...]]:
    """BOLUMLEME kimligi -- K23'un korumayi zorunlu kildigi HER SEY
    (`speaker` HARIC): `source_blocks` dizisi, `text`, `bbox`,
    `placeholders` ve (dizinin uzunlugu olarak) segment SAYISI."""
    return [
        (
            s.source_blocks,
            s.text,
            (s.bbox.x, s.bbox.y, s.bbox.w, s.bbox.h, s.bbox.monitor_index, s.bbox.dpi_scale),
            s.placeholders,
        )
        for s in segments
    ]


# ===========================================================================
# 1. K23 -- IKI-GECISLI YAPININ AST ILE YAPISAL ISPATI
#    (env.md: "iki-gecis gercekten kodda var mi? Bolumleme gecisinin
#    HICBIR noktasinda `speaker` mutasyonu olmadigini AST veya kod
#    okumasiyla goster. Goruntu gecisinin ciktisinin bolumleme kararlarina
#    GERI BESLENMEDIGINI yapisal olarak kanitla.")
# ===========================================================================


def _group_parts() -> tuple[ast.FunctionDef, ast.For, ast.If]:
    """`_group`in AST'si + bolumleme (for) ve goruntu (if apply_inheritance)
    gecislerinin dugumleri. Ikisinin de TEK olmasi ispatin parcasidir."""
    fn = _func_ast(normalizer_mod._group)
    loops = [s for s in fn.body if isinstance(s, ast.For)]
    assert len(loops) == 1, f"_group govdesinde TEK bir ust-duzey dongu beklenir, {len(loops)} var"
    flag_ifs = [
        s
        for s in fn.body
        if isinstance(s, ast.If) and isinstance(s.test, ast.Name) and s.test.id == "apply_inheritance"
    ]
    assert len(flag_ifs) == 1, (
        "goruntu gecisi TEK bir `if apply_inheritance:` blogu olmali, "
        f"{len(flag_ifs)} bulundu -- iki-gecisli yapi bozulmus"
    )
    return fn, loops[0], flag_ifs[0]


def test_r5_k23_group_gercekten_iki_gecisten_olusuyor() -> None:
    """YAPISAL: `_group` = (1) TEK bolumleme dongusu, ardindan (2) TEK
    `if apply_inheritance:` goruntu passi, ardindan `return groups`.
    Goruntu passi dongudEN SONRA gelmek ZORUNDA -- aksi halde "bolumleme
    bittikten sonra" iddiasi (K23) yapisal olarak dogru olmazdi."""
    fn, loop, flag_if = _group_parts()
    body_index = {id(st): i for i, st in enumerate(fn.body)}
    assert body_index[id(loop)] < body_index[id(flag_if)], "goruntu passi bolumleme dongusunden ONCE"

    # goruntu passinden SONRA yalniz `return groups` kalir -- baska hicbir
    # islem (yeniden gruplama, yeniden sıralama, yeni birlesim) yok.
    after = fn.body[body_index[id(flag_if)] + 1 :]
    assert len(after) == 1 and isinstance(after[0], ast.Return), [ast.unparse(s) for s in after]
    assert ast.unparse(after[0]) == "return groups"


def test_r5_k23_bolumleme_gecisinde_hicbir_speaker_mutasyonu_yok() -> None:
    """K23'un CEKIRDEK yapisal iddiasi: bolumleme gecisi (`for` dongusu)
    BOYUNCA hicbir ogenin `speaker` alani MUTE EDILMEZ.

    Kontroller (dongu govdesi icinde):
      - HIC `replace(...)` cagrisi YOK (tur 4'un `replace(nxt,
        speaker=...)` satiri dongudEN COKARILMIS olmali),
      - `speaker=` anahtar kelimesi YALNIZCA `_Item(...)` insasinda ve
        DEGERI `current.speaker` (K15'in "birlesen grubun speaker'i
        soldaki ogenin speaker'idir" kurali -- ogenin KENDI OZGUN degeri,
        MIRASLA UYDURULMUS bir deger DEGIL),
      - `.speaker`a hicbir ATAMA yok (frozen dataclass olsa da yapisal
        olarak da sabitlenir),
      - `apply_inheritance` dongu ICINDE HIC OKUNMAZ."""
    _fn, loop, _flag_if = _group_parts()

    replaces = [
        n
        for n in ast.walk(loop)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "replace"
    ]
    assert replaces == [], (
        "bolumleme gecisinde `replace(...)` var -- tur 4'un mutasyonu geri gelmis: "
        f"{[ast.unparse(n) for n in replaces]}"
    )

    speaker_kwargs = [n for n in ast.walk(loop) if isinstance(n, ast.keyword) and n.arg == "speaker"]
    assert len(speaker_kwargs) == 1, [ast.unparse(k.value) for k in speaker_kwargs]
    assert ast.unparse(speaker_kwargs[0].value) == "current.speaker", ast.unparse(speaker_kwargs[0].value)

    # `speaker=` YALNIZCA `_Item(...)` insasinda kullanilmis olmali
    item_calls = [
        n
        for n in ast.walk(loop)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "_Item"
    ]
    assert len(item_calls) == 1
    assert any(k.arg == "speaker" for k in item_calls[0].keywords)

    # hicbir yerde `<sey>.speaker = ...` atamasi yok
    for node in ast.walk(loop):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                assert not (
                    isinstance(target, ast.Attribute) and target.attr == "speaker"
                ), ast.unparse(node)

    flag_names = [n for n in ast.walk(loop) if isinstance(n, ast.Name) and n.id == "apply_inheritance"]
    assert flag_names == [], "bolumleme gecisi `apply_inheritance` bayragini OKUYOR -- K23 yapisi kirik"


def test_r5_k23_apply_inheritance_tam_olarak_tek_bir_yerde_okunur() -> None:
    """`apply_inheritance` `_group` icinde TAM OLARAK BIR KEZ okunur ve o
    yer goruntu passinin `if` KOSULUDUR. Boylece "bayrak bolumlemeyi
    etkileyemez" iddiasi TEK bir noktaya indirgenir ve o nokta denetlenir."""
    fn, _loop, flag_if = _group_parts()
    reads = [n for n in ast.walk(fn) if isinstance(n, ast.Name) and n.id == "apply_inheritance"]
    assert len(reads) == 1, f"{len(reads)} okuma var: {[n.lineno for n in reads]}"
    assert reads[0] is flag_if.test


def test_r5_k23_goruntu_gecisi_yalnizca_speaker_gunceller() -> None:
    """Goruntu gecisi (`if apply_inheritance:` blogu) YALNIZCA `speaker`
    alanini gunceller: tek bir `replace(...)` cagrisi, TEK anahtar kelime
    (`speaker`), ve `text`/`bbox`/`source_blocks`/`placeholders`
    anahtarlarinin HICBIRI GECMEZ."""
    _fn, _loop, flag_if = _group_parts()
    replaces = [
        n
        for n in ast.walk(flag_if)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "replace"
    ]
    assert len(replaces) == 1, [ast.unparse(n) for n in replaces]
    kwargs = {k.arg for k in replaces[0].keywords}
    assert kwargs == {"speaker"}, kwargs
    for yasak in ("text", "bbox", "source_blocks", "placeholders"):
        assert yasak not in kwargs


def test_r5_k23_goruntu_gecisi_hicbir_gruplama_kararina_geri_beslenmez() -> None:
    """K23'un IKINCI yapisal iddiasi: goruntu gecisinin CIKTISI bolumleme
    kararlarina GERI BESLENMEZ.

    Yapisal ispat (goruntu passinin ICI):
      - gruplama KARARI veren/uygulayan hicbir cagri YOK
        (`_group_rejection_reason`, `_should_group`, `_union_rect`,
        `_Item`, `_group`),
      - dongunun durum degiskenlerine (`current`, `tail`,
        `pure_length_boundaries`) hicbir ATAMA yok,
      - `groups` listesinin UZUNLUGU degismez: `append`/`insert`/`pop`/
        `extend`/`remove` YOK (yalniz `groups[i] = ...` yerinde guncelleme),
    ve (yukaridaki testle birlikte) pass dongudEN SONRA gelir, ardindan
    yalniz `return groups` vardir -- yani uretilen `speaker` degerinin
    tekrar bir gruplama kararina girebilecegi bir YOL YOKTUR."""
    _fn, _loop, flag_if = _group_parts()

    yasak_cagrilar = {"_group_rejection_reason", "_should_group", "_union_rect", "_Item", "_group"}
    for node in ast.walk(flag_if):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in yasak_cagrilar, ast.unparse(node)
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in ("append", "insert", "pop", "extend", "remove"), ast.unparse(
                    node
                )

    for node in ast.walk(flag_if):
        if isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for t in targets:
                if isinstance(t, ast.Name):
                    assert t.id not in ("current", "tail", "pure_length_boundaries", "groups"), ast.unparse(
                        node
                    )


def test_r5_k23_normalize_impl_bayragi_yalniz_group_cagrisina_iletir() -> None:
    """`_normalize_impl` icinde `apply_inheritance` YALNIZCA `_group(...)`
    cagrisina anahtar kelime olarak gecirilir -- boru hattinin diger BES
    adiminin (esik, gurultu, birlestirme, konusmaci, yer tutucu) hicbiri
    bayragi GORMEZ. Yani bayrak sadece adim 5'in GORUNUM passini acar."""
    fn = _func_ast(normalizer_mod._normalize_impl)
    reads = [n for n in ast.walk(fn) if isinstance(n, ast.Name) and n.id == "apply_inheritance"]
    assert len(reads) == 1, [n.lineno for n in reads]

    group_calls = [
        n
        for n in ast.walk(fn)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "_group"
    ]
    assert len(group_calls) == 1
    kw = {k.arg: ast.unparse(k.value) for k in group_calls[0].keywords}
    # TUR 6'DA YENIDEN NISANLANDI (K28): cagri artik `blocks=blocks` DE tasir.
    # Tur 5 beklentisi (`kw == {"apply_inheritance": ...}`) sefin kararinda
    # ONCEDEN adlandirilmis KACINILMAZ bayatlamadir (sef_karari-tur6.md,
    # "Tester-B'ye ve Tester-A'ya not"). Beklenti GEVSETILMEDI, GENISLETILDI:
    # iki anahtar kelimenin de ADI ve DEGERI birebir pinlenir.
    assert kw == {"blocks": "blocks", "apply_inheritance": "apply_inheritance"}, kw


def test_r5_k23_normalize_gercekten_miras_ACIK_yola_delege_ediyor() -> None:
    """K23 denetim ZINCIRININ eksik halkasi: yukaridaki BUTUN K23 kanitlari
    `_normalize_impl` uzerinden olculuyor. Ama URUNUN cagirdigi fonksiyon
    `normalize`. Sef karari (env.md TUR 5, K23 satiri): "`normalize` buna
    SABIT `True` ile delege eder". Bu test o halkayi kapatir:

      (a) YAPISAL -- `normalize` govdesi TEK satir: `return
          _normalize_impl(blocks, preset)`; baska hicbir islem YOK,
      (b) `_normalize_impl`'in `apply_inheritance` VARSAYILANI `True`
          (delegasyon anahtar kelimeyi GECMEDIGI icin urun davranisi TAM
          OLARAK bu varsayilana bagli -- varsayilan `False`'a cevrilse
          `normalize` SESSIZCE mirasi kaybederdi),
      (c) DAVRANIS -- `normalize(b, p)` ciktisi `_normalize_impl(b, p,
          apply_inheritance=True)` ile BIREBIR AYNI (dort on ayar),
      (d) ve bu esitlik BOS degil: en az bir senaryoda `apply_inheritance=
          False` ciktisindan `speaker` alaninda GERCEKTEN ayrisiyor --
          yani `normalize` mirasin ACIK oldugu yolu KULLANIYOR."""
    fn = _func_ast(normalize)
    assert isinstance(fn.body[0], ast.Expr)  # docstring
    govde = fn.body[1:]
    assert len(govde) == 1 and isinstance(govde[0], ast.Return), [ast.unparse(s) for s in govde]
    assert ast.unparse(govde[0]) == "return _normalize_impl(blocks, preset)"
    assert inspect.signature(normalizer_mod._normalize_impl).parameters["apply_inheritance"].default is True

    cap = get_params(OcrPreset.DIALOGUE).max_group_chars
    senaryolar: list[list[TextBlock]] = [
        [blk("Ada:", 10, 0)] + [blk("z" * 140, 10, 22 + i * 22) for i in range(5)],
        [blk("Ada:", 10, 0, h=12), blk("a" * (cap - 30), 10, 14), blk("b" * 60, 10, 36)],
        [blk("勇者：" + "あ" * 150, 10, 0), blk("い" * 150, 10, 22)],
        [],
    ]
    ayrisan = 0
    for blocks in senaryolar:
        for preset in ALL_PRESETS:
            acik = _normalize_impl(blocks, preset, apply_inheritance=True)
            assert normalize(blocks, preset) == acik, (preset.value, blocks)
            kapali = _normalize_impl(blocks, preset, apply_inheritance=False)
            if [s.speaker for s in acik] != [s.speaker for s in kapali]:
                ayrisan += 1
    assert ayrisan > 0, "hicbir senaryoda miras devreye girmedi -- (c) esitligi BOS bir iddia"


def test_r5_k23_normalize_impl_genel_apiye_sizmiyor() -> None:
    """Test kancasi GENEL API'ye SIZMAYACAK (sef_karari-tur5.md, K23):
    `__all__` yalniz `normalize`; `normalize`in imzasi (2 parametre)
    DEGISMEDI; `_normalize_impl` alt cizgi ile baslar (private)."""
    assert normalizer_mod.__all__ == ("normalize",)
    sig = inspect.signature(normalize)
    assert list(sig.parameters) == ["blocks", "preset"]
    assert "apply_inheritance" not in sig.parameters
    impl_sig = inspect.signature(normalizer_mod._normalize_impl)
    assert impl_sig.parameters["apply_inheritance"].kind is inspect.Parameter.KEYWORD_ONLY
    assert impl_sig.parameters["apply_inheritance"].default is True


# ===========================================================================
# 2. K23 -- MAKINE DENETIMI, KENDI ureticimle (implementer'in 2500 girdilik
#    denetimine GUVENMEDEN: farkli tohum, farkli geometri dagilimi).
# ===========================================================================


_NAMES = ("Ada", "Efe", "Zoe", "勇者", "魔王", "村人")
_SEPS = (":", "：")


def _gen_karisik(rng: random.Random) -> list[TextBlock]:
    """GENIS dagilim: yozlasmis geometri, ayni-y yan yana bloklar, cok
    kucuk `h`, esik-alti bloklar, CJK/fullwidth etiketler, gurultu."""
    n = rng.randint(1, 14)
    blocks: list[TextBlock] = []
    y = rng.randint(-40, 40)
    for _ in range(n):
        r = rng.random()
        if r < 0.28:
            text = rng.choice(_NAMES) + rng.choice(_SEPS)
            if rng.random() < 0.5:
                text += " " + "m" * rng.randint(3, 90)
        elif r < 0.36:
            text = rng.choice(["?", "！", "力", "  ", "", "a-", "well-known", "{0} ve %s", "50%"])
        else:
            text = rng.choice("xyz") * rng.randint(5, 120)
        h = rng.choice([0, -8, 1, 2, 12, 20, 60, 140])
        w = rng.choice([0, -5, 3, 40, 200, 400])
        x = rng.choice([0, 0, 5, 300, 1000])
        conf = rng.choice([0.0, 0.5, 0.55, 0.6, 0.65, 0.9, 1.0])
        blocks.append(TextBlock(text=text, bbox=Rect(x=x, y=y, w=w, h=h), confidence=conf))
        y += rng.choice([0, 0, 1, 14, 22, 30, 120, 500])
    return blocks


def _gen_monolog(rng: random.Random) -> list[TextBlock]:
    """SIKI geometri + UZUN govde: uzunluk-kaynakli bolunme (yani mirasin
    GERCEKTEN tetiklendigi durum) SIK, geometrik kopus SEYREK. Bu uretici
    K23 denetimini BOS bir dogrulama olmaktan cikarir -- miras hic
    tetiklenmezse "acik/kapali ayni" iddiasi hicbir sey kanitlamaz."""
    blocks: list[TextBlock] = []
    y = 0
    h = 20
    for _ in range(rng.randint(3, 16)):
        r = rng.random()
        if r < 0.18:
            text = rng.choice(_NAMES) + rng.choice(_SEPS)
        elif r < 0.26:
            text = rng.choice(_NAMES) + rng.choice(_SEPS) + " " + "g" * rng.randint(20, 80)
        else:
            text = rng.choice("xyzw") * rng.randint(40, 110)
        blocks.append(TextBlock(text=text, bbox=Rect(x=0, y=y, w=300, h=h), confidence=0.95))
        y += rng.choices([22, 22, 22, 24, 300], weights=[50, 20, 10, 10, 10])[0]
        h = rng.choice([0, -6, 1]) if rng.random() < 0.08 else 20
    return blocks


def test_r5_k23_bolumleme_degismezi_kendi_karisik_ureticimle() -> None:
    """K23 DEGISMEZI: 900 girdi x 4 on ayar = 3600 kosum. Miras ACIK ve
    KAPALI ciktilarin `source_blocks` dizisi, `text`, `bbox`,
    `placeholders` ve segment SAYISI BIREBIR ayni olmali; TEK fark
    `speaker` olabilir VE fark YALNIZCA `None -> deger` yonunde olabilir
    (miras bir degeri SILEMEZ ya da DEGISTIREMEZ)."""
    rng = random.Random(987654321)
    kosum = 0
    for _ in range(900):
        blocks = _gen_karisik(rng)
        for preset in ALL_PRESETS:
            kosum += 1
            acik = _normalize_impl(blocks, preset, apply_inheritance=True)
            kapali = _normalize_impl(blocks, preset, apply_inheritance=False)
            assert _seg_key(acik) == _seg_key(kapali), (
                f"K23 IHLALI (preset={preset.value}): bolumleme miras acik/kapali FARKLI\n"
                f"  acik  : {_seg_key(acik)}\n  kapali: {_seg_key(kapali)}"
            )
            for s_acik, s_kapali in zip(acik, kapali):
                if s_kapali.speaker is not None:
                    assert s_acik.speaker == s_kapali.speaker
    assert kosum == 3600


def test_r5_k23_bolumleme_degismezi_monolog_ureticiyle_ve_bos_degil() -> None:
    """AYNI degismez, mirasi SIK tetikleyen ikinci ureticiyle (600 girdi x
    4 on ayar = 2400 kosum) -- VE denetimin BOS olmadigi kanitlanir: en az
    yuzlerce kosumda miras GERCEKTEN gozlenir, bir kisminda BIRDEN FAZLA
    noktada (zincirleme)."""
    rng = random.Random(1337)
    kosum = 0
    miras_gozlenen = 0
    zincir_gozlenen = 0
    for _ in range(600):
        blocks = _gen_monolog(rng)
        for preset in ALL_PRESETS:
            kosum += 1
            acik = _normalize_impl(blocks, preset, apply_inheritance=True)
            kapali = _normalize_impl(blocks, preset, apply_inheritance=False)
            assert _seg_key(acik) == _seg_key(kapali), (
                f"K23 IHLALI (preset={preset.value})\n  acik  : {_seg_key(acik)}\n"
                f"  kapali: {_seg_key(kapali)}"
            )
            farkli = [
                (a.speaker, b.speaker) for a, b in zip(acik, kapali) if a.speaker != b.speaker
            ]
            for yeni, eski in farkli:
                assert eski is None and yeni is not None, (yeni, eski)
            if farkli:
                miras_gozlenen += 1
            if len(farkli) >= 2:
                zincir_gozlenen += 1
    assert kosum == 2400
    assert miras_gozlenen > 200, f"miras neredeyse hic tetiklenmedi ({miras_gozlenen}) -- denetim BOS"
    assert zincir_gozlenen > 20, f"zincirleme miras hic gozlenmedi ({zincir_gozlenen})"


def test_r5_k23_b1_senaryosu_kendi_etiketli_kuyruk_yapismiyor() -> None:
    """B1 (sef_karari-tur5.md, `yuksek`): etiketli uzun govde + KENDI
    etiketiyle gelen UCUNCU blok. Tur 4'te ucuncu blok, ikincinin MIRAS
    aldigi `speaker` ile eslesip onun KUYRUGUNA YAPISIYORDU (X/X'e
    dusuyordu). Artik AYRI kalmali (VARYANT B)."""
    cap = get_params(OcrPreset.DIALOGUE).max_group_chars
    blocks = [
        blk("Ada:", 10, 0, h=12),
        blk("a" * (cap - 30), 10, 14),
        blk("b" * 60, 10, 36),
        blk("Ada: " + "c" * 60, 10, 58),
    ]
    out = normalize(blocks, OcrPreset.DIALOGUE)
    src = [s.source_blocks for s in out]
    assert (2, 3) not in src, f"b2 ve b3 BIRLESTI (VARYANT A geri geldi): {src}"
    assert src == [(0, 1), (2,), (3,)], src
    assert [s.speaker for s in out] == ["Ada", "Ada", "Ada"]
    # ve bolumleme miras kapaliyken de AYNI
    kapali = _normalize_impl(blocks, OcrPreset.DIALOGUE, apply_inheritance=False)
    assert [s.source_blocks for s in kapali] == src
    # miras KAPALI: ortadaki grup `None` KALIR (miras uygulanmadi), digerleri
    # KENDI etiketlerini tasir -- yani fark YALNIZCA `speaker` alaninda.
    assert [s.speaker for s in kapali] == ["Ada", None, "Ada"]


def test_r5_k23_b1_japonca_uc_konusmaci_zinciri() -> None:
    """B1'in Japonca hali (env.md TUR 5 / C merceginin de bakis noktasi,
    KARAR UYUMU acisindan: K23 degismezi DILDEN BAGIMSIZ olmali).
    `勇者：` etiketli uzun replik + hemen ardindan YENI `勇者：` replik +
    `魔王：` + `村人：` -- dort sozce DORT ayri segment kalmali."""
    blocks = [
        blk("勇者：" + "あ" * 150, 10, 0),
        blk("い" * 150, 10, 22),
        blk("勇者：" + "う" * 100, 10, 44),
        blk("魔王：" + "え" * 100, 10, 66),
        blk("村人：" + "お" * 100, 10, 88),
    ]
    out = normalize(blocks, OcrPreset.DIALOGUE)
    assert [s.source_blocks for s in out] == [(0,), (1,), (2,), (3,), (4,)]
    assert [s.speaker for s in out] == ["勇者", "勇者", "勇者", "魔王", "村人"]
    # miras (blok 1) OZGUN string'in KENDISI -- normalize edilmis bir kopya DEGIL
    assert out[1].speaker == "勇者"
    assert out[1].speaker is out[0].speaker
    acik = _normalize_impl(blocks, OcrPreset.DIALOGUE, apply_inheritance=True)
    kapali = _normalize_impl(blocks, OcrPreset.DIALOGUE, apply_inheritance=False)
    assert _seg_key(acik) == _seg_key(kapali)


def test_r5_k23_zincirleme_miras_ve_geometrik_kopusta_kesilme() -> None:
    """Zincirleme miras (env.md TUR 5: "gecisken miras, miras zincirinin
    geometrik kopusta kesilmesi"):
      - UC ardisik uzunluk-bolunmesi -> zincir BOYUNCA miras (hepsi 'Ada'),
      - ARAYA GERCEK geometrik kopus girdiginde zincir KESILIR ve kopustan
        SONRAKI hicbir grup miras ALMAZ (`None` kalir) -- K19'un
        "geometrik bosluk -> `None` KALIR, atfetmek spekulasyondur"
        satirinin zincir uzerindeki dogal sonucu."""
    blocks = [blk("Ada:", 10, 0)] + [blk("z" * 140, 10, 22 + i * 22) for i in range(6)]
    out = normalize(blocks, OcrPreset.DIALOGUE)
    assert len(out) == 6
    assert all(s.speaker == "Ada" for s in out), [s.speaker for s in out]

    kopuslu = [blk("Ada:", 10, 0)]
    y = 22
    for _ in range(3):
        kopuslu.append(blk("z" * 140, 10, y))
        y += 22
    y += 400  # GERCEK geometrik kopus
    for _ in range(3):
        kopuslu.append(blk("q" * 140, 10, y))
        y += 22
    out2 = normalize(kopuslu, OcrPreset.DIALOGUE)
    speakers = [s.speaker for s in out2]
    assert speakers[:3] == ["Ada", "Ada", "Ada"], speakers
    assert all(sp is None for sp in speakers[3:]), speakers
    assert _seg_key(_normalize_impl(kopuslu, OcrPreset.DIALOGUE, apply_inheritance=True)) == _seg_key(
        _normalize_impl(kopuslu, OcrPreset.DIALOGUE, apply_inheritance=False)
    )


def test_r5_k23_ayni_y_yanyana_ve_cok_kucuk_h_bolumleme_ayni() -> None:
    """env.md'nin isaret ettigi ozel geometriler: ayni `y`'de YAN YANA
    bloklar, `h` cok kucuk bloklar, ic ice uzunluk+geometri bolunmeleri --
    hepsinde K23 degismezi."""
    senaryolar: list[list[TextBlock]] = [
        # ayni y'de yan yana (okuma sirasi x'e gore)
        [blk("Ada:", 0, 0), blk("x" * 150, 0, 20), blk("y" * 150, 400, 20), blk("z" * 150, 800, 20)],
        # h=1 (cok kucuk) -- gruplama esikleri carpma ile
        [blk("Ada:", 0, 0, h=1), blk("x" * 150, 0, 1, h=1), blk("y" * 150, 0, 2, h=1)],
        # ic ice: uzunluk bolunmesi + hemen ardindan yozlasmis h
        [blk("Ada:", 0, 0), blk("x" * 160, 0, 22), blk("y" * 160, 0, 44), blk("z" * 40, 0, 66, h=0)],
    ]
    for i, blocks in enumerate(senaryolar):
        for preset in ALL_PRESETS:
            acik = _normalize_impl(blocks, preset, apply_inheritance=True)
            kapali = _normalize_impl(blocks, preset, apply_inheritance=False)
            assert _seg_key(acik) == _seg_key(kapali), (i, preset.value)


# ===========================================================================
# 3. K24 -- miras-uygunluk sorgusunun SOL TARAFI `tail` MI?
# ===========================================================================


def test_r5_k24_ignore_length_sorgusu_tail_ile_cagriliyor_ast() -> None:
    """K24 + K28: `ignore_length=True` ile yapilan IKINCI (miras-uygunluk)
    cagrinin SOL tarafi `tail`den turemeli -- `current`den DEGIL. Ana
    birlestirme kararinin HALA `current` kullandigi da ayrica sabitlenir
    (K24/K28 kapsam cumlesi).

    TUR 6'DA YENIDEN NISANLANDI (sef_karari-tur6.md, K28): sorgu artik
    `_group_rejection_reason(*_raw_query_pair(tail, nxt, blocks), params,
    ignore_length=True)` bicimindedir. Tur 5'in `args[0] == "tail"`
    beklentisi sefin §4.6/5 listesinde ONCEDEN adlandirilmis KACINILMAZ bir
    bayatlamaydi. Yeni beklenti daha SIKIDIR: yildizli cagrinin adi,
    argumanlarinin SIRASI (`tail, nxt, blocks`) ve tam metin birlikte
    pinlenir -- `current`, `nxt`/`tail` takasi ya da `blocks` yerine baska
    bir ad yazan bir uygulama burada kirilir."""
    fn = _func_ast(normalizer_mod._group)
    cagrilar = [
        n
        for n in ast.walk(fn)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "_group_rejection_reason"
    ]
    assert len(cagrilar) == 2, [ast.unparse(c) for c in cagrilar]

    ignore_true = [c for c in cagrilar if any(k.arg == "ignore_length" for k in c.keywords)]
    assert len(ignore_true) == 1
    miras_sorgusu = ignore_true[0]
    # TUR 6'DA YENIDEN NISANLANDI (K28): sorgunun IKI tarafi da artik
    # `_raw_query_pair(tail, nxt, blocks)` ile OZGUN bloklardan turetiliyor,
    # yani ILK POZISYONEL arguman `tail` ADI DEGIL, YILDIZLI bir cagri.
    # `tail` KIMLIGI KAYBOLMADI -- `_raw_query_pair`'in ILK argumani olarak
    # AYNI SIKILIKTA pinlenir (`current` yazan bir uygulama burada kirilir).
    assert isinstance(miras_sorgusu.args[0], ast.Starred), ast.unparse(miras_sorgusu)
    yildizli = miras_sorgusu.args[0].value
    assert isinstance(yildizli, ast.Call) and isinstance(yildizli.func, ast.Name)
    assert yildizli.func.id == "_raw_query_pair"
    assert [ast.unparse(a) for a in yildizli.args] == ["tail", "nxt", "blocks"], ast.unparse(yildizli)
    assert not yildizli.keywords
    assert len(miras_sorgusu.args) == 2 and ast.unparse(miras_sorgusu.args[1]) == "params"
    assert ast.unparse(miras_sorgusu) == (
        "_group_rejection_reason(*_raw_query_pair(tail, nxt, blocks), params, ignore_length=True)"
    )

    ana_karar = [c for c in cagrilar if c is not miras_sorgusu][0]
    assert ast.unparse(ana_karar) == "_group_rejection_reason(current, nxt, params)"


def test_r5_k24_tail_grubun_son_ham_ogesi_olarak_tutuluyor_ast() -> None:
    """`tail` "grubun okuma sirasindaki SON HAM ogesi" tanimini yapisal
    olarak karsiliyor mu: dongudEN ONCE `items[0]` ile kurulur, dongu
    icinde SADECE `nxt` (HAM oge) atanir -- birlesik/birikmis bir ifade
    (`_Item(...)`, `current`) ASLA atanmaz."""
    fn = _func_ast(normalizer_mod._group)
    atamalar = [
        node
        for node in ast.walk(fn)
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "tail" for t in node.targets)
    ]
    degerler = [ast.unparse(node.value) for node in atamalar]
    assert degerler.count("items[0]") == 1, degerler
    assert set(degerler) == {"items[0]", "nxt"}, degerler
    assert len(degerler) == 3, degerler  # kurulum + basarili birlesim + yeni grup


def test_r5_k24_tail_ile_current_zit_sonuc_verir_kendi_geometrim() -> None:
    """K24'un zorunlu testi, KENDI geometrimle: grubun BASINDAKI oge
    sonrakilerden cok daha AŞAĞI uzaniyor (birlesik `bbox`in `bottom`unu
    O tasiyor). Ayni cift icin:
      - `current` (birlesik) ile `ignore_length=True` sorgusu YANLISLIKLA
        `None` doner ("kopus yok" -- negatif/kucuk gap artifakti),
      - `tail` (grubun SON HAM ogesi) ile AYNI sorgu DOGRU sekilde `"gap"`
        doner (GERCEK satir-arasi bosluk gorunur)."""
    params = get_params(OcrPreset.DIALOGUE)
    uzun_a = "A" * 150
    uzun_b = "B" * 120
    uzun_c = "C" * 120

    i0 = _Item(uzun_a, Rect(0, 0, 200, 120), "Ada", (0,))  # bottom=120 -- EN ALTA uzanan
    i1 = _Item(uzun_b, Rect(0, 10, 200, 12), None, (1,))  # bottom=22
    assert _group_rejection_reason(i0, i1, params) is None  # gercekten birlesirler

    current = _Item(uzun_a + " " + uzun_b, Rect(0, 0, 200, 120), "Ada", (0, 1))
    tail = i1
    i2 = _Item(uzun_c, Rect(0, 60, 200, 12), None, (2,))

    assert _group_rejection_reason(current, i2, params) == "length"
    assert _group_rejection_reason(current, i2, params, ignore_length=True) is None  # ARTIFAKT
    assert _group_rejection_reason(tail, i2, params, ignore_length=True) == "gap"  # GERCEK


def test_r5_k24_normalize_uzerinden_yanlis_miras_onlenir_kendi_geometrim() -> None:
    """AYNI ayrim, UCTAN UCA `normalize()` uzerinden: kuyruk segment
    `speaker=None` KALMALI (tail-temelli kontrol gercek kopusu gorur).
    `current`-temelli (tur 4) kontrol burada YANLISLIKLA miras verirdi."""
    blocks = [
        blk("Ada:", 0, -30, h=12),
        blk("A" * 150, 0, 0, w=200, h=120),
        blk("B" * 120, 0, 10, w=200, h=12),
        blk("C" * 120, 0, 60, w=200, h=12),
    ]
    out = normalize(blocks, OcrPreset.DIALOGUE)
    assert [s.source_blocks for s in out] == [(0, 1, 2), (3,)], [s.source_blocks for s in out]
    assert out[0].speaker == "Ada"
    assert out[1].speaker is None, "K24 IHLALI: birlesik-bbox artifakti yanlis miras verdi"


# ===========================================================================
# 4. YAPISAL AYRISMAZLIK -- `_should_group` <-> `_group_rejection_reason`,
#    `speaker`-once sirasi, reason kodlarinin tur 3-4 ile BIREBIRLIGI.
# ===========================================================================


def test_r5_should_group_hala_tek_satirlik_devretme() -> None:
    """Sef "bozmadan koru" listesi: `_should_group` govdesinin TEK
    SATIRLIK devretme deseni. Govde = docstring + TEK `return` ve o
    return TAM OLARAK `_group_rejection_reason(a, b, params) is None`
    (K25: `ignore_length` BURADA HIC gecirilmez, varsayilan kullanilir)."""
    fn = _func_ast(normalizer_mod._should_group)
    assert isinstance(fn.body[0], ast.Expr)  # docstring
    govde = fn.body[1:]
    assert len(govde) == 1 and isinstance(govde[0], ast.Return), [ast.unparse(s) for s in govde]
    assert ast.unparse(govde[0]) == "return _group_rejection_reason(a, b, params) is None"
    assert list(inspect.signature(_should_group).parameters) == ["a", "b", "params"]
    assert inspect.signature(_should_group).return_annotation == "bool"


def test_r5_should_group_reason_esdegerligi_fuzz_yeni_tohum() -> None:
    """Ayrismazligin DAVRANIS ispati (yeni tohum, tur 3'ten FARKLI):
    `_should_group(a,b,p)` HER ZAMAN `_group_rejection_reason(a,b,p) is
    None` ile ayni. 20.000 cift."""
    rng = random.Random(555_000_111)
    ciftler = 0
    reason_gorulen: dict[str | None, int] = {}
    for _ in range(5000):
        for preset in ALL_PRESETS:
            params = get_params(preset)
            a = _Item(
                rng.choice("ab") * rng.randint(1, 200),
                Rect(
                    rng.randint(-50, 500),
                    rng.randint(-50, 500),
                    rng.choice([-5, 0, 1, 50, 300]),
                    rng.choice([-5, 0, 1, 20, 100]),
                ),
                rng.choice([None, "Ada", "Efe"]),
                (0,),
            )
            b = _Item(
                rng.choice("cd") * rng.randint(1, 200),
                Rect(
                    rng.randint(-50, 500),
                    rng.randint(-50, 500),
                    rng.choice([-5, 0, 1, 50, 300]),
                    rng.choice([-5, 0, 1, 20, 100]),
                ),
                rng.choice([None, "Ada", "Efe"]),
                (1,),
            )
            reason = _group_rejection_reason(a, b, params)
            assert _should_group(a, b, params) is (reason is None)
            reason_gorulen[reason] = reason_gorulen.get(reason, 0) + 1
            ciftler += 1
    assert ciftler == 20000
    # ayrismazlik ispati BOS olmasin: hem None hem TUM reason kodlari gorulmus olmali
    assert set(reason_gorulen) == {None, "speaker", "length", "height", "gap", "width", "overlap"}, (
        reason_gorulen
    )


def test_r5_speaker_kontrolu_hala_lengthten_once() -> None:
    """Sef "bozmadan koru": `speaker` kontrolu `length`ten ONCE. Hem
    YAPISAL (return satir sirasi) hem DAVRANIS (X/Y cifti TEK BASINA
    capi asacak kadar uzun olsa bile reason `"speaker"`) olarak."""
    fn = _func_ast(normalizer_mod._group_rejection_reason)
    satir = {
        node.value.value: node.lineno
        for node in ast.walk(fn)
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Constant) and node.value.value
    }
    assert satir["speaker"] < satir["length"] < satir["height"] < satir["gap"] < satir["width"] < satir[
        "overlap"
    ], satir

    params = get_params(OcrPreset.DIALOGUE)
    uzun = "x" * (params.max_group_chars + 50)
    a = _Item(uzun, Rect(0, 0, 100, 20), "Ada", (0,))
    b = _Item(uzun, Rect(0, 20, 100, 20), "Efe", (1,))
    assert _group_rejection_reason(a, b, params) == "speaker"
    # ve `ignore_length=True` bu sirayi DEGISTIRMEZ
    assert _group_rejection_reason(a, b, params, ignore_length=True) == "speaker"


def test_r5_reason_kodlari_tur3_4_ile_birebir_ayni() -> None:
    """Reason kodlari (`ignore_length` VERILMEDEN) tur 3-4 ile BIREBIR
    ayni mi -- KENDI orneklemim, tur 3 dosyasindaki kurulumdan BAGIMSIZ
    (farkli geometri/metin, ayni beklenen kod). Alti kodun ALTISI da
    uretilebilir olmali; kod KUMESI de tam olarak bu alti + `None`."""
    params = get_params(OcrPreset.DIALOGUE)
    ornekler: list[tuple[str, _Item, _Item]] = [
        (
            "speaker",
            _Item("kisa", Rect(5, 5, 120, 18), "Zoe", (0,)),
            _Item("kisa", Rect(5, 25, 120, 18), "Ada", (1,)),
        ),
        (
            "length",
            _Item("p" * (params.max_group_chars - 10), Rect(5, 5, 120, 18), None, (0,)),
            _Item("q" * 30, Rect(5, 25, 120, 18), None, (1,)),
        ),
        (
            "height",
            _Item("kisa", Rect(5, 5, 120, -3), None, (0,)),
            _Item("kisa", Rect(5, 5, 120, 18), None, (1,)),
        ),
        (
            "gap",
            _Item("kisa", Rect(5, 5, 120, 18), None, (0,)),
            _Item("kisa", Rect(5, 900, 120, 18), None, (1,)),
        ),
        (
            "width",
            _Item("kisa", Rect(5, 5, -2, 18), None, (0,)),
            _Item("kisa", Rect(5, 24, -2, 18), None, (1,)),
        ),
        (
            "overlap",
            _Item("kisa", Rect(5, 5, 20, 18), None, (0,)),
            _Item("kisa", Rect(9000, 24, 20, 18), None, (1,)),
        ),
        (
            None,
            _Item("kisa", Rect(5, 5, 120, 18), "Ada", (0,)),
            _Item("kisa", Rect(5, 24, 120, 18), None, (1,)),
        ),
    ]
    for beklenen, a, b in ornekler:
        assert _group_rejection_reason(a, b, params) == beklenen, (beklenen, a, b)

    # Kodun DONDURDUGU deger kumesi: tam olarak alti string + None
    fn = _func_ast(normalizer_mod._group_rejection_reason)
    donenler = {
        node.value.value if isinstance(node.value, ast.Constant) else "<ifade>"
        for node in ast.walk(fn)
        if isinstance(node, ast.Return)
    }
    assert donenler == {"speaker", "length", "height", "gap", "width", "overlap", None}, donenler


# ===========================================================================
# 5. K25 -- SECENEK 1 zorunlu: `ignore_length` parametresi, donus tipi
#    `str | None`, tur 3'un string-karsilastirmali assertion'lari saglam.
# ===========================================================================


def test_r5_k25_secenek1_imza_ve_donus_tipi_korunmus() -> None:
    """K25: secenek 1 (`ignore_length` parametresi) ZORUNLU; secenek 2
    (tum sebeplerin KUMESINI dondurmek) donus tipini degistirip mevcut
    tester assertion'larini kirardi. Denetim: parametre KEYWORD-ONLY ve
    varsayilani `False`; donus ANOTASYONU `str | None`; CALISMA ZAMANINDA
    donen deger `str` ya da `None` (KUME/LISTE/FROZENSET DEGIL)."""
    sig = inspect.signature(_group_rejection_reason)
    p = sig.parameters["ignore_length"]
    assert p.kind is inspect.Parameter.KEYWORD_ONLY
    assert p.default is False
    assert p.annotation == "bool"
    assert sig.return_annotation == "str | None"

    fn = _func_ast(normalizer_mod._group_rejection_reason)
    assert fn.returns is not None and ast.unparse(fn.returns) == "str | None"

    params = get_params(OcrPreset.DIALOGUE)
    a = _Item("x" * 200, Rect(0, 0, 100, 20), "Ada", (0,))
    b = _Item("y" * 200, Rect(0, 20, 100, 20), None, (1,))
    reason = _group_rejection_reason(a, b, params)
    assert isinstance(reason, str) and not isinstance(reason, (set, frozenset, list, tuple))
    assert reason == "length"  # STRING karsilastirmasi HALA gecerli (K25'in korudugu taban)


def test_r5_k25_tur3_string_karsilastirmali_assertionlar_hala_gecerli() -> None:
    """K25'in gerekcesi: secenek 2, `tester_B/test_karar_uyumu_tur3.py`
    icindeki UC string-karsilastirmali assertion'i (h=0 -> "height",
    negatif h -> "height", w=0 -> "width") KIRARDI. O uc assertion'in
    KENDISI burada bir kez daha, dogrudan cagrilarak dogrulanir -- yani
    regresyon TABANI gercekten korunmus."""
    params = get_params(OcrPreset.DIALOGUE)
    a = _Item("a", Rect(0, 0, 100, 0), None, (0,))
    b = _Item("b", Rect(0, 0, 100, 0), None, (1,))
    assert _group_rejection_reason(a, b, params) == "height"

    a = _Item("a", Rect(0, -15, 100, 20), None, (0,))
    b = _Item("b", Rect(0, 0, 100, -10), None, (1,))
    assert _group_rejection_reason(a, b, params) == "height"

    a = _Item("a", Rect(0, 0, 0, 20), None, (0,))
    b = _Item("b", Rect(0, 20, 0, 20), None, (1,))
    assert _group_rejection_reason(a, b, params) == "width"


# ===========================================================================
# 6. K26 -- alti karakterin `unicodedata.decomposition` etiketleri.
# ===========================================================================


_K26_BEKLENEN: dict[int, tuple[str, str]] = {
    0xFE15: ("<vertical>", "!"),
    0xFE16: ("<vertical>", "?"),
    0xFE56: ("<small>", "?"),
    0xFE57: ("<small>", "!"),
    0xFF01: ("<wide>", "!"),
    0xFF1F: ("<wide>", "?"),
}


def test_r5_k26_bagimsiz_tarama_alti_karakteri_birebir_dogruluyor() -> None:
    """BAGIMSIZ tam Unicode taramasi (0x0-0x10FFFF): NFKC ile `?`/`!`ye
    acilan, ASCII HARIC codepoint'ler TAM OLARAK bu alti olmali."""
    bulunan = {
        cp
        for cp in range(0x110000)
        if chr(cp) not in ("?", "!") and unicodedata.normalize("NFKC", chr(cp)) in ("?", "!")
    }
    assert bulunan == set(_K26_BEKLENEN), (
        f"eksik={set(_K26_BEKLENEN) - bulunan} fazla={bulunan - set(_K26_BEKLENEN)}"
    )


@pytest.mark.parametrize("cp", sorted(_K26_BEKLENEN))
def test_r5_k26_altisi_da_uyumluluk_formu_ve_etiketi_dogru(cp: int) -> None:
    """K26 (sef_karari-tur5.md): ALTISI DA Unicode UYUMLULUK formudur --
    fark YALNIZCA ayristirma ETIKETIDIR. `unicodedata.decomposition`
    ciktisi `<etiket> XXXX` bicimindedir; `<...>` ile BASLAMASI zaten
    "uyumluluk (compatibility) ayristirmasi" demektir (kanonik
    ayristirmalarda etiket YOKTUR)."""
    etiket, hedef = _K26_BEKLENEN[cp]
    decomp = unicodedata.decomposition(chr(cp))
    assert decomp.startswith("<"), f"U+{cp:04X} uyumluluk formu DEGIL: {decomp!r}"
    assert decomp.split()[0] == etiket, decomp
    assert chr(int(decomp.split()[1], 16)) == hedef
    assert unicodedata.normalize("NFKC", chr(cp)) == hedef
    assert unicodedata.category(chr(cp)) == "Po"


def test_r5_k26_etiket_dagilimi_iki_iki_iki() -> None:
    """Etiket dagilimi: 2x `<wide>`, 2x `<small>`, 2x `<vertical>`."""
    dagilim: dict[str, int] = {}
    for cp in _K26_BEKLENEN:
        etiket = unicodedata.decomposition(chr(cp)).split()[0]
        dagilim[etiket] = dagilim.get(etiket, 0) + 1
    assert dagilim == {"<wide>": 2, "<small>": 2, "<vertical>": 2}, dagilim


def test_r5_k26_docstring_olgusal_ifadesi_olcumle_ortusuyor() -> None:
    """K26 SALT DOKUMANTASYON karari: docstring'in OLGUSAL ifadesi
    olcumle ORTUSMELI. K26 bolumu (a) ALTISININ DA uyumluluk formu
    OLDUGUNU soylemeli, (b) uc etiketi (`<wide>`/`<small>`/`<vertical>`)
    ANMALI, (c) K22'nin "dordu DIGER uyumluluk formu" ifadesini YANLIS
    olarak ISARETLEMELI (duzeltilmis olarak degil, HATA olarak anmali),
    (d) sayinin Python'un Unicode surumune BAGLI oldugunu belirtmeli."""
    doc = normalizer_mod.__doc__ or ""
    bas = doc.find("K26 (sef_karari-tur5.md")
    assert bas != -1, "K26 bolumu docstring'den kayip"
    bolum = doc[bas : bas + 3000]
    assert "TAMAMI" in bolum and "ALTISI DA" in bolum
    for etiket in ("<wide>", "<small>", "<vertical>"):
        assert etiket in bolum, etiket
    assert "YANLIS" in bolum, "K22'nin olgusal hatasi HATA olarak isaretlenmemis"
    assert "Unicode surumune" in bolum or "Unicode 15.0.0" in bolum
    # olculen surum, docstring'in bildirdigi surumle ayni mi (bayatlama sondasi)
    if "Unicode 15.0.0" in bolum:
        assert unicodedata.unidata_version == "15.0.0", (
            f"docstring Unicode 15.0.0 diyor, ortam {unicodedata.unidata_version} -- "
            "olgusal iddia BAYATLADI"
        )


def test_r5_k26_kod_hala_nfkc_ile_karar_veriyor_beyaz_liste_yok() -> None:
    """K26 "kod HICBIR SATIR degismedi" iddiasi: karar HALA NFKC
    denkligiyle aliniyor, alti codepoint'in HICBIRI yurutulebilir kodda
    sabit kodlanmis DEGIL."""
    fn = _func_ast(normalizer_mod._is_single_char_noise)
    kod = "\n".join(ast.unparse(node) for node in fn.body[1:])  # docstring haric
    for cp in _K26_BEKLENEN:
        assert chr(cp) not in kod, f"U+{cp:04X} kodda sabit kodlanmis (beyaz liste)"
    assert "normalize('NFKC'" in kod.replace('"', "'")
    assert "category" in kod


# ===========================================================================
# 7. K27 -- `menu` kapsam disi; DORT on ayarin HER biri icin test.
# ===========================================================================


def test_r5_k27_ayni_fixture_dort_on_ayarda_beklendigi_gibi_davraniyor() -> None:
    """K27'nin zorunlu testi, GERCEKTEN AYNI fixture ile (docstring
    "AYNI ... fixture'u DORT on ayarla da calistirilir" diyor):
    `dialogue`/`tooltip`/`subtitle` -> govde2 MIRAS ALIR; `menu` ->
    govde2 AYRI kalir VE `speaker=None`."""
    fixture = [blk("Ada:", 10, 0), blk("x" * 150, 10, 22), blk("y" * 150, 10, 44)]
    beklenen = {
        OcrPreset.DIALOGUE: "Ada",
        OcrPreset.TOOLTIP: "Ada",
        OcrPreset.SUBTITLE: "Ada",
        OcrPreset.MENU: None,
    }
    for preset, beklenen_speaker in beklenen.items():
        out = normalize(fixture, preset)
        assert len(out) == 2, (preset.value, [s.source_blocks for s in out])
        assert out[0].speaker == "Ada", preset.value
        assert out[1].speaker == beklenen_speaker, (preset.value, out[1].speaker)
        assert [s.source_blocks for s in out] == [(0, 1), (2,)], preset.value


def test_r5_k27_menu_de_group_gercekten_cagirilmiyor() -> None:
    """K27'nin MEKANIK iddiasi: `menu`'de `should_group=False` oldugu icin
    `_group` HIC cagirilmaz. Cagrilirsa patlayan bir yedekle kanitlanir --
    `menu` sorunsuz gecer, `dialogue` patlar."""
    cagrildi: list[str] = []

    def patlayan(*args: Any, **kwargs: Any) -> Any:
        cagrildi.append("evet")
        raise AssertionError("_group cagrildi")

    blocks = [blk("Ada:", 10, 0), blk("x" * 40, 10, 22), blk("y" * 40, 10, 44)]
    orijinal = normalizer_mod._group
    try:
        normalizer_mod._group = patlayan  # type: ignore[assignment]
        out = normalize(blocks, OcrPreset.MENU)  # cagirmamali
        assert cagrildi == []
        assert len(out) == 2
        with pytest.raises(AssertionError, match="_group cagrildi"):
            normalize(blocks, OcrPreset.DIALOGUE)  # cagirmali
        assert cagrildi == ["evet"]
    finally:
        normalizer_mod._group = orijinal  # type: ignore[assignment]

    # yedek gercekten geri konmus mu (sonraki testler bozulmasin)
    assert normalizer_mod._group is _group
    assert len(normalize(blocks, OcrPreset.DIALOGUE)) == 1


def test_r5_k27_group_cagrisi_yapisal_olarak_should_group_a_bagli() -> None:
    """YAPISAL: `_normalize_impl` icinde `_group(...)` cagrisi
    `params.should_group` kosuluna bagli bir IfExp icinde -- yani `menu`
    icin atlanmasi bir CALISMA ZAMANI tesadufu degil, yapisal."""
    fn = _func_ast(normalizer_mod._normalize_impl)
    ifexps = [
        n
        for n in ast.walk(fn)
        if isinstance(n, ast.IfExp)
        and isinstance(n.body, ast.Call)
        and isinstance(n.body.func, ast.Name)
        and n.body.func.id == "_group"
    ]
    assert len(ifexps) == 1, "_group cagrisi should_group kosuluna bagli bir IfExp icinde DEGIL"
    assert ast.unparse(ifexps[0].test) == "params.should_group"
    assert ast.unparse(ifexps[0].orelse) == "items"


def test_r5_k27_dort_on_ayarin_her_biri_icin_test_var() -> None:
    """K27: "Dort on ayarin her biri icin birer test bunu sabitleyecek."
    Gercek test dosyasinda dort on ayarin HER biri icin bir K27 testi
    olmali VE her test KENDI on ayarini kullanmali."""
    from tests.unit.ocr import test_normalizer as gercek

    kaynak = inspect.getsource(gercek)
    tree = ast.parse(kaynak)
    k27_testleri = {
        node.name: ast.unparse(node)
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_k27_")
    }
    assert len(k27_testleri) == 4, sorted(k27_testleri)
    for preset in ALL_PRESETS:
        eslesen = [ad for ad in k27_testleri if preset.value in ad]
        assert len(eslesen) == 1, (preset.value, sorted(k27_testleri))
        govde = k27_testleri[eslesen[0]]
        assert f"OcrPreset.{preset.name}" in govde, (preset.value, govde[:200])


# ===========================================================================
# 8. K14 -- butce assertion'i GERCEK test dosyasinin KENDI govdesi
#    uzerinde, IMKANSIZ esikle ZORLANIR.
# ===========================================================================


def test_r5_k14_gercek_testin_kendi_govdesi_imkansiz_esikle_kiriliyor() -> None:
    """K14 assertion'i dekoratif mi? Gercek testin KAYNAK KODUNU al,
    esigi `5.0` -> `0.0` yap (IMKANSIZ butce) ve AYNI govdeyi calistir --
    `AssertionError` FIRLATMALI. Firlatmiyorsa assertion sahtedir."""
    from tests.unit.ocr import test_normalizer as gercek

    kaynak = inspect.getsource(gercek.test_k14_normalizasyon_butcesi_5ms_medyan)
    assert "median_ms <= 5.0" in kaynak
    bozulmus = kaynak.replace("median_ms <= 5.0", "median_ms <= 0.0")
    assert bozulmus != kaynak

    ns: dict[str, Any] = {
        "_budget_blocks": gercek._budget_blocks,
        "normalize": normalize,
        "OcrPreset": OcrPreset,
        "statistics": statistics,
        "time": time,
        "TextBlock": TextBlock,
    }
    exec(compile(bozulmus, "<k14-forced>", "exec"), ns)
    with pytest.raises(AssertionError, match="butcesi"):
        ns["test_k14_normalizasyon_butcesi_5ms_medyan"]()

    # ORIJINAL govde (5 ms) HALA geciyor -- yani kirilma esikten geliyor
    gercek.test_k14_normalizasyon_butcesi_5ms_medyan()


def test_r5_k14_gercek_testte_hala_gercek_assert_ve_skip_yok() -> None:
    from tests.unit.ocr import test_normalizer as gercek

    fn = gercek.test_k14_normalizasyon_butcesi_5ms_medyan
    kaynak = inspect.getsource(fn)
    assert "assert median_ms <= 5.0" in kaynak
    marks = getattr(fn, "pytestmark", [])
    assert {m.name for m in marks}.isdisjoint({"skip", "xfail", "skipif"})


# ===========================================================================
# 9. TUR 5 KARARLARI DOCSTRING'DE BELGELENDI MI (packet.md: her karar
#    ILGILI DOCSTRING'e yazilacak -- "tester yalnizca burayi gorur").
#    Tur 3'un docstring-OFSET testleri hala yesil mi (docstring buyudu).
# ===========================================================================


@pytest.mark.parametrize(
    "anchor",
    [
        "## K23/K24",
        "K23 -- DEGISMEZ",
        "K24 -- K21'in TEK gecerli ifadesi",
        "K25",
        "K26 (sef_karari-tur5.md",
        "K27 (tur 5)",
    ],
)
def test_r5_tur5_kararlari_modul_docstringinde_belgeli(anchor: str) -> None:
    doc = normalizer_mod.__doc__ or ""
    assert anchor in doc, f"{anchor!r} docstring'de yok"


def test_r5_docstring_ofset_bolumleri_buyume_sonrasi_hala_bulunabiliyor() -> None:
    """Tur 3'te kurdugum docstring-OFSET yontemi (bolumu anchor'dan
    bulup pencere icinde okuma) docstring BUYUDUKTEN sonra da calisiyor
    mu -- ve bulunan pencereler DOGRU bolumu mu gosteriyor (bir sonraki
    bolumun basligina TASMIYOR mu)."""
    doc = normalizer_mod.__doc__ or ""

    # 1. "## Isleme sirasi" -> "## K1" penceresi (tur 3 testinin yontemi)
    bas = doc.find("## Isleme sirasi")
    son = doc.find("## K1", bas)
    assert bas != -1 and son > bas
    pencere = doc[bas:son]
    for adim in (
        "guven esigi filtresi",
        "gurultu eleme",
        "satir birlestirme",
        "konusmaci ayiklama",
        "gruplama",
        "yer tutucu toplama",
    ):
        assert adim in pencere, adim
    sirasi = [
        pencere.find("guven esigi filtresi"),
        pencere.find("gurultu eleme"),
        pencere.find("satir birlestirme"),
        pencere.find("konusmaci ayiklama"),
        pencere.find("gruplama"),
        pencere.find("yer tutucu toplama"),
    ]
    assert sirasi == sorted(sirasi), sirasi

    # 2. K20 penceresi (tur 3): 3000 karakterlik pencere HALA K20'nin
    #    kendi metnini kapsiyor ve gerekli ibareleri tasiyor.
    k20 = doc.find("K20 (sef_karari-tur3.md")
    assert k20 != -1
    k20_bolum = doc[k20 : k20 + 3000]
    assert "BILGI AMACLIDIR" in k20_bolum
    assert "BEYAZ LISTE DEGILDIR" in k20_bolum
    assert "NFKC" in k20_bolum

    # 3. K23 degismezinin METNI docstring'de -- "BIREBIR AYNI" + "YALNIZCA"
    k23 = doc.find("K23 -- DEGISMEZ")
    assert k23 != -1
    k23_bolum = doc[k23 : k23 + 2000]
    assert "BOLUMLEMESI" in k23_bolum
    assert "BIREBIR AYNI" in k23_bolum
    assert "source_blocks" in k23_bolum


# ===========================================================================
# 10. `_group` YENIDEN YAZILDI -- ondan ETKILENEBILECEK ONCEKI kararlarin
#     (K3/K8/K9/K10/K11/K12/K13 + "asil is") TUR 5 SPOT REGRESYONU.
# ===========================================================================


def test_r5_regresyon_asil_is_bolunmus_cumle_hala_birlesiyor() -> None:
    """Modulun VAR OLMA SEBEBI (tasarim S5.2): iki satira bolunmus cumle
    gruplayan on ayarlarda BIRLESIR, `menu`'de BIRLESMEZ."""
    blocks = [blk("Bu uzun bir", 10, 0), blk("cumledir.", 10, 22)]
    for preset in (OcrPreset.DIALOGUE, OcrPreset.TOOLTIP, OcrPreset.SUBTITLE):
        out = normalize(blocks, preset)
        assert [s.text for s in out] == ["Bu uzun bir cumledir."], preset.value
    assert len(normalize(blocks, OcrPreset.MENU)) == 2


def test_r5_regresyon_k3_k8_miras_varken_de_gecerli() -> None:
    """K3 (okuma sirasi) + K8 (ORIJINAL indeks uzayi, artan, tekrarsiz,
    AYRIK) -- miras GERCEKTEN devredeyken de gecerli olmali (goruntu
    gecisi `source_blocks`a dokunmuyor)."""
    blocks = [blk("Ada:", 10, 0)] + [blk("z" * 140, 10, 22 + i * 22) for i in range(5)]
    blocks.insert(3, blk("ELENECEK", 10, 999, confidence=0.05))  # esik alti
    out = normalize(blocks, OcrPreset.DIALOGUE)
    assert all(s.speaker == "Ada" for s in out), [s.speaker for s in out]
    ys = [s.bbox.y for s in out]
    assert ys == sorted(ys)
    tum: list[int] = []
    for s in out:
        assert list(s.source_blocks) == sorted(s.source_blocks)
        assert len(set(s.source_blocks)) == len(s.source_blocks)
        assert s.source_blocks
        tum.extend(s.source_blocks)
    assert len(set(tum)) == len(tum), "segmentlerin source_blocks kumeleri AYRIK degil"
    assert 3 not in tum  # esik-alti blogun indeksi hicbir segmentte yok


def test_r5_regresyon_k9_k15_x_y_ve_none_y_hala_birlesmiyor() -> None:
    """K15 matrisinin iki KRITIK satiri (`X/Y` ve `None/Y`), `_group`
    yeniden yazildiktan SONRA da: iki farkli konusmaci ASLA birlesmez."""
    params = get_params(OcrPreset.DIALOGUE)
    x_y = (_Item("a", Rect(0, 0, 100, 20), "Ada", (0,)), _Item("b", Rect(0, 20, 100, 20), "Efe", (1,)))
    none_y = (_Item("a", Rect(0, 0, 100, 20), None, (0,)), _Item("b", Rect(0, 20, 100, 20), "Efe", (1,)))
    assert _should_group(*x_y, params) is False
    assert _should_group(*none_y, params) is False

    blocks = [blk("Ada: Merhaba", 10, 0), blk("Efe: Selam", 10, 22)]
    out = normalize(blocks, OcrPreset.DIALOGUE)
    assert [(s.speaker, s.text) for s in out] == [("Ada", "Merhaba"), ("Efe", "Selam")]


def test_r5_regresyon_k10_birlesik_bbox_hala_kapsayici_ve_hata_veriyor() -> None:
    """K10: birlesik bbox KAPSAYICI dikdortgen; `monitor_index`/
    `dpi_scale` uyusmazliginda `ValueError`. (K24 SADECE miras-uygunluk
    sorgusunun SOL TARAFINI degistirdi -- ANA birlesim semantigi degil.)"""
    a = blk("Bu uzun bir", 10, 0, w=100, h=20)
    b = blk("cumledir.", 40, 22, w=200, h=30)
    out = normalize([a, b], OcrPreset.DIALOGUE)
    assert len(out) == 1
    r = out[0].bbox
    assert (r.x, r.y, r.right, r.bottom) == (10, 0, 240, 52)

    with pytest.raises(ValueError):
        normalize([blk("Bu uzun bir", 10, 0), blk("cumledir.", 10, 22, monitor_index=1)], OcrPreset.DIALOGUE)


def test_r5_regresyon_k11_k12_k13_hala_gecerli() -> None:
    """K11 (dort on ayar gercekten farkli), K12 (bos sonuclar), K13
    (ayni girdiyle ardisik cagrilar bit-bit ayni) -- tur 5 sonrasi."""
    blocks = [blk("Bu uzun bir", 10, 0), blk("cumledir.", 10, 22)]
    assert len(normalize(blocks, OcrPreset.DIALOGUE)) == 1
    assert len(normalize(blocks, OcrPreset.MENU)) == 2
    # tooltip: dikey bosluk orani 0.3 -> gap=2 < 0.3*20=6, birlesir; ama
    # gap buyudugunde dialogue birlestirirken tooltip birlestirmez.
    ayrisan = [blk("Bu uzun bir", 10, 0, h=20), blk("cumledir.", 10, 30, h=20)]
    assert len(normalize(ayrisan, OcrPreset.DIALOGUE)) == 1
    assert len(normalize(ayrisan, OcrPreset.TOOLTIP)) == 2

    assert normalize([], OcrPreset.DIALOGUE) == []
    assert normalize([blk("Merhaba", 10, 0, confidence=0.1)], OcrPreset.DIALOGUE) == []
    assert normalize([blk("", 10, 0), blk("   ", 10, 22), blk(".", 10, 44)], OcrPreset.DIALOGUE) == []

    karisik = [blk("Ada:", 10, 0)] + [blk("z" * 140, 10, 22 + i * 22) for i in range(4)]
    ilk = normalize(karisik, OcrPreset.DIALOGUE)
    for _ in range(5):
        assert normalize(karisik, OcrPreset.DIALOGUE) == ilk


# ===========================================================================
# 11. §4.6/2 -- "her degismezin YANINDA onu OLCEN test ADI yazilir".
#     Docstring'lerde ANILAN test adlari GERCEKTEN var mi?
# ===========================================================================


_BILINEN_BAYAT_ATIFLAR = frozenset(
    {
        # BULGU (tur 5, Tester-B, bloke ETMEYEN -- bkz. verdict-B.md):
        # docstring satir 92 -- gercek ad: test_k2_esik_alti_orta_blok_komsulari_birlestirir
        "test_k2_esik_alti_blok_ortada",
        # K26 bolumunun "Zorunlu test" satiri -- gercek adlar:
        # test_k26_alti_karakterin_hepsi_uyumluluk_formu_ve_etiket_dogru (parametrize)
        # + test_k26_alti_karakterin_etiket_dagilimi_iki_iki_iki
        "test_k26_alti_karakterin_hepsi_uyumluluk_formu_ve_etiket_dagilimi_dogru",
    }
)


def _docstringlerde_anilan_test_adlari() -> set[str]:
    """`normalizer.py`nin MODUL ve FONKSIYON docstring'lerinde anilan test
    adlari. Satir sonu kirilmalari (`test_k26_..._\n    formu_...`) ve
    glob eki (`test_k15_matris_*`) onarilir/atilir."""
    kaynak = inspect.getsource(normalizer_mod)
    tree = ast.parse(kaynak)
    docs = [normalizer_mod.__doc__ or ""]
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            d = ast.get_docstring(node)
            if d:
                docs.append(d)
    adlar: set[str] = set()
    for d in docs:
        duz = re.sub(r"_\s*\n\s*", "_", d)
        duz = re.sub(r"\n\s*", " ", duz)
        for ham in re.findall(r"test_[A-Za-z0-9_]+\*?", duz):
            if ham.endswith("*") or ham == "test_normalizer":  # glob / dosya adi
                continue
            adlar.add(ham.rstrip("_"))
    return adlar


def test_r5_docstring_atifta_bulunan_test_adlari_gercekten_var() -> None:
    """PROTOKOL §4.6 kural 2: bir degismezin YANINDA onu OLCEN testin ADI
    yazilir. O halde docstring'de anilan HER test adi GERCEK test
    dosyasinda BULUNMALI -- yoksa okuyucu olcumu bulamaz.

    Bu test IKI BILINEN bayat atifi (bkz. `_BILINEN_BAYAT_ATIFLAR`,
    verdict-B.md tur 5 bloke-etmeyen bulgu) TOLERE eder ama YENI bir bayat
    atif eklenirse KIRILIR; bilinen ikisi DUZELTILDIGINDE de gecmeye devam
    eder (alt kume kontrolu)."""
    from tests.unit.ocr import test_normalizer as gercek

    var_olan = {
        n.name for n in ast.parse(inspect.getsource(gercek)).body if isinstance(n, ast.FunctionDef)
    }
    anilan = _docstringlerde_anilan_test_adlari()
    assert len(anilan) >= 8, anilan  # atif taramasi BOS degil
    bayat = {ad for ad in anilan if ad not in var_olan}
    yeni_bayat = bayat - _BILINEN_BAYAT_ATIFLAR
    assert yeni_bayat == set(), (
        "docstring'de anilan ama GERCEK test dosyasinda BULUNMAYAN YENI test adi: "
        f"{sorted(yeni_bayat)}"
    )


def test_r5_k26_zorunlu_olcum_gercek_adlariyla_var_ve_yesil() -> None:
    """Bayat ATIF bir bulgu; ama K26'nin ZORUNLU OLCUMUNUN kendisi var mi?
    Iki gercek test (etiket dogrulugu + 2/2/2 dagilimi) VAR olmali ve
    dogrudan cagrildiklarinda GECMELI -- yani bulgu SADECE isim
    duzeyinde, olcum duzeyinde DEGIL."""
    from tests.unit.ocr import test_normalizer as gercek

    adlar = {
        n.name for n in ast.parse(inspect.getsource(gercek)).body if isinstance(n, ast.FunctionDef)
    }
    assert "test_k26_alti_karakterin_hepsi_uyumluluk_formu_ve_etiket_dogru" in adlar
    assert "test_k26_alti_karakterin_etiket_dagilimi_iki_iki_iki" in adlar
    for ch, etiket in (("！", "<wide>"), ("？", "<wide>"), ("﹖", "<small>"), ("︕", "<vertical>")):
        gercek.test_k26_alti_karakterin_hepsi_uyumluluk_formu_ve_etiket_dogru(ch, etiket)
    gercek.test_k26_alti_karakterin_etiket_dagilimi_iki_iki_iki()
