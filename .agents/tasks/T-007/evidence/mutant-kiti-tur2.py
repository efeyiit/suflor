"""T-007 mutant ayirt-etme kiti, TUR 2 (implementer) -- tur 2 testleri tur 1'in kacirdigini yakaliyor mu?

    python .agents/tasks/T-007/evidence/mutant-kiti-tur2.py

Depoya DOKUNMAZ: `src/contracts`, `src/translate`, `tests/unit/translate`
scratchpad altinda bir AYNA agacina kopyalanir; tur 1 test dosyasi
`git show HEAD:tests/unit/translate/test_local_nmt.py` ile aynaya
`test_local_nmt_tur1.py` adiyla konur. Her mutant aynadaki `local_nmt.py`ye
uygulanir ve IKI test dosyasi ayri ayri kosulur. Stdout ASCII; ceviri metni
basilmaz. Cikis 0 = her beklenti tuttu.

Sutunlar: `tur2` = bu turun test dosyasi, `tur1` = HEAD'deki (tur 1) dosya.
`X (n)` = n test dustu (yakalandi), `.` = hepsi gecti (kacti).

Beklentiler (sef karari tur 2 + feedback-B tablosu):
  K3-01..06  alti terminator mutanti: tur2 ALTISINI da yakalar; tur1 `?` (K3-03)
             ve `！` (K3-05) icin KACIRIR (feedback-B'nin olctugu kor nokta).
  T2-2-M*    yer tutucu suzgeci tur 1 davranisina donduruldu: tur2 yakalar; tur1
             kacirir (o davranis tur 1'in kendisi).
  K10-08..11 hata mesajina motor ciktisi/nesne repr'i sizdiriliyor: tur2 yakalar;
             tur1 kacirir (yalniz kaynak nobetcisi vardi).
  C-1..C-4   davranis-esdeger degisiklikler: IKISI de kacirmali (yanlis pozitif yok).
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
KAYNAK = KOK / "src" / "translate" / "local_nmt.py"
TEST = KOK / "tests" / "unit" / "translate" / "test_local_nmt.py"

TERM = ".!?。！？"


def _term_eksik(ch: str) -> str:
    return TERM.replace(ch, "")


def _u(s: str) -> str:
    return " ".join(f"U+{ord(c):04X}" for c in s)


# (ad, aciklama, eski, yeni, tur2_yakalamali, tur1_yakalamali)
MUTANTLAR: list[tuple[str, str, str, str, bool, bool]] = [
    # --- T2-1: alti terminator, her biri ayri ---
    *[
        (
            f"K3-0{i + 1}", f"K3 (Y1): terminator kumesinden {_u(ch)} EKSIK",
            f'_TERMINATORLER: Final = "{TERM}"',
            f'_TERMINATORLER: Final = "{_term_eksik(ch)}"',
            True, ch not in "?！",  # tur 1 dosyasi `?` ve `！` icin KOR (feedback-B)
        )
        for i, ch in enumerate(TERM)
    ],
    # --- T2-2: yer tutucu suzgeci ---
    (
        "T2-2-M1", "K3 suzgeci yer tutuculari GORMUYOR (tur 1 davranisi: `{PLAYER}!` modele gider)",
        "                if modele_gider(parca, segment.placeholders):  # T2-2: yer tutucular cikarildiktan sonra karar",
        "                if modele_gider(parca):",
        True, False,
    ),
    (
        "T2-2-M2", "K3 suzgeci yer tutucunun yalniz ILK gecisini cikariyor (`{0}{0}!` gider)",
        '            kalan = kalan.replace(yt, "")',
        '            kalan = kalan.replace(yt, "", 1)',
        True, False,
    ),
    (
        "T2-2-M3", "K3 suzgeci: yalniz yer tutucudan olusan segment ciktida bos (aynen degil)",
        "                cikti = segment.text  # K3 (Y2): hicbir parcasi modele gitmeyen segment AYNEN",
        '                cikti = "" if segment.placeholders else segment.text',
        True, False,
    ),
    # --- T2-3: hata mesajina motor ciktisi / nesne repr'i siziyor ---
    (
        "K10-08", "K6/PROTOKOL 7: sayi uyusmazligi mesaji motor CIKTISINI (`{cikti!r}`) tasiyor",
        '            f"hipotez={len(cikti)} (provider={_SAGLAYICI_KIMLIGI!r})"',
        '            f"hipotez={len(cikti)} (provider={_SAGLAYICI_KIMLIGI!r}) cikti={cikti!r}"',
        True, False,
    ),
    (
        "K10-09", "K6/PROTOKOL 7: bozuk hipotez mesaji NESNE repr'ini (`{nesne!r}`) tasiyor",
        '            raise ProviderUnavailable(f"motor ciktisinda hipotez listesi yok ya da bos: {type(nesne).__name__}")',
        '            raise ProviderUnavailable(f"motor ciktisinda hipotez listesi yok ya da bos: {nesne!r}")',
        True, False,
    ),
    (
        "K10-10", "K6/PROTOKOL 7: token tipi mesaji HIPOTEZI (`{tokenler!r}`) tasiyor",
        '            raise ProviderUnavailable("hipotez tokenleri str degil")',
        '            raise ProviderUnavailable(f"hipotez tokenleri str degil: {tokenler!r}")',
        True, False,
    ),
    (
        "K10-11", "K6/PROTOKOL 7: decode tip mesaji DONEN NESNEYI (`{metinler!r}`) tasiyor",
        '            raise ProviderUnavailable("decode str dondurmedi")',
        '            raise ProviderUnavailable(f"decode str dondurmedi: {metinler!r}")',
        True, False,
    ),
    # --- davranis-esdeger kontroller: IKISI DE KACMALI ---
    (
        "C-1", "modele_gider: `replace` yerine `split/join` (esdeger)",
        '            kalan = kalan.replace(yt, "")',
        '            kalan = "".join(kalan.split(yt))',
        False, False,
    ),
    (
        "C-2", "modele_gider: generator yerine liste (esdeger)",
        "    return any(ch.isalnum() for ch in kalan)",
        "    return any([ch.isalnum() for ch in kalan])",
        False, False,
    ),
    (
        "C-3", "terminator kumesi AYNI, sirasi farkli (karakter sinifi -- esdeger)",
        f'_TERMINATORLER: Final = "{TERM}"',
        '_TERMINATORLER: Final = "。！？.!?"',
        False, False,
    ),
    (
        "C-4", "latency carpani 1000.0 -> 1e3 (esdeger)",
        "            latency_ms=(time.perf_counter() - t0 - kurulum_s) * 1000.0,",
        "            latency_ms=(time.perf_counter() - t0 - kurulum_s) * 1e3,",
        False, False,
    ),
    (
        "C-5", "close() satir sirasi degisti (esdeger)",
        "        self._motor = None\n        self._encode = None\n        self._decode = None\n        self._kapali = True",
        "        self._kapali = True\n        self._decode = None\n        self._encode = None\n        self._motor = None",
        False, False,
    ),
]


def _tur1_mutantlari() -> list[tuple[str, str, str, str, bool, bool]]:
    """Tur 1 kitinin (`mutant-kiti.py`) M-* mutantlari -- regresyon: ikisi de yakalamali.

    M-02'nin hedef satiri T2-2 ile degisti; uyarlanmis hali burada (`M-02'`).
    Esdeger kontrolleri (C-*) yukarida zaten var (C-2/C-4/C-5), alinmaz.
    """
    import importlib.util

    yol = Path(__file__).resolve().parent / "mutant-kiti.py"
    spec = importlib.util.spec_from_file_location("mutant_kiti_tur1", yol)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    sonuc: list[tuple[str, str, str, str, bool, bool]] = []
    for ad, aciklama, eski, yeni, yakalanmali in mod.MUTANTLAR:
        if not yakalanmali:
            continue
        if ad == "M-02":
            eski = "                if modele_gider(parca, segment.placeholders):  # T2-2: yer tutucular cikarildiktan sonra karar"
            ad = "M-02'"
        sonuc.append((ad, f"[tur 1] {aciklama}", eski, yeni, True, True))
    return sonuc


MUTANTLAR += _tur1_mutantlari()


def main() -> int:
    kaynak = KAYNAK.read_text(encoding="utf-8")
    for ad, _, eski, _, _, _ in MUTANTLAR:
        assert kaynak.count(eski) == 1, f"{ad}: hedef parca kaynakta tam bir kez bulunmali (bulunan {kaynak.count(eski)})"

    tur1 = subprocess.run(
        ["git", "show", "HEAD:tests/unit/translate/test_local_nmt.py"],
        capture_output=True, cwd=str(KOK), check=True,
    ).stdout.decode("utf-8")
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=str(KOK), check=True).stdout.strip()

    scratch = os.environ.get("T007_AYNA") or tempfile.mkdtemp(prefix="t007-ayna-tur2-")
    ayna = Path(scratch)
    print(f"ayna: {ayna}")
    print(f"tur 1 test dosyasi: git show {head}:tests/unit/translate/test_local_nmt.py ({len(tur1.splitlines())} satir)")
    (ayna / "src").mkdir(parents=True, exist_ok=True)
    shutil.copytree(KOK / "src" / "contracts", ayna / "src" / "contracts", dirs_exist_ok=True)
    shutil.copytree(KOK / "src" / "translate", ayna / "src" / "translate", dirs_exist_ok=True)
    shutil.copytree(KOK / "tests" / "unit" / "translate", ayna / "tests" / "unit" / "translate", dirs_exist_ok=True)
    for pyc in ayna.rglob("__pycache__"):
        shutil.rmtree(pyc, ignore_errors=True)
    hedef = ayna / "src" / "translate" / "local_nmt.py"
    test2 = ayna / "tests" / "unit" / "translate" / "test_local_nmt.py"
    test1 = ayna / "tests" / "unit" / "translate" / "test_local_nmt_tur1.py"
    test1.write_text(tur1, encoding="utf-8")
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONPATH": str(ayna)}

    def kos(test: Path) -> tuple[int, int, int, list[str]]:
        """-> (exit, failed, passed, dusen test adlari)"""
        r = subprocess.run(
            [sys.executable, "-m", "pytest", str(test), "-q", "-p", "no:cacheprovider", "--no-header", "-rf"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(ayna), env=env, timeout=600,
        )
        failed = passed = 0
        m = re.search(r"(\d+) failed", r.stdout)
        if m:
            failed = int(m.group(1))
        m = re.search(r"(\d+) passed", r.stdout)
        if m:
            passed = int(m.group(1))
        dusen = [ln.split("::", 1)[1].split(" - ")[0] for ln in r.stdout.splitlines() if ln.startswith("FAILED ")]
        if r.returncode != 0 and failed == 0:
            dusen = ["<toplama/kosum hatasi>"]
        return r.returncode, failed, passed, dusen

    def kisa(dusen: list[str], n: int = 3) -> str:
        s = ", ".join(dusen[:n]) + (f", +{len(dusen) - n}" if len(dusen) > n else "")
        return s.encode("ascii", "backslashreplace").decode("ascii")

    hedef.write_text(kaynak, encoding="utf-8")
    k2, f2, p2, _ = kos(test2)
    k1, f1, p1, d1 = kos(test1)
    print(f"temel (mutantsiz): tur2 exit={k2} {p2} passed / {f2} failed ; tur1 exit={k1} {p1} passed / {f1} failed")
    if k2 != 0:
        print("TEMEL KOSUM (tur2) DUSTU -- kit anlamsiz")
        return 1
    if k1 != 0:
        print(f"  tur 1 dosyasi yeni src'de dusuyor (bayatlayan testler): {kisa(d1, 10)}")

    print()
    print(f"  {'mutant':9s} {'tur2':10s} {'tur1':10s} aciklama")
    hatalar = 0
    for ad, aciklama, eski, yeni, bek2, bek1 in MUTANTLAR:
        hedef.write_text(kaynak.replace(eski, yeni), encoding="utf-8")
        k2, f2, _, d2 = kos(test2)
        k1, f1, _, d1 = kos(test1)
        y2, y1 = k2 != 0, k1 != 0
        s2 = f"X ({f2})" if y2 else "."
        s1 = f"X ({f1})" if y1 else "."
        isaret = ""
        if y2 != bek2:
            hatalar += 1
            isaret += "  <-- tur2 BEKLENTI DISI"
        if y1 != bek1:
            hatalar += 1
            isaret += "  <-- tur1 BEKLENTI DISI"
        print(f"  {ad:9s} {s2:10s} {s1:10s} {aciklama}{isaret}")
        if y2:
            print(f"            tur2 dusen: {kisa(d2)}")
        if y1:
            print(f"            tur1 dusen: {kisa(d1)}")
    hedef.write_text(kaynak, encoding="utf-8")
    print()
    n_m = sum(1 for m in MUTANTLAR if m[4])
    n_c = len(MUTANTLAR) - n_m
    if hatalar:
        print(f"MUTANT KITI TUR 2: {hatalar} beklenti tutmadi")
        return 1
    n_t1 = sum(1 for m in MUTANTLAR if m[1].startswith("[tur 1]"))
    print(
        f"MUTANT KITI TUR 2 TEMIZ: tur2 {n_m}/{n_m} mutant yakalandi ({n_m - n_t1} yeni + {n_t1} tur-1 regresyonu), "
        f"{n_c}/{n_c} esdeger kontrol kacti; tur1 dosyasi K3-03 (?) ve K3-05 (U+FF01), T2-2-M*, K10-08..11 icin KOR (beklenen)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
