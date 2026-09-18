"""T-018 -- dil_algila K1-K5 (sahte motorlar; gercek model real_check'te)."""
from __future__ import annotations

import ast
from pathlib import Path

import numpy as np
import pytest

from src.contracts.errors import OcrError
from src.contracts.interfaces import FakeOcrEngine, OcrEngine
from src.contracts.models import Frame, OcrPreset, Rect, TextBlock
from src.ocr.dil_algila import (ADAY_SIRASI, EMIN_ESIGI, KABUL_ESIGI, MIN_HARF, DilPuani, dili_algila, karar_ver, puanla,
                                yazi_sistemi)
from src.ocr.rapid_engine import OcrLanguage

KR, JP, ZH, EN = OcrLanguage.KOREAN, OcrLanguage.JAPAN, OcrLanguage.CHINESE, OcrLanguage.ENGLISH


def b(metin: str, guven: float = 0.99) -> TextBlock:
    return TextBlock(text=metin, bbox=Rect(0, 0, 100, 20), confidence=guven)


def kare() -> Frame:
    return Frame(image=np.zeros((40, 80, 3), dtype=np.uint8), rect=Rect(0, 0, 80, 40), captured_at=1.0, seq=1)


# olcum_dil.py'deki gercek ciktilara benzer sentetik bloklar
KR_METIN = [b("방앗간을 지나 동쪽 길로 가면 오래된 사당이 있어."), b("거기서 해가 지기 전에 만나자.")]
JP_METIN = [b("水車小屋を過ぎて東の道を行くと、古い祠がある。"), b("日が沈む前にそこで会おう。")]
ZH_METIN = [b("经过磨坊沿着东边的路走，就会看到一座古老的祠堂。"), b("日落之前我们在那里见面。")]
EN_METIN = [b("Past the mill, take the east road and you will find an old shrine.")]


# ---------------------------------------------------------------- K1 puan
def test_k1_yazi_sistemi() -> None:
    assert [yazi_sistemi(c) for c in "가あア漢a1 ,"] == ["hangul", "kana", "kana", "han", "latin", "", "", ""]
    assert yazi_sistemi("ж") == "diger"


def test_k1_dogru_dil_yuksek_yanlis_dil_sifir() -> None:
    assert puanla(KR, KR_METIN).puan > 0.95 and puanla(JP, KR_METIN).puan == 0 and puanla(EN, KR_METIN).puan == 0
    assert puanla(EN, EN_METIN).puan > 0.95 and puanla(KR, EN_METIN).puan == 0   # Latin, KR modelinin yerli sistemi degil
    p = puanla(JP, JP_METIN)
    assert p.puan > 0.95 and 0.5 < p.kana_orani < 0.9 and p.harf >= MIN_HARF


def test_k1_guven_ve_harf_sayisi_puani_carpar() -> None:
    assert puanla(KR, [b("방앗간을 지나 동쪽 길로 가면 오래된 사당이 있어.", 0.5)]).puan == pytest.approx(0.5, abs=0.02)
    kisa = puanla(KR, [b("방앗", 0.99)])   # 2 harf -> 2/20
    assert kisa.puan == pytest.approx(0.099, abs=0.01)
    assert puanla(KR, []).puan == 0 and puanla(KR, [b("123 !!")]).puan == 0


def test_k1_karisik_yazi_sistemi_oranlar() -> None:
    p = puanla(ZH, [b("漢字漢字漢字漢字漢字 abcdefghij")])   # 10 han + 10 latin
    assert p.puan == pytest.approx(0.99 * 0.5, abs=0.01)


# ---------------------------------------------------------------- K2 karar
def test_k2_en_yuksek_puan_kazanir_esik_ve_fark() -> None:
    assert karar_ver([DilPuani(KR, 0.99, 0.99, 50, 0), DilPuani(JP, 0.36, 0.45, 50, 0.1)]) is KR
    assert karar_ver([DilPuani(KR, 0.4, 0.4, 50, 0)]) is None                       # KABUL_ESIGI alti
    assert karar_ver([DilPuani(KR, 0.7, 0.7, 50, 0), DilPuani(EN, 0.6, 0.6, 50, 0)]) is None   # fark < 0.15
    assert karar_ver([]) is None


