"""T-014 kabul kapisi -- Anlik ceviri (Snapshot) GERCEK OCR + GERCEK NMT, gercek ekranda tam ekran pencere.

    python .agents/tasks/T-014/real_check.py [korean|japan]

Sefe aittir. Stdout ASCII. Kare SENTETIK (fixture diyalog kutulari 2560x1440 tuvalde) -- masaustu yakalanmaz,
ekran goruntusu masaustu icermez.
  1. AnlikAkisi.oku(kare) -> bloklar_hazir: >= 8 satir, ilk sinyal < 1500 ms; UI thread bu surede boya cizdi (paint sayaci)
  2. Pencere ekranla birebir; bloklar cizildi (grab != duz kare)
  3. Ust fixture'in bloklarina QTest surukleme -> secim 4 satir; Enter -> cevir_istendi
  4. ceviri_hazir < 3000 ms; sonuclar >= 1, Turkce metin bos degil, kaynak segment metni ceviriye esit degil
  5. Sozluk: ceviri "Marcus" iceriyor (fixture: 마르쿠스/マルクス); ekran goruntusu sef_dogrulama/anlik_sonuc_<dil>.png
  6. paintEvent 30 kare medyan < 16 ms (sonuc gosterimi dahil)
  7. Esc -> iptal 1, pencere kapandi, akis thread'i durdu
  8. Gec sonuc: yeni pencere, oku + hemen iptal -> bloklar_hazir gelmez (kural 10 pozitif kontrol: iptalsiz gelir)
"""
from __future__ import annotations

import statistics
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

KOK = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(KOK))

from PySide6 import QtCore, QtGui, QtWidgets  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402

from src.contracts.models import Frame, Rect  # noqa: E402

CIKTI = Path(__file__).resolve().parent / "sef_dogrulama"
FIX = KOK / ".agents/tasks/T-006/fixtures"
ihlaller: list[str] = []


def ihlal(m: str) -> None:
    ihlaller.append(m); print(f"  IHLAL  {m}")


def tamam(m: str) -> None:
    print(f"  ok     {m}")


def bekle(ms: int) -> None:
    son = time.perf_counter() + ms / 1000
    while time.perf_counter() < son:
        QtWidgets.QApplication.processEvents(); time.sleep(0.003)


def sentetik_kare(dil: str, w: int, h: int) -> Frame:
    tuval = Image.new("RGB", (w, h), (18, 22, 30))
    fx = Image.open(FIX / f"dlg_{dil}.png").convert("RGB")
    fw, fh = 1200, 400
    if fw > w - 120:
        olcek = (w - 120) / fw; fw, fh = int(fw * olcek), int(fh * olcek); fx = fx.resize((fw, fh), Image.LANCZOS)
    tuval.paste(fx, (60, 80))
    tuval.paste(fx, (w - fw - 60, min(h - fh - 60, 620)))
    bgr = np.ascontiguousarray(np.array(tuval)[:, :, ::-1])
    return Frame(image=bgr, rect=Rect(0, 0, w, h), captured_at=time.monotonic(), seq=1)


