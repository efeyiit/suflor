"""TESTER-D tur 3 -- parametrizasyon ESKI KAPSAMI kaybetti mi?

Tur 2'de `test_k10_exit_uzun_omurlu_tutamaci_kapatir` TEKIL bir testti ve
`__exit__`'i yalnizca temiz cikista olcuyordu. Tur 3'te `exc_type` ekseninde
iki parametreye acildi. Parametrize ederken **bir bacagin sessizce
zayiflamasi** yaygin bir hatadir: `pytest.raises` bir assert hatasini yutabilir,
ortak kurulum bir bacakta atlanabilir, ya da eski assert'ler yalnizca yeni
bacakta kalabilir.

Bu kit her BACAGI TEK BASINA kosar ve hangi mutanti yakaladigini olcer.
Beklenen: `exc_type=None` bacagi, tur 2'nin TEKIL testinin yakaladigi HER
mutanti tek basina yakalamaya devam eder (kayip yok); `exc_type=CaptureError`
bacagi ustune yeni mutantlar ekler.

Ayrica ARA ASSERT'lerin gercekten atesledigi olculur: istisna bacagindaki
`assert t.kapatma == 0` govde icindedir; `pytest.raises(CaptureError)` bir
`AssertionError`'i YUTUYORSA o assert sessizce olur.

`src/` ve `tests/` YAZILMAZ.
Kosum:  python .agents/tasks/T-005/tester_D/t3_bacak_gucu.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mutant_kiti import (  # noqa: E402
    KOK,
    SERVICE,
    Mutant,
    _ayna_kur,
    _geri_al,
    _uygula,
    _y,
)
from t3_mutant_kiti import _exit3  # noqa: E402

TEST = "tests/unit/capture/test_service.py"
EXIT_ESKI = "    def __exit__(self, *_: object) -> None:\n        self.close()"

NODE = TEST + "::test_k10_exit_uzun_omurlu_tutamaci_kapatir"

# `-k` `=` isaretini kabul etmez (olculdu: rc=4 "Wrong expression passed to
# '-k'"). Bacaklar bu yuzden TAM NODE ID ile secilir.
BACAKLAR = [
    ("exc_type=None", [NODE + "[exc_type=None]"]),
    ("exc_type=CaptureError", [NODE + "[exc_type=CaptureError]"]),
    ("HER IKISI", [NODE]),
]

# Tur 2'nin TEKIL testinin yakaladigi bilinen mutantlar + tur 3'unkiler.
MUTANTLAR: list[Mutant] = [
    Mutant(
        "M12", SERVICE,
        [_y(EXIT_ESKI, "    def __exit__(self, *_: object) -> None:\n        return None")],
        "__exit__ hicbir sey yapmaz (tur 1 bloke mutanti)",
        "K10 __exit__ -> close()",
    ),
    Mutant(
        "M50", SERVICE,
        [_y(EXIT_ESKI,
            "    def __exit__(self, *_: object) -> None:\n        self._tutamac = None")],
        "__exit__ tutamaci KAPATMADAN birakir",
        "K10 __exit__ -> close()",
    ),
    Mutant(
        "M53", SERVICE,
        [_y(EXIT_ESKI,
            "    def __exit__(self, *_: object) -> None:\n"
            "        if not _ or _[0] is None:\n"
            "            self.close()")],
        "__exit__ YALNIZ temiz cikista kapatir (tur 2 bloke mutanti)",
        "K10 __exit__ -> close() istisna yolunda",
    ),
    Mutant(
        "M53T", SERVICE,
        [_y(EXIT_ESKI,
            "    def __exit__(self, *_: object) -> None:\n"
            "        if _ and _[0] is not None:\n"
            "            self.close()")],
        "M53'un AYNASI: __exit__ YALNIZ istisnali cikista kapatir "
        "(temiz cikista sizar) -- tur 2 olcusunun tek yakaladigi sinif",
        "K10 __exit__ -> close() temiz yolda",
    ),
    Mutant(
        "M63", SERVICE,
        [_y(EXIT_ESKI,
            "    def __exit__(self, *_: object) -> bool:\n"
            "        self.close()\n"
            "        return True")],
        "__exit__ kapatir ama istisnayi YUTAR",
        "K10 __exit__ istisnayi yutmaz",
    ),
    Mutant(
        "M67", SERVICE,
        [_y(EXIT_ESKI,
            "    def _serbest_birak(self) -> None:\n"
            "        self._tutamac = None\n"
            "\n"
            "    def __exit__(self, *_: object) -> None:\n"
            "        self._serbest_birak()")],
        "__exit__ close() yerine baska metoda baglanir",
        "K10 __exit__ -> close()",
    ),
    Mutant(
        "M68", SERVICE,
        [_exit3("None",
                "        if exc_type is None:\n"
                "            self.close()\n"
                "        else:\n"
                "            self.close()\n"
                "            self._tutamac = None")],
        "KONTROL: iki dal ayri yazilir ama DAVRANIS AYNI",
        "yanlis pozitif denetimi: KACMASI DOGRU",
    ),
]

# Ara assert'in gercekten atesledigini gosteren SONDA: istisna bacagindaki
# `assert t.kapatma == 0` govde icindedir. `close()`'u __enter__'da cagiran
# bir uygulama o assert'i dusurur; `pytest.raises` onu YUTUYORSA test
# sessizce gecer.
SONDA_ENTER = Mutant(
    "S1", SERVICE,
    [_y("    def __enter__(self) -> MssBackend:\n        return self",
        "    def __enter__(self) -> MssBackend:\n        self.close()\n        return self")],
    "SONDA: __enter__ ONCEDEN kapatir -> govde ici `assert t.kapatma == 0` "
    "dusmeli. Istisna bacagi bunu YUTUYORSA parametrizasyon o assert'i "
    "sessizce oldurmustur.",
    "ara assert ATESLEYEBILIYOR mu?",
)


def _kos(hedefler: list[str]) -> tuple[int, str]:
    argv = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
            *hedefler]
    r = subprocess.run(argv, cwd=str(KOK), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def _ozet(cikti: str) -> str:
    for ln in reversed(cikti.splitlines()):
        if "passed" in ln or "failed" in ln or "error" in ln:
            return ln.strip()[:60]
    return "?"


def main() -> None:
    _ayna_kur()
    _geri_al()
    print(f"ayna agaci: {KOK}   (depo YAZILMAZ)")
    print()
    print("=" * 78)
    print("TABAN -- her bacak mutasyonsuz agacta GECMELI")
    print("=" * 78)
    for ad, k in BACAKLAR:
        rc, c = _kos(k)
        print(f"  {ad:24s} rc={rc}  {_ozet(c)}")
    print()

    print("=" * 78)
    print("BACAK BASINA AYIRT ETME GUCU (X = bacak TEK BASINA yakaliyor)")
    print("=" * 78)
    basliklar = [ad for ad, _ in BACAKLAR]
    print(f"{'mutant':8s} " + " ".join(f"{b:24s}" for b in basliklar))
    tablo: list[str] = []
    for mut in MUTANTLAR:
        _uygula(mut)
        try:
            isaret = []
            for _ad, k in BACAKLAR:
                rc, c = _kos(k)
                if rc == 0:
                    isaret.append(".")
                elif "1 failed" in c or "2 failed" in c or "failed" in c:
                    isaret.append("X")
                else:  # kosum hatasi -- sonuc OKUNAMAZ
                    isaret.append("?")
            print(f"{mut.mid:8s} " + " ".join(f"{i:24s}" for i in isaret))
            print(f"         {mut.aciklama}")
            tablo.append(f"| {mut.mid} | {mut.aciklama} | " + " | ".join(isaret) + " |")
        finally:
            _geri_al()
    print()

    print("=" * 78)
    print("ARA ASSERT SONDASI -- `pytest.raises` bir AssertionError'i yutuyor mu?")
    print("=" * 78)
    _uygula(SONDA_ENTER)
    try:
        for ad, k in BACAKLAR:
            rc, c = _kos(k)
            durum = ("ara assert ATESLEDI" if "failed" in c
                     else ("*** SESSIZ -- assert OLU ***" if rc == 0
                           else f"KOSUM HATASI rc={rc}"))
            print(f"  {ad:24s} rc={rc}  {_ozet(c)}  {durum}")
    finally:
        _geri_al()
    print()

    print("=== MARKDOWN ===")
    print("| mutant | ne yapiyor | " + " | ".join(basliklar) + " |")
    print("|---|---|" + "---|" * len(basliklar))
    for s in tablo:
        print(s)


if __name__ == "__main__":
    main()
