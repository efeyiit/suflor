"""T-007 implementer on olcumu 3 -- close() gercek modeli bellekten BIRAKIYOR mu (ayri surec).

Windows: psutil yok; `GetProcessMemoryInfo` (ctypes) ile WorkingSetSize okunur.
Stdout ASCII; ceviri metni basilmaz.
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import gc
import json
import sys
import weakref
from pathlib import Path

KOK = Path(r"C:\Users\pc\Desktop\efe\çeviri uygulaması")
sys.path.insert(0, str(KOK))
MODEL = KOK / "models" / "nllb-200-distilled-600M-ct2-int8"
FX = json.loads((KOK / ".agents/tasks/T-007/fixtures/cumleler.json").read_text(encoding="utf-8"))

from src.contracts.errors import ProviderUnavailable  # noqa: E402
from src.contracts.models import Rect, Segment, TranslationRequest  # noqa: E402
from src.translate.local_nmt import LocalNmtProvider, _varsayilan_fabrika  # noqa: E402


class PMC(ctypes.Structure):
    _fields_ = [
        ("cb", wt.DWORD), ("PageFaultCount", wt.DWORD), ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t), ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t), ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t), ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]


_k32 = ctypes.WinDLL("kernel32", use_last_error=True)
_psapi = ctypes.WinDLL("psapi", use_last_error=True)
_k32.GetCurrentProcess.restype = wt.HANDLE
_psapi.GetProcessMemoryInfo.argtypes = [wt.HANDLE, ctypes.POINTER(PMC), wt.DWORD]
_psapi.GetProcessMemoryInfo.restype = wt.BOOL


def rss_mb() -> float:
    pmc = PMC()
    pmc.cb = ctypes.sizeof(PMC)
    ok = _psapi.GetProcessMemoryInfo(_k32.GetCurrentProcess(), ctypes.byref(pmc), pmc.cb)
    assert ok, ctypes.get_last_error()
    return pmc.WorkingSetSize / 1e6


zayif: list[weakref.ref[object]] = []


def kaydeden_fabrika(model_dir: Path, params: dict[str, object]) -> tuple[object, object, object]:
    motor, enc, dec = _varsayilan_fabrika(model_dir, params)
    zayif.extend([weakref.ref(motor), weakref.ref(enc), weakref.ref(dec)])
    return motor, enc, dec  # type: ignore[return-value]


rq = TranslationRequest(segments=tuple(Segment(text=t, bbox=Rect(0, 0, 1, 1)) for t in FX["JP"]), source_lang="jpn_Jpan", target_lang="tr")
m0 = rss_mb()
p = LocalNmtProvider(model_dir=MODEL, threads=8, motor_fabrikasi=kaydeden_fabrika)  # type: ignore[arg-type]
m1 = rss_mb()
p.translate(rq)
m2 = rss_mb()
gc.collect()
print(f"[G] yapim: +{m1 - m0:.0f} MB (0 olmali, tembel); ilk translate: +{m2 - m1:.0f} MB (model yuklendi)")
print(f"[G] close() ONCESI weakref canli: {[z() is not None for z in zayif]}")
p.close()
gc.collect()
m3 = rss_mb()
print(f"[G] close() SONRASI weakref canli: {[z() is not None for z in zayif]} (hepsi False olmali)")
print(f"[G] close() sonrasi bellek: {m2:.0f} -> {m3:.0f} MB (-{m2 - m3:.0f} MB; model ~623 MB)")
try:
    p.translate(rq)
    print("[G] close() sonrasi translate -> hata YOK (beklenmiyordu)")
except ProviderUnavailable:
    print("[G] close() sonrasi translate -> ProviderUnavailable")
print("OLCUM-3 BITTI")
