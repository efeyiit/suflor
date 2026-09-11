"""Sonda r2-03 (ayri surec, gercek motor): v3 ek listesinin DISINDA kalan gercekci ekler.

KR kopula `다` (unlu sonrasi `이다`nin dogal bicimi), `예요`/`이에요` (kibar kopula), `한테서`/`에게서`
(cikma), JP hiragana saygi ekleri `くん`/`さま` (ayni betikli hiragana adla). Her negatif icin ayni
siniftan pozitif kontrol (listedeki ek: `입니다`, `야`, `에게`; JP `さん`). Olcu: hit sayisi (statik) +
ham/gomulu ceviride hedef adin varligi. Stdout yalniz ASCII; ham metinler UTF-8 dosyaya.
"""
from __future__ import annotations

import dataclasses
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from yardimci import KOK  # noqa: E402
from src.contracts.models import Rect, Segment, TranslationRequest  # noqa: E402
from src.translate.sozluk import GlossaryStore, terimleri_gom  # noqa: E402
from src.translate.local_nmt import LocalNmtProvider  # noqa: E402

OUT = KOK / ".agents/tasks/T-011/tester_A_evidence/r2-sonda-03-gercek-model.txt"


def _model_dizini() -> Path:
    """Model dizini sefin kapisindan (real_check.MODEL) okunur; burada ad gecmez."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("t011_real_check", KOK / ".agents/tasks/T-011/real_check.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return Path(mod.MODEL)


satirlar: list[str] = []


def yaz(s: str, konsol: bool = True) -> None:
    satirlar.append(s)
    if konsol:
        print(s.encode("ascii", "backslashreplace").decode("ascii"))


td = tempfile.TemporaryDirectory()
yol = Path(td.name) / "s.json"
yol.write_text(json.dumps({"terimler": [{"kaynak": "마르쿠스", "hedef": "Marcus"}, {"kaynak": "マルクス", "hedef": "Marcus"},
                                        {"kaynak": "ひかり", "hedef": "Hikari"}]}, ensure_ascii=False), encoding="utf-8")
s = GlossaryStore(yol)
p = LocalNmtProvider(model_dir=_model_dizini(), threads=8)

# (etiket, cumle, dil, hedef ad, listede mi)
cumleler = [
    ("KR kopula 다 (listede YOK)", "그는 마르쿠스다.", "kor_Hang", "Marcus", False),
    ("KR kopula 예요 (listede YOK)", "저는 마르쿠스예요.", "kor_Hang", "Marcus", False),
    ("KR cikma 한테서 (listede YOK)", "마르쿠스한테서 편지를 받았어요.", "kor_Hang", "Marcus", False),
    ("KR cikma 에게서 (listede YOK)", "마르쿠스에게서 편지를 받았어요.", "kor_Hang", "Marcus", False),
    ("KR kopula 입니다 (POZITIF, listede)", "저는 마르쿠스입니다.", "kor_Hang", "Marcus", True),
    ("KR kopula 이다 (POZITIF, listede)", "그는 마르쿠스이다.", "kor_Hang", "Marcus", True),
    ("KR yonelme 에게 (POZITIF, listede)", "마르쿠스에게 편지를 보냈어요.", "kor_Hang", "Marcus", True),
    ("JP hiragana ad + くん (listede YOK, ayni betik)", "ひかりくんが来た。", "jpn_Jpan", "Hikari", False),
    ("JP hiragana ad + さま (listede YOK, ayni betik)", "ひかりさまが来た。", "jpn_Jpan", "Hikari", False),
    ("JP hiragana ad + さん (POZITIF, listede)", "ひかりさんが来た。", "jpn_Jpan", "Hikari", True),
    ("JP katakana ad + くん (POZITIF, betik gecisi)", "マルクスくんが来た。", "jpn_Jpan", "Marcus", True),
]
ozet: list[tuple[str, int, bool, bool, bool]] = []
try:
    for etiket, c, dil, hedef, listede in cumleler:
        segs = (Segment(text=c, bbox=Rect(0, 0, 800, 36)),)
        hits = tuple(dataclasses.replace(h, segment_index=0) for h in s.lookup(c))
        gomulu = terimleri_gom(segs, hits)
        ham = p.translate(TranslationRequest(segments=segs, source_lang=dil, target_lang="tr")).translations[0]
        cev = p.translate(TranslationRequest(segments=gomulu, source_lang=dil, target_lang="tr")).translations[0]
        yaz(f"[{etiket}]")
        yaz(f"  cumle        : {c}", konsol=False)
        yaz(f"  hits         : {[(h.start, h.end) for h in hits]}")
        yaz(f"  gomulu kaynak: {gomulu[0].text}", konsol=False)
        yaz(f"  ham ceviri   : {ham}", konsol=False)
        yaz(f"  gomulu ceviri: {cev}", konsol=False)
        yaz(f"  OZET: listede={listede} hit={len(hits)} ham_ad={hedef in ham} gomulu_ad={hedef in cev}")
        ozet.append((etiket, len(hits), listede, hedef in ham, hedef in cev))
finally:
    p.close()

yaz("")
yaz("== OZET TABLO (etiket | listede | hit | hamda ad | gomuluda ad)")
for etiket, n, listede, h_ad, g_ad in ozet:
    yaz(f"  {etiket:48s} | {str(listede):5s} | {n} | {str(h_ad):5s} | {g_ad}")
kacan = [e for e, n, listede, h_ad, g_ad in ozet if not listede and n == 0 and not h_ad]
yaz(f"listede olmayan ek + 0 hit + hamda ad YOK (Y-B2 sinifi kacak): {len(kacan)}")
for e in kacan:
    yaz(f"  - {e}")
poz = [e for e, n, listede, h_ad, g_ad in ozet if listede and n == 1 and g_ad]
yaz(f"pozitif kontrol (listede, 1 hit, gomuluda ad var): {len(poz)}/{sum(1 for o in ozet if o[2])}")
OUT.write_text("\n".join(satirlar) + "\n", encoding="utf-8")
print(f"yazildi -> {OUT.name}")
