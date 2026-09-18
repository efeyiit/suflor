"""Suflor -- oyun dilini OCR ciktisindan algilama (T-018).

Motor dili tahmin etmez (rapid_engine K2: `ch` modeli Japonca'da 0.90 guvenle YANLIS metin uretir; guven tek
basina dil hatasini goremez). Bu modul BIRDEN COK dil modelinin ciktisini karsilastirir; kurala olcum karar
verdi (.agents/tasks/T-018/olcum_dil.py, 4 model x 4 dil paneli, gercek RapidOCR):

  * Dogru model: guven ~0.99 ve cikti karakterlerinin tamamina yakini o dilin YAZI SISTEMINDE.
  * Yanlis model ya guven dusuk (KR paneli/JP modeli 0.45; EN modeli 0.5-0.57) ya karakter uretmiyor
    (ZH modeli KR panelinde 0 harf) ya da yazi sistemi yabanci (KR/JP modeli EN panelinde 0.99 guvenle LATIN).
  * Tek istisna JP<->ZH: ZH modeli Japonca'da 0.895 guvenle Han uretir, JP modeli Cince'de 0.86 guvenle Han
    uretir. Ayirt eden KANA: Japonca metinde JP modeli %70 kana verir, Cince panelde 0.

## Sozlesme (K1-K5, olcu: tests/unit/ocr/test_dil_algila.py)

K1 Puan: `puanla(dil, bloklar)` = ortalama guven x (o dilin yazi sistemindeki harf orani) x min(1, harf/MIN_HARF).
   Yazi sistemi: KOREAN=hangul, JAPAN=kana+han, CHINESE=han, ENGLISH=latin. Harf disi karakterler sayilmaz.
   Blok yoksa / harf yoksa 0. Puan [0, 1].
K2 Karar (`karar_ver`): JP/ZH capraz kurali -- JP ciktisinda kana orani < KANA_ESIGI ise JP puani yariya iner
   (kanasiz Japonca olasi degil); kana >= KANA_ESIGI ve JP guveni >= 0.7 ise ZH puani yariya iner. Sonra en
   yuksek puan: >= KABUL_ESIGI ve ikinciden >= FARK_ESIGI onde ise o dil; degilse `None` (belirsiz -- cagiran
   mevcut dili korur). Puanlar karar nesnesinde (UI/olcum icin).
K3 `dili_algila(kare, motor, preset, mevcut, mevcut_bloklar)`: mevcut dilin puani mevcut bloklardan hesaplanir
   (ek OCR YOK); >= EMIN_ESIGI ise mevcut dil hemen doner (`denenen == (mevcut,)`, `asama="mevcut"`). Degilse:
   a) SERIT asamasi (olculdu: metin yogun ekranda tam kare okuma 3-4 s x 4 model = 16 s'ydi): mevcut okumanin en
      buyuk `SERIT_SATIR` kutusu kirpilip alt alta dizilir (kucuk kare); adaylar bu seridi okur. Aday sirasi
      mevcut ciktinin BASKIN yazi sistemine gore (latin -> EN once; han -> ZH, JP; kana -> JP, ZH; hangul -> KR;
      kalanlar ADAY_SIRASI). ERKEN DURMA: her adaydan sonra K2 karari; en iyi >= EMIN_ESIGI ve kazanan KR/EN
      (tek anlamli yazi sistemi) ya da JP/ZH ve IKISI de okunmussa (olculdu: ZH modeli Japonca'da 0.86 alabiliyor)
      kalan adaylar okunmaz. Karar varsa ve dil degistiyse kazanan TAM kareyi bir kez okur (`bloklar`), `asama="serit"`.
   b) Serit karar veremediyse (ya da mevcut okumada kutu yoksa) TAM asama: adaylar tam kareyi okur (ayni sira ve
      erken durma), karar K2, kazananin bloklari o okumadan, `asama="tam"`. Her motor asama basina en fazla bir kez.
   Kazanan dilin bloklari kararda -- cagiran yeniden OCR yapmaz.
K4 Motor hatasi (`TranslatorError`) o adayi 0 puanla gecer; hicbir aday okunamadiysa belirsiz. Baska istisna
   yayilir.
K5 Saf, deterministik; metin loglanmaz; kutuphane import edilmez (K1 bariyeri: rapid_engine yalniz enum icin).
"""
from __future__ import annotations

