"""T-011 kabul kapisi -- IMPLEMENTER'IN DUZELTILMIS KOPYASI (sefin dosyasi degismedi).

    python .agents/tasks/T-011/evidence/real_check-duzeltilmis-kopya.py

Sefin real_check.py'sinden iki fark (kapi itirazi, bkz. delivery.md):
  (1) #6a: `chr(44608)` (U+AE40) yerine gecici sozluge yazilan terimin kendisi aranir (U+AC80).
  (2) #3c: `cevir()` segmentlere `placeholders` verir; #3c `("{0}",)` ile cagrilir
      (paket K3: "real_check #3 segmentlere placeholders verir"; T-007 K5 onarimi ancak boyle devreye girer).
Gerisi birebir ayni.

Sefe aittir. Stdout yalniz ASCII; metin basilmaz (yalniz sayilar/boolean).
  1. G1'in 6 cumlesi: lookup -> gom -> translate -> hedef terim var (6/6)
  2. POZITIF KONTROL: gommeden -> en az 2'sinde hedef terim YOK
  3. KR degirmen cumlesi: "Degirmen" var, "Dogu'ya dogru Dogu'ya dogru" tekrari YOK
  4. Unvan: 장로 마르쿠스 -> "Elder" YOK, "Ihtiyar" ve "Marcus" var
  5. Cins isim raporu (dusurmez)
  6. Y1 negatif: tek heceli KR sema reddi; izinle bilesikte eslesmez
  7. 1000 segment x fixture < 50 ms
"""
from __future__ import annotations

import dataclasses
import json
import statistics
import sys
import time
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(KOK))

from src.contracts.models import Rect, Segment, TranslationRequest  # noqa: E402

MODEL = KOK / "models" / "nllb-200-distilled-600M-ct2-int8"
SOZLUK = Path(__file__).resolve().parents[1] / "fixtures" / "sozluk_ornek.json"
ihlaller: list[str] = []


def ihlal(m: str) -> None:
    ihlaller.append(m); print(f"  IHLAL  {m}")


def tamam(m: str) -> None:
    print(f"  ok     {m}")


