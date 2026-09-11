"""T-007 kabul kapisi -- GERCEK modelle (NLLB-200 600M CT2 int8).

    python .agents/tasks/T-007/real_check.py

Sefe aittir; implementer kosar ama YAZMAZ. Birim testleri (K1) modeli hic
yuklemez; gercek davranis yalniz burada olculur.

Stdout'a YALNIZ ASCII yazilir (cp1254 dersi, T-006 sef hatasi 17). Hicbir
ceviri/kaynak metni basilmaz (PROTOKOL 7); yalniz sayilar ve ok/IHLAL.

Kontroller (packet.md "Kabul kapisi"):
  1. JP 4 cumle -> 4 ceviri, bos degil, hizali, provider_id
  2. EN 2 cumle -> "bekliyor" ve "degirmen" gecer (zayif icerik kontrolu)
  3. C8 pozitif kontrol: JP 3-cumlelik TEK segment -> >=3 cumle ve uc anahtar
  4. KR 2 cumle TEK segment -> >=2 cumle + anahtarlar (Y1); 4b: yalniz noktalama aynen (Y2)
  5. yer tutucu: JP {0}/{1} -> ciktida var (onarim); EN -> var (model korudu)
  6. sure: JP 4 cumle tek batch beam=4 medyan <= 350 ms (UYARI esigi, Y3)
  7. ASCII-disi model_dir kopyasi -> calisir (C5)
  8. source_lang=None -> ProviderUnavailable; bos model_dir -> ModelMissingError
"""

from __future__ import annotations

import json
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

KOK = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(KOK))

from src.contracts.errors import ModelMissingError, ProviderUnavailable  # noqa: E402
from src.contracts.models import Rect, Segment, TranslationRequest  # noqa: E402

MODEL = KOK / "models" / "nllb-200-distilled-600M-ct2-int8"
FX = json.loads((Path(__file__).resolve().parent / "fixtures" / "cumleler.json").read_text(encoding="utf-8"))

ihlaller: list[str] = []
uyarilar: list[str] = []


def ihlal(m: str) -> None:
    ihlaller.append(m); print(f"  IHLAL  {m}")


def uyari(m: str) -> None:
    uyarilar.append(m); print(f"  UYARI  {m}")


def tamam(m: str) -> None:
    print(f"  ok     {m}")


def istek(metinler: list[str], kaynak: str, yer_tutucular: tuple[str, ...] = ()) -> TranslationRequest:
    segs = tuple(Segment(text=t, bbox=Rect(0, i * 40, 800, 36), placeholders=yer_tutucular) for i, t in enumerate(metinler))
    return TranslationRequest(segments=segs, source_lang=kaynak, target_lang="tr")


def cumle_say(s: str) -> int:
    return len([p for p in re.split(r"[.!?]+", s) if p.strip()])


