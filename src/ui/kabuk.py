"""Suflör -- UI kabugu (`AnaPencere`, `Tepsi`, `KabukDurumu`), T-012 K1/K5/K6/K7/K8.

Cercevesiz ana pencere; sag ustte UC dugme (kullanici istegi, 11 Eylul 2026):
  ✕  Kapat        -- uygulama tamamen kapanir (`cikis_istendi`; tepside kalinti yok)
  ▾  Tepsiye al   -- pencere gizlenir, sistem tepsisinde calisir; ikona tik -> geri gelir
  ◐  Kenara al    -- masaustunde pencere gorunmez; ekran kenarinda yarim daire (`KenarSekmesi`)
Govdede iki mod dugmesi (`dugme_anlik`, `dugme_bolge`); sekmedekiyle AYNI sinyalleri yayar.

Bu docstring, gorev paketindeki (T-012 packet.md surum 3) K1/K5/K6/K7/K8
degismezlerinin bu modulde nasil uygulandigini belgeler. Her kararin
yaninda onu olcen test adi vardir (`tests/unit/ui/test_kabuk.py`) ya da
`[ÖLÇÜLMÜYOR]` damgasi. Tester `known_gaps`i OKUMAZ; garanti alani burasidir.

## K1 -- durum makinesi: uc durum, her gecis tanimli, ulasilamayan durum yok

`KabukDurumu` (StrEnum): `GORUNUR="gorunur"`, `TEPSI="tepsi"`, `KENAR="kenar"`.
Uclu = (pencere gorunur, sekme gorunur, tepsi ikonu gorunur):

    gorunur           (T,F,F)   `goster()` -- tepsi ikonunu DA gizler (KRT O6)
    tepsi             (F,F,T)   `tepsiye_al()` (tepsi varsa)
    kenar             (F,T,T)   `kenara_al()` -- tepside de kalir (sekme bulunamazsa donus yolu)
    kenar (tepsi yok) (F,T,F)   K5 istisnasi: tepsi yoksa `tepsiye_al()` da buraya duser

Gecisler: `gorunur ⇄ tepsi`, `gorunur ⇄ kenar`, `tepsi -> kenar` (tepsi menusu
"Kenara al"); `kenar -> tepsi` YOK (kenar durumunda `tepsiye_al()` kenari
korur; `test_k1_kenar_to_tepsi_yolu_yok`). Geri donus yollari: tepsi ikonuna
tek/cift tik, menu "Pencereyi göster", sekmeye sag tik, paneldeki
`dugme_goster` -- hepsi `goster()` -> (T,F,F) (`test_k1_gorunur_yollari_hepsi_ayni_uclu`).
`tepsiye_al()` x2 / `kenara_al()` x2 idempotent.

`closeEvent` (Alt+F4, WM_CLOSE, gorev cubugu "kapat") HER durumda `kapat()`
ile esdegerdir; `ignore()` edilmez -> "pencere gizli + ikon gizli + sekme
gizli ama surec yasiyor" (KRT Y1 zombi) ULASILAMAZ
(`test_k1_close_event_*`; `real_check` [6] `PostMessage(WM_CLOSE)`).
`kapat()` IDEMPOTENT: `kapandi` bayragi; ilk cagri sekmeyi gizler
(yoklayici durur), tepsi ikonunu gizler, pencereyi gizler (`hide()`;
`close()` DEGIL -- closeEvent zinciri yeniden girmez) ve `cikis_istendi`yi
TAM BIR KEZ yayar; ikinci cagri / `close()` sonrasi `closeEvent` / tepsi
"Çıkış" hicbir sey yapmaz (`test_k1_kapat_iki_kez_tek_sinyal`,
`test_k1_close_sonra_kapat_ikinci_sinyal_yok`). `kapat()` sonrasi uclu
(F,F,F); `durum` son durumu gosterir (enum uc uyeli, paket baglayici) ve
`goster()/tepsiye_al()/kenara_al()` DIRILTMEZ (`test_k1_kapat_sonrasi_dirilme_yok`).
Kabuk `QApplication.quit()`/`exit()` CAGIRMAZ; `src.ui.uygulama.calistir`
`cikis_istendi -> app.quit` baglar ve `setQuitOnLastWindowClosed(False)`
ayarlar (`test_k1_kabuk_qapplication_quit_cagirmaz`).
`goster()` kucultulmus (`showMinimized`, Win+D sinifi) pencereyi `showNormal()`
ile geri getirir (Tester-A D-A1; `test_k1_goster_kucultulmus_pencereyi_geri_getirir`).

▲▲ OMUR (Tester-A Y-A1): sekme EBEVEYNSIZ `Tool` penceredir ve `AnaPencere`nin
PYTHON SAHIPLIGINDEDIR (`_sekme` guclu referansi tek sahip): `AnaPencere`nin
son referansi dusunce (`del` + `gc.collect()`) ya da `deleteLater` ile
silinince sekme de SILINIR -- `weakref` None, gorunur ust-duzey 0, yoklayici
durur; `Tepsi` (C++ ebeveyn: `AnaPencere`) ve menusu de gider (OLCULDU:
`test_k1_omur_kenar_durumunda_ana_pencere_dusunce_sekme_silinir[del_gc|deleteLater]`,
`test_k1_omur_tepsi_son_referans_dusunce_silinir`). Kosul: bu modulde ve
sekmede HICBIR sinyal baglantisi `self`i yakalayan lambda/closure degildir
(bagli yontem ya da `sinyal.emit`; olculdu: ikisi de sarmalayiciyi tutmaz;
`functools.partial` tutar, KULLANILMAZ). Pozitif kontrol (kural 10): lambda
baglantili minimal widget `del`+gc sonrasi canli ve gorunur kalir, bagli
yontemli toplanir (`test_k1_omur_pozitif_kontrol_lambda_baglantisi_sarmalayiciyi_tutar`);
yapisal bekci `test_k1_sinyal_baglantilarinda_lambda_yok_ast`. Tur 1'de bu
cumle olculmeden yazilmisti ve YANLISTI (sekme hic toplanmiyordu: zombi).
`kapat()` sekmeyi ayrica acikca gizler.
▲▲ tur 3 (Tester-B O-B5 / Tester-A D-A9): `deleteLater()` cagrilip Python
referansi TUTULURKEN (Qt'de yaygin desen `self.pencere.deleteLater()`) C++
`AnaPencere` (tepsi + ikon ile) olur ama `_sekme` sarmalayicisi `__dict__`te
yasardi -> ZOMBI yarim daire (gorunur, yokluyor, hover panel acar, sag tik
alicisiz, tepsi ikonu yok, donus yolu yok); tur-2 olcusu `deleteLater` sonrasi
`del p` de yaptigi icin bu siniftan ayrismiyordu. Duzeltme: `self.destroyed ->
self._sekme.deleteLater` (alici sekme; bagli yontem, `self` yakalanmaz) ve
`Tepsi.destroyed -> menu.deleteLater` (ebeveynsiz `QMenu` ust-duzeyde
kalmasin). OLCULDU: sekme ve menu C++ duzeyinde silinir (`shiboken6.isValid`
False -- sarmalayici `__dict__`te durdugu icin weakref None OLMAZ; referans
birakilinca None), gorunur ust-duzey 0, yoklayici durur; `del`+gc /
`deleteLater`+`del` / `kapat()`+`del` yollarinda cift silme yok
(`test_k1_omur_kenar_durumunda_ana_pencere_dusunce_sekme_silinir[deleteLater_referans_tutulur]`).
C++ oldukten sonra tutulan sarmalayicida `goster()/kapat()` `RuntimeError`
verir (silinmis QObject; PySide standardi) -- kotu kullanim, `[ÖLÇÜLMÜYOR]`.
Dis `sekme.deleteLater()` (paketin yolu `close()`dur) kabugu kirar: `kapandi`
yayilmaz, sonraki `goster()/kapat()` `RuntimeError` (Tester-A D-A11) --
`known_gaps`, `[ÖLÇÜLMÜYOR]`.

▲▲ DIS KAPATMA (Tester-B O-B1): sekme disaridan `close()` edilirse (WM_CLOSE,
`QApplication.closeAllWindows`, sonraki ajanin cagrisi) `KenarSekmesi.kapandi`
yayar; `AnaPencere` KENAR durumundaysa `goster()` -> (T,F,F), `durum`
gorunur -- tepsisiz konfigurasyonda da (aksi halde (F,F,F) + `kapandi=False`
= "ulasilamaz" denen durum dis yoldan ulasilirdi). Sekme gizliyken `close()`
(gorunur/tepsi durumlari) durum makinesine dokunmaz
(`test_k1_sekme_dis_close_*`). Kabugun kendi yolu `hide()`dir (`kapandi` yok).

## K5 -- tepsi yoksa kullanici kilitlenmez

`Tepsi(ikon, ebeveyn, *, kullanilabilir=None)`: `None` ->
`QSystemTrayIcon.isSystemTrayAvailable()` (offscreen'de False). `kullanilabilir`
False ise `goster()` hicbir sey yapmaz, `gorunur()` DAIMA False (offscreen'de
`show()` sonrasi `isVisible()` True doner -- olcu ateslenebilir, KRT o12),
`bildir()` sessiz. Menu: "Pencereyi göster" -> `goster_istendi`, "Kenara al"
-> `kenara_al_istendi`, ayirici, "Çıkış" -> `cikis_istendi`. Ikona
`Trigger`/`DoubleClick` -> `goster_istendi`; `Context`/`MiddleClick`/`Unknown`
hicbir sey (`test_k5_*`). `AnaPencere.tepsiye_al()` tepsi yoksa `kenara_al()`
-> `durum == KENAR`, uclu (F,T,F). `bildir` bildirimler kapaliyken
`[ÖLÇÜLMÜYOR]`; tepsi ikonuna tik sonrasi on plana gelme (foreground kilidi)
gercek ekranda `[ÖLÇÜLMÜYOR]` (sag tik yolu `real_check` [5c] ile olculur).
▲▲ BALON (Tester-B O-B3, paket v3 K5): ILK `tepsiye_al()` SUREC BASINA BIR KEZ
`bildir("Suflör arka planda", "Tepsi ikonuna tıklayınca pencere geri gelir.",
2500)` gosterir -- Windows 11 yeni tepsi ikonunu tasma alaninda gizler,
balon olmadan kullanici hicbir sey gormuyordu. Sonraki cagrilar (ayni ornek
ya da ikinci `AnaPencere`) gostermez; sayac sinif duzeyinde
(`_balon_gosterildi`, testler sifirlar); tepsisiz `tepsiye_al()` (kenara duser)
sayaci tuketmez (`test_k5_ilk_tepsiye_al_surec_basina_bir_kez_balon`,
`test_k5_balon_surec_basina_bir_kez_ikinci_ornek_de_gostermez`,
`test_k5_tepsi_yokken_tepsiye_al_balon_sayacini_tuketmez`; `showMessage`
casusu, pozitif kontrollu). ▲▲ tur 3 (Tester-B D-B12): balona TIK da
pencereyi getirir (`QSystemTrayIcon.messageClicked -> goster_istendi ->
goster()`; `test_k5_balona_tik_pencereyi_getirir` -- balon baska surecin
penceresi oldugundan tik `messageClicked.emit()` ile temsil edilir).
OLCULDU (tur 1, `real_check` [5c]): balon BASKA
surecin penceresidir (`Windows.UI.Core.CoreWindow`), sag altta 396x153 px,
~6.2 s kalir, `ms` yok sayilir; sekme alt-sag banda suruklenmisse orter.
Tur-2 karari: tepsi durumunda sekme zaten gizlidir; kapi [5] sekmeyi YUKARI
surukler (balon alanindan uzak). Kalan sinif: `tepsi -> kenar` gecisi balon
omru icinde + sekme alt-sag bantta -- belgeli, `[ÖLÇÜLMÜYOR]`. Baska
uygulamalarin balonlari ayni bandi ayni sure orter `[ÖLÇÜLMÜYOR]`
(`known_gaps`; kabuk ust-band shell penceresinin ustune cikamaz).

## K6 -- modal yok, metin yok, blok yok

`QMessageBox`/`QDialog`/`QInputDialog`/`QFileDialog`/`print`/`logging`/
`warnings`/`time.sleep`/`processEvents` yok (AST, pozitif kontrollu:
`test_k6_k7_*`). Hata durum cubuguna yazilir (bu modulde hata uretmeyen
yol yok). Hicbir kullanici metni loglanmaz.

## K7 -- kabuk bagimsiz: pipeline bilmez

`src.capture`/`src.ocr`/`src.translate` import edilmez (AST + taze surec
`sys.modules` olcusu). Pencere dugmeleri ve sekme dugmeleri ayni sinyalleri
yayar (`anlik_cevir_istendi`, `bolge_izle_istendi`); dinleyicisiz calisir;
mod sinyali durumu DEGISTIRMEZ (kenar durumunda sekme kapali kalir, pencere
gelmez -- baglayan taraf karar verir). Global kisayollar (`Ctrl+Alt+T/R`)
ve yatay/monitorler arasi tasima bu paketin DISINDA (`known_gaps`).

## K8 -- cercevesiz pencere suruklenebilir, dugmeler erisilebilir

Ust 44 px baslik seridinden sol dugmeyle surukleme pencereyi tasir; dugme
uzerinde basinca `QPushButton` olayi yutar, surukleme baslamaz; govdeden
baslamaz (`test_k8_*`). Uc dugmenin `accessibleName`i {"Kapat", "Tepsiye al",
"Kenara al"}, `toolTip`leri dolu; mod dugmeleri de.
"""
from __future__ import annotations

