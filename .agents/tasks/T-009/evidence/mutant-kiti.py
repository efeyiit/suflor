"""T-009 mutant ayirt-etme kiti (implementer, tur 1).

    python .agents/tasks/T-009/evidence/mutant-kiti.py            # birim testler (hizli)
    python .agents/tasks/T-009/evidence/mutant-kiti.py --gercek   # + gercek modelle kapilar (~2-3 dk)

Depoya DOKUNMAZ: `src/`, `tests/unit/ocr/{conftest,test_rapid_engine}.py`,
T-006 fixture'lari ve iki `real_check.py` scratchpad altinda bir AYNA
agacina kopyalanir (`T009_AYNA` ile yer secilebilir); `models/` (NMT) icin
aynada bir junction acilir (kopyalanmaz). Her mutant aynadaki
`rapid_engine.py`ye metin ikamesiyle uygulanir. Stdout ASCII; metin
basilmaz. Cikis 0 = her beklenti tuttu.

`X (n)` = n birim testi dustu (YAKALANDI), `.` = hepsi gecti (KACTI).

Mutantlar (paket "Ayirt etme"):
  M01  KOREAN Rec.ocr_version v5 -> v4 geri (dosya adi v5 kalir).
       Beklenti: birim YAKALAR; --gercek: T-009 real_check GECER (olculdu:
       `Rec.model_path` acik verildiginde dosya baskin; surum yalniz
       indirme yolunda belirleyici -- bkz. olcum-1).
  M02  KOREAN rec dosya adi v5 -> v4 geri (surum v5 kalir).
       Beklenti: birim YAKALAR (ModelMissingError/acik yol testleri);
       --gercek: T-009 real_check DUSER (#1 '.'=0, #2 6 kelime, #3 ~1100 ms).
  M01+M02  ikisi v4 = T-009 oncesi kod. Pozitif kontrol: birim YAKALAR,
       --gercek: DUSER.
  M03  JAPAN Rec.ocr_version v4 -> v5 (KOREAN da v5).
       Beklenti: birim YAKALAR (JAPAN v4 testi); --gercek: JAPAN motoru
       gercek kutuphanede ne yapar, OLCULUR ve YAZILIR (olculdu, olcum-1 E/F:
       indirme yolunda `OcrError <- ValueError`; acik v4 `model_path`
       yolunda SESSIZCE v4 kosar, 4 blok -- gercek kapi M03'u GOREMEZ,
       tek bekci JAPAN v4 birim testi).
  C-1  KONTROL: `_DIL_TABLOSU` satir sirasi degisir (esdeger) -> KACMALI.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
KAYNAK = KOK / "src" / "ocr" / "rapid_engine.py"
TEST = KOK / "tests" / "unit" / "ocr" / "test_rapid_engine.py"

KR_V5 = '    (OcrLanguage.KOREAN, "multi", "korean", "PP-OCRv5"),  # v4 noktayi vermiyor (T-009 K1/K4)\n'
KR_V4 = '    (OcrLanguage.KOREAN, "multi", "korean", "PP-OCRv4"),  # v4 noktayi vermiyor (T-009 K1/K4)\n'
JP_V4 = '    (OcrLanguage.JAPAN, "multi", "japan", "PP-OCRv4"),  # v5 YOK (ValueError, T-009 K5)\n'
JP_V5 = '    (OcrLanguage.JAPAN, "multi", "japan", "PP-OCRv5"),  # v5 YOK (ValueError, T-009 K5)\n'
DOSYA_V5 = '    (OcrLanguage.KOREAN, "multi_PP-OCRv3_det_mobile.onnx", "korean_PP-OCRv5_rec_mobile.onnx"),  # T-009 K1\n'
DOSYA_V4 = '    (OcrLanguage.KOREAN, "multi_PP-OCRv3_det_mobile.onnx", "korean_PP-OCRv4_rec_mobile.onnx"),  # T-009 K1\n'

# (ad, aciklama, [(eski, yeni), ...], birim yakalamali, gercek kapi, gercek kapi dusmeli)
#
# M01 gercek-kapi beklentisi ILK KOSUMDA "duser" idi ve TUTMADI (olculdu, tur 1):
# `allow_download=False` yolunda `Rec.model_path` ACIK verildiginden kutuphane
# DOSYAYI yukler, `Rec.ocr_version`i dosya secimi icin kullanmaz -> v5 dosyasi
# yuklenir, noktalar gelir, kapi GECER. Belirleyici olan `_MODEL_DOSYALARI`
# (M02 kapiyi dusurur). `Rec.ocr_version`in indirme yolunda (model_path YOK)
# belirleyici oldugu ayri kitle olculdu: `olcum-1-surum-mu-dosya-mi-baskin.py`.
# Beklenti buna gore GECER olarak duzeltildi; birim testler M01'i yine yakalar.
MUTANTLAR: list[tuple[str, str, list[tuple[str, str]], bool, str | None, bool]] = [
    ("M01", "KOREAN Rec.ocr_version v5 -> v4 geri (dosya adi v5)", [(KR_V5, KR_V4)], True, "t009", False),
    ("M02", "KOREAN rec dosya adi v5 -> v4 geri (surum v5)", [(DOSYA_V5, DOSYA_V4)], True, "t009", True),
    ("M01+M02", "IKISI v4 = T-009 oncesi kod (pozitif kontrol)", [(KR_V5, KR_V4), (DOSYA_V5, DOSYA_V4)], True, "t009", True),
    ("M03", "JAPAN Rec.ocr_version v4 -> v5 (KOREAN da v5)", [(JP_V4, JP_V5)], True, "japan", False),
    ("C-1", "KONTROL: _DIL_TABLOSU satir sirasi (JAPAN<->KOREAN) esdeger", [(JP_V4 + KR_V5, KR_V5 + JP_V4)], False, None, False),
]


def ayna_kur(ayna: Path) -> None:
    if ayna.exists():
        # junction'i rmtree ile silmek hedefi SILMEZ (Windows junction), ama
        # once acikca kaldiralim.
        j = ayna / "models"
        if j.exists():
            subprocess.run(["cmd", "/c", "rmdir", str(j)], capture_output=True)
        shutil.rmtree(ayna)
    ayna.mkdir(parents=True)
    shutil.copytree(KOK / "src", ayna / "src", ignore=shutil.ignore_patterns("__pycache__"))
    (ayna / "tests" / "unit" / "ocr").mkdir(parents=True)
    for ad in ("conftest.py", "test_rapid_engine.py"):
        shutil.copy(KOK / "tests" / "unit" / "ocr" / ad, ayna / "tests" / "unit" / "ocr" / ad)
    (ayna / ".agents" / "tasks" / "T-004").mkdir(parents=True)  # conftest KOK cozumu icin
    shutil.copytree(KOK / ".agents" / "tasks" / "T-006" / "fixtures", ayna / ".agents" / "tasks" / "T-006" / "fixtures")
    (ayna / ".agents" / "tasks" / "T-009").mkdir(parents=True)
    shutil.copy(KOK / ".agents" / "tasks" / "T-009" / "real_check.py", ayna / ".agents" / "tasks" / "T-009" / "real_check.py")
    r = subprocess.run(["cmd", "/c", "mklink", "/J", str(ayna / "models"), str(KOK / "models")], capture_output=True)
    if r.returncode != 0:
        print("UYARI: models junction acilamadi; --gercek #2 NMT'siz kalir")


def _env(ayna: Path) -> dict[str, str]:
    return dict(os.environ, PYTHONPATH=str(ayna), PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")


def birim(ayna: Path) -> tuple[int, int, int, list[str]]:
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/unit/ocr/test_rapid_engine.py", "-q",
         "-p", "no:cacheprovider", "--no-header", "-rf"],
        cwd=str(ayna), env=_env(ayna), capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    m_f = re.search(r"(\d+) failed", r.stdout)
    m_p = re.search(r"(\d+) passed", r.stdout)
    m_e = re.search(r"(\d+) error", r.stdout)
    dusen = [ln.split("::", 1)[1].split(" ")[0] for ln in r.stdout.splitlines() if ln.startswith("FAILED ")]
    return (int(m_f.group(1)) if m_f else 0, int(m_p.group(1)) if m_p else 0,
            int(m_e.group(1)) if m_e else (0 if (m_f or m_p) else 1), dusen)


def gercek_t009(ayna: Path) -> tuple[int, list[str]]:
    """Aynada T-009 real_check; (exit, satirlar). Metin basmaz (kapi ASCII)."""
    r = subprocess.run([sys.executable, ".agents/tasks/T-009/real_check.py"], cwd=str(ayna), env=_env(ayna),
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
    satirlar = [ln.strip() for ln in (r.stdout + r.stderr).splitlines() if ln.strip().startswith(("ok", "IHLAL", "REAL_CHECK"))]
    return r.returncode, satirlar


def gercek_japan(ayna: Path) -> str:
    """JAPAN motorunu gercek kutuphanede kurmayi dener; istisna tipini/ozetini dondurur."""
    kod = (
        "import sys, numpy as np\n"
        "from PIL import Image\n"
        "from pathlib import Path\n"
        "from src.contracts.models import Frame, OcrPreset, Rect\n"
        "from src.ocr.rapid_engine import OcrLanguage, RapidOcrEngine\n"
        "img = np.array(Image.open(Path('.agents/tasks/T-006/fixtures/dlg_JP.png')).convert('RGB'))[:, :, ::-1].copy()\n"
        "f = Frame(image=img, rect=Rect(0, 0, 1200, 400), captured_at=0.0, seq=0)\n"
        "m = RapidOcrEngine(language=OcrLanguage.JAPAN, threads=8, allow_download=False)\n"
        "print('params Rec.ocr_version =', m.parametreler()['Rec.ocr_version'])\n"
        "try:\n"
        "    bl = m.recognize(f, OcrPreset.DIALOGUE)\n"
        "    print('SONUC: istisna YOK;', len(bl), 'blok')\n"
        "except Exception as e:\n"
        "    print('SONUC:', type(e).__name__, '<- cause', type(e.__cause__).__name__ if e.__cause__ else None)\n"
    )
    r = subprocess.run([sys.executable, "-c", kod], cwd=str(ayna), env=_env(ayna),
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    return " | ".join(ln for ln in (r.stdout + r.stderr).splitlines() if ln.startswith(("params", "SONUC")))


def main() -> int:
    gercek = "--gercek" in sys.argv
    ayna = Path(os.environ.get("T009_AYNA") or (Path(os.environ.get("TEMP", ".")) / "t009_ayna"))
    ayna_kur(ayna)
    kaynak_ayna = ayna / "src" / "ocr" / "rapid_engine.py"
    orijinal = kaynak_ayna.read_text(encoding="utf-8")

    print("T-009 mutant kiti -- ayna:", ayna, "| gercek model:", "EVET" if gercek else "HAYIR")
    f, p, e, _ = birim(ayna)
    print(f"TEMEL (mutantsiz): failed={f} passed={p} error={e}")
    if f or e or p == 0:
        print("TEMEL kirmizi -- kit anlamsiz"); return 2
    if gercek:
        rc, sat = gercek_t009(ayna)
        print(f"TEMEL gercek T-009 real_check: exit={rc}")
        for s in sat:
            print("      ", s)
        if rc != 0:
            print("TEMEL gercek kapi kirmizi -- kit anlamsiz"); return 2

    hatalar: list[str] = []
    for ad, aciklama, ikameler, yakalanmali, kapi, kapi_dusmeli in MUTANTLAR:
        metin = orijinal
        bozuk = False
        for eski, yeni in ikameler:
            if metin.count(eski) != 1:
                print(f"{ad:8} ?        {aciklama}  [IKAME NOKTASI {metin.count(eski)} KEZ -- KIT BOZUK]")
                bozuk = True
                break
            metin = metin.replace(eski, yeni)
        if bozuk:
            hatalar.append(ad); continue
        kaynak_ayna.write_text(metin, encoding="utf-8")
        f, p, e, dusen = birim(ayna)
        yakalandi = (f + e) > 0
        sonuc = f"X ({f + e})" if yakalandi else "."
        beklenen = "YAKALA" if yakalanmali else "KACSIN"
        durum = "" if yakalandi == yakalanmali else "  <-- BEKLENTI TUTMADI"
        if durum:
            hatalar.append(ad)
        print(f"{ad:8} {sonuc:8} {beklenen:10} {aciklama}{durum}")
        for d in dusen:
            print(f"        dusen: {d}")
        if gercek and kapi == "t009":
            rc, sat = gercek_t009(ayna)
            dustu = rc != 0
            tuttu = dustu == kapi_dusmeli
            print(f"        gercek T-009 real_check: exit={rc}  "
                  + ("DUSTU" if dustu else "GECTI") + f" (beklenen: {'DUSER' if kapi_dusmeli else 'GECER -- dosya yolu baskin'})"
                  + ("" if tuttu else "  <-- BEKLENTI TUTMADI"))
            for s in sat:
                print("          ", s)
            if not tuttu:
                hatalar.append(ad + "-gercek")
        if gercek and kapi == "japan":
            print(f"        gercek JAPAN kurulum: {gercek_japan(ayna)}")
    kaynak_ayna.write_text(orijinal, encoding="utf-8")

    n_mut = sum(1 for m in MUTANTLAR if m[3])
    print()
    print(f"{n_mut} davranis mutanti + {len(MUTANTLAR) - n_mut} kontrol; beklenti tutmayan: {len(hatalar)} {hatalar}")
    return 1 if hatalar else 0


if __name__ == "__main__":
    raise SystemExit(main())
