"""T-006 kabul kapısı - GERÇEK modelle, şefin üç fixture'ı üzerinde.

    python .agents/tasks/T-006/real_check.py

Şefe aittir; implementer koşar ama YAZMAZ. Birim testleri (K1) gerçek modele
hiç dokunmaz; gerçek davranış yalnız burada ölçülür. Modeller diskte olmalı
(rapidocr ilk kullanımda indirir - O4).

Kontroller (packet.md "Kabul kapısı"):
  1. JAPAN  -> 4/4 satır birebir
  2. Aynı görüntü CHINESE -> 4/4 DEĞİL   (K2'nin pozitif kontrolü, §4.6/10)
  3. KOREAN -> okuma sırasında birleştirilince benzerlik >= 0.95
  4. ENGLISH -> 4/4
  5. Süreler K9'a göre RAPORLANIR (eşik aşımı uyarı, düşürmez)
  6. bbox ekran koordinatında: Frame.rect=(-2600,-50,…) ile ilk satır bbox.x < 0,
     ve aynı görüntü Frame.rect=(0,0,…) ile bbox.x >= 0  (iki nokta, §4.6/7)
  7. allow_download=False + model yok -> ModelMissingError (ayrı süreçte)

Bu dosya hiçbir OCR metnini stdout'a yazmaz (PROTOKOL §7); yalnızca
eşleşme sayısı ve süre yazar. Beklenen metinler burada sabit, çıktı metni
yalnız karşılaştırmada kullanılır.
"""

from __future__ import annotations

import dataclasses
import difflib
import json
import statistics
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

KOK = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(KOK))

from src.contracts.models import Frame, OcrPreset, Rect, TextBlock  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures"

BEKLENEN = {
    "JP": ["長老マルクス", "村の長老があなたを待っています。",
           "水車小屋を過ぎて東の道を行きなさい。", "日が暮れたら道を外れないように。"],
    "EN": ["ELDER MARCUS", "The village elder is waiting for you.",
           "Take the eastern road past the mill,", "and do not stray after dark."],
    "KR": ["장로 마르쿠스", "마을 장로가 당신을 기다리고 있습니다.",
           "방앗간을 지나 동쪽 길로 가십시오.", "해가 지면 길을 벗어나지 마십시오."],
}

ihlaller: list[str] = []
uyarilar: list[str] = []


def ihlal(m: str) -> None:
    ihlaller.append(m)
    print(f"  IHLAL  {m}")


def uyari(m: str) -> None:
    uyarilar.append(m)
    print(f"  UYARI  {m}")


def tamam(m: str) -> None:
    print(f"  ok     {m}")


def kare(ad: str, rect: Rect) -> Frame:
    # RGB -> BGR. `.copy()` bilerek: `ascontiguousarray` 3 kanalda takma ad sizdirir (T-005 A merceği ölçtü).
    img = np.array(Image.open(FIX / f"dlg_{ad}.png").convert("RGB"))[:, :, ::-1].copy()
    assert img.flags["C_CONTIGUOUS"] and img.flags["OWNDATA"]
    assert img.shape == (400, 1200, 3) and img.dtype == np.uint8, img.shape
    return Frame(image=img, rect=rect, captured_at=0.0, seq=0)


def okuma_sirasi(bloklar: list[TextBlock]) -> list[TextBlock]:
    """Satır kümeleme y-BOŞLUĞUNA göre; sabit kova DEĞİL.

    v1 `round(y/25)` kullanıyordu: aynı satırın kelimeleri y=212 ve 213'te kova
    sınırına bölünüyor (212->8, 213->9), bir kelime satırın önüne kaçıyordu
    (implementer tur 1'de ölçtü, şef doğruladı: KR 0.932 vs 0.971). Şimdi:
    y'ye göre sırala, bir önceki satırın y'sinden 20 px'ten fazla uzaksa yeni
    satır. Fixture'da satır aralığı 54 px, satır içi sapma <= 4 px.
    """
    if not bloklar:
        return []
    ys = sorted(bloklar, key=lambda b: b.bbox.y)
    satirlar: list[list[TextBlock]] = [[ys[0]]]
    for b in ys[1:]:
        if b.bbox.y - satirlar[-1][0].bbox.y > 20:
            satirlar.append([b])
        else:
            satirlar[-1].append(b)
    return [b for satir in satirlar for b in sorted(satir, key=lambda b: b.bbox.x)]


def bosluksuz(s: str) -> str:
    return "".join(s.split())


def satir_esle(bloklar: list[TextBlock], beklenen: list[str]) -> int:
    """Kaç beklenen satır, okunan bloklardan birine BİREBİR eşit (boşluksuz)."""
    okunan = {bosluksuz(b.text) for b in bloklar}
    return sum(1 for s in beklenen if bosluksuz(s) in okunan)


