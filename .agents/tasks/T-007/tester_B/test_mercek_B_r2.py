"""TESTER-B mercek B -- TUR 2 ek testleri (T2-1 / T2-2 / T2-3 degismezleri, biçimden bagimsiz).

Tur 1'in 55 testi `test_mercek_B.py`de aynen duruyor (regresyon). Buradakiler
sef kararinin uc kalemini DEGISMEZ olarak (mekanizma degil) yeniden olcer:

  B2-1  K3 kume degismezi: `.!?。！？` altisinin HER BIRI, TEK BASINA, HER
        KONUMDA boler; kume DISI hicbir isaret bolmez (deterministik fuzz).
  B2-2  T2-2 degismezi: parca, bildirilen yer tutucular cikarildiktan sonra
        harf/rakam icermiyorsa gitmez -- uc durumlar (`{0}}`, `{{0}`, iki yt +
        bir harf, Unicode harf, yalniz noktalama, segment izolasyonu).
  B2-3  T2-3: nobetci testinin bes yolu GERCEKTEN hedeflenen raise satirina
        dusuyor; `match=` dogru sebebi sabitliyor (kanal degisince duser);
        nobetcisiz kalan iki yol (dizi-yerine, `ilk` str) karakterize edildi.

Kosum: python -m pytest .agents/tasks/T-007/tester_B -q -p no:cacheprovider
"""
from __future__ import annotations

import logging
import random
import re
import sys
import warnings
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

import tb_bariyer  # noqa: F401
from src.contracts.errors import ContractViolation, ProviderUnavailable
from src.contracts.models import Rect, Segment, TranslationRequest
from src.translate.local_nmt import cumlelere_bol, modele_gider
from test_mercek_B import HEDEF, NOBETCILER, SahteFabrika, SahteHipotez, SahteMotor, T, istek, saglayici

TERMINATORLER = ".!?。！？"  # paket K3 metninden SABIT (4.6/8: saglayicidan turetilmez)
KAPANISLAR = "」』）)\"'”’»"
TERMINATOR_DEGIL = ",;:…、，．\n\t ~-·"  # kume DISI: bolmemeli (`．` U+FF0E ve `…` docstring'de acikca terminator DEGIL)


@pytest.fixture
def handle_kancasi(monkeypatch: pytest.MonkeyPatch) -> list[logging.LogRecord]:
    kayitlar: list[logging.LogRecord] = []
    ozgun = logging.Logger.handle

    def _handle(self: logging.Logger, record: logging.LogRecord) -> None:
        kayitlar.append(record)
        ozgun(self, record)

    monkeypatch.setattr(logging.Logger, "handle", _handle)
    return kayitlar


@pytest.fixture
def yabanci_logger_geri_al() -> Iterator[None]:
    adlar = ("bilinmeyen.kutuphane.logger", "suflor.translate")
    eski = {ad: (logging.getLogger(ad).level, logging.getLogger(ad).propagate, list(logging.getLogger(ad).handlers)) for ad in adlar}
    yield
    for ad, (lv, pr, hs) in eski.items():
        lg = logging.getLogger(ad)
        lg.setLevel(lv)
        lg.propagate = pr
        lg.handlers[:] = hs


# ===========================================================================
# B2-1 -- K3 kume degismezi: her terminator tek basina her konumda; kume disi bolmez
# ===========================================================================


@pytest.mark.parametrize("t", list(TERMINATORLER), ids=[f"U+{ord(c):04X}" for c in TERMINATORLER])
@pytest.mark.parametrize("konum", ["A{t} B", "A{t}B", "{t}A", "A{t}{t}B", "A{t}」B", "A{t} 」 B", "AB{t}C{t}D"], ids=["bosluklu", "bitisik", "basta", "ardisik", "kapanisli", "bosluklu-kapanis", "uclu"])
def test_r2_k3_her_terminator_tek_basina_her_konumda_boler(t: str, konum: str) -> None:
    """Degismez: `t` tek basina (baska terminator yokken) bir cumle sonudur -- konumdan bagimsiz.

    Beklenen parca sayisi konuma gore SABIT (terminatorden turetilmez): terminatorden
    sonra harf geliyorsa yeni parca baslar; ardisik/kapanisli isaretler ayni parcada.
    """
    metin = konum.format(t=t)
    parcalar = cumlelere_bol(metin)
    beklenen = {"bosluklu": 2, "bitisik": 2, "basta": 2, "ardisik": 2, "kapanisli": 2, "bosluklu-kapanis": 2, "uclu": 3}
    ad = {"A{t} B": "bosluklu", "A{t}B": "bitisik", "{t}A": "basta", "A{t}{t}B": "ardisik", "A{t}」B": "kapanisli", "A{t} 」 B": "bosluklu-kapanis", "AB{t}C{t}D": "uclu"}[konum]
    assert len(parcalar) == beklenen[ad], (metin, parcalar)
    assert "".join(cumlelere_bol(metin, ham=True)) == metin  # kayipsiz
    # ilk parca `t` ile (ya da `t` + kapanis) biter; hicbir parcada `t`den sonra harf gelmez
    for p in parcalar[:-1]:
        assert p.rstrip(KAPANISLAR + " ").endswith(t), (metin, p)
    for p in parcalar:
        i = p.find(t)
        if i >= 0:
            assert not any(ch.isalnum() for ch in p[i:]), (metin, p)


