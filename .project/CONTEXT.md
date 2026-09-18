# Suflör v1 — proje bağlamı

Revision: 0 · Yetkili kaynak: .project/state.json

Bu görünüm türetilmiştir. Güncel kanıt kontrolü için context komutunu çalıştır.

Amaç: Windows oyuncularına oyun akışını kesmeden doğru, bağlamlı ve yerel Türkçe ekran çevirisi sunan Suflör v1'i GitHub Releases üzerinden dağıtılabilir hale getirmek.
Hedef kitle: Türkçe yaması olmayan oyunları oynayan Windows kullanıcıları

## Kapsam

- Snapshot ve Bölge İzleme modlarının doğrulanması
- Bağlamlı yerel çeviri kalitesinin Blue Prince üzerinde değerlendirilmesi
- Ekran yakalama gizliliği, yerleşim ve gecikme ölçümlerinin kanıtlanması
- Temiz Windows ortamında çalışan v1 paketinin ve GitHub dağıtım hazırlığının tamamlanması

## Kapsam dışı

- v2 yerinde kaplama
- Exclusive fullscreen için injection veya hook
- Kendi çeviri modelini ince ayarlama
- macOS, Linux, mobil ve konsol desteği

## Kısıtlar

- Doğru çeviri hızdan önce gelir
- Varsayılan yol ücretsiz, yerel ve çevrimdışıdır
- OCR metni, çeviri ve ekran görüntüsü çevrimdışı yolda diske veya ağa yazılmaz
- Modal hata penceresi açılmaz ve oyun süreci kesilmez
- Oyun sürecine injection, DLL enjeksiyonu, API hook veya bellek okuma yapılmaz

## Açık sorular

- Blue Prince değerlendirme örneklerinin sayısı ve kesin geçme eşiği nedir?
- GitHub sürümünde hangi paket seçenekleri sunulacak: taşınabilir paket, kurucu veya ikisi?
- Uygulama kodu için hangi lisans seçilecek?
- İlk sürüm kod imzasız mı yayımlanacak, yoksa sertifika beklenecek mi?
- İngilizce dışındaki kaynak diller v1'de hangi kararlılık seviyesinde ilan edilecek?

## Nesneler ve ilişkiler

- suflor (product): Suflör
- current-build (artifact): Ana dal geliştirme sürümü
- test-guide (artifact): Kullanıcı test rehberi
- windows-package (artifact): Windows v1 dağıtım paketi
- c-quality-v1 (criterion): Bağlamsal çeviri doğruluğu v1
- c-latency-v1 (criterion): Bölge İzleme gecikmesi v1
- c-capture-privacy-v1 (criterion): Yakalama gizliliği v1
- c-overlay-usability-v1 (criterion): Bölge şeridi kullanılabilirliği v1
- c-engineering-v1 (criterion): Otomatik doğrulama sağlığı v1
- c-distribution-v1 (criterion): Windows dağıtım hazır olma v1
- run-auto-cc5cb15 (verification_run): cc5cb15 tam otomatik doğrulama
- run-quality-sample-cc5cb15 (verification_run): cc5cb15 gerçek yerel model örneği
- eval-automation-cc5cb15 (evaluation): cc5cb15 otomatik değerlendirmesi
- eval-quality-sample-cc5cb15 (evaluation): cc5cb15 yerel kalite örneği değerlendirmesi
- eval-blue-prince-v1 (evaluation): Blue Prince gerçek oyun değerlendirmesi
- release-policy-v1 (release_policy): v1 dağıtım tercihleri
- eval-package-v1 (evaluation): Windows paket değerlendirmesi
- v1-readiness (release_assessment): Suflör v1 hazır olma değerlendirmesi
- eval-automation-cc5cb15 → ölçütü değerlendirir → c-engineering-v1
- eval-automation-cc5cb15 → koşuma dayanır → run-auto-cc5cb15
- eval-quality-sample-cc5cb15 → ölçütü değerlendirir → c-quality-v1
- eval-quality-sample-cc5cb15 → ölçütü değerlendirir → c-latency-v1
- eval-quality-sample-cc5cb15 → koşuma dayanır → run-quality-sample-cc5cb15
- eval-blue-prince-v1 → ölçütü değerlendirir → c-quality-v1
- eval-blue-prince-v1 → ölçütü değerlendirir → c-latency-v1
- eval-blue-prince-v1 → ölçütü değerlendirir → c-capture-privacy-v1
- eval-blue-prince-v1 → ölçütü değerlendirir → c-overlay-usability-v1
- eval-package-v1 → ölçütü değerlendirir → c-distribution-v1
- eval-automation-cc5cb15 → sürüm kararına katkı verir → v1-readiness
- eval-quality-sample-cc5cb15 → sürüm kararına katkı verir → v1-readiness
- eval-blue-prince-v1 → sürüm kararına katkı verir → v1-readiness
- eval-package-v1 → sürüm kararına katkı verir → v1-readiness

