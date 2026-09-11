"""TESTER-B RET olcusu (T-008 tur 1) -- mevcut kodda DUSMESI beklenen, duzeltme sonrasi gecmesi gereken.

Sinif: uzun kutu koprusu (KRT-1 O2; implementer docstring'de `[ÖLÇÜLMÜYOR]`; sefin 13:11
`real_check` #1c gercek OCR'da 11 -> 1). Burada OCR YOK: sentetik geometriyle ayni cokme.

Neden mercek B'nin bulgusu: teslimdeki `test_k2_grup_icinde_dikey_ortusme_grubun_ilk_bloguyla`
bu sinifi "olctugunu" soyluyor ama fixture'i uzun kutuyu ORTAYA (x=60) koyuyor; grubun ilk
blogu kisa `a` oldugu icin `c` ayri kaliyor ve test gecer. Erisilebilir geometri (etiket
SOLDA, x=0; etiket|deger duzeninin dogal hali) uzun kutuyu grubun ILK blogu yapar: iki
satirin butun kelimeleri onunla ortusur, x sirasinda satirlar birbirine GECER ve tek blok
cikar ("T a d b e c f" -- iki satir kelime kelime fermuarlanmis). Olcu mekanizmayi
("grubun ilk blogu") kancaliyor, degismezi ("farkli satirlar birlesmez") degil (§4.6/4, /7).

Degismez burada MEKANIZMASIZ yazilir: bir ciktinin `line_boxes` parcalari ikili olarak
dikey ortusmeli (>= 0.5 * min(h)); aksi halde farkli satirlar tek bloga girmistir.
"""
from __future__ import annotations

import itertools

import pytest

import tb_bariyer  # noqa: F401
from src.contracts.models import Rect, TextBlock
from src.ocr.satir_birlestirici import DIKEY_ORTUSME_ESIGI, satirlari_birlestir


def _b(x: int, y: int, w: int, h: int, t: str) -> TextBlock:
    return TextBlock(text=t, bbox=Rect(x, y, w, h), confidence=0.9)


def _parcalar_ayni_satirda(blok: TextBlock) -> bool:
    for p, q in itertools.combinations(blok.line_boxes, 2):
        ortusme = min(p.bottom, q.bottom) - max(p.y, q.y)
        if ortusme < DIKEY_ORTUSME_ESIGI * min(p.h, q.h):
            return False
    return True


def _kopru_fixture(etiket: bool, kayma: int) -> list[TextBlock]:
    """Etiket T (x=0, h=60, iki satiri kapsar) + satir 1 (y=5) + satir 2 (y=40, x'i `kayma` kadar kaymis)."""
    s1 = [_b(50, 5, 50, 20, "a"), _b(110, 5, 50, 20, "b"), _b(170, 5, 50, 20, "c")]
    s2 = [_b(50 + kayma, 40, 50, 20, "d"), _b(110 + kayma, 40, 50, 20, "e"), _b(170 + kayma, 40, 50, 20, "f")]
    return ([_b(0, 0, 40, 60, "T")] if etiket else []) + s1 + s2


@pytest.mark.parametrize("kayma", [5, 0, 12], ids=["satir2-x+5-fermuar", "satir2-x-ayni", "satir2-x+12"])
def test_ret_uzun_etiket_solda_iki_satiri_tek_bloga_almamali(kayma: int) -> None:
    cikti = satirlari_birlestir(_kopru_fixture(etiket=True, kayma=kayma))
    metinler = [c.text for c in cikti]
    # DEGISMEZ 1: hicbir blok farkli satirlardan parca tasimaz
    karisik = [c.text for c in cikti if not _parcalar_ayni_satirda(c)]
    assert karisik == [], f"farkli satirlar tek blokta: {karisik}; cikti {metinler}"
    # DEGISMEZ 2: iki satirin kelimeleri kendi icinde birlesik kalir (etiketsiz pozitif kontrolle ayni)
    assert "a b c" in " | ".join(metinler) and "d e f" in " | ".join(metinler), metinler


def test_ret_pozitif_kontrol_etiketsiz_iki_satir_dogru() -> None:
    """Etiket olmadan ayni geometri dogru: bu, dusmenin sebebinin ETIKET oldugunu gosterir."""
    assert [c.text for c in satirlari_birlestir(_kopru_fixture(etiket=False, kayma=5))] == ["a b c", "d e f"]
