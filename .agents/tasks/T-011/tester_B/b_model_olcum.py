"""TESTER-B (T-011, mercek: kotu kullanim + sartname uyumu) -- gercek NMT ile olcumler.

    python .agents/tasks/T-011/tester_B/b_model_olcum.py

Stdout yalniz ASCII (sayilar/boolean). Ham ceviri metinleri UTF-8 dosyaya:
    .agents/tasks/T-011/tester_B_evidence/model-olcum-ham.txt

Bolumler:
  A. G1'in 6 cumlesi: ham vs gomulu; #1'in 6/6'sinin kaci GERCEKTEN gommeden geliyor
     (hedef hamda YOK ve gomuluda VAR) -- iki kosum, determinizm.
  B. Kendi 6 cumlem (JP 3, KR 3): ham vs gomulu -- gommenin BOZDUGU ceviri var mi
     (ham dogru, gomulu yanlis) -- ham metinler dosyada, karar raporda.
  C. Y3 yazarlik kurali: fixture'daki 11 terimin her biri icin tek cumle, HAM
     ceviride hedef terim var mi (varsa model zaten biliyor -> fixture Y3'u ihlal ediyor).
  D. Yalniz-terim segment (`マルクス` -> `Marcus`): modele gidiyor mu, ne cikiyor.
  E. Sinir kurali kacaklari (JP saygi eki / KR `에게`, `님`): hit yok -> ham ceviride ad korunuyor mu.
  H. Fixture terimiyle Y3 zarar sinifi: unvan (`장로/長老/elder`) bilesik icinde -- ham dogru, gomulu bozuk mu.
  F. real_check #3 pozitif kontrol: KR ham ceviride "dogu'ya dogru dogu'ya dogru" tekrari VAR mi.
  G. Sure: 1000 segment x {11, 50, 500} terim; `lookup_segments`+`gom` ve kapinin yolu; medyan.
  I. Kaynak terimde `。`: gomme cumle sinirini yutuyor -> parca sayisi ve ceviri.
"""
from __future__ import annotations

import dataclasses
import json
import statistics
import sys
import tempfile
import time
import unicodedata
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(KOK))

from src.contracts.models import Rect, Segment, TranslationRequest  # noqa: E402
from src.translate.local_nmt import LocalNmtProvider, cumlelere_bol  # noqa: E402
from src.translate.sozluk import GlossaryStore, terimleri_gom  # noqa: E402

MODEL = KOK / "models" / "nllb-200-distilled-600M-ct2-int8"
SOZLUK = KOK / ".agents" / "tasks" / "T-011" / "fixtures" / "sozluk_ornek.json"
HAM_DOSYA = KOK / ".agents" / "tasks" / "T-011" / "tester_B_evidence" / "model-olcum-ham.txt"
R = Rect(0, 0, 800, 36)

ham_out = open(HAM_DOSYA, "w", encoding="utf-8")


def h(*a: object, sep: str = " ") -> None:
    print(*a, file=ham_out, sep=sep)


def _k(m: str) -> str:
    """Karsilastirma anahtari: casefold + Turkce `İ`/`ı` katlama (`"İ".lower()` 2 kodpoint -> `in` sessizce False)."""
    return m.casefold().replace("i̇", "i").replace("ı", "i")


def say(m: str) -> None:
    print(m.encode("ascii", "replace").decode("ascii"))