import statistics
import unicodedata
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from src.contracts.errors import TranslatorError
from src.contracts.interfaces import OcrEngine
import numpy as np

from src.contracts.models import Frame, OcrPreset, Rect, TextBlock
from src.ocr.rapid_engine import OcrLanguage

__all__ = ["ADAY_SIRASI", "EMIN_ESIGI", "FARK_ESIGI", "KABUL_ESIGI", "KANA_ESIGI", "MIN_HARF", "SERIT_SATIR", "DilKarari",
           "DilPuani", "aday_sirasi", "dili_algila", "karar_ver", "puanla", "serit_kare", "yazi_sistemi"]

MIN_HARF = 20
SERIT_SATIR = 8
_SERIT_PAY = 6
_SERIT_ARALIK = 12
KANA_ESIGI = 0.05
EMIN_ESIGI = 0.9
KABUL_ESIGI = 0.5
FARK_ESIGI = 0.15
ADAY_SIRASI: tuple[OcrLanguage, ...] = (OcrLanguage.KOREAN, OcrLanguage.JAPAN, OcrLanguage.CHINESE, OcrLanguage.ENGLISH)
_YAZI_SISTEMI: Mapping[OcrLanguage, frozenset[str]] = {
    OcrLanguage.KOREAN: frozenset({"hangul"}), OcrLanguage.JAPAN: frozenset({"kana", "han"}),
    OcrLanguage.CHINESE: frozenset({"han"}), OcrLanguage.ENGLISH: frozenset({"latin"}),
}


def yazi_sistemi(ch: str) -> str:
    """hangul / kana / han / latin / diger; harf olmayan -> ''."""
    if not ch.isalpha():
        return ""
    ad = unicodedata.name(ch, "")
    if ad.startswith("HANGUL"):
        return "hangul"
    if ad.startswith(("HIRAGANA", "KATAKANA")):
        return "kana"
    if ad.startswith("CJK"):
        return "han"
    if ad.startswith("LATIN"):
        return "latin"
    return "diger"


@dataclass(frozen=True)
class DilPuani:
    dil: OcrLanguage
    puan: float
    guven: float
    harf: int
    kana_orani: float
    baskin: str = ""      # ciktida en cok gorulen yazi sistemi (hangul/kana/han/latin/diger), harf yoksa ""


@dataclass(frozen=True)
class DilKarari:
    dil: OcrLanguage | None            # None = belirsiz, mevcut dil korunur
    puanlar: tuple[DilPuani, ...]
    denenen: tuple[OcrLanguage, ...]
    bloklar: tuple[TextBlock, ...]     # kazanan dilin (ya da bos) OCR bloklari
    asama: str = "mevcut"              # mevcut | serit | tam


def puanla(dil: OcrLanguage, bloklar: Sequence[TextBlock]) -> DilPuani:
    """K1."""
    dil = OcrLanguage(dil)
    sistemler = [s for b in bloklar for s in map(yazi_sistemi, b.text) if s]
    if not bloklar or not sistemler:
        return DilPuani(dil, 0.0, 0.0, 0, 0.0, "")
    guven = statistics.mean(b.confidence for b in bloklar)
    yerli = sum(1 for s in sistemler if s in _YAZI_SISTEMI[dil]) / len(sistemler)
    kana = sum(1 for s in sistemler if s == "kana") / len(sistemler)
    puan = max(0.0, min(1.0, guven * yerli * min(1.0, len(sistemler) / MIN_HARF)))
    baskin = Counter(sistemler).most_common(1)[0][0]
    return DilPuani(dil, puan, guven, len(sistemler), kana, baskin)