from collections.abc import Callable
from enum import StrEnum
from typing import ClassVar

from PySide6.QtCore import QObject, QPoint, Qt, Signal
from PySide6.QtGui import QCloseEvent, QColor, QFont, QGuiApplication, QIcon, QMouseEvent, QPainter, QPixmap, QScreen
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMenu, QPushButton, QSystemTrayIcon, QVBoxLayout, QWidget

from src.ui.geometri import Kenar
from src.ui.kenar_sekmesi import KenarSekmesi

__all__ = ["AnaPencere", "KabukDurumu", "Tepsi"]

_ARKA = "#0d1116"
_YUZEY = "#161b21"
_CIZGI = "#2a3138"
_YAZI = "#d8e2ee"
_VURGU = "#5ec6ff"
_BASLIK_SERIDI_PX = 44
_PENCERE_STILI = (
    f"QWidget{{background:{_ARKA}; color:{_YAZI}; font-family:'Segoe UI';}}"
    f"QPushButton#mod{{background:{_YUZEY}; border:1px solid {_CIZGI}; border-radius:10px; padding:18px;"
    f" font-size:15px; text-align:left;}}"
    f"QPushButton#mod:hover{{border-color:{_VURGU};}}"
    f"QPushButton#ust{{background:transparent; border:none; color:#9fb3c8; font-size:15px; min-width:36px; min-height:28px;}}"
    f"QPushButton#ust:hover{{background:#222a33; color:{_YAZI};}}"
    f"QPushButton#kapat{{background:transparent; border:none; color:#9fb3c8; font-size:15px; min-width:36px; min-height:28px;}}"
    f"QPushButton#kapat:hover{{background:#c0392b; color:white;}}"
    f"QLabel#baslik{{font-size:18px; font-weight:600; color:{_VURGU};}}"
    f"QLabel#not{{color:#8fa3b8; font-size:12px;}}"
)


