"""T-007 implementer on olcumu 2 -- GERCEK modelle saglayici davranisi (ayri surec, test DEGIL).

Stdout'a YALNIZ ASCII; hicbir ceviri/kaynak metni basilmaz (PROTOKOL 7).
  [A] kanal: alt surecte translate; stdout/stderr BAYT sayisi (CT2 C++ logu dahil)
  [B] K6: sifir bayt model.bin -> ProviderUnavailable (cause RuntimeError), fabrika kuruldu mu
  [C] K6: bos sentencepiece protosu -> kurulum sessiz, encode'da ProviderUnavailable
  [D] K8: repetition_penalty=1.2 gercek CT2'ye gecer, hata yok; 1.0 ile cikti farki var mi (sayi)
  [E] Y2 pozitif kontrol (gercek model): 'A。？' ve '「A。」' tek parca; ciktida 'Hayır' YOK; cumle sayisi == 1
  [F] K9: latency_ms kurulum haric -- ilk cagri latency < kurulum suresi
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

KOK = Path(r"C:\Users\pc\Desktop\efe\çeviri uygulaması")
sys.path.insert(0, str(KOK))
MODEL = KOK / "models" / "nllb-200-distilled-600M-ct2-int8"
FX = json.loads((KOK / ".agents/tasks/T-007/fixtures/cumleler.json").read_text(encoding="utf-8"))

from src.contracts.errors import ProviderUnavailable  # noqa: E402
from src.contracts.models import Rect, Segment, TranslationRequest  # noqa: E402
from src.translate.local_nmt import LocalNmtProvider, cumlelere_bol  # noqa: E402


def istek(metinler: list[str], kaynak: str = "jpn_Jpan") -> TranslationRequest:
    return TranslationRequest(
        segments=tuple(Segment(text=t, bbox=Rect(0, i * 40, 800, 36)) for i, t in enumerate(metinler)),
        source_lang=kaynak, target_lang="tr",
    )


# [A] kanal olcusu: alt surec, stdout/stderr bayt sayisi
kod = (
    "import sys, json; sys.path.insert(0, %r)\n"
    "from src.contracts.models import Rect, Segment, TranslationRequest\n"
    "from src.translate.local_nmt import LocalNmtProvider\n"
    "fx = json.load(open(%r, encoding='utf-8'))\n"
    "p = LocalNmtProvider(model_dir=%r, threads=8)\n"
    "for k in ('JP', 'KR', 'EN'):\n"
    "    segs = tuple(Segment(text=t, bbox=Rect(0, 0, 1, 1)) for t in fx[k])\n"
    "    p.translate(TranslationRequest(segments=segs, source_lang={'JP':'jpn_Jpan','KR':'kor_Hang','EN':'eng_Latn'}[k], target_lang='tr'))\n"
    "p.close()\n"
) % (str(KOK), str(KOK / ".agents/tasks/T-007/fixtures/cumleler.json"), str(MODEL))
rr = subprocess.run([sys.executable, "-c", kod], capture_output=True, timeout=300, cwd=str(KOK))
print(f"[A] alt surec exit={rr.returncode}; stdout {len(rr.stdout)} bayt, stderr {len(rr.stderr)} bayt (ikisi de 0 olmali)")
if rr.returncode != 0:
    print("[A] stderr son 300:", rr.stderr[-300:])

# [B] sifir bayt model.bin
with tempfile.TemporaryDirectory() as td:
    d = Path(td) / "m"
    d.mkdir()
    for ad in ("sentencepiece.bpe.model", "shared_vocabulary.txt", "config.json"):
        shutil.copy2(MODEL / ad, d / ad)
    (d / "model.bin").write_bytes(b"")
    p = LocalNmtProvider(model_dir=d, threads=8)
    try:
        p.translate(istek(["x。"]))
        print("[B] sifir bayt model.bin -> hata YOK (beklenmiyordu)")
    except ProviderUnavailable as e:
        print(f"[B] sifir bayt model.bin -> ProviderUnavailable, cause={type(e.__cause__).__name__}, mesaj metin tasimiyor: {'x' not in str(e).split('dizin')[0]}")
    except Exception as e:  # noqa: BLE001
        print(f"[B] sifir bayt model.bin -> {type(e).__name__} (beklenmiyordu)")

    # [C] bos sentencepiece protosu (gercek model.bin ile) -> kurulum sessiz, encode'da patlar
    (d / "model.bin").unlink()
    (d / "sentencepiece.bpe.model").write_bytes(b"")
    try:
        (d / "model.bin").symlink_to(MODEL / "model.bin")
        yol_turu = "symlink"
    except OSError:
        shutil.copy2(MODEL / "model.bin", d / "model.bin")
        yol_turu = "kopya"
    p = LocalNmtProvider(model_dir=d, threads=8)
    try:
        p.translate(istek(["x。"]))
        print("[C] bos proto -> hata YOK (beklenmiyordu)")
    except ProviderUnavailable as e:
        print(f"[C] bos proto ({yol_turu}) -> ProviderUnavailable, cause={type(e.__cause__).__name__}, mesaj='{str(e)[:40]}'")
    except Exception as e:  # noqa: BLE001
        print(f"[C] bos proto -> {type(e).__name__} (beklenmiyordu)")
    p.close()

# [D] repetition_penalty=1.2 gercek CT2'ye gecer
p1 = LocalNmtProvider(model_dir=MODEL, threads=8)
p2 = LocalNmtProvider(model_dir=MODEL, threads=8, repetition_penalty=1.2)
r1 = p1.translate(istek(FX["KR"], "kor_Hang"))
r2 = p2.translate(istek(FX["KR"], "kor_Hang"))
print(f"[D] rp=1.2 -> hata yok, {len(r2.translations)} ceviri; rp=1.0 ile ayni mi: {r1.translations == r2.translations} (C7: farkli beklenir)")
p2.close()

# [E] Y2 pozitif kontrol gercek modelle
for metin in ["A。？", "「A。」", "待って！？本当に行くの？", "長老は言った。「東へ行きなさい。」"]:
    parcalar = cumlelere_bol(metin)
    r = p1.translate(istek([metin]))
    c = r.translations[0]
    print(f"[E] parca={len(parcalar)} -> ciktida 'Hayır' var mi: {'Hayır' in c or 'hayır' in c.lower()}; 'Böyle' var mi: {'Böyle' in c}; bos mu: {not c.strip()}")

# [F] latency kurulum haric
p3 = LocalNmtProvider(model_dir=MODEL, threads=8)
t0 = time.perf_counter()
r = p3.translate(istek(FX["JP"][:1]))
duvar = (time.perf_counter() - t0) * 1000
print(f"[F] ilk cagri: duvar {duvar:.0f} ms, latency_ms {r.latency_ms:.0f} ms -> kurulum haric mi: {r.latency_ms < duvar - 200}")
p3.close()
p1.close()
print("OLCUM-2 BITTI")
