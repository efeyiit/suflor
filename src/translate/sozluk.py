"""Suflor -- terim sozlugu (`GlossaryStore`) ve kaynaga gomme (`terimleri_gom`), T-011.

Katman 0 on-islemcisi. Tasarim 4.1 "sozluk motora zorunlu kisit olarak
enjekte edilir" der; yerel NMT motoru (T-007) kisit ALAMAZ ve
`TranslationRequest.glossary_hits`i okumaz (dondurulmus). Olculen tek
calisan yol (olgular G1/G4: 21/21 korundu, Ingilizce'ye kayma 0/21): terimi
KAYNAK metinde hedef bicimiyle degistirmek ve aralik disindaki her karakteri
(KR ekler `을/를/가/는`, JP parcaciklar `を/が/は`) DOKUNMADAN birakmak; motor
gomulu terimi aynen tasir ve kalan eki dogru cekimler (`방앗간을` ->
`Değirmen을` -> "Değirmen'den gecin").

Zincir (pipeline kurar, bu modul cevirmez):
    hits = store.lookup_segments(segments)          # segment_index dolu
    gomulu = terimleri_gom(segments, hits)          # saf, kopya dondurur
    provider.translate(TranslationRequest(segments=gomulu, ...))
`lookup(text, placeholders)` tek metin uzerinde calisir ve `segment_index`i
dolduramaz (sozlesme); `lookup_segments` iliskilendirmeyi yapar.

Bu docstring, gorev paketindeki (T-011 packet.md surum 2) K1-K7
degismezlerinin bu modulde nasil uygulandigini belgeler. Her kararin
yaninda onu olcen test adi vardir (`tests/unit/translate/test_sozluk.py`)
ya da `[ÖLÇÜLMÜYOR]` damgasi. Tester `known_gaps`i OKUMAZ; garanti alani
burasidir.

YAZARLIK KURALI (K4, Y3 -- gercek motorla OLCULDU): sozluge YALNIZ motorun
YANLIS cevirdigi terimler girer -- ozel adlar, motorun bilmedigi bilesikler
(`水車小屋`/`방앗간` -> "su arabasi" yerine `Değirmen`). Motorun ZATEN
BILDIGI bir kelimeyi gommek ceviriyi BOZAR: bilinen kelime yerine gecen
Latin terim motoru kesme isaretli, yanlis unlulu ("Kılıç'i") ya da anlamsiz
("insa ediyoruz") ciktilara surukler. Sozluk kalite araci degil, ad/terim
sabitleme aracidir; bir terimi eklemeden once ham ceviride yanlis oldugunu
gor. Ceviri KALITESI bu modulde `[ÖLÇÜLMÜYOR]` (altin set yok; gomulu
terimin korunumu `real_check.py` #1/#2'de gercek motorla olculur).

## K1 -- esleme: en uzun once, ortusmesiz, sinir kurali HER BETIKTE AYNI

`lookup(text, placeholders=())`:
  1. `text` ve `placeholders` NFC'lenir (K6). Bos sozluk/metin -> `[]`.
  2. TEK GECIS: sozlugun butun terimleri tek bir ileri-bakisli TRIE
     deseninde (`re.IGNORECASE`, ORIJINAL/NFC metin uzerinde; metin
     kucultulmez -- casefold `İ`/`ﬁ`yi genisletip indeksi kaydirir, KRT O2)
     taranir; her konumda o konumdan baslayan EN UZUN terim bulunur (eslesen
     dilim kanonik anahtarla terime baglanir), ayni konumda baslayan daha kisa
     terimler yukleme zamaninda hesaplanan onek tablosundan eklenir. Boylece
     aday kumesi TAMDIR (her `(konum, terim)` cifti) ve maliyet terim
     sayisindan bagimsiz, metinle olcekli (K5; `_tarama_deseni`).
  3. Adaylar `(uzunluk azalan, start artan, sozluk sirasi)` ile islenir:
     kabul edilen bir aralikla ya da korunan bir aralikla (K3) ortusen aday
     ATLANIR; iki ucunda da sinir olmayan aday ATLANIR. Esit uzunlukta
     ortusen iki aday: kucuk `start` kazanir (JSON sirasi sonucu
     degistirmez; `test_k1_esit_uzunlukta_*`).
  4. Donus `start` ARTAN sirali `list[TermHit]`; `source_term` METINDEKI
     DILIM (buyuk/kucuk harf metinden, `MARCUS` -> `"MARCUS"`; K2 tam
     esitlik denetimi bunu ister), `target_term` sozlugun ilk harfi
     buyutulmus hedefi (K4), `segment_index=None`, `note` = JSON `not`.
     Indeksler KODPOINT indeksidir (Python `str`), NFC metne gore.

SINIR KURALI (G5/G6, KRT Y1/O1) -- terimin betigine ya da metnin diline
bakilmaz; kelime siniri meta-karakteri KULLANILMAZ (CJK'da Latin terim +
parcacik `Marcusが` hic eslesmezdi). Bir aday ancak HER IKI UCUNDA sinir
varsa eslesir. Sinir:
  - metin ucu · bosluk (`str.isspace`, ideografik bosluk dahil) ·
    Unicode noktalama (kategori `P*`: `.,!?、。「」()[]{}“”'-…` ...);
  - JP parcacik `をがはにのでともへや` (iki tarafta: `村は`, `が村に`);
  - KR ek `을 를 이 가 은 는 에 에서 으로 로 와 과 도 의 만 께서 부터 까지`
    -- yalniz SAG tarafta, en uzun once, ve EKTEN SONRA DA SINIR gerekir
    (`방앗간을 지나` evet, `방앗간도둑` hayir: `도`+`둑`). Ek zinciri en fazla
    IKI ek (`방앗간에서는`, `방앗간까지는.` evet; uc ek hayir) -- paketin
    "ekten sonra da sinir" kurali ozyineli okunmustur, `_KR_EK_ZINCIRI`;
  - sozlukteki BASKA bir terimin baslangici (sagda) ya da bitisi (solda):
    `長老マルクス` -> iki hit. Komsu terimin kendisinin KABUL edilmesi
    gerekmez (aday olmasi yeter): `マルクス長老`da uzun terim once islenir,
    kisa komsu henuz kabul edilmemistir, yine sinirdir.
  - korunan araligin (yer tutucu, K3) ucu: `%sマルクス` + `("%s",)` -> hit;
    bildirilmemisken `s` harftir, hit yok.
  Sinir OLMAYANLAR: harf/rakam/kana/kanji/hangul komsusu (`村人`, `剣士`,
  `검사`, `방앗간집`, `真剣に`, `中村`, `windmill`, `elders`, `Marcus2`),
  sembol kategorileri (`S*`) `[ÖLÇÜLMÜYOR]`.
  Bilinen sinir (belgelenir, duzeltilemez): `검은 옷` (siyah giysi) = `검` +
  GERCEK ek `은` -> kural GECER; tek heceli/tek kodpointlik kaynak terim bu
  yuzden semada reddedilir, `kisa_terim_izni: true` ile acik opt-in (K6;
  `real_check` #6c yalniz raporlar).
Olcu: `test_k1_sinir_negatif_eslesmez[*]` (13 ornek), `test_k1_sinir_pozitif_
eslesir[*]` (21), `test_k1_her_jp_parcacik_*` (10), `test_k1_her_kr_ek_*`
(18), `test_k1_en_uzun_once_*`, `test_k1_bitisik_iki_terim_*`,
`test_k1_casefold_tuzagi_*`, `test_k1_ayni_terim_n_gecis_*`.

## K2 -- gomme: aralik disi karakter dokunulmaz; gecersiz hit -> `ContractViolation`

`terimleri_gom(segments, hits) -> tuple[Segment, ...]`: her hit
`segment_index`ine gore gruplanir; grup `start` AZALAN sirayla uygulanir
(indeksler kaymasin -- hedef uzunlugu kaynaktan farkli, `test_k2_iki_hit_
basta_ve_sonda_*` start-artan uygulamayi ayirt eder). Cikti `Segment`
`dataclasses.replace(seg, text=...)`: `bbox/speaker/placeholders/
source_blocks` AYNEN. Hit'i olmayan segment ve `hits` bos -> AYNI nesne
(`is`). Girdi degistirilmez.
Denetim (hepsi `ContractViolation`, sessiz kayma/yutma yok): oge `Segment`
degil · `text` `str` degil · oge `TermHit` degil · `segment_index` `None`/
`bool`/`int` degil/aralik disi (K7) · `start`/`end` `int` degil ·
`0 <= start < end <= len(metin)` degil (`start == end` dahil) ·
`metin[start:end] != source_term` (TAM esitlik; iki taraf da NFC) · iki hit
ortusur (`a.end > b.start`; bitisik `==` serbest) · hit segmentin
`placeholders`indan biriyle ortusur (K3) · `target_term` bos/`str` degil.
Hata mesajlari yalniz sayi ve tip adi tasir; kaynak metin, terim ve dilim
ASLA (PROTOKOL 7; `test_k2_hata_mesajlari_metin_tasimaz[*]`).
Olcu: `test_k2_*`, `test_k7_*`.

## K3 -- terim yer tutucu ile cakismaz (KRT Y2)

`placeholders` icindeki her dizenin metindeki TUM gecisleri (tam alt dize,
buyuk/kucuk duyarli, ortusmesiz tarama) korunan araliktir; onlarla (kismen
de olsa) ortusen aday eslesmez: `{PLAYER}は村にいます` + `("{PLAYER}",)` ->
hit yok; `placeholders=()` iken `{`/`}` `P*` sinirdir ve `PLAYER` eslesir
(pozitif kontrol). `{0}マルクス` -> `マルクス` eslesir, `{0}` dokunulmaz.
`terimleri_gom` `segment.placeholders`i AYNI kurala gore denetler: ortusen
hit -> `ContractViolation` (dusurme degil). Bos dize yok sayilir; duz `str`
ya da `str` olmayan oge -> `TypeError`. Yer tutucu bilgisi YALNIZ cagirandan
gelir (T-007 K3 ile ayni ilke): bildirilmemis `{PLAYER}` metindir.
Olcu: `test_k3_*`, `test_k1_yer_tutucu_ucu_sinirdir`; `real_check` #3a-c.

## K4 -- hedef her zaman ilk harfi BUYUK gomulur (G7, Y3)

JP kaynakta kucuk harfli cins isim (`değirmen`) motorda KAYBOLUYOR (G7);
buyuk harf 21/21 korundu. `ilk_harfi_buyut`: ilk kodpoint `upper()`, Turkce
`i` -> `İ` (hedef dili Turkce; `ihtiyar` -> `İhtiyar`, `ışık` -> `Işık`);
gerisi aynen, zaten buyukse aynen, harf degilse aynen. Iki yerde: yukleme
(`SozlukTerimi.hedef` ve `TermHit.target_term` buyuk) VE `terimleri_gom`
(elle kurulan hit de buyuk gomulur). Motorun ozel-ad kesme isareti
(`Değirmen'de`) kozmetik, `[ÖLÇÜLMÜYOR]` (`real_check` #5 raporlar).
`ozel_ad` bayragi YOK; serbest `not` alani `TermHit.note`ya gider.
Sinir `[ÖLÇÜLMÜYOR]`: kucuk `i` ile baslamasi gereken hedef (marka adi gibi)
da `İ` ile buyutulur -- paket her hedefi buyutmeyi zorunlu kilar (G7).
Olcu: `test_k4_*`.

## K5 -- saf, deterministik, hizli

`lookup`, `lookup_segments`, `terimleri_gom`, `ilk_harfi_buyut` I/O yapmaz,
import etmez, modul duzeyinde degisken durum yok (yalniz `Final` sabitler);
dosya YALNIZ `GlossaryStore.__init__`te okunur (yeniden yukleme yok: yeni
profil = yeni `GlossaryStore`; dosya sonradan silinse lookup calisir).
Ayni girdi -> esit cikti (yeni liste). Butce: 1000 segment x 50 terim,
`lookup_segments` + `terimleri_gom` medyan < 50 ms; olculdu 15-17 ms, kapinin
yolu (`lookup` + `dataclasses.replace`) 18-21 ms, terim sayisindan bagimsiz
(11 / 50 / 500 terim ayni; `evidence/sure-olcumu.txt`). Kapsam izleyicisi
(C tracer) aktifken Python satirlari ~4x yavaslar; sure testleri o kosumda
butceyi 4x alir, gercek butce izleyicisiz kosumda ve `real_check` #7'de
olculur. Hicbir kanala (stdout/stderr/logging/warnings) metin yazilmaz;
`repr` terim basmaz (yalniz sayi + dosya adi). Olcu: `test_k5_*`;
`real_check` #7.

## K6 -- yukleme, sema ve hata

`GlossaryStore(json_path)`: `Path` ya da `str` (baskasi `TypeError`); dosya
BAYT ile okunur ve `json.loads(bayt)` ile cozulur (UTF-8 BOM cozulur, KRT
D4; ASCII-disi yol calisir). Dosya yoksa `FileNotFoundError` SARILMAZ
(model dosyasi degil, `ModelMissingError` yanlis sinif olurdu); diger
`OSError`ler de aynen gecer. Bozuk JSON -> `ValueError` (dosya adi mesajda).
Sema `{"terimler": [{"kaynak": str, "hedef": str, "not": str|null?,
"kisa_terim_izni": bool?}]}`; ust duzeyde ek anahtar (profil meta verisi)
SERBEST, kayit duzeyinde bilinmeyen anahtar RED (`ozel_ad` v1 bayragi ve
yazim hatalari sessizce yutulmaz). `kaynak`/`hedef` NFC'lenir. Red
(`ValueError`, mesajda terim ya da alan adi; ILK hatali kayit bildirilir):
  - `kaynak`/`hedef` eksik, `str` degil, bos/yalniz bosluk, bas/son bosluklu;
  - `kaynak` NFC sonrasi TEK KODPOINT (tek hangul hecesi, tek kanji, tek
    kana, tek Latin harf -- sinir kurali ayristiramaz, `검은`) ve
    `kisa_terim_izni` `true` degil (paket "tek hangul/tek kanji" der; kural
    tum tek kodpointlere genisletildi, gerekce ayni);
  - tekrar eden `kaynak` (esleme semantigiyle: `Marcus`/`MARCUS`,
    `istanbul`/`İstanbul`, NFC/NFD ayni terim);
  - `hedef`te cumle sonu isareti `.!?。！？` (T-007 K3 kumesi; `St. Marcus`
    cumleyi boler, motor uydurur -- KRT O5) ya da `{`/`}` (yer tutucu bicimi);
  - `not` `str`/`null` degil; `kisa_terim_izni` `bool` degil (`1` de red).
`terimler` ozelligi uzunluk-azalan sirali `tuple[SozlukTerimi, ...]`
(`hedef` buyutulmus, `kaynak` NFC), `len(store)` terim sayisi, `yol`.
Olcu: `test_k6_*` (her red sinifi ayri kimlikle; alti terminator ayri).

## K7 -- `segment_index` denetimi

`terimleri_gom`a gelen hit'in `segment_index`i `None`, `bool`, `int` degil
ya da `[0, len(segments))` disi -> `ContractViolation`; bir hit gecersizse
cagri BUTUNUYLE duser, kismi cikti yok. Olcu: `test_k7_*`.

Loglama (PROTOKOL 7): bu modulde stdout/stderr/logging/warnings YOK.
Thread-safe: `GlossaryStore` yuklemeden sonra degismezdir, paylasilabilir.
"""
from __future__ import annotations

