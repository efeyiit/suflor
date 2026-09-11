"""TESTER-B mutant kiti (T-007, mercek B: test kalitesi) -- bes kapinin AYIRT ETME GUCU.

Soru: "210 birim testi + real_check + mypy + kapsam + tam takim, saglayiciyi
gercekten olcuyor mu?" Tek yontem: saglayiciyi bilerek bozup HANGI KAPININ
yakaladigini saymak. Hicbir kapinin yakalamadigi, urunu bozan ve uygulamada
ERISILEBILIR bir mutant, o degismezin olcusunun BOS oldugunu kanitlar.
Davranis-esdeger KONTROL mutantlari (C0x) kacmak ZORUNDADIR; yakalanirlarsa
olcu yanlis pozitif veriyordur (sefe bulgu).

`src/`, `tests/`, `real_check.py`, `conftest.py` DEGISTIRILMEZ: depo, scratchpad
altindaki bir AYNA AGACINA kopyalanir (models/ dahil -- real_check kapisi
gercek modelle kosar); mutasyon orada yapilir, her mutanttan sonra dosya
depodan geri yazilir.

Kosum:
    TESTER_B_SCRATCH=<dizin> python .agents/tasks/T-007/tester_B/mutant_kiti.py [mutant_id ...]
    TB_DRY=1 ...   -> yalniz yama hedeflerini dogrular + py_compile, kapi kosmaz

Kapilar paketin bes kabul komutudur (packet.md `acceptance`); pytest'e yalniz
`-p no:cacheprovider` (ayna agacina cache yazmasin) ve `-rfE` (dusen test adlari
kanita gecsin) eklenmistir -- gecti/kaldi anlamini degistirmez. real_check
YALNIZ ASCII bastigi icin PYTHONIOENCODING verilmez: kapilar cp1254 konsol
kosullarinda kosar (T-006 S1 dersi).
"""
from __future__ import annotations

import os
import py_compile
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

DEPO = Path(__file__).resolve().parents[4]
SCRATCH = Path(os.environ.get("TESTER_B_SCRATCH", tempfile.gettempdir()))
KOK = SCRATCH / "t007_tester_B_mutroot"
DRY = os.environ.get("TB_DRY", "") == "1"

MOTOR = "src/translate/local_nmt.py"
GERI_ALINAN = (MOTOR,)

AYNALANAN_DIZINLER = ("src", "tests", ".agents/tasks/T-007/fixtures")
AYNALANAN_DOSYALAR = (".agents/tasks/T-004/olcu_kiti.py", ".agents/tasks/T-007/real_check.py")
MODEL_DIZINI = "models/nllb-200-distilled-600M-ct2-int8"
MODEL_DOSYALARI = ("model.bin", "sentencepiece.bpe.model", "shared_vocabulary.txt", "config.json")

