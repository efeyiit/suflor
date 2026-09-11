"""T-007 · Tester-A · mercek A: sözleşme uyumu, cümle bölme, dil/yer tutucu doğruluğu · tur 1.

Kör yazıldı: `delivery.md` okunmadı; yalnız `packet.md` (v2), `olgular.txt`,
`krt-1.md`, sözleşme ve kodun kendisi. Referanslar BAĞIMSIZ kanaldan
(PROTOKOL §4.6/8): NLLB kodları, kabul kümesi, dosya adları ve beklenen
parçalar burada SABİT yazılıdır; sağlayıcının tablosundan türetilmez.

Sahte motor: `translate_batch(tokens, target_prefix=..., beam_size=...,
max_decoding_length=..., **kw)` çağrılarını kaydeder; sahte `encode` parçayı
tek token yapar (`[parça]`), `decode` `"".join`. Böylece `tokens[i][1]` tam
olarak modele giden parça metnidir. `cevir` verilmezse echo.

Hiçbir test çeviri/kaynak metni yazdırmaz (PROTOKOL §6/7).

Bölümler: A0 bariyer · A1 bölme (K3) · A2 hizalama (K2) · A3 dil kodları (K4)
· A4 yer tutucu (K5) · A6 sayısal/tip (K8/K9) · AM mutant pozitif kontrolleri
(monkeypatch ile: ölçü gerçekten ateşliyor mu, §4.6/10).
"""
from __future__ import annotations

import ast
import dataclasses
import importlib
import re
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from src.contracts.errors import ContractViolation, ModelMissingError, ProviderUnavailable
from src.contracts.interfaces import TranslationProvider, ensure_aligned
from src.contracts.models import Pair, Rect, Segment, TermHit, TranslationRequest, TranslationResult
from src.translate import local_nmt
from src.translate.local_nmt import LocalNmtProvider, cumlelere_bol, modele_gider

# --- BAĞIMSIZ referanslar (olgular C4, packet K4/K6; sağlayıcıdan TÜRETİLMEZ) ---

KIMLIK = "local-nmt-nllb200-600m-int8"
HEDEF = "tur_Latn"
SON = "</s>"
DOSYALAR = ("model.bin", "sentencepiece.bpe.model", "shared_vocabulary.txt", "config.json")
KAYNAK_KODLARI: dict[str, tuple[str, str, str]] = {  # NLLB -> (NLLB, ISO 639-1, OcrLanguage)
    "jpn_Jpan": ("jpn_Jpan", "ja", "japan"),
    "kor_Hang": ("kor_Hang", "ko", "korean"),
    "zho_Hans": ("zho_Hans", "zh", "chinese"),
    "eng_Latn": ("eng_Latn", "en", "english"),
}
HEDEF_KODLARI = ("tr", "tur", "tur_Latn", "turkish")
KR = ("마을 장로가 당신을 기다리고 있습니다.", "방앗간을 지나 동쪽 길로 가십시오.")
JP = ("村の長老があなたを待っています。", "水車小屋を過ぎて東の道を行きなさい。", "日が暮れたら道を外れないように。")


# --- sahte motor / fabrika -----------------------------------------------------


@dataclasses.dataclass
class Hip:
    hypotheses: Any


class Motor:
    def __init__(
        self,
        cevir: Callable[[str], str] | None = None,
        cikti: Callable[[list[list[str]]], Any] | None = None,
    ) -> None:
        self.cevir = cevir
        self.cikti = cikti
        self.calls: list[dict[str, Any]] = []

    def translate_batch(
        self,
        tokens: list[list[str]],
        *,
        target_prefix: list[list[str]],
        beam_size: int,
        max_decoding_length: int,
        **kw: object,
    ) -> Sequence[object]:
        self.calls.append(
            {
                "tokens": [list(t) for t in tokens],
                "target_prefix": [list(p) for p in target_prefix],
                "beam_size": beam_size,
                "max_decoding_length": max_decoding_length,
                "kw": dict(kw),
            }
        )
        if self.cikti is not None:
            return self.cikti(tokens)  # type: ignore[no-any-return]
        return [Hip([[HEDEF, self._cevir("".join(t[1:-1]))]]) for t in tokens]

    def _cevir(self, p: str) -> str:
        return p if self.cevir is None else self.cevir(p)

    def parcalar(self, cagri: int = -1) -> list[str]:
        return [t[1] for t in self.calls[cagri]["tokens"]]

    def tum_parcalar(self) -> list[str]:
        return [t[1] for c in self.calls for t in c["tokens"]]


class Fabrika:
    def __init__(self, motor: Motor | None = None) -> None:
        self.motor = motor if motor is not None else Motor()
        self.calls = 0
        self.params: list[dict[str, object]] = []

    def __call__(self, model_dir: Path, params: dict[str, object]) -> tuple[Any, Any, Any]:
        self.calls += 1
        self.params.append(dict(params))
        return self.motor, (lambda m: [m]), (lambda ts: "".join(ts))


def dosyalar(dizin: Path) -> None:
    for ad in DOSYALAR:
        (dizin / ad).write_bytes(b"")


def sag(tmp_path: Path, f: Fabrika, **ek: Any) -> LocalNmtProvider:
    dosyalar(tmp_path)
    return LocalNmtProvider(model_dir=tmp_path, motor_fabrikasi=f, **ek)


def istek(
    metinler: Sequence[str],
    kaynak: Any = "jpn_Jpan",
    hedef: Any = "tr",
    ph: tuple[str, ...] = (),
    **ek: Any,
) -> TranslationRequest:
    segs = tuple(Segment(text=m, bbox=Rect(0, i * 40, 800, 36), placeholders=ph) for i, m in enumerate(metinler))
    return TranslationRequest(segments=segs, source_lang=kaynak, target_lang=hedef, **ek)


def isaretle(p: str) -> str:
    """Echo DEĞİL: çeviri parçasını `T(...)` ile sarar; geçiş parçası sarılmaz — ikisi ayırt edilir."""
    return "T(" + p + ")"


