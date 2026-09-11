"""Tester-A — GERÇEK modelle ayrı süreç deneyleri (bariyer yok; K1 gereği birim testte DEĞİL).

    python .agents/tasks/T-006/tester_A/a6_gercek_model.py

Rapor niteliğinde (§4.6/10 pozitif kontrol + A6/A4 sınıfları). OCR metni stdout'a
YAZILMAZ: yalnız sayı, tip, kutu, eşleşme boolean'ı ve süre yazılır.

Deneyler
  D1  küçük görüntü 300x80, 14 px İngilizce (arial)           -> ENGLISH
  D2  büyük görüntü 2560x1440, tek satır Japonca 40 px (msgothic) -> JAPAN
  D3  büyük görüntü 2560x1440, tek satır İngilizce 40 px      -> ENGLISH
  D4  C-bitişik OLMAYAN / salt-okunur / BGRA-dilimi uint8 (h,w,3) gerçek motora
  D5  allow_download=True + model_dir=None, ağ KAPALI (requests.get yamalı) -> çalışır mı?
  D6  allow_download=True + BOŞ model_dir, ağ KAPALI -> ModelMissingError? __cause__?
  D7  gerçek oturumda intra/inter iş parçacığı (threads=4 ve 8, iki nokta)
  D8  K11 keskinlik: açık model_path varken Rec.lang_type'ı yanlış vermek çıktıyı değiştiriyor mu?
"""
from __future__ import annotations

import dataclasses
import json
import statistics
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

KOK = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(KOK))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

from src.contracts.errors import ContractViolation, ModelMissingError, OcrError  # noqa: E402
from src.contracts.models import Frame, OcrPreset, Rect, TextBlock  # noqa: E402
from src.ocr.rapid_engine import OcrLanguage, RapidOcrEngine, _varsayilan_fabrika  # noqa: E402

FIX = KOK / ".agents" / "tasks" / "T-006" / "fixtures"
ARIAL = "C:/Windows/Fonts/arial.ttf"
GOTHIC = "C:/Windows/Fonts/msgothic.ttc"

EN_KUCUK = "Press A to continue"
JP_UZUN = "村の長老があなたを待っています。"
EN_UZUN = "The village elder is waiting for you."


def render(w: int, h: int, metin: str, font: str, px: int, xy: tuple[int, int]) -> np.ndarray:
    im = Image.new("RGB", (w, h), (24, 24, 40))
    ImageDraw.Draw(im).text(xy, metin, font=ImageFont.truetype(font, px), fill=(240, 240, 240))
    return np.array(im)[:, :, ::-1].copy()  # BGR, C-bitişik, OWNDATA


def frame(img: np.ndarray, rect: Rect | None = None) -> Frame:
    h, w = img.shape[:2]
    return Frame(image=img, rect=rect or Rect(0, 0, w, h), captured_at=0.0, seq=0)


def bosluksuz(s: str) -> str:
    return "".join(s.split())


def ozet(ad: str, bl: list[TextBlock], beklenen: str | None, sinir: tuple[int, int]) -> None:
    w, h = sinir
    icinde = all(0 <= b.bbox.x and 0 <= b.bbox.y and b.bbox.x + b.bbox.w <= w and b.bbox.y + b.bbox.h <= h for b in bl)
    tipler = all(type(getattr(b.bbox, a)) is int for b in bl for a in ("x", "y", "w", "h")) and all(type(b.confidence) is float for b in bl)
    kutular = [(b.bbox.x, b.bbox.y, b.bbox.w, b.bbox.h) for b in bl]
    puanlar = [round(b.confidence, 3) for b in bl]
    esles = None
    if beklenen is not None:
        birlesik = bosluksuz("".join(b.text for b in sorted(bl, key=lambda b: (b.bbox.y, b.bbox.x))))
        esles = birlesik == bosluksuz(beklenen)
    print(f"  {ad}: {len(bl)} blok | kutular {kutular} | puanlar {puanlar} | goruntu icinde={icinde} | tipler duz={tipler} | birlesik==beklenen: {esles}")
    for b in bl:
        json.dumps(dataclasses.asdict(b.bbox))


def sure(m: RapidOcrEngine, f: Frame, n: int = 5) -> float:
    m.recognize(f, OcrPreset.DIALOGUE)
    s = []
    for _ in range(n):
        t0 = time.perf_counter()
        m.recognize(f, OcrPreset.DIALOGUE)
        s.append((time.perf_counter() - t0) * 1000)
    return statistics.median(s)