class KabukDurumu(StrEnum):
    """Kabugun uc durumu (modul docstring'indeki uclu tablosu)."""

    GORUNUR = "gorunur"
    TEPSI = "tepsi"
    KENAR = "kenar"


def _ikon() -> QIcon:
    """Tepsi ve pencere ikonu: vurgu renginde daire icinde 'S' (dosya yok, cizilir)."""
    pix = QPixmap(64, 64)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor(_VURGU))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(2, 2, 60, 60)
    p.setPen(QColor(_ARKA))
    p.setFont(QFont("Segoe UI", 30, QFont.Weight.Bold))
    p.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, "S")
    p.end()
    return QIcon(pix)


class Tepsi(QObject):
    """Sistem tepsisi ikonu + menu; tepsi yoksa sessiz ve `gorunur()` daima False (K5)."""

    goster_istendi = Signal()
    kenara_al_istendi = Signal()
    cikis_istendi = Signal()

    def __init__(self, ikon: QIcon, ebeveyn: QObject | None, *, kullanilabilir: bool | None = None) -> None:
        super().__init__(ebeveyn)
        self._kullanilabilir = QSystemTrayIcon.isSystemTrayAvailable() if kullanilabilir is None else bool(kullanilabilir)
        self._ikon = QSystemTrayIcon(ikon, self)
        self._ikon.setToolTip("Suflör — arka planda")
        self._menu = QMenu()
        self._menu.addAction("Pencereyi göster").triggered.connect(self.goster_istendi.emit)
        self._menu.addAction("Kenara al").triggered.connect(self.kenara_al_istendi.emit)
        self._menu.addSeparator()
        self._menu.addAction("Çıkış").triggered.connect(self.cikis_istendi.emit)
        self._ikon.setContextMenu(self._menu)
        self._ikon.activated.connect(self._tiklandi)
        self._ikon.messageClicked.connect(self.goster_istendi.emit)  # D-B12: balona tik da pencereyi getirir
        self.destroyed.connect(self._menu.deleteLater)  # O-B5: C++ Tepsi olunce ebeveynsiz menu de gitsin (sarmalayici tutulsa da)

    @property
    def kullanilabilir(self) -> bool:
        return self._kullanilabilir

    @property
    def ikon(self) -> QSystemTrayIcon:
        return self._ikon

    @property
    def menu(self) -> QMenu:
        return self._menu

    def goster(self) -> None:
        if self._kullanilabilir:
            self._ikon.show()

    def gizle(self) -> None:
        self._ikon.hide()

    def gorunur(self) -> bool:
        return self._kullanilabilir and self._ikon.isVisible()

    def bildir(self, baslik: str, metin: str, ms: int) -> None:
        if self._kullanilabilir:
            self._ikon.showMessage(baslik, metin, QSystemTrayIcon.MessageIcon.NoIcon, ms)

    def _tiklandi(self, sebep: QSystemTrayIcon.ActivationReason) -> None:
        if sebep in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self.goster_istendi.emit()


