"""TESTER-D tur 2 mutant dalgasi -- "degismezi mi, YAZILDIGI BICIMI mi olcuyor?"

Tur 2'de eklenen dort test (K10 x2, K1 varsayilan uretici, K3 tip kimligi)
sefin adlandirdigi dort mutanti (M12/M13/M37/M44) yakaliyor. Bu dosya bunun
**mutantin adini kancalamaktan** mi yoksa **degismezi olcmekten** mi
kaynaklandigini sorar: ayni degismezi BASKA BICIMDE ihlal eden varyantlar
kurulur, artı davranisi degistirmeyen KONTROL mutantlari (yanlis pozitif
denetimi).

`src/` ve `tests/` YAZILMAZ -- makine `mutant_kiti.py`'nin ayna agacidir.
Kosum:  python .agents/tasks/T-005/tester_D/mutant_kiti_tur2.py [mutant_id ...]
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mutant_kiti import (  # noqa: E402
    KAPILAR,
    SERVICE,
    Mutant,
    _ayna_kur,
    _geri_al,
    _kapi_kos,
    _uygula,
    _y,
)

CLOSE_BASLIK = (
    "    def close(self) -> None:  # pragma: no cover"
    " -- K1: gercek ekran, headless_check §3 ile denetleniyor\n"
)
CLOSE_GOVDE = (
    "        if self._tutamac is not None:\n"
    "            self._tutamac.close()\n"
    "            self._tutamac = None"
)
EXIT_ESKI = "    def __exit__(self, *_: object) -> None:\n        self.close()"
GRAB_ESKI = (
    "        if self._tutamac is None:\n"
    "            self._tutamac = mss.MSS()\n"
    '        kutu = {"left": rect.x, "top": rect.y, "width": rect.w, "height": rect.h}\n'
    "        return np.asarray(self._tutamac.grab(kutu), dtype=np.uint8)"
)

MUTANTLAR: list[Mutant] = [
    # ---- K10 `__exit__` -> close() : AYNI degismez, BASKA bicim -----------
    Mutant(
        "M50", SERVICE,
        [_y(EXIT_ESKI,
            "    def __exit__(self, *_: object) -> None:\n        self._tutamac = None")],
        "__exit__ tutamaci KAPATMADAN birakir (alan None olur, DC sizar)",
        "K10 `__exit__` -> close()  [M12'nin `_tutamac`'i sifirlayan varyanti]",
    ),
    Mutant(
        "M53", SERVICE,
        [_y(EXIT_ESKI,
            "    def __exit__(self, *_: object) -> None:\n"
            "        if not _ or _[0] is None:\n"
            "            self.close()")],
        "__exit__ yalnizca ISTISNASIZ cikista kapatir (govde patlarsa tutamac sizar)",
        "K10 `__exit__` -> close()  [istisna yolu]",
    ),
    # ---- K10 close() : AYNI degismez, BASKA bicim -------------------------
    Mutant(
        "M51", SERVICE,
        [_y(CLOSE_BASLIK + CLOSE_GOVDE,
            CLOSE_BASLIK
            + "        if self._tutamac is not None:\n"
              "            self._tutamac = None")],
        "close() alani sifirlar ama ALTTAKI close()'u CAGIRMAZ (M13'un aynasi)",
        "K10 close() tutamaci kapatir",
    ),
    Mutant(
        "M52", SERVICE,
        [_y(CLOSE_BASLIK + CLOSE_GOVDE,
            CLOSE_BASLIK
            + "        tutamac = self._tutamac\n"
              "        self._tutamac = None\n"
              "        if tutamac is not None:\n"
              "            tutamac.close()")],
        "KONTROL: close() sirasi ters (once alan sifirlanir, sonra kapatilir) -- davranis AYNI",
        "yanlis pozitif denetimi: KACMASI DOGRU",
    ),
    # ---- K10 tutamac KIMLIGI: testin enjekte ettigi alan uretimin yazdigi mi?
    Mutant(
        "M54", SERVICE,
        [_y("    def __init__(self) -> None:\n        self._tutamac: mss.MSS | None = None",
            "    def __init__(self) -> None:\n        self._tutamac: mss.MSS | None = None\n"
            "        self._tutamac2: mss.MSS | None = None"),
         _y(GRAB_ESKI,
            "        if self._tutamac2 is None:\n"
            "            self._tutamac2 = mss.MSS()\n"
            '        kutu = {"left": rect.x, "top": rect.y, "width": rect.w, "height": rect.h}\n'
            "        return np.asarray(self._tutamac2.grab(kutu), dtype=np.uint8)")],
        "grab() tutamaci BASKA alana (_tutamac2) yazar; close()/__exit__ hala _tutamac'a bakar "
        "-> enjeksiyon testleri gecer, URETIMDE her tutamac sizar",
        "TOTOLOJI SONDASI: sahte tutamac enjeksiyonu uretimin kurdugu durumu mu olcuyor?",
    ),
    # ---- K1 FakeBackend varsayilan uretici: baska ihlal bicimleri ---------
    Mutant(
        "M56", SERVICE,
        [_y("    return np.zeros((rect.h, rect.w, 4), dtype=np.uint8)",
            "    return np.zeros((rect.w, rect.h, 4), dtype=np.uint8)")],
        "varsayilan uretici DEVRIK sekil dondurur ((w,h,4))",
        "K1 varsayilan uretici sekli  [M44'un devrik varyanti]",
    ),
    Mutant(
        "M57", SERVICE,
        [_y("    return np.zeros((rect.h, rect.w, 4), dtype=np.uint8)",
            "    return np.ones((rect.h, rect.w, 4), dtype=np.uint8)")],
        "varsayilan uretici SIFIR degil BIR dizi dondurur",
        "K1 varsayilan uretici icerigi  [M44'un icerik varyanti]",
    ),
    # ---- K3 tip kimligi: olcu hangi yolda kosuyor? ------------------------
    Mutant(
        "M58", SERVICE,
        [_y("        goruntu = self._backend_dan_al(hedef)",
            "        kirpildi = (hedef.x, hedef.y, hedef.w, hedef.h) != (duz.x, duz.y, duz.w, duz.h)\n"
            "        sifir = rect.x * 0\n"
            "        backend_hedefi = Rect(hedef.x + sifir, hedef.y + sifir, hedef.w + sifir,\n"
            "                              hedef.h + sifir, hedef.monitor_index,\n"
            "                              hedef.dpi_scale) if kirpildi else hedef\n"
            "        goruntu = self._backend_dan_al(backend_hedefi)")],
        "backend kutusuna numpy skaleri YALNIZ PARTIAL yolunda sizar (geometri ayni, `==` esit)",
        "K3/K8 tip kimligi -- olcunun INSIDE + PARTIAL iki noktada kosmasi (§4.6/7)",
    ),
]


def main() -> None:
    secilen = set(sys.argv[1:])
    _ayna_kur()
    _geri_al()
    print("TUR 2 MUTANT DALGASI -- X = kapi yakaladi, . = kacirdi")
    print("kapilar: " + " | ".join(ad for ad, _ in KAPILAR))
    print()
    satirlar: list[str] = []
    kacan: list[str] = []
    for mut in MUTANTLAR:
        if secilen and mut.mid not in secilen:
            continue
        _uygula(mut)
        try:
            isaretler: list[str] = []
            detaylar: list[str] = []
            for ad, argv in KAPILAR:
                rc, ozet = _kapi_kos(ad, argv)
                isaretler.append("X" if rc != 0 else ".")
                if rc != 0:
                    ilk = next((ln for ln in ozet.splitlines()
                                if ("IHLAL" in ln or "error:" in ln or "failed" in ln
                                    or "Required test coverage" in ln)), "")
                    detaylar.append(f"{ad}:{ilk.strip()[:120]}")
                    for ln in ozet.splitlines():
                        if ln.startswith("FAILED") or ln.startswith("      §"):
                            detaylar.append(f"      {ln.strip()[:150]}")
            durum = "".join(isaretler)
            yakalandi = "X" in durum
            if not yakalandi:
                kacan.append(mut.mid)
            print(f"{mut.mid} [{durum}] "
                  f"{'YAKALANDI' if yakalandi else '*** HICBIR KAPI YAKALAMADI ***'}")
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
    print("| # | mutant | hedef degismez | " + " | ".join(ad for ad, _ in KAPILAR) + " |")
    print("|---|---|---|" + "---|" * len(KAPILAR))
    for s in satirlar:
        print(s)
    print()
    print(f"HICBIR KAPININ YAKALAMADIGI MUTANTLAR ({len(kacan)}): "
          + (", ".join(kacan) if kacan else "yok"))


if __name__ == "__main__":
    main()
