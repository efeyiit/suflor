"""SQLite tabanli yerel ceviri hafizasi.

Ayni kaynak metin icin son onayli/uretilmis Turkceyi kesin eslesmeyle geri verir;
benzer metinleri trigram aday secimiyle bulur. Veritabani WAL modundadir ve
uygulamanin OCR/ceviri thread'lerinden kilit altinda kullanilabilir.
"""
from __future__ import annotations

import os
import re
import sqlite3
import threading
import unicodedata
from pathlib import Path

from src.contracts.models import Pair

__all__ = ["TranslationMemory", "metni_normalize_et", "varsayilan_hafiza_yolu"]

_BOSLUK = re.compile(r"\s+")


def varsayilan_hafiza_yolu() -> Path:
    kok = os.environ.get("APPDATA")
    taban = Path(kok) / "Suflor" if kok else Path.home() / ".suflor"
    return taban / "db.sqlite"


def metni_normalize_et(metin: str) -> str:
    """Eslesme anahtari: NFC, casefold ve tek bosluk; asil metin ayrica korunur."""
    return _BOSLUK.sub(" ", unicodedata.normalize("NFC", metin).casefold()).strip()


def _trigramlar(metin: str) -> frozenset[str]:
    dolgulu = f"  {metin}  "
    return frozenset(dolgulu[i:i + 3] for i in range(max(0, len(dolgulu) - 2)))


