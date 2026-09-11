import sys, dataclasses, json
from pathlib import Path as _P
KOK = _P(__file__).resolve().parents[4]
sys.path.insert(0, str(KOK))
from pathlib import Path
from src.contracts.models import Segment, Rect, TermHit
from src.contracts.errors import ContractViolation
from src.translate.sozluk import GlossaryStore, terimleri_gom
out = open(str(KOK / ".agents" / "tasks" / "T-011" / "tester_B_evidence" / "sonda1-statik.txt"), "w", encoding="utf-8")
def p(*a):
    print(*a, file=out)
s = GlossaryStore(Path(str(KOK / ".agents" / "tasks" / "T-011" / "fixtures" / "sozluk_ornek.json")))
R = Rect(0,0,1,1)
# 1. lookup -> gom without segment_index fill
seg = Segment(text="長老マルクスが水車小屋で待っています。", bbox=R)
hits = s.lookup(seg.text)
p("hits:", hits)
try:
    terimleri_gom((seg,), hits)
except ContractViolation as e:
    p("CV:", e)
# 2. same Segment object twice
hits2 = s.lookup_segments((seg, seg))
p("dup seg hits:", [(h.segment_index, h.start, h.end, h.target_term) for h in hits2])
g = terimleri_gom((seg, seg), hits2)
p("dup gom:", [x.text for x in g], g[0] is g[1])
# 3. speaker containing term
seg3 = Segment(text="はい。", bbox=R, speaker="マルクス")
p("speaker hits:", s.lookup_segments((seg3,)))
# 4. identity embedding: Marcus -> Marcus in JP text with Latin Marcus
seg4 = Segment(text="Marcusが待っています。", bbox=R)
h4 = s.lookup_segments((seg4,))
p("identity hits:", h4)
g4 = terimleri_gom((seg4,), h4)
p("identity gom:", g4[0].text, g4[0] is seg4, g4[0] == seg4)
# 5. idempotence: gom output re-looked-up
g1 = terimleri_gom((seg,), s.lookup_segments((seg,)))
p("gom1:", g1[0].text)
h_again = s.lookup_segments(g1)
p("re-lookup:", h_again)
g2 = terimleri_gom(g1, h_again)
p("gom2:", g2[0].text, g2[0].text == g1[0].text)
# EN: "The elder Marcus waits by the mill."
segE = Segment(text="The elder Marcus waits by the mill.", bbox=R)
gE = terimleri_gom((segE,), s.lookup_segments((segE,)))
p("EN gom1:", gE[0].text)
hE2 = s.lookup_segments(gE)
p("EN re-lookup:", hE2)
gE2 = terimleri_gom(gE, hE2)
p("EN gom2:", gE2[0].text)
# 6. placeholders empty and text contains {0}, term "0" short with izin
import tempfile
td = tempfile.mkdtemp()
pj = Path(td)/"sifir.json"
pj.write_text(json.dumps({"terimler":[{"kaynak":"0","hedef":"Sıfır","kisa_terim_izni":True},{"kaynak":"マルクス","hedef":"Marcus"}]}, ensure_ascii=False), encoding="utf-8")
s0 = GlossaryStore(pj)
seg6 = Segment(text="{0}マルクスは村にいます。", bbox=R, placeholders=())
h6 = s0.lookup_segments((seg6,))
p("sifir hits (no placeholders):", h6)
g6 = terimleri_gom((seg6,), h6)
p("sifir gom:", g6[0].text)
seg6b = Segment(text="{0}マルクスは村にいます。", bbox=R, placeholders=("{0}",))
h6b = s0.lookup_segments((seg6b,))
p("sifir hits (with placeholders):", h6b)
# 7. symbols as boundary
for t in ["マルクス♪", "♪マルクス", "マルクス→", "マルクス＋", "マルクス♥", "マルクス☆", "Marcus♪", "마르쿠스♪", "マルクス～", "マルクス♡", "★マルクス★", "マルクス…", "マルクス:", "マルクス;", "マルクス!", "マルクス！", "マルクス ", "マルクス※", "マルクス〜", "マルクス♫"]:
    import unicodedata
    last = t[-1] if not t[-1].isalpha() and not ('\u30a0' <= t[-1] <= '\u30ff') else t[0]
    p(repr(t), len(s.lookup(t)), unicodedata.category(last))
