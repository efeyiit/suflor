"""T-008 kabul kapisi -- gercek OCR + normalize + NMT ile uctan uca.

    python .agents/tasks/T-008/real_check.py

Sefe aittir; implementer kosar ama YAZMAZ. Stdout yalniz ASCII; metin basilmaz.

Kontroller (packet.md):
  1. KR 17 blok -> 4 blok, line_boxes [2,5,5,5]
  2. JP 4 -> 4 birebir; EN 4 -> 4 birebir (no-op)
  3. UCTAN UCA: KR -> birlestir -> normalize -> <= 4 segment -> NMT -> tek kelimelik ceviri yok
     (icerik beklentisi YOK: KR tanima noktayi dusuruyor, T-009)
  4b. menu fixture (13-16xh): etiket|deger asla birlesmez
  4c. 1-em menu (0.78-1.06xh): 0.75 ayirir, 1.0+ birlestirir -- esik ayirt edici (Y3)
  5. saflik AST
  6. 1000 blok < 50 ms
"""

from __future__ import annotations

import ast
import random
import statistics
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

KOK = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(KOK))

from src.contracts.models import Frame, OcrPreset, Rect, TextBlock, TranslationRequest  # noqa: E402

FIX = KOK / ".agents" / "tasks" / "T-006" / "fixtures"
MODEL = KOK / "models" / "nllb-200-distilled-600M-ct2-int8"
ihlaller: list[str] = []


def ihlal(m: str) -> None:
    ihlaller.append(m); print(f"  IHLAL  {m}")


def tamam(m: str) -> None:
    print(f"  ok     {m}")


def oku(ad: str, dil: object) -> list[TextBlock]:
    from src.ocr.rapid_engine import RapidOcrEngine
    img = np.array(Image.open(FIX / f"dlg_{ad}.png").convert("RGB"))[:, :, ::-1].copy()
    f = Frame(image=img, rect=Rect(0, 0, 1200, 400), captured_at=0.0, seq=0)
    return RapidOcrEngine(language=dil, threads=8).recognize(f, OcrPreset.DIALOGUE)  # type: ignore[arg-type]


