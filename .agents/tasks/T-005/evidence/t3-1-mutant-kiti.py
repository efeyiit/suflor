"""T3-1 -- `__exit__` cikis-yolu ekseninin AYIRT ETME GUCU olcum kiti.

Kosum (depo kokunden ya da baska bir yerden, fark etmez):

    python .agents/tasks/T-005/evidence/t3-1-mutant-kiti.py

Ne yapar
--------
Depoyu gecici bir AYNA agacina kopyalar ve butun mutasyonlari orada uygular;
depodaki `src/` ve `tests/` HIC degistirilmez. Her varyant IKI ayri test
dosyasiyla kosulur:

  * TUR2 = `git show HEAD:tests/unit/capture/test_service.py`
           (tur 2'de teslim edilen hal -- tek noktali `__exit__` olcusu)
  * TUR3 = calisma agacindaki hal (`exc_type` ekseninde parametreli)

Beklenen yon: hedef mutantlar TUR2'de kacar ya da tek bicimde yakalanir,
TUR3'te yakalanir; KONTROL mutanti (davranis-esdeger) IKISINDE DE kacar --
kapiya takilirsa olcu yanlis pozitif veriyordur.

Not: kit `git show HEAD:...` kullanir, yani TUR2 tabani HEAD commit'idir.
HEAD ilerledikten sonra kosulursa TUR2 sutunu artik "tur 2" degil "HEAD"
anlamina gelir; ham cikti dosyasi (t3-1-mutant-ayirt-etme.txt) tur 3
teslimi sirasindaki kosumu saklar.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]

ORIJINAL_EXIT = """    def __exit__(self, *_: object) -> None:
        self.close()
"""

MUTANTLAR: dict[str, tuple[str, str]] = {
    "TABAN": ("(mutasyon yok)", ORIJINAL_EXIT),
    "MT-53": (
        "__exit__ YALNIZCA istisnasiz cikista kapatir (govde patlarsa sizar)",
        """    def __exit__(self, *_: object) -> None:
        if not _ or _[0] is None:
            self.close()
""",
    ),
    "MT-12": (
        "__exit__ hicbir sey yapmaz (-> return None)",
        """    def __exit__(self, *_: object) -> None:
        return None
""",
    ),
    "MT-YUT": (
        "__exit__ kapatir ama istisnayi YUTAR (-> return True)",
        """    def __exit__(self, *_: object) -> bool:
        self.close()
        return True
""",
    ),
    "MT-KONTROL": (
        "KONTROL: davranis-esdeger (govde tek satirdan iki satira acildi)",
        """    def __exit__(self, *_: object) -> None:
        kapat = self.close
        kapat()
""",
    ),
}


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="t005-ayna-") as gecici:
        ayna = Path(gecici) / "ayna"
        yoksay = shutil.ignore_patterns("__pycache__", "*.pyc")
        ayna.mkdir()
        shutil.copytree(KOK / "src", ayna / "src", ignore=yoksay)
        shutil.copytree(KOK / "tests", ayna / "tests", ignore=yoksay)

        service = ayna / "src" / "capture" / "service.py"
        testler = ayna / "tests" / "unit" / "capture" / "test_service.py"
        taban_service = service.read_text(encoding="utf-8")

        tur3 = Path(gecici) / "test_service_TUR3.py"
        tur3.write_text(
            (KOK / "tests" / "unit" / "capture" / "test_service.py").read_text(
                encoding="utf-8"
            ),
            encoding="utf-8",
        )
        tur2 = Path(gecici) / "test_service_TUR2.py"
        gecmis = subprocess.run(
            ["git", "show", "HEAD:tests/unit/capture/test_service.py"],
            cwd=KOK, capture_output=True, text=True, encoding="utf-8",
        )
        if gecmis.returncode != 0:
            print("HATA: `git show HEAD:...` basarisiz:", gecmis.stderr.strip())
            return 1
        tur2.write_text(gecmis.stdout, encoding="utf-8")

        def kos(test_dosyasi: Path) -> str:
            shutil.copyfile(test_dosyasi, testler)
            ortam = dict(os.environ, PYTHONPATH=str(ayna), PYTHONIOENCODING="utf-8")
            p = subprocess.run(
                [sys.executable, "-m", "pytest",
                 "tests/unit/capture/test_service.py", "-q",
                 "-p", "no:cacheprovider"],
                cwd=ayna, env=ortam, capture_output=True, text=True,
            )
            son = [s for s in p.stdout.strip().splitlines() if s.strip()][-1]
            return re.sub(r"\s+", " ", son).strip()

        print("=" * 78)
        print("T3-1 -- `__exit__` cikis-yolu ekseni: ayirt etme gucu")
        print("=" * 78)
        print(f"depo koku  : {KOK}")
        print(f"ayna agaci : {ayna}  (gecici; depodaki src/ ve tests/ DEGISMEZ)")
        print("TUR2 testi : git show HEAD:tests/unit/capture/test_service.py")
        print("TUR3 testi : tests/unit/capture/test_service.py (calisma agaci)")
        print()
        print(f"{'mutant':<12} {'TUR2 testleri':<34} {'TUR3 testleri':<34}")
        print("-" * 78)

        sonuclar: dict[str, tuple[str, str]] = {}
        for ad, (_aciklama, govde) in MUTANTLAR.items():
            service.write_text(
                taban_service.replace(ORIJINAL_EXIT, govde), encoding="utf-8"
            )
            uygulandi = (ORIJINAL_EXIT in service.read_text(encoding="utf-8"))
            assert uygulandi == (ad == "TABAN"), f"{ad}: mutasyon uygulanamadi"
            o2 = kos(tur2)
            o3 = kos(tur3)
            sonuclar[ad] = (o2, o3)
            print(f"{ad:<12} {o2:<34} {o3:<34}")

        print()
        for ad, (aciklama, _govde) in MUTANTLAR.items():
            o2, o3 = sonuclar[ad]
            print(f"{ad:<12} "
                  f"TUR2={'KACTI' if 'failed' not in o2 else 'YAKALANDI':<10} "
                  f"TUR3={'KACTI' if 'failed' not in o3 else 'YAKALANDI':<10}  "
                  f"{aciklama}")
    print()
    print("ayna agaci silindi; depo dokunulmadan kaldi.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
