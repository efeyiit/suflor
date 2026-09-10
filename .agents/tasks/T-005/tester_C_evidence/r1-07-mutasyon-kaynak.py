"""MERCEK C -- kendi kapilarimi MUTASYONLA denetle (PROTOKOL §4.6/8).

Depo DOKUNULMAZ: `src/` ve `tester_C/` gecici bir koke KOPYALANIR, kopyada
tek bir mutasyon yapilir ve yalnizca tester_C testleri kosulur. Her mutasyon
en az bir testi KIRMALIDIR; kirmiyorsa o kapi bir sey olcmuyor demektir.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

DEPO = Path(r"C:\Users\pc\Desktop\efe\çeviri uygulaması")
KOK = Path(__file__).resolve().parent / "mutant"

MUTASYONLAR: dict[str, tuple[str, str, str]] = {
    # ad: (dosya, eski, yeni)
    "M1_seq_hatada_da_tuketilir": (
        "src/capture/service.py",
        "        goruntu = self._backend_dan_al(hedef)\n        self._seq += 1\n",
        "        self._seq += 1\n        goruntu = self._backend_dan_al(hedef)\n",
    ),
    "M2_refresh_once_atar_sonra_dogrular": (
        "src/capture/service.py",
        "        yeni = list_monitors(self._backend)\n        self._monitors = yeni\n",
        "        self._monitors = ()\n"
        "        yeni = list_monitors(self._backend)\n"
        "        self._monitors = yeni\n",
    ),
    "M3_refresh_seq_i_sifirlar": (
        "src/capture/service.py",
        "        yeni = list_monitors(self._backend)\n",
        "        self._seq = -1\n        yeni = list_monitors(self._backend)\n",
    ),
    "M4_c_sinifi_yeniden_denenir": (
        "src/capture/service.py",
        "                ham = self._backend.grab(hedef)\n"
        "            except Exception as exc:  # sinif (b) -- backend'in kendi hatasi\n"
        "                son_istisna = exc\n"
        "                continue\n"
        "            self._bicimi_dogrula(ham, hedef, deneme)\n"
        "            return self._kopyala(ham)\n",
        "                ham = self._backend.grab(hedef)\n"
        "                self._bicimi_dogrula(ham, hedef, deneme)\n"
        "            except Exception as exc:  # sinif (b) -- backend'in kendi hatasi\n"
        "                son_istisna = exc\n"
        "                continue\n"
        "            return self._kopyala(ham)\n",
    ),
    "M5_deneme_sayisi_5": (
        "src/capture/service.py",
        "_DENEME_SAYISI = 3\n",
        "_DENEME_SAYISI = 5\n",
    ),
    "M6_ilk_istisna_baglanir": (
        "src/capture/service.py",
        "                son_istisna = exc\n",
        "                son_istisna = son_istisna or exc\n",
    ),
    "M7_capture_full_negatif_indeks": (
        "src/capture/service.py",
        "        if not 0 <= monitor_index < len(self._monitors):\n",
        "        if not -len(self._monitors) <= monitor_index < len(self._monitors):\n",
    ),
    "M8_capture_full_len_kabul": (
        "src/capture/service.py",
        "        if not 0 <= monitor_index < len(self._monitors):\n",
        "        if not 0 <= monitor_index <= len(self._monitors):\n",
    ),
    "M9_monitor_index_cagirandan": (
        "src/capture/service.py",
        "            monitor_index=self._monitor_indeksi(aday),\n",
        "            monitor_index=duz.monitor_index,\n",
    ),
    "M10_kirpma_tek_monitore": (
        "src/capture/service.py",
        "            kirpik = dpi.intersect(duz, birlesim)\n",
        "            kirpik = dpi.intersect(duz, self._monitors[0])\n",
    ),
    "M11_mss_monitors_kapatmaz": (
        "src/capture/service.py",
        "        with mss.MSS() as oturum:\n            return [dict(ham) for ham in oturum.monitors]\n",
        "        oturum = mss.MSS()\n        return [dict(ham) for ham in oturum.monitors]\n",
    ),
    "M12_mss_grab_her_cagrida_yeni": (
        "src/capture/service.py",
        "        if self._tutamac is None:\n            self._tutamac = mss.MSS()\n",
        "        self._tutamac = mss.MSS()\n",
    ),
    "M13_mss_close_idempotent_degil": (
        "src/capture/service.py",
        "        if self._tutamac is not None:\n"
        "            self._tutamac.close()\n"
        "            self._tutamac = None\n",
        "        if self._tutamac is not None:\n            self._tutamac.close()\n",
    ),
    "M14_mss_monitors_onbellekler": (
        "src/capture/service.py",
        "        with mss.MSS() as oturum:\n"
        "            return [dict(ham) for ham in oturum.monitors]\n",
        "        onb = getattr(self, '_onb', None)\n"
        "        if onb is None:\n"
        "            with mss.MSS() as oturum:\n"
        "                onb = [dict(ham) for ham in oturum.monitors]\n"
        "            self._onb = onb\n"
        "        return onb\n",
    ),
    "M15_mss_exit_istisnayi_yutar": (
        "src/capture/service.py",
        "    def __exit__(self, *_: object) -> None:\n        self.close()\n",
        "    def __exit__(self, *_: object) -> bool:\n        self.close()\n        return True\n",
    ),
    "M16_yapim_hatasinda_bos_kume": (
        "src/capture/service.py",
        "        self._monitors: tuple[Rect, ...] = list_monitors(backend)\n",
        "        try:\n"
        "            self._monitors: tuple[Rect, ...] = list_monitors(backend)\n"
        "        except CaptureError:\n"
        "            self._monitors = ()\n",
    ),
    "M17_giris_kapisi_yok": (
        "src/capture/service.py",
        "    if isinstance(deger, bool):\n"
        "        raise CaptureError(f\"bolge alani '{ad}' tamsayi olmali, gelen: {deger!r}\")\n",
        "    if False:\n"
        "        raise CaptureError(f\"bolge alani '{ad}' tamsayi olmali, gelen: {deger!r}\")\n"
        "    try:\n"
        "        return int(deger)  # type: ignore[call-overload]\n"
        "    except Exception:\n"
        "        pass\n",
    ),
    "M18_bos_kume_denetimi_yok": (
        "src/capture/service.py",
        "        if not self._monitors:\n"
        "            raise CaptureError(\"monitor kumesi bos: yakalanacak ekran yok\")\n",
        "        if False:\n"
        "            raise CaptureError(\"monitor kumesi bos: yakalanacak ekran yok\")\n",
    ),
}


def hazirla() -> None:
    if KOK.exists():
        shutil.rmtree(KOK)
    (KOK / ".agents" / "tasks" / "T-005").mkdir(parents=True)
    shutil.copytree(DEPO / "src", KOK / "src")
    shutil.copytree(
        DEPO / ".agents" / "tasks" / "T-005" / "tester_C",
        KOK / ".agents" / "tasks" / "T-005" / "tester_C",
    )
    for p in (KOK / ".agents").rglob("__pycache__"):
        shutil.rmtree(p, ignore_errors=True)
    for p in (KOK / "src").rglob("__pycache__"):
        shutil.rmtree(p, ignore_errors=True)


def kos() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "pytest", ".agents/tasks/T-005/tester_C", "-q",
         "-p", "no:cacheprovider", "--no-header", "-x", "--tb=no"],
        cwd=str(KOK), capture_output=True, text=True, encoding="utf-8",
    )


def main() -> int:
    hazirla()
    temiz = kos()
    son = [ln for ln in temiz.stdout.strip().splitlines() if ln.strip()][-1]
    print(f"[TABAN] mutasyonsuz kopya: {son}  (exit {temiz.returncode})")
    if temiz.returncode != 0:
        print(temiz.stdout[-3000:])
        return 1

    hayatta: list[str] = []
    for ad, (dosya, eski, yeni) in MUTASYONLAR.items():
        hazirla()
        p = KOK / dosya
        s = p.read_text(encoding="utf-8")
        if eski not in s:
            print(f"  {ad:38s} ATLANDI -- desen bulunamadi")
            hayatta.append(ad + " (desen yok)")
            continue
        p.write_text(s.replace(eski, yeni, 1), encoding="utf-8")
        r = kos()
        satirlar = [ln for ln in r.stdout.strip().splitlines() if ln.strip()]
        ozet = satirlar[-1] if satirlar else "(cikti yok)"
        durum = "OLDU " if r.returncode != 0 else "HAYATTA"
        if r.returncode == 0:
            hayatta.append(ad)
        print(f"  {ad:38s} {durum} | {ozet[:90]}")
    print()
    if hayatta:
        print(f"HAYATTA KALAN MUTASYONLAR ({len(hayatta)}): {hayatta}")
        return 2
    print(f"Butun {len(MUTASYONLAR)} mutasyon en az bir kapida oldu.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