def main() -> int:
    print("T-008 real_check -- gercek OCR, normalize, NMT")
    try:
        from src.ocr.satir_birlestirici import satirlari_birlestir
    except Exception as e:  # noqa: BLE001
        ihlal(f"src.ocr.satir_birlestirici import edilemedi: {type(e).__name__}: {e}")
        return 1
    from src.ocr.rapid_engine import OcrLanguage
    from src.ocr.normalizer import normalize

    # 1 KR
    kr = oku("KR", OcrLanguage.KOREAN)
    b = satirlari_birlestir(kr)
    lb = [len(x.line_boxes) for x in b]
    (tamam if len(kr) == 17 and len(b) == 4 else ihlal)(f"[1] KR {len(kr)} blok -> {len(b)} blok (beklenen 17 -> 4)")
    (tamam if lb == [2, 5, 5, 5] else ihlal)(f"[1] line_boxes uzunluklari {lb} (beklenen [2,5,5,5])")
    (tamam if all(" " in x.text for x in b) else ihlal)("[1] her satir bosluklu birlesmis")
    (tamam if all(type(v) is int for x in b for v in (x.bbox.x, x.bbox.y, x.bbox.w, x.bbox.h)) else ihlal)("[1] bbox alanlari int")

    # 2 JP / EN no-op
    for ad, dil in (("JP", OcrLanguage.JAPAN), ("EN", OcrLanguage.ENGLISH)):
        g = oku(ad, dil); c = satirlari_birlestir(g)
        ayni = len(c) == len(g) and all(x.text == y.text and x.bbox == y.bbox for x, y in zip(sorted(g, key=lambda t: (t.bbox.y, t.bbox.x)), c))
        (tamam if ayni else ihlal)(f"[2] {ad} {len(g)} -> {len(c)} no-op (text+bbox birebir)")

    # 3 uctan uca
    segs = normalize(b, OcrPreset.DIALOGUE)
    (tamam if len(segs) <= 4 else ihlal)(f"[3] normalize -> {len(segs)} segment (<= 4; birlestirme oncesi 16)")
    if (MODEL / "model.bin").exists() and segs:
        from src.translate.local_nmt import LocalNmtProvider
        p = LocalNmtProvider(model_dir=MODEL, threads=8)
        r = p.translate(TranslationRequest(segments=tuple(segs), source_lang="kor_Hang", target_lang="tr"))
        birlesik = " ".join(r.translations).lower().replace("ğ", "g")
        tek_kelime = [t for t in r.translations if len(t.strip().rstrip(".!?").split()) <= 1]
        # v1 burada "dogu" bekliyordu -- OLCULMEDEN yazilmisti (sef hatasi, 4.6/10): KR tanima
        # noktayi dusuruyor, cumle kaybi T-009'un konusu. Birlestirmenin garantisi: kelime-kelime YOK.
        tamam(f"[3] NMT kostu: bekliyor={'bekliyor' in birlesik} dogu={'dogu' in birlesik}  (rapor; T-009 acik)")
        (tamam if not tek_kelime else ihlal)(f"[3] tek kelimelik ceviri sayisi {len(tek_kelime)} (0 olmali; onceden 'Evet.' 'Seni.')")
        p.close()
    else:
        ihlal("[3] NMT modeli yok ya da segment yok")

    # 4b menu fixture (Y3 pozitif kontrol): etiket|deger asla birlesmez
    from src.ocr.rapid_engine import OcrLanguage as _OL
    for ad, dil, beklenen_min in (("KR", _OL.KOREAN, 2), ("EN", _OL.ENGLISH, 2)):
        img = np.array(Image.open(KOK / ".agents" / "tasks" / "T-008" / "fixtures" / "menu_KR_EN.png").convert("RGB"))[:, :, ::-1].copy()
        from src.ocr.rapid_engine import RapidOcrEngine as _RE
        mb = _RE(language=dil, threads=8).recognize(Frame(image=img, rect=Rect(0, 0, 900, 300), captured_at=0.0, seq=0), OcrPreset.DIALOGUE)
        mc = satirlari_birlestir(mb)
        satir: dict[int, int] = {}
        for x in mc:
            satir[round(x.bbox.y / 50)] = satir.get(round(x.bbox.y / 50), 0) + 1
        en_az = min(satir.values()) if satir else 0
        (tamam if en_az >= beklenen_min else ihlal)(
            f"[4b] menu {ad}: {len(mb)} -> {len(mc)} blok; satir basina en az {en_az} blok (>= {beklenen_min}: etiket|deger birlesmemeli)")
    # 4c 1-em menu (implementer ITIRAZ 2 + KRT Y3): etiket|deger boslugu 0.78-1.06 x h
    # -> 0.75 ayirir, 1.0/2.0/10.0 birlestirir. Sefin 13-16xh fixture'i bunu AYIRAMIYORDU.
    img = np.array(Image.open(KOK / ".agents" / "tasks" / "T-008" / "fixtures" / "menu_KR_1em.png").convert("RGB"))[:, :, ::-1].copy()
    mb = _RE(language=_OL.KOREAN, threads=8).recognize(Frame(image=img, rect=Rect(0, 0, img.shape[1], img.shape[0]), captured_at=0.0, seq=0), OcrPreset.DIALOGUE)
    mc = satirlari_birlestir(mb)
    satir2: dict[int, int] = {}
    for x in mc:
        satir2[round(x.bbox.y / 40)] = satir2.get(round(x.bbox.y / 40), 0) + 1
    en_az2 = min(satir2.values()) if satir2 else 0
    (tamam if len(mb) == 4 and len(mc) == 4 and en_az2 >= 2 else ihlal)(
        f"[4c] 1-em menu KR: {len(mb)} -> {len(mc)} blok; satir basina en az {en_az2} (>= 2; bosluk 0.78-1.06xh, 1.0+ esik birlestirir)")
    # 5 saflik
    src = (KOK / "src" / "ocr" / "satir_birlestirici.py").read_text(encoding="utf-8")
    agac = ast.parse(src)
    yasak = {"open", "print", "input", "exec", "eval"}
    cagri = {n.func.id for n in ast.walk(agac) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    modul = {a.names[0].name.split(".")[0] for a in ast.walk(agac) if isinstance(a, (ast.Import,)) } | {a.module.split(".")[0] for a in ast.walk(agac) if isinstance(a, ast.ImportFrom) and a.module}
    kotu_modul = modul & {"random", "time", "os", "sys", "io", "pathlib", "logging", "subprocess"}
    (tamam if not (cagri & yasak) and not kotu_modul else ihlal)(f"[5] saflik: yasak cagri {sorted(cagri & yasak)}, yasak modul {sorted(kotu_modul)}")

    # 6 sure
    rnd = random.Random(7)
    cok = [TextBlock(text=f"w{i}", bbox=Rect(rnd.randrange(0, 2000), rnd.randrange(0, 1400) // 40 * 40, 60, 36), confidence=0.9) for i in range(1000)]
    satirlari_birlestir(cok)
    s = []
    for _ in range(5):
        t0 = time.perf_counter(); satirlari_birlestir(cok); s.append((time.perf_counter() - t0) * 1000)
    med = statistics.median(s)
    (tamam if med < 50 else ihlal)(f"[6] 1000 blok medyan {med:.1f} ms (< 50)")

    print()
    if ihlaller:
        print(f"REAL_CHECK: {len(ihlaller)} IHLAL"); return 1
    print("REAL_CHECK: TEMIZ"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
