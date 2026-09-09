"""ChangeDetector -- algisal hash + kararlilik (debounce).

Tasarim dokumani 2.2 (adim 4-5) ve 5.7'nin uygulamasi (gorev T-002). Mod 2'nin
canli dongusundeki ilk savunma hatti: bolge her ~250 ms yakalanir, bu sinif
"hicbir sey degismedi" derse pipeline'in geri kalani (OCR, ceviri) hic
calismaz -- CPU ve maliyet tam olarak burada kurtarilir.

Algoritma -- dHash (difference hash):
  1. BGR goruntu tek kanal gri tona indirgenir (ITU-R BT.601 luma agirliklari,
     BGR sirasina gore).
  2. Gri goruntu `hash_size` x `hash_size + 1` hucreye BLOK-ORTALAMA ile
     kucultulur (komsu piksel gurultusunu yumusatir). Piksel-piksel
     karsilastirma BILEREK kullanilmadi -- gorev paketi bunu acikca
     yasakliyor: "sikistirma gurultusu ve tek piksellik oynamalar yanlis
     pozitif uretir". En yakin komsu ornekleme de ayni riski tasirdi; blok
     ortalamasi PIL/cv2 olmadan (yalnizca stdlib+numpy izinli) basit bir
     "area resize" esdegeridir.
  3. Her satirda komsu hucreler karsilastirilir (sol < sag -> bit 1); sonuc
     `hash_size * hash_size` bitlik bir tamsayidir (Python `int`, kesin
     buyuklukte -- tasma riski yok).

Kararlilik / debounce -- tasarim 2.2 adim 5:
  Yeni karenin hash'i, son ONAYLANMIS (kararli) hash'ten Hamming mesafesi
  bakimindan esik disindaysa bir "aday degisiklik" baslar. Aday, ardisik
  `stable_frames` karede (kendi aralarinda esik ici) tekrar goruldukten
  sonra KARARLI sayilir ve `has_changed` `True` doner. Boylece harf harf
  yazilan bir metin yari yazilmisken OCR'a girip cop ceviri uretmez.

  Tasarim dokumaninin ACIKCA belirtmedigi iki karar (teslim raporunda
  `known_gaps` altinda da bildirilmistir):
    (a) "Ayni hash" debounce kosulu, yeni bir kesin-esitlik kavrami yerine
        AYNI esik/Hamming karsilastirmasiyla uygulanir (hem taban-fark hem
        aday-eslesme icin tek bir `_similar` iliskisi). Boylece esik,
        sistemde tutarli tek bir "esitlik" anlamina gelir; kesin bit-esitligi
        kullanilsaydi, sonsuz kucuk artik gurultu debounce'un hic
        onaylanmamasina (canli kilitlenme) yol acabilirdi.
    (b) Aday surerken icerik taban (son kararli) hash'e geri donerse
        bekleyen aday IPTAL edilir (sifirlanir). Aksi halde eski bir aday
        sayaci, alakasiz bir sonraki degisiklige "tasinmis" gibi yanlis
        onay verebilirdi.

Saflik: bu modul ekran yakalama yapmaz, Windows API cagirmaz, dosya okumaz --
yalnizca kendisine verilen `Frame` uzerinde calisir. Yalnizca stdlib ve
numpy kullanir; `Frame`/`Rect`/`ImageArray` sozlesmelerine yalnizca
kullanici olarak dokunur, degistirmez.

Kucuk bolge davranisi (T-002 TUR 2 duzeltmesi -- bkz. .agents/tasks/T-002/
feedback.md):
  Tur 1'de `_block_mean_resize`, hedef izgara (`hash_size` x `hash_size+1`,
  varsayilan 8x9) girdi bolgesinden BUYUKse (`h < 8` veya `w < 9`)
  `np.add.reduceat` icin cakisan kova sinirlari uretiyordu: `h/w < 5`
  bandinda `IndexError` ile COKUYOR, `5 <= h/w < hash_size (+1)` bandinda
  sessizce `0/0` -> `NaN` uretiyordu (karsilastirmalar `NaN` ile hep `False`
  doner, yani ilgili hash bitleri donetlenemez sekilde sabitlenirdi).
  Tasarim dokumani (Suflor) SS2.2 kullanicinin yakalama bolgesini serbestce
  yeniden boyutlandirabilecegini soyluyor -- kucuk bir bolge (bir sayac, bir
  rozet, tek satirlik bir etiket) GECERLI bir kullanim, cokme kabul edilemez.

  Secilen duzeltme: izgarayi bolgeye gore KUCULT. `_block_mean_resize` artik
  hedef hucre sayisini girdinin kendi boyutuyla sinirlar
  (`eff_out_h = min(out_h, h)`, `eff_out_w = min(out_w, w)`). Bu kirpma
  matematiksel olarak kova basina en az 1 piksel garanti eder (bkz. fonksiyon
  docstring'i) -- hem `IndexError` hem `NaN` yapisal olarak imkansiz hale
  gelir, HERHANGI bir bolge boyutu icin. Gercekci bolgeler (>= 8x9, pratikte
  hep boyle) icin `min(...)` her zaman `out_h`/`out_w`'yi secer -- yani bu
  duzeltme BUYUK bolgelerde davranisi degistirmez (debounce, esik, bolge
  sifirlama, butce -- hepsi ayni).

  Sonuc olarak KUCUK bolgelerde hash uzunlugu (`hash_size * hash_size`
  yerine `eff_out_h * (eff_out_w - 1)` bit) kucumektedir; bu, daha az bit
  uzerinden karsilastirma anlamina gelir ve ayni `threshold` daha "toleransli"
  hale gelebilir -- kucuk bolgelerde algilama hassasiyeti dogal olarak
  azalir (ama asla cokme/NaN olmaz, `has_changed` her zaman gecerli bir
  `bool` doner). Ozel bir durum: `w == 1` (tek piksel genislikte bolge)
  icin izgara genisligi de 1'e kirpilir; bu dHash'in yalnizca YATAY komsu
  hucre farkina baktigi icin (bkz. yukaridaki algoritma), tek sutunlu bir
  goruntude karsilastirilacak ikinci bir sutun yoktur -- hash 0 bit uzunlugunda
  olur ve o bolge icin `has_changed` ilk kareden sonra hep `False` doner.
  Bu, implementasyon hatasi degil GEOMETRIK bir sinir (1 piksel genislikte
  yatay turev tanimsizdir); regresyon testinde bu boyut de dahil ("cokme
  yok, NaN yok, bool doner" kriterleriyle sinanir; algilama hassasiyeti
  degil).

Bilinen sinirlar (dHash'in doganda getirdigi, implementasyon hatasi
SAYILMAYAN, tester tarafindan bloke etmeyen not olarak isaretlenen iki
davranis -- .agents/tasks/T-002/feedback.md "Bloke etmeyen notlar"):
  1. Duz renk (tek renkli) tam ekran gecisi (or. tamamen siyahtan tamamen
     beyaza) dHash icin GORUNMEZ kalir: yalnizca yatay-komsu hucre farkina
     bakildigi icin duz bir goruntude her komsu fark esittir (deger ne
     olursa olsun hash hep ayni cikar). Bu, dHash algoritmasinin matematiksel
     bir ozelligidir (aHash de benzer riski tasir), implementasyon hatasi
     degil. Entegrasyon: yakalanan bolge duz renkli bir yuzeyse (nadir --
     oyun metni oyle degildir) degisiklik kacabilir.
  2. Periyodik-dosemeli icerik (or. tekrar eden bir doku/arkaplan) blok-
     ortalamali kucultmeyle birlesince kaydirmaya karsi algilamayi
     korelestirebilir -- periyot izgara hucre boyutuna yakinsa komsu
     hucreler kaydirmadan once/sonra ayni ortalamaya sahip olabilir. Gercek
     oyun metni bu kadar periyodik olmadigi icin pratikte bloke edici
     degildir.
"""
from __future__ import annotations

