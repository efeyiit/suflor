---
task: T-012
role: sef
round: 1
decision: tur-2
---

# T-012 tur 1 → tur 2 kararı

Tester-A (durum makinesi + sınır + ömür) **RET** — 1 yüksek / 1 orta / 8 düşük, 239 test. Tester-B (kötü kullanım + istek uyumu + test kalitesi) **ONAY** — 1 yüksek (şefin demosunda) / 4 orta / 9 düşük, 99 koşum. İkisi de kapıyı (gerçek ekran) 18/18 temiz gördü; Tester-B'nin gerçek fare kalemleri **kilitli oturum** yüzünden ölçülemedi (kilit açılınca şef koşar).

## Şefin yeniden üretimleri

| Bulgu | Kim | Şef | Karar |
|---|---|---|---|
| `KenarSekmesi` hiç toplanmıyor (lambda bağlantıları `self` tutuyor) → kenar durumunda `AnaPencere` düşürülünce **zombi** yarım daire (görünür, yokluyor, sağ tık alıcısız) | A Y-A1 | `sef_dogrulama/tur1_testerA_YA1_sef.txt`: görünür=True, yoklayıcı aktif, alıcı 0; pozitif kontrol bağlı-yöntemli widget toplanıyor | **implementer tur 2** (K1 ▲▲ ömür) |
| Mod tıkından sonra imleç diskin içinde kalınca panel 120 ms sonra yeniden açılıyor (ertelenmiş Snapshot karesine girer) | A O-A1 | kod okuma (`_mod_tiki` sonrası sayaç engeli yok) | implementer tur 2 (K4 ▲▲) |
| Dış `sekme.close()` → `durum` kenar, sekme yok; tepsisiz konfigürasyonda ulaşılamaz | B O-B1 | kod okuma | implementer tur 2 (K1 ▲▲ `kapandi`) |
| `tepsiye_al()` sonrası kullanıcı hiçbir şey görmüyor (balon kaldırılmıştı; Win11 ikonu taşmada) | B O-B3 | tur-1 kararının yan etkisi | implementer tur 2 (K5 ▲▲ süreç başına bir kez balon); kapı sürüklemeyi **yukarı** alır (balon alanından uzak) |
| **Esc bölge seçimini iptal ederken uygulamayı kapatıyor** (`SecimKatmani.keyPressEvent → quit`) | B Y-B1 | kod okuma; `demo/bolge_izle.py` şefin | **şef düzeltti**: `iptal` sinyali, katman kapanır |
| Seçim sırasında imleç sekmeye gelince panel seçim katmanının üstüne çıkıyor | B O-B2 | z-sırası ölçümü B'de | **şef düzeltti** (demo): seçim boyunca sekme gizli, bitince geri |
| `real_check` [3] pozitif kontrolü `sef_dogrulama/`'da yok | B O-B4 | doğru — KRT ölçtü, şef henüz koşmadı (kilit) | kilit açılınca şef koşar (`k5b` deseni) |
| Tam takımda T-011 `test_k5_sure_8000_uyeli_zincir` yük altında 61–65 ms > 60 | A, B, implementer | bilinen (T-011 açık kalemi) | T-011 bakım kalemi: eşik ölçüm koşuluna bağlansın |

## Şefin ölçülmüş hataları (tur 1)

| # | Hata | Yakalayan |
|---|---|---|
| 1 | Paket v2 ömür cümlesi ("Python sahipliği: AnaPencere silinince silinir") ölçülmeden yazıldı; kapı ve K1 ÖLÇÜ bu sınıfa uğramıyordu | Tester-A |
| 2 | Demo `SecimKatmani` Esc → `QApplication.quit()` (T-005 gösteriminden kalma) ürün kabuğuna bağlanınca uygulamayı kapatıyordu | Tester-B |
| 3 | Tur-1 [5c] düzeltmesi (balonu kaldır) kullanıcı geri bildirimini yok etti; doğru düzeltme kapının balon alanından uzak ölçmesi | Tester-B |
| 4 | [3] pozitif kontrolü KRT'ye bırakıldı, şef kendi koşmadı (§4.6/6) | Tester-B |

## Tur 2 kapsamı (implementer)
K1 ▲▲ ömür (lambda → bağlı yöntem; `del`/`deleteLater` testleri; pozitif kontrol) + `KenarSekmesi.kapandi` · K4 ▲▲ mod tıkı sonrası imleç diskten çıkana kadar yeniden açılmaz · K5 ▲▲ süreç başına bir kez balon (çağrı sayacı testi). Kapı v3: sürükleme yukarı.

Tester'lar tur 2'de kendi testleriyle yeniden doğrular (`verdict-*-tur2.md`); Tester-B'nin gerçek fare kalemleri (tepsi tıkı → ön plan, menü "Göster" → ön plan) kilit açıkken koşulur.
