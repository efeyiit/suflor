"""T-014 -- AnlikAkisi (Snapshot akisi) K1-K6. Sahte motorlar; gercek OCR/NMT yok (real_check ayri)."""
from __future__ import annotations

import gc
import json
import time
import weakref
from collections.abc import Callable, Iterator, Sequence
from pathlib import Path

import numpy as np
import pytest
from PySide6.QtCore import QThread
from pytestqt.qtbot import QtBot

from src.contracts.errors import OcrError, ProviderUnavailable
from src.contracts.interfaces import FakeOcrEngine, FakeProvider, OcrEngine
from src.contracts.models import Frame, OcrPreset, Rect, TextBlock, TranslationRequest, TranslationResult
from src.ocr.satir_birlestirici import satirlari_birlestir
from src.ocr.rapid_engine import OcrLanguage
from src.pipeline.anlik import AnlikAkisi
from src.pipeline.dil_secici import DilSecici
from src.pipeline.secim import secimi_birlestir
from src.translate.sozluk import GlossaryStore


def kare(seq: int = 1) -> Frame:
    return Frame(image=np.zeros((40, 80, 3), dtype=np.uint8), rect=Rect(0, 0, 80, 40), captured_at=1.0, seq=seq)


def blok(metin: str, x: int, y: int, w: int = 100, h: int = 20) -> TextBlock:
    return TextBlock(text=metin, bbox=Rect(x, y, w, h), confidence=0.9)


BLOKLAR = [blok("Marcus", 10, 10, 60), blok("waits", 75, 10, 50), blok("by the mill.", 10, 40, 120)]


class YavasOcr(OcrEngine):
    """Ilk cagrida `bekleme_s` uyur (K2 sira korumasi olcusu icin), sonrakiler aninda."""

    def __init__(self, sonuclar: Sequence[Sequence[TextBlock]], bekleme_s: float) -> None:
        self._sonuclar = [list(s) for s in sonuclar]
        self._bekleme = bekleme_s
        self.cagri = 0

    def recognize(self, frame: Frame, preset: OcrPreset) -> list[TextBlock]:
        i = self.cagri
        self.cagri += 1
        if i == 0:
            time.sleep(self._bekleme)
        return list(self._sonuclar[min(i, len(self._sonuclar) - 1)])


class PatlayanOcr(OcrEngine):
    def __init__(self, hata: Exception, sonra: Sequence[TextBlock]) -> None:
        self._hata, self._sonra, self.cagri = hata, list(sonra), 0

    def recognize(self, frame: Frame, preset: OcrPreset) -> list[TextBlock]:
        self.cagri += 1
        if self.cagri == 1:
            raise self._hata
        return list(self._sonra)


@pytest.fixture
def akis(qtbot: QtBot) -> Iterator[Callable[..., AnlikAkisi]]:
    yaratilanlar: list[AnlikAkisi] = []

    def yarat(ocr: OcrEngine | None = None, saglayici: FakeProvider | None = None, sozluk: GlossaryStore | None = None,
              kaynak: str = "eng_Latn") -> AnlikAkisi:
        a = AnlikAkisi(ocr or FakeOcrEngine([BLOKLAR]), saglayici or FakeProvider(), sozluk, kaynak_dili=kaynak)
        yaratilanlar.append(a)
        return a

    yield yarat
    for a in yaratilanlar:
        a.kapat()


# ---------------------------------------------------------------- K3 zincir
def test_k3_oku_bloklar_hazir_satirlari_birlestirilmis(qtbot: QtBot, akis: Callable[..., AnlikAkisi]) -> None:
    a = akis()
    with qtbot.waitSignal(a.bloklar_hazir, timeout=3000) as sinyal:
        seq = a.oku(kare())
    assert seq == 1 and a.seq == 1
    bloklar = sinyal.args[0]
    assert bloklar == satirlari_birlestir(BLOKLAR)          # ayni satirdaki iki kutu birlesti
    assert len(bloklar) == 2 and bloklar[0].text == "Marcus waits"