### Somut nesne değerleri

- suflor: {"amac": "Oyun ekranındaki metni güvenli biçimde yakalayıp bağlamlı Türkçeye çevirmek."}
- current-build: {"aciklama": "Yakalama gizliliği, yapışık şerit ve Qwen3 kalite motorunu içeren doğrulanmış ana dal.", "surum": "cc5cb155eeca631858158ec1d5bc98d599da1c0a"}
- test-guide: {"aciklama": "Snapshot, Bölge İzleme ve kalite modeli için uygulanabilir kullanıcı adımları.", "dosya": "docs/KULLANICI_TEST_REHBERI.md", "surum": "cc5cb15"}
- windows-package: {"aciklama": "Temiz Windows ortamında sınanacak, modellerden ayrı dağıtım çıktısı."}
- c-quality-v1: {"hedef": "Blue Prince gerçek oyun örnekleri kullanıcı tarafından incelenir; kesin örnek sayısı ve geçme eşiği açık sorudur.", "kategori": "quality", "surum": "v1", "tanim": "Çeviri anlamı ve mantıksal ilişkileri korur; ipucu, sayı ve zorunlu oyun terimlerini bozmaz; açıklanamayan kaynak dil kalıntısı bırakmaz."}
- c-latency-v1: {"hedef": "Cache isabeti en çok 160 ms; cache ıskası en çok 320 ms; oyun FPS düşüşü en çok yüzde 3.", "kategori": "performance", "surum": "v1", "tanim": "Bölge İzleme değişen metni kullanıcıyı bekletmeden işler ve durağan metni yeniden çevirmez."}
- c-capture-privacy-v1: {"hedef": "Windows koruması ve geri dönüş yolu gerçek oyun ekranında doğrulanır.", "kategori": "privacy", "surum": "v1", "tanim": "Snapshot ve Bölge İzleme karelerinde hiçbir Suflör penceresi görünmez."}
- c-overlay-usability-v1: {"hedef": "Blue Prince içinde gerçek kullanıcı akışında yerleşim, hover, duraklatma, yeniden seçim ve kapatma doğrulanır.", "kategori": "usability", "surum": "v1", "tanim": "Çeviri seçilen alanın üstüne veya gerekirse altına yapışır; metni örtmez; kontroller yalnız gerektiğinde görünür."}
- c-engineering-v1: {"hedef": "Tüm pytest testleri geçer ve mypy strict hata vermez.", "kategori": "engineering", "surum": "v1", "tanim": "Ana dalın test ve katı tip denetimi temizdir."}
- c-distribution-v1: {"hedef": "Temiz Windows ortamında açılış ve iki mod duman testi geçer; uygulama paketi modeller hariç en çok 150 MB olur.", "kategori": "distribution", "surum": "v1", "tanim": "Kullanıcı geliştirme ortamı kurmadan Suflör'ü indirip açabilir; üçüncü taraf lisansları ve model indirme yolu pakette bulunur."}
- run-auto-cc5cb15: {"kaynak_commit": "cc5cb155eeca631858158ec1d5bc98d599da1c0a", "ozet": "2497 pytest testi geçti; 45 kaynak dosyasında mypy hatası yok.", "sonuc": "pass", "tarih": "2026-09-18", "yontem": "pytest -q ve mypy --strict --explicit-package-bases src"}
- run-quality-sample-cc5cb15: {"kaynak_commit": "cc5cb155eeca631858158ec1d5bc98d599da1c0a", "ozet": "İlk çalışma 3,36 saniye, sıcak çalışma 0,33 saniye; Plan yeniden devrede, Batı Kapısı ve Ön Oda üretildi.", "sonuc": "pass", "tarih": "2026-09-18", "yontem": "Qwen3 4B yerel sağlayıcıyla iki segment, sözlük ve çeviri hafızası içeren örnek koşum"}
- eval-automation-cc5cb15: {"karar": "pass", "ozet": "Kayıtlı ana dal koşumunda bütün testler ve tip denetimi geçti."}
- eval-quality-sample-cc5cb15: {"karar": "needs_review", "ozet": "Örnek bağlam ve zorunlu terimleri kullandı; tek sentetik koşum Blue Prince kalite ve uçtan uca gecikme ölçütlerini kapatmaz."}
- eval-blue-prince-v1: {"karar": "pending", "ozet": "Gerçek oyun testi henüz yapılmadı."}
- release-policy-v1: {"kod_imzasi": "pending", "paket_secenekleri": "pending", "uygulama_lisansi": "pending"}
- eval-package-v1: {"karar": "pending", "ozet": "Temiz Windows paketi henüz üretilip sınanmadı."}
- v1-readiness: {"durum": "pending", "ozet": "Otomatik testler temiz; Blue Prince gerçek oyun ve Windows paket kapıları açık."}