import dataclasses
import json
import re
import unicodedata
from collections.abc import Sequence
from pathlib import Path
from typing import Final, TypeAlias

from src.contracts.errors import ContractViolation
from src.contracts.models import Segment, TermHit

__all__ = ["GlossaryStore", "SozlukTerimi", "terimleri_gom", "ilk_harfi_buyut"]


_NFC: Final = "NFC"
_JP_PARCACIKLAR: Final = frozenset("をがはにのでともへや")
"""K1 (G6): JP parcaciklar -- terimin iki yaninda da sinir."""
_KR_EKLER: Final[tuple[str, ...]] = tuple(
    sorted(
        ("을", "를", "이", "가", "은", "는", "에", "에서", "으로", "로", "와", "과", "도", "의", "만", "께서", "부터", "까지"),
        key=len,
        reverse=True,
    )
)
"""K1 (G6): KR ekler, en uzun once; yalniz SAG sinir, ekten sonra da sinir gerekir."""
_KR_EK_ZINCIRI: Final = 2
"""K1: art arda en fazla bu kadar ek (`에서는`, `까지는`)."""
_CUMLE_SONU: Final = ".!?。！？"
"""K6: hedefte yasak -- T-007 K3'un evrensel cumle sonu kumesiyle AYNI (bolmeyi tetikler)."""
_YER_TUTUCU_AYRACLARI: Final = "{}"
"""K6: hedefte yasak -- yer tutucu bicimi (T-007 K5 onarimiyla cakisir)."""
_ANAHTAR_TERIMLER: Final = "terimler"
_ANAHTAR_KAYNAK: Final = "kaynak"
_ANAHTAR_HEDEF: Final = "hedef"
_ANAHTAR_NOT: Final = "not"
_ANAHTAR_IZIN: Final = "kisa_terim_izni"
_KAYIT_ANAHTARLARI: Final = frozenset({_ANAHTAR_KAYNAK, _ANAHTAR_HEDEF, _ANAHTAR_NOT, _ANAHTAR_IZIN})


