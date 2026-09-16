"""Suflör -- UI giris noktasi (`calistir`), T-012 K1 (▲ KRT Y1: "uygulama karar verir") + T-013 K4/K5.

`calistir(argv=None, *, kenar=Kenar.SAG, calistirici=None, kisayollar=None, kisayol_servisi=None) -> int`:
  1. `QApplication`: mevcut bir ornek varsa YENIDEN KULLANILIR (pytest-qt
     `qapp`), yoksa `QApplication(list(argv) ya da sys.argv)` kurulur.
  2. `app.setQuitOnLastWindowClosed(False)` -- tepsi/kenar halinde hicbir
     pencere gorunmezken surec yasamali (KRT k4 D); `AnaPencere.kapat()`
     (dugme, tepsi "Çıkış", Alt+F4/WM_CLOSE) `cikis_istendi` yayar ve
     BURADA `app.quit`e baglanir -- kabuk kendisi `quit()` cagirmaz (K1).
  3. T-013: kisayol servisi. `kisayol_servisi` verilmezse GERCEK Win32'li
     servis kurulur: `KisayolServisi(pencere, gercek_win32=True)` -- ebeveyn
     pencere (omur: pencere silinince kayitlar kalkar, K1 ▲ Y3); testler
     sahte fn'li servisi ENJEKTE eder (▲ Y1: offscreen'de de gercek kayit
     olur; sefin `conftest.py`si `SUFLOR_GERCEK_KISAYOL_YASAK=1` ile
     enjeksiyonsuz cagriyi `RuntimeError` yapar --
     `test_k4_kisayol_servisi_verilmezse_*`). `kisayollar` verilmezse
     `VARSAYILAN_KISAYOLLAR` = `{"anlik_cevir": "Ctrl+Alt+D", "bolge_izle":
     "Ctrl+Alt+R"}` (▲ Y2: TR-Q'da `Ctrl+Alt` = AltGr; `T` ₺ uretir, `D` ve
     `R` bos -- KRT k4b; `test_k4_varsayilan_kisayollar_*`).
     Baglantilar: `servis.tetiklendi -> pencere.kisayol_tetiklendi` (BAGLI
     YONTEM; ad tablosu kabukta, bilinmeyen ad yok sayilir; K4 -- lambda/
     partial pencereyi Qt baglantisinda tutar, Y-A1 zombi sinifi:
     `test_k4_calistir_sonrasi_pencere_toplanabilir_*`) ve
     `pencere.cikis_istendi -> servis.hepsini_kaldir`
     (`test_k4_cikis_istendi_hepsini_kaldirir`). Her ad icin
     `servis.kaydet(ad, kombinasyon)`; `OK` disi sonuc durum satirina yazilir
     (K5): `"<kombinasyon> kaydedilemedi: <sebep>"` parcalari `"; "` ile,
     sonda tek kez `". Pencere düğmeleri ve tepsi menüsü çalışmaya devam
     eder."`; sebep `kayit_sebebi(sonuc, hata_kodu)`: 1409 "başka bir uygulama
     kullanıyor", AltGr "bu klavye düzeninde AltGr ile çakışıyor", gecersiz
     "geçersiz kombinasyon", diger "Windows hata kodu N"; "ayarlardan
     değiştirin" YAZILMAZ (ayar yok, v2). `pencere.kisayol_etiketleri(...)`
     KAYITLI kombinasyonlari (`servis.kayitli()`) dugmelere ve tepsi ipucuna
     yazar; kaydedilemeyen "(kısayol yok)". Diger kisayol calismaya devam eder,
     cikis kodu degismez, `QMessageBox` yok (`test_k5_*`, AST).
  4. `AnaPencere(kenar=kenar)` gosterilir; `calistirici(app, pencere)`
     calistirilir (varsayilan `app.exec()`), donusu cikis kodudur.
`calistirici` ENJEKTE edilebilir: birim testi `exec()` cagirmadan kurulumu
sinar; `quit` baglantisi gercek `app.exec()` + 0 ms sonra `kapat()` ile
olculur (`tests/unit/ui/test_uygulama.py`). Pipeline baglanmaz; o is
`demo/kabuk.py`nindir (sefe ait) ve bu modulu kullanir. Gecikme (WM_HOTKEY ->
sinyal) bosta < 20 ms (`real_check` [1]); yuk altinda `[ÖLÇÜLMÜYOR]`.
"""
from __future__ import annotations