def main() -> int:
    dil_arg = (sys.argv[1] if len(sys.argv) > 1 else "korean").lower()
    dil_fx, nllb = ("KR", "kor_Hang") if dil_arg == "korean" else ("JP", "jpn_Jpan")
    print(f"T-014 real_check -- Snapshot modu, gercek OCR+NMT ({dil_arg})")
    try:
        from src.ocr.rapid_engine import OcrLanguage, RapidOcrEngine
        from src.pipeline.anlik import AnlikAkisi
        from src.translate.local_nmt import LocalNmtProvider
        from src.translate.sozluk import GlossaryStore
        from src.ui.anlik_pencere import AnlikDurumu, AnlikPencere
    except Exception as e:  # noqa: BLE001
        ihlal(f"import edilemedi: {type(e).__name__}"); return 1
    app = QtWidgets.QApplication(sys.argv)
    CIKTI.mkdir(exist_ok=True)
    ekran = QtGui.QGuiApplication.primaryScreen(); g = ekran.geometry(); dpr = ekran.devicePixelRatio()
    w, h = int(g.width() * dpr), int(g.height() * dpr)
    kare = sentetik_kare(dil_fx, w, h)

    ocr = RapidOcrEngine(language=OcrLanguage(dil_arg), threads=8, allow_download=True)
    nmt = LocalNmtProvider(model_dir=KOK / "models/nllb-200-distilled-600M-ct2-int8", threads=8)
    sozluk = GlossaryStore(KOK / "demo/sozluk_ornek.json")
    ocr.recognize(kare, __import__("src.contracts.models", fromlist=["OcrPreset"]).OcrPreset.DIALOGUE)  # isinma

    akis = AnlikAkisi(ocr, nmt, sozluk, kaynak_dili=nllb)
    pencere = AnlikPencere(ekran, kare)
    boya = {"n": 0}
    orijinal_paint = pencere.paintEvent

    def sayan_paint(e: QtGui.QPaintEvent) -> None:
        boya["n"] += 1; orijinal_paint(e)

    pencere.paintEvent = sayan_paint  # type: ignore[method-assign]
    akis.bloklar_hazir.connect(pencere.bloklari_goster)
    akis.ceviri_hazir.connect(pencere.ceviriyi_goster)
    akis.hata.connect(pencere.hata_goster)
    pencere.cevir_istendi.connect(akis.cevir)
    pencere.show(); pencere.activateWindow(); bekle(300)

    # 1 okuma
    t0 = time.perf_counter(); akis.oku(kare)
    boya_once = boya["n"]
    while pencere.durum == AnlikDurumu.OKUNUYOR and time.perf_counter() - t0 < 5:
        pencere.update(); bekle(20)
    okuma_ms = (time.perf_counter() - t0) * 1000
    (tamam if pencere.durum == AnlikDurumu.SECIM and len(pencere.bloklar) >= 8 and okuma_ms < 1500 else ihlal)(
        f"[1] okuma: {len(pencere.bloklar)} satir, {okuma_ms:.0f} ms (< 1500), UI bu surede {boya['n'] - boya_once} kare cizdi (> 0 = donmadi)")
    (tamam if boya["n"] - boya_once > 0 else ihlal)(f"[1b] UI thread OCR sirasinda boyadi: {boya['n'] - boya_once} kare")

    # 2 geometri + cizim
    duz = QtGui.QPixmap.fromImage(QtGui.QImage(kare.image.data, w, h, kare.image.strides[0], QtGui.QImage.Format.Format_BGR888).copy()).scaled(g.size()).toImage()
    grab = pencere.grab().toImage()
    fark = grab != duz
    (tamam if pencere.geometry() == g and fark else ihlal)(f"[2] pencere==ekran {pencere.geometry() == g}; bloklar cizildi (grab != kare) {fark}")

    # 3 secim: ust fixture bloklarini kapsayan surukleme (fixture (60,80) 1200x400 fiziksel -> mantiksal)
    x1, y1 = int(50 / dpr), int(70 / dpr); x2, y2 = int((60 + 1200 + 20) / dpr), int((80 + 400 + 20) / dpr)
    QTest.mousePress(pencere, QtCore.Qt.MouseButton.LeftButton, pos=QtCore.QPoint(x1, y1)); bekle(30)
    QTest.mouseMove(pencere, QtCore.QPoint(x2, y2)); bekle(30)
    QTest.mouseRelease(pencere, QtCore.Qt.MouseButton.LeftButton, pos=QtCore.QPoint(x2, y2)); bekle(50)
    secim = pencere.secili_bloklar()
    (tamam if 3 <= len(secim) <= 6 else ihlal)(f"[3a] surukleme secimi: {len(secim)} satir (fixture 4 satir; 3-6 kabul)")
    QTest.keyClick(pencere, QtCore.Qt.Key.Key_Return); bekle(50)
    (tamam if pencere.durum == AnlikDurumu.CEVRILIYOR else ihlal)(f"[3b] Enter -> durum {pencere.durum} (cevriliyor)")

    # 4 ceviri
    t0 = time.perf_counter()
    while pencere.durum == AnlikDurumu.CEVRILIYOR and time.perf_counter() - t0 < 10: bekle(20)
    ceviri_ms = (time.perf_counter() - t0) * 1000
    sonuclar = pencere.sonuclar()
    iyi = pencere.durum == AnlikDurumu.SONUC and len(sonuclar) >= 1 and all(c.strip() and c != k for k, c in sonuclar) and ceviri_ms < 3000
    (tamam if iyi else ihlal)(f"[4] ceviri: {len(sonuclar)} sonuc, {ceviri_ms:.0f} ms (< 3000), durum {pencere.durum}, bos/esit yok={all(c.strip() and c != k for k, c in sonuclar)}")

    # 5 sozluk + ekran goruntusu
    marcus = any("Marcus" in c for _, c in sonuclar)
    (tamam if marcus else ihlal)(f"[5] sozluk gomme sonucta: Marcus var={marcus}")
    pencere.grab().save(str(CIKTI / f"anlik_sonuc_{dil_fx}.png"))

    # 6 paint suresi
    t = []
    for _ in range(30):
        t0 = time.perf_counter(); pencere.repaint(); t.append((time.perf_counter() - t0) * 1000)
    (tamam if statistics.median(t) < 16 else ihlal)(f"[6] paintEvent 30 kare medyan {statistics.median(t):.2f} ms (< 16)")

    # 7 Esc
    iptal: list[int] = []
    pencere.iptal.connect(lambda: iptal.append(1))
    QTest.keyClick(pencere, QtCore.Qt.Key.Key_Escape); bekle(200)
    akis.kapat()
    (tamam if iptal == [1] and not pencere.isVisible() and akis.kapandi else ihlal)(f"[7] Esc: iptal={len(iptal)} (1) gorunur={pencere.isVisible()} akis kapandi={akis.kapandi}")

    # 8 gec sonuc pozitif kontrollu
    akis2 = AnlikAkisi(ocr, nmt, sozluk, kaynak_dili=nllb); gelen: list[object] = []
    akis2.bloklar_hazir.connect(gelen.append)
    akis2.oku(kare); akis2.iptal(); bekle(1500)
    n_iptal = len(gelen)
    akis2.oku(kare); bekle(1500)
    (tamam if n_iptal == 0 and len(gelen) == 1 else ihlal)(f"[8] iptal sonrasi gelen={n_iptal} (0); pozitif kontrol iptalsiz gelen={len(gelen) - n_iptal} (1)")
    akis2.kapat(); nmt.close()
    print()
    if ihlaller: print(f"REAL_CHECK: {len(ihlaller)} IHLAL"); return 1
    print("REAL_CHECK: TEMIZ"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
