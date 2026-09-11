"""TESTER-B B4 -- GERCEK modelle ayri surecte K10 kanal olcusu: stdout/stderr BAYT sayisi (CT2 C++ logu dahil).

    python .agents/tasks/T-007/tester_B/b4_gercek_surec_sondasi.py

Ebeveyn: cocuk sureci `capture_output=True` ile kosar -> fd 1/2'ye inen HER bayt
(Python `print`, C++ `fprintf(stderr)`, spdlog) sayilir. Cocuk basarida hicbir
sey basmaz; sonuclari (yalniz SAYILAR/boolean, metin yok) bir JSON dosyasina yazar.

A  saglayici: kurulum + JP 4 / KR 2 (tek segment) / EN 2 / JP yer tutucu / bos
   / yalniz noktalama / kapali -> beklenen stdout 0 bayt, stderr 0 bayt
B  pozitif kontrol 1: cocuk `os.write(2, b"x")` -> stderr 1 bayt (fd yakalama calisiyor)
C  pozitif kontrol 2: CT2 log seviyesi DEBUG'a cekilmis ayni akis -> C++ logu stderr'e
   dusuyor mu (dusuyorsa: A'daki 0, saglayicinin seviyeye DOKUNMAMASI + CT2
   varsayilani WARNING sayesinde; dusmuyorsa: C++ logu fd'ye inmiyor, olcu kor)
D  sahte encode/decode gercekcilik: gercek sentencepiece `encode(out_type=str)`
   ilk parcasi `▁` ile basliyor mu, `decode(encode(x)) == x` mi, parca sayilari;
   `translate_batch` gercek imza parametre adlari (test_mercek_B sabitiyle karsilastirilir)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
MODEL = KOK / "models" / "nllb-200-distilled-600M-ct2-int8"
FX = KOK / ".agents" / "tasks" / "T-007" / "fixtures" / "cumleler.json"

COCUK = r'''
import json, logging, os, sys, time
sys.path.insert(0, %(kok)r)
from pathlib import Path
from src.contracts.errors import ProviderUnavailable
from src.contracts.models import Rect, Segment, TranslationRequest
from src.translate.local_nmt import LocalNmtProvider
kip = sys.argv[1]; cikti = Path(sys.argv[2])
FX = json.loads(Path(%(fx)r).read_text(encoding="utf-8"))
son = {"kip": kip}
if kip == "B":
    os.write(2, b"x"); cikti.write_text(json.dumps(son)); raise SystemExit(0)
if kip == "C":
    import ctranslate2
    son["ct2_log_level_once"] = ctranslate2.get_log_level()
    ctranslate2.set_log_level(logging.DEBUG)
    son["ct2_log_level_sonra"] = ctranslate2.get_log_level()
if kip == "D":
    import ctranslate2, sentencepiece, inspect
    son["ct2_log_level_varsayilan"] = ctranslate2.get_log_level()
    sp = sentencepiece.SentencePieceProcessor(model_proto=(Path(%(model)r) / "sentencepiece.bpe.model").read_bytes())
    ornekler = [FX["JP"][1], FX["KR"][0], FX["EN"][0], "A。", "3.5 km", " ".join(FX["KR"])]
    son["sp"] = []
    for x in ornekler:
        p = sp.encode(x, out_type=str)
        son["sp"].append({"karakter": len(x), "parca": len(p), "ilk_parca_alt_cizgi": p[0].startswith("▁") if p else None,
                          "roundtrip": sp.decode(p) == x, "roundtrip_strip": sp.decode(p) == x.strip()})
    son["sp_bos_encode"] = sp.encode("", out_type=str)
    son["sp_bos_decode"] = sp.decode([])
    imza = ctranslate2.Translator.translate_batch.__doc__.split("\n")[0]
    son["translate_batch_ilk_satir_uzunluk"] = len(imza)
    govde = imza.split("(", 1)[1].rsplit(")", 1)[0]
    son["translate_batch_parametreleri"] = sorted({seg.split(":")[0].strip("* ") for seg in govde.split(", ") if ":" in seg and not seg.startswith("self")})
    cikti.write_text(json.dumps(son)); raise SystemExit(0)

def istek(metinler, kaynak, yt=()):
    return TranslationRequest(segments=tuple(Segment(text=t, bbox=Rect(0, i*40, 800, 36), placeholders=yt) for i, t in enumerate(metinler)), source_lang=kaynak, target_lang="tr")

p = LocalNmtProvider(model_dir=Path(%(model)r), threads=8)
t0 = time.perf_counter()
r1 = p.translate(istek(FX["JP"], "jpn_Jpan")); son["jp4_duvar_ms"] = (time.perf_counter() - t0) * 1000; son["jp4_latency_ms"] = r1.latency_ms
son["jp4_bos_olmayan"] = sum(1 for t in r1.translations if t.strip())
r2 = p.translate(istek([" ".join(FX["KR"])], "kor_Hang")); son["kr_tek_segment_cumle"] = len([x for x in r2.translations[0].replace("!", ".").replace("?", ".").split(".") if x.strip()])
r3 = p.translate(istek(FX["EN"], "eng_Latn")); son["en_bekliyor"] = "bekliyor" in " ".join(r3.translations).lower()
r4 = p.translate(istek([FX["JP_yer_tutucu"]], "jpn_Jpan", ("{0}", "{1}"))); son["jp_yt_ikisi_var"] = "{0}" in r4.translations[0] and "{1}" in r4.translations[0]
r5 = p.translate(istek([], "jpn_Jpan")); son["bos_istek"] = r5.translations == ()
r6 = p.translate(istek(["。。。", "   ", ""], "jpn_Jpan")); son["gecis_aynen"] = list(r6.translations) == ["。。。", "   ", ""]
r7 = p.translate(istek(["42", "3.5"], "eng_Latn")); son["rakam_only_cikti_uzunluk"] = [len(t) for t in r7.translations]
p.close(); p.close()
try:
    p.translate(istek(FX["JP"][:1], "jpn_Jpan")); son["kapali_sonrasi"] = "HATA-YOK"
except ProviderUnavailable:
    son["kapali_sonrasi"] = "ProviderUnavailable"
cikti.write_text(json.dumps(son))
'''


def kos(kip: str) -> dict[str, object]:
    with tempfile.TemporaryDirectory() as td:
        cikti = Path(td) / "sonuc.json"
        kod = COCUK % {"kok": str(KOK), "fx": str(FX), "model": str(MODEL)}
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        env.pop("PYTHONIOENCODING", None)
        r = subprocess.run([sys.executable, "-c", kod, kip, str(cikti)], capture_output=True, cwd=str(KOK), env=env, timeout=600)
        son: dict[str, object] = {"kip": kip, "exit": r.returncode, "stdout_bayt": len(r.stdout), "stderr_bayt": len(r.stderr)}
        if r.returncode != 0:
            son["stderr_kuyruk_ascii"] = r.stderr[-400:].decode("ascii", "replace")
        if cikti.exists():
            son["cocuk"] = json.loads(cikti.read_text())
        return son


def main() -> int:
    if not (MODEL / "model.bin").exists():
        print("model yok"); return 1
    ihlal = 0
    for kip, aciklama in [("A", "saglayici gercek model, 7 istek + close x2"), ("B", "pozitif kontrol: os.write(2, b'x')"),
                          ("C", "pozitif kontrol: CT2 log DEBUG + ayni akis"), ("D", "sentencepiece/CT2 gercekcilik olgulari")]:
        s = kos(kip)
        print(f"[{kip}] {aciklama}")
        print(f"    exit={s['exit']}  stdout={s['stdout_bayt']} bayt  stderr={s['stderr_bayt']} bayt")
        if "cocuk" in s:
            for k, v in s["cocuk"].items():  # type: ignore[union-attr]
                if k != "kip":
                    print(f"    {k}: {v}")
        if "stderr_kuyruk_ascii" in s:
            print(f"    stderr kuyruk: {s['stderr_kuyruk_ascii']!r}")
        if kip == "A" and (s["stdout_bayt"] != 0 or s["stderr_bayt"] != 0 or s["exit"] != 0):
            ihlal += 1; print("    IHLAL: gercek yolda kanal temiz degil")
        if kip == "B" and s["stderr_bayt"] != 1:
            ihlal += 1; print("    IHLAL: fd yakalama calismiyor (pozitif kontrol dusmedi)")
        if kip == "C":
            print("    yorum:", "CT2 C++ logu DEBUG'da stderr'e DUSUYOR -> A'daki 0 anlamli (seviye WARNING'de kaldi)" if s["stderr_bayt"] > 0 else "CT2 DEBUG'da bile fd'ye yazmadi -> C++ log kanali bu olcuyle GORULMUYOR (bilgi)")
        print()
    print("B4 SONUC:", "TEMIZ" if ihlal == 0 else f"{ihlal} IHLAL")
    return 1 if ihlal else 0


if __name__ == "__main__":
    raise SystemExit(main())
