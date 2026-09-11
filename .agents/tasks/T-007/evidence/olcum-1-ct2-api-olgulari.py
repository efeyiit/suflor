"""T-007 implementer on olcumu 1 -- gercek kutuphane API olgulari (ayri surec, test DEGIL).

Stdout'a YALNIZ ASCII; hicbir ceviri/kaynak metni basilmaz (PROTOKOL 7) --
yalniz sayilar, tipler, bool ve hata sinif adlari.
"""
from __future__ import annotations

import inspect
import json
import shutil
import sys
import tempfile
import time
from pathlib import Path

KOK = Path(r"C:\Users\pc\Desktop\efe\çeviri uygulaması")
MODEL = KOK / "models" / "nllb-200-distilled-600M-ct2-int8"
FX = json.loads((KOK / ".agents/tasks/T-007/fixtures/cumleler.json").read_text(encoding="utf-8"))

import ctranslate2  # noqa: E402
import sentencepiece as spm  # noqa: E402

print(f"[0] ctranslate2 {ctranslate2.__version__}  sentencepiece {spm.__version__}  python {sys.version.split()[0]}")
print(f"[0] repo yolu ASCII mi: {str(MODEL).isascii()}  (beklenen False: 'ceviri' -> c-cedilla)")

# --- 1 sentencepiece: model_file ASCII-disi mutlak yol vs model_proto=bytes (C5, K7) ---
try:
    spm.SentencePieceProcessor(model_file=str(MODEL / "sentencepiece.bpe.model"))
    print("[1] model_file=<ASCII-disi mutlak yol> -> ACILDI (beklenmiyordu)")
except Exception as e:  # noqa: BLE001
    print(f"[1] model_file=<ASCII-disi mutlak yol> -> {type(e).__name__} (C5 dogrulandi)")
sp = spm.SentencePieceProcessor(model_proto=(MODEL / "sentencepiece.bpe.model").read_bytes())
print(f"[1] model_proto=bytes -> acildi, vocab={sp.get_piece_size()}")
enc = sp.encode(FX["JP"][0], out_type=str)
print(f"[1] encode(out_type=str) tip={type(enc).__name__}, eleman tipi={type(enc[0]).__name__}, n={len(enc)}")
dec = sp.decode(enc)
print(f"[1] decode(list[str]) tip={type(dec).__name__}, kaynakla ayni mi={dec == FX['JP'][0]}")
print(f"[1] encode('') -> {sp.encode('', out_type=str)!r}; encode('   ') -> {sp.encode('   ', out_type=str)!r}")
print(f"[1] encode(chr(0x3002)*3) uzunluk -> {len(sp.encode(chr(0x3002)*3, out_type=str))}")

# --- 2 ctranslate2: Translator kurulumu, mutlak ASCII-disi yol (C5: CT2 acabiliyor) ---
t0 = time.perf_counter()
tr = ctranslate2.Translator(str(MODEL.resolve()), device="cpu", compute_type="int8", inter_threads=1, intra_threads=8)
print(f"[2] Translator(<ASCII-disi mutlak yol>) -> OK, kurulum {1000*(time.perf_counter()-t0):.0f} ms")
doc = (ctranslate2.Translator.translate_batch.__doc__ or "").splitlines()
imza = [ln for ln in doc if "translate_batch(" in ln]
print(f"[2] translate_batch imza satiri: {imza[0].strip()[:200] if imza else 'YOK'}")
try:
    print(f"[2] inspect.signature: {inspect.signature(ctranslate2.Translator.translate_batch)}"[:300])
except (TypeError, ValueError) as e:
    print(f"[2] inspect.signature -> {type(e).__name__} (pybind)")


def tok(cumleler: list[str], kod: str) -> list[list[str]]:
    return [[kod] + sp.encode(c, out_type=str) + ["</s>"] for c in cumleler]


# --- 3 cagri bicimi: konumsal `source` vs anahtar `tokens=` (KRT D2) ---
t = tok(FX["JP"], "jpn_Jpan")
out = tr.translate_batch(t, target_prefix=[["tur_Latn"]] * len(t), beam_size=4, max_decoding_length=256)
print(f"[3] konumsal cagri -> OK, cikti tipi={type(out).__name__}, n={len(out)}, eleman tipi={type(out[0]).__name__}")
try:
    tr.translate_batch(tokens=t, target_prefix=[["tur_Latn"]] * len(t), beam_size=4, max_decoding_length=256)
    print("[3] tokens= anahtarli cagri -> OK (beklenmiyordu)")
except TypeError as e:
    print(f"[3] tokens= anahtarli cagri -> TypeError (KRT D2 dogrulandi): {str(e)[:80]}")
try:
    tr.translate_batch(source=t, target_prefix=[["tur_Latn"]] * len(t), beam_size=4, max_decoding_length=256)
    print("[3] source= anahtarli cagri -> OK")
except TypeError as e:
    print(f"[3] source= anahtarli cagri -> TypeError: {str(e)[:80]}")

