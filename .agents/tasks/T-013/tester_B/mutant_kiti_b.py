"""T-013 Tester-B ek mutant kiti -- implementer kitinde OLMAYAN siniflar; ayna agaci (depoya dokunmaz).

    python .agents/tasks/T-013/tester_B/mutant_kiti_b.py

Her mutant once implementer testlerine (`tests/unit/ui`), sonra Tester-B testlerine (`test_mercek_b.py`) karsi kosulur.
`X (n)` = n test dustu (YAKALANDI), `.` = hepsi gecti (KACTI). Stdout ASCII. Kemer aynada da acik (gercek kayit yok).
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
KI, UY, KB = "kisayol.py", "uygulama.py", "kabuk.py"
Ikame = tuple[str, str, str]
MUTANTLAR: list[tuple[str, str, list[Ikame], str]] = [
    ("MB1", "K1: servis ici cakisma denetimi ESKI kaydi kaldirmadan once (ayni ad haric) -- a1 bulgusunun duzeltmesi; davranis iyilesir",
     [(KI, "        self.kaldir(ad)\n        if any((m, v) == (mod, vk) for _, m, v in self._kayitlar.values()):\n            return KayitSonucu.CAKISMA\n",
       "        if any((m, v) == (mod, vk) for a, (_, m, v) in self._kayitlar.items() if a != ad):\n            return KayitSonucu.CAKISMA\n        self.kaldir(ad)\n")], "KACSIN"),
    ("MB2", "K1: basarisiz kayitta kimlik canli kumesinden dusurulmuyor (kimlik sizintisi)",
     [(KI, "            _canli_kimlikler.discard(kimlik)\n            self._son_hata_kodu = int(self._hata_kodu_fn())\n", "            self._son_hata_kodu = int(self._hata_kodu_fn())\n")], "?"),
    ("MB3", "K1: basarili kayitta son_hata_kodu sifirlanmiyor (onceki 1409 kalir)",
     [(KI, "        self._son_hata_kodu = 0\n        self._kayitlar[ad] = (kimlik, mod, vk)\n", "        self._kayitlar[ad] = (kimlik, mod, vk)\n")], "?"),
    ("MB4", "K1 (Y3): yikim temizleyicisi canli kimlikleri serbest birakmiyor",
     [(KI, "        kaldir_fn(kimlik)\n        _canli_kimlikler.discard(kimlik)\n", "        kaldir_fn(kimlik)\n")], "?"),
    ("MB5", "K5 kabuk: tepsi ipucu guncellenmiyor",
     [(KB, "        self._tepsi.ikon.setToolTip(\"Suflör — \" + \" · \".join(tepsi_parcalari))\n", "")], "YAKALA"),
    ("MB6", "K4: tetiklendi baglantisi pencereyi yakalayan lambda (Y-A1 zombi sinifi)",
     [(UY, "    servis.tetiklendi.connect(pencere.kisayol_tetiklendi)\n", "    servis.tetiklendi.connect(lambda ad: pencere.kisayol_tetiklendi(ad))\n")], "YAKALA"),
    ("MB7", "K1/K4: cikis_istendi yalniz anlik_cevir'i kaldirir",
     [(UY, "    pencere.cikis_istendi.connect(servis.hepsini_kaldir)\n", "    pencere.cikis_istendi.connect(lambda: servis.kaldir(\"anlik_cevir\"))\n")], "YAKALA"),
    ("MB8", "K2: bilinen kimlikte sinyal yayilir ama False doner (olay yutulmaz)",
     [(KI, "            servis.tetiklendi.emit(ad)\n        return True, 0\n", "            servis.tetiklendi.emit(ad)\n        return False, 0\n")], "YAKALA"),
    ("MB9", "K3: Ctrl+Alt+Shift+<tus> AltGr sorgusuna GIRER (Shift'li kombinasyon ALTGR_CAKISMA olur)",
     [(KI, "and not mod & MOD_SHIFT and self._altgr_karakteri_fn(vk):", "and self._altgr_karakteri_fn(vk):")], "YAKALA"),
    ("MB10", "K5: sebep metni 'ayarlardan degistirin' ekler (paket yasagi)",
     [(UY, "        return \"başka bir uygulama kullanıyor\"\n", "        return \"başka bir uygulama kullanıyor, ayarlardan değiştirin\"\n")], "YAKALA"),
    ("MB11", "K1: kaldir() filtre tablosundan silmiyor (kaldirilan kimlik hala sinyal yayar)",
     [(KI, "        self._kimlikler.pop(kimlik, None)\n        _canli_kimlikler.discard(kimlik)\n        self._kaldir_fn(kimlik)\n", "        _canli_kimlikler.discard(kimlik)\n        self._kaldir_fn(kimlik)\n")], "YAKALA"),
    ("MB12", "Y1: calistir servisi EBEVEYNSIZ kurar (yerel degisken dusunce kayitlar kalkar)",
     [(UY, "    servis = kisayol_servisi if kisayol_servisi is not None else KisayolServisi(pencere, gercek_win32=True)\n",
       "    servis = kisayol_servisi if kisayol_servisi is not None else KisayolServisi(None, gercek_win32=True)\n")], "YAKALA"),
    ("CB-1", "KONTROL (esdeger): kimlik tablosu guncelleme sirasi degisti",
     [(KI, "        self._kayitlar[ad] = (kimlik, mod, vk)\n        self._kimlikler[kimlik] = ad\n", "        self._kimlikler[kimlik] = ad\n        self._kayitlar[ad] = (kimlik, mod, vk)\n")], "KACSIN"),
]


def kos(ayna: Path, hedef: str, ek_ortam: dict[str, str]) -> tuple[int, int, list[str]]:
    ortam = {**os.environ, "QT_QPA_PLATFORM": "offscreen", "SUFLOR_GERCEK_KISAYOL_YASAK": "1", "PYTHONIOENCODING": "utf-8", **ek_ortam}
    r = subprocess.run([sys.executable, "-m", "pytest", hedef, "-q", "-p", "no:cacheprovider", "--import-mode=importlib", "-rf", "--no-header"],
                       cwd=str(ayna), env=ortam, capture_output=True, text=True, encoding="utf-8", errors="replace")
    cikti = r.stdout + r.stderr
    m = re.search(r"(\d+) failed", cikti)
    f = int(m.group(1)) if m else 0
    m2 = re.search(r"(\d+) passed", cikti)
    p = int(m2.group(1)) if m2 else 0
    dusen = re.findall(r"^FAILED (\S+)", cikti, re.M)
    hata = re.findall(r"^ERROR (\S+)", cikti, re.M)
    return f + len(hata), p, dusen + hata


def main() -> int:
    ayna = Path(tempfile.mkdtemp(prefix="t013_ayna_b_"))
    print(f"ayna: <gecici dizin>/{ayna.name}")
    (ayna / "src").mkdir()
    (ayna / "src" / "__init__.py").write_text("", encoding="utf-8")
    shutil.copytree(KOK / "src" / "ui", ayna / "src" / "ui", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(KOK / "tests" / "unit" / "ui", ayna / "tests" / "unit" / "ui", ignore=shutil.ignore_patterns("__pycache__"))
    for d in ("tests", "tests/unit"):
        (ayna / d / "__init__.py").write_text("", encoding="utf-8") if (KOK / d / "__init__.py").exists() else None
    hedef_b = ayna / ".agents" / "tasks" / "T-013" / "tester_B"
    hedef_b.mkdir(parents=True)
    for ad in ("conftest.py", "test_mercek_b.py"):
        shutil.copy(KOK / ".agents" / "tasks" / "T-013" / "tester_B" / ad, hedef_b / ad)
    (ayna / "pytest.ini").write_text("[pytest]\n", encoding="utf-8") if not (KOK / "pytest.ini").exists() else shutil.copy(KOK / "pytest.ini", ayna / "pytest.ini")
    if (KOK / "pyproject.toml").exists():
        shutil.copy(KOK / "pyproject.toml", ayna / "pyproject.toml")
    orijinal = {d: (ayna / "src" / "ui" / d).read_text(encoding="utf-8") for d in (KI, UY, KB)}
    f0, p0, _ = kos(ayna, "tests/unit/ui", {})
    fb0, pb0, _ = kos(ayna, ".agents/tasks/T-013/tester_B", {})
    print(f"TEMEL implementer: failed={f0} passed={p0} | tester-B: failed={fb0} passed={pb0} (1 xfail beklenir, failed sayilmaz)")
    print("ad    impl      tester-B  beklenen  aciklama")
    sorun: list[str] = []
    hangi: list[str] = []
    for ad, aciklama, ikameler, beklenen in MUTANTLAR:
        for dosya, eski, yeni in ikameler:
            yol = ayna / "src" / "ui" / dosya
            metin = yol.read_text(encoding="utf-8")
            if eski not in metin:
                print(f"{ad}: ikame metni bulunamadi ({dosya}) -- mutant bayat")
                return 2
            yol.write_text(metin.replace(eski, yeni, 1), encoding="utf-8")
        f_i, _, dusen_i = kos(ayna, "tests/unit/ui", {})
        f_b, _, dusen_b = kos(ayna, ".agents/tasks/T-013/tester_B", {})
        for dosya in orijinal:
            (ayna / "src" / "ui" / dosya).write_text(orijinal[dosya], encoding="utf-8")
        si = f"X ({f_i})" if f_i else "."
        sb = f"X ({f_b})" if f_b else "."
        print(f"{ad:5s} {si:9s} {sb:9s} {beklenen:9s} {aciklama}")
        hangi.append(f"{ad} impl: {', '.join(d.split('::')[-1] for d in dusen_i)[:400]}")
        hangi.append(f"{ad} tester-B: {', '.join(d.split('::')[-1] for d in dusen_b)[:400]}")
        if beklenen == "YAKALA" and not f_i:
            sorun.append(f"{ad} implementer testlerinden KACTI")
        if beklenen == "KACSIN" and f_i:
            sorun.append(f"{ad} kontrol mutanti implementer testlerinde yanlis pozitif")
    print()
    print("dusen testler:")
    for h in hangi:
        print("  " + h.encode("ascii", "backslashreplace").decode())
    print()
    print(f"beklenti tutmayan: {len(sorun)} {sorun}")
    shutil.rmtree(ayna, ignore_errors=True)
    return 1 if sorun else 0


if __name__ == "__main__":
    raise SystemExit(main())
