"""TESTER-B tur 2 -- T2-2 (yalniz yer tutucu parcasi) GERCEK MODELDE, depodaki (mutasyonsuz) kodla.

    python .agents/tasks/T-007/tester_B/r2_gercek_model_t22.py

Sef karari T2-2 olcusu olarak `real_check #4c` yaziyor ama `real_check.py`de #4c YOK
(13 kontrol). Bu betik o bosluğu kapatir: ayri alt surecte gercek model, motor
sarmalanarak modele giden parca sayilir; cikti yalniz "kaynakla ayni mi" + sayilar.
Ceviri metni basilmaz (PROTOKOL 7). Pozitif kontrol: `{PLAYER} is here.` gider.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

DEPO = Path(__file__).resolve().parents[4]
MODEL = DEPO / "models" / "nllb-200-distilled-600M-ct2-int8"

COCUK = r'''
import json, sys
sys.path.insert(0, %(kok)r)
from pathlib import Path
from src.contracts.models import Rect, Segment, TranslationRequest
from src.translate.local_nmt import LocalNmtProvider, _varsayilan_fabrika
sayac = {"parca": 0, "fabrika": 0}
def fabrika(model_dir, params):
    sayac["fabrika"] += 1
    motor, enc, dec = _varsayilan_fabrika(model_dir, params)
    class Sarmal:
        def translate_batch(self, tokens, **kw):
            sayac["parca"] += len(tokens)
            return motor.translate_batch(tokens, **kw)
    return Sarmal(), enc, dec
p = LocalNmtProvider(model_dir=Path(%(model)r), threads=8, motor_fabrikasi=fabrika)
out = []
for metin, kaynak, yt in json.loads(sys.argv[1]):
    sayac["parca"] = 0
    r = p.translate(TranslationRequest(segments=(Segment(text=metin, bbox=Rect(0,0,800,36), placeholders=tuple(yt)),), source_lang=kaynak, target_lang="tr"))
    c = r.translations[0]
    out.append({"girdi": metin, "yt": yt, "modele_giden_parca": sayac["parca"], "fabrika_sayaci": sayac["fabrika"],
                "cikti_kaynakla_ayni": c == metin, "cikti_karakter": len(c), "yt_ciktida": {y: (y in c) for y in yt}})
print(json.dumps(out, ensure_ascii=True))
'''

GIRDILER = [
    ["{PLAYER}!", "eng_Latn", ["{PLAYER}"]],  # sef uretti: tur 1'de "- Hayir, hayir. {PLAYER}" uyduruluyordu
    ["{0}!", "eng_Latn", ["{0}"]],
    ["{0}。", "jpn_Jpan", ["{0}"]],  # sef uretti: `{0}♪`
    ["{0} {1}!", "eng_Latn", ["{0}", "{1}"]],
    ["<T0>?!", "kor_Hang", ["<T0>"]],
    ["{PLAYER}!", "eng_Latn", []],  # bildirilmemis: METIN, gider (pozitif kontrol 1)
    ["{PLAYER} is here.", "eng_Latn", ["{PLAYER}"]],  # yaninda metin: gider (pozitif kontrol 2)
    ["{0}! Wait!", "eng_Latn", ["{0}"]],  # vokatif + cumle: yalniz `Wait!` gider
]


def main() -> None:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, "-c", COCUK % {"kok": str(DEPO), "model": str(MODEL)}, json.dumps(GIRDILER)],
                       cwd=str(DEPO), capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=600)
    if r.returncode != 0:
        print("COCUK SUREC HATA:", (r.stderr or "")[-800:])
        raise SystemExit(1)
    print("T2-2 gercek model (depo kodu, mutasyonsuz) -- ceviri metni basilmaz; stderr bayt:", len(r.stderr or ""))
    for o in json.loads(r.stdout):
        print(f"  {o['girdi']!r:22s} yt={o['yt']!s:22s} modele_giden_parca={o['modele_giden_parca']}  fabrika={o['fabrika_sayaci']}  "
              f"cikti==kaynak={o['cikti_kaynakla_ayni']}  cikti_karakter={o['cikti_karakter']}  yt_ciktida={o['yt_ciktida']}")


if __name__ == "__main__":
    main()