@pytest.mark.parametrize("k", list(KAPANISLAR), ids=[f"U+{ord(c):04X}" for c in KAPANISLAR])
def test_r2_k3_her_kapanis_isareti_tek_basina_onceki_cumleye_dahil(k: str) -> None:
    """Kapanis kumesi degismezi DOKUZ noktada ayri (4.6/7): teslim yalniz `」` ile olcuyor (R2-K3-18a..h bes kapidan kacti).

    `A.{k} B.` -> [`A.{k}`, `B.`]; `A. {k} B.` (bosluklu) -> [`A. {k}`, `B.`]; `{k}` tek basina gecis parcasi.
    """
    assert cumlelere_bol(f"A.{k} B.") == [f"A.{k}", "B."], k
    assert cumlelere_bol(f"A. {k} B.") == [f"A. {k}", "B."], k
    assert cumlelere_bol(f"A。{k}{k}B。") == [f"A。{k}{k}", "B。"], k
    assert cumlelere_bol(k) == [k] and not modele_gider(k)


@pytest.mark.parametrize("isaret", list(TERMINATOR_DEGIL), ids=[f"U+{ord(c):04X}" for c in TERMINATOR_DEGIL])
def test_r2_k3_kume_disi_isaret_bolmez(isaret: str) -> None:
    """Kume SINIRI: `．` (U+FF0E), `…`, satir sonu, sekme, `、`, `，`, `;`, `:` ... hicbiri bolmez."""
    assert cumlelere_bol(f"A{isaret}B") == [f"A{isaret}B"]
    assert cumlelere_bol(f"A{isaret} B.") == [f"A{isaret} B."]
    assert len(cumlelere_bol(f"A{isaret}\nB{isaret} C")) == 1


def _parca_gecerli(p: str) -> bool:
    """Bir parca: [terminatorsuz govde][terminator+][bosluk*kapanis*]* -- ya da terminatorsuz kuyruk."""
    i = next((k for k, ch in enumerate(p) if ch in TERMINATORLER), -1)
    if i < 0:
        return True
    kuyruk = p[i:]
    return all(ch in TERMINATORLER or ch in KAPANISLAR or ch.isspace() for ch in kuyruk)


def test_r2_k3_fuzz_degismezi_1000_rastgele_metin() -> None:
    """Deterministik fuzz (seed 7): harf + 6 terminator + kapanis + kume disi + bosluk karisimi.

    Degismezler: (1) ham parcalarin birlesimi kaynak; (2) her parcada ilk terminatorden
    sonra yalniz terminator/kapanis/bosluk gelir (yani terminator her zaman parcayi bitirir);
    (3) son parca disinda her parca terminator (+kapanis) ile biter -- kume DISI bir isaret
    parcayi bitirmez; (4) modele giden her parca harf/rakam icerir.
    """
    rng = random.Random(7)
    alfabe = "abcXYZçğ村長老" + TERMINATORLER * 2 + KAPANISLAR + TERMINATOR_DEGIL + "  "
    for _ in range(1000):
        metin = "".join(rng.choice(alfabe) for _ in range(rng.randint(0, 24)))
        ham = cumlelere_bol(metin, ham=True)
        assert "".join(ham) == metin, metin
        parcalar = cumlelere_bol(metin)
        assert all(p == p.strip() and p for p in parcalar), metin
        for p in parcalar:
            assert _parca_gecerli(p), (metin, p)
        for p in parcalar[:-1]:
            govde = p.rstrip(KAPANISLAR + " \t\n")
            assert govde and govde[-1] in TERMINATORLER, (metin, p)
        for p in parcalar:
            if modele_gider(p):
                assert any(ch.isalnum() for ch in p)
        # (5) her terminator bir parca sinirinda: kaynakta `t` + harf ardisikligi varsa iki ayri parcada
        for m in re.finditer(f"[{re.escape(TERMINATORLER)}][{re.escape(KAPANISLAR)}\\s]*(\\w)", metin):
            harf_konumu = m.end() - 1
            # harfin bulundugu parca, terminatoru iceren parcadan farkli olmali
            konum = 0
            sahibi: list[int] = []
            for k, h in enumerate(ham):
                sahibi.extend([k] * len(h))
                konum += len(h)
            assert sahibi[harf_konumu] != sahibi[m.start()], (metin, ham)


