"""Windows çift-tık başlatıcısının proje ortamını seçmesi."""
from pathlib import Path


def test_bat_once_proje_sanal_ortamindaki_pythonw_kullanir() -> None:
    metin = Path("Suflor.bat").read_text(encoding="utf-8").lower()
    sanal = 'if exist "%~dp0.venv\\scripts\\pythonw.exe"'
    sistem = "where pythonw.exe"
    assert sanal in metin
    assert sistem in metin
    assert metin.index(sanal) < metin.index(sistem)
    assert '"%~dp0.venv\\scripts\\pythonw.exe" "%~dp0demo\\kabuk.py"' in metin


def test_bat_cmd_codepage_bagimsiz_ascii_karakterlerden_olusur() -> None:
    ham = Path("Suflor.bat").read_bytes()
    assert all(b < 128 for b in ham)