def birlesik_benzerlik(bloklar: list[TextBlock], beklenen: list[str]) -> float:
    o = bosluksuz("".join(b.text for b in okuma_sirasi(bloklar)))
    b = bosluksuz("".join(beklenen))
    return difflib.SequenceMatcher(None, o, b).ratio()


def sure_olc(motor: object, frame: Frame, n: int = 5) -> tuple[float, int]:
    from src.ocr.rapid_engine import RapidOcrEngine  # noqa: F401  (tip için)

    m = motor  # type: ignore[assignment]
    m.recognize(frame, OcrPreset.DIALOGUE)  # ısınma
    m.recognize(frame, OcrPreset.DIALOGUE)
    s: list[float] = []
    kutu = 0
    for _ in range(n):
        t0 = time.perf_counter()
        r = m.recognize(frame, OcrPreset.DIALOGUE)
        s.append((time.perf_counter() - t0) * 1000.0)
        kutu = len(r)
    return statistics.median(s), kutu


def bbox_tipleri_duz_int(bloklar: list[TextBlock]) -> bool:
    for b in bloklar:
        for alan in ("x", "y", "w", "h"):
            if type(getattr(b.bbox, alan)) is not int:
                return False
        try:
            json.dumps(dataclasses.asdict(b.bbox))
        except TypeError:
            return False
    return True


