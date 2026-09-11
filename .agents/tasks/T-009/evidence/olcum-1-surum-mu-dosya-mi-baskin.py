"""T-009 olcum-1: `Rec.ocr_version` mi, `Rec.model_path` mi baskin? (implementer, tur 1)

    python .agents/tasks/T-009/evidence/olcum-1-surum-mu-dosya-mi-baskin.py

Mutant kiti M01 beklenmedik sonuc verdi: yalniz `Rec.ocr_version`i v4'e
geri alan mutant (dosya adi v5) gercek T-009 kapisini GECTI. Hipotez:
`allow_download=False` yolunda motor `Rec.model_path`i ACIK verir ve
kutuphane dosyayi yukler; `ocr_version` dosya secimine katilmaz. Bu kit,
kaynagi DEGISTIRMEDEN (fabrika enjeksiyonu ile `params`i sararak) dort
noktada olcer -- her nokta dlg_KR ile 17 kutu, '.' sayisi ve medyan sure:

  A  allow_download=False, model_path v5 dosyasi, ocr_version v5 (URUN)  -> '.'=3 beklenir
  B  allow_download=False, model_path v5 dosyasi, ocr_version v4 (M01)   -> '.'=3 ise dosya baskin
  C  allow_download=True,  model_path YOK,       ocr_version v5          -> '.'=3 ise surum indirme yolunda belirleyici
  D  allow_download=True,  model_path YOK,       ocr_version v4          -> '.'=0 ise surum indirme yolunda belirleyici
  E  JAPAN, allow_download=True, model_path YOK, ocr_version v5          -> istisna tipi (olgular K5: ValueError)
  F  JAPAN, allow_download=False, model_path v4 dosyasi, ocr_version v5  -> ne olur? (M03 acik yol)

C/D indirme YAPMAZ: kutuphane kendi `models/` dizininde v4 ve v5 Korece
dosyalarini bulur (diskte, sef indirdi). Stdout ASCII, metin basilmaz.
Cikis 0 = A/B/C/D beklentileri tuttu (E/F yalniz rapor).
"""
from __future__ import annotations

import statistics
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

KOK = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(KOK))

from src.contracts.models import Frame, OcrPreset, Rect  # noqa: E402
from src.ocr import rapid_engine  # noqa: E402
from src.ocr.rapid_engine import OcrLanguage, RapidOcrEngine  # noqa: E402

FIX = KOK / ".agents" / "tasks" / "T-006" / "fixtures"


def kare(ad: str) -> Frame:
    img = np.array(Image.open(FIX / f"dlg_{ad}.png").convert("RGB"))[:, :, ::-1].copy()
    return Frame(image=img, rect=Rect(0, 0, 1200, 400), captured_at=0.0, seq=0)


def sarilmis_fabrika(surum: str) -> Any:
    """`params["Rec.ocr_version"]`i `surum` yapip gercek fabrikaya verir; gorulen params'i kaydeder."""
    goruldu: dict[str, object] = {}

    def fabrika(params: dict[str, object]) -> Any:
        p = dict(params)
        p["Rec.ocr_version"] = surum
        goruldu.update(p)
        return rapid_engine._varsayilan_fabrika(p)

    fabrika.goruldu = goruldu  # type: ignore[attr-defined]
    return fabrika


def olc(etiket: str, dil: OcrLanguage, allow_download: bool, surum: str, beklenen_nokta: int | None) -> bool:
    f = sarilmis_fabrika(surum)
    m = RapidOcrEngine(language=dil, threads=8, allow_download=allow_download, recognizer_factory=f)
    fr = kare("KR" if dil is OcrLanguage.KOREAN else "JP")
    try:
        bl = m.recognize(fr, OcrPreset.DIALOGUE)
    except Exception as e:
        neden = type(e.__cause__).__name__ if e.__cause__ is not None else "-"
        print(f"  {etiket}  {dil.name:6} allow_download={allow_download!s:5} Rec.ocr_version={surum}  -> ISTISNA {type(e).__name__} (cause {neden})")
        m.close()
        return beklenen_nokta is None
    yol = f.goruldu.get("Rec.model_path")
    yol_ad = Path(str(yol)).name if yol is not None else "YOK"
    nokta = sum(b.text.count(".") for b in bl)
    s = []
    for _ in range(5):
        t0 = time.perf_counter(); m.recognize(fr, OcrPreset.DIALOGUE); s.append((time.perf_counter() - t0) * 1000)
    med = statistics.median(s)
    m.close()
    tuttu = beklenen_nokta is None or nokta == beklenen_nokta
    bek = "-" if beklenen_nokta is None else str(beklenen_nokta)
    print(f"  {etiket}  {dil.name:6} allow_download={allow_download!s:5} Rec.ocr_version={surum} model_path={yol_ad:34} "
          f"-> {len(bl)} blok, '.'={nokta} (beklenen {bek}), medyan {med:.0f} ms" + ("" if tuttu else "  <-- TUTMADI"))
    return tuttu


def main() -> int:
    print("T-009 olcum-1 -- surum mu dosya mi baskin (dlg_KR, gercek model)")
    sonuc = [
        olc("A", OcrLanguage.KOREAN, False, "PP-OCRv5", 3),
        olc("B", OcrLanguage.KOREAN, False, "PP-OCRv4", 3),
        olc("C", OcrLanguage.KOREAN, True, "PP-OCRv5", 3),
        olc("D", OcrLanguage.KOREAN, True, "PP-OCRv4", 0),
        olc("E", OcrLanguage.JAPAN, True, "PP-OCRv5", None),
        olc("F", OcrLanguage.JAPAN, False, "PP-OCRv5", None),
    ]
    print()
    if all(sonuc):
        print("OLCUM-1: A/B/C/D beklentileri TUTTU -- acik model_path baskin (B); surum indirme yolunda belirleyici (C/D)")
        return 0
    print("OLCUM-1: beklenti tutmayan var")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
