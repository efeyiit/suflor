import sys, dataclasses, json, unicodedata, random, tempfile
sys.path.insert(0, r"C:\Users\pc\Desktop\efe\çeviri uygulaması")
from pathlib import Path
from src.contracts.models import Segment, Rect, TermHit
from src.contracts.errors import ContractViolation
from src.translate.sozluk import GlossaryStore, terimleri_gom, ilk_harfi_buyut
from src.translate.local_nmt import cumlelere_bol, modele_gider, _yer_tutuculari_onar
out = open(r"C:\Users\pc\Desktop\efe\çeviri uygulaması\.agents\tasks\T-011\tester_B_evidence\sonda2-statik.txt", "w", encoding="utf-8")
def p(*a): print(*a, file=out)
s = GlossaryStore(Path(r"C:\Users\pc\Desktop\efe\çeviri uygulaması\.agents\tasks\T-011\fixtures\sozluk_ornek.json"))
R = Rect(0,0,1,1)
p("== honorific / ek miss class ==")
for t in ["マルクスさん", "マルクスさんが来た。", "マルクス様", "マルクス殿", "マルクス君", "マルクスちゃん", "マルクス達", "マルクスたち", "マルクスって", "マルクスだ", "マルクスです", "マルクスじゃない", "マルクスなら", "マルクスも", "マルクスへ", "マルクスから", "マルクスまで", "マルクスより", "マルクスか", "マルクスよ", "マルクスね", "マルクス!",
          "마르쿠스님", "마르쿠스씨", "마르쿠스야", "마르쿠스아", "마르쿠스에게", "마르쿠스한테", "마르쿠스께", "마르쿠스랑", "마르쿠스처럼", "마르쿠스보다", "마르쿠스마다", "마르쿠스밖에", "마르쿠스조차", "마르쿠스한테서", "마르쿠스들", "마르쿠스라고", "마르쿠스라면", "마르쿠스인가", "마르쿠스야!", "마르쿠스가", "마르쿠스를", "마르쿠스는",
          "장로님", "장로께서", "장로에게", "방앗간으로", "방앗간에서는", "방앗간까지는", "방앗간이다", "방앗간입니다",
          "Marcus's", "Marcus'", "Marcus2", "elder's", "elders", "mills", "Marcus-san"]:
    p(repr(t), len(s.lookup(t)))
p("== symbol class on fixture sentences ==")
base = ["長老マルクス", "マルクスがあなたを待っています。", "水車小屋を過ぎて東の道を行きなさい。", "장로 마르쿠스", "방앗간을 지나 동쪽 길로 가십시오."]
n0 = sum(len(s.lookup(t)) for t in base)
p("base hits", n0)
for sym in ["♪", "～", "♥", "☆", "→", "＋", "♡", "★", "…", "！", "〜", "・", "♫", "※", "〒", "©", "™", "°", "＄", "￥", "％", "＆", "＃", "＠"]:
    n = sum(len(s.lookup(t.rstrip("。") + sym)) for t in base)
    n_pre = sum(len(s.lookup(sym + t)) for t in base)
    p(repr(sym), unicodedata.category(sym), "suffix hits", n, "prefix hits", n_pre)
p("== NFD placeholder + gom NFC drift ==")
nfd = unicodedata.normalize("NFD", "{Değirmen}")
txt = nfd + "はマルクスの家です。"
seg = Segment(text=txt, bbox=R, placeholders=(nfd,))
hits = s.lookup_segments((seg,))
p("hits", hits)
g = terimleri_gom((seg,), hits)
p("gom text NFC?", unicodedata.is_normalized("NFC", g[0].text), "placeholder still substring?", g[0].placeholders[0] in g[0].text, "ph NFC in text?", unicodedata.normalize("NFC", nfd) in g[0].text)
parts = cumlelere_bol(g[0].text)
p("parts", parts, [modele_gider(pp, g[0].placeholders) for pp in parts])
p("repair on hypothetical output:", _yer_tutuculari_onar(unicodedata.normalize("NFC", nfd) + " Marcus evi", g[0].text, g[0].placeholders))
nfc = unicodedata.normalize("NFC", "{Değirmen}")
seg2 = Segment(text=nfc + "はマルクスの家です。", bbox=R, placeholders=(nfc,))
g2 = terimleri_gom((seg2,), s.lookup_segments((seg2,)))
p("control NFC: ph substring?", g2[0].placeholders[0] in g2[0].text)
seg3 = Segment(text=unicodedata.normalize("NFD", "Değirmen yok."), bbox=R)
g3 = terimleri_gom((seg3,), s.lookup_segments((seg3,)))
p("no-hit NFD stays NFD?", g3[0] is seg3, unicodedata.is_normalized("NFC", g3[0].text))
p("== kaynak with terminator changes T-007 split ==")
td = Path(tempfile.mkdtemp())
pj = td/"a.json"; pj.write_text(json.dumps({"terimler":[{"kaynak":"マルクス。","hedef":"Marcus"}]}, ensure_ascii=False), encoding="utf-8")
s2 = GlossaryStore(pj)
txt = "彼はマルクス。行こう。"
segk = Segment(text=txt, bbox=R)
hk = s2.lookup_segments((segk,))
p("hits", hk)
txt2 = "彼はマルクス。 行こう。"
segk2 = Segment(text=txt2, bbox=R)
hk2 = s2.lookup_segments((segk2,))
gk2 = terimleri_gom((segk2,), hk2)
p("hits2", hk2, "gom:", gk2[0].text, "split before", len(cumlelere_bol(txt2)), "after", len(cumlelere_bol(gk2[0].text)))
p("== IGNORECASE Turkish I ==")
pj2 = td/"b.json"; pj2.write_text(json.dumps({"terimler":[{"kaynak":"İstanbul","hedef":"İstanbul"},{"kaynak":"ışık","hedef":"Işık"}]}, ensure_ascii=False), encoding="utf-8")
s3 = GlossaryStore(pj2)
for t in ["istanbul", "ISTANBUL", "ıstanbul", "İstanbul", "IŞIK", "isik", "Isık", "ışık"]:
    p(repr(t), [(h.source_term, h.start, h.end) for h in s3.lookup(t)])
