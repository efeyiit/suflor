"""TESTER-B -- kacan mutantlar icin AYIRT ETME OLCUMU (feedback-B'nin onerdigi test eklerinin gucu).

    TESTER_B_SCRATCH=<dizin> python .agents/tasks/T-007/tester_B/mercekB_ayirt_etme.py

Ayri bir ayna agacinda (`t007_tester_B_ayirt`, models/ yok -- yalniz G2 birim kapisi):
  1. Teslim testleri + mutasyonsuz src -> gecmeli (taban)
  2. ONERILEN ek testler yamali test dosyasi + mutasyonsuz src -> gecmeli (yanlis pozitif yok)
  3. Alti terminator mutanti (K3-01..06) x {teslim testleri, yamali testler} -> G2 sonucu
  4. K10-08/K10-09 (hata mesajina motor ciktisi) x {teslim, yamali}
Beklenen: teslim testleri K3-03 ve K3-05'i (ve K10-08/09'u) KACIRIR; yamali testler HEPSINI yakalar.

Onerilen ekler (feedback-B.md ile birebir):
  (a) test_k3b parametrize'ina iki satir: ("A? B.", ["A?", "B."]), ("A！B。", ["A！", "B。"])
  (b) yeni test: her terminator TEK BASINA boler (6 nokta, dogrudan degismezin kendisi)
  (c) test_k6_hata_mesajlari_kaynak_metni_tasimaz'a nobetci tasiyan MOTOR CIKTISI noktasi (K10-08/09)
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mutant_kiti as MK  # noqa: E402  -- ayni mutant tanimlari, ayni yama mekanigi

DEPO = MK.DEPO
SCRATCH = Path(os.environ.get("TESTER_B_SCRATCH", tempfile.gettempdir()))
KOK = SCRATCH / "t007_tester_B_ayirt"
TEST = "tests/unit/translate/test_local_nmt.py"

EK_PARAM_HEDEF = '        ("A! B？ C.", ["A!", "B？", "C."]),  # karisik\n'
EK_PARAM = (
    EK_PARAM_HEDEF
    + '        ("A? B.", ["A?", "B."]),  # TESTER-B: ASCII soru isareti tek basina ayirt edici\n'
    + '        ("A！B。", ["A！", "B。"]),  # TESTER-B: CJK unlem tek basina ayirt edici\n'
)
EK_TEST_HEDEF = "def test_k3_cumlelere_bol_yardimcisi_ve_modele_gider() -> None:\n"
EK_TEST = (
    '@pytest.mark.parametrize("t", list(".!?。！？"))\n'
    "def test_k3b_her_terminator_tek_basina_boler(tmp_path: Path, t: str) -> None:\n"
    '    """TESTER-B: K3 degismezi ALTI isaretin her birinde ayri olculur (4.6/7: tek noktaya kapili uygulama gorunsun)."""\n'
    "    f = SahteFabrika()\n"
    '    saglayici(tmp_path, f).translate(istek([f"A{t}B{t} C{t}"]))\n'
    '    assert f.motor.gonderilen_parcalar() == [f"A{t}", f"B{t}", f"C{t}"]\n'
    "\n\n" + EK_TEST_HEDEF
)
EK_NOBETCI_HEDEF = '    ids=["sayi", "bozuk-cikti", "motor", "fabrika", "encode", "decode", "decode-tip"],\n'
EK_NOBETCI_PARAM_HEDEF = "        (lambda: SahteFabrika(SahteMotor(cikti=_n_hipotez(3))), ContractViolation),  # sayi uyusmazligi (2 cumle / 3 hipotez)\n"
EK_NOBETCI_PARAM = (
    EK_NOBETCI_PARAM_HEDEF
    + '        (lambda: SahteFabrika(SahteMotor(cikti=lambda t: [SahteHipotez([[HEDEF, "NOBETCI-9c1e"]])] * (len(t) + 1))), ContractViolation),  # TESTER-B: MOTOR CIKTISI nobetci tasir\n'
    + '        (lambda: SahteFabrika(SahteMotor(cikti=lambda t: [types.SimpleNamespace(hypotheses=None, metin="NOBETCI-9c1e") for _ in t])), ProviderUnavailable),  # TESTER-B: nesne repr nobetci tasir\n'
)
EK_NOBETCI_IDS = '    ids=["sayi", "sayi-nobetcili-cikti", "bozuk-nesne-nobetcili", "bozuk-cikti", "motor", "fabrika", "encode", "decode", "decode-tip"],\n'
EK_IMPORT_HEDEF = "import time\n"
EK_IMPORT = "import time\nimport types\n"

YAMA_TEST: list[tuple[str, str]] = [
    (EK_IMPORT_HEDEF, EK_IMPORT),
    (EK_PARAM_HEDEF, EK_PARAM),
    (EK_TEST_HEDEF, EK_TEST),
    (EK_NOBETCI_PARAM_HEDEF, EK_NOBETCI_PARAM),
    (EK_NOBETCI_HEDEF, EK_NOBETCI_IDS),
]

SECILEN = ["K3-01", "K3-02", "K3-03", "K3-04", "K3-05", "K3-06", "K10-08", "K10-09"]


def _kos() -> tuple[int, str]:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    env.pop("PYTHONIOENCODING", None)
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-rfE", TEST],
                       cwd=str(KOK), capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=600)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def _ozet(cikti: str) -> str:
    son = [ln for ln in cikti.strip().splitlines() if ln.strip()][-1:] or [""]
    dusen = [ln.split(" - ")[0].replace("FAILED ", "").split("::")[-1][:70] for ln in cikti.splitlines() if ln.startswith("FAILED")]
    return son[0][:60] + ("   dusen: " + "; ".join(dusen[:4]) + (" ..." if len(dusen) > 4 else "") if dusen else "")


def _test_yaz(yamali: bool) -> None:
    metin = (DEPO / TEST).read_text(encoding="utf-8")
    if yamali:
        for eski, yeni in YAMA_TEST:
            assert metin.count(eski) == 1, eski[:80]
            metin = metin.replace(eski, yeni, 1)
    (KOK / TEST).write_text(metin, encoding="utf-8")


def main() -> int:
    if KOK.exists():
        shutil.rmtree(KOK, ignore_errors=True)
    yoksay = shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache", ".mypy_cache")
    shutil.copytree(DEPO / "src", KOK / "src", ignore=yoksay)
    shutil.copytree(DEPO / "tests", KOK / "tests", ignore=yoksay)
    (KOK / ".agents").mkdir()
    MK.KOK = KOK  # mutant_kiti'nin yama/geri alma fonksiyonlari bu agacta calissin
    print(f"ayna agaci: {KOK}  (yalniz G2 birim kapisi)")
    print()
    for yamali in (False, True):
        _test_yaz(yamali)
        rc, out = _kos()
        print(f"TABAN {'YAMALI' if yamali else 'teslim'} testler + mutasyonsuz src: exit={rc}  {_ozet(out)}")
    print()
    print(f"{'mutant':8s} {'teslim testleri':40s} {'yamali testler':40s}")
    for mid in SECILEN:
        mut = next(m for m in MK.MUTANTLAR if m.mid == mid)
        sonuc = []
        for yamali in (False, True):
            _test_yaz(yamali)
            MK._uygula(mut)
            try:
                rc, out = _kos()
            finally:
                MK._geri_al()
            sonuc.append(("X " if rc != 0 else ". ") + _ozet(out))
        print(f"{mid:8s} {sonuc[0][:60]:60s} | {sonuc[1][:120]}")
        print(f"         {mut.aciklama[:110]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
