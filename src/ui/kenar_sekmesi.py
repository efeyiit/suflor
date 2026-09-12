"""Suflör -- kenar sekmesi (`KenarSekmesi`), T-012 K1/K2/K3/K4/K6/K8.

Ekranin bir kenarinda kucuk YARIM DAIRE (kapali hal, `yaricap x 2*yaricap`);
imlec ustune gelince `acilma_ms` sonra iki secenekli panele acilir ("Anlık
çeviri" / "Bölge izle" + kucuk "pencereyi göster"), imlec ayrilinca
`kapanma_ms` sonra kapanir. Dikeyde suruklenebilir; sag tik -> `pencereyi_goster`.

Bu docstring, gorev paketindeki (T-012 packet.md surum 3) K1/K2/K3/K4/K6/K8
degismezlerinin bu modulde nasil uygulandigini belgeler. Her kararin
yaninda onu olcen test adi vardir (`tests/unit/ui/test_kenar_sekmesi.py`)
ya da `[ÖLÇÜLMÜYOR]` damgasi. Tester `known_gaps`i OKUMAZ; garanti alani
burasidir. Gercek ekran davranisi (odak, sureler, gercek OS tiki)
`.agents/tasks/T-012/real_check.py` ile ayri surecte olculur.

## K1 -- omur ve dis kapatma (▲▲ tur 2: Tester-A Y-A1, Tester-B O-B1)

OMUR: sekme ebeveynsiz (`Tool`) bir penceredir ve PYTHON SAHIPLIGINDEDIR: son
Python referansi dusunce (`del` + `gc.collect()` ya da `deleteLater`) C++ nesnesi
silinir, ekranda kalmaz, yoklayici durur (OLCULDU:
`test_k1_omur_son_referans_dusunce_silinir_gorunur_kalmaz[del_gc|deleteLater]`:
`weakref` None, gorunur ust-duzey listesinde yok, enjekte imlec sayaci artmaz).
Bunun kosulu: HICBIR sinyal baglantisi `self`i yakalayan lambda/closure
DEGILDIR -- uc panel dugmesi bagli yontemlere (`_anlik_tiki`/`_bolge_tiki`/
`_goster_tiki`) baglidir, sayaclar bagli yontemlere (`_ac`/`_kapat`/`_yokla`).
Lambda Qt baglantisinda `self`i tutar, gc dongusu gormez, sekme HIC silinmez
(tur 1 boyleydi: kenar durumundaki `AnaPencere` dusurulunce ZOMBI yarim daire).
Pozitif kontrol: lambda baglantili minimal widget canli kalir, bagli yontemli
toplanir (`test_k1_omur_pozitif_kontrol_lambda_baglantisi_sarmalayiciyi_tutar`,
`test_kabuk.py`); yapisal bekci: `src/ui`de `.connect(lambda ...)` yok
(`test_k1_sinyal_baglantilarinda_lambda_yok_ast`). `functools.partial` de
`self`i guclu tutar -- KULLANILMAZ. `availableGeometryChanged.connect` yapicinin
SON satiridir: yapici tasarsa yarim kurulu nesne ekran sinyaline bagli kalmaz
(Tester-A D-A4; ust sinir dogrulamasi zaten en basta).
DIS KAPATMA: `close()` (WM_CLOSE, `QApplication.closeAllWindows`, sonraki
ajanin `sekme.close()` cagrisi) `closeEvent` -> `kapandi` sinyali; pencere
gizlenir (`hideEvent`: yoklayici durur, panel kapanir). Kabugun kendi yolu
`hide()`dir ve `kapandi` YAYMAZ (ayirt edici:
`test_k1_kapandi_sinyali_close_ile_yayilir_hide_ile_yayilmaz`). `AnaPencere`
kenar durumunda `kapandi` -> `goster()` (`test_kabuk.py`
`test_k1_sekme_dis_close_kenar_durumunda_gorunure_doner`).

## K2 -- geometri saf modulden; kenara bitisik; `availableGeometry`

Butun konumlar `src.ui.geometri` fonksiyonlarindan gelir; bu sinif yalniz
`setGeometry` uygular. Ekran dikdortgeni `ekran.availableGeometry()` ile
baslar ve `QScreen.availableGeometryChanged` sinyaliyle GUNCELLENIR (gorev
cubugu tasininca sekme yeniden konumlanir; `y` yeni aralığa sikistirilir;
`test_k2_available_geometry_changed_sahte_sinyal_yeni_x`). `ekran_dikdortgeni`
salt-okunur ozelligi bunu verir. Varsayilan `y` dikey orta:
`top + height // 2 - yaricap` (U2 `(2534,670,26,52)` birebir). `y` yazilinca
`y_sinirla` uygulanir ve pencere tasinir (acikken panel, kapaliyken sekme);
`kenar` yazilinca ayni sekilde yeniden konumlanir ve cizim aynalanir.
DIKKAT: `y` OZELLIGI (paket arayuzu, `real_check` [5a] `s.y` okur) tabanin
`QWidget.y()` YONTEMINI golgeler: `sekme.y()` cagrisi `TypeError` verir;
pencerenin gercek konumu icin `frameGeometry()`/`pos()` kullanilir. `s.y`
her zaman KAPALI sekmenin ust kenaridir (panel acikken pencere `y`si panelin
ustudur, `s.y` degismez).
Cizim: `sag` kenarda dairenin merkezi widget'in SAG sinirinda (`(r, r)`),
yalniz sol yarim gorunur; `sol` kenarda merkez SOL sinirda (`(0, r)`), sag
yarim gorunur -- opak yari her zaman ekranin IC tarafindadir
(`test_k2_cizim_*`, `grab()` alfa). Monitor cikarilmasi (`screenRemoved`)
`[ÖLÇÜLMÜYOR]`: verilen `QScreen` silinirse Qt nesnesi olur, `RuntimeError`
(bilinen sinir, sonraki surum birincile tasir). DPI != 1.0 fiziksel kenar
yuvarlamasi `[ÖLÇÜLMÜYOR birim]` (`real_check` [8]).

## K3 -- odak almaz, girdiyi yalniz kendi alaninda yutar (YAPISAL)

Bayraklar `FramelessWindowHint | Tool | WindowStaysOnTopHint |
WindowDoesNotAcceptFocus`; oznitelikler `WA_TranslucentBackground`,
`WA_ShowWithoutActivating`; `focusPolicy = NoFocus` (panel dugmeleri de).
Pencere yalniz sekme/panel kadar; tam ekran katman yok -> disindaki her tik
oyuna gider. `_ac()` icinde `raise_()` (yoklamada degil: K6 blok yok).
`test_k3_bayraklar_ve_oznitelikler` yapisaldir; `activeWindow()` offscreen'de
`[ÖLÇÜLMÜYOR]` (platform bayraklari uygulamaz, KRT k2b) -- gercek davranis
yalniz `real_check` [3] gercek OS tiki ile. Topmost/exclusive tam ekran oyun
ustunde sekme gorunmez `[ÖLÇÜLMÜYOR]` (KRT k5 Z2; `known_gaps`).
Kabuk (shell) ust-band pencereleri de sekmenin USTUNDEDIR: Windows bildirim
balonu (`Windows.UI.Core.CoreWindow`, sag altta 396x153 px, ~6.2 s) alt-sag
banda suruklenmis sekmeyi orter; o surede gercek tik balona gider, hover
panel acmaz (OLCULDU: `real_check` tur-1 [5c] ihlali, kabugun KENDI balonu).
Tur 2 karari (paket v3, K5 ▲▲): `AnaPencere.tepsiye_al()` balonu SUREC BASINA
BIR KEZ gosterir (kullanici ilk kez kaybolan pencereyi bulabilsin); kapi [5]
sekmeyi YUKARI surukler (balon alanindan uzak). Tepsi durumunda sekme zaten
GIZLIDIR; balon yalniz `tepsi -> kenar` gecisi balon omru (~6 s) icinde
yapilirsa ve sekme alt-sag banda suruklenmisse orter -- belgeli, `[ÖLÇÜLMÜYOR]`.
Baska uygulamalarin balonlari / Baslat / bildirim merkezi icin ayni sinif
`[ÖLÇÜLMÜYOR]` (`known_gaps`; `WindowStaysOnTopHint` shell bandinin ustune
cikamaz).

## K4 -- yoklama tabanli zamanlama, enjekte imlec, surukleme, mod tiki

Imlec konumu YALNIZ yapiciya verilen `imlec_konumu()` ile okunur (varsayilan
`QCursor.pos`; enter/leave olaylarina guvenilmez --
`test_k4_imlec_yalniz_enjekte_edilen_callable_ile_okunur`). Yoklayici
(`yoklama_ms`) yalniz sekme GORUNURKEN calisir: `showEvent` baslatir,
`hideEvent` durdurur (`yokluyor` ozelligi; `test_k4_yoklayici_yalniz_gorunurken`;
bosta CPU ~%0.3 tek cekirdek, KRT k4b). Her yoklamada `sekme_icinde`
(kapaliyken yarim daire, acikken panel dikdortgeni):
  - iceride: kapanma sayaci durur; kapaliysa ve acilma sayaci calismiyorsa
    baslar (`acilma_ms`, tek atim) -> `_ac()`.
  - disarida: acilma sayaci durur; acik ve kapanma sayaci calismiyorsa
    baslar (`kapanma_ms`) -> `_kapat()`.
  Iceri-disari titremesi sayaclari sifirlar; icerideyken kapanma sayaci
  durur (`test_k4_iceri_disari_iceri_titremesi_acik_kalir`). Ornekleme fazi
  belirsizligi <= 1 yoklama: 50/50 ms titremede tek tuk acilma olabilir
  (KRT k1 P2 1/10) -- belgeli, `[ÖLÇÜLMÜYOR]`.
SURUKLEME (▲ Y2): kapaliyken sol dugme basilinca `surukleniyor=True`, acilma
sayaci DURUR; surukleme boyunca yoklayici sayac baslatmaz (`_yokla` erken
doner), `acik` degismez; `mouseMoveEvent` `y`yi tasir (`y_sinirla` ile sinira
kilitlenir); birakilinca `surukleniyor=False`, imlec icerideyse sayac bir
sonraki yoklamada SIFIRDAN baslar (`test_k4_surukleme_*`). Acikken sol tik
surukleme baslatmaz.
MOD TIKI (▲ O9): `dugme_anlik`/`dugme_bolge`/`dugme_goster` tiklaninca ONCE
panel kapanir (`acik=False`, kapali geometri uygulanir), SONRA sinyal yayilir
-- Snapshot karesine panel metni girmez
(`test_k4_mod_tiki_once_panel_kapanir_sonra_sinyal`). ▲▲ MANDAL (Tester-A
O-A1): dugmelerin kenara yakin ucu KAPALI diskin icindedir; tik oradaysa
imlec disk icinde kalir ve panel `acilma_ms` sonra yeniden acilirdi
(ertelenmis Snapshot karesine girer). Tik sonrasi tek atimlik mandal
(`_cikis_bekleniyor`): imlec kapali diskten BIR KEZ cikana kadar acilma sayaci
baslamaz; ciktiktan sonra normal
(`test_k4_mod_tiki_sonrasi_imlec_diskte_kalsa_da_yeniden_acilmaz_ciktiktan_sonra_acilir`,
iki dugme). Gizlenirken (`hideEvent`) panel kapanir, surukleme ve mandal
sifirlanir: yeniden gosterilince kapali ve taze gelir
(`test_k4_mod_tiki_mandali_gizlenip_gosterilince_sifirlanir`). Sag tik
`_mod_tiki`den gecmez (mandal yok; kabuk sekmeyi zaten gizler).
Sinirlar: birim testte ust sinir gevsek (`acilma_ms + 2*yoklama_ms + 300`,
CI titremesi KRT O2) + deterministik alt sinir (`acilma_ms // 2` sonra hala
kapali); siki sayilar `real_check` [4] (gercek ekran 129-153 / 476-478 ms).

## K6 -- modal yok, metin yok, blok yok; paint <= 16 ms

`QMessageBox`/`QDialog`/`print`/`logging`/`sleep`/`processEvents` yok (AST:
`test_k6_k7_kaynak_yasak_ad_ve_import_icermez`). `paintEvent` kapali halde
yarim daire + "S" (antialias), acik halde hicbir sey cizmez (panel kendi
stilini cizer). 100 kare medyani offscreen 0.04 / 0.21 ms, gercek ekran
0.24 / 0.83 ms (`test_k6_paint_100_kare_medyani_kapali_ve_acik`,
`real_check` [7]).

## K8 -- kesfedilebilirlik

`toolTip` "Sağ tık: pencereyi göster" icerir; panel baslik satirinda
`dugme_goster` (kucuk) `pencereyi_goster` yayar; uc panel dugmesinin
`toolTip` ve `accessibleName`i dolu (`test_k8_*`). Sag tik (kapali ya da
acik) `pencereyi_goster` yayar.

Parametre dogrulama (paket sessiz; bir adim otesi): `1 <= yaricap <= 66`
(`PANEL_BOYUTU.height() // 2`: acik panel kapali sekmeyi KAPSAMALI, aksi
halde imlec disk icinde-panel disinda kalip salinir -- Tester-A D-A3),
`0 <= acilma_ms/kapanma_ms <= 2**31-1`, `1 <= yoklama_ms <= 2**31-1` (QTimer
C++ int; otesi `OverflowError` olurdu -- D-A4); aksi `ValueError` yapimda,
hicbir Qt nesnesi yaratilmadan (`test_k4_gecersiz_parametre_valueerror`,
`test_k4_yaricap_ust_sinir_tam_degeri_kabul`).
"""
from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QPoint, QPointF, QRect, Qt, QTimer, Signal, SignalInstance
from PySide6.QtGui import (
    QCloseEvent,
    QColor,
    QCursor,
    QFont,
    QHideEvent,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QPen,
    QScreen,
    QShowEvent,
)
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from src.ui.geometri import PANEL_BOYUTU, Kenar, sekme_acik_dikdortgeni, sekme_icinde, sekme_kapali_dikdortgeni, y_sinirla