def main() -> int:
    print("T-007 real_check -- gercek model")
    try:
        from src.translate.local_nmt import LocalNmtProvider
    except Exception as e:  # noqa: BLE001
        ihlal(f"src.translate.local_nmt import edilemedi: {type(e).__name__}: {e}")
        return 1
    if not (MODEL / "model.bin").exists():
        ihlal(f"model yok: {MODEL}")
        return 1

    p = LocalNmtProvider(model_dir=MODEL, threads=8)

    # 1 JP 4 cumle
    r = p.translate(istek(FX["JP"], "jpn_Jpan"))
    (tamam if len(r.translations) == 4 and all(t.strip() for t in r.translations) else ihlal)(
        f"[1] JP 4 cumle -> {len(r.translations)} ceviri, bos olan {sum(1 for t in r.translations if not t.strip())}")
    (tamam if r.provider_id == "local-nmt-nllb200-600m-int8" else ihlal)(f"[1] provider_id={r.provider_id!r}")
    (tamam if r.latency_ms >= 0 and not r.partial and not r.from_cache else ihlal)(
        f"[1] latency_ms={r.latency_ms:.0f} partial={r.partial} from_cache={r.from_cache}")

    # 2 EN icerik
    r = p.translate(istek(FX["EN"], "eng_Latn"))
    birlesik = " ".join(r.translations).lower()
    (tamam if "bekliyor" in birlesik and "degirmen" in birlesik.replace("ğ", "g") else ihlal)(
        f"[2] EN: 'bekliyor' {'var' if 'bekliyor' in birlesik else 'YOK'}, "
        f"'degirmen' {'var' if 'degirmen' in birlesik.replace(chr(0x11f),'g') else 'YOK'}")

    # 3 C8 pozitif kontrol: paragraf tek segment
    r = p.translate(istek([FX["JP_paragraf"]], "jpn_Jpan"))
    c = r.translations[0]; n = cumle_say(c); cl = c.lower()
    anahtar = ("ihtiyar" in cl, "doğu" in cl or "dogu" in cl, "güneş" in cl or "gun" in cl.replace("ü", "u"))
    (tamam if n >= 3 and all(anahtar) else ihlal)(
        f"[3] JP paragraf tek segment -> {n} cumle, anahtarlar ihtiyar/dogu/gunes = {anahtar}  (tek girdide 2. cumle eriyordu)")

    # 4 KR: TEK segment (Y1 pozitif kontrolu -- v1 onceden bolunmus gonderiyordu, kapi kordu)
    r = p.translate(istek([" ".join(FX["KR"])], "kor_Hang"))
    c = r.translations[0]; n = cumle_say(c); cl = c.lower().replace("ğ", "g")
    (tamam if n >= 2 and "bekliyor" in cl and "dogu" in cl else ihlal)(
        f"[4] KR 2 cumle TEK segment -> {n} cumle, bekliyor={'bekliyor' in cl} dogu={'dogu' in cl}  (ASCII nokta bolunmezse 2. cumle kaybolur)")

    # 4b Y2 pozitif kontrolu: yalniz noktalama parcasi modele gitmez, aynen gecer
    r = p.translate(istek(["。。。"], "jpn_Jpan"))   # 。。。
    (tamam if r.translations[0].strip() == "。。。" else ihlal)(
        f"[4b] '...' (JP) -> aynen mi: {r.translations[0].strip() == chr(0x3002)*3}  (v1'de 'Hayir, hayir.' uyduruluyordu)")
    # 5 yer tutucu
    r = p.translate(istek([FX["JP_yer_tutucu"]], "jpn_Jpan", ("{0}", "{1}")))
    (tamam if "{0}" in r.translations[0] and "{1}" in r.translations[0] else ihlal)(
        f"[5] JP yer tutucu: {{0}} {'var' if '{0}' in r.translations[0] else 'YOK'}, {{1}} {'var' if '{1}' in r.translations[0] else 'YOK'}  (C9: model dusurur, saglayici onarir)")
    r = p.translate(istek([FX["EN_yer_tutucu"]], "eng_Latn", ("{0}", "{1}")))
    (tamam if "{0}" in r.translations[0] and "{1}" in r.translations[0] else ihlal)(f"[5] EN yer tutucu: korundu")

    # 6 sure
    rq = istek(FX["JP"], "jpn_Jpan")
    p.translate(rq); p.translate(rq)
    s = []
    for _ in range(5):
        t0 = time.perf_counter(); p.translate(rq); s.append((time.perf_counter() - t0) * 1000)
    med = statistics.median(s)
    (tamam if med <= 350 else uyari)(f"[6] JP 4 cumle tek batch beam=4: medyan {med:.0f} ms (esik 350 = olculen 307-316 + pay; uyari)")

    # 7 ASCII-disi model_dir
    with tempfile.TemporaryDirectory() as td:
        hedef = Path(td) / "çeviri-ölçüm"
        hedef.mkdir()
        for ad in ("model.bin", "sentencepiece.bpe.model", "shared_vocabulary.txt", "config.json"):
            if (MODEL / ad).exists():
                shutil.copy2(MODEL / ad, hedef / ad)
        try:
            p2 = LocalNmtProvider(model_dir=hedef, threads=8)
            r = p2.translate(istek(FX["EN"][:1], "eng_Latn"))
            (tamam if r.translations[0].strip() else ihlal)("[7] ASCII-disi model_dir -> calisti")
            p2.close()
        except Exception as e:  # noqa: BLE001
            ihlal(f"[7] ASCII-disi model_dir: {type(e).__name__}: {str(e)[:80]}")

    # 8 hata siniflari
    try:
        p.translate(TranslationRequest(segments=(Segment(text="x", bbox=Rect(0, 0, 1, 1)),), source_lang=None, target_lang="tr"))
        ihlal("[8] source_lang=None -> istisna YOK")
    except ProviderUnavailable:
        tamam("[8] source_lang=None -> ProviderUnavailable")
    except Exception as e:  # noqa: BLE001
        ihlal(f"[8] source_lang=None -> {type(e).__name__} (ProviderUnavailable bekleniyordu)")
    kod = (
        "import sys, tempfile, pathlib; sys.path.insert(0, %r)\n"
        "from src.translate.local_nmt import LocalNmtProvider\n"
        "from src.contracts.errors import ModelMissingError\n"
        "from src.contracts.models import Rect, Segment, TranslationRequest\n"
        "d = pathlib.Path(tempfile.mkdtemp())\n"
        "p = LocalNmtProvider(model_dir=d, threads=8)\n"
        "try:\n"
        "    p.translate(TranslationRequest(segments=(Segment(text='x', bbox=Rect(0,0,1,1)),), source_lang='eng_Latn', target_lang='tr')); print('HATA-YOK')\n"
        "except ModelMissingError: print('MME')\n"
    ) % str(KOK)
    rr = subprocess.run([sys.executable, "-c", kod], capture_output=True, text=True, timeout=120, cwd=str(KOK))
    son = (rr.stdout.strip().splitlines() or [""])[-1]
    (tamam if son == "MME" else ihlal)(f"[8] bos model_dir -> {son!r} (MME bekleniyordu) {rr.stderr.strip()[-120:] if son != 'MME' else ''}")

    p.close()
    print()
    if ihlaller:
        print(f"REAL_CHECK: {len(ihlaller)} IHLAL, {len(uyarilar)} uyari"); return 1
    print(f"REAL_CHECK: TEMIZ ({len(uyarilar)} uyari)"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