# ===========================================================================
# A0 — bariyer pozitif kontrolü (kendi başına + şefinkiyle birlikte aynı desen)
# ===========================================================================


@pytest.mark.parametrize("ad", ["ctranslate2", "sentencepiece", "ctranslate2.converters", "sentencepiece.x"])
def test_a0_bariyer_atesliyor(ad: str) -> None:
    sys.modules.pop(ad, None)
    with pytest.raises(RuntimeError, match="K1 bariyeri"):
        importlib.import_module(ad)


def test_a0_bariyer_komsulari_engellemiyor() -> None:
    importlib.import_module("numpy")
    importlib.import_module("json")


def test_a0_modul_duzeyinde_kutuphane_yok() -> None:
    """Modül zaten yüklü ve bariyer altında yüklendi → modül düzeyinde import olsaydı toplama patlardı."""
    agac = ast.parse(Path(local_nmt.__file__).read_text(encoding="utf-8"))
    ust = {n.names[0].name.split(".")[0] for n in agac.body if isinstance(n, ast.Import)}
    ust |= {(n.module or "").split(".")[0] for n in agac.body if isinstance(n, ast.ImportFrom)}
    assert not ust & {"ctranslate2", "sentencepiece"}


# ===========================================================================
# A1 — bölme (K3): parça sayısı, modele giden sayı, kayıpsızlık, çıktı bileşimi
# ===========================================================================

# (metin, beklenen parçalar, modele giden parça sayısı)
BOLME_TABLOSU: list[tuple[str, list[str], int]] = [
    ("A. B.", ["A.", "B."], 2),
    ("A.B.", ["A.", "B."], 2),  # boşluksuz — paket v2: boşluk şartı YOK
    ("3.5 km.", ["3.", "5 km."], 2),  # bilinen zayıflık: ondalık bölünür, ikisi de modele gider
    ("Dr. Smith.", ["Dr.", "Smith."], 2),  # bilinen zayıflık: kısaltma
    ("「A。」B。", ["「A。」", "B。"], 2),  # kapanış cümleye dahil
    ("A！？B", ["A！？", "B"], 2),  # ardışık terminatör tek parça + terminatörsüz kuyruk
    ("A.\n\nB.", ["A.", "B."], 2),
    ("...", ["..."], 0),  # Y2: harf/rakam yok → geçer
    ("？", ["？"], 0),
    ("   ", [], 0),  # yalnız boşluk → parça yok
    ("", [], 0),
    ("A。」」』", ["A。」」』"], 1),  # çoklu kapanış
    ("A. )", ["A. )"], 1),  # boşluklu kapanış
    (" ".join(KR), list(KR), 2),  # KR fixture'ının kendisi — ASCII nokta (Y1)
    ("".join(JP), list(JP), 3),  # C8 paragrafı
    ("待っています. 行きなさい.", ["待っています.", "行きなさい."], 2),  # yarım-genişlik JP nokta
    ("👨‍👩‍👧 hello. 🎉!", ["👨‍👩‍👧 hello.", "🎉!"], 1),  # ZWJ emoji; `🎉!` harf yok → geçer
    ("A🎉. B", ["A🎉.", "B"], 2),
    ("A. . B", ["A.", ".", "B"], 2),  # yalnız `.` parçası geçer
    ("(A.) B.", ["(A.)", "B."], 2),
    ("A)。B", ["A)。", "B"], 2),
    ("A.」.B", ["A.」", ".", "B"], 2),
    ("A.　B。", ["A.", "B。"], 2),  # ideografik boşluk kırpılır
    ("A．B．", ["A．B．"], 1),  # KAYIT: tam genişlik nokta U+FF0E terminatör DEĞİL (paket kümesinde yok)
    ("…A…B…", ["…A…B…"], 1),  # KAYIT: U+2026 terminatör değil (belgeli)
    ('A. "B."', ['A. "', 'B."'], 2),  # KAYIT: ASCII tırnak simetrik — AÇILIŞ tırnağı önceki cümleye yapışır
    ("{0}. B.", ["{0}.", "B."], 2),  # KAYIT: yalnız yer tutucu cümlesi rakam içerir → modele GİDER
    ("{PLAYER}! Wait!", ["{PLAYER}!", "Wait!"], 2),  # KAYIT: aynı sınıf, harfli yer tutucu
    ("%s!", ["%s!"], 1),  # `s` harf → modele gider (A5 5b6: gerçek model aynen geri verdi)
    ("①.", ["①."], 1),  # Unicode rakam sayılır
]


@pytest.mark.parametrize(("metin", "parcalar", "giden"), BOLME_TABLOSU, ids=[repr(m)[:24] for m, _, _ in BOLME_TABLOSU])
def test_a1_bolme_tablosu_parca_giden_kayipsiz(metin: str, parcalar: list[str], giden: int) -> None:
    assert cumlelere_bol(metin) == parcalar
    assert sum(1 for p in parcalar if modele_gider(p)) == giden
    ham = cumlelere_bol(metin, ham=True)
    assert "".join(ham) == metin  # kayıpsızlık: ham parçaların birleşimi kaynağın AYNISI
    assert [p.strip() for p in ham if p.strip()] == parcalar


@pytest.mark.parametrize(("metin", "parcalar", "giden"), BOLME_TABLOSU, ids=[repr(m)[:24] for m, _, _ in BOLME_TABLOSU])
def test_a1_saglayici_uzerinden_giden_sayi_ve_cikti_bilesimi(tmp_path: Path, metin: str, parcalar: list[str], giden: int) -> None:
    """Modele giden parçalar `T(...)` ile işaretlenir, geçiş parçaları aynen; çıktı `" "` ile birleşir."""
    f = Fabrika(Motor(cevir=isaretle))
    r = sag(tmp_path, f).translate(istek([metin]))
    assert len(r.translations) == 1
    if giden == 0:
        assert f.calls == 0 and not f.motor.calls  # motor KURULMAZ bile
        assert r.translations == (metin,)  # segment AYNEN
    else:
        assert f.calls == 1 and len(f.motor.calls) == 1
        assert f.motor.parcalar() == [p for p in parcalar if modele_gider(p)]
        beklenen = " ".join(isaretle(p) if modele_gider(p) else p for p in parcalar)
        assert r.translations == (beklenen,)
        # her modele giden parça çıktıda tam olarak BİR kez işaretli görünür
        assert r.translations[0].count("T(") == giden