def test_k3_cevir_ceviri_hazir_birlestirilmis_segmentler_ve_ceviriler(qtbot: QtBot, akis: Callable[..., AnlikAkisi]) -> None:
    saglayici = FakeProvider(translations={"Marcus waits by the mill.": "Marcus degirmenin yaninda bekliyor."})
    a = akis(saglayici=saglayici)
    secim = satirlari_birlestir(BLOKLAR)
    with qtbot.waitSignal(a.ceviri_hazir, timeout=3000) as sinyal:
        a.cevir(secim)
    segmentler, ceviriler = sinyal.args
    assert segmentler == secimi_birlestir(secim)
    assert len(segmentler) == len(ceviriler) == 1
    assert ceviriler[0] == "Marcus degirmenin yaninda bekliyor."
    assert saglayici.requests[0].source_lang == "eng_Latn" and saglayici.requests[0].target_lang == "tr"


def test_k3_sozluk_varsa_modele_gomulu_gider_uiya_orijinal_doner(qtbot: QtBot, akis: Callable[..., AnlikAkisi], tmp_path: Path) -> None:
    yol = tmp_path / "s.json"
    yol.write_text(json.dumps({"terimler": [{"kaynak": "mill", "hedef": "Degirmen"}]}), encoding="utf-8")
    saglayici = FakeProvider()
    a = akis(saglayici=saglayici, sozluk=GlossaryStore(yol))
    with qtbot.waitSignal(a.ceviri_hazir, timeout=3000) as sinyal:
        a.cevir(satirlari_birlestir(BLOKLAR))
    segmentler, _ = sinyal.args
    istek: TranslationRequest = saglayici.requests[0]
    assert "Degirmen" in istek.segments[0].text and "mill" not in istek.segments[0].text   # modele gomulu
    assert "mill" in segmentler[0].text and "Degirmen" not in segmentler[0].text          # UI'ya orijinal


def test_t020_ceviri_hafizasi_kesin_eslesmede_modeli_atlar_ve_kalici_yazar(tmp_path: Path) -> None:
    from src.pipeline.anlik import cevir_yap
    from src.store.translation_memory import TranslationMemory

    hafiza = TranslationMemory(tmp_path / "db.sqlite")
    try:
        saglayici = FakeProvider(translations={"Open the west door.": "Batı kapısını aç."})
        secim = [blok("Open the west door.", 0, 0, 200, 20)]
        _, ilk = cevir_yap(saglayici, None, secim, "eng_Latn", OcrPreset.DIALOGUE, hafiza=hafiza)
        assert ilk == ["Batı kapısını aç."] and saglayici.call_count == 1
        _, ikinci = cevir_yap(saglayici, None, secim, "eng_Latn", OcrPreset.DIALOGUE, hafiza=hafiza)
        assert ikinci == ilk and saglayici.call_count == 1
    finally:
        hafiza.close()


def test_t020_benzer_hafiza_ornegi_istege_eklenir(tmp_path: Path) -> None:
    from src.pipeline.anlik import cevir_yap
    from src.store.translation_memory import TranslationMemory

    hafiza = TranslationMemory(tmp_path / "db.sqlite")
    try:
        hafiza.add("Open the western door before midnight", "Gece yarısından önce batı kapısını aç", "eng_Latn")
        saglayici = FakeProvider()
        cevir_yap(saglayici, None, [blok("Open the west door before midnight", 0, 0, 260, 20)],
                   "eng_Latn", OcrPreset.DIALOGUE, hafiza=hafiza)
        assert saglayici.requests[0].tm_examples
        assert saglayici.requests[0].tm_examples[0].target.startswith("Gece yarısından")
    finally:
        hafiza.close()


def test_t020_kismi_kesin_eslesmede_yalniz_eksik_segment_modele_gider(tmp_path: Path) -> None:
    from src.pipeline.anlik import cevir_yap
    from src.store.translation_memory import TranslationMemory

    hafiza = TranslationMemory(tmp_path / "db.sqlite")
    try:
        hafiza.add("First clue", "İlk ipucu", "eng_Latn")
        saglayici = FakeProvider(translations={"Second clue": "İkinci ipucu"})
        bloklar = [blok("First clue", 0, 0, 100, 20), blok("Second clue", 0, 100, 100, 20)]
        _, ceviriler = cevir_yap(saglayici, None, bloklar, "eng_Latn", OcrPreset.DIALOGUE, hafiza=hafiza)
        assert ceviriler == ["İlk ipucu", "İkinci ipucu"]
        assert [s.text for s in saglayici.requests[0].segments] == ["Second clue"]
        assert hafiza.exact("Second clue", "eng_Latn").target == "İkinci ipucu"  # type: ignore[union-attr]
    finally:
        hafiza.close()