def aday_sirasi(mevcut_puan: DilPuani) -> tuple[OcrLanguage, ...]:
    """K3a: mevcut ciktinin baskin yazi sistemine gore once denenecek diller; kalanlar ADAY_SIRASI."""
    once = {"latin": (OcrLanguage.ENGLISH,), "han": (OcrLanguage.CHINESE, OcrLanguage.JAPAN),
            "kana": (OcrLanguage.JAPAN, OcrLanguage.CHINESE), "hangul": (OcrLanguage.KOREAN,)}.get(mevcut_puan.baskin, ())
    return once + tuple(d for d in ADAY_SIRASI if d not in once)


def serit_kare(kare: Frame, bloklar: Sequence[TextBlock], en_fazla: int = SERIT_SATIR) -> Frame | None:
    """K3a: en buyuk `en_fazla` kutunun kirpiklari alt alta (ortak genislik, `_SERIT_ARALIK` bosluk). Kutu yoksa None.
    Kutular kare koordinatinda; goruntu disina tasanlar kirpilir, bos kalanlar atlanir."""
    img = kare.image
    h, w = img.shape[0], img.shape[1]
    kirpiklar: list[np.ndarray] = []
    for b in sorted(bloklar, key=lambda b: b.bbox.w * b.bbox.h, reverse=True)[:en_fazla]:
        x1 = max(0, b.bbox.x - kare.rect.x - _SERIT_PAY); y1 = max(0, b.bbox.y - kare.rect.y - _SERIT_PAY)
        x2 = min(w, b.bbox.x - kare.rect.x + b.bbox.w + _SERIT_PAY); y2 = min(h, b.bbox.y - kare.rect.y + b.bbox.h + _SERIT_PAY)
        if x2 > x1 and y2 > y1:
            kirpiklar.append(img[y1:y2, x1:x2])
    if not kirpiklar:
        return None
    genislik = max(k.shape[1] for k in kirpiklar)
    yukseklik = sum(k.shape[0] for k in kirpiklar) + _SERIT_ARALIK * (len(kirpiklar) + 1)
    tuval = np.zeros((yukseklik, genislik + 2 * _SERIT_ARALIK, 3), dtype=np.uint8)
    tuval[:] = img[0, 0]   # arka plan rengi: karenin kosesi (koyu/acik uyumu)
    y = _SERIT_ARALIK
    for k in kirpiklar:
        tuval[y:y + k.shape[0], _SERIT_ARALIK:_SERIT_ARALIK + k.shape[1]] = k
        y += k.shape[0] + _SERIT_ARALIK
    return Frame(image=np.ascontiguousarray(tuval), rect=Rect(0, 0, tuval.shape[1], tuval.shape[0]), captured_at=kare.captured_at, seq=kare.seq)


def karar_ver(puanlar: Sequence[DilPuani]) -> OcrLanguage | None:
    """K2."""
    if not puanlar:
        return None
    duzeltilmis: dict[OcrLanguage, float] = {p.dil: p.puan for p in puanlar}
    jp = next((p for p in puanlar if p.dil is OcrLanguage.JAPAN), None)
    if jp is not None:
        if jp.kana_orani < KANA_ESIGI:
            duzeltilmis[OcrLanguage.JAPAN] = jp.puan * 0.5
        elif jp.guven >= 0.7 and OcrLanguage.CHINESE in duzeltilmis:
            duzeltilmis[OcrLanguage.CHINESE] *= 0.5
    sirali = sorted(duzeltilmis.items(), key=lambda dp: dp[1], reverse=True)
    en_iyi, puan = sirali[0]
    ikinci = sirali[1][1] if len(sirali) > 1 else 0.0
    if puan >= KABUL_ESIGI and puan - ikinci >= FARK_ESIGI:
        return en_iyi
    return None


