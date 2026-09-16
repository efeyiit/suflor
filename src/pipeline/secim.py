"""Suflor -- Snapshot secimini butun metne cevirme (T-017, kullanicinin ilk gercek test geri bildirimi).

Sorun: gercek oyunda satirlar ayri segment olarak cevriliyordu ("bir metni butunsel algilayamiyor, satir satir
algiliyor; metnin butunlugu bozuluyor"). Normalizer'in paragraf esigi (satir yuksekligine gore bosluk orani)
oyunun satir araliginda tutmadi. Snapshot'ta kullanici zaten NEYIN bir arada oldugunu secimle soyluyor:
secim = metin. Bu modul secilen satirlari okuma sirasina dizip TEK segmente birlestirir; yalniz iki durumda
boler: (1) buyuk dikey bosluk (ayri kutu/panel), (2) konusmaci satiri (kisa, noktalamasiz ilk satir).

## Sozlesme (K1-K4, olcu: tests/unit/pipeline/test_secim.py)

K1 Satirlar: bloklar once SATIRLARA kumelenir -- dikey ortusmesi min(h)'nin yarisindan buyuk iki blok ayni
   satirdir (olculdu: Japonca'da OCR bir satiri yan yana 2-3 parcaya bolebiliyor; satir birlestirici bunlari
   yakalamiyor). Satir icindeki parcalar x'e gore dizilir; satirlar y'ye gore. Bos girdi -> [].
K2 Gruplama: ardisik iki SATIR arasindaki dikey bosluk (`alt.y - (ust.y + ust.h)`) > `BOSLUK_ORANI` x medyan satir
   yuksekligi ise YENI grup (olculdu, olcum_secim.py: gercek OCR kutularinda satir adimi 2.8 x punto icin
   bosluk/h Korece 1.33, Japonca 2.2 -- 1.6 Japonca'yi boluyordu; 2.5 ikisini de tek tutar, ayri paneller > 3 adim).
   Ayni grup icindeki satirlar tek segment: metinler `satir_birlestir` ile (iki CJK karakter arasinda bosluk
   YOK, aksi halde tek bosluk; `-` ile biten satir + kucuk harf -> tire duser), `bbox` birlesim,
   `source_blocks` secimdeki indeksler (okuma sirasi), `speaker=None`. Hangul CJK sayilmaz (Korece bosluklu).
K3 Konusmaci: grupta >= 2 satir varsa ve ILK satir (a) grubun en genis satirinin `KONUSMACI_GENISLIK_ORANI`
   katindan dar, (b) cumle sonu isaretiyle bitmiyor (`.!?。！？…`), (c) <= `KONUSMACI_MAX_KARAKTER` karakter ise
   AYRI segment olur (cevirisi ayri; kabuk onu ustte gosterir). `Isim:` bicimi de konusmacidir.
K4 Saf, deterministik; metin loglanmaz.
"""
from __future__ import annotations

import statistics
import unicodedata
from collections.abc import Sequence

from src.contracts.models import Rect, Segment, TextBlock

__all__ = ["BOSLUK_ORANI", "KONUSMACI_GENISLIK_ORANI", "KONUSMACI_MAX_KARAKTER", "SATIR_ORTUSME_ORANI", "satir_birlestir",
           "secimi_birlestir"]

BOSLUK_ORANI = 2.5
SATIR_ORTUSME_ORANI = 0.5
KONUSMACI_GENISLIK_ORANI = 0.5
KONUSMACI_MAX_KARAKTER = 24
_CUMLE_SONU = ".!?。！？…"
_KONUSMACI_AYRAC = ":："


def _cjk(ch: str) -> bool:
    if not ch:
        return False
    ad = unicodedata.name(ch, "")
    # Hangul BILEREK yok: Korece kelimeler bosluklu yazilir, satir kirigi kelime sinirindadir -> bosluk gerekir.
    return ad.startswith(("CJK", "HIRAGANA", "KATAKANA", "IDEOGRAPHIC", "FULLWIDTH", "HALFWIDTH KATAKANA"))


