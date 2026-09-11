"""Tester-A RET kanıtı — uzun kutu köprüsü, GERÇEK OCR geometrisi (tur 1).

Kaynak: `a6_gercek_ocr.py` [4b] (`tester_A_evidence/a6-gercek-ocr.txt`), gerçek motor,
`tester_A/fixtures/kr_etiket_ortali_*.png`: solda iki satırı kaplayan büyük etiket
(2× font, dikey ortalı), sağda iki KR satırı (font 30). Tespitçi 11 kutu verir
(etiket + 5 + 5); aynı görüntü etiket karartılınca 10 kutu → 2 blok (DOĞRU).
Etiketle: 1 blok (11 parça, iki satırın kelimeleri x sırasında İÇ İÇE — metin iki
cümlenin kelime salatası) ya da 9–10 blok (satırlar PARÇALANDI — kelime-kelime
çeviri, S3 sınıfı). Sebep: etiket `(y,x)`-ilk blok olunca satır bölümlemesi iki
satırı tek "satır"a toplar; satır içi `(x,y)` sıralaması kelimeleri karıştırır.

Referans kanal (bağımsız, §4.6/8): çizilen satır merkezleri (PIL textbbox) —
uygulamanın çıktısından türetilmedi. Ayırt etme ölçüsü (düzeltme turu için):
  (a) her çizilen satırın 5 kelime kutusu TAM OLARAK BİR çıktı bloğunda;
  (b) hiçbir çıktı bloğu iki çizilen satırdan kelime kutusu içermez;
  (c) etiketsiz girdi → 2 blok (mevcut doğru davranış korunur);
  (d) `dlg_KR` 17 → [2,5,5,5] ve 1-em menü 4 → 4 (real_check #1/#4c) bozulmaz.
Etiketin kendi bloğu serbesttir (ayrı ya da satır 0'a yapışık).

Bu dosya şu an KIRMIZI (3 test düşer) — bu, ölçünün ateşlediğinin kanıtıdır
(§4.6/10 pozitif kontrol: etiketsiz varyantlar GEÇER).
"""
from __future__ import annotations

import pytest

from src.contracts.models import Rect, TextBlock
from src.ocr.satir_birlestirici import satirlari_birlestir

# (ad, çizilen satır merkezleri, etiket kutusu, kelime kutuları [(x,y,w,h), ...]) — gerçek OCR çıktısı
GERCEK_GEOMETRI: list[tuple[str, list[int], tuple[int, int, int, int], list[tuple[int, int, int, int]]]] = [
    (
        "kr_etiket_ortali_60_45_10",  # 11 -> 1 blok (11 parça iç içe) — a6-gercek-ocr.txt
        [81, 126],
        (57, 55, 125, 72),
        [(609, 64, 120, 35), (206, 65, 59, 34), (277, 66, 87, 31), (378, 66, 87, 32), (481, 68, 113, 28),
         (508, 109, 59, 35), (365, 110, 61, 34), (435, 110, 61, 33), (205, 111, 148, 32), (580, 111, 117, 32)],
    ),
    (
        "kr_etiket_ortali_72_48_14",  # 11 -> 9 blok (parçalandı)
        [81, 129],
        (57, 56, 149, 81),
        [(230, 65, 59, 34), (300, 65, 88, 33), (634, 65, 119, 34), (403, 66, 86, 31), (504, 67, 114, 30),
         (531, 112, 61, 36), (389, 113, 61, 34), (460, 113, 60, 34), (604, 114, 117, 32), (230, 115, 147, 31)],
    ),
    (
        "kr_etiket_ortali_60_40_8",  # 11 -> 10 blok (parçalandı)
        [81, 121],
        (59, 62, 121, 67),
        [(609, 64, 120, 35), (206, 65, 59, 34), (276, 66, 88, 32), (379, 66, 86, 32), (481, 68, 113, 28),
         (365, 105, 62, 34), (436, 105, 60, 34), (508, 105, 59, 34), (206, 106, 147, 32), (581, 107, 116, 31)],
    ),
]


