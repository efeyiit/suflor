"""T-011 kapi itirazi olcumu (implementer) -- real_check #3c ve #6a.

    python .agents/tasks/T-011/evidence/kapi-itirazi-3c-6a.py

Stdout yalniz ASCII; metin basilmaz (sayilar, boolean, kod noktalari).

#6a: kapi `chr(44608)` (U+AE40) ariyor; fixture'daki terim U+AC80. Iki kod
     noktasi farkli hecelerdir. Hata mesajinda GERCEK terim var mi olculur.
#3c: kapinin `cevir()`i segmente `placeholders` VERMIYOR (`Segment(text=t,
     bbox=...)`); `{0}` duz metindir, T-007 K5 onarimi devreye giremez, model
     JP'de yer tutucuyu dusurur (T-007 C9). Uc kol: (a) ham, yer tutucusuz;
     (b) gomulu, yer tutucusuz (kapinin yolu); (c) gomulu, `placeholders=("{0}",)`
     (paket K3 "real_check #3 segmentlere placeholders verir").
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(KOK))

from src.contracts.models import Rect, Segment, TranslationRequest  # noqa: E402
from src.translate.local_nmt import LocalNmtProvider  # noqa: E402
from src.translate.sozluk import GlossaryStore, terimleri_gom  # noqa: E402

MODEL = KOK / "models" / "nllb-200-distilled-600M-ct2-int8"
SOZLUK = KOK / ".agents" / "tasks" / "T-011" / "fixtures" / "sozluk_ornek.json"


def main() -> int:
    print("T-011 kapi itirazi olcumu")
    # --- #6a
    kaynak_dosyasi = (KOK / ".agents" / "tasks" / "T-011" / "real_check.py").read_text(encoding="utf-8")
    i = kaynak_dosyasi.index('"kaynak": "') + len('"kaynak": "')
    fixture_terimi = kaynak_dosyasi[i]
    print(f"[6a] kapinin aradigi kod noktasi: U+{44608:04X} (chr(44608))")
    print(f"[6a] real_check gecici sozlugundeki terimin kod noktasi: U+{ord(fixture_terimi):04X} (uzunluk {len(fixture_terimi)})")
    print(f"[6a] ikisi ayni mi: {ord(fixture_terimi) == 44608}")
    with tempfile.TemporaryDirectory() as td:
        kotu = Path(td) / "kotu.json"
        kotu.write_text(json.dumps({"terimler": [{"kaynak": fixture_terimi, "hedef": "X"}]}, ensure_ascii=False), encoding="utf-8")
        try:
            GlossaryStore(kotu)
            print("[6a] HATA: kabul edildi")
        except ValueError as e:
            print(f"[6a] ValueError; mesajda GERCEK terim (U+{ord(fixture_terimi):04X}) var: {fixture_terimi in str(e)}; "
                  f"mesajda chr(44608) var: {chr(44608) in str(e)}")

    # --- #3c
    p = LocalNmtProvider(model_dir=MODEL, threads=8)
    s = GlossaryStore(SOZLUK)
    metin = "{0}" + "マルクスは村にいます。"  # kapinin #3c cumlesi

    def cevir(seg: Segment, gom: bool) -> str:
        segs = (seg,)
        if gom:
            segs = terimleri_gom(segs, s.lookup_segments(segs))
        return p.translate(TranslationRequest(segments=segs, source_lang="jpn_Jpan", target_lang="tr")).translations[0]

    a = cevir(Segment(text=metin, bbox=Rect(0, 0, 800, 36)), gom=False)
    b = cevir(Segment(text=metin, bbox=Rect(0, 0, 800, 36)), gom=True)
    c = cevir(Segment(text=metin, bbox=Rect(0, 0, 800, 36), placeholders=("{0}",)), gom=True)
    gomulu_kaynak = terimleri_gom((Segment(text=metin, bbox=Rect(0, 0, 800, 36), placeholders=("{0}",)),),
                                  s.lookup_segments((Segment(text=metin, bbox=Rect(0, 0, 800, 36), placeholders=("{0}",)),)))[0].text
    print(f"[3c] gomulu KAYNAK metinde {{0}} sayisi: {gomulu_kaynak.count('{0}')}; Marcus var: {'Marcus' in gomulu_kaynak}")
    print(f"[3c-a] HAM, placeholders=():        Marcus={'Marcus' in a} {{0}}={'{0}' in a}  (yer tutucu dususu modelin, gommeden bagimsiz)")
    print(f"[3c-b] GOMULU, placeholders=():     Marcus={'Marcus' in b} {{0}}={'{0}' in b}  (kapinin cevir() yolu)")
    print(f"[3c-c] GOMULU, placeholders=('{{0}}',): Marcus={'Marcus' in c} {{0}}={'{0}' in c}  (paket K3'un dedigi yol)")
    p.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
