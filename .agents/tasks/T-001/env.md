# Koşum Ortamı — T-001

Ortam Ajanı ürünü. Tester bu dosyayı okur; ortamı kendisi kurmaz.

## Doğrulanmış ortam

| | |
|---|---|
| Python | 3.12.10 |
| pytest | 9.1.1 |
| mypy | kurulu |
| numpy | 2.4.6 |
| Çalışma dizini | depo kökü (`çeviri uygulaması/`) |

## Koşum komutları

```bash
python -m mypy --strict src/contracts
python -m pytest tests/unit/contracts -q
python .agents/tasks/T-001/purity_check.py
```

Üçü de depo kökünden çalıştırılır. Hiçbiri ağ, GPU, ekran veya model dosyası gerektirmez — tamamen izole ve deterministiktir.

## Tester'ın kendi testleri

Tester **kendi bağımsız testlerini** şuraya yazar:

```
.agents/tasks/T-001/tester_tests/
```

ve şöyle koşar:

```bash
python -m pytest .agents/tasks/T-001/tester_tests -q
```

`src/` içine import edebilmek için depo kökünden koşmak yeterli; `conftest.py` gerekmez çünkü `src` paket kökü olarak çözülüyor. Çözülmezse tester `PYTHONPATH=.` ön ekiyle koşar ve bunu kanıt dosyasına yazar.

## Tester'ın okumaması gerekenler

- `delivery.md` — **okuma.** Implementer'ın iddialarına demirlemek körlüğü bozar.
- `evidence/` altındaki implementer çıktıları — **okuma.** Kendi komutunu kendin çalıştır.

Okuyacakların: `packet.md`, bu dosya, ve `src/contracts/` ile `tests/unit/contracts/` altındaki kodun kendisi.

## Neye bakılacak (kabul kriterlerinin ötesinde)

Kabul komutları geçiyor olabilir ama iş yine de bozuk olabilir. Bağımsız olarak şunları sına:

1. **Gerçekten frozen mı?** Her modelin bir örneğini oluşturup alanına atama yapmayı dene — `FrozenInstanceError` fırlatmalı. Testin var olması yetmez, davranışı doğrula.
2. **`FakeProvider` hizalı mı?** 1, 3 ve 0 segmentle çağır; dönen `translations` uzunluğu her seferinde `segments` uzunluğuna eşit olmalı.
3. **`image_crops` alanı var mı?** `TranslationRequest` içinde tanımlı ve `None` olabilir olmalı.
4. **Hata hiyerarşisi doğru mu?** Altı hata sınıfının hepsi `TranslatorError`'dan türemeli; `issubclass` ile doğrula.
5. **Saflık gerçek mi?** `purity_check.py` geçse bile `src/contracts/` altındaki import satırlarını gözle tara — dinamik import (`importlib`, `__import__`) ile atlatılmış mı?
