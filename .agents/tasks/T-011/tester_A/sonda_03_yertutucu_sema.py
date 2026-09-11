"""Sonda 3: yer tutucu sinirlari (K3), sema sinirlari (K6), hata mesaji sizintisi, saflik/kanal."""
from __future__ import annotations

import dataclasses
import io
import logging
import sys
import unicodedata
import warnings
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from yardimci import KOK, hit_ozet, seg, sozluk, sozluk_ham, u  # noqa: E402
from src.contracts.errors import ContractViolation  # noqa: E402
from src.contracts.models import TermHit  # noqa: E402
from src.translate.sozluk import GlossaryStore, terimleri_gom  # noqa: E402

OUT = KOK / ".agents/tasks/T-011/tester_A_evidence/sonda-03-yertutucu-sema.txt"
satirlar: list[str] = []


def yaz(*a: object) -> None:
    satirlar.append(" ".join(str(x) for x in a))


def dene(store, metin: str, yt=(), etiket: str = "") -> list:
    try:
        h = store.lookup(metin, yt)
    except Exception as e:  # noqa: BLE001
        yaz(f"{etiket:46s} metin={u(metin)!s:34s} yt={u(str(yt))!s:22s} -> HATA {type(e).__name__}: {u(str(e))}")
        return []
    yaz(f"{etiket:46s} metin={u(metin)!s:34s} yt={u(str(yt))!s:22s} -> {hit_ozet(h)}")
    return h


def gom_dene(segs, hits, etiket: str) -> None:
    try:
        o = terimleri_gom(segs, hits)
        yaz(f"{etiket:46s} -> OK {[u(s.text) for s in o]}")
    except Exception as e:  # noqa: BLE001
        yaz(f"{etiket:46s} -> {type(e).__name__}: {u(str(e))}")


yaz("== 1. yer tutucu: icerme / ortusme / bos / uzun / terim icinden ==")
p = sozluk(("Marcus", "Marcus"), ("マルクス", "Marcus"), ("PLAYER", "Oyuncu"), ("{0}{1}", "Cift"))
dene(p, "{0}{1}Marcus", ("{0}", "{0}{1}"), etiket="birbirini iceren yt")
dene(p, "{0}{1}Marcus", ("{0}{1}", "{0}"), etiket="ters sira")
dene(p, "{0}{1}Marcus", ("{0}",), etiket="yalniz {0} -> {1} metin, Marcus?")
dene(p, "{0}{1}Marcus", (), etiket="yt yok: {0}{1} TERIM -> hit?")
dene(p, "{0}{1}Marcus", ("0}{1",), etiket="ortusen yt: 0}{1 (kismi)")
dene(p, "Marcus", ("", "Marcus"), etiket="bos dize + terimle ayni yt")
dene(p, "Marcus Marcus", ("Marcus",), etiket="yt == terim, iki gecis")
dene(p, "Mar{0}cus", ("{0}",), etiket="yt terimin icinden geciyor")
dene(p, "Mar{0}cus", (), etiket="kontrol: yt bildirilmemis, { P* sinir -> Mar? cus?")
dene(p, "Marcus", ("x" * 10000,), etiket="cok uzun yt (metinde yok)")
dene(p, "Marcus", ("M",), etiket="tek harf yt terimin ilk harfi")
dene(p, "Marcus", ("s",), etiket="tek harf yt terimin son harfi")
dene(p, "Marcus", ("arc",), etiket="yt terimin ortasi")
dene(p, "Marcusマルクス", ("マルクス",), etiket="yt bitisik terim (yt basi sinir)")
dene(p, "マルクスMarcus", ("マルクス",), etiket="yt solda bitisik (yt sonu sinir)")
dene(p, "MARCUS", ("Marcus",), etiket="yt buyuk/kucuk DUYARLI -> MARCUS terim mi?")
dene(p, "marcus", ("MARCUS",), etiket="yt buyuk, metin kucuk")
nfd_yt = unicodedata.normalize("NFD", "{Ünlü}")
dene(p, nfd_yt + "Marcus", (nfd_yt,), etiket="NFD yt + NFD metin")
dene(p, "{Ünlü}Marcus", (nfd_yt,), etiket="NFC metin, NFD yt (yt NFC'lenir mi)")
dene(p, nfd_yt + "Marcus", ("{Ünlü}",), etiket="NFD metin, NFC yt")
dene(p, "Marcus", ["Marcus"], etiket="liste yt (Sequence)")
try:
    p.lookup("Marcus", "Marcus")
    yaz("  duz str yt -> KABUL (hata bekleniyordu)")