from typing import Final

import numpy as np
import numpy.typing as npt

from src.contracts.models import Frame, ImageArray, Rect

__all__ = ["ChangeDetector"]


_DEFAULT_HASH_SIZE: Final[int] = 8
_DEFAULT_THRESHOLD: Final[int] = 4
_DEFAULT_STABLE_FRAMES: Final[int] = 2

# ITU-R BT.601 luma agirliklari, BGR sirasina gore (Y = 0.299 R + 0.587 G +
# 0.114 B). float32: hash bit kararlari (esik karsilastirmasi) icin float64
# hassasiyeti gereksiz, float32 olcumde belirgin sekilde daha hizli.
_BGR_LUMA_WEIGHTS: Final[npt.NDArray[np.float32]] = np.array(
    [0.114, 0.587, 0.299], dtype=np.float32
)


def _to_grayscale(image: ImageArray) -> npt.NDArray[np.float32]:
    """BGR uint8 goruntuyu tek kanal float32 luma'ya indirger."""
    gray = image.astype(np.float32) @ _BGR_LUMA_WEIGHTS
    return gray.astype(np.float32)


def _block_mean_resize(
    gray: npt.NDArray[np.float32], out_h: int, out_w: int
) -> npt.NDArray[np.float32]:
    """`gray`'i EN FAZLA (out_h, out_w) hucreye blok-ortalama ile kucultur.

    Tamamen vektorize (Python dongusu yok): satir ve sutunlar
    `np.add.reduceat` ile degisken genislikli kovalara toplanir, sonra kova
    piksel sayisina bolunur. Girdinin boyutlari `out_h`/`out_w`'ye tam
    bolunmese bile (gercek yakalama bolgeleri boyle olur) dogru calisir.

    KUCUK GIRDI GUVENLIGI (T-002 tur 2 duzeltmesi): `np.add.reduceat`
    yalnizca kova sayisi girdi piksel sayisini ASMADIGINDA guvenlidir --
    aksi halde kova sinirlari cakisir ve ya `IndexError` firlatir ya da
    (cakisan sinirlar `np.diff` ile 0 genislik urettiginde) `0/0` -> `NaN`
    sessizce olusur. Bu yuzden donen dizi istenenden KUCUK olabilir: hedef
    hucre sayisi girdinin kendi boyutuna kirpilir --
    `eff_out_h = min(out_h, h)`, `eff_out_w = min(out_w, w)`. Cagiran taraf
    (`_dhash`) bunu hesaba katar. `h >= out_h` ve `w >= out_w` oldugu
    (gercekci yakalama bolgeleri icin hep dogru) durumlarda kirpma devreye
    girmez, davranis oncekiyle BIREBIR aynidir. `h >= 1` ve `w >= 1`
    varsayilir (Frame/Rect sozlesmesi: bos bir goruntu gecerli bir yakalama
    degildir); bu kosul altinda kirpilmis kova sayisi <= piksel sayisi
    esitsizligi, her kovaya en az 1 piksel dusmesini (dolayisiyla `counts`
    hicbir zaman 0 olmamasini) garanti eder -- genis bir aralikta (kova
    sayisi 1..24, piksel sayisi kova sayisina esit veya daha buyuk, 1000'e
    kadar) ampirik olarak dogrulanmistir.
    """
    h, w = gray.shape
    eff_out_h = min(out_h, h)
    eff_out_w = min(out_w, w)

    row_edges = np.linspace(0, h, eff_out_h + 1).round().astype(np.int64)
    col_edges = np.linspace(0, w, eff_out_w + 1).round().astype(np.int64)

    row_sums: npt.NDArray[np.float32] = np.add.reduceat(
        gray, row_edges[:-1], axis=0
    )
    block_sums: npt.NDArray[np.float32] = np.add.reduceat(
        row_sums, col_edges[:-1], axis=1
    )

    row_counts = np.diff(row_edges).astype(np.float32)
    col_counts = np.diff(col_edges).astype(np.float32)
    counts = row_counts[:, None] * col_counts[None, :]

    result: npt.NDArray[np.float32] = block_sums / counts
    return result.astype(np.float32)


