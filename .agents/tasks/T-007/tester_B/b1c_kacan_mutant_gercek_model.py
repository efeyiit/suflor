"""TESTER-B B1c -- bes kapidan kacan K3-03 ('?' eksik) ve K3-05 (U+FF01 eksik) mutantlarinin GERCEK MODELDE urun etkisi.

    TESTER_B_SCRATCH=<dizin> python .agents/tasks/T-007/tester_B/b1c_kacan_mutant_gercek_model.py

Ayri ayna agacinda (`t007_tester_B_ayirt`) src mutasyona ugratilir; her durum icin ayri
alt surec mutasyonlu/mutasyonsuz `src.translate.local_nmt`i import eder, gercek modelle
(depodaki models/, mutlak yol) tek segmentlik istekleri cevirir ve YALNIZ SAYI basar:
modele giden parca sayisi (motor sarmalanarak sayilir), cikti cumle sayisi, anahtar
kelime varligi. Ceviri metni basilmaz (PROTOKOL 7).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mutant_kiti as MK  # noqa: E402

DEPO = MK.DEPO
SCRATCH = Path(os.environ.get("TESTER_B_SCRATCH", tempfile.gettempdir()))
KOK = SCRATCH / "t007_tester_B_ayirt"
MODEL = DEPO / "models" / "nllb-200-distilled-600M-ct2-int8"

COCUK = r'''
import json, re, sys
sys.path.insert(0, %(kok)r)
from pathlib import Path
from src.contracts.models import Rect, Segment, TranslationRequest
from src.translate import local_nmt
from src.translate.local_nmt import LocalNmtProvider, _varsayilan_fabrika
sayac = {"parca": 0}
def fabrika(model_dir, params):
    motor, enc, dec = _varsayilan_fabrika(model_dir, params)
    class Sarmal:
        def translate_batch(self, tokens, **kw):
            sayac["parca"] += len(tokens)
            return motor.translate_batch(tokens, **kw)
    return Sarmal(), enc, dec
p = LocalNmtProvider(model_dir=Path(%(model)r), threads=8, motor_fabrikasi=fabrika)
girdiler = json.loads(sys.argv[1])
out = []
for metin, kaynak, anahtarlar in girdiler:
    sayac["parca"] = 0
    r = p.translate(TranslationRequest(segments=(Segment(text=metin, bbox=Rect(0,0,800,36)),), source_lang=kaynak, target_lang="tr"))
    c = r.translations[0]; cl = c.lower().replace("ğ", "g").replace("ı", "i").replace("ü", "u").replace("ş", "s")
    cumle = len([x for x in re.split(r"[.!?]+", c) if x.strip()])
    out.append({"modele_giden_parca": sayac["parca"], "cikti_cumle": cumle, "anahtar": {a: (a in cl) for a in anahtarlar}, "cikti_karakter": len(c)})
print(json.dumps(out))
'''

GIRDILER = [
    # (metin, kaynak, anahtarlar)  -- anahtarlar sadeleştirilmiş Türkçe köklerdir
    ["기다려! 정말 가는 거야? 마을 장로가 당신을 기다리고 있습니다.", "kor_Hang", ["bekle", "gidiyor", "ihtiyar"]],
    ["Are you ready? The village elder is waiting for you.", "eng_Latn", ["hazir", "bekliyor", "ihtiyar"]],
    ["止まれ！村の長老があなたを待っています。", "jpn_Jpan", ["dur", "bekliyor", "ihtiyar"]],
    ["待って！本当に行くの？", "jpn_Jpan", ["bekle", "gidiyor", "gercekten"]],
]


def _kos(etiket: str) -> None:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    env.pop("PYTHONIOENCODING", None)
    kod = COCUK % {"kok": str(KOK), "model": str(MODEL)}
    r = subprocess.run([sys.executable, "-c", kod, json.dumps(GIRDILER)], cwd=str(KOK), capture_output=True,
                       text=True, encoding="utf-8", errors="replace", env=env, timeout=600)
    print(f"--- {etiket} (exit={r.returncode}) ---")
    if r.returncode != 0:
        print(r.stderr[-600:])
        return
    for g, s in zip(GIRDILER, json.loads(r.stdout.strip().splitlines()[-1]), strict=True):
        print(f"  {g[1]:9s} kaynak {len(g[0]):3d} kr | modele giden parca {s['modele_giden_parca']} | cikti cumle {s['cikti_cumle']} | anahtar {s['anahtar']}")


def main() -> int:
    if KOK.exists():
        shutil.rmtree(KOK, ignore_errors=True)
    yoksay = shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache", ".mypy_cache")
    shutil.copytree(DEPO / "src", KOK / "src", ignore=yoksay)
    (KOK / "tests").mkdir()
    (KOK / ".agents").mkdir()
    MK.KOK = KOK
    print(f"ayna agaci: {KOK}; model: depodaki models/ (mutlak yol)")
    _kos("MUTASYONSUZ (teslim)")
    for mid in ("K3-03", "K3-05"):
        mut = next(m for m in MK.MUTANTLAR if m.mid == mid)
        MK._uygula(mut)
        try:
            _kos(f"{mid}: {mut.aciklama}")
        finally:
            shutil.copyfile(DEPO / MK.MOTOR, KOK / MK.MOTOR)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
