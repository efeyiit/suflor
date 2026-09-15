"""T-013 mutant ayirt-etme kiti (implementer, tur 1).

    python .agents/tasks/T-013/evidence/mutant-kiti.py

Depoya DOKUNMAZ: `src/ui/*.py` ve `tests/unit/ui/*` (sefin `conftest.py` ve bariyer testi dahil, degistirilmeden)
gecici dizin altinda bir AYNA agacina kopyalanir (`T013_AYNA` ortam degiskeni ile yer secilebilir). Her mutant
aynadaki kaynaga metin ikamesiyle uygulanir (ikame metni bulunamazsa kit durur: mutant bayatlamis demektir) ve
`tests/unit/ui` ayna koku cwd ile offscreen + `SUFLOR_GERCEK_KISAYOL_YASAK=1` kosulur (hicbir mutant gercek
`RegisterHotKey` cagirmaz: kemer aynada da acik). Stdout ASCII; kullanici metni basilmaz. Cikis 0 = her beklenti
tuttu. Dusen test adlari `mutant-ayirt-etme-hangi-testler.txt`e yazilir (ayni dizin).

`X (n)` = n test dustu (YAKALANDI), `.` = hepsi gecti (KACTI).

Beklentiler (brief'teki 14 zorunlu mutant + ek):
  M01 NOREPEAT kaldirildi · M02 kimlik sayaci ornek basina · M03 destroyed alicisi self'in bagli yontemi ·
  M03b destroyed partial'i self'i yakalar · M04 eventType denetimi yok · M05 bilinmeyen kimlik True doner ·
  M06 AltGr sorgusu yok · M06b AltGr Shift'lide de sorulur · M07 tek degistirici kabul · M08 Win kabul ·
  M09 kara liste yok · M10 1409 -> OK · M11 durum metni bos · M12 etiketler guncellenmiyor ·
  M12b etiketler kaydedilemeyeni de gosterir · M13 thread kontrolu yok · M14 gercek_win32 kemeri yok ·
  M14b fn eksikse RuntimeError yok · M15 yikimda filtre sokulmuyor · M16 ayni ad yeniden kayitta eski
  kaldirilmiyor · M17 servis ici cakisma denetimi yok · M18 tetiklendi -> kabuk bagli degil · M19 cikis_istendi
  -> hepsini_kaldir yok · M20 varsayilan Ctrl+Alt+T (AltGr ₺) · M21 bilinmeyen ad anlik sinyali yayar ·
  M22 bozuk metin ValueError yayar (GECERSIZ degil) · M23 F12 kabul · M24 kaldir(bilinmeyen) KeyError ·
  M25 hata kodu okunmuyor (1409 HATA olur) · M26 kabuk: bos etiket "(kısayol yok)" olmaz · M27 K6 pozitif
  kontrol: print eklendi (AST) · M28 dilbilgisi: bos parca kabul · M29 kimlik 0xBFFF'te sarmiyor (0xC000) ·
  M30 filtre yikim temizleyicisi kaldir_fn cagirmiyor.
  C-1..C-4 davranis-esdeger degisiklikler (kontrol): KACMALI -- yanlis pozitif yok.
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
KI, UY, KB = "kisayol.py", "uygulama.py", "kabuk.py"
MUTANTLAR: list[tuple[str, str, list[Ikame], bool]] = [
    ("M01", "K1: MOD_NOREPEAT kaldirildi (basili tutunca tekrar)",
     [(KI, "        if not self._kayit_fn(kimlik, mod | MOD_NOREPEAT, vk):\n", "        if not self._kayit_fn(kimlik, mod, vk):\n")], True),
    ("M02", "K1 (O4): kimlik sayaci ORNEK basina (iki servis ayni id)",
     [(KI, "        kimlik = _yeni_kimlik()\n", "        kimlik = len(self._kayitlar) + 1\n")], True),
    ("M03", "K1 (Y3): destroyed alicisi self'in bagli yontemi (PySide6 6.11'de kosmaz)",
     [(KI, "        self.destroyed.connect(functools.partial(_yikimda_temizle, kimlikler, kaldir_fn, filtre, app.removeNativeEventFilter))\n",
       "        self.destroyed.connect(self.hepsini_kaldir)\n")], True),
    ("M03b", "K1 (Y3): destroyed partial'i self'i yakalar (del+gc toplamaz; filtre sokulmez)",
     [(KI, "        self.destroyed.connect(functools.partial(_yikimda_temizle, kimlikler, kaldir_fn, filtre, app.removeNativeEventFilter))\n",
       "        self.destroyed.connect(functools.partial(KisayolServisi.hepsini_kaldir, self))\n")], True),
    ("M04", "K2 (O7): eventType denetimi yok",
     [(KI, "        if ham != _OLAY_TIPI:\n            return False, 0\n", "")], True),
    ("M05", "K2: bilinmeyen kimlik True doner (eski servis yeni servisin olayini yutar)",
     [(KI, "        if ad is None:\n            return False, 0\n", "        if ad is None:\n            return True, 0\n")], True),
    ("M06", "K3 (Y2): AltGr sorgusu yok",
     [(KI, "        if mod & (MOD_CONTROL | MOD_ALT) == MOD_CONTROL | MOD_ALT and not mod & MOD_SHIFT and self._altgr_karakteri_fn(vk):\n            return KayitSonucu.ALTGR_CAKISMA\n", "")], True),
    ("M06b", "K3 (Y2): AltGr Shift'li kombinasyonda da sorulur",
     [(KI, "and not mod & MOD_SHIFT and self._altgr_karakteri_fn(vk):", "and self._altgr_karakteri_fn(vk):")], True),
    ("M07", "K3 (O3): tek degistirici kabul",
     [(KI, "    elif bin(mod).count(\"1\") < 2:\n", "    elif bin(mod).count(\"1\") < 1:\n")], True),
    ("M08", "K3 (O3): Win kabul",
     [(KI, "    if mod & MOD_WIN:\n        raise GecersizKombinasyon(\"Win/Meta Windows'a ayrilmis\")\n", "")], True),
    ("M09", "K3 (O3): kara liste yok",
     [(KI, "    if (mod, vk) in _KARA_LISTE:\n        raise GecersizKombinasyon(\"sistem kombinasyonu (kara liste)\")\n", "")], True),
    ("M10", "K1/K5: 1409 -> OK (cakisma gizlenir)",
     [(KI, "            return KayitSonucu.CAKISMA if self._son_hata_kodu == ERROR_HOTKEY_ALREADY_REGISTERED else KayitSonucu.HATA\n",
       "            return KayitSonucu.OK if self._son_hata_kodu == ERROR_HOTKEY_ALREADY_REGISTERED else KayitSonucu.HATA\n")], True),
    ("M11", "K5: durum metni bos (cakisma bildirilmez)",
     [(UY, "    if sorunlar:\n        pencere.durum_goster(\"; \".join(sorunlar) + \". \" + _DEVAM_NOTU)\n", "")], True),
    ("M12", "K5: etiketler guncellenmiyor (dugmeler '(kısayol yok)' kalir)",
     [(UY, "    pencere.kisayol_etiketleri(servis.kayitli())\n", "")], True),
    ("M12b", "K5: etiketler kaydedilemeyeni de gosterir (istenen tablo, kayitli degil)",
     [(UY, "    pencere.kisayol_etiketleri(servis.kayitli())\n", "    pencere.kisayol_etiketleri(dict(kisayollar))\n")], True),
    ("M13", "K6: thread kontrolu yok",
     [(KI, "        if QThread.currentThread() is not _uygulama().thread():\n            raise RuntimeError(\"KisayolServisi yalniz ana (GUI) thread'den kullanilir (K6)\")\n",
       "        return\n")], True),
    ("M14", "Y1: gercek_win32 kemeri yok (ortam degiskeni denetlenmez)",
     [(KI, "            if os.environ.get(GERCEK_KISAYOL_YASAK_DEGISKENI):\n                raise RuntimeError(f\"{GERCEK_KISAYOL_YASAK_DEGISKENI} ayarli: bu surecte gercek Win32 kisayol kaydi yasak (Y1)\")\n", "")], True),
    ("M14b", "Y1: fn eksikse RuntimeError yok (sessizce None)",
     [(KI, "            if fn is None:\n                raise RuntimeError(f\"gercek_win32=False iken {ad} verilmek zorunda (Y1: offscreen'de de gercek kayit olur)\")\n",
       "            pass\n")], True),
    ("M15", "K1/K2: yikimda filtre sokulmuyor",
     [(KI, "    kimlikler.clear()\n    filtreyi_sok(filtre)\n", "    kimlikler.clear()\n")], True),
    ("M16", "K1: ayni ad yeniden kayitta eski kaldirilmiyor",
     [(KI, "        self.kaldir(ad)\n        if any((m, v) == (mod, vk) for _, m, v in self._kayitlar.values()):\n",
       "        if any((m, v) == (mod, vk) for _, m, v in self._kayitlar.values()):\n")], True),
    ("M17", "K1: servis ici ayni kombinasyon denetimi yok (Win32'ye gider)",
     [(KI, "        if any((m, v) == (mod, vk) for _, m, v in self._kayitlar.values()):\n            return KayitSonucu.CAKISMA\n", "")], True),
    ("M18", "K4: tetiklendi -> kisayol_tetiklendi bagli degil",
     [(UY, "    servis.tetiklendi.connect(pencere.kisayol_tetiklendi)\n", "")], True),
    ("M19", "K1/K4: cikis_istendi -> hepsini_kaldir bagli degil",
     [(UY, "    pencere.cikis_istendi.connect(servis.hepsini_kaldir)\n", "")], True),
    ("M20", "Y2: varsayilan Ctrl+Alt+T (TR-Q'da AltGr ₺)",
     [(UY, "MappingProxyType({\"anlik_cevir\": \"Ctrl+Alt+D\"", "MappingProxyType({\"anlik_cevir\": \"Ctrl+Alt+T\"")], True),
    ("M21", "K4: bilinmeyen ad anlik sinyali yayar",
     [(KB, "        sinyal = {\"anlik_cevir\": self.anlik_cevir_istendi, \"bolge_izle\": self.bolge_izle_istendi}.get(ad)\n",
       "        sinyal = {\"anlik_cevir\": self.anlik_cevir_istendi, \"bolge_izle\": self.bolge_izle_istendi}.get(ad, self.anlik_cevir_istendi)\n")], True),
    ("M22", "K3/K5: bozuk metin kaydet'ten ValueError olarak cikar (GECERSIZ degil)",
     [(KI, "        except ValueError:\n            return KayitSonucu.GECERSIZ\n", "        except GecersizKombinasyon:\n            return KayitSonucu.GECERSIZ\n")], True),
    ("M23", "K3: F12 kabul",
     [(KI, "        if n == 12:\n            raise GecersizKombinasyon(\"F12 hata ayiklayiciya ayrilmis\")\n        if 1 <= n <= 11:\n", "        if 1 <= n <= 12:\n")], True),
    ("M24", "K1: kaldir(bilinmeyen) KeyError (sessiz degil)",
     [(KI, "        kayit = self._kayitlar.pop(ad, None)\n", "        kayit = self._kayitlar.pop(ad)\n")], True),
    ("M25", "K1: hata kodu okunmuyor (1409 HATA olur)",
     [(KI, "            self._son_hata_kodu = int(self._hata_kodu_fn())\n", "            self._son_hata_kodu = 0\n")], True),
    ("M26", "K5 kabuk: bos etiket '(kısayol yok)' olmaz",
     [(KB, "            etiket = etiketler.get(ad) or _KISAYOL_YOK\n", "            etiket = etiketler.get(ad, _KISAYOL_YOK)\n")], True),
    ("M27", "K6 pozitif kontrol: kaynaga print eklendi (AST olcusu ateslemeli)",
     [(KI, "        self._son_hata_kodu = 0\n        self._kayitlar[ad] = (kimlik, mod, vk)\n",
       "        self._son_hata_kodu = 0\n        print(ad)\n        self._kayitlar[ad] = (kimlik, mod, vk)\n")], True),
    ("M28", "K3: bos parca kabul ('Ctrl+' gecer)",
     [(KI, "    if any(not p or not p.isascii() for p in parcalar):\n", "    parcalar = [p for p in parcalar if p]\n    if any(not p.isascii() for p in parcalar):\n")], True),
    ("M29", "K1 (O4): kimlik 0xBFFF'te sarmiyor (uygulama araligi disina cikar)",
     [(KI, "        _sonraki_kimlik = aday + 1 if aday < _KIMLIK_SON else _KIMLIK_ILK\n", "        _sonraki_kimlik = aday + 1\n")], True),
    ("M30", "K1 (Y3): yikim temizleyicisi kaldir_fn cagirmiyor (kayitlar Windows'ta kalir)",
     [(KI, "    for kimlik in list(kimlikler):\n        kaldir_fn(kimlik)\n        _canli_kimlikler.discard(kimlik)\n",
       "    for kimlik in list(kimlikler):\n        _canli_kimlikler.discard(kimlik)\n")], True),
    # --- kontroller: davranis-esdeger ---
    ("C-1", "KONTROL: >= 2 degistirici kurali acik kume ile yazildi -- esdeger",
     [(KI, "    elif bin(mod).count(\"1\") < 2:\n",
       "    elif mod not in (MOD_CONTROL | MOD_ALT, MOD_CONTROL | MOD_SHIFT, MOD_ALT | MOD_SHIFT, MOD_CONTROL | MOD_ALT | MOD_SHIFT):\n")], False),
    ("C-2", "KONTROL: yikim dongusu tuple ile -- esdeger",
     [(KI, "    for kimlik in list(kimlikler):\n", "    for kimlik in tuple(kimlikler):\n")], False),
    ("C-3", "KONTROL: servis ici cakisma denetimi kume ile -- esdeger",
     [(KI, "        if any((m, v) == (mod, vk) for _, m, v in self._kayitlar.values()):\n",
       "        if (mod, vk) in {(m, v) for _, m, v in self._kayitlar.values()}:\n")], False),
    ("C-4", "KONTROL: uygulama sorun listesi f-string yerine birlestirme -- esdeger",
     [(UY, "            sorunlar.append(f\"{kombinasyon} kaydedilemedi: {kayit_sebebi(sonuc, servis.son_hata_kodu)}\")\n",
       "            sorunlar.append(kombinasyon + \" kaydedilemedi: \" + kayit_sebebi(sonuc, servis.son_hata_kodu))\n")], False),
]


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
    ortam = dict(os.environ, QT_QPA_PLATFORM="offscreen", PYTHONIOENCODING="utf-8", SUFLOR_GERCEK_KISAYOL_YASAK="1")
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
    kok = Path(os.environ.get("T013_AYNA") or Path(tempfile.gettempdir()) / "t013_ayna")
    ayna_kur(kok)
    print("T-013 mutant kiti -- ayna: <gecici dizin>/t013_ayna")
    f0, p0, e0, _ = kos(kok)
    print(f"TEMEL (mutantsiz): failed={f0} passed={p0} error={e0}")
    if f0 or e0 or p0 == 0:
        print("TEMEL kirmizi; kit durdu"); return 2
    print("ad    sonuc    beklenen   aciklama")
    hangi: list[str] = ["T-013 mutant basina dusen testler (ayna kosumu)\n"]
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
        print(f"{ad:<5} {sonuc:<8} {beklenen:<10} {aciklama}".encode("ascii", "replace").decode())
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
