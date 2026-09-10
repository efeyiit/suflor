"""TESTER-D mutant kiti -- kapilarin AYIRT ETME GUCUNU olcer.

Mercek D sorusu: "olcu var gorunuyor ama gercekten bir sey olcuyor mu?"
Tek cevap yontemi: uygulamayi bozup **hangi kapinin yakaladigini** saymak.
Hicbir kapinin yakalamadigi bir mutant, o degismezin ölçüsünün BOS oldugunu
kanitlar.

`src/` DEGISTIRILMEZ. Depo `scratchpad/mutroot/` altina bir kez kopyalanir,
mutasyon orada yapilir ve her mutanttan sonra dosya geri yazilir.

Kosum:  python .agents/tasks/T-005/tester_D/mutant_kiti.py [mutant_id ...]
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

DEPO = Path(__file__).resolve().parents[4]
# Ayna agaci depo DISINDA durur; `src/` ve `tests/` asla yazilmaz.
# `TESTER_D_SCRATCH` ile baska bir yere alinabilir.
SCRATCH = Path(os.environ.get("TESTER_D_SCRATCH", tempfile.gettempdir()))
KOK = SCRATCH / "t005_tester_D_mutroot"
AYNALANAN = ("src", "tests")
KAPI_REL = Path(".agents") / "tasks" / "T-005" / "headless_check.py"

SERVICE = "src/capture/service.py"
MONITORS = "src/capture/monitors.py"
CONFTEST = "tests/unit/capture/conftest.py"

# Paketin BES kabul komutu -- kapilarin kendisi.
KAPILAR: list[tuple[str, list[str]]] = [
    ("G1-mypy", [sys.executable, "-m", "mypy", "--strict", "--explicit-package-bases",
                 "src/capture/service.py", "src/capture/monitors.py"]),
    ("G2-pytest", [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                   "tests/unit/capture/test_service.py", "tests/unit/capture/test_monitors.py"]),
    ("G3-headless", [sys.executable, ".agents/tasks/T-005/headless_check.py"]),
    ("G4-kapsam", [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                   "tests/unit/capture/test_service.py", "tests/unit/capture/test_monitors.py",
                   "--cov=src.capture.service", "--cov=src.capture.monitors",
                   "--cov-fail-under=95", "--cov-report=term-missing"]),
    ("G5-tumdizin", [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                     "tests/unit/capture"]),
]


@dataclass
class Mutant:
    mid: str
    dosya: str
    yamalar: list[tuple[str, str]]
    aciklama: str
    hedef_degismez: str
    ek_dosyalar: list[tuple[str, list[tuple[str, str]]]] = field(default_factory=list)


def _y(eski: str, yeni: str) -> tuple[str, str]:
    return (eski, yeni)


MUTANTLAR: list[Mutant] = [
    # ---- K7 sahiplik ----------------------------------------------------
    Mutant(
        "M01", SERVICE,
        [_y('return np.array(ham[:, :, :3], dtype=np.uint8, copy=True, order="C")',
            "return np.ascontiguousarray(ham[:, :, :3])")],
        "kopya -> ascontiguousarray (4 kanalda kopyalar, 3 kanalda TAKMA AD)",
        "K7 sahiplik",
    ),
    Mutant(
        "M02", SERVICE,
        [_y('return np.array(ham[:, :, :3], dtype=np.uint8, copy=True, order="C")',
            "return np.frombuffer(np.ascontiguousarray(ham[:, :, :3]).tobytes(), "
            "dtype=np.uint8).reshape(ham.shape[0], ham.shape[1], 3)")],
        "kopya SALT-OKUNUR (frombuffer/tobytes): bellek paylasmiyor ama writeable=False",
        "K7 writeable -- `writeable` iddiasinin BAGIMSIZ gucu",
    ),
    # ---- K7 bicim: girdi SAYAN kural ------------------------------------
    Mutant(
        "M03", SERVICE,
        [_y("        if not isinstance(ham, np.ndarray):",
            "        if hasattr(ham, '__array_interface__') or hasattr(ham, '__array__'):"),
         _y("        if ham.ndim != 3:",
            "        ham = ham if isinstance(ham, np.ndarray) else np.asarray(ham)\n"
            "        if ham.ndim != 3:")],
        "TIP kurali -> GIRDI SAYAN kural: iki bicimi hasattr ile eler, gerisini np.asarray ile cevirir",
        "K7 `isinstance` tip duzeyi kurali (dort ayrisan bicim)",
    ),
    Mutant(
        "M04", SERVICE,
        [_y("        if not isinstance(ham, np.ndarray):",
            "        if False:"),
         _y("        if ham.ndim != 3:",
            "        ham = np.asarray(ham)\n        if ham.ndim != 3:")],
        "tip denetimi tamamen kaldirildi, her sey np.asarray ile cevriliyor",
        "K7 sessiz donusum yasagi",
    ),
    # ---- K10 MssBackend: sadece §3'un gorebilecegi ----------------------
    Mutant(
        "M05", SERVICE,
        [_y('kutu = {"left": rect.x, "top": rect.y, "width": rect.w, "height": rect.h}',
            'kutu = {"left": max(0, rect.x), "top": max(0, rect.y), '
            '"width": rect.w, "height": rect.h}')],
        "grab kutusunu 0'a KIRPAR (negatif sanal-masaustu koordinati)",
        "K10 kutu birebir -- olcunun IKI NOKTADA kosmasi (Y7-1)",
    ),
    Mutant(
        "M06", SERVICE,
        [_y("return np.asarray(self._tutamac.grab(kutu), dtype=np.uint8)",
            "return self._tutamac.grab(kutu)  # type: ignore[return-value]")],
        "grab HAM ScreenShot dondurur (np.ndarray degil)",
        "K10/K7 -- olcunun denetledigi koddan referans TURETMEMESI (Y6-2)",
    ),
    Mutant(
        "M07", SERVICE,
        [_y("        with mss.MSS() as oturum:\n            return [dict(ham) for ham in oturum.monitors]",
            "        oturum = mss.MSS()\n        return [dict(ham) for ham in oturum.monitors]")],
        "monitors() kurdugu MSS()'i KAPATMAZ (5001. cagrida GetWindowDC olur)",
        "K10 cagri basina tam 1 kapatma",
    ),
    Mutant(
        "M08", SERVICE,
        [_y("        with mss.MSS() as oturum:\n            return [dict(ham) for ham in oturum.monitors]",
            "        onbellek: object = getattr(self, '_mon_onbellek', None)\n"
            "        if onbellek is not None:\n"
            "            return onbellek  # type: ignore[return-value]\n"
            "        with mss.MSS() as oturum:\n"
            "            sonuc = [dict(ham) for ham in oturum.monitors]\n"
            "        self._mon_onbellek = sonuc  # type: ignore[attr-defined]\n"
            "        return sonuc")],
        "monitors() sonucu ONBELLEKLER (canli degil)",
        "K10 canlilik",
    ),
    Mutant(
        "M09", SERVICE,
        [_y("_uyum_fake: CaptureBackend = FakeBackend(())\n_uyum_mss: CaptureBackend = MssBackend()",
            "# uyum satirlari silindi")],
        "protokol uyum satirlari SILINDI",
        "K1/O-F uyum -- mekanizmanin varligi (Y5-1)",
    ),
    Mutant(
        "M10", SERVICE,
        [_y("_uyum_fake: CaptureBackend = FakeBackend(())\n_uyum_mss: CaptureBackend = MssBackend()",
            "_uyum_fake: CaptureBackend\n_uyum_mss: CaptureBackend")],
        "uyum satirlari CIPLAK ek aciklamaya dondu (deger yok -> mypy hicbir sey dogrulamaz)",
        "K1/O-F uyum -- degerin CAGRI olmasi (Y6-1)",
    ),
    Mutant(
        "M11", SERVICE,
        [_y("    def grab(self, rect: Rect) -> ImageArray:\n        self.grab_calls += 1",
            "    @_gecirgen\n    def grab(self, rect: Rect) -> ImageArray:\n        self.grab_calls += 1"),
         _y("def _ham_sozluk(rect: Rect) -> Mapping[str, object]:",
            "def _gecirgen(f: Any) -> Any:\n    return f\n\n\n"
            "def _ham_sozluk(rect: Rect) -> Mapping[str, object]:"),
         _y("from typing import TYPE_CHECKING, Protocol",
            "from typing import TYPE_CHECKING, Any, Protocol")],
        "FakeBackend.grab DEKORATORLU (mypy imzayi Any'ye dusurur)",
        "K1 uyum -- dekorator kacisi (Y7-5)",
    ),
    Mutant(
        "M12", SERVICE,
        [_y("    def __exit__(self, *_: object) -> None:\n        self.close()",
            "    def __exit__(self, *_: object) -> None:\n        return None")],
        "__exit__ close() CAGIRMAZ (baglam yoneticisi tutamaci sizdirir)",
        "K10 `__exit__` -> close()",
    ),
    Mutant(
        "M13", SERVICE,
        [_y("    def close(self) -> None:  # pragma: no cover"
            " -- K1: gercek ekran, headless_check §3 ile denetleniyor\n"
            "        if self._tutamac is not None:\n"
            "            self._tutamac.close()\n"
            "            self._tutamac = None",
            "    def close(self) -> None:  # pragma: no cover"
            " -- K1: gercek ekran, headless_check §3 ile denetleniyor\n"
            "        if self._tutamac is not None:\n"
            "            self._tutamac.close()")],
        "close() idempotent DEGIL (tutamaci None yapmaz -> ikinci close tekrar kapatir)",
        "K10 close idempotent",
    ),
    # ---- K5/K8 duzlestirme ---------------------------------------------
    Mutant(
        "M14", MONITORS,
        [_y("    return int(deger)", "    return cast(int, deger)"),
         _y("from typing import Protocol", "from typing import Protocol, cast")],
        "monitors.py: int(v) yerine cast(int, v) -- numpy skaleri Rect'e sizar",
        "K5 duzlestirme (Y-C)",
    ),
    Mutant(
        "M15", MONITORS,
        [_y("    return int(deger)",
            "    return int(deger) if isinstance(deger, np.int64) else cast(int, deger)"),
         _y("from typing import Protocol", "from typing import Protocol, cast"),
         _y("import numbers", "import numbers\n\nimport numpy as np")],
        "monitors.py: YALNIZ np.int64 duzlestirilir; int32/uint8 sizar",
        "K5 duzlestirme olcusunun DORT TIPTE kosmasi (Y5-6)",
    ),
    Mutant(
        "M16", SERVICE,
        [_y("    if isinstance(deger, numbers.Integral):\n        return int(deger)",
            "    if isinstance(deger, numbers.Integral):\n"
            "        return deger if isinstance(deger, (np.int32, np.uint8)) "
            "else int(deger)  # type: ignore[return-value]")],
        "capture_region girisi: YALNIZ int64/int duzlesir; int32/uint8 Frame.rect'e sizar",
        "K8 duzlestirme olcusunun DORT TIPTE kosmasi (Y6-5)",
    ),
    Mutant(
        "M17", SERVICE,
        [_y("    if isinstance(deger, bool):\n"
            "        raise CaptureError(f\"bolge alani '{ad}' tamsayi olmali, gelen: {deger!r}\")\n"
            "    if isinstance(deger, numbers.Integral):\n        return int(deger)\n"
            "    if isinstance(deger, (float, np.floating)):\n"
            "        sayi = float(deger)\n        if sayi.is_integer():\n            return int(sayi)\n"
            "    raise CaptureError(f\"bolge alani '{ad}' tamsayi olmali, gelen: {deger!r}\")",
            "    return int(deger)  # type: ignore[call-overload]")],
        "giris KABUL KAPISI kaldirildi, ciplak int() (10.9 -> 10, '10'/True sessizce kabul)",
        "K8 kabul kapisi (Y7-3)",
    ),
    Mutant(
        "M18", SERVICE,
        [_y("    if isinstance(deger, bool) or not isinstance(deger, (int, float, np.floating, np.integer)):\n"
            "        raise CaptureError(f\"bolge alani 'dpi_scale' sayi olmali, gelen: {deger!r}\")\n"
            "    return float(deger)",
            "    return deger  # type: ignore[return-value]")],
        "dpi_scale duzlestirmesi kaldirildi (np.float32 Frame.rect'e sizar)",
        "K8 dpi_scale float duzlestirmesi",
    ),
    Mutant(
        "M19", SERVICE,
        [_y("        duz = self._duzlestir(rect)", "        duz = rect")],
        "capture_region girisinde duzlestirme HIC yapilmaz",
        "K8 giristeki duzlestirme (isaretsiz numpy tasmasi)",
    ),
    # ---- K4 kirpma / K8 monitor_index ------------------------------------
    Mutant(
        "M20", SERVICE,
        [_y("            birlesim = union_bbox(self._monitors)",
            "            birlesim = self._monitors[0]")],
        "PARTIAL kirpmasi TEK MONITORE gore (birlesime degil)",
        "K4 kirpma birlesime gore",
    ),
    Mutant(
        "M21", SERVICE,
        [_y("        return kesisen[0] if len(kesisen) == 1 else -1",
            "        return kesisen[0] if kesisen else -1")],
        "monitor_index: 1'den fazla kesisimde -1 yerine ILKI dondurulur",
        "K8 monitor_index -1 kurali",
    ),
    Mutant(
        "M22", SERVICE,
        [_y("            monitor_index=self._monitor_indeksi(aday),",
            "            monitor_index=duz.monitor_index,")],
        "monitor_index: cagiranin degeri kullanilir (hesaplanmaz)",
        "K8 monitor_index hesaplanir",
    ),
    # ---- K5 durum / K6 taksonomi -----------------------------------------
    Mutant(
        "M23", SERVICE,
        [_y("        yeni = list_monitors(self._backend)\n        self._monitors = yeni\n        return yeni",
            "        self._monitors = ()\n        yeni = list_monitors(self._backend)\n"
            "        self._monitors = yeni\n        return yeni")],
        "refresh_monitors hata yolunda ESKI KUMEYI KAYBEDER",
        "K5 durum degismezi",
    ),
    Mutant(
        "M24", SERVICE,
        [_y("            self._bicimi_dogrula(ham, hedef, deneme)\n            return self._kopyala(ham)",
            "            try:\n                self._bicimi_dogrula(ham, hedef, deneme)\n"
            "            except CaptureError as exc:\n                son_istisna = exc\n"
            "                continue\n            return self._kopyala(ham)")],
        "K6 sinif (c) YENIDEN DENENIR (3 cagri) ve __cause__ baglanir",
        "K6 (c): 1 cagri, __cause__ None",
    ),
    Mutant(
        "M25", SERVICE,
        [_y("        duz = self._duzlestir(rect)\n        hedef = self._hedef_dikdortgen(duz)\n"
            "        goruntu = self._backend_dan_al(hedef)\n        self._seq += 1",
            "        self._seq += 1\n        duz = self._duzlestir(rect)\n"
            "        hedef = self._hedef_dikdortgen(duz)\n        goruntu = self._backend_dan_al(hedef)")],
        "seq basarisiz yakalamalarda da TUKETILIR",
        "K2 seq tuketilmez",
    ),
    Mutant(
        "M26", SERVICE,
        [_y("        if not 0 <= monitor_index < len(self._monitors):",
            "        if not -len(self._monitors) <= monitor_index < len(self._monitors):")],
        "capture_full NEGATIF indeksi kabul eder (Python dilimlemesi)",
        "K9 aralik disi",
    ),
    Mutant(
        "M27", SERVICE,
        [_y("        self._monitors: tuple[Rect, ...] = list_monitors(backend)",
            "        self._monitors: tuple[Rect, ...] = ()")],
        "yapimda monitor kumesi HIC okunmaz",
        "K5 okuma zamani",
    ),
    Mutant(
        "M28", MONITORS,
        [_y("    for i, ham in enumerate(dicts[1:]):", "    for i, ham in enumerate(dicts):")],
        "rects_from_mss_monitors [0] birlesim girdisini ATMAZ",
        "K5 bicim",
    ),
    # ---- K1 conftest engeli ---------------------------------------------
    Mutant(
        "M29", CONFTEST,
        [_y('@pytest.fixture(scope="session", autouse=True)',
            '@pytest.fixture(scope="function", autouse=True)')],
        "engel fixture'i oturum degil FONKSIYON kapsamli",
        "K1 oturum kapsami",
    ),
    Mutant(
        "M30", CONFTEST,
        [_y("    modul = types.ModuleType(\"mss\")",
            "    import importlib\n    try:\n        modul = importlib.import_module('mss')\n"
            "    except Exception:\n        modul = types.ModuleType('mss')\n    return modul\n"
            "    modul = types.ModuleType(\"mss\")")],
        "engel modul GERCEK mss'e devreder",
        "K1 engel devretmez",
    ),
    # ---- K13 kapsam yalani ----------------------------------------------
    Mutant(
        "M31", SERVICE,
        [_y("    def refresh_monitors(self) -> tuple[Rect, ...]:",
            "    def refresh_monitors(self) -> tuple[Rect, ...]:  # pragma: no cover")],
        "FAZLADAN `# pragma: no cover` (K13'un yasakladigi yer)",
        "K13 'baska no cover yasak' -- makinenin GORMEDIGI kural",
    ),
    Mutant(
        "M32", SERVICE,
        [_y("    def capture_full(self, monitor_index: int) -> Frame:",
            "    def capture_full(self, monitor_index: int) -> Frame:  # pragma: no cover"),
         _y("    def _monitor_indeksi(self, hedef: Rect) -> int:",
            "    def _monitor_indeksi(self, hedef: Rect) -> int:  # pragma: no cover"),
         _y("    def _backend_dan_al(self, hedef: Rect) -> ImageArray:",
            "    def _backend_dan_al(self, hedef: Rect) -> ImageArray:  # pragma: no cover")],
        "UC fazladan pragma (capture_full + _monitor_indeksi + _backend_dan_al)",
        "K13 kapsam esigi fazladan pragmayi GORMEZ",
    ),
    # ---- [OLCULMUYOR] damgasinin dogrulugu -------------------------------
    Mutant(
        "M33", SERVICE,
        [_y("        return self.capture_region(self._monitors[monitor_index])",
            "        m = self._monitors[monitor_index]\n"
            "        return self.capture_region(Rect(_np64(m.x), _np64(m.y), "
            "_np64(m.w), _np64(m.h), m.monitor_index, m.dpi_scale))"),
         _y("def _ham_sozluk(rect: Rect) -> Mapping[str, object]:",
            "def _np64(v: int) -> int:\n"
            "    \"\"\"numpy skaleri uretir ama mypy'ye `int` gorunur (cast kacisi).\"\"\"\n"
            "    return np.int64(v)  # type: ignore[return-value]\n\n\n"
            "def _ham_sozluk(rect: Rect) -> Mapping[str, object]:")],
        "capture_full numpy skaleri ENJEKTE eder (paketin [OLCULMUYOR] damgaladigi bacak)",
        "K8 capture_full duzlestirme bacagi -- damganin dogrulugu",
    ),
    # ---- ikinci dalga: bosluk avi ----------------------------------------
    Mutant(
        "M34", SERVICE,
        [_y("        self.raw_override = raw_override",
            "        self._raw_override = raw_override"),
         _y("        if self.raw_override is not None:\n            return self.raw_override",
            "        if self._raw_override is not None:\n            return self._raw_override")],
        "FakeBackend raw_override'i OZEL adla saklar (tester'in mutasyonu sessizce kaybolur)",
        "K1 FakeBackend sozlesmesi -- public mutasyon arayuzu",
    ),
    Mutant(
        "M35", SERVICE,
        [_y("        kutu = {\"left\": rect.x, \"top\": rect.y, \"width\": rect.w, \"height\": rect.h}\n"
            "        return np.asarray(self._tutamac.grab(kutu), dtype=np.uint8)",
            "        kutu = {\"left\": rect.x, \"top\": rect.y, \"width\": rect.w, \"height\": rect.h}\n"
            "        ham = np.asarray(self._tutamac.grab(kutu), dtype=np.uint8)\n"
            "        self._tutamac.close()\n"
            "        self._tutamac = None\n"
            "        return ham")],
        "grab her cagrida tutamaci kapatip birakir (uzun omurlu DEGIL)",
        "K10 uzun omurlu tutamac (sicak yol maliyeti)",
    ),
    Mutant(
        "M36", SERVICE,
        [_y("        if self._tutamac is not None:\n"
            "            self._tutamac.close()\n"
            "            self._tutamac = None",
            "        self._tutamac = None")],
        "close() tutamaci SIZDIRIR (alttaki MSS()'i hic kapatmaz)",
        "K10 close() gercekten kapatir",
    ),
    Mutant(
        "M37", SERVICE,
        [_y("        goruntu = self._backend_dan_al(hedef)",
            "        kirpilmadi = (hedef.x, hedef.y, hedef.w, hedef.h) == (duz.x, duz.y, duz.w, duz.h)\n"
            "        backend_hedefi = Rect(rect.x, rect.y, rect.w, rect.h,\n"
            "                              hedef.monitor_index, hedef.dpi_scale) if kirpilmadi else hedef\n"
            "        goruntu = self._backend_dan_al(backend_hedefi)")],
        "backend'e DUZLESTIRILMEMIS geometri gider; Frame.rect duz kalir (K3 `==` gormez)",
        "K8 duzlestirme -- olcunun `==` ile yazilmasi",
    ),
    Mutant(
        "M42", SERVICE,
        [_y("    def __init__(self) -> None:\n        self._tutamac: mss.MSS | None = None",
            "    def __init__(self) -> None:\n        self._tutamac: mss.MSS | None = None\n"
            "        self._sizinti: list[object] = []")],
        "kontrol mutanti: zararsiz ekleme (kapilar yanlis pozitif vermemeli)",
        "-- kontrol --",
    ),
    Mutant(
        "M43", SERVICE,
        [_y("    def monitors(self) -> tuple[Rect, ...]:\n"
            '        """Servisin ONBELLEKTEKI monitor kumesi',
            "    def monitors(self) -> tuple[Rect, ...]:\n"
            "        return tuple(self._monitors)\n"
            '        """Servisin ONBELLEKTEKI monitor kumesi')],
        "CaptureService.monitors ozelligi KOPYA dondurur (docstring ulasilmaz olur)",
        "-- kontrol: ozelligin gozlemlenebilirligi --",
    ),
    Mutant(
        "M44", SERVICE,
        [_y("    return np.zeros((rect.h, rect.w, 4), dtype=np.uint8)",
            "    return np.zeros((rect.h, rect.w, 3), dtype=np.uint8)")],
        "FakeBackend varsayilan ureticisi 4 kanal yerine 3 kanal dondurur",
        "K1 FakeBackend varsayilan sozlesmesi",
    ),
    Mutant(
        "M45", SERVICE,
        [_y("        self.grab_calls += 1\n        self.grab_rects.append(rect)",
            "        self.grab_calls += 1")],
        "FakeBackend grab_rects'i KAYDETMEZ (K3/K9 gozlem kanali kapanir)",
        "K1 FakeBackend gozlem oznitelikleri",
    ),
    Mutant(
        "M38", MONITORS,
        [_y("    return Rect(x=x, y=y, w=sag - x, h=alt - y, monitor_index=-1, dpi_scale=1.0)",
            "    return Rect(x=x, y=y, w=sag - x, h=alt - y, monitor_index=0, dpi_scale=1.0)")],
        "union_bbox monitor_index=-1 yerine 0 yazar",
        "K5 union_bbox metadata",
    ),
    Mutant(
        "M39", MONITORS,
        [_y("    return rects_from_mss_monitors(backend.monitors())",
            "    try:\n        return rects_from_mss_monitors(backend.monitors())\n"
            "    except CaptureError:\n        raise\n"
            "    except Exception as exc:\n"
            "        raise CaptureError(f'monitor okunamadi: {exc}') from exc")],
        "list_monitors backend istisnasini SARMALAR (oldugu gibi yaymaz)",
        "K5 istisna oldugu gibi yayilir",
    ),
    Mutant(
        "M40", SERVICE,
        [_y("        if ham.shape[0] != hedef.h or ham.shape[1] != hedef.w:",
            "        if False:")],
        "K7 boyut (h, w) uyusma denetimi kaldirildi",
        "K7 bicim -- boyut uyusmazligi",
    ),
    Mutant(
        "M41", SERVICE,
        [_y("    def __enter__(self) -> MssBackend:\n        return self",
            "    def __enter__(self) -> MssBackend:\n        return MssBackend()")],
        "__enter__ BASKA bir ornek dondurur",
        "K10 baglam yoneticisi",
    ),
    Mutant(
        "M46", SERVICE,
        [_y("            return [dict(ham) for ham in oturum.monitors]",
            "            return oturum.monitors  # type: ignore[no-any-return]")],
        "monitors() ham listeyi KOPYALAMADAN dondurur",
        "K10 -- paket bunu 'uygulama tercihi, kapi DEGIL' diyor (Y7-2); damga durust mu",
    ),
    Mutant(
        "M47", SERVICE,
        [_y("ham: list[Mapping[str, object]] = [_ham_sozluk(kok)]",
            "ham: list[Mapping[str, object]] = []")],
        "FakeBackend.monitors() [0] birlesim girdisini KOYMAZ (ilk monitoru yutar)",
        "K1 FakeBackend bicim sozlesmesi",
    ),
    Mutant(
        "M48", SERVICE,
        [_y("_DENEME_SAYISI = 3", "_DENEME_SAYISI = 2")],
        "K6 (b) yeniden deneme sayisi 3 yerine 2",
        "K6 (b) en fazla 3 cagri",
    ),
    Mutant(
        "M49", SERVICE,
        [_y("        self._seq = -1", "        self._seq = 0")],
        "ilk basarili yakalama seq=1 olur (0 degil)",
        "K2 ilk yakalama seq=0",
    ),
]


