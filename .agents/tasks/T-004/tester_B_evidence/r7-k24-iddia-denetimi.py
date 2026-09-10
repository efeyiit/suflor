"""T7-1/K29: yeni `### K24` metninin TESTLER hakkindaki OLCULEBILIR iddialarini
ve T7-2 sondasinin KANCA HIJYENINI dogrular.

K29 "var olmayan teste atif" yasagini bir kademe ileri goturur: atif VAR olan
teste ama iddia edilen MEKANIZMA dogru mu?
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

KOK = Path(__file__).resolve()
while not (KOK / ".agents").is_dir():
    KOK = KOK.parent
for _y in (str(KOK), str(KOK / ".agents" / "tasks" / "T-004")):
    if _y not in sys.path:
        sys.path.insert(0, _y)

from src.ocr import normalizer as N  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "t7_tn", KOK / "tests" / "unit" / "ocr" / "test_normalizer.py")
assert spec and spec.loader
tm = importlib.util.module_from_spec(spec)
sys.modules["t7_tn"] = tm
spec.loader.exec_module(tm)

BIR = "test_k24_kuyruk_ile_birlesik_bbox_farkli_sonuc_verir"
IKI = "test_k24_normalize_uzerinden_kuyruk_temelli_kontrol_yanlis_mirasi_onler"

print("--- K29: atfedilen testler VAR MI ve YESIL MI ---")
for ad in (BIR, IKI):
    f = getattr(tm, ad, None)
    if f is None:
        print(f"  {ad}: YOK  <-- K29 IHLALI")
        continue
    try:
        f()
        print(f"  {ad}: VAR, YESIL")
    except AssertionError as e:
        print(f"  {ad}: VAR ama DUSTU -> {e}")

print()
print("--- IDDIA 1: birincisi `_raw_query_pair` YOLUNA hic girmez ---")
sayac = {"n": 0}
orij_rqp = N._raw_query_pair


def sayan(tail, nxt, blocks):  # type: ignore[no-untyped-def]
    sayac["n"] += 1
    return orij_rqp(tail, nxt, blocks)


N._raw_query_pair = sayan  # type: ignore[assignment]
try:
    getattr(tm, BIR)()
finally:
    N._raw_query_pair = orij_rqp  # type: ignore[assignment]
print(f"  `{BIR}` kosumunda `_raw_query_pair` cagri sayisi = {sayac['n']}"
      f"  -> iddia {'DOGRU' if sayac['n'] == 0 else 'YANLIS'}")

print()
print("--- IDDIA 2: ikincisinde kuyruk TEK bloklu (2,) ve ham ikame OZDESLIK ---")
from olcu_kiti import sorgu_kaydi  # noqa: E402

with sorgu_kaydi() as kayit:
    getattr(tm, IKI)()
miras = [s for s in kayit if s.miras]
print(f"  miras sorgusu sayisi = {len(miras)}")
for s in miras:
    print(f"    sol_sb={s.sol_sb} sag_sb={s.sag_sb}  sol_bbox={s.sol_bbox}")
tek_bloklu = [s for s in miras if len(s.sol_sb) == 1]
print(f"  sol_sb == (2,) olan sorgu var mi : "
      f"{'EVET' if any(s.sol_sb == (2,) for s in miras) else 'HAYIR'}")
print(f"  TUM miras sorgularinda sol kuyruk TEK bloklu mu: "
      f"{'EVET' if len(tek_bloklu) == len(miras) else 'HAYIR'}"
      f"  -> 'ham ikame OZDESLIKTIR' iddiasi "
      f"{'DOGRU' if len(tek_bloklu) == len(miras) else 'YANLIS'}")

print()
print("--- T7-2 KANCA HIJYENI: sonda cikista GERI ALIYOR MU ---")
from src.contracts.models import OcrPreset  # noqa: E402
oncesi = N._group_rejection_reason
bloklar = [tm.blk("Ada: " + "X" * 150, 0, 0, w=240, h=18),
           tm.blk("Y" * 150, 0, 30, w=240, h=18)]
out, mrs, prm = tm._t72_params_sondasi(bloklar, OcrPreset.DIALOGUE)
sonrasi = N._group_rejection_reason
print(f"  sonda ONCESI is SONRASI            : {oncesi is sonrasi}")
print(f"  sonda GERCEK fonksiyonu mu birakti : {sonrasi is N.__dict__['_group_rejection_reason']}")
print(f"  kit kaydi (miras) = {len(mrs)}   kendi kancasi (tum cagrilar) = {len(prm)}")
print(f"  -> kancalar KATMANLI (LIFO): kit'inki bizimkinin USTUNE binmis, "
      f"ikisi de KAYIT ALMIS: {'EVET' if mrs and prm else 'HAYIR'}")
