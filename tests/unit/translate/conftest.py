"""ŞEFE AİT — T-007 K1 bariyeri, modül düzeyinde (fixture'da DEĞİL).

Test sürecinde `ctranslate2*` ve `sentencepiece*` import girişimi `RuntimeError`
ile kesilir: birim testleri modeli hiç yükleyemez; gerçek davranış yalnız
`.agents/tasks/T-007/real_check.py`'de (ayrı süreç) ölçülür.

Neden modül düzeyi: oturum fixture'ı toplama SONRASI kurulur ve test modülünün
en üstündeki import'u göremez (T-006 KRT-1 Y7, pytest sandığında ölçüldü).
Pozitif kontrol: `test_conftest_bariyer.py`. **Dokunma.**
"""
from __future__ import annotations

import importlib.abc as _abc
import importlib.machinery as _mach
import sys

_YASAK_KOKLER: tuple[str, ...] = ("ctranslate2", "sentencepiece")


class _T007Bariyer(_abc.MetaPathFinder):
    def find_spec(self, fullname: str, path: object = None, target: object = None) -> _mach.ModuleSpec | None:
        if fullname.split(".", 1)[0] in _YASAK_KOKLER:
            raise RuntimeError(
                f"T-007 K1 bariyeri: birim testleri {fullname!r} import edemez; "
                "gerçek model yalnız .agents/tasks/T-007/real_check.py ile ölçülür"
            )
        return None


if not any(isinstance(_f, _T007Bariyer) for _f in sys.meta_path):
    sys.meta_path.insert(0, _T007Bariyer())