def _kapi_kos(ad: str, argv: list[str]) -> tuple[int, str]:
    r = subprocess.run(argv, cwd=str(KOK), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    ozet = (r.stdout or "") + (r.stderr or "")
    return r.returncode, ozet


def _uygula(mut: Mutant) -> list[Path]:
    dokunulan: list[Path] = []
    gruplar = [(mut.dosya, mut.yamalar), *mut.ek_dosyalar]
    for rel, yamalar in gruplar:
        p = KOK / rel
        metin = p.read_text(encoding="utf-8")
        for eski, yeni in yamalar:
            if eski not in metin:
                raise SystemExit(f"{mut.mid}: yama hedefi bulunamadi -> {rel}\n{eski[:160]!r}")
            metin = metin.replace(eski, yeni, 1)
        p.write_text(metin, encoding="utf-8")
        dokunulan.append(p)
    return dokunulan


def _geri_al() -> None:
    for rel in (SERVICE, MONITORS, CONFTEST):
        shutil.copyfile(DEPO / rel, KOK / rel)


def _ayna_kur() -> None:
    """Ayna agacini kurar (yoksa) -- kit kendi kendine yeter, sef de kosabilir."""
    for ad in AYNALANAN:
        hedef = KOK / ad
        if hedef.exists():
            shutil.rmtree(hedef, ignore_errors=True)
        shutil.copytree(DEPO / ad, hedef,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc",
                                                      ".pytest_cache"))
    (KOK / KAPI_REL.parent).mkdir(parents=True, exist_ok=True)
    shutil.copyfile(DEPO / KAPI_REL, KOK / KAPI_REL)


