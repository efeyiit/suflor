"""Tester-A / tur 2 / A2-1 + A2-2 -- gercek OCR (ayri surec), "referans = en kisa" kuralinin sinirlari.

    python -X utf8 .agents/tasks/T-008/tester_A/a6_tur2_gercek_ocr.py [--geometri] [a b c d]

Referans kanal (PROTOKOL 4.6/8): her sentetik fixture'da kutunun hangi CIZILEN satira ait
oldugu kutu merkezinin y'sinden ve CIZIM parametrelerinden (satir merkezleri, etiket
bolgeleri) turetilir -- uygulamanin ciktisindan DEGIL. Etiket kutusu = merkezi bir etiket
bolgesinin icinde olan kutu; satir uyeliginden MUAF (iki satirin arasindadir).

Olcu (her fixture):
  (a) YANLIS BIRLESME: bir cikti blogu iki farkli cizilen satirdan KELIME kutusu iceriyor.
  (b) YANLIS AYRILMA:  tek cizilen satirin kelime kutulari > `izin` blokta (izin: tek
      sutunlu duzende 1; etiket satirin ORTASINDA ise 2 -- K7 bosluk kurali beklenen).
Etiketin hangi bloga yapistigi serbesttir (ayri ya da bir satira yapisik).

Bolumler:
  [A] etiket koprusu varyantlari (A2-1): sagda, ortada (iki tarafta kelime), merdiven
      (satir 0 solda / satir 1 sagda), 3 satiri kaplayan, iki etiket (sol+sag), 1.2x ve
      1.5x etiket (esigin hemen ustu), etiketsiz kontroller.
  [B] "en kisa referans" siniri (A2-2): satirin altina sarkan kisa kutu (kucuk fontlu
      token, sarkma 0/4/8/12 px) + dar satir araligi; alti cizili metin; Latin g/j/y
      alt uzantili kelimeler; bagimsiz noktalama ("...", "*", tirnak) -> yanlis
      bolunme (bir satir ikiye) ya da yanlis birlesme var mi.
  [C] iki sutunlu KR menu, dar aralik (satir referansi kisa deger kutusu).
  [D] ust konumlu minik isaret kutusu (tm, (R), derece, ust simge, kesme, sapka, yildiz,
      tirnak) satir ortasinda: en kisa referans olunca sonraki titresimli kelime satiri
      BOLER mi (yanlis bolunme sinifi; tur 1 kurali bunu yapmazdi).

Stdout yalniz ASCII; OCR METNI BASILMAZ (yalniz geometri ve sayilar). `--geometri`
verilirse her fixture'in kutu listesi de basilir (sentetik teste gommek icin).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

KOK = Path(__file__).resolve().parents[4]
sys.path.insert(0, os.environ.get("TESTER_A_KOK") or str(KOK))

from src.contracts.models import Frame, OcrPreset, Rect, TextBlock  # noqa: E402
from src.ocr import satir_birlestirici as sb  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures" / "r2"
FIX.mkdir(parents=True, exist_ok=True)
KR_F = r"C:\Windows\Fonts\malgun.ttf"
EN_F = r"C:\Windows\Fonts\arial.ttf"
GEOMETRI = "--geometri" in sys.argv
ARKA = (24, 24, 40)
ON = (240, 240, 240)

ihlaller: list[str] = []
notlar: list[str] = []

KR_S1 = "\ub9c8\uc744 \uc7a5\ub85c\uac00 \ub2f9\uc2e0\uc744 \uae30\ub2e4\ub9ac\uace0 \uc788\uc2b5\ub2c8\ub2e4"
KR_S2 = "\ubb3c\ub808\ubc29\uc544\ub97c \uc9c0\ub098 \ub3d9\ucabd \uae38\ub85c \uac00\uc2ed\uc2dc\uc624"
KR_S3 = "\ud574\uac00 \uc9c0\uba74 \uae38\uc744 \ubc97\uc5b4\ub098\uc9c0 \ub9c8\uc2ed\uc2dc\uc624"
KR_ETIKET = "\uc7a5\ub85c"
KR_KISA = ["\ub9c8\uc744 \uc7a5\ub85c", "\ub2f9\uc2e0\uc744 \uae30\ub2e4\ub9b0\ub2e4"]  # kisa iki kelimelik satirlar


def oku(yol: Path, dil: object) -> list[TextBlock]:
    from src.ocr.rapid_engine import RapidOcrEngine
    img = np.array(Image.open(yol).convert("RGB"))[:, :, ::-1].copy()
    f = Frame(image=img, rect=Rect(0, 0, img.shape[1], img.shape[0]), captured_at=0.0, seq=0)
    return RapidOcrEngine(language=dil, threads=8).recognize(f, OcrPreset.DIALOGUE)  # type: ignore[arg-type]


class Sahne:
    """Bir fixture: cizim + referans kanal (satir merkezleri, etiket bolgeleri)."""

    def __init__(self, ad: str, w: int = 1200, h: int = 300) -> None:
        self.ad = ad
        self.im = Image.new("RGB", (w, h), ARKA)
        self.d = ImageDraw.Draw(self.im)
        self.merkezler: list[int] = []
        self.etiketler: list[tuple[int, int, int, int]] = []  # (x0,y0,x1,y1)

    def satir(self, x: int, y: int, metin: str, px: int, font: str = KR_F, alt_cizgi: bool = False) -> tuple[int, int, int, int]:
        f = ImageFont.truetype(font, px)
        self.d.text((x, y), metin, font=f, fill=ON)
        bb = self.d.textbbox((x, y), metin, font=f)
        if alt_cizgi:
            self.d.line((bb[0], bb[3] + 2, bb[2], bb[3] + 2), fill=ON, width=2)
        self.merkezler.append((bb[1] + bb[3]) // 2)
        return bb

    def ek(self, x: int, y: int, metin: str, px: int, font: str = KR_F) -> tuple[int, int, int, int]:
        """Var olan bir satira ek parca (satir merkezi listesine girmez)."""
        f = ImageFont.truetype(font, px)
        self.d.text((x, y), metin, font=f, fill=ON)
        return self.d.textbbox((x, y), metin, font=f)

    def etiket(self, x: int, y: int, metin: str, px: int, font: str = KR_F) -> tuple[int, int, int, int]:
        f = ImageFont.truetype(font, px)
        self.d.text((x, y), metin, font=f, fill=ON)
        bb = self.d.textbbox((x, y), metin, font=f)
        self.etiketler.append((bb[0] - 6, bb[1] - 6, bb[2] + 6, bb[3] + 6))
        return bb

    def kaydet(self) -> Path:
        yol = FIX / f"{self.ad}.png"
        self.im.save(yol)
        return yol

    def etiketsiz(self) -> Path:
        im2 = self.im.copy()
        d2 = ImageDraw.Draw(im2)
        for (x0, y0, x1, y1) in self.etiketler:
            d2.rectangle((x0, y0, x1, y1), fill=ARKA)
        yol = FIX / f"{self.ad}_etiketsiz.png"
        im2.save(yol)
        return yol


def _etiket_mi(r: Rect, etiketler: list[tuple[int, int, int, int]]) -> bool:
    cx, cy = r.x + r.w / 2, r.y + r.h / 2
    return any(x0 <= cx <= x1 and y0 <= cy <= y1 for (x0, y0, x1, y1) in etiketler)


def _satir(r: Rect, merkezler: list[int]) -> int:
    cy = r.y + r.h / 2
    return min(range(len(merkezler)), key=lambda i: abs(merkezler[i] - cy))


def degerlendir(ad: str, bl: list[TextBlock], merkezler: list[int],
                etiketler: list[tuple[int, int, int, int]] | None = None, izin: int = 1) -> list[TextBlock]:
    etiketler = etiketler or []
    c = sb.satirlari_birlestir(bl)
    lb = [len(x.line_boxes) or 1 for x in c]
    print(f"  [{ad}] {len(bl)} kutu -> {len(c)} blok; parca sayilari {lb}")
    sirali = sorted(bl, key=lambda b: (b.bbox.y, b.bbox.x))
    if GEOMETRI:
        print(f"    kutular (x,y,w,h): {[(b.bbox.x, b.bbox.y, b.bbox.w, b.bbox.h) for b in sirali]}")
    et = [b for b in bl if _etiket_mi(b.bbox, etiketler)]
    if etiketler:
        print(f"    etiket kutulari: {[(b.bbox.x, b.bbox.y, b.bbox.w, b.bbox.h) for b in et]}; satir merkezleri {merkezler}")
    kelime_satir: dict[int, int] = {}
    for b in bl:
        if b not in et:
            s = _satir(b.bbox, merkezler)
            kelime_satir[s] = kelime_satir.get(s, 0) + 1
    satir_blok: dict[int, set[int]] = {}
    yanlis_birlesme = 0
    for bi, x in enumerate(c):
        parcalar = list(x.line_boxes) if x.line_boxes else [x.bbox]
        kelime = [r for r in parcalar if not _etiket_mi(r, etiketler)]
        idx = {_satir(r, merkezler) for r in kelime}
        for s_ in idx:
            satir_blok.setdefault(s_, set()).add(bi)
        if len(idx) > 1:
            yanlis_birlesme += 1
            satirlar_x = [(_satir(r, merkezler), r.x) for r in kelime]
            print(f"    YANLIS BIRLESME: blok {bi} (x={x.bbox.x},y={x.bbox.y},w={x.bbox.w},h={x.bbox.h}) cizilen satirlar {sorted(idx)}; parca (satir,x): {satirlar_x}")
    parcalanan = {s_: sorted(v) for s_, v in satir_blok.items() if len(v) > izin}
    print(f"    cizilen satir -> kelime kutusu: {dict(sorted(kelime_satir.items()))}; kelimelerin dagildigi bloklar: {dict(sorted((k, sorted(v)) for k, v in satir_blok.items()))}")
    if parcalanan:
        print(f"    YANLIS AYRILMA (izin {izin}): {parcalanan}")
        ihlaller.append(f"{ad}: satir kelimeleri >{izin} bloga dagildi {parcalanan}")
    if yanlis_birlesme:
        ihlaller.append(f"{ad}: {yanlis_birlesme} blok iki cizilen satiri birlestirdi")
    return c


def _w(metin: str, px: int, font: str = KR_F) -> int:
    return int(ImageDraw.Draw(Image.new("RGB", (4, 4))).textlength(metin, font=ImageFont.truetype(font, px)))


def bolum_a(L: object) -> None:
    print("[A] etiket koprusu varyantlari (KR font 30; etiket 60 px dikey ortali dy=-10, tur 1 ret geometrisi)")
    f30, et_px, pitch, dy = 30, 60, 45, -10
    et_w = _w(KR_ETIKET, et_px)

    # A1 -- etiket SAGDA
    s = Sahne("r2_etiket_sagda")
    s.satir(60, 60, KR_S1, f30)
    s.satir(60, 60 + pitch, KR_S2, f30)
    sag_x = 60 + max(_w(KR_S1, f30), _w(KR_S2, f30)) + 24
    s.etiket(sag_x, 60 + dy, KR_ETIKET, et_px)
    yol = s.kaydet(); yol2 = s.etiketsiz()
    degerlendir(s.ad, oku(yol, L.KOREAN), s.merkezler, s.etiketler)
    degerlendir(s.ad + "_etiketsiz", oku(yol2, L.KOREAN), s.merkezler)

    # A2 -- etiket ORTADA, iki tarafta da kelimeler (her iki satirda)
    s = Sahne("r2_etiket_ortada_iki_taraf")
    sol1, sol2 = KR_S1.split(" ", 2), KR_S2.split(" ", 2)
    s.satir(60, 60, " ".join(sol1[:2]), f30)
    s.satir(60, 60 + pitch, " ".join(sol2[:2]), f30)
    orta_x = 60 + max(_w(" ".join(sol1[:2]), f30), _w(" ".join(sol2[:2]), f30)) + 24
    s.etiket(orta_x, 60 + dy, KR_ETIKET, et_px)
    sag_x = orta_x + et_w + 24
    s.ek(sag_x, 60, sol1[2], f30)
    s.ek(sag_x, 60 + pitch, sol2[2], f30)
    yol = s.kaydet(); yol2 = s.etiketsiz()
    degerlendir(s.ad, oku(yol, L.KOREAN), s.merkezler, s.etiketler, izin=2)
    degerlendir(s.ad + "_etiketsiz", oku(yol2, L.KOREAN), s.merkezler, izin=2)
    notlar.append("etiket ortada: satir 1'in kelimeleri etiketin iki yaninda -> K7 bosluk kurali 2 blok verir (izin 2, beklenen)")

    # A3 -- MERDIVEN: satir 0 etiketin solunda, satir 1 etiketin saginda (implementer'in 'a T | c' fixture'i)
    s = Sahne("r2_etiket_merdiven")
    s.satir(60, 60, KR_KISA[0], f30)
    orta_x = 60 + _w(KR_KISA[0], f30) + 24
    s.etiket(orta_x, 60 + dy, KR_ETIKET, et_px)
    s.satir(orta_x + et_w + 24, 60 + pitch, KR_KISA[1], f30)
    yol = s.kaydet(); yol2 = s.etiketsiz()
    degerlendir(s.ad, oku(yol, L.KOREAN), s.merkezler, s.etiketler)
    degerlendir(s.ad + "_etiketsiz", oku(yol2, L.KOREAN), s.merkezler)

    # A4 -- etiket 3 satiri kapliyor (etiket 96 px, satirlar pitch 45)
    s = Sahne("r2_etiket_3satir")
    et3_px = 96
    et3_w = _w(KR_ETIKET, et3_px)
    s.etiket(60, 60 - 22, KR_ETIKET, et3_px)
    x_m = 60 + et3_w + 24
    s.satir(x_m, 60, KR_S1, f30)
    s.satir(x_m, 60 + pitch, KR_S2, f30)
    s.satir(x_m, 60 + 2 * pitch, KR_S3, f30)
    yol = s.kaydet(); yol2 = s.etiketsiz()
    degerlendir(s.ad, oku(yol, L.KOREAN), s.merkezler, s.etiketler)
    degerlendir(s.ad + "_etiketsiz", oku(yol2, L.KOREAN), s.merkezler)

    # A5 -- iki etiket: sol + sag
    s = Sahne("r2_iki_etiket_sol_sag")
    s.etiket(60, 60 + dy, KR_ETIKET, et_px)
    x_m = 60 + et_w + 24
    s.satir(x_m, 60, KR_S1, f30)
    s.satir(x_m, 60 + pitch, KR_S2, f30)
    sag_x = x_m + max(_w(KR_S1, f30), _w(KR_S2, f30)) + 24
    s.etiket(sag_x, 60 + dy, KR_ETIKET, et_px)
    yol = s.kaydet(); yol2 = s.etiketsiz()
    degerlendir(s.ad, oku(yol, L.KOREAN), s.merkezler, s.etiketler)
    degerlendir(s.ad + "_etiketsiz", oku(yol2, L.KOREAN), s.merkezler)

    # A6 -- etiket yuksekligi satirin 1.2x / 1.5x (esigin hemen ustu); ust hizali (dy=0) ve iki satirin ortasi
    for et_px2, dy2, ad in ((36, 0, "r2_etiket_1p2_ust"), (36, 22, "r2_etiket_1p2_orta"), (45, 0, "r2_etiket_1p5_ust"), (45, 14, "r2_etiket_1p5_orta")):
        s = Sahne(ad)
        s.etiket(60, 60 + dy2, KR_ETIKET, et_px2)
        x_m = 60 + _w(KR_ETIKET, et_px2) + 24
        s.satir(x_m, 60, KR_S1, f30)
        s.satir(x_m, 60 + pitch, KR_S2, f30)
        yol = s.kaydet(); yol2 = s.etiketsiz()
        degerlendir(s.ad, oku(yol, L.KOREAN), s.merkezler, s.etiketler)
        degerlendir(s.ad + "_etiketsiz", oku(yol2, L.KOREAN), s.merkezler)
    print()


def bolum_b(L: object) -> None:
    print("[B] 'en kisa referans' siniri: satirin altina sarkan kisa kutu + dar satir araligi")
    f30 = 30
    # B1 -- satir 0 sonunda kucuk fontlu token (16 px), sarkma 0/4/8/12 px alt cizgi hizasindan asagi; pitch 36 (1.05 x kutu h ~34)
    for pitch in (36, 40):
        for sark in (0, 4, 8, 12):
            s = Sahne(f"r2_sarkan_token_p{pitch}_s{sark}")
            bb = s.satir(60, 60, KR_S1, f30)
            # kucuk token: alt kenari satirin alt kenarina + sark hizali
            f16 = ImageFont.truetype(KR_F, 16)
            tb = s.d.textbbox((0, 0), "x2", font=f16)
            ty = bb[3] + sark - (tb[3] - tb[1]) - tb[1]
            s.ek(bb[2] + 12, ty, "x2", 16)
            s.satir(60, 60 + pitch, KR_S2, f30)
            s.satir(60, 60 + 2 * pitch, KR_S3, f30)
            yol = s.kaydet()
            bl = oku(yol, L.KOREAN)
            kisa = [b for b in bl if b.bbox.h < 26]
            print(f"    kisa kutular (h<26): {[(b.bbox.x, b.bbox.y, b.bbox.w, b.bbox.h) for b in kisa]}")
            degerlendir(s.ad, bl, s.merkezler)
    # B2 -- alti cizili KR metin, pitch 36 ve 34
    for pitch in (34, 36):
        s = Sahne(f"r2_alt_cizgi_p{pitch}")
        s.satir(60, 60, KR_S1, f30, alt_cizgi=True)
        s.satir(60, 60 + pitch, KR_S2, f30, alt_cizgi=True)
        s.satir(60, 60 + 2 * pitch, KR_S3, f30, alt_cizgi=True)
        yol = s.kaydet()
        bl = oku(yol, L.KOREAN)
        kisa = [b for b in bl if b.bbox.h < 26]
        print(f"    kisa kutular (h<26): {[(b.bbox.x, b.bbox.y, b.bbox.w, b.bbox.h) for b in kisa]}")
        degerlendir(s.ad, bl, s.merkezler)
    # B3 -- KR satirinda Latin g/j/y alt uzantili kelimeler, pitch 36
    s = Sahne("r2_latin_gjy_p36")
    s.satir(60, 60, "\ub9c8\uc744 gym \uc7a5\ub85c\uac00 joy \ub2f9\uc2e0\uc744 yoga", f30)
    s.satir(60, 96, "\ubb3c\ub808\ubc29\uc544\ub97c jog \uc9c0\ub098 gyp \uac00\uc2ed\uc2dc\uc624", f30)
    s.satir(60, 132, KR_S3, f30)
    yol = s.kaydet()
    degerlendir(s.ad, oku(yol, L.KOREAN), s.merkezler)
    # B4 -- bagimsiz noktalama / kucuk isaret: "...", "*", tirnak, "-" bosluklarla ayri; pitch 36
    for ad, sat1 in (("r2_uc_nokta_p36", "\uc7a0\uae50 ... \uae30\ub2e4\ub824 \uc8fc\uc138\uc694"),
                     ("r2_yildiz_p36", "\uc544\uc774\ud15c * \ud68d\ub4dd \ud588\uc2b5\ub2c8\ub2e4 *"),
                     ("r2_tirnak_p36", "\" \ub9c8\uc744 \uc7a5\ub85c \" \uac00 \ub9d0\ud588\ub2e4"),
                     ("r2_tire_p36", "\ub9c8\uc744 - \uc7a5\ub85c - \ub2f9\uc2e0\uc744")):
        s = Sahne(ad)
        s.satir(60, 60, sat1, f30)
        s.satir(60, 96, KR_S2, f30)
        s.satir(60, 132, KR_S3, f30)
        yol = s.kaydet()
        bl = oku(yol, L.KOREAN)
        kisa = [b for b in bl if b.bbox.h < 26]
        print(f"    kisa kutular (h<26): {[(b.bbox.x, b.bbox.y, b.bbox.w, b.bbox.h) for b in kisa]}")
        degerlendir(s.ad, bl, s.merkezler)
    # B5 -- EN word boxes with descenders and quotes at narrow pitch (Arial 30, pitch 36): tespitci satir mi kelime mi verir
    s = Sahne("r2_en_gjy_quote_p36")
    s.satir(60, 60, "The \" gym \" joy of yoga is here", f30, EN_F)
    s.satir(60, 96, "Jump over the lazy dog quickly", f30, EN_F)
    s.satir(60, 132, "Every good boy deserves fudge", f30, EN_F)
    yol = s.kaydet()
    bl = oku(yol, L.ENGLISH)
    kisa = [b for b in bl if b.bbox.h < 26]
    print(f"    kisa kutular (h<26): {[(b.bbox.x, b.bbox.y, b.bbox.w, b.bbox.h) for b in kisa]}")
    degerlendir(s.ad, bl, s.merkezler)
    print()


def bolum_c(L: object) -> None:
    print("[C] iki sutunlu KR menu, dar aralik: etiket (h~37) + kisa deger kutusu (rakam, h~27), pitch 40 ve 44")
    for pitch in (40, 44):
        s = Sahne(f"r2_menu_dar_p{pitch}", 700, 260)
        for i, (et, dg) in enumerate(((("\uccb4\ub825"), "120/150"), ("\ub9c8\ub098", "40/40"), ("\ub808\ubca8", "12"), ("\uace8\ub4dc", "3400"))):
            bb = s.satir(60, 40 + i * pitch, et, 30)
            s.ek(bb[2] + 40, 40 + i * pitch, dg, 30)
        yol = s.kaydet()
        bl = oku(yol, L.KOREAN)
        degerlendir(s.ad, bl, s.merkezler, izin=2)
        c = sb.satirlari_birlestir(bl)
        birlesen = [x for x in c if len(x.line_boxes) >= 2]
        if birlesen:
            notlar.append(f"{s.ad}: etiket|deger birlesti ({len(birlesen)} blok)")
            print(f"    NOT: etiket|deger birlesti: {[(x.bbox.x, x.bbox.y, x.bbox.w, x.bbox.h) for x in birlesen]}")
    print()


def bolum_d(L: object) -> None:
    """Yanlis BOLUNME sinifi (en kisa referans, ust konumlu minik kutu): satirin ustune yakin
    minik bir isaret kutusu (h ~ 8-16) satira katilinca referans olur; ondan SONRA islenen
    (y'si daha buyuk, titresimli) ayni-satir kelimesi onunla `>= 0.5*h_minik` ortusmezse
    YENI SATIR acilir -> satir ikiye bolunur. Referans = ILK blok (tur 1) bunu yapmazdi.
    Olcu: her fixture'da minik kutu(lar) ve her biri icin 'sonra islenen ayni-satir
    kelimelerinin en kucuk ortusme payi' = min(ortusme - 0.5*h_minik) (negatifse bolunme)."""
    print("[D] ust konumlu minik isaret kutusu (yanlis bolunme sinifi), KR font 30 ve 40, pitch 1.2 x font")
    isaretler = (("tm", "™"), ("reg", "®"), ("derece", "°"), ("ust2", "²"),
                 ("kesme", "'"), ("sapka", "^"), ("yildiz", "*"), ("cift_tirnak", "\""))
    for px in (30, 40):
        pitch = int(px * 1.2)
        for ad, isaret in isaretler:
            s = Sahne(f"r2_minik_{ad}_f{px}")
            # isaret satirin ORTASINDA ve bosluklarla ayri: sonraki kelimeler ondan sonra islenebilir
            s.satir(60, 60, f"마을 {isaret} 장로가 당신을 {isaret} 기다리고 있습니다", px)
            s.satir(60, 60 + pitch, KR_S2, px)
            yol = s.kaydet()
            bl = oku(yol, L.KOREAN)
            sirali = sorted(bl, key=lambda b: (b.bbox.y, b.bbox.x))
            minik = [b for b in bl if b.bbox.h < 0.6 * px]
            paylar = []
            for m in minik:
                r = m.bbox
                sonra = [b.bbox for b in sirali if (b.bbox.y, b.bbox.x) > (r.y, r.x) and _satir(b.bbox, s.merkezler) == _satir(r, s.merkezler) and b is not m]
                if sonra:
                    en_kucuk = min(min(r.bottom, k.bottom) - max(r.y, k.y) - 0.5 * min(r.h, k.h) for k in sonra)
                    paylar.append(((r.x, r.y, r.w, r.h), len(sonra), round(en_kucuk, 1)))
                else:
                    paylar.append(((r.x, r.y, r.w, r.h), 0, None))
            print(f"    minik kutular (h<{0.6*px:.0f}) -> (kutu, sonra islenen ayni-satir kelime sayisi, en kucuk ortusme payi px; <0 = bolunme): {paylar}")
            degerlendir(s.ad, bl, s.merkezler)
    print()


def main() -> int:
    from src.ocr.rapid_engine import OcrLanguage as L
    print("Tester-A tur 2 -- gercek OCR: etiket varyantlari + 'en kisa referans' siniri")
    print()
    secim = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not secim or "a" in secim:
        bolum_a(L)
    if not secim or "b" in secim:
        bolum_b(L)
    if not secim or "c" in secim:
        bolum_c(L)
    if not secim or "d" in secim:
        bolum_d(L)
    print("NOTLAR:")
    for n in notlar:
        print("  - " + n)
    if not notlar:
        print("  (yok)")
    print()
    if ihlaller:
        print(f"A2 gercek OCR: {len(ihlaller)} ihlal:")
        for i in ihlaller:
            print("  - " + i)
        return 1
    print("A2 gercek OCR: yanlis birlesme / yanlis ayrilma YOK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