def satir_birlestir(satirlar: Sequence[str]) -> str:
    """Satirlari okuma sirasinda birlestirir: CJK-CJK arasinda bosluk yok; `-` + kucuk harf -> tire duser; aksi bosluk."""
    sonuc = ""
    for ham in satirlar:
        s = ham.strip()
        if not s:
            continue
        if not sonuc:
            sonuc = s
        elif sonuc.endswith("-") and s[:1].islower():
            sonuc = sonuc[:-1] + s
        elif _cjk(sonuc[-1]) and _cjk(s[0]):
            sonuc += s
        else:
            sonuc += " " + s
    return sonuc


def _birlesim(kutular: Sequence[Rect]) -> Rect:
    x1 = min(k.x for k in kutular); y1 = min(k.y for k in kutular)
    x2 = max(k.x + k.w for k in kutular); y2 = max(k.y + k.h for k in kutular)
    return Rect(x1, y1, x2 - x1, y2 - y1)


class _Satir:
    """Ayni satirdaki parcalar (x sirali): metin, birlesik kutu, secim indeksleri."""

    def __init__(self, i: int, b: TextBlock) -> None:
        self.parcalar: list[tuple[int, TextBlock]] = [(i, b)]
        self.bbox: Rect = b.bbox

    def ekle(self, i: int, b: TextBlock) -> None:
        self.parcalar.append((i, b))
        self.parcalar.sort(key=lambda ib: ib[1].bbox.x)
        self.bbox = _birlesim([p.bbox for _, p in self.parcalar])

    @property
    def text(self) -> str:
        return satir_birlestir([p.text for _, p in self.parcalar])

    @property
    def indeksler(self) -> tuple[int, ...]:
        return tuple(i for i, _ in self.parcalar)


def _satirlara_ayir(bloklar: Sequence[TextBlock]) -> list[_Satir]:
    """K1: dikey ortusme > SATIR_ORTUSME_ORANI x min(h) -> ayni satir."""
    sirali = sorted(enumerate(bloklar), key=lambda ib: (ib[1].bbox.y + ib[1].bbox.h / 2, ib[1].bbox.x))
    satirlar: list[_Satir] = []
    for i, b in sirali:
        if satirlar:
            son = satirlar[-1].bbox
            ortusme = min(son.y + son.h, b.bbox.y + b.bbox.h) - max(son.y, b.bbox.y)
            if ortusme > SATIR_ORTUSME_ORANI * max(1, min(son.h, b.bbox.h)):
                satirlar[-1].ekle(i, b)
                continue
        satirlar.append(_Satir(i, b))
    return satirlar


def _konusmaci_mi(ilk: _Satir, grup: Sequence[_Satir]) -> bool:
    metin = ilk.text.strip()
    if len(grup) < 2 or not metin or len(metin) > KONUSMACI_MAX_KARAKTER:
        return False
    if metin[-1] in _KONUSMACI_AYRAC:
        return True
    en_genis = max(s.bbox.w for s in grup)
    return ilk.bbox.w < KONUSMACI_GENISLIK_ORANI * en_genis and metin[-1] not in _CUMLE_SONU


def _segment(grup: Sequence[_Satir]) -> Segment:
    metin = satir_birlestir([s.text for s in grup])
    return Segment(text=metin, bbox=_birlesim([s.bbox for s in grup]), speaker=None, placeholders=(),
                   source_blocks=tuple(i for s in grup for i in s.indeksler))


def secimi_birlestir(bloklar: Sequence[TextBlock]) -> list[Segment]:
    """Secilen bloklar -> satirlar -> okuma sirasinda gruplar -> segmentler (K1-K3)."""
    satirlar = _satirlara_ayir(bloklar)
    if not satirlar:
        return []
    medyan_h = statistics.median(s.bbox.h for s in satirlar) or 1
    gruplar: list[list[_Satir]] = [[satirlar[0]]]
    for onceki, simdiki in zip(satirlar, satirlar[1:]):
        bosluk = simdiki.bbox.y - (onceki.bbox.y + onceki.bbox.h)
        if bosluk > BOSLUK_ORANI * medyan_h:
            gruplar.append([simdiki])
        else:
            gruplar[-1].append(simdiki)
    segmentler: list[Segment] = []
    for grup in gruplar:
        if _konusmaci_mi(grup[0], grup):
            segmentler.append(_segment(grup[:1]))
            grup = grup[1:]
        if grup:
            segmentler.append(_segment(grup))
    return [s for s in segmentler if s.text]
