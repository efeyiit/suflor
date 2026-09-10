"""TESTER-D tur 2 -- ONERILEN duzeltmenin AYIRT ETME GUCUNU olcer.

feedback-D.md'de verilen tek testi ayna agacina ekler ve dort durumda kosar:
TABAN / M53 (`__exit__` yalniz istisnasiz cikista kapatir) / M12 (`__exit__`
bos) / M50 (`__exit__` kapatmadan birakir). `src/` ve `tests/` YAZILMAZ.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mutant_kiti import DEPO, KOK, SERVICE, _ayna_kur, _geri_al  # noqa: E402

TESTLER = "tests/unit/capture/test_service.py"

ONERILEN_TEST = '''

def test_k10_exit_ISTISNA_yolunda_da_kapatir() -> None:
    """K10: `__exit__` -> `close()` KOSULSUZDUR -- istisna yolunda da.

    `with MssBackend() as b:` govdesinin `CaptureError` ile bitmesi urunun
    NORMAL hata yoludur (K6 sinif b/c: backend istisnasi ve gecersiz cikti).
    Yalnizca temiz cikista kapatan bir uygulama HER hatada bir window DC
    sizdirir -- K10'un kendi olctugu ariza 5001. kapatilmamis ornekte
    `GetWindowDC`'yi kalici olarak dusuruyor. Ustteki test istisnasiz yolu
    olcer; bu test ikinci noktadir (PROTOKOL §4.6/7).
    """
    b = MssBackend()
    t = _SahteTutamac()
    b._tutamac = t  # type: ignore[assignment]
    with pytest.raises(RuntimeError):
        with b:
            raise RuntimeError("govde patladi")
    assert t.kapatma == 1, (
        "istisna ile cikilan `with` blogunda __exit__ close() cagirmadi -> "
        "her hatali yakalama bir window DC sizdirir"
    )
    assert b._tutamac is None
'''

MUTANTLAR: dict[str, list[tuple[str, str]]] = {
    "TABAN": [],
    "M53 (__exit__ yalniz istisnasiz cikista kapatir)": [
        ("    def __exit__(self, *_: object) -> None:\n        self.close()",
         "    def __exit__(self, *_: object) -> None:\n"
         "        if not _ or _[0] is None:\n            self.close()")],
    "M12 (__exit__ -> return None)": [
        ("    def __exit__(self, *_: object) -> None:\n        self.close()",
         "    def __exit__(self, *_: object) -> None:\n        return None")],
    "M50 (__exit__ kapatmadan birakir)": [
        ("    def __exit__(self, *_: object) -> None:\n        self.close()",
         "    def __exit__(self, *_: object) -> None:\n        self._tutamac = None")],
}

KOMUT = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
         "tests/unit/capture/test_service.py", "tests/unit/capture/test_monitors.py"]


def main() -> None:
    _ayna_kur()
    _geri_al()
    shutil.copyfile(DEPO / TESTLER, KOK / TESTLER)
    print("ONERILEN DUZELTMENIN AYIRT ETME GUCU (ayna agaci, depo YAZILMAZ)")
    print(f"ayna: {KOK}\n")

    # 0) once ONERILEN TEST OLMADAN: mutantlar kapiya takiliyor mu?
    print("== A) oneri EKLENMEDEN (bugunku taban) ==")
    for ad, yamalar in MUTANTLAR.items():
        _geri_al()
        shutil.copyfile(DEPO / TESTLER, KOK / TESTLER)
        _yama(SERVICE, yamalar)
        print(f"  {ad:48s} -> {_kos()}")

    # 1) oneri EKLENEREK
    print("\n== B) oneri EKLENEREK (tek test, +25 satir) ==")
    for ad, yamalar in MUTANTLAR.items():
        _geri_al()
        metin = (DEPO / TESTLER).read_text(encoding="utf-8") + ONERILEN_TEST
        (KOK / TESTLER).write_text(metin, encoding="utf-8")
        _yama(SERVICE, yamalar)
        print(f"  {ad:48s} -> {_kos()}")

    _geri_al()
    shutil.copyfile(DEPO / TESTLER, KOK / TESTLER)
    print("\nayna geri alindi.")


def _yama(rel: str, yamalar: list[tuple[str, str]]) -> None:
    if not yamalar:
        return
    p = KOK / rel
    metin = p.read_text(encoding="utf-8")
    for eski, yeni in yamalar:
        assert eski in metin, f"yama hedefi yok: {eski[:60]!r}"
        metin = metin.replace(eski, yeni, 1)
    p.write_text(metin, encoding="utf-8")


def _kos() -> str:
    r = subprocess.run(KOMUT, cwd=str(KOK), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    ozet = next((ln for ln in (r.stdout or "").splitlines()
                 if "passed" in ln or "failed" in ln), "?")
    kirik = [ln.split("::")[-1].split(" ")[0] for ln in (r.stdout or "").splitlines()
             if ln.startswith("FAILED")]
    return f"exit={r.returncode}  {ozet.strip()}  {kirik if kirik else ''}"


if __name__ == "__main__":
    main()
