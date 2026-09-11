"""TESTER-B tur 2 kiti (T-006, mercek B) -- YENI K7 olcusunun KANCASI: kacis yollari.

Soru: tur 2'nin `_k7_kanal_olcusu`u (capfd sifir bayt + kok caplog/RapidOCR
dogrudan handler + warnings) davranisa mi kancali, yoksa yine bir MEKANIZMA
listesine mi? Cevap icin motora, olcunun dogrudan hedeflemedigi yollardan
metin yazdiran mutantlar ayna agacinda BES KAPIYA karsi kosulur.

Tur 1 kitinin (`mutant_kiti.py`) altyapisi yeniden kullanilir: ayna agaci,
yama/geri alma, bes kapi. FARK: bu kit kapilari PYTHONIOENCODING VERMEDEN
(stdout cp1254) kosar -- sef Ş1'i duzeltti; her mutantta bes kapinin cp1254
altinda da calistigi boylece yeniden olculur.

Her mutantin `beklenen` alani: kitin YAZILMADAN ONCE verdigim tahmin
(hangi kapi yakalar). Tablo tahminle karsilastirilir; sapma = ogrenilen sey.

Etiketler:
  BULGU-ADAYI  : olcunun gormemesi bir kusur olurdu (urunde bir kanala yazar)
  KONTROL      : hicbir kanala yazmaz; davranis olcusu GECIRMELI (yanlis pozitif yok)
  KARAKTERIZ.  : davranis olcusunun sinirini gosterir (girdi uzayi / zaman penceresi);
                 AST ikincil kapinin degeri burada olculur

Kosum: python .agents/tasks/T-006/tester_B/r2_mutant_kiti.py [mutant_id ...]
"""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import time
from pathlib import Path

BURASI = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("mutant_kiti", BURASI / "mutant_kiti.py")
assert _spec is not None and _spec.loader is not None
mk = importlib.util.module_from_spec(_spec)
sys.modules["mutant_kiti"] = mk
_spec.loader.exec_module(mk)

Mutant, _y, MOTOR = mk.Mutant, mk._y, mk.MOTOR
DONUS, BLOK_EKLE, CLOSE = mk.DONUS, mk.BLOK_EKLE, mk.CLOSE
IMPORT_OS = "import os\n"
BOS_KARE = (
    "        if boxes is None:\n"
    "            if txts is not None and len(txts) > 0:\n"
)
TANIMA_HATA_R2 = (
    "        except Exception as e:\n"
    '            raise OcrError(f"tanıma basarisiz: {type(e).__name__}") from e\n'
)


def _donus(ek_satirlar: str) -> tuple[str, str]:
    """`recognize` sonunda, bloklar hazirken metin yazan yama."""
    return _y(DONUS, "        bloklar = _bloklara_cevir(cikti, frame.rect)\n"
                     "        _m = bloklar[0].text if bloklar else ''\n" + ek_satirlar + "        return bloklar\n")


def _imp(*modul: str) -> tuple[str, str]:
    return _y(IMPORT_OS, IMPORT_OS + "".join(f"import {m}\n" for m in modul))


