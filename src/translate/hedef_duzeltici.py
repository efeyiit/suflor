"""Suflor -- hedef tarafi duzeltme (T-015): ceviri CIKTISINDA kelime sinirli, buyuk/kucuk duyarsiz ikame.

Neden var (T-011 karari, Tester-B O-B10 olcumu): sozluk kaynak tarafinda calisir; unvanlar gri bolgedir --
unvani gommek bilesik cumleyi bozuyor ("Koy ihtiyari" -> "Ihtiyar kasabasi"), gommemek yalniz-unvan+ad
segmentinde Ingilizce sizdiriyor ("장로 Marcus" -> "Elder Marcus", 1/10) ya da modelin ad yazimini oynatiyor
("Marks", "Markos", "Eira"). Bu modul o kalan sinifi CIKTIDA duzeltir: `Elder -> İhtiyar`, `Marks -> Marcus`.

## Sozlesme (K1-K5, olcu: tests/unit/translate/test_hedef_duzeltici.py)

K1 Kelime sinirli: `Elder` -> `Elderberry`/`elders` icinde DEGISMEZ; sinir = metin ucu, bosluk, noktalama,
   kesme (`Marks'ın` -> `Marcus'ın`: Turkce ek korunur). Eslesme buyuk/kucuk duyarsiz (Turkce katlama:
   `I/ı`, `İ/i` ayri tutulur -- `casefold` degil, ozel katlama); ikame metni oldugu gibi yazilir (`hedef`).
K2 En uzun kaynak once; ortusmesiz; cikti uzerinde tekrar taranmaz (bir gecis: `Marks -> Marcus` sonra
   `Marcus -> X` kurali ayni cagrida ZINCIRLENMEZ). Ayni kaynak iki kez -> `ValueError`.
K3 Yukleme: sozluk JSON'unun istege bagli `"hedef_duzeltmeler": [{"kaynak": str, "hedef": str}]` listesi;
   anahtar yoksa BOS duzeltici (kimlik). Bos/bosluklu kaynak/hedef, `str` olmayan alan -> `ValueError`
   (mesajda alan adi). Dosya bayt ile acilir (T-011 K6 ile ayni).
K4 Saf: `duzelt(metin) -> str`, I/O yok, durum yok; bos kural seti -> ayni dize (`is`). Metin loglanmaz.
K5 Butce: 1000 ceviri x 50 kural < 20 ms (tek derlenmis desen, alternation en uzun once).
"""
from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path

__all__ = ["HedefDuzeltici"]

_ANAHTAR = "hedef_duzeltmeler"
# Sinir: kelime karakteri olmayan her sey (Unicode harf/rakam/alt cizgi disinda). Kesme isareti sinirdir
# -> "Marks'ın" icinde "Marks" eslesir, ek korunur.
_SINIR_ONCE = r"(?<![^\W_])"
_SINIR_SONRA = r"(?![^\W_])"


def _katla(metin: str) -> str:
    """Turkce-guvenli katlama: I->ı, İ->i, sonra lower (casefold 'İ'yi iki kodpointe acar -- T-011 dersi)."""
    return metin.replace("I", "ı").replace("İ", "i").lower()


class HedefDuzeltici:
    """Ceviri ciktisinda kelime sinirli ikame tablosu."""

    def __init__(self, kurallar: Mapping[str, str] | Sequence[tuple[str, str]] = ()) -> None:
        ciftler = list(kurallar.items()) if isinstance(kurallar, Mapping) else list(kurallar)
        self._tablo: dict[str, str] = {}
        for kaynak, hedef in ciftler:
            if not isinstance(kaynak, str) or not isinstance(hedef, str):
                raise ValueError("kural alanlari 'kaynak' ve 'hedef' str olmali")
            if not kaynak.strip() or kaynak != kaynak.strip():
                raise ValueError("kaynak bos ya da bas/son bosluklu olamaz")
            if not hedef.strip() or hedef != hedef.strip():
                raise ValueError(f"hedef bos ya da bas/son bosluklu olamaz (kaynak: {kaynak!r})")
            anahtar = _katla(kaynak)
            if anahtar in self._tablo:
                raise ValueError(f"tekrar eden kaynak: {kaynak!r}")
            self._tablo[anahtar] = hedef
        self._desen: re.Pattern[str] | None = None
        if self._tablo:
            parcalar = sorted(self._tablo, key=len, reverse=True)   # K2: en uzun once
            self._desen = re.compile(_SINIR_ONCE + "(" + "|".join(re.escape(p) for p in parcalar) + ")" + _SINIR_SONRA, re.IGNORECASE)

    @classmethod
    def dosyadan(cls, yol: Path | str) -> HedefDuzeltici:
        """Sozluk JSON'undaki istege bagli `hedef_duzeltmeler` listesinden; anahtar yoksa bos duzeltici."""
        veri = json.loads(Path(yol).read_bytes())
        if not isinstance(veri, dict):
            raise ValueError("sozluk dosyasi ust duzeyde nesne olmali")
        ham = veri.get(_ANAHTAR, [])
        if not isinstance(ham, list):
            raise ValueError(f"'{_ANAHTAR}' liste olmali")
        ciftler: list[tuple[str, str]] = []
        for i, kayit in enumerate(ham):
            if not isinstance(kayit, dict) or "kaynak" not in kayit or "hedef" not in kayit:
                raise ValueError(f"'{_ANAHTAR}'[{i}]: 'kaynak' ve 'hedef' alanlari gerekli")
            ciftler.append((kayit["kaynak"], kayit["hedef"]))
        return cls(ciftler)

    def __len__(self) -> int:
        return len(self._tablo)

    @property
    def kurallar(self) -> Mapping[str, str]:
        return dict(self._tablo)

    def duzelt(self, metin: str) -> str:
        """Kelime sinirli, buyuk/kucuk duyarsiz tek gecis ikame; kural yoksa ayni dize."""
        if self._desen is None:
            return metin
        return self._desen.sub(self._ikame, metin)

    def _ikame(self, m: re.Match[str]) -> str:
        anahtar = _katla(m.group(1))
        return self._tablo.get(anahtar, m.group(0))

    def hepsini_duzelt(self, metinler: Sequence[str]) -> list[str]:
        return [self.duzelt(m) for m in metinler]
