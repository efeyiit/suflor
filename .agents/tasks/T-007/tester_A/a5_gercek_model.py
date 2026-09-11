"""Tester-A · A5 — gerçek modelle ayrı süreç (K1 bariyeri DIŞI).

    python .agents/tasks/T-007/tester_A/a5_gercek_model.py

Stdout'a YALNIZ sayı/boolean/uzunluk yazılır; hiçbir çeviri ya da kaynak
metni basılmaz (PROTOKOL §6/7). Model, sağlayıcı ve kütüphane adı da
yazılmaz; `provider_id` yalnız beklenen sabitle EŞİTLİK olarak raporlanır.

Bölümler:
  [1] 4 dil × 2 cümle → `TranslationResult` alanları (tip, hizalama, boş değil)
  [2] aynı dil üç kod biçimiyle (NLLB / ISO 639-1 / OcrLanguage) → çıktı AYNI mı
  [3] beam=1 vs beam=4 → kaç cümle farklı (rapor, bulgu değil) + süre
  [4] 50 segment tek batch → duvar saati vs `latency_ms` tutarlılığı; ilk çağrı kurulum hariç
  [5] keskinlik sondaları: yalnız yer tutucu cümlesi (`{0}.`, `{PLAYER}!`), ASCII tırnak
      yapışması (`A. "B."`), boş hipotez var mı, `3.5 km.` rakam korunumu
"""
from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(KOK))

from src.contracts.models import Rect, Segment, TranslationRequest, TranslationResult  # noqa: E402
from src.translate.local_nmt import LocalNmtProvider, cumlelere_bol  # noqa: E402

MODEL = KOK / "models" / "nllb-200-distilled-600M-ct2-int8"
FX = json.loads((KOK / ".agents/tasks/T-007/fixtures/cumleler.json").read_text(encoding="utf-8"))
BEKLENEN_KIMLIK = "local-nmt-nllb200-600m-int8"
NLLB = {"JP": "jpn_Jpan", "KR": "kor_Hang", "ZH": "zho_Hans", "EN": "eng_Latn"}
UC_BICIM = {
    "JP": ("jpn_Jpan", "ja", "japan"),
    "KR": ("kor_Hang", "ko", "korean"),
    "ZH": ("zho_Hans", "zh", "chinese"),
    "EN": ("eng_Latn", "en", "english"),
}
CUMLELER: dict[str, list[str]] = {
    "JP": FX["JP"][1:3],
    "KR": FX["KR"],
    "ZH": ["村长在等你。", "沿着东边的路走，经过磨坊。"],
    "EN": FX["EN"],
}

ihlal_sayisi = 0


def satir(etiket: str, ok: bool, detay: str) -> None:
    global ihlal_sayisi
    if not ok:
        ihlal_sayisi += 1
    print(f"  {'ok    ' if ok else 'IHLAL '} {etiket}: {detay}")


def istek(metinler: list[str], kaynak: str, ph: tuple[str, ...] = ()) -> TranslationRequest:
    return TranslationRequest(
        segments=tuple(Segment(text=t, bbox=Rect(0, i * 40, 800, 36), placeholders=ph) for i, t in enumerate(metinler)),
        source_lang=kaynak,
        target_lang="tr",
    )


def sonuc_sozlesmesi(r: TranslationResult, n: int, nllb: str) -> tuple[bool, str]:
    kosullar = {
        "tuple": type(r.translations) is tuple,
        "n": len(r.translations) == n,
        "str": all(type(t) is str for t in r.translations),
        "bos_degil": all(t.strip() for t in r.translations),
        "kimlik": r.provider_id == BEKLENEN_KIMLIK,
        "latency_float": type(r.latency_ms) is float,
        "latency_ge0": r.latency_ms >= 0.0,
        "from_cache_False": r.from_cache is False,
        "partial_False": r.partial is False,
        "detected": r.detected_lang == nllb,
    }
    return all(kosullar.values()), " ".join(f"{k}={'1' if v else '0'}" for k, v in kosullar.items())