def test_t017_cok_satirli_secim_TEK_segment_olarak_modele_gider(qtbot: QtBot, akis: Callable[..., AnlikAkisi]) -> None:
    """Kullanici geri bildirimi: satir satir ceviri metnin butunlugunu bozuyordu. Secim = tek metin."""
    satirlar = [blok("방앗간을 지나 동쪽 길로", 40, 500, 420, 30), blok("가면 오래된 사당이 있어.", 40, 536, 440, 30),
                blok("거기서 만나자.", 40, 572, 260, 30)]
    saglayici = FakeProvider()
    a = akis(saglayici=saglayici, kaynak="kor_Hang")
    with qtbot.waitSignal(a.ceviri_hazir, timeout=3000) as sinyal:
        a.cevir(satirlar)
    segmentler, ceviriler = sinyal.args
    assert len(segmentler) == len(ceviriler) == 1
    assert segmentler[0].text == "방앗간을 지나 동쪽 길로 가면 오래된 사당이 있어. 거기서 만나자."
    assert len(saglayici.requests) == 1 and len(saglayici.requests[0].segments) == 1   # modele tek parca


def test_t017_ikinci_cevir_ilkinin_gec_sonucunu_dusurur(qtbot: QtBot, akis: Callable[..., AnlikAkisi]) -> None:
    """Secim degisince yeni ceviri; eski (yavas) ceviri gec gelse bile yayilmaz."""
    class IlkiYavas(FakeProvider):
        def translate(self, request: TranslationRequest) -> TranslationResult:
            if len(self.requests) == 0:
                time.sleep(0.3)
            return super().translate(request)

    a = akis(saglayici=IlkiYavas())
    gelen: list[object] = []
    a.ceviri_hazir.connect(lambda seg, cev: gelen.append(list(cev)))
    a.cevir([blok("eski", 0, 0)])
    a.cevir([blok("yeni", 0, 0)])
    qtbot.waitUntil(lambda: bool(gelen), timeout=3000)
    qtbot.wait(300)
    assert gelen == [["[tr] yeni"]]


def test_k3_bos_secim_model_cagrilmaz_bos_sonuc(qtbot: QtBot, akis: Callable[..., AnlikAkisi]) -> None:
    saglayici = FakeProvider()
    a = akis(saglayici=saglayici)
    with qtbot.waitSignal(a.ceviri_hazir, timeout=3000) as sinyal:
        a.cevir([])
    assert sinyal.args == [[], []] and saglayici.call_count == 0


def test_k3_oku_yapilmadan_cevir_calisir(qtbot: QtBot, akis: Callable[..., AnlikAkisi]) -> None:
    a = akis()
    with qtbot.waitSignal(a.ceviri_hazir, timeout=3000):
        a.cevir([blok("hello", 0, 0)])


# ---------------------------------------------------------------- K1 UI thread bloklanmaz
def test_k1_oku_hemen_doner_is_arka_planda(qtbot: QtBot, akis: Callable[..., AnlikAkisi]) -> None:
    ocr = YavasOcr([BLOKLAR], bekleme_s=0.3)
    a = akis(ocr=ocr)
    t0 = time.perf_counter()
    a.oku(kare())
    sure_ms = (time.perf_counter() - t0) * 1000
    assert sure_ms < 5, f"oku() {sure_ms:.1f} ms surdu -- UI thread bloklandi"
    with qtbot.waitSignal(a.bloklar_hazir, timeout=3000):
        pass


def test_k1_isci_ana_threadde_degil(qtbot: QtBot, akis: Callable[..., AnlikAkisi]) -> None:
    gorulen: list[bool] = []

    class KaydedenOcr(OcrEngine):
        def recognize(self, frame: Frame, preset: OcrPreset) -> list[TextBlock]:
            gorulen.append(QThread.currentThread() is not _ana_thread)
            return list(BLOKLAR)

    _ana_thread = QThread.currentThread()
    a = akis(ocr=KaydedenOcr())
    with qtbot.waitSignal(a.bloklar_hazir, timeout=3000):
        a.oku(kare())
    assert gorulen[-1] is True   # OCR isci thread'inde kostu


