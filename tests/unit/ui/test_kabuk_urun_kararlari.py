"""Ürün kabuğunun kullanıcıya dönük sabit kararları."""
from demo.kabuk import OTOMATIK_BASLANGIC
from src.ocr.rapid_engine import OcrLanguage


def test_yeni_oturum_otomatik_dile_ingilizceyle_baslar() -> None:
    assert OTOMATIK_BASLANGIC is OcrLanguage.ENGLISH

