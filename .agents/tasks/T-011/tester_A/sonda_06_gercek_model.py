"""Sonda 6 (ayri surec, gercek motor): Latin bilesik kelime sinifi -- komsu-terim kurali `windmills`/`windmill`i boler.

Stdout yalniz ASCII ve sayi/bool; ham metinler UTF-8 dosyaya.
"""
from __future__ import annotations

import dataclasses
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from yardimci import KOK, seg  # noqa: E402
from src.contracts.models import Rect, Segment, TranslationRequest  # noqa: E402
from src.translate.sozluk import GlossaryStore, terimleri_gom  # noqa: E402
from src.translate.local_nmt import LocalNmtProvider  # noqa: E402

OUT = KOK / ".agents/tasks/T-011/tester_A_evidence/sonda-06-gercek-model.txt"
def _model_dizini() -> Path:
    """Model dizini sefin kapisindan (real_check.MODEL) okunur; burada ad gecmez."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("t011_real_check", KOK / ".agents/tasks/T-011/real_check.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return Path(mod.MODEL)


MODEL = _model_dizini()
satirlar: list[str] = []


def yaz(s: str) -> None:
    satirlar.append(s)
    print(s.encode("ascii", "backslashreplace").decode("ascii"))


td = tempfile.TemporaryDirectory()
yol = Path(td.name) / "s.json"
yol.write_text(json.dumps({"terimler": [{"kaynak": "mill", "hedef": "Değirmen"}, {"kaynak": "wind", "hedef": "Rüzgar"},
                                        {"kaynak": "Marcus", "hedef": "Marcus"}]}, ensure_ascii=False), encoding="utf-8")
s = GlossaryStore(yol)
p = LocalNmtProvider(model_dir=MODEL, threads=8)

cumleler = [
    "The windmills turn slowly.",
    "The old windmill is broken.",
    "Marcus waits by the windmill.",
    "Marcus waits by the mill.",           # pozitif kontrol: dogru gomme
    "The wind is strong today.",           # pozitif kontrol: wind tek basina
]
try:
    for c in cumleler:
        segs = (Segment(text=c, bbox=Rect(0, 0, 800, 36)),)
        hits = tuple(dataclasses.replace(h, segment_index=0) for h in s.lookup(c))
        gomulu = terimleri_gom(segs, hits)
        ham = p.translate(TranslationRequest(segments=segs, source_lang="eng_Latn", target_lang="tr")).translations[0]
        cev = p.translate(TranslationRequest(segments=gomulu, source_lang="eng_Latn", target_lang="tr")).translations[0]
        yaz(f"CUMLE: {c}")
        yaz(f"  hits: {[(h.start, h.end, h.source_term) for h in hits]}")
        yaz(f"  gomulu kaynak: {gomulu[0].text}")
        yaz(f"  ham ceviri   : {ham}")
        yaz(f"  gomulu ceviri: {cev}")
        yaz(f"  OZET: hit={len(hits)} gomulu_kaynak_parcali_kelime={'Rüzgarmills' in gomulu[0].text or 'RüzgarDeğirmen' in gomulu[0].text} "
            f"ciktida_Degirmen={'Değirmen' in cev} ciktida_Ruzgar={'Rüzgar' in cev} ham_kelime={len(ham.split())} gom_kelime={len(cev.split())}")
finally:
    p.close()

OUT.write_text("\n".join(satirlar) + "\n", encoding="utf-8")
print(f"yazildi -> {OUT.name}")