import sys
from collections.abc import Callable, Mapping, Sequence
from types import MappingProxyType

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QApplication, QWidget

from src.ayarlar import Ayarlar, AyarlarDeposu
from src.ui.geometri import Kenar
from src.ui.kabuk import AnaPencere
from src.ui.kisayol import KayitSonucu, KisayolServisi

__all__ = ["VARSAYILAN_KISAYOLLAR", "Calistirici", "calistir", "kayit_sebebi"]

Calistirici = Callable[[QApplication, AnaPencere], int]
VARSAYILAN_KISAYOLLAR: Mapping[str, str] = MappingProxyType({"anlik_cevir": "Ctrl+Alt+D", "bolge_izle": "Ctrl+Alt+R"})
_DEVAM_NOTU = "Pencere düğmeleri ve tepsi menüsü çalışmaya devam eder."


def kayit_sebebi(sonuc: KayitSonucu, hata_kodu: int) -> str:
    """K5 durum satiri sebebi; `OK` icin bos."""
    if sonuc is KayitSonucu.CAKISMA:
        return "başka bir uygulama kullanıyor"
    if sonuc is KayitSonucu.ALTGR_CAKISMA:
        return "bu klavye düzeninde AltGr ile çakışıyor"
    if sonuc is KayitSonucu.GECERSIZ:
        return "geçersiz kombinasyon"
    if sonuc is KayitSonucu.HATA:
        return f"Windows hata kodu {hata_kodu}"
    return ""


def _uygulama(argv: Sequence[str] | None) -> QApplication:
    mevcut = QApplication.instance()
    if isinstance(mevcut, QApplication):
        return mevcut
    return QApplication(list(argv) if argv is not None else sys.argv)


def _varsayilan_calistirici(app: QApplication, pencere: AnaPencere) -> int:
    return app.exec()


def _kisayollari_kur(pencere: AnaPencere, servis: KisayolServisi, kisayollar: Mapping[str, str]) -> None:
    servis.tetiklendi.connect(pencere.kisayol_tetiklendi)
    pencere.cikis_istendi.connect(servis.hepsini_kaldir)
    _kisayollari_kaydet(pencere, servis, kisayollar)


def _kisayollari_kaydet(pencere: AnaPencere, servis: KisayolServisi, kisayollar: Mapping[str, str]) -> None:
    """(Yeniden) kayit: onceki kayitlar kaldirilir, verilenler kaydedilir, etiketler/durum guncellenir (T-016 canli uygulama)."""
    servis.hepsini_kaldir()
    sorunlar: list[str] = []
    for ad, kombinasyon in kisayollar.items():
        sonuc = servis.kaydet(ad, kombinasyon)
        if sonuc is not KayitSonucu.OK:
            sorunlar.append(f"{kombinasyon} kaydedilemedi: {kayit_sebebi(sonuc, servis.son_hata_kodu)}")
    pencere.kisayol_etiketleri(servis.kayitli())
    if sorunlar:
        pencere.durum_goster("; ".join(sorunlar) + ". " + _DEVAM_NOTU)


def _ayarlardan_kisayollar(a: Ayarlar) -> Mapping[str, str]:
    return {"anlik_cevir": a.kisayol_anlik, "bolge_izle": a.kisayol_bolge}


def _ayarlari_uygula(pencere: AnaPencere, servis: KisayolServisi, a: Ayarlar) -> None:
    """T-016 canli uygulama: kisayollar yeniden kaydedilir, sekme kenari degisir. Dil/sozluk pipeline'in isi (sinyal)."""
    _kisayollari_kaydet(pencere, servis, _ayarlardan_kisayollar(a))
    pencere.sekme.kenar = Kenar(a.kenar)


