"""TESTER-B mutant kiti (T-008, mercek B: test kalitesi) -- bes kapinin AYIRT ETME GUCU.

Soru (tur 2: 76 test): "birim testleri + real_check + mypy + kapsam + tam takim, `satirlari_birlestir`i
gercekten olcuyor mu?" Yontem: kaynagi bilerek bozup HANGI KAPININ yakaladigini
saymak. Hicbir kapinin yakalamadigi, urunu bozan ve ERISILEBILIR bir mutant, o
degismezin olcusunun BOS oldugunu kanitlar. Davranis-esdeger KONTROL mutantlari
(C-xx) kacmak ZORUNDADIR; yakalanirlarsa olcu yanlis pozitif veriyordur.

`src/`, `tests/`, `real_check.py`, `conftest.py` DEGISTIRILMEZ: depo, scratchpad
altindaki bir AYNA AGACINA kopyalanir (models/ junction ile baglanir, olmazsa
kopyalanir -- real_check #3 gercek NMT ile kosar); mutasyon orada yapilir, her
mutanttan sonra dosya depodan geri yazilir.

Kosum (depo kokunden):
    T008_TB_SCRATCH=<dizin> python .agents/tasks/T-008/tester_B/mutant_kiti.py [--taban] [--jsonl DOSYA] [mutant_id ...]
    T008_TB_DRY=1 ...   -> yalniz yama hedeflerini dogrular + py_compile, kapi kosmaz

Kapilar paketin bes kabul komutudur (packet.md `acceptance`); pytest'e yalniz
`-p no:cacheprovider` ve `-rfE` eklenmistir. real_check YALNIZ ASCII bastigi icin
PYTHONIOENCODING verilmez (cp1254 konsul kosullari). Her mutantin tahmini
("beklenen") kosumdan ONCE yazilmistir.
"""
from __future__ import annotations

import json
import os
import py_compile
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

DEPO = Path(__file__).resolve().parents[4]
SCRATCH = Path(os.environ.get("T008_TB_SCRATCH", tempfile.gettempdir()))
KOK = SCRATCH / "t008_tester_B_ayna"
DRY = os.environ.get("T008_TB_DRY", "") == "1"

KAYNAK = "src/ocr/satir_birlestirici.py"
TEST = "tests/unit/ocr/test_satir_birlestirici.py"

AYNALANAN_DIZINLER = ("src", "tests", ".agents/tasks/T-006/fixtures", ".agents/tasks/T-008/fixtures")
AYNALANAN_DOSYALAR = (".agents/tasks/T-004/olcu_kiti.py", ".agents/tasks/T-008/real_check.py")
MODEL_DIZINI = "models/nllb-200-distilled-600M-ct2-int8"
MODEL_DOSYALARI = ("model.bin", "sentencepiece.bpe.model", "shared_vocabulary.txt", "config.json")