def test_k2_jp_zh_capraz_kana_kurali() -> None:
    # Japonca panel (olcum: JP 0.996 kana 0.70; ZH 0.86 han) -> ZH yariya iner, JP kazanir
    assert karar_ver([DilPuani(JP, 0.996, 0.996, 86, 0.70), DilPuani(ZH, 0.86, 0.895, 28, 0)]) is JP
    # Cince panel (olcum: JP 0.85 kana 0.0; ZH 0.999) -> JP yariya iner, ZH acik farkla
    assert karar_ver([DilPuani(JP, 0.85, 0.86, 69, 0.0), DilPuani(ZH, 0.999, 0.999, 69, 0)]) is ZH
    # kanasiz JP tek basina: 0.85 * 0.5 = 0.425 < KABUL -> belirsiz
    assert karar_ver([DilPuani(JP, 0.85, 0.86, 69, 0.0)]) is None
    # JP kana var ama guven dusuk (KR paneli: JP 0.445 kana 0.11) -> ZH cezalandirilmaz
    assert karar_ver([DilPuani(JP, 0.36, 0.445, 70, 0.11), DilPuani(ZH, 0.6, 0.9, 30, 0)]) is ZH


def test_k2_olcum_tablosu_dort_panel() -> None:
    """olcum_dil.py tam kare tablosu (puan = guven x yerli x min(1, harf/20))."""
    tablo = {
        "KR": [DilPuani(KR, 0.996, 0.996, 75, 0), DilPuani(JP, 0.445 * 0.80, 0.445, 70, 0.11), DilPuani(ZH, 0, 0.683, 0, 0), DilPuani(EN, 0, 0.495, 54, 0)],
        "JP": [DilPuani(KR, 0.52 * 0.75 * 0.2, 0.52, 4, 0), DilPuani(JP, 0.996, 0.996, 86, 0.70), DilPuani(ZH, 0.895 * 0.96, 0.895, 28, 0.04), DilPuani(EN, 0, 0.571, 62, 0)],
        "ZH": [DilPuani(KR, 0, 0.694, 0, 0), DilPuani(JP, 0.860 * 0.99, 0.860, 69, 0), DilPuani(ZH, 0.999, 0.999, 69, 0), DilPuani(EN, 0, 0.566, 29, 0)],
        "EN": [DilPuani(KR, 0, 0.989, 179, 0), DilPuani(JP, 0, 0.964, 179, 0), DilPuani(ZH, 0, 0.988, 179, 0), DilPuani(EN, 0.994, 0.994, 179, 0)],
    }
    assert {ad: karar_ver(p) for ad, p in tablo.items()} == {"KR": KR, "JP": JP, "ZH": ZH, "EN": EN}


# ---------------------------------------------------------------- K3 algila
class Motorlar:
    def __init__(self, ciktilar: dict[OcrLanguage, list[TextBlock]]) -> None:
        self.motorlar = {d: FakeOcrEngine([c]) for d, c in ciktilar.items()}
        self.istenen: list[OcrLanguage] = []

    def __call__(self, dil: OcrLanguage) -> OcrEngine:
        self.istenen.append(dil)
        return self.motorlar[dil]


def test_k3_mevcut_dil_eminse_baska_motor_cagrilmaz() -> None:
    m = Motorlar({KR: KR_METIN, JP: JP_METIN, ZH: ZH_METIN, EN: EN_METIN})
    k = dili_algila(kare(), m, OcrPreset.DIALOGUE, mevcut=KR, mevcut_bloklar=KR_METIN)
    assert k.dil is KR and k.denenen == (KR,) and m.istenen == [] and k.bloklar == tuple(KR_METIN)
    assert k.puanlar[0].puan >= EMIN_ESIGI


def test_k3_mevcut_yanlis_adaylar_okunur_kazanan_bloklariyla_doner() -> None:
    # oyun Japonca, ayar Korece: KR modeli az/dusuk cikti verir
    kr_cop = [b("가나", 0.4)]
    m = Motorlar({KR: kr_cop, JP: JP_METIN, ZH: [b("水車小屋過東道行古祠", 0.9)], EN: [b("abc", 0.5)]})
    k = dili_algila(kare(), m, OcrPreset.DIALOGUE, mevcut=KR, mevcut_bloklar=kr_cop)
    assert k.dil is JP and k.bloklar == tuple(JP_METIN)
    assert k.denenen == (KR, JP, ZH) and m.istenen == [JP, ZH, JP]
    # JP/ZH kucuk seritte denenir; kazanan JP dogru ekran koordinatlari icin tam kareyi bir kez daha okur.
    assert m.motorlar[JP].call_count == 2 and m.motorlar[KR].call_count == 0


