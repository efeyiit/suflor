"""T-004 tur 6 — K28 OLCU KITI, SURUM 3 (sefe ait; implementer ve tester ICE AKTARIR, DEGISTIRMEZ).

Neden kod, neden duzyazi degil
------------------------------
K28'in olculeri bes karar-kirmizi-takim gecisinde duzyazi olarak yazildi ve her
gecişte kor bir uygulama duzyazinin birakmadigi bosluktan geçti:

  gecis 2  fixture uc uygulamada da ayni ciktiyi veriyordu (hicbir sey olcmuyordu)
  gecis 3  olculerin tamami tek on ayardaydi -> dialogue-kapili mutant gecti
  gecis 4  olcu mekanizmayi (_raw_query_pair) kancaliyordu -> kapali kapida bosaliyordu
  gecis 5  (a) kuyruk hicbir fixture'da 2 bloktan buyuk degildi -> sirali[-1] ile
               sirali[1] ayirt edilemiyordu (off-by-one 8 olcuyu de gecti)
           (b) kancanin gordugu imza (a, b, params) tail/nxt kimligini tasimiyor;
               referans yalnizca source_blocks'tan geri kazanilabiliyor

Duzyazi her seferinde yeniden yorumlanabildigi icin dongu kapanmadi. Bu kit
olcunun KENDISIDIR: referans turetimi, derlem, alt sinirlar ve fixture'lar burada
tek bir yerde ve sef tarafindan mutantlara karsi dogrulanmis halde durur.

SURUM 2 -- kitin surum 1'i 6. gecişte KIRILDI
---------------------------------------------
26 yeni mutantin 13'u kitin uc on ayarini da TEMIZ geciyordu. Kok sebep kitin
kendi tasarimindaydi: `referans_cifti` referansi MUTANTIN KENDI VERDIGI
`source_blocks`'tan turetiyordu. Kit yalnizca "verdigin bbox verdigin
source_blocks ile tutarli mi" diye soruyordu; "DOGRU OGEYI mi verdin, DOGRU
YERDE mi sordun" diye sormuyordu. Ornekler (kitin KENDI derleminde davranissal
ayrisma, olcu 6 hepsinde TEMIZ diyordu): n06 tail birlesim dalinda guncellenmiyor
(1280), n08 taraflar takas (5317), n10 bir onceki oge (2281), n18/n19/n20
kapsam ihlali (3726/1724/1235).

SURUM 3 -- surum 2'nin DORT gercek kusuru (7. gecis)
----------------------------------------------------
Y3 (EN AGIR) KAPSAM kanali DOGRU uygulamada YANLIS POZITIF veriyordu. Iki
   sebep: `birlesik_kutu` `monitor_index`/`dpi_scale` tasimiyordu (girdi
   (1, 1.5) iken (0, 1.0) uretiyordu), ve K9'un `pending_blocks` yoluyla
   yutulan YALNIZ-ETIKET bloklari `source_blocks`'a giriyor ama bbox'a
   girmiyor -- birlesik-kutu esitligi orada YAPI GEREGI yanlis. Kapinin
   dogru uygulamayi reddetmesi, hic kapi olmamasindan kotudur. Kanal artik
   esitlik degil SIZINTI ariyor: cok bloklu bir tarafin bbox'i, o tarafin
   TEK bir ham blogunun bbox'ina esitse (ve birlesikten farkliysa) ham ikame
   o yola sizmis demektir.
Y4 KAPSAM yalniz SOL tarafi denetliyordu; sag taraftan sizan mutant geciyordu.
Y2 KIMLIK ve SIRA kanallari istisnada SESSIZCE kapaniyordu (`except: sb_liste=[]`
   ve `if sb_liste:`). `_merge_hyphenated`'e tek bir zorunlu argüman eklemek
   ikisini de susturuyordu. Artik `kimlik_kosulamadi` sayaci var ve `temiz`e dahil.
Y5 Kabul komutu (`python olcu_kiti.py`) dort sayaci YAZDIRIYOR ama ASSERT
   ETMIYORDU: 1216 ayrisma ureten bir uygulamaya "KIT: TEMIZ", exit 0 diyordu.
   Artik kimlik/kapsam/sira ihlalleri assert ediliyor (ayrisma K28 uygulanana
   kadar beklenen bir deger oldugu icin ayri raporlanir) ve etiket
   "KIT SAGLIGI" -- "uygulama temiz" diye okunmasin diye.
Ek: SAYI kanali (bolumleme sorgusu sayisi = oge sayisi - 1) -- 7. gecisin
   n18/M10 sinifini yeniden uygulama gerektirmeden yakalar.

BILINEN SINIR (gizlenmiyor, karara yazildi): `adim1_4` referansi denetlenen
modulun kendi yardimcilarini (`_merge_hyphenated`, `_extract_speakers`, ...)
cagirarak uretir, yani PROTOKOL 4.6/8'in tam anlamiyla bagimsiz DEGILDIR: o
yardimcilari degistiren bir mutantta kitin oge listesi mutantla birlikte kayar.
Adim 1-4'u kit icinde yeniden yazmak kitin kendi yeniden uygulamasini bir hata
kaynagi yapardi; sef bu takasi bilerek yapti ve sinifi tester yukumlulugune
cevirdi (bkz. karar, M12).

Surum 2 uc sey ekliyor:
  1. BAGIMSIZ KIMLIK KANALI -- kit adim 1-4'u kendi yeniden turetir ve her
     sorguda (a) sol tarafin bir OGENIN source_blocks'u oldugunu, (b) sag
     tarafin onu okuma sirasinda HEMEN IZLEYEN oge oldugunu assert eder.
  2. KAPSAM DENETIMI -- `ignore_length=False` cagrilari da kaydedilir ve
     bunlarda bbox'in source_blocks'un BIRLESIK kutusu oldugu (yani ham ikame
     UYGULANMADIGI) assert edilir. K28'in kapsam cumlesinin olcusu budur.
  3. ALTI YENI GIRDI SINIFI -- ASCII-disi (CJK/RTL), w<=0, negatif koordinat,
     >=16 bloklu girdi, iki konusmaci, >=5 bloklu derin zincir. Surum 1'in
     derlemi bunlarin HICBIRINI uretmiyordu; yedi mutant hem kite hem 478
     kor teste gorunmez kaliyordu.

Onkosul (K28'e yazildi)
-----------------------
Ham ikame `dataclasses.replace(...)` ile yapilir; `speaker`, `text` VE
`source_blocks` aynen korunur, yalniz `bbox` degisir. `source_blocks`'un
korunmasi urun davranisi icin OLU bir alandir (yeniden yazan uygulama 16.000
kosumda 0 ayrisma verir) ama bu kitin ONKOSULUDUR: kanca yalnizca (a, b, params)
gorur, tail/nxt kimligi baska hicbir kanaldan geri kazanilamaz.

Kullanim
--------
    from olcu_kiti import olcu3_fixture, olcu6_kos, OLCU6_ALT_SINIRLAR

    def test_k28_olcu6_makine_denetimi(preset):
        r = olcu6_kos(preset)
        assert r.ayrisma == 0, r.ilk_fark
        assert r.sinir > 0
        assert r.coklu_sol >= OLCU6_ALT_SINIRLAR["coklu_sol"]
        ...

Kendini sinama:  python .agents/tasks/T-004/olcu_kiti.py
"""
from __future__ import annotations