@dataclasses.dataclass(frozen=True)
class SozlukTerimi:
    """Yuklenmis bir sozluk kaydi: `kaynak` NFC, `hedef` NFC + ilk harfi buyuk (K4)."""

    kaynak: str
    hedef: str
    note: str | None = None
    """JSON `not` alani -- `TermHit.note`ya gider (cevirmene serbest talimat)."""
    kisa_terim_izni: bool = False
    """K6: tek kodpointlik kaynak icin acik opt-in."""


# ---------------------------------------------------------------------------
# yardimcilar: buyutme / NFC / sinir / araliklar
# ---------------------------------------------------------------------------


def ilk_harfi_buyut(metin: str) -> str:
    """K4: ilk kodpoint buyuk (Turkce `i` -> `İ`), gerisi aynen; bos/harf-disi aynen."""
    if not metin:
        return metin
    ilk = metin[0]
    if ilk == "i":
        return "İ" + metin[1:]
    return ilk.upper() + metin[1:]


def _nfc(metin: str) -> str:
    return unicodedata.normalize(_NFC, metin)


def _sinir_karakteri(ch: str) -> bool:
    """K1: bosluk, Unicode noktalama (`P*`) ya da JP parcacik."""
    return ch.isspace() or unicodedata.category(ch).startswith("P") or ch in _JP_PARCACIKLAR