# ===========================================================================
# B2-2 -- T2-2 degismezi: yer tutucular cikarildiktan sonra harf/rakam
# ===========================================================================


@pytest.mark.parametrize(
    ("parca", "yt", "beklenen"),
    [
        ("{0}}!", ("{0}",), False),  # fazla `}` kalir: noktalama -> gitmez (tam alt dize cikarimi)
        ("{{0}!", ("{0}",), False),  # fazla `{` kalir -> gitmez
        ("{0}}!", ("{0}}",), False),
        ("{0} a {1}", ("{0}", "{1}"), True),  # iki yt + BIR harf -> gider
        ("{0} ç", ("{0}",), True),  # Unicode harf
        ("{0} ３", ("{0}",), True),  # tam genislik rakam (isalnum)
        ("{0}村", ("{0}",), True),  # CJK harf
        ("{0}!", (), True),  # liste bos: yer tutucu bicimli metin METINDIR
        ("{0}!", ("",), True),  # bos yer tutucu yok sayilir; `{0}` metindir
        ("PLAYER!", ("PLAYER",), False),  # yer tutucu harf-only olsa da cikarilir
        ("PLAYERS!", ("PLAYER",), True),  # `S` kalir
        ("{0}!", ("{0}", "{0}"), False),  # yinelenen liste
        ("{0}{1}{0}?!", ("{0}", "{1}"), False),
        ("({0})", ("{0}",), False),
        ("「{0}」", ("{0}",), False),
        ("{0}...", ("{0}",), False),
        ("{0} {1}", ("{0}", "{1}"), False),  # yalniz bosluk kalir
        ("%s%%!", ("%s",), False),
        ("{0}", ("{1}",), True),  # bildirilmemis `{0}`: rakam icerir -> gider
        ("{name}!", ("{name}",), False),
        ("{name}!", ("{NAME}",), True),  # buyuk/kucuk harf duyarli: bildirilen `{NAME}` metinde yok
    ],
    ids=["fazla-kapali", "fazla-acik", "kapali-yt", "iki-yt-bir-harf", "unicode-c", "tam-genislik-rakam", "CJK", "liste-bos", "bos-yt", "harf-yt", "harf-yt-kalan", "yinelenen", "uclu-karisik", "parantez", "tirnak", "uc-nokta", "yalniz-bosluk", "yuzde", "bildirilmemis", "adli", "buyuk-kucuk"],
)
def test_r2_t22_modele_gider_yardimcisi_uc_durumlar(parca: str, yt: tuple[str, ...], beklenen: bool) -> None:
    assert modele_gider(parca, yt) is beklenen


def test_r2_t22_cikarim_sirasi_ortusen_yer_tutucularda_sonucu_degistirmiyor() -> None:
    """Karakterizasyon: ortusen yer tutucular (`{0}`, `{0}}`) iki sirada da ayni sonuc -- gercekci girdi uzayinda sira bagimsiz."""
    for parca in ("{0}}!", "{0}!", "{0}} x", "{{0}}"):
        a = modele_gider(parca, ("{0}", "{0}}"))
        b = modele_gider(parca, ("{0}}", "{0}"))
        assert a is b, parca