def test_k3_erken_durma_kr_en_hemen_jp_zh_ikisi_okununca() -> None:
    # EN mevcut, oyun Korece: KR 1.0 -> hemen dur (JP/ZH/EN okunmaz)
    m = Motorlar({KR: KR_METIN, JP: JP_METIN, ZH: ZH_METIN, EN: [b("ab", 0.4)]})
    k = dili_algila(kare(), m, OcrPreset.DIALOGUE, mevcut=EN, mevcut_bloklar=[b("ab", 0.4)])
    assert k.dil is KR and k.denenen == (EN, KR) and m.istenen == [KR, KR]
    # KR mevcut, oyun Japonca: JP 1.0 ama ZH okunmadan durulmaz; ZH okununca durur, EN okunmaz
    m = Motorlar({KR: [b("가", 0.4)], JP: JP_METIN, ZH: [b("水車小屋過東道行古祠", 0.9)], EN: EN_METIN})
    k = dili_algila(kare(), m, OcrPreset.DIALOGUE, mevcut=KR, mevcut_bloklar=[b("가", 0.4)])
    assert k.dil is JP and k.denenen == (KR, JP, ZH) and m.istenen == [JP, ZH, JP]
    # JP mevcut, oyun Cince: KR 0, ZH 1.0 -> JP+ZH okunmus -> dur, EN okunmaz
    m = Motorlar({KR: [], JP: [b("水車小屋過東道行古祠水車小屋過東道行古祠", 0.86)], ZH: ZH_METIN, EN: EN_METIN})
    k = dili_algila(kare(), m, OcrPreset.DIALOGUE, mevcut=JP, mevcut_bloklar=[b("水車小屋過東道行古祠水車小屋過東道行古祠", 0.86)])
    assert k.dil is ZH and k.denenen == (JP, ZH) and m.istenen == [ZH, ZH]


def test_k3_hepsi_dusuk_belirsiz_bloklar_bos() -> None:
    m = Motorlar({KR: [], JP: [b("あ", 0.3)], ZH: [], EN: [b("x", 0.2)]})
    k = dili_algila(kare(), m, OcrPreset.DIALOGUE, mevcut=KR, mevcut_bloklar=[])
    assert k.dil is None and k.bloklar == () and len(k.puanlar) == 4


def test_k3_aday_sirasi_sabit() -> None:
    assert ADAY_SIRASI == (KR, JP, ZH, EN) and KABUL_ESIGI < EMIN_ESIGI


# ---------------------------------------------------------------- K4 hata
class PatlayanMotor(OcrEngine):
    def recognize(self, frame: Frame, preset: OcrPreset) -> list[TextBlock]:
        raise OcrError("x")


def test_k4_motor_hatasi_adayi_sifirlar_digerleri_devam() -> None:
    m = Motorlar({KR: [], JP: JP_METIN, ZH: ZH_METIN, EN: [b("ab", 0.5)]})
    m.motorlar[JP] = PatlayanMotor()   # type: ignore[assignment]
    k = dili_algila(kare(), m, OcrPreset.DIALOGUE, mevcut=KR, mevcut_bloklar=[])
    assert k.dil is ZH and next(p for p in k.puanlar if p.dil is JP).puan == 0


def test_k4_baska_istisna_yayilir() -> None:
    class Bozuk(OcrEngine):
        def recognize(self, frame: Frame, preset: OcrPreset) -> list[TextBlock]:
            raise RuntimeError("bug")

    m = Motorlar({KR: [], JP: [], ZH: [], EN: []})
    m.motorlar[JP] = Bozuk()   # type: ignore[assignment]
    with pytest.raises(RuntimeError):
        dili_algila(kare(), m, OcrPreset.DIALOGUE, mevcut=KR, mevcut_bloklar=[])


# ---------------------------------------------------------------- K5 saf
def test_k5_modul_kutuphane_ve_log_bilmez() -> None:
    kaynak = (Path(__file__).resolve().parents[3] / "src" / "ocr" / "dil_algila.py").read_text(encoding="utf-8")
    agac = ast.parse(kaynak)
    modüller = {n.names[0].name.split(".")[0] for n in ast.walk(agac) if isinstance(n, ast.Import)} | \
        {(n.module or "").split(".")[0] for n in ast.walk(agac) if isinstance(n, ast.ImportFrom)}
    assert not modüller & {"rapidocr", "onnxruntime", "logging", "print", "cv2", "PIL"}
    assert "print(" not in kaynak
