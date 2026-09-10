"""KIRMIZI FAZ (T-004, tur 7, T7-2) -- yeni kapinin HAM basarisizlik ciktisi.

Uc M15 mutanti GECICI bir depo kopyasinda tek tek kurulur ve
`test_k28_miras_sorgusu_ayni_params_ile_sorulur` her birinde kosulur.
Beklenen: UCUNDE de KIRMIZI (exit 1). Depo dosyalarina DOKUNULMAZ.

Kullanim (depo kokunden):
    python .agents/tasks/T-004/evidence/kirmizi_r7.py
Cikis: 0 = ucu de kirmizi, 1 = en az biri yesil kaldi
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _mutant_kopya_r7 import SORGU_SATIRI, kopya  # noqa: E402
from mutasyon_r7 import MUTANTLAR  # noqa: E402


def main() -> None:
    kirmizi = 0
    with kopya() as kok:
        urun = kok / "src" / "ocr" / "normalizer.py"
        temiz = urun.read_text(encoding="utf-8")
        assert temiz.count(SORGU_SATIRI) == 1, "miras sorgusunun cagri noktasi bulunamadi"
        for ad, yeni in MUTANTLAR.items():
            print("=" * 78)
            print(f"MUTANT {ad}")
            print(f"  kurulan cagri: _group_rejection_reason({yeni})")
            print("=" * 78)
            urun.write_text(temiz.replace(SORGU_SATIRI, yeni), encoding="utf-8")
            r = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/unit/ocr/test_normalizer.py",
                 "-q", "-k", "miras_sorgusu_ayni_params"],
                cwd=str(kok), capture_output=True, text=True)
            print(r.stdout + r.stderr)
            print(f"--> exit={r.returncode}  (KIRMIZI bekleniyor: 1)\n")
            kirmizi += int(r.returncode != 0)
        urun.write_text(temiz, encoding="utf-8")

    print(f"KIRMIZI olan mutant sayisi: {kirmizi}/{len(MUTANTLAR)}")
    print("(gecici kopya silindi; depo dosyalarina dokunulmadi)")
    sys.exit(0 if kirmizi == len(MUTANTLAR) else 1)


if __name__ == "__main__":
    main()
