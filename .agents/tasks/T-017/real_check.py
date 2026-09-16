"""T-017 kabul kapisi -- secim = BUTUN metin + Enter'siz (kendiliginden) ceviri; GERCEK OCR + GERCEK NMT, gercek ekran.

    python .agents/tasks/T-017/real_check.py [korean|japan]

Stdout ASCII. Kare SENTETIK (fixture.py: oyun benzeri panel, satir adimi 2.4 x punto -- kullanici sikayetini
yeniden ureten duzen; masaustu yakalanmaz).
  1. oku -> >= 5 satir, < 1500 ms
  2. Govde uzerine QTest surukleme -> secim 4-8 blok; ENTER YOK
  3. Kendiliginden: <= OTOMATIK_CEVIRI_MS + 300 ms icinde durum cevriliyor (T-017 K3)
  4. ceviri_hazir < 4000 ms; TAM 1 sonuc (govde tek metin); kaynak 4 satirin hepsini iceriyor; ceviri bos degil,
     kaynaktan farkli, satir kirigi yok. MUTANT: ayni secimde eski yol `normalize` >= 3 parca verir (kapi ayirt eder)
  5. Konusmaci satirina tik -> sonuclar silinir, kendiliginden yeniden ceviri -> 2 sonuc (konusmaci + govde);
     sozluk: ceviride "Marcus" var. Ekran goruntusu sef_dogrulama/anlik_butun_<dil>.png
  6. Sag tik: bir satiri tikla (secim degisti, sayac calisiyor) + hemen sag tik -> < 50 ms icinde cevriliyor
  7. Esc -> iptal 1, pencere kapandi, akis durdu; sayac sonrasi sinyal yok
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

KOK = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(KOK)); sys.path.insert(0, str(Path(__file__).resolve().parent))

from PySide6 import QtCore, QtGui, QtWidgets  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402

from fixture import sentetik_kare  # noqa: E402

from src.contracts.models import OcrPreset  # noqa: E402

CIKTI = Path(__file__).resolve().parent / "sef_dogrulama"
ihlaller: list[str] = []


def ihlal(m: str) -> None:
    ihlaller.append(m); print(f"  IHLAL  {m}")


def tamam(m: str) -> None:
    print(f"  ok     {m}")


def bekle(ms: int) -> None:
    son = time.perf_counter() + ms / 1000
    while time.perf_counter() < son:
        QtWidgets.QApplication.processEvents(); time.sleep(0.003)


def bekle_durum(pencere: object, durum: object, ms: int) -> float:
    t0 = time.perf_counter()
    while getattr(pencere, "durum") != durum and (time.perf_counter() - t0) * 1000 < ms:
        bekle(10)
    return (time.perf_counter() - t0) * 1000


def main() -> int:
    dil_arg = (sys.argv[1] if len(sys.argv) > 1 else "korean").lower()
    dil_fx, nllb = ("KR", "kor_Hang") if dil_arg == "korean" else ("JP", "jpn_Jpan")
    print(f"T-017 real_check -- secim = butun metin, Enter'siz ceviri ({dil_arg})")
    from src.ocr.normalizer import normalize
    from src.ocr.rapid_engine import OcrLanguage, RapidOcrEngine
    from src.pipeline.anlik import AnlikAkisi, ikinci_gecis
    from src.translate.local_nmt import LocalNmtProvider
    from src.translate.sozluk import GlossaryStore
    from src.ui.anlik_pencere import OTOMATIK_CEVIRI_MS, AnlikDurumu, AnlikPencere

    app = QtWidgets.QApplication(sys.argv)
    CIKTI.mkdir(exist_ok=True)
    ekran = QtGui.QGuiApplication.primaryScreen(); g = ekran.geometry(); dpr = ekran.devicePixelRatio()
    w, h = int(g.width() * dpr), int(g.height() * dpr)
    kare, panel, govde = sentetik_kare(dil_fx, w, h, adim_orani=2.4)

    ocr = RapidOcrEngine(language=OcrLanguage(dil_arg), threads=8, allow_download=True)
    nmt = LocalNmtProvider(model_dir=KOK / "models/nllb-200-distilled-600M-ct2-int8", threads=8)
    sozluk = GlossaryStore(KOK / "demo/sozluk_ornek.json")
    ocr.recognize(kare, OcrPreset.DIALOGUE)  # isinma

    akis = AnlikAkisi(ocr, nmt, sozluk, kaynak_dili=nllb)
    pencere = AnlikPencere(ekran, kare)
    akis.bloklar_hazir.connect(pencere.bloklari_goster)
    akis.ceviri_hazir.connect(pencere.ceviriyi_goster)
    akis.hata.connect(pencere.hata_goster)
    pencere.cevir_istendi.connect(akis.cevir)
    istekler: list[int] = []
    pencere.cevir_istendi.connect(lambda bl: istekler.append(len(bl)))
    pencere.show(); pencere.activateWindow(); bekle(300)

    # 1 okuma
    akis.oku(kare)
    okuma_ms = bekle_durum(pencere, AnlikDurumu.SECIM, 5000)
    (tamam if pencere.durum == AnlikDurumu.SECIM and len(pencere.bloklar) >= 5 and okuma_ms < 1500 else ihlal)(
        f"[1] okuma: {len(pencere.bloklar)} satir, {okuma_ms:.0f} ms (< 1500)")

    # 2 govde secimi (kare -> pencere: /dpr), Enter YOK
    def pw(x: float, y: float) -> QtCore.QPoint:
        return QtCore.QPoint(int(x / dpr), int(y / dpr))

    QTest.mousePress(pencere, QtCore.Qt.MouseButton.LeftButton, pos=pw(govde.x - 10, govde.y - 4)); bekle(20)
    QTest.mouseMove(pencere, pw(govde.x + govde.w + 10, govde.y + govde.h + 4)); bekle(20)
    t_birak = time.perf_counter()
    QTest.mouseRelease(pencere, QtCore.Qt.MouseButton.LeftButton, pos=pw(govde.x + govde.w + 10, govde.y + govde.h + 4))
    secim = pencere.secili_bloklar()
    (tamam if 4 <= len(secim) <= 8 and pencere.durum == AnlikDurumu.SECIM else ihlal)(
        f"[2] surukleme: {len(secim)} blok secildi (4-8), durum {pencere.durum}, Enter basilmadi")

    # 3 kendiliginden ceviri
    bekle_durum(pencere, AnlikDurumu.CEVRILIYOR, OTOMATIK_CEVIRI_MS + 300)
    gecen = (time.perf_counter() - t_birak) * 1000
    (tamam if pencere.durum == AnlikDurumu.CEVRILIYOR and istekler == [len(secim)] else ihlal)(
        f"[3] birakmadan {gecen:.0f} ms sonra kendiliginden cevriliyor (<= {OTOMATIK_CEVIRI_MS + 300}); istek={istekler}")

    # 4 tek sonuc, butun metin
    ceviri_ms = bekle_durum(pencere, AnlikDurumu.SONUC, 10000)
    sonuclar = pencere.sonuclar()
    siki = ikinci_gecis(ocr, kare, secim, OcrPreset.DIALOGUE)
    eski_parca = len(normalize(siki, OcrPreset.DIALOGUE))
    kaynak = sonuclar[0][0] if sonuclar else ""
    hepsi = all(b.text.strip() and b.text.strip() in kaynak for b in siki)
    ceviri = sonuclar[0][1] if sonuclar else ""
    kirik_yok = "\n" not in ceviri
    iyi = (pencere.durum == AnlikDurumu.SONUC and len(sonuclar) == 1 and hepsi and bool(ceviri.strip()) and ceviri != kaynak
           and kirik_yok and ceviri_ms < 4000)
    (tamam if iyi else ihlal)(f"[4] ceviri {ceviri_ms:.0f} ms (< 4000): {len(sonuclar)} sonuc (1), kaynak {len(siki)} satirin hepsini iceriyor={hepsi}, "
                              f"ceviri {len(ceviri)} kr, kaynaktan farkli={ceviri != kaynak}, satir kirigi yok={kirik_yok}")
    (tamam if eski_parca >= 3 else ihlal)(f"[4m] MUTANT: eski yol normalize ayni secimi {eski_parca} parcaya bolerdi (>= 3 -> kapi ayirt eder)")

    # 5 konusmaci satirini ekle -> yeniden ceviri, 2 sonuc, Marcus
    konusmaci = [b for b in pencere.bloklar if b.bbox.y < govde.y]
    if not konusmaci:
        ihlal("[5] konusmaci satiri bulunamadi")
    else:
        k = konusmaci[0]
        istekler.clear()
        QTest.mouseClick(pencere, QtCore.Qt.MouseButton.LeftButton, pos=pw(k.bbox.x + k.bbox.w / 2, k.bbox.y + k.bbox.h / 2))
        temiz = pencere.sonuclar() == [] and pencere.durum == AnlikDurumu.SECIM
        bekle_durum(pencere, AnlikDurumu.CEVRILIYOR, OTOMATIK_CEVIRI_MS + 300)
        bekle_durum(pencere, AnlikDurumu.SONUC, 10000)
        sonuclar = pencere.sonuclar()
        marcus = any("Marcus" in c for _, c in sonuclar)
        (tamam if temiz and len(sonuclar) == 2 and istekler == [len(secim) + 1] and marcus else ihlal)(
            f"[5] konusmaci tiki: eski sonuc silindi={temiz}, yeniden istek={istekler}, {len(sonuclar)} sonuc (2), Marcus={marcus}")
        pencere.grab().save(str(CIKTI / f"anlik_butun_{dil_fx}.png"))

    # 6 sag tik hemen cevirir
    son_satir = max(secim, key=lambda b: b.bbox.y)
    istekler.clear()
    QTest.mouseClick(pencere, QtCore.Qt.MouseButton.LeftButton, pos=pw(son_satir.bbox.x + 20, son_satir.bbox.y + son_satir.bbox.h / 2))   # kaldir
    t0 = time.perf_counter()
    QTest.mouseClick(pencere, QtCore.Qt.MouseButton.RightButton, pos=pw(20, 20))
    sag_ms = (time.perf_counter() - t0) * 1000
    (tamam if pencere.durum == AnlikDurumu.CEVRILIYOR and sag_ms < 50 and len(istekler) == 1 else ihlal)(
        f"[6] sag tik: {sag_ms:.1f} ms icinde cevriliyor (< 50), istek={istekler}")
    bekle_durum(pencere, AnlikDurumu.SONUC, 10000)
    bekle(OTOMATIK_CEVIRI_MS + 200)
    (tamam if len(istekler) == 1 else ihlal)(f"[6b] sayac iptal edildi: toplam istek {len(istekler)} (1)")

    # 7 Esc
    iptal: list[int] = []
    pencere.iptal.connect(lambda: iptal.append(1))
    istekler.clear()
    QTest.keyClick(pencere, QtCore.Qt.Key.Key_Escape); bekle(OTOMATIK_CEVIRI_MS + 200)
    akis.kapat()
    (tamam if iptal == [1] and not pencere.isVisible() and akis.kapandi and istekler == [] else ihlal)(
        f"[7] Esc: iptal={len(iptal)} (1) gorunur={pencere.isVisible()} akis kapandi={akis.kapandi} kapanis sonrasi istek={istekler}")
    nmt.close()
    print()
    if ihlaller:
        print(f"REAL_CHECK: {len(ihlaller)} IHLAL"); return 1
    print("REAL_CHECK: TEMIZ"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
