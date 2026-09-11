"""TESTER-B tur 2 / B2-2 -- "pozitif kontrol gercek mi?" AST cagri grafigi.

Soru: `test_k7_pozitif_kontrol_kanal_olcusu_atesliyor` 7 sahte motorda dusuyor;
gercek motor (`RapidOcrEngine`) `test_k7_soguk_*` / `test_k7_sicak_*`te geciyor.
Bu "olcu atesliyor" kaniti mi, yoksa sahteler FARKLI bir olcu yolundan mi
geciyor? AST ile olculur:

  1. `_k7_kanal_olcusu` adinda KAC tanim var (1 olmali; ikinci tanim = ayri yol).
  2. Onu KIM cagiriyor, ilk argumana NE veriyor (gercek motor / sahte / FakeOcrEngine).
  3. Olcu fonksiyonunun govdesinde `m`nin tipine bakan bir dal var mi
     (`isinstance(m, ...)`, `type(m)`, `RapidOcrEngine` adi) -- olsaydi sahte ve
     gercek ayni fonksiyondan gecse bile farkli yoldan gecebilirdi.
  4. Govdedeki her `assert` satiri (hangi kanal hangi mesajla).

Calisma zamani kaniti ayri: `r2_izleme_plugin.py` (ayni kod nesnesi, ayni cagri).

Kosum: python .agents/tasks/T-006/tester_B/r2_b2_2_cagri_grafigi.py
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

DEPO = Path(__file__).resolve().parents[4]
TEST = DEPO / "tests" / "unit" / "ocr" / "test_rapid_engine.py"
OLCU = "_k7_kanal_olcusu"


def _ilk_arg_ozeti(cagri: ast.Call) -> str:
    if not cagri.args:
        return "(argumansiz)"
    return ast.unparse(cagri.args[0])


def main() -> int:
    agac = ast.parse(TEST.read_text(encoding="utf-8"))
    print(f"dosya: {TEST.relative_to(DEPO)}")
    print()

    # 1 -- tanim sayisi
    tanimlar = [d for d in ast.walk(agac) if isinstance(d, ast.FunctionDef) and d.name == OLCU]
    print(f"[1] `{OLCU}` tanim sayisi: {len(tanimlar)}  (satir: {[d.lineno for d in tanimlar]})")
    hata = len(tanimlar) != 1

    # 2 -- cagiranlar
    print(f"[2] `{OLCU}` cagiranlar (fonksiyon -> ilk arguman):")
    cagiranlar: list[tuple[str, str, int]] = []
    for fn in ast.walk(agac):
        if not isinstance(fn, ast.FunctionDef):
            continue
        for d in ast.walk(fn):
            if isinstance(d, ast.Call) and isinstance(d.func, ast.Name) and d.func.id == OLCU:
                cagiranlar.append((fn.name, _ilk_arg_ozeti(d), d.lineno))
    for ad, arg, ln in cagiranlar:
        print(f"    {ad:58s} <- {arg:45s} (satir {ln})")
    adlar = {c[0] for c in cagiranlar}
    beklenen = {
        "test_k7_soguk_motor_hicbir_kanala_metin_yazmaz",
        "test_k7_sicak_motor_kutuphane_logger_i_acikken_metin_yazmaz",
        "test_k7_pozitif_kontrol_kanal_olcusu_atesliyor",
        "test_k7_negatif_kontrol_sessiz_sahte_motor_olcuden_gecer",
    }
    eksik = beklenen - adlar
    print(f"    beklenen dort cagiran mevcut mu: {'EVET' if not eksik else 'HAYIR, eksik: ' + ', '.join(sorted(eksik))}")
    hata = hata or bool(eksik)

    # sahte motorlarin gercekten OcrEngine altsinifi oldugu ve `recognize` tanimladigi
    print("[2b] pozitif kontrol sahteleri (OcrEngine altsinifi, recognize tanimli):")
    for s in ast.walk(agac):
        if isinstance(s, ast.ClassDef) and any(ast.unparse(b) == "OcrEngine" for b in s.bases):
            metotlar = [m.name for m in s.body if isinstance(m, ast.FunctionDef)]
            print(f"    {s.name:28s} bases={[ast.unparse(b) for b in s.bases]} metotlar={metotlar}")

    # 3 -- olcu govdesinde tip dali var mi
    if tanimlar:
        govde = tanimlar[0]
        tip_dallari = []
        for d in ast.walk(govde):
            kaynak = ast.unparse(d) if isinstance(d, (ast.Call, ast.Compare, ast.Name)) else ""
            if any(k in kaynak for k in ("isinstance(", "type(m)", "RapidOcrEngine", "SahteFabrika", "_fabrika", "_taniyici")):
                tip_dallari.append((d.lineno, kaynak[:80]))
        tekil = sorted(set(tip_dallari))
        print(f"[3] olcu govdesinde motor tipine/ic durumuna bakan ifade: {len(tekil)}")
        for ln, k in tekil:
            print(f"    satir {ln}: {k}")
        hata = hata or bool(tekil)

        # `m` uzerinde yapilan TEK sey `.recognize(...)` mi?
        m_kullanimlari = sorted({ast.unparse(d) for d in ast.walk(govde)
                                 if isinstance(d, ast.Attribute) and isinstance(d.value, ast.Name) and d.value.id == "m"})
        print(f"[3b] `m` uzerindeki oznitelik erisimleri: {m_kullanimlari}")
        hata = hata or m_kullanimlari != ["m.recognize"]

        # 4 -- assert satirlari
        print("[4] olcu govdesindeki assert'ler:")
        for d in ast.walk(govde):
            if isinstance(d, ast.Assert):
                print(f"    satir {d.lineno}: {ast.unparse(d)[:110]}")

    print()
    print("SONUC:", "TEK olcu fonksiyonu, dort cagiran, tip dali YOK, m yalniz .recognize -> sahte ve gercek AYNI yoldan gecer"
          if not hata else "*** SAPMA VAR -- yukariya bak ***")
    return 1 if hata else 0


if __name__ == "__main__":
    sys.exit(main())