def dili_algila(kare: Frame, motor: Callable[[OcrLanguage], OcrEngine], preset: OcrPreset, *, mevcut: OcrLanguage,
                mevcut_bloklar: Sequence[TextBlock]) -> DilKarari:
    """K3/K4: mevcut dil emin mi -> evet: bitti; hayir: serit asamasi; karar yoksa tam asama."""
    mevcut = OcrLanguage(mevcut)
    mevcut_puan = puanla(mevcut, mevcut_bloklar)
    if mevcut_puan.puan >= EMIN_ESIGI:
        return DilKarari(mevcut, (mevcut_puan,), (mevcut,), tuple(mevcut_bloklar), "mevcut")
    sira = aday_sirasi(mevcut_puan)
    serit = serit_kare(kare, mevcut_bloklar)
    denenen: list[OcrLanguage] = [mevcut]
    if serit is not None:
        sonuclar = _adaylari_oku(serit, motor, preset, sira, mevcut, mevcut_puan, denenen)
        puanlar = tuple(sonuclar[d] for d in denenen)
        secilen = karar_ver(puanlar)
        if secilen is not None:
            if secilen is mevcut:
                return DilKarari(mevcut, puanlar, tuple(denenen), tuple(mevcut_bloklar), "serit")
            try:
                bloklar = tuple(motor(secilen).recognize(kare, preset))
            except TranslatorError:
                bloklar = ()
            return DilKarari(secilen, puanlar, tuple(denenen), bloklar, "serit")
    denenen = [mevcut]
    tam: dict[OcrLanguage, tuple[TextBlock, ...]] = {}
    sonuclar = _adaylari_oku(kare, motor, preset, sira, mevcut, mevcut_puan, denenen, tam)
    puanlar = tuple(sonuclar[d] for d in denenen)
    secilen = karar_ver(puanlar)
    bloklar = tuple(mevcut_bloklar) if secilen is mevcut else tam.get(secilen, ()) if secilen is not None else ()
    return DilKarari(secilen, puanlar, tuple(denenen), bloklar, "tam")


def _adaylari_oku(kare: Frame, motor: Callable[[OcrLanguage], OcrEngine], preset: OcrPreset, sira: Sequence[OcrLanguage],
                  mevcut: OcrLanguage, mevcut_puan: DilPuani, denenen: list[OcrLanguage],
                  bloklar_cikti: dict[OcrLanguage, tuple[TextBlock, ...]] | None = None) -> dict[OcrLanguage, DilPuani]:
    """Adaylari sirayla okur (mevcut atlanir), erken durmayi uygular; puanlari dondurur, `denenen`i uzatir."""
    sonuclar: dict[OcrLanguage, DilPuani] = {mevcut: mevcut_puan}
    for aday in sira:
        if aday in sonuclar:
            continue
        denenen.append(aday)
        try:
            bloklar = tuple(motor(aday).recognize(kare, preset))
        except TranslatorError:
            sonuclar[aday] = DilPuani(aday, 0.0, 0.0, 0, 0.0, "")
            continue
        sonuclar[aday] = puanla(aday, bloklar)
        if bloklar_cikti is not None:
            bloklar_cikti[aday] = bloklar
        if _erken_durulur(sonuclar):
            break
    return sonuclar


def _erken_durulur(sonuclar: Mapping[OcrLanguage, DilPuani]) -> bool:
    en_iyi = karar_ver(list(sonuclar.values()))
    if en_iyi is None or sonuclar[en_iyi].puan < EMIN_ESIGI:
        return False
    if en_iyi in (OcrLanguage.JAPAN, OcrLanguage.CHINESE):
        return OcrLanguage.JAPAN in sonuclar and OcrLanguage.CHINESE in sonuclar
    return True
