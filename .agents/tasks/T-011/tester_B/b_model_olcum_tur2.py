"""TESTER-B (T-011, tur 2; mercek: kotu kullanim + sartname uyumu) -- gercek NMT ile olcumler.

    python .agents/tasks/T-011/tester_B/b_model_olcum_tur2.py

Stdout yalniz ASCII (sayilar/boolean). Ham ceviri metinleri UTF-8 dosyaya:
    .agents/tasks/T-011/tester_B_evidence/tur2/model-olcum-tur2-ham.txt
Model dizini `models/` altindaki tek dizindir (ad bu dosyada gecmez).

Bolumler:
  M1. Zincir + betik gecisi, gercek model: `長老マルクス` (unvan sozlukte yok) ham vs gomulu `長老Marcus`;
      `マルクスアイラ` -> `MarcusAyla` bitisik Latin -- model ayiriyor mu; `長老マルクスアイラ`; kontrol `マルクスとアイラ`.
  M2. Betik gecisi kotu kullanim (K4 cins isim uyarisina ragmen): `ゴブリン->Goblin` + `ゴブリン王` (1 hit, `Goblin王`)
      vs `ゴブリンキング` (0 hit); `ポーション瓶`; `エルフ族の村`; ham vs gomulu.
  M3. UNVAN OLCUMU (Y-B1 gri bolge; hedef tarafi duzeltme gorevine girdi): 10 unvan+ad segmenti (JP 5 / KR 5),
      adlar-yalniz fixture v3: ham ciktida Ingilizce unvan kac/10, gomulu kac/10; ayrica 10 cumle-ici varyant.
  M4. KR 3-ek / liste disi ek kacagi: S3'un 10 dogal cumlesi -- hit yok olanlarda ham ciktida ad korunuyor mu.
  M5. JP kanji ad + kanji unvan eki (`先生`), hiragana ad + `くん`: 0 hit -> ham ciktida ad?
  M6. Kapi denetimi: #6 zincir sinifi gercek modelle (`windmills` ham dogru mu; `windmill` -> `RüzgarDeğirmen` zarar;
      tur-1 `Rüzgarmills` kismi gomme); #5c JP/KR ayri ayri; #4a JP tarafi ("Elder" JP'de de siziyor mu).
  M7. Gomulu segment tekrar lookup+gom+translate (idempotens kotu kullanimi, fixture ile) -- cikti degisiyor mu.
"""
from __future__ import annotations

import re
import sys
import json
import tempfile
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(KOK))

from src.contracts.models import Rect, Segment, TranslationRequest  # noqa: E402
from src.translate.local_nmt import LocalNmtProvider  # noqa: E402
from src.translate.sozluk import GlossaryStore, terimleri_gom  # noqa: E402

MODEL = next(d for d in sorted((KOK / "models").iterdir()) if d.is_dir())
SOZLUK = KOK / ".agents" / "tasks" / "T-011" / "fixtures" / "sozluk_ornek.json"
HAM_DOSYA = KOK / ".agents" / "tasks" / "T-011" / "tester_B_evidence" / "tur2" / "model-olcum-tur2-ham.txt"
R = Rect(0, 0, 800, 36)
EN_UNVAN = {"elder", "captain", "chief", "knight", "princess", "prince", "mayor", "leader", "commander", "lord", "king", "queen",
            "village", "head", "master", "sir", "lady", "the", "of", "general", "guard", "priest", "sage", "old", "man", "chieftain",
            "headman", "boss", "senior"}
TR_UNVAN = {"ihtiyar", "yaşlı", "kaptan", "komutan", "şövalye", "prenses", "muhtar", "reis", "lider", "köy", "şef", "büyük", "kız", "kral"}

ham_out = open(HAM_DOSYA, "w", encoding="utf-8")


def h(*a: object, sep: str = " ") -> None:
    print(*a, file=ham_out, sep=sep)


def _k(m: str) -> str:
    return m.replace("İ", "i").replace("I", "ı").casefold()


def say(m: str) -> None:
    print(m.encode("ascii", "replace").decode("ascii"))


def kelimeler(m: str) -> set[str]:
    return set(re.findall(r"[^\W\d_]+", _k(m)))


