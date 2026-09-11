"""Tester-A yardimcilari: gecici sozluk kurma, ASCII-guvenli yazim."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
if str(KOK) not in sys.path:
    sys.path.insert(0, str(KOK))

from src.contracts.models import Rect, Segment  # noqa: E402
from src.translate.sozluk import GlossaryStore  # noqa: E402

_TMP: list[tempfile.TemporaryDirectory[str]] = []


def sozluk(*cift: tuple[str, str] | dict, ad: str = "s.json", ust: dict | None = None) -> GlossaryStore:
    """(kaynak, hedef) ciftleri ya da ham kayit dict'lerinden gecici bir GlossaryStore."""
    td = tempfile.TemporaryDirectory()
    _TMP.append(td)
    kayitlar = []
    for c in cift:
        if isinstance(c, dict):
            kayitlar.append(c)
        else:
            k, h = c
            kayitlar.append({"kaynak": k, "hedef": h})
    veri: dict = {"terimler": kayitlar}
    if ust:
        veri.update(ust)
    yol = Path(td.name) / ad
    yol.write_bytes(json.dumps(veri, ensure_ascii=False).encode("utf-8"))
    return GlossaryStore(yol)


def sozluk_ham(veri: object, ad: str = "s.json") -> GlossaryStore:
    """Ham JSON nesnesinden GlossaryStore (sema sinirlari icin)."""
    td = tempfile.TemporaryDirectory()
    _TMP.append(td)
    yol = Path(td.name) / ad
    yol.write_bytes(json.dumps(veri, ensure_ascii=False).encode("utf-8"))
    return GlossaryStore(yol)


def seg(text: str, placeholders: tuple[str, ...] = (), speaker: str | None = None) -> Segment:
    return Segment(text=text, bbox=Rect(0, 0, 10, 10), speaker=speaker, placeholders=placeholders, source_blocks=(0,))


def u(s: str) -> str:
    """ASCII-guvenli gosterim (cp1254 konsol)."""
    return s.encode("ascii", "backslashreplace").decode("ascii")


def hit_ozet(hits) -> list[tuple[int, int, str, str]]:
    return [(h.start, h.end, u(h.source_term), u(h.target_term)) for h in hits]
