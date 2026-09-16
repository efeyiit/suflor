"""T-017 -- secimi_birlestir K1-K4."""
from __future__ import annotations

from src.contracts.models import Rect, TextBlock
from src.pipeline.secim import BOSLUK_ORANI, satir_birlestir, secimi_birlestir


def b(metin: str, x: int, y: int, w: int, h: int = 30) -> TextBlock:
    return TextBlock(text=metin, bbox=Rect(x, y, w, h), confidence=0.9)


def test_k1_bos_ve_siralama() -> None:
    assert secimi_birlestir([]) == []
    s = secimi_birlestir([b("ikinci satır.", 10, 40, 300), b("Birinci satır", 10, 0, 300)])   # ters verilmis
    assert len(s) == 1 and s[0].text == "Birinci satır ikinci satır." and s[0].source_blocks == (1, 0)


def test_k2_satir_ici_bosluk_ayni_grup_kr_cumle_butunlugu() -> None:
    # gercek oyun sikayeti: cumle iki satira bolunmus, satir satir cevriliyordu
    s = secimi_birlestir([b("방앗간을 지나 동쬽", 10, 0, 300), b("길로 가십시오.", 10, 38, 240)])
    assert len(s) == 1 and s[0].text == "방앗간을 지나 동쬽 길로 가십시오." and s[0].bbox == Rect(10, 0, 300, 68)   # Korece: bosluk


def test_k2_latin_bosluk_ve_tire() -> None:
    assert satir_birlestir(["The village el-", "der waits.", "Go east."]) == "The village elder waits. Go east."
    assert satir_birlestir(["日本語の", "テキスト"]) == "日本語のテキスト"
    assert satir_birlestir(["한국어", "문장"]) == "한국어 문장"   # Hangul bosluklu
    assert satir_birlestir(["Marcus", "が来た"]) == "Marcus が来た"   # Latin-CJK arasi bosluk
    assert satir_birlestir(["", "  ", "a"]) == "a"


def test_k2_buyuk_dikey_bosluk_yeni_grup() -> None:
    h = 30
    yakin = int(BOSLUK_ORANI * h) - 1
    uzak = int(BOSLUK_ORANI * h) + 2
    ayni = secimi_birlestir([b("a.", 0, 0, 200, h), b("b.", 0, h + yakin, 200, h)])
    ayri = secimi_birlestir([b("a.", 0, 0, 200, h), b("b.", 0, h + uzak, 200, h)])
    assert len(ayni) == 1 and len(ayri) == 2 and [s.text for s in ayri] == ["a.", "b."]


def test_k1_ayni_satirin_yan_yana_parcalari_x_sirasinda_birlesir() -> None:
    # olculdu: Japonca'da OCR bir satiri 2-3 parcaya boluyor; y'leri birkac px oynuyor -> saf (y, x) sirasi metni bozar
    parcalar = [b("東の道を行くと、", 420, 103, 300, 30), b("水車小屋を過ぎて", 60, 100, 340, 34), b("古い祠がある。", 740, 101, 260, 31),
                b("日が沈む前にそこで会おう。", 60, 170, 520, 32)]
    s = secimi_birlestir(parcalar)
    assert len(s) == 1 and s[0].text == "水車小屋を過ぎて東の道を行くと、古い祠がある。日が沈む前にそこで会おう。"
    assert s[0].source_blocks == (1, 0, 2, 3)


def test_k2_japonca_gercek_olcum_adim_2_8_tek_segment() -> None:
    # olcum_secim.py: JP satir adimi 2.8 x punto -> kutu h ~31, bosluk ~68 (2.2 x h): tek metin kalmali
    s = secimi_birlestir([b("水車小屋を過ぎて東の道を行くと、古い祠がある。", 60, 0, 900, 31), b("日が沈む前にそこで会おう。", 60, 99, 520, 30),
                          b("急いだほうがいい。", 60, 198, 360, 32), b("夜道は危ないからな。", 60, 297, 400, 31)])
    assert len(s) == 1


def test_k3_konusmaci_kisa_noktalamasiz_ilk_satir_ayri() -> None:
    s = secimi_birlestir([b("장로 마르쿠스", 10, 0, 130), b("마을 장로가 당신을 기다리고 있습니다.", 10, 40, 470), b("방앗간을 지나 동쪽 길로 가십시오.", 10, 80, 420)])
    assert [x.text for x in s] == ["장로 마르쿠스", "마을 장로가 당신을 기다리고 있습니다. 방앗간을 지나 동쪽 길로 가십시오."]
    assert s[0].source_blocks == (0,) and s[1].source_blocks == (1, 2)


def test_k3_konusmaci_degil_uzun_ya_da_noktali_ya_da_tek_satir() -> None:
    # noktali kisa ilk satir -> cumle, konusmaci degil
    s = secimi_birlestir([b("Evet.", 10, 0, 60), b("Hadi gidelim buradan artık.", 10, 40, 400)])
    assert len(s) == 1
    # tek satir -> konusmaci sayilmaz
    assert len(secimi_birlestir([b("Marcus", 10, 0, 80)])) == 1
    # genis ilk satir -> konusmaci degil
    assert len(secimi_birlestir([b("Uzun bir giriş satırı burada", 10, 0, 380), b("ve devamı.", 10, 40, 400)])) == 1


def test_k3_isim_iki_nokta_konusmaci() -> None:
    s = secimi_birlestir([b("Marcus:", 10, 0, 380), b("Come with me.", 10, 40, 400)])
    assert [x.text for x in s] == ["Marcus:", "Come with me."]


def test_k4_deterministik_ve_girdi_degismez() -> None:
    girdi = [b("x", 0, 0, 100), b("y", 0, 35, 100)]
    kopya = list(girdi)
    a = secimi_birlestir(girdi); c = secimi_birlestir(girdi)
    assert a == c and girdi == kopya
