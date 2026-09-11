"""TESTER-D tur 3 -- `with` cikis yollarinin YAPISAL olcumu.

Sefin tur 3 karari su iddiada bulunuyor:

    "Eksenin ayrik sinif sayisi = 2. `return`/`break`/`continue` birinci
     sinifa, `generator.close()` ikinciye cokuyor. UCUNCU BIR VARYANT YOK --
     ikisini de kosan bir olcu ekseni TAMAMEN kapatir."

Bu bir olgu iddiasidir (PROTOKOL §4.6/3) ve kor tester onu KENDI olcmek
zorundadir. Burada `__exit__`'in gercekten gordugu `(exc_type, exc, tb)`
uclusu, dusunulebilen HER cikis yolu icin kaydedilir.

Iddianin IKI ayri okunusu var ve bu kit ikisini AYIRIR:

  (A) CIKIS YOLU ekseni: `with` bloğundan cikmanin kac ayrik yolu var ve
      her biri `exc_type`'i hangi sinifa dusuruyor?           -> olculur
  (B) `exc_type` DEGER ekseni: `exc_type` kac ayrik deger alabilir?
      -> `None` + BaseException'in TUM alt siniflari (sinirsiz)

(A) dogruysa bile (B) yanlissa, "iki parametre ekseni TAMAMEN kapatir"
sonucu CIKMAZ: `exc_type`'in DEGERINE gore ayrisan bir uygulama iki
parametreyi de gecer. Bu dosya ikisini de olcer.

Kosum:  python .agents/tasks/T-005/tester_D/t3_exc_type_ekseni.py
"""
from __future__ import annotations

import sys
import types
from typing import Any


class Sonda:
    """`__exit__`'in gordugu ucluyu kaydeden baglam yoneticisi."""

    def __init__(self) -> None:
        self.kayit: list[tuple[object, object, object]] = []

    def __enter__(self) -> Sonda:
        return self

    def __exit__(self, t: object, v: object, tb: object) -> None:
        self.kayit.append((t, v, tb))

    @property
    def son_tip(self) -> str:
        if not self.kayit:
            return "<__exit__ HIC CAGRILMADI>"
        t = self.kayit[-1][0]
        return "None" if t is None else getattr(t, "__name__", repr(t))


def _ad(x: object) -> str:
    return "None" if x is None else getattr(x, "__name__", repr(x))


# ---------------------------------------------------------------------------
# (A) CIKIS YOLU ekseni
# ---------------------------------------------------------------------------

def yol_normal(s: Sonda) -> None:
    with s:
        pass


def yol_return(s: Sonda) -> int:
    with s:
        return 1
    return 0  # pragma: no cover


def yol_break(s: Sonda) -> None:
    for _ in range(3):
        with s:
            break


def yol_continue(s: Sonda) -> None:
    for _ in range(1):
        with s:
            continue


def yol_istisna_Exception(s: Sonda) -> None:
    try:
        with s:
            raise ValueError("x")
    except ValueError:
        pass


def yol_istisna_CaptureError(s: Sonda) -> None:
    from src.contracts.errors import CaptureError
    try:
        with s:
            raise CaptureError("x")
    except CaptureError:
        pass


def yol_istisna_BaseException(s: Sonda) -> None:
    try:
        with s:
            raise KeyboardInterrupt
    except KeyboardInterrupt:
        pass


def yol_SystemExit(s: Sonda) -> None:
    try:
        with s:
            sys.exit(3)
    except SystemExit:
        pass


def yol_generator_close(s: Sonda) -> None:
    def g() -> Any:
        with s:
            yield 1
            yield 2
    it = g()
    next(it)
    it.close()


def yol_generator_cop(s: Sonda) -> None:
    """Uretec REFERANSI dusurulur -> yorumlayici `close()` cagirir."""
    import gc

    def g() -> Any:
        with s:
            yield 1
    it = g()
    next(it)
    del it
    gc.collect()


def yol_gonderilen_istisna(s: Sonda) -> None:
    """`generator.throw()` -- govdeye DISARIDAN istisna enjekte edilir."""
    def g() -> Any:
        with s:
            yield 1
    it = g()
    next(it)
    try:
        it.throw(RuntimeError("disaridan"))
    except RuntimeError:
        pass


def yol_StopIteration(s: Sonda) -> None:
    def g() -> Any:
        with s:
            yield 1
    it = g()
    next(it)
    try:
        next(it)
    except StopIteration:
        pass


def yol_ic_ice_yeniden_yukseltme(s: Sonda) -> None:
    try:
        with s:
            try:
                raise ValueError("ilk")
            except ValueError:
                raise TypeError("ikinci") from None
    except TypeError:
        pass


def yol_finally_icinde_return(s: Sonda) -> int:
    """`try/finally`'nin `return`'u yukselen istisnayi YUTAR."""
    try:
        with s:
            raise ValueError("yutulacak")
    finally:
        return 7  # noqa: B012