def _dhash(image: ImageArray, hash_size: int) -> int:
    """Difference hash: komsu hucre karsilastirmasindan EN FAZLA
    `hash_size**2` bit.

    Adimlar: kucult -> gri tonla -> komsu hucre karsilastir -> bit dizisi.

    Bolge, izgaradan (hash_size x hash_size+1) KUCUKSE `_block_mean_resize`
    daha kucuk bir izgara doner (bkz. o fonksiyonun docstring'i) ve bu
    fonksiyon da orantili olarak DAHA AZ bit uretir (`eff_h * (eff_w - 1)`)
    -- cokme/NaN yerine azaltilmis ama dogru bir sonuc. `w == 1` ozel
    durumunda (yatay komsu yok) 0 bit uretilir, yani o bolge icin hash hep
    ayni (0) kalir -- bkz. modul docstring'i "Kucuk bolge davranisi".
    """
    gray = _to_grayscale(image)
    thumb = _block_mean_resize(gray, hash_size, hash_size + 1)
    diff = thumb[:, 1:] > thumb[:, :-1]
    packed = np.packbits(diff.reshape(-1))
    return int.from_bytes(packed.tobytes(), byteorder="big")


def _hamming_distance(a: int, b: int) -> int:
    """Iki hash arasindaki farkli bit sayisi."""
    return (a ^ b).bit_count()