import random
import sys
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, Sequence

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.contracts.models import OcrPreset, Rect, TextBlock  # noqa: E402
from src.ocr import normalizer as N  # noqa: E402

ON_AYARLAR = (OcrPreset.DIALOGUE, OcrPreset.TOOLTIP, OcrPreset.SUBTITLE)

# Olcu 6'nin on ayar BASINA alt sinirlari. Tek bir sinir bile saglanmazsa denetim
# totolojiktir: olctugu seyi hic uretmemis demektir.
# Alt sinirlar: her biri, DERLEMIN uretebilecegi TABAN degerin yarisi olarak
# kontrol edilir (`olcu6_taban()`), boylece kit kendi derlemi degisince bayatlamaz
# ve mutantin sayaci dusurerek kacmasi zorlasir. Mutlak zeminler:
OLCU6_ALT_SINIRLAR = {
    "sinir": 1,          # en az bir miras-uygunluk sorgusu gozlendi
    "coklu_sol": 500,    # len(tail.source_blocks) > 1
    "uclu_sol": 200,     # len(tail.source_blocks) >= 3  -- off-by-one'i gorunur kilar
    "coklu_sag": 500,    # len(nxt.source_blocks) > 1
    "derin_sol": 50,     # len(tail.source_blocks) >= 5  -- derin zincir (surum 2)
    "ascii_disi": 100,   # CJK/RTL metin iceren sorgu   (surum 2)
    "yozlasmis": 50,     # w<=0 ya da h<=0 blok iceren sorgu (surum 2)
    "negatif": 50,       # negatif koordinatli blok iceren sorgu (surum 2)
    "buyuk": 50,         # >=16 bloklu girdiden gelen sorgu (surum 2)
    "iki_konusmaci": 50,  # girdide >=2 etiketli blok (surum 2)
    "kapsam": 100,       # ignore_length=False cagrisi (kapsam denetimi, surum 2)
}