# 8. TypeError classes
for bad in [("str placeholders", lambda: s.lookup("マルクス", "{0}")), ("None path", lambda: GlossaryStore(None)), ("int text", lambda: s.lookup(5)), ("list of int placeholders", lambda: s.lookup("マルクス", [1]))]:
    try:
        bad[1]()
        p(bad[0], "no error")
    except Exception as e:
        p(bad[0], type(e).__name__, isinstance(e, ContractViolation), e)
# gom with segment placeholders str
segS = Segment(text="マルクス", bbox=R, placeholders="{0}")  # type: ignore
try:
    terimleri_gom((segS,), (TermHit("マルクス","Marcus",0,4,0),))
    p("gom str placeholders: ok")
except Exception as e:
    p("gom str placeholders:", type(e).__name__, e)
try:
    s.lookup_segments((segS,))
    p("lookup_segments str placeholders: ok")
except Exception as e:
    p("lookup_segments str placeholders:", type(e).__name__, e)
# generator input
gen = (x for x in (seg,))
try:
    r = s.lookup_segments(gen)
    p("generator lookup_segments:", r)
except Exception as e:
    p("generator lookup_segments:", type(e).__name__, e)
gen = (x for x in (seg,))
try:
    r = terimleri_gom(gen, ())
    p("generator gom empty hits:", r)
except Exception as e:
    p("generator gom empty:", type(e).__name__, e)
gen = (x for x in (seg,))
try:
    r = terimleri_gom(gen, s.lookup_segments((seg,)))
    p("generator gom hits:", [x.text for x in r])
except Exception as e:
    p("generator gom hits:", type(e).__name__, e)
# list vs tuple
r = terimleri_gom([seg], s.lookup_segments([seg]))
p("list in:", type(r), [x.text for x in r])
# empty text segment; only placeholder
for t, ph in [("", ()), ("{0}", ("{0}",)), ("{0}", ()), ("   ", ())]:
    sg = Segment(text=t, bbox=R, placeholders=ph)
    hh = s.lookup_segments((sg,))
    gg = terimleri_gom((sg,), hh)
    p(repr(t), ph, hh, gg[0] is sg)
# source term containing 。
pj2 = Path(td)/"nokta.json"
pj2.write_text(json.dumps({"terimler":[{"kaynak":"「マルクス」。","hedef":"Marcus"},{"kaynak":"mill","hedef":"Değirmen mill"}]}, ensure_ascii=False), encoding="utf-8")
try:
    s2 = GlossaryStore(pj2)
    p("kaynak with 。 accepted; terimler:", s2.terimler)
    p(s2.lookup("「マルクス」。行こう。"))
    sgm = Segment(text="by the mill.", bbox=R)
    gm = terimleri_gom((sgm,), s2.lookup_segments((sgm,)))
    p("mill->Değirmen mill gom1:", gm[0].text)
    gm2 = terimleri_gom(gm, s2.lookup_segments(gm))
    p("gom2:", gm2[0].text)
    gm3 = terimleri_gom(gm2, s2.lookup_segments(gm2))
    p("gom3:", gm3[0].text)
except Exception as e:
    p("kaynak 。:", type(e).__name__, e)
# hedef with … : ;
for hed in ["Marcus…", "Marcus:", "Marcus;", "Marcus,", "St Marcus", "Marcus・A", "Marcus\n", "Marcus\tA", "Ma rcus"]:
    pj3 = Path(td)/"h.json"
    pj3.write_text(json.dumps({"terimler":[{"kaynak":"マルクス","hedef":hed}]}, ensure_ascii=False), encoding="utf-8")
    try:
        GlossaryStore(pj3); p("hedef", repr(hed), "kabul")
    except ValueError as e:
        p("hedef", repr(hed), "RED", e)
out.close()
