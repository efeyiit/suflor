"""ŞEFE AİT — T-004 ölçü kitinin (`olcu_kiti.py`) içe aktarılabilmesi için.

İmplementer ve üç tester `from olcu_kiti import ...` yazar. Kit
`.agents/tasks/T-004/` altında ve şefe aittir; hiçbir görevin `owns`
kapsamında değildir. Bu dosya da şefe aittir — **dokunma**.

Neden gerekli: depoda `pytest.ini`/`pyproject.toml` yok ve `tests/unit/ocr`
bir paket değil, bu yüzden kitin dizini `sys.path`'e kendiliğinden girmiyor
(ölçüldü: `ModuleNotFoundError: No module named 'olcu_kiti'`). Test dosyası
içine `sys.path.insert` yazmak çalışır ama toplama sırasına bağlıdır: tester
dizini tek başına koşulduğunda patlar, birlikte koşulduğunda çalışır.
"""
from __future__ import annotations

import sys
from pathlib import Path

_KOK = Path(__file__).resolve()
while _KOK.name and not (_KOK / ".agents").is_dir():
    _KOK = _KOK.parent
_KIT = _KOK / ".agents" / "tasks" / "T-004"
for _yol in (str(_KOK), str(_KIT)):
    if _yol not in sys.path:
        sys.path.insert(0, _yol)


# ---------------------------------------------------------------------------
# T-006 K1 bariyeri — ŞEFE AİT, modül düzeyinde (fixture'da DEĞİL).
#
# Neden modül düzeyi: oturum fixture'ı toplama SONRASI kurulur ve test
# modülünün en üstündeki `import rapidocr`'u göremez (T-006 KRT-1 Y7, pytest
# sandığında ölçüldü). Bu bloğun çalışması `conftest` yüklenirken olur, yani
# bu dizindeki hiçbir test modülü toplanmadan önce.
#
# Ne yapar: `rapidocr*` ve `onnxruntime*` için import girişimini `RuntimeError`
# ile KESER. Birim testleri gerçek modeli hiç yükleyemez; gerçek davranış yalnız
# `.agents/tasks/T-006/real_check.py`'de (ayrı süreç) ölçülür.
#
# Pozitif kontrol (§4.6/10): `tests/unit/ocr/test_conftest_bariyer.py` bu
# bariyerin gerçekten ateşlediğini doğrular. Bariyer sessizce boşalırsa o test
# düşer.
# ---------------------------------------------------------------------------
import importlib.abc as _abc
import importlib.machinery as _mach

_YASAK_KOKLER: tuple[str, ...] = ("rapidocr", "onnxruntime")


class _T006Bariyer(_abc.MetaPathFinder):
    """`rapidocr`/`onnxruntime` import'unu test sürecinde keser."""

    def find_spec(
        self,
        fullname: str,
        path: object = None,
        target: object = None,
    ) -> _mach.ModuleSpec | None:
        kok = fullname.split(".", 1)[0]
        if kok in _YASAK_KOKLER:
            raise RuntimeError(
                f"T-006 K1 bariyeri: birim testleri {fullname!r} import edemez; "
                "gerçek model yalnız .agents/tasks/T-006/real_check.py ile ölçülür"
            )
        return None


if not any(isinstance(_f, _T006Bariyer) for _f in sys.meta_path):
    sys.meta_path.insert(0, _T006Bariyer())