class ChangeDetector:
    """Bir bolgenin ardisik kareler arasinda KARARLI olarak degisip
    degismedigini bildirir (`has_changed`).

    Parametreler:
      hash_size: dHash izgara boyutu; hash `hash_size ** 2` bit uzunlugunda
        olur. Varsayilan 8 (64 bit).
      threshold: iki hash arasindaki Hamming mesafesi bu degerin altinda
        veya esitse (`<=`) "ayni icerik" sayilir. Varsayilan 4/64 bit --
        sikistirma gurultusune tolerans birakirken gercek bir metin
        degisikligini (genelde onlarca bit farki) kacirmayacak kadar sikidir.
      stable_frames: bir aday degisikligin "olustu" sayilmasi icin gereken
        ardisik (esik ici) kare sayisi. Tasarim 2.2/adim 5 degerini (2)
        varsayilan yapar; ayarlanabilir birakildi.

    Not: `has_changed` SAF bir fonksiyon degildir -- nesne, cagrilar
    arasinda son kararli hash'i ve bekleyen (henuz onaylanmamis) adayi
    durum olarak tutar; bu debounce'un dogasi geregi kacinilmazdir. Disariya
    hicbir yan etkisi yoktur (I/O yok, ekran yakalama yok); yalnizca kendi
    ic durumunu degistirir.
    """

    def __init__(
        self,
        *,
        hash_size: int = _DEFAULT_HASH_SIZE,
        threshold: int = _DEFAULT_THRESHOLD,
        stable_frames: int = _DEFAULT_STABLE_FRAMES,
    ) -> None:
        if hash_size < 1:
            raise ValueError(f"hash_size en az 1 olmali: {hash_size}")
        if threshold < 0:
            raise ValueError(f"threshold negatif olamaz: {threshold}")
        if stable_frames < 1:
            raise ValueError(f"stable_frames en az 1 olmali: {stable_frames}")

        self._hash_size = hash_size
        self._threshold = threshold
        self._stable_frames = stable_frames

        self._last_rect: Rect | None = None
        self._stable_hash: int | None = None
        self._pending_hash: int | None = None
        self._pending_count: int = 0

    def _is_similar(self, a: int, b: int) -> bool:
        return _hamming_distance(a, b) <= self._threshold

    def has_changed(self, frame: Frame) -> bool:
        """`frame`, son bildirilen KARARLI durumdan farkli mi?

        Bolge (`frame.rect`) ilk kez goruluyorsa veya bir onceki cagridan
        farkliysa gecmis gecersiz sayilir: bu kare kosulsuz `True` doner ve
        yeni bir taban alinir (tasarim 2.2 adim 4 / gorev paketi madde 4).

        Aksi halde: yeni karenin hash'i, son kararli hash'ten esik disindaysa
        bir "aday degisiklik" baslar/surer. Aday, ardisik `stable_frames`
        karede (birbirine gore esik ici) tekrarlanirsa KARARLI sayilir ve
        `True` doner -- boylece OCR, harf harf yazilan bir metnin yarisini
        gormez (tasarim 2.2 adim 5). Aday, esik disina cikarsa VEYA taban
        hash'e geri donerse iptal edilir (sifirlanir).
        """
        current = _dhash(frame.image, self._hash_size)

        if self._last_rect is None or frame.rect != self._last_rect:
            self._last_rect = frame.rect
            self._stable_hash = current
            self._pending_hash = None
            self._pending_count = 0
            return True

        assert self._stable_hash is not None  # _last_rect ile birlikte kurulur

        if self._is_similar(current, self._stable_hash):
            # taban ile ayni -> hicbir sey degismedi; bekleyen aday da gecersiz
            self._pending_hash = None
            self._pending_count = 0
            return False

        if self._pending_hash is not None and self._is_similar(
            current, self._pending_hash
        ):
            self._pending_count += 1
        else:
            self._pending_hash = current
            self._pending_count = 1

        if self._pending_count >= self._stable_frames:
            self._stable_hash = current
            self._pending_hash = None
            self._pending_count = 0
            return True

        return False