def test_r2_t22_segment_izolasyonu_baska_segmentin_yer_tutucusu_bu_segmentte_metindir(tmp_path: Path) -> None:
    """Segment A `{0}` bildirir (aynen gecer); segment B ayni metni BILDIRMEDEN tasir: METINDIR, gider."""
    segs = (
        Segment(text="{0}!", bbox=Rect(0, 0, 800, 36), placeholders=("{0}",)),
        Segment(text="{0}!", bbox=Rect(0, 40, 800, 36)),
        Segment(text="{1} x", bbox=Rect(0, 80, 800, 36), placeholders=("{1}",)),
    )
    f = SahteFabrika(SahteMotor(cevir=lambda p: "T(" + p + ")"))
    r = saglayici(tmp_path, f).translate(TranslationRequest(segments=segs, source_lang="en", target_lang="tr"))
    assert f.motor.tum_gonderilen_parcalar() == ["{0}!", "{1} x"]
    assert r.translations == ("{0}!", "T({0}!)", "T({1} x)")


def _segs(*cift: tuple[str, tuple[str, ...]]) -> tuple[Segment, ...]:
    """Segment basina KENDI yer tutuculari (metinde gecenler) -- K5 `max(1, sayim)` kurali bildirilen-ama-yok yer tutucuyu EKLER."""
    return tuple(Segment(text=m, bbox=Rect(0, i * 40, 800, 36), placeholders=yt) for i, (m, yt) in enumerate(cift))


def test_r2_t22_iki_yer_tutucu_bir_harf_gider_ve_onarim_eklemez(tmp_path: Path) -> None:
    f = SahteFabrika(SahteMotor(cevir=lambda p: "T(" + p + ")"))
    segs = _segs(("{0} a {1}", ("{0}", "{1}")), ("{0} ç", ("{0}",)), ("{0}村。", ("{0}",)))
    r = saglayici(tmp_path, f).translate(TranslationRequest(segments=segs, source_lang="en", target_lang="tr"))
    assert f.motor.tum_gonderilen_parcalar() == ["{0} a {1}", "{0} ç", "{0}村。"]
    assert r.translations == ("T({0} a {1})", "T({0} ç)", "T({0}村。)")  # yer tutucular ciktida var -> onarim eklemedi


def test_r2_t22_bilgi_bildirilen_ama_metinde_olmayan_yer_tutucu_k5_ile_eklenir(tmp_path: Path) -> None:
    """Karakterizasyon (K5, tur 1 kabul; docstring `max(1, sayim)`): metinde gecmeyen bildirilmis `{1}` ciktiya EKLENIR.
    Normalizer yer tutucuyu metinden cikardigi icin erisilemez; T2-2 bulgusu DEGIL, kayit."""
    f = SahteFabrika(SahteMotor(cevir=lambda p: "T(" + p + ")"))
    r = saglayici(tmp_path, f).translate(istek(["{0} ç"], kaynak="en", yer_tutucular=("{0}", "{1}")))
    assert r.translations == ("T({0} ç) {1}",)


def test_r2_t22_yer_tutucu_cikarilinca_yalniz_noktalama_kalan_parcalar_motor_kurulmaz(tmp_path: Path) -> None:
    ciftler: list[tuple[str, tuple[str, ...]]] = [
        ("{0}!", ("{0}",)), ("{0}?!", ("{0}",)), ("{0}...", ("{0}",)), ("({0})", ("{0}",)), ("「{0}」", ("{0}",)),
        ("{0} {1}", ("{0}", "{1}")), ("{0}}!", ("{0}",)), ("{{0}!", ("{0}",)), ("PLAYER!", ("PLAYER",)),
    ]
    f = SahteFabrika(SahteMotor(cevir=lambda p: "UYDURMA"))
    r = saglayici(tmp_path, f).translate(TranslationRequest(segments=_segs(*ciftler), source_lang="en", target_lang="tr"))
    assert f.calls == 0 and f.motor.call_count == 0
    assert r.translations == tuple(m for m, _ in ciftler)


def test_r2_t22_ayni_metin_bildirimle_gecer_bildirimsiz_gider_pozitif_negatif_cift(tmp_path: Path) -> None:
    """Ayni parca, yalniz `placeholders` farkiyla iki kola ayrilir -- suzgec gercekten listeye bagli (4.6/10)."""
    f1 = SahteFabrika(SahteMotor(cevir=lambda p: "T(" + p + ")"))
    r1 = saglayici(tmp_path, f1).translate(istek(["<T0>!"], kaynak="en", yer_tutucular=("<T0>",)))
    f2 = SahteFabrika(SahteMotor(cevir=lambda p: "T(" + p + ")"))
    r2 = saglayici(tmp_path, f2).translate(istek(["<T0>!"], kaynak="en"))
    assert (f1.calls, r1.translations) == (0, ("<T0>!",))
    assert (f2.calls, r2.translations) == (1, ("T(<T0>!)",))


