"""TESTER-D tur 3 mutant dalgasi -- `exc_type` EKSENI gercekten kapandi mi?

Tur 3'te `test_k10_exit_uzun_omurlu_tutamaci_kapatir` `exc_type` ekseninde
IKI parametreye (`None`, `CaptureError`) acildi. Sefin karari bunu
"eksen TAMAMEN kapandi" diye okuyor.

`t3_exc_type_ekseni.py` olctu: CIKIS YOLU ekseni gercekten iki ayrik sinifa
cokuyor (14 yol, ucuncu sinif yok). Ama `exc_type`'in DEGER ekseni iki
degildir. Bu dosya farki mutantla olcer: **iki parametreyi de gecen ama
degismezi ihlal eden** varyantlar kurulur.

Kapilar tur 3 kararinin BES kabul komutunun BIREBIR kendisidir.

Ayrisan varyantlarin imzasi ACIKCA TIPLENIR (`exc_type: type[BaseException] |
None, ...`) ki G1-mypy'ye yanlislikla takilmasinlar -- olculmek istenen sey
DAVRANISSAL kapilarin gucudur, tip denetleyicinin degil.

`src/` ve `tests/` YAZILMAZ -- makine `mutant_kiti.py`'nin ayna agacidir.
Kosum:  python .agents/tasks/T-005/tester_D/t3_mutant_kiti.py [mutant_id ...]
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mutant_kiti import (  # noqa: E402
    DEPO,
    KOK,
    SERVICE,
    Mutant,
    _ayna_kur,
    _geri_al,
    _uygula,
    _y,
)

# `mutant_kiti.py`'nin aynasi yalnizca `src/`, `tests/` ve T-005'in
# `headless_check.py`'sini kopyalar. TAM TAKIM (`pytest tests`) kapisi ise
# `tests/unit/ocr/conftest.py` uzerinden `.agents/tasks/T-004/olcu_kiti.py`'ye
# BAGIMLIDIR -- o dosya kopyalanmazsa toplama hatasi cikar ve kapi HER mutant
# icin (davranis-esdeger KONTROL mutantlari dahil) yanlis pozitif verir.
# Olculdu: ilk kosumda sekiz mutantin sekizi de G5'e takildi; sebep mutant
# degil, EKSIK AYNA idi. Kapinin kendisi bu yuzden burada tamamlanir.
AYNA_EK: tuple[str, ...] = (".agents/tasks/T-004/olcu_kiti.py",)

# Tur 3 kararinin BES kabul komutu (sef_karari-tur3.md "Kabul komutlari").
KAPILAR3: list[tuple[str, list[str]]] = [
    ("G1-mypy", [sys.executable, "-m", "mypy", "--strict", "--explicit-package-bases",
                 "src/capture/service.py", "src/capture/monitors.py"]),
    ("G2-sahipli", [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                    "tests/unit/capture/test_service.py",
                    "tests/unit/capture/test_monitors.py"]),
    ("G3-headless", [sys.executable, ".agents/tasks/T-005/headless_check.py"]),
    ("G4-kapsam", [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                   "tests/unit/capture", "--cov=src.capture.service",
                   "--cov=src.capture.monitors", "--cov-fail-under=95"]),
    ("G5-tamtakim", [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                     "tests"]),
]

EXIT_ESKI = "    def __exit__(self, *_: object) -> None:\n        self.close()"

IMZA3 = (
    "    def __exit__(\n"
    "        self,\n"
    "        exc_type: type[BaseException] | None,\n"
    "        exc: BaseException | None,\n"
    "        tb: object,\n"
    "    ) -> "
)


def _exit3(donus: str, govde: str) -> tuple[str, str]:
    """Tipli 3-argumanli `__exit__` imzasiyla yama uretir."""
    return _y(EXIT_ESKI, IMZA3 + donus + ":\n" + govde)


MUTANTLAR: list[Mutant] = [
    # ------------------------------------------------------------------
    # A. `exc_type` DEGERINE gore ayrisan varyantlar
    #    -- ucu de yeni testin IKI bacagini da GECMEK uzere kuruldu
    # ------------------------------------------------------------------
    Mutant(
        "M60", SERVICE,
        [_exit3("None",
                "        if exc_type is not GeneratorExit:\n"
                "            self.close()")],
        "__exit__ YALNIZ GeneratorExit'te kapatmaz "
        "(uretec close()/cop toplama her seferinde bir DC sizdirir)",
        "K10 `__exit__` -> close() KOSULSUZ  [exc_type DEGER ekseni: GeneratorExit]",
    ),
    Mutant(
        "M61", SERVICE,
        [_exit3("None",
                "        if exc_type is None or exc_type is CaptureError:\n"
                "            self.close()")],
        "__exit__ YALNIZ olcunun sectigi IKI degerde kapatir (None, CaptureError) -- "
        "diger HER istisnada tutamac sizar",
        "K10 `__exit__` -> close() KOSULSUZ  [olcunun IKI NOKTASINA kapili varyant]",
    ),
    Mutant(
        "M62", SERVICE,
        [_exit3("None",
                "        if exc_type is None or issubclass(exc_type, Exception):\n"
                "            self.close()")],
        "__exit__ BaseException'da kapatmaz (KeyboardInterrupt / GeneratorExit / "
        "SystemExit) -- 'except Exception' aliskanliginin DOGAL hatasi",
        "K10 `__exit__` -> close() KOSULSUZ  [exc_type DEGER ekseni: BaseException]",
    ),
    # ------------------------------------------------------------------
    # B. "istisnayi yutma" ekseni -- yeni assert'in gucu
    # ------------------------------------------------------------------
    Mutant(
        "M63", SERVICE,
        [_y(EXIT_ESKI,
            "    def __exit__(self, *_: object) -> bool:\n"
            "        self.close()\n"
            "        return True")],
        "POZITIF KONTROL: __exit__ kapatir AMA istisnayi YUTAR (return True)",
        "K10 `__exit__` istisnayi yutmaz  [yeni assert ATESLEYEBILIYOR mu?]",
    ),
    Mutant(
        "M64", SERVICE,
        [_exit3("bool",
                "        self.close()\n"
                "        return exc_type is not None and not issubclass(\n"
                "            exc_type, CaptureError\n"
                "        )")],
        "__exit__ CaptureError'u gecirir ama DIGER istisnalari sessizce YUTAR "
        "(ValueError / KeyboardInterrupt cagirana hic ulasmaz)",
        "K10 `__exit__` istisnayi yutmaz  [yutma ekseni de IKI NOKTAYA kapili]",
    ),
    # ------------------------------------------------------------------
    # C. KONTROL mutantlari -- yanlis pozitif denetimi (KACMALI)
    # ------------------------------------------------------------------
    Mutant(
        "M65", SERVICE,
        [_y(EXIT_ESKI,
            "    def __exit__(self, *_: object) -> bool:\n"
            "        self.close()\n"
            "        return False")],
        "KONTROL: __exit__ acikca `False` dondurur -- davranis AYNI",
        "yanlis pozitif denetimi: KACMASI DOGRU",
    ),
    Mutant(
        "M66", SERVICE,
        [_y(EXIT_ESKI,
            "    def __exit__(self, *_: object) -> None:\n"
            "        if self._tutamac is not None:\n"
            "            self._tutamac.close()\n"
            "            self._tutamac = None")],
        "KONTROL: __exit__ `close()` CAGIRMAZ, govdesini SATIR ICI yapar -- davranis AYNI "
        "(olcu MEKANIZMAYI mi DEGISMEZI mi kancaliyor?)",
        "yanlis pozitif denetimi: KACMASI DOGRU (PROTOKOL §4.6/7)",
    ),
    # ------------------------------------------------------------------
    # D. `__exit__`'i `close()` yerine baska bir seye baglayan varyant
    # ------------------------------------------------------------------
    Mutant(
        "M67", SERVICE,
        [_y(EXIT_ESKI,
            "    def _serbest_birak(self) -> None:\n"
            "        self._tutamac = None\n"
            "\n"
            "    def __exit__(self, *_: object) -> None:\n"
            "        self._serbest_birak()")],
        "__exit__ `close()` yerine tutamaci yalnizca BIRAKAN bir metoda baglanir "
        "(alan None olur, alttaki DC sizar)",
        "K10 `__exit__` -> close()  [mekanizma degistirme]",
    ),
]


def _ayna_tamamla() -> None:
    """`AYNA_EK` dosyalarini aynaya kopyalar (tam takim kapisi icin)."""
    import shutil

    for rel in AYNA_EK:
        hedef = KOK / rel
        hedef.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(DEPO / rel, hedef)


def _kapi_kos3(argv: list[str]) -> tuple[int, str]:
    r = subprocess.run(argv, cwd=str(KOK), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def main() -> None:
    secilen = set(sys.argv[1:])
    _ayna_kur()
    _ayna_tamamla()
    print(f"ayna agaci: {KOK}   (depo YAZILMAZ)")
    print("kapilar = tur 3 kararinin BES kabul komutu")
    print("kapilar: " + " | ".join(ad for ad, _ in KAPILAR3))
    print()
    _geri_al()

    # TABAN KONTROLU -- "kapi yakalamadi" iddiasi ancak kapilarin mutasyonsuz
    # agacta TEMIZ oldugu gosterilerek anlam tasir (PROTOKOL §4.6/10).
    taban = []
    for ad, argv in KAPILAR3:
        rc, _ozet = _kapi_kos3(argv)
        taban.append(f"{ad}={'TEMIZ' if rc == 0 else f'KIRIK(rc={rc})'}")
    print("TABAN (mutasyonsuz ayna): " + " | ".join(taban))
    if any("KIRIK" in t for t in taban):
        print("!!! TABAN KIRIK -- mutant sonuclari OKUNAMAZ, once ayna duzeltilmeli")
    print()

    satirlar: list[str] = []
    kacan: list[str] = []
    for mut in MUTANTLAR:
        if secilen and mut.mid not in secilen:
            continue
        _uygula(mut)
        try:
            isaretler = []
            detaylar = []
            for ad, argv in KAPILAR3:
                rc, ozet = _kapi_kos3(argv)
                isaretler.append("X" if rc != 0 else ".")
                if rc != 0:
                    ilk = next((ln for ln in ozet.splitlines()
                                if ("IHLAL" in ln or "error:" in ln or "failed" in ln
                                    or "Required test coverage" in ln)), "")
                    detaylar.append(f"{ad}:{ilk.strip()[:110]}")
            durum = "".join(isaretler)
            yakalandi = "X" in durum
            if not yakalandi:
                kacan.append(mut.mid)
            print(f"{mut.mid} [{durum}] "
                  f"{'YAKALANDI' if yakalandi else '*** HICBIR KAPI YAKALAMADI ***'}")
            print(f"     {mut.aciklama}")
            print(f"     hedef degismez: {mut.hedef_degismez}")
            for d in detaylar:
                print(f"     | {d}")
            satirlar.append(f"| {mut.mid} | {mut.aciklama} | {mut.hedef_degismez} | "
                            + " | ".join(isaretler) + " |")
        finally:
            _geri_al()
    print()
    print("=== MARKDOWN TABLOSU ===")
    print("| mutant | ne yapiyor | hedef degismez | "
          + " | ".join(a for a, _ in KAPILAR3) + " |")
    print("|---|---|---|" + "---|" * len(KAPILAR3))
    for s in satirlar:
        print(s)
    print()
    if kacan:
        print(f"HICBIR KAPININ YAKALAMADIGI MUTANTLAR ({len(kacan)}): {', '.join(kacan)}")
    else:
        print("kacan mutant YOK")


if __name__ == "__main__":
    main()