class _AyarKontrolu(QObject):
    """Ayar panelini acar, kaydedileni uygular (T-016). Pencereye EBEVEYNLI QObject: baglantilar bagli yontem
    (lambda/closure yok -- Y-A1 sinifi; `test_k1_sinyal_baglantilarinda_lambda_yok_ast`), pencere silinince silinir."""

    def __init__(self, pencere: AnaPencere, servis: KisayolServisi, depo: AyarlarDeposu, mevcut: Ayarlar) -> None:
        super().__init__(pencere)
        # Pencereye GUCLU referans tutulmaz: cocuk -> ebeveyn Python referansi + ebeveyn -> cocuk C++ sahipligi
        # capraz dongu kurar; GC ebeveyni toplarken cocugun ozniteliklerini bosaltmasi yigin bozulmasina yol
        # acti (olculdu: pipeline+ui testleri birlikte 0xC0000374). `parent()` uzerinden erisilir.
        self._servis, self._depo, self._mevcut = servis, depo, mevcut
        self._panel: QWidget | None = None

    @property
    def _pencere(self) -> AnaPencere:
        ebeveyn = self.parent()
        assert isinstance(ebeveyn, AnaPencere)
        return ebeveyn

    @property
    def mevcut(self) -> Ayarlar:
        return self._mevcut

    def ac(self) -> None:
        from src.ui.ayarlar_paneli import AyarlarPaneli
        from src.ui.kisayol import altgr_karakteri

        if self._panel is not None and self._panel.isVisible():
            self._panel.raise_(); self._panel.activateWindow()
            return
        panel = AyarlarPaneli(self._mevcut, altgr_karakteri=altgr_karakteri)
        panel.kaydedildi.connect(self.kaydedildi)
        g = self._pencere.frameGeometry()
        panel.move(g.right() + 12, g.top())
        panel.show()
        self._panel = panel

    def kaydedildi(self, a: object) -> None:
        if not isinstance(a, Ayarlar):
            return
        try:
            self._depo.kaydet(a)
        except (ValueError, OSError) as hata:
            self._pencere.durum_goster(f"ayarlar kaydedilemedi: {type(hata).__name__}")
            return
        self._mevcut = a
        _ayarlari_uygula(self._pencere, self._servis, a)
        self._pencere.ayarlar_degisti.emit(a)


def calistir(
    argv: Sequence[str] | None = None,
    *,
    kenar: Kenar = Kenar.SAG,
    calistirici: Calistirici | None = None,
    kisayollar: Mapping[str, str] | None = None,
    kisayol_servisi: KisayolServisi | None = None,
    ayarlar_deposu: AyarlarDeposu | None = None,
) -> int:
    """`QApplication` + `AnaPencere` + kisayollar (+ T-016 ayarlar); `cikis_istendi -> app.quit`; `calistirici(app, pencere)` donusu.

    `ayarlar_deposu` verilirse ayarlar dosyadan yuklenir (asla istisna; sorunlar durum satirinda), `kenar`/`kisayollar`
    ayarlardan gelir (acik parametreler yine ONCELIKLI), ⚙ dugmesi paneli acar, kaydedilen ayarlar canli uygulanir ve
    `pencere.ayarlar_degisti` yayilir; `baslangic` tepsi/kenar ise pencere o durumda acilir.
    """
    app = _uygulama(argv)
    app.setQuitOnLastWindowClosed(False)
    mevcut: list[Ayarlar] = [Ayarlar()]
    yukleme_sorunlari: list[str] = []
    if ayarlar_deposu is not None:
        sonuc = ayarlar_deposu.yukle()
        mevcut[0] = sonuc.ayarlar
        yukleme_sorunlari = sonuc.sorunlar
        if kenar is Kenar.SAG:
            kenar = Kenar(mevcut[0].kenar)
        if kisayollar is None:
            kisayollar = _ayarlardan_kisayollar(mevcut[0])
    pencere = AnaPencere(kenar=kenar)
    pencere.cikis_istendi.connect(app.quit)
    servis = kisayol_servisi if kisayol_servisi is not None else KisayolServisi(pencere, gercek_win32=True)
    _kisayollari_kur(pencere, servis, kisayollar if kisayollar is not None else VARSAYILAN_KISAYOLLAR)
    if ayarlar_deposu is not None:
        kontrol = _AyarKontrolu(pencere, servis, ayarlar_deposu, mevcut[0])
        pencere.ayarlar_istendi.connect(kontrol.ac)
        if yukleme_sorunlari:
            pencere.durum_goster("ayarlar dosyasında sorunlu alanlar varsayılana döndü: " + ", ".join(yukleme_sorunlari))
    pencere.show()
    if ayarlar_deposu is not None:
        if mevcut[0].baslangic == "tepsi":
            pencere.tepsiye_al()
        elif mevcut[0].baslangic == "kenar":
            pencere.kenara_al()
    return (calistirici if calistirici is not None else _varsayilan_calistirici)(app, pencere)