def _ortusur(start: int, end: int, araliklar: Sequence[tuple[int, int]]) -> bool:
    for a, b in araliklar:
        if start < b and a < end:
            return True
    return False


def _korunan_araliklar(metin: str, yer_tutucular: Sequence[str]) -> list[tuple[int, int]]:
    """K3: her yer tutucunun metindeki TUM gecisleri (tam alt dize, ortusmesiz tarama)."""
    sonuc: list[tuple[int, int]] = []
    for yt in yer_tutucular:  # bos dize `_yer_tutuculari_dogrula`da atildi
        i = metin.find(yt)
        while i != -1:
            sonuc.append((i, i + len(yt)))
            i = metin.find(yt, i + len(yt))
    return sonuc


def _yer_tutuculari_dogrula(yer_tutucular: object) -> tuple[str, ...]:
    """K3: `str` dizisi (duz `str` DEGIL); bos dize atilir; NFC."""
    if isinstance(yer_tutucular, (str, bytes)) or not isinstance(yer_tutucular, Sequence):
        raise TypeError(f"placeholders bir str dizisi olmali, gelen: {type(yer_tutucular).__name__}")
    sonuc: list[str] = []
    for yt in yer_tutucular:
        if not isinstance(yt, str):
            raise TypeError(f"placeholders ogesi str olmali, gelen: {type(yt).__name__}")
        if yt:
            sonuc.append(_nfc(yt))
    return tuple(sonuc)


