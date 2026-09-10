"""CaptureService headless denetimi, surum 8 (Ortam Ajani + sef).

Surum 7 kirmizi takimdan dondu (16 bulgu, 2 yuksek):
  Y7-1  §3'un `grab_args` denetimi TEK NOKTADA olcuyordu (`Rect(10,20,64,16)`,
        hepsi pozitif). Negatif sanal-masaustu koordinatini 0'a KIRPAN bir grab
        bes kapidan da geciyordu -- bu makinenin gercek duzeninde (sol monitor
        x=-2560) her yakalama sessizce yanlis piksel verirdi. Artik IKI noktada:
        pozitif ve `Rect(-2600,-50,64,16)`.
  Y7-4  §5 dort iddiayi `elif` zinciriyle olcuyordu, yani ilki duserse gerisi
        HIC kosmuyordu; `tumuyle_sifir` hesaplaniyor ama kullanilmiyordu.
        Artik her iddia AYRI olculuyor; `tumuyle_sifir` KOSULSUZ ihlal.
  Y7-5  Bir dekorator `grab`in imzasini mypy'de `Any`'ye dusurup uyum
        satirlarinin garantisini bosaltiyordu. Artik §4 `decorator_list`in bos
        olmasini arar VE calisma zamaninda `isinstance(FakeBackend(()),
        CaptureBackend)` olculur (ad/kalitim/dekorator hilelerinden bagimsiz).
  Y7-7  §3'un `type(a1) is np.ndarray` katiligi K7'nin `isinstance` degismezinden
        GENISTI ve hata mesaji olgusal olarak yanlisti (servis alt sinifi
        reddetmiyor). Artik `isinstance` ihlal, `type is` degilse UYARI.

Surum 6 kirmizi takimdan dondu (14 bulgu, 2 yuksek). Ikisi de ayni sinif:
KAPI, DEGISMEZI DEGIL MEKANIZMANIN ADINI kancaliyordu (PROTOKOL 4.6/7).
  Y6-1  §4'un uyum kapisi `AnnAssign`in DEGERINI denetlemiyordu: ciplak
        `_uyum_fake: CaptureBackend` (deger yok) kapiyi geciyor ve mypy hicbir
        uyum dogrulamiyor. Ustelik `grab` bir taban sinifa tasinip donusu
        `np.ndarray | None` yapilinca (paketin YASAK dedigi bicim) ne kapi ne
        mypy goruyordu. Artik: deger bir CAGRI olmali, hedef sinif adi
        eslesmeli, `grab` FakeBackend'in KENDI govdesinde tanimli olmali.
  Y6-2  §3, grab donusunu `np.asarray(a1)` ile olcuyordu -- yani K7'nin
        yasakladigi SESSIZ DONUSUMU denetleyicinin icinde yapiyordu. Ham
        `ScreenShot` donduren bir MssBackend.grab bes kapidan da geciyor,
        gercek ekranla her yakalama CaptureError veriyordu. Artik once
        `type(a1) is np.ndarray` denetleniyor, `np.asarray` §3'te YOK.
  Y6-3  §4 dort mesru bicimde yanlis pozitif veriyordu (tirnakli aciklama,
        `ImageArray` takma adi, `if TYPE_CHECKING:` govdesi, tirnakli
        `"CaptureBackend"`). Hepsi kabul ediliyor.
  Y6-4  §1(d) uc mesru engel biciminde "fixture bulunamadi" diyordu
        (monkeypatch setitem, yardimci fonksiyon, `from sys import modules`).
        Tanima genisletildi; bulunamama artik IHLAL degil UYARI -- kapsam
        ayrimini iki dosyali calisma zamani sondasi zaten yapiyor.
  Y6-8  §5'in icerik iddiasi tek renkli masaustunde yanlis pozitif veriyordu.
        Artik KONUM SADAKATI kosulsuz olculuyor (sag yarim = tam grab'in sag
        yarisi), icerik iddiasi ise masaustu tek renkliyse ATLANIYOR.

Surum 5 kirmizi takimdan dondu (12 bulgu, 1 yuksek):
  Y5-1  K1'in protokol UYUM SATIRLARI (_uyum_fake / _uyum_mss) bir mekanizmaydi ve
        varligini hicbir kapi denetlemiyordu -- satirlari silen uygulama bes kabul
        komutundan da geciyordu (PROTOKOL 4.6/7'nin tarif ettigi hal). §4 artik
        AST ile bunlari ve FakeBackend.grab'in donus aciklamasini denetliyor.
  Y5-3  §1(d) conftest'teki HER autouse fixture'i session olmaya zorluyordu; mesru
        ikinci bir autouse fixture (ornegin numpy hata ayari) YANLIS POZITIF
        uretiyordu. Artik ENGEL fixture'i govdesinden secilir (sys.modules['mss']
        atamasi geceni), digerleri denetim disidir; sabit olmayan scope UYARI'dir.
  Y5-5  §5'in icerik iddiasi hem bostu (4 kanalli her grab'de alfa kanali tekil
        degeri 2'ye cikariyordu) hem kirilgandi (birincil monitorun 64x16'lik
        bloklarinin %68'i BGR'de tek renkli). Artik BIRINCIL MONITORUN TAMAMINDA
        np.unique(...) >= 8 olculuyor; 64x16 yalniz shape/dtype/writeable icin.

Surum 4 kirmizi takimdan dondu (13 bulgu): §1 scope="module"/"package" varyantlarini
scope="session"'dan ayirt edemiyordu (tek dosyalik sonda modul kapsaminda da ayni
nesneyi gorur) ve §5 (--real) icerik koruydu (np.zeros donduren grab temiz geciyordu).
v5: §1 hem conftest AST'sinde scope="session" arar hem de sondayi IKI dosyaya boler;
§5 dizinin tumuyle sifir olmadigini ve yazilabilir oldugunu assert eder.

Surum 3 kirmizi takimdan dondu (15 bulgu, 2 yuksek): §3'un casus ScreenShot'u
`__array_interface__['data']`'ya `id(bytearray)` veriyordu -- bu NESNE adresidir,
veri adresi degil (sinir disi okuma, buyuk kutuda segfault) -- ve grab() donusu
yalnizca shape/dtype ile olculuyordu (ekrani hic okumayan grab bes kapidan
geciyordu). §2 TYPE_CHECKING muafiyeti `else` dalini ayirt etmiyordu ve takma adi
reddediyordu; §1 fixture kapsamini olcmuyordu ve `mss.windows` iddiasi bostu.
Hepsi duzeltildi.

Dort kontrol (+1 istege bagli):
  §1  conftest.py'deki engel fixture'i GERCEKTEN calisiyor: alt-surecte pytest
      altinda (a) mss.MSS()/mss.mss() AssertionError, (b) engel modulun __file__'i
      yok ve gercek mss'in base/factory alt modullerini tasimiyor (devretmiyor),
      (c) IKI AYRI DOSYADAKI testler `import mss` ile AYNI nesneyi gorur (modul ve
      fonksiyon kapsami burada duser), (d) conftest AST'sinde autouse fixture
      scope="session" ilan ediyor (package kapsami burada duser) (K1).
  §2  service.py/monitors.py yuklenirken mss'e HIC import girisimi olmaz
      (sys.meta_path bulucusu try/except ve importlib kacislarini da gorur);
      AST: calisma zamani `import mss` bir fonksiyon govdesi ICINDE;
      `if TYPE_CHECKING:` GOVDESI (else dali degil; takma ad cozulur) muaf (K10).
  §3  Casus modul: sys.modules['mss'] yerine sayacli sahte modul konur. Casus
      ScreenShot gercek mss gibi `'data'` alanina tampon NESNESINI verir ve
      raw/bgra'yi desenli (01 02 03 FF) doldurur. Olculenler:
        - grab() donusunun HER pikseli casusun baytlari ([1,2,3,255] / [1,2,3])
        - MssBackend() yapimi MSS kurmaz (tembel)
        - monitors() cagri basina tam +1 kurulum, tam +1 kapatma, mss.mss() 0
        - monitors() donusu casusun ham listesine ESIT ([0] dahil, len 3)
        - iki cagri arasinda casus listesi degistirilir -> ikinci cagri yeniyi gorur
        - grab(): ilk cagrida +1 kurulum (uzun omurlu), ikinci cagrida +0;
          MSS.grab'e {'left','top','width','height'} sozlugu gider
        - close(): kapatma +1; ikinci close() sessiz (+0)
  §4  owns kapsamindaki BES dosyada Qt import'u yok; AYRICA service.py modul
      duzeyinde `_uyum_fake`/`_uyum_mss: CaptureBackend` satirlari VAR ve
      FakeBackend.grab'in donus aciklamasi tam olarak `np.ndarray` (Y5-1).
  §5  (istege bagli, --real) gercek mss ile duman: yalnizca sef kosar.

Kullanim:  python .agents/tasks/T-005/headless_check.py [--real]
Cikis:     0 = temiz, 1 = ihlal
Not:       §1 calisirken tests/unit/capture/ altina _hc_probe_k1_a.py, _hc_probe_k1_b.py
           ve _hc_probe_store.py gecici dosyalarini yazip siler; bu adlar owns disidir.
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys
import textwrap
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SERVICE = REPO / "src" / "capture" / "service.py"
MONITORS = REPO / "src" / "capture" / "monitors.py"
CONFTEST = REPO / "tests" / "unit" / "capture" / "conftest.py"
TEST_SERVICE = REPO / "tests" / "unit" / "capture" / "test_service.py"
TEST_MONITORS = REPO / "tests" / "unit" / "capture" / "test_monitors.py"
OWNS_SRC = [SERVICE, MONITORS]
OWNS_ALL = [SERVICE, MONITORS, CONFTEST, TEST_SERVICE, TEST_MONITORS]
QT = {"PySide6", "PySide2", "PyQt5", "PyQt6", "qtpy"}


def _run(code: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, "-X", "utf8", "-c", textwrap.dedent(code)],
                          cwd=str(REPO), capture_output=True, text=True, encoding="utf-8")


def _tail(s: str, n: int = 6) -> str:
    return "\n      ".join(s.strip().splitlines()[-n:]) if s.strip() else "(bos)"


# ---------------------------------------------------------------- §1
def _mss_modules_yazimi(node: ast.AST) -> bool:
    """`sys.modules`'a "mss" yazan HERHANGI bir mesru bicimi tanir (Y6-4).

    Taninan bicimler:
      sys.modules["mss"] = ...          modules["mss"] = ...   (from sys import modules)
      sys.modules.update({...})         mp.setitem(sys.modules, "mss", ...)  (monkeypatch)
    """
    for n in ast.walk(node):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if (isinstance(t, ast.Subscript)
                        and isinstance(t.slice, ast.Constant) and t.slice.value == "mss"
                        and ((isinstance(t.value, ast.Attribute) and t.value.attr == "modules")
                             or (isinstance(t.value, ast.Name) and t.value.id == "modules"))):
                    return True
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Attribute) and f.attr in ("setitem", "update"):
                metin = ast.unparse(n)
                if "modules" in metin and "mss" in metin:
                    return True
    return False


def _engel_fixture_mi(node: ast.AST, yardimcilar: dict[str, ast.AST]) -> bool:
    """ENGEL fixture'ini tanir: kendi govdesinde ya da CAGIRDIGI modul duzeyi
    yardimci fonksiyonda (bir duzey) sys.modules'a "mss" yazan (Y5-3, Y6-4).

    conftest.py'de baska mesru `autouse` fixture'lar olabilir (numpy hata ayari,
    saat dondurma, ...); onlari session olmaya zorlamak yanlis pozitiftir.
    """
    if _mss_modules_yazimi(node):
        return True
    for n in ast.walk(node):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
            hedef = yardimcilar.get(n.func.id)
            if hedef is not None and _mss_modules_yazimi(hedef):
                return True
    return False


def _conftest_scope_ast(errs: list[str]) -> None:
    """K1(d): ENGEL fixture'i AST'de scope="session" ilan ediyor mu (yalniz o)."""
    tree = ast.parse(CONFTEST.read_text(encoding="utf-8"), filename=str(CONFTEST))
    yardimcilar = {n.name: n for n in tree.body
                   if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    bulundu = False
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not _engel_fixture_mi(node, yardimcilar):
            continue
        for dec in node.decorator_list:
            if not isinstance(dec, ast.Call):
                continue
            kw = {k.arg: k.value for k in dec.keywords}
            autouse = kw.get("autouse")
            if not (isinstance(autouse, ast.Constant) and autouse.value is True):
                errs.append(f"§1(d) conftest.py:{node.lineno} engel fixture'i autouse=True degil -> K1")
                bulundu = True
                continue
            bulundu = True
            sc = kw.get("scope")
            if sc is None:
                errs.append(f"§1(d) conftest.py:{node.lineno} engel fixture'i scope ilan etmiyor "
                            f"(varsayilan 'function') -> K1")
            elif not isinstance(sc, ast.Constant):
                # sabit olmayan scope: ihlal DEGIL, uyari; kapsam ayrimini iki dosyali
                # calisma zamani sondasi yapar (Y5-3).
                print(f"  UYARI §1(d) conftest.py:{node.lineno} scope sabit dizge degil "
                      f"({ast.unparse(sc)}); kapsam yalnizca calisma zamani sondasiyla dogrulandi")
            elif sc.value != "session":
                errs.append(f"§1(d) conftest.py:{node.lineno} engel fixture'i scope=\"session\" degil: "
                            f"{sc.value!r} -> K1")
    if not bulundu:
        # Y6-4: bulunamama IHLAL DEGIL, UYARI. Kapsam ayrimini iki dosyali
        # calisma zamani sondasi zaten deterministik olarak yapiyor.
        print("  UYARI §1(d) conftest.py'de sys.modules'a \"mss\" yazan bir fixture AST ile "
              "taninamadi; kapsam yalnizca calisma zamani sondasiyla dogrulandi")


def check_1_conftest_barrier(errs: list[str]) -> None:
    """K1: engel fixture'i gercek mss'i durduruyor, devretmiyor ve oturum kapsamli mi."""
    if not CONFTEST.exists():
        errs.append("§1 tests/unit/capture/conftest.py yok -> K1 engel fixture'i eksik")
        return
    _conftest_scope_ast(errs)
    # Kapsam ayrimi icin sonda IKI dosyaya bolunur: modul/fonksiyon kapsaminda
    # engel modul dosyalar arasinda yeniden kurulur, oturum kapsaminda kurulmaz.
    d = REPO / "tests" / "unit" / "capture"
    store = d / "_hc_probe_store.py"
    pa = d / "_hc_probe_k1_a.py"
    pb = d / "_hc_probe_k1_b.py"
    store.write_text("GORULEN: list[object] = []\n", encoding="utf-8")
    pa.write_text(textwrap.dedent("""
        import pytest
        from _hc_probe_store import GORULEN
        def test_a_gercek_mss_engelli():
            import mss
            GORULEN.append(mss)
            with pytest.raises(AssertionError):
                mss.MSS()
            with pytest.raises(AssertionError):
                mss.mss()
        def test_b_engel_gercek_mss_degil():
            import mss
            assert getattr(mss, "__file__", None) is None, "engel modul gercek mss'e devrediyor"
            assert not hasattr(mss, "base") and not hasattr(mss, "factory"), \
                "engel modul gercek mss alt modullerini tasiyor"
        """), encoding="utf-8")
    pb.write_text(textwrap.dedent("""
        from _hc_probe_store import GORULEN
        def test_c_oturum_kapsami_dosyalar_arasi():
            import mss
            assert GORULEN, "ilk sonda dosyasi kosmadi"
            assert mss is GORULEN[0], (
                "engel modul DOSYALAR ARASINDA degisti -> fixture oturum kapsamli degil "
                "(scope='module' ya da 'function')")
        """), encoding="utf-8")
    try:
        r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                            str(pa), str(pb)],
                           cwd=str(d), capture_output=True, text=True, encoding="utf-8")
        if r.returncode != 0:
            errs.append("§1 K1 engel fixture'i CALISMIYOR / devrediyor / oturum kapsamli degil\n      "
                        + _tail(r.stdout, 10))
    finally:
        for f in (store, pa, pb):
            f.unlink(missing_ok=True)


# ---------------------------------------------------------------- §2
def _type_checking_names(tree: ast.Module) -> set[str]:
    names = {"TYPE_CHECKING"}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "typing":
            for a in node.names:
                if a.name == "TYPE_CHECKING":
                    names.add(a.asname or a.name)
    return names


def _is_tc_test(t: ast.expr, tc_names: set[str]) -> bool:
    return (isinstance(t, ast.Name) and t.id in tc_names) or \
           (isinstance(t, ast.Attribute) and t.attr == "TYPE_CHECKING")


def _in_type_checking_body(node: ast.AST, parents: dict[int, ast.AST],
                           branch: dict[int, str], tc_names: set[str]) -> bool:
    cur: ast.AST | None = node
    while cur is not None:
        par = parents.get(id(cur))
        if isinstance(par, ast.If) and _is_tc_test(par.test, tc_names) and branch.get(id(cur)) == "body":
            return True
        cur = par
    return False


def check_2_lazy_import(errs: list[str]) -> None:
    """K10: calisma zamani `import mss` yalnizca fonksiyon govdesinde; modul mss'e hic dokunmadan yuklenir."""
    for p in OWNS_SRC:
        if not p.exists():
            errs.append(f"§2 dosya yok: {p.relative_to(REPO)}")
            continue
        tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        tc_names = _type_checking_names(tree)
        parents: dict[int, ast.AST] = {}
        branch: dict[int, str] = {}
        for node in ast.walk(tree):
            for ch in ast.iter_child_nodes(node):
                parents[id(ch)] = node
            if isinstance(node, ast.If):
                for ch in node.body:
                    branch[id(ch)] = "body"
                for ch in node.orelse:
                    branch[id(ch)] = "orelse"
        for node in ast.walk(tree):
            mod = None
            if isinstance(node, ast.Import):
                mod = next((a.name for a in node.names if a.name.split(".")[0] == "mss"), None)
            elif isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] == "mss":
                mod = node.module
            if mod is None:
                continue
            if _in_type_checking_body(node, parents, branch, tc_names):
                continue  # calisma zamani etkisi sifir; serbest
            if p is MONITORS:
                errs.append(f"§2 monitors.py:{node.lineno} mss import ediyor -> saf kalmali (K5)")
                continue
            cur: ast.AST | None = node
            inside_fn = False
            while cur is not None:
                cur = parents.get(id(cur))
                if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    inside_fn = True
                    break
            if not inside_fn:
                errs.append(f"§2 service.py:{node.lineno} calisma zamani `import mss` fonksiyon govdesi "
                            f"DISINDA (try/except, TYPE_CHECKING else dali dahil) -> K10")
    r = _run(f"""
        import sys, importlib.abc
        attempts = []
        class _F(importlib.abc.MetaPathFinder):
            def find_spec(self, name, path, target=None):
                if name.split('.')[0] == 'mss':
                    attempts.append(name)
                    raise ImportError('mss yasak (headless sonda)')
                return None
        sys.meta_path.insert(0, _F())
        sys.modules.pop('mss', None)
        sys.path.insert(0, r'{REPO}')
        import src.capture.service, src.capture.monitors
        print('ATTEMPTS=' + repr(attempts))
    """)
    line = next((ln for ln in r.stdout.splitlines() if ln.startswith("ATTEMPTS=")), None)
    if r.returncode != 0 or line is None:
        errs.append("§2 service.py/monitors.py mss OLMADAN import edilemiyor -> K10\n      " + _tail(r.stderr))
    elif line != "ATTEMPTS=[]":
        errs.append(f"§2 modul yuklenirken mss import GIRISIMI var ({line[9:]}) -> K10: try/except ile de olsa yasak")


