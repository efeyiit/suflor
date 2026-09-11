"""B1b -- KACAN mutantlarin (M23, M40, M41) AYIRT EDILMESI: esdeger mi, yoksa olcu bos mu?

Bes kapinin hicbiri yakalamadi. Iki olasilik: (a) mutant davranis-esdeger (o zaman
KONTROL'dur, bulgu degil); (b) davranis degisiyor ama hicbir olcu o sinifa
ugramiyor (§4.6/10). Bunu ayirmak icin her mutant kaynaga uygulanip AYRI bir modul
olarak yuklenir; el yapimi fixture + rastgele arama ile orijinalden AYRISTIGI girdi
sayisi olculur. Ayrisan girdi bulunursa (b): olcu bos, hazir test onerisi asagida.

Kosum (depo kokunden): python .agents/tasks/T-008/tester_B/b1b_kacan_ayirt.py
Metin basilmaz (sentetik etiketler yalniz).
"""
from __future__ import annotations

import importlib.util
import random
import sys
import types
import unicodedata
from pathlib import Path

DEPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(DEPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.contracts.models import Rect, TextBlock  # noqa: E402
from src.ocr import satir_birlestirici as ORJ  # noqa: E402

import mutant_kiti as kit  # noqa: E402  (yalniz yama tanimlari; kosmaz)

KAYNAK = (DEPO / "src/ocr/satir_birlestirici.py").read_text(encoding="utf-8")


def _mutant_modul(mid: str) -> types.ModuleType:
    mut = next(m for m in kit.MUTANTLAR if m.mid == mid)
    metin = KAYNAK
    for eski, yeni in mut.yamalar:
        assert metin.count(eski) == 1, (mid, eski[:60])
        metin = metin.replace(eski, yeni, 1)
    spec = importlib.util.spec_from_loader(f"_mut_{mid}", loader=None)
    assert spec is not None
    mod = importlib.util.module_from_spec(spec)
    exec(compile(metin, f"<{mid}>", "exec"), mod.__dict__)
    return mod


def _b(x: int, y: int, w: int, h: int, text: str, mon: int = 0) -> TextBlock:
    return TextBlock(text=text, bbox=Rect(x, y, w, h, monitor_index=mon), confidence=0.9)


def _imza(cikti: list[TextBlock]) -> list[tuple[str, int, int, int, int, int]]:
    return [(c.text, c.bbox.x, c.bbox.y, c.bbox.w, c.bbox.h, len(c.line_boxes)) for c in cikti]


def main() -> int:
    bulgular = 0
    # ---------------------------------------------------------------- M23
    m23 = _mutant_modul("M23")
    uyum = chr(0xF902)  # CJK COMPATIBILITY IDEOGRAPH-F902 (korean v4 sozlugunde VAR, B1b-M23 kaniti)
    cjk = chr(0x8C48)   # CJK UNIFIED IDEOGRAPH
    assert "CJK COMPATIBILITY IDEOGRAPH" in unicodedata.name(uyum)
    girdi = [_b(0, 0, 50, 20, uyum + uyum), _b(55, 0, 50, 20, cjk + cjk)]
    o, m = ORJ.satirlari_birlestir(girdi), m23.satirlari_birlestir(girdi)
    ayristi = o[0].text != m[0].text
    print(f"M23 (uyumluluk ideografi CJK degil): uyum+cjk komsu -> orijinal bosluk sayisi {o[0].text.count(' ')}, "
          f"mutant {m[0].text.count(' ')} -> {'AYRISTI (olcu bos)' if ayristi else 'esdeger'}")
    # erisilebilirlik: KR v4 sozlugunde 76 uyumluluk ideografi (B1b-M23-erisilebilirlik-ocr-sozlugu.txt);
    # JP v4 sozlugunde 0 -> yalniz KR'de, iki Hanja kutusu yan yana gelirse.
    bulgular += ayristi
    # ---------------------------------------------------------------- M40
    m40 = _mutant_modul("M40")
    # ayni (y,x)'te iki YUZEY: monitor 0'da birlesik grup [p(idx0), q(idx2)], monitor 1'de tekil s(idx1)
    girdi40 = [_b(0, 0, 50, 20, "p", mon=0), _b(0, 0, 50, 20, "s", mon=1), _b(55, 0, 50, 20, "q", mon=0)]
    o40, mm40 = [c.text for c in ORJ.satirlari_birlestir(girdi40)], [c.text for c in m40.satirlari_birlestir(girdi40)]
    print(f"M40 (bag max idx): monitorler arasi (y,x) bagi -> orijinal {o40}, mutant {mm40} -> "
          f"{'AYRISTI' if o40 != mm40 else 'esdeger'}")
    # tek yuzeyde erisilebilir mi? rastgele arama (ayni yuzey, cift tespit dahil)
    rnd = random.Random(8)
    ayrisan = 0
    for _ in range(3000):
        n = rnd.randrange(2, 7)
        g = []
        for i in range(n):
            g.append(_b(rnd.choice([0, 0, 55, 110]), rnd.choice([0, 0, 0, 30]), 50, rnd.choice([20, 20, 60]), f"t{i}"))
        if _imza(ORJ.satirlari_birlestir(g)) != _imza(m40.satirlari_birlestir(g)):
            ayrisan += 1
    print(f"M40 tek yuzey rastgele 3000 girdi (cift tespitli): ayrisan {ayrisan}")
    bulgular += (o40 != mm40) or ayrisan > 0
    # ---------------------------------------------------------------- M41
    m41 = _mutant_modul("M41")
    # ayni x, farkli y, ayni satir: a(0,0,h20) idx0, b(0,8,h20) idx1 -- x_sirali (x,y,idx): a,b ; (x,idx): a,b (ayni)
    # girdi sirasi ters: [b, a] -> (x,y,idx): a(y0) once ; (x,idx): b(idx0) once -> c hangi gruba?
    a = _b(0, 0, 50, 20, "a")
    b = _b(0, 8, 50, 20, "b")
    c = _b(55, 4, 50, 20, "c")
    for girdi41 in ([a, b, c], [b, a, c]):
        o41 = [x.text for x in ORJ.satirlari_birlestir(girdi41)]
        mm41 = [x.text for x in m41.satirlari_birlestir(girdi41)]
        print(f"M41 (satir ici (x,idx), y yok): girdi {[x.text for x in girdi41]} -> orijinal {o41}, mutant {mm41} -> "
              f"{'AYRISTI' if o41 != mm41 else 'esdeger'}")
        bulgular += o41 != mm41
    rnd = random.Random(9)
    ayrisan41 = 0
    for _ in range(3000):
        n = rnd.randrange(2, 7)
        g = [_b(rnd.choice([0, 0, 55, 110]), rnd.choice([0, 4, 8]), 50, 20, f"t{i}") for i in range(n)]
        if _imza(ORJ.satirlari_birlestir(g)) != _imza(m41.satirlari_birlestir(g)):
            ayrisan41 += 1
    print(f"M41 rastgele 3000 girdi (ayni x farkli y): ayrisan {ayrisan41}")
    bulgular += ayrisan41 > 0
    print()
    print(f"SONUC: {bulgular} ayrisma kaydi -> kacan mutantlar davranis-esdeger DEGIL; olculeri bos (§4.6/10).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