class _SinirBaglami:
    """K1 sinir denetimi icin bir metnin sabit baglami (sicak yol: `__slots__`, dataclass degil).

    `terim_baslari`/`terim_bitisleri`: sozlukteki HERHANGI bir terimin metinde
    basladigi/bittigi konumlar (kabul edilmesi gerekmez). `yt_baslari`/
    `yt_bitisleri`: korunan araliklarin (yer tutucu) uclari.
    """

    __slots__ = ("metin", "terim_baslari", "terim_bitisleri", "yt_baslari", "yt_bitisleri")

    def __init__(
        self,
        metin: str,
        terim_baslari: set[int],
        terim_bitisleri: set[int],
        korunan: Sequence[tuple[int, int]],
    ) -> None:
        self.metin = metin
        self.terim_baslari = terim_baslari
        self.terim_bitisleri = terim_bitisleri
        self.yt_baslari = {a for a, _ in korunan}
        self.yt_bitisleri = {b for _, b in korunan}

    def sol(self, start: int) -> bool:
        """Terimden ONCE sinir var mi."""
        return (
            start == 0
            or _sinir_karakteri(self.metin[start - 1])
            or start in self.terim_bitisleri
            or start in self.yt_bitisleri
        )

    def _sag_temel(self, end: int) -> bool:
        return (
            end == len(self.metin)
            or _sinir_karakteri(self.metin[end])
            or end in self.terim_baslari
            or end in self.yt_baslari
        )

    def _kr_ek_sonrasi(self, konum: int, derinlik: int) -> bool:
        """K1 (G6): ek (en uzun once) + EKTEN SONRA sinir; en fazla `derinlik` ek zinciri."""
        if derinlik <= 0:
            return False
        for ek in _KR_EKLER:
            if self.metin.startswith(ek, konum):
                sonrasi = konum + len(ek)
                if self._sag_temel(sonrasi) or self._kr_ek_sonrasi(sonrasi, derinlik - 1):
                    return True
        return False

    def sag(self, end: int) -> bool:
        """Terimden SONRA sinir var mi (KR ek zinciri dahil)."""
        return self._sag_temel(end) or self._kr_ek_sonrasi(end, _KR_EK_ZINCIRI)


# ---------------------------------------------------------------------------
# yukleme ve sema (K6)
# ---------------------------------------------------------------------------


def _metin_alani(kayit: dict[str, object], anahtar: str, etiket: str) -> str:
    """K6: zorunlu `str` alan -- eksik, `str` degil, bos, bas/son bosluklu -> `ValueError`."""
    if anahtar not in kayit:
        raise ValueError(f"sozluk semasi: {etiket}: '{anahtar}' alani eksik")
    deger = kayit[anahtar]
    if not isinstance(deger, str):
        raise ValueError(f"sozluk semasi: {etiket}: '{anahtar}' str olmali, gelen: {type(deger).__name__}")
    if not deger.strip():
        raise ValueError(f"sozluk semasi: {etiket}: '{anahtar}' bos")
    if deger != deger.strip():
        raise ValueError(f"sozluk semasi: {etiket}: '{anahtar}' bas/son bosluk tasiyor: {deger!r}")
    return _nfc(deger)


def _kaydi_dogrula(indeks: int, ham: object) -> SozlukTerimi:
    """K6: tek kayit -> `SozlukTerimi`; her red sinifi terim adiyla `ValueError`."""
    if not isinstance(ham, dict):
        raise ValueError(f"sozluk semasi: terim kaydi #{indeks} bir JSON nesnesi degil: {type(ham).__name__}")
    kayit: dict[str, object] = {str(k): v for k, v in ham.items()}
    kaynak = _metin_alani(kayit, _ANAHTAR_KAYNAK, f"terim kaydi #{indeks}")
    etiket = f"terim {kaynak!r}"
    fazla = sorted(set(kayit) - _KAYIT_ANAHTARLARI)
    if fazla:
        raise ValueError(f"sozluk semasi: {etiket}: bilinmeyen anahtar(lar) {fazla}; izinli: {sorted(_KAYIT_ANAHTARLARI)}")
    hedef = _metin_alani(kayit, _ANAHTAR_HEDEF, etiket)
    for ch in hedef:
        if ch in _CUMLE_SONU:
            raise ValueError(f"sozluk semasi: {etiket}: hedef cumle sonu isareti iceremez ({_CUMLE_SONU}); bolmeyi tetikler")
        if ch in _YER_TUTUCU_AYRACLARI:
            raise ValueError(f"sozluk semasi: {etiket}: hedef yer tutucu ayraci iceremez ({_YER_TUTUCU_AYRACLARI})")
    not_ = kayit.get(_ANAHTAR_NOT)
    if not_ is not None and not isinstance(not_, str):
        raise ValueError(f"sozluk semasi: {etiket}: 'not' str ya da null olmali, gelen: {type(not_).__name__}")
    izin = kayit.get(_ANAHTAR_IZIN, False)
    if not isinstance(izin, bool):
        raise ValueError(f"sozluk semasi: {etiket}: '{_ANAHTAR_IZIN}' bool olmali, gelen: {type(izin).__name__}")
    if len(kaynak) == 1 and not izin:
        raise ValueError(
            f"sozluk semasi: {etiket}: tek kodpointlik kaynak terim (tek hangul hecesi / tek kanji / tek harf) "
            f"sinir kuraliyla bilesiklerden ayristirilamaz; bilincli kabul icin '{_ANAHTAR_IZIN}': true"
        )
    return SozlukTerimi(kaynak=kaynak, hedef=ilk_harfi_buyut(hedef), note=not_, kisa_terim_izni=izin)