# ---------------------------------------------------------------- §3
_SPY_PROBE = """
    import sys, types, json
    sys.path.insert(0, r'{repo}')
    import numpy as np
    from src.contracts.models import Rect

    RAW = [
        {{'left': -2560, 'top': 0, 'width': 5120, 'height': 1440}},
        {{'left': -2560, 'top': 0, 'width': 2560, 'height': 1440, 'is_primary': False, 'name': 'A', 'unique_id': 'a'}},
        {{'left': 0, 'top': 0, 'width': 2560, 'height': 1440, 'is_primary': True, 'name': 'B', 'unique_id': 'b'}},
    ]
    state = {{'raw': RAW, 'MSS': 0, 'mss': 0, 'close': 0, 'grab_args': []}}
    PATTERN = b'\\x01\\x02\\x03\\xff'

    class _Shot:
        # gercek mss.ScreenShot gibi: 'data' alaninda TAMPON NESNESI (adres degil)
        def __init__(self, box):
            self.width, self.height = box['width'], box['height']
            self.size = (self.width, self.height)
            self.raw = bytearray(PATTERN * (self.width * self.height))
            self.bgra = bytes(self.raw)
        @property
        def __array_interface__(self):
            return {{'shape': (self.height, self.width, 4), 'typestr': '|u1', 'data': self.raw, 'version': 3}}

    class _FakeMSS:
        def __init__(self, **kw):
            state['MSS'] += 1
            self._closed = False
            self._monitors = None
        @property
        def monitors(self):
            if self._monitors is None:
                self._monitors = [dict(m) for m in state['raw']]   # memoize gibi
            return self._monitors
        def grab(self, box):
            state['grab_args'].append(dict(box) if isinstance(box, dict) else repr(box))
            return _Shot(box)
        def close(self):
            if not self._closed:
                state['close'] += 1
                self._closed = True
        def __enter__(self): return self
        def __exit__(self, *a):
            self.close(); return False

    def _dep(*a, **k):
        state['mss'] += 1
        return _FakeMSS()

    spy = types.ModuleType('mss'); spy.MSS = _FakeMSS; spy.mss = _dep
    sys.modules['mss'] = spy
    from src.capture.service import MssBackend

    out = {{}}
    b = MssBackend()
    out['init_MSS'] = state['MSS']
    m1 = b.monitors(); out['m1_MSS'] = state['MSS']; out['m1_close'] = state['close']
    out['m1_eq_raw'] = [dict(x) for x in m1] == RAW
    out['m1_len'] = len(m1)
    state['raw'] = RAW[:2]
    m2 = b.monitors(); out['m2_MSS'] = state['MSS']; out['m2_close'] = state['close']
    out['m2_len'] = len(m2)
    out['dep_mss'] = state['mss']
    a1 = b.grab(Rect(10, 20, 64, 16)); out['g1_MSS'] = state['MSS']
    a2 = b.grab(Rect(10, 20, 64, 16)); out['g2_MSS'] = state['MSS']
    # Y7-1: IKINCI NOKTA -- negatif sanal-masaustu koordinati. Bu makinenin gercek
    # duzeninde sol monitor x=-2560'ta; kutuyu 0'a kirpan bir grab yalniz burada duser.
    b.grab(Rect(-2600, -50, 64, 16))
    out['grab_args'] = state['grab_args']
    # Y6-2: ONCE TIP. `np.asarray` K7'nin yasakladigi sessiz donusumdur; onu
    # denetleyicinin icinde kullanmak, ham ScreenShot donduren bir grab'i AKLAR.
    out['grab_isinstance'] = bool(isinstance(a1, np.ndarray))
    out['grab_tam_ndarray'] = bool(type(a1) is np.ndarray)
    arr = a1 if isinstance(a1, np.ndarray) else np.asarray(a1)
    out['grab_shape'] = list(arr.shape); out['grab_dtype'] = str(arr.dtype)
    ok = False
    if arr.ndim == 3 and arr.shape[:2] == (16, 64) and arr.shape[2] in (3, 4) and arr.dtype == np.uint8:
        want = np.frombuffer(PATTERN, dtype=np.uint8)[: arr.shape[2]]
        ok = bool(np.all(arr.reshape(-1, arr.shape[2]) == want))
    out['grab_content_ok'] = ok
    b.close(); out['c1_close'] = state['close']
    b.close(); out['c2_close'] = state['close']
    print('JSON=' + json.dumps(out))
"""


