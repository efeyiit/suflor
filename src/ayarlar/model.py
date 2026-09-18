"""Suflor -- ayar modeli ve deposu (T-016).

Ayarlar `%APPDATA%\\Suflor\\ayarlar.json` dosyasinda (Qt `AppDataLocation`; `varsayilan_ayar_yolu()`), JSON,
UTF-8, insan tarafindan duzenlenebilir. Depoya girmez (`.gitignore` `settings.json` benzeri kisisel veri).

## Sozlesme (K1-K5, olcu: tests/unit/ayarlar/test_model.py)

K1 Model: `Ayarlar` dondurulmus dataclass; alanlar ve varsayilanlar: `dil="auto"` (T-018: algila; ya da OcrLanguage degeri),
   `kisayol_anlik="Ctrl+Alt+D"`, `kisayol_bolge="Ctrl+Alt+R"`, `sozluk_yolu=None` (str ya da None),
   `kenar="sag"` (`sag`|`sol`), `baslangic="gorunur"` (`gorunur`|`tepsi`|`kenar`), `surum=1`.
K2 Dogrulama (`dogrula() -> list[str]`, alan adiyla mesaj): `dil` gecerli OcrLanguage degeri; kisayollar
   `KisayolServisi.kombinasyonu_coz` ile ayristirilir ve birbirinden FARKLI; `kenar`/`baslangic` kumeden;
   `sozluk_yolu` verilmisse `str`. Dogrulama dosya acmaz (sozluk dosyasinin varligi calisma zamaninda).
K3 Yukleme (`AyarlarDeposu.yukle()`): dosya yoksa -> varsayilanlar, `sorunlar=[]`; bozuk JSON / ust duzey
   nesne degil -> varsayilanlar + `sorunlar=["json"]`; bilinmeyen alanlar YOK SAYILIR (ileri surum), bilinen
   alanlarda tip/deger hatasi -> o alan varsayilana doner ve sorun listesine girer (asla istisna; uygulama
   her zaman acilir). `surum` > 1 -> sorun "surum" (yine acilir).
K4 Kaydetme (`kaydet(ayarlar)`): once `dogrula()`; sorun varsa `ValueError` (kaydedilmez). Yazma ATOMIK:
   gecici dosya + `os.replace` (yarim dosya kalmaz; olcu: yazma sirasinda istisna -> eski dosya bozulmadi).
   Dizin yoksa yaratilir. Cikti UTF-8, `ensure_ascii=False`, girintili.
K5 Saf/gizlilik: model hicbir metni loglamaz; dosya yolu disinda I/O yok; `kaydet` icerigi ayni ise yine yazar
   (idempotent, mtime degisir -- kabul).
"""
from __future__ import annotations

import dataclasses
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

__all__ = ["AYARLAR_DOSYASI_ADI", "Ayarlar", "AyarlarDeposu", "varsayilan_ayar_yolu"]

AYARLAR_DOSYASI_ADI = "ayarlar.json"
_DILLER = ("auto", "japan", "korean", "chinese", "english")   # T-018: auto = oyun dilini algila
_KENARLAR = ("sag", "sol")
_BASLANGICLAR = ("gorunur", "tepsi", "kenar")


@dataclass(frozen=True)
class Ayarlar:
    dil: str = "auto"
    kisayol_anlik: str = "Ctrl+Alt+D"
    kisayol_bolge: str = "Ctrl+Alt+R"
    sozluk_yolu: str | None = None
    kenar: str = "sag"
    baslangic: str = "gorunur"
    surum: int = 1

    def dogrula(self) -> list[str]:
        """Alan adiyla sorun listesi; bos liste = gecerli. Dosya acmaz."""
        from src.ui.kisayol import KisayolServisi  # gecikmeli: ayar modeli Qt'yi yalniz burada kullanir

        sorunlar: list[str] = []
        if self.dil not in _DILLER:
            sorunlar.append(f"dil: {self.dil!r} desteklenmiyor ({', '.join(_DILLER)})")
        for ad, deger in (("kisayol_anlik", self.kisayol_anlik), ("kisayol_bolge", self.kisayol_bolge)):
            try:
                KisayolServisi.kombinasyonu_coz(deger)
            except ValueError as e:
                sorunlar.append(f"{ad}: {e}")
        if self.kisayol_anlik.strip().lower() == self.kisayol_bolge.strip().lower():
            sorunlar.append("kisayol_bolge: iki kısayol aynı olamaz")
        if self.kenar not in _KENARLAR:
            sorunlar.append(f"kenar: {self.kenar!r} ({'|'.join(_KENARLAR)})")
        if self.baslangic not in _BASLANGICLAR:
            sorunlar.append(f"baslangic: {self.baslangic!r} ({'|'.join(_BASLANGICLAR)})")
        if self.sozluk_yolu is not None and (not isinstance(self.sozluk_yolu, str) or not self.sozluk_yolu.strip()):
            sorunlar.append("sozluk_yolu: dosya yolu (str) ya da null olmalı")
        return sorunlar

    def ile(self, **degisiklik: Any) -> Ayarlar:
        return dataclasses.replace(self, **degisiklik)


