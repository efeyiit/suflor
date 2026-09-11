---
task: T-005
role: sef
round: 3
decision: kabul
---

# T-005 — CaptureService: KABUL

Üç tur. Görev kapandı.

## Ne teslim edildi

`src/capture/service.py` (623+ satır) ve `src/capture/monitors.py` (164 satır). `CaptureService.capture_region(rect) -> Frame` ve `capture_full(monitor_index) -> Frame`: çok monitör, negatif sanal-masaüstü koordinatı, birleşime göre kırpma, numpy skaler düzleştirme, K6 yeniden deneme taksonomisi, koşulsuz kopya (K7), tembel `mss` tutamacı ve bağlam yöneticisi ömrü (K10). `MssBackend` gerçek ekran, `FakeBackend` headless test.

`tests/unit/capture/test_service.py` + `test_monitors.py` — **164 test**. Kör tester takımı (A/B/C/D) — **458 test**.

Gerçek ekranda doğrulandı: iki monitör `(-2560,0,2560,1440)` + `(0,0,2560,1440)`, negatif koordinattan yakalama, tam monitör `(1440,2560,3)`, `shares_memory=False`, `Rect` alanları düz `int`. `demo/bolge_izle.py` bu servisi canlı kullanıyor.

## Kapanış ölçümleri (şefin kendi koşumu)

```
mypy --strict                          exit 0
pytest sahipli iki dosya               164 passed
headless_check.py                      exit 0 TEMİZ
pytest tests/unit/capture --cov        747 passed, %98.83
pytest tests                           986 passed
kör tester takımı (A+B+C+D)            458 passed, 1 skipped, 3 xfailed*
mutant kapısı (10 mutant)              9 yakalandı, M52 kontrol doğru kaçtı
```

\* Üç xfail, D'nin tur 3'te bıraktığı **yaşayan işaretler** (değer ekseni yükümlülüğü D-3.Y1). Kapatıldığında XPASS'a döner.

## Tur kaydı

| Tur | Ne oldu |
|---|---|
| paket | 8 kırmızı takım geçişi; **iki yüksek bulgu yine şefin kapısında** (§3 `np.asarray`, §4 `AnnAssign.value`) |
| 1 | Implementer teslim. **A, B, C onay · D ret** — K10'un iki ölçüsü yapısal olarak boş; M13 ürünü kırıyor (gerçek ekranda `BitBlt` hatası) ve beş kapı görmüyor |
| 2 | İki test eklendi, docstring düzeltildi. **Implementer şefin kararına ölçüyle itiraz etti ve haklı çıktı** (sessiz ayrışma "sıfır" değil, grid kördü). **D ret** — istisna yolunda `__exit__` ölçülmüyor; docstring'in olumsuz iddiası yanlış |
| 3 | `exc_type` ekseninde parametrize test, docstring'den evrensel iddia silindi. **D onay** + üç adlandırılmış yükümlülük |

Tur 1'e gelmeden paket **sekiz** kırmızı takım geçişi gördü. Tester turlarının **üçü de** gerçek boşluk buldu — ama üçünde de kod doğruydu; kusur her seferinde **ölçüde** idi.

## Kalite kanıtı

**İmplementer'a giden kod hatası: sıfır.** `src/capture` mantığı tur 1'den beri değişmedi; üç turda değişen yalnız testler ve docstring metni.

Şefin bu görevde ölçülmüş hataları (hepsi yakalandı, hepsi şef tarafından yeniden üretildi):

| # | Hata | Yakalayan |
|---|---|---|
| 1 | `headless_check` §3 `np.asarray` kullandı — K7'nin yasakladığı dönüşümün ta kendisi, kapının içinde | KRT (paket) |
| 2 | §4 uyum kapısı `AnnAssign.value` denetlemedi; çıplak beyan geçti | KRT (paket) |
| 3 | §5 konum sadakati kendi yanlış pozitifim (canlı ekran iki grab arasında değişir) | KRT (paket) |
| 4 | `git add -A` başka görevin kırmızı-faz dosyalarını süpürdü; `f75d4d4` temiz checkout'ta kırık | Tester-B (T-004) |
| 5 | Paket K10: *"Test paketi bunu ölçemez, K1 gereği"* — yanlış; kapının kör kalmasını meşrulaştırdı | Tester-D |
| 6 | Docstring: *"monitor_index sessizce yanlış çıkardı"* — yanlış mekanizma | şef (B'yi doğrularken) |
| 7 | Karar T2-2: *"sessiz ayrışma sıfır"* — 1.136.328 örnek, hepsi tek sınıfta; iddianın sınıfı grid'de doğamıyordu | **Implementer** |
| 8 | Elimdeki doğru ölçümü yavaş diye kestim, dar olanın sonucunu yazdım | şef (geriye dönük) |
| 9 | "Kapsam %98.83 → %99" — yuvarlama, gerçek artış yok | Tester-D |
| 10 | Erteleme gerekçesi *"T2-1 sınıfı tests/ katmanında kapanıyor"* — ölçülmemiş, yanlış | Tester-D |
| 11 | Ayrışan aile "`x == w`" — 52 karşı üye | **Implementer** |
| 12 | *"İki parametre ekseni TAMAMEN kapatır"* — çıkış-yolu ekseninde doğru, **değer** ekseninde yanlış | Tester-D |

Bu tablo PROTOKOL §4.6'ya **10. kuralı** doğurdu ve **implementer'ın şefe itiraz etme yükümlülüğünü** (§6) iki kez fiilen kullandırdı.

## Açık kalemler (kapanışta kayda geçer)

| Kalem | Neden ertelendi | Sahip |
|---|---|---|
| `exc_type` **değer** ekseni: belirli istisna tipine kapılı `__exit__` testlerden geçer | Üründe `with MssBackend()` çağrı yeri yok — erişilemez. Yaşayan üç `xfail(strict)` işareti `tester_D/test_d10` | D-3.Y1 |
| Parametrik testin docstring'i "ekseni tamamen kapatır" diyor — değer ekseninde yanlış | Belge kalemi | D-3.Y2 |
| M54 (`grab` tutamacı başka alana yazarsa yalnız `headless_check` §3 yakalar), M58 (K3 kutu ölçüsünün PARTIAL bacağı) | `known_gaps`'te adlandırılmış, `[ÖLÇÜLMÜYOR]` | D-3.Y3 |
| `headless_check.py` §3'te `with` bacağı yok, §4 dekoratör denetimi yalnız `FakeBackend.grab`'e bakıyor | `tests/` katmanı iki sınıfı da ölçüyor; §3'e ikinci savunma fazlalık | şef, ayrı tur |
| `dpi_scale = nan/inf` kabul ediliyor | `src/contracts/` dondurulmuş, sözleşme sorusu | yeni görev |
| `Frame.image` `compare=False` → `==` sahiplik regresyonunu göremez | Dondurulmuş sözleşme | yeni görev |
| Saat fırlatırsa `seq` tüketilir, `Frame` doğmaz | `time.monotonic` fırlatmaz; üretimde erişilemez | kayıt |
| Boş monitör guard'ı davranışsal olarak gereksiz (değeri tanı mesajı) | Dokunulmuyor | kayıt |
| `mss.grab` ~13.5 ms, tasarımın 10 ms bütçesini aşıyor | DXGI Desktop Duplication | T-010 |

## Karar

**T-005 KABUL.** Dört tester onayı (tur 1: A, B, C — tur 3: D), beş kabul komutu exit 0, on mutantlık kapı dişli, 986 test yeşil, gerçek ekranda doğrulandı, `demo/bolge_izle.py` canlı çalışıyor.