def check_3_spy_backend(errs: list[str]) -> None:
    """K10: MssBackend'in mss kullanimi — icerik dogru, tembel, cagri basina kur+kapat, canli, deprecated yok."""
    r = _run(_SPY_PROBE.format(repo=REPO))
    line = next((ln for ln in r.stdout.splitlines() if ln.startswith("JSON=")), None)
    if r.returncode != 0 or line is None:
        errs.append("§3 casus-modul sondasi tamamlanamadi: MssBackend'in bir metodu casus mss ile patladi "
                    "(casus yalnizca MSS/monitors/grab/close/__enter__/__exit__ ve ScreenShot.raw/bgra/size/"
                    "width/height/__array_interface__ sunar)\n      " + _tail(r.stderr) + "\n      " + _tail(r.stdout))
        return
    o = json.loads(line[5:])
    exp = {
        "grab_isinstance": (True, "MssBackend.grab `np.ndarray` DONDURMEDI (ham ScreenShot ya da "
                                  "baska bir nesne) -> K7: servis `isinstance` ile reddeder, gercek "
                                  "ekranla her yakalama CaptureError verir"),
        "grab_content_ok": (True, "grab() donusu casusun baytlarini tasimiyor: (h,w,3|4) uint8 ve her piksel "
                                  "[1,2,3(,255)] olmali -> ekran okunmuyor ya da kanal sirasi bozuk"),
        "init_MSS": (0, "MssBackend() yapimi MSS() kurdu -> K10: tembel olmali"),
        "m1_MSS": (1, "ilk monitors() tam 1 MSS() kurmali"),
        "m1_close": (1, "ilk monitors() kurdugu MSS()'i KAPATMADI -> K10: 5001. cagrida GetWindowDC olur"),
        "m1_eq_raw": (True, "monitors() donusu casusun ham listesine esit degil ([0] birlesim dahil olmali, kopya)"),
        "m1_len": (3, "monitors() uzunlugu 3 olmali ([0] + 2 monitor)"),
        "m2_MSS": (2, "ikinci monitors() +1 MSS() kurmali (memoize atlatma)"),
        "m2_close": (2, "ikinci monitors() +1 kapatma yapmali"),
        "m2_len": (2, "monitors() CANLI degil: casus listesi 2'ye dustu, ikinci cagri eskiyi gordu"),
        "dep_mss": (0, "kullanimdan kalkmis mss.mss() cagrildi -> K10"),
        "g1_MSS": (3, "ilk grab() uzun omurlu MSS()'i kurmali (+1)"),
        "g2_MSS": (3, "ikinci grab() YENI MSS() kurdu -> K10: uzun omurlu tutamac tek olmali"),
        "grab_dtype": ("uint8", "grab() dtype uint8 olmali"),
        "c1_close": (3, "close() uzun omurlu tutamaci kapatmali (+1)"),
        "c2_close": (3, "ikinci close() sessiz olmali (+0, idempotent)"),
    }
    for k, (want, msg) in exp.items():
        if o.get(k) != want:
            errs.append(f"§3 {msg}  [{k}: beklenen {want!r}, olculen {o.get(k)!r}]")
    if o.get("grab_shape") not in ([16, 64, 4], [16, 64, 3]):
        errs.append(f"§3 grab() sekli (16,64,4) ya da (16,64,3) olmali; olculen {o.get('grab_shape')!r}")
    if not o.get("grab_tam_ndarray", True):
        print("  UYARI §3 grab() bir np.ndarray ALT SINIFI dondurdu; K7'yi ihlal etmez "
              "(servis `isinstance` kullanir) ama gercek mss yolunda hicbir mesru bicim "
              "alt sinif uretmez -- beklenmedik bir donusum isareti.")
    ga = o.get("grab_args") or []
    if not ga or not all(isinstance(g, dict) and {"left", "top", "width", "height"} <= set(g) for g in ga):
        errs.append(f"§3 grab() MSS.grab'e {{'left','top','width','height'}} sozlugu vermeli; olculen {ga!r}")
    else:
        # Y7-1: IKI NOKTA. Kutu, cagiranin Rect'inin BIREBIR kendisi olmali.
        bekle = [{"left": 10, "top": 20, "width": 64, "height": 16},
                 {"left": 10, "top": 20, "width": 64, "height": 16},
                 {"left": -2600, "top": -50, "width": 64, "height": 16}]
        for i, (b_, g_) in enumerate(zip(bekle, ga)):
            if g_ != b_:
                errs.append(f"§3 grab() {i}. cagrida kutuyu degistirdi: beklenen {b_}, olculen {g_} "
                            f"-> K10: kutu cagiranin Rect'inin birebir kendisidir (negatif sanal-masaustu "
                            f"koordinatlari KIRPILMAZ)")