except TypeError as e:
    yaz(f"  duz str yt -> TypeError: {u(str(e))}")
try:
    p.lookup("Marcus", (1,))
    yaz("  int yt -> KABUL")
except TypeError as e:
    yaz(f"  int yt -> TypeError: {u(str(e))}")
try:
    p.lookup("Marcus", None)
    yaz("  None yt -> KABUL")
except TypeError as e:
    yaz(f"  None yt -> TypeError: {u(str(e))}")

yaz("== 1b. gom: yt ile ortusen hit (lookup atlar, elle verilirse ContractViolation mi) ==")
s1 = seg("{PLAYER}は村にいます", ("{PLAYER}",))
elle = TermHit(source_term="PLAYER", target_term="Oyuncu", start=1, end=7, segment_index=0)
gom_dene((s1,), (elle,), "yt icindeki hit elle")
s2 = seg("Marcus", ("Marcus",))
gom_dene((s2,), (TermHit("Marcus", "Marcus", 0, 6, 0),), "yt == terim, hit tam yt")
s3 = seg("Mar{0}cus", ("{0}",))
gom_dene((s3,), (TermHit("Mar{0}cus", "Marcus", 0, 9, 0),), "hit yt'yi kapsiyor")
# NFD segment + NFD yt + hit -> cikti text NFC, placeholders NFD -> yt artik text'te yok!
s4 = seg(nfd_yt + " Marcus", (nfd_yt,))
h4 = tuple(dataclasses.replace(h, segment_index=0) for h in p.lookup(s4.text, s4.placeholders))
yaz(f"  NFD seg: girdi yt in text = {s4.placeholders[0] in s4.text}; hits={hit_ozet(h4)}")
o4 = terimleri_gom((s4,), h4)
yaz(f"  NFD seg gom -> cikti yt in text = {o4[0].placeholders[0] in o4[0].text}; placeholders aynen={o4[0].placeholders == s4.placeholders}; text NFC={o4[0].text == unicodedata.normalize('NFC', o4[0].text)}")

yaz("== 2. sema sinirlari ==")
def sema(veri, etiket):
    try:
        st = sozluk_ham(veri, ad="cev.json")
        yaz(f"  {etiket:50s} -> KABUL len={len(st)} repr={st!r}")
        return st
    except Exception as e:  # noqa: BLE001
        yaz(f"  {etiket:50s} -> {type(e).__name__}: {u(str(e))[:140]}")
        return None

