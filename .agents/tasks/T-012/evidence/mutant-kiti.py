"""T-012 mutant ayirt-etme kiti (implementer, tur 1).

    python .agents/tasks/T-012/evidence/mutant-kiti.py

Depoya DOKUNMAZ: `src/ui/*.py` ve `tests/unit/ui/*` (sefin `conftest.py` ve
bariyer testi dahil, degistirilmeden) gecici dizin altinda bir AYNA agacina
kopyalanir (`T012_AYNA` ortam degiskeni ile yer secilebilir). Her mutant
aynadaki kaynaga metin ikamesiyle uygulanir (ikame metni bulunamazsa kit
durur: mutant bayatlamis demektir) ve `tests/unit/ui` ayna koku cwd ile
offscreen kosulur. Stdout ASCII; kullanici metni basilmaz. Cikis 0 = her
beklenti tuttu. Dusen test adlari `mutant-ayirt-etme-hangi-testler.txt`e
yazilir (ayni dizin).

`X (n)` = n test dustu (YAKALANDI), `.` = hepsi gecti (KACTI).

Beklentiler:
  M01..M28  davranis mutantlari (paketin K1-K8 degismezleri; brief'teki 14
            zorunlu mutant + ek; M26-M28 tur-1 sonu [5c] kok nedeni ve sefin iki
            hipotezi): birim testleri YAKALAMALI.
  C-1..C-3  davranis-esdeger degisiklikler (kontrol): KACMALI -- yanlis
            pozitif yok. C-1 kenara_al icinde hide/tepsi.goster sirasi;
            C-2 disk esitsizligi `**` ile; C-3 `_konumlan` icinde ayni ifade
            gecici degiskenle.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
KAYNAK_DIZINI = KOK / "src" / "ui"
TEST_DIZINI = KOK / "tests" / "unit" / "ui"
HANGI = Path(__file__).resolve().parent / "mutant-ayirt-etme-hangi-testler.txt"

Ikame = tuple[str, str, str]  # (dosya, eski, yeni)
KS, KB, GE, UY = "kenar_sekmesi.py", "kabuk.py", "geometri.py", "uygulama.py"
# (ad, aciklama, ikameler, yakalanmali)
MUTANTLAR: list[tuple[str, str, list[Ikame], bool]] = [
    ("M01", "K1: closeEvent ignore edilir (kapat cagrilmaz) -> Alt+F4/WM_CLOSE zombi",
     [(KB, "    def closeEvent(self, event: QCloseEvent) -> None:\n        self.kapat()\n        event.accept()\n",
       "    def closeEvent(self, event: QCloseEvent) -> None:\n        event.ignore()\n")], True),
    ("M02", "K1: kapat() idempotent degil (kapandi bayragi yok) -> cikis_istendi ikinci kez",
     [(KB, "        if self._kapandi:\n            return\n        self._kapandi = True\n        self._sekme.hide()\n",
       "        self._kapandi = True\n        self._sekme.hide()\n")], True),
    ("M03", "K1: goster() tepsi ikonunu gizlemez -> gorunur uclusu (T,F,T)",
     [(KB, "        self._sekme.hide()\n        self._tepsi.gizle()\n        self._durum = KabukDurumu.GORUNUR\n",
       "        self._sekme.hide()\n        self._durum = KabukDurumu.GORUNUR\n")], True),
    ("M04", "K5: tepsi yokken tepsiye_al() kenara dusmez -> pencere gizli, ikon yok, sekme yok (kilit)",
     [(KB, "        if not self._tepsi.kullanilabilir:\n            self.kenara_al()\n            return\n", "")], True),
    ("M05", "K4 (Y2): surukleme sirasinda yoklayici acilma sayacini baslatir",
     [(KS, "        if self._surukleme is not None:\n            return\n        icinde = ", "        icinde = ")], True),
    ("M05b", "K4 (Y2): basinca calisan acilma sayaci durdurulmaz",
     [(KS, "            self._acilma.stop()\n            self._surukleme = int(event.globalPosition().y()) - self._y\n",
       "            self._surukleme = int(event.globalPosition().y()) - self._y\n")], True),
    ("M06", "K4 (O9): mod tiki paneli kapatmadan sinyal yayar",
     [(KS, "        self._acilma.stop()\n        self._kapat()\n        sinyal.emit()\n", "        sinyal.emit()\n")], True),
    ("M07", "K4: yoklayici gizliyken de calisir (init'te baslar, hide durdurmaz)",
     [(KS, "        super().hideEvent(event)\n        self._yoklayici.stop()\n", "        super().hideEvent(event)\n"),
      (KS, "        ekran.availableGeometryChanged.connect(self._ekran_degisti)\n        self._kapat()\n",
       "        ekran.availableGeometryChanged.connect(self._ekran_degisti)\n        self._kapat()\n        self._yoklayici.start()\n")], True),
    ("M08", "K4: imlec_konumu yok sayilir, dogrudan QCursor.pos okunur",
     [(KS, "sekme_icinde(self.frameGeometry(), self._imlec_konumu(), self._yaricap, self._kenar)",
       "sekme_icinde(self.frameGeometry(), QCursor.pos(), self._yaricap, self._kenar)")], True),
    ("M09", "K2 (D1): disk yerine dikdortgen ici (saydam kose 'icinde')",
     [(GE, "    if dikdortgen.size() != QSize(yaricap, 2 * yaricap):\n        return True\n", "    return True\n")], True),
    ("M10", "K2: sol kenar x yanlis (+1)",
     [(GE, "    x = ekran.right() - yaricap + 1 if Kenar(kenar) is Kenar.SAG else ekran.left()\n    return QRect(x, y_sinirla",
       "    x = ekran.right() - yaricap + 1 if Kenar(kenar) is Kenar.SAG else ekran.left() + 1\n    return QRect(x, y_sinirla")], True),
    ("M11", "K2: y sinirlanmaz",
     [(GE, "    alt = ekran.bottom() - 2 * yaricap + 1\n    return max(ekran.top(), min(y, alt))\n", "    return y\n")], True),
    ("M12", "K3: WindowDoesNotAcceptFocus bayragi eksik",
     [(KS, "    | Qt.WindowType.WindowStaysOnTopHint\n    | Qt.WindowType.WindowDoesNotAcceptFocus\n)",
       "    | Qt.WindowType.WindowStaysOnTopHint\n)")], True),
    ("M13", "K2: acik panel ekran disina tasar (sikistirma yok)",
     [(GE, "    ust = max(ekran.top(), min(ust, ekran.bottom() - panel.height() + 1))\n", "")], True),
    ("M14", "K2: availableGeometryChanged bagli degil",
     [(KS, "        ekran.availableGeometryChanged.connect(self._ekran_degisti)\n", "")], True),
    ("M15", "K2 (D5): sol kenarda cizim aynalanmaz",
     [(KS, "        merkez_x = r if self._kenar is Kenar.SAG else 0\n", "        merkez_x = r\n")], True),
    ("M16", "K1: kapat() sekmeyi gizlemez (yoklayici calisir, sekme gorunur kalir)",
     [(KB, "        self._kapandi = True\n        self._sekme.hide()\n        self._tepsi.gizle()\n",
       "        self._kapandi = True\n        self._tepsi.gizle()\n")], True),
    ("M17", "K5: tepsi yokken de ikon.show() cagrilir ve gorunur() = isVisible (dogal yanlis uygulama; offscreen'de True)",
     [(KB, "        return self._kullanilabilir and self._ikon.isVisible()\n", "        return self._ikon.isVisible()\n"),
      (KB, "    def goster(self) -> None:\n        if self._kullanilabilir:\n            self._ikon.show()\n",
       "    def goster(self) -> None:\n        self._ikon.show()\n")], True),
    ("M17b", "K5: yalniz goster() kosulu kaldirildi (gorunur() hala kullanilabilir ile AND)",
     [(KB, "    def goster(self) -> None:\n        if self._kullanilabilir:\n            self._ikon.show()\n",
       "    def goster(self) -> None:\n        self._ikon.show()\n")], True),
    ("M18", "K5: her activated sebebi (Context dahil) pencereyi gosterir",
     [(KB, "        if sebep in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):\n            self.goster_istendi.emit()\n",
       "        self.goster_istendi.emit()\n")], True),
    ("M19", "K4: icerideyken kapanma sayaci durdurulmaz (titremede kapanir)",
     [(KS, "        if icinde:\n            self._kapanma.stop()\n            if not self._acik", "        if icinde:\n            if not self._acik")], True),
    ("M20", "K1 (Y1): calistir setQuitOnLastWindowClosed(False) ayarlamaz",
     [(UY, "    app.setQuitOnLastWindowClosed(False)\n", "")], True),
    ("M21", "K1 (Y1): calistir cikis_istendi -> app.quit baglamaz",
     [(UY, "    pencere.cikis_istendi.connect(app.quit)\n", "")], True),
    ("M22", "K1: kenar -> tepsi gecisi acilir (kenar korunmaz)",
     [(KB, "        if self._kapandi or self._durum is KabukDurumu.KENAR:\n            return\n        if not self._tepsi",
       "        if self._kapandi:\n            return\n        if not self._tepsi")], True),
    ("M23", "K1: kapat() sonrasi goster() diriltir",
     [(KB, "        if self._kapandi:\n            return\n        self._sekme.hide()\n        self._tepsi.gizle()\n        self._durum = KabukDurumu.GORUNUR\n",
       "        self._sekme.hide()\n        self._tepsi.gizle()\n        self._durum = KabukDurumu.GORUNUR\n")], True),
    ("M24", "K6 pozitif kontrol: kaynaga print eklendi (AST olcusu ateslemeli)",
     [(KB, "        self._kapandi = True\n        self._sekme.hide()\n", "        self._kapandi = True\n        print('kapat')\n        self._sekme.hide()\n")], True),
    ("M25", "K7 pozitif kontrol: src.capture import edildi (AST + taze surec olcusu ateslemeli)",
     [(KB, "from src.ui.geometri import Kenar\n", "from src.ui.geometri import Kenar\nimport src.capture.dpi  # noqa: F401\n")], True),
    ("M26", "K5 ([5c] kok neden): tepsiye_al() balon gosterir (prototipteki bildir cagrisi geri geldi)",
     [(KB, "        self.hide()\n        self._durum = KabukDurumu.TEPSI\n",
       "        self.hide()\n        self._durum = KabukDurumu.TEPSI\n        self._tepsi.bildir('a', 'b', 2500)\n")], True),
    ("M27", "K8 (sef hipotezi [5c]): sag tik press yerine release'te yayilir",
     [(KS, "        if event.button() == Qt.MouseButton.RightButton:\n            self.pencereyi_goster.emit()\n        elif event.button() == Qt.MouseButton.LeftButton and not self._acik:",
       "        if event.button() == Qt.MouseButton.LeftButton and not self._acik:"),
      (KS, "    def mouseReleaseEvent(self, event: QMouseEvent) -> None:\n        self._surukleme = None\n",
       "    def mouseReleaseEvent(self, event: QMouseEvent) -> None:\n        self._surukleme = None\n        if event.button() == Qt.MouseButton.RightButton:\n            self.pencereyi_goster.emit()\n")], True),
    ("M28", "K4 (sef hipotezi [5c]): birakinca surukleme bayragi temizlenmez (takili kalir) -> yoklayici hic acmaz",
     [(KS, "    def mouseReleaseEvent(self, event: QMouseEvent) -> None:\n        self._surukleme = None\n",
       "    def mouseReleaseEvent(self, event: QMouseEvent) -> None:\n")], True),
    # --- kontroller: davranis-esdeger ---
    ("C-1", "KONTROL: kenara_al icinde hide() ve tepsi.goster() sirasi degisti -- esdeger",
     [(KB, "        self._tepsi.goster()\n        self.hide()\n        self._sekme.show()\n",
       "        self.hide()\n        self._tepsi.goster()\n        self._sekme.show()\n")], False),
    ("C-2", "KONTROL: disk esitsizligi `**` ile yazildi -- esdeger",
     [(GE, "    return dx2 * dx2 + dy2 * dy2 <= 4 * yaricap * yaricap\n", "    return dx2**2 + dy2**2 <= (2 * yaricap) ** 2\n")], False),
    ("C-3", "KONTROL: _konumlan gecici degiskenle -- esdeger",
     [(KS, "        self.setGeometry(self._acik_geometri() if self._acik else self._kapali_geometri())\n",
       "        hedef = self._acik_geometri() if self._acik else self._kapali_geometri()\n        self.setGeometry(hedef)\n")], False),
]

OZET = re.compile(r"(?:(\d+) failed)?(?:, )?(?:(\d+) passed)?(?:, )?(?:(\d+) error)?")


def ayna_kur(kok: Path) -> None:
    if kok.exists():
        shutil.rmtree(kok)
    (kok / "src" / "ui").mkdir(parents=True)
    (kok / "tests" / "unit" / "ui").mkdir(parents=True)
    for f in KAYNAK_DIZINI.glob("*.py"):
        shutil.copy(f, kok / "src" / "ui" / f.name)
    for f in TEST_DIZINI.glob("*.py"):
        shutil.copy(f, kok / "tests" / "unit" / "ui" / f.name)


def kos(kok: Path) -> tuple[int, int, int, list[str]]:
    ortam = dict(os.environ, QT_QPA_PLATFORM="offscreen", PYTHONIOENCODING="utf-8")
    sonuc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/unit/ui", "-q", "-p", "no:cacheprovider", "--no-header", "-rf", "--tb=no"],
        cwd=kok, capture_output=True, text=True, encoding="utf-8", errors="replace", env=ortam, timeout=900,
    )
    cikti = sonuc.stdout + sonuc.stderr
    dusenler = [s.split("::", 1)[1].split(" - ")[0] for s in cikti.splitlines() if s.startswith("FAILED ")]
    failed = passed = error = 0
    for satir in cikti.splitlines():
        if " passed" in satir or " failed" in satir or " error" in satir:
            m = re.search(r"(\d+) failed", satir); failed = int(m.group(1)) if m else failed
            m = re.search(r"(\d+) passed", satir); passed = int(m.group(1)) if m else passed
            m = re.search(r"(\d+) error", satir); error = int(m.group(1)) if m else error
    if sonuc.returncode not in (0, 1):
        error = max(error, 1)
    return failed, passed, error, dusenler


def main() -> int:
    kok = Path(os.environ.get("T012_AYNA") or Path(tempfile.gettempdir()) / "t012_ayna")
    ayna_kur(kok)
    print("T-012 mutant kiti -- ayna: <gecici dizin>/t012_ayna")
    f0, p0, e0, _ = kos(kok)
    print(f"TEMEL (mutantsiz): failed={f0} passed={p0} error={e0}")
    if f0 or e0 or p0 == 0:
        print("TEMEL kirmizi; kit durdu"); return 2
    print("ad    sonuc    beklenen   aciklama")
    hangi: list[str] = ["T-012 mutant basina dusen testler (ayna kosumu)\n"]
    tutmayan: list[str] = []
    for ad, aciklama, ikameler, yakalanmali in MUTANTLAR:
        ayna_kur(kok)
        for dosya, eski, yeni in ikameler:
            yol = kok / "src" / "ui" / dosya
            metin = yol.read_text(encoding="utf-8")
            if metin.count(eski) != 1:
                print(f"{ad}: ikame metni {metin.count(eski)} kez bulundu (1 beklenir) -> {dosya}; kit durdu"); return 2
            yol.write_text(metin.replace(eski, yeni), encoding="utf-8")
        f, p, e, dusenler = kos(kok)
        yakalandi = (f + e) > 0
        sonuc = f"X ({f + e})" if yakalandi else "."
        beklenen = "YAKALA" if yakalanmali else "KACSIN"
        print(f"{ad:<5} {sonuc:<8} {beklenen:<10} {aciklama}")
        hangi.append(f"\n== {ad} [{sonuc}] {aciklama}\n" + ("\n".join(f"  {t}" for t in dusenler) if dusenler else "  (dusen yok)") + "\n")
        if yakalandi != yakalanmali:
            tutmayan.append(ad)
    HANGI.write_text("".join(hangi), encoding="utf-8")
    davranis = sum(1 for m in MUTANTLAR if m[3])
    print(f"\n{davranis} davranis mutanti + {len(MUTANTLAR) - davranis} kontrol; beklenti tutmayan: {len(tutmayan)} {tutmayan}")
    print("dusen test adlari: mutant-ayirt-etme-hangi-testler.txt")
    shutil.rmtree(kok, ignore_errors=True)
    return 1 if tutmayan else 0


if __name__ == "__main__":
    raise SystemExit(main())