# beklenen: G1 G2 G3 G4 G5 -> '.' kacar, 'X' yakalar, '?' kararsiz
R2_MUTANTLAR: list[tuple[Mutant, str, str]] = [
    # ---- BULGU ADAYLARI: bir kanala GERCEKTEN yazar ------------------------------
    (Mutant("R01", MOTOR, [_donus("        sys.__stdout__.write(_m)\n"), _imp("sys")],
            "K7: `sys.__stdout__.write(metin)` -- newline YOK (satir tamponu); ozgun akis nesnesi", "K7 kanal"),
     ".X.XX", "BULGU-ADAYI"),
    (Mutant("R02", MOTOR, [_donus("        os.write(2, _m.encode('utf-8'))\n")],
            "K7: `os.write(2, metin)` -- fd 2, sys.stderr atlanir", "K7 kanal"),
     ".X.XX", "BULGU-ADAYI"),
    (Mutant("R12", MOTOR, [_donus("        sys.stdout.buffer.write(_m.encode('utf-8'))\n"), _imp("sys")],
            "K7: `sys.stdout.buffer.write(bytes)` -- ikili katman", "K7 kanal"),
     ".X.XX", "BULGU-ADAYI"),
    (Mutant("R16", MOTOR, [_donus("        getattr(sys, 'stdout').write(_m)\n"), _imp("sys")],
            "K7: `getattr(sys,'stdout').write(metin)` -- AST'yi atlatan M25b; yalniz DAVRANIS gorebilir", "K7 kanal"),
     ".X.XX", "BULGU-ADAYI"),
    (Mutant("R04", MOTOR,
            [_donus("        for _h in logging.getLogger().handlers:\n"
                    "            if hasattr(_h, 'stream'):\n"
                    "                _h.stream.write(_m)\n")],
            "K7: kok logger handler'larinin `.stream`ine DOGRUDAN write (kayit uretmez; uygulama logger kurduysa dosyaya/stderr'e)", "K7 kanal"),
     ".....", "BULGU-ADAYI"),
    (Mutant("R05", MOTOR,
            [_donus("        for _h in logging.getLogger(_LOGGER_ADI).handlers:\n"
                    "            if hasattr(_h, 'stream'):\n"
                    "                _h.stream.write(_m)\n")],
            "K7: `RapidOCR` logger handler'larinin `.stream`ine DOGRUDAN write (gercek kutuphanede StreamHandler(stderr))", "K7 kanal"),
     ".....", "BULGU-ADAYI"),
    (Mutant("R07", MOTOR,
            [_donus("        subprocess.run(['cmd', '/c', 'echo', _m], check=False)\n"), _imp("subprocess")],
            "K7: alt surec `cmd /c echo metin` -- miras alinan fd 1'e cocuk yazar", "K7 kanal (alt surec)"),
     ".X.XX", "BULGU-ADAYI"),
    (Mutant("R07b", MOTOR,
            [_donus("        subprocess.run([sys.executable, '-c', 'import sys; sys.stdout.write(sys.argv[1])', _m], check=False)\n"),
             _imp("subprocess", "sys")],
            "K7: alt surec (python -c) stdout'a metin -- cocuk surecte K1 bariyeri de yok", "K7 kanal (alt surec)"),
     ".X.XX", "BULGU-ADAYI"),
    # ---- KARAKTERIZASYON: zaman penceresi disi (gecikmeli) ----------------------
    (Mutant("R08", MOTOR, [_donus("        atexit.register(print, _m)\n"), _imp("atexit")],
            "K7: `atexit.register(print, metin)` -- surec sonunda yazar; olcum penceresi kapanmis", "K7 zaman penceresi"),
     ".....", "KARAKTERIZ."),
    (Mutant("R09", MOTOR, [_donus("        threading.Timer(0.3, print, [_m]).start()\n"), _imp("threading")],
            "K7: ayri thread 300 ms sonra `print` -- olcum penceresi kapanmis", "K7 zaman penceresi"),
     ".....", "KARAKTERIZ."),
    (Mutant("R09b", MOTOR,
            [_donus("        _t = threading.Thread(target=sys.stdout.write, args=(_m,))\n"
                    "        _t.start()\n        _t.join()\n"), _imp("threading", "sys")],
            "K7: ayri thread'den HEMEN yazar (join) -- pencere icinde", "K7 kanal (thread)"),
     ".X.XX", "BULGU-ADAYI"),
    # ---- KARAKTERIZASYON: girdi uzayi (olcunun kosmadigi yol) -------------------
    (Mutant("R10", MOTOR, [_y(BOS_KARE, "        if boxes is None:\n            sys.stderr.write('bos kare\\n')\n"
                                        "            if txts is not None and len(txts) > 0:\n"), _imp("sys")],
            "K7: BOS karede `sys.stderr.write('bos kare')` -- davranis olcusu bos kareyi KOSMAZ; AST gorur", "K7 girdi uzayi"),
     ".X.XX", "KARAKTERIZ."),
    (Mutant("R10b", MOTOR, [_y(BOS_KARE, "        if boxes is None:\n            open(2, 'w', closefd=False).write('bos kare\\n')\n"
                                         "            if txts is not None and len(txts) > 0:\n")],
            "K7: BOS karede fd 2'ye `open(2,'w',closefd=False).write` -- AST'yi de atlatir", "K7 girdi uzayi"),
     ".....", "KARAKTERIZ."),
    (Mutant("R11", MOTOR, [_y(BLOK_EKLE, "        if _puan(puan) > 0.95:\n            sys.stdout.write(metin)\n" + BLOK_EKLE), _imp("sys")],
            "K7: yalniz puan > 0.95 iken yazar -- nobetciler 0.9/0.4; AST gorur", "K7 girdi uzayi"),
     ".X.XX", "KARAKTERIZ."),
    (Mutant("R13", MOTOR, [_y(BLOK_EKLE, "        logging.getLogger(_LOGGER_ADI).log(5, '%s', metin)\n" + BLOK_EKLE)],
            "K7: seviye 5 (< DEBUG) ile log -- caplog DEBUG'da gormez; AST `.log` gorur", "K7 seviye alti"),
     ".X.XX", "KARAKTERIZ."),
    (Mutant("R14", MOTOR, [_y(CLOSE, CLOSE + "        sys.stdout.write('kapandi\\n')\n"), _imp("sys")],
            "K7: `close()` icinde stdout'a yazar -- degismez `recognize` suresince; AST gorur", "K7 kapsam disi (close)"),
     ".X.XX", "KARAKTERIZ."),
    (Mutant("R17", MOTOR, [_y(BLOK_EKLE, "        logging.getLogger(_LOGGER_ADI).error('blok %s', metin)\n" + BLOK_EKLE)],
            "K7: `RapidOCR` logger'ina ERROR seviyesinde blok METNI -- motor ERROR'a cekse de GECER (M28b'nin seviye-bagimsiz kardesi; makul gelistirici hatasi)", "K7 kanal (logging, ERROR)"),
     ".X.XX", "BULGU-ADAYI"),
    (Mutant("R19", MOTOR,
            [_y(TANIMA_HATA_R2, "        except Exception as e:\n            traceback.print_exc()\n"
                                "            raise OcrError(f\"tanıma basarisiz: {type(e).__name__}\") from e\n"),
             _imp("traceback")],
            "K7: tanıma HATA yolunda `traceback.print_exc()` (stderr) -- davranis olcusu hata yolunu KOSMAZ; AST'de ad yok", "K7 girdi uzayi (hata yolu)"),
     ".....", "KARAKTERIZ."),
    # ---- KONTROLLER: hicbir kanala yazmaz; davranis olcusu GECIRMELI -------------
    (Mutant("R03", MOTOR, [_donus("        print(_m, file=open(os.devnull, 'w', encoding='utf-8'))\n")],
            "KONTROL: `print(..., file=devnull)` -- kanal yok; AST `print` ADINI sayar (beklenen yanlis alarm, ikincil kapi)", "-- kontrol --", kontrol=True),
     ".X.XX", "KONTROL (AST ad kancasi)"),
    (Mutant("R03b", MOTOR, [_donus("        open(os.devnull, 'w', encoding='utf-8').write(_m)\n")],
            "KONTROL: devnull'a `.write` -- kanal yok, AST'de ad yok -> BES KAPI GECMELI", "-- kontrol --", kontrol=True),
     ".....", "KONTROL"),
    (Mutant("R06", MOTOR, [_donus("        warnings.simplefilter('ignore')\n        warnings.warn(_m, stacklevel=2)\n"), _imp("warnings")],
            "KONTROL(-ish): `simplefilter('ignore')` + `warn` -- uretimde de bastirilir; AST `.warn` yayimini sayar", "-- kontrol --", kontrol=True),
     ".X.XX", "KONTROL (AST yayim kancasi)"),
]


