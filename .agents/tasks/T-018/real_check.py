"""T-018 kabul kapisi -- oyun dilini otomatik algilama; GERCEK RapidOCR (4 model) + GERCEK NMT, gercek ekran.

    python .agents/tasks/T-018/real_check.py

Stdout ASCII. Kareler SENTETIK (T-017 fixture.py: KR/JP/ZH/EN diyalog paneli; masaustu yakalanmaz).
  1. Isitma: DilSecici.isit(3 dil) arka plan thread'inde tamamlanir (sure raporlanir)
  2. Sira KR -> JP -> JP -> ZH -> EN -> KR, baslangic Korece: her panelde dogru dil (6/6); mevcut dil dogruysa
     `denenen` 1 (ek OCR yok), yanlissa <= 4; sure raporlanir
  3. Negatif kontrol: bos kare -> belirsiz, mevcut korunur, degisti=False
  4. Ucta uca: AnlikAkisi + AnlikPencere, Japonca panel, baslangic Korece -> dil_algilandi("japan", False) bloklar_hazir'dan
     once; bloklar kana iceriyor; secim -> ceviri Turkce, bos degil; rozet "Japonca"; goruntu sef_dogrulama/dil_JP.png
  5. Ucta uca ikinci Snapshot (JP mevcut): dil_algilandi("japan") ve akisin okuma suresi tek OCR (< 1500 ms)
"""
from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

import numpy as np

KOK = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(KOK)); sys.path.insert(0, str(KOK / ".agents/tasks/T-017"))

from PySide6 import QtCore, QtGui, QtWidgets  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402

from fixture import sentetik_kare  # noqa: E402

from src.contracts.models import Frame, OcrPreset, Rect  # noqa: E402

CIKTI = Path(__file__).resolve().parent / "sef_dogrulama"
ihlaller: list[str] = []


def ihlal(m: str) -> None:
    ihlaller.append(m); print(f"  IHLAL  {m}")


def tamam(m: str) -> None:
    print(f"  ok     {m}")


def test_ekrani() -> QtGui.QScreen:
    """Kullanicinin calistigi birincil ekrana dokunma: birincil olmayan ekran varsa onu kullan (kullanici istegi)."""
    birincil = QtGui.QGuiApplication.primaryScreen()
    return next((s for s in QtGui.QGuiApplication.screens() if s is not birincil), birincil)


def bekle(ms: int) -> None:
    son = time.perf_counter() + ms / 1000
    while time.perf_counter() < son:
        QtWidgets.QApplication.processEvents(); time.sleep(0.003)