# ---------------------------------------------------------------- K2 sira korumasi
def test_k2_ikinci_oku_ilkinin_gec_sonucunu_dusurur(qtbot: QtBot, akis: Callable[..., AnlikAkisi]) -> None:
    ilk = [blok("ESKI", 0, 0)]
    ikinci = [blok("YENI", 0, 50)]
    a = akis(ocr=YavasOcr([ilk, ikinci], bekleme_s=0.25))
    gelen: list[list[TextBlock]] = []
    a.bloklar_hazir.connect(gelen.append)
    a.oku(kare(1))
    qtbot.wait(30)
    a.oku(kare(2))
    qtbot.waitUntil(lambda: len(gelen) >= 1, timeout=3000)
    qtbot.wait(400)   # eski sonucun gelmesi icin bol zaman
    assert len(gelen) == 1 and gelen[0][0].text == "YENI"


def test_k2_iptal_ucustaki_sonucu_dusurur(qtbot: QtBot, akis: Callable[..., AnlikAkisi]) -> None:
    a = akis(ocr=YavasOcr([BLOKLAR], bekleme_s=0.2))
    gelen: list[object] = []
    a.bloklar_hazir.connect(gelen.append)
    a.oku(kare())
    a.iptal()
    qtbot.wait(500)
    assert gelen == []
    # pozitif kontrol: iptal sonrasi yeni okuma gelir
    with qtbot.waitSignal(a.bloklar_hazir, timeout=3000):
        a.oku(kare())


def test_k2_iptal_ucustaki_ceviriyi_dusurur(qtbot: QtBot, akis: Callable[..., AnlikAkisi]) -> None:
    class YavasSaglayici(FakeProvider):
        def translate(self, request: TranslationRequest) -> TranslationResult:
            time.sleep(0.2)
            return super().translate(request)

    a = akis(saglayici=YavasSaglayici())
    gelen: list[object] = []
    a.ceviri_hazir.connect(lambda *args: gelen.append(args))
    a.cevir(satirlari_birlestir(BLOKLAR))
    a.iptal()
    qtbot.wait(500)
    assert gelen == []


# ---------------------------------------------------------------- K4 hata
@pytest.mark.parametrize("istisna, ad", [(OcrError("x"), "OcrError"), (RuntimeError("y"), "RuntimeError")])
def test_k4_ocr_hatasi_sinif_adiyla_gelir_metin_yok_thread_yasar(qtbot: QtBot, akis: Callable[..., AnlikAkisi], istisna: Exception, ad: str) -> None:
    a = akis(ocr=PatlayanOcr(istisna, BLOKLAR))
    with qtbot.waitSignal(a.hata, timeout=3000) as sinyal:
        a.oku(kare())
    assert sinyal.args == [ad]          # yalniz sinif adi; "x"/"y" metni yok
    with qtbot.waitSignal(a.bloklar_hazir, timeout=3000):   # thread yasiyor
        a.oku(kare())


def test_k4_ceviri_hatasi_sinif_adiyla(qtbot: QtBot, akis: Callable[..., AnlikAkisi]) -> None:
    a = akis(saglayici=FakeProvider(error=ProviderUnavailable("gizli metin")))
    with qtbot.waitSignal(a.hata, timeout=3000) as sinyal:
        a.cevir([blok("hello", 0, 0)])
    assert sinyal.args == ["ProviderUnavailable"]


def test_k4_hata_da_sira_korumasina_tabi(qtbot: QtBot, akis: Callable[..., AnlikAkisi]) -> None:
    class YavasPatlayan(OcrEngine):
        def recognize(self, frame: Frame, preset: OcrPreset) -> list[TextBlock]:
            time.sleep(0.2)
            raise OcrError("x")

    a = akis(ocr=YavasPatlayan())
    gelen: list[str] = []
    a.hata.connect(gelen.append)
    a.oku(kare())
    a.iptal()
    qtbot.wait(500)
    assert gelen == []