def main() -> int:
    p = LocalNmtProvider(model_dir=MODEL, threads=8)
    s = GlossaryStore(SOZLUK)

    def segs(metinler: list[str], yt: tuple[str, ...] = ()) -> tuple[Segment, ...]:
        return tuple(Segment(text=t, bbox=R, placeholders=yt) for t in metinler)

    def cevir(sg: tuple[Segment, ...], dil: str, gom: bool) -> tuple[tuple[Segment, ...], list[str]]:
        if gom:
            sg = terimleri_gom(sg, s.lookup_segments(sg))
        return sg, list(p.translate(TranslationRequest(segments=sg, source_lang=dil, target_lang="tr")).translations)

    # ---------------- A ----------------
    say("== A. G1 6 cumle: ham vs gomulu, gomme katkisi ==")
    h("== A ==")
    ornek = [("jpn_Jpan", "長老マルクス", "Marcus"), ("jpn_Jpan", "マルクスがあなたを待っています。", "Marcus"),
             ("jpn_Jpan", "水車小屋を過ぎて東の道を行きなさい。", "Değirmen"), ("kor_Hang", "장로 마르쿠스", "Marcus"),
             ("kor_Hang", "방앗간을 지나 동쪽 길로 가십시오.", "Değirmen"), ("eng_Latn", "The elder Marcus waits by the mill.", "Değirmen")]
    katki = 0; var_gom = 0; yok_ham = 0; det = 0
    for i, (dil, m, hedef) in enumerate(ornek):
        _, ham = cevir(segs([m]), dil, False)
        gs, gom = cevir(segs([m]), dil, True)
        _, gom2 = cevir(segs([m]), dil, True)
        det += gom == gom2
        hv = _k(hedef) in _k(ham[0]); gv = _k(hedef) in _k(gom[0])
        var_gom += gv; yok_ham += not hv; katki += (gv and not hv)
        h(f"[A{i}] {dil} kaynak={m!r}\n      gomulu_kaynak={gs[0].text!r}\n      ham={ham[0]!r}\n      gom={gom[0]!r}\n      hedef_hamda={hv} hedef_gomuluda={gv}")
        say(f"  A{i} {dil}: hedef hamda={hv} gomuluda={gv} katki={gv and not hv}")
    say(f"  [A] #1 sayaci {var_gom}/6, #2 sayaci {yok_ham}/6, GERCEK gomme katkisi {katki}/6, deterministik {det}/6")

    # ---------------- B ----------------
    say("== B. kendi 6 cumlem: ham vs gomulu (bozulma aranir) ==")
    h("== B ==")
    benim = [("jpn_Jpan", "マルクスはアイラと水車小屋へ行った。"),
             ("jpn_Jpan", "アイラが長老に手紙を渡した。"),
             ("jpn_Jpan", "水車小屋の長老がマルクスを呼んだ。"),
             ("kor_Hang", "장로가 마르쿠스를 불렀습니다."),
             ("kor_Hang", "마르쿠스는 방앗간에서 아일라를 만났습니다."),
             ("kor_Hang", "아일라가 장로에게 편지를 건넸습니다.")]
    for i, (dil, m) in enumerate(benim):
        _, ham = cevir(segs([m]), dil, False)
        gs, gom = cevir(segs([m]), dil, True)
        hits = s.lookup(m)
        hedefler = sorted({x.target_term for x in hits})
        hedef_gom = [t for t in hedefler if _k(t) in _k(gom[0])]
        hedef_ham = [t for t in hedefler if _k(t) in _k(ham[0])]
        ingilizce = sum(w.lower() in {"elder", "the", "mill", "and", "to", "letter", "called", "met", "went", "with", "at", "of", "gave", "handed"} for w in gom[0].replace(".", " ").split())
        h(f"[B{i}] {dil} kaynak={m!r}\n      gomulu_kaynak={gs[0].text!r}\n      ham={ham[0]!r}\n      gom={gom[0]!r}\n      hits={len(hits)} hedefler={hedefler} hamda={hedef_ham} gomuluda={hedef_gom} ingilizce_kelime={ingilizce}")
        say(f"  B{i} {dil}: hit={len(hits)} hedef {len(hedef_gom)}/{len(hedefler)} gomuluda, {len(hedef_ham)}/{len(hedefler)} hamda, EN kelime={ingilizce}, uzunluk ham={len(ham[0])} gom={len(gom[0])}")

    # ---------------- C ----------------
    say("== C. Y3: 11 terim, ham ceviride hedef var mi (varsa model biliyor) ==")
    h("== C ==")
    y3 = [("jpn_Jpan", "マルクス", "マルクスが来た。"), ("kor_Hang", "마르쿠스", "마르쿠스가 왔습니다."), ("eng_Latn", "Marcus", "Marcus came."),
          ("jpn_Jpan", "アイラ", "アイラが来た。"), ("kor_Hang", "아일라", "아일라가 왔습니다."),
          ("jpn_Jpan", "水車小屋", "水車小屋は古い。"), ("kor_Hang", "방앗간", "방앗간은 오래되었습니다."), ("eng_Latn", "mill", "The mill is old."),
          ("jpn_Jpan", "長老", "長老が来た。"), ("kor_Hang", "장로", "장로가 왔습니다."), ("eng_Latn", "elder", "The elder came.")]
    biliyor = 0
    for i, (dil, kaynak, m) in enumerate(y3):
        hedef = next(t.hedef for t in s.terimler if t.kaynak == kaynak)
        _, ham = cevir(segs([m]), dil, False)
        _, gom = cevir(segs([m]), dil, True)
        hv = _k(hedef) in _k(ham[0])
        biliyor += hv
        h(f"[C{i}] {dil} terim={kaynak!r}->{hedef!r} kaynak={m!r}\n      ham={ham[0]!r}\n      gom={gom[0]!r}\n      hedef_hamda={hv}")
        say(f"  C{i} {dil} terim#{i}: hedef hamda={hv} (True = model zaten biliyor, Y3 ihlali) gomuluda={_k(hedef) in _k(gom[0])}")
    say(f"  [C] 11 terimin {biliyor}'inde ham ceviri hedefi zaten iceriyor")

    # ---------------- D ----------------
    say("== D. yalniz-terim segment ==")
    h("== D ==")
    tek = [("jpn_Jpan", "マルクス"), ("jpn_Jpan", "水車小屋"), ("jpn_Jpan", "長老マルクス"), ("kor_Hang", "장로"), ("eng_Latn", "mill"), ("jpn_Jpan", "アイラ")]
    for i, (dil, m) in enumerate(tek):
        _, ham = cevir(segs([m]), dil, False)
        gs, gom = cevir(segs([m]), dil, True)
        aynen = gom[0].strip().rstrip(".") == gs[0].text
        h(f"[D{i}] {dil} kaynak={m!r} gomulu_kaynak={gs[0].text!r}\n      ham={ham[0]!r}\n      gom={gom[0]!r}\n      gomulu_metin_aynen_cikti={aynen}")
        say(f"  D{i} {dil}: gomulu kaynak uzunluk={len(gs[0].text)} cikti uzunluk={len(gom[0])} aynen={aynen}")

    # ---------------- E ----------------
    say("== E. sinir kacagi sinifi (saygi eki / KR ek disi): hit yok -> ham ceviride ad? ==")
    h("== E ==")
    kacak = [("jpn_Jpan", "マルクスさんが来た。", "Marcus"), ("jpn_Jpan", "マルクス様は水車小屋にいます。", "Marcus"),
             ("kor_Hang", "마르쿠스에게 말했습니다.", "Marcus"), ("kor_Hang", "장로님이 오셨습니다.", "İhtiyar"),
             ("kor_Hang", "마르쿠스님, 안녕하세요.", "Marcus"), ("jpn_Jpan", "マルクスたちは東へ行った。", "Marcus")]
    kayip = 0
    for i, (dil, m, hedef) in enumerate(kacak):
        hits = s.lookup(m)
        _, ham = cevir(segs([m]), dil, False)
        gs, gom = cevir(segs([m]), dil, True)
        hv = _k(hedef) in _k(gom[0])
        kayip += not hv
        h(f"[E{i}] {dil} kaynak={m!r} hits={len(hits)} gomulu_kaynak={gs[0].text!r}\n      ham={ham[0]!r}\n      gom={gom[0]!r}\n      hedef_ciktida={hv}")
        say(f"  E{i} {dil}: hit={len(hits)} hedef ciktida={hv}")
    say(f"  [E] 6 cumlenin {kayip}'inde hedef terim ciktida YOK (sinir kurali eslemedi)")

    # ---------------- F ----------------
    say("== F. real_check #3 pozitif kontrol: KR hamda tekrar var mi ==")
    _, ham = cevir(segs(["방앗간을 지나 동콍 길로 가십시오."]), "kor_Hang", False)
    _, ham2 = cevir(segs(["방앗간을 지나 동쪽 길로 가십시오."]), "kor_Hang", False)
    c = ham2[0].lower().replace("ğ", "g")
    h(f"[F] ham={ham2[0]!r} tekrar={'dogu' + chr(39) + 'ya dogru dogu' + chr(39) + 'ya dogru' in c}")
    say(f"  [F] hamda 'dogu'ya dogru dogu'ya dogru' tekrari: {('dogu' + chr(39) + 'ya dogru dogu' + chr(39) + 'ya dogru') in c}")

    # ---------------- H ----------------
    say("== H. fixture terimiyle Y3 zarar sinifi: unvan bilesik icinde (ham dogru mu, gomulu bozuk mu) ==")
    h("== H ==")
    bilesik = [("kor_Hang", "마을 장로가 왔습니다.", "İhtiyar"), ("kor_Hang", "마을 장로가 마르쿠스를 불렀습니다.", "İhtiyar"),
               ("kor_Hang", "장로 회의가 열렸습니다.", "İhtiyar"), ("kor_Hang", "장로의 집은 방앗간 옆입니다.", "İhtiyar"),
               ("jpn_Jpan", "村の長老が来た。", "İhtiyar"), ("jpn_Jpan", "長老の家は水車小屋の隣です。", "İhtiyar"),
               ("eng_Latn", "The village elder came.", "İhtiyar"), ("eng_Latn", "The elder council met at the mill.", "İhtiyar")]
    for i, (dil, m, hedef) in enumerate(bilesik):
        _, ham = cevir(segs([m]), dil, False)
        gs, gom = cevir(segs([m]), dil, True)
        hv = _k(hedef) in _k(ham[0]); gv = _k(hedef) in _k(gom[0])
        h(f"[H{i}] {dil} kaynak={m!r}", f"      gomulu_kaynak={gs[0].text!r}", f"      ham={ham[0]!r}",
          f"      gom={gom[0]!r}", f"      hedef_hamda={hv} hedef_gomuluda={gv}", sep="\n")
        say(f"  H{i} {dil}: hit={len(s.lookup(m))} hedef hamda={hv} gomuluda={gv} uzunluk ham={len(ham[0])} gom={len(gom[0])}")

    # ---------------- I ----------------
    say("== I. kaynak terimde terminator: cumle siniri yutulur ==")
    with tempfile.TemporaryDirectory() as td:
        pj = Path(td) / "n.json"
        pj.write_text(json.dumps({"terimler": [{"kaynak": "マルクス。", "hedef": "Marcus"}]}, ensure_ascii=False), encoding="utf-8")
        s2 = GlossaryStore(pj)
        m = "彼はマルクス。 行こう。"
        sg = segs([m])
        gs = terimleri_gom(sg, s2.lookup_segments(sg))
        ham = list(p.translate(TranslationRequest(segments=sg, source_lang="jpn_Jpan", target_lang="tr")).translations)
        gom = list(p.translate(TranslationRequest(segments=gs, source_lang="jpn_Jpan", target_lang="tr")).translations)
        h(f"[I] kaynak={m!r} gomulu={gs[0].text!r}\n    ham={ham[0]!r}\n    gom={gom[0]!r}")
        say(f"  [I] sema kabul etti; parca sayisi ham={len(cumlelere_bol(m))} gomulu={len(cumlelere_bol(gs[0].text))}; ceviri uzunluk ham={len(ham[0])} gom={len(gom[0])}")

    p.close()

    # ---------------- G ----------------
    say("== G. sure (modelsiz): 1000 segment x N terim ==")
    metin = "長老マルクスが水車小屋で待っています。"
    sg1000 = tuple(Segment(text=metin, bbox=Rect(0, i, 1, 1)) for i in range(1000))
    with tempfile.TemporaryDirectory() as td:
        for n in (11, 50, 500):
            terimler = [dict(kaynak=t.kaynak, hedef=t.hedef) for t in s.terimler]
            k = 0
            while len(terimler) < n:
                terimler.append({"kaynak": f"terim{k:04d}x", "hedef": f"Hedef{k:04d}"}); k += 1
            pj = Path(td) / f"n{n}.json"
            pj.write_text(json.dumps({"terimler": terimler}, ensure_ascii=False), encoding="utf-8")
            sN = GlossaryStore(pj)
            t_a: list[float] = []; t_b: list[float] = []
            for _ in range(7):
                t0 = time.perf_counter(); terimleri_gom(sg1000, sN.lookup_segments(sg1000)); t_a.append((time.perf_counter() - t0) * 1000)
                t0 = time.perf_counter()
                hits = tuple(dataclasses.replace(x, segment_index=i) for i, g in enumerate(sg1000) for x in sN.lookup(g.text, g.placeholders))
                terimleri_gom(sg1000, hits); t_b.append((time.perf_counter() - t0) * 1000)
            say(f"  G n={n}: lookup_segments+gom medyan {statistics.median(t_a):.1f} ms (min {min(t_a):.1f}); kapi yolu medyan {statistics.median(t_b):.1f} ms (min {min(t_b):.1f})")
    ham_out.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
