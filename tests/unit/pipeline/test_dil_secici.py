"""T-018 -- DilSecici K1-K4 (sahte motorlar)."""
from __future__ import annotations

import ast
import threading
from pathlib import Path

import numpy as np
import pytest

from src.contracts.errors import OcrError
from src.contracts.interfaces import FakeOcrEngine, OcrEngine
from src.contracts.models import Frame, OcrPreset, Rect, TextBlock
from src.ocr.rapid_engine import OcrLanguage
from src.pipeline.dil_secici import DilSecici

KR, JP, ZH, EN = OcrLanguage.KOREAN, OcrLanguage.JAPAN, OcrLanguage.CHINESE, OcrLanguage.ENGLISH
NLLB = {KR: "kor_Hang", JP: "jpn_Jpan", ZH: "zho_Hans", EN: "eng_Latn"}


def b(metin: str, guven: float = 0.99, x: int = 0) -> TextBlock:
    return TextBlock(text=metin, bbox=Rect(x, 0, 100, 20), confidence=guven)


def kare() -> Frame:
    return Frame(image=np.zeros((40, 80, 3), dtype=np.uint8), rect=Rect(0, 0, 80, 40), captured_at=1.0, seq=1)


KR_METIN = [b("방앗간을 지나 동쪽 길로 가면 오래된 사당이 있어.")]
JP_METIN = [b("水車小屋を過ぎて東の道を行くと、古い祠がある。"), b("日が沈む前にそこで会おう。")]


class Fabrika:
    def __init__(self, ciktilar: dict[OcrLanguage, list[TextBlock]]) -> None:
        self.ciktilar = ciktilar
        self.cagrilar: list[OcrLanguage] = []

    def __call__(self, dil: OcrLanguage) -> OcrEngine:
        self.cagrilar.append(dil)
        return FakeOcrEngine([self.ciktilar.get(dil, [])])


# ---------------------------------------------------------------- K1
def test_k1_motor_dil_basina_bir_kez_ve_kaynak_dili() -> None:
    f = Fabrika({}); s = DilSecici(f, NLLB, baslangic=KR)
    m1 = s.motor(JP); m2 = s.motor(JP); s.motor("korean")  # type: ignore[arg-type]
    assert m1 is m2 and f.cagrilar == [JP, KR] and s.kaynak_dili(JP) == "jpn_Jpan" and s.mevcut is KR
    with pytest.raises(KeyError):
        DilSecici(f, {KR: "kor_Hang"}, baslangic=KR).kaynak_dili(JP)


def test_k1_esz_zamanli_istek_tek_motor() -> None:
    f = Fabrika({}); s = DilSecici(f, NLLB, baslangic=KR)
    sonuc: list[OcrEngine] = []
    ts = [threading.Thread(target=lambda: sonuc.append(s.motor(EN))) for _ in range(8)]
    for t in ts: t.start()
    for t in ts: t.join()
    assert len(set(map(id, sonuc))) == 1 and f.cagrilar == [EN]


# ---------------------------------------------------------------- K2
def test_k2_mevcut_eminse_bloklar_aynen_degisti_yok() -> None:
    f = Fabrika({KR: KR_METIN}); s = DilSecici(f, NLLB, baslangic=KR)
    secim = s.sec(kare(), KR_METIN, OcrPreset.DIALOGUE)
    assert not secim.degisti and not secim.belirsiz and secim.dil is KR and secim.bloklar == KR_METIN
    assert secim.kaynak_dili == "kor_Hang" and secim.ocr is s.motor(KR) and f.cagrilar == [KR]   # baska motor kurulmadi


def test_k2_dil_degisir_kazananin_bloklari_satir_birlesik_mevcut_guncellenir() -> None:
    parcali_jp = [b("水車小屋を過ぎて", x=0), b("東の道を行くと、古い祠がある。", x=101), b("日が沈む前にそこで会おう。")]
    f = Fabrika({KR: [b("가", 0.3)], JP: parcali_jp, ZH: [b("水車小屋過", 0.8)], EN: [b("ab", 0.4)]})
    s = DilSecici(f, NLLB, baslangic=KR)
    secim = s.sec(kare(), [b("가", 0.3)], OcrPreset.DIALOGUE)
    assert secim.degisti and secim.dil is JP and secim.kaynak_dili == "jpn_Jpan" and secim.ocr is s.motor(JP)
    assert s.mevcut is JP and len(secim.bloklar) < len(parcali_jp)   # satirlari_birlestir uygulandi
    assert secim.karar.denenen == (KR, JP, ZH)   # erken durma: EN okunmadi
    # sonraki Snapshot: mevcut JP, JP bloklari emin -> ek okuma yok
    secim2 = s.sec(kare(), JP_METIN, OcrPreset.DIALOGUE)
    assert not secim2.degisti and secim2.dil is JP and secim2.karar.denenen == (JP,)


def test_k2_belirsiz_mevcut_korunur() -> None:
    f = Fabrika({KR: [], JP: [b("あ", 0.3)], ZH: [], EN: []})
    s = DilSecici(f, NLLB, baslangic=KR)
    secim = s.sec(kare(), [], OcrPreset.DIALOGUE)
    assert secim.belirsiz and not secim.degisti and secim.dil is KR and secim.bloklar == [] and s.mevcut is KR


# ---------------------------------------------------------------- K3
def test_k3_isit_motorlari_kurar_bir_kez_okur_hata_yutar() -> None:
    class Patlayan(OcrEngine):
        def recognize(self, frame: Frame, preset: OcrPreset) -> list[TextBlock]:
            raise OcrError("model yok")

    kr, en = FakeOcrEngine(), FakeOcrEngine()
    motorlar: dict[OcrLanguage, OcrEngine] = {KR: kr, JP: Patlayan(), EN: en}
    s = DilSecici(lambda d: motorlar[d], NLLB, baslangic=KR)
    s.isit([KR, JP, EN])
    assert kr.call_count == 1 and en.call_count == 1
    k = kr.calls[0][0]
    assert k.image.shape == (64, 64, 3) and k.rect == Rect(0, 0, 64, 64)


def test_k3_isit_baska_istisna_yayilir() -> None:
    class Bozuk(OcrEngine):
        def recognize(self, frame: Frame, preset: OcrPreset) -> list[TextBlock]:
            raise RuntimeError("bug")

    s = DilSecici(lambda d: Bozuk(), NLLB, baslangic=KR)
    with pytest.raises(RuntimeError):
        s.isit([KR])


# ---------------------------------------------------------------- K4
def test_k4_modul_qt_dosya_ag_log_bilmez() -> None:
    kaynak = (Path(__file__).resolve().parents[3] / "src" / "pipeline" / "dil_secici.py").read_text(encoding="utf-8")
    agac = ast.parse(kaynak)
    modüller = {n.names[0].name.split(".")[0] for n in ast.walk(agac) if isinstance(n, ast.Import)} | \
        {(n.module or "").split(".")[0] for n in ast.walk(agac) if isinstance(n, ast.ImportFrom)}
    assert not modüller & {"PySide6", "logging", "socket", "urllib", "requests", "rapidocr", "onnxruntime"}
    assert "open(" not in kaynak and "print(" not in kaynak
