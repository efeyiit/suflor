"""T-011 mutant ayirt-etme kiti (implementer, tur 2).

    python .agents/tasks/T-011/evidence/mutant-kiti-tur2.py

Depoya DOKUNMAZ: `src/contracts`, `src/translate/__init__.py`,
`src/translate/sozluk.py`, `tests/unit/translate/__init__.py`,
`tests/unit/translate/conftest.py` ve `tests/unit/translate/test_sozluk.py`
gecici dizin altinda bir AYNA agacina kopyalanir (`T011_AYNA` ortam degiskeni
ile yer secilebilir). Her mutant aynadaki `sozluk.py`ye metin ikamesiyle
(bir ya da birden fazla `(eski, yeni)` cifti) uygulanir ve birim test dosyasi
ayna koku cwd ile kosulur. Stdout ASCII; metin basilmaz. Cikis 0 = her
beklenti tuttu. Dusen test adlari `mutant-ayirt-etme-hangi-testler-tur2.txt`e
yazilir (ayni dizin).

`X (n)` = n test dustu (YAKALANDI), `.` = hepsi gecti (KACTI).

Beklentiler:
  M01..M32  tur 1 mutantlari (ikame noktalari v3 koduna tasindi; M32 bitmap
            surumu): birim testleri YAKALAMALI.
  M33..M44  tur 2 mutantlari (zincir, betik gecisi, saygi/ek listeleri, NFC,
            sema, Mn, trie anahtari, kabul komsusu): YAKALAMALI.
  M45       bitmap yerine DOGRUSAL kabul listesi (tur 1 mekanizmasi): sure
            testleri HARIC kosumda davranis ayni -> KACSIN (bilgi); sure
            testleri DAHIL ayri kosumda yakalaniyor mu -> raporlanir.
  C-1..C-5  davranis-esdeger degisiklikler (kontrol): KACMALI -- yanlis
            pozitif yok. C-1 aday siralamasi acik anahtarla; C-2 bitmap
            denetimi dilimle (`1 in dolu[s:e]`); C-3 ek dongusu kisa once;
            C-4 olu-konum hafizasi kapali (yalniz hiz); C-5 zincir aramada
            once sag sonra sol adimlanir.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
KAYNAK = KOK / "src" / "translate" / "sozluk.py"
TEST = KOK / "tests" / "unit" / "translate" / "test_sozluk.py"
HANGI = Path(__file__).resolve().parent / "mutant-ayirt-etme-hangi-testler-tur2.txt"

Ikame = tuple[str, str]
SURE_HARIC = "not test_k5_sure"
SURE_DAHIL = "test_k5_sure"
# (ad, aciklama, ikameler, yakalanmali, -k ifadesi)
MUTANTLAR: list[tuple[str, str, list[Ikame], bool, str]] = [
    ("M01", "K1: sinir kurali tamamen kaldirildi (alt dize esleme)",
     [("        if start == 0 or start in self.yt_bitisleri:\n            return True\n", "        return True\n"),
      ("        if end == self.n or end in self.yt_baslari:\n            return True\n", "        return True\n")], True, SURE_HARIC),
    ("M02", "K1: en-uzun-once TERS (kisa once)",
     [("        adaylar.sort()\n", "        adaylar.sort(key=lambda a: (-a[0], a[1], a[2]))\n")], True, SURE_HARIC),
    ("M03", "K1: JP parcacik kumesi sinir degil",
     [("    return ch.isspace() or unicodedata.category(ch).startswith(\"P\") or ch in _JP_PARCACIKLAR\n",
       "    return ch.isspace() or unicodedata.category(ch).startswith(\"P\")\n")], True, SURE_HARIC),
    ("M04", "K1: ek kurali (KR + JP saygi) kaldirildi",
     [("        return self._sag_temel(end) or self._ek_sonrasi(end, _EK_ZINCIRI)\n", "        return self._sag_temel(end)\n")], True, SURE_HARIC),
    ("M05", "K1 (KRT O2): metin casefold'lanip aranir (indeks kayar, source_term degisir)",
     [("        metin = _nfc(text)\n        adaylar = self._adaylar(metin)\n",
       "        metin = _nfc(text).casefold()\n        adaylar = self._adaylar(metin)\n")], True, SURE_HARIC),
    ("M06", "K6: NFC kaldirildi",
     [("    return unicodedata.normalize(_NFC, metin)\n", "    return metin\n")], True, SURE_HARIC),
    ("M07", "K2: start-ARTAN uygulama (indeksler kayar)",
     [("        for h in reversed(_hitleri_dogrula(metin, grup, korunan)):  # start AZALAN: indeksler kaymaz\n",
       "        for h in _hitleri_dogrula(metin, grup, korunan):\n")], True, SURE_HARIC),
    ("M08", "K4: gomde buyuk harf kapali",
     [("            metin = metin[: h.start] + ilk_harfi_buyut(_nfc(h.target_term)) + metin[h.end :]\n",
       "            metin = metin[: h.start] + _nfc(h.target_term) + metin[h.end :]\n")], True, SURE_HARIC),
    ("M09", "K4: yuklemede buyuk harf kapali (TermHit.target_term kucuk)",
     [("    return SozlukTerimi(kaynak=kaynak, hedef=ilk_harfi_buyut(hedef), note=not_, kisa_terim_izni=izin)\n",
       "    return SozlukTerimi(kaynak=kaynak, hedef=hedef, note=not_, kisa_terim_izni=izin)\n")], True, SURE_HARIC),
    ("M10", "K3: lookup placeholders yoksayildi",
     [("        baglam = _SinirBaglami(metin, _korunan_araliklar(metin, yer_tutucular), adaylar)\n",
       "        baglam = _SinirBaglami(metin, [], adaylar)\n")], True, SURE_HARIC),
    ("M11", "K7: segment_index None SESSIZCE yutuldu (hit atlanir)",
     [("        if not isinstance(h, TermHit):\n            raise ContractViolation(f\"hits[{sira}] TermHit degil",
       "        if isinstance(h, TermHit) and h.segment_index is None:\n            continue\n        if not isinstance(h, TermHit):\n            raise ContractViolation(f\"hits[{sira}] TermHit degil")], True, SURE_HARIC),
    ("M12", "K6: tek kodpoint sema kontrolu kaldirildi",
     [("    if len(kaynak) == 1 and not izin:\n", "    if False:\n")], True, SURE_HARIC),
    ("M13", "K6: hedefte terminator kontrolu kaldirildi",
     [("        if ch in _CUMLE_SONU:\n            raise ValueError(f\"sozluk semasi: {etiket}: hedef cumle sonu",
       "        if False:\n            raise ValueError(f\"sozluk semasi: {etiket}: hedef cumle sonu")], True, SURE_HARIC),
    ("M14", "K6: hedefte {} kontrolu kaldirildi",
     [("        if ch in _YER_TUTUCU_AYRACLARI:\n", "        if False:\n")], True, SURE_HARIC),
    ("M15", "K6: tekrar eden kaynak kontrolu kaldirildi",
     [("            if k in anahtarlar:\n", "            if False:\n")], True, SURE_HARIC),
    ("M16", "K2: ortusen hit denetimi kaldirildi",
     [("        if a.end > b.start:\n", "        if False:\n")], True, SURE_HARIC),
    ("M17", "K2: text[start:end] == source_term denetimi kaldirildi",
     [("        if not isinstance(h.source_term, str) or metin[h.start : h.end] != _nfc(h.source_term):\n",
       "        if not isinstance(h.source_term, str):\n")], True, SURE_HARIC),
    ("M18", "K3: gomde yer tutucu ortusme denetimi kaldirildi",
     [("        if korunan_bit.find(1, h.start, h.end) != -1:\n            raise", "        if False:\n            raise")], True, SURE_HARIC),
    ("M19", "K2: bos hits -> kopya nesneler (is bozulur)",
     [("    if not hits:\n        return segs\n", "    if not hits:\n        return tuple(dataclasses.replace(s) for s in segs)\n")], True, SURE_HARIC),
    ("M20", "K1: zincir aramasi kapali (komsu terim hicbir zaman sinir vermez)",
     [("                yollar = baglam.zincir(start, end, sol_ok, sag_ok)\n", "                yollar = None\n")], True, SURE_HARIC),
    ("M21", "K1: donus start-artan siralanmaz (islem sirasi)",
     [("        hits.sort(key=lambda h: h.start)\n", "")], True, SURE_HARIC),
    ("M22", "K1: ek zinciri derinligi 1 (iki ek ust uste eslesmez)",
     [("_EK_ZINCIRI: Final = 2\n", "_EK_ZINCIRI: Final = 1\n")], True, SURE_HARIC),
    ("M23", "K1/K3: yer tutucu ucu sinir degil (%s + Latin ad)",
     [("        if start == 0 or start in self.yt_bitisleri:\n", "        if start == 0:\n"),
      ("        if end == self.n or end in self.yt_baslari:\n", "        if end == self.n:\n")], True, SURE_HARIC),
    ("M24", "K1: trie anahtari harf durumunu katlamaz (Marcus / marcus aurelius ayri dal)",
     [("    return _anahtar(ch)\n", "    return ch\n")], True, SURE_HARIC),
    ("M24b", "K1 v3: trie anahtari tur-1 kurali (coklu kodpointe katlanan karakter kendisi: ss/eszett ayri dal)",
     [("    return _anahtar(ch)\n", "    k = _anahtar(ch)\n    return k if len(k) == 1 else ch\n")], True, SURE_HARIC),
    ("M24c", "K1 v3: trie anahtari `ch.lower()` temsilcisi (tasarim adayi; olcumde 3 cift ayristi -- birim testi yakaliyor mu?)",
     [("    return _anahtar(ch)\n", "    k = _anahtar(ch)\n    return k if len(k) == 1 else ch.lower()\n")], True, SURE_HARIC),
    ("M25", "K1: onek tablosu kullanilmaz (konum basina yalniz en uzun aday)",
     [("            for j in (en_uzun, *self._onekler[en_uzun]):\n", "            for j in (en_uzun,):\n")], True, SURE_HARIC),
    ("M26", "K1 (G6): ekten SONRA sinir sarti kaldirildi (ek+devam eden hece eslesir)",
     [("                if self._sag_temel(sonrasi) or self._ek_sonrasi(sonrasi, derinlik - 1):\n", "                if True:\n")], True, SURE_HARIC),
    ("M27", "K1: SOL sinir kurali kaldirildi (on-bilesikler: windmill vb.)",
     [("        if start == 0 or start in self.yt_bitisleri:\n            return True\n", "        return True\n")], True, SURE_HARIC),
    ("M28", "K1: SAG sinir kurali kaldirildi (son-bilesikler: elders vb.)",
     [("        if end == self.n or end in self.yt_baslari:\n            return True\n", "        return True\n")], True, SURE_HARIC),
    ("M29", "K2: start == end (bos aralik) kabul",
     [("        if not 0 <= h.start < h.end <= n:\n", "        if not 0 <= h.start <= h.end <= n:\n")], True, SURE_HARIC),
    ("M30", "K4: Turkce i -> noktali buyuk I kurali kaldirildi",
     [("    if ilk == \"i\":\n        return \"İ\" + metin[1:]\n", "")], True, SURE_HARIC),
    ("M31", "K1: lookup_segments segment_index doldurmaz",
     [("            hits.extend(self._ara(seg.text, _segment_yer_tutuculari(seg, i), i))\n",
       "            hits.extend(self._ara(seg.text, _segment_yer_tutuculari(seg, i), None))\n")], True, SURE_HARIC),
    ("M32", "K1/K2: bitmap denetimi bitisik araligi ortusme sayar (end + 1)",
     [("        return self.dolu.find(1, start, end) != -1\n", "        return self.dolu.find(1, start, end + 1) != -1\n")], True, SURE_HARIC),
    # --- tur 2 ---
    ("M33", "K1 v3: ZINCIR kurali kaldirildi -- komsu adayin VARLIGI sinir verir (tur 1 mekanizmasi; windmills -> wind)",
     [("            sol_ok = baglam.sinir_sol(start)\n            sag_ok = baglam.sinir_sag(end)\n",
       "            sol_ok = baglam.sinir_sol(start) or start in baglam.bitenler\n            sag_ok = baglam.sinir_sag(end) or end in baglam.baslayanlar\n")], True, SURE_HARIC),
    ("M34", "K1 v3: BETIK GECISI kaldirildi (her karakter DIGER sinifi)",
     [("    o = ord(ch)\n    if o < 0x1100:\n        return _BETIK_DIGER\n", "    return _BETIK_DIGER\n    o = ord(ch)\n    if o < 0x1100:\n        return _BETIK_DIGER\n")], True, SURE_HARIC),
    ("M35", "K1 v3: JP saygi/kopula listesi BOS",
     [("    \"さん\", \"様\", \"殿\", \"君\", \"ちゃん\", \"達\", \"たち\", \"って\", \"だ\", \"から\", \"まで\", \"より\", \"か\", \"よ\", \"ね\",\n", "")], True, SURE_HARIC),
    ("M36", "K1 v3: KR yeni ek listesi (19 ek) BOS",
     [("    \"에게\", \"한테\", \"께\", \"님\", \"씨\", \"야\", \"아\", \"랑\", \"이랑\", \"들\", \"처럼\", \"보다\", \"마다\", \"밖에\", \"조차\", \"라고\", \"라면\", \"입니다\", \"이다\",\n", "")], True, SURE_HARIC),
    ("M37", "K2 v3: gomde placeholders NFC'lenmez (aynen kopyalanir)",
     [("        cikti[i] = dataclasses.replace(seg, text=metin, placeholders=yer_tutucular)\n",
       "        cikti[i] = dataclasses.replace(seg, text=metin)\n")], True, SURE_HARIC),
    ("M38", "K6 v3: kaynakta terminator kontrolu kaldirildi",
     [("        if ch in _CUMLE_SONU:\n            raise ValueError(f\"sozluk semasi: {etiket}: kaynak cumle sonu",
       "        if False:\n            raise ValueError(f\"sozluk semasi: {etiket}: kaynak cumle sonu")], True, SURE_HARIC),
    ("M39", "K6 v3: hedefte kontrol karakteri (Cc) kontrolu kaldirildi",
     [("        if unicodedata.category(ch) == \"Cc\":\n", "        if False:\n")], True, SURE_HARIC),
    ("M40", "K6 v3: kaynak <= 100 kodpoint kontrolu kaldirildi (2000 kodpoint -> RecursionError)",
     [("    if len(kaynak) > _KAYNAK_AZAMI:\n", "    if False:\n")], True, SURE_HARIC),
    ("M41", "K2 v3: Segment placeholders bicim hatasi TypeError kalir (ContractViolation'a sarilmaz)",
     [("    try:\n        return _yer_tutuculari_dogrula(seg.placeholders)\n    except TypeError as e:\n        raise ContractViolation(f\"segments[{i}].placeholders bicimi gecersiz: {e}\") from e\n",
       "    return _yer_tutuculari_dogrula(seg.placeholders)\n")], True, SURE_HARIC),
    ("M42", "K1 v3: sagdaki birlestirici isaret (M*) sinir sayilir",
     [("        if unicodedata.category(sonraki).startswith(\"M\"):\n            return False  # birlestirici isaret onceki karaktere aittir\n", "")], True, SURE_HARIC),
    ("M43", "K1 v3: kabul edilmis komsunun ucu sinir DEGIL (yalniz gercek sinir)",
     [("        return konum in self.kabul_bit or self.gercek_sol(konum)\n", "        return self.gercek_sol(konum)\n"),
      ("        return konum in self.kabul_bas or self.gercek_sag(konum)\n", "        return self.gercek_sag(konum)\n")], True, SURE_HARIC),
    ("M44", "K1 v3: zincir icinde kisa aday once denenir (en uzun once degil)",
     [("            self.bitenler.setdefault(end, []).append((start, j))\n            self.baslayanlar.setdefault(start, []).append((end, j))\n",
       "            self.bitenler.setdefault(end, []).insert(0, (start, j))\n            self.baslayanlar.setdefault(start, []).insert(0, (end, j))\n")], True, SURE_HARIC),
    ("M45", "K5 v3: bitmap yerine DOGRUSAL kabul listesi (tur 1 `_ortusur`) -- sure testleri HARIC: davranis ayni, KACMALI",
     [("        \"kabul_bas\", \"kabul_bit\", \"olumsuz_sol\", \"olumsuz_sag\",\n    )\n",
       "        \"kabul_bas\", \"kabul_bit\", \"olumsuz_sol\", \"olumsuz_sag\", \"kabul_liste\",\n    )\n"),
      ("        self.kabul_bas: set[int] = set()\n", "        self.kabul_liste: list[tuple[int, int]] = []\n        self.kabul_bas: set[int] = set()\n"),
      ("        self.kabul_bas.add(start)\n", "        self.kabul_liste.append((start, end))\n        self.kabul_bas.add(start)\n"),
      ("        return self.dolu.find(1, start, end) != -1\n",
       "        return any(a < end and start < b for a, b in self.kabul_liste) or self.dolu.find(1, start, end) != -1\n")], False, SURE_HARIC),
    ("M45s", "K5 v3: ayni dogrusal mutant, YALNIZ sure testleri (test_k5_sure_*) -- yakaliyor mu?",
     [("        \"kabul_bas\", \"kabul_bit\", \"olumsuz_sol\", \"olumsuz_sag\",\n    )\n",
       "        \"kabul_bas\", \"kabul_bit\", \"olumsuz_sol\", \"olumsuz_sag\", \"kabul_liste\",\n    )\n"),
      ("        self.kabul_bas: set[int] = set()\n", "        self.kabul_liste: list[tuple[int, int]] = []\n        self.kabul_bas: set[int] = set()\n"),
      ("        self.kabul_bas.add(start)\n", "        self.kabul_liste.append((start, end))\n        self.kabul_bas.add(start)\n"),
      ("        return self.dolu.find(1, start, end) != -1\n",
       "        return any(a < end and start < b for a, b in self.kabul_liste) or self.dolu.find(1, start, end) != -1\n")], True, SURE_DAHIL),
    ("C-1", "KONTROL: aday siralamasi acik anahtarla (ayni tuple) -- esdeger",
     [("        adaylar.sort()\n", "        adaylar.sort(key=lambda a: (a[0], a[1], a[2]))\n")], False, SURE_HARIC),
    ("C-2", "KONTROL: bitmap denetimi dilimle (`1 in dolu[s:e]`) -- esdeger",
     [("        return self.dolu.find(1, start, end) != -1\n", "        return 1 in self.dolu[start:end]\n")], False, SURE_HARIC),
    ("C-3", "KONTROL: ek dongusu kisa once -- ozyineli tarama sirayi anlamsiz kilar, esdeger",
     [("        for ek in _EK_ILK_KARAKTER.get(self.metin[konum], ()):\n",
       "        for ek in sorted(_EK_ILK_KARAKTER.get(self.metin[konum], ()), key=len):\n")], False, SURE_HARIC),
    ("C-4", "KONTROL: olu-konum hafizasi kapali (yalniz hiz; davranis esdeger)",
     [("            self.olumsuz.add(p)\n", "            pass\n")], False, SURE_HARIC),
    ("C-5", "KONTROL: zincir aramada once SAG sonra SOL adimlanir -- esdeger",
     [("            if sol.durum == _SURUYOR:\n                sol.adim()\n            if sag.durum == _SURUYOR and sol.durum != _OLU:\n                sag.adim()\n",
       "            if sag.durum == _SURUYOR:\n                sag.adim()\n            if sol.durum == _SURUYOR and sag.durum != _OLU:\n                sol.adim()\n")], False, SURE_HARIC),
]


def ayna_kur(ayna: Path) -> None:
    if ayna.exists():
        shutil.rmtree(ayna)
    (ayna / "src" / "translate").mkdir(parents=True)
    (ayna / "tests" / "unit" / "translate").mkdir(parents=True)
    shutil.copytree(KOK / "src" / "contracts", ayna / "src" / "contracts", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copy(KOK / "src" / "translate" / "__init__.py", ayna / "src" / "translate" / "__init__.py")
    shutil.copy(KAYNAK, ayna / "src" / "translate" / "sozluk.py")
    shutil.copy(KOK / "tests" / "unit" / "translate" / "__init__.py", ayna / "tests" / "unit" / "translate" / "__init__.py")
    shutil.copy(KOK / "tests" / "unit" / "translate" / "conftest.py", ayna / "tests" / "unit" / "translate" / "conftest.py")
    shutil.copy(TEST, ayna / "tests" / "unit" / "translate" / "test_sozluk.py")


def kos(ayna: Path, k_ifadesi: str) -> tuple[int, int, int, list[str]]:
    env = dict(os.environ, PYTHONPATH=str(ayna), PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/unit/translate/test_sozluk.py", "-q", "-p", "no:cacheprovider",
         "--no-header", "-rf", "--tb=no", "-k", k_ifadesi],
        cwd=str(ayna), env=env, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    m_f = re.search(r"(\d+) failed", r.stdout)
    m_p = re.search(r"(\d+) passed", r.stdout)
    m_e = re.search(r"(\d+) error", r.stdout)
    dusenler = [ln.split(" ", 1)[1].split("::", 1)[-1].split(" - ")[0] for ln in r.stdout.splitlines() if ln.startswith("FAILED ")]
    return (int(m_f.group(1)) if m_f else 0, int(m_p.group(1)) if m_p else 0,
            int(m_e.group(1)) if m_e else (0 if (m_f or m_p) else 1), dusenler)


def main() -> int:
    ayna = Path(os.environ.get("T011_AYNA") or (Path(os.environ.get("TEMP", ".")) / "t011_ayna_tur2"))
    ayna_kur(ayna)
    kaynak_ayna = ayna / "src" / "translate" / "sozluk.py"
    orijinal = kaynak_ayna.read_text(encoding="utf-8")

    print("T-011 mutant kiti (tur 2) -- ayna: <gecici dizin>/t011_ayna_tur2")
    f, p, e, _ = kos(ayna, SURE_HARIC)
    print(f"TEMEL (mutantsiz; sure testleri haric): failed={f} passed={p} error={e}")
    if f or e or p == 0:
        print("TEMEL kirmizi -- kit anlamsiz")
        return 2
    f, p, e, _ = kos(ayna, SURE_DAHIL)
    print(f"TEMEL (mutantsiz; yalniz sure testleri): failed={f} passed={p} error={e}")
    if f or e or p == 0:
        print("TEMEL (sure) kirmizi -- kit anlamsiz")
        return 2

    hatalar: list[str] = []
    hangi: list[str] = ["T-011 mutantlari (tur 2) -- dusen testler (ayna agaci)\n"]
    print(f"{'ad':5} {'sonuc':8} {'beklenen':10} aciklama")
    for ad, aciklama, ikameler, yakalanmali, k_ifadesi in MUTANTLAR:
        kaynak = orijinal
        bozuk = False
        for eski, yeni in ikameler:
            if kaynak.count(eski) != 1:
                print(f"{ad:5} {'?':8} {'-':10} {aciklama}  [IKAME NOKTASI {kaynak.count(eski)} KEZ -- KIT BOZUK]")
                bozuk = True
                break
            kaynak = kaynak.replace(eski, yeni)
        if bozuk:
            hatalar.append(ad)
            continue
        kaynak_ayna.write_text(kaynak, encoding="utf-8")
        f, p, e, dusenler = kos(ayna, k_ifadesi)
        yakalandi = (f + e) > 0
        sonuc = f"X ({f + e})" if yakalandi else "."
        beklenen = "YAKALA" if yakalanmali else "KACSIN"
        durum = "" if yakalandi == yakalanmali else "  <-- BEKLENTI TUTMADI"
        if durum:
            hatalar.append(ad)
        print(f"{ad:5} {sonuc:8} {beklenen:10} {aciklama}{durum}")
        hangi.append(f"\n{ad} ({aciklama}) [-k '{k_ifadesi}']: {f + e} dusen" + (" [TOPLAMA HATASI]" if e else ""))
        for t in dusenler:
            hangi.append(f"    {t}")
    kaynak_ayna.write_text(orijinal, encoding="utf-8")
    HANGI.write_text("\n".join(hangi) + "\n", encoding="utf-8")

    n_mut = sum(1 for m in MUTANTLAR if m[3])
    n_kont = len(MUTANTLAR) - n_mut
    print()
    print(f"{n_mut} davranis mutanti + {n_kont} kontrol/bilgi; beklenti tutmayan: {len(hatalar)} {hatalar}")
    print(f"dusen test adlari: {HANGI.name}")
    return 1 if hatalar else 0


if __name__ == "__main__":
    raise SystemExit(main())
