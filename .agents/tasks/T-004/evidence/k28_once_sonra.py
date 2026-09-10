"""K28 ONCESI/SONRASI olcumu -- kit `olcu6_kos`, uc on ayar.

"ONCE" = `_raw_query_pair` KIMLIK fonksiyonuna indirgenmis hali, yani K28
ONCESI kodun BIREBIR aynisi (`_group_rejection_reason(tail, nxt, params,
ignore_length=True)`). Kaynak dosya DEGISTIRILMEZ; olcum yeniden uretilebilir.
"""
import sys
sys.path.insert(0, r"C:\Users\pc\Desktop\efe\çeviri uygulaması")
sys.path.insert(0, r"C:\Users\pc\Desktop\efe\çeviri uygulaması\.agents\tasks\T-004")
from src.ocr import normalizer as N
from olcu_kiti import olcu6_kos, derlem, ON_AYARLAR

g = derlem()
orij = N._raw_query_pair
print("=== ONCE  (K28 uygulanmamis: _raw_query_pair -> (tail, nxt) kimligi) ===")
N._raw_query_pair = lambda tail, nxt, blocks: (tail, nxt)
for pr in ON_AYARLAR:
    r = olcu6_kos(pr, g)
    print(f"  {r.on_ayar:9s} ayrisma={r.ayrisma:5d} kimlik={r.kimlik_ihlali} kapsam_ihlali={r.kapsam_ihlali} "
          f"sira={r.sira_ihlali} sayi={r.sayi_ihlali} patlama={r.patlama} temiz={r.temiz}")
N._raw_query_pair = orij
print("=== SONRA (K28 uygulanmis, teslim edilen kod) ===")
for pr in ON_AYARLAR:
    r = olcu6_kos(pr, g)
    print(f"  {r.on_ayar:9s} ayrisma={r.ayrisma:5d} kimlik={r.kimlik_ihlali} kapsam_ihlali={r.kapsam_ihlali} "
          f"sira={r.sira_ihlali} sayi={r.sayi_ihlali} patlama={r.patlama} temiz={r.temiz}")
