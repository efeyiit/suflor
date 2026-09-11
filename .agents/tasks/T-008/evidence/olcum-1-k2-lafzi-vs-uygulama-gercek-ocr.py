"""T-008 olcum 1 (implementer) -- paket v2 K2 LAFZI vs uygulama, GERCEK OCR.

    python .agents/tasks/T-008/evidence/olcum-1-k2-lafzi-vs-uygulama-gercek-ocr.py

Gercek motor (T-006 fixture'lari + T-008 menu fixture'i), ayri surec.
Stdout yalniz ASCII; METIN BASILMAZ (yalniz geometri ve sayilar).

[A] Paketin K2 lafzi -- "(y,x,idx) sirala; TEK GECIS: acik grubun ILK
    bloguyla dikey ortusme, SON bloguna gore x ilerleme + bosluk" -- gercek
    KR geometrisinde kac blok verir? Uygulama kac verir? Sirali (y,x)
    dizisi satir ici x sirasini koruyor mu?
[B] YATAY_BOSLUK_ESIGI taramasi {0.57, 0.75, 1.0, 2.0, 10.0}: dlg_KR blok
    sayisi ve menu fixture'inda satir basina en az blok (real_check #4b
    olcusu). Paketin "2.0/10.0 dlg_KR'de 4 verir, menu'de 10.0 duser"
    iddiasi kendi elimle.
[C] Menu fixture'inda ayni satirdaki ardisik kutu ciftlerinin bosluk/min(h)
    oranlari (gri bolge kaydi).
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

FIX6 = KOK / ".agents" / "tasks" / "T-006" / "fixtures"
MENU = KOK / ".agents" / "tasks" / "T-008" / "fixtures" / "menu_KR_EN.png"


def oku(yol: Path, dil: object, w: int, h: int) -> list[TextBlock]:
    from src.ocr.rapid_engine import RapidOcrEngine
    img = np.array(Image.open(yol).convert("RGB"))[:, :, ::-1].copy()
    f = Frame(image=img, rect=Rect(0, 0, w, h), captured_at=0.0, seq=0)
    return RapidOcrEngine(language=dil, threads=8).recognize(f, OcrPreset.DIALOGUE)  # type: ignore[arg-type]


def paket_lafzi(blocks: list[TextBlock]) -> list[list[TextBlock]]:
    sirali = sorted(enumerate(blocks), key=lambda c: (c[1].bbox.y, c[1].bbox.x, c[0]))
    gruplar: list[list[TextBlock]] = []
    for _, b in sirali:
        r = b.bbox
        if gruplar:
            ilk = gruplar[-1][0].bbox
            son = gruplar[-1][-1].bbox
            ort = min(ilk.bottom, r.bottom) - max(ilk.y, r.y)
            if (
                ort >= sb.DIKEY_ORTUSME_ESIGI * min(ilk.h, r.h)
                and r.x > son.x
                and (r.x - son.right) <= sb.YATAY_BOSLUK_ESIGI * min(son.h, r.h)
            ):
                gruplar[-1].append(b)
                continue
        gruplar.append([b])
    return gruplar


def satir_basina_en_az(bloklar: list[TextBlock]) -> int:
    satir: dict[int, int] = {}
    for x in bloklar:
        satir[round(x.bbox.y / 50)] = satir.get(round(x.bbox.y / 50), 0) + 1
    return min(satir.values()) if satir else 0


def main() -> int:
    from src.ocr.rapid_engine import OcrLanguage

    print("T-008 olcum 1 -- K2 lafzi vs uygulama, gercek OCR")
    kr = oku(FIX6 / "dlg_KR.png", OcrLanguage.KOREAN, 1200, 400)
    print(f"[A] dlg_KR gercek OCR: {len(kr)} kutu")
    print("    kutular (idx: x y w h):", " ".join(f"{i}:{b.bbox.x},{b.bbox.y},{b.bbox.w},{b.bbox.h}" for i, b in enumerate(kr)))
    sirali = sorted(enumerate(kr), key=lambda c: (c[1].bbox.y, c[1].bbox.x, c[0]))
    print("    (y,x,idx) sirali dizi (idx:y,x):", " ".join(f"{i}:{b.bbox.y},{b.bbox.x}" for i, b in sirali))
    lafzi = paket_lafzi(kr)
    print(f"    PAKET LAFZI (tek gecis): {len(kr)} -> {len(lafzi)} grup; parca sayilari {[len(g) for g in lafzi]}")
    uyg = sb.satirlari_birlestir(kr)
    print(f"    UYGULAMA (satir bolumleme + x sirasi): {len(kr)} -> {len(uyg)} blok; line_boxes {[len(b.line_boxes) for b in uyg]}")
    for b in uyg:
        xs = [r.x for r in b.line_boxes]
        print(f"      blok y={b.bbox.y} x={b.bbox.x} w={b.bbox.w} h={b.bbox.h} parca x'leri {xs} artan={xs == sorted(xs)}")
    print(f"    SONUC: lafiz {'4 VERMIYOR' if len(lafzi) != 4 else '4 veriyor'}; uygulama {'4 veriyor' if len(uyg) == 4 else '4 VERMIYOR'}")

    for ad, dil in (("JP", OcrLanguage.JAPAN), ("EN", OcrLanguage.ENGLISH)):
        g = oku(FIX6 / f"dlg_{ad}.png", dil, 1200, 400)
        print(f"    dlg_{ad}: {len(g)} -> lafiz {len(paket_lafzi(g))} / uygulama {len(sb.satirlari_birlestir(g))} (no-op bekleniyor)")

    print("[B] YATAY_BOSLUK_ESIGI taramasi (modul sabiti gecici olarak degistirildi)")
    menu_kr = oku(MENU, OcrLanguage.KOREAN, 900, 300)
    menu_en = oku(MENU, OcrLanguage.ENGLISH, 900, 300)
    print(f"    menu gercek OCR: KR {len(menu_kr)} kutu, EN {len(menu_en)} kutu")
    orijinal = sb.YATAY_BOSLUK_ESIGI
    print(f"    {'esik':>6} {'dlg_KR blok':>12} {'menu KR blok':>13} {'menu KR satir/min':>18} {'menu EN blok':>13} {'menu EN satir/min':>18}  real_check #1 / #4b")
    for esik in (0.57, 0.75, 1.0, 2.0, 10.0):
        sb.YATAY_BOSLUK_ESIGI = esik  # type: ignore[misc]
        n_kr = len(sb.satirlari_birlestir(kr))
        m_kr = sb.satirlari_birlestir(menu_kr)
        m_en = sb.satirlari_birlestir(menu_en)
        r1 = "ok" if n_kr == 4 else "IHLAL"
        r4 = "ok" if satir_basina_en_az(m_kr) >= 2 and satir_basina_en_az(m_en) >= 2 else "IHLAL"
        print(f"    {esik:>6} {n_kr:>12} {len(m_kr):>13} {satir_basina_en_az(m_kr):>18} {len(m_en):>13} {satir_basina_en_az(m_en):>18}  {r1} / {r4}")
    sb.YATAY_BOSLUK_ESIGI = orijinal  # type: ignore[misc]

    print("[C] menu fixture: ayni satirda ardisik kutu ciftleri bosluk/min(h) (satir = round(y/50))")
    for ad, mb in (("KR", menu_kr), ("EN", menu_en)):
        satirlar: dict[int, list[TextBlock]] = {}
        for b in mb:
            satirlar.setdefault(round(b.bbox.y / 50), []).append(b)
        for s in sorted(satirlar):
            kutular = sorted(satirlar[s], key=lambda b: b.bbox.x)
            oranlar = []
            for a, b in zip(kutular, kutular[1:]):
                oranlar.append(round((b.bbox.x - a.bbox.right) / min(a.bbox.h, b.bbox.h), 2))
            print(f"    {ad} satir {s}: {len(kutular)} kutu, h={[b.bbox.h for b in kutular]}, bosluk/min(h)={oranlar}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