# ===========================================================================
# B2-3 -- T2-3: nobetci testi hedeflenen yola dusuyor mu; match= dogru sebep
# ===========================================================================


def _parametrize_mark(fn: Any) -> Any:
    for m in getattr(fn, "pytestmark", []):
        if m.name == "parametrize":
            return m
    raise AssertionError("parametrize yok")


BEKLENEN_YOL_MESAJI: dict[str, str] = {
    "sayi-nobetcili-cikti": "kadar hipotez dondurmedi",
    "bozuk-nesne-nobetcili": "hipotez listesi yok ya da bos",
    "bos-hipotez-nobetcili-nesne": "hipotez listesi yok ya da bos",
    "int-token-nobetcili-hipotez": "hipotez tokenleri str degil",
    "decode-tip-nobetcili-nesne": "decode str dondurmedi",
}


def test_r2_t23_nobetci_testinin_bes_motor_yolu_hedeflenen_raise_satirina_dusuyor(tmp_path: Path) -> None:
    """Teslimin nobetcili bes fabrikasi, iddia ettigi yola dusuyor (baska bir erken raise'e degil) -- ve o yolda MOTOR_NOBETCISI sizmiyor."""
    mark = _parametrize_mark(T.test_k6_hata_mesajlari_kaynak_metni_tasimaz)
    ids = list(mark.kwargs["ids"])
    gorulen: set[str] = set()
    for (fabrika, hata), kimlik in zip(mark.args[1], ids, strict=True):
        if kimlik not in BEKLENEN_YOL_MESAJI:
            continue
        with pytest.raises(hata) as ei:
            saglayici(tmp_path, fabrika()).translate(istek(["NOBETCI-9c1e。", "x NOBETCI-9c1e."]))
        assert BEKLENEN_YOL_MESAJI[kimlik] in str(ei.value), (kimlik, str(ei.value))
        assert T.MOTOR_NOBETCISI not in str(ei.value) and T.MOTOR_NOBETCISI not in repr(ei.value)
        gorulen.add(kimlik)
    assert gorulen == set(BEKLENEN_YOL_MESAJI)


@pytest.mark.parametrize(
    ("cikti", "beklenen_mesaj"),
    [
        (lambda t: T.MOTOR_NOBETCISI, "motor dizi yerine str dondurdu"),  # motor duz str: `dizi yerine` yolu
        (lambda t: T.MOTOR_NOBETCISI.encode(), "motor dizi yerine bytes dondurdu"),
        (lambda t: [SahteHipotez(T.MOTOR_NOBETCISI) for _ in t], "hipotez listesi yok ya da bos"),  # hypotheses duz str -> Sequence ama str
        (lambda t: [SahteHipotez([T.MOTOR_NOBETCISI]) for _ in t], "hipotez token dizisi degil"),  # `ilk` duz str
        (lambda t: [SahteHipotez([T.MOTOR_NOBETCISI.encode()]) for _ in t], "hipotez token dizisi degil"),  # `ilk` bytes
    ],
    ids=["dizi-yerine-str", "dizi-yerine-bytes", "hypotheses-str", "ilk-str", "ilk-bytes"],
)
def test_r2_t23_nobetcisiz_kalan_yollar_da_motor_ciktisini_tasimaz(tmp_path: Path, cikti: Any, beklenen_mesaj: str) -> None:
    """Teslimin nobetci testi bu yollari nobetcisiz birakti (`None`/`7`/`"tur_Latn x"`): burada nobetcili -- mesaj tasimamali.

    Gercek CT2 bu bicimleri uretmez (liste/liste/str) -> erisilebilirlik dusuk; keskinlik kaydi (R2-K10-10/11 kitte).
    """
    with pytest.raises(ProviderUnavailable) as ei:
        saglayici(tmp_path, SahteFabrika(SahteMotor(cikti=cikti))).translate(istek(["A。"]))
    assert beklenen_mesaj in str(ei.value)
    assert T.MOTOR_NOBETCISI not in str(ei.value) and T.MOTOR_NOBETCISI not in repr(ei.value)