def main() -> int:
    print("T-006 real_check - gerçek model")
    try:
        from src.ocr.rapid_engine import OcrLanguage, RapidOcrEngine
    except Exception as e:  # noqa: BLE001
        ihlal(f"src.ocr.rapid_engine import edilemedi: {type(e).__name__}: {e}")
        return 1

    NEG = Rect(-2600, -50, 1200, 400, monitor_index=0)
    SIFIR = Rect(0, 0, 1200, 400, monitor_index=1)

    # --- 1. JAPAN 4/4 ---------------------------------------------------------
    jp = RapidOcrEngine(language=OcrLanguage.JAPAN, threads=8, allow_download=False)
    f_jp = kare("JP", NEG)
    b_jp = jp.recognize(f_jp, OcrPreset.DIALOGUE)
    n = satir_esle(b_jp, BEKLENEN["JP"])
    (tamam if n == 4 else ihlal)(f"[1] JAPAN: {n}/4 satır birebir  ({len(b_jp)} blok)")

    # --- 6. bbox ekran koordinatı, iki nokta ----------------------------------
    if b_jp:
        ilk = okuma_sirasi(b_jp)[0]
        # v1 burada `y < 0` da istiyordu: YAPISAL OLARAK YANLIŞ - ilk satır görüntü-yerel
        # y=93'te, rect.y=-50 ile 43 >= 0; hiçbir doğru uygulamada tutmazdı (implementer ölçtü,
        # şef doğruladı). Kaydırmanın asıl ölçüsü [6c]'nin iki-nokta farkıdır.
        (tamam if ilk.bbox.x < 0 else ihlal)(
            f"[6a] Frame.rect=(-2600,-50): ilk blok bbox.x={ilk.bbox.x} negatif olmalı (görüntü-yerel x~75)")
        (tamam if ilk.bbox.monitor_index == 0 else ihlal)(
            f"[6a] monitor_index frame'den taşındı: {ilk.bbox.monitor_index} (beklenen 0)")
        (tamam if bbox_tipleri_duz_int(b_jp) else ihlal)("[6a] tüm bbox alanları type is int, json'lanabilir")
        b_jp0 = jp.recognize(kare("JP", SIFIR), OcrPreset.DIALOGUE)
        ilk0 = okuma_sirasi(b_jp0)[0] if b_jp0 else None
        if ilk0 is None:
            ihlal("[6b] Frame.rect=(0,0) ile blok yok")
        else:
            (tamam if ilk0.bbox.x >= 0 and ilk0.bbox.y >= 0 else ihlal)(
                f"[6b] Frame.rect=(0,0): ilk blok bbox=({ilk0.bbox.x},{ilk0.bbox.y}) negatif olmamalı")
            dx, dy = ilk.bbox.x - ilk0.bbox.x, ilk.bbox.y - ilk0.bbox.y
            (tamam if (dx, dy) == (-2600, -50) else ihlal)(
                f"[6c] iki nokta farkı ({dx},{dy}) == (-2600,-50)  (kaydırma tam frame.rect kadar)")
            (tamam if ilk0.bbox.monitor_index == 1 else ihlal)(
                f"[6c] monitor_index ikinci frame'de {ilk0.bbox.monitor_index} (beklenen 1)")

    # --- 2. CHINESE aynı görüntüde 4/4 DEĞİL (pozitif kontrol) ---------------
    zh = RapidOcrEngine(language=OcrLanguage.CHINESE, threads=8, allow_download=False)
    n_zh = satir_esle(zh.recognize(f_jp, OcrPreset.DIALOGUE), BEKLENEN["JP"])
    (tamam if n_zh < 4 else ihlal)(f"[2] CHINESE modeli Japonca diyalogda {n_zh}/4 - 4 OLMAMALI (dil ölçüsü ateşliyor)")

    # --- 4. ENGLISH 4/4 -------------------------------------------------------
    en = RapidOcrEngine(language=OcrLanguage.ENGLISH, threads=8, allow_download=False)
    f_en = kare("EN", NEG)
    b_en = en.recognize(f_en, OcrPreset.DIALOGUE)
    n_en = satir_esle(b_en, BEKLENEN["EN"])
    # "ELDER MARCUS" başlığı tek kelime gibi okunabilir (O4: 'ELDERMARCUS'); boşluksuz eşleme bunu tolere eder
    (tamam if n_en == 4 else ihlal)(f"[4] ENGLISH: {n_en}/4 satır birebir  ({len(b_en)} blok)")

    # --- 3. KOREAN benzerlik >= 0.95 ------------------------------------------
    kr = RapidOcrEngine(language=OcrLanguage.KOREAN, threads=8, allow_download=False)
    f_kr = kare("KR", NEG)
    b_kr = kr.recognize(f_kr, OcrPreset.DIALOGUE)
    bz = birlesik_benzerlik(b_kr, BEKLENEN["KR"])
    (tamam if bz >= 0.95 else ihlal)(f"[3] KOREAN: birleşik benzerlik {bz:.3f} >= 0.95  ({len(b_kr)} blok)")

    # --- 5. Süreler (rapor; K9) ----------------------------------------------
    for ad, motor, f, esik in (("JAPAN", jp, f_jp, 300.0), ("ENGLISH", en, f_en, 350.0)):
        med, kutu = sure_olc(motor, f)
        (tamam if med <= esik else uyari)(f"[5] {ad}: medyan {med:.0f} ms, {kutu} kutu  (eşik {esik:.0f} ms)")
    med, kutu = sure_olc(kr, f_kr)
    kb = med / max(kutu, 1)
    (tamam if kb <= 150.0 else uyari)(f"[5] KOREAN: medyan {med:.0f} ms / {kutu} kutu = {kb:.0f} ms/kutu  (eşik 150 ms/kutu)")

    # --- K5 güven süzülmüyor: en düşük güvenli blok da listede -----------------
    # #8 (KRT-1 Y1 pozitif kontrolü): KR fixture + JAPAN modeli düşük puanlı bloklar üretir;
    # kütüphanenin Global.text_score=0.5 süzgeci AÇIKSA bunlar sessizce kaybolur.
    b_kr_jp = jp.recognize(f_kr, OcrPreset.DIALOGUE)
    dusuk = sum(1 for b in b_kr_jp if b.confidence < 0.5)
    (tamam if dusuk >= 1 else ihlal)(
        f"[8] KR+JAPAN: {len(b_kr_jp)} blok, {dusuk} tanesi confidence<0.5 - >=1 olmalı (süzgeç KAPALI kanıtı)")
    if b_kr:
        gmin = min(b.confidence for b in b_kr)
        (tamam if type(gmin) is float else ihlal)(f"[K5] confidence tipi float (min {gmin:.3f})")

    # --- 7. model yok -> ModelMissingError (ayrı süreç) -------------------------
    kod = (
        "import sys, tempfile, pathlib; sys.path.insert(0, %r)\n"
        "from src.ocr.rapid_engine import OcrLanguage, RapidOcrEngine\n"
        "from src.contracts.errors import ModelMissingError\n"
        "from src.contracts.models import Frame, Rect, OcrPreset\n"
        "import numpy as np\n"
        "d = tempfile.mkdtemp()\n"
        "m = RapidOcrEngine(language=OcrLanguage.JAPAN, threads=8, allow_download=False, model_dir=pathlib.Path(d))\n"
        "f = Frame(image=np.zeros((64,256,3),np.uint8), rect=Rect(0,0,256,64), captured_at=0.0, seq=0)\n"
        "try:\n"
        "    m.recognize(f, OcrPreset.DIALOGUE); print('HATA-YOK')\n"
        "except ModelMissingError as e:\n"
        "    print('MME', type(e.__cause__).__name__)\n"
    ) % str(KOK)
    r = subprocess.run([sys.executable, "-c", kod], capture_output=True, text=True, timeout=120, cwd=str(KOK))
    son = (r.stdout.strip().splitlines() or [""])[-1]
    if son.startswith("MME"):
        tamam(f"[7] model yok + allow_download=False -> ModelMissingError (__cause__ {son.split()[1] if len(son.split())>1 else '?'})")
    else:
        ihlal(f"[7] beklenen ModelMissingError; alınan: {son!r}  stderr: {r.stderr.strip()[-200:]}")

    print()
    if ihlaller:
        print(f"REAL_CHECK: {len(ihlaller)} IHLAL, {len(uyarilar)} uyarı")
        return 1
    print(f"REAL_CHECK: TEMİZ ({len(uyarilar)} uyarı)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