# ---------------------------------------------------------------- §4
_KABUL_DONUS = {"np.ndarray", "ndarray", "ImageArray", "npt.NDArray[np.uint8]",
                "NDArray[np.uint8]"}


def _annassign_dugumleri(tree: ast.Module) -> list[ast.AnnAssign]:
    """Modul duzeyi + `if TYPE_CHECKING:` govdesi (Y6-3: TYPE_CHECKING mesru bir bicim)."""
    out: list[ast.AnnAssign] = []
    for node in tree.body:
        if isinstance(node, ast.AnnAssign):
            out.append(node)
        elif isinstance(node, ast.If):
            t = node.test
            if (isinstance(t, ast.Name) and "TYPE_CHECKING" in t.id) or \
               (isinstance(t, ast.Attribute) and t.attr == "TYPE_CHECKING"):
                out.extend(x for x in node.body if isinstance(x, ast.AnnAssign))
    return out


def _uyum_satirlari(errs: list[str]) -> None:
    """K1/O-F (Y5-1, Y6-1, Y6-3): protokol uyum satirlari GERCEKTEN bir sey dogruluyor mu.

    Y6-1: yalnizca ADI ve ACIKLAMAYI aramak yetmez -- ciplak `_uyum_fake: CaptureBackend`
    (deger yok) mypy'ye hicbir sey dogrulatmaz ve eski kapi onu KABUL EDIYORDU.
    Bu yuzden deger bir CAGRI olmali ve hedef sinif adi eslesmelidir. Ayrica
    `grab` FakeBackend'in KENDI govdesinde tanimli olmali; taban sinifa tasinirsa
    donus aciklamasi denetimi sessizce bosalir.
    """
    tree = ast.parse(SERVICE.read_text(encoding="utf-8"), filename=str(SERVICE))
    beklenen = {"_uyum_fake": "FakeBackend", "_uyum_mss": "MssBackend"}
    gorulen: dict[str, ast.AnnAssign] = {}
    for node in _annassign_dugumleri(tree):
        if not isinstance(node.target, ast.Name):
            continue
        ann = ast.unparse(node.annotation).strip().strip("'\"")
        if ann == "CaptureBackend":
            gorulen[node.target.id] = node
    for ad, sinif in beklenen.items():
        n = gorulen.get(ad)
        if n is None:
            errs.append(f"§4 service.py'de `{ad}: CaptureBackend = {sinif}(...)` satiri YOK "
                        f"-> K1/O-F: protokol uyumu makineyle dogrulanmiyor")
            continue
        if n.value is None:
            errs.append(f"§4 service.py:{n.lineno} `{ad}` ciplak ek aciklama (deger YOK) -> K1/O-F: "
                        f"deger olmadan mypy hicbir uyum dogrulamaz; `{sinif}(...)` atanmali")
            continue
        if not (isinstance(n.value, ast.Call) and
                ast.unparse(n.value.func).split(".")[-1] == sinif):
            errs.append(f"§4 service.py:{n.lineno} `{ad}` degeri `{sinif}(...)` cagrisi degil "
                        f"({ast.unparse(n.value)}) -> K1/O-F: baska bir ada baglamak {sinif}'i "
                        f"denetim disi birakir")
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef) or node.name != "FakeBackend":
            continue
        kendi = [f for f in node.body
                 if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef)) and f.name == "grab"]
        if not kendi:
            errs.append("§4 FakeBackend.grab KENDI govdesinde tanimli degil (taban siniftan miras?) "
                        "-> K1: donus aciklamasi denetimi bosalir")
            continue
        f = kendi[0]
        if f.decorator_list:
            errs.append("§4 FakeBackend.grab DEKORATORLU -> K1: dekorator mypy'nin gordugu imzayi "
                        "`Any`'ye dusurup uyum satirlarinin garantisini bosaltabilir "
                        "(KRT olctu: uyumsuz imza mypy'yi geciyor)")
        don = (ast.unparse(f.returns) if f.returns is not None else "(yok)").strip().strip("'\"")
        if don.replace(" ", "") not in {x.replace(" ", "") for x in _KABUL_DONUS}:
            errs.append(f"§4 FakeBackend.grab donus aciklamasi `{don}` -> K1: `np.ndarray` "
                        f"(ya da `ImageArray` / `npt.NDArray[np.uint8]`) olmali; `np.ndarray | None` "
                        f"YASAK: mypy'yi gecer ama FakeBackend artik CaptureBackend degildir")