sema({"terimler": []}, "bos sozluk")
sema({"terimler": {}}, "terimler dict")
sema({"terimler": None}, "terimler null")
sema({"terimler": "abc"}, "terimler str")
sema([], "ust duzey liste")
sema({}, "ust duzey bos nesne")
sema({"terimler": [{"kaynak": "ab", "hedef": "X", "kisa_terim_izni": True}]}, "kisa_terim_izni true + 2 kodpoint")
sema({"terimler": [{"kaynak": "ab", "hedef": "X", "not": ""}]}, "not bos dize")
sema({"terimler": [{"kaynak": "ab", "hedef": "X", "not": None}]}, "not null")
sema({"terimler": [{"kaynak": "ab", "hedef": "X", "not": 5}]}, "not int")
sema({"terimler": [{"kaynak": "ab", "hedef": "  "}]}, "hedef yalniz bosluk")
sema({"terimler": [{"kaynak": "  ", "hedef": "X"}]}, "kaynak yalniz bosluk")
sema({"terimler": [{"kaynak": "a b", "hedef": "X"}]}, "kaynak ic bosluk (izinli mi)")
sema({"terimler": [{"kaynak": "ab", "hedef": "X Y"}]}, "hedef ic bosluk")
sema({"terimler": [{"kaynak": "ab", "hedef": "X\tY"}]}, "hedef ic tab")
sema({"terimler": [{"kaynak": "ab", "hedef": "X\nY"}]}, "hedef ic yeni satir")
sema({"terimler": [{"kaynak": "a\nb", "hedef": "X"}]}, "kaynak ic yeni satir")
sema({"terimler": [{"kaynak": "Değirmen", "hedef": "X"}, {"kaynak": unicodedata.normalize("NFD", "Değirmen"), "hedef": "Y"}]}, "yinelenen kaynak NFC/NFD")
sema({"terimler": [{"kaynak": "ab", "hedef": "X。"}]}, "hedef ideografik nokta")
sema({"terimler": [{"kaynak": "ab", "hedef": "X…"}]}, "hedef elipsis (yasak degil?)")
sema({"terimler": [{"kaynak": "ab", "hedef": "X;"}]}, "hedef noktali virgul")
sema({"terimler": [{"kaynak": "ab", "hedef": "X:"}]}, "hedef iki nokta")
sema({"terimler": [{"kaynak": "ab", "hedef": "X‼"}]}, "hedef cift unlem U+203C")
sema({"terimler": [{"kaynak": "ab", "hedef": "X？"}]}, "hedef tam genislik soru")
sema({"terimler": [{"kaynak": "ab", "hedef": "%s"}]}, "hedef %s (yer tutucu bicimi, yasak degil)")
sema({"terimler": [{"kaynak": "ab", "hedef": "<T0>"}]}, "hedef <T0>")
sema({"terimler": [{"kaynak": "ab", "hedef": "[Mill]"}]}, "hedef [Mill]")
sema({"terimler": [{"kaynak": "{0}", "hedef": "X"}]}, "kaynak {0} (yer tutucu bicimi kaynakta)")
sema({"terimler": [{"kaynak": "ab", "hedef": "X", "ozel_ad": True}]}, "v1 ozel_ad bayragi")
sema({"terimler": [{"kaynak": "ab", "hedef": "X", "kisa_terim_izni": 1}]}, "kisa_terim_izni int 1")
sema({"terimler": [{"kaynak": "ab", "hedef": "X", "kisa_terim_izni": None}]}, "kisa_terim_izni null")
sema({"terimler": [{"kaynak": "ab", "hedef": "X"}], "oyun": "Test", "surum": 2}, "ust duzey ek anahtar")
sema({"terimler": [{"kaynak": "ab", "hedef": "X"}, "str"]}, "kayit str")
sema({"terimler": [{"kaynak": "ab", "hedef": "X"}, None]}, "kayit null")
sema({"terimler": [{"kaynak": "ab", "hedef": "X"}, {"kaynak": "cd"}]}, "ikinci kayit hedef eksik (ILK hatali bildirilir)")
sema({"terimler": [{"kaynak": 5, "hedef": "X"}]}, "kaynak int")
sema({"terimler": [{"kaynak": "ab", "hedef": "X"}, {"kaynak": "ab", "hedef": "Y"}]}, "tekrar kaynak")
sema({"terimler": [{"kaynak": "AB", "hedef": "X"}, {"kaynak": "ab", "hedef": "Y"}]}, "tekrar kaynak buyuk/kucuk")
sema({"terimler": [{"kaynak": "İ", "hedef": "X", "kisa_terim_izni": True}]}, "tek kodpoint buyuk noktali I + izin")
sema({"terimler": [{"kaynak": "\U0001F600", "hedef": "X"}]}, "tek emoji kodpoint")
sema({"terimler": [{"kaynak": "\U0001F600\U0001F600", "hedef": "X"}]}, "iki emoji")
sema({"terimler": [{"kaynak": "ab", "hedef": "\U0001F600"}]}, "hedef emoji (ilk_harfi_buyut harf-disi)")
sema({"terimler": [{"kaynak": "ab", "hedef": "ışık"}]}, "hedef isik -> Isik")
sema({"terimler": [{"kaynak": "ab", "hedef": "ihtiyar"}]}, "hedef ihtiyar -> Ihtiyar noktali")
sema({"terimler": [{"kaynak": "ab", "hedef": "ﬁne"}]}, "hedef fi ligature -> upper 'FI'ne? (uzunluk degisir)")
sema({"terimler": [{"kaynak": "ab", "hedef": "ǆ"}]}, "hedef dz digraph U+01C6 -> upper U+01C4 (titlecase U+01C5?)")
sema({"terimler": [{"kaynak": "ab", "hedef": "ß"}]}, "hedef eszett -> upper 'SS'")
sema({"terimler": [{"kaynak": "a" * 10000, "hedef": "X"}]}, "10000 kodpoint kaynak")
sema({"terimler": [{"kaynak": "ab", "hedef": "X" * 10000}]}, "10000 kodpoint hedef")
sema({"terimler": [{"kaynak": "ab", "hedef": "X", "kaynak": "cd"}]}, "yinelenen JSON anahtari (son kazanir)")