# ---------------------------------------------------------------- K5 kapanis / omur
def test_k5_kapat_threadi_durdurur_idempotent(qtbot: QtBot) -> None:
    a = AnlikAkisi(FakeOcrEngine([BLOKLAR]), FakeProvider(), None, kaynak_dili="eng_Latn")
    assert a._thread.isRunning()
    a.kapat()
    assert not a._thread.isRunning() and a.kapandi
    a.kapat()   # sessiz
    gelen: list[object] = []
    a.bloklar_hazir.connect(gelen.append)
    a.oku(kare())
    qtbot.wait(100)
    assert gelen == []   # kapali akis sonuc yaymaz


def test_k5_referans_dusunce_thread_durur(qtbot: QtBot) -> None:
    a = AnlikAkisi(FakeOcrEngine([BLOKLAR]), FakeProvider(), None, kaynak_dili="eng_Latn")
    thread = a._thread
    ref = weakref.ref(a)
    del a
    gc.collect()
    qtbot.wait(100)
    assert ref() is None or not thread.isRunning()


# ---------------------------------------------------------------- K6 enjeksiyon / saflik
def test_k6_modul_dosya_ag_ve_log_bilmez() -> None:
    import ast

    kaynak = Path("src/pipeline/anlik.py").read_text(encoding="utf-8")
    agac = ast.parse(kaynak)
    modul_adlari = {n.names[0].name.split(".")[0] for n in ast.walk(agac) if isinstance(n, ast.Import)} | {
        (n.module or "").split(".")[0] for n in ast.walk(agac) if isinstance(n, ast.ImportFrom)}
    assert not modul_adlari & {"logging", "warnings", "socket", "urllib", "requests", "subprocess", "os", "io"}
    assert "print(" not in kaynak
    # pozitif kontrol: gercekten import taramasi yapiyoruz
    assert "PySide6" in modul_adlari and "src" in modul_adlari


def test_k6_preset_motora_aynen_gider(qtbot: QtBot) -> None:
    ocr = FakeOcrEngine([BLOKLAR])
    a = AnlikAkisi(ocr, FakeProvider(), None, kaynak_dili="jpn_Jpan", preset=OcrPreset.MENU)
    try:
        with qtbot.waitSignal(a.bloklar_hazir, timeout=3000):
            a.oku(kare())
        assert ocr.calls[0][1] == OcrPreset.MENU
    finally:
        a.kapat()


# ---------------------------------------------------------------- saf zincir fonksiyonlari (isci thread'i kapsam izleyicisinin disinda)
def test_saf_oku_yap_ve_cevir_yap(tmp_path: Path) -> None:
    from src.pipeline.anlik import cevir_yap, oku_yap

    bloklar = oku_yap(FakeOcrEngine([BLOKLAR]), kare(), OcrPreset.DIALOGUE)
    assert bloklar == satirlari_birlestir(BLOKLAR)
    yol = tmp_path / "s.json"
    yol.write_text(json.dumps({"terimler": [{"kaynak": "mill", "hedef": "Degirmen"}]}), encoding="utf-8")
    saglayici = FakeProvider()
    segmentler, ceviriler = cevir_yap(saglayici, GlossaryStore(yol), bloklar, "eng_Latn", OcrPreset.DIALOGUE)
    assert len(segmentler) == len(ceviriler) == 1 and "Degirmen" in saglayici.requests[0].segments[0].text
    assert cevir_yap(saglayici, None, [], "eng_Latn", OcrPreset.DIALOGUE) == ([], [])
    with pytest.raises(ProviderUnavailable):
        cevir_yap(FakeProvider(error=ProviderUnavailable("x")), None, bloklar, "eng_Latn", OcrPreset.DIALOGUE)