def main() -> int:
    print("Tester-A A5 -- gercek model, ayri surec")
    if not (MODEL / "model.bin").exists():
        print("  IHLAL  model dizini yok")
        return 1

    # [4a] ilk cagri: duvar saati kurulumu icerir, latency_ms icermez
    p = LocalNmtProvider(model_dir=MODEL, threads=8)
    t0 = time.perf_counter()
    r = p.translate(istek(CUMLELER["JP"], "jpn_Jpan"))
    duvar_ilk = (time.perf_counter() - t0) * 1000
    satir("[4a] ilk cagri kurulum haric", r.latency_ms < duvar_ilk * 0.8,
          f"duvar={duvar_ilk:.0f} ms latency_ms={r.latency_ms:.0f} ms fark={duvar_ilk - r.latency_ms:.0f} ms")

    # [1] dort dil x iki cumle
    ciktilar: dict[str, tuple[str, ...]] = {}
    for dil, metinler in CUMLELER.items():
        r = p.translate(istek(metinler, NLLB[dil]))
        ok, detay = sonuc_sozlesmesi(r, 2, NLLB[dil])
        satir(f"[1] {dil} 2 cumle", ok, detay + f" uzunluklar={[len(t) for t in r.translations]}")
        ciktilar[dil] = r.translations

    # [2] uc kod bicimi -> ayni cikti
    for dil, bicimler in UC_BICIM.items():
        sonuclar = [p.translate(istek(CUMLELER[dil], kod)).translations for kod in bicimler]
        sonuclar += [p.translate(istek(CUMLELER[dil], kod.upper())).translations for kod in bicimler]
        ayni = all(s == sonuclar[0] for s in sonuclar)
        satir(f"[2] {dil} 3 bicim x 2 harf = 6 kod ayni cikti", ayni, f"ayni={ayni} detected={[p.translate(istek(CUMLELER[dil][:1], kod)).detected_lang == NLLB[dil] for kod in bicimler]}")
    # deterministiklik: ayni kodla iki kosum ayni mi (yukaridaki karsilastirmanin on kosulu)
    a = p.translate(istek(CUMLELER["JP"], "jpn_Jpan")).translations
    b = p.translate(istek(CUMLELER["JP"], "jpn_Jpan")).translations
    satir("[2] deterministik (ayni girdi iki kez)", a == b, f"ayni={a == b}")

    # [3] beam=1 vs beam=4 (rapor)
    p1 = LocalNmtProvider(model_dir=MODEL, threads=8, beam_size=1)
    tum = [(dil, m) for dil, ms in CUMLELER.items() for m in ms]
    farkli = 0
    s1: list[float] = []
    s4: list[float] = []
    for dil, m in tum:
        r4 = p.translate(istek([m], NLLB[dil]))
        r1 = p1.translate(istek([m], NLLB[dil]))
        farkli += r1.translations != r4.translations
        s1.append(r1.latency_ms)
        s4.append(r4.latency_ms)
    print(f"  rapor  [3] beam=1 vs beam=4: 8 cumlenin {farkli} tanesi farkli; tek cumle latency medyan beam1={statistics.median(s1):.0f} ms beam4={statistics.median(s4):.0f} ms")
    p1.close()

    # [4] 50 segment tek batch: duvar saati vs latency_ms
    elli = [CUMLELER["JP"][i % 2] for i in range(50)]
    rq = istek(elli, "jpn_Jpan")
    p.translate(rq)  # isinma
    farklar: list[float] = []
    sureler: list[float] = []
    for _ in range(3):
        t0 = time.perf_counter()
        r = p.translate(rq)
        duvar = (time.perf_counter() - t0) * 1000
        farklar.append(duvar - r.latency_ms)
        sureler.append(r.latency_ms)
    satir("[4] 50 segment tek batch hizali + latency tutarli", len(r.translations) == 50 and all(t.strip() for t in r.translations) and max(farklar) < 20,
          f"n={len(r.translations)} latency_ms medyan={statistics.median(sureler):.0f} ms ({statistics.median(sureler) / 50:.0f} ms/cumle) duvar-latency farki maks={max(farklar):.2f} ms")

    # [5] keskinlik sondalari (bulgu degil, kayit) -- cikti METNI basilmaz
    def sonda(etiket: str, metin: str, kaynak: str, ph: tuple[str, ...] = ()) -> str:
        r = p.translate(istek([metin], kaynak, ph))
        c = r.translations[0]
        parcalar = cumlelere_bol(metin)
        return (f"parca={len(parcalar)} cikti_uzunluk={len(c)} bos={not c.strip()} "
                f"tirnak_kaynak={metin.count(chr(34))} tirnak_cikti={c.count(chr(34))} "
                f"uydurma_isareti={'hayır' in c.lower() or 'hayir' in c.lower()} "
                f"yer_tutucu_hepsi_var={all(x in c for x in ph)} "
                f"rakamlar_korundu={all(d in c for d in metin if d.isdigit())}")

    print("  rapor  [5a] yalniz yer tutucu cumlesi `{0}.` (EN): " + sonda("", "{0}. Take the road.", "eng_Latn", ("{0}",)))
    print("  rapor  [5b] `{PLAYER}! Wait!` (EN): " + sonda("", "{PLAYER}! Wait!", "eng_Latn", ("{PLAYER}",)))
    print("  rapor  [5b2] `{PLAYER}!` TEK BASINA (EN): " + sonda("", "{PLAYER}!", "eng_Latn", ("{PLAYER}",)))
    print("  rapor  [5b3] `Wait!` TEK BASINA (EN): " + sonda("", "Wait!", "eng_Latn"))
    print("  rapor  [5b4] `{0}!` TEK BASINA (EN): " + sonda("", "{0}!", "eng_Latn", ("{0}",)))
    print("  rapor  [5b5] `{0}` TEK BASINA, terminatorsuz (EN): " + sonda("", "{0}", "eng_Latn", ("{0}",)))
    print("  rapor  [5b6] `%s!` TEK BASINA (EN): " + sonda("", "%s!", "eng_Latn", ("%s",)))
    print("  rapor  [5c] `{0}` + JP nokta tek basina (JP): " + sonda("", "{0}。", "jpn_Jpan", ("{0}",)))
    print("  rapor  [5d] ASCII tirnak yapismasi `A. \"B.\"` (EN): " + sonda("", 'The elder spoke. "Go east."', "eng_Latn"))
    print("  rapor  [5e] ayni metin onceden dogru bolunmus 2 segment (EN): "
          + str([len(t) for t in p.translate(istek(["The elder spoke.", '"Go east."'], "eng_Latn")).translations]))
    print("  rapor  [5f] `3.5 km.` (EN): " + sonda("", "Walk 3.5 km. Then rest.", "eng_Latn"))
    print("  rapor  [5g] `Dr. Smith.` (EN): " + sonda("", "Dr. Smith is waiting.", "eng_Latn"))
    print("  rapor  [5h] tek rakam `5` (EN): " + sonda("", "5", "eng_Latn"))
    print("  rapor  [5i] tam genislik nokta U+FF0E `A.B.` (JP, bolunmez): " + sonda("", "村の長老があなたを待っています．水車小屋を過ぎて東の道を行きなさい．", "jpn_Jpan"))
    print("  rapor  [5j] KR unlem/soru `A! B?` (KR): " + sonda("", "기다려! 정말 가는 거야?", "kor_Hang"))

    # [5k] tam genislik nokta (U+FF0E) bolunmedigi icin C6/C8 kaynasmasi geri geliyor mu? real_check #3/#4 olcusuyle
    import re as _re
    def _cumle_say(t: str) -> int:
        return len([x for x in _re.split(r"[.!?]+", t) if x.strip()])
    jp_ff0e = FX["JP"][1].rstrip("。") + "．" + FX["JP"][2].rstrip("。") + "．"
    c_ff0e = p.translate(istek([jp_ff0e], "jpn_Jpan")).translations[0].lower()
    c_bol = " ".join(p.translate(istek(FX["JP"][1:3], "jpn_Jpan")).translations).lower()
    print(f"  rapor  [5k] U+FF0E ile 2 cumle TEK parca: cumle={_cumle_say(c_ff0e)} bekliyor={'bekliyor' in c_ff0e} dogu={'doğu' in c_ff0e or 'dogu' in c_ff0e} | ayni cumleler U+3002 ile (2 parca): cumle={_cumle_say(c_bol)} bekliyor={'bekliyor' in c_bol} dogu={'doğu' in c_bol or 'dogu' in c_bol}")
    # [5l] ASCII tirnak yapismasi: tirnak hangi parcada bitiyor?
    c1 = p.translate(istek(['The elder spoke. "'], "eng_Latn")).translations[0]
    c2 = p.translate(istek(['Go east."'], "eng_Latn")).translations[0]
    c3 = p.translate(istek(['"Go east."'], "eng_Latn")).translations[0]
    print(f"  rapor  [5l] yapismis ilk parca `A. \"` -> cikti tirnak sayisi={c1.count(chr(34))} sonda_tirnak={c1.endswith(chr(34))} | ikinci parca `B.\"` -> tirnak={c2.count(chr(34))} basta={c2.startswith(chr(34))} sonda={c2.endswith(chr(34))} | dogru `\"B.\"` -> tirnak={c3.count(chr(34))} basta={c3.startswith(chr(34))} sonda={c3.endswith(chr(34))}")
    # [5m] bos hipotez: model hic bos cikti veriyor mu (tek karakterli girdiler)
    tekler = ["5", "A", "x", "1.", "Lv.5", "OK", "Z!", "9?"]
    r = p.translate(istek(tekler, "eng_Latn"))
    print(f"  rapor  [5m] {len(tekler)} kisa girdi -> bos cikti sayisi={sum(1 for t in r.translations if not t.strip())} uzunluklar={[len(t) for t in r.translations]}")

    p.close()
    print()
    print(f"A5: {ihlal_sayisi} IHLAL" if ihlal_sayisi else "A5: TEMIZ")
    return 1 if ihlal_sayisi else 0


if __name__ == "__main__":
    raise SystemExit(main())