def _ekrani_coz(ekran: QScreen | None) -> QScreen:
    if ekran is not None:
        return ekran
    birincil = QGuiApplication.primaryScreen()
    if birincil is None:
        raise RuntimeError("ekran yok: QGuiApplication.primaryScreen() None dondu")
    return birincil


class AnaPencere(QWidget):
    """Cercevesiz ana pencere; sag ustte Kapat · Tepsiye al · Kenara al (modul docstring'i)."""

    anlik_cevir_istendi = Signal()
    bolge_izle_istendi = Signal()
    cikis_istendi = Signal()
    _balon_gosterildi: ClassVar[bool] = False  # K5 ▲▲: "arka planda" balonu SUREC basina bir kez (test sifirlar)

    def __init__(
        self,
        ekran: QScreen | None = None,
        *,
        kenar: Kenar = Kenar.SAG,
        tepsi_kullanilabilir: bool | None = None,
        imlec_konumu: Callable[[], QPoint] | None = None,
    ) -> None:
        super().__init__(None, Qt.WindowType.FramelessWindowHint)
        self._durum = KabukDurumu.GORUNUR
        self._kapandi = False
        self._surukleme: QPoint | None = None
        self.setWindowTitle("Suflör")
        self.setWindowIcon(_ikon())
        self.resize(520, 340)
        self.setStyleSheet(_PENCERE_STILI)

        baslik = QLabel("Suflör")
        baslik.setObjectName("baslik")
        self._dugme_kenar = self._ust_dugme("◐", "Kenara al", "Kenara al — masaüstünde görünmez, ekran kenarında yarım daire")
        self._dugme_tepsi = self._ust_dugme("▾", "Tepsiye al", "Tepsiye al — arka planda çalışır, tepsi ikonuna tık geri getirir")
        self._dugme_kapat = self._ust_dugme("✕", "Kapat", "Kapat — uygulama tamamen kapanır")
        self._dugme_kapat.setObjectName("kapat")
        ust = QHBoxLayout()
        ust.setContentsMargins(14, 8, 8, 0)
        ust.addWidget(baslik)
        ust.addStretch(1)
        for dugme in (self._dugme_kenar, self._dugme_tepsi, self._dugme_kapat):
            ust.addWidget(dugme)

        self._dugme_anlik = QPushButton("⚡  Anlık çeviri\nEkranı dondur, blokları seç, çevir")
        self._dugme_anlik.setObjectName("mod")
        self._dugme_anlik.setAccessibleName("Anlık çeviri")
        self._dugme_anlik.setToolTip("Anlık çeviri (Snapshot modu)")
        self._dugme_bolge = QPushButton("▭  Bölge izle\nDikdörtgen çiz, sürekli çevir")
        self._dugme_bolge.setObjectName("mod")
        self._dugme_bolge.setAccessibleName("Bölge izle")
        self._dugme_bolge.setToolTip("Bölge izle (Region-watch modu)")
        notu = QLabel("Çevrimdışı · yerel OCR + yerel çeviri · hiçbir metin diske ya da ağa gitmez")
        notu.setObjectName("not")
        self._durum_satiri = QLabel("")
        self._durum_satiri.setObjectName("not")
        govde = QVBoxLayout()
        govde.setContentsMargins(18, 10, 18, 14)
        govde.setSpacing(10)
        govde.addWidget(self._dugme_anlik)
        govde.addWidget(self._dugme_bolge)
        govde.addStretch(1)
        govde.addWidget(notu)
        govde.addWidget(self._durum_satiri)
        duzen = QVBoxLayout(self)
        duzen.setContentsMargins(0, 0, 0, 0)
        duzen.addLayout(ust)
        duzen.addLayout(govde)

        self._tepsi = Tepsi(self.windowIcon(), self, kullanilabilir=tepsi_kullanilabilir)
        self._tepsi.goster_istendi.connect(self.goster)
        self._tepsi.kenara_al_istendi.connect(self.kenara_al)
        self._tepsi.cikis_istendi.connect(self.kapat)

        self._sekme = KenarSekmesi(_ekrani_coz(ekran), kenar=kenar, imlec_konumu=imlec_konumu)
        self._sekme.pencereyi_goster.connect(self.goster)
        self._sekme.kapandi.connect(self._sekme_kapandi)
        self._sekme.anlik_cevir.connect(self.anlik_cevir_istendi.emit)
        self._sekme.bolge_izle.connect(self.bolge_izle_istendi.emit)

        self._dugme_kapat.clicked.connect(self.kapat)
        self._dugme_tepsi.clicked.connect(self.tepsiye_al)
        self._dugme_kenar.clicked.connect(self.kenara_al)
        self._dugme_anlik.clicked.connect(self.anlik_cevir_istendi.emit)
        self._dugme_bolge.clicked.connect(self.bolge_izle_istendi.emit)
        # O-B5 / D-A9: `deleteLater()` + tutulan Python referansi -> C++ AnaPencere olur, `_sekme` sarmalayicisi
        # `__dict__`te yasar (zombi yarim daire). Alici sekme (bagli yontem, `self` yakalanmaz): C++ olunce sekme de silinir.
        self.destroyed.connect(self._sekme.deleteLater)

    @staticmethod
    def _ust_dugme(metin: str, ad: str, ipucu: str) -> QPushButton:
        dugme = QPushButton(metin)
        dugme.setObjectName("ust")
        dugme.setAccessibleName(ad)
        dugme.setToolTip(ipucu)
        return dugme

    # -- ozellikler ------------------------------------------------------------------------------
    @property
    def durum(self) -> KabukDurumu:
        return self._durum

    @property
    def kapandi(self) -> bool:
        """`kapat()` cagrildi mi (bir kez; sonrasi uclu (F,F,F), dirilme yok)."""
        return self._kapandi

    @property
    def sekme(self) -> KenarSekmesi:
        return self._sekme

    @property
    def tepsi(self) -> Tepsi:
        return self._tepsi

    @property
    def dugme_kapat(self) -> QPushButton:
        return self._dugme_kapat

    @property
    def dugme_tepsi(self) -> QPushButton:
        return self._dugme_tepsi

    @property
    def dugme_kenar(self) -> QPushButton:
        return self._dugme_kenar

    @property
    def dugme_anlik(self) -> QPushButton:
        return self._dugme_anlik

    @property
    def dugme_bolge(self) -> QPushButton:
        return self._dugme_bolge

    # -- durum gecisleri -------------------------------------------------------------------------
    def goster(self) -> None:
        """-> gorunur (T,F,F): sekme ve tepsi ikonu gizlenir, pencere one gelir (kucultulmusse normal boyuta)."""
        if self._kapandi:
            return
        self._sekme.hide()
        self._tepsi.gizle()
        self._durum = KabukDurumu.GORUNUR
        if self.isMinimized():
            self.showNormal()
        else:
            self.show()
        self.raise_()
        self.activateWindow()

    def tepsiye_al(self) -> None:
        """-> tepsi (F,F,T); tepsi yoksa `kenara_al()`; kenar durumunda kenar korunur; ilk kez surec basina bir balon."""
        if self._kapandi or self._durum is KabukDurumu.KENAR:
            return
        if not self._tepsi.kullanilabilir:
            self.kenara_al()
            return
        self._sekme.hide()
        self._tepsi.goster()
        self.hide()
        self._durum = KabukDurumu.TEPSI
        if not AnaPencere._balon_gosterildi:
            AnaPencere._balon_gosterildi = True
            self._tepsi.bildir("Suflör arka planda", "Tepsi ikonuna tıklayınca pencere geri gelir.", 2500)

    def kenara_al(self) -> None:
        """-> kenar (F,T,T) / tepsi yoksa (F,T,F): pencere gizli, sekme gorunur, tepsi ikonu da kalir."""
        if self._kapandi:
            return
        self._tepsi.goster()
        self.hide()
        self._sekme.show()
        self._durum = KabukDurumu.KENAR

    def kapat(self) -> None:
        """Her durumdan (F,F,F); yoklayici durur; `cikis_istendi` TAM BIR KEZ; idempotent."""
        if self._kapandi:
            return
        self._kapandi = True
        self._sekme.hide()
        self._tepsi.gizle()
        self.hide()
        self.cikis_istendi.emit()

    def _sekme_kapandi(self) -> None:
        """Sekme DISARIDAN `close()` edildi (WM_CLOSE, `closeAllWindows`): kenar durumundaysak gorunure don."""
        if self._durum is KabukDurumu.KENAR and not self._kapandi:
            self.goster()

    # -- olaylar ---------------------------------------------------------------------------------
    def closeEvent(self, event: QCloseEvent) -> None:
        self.kapat()
        event.accept()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and event.position().y() < _BASLIK_SERIDI_PX:
            self._surukleme = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._surukleme is not None:
            self.move(event.globalPosition().toPoint() - self._surukleme)
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._surukleme = None
        event.accept()