Türler ve bağlantı kuralları: `ontology` komutu / `ONTOLOJİ.md`.

## Kararlar

- D-V1 [accepted]: Daraltılmış beta yerine tasarım belgesindeki bütün v1 kapsamını hedefle.
  Gerekçe: Kullanıcı bütün v1'i istedi.; kaynak: 18 Eylül 2026 kullanıcı kararı; Depo knowledge/suflor-v1-hedef-ve-dagitim-kararlari-2026-09-18.md.; kabul eden: user
- D-GITHUB [accepted]: İlk dağıtımı GitHub Releases üzerinden yap ve kullanıcıya uygun çalışma seçenekleri sun.
  Gerekçe: Kullanıcının seçtiği ilk dağıtım kanalı GitHub'dır.; kaynak: 18 Eylül 2026 kullanıcı kararı; Depo knowledge/suflor-v1-hedef-ve-dagitim-kararlari-2026-09-18.md.; kabul eden: user
- D-QUALITY [accepted]: Doğru çeviriyi hızdan önce tut; hız için anlam ve mantık doğruluğunu düşürme.
  Gerekçe: Çeviri doğruluğu ürünün birincil ölçütüdür.; kaynak: 18 Eylül 2026 kullanıcı kararı ve son çeviri kalite geri bildirimi.; kabul eden: user
- D-BLUE-PRINCE [accepted]: İlk gerçek oyun doğrulamasını Blue Prince üzerinde yap.
  Gerekçe: Kullanıcı Blue Prince'i ilk deneme oyunu olarak seçti; kaynak dili İngilizcedir.; kaynak: 18 Eylül 2026 kullanıcı kararı; Depo knowledge/suflor-v1-hedef-ve-dagitim-kararlari-2026-09-18.md.; kabul eden: user
- D-OFFLINE [accepted]: Varsayılan çeviri yolunu ücretsiz, yerel ve çevrimdışı tut; bulutu yalnız isteğe bağlı yap.
  Gerekçe: Ürün tasarımının maliyet ve gizlilik duruşudur.; kaynak: Suflör v1 tasarım belgesi ve kullanıcı tarafından sürdürülen ürün kapsamı.; kabul eden: user
- D-ORVANT-WORK-PACKAGE [accepted]: Orvant'ın ilk izlenebilir iş paketini Blue Prince gerçek oyun kapısı, dağıtım kararları, Windows paketi ve v1 hazır olma incelemesiyle sınırla.
  Gerekçe: Mevcut otomatik teslimat tamamlandı; kalan v1 riskleri gerçek oyun ve dağıtım kanıtlarında yoğunlaşıyor.; kaynak: Ajanın mevcut README, tasarım belgesi, görev panosu ve doğrulanmış cc5cb15 teslimatına dayalı proje uyarlaması; yeni kullanıcı tercihi sayılmaz.; kabul eden: agent
- D-PACKAGE-FORMAT [proposed]: GitHub Releases üzerinde taşınabilir paket ve kurucu seçeneklerini birlikte sun.
  Gerekçe: Teknik kullanıcı ile çift tıklayıp kurmak isteyen kullanıcıya ayrı yollar sağlar.; kaynak: Ajan önerisi; kullanıcı seçenek sunulmasını istedi ancak kesin paket türlerini henüz seçmedi.; kabul eden: henüz kabul edilmedi

## Görevler

- T-BLUE-PRINCE [todo] Blue Prince gerçek oyun kalite ve kullanım kapısını çalıştır (kayıt: todo)
  - Ölçüt: Blue Prince içinden diyalog, menü ve belge/bulmaca örnekleri Snapshot ve Bölge İzleme ile gerçekten denenmiş; kaynak, çeviri, beklenen anlam ve karar kayıtlıdır.
  - Ölçüt: Anlam, mantıksal ilişki, ipucu, sayı ve zorunlu terim korunumu her örnek için incelenmiş; kaynak dilde kalan açıklanamayan ifade görünürdür.
  - Ölçüt: İlk ve sıcak çeviri gecikmeleri ölçülmüş; tekrar eden metnin yeniden çevrilmediği gözlenmiştir.
  - Ölçüt: Suflör penceresinin yakalamada görünmediği ve şerit yerleşimi ile hover kontrollerinin oyun içinde çalıştığı doğrulanmıştır.
  - Ölçüt: Sonuç kullanıcı gözlemi ile otomatik ölçümü ayıran bir rapora bağlanmıştır.
  - İlgili nesneler: current-build, test-guide, c-quality-v1, c-latency-v1, c-capture-privacy-v1, c-overlay-usability-v1, eval-blue-prince-v1
  - Girdiler: current-build, test-guide, c-quality-v1, c-latency-v1, c-capture-privacy-v1, c-overlay-usability-v1
  - Ürettiği nesneler: eval-blue-prince-v1
  - Etkin önkoşullar: yok
  - Kabul güncelliği: henüz doğrulanmadı · tamamlanma sayısı: 0
