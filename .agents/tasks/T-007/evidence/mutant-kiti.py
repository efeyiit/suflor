"""T-007 mutant ayirt-etme kiti (implementer, tur 1) -- test dosyasi mutantlari YAKALIYOR mu?

    python .agents/tasks/T-007/evidence/mutant-kiti.py

Depoya DOKUNMAZ: `src/` ve `tests/unit/translate/` scratchpad altinda bir AYNA
agacina kopyalanir, her mutant aynadaki `local_nmt.py`ye uygulanir, test dosyasi
o aynada kosulur. Stdout ASCII; ceviri metni basilmaz. Cikis 0 = her mutant
yakalandi VE her esdeger kontrol kacti (yanlis pozitif yok).

Mutantlar paketin K2/K3/K4/K5/K6/K8/K9/K10 degismezlerini teker teker bozar;
C-* kontrolleri davranis-esdeger degisikliklerdir ve KACMALIDIR.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
KAYNAK = KOK / "src" / "translate" / "local_nmt.py"
TEST = KOK / "tests" / "unit" / "translate" / "test_local_nmt.py"

# (ad, aciklama, eski, yeni, yakalanmali)
MUTANTLAR: list[tuple[str, str, str, str, bool]] = [
    (
        "M-01", "K3/Y1: bolme DILE gore (JP/KR/ZH -> yalniz CJK isaretleri; EN -> ASCII) -- v1 hatasi",
        "            for parca in cumlelere_bol(segment.text):",
        "            for parca in (cumlelere_bol(segment.text) if kaynak is NmtDili.ENGLISH else [p.strip() for p in re.split('(?<=[。！？])', segment.text) if p.strip()]):",
        True,
    ),
    (
        "M-02", "K3/Y2: parca suzgeci kaldirildi -- her parca modele gider",
        "                if modele_gider(parca):",
        "                if True:",
        True,
    ),
    (
        "M-03", "K2/O3: cumle sayisi denetimi kaldirildi (kisa olan kadar zip)",
        "    if len(cikti) != beklenen:\n        raise ContractViolation(",
        "    if False:\n        raise ContractViolation(",
        True,
    ),
    (
        "M-04", "K2: ensure_aligned cagrisi kaldirildi",
        "        ensure_aligned(request, sonuc)\n        return sonuc",
        "        return sonuc",
        True,
    ),
    (
        "M-05", "K5/O1: sayim yerine `in` kontrolu (ikinci `%s` sessizce kaybolur)",
        "        gereken = max(1, kaynak.count(yt))\n        ekler.extend([yt] * (gereken - cikti.count(yt)))",
        "        if yt not in cikti:\n            ekler.append(yt)",
        True,
    ),
    (
        "M-06", "K5: onarim tamamen kaldirildi",
        "            sonuclar.append(_yer_tutuculari_onar(cikti, segment.text, segment.placeholders))",
        "            sonuclar.append(cikti)",
        True,
    ),
    (
        "M-07", "K8: repetition_penalty 1.0 iken de motora geciliyor",
        "        if self._repetition_penalty != 1.0:\n            ek[\"repetition_penalty\"] = self._repetition_penalty",
        "        ek[\"repetition_penalty\"] = self._repetition_penalty",
        True,
    ),
    (
        "M-08", "K8: inter_threads = threads (1 degil)",
        "            \"inter_threads\": 1,",
        "            \"inter_threads\": self._threads,",
        True,
    ),
    (
        "M-09", "K9: latency kurulum suresini ICERIYOR",
        "            latency_ms=(time.perf_counter() - t0 - kurulum_s) * 1000.0,",
        "            latency_ms=(time.perf_counter() - t0) * 1000.0,",
        True,
    ),
    (
        "M-10", "K10: close() motoru BIRAKMIYOR",
        "        self._motor = None\n        self._encode = None\n        self._decode = None\n        self._kapali = True",
        "        self._kapali = True",
        True,
    ),
    (
        "M-11", "K10: segment metni stdout'a yaziliyor",
        "        for i, segment in enumerate(request.segments):\n            if not isinstance(segment.text, str):",
        "        for i, segment in enumerate(request.segments):\n            __import__('sys').stdout.write(str(segment.text))\n            if not isinstance(segment.text, str):",
        True,
    ),
    (
        "M-12", "K10: segment metni propagate=False, adi bilinmeyen bir logger'a INFO yaziliyor",
        "        for i, segment in enumerate(request.segments):\n            if not isinstance(segment.text, str):",
        "        for i, segment in enumerate(request.segments):\n            _lg = __import__('logging').getLogger('gizli.kanal'); _lg.propagate = False; _lg.setLevel(20); _lg.info('%s', segment.text)\n            if not isinstance(segment.text, str):",
        True,
    ),
    (
        "M-13", "K4: source_lang=None sessizce JAPAN sayiliyor",
        "        kaynak = kaynak_dili_coz(request.source_lang)",
        "        kaynak = NmtDili.JAPAN if request.source_lang is None else kaynak_dili_coz(request.source_lang)",
        True,
    ),
    (
        "M-14", "K6/O4: yalniz model.bin + sentencepiece denetleniyor (v1 listesi)",
        "    return [ad for ad in _ZORUNLU_DOSYALAR if not (model_dir / ad).is_file()]",
        "    return [ad for ad in _ZORUNLU_DOSYALAR[:2] if not (model_dir / ad).is_file()]",
        True,
    ),
    (
        "M-15", "K3: segment ciktisi bosluksuz birlestiriliyor",
        "                cikti = \" \".join(ceviriler[idx] if idx >= 0 else parca for parca, idx in plan)",
        "                cikti = \"\".join(ceviriler[idx] if idx >= 0 else parca for parca, idx in plan)",
        True,
    ),
    (
        "M-16", "K9/O2: max_decoding_length 160 (demo degeri)",
        "_MAKS_COZUM_UZUNLUGU: Final = 256",
        "_MAKS_COZUM_UZUNLUGU: Final = 160",
        True,
    ),
    (
        "M-17", "K3/Y2: hicbir parcasi modele gitmeyen segment bos string oluyor (aynen degil)",
        "                cikti = segment.text  # K3 (Y2): hicbir parcasi modele gitmeyen segment AYNEN",
        "                cikti = \"\"",
        True,
    ),
    (
        "M-18", "K4: kaynak belirteci basa degil SONA konuyor",
        "            tokenler = [[kaynak.value, *encode(p), _SON_BELIRTECI] for p in parcalar]",
        "            tokenler = [[*encode(p), _SON_BELIRTECI, kaynak.value] for p in parcalar]",
        True,
    ),
    (
        "M-19", "K6: fabrika istisnasi sarilmadan yayiliyor (ProviderUnavailable degil)",
        "        except Exception as e:\n            raise ProviderUnavailable(f\"ceviri motoru kurulamadi: {type(e).__name__}\") from e",
        "        except ValueError as e:\n            raise ProviderUnavailable(f\"ceviri motoru kurulamadi: {type(e).__name__}\") from e",
        True,
    ),
    (
        "M-20", "K10: kapali saglayici bos istegi KABUL ediyor (kapali denetimi bos istekte atlaniyor)",
        "        if self._kapali:\n            raise ProviderUnavailable(",
        "        if self._kapali and request.segments:\n            raise ProviderUnavailable(",
        True,
    ),
    (
        "M-21", "K3: tum segmentler tek batch yerine segment basina ayri translate_batch",
        "            ceviriler = self._cevir(motor, encode, decode, gonderilecek, kaynak, hedef)",
        "            ceviriler = [c for p in gonderilecek for c in self._cevir(motor, encode, decode, [p], kaynak, hedef)]",
        True,
    ),
    (
        "M-22", "K6: hata mesaji kaynak metni tasiyor (PROTOKOL 7)",
        "            raise ProviderUnavailable(f\"ceviri basarisiz: {type(e).__name__}\") from e",
        "            raise ProviderUnavailable(f\"ceviri basarisiz: {type(e).__name__} {parcalar}\") from e",
        True,
    ),
    # --- esdeger kontroller: KACMALI (yanlis pozitif yok) ---
    (
        "C-1", "close() satir sirasi degisti (esdeger)",
        "        self._motor = None\n        self._encode = None\n        self._decode = None\n        self._kapali = True",
        "        self._kapali = True\n        self._decode = None\n        self._encode = None\n        self._motor = None",
        False,
    ),
    (
        "C-2", "latency carpani 1000.0 -> 1e3 (esdeger)",
        "            latency_ms=(time.perf_counter() - t0 - kurulum_s) * 1000.0,",
        "            latency_ms=(time.perf_counter() - t0 - kurulum_s) * 1e3,",
        False,
    ),
    (
        "C-3", "modele_gider: generator yerine liste (esdeger)",
        "    return any(ch.isalnum() for ch in parca)",
        "    return any([ch.isalnum() for ch in parca])",
        False,
    ),
]


def main() -> int:
    kaynak = KAYNAK.read_text(encoding="utf-8")
    for ad, _, eski, _, _ in MUTANTLAR:
        assert kaynak.count(eski) == 1, f"{ad}: hedef parca kaynakta tam bir kez bulunmali (bulunan {kaynak.count(eski)})"

    scratch = os.environ.get("T007_AYNA") or tempfile.mkdtemp(prefix="t007-ayna-")
    ayna = Path(scratch)
    print(f"ayna: {ayna}")
    (ayna / "src").mkdir(parents=True, exist_ok=True)
    shutil.copytree(KOK / "src" / "contracts", ayna / "src" / "contracts", dirs_exist_ok=True)
    shutil.copytree(KOK / "src" / "translate", ayna / "src" / "translate", dirs_exist_ok=True)
    shutil.copytree(KOK / "tests" / "unit" / "translate", ayna / "tests" / "unit" / "translate", dirs_exist_ok=True)
    for pyc in ayna.rglob("__pycache__"):
        shutil.rmtree(pyc, ignore_errors=True)
    hedef = ayna / "src" / "translate" / "local_nmt.py"
    test = ayna / "tests" / "unit" / "translate" / "test_local_nmt.py"
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONPATH": str(ayna)}

    def kos() -> tuple[int, str]:
        r = subprocess.run(
            [sys.executable, "-m", "pytest", str(test), "-q", "-p", "no:cacheprovider", "-x", "--no-header"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(ayna), env=env, timeout=600,
        )
        son = [ln for ln in r.stdout.strip().splitlines() if ln.strip()]
        return r.returncode, (son[-1] if son else "")

    hedef.write_text(kaynak, encoding="utf-8")
    kod, ozet = kos()
    print(f"temel (mutantsiz): exit={kod}  {ozet}")
    if kod != 0:
        print("TEMEL KOSUM DUSTU -- kit anlamsiz")
        return 1

    hatalar = 0
    for ad, aciklama, eski, yeni, yakalanmali in MUTANTLAR:
        hedef.write_text(kaynak.replace(eski, yeni), encoding="utf-8")
        kod, ozet = kos()
        yakalandi = kod != 0
        if yakalanmali:
            durum = "YAKALANDI" if yakalandi else "KACTI  <-- HATA"
        else:
            durum = "KACTI (esdeger, beklenen)" if not yakalandi else "YAKALANDI <-- YANLIS POZITIF"
        if yakalandi != yakalanmali:
            hatalar += 1
        print(f"  {ad}  {durum:28s} {aciklama}")
        if yakalandi:
            print(f"        ilk dusen: {ozet[:110]}")
    hedef.write_text(kaynak, encoding="utf-8")
    print()
    if hatalar:
        print(f"MUTANT KITI: {hatalar} sorun")
        return 1
    n_m = sum(1 for m in MUTANTLAR if m[4])
    n_c = len(MUTANTLAR) - n_m
    print(f"MUTANT KITI TEMIZ: {n_m}/{n_m} mutant yakalandi, {n_c}/{n_c} esdeger kontrol kacti")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
