"""T-011 mutant ayirt-etme kiti (implementer, tur 1).

    python .agents/tasks/T-011/evidence/mutant-kiti.py

Depoya DOKUNMAZ: `src/contracts`, `src/translate/__init__.py`,
`src/translate/sozluk.py`, `tests/unit/translate/__init__.py`,
`tests/unit/translate/conftest.py` ve `tests/unit/translate/test_sozluk.py`
scratchpad altinda bir AYNA agacina kopyalanir (`T011_AYNA` ortam degiskeni
ile yer secilebilir). Her mutant aynadaki `sozluk.py`ye metin ikamesiyle
(bir ya da birden fazla `(eski, yeni)` cifti) uygulanir ve birim test dosyasi
ayna koku cwd ile kosulur. Stdout ASCII; metin basilmaz. Cikis 0 = her
beklenti tuttu. Dusen test adlari `mutant-ayirt-etme-hangi-testler.txt`e
yazilir (ayni dizin).

`X (n)` = n test dustu (YAKALANDI), `.` = hepsi gecti (KACTI).

Beklentiler:
  M01..M32  davranis degistiren mutantlar: birim testleri YAKALAMALI.
  C-1..C-3  davranis-esdeger degisiklikler (kontrol): KACMALI -- yanlis
            pozitif yok. C-1: aday siralamasi acik anahtarla (ayni tuple).
            C-2: `_ortusur` kosulunun iki yani yer degistirir. C-3: KR ek
            dongusu en uzun once DEGIL kisa once -- ek kurali "herhangi bir
            ek + sonrasinda sinir" diye ozyineli tarandigi icin sira sonucu
            degistirmez (paketin "en uzun once" ifadesi mekanizma, degismez
            degil; olculur).
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
HANGI = Path(__file__).resolve().parent / "mutant-ayirt-etme-hangi-testler.txt"

Ikame = tuple[str, str]
# (ad, aciklama, ikameler, yakalanmali)
MUTANTLAR: list[tuple[str, str, list[Ikame], bool]] = [
    ("M01", "K1: sinir kurali tamamen kaldirildi (alt dize esleme)",
     [("            if not (baglam.sol(start) and baglam.sag(end)):\n                continue\n", "")], True),
    ("M02", "K1: en-uzun-once TERS (kisa once)",
     [("        adaylar.sort()\n", "        adaylar.sort(key=lambda a: (-a[0], a[1], a[2]))\n")], True),
    ("M03", "K1: JP parcacik kumesi sinir degil (Latin ad + JP parcacik eslesmez)",
     [("    return ch.isspace() or unicodedata.category(ch).startswith(\"P\") or ch in _JP_PARCACIKLAR\n",
       "    return ch.isspace() or unicodedata.category(ch).startswith(\"P\")\n")], True),
    ("M04", "K1: KR ek kurali kaldirildi (terim+KR ek eslesmez)",
     [("        return self._sag_temel(end) or self._kr_ek_sonrasi(end, _KR_EK_ZINCIRI)\n", "        return self._sag_temel(end)\n")], True),
    ("M05", "K1 (KRT O2): metin casefold'lanip aranir (indeks kayar, source_term degisir)",
     [("        metin = _nfc(text)\n        korunan = _korunan_araliklar(metin, yer_tutucular)\n",
       "        metin = _nfc(text).casefold()\n        korunan = _korunan_araliklar(metin, yer_tutucular)\n")], True),
    ("M06", "K6: NFC kaldirildi",
     [("    return unicodedata.normalize(_NFC, metin)\n", "    return metin\n")], True),
    ("M07", "K2: start-ARTAN uygulama (indeksler kayar)",
     [("        for h in reversed(_hitleri_dogrula(metin, grup, korunan)):  # start AZALAN: indeksler kaymaz\n",
       "        for h in _hitleri_dogrula(metin, grup, korunan):\n")], True),
    ("M08", "K4: gomde buyuk harf kapali",
     [("            metin = metin[: h.start] + ilk_harfi_buyut(_nfc(h.target_term)) + metin[h.end :]\n",
       "            metin = metin[: h.start] + _nfc(h.target_term) + metin[h.end :]\n")], True),
    ("M09", "K4: yuklemede buyuk harf kapali (TermHit.target_term kucuk)",
     [("    return SozlukTerimi(kaynak=kaynak, hedef=ilk_harfi_buyut(hedef), note=not_, kisa_terim_izni=izin)\n",
       "    return SozlukTerimi(kaynak=kaynak, hedef=hedef, note=not_, kisa_terim_izni=izin)\n")], True),
    ("M10", "K3: lookup placeholders yoksayildi",
     [("        korunan = _korunan_araliklar(metin, yer_tutucular)\n\n        adaylar", "        korunan: list[tuple[int, int]] = []\n\n        adaylar")], True),
    ("M11", "K7: segment_index None SESSIZCE yutuldu (hit atlanir)",
     [("        if not isinstance(h, TermHit):\n            raise ContractViolation(f\"hits[{sira}] TermHit degil",
       "        if isinstance(h, TermHit) and h.segment_index is None:\n            continue\n        if not isinstance(h, TermHit):\n            raise ContractViolation(f\"hits[{sira}] TermHit degil")], True),
    ("M12", "K6: tek kodpoint sema kontrolu kaldirildi",
     [("    if len(kaynak) == 1 and not izin:\n", "    if False:\n")], True),
    ("M13", "K6: hedefte terminator kontrolu kaldirildi",
     [("        if ch in _CUMLE_SONU:\n", "        if False:\n")], True),
    ("M14", "K6: hedefte {} kontrolu kaldirildi",
     [("        if ch in _YER_TUTUCU_AYRACLARI:\n", "        if False:\n")], True),
    ("M15", "K6: tekrar eden kaynak kontrolu kaldirildi",
     [("            if k in anahtarlar:\n", "            if False:\n")], True),
    ("M16", "K2: ortusen hit denetimi kaldirildi",
     [("        if a.end > b.start:\n", "        if False:\n")], True),
    ("M17", "K2: text[start:end] == source_term denetimi kaldirildi",
     [("        if not isinstance(h.source_term, str) or metin[h.start : h.end] != _nfc(h.source_term):\n",
       "        if not isinstance(h.source_term, str):\n")], True),
    ("M18", "K3: gomde yer tutucu ortusme denetimi kaldirildi",
     [("        if _ortusur(h.start, h.end, korunan):\n            raise", "        if False:\n            raise")], True),
    ("M19", "K2: bos hits -> kopya nesneler (is bozulur)",
     [("    if not hits:\n        return segs\n", "    if not hits:\n        return tuple(dataclasses.replace(s) for s in segs)\n")], True),
    ("M20", "K1: komsu terim siniri kaldirildi (sol + sag; bitisik unvan+ad tek/hicbir hit)",
     [("            or start in self.terim_bitisleri\n", ""), ("            or end in self.terim_baslari\n", "")], True),
    ("M21", "K1: donus start-artan siralanmaz (islem sirasi)",
     [("        hits.sort(key=lambda h: h.start)\n", "")], True),
    ("M22", "K1: KR ek zinciri derinligi 1 (iki ek ust uste eslesmez)",
     [("_KR_EK_ZINCIRI: Final = 2\n", "_KR_EK_ZINCIRI: Final = 1\n")], True),
    ("M23", "K1/K3: yer tutucu ucu sinir degil (%s + JP ad)",
     [("            or start in self.yt_bitisleri\n", ""), ("            or end in self.yt_baslari\n", "")], True),
    ("M24", "K1: trie anahtari harf durumunu katlamaz (Marcus / marcus aurelius ayri dal)",
     [("    k = _anahtar(ch)\n    return k if len(k) == 1 else ch\n", "    return ch\n")], True),
    ("M25", "K1: onek tablosu kullanilmaz (konum basina yalniz en uzun aday)",
     [("            for j in (en_uzun, *self._onekler[en_uzun]):\n", "            for j in (en_uzun,):\n")], True),
    ("M26", "K1 (G6): ekten SONRA sinir sarti kaldirildi (ek+devam eden hece eslesir)",
     [("                if self._sag_temel(sonrasi) or self._kr_ek_sonrasi(sonrasi, derinlik - 1):\n", "                if True:\n")], True),
    ("M27", "K1: SOL sinir kurali kaldirildi (on-bilesikler: windmill vb.)",
     [("        \"\"\"Terimden ONCE sinir var mi.\"\"\"\n        return (\n", "        \"\"\"Terimden ONCE sinir var mi.\"\"\"\n        return True or (\n")], True),
    ("M28", "K1: SAG sinir kurali kaldirildi (son-bilesikler: elders vb.)",
     [("        \"\"\"Terimden SONRA sinir var mi (KR ek zinciri dahil).\"\"\"\n        return ",
       "        \"\"\"Terimden SONRA sinir var mi (KR ek zinciri dahil).\"\"\"\n        return True or ")], True),
    ("M29", "K2: start == end (bos aralik) kabul",
     [("        if not 0 <= h.start < h.end <= n:\n", "        if not 0 <= h.start <= h.end <= n:\n")], True),
    ("M30", "K4: Turkce i -> noktali buyuk I kurali kaldirildi",
     [("    if ilk == \"i\":\n        return \"İ\" + metin[1:]\n", "")], True),
    ("M31", "K1: lookup_segments segment_index doldurmaz",
     [("            hits.extend(self._ara(seg.text, _yer_tutuculari_dogrula(seg.placeholders), i))\n",
       "            hits.extend(self._ara(seg.text, _yer_tutuculari_dogrula(seg.placeholders), None))\n")], True),
    ("M32", "K1/K2: ortusme `<` -> `<=` (bitisik araliklar ortusme sayilir)",
     [("        if start < b and a < end:\n", "        if start <= b and a <= end:\n")], True),
    ("C-1", "KONTROL: aday siralamasi acik anahtarla (ayni tuple) -- esdeger",
     [("        adaylar.sort()\n", "        adaylar.sort(key=lambda a: (a[0], a[1], a[2]))\n")], False),
    ("C-2", "KONTROL: _ortusur kosulunun yanlari yer degistirdi -- esdeger",
     [("        if start < b and a < end:\n", "        if a < end and start < b:\n")], False),
    ("C-3", "KONTROL: KR ek dongusu kisa once -- ozyineli tarama sirayi anlamsiz kilar, esdeger",
     [("        for ek in _KR_EKLER:\n", "        for ek in sorted(_KR_EKLER, key=len):\n")], False),
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


def kos(ayna: Path) -> tuple[int, int, int, list[str]]:
    env = dict(os.environ, PYTHONPATH=str(ayna), PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/unit/translate/test_sozluk.py", "-q", "-p", "no:cacheprovider",
         "--no-header", "-rf", "--tb=no", "-k", "not test_k5_sure"],
        cwd=str(ayna), env=env, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    m_f = re.search(r"(\d+) failed", r.stdout)
    m_p = re.search(r"(\d+) passed", r.stdout)
    m_e = re.search(r"(\d+) error", r.stdout)
    dusenler = [ln.split(" ", 1)[1].split("::", 1)[-1].split(" - ")[0] for ln in r.stdout.splitlines() if ln.startswith("FAILED ")]
    return (int(m_f.group(1)) if m_f else 0, int(m_p.group(1)) if m_p else 0,
            int(m_e.group(1)) if m_e else (0 if (m_f or m_p) else 1), dusenler)


def main() -> int:
    ayna = Path(os.environ.get("T011_AYNA") or (Path(os.environ.get("TEMP", ".")) / "t011_ayna"))
    ayna_kur(ayna)
    kaynak_ayna = ayna / "src" / "translate" / "sozluk.py"
    orijinal = kaynak_ayna.read_text(encoding="utf-8")

    print("T-011 mutant kiti -- ayna:", ayna)
    f, p, e, _ = kos(ayna)
    print(f"TEMEL (mutantsiz; sure testleri haric): failed={f} passed={p} error={e}")
    if f or e or p == 0:
        print("TEMEL kirmizi -- kit anlamsiz")
        return 2

    hatalar: list[str] = []
    hangi: list[str] = ["T-011 mutantlari -- dusen testler (ayna agaci; sure testleri haric)\n"]
    print(f"{'ad':5} {'sonuc':8} {'beklenen':10} aciklama")
    for ad, aciklama, ikameler, yakalanmali in MUTANTLAR:
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
        f, p, e, dusenler = kos(ayna)
        yakalandi = (f + e) > 0
        sonuc = f"X ({f + e})" if yakalandi else "."
        beklenen = "YAKALA" if yakalanmali else "KACSIN"
        durum = "" if yakalandi == yakalanmali else "  <-- BEKLENTI TUTMADI"
        if durum:
            hatalar.append(ad)
        print(f"{ad:5} {sonuc:8} {beklenen:10} {aciklama}{durum}")
        hangi.append(f"\n{ad} ({aciklama}): {f + e} dusen" + (" [TOPLAMA HATASI]" if e else ""))
        for t in dusenler:
            hangi.append(f"    {t}")
    kaynak_ayna.write_text(orijinal, encoding="utf-8")
    HANGI.write_text("\n".join(hangi) + "\n", encoding="utf-8")

    n_mut = sum(1 for m in MUTANTLAR if m[3])
    n_kont = len(MUTANTLAR) - n_mut
    print()
    print(f"{n_mut} davranis mutanti + {n_kont} kontrol; beklenti tutmayan: {len(hatalar)} {hatalar}")
    print(f"dusen test adlari: {HANGI.name}")
    return 1 if hatalar else 0


if __name__ == "__main__":
    raise SystemExit(main())
