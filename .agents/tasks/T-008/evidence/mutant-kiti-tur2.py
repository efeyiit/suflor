"""T-008 mutant ayirt-etme kiti (implementer, tur 2 -- tur 1 kiti + T2 mutantlari).

    python .agents/tasks/T-008/evidence/mutant-kiti-tur2.py

Depoya DOKUNMAZ: `src/contracts`, `src/ocr/__init__.py`,
`src/ocr/satir_birlestirici.py`, `tests/unit/ocr/conftest.py` ve
`tests/unit/ocr/test_satir_birlestirici.py` scratchpad altinda bir AYNA
agacina kopyalanir (`T008_AYNA` ortam degiskeni ile yer secilebilir). Her
mutant aynadaki `satir_birlestirici.py`ye metin ikamesiyle uygulanir ve
birim test dosyasi ayna koku `PYTHONPATH`/cwd ile kosulur. Stdout ASCII;
metin basilmaz. Cikis 0 = her beklenti tuttu.

`X (n)` = n test dustu (YAKALANDI), `.` = hepsi gecti (KACTI).

Beklentiler:
  M01..M24  davranis degistiren mutantlar: birim testleri YAKALAMALI.
            Tur 2: M17 yeniden hedeflendi (satir referansi = son eklenen),
            M21 = E geri alinmis (referans = satirin ILK blogu, tur 1 kodu),
            M22 = referans EN UZUN blok, M23 = satir ici anahtar `(x, idx)`
            (y'siz, Tester-B M41), M24 = referans guncellemesi `<=` (bagda
            SON kisa blok; esdeger olmali mi? olculur -- bkz. sonuc).
  C-1..C-3  davranis-esdeger degisiklikler (kontrol): KACMALI --
            yanlis pozitif yok. C-1: ilk siralama anahtarindan `idx`
            cikarilir; `sorted` KARARLI oldugu ve girdi `enumerate`
            sirasinda verildigi icin sonuc AYNIDIR. C-2: `min/max`
            argumanlari yer degistirir. C-3 (tur 2, eski M04): ilk
            siralamada bag TERS cozulur (`-idx`) -- T2-1 sonrasi satir
            referansi en kisa blok oldugu icin bagli ciftin isleme sirasi
            ne uyeligi ne referansi degistirir; satir ici `(x,y,idx)` ve
            cikti `(y,x,min idx)` yeniden siralar -> davranis ESDEGER
            (tur 1'de 1 testle yakalaniyordu; o test yeniden nisanlandi).
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
KAYNAK = KOK / "src" / "ocr" / "satir_birlestirici.py"
TEST = KOK / "tests" / "unit" / "ocr" / "test_satir_birlestirici.py"

# (ad, aciklama, eski, yeni, yakalanmali)
MUTANTLAR: list[tuple[str, str, str, str, bool]] = [
    ("M01", "YATAY_BOSLUK_ESIGI 0.75 -> 10.0 (menu sutunlari birlesir)",
     "YATAY_BOSLUK_ESIGI: Final[float] = 0.75", "YATAY_BOSLUK_ESIGI: Final[float] = 10.0", True),
    ("M02", "DIKEY_ORTUSME_ESIGI 0.5 -> 0.0 (degen kutular ayni satir)",
     "DIKEY_ORTUSME_ESIGI: Final[float] = 0.5", "DIKEY_ORTUSME_ESIGI: Final[float] = 0.0", True),
    ("M03", "Y2: bosluk esigi BIRLESIK yukseklikle (grubun max h)",
     "            if _dikey_ortusme_yeterli(ilk, oge[1].bbox) and _yatay_komsu(son, oge[1].bbox):",
     "            if _dikey_ortusme_yeterli(ilk, oge[1].bbox) and _yatay_komsu(Rect(son.x, min(p[1].bbox.y for p in gruplar[-1]), son.w, max(p[1].bbox.bottom for p in gruplar[-1]) - min(p[1].bbox.y for p in gruplar[-1])), oge[1].bbox):",
     True),
    ("C-3", "KONTROL (eski M04): ilk siralamada bag TERS cozulur (-idx) -- T2-1 sonrasi esdeger",
     "key=lambda c: (c[1].bbox.y, c[1].bbox.x, c[0]))", "key=lambda c: (c[1].bbox.y, c[1].bbox.x, -c[0]))", False),
    ("M05", "K3: CJK-CJK arasina da bosluk",
     "        if sonuc and not (onceki_cjk and cjk):", "        if sonuc:", True),
    ("M06", "K5: confidence min -> max",
     "    confidence = min(guvenler) if guvenler else math.nan", "    confidence = max(guvenler) if guvenler else math.nan", True),
    ("M07", "K5: birlesik blokta line_boxes bos",
     "        line_boxes=tuple(p.bbox for p in parcalar),", "        line_boxes=(),", True),
    ("M08", "K2: monitor_index denetimi yok",
     "        anahtar = (blok.bbox.monitor_index, blok.bbox.dpi_scale)", "        anahtar = (0, blok.bbox.dpi_scale)", True),
    ("M09", "K2: dpi_scale denetimi yok (KARAR)",
     "        anahtar = (blok.bbox.monitor_index, blok.bbox.dpi_scale)", "        anahtar = (blok.bbox.monitor_index, 1.0)", True),
    ("M10", "K2: x ilerleme `>` -> `>=` (cift tespit birlesir)",
     "    if not aday.x > son.x:", "    if not aday.x >= son.x:", True),
    ("M11", "K2: bosluk `<=` -> `<` (tam 0.75 ayrilir)",
     "    return bosluk <= YATAY_BOSLUK_ESIGI * min(son.h, aday.h)", "    return bosluk < YATAY_BOSLUK_ESIGI * min(son.h, aday.h)", True),
    ("M12", "K2: ortusme `>=` -> `>` (tam 0.5 ayrilir)",
     "    return ortusme >= DIKEY_ORTUSME_ESIGI * min(a.h, b.h)", "    return ortusme > DIKEY_ORTUSME_ESIGI * min(a.h, b.h)", True),
    ("M13", "K8: NaN suzgeci yok (naif min)",
     "    guvenler = [p.confidence for p in parcalar if not math.isnan(p.confidence)]", "    guvenler = [p.confidence for p in parcalar]", True),
    ("M14", "K3: strip yok",
     "        metin = ham.strip()", "        metin = ham", True),
    ("M15", "K6: son siralama yok (isleme sirasi)",
     "    sonuc.sort(key=lambda c: c[0])", "    pass", True),
    ("M16", "K2/K8: yozlasmis kutu birlesebilir",
     "    return r.h <= 0 or r.w <= 0", "    return False", True),
    ("M17", "K2: satir referansi EN KISA degil SON EKLENEN blok (merdiven)",
     "            if kutu.h < referans.h:\n                referans = kutu",
     "            referans = kutu", True),
    ("M18", "K2: grup ici dikey referans ILK degil SON blok (uzun kutu koprusu)",
     "            ilk = gruplar[-1][0][1].bbox", "            ilk = gruplar[-1][-1][1].bbox", True),
    ("M19", "K2: bosluk esigi min(h) -> max(h)",
     "    return bosluk <= YATAY_BOSLUK_ESIGI * min(son.h, aday.h)", "    return bosluk <= YATAY_BOSLUK_ESIGI * max(son.h, aday.h)", True),
    ("M20", "K3: bos parca atlanmaz (cift bosluk)",
     "        if not metin:\n            continue", "        if not metin:\n            pass", True),
    ("M21", "T2-1 GERI ALINMIS: satir referansi satirin ILK blogu (tur 1 kodu; etiket koprusu)",
     "            if kutu.h < referans.h:\n                referans = kutu",
     "            pass", True),
    ("M22", "T2-1: satir referansi EN UZUN blok (`<` -> `>`)",
     "            if kutu.h < referans.h:", "            if kutu.h > referans.h:", True),
    ("M23", "T2-2: satir ici anahtar `(x, idx)` -- y'siz (Tester-B M41)",
     "    x_sirali = sorted(satir, key=lambda c: (c[1].bbox.x, c[1].bbox.y, c[0]))",
     "    x_sirali = sorted(satir, key=lambda c: (c[1].bbox.x, c[0]))", True),
    ("M24", "T2-1 bag: referans guncellemesi `<=` (esit yukseklikte SON kisa blok referans)",
     "            if kutu.h < referans.h:", "            if kutu.h <= referans.h:", True),
    ("C-1", "KONTROL: ilk siralama anahtarindan idx cikarildi (kararli sort -> esdeger)",
     "key=lambda c: (c[1].bbox.y, c[1].bbox.x, c[0]))", "key=lambda c: (c[1].bbox.y, c[1].bbox.x))", False),
    ("C-2", "KONTROL: min/max argumanlari yer degistirdi (esdeger)",
     "    ortusme = min(a.bottom, b.bottom) - max(a.y, b.y)", "    ortusme = min(b.bottom, a.bottom) - max(b.y, a.y)", False),
]


def ayna_kur(ayna: Path) -> None:
    if ayna.exists():
        shutil.rmtree(ayna)
    (ayna / "src" / "ocr").mkdir(parents=True)
    (ayna / "tests" / "unit" / "ocr").mkdir(parents=True)
    (ayna / ".agents" / "tasks" / "T-004").mkdir(parents=True)  # conftest KOK cozumu icin
    shutil.copytree(KOK / "src" / "contracts", ayna / "src" / "contracts",
                    ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copy(KOK / "src" / "ocr" / "__init__.py", ayna / "src" / "ocr" / "__init__.py")
    shutil.copy(KAYNAK, ayna / "src" / "ocr" / "satir_birlestirici.py")
    shutil.copy(KOK / "tests" / "unit" / "ocr" / "conftest.py", ayna / "tests" / "unit" / "ocr" / "conftest.py")
    shutil.copy(TEST, ayna / "tests" / "unit" / "ocr" / "test_satir_birlestirici.py")


def kos(ayna: Path) -> tuple[int, int, int]:
    env = dict(os.environ, PYTHONPATH=str(ayna), PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/unit/ocr/test_satir_birlestirici.py", "-q",
         "-p", "no:cacheprovider", "--no-header"],
        cwd=str(ayna), env=env, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    m_f = re.search(r"(\d+) failed", r.stdout)
    m_p = re.search(r"(\d+) passed", r.stdout)
    m_e = re.search(r"(\d+) error", r.stdout)
    return (int(m_f.group(1)) if m_f else 0, int(m_p.group(1)) if m_p else 0,
            int(m_e.group(1)) if m_e else (0 if (m_f or m_p) else 1))


def main() -> int:
    ayna = Path(os.environ.get("T008_AYNA") or (Path(os.environ.get("TEMP", ".")) / "t008_ayna"))
    ayna_kur(ayna)
    kaynak_ayna = ayna / "src" / "ocr" / "satir_birlestirici.py"
    orijinal = kaynak_ayna.read_text(encoding="utf-8")

    print("T-008 mutant kiti -- ayna:", ayna)
    f, p, e = kos(ayna)
    print(f"TEMEL (mutantsiz): failed={f} passed={p} error={e}")
    if f or e or p == 0:
        print("TEMEL kirmizi -- kit anlamsiz"); return 2

    hatalar: list[str] = []
    print(f"{'ad':5} {'sonuc':8} {'beklenen':10} aciklama")
    for ad, aciklama, eski, yeni, yakalanmali in MUTANTLAR:
        if orijinal.count(eski) != 1:
            print(f"{ad:5} {'?':8} {'-':10} {aciklama}  [IKAME NOKTASI {orijinal.count(eski)} KEZ -- KIT BOZUK]")
            hatalar.append(ad); continue
        kaynak_ayna.write_text(orijinal.replace(eski, yeni), encoding="utf-8")
        f, p, e = kos(ayna)
        yakalandi = (f + e) > 0
        sonuc = f"X ({f + e})" if yakalandi else "."
        beklenen = "YAKALA" if yakalanmali else "KACSIN"
        durum = "" if yakalandi == yakalanmali else "  <-- BEKLENTI TUTMADI"
        if durum:
            hatalar.append(ad)
        print(f"{ad:5} {sonuc:8} {beklenen:10} {aciklama}{durum}")
    kaynak_ayna.write_text(orijinal, encoding="utf-8")

    n_mut = sum(1 for m in MUTANTLAR if m[4])
    n_kont = len(MUTANTLAR) - n_mut
    print()
    print(f"{n_mut} davranis mutanti + {n_kont} kontrol; beklenti tutmayan: {len(hatalar)} {hatalar}")
    return 1 if hatalar else 0


if __name__ == "__main__":
    raise SystemExit(main())
