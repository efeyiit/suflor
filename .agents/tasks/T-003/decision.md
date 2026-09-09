---
task: T-003
role: orkestra-sefi
round: 2
decision: kabul
---

# Şef Kararı — T-003

**Kabul.** 2 turda kapandı.

## Tur 1 — RET

Kör tester gerçek bir kusur buldu ve reddetti. Şef reddi **bağımsız olarak yeniden üretti**; kusur tester'ın bildirdiğinden daha genişti.

**Kusur:** Modül docstring'i `physical_to_logical(logical_to_physical(r)) == r` eşitliğinin *koşulsuz* doğru olduğunu iddia ediyordu. Aynı docstring'in ispat taslağı `s >= 1` varsayıyor, koddaki tek doğrulama ise yalnızca `dpi_scale <= 0` reddediyordu. Sonuç: `0 < dpi_scale < 1` sessizce kabul ediliyor ve garanti orada tutmuyordu.

**Şefin ölçümü:** `(0,1)` aralığında round-trip **%68.6 oranında kırılıyordu**. Teslim edilen 133 testin hiçbiri bunu yakalamamıştı.

Kusurun türü dikkate değer: kod değil, **kodun verdiği söz** yanlıştı. Docstring'e güvenen bir tüketici yanılırdı.

## Şef kararı — uygulanan çözüm

Tester iki seçenek sundu; şef **ikisini birden** istedi:

1. Doğrulama sıkılaştırıldı: `dpi_scale < 1.0` artık `ValueError` (Windows ölçekleri %100'ün altına inmez)
2. Docstring garantisi, modülün **kabul ettiği girdi kümesinin tamamına** daraltıldı

İlke: *bir garanti, fonksiyonun kabul ettiği her girdi için tutmalıdır.* Tutmuyorsa ya alan daraltılır ya iddia — burada ikisi de yapıldı, böylece hem sessiz kabul bitti hem belge dürüst oldu.

## Tur 2 — ONAY

Yeni bir kör tester düzeltmeyi doğruladı ve **regresyona odaklandı** (düzeltmenin çalışan şeyleri bozup bozmadığı).

| Kontrol | Sonuç |
|---|---|
| Kusur gitti mi | `(0,1)` aralığında 40.000 rastgele kombinasyon, **0 sessiz kabul** |
| Regresyon (ölçek ≥ 1.0) | 300.000 örnekli round-trip fuzz, **0 hata** |
| Yuvarlama simetrisi | 100.000 örnek, 0 asimetri |
| Negatif koordinatlı monitör | 6.000 deneme, 0 hata |
| Bayat testler | 1. turun 2 testi güncellendi, `tester_tests/` **54/54 yeşil** |

Tester farklı tohum kullandı (424242 ≠ 1. turun 908171'i) ve farklı monitör düzenleriyle sınadı — 1. turun örneklemini tekrarlamadı.

## Şefin bağımsız doğrulaması

Ne implementer'ın ne tester'ın raporuna güvenildi:

| Kontrol | Sonuç |
|---|---|
| `mypy --strict` | Temiz |
| Teslim testleri | 149 geçti (133'ten +16) |
| Tester testleri | 54 geçti |
| Sınır davranışı | `0.999999` red · `1.0` kabul · `1.0000001` kabul |
| Ölçek ≥ 1.0 round-trip | **3157/3157 tutuyor** |
| Sahiplik | Temiz — hiçbir ajan `owns` dışına yazmadı |

## Sonuç

`src/capture/dpi.py` **kabul edildi**.

Kayda değer olan: bu kusuru yakalayan şey ek test sayısı değil, **kör tester'ın bağımsız ve düşmanca örneklemesiydi**. Implementer kendi seçtiği 65 vakayla test etmişti ve hepsi geçiyordu. Sistemin varlık sebebi tam olarak bu.
