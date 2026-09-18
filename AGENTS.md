# Suflor proje talimatları

## Kod konumu
- Proje kökü `C:\Users\Gaming\Desktop\Project\Suflor` klasörüdür. Tüm kod, test, model, bağımlılık ve proje belgelerini burada tut.
- Eski `çeviri uygulaması` klasöründe geliştirme yapma; komutları Suflor kökünden çalıştır.

## Ortak hafıza: Depo / Beyin
- Ortak hafıza, yan klasördeki mevcut `../Depo` Beyin sistemidir: `C:\Users\Gaming\Desktop\Project\Depo`.
- Çalışmaya başlarken `../Depo/AGENTS.md` ve hafıza işlemleri için `../Depo/.agents/skills/beyin/SKILL.md` dosyasını oku.
- Beyin komutlarını Depo kökünde, mevcut `beyin.py` ile çalıştır. Örnek: `python beyin.py context "Suflor"`. Ortamda Python yoksa Depo/AGENTS.md içindeki mevcut Python yolunu kullan.
- Proje kararlarını, kalıcı öğrenimleri ve çalışma sonuçlarını Depo'ya, `project: suflor` bilgisiyle ve kaynak bağlantılarıyla kaydet. Kararlar için `knowledge/` altında note-create, sonuçlar için receipt kullan; ardından sync çalıştır ve kaydı doğrula.
- Yeni görevlere task-create, mevcut görevlere gerçek expected_revision ile task-update uygula. Kullanıcı beyanını doğrulanan sonuçtan ayır; tamamlanmamış işi tamamlandı diye kaydetme.
- Suflor içinde ayrı Beyin sistemi kurma veya ortak hafızayı kopyalama. Mevcut `.agents` arşivini koru; yeni ortak hafıza kayıtlarını Depo'da tut.
- Kullanıcının hafızaya kaydetmeme taleplerine uy.

## Orvant proje modeli
- Çalışmaya devam etmeden önce `.project/state.json` ve [`.project/integration.md`](.project/integration.md) talimatlarını uygula.
- Güncel görev, kanıt ve etki durumunu `.project/scripts/project.py context .`; alan modelini `ontology .` komutuyla oku.
- `.project/state.json` dosyasını elle değiştirme. Görev ve karar değişikliklerinde önce `preview`, sonra aynı revizyon ve preview digest ile `apply` kullan.
- Orvant kayıtları ortak Depo/Beyin'in yerine geçmez; proje içi doğrulanabilir iş modeli Suflor'da, kalıcı ortak karar ve sonuç kayıtları `../Depo` içinde tutulur.