def varsayilan_ayar_yolu() -> Path:
    """`%APPDATA%\\Suflor\\ayarlar.json` (Windows); APPDATA yoksa ev dizini altinda `.suflor`."""
    kok = os.environ.get("APPDATA")
    taban = Path(kok) / "Suflor" if kok else Path.home() / ".suflor"
    return taban / AYARLAR_DOSYASI_ADI


@dataclass
class YuklemeSonucu:
    ayarlar: Ayarlar
    sorunlar: list[str] = field(default_factory=list)


class AyarlarDeposu:
    """Tek dosya: yukle (asla istisna) / kaydet (dogrulama + atomik yazma)."""

    def __init__(self, yol: Path | None = None) -> None:
        self._yol = Path(yol) if yol is not None else varsayilan_ayar_yolu()

    @property
    def yol(self) -> Path:
        return self._yol

    def yukle(self) -> YuklemeSonucu:
        if not self._yol.exists():
            return YuklemeSonucu(Ayarlar())
        try:
            veri = json.loads(self._yol.read_bytes())
        except (ValueError, OSError):
            return YuklemeSonucu(Ayarlar(), ["json"])
        if not isinstance(veri, dict):
            return YuklemeSonucu(Ayarlar(), ["json"])
        varsayilan = Ayarlar()
        sorunlar: list[str] = []
        alanlar: dict[str, Any] = {}
        for f in dataclasses.fields(Ayarlar):
            if f.name not in veri:
                continue
            deger = veri[f.name]
            aday = varsayilan.ile(**{f.name: deger})
            tip_ok = isinstance(deger, str) if f.name != "sozluk_yolu" and f.name != "surum" else (
                deger is None or isinstance(deger, str) if f.name == "sozluk_yolu" else isinstance(deger, int) and not isinstance(deger, bool))
            if tip_ok and not any(s.startswith(f.name + ":") for s in aday.dogrula()):
                alanlar[f.name] = deger
            else:
                sorunlar.append(f.name)
        ayarlar = varsayilan.ile(**alanlar)
        if ayarlar.surum > 1:
            sorunlar.append("surum")
        # iki kisayol ayni ise ikincisi varsayilana doner
        if ayarlar.kisayol_anlik.strip().lower() == ayarlar.kisayol_bolge.strip().lower():
            ayarlar = ayarlar.ile(kisayol_bolge=varsayilan.kisayol_bolge)
            if ayarlar.kisayol_anlik.strip().lower() == ayarlar.kisayol_bolge.strip().lower():
                ayarlar = ayarlar.ile(kisayol_anlik=varsayilan.kisayol_anlik)
            sorunlar.append("kisayol_bolge")
        return YuklemeSonucu(ayarlar, sorunlar)

    def kaydet(self, ayarlar: Ayarlar) -> None:
        sorunlar = ayarlar.dogrula()
        if sorunlar:
            raise ValueError("; ".join(sorunlar))
        self._yol.parent.mkdir(parents=True, exist_ok=True)
        gecici = self._yol.with_suffix(self._yol.suffix + ".tmp")
        metin = json.dumps(dataclasses.asdict(ayarlar), ensure_ascii=False, indent=2) + "\n"
        gecici.write_text(metin, encoding="utf-8")
        os.replace(gecici, self._yol)
