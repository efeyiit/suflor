"""T7-2'nin DISLERI -- M15 sinifi UC mutantla olculur (T-004, tur 7).

DEGISMEZ (sef_karari-tur7.md, T7-2): miras-uygunluk sorgusu, `_group`'a
verilen AYNI `params` nesnesiyle sorulur; on ayar esigi sorgu ICINDE
degistirilemez.

Her mutant GECICI bir depo kopyasinda kurulur (bkz. `_mutant_kopya_r7.py`)
ve bes kapi ayri ayri kosulur: dort kabul komutu + urun testleri (T7-2
HARIC, yani "kapinin OLMADIGI tur 6 durumu") + T7-2. Aranan: T7-2 UC
mutanti da YAKALAMALI (exit != 0). Depo dosyalarina DOKUNULMAZ.

Kullanim (depo kokunden):
    python .agents/tasks/T-004/evidence/mutasyon_r7.py
Cikis: 0 = T7-2 ucunu de yakaladi, 1 = en az biri kacti
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _mutant_kopya_r7 import SORGU_SATIRI, kopya  # noqa: E402

T72 = "tests/unit/ocr/test_normalizer.py::test_k28_miras_sorgusu_ayni_params_ile_sorulur"

MUTANTLAR = {
    "M15-a  sorgu SABIT `tooltip` params'i ile soruluyor": (
        "*_raw_query_pair(tail, nxt, blocks), get_params(OcrPreset.TOOLTIP), "
        "ignore_length=True"
    ),
    "M15-b  sorgu ICINDE on ayar esigi ikame ediliyor (replace, 0.3)": (
        "*_raw_query_pair(tail, nxt, blocks), "
        "replace(params, max_vertical_gap_ratio=0.3), ignore_length=True"
    ),
    "M15-c  sorgu SABIT `dialogue` params'i ile soruluyor (KARARIN M15'i)": (
        "*_raw_query_pair(tail, nxt, blocks), get_params(OcrPreset.DIALOGUE), "
        "ignore_length=True"
    ),
}

KOMUTLAR = [
    ("KABUL 1  mypy --strict",
     [sys.executable, "-m", "mypy", "--strict", "src/ocr/normalizer.py", "src/ocr/presets.py"]),
    ("KABUL 2  urun testleri, T7-2 HARIC  (= kapinin OLMADIGI tur 6 durumu)",
     [sys.executable, "-m", "pytest", "tests/unit/ocr/test_normalizer.py", "-q",
      "--deselect", T72]),
    ("KABUL 3  purity_check",
     [sys.executable, ".agents/tasks/T-004/purity_check.py"]),
    ("KABUL 4  olcu kiti (bes kanal)",
     [sys.executable, ".agents/tasks/T-004/olcu_kiti.py"]),
    ("T7-2     YENI KAPI",
     [sys.executable, "-m", "pytest", "tests/unit/ocr/test_normalizer.py", "-q",
      "-k", "miras_sorgusu_ayni_params"]),
]


def kos(kok: Path, cmd: list[str]) -> tuple[int, str]:
    r = subprocess.run(cmd, cwd=str(kok), capture_output=True, text=True)
    satirlar = [s for s in (r.stdout + r.stderr).strip().splitlines() if s.strip()]
    return r.returncode, (satirlar[-1] if satirlar else "")


def tablo(kok: Path, baslik: str) -> dict[str, int]:
    print("\n" + "=" * 78)
    print(baslik)
    print("=" * 78)
    kodlar: dict[str, int] = {}
    for ad, cmd in KOMUTLAR:
        kod, son = kos(kok, cmd)
        kodlar[ad] = kod
        print(f"  {ad:<62} exit={kod}")
        print(f"      | {son}")
    return kodlar


def main() -> None:
    with kopya() as kok:
        urun = kok / "src" / "ocr" / "normalizer.py"
        temiz = urun.read_text(encoding="utf-8")
        assert temiz.count(SORGU_SATIRI) == 1, "miras sorgusunun cagri noktasi bulunamadi"

        tablo(kok, "KONTROL: MUTASYONSUZ kopya (hepsi exit 0 olmali)")

        yakalandi: dict[str, bool] = {}
        for ad, yeni in MUTANTLAR.items():
            urun.write_text(temiz.replace(SORGU_SATIRI, yeni), encoding="utf-8")
            kodlar = tablo(kok, f"MUTANT {ad}")
            yakalandi[ad] = kodlar["T7-2     YENI KAPI"] != 0
        urun.write_text(temiz, encoding="utf-8")

    print("\n" + "=" * 78)
    print("SONUC")
    print("=" * 78)
    for ad, y in yakalandi.items():
        print(f"  {'YAKALANDI' if y else 'KACIRILDI'}  <- T7-2  |  {ad}")
    tum = len(yakalandi) == len(MUTANTLAR) and all(yakalandi.values())
    print()
    print("T7-2 UC MUTANTI DA YAKALIYOR -- test DISLIDIR." if tum
          else "T7-2 EN AZ BIR MUTANTI KACIRIYOR -- test yetersiz.")
    print("(gecici kopya silindi; depo dosyalarina dokunulmadi)")
    sys.exit(0 if tum else 1)


if __name__ == "__main__":
    main()
