"""D8 -- Makinenin gormedigi kapilar.

`validate.py` sunlari DENETLEMEZ: `known_gaps` icerigi (hatta VARLIGI),
`commands` SAYISI, "baska `no cover` yasak" kurali. Paket ucunu de "sef elle
denetler" diye isaretliyor.

Tester KOR calisir (PROTOKOL kapi 2): `delivery.md` okunamaz. Bu yuzden burada
olculebilen ikisi olculur:
  (a) validate.py'nin korlugu -- SENTETIK bir teslim dosyasiyla yeniden uretilir
      (gercek `delivery.md` OKUNMAZ);
  (b) paketin "Kararlarini IKI YERE yaz" kuralinin DOCSTRING yarisi -- K2, K5,
      K8, K10, K11 (+K12) zorunlu maddeleri kaynak docstring'lerinde var mi.

`known_gaps` yarisi ve `commands` sayisi sefin elle denetleyecegi kalemdir;
tester korlugu geregi burada olculemez ve verdict'te oyle bildirilir.
"""
from __future__ import annotations

import re
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

DEPO = Path(__file__).resolve().parents[4]
VALIDATE = DEPO / ".agents" / "validate.py"
SERVICE = (DEPO / "src" / "capture" / "service.py").read_text(encoding="utf-8")
MONITORS = (DEPO / "src" / "capture" / "monitors.py").read_text(encoding="utf-8")
KAYNAKLAR = SERVICE + "\n" + MONITORS

SENTETIK = textwrap.dedent("""\
    ---
    task: T-005
    role: implementer
    round: 1
    status: tamamlandi
    files_written:
      - src/capture/service.py
    commands:
      - cmd: "echo tek komut"
        exit_code: 0
        evidence: kanit.txt
    known_gaps: []
    ---
    """)


def _validate(tmp_path: Path, on_bilgi: str) -> subprocess.CompletedProcess[str]:
    (tmp_path / "kanit.txt").write_text("sahte kanit\n", encoding="utf-8")
    p = tmp_path / "sentetik_teslim.md"
    p.write_text(on_bilgi, encoding="utf-8")
    return subprocess.run([sys.executable, str(VALIDATE), str(p)],
                          cwd=str(DEPO), capture_output=True, text=True,
                          encoding="utf-8")


def test_d8_validate_bos_known_gaps_i_GORMUYOR(tmp_path: Path) -> None:
    r = _validate(tmp_path, SENTETIK)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "KABUL EDILEBILIR" in r.stdout, (
        "beklenmedik: validate.py artik known_gaps icerigini denetliyor -- "
        "verdict notu guncellenmeli"
    )


def test_d8_validate_known_gaps_ALANININ_YOKLUGUNU_gormuyor(tmp_path: Path) -> None:
    r = _validate(tmp_path, SENTETIK.replace("known_gaps: []\n", ""))
    assert r.returncode == 0, r.stdout + r.stderr


def test_d8_validate_commands_SAYISINI_gormuyor(tmp_path: Path) -> None:
    """Paket BES komut sart kosuyor; validate.py yalnizca 'bos degil' diyor."""
    r = _validate(tmp_path, SENTETIK)
    assert r.returncode == 0
    assert re.search(r"\b1 komut/kontrol\b", r.stdout), r.stdout


def test_d8_validate_no_cover_kuralini_hic_bilmiyor() -> None:
    metin = VALIDATE.read_text(encoding="utf-8")
    assert "no cover" not in metin and "pragma" not in metin
    assert "known_gaps" not in metin


# --------------------------------------------------------------------------
# "IKI YERE yaz" kuralinin DOCSTRING yarisi (tester bunu olcebilir)
# --------------------------------------------------------------------------

ZORUNLU_MADDELER = [
    ("K2  seq yalniz tek ornek icinde", r"seq` yalnizca TEK ORNEK|ornekler ARASINDA calismaz"),
    ("K5  monitor kimligi konumsal/kararsiz", r"KONUMSAL ve KARARSIZ"),
    ("K8  servis DPI olcegi uretemez", r"DPI olcegi URETEMEZ"),
    ("K8  intersect metadata'si kullanilmaz", r"intersect. ciktisinin metadata'si \*\*kullanilmaz\*\*"),
    ("K8  capture_full dpi_scale 1.0", r"capture_full` icin `1\.0`"),
    ("K10 DPI politikasi kalici degisiyor", r"PER_MONITOR_DPI_AWARE"),
    ("K10 QApplication'dan once cagirma", r"QApplication` kurulmadan"),
    ("K10 kapatilmayan MSS sizintisi", r"5001\. kapatilmamis"),
    ("K11 gercek mss.grab medyani 13.5 ms", r"13\.5 ms"),
    ("K11 5.7 butcesi zaten asiliyor", r"butcesi `mss` ile \*\*zaten asiliyor\*\*"),
    ("K12 thread-safe degil", r"thread-safe \*\*degildir\*\*"),
]


@pytest.mark.parametrize("ad,desen", ZORUNLU_MADDELER, ids=[a.split()[0] + a.split()[1][:6]
                                                            for a, _ in ZORUNLU_MADDELER])
def test_d8_zorunlu_karar_docstring_de_var(ad: str, desen: str) -> None:
    assert re.search(desen, KAYNAKLAR), (
        f"zorunlu karar docstring'de YOK: {ad} (desen: {desen}) -- paket bunu "
        f"'IKI YERE yaz' diye sart kosuyor"
    )
