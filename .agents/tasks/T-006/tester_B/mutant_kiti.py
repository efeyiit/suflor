"""TESTER-B mutant kiti (T-006, mercek B: test kalitesi) -- kapilarin AYIRT ETME GUCU.

Soru: "95 test + real_check + mypy + kapsam + tam takim, motoru gercekten
olcuyor mu?" Tek yontem: motoru bilerek bozup HANGI KAPININ yakaladigini
saymak. Hicbir kapinin yakalamadigi, urunu bozan bir mutant, o degismezin
olcusunun BOS oldugunu kanitlar. Davranis-esdeger KONTROL mutantlari
(C0x) kacmak ZORUNDADIR; yakalanirlarsa olcu yanlis pozitif veriyordur.

`src/`, `tests/`, `real_check.py` DEGISTIRILMEZ: depo, scratchpad altindaki
bir AYNA AGACINA kopyalanir; mutasyon orada yapilir, her mutanttan sonra
dosya depodan geri yazilir.

Kosum:
    python .agents/tasks/T-006/tester_B/mutant_kiti.py [mutant_id ...]

Not (kendi olcumum): `real_check.py` cp1254 konsolda `≈` (U+2248) yuzunden
`UnicodeEncodeError` ile coker (bkz. tester_B_evidence/taban-3-real_check.txt).
Kit bu yuzden her kapiyi `PYTHONIOENCODING=utf-8` ile kosar; aksi halde
HER mutant "real_check dustu" gorunur ve tablo yanlis pozitif olurdu.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

DEPO = Path(__file__).resolve().parents[4]
SCRATCH = Path(os.environ.get("TESTER_B_SCRATCH", tempfile.gettempdir()))
KOK = SCRATCH / "t006_tester_B_mutroot"

MOTOR = "src/ocr/rapid_engine.py"
CONFTEST = "tests/unit/ocr/conftest.py"
GERI_ALINAN = (MOTOR, CONFTEST)

# Ayna agacina kopyalanan seyler: src, tests, T-004 olcu kiti (normalizer
# testleri icin), T-006 real_check + fixtures.
AYNALANAN_DIZINLER = ("src", "tests", ".agents/tasks/T-006/fixtures")
AYNALANAN_DOSYALAR = (".agents/tasks/T-004/olcu_kiti.py", ".agents/tasks/T-006/real_check.py")

# Paketin BES kabul komutu -- kapilarin kendisi (packet.md `acceptance`).
KAPILAR: list[tuple[str, list[str]]] = [
    ("G1-mypy", [sys.executable, "-m", "mypy", "--strict", "--explicit-package-bases", MOTOR]),
    ("G2-birim", [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                  "tests/unit/ocr/test_rapid_engine.py"]),
    ("G3-real", [sys.executable, ".agents/tasks/T-006/real_check.py"]),
    ("G4-kapsam", [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                   "tests/unit/ocr/test_rapid_engine.py", "--cov=src.ocr.rapid_engine",
                   "--cov-fail-under=90", "--cov-report=term-missing"]),
    ("G5-tum", [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests"]),
]


@dataclass
class Mutant:
    mid: str
    dosya: str
    yamalar: list[tuple[str, str]]
    aciklama: str
    hedef: str
    kontrol: bool = False
    ek: list[tuple[str, list[tuple[str, str]]]] = field(default_factory=list)


def _y(eski: str, yeni: str) -> tuple[str, str]:
    return (eski, yeni)


TS = '            "Global.text_score": 0.0,  # K5\n'
INTER = '            "EngineConfig.onnxruntime.inter_op_num_threads": self._threads,  # K3\n'
ARALIK = "    if not 1 <= n <= cekirdek:"
NONE_DAL = "        return min(_VARSAYILAN_PARCACIK, cekirdek)"
FLOOR_X = "    x0 = math.floor(float(noktalar[:, 0].min()))"
FLOOR_Y = "    y0 = math.floor(float(noktalar[:, 1].min()))"
CEIL_X = "    x1 = math.ceil(float(noktalar[:, 0].max()))"
RECT = (
    "    return Rect(\n"
    "        x=x0 + rect.x,\n"
    "        y=y0 + rect.y,\n"
    "        w=x1 - x0,\n"
    "        h=y1 - y0,\n"
)
KAPALI = (
    "        if self._kapali:\n"
    '            raise OcrError("motor kapatildi; close() sonrasi recognize cagrilamaz")\n'
)
TEK_ORNEK = (
    "        if self._taniyici is not None:\n"
    "            return self._taniyici\n"
)
CLOSE = (
    "        self._taniyici = None\n"
    "        self._kapali = True\n"
)
SONRA_SEVIYE = (
    "        logging.getLogger(_LOGGER_ADI).setLevel(logging.ERROR)\n"
    "        self._taniyici = taniyici\n"
)
FABRIKA_CAGRI = (
    "        params = self.parametreler()\n"
    "        try:\n"
    "            taniyici = self._fabrika(params)\n"
)
BLOK_EKLE = (
    "        bloklar.append(\n"
    "            TextBlock(text=metin, bbox=_cokgen_kutusu(kutu, rect), confidence=_puan(puan))\n"
    "        )\n"
)
DONUS = "        return _bloklara_cevir(cikti, frame.rect)\n"
MME_EKSIK = (
    "        if eksik:\n"
    "            raise ModelMissingError(\n"
)
TANIMA_HATA = (
    "        except TranslatorError:\n"
    "            raise\n"
    "        except Exception as e:\n"
    '            raise OcrError(f"tanıma basarisiz: {type(e).__name__}") from e\n'
)
FNF = (
    "        except FileNotFoundError as e:\n"
    '            raise ModelMissingError("model dosyasi kurulum sirasinda bulunamadi") from e\n'
)

MUTANTLAR: list[Mutant] = [
    # ---- K5 suzgec ---------------------------------------------------------
    Mutant("M01", MOTOR, [_y(TS, "")],
           "K5: `Global.text_score` anahtari SILINDI (kutuphane varsayilani 0.5 -> sessiz eleme)", "K5"),
    Mutant("M02", MOTOR, [_y(TS, '            "Global.text_score": 0.5,  # K5\n')],
           "K5: `Global.text_score` = 0.5 yazilmis (suzgec ACIK)", "K5"),
    Mutant("M03", MOTOR, [_y(TS, '            "Global.textscore": 0.0,  # K5\n')],
           "K5: yanlis anahtar adi `Global.textscore` (kutuphane sessizce kabul eder, KRT D4)", "K5"),
    Mutant("M03b", MOTOR,
           [_y(BLOK_EKLE,
               "        if _puan(puan) < 0.5:\n            continue\n" + BLOK_EKLE)],
           "K5: motor kendi esigini uyguluyor (puan < 0.5 atlanir)", "K5"),
    Mutant("M03c", MOTOR,
           [_y("            TextBlock(text=metin, bbox=_cokgen_kutusu(kutu, rect), confidence=_puan(puan))",
               "            TextBlock(text=metin.strip(), bbox=_cokgen_kutusu(kutu, rect), confidence=_puan(puan))")],
           "K5: `text` DEGISTIRILIYOR (strip)", "K5"),
    # ---- K11 tablo: dort dilde AYRI AYRI --------------------------------------
    Mutant("M04", MOTOR,
           [_y('    (OcrLanguage.JAPAN, "multi", "japan"),', '    (OcrLanguage.JAPAN, "ch", "japan"),')],
           "K11 JAPAN: Det.lang_type multi -> ch", "K11 (JAPAN det)"),
    Mutant("M05", MOTOR,
           [_y('    (OcrLanguage.KOREAN, "multi", "korean"),', '    (OcrLanguage.KOREAN, "multi", "japan"),')],
           "K11 KOREAN: Rec.lang_type korean -> japan", "K11 (KOREAN rec)"),
    Mutant("M06", MOTOR,
           [_y('            "Det.ocr_version": _OCR_SURUMU,',
               '            "Det.ocr_version": ("PP-OCRv5" if self._language is OcrLanguage.CHINESE else _OCR_SURUMU),')],
           "K11 CHINESE: Det.ocr_version yalniz CHINESE'de PP-OCRv5", "K11 (CHINESE version)"),
    Mutant("M07", MOTOR,
           [_y('            "Rec.model_type": _MODEL_TIPI,',
               '            "Rec.model_type": ("server" if self._language is OcrLanguage.ENGLISH else _MODEL_TIPI),')],
           "K11 ENGLISH: Rec.model_type yalniz ENGLISH'te server", "K11 (ENGLISH type)"),
    Mutant("M08", MOTOR,
           [_y('    (OcrLanguage.KOREAN, "multi_PP-OCRv3_det_mobile.onnx", "korean_PP-OCRv4_rec_mobile.onnx"),',
               '    (OcrLanguage.KOREAN, "multi_PP-OCRv3_det_mobile.onnx", "japan_PP-OCRv4_rec_mobile.onnx"),')],
           "K6/K11 KOREAN: rec model DOSYASI japan (diskte var -> yanlis model sessizce yuklenir)", "K11 dosya tablosu (KOREAN)"),
    Mutant("M09", MOTOR,
           [_y('    (OcrLanguage.ENGLISH, "ch_PP-OCRv4_det_mobile.onnx", "en_PP-OCRv4_rec_mobile.onnx"),',
               '    (OcrLanguage.ENGLISH, "multi_PP-OCRv3_det_mobile.onnx", "en_PP-OCRv4_rec_mobile.onnx"),')],
           "K6/K11 ENGLISH: det model DOSYASI multi (Y3: 22 kelime kutusu)", "K11 dosya tablosu (ENGLISH)"),
    # ---- K3 -------------------------------------------------------------------
    Mutant("M10", MOTOR, [_y(ARALIK, "    if n < 1:")],
           "K3: UST sinir denetimi yok (cpu_count ustu sessiz otomatik)", "K3 ust sinir"),
    Mutant("M11", MOTOR, [_y(ARALIK, "    if not 0 <= n <= cekirdek:")],
           "K3: ALT sinir 0'i kabul eder (0 = onnxruntime otomatik)", "K3 alt sinir"),
    Mutant("M11b", MOTOR, [_y(ARALIK, "    if not 1 <= n < cekirdek:")],
           "K3: tam sinir (n == cpu_count) REDDEDILIR (off-by-one)", "K3 tam sinir"),
    Mutant("M12", MOTOR, [_y(INTER, "")],
           "K3: `inter_op_num_threads` anahtari UNUTULMUS, intra dogru", "K3 inter"),
    Mutant("M12b", MOTOR,
           [_y(INTER, '            "EngineConfig.onnxruntime.inter_op_num_threads": 1,  # K3\n')],
           "K3: inter sabit 1, intra dogru", "K3 inter"),
    Mutant("M13", MOTOR, [_y(NONE_DAL, "        return cekirdek")],
           "K3: None -> cpu_count (min(8, ...) yok)", "K3 None varsayilani"),
    Mutant("M13b", MOTOR, [_y(NONE_DAL, "        return _VARSAYILAN_PARCACIK")],
           "K3: None -> 8 kosulsuz (cpu_count < 8'de sessiz otomatik)", "K3 None varsayilani"),
    # ---- K4 -------------------------------------------------------------------
    Mutant("M14", MOTOR,
           [_y(FLOOR_X, "    x0 = round(float(noktalar[:, 0].min()))"),
            _y(FLOOR_Y, "    y0 = round(float(noktalar[:, 1].min()))")],
           "K4: floor -> round (x ve y)", "K4 floor"),
    Mutant("M15", MOTOR, [_y(CEIL_X, "    x1 = math.floor(float(noktalar[:, 0].max()))")],
           "K4: ceil -> floor (x)", "K4 ceil"),
    Mutant("M16", MOTOR, [_y("        y=y0 + rect.y,\n", "        y=y0,\n")],
           "K4: kaydirma YALNIZ x'e (y kaydirilmiyor)", "K4 kaydirma"),
    Mutant("M17", MOTOR, [_y("        x=x0 + rect.x,\n", "        x=x0 - rect.x,\n")],
           "K4: x kaydirmasi ters isaretli", "K4 kaydirma"),
    Mutant("M18", MOTOR, [_y("        w=x1 - x0,\n", "        w=x1 - x0 + 1,\n")],
           "K4: w'ye fazladan 1 piksel", "K4 fazla piksel"),
    Mutant("M18b", MOTOR,
           [_y("        w=x1 - x0,\n", "        w=math.ceil(float(noktalar[:, 0].max()) - float(noktalar[:, 0].min())),\n")],
           "K4: w = ceil(max-min) (floor/ceil ayrik uygulanmiyor)", "K4 w formulu"),
    # ---- K6 -------------------------------------------------------------------
    Mutant("M19", MOTOR, [_y(MME_EKSIK, "        if eksik:\n            raise OcrError(\n")],
           "K6: model yok -> ModelMissingError yerine OcrError", "K6 (a) siniflandirma"),
    Mutant("M20", MOTOR, [_y("        _kareyi_dogrula(frame)\n", "")],
           "K6 (c): kare dogrulamasi YOK, bozuk kare motora gider", "K6 (c) ContractViolation"),
    Mutant("M20b", MOTOR,
           [_y("        _kareyi_dogrula(frame)\n        taniyici = self._taniyici_al()\n",
               "        taniyici = self._taniyici_al()\n        _kareyi_dogrula(frame)\n")],
           "K6 (c): dogrulama kurulumdan SONRA (bozuk karede fabrika cagrilir)", "K6 (c) sira"),
    Mutant("M21", MOTOR,
           [_y('            raise OcrError(f"tanıma basarisiz: {type(e).__name__}") from e\n',
               '            raise OcrError(f"tanıma basarisiz: {type(e).__name__}") from None\n')],
           "K6 (b): `__cause__` DUSURULMUS", "K6 (b) __cause__"),
    Mutant("M22", MOTOR, [_y(FNF, "")],
           "K6: fabrikanin FileNotFoundError'u ModelMissingError yerine OcrError olur", "K6 (a) kurulum"),
    Mutant("M23", MOTOR,
           [_y(TANIMA_HATA,
               "        except Exception as e:\n"
               '            raise OcrError(f"tanıma basarisiz: {type(e).__name__}") from e\n')],
           "K6 (b): tanıyıcının TranslatorError'u da OcrError'a SARILIR (ModelMissingError kaybolur)", "K6 (b) oldugu gibi"),
    Mutant("M36", MOTOR, [_y("        if self._allow_download:\n", "        if False:\n")],
           "K6: allow_download=True'da da model_path zorlanir (indirme yolu kapali)", "K6 allow_download"),
    Mutant("M37", MOTOR,
           [_y("    if img.ndim != 3 or img.shape[2] != 3:", "    if img.ndim != 3 or img.shape[2] not in (3, 4):")],
           "K6 (c): (h,w,4) kabul edilir", "K6 (c) bicim"),
    # ---- K7 -------------------------------------------------------------------
    Mutant("M24", MOTOR,
           [_y(SONRA_SEVIYE, "        self._taniyici = taniyici\n"),
            _y(FABRIKA_CAGRI, "        logging.getLogger(_LOGGER_ADI).setLevel(logging.ERROR)\n" + FABRIKA_CAGRI)],
           "K7: logger seviyesi kurulumdan ONCE cekiliyor (kutuphane sifirlar)", "K7 sira"),
    Mutant("M25", MOTOR,
           [_y(DONUS, "        bloklar = _bloklara_cevir(cikti, frame.rect)\n        print(len(bloklar))\n        return bloklar\n")],
           "K7: `print` eklendi (metinsiz)", "K7 print"),
    Mutant("M25b", MOTOR,
           [_y(DONUS, "        bloklar = _bloklara_cevir(cikti, frame.rect)\n"
                      "        sys.stdout.write(bloklar[0].text if bloklar else '')\n        return bloklar\n"),
            _y("import os\n", "import os\nimport sys\n")],
           "K7: `sys.stdout.write(blok.text)` (print DEGIL -- AST `print` sayaci gormez)", "K7 stdout"),
    Mutant("M26", MOTOR,
           [_y("        logging.getLogger(_LOGGER_ADI).setLevel(logging.ERROR)\n",
               "        logging.getLogger(_LOGGER_ADI).setLevel(logging.WARNING)\n")],
           "K7: seviye WARNING (bos karede WARNING basar)", "K7 seviye"),
    Mutant("M27", MOTOR,
           [_y('            "Global.log_level": "error",  # K7 (kurulum sirasi)\n',
               '            "Global.log_level": "info",  # K7 (kurulum sirasi)\n')],
           "K7: params log_level=info (kurulum sirasinda INFO satirlari)", "K7 kurulum logu"),
    Mutant("M28a", MOTOR,
           [_y(BLOK_EKLE, '        logging.getLogger(__name__).warning("blok %s", metin)\n' + BLOK_EKLE)],
           "K7: modul logger'ina WARNING ile blok METNI (degisken adi `metin`, `.text`/`txts` degil)", "K7 metin loglanmaz"),
    Mutant("M28b", MOTOR,
           [_y(BLOK_EKLE, '        logging.getLogger(_LOGGER_ADI).info("blok %s", metin)\n' + BLOK_EKLE)],
           "K7: RapidOCR logger'ina INFO ile blok METNI (motor ERROR'a cektigi icin sessiz)", "K7 metin loglanmaz"),
    Mutant("M28c", MOTOR,
           [_y(BLOK_EKLE, '        logging.getLogger("suflor.ocr").debug("blok %s", metin)\n' + BLOK_EKLE)],
           "K7: uygulama logger'ina DEBUG ile blok METNI (uygulama DEBUG acinca log dosyasina sizar)", "K7 metin loglanmaz"),
    # ---- K10 ------------------------------------------------------------------
    Mutant("M29", MOTOR, [_y(KAPALI, "")],
           "K10: close() sonrasi recognize CALISIYOR (fabrika yeniden kurulur)", "K10 close sonrasi"),
    Mutant("M30", MOTOR, [_y(TEK_ORNEK, "")],
           "K10: fabrika HER cagrida yeniden kuruluyor", "K10 tek ornek"),
    Mutant("M31", MOTOR, [_y(CLOSE, "        self._taniyici = None\n")],
           "K10: close() `_kapali` isaretlemez -> sonraki recognize fabrikayi yeniden kurar", "K10 close"),
    Mutant("M32", MOTOR, [_y(CLOSE, "        self._kapali = True\n")],
           "K10: close() tanıyıcıyı BIRAKMAZ (oturumlar canli kalir; disaridan gorunmez)", "K10 close birakir"),
    # ---- K1 / K2 --------------------------------------------------------------
    Mutant("M33", MOTOR, [_y("import numpy as np\n", "import numpy as np\nimport rapidocr  # noqa: F401\n")],
           "K1: modul duzeyinde `import rapidocr`", "K1 tembel import"),
    Mutant("M33c", MOTOR,
           [_y("    try:\n        dagitim = importlib.metadata.distribution(\"rapidocr\")",
               "    import rapidocr as _r\n    return Path(_r.__file__).resolve().parent / \"models\"\n"
               "    try:\n        dagitim = importlib.metadata.distribution(\"rapidocr\")")],
           "K1: varsayilan model dizini `import rapidocr` ile bulunuyor", "K1 bariyer altinda dizin"),
    Mutant("M38", MOTOR, [_y("        language: OcrLanguage,\n", "        language: OcrLanguage = OcrLanguage.JAPAN,\n")],
           "K2: `language` varsayilani JAPAN", "K2 zorunlu dil"),
    # ---- KONTROL: davranis-esdeger, KACMALI --------------------------------------
    Mutant("C01", MOTOR, [_y("        if dil is language:\n            return det, rec", "        if dil == language:\n            return det, rec")],
           "KONTROL: `is` -> `==` (enum uyesi icin esdeger)", "-- kontrol --", kontrol=True),
    Mutant("C02", MOTOR, [_y("        noktalar = np.asarray(kutu, dtype=np.float64)", "        noktalar = np.array(kutu, dtype=np.float64)")],
           "KONTROL: asarray -> array (kopya; sonuc ayni)", "-- kontrol --", kontrol=True),
    Mutant("C03", MOTOR, [_y("        self._kapali = False\n", "        self._kapali: bool = False\n")],
           "KONTROL: yalniz tip ek aciklamasi", "-- kontrol --", kontrol=True),
    Mutant("C04", MOTOR,
           [_y('            "Global.use_cls": False,  # K3 / O3\n            "Global.log_level": "error",  # K7 (kurulum sirasi)\n',
               '            "Global.log_level": "error",  # K7 (kurulum sirasi)\n            "Global.use_cls": False,  # K3 / O3\n')],
           "KONTROL: sozluk anahtar sirasi degisti", "-- kontrol --", kontrol=True),
]


def _kapi_kos(argv: list[str]) -> tuple[int, str, float]:
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    t0 = time.perf_counter()
    r = subprocess.run(argv, cwd=str(KOK), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=env, timeout=600)
    return r.returncode, (r.stdout or "") + (r.stderr or ""), time.perf_counter() - t0


def _uygula(mut: Mutant) -> None:
    for rel, yamalar in [(mut.dosya, mut.yamalar), *mut.ek]:
        p = KOK / rel
        metin = p.read_text(encoding="utf-8")
        for eski, yeni in yamalar:
            if metin.count(eski) != 1:
                raise SystemExit(f"{mut.mid}: yama hedefi {metin.count(eski)} kez bulundu (1 olmali) -> {rel}\n{eski[:200]!r}")
            metin = metin.replace(eski, yeni, 1)
        p.write_text(metin, encoding="utf-8")


def _geri_al() -> None:
    for rel in GERI_ALINAN:
        shutil.copyfile(DEPO / rel, KOK / rel)


def _ayna_kur() -> None:
    if KOK.exists():
        shutil.rmtree(KOK, ignore_errors=True)
    yoksay = shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache", ".mypy_cache")
    for ad in AYNALANAN_DIZINLER:
        shutil.copytree(DEPO / ad, KOK / ad, ignore=yoksay)
    for ad in AYNALANAN_DOSYALAR:
        (KOK / ad).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(DEPO / ad, KOK / ad)


def _ilk_hata(ad: str, ozet: str) -> str:
    for ln in ozet.splitlines():
        if any(k in ln for k in ("IHLAL", "error:", "failed", "Required test coverage", "RuntimeError", "Error")):
            return f"{ad}: {ln.strip()[:120]}"
    return f"{ad}: (ilk hata satiri bulunamadi)"


def main() -> None:
    secilen = set(sys.argv[1:])
    _ayna_kur()
    print(f"ayna agaci: {KOK}   (depo YAZILMAZ)")
    print("kapilar PYTHONIOENCODING=utf-8 ile kosar (real_check cp1254'te coker -- kit notu)")
    print()
    basliklar = [ad for ad, _ in KAPILAR]

    # 0 -- TABAN: mutasyonsuz ayna agacinda bes kapi da gecmeli; aksi halde tablo anlamsiz.
    print("TABAN (mutasyonsuz ayna):")
    taban_ok = True
    for ad, argv in KAPILAR:
        rc, ozet, sn = _kapi_kos(argv)
        son = [l for l in ozet.strip().splitlines() if l.strip()][-1:] or [""]
        print(f"  {ad:10s} exit={rc}  {sn:5.1f}s  {son[0][:90]}")
        taban_ok = taban_ok and rc == 0
    if not taban_ok:
        raise SystemExit("TABAN GECMEDI -- ayna agaci bozuk, mutant tablosu uretilmedi")
    print()

    satirlar: list[str] = []
    kacan: list[str] = []
    yakalanan_kontrol: list[str] = []
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
            for ad, argv in KAPILAR:
                rc, ozet, _ = _kapi_kos(argv)
                isaretler.append("X" if rc != 0 else ".")
                if rc != 0:
                    detaylar.append(_ilk_hata(ad, ozet))
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
            print(f"{mut.mid:5s} [{durum}] {etiket}")
            print(f"       {mut.aciklama}")
            print(f"       hedef: {mut.hedef}")
            for d in detaylar:
                print(f"       | {d}")
            satirlar.append(f"| {mut.mid} | {mut.aciklama} | {mut.hedef} | " + " | ".join(isaretler) + " |")
            sys.stdout.flush()
        finally:
            _geri_al()

    print()
    print("=== MARKDOWN TABLOSU ===")
    print("| # | mutant | hedef | " + " | ".join(basliklar) + " |")
    print("|---|---|---|" + "---|" * len(basliklar))
    for s in satirlar:
        print(s)
    print()
    if kacan:
        print(f"HICBIR KAPININ YAKALAMADIGI MUTANTLAR ({len(kacan)}): {', '.join(kacan)}")
    else:
        print("Kacan (kontrol olmayan) mutant yok.")
    if yakalanan_kontrol:
        print(f"YAKALANAN KONTROL MUTANTLARI = YANLIS POZITIF ({len(yakalanan_kontrol)}): {', '.join(yakalanan_kontrol)}")
    else:
        print("Kontrol mutantlarinin hepsi kacti (yanlis pozitif yok).")


if __name__ == "__main__":
    main()
