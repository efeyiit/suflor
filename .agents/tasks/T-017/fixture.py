"""T-017 fixture -- oyun benzeri diyalog paneli (genis satir araligi), sentetik kare. Masaustu yakalanmaz.

Gercek oyunda gorulen duzen: konusmaci satiri + 4 govde satiri, satir adimi ~2.0 x satir yuksekligi
(bosluk ~1.0 x h), son satir kisa. Normalizer DIALOGUE esigi (bosluk < 0.8 x min h) burada tutmaz ->
satir satir parcalanma; kullanicinin sikayeti buydu.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from src.contracts.models import Frame, Rect

FONTLAR = {"KR": "C:/Windows/Fonts/malgun.ttf", "JP": "C:/Windows/Fonts/YuGothR.ttc"}
METIN = {
    "KR": ("엘더 마르쿠스", ["방앗간을 지나 동쪽 길로 가면 오래된 사당이 있어.",
                           "거기서 해가 지기 전에 만나자. 늦으면 문이 닫히니까",
                           "서두르는 게 좋을 거야. 아, 그리고 등불을 꼭 챙겨 와.",
                           "밤길은 위험하거든."]),
    "JP": ("長老マルクス", ["水車小屋を過ぎて東の道を行くと、古い祠がある。",
                          "日が沈む前にそこで会おう。遅れると門が閉まるから、",
                          "急いだほうがいい。ああ、それと灯りを忘れずに持ってきてくれ。",
                          "夜道は危ないからな。"]),
}


def panel(dil: str, w: int = 1500, punto: int = 36, adim_orani: float = 2.0) -> tuple[Image.Image, Rect]:
    """Diyalog paneli PNG'si ve govde metninin kutusu (panel koordinatinda)."""
    font = ImageFont.truetype(FONTLAR[dil], punto)
    konusmaci, satirlar = METIN[dil]
    adim = int(punto * adim_orani)
    h = 60 + adim + adim * len(satirlar) + 40
    img = Image.new("RGB", (w, h), (24, 28, 40))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((10, 10, w - 10, h - 10), radius=18, fill=(12, 14, 22), outline=(120, 130, 160), width=3)
    d.text((60, 40), konusmaci, font=font, fill=(255, 214, 120))
    y = 40 + adim
    for s in satirlar:
        d.text((60, y), s, font=font, fill=(235, 238, 245))
        y += adim
    return img, Rect(50, 40 + adim - 6, w - 100, adim * len(satirlar) + 12)


def sentetik_kare(dil: str, w: int, h: int, *, konum: tuple[int, int] = (80, 120),
                  adim_orani: float = 2.0) -> tuple[Frame, Rect, Rect]:
    """Tuval (w x h) + panel; (kare, panel kutusu, govde kutusu) kare koordinatinda."""
    tuval = Image.new("RGB", (w, h), (18, 22, 30))
    p, govde = panel(dil, adim_orani=adim_orani)
    if p.width > w - 160:
        olcek = (w - 160) / p.width
        p = p.resize((int(p.width * olcek), int(p.height * olcek)), Image.LANCZOS)
        govde = Rect(int(govde.x * olcek), int(govde.y * olcek), int(govde.w * olcek), int(govde.h * olcek))
    px, py = konum
    tuval.paste(p, (px, py))
    bgr = np.ascontiguousarray(np.array(tuval)[:, :, ::-1])
    kare = Frame(image=bgr, rect=Rect(0, 0, w, h), captured_at=1.0, seq=1)
    return kare, Rect(px, py, p.width, p.height), Rect(px + govde.x, py + govde.y, govde.w, govde.h)


if __name__ == "__main__":
    cikti = Path(__file__).resolve().parent / "sef_dogrulama"
    cikti.mkdir(exist_ok=True)
    for dil in ("KR", "JP"):
        panel(dil)[0].save(cikti / f"fixture_{dil}.png")
    print("fixture yazildi")