def _esik_alti_conf() -> float:
    """Esik-alti guven degeri ON AYAR TABLOSUNDAN turetilir (surum 2).

    Sabit 0.50 yazilirsa esik tablosu asagi kayinca (SUBTITLE 0.55 -> 0.495)
    deger artik esik-alti olmaz ve denetim sessizce bosalir -- sef olctu.
    """
    from src.ocr.presets import get_params
    return min(get_params(pr).confidence_threshold for pr in ON_AYARLAR) * 0.8


ESIK_ALTI_CONF = _esik_alti_conf()


# --------------------------------------------------------------------------- referans
def okuma_sirasi(blocks: Sequence[TextBlock], idxs: Sequence[int]) -> list[int]:
    """K28'in okuma sirasi: (bbox.y, bbox.x, girdi indeksi) artan.

    Ucuncu bilesen bugunku kodda davranissal no-op'tur (source_blocks K8 geregi
    artan, sorted kararli); tanimi K8'e bagimli olmaktan cikarmak icin yazilir.
    """
    return sorted(idxs, key=lambda i: (blocks[i].bbox.y, blocks[i].bbox.x, i))


def referans_cifti(blocks: Sequence[TextBlock], sol_sb: Sequence[int],
                   sag_sb: Sequence[int]) -> tuple[Rect, Rect]:
    """Miras-uygunluk sorgusunun ALMASI GEREKEN (sol.bbox, sag.bbox) cifti."""
    return (blocks[okuma_sirasi(blocks, sol_sb)[-1]].bbox,
            blocks[okuma_sirasi(blocks, sag_sb)[0]].bbox)


@dataclass
class Sorgu:
    sol_sb: tuple[int, ...]
    sag_sb: tuple[int, ...]
    sol_bbox: Rect
    sag_bbox: Rect
    miras: bool = True   # ignore_length=True ise miras sorgusu, degilse bolumleme sorgusu


@contextmanager
def sorgu_kaydi() -> Iterator[list[Sorgu]]:
    """`ignore_length=True` ile gelen HER `_group_rejection_reason` cagrisini kaydeder.

    Kanca DEGISMEZI kancalar, mekanizmayi degil: ikame ister `_raw_query_pair`
    ile, ister satir ici, ister hic yapilmasin -- cagri buradan gecer.
    """
    kayit: list[Sorgu] = []
    orij = N._group_rejection_reason

    def kanca(a, b, params, *, ignore_length: bool = False):  # type: ignore[no-untyped-def]
        # SURUM 2: bolumleme (ignore_length=False) cagrilari da kaydedilir --
        # K28'in kapsam cumlesinin olcusu bunlarda.
        kayit.append(Sorgu(tuple(a.source_blocks), tuple(b.source_blocks),
                           a.bbox, b.bbox, miras=ignore_length))
        return orij(a, b, params, ignore_length=ignore_length)

    N._group_rejection_reason = kanca  # type: ignore[assignment]
    try:
        yield kayit
    finally:
        N._group_rejection_reason = orij  # type: ignore[assignment]


def adim1_4(blocks: Sequence[TextBlock], preset: OcrPreset) -> list[object]:
    """`_group`'a giren oge listesini KIT kendi yeniden turetir (surum 2, bagimsiz kimlik).

    `_normalize_impl`'in adim 1-4'unun birebir kopyasi. Mutantin verdigi
    `source_blocks`'a guvenmemek icin var: sorgunun DOGRU OGEYI, DOGRU YERDE
    sorup sormadigi ancak bagimsiz bir oge listesiyle denetlenebilir.
    """
    from dataclasses import replace as _replace
    from src.ocr.presets import get_params
    params = get_params(preset)
    ordered = sorted(enumerate(blocks), key=lambda pair: (pair[1].bbox.y, pair[1].bbox.x))
    items = [N._Item(text=b.text, bbox=b.bbox, speaker=None, source_blocks=(i,))
             for i, b in ordered if b.confidence >= params.confidence_threshold]
    items = [it for it in items if not N._is_noise(it.text)]
    items = [_replace(it, text=N._collapse_intraline(it.text)) for it in items]
    items = N._merge_hyphenated(items)
    items = N._extract_speakers(items)
    return list(items)


def birlesik_kutu(blocks: Sequence[TextBlock], sb: Sequence[int]) -> Rect:
    """`source_blocks`'un birlesik sinirlayici kutusu.

    SURUM 3: `monitor_index`/`dpi_scale` ILK bloktan tasinir. Surum 2 bunlari
    varsayilanda (0, 1.0) birakiyordu ve girdi (1, 1.5) oldugunda DOGRU
    uygulamada yanlis pozitif uretiyordu (sef olctu).
    """
    xs = [blocks[i].bbox for i in sb]
    x0 = min(b.x for b in xs); y0 = min(b.y for b in xs)
    x1 = max(b.x + b.w for b in xs); y1 = max(b.y + b.h for b in xs)
    ilk = xs[0]
    return Rect(x0, y0, x1 - x0, y1 - y0, ilk.monitor_index, ilk.dpi_scale)