# --- 4 cikti bicimi: hypotheses[0][0] hedef belirteci, </s> yok, sayi esit ---
h = out[0].hypotheses
print(f"[4] hypotheses tip={type(h).__name__}, adet={len(h)}, hyp[0] tip={type(h[0]).__name__}, token tipi={type(h[0][0]).__name__}")
print(f"[4] her ciktida hyp[0][0]=='tur_Latn': {all(o.hypotheses[0][0] == 'tur_Latn' for o in out)}")
print(f"[4] herhangi bir hyp'de '</s>' var mi: {any('</s>' in o.hypotheses[0] for o in out)}")
print(f"[4] cikti sayisi == girdi sayisi: {len(out) == len(t)}; decode([1:]) bos olan: {sum(1 for o in out if not sp.decode(o.hypotheses[0][1:]).strip())}")
print(f"[4] TranslationResult ozellikleri: {[a for a in dir(out[0]) if not a.startswith('_')]}")

# --- 5 repetition_penalty=1.0 acik vs gecilmemis -> ayni hipotezler (KRT D1) ---
tk = tok(FX["KR"], "kor_Hang")
a = tr.translate_batch(tk, target_prefix=[["tur_Latn"]] * 2, beam_size=4, max_decoding_length=256)
b = tr.translate_batch(tk, target_prefix=[["tur_Latn"]] * 2, beam_size=4, max_decoding_length=256, repetition_penalty=1.0)
print(f"[5] rp=1.0 acik == gecilmemis: {[x.hypotheses[0] for x in a] == [y.hypotheses[0] for y in b]}")

# --- 6 bos batch ve target_prefix sayi uyusmazligi ---
print(f"[6] bos batch -> {tr.translate_batch([], target_prefix=[], beam_size=4, max_decoding_length=256)!r}")
try:
    tr.translate_batch(t[:2], target_prefix=[["tur_Latn"]] * 3, beam_size=4, max_decoding_length=256)
    print("[6] target_prefix 3 / source 2 -> hata YOK")
except Exception as e:  # noqa: BLE001
    print(f"[6] target_prefix 3 / source 2 -> {type(e).__name__}: {str(e)[:70]}")

# --- 7 sifir bayt model.bin / eksik dosya -> CT2 hata sinifi (KRT O4) ---
with tempfile.TemporaryDirectory() as td:
    d = Path(td) / "m"
    d.mkdir()
    for ad in ("sentencepiece.bpe.model", "shared_vocabulary.txt", "config.json"):
        shutil.copy2(MODEL / ad, d / ad)
    (d / "model.bin").write_bytes(b"")
    try:
        ctranslate2.Translator(str(d), device="cpu", compute_type="int8")
        print("[7] sifir bayt model.bin -> Translator KURULDU (beklenmiyordu)")
    except Exception as e:  # noqa: BLE001
        print(f"[7] sifir bayt model.bin -> {type(e).__name__}: {str(e)[:60]}")
    print(f"[7] ctranslate2.contains_model(sifir bayt) = {ctranslate2.contains_model(str(d))}")
    (d / "model.bin").unlink()
    print(f"[7] ctranslate2.contains_model(model.bin yok) = {ctranslate2.contains_model(str(d))}")
try:
    spm.SentencePieceProcessor(model_proto=b"")
    print("[7] SentencePieceProcessor(model_proto=b'') -> kurulumda hata YOK")
    try:
        spm.SentencePieceProcessor(model_proto=b"").encode("x", out_type=str)
        print("[7] bos proto encode -> hata YOK")
    except Exception as e:  # noqa: BLE001
        print(f"[7] bos proto encode -> {type(e).__name__}")
except Exception as e:  # noqa: BLE001
    print(f"[7] SentencePieceProcessor(model_proto=b'') -> {type(e).__name__}")

# --- 8 weakref / unload ---
import weakref  # noqa: E402

print(f"[8] Translator weakref: {weakref.ref(tr)() is tr}; SentencePieceProcessor weakref: {weakref.ref(sp)() is sp}")
print(f"[8] Translator.unload_model var mi: {hasattr(tr, 'unload_model')}")

# --- 9 sure: JP 4 cumle tek batch, beam=4, 8 iplik, isinma sonrasi 7 kosum medyani ---
import statistics  # noqa: E402

for _ in range(2):
    tr.translate_batch(t, target_prefix=[["tur_Latn"]] * len(t), beam_size=4, max_decoding_length=256)
s = []
for _ in range(7):
    t0 = time.perf_counter()
    tr.translate_batch(t, target_prefix=[["tur_Latn"]] * len(t), beam_size=4, max_decoding_length=256)
    s.append((time.perf_counter() - t0) * 1000)
print(f"[9] JP 4 cumle tek batch beam=4 8 iplik: medyan {statistics.median(s):.0f} ms, min {min(s):.0f}, maks {max(s):.0f}")

print("OLCUM-1 BITTI")
