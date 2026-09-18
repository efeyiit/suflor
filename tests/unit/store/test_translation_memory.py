"""Yerel ceviri hafizasi sozlesmesi."""
from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

from src.store.translation_memory import TranslationMemory, metni_normalize_et


def test_normalizasyon_unicode_buyuk_kucuk_ve_bosluk() -> None:
    assert metni_normalize_et("  CAFÉ\n  Door  ") == metni_normalize_et("cafe\u0301 door") == "café door"


def test_add_exact_kalici_ve_guncelleme(tmp_path: Path) -> None:
    yol = tmp_path / "db.sqlite"
    with TranslationMemory(yol) as h:
        h.add("Open the Door", "Kapıyı aç", "eng_Latn")
        assert h.exact(" open  THE door ", "eng_Latn").target == "Kapıyı aç"  # type: ignore[union-attr]
        h.add("OPEN THE DOOR", "Kapıyı aç.", "eng_Latn")
        assert h.count() == 1
    with TranslationMemory(yol) as h:
        assert h.exact("Open the door", "eng_Latn").target == "Kapıyı aç."  # type: ignore[union-attr]


def test_diller_birbirine_karismaz(tmp_path: Path) -> None:
    with TranslationMemory(tmp_path / "db.sqlite") as h:
        h.add("Gift", "Hediye", "eng_Latn")
        h.add("Gift", "Zehir", "deu_Latn")
        assert h.exact("gift", "eng_Latn").target == "Hediye"  # type: ignore[union-attr]
        assert h.exact("gift", "deu_Latn").target == "Zehir"  # type: ignore[union-attr]
        assert h.exact("gift", "eng_Latn", "fr") is None


def test_benzer_eslesme_puan_sirasi_esik_ve_limit(tmp_path: Path) -> None:
    with TranslationMemory(tmp_path / "db.sqlite") as h:
        h.add("Open the western door before midnight", "Gece yarısından önce batı kapısını aç", "eng_Latn")
        h.add("Close the eastern window", "Doğu penceresini kapat", "eng_Latn")
        h.add("Take the blue key", "Mavi anahtarı al", "eng_Latn")
        sonuc = h.find_similar("Open the west door before midnight", "eng_Latn", limit=2, threshold=0.45)
        assert sonuc and sonuc[0].target.startswith("Gece yarısından") and sonuc[0].score > 0.7
        assert h.find_similar("completely unrelated", "eng_Latn", threshold=0.9) == []


def test_wal_yabanci_anahtar_ve_thread_kullanimi(tmp_path: Path) -> None:
    yol = tmp_path / "db.sqlite"
    h = TranslationMemory(yol)
    try:
        t = threading.Thread(target=lambda: h.add("Wait here", "Burada bekle", "eng_Latn"))
        t.start(); t.join()
        assert h.exact("wait here", "eng_Latn") is not None
        with sqlite3.connect(yol) as db:
            assert db.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
            assert db.execute("PRAGMA foreign_keys").fetchone()[0] == 0  # yeni baglantinin ayri ayari
    finally:
        h.close()


def test_bos_girdi_ve_idempotent_close(tmp_path: Path) -> None:
    h = TranslationMemory(tmp_path / "db.sqlite")
    h.add(" ", "hedef", "eng_Latn")
    h.add("kaynak", " ", "eng_Latn")
    assert h.count() == 0 and h.exact(" ", "eng_Latn") is None and h.find_similar(" ", "eng_Latn") == []
    h.close(); h.close()