def test_a1_uc_dilde_ayni_bolme(tmp_path: Path) -> None:
    """Bölme DİLE göre değil: aynı metin dört kaynak kodunda aynı parçalara ayrılır (Y1)."""
    metin = "A. B! C? D。E！F？ G"
    beklenen = ["A.", "B!", "C?", "D。", "E！", "F？", "G"]
    for kod in KAYNAK_KODLARI:
        f = Fabrika()
        sag(tmp_path, f).translate(istek([metin], kaynak=kod))
        assert f.motor.parcalar() == beklenen, kod


def test_a1_cok_segment_tek_cagri_dagitim_ve_sira(tmp_path: Path) -> None:
    f = Fabrika(Motor(cevir=isaretle))
    metinler = ["A。B。C。", "。。。", "D.", "", "E! 」 F?", "   "]
    r = sag(tmp_path, f).translate(istek(metinler))
    assert len(f.motor.calls) == 1
    assert f.motor.parcalar() == ["A。", "B。", "C。", "D.", "E! 」", "F?"]
    assert r.translations == ("T(A。) T(B。) T(C。)", "。。。", "T(D.)", "", "T(E! 」) T(F?)", "   ")


def test_a1_kayipsizlik_rastgele_karisimlar() -> None:
    """Ham parçaların birleşimi her zaman kaynağın kendisi — 300 rastgele karışım."""
    rng = np.random.default_rng(7)
    alfabe = list("ab1 \n\t.!?。！？」』）)\"'”’»「『(…{}%s") + ["　", "🎉", "‍", "あ", "한"]
    for _ in range(300):
        n = int(rng.integers(0, 40))
        metin = "".join(alfabe[int(i)] for i in rng.integers(0, len(alfabe), size=n))
        ham = cumlelere_bol(metin, ham=True)
        assert "".join(ham) == metin
        for p in cumlelere_bol(metin):
            assert p == p.strip() and p


def test_a1_kayipsizlik_saglayici_uzerinden_harf_rakam_dizisi(tmp_path: Path) -> None:
    f = Fabrika()
    metinler = [*JP, "".join(JP), *KR, "A! B？ C.", 'He said. "Go."', "3.5 km. OK", "{0}. B.", "e.g. x"]
    r = sag(tmp_path, f).translate(istek(metinler))

    def alnum(s: str) -> str:
        return "".join(ch for ch in s if ch.isalnum())

    for k, c in zip(metinler, r.translations, strict=True):
        assert alnum(c) == alnum(k)


def test_a1_regex_dogrusal_zaman_patolojik_girdi() -> None:
    import time

    for s in ["A." + " " * 200_000 + "x", "x" * 300_000, "A." + ' "' * 100_000 + "x", "." * 200_000, "A." + " " * 100_000 + '"' * 100_000 + "x"]:
        t0 = time.perf_counter()
        cumlelere_bol(s)
        assert (time.perf_counter() - t0) < 2.0, len(s)


# ===========================================================================
# A2 — hizalama (K2): cümle-düzeyi sayım, ensure_aligned, bozuk hipotez
# ===========================================================================


def _n_hip(n: int) -> Callable[[list[list[str]]], list[Hip]]:
    return lambda toks: [Hip([[HEDEF, "x"]]) for _ in range(n)]


@pytest.mark.parametrize(
    ("metinler", "donen"),
    [
        (["A。B。C。", "D。"], 3),  # 2 segment, 4 cümle, 3 döner → ensure_aligned GÖREMEZ (2 segment üretilebilir)
        (["A。B。C。", "D。"], 2),  # tam segment sayısı kadar — yine cümle sayısı tutmuyor
        (["A。", "B。C。D。"], 2),
        (["A。", "。。。", "B。"], 3),  # geçiş parçalı: gönderilen 2, dönen 3
        (["A。", "。。。", "B。"], 1),
        (["A。B。"], 1),  # tek segment, 2 cümle, 1 döner
        (["A。B。"], 3),
        (["A。"], 0),
        (["A。", "B。", "C。"], 2),
    ],
)
def test_a2_cumle_sayisi_tutmayan_hipotez_contractviolation(tmp_path: Path, metinler: list[str], donen: int) -> None:
    f = Fabrika(Motor(cikti=_n_hip(donen)))
    with pytest.raises(ContractViolation):
        sag(tmp_path, f).translate(istek(metinler))
    assert len(f.motor.calls) == 1  # motor çağrıldı, sayı burada yakalandı


def test_a2_dogru_sayida_hipotez_hizali_ve_gecis_parcasi_yerinde(tmp_path: Path) -> None:
    f = Fabrika(Motor(cikti=lambda toks: [Hip([[HEDEF, f"h{i}"]]) for i in range(len(toks))]))
    r = sag(tmp_path, f).translate(istek(["A。B。", "。。。", "C。", ""]))
    assert r.translations == ("h0 h1", "。。。", "h2", "")
    assert type(r.translations) is tuple and len(r.translations) == 4