def main() -> int:
    p = LocalNmtProvider(model_dir=MODEL, threads=8)
    s = GlossaryStore(SOZLUK)

    def segs(metinler: list[str], yt: tuple[str, ...] = ()) -> tuple[Segment, ...]:
        return tuple(Segment(text=t, bbox=R, placeholders=yt) for t in metinler)

    def cevir(sg: tuple[Segment, ...], dil: str, gom: bool, st: GlossaryStore | None = None) -> tuple[tuple[Segment, ...], list[str]]:
        g = st or s
        if gom:
            sg = terimleri_gom(sg, g.lookup_segments(sg))
        return sg, list(p.translate(TranslationRequest(segments=sg, source_lang=dil, target_lang="tr")).translations)

    def cift(ad: str, dil: str, m: str, st: GlossaryStore | None = None) -> tuple[str, str, str]:
        _, ham = cevir(segs([m]), dil, False, st)
        gs, gom = cevir(segs([m]), dil, True, st)
        h(f"[{ad}] {dil} kaynak={m!r}\n      gomulu_kaynak={gs[0].text!r}\n      ham={ham[0]!r}\n      gom={gom[0]!r}")
        return gs[0].text, ham[0], gom[0]

    # ---------------- M1 ----------------
    say("== M1. zincir + betik gecisi, gercek model ==")
    h("== M1 ==")
    for i, (dil, m) in enumerate([("jpn_Jpan", "長老マルクス"), ("jpn_Jpan", "長老マルクスが来た。"), ("jpn_Jpan", "マルクスアイラ"),
                                  ("jpn_Jpan", "マルクスアイラが来た。"), ("jpn_Jpan", "長老マルクスアイラ"), ("jpn_Jpan", "マルクスとアイラが来た。"),
                                  ("kor_Hang", "장로마르쿠스"), ("kor_Hang", "마르쿠스아일라가 왔습니다.")]):
        gk, ham, gom = cift(f"M1-{i}", dil, m)
        hits = s.lookup(m)
        marcus_g = "Marcus" in gom; ayla_g = "Ayla" in gom
        bitisik = "MarcusAyla" in gom or "Marcusayla" in _k(gom)
        say(f"  M1-{i} {dil}: hit={len(hits)} gomulu_kaynak_uzunluk={len(gk)} | ham: Marcus={'Marcus' in ham} Ayla={'Ayla' in ham} | gom: Marcus={marcus_g} Ayla={ayla_g} bitisik_MarcusAyla_ciktida={bitisik} EN={sorted(kelimeler(gom) & EN_UNVAN)}")

    # ---------------- M2 ----------------
    say("== M2. betik gecisi kotu kullanim: katakana cins isim + kanji ==")
    h("== M2 ==")
    with tempfile.TemporaryDirectory() as td:
        pj = Path(td) / "cins.json"
        pj.write_text(json.dumps({"terimler": [{"kaynak": "ゴブリン", "hedef": "Goblin"}, {"kaynak": "ポーション", "hedef": "İksir"},
                                               {"kaynak": "エルフ", "hedef": "Elf"}, {"kaynak": "マルクス", "hedef": "Marcus"}]}, ensure_ascii=False), encoding="utf-8")
        sc = GlossaryStore(pj)
        for i, m in enumerate(["ゴブリン王が現れた。", "ゴブリンキングが現れた。", "ゴブリンが現れた。", "ポーション瓶を拾った。", "ポーションを拾った。",
                               "エルフ族の村へ行った。", "マルクス家の屋敷です。"]):
            gk, ham, gom = cift(f"M2-{i}", "jpn_Jpan", m, sc)
            hedef = [x.target_term for x in sc.lookup(m)]
            say(f"  M2-{i}: hit={len(hedef)} hedef_gomuluda={[_k(t) in _k(gom) for t in hedef]} hedef_hamda={[_k(t) in _k(ham) for t in hedef]} EN_gom={sorted(kelimeler(gom) & EN_UNVAN)} uzunluk ham={len(ham)} gom={len(gom)}")

    # ---------------- M3 ----------------
    say("== M3. UNVAN OLCUMU: 10 unvan+ad segmenti, adlar-yalniz sozluk (fixture v3) ==")
    h("== M3 ==")
    unvan = [("jpn_Jpan", "長老マルクス"), ("jpn_Jpan", "隊長アイラ"), ("jpn_Jpan", "村長マルクス"), ("jpn_Jpan", "騎士アイラ"), ("jpn_Jpan", "王女アイラ"),
             ("kor_Hang", "장로 마르쿠스"), ("kor_Hang", "대장 아일라"), ("kor_Hang", "촌장 마르쿠스"), ("kor_Hang", "기사 아일라"), ("kor_Hang", "공주 아일라")]
    en_ham = en_gom = tr_ham = tr_gom = ad_ham = ad_gom = 0
    for i, (dil, m) in enumerate(unvan):
        gk, ham, gom = cift(f"M3-{i}", dil, m)
        eh, eg = kelimeler(ham) & EN_UNVAN, kelimeler(gom) & EN_UNVAN
        th, tg = kelimeler(ham) & TR_UNVAN, kelimeler(gom) & TR_UNVAN
        ad = "Marcus" if "マルクス" in m or "마르쿠스" in m else "Ayla"
        en_ham += bool(eh); en_gom += bool(eg); tr_ham += bool(th); tr_gom += bool(tg); ad_ham += ad in ham; ad_gom += ad in gom
        h(f"      EN_ham={sorted(eh)} EN_gom={sorted(eg)} TR_ham={sorted(th)} TR_gom={sorted(tg)}")
        say(f"  M3-{i} {dil}: EN unvan ham={sorted(eh)} gom={sorted(eg)} | TR unvan ham={sorted(th)} gom={sorted(tg)} | ad ham={ad in ham} gom={ad in gom}")
    say(f"  [M3] 10 segment: Ingilizce unvan HAM {en_ham}/10, GOMULU {en_gom}/10 | Turkce unvan ham {tr_ham}/10, gomulu {tr_gom}/10 | ad dogru ham {ad_ham}/10, gomulu {ad_gom}/10")
    h("== M3b (cumle ici) ==")
    unvan_c = [("jpn_Jpan", "長老マルクスが来た。"), ("jpn_Jpan", "隊長アイラは村にいます。"), ("jpn_Jpan", "村長マルクスに会った。"), ("jpn_Jpan", "騎士アイラが剣を抜いた。"),
               ("jpn_Jpan", "王女アイラは城にいる。"), ("kor_Hang", "장로 마르쿠스가 왔습니다."), ("kor_Hang", "대장 아일라는 마을에 있습니다."),
               ("kor_Hang", "촌장 마르쿠스를 만났습니다."), ("kor_Hang", "기사 아일라가 검을 뽑았습니다."), ("kor_Hang", "공주 아일라는 성에 있습니다.")]
    en_ham = en_gom = ad_ham = ad_gom = 0
    for i, (dil, m) in enumerate(unvan_c):
        gk, ham, gom = cift(f"M3b-{i}", dil, m)
        eh, eg = kelimeler(ham) & EN_UNVAN, kelimeler(gom) & EN_UNVAN
        ad = "Marcus" if "マルクス" in m or "마르쿠스" in m else "Ayla"
        en_ham += bool(eh); en_gom += bool(eg); ad_ham += ad in ham; ad_gom += ad in gom
        h(f"      EN_ham={sorted(eh)} EN_gom={sorted(eg)}")
        say(f"  M3b-{i} {dil}: EN unvan ham={sorted(eh)} gom={sorted(eg)} | ad ham={ad in ham} gom={ad in gom}")
    say(f"  [M3b] 10 cumle: Ingilizce unvan HAM {en_ham}/10, GOMULU {en_gom}/10 | ad dogru ham {ad_ham}/10, gomulu {ad_gom}/10")

    # ---------------- M4 ----------------
    say("== M4. KR dogal 10 cumle: hit yok olanlarda ham ciktida ad? ==")
    h("== M4 ==")
    dogal = ["마르쿠스님, 어서 오세요.", "마르쿠스님께서 부르십니다.", "아일라는 방앗간에 있어요.", "마르쿠스님께서는 오늘 안 계십니다.",
             "이건 아일라의 검이에요.", "마르쿠스에게 이 편지를 전해 주세요.", "아일라한테서 들었어요.", "마르쿠스님도 함께 가실 거예요.",
             "아일라야, 조심해!", "마르쿠스님은 마을 장로입니다."]
    kacak = 0; kacak_ad_kayip = 0; kazanc = 0
    for i, m in enumerate(dogal):
        gk, ham, gom = cift(f"M4-{i}", "kor_Hang", m)
        ad = "Marcus" if "마르쿠스" in m else "Ayla"
        n = len(s.lookup(m))
        if n == 0:
            kacak += 1; kacak_ad_kayip += ad not in ham
        else:
            kazanc += (ad in gom) and (ad not in ham)
        say(f"  M4-{i}: hit={n} ad ham={ad in ham} gom={ad in gom}")
    say(f"  [M4] 10 dogal cumle: hit yok {kacak}/10; bunlarda ad hamda KAYIP {kacak_ad_kayip}/{kacak}; hit olanlarda gomme kazanci {kazanc}/{10 - kacak}")

    # ---------------- M5 ----------------
    say("== M5. JP kanji ad + kanji ek (先生), hiragana ad + くん: liste disi ==")
    h("== M5 ==")
    with tempfile.TemporaryDirectory() as td:
        pj = Path(td) / "jp.json"
        pj.write_text(json.dumps({"terimler": [{"kaynak": "太郎", "hedef": "Taro"}, {"kaynak": "ひかり", "hedef": "Hikari"}]}, ensure_ascii=False), encoding="utf-8")
        sj = GlossaryStore(pj)
        for i, m in enumerate(["太郎先生が来た。", "太郎先輩が来た。", "太郎様が来た。", "ひかりくんが来た。", "ひかりさまが来た。", "ひかりちゃんが来た。"]):
            gk, ham, gom = cift(f"M5-{i}", "jpn_Jpan", m, sj)
            ad = "Taro" if "太郎" in m else "Hikari"
            say(f"  M5-{i}: hit={len(sj.lookup(m))} ad ham={ad in ham} gom={ad in gom} EN_gom={sorted(kelimeler(gom) & EN_UNVAN)}")

    # ---------------- M6 ----------------
    say("== M6. kapi denetimi: #6 zincir sinifi gercek modelle, #5c ayri ayri, #4a JP ==")
    h("== M6 ==")
    with tempfile.TemporaryDirectory() as td:
        pj = Path(td) / "ruzgar.json"
        pj.write_text(json.dumps({"terimler": [{"kaynak": "wind", "hedef": "Rüzgar"}, {"kaynak": "mill", "hedef": "Değirmen"}]}, ensure_ascii=False), encoding="utf-8")
        sr = GlossaryStore(pj)
        for i, m in enumerate(["The windmills turn.", "The windmill turns.", "The old mill is by the river."]):
            gk, ham, gom = cift(f"M6-{i}", "eng_Latn", m, sr)
            say(f"  M6-{i}: hit={len(sr.lookup(m))} gomulu_kaynak_degisti={gk != m} | ham degirmen={'değirmen' in _k(ham)} | gom degirmen={'değirmen' in _k(gom)} ruzgar={'rüzgar' in _k(gom)} bitisik_RuzgarDegirmen={'rüzgardeğirmen' in _k(gom)} uzunluk ham={len(ham)} gom={len(gom)}")
        # tur-1 kismi gomme (zincir kuralinin engelledigi sinif) -- elle kurulmus girdi
        _, kismi = cevir(segs(["The Rüzgarmills turn."]), "eng_Latn", False)
        h(f"[M6-kismi] 'The Rüzgarmills turn.' -> {kismi[0]!r}")
        say(f"  M6-kismi (tur-1 sinifi, elle): degirmen={'değirmen' in _k(kismi[0])} ruzgar={'rüzgar' in _k(kismi[0])}")
    # #5c ayri ayri
    _, jp_ham = cevir(segs(["マルクスさんが来た。"]), "jpn_Jpan", False)
    _, kr_ham = cevir(segs(["마르쿠스에게 말했습니다."]), "kor_Hang", False)
    h(f"[M6-5c] JP ham={jp_ham[0]!r} KR ham={kr_ham[0]!r}")
    say(f"  M6-5c: hamda Marcus YOK -- JP={'Marcus' not in jp_ham[0]} KR={'Marcus' not in kr_ham[0]} (kapi `or` ile geciyor; `and` de gecer mi: {'Marcus' not in jp_ham[0] and 'Marcus' not in kr_ham[0]})")
    # #4b kirilganlik: ham 'ihtiyar' var mi (model degisirse sart bosa duser)
    gk, ham, gom = cift("M6-4b", "kor_Hang", "마을 장로가 마르쿠스를 불렀습니다.")
    say(f"  M6-4b: ham ihtiyar={'ihtiyar' in _k(ham)} gom ihtiyar={'ihtiyar' in _k(gom)} Marcus_gom={'Marcus' in gom} kasaba_gom={'kasaba' in _k(gom)}")

    # ---------------- M7 ----------------
    say("== M7. gomulu segment tekrar zincire (fixture ile) ==")
    h("== M7 ==")
    for i, (dil, m) in enumerate([("jpn_Jpan", "長老マルクスが水車小屋で待っています。"), ("kor_Hang", "마르쿠스는 방앗간에서 아일라를 만났습니다.")]):
        g1, c1 = cevir(segs([m]), dil, True)
        g2, c2 = cevir(g1, dil, True)
        h(f"[M7-{i}] {dil} 1.gecis={g1[0].text!r} ceviri={c1[0]!r}\n        2.gecis={g2[0].text!r} ceviri={c2[0]!r}")
        say(f"  M7-{i}: 2. gecis metin ayni={g1[0].text == g2[0].text} ceviri ayni={c1 == c2}")

    p.close()
    ham_out.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