def _terimleri_yukle(yol: Path) -> tuple[SozlukTerimi, ...]:
    """K6: dosya BAYT ile okunur, `json.loads(bayt)` (BOM cozulur); `FileNotFoundError` sarilmaz."""
    ham = yol.read_bytes()
    try:
        veri: object = json.loads(ham)
    except ValueError as e:
        raise ValueError(f"sozluk JSON ayristirilamadi ({yol.name}): {e}") from e
    if not isinstance(veri, dict) or _ANAHTAR_TERIMLER not in veri:
        raise ValueError(f"sozluk semasi ({yol.name}): ust duzey '{_ANAHTAR_TERIMLER}' listesi tasiyan bir JSON nesnesi olmali")
    kayitlar = veri[_ANAHTAR_TERIMLER]
    if not isinstance(kayitlar, list):
        raise ValueError(f"sozluk semasi ({yol.name}): '{_ANAHTAR_TERIMLER}' bir liste olmali, gelen: {type(kayitlar).__name__}")
    return tuple(_kaydi_dogrula(i, k) for i, k in enumerate(kayitlar))


def _anahtar(metin: str) -> str:
    """IGNORECASE denkligiyle ortusen kanonik anahtar: casefold + Turkce I sinifi (`i/I/İ/ı`) tek harf (olculdu, K1)."""
    return metin.casefold().replace("i\u0307", "i").replace("ı", "i")


_TrieDugumu: TypeAlias = dict[str, "_TrieDugumu"]
_TERMINAL: Final = ""


def _trie_anahtari(ch: str) -> str:
    """Trie dugum anahtari: tek kodpointe katlanabilen karakter katlanir (`M`/`m` -> `m`, `İ`/`I`/`ı` -> `i`).

    IGNORECASE altinda `Marcus` ve `marcus aurelius` AYNI dalda olmali; dal harf
    durumuna gore ayrilirsa ilk dal kazanir ve uzun terim kacar. Katlama coklu
    kodpoint uretirse (`ß` -> `ss`) karakter oldugu gibi kalir (IGNORECASE zaten esler).
    """
    k = _anahtar(ch)
    return k if len(k) == 1 else ch


def _trie_govdesi(dugum: _TrieDugumu) -> str:
    """Trie -> regex govdesi. Terminal dugumde cocuklar `(?:...)?` ile ONCE denenir -> konumdaki EN UZUN terim."""
    dallar = [re.escape(ch) + _trie_govdesi(alt) for ch, alt in dugum.items() if ch != _TERMINAL]
    if not dallar:
        return ""
    if _TERMINAL in dugum:
        return "(?:" + "|".join(dallar) + ")?"
    return dallar[0] if len(dallar) == 1 else "(?:" + "|".join(dallar) + ")"


def _tarama_deseni(terimler: Sequence[SozlukTerimi]) -> re.Pattern[str]:
    """K1/K5: ileri-bakisli TRIE deseni; `group(1)` = konumdan baslayan en uzun terimin metindeki dilimi.

    Duz alternation her konumda her terimi dener (50 terim: 28 ms, 500 terim:
    300+ ms / 1000 segment). Trie'de bir konumda yalniz ilk karakteri tutan
    dal yurur; onde ilk-karakter kumesi bekcisi (IGNORECASE kumeye de
    uygulanir). Maliyet terim sayisindan bagimsiz (500 terimde de ~13 ms).
    Dugum anahtarlari katlanmis karakterdir (`_trie_anahtari`); IGNORECASE
    literal karsilastirmayi ustlenir.
    """
    kok: _TrieDugumu = {}
    for t in terimler:
        dugum = kok
        for ch in t.kaynak:
            dugum = dugum.setdefault(_trie_anahtari(ch), {})
        dugum[_TERMINAL] = {}
    ilk_karakterler = "".join(sorted(kok))
    return re.compile(f"(?=[{re.escape(ilk_karakterler)}])(?=({_trie_govdesi(kok)}))", re.IGNORECASE)