yaz("== 2b. sema hatasi mesaj sizintisi: terim tasir (istenen), ContractViolation tasimaz ==")
try:
    sozluk_ham({"terimler": [{"kaynak": "GIZLI_TERIM_XYZ", "hedef": "St. Marcus"}]})
except ValueError as e:
    yaz(f"  sema ValueError terim tasiyor: {'GIZLI_TERIM_XYZ' in str(e)}; dosya adi tasiyor: {'.json' in str(e)}")
try:
    sozluk_ham({"terimler": "x"}, ad="GIZLIDOSYA.json")
except ValueError as e:
    yaz(f"  ust duzey hata dosya adi tasiyor: {'GIZLIDOSYA' in str(e)}")
try:
    GlossaryStore(KOK / "yok" / "GIZLIYOL.json")
except FileNotFoundError as e:
    yaz(f"  FileNotFoundError sarilmamis: {type(e).__name__}; mesaj yol tasiyor: {'GIZLIYOL' in str(e)}")
try:
    GlossaryStore(123)
except TypeError as e:
    yaz(f"  json_path int -> TypeError: {u(str(e))}")
td = Path(sozluk(("ab", "X")).yol).parent
kotu = td / "kotu.json"
kotu.write_bytes(b"{GIZLI_METIN_ABC")
try:
    GlossaryStore(kotu)
except ValueError as e:
    yaz(f"  bozuk JSON ValueError: dosya adi={'kotu.json' in str(e)}; icerik sizdi={'GIZLI_METIN_ABC' in str(e)}; mesaj={u(str(e))[:120]}")
bom = td / "bom.json"
bom.write_bytes(b"\xef\xbb\xbf" + '{"terimler": [{"kaynak": "ab", "hedef": "X"}]}'.encode("utf-8"))
yaz(f"  BOM'lu dosya: {len(GlossaryStore(bom))} terim")
utf16 = td / "u16.json"
utf16.write_bytes('{"terimler": [{"kaynak": "ab", "hedef": "X"}]}'.encode("utf-16"))
try:
    yaz(f"  UTF-16 dosya: {len(GlossaryStore(utf16))} terim")
except ValueError as e:
    yaz(f"  UTF-16 dosya -> ValueError: {u(str(e))[:100]}")
gecersiz = td / "gecersiz.json"
gecersiz.write_bytes(b'{"terimler": [{"kaynak": "\xff\xfe", "hedef": "X"}]}')
try:
    GlossaryStore(gecersiz)
    yaz("  gecersiz UTF-8 bayt -> KABUL?")
