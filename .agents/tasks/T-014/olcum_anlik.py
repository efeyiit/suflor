"""T-014 on olcum -- Snapshot (anlik ceviri) modu: tam ekran yakala + OCR + secim + ceviri suresi.

    python .agents/tasks/T-014/olcum_anlik.py

A1 capture_full(birincil) suresi ve kare boyutu
A2 tam kare (2560x1440 sentetik: KR/JP diyalog fixture'lari 3 boyda) OCR suresi ve blok sayisi -- dilogue on ayari
A3 ayni kare, 1280 genislige kucultulmus: sure ve kayip (kucuk metin okunuyor mu)
A4 secilen 2 blok -> satirlari_birlestir -> normalize -> sozluk -> NMT suresi (soguk/sicak)
A5 tam ekran QImage gosterimi: 2560x1440 BGR -> QImage -> QPixmap donusum suresi (UI thread butcesi)
Stdout ASCII; metin basilmaz (sayilar).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

KOK = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(KOK))

from PIL import Image  # noqa: E402

from src.capture.service import CaptureService, MssBackend  # noqa: E402
from src.contracts.models import Frame, OcrPreset, Rect, TranslationRequest  # noqa: E402
from src.ocr.normalizer import normalize  # noqa: E402
from src.ocr.rapid_engine import OcrLanguage, RapidOcrEngine  # noqa: E402
from src.ocr.satir_birlestirici import satirlari_birlestir  # noqa: E402
from src.translate.local_nmt import LocalNmtProvider  # noqa: E402
from src.translate.sozluk import GlossaryStore, terimleri_gom  # noqa: E402

CIKTI = Path(__file__).resolve().parent
FIX = KOK / ".agents/tasks/T-006/fixtures"
satirlar: list[str] = []


def olgu(m: str) -> None:
    satirlar.append(m); print(" ", m)


def sentetik_kare(dil: str, olcek: float) -> Frame:
    """2560x1440 koyu tuval; diyalog fixture'i (1200x400) verilen olcekle 3 yere yerlestirilir."""
    tuval = Image.new("RGB", (2560, 1440), (18, 22, 30))
    fx = Image.open(FIX / f"dlg_{dil}.png").convert("RGB")
    w, h = int(1200 * olcek), int(400 * olcek)
    fx = fx.resize((w, h), Image.LANCZOS)
    for (x, y) in ((60, 80), (2560 - w - 60, 520), (680, 1440 - h - 60)):
        tuval.paste(fx, (x, y))
    bgr = np.ascontiguousarray(np.array(tuval)[:, :, ::-1])
    return Frame(image=bgr, rect=Rect(0, 0, 2560, 1440), captured_at=time.monotonic(), seq=0)


def main() -> int:
    servis = CaptureService(MssBackend())
    t0 = time.perf_counter(); kare = servis.capture_full(0); t1 = time.perf_counter()
    olgu(f"A1 capture_full(0): {(t1 - t0) * 1000:.1f} ms, kare {kare.rect.w}x{kare.rect.h}, dtype={kare.image.dtype} shape={kare.image.shape}")

    for dil, ocr_dil in (("KR", OcrLanguage.KOREAN), ("JP", OcrLanguage.JAPAN)):
        motor = RapidOcrEngine(language=ocr_dil, threads=8, allow_download=True)
        for olcek in (1.0, 0.6, 0.4):
            k = sentetik_kare(dil, olcek)
            motor.recognize(k, OcrPreset.DIALOGUE)  # isinma (ilk cagri model yukler)
            t0 = time.perf_counter(); bloklar = motor.recognize(k, OcrPreset.DIALOGUE); t1 = time.perf_counter()
            birlesik = satirlari_birlestir(bloklar)
            yuk = sum(1 for b in birlesik if b.bbox.y < 500)  # ust bolgedeki fixture
            olgu(f"A2 {dil} tam kare olcek {olcek}: OCR {(t1 - t0) * 1000:.0f} ms, {len(bloklar)} blok -> {len(birlesik)} satir (ust fixture {yuk} satir; fixture 4 satir)")
            # A3: kucultulmus kare
            im = Image.fromarray(k.image[:, :, ::-1]).resize((1280, 720), Image.BILINEAR)
            kk = Frame(image=np.ascontiguousarray(np.array(im)[:, :, ::-1]), rect=Rect(0, 0, 1280, 720), captured_at=k.captured_at, seq=1)
            t0 = time.perf_counter(); b2 = motor.recognize(kk, OcrPreset.DIALOGUE); t1 = time.perf_counter()
            olgu(f"A3 {dil} 1280x720 kucultme olcek {olcek}: OCR {(t1 - t0) * 1000:.0f} ms, {len(b2)} blok -> {len(satirlari_birlestir(b2))} satir")

    # A4 secim -> ceviri
    motor = RapidOcrEngine(language=OcrLanguage.KOREAN, threads=8, allow_download=True)
    k = sentetik_kare("KR", 1.0)
    bloklar = satirlari_birlestir(motor.recognize(k, OcrPreset.DIALOGUE))
    secili = [b for b in bloklar if b.bbox.y < 500][:4]
    segs = normalize(secili, OcrPreset.DIALOGUE)
    s = GlossaryStore(KOK / "demo/sozluk_ornek.json")
    hits = s.lookup_segments(segs)
    gomulu = terimleri_gom(segs, hits)
    p = LocalNmtProvider(model_dir=KOK / "models/nllb-200-distilled-600M-ct2-int8", threads=8)
    t0 = time.perf_counter(); r = p.translate(TranslationRequest(segments=tuple(gomulu), source_lang="kor_Hang", target_lang="tr")); t1 = time.perf_counter()
    t2 = time.perf_counter(); p.translate(TranslationRequest(segments=tuple(gomulu), source_lang="kor_Hang", target_lang="tr")); t3 = time.perf_counter()
    olgu(f"A4 secili {len(secili)} blok -> {len(segs)} segment, {len(hits)} sozluk hit; ceviri soguk {(t1 - t0) * 1000:.0f} ms, sicak {(t3 - t2) * 1000:.0f} ms, {len(r.translations)} ceviri")
    p.close()

    # A5 QImage donusumu
    from PySide6 import QtGui, QtWidgets
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    img = kare.image
    t0 = time.perf_counter()
    qimg = QtGui.QImage(img.data, img.shape[1], img.shape[0], img.strides[0], QtGui.QImage.Format.Format_BGR888).copy()
    pix = QtGui.QPixmap.fromImage(qimg)
    t1 = time.perf_counter()
    olgu(f"A5 {img.shape[1]}x{img.shape[0]} BGR -> QImage.copy -> QPixmap: {(t1 - t0) * 1000:.1f} ms (UI thread; < 16 ms hedef)")
    (CIKTI / "olgular.txt").write_text("T-014 ON OLCUM -- Snapshot modu, gercek OCR/NMT, sentetik 2560x1440 kare\n\n" + "\n".join(satirlar) + "\n", encoding="utf-8")
    print("yazildi: olgular.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