class GlossaryStore:
    """Oyun profili basina terim sozlugu; JSON'dan yuklenir, sonra DEGISMEZ (K5/K6).

    `lookup(text, placeholders)` -> `list[TermHit]` (K1/K3), `lookup_segments`
    `segment_index` doldurur, `terimler`/`len` yuklenmis kayitlar.
    """

    def __init__(self, json_path: Path | str) -> None:
        if isinstance(json_path, str):
            json_path = Path(json_path)
        if not isinstance(json_path, Path):
            raise TypeError(f"json_path Path ya da str olmali, gelen: {type(json_path).__name__}")
        self._yol: Path = json_path
        ham = _terimleri_yukle(json_path)
        # K1: uzunluk azalan, esitlikte JSON sirasi (kararli sort).
        self._terimler: tuple[SozlukTerimi, ...] = tuple(sorted(ham, key=lambda t: -len(t.kaynak)))
        self._anahtarlar: dict[str, int] = self._anahtarlari_kur()
        self._desen: re.Pattern[str] | None = _tarama_deseni(self._terimler) if self._terimler else None
        self._onekler: tuple[tuple[int, ...], ...] = self._onekleri_hesapla()

    # -- yukleme sonrasi kurulum -------------------------------------------------

    def _anahtarlari_kur(self) -> dict[str, int]:
        """K6: kanonik anahtar -> terim indeksi; ayni anahtara ikinci kaynak (`Marcus`/`MARCUS`, `istanbul`/`İstanbul`) -> `ValueError`."""
        anahtarlar: dict[str, int] = {}
        for i, t in enumerate(self._terimler):
            k = _anahtar(t.kaynak)
            if k in anahtarlar:
                raise ValueError(
                    f"sozluk semasi: terim {t.kaynak!r}: tekrar eden kaynak ({self._terimler[anahtarlar[k]].kaynak!r} ile ayni)"
                )
            anahtarlar[k] = i
        return anahtarlar

    def _indeks(self, dilim: str) -> int | None:
        """Metindeki dilim (ya da bir terimin oneki) -> terim indeksi, kanonik anahtarla.

        `_anahtar`, IGNORECASE'in denk saydigi 1514 kodpoint ciftinin hepsinde
        ayni anahtari verir (tum Unicode tarandi: `evidence/olcum-anahtar-
        ignorecase-denkligi.txt`); yedek tarama gerekmez.
        """
        j = self._anahtarlar.get(_anahtar(dilim))
        if j is not None and len(self._terimler[j].kaynak) == len(dilim):
            return j
        return None

    def _onekleri_hesapla(self) -> tuple[tuple[int, ...], ...]:
        """K1: her terim icin, ayni konumda baslayabilen DAHA KISA terimlerin indeksleri (onekleri)."""
        uzunluklar = sorted({len(t.kaynak) for t in self._terimler})
        sonuc: list[tuple[int, ...]] = []
        for t in self._terimler:
            onekler: list[int] = []
            for n in uzunluklar:
                if n >= len(t.kaynak):
                    break
                j = self._indeks(t.kaynak[:n])
                if j is not None:
                    onekler.append(j)
            sonuc.append(tuple(onekler))
        return tuple(sonuc)

    # -- ozellikler --------------------------------------------------------------

    @property
    def yol(self) -> Path:
        return self._yol

    @property
    def terimler(self) -> tuple[SozlukTerimi, ...]:
        """Uzunluk-azalan sirali kayitlar (`kaynak` NFC, `hedef` ilk harfi buyuk)."""
        return self._terimler

    def __len__(self) -> int:
        return len(self._terimler)

    def __repr__(self) -> str:
        return f"GlossaryStore(terim_sayisi={len(self._terimler)}, dosya={self._yol.name!r})"

    # -- esleme (K1/K3) ------------------------------------------------------------

    def lookup(self, text: str, placeholders: Sequence[str] = ()) -> list[TermHit]:
        """K1/K3: metindeki terim eslemeleri, `start` artan; `segment_index=None`.

        `text` NFC'lenir; indeksler NFC metne gore kodpoint. `placeholders`
        gecisleri korunur ve uclari sinir sayilir. Saf: I/O yok, durum yok.
        """
        if not isinstance(text, str):
            raise TypeError(f"text str olmali, gelen: {type(text).__name__}")
        return self._ara(text, _yer_tutuculari_dogrula(placeholders), None)

    def _ara(self, text: str, yer_tutucular: tuple[str, ...], segment_index: int | None) -> list[TermHit]:
        """`lookup`un govdesi; `segment_index` dogrudan yazilir (`lookup_segments` kopyasiz)."""
        if self._desen is None or not text:
            return []
        metin = _nfc(text)
        korunan = _korunan_araliklar(metin, yer_tutucular)

        adaylar: list[tuple[int, int, int]] = []  # (-uzunluk, start, terim indeksi)
        baslar: set[int] = set()
        bitisler: set[int] = set()
        for m in self._desen.finditer(metin):
            start = m.start()
            en_uzun = self._indeks(m.group(1))
            if en_uzun is None:  # pragma: no cover -- trie yalniz sozluk terimlerini uretir
                continue
            for j in (en_uzun, *self._onekler[en_uzun]):
                n = len(self._terimler[j].kaynak)
                adaylar.append((-n, start, j))
                baslar.add(start)
                bitisler.add(start + n)
        if not adaylar:
            return []
        adaylar.sort()

        baglam = _SinirBaglami(metin, baslar, bitisler, korunan)
        kabul: list[tuple[int, int]] = []
        hits: list[TermHit] = []
        for eksi_uzunluk, start, j in adaylar:
            end = start - eksi_uzunluk
            if _ortusur(start, end, kabul) or _ortusur(start, end, korunan):
                continue
            if not (baglam.sol(start) and baglam.sag(end)):
                continue
            kabul.append((start, end))
            t = self._terimler[j]
            hits.append(
                TermHit(
                    source_term=metin[start:end],
                    target_term=t.hedef,
                    start=start,
                    end=end,
                    segment_index=segment_index,
                    note=t.note,
                )
            )
        hits.sort(key=lambda h: h.start)
        return hits

    def lookup_segments(self, segments: Sequence[Segment]) -> tuple[TermHit, ...]:
        """Her segmentin `text`/`placeholders`i ile `lookup`; `segment_index` dolu; segment sirasi, sonra `start`."""
        hits: list[TermHit] = []
        for i, seg in enumerate(segments):
            if not isinstance(seg, Segment) or not isinstance(seg.text, str):
                raise ContractViolation(f"segments[{i}] Segment degil ya da text str degil: {type(seg).__name__}")
            hits.extend(self._ara(seg.text, _yer_tutuculari_dogrula(seg.placeholders), i))
        return tuple(hits)