except (ValueError, UnicodeDecodeError) as e:
    yaz(f"  gecersiz UTF-8 -> {type(e).__name__} (ValueError alt sinifi mi: {isinstance(e, ValueError)}): {u(str(e))[:100]}")
dizin = td / "dizin.json"
dizin.mkdir()
try:
    GlossaryStore(dizin)
except OSError as e:
    yaz(f"  dizin yolu -> {type(e).__name__} (sarilmamis)")

yaz("== 2c. ContractViolation mesajlari metin/terim tasir mi ==")
gizli_metin = "GIZLIMETIN kelimesi burada"
gizli_seg = seg(gizli_metin)
kotu_hitler = [
    ("aralik disi", TermHit("GIZLITERIM", "GIZLIHEDEF", 0, 999, 0)),
    ("dilim farkli", TermHit("GIZLITERIM", "GIZLIHEDEF", 0, 10, 0)),
    ("start==end", TermHit("", "GIZLIHEDEF", 3, 3, 0)),
    ("negatif start", TermHit("GIZLITERIM", "GIZLIHEDEF", -1, 5, 0)),
    ("segment_index None", TermHit("GIZLIMETIN", "GIZLIHEDEF", 0, 10, None)),
    ("segment_index -1", TermHit("GIZLIMETIN", "GIZLIHEDEF", 0, 10, -1)),
    ("segment_index 1 (len 1)", TermHit("GIZLIMETIN", "GIZLIHEDEF", 0, 10, 1)),
    ("segment_index True", TermHit("GIZLIMETIN", "GIZLIHEDEF", 0, 10, True)),
    ("segment_index float", TermHit("GIZLIMETIN", "GIZLIHEDEF", 0, 10, 0.0)),
    ("bos target", TermHit("GIZLIMETIN", "", 0, 10, 0)),
    ("start bool", TermHit("GIZLIMETIN", "GIZLIHEDEF", False, 10, 0)),
    ("start float", TermHit("GIZLIMETIN", "GIZLIHEDEF", 0.0, 10, 0)),
    ("source_term None", TermHit(None, "GIZLIHEDEF", 0, 10, 0)),
    ("target None", TermHit("GIZLIMETIN", None, 0, 10, 0)),
]
for etiket, h in kotu_hitler:
    try:
        terimleri_gom((gizli_seg,), (h,))
        yaz(f"  {etiket:26s} -> KABUL EDILDI (ihlal bekleniyordu)")
    except ContractViolation as e:
        m = str(e)
        yaz(f"  {etiket:26s} -> CV; sizinti: metin={'GIZLIMETIN' in m} terim={'GIZLITERIM' in m} hedef={'GIZLIHEDEF' in m}; msg={u(m)[:100]}")
    except Exception as e:  # noqa: BLE001
        yaz(f"  {etiket:26s} -> BASKA HATA {type(e).__name__}: {u(str(e))[:100]}")
# ortusen iki hit
try:
    terimleri_gom((gizli_seg,), (TermHit("GIZLIMETIN", "A", 0, 10, 0), TermHit("METIN kel", "B", 5, 14, 0)))
except ContractViolation as e:
    yaz(f"  ortusen iki hit -> CV; sizinti metin={'GIZLI' in str(e)}; msg={u(str(e))[:100]}")
# bitisik iki hit (a.end == b.start) serbest
try:
    o = terimleri_gom((gizli_seg,), (TermHit("GIZLI", "A", 0, 5, 0), TermHit("METIN", "B", 5, 10, 0)))
    yaz(f"  bitisik iki hit -> OK: {u(o[0].text)!r}")
except ContractViolation as e:
    yaz(f"  bitisik iki hit -> CV: {u(str(e))}")
# hit TermHit degil
try:
    terimleri_gom((gizli_seg,), ("GIZLITERIM",))
except ContractViolation as e:
    yaz(f"  hit str -> CV; sizinti={'GIZLITERIM' in str(e)}; msg={u(str(e))[:100]}")