def _dice(a: frozenset[str], b: frozenset[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return 2.0 * len(a & b) / (len(a) + len(b))


class TranslationMemory:
    """Kalici kesin ve benzer ceviri ciftleri."""

    def __init__(self, yol: Path | None = None) -> None:
        self._yol = Path(yol) if yol is not None else varsayilan_hafiza_yolu()
        self._yol.parent.mkdir(parents=True, exist_ok=True)
        self._kilit = threading.RLock()
        self._kapandi = False
        self._db = sqlite3.connect(self._yol, timeout=5.0, check_same_thread=False)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA synchronous=NORMAL")
        self._db.execute("PRAGMA foreign_keys=ON")
        self._db.executescript(
            """
            CREATE TABLE IF NOT EXISTS ceviri_hafizasi (
                id INTEGER PRIMARY KEY,
                kaynak TEXT NOT NULL,
                normalize TEXT NOT NULL,
                hedef TEXT NOT NULL,
                kaynak_dili TEXT NOT NULL,
                hedef_dili TEXT NOT NULL,
                guncellendi TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(normalize, kaynak_dili, hedef_dili)
            );
            CREATE TABLE IF NOT EXISTS ceviri_trigram (
                kayit_id INTEGER NOT NULL REFERENCES ceviri_hafizasi(id) ON DELETE CASCADE,
                gram TEXT NOT NULL,
                PRIMARY KEY(kayit_id, gram)
            );
            CREATE TABLE IF NOT EXISTS ceviri_gram_sayac (
                gram TEXT PRIMARY KEY,
                sayi INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS ix_ceviri_trigram_gram ON ceviri_trigram(gram);
            CREATE INDEX IF NOT EXISTS ix_ceviri_dil ON ceviri_hafizasi(kaynak_dili, hedef_dili);
            """
        )
        sayac_bos = self._db.execute("SELECT 1 FROM ceviri_gram_sayac LIMIT 1").fetchone() is None
        trigram_var = self._db.execute("SELECT 1 FROM ceviri_trigram LIMIT 1").fetchone() is not None
        if sayac_bos and trigram_var:
            self._db.execute(
                "INSERT INTO ceviri_gram_sayac(gram, sayi) "
                "SELECT gram, COUNT(*) FROM ceviri_trigram GROUP BY gram"
            )
        self._db.commit()

    @property
    def yol(self) -> Path:
        return self._yol

    def exact(self, kaynak: str, kaynak_dili: str, hedef_dili: str = "tr") -> Pair | None:
        anahtar = metni_normalize_et(kaynak)
        if not anahtar:
            return None
        with self._kilit:
            self._acik_mi()
            satir = self._db.execute(
                "SELECT kaynak, hedef FROM ceviri_hafizasi "
                "WHERE normalize=? AND kaynak_dili=? AND hedef_dili=?",
                (anahtar, kaynak_dili, hedef_dili),
            ).fetchone()
        return None if satir is None else Pair(str(satir[0]), str(satir[1]), 1.0)

    def add(self, kaynak: str, hedef: str, kaynak_dili: str, hedef_dili: str = "tr") -> None:
        anahtar = metni_normalize_et(kaynak)
        if not anahtar or not hedef.strip():
            return
        gramlar = _trigramlar(anahtar)
        with self._kilit:
            self._acik_mi()
            self._db.execute(
                "INSERT INTO ceviri_hafizasi(kaynak, normalize, hedef, kaynak_dili, hedef_dili) "
                "VALUES(?,?,?,?,?) ON CONFLICT(normalize, kaynak_dili, hedef_dili) DO UPDATE SET "
                "kaynak=excluded.kaynak, hedef=excluded.hedef, guncellendi=CURRENT_TIMESTAMP",
                (kaynak, anahtar, hedef, kaynak_dili, hedef_dili),
            )
            kayit = self._db.execute(
                "SELECT id FROM ceviri_hafizasi WHERE normalize=? AND kaynak_dili=? AND hedef_dili=?",
                (anahtar, kaynak_dili, hedef_dili),
            ).fetchone()
            assert kayit is not None
            kimlik = int(kayit[0])
            eski_gramlar = tuple(
                str(satir[0])
                for satir in self._db.execute("SELECT gram FROM ceviri_trigram WHERE kayit_id=?", (kimlik,))
            )
            self._db.execute("DELETE FROM ceviri_trigram WHERE kayit_id=?", (kimlik,))
            self._db.executemany(
                "UPDATE ceviri_gram_sayac SET sayi=sayi-1 WHERE gram=?",
                ((gram,) for gram in eski_gramlar),
            )
            self._db.execute("DELETE FROM ceviri_gram_sayac WHERE sayi<=0")
            self._db.executemany(
                "INSERT INTO ceviri_trigram(kayit_id, gram) VALUES(?,?)",
                ((kimlik, gram) for gram in gramlar),
            )
            self._db.executemany(
                "INSERT INTO ceviri_gram_sayac(gram, sayi) VALUES(?,1) "
                "ON CONFLICT(gram) DO UPDATE SET sayi=sayi+1",
                ((gram,) for gram in gramlar),
            )
            self._db.commit()

    def find_similar(self, kaynak: str, kaynak_dili: str, hedef_dili: str = "tr", *,
                     limit: int = 3, threshold: float = 0.72) -> list[Pair]:
        anahtar = metni_normalize_et(kaynak)
        if not anahtar or limit < 1:
            return []
        gramlar = _trigramlar(anahtar)
        if not gramlar:
            return []
        with self._kilit:
            self._acik_mi()
            # Tum yaygin trigramlari GROUP BY ile taramak yerine, yazma sirasinda
            # tutulan sayactan en seyrek alti grami secip aday kumesini daralt.
            gram_yerleri = ",".join("?" for _ in gramlar)
            seyrek = self._db.execute(
                f"SELECT gram FROM ceviri_gram_sayac WHERE gram IN ({gram_yerleri}) "
                "ORDER BY sayi ASC LIMIT 2",
                tuple(gramlar),
            ).fetchall()
            aday_gramlar = tuple(str(satir[0]) for satir in seyrek)
            if not aday_gramlar:
                return []
            yerler = ",".join("?" for _ in aday_gramlar)
            parametreler: tuple[object, ...] = aday_gramlar + (
                kaynak_dili, hedef_dili, max(20, limit * 12),
            )
            satirlar = self._db.execute(
                f"SELECT DISTINCT h.kaynak, h.normalize, h.hedef "
                f"FROM ceviri_trigram t JOIN ceviri_hafizasi h ON h.id=t.kayit_id "
                f"WHERE t.gram IN ({yerler}) AND h.kaynak_dili=? AND h.hedef_dili=? "
                f"LIMIT ?",
                parametreler,
            ).fetchall()
        puanli = [
            Pair(str(kaynak_metin), str(hedef), _dice(gramlar, _trigramlar(str(normalize))))
            for kaynak_metin, normalize, hedef in satirlar
        ]
        return sorted((p for p in puanli if p.score >= threshold), key=lambda p: p.score, reverse=True)[:limit]

    def count(self) -> int:
        with self._kilit:
            self._acik_mi()
            satir = self._db.execute("SELECT COUNT(*) FROM ceviri_hafizasi").fetchone()
        return int(satir[0]) if satir is not None else 0

    def close(self) -> None:
        with self._kilit:
            if self._kapandi:
                return
            self._kapandi = True
            self._db.close()

    def _acik_mi(self) -> None:
        if self._kapandi:
            raise RuntimeError("ceviri hafizasi kapali")

    def __enter__(self) -> TranslationMemory:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
