# Koşum Ortamı — T-002

Ortam Ajanı ürünü. Tester bu dosyayı okur; ortamı kendisi kurmaz.

## Doğrulanmış ortam

| | |
|---|---|
| Python | 3.12.10 |
| pytest | 9.1.1 · mypy · numpy 2.4.6 |
| Çalışma dizini | depo kökü |

Ekran, GPU veya ağ gerektirmez — `ChangeDetector` yalnızca verilen `Frame` nesneleri üzerinde çalışır, kendisi yakalama yapmaz. Test `Frame`'lerini numpy dizileriyle sen kurarsın.

## Koşum komutları

```bash
python -m mypy --strict src/capture/change_detector.py
python -m pytest tests/unit/capture/test_change_detector.py -q
```

Tester kendi testlerini şuraya yazar ve şöyle koşar:

```bash
python -m pytest .agents/tasks/T-002/tester_tests -q
```

## Okumaman gerekenler

- `.agents/tasks/T-002/delivery.md` — **okuma**
- `.agents/tasks/T-002/evidence/` — **okuma**

Okuyacakların: `packet.md`, bu dosya, `src/capture/change_detector.py`, `tests/unit/capture/test_change_detector.py`, `src/contracts/models.py` ve tasarım dokümanı §2.2 / §5.7.

`src/capture/dpi.py` senin kapsamında **değil** — başka bir görevin ürünü, dokunma.

## Bu görevde özellikle saldırılacak yerler

Bu bileşenin doğruluğu Mod 2'nin tamamını belirliyor. Yanlış "değişmedi" derse çeviri hiç güncellenmez; yanlış "değişti" derse pipeline boşuna koşar ve şerit titrer.

**1 · Debounce gerçekten çalışıyor mu?** Tasarım §2.2 adım 5: metin harf harf yazılırken yarısı okunmamalı. Kademeli değişen bir kare dizisi kur (her karede biraz daha metin) ve bileşenin **kararlı hâle gelmeden** "değişti" demediğini doğrula. Bu, bileşenin en kritik ve en kolay yanlış yapılan davranışı.

**2 · Livelock / açlık.** Sürekli hafifçe değişen (gürültülü) bir kaynakta bileşen **hiç** "değişti" demeyi bırakıyor mu, yoksa sonsuza kadar "henüz kararlı değil" mi diyor? İkisi de hata olur. Yavaş ama sürekli değişen sahne senaryosunu kur.

**3 · Geri dönen içerik.** Değişiklik adayı beklerken içerik eski hâline dönerse ne oluyor? Aday iptal mi ediliyor, yoksa yanlışlıkla onaylanıyor mu? Davranış tutarlı ve savunulabilir olmalı.

**4 · Bölge sıfırlama.** `Frame.rect` değiştiğinde geçmiş hash geçersiz olmalı ve ilk kare her zaman "değişti" saymalı. Yeni bölgede eski bölgenin hash'i sızıyor mu?

**5 · Eşik davranışı.** Tek piksellik değişiklik → "değişmedi" olmalı (gürültü toleransı). Metnin tamamının değişmesi → "değişti" olmalı. **Eşiğin iki tarafını da** sına: eşiğin hemen altında ve hemen üstünde ne oluyor?

**6 · Yozlaşmış girdiler.** Tek renk (tamamen siyah/beyaz) görüntü · çok küçük bölge (1×1, 3×3) · gradyan · aşırı geniş/dar en-boy oranı. Çökme veya sessiz saçmalık var mı?

**7 · Bütçe iddiası ≤ 5 ms.** Kendin ölç. Ayrıca **testin kendisinin gerçek olduğunu** doğrula: assertion'ı geçici olarak imkânsız bir eşikle zorladığında gerçekten kırılıyor mu, yoksa dekoratif bir `print` mi? (Bunu kendi test dosyanda yap, teslim edilen testi değiştirme.)

**8 · Determinizm ve saflık.** Aynı kare dizisi iki kez verildiğinde aynı sonuç dizisi çıkıyor mu? Modülde I/O, `time` bağımlılığı, global durum, rastgelelik var mı?

**9 · Sözleşmeye saygı.** `Frame` ve `Rect` **dondurulmuş**. Bileşen bunları mutasyona uğratmaya çalışıyor mu?