# ---------------------------------------------------------------- K3 ikinci gecis (secim kirpigi yeniden okunur)
def test_ikinci_gecis_kirpik_kare_koordinatinda_ve_pay_sinirlanir() -> None:
    from src.pipeline.anlik import KIRPMA_PAYI_PX, ikinci_gecis

    class KaydedenOcr(OcrEngine):
        def __init__(self) -> None:
            self.kareler: list[Frame] = []

        def recognize(self, frame: Frame, preset: OcrPreset) -> list[TextBlock]:
            self.kareler.append(frame)
            return [blok("yeni", frame.rect.x + 5, frame.rect.y + 5, 30, 10)]

    ocr = KaydedenOcr()
    k = Frame(image=np.zeros((400, 600, 3), dtype=np.uint8), rect=Rect(1000, 500, 600, 400), captured_at=0.0, seq=3)
    secim = [blok("a", 1010, 505, 100, 20), blok("b", 1010, 600, 200, 20)]   # kare koordinatinda (ofsetli)
    yeni = ikinci_gecis(ocr, k, secim, OcrPreset.DIALOGUE)
    alt = ocr.kareler[0]
    assert alt.rect.x == 1000 and alt.rect.y == 500                      # ust/sol pay kare disina tasmadi (kare kenarinda)
    assert alt.rect.x + alt.rect.w == 1010 + 200 + KIRPMA_PAYI_PX        # sag pay
    assert alt.rect.y + alt.rect.h == 620 + KIRPMA_PAYI_PX
    assert alt.image.shape[:2] == (alt.rect.h, alt.rect.w) and alt.seq == 3
    assert yeni[0].bbox.x == 1005 and yeni[0].bbox.y == 505               # sonuc kare koordinatinda


def test_ikinci_gecis_bos_okuma_secimi_korur_ve_bos_secim_bos() -> None:
    from src.pipeline.anlik import ikinci_gecis

    k = Frame(image=np.zeros((100, 100, 3), dtype=np.uint8), rect=Rect(0, 0, 100, 100), captured_at=0.0, seq=1)
    secim = [blok("a", 10, 10, 20, 10)]
    assert ikinci_gecis(FakeOcrEngine([[]]), k, secim, OcrPreset.DIALOGUE) == secim
    assert ikinci_gecis(FakeOcrEngine([[]]), k, [], OcrPreset.DIALOGUE) == []


def test_k3_cevir_oku_sonrasi_ikinci_gecis_yapar(qtbot: QtBot, akis: Callable[..., AnlikAkisi]) -> None:
    ocr = FakeOcrEngine([BLOKLAR, [blok("ikinci gecis", 10, 10, 200, 20)]])
    a = akis(ocr=ocr)
    buyuk = Frame(image=np.zeros((600, 800, 3), dtype=np.uint8), rect=Rect(0, 0, 800, 600), captured_at=1.0, seq=1)
    with qtbot.waitSignal(a.bloklar_hazir, timeout=3000):
        a.oku(buyuk)
    with qtbot.waitSignal(a.ceviri_hazir, timeout=3000) as s:
        a.cevir(satirlari_birlestir(BLOKLAR))
    assert ocr.call_count == 2 and ocr.calls[1][0].rect.w < 800       # kirpik kare, tam kare degil
    assert s.args[0][0].text == "ikinci gecis"                          # normalize ikinci gecisin bloklarini kullandi


def test_k3_duzeltici_ciktiya_uygulanir(qtbot: QtBot) -> None:
    from src.translate.hedef_duzeltici import HedefDuzeltici

    saglayici = FakeProvider(translations={"Marcus waits by the mill.": "Elder Marks bekliyor."})
    a = AnlikAkisi(FakeOcrEngine([BLOKLAR]), saglayici, None, kaynak_dili="eng_Latn",
                   duzeltici=HedefDuzeltici({"Elder": "İhtiyar", "Marks": "Marcus"}))
    try:
        with qtbot.waitSignal(a.ceviri_hazir, timeout=3000) as s:
            a.cevir(satirlari_birlestir(BLOKLAR))
        assert s.args[1] == ["İhtiyar Marcus bekliyor."]
    finally:
        a.kapat()


# ---------------------------------------------------------------- K7 (T-018) dil secici
_NLLB = {OcrLanguage.KOREAN: "kor_Hang", OcrLanguage.JAPAN: "jpn_Jpan", OcrLanguage.CHINESE: "zho_Hans", OcrLanguage.ENGLISH: "eng_Latn"}
_JP = [blok("水車小屋を過ぎて東の道を行くと、古い祠がある。", 10, 10, 400), blok("日が沈む前にそこで会おう。", 10, 40, 300)]


def _secici(motorlar: dict[OcrLanguage, OcrEngine], baslangic: OcrLanguage) -> DilSecici:
    return DilSecici(lambda d: motorlar[d], _NLLB, baslangic=baslangic)


