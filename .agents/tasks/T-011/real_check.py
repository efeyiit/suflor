"""T-011 kabul kapisi v4 -- gercek NMT ile sozluk gomme.

    python .agents/tasks/T-011/real_check.py

Sefe aittir. Stdout yalniz ASCII; metin basilmaz (yalniz sayilar/boolean).
  1. G1'in 6 cumlesi: gomulu ciktida hedef 6/6; kazanc (hamda yok, gomulude var) >= 2 (pozitif kontrol)
  2. KR degirmen cumlesi: "Degirmen" var, tekrar yok; POZITIF KONTROL: hamda tekrar VAR
  3. Yer tutucu: {PLAYER} korunan aralik (+ pozitif kontrol); {0} + ad gomulu ceviride ikisi de var
  4. Unvan gri bolgesi: rapor (Elder sizmasi) + NEGATIF olcu (ham dogru -> gomulu dogru kalmali)
  5. Y-B2: JP saygi eki / KR yonelme eki ile ad gomulur; pozitif kontrol: hamda ad yok
  6. Zincir kurali: windmills 0 hit, windmill 2, ad+ad bitisik 2 (statik) + gercek modelle windmills ham==gomulu
  7. Y1 negatif: tek kodpoint sema reddi; izinle bilesikte bos, bilinen sinir dolu (rapor)
  8. 1000 segment x fixture: lookup+gom medyan < 50 ms
"""
from __future__ import annotations

import dataclasses
import json
import statistics
import sys
import tempfile
import time
from pathlib import Path

KOK = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(KOK))

from src.contracts.models import Rect, Segment, TranslationRequest  # noqa: E402

MODEL = KOK / "models" / "nllb-200-distilled-600M-ct2-int8"
SOZLUK = Path(__file__).resolve().parent / "fixtures" / "sozluk_ornek.json"
TEK_HECE = "검"   # tek hangul hecesi (kilic); #7 sema reddi -- kod noktasi tek yerden
ihlaller: list[str] = []


def ihlal(m: str) -> None:
    ihlaller.append(m); print(f"  IHLAL  {m}")


def tamam(m: str) -> None:
    print(f"  ok     {m}")


def _kat(t: str) -> str:
    """Turkce-guvenli katlama: 'I'.lower() 2 kodpoint tuzagi (Tester-B K-B4)."""
    return t.replace("İ", "i").replace("I", "ı").casefold()


def icerir(hedef: str, metin: str) -> bool:
    return _kat(hedef) in _kat(metin)


