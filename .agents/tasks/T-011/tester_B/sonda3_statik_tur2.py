"""TESTER-B (T-011, tur 2) -- statik sonda: v3 kodunun ▲ maddeleri + kotu kullanim noktalari, modelsiz.

    python .agents/tasks/T-011/tester_B/sonda3_statik_tur2.py

Stdout yalniz ASCII (sayilar/boolean). Ham (CJK) ciktilar UTF-8 dosyaya:
    .agents/tasks/T-011/tester_B_evidence/tur2/sonda3-statik-ham.txt

Bolumler:
  S1. JP saygi eki 17 / KR ek disi 21 (tur-1 kacak listeleri) -> v3'te kac eslesiyor, kalanlar neden.
  S2. Paket-olcum celiskileri: `マルクス山` (1, betik gecisi), `마르쿠스들이다` (1, 2 ek); 3-ek yiginlari.
  S3. KR 3-ek yayginligi: 10 dogal NPC cumlesi + 10 yigin-agirlikli cumle; hit yok = kacak.
  S4. JP kanji ad + kanji unvan eki (`先生/先輩/氏/公`) ve hiragana ad + hiragana eki (`くん/さま`): liste disi.
  S5. Betik gecisi kotu kullanim: katakana cins isim (`ゴブリン`) + `キング`/`王`; `ポーション瓶`; `마르쿠스王`; Latin ad + Latin ek.
  S6. K2/K3 kotu kullanim: bosluklu yer tutucu, terimle ayni yer tutucu, gomulu segmentin tekrar lookup'i, `_` siniri.
  S7. K6: `kisa_terim_izni` + terminator/`{`; 100/101 kodpoint; tam/yarim genislik.
  S8. Zincir: `windmill` -> `RüzgarDeğirmen` (bitisik Latin), `oldmillhouse`, olu yon hafizasi.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unicodedata
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(KOK))

from src.contracts.errors import ContractViolation  # noqa: E402
from src.contracts.models import Rect, Segment, TermHit  # noqa: E402
from src.translate.sozluk import GlossaryStore, terimleri_gom  # noqa: E402

FIXTURE = KOK / ".agents" / "tasks" / "T-011" / "fixtures" / "sozluk_ornek.json"
HAM = KOK / ".agents" / "tasks" / "T-011" / "tester_B_evidence" / "tur2" / "sonda3-statik-ham.txt"
R = Rect(0, 0, 800, 36)
out = open(HAM, "w", encoding="utf-8")


def h(*a: object) -> None:
    print(*a, file=out)


def say(m: str) -> None:
    print(m.encode("ascii", "replace").decode("ascii"))


def sozluk(td: str, terimler: list[dict[str, object]], ad: str) -> GlossaryStore:
    p = Path(td) / ad
    p.write_text(json.dumps({"terimler": terimler}, ensure_ascii=False), encoding="utf-8")
    return GlossaryStore(p)


def L(s: GlossaryStore, t: str, ph: tuple[str, ...] = ()) -> list[tuple[str, str, int, int]]:
    return [(x.source_term, x.target_term, x.start, x.end) for x in s.lookup(t, ph)]


def main() -> int:
    s = GlossaryStore(FIXTURE)
    td_obj = tempfile.TemporaryDirectory()
    td = td_obj.name

    # ---------------- S1 ----------------
    say("== S1. tur-1 kacak listeleri v3'te ==")
    h("== S1 ==")
    JP = ["マルクスさん", "マルクス様", "マルクス殿", "マルクス君", "マルクスちゃん", "マルクス達", "マルクスたち", "マルクスって", "マルクスだ",
          "マルクスじゃない", "マルクスなら", "マルクスから", "マルクスまで", "マルクスより", "マルクスか", "マルクスよ", "マルクスね"]
    KR = ["마르쿠스님", "마르쿠스씨", "마르쿠스야", "마르쿠스아", "마르쿠스에게", "마르쿠스한테", "마르쿠스께", "마르쿠스랑", "마르쿠스처럼",
          "마르쿠스보다", "마르쿠스마다", "마르쿠스밖에", "마르쿠스조차", "마르쿠스들", "마르쿠스라고", "마르쿠스라면", "마르쿠스인가",
          "방앗간이다", "방앗간입니다"]
    jp_hit = [t for t in JP if s.lookup(t)]
    kr_hit = [t for t in KR if s.lookup(t)]
    h("JP eslesen:", jp_hit, "\nJP kacak:", [t for t in JP if t not in jp_hit])
    h("KR eslesen:", kr_hit, "\nKR kacak:", [t for t in KR if t not in kr_hit])
    say(f"  JP 17 eki: {len(jp_hit)}/17 eslesiyor (liste disi `じゃない`/`なら` da betik gecisiyle); KR 19 (unvansiz): {len(kr_hit)}/19, kacak: {19 - len(kr_hit)} (`인가` listede yok)")

    # ---------------- S2 ----------------
    say("== S2. paket-olcum celiskileri ve 3-ek yiginlari ==")
    h("== S2 ==")
    for t in ["マルクス山", "マルクス様", "마르쿠스들이다", "마르쿠스들이", "마르쿠스님에게는", "마르쿠스에게는", "마르쿠스님께서는",
              "마르쿠스님께서", "마르쿠스님한테도", "마르쿠스들에게", "마르쿠스들에게는", "마르쿠스에게서", "마르쿠스한테서", "마르쿠스으로부터",
              "마르쿠스님으로부터", "마르쿠스예요", "마르쿠스이에요", "마르쿠스요", "마르쿠스가요", "마르쿠스는데", "마르쿠스님들은"]:
        h(f"{t!r}: {L(s, t)}")
    say(f"  マルクス山={len(s.lookup('マルクス山'))} (implementer 1; paket 'eslesmez')  마르쿠스들이다={len(s.lookup('마르쿠스들이다'))} (implementer 1; paket 'eslesmez')")
    uc = ["마르쿠스님에게는", "마르쿠스님께서는", "마르쿠스님한테도", "마르쿠스들에게는", "마르쿠스님으로부터", "마르쿠스님들은"]
    say(f"  3-ek yigini (6): eslesen {sum(bool(s.lookup(t)) for t in uc)}/6")
    ek_disi = ["마르쿠스에게서", "마르쿠스한테서", "마르쿠스예요", "마르쿠스이에요", "마르쿠스요", "마르쿠스가요", "마르쿠스는데"]
    say(f"  liste disi ek (에게서/한테서/예요/이에요/요/가요/는데, 7): eslesen {sum(bool(s.lookup(t)) for t in ek_disi)}/7")

    # ---------------- S3 ----------------
    say("== S3. KR 3-ek yayginligi: 10 dogal NPC cumlesi / 10 yigin agirlikli ==")
    h("== S3 ==")
    dogal = ["마르쿠스님, 어서 오세요.", "마르쿠스님께서 부르십니다.", "아일라는 방앗간에 있어요.", "마르쿠스님께서는 오늘 안 계십니다.",
             "이건 아일라의 검이에요.", "마르쿠스에게 이 편지를 전해 주세요.", "아일라한테서 들었어요.", "마르쿠스님도 함께 가실 거예요.",
             "아일라야, 조심해!", "마르쿠스님은 마을 장로입니다."]
    yigin = ["마르쿠스님께서는 지금 안 계십니다.", "마르쿠스님에게는 비밀이 있습니다.", "아일라님한테도 말했어요.", "마르쿠스님께 전해 주세요.",
             "아일라님이 오셨습니다.", "마르쿠스에게서 편지가 왔습니다.", "마르쿠스님의 검입니다.", "아일라님은 방앗간에 계십니다.",
             "마르쿠스님들은 어디 계세요?", "마르쿠스님께서도 동의하셨습니다."]
    for ad, kume in (("dogal", dogal), ("yigin", yigin)):
        kacak = []
        for c in kume:
            n = len([x for x in s.lookup(c) if x.target_term in ("Marcus", "Ayla")])
            h(f"[{ad}] {c!r}: ad hit={n}")
            if n == 0:
                kacak.append(c)
        h(f"[{ad}] kacak: {kacak}")
        say(f"  {ad}: 10 cumlenin {len(kacak)}'inde ad hit YOK")

    # ---------------- S4 ----------------
    say("== S4. kanji ad + kanji unvan eki / hiragana ad + hiragana eki (liste disi) ==")
    h("== S4 ==")
    s4 = sozluk(td, [{"kaynak": "太郎", "hedef": "Taro"}, {"kaynak": "ひかり", "hedef": "Hikari"}], "s4.json")
    kanji = ["太郎先生", "太郎先輩", "太郎氏", "太郎公", "太郎王", "太郎隊長", "太郎様", "太郎君", "太郎達", "太郎殿", "太郎が", "太郎さん"]
    hira = ["ひかりくん", "ひかりさま", "ひかりせんぱい", "ひかりせんせい", "ひかりたん", "ひかりちゃん", "ひかりさん", "ひかりは", "ひかりです", "ひかり姫"]
    for t in kanji + hira:
        h(f"{t!r}: {L(s4, t)}")
    k_kacak = [t for t in kanji if not s4.lookup(t)]
    h_kacak = [t for t in hira if not s4.lookup(t)]
    h("kanji kacak:", k_kacak, "\nhiragana kacak:", h_kacak)
    say(f"  kanji ad + kanji ek (12): kacak {len(k_kacak)} (先生/先輩/氏/公/王/隊長 listede yok); hiragana ad + hiragana ek (10): kacak {len(h_kacak)} (くん/さま/せんぱい/せんせい/たん)")

    # ---------------- S5 ----------------
    say("== S5. betik gecisi kotu kullanim ==")
    h("== S5 ==")
    s5 = sozluk(td, [{"kaynak": "ゴブリン", "hedef": "Goblin"}, {"kaynak": "ポーション", "hedef": "İksir"}, {"kaynak": "마르쿠스", "hedef": "Marcus"},
                     {"kaynak": "Marcus", "hedef": "Marcus"}, {"kaynak": "マルクス", "hedef": "Marcus"}, {"kaynak": "エルフ", "hedef": "Elf"}], "s5.json")
    for t in ["ゴブリンキング", "ゴブリン王", "ゴブリン王が現れた。", "ポーション瓶", "ポーション瓶を拾った。", "마르쿠스王", "마르쿠스가", "エルフ族の村",
              "ゴブリンの王", "ゴブリン・キング", "Marcus's", "Marcus'", "Marcus'ın", "Marcus-san", "Marcus’s", "Marcusさん", "Marcus様", "Marcus2",
              "Marcuss", "Marcus_2", "MARCUS'UN", "マルクス♪", "Marcus♪", "マルクス～", "Marcus$", "ﾏﾙｸｽ", "Ｍａｒｃｕｓ"]:
        h(f"{t!r}: {L(s5, t)}")
    say(f"  ゴブリンキング={len(s5.lookup('ゴブリンキング'))} ゴブリン王={len(s5.lookup('ゴブリン王'))} ポーション瓶={len(s5.lookup('ポーション瓶'))} 마르쿠스王={len(s5.lookup('마르쿠스王'))} エルフ族={len(s5.lookup('エルフ族の村'))}")
    say(f"  Marcus's={len(s5.lookup(chr(77)+'arcus'+chr(39)+'s'))} Marcus'={len(s5.lookup('Marcus'+chr(39)))} Marcus'in={len(s5.lookup('Marcus'+chr(39)+'ın'))} Marcus-san={len(s5.lookup('Marcus-san'))} Marcus_2={len(s5.lookup('Marcus_2'))} Marcus2={len(s5.lookup('Marcus2'))}")
    say(f"  halfwidth katakana={len(s5.lookup('ﾏﾙｸｽ'))} fullwidth Latin={len(s5.lookup('Ｍａｒｃｕｓ'))} (NFC genislik katlamaz; [OLCULMUYOR] adayi)")

    # ---------------- S6 ----------------
    say("== S6. K2/K3 kotu kullanim ==")
    h("== S6 ==")
    sg = Segment(text="マルクスが アイラを 待つ", bbox=R, placeholders=(" ",))
    hits = s.lookup_segments((sg,))
    g = terimleri_gom((sg,), hits)
    h(f"bosluklu yer tutucu: hits={[(x.source_term, x.start) for x in hits]} gomulu={g[0].text!r} ph={g[0].placeholders!r}")
    say(f"  placeholders=(' ',): hit {len(hits)} (bosluk zaten sinir; korunan aralik hit'i engellemez), gomulu ok={g[0].text == 'Marcusが Aylaを 待つ'}")
    sg2 = Segment(text="マルクスが来た。", bbox=R, placeholders=("マルクス",))
    hits2 = s.lookup_segments((sg2,))
    try:
        terimleri_gom((sg2,), (TermHit("マルクス", "Marcus", 0, 4, 0),))
        cv = "YOK"
    except ContractViolation as e:
        cv = type(e).__name__
    h(f"terimle ayni yer tutucu: lookup hits={hits2} elle hit -> {cv}")
    say(f"  placeholders=(terim,): lookup {len(hits2)} hit; elle hit -> {cv}")
    # gomulu segment tekrar lookup'a: fixture (kimlik ile) sessiz sabit; hedef⊇kaynak sessiz buyume; hedef baska terimin kaynagi sessiz kayma
    sg3 = Segment(text="長老マルクスが水車小屋で待っています。", bbox=R)
    g1 = terimleri_gom((sg3,), s.lookup_segments((sg3,)))
    g2 = terimleri_gom(g1, s.lookup_segments(g1))
    h(f"fixture 2. gecis: {g1[0].text!r} -> {g2[0].text!r} hits2={[(x.source_term, x.target_term) for x in s.lookup_segments(g1)]}")
    say(f"  fixture ile 2. gecis metin ayni={g1[0].text == g2[0].text}; 2. geciste kimlik hit sayisi={len(s.lookup_segments(g1))} (sessiz; CV yok)")
    s6 = sozluk(td, [{"kaynak": "マルクス", "hedef": "Marcus"}, {"kaynak": "Marcus", "hedef": "Marküs"}], "s6.json")
    sg4 = Segment(text="マルクスが来た。", bbox=R)
    a1 = terimleri_gom((sg4,), s6.lookup_segments((sg4,)))
    a2 = terimleri_gom(a1, s6.lookup_segments(a1))
    h(f"hedef baska terimin kaynagi: {sg4.text!r} -> {a1[0].text!r} -> {a2[0].text!r}")
    say(f"  hedef=baska terimin kaynagi: 2. geciste sessiz kayma var={a1[0].text != a2[0].text} (CV yok; docstring 'tekrar gecirilmez')")
    # kaydirilmis segment listesi: ayni terim ayni konumda -> sessiz yanlis segment
    A = (Segment(text="マルクスが来た。", bbox=R), Segment(text="マルクスは村にいます。", bbox=Rect(0, 1, 1, 1)))
    hA = s.lookup_segments(A)
    B = (A[1], A[0])
    gB = terimleri_gom(B, hA)
    h(f"kaydirilmis liste: hits(A) gom(B) -> {[x.text for x in gB]} (CV yok)")
    say(f"  hits(A) + gom(B=ters sira): CV yok, ikisi de gomuldu={all('Marcus' in x.text for x in gB)} (ayni terim ayni konum; cagiran hatasi gorunmez)")
    # `_` P* siniri: `PLAYER_NAME` yer tutucu bildirilmemis
    s6b = sozluk(td, [{"kaynak": "PLAYER", "hedef": "Oyuncu"}], "s6b.json")
    h(f"PLAYER_NAME: {L(s6b, 'PLAYER_NAME is here')}")
    say(f"  `PLAYER_NAME` (bildirilmemis): hit={len(s6b.lookup('PLAYER_NAME is here'))} (`_` P* sinir; D-A5 belgeli)")

    # ---------------- S7 ----------------
    say("== S7. K6 sema kenarlari ==")
    h("== S7 ==")
    for kayit in [{"kaynak": ".", "hedef": "Nokta", "kisa_terim_izni": True}, {"kaynak": "。", "hedef": "Nokta", "kisa_terim_izni": True},
                  {"kaynak": "{", "hedef": "Kume", "kisa_terim_izni": True}, {"kaynak": "{0}", "hedef": "Sıfır"},
                  {"kaynak": "x" * 100, "hedef": "Y"}, {"kaynak": "x" * 101, "hedef": "Y"}, {"kaynak": "Mr. Marcus", "hedef": "Marcus"},
                  {"kaynak": "マルクス", "hedef": "Marcus"}, {"kaynak": "マルクス", "hedef": "Mar​cus"}, {"kaynak": "マルクス", "hedef": "Marcus "},
                  {"kaynak": "マルクス", "hedef": "Marcus", "not": None}, {"kaynak": "マルクス", "hedef": "Marcus", "kisa_terim_izni": 1}]:
        try:
            st = sozluk(td, [kayit], "s7.json")
            sonuc = f"KABUL ({len(st)})"
        except ValueError as e:
            sonuc = f"RED: {str(e)[:80]}"
        h(f"{kayit!r} -> {sonuc}")
        say(f"  kaynak={kayit['kaynak'][:12]!r} hedef={kayit['hedef']!r} -> {sonuc[:6]}")

    # ---------------- S8 ----------------
    say("== S8. zincir ==")
    h("== S8 ==")
    s8 = sozluk(td, [{"kaynak": "wind", "hedef": "Rüzgar"}, {"kaynak": "mill", "hedef": "Değirmen"}, {"kaynak": "old", "hedef": "Eski"},
                     {"kaynak": "millhouse", "hedef": "Değirmen Evi"}, {"kaynak": "house", "hedef": "Ev"}], "s8.json")
    for t in ["The windmill turns.", "The windmills turn.", "oldmillhouse", "old millhouse", "windmillhouse", "windmillhouses", "millwind", "xwindmill"]:
        sg = Segment(text=t, bbox=R)
        g = terimleri_gom((sg,), s8.lookup_segments((sg,)))[0]
        h(f"{t!r}: {L(s8, t)} -> {g.text!r}")
    say(f"  windmill -> {terimleri_gom((Segment(text='The windmill turns.', bbox=R),), s8.lookup_segments((Segment(text='The windmill turns.', bbox=R),)))[0].text.encode('ascii', 'replace').decode()}")
    say(f"  windmills={len(s8.lookup('The windmills turn.'))} oldmillhouse={[x.target_term for x in s8.lookup('oldmillhouse')]!r} windmillhouses={len(s8.lookup('windmillhouses'))}")

    td_obj.cleanup()
    out.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
