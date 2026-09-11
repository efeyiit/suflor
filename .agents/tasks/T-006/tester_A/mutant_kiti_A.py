"""Tester-A mutant kiti — ayna ağacında koşar, depoya DOKUNMAZ.

Her mutant `src/ocr/rapid_engine.py`'nin AYNA kopyasına tek bir metin
değişikliğiyle uygulanır; sonra (a) implementer'ın `test_rapid_engine.py`
ve (b) tester-A'nın `test_a_sozlesme_sayisal.py` koşulur. Amaç: mercek A'nın
sınıflarında hangi takımın ayırt etme gücü var, ölçmek (§4.6/4, /10).

    python .agents/tasks/T-006/tester_A/mutant_kiti_A.py

Çıktı: stdout (ham); kanıt olarak `tester_A_evidence/mutant-A.txt`'ye yönlendirilir.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
assert (KOK / ".agents").is_dir(), KOK

MOTOR_REL = Path("src/ocr/rapid_engine.py")

# (etiket, eski, yeni, açıklama, beklenti)  beklenti: "YAKALANMALI" | "KACMALI"
MUTANTLAR: list[tuple[str, str, str, str, str]] = [
    ("MA-01", "monitor_index=rect.monitor_index,", "monitor_index=0,",
     "K4: monitor_index sabit 0 (birlesim -1 kaybolur)", "YAKALANMALI"),
    ("MA-02", "dpi_scale=rect.dpi_scale,", "dpi_scale=1.0,",
     "K4: dpi_scale sabit 1.0", "YAKALANMALI"),
    ("MA-03", "w=x1 - x0,", "w=x1 - (x0 + rect.x),",
     "K4: genislik kaydirilmis x ile hesaplaniyor", "YAKALANMALI"),
    ("MA-04", "    return float(deger)\n", "    return deger  # type: ignore[return-value]\n",
     "K5: confidence ham puan (np.float32 sizar)", "YAKALANMALI"),
    ("MA-05", "if isinstance(threads, bool) or not isinstance(threads, numbers.Integral):",
     "if not isinstance(threads, numbers.Integral):",
     "K3: bool threads kabul (True==1 sessiz)", "YAKALANMALI"),
    ("MA-06", '(OcrLanguage.KOREAN, "multi", "korean"),', '(OcrLanguage.KOREAN, "ch", "korean"),',
     "K11: KOREAN det multi->ch (tek dil yanlis)", "YAKALANMALI"),
    ("MA-07", "    if img.dtype != np.uint8:\n", "    if False:\n",
     "K6c: dtype denetimi kaldirildi (int32 motora gider)", "YAKALANMALI"),
    ("MA-08", "    return float(deger)\n", "    return round(float(deger), 2)\n",
     "K5: confidence 2 haneye yuvarlaniyor (sessiz bozulma)", "YAKALANMALI"),
    ("MA-09", "x1 = math.ceil(float(noktalar[:, 0].max()))", "x1 = math.floor(float(noktalar[:, 0].max())) + 1",
     "K4: ceil yerine floor+1 (tam sayi kosede fazla piksel)", "YAKALANMALI"),
    ("MA-10", "        if not isinstance(metin, str):\n",
     "        if _puan(puan) < 0.5:\n            continue\n        if not isinstance(metin, str):\n",
     "K5: motor duzeyinde 0.5 esigi", "YAKALANMALI"),
    ("MA-11", "y=y0 + rect.y,", "y=y0 + rect.x,",
     "K4: y kaydirmasi rect.x ile", "YAKALANMALI"),
    ("MA-12", 'for ad in ("x", "y", "monitor_index"):', 'for ad in ("x", "y"):',
     "K6c: monitor_index numpy denetimi kaldirildi", "YAKALANMALI"),
    ("MA-13", "x0 = math.floor(float(noktalar[:, 0].min()))", "x0 = math.floor(float(noktalar[0, 0]))",
     "K4: min yerine ilk kose (egik cokgende yanlis)", "YAKALANMALI"),
    ("MA-14", "if not 1 <= n <= cekirdek:", "if not 1 <= n < cekirdek:",
     "K3: ust sinir dahil degil (threads=cpu_count reddedilir)", "YAKALANMALI"),
    ("MA-15", "x0 = math.floor(float(noktalar[:, 0].min()))", "x0 = int(float(noktalar[:, 0].min()))",
     "K4: floor yerine int() (negatifte sifira dogru)", "YAKALANMALI"),
    ("MA-16", "x0 = math.floor(float(noktalar[:, 0].min()))", "x0 = np.int64(math.floor(float(noktalar[:, 0].min())))",
     "K4: x0 np.int64 (type is int bozulur, json duser)", "YAKALANMALI"),
    ("MA-17", "y1 = math.ceil(float(noktalar[:, 1].max()))", "y1 = math.ceil(float(noktalar[:, 1].max())) + 0 if noktalar.shape[0] > 1 else math.ceil(float(noktalar[:, 1].max())) + 1",
     "K4: tek noktali cokgende h+1 (dejenere yol farkli)", "YAKALANMALI"),
    ("MA-KONTROL", "zip(boxes, txts, scores, strict=True)", "zip(boxes, txts, scores)",
     "davranis-esdeger: uzunluk zaten denetlendi", "KACMALI"),
]


def kos(ayna: Path, hedef: str) -> tuple[int, str]:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    r = subprocess.run(
        [sys.executable, "-m", "pytest", hedef, "-q", "-p", "no:cacheprovider", "-x", "--no-header"],
        cwd=str(ayna), capture_output=True, text=True, encoding="utf-8", errors="replace", env=env,
    )
    satirlar = [s for s in r.stdout.strip().splitlines() if s.strip()]
    ozet = satirlar[-1] if satirlar else r.stderr.strip().splitlines()[-1:] or ["?"]
    return r.returncode, ozet if isinstance(ozet, str) else ozet[0]


def main() -> int:
    ayna = Path(tempfile.mkdtemp(prefix="t006_mutantA_"))
    (ayna / ".agents" / "tasks" / "T-006").mkdir(parents=True)
    (ayna / ".agents" / "tasks" / "T-004").mkdir(parents=True)
    shutil.copytree(KOK / "src", ayna / "src")
    (ayna / "tests" / "unit" / "ocr").mkdir(parents=True)
    for ad in ("conftest.py", "test_rapid_engine.py"):
        shutil.copy2(KOK / "tests" / "unit" / "ocr" / ad, ayna / "tests" / "unit" / "ocr" / ad)
    shutil.copytree(KOK / ".agents" / "tasks" / "T-006" / "tester_A", ayna / ".agents" / "tasks" / "T-006" / "tester_A",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    motor = ayna / MOTOR_REL
    orijinal = motor.read_text(encoding="utf-8")

    IMPL = "tests/unit/ocr/test_rapid_engine.py"
    TESTA = ".agents/tasks/T-006/tester_A/test_a_sozlesme_sayisal.py"

    print(f"ayna: {ayna}")
    c0, s0 = kos(ayna, IMPL)
    c1, s1 = kos(ayna, TESTA)
    print(f"TABAN      impl exit={c0} {s0} | testerA exit={c1} {s1}")
    if c0 != 0 or c1 != 0:
        print("TABAN KIRIK -- kit gecersiz")
        return 2

    temiz = True
    for etiket, eski, yeni, aciklama, beklenti in MUTANTLAR:
        if orijinal.count(eski) != 1:
            print(f"{etiket:10s}: HEDEF METIN {orijinal.count(eski)} KEZ BULUNDU -- mutant uygulanamadi ({aciklama})")
            temiz = False
            continue
        motor.write_text(orijinal.replace(eski, yeni), encoding="utf-8")
        ci, si = kos(ayna, IMPL)
        ca, sa = kos(ayna, TESTA)
        motor.write_text(orijinal, encoding="utf-8")
        yak_i, yak_a = ci != 0, ca != 0
        if beklenti == "YAKALANMALI":
            durum = "YAKALANDI" if (yak_i or yak_a) else "KACTI  !!"
            if not (yak_i or yak_a):
                temiz = False
        else:
            durum = "KACTI ok" if not (yak_i or yak_a) else "YAKALANDI !! (esdeger olmali)"
            if yak_i or yak_a:
                temiz = False
        print(f"{etiket:10s}: {durum:12s} impl={'DUSTU' if yak_i else 'gecti':5s} ({si[:38]:38s}) "
              f"testerA={'DUSTU' if yak_a else 'gecti':5s} ({sa[:38]:38s}) -- {aciklama}")

    print("MUTANT KITI A:", "TEMIZ" if temiz else "BULGU VAR")
    shutil.rmtree(ayna, ignore_errors=True)
    return 0 if temiz else 1


if __name__ == "__main__":
    raise SystemExit(main())