KAPILAR: list[tuple[str, list[str]]] = [
    ("G1-mypy", [sys.executable, "-m", "mypy", "--strict", "--explicit-package-bases", MOTOR]),
    ("G2-birim", [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-rfE",
                  "tests/unit/translate/test_local_nmt.py"]),
    ("G3-real", [sys.executable, ".agents/tasks/T-007/real_check.py"]),
    ("G4-kapsam", [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-rfE",
                   "tests/unit/translate/test_local_nmt.py", "--cov=src.translate.local_nmt",
                   "--cov-fail-under=90", "--cov-report=term-missing"]),
    ("G5-tum", [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-rfE", "tests"]),
]


@dataclass
class Mutant:
    mid: str
    yamalar: list[tuple[str, str]]
    aciklama: str
    hedef: str
    beklenen: str  # kosumdan ONCE yazilan tahmin: hangi kapi yakalar
    kontrol: bool = False
    urun_etkisi: str = ""


def _y(eski: str, yeni: str) -> tuple[str, str]:
    return (eski, yeni)


# --- yama hedefleri (kaynaktan birebir; tekillik kurulumda dogrulanir) --------
TERM = '_TERMINATORLER: Final = ".!?。！？"\n'
KAPANIS = '_KAPANIS_ISARETLERI: Final = "」』）)\\"\'”’»"\n'
ISALNUM = "    return any(ch.isalnum() for ch in parca)\n"
SAYI_DENETIMI = (
    "    if len(cikti) != beklenen:\n"
    "        raise ContractViolation(\n"
    '            f"motor gonderilen cumle sayisi kadar hipotez dondurmedi: cumle={beklenen}, "\n'
    '            f"hipotez={len(cikti)} (provider={_SAGLAYICI_KIMLIGI!r})"\n'
    "        )\n"
)
ENSURE = "        ensure_aligned(request, sonuc)\n"
JA_SATIRI = '    "jpn_jpan": NmtDili.JAPAN, "ja": NmtDili.JAPAN, "japan": NmtDili.JAPAN,\n'
KO_SATIRI = '    "kor_hang": NmtDili.KOREAN, "ko": NmtDili.KOREAN, "korean": NmtDili.KOREAN,\n'
ZH_SATIRI = '    "zho_hans": NmtDili.CHINESE, "zh": NmtDili.CHINESE, "chinese": NmtDili.CHINESE,\n'
EN_ENUM = '    ENGLISH = "eng_Latn"\n'
HEDEF_PREFIX = "                target_prefix=[[hedef.value]] * len(tokenler),\n"
KUCUK_HARF = "    dil = _KAYNAK_KODLARI.get(kod.lower())\n"
TOKEN_DIZISI = "            tokenler = [[kaynak.value, *encode(p), _SON_BELIRTECI] for p in parcalar]\n"
YT_SAYIM = "        ekler.extend([yt] * (gereken - cikti.count(yt)))\n"
YT_BIRLESTIR = '    return " ".join([cikti, *ekler]) if cikti else " ".join(ekler)\n'
YT_DEDUP = (
    "        if not yt or yt in islenen:\n"
    "            continue\n"
    "        islenen.add(yt)\n"
)
YT_ONARIM_CAGRI = "            sonuclar.append(_yer_tutuculari_onar(cikti, segment.text, segment.placeholders))\n"
DOSYA_MODEL = '    "model.bin",\n'
DOSYA_SPM = '    "sentencepiece.bpe.model",\n'
DOSYA_VOCAB = '    "shared_vocabulary.txt",\n'
DOSYA_CFG = '    "config.json",\n'
MME_RAISE = "            raise ModelMissingError(f\"model dosyasi yok: {', '.join(eksik)} (dizin: {self._model_dir})\")\n"
FNF = (
    "        except FileNotFoundError as e:\n"
    '            raise ModelMissingError("model dosyasi kurulum sirasinda bulunamadi") from e\n'
)
KURULUM_TE = (
    "            motor, encode, decode = self._fabrika(self._model_dir, self.motor_parametreleri())\n"
    "        except TranslatorError:\n"
    "            raise\n"
)
CEVIRI_HATA = '            raise ProviderUnavailable(f"ceviri basarisiz: {type(e).__name__}") from e\n'
SP_PROTO = '    sp = sentencepiece.SentencePieceProcessor(model_proto=(model_dir / "sentencepiece.bpe.model").read_bytes())\n'
CT2_RESOLVE = "    motor = ctranslate2.Translator(str(model_dir.resolve()), **params)\n"
INTER = '            "inter_threads": 1,\n'
RP_KOSUL = (
    "        if self._repetition_penalty != 1.0:\n"
    '            ek["repetition_penalty"] = self._repetition_penalty  # K8: 1.0 iken HIC gecilmez\n'
)
MDL_SABIT = "_MAKS_COZUM_UZUNLUGU: Final = 256\n"
MDL_CAGRI = "                max_decoding_length=_MAKS_COZUM_UZUNLUGU,\n"
MDL_PROTO = "        max_decoding_length: int,\n"
ARALIK = "    if not 1 <= n <= cekirdek:\n"
NONE_DAL = "        return min(_VARSAYILAN_PARCACIK, cekirdek)\n"
LATENCY = "            latency_ms=(time.perf_counter() - t0 - kurulum_s) * 1000.0,\n"
KAPALI = (
    "        if self._kapali:\n"
    '            raise ProviderUnavailable("saglayici kapatildi; close() sonrasi translate cagrilamaz")\n'
)
CLOSE_GOVDE = (
    "        self._motor = None\n"
    "        self._encode = None\n"
    "        self._decode = None\n"
    "        self._kapali = True\n"
)
TEK_ORNEK = (
    "        if self._motor is not None and self._encode is not None and self._decode is not None:\n"
    "            return self._motor, self._encode, self._decode\n"
)
METIN_DONUS = (
    '            raise ProviderUnavailable("decode str dondurmedi")\n'
    "        return metinler\n"
)
IMPORT_RE = "import re\n"
INIT_SON = "        self._kapali = False\n"
HIPOTEZ_MSG = '            f"hipotez={len(cikti)} (provider={_SAGLAYICI_KIMLIGI!r})"\n'
HIPOTEZ_YOK_MSG = '            raise ProviderUnavailable(f"motor ciktisinda hipotez listesi yok ya da bos: {type(nesne).__name__}")\n'
BELIRTEC_AT = "        if tokenler and tokenler[0] == hedef_kodu:\n"
STRIP_PARCA = "    return [p.strip() for p in parcalar if p.strip()]\n"
BIRLESTIR = '                cikti = " ".join(ceviriler[idx] if idx >= 0 else parca for parca, idx in plan)\n'
AYNEN = "                cikti = segment.text  # K3 (Y2): hicbir parcasi modele gitmeyen segment AYNEN\n"
DETECTED = "            detected_lang=kaynak.value,\n"


def _term_eksik(mid: str, isaret: str, ad: str, etki: str) -> Mutant:
    return Mutant(
        mid, [_y(TERM, f'_TERMINATORLER: Final = "{".!?。！？".replace(isaret, "")}"\n')],
        f"K3 (Y1): terminator kumesinden `{ad}` ({isaret!r}) EKSIK", f"K3 terminator {ad}",
        "G2 G4 G5" + (" G3" if isaret in ".。" else ""), urun_etkisi=etki,
    )


MUTANTLAR: list[Mutant] = [
    # ---- K3: bolme / suzgec -------------------------------------------------------
    _term_eksik("K3-01", ".", "ASCII nokta", "KR/EN paragraf bolunmez -> C6 kaynasmasi, 2. cumle kaybi (real_check #4)"),
    _term_eksik("K3-02", "!", "ASCII unlem", "EN/KR `A! B.` tek parca -> kaynasma"),
    _term_eksik("K3-03", "?", "ASCII soru", "EN/KR `A? B.` tek parca -> kaynasma"),
    _term_eksik("K3-04", "。", "CJK nokta", "JP paragraf bolunmez -> C8 kaynasmasi (real_check #3)"),
    _term_eksik("K3-05", "！", "CJK unlem", "JP `A！B。` tek parca"),
    _term_eksik("K3-06", "？", "CJK soru", "JP `A？B。` tek parca"),
    Mutant("K3-07", [_y(KAPANIS, '_KAPANIS_ISARETLERI: Final = "』）)\\"\'”’»"\n')],
           "K3: kapanis kumesinden `」` (U+300D) EKSIK -- JP tirnak kapanisi cumleye DAHIL EDILMEZ, sonraki parcanin basina yapisir",
           "K3 kapanis", "G2 G4 G5",
           urun_etkisi="`「A。」B。` -> `「A。`, `」B。`: `」` yanlis cumleye gider. (Ilk surum bos kume idi -> regex `[]` re.error: kit hatasi, duzeltildi; ilk kosum B1-mutant-kiti.txt'te)"),
    Mutant("K3-08", [_y(ISALNUM, "    return any(ch.isalpha() for ch in parca)\n")],
           "K3 (Y2): suzgec `isalnum` yerine `isalpha` -- rakam-only parca (`42`, `3.`, `5`) modele GITMEZ, aynen gecer",
           "K3 suzgec rakam", "G2 G4 G5", urun_etkisi="OCR'dan gelen `42` gibi sayisal satirlar cevrilmez (zararsiz ama sozlesme disi)"),
    Mutant("K3-09", [_y(STRIP_PARCA, "    return [p for p in parcalar if p.strip()]\n")],
           "K3: parcalar KIRPILMIYOR (` B.` bosluklu gider)", "K3 kirpma", "G2 G4 G5",
           urun_etkisi="modele bosluk onekli parca; sentencepiece `▁` fazladan"),
    Mutant("K3-10", [_y(BIRLESTIR, '                cikti = "".join(ceviriler[idx] if idx >= 0 else parca for parca, idx in plan)\n')],
           "K3: cumleler `\" \"` yerine `\"\"` ile birlestiriliyor", "K3 birlestirme", "G2 G4 G5",
           urun_etkisi="Turkce ciktida cumleler bitisik"),
    Mutant("K3-11", [_y(AYNEN, '                cikti = ""\n')],
           "K3 (Y2): hicbir parcasi modele gitmeyen segment AYNEN yerine BOS donuyor", "K3 gecis segment", "G2 G4 G5 G3",
           urun_etkisi="`。。。`/bos satir ekranda silinir (real_check #4b)"),
    # ---- K2: hizalama --------------------------------------------------------------
    Mutant("K2-01", [_y(SAYI_DENETIMI, "")],
           "K2 (O3): CUMLE SAYISI denetimi kaldirildi (fazla hipotez sessiz, eksik hipotez IndexError)",
           "K2 cumle sayimi", "G2 G4 G5", urun_etkisi="motor kaymasi ContractViolation yerine sessiz/ham IndexError"),
    Mutant("K2-02", [_y(ENSURE, "")],
           "K2: `ensure_aligned` cagrisi atlanmis", "K2 ensure_aligned", "G2 G4 G5 (yalniz AST)",
           urun_etkisi="bu uygulamada davranis ayni (hizalama yapisal) -- olcu MEKANIZMA (AST)"),
    Mutant("K2-03", [_y(DETECTED, "            detected_lang=None,\n")],
           "K2: `detected_lang` doldurulmuyor", "K2 sonuc alanlari", "G2 G4 G5",
           urun_etkisi="ust katman kullanilan dil kodunu goremez (kucuk)"),
    # ---- K4: dil tablosu -- dort dilde AYRI ---------------------------------------
    Mutant("K4-01", [_y(JA_SATIRI, '    "jpn_jpan": NmtDili.JAPAN, "ja": NmtDili.CHINESE, "japan": NmtDili.JAPAN,\n')],
           "K4 JAPAN: ISO `ja` -> zho_Hans (yalniz bir bicim yanlis)", "K4 JAPAN", "G2 G4 G5",
           urun_etkisi="`ja` ile gelen istek Cince belirteciyle gider; CT2 hata vermez (KRT O6), kalite sessizce duser"),
    Mutant("K4-02", [_y(KO_SATIRI, '    "kor_hang": NmtDili.JAPAN, "ko": NmtDili.KOREAN, "korean": NmtDili.KOREAN,\n')],
           "K4 KOREAN: NLLB `kor_hang` -> jpn_Jpan", "K4 KOREAN", "G2 G4 G5 G3",
           urun_etkisi="real_check #4 `kor_Hang` ile kosar -> KR metin JP belirteciyle"),
    Mutant("K4-03", [_y(ZH_SATIRI, '    "zho_hans": NmtDili.CHINESE, "zh": NmtDili.CHINESE, "chinese": NmtDili.KOREAN,\n')],
           "K4 CHINESE: OcrLanguage `chinese` -> kor_Hang", "K4 CHINESE", "G2 G4 G5",
           urun_etkisi="T-006 uretici degeriyle gelen ZH istegi KR belirteciyle gider"),
    Mutant("K4-04", [_y(EN_ENUM, '    ENGLISH = "en_Latn"\n')],
           "K4 ENGLISH: NLLB kodu yanlis yazilmis (`en_Latn`)", "K4 ENGLISH", "G2 G4 G5 G3",
           urun_etkisi="`eng_Latn` anahtari tabloda yok -> ProviderUnavailable; `en`/`english` yanlis belirtecle gider"),
    Mutant("K4-05", [_y(HEDEF_PREFIX, "                target_prefix=[[NmtDili.ENGLISH.value]] * len(tokenler),\n")],
           "K4: hedef `tur_Latn` yerine `eng_Latn` (target_prefix)", "K4 hedef", "G2 G4 G5 G3",
           urun_etkisi="ceviri Ingilizce cikar; real_check #2 'bekliyor' yok"),
    Mutant("K4-06", [_y(KUCUK_HARF, "    dil = _KAYNAK_KODLARI.get(kod)\n")],
           "K4: buyuk/kucuk harf duyarsizligi kaldirildi (`jpn_Jpan` bile reddedilir)", "K4 harf", "G2 G4 G5 G3",
           urun_etkisi="tablo kucuk harfli -> `jpn_Jpan`, `eng_Latn` ProviderUnavailable"),
    Mutant("K4-07", [_y(TOKEN_DIZISI, "            tokenler = [[*encode(p), _SON_BELIRTECI] for p in parcalar]\n")],
           "K4: kaynak dil belirteci token dizisinin basina KONMUYOR", "K4 belirtec", "G2 G4 G5",
           urun_etkisi="NLLB kaynak dili bilmeden cevirir; kalite sessizce duser"),
    # ---- K5: yer tutucu -------------------------------------------------------------
    Mutant("K5-01", [_y(YT_SAYIM, "        if yt not in cikti:\n            ekler.append(yt)\n")],
           "K5 (O1): sayim yerine `in` (ikinci `%s` gecisi kaybolur)", "K5 sayim", "G2 G4 G5",
           urun_etkisi="normalizer `(\"%s\",\"%s\")` verir; tek gecis tatmin eder, biri kaybolur"),
    Mutant("K5-02", [_y(YT_BIRLESTIR, '    return " ".join([*ekler, cikti]) if cikti else " ".join(ekler)\n')],
           "K5: onarim SONA degil BASA", "K5 konum", "G2 G4 G5",
           urun_etkisi="paket 'sona eklenir' der; ust katman sonu bekler"),
    Mutant("K5-03", [_y(YT_DEDUP, "        if not yt:\n            continue\n")],
           "K5: cogaltilmis yer tutucu tekillestirmesi SILINDI (`(\"%s\",\"%s\")` iki kez sayilir -> fazla ek)",
           "K5 dedup", "G2 G4 G5", urun_etkisi="ciktida fazladan `%s` kopyalari"),
    Mutant("K5-04", [_y(YT_ONARIM_CAGRI, "            sonuclar.append(cikti)\n")],
           "K5: onarim tamamen kaldirildi (sefin M4 ile ayni sinif; regresyon cipasi)", "K5 onarim", "G2 G4 G5 G3",
           urun_etkisi="JP `{0}` kaybolur (real_check #5)"),
    # ---- K6: hata siniflandirmasi -- dort dosya AYRI ---------------------------------
    Mutant("K6-01", [_y(DOSYA_MODEL, "")], "K6 (a): `model.bin` denetlenmiyor", "K6 model.bin", "G2 G4 G5",
           urun_etkisi="eksik model.bin CT2 RuntimeError -> ProviderUnavailable (indirme tetiklenmez)"),
    Mutant("K6-02", [_y(DOSYA_SPM, "")], "K6 (a): `sentencepiece.bpe.model` denetlenmiyor", "K6 spm", "G2 G4 G5",
           urun_etkisi="read_bytes FileNotFoundError -> (yalniz bu uygulamada) ModelMissingError; paket lafzinda ProviderUnavailable"),
    Mutant("K6-03", [_y(DOSYA_VOCAB, "")], "K6 (a): `shared_vocabulary.txt` denetlenmiyor (O4)", "K6 vocab", "G2 G4 G5",
           urun_etkisi="CT2 'Cannot load the target vocabulary' -> ProviderUnavailable"),
    Mutant("K6-04", [_y(DOSYA_CFG, "")], "K6 (a): `config.json` denetlenmiyor (O4)", "K6 config", "G2 G4 G5",
           urun_etkisi="CT2 json hatasi -> ProviderUnavailable"),
    Mutant("K6-05", [_y(MME_RAISE, MME_RAISE.replace("ModelMissingError", "ProviderUnavailable"))],
           "K6 (a): eksik dosyada `ModelMissingError` yerine `ProviderUnavailable`", "K6 sinif", "G2 G4 G5 G3",
           urun_etkisi="tasarim 5.6 indirme/preflight dali tetiklenmez (real_check #8)"),
    Mutant("K6-06", [_y(FNF, "")],
           "K6 (b) PAKET LAFZI: fabrikanin FileNotFoundError'u ModelMissingError'a DEGIL ProviderUnavailable'a (paket: 'kurulum istisnasi -> ProviderUnavailable')",
           "K6 (b) FNF eslemesi", "G2 G4 G5 (test paketten sert)",
           urun_etkisi="paket lafziyla UYUMLU; teslim docstring'i ek esleme belgeliyor -> testler paketin otesini kilitliyor (bilgi)"),
    Mutant("K6-07", [_y(CEVIRI_HATA, CEVIRI_HATA.replace(" from e\n", " from None\n"))],
           "K6 (b): ceviri hatasinda `__cause__` dusuruldu", "K6 __cause__", "G2 G4 G5",
           urun_etkisi="kok neden kaybolur; tani zorlasir"),
    Mutant("K6-08", [_y(KURULUM_TE, KURULUM_TE.replace("        except TranslatorError:\n            raise\n", ""))],
           "K6 (b): fabrikanin `TranslatorError`'u da ProviderUnavailable'a SARILIR (ModelMissingError kaybolur)",
           "K6 oldugu gibi", "G2 G4 G5", urun_etkisi="ModelManager'in firlattigi ModelMissingError sarilir"),
    # ---- K7 -------------------------------------------------------------------------
    Mutant("K7-01", [_y(SP_PROTO, '    sp = sentencepiece.SentencePieceProcessor(model_file=str(model_dir / "sentencepiece.bpe.model"))\n')],
           "K7 (C5): `model_proto=` yerine `model_file=` (ASCII-disi yolda NOT_FOUND)", "K7 bayt", "G2 G4 G5 (AST) G3 (#7)",
           urun_etkisi="Turkce karakterli kullanici dizininde saglayici kurulamaz"),
    Mutant("K7-02", [_y(CT2_RESOLVE, "    motor = ctranslate2.Translator(str(model_dir), **params)\n")],
           "K7: CT2'ye `.resolve()` olmadan yol (goreli yol CWD'ye bagli)", "K7 mutlak", "G2 G4 G5 (yalniz AST)",
           urun_etkisi="real_check mutlak yol verir -> ayrismaz; MEKANIZMA olcusu"),
    # ---- K8 -------------------------------------------------------------------------
    Mutant("K8-01", [_y(INTER, '            "inter_threads": self._threads,\n')],
           "K8: `inter_threads` 1 degil (threads kadar)", "K8 inter", "G2 G4 G5",
           urun_etkisi="CT2 threads^2 iplik; 32 cekirdekte 64+ iplik"),
    Mutant("K8-02", [_y(RP_KOSUL, '        ek["repetition_penalty"] = self._repetition_penalty\n')],
           "K8: `repetition_penalty=1.0` iken de GECILIYOR (CT2'de ayni sonuc -- KRT D1 mekanizma)", "K8 rp 1.0", "G2 G4 G5",
           urun_etkisi="gercek CT2'de hipotezler ayni (olcum-1 [5]); olcu MEKANIZMA"),
    Mutant("K8-03", [_y(MDL_SABIT, "_MAKS_COZUM_UZUNLUGU: Final = 1024\n")],
           "K8/K9 (O2): `max_decoding_length` 256 degil 1024", "K8 mdl deger", "G2 G4 G5",
           urun_etkisi="dejenere girdide 4x uzun kuyruk (5.9 s -> daha uzun)"),
    Mutant("K8-04", [_y(MDL_CAGRI, ""), _y(MDL_PROTO, "        max_decoding_length: int = 256,\n")],
           "K8/K9 (O2): `max_decoding_length` HIC gecilmiyor (CT2 varsayilanina birakilmis)", "K8 mdl yok", "G2 G4 G5",
           urun_etkisi="CT2 varsayilani 256 -> davranis ayni; paket 'acik gecilir' der (mekanizma)"),
    Mutant("K8-05", [_y(ARALIK, "    if n < 1:\n")],
           "K8: `threads` UST sinir denetimi yok (cpu_count ustu sessiz)", "K8 ust sinir", "G2 G4 G5",
           urun_etkisi="threads=64 32 cekirdekte sessiz kabul (KRT D2)"),
    Mutant("K8-06", [_y(NONE_DAL, "        return cekirdek\n")],
           "K8: `threads=None` -> cpu_count (min(8, ...) yok)", "K8 None", "G2 G4 G5",
           urun_etkisi="32 iplik; C2 8 iplikle olculdu"),
    # ---- K9 -------------------------------------------------------------------------
    Mutant("K9-01", [_y(LATENCY, "            latency_ms=(time.perf_counter() - t0) * 1000.0,\n")],
           "K9: `latency_ms` motor KURULUMUNU iceriyor", "K9 latency", "G2 G4 G5",
           urun_etkisi="ilk kare 600+ ms gorunur; butce/istatistik yaniltir"),
    Mutant("K9-02", [_y(LATENCY, "            latency_ms=0.0,\n")],
           "K9: `latency_ms` sabit 0", "K9 latency sabit", "G2 G4 G5",
           urun_etkisi="sure olculmuyor"),
    # ---- K10 ------------------------------------------------------------------------
    Mutant("K10-01", [_y(KAPALI, "")],
           "K10: `close()` sonrasi `translate` CALISIYOR (fabrika yeniden kurulur)", "K10 kapali", "G2 G4 G5",
           urun_etkisi="kapatilmis saglayici 600 MB modeli yeniden yukler"),
    Mutant("K10-02", [_y(CLOSE_GOVDE, "        self._kapali = True\n")],
           "K10: `close()` motoru BIRAKMIYOR (referans tutulur)", "K10 close birakir", "G2 G4 G5",
           urun_etkisi="close sonrasi 700 MB calisma kumesi kalir (olcum-3'un tersi)"),
    Mutant("K10-03", [_y(TEK_ORNEK, "")],
           "K10: tek ornek YOK -- fabrika her `translate`te yeniden cagrilir", "K10 tek ornek", "G2 G4 G5",
           urun_etkisi="her karede 470 ms model yukleme"),
    Mutant("K10-04", [_y(METIN_DONUS, METIN_DONUS.replace("        return metinler\n", "        sys.stdout.write(metinler[0])\n        return metinler\n")),
                      _y(IMPORT_RE, "import re\nimport sys\n")],
           "K10: `sys.stdout.write(ceviri)` (print DEGIL)", "K10 stdout", "G2 G4 G5 (davranis + AST)",
           urun_etkisi="ceviri metni konsola; pythonw'da None.write cokusu"),
    Mutant("K10-05", [_y(METIN_DONUS, METIN_DONUS.replace("        return metinler\n", '        logging.getLogger("suflor.nmt").info("ceviri %s", metinler[0])\n        return metinler\n')),
                      _y(IMPORT_RE, "import logging\nimport re\n")],
           "K10: adli logger'a INFO ile ceviri metni (propagate acik)", "K10 logging", "G2 G4 G5",
           urun_etkisi="uygulama log dosyasina ceviri metni"),
    Mutant("K10-06", [_y(METIN_DONUS, METIN_DONUS.replace("        return metinler\n",
                      '        _lg = logging.getLogger("nllb.motor.ic")\n        _lg.propagate = False\n        _lg.setLevel(logging.INFO)\n        _lg.info("ceviri %s", metinler[0])\n        return metinler\n')),
                      _y(IMPORT_RE, "import logging\nimport re\n")],
           "K10: `propagate=False` adi bilinmeyen logger'a INFO ile ceviri metni (kok caplog GOREMEZ; Logger.handle kancasi gorur mu?)",
           "K10 logging propagate=False", "G2 G4 G5 (kanca)",
           urun_etkisi="o logger'a handler takan her yer ceviri metnini alir"),
    Mutant("K10-07", [_y(CEVIRI_HATA, '            raise ProviderUnavailable(f"ceviri basarisiz: {type(e).__name__}: {parcalar!r}") from e\n')],
           "K10/K6: hata mesajina KAYNAK metin", "K10 hata mesaji kaynak", "G2 G4 G5",
           urun_etkisi="istisna loglanir -> kaynak metin log dosyasinda"),
    Mutant("K10-08", [_y(HIPOTEZ_MSG, '            f"hipotez={len(cikti)} {cikti!r} (provider={_SAGLAYICI_KIMLIGI!r})"\n')],
           "K10/K6: sayi uyusmazligi mesajina MOTOR CIKTISI (ceviri metni) -- nobetci testi bu yolda sahte `x` hipotezi kullaniyor",
           "K10 hata mesaji ceviri", "? (nobetci sahte ciktida yok)",
           urun_etkisi="gercek CT2 sayi uyusmazligi uretmez (D2) -> erisilebilirlik dusuk; keskinlik sinifi"),
    Mutant("K10-09", [_y(HIPOTEZ_YOK_MSG, '            raise ProviderUnavailable(f"motor ciktisinda hipotez listesi yok ya da bos: {nesne!r}")\n')],
           "K10/K6: bozuk cikti mesajina motor NESNESI (repr ceviri tasiyabilir)", "K10 hata mesaji nesne", "?",
           urun_etkisi="gercek CT2 bicimi sabit -> erisilebilirlik dusuk; keskinlik sinifi"),
    # ---- K1 -------------------------------------------------------------------------
    Mutant("K1-01", [_y(IMPORT_RE, "import re\nimport ctranslate2  # noqa: F401\n")],
           "K1: modul duzeyinde `import ctranslate2`", "K1 tembel import", "G1 G2 G4 G5 (bariyer toplama aninda)",
           urun_etkisi="import 400+ ms; testler bariyere carpar"),
    # ---- KONTROL: davranis-esdeger, KACMALI ------------------------------------------
    Mutant("C01", [_y(BELIRTEC_AT, "        if len(tokenler) > 0 and tokenler[0] == hedef_kodu:\n")],
           "KONTROL: `tokenler and` -> `len(tokenler) > 0 and` (esdeger)", "-- kontrol --", ".....", kontrol=True),
    Mutant("C02", [_y(YT_SAYIM, "        for _ in range(gereken - cikti.count(yt)):\n            ekler.append(yt)\n")],
           "KONTROL: `extend([yt]*n)` -> dongu (esdeger)", "-- kontrol --", ".....", kontrol=True),
    Mutant("C03", [_y(INIT_SON, "        self._kapali: bool = False\n")],
           "KONTROL: yalniz tip ek aciklamasi", "-- kontrol --", ".....", kontrol=True),
    Mutant("C04", [_y(JA_SATIRI + KO_SATIRI, KO_SATIRI + JA_SATIRI)],
           "KONTROL: tablo satir sirasi degisti (dict; hata mesaji `sorted`)", "-- kontrol --", ".....", kontrol=True),
    Mutant("C05", [_y(YT_BIRLESTIR, '    return (cikti + " " + " ".join(ekler)) if cikti else " ".join(ekler)\n')],
           "KONTROL: join -> birlestirme operatoru (esdeger)", "-- kontrol --", ".....", kontrol=True),
    Mutant("C06", [_y(LATENCY, "            latency_ms=((time.perf_counter() - t0) - kurulum_s) * 1000.0,\n")],
           "KONTROL: parantezleme (esdeger)", "-- kontrol --", ".....", kontrol=True),
]


def _kapi_kos(argv: list[str]) -> tuple[int, str, float]:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    env.pop("PYTHONIOENCODING", None)  # cp1254 konsol kosullari (T-006 S1 dersi)
    t0 = time.perf_counter()
    r = subprocess.run(argv, cwd=str(KOK), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=env, timeout=900)
    return r.returncode, (r.stdout or "") + (r.stderr or ""), time.perf_counter() - t0


def _uygula(mut: Mutant) -> None:
    p = KOK / MOTOR
    metin = p.read_text(encoding="utf-8")
    for eski, yeni in mut.yamalar:
        n = metin.count(eski)
        if n != 1:
            raise SystemExit(f"{mut.mid}: yama hedefi {n} kez bulundu (1 olmali)\n{eski[:200]!r}")
        metin = metin.replace(eski, yeni, 1)
    p.write_text(metin, encoding="utf-8")


def _geri_al() -> None:
    for rel in GERI_ALINAN:
        shutil.copyfile(DEPO / rel, KOK / rel)


def _ayna_kur() -> None:
    if KOK.exists():
        shutil.rmtree(KOK, ignore_errors=True)
    yoksay = shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache", ".mypy_cache")
    for ad in AYNALANAN_DIZINLER:
        shutil.copytree(DEPO / ad, KOK / ad, ignore=yoksay)
    for ad in AYNALANAN_DOSYALAR:
        (KOK / ad).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(DEPO / ad, KOK / ad)
    (KOK / MODEL_DIZINI).mkdir(parents=True, exist_ok=True)
    for ad in MODEL_DOSYALARI:  # real_check kapisi gercek modelle kosar (~630 MB, ayni surucu)
        shutil.copyfile(DEPO / MODEL_DIZINI / ad, KOK / MODEL_DIZINI / ad)


def _dusen_testler(ozet: str) -> list[str]:
    return [ln.strip()[:150] for ln in ozet.splitlines() if ln.startswith(("FAILED", "ERROR"))]


def _ilk_hata(ad: str, ozet: str) -> str:
    for ln in ozet.splitlines():
        if any(k in ln for k in ("IHLAL", "error:", "failed", "Required test coverage", "RuntimeError", "Error")):
            return f"{ad}: {ln.strip()[:140]}"
    return f"{ad}: (ilk hata satiri bulunamadi; exit != 0)"


def main() -> None:
    secilen = set(sys.argv[1:])
    _ayna_kur()
    print(f"ayna agaci: {KOK}   (depo YAZILMAZ; models/ 4 dosya kopyalandi)")
    print("kapilar PYTHONIOENCODING'siz (cp1254) kosar; real_check yalniz ASCII basar")
    print()
    if DRY:
        print("KURU KOSUM: yama hedefleri + py_compile")
        for mut in MUTANTLAR:
            if secilen and mut.mid not in secilen:
                continue
            _uygula(mut)
            try:
                py_compile.compile(str(KOK / MOTOR), doraise=True)
                print(f"  {mut.mid:7s} yama OK, derlendi")
            finally:
                _geri_al()
        return

    basliklar = [ad for ad, _ in KAPILAR]
    print("TABAN (mutasyonsuz ayna):")
    taban_ok = True
    for ad, argv in KAPILAR:
        rc, ozet, sn = _kapi_kos(argv)
        son = [ln for ln in ozet.strip().splitlines() if ln.strip()][-1:] or [""]
        print(f"  {ad:10s} exit={rc}  {sn:6.1f}s  {son[0][:100]}")
        taban_ok = taban_ok and rc == 0
    if not taban_ok:
        raise SystemExit("TABAN GECMEDI -- ayna agaci bozuk, mutant tablosu uretilmedi")
    print()

    satirlar: list[str] = []
    kacan: list[str] = []
    yakalanan_kontrol: list[str] = []
    sapan: list[str] = []
    print("MUTANT KITI -- her mutant icin hangi kapi YAKALAR (X) / KACIRIR (.)")
    print("kapilar: " + " | ".join(basliklar))
    print()
    for mut in MUTANTLAR:
        if secilen and mut.mid not in secilen:
            continue
        _uygula(mut)
        try:
            isaretler: list[str] = []
            detaylar: list[str] = []
            dusenler: dict[str, list[str]] = {}
            for ad, argv in KAPILAR:
                rc, ozet, _ = _kapi_kos(argv)
                isaretler.append("X" if rc != 0 else ".")
                if rc != 0:
                    detaylar.append(_ilk_hata(ad, ozet))
                    d = _dusen_testler(ozet)
                    if d:
                        dusenler[ad] = d
            durum = "".join(isaretler)
            yakalandi = "X" in durum
            if mut.kontrol:
                etiket = "KACTI (dogru: kontrol)" if not yakalandi else "*** KONTROL YAKALANDI = YANLIS POZITIF ***"
                if yakalandi:
                    yakalanan_kontrol.append(mut.mid)
            else:
                etiket = "YAKALANDI" if yakalandi else "*** HICBIR KAPI YAKALAMADI ***"
                if not yakalandi:
                    kacan.append(mut.mid)
            print(f"{mut.mid:7s} [{durum}] {etiket}   (beklenen: {mut.beklenen})")
            print(f"        {mut.aciklama}")
            print(f"        hedef: {mut.hedef}")
            if mut.urun_etkisi:
                print(f"        urun etkisi: {mut.urun_etkisi}")
            for d in detaylar:
                print(f"        | {d}")
            for ad, liste in dusenler.items():
                print(f"        | {ad} dusen {len(liste)}: " + "; ".join(x.split(" - ")[0].replace("FAILED ", "") for x in liste[:6]) + (" ..." if len(liste) > 6 else ""))
            if mut.beklenen not in (".....", "?") and not mut.kontrol:
                bek = {g for g in mut.beklenen.replace("(", " ").replace(")", " ").split() if g.startswith("G")}
                gercek = {basliklar[i].split("-")[0] for i, c in enumerate(durum) if c == "X"}
                if bek != gercek:
                    sapan.append(f"{mut.mid}: beklenen {sorted(bek)} gercek {sorted(gercek)}")
            satirlar.append(f"| {mut.mid} | {mut.aciklama} | {mut.hedef} | " + " | ".join(isaretler) + " |")
            sys.stdout.flush()
        finally:
            _geri_al()

    print()
    print("=== MARKDOWN TABLOSU ===")
    print("| # | mutant | hedef | " + " | ".join(basliklar) + " |")
    print("|---|---|---|" + "---|" * len(basliklar))
    for s in satirlar:
        print(s)
    print()
    if kacan:
        print(f"HICBIR KAPININ YAKALAMADIGI MUTANTLAR ({len(kacan)}): {', '.join(kacan)}")
    else:
        print("Kacan (kontrol olmayan) mutant yok.")
    if yakalanan_kontrol:
        print(f"YAKALANAN KONTROL MUTANTLARI = YANLIS POZITIF ({len(yakalanan_kontrol)}): {', '.join(yakalanan_kontrol)}")
    else:
        print("Kontrol mutantlarinin hepsi kacti (yanlis pozitif yok).")
    if sapan:
        print(f"TAHMINDEN SAPAN ({len(sapan)}):")
        for s in sapan:
            print(f"  {s}")
    else:
        print("Tahminden sapan yok.")


if __name__ == "__main__":
    main()