p("== lookup vs lookup_segments equality over random segments ==")
random.seed(11)
pool = ["長老", "マルクス", "水車小屋", "アイラ", "が", "を", "は", "に", "で", "。", " ", "村", "人", "{0}", "%s", "장로", " ", "마르쿠스", "방앗간", "을", "에서", "아일라", "Marcus", "mill", "elder", "MARCUS", "the", ".", ",", "Elder", "Mill", "{PLAYER}", "[Mill]"]
diff = 0; n_hits=0
for k in range(1000):
    txt = "".join(random.choice(pool) for _ in range(random.randint(1, 12)))
    phs = tuple(random.sample(["{0}", "%s", "{PLAYER}", "[Mill]"], random.randint(0, 3)))
    segs = tuple(Segment(text=txt, bbox=R, placeholders=phs) for _ in range(random.randint(1,3)))
    a = s.lookup_segments(segs)
    b = tuple(dataclasses.replace(h, segment_index=i) for i, sg in enumerate(segs) for h in s.lookup(sg.text, sg.placeholders))
    n_hits += len(a)
    if a != b: diff += 1
    ga = terimleri_gom(segs, a); gb = terimleri_gom(list(segs), list(b))
    if ga != gb: diff += 1
p("diff", diff, "hits", n_hits)
p("== identity hit & counter semantics ==")
seg4 = Segment(text="Marcusが待っています。", bbox=R)
h4 = s.lookup_segments((seg4,))
g4 = terimleri_gom((seg4,), h4)
p("identity: hits", len(h4), "text same", g4[0].text == seg4.text, "is", g4[0] is seg4)
p("== hedef contains kaynak (idempotence) ==")
pj3 = td/"c.json"; pj3.write_text(json.dumps({"terimler":[{"kaynak":"mill","hedef":"Değirmen mill"},{"kaynak":"장로","hedef":"장로 İhtiyar"}]}, ensure_ascii=False), encoding="utf-8")
s4 = GlossaryStore(pj3)
sg = Segment(text="by the mill.", bbox=R)
for i in range(3):
    sg = terimleri_gom((sg,), s4.lookup_segments((sg,)))[0]
    p(i, sg.text)
p("== schema: hedef == kaynak? hedef contains kaynak? ==")
for kaynak, hedef in [("Marcus","Marcus"), ("mill","Değirmen mill"), ("Değirmen mill", "mill")]:
    pj4 = td/"d.json"; pj4.write_text(json.dumps({"terimler":[{"kaynak":kaynak,"hedef":hedef}]}, ensure_ascii=False), encoding="utf-8")
    try: GlossaryStore(pj4); p(kaynak, "->", hedef, "kabul")
    except ValueError as e: p(kaynak, "->", hedef, "RED", e)
p("== record-level unknown key / whitespace ==")
for rec in [{"kaynak":"マルクス","hedef":"Marcus","ozel_ad":True}, {"kaynak":"マルクス","hedef":"Marcus","kategori":"ad"}, {"kaynak":"マルクス ","hedef":"Marcus"}, {"kaynak":"マルクス","hedef":"Marcus","not":None}, {"kaynak":"マルクス","hedef":"Marcus","kisa_terim_izni":1}]:
    pj5 = td/"e.json"; pj5.write_text(json.dumps({"terimler":[rec]}, ensure_ascii=False), encoding="utf-8")
    try: GlossaryStore(pj5); p(rec, "kabul")
    except ValueError as e: p(rec, "RED", str(e)[:90])
p("== top-level extra keys ==")
pj6 = td/"f.json"; pj6.write_text(json.dumps({"oyun":"X","surum":2,"terimler":[{"kaynak":"マルクス","hedef":"Marcus"}]}, ensure_ascii=False), encoding="utf-8")
p("top-level extra:", len(GlossaryStore(pj6)))
pj7 = td/"g.json"; pj7.write_text(json.dumps({"terimler":[]}), encoding="utf-8")
s7 = GlossaryStore(pj7); p("empty glossary:", len(s7), s7.lookup("マルクス"), terimleri_gom((seg4,), s7.lookup_segments((seg4,)))[0] is seg4)
p("== KR ek chain false positive probes ==")
for t in ["방앗간이 왔다", "방앗간이다", "방앗간에 가", "방앗간의 로", "방앗간도 둑", "방앗간도둑", "방앗간은가", "방앗간이가 왔다", "방앗간로가", "방앗간에서는요"]:
    p(repr(t), len(s.lookup(t)))
p("== hedef ilk harf buyutme ==")
for h in ["iPhone", "ışık", "ihtiyar", "1up", "ñandu", "ǆemal", "ﬁne", "ß", "değirmen", "ǅ"]:
    p(repr(h), repr(ilk_harfi_buyut(h)))
out.close()