KAPILAR: list[tuple[str, list[str]]] = [
    ("G1-mypy", [sys.executable, "-m", "mypy", "--strict", "--explicit-package-bases", KAYNAK]),
    ("G2-birim", [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-rfE", TEST]),
    ("G3-real", [sys.executable, ".agents/tasks/T-008/real_check.py"]),
    ("G4-kapsam", [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-rfE", TEST,
                   "--cov=src.ocr.satir_birlestirici", "--cov-fail-under=95", "--cov-report=term-missing"]),
    ("G5-tum", [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-rfE", "tests"]),
]


@dataclass
class Mutant:
    mid: str
    yamalar: list[tuple[str, str]]
    aciklama: str
    sinif: str
    beklenen: str  # kosumdan ONCE yazilan tahmin
    kontrol: bool = False
    urun_etkisi: str = ""


def _y(eski: str, yeni: str) -> tuple[str, str]:
    return (eski, yeni)


# --- yama hedefleri (kaynaktan birebir; tekillik kurulumda dogrulanir) ---------------
DIKEY = "DIKEY_ORTUSME_ESIGI: Final[float] = 0.5\n"
YATAY = "YATAY_BOSLUK_ESIGI: Final[float] = 0.75\n"
CJK_TUPLE = (
    '_CJK_AD_PARCALARI: Final[tuple[str, ...]] = (\n'
    '    "HIRAGANA",\n'
    '    "KATAKANA",\n'
    '    "CJK UNIFIED IDEOGRAPH",\n'
    '    "CJK COMPATIBILITY IDEOGRAPH",\n'
    ")\n"
)
ILK_SIRALAMA = "    sirali = sorted(enumerate(blocks), key=lambda c: (c[1].bbox.y, c[1].bbox.x, c[0]))\n"
YUZEY_ANAHTAR = "        anahtar = (blok.bbox.monitor_index, blok.bbox.dpi_scale)\n"
SON_SIRALAMA = "    sonuc.sort(key=lambda c: c[0])\n"
YOZLASMIS = "    return r.h <= 0 or r.w <= 0\n"
DIKEY_DONUS = "    return ortusme >= DIKEY_ORTUSME_ESIGI * min(a.h, b.h)\n"
X_ILERLEME = "    if not aday.x > son.x:\n        return False\n"
BOSLUK_DONUS = "    return bosluk <= YATAY_BOSLUK_ESIGI * min(son.h, aday.h)\n"
# tur 2 (T2-1): satir referansi = EN KISA blok; tur 1 hedefi `satirlar[-1][0][1].bbox` artik yok
REF_KOSUL = "        if referans is not None and _dikey_ortusme_yeterli(referans, kutu):\n"
REF_GUNCELLE = "            if kutu.h < referans.h:\n                referans = kutu\n"
REF_EKLE_GUNCELLE = "            satirlar[-1].append(oge)\n" + REF_GUNCELLE
X_SIRALI = "    x_sirali = sorted(satir, key=lambda c: (c[1].bbox.x, c[1].bbox.y, c[0]))\n"
GRUP_ILK = "            ilk = gruplar[-1][0][1].bbox\n"
GRUP_SON = "            son = gruplar[-1][-1][1].bbox\n"
GRUP_KOSUL = "            if _dikey_ortusme_yeterli(ilk, oge[1].bbox) and _yatay_komsu(son, oge[1].bbox):\n"
EN_KUCUK = "    en_kucuk_idx = min(idx for idx, _ in grup)\n"
TEK_PARCA = "        tek = grup[0][1]\n"
X_MIN = "    x = min(p.bbox.x for p in parcalar)\n"
BBOX_BLOK = (
    "    bbox = Rect(\n"
    "        x=x,\n"
    "        y=y,\n"
    "        w=sag - x,\n"
    "        h=alt - y,\n"
    "        monitor_index=ilk.monitor_index,\n"
    "        dpi_scale=ilk.dpi_scale,\n"
    "    )\n"
)
MON_ILK = "        monitor_index=ilk.monitor_index,\n"
GUVENLER = "    guvenler = [p.confidence for p in parcalar if not math.isnan(p.confidence)]\n"
CONF = "    confidence = min(guvenler) if guvenler else math.nan\n"
LINE_BOXES = "        line_boxes=tuple(p.bbox for p in parcalar),\n"
STRIP = "        metin = ham.strip()\n"
AYIRICI = '        if sonuc and not (onceki_cjk and cjk):\n            sonuc += " "\n'
ISALPHA = "        if karakter.isalpha():\n"
FONK_BAS = "    sonuc: list[tuple[_Anahtar, TextBlock]] = []\n"
ALL_SATIRI = '__all__ = ("satirlari_birlestir", "DIKEY_ORTUSME_ESIGI", "YATAY_BOSLUK_ESIGI")\n'

BIRLESIK_SON = (
    "            _pr = [g[1].bbox for g in gruplar[-1]]\n"
    "            _bx = min(r.x for r in _pr)\n"
    "            _by = min(r.y for r in _pr)\n"
    "            son = Rect(x=_bx, y=_by, w=max(r.right for r in _pr) - _bx, h=max(r.bottom for r in _pr) - _by)\n"
)

MUTANTLAR: list[Mutant] = [
    # ---- K2: esikler -------------------------------------------------------------------
    Mutant("M01", [_y(DIKEY, DIKEY.replace("0.5", "0.0"))],
           "K2: DIKEY 0.5 -> 0.0 (yalnizca degen kutular da ayni satir)", "K2 dikey esik", "G2 G4 G5",
           urun_etkisi="alt alta bitisik satirlar ayni satir sayilir"),
    Mutant("M02", [_y(DIKEY, DIKEY.replace("0.5", "0.9"))],
           "K2: DIKEY 0.5 -> 0.9 (KR y-titresimli kelimeler ayri satir)", "K2 dikey esik", "G2 G4 G5",
           urun_etkisi="KR 3. satir ortusme 34/41=0.83 -> 0.9 ile de gecer (elle hesap); yalniz 0.51 sinir testi"),
    Mutant("M03", [_y(YATAY, YATAY.replace("0.75", "0.6"))],
           "K2: YATAY 0.75 -> 0.6 (KR 0.57 hala birlesir; 0.74 sinir testi ayirir)", "K2 yatay esik", "G2 G4 G5",
           urun_etkisi="gri bolge alt ucu; gercek KR kelime boslugu (<=0.57) yine birlesir"),
    Mutant("M04", [_y(YATAY, YATAY.replace("0.75", "0.9"))],
           "K2: YATAY 0.75 -> 0.9 (1-em KR 0.78 birlesir)", "K2 yatay esik", "G2 G3 G4 G5 (#4c)",
           urun_etkisi="kr_menu 1-em etiket|deger birlesir"),
    Mutant("M05", [_y(YATAY, YATAY.replace("0.75", "1.0"))],
           "K2: YATAY 0.75 -> 1.0 (paket v1 degeri; KRT Y3)", "K2 yatay esik", "G2 G3 G4 G5 (#4c)",
           urun_etkisi="1-em bosluk sinifi (0.97-1.06) sinira dayanir; KR 0.78 birlesir"),
    Mutant("M06", [_y(YATAY, YATAY.replace("0.75", "10.0"))],
           "K2: YATAY 0.75 -> 10.0 (menu sutunlari birlesir)", "K2 yatay esik", "G2 G3 G4 G5 (#4c)",
           urun_etkisi="1-em menu etiket|deger tek blok; 13xh menu hala ayri (implementer ITIRAZ 2)"),
    Mutant("M07", [_y(BOSLUK_DONUS, BOSLUK_DONUS.replace("min(son.h, aday.h)", "max(son.h, aday.h)"))],
           "K2: bosluk esigi min(h) -> max(h)", "K2 min(h)", "G2 G4 G5",
           urun_etkisi="kisa kutunun yanindaki uzun kutu esigi buyutur -> yanlis birlestirme"),
    Mutant("M08", [_y(DIKEY_DONUS, DIKEY_DONUS.replace("min(a.h, b.h)", "max(a.h, b.h)"))],
           "K2: dikey esik min(h) -> max(h)", "K2 min(h)", "G2 G4 G5",
           urun_etkisi="kisa kutu uzun kutuyla ayni satira giremez; KR h 33-41 gecer, uzun kutu koprusu testi yakalar"),
    Mutant("M09", [_y(GRUP_SON, BIRLESIK_SON)],
           "K2 (Y2): komsuluk grubun BIRLESIK bbox'ina gore (birlesik h ile esik)", "K2 birlesik yukseklik", "G2 G4 G5",
           urun_etkisi="birlesik h buyudukce daha uzak kutular komsu olur (KRT Y2)"),
    Mutant("M10", [_y(X_ILERLEME, X_ILERLEME.replace("aday.x > son.x", "aday.x >= son.x"))],
           "K2: x ilerleme `>` -> `>=` (ayni x'teki cift tespit birlesir)", "K2 x ilerleme", "G2 G4 G5",
           urun_etkisi="cift tespit metni cogaltir"),
    Mutant("M11", [_y(YUZEY_ANAHTAR, "        anahtar = (0, blok.bbox.dpi_scale)\n")],
           "K2: monitor_index denetimi YOK (yuzey anahtarindan cikarildi)", "K2 monitor_index", "G2 G4 G5",
           urun_etkisi="iki monitorun ayni koordinatli kutulari birlesir"),
    Mutant("M12", [_y(YUZEY_ANAHTAR, "        anahtar = (blok.bbox.monitor_index, 0.0)\n")],
           "K2: dpi_scale denetimi YOK (KARAR; K5 'ilk parcadan' sessiz kopya)", "K2 dpi_scale", "G2 G4 G5",
           urun_etkisi="farkli dpi kutular birlesir, dpi ilk parcadan kopyalanir (normalizer K10 reddederdi)"),
    Mutant("M13", [_y(X_SIRALI, "    x_sirali = list(satir)\n")],
           "K2: satir ici x siralamasi YOK -- paket lafzinin (y,x) sirasi (ITIRAZ 1'in tersi: 17 -> 9)", "K2 satir ici siralama", "G2 G3 G4 G5",
           urun_etkisi="gercek KR 17 -> 9 blok; kelime kelime ceviri geri gelir"),
    Mutant("M14", [_y(DIKEY_DONUS, DIKEY_DONUS.replace(">=", ">"))],
           "K2: ortusme `>=` -> `>` (tam 0.5 ayrilir)", "K2 sinir", "G2 G4 G5",
           urun_etkisi="sinirda ayri satir"),
    Mutant("M15", [_y(BOSLUK_DONUS, BOSLUK_DONUS.replace("<=", "<"))],
           "K2: bosluk `<=` -> `<` (tam 0.75 ayrilir)", "K2 sinir", "G2 G4 G5",
           urun_etkisi="sinirda ayri blok"),
    Mutant("M16", [_y(REF_GUNCELLE, "            referans = kutu\n")],
           "K2 (tur 2 nisan): satir referansi EN KISA degil SON EKLENEN blok (= uyelik bir oncekiyle; merdiven tek satir)", "K2 satir referansi", "G2 G4 G5",
           urun_etkisi="merdiven dizilim tek satira toplanir"),
    Mutant("M17", [_y(GRUP_ILK, "            ilk = gruplar[-1][-1][1].bbox\n")],
           "K2: grup ici dikey referans ILK degil SON blok (uzun kutu koprusu)", "K2 grup referansi", "G2 G4 G5",
           urun_etkisi="uzun kutu iki satiri kopruler"),
    Mutant("M18", [_y(GRUP_KOSUL, "            if _yatay_komsu(son, oge[1].bbox):\n")],
           "K2: grup icinde dikey ortusme HIC denetlenmiyor (yalniz yatay)", "K2 grup referansi", "G2 G4 G5",
           urun_etkisi="ayni satirda x-komsu ama dikeyde ayrik kutular birlesir"),
    # ---- K3: betik ---------------------------------------------------------------------
    Mutant("M19", [_y(AYIRICI, '        if sonuc:\n            sonuc += " "\n')],
           "K3: CJK-CJK arasina da bosluk", "K3 CJK bosluk", "G2 G4 G5",
           urun_etkisi="JP kelime kutulari bosluklu birlesir (tokenizasyon bozulur)"),
    Mutant("M20", [_y(CJK_TUPLE, CJK_TUPLE.replace('    "HIRAGANA",\n', '    "HIRAGANA",\n    "HANGUL",\n'))],
           "K3: Hangul da CJK sayilir -> KR kelimeler BOSSUZ birlesir", "K3 Hangul", "G2 G3 G4 G5 (#1 'bosluklu')",
           urun_etkisi="KR 'jangro marcus' -> 'jangromarcus'; NMT bozulur"),
    Mutant("M21", [_y(ISALPHA, "        if karakter == metin[0]:\n")],
           "K3: ilk HARF degil ilk KARAKTER (tirnakla baslayan katakana LATIN)", "K3 ilk harf", "G2 G4 G5",
           urun_etkisi="koseli tirnakla baslayan katakana + hiragana -> bosluklu birlesir"),
    Mutant("M22", [_y(STRIP, "        metin = ham\n")],
           "K3: strip yok", "K3 strip", "G2 G4 G5",
           urun_etkisi="bosluklu OCR metni cift bosluk verir"),
    Mutant("M23", [_y(CJK_TUPLE, CJK_TUPLE.replace('    "CJK COMPATIBILITY IDEOGRAPH",\n', ""))],
           "K3: uyumluluk ideograflari (U+F900..) CJK sayilmiyor -- docstring 'CJK'dir' der", "K3 uyumluluk", "? (tabloda ornek yok)",
           urun_etkisi="nadir: uyumluluk ideografiyla baslayan parca bosluklu birlesir; docstring iddiasi olculuyor mu?"),
    Mutant("M24", [_y(CJK_TUPLE, CJK_TUPLE.replace('    "HIRAGANA",\n', ""))],
           "K3: HIRAGANA CJK degil", "K3 betik kumesi", "G2 G4 G5",
           urun_etkisi="hiragana ile baslayan parca bosluklu"),
    Mutant("M25", [_y(CJK_TUPLE, CJK_TUPLE.replace('    "KATAKANA",\n', ""))],
           "K3: KATAKANA CJK degil", "K3 betik kumesi", "G2 G4 G5",
           urun_etkisi="katakana ile baslayan parca bosluklu"),
    Mutant("M26", [_y(AYIRICI, '        if sonuc and not (onceki_cjk or cjk):\n            sonuc += " "\n')],
           "K3: bosluk yalniz LATIN-LATIN arasinda (karisik betik bossuz)", "K3 karisik", "G2 G3 G4 G5",
           urun_etkisi="Latin + hiragana bossuz; Hangul-Hangul da bossuz (KR bozulur)"),
    # ---- K5: alanlar -------------------------------------------------------------------
    Mutant("M27", [_y(CONF, CONF.replace("min(guvenler)", "max(guvenler)"))],
           "K5: confidence min -> max", "K5 confidence", "G2 G4 G5",
           urun_etkisi="normalizer esigi en zayif kelimeyi gormez"),
    Mutant("M28", [_y(CONF, "    confidence = parcalar[0].confidence\n")],
           "K5: confidence ILK parcadan", "K5 confidence", "G2 G4 G5",
           urun_etkisi="ayni"),
    Mutant("M29", [_y(CONF, "    confidence = (sum(guvenler) / len(guvenler)) if guvenler else math.nan\n")],
           "K5: confidence ORTALAMA", "K5 confidence", "G2 G4 G5",
           urun_etkisi="ayni"),
    Mutant("M30", [_y(GUVENLER, "    guvenler = [p.confidence for p in parcalar]\n")],
           "K8: NaN suzgeci yok (naif min, sira bagimli)", "K8 NaN", "G2 G4 G5",
           urun_etkisi="NaN x sirasinda ilkse confidence NaN, sondaysa degil -> K6'yi bozar"),
    Mutant("M31", [_y(CONF, CONF.replace("math.nan", "0.0"))],
           "K8: hepsi NaN -> 0.0 (NaN degil)", "K8 NaN", "G2 G4 G5",
           urun_etkisi="normalizer NaN reddi (K7) atlanir; blok sessizce elenir"),
    Mutant("M32", [_y(LINE_BOXES, "        line_boxes=(),\n")],
           "K5: birlesik blokta line_boxes BOS", "K5 line_boxes", "G2 G3 G4 G5 (#1 [2,5,5,5])",
           urun_etkisi="kaplama parcalari kaybolur"),
    Mutant("M33", [_y(LINE_BOXES, "        line_boxes=tuple(p.bbox for p in reversed(parcalar)),\n")],
           "K5: line_boxes TERS x sirasinda", "K5 line_boxes", "G2 G4 G5",
           urun_etkisi="parca kutulari ters sirada"),
    Mutant("M34", [_y(BBOX_BLOK, "    bbox = ilk\n")],
           "K5: bbox birlesim yerine ILK parcanin bbox'i", "K5 bbox", "G2 G4 G5",
           urun_etkisi="kaplama yalniz ilk kelimeyi kapsar"),
    Mutant("M35", [_y(BBOX_BLOK, BBOX_BLOK.replace("        h=alt - y,\n", "        h=ilk.h,\n"))],
           "K5: birlesik h yalniz ilk parcadan (alt kenar birlesmez)", "K5 bbox", "G2 G4 G5",
           urun_etkisi="kaplama alt kenari kisa kalir"),
    Mutant("M36", [_y(TEK_PARCA, "        tek = TextBlock(text=grup[0][1].text, bbox=grup[0][1].bbox, confidence=grup[0][1].confidence, line_boxes=grup[0][1].line_boxes)\n")],
           "K5/K8: tek parca `is` yerine ESIT KOPYA", "K5 tek parca", "G2 G4 G5",
           urun_etkisi="ayni nesne garantisi (docstring) bozulur; `==` tutar"),
    # ---- K6: sira ----------------------------------------------------------------------
    Mutant("M37", [_y(ILK_SIRALAMA, ILK_SIRALAMA.replace(", c[0]))", ", -c[0]))"))],
           "K6: bag girdi sirasinin TERSIYLE (-idx) -- tur 2: implementer C-3 'esdeger' dedi; DEGIL (ayni (y,x) farkli h cift satir uyeligini degistirir)", "K6 bag keskinlik", "? (tur 2: fixture yok, kacmasi beklenir)",
           urun_etkisi="ayni (y,x) farkli h cift tespit: kisa olan onceki satira yapisirsa uzun olan da surukleniyor -- girdi sirasina bagli satir uyeligi"),
    Mutant("M38", [_y(SON_SIRALAMA, "    sonuc.sort(key=lambda c: c[0], reverse=True)\n")],
           "K6: cikti TERS okuma sirasinda", "K6 sira", "G2 G3 G4 G5",
           urun_etkisi="normalizer yeniden siralar ama sozlesme bozuk"),
    Mutant("M39", [_y(SON_SIRALAMA, "")],
           "K6: son siralama YOK (yuzey/satir isleme sirasi)", "K6 sira", "G2 G4 G5",
           urun_etkisi="yozlasmis kutular basa gelir; monitorler sirasiz"),
    Mutant("M40", [_y(EN_KUCUK, "    en_kucuk_idx = max(idx for idx, _ in grup)\n")],
           "K6: bag EN KUCUK degil EN BUYUK girdi indeksiyle (birlesik grup vs tekil, ayni (y,x))", "K6 bag keskinlik", "? (bagli+birlesik fixture yok)",
           urun_etkisi="nadir: birlesik grup ile ayni (y,x)'teki tekil blogun sirasi"),
    Mutant("M41", [_y(X_SIRALI, X_SIRALI.replace("(c[1].bbox.x, c[1].bbox.y, c[0])", "(c[1].bbox.x, c[0])"))],
           "K2/K6: satir ici siralama (x, idx) -- y anahtari yok", "K6 satir ici bag keskinlik", "? (ayni x farkli y fixture yok)",
           urun_etkisi="ayni x, farkli y iki kutuda hangisi gruba once girer degisir"),
    # ---- K8: yozlasmis -----------------------------------------------------------------
    Mutant("M42", [_y(FONK_BAS, '    if not blocks:\n        raise ValueError("bos girdi")\n' + FONK_BAS)],
           "K8: bos girdi -> ValueError", "K8 bos", "G2 G4 G5",
           urun_etkisi="OCR bos kare verince pipeline patlar"),
    Mutant("M43", [_y(YOZLASMIS, "    return r.h < 0 or r.w < 0\n")],
           "K8: h=0/w=0 yozlasmis DEGIL (birlesebilir)", "K8 yozlasmis", "G2 G4 G5",
           urun_etkisi="sifir yukseklikli kutu komsusuyla birlesir"),
    Mutant("M44", [_y(YOZLASMIS, "    return r.h <= 0 and r.w <= 0\n")],
           "K8: yozlasmis icin HEM h HEM w <= 0 gerekir", "K8 yozlasmis", "G2 G4 G5",
           urun_etkisi="w=0 kutu birlesir"),
    Mutant("M45", [_y(YOZLASMIS, "    return r.h == 0 or r.w == 0\n")],
           "K8: negatif h/w yozlasmis DEGIL", "K8 yozlasmis", "G2 G4 G5",
           urun_etkisi="negatif yukseklik esigi negatif yapar (KRT D2)"),
    # ---- K1: saflik --------------------------------------------------------------------
    Mutant("M46", [_y(ALL_SATIRI, ALL_SATIRI + "\n_ONBELLEK: dict[int, int] = {}\n")],
           "K1: modul duzeyi MUTABLE (`_ONBELLEK: dict = {}`)", "K1 saflik", "G2 G4 G5",
           urun_etkisi="paylasilan durum kapisi acilir"),
    Mutant("M47", [_y("import math\n", "import math\nimport os\n")],
           "K1: modul duzeyinde `import os`", "K1 saflik", "G2 G3 G4 G5",
           urun_etkisi="I/O kapisi"),
    # ---- TUR 2: T2-1 satir referansi (en kisa) / T2-2 ----------------------------------
    Mutant("M48", [_y(REF_EKLE_GUNCELLE, "            satirlar[-1].append(oge)\n")],
           "T2-1 GERI (E geri): referans satirin ILK blogu -- guncelleme yok (tur 1 kodu)", "T2-1 satir referansi", "G2 G3 G4 G5 (#1c)",
           urun_etkisi="uzun etiket iki satiri kopruler: 11 -> 1 blok (tur 1 ret sinifi)"),
    Mutant("M49", [_y(REF_GUNCELLE, REF_GUNCELLE.replace("kutu.h < referans.h", "kutu.h > referans.h"))],
           "T2-1: referans EN UZUN blok (`<` -> `>`)", "T2-1 satir referansi", "G2 G3 G4 G5 (#1c)",
           urun_etkisi="en uzun kutu referans: etiket koprusu geri gelir"),
    Mutant("M50", [_y(REF_GUNCELLE, REF_GUNCELLE.replace("kutu.h < referans.h", "kutu.h <= referans.h"))],
           "T2-1 bag: `<=` (esit yukseklikte SON kisa blok referans; karar `bag: ilk`)", "T2-1 bag", "G2 G4 G5",
           urun_etkisi="esit yukseklikli merdivende referans kayar"),
    Mutant("M51", [_y(REF_KOSUL, "        if satirlar and _dikey_ortusme_yeterli(satirlar[-1][0][1].bbox, kutu):\n")],
           "T2-1: uyelik satirin ILK bloguyla (tur 1 lafzi birebir; referans guncellenir ama KULLANILMAZ) -- M48 ile ayni davranis beklenir", "T2-1 satir referansi", "G2 G3 G4 G5 (#1c)",
           urun_etkisi="M48 ile ayni: etiket koprusu"),
    Mutant("M52", [_y(REF_GUNCELLE, REF_GUNCELLE.replace("kutu.h < referans.h", "kutu.w < referans.w"))],
           "T2-1: referans yanlis boyutla (en DAR blok, h degil w)", "T2-1 satir referansi", "G2 G4 G5",
           urun_etkisi="genis kelime etiketi asamaz -> kopru; dar etiket gecer"),
    Mutant("M53", [_y(REF_KOSUL, "        if referans is not None and _dikey_ortusme_yeterli(satirlar[-1][-1][1].bbox, kutu):\n")],
           "T2-1: uyelik bir ONCEKIYLE olculur, referans guncellenir ama kullanilmaz (M16 ile ayni davranis beklenir)", "K2 satir referansi", "G2 G4 G5",
           urun_etkisi="merdiven tek satir"),
    Mutant("C-7", [_y(DIKEY_DONUS, DIKEY_DONUS.replace("min(a.h, b.h)", "min(b.h, a.h)")),
                   _y(BOSLUK_DONUS, BOSLUK_DONUS.replace("min(son.h, aday.h)", "min(aday.h, son.h)"))],
           "KONTROL (implementer C-2): min argumanlari yer degistirdi (esdeger)", "-- kontrol --", ".....", kontrol=True),
    Mutant("C-8", [_y(REF_KOSUL, REF_KOSUL.replace("_dikey_ortusme_yeterli(referans, kutu)", "_dikey_ortusme_yeterli(kutu, referans)"))],
           "KONTROL: satir uyeligi ortusme argumanlari yer degistirdi (simetrik; esdeger)", "-- kontrol --", ".....", kontrol=True),
    # NOT: implementer C-3 (`-idx`, eski M04) = buradaki M37 (DAVRANIS mutanti). Tur 2'de esdeger
    # DEGIL (r2-B2-1b-idx-mutanti-esdeger-degil.txt: ayni (y,x) farkli h cift + komsu satir, 3000'de 264
    # ayrisma); teslim fixture'lari bu sinifa ugramadigi icin kacar -- beklenen `.....` (§4.6/10).
    Mutant("C-6", [_y(FONK_BAS, FONK_BAS + "    _kayit = sorted(blocks, key=lambda b: b.text)\n")],
           "KONTROL: ciktiya etkisiz ek siralama (yalniz sure; 1000 blok butcesi hassas mi?)", "-- kontrol --", ".....", kontrol=True),
    # ---- KONTROL: davranis-esdeger, KACMALI -------------------------------------------------
    Mutant("C-1", [_y(ILK_SIRALAMA, ILK_SIRALAMA.replace(", c[0]))", "))"))],
           "KONTROL: ilk siralama anahtari (y,x,idx) -> (y,x) -- kararli sort + enumerate = esdeger", "-- kontrol --", ".....", kontrol=True),
    Mutant("C-2", [_y(DIKEY_DONUS, DIKEY_DONUS.replace("min(a.h, b.h)", "sorted([a.h, b.h])[0]"))],
           "KONTROL: min -> sorted()[0] (esdeger)", "-- kontrol --", ".....", kontrol=True),
    Mutant("C-3", [_y(X_MIN, "    x = parcalar[0].bbox.x\n")],
           "KONTROL: min x yerine x-sirali ilk parcanin x'i (esdeger)", "-- kontrol --", ".....", kontrol=True),
    Mutant("C-4", [_y(EN_KUCUK, "    en_kucuk_idx = sorted(idx for idx, _ in grup)[0]\n")],
           "KONTROL: min idx -> sorted()[0] (esdeger)", "-- kontrol --", ".....", kontrol=True),
    Mutant("C-5", [_y(MON_ILK, "        monitor_index=parcalar[-1].bbox.monitor_index,\n")],
           "KONTROL: monitor_index SON parcadan (yuzey bolumlemesi -> hepsi ayni; esdeger)", "-- kontrol --", ".....", kontrol=True),
]


def _kapi_kos(argv: list[str]) -> tuple[int, str, float]:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    env.pop("PYTHONIOENCODING", None)
    t0 = time.perf_counter()
    r = subprocess.run(argv, cwd=str(KOK), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=env, timeout=900)
    return r.returncode, (r.stdout or "") + (r.stderr or ""), time.perf_counter() - t0


def _uygula(mut: Mutant) -> None:
    p = KOK / KAYNAK
    metin = p.read_text(encoding="utf-8")
    for eski, yeni in mut.yamalar:
        n = metin.count(eski)
        if n != 1:
            raise SystemExit(f"{mut.mid}: yama hedefi {n} kez bulundu (1 olmali)\n{eski[:200]!r}")
        metin = metin.replace(eski, yeni, 1)
    p.write_text(metin, encoding="utf-8")


def _geri_al() -> None:
    shutil.copyfile(DEPO / KAYNAK, KOK / KAYNAK)


def _ayna_kur() -> None:
    if KOK.exists():
        shutil.rmtree(KOK, ignore_errors=True)
    yoksay = shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache", ".mypy_cache")
    for ad in AYNALANAN_DIZINLER:
        shutil.copytree(DEPO / ad, KOK / ad, ignore=yoksay)
    for ad in AYNALANAN_DOSYALAR:
        (KOK / ad).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(DEPO / ad, KOK / ad)
    hedef = KOK / MODEL_DIZINI
    hedef.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(["cmd", "/c", "mklink", "/J", str(hedef), str(DEPO / MODEL_DIZINI)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0 or not (hedef / "model.bin").exists():
        hedef.mkdir(parents=True, exist_ok=True)
        for ad in MODEL_DOSYALARI:
            shutil.copyfile(DEPO / MODEL_DIZINI / ad, hedef / ad)
        print("models/: kopyalandi (junction kurulamadi)")
    else:
        print("models/: junction (salt okunur kullanim; depo dosyalarina yazilmaz)")


def _dusen_testler(ozet: str) -> list[str]:
    return [ln.strip()[:150] for ln in ozet.splitlines() if ln.startswith(("FAILED", "ERROR"))]


def _ilk_hata(ad: str, ozet: str) -> str:
    for ln in ozet.splitlines():
        if any(k in ln for k in ("IHLAL", "error:", "failed", "Required test coverage", "RuntimeError", "Error")):
            return f"{ad}: {ln.strip()[:140]}"
    return f"{ad}: (ilk hata satiri bulunamadi; exit != 0)"


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")  # cp1254 konsolda ASCII disi aciklama cokmesin
    argv = sys.argv[1:]
    taban_iste = "--taban" in argv
    jsonl: Path | None = None
    if "--jsonl" in argv:
        jsonl = Path(argv[argv.index("--jsonl") + 1])
    secilen = {a for a in argv if not a.startswith("--") and (jsonl is None or a != str(jsonl))}
    _ayna_kur()
    print(f"ayna agaci: {KOK}   (depo YAZILMAZ)")
    print("kapilar PYTHONIOENCODING'siz (cp1254) kosar; real_check yalniz ASCII basar")
    print()
    if DRY:
        print("KURU KOSUM: yama hedefleri + py_compile")
        for mut in MUTANTLAR:
            if secilen and mut.mid not in secilen:
                continue
            _uygula(mut)
            try:
                py_compile.compile(str(KOK / KAYNAK), doraise=True)
                print(f"  {mut.mid:5s} yama OK, derlendi")
            finally:
                _geri_al()
        return

    basliklar = [ad for ad, _ in KAPILAR]
    if taban_iste or not secilen:
        print("TABAN (mutasyonsuz ayna):")
        taban_ok = True
        for ad, argv_k in KAPILAR:
            rc, ozet, sn = _kapi_kos(argv_k)
            son = [ln for ln in ozet.strip().splitlines() if ln.strip()][-1:] or [""]
            print(f"  {ad:10s} exit={rc}  {sn:6.1f}s  {son[0][:100]}")
            taban_ok = taban_ok and rc == 0
        if not taban_ok:
            raise SystemExit("TABAN GECMEDI -- ayna agaci bozuk, mutant tablosu uretilmedi")
        print()

    kacan: list[str] = []
    yakalanan_kontrol: list[str] = []
    sapan: list[str] = []
    print("MUTANT KITI -- her mutant icin hangi kapi YAKALAR (X) / KACIRIR (.)")
    print("kapilar: " + " | ".join(basliklar))
    print()
    for mut in MUTANTLAR:
        if secilen and mut.mid not in secilen:
            continue
        _uygula(mut)
        try:
            isaretler: list[str] = []
            detaylar: list[str] = []
            dusenler: dict[str, list[str]] = {}
            sureler: list[float] = []
            for ad, argv_k in KAPILAR:
                rc, ozet, sn = _kapi_kos(argv_k)
                sureler.append(sn)
                isaretler.append("X" if rc != 0 else ".")
                if rc != 0:
                    detaylar.append(_ilk_hata(ad, ozet))
                    d = _dusen_testler(ozet)
                    if d:
                        dusenler[ad] = d
            durum = "".join(isaretler)
            yakalandi = "X" in durum
            if mut.kontrol:
                etiket = "KACTI (dogru: kontrol)" if not yakalandi else "*** KONTROL YAKALANDI = YANLIS POZITIF ***"
                if yakalandi:
                    yakalanan_kontrol.append(mut.mid)
            else:
                etiket = "YAKALANDI" if yakalandi else "*** HICBIR KAPI YAKALAMADI ***"
                if not yakalandi:
                    kacan.append(mut.mid)
            tahmin_kapilar = {p for p in mut.beklenen.replace("(", " ").replace(")", " ").split() if p.startswith("G")}
            gercek_kapilar = {basliklar[i].split("-")[0] for i, c in enumerate(durum) if c == "X"}
            if not mut.kontrol and "?" not in mut.beklenen and tahmin_kapilar != gercek_kapilar:
                sapan.append(f"{mut.mid}: tahmin {sorted(tahmin_kapilar)} gercek {sorted(gercek_kapilar)}")
            g2_sayi = len(dusenler.get("G2-birim", []))
            print(f"{mut.mid:5s} [{durum}] {etiket}   G2 dusen={g2_sayi}  (beklenen: {mut.beklenen})")
            print(f"       {mut.aciklama}")
            if mut.urun_etkisi:
                print(f"       urun: {mut.urun_etkisi}")
            for d in detaylar:
                print(f"       {d}")
            for ad, liste in dusenler.items():
                for t in liste[:4]:
                    print(f"         {ad}: {t}")
                if len(liste) > 4:
                    print(f"         {ad}: ... +{len(liste) - 4}")
            print(f"       sureler: " + " ".join(f"{s:.0f}s" for s in sureler))
            if jsonl is not None:
                with jsonl.open("a", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "mid": mut.mid, "durum": durum, "kontrol": mut.kontrol, "sinif": mut.sinif,
                        "beklenen": mut.beklenen, "aciklama": mut.aciklama, "g2_dusen": g2_sayi,
                        "dusenler": dusenler, "detaylar": detaylar,
                    }, ensure_ascii=True) + "\n")
        finally:
            _geri_al()
    print()
    print(f"kacan davranis mutanti: {kacan}")
    print(f"yakalanan kontrol (yanlis pozitif): {yakalanan_kontrol}")
    print(f"tahminden sapan: {sapan}")


if __name__ == "__main__":
    main()