__all__ = ["KenarSekmesi"]

_YUZEY = "#161b21"
_CIZGI = "#2a3138"
_YAZI = "#d8e2ee"
_VURGU = "#5ec6ff"
_SEKME_BAYRAKLARI = (
    Qt.WindowType.FramelessWindowHint
    | Qt.WindowType.Tool
    | Qt.WindowType.WindowStaysOnTopHint
    | Qt.WindowType.WindowDoesNotAcceptFocus
)
_YARICAP_AZAMI = PANEL_BOYUTU.height() // 2  # 66: `2*yaricap <= panel.h` -> acik panel kapali sekmeyi kapsar (K2)
_MS_AZAMI = 2**31 - 1  # QTimer araligi C++ int; otesi OverflowError olurdu
_PANEL_STILI = (
    f"QFrame{{background:{_YUZEY}; border:1px solid {_CIZGI}; border-radius:10px;}}"
    f"QPushButton{{background:#1e2630; color:{_YAZI}; border:1px solid {_CIZGI}; border-radius:6px;"
    f" padding:8px 12px; font:13px 'Segoe UI'; text-align:left;}}"
    f"QPushButton:hover{{border-color:{_VURGU}; color:{_VURGU};}}"
    f"QPushButton#goster{{padding:0px; font:11px 'Segoe UI'; text-align:center; min-width:22px; max-width:22px;"
    f" min-height:20px; max-height:20px;}}"
    f"QLabel{{color:#8fa3b8; font:11px 'Segoe UI'; border:none;}}"
)


