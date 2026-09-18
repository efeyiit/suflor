"""Suflor -- oturum boyunca oyun dilini secen nesne (T-018): dil basina tembel OCR motoru + mevcut dil.

Kullanici "Otomatik" secmisse kabuk bir `DilSecici` kurar ve her `AnlikAkisi`ye verir. Akisin isci thread'i
`oku` sonrasinda `sec()` cagirir: mevcut dil emin (`dil_algila` K3) -> ek is yok; degilse diger modeller
denenir, kazanan dil OTURUM boyunca mevcut olur (sonraki Snapshot dogrudan onunla baslar, tek okuma).

## Sozlesme (K1-K4, olcu: tests/unit/pipeline/test_dil_secici.py)

K1 `motor(dil)` fabrikayi dil basina EN FAZLA BIR KEZ cagirir (kilitli: isitma thread'i ile isci thread'i
   ayni anda isteyebilir); `kaynak_dili(dil)` NLLB kodu (tabloda yoksa `KeyError`).
K2 `sec(kare, bloklar, preset)` -> `DilSecimi`: `dil` (secilen ya da korunan mevcut), `ocr` o dilin motoru,
   `kaynak_dili`, `bloklar` (dil degistiyse kazananin bloklari `satirlari_birlestir`den gecmis; degismediyse
   verilenler AYNEN), `degisti`, `belirsiz` (algilayici karar veremedi -> mevcut korunur, `degisti=False`).
   Degisince `mevcut` guncellenir.
K3 `isit(diller)` verilen dillerin motorlarini kurar ve kucuk bos bir kareyle bir kez `recognize` cagirir
   (model yuklemesi ilk cagrida); motor hatasi (`TranslatorError`) yutulur (o dil sonra yine denenir), baska
   istisna yayilir. Arka plan thread'inden cagrilmak icin.
K4 Qt yok, dosya/ag/log yok; metin loglanmaz.
"""
from __future__ import annotations

import threading
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass

import numpy as np

from src.contracts.errors import TranslatorError
from src.contracts.interfaces import OcrEngine
from src.contracts.models import Frame, OcrPreset, Rect, TextBlock
from src.ocr.dil_algila import DilKarari, dili_algila
from src.ocr.rapid_engine import OcrLanguage
from src.ocr.satir_birlestirici import satirlari_birlestir

__all__ = ["DilSecici", "DilSecimi"]


@dataclass(frozen=True)
class DilSecimi:
    dil: OcrLanguage
    ocr: OcrEngine
    kaynak_dili: str
    bloklar: list[TextBlock]
    degisti: bool
    belirsiz: bool
    karar: DilKarari


class DilSecici:
    def __init__(self, fabrika: Callable[[OcrLanguage], OcrEngine], nllb_kodu: Mapping[OcrLanguage, str], *,
                 baslangic: OcrLanguage) -> None:
        self._fabrika = fabrika
        self._nllb = dict(nllb_kodu)
        self._mevcut = OcrLanguage(baslangic)
        self._motorlar: dict[OcrLanguage, OcrEngine] = {}
        self._kilit = threading.Lock()

    @property
    def mevcut(self) -> OcrLanguage:
        return self._mevcut

    def motor(self, dil: OcrLanguage) -> OcrEngine:
        """K1."""
        dil = OcrLanguage(dil)
        with self._kilit:
            m = self._motorlar.get(dil)
            if m is None:
                m = self._fabrika(dil)
                self._motorlar[dil] = m
            return m

    def kaynak_dili(self, dil: OcrLanguage) -> str:
        return self._nllb[OcrLanguage(dil)]

    def sec(self, kare: Frame, bloklar: Sequence[TextBlock], preset: OcrPreset) -> DilSecimi:
        """K2."""
        mevcut = self._mevcut
        karar = dili_algila(kare, self.motor, preset, mevcut=mevcut, mevcut_bloklar=bloklar)
        if karar.dil is None or karar.dil is mevcut:
            return DilSecimi(mevcut, self.motor(mevcut), self.kaynak_dili(mevcut), list(bloklar), False, karar.dil is None, karar)
        self._mevcut = karar.dil
        return DilSecimi(karar.dil, self.motor(karar.dil), self.kaynak_dili(karar.dil), list(satirlari_birlestir(karar.bloklar)),
                         True, False, karar)

    def isit(self, diller: Iterable[OcrLanguage]) -> None:
        """K3."""
        kare = Frame(image=np.zeros((64, 64, 3), dtype=np.uint8), rect=Rect(0, 0, 64, 64), captured_at=0.0, seq=0)
        for dil in diller:
            try:
                self.motor(dil).recognize(kare, OcrPreset.DIALOGUE)
            except TranslatorError:
                continue