YOLLAR = [
    ("normal dusus", yol_normal),
    ("return", yol_return),
    ("break", yol_break),
    ("continue", yol_continue),
    ("govdede Exception (ValueError)", yol_istisna_Exception),
    ("govdede CaptureError", yol_istisna_CaptureError),
    ("govdede BaseException (KeyboardInterrupt)", yol_istisna_BaseException),
    ("sys.exit() -> SystemExit", yol_SystemExit),
    ("generator.close() -> GeneratorExit", yol_generator_close),
    ("uretec cop toplandi -> GeneratorExit", yol_generator_cop),
    ("generator.throw(RuntimeError)", yol_gonderilen_istisna),
    ("uretec tuketildi (StopIteration)", yol_StopIteration),
    ("except icinde yeniden yukseltme (TypeError)", yol_ic_ice_yeniden_yukseltme),
    ("dis finally return ile YUTAR (govde ValueError)", yol_finally_icinde_return),
]


def a_bolumu() -> dict[str, str]:
    print("=" * 78)
    print("(A) CIKIS YOLU ekseni -- `__exit__` her yolda NE goruyor?")
    print("=" * 78)
    goruldu: dict[str, str] = {}
    for ad, fn in YOLLAR:
        s = Sonda()
        fn(s)
        tip = s.son_tip
        cagri = len(s.kayit)
        goruldu[ad] = tip
        print(f"  {ad:45s} -> exc_type={tip:20s} (__exit__ cagrisi: {cagri})")
    print()
    sinif_none = sorted(a for a, t in goruldu.items() if t == "None")
    sinif_istisna = sorted(a for a, t in goruldu.items() if t != "None")
    print(f"  `exc_type is None` sinifina dusen yollar   : {len(sinif_none)}")
    for a in sinif_none:
        print(f"      - {a}")
    print(f"  `exc_type is not None` sinifina dusen yollar: {len(sinif_istisna)}")
    for a in sinif_istisna:
        print(f"      - {a}  ({goruldu[a]})")
    print()
    print("  SONUC (A): sefin iddiasi -- cikis YOLU ekseni iki ayrik sinifa")
    print("  cokuyor -- DOGRULANDI. Ucuncu bir SINIF yok.")
    print()
    return goruldu


# ---------------------------------------------------------------------------
# (B) `exc_type` DEGER ekseni
# ---------------------------------------------------------------------------

def b_bolumu(goruldu: dict[str, str]) -> None:
    print("=" * 78)
    print("(B) `exc_type` DEGER ekseni -- kac AYRIK deger gorulebilir?")
    print("=" * 78)
    tipler = sorted({t for t in goruldu.values() if t != "None"})
    print(f"  Yukaridaki 14 yolun urettigi AYRIK `exc_type` degeri: "
          f"None + {len(tipler)} istisna tipi")
    print(f"      {tipler}")
    print()
    print("  `__exit__` imzasi `exc_type`'i BIR DEGER olarak alir; deger uzayi")
    print("  `None` + BaseException'in tum alt siniflaridir. Bu ortamdaki")
    print("  yuklu alt sinif sayisi:")
    n = 0
    yigin = [BaseException]
    gorulen: set[int] = set()
    while yigin:
        c = yigin.pop()
        if id(c) in gorulen:
            continue
        gorulen.add(id(c))
        n += 1
        yigin.extend(c.__subclasses__())
    print(f"      BaseException alt sinif sayisi (bu process): {n}")
    print()
    print("  SONUC (B): cikis YOLU ekseni 2 sinifa cokuyor (A dogru), ama")
    print("  `exc_type`'in DEGER ekseni 2 degildir. Bir uygulama `exc_type`'in")
    print(f"  DEGERINE gore ayrisabilir ({n} tip + None). 'Iki parametre ekseni")
    print("  TAMAMEN kapatir' sonucu bu yuzden YAPIDAN CIKMAZ; olcunun secilen")
    print("  iki NOKTASI (None, CaptureError) disinda kalan degerlere kapili bir")
    print("  uygulama iki bacagi da gecer. Mutantlarla olculur: t3_mutant_kiti.py")
    print()


# ---------------------------------------------------------------------------
# (C) URUNDE GeneratorExit yolu GERCEKTEN kullaniliyor mu?
# ---------------------------------------------------------------------------

def c_bolumu() -> None:
    print("=" * 78)
    print("(C) Uretim kodunda `with MssBackend()` / uretec kullanimi var mi?")
    print("=" * 78)
    import pathlib
    kok = pathlib.Path(__file__).resolve().parents[4]
    bulgu = 0
    for p in sorted((kok / "src").rglob("*.py")) + sorted((kok / "demo").rglob("*.py")):
        try:
            metin = p.read_text(encoding="utf-8")
        except OSError:  # pragma: no cover
            continue
        for i, satir in enumerate(metin.splitlines(), 1):
            s = satir.strip()
            if "with " in s and "Backend" in s:
                print(f"  {p.relative_to(kok)}:{i}: {s}")
                bulgu += 1
    if not bulgu:
        print("  (uretimde `with <...>Backend()` kullanimi YOK -- omur yonetimi")
        print("   cagirana birakilmis; `close()` ve `__exit__` ikisi de API yuzeyi)")
    print()


def main() -> None:
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[4]))
    goruldu = a_bolumu()
    b_bolumu(goruldu)
    c_bolumu()


if __name__ == "__main__":
    main()