def main() -> int:
    print("T-018 real_check -- otomatik dil algilama (gercek OCR x4 + NMT)")
    from src.ocr.dil_algila import EMIN_ESIGI
    from src.ocr.rapid_engine import OcrLanguage, RapidOcrEngine
    from src.pipeline.anlik import AnlikAkisi, oku_yap
    from src.pipeline.dil_secici import DilSecici
    from src.translate.local_nmt import LocalNmtProvider
    from src.ui.anlik_pencere import AnlikDurumu, AnlikPencere

    KR, JP, ZH, EN = OcrLanguage.KOREAN, OcrLanguage.JAPAN, OcrLanguage.CHINESE, OcrLanguage.ENGLISH
    NLLB = {KR: "kor_Hang", JP: "jpn_Jpan", ZH: "zho_Hans", EN: "eng_Latn"}
    app = QtWidgets.QApplication(sys.argv)
    CIKTI.mkdir(exist_ok=True)
    ekran = test_ekrani(); g = ekran.geometry(); dpr = ekran.devicePixelRatio()
    w, h = int(g.width() * dpr), int(g.height() * dpr)
    kareler = {ad: sentetik_kare(ad, w, h, adim_orani=2.0) for ad in ("KR", "JP", "ZH", "EN")}
    dil_kodu = {"KR": KR, "JP": JP, "ZH": ZH, "EN": EN}

    secici = DilSecici(lambda d: RapidOcrEngine(language=d, threads=8, allow_download=True), NLLB, baslangic=KR)
    secici.isit([KR])   # kabukta depo kurulumu: mevcut dil once

    # 1 isitma (arka plan)
    t0 = time.perf_counter()
    t = threading.Thread(target=secici.isit, args=([JP, ZH, EN],), daemon=True); t.start(); t.join(60)
    isitma_ms = (time.perf_counter() - t0) * 1000
    (tamam if not t.is_alive() else ihlal)(f"[1] 3 modelin isitilmasi {isitma_ms:.0f} ms (arka plan, UI'yi bloklamaz)")

    # 2 sira
    sira = ["KR", "JP", "JP", "ZH", "EN", "KR"]
    dogru = 0
    for ad in sira:
        kare, _, _ = kareler[ad]
        onceki = secici.mevcut
        t0 = time.perf_counter()
        bloklar = oku_yap(secici.motor(onceki), kare, OcrPreset.DIALOGUE)
        ilk_ms = (time.perf_counter() - t0) * 1000
        t0 = time.perf_counter()
        secim = secici.sec(kare, bloklar, OcrPreset.DIALOGUE)
        sec_ms = (time.perf_counter() - t0) * 1000
        beklenen = dil_kodu[ad]
        dogru_mu = secim.dil is beklenen and secici.mevcut is beklenen
        denenen_iyi = (len(secim.karar.denenen) == 1) if onceki is beklenen else (len(secim.karar.denenen) <= 4 and secim.degisti)
        puan = {p.dil.value[:2]: round(p.puan, 2) for p in secim.karar.puanlar}
        dogru += int(dogru_mu and denenen_iyi)
        (tamam if dogru_mu and denenen_iyi else ihlal)(
            f"[2] panel {ad}, mevcut {onceki.value}: secilen {secim.dil.value} (dogru={dogru_mu}), denenen {len(secim.karar.denenen)}, "
            f"ilk okuma {ilk_ms:.0f} ms + secim {sec_ms:.0f} ms, puanlar {puan}")
    (tamam if dogru == len(sira) else ihlal)(f"[2t] {dogru}/{len(sira)} dogru")

    # 3 negatif kontrol
    bos = Frame(image=np.full((h, w, 3), 20, dtype=np.uint8), rect=Rect(0, 0, w, h), captured_at=1.0, seq=1)
    onceki = secici.mevcut
    bloklar = oku_yap(secici.motor(onceki), bos, OcrPreset.DIALOGUE)
    secim = secici.sec(bos, bloklar, OcrPreset.DIALOGUE)
    (tamam if secim.belirsiz and not secim.degisti and secici.mevcut is onceki else ihlal)(
        f"[3] bos kare: belirsiz={secim.belirsiz} degisti={secim.degisti} mevcut korundu={secici.mevcut is onceki}")

    # 4 ucta uca: Japonca panel, baslangic Korece
    secici2 = DilSecici(lambda d: secici.motor(d), NLLB, baslangic=KR)
    nmt = LocalNmtProvider(model_dir=KOK / "models/nllb-200-distilled-600M-ct2-int8", threads=8)
    kare, _, govde = kareler["JP"]
    akis = AnlikAkisi(secici2.motor(KR), nmt, None, kaynak_dili=NLLB[KR], dil_secici=secici2)
    pencere = AnlikPencere(ekran, kare)
    olaylar: list[str] = []
    akis.dil_algilandi.connect(lambda d, b: olaylar.append(f"dil:{d}:{b}"))
    akis.dil_algilandi.connect(pencere.dil_goster)
    akis.bloklar_hazir.connect(lambda bl: olaylar.append("bloklar"))
    akis.bloklar_hazir.connect(pencere.bloklari_goster)
    akis.ceviri_hazir.connect(pencere.ceviriyi_goster)
    akis.hata.connect(pencere.hata_goster)
    pencere.cevir_istendi.connect(akis.cevir)
    pencere.show(); pencere.activateWindow(); bekle(300)
    t0 = time.perf_counter(); akis.oku(kare)
    while pencere.durum == AnlikDurumu.OKUNUYOR and time.perf_counter() - t0 < 15: bekle(20)
    okuma_ms = (time.perf_counter() - t0) * 1000
    kana = any(0x3040 <= ord(c) <= 0x30FF for b in pencere.bloklar for c in b.text)
    (tamam if olaylar == ["dil:japan:False", "bloklar"] and kana and pencere.dil_metni == "Japonca" else ihlal)(
        f"[4a] olaylar {olaylar} (dil once, bloklar sonra), bloklar kana iceriyor={kana}, rozet={pencere.dil_metni!r}, {okuma_ms:.0f} ms")

    def pw(x: float, y: float) -> QtCore.QPoint:
        return QtCore.QPoint(int(x / dpr), int(y / dpr))
    QTest.mousePress(pencere, QtCore.Qt.MouseButton.LeftButton, pos=pw(govde.x - 10, govde.y - 4)); bekle(20)
    QTest.mouseMove(pencere, pw(govde.x + govde.w + 10, govde.y + govde.h + 4)); bekle(20)
    QTest.mouseRelease(pencere, QtCore.Qt.MouseButton.LeftButton, pos=pw(govde.x + govde.w + 10, govde.y + govde.h + 4))
    t0 = time.perf_counter()
    while pencere.durum != AnlikDurumu.SONUC and time.perf_counter() - t0 < 15: bekle(20)
    sonuclar = pencere.sonuclar()
    turkce = bool(sonuclar) and all(c.strip() and c != k and not any(0x3040 <= ord(ch) <= 0x30FF for ch in c) for k, c in sonuclar)
    (tamam if pencere.durum == AnlikDurumu.SONUC and turkce else ihlal)(
        f"[4b] ceviri: {len(sonuclar)} sonuc, Turkce (kana yok, kaynaktan farkli)={turkce}, {(time.perf_counter() - t0) * 1000:.0f} ms")
    pencere.grab().save(str(CIKTI / "dil_JP.png"))
    pencere.close(); bekle(100); akis.kapat()

    # 5 ikinci Snapshot: JP mevcut -> tek OCR
    akis2 = AnlikAkisi(secici2.motor(secici2.mevcut), nmt, None, kaynak_dili=NLLB[secici2.mevcut], dil_secici=secici2)
    olay2: list[str] = []
    akis2.dil_algilandi.connect(lambda d, b: olay2.append(f"dil:{d}:{b}"))
    geldi: list[int] = []
    akis2.bloklar_hazir.connect(lambda bl: geldi.append(len(bl)))
    t0 = time.perf_counter(); akis2.oku(kare)
    while not geldi and time.perf_counter() - t0 < 10: bekle(10)
    ms2 = (time.perf_counter() - t0) * 1000
    (tamam if olay2 == ["dil:japan:False"] and geldi and ms2 < 1500 else ihlal)(f"[5] ikinci Snapshot: {olay2}, {geldi} blok, {ms2:.0f} ms (< 1500, tek OCR)")
    akis2.kapat(); nmt.close()
    print()
    if ihlaller:
        print(f"REAL_CHECK: {len(ihlaller)} IHLAL"); return 1
    print("REAL_CHECK: TEMIZ"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
