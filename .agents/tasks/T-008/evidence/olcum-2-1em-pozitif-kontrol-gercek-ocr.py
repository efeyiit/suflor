"""T-008 olcum 2 (implementer) -- 1-em bosluk sinifi: esik icin GERCEK pozitif kontrol.

    python .agents/tasks/T-008/evidence/olcum-2-1em-pozitif-kontrol-gercek-ocr.py

Olcum 1 gosterdi: `real_check` #4b'nin menu fixture'inda etiket|deger boslugu
13.1-16.3 x h; `YATAY_BOSLUK_ESIGI = 10.0` mutanti orada DUSMUYOR (paketin
"10.0 burada duser" cumlesi olculmemis). Esigin 0.75 secilme sebebi olan
1-em bosluk sinifi (KRT Y3: 0.97-1.06 x h) kapida HIC yok. Bu betik KRT'nin
sentetik goruntulerini (`fixtures-1em/`, sistem fontu, gercek motor) kosar ve
esik taramasiyla hangi esiklerin bu sinifi ayirdigini olcer.

Stdout yalniz ASCII; METIN BASILMAZ (geometri ve sayilar).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

KOK = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(KOK))

from src.contracts.models import Frame, OcrPreset, Rect, TextBlock  # noqa: E402
from src.ocr import satir_birlestirici as sb  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures-1em"


def oku(yol: Path, dil: object) -> list[TextBlock]:
    from src.ocr.rapid_engine import RapidOcrEngine
    img = np.array(Image.open(yol).convert("RGB"))[:, :, ::-1].copy()
    f = Frame(image=img, rect=Rect(0, 0, img.shape[1], img.shape[0]), captured_at=0.0, seq=0)
    return RapidOcrEngine(language=dil, threads=8).recognize(f, OcrPreset.DIALOGUE)  # type: ignore[arg-type]


def main() -> int:
    from src.ocr.rapid_engine import OcrLanguage

    print("T-008 olcum 2 -- 1-em bosluk sinifi, gercek OCR, esik taramasi")
    esikler = (0.57, 0.75, 1.0, 2.0, 10.0)
    fixturelar = (
        ("jp_secim_ideospace.png", OcrLanguage.JAPAN, "JP secim satiri, ideografik bosluk (U+3000)"),
        ("jp_secim_gap1h.png", OcrLanguage.JAPAN, "JP secim satiri, ~1.0 x font bosluk"),
        ("kr_menu_2sutun_1h.png", OcrLanguage.KOREAN, "KR etiket|deger, ~1.0 x font bosluk"),
        ("kr_menu_2sutun_2h.png", OcrLanguage.KOREAN, "KR etiket|deger, ~2.0 x font bosluk"),
    )
    orijinal = sb.YATAY_BOSLUK_ESIGI
    ozet: list[str] = []
    for ad, dil, aciklama in fixturelar:
        bl = oku(FIX / ad, dil)
        print(f"[{ad}] {aciklama}: {len(bl)} kutu")
        # ayni satir ciftleri (uygulamanin satir bolumlemesiyle) bosluk/min(h)
        sirali = sorted(bl, key=lambda b: (b.bbox.y, b.bbox.x))
        oranlar: list[float] = []
        for a, b in zip(sirali, sirali[1:]):
            ort = min(a.bbox.bottom, b.bbox.bottom) - max(a.bbox.y, b.bbox.y)
            if ort >= 0.5 * min(a.bbox.h, b.bbox.h) and b.bbox.x > a.bbox.x:
                oranlar.append(round((b.bbox.x - a.bbox.right) / min(a.bbox.h, b.bbox.h), 2))
        print(f"    kutular (x,y,w,h): {[(b.bbox.x, b.bbox.y, b.bbox.w, b.bbox.h) for b in sirali]}")
        print(f"    ayni satir komsu ciftleri bosluk/min(h): {oranlar}")
        satir = []
        for esik in esikler:
            sb.YATAY_BOSLUK_ESIGI = esik  # type: ignore[misc]
            n = len(sb.satirlari_birlestir(bl))
            satir.append(f"{esik}->{n}")
        sb.YATAY_BOSLUK_ESIGI = orijinal  # type: ignore[misc]
        print(f"    esik->blok: {' '.join(satir)}  (beklenen: 1-em sinifi AYRI kalsin = kutu sayisi korunsun)")
        ozet.append(f"{ad}: {' '.join(satir)}")
    print()
    print("OZET (esik->blok):")
    for s in ozet:
        print("  " + s)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
