"""Bölge çeviri şeridinin seçili alana göre yerleşimi."""
from src.contracts.models import Rect
from src.ui.bolge_geometrisi import SERIT_EN_AZ, serit_dikdortgeni


def test_serit_bolgenin_ustunde_ve_ayni_genislikte() -> None:
    sonuc = serit_dikdortgeni(Rect(100, 300, 500, 100), Rect(0, 0, 1920, 1080))
    assert sonuc == Rect(100, 180, 500, 112)


def test_ustte_yer_yoksa_bolgenin_altina_koyar() -> None:
    sonuc = serit_dikdortgeni(Rect(100, 20, 500, 100), Rect(0, 0, 1920, 1080))
    assert sonuc == Rect(100, 128, 500, 112)


def test_dar_bolge_icin_okunabilir_en_kullanir_ve_ekrana_sikistirir() -> None:
    sonuc = serit_dikdortgeni(Rect(1850, 400, 60, 80), Rect(0, 0, 1920, 1080))
    assert sonuc.w == SERIT_EN_AZ and sonuc.right == 1920
    assert sonuc.y == 280


def test_negatif_koordinatli_ekranda_tamamen_ekranda_kalir() -> None:
    ekran = Rect(-2560, 0, 2560, 1440, monitor_index=1)
    sonuc = serit_dikdortgeni(Rect(-2550, 10, 300, 100), ekran)
    assert sonuc == Rect(-2550, 118, 300, 112, monitor_index=1)


def test_bolge_ekrandan_genisse_serit_ekran_genisligine_iner() -> None:
    sonuc = serit_dikdortgeni(Rect(-50, 300, 1200, 100), Rect(0, 0, 800, 600))
    assert sonuc == Rect(0, 180, 800, 112)

