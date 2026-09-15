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

from PySide6.QtWidgets import QApplication

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
    sorunlar: list[str] = []
    for ad, kombinasyon in kisayollar.items():
        sonuc = servis.kaydet(ad, kombinasyon)
        if sonuc is not KayitSonucu.OK:
            sorunlar.append(f"{kombinasyon} kaydedilemedi: {kayit_sebebi(sonuc, servis.son_hata_kodu)}")
    pencere.kisayol_etiketleri(servis.kayitli())
    if sorunlar:
        pencere.durum_goster("; ".join(sorunlar) + ". " + _DEVAM_NOTU)


def calistir(
    argv: Sequence[str] | None = None,
    *,
    kenar: Kenar = Kenar.SAG,
    calistirici: Calistirici | None = None,
    kisayollar: Mapping[str, str] | None = None,
    kisayol_servisi: KisayolServisi | None = None,
) -> int:
    """`QApplication` + `AnaPencere` + kisayollar; `cikis_istendi -> app.quit`; `calistirici(app, pencere)` donusu."""
    app = _uygulama(argv)
    app.setQuitOnLastWindowClosed(False)
    pencere = AnaPencere(kenar=kenar)
    pencere.cikis_istendi.connect(app.quit)
    servis = kisayol_servisi if kisayol_servisi is not None else KisayolServisi(pencere, gercek_win32=True)
    _kisayollari_kur(pencere, servis, kisayollar if kisayollar is not None else VARSAYILAN_KISAYOLLAR)
    pencere.show()
    return (calistirici if calistirici is not None else _varsayilan_calistirici)(app, pencere)