def _yalniz_etiket(text: str) -> bool:
    """Blok yalnizca bir konusmaci etiketi mi ("Ada:") -- geometriye katki vermez.

    K9 boyle bloklari `pending_blocks` ile bir sonraki ogeye yutar: blok
    `source_blocks`'a girer ama bbox'a girmez. Kapsam kanali bunu bilmezse
    dogru uygulamada yanlis pozitif uretir (sef olctu).
    """
    ad, kalan = N._split_speaker_label(text)
    return ad is not None and not kalan.strip()


def ham_ikame_sizmis(blocks: Sequence[TextBlock], sb: Sequence[int], bbox: Rect) -> bool:
    """Bolumleme sorgusuna ham ikame SIZMIS mi (surum 3, Y3).

    Esitlik ("bbox birlesik kutu olmali") YANLIS bir degismezdir: K9'un
    `pending_blocks` yoluyla yutulan yalniz-etiket bloklari `source_blocks`'a
    girer ama bbox'a girmez. Onun yerine SIZINTININ KENDISI aranir: ham ikame
    bbox'i TEK bir ham blogun kutusuyla degistirir. Yani cok bloklu bir tarafin
    bbox'i, o tarafin tek bir kaynak blogunun bbox'ina esitse ve birlesik
    kutudan farkliysa, ikame o yola sizmistir.
    """
    if len(sb) < 2:
        return False                      # tek bloklu tarafta sizinti gozlenemez
    if bbox == birlesik_kutu(blocks, sb):
        return False                      # tam birlesik kutu: temiz
    # K9'un `pending_blocks` yoluyla yutulan YALNIZ-ETIKET bloklari
    # `source_blocks`'a girer ama GEOMETRIYE katkı vermez ("Ada:" gibi, bolme
    # sonrasi kalani bos). Karsilastirma yalnizca geometriye katki veren
    # altkumeyle yapilir; aksi halde kapı DOGRU uygulamayi reddeder (sef olctu).
    gecerli = [i for i in sb if not _yalniz_etiket(blocks[i].text)]
    if gecerli and gecerli != list(sb) and bbox == birlesik_kutu(blocks, gecerli):
        return False
    return any(bbox == blocks[i].bbox for i in sb)