def _runtime_protokol(errs: list[str]) -> None:
    """K1 (Y7-5): protokol uyumu CALISMA ZAMANINDA olculur -- ad/kalitim/dekorator bagimsiz.

    AST ve mypy kancalari mekanizmayi kancaliyor; `runtime_checkable` protokolle
    `isinstance` ise nesnenin gercekten gerekli metotlari tasidigini olcer.
    """
    r = _run(f"""
        import sys, typing
        sys.path.insert(0, r'{REPO}')
        import src.capture.service as S
        P = typing.runtime_checkable(S.CaptureBackend) if not getattr(
            S.CaptureBackend, "_is_runtime_protocol", False) else S.CaptureBackend
        f_ok = isinstance(S.FakeBackend(()), P)
        m_ok = isinstance(S.MssBackend(), P)
        print('UYUM=%s,%s' % (f_ok, m_ok))
    """)
    line = next((ln for ln in r.stdout.splitlines() if ln.startswith("UYUM=")), None)
    if line is None:
        errs.append("§4 calisma zamani protokol uyumu olculemedi\n      " + _tail(r.stderr))
        return
    f_ok, m_ok = (x == "True" for x in line[5:].split(","))
    if not f_ok:
        errs.append("§4 FakeBackend calisma zamaninda CaptureBackend protokolune UYMUYOR -> K1")
    if not m_ok:
        errs.append("§4 MssBackend calisma zamaninda CaptureBackend protokolune UYMUYOR -> K1")


