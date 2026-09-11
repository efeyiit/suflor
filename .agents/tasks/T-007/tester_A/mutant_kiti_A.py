"""Tester-A mutant kiti — `src/` kopyası mutasyona uğratılır, `test_mercek_a.py` ona karşı koşulur.

    python .agents/tasks/T-007/tester_A/mutant_kiti_A.py

Her mutant için: geçici köke `src/` kopyalanır, `src/translate/local_nmt.py`
üzerinde TEK metinsel değişiklik yapılır, `TESTER_A_KOK=<geçici kök>` ile
tester-A testleri koşulur. Beklenti: mutant YAKALANIR (en az bir test düşer).
MA-00 (kimlik sabiti) kopyanın gerçekten yüklendiğinin kanıtıdır; MA-99
davranış-eşdeğer kontrol mutantıdır ve YAKALANMAMALIDIR (ölçüler mesaja
değil davranışa bağlı). Stdout yalnız ASCII; çeviri metni yok.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
TEST_DIZINI = Path(__file__).resolve().parent
HEDEF = "src/translate/local_nmt.py"

# (ad, aranan, yerine, beklenen_yakalanma)
MUTANTLAR: list[tuple[str, str, str, bool]] = [
    ("MA-00 kimlik sabiti degisti (kopya yukleniyor mu)", '"local-nmt-nllb200-600m-int8"', '"local-nmt-MUTANT"', True),
    ("MA-01 Y1: ASCII nokta terminator degil", '_TERMINATORLER: Final = ".!?。！？"', '_TERMINATORLER: Final = "!?。！？"', True),
    ("MA-02 Y1: v1 kurali (yalniz CJK)", '_TERMINATORLER: Final = ".!?。！？"', '_TERMINATORLER: Final = "。！？"', True),
    ("MA-03 Y2: suzgec yok", "    return any(ch.isalnum() for ch in parca)", "    return True", True),
    ("MA-04 Y2: rakam sayilmaz", "    return any(ch.isalnum() for ch in parca)", "    return any(ch.isalpha() for ch in parca)", True),
    ("MA-05 K2: ensure_aligned cagrisi yok", "        ensure_aligned(request, sonuc)\n", "        pass\n", True),
    ("MA-06 K2: cumle sayimi yok", "    if len(cikti) != beklenen:\n        raise ContractViolation(", "    if False:\n        raise ContractViolation(", True),
    ("MA-07 K3: kapanis isaretleri dahil degil", '_KAPANIS_ISARETLERI: Final = "」』）)\\"\'”’»"', '_KAPANIS_ISARETLERI: Final = "№"', True),  # bos kume regex'i patlatir (toplama hatasi); hic gecmeyen tek karakter
    ("MA-08 K3: birlestirme bosluksuz", '                cikti = " ".join(ceviriler[idx] if idx >= 0 else parca for parca, idx in plan)', '                cikti = "".join(ceviriler[idx] if idx >= 0 else parca for parca, idx in plan)', True),
    ("MA-09 K3: gecis segmenti bos doner", "                cikti = segment.text  # K3 (Y2)", '                cikti = ""  # MUTANT', True),
    ("MA-10 K3: strip yok", "    return [p.strip() for p in parcalar if p.strip()]", "    return [p for p in parcalar if p.strip()]", True),
    ("MA-11 K4: harf duyarli", "    dil = _KAYNAK_KODLARI.get(kod.lower())", "    dil = _KAYNAK_KODLARI.get(kod)", True),
    ("MA-12 K4: ISO kodu tabloda yok", '"jpn_jpan": NmtDili.JAPAN, "ja": NmtDili.JAPAN, "japan": NmtDili.JAPAN,', '"jpn_jpan": NmtDili.JAPAN, "japan": NmtDili.JAPAN,', True),
    ("MA-13 K4: kaynak belirteci SONA", "            tokenler = [[kaynak.value, *encode(p), _SON_BELIRTECI] for p in parcalar]", "            tokenler = [[*encode(p), _SON_BELIRTECI, kaynak.value] for p in parcalar]", True),
    ("MA-14 K4: target_prefix tek satir", "                target_prefix=[[hedef.value]] * len(tokenler),", "                target_prefix=[[hedef.value]] * min(1, len(tokenler)),", True),
    ("MA-15 K4: detected_lang None", "            detected_lang=kaynak.value,", "            detected_lang=None,", True),
    ("MA-16 K4: hedef 'en' kabul", '    "tr": NmtDili.TURKISH, "tur": NmtDili.TURKISH,', '    "tr": NmtDili.TURKISH, "tur": NmtDili.TURKISH, "en": NmtDili.TURKISH,', True),
    ("MA-17 K5: sayim yerine in (gereken=1)", "        gereken = max(1, kaynak.count(yt))", "        gereken = 1", True),
    ("MA-18 K5: kosulsuz ekleme", "        ekler.extend([yt] * (gereken - cikti.count(yt)))", "        ekler.extend([yt] * gereken)", True),
    ("MA-19 K5: onarim yok", "            sonuclar.append(_yer_tutuculari_onar(cikti, segment.text, segment.placeholders))", "            sonuclar.append(cikti)", True),
    ("MA-20 K5: bos yer tutucu atlanmaz", "        if not yt or yt in islenen:", "        if yt in islenen:", True),
    ("MA-21 K2: hedef belirteci kosulsuz atilir", "        if tokenler and tokenler[0] == hedef_kodu:\n            tokenler = tokenler[1:]", "        if tokenler:\n            tokenler = tokenler[1:]", True),
    ("MA-22 K8: np.int64 duzlestirilmez", "    n = int(threads)\n    if not 1 <= n <= cekirdek:", "    n = threads  # type: ignore[assignment]\n    if not 1 <= n <= cekirdek:", True),
    ("MA-23 K8: beam_size=0 kabul", "    if n < 1:\n        raise ValueError(f\"beam_size", "    if n < 0:\n        raise ValueError(f\"beam_size", True),
    ("MA-24 K8: rp nan kabul", "    if not math.isfinite(x) or x < 1.0:", "    if x < 1.0:", True),
    ("MA-25 K8: rp 1.0 iken de gecilir", "        if self._repetition_penalty != 1.0:", "        if True:", True),
    ("MA-26 K9: latency int", "            latency_ms=(time.perf_counter() - t0 - kurulum_s) * 1000.0,", "            latency_ms=int((time.perf_counter() - t0 - kurulum_s) * 1000.0),", True),
    ("MA-27 K2: bos istekte translations liste", "            translations=tuple(sonuclar),", "            translations=tuple(sonuclar) if sonuclar else [],  # type: ignore[arg-type]", True),
    ("MA-28 K4: source_lang=None kabul (JAPAN varsayilan)", "    if not isinstance(kod, str):\n        raise ProviderUnavailable(\n            \"kaynak dili verilmedi", "    if kod is None:\n        return NmtDili.JAPAN\n    if not isinstance(kod, str):\n        raise ProviderUnavailable(\n            \"kaynak dili verilmedi", True),
    ("MA-29 K3: bos segment cikti None", "                cikti = segment.text  # K3 (Y2)", "                cikti = segment.text or \" \"  # MUTANT", True),
    ("MA-99 KONTROL: hata mesaji metni degisti (davranis esdeger)", 'raise ProviderUnavailable(f"desteklenmeyen kaynak dili kodu: {kod!r}; kabul: {sorted(_KAYNAK_KODLARI)}")', 'raise ProviderUnavailable("MUTANT mesaj")', False),
]


def kos(kok: Path) -> tuple[int, str]:
    env = dict(os.environ, TESTER_A_KOK=str(kok), PYTHONDONTWRITEBYTECODE="1")
    r = subprocess.run(
        [sys.executable, "-m", "pytest", str(TEST_DIZINI), "-q", "-p", "no:cacheprovider", "-x", "--no-header", "-o", "console_output_style=classic"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, cwd=str(kok), timeout=600,
    )
    return r.returncode, r.stdout + r.stderr


def main() -> int:
    kaynak = (KOK / HEDEF).read_text(encoding="utf-8")
    yakalanan = 0
    beklenen_toplam = sum(1 for m in MUTANTLAR if m[3])
    hatalar: list[str] = []
    print(f"Tester-A mutant kiti: {len(MUTANTLAR)} mutant ({beklenen_toplam} yakalanmali + {len(MUTANTLAR) - beklenen_toplam} kontrol)")
    for ad, aranan, yerine, beklenen in MUTANTLAR:
        if kaynak.count(aranan) != 1:
            hatalar.append(ad)
            print(f"  HATA   {ad}: aranan metin {kaynak.count(aranan)} kez bulundu (1 olmali) -> mutant uygulanamadi")
            continue
        with tempfile.TemporaryDirectory(prefix="t007-mutantA-") as td:
            kok = Path(td)
            shutil.copytree(KOK / "src", kok / "src", ignore=shutil.ignore_patterns("__pycache__"))
            (kok / HEDEF).write_text(kaynak.replace(aranan, yerine), encoding="utf-8")
            kod, cikti = kos(kok)
            dusen = [s for s in cikti.splitlines() if s.startswith("FAILED") or s.startswith("ERROR")]
            ozet = next((s for s in reversed(cikti.splitlines()) if "passed" in s or "failed" in s or "error" in s), "?")
            if beklenen:
                ok = kod != 0
                yakalanan += ok
                ilk = (dusen[0].split("::", 1)[-1].split(" - ")[0] if dusen else "-")[:90].encode("ascii", "replace").decode("ascii")
                print(f"  {'ok    ' if ok else 'KACTI '} {ad}: {ozet.strip()} | ilk dusen: {ilk}")
            else:
                ok = kod == 0
                print(f"  {'ok    ' if ok else 'ASIRI '} {ad}: {ozet.strip()} (yakalanmamali)")
                if not ok:
                    hatalar.append(ad)
    print()
    print(f"MUTANT-A: {yakalanan}/{beklenen_toplam} yakalandi; kontrol {'temiz' if not hatalar else 'HATALI: ' + ', '.join(hatalar)}")
    return 0 if yakalanan == beklenen_toplam and not hatalar else 1


if __name__ == "__main__":
    raise SystemExit(main())
