"""T-007 implementer olcumu 4 (tur 2) -- GERCEK modelle T2-2 ve T2-1 (ayri surec, test DEGIL).

    python .agents/tasks/T-007/evidence/olcum-4-yer-tutucu-ve-terminator-gercek-model.py

Stdout'a YALNIZ ASCII; hicbir ceviri/kaynak metni basilmaz (PROTOKOL 7) --
yalniz parca sayisi, uzunluk, boolean ve anahtar kelime var/yok.

  [A] T2-2: yalniz yer tutucudan olusan cumle modele GITMEZ, cikti AYNEN.
      Gercek fabrika sarmalanir: motora giden parca sayilir (0 olmali).
      `{PLAYER}!`, `{0}!`, `{0}。` (JP), `%s!` -> giden 0, cikti == kaynak.
      `{PLAYER}! Wait!` -> giden 1 (yalniz `Wait!`), cikti `{PLAYER}! ` ile baslar,
      uydurma kalibi ("Hayır") YOK. Pozitif kontroller: `{PLAYER} is here.` -> giden 1;
      `placeholders=()` iken `{PLAYER}!` -> giden 1 (metin sayilir; model uydurabilir --
      bu, Tester-A K-1'in olctugu tur 1 davranisidir, yalniz bildirilmemis yer tutucuda kalir).
  [B] T2-1: `?` ve `！` tek basina bolunce cumle kaybi gidiyor mu (feedback-B'nin
      gercek model tablosu): EN "Are you ready? ..." -> 2 parca, "hazır" VAR;
      JP "止まれ！..." -> 2 parca, "dur" VAR; JP "待って！本当に行くの？" -> 2 parca
      (yalniz parca sayisi; ilk kosumda uydurdugum "bekle" anahtari tutmadi -- model baska
      kelime secti; feedback-B de bu satiri yalniz sayiyla olcmustu. Kalite altin setsiz olculmez).
"""
from __future__ import annotations

import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(KOK))
MODEL = KOK / "models" / "nllb-200-distilled-600M-ct2-int8"

from src.contracts.models import Rect, Segment, TranslationRequest  # noqa: E402
from src.translate import local_nmt  # noqa: E402
from src.translate.local_nmt import LocalNmtProvider, cumlelere_bol  # noqa: E402

GIDEN: list[int] = []  # her translate_batch cagrisinda giden parca sayisi


class _SayanMotor:
    def __init__(self, ic: object) -> None:
        self._ic = ic

    def translate_batch(self, tokens, **kw):  # type: ignore[no-untyped-def]
        GIDEN.append(len(tokens))
        return self._ic.translate_batch(tokens, **kw)  # type: ignore[attr-defined]


def sayan_fabrika(model_dir, params):  # type: ignore[no-untyped-def]
    motor, enc, dec = local_nmt._varsayilan_fabrika(model_dir, params)
    return _SayanMotor(motor), enc, dec


def istek(metin: str, kaynak: str, yt: tuple[str, ...] = ()) -> TranslationRequest:
    return TranslationRequest(
        segments=(Segment(text=metin, bbox=Rect(0, 0, 800, 36), placeholders=yt),),
        source_lang=kaynak, target_lang="tr",
    )


def main() -> int:
    if not (MODEL / "model.bin").exists():
        print(f"model yok: {MODEL}")
        return 1
    p = LocalNmtProvider(model_dir=MODEL, threads=8, motor_fabrikasi=sayan_fabrika)
    ihlal = 0

    def kos(etiket: str, metin: str, kaynak: str, yt: tuple[str, ...], beklenen_giden: int) -> str:
        nonlocal ihlal
        GIDEN.clear()
        r = p.translate(istek(metin, kaynak, yt))
        c = r.translations[0]
        giden = sum(GIDEN)
        ok = giden == beklenen_giden
        ihlal += 0 if ok else 1
        print(f"  {'ok' if ok else 'IHLAL':5s} {etiket:34s} parca={len(cumlelere_bol(metin))} giden={giden} (beklenen {beklenen_giden})"
              f" aynen={c == metin} uzunluk={len(c)} hayir_kalibi={'hayır' in c.lower()} yt_var={all(y in c for y in yt)}")
        return c

    print("[A] T2-2 -- yalniz yer tutucu cumlesi (gercek model)")
    for etiket, metin, kaynak, yt in [
        ("EN {PLAYER}!", "{PLAYER}!", "eng_Latn", ("{PLAYER}",)),
        ("EN {0}!", "{0}!", "eng_Latn", ("{0}",)),
        ("JP {0}。", "{0}。", "jpn_Jpan", ("{0}",)),
        ("EN %s!", "%s!", "eng_Latn", ("%s",)),
        ("KR {0}!", "{0}!", "kor_Hang", ("{0}",)),
    ]:
        c = kos(etiket, metin, kaynak, yt, 0)
        if c != metin:
            ihlal += 1
            print("        IHLAL: cikti kaynagin aynisi degil")
    c = kos("EN {PLAYER}! Wait!", "{PLAYER}! Wait!", "eng_Latn", ("{PLAYER}",), 1)
    basla = c.startswith("{PLAYER}! ")
    print(f"        '{{PLAYER}}! ' ile basliyor={basla} kalan_uzunluk={len(c) - len('{PLAYER}! ')} (kalan = yalniz 'Wait!' cevirisi)")
    if not basla:
        ihlal += 1
    kos("EN {PLAYER} is here. (pozitif)", "{PLAYER} is here.", "eng_Latn", ("{PLAYER}",), 1)
    kos("EN {PLAYER}! placeholders=() (metin)", "{PLAYER}!", "eng_Latn", (), 1)

    print("[B] T2-1 -- `?` / U+FF01 tek basina bolunce cumle kaybi (gercek model)")
    for etiket, metin, kaynak, anahtarlar in [
        ("EN 'Are you ready? The village...'", "Are you ready? The village elder is waiting for you.", "eng_Latn", ("hazır", "bekliyor")),
        ("JP 'Tomare! Mura no...' (U+FF01)", "止まれ！村の長老があなたを待っています。", "jpn_Jpan", ("dur", "bekliyor")),
        ("JP 'Matte! Hontou ni...' (U+FF01)", "待って！本当に行くの？", "jpn_Jpan", ()),  # feedback-B: yalniz parca sayisi (2 -> 2)
    ]:
        GIDEN.clear()
        r = p.translate(istek(metin, kaynak))
        c = r.translations[0].lower()
        giden = sum(GIDEN)
        bulunan = {a: (a in c) for a in anahtarlar}
        ok = giden == 2 and all(bulunan.values())
        ihlal += 0 if ok else 1
        print(f"  {'ok' if ok else 'IHLAL':5s} {etiket:34s} parca={len(cumlelere_bol(metin))} giden={giden} (beklenen 2)"
              f" uzunluk={len(c)} anahtarlar={bulunan}")
    p.close()
    print()
    print(f"OLCUM-4: {'TEMIZ' if ihlal == 0 else str(ihlal) + ' IHLAL'}")
    return 0 if ihlal == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