def _blok(x: int, y: int, w: int, h: int, t: str) -> TextBlock:
    return TextBlock(text=t, bbox=Rect(x, y, w, h), confidence=0.9)


def _cizilen_satir(r: Rect, merkezler: list[int]) -> int:
    cy = r.y + r.h / 2
    return min(range(len(merkezler)), key=lambda i: abs(merkezler[i] - cy))


def _kelime_bloklari(cikti: list[TextBlock], kelime_kutulari: set[Rect]) -> dict[Rect, int]:
    """Her kelime kutusu hangi çıktı bloğunda (indeks)."""
    yer: dict[Rect, int] = {}
    for i, b in enumerate(cikti):
        parcalar = b.line_boxes if b.line_boxes else (b.bbox,)
        for r in parcalar:
            if r in kelime_kutulari:
                yer[r] = i
    return yer


@pytest.mark.parametrize("ad, merkezler, etiket, kelimeler", GERCEK_GEOMETRI, ids=[g[0] for g in GERCEK_GEOMETRI])
def test_ret_etiketsiz_iki_satir_dogru_POZITIF_KONTROL(
    ad: str, merkezler: list[int], etiket: tuple[int, int, int, int], kelimeler: list[tuple[int, int, int, int]]
) -> None:
    """Etiket yokken (aynı gerçek kelime geometrisi) → 2 blok, her satır 5 parça. GEÇER."""
    bl = [_blok(*k, f"w{i}") for i, k in enumerate(kelimeler)]
    cikti = satirlari_birlestir(bl)
    assert len(cikti) == 2
    assert [len(c.line_boxes) for c in cikti] == [5, 5]
    for c in cikti:
        assert len({_cizilen_satir(r, merkezler) for r in c.line_boxes}) == 1


@pytest.mark.parametrize("ad, merkezler, etiket, kelimeler", GERCEK_GEOMETRI, ids=[g[0] for g in GERCEK_GEOMETRI])
def test_ret_buyuk_etiket_solda_satirlar_bozulmamali(
    ad: str, merkezler: list[int], etiket: tuple[int, int, int, int], kelimeler: list[tuple[int, int, int, int]]
) -> None:
    """Etiketle: (a) her satırın 5 kelimesi tek blokta, (b) hiçbir blok iki satırdan kelime
    içermez. ŞU AN DÜŞER: 60_45_10 → tek blok (iki satır iç içe); 72_48_14 → 9 blok;
    60_40_8 → 10 blok."""
    bl = [_blok(*etiket, "ETIKET")] + [_blok(*k, f"w{i}") for i, k in enumerate(kelimeler)]
    kelime_kutulari = {Rect(*k) for k in kelimeler}
    cikti = satirlari_birlestir(bl)
    yer = _kelime_bloklari(cikti, kelime_kutulari)
    assert len(yer) == len(kelimeler), "her kelime kutusu çıktıda bir kez"
    satir_blok: dict[int, set[int]] = {}
    for r, i in yer.items():
        satir_blok.setdefault(_cizilen_satir(r, merkezler), set()).add(i)
    ozet = {s: sorted(v) for s, v in sorted(satir_blok.items())}
    # (a) her çizilen satırın kelimeleri TEK blokta
    assert all(len(v) == 1 for v in satir_blok.values()), (
        f"{ad}: satır -> bloklar {ozet}; toplam {len(cikti)} blok, parça sayıları "
        f"{[len(c.line_boxes) or 1 for c in cikti]} (satırlar parçalandı)"
    )
    # (b) iki satır aynı blokta değil
    assert satir_blok[0].isdisjoint(satir_blok[1]), (
        f"{ad}: iki satır aynı blokta {ozet}; blok parça sayıları {[len(c.line_boxes) or 1 for c in cikti]}"
    )
