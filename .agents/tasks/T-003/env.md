# Koşum Ortamı — T-003

Ortam Ajanı ürünü. Tester bu dosyayı okur; ortamı kendisi kurmaz.

## Doğrulanmış ortam

| | |
|---|---|
| Python | 3.12.10 |
| pytest | 9.1.1 · mypy · numpy 2.4.6 |
| Çalışma dizini | depo kökü |

Ağ, GPU, ekran veya gerçek monitör gerektirmez — hedef modül tamamen saf fonksiyonlardan oluşuyor.

## Koşum komutları

```bash
python -m mypy --strict src/capture/dpi.py
python -m pytest tests/unit/capture/test_dpi.py -q
```

Tester kendi testlerini şuraya yazar ve şöyle koşar:

```bash
python -m pytest .agents/tasks/T-003/tester_tests -q
```

## Okumaman gerekenler

- `.agents/tasks/T-003/delivery.md` — **okuma**
- `.agents/tasks/T-003/evidence/` — **okuma**

Okuyacakların: `packet.md`, bu dosya, `src/capture/dpi.py`, `tests/unit/capture/test_dpi.py`, `src/contracts/models.py` ve tasarım dokümanı.

## Bu görevde özellikle saldırılacak yerler

Kabul komutları geçiyor olabilir ama iş yine de bozuk olabilir. Bunlar bu modülün gerçek hata sınıfları:

**1 · Round-trip iddiası.** Modül `logical→physical→logical` dönüşümünün kayıpsız olduğunu iddia ediyor. **Kendi rastgele/kapsamlı örneklemenle sına** — mevcut testlerin seçtiği örneklere güvenme. Özellikle: negatif koordinatlar, tek sayı genişlikler, `dpi_scale` 1.25 ve 1.75 gibi tam olmayan ölçekler. İddia tutmuyorsa bu **bloke edici**.

**2 · Yuvarlama simetrisi.** Yuvarlama kuralı negatif koordinatlarda pozitiflerle simetrik davranmalı. `-2.5` ile `2.5` aynı yönde mi yuvarlanıyor, yoksa banker's rounding sızmış mı? Sanal masaüstünde negatif koordinat normaldir, asimetri gerçek bir hata olur.

**3 · Negatif koordinatlı monitör.** Birincilin solunda **ve** üstünde olan monitör. Göreli ↔ sanal dönüşümü oraya doğru mu gidiyor? İki yönlü round-trip tutuyor mu?

**4 · Karışık DPI.** Farklı `dpi_scale` değerine sahip iki-üç monitör. Bir monitörün ölçeği yanlışlıkla diğerine uygulanıyor mu?

**5 · Sınır durumları.** Sıfır genişlik/yükseklik · tamamen dışarıda kalan dikdörtgen · tam sınırda oturan · sınıra değen ama kesişmeyen (`right == monitor.x`) · **negatif genişlik/yükseklik** (paket bunu zorunlu kılmadı, davranışı ne? çökme mi, sessiz saçmalık mı?).

**6 · Saflık gerçek mi?** Modülde I/O, `ctypes`, `win32`, `importlib`, global durum var mı? Gözle ve grep ile tara. Aynı girdiyle iki kez çağırınca aynı sonucu veriyor mu (determinizm)?

**7 · Sözleşmeye saygı.** `src/contracts/models.py` içindeki `Rect` **dondurulmuş**. Modül onu mutasyona uğratmaya çalışıyor mu, yoksa hep yeni `Rect` mi döndürüyor?

**8 · Tasarım dokümanı uyumu.** §5.6'daki "bölge geçersiz" durumu bu modüle dayanıyor. Geçerlilik sınıflandırması o ihtiyacı gerçekten karşılıyor mu?