# segments ogesi Segment degil (hit var)
try:
    terimleri_gom(("GIZLIMETIN",), (TermHit("GIZLIMETIN", "X", 0, 10, 0),))
except ContractViolation as e:
    yaz(f"  segment str -> CV; sizinti={'GIZLIMETIN' in str(e)}; msg={u(str(e))[:100]}")
# segments ogesi Segment degil, hits BOS -> sessiz gecer mi?
o = terimleri_gom(("GIZLIMETIN", 5), ())
yaz(f"  segments bozuk + hits bos -> {type(o).__name__} len {len(o)} (denetim yok, aynen doner)")
# lookup_segments bozuk segment
try:
    p.lookup_segments(("GIZLIMETIN",))
except ContractViolation as e:
    yaz(f"  lookup_segments str -> CV; sizinti={'GIZLIMETIN' in str(e)}; msg={u(str(e))[:100]}")
try:
    p.lookup(123)
except TypeError as e:
    yaz(f"  lookup int -> TypeError: {u(str(e))}")
try:
    p.lookup(None)
except TypeError as e:
    yaz(f"  lookup None -> TypeError: {u(str(e))}")

yaz("== 3. saflik/kanal: 0 bayt stdout/stderr/log/warnings ==")
out, err = io.StringIO(), io.StringIO()
kayit = io.StringIO()
hnd = logging.StreamHandler(kayit)
kok = logging.getLogger()
eski = kok.level
kok.setLevel(logging.DEBUG)
kok.addHandler(hnd)
with warnings.catch_warnings(record=True) as w, redirect_stdout(out), redirect_stderr(err):
    warnings.simplefilter("always")
    st = sozluk(("マルクス", "Marcus"), ("方앗간", "X"), ("Marcus", "Marcus"))
    for _ in range(3):
        hs = st.lookup("長老マルクスが Marcus 방앗간을", ("{0}",))
        terimleri_gom((seg("長老マルクスが Marcus"),), tuple(dataclasses.replace(h, segment_index=0) for h in st.lookup("長老マルクスが Marcus")))
    repr(st); str(st); len(st); st.terimler; st.yol
    for etiket, h in kotu_hitler[:4]:
        try:
            terimleri_gom((gizli_seg,), (h,))
        except ContractViolation:
            pass
    try:
        sozluk_ham({"terimler": [{"kaynak": "x", "hedef": "Y"}]})
    except ValueError:
        pass
    try:
        GlossaryStore(KOK / "yok.json")
    except FileNotFoundError:
        pass
kok.removeHandler(hnd)
kok.setLevel(eski)
yaz(f"  stdout={len(out.getvalue())} stderr={len(err.getvalue())} log={len(kayit.getvalue())} warnings={len(w)}")
yaz(f"  repr terim tasir mi: {'Marcus' in repr(st)} ; repr={repr(st)}")
yaz(f"  'src' logger handler sayisi: {len(logging.getLogger('src').handlers)}; 'src.translate.sozluk' handler: {len(logging.getLogger('src.translate.sozluk').handlers)}")
yaz(f"  logging.Logger.manager'da sozluk logger var mi: {'src.translate.sozluk' in logging.Logger.manager.loggerDict}")

yaz("== 3b. dosya silinince lookup ==")
st2 = sozluk(("Marcus", "Marcus"))
Path(st2.yol).unlink()
yaz(f"  dosya var: {Path(st2.yol).exists()}; lookup: {hit_ozet(st2.lookup('Marcus geldi'))}")

yaz("== 3c. determinizm: ayni girdi iki kez, yeni liste ==")
a1 = p.lookup("Marcus PLAYER マルクス")
a2 = p.lookup("Marcus PLAYER マルクス")
yaz(f"  esit={a1 == a2} ayni nesne={a1 is a2}")
yaz(f"  terimler tuple degismez: {type(p.terimler).__name__}")

OUT.write_text("\n".join(satirlar) + "\n", encoding="utf-8")
print(f"yazildi: {len(satirlar)} satir -> {OUT.name}")
