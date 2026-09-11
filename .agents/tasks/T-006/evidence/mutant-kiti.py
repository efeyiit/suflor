"""T-006 mutant kiti — testler hangi mutanti YAKALIYOR? (ayna agacinda, depo DEGISMEZ)

Her mutant `src/ocr/rapid_engine.py`nin bir kopyasina METIN duzeyinde uygulanir;
`tests/unit/ocr/test_rapid_engine.py` + sefin `conftest.py` ayna agacinda kosulur.
YAKALANDI = en az bir test dustu. MT-KONTROL davranis-esdegerdir; YAKALANMAMALI
(yanlis pozitif kontrolu).

Koşum: python .agents/tasks/T-006/evidence/mutant-kiti.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
KAYNAK = KOK / "src" / "ocr" / "rapid_engine.py"

MUTANTLAR: list[tuple[str, str, str, str]] = [
    # (ad, aciklama, eski, yeni)
    ("MT-01", "K5: text_score 0.0 -> 0.5 (kutuphane suzgeci ACIK)",
     '"Global.text_score": 0.0,', '"Global.text_score": 0.5,'),
    ("MT-02", "K3: ust sinir kaldirildi (cpu ustu sessiz otomatik)",
     "if not 1 <= n <= cekirdek:", "if not 1 <= n:"),
    ("MT-03", "K7: logger seviyesi fabrikadan ONCE cekiliyor",
     "        taniyici = self._fabrika(params)\n",
     "        logging.getLogger(_LOGGER_ADI).setLevel(logging.ERROR)\n        taniyici = self._fabrika(params)\n"),
    ("MT-03b", "K7: kurulum sonrasi setLevel kaldirildi",
     "        logging.getLogger(_LOGGER_ADI).setLevel(logging.ERROR)\n        self._taniyici = taniyici",
     "        self._taniyici = taniyici"),
    ("MT-04", "K7: Global.log_level params'tan cikarildi",
     '            "Global.log_level": "error",  # K7 (kurulum sirasi)\n', ""),
    ("MT-05", "K4: floor/ceil yerine round",
     "x0 = math.floor(float(noktalar[:, 0].min()))", "x0 = round(float(noktalar[:, 0].min()))"),
    ("MT-05c", "K4: x1 ceil yerine round",
     "x1 = math.ceil(float(noktalar[:, 0].max()))", "x1 = round(float(noktalar[:, 0].max()))"),
    ("MT-05d", "K4: y0 floor yerine round",
     "y0 = math.floor(float(noktalar[:, 1].min()))", "y0 = round(float(noktalar[:, 1].min()))"),
    ("MT-05b", "K4: ceil yerine floor (max kenar)",
     "y1 = math.ceil(float(noktalar[:, 1].max()))", "y1 = math.floor(float(noktalar[:, 1].max()))"),
    ("MT-06", "K4: y kaydirmasi yok",
     "        y=y0 + rect.y,", "        y=y0,"),
    ("MT-07", "K6: fabrika model kontrolunden ONCE cagriliyor",
     "        params = self.parametreler()\n        try:\n            taniyici = self._fabrika(params)",
     "        try:\n            taniyici = self._fabrika({})\n            params = self.parametreler()"),
    ("MT-08", "K11: JAPAN det 'multi' -> 'ch'",
     '(OcrLanguage.JAPAN, "multi", "japan")', '(OcrLanguage.JAPAN, "ch", "japan")'),
    ("MT-08b", "K11: ENGLISH rec 'en' -> 'ch'",
     '(OcrLanguage.ENGLISH, "ch", "en")', '(OcrLanguage.ENGLISH, "ch", "ch")'),
    ("MT-09", "K10: close() kapali bayragini koymuyor",
     "        self._kapali = True", "        pass"),
    ("MT-10", "K4: int() kesme (negatifte floor degil)",
     "x0 = math.floor(float(noktalar[:, 0].min()))", "x0 = int(float(noktalar[:, 0].min()))"),
    ("MT-11", "K3: inter_op anahtari threads yerine -1",
     '"EngineConfig.onnxruntime.inter_op_num_threads": self._threads,', '"EngineConfig.onnxruntime.inter_op_num_threads": -1,'),
    ("MT-12", "K3: use_cls True",
     '"Global.use_cls": False,', '"Global.use_cls": True,'),
    ("MT-13", "K5: metin strip ediliyor",
     "TextBlock(text=metin,", "TextBlock(text=metin.strip(),"),
    ("MT-14", "K6: 0-boyut denetimi kaldirildi",
     "    if img.shape[0] == 0 or img.shape[1] == 0:", "    if False:"),
    ("MT-15", "K5: bos sonucta (boxes None) OcrError",
     "            return []\n        if txts is None or scores is None:",
     "            raise OcrError('bos')\n        if txts is None or scores is None:"),
    ("MT-16", "K6: kutuphane istisnasi sarilmadan yayiliyor",
     "        except Exception as e:\n            raise OcrError(f\"tanıma basarisiz: {type(e).__name__}\") from e",
     "        except Exception:\n            raise"),
    ("MT-17", "K3: threads=None varsayilani 8 yerine -1",
     "return min(_VARSAYILAN_PARCACIK, cekirdek)", "return -1"),
    ("MT-18", "K6: allow_download=False'ta model_path gecilmiyor (root_dir ile)",
     '        p["Det.model_path"] = det_yol\n        p["Rec.model_path"] = rec_yol\n',
     '        p["Global.model_root_dir"] = dizin\n'),
    ("MT-KONTROL", "davranis-esdeger: sozluk anahtar sirasi degisti (YAKALANMAMALI)",
     '            "Global.text_score": 0.0,  # K5\n            "Global.use_cls": False,  # K3 / O3\n',
     '            "Global.use_cls": False,  # K3 / O3\n            "Global.text_score": 0.0,  # K5\n'),
]


def kos(ayna: Path) -> tuple[int, str]:
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/unit/ocr/test_rapid_engine.py", "-q", "-p", "no:cacheprovider"],
        cwd=str(ayna), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300,
        env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8", "PYTHONPATH": str(ayna)},
    )
    ozet = (r.stdout.strip().splitlines() or [""])[-1]
    return r.returncode, ozet


def main() -> int:
    ozgun = KAYNAK.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as td:
        ayna = Path(td) / "ayna"
        (ayna / ".agents").mkdir(parents=True)  # conftest kok bulucu isareti
        shutil.copytree(KOK / "src", ayna / "src", ignore=shutil.ignore_patterns("__pycache__"))
        (ayna / "tests" / "unit" / "ocr").mkdir(parents=True)
        for ad in ("conftest.py", "test_rapid_engine.py"):
            shutil.copy(KOK / "tests" / "unit" / "ocr" / ad, ayna / "tests" / "unit" / "ocr" / ad)
        hedef = ayna / "src" / "ocr" / "rapid_engine.py"

        kod, ozet = kos(ayna)
        print(f"TABAN      : exit={kod}  {ozet}")
        sonuc = 0
        for ad, aciklama, eski, yeni in MUTANTLAR:
            if ozgun.count(eski) != 1:
                print(f"{ad:10s}: HEDEF METIN {ozgun.count(eski)} KEZ BULUNDU -> mutant uygulanamadi ({aciklama})")
                sonuc = 1
                continue
            hedef.write_text(ozgun.replace(eski, yeni), encoding="utf-8")
            kod, ozet = kos(ayna)
            yakalandi = kod != 0
            beklenti = (not yakalandi) if ad == "MT-KONTROL" else yakalandi
            durum = "YAKALANDI" if yakalandi else "KACTI"
            print(f"{ad:10s}: {durum:9s} {'ok ' if beklenti else 'HATA'} {ozet:40s} -- {aciklama}")
            if not beklenti:
                sonuc = 1
        hedef.write_text(ozgun, encoding="utf-8")
    print("MUTANT KITI:", "TEMIZ" if sonuc == 0 else "SORUN VAR")
    return sonuc


if __name__ == "__main__":
    raise SystemExit(main())