def main() -> int:
    print("T-011 real_check v4 -- sozluk gomme, gercek NMT")
    try:
        from src.translate.sozluk import GlossaryStore, terimleri_gom
    except Exception as e:  # noqa: BLE001
        ihlal(f"src.translate.sozluk import edilemedi: {type(e).__name__}: {e}"); return 1
    from src.translate.local_nmt import LocalNmtProvider
    p = LocalNmtProvider(model_dir=MODEL, threads=8)
    s = GlossaryStore(SOZLUK)

    def gecici(terimler: list[dict[str, object]], td: str, ad: str) -> GlossaryStore:
        yol = Path(td) / ad
        yol.write_text(json.dumps({"terimler": terimler}, ensure_ascii=False), encoding="utf-8")
        return GlossaryStore(yol)

    def cevir(metinler: list[str], dil: str, gom: bool, yer_tutucular: tuple[str, ...] = (),
              sozluk: GlossaryStore | None = None) -> list[str]:
        g = sozluk or s
        segs = tuple(Segment(text=t, bbox=Rect(0, i * 40, 800, 36), placeholders=yer_tutucular) for i, t in enumerate(metinler))
        if gom:
            hits = []
            for i, seg in enumerate(segs):
                for h in g.lookup(seg.text, seg.placeholders):
                    hits.append(dataclasses.replace(h, segment_index=i))
            segs = terimleri_gom(segs, tuple(hits))
        return list(p.translate(TranslationRequest(segments=segs, source_lang=dil, target_lang="tr")).translations)

    # 1 -- G1'in 6 cumlesi (fixture v3: adlar + bilinmeyen bilesikler)
    ornek = [("jpn_Jpan", "長老マルクス", "Marcus"),
             ("jpn_Jpan", "マルクスがあなたを待っています。", "Marcus"),
             ("jpn_Jpan", "水車小屋を過ぎて東の道を行きなさい。", "Değirmen"),
             ("kor_Hang", "장로 마르쿠스", "Marcus"),
             ("kor_Hang", "방앗간을 지나 동쪽 길로 가십시오.", "Değirmen"),
             ("eng_Latn", "The elder Marcus waits by the mill.", "Marcus")]
    var_gom = 0; kazanc = 0; kazanc_hangi = []
    for k, (dil, m, hedef) in enumerate(ornek):
        g = cevir([m], dil, True)[0]; h = cevir([m], dil, False)[0]
        var_gom += icerir(hedef, g)
        if icerir(hedef, g) and not icerir(hedef, h):
            kazanc += 1; kazanc_hangi.append(k)
    (tamam if var_gom == 6 else ihlal)(f"[1a] gomulu: hedef terim {var_gom}/6 ciktida")
    (tamam if kazanc >= 2 else ihlal)(f"[1b] kazanc (hamda yok, gomulude var): {kazanc}/6, cumleler {kazanc_hangi} (>= 2 pozitif kontrol)")

    # 2 -- KR degirmen: tekrar dejenerasyonu + pozitif kontrol
    kr = "방앗간을 지나 동쪽 길로 가십시오."

    def tekrar_var(t: str) -> bool:
        kel = _kat(t).replace("ğ", "g").split()
        return any(kel[i] == kel[i + 2] and kel[i + 1] == kel[i + 3] for i in range(len(kel) - 3))

    c_gom = cevir([kr], "kor_Hang", True)[0]; c_ham = cevir([kr], "kor_Hang", False)[0]
    (tamam if icerir("Değirmen", c_gom) and not tekrar_var(c_gom) else ihlal)(
        f"[2a] KR gomulu: degirmen={icerir('Değirmen', c_gom)} tekrar={tekrar_var(c_gom)}")
    (tamam if tekrar_var(c_ham) else ihlal)(f"[2b] pozitif kontrol: hamda ikili tekrar var={tekrar_var(c_ham)} (K-B2)")

    with tempfile.TemporaryDirectory() as td:
        # 3 -- yer tutucu
        g3 = gecici([{"kaynak": "PLAYER", "hedef": "Oyuncu"}], td, "oyuncu.json")
        h_yok = g3.lookup("{PLAYER}は村にいます", ("{PLAYER}",))
        h_kontrol = g3.lookup("{PLAYER}は村にいます", ())
        (tamam if not h_yok and len(h_kontrol) == 1 else ihlal)(f"[3a] {{PLAYER}} korunan aralikta: {len(h_yok)} hit; bildirilmezse {len(h_kontrol)} (kontrol)")
        h_var = s.lookup("{0}マルクス", ("{0}",))
        (tamam if any(x.target_term == "Marcus" for x in h_var) else ihlal)(f"[3b] {{0}} bitisik: Marcus hit var ({len(h_var)})")
        c3 = cevir(["{0}マルクスは村にいます。"], "jpn_Jpan", True, ("{0}",))[0]
        (tamam if "Marcus" in c3 and "{0}" in c3 else ihlal)(f"[3c] gomulu+yer tutucu ceviri: Marcus={'Marcus' in c3} {{0}}={'{0}' in c3}")

        # 4 -- unvan gri bolgesi (Y-B1 / K-B3)
        u = cevir(["장로 마르쿠스"], "kor_Hang", True)[0]
        tamam(f"[4a] RAPOR unvan+ad, adlar-yalniz sozluk: Elder sizmasi={'elder' in _kat(u)} Marcus={'Marcus' in u} (gri bolge, dusurmez)")
        b = "마을 장로가 마르쿠스를 불렀습니다."
        bg = cevir([b], "kor_Hang", True)[0]; bh = cevir([b], "kor_Hang", False)[0]
        # K-B8: "ihtiyar" mutlak sarti model surumune bagli ve kirilgan; olcu = ad var + Y-B1 hatasi ("kasaba") yok + kelime sayisi hama yakin
        oran = len(bg.split()) / max(1, len(bh.split()))
        iyi = "Marcus" in bg and "kasaba" not in _kat(bg) and 0.6 <= oran <= 1.6
        (tamam if iyi else ihlal)(f"[4b] NEGATIF: bilesik cumlede ad gomme yapiyi bozmaz: Marcus={'Marcus' in bg} kasaba={'kasaba' in _kat(bg)} kelime orani={oran:.2f} (ihtiyar rapor: gom={'ihtiyar' in _kat(bg)} ham={'ihtiyar' in _kat(bh)})")

        # 5 -- Y-B2: saygi/yonelme ekleri
        jp5 = "マルクスさんが来た。"
        kr5 = "마르쿠스에게 말했습니다."
        n_jp = len(s.lookup(jp5)); n_kr = len(s.lookup(kr5))
        (tamam if n_jp == 1 and n_kr == 1 else ihlal)(f"[5a] statik: JP -san eki {n_jp} hit, KR -ege eki {n_kr} hit (1/1 beklenir)")
        if n_jp == 1 and n_kr == 1:
            g_jp = cevir([jp5], "jpn_Jpan", True)[0]; h_jp = cevir([jp5], "jpn_Jpan", False)[0]
            g_kr = cevir([kr5], "kor_Hang", True)[0]; h_kr = cevir([kr5], "kor_Hang", False)[0]
            (tamam if "Marcus" in g_jp and "Marcus" in g_kr else ihlal)(f"[5b] gomulu: JP Marcus={'Marcus' in g_jp} KR Marcus={'Marcus' in g_kr}")
            (tamam if "Marcus" not in h_jp and "Marcus" not in h_kr else ihlal)(f"[5c] pozitif kontrol: hamda ad yok -- JP={'Marcus' not in h_jp} KR={'Marcus' not in h_kr} (ikisi de; K-B9)")

        # 6 -- zincir kurali (statik)
        g6 = gecici([{"kaynak": "wind", "hedef": "Rüzgar"}, {"kaynak": "mill", "hedef": "Değirmen"}], td, "ruzgar.json")
        n_wms = len(g6.lookup("The windmills turn.")); n_wm = len(g6.lookup("The windmill turns."))
        n_adad = len(s.lookup("マルクスアイラ"))
        (tamam if n_wms == 0 and n_wm == 2 and n_adad == 2 else ihlal)(f"[6a] zincir: windmills={n_wms} (0) windmill={n_wm} (2) ad+ad bitisik={n_adad} (2)")
        n_kanji_ad = len(s.lookup("長老マルクス")); n_kata_kata = len(s.lookup("マルクスタウン"))
        (tamam if n_kanji_ad == 1 and n_kata_kata == 0 else ihlal)(f"[6b] betik gecisi: kanji+katakana ad={n_kanji_ad} (1) katakana+katakana={n_kata_kata} (0)")
        # K-B10: zincir sinifi gercek modelle -- windmills gommesiz kalinca ham ceviri korunur (Tester-B: Ruzgarmills bozuktu)
        w_gom = cevir(["The windmills turn slowly."], "eng_Latn", True, sozluk=g6)[0]
        w_ham = cevir(["The windmills turn slowly."], "eng_Latn", False)[0]
        (tamam if w_gom == w_ham and "mills" not in w_gom else ihlal)(f"[6c] zincir gercek model: windmills gomulu==ham {w_gom == w_ham}, melez kelime yok {'mills' not in w_gom}")

        # 7 -- Y1 negatif
        try:
            gecici([{"kaynak": TEK_HECE, "hedef": "Kılıç"}], td, "kotu.json"); ihlal("[7a] tek heceli KR terim kabul edildi (ValueError bekleniyordu)")
        except ValueError as e:
            (tamam if TEK_HECE in str(e) else ihlal)(f"[7a] tek heceli KR terim reddedildi, mesajda terim var={TEK_HECE in str(e)}")
        g7 = gecici([{"kaynak": TEK_HECE, "hedef": "Kılıç", "kisa_terim_izni": True}], td, "izin.json")
        n7b = len(g7.lookup("검사가 왔습니다."))
        (tamam if n7b == 0 else ihlal)(f"[7b] izinli tek hece, bilesik icinde eslesmez: {n7b} hit")
        n7c = len(g7.lookup("검은 옷을 입었다."))
        tamam(f"[7c] bilinen sinir (siyah giysi cumlesi): {n7c} hit (rapor; ek kurali ayristiramaz)")

    # 8 -- sure
    segs = tuple(Segment(text="長老マルクスが水車小屋で待っています。", bbox=Rect(0, i, 1, 1)) for i in range(1000))
    t = []
    for _ in range(5):
        t0 = time.perf_counter()
        hits = tuple(dataclasses.replace(h, segment_index=i) for i, sg in enumerate(segs) for h in s.lookup(sg.text, sg.placeholders))
        terimleri_gom(segs, hits); t.append((time.perf_counter() - t0) * 1000)
    (tamam if statistics.median(t) < 50 else ihlal)(f"[8] 1000 segment lookup+gom medyan {statistics.median(t):.1f} ms (< 50)")
    p.close()
    print()
    if ihlaller: print(f"REAL_CHECK: {len(ihlaller)} IHLAL"); return 1
    print("REAL_CHECK: TEMIZ"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