def test_k7_dil_degisince_motor_ve_kaynak_dili_degisir_bloklar_kazanandan(qtbot: QtBot) -> None:
    """Ayar Korece, oyun Japonca: KR motoru cop verir -> JP secilir; bloklar JP'den; ceviri jpn_Jpan ile; ikinci gecis JP motoruyla."""
    def dusuk(metin: str) -> TextBlock:
        return TextBlock(text=metin, bbox=Rect(0, 0, 100, 20), confidence=0.5)
    kr_cop = FakeOcrEngine([[dusuk("가")]])
    jp = FakeOcrEngine([_JP]); zh = FakeOcrEngine([[dusuk("水車小屋過")]]); en = FakeOcrEngine([[dusuk("ab")]])
    secici = _secici({OcrLanguage.KOREAN: kr_cop, OcrLanguage.JAPAN: jp, OcrLanguage.CHINESE: zh, OcrLanguage.ENGLISH: en}, OcrLanguage.KOREAN)
    saglayici = FakeProvider()
    a = AnlikAkisi(kr_cop, saglayici, None, kaynak_dili="kor_Hang", dil_secici=secici)
    diller: list[tuple[str, bool]] = []
    a.dil_algilandi.connect(lambda d, b: diller.append((d, b)))
    with qtbot.waitSignal(a.bloklar_hazir, timeout=3000) as s:
        a.oku(kare())
    assert diller == [("japan", False)] and [b.text for b in s.args[0]] == [b.text for b in _JP]
    assert secici.mevcut is OcrLanguage.JAPAN
    with qtbot.waitSignal(a.ceviri_hazir, timeout=3000):
        a.cevir(s.args[0])
    assert saglayici.requests[0].source_lang == "jpn_Jpan"
    # Dil algilama: JP serit + JP tam kare; ceviri: secim kirpigiyle ikinci gecis.
    assert jp.call_count == 3 and kr_cop.call_count == 1
    a.kapat()


def test_k7_mevcut_eminse_sinyal_gelir_baska_motor_yok(qtbot: QtBot) -> None:
    kr = FakeOcrEngine([[blok("방앗간을 지나 동쪽 길로 가면 오래된 사당이 있어.", 10, 10, 400)]])
    kurulan: list[OcrLanguage] = []

    def fabrika(d: OcrLanguage) -> OcrEngine:
        kurulan.append(d); return kr
    secici = DilSecici(fabrika, _NLLB, baslangic=OcrLanguage.KOREAN)
    a = AnlikAkisi(kr, FakeProvider(), None, kaynak_dili="kor_Hang", dil_secici=secici)
    diller: list[tuple[str, bool]] = []
    a.dil_algilandi.connect(lambda d, b: diller.append((d, b)))
    with qtbot.waitSignal(a.bloklar_hazir, timeout=3000):
        a.oku(kare())
    assert diller == [("korean", False)] and kurulan == [OcrLanguage.KOREAN] and kr.call_count == 1
    a.kapat()


def test_k7_secici_yoksa_sinyal_yok(qtbot: QtBot, akis: Callable[..., AnlikAkisi]) -> None:
    a = akis()
    diller: list[object] = []
    a.dil_algilandi.connect(diller.append)
    with qtbot.waitSignal(a.bloklar_hazir, timeout=3000):
        a.oku(kare())
    assert diller == []


def test_k7_secici_hatasi_hata_sinyali(qtbot: QtBot) -> None:
    class Bozuk(OcrEngine):
        def recognize(self, frame: Frame, preset: OcrPreset) -> list[TextBlock]:
            raise RuntimeError("bug")

    kr = FakeOcrEngine([[blok("가", 0, 0, 20)]])
    secici = DilSecici(lambda d: kr if d is OcrLanguage.KOREAN else Bozuk(), _NLLB, baslangic=OcrLanguage.KOREAN)
    a = AnlikAkisi(kr, FakeProvider(), None, kaynak_dili="kor_Hang", dil_secici=secici)
    with qtbot.waitSignal(a.hata, timeout=3000) as h:
        a.oku(kare())
    assert h.args == ["RuntimeError"]
    a.kapat()