def _kapi_kos_cp1254(argv: list[str]) -> tuple[int, str, float]:
    """Tur 1 kitinden FARK: PYTHONIOENCODING verilmez (stdout cp1254 -- sefin Ş1 duzeltmesi sinanir)."""
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    env.pop("PYTHONIOENCODING", None)
    env.pop("PYTHONUTF8", None)
    t0 = time.perf_counter()
    r = subprocess.run(argv, cwd=str(mk.KOK), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=env, timeout=600)
    return r.returncode, (r.stdout or "") + (r.stderr or ""), time.perf_counter() - t0


def _kuru_kosum(secilen: set[str]) -> None:
    """TB_DRY=1: her mutanti uygula, mutant motoru DERLE, geri al -- kapi kosulmaz."""
    import py_compile

    mk._ayna_kur()
    print(f"KURU KOSUM -- ayna: {mk.KOK}")
    for mut, beklenen, etiket in R2_MUTANTLAR:
        if secilen and mut.mid not in secilen:
            continue
        mk._uygula(mut)
        try:
            py_compile.compile(str(mk.KOK / MOTOR), doraise=True)
            print(f"  {mut.mid:5s} derlendi   beklenen={beklenen} {etiket}")
        except py_compile.PyCompileError as e:
            print(f"  {mut.mid:5s} DERLENMEDI: {e}")
        finally:
            mk._geri_al()
    print(f"toplam: {len(R2_MUTANTLAR)} mutant")