def main() -> int:
    print("T-011 real_check (implementer duzeltilmis kopya) -- sozluk gomme, gercek NMT")
    try:
        from src.translate.sozluk import GlossaryStore, terimleri_gom
    except Exception as e:  # noqa: BLE001
        ihlal(f"src.translate.sozluk import edilemedi: {type(e).__name__}: {e}"); return 1
    from src.translate.local_nmt import LocalNmtProvider
    p = LocalNmtProvider(model_dir=MODEL, threads=8)
    s = GlossaryStore(SOZLUK)

    def cevir(metinler: list[str], dil: str, gom: bool, yer_tutucular: tuple[str, ...] = ()) -> list[str]:
        segs = tuple(Segment(text=t, bbox=Rect(0, i * 40, 800, 36), placeholders=yer_tutucular) for i, t in enumerate(metinler))
        if gom:
            hits = []
            for i, seg in enumerate(segs):
                for h in s.lookup(seg.text, seg.placeholders):
                    hits.append(dataclasses.replace(h, segment_index=i))
            segs = terimleri_gom(segs, tuple(hits))
        return list(p.translate(TranslationRequest(segments=segs, source_lang=dil, target_lang="tr")).translations)

    # 1 + 2
    ornek = [("jpn_Jpan", "長老マルクス", "Marcus"), ("jpn_Jpan", "マルクスがあなたを待っています。", "Marcus"),
             ("jpn_Jpan", "水車小屋を過ぎて東の道を行きなさい。", "Değirmen"), ("kor_Hang", "장로 마르쿠스", "Marcus"),
             ("kor_Hang", "방앗간을 지나 동쪽 길로 가십시오.", "Değirmen"), ("eng_Latn", "The elder Marcus waits by the mill.", "Değirmen")]
    var_gom = 0; yok_ham = 0
    for dil, m, hedef in ornek:
        g = cevir([m], dil, True)[0]; h = cevir([m], dil, False)[0]
        var_gom += hedef.lower() in g.lower(); yok_ham += hedef.lower() not in h.lower()
    (tamam if var_gom == 6 else ihlal)(f"[1] gomulu: hedef terim {var_gom}/6 ciktida")
    (tamam if yok_ham >= 2 else ihlal)(f"[2] pozitif kontrol: gommeden {yok_ham}/6'da hedef YOK (>= 2)")

    # 3
    c = cevir(["방앗간을 지나 동쪽 길로 가십시오."], "kor_Hang", True)[0].lower().replace("ğ", "g")
    tekrar = "dogu'ya dogru dogu'ya dogru" in c
    (tamam if "degirmen" in c and not tekrar else ihlal)(f"[3] KR: degirmen={'degirmen' in c} tekrar={tekrar}")

    # 4
    u = cevir(["장로 마르쿠스"], "kor_Hang", True)[0]
    (tamam if "Elder" not in u and "İhtiyar" in u and "Marcus" in u else ihlal)(
        f"[4] unvan: Elder={'Elder' in u} Ihtiyar={'İhtiyar' in u} Marcus={'Marcus' in u}")

    # 3 yer tutucu (Y2)
    h_yok = s.lookup("{PLAYER}は村にいます", ("{PLAYER}",))
    h_var = s.lookup("{0}マルクス", ("{0}",))
    (tamam if not any(x.source_term.lower() == "player" for x in h_yok) else ihlal)(f"[3a] {{PLAYER}} icinde terim eslesmedi: {len(h_yok)} hit")
    (tamam if any(x.target_term == "Marcus" for x in h_var) else ihlal)(f"[3b] {{0}} bitisik: Marcus hit var ({len(h_var)})")
    c3 = cevir(["{0}マルクスは村にいます。"], "jpn_Jpan", True, ("{0}",))[0]
    (tamam if "Marcus" in c3 and "{0}" in c3 else ihlal)(f"[3c] gomulu+yer tutucu ceviri: Marcus={'Marcus' in c3} {{0}}={'{0}' in c3}")

    # 6 Y1 negatif: tek heceli KR terim semada reddedilir
    import tempfile
    from src.translate.sozluk import GlossaryStore as _GS
    with tempfile.TemporaryDirectory() as td:
        kotu = Path(td) / "kotu.json"
        TEK_HECE = "검"  # U+AC80
        kotu.write_text(json.dumps({"terimler": [{"kaynak": TEK_HECE, "hedef": "Kılıç"}]}, ensure_ascii=False), encoding="utf-8")
        try:
            _GS(kotu); ihlal("[6a] tek heceli KR terim kabul edildi (ValueError bekleniyordu)")
        except ValueError as e:
            (tamam if TEK_HECE in str(e) else ihlal)(f"[6a] tek heceli KR terim reddedildi, mesajda terim var={TEK_HECE in str(e)}")
        izin = Path(td) / "izin.json"
        izin.write_text(json.dumps({"terimler": [{"kaynak": TEK_HECE, "hedef": "Kılıç", "kisa_terim_izni": True}]}, ensure_ascii=False), encoding="utf-8")
        g2 = _GS(izin)
        (tamam if not g2.lookup("검사가 왔습니다.") else ihlal)(f"[6b] izinli tek hece, bilesik icinde eslesmez: {len(g2.lookup('검사가 왔습니다.'))} hit")
        n6c = len(g2.lookup("검은 옷을 입었다."))
        tamam(f"[6c] bilinen sinir (siyah giysi cumlesi): {n6c} hit (rapor; ek kurali ayristiramaz)")

    # 5 rapor
    r = cevir(["水車小屋は古い。"], "jpn_Jpan", True)[0]
    tamam(f"[5] buyuk harf gomme raporu (Degirmen): kesme={chr(39) in r} ({len(r)} kar.)")

    # 6 sure
    segs = tuple(Segment(text="長老マルクスが水車小屋で待っています。", bbox=Rect(0, i, 1, 1)) for i in range(1000))
    t = []
    for _ in range(5):
        t0 = time.perf_counter()
        hits = tuple(dataclasses.replace(h, segment_index=i) for i, sg in enumerate(segs) for h in s.lookup(sg.text, sg.placeholders))
        terimleri_gom(segs, hits); t.append((time.perf_counter() - t0) * 1000)
    (tamam if statistics.median(t) < 50 else ihlal)(f"[7] 1000 segment lookup+gom medyan {statistics.median(t):.1f} ms (< 50)")
    p.close()
    print()
    if ihlaller: print(f"REAL_CHECK: {len(ihlaller)} IHLAL"); return 1
    print("REAL_CHECK: TEMIZ"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