- T-RELEASE-POLICY [todo] v1 lisans, paket seçenekleri ve kod imzası kararlarını kapat (kayıt: todo)
  - Ölçüt: Uygulama kodu lisansı kullanıcı kararı olarak kaydedilmiştir.
  - Ölçüt: GitHub Releases üzerinde sunulacak paket seçenekleri kullanıcı kararı olarak kaydedilmiştir.
  - Ölçüt: İlk sürümde kod imzası kullanılıp kullanılmayacağı ve SmartScreen etkisi kaydedilmiştir.
  - İlgili nesneler: suflor, release-policy-v1
  - Girdiler: suflor
  - Ürettiği nesneler: release-policy-v1
  - Etkin önkoşullar: yok
  - Kabul güncelliği: henüz doğrulanmadı · tamamlanma sayısı: 0
- T-PACKAGE [blocked] Temiz Windows v1 paketini üret ve doğrula (kayıt: todo)
  - Ölçüt: Seçilen paket türleri temiz Windows ortamında geliştirme Python'u olmadan açılmıştır.
  - Ölçüt: Snapshot ve Bölge İzleme duman testleri paketli uygulamada geçmiştir.
  - Ölçüt: Model indirme, SHA-256 doğrulama, yarıda kesilme ve yeniden deneme akışları sınanmıştır.
  - Ölçüt: Üçüncü taraf lisansları pakete eklenmiş ve modeller hariç uygulama boyutu en çok 150 MB olarak ölçülmüştür.
  - Ölçüt: Paket dosyaları ve test raporu kanıta bağlanmıştır.
  - İlgili nesneler: current-build, release-policy-v1, c-distribution-v1, windows-package, eval-package-v1
  - Girdiler: current-build, release-policy-v1, c-distribution-v1
  - Ürettiği nesneler: windows-package, eval-package-v1
  - Etkin önkoşullar: T-RELEASE-POLICY
  - Üretici bağı: release-policy-v1 ← T-RELEASE-POLICY
  - Kabul güncelliği: henüz doğrulanmadı · tamamlanma sayısı: 0
  - Kontrol: dependency T-RELEASE-POLICY: todo
- T-V1-READINESS [blocked] v1 GitHub dağıtım hazır olma kararını kanıtlarla ver (kayıt: todo)
  - Ölçüt: Otomatik, gerçek oyun ve paket değerlendirmeleri güncel girdilere dayanarak birlikte incelenmiştir.
  - Ölçüt: Geçmeyen veya açık kalan her ölçüt sürüm notunda görünürdür; hazır kararı yalnız tüm zorunlu kapılar karşılandığında verilir.
  - Ölçüt: GitHub sürüm notu, doğrulanmış özellikleri ve bilinen sınırları teknik olmayan dille açıklar.
  - İlgili nesneler: eval-automation-cc5cb15, eval-quality-sample-cc5cb15, eval-blue-prince-v1, eval-package-v1, v1-readiness
  - Girdiler: eval-automation-cc5cb15, eval-quality-sample-cc5cb15, eval-blue-prince-v1, eval-package-v1
  - Ürettiği nesneler: v1-readiness
  - Etkin önkoşullar: T-BLUE-PRINCE, T-PACKAGE
  - Üretici bağı: eval-blue-prince-v1 ← T-BLUE-PRINCE
  - Üretici bağı: eval-package-v1 ← T-PACKAGE
  - Kabul güncelliği: henüz doğrulanmadı · tamamlanma sayısı: 0
  - Kontrol: dependency T-BLUE-PRINCE: todo
  - Kontrol: dependency T-PACKAGE: blocked

## Çalışılabilir görevler

T-BLUE-PRINCE, T-RELEASE-POLICY

## Uyarılar

- Yok.

## Onarım işlemleri

Bunlar öneridir; gerekçeyi değerlendir, actor ekle ve güncel revision ile uygula.
- Yok.

Kanıt hash'i dosya sürümünü denetler; kalite veya insan kabulünü ispatlamaz.