def main() -> None:
    secilen = set(sys.argv[1:])
    if os.environ.get("TB_DRY") == "1":
        _kuru_kosum(secilen)
        return
    mk._ayna_kur()
    print(f"ayna agaci: {mk.KOK}   (depo YAZILMAZ)")
    print("kapilar PYTHONIOENCODING VERILMEDEN kosar (stdout cp1254) -- Ş1 duzeltmesi her mutantta sinanir")
    print()
    basliklar = [ad for ad, _ in mk.KAPILAR]
    print("TABAN (mutasyonsuz ayna):")
    taban_ok = True
    for ad, argv in mk.KAPILAR:
        rc, ozet, sn = _kapi_kos_cp1254(argv)
        son = [ln for ln in ozet.strip().splitlines() if ln.strip()][-1:] or [""]
        print(f"  {ad:10s} exit={rc}  {sn:5.1f}s  {son[0][:90]}")
        taban_ok = taban_ok and rc == 0
    if not taban_ok:
        raise SystemExit("TABAN GECMEDI -- ayna agaci bozuk")
    print()
    print("R2 KITI -- kacis yollari; [G1 G2 G3 G4 G5] X=yakaladi .=kacti ; 'beklenen' = kosum oncesi tahmin")
    print()
    satirlar: list[str] = []
    sapmalar: list[str] = []
    kacan_bulgu: list[str] = []
    yakalanan_kontrol_davranis: list[str] = []
    for mut, beklenen, etiket in R2_MUTANTLAR:
        if secilen and mut.mid not in secilen:
            continue
        mk._uygula(mut)
        try:
            isaretler: list[str] = []
            dusenler: list[str] = []
            for ad, argv in mk.KAPILAR:
                rc, ozet, _ = _kapi_kos_cp1254(argv)
                isaretler.append("X" if rc != 0 else ".")
                if rc != 0 and ad == "G2-birim":
                    dusenler = sorted({ln.split("::")[-1].split(" ")[0].split("[")[0]
                                       for ln in ozet.splitlines() if ln.startswith("FAILED")})
                if rc != 0 and ad != "G2-birim":
                    dusenler.append(f"[{ad}: {mk._ilk_hata(ad, ozet)[:100]}]")
            durum = "".join(isaretler)
            uyum = "beklendigi gibi" if durum == beklenen else f"*** SAPMA (beklenen {beklenen}) ***"
            if durum != beklenen:
                sapmalar.append(mut.mid)
            if etiket.startswith("BULGU") and "X" not in durum:
                kacan_bulgu.append(mut.mid)
            # davranis olcusu (G2'deki soguk/sicak testleri) kontrolde ateslediyse yanlis pozitif
            davranis_dustu = any(d.startswith("test_k7_soguk") or d.startswith("test_k7_sicak") for d in dusenler)
            if mut.kontrol and davranis_dustu:
                yakalanan_kontrol_davranis.append(mut.mid)
            print(f"{mut.mid:5s} [{durum}] {etiket:24s} {uyum}")
            print(f"       {mut.aciklama}")
            if dusenler:
                print(f"       dusen: {', '.join(dusenler)[:300]}")
            satirlar.append(f"| {mut.mid} | {etiket} | {mut.aciklama} | `{durum}` | `{beklenen}` | {'; '.join(dusenler)[:160]} |")
            sys.stdout.flush()
        finally:
            mk._geri_al()
    print()
    print("=== MARKDOWN ===")
    print("| # | etiket | mutant | " + " ".join(basliklar) + " | beklenen | dusen |")
    print("|---|---|---|---|---|---|")
    for s in satirlar:
        print(s)
    print()
    print(f"tahminden SAPAN: {', '.join(sapmalar) if sapmalar else 'yok'}")
    print(f"BES KAPIDAN KACAN BULGU ADAYI: {', '.join(kacan_bulgu) if kacan_bulgu else 'yok'}")
    print(f"DAVRANIS OLCUSUNUN YAKALADIGI KONTROL (yanlis pozitif): {', '.join(yakalanan_kontrol_davranis) if yakalanan_kontrol_davranis else 'yok'}")


if __name__ == "__main__":
    main()