# --------------------------------------------------------------------------- derlem
def derlem(n: int = 2500, tohum: int = 20260910) -> list[list[TextBlock]]:
    """Olcu 6'nin derlemi (surum 2). Girdilerin ~%60'i "duz" sinif, ~%40'i alti
    OZEL sinifa dagilir; her sinifin kendi alt siniri var (OLCU6_ALT_SINIRLAR).

    Duz sinif:
      1. ZINCIRLEME hyphen -> len(tail.source_blocks) >= 3 (2 elemanli kumede
         `sirali[-1]` ile `sirali[1]` AYNI seydir; off-by-one ancak 3+'ta gorunur)
      2. esik-alti bloklar -> suzulmus `blocks` geciren uygulamada indeks kaymasi
      3. shuffle -> girdi listesi okuma sirasinda DEGIL (K3)

    Ozel siniflar (surum 2 -- surum 1 bunlarin HICBIRINI uretmiyordu ve yedi
    mutant hem kite hem 478 kor teste gorunmez kaliyordu):
      d) DERIN zincir  -> len(tail.source_blocks) >= 5
      e) ASCII-disi    -> CJK ve RTL metin
      f) YOZLASMIS     -> w<=0 / h<=0 blok
      g) NEGATIF       -> negatif koordinat
      h) BUYUK         -> >=16 bloklu girdi
      i) IKI KONUSMACI -> girdide iki etiketli blok
    """
    rng = random.Random(tohum)
    CJK = "\u3053\u3093\u306b\u3061\u306f\u4e16\u754c"      # konnichiha sekai
    RTL = "\u0645\u0631\u062d\u0628\u0627\u0020\u0628\u0627\u0644\u0639\u0627\u0644\u0645"  # merhaba dunya
    out: list[list[TextBlock]] = []
    for k in range(n):
        _OZEL = ["derin", "ascii_disi", "yozlasmis", "negatif", "buyuk", "iki_konusmaci"]
        sinif = "duz" if k % 5 < 3 else _OZEL[(k // 5) % 6]
        bs: list[TextBlock] = []
        y = -400 if sinif == "negatif" else 0
        etiket = "Ada: "
        bs.append(TextBlock(etiket + "X" * rng.randint(60, 150), Rect(0, y, 240, 18), 0.9))
        y += 20
        zincir_sayisi = rng.randint(1, 3) if sinif != "buyuk" else 5
        for z in range(zincir_sayisi):
            halka = rng.randint(2, 3) if sinif != "derin" else rng.randint(5, 7)
            for j2 in range(halka):
                conf = ESIK_ALTI_CONF if rng.random() < 0.12 else 0.9
                if sinif == "ascii_disi":
                    # Zincirin BIRLESEBILMESI icin devam satirlari ASCII kucuk harfle
                    # BASLAMALI (K5); ASCII-disi govde ARDINDAN gelir. Yoksa zincir
                    # kopar, kuyruk tek bloklu kalir ve ASCII-disi yolda R5-1 kosulu
                    # hic dogmaz -- surum 2'nin ilk kalibrasyonunda boyle oldu.
                    on = "Y" if j2 == 0 else rng.choice("yzw")
                    govde = on * rng.randint(6, 12) + rng.choice([CJK, RTL]) * rng.randint(4, 10)
                else:
                    govde = ("Y" if j2 == 0 else rng.choice("yzw")) * rng.randint(20, 60)
                w = 0 if (sinif == "yozlasmis" and rng.random() < 0.3) else rng.choice([240, 240, 8, 308])
                h = 0 if (sinif == "yozlasmis" and rng.random() < 0.3) else rng.choice([18, 18, 5, 50])
                bs.append(TextBlock(govde + " son-",
                                    Rect(rng.choice([0, 0, 100]) - (500 if sinif == "negatif" else 0),
                                         y, w, h), conf))
                y += rng.choice([0, 2, 20])
            kuyruk = ("raki" + rng.choice([CJK, RTL]) * rng.randint(4, 10) if sinif == "ascii_disi"
                      else "raki" + "k" * rng.randint(0, 40))
            bs.append(TextBlock(kuyruk,
                                Rect(rng.choice([0, 300, 100]) - (500 if sinif == "negatif" else 0), y,
                                     rng.choice([240, 8, 308]), rng.choice([18, 0, 5, 50])), 0.9))
            y += rng.choice([2, 20, 45])
            if sinif == "iki_konusmaci" and z == 0:
                bs.append(TextBlock("Bora: " + "Q" * rng.randint(60, 150), Rect(0, y, 240, 18), 0.9))
                y += 20
        bs.append(TextBlock("Z" * rng.randint(60, 160), Rect(0, y, 240, 18), 0.9))
        if rng.random() < 0.6:
            rng.shuffle(bs)
        out.append(bs)
    return out


@dataclass
class Olcu6Sonuc:
    on_ayar: str
    sinir: int = 0
    sira_ihlali: int = 0
    coklu_sol: int = 0
    uclu_sol: int = 0
    derin_sol: int = 0
    coklu_sag: int = 0
    ascii_disi: int = 0
    yozlasmis: int = 0
    negatif: int = 0
    buyuk: int = 0
    iki_konusmaci: int = 0
    kapsam: int = 0
    esik_alti: int = 0
    sayi_ihlali: int = 0
    kimlik_kosulamadi: int = 0
    ayrisma: int = 0
    kimlik_ihlali: int = 0
    kapsam_ihlali: int = 0
    patlama: int = 0
    ilk_fark: str = ""
    eksik_sinirlar: list[str] = field(default_factory=list)

    @property
    def temiz(self) -> bool:
        return (self.ayrisma == 0 and self.kimlik_ihlali == 0 and self.kapsam_ihlali == 0
                and self.sira_ihlali == 0 and self.sayi_ihlali == 0
                and self.kimlik_kosulamadi == 0
                and self.patlama == 0 and not self.eksik_sinirlar)


def olcu6_kos(preset: OcrPreset, girdiler: list[list[TextBlock]] | None = None) -> Olcu6Sonuc:
    """K28 olcu 6 (surum 2) -- UC bagimsiz denetim:

    A) GEOMETRI: her miras sorgusunun bbox cifti, `blocks`'tan okuma sirasi referansi.
    B) KIMLIK  : sol taraf bir OGENIN source_blocks'u ve sag taraf onu HEMEN IZLEYEN
                 oge mi (kit adim 1-4'u kendi turetir; mutantin verdigi veriye guvenmez).
    C) KAPSAM  : `ignore_length=False` (bolumleme) cagrilarinda bbox, source_blocks'un
                 BIRLESIK kutusu -- yani ham ikame o yola SIZMAMIS.
    D) SIRA    : miras sorgulari oge listesinde ARTAN sirada geliyor mu (gorunum
                 gecisi soldan saga tek yonlu; ters yonde isleyen bir uygulama
                 zincirlemeyi bozar ama A/B/C'nin hicbirini ihlal etmez).
    """
    from src.ocr.presets import get_params
    girdiler = girdiler if girdiler is not None else derlem()
    esik = get_params(preset).confidence_threshold
    r = Olcu6Sonuc(on_ayar=preset.name)
    for bl in girdiler:
        if any(b.confidence < esik for b in bl):
            r.esik_alti += 1
        ascii_disi = any(not b.text.isascii() for b in bl)
        yozlasmis = any(b.bbox.w <= 0 or b.bbox.h <= 0 for b in bl)
        negatif = any(b.bbox.x < 0 or b.bbox.y < 0 for b in bl)
        buyuk = len(bl) >= 16
        iki_kon = sum(1 for b in bl if ":" in b.text[:12]) >= 2
        try:
            ogeler = adim1_4(bl, preset)
            sb_liste = [tuple(it.source_blocks) for it in ogeler]  # type: ignore[attr-defined]
        except Exception as exc:  # noqa: BLE001
            # Y2: SESSIZ KAPANMA YOK. Kimlik/sira/sayi kanallari kosulamadiysa
            # bu bir IHLALDIR -- tek satirlik bir imza degisikligi ikisini de
            # susturup mutanti akliyordu (sef olctu).
            sb_liste = []
            r.kimlik_kosulamadi += 1
            if not r.ilk_fark:
                r.ilk_fark = f"KIMLIK KOSULAMADI: adim1_4 patladi -> {type(exc).__name__}: {exc}"
        bolumleme_sayisi = 0
        with sorgu_kaydi() as kayit:
            try:
                N.normalize(bl, preset)
            except Exception as exc:  # noqa: BLE001 -- suzulmus blocks IndexError uretir
                r.patlama += 1
                if not r.ilk_fark:
                    r.ilk_fark = f"{type(exc).__name__}: {exc}"
                continue
        onceki_k = -1
        for sg in kayit:
            if not sg.miras:
                # (C) KAPSAM: bolumleme sorgusuna ham ikame SIZMAMIS olmali.
                # Surum 3: esitlik degil SIZINTI aranir (Y3) ve IKI TARAF da
                # denetlenir (Y4).
                r.kapsam += 1
                bolumleme_sayisi += 1
                try:
                    sol_sizdi = ham_ikame_sizmis(bl, sg.sol_sb, sg.sol_bbox)
                    sag_sizdi = ham_ikame_sizmis(bl, sg.sag_sb, sg.sag_bbox)
                except Exception:
                    continue
                if sol_sizdi or sag_sizdi:
                    r.kapsam_ihlali += 1
                    if not r.ilk_fark:
                        taraf = "sol" if sol_sizdi else "sag"
                        sb_ = sg.sol_sb if sol_sizdi else sg.sag_sb
                        bb_ = sg.sol_bbox if sol_sizdi else sg.sag_bbox
                        r.ilk_fark = (f"KAPSAM: bolumleme sorgusunun {taraf} tarafina ham ikame "
                                      f"sizmis; sb={sb_} birlesik={birlesik_kutu(bl, sb_)} "
                                      f"olculen={bb_}")
                continue
            r.sinir += 1
            if len(sg.sol_sb) > 1:
                r.coklu_sol += 1
            if len(sg.sol_sb) >= 3:
                r.uclu_sol += 1
            if len(sg.sol_sb) >= 5:
                r.derin_sol += 1
            if len(sg.sag_sb) > 1:
                r.coklu_sag += 1
            if ascii_disi:
                r.ascii_disi += 1
            if yozlasmis:
                r.yozlasmis += 1
            if negatif:
                r.negatif += 1
            if buyuk:
                r.buyuk += 1
            if iki_kon:
                r.iki_konusmaci += 1
            # (B) KIMLIK -- mutantin verdigi source_blocks'a GUVENMEZ
            if sb_liste:
                if sg.sol_sb not in sb_liste:
                    r.kimlik_ihlali += 1
                    if not r.ilk_fark:
                        r.ilk_fark = (f"KIMLIK: sol taraf hicbir ogenin source_blocks'u degil: "
                                      f"{sg.sol_sb}")
                else:
                    k = sb_liste.index(sg.sol_sb)
                    # (D) SIRA: gorunum gecisi tek yonlu ve artan
                    if k < onceki_k:
                        r.sira_ihlali += 1
                        if not r.ilk_fark:
                            r.ilk_fark = (f"SIRA: miras sorgulari artan sirada degil; "
                                          f"onceki oge={onceki_k} simdiki={k}")
                    onceki_k = k
                    if k + 1 >= len(sb_liste) or sb_liste[k + 1] != sg.sag_sb:
                        r.kimlik_ihlali += 1
                        if not r.ilk_fark:
                            izleyen = sb_liste[k + 1] if k + 1 < len(sb_liste) else None
                            r.ilk_fark = (f"KIMLIK: sag taraf solu HEMEN IZLEMIYOR; sol={sg.sol_sb} "
                                          f"beklenen_sag={izleyen} olculen_sag={sg.sag_sb}")
            # (A) GEOMETRI
            bek_sol, bek_sag = referans_cifti(bl, sg.sol_sb, sg.sag_sb)
            if sg.sol_bbox != bek_sol or sg.sag_bbox != bek_sag:
                r.ayrisma += 1
                if not r.ilk_fark:
                    r.ilk_fark = (f"GEOMETRI: sol_sb={sg.sol_sb} beklenen={bek_sol} "
                                  f"olculen={sg.sol_bbox} | sag_sb={sg.sag_sb} "
                                  f"beklenen={bek_sag} olculen={sg.sag_bbox}")
        # (E) SAYI: bolumleme sorgusu sayisi = oge sayisi - 1 (surum 3).
        # Miras kararina fazladan kosul ekleyen ya da sorgu uretimini kapayan
        # mutantlari yeniden uygulama gerektirmeden yakalar (7. gecis n18/M10).
        if sb_liste and len(sb_liste) >= 2 and bolumleme_sayisi != len(sb_liste) - 1:
            r.sayi_ihlali += 1
            if not r.ilk_fark:
                r.ilk_fark = (f"SAYI: bolumleme sorgusu sayisi {bolumleme_sayisi}, "
                              f"beklenen {len(sb_liste) - 1} (oge sayisi - 1)")
    for ad, alt in OLCU6_ALT_SINIRLAR.items():
        if getattr(r, ad) < alt:
            r.eksik_sinirlar.append(f"{ad}={getattr(r, ad)} < {alt}")
    return r


# --------------------------------------------------------------------------- fixture'lar
def olcu3_fixture() -> list[TextBlock]:
    """Sirasiz girdi + CIFT bloklu kuyruk; indeks sirasi okuma sirasina ters.

    tail.source_blocks = (0, 2): indeks sirasiyla son 2 (y=20), okuma sirasiyla son 0 (y=40).
    """
    return [
        TextBlock("raki", Rect(0, 40, 240, 5), 0.9),              # idx0, okuma sirasinda 3.
        TextBlock("Ada: " + "X" * 130, Rect(0, 0, 240, 18), 0.9),  # idx1, okuma sirasinda 1.
        TextBlock("Y" * 88 + " son-", Rect(0, 20, 240, 18), 0.9),  # idx2, okuma sirasinda 2.
        TextBlock("Z" * 140, Rect(0, 50, 240, 18), 0.9),           # idx3, aday
    ]


OLCU3_BEKLENEN = {
    OcrPreset.DIALOGUE: [((0, 1, 2), "Ada"), ((3,), None)],
    OcrPreset.TOOLTIP: [((1,), "Ada"), ((0, 2), "Ada"), ((3,), None)],
}


def olcu3b_fixture() -> list[TextBlock]:
    """ZINCIRLEME hyphen -> UC bloklu kuyruk (Y1).

    tail.source_blocks = (1, 2, 3): `sirali[-1]` = 3, `sirali[1]` = 2 -> off-by-one AYRISIR.
    Iki elemanli kuyrukta bu iki ifade AYNI seydir; bu yuzden olcu3 tek basina yetmez.
    """
    return [
        TextBlock("Ada: " + "X" * 130, Rect(0, 0, 240, 18), 0.9),   # idx0
        TextBlock("Y" * 40 + " son-", Rect(0, 20, 240, 18), 0.9),   # idx1
        TextBlock("z" * 40 + " son-", Rect(0, 40, 240, 18), 0.9),   # idx2
        TextBlock("w" * 40, Rect(0, 60, 240, 5), 0.9),              # idx3  <- ham son satir, h=5
        TextBlock("Z" * 150, Rect(0, 90, 240, 18), 0.9),            # idx4, aday
    ]


OLCU3B_BEKLENEN = {OcrPreset.DIALOGUE: [((0, 1, 2, 3), "Ada"), ((4,), None)]}


def olcu5_fixture() -> list[TextBlock]:
    """IKI sinir, ikisinde de cok bloklu kuyruk (olcu 5'in `sinir >= 2` sarti)."""
    return [
        TextBlock("raki", Rect(0, 40, 240, 5), 0.9),
        TextBlock("Ada: " + "X" * 130, Rect(0, 0, 240, 18), 0.9),
        TextBlock("Y" * 88 + " son-", Rect(0, 20, 240, 18), 0.9),
        TextBlock("Z" * 140, Rect(0, 50, 240, 18), 0.9),
        TextBlock("kola", Rect(0, 90, 240, 5), 0.9),
        TextBlock("W" * 100 + " son-", Rect(0, 70, 240, 18), 0.9),
        TextBlock("V" * 150, Rect(0, 110, 240, 18), 0.9),
    ]


def _selftest() -> int:
    """Kitin KENDI sagligini sinar: derlem alt sinirlari uretebiliyor mu, fixture'lar
    gerekli sekli veriyor mu, kanca kayit tutuyor mu.

    URUNUN dogrulugunu sinamaz: K28 uygulanmadan once `ayrisma > 0` BEKLENIR
    (R5-1 hala acik). O yuzden ayrisma burada bilgi olarak yazilir, hata sayilmaz.
    """
    hata = 0
    g = derlem()
    print("--- olcu 6 alt sinirlari (kitin sagligi) ---")
    for pr in ON_AYARLAR:
        r = olcu6_kos(pr, g)
        print(f"  {r.on_ayar:9s} sinir={r.sinir:5d} coklu={r.coklu_sol:5d} uclu={r.uclu_sol:5d} "
              f"derin={r.derin_sol:4d} sag={r.coklu_sag:5d} ascii_disi={r.ascii_disi:4d} "
              f"yoz={r.yozlasmis:4d} neg={r.negatif:4d} buyuk={r.buyuk:4d} ikikon={r.iki_konusmaci:4d} "
              f"kapsam={r.kapsam:5d} esik_alti={r.esik_alti:4d}")
        print(f"  {'':9s} | ayrisma={r.ayrisma} kimlik={r.kimlik_ihlali} "
              f"kapsam_ihlali={r.kapsam_ihlali} sira={r.sira_ihlali} sayi={r.sayi_ihlali} "
              f"kimlik_kosulamadi={r.kimlik_kosulamadi} patlama={r.patlama}")
        if r.eksik_sinirlar:
            hata = 1
            print(f"    KIT IHLALI (derlem yetersiz): {r.eksik_sinirlar}")
        if r.patlama:
            hata = 1
            print(f"    KIT IHLALI (patlama): {r.ilk_fark[:160]}")
        # Y5: sayaclar YAZDIRILMAKLA KALMAZ, ASSERT EDILIR. `ayrisma` K28
        # uygulanana kadar beklenen bir degerdir (R5-1 hala acik), o yuzden
        # ayri raporlanir; digerleri BUGUN de 0 olmak zorundadir.
        for ad in ("kimlik_ihlali", "kapsam_ihlali", "sira_ihlali", "sayi_ihlali",
                   "kimlik_kosulamadi"):
            if getattr(r, ad):
                hata = 1
                print(f"    IHLAL {ad}={getattr(r, ad)}: {r.ilk_fark[:200]}")
    print("--- fixture sekilleri ---")
    with sorgu_kaydi() as k3b:
        N.normalize(olcu3b_fixture(), OcrPreset.DIALOGUE)
    uclu = [s.sol_sb for s in k3b if s.miras and len(s.sol_sb) >= 3]
    print(f"  olcu3b uclu kuyruk: {uclu}  {'OK' if uclu else 'YOK -- off-by-one gorunmez!'}")
    if not uclu:
        hata = 1
    with sorgu_kaydi() as k5:
        N.normalize(olcu5_fixture(), OcrPreset.DIALOGUE)
    coklu = sum(1 for s in k5 if s.miras and len(s.sol_sb) > 1)
    miras5 = [s for s in k5 if s.miras]
    print(f"  olcu5 fixture: miras_sinir={len(miras5)} coklu_sol={coklu}  {'OK' if len(miras5) >= 2 and coklu >= 2 else 'YETERSIZ'}")
    if not (len(miras5) >= 2 and coklu >= 2):
        hata = 1
    print("--- fixture beklentileri (K28 UYGULANDIKTAN SONRA gecerli) ---")
    for ad, f, bek in (("olcu3", olcu3_fixture, OLCU3_BEKLENEN),
                       ("olcu3b", olcu3b_fixture, OLCU3B_BEKLENEN)):
        for pr, b in bek.items():
            got = [(s.source_blocks, s.speaker) for s in N.normalize(f(), pr)]
            print(f"  {ad} {pr.name:9s} simdi={got}")
            print(f"  {' ' * (len(ad) + 10)}bek ={b}  {'(zaten saglaniyor)' if got == b else '(K28 sonrasi saglanacak)'}")
    print("KIT SAGLIGI: TEMIZ" if not hata else "KIT SAGLIGI: IHLAL")
    print("  (not: `ayrisma` K28 uygulanana kadar >0 BEKLENIR -- R5-1 acik; "
          "kimlik/kapsam/sira/sayi ihlalleri ise bugun de 0 olmalidir)")
    return hata


if __name__ == "__main__":
    sys.exit(_selftest())