def main() -> None:
    secilen = set(sys.argv[1:])
    _ayna_kur()
    print(f"ayna agaci: {KOK}   (depo YAZILMAZ)")
    _geri_al()

    satirlar: list[str] = []
    basliklar = [ad for ad, _ in KAPILAR]
    print("MUTANT KITI -- her mutant icin hangi kapi YAKALAR (X) / KACIRIR (.)")
    print("kapilar: " + " | ".join(basliklar))
    print()
    kacan: list[str] = []
    for mut in MUTANTLAR:
        if secilen and mut.mid not in secilen:
            continue
        _uygula(mut)
        try:
            isaretler = []
            detaylar = []
            for ad, argv in KAPILAR:
                rc, ozet = _kapi_kos(ad, argv)
                isaretler.append("X" if rc != 0 else ".")
                if rc != 0:
                    ilk = next((ln for ln in ozet.splitlines()
                                if ("IHLAL" in ln or "error:" in ln or "failed" in ln
                                    or "Required test coverage" in ln)), "")
                    detaylar.append(f"{ad}:{ilk.strip()[:110]}")
            durum = "".join(isaretler)
            yakalandi = "X" in durum
            if not yakalandi:
                kacan.append(mut.mid)
            print(f"{mut.mid} [{durum}] {'YAKALANDI' if yakalandi else '*** HICBIR KAPI YAKALAMADI ***'}")
            print(f"     {mut.aciklama}")
            print(f"     hedef degismez: {mut.hedef_degismez}")
            for d in detaylar:
                print(f"     | {d}")
            satirlar.append(f"| {mut.mid} | {mut.aciklama} | {mut.hedef_degismez} | "
                            + " | ".join(isaretler) + " |")
        finally:
            _geri_al()
    print()
    print("=== MARKDOWN TABLOSU ===")
    print("| # | mutant | hedef degismez | " + " | ".join(basliklar) + " |")
    print("|---|---|---|" + "---|" * len(basliklar))
    for s in satirlar:
        print(s)
    print()
    if kacan:
        print(f"HICBIR KAPININ YAKALAMADIGI MUTANTLAR ({len(kacan)}): {', '.join(kacan)}")
    else:
        print("Kacan mutant yok.")


if __name__ == "__main__":
    main()