def test_a2_ensure_aligned_davranissal_olarak_cagriliyor(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """AST değil DAVRANIŞ: modüldeki `ensure_aligned` adı kayıt edici ile değiştirilir; dolu ve BOŞ istekte çağrılmalı."""
    kayit: list[tuple[TranslationRequest, TranslationResult]] = []

    def kaydet(request: TranslationRequest, result: TranslationResult) -> None:
        kayit.append((request, result))
        ensure_aligned(request, result)

    monkeypatch.setattr(local_nmt, "ensure_aligned", kaydet)
    p = sag(tmp_path, Fabrika())
    rq = istek(["A。B。", "C。"])
    r = p.translate(rq)
    assert kayit and kayit[-1][0] is rq and kayit[-1][1] is r
    bos = istek([])
    rb = p.translate(bos)
    assert kayit[-1][0] is bos and kayit[-1][1] is rb and rb.translations == ()


def test_a2_bos_istek_bos_demet_latency_sifir_veya_pozitif_motor_yok(tmp_path: Path) -> None:
    f = Fabrika()
    r = sag(tmp_path, f).translate(istek([]))
    assert r.translations == () and type(r.translations) is tuple
    assert r.latency_ms >= 0.0 and type(r.latency_ms) is float
    assert f.calls == 0
    assert r.provider_id == KIMLIK and r.from_cache is False and r.partial is False


@pytest.mark.parametrize(
    "hip",
    [
        lambda toks: [Hip([]) for _ in toks],  # hypotheses boş liste
        lambda toks: [Hip(None) for _ in toks],
        lambda toks: [Hip("tur_Latn x") for _ in toks],  # str, dizi değil
        lambda toks: [object() for _ in toks],  # .hypotheses yok
        lambda toks: [Hip([[HEDEF, 5]]) for _ in toks],  # token str değil
        lambda toks: "abc",  # dizi değil
        lambda toks: None,
    ],
)
def test_a2_bozuk_hipotez_bicimi_provider_unavailable(tmp_path: Path, hip: Callable[[list[list[str]]], Any]) -> None:
    f = Fabrika(Motor(cikti=hip))
    with pytest.raises(ProviderUnavailable):
        sag(tmp_path, f).translate(istek(["A。"]))


def test_a2_yalniz_dil_belirteci_hipotezi_bos_ceviri_hizali(tmp_path: Path) -> None:
    """KAYIT: `hypotheses[0] == ["tur_Latn"]` → o cümlenin çevirisi `""`; iki cümlelik segmentte çıktı `" "` (yalnız boşluk)."""
    f = Fabrika(Motor(cikti=lambda toks: [Hip([[HEDEF]]) for _ in toks]))
    r = sag(tmp_path, f).translate(istek(["A。", "B。C。"]))
    assert r.translations == ("", " ")  # hizalı; boş çeviri sözleşmeyi ihlal etmez, keskinlik olarak kayıt


def test_a2_hedef_belirteci_yoksa_ilk_token_korunur(tmp_path: Path) -> None:
    f = Fabrika(Motor(cikti=lambda toks: [Hip([["merhaba", "dünya"]]) for _ in toks]))
    r = sag(tmp_path, f).translate(istek(["A。"]))
    assert r.translations == ("merhabadünya",)


def test_a2_uyum_altsinif_ve_sonuc_tipi(tmp_path: Path) -> None:
    p = sag(tmp_path, Fabrika())
    assert isinstance(p, TranslationProvider)
    r = p.translate(istek(["A。"]))
    assert isinstance(r, TranslationResult) and all(type(t) is str for t in r.translations)
    ensure_aligned(istek(["A。"]), r)


def test_a2_segments_listesi_de_hizalanir(tmp_path: Path) -> None:
    """Frozen dataclass tuple'ı zorlamaz; `segments` liste gelirse de hizalama tutar."""
    segs = [Segment(text="A。B。", bbox=Rect(0, 0, 1, 1)), Segment(text="C。", bbox=Rect(0, 0, 1, 1))]
    rq = TranslationRequest(segments=segs, source_lang="ja", target_lang="tr")  # type: ignore[arg-type]
    r = sag(tmp_path, Fabrika()).translate(rq)
    assert len(r.translations) == 2 and type(r.translations) is tuple


# ===========================================================================
# A3 — dil kodları (K4)
# ===========================================================================


def _bicimler(kod: str) -> list[str]:
    return [kod, kod.upper(), kod.lower(), kod.title(), kod.swapcase()]


@pytest.mark.parametrize("nllb", list(KAYNAK_KODLARI))
@pytest.mark.parametrize("bicim", [0, 1, 2])
def test_a3_uc_bicim_bes_harf_hali_ilk_token_son_prefix_her_satirda(tmp_path: Path, nllb: str, bicim: int) -> None:
    for kod in _bicimler(KAYNAK_KODLARI[nllb][bicim]):
        f = Fabrika()
        r = sag(tmp_path, f).translate(istek(["A。B。", "C.", "。。。", "D! E?"], kaynak=kod))
        toks = f.motor.calls[0]["tokens"]
        assert len(toks) == 5, kod
        for t in toks:
            assert t[0] == nllb and t[-1] == SON and len(t) == 3, (kod, t)
        assert f.motor.calls[0]["target_prefix"] == [[HEDEF]] * 5, kod
        assert r.detected_lang == nllb, kod
        assert isinstance(r.detected_lang, str)


@pytest.mark.parametrize(
    "kod",
    [None, "", " ja ", "ja ", " ja", "JA ", "jpn", "jp", "zh-CN", "zh_CN", "ja-JP", "tr", "tur", "tur_Latn", "turkish", "TR",
     "auto", "xx", "japanese", "kor", "eng", "en-US", "jpn-Jpan", "jpn_jpan_", b"ja", 5, 0, ("ja",), ["ja"], {"ja"}],
)
def test_a3_tablo_disi_kaynak_provider_unavailable_fabrika_sifir(tmp_path: Path, kod: Any) -> None:
    f = Fabrika()
    with pytest.raises(ProviderUnavailable):
        sag(tmp_path, f).translate(istek(["A。"], kaynak=kod))
    assert f.calls == 0


@pytest.mark.parametrize("hedef", [h for k in HEDEF_KODLARI for h in _bicimler(k)])
def test_a3_hedef_dort_bicim_harf_duyarsiz(tmp_path: Path, hedef: str) -> None:
    f = Fabrika()
    r = sag(tmp_path, f).translate(istek(["A。", "B。C。"], hedef=hedef))
    assert f.motor.calls[0]["target_prefix"] == [[HEDEF]] * 3
    assert len(r.translations) == 2


@pytest.mark.parametrize("hedef", ["en", "eng_Latn", "ja", "jpn_Jpan", " tr", "tr ", "tr-TR", "tr_TR", "", None, 5, b"tr", "türkçe", "turkce"])
def test_a3_tablo_disi_hedef_provider_unavailable_fabrika_sifir(tmp_path: Path, hedef: Any) -> None:
    f = Fabrika()
    with pytest.raises(ProviderUnavailable):
        sag(tmp_path, f).translate(istek(["A。"], hedef=hedef))
    assert f.calls == 0


def test_a3_kaynak_hata_hedeften_once_ve_ikisi_de_gecersizken_provider_unavailable(tmp_path: Path) -> None:
    with pytest.raises(ProviderUnavailable):
        sag(tmp_path, Fabrika()).translate(istek(["A。"], kaynak="xx", hedef="en"))


def test_a3_dil_hatasi_kapali_saglayicida_da_provider_unavailable(tmp_path: Path) -> None:
    p = sag(tmp_path, Fabrika())
    p.close()
    with pytest.raises(ProviderUnavailable):
        p.translate(istek(["A。"]))


def test_a3_source_lang_none_bos_istekte_bile_reddedilir(tmp_path: Path) -> None:
    with pytest.raises(ProviderUnavailable):
        sag(tmp_path, Fabrika()).translate(istek([], kaynak=None))


def test_a3_dil_hatasi_model_dosyasi_yokken_de_once_gelir(tmp_path: Path) -> None:
    """Dil doğrulaması dosya denetiminden ÖNCE: boş dizin + geçersiz kod → ProviderUnavailable (ModelMissing değil)."""
    p = LocalNmtProvider(model_dir=tmp_path, motor_fabrikasi=Fabrika())
    with pytest.raises(ProviderUnavailable):
        p.translate(istek(["A。"], kaynak="xx"))
    with pytest.raises(ModelMissingError):
        p.translate(istek(["A。"], kaynak="ja"))


def test_a3_karisik_dil_kodu_ayni_cikti_tum_bicimlerde(tmp_path: Path) -> None:
    """Aynı istek 12 kaynak kodu ile: motora giden tokenler (ilk token dahil) ve çıktı özdeş."""
    for nllb, bicimler in KAYNAK_KODLARI.items():
        kayitlar = []
        for kod in bicimler:
            for k in (kod, kod.upper()):
                f = Fabrika(Motor(cevir=isaretle))
                r = sag(tmp_path, f).translate(istek(["A. B。", "C"], kaynak=k))
                kayitlar.append((f.motor.calls[0]["tokens"], r.translations, r.detected_lang))
        assert all(k == kayitlar[0] for k in kayitlar), nllb
        assert kayitlar[0][2] == nllb


# ===========================================================================
# A4 — yer tutucu (K5)
# ===========================================================================


def test_a4_kaynakta_iki_ciktida_bir_bir_eklenir(tmp_path: Path) -> None:
    f = Fabrika(Motor(cevir=lambda p: "x {0} y"))
    r = sag(tmp_path, f).translate(istek(["{0} ve {0}。"], ph=("{0}",)))
    assert r.translations == ("x {0} y {0}",)
    assert r.translations[0].count("{0}") == 2


def test_a4_ciktida_uc_kaynakta_bir_ekleme_yok(tmp_path: Path) -> None:
    f = Fabrika(Motor(cevir=lambda p: "{0}{0}{0}"))
    r = sag(tmp_path, f).translate(istek(["{0} x。"], ph=("{0}",)))
    assert r.translations == ("{0}{0}{0}",)


@pytest.mark.parametrize(
    ("kaynak", "ph", "cikti", "beklenen"),
    [
        ("%s got %s.", ("%s", "%s"), "%s aldı", "%s aldı %s"),  # listede iki kez, sayım
        ("%s got %s.", ("%s",), "aldı", "aldı %s %s"),  # listede BİR kez, kaynakta iki → iki eklenir
        ("<color=red>X</color>.", ("<color=red>", "</color>"), "X", "X <color=red> </color>"),
        ("<color=red>X</color>.", ("<color=red>", "</color>"), "<color=red>X</color>", "<color=red>X</color>"),
        ("{PLAYER} wins.", ("{PLAYER}",), "kazandı", "kazandı {PLAYER}"),
        ("{PLAYER} wins.", ("{PLAYER}",), "{player} kazandı", "{player} kazandı {PLAYER}"),  # harf duyarlı: bozuk sayılır
        ("{{0}} x.", ("{{0}}", "{0}"), "t", "t {{0}} {0}"),  # iç içe: {{0}} eklenince {0} da sağlanır ama sıra: ikisi de eksikti
        ("{{0}} x.", ("{0}", "{{0}}"), "t", "t {0} {{0}}"),
        ("{{0}} x.", ("{{0}}", "{0}"), "{{0}} t", "{{0}} t"),  # {{0}} varsa {0} da alt dize olarak var → ekleme yok
        ("[Mill] x.", ("[Mill]",), "[Mill'de] x", "[Mill'de] x [Mill]"),  # O1 bozuk biçim: hem bozuk hem ekli (belgeli)
        ("{0} x.", ("{0}", "{0}"), "t", "t {0}"),  # listede tekrar, kaynakta bir → bir
        ("x.", ("{0}",), "t", "t {0}"),  # kaynakta HİÇ yok (normalizer hatası) → yine bir eklenir (max(1, 0))
        ("{0} x.", ("", "{0}"), "t", "t {0}"),  # boş yer tutucu atlanır
    ],
)
def test_a4_sayim_mantigi_tablosu(tmp_path: Path, kaynak: str, ph: tuple[str, ...], cikti: str, beklenen: str) -> None:
    f = Fabrika(Motor(cevir=lambda p, c=cikti: c))
    r = sag(tmp_path, f).translate(istek([kaynak], kaynak="en", ph=ph))
    assert r.translations == (beklenen,)


def test_a4_placeholders_bos_dokunulmaz(tmp_path: Path) -> None:
    f = Fabrika(Motor(cevir=lambda p: "t"))
    r = sag(tmp_path, f).translate(istek(["{0} {1} <T0> x。"], ph=()))
    assert r.translations == ("t",)


def test_a4_cumle_sinirinda_yer_tutucu_dogru_segmentte_onarilir(tmp_path: Path) -> None:
    """`{0}. B.` → `{0}.` kendi parçası (rakam içerir → modele gider). Model düşürürse SEGMENT sonuna eklenir; komşu segmente sızmaz."""
    f = Fabrika(Motor(cevir=lambda p: "t"))
    r = sag(tmp_path, f).translate(istek(["{0}. B.", "C. {1}", "D."], kaynak="en", ph=("{0}", "{1}")))
    assert f.motor.parcalar() == ["{0}.", "B.", "C.", "{1}", "D."]
    assert r.translations == ("t t {0} {1}", "t t {0} {1}", "t {0} {1}")  # her segment aynı listeyi taşıdı → her birine eklenir


def test_a4_segment_basina_farkli_yer_tutucu_listesi(tmp_path: Path) -> None:
    segs = (
        Segment(text="{0}. B.", bbox=Rect(0, 0, 1, 1), placeholders=("{0}",)),
        Segment(text="C. {1}", bbox=Rect(0, 0, 1, 1), placeholders=("{1}",)),
        Segment(text="D.", bbox=Rect(0, 0, 1, 1)),
    )
    f = Fabrika(Motor(cevir=lambda p: "t"))
    r = sag(tmp_path, f).translate(TranslationRequest(segments=segs, source_lang="en", target_lang="tr"))
    assert r.translations == ("t t {0}", "t t {1}", "t")


def test_a4_yer_tutucu_baska_cumleye_kaysa_da_segment_duzeyinde_var_sayilir(tmp_path: Path) -> None:
    f = Fabrika(Motor(cevir=lambda p: "{0} t" if p.startswith("B") else "t"))
    r = sag(tmp_path, f).translate(istek(["{0} A。B。"], ph=("{0}",)))
    assert r.translations == ("t {0} t",)


def test_a4_gecis_segmentinde_yer_tutucu_zaten_kaynakta(tmp_path: Path) -> None:
    f = Fabrika()
    r = sag(tmp_path, f).translate(istek(["<>", "..."], kaynak="en", ph=("<>",)))
    assert r.translations == ("<>", "... <>")  # ikinci segmentte kaynakta yok → eklenir (liste her segmente aynı)
    assert f.calls == 0  # ikisi de geçiş: motor kurulmadı


def test_a4_sozluk_tm_stil_gorsel_dolu_cikti_ve_motor_cagrisi_ayni(tmp_path: Path) -> None:
    f1, f2 = Fabrika(Motor(cevir=isaretle)), Fabrika(Motor(cevir=isaretle))
    duz = istek(["A。B。", "{0} C."], ph=("{0}",))
    dolu = istek(
        ["A。B。", "{0} C."],
        ph=("{0}",),
        glossary_hits=(TermHit("A", "X", 0, 1, segment_index=0, note="zorunlu"), TermHit("C", "Y", 4, 5, segment_index=1)),
        tm_examples=(Pair("A。", "Z。", 1.0), Pair("B。", "W。", 0.9)),
        style_profile="resmi",
        image_crops=(np.zeros((4, 4, 3), dtype=np.uint8),),
    )
    r1 = sag(tmp_path, f1).translate(duz)
    r2 = sag(tmp_path, f2).translate(dolu)
    assert r1.translations == r2.translations
    assert f1.motor.calls == f2.motor.calls
    assert f1.params == f2.params


def test_a4_ast_sozluk_tm_stil_gorsel_okunmuyor() -> None:
    agac = ast.parse(Path(local_nmt.__file__).read_text(encoding="utf-8"))
    nitelikler = {n.attr for n in ast.walk(agac) if isinstance(n, ast.Attribute)}
    dizeler = {n.value for n in ast.walk(agac) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    for alan in ("glossary_hits", "tm_examples", "style_profile", "image_crops"):
        assert alan not in nitelikler
        # docstring dışı dize sabiti olarak da geçmez (getattr kaçağı) — docstringler uzun metin, tam eşleşme aranır
        assert alan not in dizeler


# ===========================================================================
# A6 — sayısal / tip (K8, K9)
# ===========================================================================


def test_a6_latency_ms_type_float_ve_negatif_degil(tmp_path: Path) -> None:
    p = sag(tmp_path, Fabrika())
    for rq in (istek(["A。"]), istek([]), istek(["。。。"]), istek(["A。B。", "C."])):
        r = p.translate(rq)
        assert type(r.latency_ms) is float and r.latency_ms >= 0.0


@pytest.mark.parametrize("threads", [np.int64(8), np.int32(4), np.uint8(2), 1, 8])
def test_a6_threads_integral_duz_int_olarak_gecer(tmp_path: Path, threads: Any) -> None:
    f = Fabrika()
    p = sag(tmp_path, f, threads=threads)
    p.translate(istek(["A。"]))
    assert type(p.threads) is int and p.threads == int(threads)
    assert type(f.params[0]["intra_threads"]) is int and f.params[0]["intra_threads"] == int(threads)
    assert f.params[0]["inter_threads"] == 1


@pytest.mark.parametrize("threads", [True, False, 8.0, np.float64(8.0), np.float32(4.0), np.bool_(True), "8", 4.5, [8], np.array(8)])
def test_a6_threads_tam_sayi_olmayan_typeerror(tmp_path: Path, threads: Any) -> None:
    with pytest.raises(TypeError):
        sag(tmp_path, Fabrika(), threads=threads)


@pytest.mark.parametrize("threads", [0, -1, np.int64(0), np.int64(9999), 2**63, -(2**63)])
def test_a6_threads_aralik_disi_valueerror(tmp_path: Path, threads: Any) -> None:
    with pytest.raises(ValueError):
        sag(tmp_path, Fabrika(), threads=threads)


@pytest.mark.parametrize("beam", [0, -1, np.int64(0), np.int32(-5)])
def test_a6_beam_size_sifir_negatif_valueerror(tmp_path: Path, beam: Any) -> None:
    with pytest.raises(ValueError):
        sag(tmp_path, Fabrika(), beam_size=beam)


@pytest.mark.parametrize("beam", [True, 4.0, np.float64(4.0), "4", None])
def test_a6_beam_size_tam_sayi_olmayan_typeerror(tmp_path: Path, beam: Any) -> None:
    with pytest.raises(TypeError):
        sag(tmp_path, Fabrika(), beam_size=beam)


@pytest.mark.parametrize("beam", [np.int32(2), np.int64(4), 1, 7])
def test_a6_beam_size_duz_int_olarak_motora_gider(tmp_path: Path, beam: Any) -> None:
    f = Fabrika()
    sag(tmp_path, f, beam_size=beam).translate(istek(["A。"]))
    assert type(f.motor.calls[0]["beam_size"]) is int and f.motor.calls[0]["beam_size"] == int(beam)
    assert f.motor.calls[0]["max_decoding_length"] == 256


@pytest.mark.parametrize("rp", [float("nan"), float("inf"), float("-inf"), 0.99, 0.0, -1.0, np.float64("nan"), np.float32(0.5)])
def test_a6_repetition_penalty_nan_inf_ve_birden_kucuk_valueerror(tmp_path: Path, rp: Any) -> None:
    with pytest.raises(ValueError):
        sag(tmp_path, Fabrika(), repetition_penalty=rp)


@pytest.mark.parametrize("rp", [True, False, "1.2", None, [1.2], complex(1.2, 0)])
def test_a6_repetition_penalty_sayi_olmayan_typeerror(tmp_path: Path, rp: Any) -> None:
    with pytest.raises(TypeError):
        sag(tmp_path, Fabrika(), repetition_penalty=rp)


@pytest.mark.parametrize("rp", [1, 1.0, np.float64(1.0), np.int64(1)])
def test_a6_repetition_penalty_bir_hic_gecilmez(tmp_path: Path, rp: Any) -> None:
    f = Fabrika()
    sag(tmp_path, f, repetition_penalty=rp).translate(istek(["A。"]))
    assert "repetition_penalty" not in f.motor.calls[0]["kw"]


@pytest.mark.parametrize("rp", [1.2, 2, np.float32(1.5), np.float64(1.1)])
def test_a6_repetition_penalty_birden_buyuk_float_olarak_gider(tmp_path: Path, rp: Any) -> None:
    f = Fabrika()
    sag(tmp_path, f, repetition_penalty=rp).translate(istek(["A。"]))
    kw = f.motor.calls[0]["kw"]
    assert type(kw["repetition_penalty"]) is float and kw["repetition_penalty"] == pytest.approx(float(rp), rel=1e-6)


def test_a6_yapim_hatasi_fabrikaya_ve_dosya_sistemine_dokunmaz(tmp_path: Path) -> None:
    f = Fabrika()
    for ek in (dict(threads=0), dict(beam_size=0), dict(repetition_penalty=0.5), dict(threads=True)):
        with pytest.raises((TypeError, ValueError)):
            LocalNmtProvider(model_dir=tmp_path / "yok", motor_fabrikasi=f, **ek)  # type: ignore[arg-type]
    assert f.calls == 0


# ===========================================================================
# AM — mutant pozitif kontrolleri (§4.6/10): ölçüler gerçekten ateşliyor mu?
# monkeypatch ile modül sabitleri/fonksiyonları değiştirilir; yukarıdaki ölçü
# fonksiyonları AYNEN çağrılır ve AssertionError/ihlal beklenir.
# ===========================================================================


def _y1_olcusu(tmp_path: Path) -> None:
    f = Fabrika()
    sag(tmp_path, f).translate(istek([" ".join(KR)], kaynak="kor_Hang"))
    assert f.motor.parcalar() == list(KR)


def _y2_olcusu(tmp_path: Path) -> None:
    f = Fabrika(Motor(cevir=isaretle))
    r = sag(tmp_path, f).translate(istek(["A。？", "。。。", "？", "   ", "「A。」"]))
    assert f.motor.parcalar() == ["A。？", "「A。」"]
    assert r.translations == ("T(A。？)", "。。。", "？", "   ", "T(「A。」)")


def test_am1_y1_olcusu_ascii_nokta_terminatorden_cikinca_duser(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _y1_olcusu(tmp_path)  # sağlam kodda geçer
    for kume in ("!?。！？", "。！？"):  # M1: ASCII nokta yok; M1': v1 kuralı (yalnız CJK)
        desen = re.compile(
            f"[^{re.escape(kume)}]*[{re.escape(kume)}]+(?:\\s*[{re.escape(local_nmt._KAPANIS_ISARETLERI)}]+)*"
            f"|[^{re.escape(kume)}]+\\Z"
        )
        monkeypatch.setattr(local_nmt, "_CUMLE_DESENI", desen)
        with pytest.raises(AssertionError):
            _y1_olcusu(tmp_path)
        with pytest.raises(AssertionError):  # tablo ölçüsü de düşer
            test_a1_bolme_tablosu_parca_giden_kayipsiz(" ".join(KR), list(KR), 2)


def test_am2_y2_olcusu_suzgec_kalkinca_duser(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _y2_olcusu(tmp_path)
    monkeypatch.setattr(local_nmt, "modele_gider", lambda p: True)  # M2: süzgeç yok
    with pytest.raises(AssertionError):
        _y2_olcusu(tmp_path)
    monkeypatch.setattr(local_nmt, "modele_gider", lambda p: any(ch.isalpha() for ch in p))  # M2': rakam sayılmaz
    with pytest.raises(AssertionError):
        test_a1_saglayici_uzerinden_giden_sayi_ve_cikti_bilesimi(tmp_path, "①.", ["①."], 1)


def test_am3_k2_ensure_aligned_cagrilmazsa_davranissal_olcu_duser(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Mutant: `translate` `ensure_aligned`ı hiç çağırmıyor → kayıt edici ölçü boş kalır → düşer (AST değil davranış)."""
    monkeypatch.setattr(local_nmt.LocalNmtProvider, "translate", _translate_ensure_alignedsiz)
    with pytest.raises(AssertionError):
        test_a2_ensure_aligned_davranissal_olarak_cagriliyor(tmp_path, monkeypatch)


def _translate_ensure_alignedsiz(self: LocalNmtProvider, request: TranslationRequest) -> TranslationResult:
    """Mutant gövde: hizalı ama `ensure_aligned` çağrısı YOK (yalnız AM3 için)."""
    return TranslationResult(translations=tuple("t" for _ in request.segments), provider_id=KIMLIK, latency_ms=0.0)


def test_am4_k2_cumle_sayimi_kalkinca_fazla_hipotez_sessiz_gecer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Sayım mutantı: `_hipotez_tokenleri` sayıyı denetlemezse 3 hipotez / 2 cümle SESSİZ geçer; A2 ölçüsü düşer."""
    orijinal = local_nmt._hipotez_tokenleri

    def sayimsiz(cikti: Any, beklenen: int, hedef: str) -> list[list[str]]:
        return orijinal(cikti, len(cikti), hedef)

    monkeypatch.setattr(local_nmt, "_hipotez_tokenleri", sayimsiz)
    f = Fabrika(Motor(cikti=_n_hip(3)))
    r = sag(tmp_path, f).translate(istek(["A。", "。。。", "B。"]))  # mutantta istisna YOK — `ensure_aligned` de görmez
    assert len(r.translations) == 3
    with pytest.raises(pytest.fail.Exception):
        test_a2_cumle_sayisi_tutmayan_hipotez_contractviolation(tmp_path, ["A。", "。。。", "B。"], 3)


def test_am5_k4_harf_duyarsizlik_kalkinca_duser(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    orijinal = local_nmt.kaynak_dili_coz

    def duyarli(kod: object) -> Any:
        if isinstance(kod, str) and kod != kod.lower():
            raise ProviderUnavailable("mutant: büyük harf reddi")
        return orijinal(kod)

    monkeypatch.setattr(local_nmt, "kaynak_dili_coz", duyarli)
    with pytest.raises((AssertionError, ProviderUnavailable)):
        test_a3_uc_bicim_bes_harf_hali_ilk_token_son_prefix_her_satirda(tmp_path, "jpn_Jpan", 1)


def test_am6_k5_sayim_yerine_in_kullanilinca_duser(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def in_ile(cikti: str, kaynak: str, yts: Sequence[str]) -> str:
        eksik = [yt for yt in dict.fromkeys(yts) if yt and yt not in cikti]
        return " ".join([cikti, *eksik]) if eksik else cikti

    monkeypatch.setattr(local_nmt, "_yer_tutuculari_onar", in_ile)
    with pytest.raises(AssertionError):
        test_a4_kaynakta_iki_ciktida_bir_bir_eklenir(tmp_path)


def test_am7_k5_onarim_kosulsuz_eklerse_dokunulmazlik_duser(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(local_nmt, "_yer_tutuculari_onar", lambda c, k, yts: " ".join([c, *yts]) if yts else c)
    with pytest.raises(AssertionError):
        test_a4_ciktida_uc_kaynakta_bir_ekleme_yok(tmp_path)


def test_am8_k3_kapanis_isaretleri_kalkinca_tablo_duser(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Mutant: kapanış işaretleri cümleye dahil edilmez → `「A。」B。` 3 parça, `」` tek başına geçer → bölme tablosu düşer."""
    t = local_nmt._TERMINATORLER
    desen = re.compile(f"[^{re.escape(t)}]*[{re.escape(t)}]+|[^{re.escape(t)}]+\\Z")
    monkeypatch.setattr(local_nmt, "_CUMLE_DESENI", desen)
    assert cumlelere_bol("「A。」B。") == ["「A。", "」B。"]  # mutant davranışı
    with pytest.raises(AssertionError):
        test_a1_bolme_tablosu_parca_giden_kayipsiz("「A。」B。", ["「A。」", "B。"], 2)
    with pytest.raises(AssertionError):
        test_a1_bolme_tablosu_parca_giden_kayipsiz("A. )", ["A. )"], 1)


def test_am9_a6_latency_int_olsaydi_duser(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    orijinal = local_nmt.LocalNmtProvider.translate

    def int_latency(self: LocalNmtProvider, rq: TranslationRequest) -> TranslationResult:
        r = orijinal(self, rq)
        return dataclasses.replace(r, latency_ms=int(r.latency_ms))  # type: ignore[arg-type]

    monkeypatch.setattr(local_nmt.LocalNmtProvider, "translate", int_latency)
    with pytest.raises(AssertionError):
        test_a6_latency_ms_type_float_ve_negatif_degil(tmp_path)


def test_am10_kontrol_esdeger_mutant_yakalanmaz(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Davranış-eşdeğer değişiklik (hata mesajı metni) ölçüleri DÜŞÜRMEMELİ — ölçüler mesaja değil davranışa bağlı."""
    orijinal = local_nmt.kaynak_dili_coz

    def farkli_mesaj(kod: object) -> Any:
        try:
            return orijinal(kod)
        except ProviderUnavailable as e:
            raise ProviderUnavailable("başka bir mesaj") from e

    monkeypatch.setattr(local_nmt, "kaynak_dili_coz", farkli_mesaj)
    test_a3_tablo_disi_kaynak_provider_unavailable_fabrika_sifir(tmp_path, "xx")
    test_a3_uc_bicim_bes_harf_hali_ilk_token_son_prefix_her_satirda(tmp_path, "kor_Hang", 2)