# ---------------------------------------------------------------------------
# gomme (K2/K3/K4/K7)
# ---------------------------------------------------------------------------


def _segment_indeksi(hit: TermHit, sira: int, n: int) -> int:
    """K7: `None`/`bool`/`int` degil/aralik disi -> `ContractViolation`."""
    i = hit.segment_index
    if i is None or isinstance(i, bool) or not isinstance(i, int):
        raise ContractViolation(f"hits[{sira}].segment_index gecersiz: {type(i).__name__} (int, [0, {n}) bekleniyor)")
    if not 0 <= i < n:
        raise ContractViolation(f"hits[{sira}].segment_index aralik disi: {i} (segment sayisi {n})")
    return i


def _hitleri_dogrula(metin: str, grup: Sequence[tuple[int, TermHit]], korunan: Sequence[tuple[int, int]]) -> list[TermHit]:
    """K2/K3: tek segmentin hit'leri -- aralik, tam esitlik, ortusme, yer tutucu; `start` ARTAN sirali doner."""
    n = len(metin)
    for sira, h in grup:
        if not isinstance(h.start, int) or not isinstance(h.end, int) or isinstance(h.start, bool) or isinstance(h.end, bool):
            raise ContractViolation(f"hits[{sira}]: start/end int olmali")
        if not 0 <= h.start < h.end <= n:
            raise ContractViolation(f"hits[{sira}]: aralik gecersiz [{h.start}, {h.end}) (metin uzunlugu {n})")
        if not isinstance(h.source_term, str) or metin[h.start : h.end] != _nfc(h.source_term):
            raise ContractViolation(f"hits[{sira}]: source_term metnin [{h.start}, {h.end}) dilimiyle ayni degil")
        if not isinstance(h.target_term, str) or not h.target_term:
            raise ContractViolation(f"hits[{sira}]: target_term bos ya da str degil")
        if _ortusur(h.start, h.end, korunan):
            raise ContractViolation(f"hits[{sira}]: aralik [{h.start}, {h.end}) bir yer tutucuyla ortusuyor")
    sirali = sorted(grup, key=lambda c: c[1].start)
    for (sira_a, a), (sira_b, b) in zip(sirali, sirali[1:]):
        if a.end > b.start:
            raise ContractViolation(f"hits[{sira_a}] ve hits[{sira_b}] ortusuyor: [{a.start}, {a.end}) / [{b.start}, {b.end})")
    return [h for _, h in sirali]


def terimleri_gom(segments: Sequence[Segment], hits: Sequence[TermHit]) -> tuple[Segment, ...]:
    """K2: her hit araligini ilk harfi buyuk `target_term` ile degistirir; aralik disi karakter aynen.

    Hit'i olmayan segment ve bos `hits` -> ayni nesne (`is`). Gecersiz hit
    (K2/K3/K7) -> `ContractViolation`, cagri butunuyle duser.
    """
    segs = tuple(segments)
    if not hits:
        return segs
    n = len(segs)
    gruplar: dict[int, list[tuple[int, TermHit]]] = {}
    for sira, h in enumerate(hits):
        if not isinstance(h, TermHit):
            raise ContractViolation(f"hits[{sira}] TermHit degil: {type(h).__name__}")
        gruplar.setdefault(_segment_indeksi(h, sira, n), []).append((sira, h))

    cikti = list(segs)
    for i, grup in gruplar.items():
        seg = segs[i]
        if not isinstance(seg, Segment) or not isinstance(seg.text, str):
            raise ContractViolation(f"segments[{i}] Segment degil ya da text str degil: {type(seg).__name__}")
        metin = _nfc(seg.text)
        korunan = _korunan_araliklar(metin, _yer_tutuculari_dogrula(seg.placeholders))
        for h in reversed(_hitleri_dogrula(metin, grup, korunan)):  # start AZALAN: indeksler kaymaz
            metin = metin[: h.start] + ilk_harfi_buyut(_nfc(h.target_term)) + metin[h.end :]
        cikti[i] = dataclasses.replace(seg, text=metin)
    return tuple(cikti)