class KenarSekmesi(QWidget):
    """Ekran kenarinda yarim daire; imlec gelince iki secenekli panele acilir (moddul docstring'i)."""

    anlik_cevir = Signal()
    bolge_izle = Signal()
    pencereyi_goster = Signal()
    kapandi = Signal()  # dis `close()` (WM_CLOSE, closeAllWindows); kabugun `hide()` yolu YAYMAZ

    def __init__(
        self,
        ekran: QScreen,
        *,
        kenar: Kenar = Kenar.SAG,
        yaricap: int = 26,
        acilma_ms: int = 120,
        kapanma_ms: int = 450,
        yoklama_ms: int = 60,
        imlec_konumu: Callable[[], QPoint] | None = None,
    ) -> None:
        if not 1 <= yaricap <= _YARICAP_AZAMI:
            raise ValueError(f"1 <= yaricap <= {_YARICAP_AZAMI} olmali (panel sekmeyi kapsamali): {yaricap}")
        if not (0 <= acilma_ms <= _MS_AZAMI and 0 <= kapanma_ms <= _MS_AZAMI):
            raise ValueError(f"0 <= acilma_ms/kapanma_ms <= {_MS_AZAMI} olmali: {acilma_ms}/{kapanma_ms}")
        if not 1 <= yoklama_ms <= _MS_AZAMI:
            raise ValueError(f"1 <= yoklama_ms <= {_MS_AZAMI} olmali: {yoklama_ms}")
        super().__init__(None, _SEKME_BAYRAKLARI)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setToolTip("Suflör — imleci getir: Anlık çeviri / Bölge izle · Sağ tık: pencereyi göster · sürükle: taşı")
        self._ekran = ekran
        self._ekran_dikdortgeni = QRect(ekran.availableGeometry())
        self._kenar = Kenar(kenar)
        self._yaricap = yaricap
        self._acilma_ms = acilma_ms
        self._kapanma_ms = kapanma_ms
        self._yoklama_ms = yoklama_ms
        self._imlec_konumu: Callable[[], QPoint] = imlec_konumu if imlec_konumu is not None else QCursor.pos
        self._acik = False
        self._surukleme: int | None = None
        self._cikis_bekleniyor = False  # mod tiki mandali: imlec diskten cikana kadar yeniden acilma yok (K4 ▲▲)
        g = self._ekran_dikdortgeni
        self._y = y_sinirla(g, g.top() + g.height() // 2 - yaricap, yaricap)

        self._panel = QFrame(self)
        self._panel.setStyleSheet(_PANEL_STILI)
        duzen = QVBoxLayout(self._panel)
        duzen.setContentsMargins(10, 8, 10, 8)
        duzen.setSpacing(6)
        baslik = QHBoxLayout()
        baslik.setContentsMargins(0, 0, 0, 0)
        etiket = QLabel("Suflör")
        self._dugme_goster = QPushButton("▣")
        self._dugme_goster.setObjectName("goster")
        self._dugme_goster.setToolTip("Pencereyi göster (ya da sekmeye sağ tık)")
        self._dugme_goster.setAccessibleName("Pencereyi göster")
        baslik.addWidget(etiket)
        baslik.addStretch(1)
        baslik.addWidget(self._dugme_goster)
        self._dugme_anlik = QPushButton("⚡  Anlık çeviri")
        self._dugme_anlik.setToolTip("Ekran donar, metin blokları çerçevelenir, seçtiklerin çevrilir")
        self._dugme_anlik.setAccessibleName("Anlık çeviri")
        self._dugme_bolge = QPushButton("▭  Bölge izle")
        self._dugme_bolge.setToolTip("Dikdörtgen çiz; bölge sürekli çevrilir")
        self._dugme_bolge.setAccessibleName("Bölge izle")
        duzen.addLayout(baslik)
        duzen.addWidget(self._dugme_anlik)
        duzen.addWidget(self._dugme_bolge)
        for dugme in (self._dugme_goster, self._dugme_anlik, self._dugme_bolge):
            dugme.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        # K1 omur: BAGLI YONTEM -- lambda/closure `self`i Qt baglantisinda tutar, sekme hic silinmez (Tester-A Y-A1)
        self._dugme_anlik.clicked.connect(self._anlik_tiki)
        self._dugme_bolge.clicked.connect(self._bolge_tiki)
        self._dugme_goster.clicked.connect(self._goster_tiki)
        self._panel.hide()

        self._acilma = QTimer(self)
        self._acilma.setSingleShot(True)
        self._acilma.setInterval(acilma_ms)
        self._acilma.timeout.connect(self._ac)
        self._kapanma = QTimer(self)
        self._kapanma.setSingleShot(True)
        self._kapanma.setInterval(kapanma_ms)
        self._kapanma.timeout.connect(self._kapat)
        self._yoklayici = QTimer(self)
        self._yoklayici.setInterval(yoklama_ms)
        self._yoklayici.timeout.connect(self._yokla)
        self._kapat()
        ekran.availableGeometryChanged.connect(self._ekran_degisti)  # en son: yarim kurulu nesne sinyale bagli kalmasin

    # -- ozellikler ------------------------------------------------------------------------------
    @property
    def yaricap(self) -> int:
        return self._yaricap

    @property
    def acilma_ms(self) -> int:
        return self._acilma_ms

    @property
    def kapanma_ms(self) -> int:
        return self._kapanma_ms

    @property
    def yoklama_ms(self) -> int:
        return self._yoklama_ms

    @property
    def acik(self) -> bool:
        return self._acik

    @property
    def surukleniyor(self) -> bool:
        return self._surukleme is not None

    @property
    def yokluyor(self) -> bool:
        """Yoklayici calisiyor mu (yalniz gorunurken True)."""
        return self._yoklayici.isActive()

    @property
    def ekran_dikdortgeni(self) -> QRect:
        """Konumlandirmada kullanilan ekran dikdortgeni (`availableGeometry`, sinyalle guncel)."""
        return QRect(self._ekran_dikdortgeni)

    @property  # type: ignore[override]  # paket arayuzu baglayici: `y` ozelligi `QWidget.y()` yontemini golgeler (docstring)
    def y(self) -> int:
        return self._y

    @y.setter
    def y(self, deger: int) -> None:
        self._y = y_sinirla(self._ekran_dikdortgeni, int(deger), self._yaricap)
        self._konumlan()

    @property
    def kenar(self) -> Kenar:
        return self._kenar

    @kenar.setter
    def kenar(self, deger: Kenar) -> None:
        self._kenar = Kenar(deger)
        self._konumlan()
        self.update()

    @property
    def dugme_anlik(self) -> QPushButton:
        return self._dugme_anlik

    @property
    def dugme_bolge(self) -> QPushButton:
        return self._dugme_bolge

    @property
    def dugme_goster(self) -> QPushButton:
        return self._dugme_goster

    # -- geometri --------------------------------------------------------------------------------
    def _kapali_geometri(self) -> QRect:
        return sekme_kapali_dikdortgeni(self._ekran_dikdortgeni, self._y, self._yaricap, self._kenar)

    def _acik_geometri(self) -> QRect:
        return sekme_acik_dikdortgeni(self._ekran_dikdortgeni, self._y, self._yaricap, PANEL_BOYUTU, self._kenar)

    def _konumlan(self) -> None:
        self.setGeometry(self._acik_geometri() if self._acik else self._kapali_geometri())
        if self._acik:
            self._panel.setGeometry(self.rect())

    def _ekran_degisti(self, dikdortgen: QRect) -> None:
        self._ekran_dikdortgeni = QRect(dikdortgen)
        self._y = y_sinirla(dikdortgen, self._y, self._yaricap)
        self._konumlan()

    # -- acilma / kapanma ------------------------------------------------------------------------
    def _ac(self) -> None:
        self._acik = True
        self.setGeometry(self._acik_geometri())
        self._panel.setGeometry(self.rect())
        self._panel.show()
        self.raise_()
        self.update()

    def _kapat(self) -> None:
        self._kapanma.stop()
        self._acik = False
        self._panel.hide()
        self.setGeometry(self._kapali_geometri())
        self.update()

    def _yokla(self) -> None:
        if self._surukleme is not None:
            return
        icinde = sekme_icinde(self.frameGeometry(), self._imlec_konumu(), self._yaricap, self._kenar)
        if self._cikis_bekleniyor:
            if icinde:
                return  # mod tiki sonrasi imlec hala kapali diskte: sayac baslamaz
            self._cikis_bekleniyor = False
        if icinde:
            self._kapanma.stop()
            if not self._acik and not self._acilma.isActive():
                self._acilma.start()
        else:
            self._acilma.stop()
            if self._acik and not self._kapanma.isActive():
                self._kapanma.start()

    def _mod_tiki(self, sinyal: SignalInstance) -> None:
        self._acilma.stop()
        self._kapat()
        self._cikis_bekleniyor = True
        sinyal.emit()

    def _anlik_tiki(self) -> None:
        self._mod_tiki(self.anlik_cevir)

    def _bolge_tiki(self) -> None:
        self._mod_tiki(self.bolge_izle)

    def _goster_tiki(self) -> None:
        self._mod_tiki(self.pencereyi_goster)

    # -- olaylar ---------------------------------------------------------------------------------
    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self._yoklayici.start()

    def hideEvent(self, event: QHideEvent) -> None:
        super().hideEvent(event)
        self._yoklayici.stop()
        self._acilma.stop()
        self._surukleme = None
        self._cikis_bekleniyor = False
        self._kapat()

    def closeEvent(self, event: QCloseEvent) -> None:
        super().closeEvent(event)
        self.kapandi.emit()

    def paintEvent(self, event: QPaintEvent) -> None:
        if self._acik:
            return
        r = self._yaricap
        merkez_x = r if self._kenar is Kenar.SAG else 0
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(QColor(_VURGU), 2))
        p.setBrush(QColor(22, 27, 33, 235))
        p.drawEllipse(QPointF(merkez_x, r), r - 1.5, r - 1.5)
        p.setPen(QColor(_YAZI))
        p.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        p.drawText(QRect(0, 0, r, 2 * r), Qt.AlignmentFlag.AlignCenter, "S")
        p.end()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.RightButton:
            self.pencereyi_goster.emit()
        elif event.button() == Qt.MouseButton.LeftButton and not self._acik:
            self._acilma.stop()
            self._surukleme = int(event.globalPosition().y()) - self._y
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._surukleme is not None:
            self.y = int(event.globalPosition().y()) - self._surukleme
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._surukleme = None
        event.accept()

