"""T-011 `test_k5_sure_8000_uyeli_zincir_60ms_alti` sure titremesi -- T-012 tam takim kosumunda gorulen dusme (T-012 modulu DEGIL).

    python .agents/tasks/T-012/evidence/olcum-t011-sure-titremesi.py

T-012 tur-1 tam takim kosumlarinda (`pytest-tum-kosum1-t011-sure-titremesi.txt`: gecerli 62.3 ms; `pytest-tum.txt`:
68.5 ms; sinir 60 ms) bu test iki kez dustu; duzeltme sonrasi kosumda (`pytest-tum-tur1-son.txt`) gecti.
Bu betik testin KENDI yardimcilariyla (`fixture_v3_store`, `_medyan_ms`; test dosyasi degistirilmez) ayni olcumu
(a) bosta ve (b) 2 is parcacigi CPU yuku altinda 5'er kez tekrarlar: sinirin yuk altinda mi asildigini gosterir.
Stdout ASCII; mutlak yol yok.
"""
from __future__ import annotations

import os
import sys
import tempfile
import threading
import time
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(KOK))
sys.path.insert(0, str(KOK / "tests" / "unit" / "translate"))

import test_sozluk as ts  # noqa: E402  (tests/unit/translate/test_sozluk.py -- T-011 test modulu, salt okunur kullanim)


def olc(etiket: str, tekrar: int = 5) -> list[tuple[float, float]]:
    sonuc: list[tuple[float, float]] = []
    for _ in range(tekrar):
        with tempfile.TemporaryDirectory() as d:
            s = ts.fixture_v3_store(Path(d))
            gecerli = "Marcus" * 8000
            olu = "Marcus" * 8000 + "x"
            m1 = ts._medyan_ms(lambda: s.lookup(gecerli))
            m2 = ts._medyan_ms(lambda: s.lookup(olu))
            sonuc.append((m1, m2))
    asim = sum(1 for m1, m2 in sonuc if m1 >= 60 or m2 >= 60)
    print(f"[{etiket}] gecerli/olu ms: " + ", ".join(f"{m1:.1f}/{m2:.1f}" for m1, m2 in sonuc) + f"  -> sinir 60 ms asimi {asim}/{tekrar}")
    return sonuc


def yuk(dur: threading.Event) -> None:
    x = 0
    while not dur.is_set():
        x = (x * 1103515245 + 12345) & 0x7FFFFFFF


def main() -> int:
    print(f"T-011 K5 8000 uyeli zincir sure olcumu; cekirdek={os.cpu_count()} izleyici={'var' if sys.gettrace() else 'yok'}")
    olc("bosta")
    dur = threading.Event()
    isler = [threading.Thread(target=yuk, args=(dur,), daemon=True) for _ in range(2)]
    for i in isler:
        i.start()
    time.sleep(0.2)
    olc("2 is parcacigi CPU yuku (ayni surec, GIL paylasimi)")
    dur.set()
    for i in isler:
        i.join()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