class _KanalDegismis:
    """Teslimin sahte saglayicisinin KANALI degismis kopyasi: olcu yine duser ama BASKA sebeple."""

    def __init__(self, taban: type, yaz: Any) -> None:
        self._taban = taban
        self._yaz = yaz

    def yap(self) -> Any:
        taban = self._taban
        yaz = self._yaz

        class _Sahte(taban):  # type: ignore[misc,valid-type]
            def translate(self, request: TranslationRequest) -> Any:
                yaz()
                return T._sonuc(NOBETCILER[0])

        return _Sahte()


@pytest.mark.parametrize(
    ("sahte_adi", "teslim_match", "yeni_kanal"),
    [
        ("_StdoutaYazan", "stdout'a", lambda: sys.stderr.write(NOBETCILER[0])),
        ("_StderreYazan", "stderr'e", lambda: sys.stdout.write(NOBETCILER[0])),
        ("_FdYeYazan", "stdout'a", lambda: warnings.warn(NOBETCILER[0], stacklevel=2)),
        ("_OzgunStderreYazan", "stderr'e", lambda: logging.getLogger("suflor.translate").debug("s %s", NOBETCILER[0])),
        ("_KokLoggeraYazan", "log kaydina", lambda: sys.stdout.write(NOBETCILER[0])),
        ("_PropagateKapaliLoggeraYazan", "log kaydina", lambda: warnings.warn(NOBETCILER[0], stacklevel=2)),
        ("_UyariVeren", "warnings kaydina", lambda: sys.stderr.write(NOBETCILER[0])),
    ],
)
def test_r2_t23_match_kanal_degisince_duser_yanlis_sebeple_gecis_yok(
    sahte_adi: str, teslim_match: str, yeni_kanal: Any,
    capfd: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture,
    handle_kancasi: list[logging.LogRecord], yabanci_logger_geri_al: None,
) -> None:
    """Teslimin `match=` degeri (parametrize'dan OKUNUR, kopyalanmaz) kanal degisince uyusmaz -> pytest.raises DUSER."""
    mark = _parametrize_mark(T.test_k10_pozitif_kontrol_kanal_olcusu_atesliyor)
    beklenen = {sahte.__name__: msg for sahte, msg in mark.args[1]}
    assert beklenen[sahte_adi] == teslim_match  # teslimin tablosu benim sabitimle ayni
    sahte = _KanalDegismis(getattr(T, sahte_adi), yeni_kanal).yap()
    with pytest.raises(AssertionError, match="Regex pattern did not match|did not match"):
        with pytest.raises(AssertionError, match=beklenen[sahte_adi]):
            T._k10_kanal_olcusu(sahte, capfd, caplog, handle_kancasi)
    capfd.readouterr()
    caplog.clear()


def test_r2_t23_yedi_sahte_saglayici_teslim_match_ile_dogru_sebeple_dusuyor(
    capfd: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture,
    handle_kancasi: list[logging.LogRecord], yabanci_logger_geri_al: None,
) -> None:
    """Pozitif kontrol: degismemis yedi sahte, teslimin kendi `match=` degeriyle gecer (tur 1 B4 testinin tablo-okuyan surumu)."""
    mark = _parametrize_mark(T.test_k10_pozitif_kontrol_kanal_olcusu_atesliyor)
    assert len(mark.args[1]) == 7
    for sahte, msg in mark.args[1]:
        with pytest.raises(AssertionError, match=msg):
            T._k10_kanal_olcusu(sahte(), capfd, caplog, handle_kancasi)
        capfd.readouterr()
        caplog.clear()
        for ad in ("bilinmeyen.kutuphane.logger",):
            lg = logging.getLogger(ad)
            lg.propagate = True
            lg.setLevel(logging.NOTSET)


def test_r2_t23_sayi_uyusmazligi_ve_bozuk_cikti_mesajlari_yalniz_sayi_tip_tasir(tmp_path: Path) -> None:
    """Mesaj SOZLESME degil ama 'yalniz sayi/tip tasir' docstring iddiasi: nobetcili ciktida mesaj kisa ve nobetcisiz."""
    f = SahteFabrika(SahteMotor(cikti=lambda t: [SahteHipotez([[HEDEF, T.MOTOR_NOBETCISI]])] * (len(t) + 2)))
    with pytest.raises(ContractViolation) as ei:
        saglayici(tmp_path, f).translate(istek(["A。"]))
    assert re.fullmatch(r"motor gonderilen cumle sayisi kadar hipotez dondurmedi: cumle=1, hipotez=3 \(provider='[^']+'\)", str(ei.value)), str(ei.value)
