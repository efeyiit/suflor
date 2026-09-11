"""T-006 tur 2 mutant kiti -- K7/K10 olcusunun AYIRT ETME gucu (ayna agacinda, depo DEGISMEZ).

Her mutant `src/ocr/rapid_engine.py`nin bir kopyasina METIN duzeyinde uygulanir ve
IKI test dosyasi ayri ayri kosulur:

  * TUR1 = `git show HEAD:tests/unit/ocr/test_rapid_engine.py` (tur 1 teslimi, 95 test)
  * TUR2 = calisma kopyasindaki `tests/unit/ocr/test_rapid_engine.py` (tur 2, 108 test)

Beklenti: K7/K10 mutantlari (M-A..M-K) TUR1'den KACAR, TUR2'de YAKALANIR;
davranis-esdeger kontroller (C-1..C-3) ikisinden de KACAR (yanlis pozitif yok).
M-H (`print`) tur 1'in AST olcusunde de yakalanir -- iki turda da YAKALANDI beklenir.

Kosum: python .agents/tasks/T-006/evidence/mutant-kiti-tur2.py
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
KAYNAK = KOK / "src" / "ocr" / "rapid_engine.py"
TEST = KOK / "tests" / "unit" / "ocr" / "test_rapid_engine.py"

RECOGNIZE_SON = "        return _bloklara_cevir(cikti, frame.rect)\n"
DONGU_SATIRI = "        if not isinstance(metin, str):\n            raise OcrError(f\"metin str degil: {type(metin).__name__}\")\n"
CLOSE_GOVDE = "        self._taniyici = None\n        self._kapali = True\n"

# (ad, aciklama, [(eski, yeni), ...], tur1_beklenen_yakalanma, tur2_beklenen_yakalanma)
MUTANTLAR: list[tuple[str, str, list[tuple[str, str]], bool, bool]] = [
    ("M-A", "K7: recognize sonunda sys.stdout.write(blok.text)  [M25b sinifi]",
     [("import numbers\nimport os\n", "import numbers\nimport os\nimport sys\n"),
      (RECOGNIZE_SON,
       "        bloklar = _bloklara_cevir(cikti, frame.rect)\n"
       "        for blok in bloklar:\n            sys.stdout.write(blok.text)\n"
       "        return bloklar\n")],
     False, True),
    ("M-B", "K7: recognize sonunda sys.stderr.write(blok.text)",
     [("import numbers\nimport os\n", "import numbers\nimport os\nimport sys\n"),
      (RECOGNIZE_SON,
       "        bloklar = _bloklara_cevir(cikti, frame.rect)\n"
       "        for blok in bloklar:\n            sys.stderr.write(blok.text)\n"
       "        return bloklar\n")],
     False, True),
    ("M-C", "K7: donguden kok logger'a logging.getLogger('suflor.ocr').debug(metin)  [M28c sinifi]",
     [(DONGU_SATIRI, DONGU_SATIRI + "        logging.getLogger(\"suflor.ocr\").debug(\"blok %s\", metin)\n")],
     False, True),
    ("M-D", "K7: donguden RapidOCR logger'ina .info(metin)  [M28b sinifi]",
     [(DONGU_SATIRI, DONGU_SATIRI + "        logging.getLogger(_LOGGER_ADI).info(\"blok %s\", metin)\n")],
     False, True),
    ("M-E", "K10: close() taniyiciyi BIRAKMIYOR (_taniyici = None silindi)  [M32 sinifi]",
     [(CLOSE_GOVDE, "        self._kapali = True\n")],
     False, True),
    ("M-F", "K7: os.write(1, blok.text) -- sys.stdout'u atlayan fd yazimi (capsys goremez, capfd gorur)",
     [(RECOGNIZE_SON,
       "        bloklar = _bloklara_cevir(cikti, frame.rect)\n"
       "        for blok in bloklar:\n            os.write(1, blok.text.encode(\"utf-8\"))\n"
       "        return bloklar\n")],
     False, True),
    ("M-G", "K7: warnings.warn(metin) -- uyari kanali",
     [("import numbers\nimport os\n", "import numbers\nimport os\nimport warnings\n"),
      (DONGU_SATIRI, DONGU_SATIRI + "        warnings.warn(metin, stacklevel=2)\n")],
     False, True),
    ("M-H", "K7: print(blok.text) -- tur 1 AST olcusu de gorur (kontrol: iki turda da yakalanmali)",
     [(RECOGNIZE_SON,
       "        bloklar = _bloklara_cevir(cikti, frame.rect)\n"
       "        for blok in bloklar:\n            print(blok.text)\n"
       "        return bloklar\n")],
     True, True),
    ("M-I", "K7: logging.getLogger(__name__).log(DEBUG, metin) -- modul logger'i, .log metodu",
     [(DONGU_SATIRI, DONGU_SATIRI + "        logging.getLogger(__name__).log(logging.DEBUG, \"blok %s\", metin)\n")],
     False, True),
    ("M-J", "K7: kurulum sirasinda sys.stdout.write(str(params)) -- OCR metni degil ama SIFIR BAYT ihlali (soguk nokta)",
     [("import numbers\nimport os\n", "import numbers\nimport os\nimport sys\n"),
      ("        params = self.parametreler()\n        try:\n            taniyici = self._fabrika(params)",
       "        params = self.parametreler()\n        sys.stdout.write(str(params))\n        try:\n            taniyici = self._fabrika(params)")],
     False, True),
    ("M-K", "K7: sys.__stderr__.write(blok.text) -- ozgun akis nesnesi (capsys goremez, capfd gorur)",
     [("import numbers\nimport os\n", "import numbers\nimport os\nimport sys\n"),
      (RECOGNIZE_SON,
       "        bloklar = _bloklara_cevir(cikti, frame.rect)\n"
       "        for blok in bloklar:\n            sys.__stderr__.write(blok.text)\n"
       "        return bloklar\n")],
     False, True),
    ("C-1", "KONTROL davranis-esdeger: close() icinde sira degisti (once _kapali, sonra _taniyici)",
     [(CLOSE_GOVDE, "        self._kapali = True\n        self._taniyici = None\n")],
     False, False),
    ("C-2", "KONTROL davranis-esdeger: setLevel(logging.ERROR) -> setLevel(40)",
     [("        logging.getLogger(_LOGGER_ADI).setLevel(logging.ERROR)\n",
       "        logging.getLogger(_LOGGER_ADI).setLevel(40)\n")],
     False, False),
    ("C-3", "KONTROL davranis-esdeger: recognize sonucu yerel degiskene alinip donduruluyor",
     [(RECOGNIZE_SON,
       "        bloklar = _bloklara_cevir(cikti, frame.rect)\n        return bloklar\n")],
     False, False),
]


def kos(ayna: Path, test_dosyasi: str) -> tuple[int, str]:
    r = subprocess.run(
        [sys.executable, "-m", "pytest", test_dosyasi, "-q", "-p", "no:cacheprovider", "-rf"],
        cwd=str(ayna), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300,
        env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONPATH": str(ayna)},
    )
    satirlar = [s for s in r.stdout.strip().splitlines() if s.strip()]
    ozetler = [s for s in satirlar if (" passed" in s or " failed" in s or " error" in s) and " in " in s]
    ozet = ozetler[-1].strip("= ") if ozetler else (satirlar[-1] if satirlar else "")
    dusen = [s.split("::", 1)[-1].split(" ", 1)[0] for s in satirlar if s.startswith("FAILED ")]
    ek = f"  dusen: {', '.join(dusen[:4])}{' ...' if len(dusen) > 4 else ''}" if dusen else ""
    return r.returncode, ozet + ek


def main() -> int:
    ozgun = KAYNAK.read_text(encoding="utf-8")
    tur1 = subprocess.run(
        ["git", "show", "HEAD:tests/unit/ocr/test_rapid_engine.py"],
        cwd=str(KOK), capture_output=True, text=True, encoding="utf-8", check=True,
    ).stdout
    tur2 = TEST.read_text(encoding="utf-8")
    print("HEAD:", subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=str(KOK), capture_output=True, text=True).stdout.strip())
    print("TUR1 test dosyasi = git show HEAD:tests/unit/ocr/test_rapid_engine.py")
    print("TUR2 test dosyasi = calisma kopyasi tests/unit/ocr/test_rapid_engine.py")
    with tempfile.TemporaryDirectory() as td:
        ayna = Path(td) / "ayna"
        (ayna / ".agents").mkdir(parents=True)  # conftest kok bulucu isareti
        shutil.copytree(KOK / "src", ayna / "src", ignore=shutil.ignore_patterns("__pycache__"))
        tdir = ayna / "tests" / "unit" / "ocr"
        tdir.mkdir(parents=True)
        shutil.copy(KOK / "tests" / "unit" / "ocr" / "conftest.py", tdir / "conftest.py")
        (tdir / "test_tur1.py").write_text(tur1, encoding="utf-8")
        (tdir / "test_tur2.py").write_text(tur2, encoding="utf-8")
        hedef = ayna / "src" / "ocr" / "rapid_engine.py"

        k1, o1 = kos(ayna, "tests/unit/ocr/test_tur1.py")
        k2, o2 = kos(ayna, "tests/unit/ocr/test_tur2.py")
        print(f"TABAN  TUR1: exit={k1}  {o1}")
        print(f"TABAN  TUR2: exit={k2}  {o2}")
        if k1 != 0 or k2 != 0:
            print("TABAN YESIL DEGIL -- kit anlamsiz")
            return 2
        print()
        print(f"{'mutant':7s} {'TUR1':10s} {'TUR2':10s} {'beklenti':9s} aciklama")
        sonuc = 0
        for ad, aciklama, degisimler, bek1, bek2 in MUTANTLAR:
            kaynak = ozgun
            uygulanamadi = False
            for eski, yeni in degisimler:
                if kaynak.count(eski) != 1:
                    print(f"{ad:7s} HEDEF METIN {kaynak.count(eski)} KEZ BULUNDU -> uygulanamadi ({aciklama})")
                    uygulanamadi = True
                    break
                kaynak = kaynak.replace(eski, yeni)
            if uygulanamadi:
                sonuc = 1
                continue
            hedef.write_text(kaynak, encoding="utf-8")
            k1, o1 = kos(ayna, "tests/unit/ocr/test_tur1.py")
            k2, o2 = kos(ayna, "tests/unit/ocr/test_tur2.py")
            y1, y2 = k1 != 0, k2 != 0
            d1 = "YAKALANDI" if y1 else "KACTI"
            d2 = "YAKALANDI" if y2 else "KACTI"
            uygun = (y1 == bek1) and (y2 == bek2)
            print(f"{ad:7s} {d1:10s} {d2:10s} {'ok' if uygun else 'HATA':9s} {aciklama}")
            print(f"{'':7s}   TUR1: {o1}")
            print(f"{'':7s}   TUR2: {o2}")
            if not uygun:
                sonuc = 1
        hedef.write_text(ozgun, encoding="utf-8")
    print()
    print("MUTANT KITI TUR 2:", "TEMIZ" if sonuc == 0 else "SORUN VAR")
    return sonuc


if __name__ == "__main__":
    raise SystemExit(main())
