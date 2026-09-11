"""Tester-A / A6 -- gercek OCR (ayri surec), kendi fixture'larim + T-006/T-008 fixture'lari.

    python .agents/tasks/T-008/tester_A/a6_gercek_ocr.py

Referans kanal (PROTOKOL 4.6/8): her sentetik fixture'da kutunun hangi CIZILEN
satira ait oldugu, kutu merkezinin y'sinden ve cizim parametrelerinden turetilir --
uygulamanin ciktisindan DEGIL. Yanlis birlesme = bir cikti blogu iki farkli cizilen
satirdan kutu iceriyor. Yanlis ayrilma = tek cizilen satirin kelime kutulari > 1
blokta kaldi (yalniz KELIME kutusu veren KR'de anlamli; EN/JP tespit satir kutusu
verdiginde ayrilma tespitcinin isidir, ayrica raporlanir).

Stdout yalniz ASCII; OCR METNI BASILMAZ (yalniz geometri, sayilar, uzunluklar).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

KOK = Path(__file__).resolve().parents[4]
# TESTER_A_KOK: `src` kopyasi (ayna) verilirse import ORADAN (aday duzeltme olcumu); fixture yollari gercek depoda kalir.
sys.path.insert(0, os.environ.get("TESTER_A_KOK") or str(KOK))

from src.contracts.models import Frame, OcrPreset, Rect, TextBlock  # noqa: E402
from src.ocr import satir_birlestirici as sb  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures"
FIX.mkdir(exist_ok=True)
T006 = KOK / ".agents" / "tasks" / "T-006" / "fixtures"
T008 = KOK / ".agents" / "tasks" / "T-008" / "fixtures"
KR_F = r"C:\Windows\Fonts\malgun.ttf"
JP_F = r"C:\Windows\Fonts\YuGothM.ttc"
EN_F = r"C:\Windows\Fonts\arial.ttf"

ihlaller: list[str] = []
notlar: list[str] = []

KR_S1 = "\ub9c8\uc744 \uc7a5\ub85c\uac00 \ub2f9\uc2e0\uc744 \uae30\ub2e4\ub9ac\uace0 \uc788\uc2b5\ub2c8\ub2e4"
KR_S2 = "\ubb3c\ub808\ubc29\uc544\ub97c \uc9c0\ub098 \ub3d9\ucabd \uae38\ub85c \uac00\uc2ed\uc2dc\uc624"
KR_S3 = "\ud574\uac00 \uc9c0\uba74 \uae38\uc744 \ubc97\uc5b4\ub098\uc9c0 \ub9c8\uc2ed\uc2dc\uc624"
KR_ETIKET = "\uc7a5\ub85c"
KR_KONUSMACI = "\uc7a5\ub85c \ub9c8\ub974\ucfe0\uc2a4"
JP_S1 = "\u6751\u306e\u9577\u8001\u304c\u3042\u306a\u305f\u3092\u5f85\u3063\u3066\u3044\u307e\u3059\u3002"
JP_S2 = "\u6c34\u8eca\u5c0f\u5c4b\u3092\u904e\u304e\u3066\u6771\u306e\u9053\u3092\u884c\u304d\u306a\u3055\u3044\u3002"
JP_S3 = "\u65e5\u304c\u6c88\u3093\u3060\u3089\u9053\u3092\u96e2\u308c\u306a\u3044\u3067\u304f\u3060\u3055\u3044\u3002"


def oku(yol: Path, dil: object) -> list[TextBlock]:
    from src.ocr.rapid_engine import RapidOcrEngine
    img = np.array(Image.open(yol).convert("RGB"))[:, :, ::-1].copy()
    f = Frame(image=img, rect=Rect(0, 0, img.shape[1], img.shape[0]), captured_at=0.0, seq=0)
    return RapidOcrEngine(language=dil, threads=8).recognize(f, OcrPreset.DIALOGUE)  # type: ignore[arg-type]


def ciz(ad: str, satirlar: list[list[tuple[int, str, int]]], font: str, w: int, h: int,
        x0: int, y0: int, pitch: int) -> tuple[Path, list[int]]:
    """satirlar: her satir [(x_ofset, metin, font_px)]. Doner: (yol, satir merkez y listesi)."""
    im = Image.new("RGB", (w, h), (24, 24, 40))
    d = ImageDraw.Draw(im)
    merkezler: list[int] = []
    for i, parcalar in enumerate(satirlar):
        y = y0 + i * pitch
        merkez = None
        for dx, t, px in parcalar:
            f = ImageFont.truetype(font, px)
            d.text((x0 + dx, y), t, font=f, fill=(240, 240, 240))
            bb = d.textbbox((x0 + dx, y), t, font=f)
            if merkez is None:
                merkez = (bb[1] + bb[3]) // 2
        merkezler.append(merkez if merkez is not None else y)
    yol = FIX / f"{ad}.png"
    im.save(yol)
    return yol, merkezler


def satir_indeksi(r: Rect, merkezler: list[int]) -> int:
    cy = r.y + r.h / 2
    return min(range(len(merkezler)), key=lambda i: abs(merkezler[i] - cy))


def geometri(bl: list[TextBlock]) -> None:
    sirali = sorted(bl, key=lambda b: (b.bbox.y, b.bbox.x))
    print(f"    kutular (x,y,w,h): {[(b.bbox.x, b.bbox.y, b.bbox.w, b.bbox.h) for b in sirali]}")
    neg = []
    for i, a in enumerate(sirali):
        for b in sirali[i + 1:]:
            ort = min(a.bbox.bottom, b.bbox.bottom) - max(a.bbox.y, b.bbox.y)
            if ort >= 0.5 * min(a.bbox.h, b.bbox.h):
                sol, sag = (a, b) if a.bbox.x <= b.bbox.x else (b, a)
                gap = sag.bbox.x - sol.bbox.right
                if gap < 0:
                    ic = sag.bbox.right <= sol.bbox.right
                    neg.append((gap, round(gap / min(a.bbox.h, b.bbox.h), 2), "IC_ICE" if ic else "cakisma"))
    print(f"    ayni-satir negatif bosluk ciftleri: {neg if neg else 'yok'}")


def degerlendir(ad: str, bl: list[TextBlock], merkezler: list[int] | None, *, tek_sutun: bool = True, etiket_x_siniri: int | None = None) -> list[TextBlock]:
    c = sb.satirlari_birlestir(bl)
    lb = [len(x.line_boxes) or 1 for x in c]
    print(f"  [{ad}] {len(bl)} kutu -> {len(c)} blok; parca sayilari {lb}")
    geometri(bl)
    if merkezler is None:
        return c
    # Referans kanal yalniz KELIME kutulari icin anlamli: iki satiri kaplayan etiket
    # kutusu (h > 1.5 x medyan h) satir indeksinden MUAF tutulur (merkezi iki satirin
    # arasindadir; ona satir atamak referansi kirletir). Etiketin hangi bloga
    # yapistigi serbesttir; olculen sey kelime kutularinin satir butunlugudur.
    # `etiket_x_siniri`: fixture'da bilinen bir etiket varsa (metin bu x'ten baslar) solundaki
    # kutular ETIKET sayilir ve referans kanalindan cikarilir (cizim parametresi, bagimsiz kanal).
    # `tek_sutun`: satirin kelime kutulari tek blokta olmali (menu/iki sutun icin KAPALI).
    yanlis_birlesme = 0
    satir_kelime_blok: dict[int, set[int]] = {}
    for bi, x in enumerate(c):
        parcalar = list(x.line_boxes) if x.line_boxes else [x.bbox]
        kelime_parcalar = [r for r in parcalar if etiket_x_siniri is None or r.x >= etiket_x_siniri]
        idx = {satir_indeksi(r, merkezler) for r in kelime_parcalar}
        for s_ in idx:
            satir_kelime_blok.setdefault(s_, set()).add(bi)
        if len(idx) > 1:
            yanlis_birlesme += 1
            print(f"    YANLIS BIRLESME: blok (x={x.bbox.x},y={x.bbox.y},w={x.bbox.w},h={x.bbox.h}) cizilen satirlar {sorted(idx)} parca={len(parcalar)} (etiket haric)")
    parcalanan = {s_: sorted(v) for s_, v in satir_kelime_blok.items() if len(v) > 1} if tek_sutun else {}
    if parcalanan:
        print(f"    YANLIS AYRILMA: cizilen satir -> kelime kutularinin dagildigi bloklar {parcalanan}")
        ihlaller.append(f"{ad}: satir kelimeleri >1 bloga dagildi {parcalanan}")
    satir_blok: dict[int, int] = {}
    satir_kutu: dict[int, int] = {}
    for x in c:
        s = satir_indeksi(x.bbox, merkezler)
        satir_blok[s] = satir_blok.get(s, 0) + 1
    for b in bl:
        s = satir_indeksi(b.bbox, merkezler)
        satir_kutu[s] = satir_kutu.get(s, 0) + 1
    print(f"    cizilen satir -> tespit kutu: {dict(sorted(satir_kutu.items()))}; birlestirme sonrasi blok: {dict(sorted(satir_blok.items()))}")
    if yanlis_birlesme:
        ihlaller.append(f"{ad}: {yanlis_birlesme} blok iki cizilen satiri birlestirdi")
    return c


def main() -> int:
    from src.ocr.rapid_engine import OcrLanguage as L
    print("Tester-A A6 -- gercek OCR, kendi fixture'larim")
    print()

    print("[0] mevcut fixture'lar: negatif bosluk (ic ice / cakisma) taramasi + birlestirme")
    for ad, yol, dil in (("dlg_KR", T006 / "dlg_KR.png", L.KOREAN), ("dlg_JP", T006 / "dlg_JP.png", L.JAPAN),
                         ("dlg_EN", T006 / "dlg_EN.png", L.ENGLISH), ("menu_KR_EN/KR", T008 / "menu_KR_EN.png", L.KOREAN),
                         ("menu_KR_EN/EN", T008 / "menu_KR_EN.png", L.ENGLISH), ("menu_KR_1em", T008 / "menu_KR_1em.png", L.KOREAN)):
        degerlendir(ad, oku(yol, dil), None)
    print()

    print("[1] dar satir araligi: font 30 px, pitch 33 px (1.1 x font) ve 30 px (1.0 x font)")
    kr3 = [[(0, KR_S1, 30)], [(0, KR_S2, 30)], [(0, KR_S3, 30)]]
    yol, m = ciz("kr_dar_1p1", kr3, KR_F, 1200, 260, 80, 60, 33)
    degerlendir("kr_dar_1p1", oku(yol, L.KOREAN), m)
    jp3 = [[(0, JP_S1, 30)], [(0, JP_S2, 30)], [(0, JP_S3, 30)]]
    yol, m = ciz("jp_dar_1p1", jp3, JP_F, 1200, 260, 80, 60, 33)
    degerlendir("jp_dar_1p1", oku(yol, L.JAPAN), m)
    yol, m = ciz("kr_dar_1p0", kr3, KR_F, 1200, 260, 80, 60, 30)
    degerlendir("kr_dar_1p0", oku(yol, L.KOREAN), m)
    print()

    print("[2] iki sutunlu EN menu: etiket|deger boslugu ~1.0 x font (30 px) ve ~1.0 x kutu h (40 px)")
    olcek = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    for gap in (30, 40):
        satirlar = []
        f = ImageFont.truetype(EN_F, 30)
        for et, dg in (("HP", "120/150"), ("MP", "40/40"), ("Level", "12"), ("Gold", "3400")):
            et_w = olcek.textlength(et, font=f)
            satirlar.append([(0, et, 30), (int(et_w) + gap, dg, 30)])
        yol, m = ciz(f"en_menu_gap{gap}", satirlar, EN_F, 900, 300, 80, 40, 56)
        c = degerlendir(f"en_menu_gap{gap}", oku(yol, L.ENGLISH), m, tek_sutun=False)
        for x in c:
            if len(x.line_boxes) >= 2:
                r = x.line_boxes
                oran = [round((r[i + 1].x - r[i].right) / min(r[i].h, r[i + 1].h), 2) for i in range(len(r) - 1)]
                print(f"    BIRLESTI: satir y={x.bbox.y} parca={len(r)} bosluk/h={oran}")
                notlar.append(f"en_menu_gap{gap}: etiket|deger birlesti (bosluk/h {oran})")
    print()

    print("[3] tek uzun satir ~2000 px (goruntu 2200 px)")
    kr_uzun = " ".join([KR_S1] * 3)
    yol, m = ciz("kr_uzun_2000", [[(0, kr_uzun, 34)]], KR_F, 2200, 140, 40, 40, 60)
    c = degerlendir("kr_uzun_2000", oku(yol, L.KOREAN), m)
    print(f"    cikti blok genislikleri: {[x.bbox.w for x in c]}")
    en_uzun = " ".join(["The village elder is waiting for you at the mill."] * 3)
    yol, m = ciz("en_uzun_2000", [[(0, en_uzun, 30)]], EN_F, 2200, 140, 40, 40, 60)
    c = degerlendir("en_uzun_2000", oku(yol, L.ENGLISH), m)
    print(f"    cikti blok genislikleri: {[x.bbox.w for x in c]}")
    print()

    print("[4] uzun kutu koprusu: solda buyuk etiket (iki satiri kaplar), sagda iki KR satiri (font 30)")
    for etiket_px, pitch in ((60, 45), (60, 40), (48, 40), (72, 48)):
        ad = f"kr_buyuk_etiket_solda_{etiket_px}_{pitch}"
        f_et = ImageFont.truetype(KR_F, etiket_px)
        et_w = int(olcek.textlength(KR_ETIKET, font=f_et))
        im = Image.new("RGB", (1200, 260), (24, 24, 40))
        d = ImageDraw.Draw(im)
        d.text((60, 60), KR_ETIKET, font=f_et, fill=(240, 240, 240))
        f30 = ImageFont.truetype(KR_F, 30)
        x_metin = 60 + et_w + 24
        d.text((x_metin, 60), KR_S1, font=f30, fill=(240, 240, 240))
        d.text((x_metin, 60 + pitch), KR_S2, font=f30, fill=(240, 240, 240))
        yol = FIX / f"{ad}.png"
        im.save(yol)
        bb0 = d.textbbox((x_metin, 60), KR_S1, font=f30)
        bb1 = d.textbbox((x_metin, 60 + pitch), KR_S2, font=f30)
        m = [(bb0[1] + bb0[3]) // 2, (bb1[1] + bb1[3]) // 2]
        bl = oku(yol, L.KOREAN)
        en_sol = min(bl, key=lambda b: b.bbox.x) if bl else None
        if en_sol is not None:
            print(f"    en soldaki kutu (x,y,w,h)={(en_sol.bbox.x, en_sol.bbox.y, en_sol.bbox.w, en_sol.bbox.h)}; cizilen satir merkezleri {m}")
        im2 = im.copy()
        ImageDraw.Draw(im2).rectangle((0, 0, x_metin - 4, 260), fill=(24, 24, 40))
        yol2 = FIX / f"{ad}_etiketsiz.png"
        im2.save(yol2)
        bl2 = oku(yol2, L.KOREAN)
        c_ile = degerlendir(ad, bl, m, etiket_x_siniri=x_metin - 4)
        c_siz = degerlendir(ad + "_etiketsiz", bl2, m)
        print(f"    etiketli {len(bl)} kutu -> {len(c_ile)} blok  |  etiketsiz {len(bl2)} kutu -> {len(c_siz)} blok")
        if len(c_ile) > len(c_siz) + 1:
            notlar.append(f"{ad}: etiketli cikti {len(c_ile)} blok, etiketsiz {len(c_siz)} (+1 etiket beklenirdi) -> satirlar PARCALANDI")
    print()


    print("[4b] uzun kutu koprusu -- etiket DIKEY ORTALI (ustu satir 0'in ustunden yukarida, alti satir 1'e sarkiyor)")
    print("     kosul: etiket kutusu satirin ILK blogu olur (en kucuk y) -> iki satir tek 'satir'a toplanir")
    for etiket_px, pitch, dy, dil_ad in ((72, 48, -14, "KR"), (60, 45, -10, "KR"), (60, 40, -8, "KR"), (72, 48, -14, "JP")):
        ad = f"{dil_ad.lower()}_etiket_ortali_{etiket_px}_{pitch}_{abs(dy)}"
        font = KR_F if dil_ad == "KR" else JP_F
        dil = L.KOREAN if dil_ad == "KR" else L.JAPAN
        etiket = KR_ETIKET if dil_ad == "KR" else "第３章"
        s1, s2 = (KR_S1, KR_S2) if dil_ad == "KR" else (JP_S1, JP_S2)
        f_et = ImageFont.truetype(font, etiket_px)
        et_w = int(olcek.textlength(etiket, font=f_et))
        im = Image.new("RGB", (1200, 260), (24, 24, 40))
        d = ImageDraw.Draw(im)
        d.text((60, 60 + dy), etiket, font=f_et, fill=(240, 240, 240))
        f30 = ImageFont.truetype(font, 30)
        x_metin = 60 + et_w + 24
        d.text((x_metin, 60), s1, font=f30, fill=(240, 240, 240))
        d.text((x_metin, 60 + pitch), s2, font=f30, fill=(240, 240, 240))
        yol = FIX / f"{ad}.png"
        im.save(yol)
        bb0 = d.textbbox((x_metin, 60), s1, font=f30)
        bb1 = d.textbbox((x_metin, 60 + pitch), s2, font=f30)
        m = [(bb0[1] + bb0[3]) // 2, (bb1[1] + bb1[3]) // 2]
        bl = oku(yol, dil)
        en_sol = min(bl, key=lambda b: b.bbox.x) if bl else None
        en_ust_y = min(b.bbox.y for b in bl) if bl else None
        if en_sol is not None:
            print(f"    etiket kutusu (x,y,w,h)={(en_sol.bbox.x, en_sol.bbox.y, en_sol.bbox.w, en_sol.bbox.h)}; en kucuk y={en_ust_y} (etiket ilk blok mu: {en_sol.bbox.y == en_ust_y}); satir merkezleri {m}")
        im2 = im.copy()
        ImageDraw.Draw(im2).rectangle((0, 0, x_metin - 4, 260), fill=(24, 24, 40))
        yol2 = FIX / f"{ad}_etiketsiz.png"
        im2.save(yol2)
        bl2 = oku(yol2, dil)
        c_ile = degerlendir(ad, bl, m, etiket_x_siniri=x_metin - 4)
        c_siz = degerlendir(ad + "_etiketsiz", bl2, m)
        print(f"    etiketli {len(bl)} kutu -> {len(c_ile)} blok  |  etiketsiz {len(bl2)} kutu -> {len(c_siz)} blok")
        for x in c_ile:
            if x.line_boxes:
                sirali_x = [r.x for r in x.line_boxes]
                satirlar_x = [satir_indeksi(r, m) for r in x.line_boxes]
                print(f"    cikti blok parca x'leri {sirali_x}; parcalarin cizilen satirlari {satirlar_x}; metin uzunlugu {len(x.text)}")
    print()
    print("[5] kontrol: standart KR, font 30, pitch 48 (1.6 x font), ustte konusmaci etiketi (26 px)")
    kr_std = [[(0, KR_KONUSMACI, 26)], [(0, KR_S1, 30)], [(0, KR_S2, 30)]]
    yol, m = ciz("kr_std", kr_std, KR_F, 1200, 260, 80, 40, 48)
    degerlendir("kr_std", oku(yol, L.KOREAN), m)
    print()

    print("NOTLAR:")
    for n in notlar:
        print("  - " + n)
    if not notlar:
        print("  (yok)")
    print()
    if ihlaller:
        print(f"A6: {len(ihlaller)} YANLIS BIRLESME sinifi:")
        for i in ihlaller:
            print("  - " + i)
        return 1
    print("A6: cizilen satirlar arasi yanlis birlesme YOK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
