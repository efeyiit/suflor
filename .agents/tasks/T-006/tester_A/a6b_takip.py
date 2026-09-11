"""Tester-A takip: D2 benzerlik orani (metinsiz), D10 dort dilde allow_download=True cevrimdisi (K11 tablosu gercek yolda), D11 sure/boyut."""
from __future__ import annotations
import difflib, statistics, sys, time
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
KOK = Path(__file__).resolve().parents[4]; sys.path.insert(0, str(KOK))
sys.stdout.reconfigure(encoding="utf-8")
from src.contracts.models import Frame, OcrPreset, Rect
from src.ocr.rapid_engine import OcrLanguage, RapidOcrEngine
FIX = KOK / ".agents/tasks/T-006/fixtures"
GOTHIC = "C:/Windows/Fonts/msgothic.ttc"; ARIAL = "C:/Windows/Fonts/arial.ttf"
JP_UZUN = "村の長老があなたを待っています。"
def render(w, h, metin, font, px, xy):
    im = Image.new("RGB", (w, h), (24, 24, 40)); ImageDraw.Draw(im).text(xy, metin, font=ImageFont.truetype(font, px), fill=(240, 240, 240))
    return np.array(im)[:, :, ::-1].copy()
def fr(img): h, w = img.shape[:2]; return Frame(image=img, rect=Rect(0, 0, w, h), captured_at=0.0, seq=0)
def bs(s): return "".join(s.split())
def fixture(ad): return np.array(Image.open(FIX / f"dlg_{ad}.png").convert("RGB"))[:, :, ::-1].copy()
BEK = {"JP": ["長老マルクス", "村の長老があなたを待っています。", "水車小屋を過ぎて東の道を行きなさい。", "日が暮れたら道を外れないように。"],
       "EN": ["ELDER MARCUS", "The village elder is waiting for you.", "Take the eastern road past the mill,", "and do not stray after dark."],
       "KR": ["장로 마르쿠스", "마을 장로가 당신을 기다리고 있습니다.", "방앗간을 지나 동쪽 길로 가십시오.", "해가 지면 길을 벗어나지 마십시오."]}
def esle(bl, bek):
    ok = {bs(b.text) for b in bl}; return sum(1 for s in bek if bs(s) in ok)
def sure(m, f, n=5):
    m.recognize(f, OcrPreset.DIALOGUE); s = []
    for _ in range(n):
        t0 = time.perf_counter(); m.recognize(f, OcrPreset.DIALOGUE); s.append((time.perf_counter() - t0) * 1000)
    return statistics.median(s)

jp = RapidOcrEngine(language=OcrLanguage.JAPAN, threads=8)
# D2 takip
b = jp.recognize(fr(render(2560, 1440, JP_UZUN, GOTHIC, 40, (300, 1200))), OcrPreset.DIALOGUE)
o = bs("".join(x.text for x in b)); e = bs(JP_UZUN)
print(f"D2 takip: okunan uzunluk {len(o)} vs beklenen {len(e)}; benzerlik {difflib.SequenceMatcher(None, o, e).ratio():.3f}; farkli opcode'lar: {[(t, i2-i1, j2-j1) for t,i1,i2,j1,j2 in difflib.SequenceMatcher(None,o,e).get_opcodes() if t!='equal']}")
for px in (28, 48, 64):
    b = jp.recognize(fr(render(2560, 1440, JP_UZUN, GOTHIC, px, (300, 1200))), OcrPreset.DIALOGUE)
    o = bs("".join(x.text for x in b)); print(f"D2 takip {px}px: {len(b)} blok, benzerlik {difflib.SequenceMatcher(None, o, e).ratio():.3f}, birebir={o==e}")
# aynı cümle şefin fixture'ında 4/4 idi -> fixture fontu/boyutu farklı; 1200x400'de aynı fontla dene
b = jp.recognize(fr(render(1200, 400, JP_UZUN, GOTHIC, 40, (80, 150))), OcrPreset.DIALOGUE)
o = bs("".join(x.text for x in b)); print(f"D2 takip 1200x400 msgothic 40px: {len(b)} blok, benzerlik {difflib.SequenceMatcher(None, o, e).ratio():.3f}, birebir={o==e}")

# D10 dört dil allow_download=True, ağ kapalı -> K11 tablosu gerçek çözücüyle dosyaya çözülüyor mu (pozitif kontrol: dosyalar yerelde)
import requests
def _kapali(*a, **k): raise requests.ConnectionError("tester-A: ag kapali")
requests.get = _kapali
for dil, fx, bek in (("japan","JP",BEK["JP"]),("english","EN",BEK["EN"]),("korean","KR",BEK["KR"]),("chinese","JP",BEK["JP"])):
    m = RapidOcrEngine(language=OcrLanguage(dil), threads=8, allow_download=True)
    try:
        bl = m.recognize(fr(fixture(fx)), OcrPreset.DIALOGUE)
        ek = f"{esle(bl, bek)}/4 satir" if dil != "korean" else f"birlesik benzerlik {difflib.SequenceMatcher(None, bs(''.join(x.text for x in sorted(bl, key=lambda x:(x.bbox.y//40, x.bbox.x)))), bs(''.join(bek))).ratio():.3f}"
        print(f"D10 {dil} allow_download=True ag KAPALI fixture {fx}: kuruldu, {len(bl)} blok, {ek}")
    except Exception as e:
        print(f"D10 {dil}: {type(e).__name__} cause={type(e.__cause__).__name__}")

# D11 süre / boyut (aynı süreç, tek satır)
en = RapidOcrEngine(language=OcrLanguage.ENGLISH, threads=8)
for (w,h,px,xy) in ((300,80,14,(12,30)),(600,160,20,(20,60)),(1200,400,28,(80,150)),(2560,1440,40,(300,1200))):
    img = render(w,h,"Press A to continue",ARIAL,px,xy)
    print(f"D11 EN {w}x{h} {px}px tek satir: medyan {sure(en, fr(img)):.0f} ms, {len(en.recognize(fr(img), OcrPreset.DIALOGUE))} blok")
print(f"D11 EN fixture 1200x400 4 satir: medyan {sure(en, fr(fixture('EN'))):.0f} ms")