def main() -> int:
    print("T-006 tester-A gercek model deneyleri")

    # --- D1 kucuk goruntu ---------------------------------------------------
    en = RapidOcrEngine(language=OcrLanguage.ENGLISH, threads=8)
    kucuk = render(300, 80, EN_KUCUK, ARIAL, 14, (12, 30))
    bl = en.recognize(frame(kucuk), OcrPreset.DIALOGUE)
    ozet("D1 300x80 14px EN", bl, EN_KUCUK, (300, 80))
    print(f"     medyan {sure(en, frame(kucuk)):.0f} ms")
    kucuk10 = render(300, 80, EN_KUCUK, ARIAL, 10, (12, 30))
    ozet("D1b 300x80 10px EN", en.recognize(frame(kucuk10), OcrPreset.DIALOGUE), EN_KUCUK, (300, 80))

    # --- D2 / D3 buyuk goruntu ---------------------------------------------
    jp = RapidOcrEngine(language=OcrLanguage.JAPAN, threads=8)
    buyuk_jp = render(2560, 1440, JP_UZUN, GOTHIC, 40, (300, 1200))
    bl = jp.recognize(frame(buyuk_jp, Rect(-2560, 0, 2560, 1440, monitor_index=0)), OcrPreset.DIALOGUE)
    print(f"  D2 2560x1440 40px JP (rect.x=-2560): {len(bl)} blok | kutular {[(b.bbox.x, b.bbox.y, b.bbox.w, b.bbox.h) for b in bl]} | puanlar {[round(b.confidence,3) for b in bl]}")
    if bl:
        ilk = bl[0]
        print(f"     ilk kutu goruntu-yerel x={ilk.bbox.x + 2560}, y={ilk.bbox.y}; metin cizim noktasi (300,1200) civarinda mi: {abs(ilk.bbox.x + 2560 - 300) < 30 and abs(ilk.bbox.y - 1200) < 30}")
        print(f"     birlesik==beklenen: {bosluksuz(''.join(b.text for b in bl)) == bosluksuz(JP_UZUN)}")
    print(f"     medyan {sure(jp, frame(buyuk_jp)):.0f} ms")
    buyuk_en = render(2560, 1440, EN_UZUN, ARIAL, 40, (300, 1200))
    bl = en.recognize(frame(buyuk_en), OcrPreset.DIALOGUE)
    ozet("D3 2560x1440 40px EN", bl, EN_UZUN, (2560, 1440))
    print(f"     medyan {sure(en, frame(buyuk_en)):.0f} ms")
    # bos buyuk kare
    bl = jp.recognize(frame(np.zeros((1440, 2560, 3), np.uint8)), OcrPreset.DIALOGUE)
    print(f"  D2c 2560x1440 bos kare -> {len(bl)} blok (istisna yok)")

    # --- D4 bitisik olmayan / salt okunur --------------------------------------
    img = np.array(Image.open(FIX / "dlg_JP.png").convert("RGB"))[:, :, ::-1].copy()
    beklenen_jp = ["長老マルクス", "村の長老があなたを待っています。", "水車小屋を過ぎて東の道を行きなさい。", "日が暮れたら道を外れないように。"]

    def esles_jp(bl: list[TextBlock]) -> int:
        okunan = {bosluksuz(b.text) for b in bl}
        return sum(1 for s in beklenen_jp if bosluksuz(s) in okunan)

    taban = jp.recognize(frame(img), OcrPreset.DIALOGUE)
    print(f"  D4 taban (C-bitisik kopya): {len(taban)} blok, {esles_jp(taban)}/4 satir")
    varyantlar: list[tuple[str, np.ndarray]] = []
    dolgu = np.zeros((420, 1220, 3), np.uint8)
    dolgu[10:410, 10:1210] = img
    varyantlar.append(("dilim_gorunum(420x1220 icinden)", dolgu[10:410, 10:1210]))
    varyantlar.append(("fortran", np.asfortranarray(img)))
    salt = img.copy(); salt.flags.writeable = False
    varyantlar.append(("salt_okunur", salt))
    bgra = np.zeros((400, 1200, 4), np.uint8); bgra[:, :, :3] = img; bgra[:, :, 3] = 255
    varyantlar.append(("bgra_dilimi[:,:,:3]", bgra[:, :, :3]))
    varyantlar.append(("yatay_ters_gorunum[:, ::-1] (icerik aynali)", img[:, ::-1]))
    for ad, v in varyantlar:
        assert v.shape == (400, 1200, 3) and v.dtype == np.uint8
        try:
            bl = jp.recognize(frame(v), OcrPreset.DIALOGUE)
            print(f"  D4 {ad}: C={v.flags['C_CONTIGUOUS']} W={v.flags['WRITEABLE']} -> {len(bl)} blok, {esles_jp(bl)}/4 satir (istisna yok)")
        except Exception as e:  # noqa: BLE001
            print(f"  D4 {ad}: C={v.flags['C_CONTIGUOUS']} W={v.flags['WRITEABLE']} -> {type(e).__name__} (cause {type(e.__cause__).__name__})")

    # --- D5 / D6 ag kapali -------------------------------------------------
    import requests

    def _kapali(*a: object, **k: object) -> object:
        raise requests.ConnectionError("tester-A: ag kapali (yama)")

    orijinal_get = requests.get
    requests.get = _kapali  # type: ignore[assignment]
    try:
        m5 = RapidOcrEngine(language=OcrLanguage.JAPAN, threads=8, allow_download=True, model_dir=None)
        try:
            bl = m5.recognize(frame(img), OcrPreset.DIALOGUE)
            print(f"  D5 allow_download=True, model_dir=None, ag KAPALI -> kuruldu, {len(bl)} blok, {esles_jp(bl)}/4 (dosyalar yerelde; indirme gerekmedi)")
        except Exception as e:  # noqa: BLE001
            print(f"  D5 allow_download=True, model_dir=None, ag KAPALI -> {type(e).__name__}: cause={type(e.__cause__).__name__}")
        bos = Path(tempfile.mkdtemp(prefix="t006_A_bos_"))
        m6 = RapidOcrEngine(language=OcrLanguage.JAPAN, threads=8, allow_download=True, model_dir=bos)
        try:
            m6.recognize(frame(img), OcrPreset.DIALOGUE)
            print("  D6 allow_download=True, BOS model_dir, ag KAPALI -> HATA YOK (beklenmedik)")
        except ModelMissingError as e:
            zincir = []
            c: BaseException | None = e
            while c is not None:
                zincir.append(type(c).__name__)
                c = c.__cause__
            print(f"  D6 allow_download=True, BOS model_dir, ag KAPALI -> ModelMissingError; __cause__ zinciri: {' -> '.join(zincir)}; dizin icerigi: {sorted(p.name for p in bos.iterdir())}")
        except Exception as e:  # noqa: BLE001
            print(f"  D6 -> BASKA: {type(e).__name__} cause={type(e.__cause__).__name__}")
    finally:
        requests.get = orijinal_get  # type: ignore[assignment]

    # --- D7 gercek oturum is parcacigi (iki nokta) ---------------------------
    for n in (4, 8):
        m7 = RapidOcrEngine(language=OcrLanguage.JAPAN, threads=n)
        m7.recognize(frame(img), OcrPreset.DIALOGUE)
        tan = m7._taniyici  # noqa: SLF001 -- gozlem
        rapid = None
        for hucre in (tan.__closure__ or []):  # type: ignore[union-attr]
            if type(hucre.cell_contents).__name__ == "RapidOCR":
                rapid = hucre.cell_contents
        if rapid is None:
            print(f"  D7 threads={n}: RapidOCR ornegi bulunamadi")
            continue
        sonuc = []
        for parca in ("text_det", "text_rec"):
            oturum = getattr(getattr(rapid, parca), "session", None)
            ic = getattr(oturum, "session", oturum)
            try:
                so = ic.get_session_options()
                sonuc.append(f"{parca}: intra={so.intra_op_num_threads} inter={so.inter_op_num_threads}")
            except Exception as e:  # noqa: BLE001
                sonuc.append(f"{parca}: okunamadi {type(e).__name__}")
        print(f"  D7 threads={n}: {' | '.join(sonuc)} | text_score={rapid.text_score} | use_cls={rapid.cfg.Global.use_cls if hasattr(rapid, 'cfg') else '?'}")

    # --- D8 K11 keskinlik: acik model_path + yanlis Rec.lang_type ------------
    p = jp.parametreler()
    for yanlis in ("ch", "en", "korean"):
        q = dict(p); q["Rec.lang_type"] = yanlis
        try:
            tan8 = _varsayilan_fabrika(q)
            out = tan8(img)
            n8 = len(out.txts or ())
            okunan = {bosluksuz(t) for t in (out.txts or ())}
            e8 = sum(1 for s in beklenen_jp if bosluksuz(s) in okunan)
            print(f"  D8 JAPAN model_path acik + Rec.lang_type={yanlis!r}: {n8} kutu, {e8}/4 satir birebir")
        except Exception as e:  # noqa: BLE001
            print(f"  D8 Rec.lang_type={yanlis!r}: {type(e).__name__}")
    q = dict(p); q["Det.lang_type"] = "ch"
    try:
        out = _varsayilan_fabrika(q)(img)
        okunan = {bosluksuz(t) for t in (out.txts or ())}
        print(f"  D8 JAPAN model_path acik + Det.lang_type='ch': {len(out.txts or ())} kutu, {sum(1 for s in beklenen_jp if bosluksuz(s) in okunan)}/4")
    except Exception as e:  # noqa: BLE001
        print(f"  D8 Det.lang_type='ch': {type(e).__name__}")

    # --- D9 ContractViolation gercek motorla da once (motor kurulu) ----------
    try:
        jp.recognize(frame(np.zeros((40, 100, 3), np.int32)), OcrPreset.DIALOGUE)
    except ContractViolation as e:
        print(f"  D9 kurulu gercek motor + int32 kare -> ContractViolation (cause {type(e.__cause__).__name__})")
    try:
        jp.recognize(frame(np.zeros((0, 0, 3), np.uint8)), OcrPreset.DIALOGUE)
    except ContractViolation:
        print("  D9 kurulu gercek motor + 0x0 -> ContractViolation (ZeroDivisionError yuzeye cikmadi)")
    bl = jp.recognize(frame(np.zeros((1, 1, 3), np.uint8)), OcrPreset.DIALOGUE)
    print(f"  D9 1x1 -> {len(bl)} blok, istisna yok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