def check_4_no_qt(errs: list[str]) -> None:
    for p in OWNS_ALL:
        if not p.exists():
            continue
        tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        for node in ast.walk(tree):
            mods = []
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and not node.level:
                mods = [node.module or ""]
            for m in mods:
                if m.split(".")[0] in QT:
                    errs.append(f"§4 {p.name}:{node.lineno} Qt import'u -> §8.3-A2 ihlali")
    _uyum_satirlari(errs)
    _runtime_protokol(errs)


# ---------------------------------------------------------------- §5 (istege bagli)
def check_5_real_smoke(errs: list[str]) -> None:
    """Yalnizca --real ile: gercek mss uzerinden MssBackend duman testi (sef kosar)."""
    r = _run(f"""
        import sys, json
        sys.path.insert(0, r'{REPO}')
        import numpy as np
        from src.contracts.models import Rect
        from src.capture.service import MssBackend
        with MssBackend() as b:
            m = b.monitors()
            a = np.asarray(b.grab(Rect(0, 0, 64, 16)))
            # Icerik iddiasi KUCUK kutuda degil, BIRINCIL MONITORUN TAMAMINDA olculur:
            # 64x16 kose bloklarinin %68'i BGR'de tek renkli (KRT olctu) -> yanlis pozitif.
            pm = next((d for d in m[1:] if d.get('is_primary')), m[1])
            L, T, W, H = int(pm['left']), int(pm['top']), int(pm['width']), int(pm['height'])
            tam = np.asarray(b.grab(Rect(L, T, W, H)))
            # KONUM SADAKATI (kosulsuz, masaustu iceriginden BAGIMSIZ): sag yarim
            # ayrica grab edilir ve tam grab'in sag yarisina bayt bayt esit olmali.
            sag = np.asarray(b.grab(Rect(L + W // 2, T, W - W // 2, H)))
            konum_ok = bool(sag.shape == tam[:, W // 2:].shape and np.array_equal(sag, tam[:, W // 2:])) 
        print('JSON=' + json.dumps({{'len': len(m), 'first0': 'left' in m[0], 'shape': list(a.shape),
                                    'dtype': str(a.dtype), 'writeable': bool(a.flags.writeable),
                                    'tumuyle_sifir': bool(not tam.any()),
                                    'konum_sadakati': konum_ok,
                                    'tekil_bgr': int(np.unique(tam[:, :, :3]).size)}}))
    """)
    line = next((ln for ln in r.stdout.splitlines() if ln.startswith("JSON=")), None)
    if r.returncode != 0 or line is None:
        errs.append("§5 gercek mss dumani PATLADI\n      " + _tail(r.stderr))
        return
    o = json.loads(line[5:])
    if not (o["len"] >= 2 and o["first0"] and o["dtype"] == "uint8" and o["shape"] in ([16, 64, 4], [16, 64, 3])):
        errs.append(f"§5 gercek mss dumani beklenmeyen cikti: {o!r}")
    # Y7-4: her iddia AYRI olculur; `elif` zinciri ilki dusunce gerisini susturuyordu.
    if o["tumuyle_sifir"]:
        errs.append(f"§5 birincil monitorun TAMAMI sifir -> grab ekrani okumuyor: {o!r}")
    if not o["writeable"]:
        errs.append(f"§5 gercek mss yolunda dizi salt-okunur: {o!r} -> K7 kopya kurali")
    if not o["konum_sadakati"]:
        # Sefin kendi olcumu: CANLI ekranda iki grab arasinda masaustu degisir
        # (imlec, saat, animasyon) -- bu denetim yapisi geregi kararsizdir ve
        # IHLAL sayilamaz. Konum sadakatinin DETERMINISTIK kapisi §3'un
        # `grab_args` denetimidir (MSS.grab'e giden {left,top,width,height}).
        print(f"  UYARI §5 konum sadakati esitlik vermedi (canli ekran iki grab arasinda degismis "
              f"olabilir). Deterministik konum kapisi §3'un grab_args denetimidir.")
    if o["tekil_bgr"] == 1:
        # Y6-8: masaustu TEK RENKLI olabilir; icerik iddiasi bunu "ekrani okumuyor"dan
        # ayirt edemez. Ekrani hic okumayan grab'in deterministik kapisi §3'tur.
        print(f"  UYARI §5 masaustu tek renkli (tekil_bgr=1); icerik iddiasi olculemedi. "
              f"Konum sadakati ve §3 casus baytlari gecerli.")
    print(f"§5 gercek mss: {o}")


def main() -> None:
    real = "--real" in sys.argv[1:]
    errs: list[str] = []
    for p in OWNS_ALL:
        if not p.exists():
            errs.append(f"dosya yok: {p.relative_to(REPO)}")
    if errs:
        _report(errs)
    check_1_conftest_barrier(errs)
    check_2_lazy_import(errs)
    check_3_spy_backend(errs)
    check_4_no_qt(errs)
    if real:
        check_5_real_smoke(errs)
    _report(errs)


def _report(errs: list[str]) -> None:
    print("denetlenen: service.py, monitors.py, conftest.py, test_service.py, test_monitors.py")
    if errs:
        print(f"\nIHLAL ({len(errs)}):")
        for e in errs:
            print(f"  {e}")
        sys.exit(1)
    print("\nTEMIZ: K1 engeli calisiyor, devretmiyor, oturum kapsamli; mss'e yuklemede girisim yok; "
          "grab icerigi dogru; monitors() kur+kapat+canli; grab tutamaci tek; close idempotent; Qt yok")
    sys.exit(0)


if __name__ == "__main__":
    main()
